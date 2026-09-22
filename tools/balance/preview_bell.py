#!/usr/bin/env python3
"""preview_bell.py — what would §12.0i's bell change, without writing a byte of yaml?

    python tools/balance/preview_bell.py            # summary
    python tools/balance/preview_bell.py --detail CannonAP

CLAUDE.md rule 4: a warhead's `Versus` may not change without explicit maintainer permission.
`gen_weapon_template.USE_BELL` is therefore OFF by default and this script is how the decision
gets made — it runs the generator's profile pipeline BOTH ways in-process and reports the
difference, so the authorisation is given against measured impact rather than a promise.

⛔ THE ACCEPTANCE TEST IS TILT-TO-TILT ON THE SAME BASE, and getting that wrong is the trap this
script exists to avoid. Comparing the bell against the shipped TEMPLATES answers a different
question — the level also changes the body's `step` and `floor` (`LEVELS`), so the profiles differ
for reasons the tilt never touched. Run the SHIPPED `class_tilt` through the same comparison and it
scores **+18.7% worse than doing nothing**, which is the control that proves the comparison invalid.
This script always reports that control alongside the bell.

⚠ NEVER HAND-PARSE YAML — the live profiles come through `miniyaml.Ruleset.resolve_weapon` and
`weapon_efficiency.versus_of`.
"""

from __future__ import annotations

import argparse
import math
import pathlib
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):          # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8")

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(ROOT / "tools" / "audit"))

import gen_weapon_template as gwt  # noqa: E402
from miniyaml import Ruleset  # noqa: E402
import weapon_efficiency as we  # noqa: E402

LEVELS = ("Light", "Medium", "Heavy")
COMPANION = ("Percentage", "ExtraDamage", "ExtraRepair", "Concrete")
OFF_AXIS = {"Shield", "HAZMAT", "COMPOSITE", "BLAST", "REFLECTOR", "ARMOR"}


def live_profiles() -> dict[tuple[str, str], dict[str, float]]:
    """{(family, level): {armor: versus}} straight off the resolved ruleset."""
    rs = Ruleset(ROOT)
    out: dict[tuple[str, str], dict[str, float]] = {}
    for name in sorted(rs.weapons):
        if not name.startswith("^Warhead_"):
            continue
        family, _, level = name[len("^Warhead_"):].rpartition("_")
        if level not in LEVELS or not family:
            continue
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            continue
        for wh in resolved.children:
            if not wh.key.startswith("Warhead@") or any(c in wh.key for c in COMPANION):
                continue
            versus = we.versus_of(wh)
            if versus:
                out[(family, level)] = {a: float(v) for a, v in versus.items()
                                        if a not in OFF_AXIS}
            break
    return out


def untilted(profile: dict[str, float], level: str) -> list[tuple[str, float]]:
    """Undo `class_tilt`'s exponent to recover the base the tilt was applied to.

    The tilt is `TILT_RATIO ** tilt_exponent` plus a rank restore, and both are invertible: the
    restore is a permutation within a ladder, so re-sorting against the reciprocal exponents
    returns the pre-tilt magnitudes. This is what makes a like-for-like comparison possible.
    """
    vals = dict(profile)
    # ⛔ MIRROR `class_tilt`'s OWN GUARD. It returns a flat profile untouched — Sonic and Magic
    # are flat BY DESIGN — so there is no tilt to invert there, and inverting one anyway
    # FABRICATES a gradient. Measured with that mistake in: 8 "reorderings" that were entirely
    # my own inverse, on families the shipped generator never tilts.
    live = [v for a, v in profile.items() if a not in gwt.NON_ARMOR_ROWS]
    if not live or max(live) <= min(live):
        return [(a, v) for a, v in profile.items()]
    out = dict(vals)
    for ladder in gwt.LADDERS.values():
        rungs = [a for a in ladder if a in vals and a not in gwt.DERIVED_ARMORS]
        if len(rungs) < 2:
            continue
        n = len(rungs)
        loose = [vals[a] * gwt.TILT_RATIO ** -gwt.tilt_exponent(level, i, n)
                 for i, a in enumerate(rungs)]
        order = sorted(range(n), key=lambda i: (-vals[rungs[i]], i))
        for slot, i in enumerate(order):
            out[rungs[i]] = sorted(loose, reverse=True)[slot]
    return [(a, out[a]) for a in profile]


