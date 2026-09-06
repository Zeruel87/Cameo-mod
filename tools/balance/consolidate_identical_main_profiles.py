#!/usr/bin/env python3
"""Fold reachable duplicate mains whose complete damage profiles are identical.

This is deliberately narrower than choosing a weapon role.  Each selected group
has the same resolved warhead type and recursively identical fields except for
``Damage`` and the folded ``PercentageScale`` fields.  The flat damage is
summed onto one existing semantic key; every other projectile, effect, target,
relationship, status, and companion warhead remains untouched.

The normal Freedom Rocket is handled by a focused converter that reconstructs
its elite child. The elite remains split because no single scale preserves its
live percentage result within one HP at every active health value. The Syndicate
fireball impact is excluded because its otherwise-identical mains each apply a
physical state, so reducing the number of applications would change behavior.
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

from audit_three_way_split import main_warhead_nodes  # noqa: E402
from consolidate_compatibility_profiles import fingerprint  # noqa: E402
from consolidate_final_safe_cohorts import percentage_scale  # noqa: E402
from consolidate_reviewed_weapon_roots import block_bounds  # noqa: E402
from miniyaml import Ruleset  # noqa: E402


# SELECTED is declared parent-before-child for readability, but apply() walks it
# in reverse so descendants are materialized before their inherited parents are
# consolidated.  The explicit lockdown pins and child-removal reconciliation
# then preserve the intended resolved routes.
SELECTED = {
    "AsianSniper": [("SniperChaingun", {"SniperMediumMissile", "SniperFlak", "SniperChaingun"})],
    "AsianSniperAP": [
        ("SniperChaingun", {"SniperMediumMissile", "SniperFlak", "SniperChaingun"}),
        ("Bullet_Medium", {"Bullet_Light", "Bullet_Medium"}),
    ],
    "AsianSniperLockdown": [
        ("SniperFlak", {"SniperMediumMissile", "SniperFlak"}),
        ("Bullet_Medium", {"Bullet_Light", "Bullet_Medium"}),
    ],
    "FutureEnforcerShotgun": [("ShotgunShrapnelEnemy", {"ShotgunGrenadeEnemy", "ShotgunShrapnelEnemy"})],
    "FutureEnforcerShotgunDeployed": [("ShotgunShrapnelEnemy", {"ShotgunGrenadeEnemy", "ShotgunShrapnelEnemy"})],
    "FutureEnforcerShotgunDeployed_elite": [("ShotgunShrapnelEnemy", {"ShotgunGrenadeEnemy", "ShotgunShrapnelEnemy"})],
    "FutureEnforcerShotgun_elite": [("ShotgunShrapnelEnemy", {"ShotgunGrenadeEnemy", "ShotgunShrapnelEnemy"})],
    "GDISniperRifle": [("SniperChaingun", {"SniperFlak", "SniperChaingun"})],
    "GhostSniper": [("SniperChaingun", {"SniperMediumMissile", "SniperFlak", "SniperChaingun"})],
    "GhostSniperLockdown": [
        ("SniperFlak", {"SniperMediumMissile", "SniperFlak"}),
        ("Bullet_Medium", {"Bullet_Light", "Bullet_Medium"}),
    ],
    "GladiusCannon": [("CannonHE_Heavy", {"CannonAP_Light", "CannonHE_Medium", "CannonHE_Heavy"})],
    "KamovTeslaArcFragment1": [("TeslaWeapon", {"LightMissile", "TeslaWeapon"})],
    "KamovTeslaArcFragment2": [("TeslaWeapon", {"LightMissile", "TeslaWeapon"})],
    "NaxCorrosionRocketTrooper_elite": [("PreservedFlat_HeavyMissile", {"PreservedFlat_Grenade", "PreservedFlat_HeavyMissile"})],
    "PositronBounce1": [("CannonAP_Light", {"Bullet_Light", "CannonAP_Light"})],
    "PositronBounce2": [("CannonAP_Light", {"Bullet_Light", "CannonAP_Light"})],
    "RA2LasherToxicMortar_elite": [("CannonHE_Medium", {"CannonAP_Light", "CannonHE_Medium", "CannonHE_Heavy"})],
    "SandmarineTuskTwin": [("Grenade", {"Grenade", "FlakWeapon"})],
    "SpecterSniper": [("SniperChaingun", {"SniperMediumMissile", "SniperFlak", "SniperChaingun"})],
    "SpecterSniperLockdown": [
        ("SniperFlak", {"SniperMediumMissile", "SniperFlak"}),
        ("Bullet_Medium", {"Bullet_Light", "Bullet_Medium"}),
    ],
    "SteelQuantumCannon_EMP": [("RailgunWeapon", {"LaserWeapon", "RailgunWeapon"})],
    "SteelQuantumCannon_elite": [("RailgunWeapon", {"LaserWeapon", "RailgunWeapon"})],
    "SteelQuantumCannonScatter_elite": [("RailgunWeapon", {"LaserWeapon", "RailgunWeapon"})],
    "TSCommandoShotgun": [("ShotgunShrapnelEnemy", {"ShotgunGrenadeEnemy", "ShotgunShrapnelEnemy"})],
    "TSMutShotgun": [("ShotgunShrapnelEnemy", {"ShotgunGrenadeEnemy", "ShotgunShrapnelEnemy"})],
    "TSShotgun": [("ShotgunShrapnelEnemy", {"ShotgunGrenadeEnemy", "ShotgunShrapnelEnemy"})],
    "VonSniper": [("SniperChaingun", {"SniperMediumMissile", "SniperFlak", "SniperChaingun"})],
    "VonSniperAP": [
        ("SniperChaingun", {"SniperMediumMissile", "SniperFlak", "SniperChaingun"}),
        ("Bullet_Medium", {"Bullet_Light", "Bullet_Medium"}),
    ],
    "VonSniperLockdown": [
        ("SniperFlak", {"SniperMediumMissile", "SniperFlak"}),
        ("Bullet_Medium", {"Bullet_Light", "Bullet_Medium"}),
    ],
    "WaveTurretImpact": [("RailgunWeapon", {"TeslaWeapon", "RailgunWeapon"})],
    "YakTeslaArcFragment1": [("TeslaWeapon", {"LightMissile", "TeslaWeapon"})],
    "YakTeslaArcFragment2": [("TeslaWeapon", {"LightMissile", "TeslaWeapon"})],
}

# Parent sniper folds change the inherited Chaingun amount.  Lockdown variants
# also authored their selected profiles as partial overrides.  Materialize the
# folded enemy-only profile and pin the unrelated Chaingun amount so the parent
# cleanup cannot change either route.
LOCKDOWN_PINS = {
    "AsianSniperLockdown": (64000, 6000),
    "GhostSniperLockdown": (40000, 2000),
    "SpecterSniperLockdown": (80000, 4000),
    "VonSniperLockdown": (64000, 6000),
}

REDUNDANT_CHILD_REMOVALS = {
    "FutureEnforcerShotgun_elite": "ShotgunGrenadeEnemy",
    "FutureEnforcerShotgunDeployed": "ShotgunGrenadeEnemy",
    "FutureEnforcerShotgunDeployed_elite": "ShotgunGrenadeEnemy",
}


def main_nodes(rules: Ruleset, name: str):
    resolved = rules.resolve_weapon(name)
    if resolved is None:
        raise RuntimeError(f"{name}: missing resolved weapon")
    return {node.key.split("@", 1)[-1]: node for node in main_warhead_nodes(resolved)}


def stateful(node) -> bool:
    return any("PhysicalState" in child.key or child.key in {"IntegrityScale", "DamageDuration"}
               for child in node.children)


def local_node_bounds(lines: list[str], name: str, key: str, start: int, end: int):
    pattern = re.compile(r"^\tWarhead@" + re.escape(key) + r":")
    matches = [i for i in range(start + 1, end) if pattern.match(lines[i].rstrip("\r\n"))]
    if len(matches) > 1:
        raise RuntimeError(f"{name}: duplicate local Warhead@{key}")
    if not matches:
        return None
    node_start = matches[0]
    node_end = end
    for i in range(node_start + 1, end):
        if lines[i].startswith("\t") and not lines[i].startswith("\t\t") and lines[i].strip():
            node_end = i
            break
    return node_start, node_end


def set_field(lines: list[str], node_start: int, node_end: int, field: str, value: int):
    rows = [i for i in range(node_start + 1, node_end)
            if lines[i].startswith(f"\t\t{field}:")]
    if len(rows) > 1:
        raise RuntimeError(f"duplicate {field} in selected warhead")
    if rows:
        lines[rows[0]] = f"\t\t{field}: {value}\n"
    else:
        lines.insert(node_end, f"\t\t{field}: {value}\n")


def apply_weapon(name: str, groups) -> int:
    rules = Ruleset(ROOT)
    nodes = main_nodes(rules, name)
    operations = []
    for destination, allowed in groups:
        present = allowed & set(nodes)
        if len(present) < 2:
            continue
        if destination not in present:
            raise RuntimeError(f"{name}: destination {destination} disappeared")
        selected = [nodes[key] for key in sorted(present)]
        if len({fingerprint(node) for node in selected}) != 1:
            raise RuntimeError(f"{name}: selected profiles are no longer identical")
        if any(stateful(node) for node in selected):
            raise RuntimeError(f"{name}: selected profile gained a state hook")
        total = sum(int(str(node.get("Damage") or 0)) for node in selected)
        if percentage_scale(rules.resolve_weapon(name), present, total) != 0:
            raise RuntimeError(f"{name}: selected profile gained folded percentage behavior")
        operations.append((destination, present, total))
    if not operations:
        return 0

    local = rules.weapon(name)
    path = pathlib.Path(local.file)
    lines = path.read_text(encoding="utf-8-sig").splitlines(True)
    start, end = block_bounds(lines, name)
    for destination, present, total in operations:
        bounds = local_node_bounds(lines, name, destination, start, end)
        if bounds is None:
            insertion = end
            while insertion > start + 1 and not lines[insertion - 1].strip():
                insertion -= 1
            payload = [
                f"\tWarhead@{destination}:\n",
                f"\t\tDamage: {total}\n",
                "\t\tPercentageScale: 0\n",
            ]
            lines[insertion:insertion] = payload
            end += len(payload)
        else:
            node_start, node_end = bounds
            before = len(lines)
            set_field(lines, node_start, node_end, "Damage", total)
            end += len(lines) - before
            bounds = local_node_bounds(lines, name, destination, start, end)
            node_start, node_end = bounds
            before = len(lines)
            set_field(lines, node_start, node_end, "PercentageScale", 0)
            end += len(lines) - before

        existing = {
            match.group(1)
            for line in lines[start + 1:end]
            if (match := re.match(r"^\t-Warhead@([^:]+):", line.rstrip("\r\n")))
        }
        removals = [key for key in sorted(present - {destination}) if key not in existing]
        insertion = end
        while insertion > start + 1 and not lines[insertion - 1].strip():
            insertion -= 1
        lines[insertion:insertion] = [f"\t-Warhead@{key}:\n" for key in removals]
        end += len(removals)

    path.write_text("".join(lines), encoding="utf-8", newline="\n")
    return len(operations)


def remaining_groups(rules: Ruleset):
    rows = []
    for name, groups in SELECTED.items():
        nodes = main_nodes(rules, name)
        for destination, allowed in groups:
            present = allowed & set(nodes)
            if len(present) > 1:
                rows.append((name, destination, sorted(present)))
    return rows


def repair_lockdown_pins() -> None:
    for name, (flak_damage, chaingun_damage) in LOCKDOWN_PINS.items():
        rules = Ruleset(ROOT)
        local = rules.weapon(name)
        path = pathlib.Path(local.file)
        lines = path.read_text(encoding="utf-8-sig").splitlines(True)
        start, end = block_bounds(lines, name)
        bounds = local_node_bounds(lines, name, "SniperFlak", start, end)
        if bounds is None:
            raise RuntimeError(f"{name}: folded SniperFlak override is missing")
        node_start, node_end = bounds
        lines[node_start] = "\tWarhead@SniperFlak: AreaDamage\n"
        required = [
            ("Spread", "1"),
            ("Falloff", "100, 0"),
            ("ValidTargets", "Ground, Water, Air"),
            ("ValidRelationships", "Enemy, Neutral"),
            ("FriendlyFireDamage", "100"),
            ("Damage", str(flak_damage)),
            ("PercentageScale", "0"),
        ]
        existing = {
            line.strip().split(":", 1)[0]
            for line in lines[node_start + 1:node_end]
            if line.startswith("\t\t") and ":" in line
        }
        insertion = node_start + 1
        payload = [f"\t\t{field}: {value}\n" for field, value in required
                   if field not in existing]
        lines[insertion:insertion] = payload
        end += len(payload)
        bounds = local_node_bounds(lines, name, "SniperChaingun", start, end)
        if bounds is None:
            insertion = end
            while insertion > start + 1 and not lines[insertion - 1].strip():
                insertion -= 1
            lines[insertion:insertion] = [
                "\tWarhead@SniperChaingun:\n",
                f"\t\tDamage: {chaingun_damage}\n",
            ]
        else:
            node_start, node_end = bounds
            set_field(lines, node_start, node_end, "Damage", chaingun_damage)
        path.write_text("".join(lines), encoding="utf-8", newline="\n")


def remove_redundant_child_removals() -> None:
    rules = Ruleset(ROOT)
    changed = {}
    for name, key in REDUNDANT_CHILD_REMOVALS.items():
        local = rules.weapon(name)
        path = pathlib.Path(local.file)
        lines = changed.setdefault(
            path, path.read_text(encoding="utf-8-sig").splitlines(True))
        start, end = block_bounds(lines, name)
        exact = f"\t-Warhead@{key}:"
        matches = [i for i in range(start + 1, end)
                   if lines[i].rstrip("\r\n") == exact]
        if len(matches) > 1:
            raise RuntimeError(f"{name}: duplicate redundant removal {key}")
        if matches:
            del lines[matches[0]]
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    before = remaining_groups(Ruleset(ROOT))
    if not before:
        if args.apply:
            repair_lockdown_pins()
            remove_redundant_child_removals()
        print(f"Already consolidated {len(SELECTED)} selected definitions")
        return 0
    print(f"{len(before)} identical groups across {len({row[0] for row in before})} definitions")
    if not args.apply:
        print("Dry run; pass --apply to write")
        return 0
    applied = 0
    for name, groups in reversed(SELECTED.items()):
        applied += apply_weapon(name, groups)
    repair_lockdown_pins()
    remove_redundant_child_removals()
    after = remaining_groups(Ruleset(ROOT))
    if after:
        raise RuntimeError(f"selected identical groups remain: {after}")
    print(f"Applied {applied} local consolidations across {len(SELECTED)} selected definitions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
