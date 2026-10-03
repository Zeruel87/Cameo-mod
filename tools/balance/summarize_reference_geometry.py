#!/usr/bin/env python3
"""Summarize source-local weapon geometry without cross-source comparison."""
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
GEOMETRY_FIELDS = ("spread", "range", "projectile_range", "falloff")
INPUT_DEFAULT = (Path(r"C:\Users\Blackrobe\Documents\agents\cameo-reference-sources-20260909") /
                 "validation/reference-weapon-geometry-20260911/reference_weapon_geometry.json")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _finite(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _field(record, name):
    geometry = record.get("geometry") if isinstance(record, Mapping) else None
    field = geometry.get(name) if isinstance(geometry, Mapping) else None
    if isinstance(field, Mapping):
        return field
    return {"source_field": None, "raw": None, "values": [],
            "tokens": [], "status": "ABSENT"}


def falloff_shape_metrics(field):
    """Describe numeric Falloff token shape while preserving field status."""
    field = field if isinstance(field, Mapping) else {}
    values = []
    raw_values = field.get("values")
    if isinstance(raw_values, (list, tuple)):
        for raw in raw_values:
            value = _finite(raw)
            if value is not None:
                values.append(value)
    tokens = field.get("tokens") if isinstance(field.get("tokens"), list) else []
    unparsed = sum(token.get("status") == "SOURCE_TOKEN_UNPARSED"
                   for token in tokens if isinstance(token, Mapping))
    malformed = sum(token.get("status") == "MALFORMED"
                    for token in tokens if isinstance(token, Mapping))
    counts = collections.Counter(values)
    repeated = []
    for value in values:
        if counts[value] > 1 and value not in repeated:
            repeated.append(value)
    zero_indices = [index for index, value in enumerate(values) if value == 0]
    return {
        "field_status": field.get("status", "ABSENT"),
        "numeric_token_count": len(values),
        "first": values[0] if values else None,
        "last": values[-1] if values else None,
        "zero_index": zero_indices[0] if zero_indices else None,
        "zero_indices": zero_indices,
        "non_increasing": (all(left >= right for left, right in zip(values, values[1:]))
                           if values else None),
        "repeated_values": repeated,
        "has_repeated_values": bool(repeated),
        "unparsed_token_count": unparsed,
        "malformed_token_count": malformed,
    }


def _identity(record, input_index):
    names = ("source", "actor", "source_actor", "reference_id", "slot",
             "weapon", "warhead", "warhead_type", "channel_index",
             "warhead_index")
    return {name: record.get(name) for name in names} | {"input_index": input_index}


def _record_entry(record, input_index):
    fields = {name: _field(record, name) for name in GEOMETRY_FIELDS}
    falloff = fields["falloff"]
    return {
        "identity": _identity(record, input_index),
        "record_status": record.get("status"),
        "geometry_gap": bool(record.get("geometry_gap")),
        "inheritance_status": record.get("inheritance_status"),
        "raw_geometry": {name: field.get("raw") for name, field in fields.items()},
        "geometry_field_status": {name: field.get("status", "ABSENT")
                                  for name, field in fields.items()},
        "geometry_source_fields": {name: field.get("source_field")
                                   for name, field in fields.items()},
        "falloff_shape": falloff_shape_metrics(falloff),
    }


def _coverage_entry():
    return {
        "record_count": 0,
        "geometry_gap_records": 0,
        "field_status_counts": collections.defaultdict(collections.Counter),
        "falloff_shape": {
            "records_with_numeric_tokens": 0,
            "numeric_token_count_total": 0,
            "numeric_token_count_max": 0,
            "zero_index_counts": collections.Counter(),
            "non_increasing_counts": collections.Counter(),
            "records_with_repeated_values": 0,
            "records_with_unparsed_tokens": 0,
            "records_with_malformed_tokens": 0,
        },
        "records": [],
    }


def _add_entry(group, entry):
    group["record_count"] += 1
    group["geometry_gap_records"] += int(entry["geometry_gap"])
    for name, status in entry["geometry_field_status"].items():
        group["field_status_counts"][name][status] += 1
    shape = entry["falloff_shape"]
    shape_summary = group["falloff_shape"]
    numeric_count = shape["numeric_token_count"]
    if numeric_count:
        shape_summary["records_with_numeric_tokens"] += 1
    shape_summary["numeric_token_count_total"] += numeric_count
    shape_summary["numeric_token_count_max"] = max(
        shape_summary["numeric_token_count_max"], numeric_count)
    zero_key = str(shape["zero_index"]) if shape["zero_index"] is not None else "none"
    shape_summary["zero_index_counts"][zero_key] += 1
    increasing_key = (str(shape["non_increasing"]).lower()
                      if shape["non_increasing"] is not None else "unavailable")
    shape_summary["non_increasing_counts"][increasing_key] += 1
    shape_summary["records_with_repeated_values"] += int(shape["has_repeated_values"])
    shape_summary["records_with_unparsed_tokens"] += int(shape["unparsed_token_count"] > 0)
    shape_summary["records_with_malformed_tokens"] += int(shape["malformed_token_count"] > 0)
    group["records"].append(entry)


def _exemplars(entries, limit=3):
    """Choose compact representatives without discarding group records."""
    chosen = []
    categories = (
        lambda entry: entry["falloff_shape"]["numeric_token_count"] > 0,
        lambda entry: entry["falloff_shape"]["unparsed_token_count"] > 0,
        lambda entry: entry["falloff_shape"]["field_status"] in (
            "ABSENT", "EXPLICIT_EMPTY", "MALFORMED", "INHERITED_UNRESOLVED"),
    )
    for category in categories:
        item = next((entry for entry in entries
                     if category(entry) and entry not in chosen), None)
        if item is not None:
            chosen.append(item)
        if len(chosen) == limit:
            return chosen
    for entry in entries:
        if entry not in chosen:
            chosen.append(entry)
        if len(chosen) == limit:
            break
    return chosen


def _regularize(value):
    if isinstance(value, collections.Counter):
        return dict(sorted(value.items()))
    if isinstance(value, collections.defaultdict):
        return {key: _regularize(item) for key, item in sorted(value.items())}
    if isinstance(value, dict):
        return {key: _regularize(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_regularize(item) for item in value]
    return value


def validate_input(data):
    if not isinstance(data, Mapping) or not isinstance(data.get("records"), list):
        raise ValueError("geometry input records must be a list")
    return data


def build(data, *, provenance=None, input_path=None):
    """Group geometry records without mutating the input report."""
    validate_input(data)
    grouped = collections.defaultdict(lambda: {"warhead_types": collections.defaultdict(_coverage_entry)})
    field_status_counts = collections.defaultdict(collections.Counter)
    source_counts = collections.Counter()
    status_counts = collections.Counter()
    geometry_gap_records = 0
    for input_index, record in enumerate(data["records"]):
        if not isinstance(record, Mapping):
            raise ValueError(f"geometry input record {input_index} must be an object")
        source = record.get("source") or "UNKNOWN"
        warhead_type = record.get("warhead_type") or "UNKNOWN"
        entry = _record_entry(record, input_index)
        group = grouped[source]["warhead_types"][warhead_type]
        _add_entry(group, entry)
        source_counts[source] += 1
        status_counts[record.get("status") or "UNKNOWN"] += 1
        geometry_gap_records += int(entry["geometry_gap"])
        for name, status in entry["geometry_field_status"].items():
            field_status_counts[name][status] += 1

    for source_info in grouped.values():
        for group in source_info["warhead_types"].values():
            group["exemplars"] = _exemplars(group["records"])

    summary = {
        "input_records": len(data["records"]),
        "source_counts": dict(sorted(source_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "group_count": sum(len(info["warhead_types"]) for info in grouped.values()),
        "geometry_gap_records": geometry_gap_records,
        "field_status_counts": _regularize(field_status_counts),
        "falloff_shape_records_with_numeric_tokens": sum(
            group["falloff_shape"]["records_with_numeric_tokens"]
            for info in grouped.values() for group in info["warhead_types"].values()),
        "falloff_records_with_unparsed_tokens": sum(
            group["falloff_shape"]["records_with_unparsed_tokens"]
            for info in grouped.values() for group in info["warhead_types"].values()),
        "falloff_records_with_malformed_tokens": sum(
            group["falloff_shape"]["records_with_malformed_tokens"]
            for info in grouped.values() for group in info["warhead_types"].values()),
    }
    result = {
        "schema": 1,
        "scope": (
            "Review-only shape summary of source-local geometry. Raw Spread, "
            "Range, projectile_range and Falloff values remain grouped by source "
            "and warhead type; no source units are compared or normalized."
        ),
        "method": [
            "Groups retain source, actor, source actor, slot, weapon, warhead and input index for every input record; equal names are not treated as shared families.",
            "Falloff shape metrics describe only retained numeric tokens: count, first/last, first zero index, non-increasing order and repeated values.",
            "Absent, explicit empty, malformed and source-token-unparsed states remain distinct; raw fields are retained in each grouped record.",
            "Falloff values are source-declared numbers. Even percentage-looking entries may differ in meaning without source proof, so no cross-source shape or unit comparison is made.",
            "Projectile travel speed remains separate; no runtime density, impact-radius behavior or target selection is inferred.",
        ],
        "source_geometry_semantics": data.get("source_geometry_semantics", {}),
        "summary": summary,
        "groups": _regularize(grouped),
        "input_report_metadata": {
            key: data.get(key) for key in (
                "schema", "matrix_path", "matrix_sha256", "tool_sha256")
        },
    }
    if provenance is not None:
        input_key = str(Path(input_path).resolve()) if input_path else None
        result.update({"input_path": input_key,
                       "input_sha256": provenance["files_sha256"].get(input_key),
                       "input_fingerprints_before": provenance})
    return result


def input_fingerprints(input_path):
    input_path = Path(input_path).resolve()
    paths = {
        "tools/balance/summarize_reference_geometry.py": ROOT / "tools/balance/summarize_reference_geometry.py",
        "tools/balance/diagnostic_output.py": ROOT / "tools/balance/diagnostic_output.py",
        str(input_path): input_path,
    }
    return {"files_sha256": {
        name: _sha256(path) for name, path in sorted(paths.items())}}


def build_from_path(input_path):
    input_path = Path(input_path).resolve()
    data = json.loads(input_path.read_text(encoding="utf-8"))
    before = input_fingerprints(input_path)
    result = build(data, provenance=before, input_path=input_path)
    after = input_fingerprints(input_path)
    if after != before:
        raise ValueError("geometry input or summarizer helper inputs changed during collection")
    result["input_fingerprints_after"] = after
    result["input_guard"] = {"before": before, "after": after, "unchanged": True}
    return result


def _fmt(value):
    if value is None:
        return "—"
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return str(value)


def _field_status_text(statuses):
    return ", ".join(f"{key}:{value}" for key, value in sorted(statuses.items())) or "—"


def _shape_text(shape):
    if not shape:
        return "—"
    values = (
        f"n={shape.get('numeric_token_count', 0)}",
        f"first={_fmt(shape.get('first'))}",
        f"last={_fmt(shape.get('last'))}",
        f"zero={shape.get('zero_index')}",
        f"non-increasing={shape.get('non_increasing')}",
        f"repeated={shape.get('repeated_values') or '—'}",
    )
    return "; ".join(values)


def _raw_text(raw):
    if raw is None:
        return "—"
    return str(raw).replace("|", "\\|").replace("\n", " ")


def render_markdown(result):
    summary = result.get("summary") or {}
    lines = [
        "# Reference weapon geometry shape summary", "",
        "**Review-only and unapproved.** This summary describes source-declared geometry shapes and preserves raw fields; it proposes no YAML, runtime or balance values.",
        "", "## Scope and caveats", "",
    ]
    lines.extend(f"- {item}" for item in result.get("method", []))
    lines += [
        "", "## Summary", "",
        f"- Input geometry records: **{summary.get('input_records', 0)}**; source/type groups: **{summary.get('group_count', 0)}**; geometry-gap records: **{summary.get('geometry_gap_records', 0)}**.",
        f"- Numeric Falloff records: **{summary.get('falloff_shape_records_with_numeric_tokens', 0)}**; unparsed Falloff records: **{summary.get('falloff_records_with_unparsed_tokens', 0)}**; malformed Falloff records: **{summary.get('falloff_records_with_malformed_tokens', 0)}**.",
        "", "## Coverage by source and warhead type", "",
        "| source | warhead type | records | spread statuses | range statuses | projectile range statuses | falloff statuses | numeric Falloff records | non-increasing true/false/unavailable | repeated Falloff records | gaps |",
        "|---|---|---:|---|---|---|---|---:|---|---:|---:|",
    ]
    for source, source_info in sorted((result.get("groups") or {}).items()):
        for warhead_type, group in sorted((source_info.get("warhead_types") or {}).items()):
            fields = group.get("field_status_counts") or {}
            shape = group.get("falloff_shape") or {}
            increasing = shape.get("non_increasing_counts") or {}
            lines.append(
                "| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                    str(source).replace("|", "\\|"), str(warhead_type).replace("|", "\\|"),
                    group.get("record_count", 0),
                    _field_status_text(fields.get("spread") or {}),
                    _field_status_text(fields.get("range") or {}),
                    _field_status_text(fields.get("projectile_range") or {}),
                    _field_status_text(fields.get("falloff") or {}),
                    shape.get("records_with_numeric_tokens", 0),
                    _field_status_text(increasing),
                    shape.get("records_with_repeated_values", 0),
                    group.get("geometry_gap_records", 0)))
    lines += [
        "", "## Compact exemplars", "",
        "Raw geometry is retained for every grouped record in JSON. These examples show identity, raw values and Falloff metrics without treating equal names as equal families.",
        "", "| source | type | actor | source actor | slot | weapon | warhead | raw Spread | raw Range | raw projectile_range | raw Falloff | Falloff shape |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for source, source_info in sorted((result.get("groups") or {}).items()):
        for warhead_type, group in sorted((source_info.get("warhead_types") or {}).items()):
            for entry in group.get("exemplars") or []:
                identity = entry.get("identity") or {}
                raw = entry.get("raw_geometry") or {}
                values = [source, warhead_type, identity.get("actor"),
                          identity.get("source_actor"), identity.get("slot"),
                          identity.get("weapon"), identity.get("warhead"),
                          raw.get("spread"), raw.get("range"),
                          raw.get("projectile_range"), raw.get("falloff"),
                          _shape_text(entry.get("falloff_shape"))]
                lines.append("| " + " | ".join(_raw_text(value) for value in values) + " |")
    lines += [
        "", "The JSON retains exact raw Spread, Range, projectile_range and Falloff values and field statuses for every record. Numeric Falloff shape metrics are descriptive only; they do not establish shared percentage semantics, runtime impact-radius behavior, target density, or cross-source equivalence. Projectile travel speed remains outside this report.",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", type=Path, default=INPUT_DEFAULT)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)
    try:
        out_path = diagnostic_output.validate_path(ROOT, args.out)
        markdown_path = (diagnostic_output.validate_path(ROOT, args.markdown)
                         if args.markdown else None)
        if markdown_path is not None and markdown_path == out_path:
            raise ValueError("JSON and Markdown outputs must use different resolved paths")
        input_path = args.input.resolve()
        if not input_path.is_file():
            raise ValueError(f"geometry input does not exist: {input_path}")
        result = build_from_path(input_path)
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
