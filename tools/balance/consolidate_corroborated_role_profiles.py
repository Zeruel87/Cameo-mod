#!/usr/bin/env python3
"""Collapse a reviewed cohort whose single damage role is corroborated.

The selected roots name their delivery family directly (flak, machine gun, or
molotov), or combine that delivery evidence with an existing compatible
profile.  Every selected definition has flat mains with one target/relationship
contract and safely foldable percentage arithmetic.  The Latin Molotov pair
is the sole state-bearing exception: its Temperature contribution is preserved
by scaling the combined Flame main from 100 to 75 percent.

This deliberately excludes the user-pinned Atreus, Epigraph, Goliath, Duelist,
and Ordos autogun roles, plus branches whose names contradict their inherited
family (chemical, rail, mortar, and magnetic variants).
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from audit_three_way_split import main_warheads  # noqa: E402
from consolidate_final_safe_cohorts import (  # noqa: E402
    cleanup_duplicate_template_inherits,
    cleanup_stale_removals,
    ensure_template_inherit,
    flat_main_nodes,
    percentage_scale,
    set_scale,
    tokens,
)
from consolidate_reviewed_weapon_roots import (  # noqa: E402
    add_compatibility_templates,
    apply_compatibility_block,
    block_bounds,
    resolved_flat_total,
)
from miniyaml import Ruleset  # noqa: E402


# root: (destination profile, exact concrete descendant closure, evidence)
ROOTS = {
    "AsianPelicanMG": ("Bullet_Medium", {"AsianPelicanMG_elite"}, "name"),
    "light_inf_lmg_upgrade": ("Bullet_Medium", set(), "name"),
    "FLAK-23-AG": ("Flak_Medium", {"FLAK-23-AA"}, "name"),
    "NaxQuadCannon_AA": (
        "Flak_Medium",
        {
            "NaxFlakAA", "NaxQuadCannon_AA_elite", "PortableFlak",
            "PortableFlak_elite", "SkyMageCannon_AA",
            "SkyMageCannon_AA_elite",
        },
        "name",
    ),
    "SteelMantaHunterCannons_AA": (
        "Flak_Medium",
        {
            "SteelMantaHunterCannonsAAResonance_AA",
            "SteelMantaHunterCannonsAAResonanceBounce1",
            "SteelMantaHunterCannonsAAResonanceBounce2",
        },
        "name",
    ),
    "ra2roktgun": ("Bullet_Medium", {"RA2CosmonautLaser"}, "name"),
    "ManifoldMG": ("Bullet_Medium", {"ManifoldMG_AA"}, "name"),
    "HMG_turret_upgrade": ("Bullet_Medium", set(), "name"),
    "RaiderGuns_upgrade": ("Bullet_Medium", set(), "name"),
    "LatinSentryMG": ("Bullet_Medium", {"LatinSentryMG_elite"}, "name"),
    "RA2CRM60H": ("Bullet_Medium", set(), "name"),
    "RA2FreedomAK47": (
        "Bullet_Medium", {"RA2FreedomAK47_elite"}, "name"),
    "NaxisBlackBombSmaller": ("Demolition_Medium", set(), "name"),
    "AsianMLRS": (
        "MissileAA_Medium", {"AsianSpitfireRockets"}, "existing-roleflat"),
    "harkonnen_autogunturret": ("Bullet_Medium", set(), "name"),
    "SteelCloneGun": (
        "Bullet_Medium",
        {
            "SteelCloneGun_elite", "SteelCloneGunResonance",
            "SteelCloneGunResonance_elite", "SteelCloneGunResonanceBounce1",
            "SteelCloneGunResonanceBounce1_elite",
            "SteelCloneGunResonanceBounce2",
            "SteelCloneGunResonanceBounce2_elite",
        },
        "local-scout-anti-infantry",
    ),
    "NaxiShrek": (
        "MissileAP_Medium", {"NaxiShrek_elite"}, "existing-roleflat"),
    "NaxiShrekCons": (
        "MissileAP_Medium", {"NaxiShrekCons_elite"}, "existing-roleflat"),
    "AsianPulverizerGatling": (
        "Bullet_Medium", {"AsianPulverizerMechaGatling"},
        "reviewed-anti-infantry"),
    "MarineMG": ("Bullet_Medium", set(), "reviewed-anti-infantry"),
    "MadcapGun": ("Bullet_Medium", set(), "reviewed-anti-infantry"),
    "Future_MultiMissile": ("MissileAP_Light", set(), "name"),
    "latinsyndicate_latinmilitia_molotov": (
        "Flame_Light", {"latinsyndicate_latinmilitia_molotov_elite"},
        "molotov-flame-role"),
}

DESTINATION_OVERRIDES = {
    "RA2CosmonautLaser": "Laser_Light",
}

# Exact baseline arithmetic.  These pins make the converter fail closed if a
# selected profile changes before it is applied again.
BASELINE = {
    "AsianPelicanMG": (
        {"Bullet_Light", "Bullet_Medium", "CannonHE_Heavy"}, 6000, 9984),
    "AsianPelicanMG_elite": (
        {"Bullet_Light", "Bullet_Medium", "CannonHE_Heavy"}, 6000, 9984),
    "light_inf_lmg_upgrade": (
        {"Bullet_Light", "Bullet_Medium", "CannonHE_Heavy"}, 6000, 9984),
    "FLAK-23-AG": ({"Bullet_Medium", "Flak_Medium"}, 4000, 9975),
    "FLAK-23-AA": ({"Bullet_Medium", "Flak_Medium"}, 4000, 9975),
    "NaxFlakAA": ({"Flak_Medium", "NaxFlakGroundWater"}, 7000, 2843),
    "NaxQuadCannon_AA": (
        {"Flak_Medium", "NaxFlakGroundWater"}, 7000, 2843),
    "NaxQuadCannon_AA_elite": (
        {"Flak_Medium", "NaxFlakGroundWater"}, 7000, 2843),
    "PortableFlak": ({"Flak_Medium", "NaxFlakGroundWater"}, 7000, 2843),
    "PortableFlak_elite": ({"Flak_Medium", "NaxFlakGroundWater"}, 7000, 2843),
    "SkyMageCannon_AA": (
        {"Flak_Medium", "NaxFlakGroundWater"}, 7000, 2843),
    "SkyMageCannon_AA_elite": (
        {"Flak_Medium", "NaxFlakGroundWater"}, 7000, 2843),
    "SteelMantaHunterCannons_AA": (
        {"Flak_MediumFlatCompatibility", "MissileAP_Medium"}, 6000, 9984),
    "SteelMantaHunterCannonsAAResonance_AA": (
        {"Flak_MediumFlatCompatibility", "MissileAP_Medium"}, 6000, 9984),
    "SteelMantaHunterCannonsAAResonanceBounce1": (
        {"Flak_MediumFlatCompatibility", "MissileAP_Medium"}, 6000, 9984),
    "SteelMantaHunterCannonsAAResonanceBounce2": (
        {"Flak_MediumFlatCompatibility", "MissileAP_Medium"}, 6000, 9984),
    "ra2roktgun": (
        {"Bullet_Medium", "Bullet_MediumFlatCompatibility"}, 8000, 2488),
    "RA2CosmonautLaser": (
        {"Laser_LightFlatCompatibility"}, 13600, 1464),
    "ManifoldMG": (
        {"Bullet_Medium", "CannonHE_Heavy", "Concussion_Light"}, 6000, 9984),
    "ManifoldMG_AA": (
        {"Bullet_Medium", "CannonHE_Heavy", "Concussion_Light"}, 6000, 9984),
    "HMG_turret_upgrade": (
        {"Bullet_MediumFlatCompatibility", "CannonHE_Heavy"}, 6000, 9984),
    "RaiderGuns_upgrade": (
        {"Bullet_MediumFlatCompatibility", "CannonHE_Heavy"}, 6000, 9984),
    "LatinSentryMG": (
        {"Bullet_Light", "Bullet_Medium", "CannonHE_Heavy"}, 6000, 9984),
    "LatinSentryMG_elite": (
        {"Bullet_Light", "Bullet_Medium", "CannonHE_Heavy"}, 6000, 9984),
    "RA2CRM60H": (
        {"Bullet_Medium", "Bullet_MediumFlatCompatibility", "CannonHE_Heavy"},
        6000, 6650),
    "RA2FreedomAK47": (
        {"Bullet_MediumFlatCompatibility", "CannonHE_Heavy"}, 18000, 3328),
    "RA2FreedomAK47_elite": (
        {"Bullet_MediumFlatCompatibility", "CannonHE_Heavy"}, 18000, 3328),
    "NaxisBlackBombSmaller": (
        {"CannonHE_Medium", "Demolition_MediumFlatCompatibility"},
        75000, 2666),
    "AsianMLRS": (
        {"Demolition_Light", "MissileAA_MediumFlatCompatibility",
         "MissileAP_Medium"}, 8000, 4988),
    "AsianSpitfireRockets": (
        {"Demolition_Light", "MissileAA_MediumFlatCompatibility",
         "MissileAP_Medium"}, 16000, 2494),
    "harkonnen_autogunturret": (
        {"Bullet_Light", "Bullet_Medium", "CannonHE_Heavy"}, 6000, 9984),
    "SteelCloneGun": (
        {"Bullet_Light", "CannonHE_Heavy", "MissileAP_Medium"}, 6000, 9984),
    "SteelCloneGun_elite": (
        {"Bullet_Light", "CannonHE_Heavy", "MissileAP_Medium"}, 6000, 9984),
    "SteelCloneGunResonance": (
        {"Bullet_Light", "CannonHE_Heavy", "MissileAP_Medium"}, 6000, 9984),
    "SteelCloneGunResonance_elite": (
        {"Bullet_Light", "CannonHE_Heavy", "MissileAP_Medium"}, 6000, 9984),
    "SteelCloneGunResonanceBounce1": (
        {"Bullet_Light", "CannonHE_Heavy", "MissileAP_Medium"}, 6000, 9984),
    "SteelCloneGunResonanceBounce1_elite": (
        {"Bullet_Light", "CannonHE_Heavy", "MissileAP_Medium"}, 6000, 9984),
    "SteelCloneGunResonanceBounce2": (
        {"Bullet_Light", "CannonHE_Heavy", "MissileAP_Medium"}, 6000, 9984),
    "SteelCloneGunResonanceBounce2_elite": (
        {"Bullet_Light", "CannonHE_Heavy", "MissileAP_Medium"}, 6000, 9984),
    "NaxiShrek": (
        {"MissileAP_Medium", "MissileAP_MediumFlatCompatibility"},
        48000, 1665),
    "NaxiShrek_elite": (
        {"MissileAP_Medium", "MissileAP_MediumFlatCompatibility"},
        48000, 1665),
    "NaxiShrekCons": (
        {"MissileAP_Medium", "MissileAP_MediumFlatCompatibility"},
        36000, 1664),
    "NaxiShrekCons_elite": (
        {"MissileAP_Medium", "MissileAP_MediumFlatCompatibility"},
        36000, 1664),
    "AsianPulverizerGatling": (
        {"Bullet_Light", "Bullet_Medium", "CannonHE_Heavy"}, 6000, 9984),
    "AsianPulverizerMechaGatling": (
        {"Bullet_Light", "Bullet_Medium", "CannonHE_Heavy"}, 10000, 5990),
    "MarineMG": (
        {"Bullet_Light", "Bullet_Medium", "CannonHE_Heavy"}, 36000, 1664),
    "MadcapGun": (
        {"Bullet_Light", "Bullet_Medium", "CannonHE_Heavy"}, 36000, 1664),
    "Future_MultiMissile": (
        {"Arrow_Light", "MissileAP_Light"}, 8000, 9988),
    "latinsyndicate_latinmilitia_molotov": (
        {"Demolition_Light", "Flame_Light"}, 8000, 9988),
    "latinsyndicate_latinmilitia_molotov_elite": (
        {"Demolition_Light", "Flame_Light"}, 8000, 9988),
}

TARGETS = {
    "AsianPelicanMG": "Ground, Water, Air",
    "AsianPelicanMG_elite": "Ground, Water, Air",
    "light_inf_lmg_upgrade": "Ground, Water, Air",
    "FLAK-23-AG": "Ground, Water",
    "FLAK-23-AA": "Air",
    "NaxFlakAA": "Air",
    "NaxQuadCannon_AA": "Air",
    "NaxQuadCannon_AA_elite": "Air",
    "PortableFlak": "Air",
    "PortableFlak_elite": "Air",
    "SkyMageCannon_AA": "Air",
    "SkyMageCannon_AA_elite": "Air",
    "SteelMantaHunterCannons_AA": "Ground, Water, Air",
    "SteelMantaHunterCannonsAAResonance_AA": "Ground, Water, Air",
    "SteelMantaHunterCannonsAAResonanceBounce1": "Ground, Water, Air",
    "SteelMantaHunterCannonsAAResonanceBounce2": "Ground, Water, Air",
    "ra2roktgun": "Ground, Air, Water",
    "RA2CosmonautLaser": "Ground, Water, Air",
    "ManifoldMG": "Ground, Water",
    "ManifoldMG_AA": "Air",
    "HMG_turret_upgrade": "Ground, Water, Air",
    "RaiderGuns_upgrade": "Ground, Water, Air",
    "LatinSentryMG": "Ground, Water, Air",
    "LatinSentryMG_elite": "Ground, Water, Air",
    "RA2CRM60H": "Ground, Water, Air",
    "RA2FreedomAK47": "Ground, Water, Air, Garrisoned",
    "RA2FreedomAK47_elite": "Ground, Water, Air, Garrisoned",
    "NaxisBlackBombSmaller": "Ground, Water",
    "AsianMLRS": "Ground, Water, Air",
    "AsianSpitfireRockets": "Ground, Water, Air",
    "harkonnen_autogunturret": "Ground, Water, Air",
    "SteelCloneGun": "Ground, Water, Air",
    "SteelCloneGun_elite": "Ground, Water, Air",
    "SteelCloneGunResonance": "Ground, Water, Air",
    "SteelCloneGunResonance_elite": "Ground, Water, Air",
    "SteelCloneGunResonanceBounce1": "Ground, Water, Air",
    "SteelCloneGunResonanceBounce1_elite": "Ground, Water, Air",
    "SteelCloneGunResonanceBounce2": "Ground, Water, Air",
    "SteelCloneGunResonanceBounce2_elite": "Ground, Water, Air",
    "NaxiShrek": "Ground, Water",
    "NaxiShrek_elite": "Ground, Water",
    "NaxiShrekCons": "Ground, Water",
    "NaxiShrekCons_elite": "Ground, Water",
    "AsianPulverizerGatling": "Ground, Air, Water",
    "AsianPulverizerMechaGatling": "Ground, Air, Water",
    "MarineMG": "Ground, Water, Air",
    "MadcapGun": "Ground, Water, Air",
    "Future_MultiMissile": "Ground, Water, Air",
    "latinsyndicate_latinmilitia_molotov": "Ground, Water",
    "latinsyndicate_latinmilitia_molotov_elite": "Ground, Water",
}

CANONICAL = re.compile(r"^\^Warhead_([A-Za-z]+)_(\w+)$")
NAX_ALLY_ACCOUNTING = {
    "NaxFlakAA", "NaxQuadCannon_AA", "NaxQuadCannon_AA_elite",
    "PortableFlak", "PortableFlak_elite", "SkyMageCannon_AA",
    "SkyMageCannon_AA_elite",
}
STRIP_EXISTING_COMPATIBILITY_FIELDS = {"RA2CRM60H": {"Spread", "Falloff"}}
CONTRACT_FIELDS = (
    "ValidTargets", "InvalidTargets", "ValidRelationships",
    "InvalidRelationships", "AffectsParent", "TargetActorCenter",
)
TOP_LEVEL_ROUTE_OVERRIDES = {
    "NaxiShrek", "NaxiShrek_elite", "NaxiShrekCons", "NaxiShrekCons_elite",
}
INHERITED_DESTINATION_TEMPLATE = {
    "AsianPulverizerMechaGatling": "Inherits@collapseflat",
}
STATE_SCALE_OVERRIDES = {
    "latinsyndicate_latinmilitia_molotov": 75,
    "latinsyndicate_latinmilitia_molotov_elite": 75,
}


def descendants(rs: Ruleset, root: str) -> set[str]:
    direct: dict[str, set[str]] = {}
    for name, node in rs.weapons.items():
        for _, parent in rs.inherits_of(node):
            if parent in rs.weapons:
                direct.setdefault(parent, set()).add(name)
    seen: set[str] = set()
    stack = list(direct.get(root, set()))
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        stack.extend(direct.get(name, set()))
    return {name for name in seen if not name.startswith("^")}


def selections(rs: Ruleset) -> dict[str, str]:
    selected: dict[str, str] = {}
    for root, (destination, expected, evidence) in ROOTS.items():
        actual = descendants(rs, root)
        if actual != expected:
            raise RuntimeError(
                f"{root}: closure changed; added={sorted(actual - expected)}, "
                f"missing={sorted(expected - actual)}")
        if evidence == "canonical":
            local = rs.weapon(root)
            canonical = {
                "_".join(match.group(1, 2))
                for child in local.children
                if child.key == "Inherits" or child.key.startswith("Inherits@")
                if child.value and (match := CANONICAL.match(str(child.value).strip()))
            }
            if canonical != {destination}:
                raise RuntimeError(
                    f"{root}: expected sole canonical family {destination}; "
                    f"found {sorted(canonical)}")
        elif evidence == "existing-roleflat":
            compatibility = f"^Compatibility_{destination}Flat"
            if not any(str(child.value).strip() == compatibility
                       for child in rs.weapon(root).children
                       if child.key == "Inherits" or child.key.startswith("Inherits@")):
                raise RuntimeError(
                    f"{root}: expected existing {compatibility} role selection")
        elif evidence == "local-scout-anti-infantry":
            actor = rs.actors.get("steelconsortium_clonetrooper")
            buildable = actor.child("Buildable") if actor is not None else None
            description = (
                buildable.get("Description") if buildable is not None else None)
            prioritizes_infantry = actor is not None and any(
                str(child.value).strip() == "^PrioritizeInfantry"
                for child in actor.children
                if child.key == "Inherits" or child.key.startswith("Inherits@")
            )
            if (description != "template_scout_infantry.description"
                    or not prioritizes_infantry):
                raise RuntimeError(
                    f"{root}: Clone Trooper local scout/infantry role changed")
        elif evidence == "reviewed-anti-infantry":
            actor_by_weapon = {
                "AsianPulverizerGatling": "asianalliance_pulverizer",
                "MarineMG": "terran_marine",
                "MadcapGun": "terran_madcap",
            }
            actor_name = actor_by_weapon[root]
            actor = rs.resolve(actor_name)
            armed = actor is not None and any(
                child.key.startswith("Armament")
                and child.get("Weapon") == root
                for child in actor.children)
            if not armed:
                raise RuntimeError(
                    f"{root}: reviewed actor binding for {actor_name} changed")
        elif evidence == "molotov-flame-role":
            actor = rs.resolve("latinsyndicate_latinmilitia")
            bound = actor is not None and any(
                child.key.startswith("Armament")
                and child.get("Weapon") in {root, *expected}
                for child in actor.children)
            if not bound or "molotov" not in root.lower():
                raise RuntimeError(f"{root}: Molotov role evidence changed")
        for name in {root, *expected}:
            if name in selected:
                raise RuntimeError(f"{name}: selected through multiple roots")
            selected[name] = DESTINATION_OVERRIDES.get(name, destination)
    if set(selected) != set(BASELINE) or set(selected) != set(TARGETS):
        raise RuntimeError("selected definition pins are incomplete")
    return selected


def inspect(rs: Ruleset, selected: dict[str, str]):
    plans = {}
    states = set()
    for name, destination in selected.items():
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            raise RuntimeError(f"{name}: missing resolved weapon")
        expected_keys, expected_total, expected_scale = BASELINE[name]
        compatibility = f"{destination}FlatCompatibility"
        mains = set(main_warheads(resolved))
        if mains == {compatibility}:
            states.add(True)
            node = flat_main_nodes(resolved, mains).get(compatibility)
            if node is None:
                raise RuntimeError(f"{name}: missing final compatibility main")
            if int(str(node.get("Damage") or 0)) != expected_total:
                raise RuntimeError(f"{name}: applied flat total changed")
            if int(str(node.get("PercentageScale") or 0)) != expected_scale:
                raise RuntimeError(f"{name}: applied percentage scale changed")
            if str(node.get("ValidTargets") or "") != TARGETS[name]:
                raise RuntimeError(f"{name}: applied target route changed")
            if name in STATE_SCALE_OVERRIDES:
                if (node.get("PhysicalStateName") != "Temperature"
                        or node.get("PhysicalStateScale") !=
                        str(STATE_SCALE_OVERRIDES[name])):
                    raise RuntimeError(f"{name}: Temperature contribution changed")
            if name in NAX_ALLY_ACCOUNTING:
                ally = resolved.child("Warhead@NaxFlakAllyCounted")
                if ally is None or ally.get("Damage") != "1500":
                    raise RuntimeError(f"{name}: allied-fire accounting changed")
            plans[name] = None
            continue

        states.add(False)
        if mains != expected_keys:
            raise RuntimeError(
                f"{name}: expected {sorted(expected_keys)}; found {sorted(mains)}")
        destination_key = (
            destination if destination in mains else compatibility)
        if destination_key not in mains:
            if name not in {
                "SteelCloneGun", "SteelCloneGun_elite",
                "SteelCloneGunResonance", "SteelCloneGunResonance_elite",
                "SteelCloneGunResonanceBounce1",
                "SteelCloneGunResonanceBounce1_elite",
                "SteelCloneGunResonanceBounce2",
                "SteelCloneGunResonanceBounce2_elite",
            }:
                raise RuntimeError(f"{name}: destination {destination} is absent")
            destination_key = sorted(mains)[0]
        nodes = flat_main_nodes(resolved, mains)
        if set(nodes) != mains:
            raise RuntimeError(f"{name}: selected mains are not all flat damage")
        contracts = {
            tuple(tokens(node.get(field)) for field in CONTRACT_FIELDS)
            for node in nodes.values()
        }
        if len(contracts) != 1 and name not in TOP_LEVEL_ROUTE_OVERRIDES:
            raise RuntimeError(f"{name}: selected target contracts differ")
        destination_targets = str(
            nodes[destination_key].get("ValidTargets") or "")
        top_level_targets = str(resolved.get("ValidTargets") or "")
        if (destination_targets != TARGETS[name]
                and not (name in TOP_LEVEL_ROUTE_OVERRIDES
                         and top_level_targets == TARGETS[name])):
            raise RuntimeError(f"{name}: baseline target route changed")
        for key, node in nodes.items():
            state_fields = {
                child.key: str(child.value) for child in node.children
                if "PhysicalState" in child.key
                or child.key in {"IntegrityScale", "DamageDuration"}
            }
            if name in STATE_SCALE_OVERRIDES and key == "Flame_Light":
                if state_fields != {
                        "PhysicalStateName": "Temperature",
                        "PhysicalStateScale": "100"}:
                    raise RuntimeError(f"{name}: Flame state contract changed")
            elif state_fields:
                raise RuntimeError(f"{name}: {key} carries a state hook")
        if name in NAX_ALLY_ACCOUNTING:
            ally = resolved.child("Warhead@NaxFlakAllyCounted")
            if ally is None or ally.get("Damage") != "500":
                raise RuntimeError(f"{name}: baseline allied-fire accounting changed")
        total = resolved_flat_total(resolved, mains)
        if total != expected_total:
            raise RuntimeError(f"{name}: baseline flat total changed")
        scale = percentage_scale(resolved, mains, total)
        if scale != expected_scale:
            raise RuntimeError(f"{name}: folded percentage arithmetic changed")
        plans[name] = {
            "keys": mains,
            "total": total,
            "scale": scale,
            "targets": TARGETS[name],
        }
    return plans, states == {True}


def validate_result() -> None:
    rules = Ruleset(ROOT)
    plans, applied = inspect(rules, selections(rules))
    if not applied or any(plan is not None for plan in plans.values()):
        raise RuntimeError("corroborated-role cohort remains unconsolidated")


def set_nax_ally_accounting(changed: dict[pathlib.Path, list[str]],
                            path: pathlib.Path, weapon: str) -> None:
    """Keep Naxis flak's counted allied damage equal after folding its mains."""
    lines = changed[path]
    start, end = block_bounds(lines, weapon)
    marker = "\tWarhead@NaxFlakAllyCounted:"
    rows = [index for index in range(start + 1, end)
            if lines[index].rstrip("\r\n") == marker]
    if len(rows) > 1:
        raise RuntimeError(f"{weapon}: duplicate allied-fire override")
    if rows:
        block_start = rows[0]
        block_end = end
        for index in range(block_start + 1, end):
            if (lines[index].startswith("\t")
                    and not lines[index].startswith("\t\t")
                    and lines[index].strip()):
                block_end = index
                break
        damage_rows = [
            index for index in range(block_start + 1, block_end)
            if lines[index].strip().startswith("Damage:")
        ]
        if len(damage_rows) != 1 or lines[damage_rows[0]].strip() != "Damage: 500":
            raise RuntimeError(f"{weapon}: unexpected local allied-fire damage")
        lines[damage_rows[0]] = "\t\tDamage: 1500\n"
        return
    insertion = end
    while insertion > start + 1 and not lines[insertion - 1].strip():
        insertion -= 1
    lines[insertion:insertion] = [
        marker + "\n",
        "\t\tDamage: 1500\n",
    ]