def rows_to_dict(rows) -> dict[str, float]:
    return {a: float(v) for a, v in rows}


def rel(a: float, b: float) -> float:
    return abs(a - b) / b if b else 0.0


def ladder_order(prof: dict[str, float], rungs: list[str]) -> list[str]:
    """⛔ DERIVED armors are excluded — they are RECOMPUTED, not ranked (§12.0b).

    `Heroic` sits in the INF ladder but is `Plate * Scout / peak`, so it legitimately lands
    somewhere else whenever the profile moves. Counting it made the first run of this preview
    report 25 reorderings where there are none: 15 were Heroic being re-derived.
    """
    present = [a for a in rungs if a in prof and a not in gwt.DERIVED_ARMORS]
    return sorted(present, key=lambda a: prof[a])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--detail", metavar="FAMILY", help="print one family's before/after rows")
    args = ap.parse_args()

    live = live_profiles()
    if not live:
        print("no `^Warhead_*` profiles resolved — cannot run.")
        return 0

    families = sorted({f for f, _l in live})
    print("# preview_bell — what §12.0i's bell would change\n")
    print(f"`gen_weapon_template.USE_BELL` is **{'ON' if gwt.USE_BELL else 'OFF'}**; "
          f"this preview runs both paths regardless and writes nothing.\n")
    print(f"Families: **{len(families)}** · profiles compared: **{len(live)}**\n")

    moved, worst, reorders, flat = [], [], 0, []
    shipped_reorders = [0]
    per_level: dict[str, list[float]] = {lv: [] for lv in LEVELS}
    for (family, level), prof in sorted(live.items()):
        base = untilted(prof, level)
        shipped = rows_to_dict(gwt.class_tilt(base, level))
        belled = rows_to_dict(gwt.heaviness_bell(base, level))
        if all(abs(shipped[a] - belled[a]) < 1e-9 for a in shipped):
            flat.append(f"{family}_{level}")
            continue
        deltas = [rel(belled[a], shipped[a]) for a in shipped
                  if a not in gwt.NON_ARMOR_ROWS and shipped[a] > 0]
        if not deltas:
            continue
        moved.append(statistics.fmean(deltas))
        worst.append((max(deltas), family, level))
        per_level[level].append(statistics.fmean(deltas))
        # Against the BASE's own order, which is what §12.0d's rank restore promises to keep —
        # and always alongside the shipped tilt, so the number has something to mean.
        for rungs in gwt.LADDERS.values():
            want = ladder_order(rows_to_dict(base), rungs)
            if ladder_order(belled, rungs) != want:
                reorders += 1
            if ladder_order(shipped, rungs) != want:
                shipped_reorders[0] += 1

    print("## Impact\n")
    print("| | |\n|---|--:|")
    print(f"| profiles the bell would move | {len(moved)} |")
    print(f"| profiles it leaves untouched (flat by design) | {len(flat)} |")
    print(f"| mean row change | {statistics.fmean(moved) * 100:.1f}% |"
          if moved else "| mean row change | n/a |")
    print(f"| median row change | {statistics.median(moved) * 100:.1f}% |"
          if moved else "")
    print(f"| worst single row | {max(worst)[0] * 100:.1f}% "
          f"({max(worst)[1]}_{max(worst)[2]}) |" if worst else "")
    print(f"| ⛔ ladder orderings the bell changes | {reorders} |")
    print(f"| the same for the SHIPPED `class_tilt` | {shipped_reorders[0]} |")
    print()
    print("| level | profiles | mean row change |")
    print("|---|--:|--:|")
    for lv in LEVELS:
        vals = per_level[lv]
        print(f"| {lv} | {len(vals)} | {statistics.fmean(vals) * 100:.1f}% |"
              if vals else f"| {lv} | 0 | — |")

    print("\n## The control — why this comparison is the valid one\n")
    print("Comparing the bell against the SHIPPED TEMPLATES instead of tilt-to-tilt is invalid, "
          "because the level also changes the body's `step` and `floor`. Run the shipped "
          "`class_tilt` through that comparison and it scores worse than applying no tilt at all:\n")
    no_tilt, with_tilt = [], []
    for (family, level), prof in sorted(live.items()):
        if level == "Medium":
            continue
        med = live.get((family, "Medium"))
        if not med:
            continue
        base = untilted(med, "Medium")
        shipped = rows_to_dict(gwt.class_tilt(base, level))
        common = [a for a in prof if a in shipped and prof[a] > 0 and shipped[a] > 0]
        if not common:
            continue
        no_tilt.append(statistics.fmean(abs(math.log(med[a] / prof[a])) for a in common
                                        if a in med and med[a] > 0))
        with_tilt.append(statistics.fmean(abs(math.log(shipped[a] / prof[a])) for a in common))
    if no_tilt and with_tilt:
        n, w = statistics.fmean(no_tilt), statistics.fmean(with_tilt)
        print(f"    no tilt at all vs the shipped template   {n:.4f}")
        print(f"    the SHIPPED class_tilt vs the same        {w:.4f}   ({(w / n - 1) * 100:+.1f}%)")
        print("\nSo a bell scoring badly on THAT comparison would say nothing about the bell.")

    # The clearest single view: ONE base per family, swept over h, so the body's per-level
    # `step`/`floor` difference is held constant and only heaviness moves.
    print("\n## What heaviness actually does — one base, h = 0 -> 2\n")
    print("⚠ Read this table, NOT `--detail` across its level columns. `--detail` recovers a "
          "SEPARATE base per level (the levels differ in body as well as tilt), so reading it "
          "sideways mixes two changes. Here the base is held fixed.\n")
    swing: dict[str, list[float]] = {}
    for family in families:
        med = live.get((family, "Medium"))
        if not med:
            continue
        base = untilted(med, "Medium")
        body = [v for a, v in base if a not in gwt.NON_ARMOR_ROWS]
        if not body or max(body) <= min(body):
            continue
        at = {lv: rows_to_dict(gwt.heaviness_bell(base, lv)) for lv in LEVELS}
        for a in rows_to_dict(base):
            if a in gwt.NON_ARMOR_ROWS or a in gwt.DERIVED_ARMORS or a not in gwt.BELL_AXIS:
                continue
            lo, hi = at["Light"][a], at["Heavy"][a]
            if lo > 0:
                swing.setdefault(a, []).append((hi - lo) / lo)
    print("| armor | x | median move | min | max |")
    print("|---|--:|--:|--:|--:|")
    for a in sorted(swing, key=lambda a: gwt.BELL_AXIS[a]):
        v = swing[a]
        print(f"| {a} | {gwt.BELL_AXIS[a]:.3f} | {statistics.fmean(v) * 100:+.1f}% | "
              f"{min(v) * 100:+.1f}% | {max(v) * 100:+.1f}% |")
    print("\n⚠ An armor sitting AT the centre barely moves, and that is the bell working, not a "
          "fault: the peak passes over it rather than toward or away from it. `Bomber` (x=0.833) "
          "and `Helicopter` (x=1.167) are one slot either side of 1.000, so they are the two "
          "smallest movers — every non-monotone row across all families is one of those two. They "
          "still separate from each other, in opposite directions, which is the distinction the "
          "coarse bucket axis could not make at all.")

    if args.detail:
        fam = args.detail
        print(f"\n## {fam} — shipped tilt vs bell, per level\n")
        header = f"| armor | x | " + " | ".join(f"{lv} now | {lv} bell" for lv in LEVELS) + " |"
        print(header)
        print("|---" * (2 + 2 * len(LEVELS)) + "|")
        cols: dict[str, dict[str, tuple[float, float]]] = {}
        for lv in LEVELS:
            prof = live.get((fam, lv))
            if not prof:
                continue
            base = untilted(prof, lv)
            s = rows_to_dict(gwt.class_tilt(base, lv))
            b = rows_to_dict(gwt.heaviness_bell(base, lv))
            for a in s:
                cols.setdefault(a, {})[lv] = (s[a], b[a])
        for a in sorted(cols, key=lambda a: (gwt.BELL_AXIS.get(a, 99), a)):
            x = gwt.BELL_AXIS.get(a)
            cells = []
            for lv in LEVELS:
                s, b = cols[a].get(lv, (float("nan"), float("nan")))
                cells += [f"{s:.1f}", f"{b:.1f}"]
            print(f"| {a} | {'—' if x is None else f'{x:.3f}'} | " + " | ".join(cells) + " |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
