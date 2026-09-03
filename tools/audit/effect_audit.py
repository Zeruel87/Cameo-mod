#!/usr/bin/env python3
"""Audit: list all weapon effect warheads and detect duplicate DamagesConcrete.

Usage: python tools/audit/effect_audit.py
Output: tools/audit/all_warheads.json, tools/audit/duplicate_concrete.json
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from cameo_model import Model
from miniyaml import Node


def cval(node: Node, key: str):
    for c in node.children:
        if c.key == key:
            return c.value
    return None


def collect_warheads(node: Node):
    warheads = []
    for c in node.children:
        if c.key.startswith("Warhead@"):
            wtype = c.value
            damage = cval(c, "Damage")
            warheads.append((c.key, wtype, damage, str(node.key)))
    return warheads


def main():
    m = Model()
    weapons = sorted(m.rs.weapons.keys())

    out = {}
    dups = {}
    for w in weapons:
        resolved = m.rs.resolve_weapon(w)
        if resolved is None:
            continue
        warheads = collect_warheads(resolved)
        out[w] = warheads
        concrete_keys = [wh for wh in warheads if wh[1] == "DamagesConcrete"]
        if len(concrete_keys) > 1:
            dups[w] = concrete_keys

    out_dir = pathlib.Path(__file__).resolve().parent
    with open(out_dir / "all_warheads.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, sort_keys=True)

    with open(out_dir / "duplicate_concrete.json", "w", encoding="utf-8") as f:
        json.dump(dups, f, indent=1, ensure_ascii=False, sort_keys=True)

    print(f"Scanned {len(out)} weapons.")
    print(f"Weapons with >1 DamagesConcrete warhead: {len(dups)}")
    if dups:
        for w, keys in sorted(dups.items()):
            print(f"  {w}: {keys}")


if __name__ == "__main__":
    main()