def update_existing_compatibility(
        changed: dict[pathlib.Path, list[str]], path: pathlib.Path, weapon: str,
        destination: str, total: int, scale: int, targets: str) -> None:
    """Update a previously materialized compatibility node without duplicating it."""
    lines = changed[path]
    start, end = block_bounds(lines, weapon)
    marker = f"\tWarhead@{destination}FlatCompatibility:"
    rows = [index for index in range(start + 1, end)
            if lines[index].rstrip("\r\n") == marker]
    if len(rows) != 1:
        raise RuntimeError(f"{weapon}: expected one existing compatibility node")
    block_start = rows[0]
    block_end = end
    for index in range(block_start + 1, end):
        if lines[index].startswith("\t") and not lines[index].startswith("\t\t") \
                and lines[index].strip():
            block_end = index
            break
    strip = STRIP_EXISTING_COMPATIBILITY_FIELDS.get(weapon, set())
    for index in reversed(range(block_start + 1, block_end)):
        key = lines[index].strip().split(":", 1)[0]
        if key in strip:
            del lines[index]
            block_end -= 1
    replacements = {
        "ValidTargets": targets,
        "Damage": str(total),
        "PercentageScale": str(scale),
    }
    for key, value in replacements.items():
        matches = [index for index in range(block_start + 1, block_end)
                   if lines[index].strip().startswith(f"{key}:")]
        if len(matches) != 1:
            raise RuntimeError(f"{weapon}: expected one local {key}")
        lines[matches[0]] = f"\t\t{key}: {value}\n"


