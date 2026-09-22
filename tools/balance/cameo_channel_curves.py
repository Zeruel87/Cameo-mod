#!/usr/bin/env python3
"""Review-only current Cameo weapon HP curves; no stat or gameplay writeback."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import sys
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))
from miniyaml import Ruleset  # noqa: E402
import armor_projection  # noqa: E402
import diagnostic_output  # noqa: E402
import effective_heaviness as eh  # noqa: E402
import percentage_damage as pd  # noqa: E402

MATRIX_DEFAULT = (Path(r"C:\Users\Blackrobe\Documents\agents\cameo-reference-sources-20260909") /
                  "validation/four-faction-sunday-pilot/warhead-reference-freshness/"
                  "pilot-warhead-review.json")
ARMOR_AXES = ("None", "Wood", "Concrete", "Scout", "Light", "Medium", "Heavy", "Superheavy")
SCENARIOS = ("infantry", "vehicle", "ordinary_building", "aircraft", "ship")
TARGET_TYPES = {
    "infantry": {"Ground", "Infantry"},
    "vehicle": {"Ground", "Vehicle"},
    "ordinary_building": {"Ground", "Structure", "Building"},
    "aircraft": {"Air", "Aircraft"},
    "ship": {"Ground", "Water", "Ship"},
}
DEFAULT_VALID_TARGETS = {"Ground", "Water"}
DEFAULT_INVALID_TARGETS = set()
DEFAULT_VALID_RELATIONSHIPS = {"Ally", "Neutral", "Enemy"}
DEFAULT_INVALID_RELATIONSHIPS = set()
RELATIONSHIP = "Enemy"
SELECTION_MODE = "collateral"
NON_HP_TYPES = {"AffectsIntegrity", "DamagesConcrete"}
FLAT_TYPES = {"AreaDamage", "SpreadDamage", "TargetDamage"}
PERCENTAGE_TYPES = {"AreaDamagePercentage", "HealthPercentageDamage"}
SPECIAL_POSITIVE_TYPES = {"FireShrapnel"}
OPEN_TOPPED_TYPE = "OpenToppedDamage"
TOOL_FILES = (
    "tools/balance/cameo_channel_curves.py",
    "tools/balance/armor_projection.py",
    "tools/balance/diagnostic_output.py",
    "tools/balance/effective_heaviness.py",
    "tools/balance/percentage_damage.py",
    "tools/audit/miniyaml.py",
)


def _finite(value):
    if isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _field_map(node):
    return {child.key: child.value for child in node.children
            if not child.key.startswith("Inherits")}


def channel_row(actor, slot, weapon, node):
    """Export one resolved warhead node without changing the source node."""
    fields = _field_map(node)
    return {"source": "Cameo", "actor": actor, "slot": slot, "weapon": weapon,
            "warhead": node.key, "warhead_type": node.value,
            "damage": node.get("Damage"), "fields": fields}


def _zero_terms():
    return {axis: {"flat": 0.0, "max_hp_fraction": 0.0, "A": 0.0, "B": 0.0}
            for axis in ARMOR_AXES}


def _armor_value(table, axis):
    if not isinstance(table, Mapping):
        return 100.0
    raw = table.get(axis, 100.0)
    value = _finite(raw)
    return value if value is not None else None


def _first_falloff(node):
    raw = node.get("Falloff")
    if raw is None:
        return 1.0, None
    values = [value.strip() for value in str(raw).replace(";", ",").split(",")]
    first = _finite(values[0]) if values and values[0] else None
    if first is None:
        return None, "falloff_nonfinite_or_nonnumeric"
    return first / 100.0, None


def _area_versus(node):
    table = pd.versus_table(node)
    mode = eh.heaviness_mode_of(node)
    heaviness = eh.heaviness_of(node)
    if mode == eh.MODE_SHARED:
        return eh.shared_versus_profile(table, heaviness)
    return eh.versus_profile(table, heaviness)


def _state_value(node, field):
    return node.get(field)


def _percentage_application_map(applications):
    return {id(application["node"]): application for application in applications}


def _application_evidence(application):
    return {key: value for key, value in application.items() if key != "node"}


def _unmodeled_shape(node):
    values = {field: node.get(field) for field in ("Ticks", "TickDelay", "MaxRadius")}
    return {key: value for key, value in values.items() if value is not None}


def _channel_term_base(node, row):
    return {"identity": armor_projection.channel_identity(row), "channel": row,
            "warhead_type": node.value, "shape": _unmodeled_shape(node)}


def _amount_value(node):
    raw = node.get("Amount")
    if raw is None or str(raw).strip() == "":
        return -1, None
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return None, "amount_noninteger"
    return value, None


def compile_selected_nodes(nodes, rows, applications):
    """Compile selected HP payloads, withholding the whole total on errors."""
    terms = _zero_terms()
    channel_terms, errors, passenger_payloads = [], [], []
    application_map = _percentage_application_map(applications)
    for node, row in zip(nodes, rows):
        item = _channel_term_base(node, row)
        kind = node.value
        if kind == OPEN_TOPPED_TYPE:
            damage = _finite(node.get("Damage"))
            amount, amount_error = _amount_value(node)
            if damage is None or damage < 0:
                reason = "open_topped_damage_invalid"
                item.update(status="UNRESOLVED", damage=node.get("Damage"), reason=reason)
                channel_terms.append(item)
                errors.append(f"{node.key}:{reason}")
                continue
            if amount_error:
                item.update(status="UNRESOLVED", damage=damage, reason=amount_error)
                channel_terms.append(item)
                errors.append(f"{node.key}:{amount_error}")
                continue
            payload = {
                "type": "passenger_damage",
                "status": "UNRESOLVED_PASSENGER_HP",
                "identity": armor_projection.channel_identity(row),
                "warhead": node.key,
                "damage": damage,
                "damage_raw": node.get("Damage"),
                "versus": pd.versus_table(node),
                "versus_raw": node.get("Versus"),
                "amount": amount,
                "amount_raw": node.get("Amount"),
                "amount_semantics": ("default -1 means all; positive Amount below the runtime "
                                     "passenger count selects a random subset; otherwise all"),
                "modifier_caveat": "Passenger damage receives runtime damage modifiers and passenger armor-versus; carrier armor is not applied here.",
                "requires_dynamic_passenger_population": True,
                "carrier_hp_contribution": 0.0,
            }
            passenger_payloads.append(payload)
            item.update(status="PASSENGER_HP_UNRESOLVED", damage=damage,
                        passenger_payload=payload)
            channel_terms.append(item)
            continue
        if kind in SPECIAL_POSITIVE_TYPES:
            reason = "fire_shrapnel_payload_unresolved"
            item.update(status="UNRESOLVED", damage=node.get("Damage"), reason=reason)
            channel_terms.append(item)
            errors.append(f"{node.key}:{reason}")
            continue
        damage = _finite(node.get("Damage"))
        if damage is None:
            reason = "damage_missing_or_nonfinite"
            item.update(status="UNRESOLVED", reason=reason)
            channel_terms.append(item)
            errors.append(f"{node.key}:{reason}")
            continue
        if damage < 0:
            reason = "negative_or_healing_damage"
            item.update(status="UNRESOLVED", damage=damage, reason=reason)
            channel_terms.append(item)
            errors.append(f"{node.key}:{reason}")
            continue
        if kind in SPECIAL_POSITIVE_TYPES or (kind not in FLAT_TYPES | PERCENTAGE_TYPES
                                              and damage > 0):
            reason = f"unsupported_positive_warhead_type:{kind}"
            item.update(status="UNRESOLVED", damage=damage, reason=reason)
            channel_terms.append(item)
            errors.append(f"{node.key}:{reason}")
            continue
        if kind not in FLAT_TYPES | PERCENTAGE_TYPES:
            item.update(status="EXCLUDED", damage=damage,
                        reason="status_or_non_hp_effect_outside_hp_scope")
            channel_terms.append(item)
            continue
        if damage == 0:
            item.update(status="ZERO", damage=damage)
            channel_terms.append(item)
            continue

        if kind == "AreaDamage":
            versus = _area_versus(node)
        else:
            versus = pd.versus_table(node)
        falloff = 1.0
        if kind in ("AreaDamage", "SpreadDamage", "AreaDamagePercentage"):
            falloff, falloff_error = _first_falloff(node)
            if falloff_error:
                item.update(status="UNRESOLVED", damage=damage, reason=falloff_error)
                channel_terms.append(item)
                errors.append(f"{node.key}:{falloff_error}")
                continue
        flat_terms = {axis: 0.0 for axis in ARMOR_AXES}
        percentage_terms = {axis: 0.0 for axis in ARMOR_AXES}
        if kind in FLAT_TYPES:
            for axis in ARMOR_AXES:
                coefficient = _armor_value(versus, axis)
                if coefficient is None:
                    errors.append(f"{node.key}:versus_nonfinite_or_nonnumeric:{axis}")
                    continue
                flat_terms[axis] = damage * falloff * coefficient / 100.0
                terms[axis]["flat"] += flat_terms[axis]
                terms[axis]["A"] += flat_terms[axis]

        application = application_map.get(id(node))
        if kind in PERCENTAGE_TYPES or application is not None:
            if application is None:
                reason = "percentage_application_unresolved"
                item.update(status="UNRESOLVED", damage=damage, reason=reason)
                channel_terms.append(item)
                errors.append(f"{node.key}:{reason}")
                continue
            table = application.get("versus") or {}
            # The runtime-rounded units are the current source basis for the
            # HP term. Continuous units remain in the evidence below so the
            # quantisation difference is visible rather than silently lost.
            units = _finite(application.get("runtime_units"))
            continuous_units = _finite(application.get("continuous_units"))
            denominator = _finite(application.get("denominator"))
            if (units is None or continuous_units is None or denominator is None
                    or denominator <= 0):
                reason = "percentage_application_nonfinite_or_invalid"
                item.update(status="UNRESOLVED", damage=damage, reason=reason)
                channel_terms.append(item)
                errors.append(f"{node.key}:{reason}")
                continue
            percentage_falloff = (falloff if kind == "AreaDamage" or
                                  kind == "AreaDamagePercentage" else 1.0)
            for axis in ARMOR_AXES:
                coefficient = _armor_value(table, axis)
                if coefficient is None:
                    errors.append(f"{node.key}:percentage_versus_nonfinite_or_nonnumeric:{axis}")
                    continue
                percentage_terms[axis] = (units / denominator * percentage_falloff
                                          * coefficient / 100.0)
                terms[axis]["max_hp_fraction"] += percentage_terms[axis]
                terms[axis]["B"] += percentage_terms[axis]
        item.update(status="RESOLVED", damage=damage, flat_terms=flat_terms,
                    percentage_terms=percentage_terms, versus=versus,
                    falloff_fraction=falloff,
                    percentage_application=(_application_evidence(application)
                                             if application is not None else None),
                    percentage_units_basis=("runtime_units" if application is not None
                                             else None))
        channel_terms.append(item)

    if errors:
        return {"status": "UNRESOLVED", "terms": None,
                "channel_terms": channel_terms, "reason": ";".join(errors),
                "additional_target_payloads": passenger_payloads}
    if passenger_payloads:
        return {"status": "RESOLVED_PRIMARY_TARGET", "terms": terms,
                "channel_terms": channel_terms,
                "additional_target_payloads": passenger_payloads,
                "full_effect_resolved": False,
                "reason": "Primary target/carrier HP is resolved; passenger HP remains unresolved."}
    return {"status": "RESOLVED", "terms": terms, "channel_terms": channel_terms}


def _record_base(actor, armament, slot, weapon, scenario, target_types):
    return {
        "actor": actor, "slot": slot, "weapon": weapon, "scenario": scenario,
        "pricing": armament.get("pricing"), "requires": armament.get("requires"),
        "armament_metadata": armament, "target_types": sorted(target_types),
        "relationship": RELATIONSHIP, "selection_mode": SELECTION_MODE,
    }


def compile_armament(actor, armament, actor_node, weapon_node):
    slot = armament.get("slot")
    weapon = armament.get("weapon")
    records = []
    slot_node = actor_node.child(slot) if actor_node is not None and slot else None
    authored_weapon = slot_node.get("Weapon") if slot_node is not None else None
    mismatch = None
    if actor_node is None:
        mismatch = "actor_unresolved"
    elif slot_node is None:
        mismatch = "actor_slot_unresolved"
    elif authored_weapon != weapon:
        mismatch = f"actor_slot_weapon_mismatch:{authored_weapon}!={weapon}"
    elif weapon_node is None:
        mismatch = "weapon_unresolved"
    nodes = list(weapon_node.children) if weapon_node is not None else []
    nodes = [node for node in nodes if node.key.startswith("Warhead")]
    rows = [channel_row(actor, slot, weapon, node) for node in nodes]
    try:
        applications = pd.percentage_applications(weapon_node, 1) if weapon_node else []
        application_error = None
    except (TypeError, ValueError, OverflowError) as error:
        applications, application_error = [], f"percentage_application_error:{error}"
    for scenario in SCENARIOS:
        target_types = TARGET_TYPES[scenario]
        record = _record_base(actor, armament, slot, weapon, scenario, target_types)
        record["resolved_actor_weapon"] = authored_weapon
        record["input_channels"] = rows
        if mismatch:
            record.update(status="UNRESOLVED", terms=None, selected_channels=[],
                          excluded_channels=[], reason=mismatch)
            records.append(record)
            continue
        if application_error:
            record.update(status="UNRESOLVED", terms=None, selected_channels=rows,
                          excluded_channels=[], reason=application_error)
            records.append(record)
            continue
        selection = armor_projection.select_channels(
            rows,
            active_slots={slot}, target_types=target_types, relationship=RELATIONSHIP,
            default_valid_targets=DEFAULT_VALID_TARGETS,
            default_invalid_targets=DEFAULT_INVALID_TARGETS,
            default_valid_relationships=DEFAULT_VALID_RELATIONSHIPS,
            default_invalid_relationships=DEFAULT_INVALID_RELATIONSHIPS,
            weapon_valid_target_mode=SELECTION_MODE)
        selected_rows, selected_nodes = [], []
        non_hp_excluded = []
        node_by_warhead = {node.key: node for node in nodes}
        for row in selection["selected"]:
            node = node_by_warhead[row["warhead"]]
            damage = _finite(node.get("Damage"))
            if node.value in NON_HP_TYPES:
                non_hp_excluded.append({"channel": row, "reason": f"{node.value.lower()}_outside_hp_scope"})
                continue
            if node.value not in SPECIAL_POSITIVE_TYPES and damage is None:
                non_hp_excluded.append({"channel": row, "reason": "status_or_non_hp_effect_outside_hp_scope"})
                continue
            selected_rows.append(row)
            selected_nodes.append(node)
        excluded = list(selection["excluded"]) + non_hp_excluded
        record.update(selection=selection["selection"], selected_channels=selection["selected"],
                      excluded_channels=excluded, excluded_non_hp_channels=non_hp_excluded)
        if not selected_nodes:
            reasons = sorted({entry["reason"] for entry in excluded})
            record.update(status="NOT_APPLICABLE", terms=_zero_terms(),
                          reason="all channels excluded from this target state"
                          + ((": " + ";".join(reasons)) if reasons else ""))
            records.append(record)
            continue
        reduced = compile_selected_nodes(selected_nodes, selected_rows, applications)
        record.update(reduced)
        records.append(record)
    return records


def _relative(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(Path(path).resolve())


def active_input_paths(rules):
    return sorted(set(rules.manifest.sources + rules.manifest.rules + rules.manifest.weapons),
                  key=lambda path: str(path))


def input_fingerprints(matrix_path, rules):
    paths = {name: ROOT / Path(name) for name in TOOL_FILES}
    paths.update({_relative(path): path for path in active_input_paths(rules)})
    paths[_relative(matrix_path)] = Path(matrix_path)
    return {"files_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
                             for name, path in sorted(paths.items())}}


def validate_matrix(matrix):
    if not isinstance(matrix, Mapping) or not isinstance(matrix.get("rows"), list):
        raise ValueError("matrix.rows must be a list")
    for index, item in enumerate(matrix["rows"]):
        if not isinstance(item, Mapping) or not item.get("actor"):
            raise ValueError(f"matrix.rows[{index}] needs an actor")
        if "cameo_channels" in item and not isinstance(item["cameo_channels"], list):
            raise ValueError(f"matrix.rows[{index}].cameo_channels must be a list")
    return matrix


def build(matrix, rules, *, provenance=None, matrix_path=None):
    validate_matrix(matrix)
    records = []
    actor_cache = {}
    for item in matrix["rows"]:
        actor = item["actor"]
        actor_node = actor_cache.setdefault(actor, rules.resolve(actor))
        armaments = item.get("cameo_channels") or []
        if not armaments:
            records.append({"actor": actor, "scenario": None, "slot": None, "weapon": None,
                            "status": "NO_ARMAMENT", "terms": None,
                            "reason": "actor has no matrix cameo_channels; no whole-unit zero inferred",
                            "armament_metadata": [], "input_channels": []})
            continue
        for armament in armaments:
            weapon = armament.get("weapon")
            weapon_node = rules.resolve_weapon(weapon) if weapon else None
            records.extend(compile_armament(actor, armament, actor_node, weapon_node))
    status_counts = collections.Counter(record["status"] for record in records)
    result = {
        "schema": 1,
        "scope": "Current Cameo raw weapon HP curves by actor, armament, weapon and state; no target-state guarantee, cadence, incoming mitigation, gameplay certification or writeback.",
        "method": [
            "Each matrix cameo armament is resolved against the active actor slot and weapon; requires/pricing metadata remain labels and are not evaluated into simultaneous fire.",
            "Target scenarios use current Cameo abstract masks: Ground+Infantry, Ground+Vehicle, Ground+Structure+Building, Air+Aircraft and Ground+Water+Ship. Selection is collateral impact against Enemy and is not attack acquisition proof.",
            "AreaDamage and SpreadDamage flat terms use authored Damage, first Falloff and the existing effective-heaviness helper; TargetDamage uses direct Damage with missing armor default100.",
            "Folded and standalone percentage applications come from percentage_damage.percentage_applications; percentage Damage is never added to flat Damage. Folded/AreaDamagePercentage use first Falloff, HealthPercentageDamage does not.",
            "Ticks, TickDelay and MaxRadius remain caveats; AreaDamage Damage is not multiplied by Ticks. Unsupported selected positive payloads withhold the whole scenario total.",
            "OpenToppedDamage contributes zero to primary carrier HP and remains a separately unresolved passenger_damage payload; passenger population, armor and runtime modifiers are not inferred.",
            "This passenger disposition follows OpenRA.Mods.AS/Warheads/OpenToppedDamageWarhead.cs and INotifyPassengersDamage implementations in Cargo, Garrisonable and SharedCargo; the source calls passenger InflictDamage and never carrier InflictDamage.",
        ],
        "armor_axes": list(ARMOR_AXES),
        "scenario_target_types": {scenario: sorted(values) for scenario, values in TARGET_TYPES.items()},
        "defaults": {"valid_targets": sorted(DEFAULT_VALID_TARGETS),
                     "invalid_targets": sorted(DEFAULT_INVALID_TARGETS),
                     "valid_relationships": sorted(DEFAULT_VALID_RELATIONSHIPS),
                     "invalid_relationships": sorted(DEFAULT_INVALID_RELATIONSHIPS),
                     "relationship": RELATIONSHIP, "selection_mode": SELECTION_MODE},
        "summary": {"actors": len(matrix["rows"]), "records": len(records),
                    "status_counts": dict(sorted(status_counts.items()))},
        "records": records,
    }
    if provenance is not None:
        result.update({"matrix_path": str(matrix_path) if matrix_path else None,
                       "matrix_sha256": provenance["files_sha256"].get(_relative(matrix_path)),
                       "input_fingerprints_before": provenance})
    return result


def build_from_path(matrix_path):
    matrix_path = Path(matrix_path).resolve()
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    rules = Ruleset(ROOT)
    before = input_fingerprints(matrix_path, rules)
    result = build(matrix, rules, provenance=before, matrix_path=matrix_path)
    after = input_fingerprints(matrix_path, rules)
    if after != before:
        raise ValueError("matrix, active Cameo rules, or helper inputs changed during collection")
    result["input_fingerprints_after"] = after
    result["input_guard"] = {"before": before, "after": after, "unchanged": True}
    return result


def _fmt(value):
    if value is None:
        return "—"
    try:
        return f"{float(value):.4g}"
    except (TypeError, ValueError):
        return str(value)


def _terms_text(terms):
    if terms is None:
        return "—"
    return "; ".join(f"{axis}: A={_fmt(values.get('A'))}, B={_fmt(values.get('B'))}"
                      for axis, values in terms.items())


def _passenger_text(payloads):
    return "; ".join(
        f"passenger_damage {payload.get('warhead')}: damage={_fmt(payload.get('damage'))}, "
        f"Amount={payload.get('amount')} (carrier contribution 0; passenger HP unresolved)"
        for payload in payloads or ())


def render_markdown(result):
    summary = result.get("summary") or {}
    lines = [
        "# Current Cameo channel curve review", "",
        "**Review-only diagnostic.** Actor armaments and alternate states remain separate. Values are authored continuous HP arithmetic and do not certify full combat equivalence, cadence, geometry, incoming mitigation or runtime target state.",
        "", "## Summary", "",
        f"- Actors: **{summary.get('actors', 0)}**; records: **{summary.get('records', 0)}**; statuses: **{summary.get('status_counts', {})}**.",
        "- AreaDamage Damage is not multiplied by Ticks. Ticks, TickDelay and MaxRadius remain visible in JSON channel evidence only.",
        "- Percentage applications are folded or standalone according to the existing percentage helper; raw percentage Damage is never counted as flat HP.",
        "- OpenToppedDamage is shown as primary-target-only with an unresolved passenger payload; the weapon is not labeled fully resolved.",
        "", "## Scenario records", "",
        "| actor | slot | weapon | pricing | requires | scenario | status | terms or reason |",
        "|---|---|---|:---:|---|---|---|---|",
    ]
    for record in result.get("records", []):
        metadata = record.get("armament_metadata") or {}
        reason = record.get("reason") or _terms_text(record.get("terms"))
        passenger = _passenger_text(record.get("additional_target_payloads"))
        if passenger:
            reason = f"{reason} | {passenger}"
        state = str(record.get("requires") or "—").replace("|", "\\|")
        reason = str(reason).replace("|", "\\|")
        lines.append(f"| {record.get('actor', '—')} | {record.get('slot', '—')} | {record.get('weapon', '—')} | {metadata.get('pricing', record.get('pricing', '—'))} | {state} | {record.get('scenario', '—')} | {record.get('status', '—')} | {reason} |")
    lines += ["", "No armament record is treated as whole-unit zero; death, abilities and unmodeled payloads remain separate scope."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--matrix", type=Path, default=MATRIX_DEFAULT)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)
    try:
        out_path = diagnostic_output.validate_path(ROOT, args.out)
        markdown_path = (diagnostic_output.validate_path(ROOT, args.markdown)
                         if args.markdown else None)
        if markdown_path is not None and markdown_path == out_path:
            raise ValueError("JSON and Markdown outputs must use different resolved paths")
        matrix_path = args.matrix.resolve()
        if not matrix_path.is_file():
            raise ValueError(f"matrix file does not exist: {matrix_path}")
        result = build_from_path(matrix_path)
        outputs = {out_path: json.dumps(result, ensure_ascii=False, indent=2,
                                        allow_nan=False) + "\n"}
        if markdown_path is not None:
            outputs[markdown_path] = render_markdown(result)
        diagnostic_output.write_outputs(ROOT, outputs)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(result["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
