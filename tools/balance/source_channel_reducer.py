"""Review-only reducer for explicitly grouped source channel rows.

The caller must select the rows and declare their source, comparison, scenario,
and state group. This module only sums already validated affine terms within
that explicit group; it performs no joins, axis normalization, policy mapping,
or gameplay/writeback operations.
"""
from __future__ import annotations

import copy
import json
import math
from collections.abc import Mapping


AGGREGATION = "explicit_source_group_sum"
_MISSING = object()
_TERM_ALIASES = {
    "A": ("A", "flat"),
    "B": ("B", "max_hp_fraction"),
}
_GROUP_ALIASES = {
    "comparison_id": ("comparison_id", "group_id", "group_key", "comparison_group"),
    "scenario": ("scenario", "group_scenario"),
    "state_key": ("state_key", "state", "group_state", "group_state_key"),
}


def _copy(value):
    return copy.deepcopy(value)


def _missing(value):
    return value is None or value == ""


def _same(left, right):
    try:
        return left == right
    except (TypeError, ValueError):
        return repr(left) == repr(right)


def _finite(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _value_error(value, index, axis, label):
    if value is _MISSING or value is None:
        return f"term_missing:{index}:{axis}.{label}"
    if isinstance(value, bool):
        return f"term_bool:{index}:{axis}.{label}"
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return f"term_nonnumeric:{index}:{axis}.{label}"
    if not math.isfinite(number):
        return f"term_nonfinite:{index}:{axis}.{label}"
    if number < 0:
        return f"term_negative:{index}:{axis}.{label}"
    return None


def _term_value(term, index, axis, label):
    aliases = _TERM_ALIASES[label]
    present = [(key, term[key]) for key in aliases if key in term]
    if not present:
        return None, _value_error(_MISSING, index, axis, label)
    errors = [_value_error(value, index, axis, label) for _, value in present]
    errors = [error for error in errors if error]
    if errors:
        return None, errors[0]
    values = [float(value) for _, value in present]
    if len(values) > 1 and any(value != values[0] for value in values[1:]):
        return None, f"term_alias_conflict:{index}:{axis}.{label}"
    return values[0], None


def _validated_terms(raw_terms, index):
    if not isinstance(raw_terms, Mapping):
        return None, [f"terms_not_mapping:{index}"]
    if not raw_terms:
        return None, [f"terms_empty:{index}"]

    allowed = {alias for aliases in _TERM_ALIASES.values() for alias in aliases}
    reasons = [f"term_unknown_key:{index}:{key}" for axis_term in raw_terms.values()
               if isinstance(axis_term, Mapping)
               for key in axis_term if key not in allowed]
    validated = {}
    for axis, raw_term in raw_terms.items():
        if not isinstance(raw_term, Mapping):
            reasons.append(f"term_not_mapping:{index}:{axis}")
            continue
        values = {}
        for label in ("A", "B"):
            value, reason = _term_value(raw_term, index, axis, label)
            if reason:
                reasons.append(reason)
            else:
                values[label] = value
        if len(values) == 2:
            validated[axis] = {
                "A": values["A"],
                "B": values["B"],
                "flat": values["A"],
                "max_hp_fraction": values["B"],
            }
    return (validated if not reasons else None), reasons


def _row_group_value(row, field):
    """Read only explicitly named metadata fields; never derive a group."""
    containers = [row]
    for nested_name in ("group", "group_fields"):
        nested = row.get(nested_name)
        if isinstance(nested, Mapping):
            containers.append(nested)
    values = []
    for container in containers:
        for key in _GROUP_ALIASES[field]:
            if key in container:
                values.append((key, container[key]))
    if not values:
        return _MISSING, None
    first = values[0][1]
    if any(not _same(first, value) for _, value in values[1:]):
        return _MISSING, f"{field}_alias_conflict"
    return first, None


def _identity_key(value):
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError):
        encoded = repr(value)
    return type(value).__name__, encoded


def _flatten(value):
    if isinstance(value, (list, tuple)):
        flattened = []
        for item in value:
            flattened.extend(_flatten(item))
        return flattened
    return [_copy(value)]


def _evidence(rows, primary, fallback=None):
    result = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, Mapping):
            continue
        value = row.get(primary, _MISSING)
        if value is _MISSING and fallback is not None:
            value = row.get(fallback, _MISSING)
        if value is _MISSING or value is None:
            continue
        result.extend(_flatten(value))
    return result


def _base_result(rows, source, comparison_id, scenario, state_key, reasons):
    row_count = len(rows) if isinstance(rows, list) else 0
    source_copy = _copy(source)
    comparison_copy = _copy(comparison_id)
    scenario_copy = _copy(scenario)
    state_copy = _copy(state_key)
    retained = _copy(rows)
    clamped = _evidence(rows, "clamped_hp_components")
    direct = _evidence(rows, "direct_components", "direct_terms")
    ambient = _evidence(rows, "ambient_components", "ambient_terms")
    direct_terms = _evidence(rows, "direct_terms")
    ambient_terms = _evidence(rows, "ambient_terms")
    provenance = {
        "aggregation": AGGREGATION,
        "input_row_count": row_count,
        "group": {
            "source": source_copy,
            "comparison_id": comparison_copy,
            "scenario": scenario_copy,
            "state_key": state_copy,
        },
        "selection": "caller-supplied already-selected rows",
        "joins": "caller-owned",
        "axis_policy": "preserve caller axes verbatim; no normalization or mapping",
        "writeback": False,
    }
    return {
        "source": source_copy,
        "comparison_id": comparison_copy,
        "scenario": scenario_copy,
        "state_key": state_copy,
        "status": "UNRESOLVED" if reasons else "RESOLVED",
        "terms": None,
        "aggregation": AGGREGATION,
        "input_rows": retained,
        "clamped_hp_components": clamped,
        "direct_components": direct,
        "ambient_components": ambient,
        "direct_terms": direct_terms,
        "ambient_terms": ambient_terms,
        "provenance": provenance,
        "reasons": sorted(set(reasons)),
    }


