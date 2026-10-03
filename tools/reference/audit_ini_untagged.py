#!/usr/bin/env python3
"""audit_ini_untagged.py — classify untagged rows in the INI corpus.

DAWN's buildability fix means most untagged rows are now honest
neutral/campaign/decorative/no-production-claim actors. This script
produces a per-source breakdown so the fleet can see whether any
still-buildable untagged rows remain and where the next extraction fix
should go.

Run:
    python tools/reference/audit_ini_untagged.py
"""

import json
import pathlib
import sys
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CORPUS = pathlib.Path(__file__).parent.parent.parent / "docs" / "reference" / "ini_corpus.json"
BUCKETS = (
    "buildable_untagged", "zero_cost", "tech11_low_cost", "cost_tech11",
    "cost_disabled", "cost_other", "prerequisite_no_owner", "no_production_claim",
)


def classify(row: dict) -> str:
    if row.get("buildable"):
        return "buildable_untagged"
    if row.get("cost") is not None:
        cost = row.get("cost")
        tech = row.get("tech_level")
        if cost == 0:
            return "zero_cost"
        if tech == 11 and cost is not None and cost <= 100:
            return "tech11_low_cost"
        if tech == 11:
            return "cost_tech11"
        if tech is not None and tech < 0:
            return "cost_disabled"
        return "cost_other"
    if row.get("prerequisite"):
        return "prerequisite_no_owner"
    return "no_production_claim"


def summarize_untagged(rows: list[dict]):
    by_source = defaultdict(list)
    for row in rows:
        if not row.get("owners"):
            by_source[row["source"]].append(row)
    summary = {}
    for source, source_rows in sorted(by_source.items()):
        buckets = defaultdict(list)
        for row in source_rows:
            buckets[classify(row)].append(row)
        counted = sum(len(buckets.get(bucket, ())) for bucket in BUCKETS)
        if counted != len(source_rows):
            raise AssertionError(
                f"{source}: bucket total {counted} != untagged total {len(source_rows)}")
        summary[source] = buckets
    return by_source, summary


def main() -> int:
    if not CORPUS.exists():
        print(f"missing {CORPUS}", file=sys.stderr)
        return 1

    rows = []
    with CORPUS.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    by_source, summary = summarize_untagged(rows)

    print("# INI corpus untagged breakdown\n")
    headers = ["source", "total", *BUCKETS]
    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join(["---"] * len(headers)) + "|")
    for s, rs in sorted(by_source.items()):
        buckets = summary[s]
        cells = [s, str(len(rs))]
        for h in headers[2:]:
            cells.append(str(len(buckets.get(h, []))))
        print("| " + " | ".join(cells) + " |")

    print("\n## Buildable but untagged (actionable)\n")
    any_actionable = any(buckets.get("buildable_untagged") for buckets in summary.values())
    if any_actionable:
        for s, buckets in sorted(summary.items()):
            actionable = buckets.get("buildable_untagged")
            if not actionable:
                continue
            print(f"### {s} ({len(actionable)})\n")
            for r in actionable:
                print(f"- `{r['id']}` | {r.get('name', '')} | type={r.get('type')} | "
                      f"cost={r.get('cost')} | tech={r.get('tech_level')} | "
                      f"prereq={r.get('prerequisite')}")
            print()
    else:
        print("No rows are currently marked buildable without owners.\n")

    print("\n## Costed but not buildable — data-driven subcategories\n")
    print("Labels state observed fields only. Zero cost does not imply civilian identity, and "
          "TechLevel 11 with low cost does not imply hero identity.\n")
    for s, buckets in sorted(summary.items()):
        for cat in ["zero_cost", "tech11_low_cost", "cost_tech11", "cost_disabled", "cost_other"]:
            rows = buckets.get(cat, [])
            if not rows:
                continue
            print(f"### {s} — {cat} ({len(rows)})\n")
            for r in rows[:10]:
                print(f"- `{r['id']}` | {r.get('name', '')} | type={r.get('type')} | "
                      f"cost={r.get('cost')} | tech={r.get('tech_level')} | "
                      f"prereq={r.get('prerequisite')}")
            if len(rows) > 10:
                print(f"- ... and {len(rows) - 10} more")
            print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
