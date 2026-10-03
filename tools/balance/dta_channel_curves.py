#!/usr/bin/env python3
"""Review-only DTA source-basis channel damage; no target or stat writeback."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
from collections.abc import Mapping
from pathlib import Path

import diagnostic_output

ROOT = Path(__file__).resolve().parents[2]
ARMOR_EVIDENCE_PATH = ROOT / "docs/reference/dta_armor_evidence.json"
PAYLOAD_EVIDENCE_PATH = ROOT / "docs/reference/dta_additional_payload_evidence.json"
MATRIX_DEFAULT = (Path(r"C:\Users\Blackrobe\Documents\agents\cameo-reference-sources-20260909") /
                  "validation/four-faction-sunday-pilot/warhead-reference-freshness/"
                  "pilot-warhead-review.json")
SOURCE = "DTA Enhanced"
SCENARIO = "eligible_unobstructed_impact"
ARMOR_AXES = ("None", "Wood", "Concrete", "Light", "Heavy")
DTA_ARMOR_KEYS = dict(zip(ARMOR_AXES, ("none", "wood", "concrete", "light", "heavy")))
TOOL_FILES = (
    "tools/balance/dta_channel_curves.py",
    "tools/balance/diagnostic_output.py",
)
MODELED_FIELDS = {
    "damage", "ambientdamage", "israilgun", "attachedparticlesystem",
    "spawner", "suicide",
}


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _field(channel, name):
    aliases = {name.lower(), name.replace("_", "").lower()}
    containers = []
    if isinstance(channel, Mapping) and isinstance(channel.get("fields"), Mapping):
        containers.append(channel["fields"])
    if isinstance(channel, Mapping):
        containers.append(channel)
    for container in containers:
        for key, value in container.items():
            if str(key).replace("_", "").lower() in aliases:
                return True, value
    return False, None


def _finite(value):
    if isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _flag(value):
    if isinstance(value, bool):
        return value, None
    if value is None:
        return False, None
    text = str(value).strip().lower()
    if text in ("yes", "true", "1"):
        return True, None
    if text in ("no", "false", "0", ""):
        return False, None
    return False, "flag_nonfinite_or_unknown"


def load_armor_evidence():
    document = json.loads(ARMOR_EVIDENCE_PATH.read_text(encoding="utf-8"))
    if document.get("schema") != 1 or document.get("source") != SOURCE:
        raise ValueError("unsupported DTA armor evidence document")
    if not isinstance(document.get("profiles"), Mapping):
        raise ValueError("DTA armor evidence has no profiles")
    return document


def load_payload_evidence():
    document = json.loads(PAYLOAD_EVIDENCE_PATH.read_text(encoding="utf-8"))
    if document.get("schema") != 1 or not isinstance(document.get("particle_systems"), Mapping):
        raise ValueError("unsupported DTA additional-payload evidence document")
    if not isinstance(document.get("retained_weapon_systems"), Mapping):
        raise ValueError("DTA additional-payload evidence has no weapon bindings")
    return document


def proof_binding(matrix, armor_evidence, payload_evidence):
    """Match the matrix's retained DTA inputs to both reviewed proof documents."""
    source_export = (matrix.get("export_sha256") or {}).get(SOURCE)
    if not isinstance(source_export, Mapping):
        return {"status": "UNRESOLVED", "reason": "missing_dta_matrix_export_proof"}
    rules = source_export.get("rules_sha256")
    enhance = source_export.get("enhance_sha256")
    armor_inputs = armor_evidence.get("inputs") or {}
    payload_inputs = payload_evidence.get("input_sha256") or {}
    reasons = []
    for label, actual, expected in (
        ("Rules.ini", rules, armor_inputs.get("Rules.ini")),
        ("Enhance.ini", enhance, armor_inputs.get("Enhance.ini")),
        ("Rules.ini payload", rules, payload_inputs.get("Rules.ini")),
        ("Enhance.ini payload", enhance, payload_inputs.get("Enhance.ini")),
    ):
        if not actual or actual != expected:
            reasons.append(f"dta_proof_hash_mismatch:{label}")
    armor_hash = source_export.get("armor_fallback_evidence_sha256")
    actual_armor_hash = _sha256(ARMOR_EVIDENCE_PATH)
    if armor_hash != actual_armor_hash:
        reasons.append("dta_proof_hash_mismatch:dta_armor_evidence")
    if reasons:
        return {"status": "UNRESOLVED", "reason": ";".join(reasons),
                "rules_sha256": rules, "enhance_sha256": enhance,
                "armor_evidence_sha256": actual_armor_hash,
                "payload_evidence_sha256": _sha256(PAYLOAD_EVIDENCE_PATH)}
    return {
        "status": "MATCHED", "rules_sha256": rules, "enhance_sha256": enhance,
        "armor_evidence_sha256": actual_armor_hash,
        "payload_evidence_sha256": _sha256(PAYLOAD_EVIDENCE_PATH),
        "armor_evidence_path": str(ARMOR_EVIDENCE_PATH.relative_to(ROOT)),
        "payload_evidence_path": str(PAYLOAD_EVIDENCE_PATH.relative_to(ROOT)),
        "armor_source": armor_evidence.get("engine_source"),
        "payload_engine_commit": payload_evidence.get("engine_commit"),
        "derivation": "DTA resolved versus is admitted only against the reviewed Vinifera profiles and retained Rules/Enhance inputs.",
    }


