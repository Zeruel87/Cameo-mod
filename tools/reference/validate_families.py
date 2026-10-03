#!/usr/bin/env python3
"""Score a family assignment against the one source where the answer is already known.

WHY THIS EXISTS. `propagate_families.py` carries the reviewed Combined Arms family assignments
onto the other sixteen sources by matching the measured DELIVERY x ELEMENT x BAND triple. That is a
proposal engine, and nothing measured whether its proposals were any good -- the plan was to put
1,059 of them in front of the maintainer.

But one source needs no propagation at all: Cameo. A Cameo weapon that inherits
`^Warhead_<Family>_<Level>` HAS a family, stated in the yaml, by construction (R37). 904 concrete
weapons carry such an inherit. That is a labelled test set, free, and it never needed a ruling.

So: compress Cameo's own weapons into groups exactly as every reference source is compressed, ask
the propagation what family each group should get, and compare against what Cameo actually says.
Any method that cannot recover Cameo's own assignments from Cameo's own weapons will not do better
on a mod nobody has reviewed.

WHAT THE FIRST RUN FOUND (2026-09-22, recorded as R39):

  propagation by triple   19% of groups get the right family   (top-4 candidates contain it: 38%)
  nearest profile shape   11%                                  (top-3 contain it: 19%)

  ...and the reason is not the method. It is the GROUPS. At the shipped `tau = 0.50` a single
  group holds a MEDIAN OF 3 distinct Cameo families (worst: 15), and only 11 of 53 groups are
  80% one family. No single-family label can be right about a group like that, so ~61% is the
  CEILING any method is playing against, not 100%.

  Tightening the clustering fixes the purity and costs group count:

      tau    groups   median purity   >=80% pure   usage-weighted purity
      0.50      162         61%          11/53             53%
      0.30      241         67%          18/61             67%
      0.20      302         75%          29/71             77%
      0.10      413         89%          47/71             84%

  All columns are over the SAME population -- groups with at least MIN_VOTERS labelled members.
  Usage weighting makes tau 0.50 WORSE (53% vs 61%), because the big groups are the mixed ones:
  `BulletHE_Veh` is 296 uses spanning CannonHE, Bullet, Demolition and more. Reviewing "just the
  important ones" therefore reviews precisely the groups a single label fits worst.

CEILING, NOT SCORE. A method scoring 60% here is not 40% wrong -- it may be at the ceiling the
group impurity allows. Always read `--purity` alongside the score.

    python tools/reference/validate_families.py              # score the current propagation
    python tools/reference/validate_families.py --purity     # the tau sweep above
    python tools/reference/validate_families.py --shape      # score nearest-profile instead
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "reference"))

import cameo_families as cf  # noqa: E402

GROUPS = ROOT / "docs" / "reference" / "warhead_groups.json"
DOC = ROOT / "docs" / "reference" / "warhead_family_assignment.yaml"

# The source whose groups we score. Cameo's resolved weapons are the only labelled set.
TRUTH_SOURCE = "cameo_resolved"
# A group needs at least this many labelled members before its plurality means anything.
MIN_VOTERS = 3


def ground_truth() -> dict:
    """{weapon: {family: weight}} from the `^Warhead_<Family>_<Level>` templates it inherits.

    Delegates to `cameo_families.labelled_weapons` so the LEVEL-token parser lives in one place.
    This function once split on the last underscore and invented a family per template variant
    (`CannonHE_Heavy_D2K` alongside `CannonHE`), which inflated the family count 51 -> 53 and
    silently scattered the ground truth it was meant to define.
    """
    return cf.labelled_weapons()


def tally_of(group: dict, truth: dict) -> collections.Counter:
    counter: collections.Counter = collections.Counter()
    for weapon in group["weapons"]:
        if weapon in truth:
            counter.update(truth[weapon])
    return counter


def profile_map(group: dict) -> dict:
    """The group's normalised Versus row as {armor: value}, dropping `n/a` and zero cells."""
    return {a: v for a, v in zip(group["armors"], group.get("profile") or [])
            if isinstance(v, (int, float)) and v > 0}


def shape_distance(a: dict, b: dict, floor: int = 4):
    """RMS log difference over the armours both profiles state. None if too few overlap."""
    shared = [k for k in a if k in b]
    if len(shared) < floor:
        return None
    diffs = [math.log(a[k] / b[k]) for k in shared]
    return math.sqrt(sum(d * d for d in diffs) / len(diffs))


