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
ORIGINAL_SOURCES = ("OpenRA Red Alert", "OpenRA Tiberian Dawn")

# LOWER-ONLY ratchets, set from this audit's own run.
O1_BASELINE = 12
O2_BASELINE = 15


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

    failed = len(o1) > O1_BASELINE or len(o2) > O2_BASELINE
    print(f"\nexit={1 if failed else 0}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
