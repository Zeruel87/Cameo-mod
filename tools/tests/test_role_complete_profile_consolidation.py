import collections
import hashlib
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/role_complete_profile_comparison.json"
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import consolidate_role_complete_profiles as cohort
from audit_three_way_split import RAW_SPLIT_BASELINE, main_warheads
from audit_warhead_split import BROADCAST_BASELINE
from miniyaml import Ruleset


ACCEPTED = {
    "blast_shape": (
        20, "c3239489ed89040e8ae62f9267dd875a5536bf1c7df4c350696b828689bb722a"),
    "percentage_damage": (
        8, "7358ff3208ab5f09c1368032cbcb44d4225acfca563ef436d406749a13075bb2"),
}


class RoleCompleteProfileConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        # Preserve the historical report's selection. Ruling 10(a), e76fb585c0,
        # deliberately made ordos_airmine self-contained; never reattach it.
        cls.historical_selection = {
            name: spec[0] for root, spec in cohort.ROOTS.items()
            for name in {root, *spec[2]}
        }
        cls.historical_selection.update(dict.fromkeys(cohort.MANTA_AG, "Bullet_Medium"))
        cls.historical_selection.update(dict.fromkeys(cohort.MANTA_AA, "Flak_Medium"))
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.by_kind = collections.defaultdict(dict)
        for weapon, changes in cls.report["changed"].items():
            for change in changes:
                cls.by_kind[change[0]][weapon] = change[1:]

    def test_historical_converter_rejects_changed_closure_but_live_profiles_hold(self):
        with self.assertRaisesRegex(RuntimeError, "ixian_airdrone: closure changed"):
            cohort.validate_result()
        plans, already = cohort.inspect(self.rules, self.historical_selection)
        self.assertTrue(already)
        self.assertEqual(set(self.historical_selection), set(plans))
        self.assertTrue(all(value is None for value in plans.values()))
        for root, spec in cohort.ROOTS.items():
            expected = set() if root == "ixian_airdrone" else spec[2]
            self.assertEqual(expected, cohort.descendants(self.rules, root), root)
        self.assertEqual((cohort.MANTA_AG | cohort.MANTA_AA) - {cohort.MANTA_ROOT},
                         cohort.descendants(self.rules, cohort.MANTA_ROOT))

    def test_report_covers_exactly_the_selected_definitions(self):
        selected = set(self.historical_selection)
        self.assertEqual(20, len(selected))
        self.assertEqual(selected, set(self.report["changed"]))
        self.assertEqual([], self.report["added"])
        self.assertEqual([], self.report["removed"])

    def test_every_change_matches_the_accepted_manifest(self):
        self.assertEqual(set(ACCEPTED), set(self.by_kind))
        for kind, (count, expected_hash) in ACCEPTED.items():
            payload = json.dumps(
                self.by_kind[kind], sort_keys=True, separators=(",", ":")
            ).encode()
            self.assertEqual(count, len(self.by_kind[kind]), kind)
            self.assertEqual(expected_hash, hashlib.sha256(payload).hexdigest(), kind)

    def test_manta_percentage_delta_is_exactly_bounded(self):
        for weapon, changes in self.by_kind["percentage_damage"].items():
            rows = [row for group in changes for row in group]
            self.assertEqual([[160, 4, 6], [250, 8, 10]], rows, weapon)

    def test_ground_and_air_routes_have_only_their_role_profile(self):
        for weapon in cohort.MANTA_AG:
            self.assertEqual(
                ["Bullet_MediumFlatCompatibility"],
                main_warheads(self.rules.resolve_weapon(weapon)), weapon)
        for weapon in cohort.MANTA_AA:
            self.assertEqual(
                ["Flak_MediumFlatCompatibility"],
                main_warheads(self.rules.resolve_weapon(weapon)), weapon)

    def test_authored_damage_types_are_explicit(self):
        expected = {}
        for root, (destination, _mains, children, _total, _scale,
                   damage_types) in cohort.ROOTS.items():
            if damage_types:
                for weapon in {root, *children}:
                    expected[weapon] = (destination, damage_types)
        selected = self.historical_selection
        self.assertEqual(8, len(expected))
        for weapon, (destination, damage_types) in expected.items():
            self.assertEqual(destination, selected[weapon])
            resolved = self.rules.resolve_weapon(weapon)
            node = next(child for child in resolved.children
                        if child.key == f"Warhead@{destination}FlatCompatibility")
            self.assertEqual(damage_types, str(node.get("DamageTypes")), weapon)

    def test_air_mine_keeps_its_distinct_air_only_damage(self):
        self.assertNotIn("ordos_airmine", cohort.descendants(self.rules, "ixian_airdrone"))
        self.assertEqual(
            {"MissileAP_HeavyFlatCompatibility", "1Dam"},
            set(main_warheads(self.rules.resolve_weapon("ordos_airmine"))))

    def test_ratchets_match_the_live_reduction(self):
        # Upstream retired exemptions: enforce the raw ceiling, never subtract reviewed stacks.
        self.assertLessEqual(RAW_SPLIT_BASELINE, 322)
        self.assertLessEqual(BROADCAST_BASELINE, 69)


if __name__ == "__main__":
    unittest.main()
