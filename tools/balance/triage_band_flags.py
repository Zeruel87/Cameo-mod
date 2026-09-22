#!/usr/bin/env python3
"""Classify baseband flags for review without changing any balance input.

The source ``band-scope`` report already contains the class formula result.
This helper adds a deterministic review lane and preserves the raw row.  It
never reprices a unit, moves an anchor, or treats a band flag as regression or
permission to write YAML.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from collections import Counter, defaultdict
from collections.abc import Mapping
from pathlib import Path

import diagnostic_output

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "docs/balance/band-scope-20260911.json"
SOFT_FLOOR = 0.75
HARD_FLOOR = 0.50
HARD_CEILING = 3.50


def _finite(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _input_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _limitation_blockers(row):
    blockers = []
    if row.get("class_source") != "explicit":
        blockers.append("DERIVED_CLASS_MEMBERSHIP")
    if row.get("active_source_limitations"):
        blockers.append("ACTIVE_SOURCE_LIMITATION")
    if row.get("inactive_variant_limitations"):
        blockers.append("INACTIVE_VARIANT_LIMITATION")
    if not row.get("signed_off"):
        blockers.append("CLASS_ANCHOR_NOT_SIGNED_OFF")
    return blockers


def classify_row(row):
    """Return review-only classification while retaining no derived price."""
    if not isinstance(row, Mapping):
        return {
            "actor": None,
            "status": "UNRESOLVED",
            "review_lane": "INPUT_SHAPE",
            "decision": "HOLD",
            "reasons": ["row_not_object"],
        }
    ratio = _finite(row.get("ratio"))
    if ratio is None:
        band = "UNRESOLVED_RATIO"
        lane = "INPUT_SHAPE"
        reasons = ["ratio_missing_or_nonfinite"]
    elif ratio < HARD_FLOOR:
        band = "HARD_LOW"
        lane = "ANCHOR_OR_INPUT"
        reasons = ["below_hard_floor"]
    elif ratio < SOFT_FLOOR:
        band = "SOFT_LOW"
        lane = "ANCHOR_OR_INPUT"
        reasons = ["below_soft_floor"]
    elif ratio > HARD_CEILING:
        band = "HARD_HIGH"
        lane = "ANCHOR_OR_INPUT"
        reasons = ["above_hard_ceiling"]
    else:
        band = "IN_BAND"
        lane = "NONE"
        reasons = []

    blockers = _limitation_blockers(row)
    if "DERIVED_CLASS_MEMBERSHIP" in blockers:
        lane = "CLASS_MEMBERSHIP"
    elif "ACTIVE_SOURCE_LIMITATION" in blockers:
        lane = "SOURCE_MODEL"
    elif "INACTIVE_VARIANT_LIMITATION" in blockers and lane == "NONE":
        lane = "VARIANT_SCOPE"
    if blockers:
        reasons.extend(blockers)
    return {
        "actor": copy.deepcopy(row.get("actor")),
        "class": copy.deepcopy(row.get("class")),
        "status": "UNRESOLVED" if ratio is None else "REVIEW_REQUIRED",
        "ratio": ratio,
        "band": band,
        "review_lane": lane,
        "decision": "HOLD",
        "reasons": sorted(set(reasons)),
        "source_ledger": copy.deepcopy(row.get("source_ledger")),
        "class_source": copy.deepcopy(row.get("class_source")),
        "signed_off": bool(row.get("signed_off")),
        "band_exempt": bool(row.get("band_exempt")),
        "actual_cost": copy.deepcopy(row.get("actual_cost")),
        "modeled_price": copy.deepcopy(row.get("modeled_price")),
        "comparison_domain": copy.deepcopy(row.get("comparison_domain")),
        "active_source_limitations": copy.deepcopy(row.get("active_source_limitations") or []),
        "inactive_variant_limitations": copy.deepcopy(row.get("inactive_variant_limitations") or []),
        "raw_row": copy.deepcopy(row),
    }


def build_report(document, *, input_path=None, input_sha256=None):
    if not isinstance(document, Mapping):
        raise ValueError("band report must be an object")
    rows = document.get("rows")
    if not isinstance(rows, list):
        raise ValueError("band report rows must be a list")
    flagged = [row for row in rows if isinstance(row, Mapping) and row.get("flagged")]
    triage = [classify_row(row) for row in flagged]
    band_counts = Counter(row.get("band") for row in triage)
    lane_counts = Counter(row.get("review_lane") for row in triage)
    class_rows = defaultdict(list)
    for row in triage:
        class_rows[row.get("class")].append(row)
    class_summary = []
    for cls in sorted(class_rows, key=lambda value: "" if value is None else str(value)):
        members = class_rows[cls]
        class_summary.append({
            "class": cls,
            "flagged": len(members),
            "bands": dict(sorted(Counter(row.get("band") for row in members).items())),
            "review_lanes": dict(sorted(Counter(row.get("review_lane") for row in members).items())),
            "actors": [row.get("actor") for row in members],
        })
    return {
        "schema": 1,
        "status": "REVIEW_REQUIRED" if triage else "NO_FLAGS",
        "scope": "Review-only classification of the existing baseband report; no repricing, anchor change or YAML writeback.",
        "policy": {
            "hard_floor": HARD_FLOOR,
            "soft_floor": SOFT_FLOOR,
            "hard_ceiling": HARD_CEILING,
            "decision": "HOLD",
            "meaning": "Class and source review must precede any price or anchor action; flags are not regression proof.",
        },
        "input": {
            "path": str(input_path) if input_path is not None else None,
            "sha256": input_sha256,
            "source_summary": copy.deepcopy(document.get("summary")),
        },
        "summary": {
            "input_rows": len(rows),
            "flagged_rows": len(triage),
            "band_counts": dict(sorted(band_counts.items())),
            "review_lane_counts": dict(sorted(lane_counts.items())),
            "classes": len(class_summary),
        },
        "class_summary": class_summary,
        "rows": triage,
    }


def render_markdown(report):
    summary = report.get("summary") or {}
    policy = report.get("policy") or {}
    lines = [
        "# Baseband flag triage",
        "",
        "**REVIEW REQUIRED; diagnostic only.** Every listed action is HOLD. "
        "A flag does not prove a gameplay regression and does not authorize "
        "repricing, anchor movement or YAML writeback.",
        "",
        "## Policy",
        "",
        f"- Hard floor: **{policy.get('hard_floor', HARD_FLOOR):.0%}**; soft floor: **{policy.get('soft_floor', SOFT_FLOOR):.0%}**; hard ceiling: **{policy.get('hard_ceiling', HARD_CEILING):.0%}**.",
        f"- Input rows: **{summary.get('input_rows', 0)}**; flagged rows: **{summary.get('flagged_rows', 0)}**; classes: **{summary.get('classes', 0)}**.",
        f"- Band counts: `{summary.get('band_counts', {})}`; review lanes: `{summary.get('review_lane_counts', {})}`.",
        "- Derived class membership, source limitations, inactive variants and unsigned anchors stay visible as blockers.",
        "",
        "## Flagged rows",
        "",
        "| actor | class | ratio | band | lane | blockers |",
        "|---|---|---:|---|---|---|",
    ]
    for row in report.get("rows", []):
        ratio = row.get("ratio")
        ratio_text = "—" if ratio is None else f"{ratio:.3f}x"
        blockers = "; ".join(row.get("reasons") or []) or "—"
        lines.append(
            f"| `{row.get('actor', '—')}` | `{row.get('class', '—')}` | {ratio_text} | {row.get('band', '—')} | {row.get('review_lane', '—')} | {blockers.replace('|', r'\\|')} |"
        )
    lines += [
        "",
        "No row is a calibration or anchor recommendation. Resolve class membership, source coverage and role validity before reconsidering any flag.",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)
    try:
        input_path = args.input.resolve()
        if not input_path.is_file():
            raise ValueError("band report does not exist: " + str(input_path))
        out_path = diagnostic_output.validate_path(ROOT, args.out)
        markdown_path = (diagnostic_output.validate_path(ROOT, args.markdown)
                         if args.markdown else None)
        if markdown_path is not None and markdown_path == out_path:
            raise ValueError("JSON and Markdown outputs must use different resolved paths")
        document = json.loads(input_path.read_text(encoding="utf-8"))
        report = build_report(document, input_path=input_path,
                              input_sha256=_input_sha256(input_path))
        outputs = {out_path: json.dumps(report, indent=2, sort_keys=True) + "\n"}
        if markdown_path is not None:
            outputs[markdown_path] = render_markdown(report)
        diagnostic_output.write_outputs(ROOT, outputs)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
