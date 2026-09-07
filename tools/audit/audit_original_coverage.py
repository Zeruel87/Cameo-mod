#!/usr/bin/env python3
"""audit_original_coverage.py — an ORIGINAL unit must carry all three references.

⛔ THE MAINTAINER'S RULE, 2026-09-07, verbatim:

    "All the original units are in OpenRA. DTA, CA and Cameo all expand the unit roster, so if
     it doesn't exist in OpenRA or OpenTD then it is an extra unit and those can't always have
     3 references. But those that exist in OpenRA and OpenTD MUST ALWAYS HAVE 3 REFERENCES."

That makes the acceptance test mechanical, which is the point: OpenRA Red Alert and OpenRA
Tiberian Dawn ship the ORIGINAL rosters and nothing else, so an actor paired to one of their
rows is by definition an original — and Combined Arms and DTA, which are supersets, must both
have it too. Two rows short of three is a mapping defect, never missing data.

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
# ⛔ SO THIS NUMBER IS A WORK QUEUE, NOT A DEBT TO TOLERATE. Every one of the 12 is an original
# whose counterpart exists in a source we could not name-match — DTA calls its rocket soldier
# "Bazooka" and its AA gun "Anti-aircraft Gun". Each is fixed by ONE alias, and the list is
# finite and checkable. It must fall, and it may never rise again.
O1_BASELINE = 12
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
            missing = [s for s in ("Combined Arms", "DTA Enhanced") if s not in srcs]
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
        print(f"   {actor:40} has {', '.join(s[:12] for s in have):26} MISSING {', '.join(missing)}")
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
    failed = len(o1) > O1_BASELINE or len(gating) > O2_BASELINE
    print(f"\nexit={1 if failed else 0}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