def _profile_versus(channel, armor_evidence):
    warhead = channel.get("warhead")
    profile = (armor_evidence.get("profiles") or {}).get(warhead)
    if not isinstance(profile, Mapping):
        return {}, [f"armor_profile_missing:{warhead}"]
    resolved = channel.get("resolved_versus")
    if not isinstance(resolved, Mapping):
        return {}, ["resolved_versus_missing"]
    values, errors = {}, []
    for axis, dta_key in DTA_ARMOR_KEYS.items():
        if dta_key not in resolved:
            errors.append(f"resolved_versus_missing:{dta_key}")
            continue
        actual = _finite(resolved[dta_key])
        expected_entry = profile.get(dta_key)
        expected = (_finite(expected_entry.get("percent"))
                    if isinstance(expected_entry, Mapping) else None)
        if actual is None or expected is None:
            errors.append(f"resolved_versus_nonfinite:{dta_key}")
            continue
        if actual != expected:
            errors.append(f"resolved_versus_profile_mismatch:{dta_key}:{actual}!={expected}")
            continue
        values[axis] = actual
    return values, errors


def _zero_terms():
    return {axis: {"A": 0.0, "B": 0.0, "direct": 0.0, "ambient": 0.0}
            for axis in ARMOR_AXES}


def _terms(direct, ambient):
    return {axis: {"A": direct[axis] + ambient[axis], "B": 0.0,
                   "direct": direct[axis], "ambient": ambient[axis]}
            for axis in ARMOR_AXES}


def _payload_particle(weapon, channel, payload_evidence):
    present, attached = _field(channel, "AttachedParticleSystem")
    if not present or attached is None or str(attached).strip() == "":
        return None, None
    attached = str(attached).strip()
    expected = (payload_evidence.get("retained_weapon_systems") or {}).get(weapon)
    systems = payload_evidence.get("particle_systems") or {}
    system = systems.get(attached)
    if expected != attached:
        return None, f"attached_particle_binding_mismatch:{weapon}:{attached}"
    if not isinstance(system, Mapping):
        return None, f"attached_particle_system_unknown:{attached}"
    additional = _finite(system.get("additional_hp_damage"))
    if additional is None or additional != 0:
        return None, f"attached_particle_additional_damage_unresolved:{attached}"
    return {"system": attached, "expected_system": expected,
            "behavior": system.get("behavior"), "held_behavior": system.get("held_behavior"),
            "additional_hp_damage": additional}, None