def reduce_source_group(rows, source=None, comparison_id=None, scenario=None,
                        state_key=None):
    """Sum validated A/B terms from one caller-declared source/group.

    The returned object is a four-source-gate-compatible source row. A bad
    group is represented as ``UNRESOLVED`` with reasons and retained evidence;
    no partial total is returned.
    """
    reasons = []
    for name, value in (("source", source), ("comparison_id", comparison_id),
                        ("scenario", scenario), ("state_key", state_key)):
        if _missing(value):
            reasons.append(f"{name}_required")
    if not isinstance(rows, list):
        reasons.append("rows_not_list")
        return _base_result(rows, source, comparison_id, scenario, state_key, reasons)
    if not rows:
        reasons.append("rows_empty")
        return _base_result(rows, source, comparison_id, scenario, state_key, reasons)

    axes = None
    totals = None
    seen_identities = {}
    validated_rows = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            reasons.append(f"row_not_object:{index}")
            continue

        actual_source = row.get("source", _MISSING)
        if actual_source is _MISSING:
            reasons.append(f"source_missing:{index}")
        elif not _same(actual_source, source):
            reasons.append(f"source_mismatch:{index}:{actual_source!r}")

        for field, expected in (("comparison_id", comparison_id),
                                ("scenario", scenario),
                                ("state_key", state_key)):
            actual, alias_reason = _row_group_value(row, field)
            if alias_reason:
                reasons.append(f"{field}:{index}:{alias_reason}")
            elif actual is not _MISSING and not _same(actual, expected):
                reasons.append(f"{field}_mismatch:{index}:{actual!r}")

        if row.get("status") != "RESOLVED":
            reasons.append(f"status_not_resolved:{index}:{row.get('status')!r}")
            continue

        identity = row.get("channel_identity", _MISSING)
        legacy_identity = row.get("identity", _MISSING)
        if identity is not _MISSING and legacy_identity is not _MISSING:
            if not _same(identity, legacy_identity):
                reasons.append(f"identity_alias_conflict:{index}")
            identity_value = identity
        elif identity is not _MISSING:
            identity_value = identity
        elif legacy_identity is not _MISSING:
            identity_value = legacy_identity
        else:
            identity_value = _MISSING
        if identity_value is not _MISSING and identity_value is not None:
            key = _identity_key(identity_value)
            if key in seen_identities:
                reasons.append(
                    f"duplicate_channel_identity:{seen_identities[key]},{index}")
            else:
                seen_identities[key] = index

        raw_terms = row.get("terms", _MISSING)
        if raw_terms is _MISSING:
            reasons.append(f"terms_missing:{index}")
            continue
        if axes is None and isinstance(raw_terms, Mapping):
            axes = list(raw_terms.keys())
            totals = {axis: {"A": 0.0, "B": 0.0} for axis in axes}
        elif isinstance(raw_terms, Mapping) and set(raw_terms.keys()) != set(axes or ()):
            expected_axes = list(axes or ())
            actual_axes = list(raw_terms.keys())
            reasons.append(f"axes_mismatch:{index}:expected={expected_axes!r}:actual={actual_axes!r}")

        validated, term_reasons = _validated_terms(raw_terms, index)
        reasons.extend(term_reasons)
        if validated is None:
            continue
        if axes is None:
            axes = list(validated.keys())
            totals = {axis: {"A": 0.0, "B": 0.0} for axis in axes}
        if list(validated.keys()) != axes:
            # The set check above is the semantic check; this preserves the
            # first row's caller-provided order after validation.
            if set(validated.keys()) != set(axes):
                reasons.append(f"axes_mismatch:{index}:validated")
                continue
        for axis in axes:
            if axis not in validated:
                continue
            for label in ("A", "B"):
                totals[axis][label] += validated[axis][label]
                if not math.isfinite(totals[axis][label]):
                    reasons.append(f"aggregate_nonfinite:{axis}.{label}")
        validated_rows.append(index)

    result = _base_result(rows, source, comparison_id, scenario, state_key, reasons)
    if reasons:
        return result
    if not axes or totals is None or len(validated_rows) != len(rows):
        result["reasons"] = ["no_validated_rows"]
        result["status"] = "UNRESOLVED"
        return result
    result["terms"] = {
        axis: {
            "A": totals[axis]["A"],
            "B": totals[axis]["B"],
            "flat": totals[axis]["A"],
            "max_hp_fraction": totals[axis]["B"],
        }
        for axis in axes
    }
    return result


# Descriptive alias for callers that use the channel-oriented name.
reduce_source_channels = reduce_source_group


__all__ = ["AGGREGATION", "reduce_source_group", "reduce_source_channels"]
