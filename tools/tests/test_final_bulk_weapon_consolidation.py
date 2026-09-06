import collections
import hashlib
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/multi_main_bulk2_comparison.json"
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import consolidate_final_safe_cohorts as final_cohorts
from audit_three_way_split import SPLIT_BASELINE, main_warheads
from miniyaml import Ruleset


ACCEPTED = {
    "blast_shape": (97, "506188c73ee71f6bbc8b3e2c60d02a91f1d5b45d761294be84f97958afc99715"),
    "percentage_damage": (32, "3ed3b8d806745612655e253766878c7697ea8a385d936f8e5366fc253331b2d1"),
}


class FinalBulkWeaponConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.by_kind = collections.defaultdict(dict)
        for weapon, changes in cls.report["changed"].items():
            for change in changes:
                cls.by_kind[change[0]][weapon] = change[1:]

    def test_converters_are_fully_applied_and_idempotent(self):
        final_cohorts.validate_result()

    def test_whole_tree_change_manifest_is_exact(self):
        self.assertEqual([], self.report["removed"])
        self.assertEqual([], self.report["added"])
        self.assertEqual(set(ACCEPTED), set(self.by_kind))
        for kind, (expected_count, expected_hash) in ACCEPTED.items():
            payload = json.dumps(
                self.by_kind[kind], sort_keys=True, separators=(",", ":")
            ).encode()
            self.assertEqual(expected_count, len(self.by_kind[kind]), kind)
            self.assertEqual(expected_hash, hashlib.sha256(payload).hexdigest(), kind)

    def test_percentage_rounding_delta_is_never_more_than_one_hp(self):
        deltas = []
        for changes in self.by_kind["percentage_damage"].values():
            for mismatch_rows in changes:
                deltas.extend(abs(before - after)
                              for _hp, before, after in mismatch_rows)
        self.assertEqual(1, max(deltas))

    def test_every_final_cohort_has_one_selected_main(self):
        rules = Ruleset(ROOT)
        selected = final_cohorts.selections(rules)
        self.assertEqual(39, len(selected))
        for weapon, destination in selected.items():
            resolved = rules.resolve_weapon(weapon)
            self.assertEqual(
                [f"{destination}FlatCompatibility"],
                main_warheads(resolved), weapon)

    def test_selected_templates_are_not_reinherited_through_children(self):
        rules = Ruleset(ROOT)
        selected = final_cohorts.selections(rules)

        def ancestors(name):
            seen = set()
            stack = [parent for _, parent in rules.inherits_of(rules.weapon(name))
                     if parent in rules.weapons]
            while stack:
                parent = stack.pop()
                if parent in seen:
                    continue
                seen.add(parent)
                stack.extend(
                    grandparent for _, grandparent in rules.inherits_of(rules.weapon(parent))
                    if grandparent in rules.weapons)
            return seen

        for weapon in selected:
            local = rules.weapon(weapon)
            own = {
                str(child.value) for child in local.children
                if child.key == "Inherits@finalmain"
            }
            inherited = {
                str(child.value)
                for parent in ancestors(weapon)
                for child in rules.weapon(parent).children
                if child.key.startswith("Inherits")
            }
            self.assertTrue(own.isdisjoint(inherited), weapon)

    def test_structural_backlog_ratchet_was_lowered(self):
        self.assertEqual(114, SPLIT_BASELINE)

    def test_rejected_runtime_and_role_hazards_remain_unconverted(self):
        rules = Ruleset(ROOT)
        deferred = {
            # Live percentage quantisation or inherited percentage drift.
            "RA2FreedomRocket_elite", "RA2120xmm_rad",
            # Split ground/air routing without a reviewed single profile.
            "d2k_shotgun",
            # Friendly-fire or physical-state behavior would change.
            "BCYamatoCannon", "HMGo_upgrade",
            # Semantic name/delivery traps from the independent review.
            "SteelAirTurret_elite",
        }
        for weapon in deferred:
            self.assertGreater(len(main_warheads(rules.resolve_weapon(weapon))), 1, weapon)


if __name__ == "__main__":
    unittest.main()