def _unmodeled_fields(channel):
    fields = channel.get("fields") if isinstance(channel, Mapping) else None
    if not isinstance(fields, Mapping):
        return []
    return sorted(key for key in fields if str(key).replace("_", "").lower() not in MODELED_FIELDS)


def _collapse_trace_duplicates(channels):
    """Collapse identical trace visits; retain conflicting same-identity rows as unresolved."""
    by_identity = collections.defaultdict(list)
    order = []
    for channel in channels:
        identity = (channel.get("weapon"), channel.get("warhead"))
        if identity not in by_identity:
            order.append(identity)
        by_identity[identity].append(channel)
    retained, trace = [], []
    for weapon_warhead in order:
        rows = by_identity[weapon_warhead]
        if len(rows) == 1:
            retained.append(rows[0])
            continue
        identical = all(row == rows[0] for row in rows[1:])
        note = ("aggregate_archetype.trace_ini visited multiple actor slots; identical rows are "
                "one declared weapon/warhead payload and are not summed.")
        trace.append({"weapon": weapon_warhead[0], "warhead": weapon_warhead[1],
                      "original_count": len(rows), "retained_count": 1 if identical else 0,
                      "status": "COLLAPSED" if identical else "UNRESOLVED",
                      "note": note if identical else
                      "same weapon/warhead identity has nonidentical exported rows; no payload is summed."})
        if not identical:
            return None, trace
        retained.append(rows[0])
    return retained, trace


