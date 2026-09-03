#!/usr/bin/env python3
"""Consolidate the next explicitly reviewed, role-corroborated weapon cohort.

This batch is intentionally manifest-driven.  It preserves weapon delivery,
effects, routes, relationships, nominal flat totals, and bounded percentage
behavior while adopting one reviewed canonical damage profile.  Exact closure,
source-main, total, scale, and non-selected-behavior pins make it fail closed.
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
from consolidate_final_safe_cohorts import (  # noqa: E402
    HEALTH_VALUES, flat_main_nodes, tokens,
)
from consolidate_reviewed_weapon_roots import (  # noqa: E402
    add_compatibility_templates, apply_compatibility_block, block_bounds,
    resolved_flat_total,
)
from consolidate_role_complete_profiles import update_compatibility_block  # noqa: E402
from miniyaml import Ruleset  # noqa: E402
import percentage_damage as pd  # noqa: E402


# destination, exact descendants, flat total, folded PercentageScale
ROOTS = {
    "CannonAttackRobotGun": ("CannonHE_Medium", {"CannonAttackRobotGun_elite"}, 8000, 4988),
    "RA2GrenadePack": ("Concussion_Light", {"RA2GrenadePack_elite"}, 6000, 9984),
    "SteelDaggerCannon": ("CannonHE_Heavy", {"SteelDaggerCannon_elite"}, 8000, 4988),
    "LatinSmokerCannon": ("CannonHE_Medium", {"LatinSmokerCannon_elite"}, 13000, 3070),
    "RA2LarsRocket": ("MissileAP_Heavy", set(), 10000, 3990),
    "SpecterArtilleryShellUpgrade": ("CannonHE_Heavy", set(), 32000, 2497),
    "LatinAADefenderCannon": ("MissileAP_Medium", set(), 4000, 9975),
    "WyvernRockets": ("MissileAP_Heavy", set(), 16000, 2494),
}

BASELINE_MAINS = {
    "CannonAttackRobotGun": {"CannonHE_Medium", "Railgun_Heavy"},
    "CannonAttackRobotGun_elite": {"CannonHE_Medium", "Railgun_Heavy"},
    "RA2GrenadePack": {"Concussion_Light", "Flak_Medium", "MissileAP_Heavy"},
    "RA2GrenadePack_elite": {"Concussion_Light", "Flak_Medium", "MissileAP_Heavy"},
    "SteelDaggerCannon": {"CannonHE_Heavy", "Demolition_Light"},
    "SteelDaggerCannon_elite": {"CannonHE_Heavy", "Demolition_Light"},
    "LatinSmokerCannon": {"CannonHE_Heavy", "CannonHE_Medium"},
    "LatinSmokerCannon_elite": {"CannonHE_Heavy", "CannonHE_Medium"},
    "RA2LarsRocket": {"MissileAP_Heavy", "MissileAP_Medium"},
    "SpecterArtilleryShellUpgrade": {"CannonHE_HeavyFlatCompatibility", "Concussion_Medium", "Demolition_Light"},
    "LatinAADefenderCannon": {"Flak_Medium", "MissileAP_Medium"},
    "WyvernRockets": {"CannonHE_Heavy", "MissileAP_Heavy"},
}

GROUND_ONLY = {
    "CannonAttackRobotGun", "CannonAttackRobotGun_elite",
    "SteelDaggerCannon", "SteelDaggerCannon_elite",
    "LatinSmokerCannon", "LatinSmokerCannon_elite",
    "SpecterArtilleryShellUpgrade",
}

# Filled from the guarded baseline; selected main nodes are deliberately omitted.
PRESERVED_HASHES = {
    "CannonAttackRobotGun": "e0c5d9d6953ded717a5704cbd3a45fcf430e2630cf9ef3d4c82bc141624324da",
    "CannonAttackRobotGun_elite": "92a44c144c1f6bfc5de0a29476b00360d3d3aabb2779c7088060aab240a1194d",
    "LatinAADefenderCannon": "7795fa2dc60038ade6c311ede1fd05c157a0e7fdbf051ee840b23aa5e27e20ee",
    "LatinSmokerCannon": "f9825c00ae46bdcbd6a8c01e8ee75ebf17ce4579a3b5d4e33f9c2d26e8af4097",
    "LatinSmokerCannon_elite": "b6340dd1586e3b0dbad7efa30b62bfc55edc30cb3a505cb616775bd1daf233fa",
    "RA2GrenadePack": "a1348707ab51ddc8de8bcd6f209ebac6efc96d9fdfaf50b72d584ff3bb007a0f",
    "RA2GrenadePack_elite": "9e1e86c6b01fd66a11324779ab86721904b7a0bf4a58c0fd5c33fbea8aaab623",
    "RA2LarsRocket": "35d0329ad7e978f7568c01bd19a09563fd925d30b1ad5a8e3576ffed459d7584",
    "SpecterArtilleryShellUpgrade": "19081d076ca2ade415be2adbe1286fd1c1aec53f8867271501ed9790c790e0c2",
    "SteelDaggerCannon": "e0f5ce303cb7f4b74aa278fdaf5068471ac732c273ae2fc81e094fe9d0a7a27e",
    "SteelDaggerCannon_elite": "4f4749bbf619b1ee6374507fb903a3d7acae62d10e1e585777403640a32418c5",
    "WyvernRockets": "f9a06db96c28a5b1f71ee481e4a128569dbd80d639a0d33cdc65d3bb909f22dd",
}

CONTRACT_FIELDS = (
    "ValidTargets", "InvalidTargets", "ValidRelationships",
    "InvalidRelationships", "AffectsParent", "TargetActorCenter",
)


def descendants(rs: Ruleset, root: str) -> set[str]:
    direct: dict[str, set[str]] = collections.defaultdict(set)
    for name, node in rs.weapons.items():
        for _, parent in rs.inherits_of(node):
            if parent in rs.weapons:
                direct[parent].add(name)
    seen, stack = set(), list(direct[root])
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        stack.extend(direct[name])
    return {name for name in seen if not name.startswith("^")}


def selections(rs: Ruleset):
    selected = {}
    for root, (destination, expected, total, scale) in ROOTS.items():
        actual = descendants(rs, root)
        if actual != expected:
            raise RuntimeError(
                f"{root}: closure changed; added={sorted(actual - expected)}, "
                f"missing={sorted(expected - actual)}")
        for name in {root, *expected}:
            if name in selected:
                raise RuntimeError(f"{name}: selected twice")
            selected[name] = (destination, total, scale)
    if len(selected) != 12:
        raise RuntimeError(f"expected 12 closure members, found {len(selected)}")
    return selected


def node_payload(node):
    return [node.key, node.value, [node_payload(child) for child in node.children]]


def resolved_hash(rs: Ruleset, name: str, destination: str) -> str:
    excluded = {f"Warhead@{key}" for key in BASELINE_MAINS[name]}
    excluded.add(f"Warhead@{destination}FlatCompatibility")
    payload = [node_payload(child) for child in rs.resolve_weapon(name).children
               if child.key not in excluded]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def runtime_hp(resolved, keys: set[str], hp: int) -> int:
    return sum(int(app["runtime_hp"]) for app in pd.percentage_applications(resolved, hp)
               if app["tag"] in keys)


def expected_contract(name: str):
    targets = ("Ground", "Water") if name in GROUND_ONLY else ("Air", "Ground", "Water")
    return (targets, (), ("Ally", "Enemy", "Neutral"), (), (), ())


def inspect(rs: Ruleset, print_hashes: bool = False) -> bool:
    selected = selections(rs)
    if print_hashes:
        for name, (destination, _total, _scale) in sorted(selected.items()):
            print(f'    "{name}": "{resolved_hash(rs, name, destination)}",')
        return False
    states = set()
    for name, (destination, total, scale) in selected.items():
        resolved = rs.resolve_weapon(name)
        mains = set(main_warheads(resolved))
        compatibility = f"{destination}FlatCompatibility"
        before = mains == BASELINE_MAINS[name]
        after = mains == {compatibility}
        if not (before or after):
            raise RuntimeError(f"{name}: unexpected mains {sorted(mains)}")
        states.add(after)
        nodes = flat_main_nodes(resolved, mains)
        if set(nodes) != mains:
            raise RuntimeError(f"{name}: non-flat selected main")
        contracts = {
            tuple(tokens(node.get(field)) for field in CONTRACT_FIELDS)
            for node in nodes.values()
        }
        if contracts != {expected_contract(name)}:
            raise RuntimeError(f"{name}: target/relationship contract changed: {contracts}")
        for tag, node in nodes.items():
            if any(child.key in {"PhysicalState", "PhysicalStates", "PhysicalStateName", "PhysicalStateScale", "IntegrityScale"}
                   for child in node.children):
                raise RuntimeError(f"{name}: {tag} carries a state hook")
            if "PreservedFlat" in tag or tag == "1Dam":
                raise RuntimeError(f"{name}: selected a special compatibility hook")
        if before:
            if resolved_flat_total(resolved, mains) != total:
                raise RuntimeError(f"{name}: source total changed")
            old_hp = {hp: runtime_hp(resolved, mains, hp) for hp in HEALTH_VALUES}
            if any(value < 0 for value in old_hp.values()):
                raise RuntimeError(f"{name}: source percentage overflow")
            folded_units = pd.folded_units(total, scale)[1]
            folded = {hp: pd.runtime_percentage_hp(
                hp, folded_units, pd.FOLDED_DEFAULT_DENOMINATOR) for hp in HEALTH_VALUES}
            if max(abs(folded[hp] - old_hp[hp]) for hp in HEALTH_VALUES) > 1:
                raise RuntimeError(f"{name}: percentage drift exceeds one HP")
        else:
            node = nodes[compatibility]
            if int(str(node.get("Damage") or 0)) != total:
                raise RuntimeError(f"{name}: applied total changed")
            if int(str(node.get("PercentageScale") or 0)) != scale:
                raise RuntimeError(f"{name}: applied percentage scale changed")
            if any(runtime_hp(resolved, {compatibility}, hp) < 0 for hp in HEALTH_VALUES):
                raise RuntimeError(f"{name}: folded percentage overflow")
        if PRESERVED_HASHES and resolved_hash(rs, name, destination) != PRESERVED_HASHES[name]:
            raise RuntimeError(f"{name}: non-selected behavior hash changed")
    if len(states) != 1:
        raise RuntimeError("partial pinned-role consolidation detected")
    return states == {True}


def local_has(lines: list[str], weapon: str, marker: str) -> bool:
    start, end = block_bounds(lines, weapon)
    return any(lines[index].rstrip("\r\n") == marker for index in range(start + 1, end))


def add_removal(lines: list[str], weapon: str, key: str) -> None:
    marker = f"\t-Warhead@{key}:"
    if local_has(lines, weapon, marker):
        return
    start, end = block_bounds(lines, weapon)
    insertion = end
    while insertion > start + 1 and not lines[insertion - 1].strip():
        insertion -= 1
    lines.insert(insertion, marker + "\n")


def remove_removal(lines: list[str], weapon: str, key: str) -> None:
    """Remove a prior compatibility suppression before reusing that profile."""
    marker = f"\t-Warhead@{key}:"
    start, end = block_bounds(lines, weapon)
    rows = [index for index in range(start + 1, end)
            if lines[index].rstrip("\r\n") == marker]
    if len(rows) > 1:
        raise RuntimeError(f"{weapon}: duplicate removal for {key}")
    if rows:
        del lines[rows[0]]


def convert_root(rs: Ruleset, changed, root: str, destination: str,
                 total: int, scale: int) -> None:
    path = pathlib.Path(rs.weapon(root).file)
    lines = changed.setdefault(path, path.read_text(encoding="utf-8-sig").splitlines(True))
    compatibility = f"{destination}FlatCompatibility"
    removals = BASELINE_MAINS[root] - {compatibility}
    remove_removal(lines, root, compatibility)
    if local_has(lines, root, f"\tWarhead@{compatibility}:"):
        update_compatibility_block(lines, root, destination, total, scale, None)
        for key in removals:
            add_removal(lines, root, key)
    else:
        targets = "Ground, Water" if root in GROUND_ONLY else "Ground, Water, Air"
        apply_compatibility_block(changed, path, root, destination, removals, total, targets)
        update_compatibility_block(lines, root, destination, total, scale, None)


def apply_changes(rs: Ruleset) -> None:
    changed = {}
    add_compatibility_templates(
        changed, rs, {destination for destination, _children, _total, _scale in ROOTS.values()},
        ["# Canonical flat profiles for the reviewed pinned-role cohort.\n"])
    for root, (destination, _children, total, scale) in ROOTS.items():
        convert_root(rs, changed, root, destination, total, scale)
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--print-hashes", action="store_true")
    args = parser.parse_args()
    rs = Ruleset(ROOT)
    if args.print_hashes:
        inspect(rs, True)
        return 0
    already = inspect(rs)
    if already:
        print("Already consolidated 12 pinned-role definitions")
        return 0
    print("8 roots; 12 closure members; 12 multi-main conversions")
    if not args.apply:
        print("Dry run: closures, mains, routes, totals, rounding, overflow, and hashes pass")
        return 0
    apply_changes(rs)
    if not inspect(Ruleset(ROOT)):
        raise RuntimeError("pinned-role cohort remains unconsolidated")
    print("Applied and validated pinned-role cohort")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
