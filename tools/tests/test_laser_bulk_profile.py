"""Regression checks for the consolidated named heavy-laser batch."""

from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Ruleset


ROOT_LASERS = {
    "BlackHandLaser": (96000, 48000, 3),
    "CabalHunterKillerLasers": (16000, 0, 2),
    "CabalHunterKillerLasers_elite": (30000, 0, 3),
    "TSLaser25mmDep": (4000, 0, 2),
    "edenMobileLaser": (8000, 0, 4),
    "ordos_lasertank": (40000, 0, 4),
    "M16Laser": (6000, 0, 3),
    "laserelitecadregun": (6000, 0, 3),
    "td_nod_minigunner_minigun_laser": (6000, 0, 3),
    "LunarNaxiDroneLaser": (8000, 0, 4),
    "NaxLaserT": (8000, 0, 4),
    "NaxiBeetleLaser_elite": (8000, 0, 4),
    "NaxiTank2Laser": (8000, 0, 4),
}
RESOLVED_LASERS = tuple(ROOT_LASERS) + (
    "edenMobileLaserTiger",
    "edenMobileDefenceLaser",
    "Lunar_AmplifiedLaserT",
    "Lunar_YellowLaserT",
    "Lunar_AmplifiedBeetleLaser",
    "Lunar_AmplifiedBeetleLaser_AA",
    "Lunar_YellowBeetleLaser",
    "Lunar_YellowBeetleLaser_AA",
    "NaxiBeetleLaser_AA_elite",
    "Lunar_AmplifiedTank2Laser",
    "Lunar_AmplifiedTank2Laser_AA",
    "Lunar_YellowTank2Laser",
    "Lunar_YellowTank2Laser_AA",
    "NaxiTank2Laser_AA",
)
RETIRED_FLAT_TAGS = {
    "TankDestroyerCannon",
    "Chaingun",
    "FlakWeapon",
    "MediumMissile",
    "HeavyMissile",
    "LaserWeapon",
    "RailgunWeapon",
    "LaserExtraDamage",
    "RailgunExtraDamage",
}


def child(node, key):
    return next((item for item in node.children if item.key == key), None)


class LaserBulkProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)

    def test_roots_use_one_heavy_laser_destination(self):
        for name, (damage, ground_remainder, percentage_count) in ROOT_LASERS.items():
            weapon = self.rules.resolve_weapon(name)
            self.assertIsNotNone(weapon, name)

            laser = child(weapon, "Warhead@Laser_Heavy")
            self.assertIsNotNone(laser, name)
            self.assertEqual("AreaDamage", laser.value, name)
            self.assertEqual(str(damage), child(laser, "Damage").value, name)
            self.assertEqual("0", child(laser, "PercentageScale").value, name)
            self.assertEqual("64", child(laser, "Spread").value, name)
            self.assertEqual("100, 0", child(laser, "Falloff").value, name)
            self.assertEqual("Temperature", child(laser, "PhysicalStateName").value, name)
            self.assertEqual("75", child(laser, "PhysicalStateScale").value, name)

            remainder = child(weapon, "Warhead@LaserHeavyGroundRemainder")
            if ground_remainder:
                self.assertIsNotNone(remainder, name)
                self.assertEqual(str(ground_remainder), child(remainder, "Damage").value, name)
                self.assertEqual("Ground, Water", child(remainder, "ValidTargets").value, name)
            else:
                self.assertIsNone(remainder, name)

            percentages = [
                item for item in weapon.children
                if item.key.startswith("Warhead@") and item.value == "AreaDamagePercentage"
            ]
            self.assertEqual(percentage_count, len(percentages), name)

    def test_retired_flat_keys_do_not_survive_resolution(self):
        for name in RESOLVED_LASERS:
            weapon = self.rules.resolve_weapon(name)
            tags = {
                item.key.split("@", 1)[1]
                for item in weapon.children
                if item.key.startswith("Warhead@")
                and item.value in {"AreaDamage", "SpreadDamage", "TargetDamage"}
            }
            self.assertFalse(tags & RETIRED_FLAT_TAGS, f"{name}: {tags & RETIRED_FLAT_TAGS}")

    def test_shield_chips_are_preserved_under_compatibility_names(self):
        for name in RESOLVED_LASERS:
            weapon = self.rules.resolve_weapon(name)
            laser_chip = child(weapon, "Warhead@LegacyLaserExtraDamage")
            self.assertIsNotNone(laser_chip, name)
            self.assertEqual("600", child(laser_chip, "Damage").value, name)
            self.assertEqual("false", child(laser_chip, "UpdatesUnitStatistics").value, name)

        for name in ("CabalHunterKillerLasers_elite", "ordos_lasertank"):
            weapon = self.rules.resolve_weapon(name)
            rail_chip = child(weapon, "Warhead@LegacyRailgunExtraDamage")
            self.assertIsNotNone(rail_chip, name)
            self.assertEqual("1000", child(rail_chip, "Damage").value, name)

    def test_remaining_lasers_adopt_the_standard_energy_traits(self):
        for name in (
            "M16Laser",
            "laserelitecadregun",
            "td_nod_minigunner_minigun_laser",
            "LunarNaxiDroneLaser",
            "NaxLaserT",
            "NaxiBeetleLaser_elite",
            "NaxiTank2Laser",
        ):
            weapon = self.rules.resolve_weapon(name)
            laser = child(weapon, "Warhead@Laser_Heavy")
            self.assertEqual("Ally, Neutral, Enemy", child(laser, "ValidRelationships").value, name)
            self.assertEqual("50", child(laser, "FriendlyFireDamage").value, name)
            self.assertEqual("50", child(laser, "FriendlyFireSpread").value, name)
            self.assertIsNone(child(laser, "InvalidTargets"), name)

    def test_naxi_aa_children_keep_only_the_effective_air_slice(self):
        for name in (
            "NaxiBeetleLaser_AA_elite",
            "Lunar_AmplifiedBeetleLaser_AA",
            "Lunar_YellowBeetleLaser_AA",
            "NaxiTank2Laser_AA",
            "Lunar_AmplifiedTank2Laser_AA",
            "Lunar_YellowTank2Laser_AA",
        ):
            weapon = self.rules.resolve_weapon(name)
            laser = child(weapon, "Warhead@Laser_Heavy")
            remainder = child(weapon, "Warhead@LaserHeavyGroundRemainder")
            self.assertEqual("4000", child(laser, "Damage").value, name)
            self.assertEqual("Air", child(laser, "ValidTargets").value, name)
            self.assertIsNone(remainder, name)

    def test_naxi_laser_percentage_profile_survives_inheritance(self):
        for name in (
            "NaxiBeetleLaser_elite",
            "NaxiBeetleLaser_AA_elite",
            "NaxiTank2Laser",
            "NaxiTank2Laser_AA",
        ):
            weapon = self.rules.resolve_weapon(name)
            percentage = child(weapon, "Warhead@LaserWeaponPercentage")
            self.assertIsNotNone(percentage, name)
            self.assertEqual("1", child(percentage, "Damage").value, name)
            self.assertEqual("75", child(percentage, "Spread").value, name)
            self.assertEqual("false", child(percentage, "UpdatesUnitStatistics").value, name)
            versus = child(percentage, "Versus")
            self.assertEqual("35", child(versus, "Shield").value, name)
            self.assertEqual("25", child(versus, "Superheavy").value, name)
            self.assertEqual("21", child(versus, "Heavy").value, name)


if __name__ == "__main__":
    unittest.main()