def reduce_weapon_channels(channels, *, armor_evidence, payload_evidence,
                           proof, weapon):
    """Reduce one DTA weapon's channels without folding direct and ambient evidence."""
    if not channels:
        return {"status": "UNRESOLVED", "terms": None, "reason": "missing_selected_channel_evidence",
                "channel_terms": [], "direct_components": [], "ambient_components": []}
    deduplicated, duplicate_trace = _collapse_trace_duplicates(channels)
    if deduplicated is None:
        return {"status": "UNRESOLVED", "terms": None,
                "reason": "same weapon/warhead identity has nonidentical duplicate entries",
                "duplicate_trace": duplicate_trace,
                "channel_terms": [{"channel": channel, "status": "UNRESOLVED",
                                   "reason": "same weapon/warhead identity has nonidentical duplicate entries"}
                                  for channel in channels],
                "direct_components": [], "ambient_components": []}
    channels = deduplicated
    if proof.get("status") != "MATCHED":
        reason = proof.get("reason") or "dta_proof_unresolved"
        return {"status": "UNRESOLVED", "terms": None, "reason": reason,
                "duplicate_trace": duplicate_trace,
                "channel_terms": [{"channel": channel, "status": "UNRESOLVED", "reason": reason}
                                  for channel in channels],
                "direct_components": [], "ambient_components": []}

    direct = {axis: 0.0 for axis in ARMOR_AXES}
    ambient = {axis: 0.0 for axis in ARMOR_AXES}
    channel_terms, direct_components, ambient_components, errors = [], [], [], []
    for channel in channels:
        identity = {"source": SOURCE, "actor": channel.get("actor"),
                    "slot": channel.get("slot"), "weapon": channel.get("weapon"),
                    "warhead": channel.get("warhead")}
        item = {"identity": identity, "channel": channel,
                "unmodeled_payload_fields": _unmodeled_fields(channel)}
        duplicate = next((entry for entry in duplicate_trace
                          if entry["weapon"] == weapon and entry["warhead"] == channel.get("warhead")
                          and entry["status"] == "COLLAPSED"), None)
        if duplicate:
            item["duplicate_count"] = duplicate["original_count"]
            item["duplicate_trace_note"] = duplicate["note"]
        damage_present, raw_damage = _field(channel, "Damage")
        damage = _finite(raw_damage) if damage_present else None
        if damage is None:
            reason = "damage_missing_or_nonfinite"
            item.update(status="UNRESOLVED", reason=reason)
            errors.append(f"{identity}:{reason}")
            channel_terms.append(item)
            continue
        if damage < 0:
            reason = "negative_or_healing_damage"
            item.update(status="UNRESOLVED", damage=damage, reason=reason)
            errors.append(f"{identity}:{reason}")
            channel_terms.append(item)
            continue
        railgun_present, raw_railgun = _field(channel, "IsRailgun")
        railgun, railgun_error = _flag(raw_railgun) if railgun_present else (False, None)
        if railgun_error:
            item.update(status="UNRESOLVED", damage=damage, reason=railgun_error)
            errors.append(f"{identity}:{railgun_error}")
            channel_terms.append(item)
            continue
        ambient_present, raw_ambient = _field(channel, "AmbientDamage")
        ambient_damage = _finite(raw_ambient) if ambient_present else None
        if railgun and not ambient_present:
            reason = "railgun_ambientdamage_missing"
            item.update(status="UNRESOLVED", damage=damage, reason=reason)
            errors.append(f"{identity}:{reason}")
            channel_terms.append(item)
            continue
        if ambient_present and ambient_damage is None:
            reason = "ambientdamage_missing_or_nonfinite"
            item.update(status="UNRESOLVED", damage=damage, reason=reason)
            errors.append(f"{identity}:{reason}")
            channel_terms.append(item)
            continue
        if ambient_damage is not None and ambient_damage < 0:
            reason = "negative_or_healing_ambientdamage"
            item.update(status="UNRESOLVED", damage=damage, reason=reason)
            errors.append(f"{identity}:{reason}")
            channel_terms.append(item)
            continue
        if not railgun and ambient_damage not in (None, 0.0):
            reason = "ambientdamage_without_railgun"
            item.update(status="UNRESOLVED", damage=damage, ambient_damage=ambient_damage,
                        reason=reason)
            errors.append(f"{identity}:{reason}")
            channel_terms.append(item)
            continue
        spawner_present, raw_spawner = _field(channel, "Spawner")
        spawner, spawner_error = _flag(raw_spawner) if spawner_present else (False, None)
        suicide_present, raw_suicide = _field(channel, "Suicide")
        suicide, suicide_error = _flag(raw_suicide) if suicide_present else (False, None)
        special_error = spawner_error or suicide_error
        if spawner:
            special_error = "spawner_payload_unresolved"
        if suicide:
            special_error = "suicide_payload_unresolved"
        if special_error:
            item.update(status="UNRESOLVED", damage=damage, reason=special_error)
            errors.append(f"{identity}:{special_error}")
            channel_terms.append(item)
            continue
        particle, particle_error = _payload_particle(weapon, channel, payload_evidence)
        if particle_error:
            item.update(status="UNRESOLVED", damage=damage, reason=particle_error)
            errors.append(f"{identity}:{particle_error}")
            channel_terms.append(item)
            continue
        versus, versus_errors = _profile_versus(channel, armor_evidence)
        if versus_errors:
            item.update(status="UNRESOLVED", damage=damage, reason=";".join(versus_errors),
                        versus=versus)
            errors.extend(f"{identity}:{error}" for error in versus_errors)
            channel_terms.append(item)
            continue
        ambient_value = ambient_damage if railgun else 0.0
        direct_terms = {axis: damage * versus[axis] / 100.0 for axis in ARMOR_AXES}
        ambient_terms = {axis: ambient_value * versus[axis] / 100.0 for axis in ARMOR_AXES}
        for axis in ARMOR_AXES:
            direct[axis] += direct_terms[axis]
            ambient[axis] += ambient_terms[axis]
        item.update(status="RESOLVED", damage=damage, ambient_damage=ambient_value,
                    is_railgun=railgun, versus=versus, direct_terms=direct_terms,
                    ambient_terms=ambient_terms, particle_evidence=particle,
                    ambient_application=("once_per_collected_target" if railgun else "none"))
        channel_terms.append(item)
        direct_components.append({"identity": identity, "damage": damage,
                                  "terms": direct_terms})
        if railgun:
            ambient_components.append({"identity": identity, "ambient_damage": ambient_value,
                                       "terms": ambient_terms,
                                       "application": "once_per_collected_target"})

    if errors:
        return {"status": "UNRESOLVED", "terms": None, "reason": "; ".join(errors),
                "duplicate_trace": duplicate_trace,
                "channel_terms": channel_terms, "direct_components": direct_components,
                "ambient_components": ambient_components}
    return {"status": "BASE_CHANNELS_RESOLVED", "terms": _terms(direct, ambient),
            "duplicate_trace": duplicate_trace,
            "channel_terms": channel_terms, "direct_components": direct_components,
            "ambient_components": ambient_components}


