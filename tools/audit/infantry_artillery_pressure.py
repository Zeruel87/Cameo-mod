#!/usr/bin/env python3
"""Build a review-only infantry-versus-area-weapon pressure receipt.

The receipt uses explicit current-Cameo record indices and ledger actor HP to
show a single center-impact projection for a few base infantry targets. It is
not a combat simulation: target movement, armor mitigation, falloff, scatter,
cadence, area population and secondary payloads remain outside the calculation.
No YAML or balance value is written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATION_ROOT = Path(
    "C:/Users/Blackrobe/Documents/agents/cameo-reference-sources-20260909/validation"
)
DEFAULT_CAMEO = VALIDATION_ROOT / (
    "cameo-channel-curves-20260911/cameo_channel_curves_passengers.json"
)
DEFAULT_MANIFEST = ROOT / (
    "docs/balance/infantry_artillery_pressure_manifest_20260911.json"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _actor_from_ledger(path: Path, actor: str):
    document = json.loads(path.read_text(encoding="utf-8"))
    sections = document.get("sections") if isinstance(document, Mapping) else None
    if not isinstance(sections, Mapping):
        raise ValueError(f"{path}: sections must be an object")
    for section, actors in sections.items():
        if isinstance(actors, Mapping) and actor in actors:
            row = actors[actor]
            if not isinstance(row, Mapping):
                raise ValueError(f"{path}: actor {actor} is not an object")
            return document, section, row
    raise ValueError(f"{path}: actor not found: {actor}")


def _value(row: Mapping, field: str):
    value = row.get(field)
    return value.get("v") if isinstance(value, Mapping) else value


def _record(records, index, label):
    if isinstance(index, bool) or not isinstance(index, int):
        raise ValueError(f"{label}: record_index must be an integer")
    if index < 0 or index >= len(records):
        raise ValueError(f"{label}: record_index out of range: {index}")
    row = records[index]
    if not isinstance(row, Mapping):
        raise ValueError(f"{label}: selected record is not an object")
    return row


def _guard(record: Mapping, expected: Mapping, label: str):
    reasons = []
    for field, value in expected.items():
        actual = record.get(field)
        if actual != value:
            reasons.append(
                f"{label}:expected_{field}={value!r}:actual={actual!r}"
            )
    if record.get("status") != "RESOLVED":
        reasons.append(f"{label}:status_not_resolved:{record.get('status')!r}")
    return reasons


def _projection(terms: Mapping, hp: float, axis: str):
    term = terms.get(axis)
    if not isinstance(term, Mapping):
        return None, f"axis_missing:{axis}"
    flat = _finite(term.get("A", term.get("flat")))
    fraction = _finite(term.get("B", term.get("max_hp_fraction")))
    if flat is None or fraction is None or flat < 0 or fraction < 0:
        return None, f"axis_invalid:{axis}"
    percentage = fraction * hp
    total = flat + percentage
    return {
        "axis": axis,
        "flat_A": flat,
        "max_hp_fraction_B": fraction,
        "percentage_at_target_hp": percentage,
        "uncapped_total": total,
        "target_hp_bars": total / hp if hp else None,
        "capped_damage": min(total, hp) if hp else None,
        "capped_target_fraction": min(total, hp) / hp if hp else None,
    }, None


def build_report(manifest: Mapping, cameo_document: Mapping, *, input_paths=None):
    if not isinstance(manifest, Mapping):
        raise ValueError("manifest must be an object")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("manifest.cases must be a nonempty list")
    records = cameo_document.get("records")
    if not isinstance(records, list):
        raise ValueError("Cameo document records must be a list")

    rows = []
    for case in cases:
        if not isinstance(case, Mapping):
            rows.append({"status": "UNRESOLVED", "reasons": ["case_not_object"]})
            continue
        reasons = []
        target_label = f"{case.get('id', 'case')}:target"
        weapon_label = f"{case.get('id', 'case')}:weapon"
        try:
            target_record = _record(records, case.get("target_record_index"), target_label)
            weapon_record = _record(records, case.get("weapon_record_index"), weapon_label)
            expected = case.get("expected") or {}
            if not isinstance(expected, Mapping):
                reasons.append(f"{case.get('id', 'case')}:expected_not_object")
            else:
                reasons.extend(_guard(
                    target_record,
                    {
                        "actor": case.get("target_actor"),
                        "scenario": expected.get("target_scenario"),
                        "weapon": expected.get("target_weapon"),
                    },
                    target_label,
                ))
                reasons.extend(_guard(
                    weapon_record,
                    {
                        "actor": case.get("weapon_actor"),
                        "scenario": expected.get("weapon_scenario"),
                        "weapon": expected.get("weapon"),
                    },
                    weapon_label,
                ))
            ledger_path = (ROOT / str(case.get("target_ledger"))).resolve()
            _, target_section, target_ledger = _actor_from_ledger(
                ledger_path, case.get("target_actor")
            )
            weapon_ledger_path = (ROOT / str(case.get("weapon_ledger"))).resolve()
            _, weapon_section, weapon_ledger = _actor_from_ledger(
                weapon_ledger_path, case.get("weapon_actor")
            )
            hp = _finite(_value(target_ledger, "hp"))
            if hp is None or hp <= 0:
                reasons.append(f"{case.get('id', 'case')}:target_hp_invalid")
            terms = weapon_record.get("terms")
            if not isinstance(terms, Mapping):
                reasons.append(f"{weapon_label}:terms_missing")
            armaments = weapon_ledger.get("armaments")
            ledger_weapons = {
                item.get("weapon") for item in armaments
                if isinstance(item, Mapping) and item.get("weapon")
            } if isinstance(armaments, list) else set()
            if weapon_record.get("weapon") not in ledger_weapons:
                reasons.append(
                    f"{weapon_label}:ledger_weapon_missing:{weapon_record.get('weapon')!r}"
                )
            projections = {}
            if not reasons:
                for axis in ("None", "Light"):
                    projection, reason = _projection(terms, hp, axis)
                    if reason:
                        reasons.append(f"{weapon_label}:{reason}")
                    else:
                        projections[axis] = projection
            rows.append({
                "id": case.get("id"),
                "faction": case.get("faction"),
                "status": "RESOLVED" if not reasons else "UNRESOLVED",
                "reasons": sorted(set(reasons)),
                "target": {
                    "actor": case.get("target_actor"),
                    "ledger": case.get("target_ledger"),
                    "ledger_section": target_section,
                    "record_index": case.get("target_record_index"),
                    "weapon": target_record.get("weapon"),
                    "scenario": target_record.get("scenario"),
                    "hp": hp,
                    "armor": _value(target_ledger, "armor"),
                    "cost": _value(target_ledger, "cost"),
                },
                "weapon": {
                    "actor": case.get("weapon_actor"),
                    "ledger": case.get("weapon_ledger"),
                    "record_index": case.get("weapon_record_index"),
                    "ledger_section": weapon_section,
                    "weapon": weapon_record.get("weapon"),
                    "scenario": weapon_record.get("scenario"),
                    "status": weapon_record.get("status"),
                    "requires": weapon_record.get("requires"),
                    "armor": _value(weapon_ledger, "armor"),
                    "cost": _value(weapon_ledger, "cost"),
                    "selection": weapon_record.get("selection"),
                    "projections": projections,
                },
            })
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
            rows.append({
                "id": case.get("id"),
                "faction": case.get("faction"),
                "status": "UNRESOLVED",
                "reasons": [str(error)],
            })

    resolved = sum(row.get("status") == "RESOLVED" for row in rows)
    return {
        "schema": 1,
        "status": "RESOLVED" if resolved == len(rows) else "UNRESOLVED",
        "scope": manifest.get("scope"),
        "method": [
            "Every target and weapon record is selected by an explicit dataset index from the manifest.",
            "Target HP comes from the named current ledger actor; no actor or weapon join is inferred.",
            "The projection is A + B times target HP on the current record's None and Light axes.",
            "Capped damage and target-HP bars are arithmetic diagnostics; they are not a combat or cadence model.",
        ],
        "assumptions": {
            "impact": "one center impact with the selected record's resolved terms",
            "falloff": "100% center value; no scatter or edge distance",
            "armor": "the selected target scenario terms are used as supplied; no additional mitigation is applied",
            "cadence": "excluded; no reload, burst, accuracy or area-population claim",
            "secondary_payloads": "excluded; only the selected record's A/B terms are projected",
            "writeback": False,
        },
        "inputs": input_paths or {},
        "summary": {
            "cases": len(rows),
            "resolved": resolved,
            "unresolved": len(rows) - resolved,
            "axes": ["None", "Light"],
        },
        "rows": rows,
    }


def _fmt(value):
    if value is None:
        return "—"
    return f"{float(value):,.0f}"


def render_markdown(report: Mapping):
    summary = report.get("summary") or {}
    lines = [
        "# Infantry versus artillery pressure receipt",
        "",
        "**STATIC SCENARIO ONLY.** Each row is one explicit current-Cameo "
        "center-impact projection against a base infantry target. It is not a "
        "live TTK, DPS vote, balance recommendation or gameplay result.",
        "",
        "## Summary",
        "",
        f"- Cases: **{summary.get('cases', 0)}**; resolved: **{summary.get('resolved', 0)}**; unresolved: **{summary.get('unresolved', 0)}**.",
        "- Projection: flat A plus max-HP fraction B at the target's ledger HP, shown for source axes None and Light.",
        "- Center impact assumes 100% selected-record terms; falloff, scatter, cadence, armor changes, target movement and secondary payloads are excluded.",
        "",
        "| faction | area weapon | infantry target | target HP | None total | None HP bars | Light total | Light HP bars |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in report.get("rows", []):
        target = row.get("target") or {}
        weapon = row.get("weapon") or {}
        projections = weapon.get("projections") or {}
        none = projections.get("None") or {}
        light = projections.get("Light") or {}
        reasons = "; ".join(row.get("reasons") or []) or "—"
        if row.get("status") != "RESOLVED":
            lines.append(
                f"| {row.get('faction', '—')} | {weapon.get('weapon', '—')} | {target.get('actor', '—')} | {_fmt(target.get('hp'))} | UNRESOLVED | — | — | {reasons} |"
            )
            continue
        lines.append(
            f"| {row.get('faction', '—')} | `{weapon.get('weapon', '—')}` | `{target.get('actor', '—')}` | {_fmt(target.get('hp'))} | {_fmt(none.get('uncapped_total'))} | {none.get('target_hp_bars', 0):.2f}× | {_fmt(light.get('uncapped_total'))} | {light.get('target_hp_bars', 0):.2f}× |"
        )
    lines += [
        "",
        "## Interpretation boundary",
        "",
        "A result above 1.00 target-HP bars means the selected arithmetic projection exceeds the target HP before capping. It does not prove a one-shot kill: impact position, armor routing, target eligibility, projectile timing, reload cadence, overlapping units and secondary effects are outside this receipt.",
        "",
        "The receipt is evidence for a later infantry-survivability pilot. Possible cover, armor-layer, regeneration or piercing policies must be evaluated separately and approved before any gameplay change.",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--cameo", type=Path, default=DEFAULT_CAMEO)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest_path = args.manifest.resolve()
    cameo_path = args.cameo.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cameo_document = json.loads(cameo_path.read_text(encoding="utf-8"))
    report = build_report(
        manifest,
        cameo_document,
        input_paths={
            "manifest": {"path": str(manifest_path), "sha256": _sha256(manifest_path)},
            "cameo": {"path": str(cameo_path), "sha256": _sha256(cameo_path), "records": len(cameo_document.get("records", []))},
        },
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True))
    return 0 if report["status"] == "RESOLVED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
