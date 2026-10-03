#!/usr/bin/env python3
"""Carry the reviewed Combined Arms family assignments onto the other sources.

Combined Arms' 118 groups were assigned to families by hand and reviewed by the maintainer. The
other sixteen compressible sources carry ~1,080 groups between them, and pre-filling those the
same way would be a wall of guesses nobody could usefully review.

⭐ But the review already taught the pipeline something reusable. Every group is keyed by the same
measured triple — DELIVERY x ELEMENT x BAND — and CA's review fixed which family each triple maps
to. A `Laser` / `Plain` / `vehicle` group in Mental Omega is the same KIND of thing as one in
Combined Arms, so it inherits the family CA's review gave that triple. What cannot inherit is
flagged, and that is the only part a human needs to look at.

⚠ THIS PROPOSES, IT DOES NOT DECIDE. Every row it produces is `status: proposed`. The triple is a
coarse key: it says a weapon is a vehicle-mounted plain laser, not whether it is the Obelisk or a
laser turret. Where CA's own review split one triple across several families (it does, 26 times),
the propagation reports the split rather than silently picking the biggest — those are exactly the
groups whose shape has to be read.

    python tools/reference/propagate_families.py            # report
    python tools/reference/propagate_families.py --write    # write the proposal file
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference"))

DOC = ROOT / "docs" / "reference" / "warhead_family_assignment.yaml"
GROUPS = ROOT / "docs" / "reference" / "warhead_groups.json"
OUT = ROOT / "docs" / "reference" / "warhead_family_proposals.json"

# Sources that are not compressed into groups, and why. See REFERENCE_EXTRACTION_PLAN R37/R38.
NOT_COMPRESSED = {
    "cameo": "no compression needed — a ^Warhead_<Family>_<Level> template IS its family (R37)",
    "d2k_mod": "a transcribed table with no actors; it votes on the armour ladder only",
}


def ca_precedent() -> tuple[dict, dict]:
    """{(delivery, element, band): {family: weapons}} from the REVIEWED Combined Arms rows."""
    import yaml
    doc = yaml.safe_load(DOC.read_text(encoding="utf-8"))
    overrides = doc.get("overrides") or {}
    by_triple: dict[tuple, collections.Counter] = collections.defaultdict(collections.Counter)
    for row in doc["groups"].values():
        triple = (row["delivery"], row["element"], row["band"])
        for weapon in row["weapons"]:
            entry = overrides.get(weapon)
            family = entry["family"] if entry else row["family"]
            by_triple[triple][family] += 1
    return by_triple, doc


def propagate() -> dict:
    by_triple, doc = ca_precedent()
    groups = json.load(GROUPS.open(encoding="utf-8"))
    source_of_truth = doc["source"]

    out: dict[str, dict] = {}
    for sid, entry in sorted(groups.items()):
        if sid == source_of_truth or sid in NOT_COMPRESSED:
            continue
        rows, stats = [], collections.Counter()
        for group in entry["groups"]:
            triple = (group["delivery"], group["element"], group["band"])
            seen = by_triple.get(triple)
            if not seen:
                # No CA group shares this triple. Fall back to delivery+element, then delivery.
                for key_len in (2, 1):
                    merged: collections.Counter = collections.Counter()
                    for known, families in by_triple.items():
                        if known[:key_len] == triple[:key_len]:
                            merged.update(families)
                    if merged:
                        seen, why = merged, f"no CA group with this band; matched on {key_len}"
                        break
                else:
                    seen, why = None, "no Combined Arms precedent at all"
            else:
                why = "exact delivery/element/band match"

            if not seen:
                family, confidence = "?", "none"
                stats["needs a human"] += 1
            else:
                ranked = seen.most_common()
                family = ranked[0][0]
                share = ranked[0][1] / sum(seen.values())
                if len(ranked) == 1:
                    confidence, _ = "single", stats.update(["inherited cleanly"])
                elif share >= 0.6:
                    confidence, _ = "majority", stats.update(["inherited, CA split this triple"])
                else:
                    confidence, _ = "split", stats.update(["needs a human"])
                    family = "?"
            rows.append({
                "group": group["name"], "family": family, "status": "proposed",
                "confidence": confidence, "why": why,
                "candidates": dict(seen.most_common(4)) if seen else {},
                "delivery": group["delivery"], "element": group["element"],
                "band": group["band"], "uses": group["uses"],
                "weapons": group["weapons"],
            })
        out[sid] = {"groups": rows, "stats": dict(stats)}
    return out


def report(result: dict) -> str:
    lines = ["## Family propagation from the reviewed Combined Arms assignments", "",
             "| source | groups | inherited | CA split the triple | needs a human |",
             "|---|--:|--:|--:|--:|"]
    totals = collections.Counter()
    for sid, entry in result.items():
        s = entry["stats"]
        totals.update(s)
        totals["groups"] += len(entry["groups"])
        lines.append(f"| `{sid}` | {len(entry['groups'])} | {s.get('inherited cleanly', 0)} | "
                     f"{s.get('inherited, CA split this triple', 0)} | "
                     f"{s.get('needs a human', 0)} |")
    lines.append(f"| **total** | **{totals['groups']}** | "
                 f"**{totals['inherited cleanly']}** | "
                 f"**{totals['inherited, CA split this triple']}** | "
                 f"**{totals['needs a human']}** |")
    share = 100 * totals["needs a human"] / max(totals["groups"], 1)
    lines += ["", f"**{totals['needs a human']} of {totals['groups']} groups ({share:.0f}%) "
                  f"have no usable precedent and need a ruling.** Everything else is a proposal "
                  f"inherited from the Combined Arms review and still marked `proposed`."]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    result = propagate()
    print(report(result))
    if args.write:
        OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
