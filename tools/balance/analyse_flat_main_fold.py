#!/usr/bin/env python3
"""analyse_flat_main_fold.py — what folding a FLAT legacy main into its family main costs.

W24 (§11b.1: one main damage warhead per weapon). 230 weapons resolve more than one main, and
149 of those stacks contain a LEGACY-named main. The largest single cohort is `1Dam`, on 48.

⛔ `1Dam` IS NOT A 1-DAMAGE MARKER. The name is a legacy lie: all 48 nodes are `SpreadDamage`
carrying between 1,200 and 50,000 damage. Each is a genuine second main, and dropping one
would delete real damage — the mistake commit `47a66b6c2` already recorded, where a nuclear
batch "collapsed 15 warheads into 1 and kept the WARHEAD, not the TOTAL".

What makes these particular stacks tractable is that the legacy node carries **no `Versus`**,
so it applies FLAT damage to every armor, while the family main carries a full profile. So:

    before(armor) = D_main * p(armor)/100 + D_flat
    after(armor)  = (D_main + D_flat) * p(armor)/100

⭐ **§12.0h MEAN-100 MAKES THE FOLD MEAN-PRESERVING BY CONSTRUCTION.** Every `^Warhead_*` main
has its 16 armor rows normalised to arithmetic mean 100, so mean(p)/100 = 1 and:

    mean(before) = D_main + D_flat  ==  mean(after) = (D_main + D_flat) * 1

The total damage a weapon deals, averaged over the armor ladder, is **exactly unchanged**. The
fold moves SPREAD, not magnitude — which is precisely the split of duties §12.0h already rules
(`K` is shape-only, `Damage` is the sole magnitude knob). The per-armor shift is bounded by
`D_flat * (p_max - p_min) / 100`, and that bound is what needs a maintainer's eye.

This tool MEASURES that and writes nothing. A fold changes per-armor damage, so it needs
explicit permission (rule 4) — the point here is to make the decision cheap, per weapon.

Usage: python tools/balance/analyse_flat_main_fold.py [--legacy 1Dam] [--all-files]
       (default: only the CENTRAL weapon files — the ContentPacks are Codex's lane)
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import audit_three_way_split as tw  # noqa: E402
import miniyaml  # noqa: E402
import weapon_efficiency  # noqa: E402

# Mirrors audit_versus_profile.NON_ARMOR: `Shield` is its own compressed [100,400] ladder
# (§12.0c) and the other five are physical-state pseudo-armors. Folding them into a spread
# measurement is the mistake that once turned 2 out-of-band templates into a reported 9.
NON_ARMOR = {"Shield", "HAZMAT", "COMPOSITE", "BLAST", "REFLECTOR", "ARMOR"}
CENTRAL = ("mods/cameo/weapons/",)


def num(v, default=None):
    try:
        return float(str(v).split(",")[0])
    except (TypeError, ValueError):
        return default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--legacy", default="1Dam", help="the legacy main node name to fold")
    ap.add_argument("--all-files", action="store_true",
                    help="include ContentPacks (Codex's lane) as well as the central files")
    args = ap.parse_args()

    rs = miniyaml.Ruleset(str(ROOT))
    key = "Warhead@" + args.legacy
    rows, skipped = [], collections.Counter()

    for name in sorted(rs.weapons):
        if name.startswith(("^", "-")):
            continue
        node = rs.resolve_weapon(name)
        if node is None:
            continue
        mains = tw.main_warheads(node)
        if len(mains) < 2 or args.legacy not in mains:
            continue
        src_file = str(rs.weapons[name].file).replace("\\", "/")
        central = any(src_file.startswith(p) or ("/" + p) in src_file for p in CENTRAL)
        if not args.all_files and not central:
            skipped["not my lane (ContentPacks)"] += 1
            continue
        if len(mains) != 2:
            skipped[f"{len(mains)} mains — which survives is a design call"] += 1
            continue

        flat = node.child(key)
        other = [m for m in mains if m != args.legacy][0]
        prof_node = node.child("Warhead@" + other)
        if flat is None or prof_node is None:
            skipped["node not resolvable"] += 1
            continue

        d_flat = num({g.key: g.value for g in flat.children}.get("Damage"), 0) or 0
        d_main = num({g.key: g.value for g in prof_node.children}.get("Damage"), 0) or 0
        if d_flat <= 0 or d_main <= 0:
            skipped["a main carries no damage"] += 1
            continue

        # ⚠ Versus through weapon_efficiency.versus_of, never a hand parse (hook-enforced):
        # a bespoke scanner once left the `Versus:` dict open and let `PercentageVersus:` rows
        # overwrite the profile, making every measured number consistent and wrong.
        vflat = weapon_efficiency.versus_of(flat) or {}
        vprof = weapon_efficiency.versus_of(prof_node) or {}
        if vflat:
            skipped["the legacy node HAS a profile — not a flat fold"] += 1
            continue
        rowsp = {k: v for k, v in vprof.items() if k not in NON_ARMOR and v > 0}
        if len(rowsp) < 8:
            skipped["family main has no usable profile"] += 1
            continue

        mean_p = statistics.mean(rowsp.values())
        before = {a: d_main * p / 100.0 + d_flat for a, p in rowsp.items()}
        after = {a: (d_main + d_flat) * p / 100.0 for a, p in rowsp.items()}
        shifts = {a: after[a] / before[a] for a in rowsp}
        worst_a = min(shifts, key=lambda a: shifts[a])
        best_a = max(shifts, key=lambda a: shifts[a])
        rows.append(dict(
            weapon=name, other=other, d_main=d_main, d_flat=d_flat, mean_p=mean_p,
            mean_before=statistics.mean(before.values()),
            mean_after=statistics.mean(after.values()),
            worst=(worst_a, shifts[worst_a]), best=(best_a, shifts[best_a]),
            file=src_file))

    print(f"# Folding `{args.legacy}` into its family main — {len(rows)} weapons in scope\n")
    for why, n in skipped.most_common():
        print(f"  skipped {n:3d}  {why}")
    if not rows:
        print("\nnothing in scope")
        return 0

    # The MEAN-100 claim, asserted per weapon rather than asserted once in prose.
    bad = [r for r in rows if abs(r["mean_after"] / r["mean_before"] - 1) > 0.02]
    print(f"\n## Mean total damage is preserved: {len(rows) - len(bad)}/{len(rows)} within 2%")
    print("\nThat is §12.0h MEAN-100 doing the work, not a coincidence: mean(p)=100 so "
          "`mean(D_main*p/100 + D_flat)` and `mean((D_main+D_flat)*p/100)` are the same number. "
          "The fold moves SPREAD, never magnitude.")
    if bad:
        print(f"\n⚠ {len(bad)} weapons whose profile is NOT mean-100 — the fold would move "
              "their magnitude too, so they need separate review:")
        for r in bad:
            print(f"   {r['weapon']:34s} profile mean {r['mean_p']:.1f} "
                  f"(mean {r['mean_before']:.0f} -> {r['mean_after']:.0f})")

    rows.sort(key=lambda r: r["worst"][1])
    print(f"\n## Per-armor shift — the part that needs a decision\n")
    print("| weapon | family main | D_main | D_flat | flat share | worst armor | best armor |")
    print("|---|---|--:|--:|--:|---|---|")
    for r in rows:
        share = r["d_flat"] / (r["d_main"] + r["d_flat"])
        print(f"| `{r['weapon']}` | `{r['other']}` | {r['d_main']:,.0f} | {r['d_flat']:,.0f} | "
              f"{share:.0%} | {r['worst'][0]} x{r['worst'][1]:.2f} | "
              f"{r['best'][0]} x{r['best'][1]:.2f} |")

    shares = [r["d_flat"] / (r["d_main"] + r["d_flat"]) for r in rows]
    worst = min(r["worst"][1] for r in rows)
    print(f"\n**Flat share of total damage:** median {statistics.median(shares):.0%}, "
          f"max {max(shares):.0%}. **Worst single-armor change across the cohort: "
          f"x{worst:.2f}.**")
    print("\nThe flat share is the real lever: a weapon whose legacy node is a small part of "
          "its damage folds almost invisibly, and one where it dominates is effectively "
          "being given a profile it never had. Sorted worst-first above so the decision can "
          "be taken in one pass, or split at a share threshold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
