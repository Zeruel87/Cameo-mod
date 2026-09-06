import collections
import hashlib
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/laser_heavy_route_comparison.json"
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import consolidate_laser_heavy_routes as cohort
from audit_three_way_split import SPLIT_BASELINE, main_warheads
from audit_warhead_split import BROADCAST_BASELINE
from miniyaml import Ruleset


ACCEPTED = {
    "blast_shape": (
        13, "e06c04af512a5e54b3e9d7fb1a7bed2f65d579ebeda743e82faf1b3d3d6b2084"),
    "main_damage": (
        6, "6e89d6e417427c6cbb5f19ed80272ca4769fe06f0235d1e6d77953bbd70f0ef0"),
    "physical_state_bindings": (
        7, "3d114b3260c9a172ecd9233c3a2a998f91c09fe6b2981b2a742056d6f6dbee20"),
    "relationship_stat_damage": (
        7, "86c1bd89f53f3856cdc9f061ebdc9ae785ee73acd8f2b1f7ee0049311045101f"),
    "valid_target_damage": (
        7, "b8dc9f3eb4427df74c2d764a6ce6dfe70b4743ca3a18f5ee0b3c4095e306fae1"),
}


def child(node, key):
    return next((item for item in node.children if item.key == key), None)


class LaserHeavyRouteConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.by_kind = collections.defaultdict(dict)
        for weapon, changes in cls.report["changed"].items():
            for change in changes:
                cls.by_kind[change[0]][weapon] = change[1:]

    def test_converter_is_fully_applied_and_idempotent(self):
        cohort.validate_result()

    def test_full_recursive_closures_are_pinned(self):
        self.assertEqual(13, len(cohort.SELECTED))
        for root, expected in cohort.EXPECTED_CLOSURES.items():
            self.assertEqual(expected, cohort.descendants(self.rules, root), root)

    def test_ground_and_air_routes_have_one_heavy_laser_main(self):
        for name in cohort.SELECTED:
            weapon = self.rules.resolve_weapon(name)
            self.assertEqual(["Laser_Heavy"], main_warheads(weapon), name)
            laser = child(weapon, "Warhead@Laser_Heavy")
            self.assertIsNone(child(weapon, "Warhead@LaserHeavyGroundRemainder"), name)
            expected_damage = (
                4000 if name in cohort.AIR or name == "TSLaser25mmDep" else 8000
            )
            expected_targets = "Air" if name in cohort.AIR else "Ground, Water"
            self.assertEqual(str(expected_damage), child(laser, "Damage").value, name)
            self.assertEqual(expected_targets, child(laser, "ValidTargets").value, name)
            self.assertEqual("0", child(laser, "PercentageScale").value, name)

    def test_destination_profile_keeps_energy_state_and_shape(self):
        for name in cohort.SELECTED:
            laser = child(self.rules.resolve_weapon(name), "Warhead@Laser_Heavy")
            self.assertEqual("64", child(laser, "Spread").value, name)
            self.assertEqual("100, 0", child(laser, "Falloff").value, name)
            self.assertEqual("Temperature", child(laser, "PhysicalStateName").value, name)
            self.assertEqual("75", child(laser, "PhysicalStateScale").value, name)
            self.assertEqual(
                "Prone75Percent, TriggerProne, ExplosionDeath",
                child(laser, "DamageTypes").value,
                name,
            )

    def test_percentage_companions_are_unchanged_and_separate(self):
        for name in cohort.SELECTED:
            weapon = self.rules.resolve_weapon(name)
            percentages = [
                item for item in weapon.children
                if item.key.startswith("Warhead@")
                and item.value == "AreaDamagePercentage"
            ]
            expected = 2 if name == "TSLaser25mmDep" else (6 if name in cohort.AIR else 4)
            self.assertEqual(expected, len(percentages), name)

    def test_full_ruleset_comparison_has_only_the_accepted_route_cleanup(self):
        self.assertEqual(cohort.SELECTED, set(self.report["changed"]))
        self.assertEqual([], self.report["added"])
        self.assertEqual([], self.report["removed"])
        self.assertEqual(set(ACCEPTED), set(self.by_kind))
        for kind, (count, expected_hash) in ACCEPTED.items():
            payload = json.dumps(
                self.by_kind[kind], sort_keys=True, separators=(",", ":")
            ).encode()
            self.assertEqual(count, len(self.by_kind[kind]), kind)
            self.assertEqual(expected_hash, hashlib.sha256(payload).hexdigest(), kind)

    def test_comparison_preserves_every_effective_route_and_percentage_value(self):
        # The generic diff reports raw inactive routes.  Pin that the six AA
        # branches retain Air damage while only Ground/Water disappear, and the
        # Tick Tank's ground-only weapon retains Ground/Water while only Air
        # disappears.  No percentage_damage entry means exact equality across
        # all 155 active/design HP values measured by review_batch_diff.
        self.assertNotIn("percentage_damage", self.by_kind)
        for name, changes in self.by_kind["valid_target_damage"].items():
            before, after = changes
            before = dict(before)
            after = dict(after)
            effective = {"Air"} if name in cohort.AIR else {"Ground", "Water"}
            for target in effective:
                self.assertEqual(before[target], after[target], (name, target))

    def test_ratchets_match_live_reduction(self):
        self.assertEqual(114, SPLIT_BASELINE)
        self.assertEqual(90, BROADCAST_BASELINE)


if __name__ == "__main__":
    unittest.main()