def remove_local_compatibility_removal(
        changed: dict[pathlib.Path, list[str]], path: pathlib.Path,
        weapon: str, destination: str) -> None:
    """Allow a selected descendant to replace a formerly suppressed profile."""
    if path not in changed:
        changed[path] = path.read_text(encoding="utf-8-sig").splitlines(True)
    lines = changed[path]
    start, end = block_bounds(lines, weapon)
    marker = f"-Warhead@{destination}FlatCompatibility:"
    matches = [
        index for index in range(start + 1, end)
        if lines[index].strip() == marker
    ]
    if len(matches) > 1:
        raise RuntimeError(f"{weapon}: duplicate local compatibility removals")
    if matches:
        del lines[matches[0]]


def set_state_scale(changed: dict[pathlib.Path, list[str]], path: pathlib.Path,
                    weapon: str, destination: str, scale: int) -> None:
    lines = changed[path]
    start, end = block_bounds(lines, weapon)
    marker = f"\tWarhead@{destination}FlatCompatibility:"
    rows = [i for i in range(start + 1, end)
            if lines[i].rstrip("\r\n") == marker]
    if len(rows) != 1:
        raise RuntimeError(f"{weapon}: expected one compatibility override")
    node_start = rows[0]
    node_end = end
    for i in range(node_start + 1, end):
        if lines[i].startswith("\t") and not lines[i].startswith("\t\t") \
                and lines[i].strip():
            node_end = i
            break
    while node_end > node_start + 1 and not lines[node_end - 1].strip():
        node_end -= 1
    field = "\t\tPhysicalStateScale:"
    matches = [i for i in range(node_start + 1, node_end)
               if lines[i].startswith(field)]
    if len(matches) > 1:
        raise RuntimeError(f"{weapon}: duplicate PhysicalStateScale")
    if matches:
        lines[matches[0]] = f"{field} {scale}\n"
    else:
        lines.insert(node_end, f"{field} {scale}\n")


