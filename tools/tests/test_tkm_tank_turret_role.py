"""Pins the maintainer-approved TKM Tank Turret Bunker anti-armor role."""

from __future__ import annotations

import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "docs/audit/latest/tkm_tank_turret_summary.json"
COMPARISON = ROOT / "docs/audit/latest/tkm_tank_turret_comparison.json"
DERIVED_LEDGER = ROOT / "docs/balance/derived/redalert2mod_tkm.json"
sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]

from audit_three_way_split import main_warhead_nodes, main_warheads  # noqa: E402
from miniyaml import Ruleset  # noqa: E402
import extract_stats as es  # noqa: E402


EXPECTED_CHANGE_KIND_DIGESTS = {
    "armor_profile": "92f3f63980f2898193403d66e69b9c86fbf623601e9bfdc02407b56cd50915bf",
    "blast_shape": "1ddf92cfeee4bd90682fee5456d1dc01a8c09f5bb4a5412515ed411a552ccb42",
    "percentage_damage": "a23bc1fbb3e7c8a451aaa02cb29bef678115a5a4f46700a3317f00138aeb198a",
}


class TKMTankTurretRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        es.tm.use_ruleset(cls.rules)
        es.we.use_ruleset(cls.rules)
        cls.weapon = cls.rules.resolve_weapon("tkmturretcannon")
        cls.actor = cls.rules.resolve("tkm_tankturretbunker")
        cls.local_actor = cls.rules.actor("tkm_tankturretbunker")
        cls.summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        cls.comparison = json.loads(COMPARISON.read_text(encoding="utf-8"))
        cls.derived = json.loads(DERIVED_LEDGER.read_text(encoding="utf-8"))

    def test_weapon_is_one_focused_anti_armor_main(self):
        self.assertEqual(
            ["CannonAP_LightFlatCompatibility"], main_warheads(self.weapon))
        main = main_warhead_nodes(self.weapon)[0]
        self.assertEqual("16000", main.get("Damage"))
        self.assertEqual("9994", main.get("PercentageScale"))
        self.assertEqual("Ground, Water", main.get("ValidTargets"))
        self.assertEqual("300", main.get("Spread"))
        self.assertEqual("100, 50, 20, 0", main.get("Falloff"))
        self.assertEqual({
            "None": "74",
            "Light": "119",
            "Medium": "123",
            "Heavy": "127",
            "Superheavy": "139",
        }, {
            key: main.child("Versus").get(key)
            for key in ("None", "Light", "Medium", "Heavy", "Superheavy")
        })

    def test_broad_delivery_keeps_the_defense_effective_against_movers(self):
        armament = self.derived["sections"]["defenses"][
            "tkm_tankturretbunker"]["armaments"][0]
        self.assertEqual("tkmturretcannon", armament["weapon"])
        self.assertEqual(204.31, armament["sigma"])
        self.assertEqual(0.8276, armament["reliability"])
        expected = es.weapon_entry(self.rules, armament["weapon"])[es.DERIVED_KEY]
        for key in ("effective_per_shot", "effective_dps"):
            self.assertEqual(expected[key], armament[key], key)

    def test_actor_prioritizes_vehicles_and_uses_anti_tank_description(self):
        local_inherits = {
            child.key: child.value for child in self.local_actor.children
            if child.key == "Inherits" or child.key.startswith("Inherits@")
        }
        self.assertEqual("^PrioritizeVehicle", local_inherits["Inherits@AntiTank"])
        self.assertNotIn("Inherits@AntiInf", local_inherits)
        priorities = {
            child.key for child in self.actor.children
            if child.key.startswith("AutoTargetPriority@")
        }
        self.assertIn("AutoTargetPriority@VEHICLE", priorities)
        self.assertNotIn("AutoTargetPriority@INFANTRY", priorities)
        self.assertEqual(
            "actor_gun.description",
            self.actor.child("Buildable").get("Description"),
        )

    def test_ordinary_tkm_bunker_remains_anti_infantry(self):
        local = self.rules.actor("tkm_bunker")
        resolved = self.rules.resolve("tkm_bunker")
        local_inherits = {
            child.key: child.value for child in local.children
            if child.key == "Inherits" or child.key.startswith("Inherits@")
        }
        self.assertEqual("^PrioritizeInfantry", local_inherits["Inherits@AntiInf"])
        self.assertEqual(
            "template_anti_infantry_defense.description",
            resolved.child("Buildable").get("Description"),
        )

    def test_whole_tree_comparison_is_exact_and_bounded(self):
        self.assertEqual({"tkmturretcannon"}, set(self.comparison["changed"]))
        self.assertEqual([], self.comparison["added"])
        self.assertEqual([], self.comparison["removed"])
        self.assertEqual({
            "armor_profile", "blast_shape", "percentage_damage",
        }, {
            change[0] for change in self.comparison["changed"]["tkmturretcannon"]
        })
        self.assertEqual({
            "changed": {"tkmturretcannon": [
                "armor_profile", "blast_shape", "percentage_damage",
            ]},
            "counts": {"added": 0, "changed": 1, "removed": 0},
            "added": [],
            "removed": [],
            "change_kind_counts": {
                "armor_profile": 1,
                "blast_shape": 1,
                "percentage_damage": 1,
            },
            "change_kind_digests": EXPECTED_CHANGE_KIND_DIGESTS,
            "percentage_rounding": {
                "digest": "f8823e86f5adb664e8857cae1c1092cc7248c6ec2f6210dd56d98f7756615252",
                "max_absolute_delta": 1,
                "row_count": 1,
            },
            "source_digest": "1dc06a9735b946b0943f0d7691772e4f5fe278804b351a216b71a33fc09fe383",
        }, self.summary)


if __name__ == "__main__":
    unittest.main()
