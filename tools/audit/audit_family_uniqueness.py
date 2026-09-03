#!/usr/bin/env python3
"""audit_family_uniqueness.py — no two warhead families may feel the same.

    python tools/audit/audit_family_uniqueness.py

Maintainer 2026-08-22: *"every family needs to be unique as fuck! everything needs their own
unique spread and falloff shape."*

⛔ WHY THIS EXISTS. Before the physics shapes landed, 103 of 117 families shared just THREE
falloff curves — one per LEVEL — so the blast shape encoded how BIG a weapon was and never what
it WAS: 23 different Heavy families sat at Spread 800 / radius 4000 / `100,50,25,10,5,0`, from
Melee to CannonNuke. Even after the first pass 13 families were still pairwise identical, because
every pinpoint weapon had collapsed onto `100, 0` at one of a handful of radii.

WHAT IT CHECKS, on the RESOLVED `^Warhead_*` templates rather than on the generator, so a hand
edit to weapons.yaml is caught as well as a generator change:

  1. no two families share BOTH a radius and a curve at the same level;
  2. every family's blast radius is (len(Falloff) - 1) x Spread, the engine's own arithmetic
     (`AreaDamageWarhead.cs:143` lays the points at 0, S, 2S ... (N-1)S).

Sharing a CURVE alone is fine and expected — a chem cannon and a chem missile are the same
chemistry at different sizes; what must never happen is two families that are indistinguishable.

EXIT CODE: 1 on any collision.
"""
from __future__ import annotations

import collections
import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):          # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8")

YAML = pathlib.Path("mods/cameo/weapons/weapons.yaml")
HEADER_RE = re.compile(r"^\^Warhead_(?P<family>\w+?)_(?P<level>Light|Medium|Heavy|Super|Trace)\b")

# Variants hand-authored for one faction (^Warhead_Demolition_Heavy_D2K_Orni and friends) are
# deliberate one-offs, not families, and are matched by the trailing segment after the level.
VARIANT_RE = re.compile(r"^\^Warhead_\w+?_(?:Light|Medium|Heavy|Super|Trace)_\w+")


def shapes() -> dict[tuple[str, str], tuple[int, str]]:
    """{(family, level): (radius, curve)} from the MAIN warhead of each template.

    ⚠ Parse per WARHEAD BLOCK, not per template. A template holds three warheads — the main, the
    `_Percentage` twin at half the spread and the `_ExtraDamage` chip with its own curve — so
    scanning the template for "the first Spread" and "the first Falloff" independently pairs
    numbers that belong to different warheads. That bug reported ten collisions that did not
    exist, at radii no family actually has.
    """
    out: dict[tuple[str, str], tuple[int, str]] = {}
    cur = None                      # (family, level) of the template being read
    wh = None                       # name of the warhead child being read
    spread = falloff = None

    def flush():
        nonlocal spread, falloff
        if cur and wh and spread is not None and falloff is not None and cur not in out:
            out[cur] = ((len(falloff.split(",")) - 1) * spread, falloff)
        spread = falloff = None

    for line in YAML.read_text(encoding="utf-8", errors="replace").splitlines():
        if line and not line[0].isspace():                      # a top-level node
            flush()
            m = HEADER_RE.match(line)
            cur = None if (m is None or VARIANT_RE.match(line)) else (m["family"], m["level"])
            wh = None
            continue
        if cur is None:
            continue
        stripped = line.strip()
        if stripped.startswith("Warhead@"):                     # a new warhead child
            flush()
            name = stripped.split(":")[0]
            # Only the MAIN warhead defines the family's shape.
            wh = None if any(t in name for t in ("Percentage", "ExtraDamage", "Concrete",
                                                 "Effect", "ShieldHit", "Glow", "Smudge")) else name
            continue
        if wh is None:
            continue
        if stripped.startswith("Spread:"):
            try:
                spread = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                spread = None
        elif stripped.startswith("Falloff:"):
            falloff = ",".join(p.strip() for p in stripped.split(":", 1)[1].split(","))
    flush()
    return out


def main() -> int:
    found = shapes()
    by_level: dict[str, dict] = collections.defaultdict(lambda: collections.defaultdict(list))
    for (family, level), shape in found.items():
        by_level[level][shape].append(family)

    print(f"# audit_family_uniqueness — {len(found)} family/level templates\n")
    collisions = 0
    for level in sorted(by_level):
        dupes = {k: v for k, v in by_level[level].items() if len(v) > 1}
        n = len(by_level[level])
        print(f"  {level:8s} {n:3d} distinct shapes"
              + (f"   ⚠ {len(dupes)} COLLISION(S)" if dupes else "   OK"))
        for (radius, curve), fams in dupes.items():
            collisions += 1
            print(f"      radius {radius:6d}  {curve:34s} -> {', '.join(sorted(fams))}")

    if collisions:
        print(f"\nFAIL {collisions} shape collision(s) — two families are indistinguishable.")
        print("Give one of them its own radius or curve in `PHYSICS_SHAPES` "
              "(tools/balance/gen_weapon_template.py), then `splice_templates.py --all`.")
        return 1

    print("\nOK — no two families share both a radius and a curve at any level.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