def ca_reference() -> list:
    """[(family, profile)] for the reviewed Combined Arms groups."""
    import yaml
    doc = yaml.safe_load(DOC.read_text(encoding="utf-8"))
    rows = {g["name"]: g
            for g in json.load(GROUPS.open(encoding="utf-8"))["combined_arms"]["groups"]}
    out = []
    for name, row in doc["groups"].items():
        group = rows.get(name)
        if not group:
            continue
        profile = profile_map(group)
        if profile:
            out.append((row["family"], profile))
    return out


def score(use_shape: bool) -> str:
    import propagate_families as pf
    truth = ground_truth()
    groups = json.load(GROUPS.open(encoding="utf-8"))[TRUTH_SOURCE]["groups"]
    proposals = {r["group"]: r for r in pf.propagate()[TRUTH_SOURCE]["groups"]}
    reference = ca_reference() if use_shape else []

    hits = near = total = skipped = 0
    misses = []
    for group in groups:
        counter = tally_of(group, truth)
        if sum(counter.values()) < MIN_VOTERS:
            skipped += 1
            continue
        actual, actual_n = counter.most_common(1)[0]
        purity = actual_n / sum(counter.values())

        if use_shape:
            profile = profile_map(group)
            ranked = sorted((d, fam) for fam, ref in reference
                            if (d := shape_distance(profile, ref)) is not None)
            if not ranked:
                skipped += 1
                continue
            guess = ranked[0][1]
            shortlist = {f for _, f in ranked[:3]}
        else:
            row = proposals.get(group["name"])
            if not row:
                skipped += 1
                continue
            guess = row["family"]
            shortlist = set(row.get("candidates") or {})

        total += 1
        if guess == actual:
            hits += 1
        else:
            misses.append((group["uses"], group["name"], guess, actual, purity))
        if actual in shortlist:
            near += 1

    method = "nearest profile shape" if use_shape else "propagation by delivery/element/band"
    lines = ["## Family assignment scored against Cameo's own templates", "",
             f"method    : {method}",
             f"scored    : {total} groups ({skipped} had fewer than {MIN_VOTERS} labelled members)",
             f"top-1     : {hits} correct ({hits / max(total, 1):.0%})",
             f"shortlist : {near} contain the right family ({near / max(total, 1):.0%})", ""]
    if misses:
        lines += ["Biggest misses by usage. `purity` is the share of the group the right answer",
                  "itself holds, so a low one means NO single label fits:", "",
                  "| uses | group | guessed | actual | purity |", "|--:|---|---|---|--:|"]
        for uses, name, guess, actual, purity in sorted(misses, reverse=True)[:15]:
            lines.append(f"| {uses} | `{name}` | {guess} | {actual} | {purity:.0%} |")
    return "\n".join(lines)


def purity_sweep(taus: list) -> str:
    import compress_warheads as cw
    import warhead_matrix as wm
    truth = ground_truth()
    entry = wm.collect()[TRUTH_SOURCE]
    lines = ["## Group purity against Cameo's own templates, by clustering threshold", "",
             "`purity` = the share of a group held by its most common family. A single-family",
             "label cannot beat this, so it is the CEILING for every assignment method.", "",
             "| tau | groups | median purity | >=80% pure | median families/group | usage-weighted |",
             "|--:|--:|--:|--:|--:|--:|"]
    for tau in taus:
        result = cw.compress(TRUTH_SOURCE, entry, tau)
        purities, distinct, weighted = [], [], []
        for group in result["groups"]:
            counter = tally_of(group, truth)
            if sum(counter.values()) < MIN_VOTERS:
                continue
            purity = counter.most_common(1)[0][1] / sum(counter.values())
            purities.append(purity)
            distinct.append(len(counter))
            weighted.append((purity, group["uses"]))
        if not purities:
            continue
        mass = sum(u for _, u in weighted)
        wpur = sum(p * u for p, u in weighted) / mass if mass else 0
        lines.append(f"| {tau:.2f} | {len(result['groups'])} | {statistics.median(purities):.0%} | "
                     f"{sum(1 for p in purities if p >= 0.8)}/{len(purities)} | "
                     f"{statistics.median(distinct):.0f} | {wpur:.0%} |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--purity", action="store_true", help="sweep the clustering threshold")
    ap.add_argument("--shape", action="store_true", help="score nearest-profile instead")
    ap.add_argument("--taus", default="0.50,0.30,0.20,0.10")
    args = ap.parse_args()
    if args.purity:
        print(purity_sweep([float(t) for t in args.taus.split(",")]))
    else:
        print(score(args.shape))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
