#!/usr/bin/env python3
"""Fold reviewed percentage-inert compatibility slices into their canonical main.

The compatibility profiles were created while retiring legacy weapon roots.  This
batch handles only definitions where the compatibility slice and its already
selected canonical destination have identical resolved behavior except for Damage
and PercentageScale.  The compatibility slice has PercentageScale 0, so folding
its flat damage into the canonical main leaves the independently authored
percentage application untouched.

Every source value is pinned below.  A changed inheritance tree or source block
fails closed instead of silently expanding the batch.
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from miniyaml import Node, Ruleset  # noqa: E402
from audit_three_way_split import main_warheads  # noqa: E402
from consolidate_reviewed_weapon_roots import block_bounds  # noqa: E402
import percentage_damage as pd  # noqa: E402
from review_batch_diff import active_health_values  # noqa: E402


# weapon: compatibility key, canonical key, old canonical damage,
# old compatibility damage, folded damage
SPECS = {
    'TurretGunBlackMarket': ('Concussion_MediumFlatCompatibility', 'Concussion_Medium', 19000, 12000, 31000),
    'ra120mm2': ('CannonHE_HeavyFlatCompatibility', 'CannonHE_Heavy', 16000, 32000, 48000),
    'ReconRangerRecoillessGun': ('MissileAP_HeavyFlatCompatibility', 'MissileAP_Heavy', 4000, 29000, 33000),
    '25mm': ('CannonHE_MediumFlatCompatibility', 'CannonHE_Medium', 2000, 10000, 12000),
    'KodiakCannon': ('CannonHE_HeavyFlatCompatibility', 'CannonHE_Heavy', 8000, 32000, 40000),
    'TS70mmTurChem': ('CannonHE_MediumFlatCompatibility', 'CannonHE_Medium', 4000, 8000, 12000),
    'TSScoopDualTurChem': ('CannonHE_HeavyFlatCompatibility', 'CannonHE_Heavy', 16000, 32000, 48000),
    'RA2GrandCannonWeapon': ('CannonHE_HeavyFlatCompatibility', 'CannonHE_Heavy', 50000, 200000, 250000),
    'RA2FlakTrackAAGun': ('Flak_MediumFlatCompatibility', 'Flak_Medium', 2000, 6000, 8000),
    'RA2LasherCannon': ('CannonHE_MediumFlatCompatibility', 'CannonHE_Medium', 2000, 10000, 12000),
    'AsianLynxTankCannon': ('CannonHE_MediumFlatCompatibility', 'CannonHE_Medium', 2000, 10000, 12000),
    'AsianPulverizerMechaGatling': ('Bullet_MediumFlatCompatibility', 'Bullet_Medium', 2000, 4000, 6000),
    'WhiteRabbitGatling': ('Bullet_MediumFlatCompatibility', 'Bullet_Medium', 4000, 16000, 20000),
    'SteelDaggerCannon': ('CannonHE_HeavyFlatCompatibility', 'CannonHE_Heavy', 2000, 4000, 6000),
    'SteelCruiserCannons': ('Bullet_MediumFlatCompatibility', 'Bullet_Medium', 2000, 6000, 8000),
    'RA2LarsRocket': ('MissileAP_HeavyFlatCompatibility', 'MissileAP_Heavy', 2000, 6000, 8000),
    'LatinSmokerCannon': ('CannonHE_MediumFlatCompatibility', 'CannonHE_Medium', 2000, 9000, 11000),
    'DiabloCannon': ('Flak_MediumFlatCompatibility', 'Flak_Medium', 2000, 6000, 8000),
    'RA2APCFlakCannon': ('Flak_MediumFlatCompatibility', 'Flak_Medium', 2000, 6000, 8000),
    'LunarTigerCannon': ('CannonHE_MediumFlatCompatibility', 'CannonHE_Medium', 4000, 12000, 16000),
    'CannonAttackRobotGun': ('CannonHE_MediumFlatCompatibility', 'CannonHE_Medium', 2000, 4000, 6000),
    'FutureMechGatling': ('Bullet_MediumFlatCompatibility', 'Bullet_Medium', 2000, 6000, 8000),
    '120mm_td': ('CannonHE_MediumFlatCompatibility', 'CannonHE_Medium', 14000, 42000, 56000),
    'DeviatorMissile': ('MissileAP_HeavyFlatCompatibility', 'MissileAP_Heavy', 10000, 20000, 30000),
    'DeviatorMissile_Artillery': ('MissileAP_HeavyFlatCompatibility', 'MissileAP_Heavy', 10000, 40000, 50000),
    'HMG_Duelist_upgrade': ('Bullet_MediumFlatCompatibility', 'Bullet_Medium', 12000, 4000, 16000),
    'ScarabLaunch': ('CannonHE_HeavyFlatCompatibility', 'CannonHE_Heavy', 50000, 150000, 200000),
    'AtreusMG': ('Bullet_MediumFlatCompatibility', 'Bullet_Medium', 2000, 6000, 8000),
    'SCTyr': ('CannonHE_HeavyFlatCompatibility', 'CannonHE_Heavy', 4000, 12000, 16000),
    'GoliathMk2MG': ('Bullet_MediumFlatCompatibility', 'Bullet_Medium', 2000, 4000, 6000),
    'WyvernRockets': ('MissileAP_HeavyFlatCompatibility', 'MissileAP_Heavy', 2000, 12000, 14000),
    'MortarTeamArtilleryShell': ('CannonHE_MediumFlatCompatibility', 'CannonHE_Medium', 20000, 60000, 80000),
    'SteelTwisterMissiles': ('MissileAP_MediumFlatCompatibility', 'MissileAP_Medium', 2000, 9000, 11000),
    'wc2arrowFire': ('CannonHE_MediumFlatCompatibility', 'CannonHE_Medium', 4000, 20000, 24000),
    'wc2highArrowFire': ('CannonHE_MediumFlatCompatibility', 'CannonHE_Medium', 4000, 29000, 33000),
}

# Folded scales preserve the baseline runtime percentage units after the flat
# damage is combined. The normal RA2FreedomRocket is handled by the focused tail
# converter; its elite child deliberately remains split because no single scale
# preserves the now-live percentage result within one HP across all active health
# values because of integer quantisation.
PERCENTAGE_SCALES = {
    'TurretGunBlackMarket': 0,
    'ra120mm2': 3332,
    'ReconRangerRecoillessGun': 1210,
    '25mm': 1659,
    'KodiakCannon': 1998,
    'TS70mmTurChem': 3325,
    'TSScoopDualTurChem': 3332,
    'RA2GrandCannonWeapon': 2000,
    'RA2FlakTrackAAGun': 2488,
    'RA2LasherCannon': 1659,
    'AsianLynxTankCannon': 1659,
    'AsianPulverizerMechaGatling': 3317,
    'WhiteRabbitGatling': 1995,
    'SteelDaggerCannon': 3317,
    'SteelCruiserCannons': 2488,
    'RA2LarsRocket': 2488,
    'LatinSmokerCannon': 1810,
    'DiabloCannon': 2488,
    'RA2APCFlakCannon': 2488,
    'LunarTigerCannon': 2494,
    'CannonAttackRobotGun': 3317,
    'FutureMechGatling': 2488,
    '120mm_td': 2499,
    'DeviatorMissile': 3330,
    'DeviatorMissile_Artillery': 1998,
    'HMG_Duelist_upgrade': 0,
    'ScarabLaunch': 2500,
    'AtreusMG': 2488,
    'SCTyr': 2494,
    'GoliathMk2MG': 3317,
    'WyvernRockets': 1422,
    'MortarTeamArtilleryShell': 2499,
    'SteelTwisterMissiles': 1810,
    'wc2arrowFire': 1663,
    'wc2highArrowFire': 1210,
}

# A later reviewed cohort finishes these partial compatibility folds by making
# the compatibility profile the sole canonical main.  Keep this older converter
# idempotent without weakening its checks for any other entry.
FINALIZED_BY_PINNED_ROLE = {
    'AsianPulverizerMechaGatling': (10000, 5990),
    'CannonAttackRobotGun': (8000, 4988),
    'LatinSmokerCannon': (13000, 3070),
    'RA2LarsRocket': (10000, 3990),
    'SteelDaggerCannon': (8000, 4988),
    'WyvernRockets': (16000, 2494),
}

IGNORED_PROFILE_FIELDS = {"Damage", "PercentageScale"}


def flat_nodes(node: Node) -> dict[str, Node]:
    return {
        child.key.split("@", 1)[1]: child
        for child in node.children
        if child.key.startswith("Warhead@")
        and child.value in {"AreaDamage", "SpreadDamage"}
        and "FriendlyFire" not in child.key
    }


def damage(node: Node) -> int:
    return int(str(node.get("Damage") or "0"))


def fingerprint(node: Node) -> tuple:
    return (
        node.value,
        tuple(sorted(
            (child.key, child.value, tuple(sorted(fingerprint(grandchild)
             for grandchild in child.children)))
            for child in node.children
            if child.key not in IGNORED_PROFILE_FIELDS
        )),
    )


def direct_descendants(rs: Ruleset) -> dict[str, set[str]]:
    result: dict[str, set[str]] = collections.defaultdict(set)
    for name, node in rs.weapons.items():
        for _, parent in rs.inherits_of(node):
            if parent in rs.weapons:
                result[parent].add(name)
    return result


def selected_closure(rs: Ruleset) -> set[str]:
    direct = direct_descendants(rs)
    selected: set[str] = set()
    for root, (compatibility, destination, *_damage) in SPECS.items():
        seen: set[str] = set()
        stack = [root]
        while stack:
            name = stack.pop()
            if name in seen:
                continue
            seen.add(name)
            stack.extend(direct[name])
        for name in seen:
            if name.startswith("^"):
                continue
            resolved = rs.resolve_weapon(name)
            if resolved is None:
                continue
            nodes = flat_nodes(resolved)
            if compatibility in nodes and destination in nodes:
                selected.add(name)
    return selected


def validate_source(rs: Ruleset) -> tuple[set[str], bool]:
    if set(SPECS) != set(PERCENTAGE_SCALES):
        raise RuntimeError("source and percentage-scale manifests differ")
    health_values = active_health_values(ROOT)
    converted_states = []
    for name, (compatibility, destination, old_destination,
               old_compatibility, folded) in SPECS.items():
        local = rs.weapon(name)
        resolved = rs.resolve_weapon(name)
        if local is None or resolved is None:
            raise RuntimeError(f"{name}: missing source or resolved weapon")
        nodes = flat_nodes(resolved)
        finalized = (name in FINALIZED_BY_PINNED_ROLE
                     and set(main_warheads(resolved)) == {compatibility})
        if finalized:
            expected_damage, expected_scale = FINALIZED_BY_PINNED_ROLE[name]
            if damage(nodes[compatibility]) != expected_damage:
                raise RuntimeError(f"{name}: final pinned-role damage changed")
            actual_scale = int(str(nodes[compatibility].get("PercentageScale") or "0"))
            if actual_scale != expected_scale:
                raise RuntimeError(f"{name}: final pinned-role scale changed")
            converted_states.append(True)
            continue
        already = compatibility not in nodes and destination in nodes
        baseline = compatibility in nodes and destination in nodes
        if not baseline and not already:
            raise RuntimeError(
                f"{name}: expected {destination} with optional {compatibility}; "
                f"found {sorted(nodes)}")
        if baseline:
            if damage(nodes[destination]) != old_destination:
                raise RuntimeError(f"{name}: canonical damage changed")
            if damage(nodes[compatibility]) != old_compatibility:
                raise RuntimeError(f"{name}: compatibility damage changed")
            if fingerprint(nodes[destination]) != fingerprint(nodes[compatibility]):
                raise RuntimeError(f"{name}: compatibility profile no longer matches canonical")
            if str(nodes[compatibility].get("PercentageScale") or "0") != "0":
                raise RuntimeError(f"{name}: compatibility percentage is no longer inert")
            baseline_apps = {
                hp: sum(
                    int(app["runtime_hp"])
                    for app in pd.percentage_applications(resolved, hp)
                    if app["tag"] in {compatibility, destination}
                )
                for hp in health_values
            }
            units = pd.folded_units(
                folded, PERCENTAGE_SCALES[name])[1]
            for hp, before in baseline_apps.items():
                after = pd.runtime_percentage_hp(
                    hp, units, pd.FOLDED_DEFAULT_DENOMINATOR)
                if abs(before - after) > 1:
                    raise RuntimeError(
                        f"{name}: percentage fold changes {hp} HP target "
                        f"from {before} to {after}")
        else:
            if damage(nodes[destination]) != folded:
                raise RuntimeError(f"{name}: folded damage changed")
            actual_scale = int(str(nodes[destination].get("PercentageScale") or "0"))
            if actual_scale != PERCENTAGE_SCALES[name]:
                raise RuntimeError(
                    f"{name}: expected PercentageScale {PERCENTAGE_SCALES[name]}, "
                    f"found {actual_scale}")
        converted_states.append(already)
    if any(converted_states) and not all(converted_states):
        raise RuntimeError("partial compatibility consolidation detected")
    return selected_closure(rs), all(converted_states)


def _subblock_end(lines: list[str], start: int, weapon_end: int) -> int:
    for index in range(start + 1, weapon_end):
        if lines[index].startswith("\t") and not lines[index].startswith("\t\t") \
                and lines[index].strip():
            return index
    return weapon_end


def rewrite(changed: dict[pathlib.Path, list[str]], path: pathlib.Path,
            weapon: str, compatibility: str, destination: str,
            folded: int, percentage_scale: int) -> None:
    lines = changed.setdefault(
        path, path.read_text(encoding="utf-8-sig").splitlines(True))
    start, end = block_bounds(lines, weapon)
    compatibility_marker = f"\tWarhead@{compatibility}:"
    compatibility_rows = [
        index for index in range(start + 1, end)
        if lines[index].rstrip("\r\n") == compatibility_marker
    ]
    if len(compatibility_rows) != 1:
        raise RuntimeError(
            f"{weapon}: expected one local {compatibility} block, "
            f"found {len(compatibility_rows)}")

    compatibility_start = compatibility_rows[0]
    compatibility_end = _subblock_end(lines, compatibility_start, end)
    lines[compatibility_start:compatibility_end] = [f"\t-Warhead@{compatibility}:\n"]

    start, end = block_bounds(lines, weapon)
    destination_marker = f"\tWarhead@{destination}:"
    destination_rows = [
        index for index in range(start + 1, end)
        if lines[index].rstrip("\r\n") == destination_marker
    ]
    if len(destination_rows) > 1:
        raise RuntimeError(f"{weapon}: duplicate local {destination} blocks")
    if destination_rows:
        destination_start = destination_rows[0]
        destination_end = _subblock_end(lines, destination_start, end)
        damage_rows = [
            index for index in range(destination_start + 1, destination_end)
            if re.match(r"^\t\tDamage:\s*", lines[index])
        ]
        if len(damage_rows) > 1:
            raise RuntimeError(f"{weapon}: duplicate local {destination} Damage rows")
        if damage_rows:
            lines[damage_rows[0]] = f"\t\tDamage: {folded}\n"
        else:
            lines.insert(destination_start + 1, f"\t\tDamage: {folded}\n")
            destination_end += 1
        start, end = block_bounds(lines, weapon)
        destination_start = next(
            index for index in range(start + 1, end)
            if lines[index].rstrip("\r\n") == destination_marker)
        destination_end = _subblock_end(lines, destination_start, end)
        scale_rows = [
            index for index in range(destination_start + 1, destination_end)
            if re.match(r"^\t\tPercentageScale:\s*", lines[index])
        ]
        if len(scale_rows) > 1:
            raise RuntimeError(f"{weapon}: duplicate local PercentageScale rows")
        if scale_rows:
            lines[scale_rows[0]] = f"\t\tPercentageScale: {percentage_scale}\n"
        else:
            lines.insert(destination_start + 1,
                         f"\t\tPercentageScale: {percentage_scale}\n")
    else:
        removal_index = next(
            index for index in range(start + 1, end)
            if lines[index].rstrip("\r\n") == f"\t-Warhead@{compatibility}:")
        lines[removal_index:removal_index] = [
            f"\tWarhead@{destination}:\n",
            f"\t\tDamage: {folded}\n",
            f"\t\tPercentageScale: {percentage_scale}\n",
        ]


def validate_result(expected_closure: set[str]) -> None:
    rs = Ruleset(ROOT)
    closure, already = validate_source(rs)
    if not already:
        raise RuntimeError("conversion did not reach the applied state")
    if closure:
        raise RuntimeError(
            "selected compatibility slices remain after rewrite: "
            + ", ".join(sorted(closure)))
    if expected_closure == closure:
        return


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rules = Ruleset(ROOT)
    closure, already = validate_source(rules)
    if already:
        print(f"Already consolidated {len(SPECS)} source definitions")
        return 0

    print(f"{len(SPECS)} source definitions; {len(closure)} resolved variants")
    if not args.apply:
        print("Dry run: source fingerprints match")
        return 0

    changed: dict[pathlib.Path, list[str]] = {}
    for name, (compatibility, destination, _old_destination,
               _old_compatibility, folded) in SPECS.items():
        local = rules.weapon(name)
        if local is None:
            raise RuntimeError(f"{name}: missing local source")
        rewrite(changed, pathlib.Path(local.file), name,
                compatibility, destination, folded, PERCENTAGE_SCALES[name])
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")
    validate_result(closure)
    print(f"Applied and validated {len(changed)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
