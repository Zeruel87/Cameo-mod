import collections
import hashlib
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/named_family_profile_comparison.json"
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import consolidate_named_family_profiles as cohort
from audit_three_way_split import SPLIT_BASELINE, main_warheads
from audit_warhead_split import BROADCAST_BASELINE
from miniyaml import Ruleset


ACCEPTED = {
    "blast_shape": (23, "8648762802f9895732cc40289371418f4dd521f953b94bb41a706bf6273afdc6"),
    "percentage_damage": (7, "eb2dfeb50bbde8805c6b3e64ffdc232a0a71fec3d2c4c8bda8c93ab8d888475c"),
    "physical_state_bindings": (21, "56a59ab46e9b413328326eee591d6130214fadd25a00966d4802b4053255c0d1"),
    "relationship_stat_damage": (7, "71680b8d637d0b090f8b4f8ff76177d019ee37cb12f5ab5621d1e2eb81eda759"),
    "valid_target_damage": (6, "564cfda59c4e87510684fcd8ede9657dc19a37d320dbbb6c7ae95e03dc99e2fc"),
}


def child(node, key):
    return next((item for item in node.children if item.key == key), None)


class NamedFamilyProfileConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.by_kind = collections.defaultdict(dict)
        for weapon, changes in cls.report["changed"].items():
            for change in changes:
                cls.by_kind[change[0]][weapon] = change[1:]

    def test_converter_is_applied_and_closures_are_pinned(self):
        cohort.validate_result()
        self.assertEqual(24, len(cohort.selections(self.rules)))
        for root, (_destination, expected, _total, _scale) in cohort.ROOTS.items():
            self.assertEqual(expected, cohort.descendants(self.rules, root), root)

    def test_each_member_has_one_selected_named_family_main(self):
        for name, (destination, total, scale) in cohort.selections(self.rules).items():
            tag = f"{destination}FlatCompatibility"
            resolved = self.rules.resolve_weapon(name)
            self.assertEqual([tag], main_warheads(resolved), name)
            node = child(resolved, f"Warhead@{tag}")
            self.assertEqual(str(total), str(node.get("Damage")), name)
            self.assertEqual(str(scale), str(node.get("PercentageScale")), name)

    def test_harpy_multi_is_behaviorally_unchanged_and_aoe_shape_is_pinned(self):
        self.assertNotIn("TSLaserHarpyMultiClaw", self.report["changed"])
        aoe = child(self.rules.resolve_weapon("TSLaserHarpyAOEClaw"),
                    "Warhead@Laser_HeavyFlatCompatibility")
        self.assertEqual("300", str(aoe.get("Spread")))
        self.assertEqual("100, 50, 25", str(aoe.get("Falloff")))

    def test_comparison_is_exactly_the_reviewed_role_change(self):
        selected = set(cohort.selections(self.rules)) - {"TSLaserHarpyMultiClaw"}
        self.assertEqual(selected, set(self.report["changed"]))
        self.assertEqual([], self.report["added"])
        self.assertEqual([], self.report["removed"])
        self.assertEqual(set(ACCEPTED), set(self.by_kind))
        for kind, (count, expected_hash) in ACCEPTED.items():
            payload = json.dumps(self.by_kind[kind], sort_keys=True,
                                 separators=(",", ":")).encode()
            self.assertEqual(count, len(self.by_kind[kind]), kind)
            self.assertEqual(expected_hash, hashlib.sha256(payload).hexdigest(), kind)

    def test_percentage_changes_are_only_the_guarded_one_hp_rounding_cases(self):
        self.assertEqual(cohort.EXACT_PLUS_ONE,
                         set(self.by_kind["percentage_damage"]))
        for name, groups in self.by_kind["percentage_damage"].items():
            rows = [row for group in groups for row in group]
            self.assertTrue(rows, name)
            for _health, before, after in rows:
                self.assertEqual(1, after - before, name)

    def test_ratchets_match_live_reduction(self):
        self.assertEqual(114, SPLIT_BASELINE)
        self.assertEqual(90, BROADCAST_BASELINE)


if __name__ == "__main__":
    unittest.main()
