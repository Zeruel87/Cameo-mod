#!/usr/bin/env python3
"""Consolidate the reviewed Waveforce, Quantum, and Cryo family corrections."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools" / "audit"), str(ROOT / "tools" / "balance")]

from audit_physical_state_warheads import scaled_states, state_scale  # noqa: E402
from audit_three_way_split import main_warheads  # noqa: E402
from consolidate_final_safe_cohorts import (  # noqa: E402
    HEALTH_VALUES, cleanup_duplicate_template_inherits,
    cleanup_stale_removals, flat_main_nodes, tokens,
)
from consolidate_reviewed_weapon_roots import (  # noqa: E402
    add_compatibility_templates, apply_compatibility_block, block_bounds,
    resolved_flat_total,
)
from consolidate_role_complete_profiles import update_compatibility_block  # noqa: E402
from miniyaml import Ruleset  # noqa: E402
import percentage_damage as pd  # noqa: E402


# root: destination, exact descendants, flat total, folded PercentageScale
ROOTS = {
    "JHighVWaveforce": ("Waveforce_Heavy", set(), 12000, 8325),
    "JapanSpeedBoatGunWaveforce": ("Waveforce_Heavy", set(), 6000, 9984),
    "NambuMGWaveforce": ("Waveforce_Heavy", set(), 4000, 9975),
    "HueyCryoMissiles": ("Cryo_Medium", set(), 6000, 9984),
    "SteelQuantumTurretRail": (
        "Quantum_Heavy", {"SteelQuantumTurretRail_EMP"}, 14600, 1364),
}

BASELINE_MAINS = {
    "JHighVWaveforce": {"Bullet_MediumFlatCompatibility", "Railgun_Heavy"},
    "JapanSpeedBoatGunWaveforce": {"Bullet_MediumFlatCompatibility", "Railgun_Heavy"},
    "NambuMGWaveforce": {"Bullet_Light", "Railgun_Heavy"},
    "HueyCryoMissiles": {"Concussion_Medium", "Demolition_Light", "MissileAP_Medium"},
    "SteelQuantumTurretRail": {"CannonHE_Heavy", "Quantum_HeavyFlatCompatibility"},
}

# Physical-state flat scopes before and after conversion.  Scale is the
# authored state multiplier on the selected canonical family.
STATE_SCOPES = {
    "JHighVWaveforce": {
        "Temperature": (0, 12000, 35), "Corrosion": (0, 12000, 20)},
    "JapanSpeedBoatGunWaveforce": {
        "Temperature": (0, 6000, 35), "Corrosion": (0, 6000, 20)},
    "NambuMGWaveforce": {
        "Temperature": (0, 4000, 35), "Corrosion": (0, 4000, 20)},
    "HueyCryoMissiles": {"Temperature": (0, 6000, -200)},
    "SteelQuantumTurretRail": {"Temperature": (12600, 14600, 25)},
}

CONTRACT_FIELDS = (
    "ValidTargets", "InvalidTargets", "ValidRelationships",
    "InvalidRelationships", "AffectsParent", "TargetActorCenter",
)

PRESERVED_HASHES = {
    "HueyCryoMissiles": "9551ea6a6c4803b219ea9a64b8ae0a003d5b137a67bb4785f7b14e7e23c91128",
    "JHighVWaveforce": "1668788f91835cbcf85db9b8d02b546be4db1bf197b617b31c7664733da2df00",
    "JapanSpeedBoatGunWaveforce": "fdde8b44366fc5580879e01de8f749c4f0f26957414b25873b4c6b7553a2a653",
    "NambuMGWaveforce": "c21d0b7bf41c4ea74d901c3c3a46768144011fec2766dbffc9c16885dd713aeb",
    "SteelQuantumTurretRail": "73bc2ab6e666517e719de84abefb5279cc4fbbd7fe386edcdfb30b2cbce09370",
    "SteelQuantumTurretRail_EMP": "0fb467f6f3daa1d1f319f2cf501eefd6e736a42289f078352645ba35c2f8d783",
}


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
    result = {}
    for root, (destination, expected, total, scale) in ROOTS.items():
        actual = descendants(rs, root)
        if actual != expected:
            raise RuntimeError(
                f"{root}: closure changed; added={sorted(actual - expected)}, "
                f"missing={sorted(expected - actual)}")
        for name in {root, *expected}:
            result[name] = (destination, total, scale, root)
    if len(result) != 6:
        raise RuntimeError(f"expected 6 selected definitions, found {len(result)}")
    return result


def node_payload(node):
    return [node.key, node.value, [node_payload(child) for child in node.children]]


def resolved_hash(rs: Ruleset, name: str, destination: str, old_mains: set[str]) -> str:
    excluded = {f"Warhead@{key}" for key in old_mains}
    excluded.add(f"Warhead@{destination}FlatCompatibility")
    payload = [node_payload(child) for child in rs.resolve_weapon(name).children
               if child.key not in excluded]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def runtime_units(resolved, keys: set[str]) -> int:
    return sum(int(app["runtime_units"])
               for app in pd.percentage_applications(resolved, 200_000)
               if app["tag"] in keys)


def state_scope(nodes, state: str) -> tuple[int, set[int]]:
    damage = 0
    scales = set()
    for node in nodes.values():
        if state not in scaled_states(node):
            continue
        damage += int(str(node.get("Damage") or 0))
        scales.add(int(str(state_scale(node, state))))
    return damage, scales


def expected_contract(root: str):
    targets = ("Ground", "Water") if root == "SteelQuantumTurretRail" \
        else ("Air", "Ground", "Water")
    return (targets, (), ("Ally", "Enemy", "Neutral"), (), (), ())


def inspect(rs: Ruleset, print_hashes: bool = False) -> bool:
    selected = selections(rs)
    if print_hashes:
        for name, (destination, _total, _scale, root) in sorted(selected.items()):
            old = BASELINE_MAINS[root]
            print(f'    "{name}": "{resolved_hash(rs, name, destination, old)}",')
        return False
    states = set()
    for name, (destination, total, scale, root) in selected.items():
        resolved = rs.resolve_weapon(name)
        mains = set(main_warheads(resolved))
        old = BASELINE_MAINS[root]
        compatibility = f"{destination}FlatCompatibility"
        before, after = mains == old, mains == {compatibility}
        if not (before or after):
            raise RuntimeError(f"{name}: unexpected mains {sorted(mains)}")
        states.add(after)
        nodes = flat_main_nodes(resolved, mains)
        if set(nodes) != mains or resolved_flat_total(resolved, mains) != total:
            raise RuntimeError(f"{name}: flat main or total changed")
        contracts = {
            tuple(tokens(node.get(field)) for field in CONTRACT_FIELDS)
            for node in nodes.values()
        }
        if contracts != {expected_contract(root)}:
            raise RuntimeError(f"{name}: route/relationship contract changed: {contracts}")
        for physical_state, (old_scope, new_scope, expected_scale) in STATE_SCOPES[root].items():
            scope, scales = state_scope(nodes, physical_state)
            expected_scope = old_scope if before else new_scope
            expected_scales = {expected_scale} if expected_scope else set()
            if scope != expected_scope or scales != expected_scales:
                raise RuntimeError(
                    f"{name}: {physical_state} scope changed: {scope}, {sorted(scales)}")
        units = runtime_units(resolved, mains)
        folded_units = pd.folded_units(total, scale)[1] if scale else 0
        if units != folded_units:
            raise RuntimeError(f"{name}: percentage units changed: {units} != {folded_units}")
        if before:
            for hp in HEALTH_VALUES:
                old_hp = sum(int(app["runtime_hp"])
                             for app in pd.percentage_applications(resolved, hp)
                             if app["tag"] in mains)
                new_hp = pd.runtime_percentage_hp(
                    hp, folded_units, pd.FOLDED_DEFAULT_DENOMINATOR) if folded_units else 0
                if old_hp < 0 or new_hp < 0:
                    raise RuntimeError(f"{name}: percentage overflow at {hp}")
                if abs(old_hp - new_hp) > 1:
                    raise RuntimeError(f"{name}: percentage drift exceeds one HP at {hp}")
        else:
            node = nodes[compatibility]
            if int(str(node.get("PercentageScale") or 0)) != scale:
                raise RuntimeError(f"{name}: applied percentage scale changed")
        if PRESERVED_HASHES and resolved_hash(rs, name, destination, old) != PRESERVED_HASHES[name]:
            raise RuntimeError(f"{name}: non-selected behavior changed")
    if len(states) != 1:
        raise RuntimeError("partial named-state consolidation detected")
    return states == {True}


def local_has(lines, weapon, marker):
    start, end = block_bounds(lines, weapon)
    return any(lines[index].rstrip("\r\n") == marker for index in range(start + 1, end))


def add_removal(lines, weapon, key):
    marker = f"\t-Warhead@{key}:"
    if local_has(lines, weapon, marker):
        return
    start, end = block_bounds(lines, weapon)
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    lines.insert(end, marker + "\n")


def convert_member(rs, changed, name, destination, total, scale, root):
    path = pathlib.Path(rs.weapon(name).file)
    lines = changed.setdefault(path, path.read_text(encoding="utf-8-sig").splitlines(True))
    compatibility = f"{destination}FlatCompatibility"
    removals = BASELINE_MAINS[root] - {compatibility}
    if local_has(lines, name, f"\tWarhead@{compatibility}:"):
        update_compatibility_block(lines, name, destination, total, scale, None)
        for key in removals:
            add_removal(lines, name, key)
    else:
        targets = "Ground, Water" if root == "SteelQuantumTurretRail" \
            else "Ground, Water, Air"
        apply_compatibility_block(
            changed, path, name, destination, removals, total, targets,
            inherit_template=True)
        update_compatibility_block(lines, name, destination, total, scale, None)


def apply_changes(rs: Ruleset):
    selected = selections(rs)
    changed = {}
    add_compatibility_templates(
        changed, rs, {destination for destination, _total, _scale, _root in selected.values()},
        ["# Canonical flat profiles for reviewed named-family state corrections.\n"])
    for name, (destination, total, scale, root) in selected.items():
        convert_member(rs, changed, name, destination, total, scale, root)
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")
    cleanup_stale_removals(set(selected))
    cleanup_duplicate_template_inherits(set(selected))


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
        print("Already consolidated 6 named-family state corrections")
        return 0
    print("5 roots; 6 closure members; 6 reductions")
    if not args.apply:
        print("Dry run: closures, routes, totals, states, percentages, overflow, and hashes pass")
        return 0
    apply_changes(rs)
    if not inspect(Ruleset(ROOT)):
        raise RuntimeError("named-family state cohort remains unconsolidated")
    print("Applied and validated named-family state corrections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
