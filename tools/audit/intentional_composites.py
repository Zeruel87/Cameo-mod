#!/usr/bin/env python3
"""Exact decision fingerprints for reviewed multi-main weapons.

Review status is classification metadata only.  It must never change the raw
structural inventory.  Every approved weapon is named explicitly and pinned to
its full resolved behavior plus its exact resolved referrers.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import json
import pathlib
from typing import Callable


ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "audit" / "intentional_weapon_composites.json"

WEAPON_REF_FIELDS = {
    "Weapon", "Weapons", "TriggeredWeapon", "FallbackWeapon",
    "EmptyWeapon", "Explosion", "CasingWeapon", "ImpactWeapon",
    "TeleportWeapon", "DemolishWeapon", "HelixWeapon", "TriggerWeapon",
    "ThumpDamageWeapon", "DetonationWeapon", "MissileWeapon",
}
WEAPON_REF_MAP_FIELDS = {"MissileWeapons"}

# Curated decisions.  Every row expands to exact concrete names; no patterns,
# inheritance templates, or wildcard approval are permitted.
DECISION_GROUPS = {
    "staged superweapon": (
        (("ExecutionerDeath", "HermitExplode", "MiniNova", "MiniNuke",
          "RA2DemoBomb", "ReactorNuke", "ReactorNukeWeak"),
         ("10Dam_areanuke3", "11Dam_areanuke3", "1Dam_impact",
          "4Dam_areanuke1", "7Dam_areanuke2", "8Dam_areanuke2", "Damage")),
        (("CabalMagicNuke",),
         ("10Dam_areanuke3", "11Dam_areanuke3", "1Dam_impact",
          "4Dam_areanuke1", "7Dam_areanuke2", "8Dam_areanuke2",
          "Tesla_Heavy", "Tesla_Super")),
        (("PulseMissile",),
         ("10Dam_areanuke3", "11Dam_areanuke3", "1Dam_impact",
          "4Dam_areanuke1", "7Dam_areanuke2", "8Dam_areanuke2",
          "Tesla_Super")),
        (("supernova_missile_super",),
         ("10Dam_areanukec", "1Dam_impact", "3Dam_areanukea",
          "7Dam_areanukeb")),
        (("Atomic", "NaxiV1Rocket", "RA2Atomic", "RAAtomic"),
         ("Nuclear_Super", "Tesla_Super")),
        (("SteelInspectorIonCannon", "SteelInspectorIonCannonDamage"),
         ("IonCannon", "Tesla_Heavy", "Tesla_Super")),
        (("SteelIonCannonDamage", "TDIonCannonDamage"),
         ("IonCannon", "Tesla_Super")),
        (("AsianTSIonCannon", "TSIonCannon"),
         ("IonCannon", "TeslaChargedWeapon", "TeslaWeapon",
          "Tesla_Super")),
    ),
    "status payload": (
		(("Lunar_GreenGrilleArty", "Lunar_GreenGrilleArty_elite"),
		 ("CannonHE_Heavy", "Tesla_Heavy")),
		(("Lunar_GreenSturmArty",), ("Demolition_Heavy", "Tesla_Heavy")),
		(("SkyHawkPlasmaCannon",), ("CannonAP_Light", "Tesla_Heavy")),
		(("RA160mmE_rad_elite",),
		 ("Chemical_LightFlatCompatibility", "Nuclear_Super")),
		(("SandmarineTuskFire",),
		 ("Flame_Light", "MissileAP_Light", "MissileHE_HeavyFlatCompatibility")),
		(("TSChem120mmx",), ("CannonChem_Heavy", "CannonHE_Medium")),
        (("edenTiger_EMP", "edenTiger_EMP_AA", "eden_EMP", "eden_EMP_AA",
          "eden_EMP_GP", "plymouth_EMP", "plymouth_EMP_Tiger"),
         ("TemperatureCompatibility", "Tesla_Super")),
        (("SteelAirTurretEScatter", "SteelAirTurret_EMP", "SteelAirTurret_elite",
          "SteelStalkerRailgunEScatter", "SteelStalkerRailgun_EMP",
          "SteelStalkerRailgun_elite"),
         ("Quantum_HeavyFlatCompatibility", "Tesla_Heavy")),
        (("EMPGrenade",),
         ("TemperatureCompatibility", "TeslaSharedCompatibility", "Tesla_Super")),
        (("EMPGrenadeExplode",),
         ("TemperatureCompatibility", "TeslaAirCompatibility",
          "TeslaSharedCompatibility", "Tesla_Super")),
        (("AsianSniperLockdown", "GhostSniperLockdown", "SpecterSniperLockdown",
          "VonSniperLockdown"),
         ("Bullet_Heavy", "Bullet_Medium", "SniperChaingun", "SniperFlak",
          "SniperSmallArms", "Tesla_Super")),
        (("KodiakCannonSonic",), ("CannonHE_Heavy", "Sonic_Heavy")),
        (("TSGrenadeSonic",), ("Concussion_Light", "Sonic_Light")),
        (("TSBombSonic",), ("Demolition_HeavyFlatCompatibility", "Sonic_Heavy")),
        (("TSHellfireSonic",), ("MissileAP_Heavy", "Sonic_Medium")),
        (("TSZoneHellfireSonic",), ("MissileAP_Heavy", "Sonic_Heavy")),
        (("AphidCryo_AA", "HellfireCryo"),
         ("CryoBlast_Medium", "MissileCryo_Heavy")),
        (("ChemRockets", "ChemRocketsExplosion"),
         ("ChemRocketCompatibility", "Chemical_Light")),
        (("MigMissiles_rad", "MigMissiles_rad_elite"),
         ("Chemical_Medium", "MissileAP_Medium")),
        (("RA2KirovBomb_rad", "TSCropBombChem", "TSLocustBombChem"),
         ("Chemical_Heavy", "Demolition_Heavy")),
        (("RA2KirovBomb_nuclear", "RA2KirovBomb_nuclear_elite"),
         ("Demolition_Heavy", "Nuclear_Super")),
        (("RA2KirovBomb_tesla",), ("Demolition_Heavy", "Tesla_Super")),
        (("AsianChaosMine",), ("CannonAP_Light", "Chemical_Heavy")),
        (("LaserObeliskBurning",), ("Inferno_Heavy", "Laser_Heavy")),
        (("RA2LasherToxicMortar_elite",),
         ("CannonChem_MediumFlatCompatibility", "CannonHE_Medium")),
        (("VolkovMagneticWeapon",),
         ("CannonHE_Heavy", "Railgun_HeavyFlatCompatibility")),
        (("VolkovMagneticWeaponIncendiary",),
         ("CannonHE_Heavy", "Flame_Medium", "Railgun_HeavyFlatCompatibility")),
        (("VolkovMagneticWeaponIncendiaryNuclearShells",),
         ("CannonHE_Heavy", "CannonNuke_HeavyFlatCompatibility", "Grenade",
          "MediumChemicalWeapon")),
        (("VolkovMagneticWeaponIncendiaryTesla",),
         ("CannonHE_Heavy", "Grenade", "MediumChemicalWeapon",
          "Quantum_HeavyFlatCompatibility")),
        (("VolkovMagneticWeaponIncendiaryTeslaFragment1",
          "VolkovMagneticWeaponIncendiaryTeslaFragment2"),
         ("CannonHE_Heavy", "MediumFlameWeapon",
          "Railgun_HeavyFlatCompatibility", "Tesla_Heavy")),
        (("VolkovMagneticWeaponNuclearShells",),
         ("CannonHE_Heavy", "Nuclear_Super", "Railgun_HeavyFlatCompatibility")),
        (("VolkovMagneticWeaponTesla", "VolkovMagneticWeaponTeslaFragment1",
          "VolkovMagneticWeaponTeslaFragment2"),
         ("CannonHE_Heavy", "Railgun_HeavyFlatCompatibility", "Tesla_Heavy")),
        (("DredMissile", "RA2SCUD", "RA2SCUD_fire", "RA2SCUD_tesla",
          "V3Explode"),
         ("Demolition_Light", "MissileAP_Heavy",
          "RA2SCUDMissileAP_Heavy_NoWall")),
        (("RA2SCUDELITE",),
         ("Demolition_Light", "MissileAP_Heavy", "Nuclear_Super",
          "RA2SCUDMissileAP_Heavy_NoWall")),
        (("RA2SCUD_rad",),
         ("Demolition_Light", "MissileAP_Heavy",
          "MissileChem_HeavyFlatCompatibility", "RA2SCUDMissileAP_Heavy_NoWall")),
        (("SCUD",), ("Flame_Heavy", "MissileHE_Heavy")),
        (("SCUDTesla",),
         ("Flame_Heavy", "HeavyFlameWeapon", "HeavyMissile",
          "MissileHE_Heavy", "Tesla_Heavy")),
        (("SCUDThermobaric",),
         ("Demolition_Heavy", "Flame_Heavy", "HeavyFlameWeapon",
          "HeavyMissile", "MissileHE_Heavy")),
        (("AsianPhoenixRocket", "AsianPhoenixRocket_elite"),
         ("Demolition_Light", "Flame_Medium", "MissileAP_Heavy")),
        (("ConsortiumMissileSystem",),
         ("Flak_Medium", "MissileAA_MediumFlatCompatibility",
          "MissileAP_Medium")),
        (("ConsortiumMissileSystem_EMP",),
         ("Flak_Medium", "MissileAP_Medium",
          "MissileQuantum_MediumFlatCompatibility")),
        (("FutureHarbingerCannon", "FutureHarbingerCannon_elite"),
         ("CannonHE_Heavy", "Plasma_HeavyFlatCompatibility")),
        (("RA2Comet", "RA2Comet_elite"),
         ("Demolition_Light", "Flame_Medium", "Laser_Heavy")),
        (("WaveTurretImpact",),
         ("RailgunWeapon", "Railgun_Heavy", "Tesla_Heavy")),
        (("MedicFlare",),
         ("MediumChemicalWeapon", "PreservedFlat_FlakWeapon",
          "PreservedFlat_LaserWeapon", "PreservedFlat_LightFlameWeapon")),
        (("TSLaserObeliskLaserFire", "TSObeliskLaserFire"),
         ("CannonAP_Light", "Laser_Heavy")),
        (("YakTeslaBomb",),
         ("PreservedFlat_HeavyBomb", "PreservedFlat_HeavyChemicalWeapon",
          "PreservedFlat_HeavyFlameWeapon", "PreservedFlat_TeslaWeapon")),
        (("tkmfirerockets",), ("Flame_Light", "MissileAP_Light")),
        (("tkmkatyushalalauncherrocketsfire",),
         ("Concussion_Medium", "Flame_Light", "MissileAP_Light")),
        (("tkmstrykerfirerockets",),
         ("Flame_Medium", "MissileAP_Medium")),
        (("wc2deathknightDeathCoil", "wc2deathknightDeathCoilScatter_Left",
          "wc2deathknightDeathCoilScatter_Right", "wc2deathknightFire"),
         ("Flame_Heavy", "Tesla_Super")),
        (("RA2Robotmm", "RA2RobotmmScatter_elite", "RA2Robotmm_elite"),
         ("Laser_Heavy", "Railgun_Heavy", "Tesla_Heavy")),
        (("BCLaser",), ("CannonHE_Heavy", "Laser_HeavyFlatCompatibility")),
        (("BCYamatoCannon",),
         ("CannonHE_Heavy", "Plasma_HeavyFlatCompatibility")),
        (("RA2120xmm_rad", "RA2120xmm_rad_elite"),
         ("CannonAP_Light", "CannonChem_HeavyFlatCompatibility",
          "CannonHE_Heavy")),
        (("TTankZap2ArcTeslaFragment1_EMP",
          "TTankZap2ArcTeslaFragment2_EMP"),
         ("TeslaWeapon", "Tesla_Super")),
        (("plymouthStickyDefence",),
         ("CannonHE_Heavy", "CannonHE_Medium", "Chemical_Light",
          "StickyWildcardCompatibility")),
        (("plymouthStickyTiger",),
         ("CannonHE_Medium", "Chemical_Light", "StickyWildcardCompatibility")),
        (("HMGo_upgrade",),
         ("Bullet_Light", "Bullet_Medium", "Laser_Heavy")),
        (("HMGstealth_upgrade",),
         ("Bullet_MediumFlatCompatibility", "Laser_Heavy")),
        (("Laboratory_Bioball",),
         ("CannonHE_Heavy", "Chemical_Medium", "Concussion_Medium",
          "Demolition_Light")),
        (("Lunar_GreenTigerCannon", "Lunar_GreenTigerCannon_elite"),
         ("CannonHE_Medium", "Tesla_Heavy")),
        (("OIBigPlasmaCannon",),
         ("CannonHE_Heavy", "Railgun_Heavy", "Tesla_Heavy")),
        (("PositronBounce1", "PositronBounce2"),
         ("CannonAP_Light", "CannonHE_Medium",
          "Quantum_MediumFlatCompatibility")),
        (("RA2DiskDrain",), ("Magic_Heavy", "Tesla_Heavy")),
        (("SteelMegaSword_elite",),
         ("Quantum_HeavyFlatCompatibility", "Railgun_Heavy")),
        (("ViperMissilesFire",),
         ("Concussion_Medium", "Flame_Light", "MissileAP_Light",
          "MissileAP_Medium")),
        (("WaveforceCannonDistortedBeam2",),
         ("Chemical_Heavy", "Flame_Heavy")),
        (("edenMobileLaserTiger",),
         ("CannonHE_Medium", "Laser_Heavy")),
        (("ExplosiveDebris",),
         ("Demolition_Light", "Flame_Light")),
        (("SyndicateFireballLauncherExplode",),
         ("PreservedFlat_Flame_Heavy", "PreservedFlat_Flame_Light",
          "PreservedFlat_Flame_Medium", "PreservedFlat_HeavyFlameWeapon",
          "PreservedFlat_LightFlameWeapon",
          "PreservedFlat_MediumFlameWeapon")),
    ),
    "target-routed composite": (
		(("ArmoredCarMGAAWaveforce",), ("Bullet_Medium", "Railgun_Heavy")),
		(("Future_Cryocopter_Rocket",),
		 ("FutureCryocopterMissileAP_Medium", "MissileAP_MediumFlatCompatibility")),
		(("GLBarrelExplode",), ("1Dam", "Demolition_HeavyFlatCompatibility")),
		(("RashidanGun_upgrade",),
		 ("Bullet_MediumFlatCompatibility", "RashidanGroundCompatibility")),
        (("FutureEnforcerShotgun", "FutureEnforcerShotgunDeployed",
          "FutureEnforcerShotgunDeployed_elite", "FutureEnforcerShotgun_elite",
          "TSCommandoShotgun", "TSMutShotgun", "TSShotgun"),
         ("CannonHE_Medium", "ShotgunChaingun", "ShotgunShrapnelEnemy",
          "ShotgunSmallArms", "ShotgunTankDestroyer")),
        (("AsianSniper", "GDISniperRifle", "GhostSniper", "SpecterSniper",
          "VonSniper"),
         ("Bullet_Heavy", "SniperChaingun", "SniperSmallArms")),
        (("AsianSniperAP", "VonSniperAP"),
         ("Bullet_Heavy", "Bullet_Medium", "SniperChaingun", "SniperSmallArms")),
        (("CommandoSniper",), ("Bullet_Heavy", "SniperChaingun")),
        (("CommandoM16",), ("Bullet_Medium", "SniperCompatibility")),
        (("td_gdi_commando_sniper_elite",), ("Railgun_Heavy", "Sniper_Light")),
        (("ArcherArtilleryShell", "ArtilleryShellUpgrade", "wc2catapultFire"),
         ("CollapseTargetCompatibility1", "Concussion_Heavy")),
        (("BallistaMultiShot", "BallistaTowerMultiShot"),
         ("Arrow_Medium", "CollapseTargetCompatibility1")),
        (("wc2_dwarf_Rifle",), ("Bullet_Medium", "CollapseTargetCompatibility1")),
        (("D2K_155mm2",), ("CannonHE_Heavy", "CollapseTargetCompatibility1")),
        (("eye_bomberguy",), ("CollapseTargetCompatibility1", "Demolition_Heavy")),
        (("BikeRockets",), ("CollapseTargetCompatibility1", "MissileAP_Medium")),
        (("v1rocketsThermobaric",),
         ("CollapseTargetCompatibility1", "Thermobaric_Heavy")),
        (("DRPlasmaTankWeapon",), ("1Dam", "1DamBuildings")),
        (("PLYMineExplosive",), ("1Dam", "2Dam")),
        (("SaboDeath",), ("1Dam", "EnemyDam")),
        (("SonicZap",), ("ExtraSquidDamage", "Magic_Heavy")),
        (("ATMine",), ("ATMineDemolition_Light", "Demolition_Light")),
        (("TSLaser90mm", "TSLaser90mmDep"),
         ("CannonAP_Medium", "TSLaserCannonAP_Medium", "TSLaserShieldChip")),
        (("TSCABALEnlightedLaser", "TSCABALObeliskLaserFire"),
         ("CabalLaserGroundCompatibility", "Laser_Heavy")),
        (("BlackHandLaser",), ("LaserHeavyGroundRemainder", "Laser_Heavy")),
        (("TSProton",), ("Laser_Heavy", "ProtonLaserGroundCompatibility")),
        (("CabalAscendedRockets",),
         ("MissileHE_Heavy", "MissileHE_HeavyGroundBonus")),
        (("NodTorpTube", "TorpTube"), ("Concussion_Light", "MissileHE_Heavy")),
        (("NodTorpTubeBlackMarket",), ("Demolition_Heavy", "MissileHE_Heavy")),
        (("Fremen_RPG", "mtank_pri"), ("1Dam", "MissileAP_Heavy")),
        (("ordos_airmine",), ("1Dam", "MissileAP_HeavyFlatCompatibility")),
        (("RA2Virusgun2",), ("Flak_Medium", "Sniper_LightFlatCompatibility")),
        (("RA2Virusgun3", "RA2Virusgun_elite"),
         ("Flak_Medium", "MissileAP_Medium", "Sniper_LightFlatCompatibility")),
        (("AAGunBoatFlak", "AAGunBoatFlak_elite"),
         ("Flak_Medium", "Flak_MediumFlatCompatibility")),
        (("FutureTankCannons", "FutureTankCannons_elite"),
         ("CannonHE_Heavy", "CannonHE_HeavyFlatCompatibility")),
        (("JapanMaidenBowEnergized",),
         ("Arrow_Light", "Arrow_LightFlatCompatibility", "CannonHE_Medium")),
        (("BallistaSingleShotAirEnergized",),
         ("Arrow_Light", "Arrow_LightFlatCompatibility", "CannonHE_Medium",
          "MissileAP_Light")),
        (("ShotgunAttackRobotGun", "ShotgunAttackRobotGun_elite"),
         ("Bullet_LightFlatCompatibility", "Bullet_Medium",
          "CannonHE_Medium")),
        (("SkyHawkChainGun",), ("Bullet_Medium", "Demolition_Light")),
        (("SkyHawkChainGunWaveforce",),
         ("Bullet_Medium", "Demolition_Light", "Railgun_Heavy")),
        (("japan_imperialscoutsman_rifle",),
         ("Bullet_Medium", "RailgunCompatibility", "RailgunShieldCompatibility")),
        (("japan_imperialscoutsman_rifle_waveforce",),
         ("Bullet_Medium", "RailgunCompatibility", "RailgunShieldCompatibility",
          "Railgun_Heavy")),
        (("SamuraiBladeCharged",),
         ("PreservedFlat_SwordWeapon", "PreservedFlat_TeslaWeapon")),
        (("TSRPGTowerRail",),
         ("CannonHE_Heavy", "Railgun_HeavyFlatCompatibility")),
        (("TankBusterBeamCannon",),
         ("Railgun_Heavy", "TankBusterBeamUnscopedCompatibility")),
    ),
    "percentage-scope compatibility": (
        (("RA2FreedomRocket_elite",),
         ("MissileAP_Medium", "MissileAP_MediumFlatCompatibility")),
    ),
    "effect-delivery composite": (
        (("ZeroFighterChainGunWaveforce",),
         ("Bullet_Medium", "Railgun_Heavy", "ZeroFighterBullet_Medium")),
        (("ArmoredCarMGWaveforce",), ("Bullet_Medium", "Railgun_Heavy")),
        (("JapaneseHovercraftFlakAAkWaveforce", "JapaneseHovercraftFlakWaveforce"),
         ("Flak_MediumFlatCompatibility", "Railgun_Heavy")),
        (("WaveforceCannon", "WaveforceCannonChargedLaser"),
         ("MissileHE_Heavy", "Railgun_Heavy")),
        (("WaveArtilleryImpact",), ("Railgun_Heavy", "Tesla_Heavy")),
        (("Rammax_Sabot",),
         ("PreservedFlat_Chaingun", "PreservedFlat_LaserWeapon",
          "PreservedFlat_TeslaWeapon")),
    ),
    "maintainer-approved role blend": (
		(("SandmarineTuskTwin",),
		 ("Bullet_Medium", "Concussion_Medium", "Grenade",
		  "MissileAP_Medium", "MissileHE_Heavy")),
		(("ordos_autogunturret",),
		 ("Bullet_Light", "Bullet_Medium", "CannonHE_Heavy")),
        (("AtreusMG",), ("Bullet_Medium", "CannonHE_Heavy")),
        (("EpigraphMG",),
         ("Bullet_MediumFlatCompatibility", "CannonHE_Heavy")),
        (("GoliathMG",),
         ("Bullet_Medium", "CannonHE_Heavy", "Concussion_Light")),
        (("GoliathMk2MG",), ("Bullet_Medium", "CannonHE_Heavy")),
        (("DuelistTankCannon",),
         ("CannonHE_Heavy", "PreservedFlat_Grenade",
          "PreservedFlat_HeavyBomb", "PreservedFlat_MediumFlameWeapon",
          "PreservedFlat_TankDestroyerCannon")),
        (("HMG_Duelist_upgrade",), ("Bullet_Medium", "CannonHE_Heavy")),
        (("autogun_tank", "autogun_tank_small"),
         ("Bullet_MediumFlatCompatibility", "CannonHE_Heavy",
          "MissileAP_Heavy")),
    ),
    "maintainer-curated signature": (
        (("IxianCombatTankCannon", "HeavyIxianCombatTankCannon"),
         ("CannonAP_Light", "CannonHE_Heavy")),
        (("D2K_Rocket_Trooper1", "D2K_Rocket_Trooper_AA"),
         ("Flak_Medium", "MissileAP_Heavy", "MissileAP_Light")),
        (("D2K_Rocket_Trooper2", "D2K_Rocket_Trooper_AGOnly"),
         ("CannonHE_Medium", "Demolition_Light", "Railgun_Heavy")),
    ),
}


def digest(value) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def node_payload(node):
    children = [node_payload(child) for child in node.children]
    children.sort(key=lambda value: json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    return {
        "children": children,
        "key": str(node.key),
        "value": "" if node.value is None else str(node.value),
    }


def walk_with_path(node, path=()):
    for child in node.children:
        child_path = path + (str(child.key),)
        yield child, child_path
        yield from walk_with_path(child, child_path)


def referenced_values(node):
    for child, path in walk_with_path(node):
        field = child.key.split("@", 1)[0]
        values = []
        if field in WEAPON_REF_FIELDS and child.value:
            values.append(child.value)
        elif field in WEAPON_REF_MAP_FIELDS:
            if child.value:
                values.append(child.value)
            values.extend(
                descendant.value for descendant, _ in walk_with_path(child)
                if descendant.value)
        for raw in values:
            for value in str(raw).split(","):
                if value.strip():
                    yield value.strip(), "/".join(path)


def resolved_referrer_index(rules):
    """Resolve every actor/weapon once and index its weapon references."""
    rows = {}
    for kind, definitions, resolver in (
            ("actor", rules.actors, rules.resolve),
            ("weapon", rules.weapons, rules.resolve_weapon)):
        for name in sorted(definitions):
            if name.startswith("^"):
                continue
            resolved = resolver(name)
            if resolved is None:
                continue
            for value, path in referenced_values(resolved):
                if kind == "weapon" and name.lower() == value.lower():
                    continue
                rows.setdefault(value.lower(), []).append(
                    {"kind": kind, "name": name, "path": path})
    return {
        name: sorted(referrers, key=lambda row: (
            row["kind"], row["name"], row["path"]))
        for name, referrers in rows.items()
    }


def resolved_referrers(rules, weapon_name: str):
    return resolved_referrer_index(rules).get(weapon_name.lower(), [])


@functools.lru_cache(maxsize=1)
def load_manifest():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("entries"), dict):
        raise ValueError("unsupported intentional-composite manifest schema")
    return data


@functools.lru_cache(maxsize=1)
def reviewed_fingerprints():
    return {
        name: tuple(entry["mains"])
        for name, entry in load_manifest()["entries"].items()
    }


def intentional_composite(name: str, mains: list[str]) -> bool:
    return reviewed_fingerprints().get(name) == tuple(sorted(mains))


_VALIDATED_PREDICATES = {}


def validated_reviewed_predicate(rules, main_nodes: Callable):
    """Return a review predicate only after all live decision evidence validates."""
    key = id(rules)
    cached = _VALIDATED_PREDICATES.get(key)
    if cached is not None and cached[0] is rules:
        return cached[1]
    errors = validate_manifest(rules, main_nodes)
    if errors:
        raise ValueError(
            "intentional composite registry is stale or invalid:\n- "
            + "\n- ".join(errors))
    fingerprints = reviewed_fingerprints()

    def predicate(name: str, mains: list[str]) -> bool:
        return fingerprints.get(name) == tuple(sorted(mains))

    _VALIDATED_PREDICATES[key] = (rules, predicate)
    return predicate


def clear_validation_cache() -> None:
    """Test helper: force the next consumer to revalidate the live registry."""
    _VALIDATED_PREDICATES.clear()


CATEGORY_RATIONALES = {
    "staged superweapon": (
        "retains separately authored damage or effect stages whose timing, radius, "
        "or damage family makes each stage part of one superweapon impact"
    ),
    "status payload": (
        "retains its primary delivery damage and separately authored status or "
        "special-damage payload"
    ),
    "target-routed composite": (
        "retains distinct target, relationship, armor, or physical-state routes "
        "rather than treating the mains as interchangeable damage copies"
    ),
    "percentage-scope compatibility": (
        "retains separately authored fixed and percentage-scaled damage slices "
        "whose integer runtime applications are not interchangeable"
    ),
    "effect-delivery composite": (
        "retains a conventional impact together with a separately authored energy "
        "or Waveforce effect payload delivered on the same shot"
    ),
    "maintainer-approved role blend": (
        "retains the exact mixed armor profile that implements the maintainer's "
        "approved unit role instead of forcing that role into one canonical family"
    ),
    "maintainer-curated signature": (
        "retains the exact multi-layer D2K weapon identity named by the binding "
        "two-warhead-cap exception"
    ),
}

CATEGORY_REFERENCES = {
    "staged superweapon": "Resolved family review: authored stage timing and geometry",
    "status payload": "Resolved family review: primary hit plus status payload",
    "target-routed composite": "Resolved family review: target and armor routing",
    "percentage-scope compatibility": (
        "Resolved family review: fixed and percentage-scaled compatibility slices"
    ),
    "effect-delivery composite": "Resolved family review: overlapping effect delivery",
    "maintainer-approved role blend": (
        "Maintainer decision: retain the unit's current mixed combat role"
    ),
    "maintainer-curated signature": (
        "Maintainer design: WEAPON_3WAY_SPLIT two-warhead-cap exception allow-list"
    ),
}

CATEGORY_OVERLAP = {
    "staged superweapon": (
        "Any shared target route is intentional because the separately authored "
        "timing, radius, or damage family makes this a staged impact."
    ),
    "status payload": (
        "Overlap on the struck target is intentional: the delivery hit and status "
        "payload are both meant to apply."
    ),
    "target-routed composite": (
        "This is not a blanket overlap waiver; the exact components are retained "
        "for their distinct target, relationship, armor, or state routes."
    ),
    "percentage-scope compatibility": (
        "Overlap is intentional and limited to the exact fixed and percentage-scaled "
        "applications whose separate integer rounding is behaviorally significant."
    ),
    "effect-delivery composite": (
        "Overlap is intentional: the special energy or Waveforce payload is "
        "delivered together with the conventional impact."
    ),
    "maintainer-approved role blend": (
        "Overlap is intentional and limited to this exact weapon: each authored "
        "armor contribution is part of the approved broad unit role."
    ),
    "maintainer-curated signature": (
        "Overlap is intentional and limited to the exact D2K signature layers "
        "named by the maintainer-curated exception."
    ),
}

ROLE_BLEND_DECISIONS = {
    "SandmarineTuskTwin": {
        "component_purposes": {
            "Bullet_Medium": "close anti-infantry and light-target part of the twin salvo",
            "Concussion_Medium": "broad conventional blast part of the twin salvo",
            "Grenade": "separate grenade geometry in the generalist ground impact",
            "MissileAP_Medium": "anti-vehicle part of the generalist ground impact",
            "MissileHE_Heavy": "heavy explosive core of the twin missile salvo",
        },
        "rationale": (
            "The maintainer approved Sand Marine and Big Shiee as intentional "
            "generalist ground super-units; preserve the exact five-part ground profile."
        ),
        "review_reference": (
            "Maintainer decision: preserve Sand Marine and Big Shiee generalist ground role"
        ),
    },
    "ordos_autogunturret": {
        "component_purposes": {
            "Bullet_Light": "light-bullet contribution to anti-infantry defense",
            "Bullet_Medium": "medium-bullet contribution against infantry and light vehicles",
            "CannonHE_Heavy": "limited heavier impact that keeps the turret from being helpless",
        },
        "rationale": (
            "The maintainer approved the Ordos autogun family as anti-infantry and "
            "light-vehicle firepower that remains mediocre against heavier vehicles."
        ),
        "review_reference": (
            "Maintainer decision: preserve the Ordos autogun role across its inherited variants"
        ),
    },
    "AtreusMG": {
        "component_purposes": {
            "Bullet_Medium": "retained authored bullet component of the accepted Atreus profile",
            "CannonHE_Heavy": "retained authored heavy-impact component of the accepted Atreus profile",
        },
        "rationale": (
            "The maintainer accepted the current Protoss Atreus behavior as-is; "
            "preserve its exact two-part armor and blast profile."
        ),
        "review_reference": "Maintainer unit decision: Protoss Atreus is good enough as authored",
    },
    "EpigraphMG": {
        "component_purposes": {
            "Bullet_MediumFlatCompatibility": (
                "retained authored bullet component of the accepted Epigraph profile"
            ),
            "CannonHE_Heavy": "retained authored heavy-impact component of the accepted Epigraph profile",
        },
        "rationale": (
            "The maintainer accepted the current Protoss Epigraph behavior as-is; "
            "preserve its exact two-part armor and blast profile."
        ),
        "review_reference": "Maintainer unit decision: Protoss Epigraph is good enough as authored",
    },
    "GoliathMG": {
        "component_purposes": {
            "Bullet_Medium": "authored bullet contribution to the Mk1 secondary ground attack",
            "CannonHE_Heavy": "authored heavy-impact contribution to the Mk1 secondary ground attack",
            "Concussion_Light": "authored light-concussion contribution to the Mk1 secondary ground attack",
        },
        "rationale": (
            "The Goliath remains primarily anti-air; the maintainer accepted Mk1's "
            "weaker secondary ground attack and asked that existing Mk1 units remain usable."
        ),
        "review_reference": "Maintainer progression decision: preserve Goliath Mk1 ground behavior",
    },
    "GoliathMk2MG": {
        "component_purposes": {
            "Bullet_Medium": "authored bullet contribution to the improved Mk2 ground attack",
            "CannonHE_Heavy": "authored heavy-impact contribution to the improved Mk2 ground attack",
        },
        "rationale": (
            "The maintainer approved Mk2 as superior in most situations while retaining "
            "excellent anti-air and only mediocre secondary ground performance."
        ),
        "review_reference": "Maintainer progression decision: preserve approved Goliath Mk2 role",
    },
    "DuelistTankCannon": {
        "component_purposes": {
            "CannonHE_Heavy": "heavy cannon contribution to the Duelist's vehicle and structure role",
            "PreservedFlat_Grenade": "separate hostile-target grenade geometry in the Duelist impact",
            "PreservedFlat_HeavyBomb": "separate ground and ship heavy-bomb route in the Duelist impact",
            "PreservedFlat_MediumFlameWeapon": (
                "temperature-state and flame contribution to the Duelist impact"
            ),
            "PreservedFlat_TankDestroyerCannon": (
                "anti-armor contribution to the Duelist's vehicle role"
            ),
        },
        "rationale": (
            "The maintainer defined the Ixian Duelist as versatile against vehicles and "
            "structures with limited air holdoff, but not universally dominant; its "
            "resolved mains deliberately retain distinct armor, geometry, relationship, "
            "target, and Temperature-state behavior."
        ),
        "review_reference": "Maintainer unit decision: preserve the Ixian Duelist's versatile role",
    },
    "HMG_Duelist_upgrade": {
        "component_purposes": {
            "Bullet_Medium": "bullet contribution to the Duelist's upgraded secondary gun",
            "CannonHE_Heavy": "heavy-impact contribution to the Duelist's upgraded secondary gun",
        },
        "rationale": (
            "The upgraded secondary gun is part of the maintainer-approved Duelist role; "
            "preserve its exact mixed ground and air-capable profile alongside the base cannon."
        ),
        "review_reference": "Maintainer unit decision: preserve the Ixian Duelist's limited air holdoff",
    },
    "autogun_tank": {
        "component_purposes": {
            "Bullet_MediumFlatCompatibility": "primary anti-infantry and light-target bullet profile",
            "CannonHE_Heavy": "secondary general-impact contribution to the autogun profile",
            "MissileAP_Heavy": "limited vehicle and aircraft contribution to the autogun profile",
        },
        "rationale": (
            "The maintainer defined every Ordos autogun-tank variant as strong against "
            "infantry, light vehicles, and aircraft but mediocre against vehicles and "
            "inferior one-on-one to dedicated anti-armor units."
        ),
        "review_reference": "Maintainer unit decision: preserve the Ordos autogun-tank role",
    },
    "autogun_tank_small": {
        "component_purposes": {
            "Bullet_MediumFlatCompatibility": "primary anti-infantry and light-target bullet profile",
            "CannonHE_Heavy": "secondary general-impact contribution to the autogun profile",
            "MissileAP_Heavy": "limited vehicle and aircraft contribution to the autogun profile",
        },
        "rationale": (
            "The maintainer defined every Ordos autogun-tank variant as strong against "
            "infantry, light vehicles, and aircraft but mediocre against vehicles and "
            "inferior one-on-one to dedicated anti-armor units."
        ),
        "review_reference": "Maintainer unit decision: preserve the Ordos autogun-tank role",
    },
}

TECHNICAL_DECISION_OVERRIDES = {
    "ExplosiveDebris": {
        "component_purposes": {
            "Demolition_Light": (
                "separate 3000-damage wide conventional blast at Spread 1c562"
            ),
            "Flame_Light": (
                "separate 16000-damage close burn applying Temperature at scale 100"
            ),
        },
        "rationale": (
            "Devastator meltdown debris intentionally combines a weak wide explosion "
            "with a stronger close Temperature-bearing burn; folding either route "
            "into the other would multiply wide damage or erase the close fire payload."
        ),
        "review_reference": (
            "Resolved state review: Devastator wide blast and close burning debris"
        ),
    },
    "SyndicateFireballLauncherExplode": {
        "component_purposes": {
            "PreservedFlat_Flame_Heavy": (
                "independent heavy-tier flat flame application with Temperature scale 100"
            ),
            "PreservedFlat_Flame_Light": (
                "independent light-tier flat flame application with Temperature scale 100"
            ),
            "PreservedFlat_Flame_Medium": (
                "independent medium-tier flat flame application with Temperature scale 100"
            ),
            "PreservedFlat_HeavyFlameWeapon": (
                "independent legacy heavy-flame application with Temperature scale 100"
            ),
            "PreservedFlat_LightFlameWeapon": (
                "independent legacy light-flame application with Temperature scale 100"
            ),
            "PreservedFlat_MediumFlameWeapon": (
                "independent legacy medium-flame application with Temperature scale 100"
            ),
        },
        "rationale": (
            "The death fireball deliberately retains six flat Temperature-bearing "
            "applications plus three percentage Temperature applications. Per-warhead "
            "rounding, thresholds, observers, and state changes make a one-node fold "
            "behaviorally unproven even when nominal flat damage is preserved."
        ),
        "review_reference": (
            "Resolved state review: nine independent Temperature-bearing applications"
        ),
    },
}


def component_purpose(category: str, main: str) -> str:
    if category == "staged superweapon":
        return f"authored superweapon stage {main} with independently pinned behavior"
    if category == "target-routed composite":
        return f"authored target, armor, relationship, or state route {main}"
    if category == "percentage-scope compatibility":
        if main.endswith("FlatCompatibility"):
            return f"fixed compatibility remainder {main} with percentage scaling disabled"
        if main.startswith("CannonHE_"):
            return f"separate conventional impact component {main} outside the AP percentage split"
        return f"percentage-scaled canonical damage component {main}"
    if category == "maintainer-approved role blend":
        return f"authored armor contribution {main} to the approved mixed unit role"
    if category == "maintainer-curated signature":
        return f"authored D2K signature layer {main} retained by the explicit exception"
    special = (
        "tesla", "cryo", "chem", "nuclear", "sonic", "inferno",
        "temperature", "ioncannon", "railgun", "waveforce", "quantum",
    )
    if any(token in main.lower() for token in special):
        return f"special energy, status, or effect payload {main}"
    return f"primary conventional delivery or impact {main}"


def curated_decisions() -> dict[str, dict[str, object]]:
    """Expand the exact review decisions and reject overlaps or malformed groups."""
    decisions = {}
    for category, groups in DECISION_GROUPS.items():
        if category not in CATEGORY_RATIONALES:
            raise ValueError(f"missing rationale for category {category}")
        for names, mains in groups:
            expected_mains = tuple(sorted(mains))
            if len(expected_mains) < 2 or len(set(expected_mains)) != len(expected_mains):
                raise ValueError(f"invalid mains in {category}: {mains}")
            for name in names:
                if name in decisions:
                    raise ValueError(f"duplicate reviewed weapon {name}")
                role_decision = ROLE_BLEND_DECISIONS.get(name)
                exact_decision = role_decision or TECHNICAL_DECISION_OVERRIDES.get(name)
                if category == "maintainer-approved role blend" and role_decision is None:
                    raise ValueError(f"missing exact maintainer role decision for {name}")
                component_purposes = (
                    exact_decision["component_purposes"] if exact_decision is not None
                    else {
                        main: component_purpose(category, main)
                        for main in expected_mains
                    }
                )
                decisions[name] = {
                    "category": category,
                    "component_purposes": component_purposes,
                    "mains": list(expected_mains),
                    "overlap_justification": CATEGORY_OVERLAP[category],
                    "rationale": (
                        exact_decision["rationale"] if exact_decision is not None
                        else (
                            f"Exact family decision for {', '.join(names)}: "
                            f"{CATEGORY_RATIONALES[category]}; reviewed components are "
                            f"{', '.join(expected_mains)}."
                        )
                    ),
                    "review_reference": (
                        exact_decision["review_reference"] if exact_decision is not None
                        else CATEGORY_REFERENCES[category]
                    ),
                }
    if set(ROLE_BLEND_DECISIONS) != {
            name for names, _mains in DECISION_GROUPS["maintainer-approved role blend"]
            for name in names}:
        raise ValueError("exact maintainer role decision set differs from curated group")
    if not set(TECHNICAL_DECISION_OVERRIDES) <= {
            name for names, _mains in DECISION_GROUPS["status payload"]
            for name in names}:
        raise ValueError("technical decision overrides differ from status-payload groups")
    return decisions


def live_snapshot(rules, name: str, main_nodes: Callable, referrer_index=None):
    resolved = rules.resolve_weapon(name)
    if resolved is None:
        raise ValueError(f"missing weapon {name}")
    mains = sorted(main_nodes(resolved), key=lambda node: node.key)
    if referrer_index is None:
        referrer_index = resolved_referrer_index(rules)
    referrers = referrer_index.get(name.lower(), [])
    return {
        "main_digest": digest([node_payload(node) for node in mains]),
        "mains": sorted(node.key.replace("Warhead@", "") for node in mains),
        "referrer_digest": digest(referrers),
        "referrers": referrers,
        "weapon_digest": digest(node_payload(resolved)),
    }


def validate_manifest(rules, main_nodes: Callable) -> list[str]:
    from survey_weapon_structure import inventory

    data = load_manifest()
    errors = []
    referrer_index = resolved_referrer_index(rules)
    curated = curated_decisions()
    if set(data["entries"]) != set(curated):
        errors.append(
            "reviewed name set differs from curated decisions: "
            f"missing={sorted(set(curated) - set(data['entries']))}, "
            f"extra={sorted(set(data['entries']) - set(curated))}")
    raw = inventory(rules, reviewed_predicate=lambda _name, _mains: False)
    reachability = {}
    for name in raw["sets"]["direct_actor_armament"]:
        reachability[name] = "direct"
    for name in raw["sets"]["indirect_weapon_graph"]:
        reachability[name] = "indirect"
    for name in raw["sets"]["unreached"]:
        reachability[name] = "unreached"
    required = {
        "category", "component_purposes", "expected_reachability",
        "main_digest", "mains", "rationale", "referrer_digest",
        "referrers", "review_reference", "overlap_justification",
        "weapon_digest",
    }
    for name, entry in sorted(data["entries"].items()):
        missing = required - set(entry)
        extra = set(entry) - required
        if missing or extra:
            errors.append(
                f"{name}: schema mismatch missing={sorted(missing)} extra={sorted(extra)}")
            continue
        if name.startswith("^") or rules.weapon(name) is None:
            errors.append(f"{name}: reviewed entry must be one concrete weapon")
            continue
        decision = curated.get(name)
        if decision is None:
            continue
        for field in (
                "category", "component_purposes", "mains", "rationale",
                "review_reference", "overlap_justification"):
            if entry[field] != decision[field]:
                errors.append(f"{name}: {field} differs from curated decision")
        if entry["expected_reachability"] != reachability.get(name):
            errors.append(f"{name}: stale expected_reachability")
        if set(entry["component_purposes"]) != set(entry["mains"]):
            errors.append(f"{name}: every main needs exactly one declared purpose")
        live = live_snapshot(rules, name, main_nodes, referrer_index)
        for field in ("mains", "main_digest", "weapon_digest",
                      "referrers", "referrer_digest"):
            if entry[field] != live[field]:
                errors.append(f"{name}: stale {field}")
    return errors


def generated_manifest(rules, main_nodes: Callable) -> dict[str, object]:
    """Build a manifest only when every curated decision matches current rules."""
    from survey_weapon_structure import inventory

    decisions = curated_decisions()
    referrer_index = resolved_referrer_index(rules)
    raw = inventory(rules, reviewed_predicate=lambda _name, _mains: False)
    reachability = {}
    for name in raw["sets"]["direct_actor_armament"]:
        reachability[name] = "direct"
    for name in raw["sets"]["indirect_weapon_graph"]:
        reachability[name] = "indirect"
    for name in raw["sets"]["unreached"]:
        reachability[name] = "unreached"

    entries = {}
    for name, decision in sorted(decisions.items()):
        if name not in reachability:
            raise ValueError(f"{name}: curated weapon is not a current raw stack")
        if reachability[name] == "unreached":
            raise ValueError(f"{name}: curated decision must be reachable")
        snapshot = live_snapshot(rules, name, main_nodes, referrer_index)
        if snapshot["mains"] != decision["mains"]:
            raise ValueError(
                f"{name}: curated mains {decision['mains']} do not match "
                f"resolved mains {snapshot['mains']}")
        entries[name] = {
            **decision,
            "expected_reachability": reachability[name],
            **snapshot,
        }
    return {"entries": entries, "schema_version": 1}


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--snapshot", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()

    from audit_three_way_split import main_warhead_nodes
    from miniyaml import Ruleset

    rules = Ruleset(ROOT)
    if args.write:
        data = generated_manifest(rules, main_warhead_nodes)
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {MANIFEST.relative_to(ROOT)} ({len(data['entries'])} entries)")
        return 0
    data = load_manifest()
    if args.snapshot:
        referrer_index = resolved_referrer_index(rules)
        rows = {
            name: live_snapshot(rules, name, main_warhead_nodes, referrer_index)
            for name in sorted(data["entries"])
        }
        print(json.dumps(rows, indent=2, sort_keys=True))
        return 0
    errors = validate_manifest(rules, main_warhead_nodes)
    if errors:
        print("FAIL intentional composite manifest")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS {len(data['entries'])} intentional composite fingerprints")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
