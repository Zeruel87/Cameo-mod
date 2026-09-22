"""Historical four-profile evidence and upstream's current BulletChem contract."""

from __future__ import annotations

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))

from audit_three_way_split import main_warhead_nodes, main_warheads
from miniyaml import Ruleset
import hydra_history


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
        cls.rules = Ruleset(ROOT)
        cls.weapon = hydra_history.weapon()

    def test_historical_four_damage_profiles_are_preserved_in_fixture(self):
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

    def test_existing_corrosion_routes_and_percentage_companions_are_preserved(self):
        chemical = self.weapon.child("Warhead@LightChemicalWeapon")
        self.assertEqual("Corrosion", chemical.get("PhysicalStateName"))
        self.assertEqual("100", chemical.get("PhysicalStateScale"))
        percentages = [node for node in self.weapon.children
                       if node.value == "AreaDamagePercentage"]
        self.assertEqual(4, len(percentages))
        self.assertTrue(all(node.get("Damage") == "1" for node in percentages))
        # Pin existing delivery; the audit reports these duplicates separately.
        for tag in ("LightChemicalWeapon", "LightChemicalWeaponPercentage"):
            node = self.weapon.child("Warhead@" + tag)
            self.assertEqual("Corrosion", node.get("PhysicalStateName"))
            self.assertEqual("100", node.get("PhysicalStateScale"))
            self.assertEqual("100", node.get("PhysicalStates", "Corrosion"))

    def test_current_upstream_bulletchem_is_not_hidden_as_an_exception(self):
        # Upstream 8748c68e4 changed the role/profile; this PR does not revert it.
        current = self.rules.resolve_weapon('HydraSpit')
        self.assertEqual(('BulletChem_Light',), tuple(main_warheads(current)))
        main = current.child('Warhead@BulletChem_Light')
        self.assertEqual('18000', main.get('Damage'))
        self.assertEqual('10000', main.get('PercentageScale'))
        self.assertEqual('15', current.get('ReloadDelay'))
        self.assertEqual('5979', current.get('Range'))
        self.assertEqual('20', main.get('PhysicalStates', 'Corrosion'))
        self.assertIsNone(main.get('PhysicalStateName'))
        # The exemption registry was retired upstream. Inspect the raw resolved
        # topology, without rebuilding the removed approval mechanism.
        self.assertEqual(1, len(main_warhead_nodes(current)))


if __name__ == "__main__":
    unittest.main()
