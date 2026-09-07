#!/usr/bin/env python3
"""audit_stat_uniqueness.py — no two units may share a stat value (DESIGN.md, the uniqueness law).

⛔ THE LAW, and it has never been guarded for UNIT stats. `audit_weapon_uniqueness`,
`audit_family_uniqueness` and `audit_unique_traits` cover weapons, warhead families and traits;
nothing checked the chassis. DESIGN.md is explicit that Cameo departs from Warcraft 2 here:

    "mirror factions are dull. We follow the Warcraft 3 philosophy: every faction, and every
     individual unit, gets its own distinct stats (no two units may share a stat value)."

Measured 2026-09-07, the law is not merely unmet — it is collapsed on the chassis stats:

    hp       869 values, 119 distinct   86% collide   50,000 HP is shared by 67 actors
    speed    792 values,  76 distinct   90% collide   speed 75 is shared by 86
    cost     868 values,  97 distinct   89% collide   500 credits is shared by 75
    w_range  707 values, 418 distinct   41% collide
    w_dps    687 values, 376 distinct   45% collide

Range and DPS are healthy because they were always granular. HP, speed and cost were on coarse
grids (2500 / 5 / 10) that made distinct values scarce — which is why the maintainer moved HP to
1000-steps and speed to steps of 1 on 2026-09-07. This audit is what makes that change pay off.

U1  actors identical on ALL priced stats, across DIFFERENT factions — the mirror-faction case
U2  actors identical on ALL priced stats within one faction — usually a chassis variant
U3  per-stat collision counts, so the grids can be driven apart deliberately

⚠ U1 IS THE ONE THAT MATTERS. A same-faction twin is often legitimate — `ra2_allies_ifv` and
`ra2_allies_ifv_chrono` are one chassis carrying different cargo. Four factions fielding a
byte-identical light infantry is the thing the law exists to forbid.

Read-only. Ratchets are LOWER-ONLY.
"""
from __future__ import annotations

import collections
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/balance"))
import faction_routes as fr          # noqa: E402
import reference_distribution as rd  # noqa: E402

STATS = ("hp", "speed", "w_range", "w_dps", "cost")

# LOWER-ONLY ratchets, set from this audit's own run.
U1_BASELINE = 36
U2_BASELINE = 33
U3_HP_BASELINE = 750
U3_SPEED_BASELINE = 716
U3_COST_BASELINE = 771


def main() -> int:
    rows = rd.cameo_rows()
    twins = collections.defaultdict(list)
    for r in rows:
        if all(r.get(s) for s in STATS):
            twins[tuple(r[s] for s in STATS)].append(r["id"])

    cross, same = [], []
    for key, ids in twins.items():
        if len(ids) < 2:
            continue
        factions = {fr.faction_of(i) for i in ids}
        (cross if len(factions) > 1 else same).append((key, sorted(ids)))

    per_stat = {}
    for s in STATS:
        vals = [r.get(s) for r in rows if r.get(s)]
        c = collections.Counter(vals)
        per_stat[s] = (len(vals), len(c), sum(n - 1 for n in c.values() if n > 1), c.most_common(1)[0])

    n1 = sum(len(ids) for _, ids in cross)
    n2 = sum(len(ids) for _, ids in same)
    print("# Unit stat uniqueness (DESIGN.md — the uniqueness law)\n")
    print(f"## U1 — identical on every priced stat, ACROSS factions: **{n1}** actors "
          f"in {len(cross)} groups (ratchet {U1_BASELINE})\n")
    for key, ids in sorted(cross, key=lambda t: -len(t[1]))[:20]:
        print(f"   {len(ids)}x  hp={key[0]:>8.0f} sp={key[1]:>5.0f} cost={key[4]:>6.0f}  "
              f"{', '.join(ids[:4])}" + (" …" if len(ids) > 4 else ""))

    print(f"\n## U2 — identical within ONE faction: **{n2}** actors in {len(same)} groups "
          f"(ratchet {U2_BASELINE})\n")
    for key, ids in sorted(same, key=lambda t: -len(t[1]))[:10]:
        print(f"   {len(ids)}x  {', '.join(ids[:4])}" + (" …" if len(ids) > 4 else ""))

    print(f"\n## U3 — per-stat collisions (ratchets hp {U3_HP_BASELINE} · "
          f"speed {U3_SPEED_BASELINE} · cost {U3_COST_BASELINE})\n")
    for s in STATS:
        n, distinct, dup, worst = per_stat[s]
        print(f"   {s:9} {n:>5} values {distinct:>5} distinct {dup:>5} collisions "
              f"({dup / max(1, n):>4.0%})  most-shared: {worst[0]:g} x{worst[1]}")

    failed = (n1 > U1_BASELINE or n2 > U2_BASELINE
              or per_stat["hp"][2] > U3_HP_BASELINE
              or per_stat["speed"][2] > U3_SPEED_BASELINE
              or per_stat["cost"][2] > U3_COST_BASELINE)
    print(f"\nexit={1 if failed else 0}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
