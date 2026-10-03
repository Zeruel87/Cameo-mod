import collections
import hashlib
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/remaining_roots_merged_baseline_diff.json"
sys.path.insert(0, str(ROOT / "tools" / "audit"))
from miniyaml import Ruleset

# Full before/after payload hashes form a strict accepted-change manifest. This
# keeps the allowlist compact while ensuring that any weapon, armor modifier,
# target mask, relationship, physical state, or blast-profile drift fails.
ACCEPTED = {
    "ValidTargets": (2, "10e2904ec42a59cca1eb5c12f4e00dde43dbb366a4903a367a1d4d8b7684bba5"),
    "blast_shape": (158, "d8e607c9f266cd2a9793b876948463870038469d8bf8299df721e37a97f0589a"),
    "invalid_target_damage": (123, "d36c35346063ca036fc82e06351210a32f798ed0ab0b63ad9c468d7913e202f3"),
    "percentage_warheads": (2, "55ea6fb28aab629d5f1da7de4a1b7688d2390ede69ac69389230044b9c691ded"),
    "physical_state_bindings": (115, "29c1593c98fa87d23c7011a3cbd56ebb93e1c5ad459d8a2076c935c90613c99e"),
    "relationship_stat_damage": (158, "2cf4426632e2d013f2217236da816a6fecc54cc471b83765a86282dfdea783b3"),
    "top_level": (2, "4630208ae74eae8fa6dfc5933b05cbf2396d90adedb9536e332959f88b36e049"),
    "valid_target_damage": (95, "c600c441925a75d9fc747e8720a671400b5d743e502b97f0fcde613a636b9604"),
}


class RemainingRootsComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.by_kind = collections.defaultdict(dict)
        for weapon, changes in cls.report["changed"].items():
            for change in changes:
                cls.by_kind[change[0]][weapon] = change[1:]

    def test_only_reviewed_orphan_is_removed(self):
        self.assertEqual(["HueyFireMissiles"], self.report["removed"])
        self.assertEqual([], self.report["added"])

    def test_every_behavior_change_matches_the_accepted_manifest(self):
        self.assertEqual(set(ACCEPTED), set(self.by_kind))
        for kind, (expected_count, expected_hash) in ACCEPTED.items():
            payload = json.dumps(
                self.by_kind[kind], sort_keys=True, separators=(",", ":")
            ).encode()
            self.assertEqual(expected_count, len(self.by_kind[kind]), kind)
            self.assertEqual(expected_hash, hashlib.sha256(payload).hexdigest(), kind)

    def test_direct_weapon_contract_changes_are_only_the_approved_goliath_split(self):
        expected = {"GoliathMk2MG", "GoliathMk2Rockets_AA"}
        self.assertEqual(expected, set(self.by_kind["ValidTargets"]))
        self.assertEqual(expected, set(self.by_kind["top_level"]))
        self.assertEqual(expected, set(self.by_kind["percentage_warheads"]))

    def test_compatibility_profiles_are_not_inherited_twice(self):
        rules = Ruleset(ROOT)
        duplicates = []
        for name, local in rules.weapons.items():
            local_roles = {
                child.value for child in local.children
                if child.key.startswith("Inherits@roleflat")
            }
            for child in local.children:
                if child.key != "Inherits" and not child.key.startswith("Inherits@"):
                    continue
                parent = rules.weapon(child.value)
                if parent is None:
                    continue
                parent_roles = {
                    item.value for item in parent.children
                    if item.key.startswith("Inherits@roleflat")
                }
                for role in local_roles & parent_roles:
                    duplicates.append((name, role, child.value))
        self.assertEqual([], duplicates)

    def test_warhead_removals_exist_in_a_parent_or_the_local_block(self):
        rules = Ruleset(ROOT)
        invalid = []
        for name, local in rules.weapons.items():
            removals = {
                child.key[1:] for child in local.children
                if child.key.startswith("-Warhead@")
            }
            if not removals:
                continue
            available = {
                child.key for child in local.children
                if child.key.startswith("Warhead@")
            }
            for child in local.children:
                if child.key != "Inherits" and not child.key.startswith("Inherits@"):
                    continue
                parent = rules.resolve_weapon(child.value)
                if parent is not None:
                    available.update(
                        item.key for item in parent.children
                        if item.key.startswith("Warhead@")
                    )
            invalid.extend((name, key) for key in removals - available)
        self.assertEqual([], sorted(invalid))


if __name__ == "__main__":
    unittest.main()
