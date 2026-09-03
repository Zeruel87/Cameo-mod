"""Hydralisk keeps its pre-PR-287 damage and corrosion profile."""

from __future__ import annotations

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))

from audit_three_way_split import main_warhead_nodes, main_warheads
from miniyaml import Ruleset


EXPECTED_MAINS = (
    "LightChemicalWeapon", "LightMissile", "SmallArms", "ArrowWeapon")
EXPECTED_FLAT_DAMAGE = {
    "None": 51480,
    "Flak": 51480,
    "Scout": 38520,
    "Light": 39600,
    "Medium": 40680,
    "Heavy": 41760,
    "Superheavy": 42840,
    "Fighter": 39600,
    "Helicopter": 37440,
    "Bomber": 38520,
    "Spaceship": 35280,
    "Concrete": 25560,
    "Wood": 26640,
    "Steel": 34200,
    "Shield": 79200,
}


class HydraliskStrengthRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.weapon = Ruleset(ROOT).resolve_weapon("HydraSpit")

    def test_original_four_damage_profiles_are_restored(self):
        self.assertEqual(EXPECTED_MAINS, tuple(main_warheads(self.weapon)))
        for node in main_warhead_nodes(self.weapon):
            self.assertEqual("18000", node.get("Damage"), node.key)

    def test_effective_flat_damage_matches_the_pre_regression_profile(self):
        mains = main_warhead_nodes(self.weapon)
        for armor, expected in EXPECTED_FLAT_DAMAGE.items():
            actual = 0
            for node in mains:
                versus = {entry.key: int(entry.value)
                          for entry in node.child("Versus").children}
                actual += int(node.get("Damage")) * versus[armor] // 100
            self.assertEqual(expected, actual, armor)

    def test_corrosion_and_percentage_companions_are_not_amplified(self):
        chemical = self.weapon.child("Warhead@LightChemicalWeapon")
        self.assertEqual("Corrosion", chemical.get("PhysicalStateName"))
        self.assertEqual("100", chemical.get("PhysicalStateScale"))
        percentages = [node for node in self.weapon.children
                       if node.value == "AreaDamagePercentage"]
        self.assertEqual(4, len(percentages))
        self.assertTrue(all(node.get("Damage") == "1" for node in percentages))


if __name__ == "__main__":
    unittest.main()
