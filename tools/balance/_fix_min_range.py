#!/usr/bin/env python3
"""_fix_min_range.py — apply MinRange audit fixes with maintainer exceptions.

Usage:
    python _fix_min_range.py --dry-run    # preview
    python _fix_min_range.py --confirm    # write YAML

The default rule is expected = round(Range / 25) * 5 (i.e. round(Range/5) to
nearest 5). Weapons in the exception list are left alone or forced to a
canonical value instead.
"""

from __future__ import annotations

import argparse
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import formula  # noqa: E402


def _parse_num(value: str | None) -> int | None:
    return formula.wdist_value(value)


def _expected(range_val: int) -> int:
    return round(range_val / 25.0) * 5


def _is_linear_pulse(name: str, resolved=None) -> bool:
    # Maintainer-confirmed linear pulse weapon: keep this and only this removed.
    return name.lower() == "naxdieglock"


def _is_disk_weapon(name: str) -> bool:
    lname = name.lower()
    return "ra2diskdrain" in lname or "ra2disksteal" in lname


def _should_skip(name: str, range_val: int, min_val: int, weapons: set[str]) -> bool:
    lname = name.lower()
    # superweapons / spawners / missiles
    if any(p in lname for p in ("spawner", "scud", "tacticalmissile", "fragment")):
        return True
    if range_val > 100_000:
        return True
    # meme/intentional numeric pairs
    if range_val == 11111 and min_val == 2222:
        return True
    if range_val == 4444 and min_val == 888:
        return True
    # elite / energized / E-variant weapons inherit base MinRange
    if "_elite" in lname or ".elite" in lname or "_energized" in lname:
        return True
    if name.endswith("E") and name[:-1] in weapons:
        return True
    return False


def _remove_weapon_field(editor, weapon: str, field: str) -> str:
    span = editor._block(weapon)
    if span is None:
        return f"weapon `{weapon}` not found"
    s, e = span
    for i in range(e - 1, s, -1):
        line = editor.lines[i]
        if line and line.strip().startswith(f"{field}:"):
            old = line.strip()
            del editor.lines[i]
            editor.dirty = True
            return f"{old} -> removed"
    return f"`{field}` not found in `{weapon}`"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="write changes to YAML")
    args = ap.parse_args()

    sys.path.insert(0, str(ROOT / "tools" / "audit"))
    from cameo_model import Model
    from apply_balance import YamlEditor

    model = Model()
    rs = model.rs
    weapon_names = set(rs.weapons.keys())

    change_count = 0
    skip_count = 0
    remove_count = 0
    unchanged = 0

    # cache editors by file path
    editors: dict[pathlib.Path, YamlEditor] = {}

    for name in sorted(rs.weapons.keys()):
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            continue
        range_val = _parse_num(resolved.get("Range"))
        min_val = _parse_num(resolved.get("MinRange"))
        if range_val is None or min_val is None:
            continue

        wnode = rs.weapon(name)
        if wnode is None:
            continue
        wfile = wnode.file
        if wfile is None:
            continue
        wpath = pathlib.Path(wfile)

        lname = name.lower()

        if _should_skip(name, range_val, min_val, weapon_names):
            skip_count += 1
            continue

        # Linear pulse projectiles: remove MinRange entirely
        if _is_linear_pulse(name, resolved):
            if wpath not in editors:
                editors[wpath] = YamlEditor(wpath)
            ed = editors[wpath]
            result = _remove_weapon_field(ed, name, "MinRange")
            print(f"LINEAR {name}: {result}")
            if "removed" in result:
                remove_count += 1
            continue

        # RA2DiskDrain / RA2DiskSteal: remove MinRange entirely
        if _is_disk_weapon(name):
            if wpath not in editors:
                editors[wpath] = YamlEditor(wpath)
            ed = editors[wpath]
            result = _remove_weapon_field(ed, name, "MinRange")
            print(f"REMOVE {name}: {result}")
            remove_count += 1
            continue

        expected = _expected(range_val)
        if min_val == expected:
            unchanged += 1
            continue

        if wpath not in editors:
            editors[wpath] = YamlEditor(wpath)
        ed = editors[wpath]
        result = ed.set_weapon_field(name, "MinRange", expected)
        print(f"FIX {name}: {result}")
        change_count += 1

    if args.confirm:
        for ed in editors.values():
            ed.save()
        print(f"\nSaved {len(editors)} file(s).")
    else:
        print(f"\nDRY RUN — no files written.")

    print(f"changes={change_count}, removes={remove_count}, skipped={skip_count}, unchanged={unchanged}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
