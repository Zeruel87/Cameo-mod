#!/usr/bin/env python3
"""Fail-closed four-source armor synthesis gate.

This is review tooling only. Callers provide explicit comparison groups and
state joins; the gate never guesses actor/weapon matches or writes balance
values. Missing or unresolved voices remain unresolved instead of being
renormalized.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from collections import Counter
from pathlib import Path

import diagnostic_output

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ("Combined Arms", "OpenRA Red Alert", "OpenRA Tiberian Dawn", "DTA Enhanced")
# The legacy gate below keeps its fixed four-reference contract.  Aedis's
# requested 25% model is a separate explicit contract: Current Cameo plus
# three distinct voices selected from this reference set.
REFERENCE_SOURCES = SOURCES
CURRENT_VOICE = "Current Cameo"
BASE_AXES = ("None", "Wood", "Concrete", "Light", "Heavy")
COMMON_AXES = ("None", "Wood", "Concrete", "Scout", "Light", "Medium", "Heavy", "Superheavy")
INFANTRY_AXES = ("None", "Flak", "Plate")
VEHICLE_AXES = ("Scout", "Light", "Medium", "Heavy", "Superheavy")
AIRCRAFT_AXES = ("Fighter", "Bomber", "Helicopter", "Spaceship")
FULLY_RESOLVED_STATUSES = frozenset({"RESOLVED"})


# These mappings are review-only.  A source Light/Heavy value is never
# silently renamed to a target axis; each target axis below is deliberately
# constructed from the named source endpoints.
SCENARIO_POLICIES = {
    "infantry": {
        "name": "AEDIS_INFANTRY_NONE_LIGHT_TO_NONE_FLAK_PLATE",
        "target_axes": INFANTRY_AXES,
        "required_source_axes": ("None", "Light"),
        "axis_mapping": "None direct; Light maps to Plate; Flak is the equal midpoint between None and Light.",
    },
    "vehicle": {
        "name": "AEDIS_VEHICLE_LIGHT_HEAVY_LADDER",
        "target_axes": VEHICLE_AXES,
        "required_source_axes": ("Light", "Heavy"),
        "axis_mapping": "Light and Heavy direct; Medium is the equal midpoint; Scout is one equal step below Light; Superheavy is one equal step above Heavy.",
    },
    # Surface ships use the vehicle ladder until a source-specific policy is
    # supplied.  The scenario name is explicit so this is not an alias.
    "ship": {
        "name": "AEDIS_SHIP_VEHICLE_LADDER",
        "target_axes": VEHICLE_AXES,
        "required_source_axes": ("Light", "Heavy"),
        "axis_mapping": "Light and Heavy direct; Medium is the equal midpoint; Scout is one equal step below Light; Superheavy is one equal step above Heavy.",
    },
    "aircraft": {
        "name": "AEDIS_AIRCRAFT_LIGHT_HEAVY_LADDER",
        "target_axes": AIRCRAFT_AXES,
        "required_source_axes": ("Light", "Heavy"),
        "axis_mapping": "Light maps to Fighter and Heavy maps to Spaceship; Bomber and Helicopter are equal linear steps between them.",
    },
    # Keep the source-tool scenario spelling explicit for callers that use
    # its abstract target names.  It shares the aircraft rule by policy, not
    # by accepting a silent axis alias.
    "small_aircraft": {
        "name": "AEDIS_SMALL_AIRCRAFT_LIGHT_HEAVY_LADDER",
        "target_axes": AIRCRAFT_AXES,
        "required_source_axes": ("Light", "Heavy"),
        "axis_mapping": "Light maps to Fighter and Heavy maps to Spaceship; Bomber and Helicopter are equal linear steps between them.",
    },
}


def _finite(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _axis_map(terms):
    if not isinstance(terms, dict):
        return {}
    return {str(key).lower(): value for key, value in terms.items()}


def _term(value, axis):
    if not isinstance(value, dict):
        return None, f"axis_missing:{axis}"
    a = _finite(value.get("A", value.get("flat")))
    b = _finite(value.get("B", value.get("max_hp_fraction")))
    if a is None or b is None:
        return None, f"axis_nonfinite:{axis}"
    if a < 0 or b < 0:
        return None, f"axis_negative:{axis}"
    return {"A": a, "B": b, "flat": a, "max_hp_fraction": b}, None


def _linear_term(low, high, share):
    """Return an affine term at *share* between two validated terms."""
    a = low["A"] + (high["A"] - low["A"]) * share
    b = low["B"] + (high["B"] - low["B"]) * share
    return {"A": a, "B": b, "flat": a, "max_hp_fraction": b}


def _normalize_legacy_terms(terms, *, interpolate_vehicle_axes=False):
    """Return the original common-axis normalization for old callers."""
    mapped = _axis_map(terms)
    normalized = {}
    for axis in BASE_AXES:
        value, reason = _term(mapped.get(axis.lower()), axis)
        if reason:
            return None, reason
        normalized[axis] = value
    missing = [axis for axis in COMMON_AXES if axis.lower() not in mapped]
    if missing and not interpolate_vehicle_axes:
        return None, "missing_common_axes:" + ",".join(missing)
    light, heavy = normalized["Light"], normalized["Heavy"]
    for axis, share in (("Scout", 0.0), ("Medium", 0.5), ("Superheavy", 1.0)):
        if axis not in normalized:
            normalized[axis] = {
                "A": light["A"] + (heavy["A"] - light["A"]) * share,
                "B": light["B"] + (heavy["B"] - light["B"]) * share,
                "flat": light["A"] + (heavy["A"] - light["A"]) * share,
                "max_hp_fraction": light["B"] + (heavy["B"] - light["B"]) * share,
            }
    for axis in COMMON_AXES:
        if axis in normalized:
            continue
        value, reason = _term(mapped.get(axis.lower()), axis)
        if reason:
            return None, reason
        normalized[axis] = value
    return normalized, None


def _normalize_scenario_terms(terms, scenario):
    """Apply one explicit diagnostic mapping for a supported scenario."""
    policy = SCENARIO_POLICIES.get(scenario) if isinstance(scenario, str) else None
    if policy is None:
        return None, "unsupported_scenario:" + str(scenario)

    mapped = _axis_map(terms)
    source_terms = {}
    for axis in policy["required_source_axes"]:
        value, reason = _term(mapped.get(axis.lower()), axis)
        if reason:
            return None, reason
        source_terms[axis] = value

    light = source_terms.get("Light")
    heavy = source_terms.get("Heavy")
    if scenario == "infantry":
        none = source_terms["None"]
        normalized = {
            "None": none,
            "Flak": _linear_term(none, source_terms["Light"], 0.5),
            "Plate": source_terms["Light"],
        }
    elif scenario in ("vehicle", "ship"):
        step = _linear_term(light, heavy, -1.0)
        normalized = {
            "Scout": step,
            "Light": light,
            "Medium": _linear_term(light, heavy, 0.5),
            "Heavy": heavy,
            "Superheavy": _linear_term(light, heavy, 2.0),
        }
    else:
        normalized = {
            "Fighter": light,
            "Bomber": _linear_term(light, heavy, 1.0 / 3.0),
            "Helicopter": _linear_term(light, heavy, 2.0 / 3.0),
            "Spaceship": heavy,
        }
    for axis, value in normalized.items():
        if (_finite(value["A"]) is None or _finite(value["B"]) is None):
            return None, "mapped_axis_nonfinite:" + axis
        if value["A"] < 0 or value["B"] < 0:
            return None, "mapped_axis_negative:" + axis
    return normalized, None


def normalize_terms(terms, *, interpolate_vehicle_axes=False, scenario=None,
                    scenario_policy=False):
    """Return normalized diagnostic axes, or a precise fail-closed reason.

    ``interpolate_vehicle_axes`` retains the original common-axis behavior for
    existing callers.  ``scenario_policy=True`` is the explicit Aedis-directed
    mapping switch: it uses the group scenario to select the infantry,
    vehicle/ship, or aircraft target ladder above.
    """
    if scenario_policy and (scenario is not None and
                            (not isinstance(scenario, str)
                             or scenario not in SCENARIO_POLICIES)):
        return None, "unsupported_scenario:" + str(scenario)
    if scenario_policy:
        return _normalize_scenario_terms(terms, scenario)
    return _normalize_legacy_terms(terms,
                                   interpolate_vehicle_axes=interpolate_vehicle_axes)


def _geometric(values):
    values = [float(value) for value in values]
    if any(value < 0 or not math.isfinite(value) for value in values):
        raise ValueError("nonnegative finite values required")
    if any(value == 0 for value in values):
        return 0.0
    return math.exp(sum(math.log(value) for value in values) / len(values))


def _mean_terms(normalized, axes=COMMON_AXES):
    result = {}
    for axis in axes:
        values = [row[axis] for row in normalized]
        result[axis] = {
            "arithmetic": {
                "A": sum(value["A"] for value in values) / len(values),
                "B": sum(value["B"] for value in values) / len(values),
            },
            "geometric": {
                "A": _geometric([value["A"] for value in values]),
                "B": _geometric([value["B"] for value in values]),
            },
        }
    return result


def _unresolved(group, reasons, *, rows=None, policy=None):
    policy = policy or {}
    return {
        "comparison_id": group.get("comparison_id"),
        "scenario": group.get("scenario"),
        "state_key": group.get("state_key"),
        "status": "UNRESOLVED",
        "reasons": sorted(set(reasons)),
        "target_axes": copy.deepcopy(policy.get("target_axes", [])),
        "source_rows": copy.deepcopy(rows if rows is not None else group.get("source_rows", [])),
        "policy": policy,
    }


def combine_group(group, *, interpolate_vehicle_axes=False, scenario_policy=False,
                  voice_policy=False):
    """Combine one explicit group, failing closed on uncertainty.

    The default retains the original fixed four-reference contract.  With
    ``voice_policy=True`` the group is Aedis's four-voice model: one explicit
    Current Cameo row and exactly three distinct reference rows.  The latter
    may be any three of ``REFERENCE_SOURCES``; the gate never chooses them.
    """
    if not isinstance(group, dict):
        return {"status": "UNRESOLVED", "reasons": ["group_not_object"],
                "source_rows": copy.deepcopy(group)}
    scenario = group.get("scenario")
    scenario_spec = (SCENARIO_POLICIES.get(scenario)
                     if isinstance(scenario, str) else None)
    rows = group.get("source_rows")
    policy = {"interpolate_vehicle_axes": bool(interpolate_vehicle_axes),
              "scenario_policy": bool(scenario_policy),
              "voice_policy": bool(voice_policy),
              "accepted_statuses": sorted(FULLY_RESOLVED_STATUSES),
              "aggregation": ("equal arithmetic and geometric means after explicit four-voice gate"
                               if voice_policy else
                               "equal arithmetic and geometric means after four-source gate"),
              "target_axes": (list(scenario_spec["target_axes"])
                              if scenario_spec else [])
              if scenario_policy else list(COMMON_AXES),
              "axis_mapping": (scenario_spec["axis_mapping"]
                               if scenario_spec and scenario_policy else
                               ("No scenario mapping selected because the scenario is unsupported or missing."
                                 if scenario_policy else
                                 "Light/Heavy direct; missing Scout/Medium/Superheavy interpolated only when opted in"))}
    if voice_policy:
        policy.update({
            "current_voice": CURRENT_VOICE,
            "reference_sources": list(REFERENCE_SOURCES),
            "required_voice_count": 4,
            "required_reference_voice_count": 3,
            "equal_voice_weight": 0.25,
        })
    if scenario_spec and scenario_policy:
        policy.update({"scenario_policy_name": scenario_spec["name"],
                       "required_source_axes": list(scenario_spec["required_source_axes"])})
    if not isinstance(rows, list):
        return _unresolved(group, ["source_rows_not_list"], rows=rows, policy=policy)
    reasons = []
    if not group.get("comparison_id"):
        reasons.append("comparison_id_required")
    if not group.get("scenario"):
        reasons.append("scenario_required")
    if not group.get("state_key"):
        reasons.append("state_key_required")
    if scenario_policy and group.get("scenario") and scenario_spec is None:
        reasons.append("unsupported_scenario:" + str(group.get("scenario")))
    seen = Counter()
    normalized = {}
    for row in rows:
        if not isinstance(row, dict):
            reasons.append("source_row_not_object")
            continue
        source = row.get("source")
        # Keep malformed labels fail-closed.  A list/dict source must become an
        # unresolved diagnostic, not a TypeError while it is used as a Counter
        # key or tested against the allowed source set.
        if not isinstance(source, str):
            label = repr(source)
            reasons.append(("unsupported_voice:" if voice_policy else
                            "unsupported_source:") + label)
            continue
        seen[source] += 1
        allowed = (set(REFERENCE_SOURCES) | {CURRENT_VOICE}) if voice_policy else set(SOURCES)
        if source not in allowed:
            reasons.append(("unsupported_voice:" if voice_policy else "unsupported_source:") + str(source))
            continue
        if row.get("scenario") != group.get("scenario"):
            reasons.append("scenario_mismatch:" + source)
        if row.get("state_key") != group.get("state_key"):
            reasons.append("state_mismatch:" + source)
        if row.get("status") not in FULLY_RESOLVED_STATUSES:
            reasons.append("status_not_fully_resolved:" + source)
            continue
        if scenario_policy and scenario_spec is None:
            continue
        terms, reason = normalize_terms(
            row.get("terms"),
            interpolate_vehicle_axes=interpolate_vehicle_axes,
            scenario=scenario,
            scenario_policy=scenario_policy)
        if reason:
            reasons.append("axes:" + source + ":" + reason)
        else:
            normalized[source] = terms
    if voice_policy:
        if seen[CURRENT_VOICE] == 0:
            reasons.append("missing_voice:" + CURRENT_VOICE)
        elif seen[CURRENT_VOICE] > 1:
            reasons.append("duplicate_voice:" + CURRENT_VOICE)
        reference_counts = {source: seen[source] for source in REFERENCE_SOURCES}
        reference_count = sum(reference_counts.values())
        if reference_count != 3:
            reasons.append(f"reference_voice_count:expected=3:actual={reference_count}")
        for source, count in reference_counts.items():
            if count > 1:
                reasons.append("duplicate_reference_voice:" + source)
        if len(rows) != 4:
            reasons.append(f"voice_row_count:expected=4:actual={len(rows)}")
        reasons.extend("duplicate_voice:unknown" for source, count in seen.items()
                       if source not in (set(REFERENCE_SOURCES) | {CURRENT_VOICE}) and count > 1)
        required_sources = [CURRENT_VOICE] + sorted(
            source for source in REFERENCE_SOURCES if seen[source] == 1)
    else:
        for source in SOURCES:
            if seen[source] == 0:
                reasons.append("missing_source:" + source)
            elif seen[source] > 1:
                reasons.append("duplicate_source:" + source)
        reasons.extend("duplicate_source:unknown" for source, count in seen.items()
                       if source not in SOURCES and count > 1)
        required_sources = list(SOURCES)
    if reasons:
        return _unresolved(group, reasons, rows=rows, policy=policy)
    if voice_policy:
        policy["voices"] = list(required_sources)
        policy["voice_weights"] = {source: 0.25 for source in required_sources}
    source_rows = {source: copy.deepcopy(next(row for row in rows if row.get("source") == source))
                   for source in required_sources}
    return {
        "comparison_id": group["comparison_id"],
        "scenario": group["scenario"],
        "state_key": group["state_key"],
        "status": "RESOLVED",
        "sources": required_sources,
        "target_axes": copy.deepcopy(policy["target_axes"]),
        "policy": {
            **policy,
        },
        "source_rows": source_rows,
        "normalized_terms": normalized,
        "means": _mean_terms([normalized[source] for source in required_sources],
                              axes=policy["target_axes"]),
        "components": {
            source: {
                "clamped_hp_components": copy.deepcopy(source_rows[source].get("clamped_hp_components", [])),
                "direct_terms": copy.deepcopy(source_rows[source].get("direct_terms")),
                "ambient_terms": copy.deepcopy(source_rows[source].get("ambient_terms")),
                "preservation": "kept separate; not folded into affine means",
            }
            for source in required_sources
        },
    }


def combine_groups(groups, *, interpolate_vehicle_axes=False, scenario_policy=False,
                    voice_policy=False):
    if not isinstance(groups, list):
        raise ValueError("groups must be a list")
    results = [combine_group(group,
                             interpolate_vehicle_axes=interpolate_vehicle_axes,
                             scenario_policy=scenario_policy,
                             voice_policy=voice_policy)
               for group in groups]
    source_method = ("Exactly one Current Cameo row plus exactly three distinct reference rows is required in four-voice mode; any three reference sources may be used and missing voices are not renormalized."
                     if voice_policy else
                     "Exactly one fully RESOLVED row from each of the four named sources is required; missing rows are not renormalized.")
    counts = Counter(result.get("status", "UNRESOLVED") for result in results)
    return {
        "schema": 1,
        "scope": ("Review-only explicit four-voice armor synthesis gate; no source joins or balance writeback."
                  if voice_policy else
                  "Review-only explicit four-source armor synthesis gate; no source joins or balance writeback."),
        "method": [
            "Groups require an explicit comparison_id, scenario and state_key; the gate never infers matches.",
            source_method,
            "Light/Heavy are direct source axes. Missing vehicle intermediate axes use explicit Light-to-Heavy interpolation only when opted in.",
            "The explicit scenario_policy switch maps infantry None/Light to None/Flak/Plate, vehicle and ship Light/Heavy to Scout/Light/Medium/Heavy/Superheavy, and aircraft Light/Heavy to Fighter/Bomber/Helicopter/Spaceship.",
            "Vehicle Scout and Superheavy use one equal linear extrapolation step below Light and above Heavy; no source axis is silently aliased.",
            "Arithmetic/geometric means are diagnostic summaries after the gate; clamped HP, direct and ambient components remain separate.",
            "Target masks, cadence, DTA applicability and unsupported secondary payloads are caller-owned and cannot be inferred here.",
        ],
        "policy": {"sources": list(SOURCES), "common_axes": list(COMMON_AXES),
                   "voice_policy": bool(voice_policy),
                   "current_voice": CURRENT_VOICE if voice_policy else None,
                   "reference_sources": list(REFERENCE_SOURCES) if voice_policy else list(SOURCES),
                   "equal_voice_weight": 0.25 if voice_policy else None,
                   "interpolate_vehicle_axes": bool(interpolate_vehicle_axes),
                   "scenario_policy": bool(scenario_policy),
                   "scenario_policies": {
                       scenario: {
                           "name": details["name"],
                           "target_axes": list(details["target_axes"]),
                           "required_source_axes": list(details["required_source_axes"]),
                           "axis_mapping": details["axis_mapping"],
                       }
                       for scenario, details in SCENARIO_POLICIES.items()
                   },
                   "accepted_statuses": sorted(FULLY_RESOLVED_STATUSES),
                   "no_missing_source_renormalization": True},
        "summary": {"groups": len(results), "status_counts": dict(sorted(counts.items())),
                    "resolved": counts.get("RESOLVED", 0),
                    "unresolved": counts.get("UNRESOLVED", 0)},
        "groups": results,
    }


def render_markdown(result):
    summary = result.get("summary", {})
    policy = result.get("policy", {})
    lines = ["# Four-source synthesis gate", "",
             "**Review-only and fail-closed.** Explicit joins are required; no source, state or target match is inferred, and no Versus/YAML value is written.",
             "", "## Summary", "",
             f"- Groups: **{summary.get('groups', 0)}**; resolved: **{summary.get('resolved', 0)}**; unresolved: **{summary.get('unresolved', 0)}**.",
             "- Missing sources are never renormalized. Clamped HP and direct/ambient terms remain separate.",
             f"- Scenario policy enabled: **{policy.get('scenario_policy', False)}**; mappings are recorded per group.",
             f"- Four-voice policy enabled: **{policy.get('voice_policy', False)}**; Current Cameo plus three explicit reference voices when enabled.",
             "", "| comparison | scenario | state | status | target axes | mapping policy | reasons |",
             "|---|---|---|---|---|---|---|"]
    for group in result.get("groups", []):
        reasons = "; ".join(group.get("reasons", [])) or "—"
        target_axes = ", ".join(group.get("target_axes", [])) or "—"
        group_policy = group.get("policy", {})
        mapping = group_policy.get("scenario_policy_name") or "legacy_common_axes"
        lines.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            group.get("comparison_id", "—"), group.get("scenario", "—"),
            group.get("state_key", "—"), group.get("status", "—"),
            target_axes.replace("|", "\\|"), mapping.replace("|", "\\|"),
            reasons.replace("|", "\\|")))
    lines += ["", "Resolved means are diagnostic arithmetic/geometric summaries only; source-local armor, cadence, target eligibility and secondary payload limitations still require review."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--interpolate-vehicle-axes", action="store_true")
    parser.add_argument("--scenario-policy", action="store_true",
                        help="apply the explicit infantry, vehicle/ship and aircraft axis mappings")
    parser.add_argument("--voice-policy", action="store_true",
                        help="require Current Cameo plus exactly three explicit reference voices")
    args = parser.parse_args(argv)
    try:
        out_path = diagnostic_output.validate_path(ROOT, args.out)
        markdown_path = (diagnostic_output.validate_path(ROOT, args.markdown)
                         if args.markdown else None)
        if markdown_path is not None and markdown_path == out_path:
            raise ValueError("JSON and Markdown outputs must use different resolved paths")
        input_path = args.input.resolve()
        if not input_path.is_file():
            raise ValueError("input does not exist: " + str(input_path))
        data = json.loads(input_path.read_text(encoding="utf-8"))
        result = combine_groups(data.get("groups"),
                                interpolate_vehicle_axes=args.interpolate_vehicle_axes,
                                scenario_policy=args.scenario_policy,
                                voice_policy=args.voice_policy)
        outputs = {out_path: json.dumps(result, indent=2, ensure_ascii=False) + "\n"}
        if markdown_path is not None:
            outputs[markdown_path] = render_markdown(result)
        diagnostic_output.write_outputs(ROOT, outputs)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(result["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
