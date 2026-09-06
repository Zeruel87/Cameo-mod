import collections
import hashlib
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/high_identity_profile_comparison.json"
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import consolidate_high_identity_profiles as cohort
from audit_three_way_split import SPLIT_BASELINE, main_warheads
from audit_warhead_split import BROADCAST_BASELINE
from miniyaml import Ruleset


ACCEPTED = {
    "blast_shape": (
        6, "38c52ac0863726e8e88663d9f7c3ba2ec4ba75f9e2f134d39df09827a70d6948"),
    "percentage_damage": (
        1, "9b318b8f3ddbb4aff8baeee3c265326e7682dc8237cc917ce64506fac9f4c8b8"),
}


class HighIdentityProfileConsolidationTests(unittest.TestCase):
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

    def test_exact_closures_and_destinations_are_pinned(self):
        selected = cohort.selections(self.rules)
        self.assertEqual(6, len(selected))
        for root, (_destination, _old, expected, _total, _scale) in cohort.SPECS.items():
            self.assertEqual(expected, cohort.descendants(self.rules, root), root)
        for name, (destination, _old, total, scale) in selected.items():
            resolved = self.rules.resolve_weapon(name)
            key = f"{destination}FlatCompatibility"
            self.assertEqual([key], main_warheads(resolved), name)
            node = next(child for child in resolved.children
                        if child.key == f"Warhead@{key}")
            self.assertEqual(total, int(str(node.get("Damage"))), name)
            self.assertEqual(scale, int(str(node.get("PercentageScale"))), name)

    def test_full_ruleset_comparison_matches_accepted_manifest(self):
        self.assertEqual(set(cohort.selections(self.rules)), set(self.report["changed"]))
        self.assertEqual([], self.report["added"])
        self.assertEqual([], self.report["removed"])
        self.assertEqual(set(ACCEPTED), set(self.by_kind))
        for kind, (count, expected_hash) in ACCEPTED.items():
            payload = json.dumps(
                self.by_kind[kind], sort_keys=True, separators=(",", ":")
            ).encode()
            self.assertEqual(count, len(self.by_kind[kind]), kind)
            self.assertEqual(expected_hash, hashlib.sha256(payload).hexdigest(), kind)

    def test_only_one_hp_of_bounded_percentage_rounding_changes(self):
        self.assertEqual(
            [[[20, 0, 1], [160, 7, 8]]],
            self.by_kind["percentage_damage"]["TSAssaultCannonTalSonic"],
        )

    def test_later_authorized_delivery_cases_are_consolidated(self):
        consolidated = {
            "tkmjuggap", "tkmtechnicalmgap",
        }
        for name in consolidated:
            self.assertEqual(len(main_warheads(self.rules.resolve_weapon(name))), 1, name)

    def test_ratchets_match_live_reduction(self):
        self.assertEqual(114, SPLIT_BASELINE)
        self.assertEqual(90, BROADCAST_BASELINE)


if __name__ == "__main__":
    unittest.main()
