#!/usr/bin/env python3
"""Review-only source-channel armor terms from an exported pilot matrix.

This consumer selects one caller-reviewed armament state at a time, then
reduces selected OpenRA warheads to continuous nominal ``A + B * H`` terms.
It never evaluates conditions, averages sources, simulates hits or writes
gameplay/stat values.  The diagnostic output helper is preflighted and
non-overwriting, but a failed I/O operation can still leave an incomplete
batch of newly-created files.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
from collections.abc import Mapping
from pathlib import Path

import armor_projection
import diagnostic_output

ROOT = Path(__file__).resolve().parents[2]
PERCENTAGE_EVIDENCE_PATH = ROOT / "docs/reference/openra_percentage_armor_evidence.json"
CLAMPED_PERCENTAGE_EVIDENCE_PATH = ROOT / "docs/reference/ca_clamped_percentage_evidence.json"
MATRIX_DEFAULT = (Path(r"C:\Users\Blackrobe\Documents\agents\cameo-reference-sources-20260909") /
                  "validation/four-faction-sunday-pilot/warhead-reference-freshness/"
                  "pilot-warhead-review.json")

ARMOR_AXES = ("None", "Wood", "Concrete", "Light", "Heavy")
SCENARIOS = ("infantry", "vehicle", "ordinary_building", "small_aircraft", "ship")
SUPPORTED_SOURCES = ("Combined Arms", "OpenRA Red Alert", "OpenRA Tiberian Dawn")
SOURCE_CHANNEL_CODES = {
    "Combined Arms": "combined_arms",
    "OpenRA Red Alert": "openra_ra",
    "OpenRA Tiberian Dawn": "openra_td",
}

# These are abstract, source-specific target masks from the reviewed engine
# defaults. They describe a hypothetical target category, not a concrete
# actor guarantee. State-specific tags such as Disguise are intentionally out
# of this first pass. CA's ordinary building prototype includes Building;
# RA/TD use the shared Structure core.
SOURCE_TARGET_TYPES = {
    "Combined Arms": {
        "infantry": {"Ground", "Infantry"},
        "vehicle": {"Ground", "Vehicle"},
        "ordinary_building": {"Ground", "Structure", "Building"},
        "small_aircraft": {"Air", "AirSmall"},
        "ship": {"Ground", "Water", "Ship"},
    },
    "OpenRA Red Alert": {
        "infantry": {"GroundActor", "Infantry"},
        "vehicle": {"GroundActor", "Vehicle"},
        "ordinary_building": {"GroundActor", "Structure"},
        "small_aircraft": {"AirborneActor"},
        "ship": {"WaterActor", "Ship"},
    },
    "OpenRA Tiberian Dawn": {
        "infantry": {"Ground", "Infantry"},
        "vehicle": {"Ground", "Vehicle"},
        "ordinary_building": {"Ground", "Structure"},
        "small_aircraft": {"Air"},
        "ship": {"Ground", "Water"},
    },
}

# The engine defaults are supplied to select_channels by this caller. They
# stay Ground/Water even for RA, where authored warheads carry GroundActor or
# AirborneActor overrides. Empty authored masks remain empty.
DEFAULT_VALID_TARGETS = {"Ground", "Water"}
DEFAULT_INVALID_TARGETS = set()
DEFAULT_VALID_RELATIONSHIPS = {"Ally", "Neutral", "Enemy"}
DEFAULT_INVALID_RELATIONSHIPS = set()
RELATIONSHIP = "Enemy"
SELECTION_MODE = "collateral"
SUPPORTED_WARHEAD_TYPES = {"spreaddamage", "targetdamage", "healthpercentagedamage"}
TOOL_FILES = (
    "tools/balance/reference_channel_curves.py",
    "tools/balance/armor_projection.py",
    "tools/balance/diagnostic_output.py",
)
PERCENTAGE_SOURCE_SHA256 = "8cae0da324dba60b024348fea776ec131cec061924750b1ace333a66c15301fd"
PERCENTAGE_SOURCE_PATH = "OpenRA.Mods.Common/Warheads/HealthPercentageDamageWarhead.cs"
CLAMPED_PERCENTAGE_TYPE = "HealthPercentageSpreadDamage"
CLAMPED_PERCENTAGE_SOURCE = "Combined Arms"
CLAMPED_PERCENTAGE_SOURCE_PATH = "OpenRA.Mods.CA/Warheads/HealthPercentageSpreadDamageWarhead.cs"
CLAMPED_PERCENTAGE_SOURCE_COMMIT = "ab9e477c3db818e91946d4cfdc86e71012966141"
CLAMPED_PERCENTAGE_GIT_BLOB = "c337d6ef8e9d723628b978dda6f1cf63af1b932c"


def _export_field(channel, name):
    """Return (present, value), preferring nested exported warhead fields."""
    aliases = {name.lower(), name.replace("_", "").lower(),
               name.replace("_", "").lower()}
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


def load_percentage_evidence():
    """Load the reviewed, proof-only HealthPercentageDamage default."""
    document = json.loads(PERCENTAGE_EVIDENCE_PATH.read_text(encoding="utf-8"))
    if document.get("schema") != 1 or document.get("warhead_type") != "HealthPercentageDamage":
        raise ValueError("unsupported percentage armor evidence document")
    if document.get("undeclared_armor_multiplier") != 100:
        raise ValueError("percentage armor evidence must bind the 100 default")
    if document.get("health_percentage_source_sha256") != PERCENTAGE_SOURCE_SHA256:
        raise ValueError("percentage armor evidence source hash mismatch")
    if not isinstance(document.get("source_bindings"), Mapping):
        raise ValueError("percentage armor evidence has no source bindings")
    return document


def load_clamped_percentage_evidence():
    """Load the reviewed Combined Arms custom-warbhead semantics."""
    document = json.loads(CLAMPED_PERCENTAGE_EVIDENCE_PATH.read_text(encoding="utf-8"))
    if (document.get("schema") != 1
            or document.get("source") != CLAMPED_PERCENTAGE_SOURCE
            or document.get("source_path") != CLAMPED_PERCENTAGE_SOURCE_PATH
            or document.get("source_commit") != CLAMPED_PERCENTAGE_SOURCE_COMMIT
            or document.get("git_blob") != CLAMPED_PERCENTAGE_GIT_BLOB):
        raise ValueError("unsupported clamped percentage evidence document")
    example = document.get("retained_example") or {}
    if (example.get("damage_percent") != 100
            or example.get("min_reference_hp") != 30000
            or example.get("max_reference_hp") != 60000):
        raise ValueError("clamped percentage evidence retained example mismatch")
    return document


def _normalized_path(value):
    return str(value).replace("\\", "/")


def percentage_default_proof(matrix, source, evidence):
    """Return proof-gated 100 fallback for one matrix source, or its reason."""
    binding = (evidence.get("source_bindings") or {}).get(source)
    if not isinstance(binding, Mapping):
        return None, "percentage_armor_default_unproven:missing_source_binding"
    matrix_source = (matrix.get("export_sha256") or {}).get(source)
    engine_files = ((matrix_source or {}).get("engine_default_proof") or {}).get("files")
    if not isinstance(engine_files, Mapping):
        return None, "percentage_armor_default_unproven:missing_matrix_engine_proof"
    expected = {
        "OpenRA.Mods.Common/Warheads/DamageWarhead.cs": binding.get("damage_warhead_sha256"),
        "OpenRA.Mods.Common/Warheads/TargetDamageWarhead.cs": binding.get("target_damage_sha256"),
    }
    retained = {_normalized_path(key): value for key, value in engine_files.items()}
    for path, digest in expected.items():
        if not digest or retained.get(path) != digest:
            return None, f"percentage_armor_default_unproven:base_class_hash_mismatch:{path}"
    return {
        "status": "MATCHED",
        "default": evidence["undeclared_armor_multiplier"],
        "evidence_path": str(PERCENTAGE_EVIDENCE_PATH.relative_to(ROOT)),
        "evidence_sha256": _sha256(PERCENTAGE_EVIDENCE_PATH),
        "health_percentage_source_path": evidence["health_percentage_source_path"],
        "health_percentage_source_sha256": evidence["health_percentage_source_sha256"],
        "source": source,
        "engine_commit": binding.get("engine_commit"),
        "base_class_hashes": {
            "DamageWarhead.cs": binding.get("damage_warhead_sha256"),
            "TargetDamageWarhead.cs": binding.get("target_damage_sha256"),
        },
        "derivation": "HealthPercentageDamage inherits TargetDamage and its DamageVersus default is 100 for an absent named armor.",
    }, None


def clamped_percentage_proof(matrix, evidence, base_evidence):
    """Bind the CA custom type to its source record and inherited base proof."""
    if evidence.get("source") != CLAMPED_PERCENTAGE_SOURCE:
        return None, "clamped_percentage_evidence_unproven:source_mismatch"
    inherited, reason = percentage_default_proof(
        matrix, CLAMPED_PERCENTAGE_SOURCE, base_evidence)
    if inherited is None:
        return None, "clamped_percentage_evidence_unproven:" + str(reason)
    return {
        "status": "MATCHED",
        "default": inherited["default"],
        "evidence_path": str(CLAMPED_PERCENTAGE_EVIDENCE_PATH.relative_to(ROOT)),
        "evidence_sha256": _sha256(CLAMPED_PERCENTAGE_EVIDENCE_PATH),
        "source": evidence["source"],
        "source_commit": evidence["source_commit"],
        "source_path": evidence["source_path"],
        "git_blob": evidence["git_blob"],
        "warhead_type": CLAMPED_PERCENTAGE_TYPE,
        "base_class_proof": inherited,
        "derivation": "HealthPercentageSpreadDamage caps positive MaxReferenceHp, floors positive MinReferenceHp, then applies Damage percent and inherited DamageVersus.",
    }, None


def _identity_record(channel):
    identity = armor_projection.channel_identity(channel)
    return dict(zip(("source", "actor", "slot", "weapon", "warhead"), identity))


def scenario_target_types(source, scenario):
    """Return the reviewed abstract target mask for one source/scenario pair."""
    try:
        return frozenset(SOURCE_TARGET_TYPES[source][scenario])
    except KeyError as error:
        raise ValueError(f"unsupported source/scenario: {source}/{scenario}") from error


def zero_terms(axes=ARMOR_AXES):
    return {axis: {"A": 0.0, "B": 0.0, "flat": 0.0, "max_hp_fraction": 0.0}
            for axis in axes}


AIRCRAFT_AXES = ("Fighter", "Bomber", "Helicopter", "Spaceship")
AIRCRAFT_ENDPOINTS = ("Light", "Heavy")


def interpolate_aircraft_terms(terms, clamped_hp_components=None):
    """Interpolate Light/Heavy A+B endpoints for the new reference ladder.

    This is a maintainer-directed diagnostic mapping only. It does not alter
    the original source armor terms or claim runtime aircraft equivalence.
    Clamped components remain separate and are marked unsupported here rather
    than folded into an affine interpolation.
    """
    if not isinstance(terms, Mapping):
        return {"status": "UNRESOLVED", "terms": None,
                "reason": "aircraft endpoints missing"}
    endpoints = {}
    for axis in AIRCRAFT_ENDPOINTS:
        values = terms.get(axis)
        if not isinstance(values, Mapping):
            return {"status": "UNRESOLVED", "terms": None,
                    "reason": f"aircraft endpoint missing: {axis}"}
        endpoint = {}
        for key in ("A", "B"):
            fallback_key = "flat" if key == "A" else "max_hp_fraction"
            value = _finite(values.get(key, values.get(fallback_key)))
            if value is None or value < 0:
                return {"status": "UNRESOLVED", "terms": None,
                        "reason": f"aircraft endpoint invalid: {axis}.{key}"}
            endpoint[key] = value
        endpoints[axis] = endpoint
    light, heavy = endpoints["Light"], endpoints["Heavy"]
    result_terms = {}
    for index, axis in enumerate(AIRCRAFT_AXES):
        share = index / (len(AIRCRAFT_AXES) - 1)
        values = {key: light[key] + (heavy[key] - light[key]) * share
                  for key in ("A", "B")}
        result_terms[axis] = {"A": values["A"], "B": values["B"],
                              "flat": values["A"], "max_hp_fraction": values["B"]}
    clamped = {"status": "UNSUPPORTED", "reason":
               "clamped HP components remain separate; aircraft interpolation is affine-only"}
    if not clamped_hp_components:
        clamped = {"status": "NONE", "reason": "no clamped HP components"}
    return {
        "status": "RESOLVED_AFFINE_ONLY" if clamped["status"] == "UNSUPPORTED" else "RESOLVED",
        "policy": "MAINTAINER_DIRECTED_REFERENCE_AIRCRAFT_LADDER_20260911",
        "source_endpoints": {"Fighter": "Light", "Spaceship": "Heavy"},
        "intermediate_rule": "Bomber and Helicopter are equal linear steps between Light and Heavy for both A and B.",
        "terms": result_terms,
        "clamped_components": clamped,
    }


def attach_aircraft_interpolation(record):
    """Add the separate aircraft ladder only to small-aircraft source records."""
    if (record.get("source") not in SUPPORTED_SOURCES
            or record.get("scenario") != "small_aircraft"):
        return record
    if record.get("status") == "NOT_APPLICABLE":
        record["aircraft_interpolation"] = {
            "status": "NOT_APPLICABLE", "terms": None,
            "reason": "small-aircraft target scenario has no selected channels",
        }
    elif record.get("terms") is None:
        record["aircraft_interpolation"] = {
            "status": "UNRESOLVED", "terms": None,
            "reason": "source channel curve unresolved; aircraft endpoints unavailable",
        }
    else:
        record["aircraft_interpolation"] = interpolate_aircraft_terms(
            record["terms"], record.get("clamped_hp_components"))
    return record


def _number_error(value, label):
    if _finite(value) is None:
        return f"{label}_nonfinite_or_nonnumeric"
    return None


def _versus_values(channel, axes, percentage_default=None):
    table = None
    for key in ("resolved_versus", "declared_versus", "versus"):
        if key not in channel:
            continue
        if channel[key] is None:
            continue
        table = channel[key]
        break
    if table is None:
        table = {}
    if not isinstance(table, Mapping):
        return {}, ["versus_unresolved:invalid_table"], []

    fallback_present = "undeclared_armor_multiplier" in channel
    fallback = channel.get("undeclared_armor_multiplier")
    values, errors, reviewed_default_axes = {}, [], []
    for axis in axes:
        present = False
        raw = None
        for key, value in table.items():
            if str(key).strip() == axis:
                present, raw = True, value
                break
        if not present:
            if fallback_present and fallback is not None:
                raw = fallback
            elif percentage_default and percentage_default.get("status") == "MATCHED":
                raw = percentage_default["default"]
                reviewed_default_axes.append(axis)
            else:
                errors.append(f"versus_unresolved:{axis}")
                continue
        value = _finite(raw)
        if value is None:
            errors.append(f"versus_nonfinite_or_nonnumeric:{axis}")
            continue
        values[axis] = value
    return values, errors, reviewed_default_axes


def _falloff_fraction(channel):
    present, raw = _export_field(channel, "Falloff")
    if not present:
        return 1.0, None
    if isinstance(raw, str):
        values = [item.strip() for item in raw.replace(";", ",").split(",")]
        raw = values[0] if values and values[0] else None
    elif isinstance(raw, (list, tuple)):
        raw = raw[0] if raw else None
    value = _finite(raw)
    if value is None:
        return None, "falloff_nonfinite_or_nonnumeric"
    return value / 100.0, None


def _clamp_bound(channel, field):
    present, raw = _export_field(channel, field)
    if not present:
        return None, "absent"
    value = _finite(raw)
    if value is None:
        return None, "invalid"
    if value <= 0:
        return None, "disabled_nonpositive"
    return value, "enabled"


def _clamped_bounds(channel):
    minimum, minimum_status = _clamp_bound(channel, "MinReferenceHp")
    maximum, maximum_status = _clamp_bound(channel, "MaxReferenceHp")
    errors = []
    if minimum_status == "invalid":
        errors.append("min_reference_hp_nonfinite_or_nonnumeric")
    if maximum_status == "invalid":
        errors.append("max_reference_hp_nonfinite_or_nonnumeric")
    if minimum is not None and maximum is not None and minimum > maximum:
        errors.append("min_reference_hp_above_max_reference_hp")
    return {"min_hp": minimum, "max_hp": maximum,
            "min_status": minimum_status, "max_status": maximum_status}, errors


def _clamped_expression(minimum, maximum):
    expression = "H"
    if maximum is not None:
        expression = f"min(H, {maximum:g})"
    if minimum is not None:
        expression = f"max({minimum:g}, {expression})"
    return expression


def evaluate_nominal(terms, target_max_hp, *, axis="None", clamped_hp_components=()):
    """Evaluate affine A+B*H plus separate clamped-HP components for one axis."""
    hp = _finite(target_max_hp)
    if hp is None:
        raise ValueError("target_max_hp must be finite")
    axis_terms = (terms or {}).get(axis) or {}
    total = float(axis_terms.get("A", axis_terms.get("flat", 0.0)))
    total += hp * float(axis_terms.get("B", axis_terms.get("max_hp_fraction", 0.0)))
    components = clamped_hp_components
    if isinstance(components, Mapping):
        components = components.get(axis, ())
    for component in components or ():
        if component.get("axis") != axis:
            continue
        minimum, maximum = component.get("min_hp"), component.get("max_hp")
        clamped = hp
        if maximum is not None:
            clamped = min(clamped, float(maximum))
        if minimum is not None:
            clamped = max(clamped, float(minimum))
        total += float(component["coefficient"]) * clamped
    return total


def reduce_selected_channels(channels, axes=ARMOR_AXES, *, percentage_default=None,
                             clamped_percentage_default=None):
    """Reduce selected raw channels to nominal per-axis A/B terms.

    The caller has already selected an explicit slot and target state. This
    reducer admits the three affine positive authored warhead types plus the
    proof-gated Combined Arms HealthPercentageSpreadDamage component.
    Any positive unsupported payload, invalid damage, healing, falloff or
    versus data makes the whole group unresolved so no partial total is shown.
    Unsupported non-positive payloads are retained as harmless excluded
    channel evidence. Clamped components stay separate from the affine terms.
    No engine behavior is inferred here.
    """
    axes = tuple(axes)
    if not channels:
        return {"status": "NOT_APPLICABLE", "terms": zero_terms(axes),
                "clamped_hp_components": [], "channel_terms": [],
                "reason": "no selected channels"}
    totals = {axis: {"A": 0.0, "B": 0.0} for axis in axes}
    channel_terms, errors, clamped_components = [], [], []
    positive_count = 0
    for channel in channels:
        identity = _identity_record(channel)
        raw_damage = channel.get("damage") if isinstance(channel, Mapping) else None
        if raw_damage is None and isinstance(channel, Mapping):
            present, raw_damage = _export_field(channel, "Damage")
            if not present:
                raw_damage = None
        damage = _finite(raw_damage)
        kind = channel.get("warhead_type") if isinstance(channel, Mapping) else None
        kind_text = str(kind).strip() if kind is not None else ""
        kind_key = kind_text.lower()
        item = {"identity": identity, "channel": channel, "warhead_type": kind,
                "damage": damage}
        if damage is None:
            reason = "damage_nonfinite_or_nonnumeric"
            item.update(status="UNRESOLVED", reason=reason)
            channel_terms.append(item)
            errors.append(f"{identity}: {reason}")
            continue
        if damage < 0:
            reason = "healing_or_negative_damage"
            item.update(status="UNRESOLVED", reason=reason)
            channel_terms.append(item)
            errors.append(f"{identity}: {reason}")
            continue
        if kind_key == "healthpercentagedamage":
            item["base_max_hp_fraction"] = damage / 100.0
        if kind_text == CLAMPED_PERCENTAGE_TYPE:
            if channel.get("source") != SOURCE_CHANNEL_CODES[CLAMPED_PERCENTAGE_SOURCE]:
                reason = "unsupported_source_for_clamped_warhead"
                item.update(status="UNRESOLVED", reason=reason)
                channel_terms.append(item)
                errors.append(f"{identity}: {reason}")
                continue
            if damage == 0:
                item.update(status="ZERO")
                channel_terms.append(item)
                continue
            if not clamped_percentage_default or clamped_percentage_default.get("status") != "MATCHED":
                reason = ((clamped_percentage_default or {}).get("reason")
                          or "clamped_percentage_evidence_unproven")
                item.update(status="UNRESOLVED", reason=reason,
                            clamped_hp_components=[],
                            clamped_percentage_evidence=clamped_percentage_default)
                channel_terms.append(item)
                errors.append(f"{identity}: {reason}")
                continue
            bounds, bound_errors = _clamped_bounds(channel)
            proof_for_channel = clamped_percentage_default
            versus, versus_errors, reviewed_default_axes = _versus_values(
                channel, axes, proof_for_channel)
            errors_for_channel = bound_errors + versus_errors
            if errors_for_channel:
                item.update(status="UNRESOLVED", reason=";".join(errors_for_channel),
                            versus=versus, bounds=bounds)
                item["clamped_percentage_evidence"] = clamped_percentage_default
                channel_terms.append(item)
                errors.extend(f"{identity}: {error}" for error in errors_for_channel)
                continue
            falloff, falloff_error = _falloff_fraction(channel)
            if falloff_error:
                item.update(status="UNRESOLVED", reason=falloff_error,
                            versus=versus, bounds=bounds)
                item["clamped_percentage_evidence"] = clamped_percentage_default
                channel_terms.append(item)
                errors.append(f"{identity}: {falloff_error}")
                continue
            component_rows = []
            for axis in axes:
                component_rows.append({
                    "axis": axis,
                    "coefficient": damage / 100.0 * falloff * versus[axis] / 100.0,
                    "min_hp": bounds["min_hp"], "max_hp": bounds["max_hp"],
                    "min_status": bounds["min_status"], "max_status": bounds["max_status"],
                    "identity": identity, "damage_percent": damage,
                    "versus": versus[axis], "falloff_fraction": falloff,
                    "expression": _clamped_expression(bounds["min_hp"], bounds["max_hp"]),
                })
            item.update(status="RESOLVED", versus=versus, bounds=bounds,
                        clamped_hp_components=component_rows,
                        base_max_hp_fraction=damage / 100.0,
                        falloff_fraction=falloff)
            if reviewed_default_axes:
                item["clamped_percentage_evidence"] = {
                    **clamped_percentage_default, "axes_defaulted": reviewed_default_axes}
            else:
                item["clamped_percentage_evidence"] = clamped_percentage_default
            clamped_components.extend(component_rows)
            positive_count += 1
            channel_terms.append(item)
            continue
        if kind_key not in SUPPORTED_WARHEAD_TYPES:
            if damage > 0:
                reason = f"unsupported_positive_warhead_type:{kind_text or 'missing'}"
                item.update(status="UNRESOLVED", reason=reason)
                errors.append(f"{identity}: {reason}")
            else:
                item.update(status="EXCLUDED", reason="unsupported_nonpositive_payload")
            channel_terms.append(item)
            continue
        if damage == 0:
            item.update(status="ZERO", A={axis: 0.0 for axis in axes},
                        B={axis: 0.0 for axis in axes})
            channel_terms.append(item)
            continue

        positive_count += 1
        proof_for_channel = (percentage_default
                             if kind_text == "HealthPercentageDamage" else None)
        versus, versus_errors, reviewed_default_axes = _versus_values(
            channel, axes, proof_for_channel)
        if (kind_text == "HealthPercentageDamage" and versus_errors
                and percentage_default
                and percentage_default.get("status") != "MATCHED"):
            proof_reason = percentage_default.get("reason") or "percentage_armor_default_unproven"
            versus_errors.append(proof_reason)
        if versus_errors:
            item.update(status="UNRESOLVED", reason=";".join(versus_errors),
                        versus=versus)
            if kind_text == "HealthPercentageDamage" and percentage_default:
                item["percentage_default_evidence"] = percentage_default
            channel_terms.append(item)
            errors.extend(f"{identity}: {error}" for error in versus_errors)
            continue
        factor = 1.0
        if kind_key == "spreaddamage":
            factor, falloff_error = _falloff_fraction(channel)
            if falloff_error:
                item.update(status="UNRESOLVED", reason=falloff_error,
                            versus=versus)
                channel_terms.append(item)
                errors.append(f"{identity}: {falloff_error}")
                continue
        per_axis_a, per_axis_b = {}, {}
        for axis in axes:
            if kind_key == "healthpercentagedamage":
                a, b = 0.0, damage / 100.0 * versus[axis] / 100.0
            else:
                a, b = damage * factor * versus[axis] / 100.0, 0.0
            totals[axis]["A"] += a
            totals[axis]["B"] += b
            per_axis_a[axis], per_axis_b[axis] = a, b
        item.update(status="RESOLVED", versus=versus, A=per_axis_a, B=per_axis_b,
                    base_max_hp_fraction=(damage / 100.0
                                          if kind_key == "healthpercentagedamage" else 0.0),
                    falloff_fraction=factor if kind_key == "spreaddamage" else None)
        if reviewed_default_axes:
            item["percentage_default_evidence"] = {
                **percentage_default, "axes_defaulted": reviewed_default_axes}
        channel_terms.append(item)

    if errors:
        return {"status": "UNRESOLVED", "terms": None, "clamped_hp_components": None,
                "channel_terms": channel_terms, "reasons": errors,
                "reason": "; ".join(errors)}
    terms = {axis: {"A": values["A"], "B": values["B"],
                    "flat": values["A"], "max_hp_fraction": values["B"]}
             for axis, values in totals.items()}
    status = "RESOLVED" if positive_count else "RESOLVED_ZERO"
    return {"status": status, "terms": terms,
            "clamped_hp_components": clamped_components,
            "channel_terms": channel_terms}


def _state_value(channels, field):
    values = [channel.get(field) for channel in channels]
    if not values or all(value == values[0] for value in values):
        return values[0] if values else None
    return values


def _group_channels(channels):
    groups = collections.defaultdict(list)
    for channel in channels:
        identity = armor_projection.channel_identity(channel)
        groups[identity[:4]].append(channel)
    key=lambda value: tuple("" if item is None else str(item) for item in value)
    return [(identity, groups[identity]) for identity in sorted(groups, key=key)]


def _base_record(item, reference, source, scenario, identity, channels, target_types):
    _channel_source, source_actor, slot, weapon = identity
    state = {"requires_condition": _state_value(channels, "requires_condition"),
             "pause_on_condition": _state_value(channels, "pause_on_condition")}
    return {
        "actor": item.get("actor"),
        "source": source,
        "source_actor": source_actor,
        "channel_source": _channel_source,
        "reference_id": reference.get("id"),
        "selected_comparison_weapon": reference.get("selected_comparison_weapon"),
        "slot": slot,
        "weapon": weapon,
        "state": state,
        "requires_condition": state["requires_condition"],
        "pause_on_condition": state["pause_on_condition"],
        "scenario": scenario,
        "target_types": sorted(target_types),
        "relationship": RELATIONSHIP,
        "selection_mode": SELECTION_MODE,
        "input_channels": channels,
    }


def _unsupported_record(item, reference, scenario):
    source = reference.get("source")
    channels = reference.get("selected_weapon_channels") or []
    return {
        "actor": item.get("actor"), "source": source,
        "source_actor": None, "channel_source": None,
        "reference_id": reference.get("id"),
        "selected_comparison_weapon": reference.get("selected_comparison_weapon"),
        "slot": None, "weapon": reference.get("selected_comparison_weapon"),
        "state": {"requires_condition": None, "pause_on_condition": None},
        "requires_condition": None, "pause_on_condition": None,
        "scenario": scenario, "target_types": None, "relationship": RELATIONSHIP,
        "selection_mode": SELECTION_MODE, "status": "UNRESOLVED",
        "reason": f"unsupported_source_adapter:{source}",
        "input_channels": channels, "selected_channels": [], "excluded_channels": [],
    }


def _process_group(item, reference, source, scenario, identity, channels,
                   percentage_default=None, clamped_percentage_default=None):
    target_types = scenario_target_types(source, scenario)
    record = _base_record(item, reference, source, scenario, identity, channels,
                          target_types)
    source_code = SOURCE_CHANNEL_CODES[source]
    malformed = []
    for channel in channels:
        if channel.get("source") != source_code:
            malformed.append("channel_source_mismatch")
        if any(channel.get(field) is None for field in ("actor", "slot", "weapon", "warhead")):
            malformed.append("channel_identity_unresolved")
    if malformed:
        record.update(status="UNRESOLVED", reason=";".join(sorted(set(malformed))),
                      selected_channels=[], excluded_channels=[])
        return record
    selection = armor_projection.select_channels(
        channels,
        active_slots={identity[2]},
        target_types=target_types,
        relationship=RELATIONSHIP,
        default_valid_targets=DEFAULT_VALID_TARGETS,
        default_invalid_targets=DEFAULT_INVALID_TARGETS,
        default_valid_relationships=DEFAULT_VALID_RELATIONSHIPS,
        default_invalid_relationships=DEFAULT_INVALID_RELATIONSHIPS,
        weapon_valid_target_mode=SELECTION_MODE,
    )
    record.update(selection=selection["selection"],
                  selected_channels=selection["selected"],
                  excluded_channels=selection["excluded"])
    duplicate_rejections = [entry for entry in selection["excluded"]
                            if entry["reason"] == "duplicate_channel_identity"]
    if duplicate_rejections:
        record.update(status="UNRESOLVED", terms=None,
                      reason="duplicate_channel_identity: group withheld rather than partially summed")
        return record
    if not selection["selected"]:
        reasons = sorted({entry["reason"] for entry in selection["excluded"]})
        record.update(status="NOT_APPLICABLE", terms=zero_terms(),
                      reason="all channels excluded by explicit target/relationship selection"
                      + (": " + ";".join(reasons) if reasons else ""))
        return record
    record.update(reduce_selected_channels(selection["selected"],
                                            percentage_default=percentage_default,
                                            clamped_percentage_default=clamped_percentage_default))
    return record


def validate_matrix(matrix):
    if not isinstance(matrix, Mapping):
        raise ValueError("matrix must be a JSON object")
    if not isinstance(matrix.get("rows"), list):
        raise ValueError("matrix.rows must be a list")
    for index, item in enumerate(matrix["rows"]):
        if not isinstance(item, Mapping) or not item.get("actor"):
            raise ValueError(f"matrix.rows[{index}] needs an actor")
        if "references" in item and not isinstance(item["references"], list):
            raise ValueError(f"matrix.rows[{index}].references must be a list")
    return matrix


def build(matrix, *, provenance=None, matrix_path=None, percentage_defaults=None,
          percentage_evidence=None, clamped_defaults=None, clamped_evidence=None):
    """Build all per-source/per-slot/per-scenario records without averaging."""
    validate_matrix(matrix)
    records = []
    for item in matrix["rows"]:
        for reference in item.get("references") or []:
            source = reference.get("source")
            channels = reference.get("selected_weapon_channels") or []
            if source not in SUPPORTED_SOURCES:
                for scenario in SCENARIOS:
                    records.append(_unsupported_record(item, reference, scenario))
                continue
            if not channels:
                for scenario in SCENARIOS:
                    target_types = scenario_target_types(source, scenario)
                    record = _base_record(item, reference, source, scenario,
                                          (SOURCE_CHANNEL_CODES[source], None, None, None), [],
                                          target_types)
                    record.update(status="UNRESOLVED", terms=None,
                                  selected_channels=[], excluded_channels=[],
                                  reason="missing_selected_weapon_channels",
                                  target_types=sorted(target_types))
                    records.append(record)
                continue
            for identity, group in _group_channels(channels):
                for scenario in SCENARIOS:
                    records.append(_process_group(item, reference, source, scenario,
                                                  identity, group,
                                                  (percentage_defaults or {}).get(source),
                                                  (clamped_defaults or {}).get(source)))
    status_counts = collections.Counter(record["status"] for record in records)
    source_counts = collections.Counter(record["source"] for record in records)
    records = [attach_aircraft_interpolation(record) for record in records]
    aircraft_records = [record for record in records if "aircraft_interpolation" in record]
    aircraft_status_counts = collections.Counter(
        record["aircraft_interpolation"]["status"] for record in aircraft_records)
    unsupported_source_records = sum(
        1 for record in records
        if str(record.get("reason", "")).startswith("unsupported_source_adapter:"))
    result = {
        "schema": 1,
        "scope": "Review-only per-source, per-slot, per-weapon nominal channel curves; no source averaging, gameplay certification or writeback.",
        "method": [
            "Each selected_weapon_channels group is keyed by source actor, slot and weapon; one explicit active slot is passed to the selector, so alternate armament states remain separate.",
            "Target masks are source-specific abstract scenarios: infantry, vehicle, ordinary_building, small_aircraft and surface ship. They are not concrete actor guarantees and omit state-specific or submerged tags.",
            "Selection uses collateral mode, caller-supplied Ground/Water defaults and Enemy relationship; weapon-valid-target declarations are intentionally outside this engagement scenario.",
            "SpreadDamage contributes A = Damage x first Falloff / 100 x Versus / 100; TargetDamage contributes A = Damage x Versus / 100; HealthPercentageDamage contributes B = Damage / 100 x Versus / 100.",
            "Combined Arms HealthPercentageSpreadDamage is shown as separate proof-gated per-axis clamped_hp_components; it is never folded into A/B.",
            "Missing versus, invalid finite data, healing, and positive unsupported warheads make that selected group unresolved. Fully excluded groups are explicit zero/not-applicable.",
            "New aircraft reference interpolation maps Light to Fighter and Heavy to Spaceship, with equal Bomber/Helicopter steps for A/B; it is a diagnostic policy and does not rewrite the original five source axes or adopt runtime Versus values.",
        ],
        "source_channel_codes": SOURCE_CHANNEL_CODES,
        "source_target_types": {source: {scenario: sorted(values)
                                           for scenario, values in scenarios.items()}
                                for source, scenarios in SOURCE_TARGET_TYPES.items()},
        "defaults": {"valid_targets": sorted(DEFAULT_VALID_TARGETS),
                     "invalid_targets": sorted(DEFAULT_INVALID_TARGETS),
                     "valid_relationships": sorted(DEFAULT_VALID_RELATIONSHIPS),
                     "invalid_relationships": sorted(DEFAULT_INVALID_RELATIONSHIPS),
                     "relationship": RELATIONSHIP, "selection_mode": SELECTION_MODE,
                     "armor_axes": list(ARMOR_AXES)},
        "summary": {"records": len(records), "status_counts": dict(sorted(status_counts.items())),
                    "sources": dict(sorted(source_counts.items())),
                    "supported_sources": list(SUPPORTED_SOURCES),
                    "unsupported_source_records": unsupported_source_records,
                    "aircraft_interpolation": {
                        "records": len(aircraft_records),
                        "status_counts": dict(sorted(aircraft_status_counts.items()))}},
        "records": records,
        "input_matrix": matrix,
    }
    if provenance is not None:
        result["matrix_sha256"] = provenance["matrix_sha256"]
        result["tool_sha256"] = provenance["tool_sha256"]
        result["percentage_armor_evidence_sha256"] = provenance[
            "percentage_armor_evidence_sha256"]
        result["clamped_percentage_evidence_sha256"] = provenance[
            "clamped_percentage_evidence_sha256"]
        result["matrix_path"] = str(matrix_path) if matrix_path else None
    if percentage_evidence is not None:
        result["percentage_armor_evidence"] = percentage_evidence
    if clamped_evidence is not None:
        result["clamped_percentage_evidence"] = clamped_evidence
    return result


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def input_fingerprints(matrix_path):
    return {"matrix_sha256": _sha256(matrix_path),
            "tool_sha256": {name: _sha256(ROOT / Path(name)) for name in TOOL_FILES},
            "percentage_armor_evidence_sha256": _sha256(PERCENTAGE_EVIDENCE_PATH),
            "clamped_percentage_evidence_sha256": _sha256(CLAMPED_PERCENTAGE_EVIDENCE_PATH)}


def build_from_path(matrix_path):
    matrix_path = Path(matrix_path).resolve()
    before = input_fingerprints(matrix_path)
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    evidence = load_percentage_evidence()
    percentage_defaults = {}
    for source in SUPPORTED_SOURCES:
        proof, reason = percentage_default_proof(matrix, source, evidence)
        percentage_defaults[source] = proof or {"status": "UNRESOLVED", "reason": reason}
    clamped_evidence_doc = load_clamped_percentage_evidence()
    clamped_proof, clamped_reason = clamped_percentage_proof(
        matrix, clamped_evidence_doc, evidence)
    clamped_defaults = {
        CLAMPED_PERCENTAGE_SOURCE: clamped_proof or {
            "status": "UNRESOLVED", "reason": clamped_reason}}
    percentage_evidence = {
        "path": str(PERCENTAGE_EVIDENCE_PATH.relative_to(ROOT)),
        "sha256": before["percentage_armor_evidence_sha256"],
        "warhead_type": evidence["warhead_type"],
        "default": evidence["undeclared_armor_multiplier"],
        "health_percentage_source_path": evidence["health_percentage_source_path"],
        "health_percentage_source_sha256": evidence["health_percentage_source_sha256"],
        "source_proof_status": percentage_defaults,
        "source_bindings": evidence["source_bindings"],
    }
    clamped_evidence = {
        "path": str(CLAMPED_PERCENTAGE_EVIDENCE_PATH.relative_to(ROOT)),
        "sha256": before["clamped_percentage_evidence_sha256"],
        "warhead_type": CLAMPED_PERCENTAGE_TYPE,
        "source": clamped_evidence_doc["source"],
        "source_commit": clamped_evidence_doc["source_commit"],
        "source_path": clamped_evidence_doc["source_path"],
        "git_blob": clamped_evidence_doc["git_blob"],
        "source_proof_status": clamped_defaults,
        "retained_example": clamped_evidence_doc["retained_example"],
    }
    result = build(matrix, provenance=before, matrix_path=matrix_path,
                   percentage_defaults=percentage_defaults,
                   percentage_evidence=percentage_evidence,
                   clamped_defaults=clamped_defaults,
                   clamped_evidence=clamped_evidence)
    after = input_fingerprints(matrix_path)
    if after != before:
        raise ValueError("matrix or tool inputs changed during collection; retry on a stable tree")
    result["input_guard"] = {"before": before, "after": after, "unchanged": True}
    return result


def _fmt(value):
    if value is None:
        return "—"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{value:.4g}"


def _state_text(record):
    state = record.get("state") or {}
    req = state.get("requires_condition")
    pause = state.get("pause_on_condition")
    return "requires=" + ("—" if req is None else str(req)) + "; pause=" + ("—" if pause is None else str(pause))


def _terms_text(terms):
    if terms is None:
        return "—"
    return "; ".join(f"{axis}: A={_fmt(values.get('A'))}, B={_fmt(values.get('B'))}"
                      for axis, values in terms.items())


def _components_text(components):
    if not components:
        return ""
    return "; ".join(
        f"{component.get('axis')}: coeff={_fmt(component.get('coefficient'))}, "
        f"clamp={component.get('expression')}"
        for component in components)


def render_markdown(result):
    summary = result.get("summary") or {}
    lines = [
        "# Reference channel curve review", "",
        "**Review-only diagnostic.** Records stay per source, actor, slot, weapon and target scenario; no source averaging, integer hit simulation, cadence, overkill, shields, shrapnel or full payload certification is performed.",
        "",
        "## Summary", "",
        f"- Records: **{summary.get('records', 0)}**; statuses: **{summary.get('status_counts', {})}**.",
        "- Supported sources: Combined Arms, OpenRA Red Alert and OpenRA Tiberian Dawn. Other adapters, including DTA Enhanced, remain explicit `UNRESOLVED` records.",
        "- Target masks are source-specific abstract masks; they do not guarantee a concrete game actor or prove full combat equivalence.",
        "- `HealthPercentageSpreadDamage` remains a separate clamped-HP component; it is never hidden inside affine `A/B` totals.",
        "",
        "## Source target masks", "",
        "| source | scenario | abstract target types |", "|---|---|---|",
    ]
    for source in SUPPORTED_SOURCES:
        for scenario in SCENARIOS:
            values = ", ".join(sorted(SOURCE_TARGET_TYPES[source][scenario]))
            lines.append(f"| {source} | {scenario} | {values} |")
    lines += ["", "## Scenario records", "",
              "| actor | source | source actor | slot | weapon | state | scenario | status | terms or reason |",
              "|---|---|---|---|---|---|---|---|---|"]
    for record in result.get("records", []):
        reason = record.get("reason")
        if not reason:
            terms = _terms_text(record.get("terms"))
            components = _components_text(record.get("clamped_hp_components"))
            reason = " | ".join(value for value in (terms, components) if value) or "—"
        state = _state_text(record).replace("|", "\\|")
        reason = str(reason).replace("|", "\\|")
        lines.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            record.get("actor", "—"), record.get("source", "—"),
            record.get("source_actor", "—"), record.get("slot", "—"),
            record.get("weapon", "—"), state, record.get("scenario", "—"),
            record.get("status", "—"), reason))
    lines += ["", "## Aircraft ladder interpolation (new diagnostic policy)", "",
              "Aedis-directed reference mapping: source Light is Fighter, source Heavy is Spaceship, with equal linear Bomber and Helicopter steps for both A and B. This does not change the five source armor axes, historical generated documents, or runtime Versus values.", "",
              "| actor | source | slot | weapon | status | aircraft A/B terms or reason |",
              "|---|---|---|---|---|---|"]
    for record in result.get("records", []):
        interpolation = record.get("aircraft_interpolation")
        if interpolation is None:
            continue
        terms = interpolation.get("terms")
        detail = _terms_text(terms) if terms is not None else interpolation.get("reason", "—")
        detail = str(detail).replace("|", "\\|")
        lines.append("| {} | {} | {} | {} | {} | {} |".format(
            record.get("actor", "—"), record.get("source", "—"),
            record.get("slot", "—"), record.get("weapon", "—"),
            interpolation.get("status", "—"), detail))
    lines += ["", "A resolved row's original terms remain nominal continuous coefficients `A + B*H` by the five source armor axes; the aircraft ladder is comparison-only and does not establish full combat equivalence."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--matrix", type=Path, default=MATRIX_DEFAULT)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown", type=Path,
                        help="optional readable review companion (.md)")
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
        json_text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        outputs = {out_path: json_text}
        if markdown_path is not None:
            outputs[markdown_path] = render_markdown(result)
        diagnostic_output.write_outputs(ROOT, outputs)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(result["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
