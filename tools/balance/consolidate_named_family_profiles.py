#!/usr/bin/env python3
"""Consolidate reviewed elemental, energy, and sonic named-family weapons.

This is an intentional canonical-role conversion: nominal flat damage, weapon
routes, unrelated behavior, and percentage damage (within one HP across active
health values) are guarded while the selected family supplies armor and blast
behavior.  Explicit closures make newly added variants fail closed.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from audit_three_way_split import main_warheads  # noqa: E402
from consolidate_final_safe_cohorts import (  # noqa: E402
    HEALTH_VALUES, ensure_template_inherit, flat_main_nodes, tokens,
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
    "IncendiaryYakChainGun": ("Flame_Light", {"IncendiaryArmoredYakChainGun"}, 8000, 9988),
    "IncendiaryChainGun": ("Flame_Light", set(), 4000, 9975),
    "IncendiaryRAGatlingTankCannon": ("Flame_Light", {"IncendiaryRAGatlingTankCannon_AA"}, 4000, 9975),
    "NapalmA10Carrier": ("Flame_Heavy", set(), 8000, 9988),
    "GrenadeThermobaric": ("Thermobaric_Light", {"GrenadeThermobaricExplode"}, 16000, 4994),
    "HindMissilesThermobaric": ("Thermobaric_Medium", set(), 10000, 1990),
    "AsianChemical": ("Chemical_Medium", {"AsianChemical_elite"}, 24000, 1663),
    "CabalOverkillDroneLaser": ("Laser_Heavy", set(), 8000, 9988),
    "RA2CosmonautLaser": ("Laser_Light", set(), 13600, 1464),
    "TSLasergun": ("Laser_Heavy", set(), 4000, 9975),
    "edenMobileDefenceLaser": ("Laser_Heavy", set(), 10000, 1990),
    "TSLaserHarpyClaw": ("Laser_Heavy", {"TSLaserHarpyAOEClaw", "TSLaserHarpyMultiClaw"}, 8000, 9988),
    "AsianHarbingerPlasma": ("Plasma_Medium", set(), 16000, 2494),
    "FutureMechPlasma_elite": ("Plasma_Heavy", set(), 30000, 3330),
    "HovercraftPlasmaCannon": ("Plasma_Medium", set(), 27000, 0),
    "Type89PlasmaCannon": ("Plasma_Medium", set(), 15000, 0),
    "TSAssaultCannonSonic": ("Sonic_Medium", set(), 8000, 4988),
    "TSVulcanGunSonic": ("Sonic_Medium", set(), 16000, 2494),
}

BASELINE_MAINS = {
    "IncendiaryYakChainGun": {"Bullet_Medium", "Flame_Light"},
    "IncendiaryArmoredYakChainGun": {"Bullet_Medium", "Flame_Light"},
    "IncendiaryChainGun": {"Bullet_Medium", "Flame_Light"},
    "IncendiaryRAGatlingTankCannon": {"Bullet_Medium", "Flame_Light"},
    "IncendiaryRAGatlingTankCannon_AA": {"Bullet_Medium", "Flame_Light"},
    "NapalmA10Carrier": {"Demolition_Heavy", "Flame_Heavy"},
    "GrenadeThermobaric": {"Demolition_Light", "Flame_Light", "Thermobaric_LightFlatCompatibility"},
    "GrenadeThermobaricExplode": {"Demolition_Light", "Flame_Light", "Grenade", "LightFlameWeapon", "Thermobaric_LightFlatCompatibility"},
    "HindMissilesThermobaric": {"CannonHE_Heavy", "Thermobaric_Medium"},
    "AsianChemical": {"Chemical_MediumFlatCompatibility", "Demolition_Light"},
    "AsianChemical_elite": {"Chemical_MediumFlatCompatibility", "Demolition_Light"},
    "CabalOverkillDroneLaser": {"Bullet_Light", "Laser_Heavy"},
    "RA2CosmonautLaser": {"Bullet_Medium", "Laser_LightFlatCompatibility"},
    "TSLasergun": {"Bullet_Light", "Laser_Heavy"},
    "edenMobileDefenceLaser": {"CannonHE_Medium", "Laser_Heavy"},
    "TSLaserHarpyClaw": {"Bullet_Medium", "Laser_Heavy"},
    "TSLaserHarpyAOEClaw": {"Bullet_Medium", "Laser_Heavy"},
    "TSLaserHarpyMultiClaw": {"Laser_Heavy"},
    "AsianHarbingerPlasma": {"CannonHE_Medium", "MissileAP_Medium", "Plasma_Medium"},
    "FutureMechPlasma_elite": {"CannonHE_Heavy", "Plasma_Heavy"},
    "HovercraftPlasmaCannon": {"Bullet_Light", "Bullet_Medium", "CannonAP_Light", "CannonHE_Medium", "Plasma_MediumFlatCompatibility"},
    "Type89PlasmaCannon": {"CannonHE_Medium", "Plasma_MediumFlatCompatibility"},
    "TSAssaultCannonSonic": {"Flak_Medium", "Sonic_Medium"},
    "TSVulcanGunSonic": {"Bullet_Medium", "Sonic_Medium"},
}

EXPECTED_ROUTES = {
    "IncendiaryRAGatlingTankCannon": ("Ground", "Water"),
    "IncendiaryRAGatlingTankCannon_AA": ("Air",),
    "TSLaserHarpyClaw": ("Air", "Ground"),
    "TSLaserHarpyAOEClaw": ("Air", "Ground"),
    "TSLaserHarpyMultiClaw": ("Air", "Ground"),
}
EXACT_PLUS_ONE = {
    "IncendiaryChainGun", "IncendiaryRAGatlingTankCannon",
    "IncendiaryRAGatlingTankCannon_AA", "TSLasergun",
    "AsianHarbingerPlasma", "TSAssaultCannonSonic", "TSVulcanGunSonic",
}

# Filled from the guarded baseline; selected main nodes are deliberately omitted.
PRESERVED_HASHES = {
    "AsianChemical": "1b9c01e71ccd601423e1d5155b9ef5c6afd64291559a120ca4cacf6f49defbd7",
    "AsianChemical_elite": "0e3137f37d57db66978c363090ba1f92adae067f3e5fe9b4217fb3060253a20d",
    "AsianHarbingerPlasma": "a2226f62246753fb32b9d7fae6091ed5f647cdca2e95b13aeb3126f2bdd51196",
    "CabalOverkillDroneLaser": "b8e3ab18dcdb387de5353419fa7c861589300a3e55172172e98938427074c56c",
    "FutureMechPlasma_elite": "5377c85750d8713299fc3fb8d953424720672993966745977134877a92d07335",
    "GrenadeThermobaric": "68427c34d198d3c4600a23c36c6060e850116005badd8267fd22930c49e72a21",
    "GrenadeThermobaricExplode": "8fe5998a7db0e20abba7063c9347630609367cb6c2ebd9a461c98283574e64c0",
    "HindMissilesThermobaric": "d366836a8300a153b89b8fa43ad42a89262ef0a6e7364d9aefafbacddd5d1c8c",
    "HovercraftPlasmaCannon": "6bc2e618c616ace9ba4e7e2201d318f67df40efaa7f9e96ee24ae7945f1351fd",
    "IncendiaryArmoredYakChainGun": "1fb00ddcb2528c2cd2c12eb74b906b161eb12a5f51f8b0ed0aaf23aa0a72872a",
    "IncendiaryChainGun": "afbc3a13dd609f6493c8de768bffdb8330b10b13e446e709bad95ae1e3a0148f",
    "IncendiaryRAGatlingTankCannon": "2f8b34a65480f2222db704afd9dd4ccb371b5433e52ba884dcfb2abeb82ca523",
    "IncendiaryRAGatlingTankCannon_AA": "65567caab895b40a7d9d91c75a425d203ab9b69aab15268d3efa0c75e642de6d",
    "IncendiaryYakChainGun": "41c173cf4287292c5f8b45970053de5c609067d9a92e5dda586772cdc2e2d870",
    "NapalmA10Carrier": "681759d81958c17756b909aada1c0d24669ad2a12560795ad018aba701183f7e",
    "RA2CosmonautLaser": "95be178ac49664713f083712f15c5e7110c7e5b26856f3a04c5d580317f8f557",
    # Post-consolidation correction: Wolverine keeps its advertised weak AA
    # role after Sonic Weaponry replaces the base armament.
    "TSAssaultCannonSonic": "845a4a6c2be68852fed127665fe7537cbb26bab0c9886649bfd3c14945e88b4f",
    "TSLaserHarpyAOEClaw": "91796c834129cda6876c6b969432b236b98b70ef3815a37f4d2446e6225f33a0",
    "TSLaserHarpyClaw": "eeb4e892b06d1edc15620ad691e45b7e7afe45286088e83f81c9baa0a30257e1",
    "TSLaserHarpyMultiClaw": "31023bbe2fc4ead557dfb71e272e73293046514efa4470760dc0a44d5dbf5538",
    "TSLasergun": "000a97c76397f97b5194a72786dbf79e8c70f70f4270a97d708f0cc8678449fd",
    "TSVulcanGunSonic": "c8293748cea181640a204e67696d6a2d03e9ecf2d75c7e7f7c64819c35cf02e1",
    "Type89PlasmaCannon": "e9ce92eb132a5b257af46bde56c54ea43b4d0272aede1c558793ef65d8e5d1c5",
    "edenMobileDefenceLaser": "2608f8666105cf7f63e31308f375f1cb17032425c1dbd4c15ac0087a61cdc959",
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


def selections(rs: Ruleset) -> dict[str, tuple[str, int, int]]:
    selected = {}
    for root, (destination, expected, total, scale) in ROOTS.items():
        actual = descendants(rs, root)
        if actual != expected:
            raise RuntimeError(f"{root}: closure changed; added={sorted(actual - expected)}, missing={sorted(expected - actual)}")
        for name in {root, *expected}:
            if name in selected:
                raise RuntimeError(f"{name}: selected twice")
            member_total = 4000 if name == "TSLaserHarpyMultiClaw" else total
            member_scale = 9975 if name == "TSLaserHarpyMultiClaw" else scale
            selected[name] = (destination, member_total, member_scale)
    if len(selected) != 24:
        raise RuntimeError(f"expected 24 closure members, found {len(selected)}")
    return selected


def node_payload(node):
    return [node.key, node.value, [node_payload(child) for child in node.children]]


def resolved_hash(rs: Ruleset, name: str, destination: str) -> str:
    excluded = {f"Warhead@{key}" for key in BASELINE_MAINS[name]}
    if name == "TSLaserHarpyMultiClaw":
        excluded.add("Warhead@Bullet_Medium")
    excluded.add(f"Warhead@{destination}FlatCompatibility")
    payload = [node_payload(child) for child in rs.resolve_weapon(name).children
               if child.key not in excluded]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def runtime_hp(resolved, keys: set[str], hp: int) -> int:
    return sum(int(app["runtime_hp"]) for app in pd.percentage_applications(resolved, hp)
               if app["tag"] in keys)


def inspect(rs: Ruleset, print_hashes: bool = False) -> bool:
    selected = selections(rs)
    if print_hashes:
        for name, (destination, _total, _scale) in sorted(selected.items()):
            print(f'    "{name}": "{resolved_hash(rs, name, destination)}",')
        return False
    states = set()
    plus_one = set()
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
        route = tokens(resolved.get("ValidTargets"))
        expected_route = EXPECTED_ROUTES.get(name)
        if expected_route and route != expected_route:
            raise RuntimeError(f"{name}: route changed from {expected_route} to {route}")
        if before:
            if resolved_flat_total(resolved, mains) != total:
                raise RuntimeError(f"{name}: source total changed")
            old_hp = {hp: runtime_hp(resolved, mains, hp) for hp in HEALTH_VALUES}
            for hp, value in old_hp.items():
                if value < 0:
                    raise RuntimeError(f"{name}: source percentage overflow at {hp}")
            folded = {hp: pd.runtime_percentage_hp(
                hp, pd.folded_units(total, scale)[1], pd.FOLDED_DEFAULT_DENOMINATOR)
                      for hp in HEALTH_VALUES}
            deltas = {hp: folded[hp] - old_hp[hp] for hp in HEALTH_VALUES}
            if max(map(abs, deltas.values())) > 1:
                raise RuntimeError(f"{name}: percentage drift exceeds one HP")
            if any(delta == 1 for delta in deltas.values()):
                plus_one.add(name)
        else:
            node = nodes[compatibility]
            if int(str(node.get("Damage") or 0)) != total or int(str(node.get("PercentageScale") or 0)) != scale:
                raise RuntimeError(f"{name}: applied total/scale changed")
            for hp in HEALTH_VALUES:
                if runtime_hp(resolved, {compatibility}, hp) < 0:
                    raise RuntimeError(f"{name}: folded percentage overflow at {hp}")
        if PRESERVED_HASHES and resolved_hash(rs, name, destination) != PRESERVED_HASHES[name]:
            raise RuntimeError(f"{name}: non-selected behavior hash changed")
    if False in states and plus_one != EXACT_PLUS_ONE:
        raise RuntimeError(f"rounding manifest changed: {sorted(plus_one)}")
    if len(states) != 1:
        raise RuntimeError("partial named-family consolidation detected")
    return states == {True}


def local_has(lines: list[str], weapon: str, marker: str) -> bool:
    start, end = block_bounds(lines, weapon)
    return any(lines[i].rstrip("\r\n") == marker for i in range(start + 1, end))


def add_removal(lines: list[str], weapon: str, key: str) -> None:
    marker = f"\t-Warhead@{key}:"
    if local_has(lines, weapon, marker):
        return
    start, end = block_bounds(lines, weapon)
    insertion = end
    while insertion > start + 1 and not lines[insertion - 1].strip():
        insertion -= 1
    lines.insert(insertion, marker + "\n")


def set_geometry(lines: list[str], weapon: str, destination: str) -> None:
    start, end = block_bounds(lines, weapon)
    marker = f"\tWarhead@{destination}FlatCompatibility:"
    row = next(i for i in range(start + 1, end) if lines[i].rstrip("\r\n") == marker)
    insert = row + 1
    lines[insert:insert] = ["\t\tSpread: 300\n", "\t\tFalloff: 100, 50, 25\n"]


def convert_member(rs: Ruleset, changed, name: str, destination: str,
                   total: int, scale: int, removals: set[str],
                   inherit_template: bool = True) -> None:
    node = rs.weapon(name)
    path = pathlib.Path(node.file)
    lines = changed.setdefault(path, path.read_text(encoding="utf-8-sig").splitlines(True))
    compatibility = f"{destination}FlatCompatibility"
    if not local_has(lines, name, f"\tWarhead@{compatibility}:"):
        apply_compatibility_block(changed, path, name, destination, removals,
                                  total, str(rs.resolve_weapon(name).get("ValidTargets") or ""),
                                  inherit_template=inherit_template)
        update_compatibility_block(lines, name, destination, total, scale, None)
    else:
        if inherit_template:
            ensure_template_inherit(changed, path, name, destination)
        update_compatibility_block(lines, name, destination, total, scale, None)
        for key in removals:
            add_removal(lines, name, key)


def apply_changes(rs: Ruleset) -> None:
    changed = {}
    add_compatibility_templates(
        changed, rs, {destination for destination, _children, _total, _scale
                      in ROOTS.values()},
        ["# Canonical named-family flat profiles used by the reviewed elemental,\n",
         "# energy, and sonic role consolidation.\n"])
    # Convert roots. Descendants without local main overrides inherit the fold.
    for root, (destination, _children, total, scale) in ROOTS.items():
        compatibility = f"{destination}FlatCompatibility"
        convert_member(rs, changed, root, destination, total, scale,
                       BASELINE_MAINS[root] - {compatibility})

    # Route/shape descendants with local main overrides need explicit local pins.
    convert_member(rs, changed, "IncendiaryRAGatlingTankCannon_AA", "Flame_Light", 4000, 9975, {"Flame_Light"}, False)
    convert_member(rs, changed, "GrenadeThermobaricExplode", "Thermobaric_Light", 16000, 4994,
                   {"Grenade", "LightFlameWeapon"}, False)
    convert_member(rs, changed, "TSLaserHarpyAOEClaw", "Laser_Heavy", 8000, 9988,
                   {"Bullet_Medium"}, False)
    set_geometry(changed[pathlib.Path(rs.weapon("TSLaserHarpyAOEClaw").file)],
                 "TSLaserHarpyAOEClaw", "Laser_Heavy")
    convert_member(rs, changed, "TSLaserHarpyMultiClaw", "Laser_Heavy", 4000, 9975,
                   {"Bullet_Medium"}, False)

    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")


def validate_result() -> None:
    if not inspect(Ruleset(ROOT)):
        raise RuntimeError("named-family cohort remains unconsolidated")


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
        print("Already consolidated 24 closure members (23 former multi-main definitions)")
        return 0
    print("18 roots; 24 closure members; 23 multi-main conversions")
    if not args.apply:
        print("Dry run: closures, routes, totals, rounding, overflow, and hashes pass")
        return 0
    apply_changes(rs)
    validate_result()
    print("Applied and validated named-family cohort")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
