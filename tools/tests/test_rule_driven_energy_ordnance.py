import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/rule_driven_energy_ordnance_manifest.json"
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import consolidate_rule_driven_energy_ordnance as cohort
from owned_weapon_history import historical_weapon_names


class RuleDrivenEnergyOrdnanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_converter_is_fully_applied(self):
        cohort.validate_result()

    def test_comparison_scope_is_exact(self):
        expected = set(cohort.SELECTED) | {
            "NaxTorpTube", "NaxiJadgDestroyerCorrosion",
        }
        before = json.loads((ROOT / 'tools/tests/fixtures/ifv_owned_names_20260910.json').read_text(encoding='utf-8'))
        historical = {new: old for route in before['routes'].values() for old, new in route.items()}
        td = json.loads((ROOT / 'tools/tests/fixtures/td_owned_names_20260910.json').read_text(encoding='utf-8'))
        historical.update({new: old for route in td['routes'].values() for old, new in route.items()})
        self.assertEqual(historical_weapon_names({historical.get(name, name) for name in expected}), set(self.report["changed"]))
        self.assertEqual([], self.report["added"])
        self.assertEqual([], self.report["removed"])

    def test_only_authorized_role_dimensions_change(self):
        allowed = {
            "percentage_damage", "valid_target_damage",
            "relationship_stat_damage", "physical_state_bindings",
            "armor_profile", "percentage_warheads", "blast_shape",
        }
        kinds = {kind for changes in self.report["changed"].values()
                 for kind in changes}
        self.assertTrue(kinds <= allowed, sorted(kinds - allowed))
        self.assertIn("armor_profile", kinds)
        self.assertIn("blast_shape", kinds)

    def test_folded_percentage_rounding_is_bounded(self):
        self.assertEqual(
            1, self.report["percentage_rounding"]["max_absolute_delta"])

    def test_fire_viper_remains_outside_the_changed_set(self):
        self.assertNotIn("ViperMissilesFire", self.report["changed"])


if __name__ == "__main__":
    unittest.main()
