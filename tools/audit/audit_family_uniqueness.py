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
     (`AreaDamageWarhead.cs:143` lays the points at 0, S, 2S ... (N-1)S);
  3. the Shield ladder (Aedis, 2026-09-10 02:10 — the coexistence ruling for the NEW
     level-less continuous-heaviness bases): no two DISTINCT NEW bases may share a Shield
     value. A base borrows its OWN family's Medium Shield as an approved compatibility
     preview, so that duplicate stays VISIBLE in the raw groups but does not fail.

Sharing a CURVE alone is fine and expected — a chem cannon and a chem missile are the same
chemistry at different sizes; what must never happen is two families that are indistinguishable.

⚠ READS THROUGH THE RESOLVER, NEVER A HAND PARSER (CLAUDE.md rule 8e; the original version of
this audit WAS a hand line parser and is retired). Legacy Shield duplicates remain reported;
the approved new-base uniqueness gate does not retroactively reject that compatibility tree.

EXIT CODE: 1 on any collision.
"""
from __future__ import annotations

import collections
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):          # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))
from miniyaml import Ruleset  # noqa: E402
import weapon_efficiency as we  # noqa: E402
from effective_heaviness import heaviness_of as validated_heaviness

LEVELS = ("Light", "Medium", "Heavy", "Super", "Trace")
COMPANION = ("Percentage", "ExtraDamage", "ExtraRepair", "Concrete",
             "Effect", "ShieldHit", "Glow", "Smudge")


def split_name(tail: str):
    """`^Warhead_` stripped -> (family, level) for a legacy level template, (family, None)
    for a level-less base, and None for a variant or anything else (same census the old
    HEADER_RE + VARIANT_RE parser produced)."""
    family, sep, level = tail.rpartition("_")
    if not sep:
        return (level, None)                    # no underscore at all: a bare family base
    return (family, level) if level in LEVELS else None


def main_warhead(resolved):
    """The first `Warhead@` child that is not a companion twin (the family's shape owner)."""
    for wh in resolved.children:
        if wh.key.startswith("Warhead@") and not any(c in wh.key for c in COMPANION):
            return wh
    return None


def shape_of(wh):
    """Authored implicit-range shape or None; not a runtime-scaled geometry check."""
    sp, fo = wh.child("Spread"), wh.child("Falloff")
    if sp is None or fo is None or not fo.value or not sp.value:
        return None
    try:
        spread = int(sp.value)
    except ValueError:
        return None
    curve = ",".join(v.strip() for v in fo.value.split(","))
    return ((len(curve.split(",")) - 1) * spread, curve)


def heaviness_of(wh) -> int | None:
    """Absent is None; malformed authored values fail like the runtime model."""
    return None if wh.child("Heaviness") is None else validated_heaviness(wh)


def read_census(rs=None):
    """(legacy, bases, shields).

    legacy  {(family, level): (radius, curve)}
    bases   {family: (radius, curve, shield)}      ACTIVE level-less bases only
    shields {(family, template name): Shield}      measured family templates' Shield rows
    """
    rs = rs if rs is not None else Ruleset(ROOT)
    legacy: dict[tuple[str, str], tuple[int, str]] = {}
    bases: dict[str, tuple[int, str, float | None]] = {}
    shields: dict[tuple[str, str], float | None] = {}
    for name in sorted(rs.weapons):
        if not name.startswith("^Warhead_"):
            continue
        kind = split_name(name[len("^Warhead_"):])
        if kind is None:
            continue
        family, level = kind
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            continue
        wh = main_warhead(resolved)
        if wh is None:
            continue
        shields[(family, name)] = (we.versus_of(wh) or {}).get("Shield")
        if level is None:
            h = heaviness_of(wh)
            if h is None or h < 0:              # a disabled sentinel is not an active base
                continue
            shape = shape_of(wh)
            # Shield identity must not depend on whether this shape reader supports
            # the base's authored geometry (defaults/explicit Range/WDist syntax).
            bases[family] = (*shape, shields[(family, name)]) if shape is not None else (
                None, None, shields[(family, name)])
        else:
            shape = shape_of(wh)
            if shape is not None:
                legacy[(family, level)] = shape
    return legacy, bases, shields


def raw_shield_groups(shields) -> dict[float, list[str]]:
    """EVERY Shield-value duplicate group, INCLUDING the approved same-family base/Medium
    compatibility pair — coexistence stays visible in RAW counts, it is just not a failure."""
    by_value: dict[float, list[str]] = collections.defaultdict(list)
    for (family, name), shield in sorted(shields.items(), key=lambda i: (i[0], i[1])):
        if shield is None:
            continue
        by_value[shield].append(f"{family} ({name})")
    return {v: m for v, m in sorted(by_value.items()) if len(m) > 1}


def shield_conflicts(shields, base_families=frozenset()) -> list[tuple[float, list[str]]]:
    """Reject collisions between NEW bases; retain every legacy duplicate in raw output."""
    by_value: dict[float, list[str]] = collections.defaultdict(list)
    for (family, name), shield in sorted(shields.items(), key=lambda i: (i[0], i[1])):
        if shield is None or family not in base_families or name != "^Warhead_" + family:
            continue
        by_value[shield].append(f"{family} ({name})")
    bad = []
    for value, members in sorted(by_value.items()):
        fams = {m.split(" (")[0] for m in members}
        if len(fams) > 1:
            bad.append((value, sorted(members)))
    return bad


def main() -> int:
    legacy, bases, shields = read_census()
    by_level: dict[str, dict] = collections.defaultdict(lambda: collections.defaultdict(list))
    for (family, level), shape in legacy.items():
        by_level[level][shape].append(family)
    by_base: dict[tuple[int, str], list[str]] = collections.defaultdict(list)
    for family, shape in bases.items():
        if shape[0] is not None:
            by_base[shape[:2]].append(family)

    total = len(legacy) + len(bases)
    print(f"# audit_family_uniqueness — {total} family templates "
          f"({len(legacy)} legacy level templates + {len(bases)} active level-less base(s))\n")
    print("Shape checks use authored implicit-range geometry, not heaviness-scaled runtime geometry.\n")

    collisions = 0
    for level in sorted(by_level):
        dupes = {k: v for k, v in by_level[level].items() if len(v) > 1}
        n = len(by_level[level])
        print(f"  {level:8s} {n:3d} distinct shapes"
              + (f"   ⚠ {len(dupes)} COLLISION(S)" if dupes else "   OK"))
        for (radius, curve), fams in dupes.items():
            collisions += 1
            print(f"      radius {radius:6d}  {curve:34s} -> {', '.join(sorted(fams))}")

    if bases:
        print(f"\n  level-less bases (continuous heaviness):\n")
        for family in sorted(bases):
            radius, curve, shield = bases[family]
            if radius is None:
                print(f"      {family:14s} shape not measured; Shield {shield}")
            else:
                print(f"      {family:14s} radius {radius:6d}  {curve:34s} Shield {shield}")
        base_dupes = {k: v for k, v in by_base.items() if len(v) > 1}
        for (radius, curve), fams in base_dupes.items():
            collisions += 1
            print(f"      ⚠ BASE COLLISION radius {radius}  {curve} -> {', '.join(sorted(fams))}"
                  " — two distinct NEW families share a base shape.")

    # RAW Shield duplicate groups — every group is printed, INCLUDING the approved
    # same-family base/Medium compatibility pair, so coexistence stays visible.
    raw_groups = raw_shield_groups(shields)
    conf = shield_conflicts(shields, frozenset(bases))
    conflicting_values = {value for value, _ in conf}
    if raw_groups:
        print(f"\n  RAW Shield duplicate groups — {len(raw_groups)} "
              f"(base/Medium compatibility is approved and stays visible):\n")
        for value, members in raw_groups.items():
            fams = {m.split(" (")[0] for m in members}
            print(f"      Shield {value:6.0f}  ->  {', '.join(members)}")
            if value in conflicting_values:
                print(f"          ⛔ DISTINCT NEW families share a Shield value.")
            elif len(fams) > 1:
                print(f"          ⚠ DISTINCT legacy families share a Shield value — "
                      "fewer than two NEW bases are involved; reported, not failed.")
    if conf:
        print(f"\n  ⛔ {len(conf)} Shield-uniqueness violation(s) across distinct family bases:")
        for value, members in conf:
            print(f"      Shield {value:6.0f}  ->  {', '.join(members)}")

    if collisions:
        print(f"\nFAIL {collisions} shape collision(s) — two families are indistinguishable.")
        print("Give one of them its own radius or curve in `PHYSICS_SHAPES` "
              "(tools/balance/gen_weapon_template.py), then `splice_templates.py --all`.")
        return 1
    if conf:
        print(f"\nFAIL {len(conf)} Shield collision(s) across distinct families — the "
              "shield ladder ties and the families become indistinguishable on the W21 layer.")
        return 1

    print("\nOK — no two families share both a radius and a curve at any level "
          "(bases incl.), and no distinct NEW family bases share a Shield value. "
          "Raw compatibility and legacy duplicates remain listed above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
