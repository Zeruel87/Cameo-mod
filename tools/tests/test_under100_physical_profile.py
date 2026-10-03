"""Regression checks for the first under-100 physical-weapon checkpoint."""

from __future__ import annotations

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

try:
    import classify_remaining_weapons as classifier
except ImportError:
    classifier = None
from miniyaml import Ruleset


ROOTS = {
    "120mm_td", "25mm", "AsianLynxTankCannon", "CabalArtilleryWalkerShell",
    "DiabloCannon", "FutureMechGatling", "td_nod_lighttankmkii_lighttank2cannon",
    "MortarTeamArtilleryShell", "RA2APCFlakCannon", "RA2LasherCannon",
    "ra1_allies_reconranger_recoillessgun", "SteelCruiserCannons", "SteelTwisterMissiles",
    "TS70mmTurChem", "TSScoopDualTurChem", "WhiteRabbitGatling", "ra1_soviets_siegemammothtank_ra120mm2",
    "CabalCommandoPlasma", "CabalCommandoPlasmaMk2", "CabalSubmarinePlasma",
    "HeavyAATankCannontkm", "PlasmaFlamer", "td_gdi_skyshield_skyshieldcannon",
    "TSDestroyerMissiles", "TSHoverMissile", "TSSAPCMissiles",
    "td_nod_chemicalssmlauncher_chemicalhonestjohn", "JapanSuperBomb", "ra1_soviets_siegemammothtank_mammothtusk2thermobaric",
    "MammothTuskThermobaric", "ra1_soviets_monstertank_missile_thermobaric", "td_gdi_orca_orcamissiles",
    "td_gdi_advancedguardtower_towermissile", "TSBikeTibMissile", "TSHellfireTwin",
    "wc2mageBlizzard_Projectile",
    "ra1_allies_phasetransport_missile", "ra1_soviets_siegemammothtank_mammothtusk2", "td_gdi_sonicmissilesoldier_missilesoldierweapon", "Naxis_Komet",
    "Spore_AA", "wc2_tower_arrow",
    "ra1_soviets_hindattackhelicopter_hindmissilesnuclear", "NaxiMeteor", "RA2TOPOLCuba",
    "BehemothShoot", "DreadshroudSpore", "td_gdi_firehawk_firehawkbomb", "MutFlamerChem",
    "MutHFlamerChem", "ShtoraLaser", "TS30mmRail",
    "TSCABALEnlightedLaser", "TSCABALObeliskLaserFire", "TSProton",
    "TankBusterBeamCannon",
    "AsianHarbingerPlasma", "AsianPulverizerMechaGatling", "AtreusMG",
    "CannonAttackRobotGun", "DeviatorMissile", "DeviatorMissile_Artillery",
    "EpigraphMG", "FutureMechPlasma", "GoliathMk2MG", "HMG_Duelist_upgrade",
    "ra1_soviets_hindattackhelicopter_hindmissilesthermobaric", "IxRailgunDroneBullet", "KodiakCannon",
    "Laboratory_Bioball", "MarauderMissiles", "NaxiInterceptorGun",
    "PhobosLaser", "RA2LarsRocket", "RA2PsychicJab", "RA2RBurritoRocket",
    "SCTyr", "ScarabLaunch", "SteelDaggerCannon", "SteelFighterRailgun",
    "TSStankTibTusk", "ra1_soviets_migattackbomber_thermobaricmaverick", "WyvernRockets", "autogun_tank",
    "facedancer_grenade", "ixian_airdrone", "wc2arrowFire",
    "wc2highArrowFire",
    "td_gdi_archerartillery_archerartilleryshell", "td_nod_artillery_artilleryshellupgrade", "BallistaMultiShot",
    "td_nod_reconbike_rocket", "D2K_155mm2", "SwarmlingShoot", "eye_bomberguy",
    "ra1_soviets_v1rockettruck_v1rocketsthermobaric", "wc2_dwarf_Rifle", "wc2catapultFire",
}

ALLOWED_COMPARATOR_FINDINGS = {
    "blast_shape",
    "invalid_target_damage",
    "physical_state_bindings",
    "relationship_stat_damage",
}


def child(node, key):
    return next((item for item in node.children if item.key == key), None)


@unittest.skipIf(classifier is None,
                 "classify_remaining_weapons.py was deleted 2026-09-06")
