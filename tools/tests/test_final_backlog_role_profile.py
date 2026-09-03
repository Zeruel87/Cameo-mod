"""Regression checks for the final under-200 weapon-root batch."""

from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

import classify_remaining_weapons as classifier
from miniyaml import Ruleset


ROOTS = {
    "ArmoredCarMG", "BHRedDarts", "ChemRockets", "CommandoM16", "EMPGrenade",
    "GuardianShoot", "MutaliskSpore", "RashidanGun", "TDShotgun", "TurretGun",
    "eden_EMP", "japan_imperialscoutsman_rifle", "plymouthSticky", "plymouth_EMP",
    "tkmheavyaaturret",
}


def child(node, key):
    return next((item for item in node.children if item.key == key), None)


def damage(node, key):
    warhead = child(node, f"Warhead@{key}")
    return None if warhead is None else int(child(warhead, "Damage").value)


class FinalBacklogRoleProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_selected_roots_are_retired_and_total_is_below_200(self):
        remaining = classifier.classify(self.rules)
        names = {row["weapon"] for row in remaining}
        self.assertFalse(names & ROOTS, names & ROOTS)
        self.assertLess(len(remaining), 200)

    def test_role_damage_budgets_and_compatibility_slices(self):
        expected = {
            "ArmoredCarMG": {"Bullet_Medium": 16000},
            "BHRedDarts": {"Tesla_Super": 22000, "EMPCompatibility": 5000},
            "ChemRockets": {"Chemical_Light": 24000, "ChemRocketCompatibility": 12000},
            "CommandoM16": {"Bullet_Medium": 4000, "SniperCompatibility": 4000,
                              "OpenToppedCompatibility": 4000},
            "EMPGrenade": {"Tesla_Super": 32000, "TeslaSharedCompatibility": 32000,
                            "TemperatureCompatibility": 8000, "EMPCompatibility": 32000},
            "GuardianShoot": {"Concussion_MediumFlatCompatibility": 24000},
            "MutaliskSpore": {"Chemical_MediumFlatCompatibility": 32000},
            "RashidanGun": {"Bullet_Medium": 8000},
            "TDShotgun": {"Bullet_Medium": 4000, "Concussion_Medium": 8000},
            "TurretGun": {"Concussion_Medium": 19000},
            "eden_EMP": {"Tesla_Super": 16000, "TemperatureCompatibility": 2000,
                          "EMPCompatibility": 32000},
            "japan_imperialscoutsman_rifle": {"Bullet_Medium": 8000,
                                               "RailgunCompatibility": 4000,
                                               "RailgunShieldCompatibility": 1000},
            "plymouthSticky": {"Chemical_Light": 12000},
            "plymouth_EMP": {"Tesla_Super": 16000, "TemperatureCompatibility": 2000,
                              "EMPCompatibility": 32000},
            "tkmheavyaaturret": {"Bullet_Medium": 8000},
        }
        for name, warheads in expected.items():
            weapon = self.rules.resolve_weapon(name)
            for key, value in warheads.items():
                self.assertEqual(value, damage(weapon, key), f"{name}/{key}")

    def test_descendant_damage_splits_remain_explicit(self):
        expected = {
            "ArmoredCarMG_AA": {"Bullet_Medium": 16000},
            "RashidanGun_upgrade": {"Bullet_MediumFlatCompatibility": 12000,
                                     "RashidanGroundCompatibility": 4000},
            "MutaBounce1": {"Chemical_MediumFlatCompatibility": 24000},
            "MutaBounce2": {"Chemical_MediumFlatCompatibility": 16000},
            "EMPGrenadeExplode": {"Tesla_Super": 32000,
                                   "TeslaSharedCompatibility": 8000,
                                   "TeslaAirCompatibility": 8000,
                                   "TemperatureCompatibility": 4000,
                                   "EMPCompatibility": 16000},
            "plymouthStickyTiger": {"Chemical_Light": 14000,
                                     "StickyWildcardCompatibility": 4000},
            "plymouthStickyDefence": {"Chemical_Light": 12000,
                                       "StickyWildcardCompatibility": 2000},
        }
        for name, warheads in expected.items():
            weapon = self.rules.resolve_weapon(name)
            for key, value in warheads.items():
                self.assertEqual(value, damage(weapon, key), f"{name}/{key}")

        armored_car_aa = self.rules.resolve_weapon("ArmoredCarMG_AA")
        self.assertEqual("Air", child(child(armored_car_aa,
                                             "Warhead@Bullet_Medium"),
                                      "ValidTargets").value)

    def test_emp_temperature_and_sticky_side_effects_remain(self):
        for name in ("BHRedDarts", "EMPGrenade", "eden_EMP", "plymouth_EMP"):
            emp = child(self.rules.resolve_weapon(name), "Warhead@EMPCompatibility")
            self.assertEqual("AffectsIntegrity", emp.value, name)
            self.assertEqual("Shielded", child(emp, "InvalidTargets").value, name)

        bh_emp = child(self.rules.resolve_weapon("BHRedDarts"), "Warhead@EMPCompatibility")
        self.assertIsNone(child(bh_emp, "ValidRelationships"))
        for name in ("EMPGrenade", "eden_EMP", "plymouth_EMP"):
            emp = child(self.rules.resolve_weapon(name), "Warhead@EMPCompatibility")
            self.assertEqual("Neutral, Enemy", child(emp, "ValidRelationships").value, name)

        for name in ("EMPGrenade", "eden_EMP", "plymouth_EMP"):
            state = child(self.rules.resolve_weapon(name), "Warhead@TemperatureCompatibility")
            self.assertEqual("Temperature", child(state, "PhysicalStateName").value, name)
            self.assertEqual("100", child(state, "PhysicalStateScale").value, name)

        sticky = self.rules.resolve_weapon("plymouthSticky")
        self.assertEqual("stickyfoam", child(child(sticky, "Warhead@stickyfoam"), "Condition").value)
        self.assertEqual("snared", child(child(sticky, "Warhead@snared"), "Condition").value)

    def test_percentage_scale_is_disabled_on_every_canonical_main(self):
        for name in ROOTS:
            weapon = self.rules.resolve_weapon(name)
            mains = [node for node in weapon.children
                     if node.key.startswith("Warhead@") and node.value == "AreaDamage"
                     and child(node, "PercentageScale") is not None]
            self.assertTrue(mains, name)
            for main in mains:
                self.assertEqual("0", child(main, "PercentageScale").value,
                                 f"{name}/{main.key}")


if __name__ == "__main__":
    unittest.main()
