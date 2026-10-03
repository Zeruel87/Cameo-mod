"""Exact regression contract for the Facedancer AP compatibility fold."""

from __future__ import annotations

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]

from audit_three_way_split import main_warhead_nodes, main_warheads  # noqa: E402
from miniyaml import Ruleset  # noqa: E402
from percentage_damage import folded_units  # noqa: E402


class FacedancerApFoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.weapon = cls.rules.resolve_weapon("facedancer_grenade")

    def test_only_the_identical_ap_slices_are_folded(self):
        self.assertEqual(
            ["MissileAP_Heavy"],
            main_warheads(self.weapon),
        )
        nodes = {node.key.split("@", 1)[1]: node
                 for node in main_warhead_nodes(self.weapon)}
        ap = nodes["MissileAP_Heavy"]
        self.assertEqual("180000", ap.get("Damage"))
        self.assertEqual("2222", ap.get("PercentageScale"))

    def test_flat_and_percentage_output_are_exact(self):
        self.assertEqual(180000, 140000 + 20000 + 20000)
        self.assertEqual(
            folded_units(40000, 10000)[1],
            folded_units(180000, 2222)[1],
        )
        self.assertEqual(2000, folded_units(180000, 2222)[1])

    def test_special_payloads_remain_separate(self):
        companions = {
            "LightFlameWeaponPercentage", "MediumChemicalWeaponPercentage",
            "HeavyBombPercentage", "GrenadePercentage",
            "ShrapnelWeaponPercentage", "LightMissilePercentage",
            "MediumMissilePercentage",
        }
        keys = {node.key.split("@", 1)[1] for node in self.weapon.children
                if node.key.startswith("Warhead@")}
        self.assertTrue(companions <= keys)
        self.assertEqual(
            "Temperature",
            self.weapon.child("Warhead@LightFlameWeaponPercentage").get(
                "PhysicalStateName"),
        )
        chemical = self.weapon.child("Warhead@MediumChemicalWeaponPercentage")
        self.assertEqual("100", chemical.child("PhysicalStates").get("Corrosion"))
        self.assertIsNone(chemical.get("PhysicalStateName"))
        self.assertIsNone(chemical.get("PhysicalStateScale"))

    def test_authorized_reprofile_removes_the_he_splash_main(self):
        self.assertIsNone(self.weapon.child("Warhead@CannonHE_Heavy"))
        self.assertIsNone(self.weapon.child(
            "Warhead@MissileAP_HeavyFlatCompatibility"))


if __name__ == "__main__":
    unittest.main()
