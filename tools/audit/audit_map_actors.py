#!/usr/bin/env python3
"""audit_map_actors.py - every actor placed on a map must exist in the rules.

A `.oramap` is a zip whose `map.yaml` lists placed actors:

    Actors:
        Actor0: hosp
            Owner: Neutral
            Location: 48,28

If a rename moves `hosp` and the map is not updated, the map still loads its
`Actors:` list and asks the ruleset for a type that is gone.  **The main menu is
unaffected** - the failure happens when that map is STARTED, so the boot gate is
blind to it and nobody notices until someone picks the map.

That is not hypothetical: `1e30a1cb9` repaired dangling `ra1_soviets_*` refs in
SEVEN maps after the `ad7c5e232` rename, and they were found by hand.  With ~450
renames still queued across the faction lanes, this needs a gate.

  M1 DANGLING   a map places an actor type the ruleset does not define
  M2 UNREADABLE a .oramap that cannot be opened or has no parsable map.yaml

Both are hard defects: ratchet 0.

Usage: python tools/audit/audit_map_actors.py [--list] [--map NAME]
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import miniyaml
from report import h1, h2, table

M1_BASELINE = 0
M2_BASELINE = 0

# Placed-actor values that are engine placeholders rather than real actor types.
ENGINE_PLACEHOLDERS = {"mpspawn", "waypoint", "camera"}

ACTOR_LINE = re.compile(r"^\t?Actor\d+:\s*(\S+)\s*$")


def map_actors(path):
    """{actor type: count} placed on one map, or None if unreadable."""
    try:
        with zipfile.ZipFile(path) as z:
            if "map.yaml" not in z.namelist():
                return None
            text = z.read("map.yaml").decode("utf-8", "replace")
    except Exception:
        return None
    out = collections.Counter()
    inside = False
    for line in text.splitlines():
        if line.startswith("Actors:"):
            inside = True
            continue
        if inside:
            # the section ends at the next top-level key
            if line and not line[0].isspace():
                inside = False
                continue
            m = ACTOR_LINE.match(line)
            if m:
                out[m.group(1).lower()] += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--map", default="")
    args = ap.parse_args()

    root = pathlib.Path(__file__).resolve().parents[2]
    rs = miniyaml.Ruleset(root)
    known = {a.lower() for a in rs.actors if not a.startswith("^")}
    known |= ENGINE_PLACEHOLDERS

    maps = sorted((root / "mods/cameo/maps").rglob("*.oramap"))
    dangling = collections.defaultdict(list)   # actor -> [map names]
    unreadable, scanned, placed = [], 0, 0

    for mp in maps:
        if args.map and args.map.lower() not in mp.name.lower():
            continue
        actors = map_actors(mp)
        if actors is None:
            unreadable.append(mp.name)
            continue
        scanned += 1
        for a, n in actors.items():
            placed += n
            if a not in known:
                dangling[a].append(mp.name)

    print(h1("audit_map_actors - every placed actor must exist in the rules"))
    n_refs = sum(len(v) for v in dangling.values())
    rows = [
        ["M1", "DANGLING (map places an actor the rules do not define)",
         str(n_refs), str(M1_BASELINE),
         "PASS" if n_refs <= M1_BASELINE else "FAIL"],
        ["M2", "UNREADABLE .oramap", str(len(unreadable)), str(M2_BASELINE),
         "PASS" if len(unreadable) <= M2_BASELINE else "FAIL"],
    ]
    print(table(["code", "check", "count", "ratchet", ""], rows))
    print(f"\n{scanned} map(s) scanned, {placed} placed actor(s), "
          f"{len(known)} known actor type(s).\n")

    if dangling:
        print(h2(f"M1 - dangling actor types ({len(dangling)} distinct)"))
        rows2 = [[f"`{a}`", str(len(v)), ", ".join(sorted(v)[:3])
                  + (" …" if len(v) > 3 else "")]
                 for a, v in sorted(dangling.items(), key=lambda kv: -len(kv[1]))]
        print(table(["actor type", "maps", "example maps"], rows2))
    if unreadable:
        print(h2("M2 - unreadable maps"))
        for n in unreadable:
            print(f"    {n}")

    failed = (n_refs > M1_BASELINE) + (len(unreadable) > M2_BASELINE)
    print(f"\n**{'PASS' if not failed else 'FAIL'}** - {n_refs} dangling "
          f"reference(s) across {len(dangling)} actor type(s).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