class Under100PhysicalProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_selected_roots_are_retired_and_checkpoint_count_does_not_regress(self):
        remaining = classifier.classify(self.rules)
        names = {row["weapon"] for row in remaining}
        self.assertFalse(names & ROOTS, names & ROOTS)
        self.assertLessEqual(len(remaining), 99)

    def test_flat_compatibility_helpers_cannot_add_percentage_damage(self):
        helpers = [name for name in self.rules.weapons if name.startswith("^Compatibility_")]
        self.assertTrue(helpers)
        for name in helpers:
            helper = self.rules.resolve_weapon(name)
            self.assertIsNotNone(helper, name)
            damage_nodes = [node for node in helper.children
                            if node.key.startswith("Warhead@") and "Damage" in str(node.value)]
            self.assertTrue(damage_nodes, name)
            for node in damage_nodes:
                self.assertNotIn("Percentage", str(node.value), f"{name}/{node.key}")
                scale = child(node, "PercentageScale")
                if scale is not None:
                    self.assertEqual("0", scale.value, f"{name}/{node.key}")

    def test_naxis_interceptor_is_air_first_without_anti_infantry_gun_bias(self):
        shared_rockets = self.rules.resolve_weapon("NaxPlaneRockets_elite")
        self.assertEqual("Ground, Water, Air", child(shared_rockets,
                                                      "ValidTargets").value)
        rockets = self.rules.resolve_weapon("NaxInterceptorRockets")
        self.assertEqual("Air", child(rockets, "ValidTargets").value)
        main = child(rockets, "Warhead@MissileAA_HeavyFlatCompatibility")
        self.assertEqual("Air", child(main, "ValidTargets").value)

        resolved_gun = self.rules.resolve_weapon("NaxiInterceptorGun")
        gun = child(resolved_gun,
                    "Warhead@Bullet_MediumFlatCompatibility")
        self.assertEqual("1", child(gun, "Spread").value)
        self.assertIsNone(child(resolved_gun, "Warhead@CannonHE_Heavy"))
        percentage = [node for node in resolved_gun.children
                      if node.value == "AreaDamagePercentage"]
        self.assertEqual(4, len(percentage))
        for node in percentage:
            self.assertEqual("1", child(node, "Spread").value, node.key)
        versus = child(gun, "Versus")
        for armor in ("None", "Flak", "Plate", "Heroic"):
            self.assertEqual("100", child(versus, armor).value, armor)

    def test_missile_consolidations_follow_the_weapon_roles(self):
        expected = {
            "ra1_soviets_hindattackhelicopter_hindmissilesthermobaric": "Thermobaric_MediumFlatCompatibility",
            "ra1_soviets_migattackbomber_thermobaricmaverick": "Thermobaric_HeavyFlatCompatibility",
            "MarauderMissiles": "MissileAP_MediumFlatCompatibility",
            "RA2RBurritoRocket": "CannonHE_HeavyFlatCompatibility",
            "TSStankTibTusk": "MissileAP_MediumFlatCompatibility",
        }
        for weapon_name, warhead_name in expected.items():
            weapon = self.rules.resolve_weapon(weapon_name)
            self.assertIsNotNone(child(weapon, f"Warhead@{warhead_name}"),
                                 weapon_name)

    def test_named_energy_and_biological_weapons_keep_their_roles(self):
        expected = {
            "AsianHarbingerPlasma": "Plasma_MediumFlatCompatibility",
            "FutureMechPlasma": "Plasma_HeavyFlatCompatibility",
            "IxRailgunDroneBullet": "Railgun_HeavyFlatCompatibility",
            "Laboratory_Bioball": "Chemical_Medium",
            "PhobosLaser": "Laser_HeavyFlatCompatibility",
            "SteelFighterRailgun": "Laser_HeavyFlatCompatibility",
        }
        for weapon_name, warhead_name in expected.items():
            weapon = self.rules.resolve_weapon(weapon_name)
            self.assertIsNotNone(child(weapon, f"Warhead@{warhead_name}"),
                                 weapon_name)

    def test_baseline_comparison_contains_only_accepted_standardization(self):
        paths = sorted((ROOT / "docs" / "audit" / "latest").glob(
            "under100_checkpoint*_diff.json"))
        self.assertTrue(paths)
        for path in paths:
            report = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual([], report["added"], path.name)
            self.assertEqual([], report["removed"], path.name)
            self.assertTrue(report["changed"], path.name)
            for weapon, findings in report["changed"].items():
                kinds = {finding[0] for finding in findings}
                self.assertLessEqual(kinds, ALLOWED_COMPARATOR_FINDINGS,
                                     f"{path.name}/{weapon}: {sorted(kinds)}")


if __name__ == "__main__":
    unittest.main()
