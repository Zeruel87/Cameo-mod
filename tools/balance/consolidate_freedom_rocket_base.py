#!/usr/bin/env python3
"""Fold only the normal Freedom Rocket's duplicate MissileAP profile.

The normal weapon's two mains have identical resolved contracts and exactly
representable folded percentage damage. Its elite descendant must remain split:
360000 flat damage cannot encode the existing 6000 folded units with one integer
PercentageScale. The converter therefore moves the compatibility inheritance to
the elite child and pins its original canonical scale before folding the parent.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from audit_three_way_split import main_warheads  # noqa: E402
from consolidate_compatibility_profiles import flat_nodes, fingerprint  # noqa: E402
from consolidate_reviewed_weapon_roots import block_bounds  # noqa: E402
from miniyaml import Ruleset  # noqa: E402
import percentage_damage as pd  # noqa: E402


BASE = "RA2FreedomRocket"
ELITE = "RA2FreedomRocket_elite"
CANONICAL = "MissileAP_Medium"
COMPATIBILITY = "MissileAP_MediumFlatCompatibility"
SELECTED = {CANONICAL, COMPATIBILITY}
ELITE_MAIN_ORDER = [COMPATIBILITY, CANONICAL]
NONSELECTED_HASHES = {
    BASE: "c5031b664b821532fed6a26aa9f60a8099a3b4af5dc821796c195a925eddb004",
    ELITE: "8c378fcd788cad156d930f1381d7766397aa243d30cf1b3e7c104112b12c769f",
}


def descendants(rs: Ruleset, root: str) -> set[str]:
    direct: dict[str, set[str]] = collections.defaultdict(set)
    for name, node in rs.weapons.items():
        for _, parent in rs.inherits_of(node):
            if parent in rs.weapons:
                direct[parent].add(name)
    seen: set[str] = set()
    stack = list(direct[root])
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        stack.extend(direct[name])
    return {name for name in seen if not name.startswith("^")}


def node_payload(node):
    return [node.key, node.value, [node_payload(child) for child in node.children]]


def resolved_hash(rs: Ruleset, name: str) -> str:
    resolved = rs.resolve_weapon(name)
    if resolved is None:
        raise RuntimeError(f"{name}: missing resolved weapon")
    excluded = {f"Warhead@{key}" for key in SELECTED}
    payload = [node_payload(child) for child in resolved.children
               if child.key not in excluded]
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def damage_scale(node) -> tuple[int, int]:
    return (
        int(str(node.get("Damage") or 0)),
        int(str(node.get("PercentageScale") or 0)),
    )


def folded_units(resolved) -> int:
    return sum(
        int(app["runtime_units"])
        for app in pd.percentage_applications(resolved, 200_000)
        if app["tag"] in SELECTED
    )


def inspect(rs: Ruleset) -> bool:
    if descendants(rs, BASE) != {ELITE}:
        raise RuntimeError(f"{BASE}: descendant closure changed")

    base = rs.resolve_weapon(BASE)
    elite = rs.resolve_weapon(ELITE)
    base_nodes = flat_nodes(base)
    elite_nodes = flat_nodes(elite)
    base_mains = set(main_warheads(base))
    elite_main_order = main_warheads(elite)
    elite_mains = set(elite_main_order)

    baseline = base_mains == SELECTED
    applied = base_mains == {CANONICAL}
    if not baseline and not applied:
        raise RuntimeError(f"{BASE}: unexpected mains {sorted(base_mains)}")
    if elite_mains != SELECTED:
        raise RuntimeError(f"{ELITE}: must retain both mains, found {sorted(elite_mains)}")
    if elite_main_order != ELITE_MAIN_ORDER:
        raise RuntimeError(
            f"{ELITE}: main execution order changed: {elite_main_order}")

    if baseline:
        if damage_scale(base_nodes[COMPATIBILITY]) != (120000, 0):
            raise RuntimeError(f"{BASE}: compatibility source changed")
        if damage_scale(base_nodes[CANONICAL]) != (60000, 10000):
            raise RuntimeError(f"{BASE}: canonical source changed")
        if fingerprint(base_nodes[COMPATIBILITY]) != fingerprint(base_nodes[CANONICAL]):
            raise RuntimeError(f"{BASE}: selected profiles are no longer identical")
    elif damage_scale(base_nodes[CANONICAL]) != (180000, 3333):
        raise RuntimeError(f"{BASE}: folded destination changed")

    if damage_scale(elite_nodes[COMPATIBILITY]) != (240000, 0):
        raise RuntimeError(f"{ELITE}: compatibility branch changed")
    if damage_scale(elite_nodes[CANONICAL]) != (120000, 10000):
        raise RuntimeError(f"{ELITE}: canonical branch changed")
    if fingerprint(elite_nodes[COMPATIBILITY]) != fingerprint(elite_nodes[CANONICAL]):
        raise RuntimeError(f"{ELITE}: selected profiles are no longer identical")

    if folded_units(base) != 3000 or folded_units(elite) != 6000:
        raise RuntimeError("Freedom Rocket folded percentage units changed")
    for name, expected in NONSELECTED_HASHES.items():
        if resolved_hash(rs, name) != expected:
            raise RuntimeError(f"{name}: non-selected behavior changed")
    return applied


def node_bounds(lines: list[str], weapon: str, key: str) -> tuple[int, int]:
    start, end = block_bounds(lines, weapon)
    pattern = re.compile(r"^\tWarhead@" + re.escape(key) + r":")
    rows = [i for i in range(start + 1, end) if pattern.match(lines[i])]
    if len(rows) != 1:
        raise RuntimeError(f"{weapon}: expected one Warhead@{key}")
    first = rows[0]
    last = end
    for i in range(first + 1, end):
        if lines[i].startswith("\t") and not lines[i].startswith("\t\t") \
                and lines[i].strip():
            last = i
            break
    return first, last


def set_field(lines: list[str], weapon: str, key: str, field: str, value: int) -> None:
    first, last = node_bounds(lines, weapon, key)
    rows = [i for i in range(first + 1, last)
            if lines[i].startswith(f"\t\t{field}:")]
    if len(rows) > 1:
        raise RuntimeError(f"{weapon}: duplicate {field} in Warhead@{key}")
    if rows:
        lines[rows[0]] = f"\t\t{field}: {value}\n"
    else:
        lines.insert(last, f"\t\t{field}: {value}\n")


def remove_exact(lines: list[str], weapon: str, exact: str) -> None:
    start, end = block_bounds(lines, weapon)
    rows = [i for i in range(start + 1, end)
            if lines[i].rstrip("\r\n") == exact]
    if len(rows) != 1:
        raise RuntimeError(f"{weapon}: expected one {exact!r}")
    del lines[rows[0]]


def remove_node(lines: list[str], weapon: str, key: str) -> None:
    first, last = node_bounds(lines, weapon, key)
    del lines[first:last]


def apply() -> None:
    rs = Ruleset(ROOT)
    if inspect(rs):
        return
    local = rs.weapon(BASE)
    path = pathlib.Path(local.file)
    lines = path.read_text(encoding="utf-8-sig").splitlines(True)

    remove_exact(lines, BASE,
                 "\tInherits@roleflat: ^Compatibility_MissileAP_MediumFlat")
    set_field(lines, BASE, CANONICAL, "Damage", 180000)
    set_field(lines, BASE, CANONICAL, "PercentageScale", 3333)
    remove_node(lines, BASE, COMPATIBILITY)

    start, end = block_bounds(lines, ELITE)
    marker = "\tInherits: RA2FreedomRocket"
    rows = [i for i in range(start + 1, end)
            if lines[i].rstrip("\r\n") == marker]
    if len(rows) != 1:
        raise RuntimeError(f"{ELITE}: expected one parent inherit")
    lines.insert(rows[0],
                 "\tInherits@roleflat: ^Compatibility_MissileAP_MediumFlat\n")
    set_field(lines, ELITE, CANONICAL, "PercentageScale", 10000)

    path.write_text("".join(lines), encoding="utf-8", newline="\n")
    if not inspect(Ruleset(ROOT)):
        raise RuntimeError("Freedom Rocket consolidation did not apply")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    already = inspect(Ruleset(ROOT))
    if not args.apply:
        print("Freedom Rocket base is consolidated" if already
              else "Freedom Rocket base is ready to consolidate")
        return 0
    apply()
    print("Applied and validated Freedom Rocket base consolidation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
