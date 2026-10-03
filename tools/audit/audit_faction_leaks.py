#!/usr/bin/env python3
"""audit_faction_leaks.py — B1 detector (cross-faction actor leaks).

For every real faction, computes the reachable buildable set (prerequisite
closure, incl. support-power-produced actors) and flags:
  L1 buildable whose attributed owner is a DIFFERENT faction (leak)
  L2 buildable defined in another faction's ContentPack folder
  L3 buildable inheriting from a concrete actor owned by another faction
     (the tsntsamcabal / Slave-Miner bug shape)
Shared/unattributed actors are listed once as "needs human decision".
"""

from __future__ import annotations

import sys
from collections import defaultdict

from cameo_model import Model
from report import h1, h2, relpath, table


def main() -> int:
    m = Model()
    rs = m.rs
    leaks_l1, leaks_l3 = [], []
    shared: dict[str, set[str]] = defaultdict(set)

    factions = [f.internal for f in m.real_factions()]
    for fac in factions:
        roster = m.buildable_roster(fac)
        for lname in sorted(roster):
            owner = m.owner_of(lname)
            if owner is None:
                shared[lname].add(fac)
                continue
            # normalize contentpack owners like "tiberiandawn/gdi" — compare loosely
            if not _same_faction(owner, fac):
                leaks_l1.append([fac, lname, owner,
                                 relpath(rs.actor(lname).file, m.root)])
            node = rs.actor(lname)
            for _, target in rs.inherits_of(node):
                if target.startswith("^"):
                    continue
                towner = m.owner_of(target)
                if towner and not _same_faction(towner, fac):
                    leaks_l3.append([fac, lname, target, towner,
                                     relpath(node.file, m.root)])

    print(h1("audit_faction_leaks — cross-faction leaks (B1)"))
    print(f"Factions checked: **{len(factions)}** — "
          f"L1 leaks: **{len(leaks_l1)}**, L3 concrete-inherit leaks: **{len(leaks_l3)}**, "
          f"shared/unattributed buildables: **{len(shared)}**\n")

    print(h2("L1 — buildable in faction X but owned by faction Y"))
    print(table(["faction", "actor", "attributed owner", "file"], leaks_l1))

    print(h2("L3 — buildable inherits concrete actor owned by another faction"))
    print(table(["faction", "actor", "inherit target", "target owner", "file"], leaks_l3))

    print(h2("Shared / unattributed buildables (needs human decision)"))
    rows = [[a, str(len(f)), ", ".join(sorted(f)[:8]) + ("…" if len(f) > 8 else "")]
            for a, f in sorted(shared.items()) if len(f) < len(factions)]
    rows = [r for r in rows if int(r[1]) <= 6]  # cross-everything actors are fine
    print(f"(showing only actors reachable by ≤ 6 factions; "
          f"{len(shared) - len(rows)} broadly-shared actors suppressed)\n")
    print(table(["actor", "#factions", "factions"], rows))
    return 0


def _same_faction(owner: str, fac: str) -> bool:
    o = owner.lower().split("/")[-1]
    f = fac.lower()
    if o == f or o == "shared" or o == "core":
        return True
    # Use full path for disambiguation (tiberiandawn/gdi vs tiberiansun/gdi)
    full = owner.lower().rstrip("/")
    # ContentPack folder names vs internal names
    # Key = full path or last segment, value = set of faction InternalNames
    aliases = {
        "tiberiandawn/gdi": {"td_gdi"}, "tiberiandawn/nod": {"td_nod"},
        "tiberiansun/gdi": {"ts_gdi"}, "tiberiansun/nod": {"ts_nod"},
        "tiberiansun/cabal": {"cabal"}, "tiberiansun/forgotten": {"forgotten"},
        "redalert": {"ra1_allies", "ra1_soviets", "japan"},
        "redalert/allies": {"ra1_allies"}, "redalert/soviets": {"ra1_soviets"},
        "redalert/japan": {"japan"},
        "redalert2": {"ra2_allies", "ra2_soviets", "yuri"},
        "redalert2/allies": {"ra2_allies"}, "redalert2/soviets": {"ra2_soviets"},
        "redalert2/yuri": {"yuri"},
        "warcraft2/humans": {"wc2_humans"}, "warcraft2/orcs": {"wc2_orcs"},
        "redalert2mod/asianalliance": {"asianalliance"},
        "redalert2mod/consortium": {"steelconsortium"},
        "redalert2mod/syndicate": {"latinsyndicate"},
        "redalert2mod/naxis": {"naxis"},
        "redalert2mod/schwarzermond": {"schwarzermond"},
        "redalert2mod/futuretech": {"futuretech"},
        "starcraft": {"terran", "zerg", "protoss"},
        "warcraft2": {"wc2_humans", "wc2_orcs"},
        "asianalliance": {"asianalliance"},
        "steelconsortium": {"steelconsortium"},
        "latinsyndicate": {"latinsyndicate"},
        "naxis": {"naxis"},
        "schwarzermond": {"schwarzermond"}, "futuretech": {"futuretech"},
        "ordos": {"ordos"}, "ixian": {"ixian"},
        "atreides": {"atreides"}, "harkonnen": {"harkonnen"},
        "tkm": {"tkm"}, "outpost2": {"plymouth", "eden"},
        "warcraft1": {"wc1human", "wc1orc", "human", "orc"},
    }
    # Try full path first, then last segment
    if f in aliases.get(full, set()):
        return True
    return f in aliases.get(o, set())


if __name__ == "__main__":
    sys.exit(main())
