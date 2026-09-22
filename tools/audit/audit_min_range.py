#!/usr/bin/env python3
"""audit_min_range.py — DESIGN.md minimum-range detector.

Every weapon that declares a MinRange must satisfy:

    MinRange = round(Range / 5) rounded to the nearest multiple of 5.

Equivalent calculation: expected = round(Range / 25.0) * 5.
"""

from __future__ import annotations

import pathlib
import sys

from cameo_model import Model
from report import h1, h2, table

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import formula  # noqa: E402


def parse_number(value: str | None) -> int | None:
    return formula.wdist_value(value)


def expected_min_range(range_val: int) -> int:
    return round(range_val / 25.0) * 5


def _is_exempt(name: str, range_val: int, min_val: int, weapons: set[str]) -> bool:
    lname = name.lower()
    # superweapons / spawners / missiles / fragment submunitions
    if any(p in lname for p in ("spawner", "scud", "tacticalmissile", "fragment")):
        return True
    if range_val > 100_000:
        return True
    # linear-pulse impact warheads that have their MinRange intentionally removed
    if any(p in lname for p in ("waveartilleryimpact", "waveturretimpact", "lurkerspinesimpact", "naxdieglock")):
        return True
    # meme / intentional numeric pairs
    if range_val == 11111 and min_val == 2222:
        return True
    if range_val == 4444 and min_val == 888:
        return True
    # Ruling 6 (Claude-Local, 2026-09-06): DebrisMissile is a death-throe
    # weapon — its only consumer is harkonnen_missiletank's
    # FireProjectilesOnDeath@missiles, so no actor ever aims it and a
    # MinRange can never gate an attack order.
    if "debrismissile" in lname:
        return True
    # elite / energized / E-variant weapons inherit base MinRange
    if "_elite" in lname or ".elite" in lname or "_energized" in lname:
        return True
    if name.endswith("E") and name[:-1] in weapons:
        return True
    return False


def main() -> int:
    m = Model()
    rs = m.rs
    weapon_names = set(rs.weapons.keys())

    violations: list[list[str]] = []

    for name, node in rs.weapons.items():
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            continue
        range_val = parse_number(resolved.get("Range"))
        min_val = parse_number(resolved.get("MinRange"))
        if range_val is None or min_val is None:
            continue
        expected = expected_min_range(range_val)
        if min_val != expected and not _is_exempt(name, range_val, min_val, weapon_names):
            violations.append([name, str(range_val), str(min_val), str(expected)])

    print(h1("Minimum range audit"))

    if violations:
        print(h2("Weapons with MinRange != round(Range/5) to nearest step of 5"))
        print(table(["Weapon", "Range", "MinRange", "Expected MinRange"], violations))
        return 1

    print("All weapon minimum ranges are consistent with Range/5.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
