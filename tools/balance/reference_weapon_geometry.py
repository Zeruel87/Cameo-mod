#!/usr/bin/env python3
"""Review-only inventory of source-local weapon geometry declarations.

The extractor preserves the raw geometry strings from the retained pilot
matrix and parses only unambiguous numeric tokens.  It does not compare source
units, infer target density or runtime radius, or write YAML/stat values.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import re
from collections.abc import Mapping
from pathlib import Path

import diagnostic_output

ROOT = Path(__file__).resolve().parents[2]
MATRIX_DEFAULT = (Path(r"C:\Users\Blackrobe\Documents\agents\cameo-reference-sources-20260909") /
                  "validation/four-faction-sunday-pilot/warhead-reference-freshness/"
                  "pilot-warhead-review.json")
CURRENT_SOURCE = "Cameo"
KNOWN_REFERENCE_SOURCES = (
    "Combined Arms", "OpenRA Red Alert", "OpenRA Tiberian Dawn", "DTA Enhanced"
)
GEOMETRY_FIELDS = ("spread", "range", "projectile_range", "falloff")
_NUMERIC_TOKEN = re.compile(
    r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
_CELL_TOKEN = re.compile(r"^[+-]?\d+c\d+$", re.IGNORECASE)

# These are paths and semantics for the retained exports, not conversions or
# claims about installed runtime units.  DTA has both weapon range and a
# distinct projectile-range field in its selected channel exports.
SOURCE_GEOMETRY = {
    CURRENT_SOURCE: {
        "spread": {"path": "cameo_channels[].warheads[].spread",
                    "aliases": ("spread",), "kind": "scalar",
                    "allow_cell_tokens": False,
                    "units": "current Cameo exported impact-radius units; raw only"},
        "range": {"path": "cameo_channels[].warheads[].range",
                   "aliases": (), "kind": "list",
                   "allow_cell_tokens": False,
                   "units": "not retained in the current Cameo warhead export"},
        "falloff": {"path": "cameo_channels[].warheads[].falloff",
                     "aliases": ("falloff",), "kind": "list",
                     "allow_cell_tokens": False,
                     "units": "current Cameo exported falloff percentages"},
    },
    "Combined Arms": {
        "spread": {"path": "fields.Spread", "aliases": ("Spread",),
                    "kind": "scalar", "allow_cell_tokens": False,
                    "units": "Combined Arms/OpenRA source-local impact-radius units"},
        "range": {"path": "fields.Range", "aliases": ("Range",),
                   "kind": "list", "allow_cell_tokens": True,
                   "units": "Combined Arms/OpenRA Range tokens; c cell tokens stay raw"},
        "falloff": {"path": "fields.Falloff", "aliases": ("Falloff",),
                     "kind": "list", "allow_cell_tokens": False,
                     "units": "Combined Arms/OpenRA falloff percentages"},
    },
    "OpenRA Red Alert": {
        "spread": {"path": "fields.Spread", "aliases": ("Spread",),
                    "kind": "scalar", "allow_cell_tokens": False,
                    "units": "OpenRA Red Alert source-local impact-radius units"},
        "range": {"path": "fields.Range", "aliases": ("Range",),
                   "kind": "list", "allow_cell_tokens": True,
                   "units": "OpenRA Red Alert Range tokens; c cell tokens stay raw"},
        "falloff": {"path": "fields.Falloff", "aliases": ("Falloff",),
                     "kind": "list", "allow_cell_tokens": False,
                     "units": "OpenRA Red Alert falloff percentages"},
    },
    "OpenRA Tiberian Dawn": {
        "spread": {"path": "fields.Spread", "aliases": ("Spread",),
                    "kind": "scalar", "allow_cell_tokens": False,
                    "units": "OpenRA Tiberian Dawn source-local impact-radius units"},
        "range": {"path": "fields.Range", "aliases": ("Range",),
                   "kind": "list", "allow_cell_tokens": True,
                   "units": "OpenRA Tiberian Dawn Range tokens; c cell tokens stay raw"},
        "falloff": {"path": "fields.Falloff", "aliases": ("Falloff",),
                     "kind": "list", "allow_cell_tokens": False,
                     "units": "OpenRA Tiberian Dawn falloff percentages"},
    },
    "DTA Enhanced": {
        "spread": {"path": "fields.spread", "aliases": ("spread", "Spread"),
                    "kind": "scalar", "allow_cell_tokens": False,
                    "units": "DTA source-local impact-radius units"},
        "range": {"path": "fields.range", "aliases": ("range", "Range"),
                   "kind": "list", "allow_cell_tokens": False,
                   "units": "DTA source-local weapon-range units"},
        "projectile_range": {
            "path": "fields.projectilerange",
            "aliases": ("projectilerange", "ProjectileRange"),
            "kind": "scalar", "allow_cell_tokens": False,
            "units": "DTA source-local projectile-range units; kept separate from range",
        },
        "falloff": {"path": "fields.falloff", "aliases": ("falloff", "Falloff"),
                     "kind": "list", "allow_cell_tokens": False,
                     "units": "DTA source-local falloff entries"},
    },
}


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


def _field(channel, aliases):
    """Return (present, raw, source field path), preferring nested fields."""
    if not isinstance(channel, Mapping):
        return False, None, None
    containers = []
    fields = channel.get("fields")
    if isinstance(fields, Mapping):
        containers.append(("fields", fields))
    containers.append((None, channel))
    for prefix, container in containers:
        for alias in aliases:
            if alias in container:
                path = f"{prefix}.{alias}" if prefix else alias
                return True, container[alias], path
        # Preserve the actual spelling while allowing a source adapter to use
        # a case variant of its declared field name.
        lowered = {str(key).lower(): key for key in container}
        for alias in aliases:
            actual = lowered.get(alias.lower())
            if actual is not None:
                path = f"{prefix}.{actual}" if prefix else str(actual)
                return True, container[actual], path
    return False, None, None


def _tokens(raw):
    if isinstance(raw, (list, tuple)):
        return list(raw)
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        if "," in text:
            return [piece.strip() for piece in text.split(",")]
        return text.split() if any(char.isspace() for char in text) else [text]
    return [raw]


def _parse_token(raw, *, allow_cell_tokens=False):
    if isinstance(raw, bool) or raw is None:
        return {"raw": raw, "status": "MALFORMED", "value": None}
    if isinstance(raw, (int, float)):
        value = _finite(raw)
        if value is not None and value >= 0:
            return {"raw": raw, "status": "NUMERIC", "value": value}
        return {"raw": raw, "status": "MALFORMED", "value": None}
    text = str(raw).strip()
    if _NUMERIC_TOKEN.fullmatch(text):
        value = _finite(text)
        if value is not None and value >= 0:
            return {"raw": raw, "status": "NUMERIC", "value": value}
        return {"raw": raw, "status": "MALFORMED", "value": None}
    if allow_cell_tokens and _CELL_TOKEN.fullmatch(text):
        return {"raw": raw, "status": "SOURCE_TOKEN_UNPARSED",
                "value": None, "kind": "cell_distance"}
    return {"raw": raw, "status": "MALFORMED", "value": None}


def parse_geometry_field(raw, *, present, source_field, kind="scalar",
                        allow_cell_tokens=False, inherited_unresolved=False):
    """Parse one geometry field while retaining raw and source-local tokens."""
    result = {"source_field": source_field, "raw": raw, "values": [],
              "tokens": []}
    if not present or raw is None:
        result["status"] = ("INHERITED_UNRESOLVED" if inherited_unresolved
                             else "ABSENT")
        return result
    pieces = _tokens(raw)
    if not pieces:
        result["status"] = "EXPLICIT_EMPTY"
        return result
    result["tokens"] = [_parse_token(piece, allow_cell_tokens=allow_cell_tokens)
                         for piece in pieces]
    values = [token["value"] for token in result["tokens"]
              if token.get("status") == "NUMERIC"]
    result["values"] = values
    if kind == "scalar" and len(pieces) != 1:
        result["status"] = "MALFORMED"
        result["reason"] = "scalar_field_has_multiple_tokens"
        return result
    if any(token["status"] == "MALFORMED" for token in result["tokens"]):
        result["status"] = "MALFORMED"
    elif any(token["status"] == "SOURCE_TOKEN_UNPARSED"
             for token in result["tokens"]):
        result["status"] = "PRESENT_WITH_UNPARSED_TOKENS"
    elif values and all(value == 0 for value in values):
        result["status"] = "PRESENT_ZERO"
    else:
        result["status"] = "PRESENT"
    result["contains_zero"] = any(value == 0 for value in values)
    return result


def _inherited_unresolved(channel):
    if not isinstance(channel, Mapping):
        return False
    value = channel.get("inheritance_status")
    if value is None:
        return False
    text = str(value).lower()
    return any(marker in text for marker in ("unresolved", "missing", "unknown", "failed"))


def source_geometry_specs(source):
    """Return the source-local geometry field declarations used by extraction."""
    if source in SOURCE_GEOMETRY:
        return SOURCE_GEOMETRY[source]
    return {
        "spread": {"path": "fields.Spread", "aliases": ("Spread",),
                    "kind": "scalar", "allow_cell_tokens": False,
                    "units": "unknown source-local impact-radius units; raw only"},
        "range": {"path": "fields.Range", "aliases": ("Range",),
                   "kind": "list", "allow_cell_tokens": True,
                   "units": "unknown source-local range tokens; raw only"},
        "falloff": {"path": "fields.Falloff", "aliases": ("Falloff",),
                     "kind": "list", "allow_cell_tokens": False,
                     "units": "unknown source-local falloff entries"},
    }


def extract_geometry(channel, source, *, current=False):
    """Extract geometry fields from one raw current or selected reference row."""
    specs = source_geometry_specs(source)
    geometry = {}
    inherited = _inherited_unresolved(channel)
    for name, spec in specs.items():
        present, raw, actual = _field(channel, spec["aliases"])
        geometry[name] = parse_geometry_field(
            raw, present=present, source_field=actual or spec["path"],
            kind=spec["kind"], allow_cell_tokens=spec["allow_cell_tokens"],
            inherited_unresolved=inherited)
    return geometry


def _record_status(geometry):
    statuses = [field["status"] for field in geometry.values()]
    if any(status == "MALFORMED" for status in statuses):
        return "MALFORMED"
    if any(status == "INHERITED_UNRESOLVED" for status in statuses):
        return "INHERITED_UNRESOLVED"
    if all(status in ("ABSENT", "EXPLICIT_EMPTY") for status in statuses):
        return "ABSENT_OR_EMPTY"
    if any(status in ("ABSENT", "EXPLICIT_EMPTY") for status in statuses):
        return "PARTIAL"
    if any(status == "PRESENT_WITH_UNPARSED_TOKENS" for status in statuses):
        return "PRESENT_WITH_UNPARSED_TOKENS"
    return "PRESENT"


def _record_gap(geometry):
    return any(field["status"] in ("ABSENT", "MALFORMED", "INHERITED_UNRESOLVED")
               for field in geometry.values())


def _base_record(*, source, matrix_actor, source_actor, slot, weapon, warhead,
                 warhead_type, channel_index, warhead_index=None,
                 reference_id=None, channel_source=None, metadata=None,
                 inheritance_status=None):
    return {
        "source": source,
        "actor": matrix_actor,
        "source_actor": source_actor,
        "reference_id": reference_id,
        "channel_source": channel_source,
        "slot": slot,
        "weapon": weapon,
        "warhead": warhead,
        "warhead_type": warhead_type,
        "channel_index": channel_index,
        "warhead_index": warhead_index,
        "metadata": metadata or {},
        "inheritance_status": inheritance_status,
    }


def _complete_record(record, geometry):
    record["geometry"] = geometry
    record["status"] = _record_status(geometry)
    record["geometry_gap"] = _record_gap(geometry)
    record["raw_geometry"] = {name: field["raw"]
                              for name, field in geometry.items()}
    return record


def validate_matrix(matrix):
    if not isinstance(matrix, Mapping) or not isinstance(matrix.get("rows"), list):
        raise ValueError("matrix.rows must be a list")
    for index, row in enumerate(matrix["rows"]):
        if not isinstance(row, Mapping) or not row.get("actor"):
            raise ValueError(f"matrix.rows[{index}] needs an actor")
        if "cameo_channels" in row and not isinstance(row["cameo_channels"], list):
            raise ValueError(f"matrix.rows[{index}].cameo_channels must be a list")
        if "references" in row and not isinstance(row["references"], list):
            raise ValueError(f"matrix.rows[{index}].references must be a list")
    return matrix


def build(matrix, *, provenance=None, matrix_path=None):
    """Build records without mutating the retained matrix."""
    validate_matrix(matrix)
    records = []
    current_armaments_without_warheads = collections.Counter()
    malformed_current_armaments = 0
    reference_without_selected_channels = collections.Counter()
    malformed_references = 0
    for row in matrix["rows"]:
        matrix_actor = row["actor"]
        current = row.get("cameo_channels") or []
        if not current:
            current_armaments_without_warheads[CURRENT_SOURCE] += 1
        for channel_index, armament in enumerate(current):
            if not isinstance(armament, Mapping):
                malformed_current_armaments += 1
                continue
            warheads = armament.get("warheads")
            if not isinstance(warheads, list) or not warheads:
                current_armaments_without_warheads[CURRENT_SOURCE] += 1
                continue
            for warhead_index, warhead in enumerate(warheads):
                if not isinstance(warhead, Mapping):
                    malformed_current_armaments += 1
                    continue
                record = _base_record(
                    source=CURRENT_SOURCE, matrix_actor=matrix_actor,
                    source_actor=matrix_actor, slot=armament.get("slot"),
                    weapon=armament.get("weapon"), warhead=warhead.get("tag"),
                    warhead_type=warhead.get("type"), channel_index=channel_index,
                    warhead_index=warhead_index,
                    metadata={"requires": armament.get("requires"),
                              "pricing": armament.get("pricing"),
                              "families": armament.get("families")},
                )
                records.append(_complete_record(
                    record, extract_geometry(warhead, CURRENT_SOURCE, current=True)))
        references = row.get("references") or []
        for reference_index, reference in enumerate(references):
            if not isinstance(reference, Mapping):
                malformed_references += 1
                continue
            source = reference.get("source") or "Unknown reference source"
            selected = reference.get("selected_weapon_channels")
            if not isinstance(selected, list) or not selected:
                reference_without_selected_channels[source] += 1
                continue
            for channel_index, channel in enumerate(selected):
                if not isinstance(channel, Mapping):
                    malformed_references += 1
                    continue
                record = _base_record(
                    source=source, matrix_actor=matrix_actor,
                    source_actor=channel.get("actor"), slot=channel.get("slot"),
                    weapon=channel.get("weapon"), warhead=channel.get("warhead"),
                    warhead_type=channel.get("warhead_type"),
                    channel_index=channel_index, reference_id=reference.get("id"),
                    channel_source=channel.get("source"),
                    metadata={"requires_condition": channel.get("requires_condition"),
                              "pause_on_condition": channel.get("pause_on_condition"),
                              "reference_index": reference_index},
                    inheritance_status=channel.get("inheritance_status"),
                )
                records.append(_complete_record(
                    record, extract_geometry(channel, source)))

    source_counts = collections.Counter(record["source"] for record in records)
    status_counts = collections.Counter(record["status"] for record in records)
    field_status_counts = collections.defaultdict(collections.Counter)
    coverage_by_source = collections.defaultdict(lambda: {
        "records": 0, "geometry_gap_records": 0,
        "warhead_types": collections.defaultdict(lambda: {
            "records": 0, "geometry_gap_records": 0,
            "field_status_counts": collections.defaultdict(collections.Counter),
        }),
    })
    for record in records:
        source = record["source"]
        warhead_type = record.get("warhead_type") or "UNKNOWN"
        source_summary = coverage_by_source[source]
        source_summary["records"] += 1
        source_summary["geometry_gap_records"] += int(record["geometry_gap"])
        type_summary = source_summary["warhead_types"][warhead_type]
        type_summary["records"] += 1
        type_summary["geometry_gap_records"] += int(record["geometry_gap"])
        for field_name, field in record["geometry"].items():
            field_status_counts[field_name][field["status"]] += 1
            type_summary["field_status_counts"][field_name][field["status"]] += 1

    def regularize(value):
        if isinstance(value, collections.Counter):
            return dict(sorted(value.items()))
        if isinstance(value, collections.defaultdict):
            return {key: regularize(item) for key, item in sorted(value.items())}
        if isinstance(value, dict):
            return {key: regularize(item) for key, item in sorted(value.items())}
        return value

    coverage = regularize(coverage_by_source)
    summary = {
        "actors": len(matrix["rows"]),
        "records": len(records),
        "source_counts": dict(sorted(source_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "field_status_counts": regularize(field_status_counts),
        "geometry_gap_records": sum(record["geometry_gap"] for record in records),
        "unresolved_geometry_records": sum(
            record["status"] in ("MALFORMED", "INHERITED_UNRESOLVED")
            for record in records),
        "coverage_by_source": coverage,
        "current_actors_or_armaments_without_warheads": dict(
            sorted(current_armaments_without_warheads.items())),
        "references_without_selected_channels": dict(
            sorted(reference_without_selected_channels.items())),
        "malformed_current_armaments": malformed_current_armaments,
        "malformed_references": malformed_references,
    }
    result = {
        "schema": 1,
        "scope": (
            "Review-only inventory of current Cameo and selected reference "
            "projectile/warhead geometry. Raw source strings are retained; "
            "no source units are compared, converted, or approved for YAML/runtime use."
        ),
        "method": [
            "Current Cameo records use cameo_channels[].warheads[]; selected reference records use only each reference's selected_weapon_channels.",
            "Spread/impact radius, Range declarations and Falloff arrays are parsed only when tokens are unambiguous finite nonnegative numbers; raw values and unparsed tokens remain alongside them.",
            "OpenRA Range c-cell tokens and DTA source-local range/projectilerange values are not normalized or compared across sources.",
            "Weapon projectile travel speed is outside this geometry inventory and remains separate from Range and projectile_range.",
            "Missing selected channels, absent optional fields, explicit empty values, malformed values and inherited/unresolved evidence remain distinct in records and coverage counts.",
        ],
        "source_geometry_semantics": SOURCE_GEOMETRY,
        "summary": summary,
        "records": records,
    }
    if provenance is not None:
        matrix_key = str(Path(matrix_path).resolve()) if matrix_path else None
        result.update({"matrix_path": matrix_key,
                       "matrix_sha256": provenance["files_sha256"].get(matrix_key),
                       "input_fingerprints_before": provenance})
    return result


def input_fingerprints(matrix_path):
    matrix_path = Path(matrix_path).resolve()
    paths = {
        "tools/balance/reference_weapon_geometry.py": ROOT / "tools/balance/reference_weapon_geometry.py",
        "tools/balance/diagnostic_output.py": ROOT / "tools/balance/diagnostic_output.py",
        str(matrix_path): matrix_path,
    }
    return {"files_sha256": {
        name: _sha256(path) for name, path in sorted(paths.items())}}


def build_from_path(matrix_path):
    matrix_path = Path(matrix_path).resolve()
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    before = input_fingerprints(matrix_path)
    result = build(matrix, provenance=before, matrix_path=matrix_path)
    after = input_fingerprints(matrix_path)
    if after != before:
        raise ValueError("matrix or geometry helper inputs changed during collection")
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


def _field_text(field):
    status = field.get("status", "—")
    values = field.get("values") or []
    text = status
    if values:
        text += " [" + ", ".join(_fmt(value) for value in values) + "]"
    unparsed = [token.get("raw") for token in field.get("tokens", [])
                if token.get("status") == "SOURCE_TOKEN_UNPARSED"]
    if unparsed:
        text += " raw-unparsed=" + ", ".join(str(value) for value in unparsed)
    return text.replace("|", "\\|").replace("\n", " ")


def _coverage_text(counts):
    return ", ".join(f"{key}:{value}" for key, value in sorted(counts.items())) or "—"


def render_markdown(result):
    summary = result.get("summary") or {}
    lines = [
        "# Reference weapon geometry review", "",
        "**Review-only and unapproved.** This report inventories source-local projectile/warhead geometry and makes no YAML, runtime or balance proposal.",
        "", "## Scope and caveats", "",
    ]
    lines.extend(f"- {item}" for item in result.get("method", []))
    lines += [
        "", "## Summary", "",
        f"- Actors: **{summary.get('actors', 0)}**; geometry records: **{summary.get('records', 0)}**; record statuses: `{summary.get('status_counts', {})}`.",
        f"- Records with at least one absent, malformed or inherited/unresolved field: **{summary.get('geometry_gap_records', 0)}**; unresolved geometry records: **{summary.get('unresolved_geometry_records', 0)}**.",
        f"- Current actors/armaments without retained warheads: `{summary.get('current_actors_or_armaments_without_warheads', {})}`.",
        f"- References without selected channels: `{summary.get('references_without_selected_channels', {})}`.",
        "", "## Coverage by source and warhead type", "",
        "| source | warhead type | records | spread status counts | range status counts | projectile range status counts | falloff status counts | geometry gaps |",
        "|---|---|---:|---|---|---|---|---:|",
    ]
    for source, source_info in sorted((summary.get("coverage_by_source") or {}).items()):
        for warhead_type, type_info in sorted((source_info.get("warhead_types") or {}).items()):
            fields = type_info.get("field_status_counts") or {}
            lines.append(
                "| {} | {} | {} | {} | {} | {} | {} | {} |".format(
                    str(source).replace("|", "\\|"), str(warhead_type).replace("|", "\\|"),
                    type_info.get("records", 0),
                    _coverage_text(fields.get("spread") or {}),
                    _coverage_text(fields.get("range") or {}),
                    _coverage_text(fields.get("projectile_range") or {}),
                    _coverage_text(fields.get("falloff") or {}),
                    type_info.get("geometry_gap_records", 0)))
    lines += [
        "", "## Geometry records", "",
        "The raw field values below are source-local. Numeric values in separate source rows are not comparable without an independently reviewed unit mapping.",
        "", "| source | actor | source actor | slot | weapon | warhead | type | status | spread | range | projectile range | falloff |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for record in result.get("records", []):
        geometry = record.get("geometry") or {}
        values = [
            record.get("source", "—"), record.get("actor", "—"),
            record.get("source_actor", "—"), record.get("slot", "—"),
            record.get("weapon", "—"), record.get("warhead", "—"),
            record.get("warhead_type", "—"), record.get("status", "—"),
            _field_text(geometry.get("spread", {})),
            _field_text(geometry.get("range", {})),
            _field_text(geometry.get("projectile_range", {})),
            _field_text(geometry.get("falloff", {})),
        ]
        lines.append("| " + " | ".join(str(value).replace("|", "\\|")
                                        for value in values) + " |")
    lines += [
        "", "Explicit zero and explicit empty values are preserved separately from absent fields. A `PRESENT_WITH_UNPARSED_TOKENS` range retains tokens such as OpenRA `0c64` verbatim and does not turn them into cross-source numbers.",
    ]
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
