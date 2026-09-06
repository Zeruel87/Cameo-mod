#!/usr/bin/env python3
"""audit_warhead_split.py — guard against the multi-warhead over-damage bug.

Background (2026-07-22 regression, INCIDENT: commit 04de392b3):
Cameo weapons deliberately stack several offensive `Warhead@X: SpreadDamage`
nodes — one per inherited weapon-class template — and the engine detonates
ALL of them on the target, so the weapon's effective per-shot damage is the
SUM (formula.spread_damage_sum). A balance pass wrote a single design number
onto EVERY warhead of such weapons, multiplying their real damage by the
warhead count (e.g. the TD Nod Stealth Soldier's dart went 5 x 2000 -> 5 x
22000 = 110000/shot).

The pipeline now splits an edited TOTAL back across warheads proportionally
(formula.distribute_damage), so it can never broadcast again. This audit is
the belt-and-suspenders that FAILS the suite if the fingerprint ever
reappears from a hand edit or a foreign tool:

  FAIL 1 (broadcast fingerprint): a weapon with >=2 MAIN SpreadDamage / AreaDamage
         warheads where EVERY main has the identical, non-zero Damage. This is
         the W24 inheritance-pileup pattern and is caught on a ratchet so the
         existing debt stays visible without holding every commit hostage.

  FAIL 2 (own-side splash exceeds the shot): a `*FriendlyFire` SpreadDamage
         warhead whose Damage is greater than the largest main warhead.

It also prints an informational review list of high uniform stacks
(>=3 equal mains at >= REVIEW_DMG each) — allowed, but worth a glance.
"""
from __future__ import annotations

import sys

from cameo_model import Model
from report import h1, h2, table

REVIEW_DMG = 8000

# ---------------------------------------------------------------------------
# FAIL 1 — the BROADCAST FINGERPRINT, on a ratchet.
#
# W24 widened the original FAIL 1 by dropping the side-warhead precondition:
# the real bug is "every main warhead has the identical damage", regardless of
# whether a FriendlyFire/ExtraDamage twin is also present. That fingerprint was
# present on 874 fired weapons (981 concrete weapons total) as of 2026-08-17.
#
# The ratchet fails only when the count RISES above the recorded baseline. New
# broadcasts are caught immediately; the existing W24 debt stays visible.
#
# ⬇ LOWER THIS as W24 collapses weapons. It must never be raised — a rise means
# a hand edit or a foreign tool reintroduced the bug distribute_damage exists to
# prevent.
#
# ⚠ 970, not the 874 quoted in the W24 diagnosis: that figure counts only weapons
# FIRED by a concrete actor, while this audit scans EVERY concrete weapon
# (`rs.weapons`), fired or not. Two populations, both correct for their own
# question — don't reconcile them by changing one.
BROADCAST_BASELINE = 75

# The two former routing-revealed exceptions were consolidated into their
# selected Flak and Bullet profiles. Keep the registry empty so a future
# exception must be an explicit reviewed decision rather than inherited debt.
ROUTING_REVEALED_BROADCASTS = {}

# Exact behavior restoration, not a newly authored broadcast.  PR 287 folded
# these four profiles and accidentally multiplied Hydralisk's ground damage.
# (The HydraSpit entry was retired 2026-09-06: after `8748c68e4` it resolves to a
# single BulletChem main, so the exemption could never fire and would only have
# masked a future re-broadcast.)
RESTORED_GAMEPLAY_BROADCASTS = {}


def _int(v) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def classify_warheads(resolved):
    """(mains, friendlyfire, extradamage) as lists of (tag, damage) for the
    SpreadDamage / AreaDamage warheads; HealthPercentageDamage/`*Percentage` ignored."""
    mains, ff, extra = [], [], []
    for c in resolved.children:
        # AreaDamage is the Cameo drop-in for SpreadDamage (baked FF + rings);
        # classify it identically. AreaDamagePercentage stays ignored like %.
        if not c.key.startswith("Warhead@") or c.value not in ("SpreadDamage", "AreaDamage"):
            continue
        tag = c.key.split("@", 1)[1]
        low = tag.lower()
        d = _int(c.get("Damage"))
        if low.endswith("percentage"):
            continue
        if low.endswith("friendlyfire"):
            ff.append((tag, d))
        elif low.endswith("extradamage"):
            extra.append((tag, d))
        else:
            mains.append((tag, d))
    return mains, ff, extra


