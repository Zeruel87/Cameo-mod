"""Regression contract for the maintainer-authorized role redesign batch."""

from __future__ import annotations

import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/authorized_role_profile_comparison.json"
sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]

from audit_three_way_split import main_warhead_nodes, main_warheads
import consolidate_authorized_role_profiles as cohort
from miniyaml import Ruleset
import percentage_damage as pd


CHANGED = set(cohort.BASELINE_MAINS)
EXPECTED_PERCENTAGE_DELTAS = {
    "ASDFKamikazeExplosion": [[250, 24, 25]],
    "ConscriptMolotov": [[20, 0, 1]],
    "NaxiAntiTankCannon": [[250, 34, 35]],
    "NaxiAntiTankCannonCorrosion": [[250, 34, 35]],
    "NaxiAntiTankCannon_elite": [[250, 34, 35]],
    "TSBusMortar": [[160, 50, 51]],
    "tkm_trooper_gp25": [[20, 0, 1], [160, 8, 9], [250, 14, 15]],
}


class AuthorizedRoleProfileConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_exact_selected_family_and_totals_are_live(self):
        self.assertTrue(cohort.inspect(self.rules))
        self.assertEqual(12, len(CHANGED))
        for name in sorted(CHANGED):
            destination = cohort.DESTINATIONS[name]
            nodes = main_warhead_nodes(self.rules.resolve_weapon(name))
            self.assertEqual([destination], [node.key.split("@", 1)[1] for node in nodes], name)
            self.assertEqual(cohort.TOTALS[name], int(nodes[0].get("Damage")), name)
            self.assertEqual("10000", nodes[0].get("PercentageScale"), name)
            self.assertEqual(cohort.RUNTIME_UNITS[name], sum(
                int(application["runtime_units"])
                for application in pd.percentage_applications(
                    self.rules.resolve_weapon(name), 200000)
                if application["tag"] == destination
            ), name)

    def test_nominal_temperature_scale_is_compensated(self):
        expected = {
            "ConscriptMolotov": (16000, 50, 800),
            "tkm_trooper_gp25": (12000, 50, 600),
        }
        for name, (damage, scale, folded_units) in expected.items():
            node = main_warhead_nodes(self.rules.resolve_weapon(name))[0]
            self.assertEqual("Temperature", node.get("PhysicalStateName"), name)
            self.assertEqual(str(scale), node.get("PhysicalStateScale"), name)
            self.assertEqual(damage * scale, {
                "ConscriptMolotov": 8000 * 100,
                "tkm_trooper_gp25": 6000 * 100,
            }[name], name)
            self.assertEqual(folded_units * scale, {
                "ConscriptMolotov": 400 * 100,
                "tkm_trooper_gp25": 300 * 100,
            }[name], name)

    def test_gp25_temperature_armor_matrix_is_intentionally_reprofiled(self):
        changes = self.report["changed"]["tkm_trooper_gp25"]
        before, after = next(value for kind, *value in changes if kind == "armor_profile")
        before_by_tag = {row[0]: row for row in before}
        after_by_tag = {row[0]: row for row in after}

        def meter(row, scale, armors):
            damage = row[1]
            versus = dict(row[2])
            return {
                armor: damage * int(versus[armor]) * scale // 10000
                for armor in armors
            }

        armors = ("None", "Scout", "Light", "Medium", "Heavy",
                  "Superheavy", "Concrete", "Wood")
        self.assertEqual({
            "None": 12000, "Scout": 7020, "Light": 5040, "Medium": 4140,
            "Heavy": 3660, "Superheavy": 3300, "Concrete": 5520, "Wood": 11640,
        }, meter(before_by_tag["Flame_Light"], 100, armors))
        self.assertEqual({
            "None": 10980, "Scout": 6540, "Light": 5160, "Medium": 4140,
            "Heavy": 3480, "Superheavy": 3060, "Concrete": 8160, "Wood": 12000,
        }, meter(after_by_tag["Demolition_Light"], 50, armors))

    def test_molotov_death_child_remains_exactly_preserved(self):
        death = self.rules.resolve_weapon("ConscriptMolotovExplode")
        self.assertEqual(
            ["Flame_LightFlatCompatibility"], main_warheads(death))
        node = main_warhead_nodes(death)[0]
        self.assertEqual("8000", node.get("Damage"))
        self.assertEqual("9988", node.get("PercentageScale"))
        self.assertEqual("Temperature", node.get("PhysicalStateName"))
        self.assertEqual("100", node.get("PhysicalStateScale"))
        self.assertEqual(
            cohort.PRESERVED_HASHES["ConscriptMolotovExplode"],
            cohort.resolved_hash(self.rules, "ConscriptMolotovExplode"),
        )

    def test_comparison_contains_only_the_authorized_behavior_changes(self):
        self.assertEqual([], self.report["added"])
        self.assertEqual([], self.report["removed"])
        self.assertEqual(CHANGED, set(self.report["changed"]))

        by_kind: dict[str, set[str]] = {}
        for name, changes in self.report["changed"].items():
            for change in changes:
                by_kind.setdefault(change[0], set()).add(name)

        self.assertEqual(CHANGED, by_kind["armor_profile"])
        self.assertEqual(CHANGED, by_kind["blast_shape"])
        self.assertEqual(
            {"ConscriptMolotov", "tkm_trooper_gp25"},
            by_kind["physical_state_bindings"],
        )
        self.assertEqual(set(EXPECTED_PERCENTAGE_DELTAS), by_kind["percentage_damage"])
        self.assertEqual(
            {"armor_profile", "blast_shape", "physical_state_bindings", "percentage_damage"},
            set(by_kind),
        )

        for name, expected in EXPECTED_PERCENTAGE_DELTAS.items():
            actual = next(
                change[1]
                for change in self.report["changed"][name]
                if change[0] == "percentage_damage"
            )
            self.assertEqual(expected, actual, name)

    def test_allied_tank_destroyer_remains_deferred_with_its_paid_cryo_pair(self):
        self.assertEqual(
            ["CannonHE_Medium", "CannonAP_Light"],
            main_warheads(self.rules.resolve_weapon("AlliedTankDestroyerCannon")),
        )
        self.assertNotIn("AlliedTankDestroyerCannon", self.report["changed"])


if __name__ == "__main__":
    unittest.main()