def remove_redundant_local_template(
        changed: dict[pathlib.Path, list[str]], path: pathlib.Path,
        weapon: str) -> None:
    key = INHERITED_DESTINATION_TEMPLATE.get(weapon)
    if key is None:
        return
    lines = changed.setdefault(
        path, path.read_text(encoding="utf-8-sig").splitlines(True))
    start, end = block_bounds(lines, weapon)
    matches = [
        index for index in range(start + 1, end)
        if lines[index].lstrip().startswith(f"{key}:")
    ]
    if len(matches) != 1:
        raise RuntimeError(f"{weapon}: expected one redundant {key}")
    del lines[matches[0]]


def apply_changes(rs: Ruleset, selected: dict[str, str], plans) -> None:
    changed: dict[pathlib.Path, list[str]] = {}
    add_compatibility_templates(changed, rs, set(selected.values()))
    for name in sorted(selected):
        plan = plans[name]
        if plan is None:
            continue
        destination = selected[name]
        local = rs.weapon(name)
        path = pathlib.Path(local.file)
        remove_redundant_local_template(changed, path, name)
        remove_local_compatibility_removal(
            changed, path, name, destination)
        if name not in INHERITED_DESTINATION_TEMPLATE:
            ensure_template_inherit(changed, path, name, destination)
        compatibility = f"{destination}FlatCompatibility"
        local_has_compatibility = any(
            child.key == f"Warhead@{compatibility}" for child in local.children)
        apply_compatibility_block(
            changed, path, name, destination,
            plan["keys"] - {compatibility},
            0 if local_has_compatibility else plan["total"], plan["targets"],
            inherit_template=False)
        if local_has_compatibility:
            update_existing_compatibility(
                changed, path, name, destination, plan["total"],
                plan["scale"], plan["targets"])
        else:
            set_scale(changed, path, name, destination, plan["scale"])
        if name in NAX_ALLY_ACCOUNTING:
            set_nax_ally_accounting(changed, path, name)
        if name in STATE_SCALE_OVERRIDES:
            set_state_scale(
                changed, path, name, destination, STATE_SCALE_OVERRIDES[name])
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")
    cleanup_stale_removals(set(selected))
    cleanup_duplicate_template_inherits(set(selected))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    rules = Ruleset(ROOT)
    selected = selections(rules)
    plans, applied = inspect(rules, selected)
    if applied:
        print(f"Already consolidated {len(selected)} concrete definitions")
        return 0
    print(f"{len(ROOTS)} roots; {len(selected)} concrete definitions")
    if not args.apply:
        print("Dry run: closures, routes, states, and percentage arithmetic pass")
        return 0
    apply_changes(rules, selected, plans)
    validate_result()
    print(f"Applied and validated {len(selected)} concrete definitions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
