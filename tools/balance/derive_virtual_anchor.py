#!/usr/bin/env python3
"""Diagnostic virtual-anchor candidates. No YAML, anchor signatures or approvals written.

Current ledger medians are NOT approved reference targets. Until the faction
approval/calibration stages land these candidates remain UNAPPROVED. Model
damage/reload are explicit synthetic inputs, never targets for real weapons.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

import class_membership
import fit_class
import formula
import diagnostic_output

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FACTIONS = ("tiberiandawn_gdi", "tiberiandawn_nod", "redalert_allies",
                    "redalert_soviets", "redalert_japan")
FACTION_ALIASES = dict(zip(("td_gdi", "td_nod", "ra1_allies", "ra1_soviets", "japan"), DEFAULT_FACTIONS))
FIELDS = ("hp", "speed", "range_wdist", "cost")
# Speed stays on the 1-grid for EVERY type — DESIGN.md 2026-09-07 ruling: the
# old 5-step for vehicles/aircraft/ships existed only to keep TurnSpeed =
# Speed/5 an integer, which the derived turn-rate trait removed. Do not
# reintroduce a per-class speed grid.
STEPS = dict(hp=1000, speed=1, range_wdist=10, cost=100)


def number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) and value > 0 else None
    except (ValueError, TypeError):
        return None


def stat_values(unit):
    """The four diagnostic axes, using exactly the fitting armament domain."""
    ranges = [number(formula.wdist_value(a.get("range"), 0))
              for a in fit_class.pricing_armaments(unit)]
    speed = number((unit.get("speed") or {}).get("v"))
    if speed is None:
        speed = number((unit.get("speed_air") or {}).get("v"))
    return dict(hp=number((unit.get("hp") or {}).get("v")), speed=speed,
                range_wdist=max((r for r in ranges if r is not None), default=None),
                cost=number((unit.get("cost") or {}).get("v")))


def input_fingerprints(ledger):
    assignment_path = ledger / "derived/reference_assignment.json"
    provenance = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in sorted(ledger.glob("*.json"))}
    return dict(
        ledger_sha256=provenance,
        sidecar_sha256={path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in sorted((ledger / "derived").glob("*.json"))
                       if path.name in provenance},
        assignment_sha256=hashlib.sha256(assignment_path.read_bytes()).hexdigest())


def load_evidence(ledger):
    """Reject missing evidence or a changed input fingerprint during collection."""
    before = input_fingerprints(ledger)
    assignment_doc = json.loads((ledger / "derived/reference_assignment.json").read_text(encoding="utf-8-sig"))
    assignments = assignment_doc["assignment"]
    if not isinstance(assignments, dict):
        raise ValueError("reference assignment must be an object")
    members = load_members(ledger)
    if input_fingerprints(ledger) != before:
        raise ValueError("input evidence changed during collection; retry on a stable tree")
    return members, assignments, before


def load_members(ledger):
    members = []
    for path in sorted(ledger.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(doc, dict) or "sections" not in doc:
            continue
        sidecar = ledger / "derived" / path.name
        derived = json.loads(sidecar.read_text(encoding="utf-8-sig")) if sidecar.exists() else {}
        for section_name, section in doc["sections"].items():
            for actor, unit in section.items():
                cls, reason = class_membership.classify(unit.get("design") or {})
                if cls is None or not fit_class.eligible_virtual_member(unit):
                    continue
                ledger_name = doc.get("ledger", path.stem)
                # Shared content files are storage locations, not the actor's
                # faction. Keep canonical pilot actors in their faction pool.
                faction = next((name for prefix, name in FACTION_ALIASES.items()
                                if actor.startswith(prefix + "_")), ledger_name)
                members.append(dict(actor=actor, faction=faction, source_ledger=ledger_name,
                    cls=cls, membership=reason, unit=unit,
                    derived=(derived.get("sections", {}).get(section_name, {}).get(actor) or {}),
                    **stat_values(unit)))
    return members


def percentile(value, population):
    """Midrank avoids falsely calling a constant population an extreme tail."""
    return 100 * (sum(x < value for x in population) + .5 * sum(x == value for x in population)) / len(population)


def derive(cls, members, assignments, factions=DEFAULT_FACTIONS, model_damage=None, model_reload=None):
    if (model_damage is None) != (model_reload is None):
        raise ValueError("supply both model damage and model reload")
    full = [m for m in members if m["cls"] == cls]
    source = [m for m in full if m["faction"] in factions]
    # Pool provenance: the dossier must be able to show which faction pool and
    # which exact actors produced each median, including for NO SOURCE (the
    # selected factions are preserved so "0 of N" is followable, not implied).
    result = dict(cls=cls, status=["UNAPPROVED"], full_count=len(full), source_count=len(source),
                  selected_factions=list(factions), source_actors=[m["actor"] for m in source],
                  method="median of current ledger stats, reference-backed members preferred",
                  fields={}, sources=[], verifier=None)
    if not source:
        result["status"] = ["NO SOURCE"]
        result["no_source"] = ("no eligible member of this class in the selected faction pool — "
                               "class members or references outside the pool are not borrowed")
        return result
    backed = []
    for member in source:
        refs = [{"source": name, "id": ref["id"], "confidence": ref["confidence"]}
                for name, ref in assignments.get(member["actor"], {}).items()
                if ref.get("confidence") in ("STRONG", "FAIR") and ref.get("id")]
        result["sources"].append(dict(actor=member["actor"], faction=member["faction"], references=refs))
        if refs:
            backed.append(member)
    fields = ("hp", "speed", "cost") if cls == "support" else FIELDS
    for field in fields:
        preferred = [m for m in backed if m.get(field) is not None]
        pool = preferred or [m for m in source if m.get(field) is not None]
        population = [m[field] for m in full if m.get(field) is not None]
        if not pool:
            result["status"].append(f"MISSING {field}")
            continue
        median = statistics.median(m[field] for m in pool)
        step = STEPS[field]
        snapped = max(step, math.floor(median / step + .5) * step)
        rank = percentile(median, population)
        # This diagnostic threshold is exposed, not an automatic approval rule.
        # reference_preference makes the per-axis pool semantics explicit: a
        # preference that every backed member lacks the stat for is "vacated",
        # not silently the same as no preference at all.
        result["fields"][field] = dict(value=snapped, median=median, count=len(pool),
            grid_step=step, reference_backed=bool(preferred),
            reference_preference="applied" if preferred else
                                 ("vacated by missing stat" if backed else "none"),
            percentile=rank, actors=[m["actor"] for m in pool])
        if rank < 10 or rank > 90:
            result["status"].append(f"BIASED {field} — do not sign")
        if len(pool) < 3:
            result["status"].append(f"THIN {field}")
    if cls == "support":
        result["status"].append("ABILITY PRICED — no combat verifier")
        return result
    if len(result["fields"]) != len(FIELDS):
        return result
    if model_damage is None:
        result["status"].append("NO MODEL — calibrated damage/reload not supplied")
        return result
    result["status"].append("SYNTHETIC SENSITIVITY — not calibrated")
    h, s, r, cost = (result["fields"][field]["value"] for field in FIELDS)
    spec = fit_class.virtual_spec(f"{h},{s},{r},{model_damage},{model_reload},{cost}")
    if model_damage % formula.DAMAGE_STEP:
        raise ValueError("model damage must be on formula.DAMAGE_STEP")
    d = formula.dps(model_damage, model_reload)
    estimators = fit_class.virtual_estimators((h, s, r, d, 1, 1, 1), spec)
    if not all(math.isclose(x, cost) for x in estimators):
        raise ValueError("virtual baseline identity failed")
    verifier_price = sum(fit_class.virtual_estimators((2*h, s, r, 2*d, 1, 1, 1), spec)) / 3
    if not math.isclose(verifier_price, 2.5*cost):
        raise ValueError("virtual verifier identity failed")
    result["model"] = dict(damage=model_damage, reload=model_reload, tech_tier=1, K=1,
                           description="synthetic nominal model; no real weapon target")
    result["estimators"] = list(estimators)
    result["verifier"] = dict(hp=2*h, damage=2*model_damage, reload=model_reload,
                               cost=2.5*cost, tech_tier=1, K=1)
    result["command"] = f"python tools/balance/fit_class.py --class {cls} --spec {h},{s},{r},{model_damage},{model_reload},{cost}"
    residuals = []
    skipped = []
    for member in full:
        inputs, _ = fit_class.unit_inputs(member["unit"], member.get("derived"))
        if inputs is None or not member.get("cost"):
            skipped.append(member["actor"])
            continue
        price = fit_class.virtual_price(member["unit"], member.get("derived"), inputs, spec)
        residuals.append((price - member["cost"]) / member["cost"])
    result["residuals"] = dict(count=len(residuals), skipped=skipped,
        minimum=min(residuals, default=None), median=statistics.median(residuals) if residuals else None,
        maximum=max(residuals, default=None), basis="nominal DPS; no derived K")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--class", dest="cls")
    mode.add_argument("--all", action="store_true")
    parser.add_argument("--factions", default=",".join(DEFAULT_FACTIONS))
    parser.add_argument("--model-damage", type=int, help="explicit synthetic sensitivity input, not a real weapon target")
    parser.add_argument("--model-reload", type=int, help="required with --model-damage; no arbitrary model by default")
    parser.add_argument("--out", type=Path, help="optional diagnostic JSON output directory")
    args = parser.parse_args(argv)
    if args.out:
        try:
            diagnostic_output.validate_path(ROOT, args.out / "probe.json")
        except ValueError as exc:
            parser.error(str(exc))
    try:
        if (args.model_damage is None) != (args.model_reload is None):
            raise ValueError("supply both --model-damage and --model-reload")
        if args.model_damage is not None:
            fit_class.virtual_spec(f"1,1,1,{args.model_damage},{args.model_reload},1")
            if args.model_damage % formula.DAMAGE_STEP:
                raise ValueError("model damage must be on formula.DAMAGE_STEP")
    except ValueError as error:
        parser.error(str(error))
    ledger = ROOT / "docs/balance"
    registry = (ledger / "class_anchors.json").read_bytes()
    anchors = json.loads(registry.decode("utf-8"))
    classes = sorted(k for k, value in anchors.items() if isinstance(value, dict) and "spec" in value)
    if args.cls and args.cls not in classes:
        parser.error(f"unknown class: {args.cls}")
    members, assignments, provenance = load_evidence(ledger)
    if provenance.get("ledger_sha256", {}).get("class_anchors.json") != hashlib.sha256(registry).hexdigest():
        parser.error("class_anchors.json changed between registry read and evidence collection; "
                     "no output written")
    factions = [FACTION_ALIASES.get(f.strip(), f.strip()) for f in args.factions.split(",")]
    unknown = set(factions) - {m["faction"] for m in members}
    if unknown:
        parser.error(f"unknown or empty source factions: {sorted(unknown)}")
    outputs = {}
    for cls in [args.cls] if args.cls else classes:
        result = derive(cls, members, assignments, factions, args.model_damage, args.model_reload)
        result.update(provenance)
        text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.out:
            outputs[args.out / f"{cls}.json"] = text
        else:
            print(text, end="")
    if outputs:
        try:
            diagnostic_output.write_outputs(ROOT, outputs)
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
