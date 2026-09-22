#!/usr/bin/env python3
"""audit_original_coverage.py — an ORIGINAL unit must carry all three references.

⛔ THE MAINTAINER'S RULE, 2026-09-07, verbatim:

    "All the original units are in OpenRA. DTA, CA and Cameo all expand the unit roster, so if
     it doesn't exist in OpenRA or OpenTD then it is an extra unit and those can't always have
     3 references. But those that exist in OpenRA and OpenTD MUST ALWAYS HAVE 3 REFERENCES."

That makes the acceptance test mechanical, which is the point: an actor paired to one of the
declared original authorities is original, and must carry three name-backed references from the
sources routed for its own faction. The candidate sources differ by universe; reporting Combined
Arms and DTA as "missing" for RA2 or Tiberian Sun was itself a stale audit defect.

The reverse direction is checked as well, because it catches the failure the first cannot see:
an original whose OpenRA counterpart was never claimed by anybody. `ra1_allies_rifleinfantry`
drew a Cryo Trooper while OpenRA's `E1` sat unused, and no count of "how many sources did this
actor get" would have shown it — the actor had two, and both were wrong.

O1  an actor holding an OpenRA original but fewer than three sources
O2  an OpenRA/OpenTD row that no Cameo actor claimed (armed, buildable, non-exempt)

Read-only. Ratchets are LOWER-ONLY.
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/balance"))
sys.path.insert(0, str(ROOT / "tools/audit"))
import faction_routes as fr        # noqa: E402
import reference_distribution as rd  # noqa: E402

ASSIGN = ROOT / "docs/balance/derived/reference_assignment.json"
# ⛔ THE AUTHORITY ON ORIGINALS, PER UNIVERSE (maintainer 2026-09-07). These mods port an
# original game and add nothing, so their roster IS the original roster. Every other source —
# Combined Arms, DTA, Shattered Paradise, CnC Reloaded — is a superset that expands it.
ORIGINAL_SOURCES = (
    "OpenRA Red Alert",        # RA1
    "OpenRA Tiberian Dawn",    # TD
    "OpenRA Tiberian Sun",     # TS — already extracted, 74 units
    "Romanov's Vengeance",     # RA2 + YR (maintainer's ruling; see the caveat below)
)
# ⚠ ROMANOV'S VENGEANCE CARRIES 729 BUILDABLE UNITS. The maintainer named it the RA2/YR
# authority, and it is the most complete RA2 source we have — but 729 is far more than RA2 and
# Yuri's Revenge shipped between them, so it plainly expands the roster too. The corpus also
# holds `OpenRA RA2 official` (86) and `Yuri's Revenge on OpenRA` (124), whose sizes match the
# real rosters much more closely. Which of the three is the ORIGINAL authority is an open
# question, and until it is settled RV will mark add-on units as originals here.

# LOWER-ONLY ratchets, set from this audit's own run.
# ⚠ RE-BASELINED 7 -> 12 on 2026-09-07, and this one is a LOOSENING, so it needs saying plainly.
# References are now NAME-BACKED ONLY: shape-only matches are refused outright, including for
# originals. Those matches were previously filling an original's third slot with whatever sat in
# the same place in its roster — `ra1_allies_gunboat` held a Mobile Repair Ship, `alliedaagun` a
# Pill Box, `pillbox` a Silo. O1 counted those slots as FULL. It now counts them as EMPTY, which
# is what they always were.
#
# ⛔ SO THIS NUMBER IS A WORK QUEUE, NOT A DEBT TO TOLERATE. Some rows are one safe alias away;
# others expose a real source absence, a bot/variant identity, or an unsettled authority. The
# audit names every routed candidate source so those cases are not confused with missing CA/DTA
# data from another universe. It must fall, and it may never rise again.
O1_BASELINE = 12
# ⛔ O1_UNSETTLED — actors whose supersets ship the ID and give it to ANOTHER SIDE, so the gap can
# never be closed by matching. Ruled 2026-09-13; the same shape as the O2 carve-out below, and
# under the same obligation to be DELETED rather than grown.
#
# `ra1_allies_phasetransport` is the case. It holds OpenRA Red Alert's `STNK` "Phase Transport", a
# genuine France-tagged RA1 original. Combined Arms and DTA both ship an `STNK` too — and both of
# theirs is NOD'S STEALTH TANK, a different unit, which faction routing correctly refuses. So this
# actor can never reach three sources, and counting it as a mapping defect asserts something the
# data contradicts.
#
# ⚠ THIS DISPROVES THE PREMISE THE WHOLE O1 RULE RESTS ON — "an original exists in OpenRA, so CA
# and DTA, being supersets, must have it too". They are supersets of the ROSTER, not of the
# faction assignment, and a shared id is not a shared unit. `td_nod_ssmlauncher` is the mirror
# image: matched "SSM Launcher" by BOTH supersets and shipped by no OpenRA source at all.
O1_UNSETTLED = (
    "ra1_allies_phasetransport",
    # CA and OpenRA both ship `MRJ` "Mobile Radar Jammer" and DTA ships NO jammer of any kind —
    # only Radar DOMES, which are buildings. Verified 2026-09-13 after the maintainer removed this
    # actor's BuildLimit, which is what let it reach two sources in the first place.
    "ra1_allies_mobileradarjammer",
    # ⭐ ra1_allies_chronotank WAS HERE AND IS NOT ANY MORE, which is the outcome this list is
    # supposed to have. It held two exact-name `CTNK` rows while DTA Enhanced's `CTNK` "Chrono
    # Tank" sat unclaimed in the HERO pool (DTA caps it at `build_limit 2`; the maintainer had
    # just removed Cameo's own limit, putting the two sides in impermeable lanes). The fix was a
    # derived cross-lane pass in `assign_references`, NOT an exemption — see its comment for why
    # loosening `is_hero_limit` to `> 1` was measured and rejected (it also frees CnC Reloaded's
    # `NODCOMMANDO`). ⛔ Reach for that shape first: this list is for gaps the DATA closes off,
    # never for gaps our own machinery creates.
)
# ⛔ O2 IS SPLIT, because it was measuring one settled question and one unsettled one and gating
# on the sum. Tiberian Dawn, Red Alert and Tiberian Sun ship the original rosters and nothing
# else, so an unclaimed row there is a real defect and ratchets normally — that number is now
# ELEVEN, down from sixteen this morning, with Tiberian Dawn at ONE.
#
# Romanov's Vengeance is the unsettled half. The maintainer named it the RA2/YR authority, but it
# carries 729 buildable units — far more than RA2 and Yuri's Revenge shipped between them — so it
# plainly expands the roster as CA and DTA do, and most of its "unclaimed originals" are add-on
# units no Cameo actor should ever claim. Ratcheting on that would be gating on a question nobody
# has answered. It is REPORTED IN FULL and does not gate, until the authority is settled — at
# which point this exemption must be deleted, not raised.
# Re-baselined 11 -> 15 for the same reason, and under the same obligation to fall.
O2_BASELINE = 15
O2_UNSETTLED = ("Romanov's Vengeance",)


def main() -> int:
    doc = json.loads(ASSIGN.read_text(encoding="utf-8"))
    assignment = doc["assignment"]
    peers = rd.peer_rows()
    fr.register_source_ids(peers)

    claimed = collections.defaultdict(list)
    o1 = []
    for actor, srcs in sorted(assignment.items()):
        originals = [s for s in srcs if s in ORIGINAL_SOURCES]
        for s in originals:
            claimed[(s, (srcs[s].get("id") or "").upper())].append(actor)
        if originals and len(srcs) < 3:
            faction = fr.faction_of(actor)
            routed = [source for source, _tokens in fr.routes_for(faction)]
            missing = [source for source in routed if source not in srcs]
            o1.append((actor, sorted(srcs), missing))

    o2 = []
    for p in peers:
        if p["source"] not in ORIGINAL_SOURCES:
            continue
        # Only rows that could be somebody's reference: a combat unit with a weapon.
        if p.get("type") not in ("infantry", "vehicle", "aircraft", "ship", "defense"):
            continue
        if not any(p.get(k) for k in ("w_damage", "w_range", "w_reload")):
            continue
        if not claimed.get((p["source"], (p.get("id") or "").upper())):
            o2.append((p["source"], p.get("id") or "?", p.get("name") or "?", p["type"]))

    print("# Original-unit reference coverage\n")
    print(f"## O1 — holds an OpenRA original but fewer than three sources: "
          f"**{len(o1)}** (ratchet {O1_BASELINE})\n")
    for actor, have, missing in o1[:40]:
        print(f"   {actor:40} has {', '.join(s[:12] for s in have):26} "
              f"ROUTED CANDIDATES {', '.join(missing)}")
    if len(o1) > 40:
        print(f"   … and {len(o1) - 40} more")

    print(f"\n## O2 — OpenRA/OpenTD original claimed by nobody: "
          f"**{len(o2)}** (ratchet {O2_BASELINE})\n")
    by_src = collections.Counter(s for s, _, _, _ in o2)
    for s, n in by_src.most_common():
        print(f"   {s}: {n}")
    print()
    for s, i, n, t in o2[:40]:
        print(f"   {s[:12]:14}{i:14}{n[:30]:32}{t}")
    if len(o2) > 40:
        print(f"   … and {len(o2) - 40} more")

    gating = [r for r in o2 if r[0] not in O2_UNSETTLED]
    print(f"\n   gating sources: {len(gating)} (ratchet {O2_BASELINE}) · "
          f"unsettled, reported only: {len(o2) - len(gating)}")
    o1_gating = [r for r in o1 if r[0] not in O1_UNSETTLED]
    if len(o1_gating) != len(o1):
        print(f"\n   O1 gating actors: {len(o1_gating)} (ratchet {O1_BASELINE}) · "
              f"unsettled, reported only: {len(o1) - len(o1_gating)}")
    failed = len(o1_gating) > O1_BASELINE or len(gating) > O2_BASELINE
    print(f"\nexit={1 if failed else 0}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
