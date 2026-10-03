#!/usr/bin/env python3
"""audit_elite_range.py — an elite weapon reaches 1000 further than its base (DESIGN §12.0m).

Maintainer ruling 2026-09-30: RA2-style elite weapons have +1000 range ("Yes, exactly that's the rule for RA2 styled
elite weapons having +1000 range"). Every weapon `X_elite` whose base `X` exists is checked on the RESOLVED Range
(miniyaml.Ruleset.resolve_weapon — never a hand parser):

* FOLLOWS  — elite = base + 1000;
* MELEE    — both ranges below 2c0 and equal: a melee weapon must touch its target, so the rule does not apply;
* OFF-RULE — anything else (+1111 steps, +4000, a SHORTER elite, …).

OFF-RULE is a lower-only ratchet: the pre-existing count is debt for the rebalance, which moves ranges through the
balance pipeline (hard rule 3), never by hand. A new OFF-RULE pair fails; a fix lowers BASELINE here.

Usage: python tools/audit/audit_elite_range.py [--list]
"""

from __future__ import annotations

import argparse
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "audit"))
import miniyaml  # noqa: E402

ELITE_BONUS = 1000
MELEE_BELOW = 2048
BASELINE = 56  # OFF-RULE pairs on master 2026-09-30; lower-only


def wdist(value: str | None) -> int | None:
    """A Range as world units: `6170`, or `5c512` (cells × 1024 + units). None when absent or unparseable."""
    if not value:
        return None
    v = value.split(",")[0].strip()
    try:
        if "c" in v:
            cells, rest = v.split("c", 1)
            return int(cells or 0) * 1024 + int(rest or 0)
        return int(v)
    except ValueError:
        return None


def classify(base: int, elite: int) -> str:
    if elite - base == ELITE_BONUS:
        return "FOLLOWS"
    if base == elite and base < MELEE_BELOW:
        return "MELEE"
    return "OFF-RULE"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true", help="list every OFF-RULE pair")
    args = ap.parse_args()

    rs = miniyaml.Ruleset(REPO)
    names = set(rs.weapons)
    # `^` templates are abstract (no Range of their own), not weapons a unit fires.
    pairs = sorted((n[: -len("_elite")], n) for n in names
                   if n.endswith("_elite") and not n.startswith("^") and n[: -len("_elite")] in names)

    counts = {"FOLLOWS": 0, "MELEE": 0, "OFF-RULE": 0, "UNRESOLVED": 0}
    off = []
    for base, elite in pairs:
        b = rs.resolve_weapon(base)
        e = rs.resolve_weapon(elite)
        rb = wdist(b.get("Range") if b else None)
        re_ = wdist(e.get("Range") if e else None)
        if rb is None or re_ is None:
            counts["UNRESOLVED"] += 1
            continue
        kind = classify(rb, re_)
        counts[kind] += 1
        if kind == "OFF-RULE":
            off.append((base, rb, re_, re_ - rb))

    print("# audit_elite_range — elite = base + 1000 (DESIGN §12.0m)\n")
    print(f"{len(pairs)} base/elite pairs: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    if args.list or len(off) > BASELINE:
        print("\n| base | base range | elite range | elite - base |\n|---|--:|--:|--:|")
        for base, rb, re_, d in off:
            print(f"| `{base}` | {rb} | {re_} | {d:+d} |")

    if len(off) > BASELINE:
        print(f"\n**FAIL** — OFF-RULE {len(off)} exceeds the baseline {BASELINE}: a new elite weapon breaks the +1000 rule.")
        return 1
    if len(off) < BASELINE:
        print(f"\nOFF-RULE {len(off)} is below the baseline {BASELINE} — lower BASELINE in this script to lock the fix in.")
    print("\n**PASS**")
    return 0


if __name__ == "__main__":
    sys.exit(main())
