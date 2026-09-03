import collections
import hashlib
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/routed_role_cohort_comparison.json"
sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]

import consolidate_routed_role_cohort as cohort
from audit_three_way_split import SPLIT_BASELINE, main_warheads
from audit_warhead_split import BROADCAST_BASELINE
from miniyaml import Ruleset

ACCEPTED = {
    "percentage_damage": (15, "4d1f2855e2b7a7fbdee701c82590842369e57c63cd9d18f57b65899e33b6cc3d"),
    "blast_shape": (19, "187b2146154d3122d0939a92073807b7c977ff0e2a9c25f279350a2c292aba40"),
}


class RoutedRoleCohortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.by_kind = collections.defaultdict(dict)
        for weapon, changes in cls.report["changed"].items():
            for change in changes:
                cls.by_kind[change[0]][weapon] = change[1:]

    def test_converter_and_closures_are_fully_pinned(self):
        cohort.validate_result()
        self.assertEqual(20, len(cohort.selections(self.rules)))
        for root, (_dest, expected, _total, _scale) in cohort.ROOTS.items():
            self.assertEqual(expected, cohort.descendants(self.rules, root), root)

    def test_exactly_nineteen_definitions_change(self):
        expected = set(cohort.selections(self.rules)) - set(cohort.PINS)
        self.assertEqual(19, len(expected))
        self.assertEqual(expected, set(self.report["changed"]))
        self.assertEqual([], self.report["added"])
        self.assertEqual([], self.report["removed"])

    def test_comparison_manifest_is_exact(self):
        self.assertEqual(set(ACCEPTED), set(self.by_kind))
        for kind, (count, digest) in ACCEPTED.items():
            payload = json.dumps(self.by_kind[kind], sort_keys=True,
                                 separators=(",", ":")).encode()
            self.assertEqual(count, len(self.by_kind[kind]), kind)
            self.assertEqual(digest, hashlib.sha256(payload).hexdigest(), kind)

    def test_percentage_delta_is_bounded_to_one_hp(self):
        for name, groups in self.by_kind["percentage_damage"].items():
            rows = [row for group in groups for row in group]
            self.assertTrue(rows, name)
            for _hp, before, after in rows:
                self.assertLessEqual(abs(after - before), 1, name)

    def test_route_sensitive_descendants_are_exactly_preserved(self):
        for name, (_total, _scale) in cohort.PINS.items():
            self.assertNotIn(name, self.report["changed"])
            mains = main_warheads(self.rules.resolve_weapon(name))
            self.assertEqual(cohort.PINNED_AFTER_MAINS[name], set(mains), name)
            self.assertTrue(all(tag.startswith("PreservedFlat_") for tag in mains), name)
        self.assertEqual(
            {"MissileAP_MediumFlatCompatibility"},
            set(main_warheads(self.rules.resolve_weapon(
                "NaxCorrosionRocketTrooper_elite"))),
        )

    def test_ratchets_match_live_reduction(self):
        self.assertEqual(114, SPLIT_BASELINE)
        self.assertEqual(90, BROADCAST_BASELINE)


if __name__ == "__main__":
    unittest.main()
