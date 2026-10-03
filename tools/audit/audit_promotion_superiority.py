#!/usr/bin/env python3
"""Audit promotion replacements without changing balance or YAML.

The current promotion contract marks a replaced base actor with a negative
promotion prerequisite (usually ``~!faction_promotion_name``).  This audit
uses those authored markers as the replacement map, then compares the live
resolved actors and the existing balance-ledger primary armament metrics.
It deliberately reports review findings instead of deciding whether a
specialized promotion unit is a better gameplay choice.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))

import diagnostic_output  # noqa: E402
import formula  # noqa: E402
from cameo_model import Model  # noqa: E402
from firepower import armament_firepower, priced_by_default  # noqa: E402


FACTIONS = ("ra1_allies", "ra1_soviets", "td_gdi", "td_nod")
LEDGER_FILES = (
    "shared_redalert.json",
    "redalert_allies.json",
    "redalert_soviets.json",
    "shared_tiberiandawn.json",
    "tiberiandawn_gdi.json",
    "tiberiandawn_nod.json",
)

SHARED_TOKEN_DISPOSITIONS = {
    "td_gdi_promotion_havocandexosuit": {
        "pairs": (("td_gdi_commando", "td_gdi_havoc"),),
        "additional_options": ("td_gdi_exosuit",),
        "basis": "The promotion unlocks an infantry successor and a separate vehicle option; only Havoc replaces the disabled infantry Commando.",
    },
    "td_nod_promotion_upgradeupnodstealthname": {
        "pairs": (("td_nod_tiberiumharvester", "td_nod_stealthharvester"),),
        "additional_options": ("td_nod_stealthsoldier",),
        "basis": "The Stealth Harvester replaces the disabled harvester; the Stealth Soldier is an additional infantry option.",
    },
    "td_nod_promotion_upgradeupnodvenomname": {
        "pairs": (("td_nod_commando", "td_nod_lasercommando"),),
        "additional_options": ("td_nod_venom",),
        "basis": "The Laser Commando replaces the disabled infantry Commando; the Venom is an additional aircraft option.",
    },
}

NON_OFFENSIVE_ARMAMENT_MARKERS = (
    "pointdefense", "point-defense", "point_defense", "interceptor",
    "flare", "dummy", "visual", "decoration",
)


def finite(value):
    """Return a finite float, preserving missing values as ``None``."""
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def compare_value(base, promotion, *, tolerance=1e-9):
    """Compare one numeric metric with explicit missing/equal states."""
    left, right = finite(base), finite(promotion)
    if left is None or right is None:
        return {"status": "UNRESOLVED", "base": left, "promotion": right,
                "delta": None, "ratio": None}
    delta = right - left
    if math.isclose(left, right, rel_tol=tolerance, abs_tol=tolerance):
        status = "SAME"
    elif delta > 0:
        status = "UP"
    else:
        status = "DOWN"
    return {"status": status, "base": left, "promotion": right,
            "delta": delta, "ratio": (right / left if left else None)}


def parse_negative_promotion_token(raw):
    """Return the promotion token from ``~!token``/``!token`` or ``None``."""
    token = (raw or "").strip().lstrip("~").lower()
    return token[1:] if token.startswith("!") and len(token) > 1 else None


def compare_warheads(base_values, promotion_values):
    """Compare class identities without treating labels as a strength ladder."""
    base_names = sorted({str(value) for value in base_values or () if value})
    promotion_names = sorted({str(value) for value in promotion_values or () if value})
    if not base_names or not promotion_names:
        status = "UNRESOLVED"
    elif base_names == promotion_names:
        status = "SAME_LABELS"
    else:
        status = "DIFFERENT_LABELS"
    return {"status": status, "base_names": base_names,
            "promotion_names": promotion_names}


def compare_armor(base_type, promotion_type, base_armor, promotion_armor):
    result = {"base": base_armor, "promotion": promotion_armor}
    if base_type != promotion_type:
        return result | {"status": "CROSS_TYPE"}
    if not base_armor or not promotion_armor:
        return result | {"status": "UNRESOLVED"}
    return result | {"status": "SAME_LABELS" if base_armor == promotion_armor
                     else "DIFFERENT_LABELS"}


def _load_ledgers(root):
    index, paths = {}, []
    for name in LEDGER_FILES:
        path = root / "docs" / "balance" / name
        if not path.is_file():
            continue
        paths.append(path)
        ledger_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        document = json.loads(path.read_text(encoding="utf-8"))
        for section in (document.get("sections") or {}).values():
            if isinstance(section, dict):
                for actor, row in section.items():
                    index[actor] = {
                        "row": row,
                        "ledger_file": str(path),
                        "ledger_sha256": ledger_sha256,
                    }
    return index, paths


def _promotion_index(model, faction):
    """Return token -> promotion actor, unit consumers and base replacements."""
    token_to_promotion = {}
    for actor in model.rs.actors:
        if not actor.startswith(faction + "_promotion_"):
            continue
        resolved = model.rs.resolve(actor)
        if resolved is None:
            continue
        for child in resolved.children_named("ProvidesPrerequisite"):
            token = (child.get("Prerequisite") or actor).strip().lower()
            token_to_promotion[token] = actor

    token_to_units = {token: [] for token in token_to_promotion}
    for actor in sorted(model.rs.actors):
        if not actor.startswith(faction + "_") or "_promotion_" in actor:
            continue
        resolved = model.rs.resolve(actor)
        if resolved is None or not model.is_buildable(resolved):
            continue
        for token in model.positive_prereqs(resolved):
            if token in token_to_units:
                token_to_units[token].append(actor)

    token_to_bases = defaultdict(list)
    for actor in sorted(model.rs.actors):
        if not actor.startswith(faction + "_") or "_promotion_" in actor:
            continue
        resolved = model.rs.resolve(actor)
        if resolved is None:
            continue
        buildable = resolved.child("Buildable")
        if buildable is None:
            continue
        for raw in (buildable.get("Prerequisites") or "").split(","):
            token = parse_negative_promotion_token(raw)
            if token in token_to_promotion:
                token_to_bases[token].append(actor)

    return token_to_promotion, token_to_units, dict(token_to_bases)


def _is_non_offensive_armament(armament):
    fields = " ".join(str(armament.get(key) or "").lower()
                      for key in ("slot", "armament_name"))
    return any(marker in fields for marker in NON_OFFENSIVE_ARMAMENT_MARKERS)


def select_offensive_armament(unit):
    """Select one factory-state combat armament, excluding utility defenses."""
    candidates = [
        armament for armament in unit.get("armaments", [])
        if priced_by_default(armament)
        and armament.get("weapon")
        and not _is_non_offensive_armament(armament)
    ]
    if not candidates:
        return None

    def priority(armament):
        slot = (armament.get("slot") or "").lower()
        if slot == "armament@primary":
            return 0
        if slot == "armament":
            return 1
        return 2

    return min(enumerate(candidates), key=lambda item: (priority(item[1]), item[0]))[1]


def offensive_armament_metrics(unit, armament=None):
    """Compute range, DPS and class identity from the same ledger record."""
    selected = armament if armament is not None else select_offensive_armament(unit)
    if selected is None:
        return {"armament": None, "range": None, "dps": None,
                "warheads": [], "damage_tags": []}
    range_value = formula.wdist_value(selected.get("range"), None)
    reload_delay = finite(selected.get("reloaddelay"))
    burst = int(finite(selected.get("burst")) or 1)
    damage = formula.spread_damage_sum(selected.get("damage_warheads", []))
    dps = None
    if reload_delay and damage:
        dps = formula.dps(
            damage, reload_delay, burst, selected.get("burstdelays"),
            firepower_multiplier=armament_firepower(unit, selected),
        )
    return {
        "armament": selected,
        "range": finite(range_value) if finite(range_value) and finite(range_value) > 0 else None,
        "dps": finite(dps) if finite(dps) and finite(dps) > 0 else None,
        "warheads": list(selected.get("warheads") or []),
        "damage_tags": [item.get("tag") for item in
                        selected.get("damage_warheads", []) if item.get("tag")],
    }


def _metrics(model, ledger_index, actor):
    resolved = model.rs.resolve(actor)
    if resolved is None:
        return {"status": "MISSING", "actor": actor}

    hp = finite(resolved.get("Health", "HP"))
    speed = finite(resolved.get("Mobile", "Speed") or
                   resolved.get("Aircraft", "Speed"))
    cost = finite(resolved.get("Valued", "Cost"))
    ledger_record = ledger_index.get(actor)
    ledger = ledger_record["row"] if ledger_record else None
    armament_metrics = offensive_armament_metrics(ledger or {})
    primary = armament_metrics["armament"]

    return {
        "status": "RESOLVED",
        "actor": actor,
        "type": model.unit_type(actor),
        "hp": finite(hp),
        "speed": finite(speed),
        "range": armament_metrics["range"],
        "dps": armament_metrics["dps"],
        "cost": finite(cost),
        "armor": resolved.get("Armor", "Type"),
        "primary_weapon": (primary or {}).get("weapon"),
        "primary_armament_slot": (primary or {}).get("slot"),
        "armament_state": {
            "requires_condition": (primary or {}).get("requires"),
            "selection_assumption": "named conditions evaluated as zero by the existing ledger selector; this is not factory-state certification",
        },
        "selected_offensive_armament": primary is not None,
        "primary_warheads": armament_metrics["warheads"],
        "primary_damage_tags": armament_metrics["damage_tags"],
        "metric_sources": {
            "hp_speed_armor_cost": "resolved active ruleset",
            "range_dps_weapon_class": "one selected factory-state balance-ledger armament",
            "ledger_file": ledger_record.get("ledger_file") if ledger_record else None,
            "ledger_sha256": ledger_record.get("ledger_sha256") if ledger_record else None,
            "ledger_armament_freshness": (
                "HASH_DISCLOSED_NOT_INDEPENDENTLY_RECONSTRUCTED"
                if ledger_record else "NO_LEDGER_ROW"
            ),
        },
        "source": {"file": str(model.rs.actor(actor).file),
                   "line": model.rs.actor(actor).line},
    }


def _pair(model, ledger_index, faction, token, base, promotion):
    base_metrics = _metrics(model, ledger_index, base)
    promotion_metrics = _metrics(model, ledger_index, promotion)
    base_type, promotion_type = base_metrics.get("type"), promotion_metrics.get("type")
    comparisons = {
        "hp": compare_value(base_metrics.get("hp"), promotion_metrics.get("hp")),
        "speed": compare_value(base_metrics.get("speed"), promotion_metrics.get("speed")),
        "range": compare_value(base_metrics.get("range"), promotion_metrics.get("range")),
        "dps": compare_value(base_metrics.get("dps"), promotion_metrics.get("dps")),
        "armor": compare_armor(base_type, promotion_type,
                                base_metrics.get("armor"), promotion_metrics.get("armor")),
        "warhead_class": compare_warheads(
            base_metrics.get("primary_warheads") or base_metrics.get("primary_damage_tags"),
            promotion_metrics.get("primary_warheads") or promotion_metrics.get("primary_damage_tags")),
    }

    armament_scope = bool(base_metrics.get("selected_offensive_armament") or
                          promotion_metrics.get("selected_offensive_armament"))
    if base_metrics.get("speed") is None and promotion_metrics.get("speed") is None:
        comparisons["speed"] = {"status": "NOT_APPLICABLE", "base": None,
                                 "promotion": None, "delta": None, "ratio": None}
    if not armament_scope:
        for metric in ("range", "dps", "warhead_class"):
            comparisons[metric] = {"status": "NOT_APPLICABLE", "base": None,
                                   "promotion": None, "delta": None, "ratio": None}

    findings = []
    if comparisons["hp"]["status"] == "DOWN":
        findings.append("HP_LOWER")
    elif comparisons["hp"]["status"] == "SAME":
        findings.append("HP_SAME")
    if comparisons["speed"]["status"] == "DOWN":
        findings.append("SPEED_LOWER")
    if comparisons["range"]["status"] == "DOWN":
        findings.append("RANGE_LOWER")
    if comparisons["dps"]["status"] == "DOWN":
        findings.append("DPS_LOWER")
    elif comparisons["dps"]["status"] == "SAME":
        findings.append("DPS_SAME")
    if comparisons["armor"]["status"] == "DIFFERENT_LABELS":
        findings.append("ARMOR_LABELS_DIFFER")
    if comparisons["warhead_class"]["status"] == "DIFFERENT_LABELS":
        findings.append("WARHEAD_LABELS_DIFFER")

    # Missing range/DPS/warhead data is expected for unarmed defenses and
    # harvesters.  A missing value is unresolved only when one side has a
    # priced primary armament and the other side cannot be measured.
    unresolved = []
    if comparisons["hp"]["status"] == "UNRESOLVED":
        unresolved.append("hp")
    # Stationary defenses have no Mobile/Aircraft speed on either side;
    # that metric is inapplicable rather than an unresolved defect.
    if (base_metrics.get("speed") is not None or
            promotion_metrics.get("speed") is not None):
        if comparisons["speed"]["status"] == "UNRESOLVED":
            unresolved.append("speed")
    if armament_scope:
        for metric in ("range", "dps", "warhead_class"):
            if comparisons[metric]["status"] == "UNRESOLVED":
                unresolved.append(metric)
    if unresolved:
        findings.extend("UNRESOLVED_" + metric.upper() for metric in unresolved)

    if unresolved:
        status = "UNRESOLVED"
    elif findings:
        status = "STATIC_DIFFERENCES"
    else:
        status = "MEASURED_NO_LISTED_DIFFERENCE"

    return {
        "faction": faction,
        "promotion_token": token,
        "base_actor": base,
        "promotion_actor": promotion,
        "base": base_metrics,
        "promotion": promotion_metrics,
        "comparisons": comparisons,
        "status": status,
        "findings": sorted(set(findings)),
        "metric_basis": "Resolved active HP/speed/armor/cost plus one selected factory-state offensive ledger armament for range/DPS/class labels. The value and weapon identity come from that same armament; point defense, utility slots, upgrades, secondary payloads, status uptime and gameplay are excluded.",
    }


def replacement_disposition(token, bases, units):
    """Resolve authored 1:1 replacements without cross-joining shared tokens."""
    bases, units = sorted(set(bases)), sorted(set(units))
    if not bases:
        return {"status": "NO_BASE_DISABLE_MARKER", "pairs": [],
                "additional_options": [], "reason": None}
    if len(bases) == 1 and len(units) == 1:
        return {
            "status": "AUTHORED_ONE_TO_ONE",
            "pairs": [{"base_actor": bases[0], "promotion_actor": units[0]}],
            "additional_options": [],
            "reason": "The token has one disabled base and one promotion consumer.",
        }

    explicit = SHARED_TOKEN_DISPOSITIONS.get(token)
    if explicit is None:
        return {
            "status": "AMBIGUOUS_SHARED_TOKEN",
            "pairs": [],
            "additional_options": units,
            "reason": "Multiple bases or consumers share this token and no explicit replacement identity is recorded.",
        }

    pairs = [{"base_actor": base, "promotion_actor": promotion}
             for base, promotion in explicit["pairs"]]
    invalid = [pair for pair in pairs
               if pair["base_actor"] not in bases or pair["promotion_actor"] not in units]
    additional = list(explicit.get("additional_options", ()))
    invalid.extend({"promotion_actor": actor} for actor in additional if actor not in units)
    if invalid:
        return {
            "status": "INVALID_EXPLICIT_DISPOSITION",
            "pairs": [],
            "additional_options": units,
            "reason": f"Recorded disposition does not match the active token actors: {invalid}",
        }
    mapped_units = {pair["promotion_actor"] for pair in pairs}
    if set(units) != mapped_units | set(additional):
        return {
            "status": "INCOMPLETE_EXPLICIT_DISPOSITION",
            "pairs": [],
            "additional_options": units,
            "reason": "Recorded disposition does not account for every active promotion consumer.",
        }
    return {
        "status": "EXPLICIT_REPLACEMENT_WITH_ADDITIONAL_OPTIONS",
        "pairs": pairs,
        "additional_options": sorted(additional),
        "reason": explicit["basis"],
    }


def build_report(model=None, *, root=ROOT, tool_path=None):
    model = model or Model(root)
    ledger_index, ledger_paths = _load_ledgers(root)
    pairs, token_rows, unpaired = [], [], []
    for faction in FACTIONS:
        token_to_promotion, token_to_units, token_to_bases = _promotion_index(model, faction)
        for token in sorted(token_to_promotion):
            promotion = token_to_promotion[token]
            bases = sorted(token_to_bases.get(token, []))
            units = sorted(token_to_units.get(token, []))
            disposition = replacement_disposition(token, bases, units)
            token_rows.append({
                "faction": faction,
                "promotion_token": token,
                "promotion_actor": promotion,
                "promotion_units": units,
                "base_replacement_actors": bases,
                "mapping_status": disposition["status"],
                "replacement_pairs": disposition["pairs"],
                "additional_options": disposition["additional_options"],
                "mapping_reason": disposition["reason"],
            })
            if not bases:
                unpaired.extend({"faction": faction, "promotion_token": token,
                                 "promotion_actor": promotion, "promotion_unit": unit,
                                 "reason": "no active actor carries a negative ~!promotion prerequisite for this token"}
                                 for unit in units)
            else:
                unpaired.extend({"faction": faction, "promotion_token": token,
                                 "promotion_actor": promotion, "promotion_unit": unit,
                                 "reason": "additional option unlocked by a shared token; not a replacement edge"}
                                for unit in disposition["additional_options"])
            for edge in disposition["pairs"]:
                pairs.append(_pair(
                    model, ledger_index, faction, token,
                    edge["base_actor"], edge["promotion_actor"],
                ))

    findings = Counter(f for pair in pairs for f in pair["findings"])
    return {
        "schema": 2,
        "status": "REVIEW_ONLY",
        "scope": "Current RA1 Allies, RA1 Soviets, TD GDI and TD Nod promotion-token consumers; replacement edges come only from authored negative promotion prerequisites.",
        "policy": {
            "decision": "DIAGNOSTIC_ONLY",
            "meaning": "This receipt identifies explicit one-for-one replacement pairs and describes static differences. It does not apply a global strict-superiority law, remove PromotionUnitBuff, change costs, choose a discount, or certify balance.",
        },
        "method": [
            "Read the active merged ruleset through cameo_model and inspect Buildable.Prerequisites.",
            "Treat a token with one disabled base and one consumer as an authored one-to-one replacement. Shared-token dispositions explicitly separate the actual replacement from additional options; never take a Cartesian product.",
            "Compare resolved HP, speed and armor. Select one factory-state offensive armament from the hashed balance ledger and derive weapon identity, range, DPS and class labels from that same record; exclude point defense and utility slots.",
            "Report warhead labels as identities rather than a universal strength ranking. Keep missing armament data and cross-type pairs unresolved instead of inventing equivalence.",
        ],
        "inputs": {
            "factions": list(FACTIONS),
            "ledger_paths": [str(path) for path in ledger_paths],
            "ledger_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                              for path in ledger_paths},
            "tool": str(tool_path) if tool_path else None,
        },
        "summary": {
            "promotion_tokens": len(token_rows),
            "promotion_tokens_with_base_marker": sum(bool(row["base_replacement_actors"]) for row in token_rows),
            "promotion_tokens_without_base_marker": sum(not row["base_replacement_actors"] for row in token_rows),
            "promotion_units": sum(len(row["promotion_units"]) for row in token_rows),
            "promotion_units_without_base_marker": sum(
                len(row["promotion_units"]) for row in token_rows
                if not row["base_replacement_actors"]
            ),
            "replacement_pairs": len(pairs),
            "additional_options_excluded_from_pairs": sum(len(row["additional_options"]) for row in token_rows),
            "mapping_status_counts": dict(sorted(Counter(row["mapping_status"] for row in token_rows).items())),
            "pair_status_counts": dict(sorted(Counter(pair["status"] for pair in pairs).items())),
            "finding_counts": dict(sorted(findings.items())),
        },
        "tokens": token_rows,
        "pairs": pairs,
        "unpaired_promotions": unpaired,
    }


def _number(value):
    return "—" if value is None else f"{value:.0f}"


def render_markdown(report):
    summary = report["summary"]
    lines = [
        "# Promotion replacement superiority audit",
        "",
        "**REVIEW ONLY.** Replacement pairs are taken from authored negative "
        "promotion prerequisites and explicit shared-token dispositions. This "
        "receipt does not remove `^PromotionUnitBuff`, edit costs or YAML, "
        "apply a global strict-superiority rule, or certify gameplay balance.",
        "",
        "## Scope",
        "",
        f"- Promotion tokens: **{summary['promotion_tokens']}**; tokens with an explicit base-disable marker: **{summary['promotion_tokens_with_base_marker']}**.",
        f"- Promotion consumers: **{summary['promotion_units']}**; explicit replacement pairs evaluated: **{summary['replacement_pairs']}**; additional shared-token options excluded from pair comparisons: **{summary['additional_options_excluded_from_pairs']}**.",
        f"- Promotion consumers without a base-disable marker: **{summary['promotion_units_without_base_marker']}**. These remain mapping/design questions.",
        "- HP, speed, armor and cost use the resolved active ruleset. Weapon identity, range, nominal DPS and class labels come from one selected factory-state offensive record in the hashed balance ledger. Point defense and utility slots are excluded; ledger armaments are hash-disclosed rather than independently reconstructed here.",
        "",
        "## Replacement pairs",
        "",
        "| faction | base → promotion | selected weapons | HP | speed | range | nominal DPS | armor | warhead labels | status | findings |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for pair in report.get("pairs", []):
        c = pair["comparisons"]
        def mark(metric):
            return c[metric].get("status", "—")
        findings = "; ".join(pair.get("findings") or []) or "—"
        lines.append(
            f"| `{pair['faction']}` | `{pair['base_actor']}` → `{pair['promotion_actor']}` | "
            f"`{pair['base'].get('primary_weapon') or '—'}` → `{pair['promotion'].get('primary_weapon') or '—'}` | "
            f"{mark('hp')} ({_number(pair['base'].get('hp'))}→{_number(pair['promotion'].get('hp'))}) | "
            f"{mark('speed')} ({_number(pair['base'].get('speed'))}→{_number(pair['promotion'].get('speed'))}) | "
            f"{mark('range')} ({_number(pair['base'].get('range'))}→{_number(pair['promotion'].get('range'))}) | "
            f"{mark('dps')} ({_number(pair['base'].get('dps'))}→{_number(pair['promotion'].get('dps'))}) | "
            f"{mark('armor')} ({pair['base'].get('armor') or '—'}→{pair['promotion'].get('armor') or '—'}) | "
            f"{mark('warhead_class')} | {pair['status']} | {findings} |"
        )
    lines += [
        "",
        "## Promotion consumers outside an explicit replacement pair",
        "",
        "| faction | promotion token | promotion unit | reason |",
        "|---|---|---|---|",
    ]
    for row in report.get("unpaired_promotions", []):
        lines.append(f"| `{row['faction']}` | `{row['promotion_token']}` | `{row['promotion_unit']}` | {row['reason']} |")
    lines += [
        "",
        "This list is not a claim that these units are wrong. It separates consumers with no base marker from additional options that share a token with a genuine replacement, preventing false harvester-to-soldier, commando-to-aircraft and commando-to-vehicle comparisons.",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        out = diagnostic_output.validate_path(ROOT, args.out)
        markdown = diagnostic_output.validate_path(ROOT, args.markdown)
        if out == markdown:
            raise ValueError("JSON and Markdown outputs must be different paths")
        tool = Path(__file__).resolve()
        report = build_report(tool_path=tool)
        report["inputs"]["tool_sha256"] = hashlib.sha256(tool.read_bytes()).hexdigest()
        diagnostic_output.write_outputs(ROOT, {
            out: json.dumps(report, indent=2, sort_keys=True) + "\n",
            markdown: render_markdown(report),
        })
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