def _group_channels(channels):
    groups = collections.defaultdict(list)
    for channel in channels:
        groups[channel.get("weapon")].append(channel)
    return [(weapon, groups[weapon]) for weapon in sorted(groups, key=lambda value: "" if value is None else str(value))]


def build(matrix, *, armor_evidence=None, payload_evidence=None, proof=None,
          provenance=None, matrix_path=None):
    if not isinstance(matrix, Mapping) or not isinstance(matrix.get("rows"), list):
        raise ValueError("matrix.rows must be a list")
    armor_evidence = armor_evidence or {}
    payload_evidence = payload_evidence or {}
    proof = proof or {"status": "UNRESOLVED", "reason": "dta_proof_unresolved"}
    records = []
    for item in matrix["rows"]:
        for reference in item.get("references") or []:
            if reference.get("source") != SOURCE:
                continue
            channels = reference.get("selected_weapon_channels") or []
            for weapon, group in _group_channels(channels):
                reduced = reduce_weapon_channels(
                    group, armor_evidence=armor_evidence,
                    payload_evidence=payload_evidence, proof=proof, weapon=weapon)
                records.append({
                    "actor": item.get("actor"), "source": SOURCE,
                    "reference_id": reference.get("id"),
                    "selected_comparison_weapon": reference.get("selected_comparison_weapon"),
                    "weapon": weapon, "scenario": SCENARIO,
                    "scope": "eligible unobstructed impact; source basis only",
                    "input_channels": group, **reduced,
                })
            if not channels:
                records.append({
                    "actor": item.get("actor"), "source": SOURCE,
                    "reference_id": reference.get("id"),
                    "selected_comparison_weapon": reference.get("selected_comparison_weapon"),
                    "weapon": reference.get("selected_comparison_weapon"),
                    "scenario": SCENARIO,
                    "scope": "eligible unobstructed impact; source basis only",
                    "input_channels": [], "status": "UNRESOLVED", "terms": None,
                    "reason": "missing_selected_channel_evidence",
                    "channel_terms": [], "direct_components": [], "ambient_components": [],
                })
    status_counts = collections.Counter(record["status"] for record in records)
    result = {
        "schema": 1,
        "scope": "DTA Enhanced source-basis nominal damage before integer truncation; no target eligibility, cadence, geometry, secondary effects, installed-DLL certification or writeback.",
        "method": [
            "One record is emitted per DTA reference and selected weapon; multiple weapons and duplicate same-weapon/warhead rows are never silently merged.",
            "A direct component uses authored Damage x reviewed resolvedVersus / 100. A railgun ambient component uses AmbientDamage x reviewed resolvedVersus / 100 once per collected target; direct and ambient terms remain separate evidence.",
            "Only DTA Enhanced references are admitted. DTA armor axes are mapped explicitly from none/wood/concrete/light/heavy to None/Wood/Concrete/Light/Heavy; no fallback100 is invented.",
            "Smoke and railgun particles are admitted only through exact reviewed weapon-to-system bindings with zero additional HP damage. Spawner, Suicide, unknown particles and malformed payloads are unresolved.",
            "The result is continuous nominal source arithmetic for an eligible unobstructed impact, not a full combat-equivalence claim.",
        ],
        "armor_axes": list(ARMOR_AXES),
        "dta_armor_axis_keys": DTA_ARMOR_KEYS,
        "summary": {"records": len(records), "status_counts": dict(sorted(status_counts.items())),
                    "source": SOURCE, "scenario": SCENARIO},
        "records": records,
    }
    if provenance is not None:
        result.update({"matrix_sha256": provenance["matrix_sha256"],
                       "tool_sha256": provenance["tool_sha256"],
                       "dta_armor_evidence_sha256": provenance["dta_armor_evidence_sha256"],
                       "dta_payload_evidence_sha256": provenance["dta_payload_evidence_sha256"],
                       "matrix_path": str(matrix_path) if matrix_path else None})
    return result


