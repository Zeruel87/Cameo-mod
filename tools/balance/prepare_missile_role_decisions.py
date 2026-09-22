#!/usr/bin/env python3
"""Prepare a review packet for unresolved missile role-family findings.

The raw role audit is intentionally narrow.  This companion packet groups its
R1--R4 rows by concrete weapon, makes the absolute MissileHE/Air lane visible,
and separates custom selectors and the V2 Tesla SCUD question from the
three-domain rule.  It is a read-only planning artifact: it does not choose a
family, alter target masks, or write YAML.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRIAGE = ROOT / "docs" / "audit" / "latest" / "missile_role_triage_20260911.json"
DEFAULT_JSON = ROOT / "docs" / "audit" / "latest" / "missile_role_decisions_20260911.json"
DEFAULT_MD = ROOT / "docs" / "audit" / "latest" / "missile_role_decisions_20260911.md"


LANE_TEXT = {
    "DUAL_DOMAIN_ABSOLUTE_RULE": (
        "Both-domain route; MissileHE-against-Air also violates the explicit "
        "never rule. Review the complete consumer closure before choosing AP."
    ),
    "DUAL_DOMAIN_ROLE_REVIEW": (
        "Both-domain route with HE/AA family mismatch. A role choice changes "
        "armor and delivery behavior for every consumer."
    ),
    "SINGLE_DOMAIN_ROLE_REVIEW": (
        "Literal ground-only or air-only route, but a family correction still "
        "changes armor response and projectile delivery."
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(value: str | None, root: Path = ROOT) -> str:
    if not value:
        return ""
    path = Path(value)
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(value).replace("\\", "/")


def _unique_strict_rows(triage: dict[str, Any]) -> list[dict[str, Any]]:
    """Merge R3/R4 duplicate evidence into one row per concrete weapon."""

    grouped: dict[str, dict[str, Any]] = {}
    for code in ("R1", "R2", "R3", "R4"):
        for source in triage.get("strict_findings", {}).get(code, []):
            name = source["weapon"]
            target = grouped.setdefault(
                name,
                {
                    "weapon": name,
                    "codes": [],
                    "role": source.get("role"),
                    "flies": source.get("flies"),
                    "expected": source.get("expected"),
                    "valid_targets": source.get("valid_targets", ""),
                    "invalid_targets": source.get("invalid_targets", ""),
                    "actor_consumers": source.get("actor_consumers", []),
                    "inheritance_chain": source.get("inheritance_chain", []),
                    "family_sources": source.get("family_sources", []),
                    "weapon_source": source.get("weapon_source"),
                },
            )
            if code not in target["codes"]:
                target["codes"].append(code)
    rows: list[dict[str, Any]] = []
    for row in grouped.values():
        row["codes"] = sorted(row["codes"], key=("R1", "R2", "R3", "R4").index)
        if "R4" in row["codes"]:
            lane = "DUAL_DOMAIN_ABSOLUTE_RULE"
            priority = "critical"
        elif "R3" in row["codes"]:
            lane = "DUAL_DOMAIN_ROLE_REVIEW"
            priority = "high"
        else:
            lane = "SINGLE_DOMAIN_ROLE_REVIEW"
            priority = "high" if len(row["actor_consumers"]) > 1 else "normal"
        row["lane"] = lane
        row["priority"] = priority
        row["consumer_count"] = len(row["actor_consumers"])
        row["consumer_routes"] = [
            {
                "actor": item.get("actor"),
                "route": item.get("route"),
                "source": {
                    "file": _relative(item.get("source", {}).get("file")),
                    "line": item.get("source", {}).get("line"),
                },
            }
            for item in row["actor_consumers"]
        ]
        row["family_sources"] = [
            {
                **item,
                "file": _relative(item.get("file")),
            }
            for item in row["family_sources"]
        ]
        row["weapon_source"] = {
            **(row["weapon_source"] or {}),
            "file": _relative((row["weapon_source"] or {}).get("file")),
        }
        row["review_action"] = (
            "Maintainer role decision; compare every consumer's target route, "
            "armor response and delivery geometry before any edit."
        )
        rows.append(row)
    return sorted(rows, key=lambda row: (row["priority"] != "critical", row["weapon"]))


def build_packet(triage: dict[str, Any], triage_path: Path = DEFAULT_TRIAGE) -> dict[str, Any]:
    rows = _unique_strict_rows(triage)
    lanes = collections.Counter(row["lane"] for row in rows)
    priorities = collections.Counter(row["priority"] for row in rows)
    custom = triage.get("custom_selectors", [])
    custom_buckets = collections.Counter(row.get("bucket", "unknown") for row in custom)
    custom_summary = [
        {
            "bucket": bucket,
            "count": count,
            "consumer_routes": sum(
                len(row.get("actor_consumers", []))
                for row in custom
                if row.get("bucket", "unknown") == bucket
            ),
        }
        for bucket, count in sorted(custom_buckets.items())
    ]
    questions = [
        {
            "subject": row.get("subject"),
            "weapon": row.get("weapon"),
            "valid_targets": row.get("valid_targets"),
            "invalid_targets": row.get("invalid_targets", ""),
            "consumer_count": len(row.get("actor_consumers", [])),
            "review_status": row.get("review_status"),
        }
        for row in triage.get("policy_questions", [])
    ]
    return {
        "summary": {
            "unique_strict_weapon_count": len(rows),
            "raw_strict_row_count": sum(
                len(triage.get("strict_findings", {}).get(code, []))
                for code in ("R1", "R2", "R3", "R4")
            ),
            "lane_counts": dict(sorted(lanes.items())),
            "priority_counts": dict(sorted(priorities.items())),
            "custom_selector_count": len(custom),
            "custom_bucket_counts": dict(sorted(custom_buckets.items())),
            "policy_question_count": len(questions),
        },
        "strict_cases": rows,
        "custom_selector_summary": custom_summary,
        "policy_questions": questions,
        "decision_order": [
            "Clear the dual-domain MissileHE/Air absolute-rule rows first.",
            "Review dual-domain and multi-consumer closures as complete weapon/actor groups.",
            "Review single-domain rows only after confirming the intended armor and delivery change.",
            "Handle custom selectors and the V2 Tesla SCUD parent as separate recipient/runtime policy lanes.",
        ],
        "guardrails": [
            "This packet is review-only; it selects no canonical family.",
            "Do not infer combat activation from a Weapon consumer route alone.",
            "Do not change ValidTargets, InvalidTargets, damage, projectile, or Versus values from this receipt.",
            "Existing design holds and preserve candidates remain maintainer decisions; this packet does not override them.",
        ],
        "source": {
            "triage_receipt": str(triage_path).replace("\\", "/"),
            "triage_sha256": _sha256(triage_path) if triage_path.exists() else None,
            "status": "REVIEW_ONLY",
        },
    }


def _md_source(source: dict[str, Any] | None) -> str:
    if not source or not source.get("file"):
        return ""
    return f"`{source['file']}:{source.get('line', '')}`"


def render_markdown(packet: dict[str, Any]) -> str:
    summary = packet["summary"]
    out = [
        "# Missile role decision packet",
        "",
        "**Review-only.** This packet groups the raw role audit by concrete weapon",
        "and makes the next decision lane explicit. It does not select a family,",
        "change a target mask, or authorize YAML/runtime work.",
        "",
        "## Summary",
        "",
        f"- Unique strict weapons: **{summary['unique_strict_weapon_count']}** (raw R1-R4 rows: **{summary['raw_strict_row_count']}**; R3/R4 duplicates are merged).",
        f"- Custom selectors: **{summary['custom_selector_count']}**; explicit policy questions: **{summary['policy_question_count']}**.",
        "",
        "| decision lane | count | meaning |",
        "|---|---:|---|",
    ]
    for lane in ("DUAL_DOMAIN_ABSOLUTE_RULE", "DUAL_DOMAIN_ROLE_REVIEW", "SINGLE_DOMAIN_ROLE_REVIEW"):
        out.append(f"| {lane} | {summary['lane_counts'].get(lane, 0)} | {LANE_TEXT[lane]} |")
    out += ["", "## Strict cases", "", "| priority | weapon | audit codes | role | family | expected | consumers | source |", "|---|---|---|---|---|---|---:|---|"]
    for row in packet["strict_cases"]:
        out.append(
            f"| {row['priority']} | `{row['weapon']}` | {', '.join(row['codes'])} | {row['role']} | {row['flies']} | {row['expected']} | {row['consumer_count']} | {_md_source(row['weapon_source'])} |"
        )
    if not packet["strict_cases"]:
        out.append("| _none_ |  |  |  |  |  | 0 |  |")
    out += ["", "Every row retains inheritance, field provenance and consumer route details in the JSON receipt. A consumer count of zero means no resolved actor `Weapon:` route was found; it is not proof that the definition is unreachable.", ""]
    out += ["## Decision order", ""]
    out.extend(f"{index}. {value}" for index, value in enumerate(packet["decision_order"], start=1))
    out += ["", "## Custom selector lanes", "", "| bucket | selectors | consumer routes |", "|---|---:|---:|"]
    for row in packet["custom_selector_summary"]:
        out.append(f"| {row['bucket']} | {row['count']} | {row['consumer_routes']} |")
    if not packet["custom_selector_summary"]:
        out.append("| _none_ | 0 | 0 |")
    out += ["", "Custom recipient vocabularies, naval selectors and invalid-tag combinations need recipient/runtime evidence; they do not enter the three-domain conversion rule automatically.", ""]
    out += ["## Explicit policy questions", "", "| subject | weapon | selector | consumers | status |", "|---|---|---|---:|---|"]
    for row in packet["policy_questions"]:
        selector = row["valid_targets"] or ""
        if row["invalid_targets"]:
            selector += f" / invalid {row['invalid_targets']}"
        out.append(f"| {row['subject']} | `{row['weapon']}` | `{selector}` | {row['consumer_count']} | {row['review_status']} |")
    if not packet["policy_questions"]:
        out.append("| _none_ |  |  | 0 |  |")
    out += ["", "## Guardrails", ""]
    out.extend(f"- {value}" for value in packet["guardrails"])
    triage_receipt = packet.get("source", {}).get("triage_receipt", "")
    out += ["", f"Source receipt: `{triage_receipt}`.", ""]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--triage", type=Path, default=DEFAULT_TRIAGE)
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)
    triage_path = args.triage.resolve()
    triage = json.loads(triage_path.read_text(encoding="utf-8"))
    packet = build_packet(triage, triage_path)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(render_markdown(packet) + "\n", encoding="utf-8")
    print(json.dumps(packet["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