def main() -> int:
    m = Model()
    rs = m.rs

    broadcast_rows = []   # FAIL 1 (uniform main warheads)
    routing_revealed_rows = []  # known composites unmasked by target-route repair
    restored_gameplay_rows = []  # exact profiles restored to repair regressions
    ff_rows = []          # FAIL 2
    review_rows = []      # informational

    for wname in sorted(rs.weapons):
        if wname.startswith("^"):
            continue
        resolved = rs.resolve_weapon(wname)
        if resolved is None:
            continue
        mains, ff, extra = classify_warheads(resolved)
        if len(mains) < 2:
            continue
        main_dmgs = [d for _, d in mains]
        mx = max(main_dmgs)

        # FAIL 1 — every MAIN broadcast to one identical, non-zero value
        if len(set(main_dmgs)) == 1 and main_dmgs[0] > 0:
            row = [
                wname, str(len(mains)), str(main_dmgs[0]),
                str(main_dmgs[0] * len(mains))]
            fingerprint = tuple(sorted(mains))
            if ROUTING_REVEALED_BROADCASTS.get(wname) == fingerprint:
                routing_revealed_rows.append(row)
            elif RESTORED_GAMEPLAY_BROADCASTS.get(wname) == fingerprint:
                restored_gameplay_rows.append(row)
            else:
                broadcast_rows.append(row)

        # FAIL 2 — friendly fire louder than the offensive shot
        for tag, d in ff:
            if d > mx:
                ff_rows.append([wname, tag, str(d), str(mx)])

        # review — big uniform stacks (allowed, but flag for a look)
        if len(set(main_dmgs)) == 1 and len(mains) >= 3 and mx >= REVIEW_DMG:
            review_rows.append([
                wname, str(len(mains)), str(mx), str(mx * len(mains))])

    out = [h1("Warhead-split guard (multi-warhead over-damage)")]
    over_baseline = len(broadcast_rows) > BROADCAST_BASELINE
    failed = bool(ff_rows or over_baseline)

    out.append(h2(f"FAIL 1 — broadcast fingerprint / every MAIN identical "
                  f"({len(broadcast_rows)} vs baseline {BROADCAST_BASELINE})"))
    if over_baseline:
        out.append(f"**FAIL — {len(broadcast_rows)} exceeds the baseline of "
                   f"{BROADCAST_BASELINE}.** A weapon just had one damage number broadcast "
                   "across its mains. Edit the per-shot TOTAL through the workbook so "
                   "`formula.distribute_damage` splits it, or collapse the weapon to one "
                   "main warhead during W24.\n")
    else:
        out.append(
            "_at or below baseline_ — pre-existing **W24** debt "
            f"({len(broadcast_rows)} weapons), not a regression. The ratchet catches new "
            "broadcasts without blocking every commit on the existing pile. "
            "**Lower `BROADCAST_BASELINE` as W24 collapses weapons; never raise it.**\n")
    out.append(table(["weapon", "mains", "per_warhead", "total"], broadcast_rows[:40]))
    if len(broadcast_rows) > 40:
        out.append(f"\n_... and {len(broadcast_rows) - 40} more._\n")

    out.append(h2(f"Review — exact gameplay restorations ({len(restored_gameplay_rows)})"))
    out.append(table(
        ["weapon", "mains", "per_warhead", "total"], restored_gameplay_rows))

    out.append(h2(f"Review — routing-revealed composites ({len(routing_revealed_rows)})"))
    out.append(
        "Exact-fingerprint exceptions for pre-existing composites whose dead legacy slots "
        "previously masked them from the ratchet. Any main-key or damage change removes the "
        "exception and is checked normally.\n")
    out.append(table(["weapon", "mains", "per_warhead", "total"],
                     routing_revealed_rows))

    out.append(h2(f"FAIL 2 — FriendlyFire louder than the shot ({len(ff_rows)})"))
    if ff_rows:
        out.append(table(["weapon", "warhead", "ff_damage", "max_main"], ff_rows))
    else:
        out.append("None. ✅\n")

    out.append(h2(f"Review — high uniform stacks (informational, {len(review_rows)})"))
    if review_rows:
        out.append(f"Allowed, but {REVIEW_DMG}+ per-warhead x N is a big total "
                   "— confirm it is intended (not flattening residue).\n")
        out.append(table(["weapon", "mains", "per_warhead", "total"],
                         review_rows[:120]))
    else:
        out.append("None.\n")

    sys.stdout.write("\n".join(out) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