def input_fingerprints(matrix_path):
    return {
        "matrix_sha256": _sha256(matrix_path),
        "tool_sha256": {name: _sha256(ROOT / Path(name)) for name in TOOL_FILES},
        "dta_armor_evidence_sha256": _sha256(ARMOR_EVIDENCE_PATH),
        "dta_payload_evidence_sha256": _sha256(PAYLOAD_EVIDENCE_PATH),
    }


def build_from_path(matrix_path):
    matrix_path = Path(matrix_path).resolve()
    before = input_fingerprints(matrix_path)
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    armor_evidence = load_armor_evidence()
    payload_evidence = load_payload_evidence()
    proof = proof_binding(matrix, armor_evidence, payload_evidence)
    result = build(matrix, armor_evidence=armor_evidence,
                   payload_evidence=payload_evidence, proof=proof,
                   provenance=before, matrix_path=matrix_path)
    result["dta_proof"] = proof
    after = input_fingerprints(matrix_path)
    if after != before:
        raise ValueError("matrix, tool or DTA evidence inputs changed during collection")
    result["input_guard"] = {"before": before, "after": after, "unchanged": True}
    return result


def _fmt(value):
    if value is None:
        return "—"
    return f"{float(value):.4g}"


def _component_text(record):
    terms = record.get("terms")
    if terms is None:
        return record.get("reason", "—")
    direct = ", ".join(f"{axis}={_fmt(values['direct'])}" for axis, values in terms.items())
    ambient = ", ".join(f"{axis}={_fmt(values['ambient'])}" for axis, values in terms.items())
    return f"direct A [{direct}] | ambient A [{ambient}] | B=0"


def render_markdown(result):
    summary = result.get("summary") or {}
    lines = [
        "# DTA source channel curve review", "",
        "**Review-only source basis.** Each row is an eligible unobstructed impact scenario for one DTA reference weapon. No target-mask decision, cadence, geometry, secondary effect or full combat-equivalence claim is made.",
        "", "## Summary", "",
        f"- Records: **{summary.get('records', 0)}**; statuses: **{summary.get('status_counts', {})}**.",
        "- DTA armor axes are `none/wood/concrete/light/heavy` mapped explicitly to `None/Wood/Concrete/Light/Heavy`; missing profile values remain unresolved.",
        "- Direct and railgun ambient components remain separate; ambient is applied once per collected target under the reviewed OpenTS rule.",
        "", "## Weapon records", "",
        "| actor | reference | weapon | scenario | status | direct/ambient terms or reason |", "|---|---|---|---|---|---|",
    ]
    for record in result.get("records", []):
        text = _component_text(record).replace("|", "\\|")
        lines.append(f"| {record.get('actor', '—')} | {record.get('reference_id', '—')} | {record.get('weapon', '—')} | {record.get('scenario', '—')} | {record.get('status', '—')} | {text} |")
    lines += ["", "All values are continuous nominal source arithmetic before integer truncation and remain diagnostic evidence only."]
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
