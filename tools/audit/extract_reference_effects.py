#!/usr/bin/env python3
"""extract_reference_effects.py - the CANONICAL visual+sound pairings, from the source.

The upstream OpenRA mods ship inside `engine/mods/` (d2k, cnc, ra, ts). Each is the
authoritative record of which explosion sprite goes with which sound **in its own game**,
because that is how the original shipped.

This reads them and prints the pairing table, so `docs/design/EFFECT_SOUND_TEMPLATES.md`
can be built from measurement rather than taste.

⛔ THE RULE THIS EXISTS TO ENFORCE: **never pair a visual from one game with a sound from
another.** The tell is the file extension and the naming:

    d2k   EXPLSML1.WAV, EXPLMD2.WAV, EXPLLG3.WAV      (uppercase .WAV, EXPL* family)
    cnc   xplos.aud, xplobig4.aud, flamer2.aud        (.aud)
    ra    kaboom12.aud, firebl3.aud, splash9.aud      (.aud)
    ts    (see the table)

That is not academic. `D2K_Rocket_Trooper` currently pairs the D2k sprite
`d2k_tiny_explosion` with **`xplobig4.aud`**, which this tool shows is Tiberian Dawn's
sound for `big_frag` / `med_frag` / `small_poof`. A big TD explosion sound on a tiny
Dune sprite - which is exactly what the maintainer heard.

Usage:
  python tools/audit/extract_reference_effects.py            # table
  python tools/audit/extract_reference_effects.py --json     # machine-readable
  python tools/audit/extract_reference_effects.py --mod d2k
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

MODS = ("d2k", "cnc", "ra", "ts")


def pairs_for(root: pathlib.Path):
    """[(visual, sound)] in file order, pairing each Explosions: with the ImpactSounds:
    that follows it inside the same warhead node."""
    files = sorted(set(list(root.rglob("weapons*.yaml"))
                       + list((root / "weapons").glob("*.yaml"))))
    out, cur = [], None
    for f in files:
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if s.startswith("Explosions:"):
                cur = s.split(":", 1)[1].strip()
            elif s.startswith("ImpactSounds:") and cur:
                out.append((cur, s.split(":", 1)[1].strip()))
                cur = None
            elif s and not line[0].isspace() and s.endswith(":"):
                cur = None          # a new top-level weapon ends the pending visual
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--mod", default="", choices=("",) + MODS)
    args = ap.parse_args()

    base = pathlib.Path(__file__).resolve().parents[2] / "engine/mods"
    if not base.exists():
        print("engine/mods not found - the engine is gitignored and must be built "
              "(`make.cmd all`). Nothing to extract.", file=sys.stderr)
        return 2

    result = {}
    for mod in ([args.mod] if args.mod else MODS):
        root = base / mod
        if not root.exists():
            continue
        # dict() keeps the LAST pairing for a repeated visual; collect all first so a
        # visual used with two sounds inside one mod is visible rather than hidden.
        allp = pairs_for(root)
        byvis = {}
        for v, s in allp:
            byvis.setdefault(v, []).append(s)
        result[mod] = {v: sorted(set(s)) for v, s in byvis.items()}

    if args.json:
        print(json.dumps(result, indent=1, sort_keys=True))
        return 0

    for mod, table in result.items():
        conflicted = {v: s for v, s in table.items() if len(s) > 1}
        print(f"\n=== {mod}  -  {len(table)} visuals, "
              f"{len(conflicted)} used with more than one sound")
        for v, s in sorted(table.items()):
            mark = "  <-- AMBIGUOUS" if len(s) > 1 else ""
            print(f"    {v:26s} {', '.join(s)}{mark}")
    print("\nPair a visual only with a sound from ITS OWN mod. "
          "Cross-game pairing is the defect this table exists to prevent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
