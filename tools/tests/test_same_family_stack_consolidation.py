import collections
import hashlib
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/multi_main_bulk1_comparison.json"
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import consolidate_adjacent_family_stacks as adjacent
import consolidate_same_family_stacks as bullets
from miniyaml import Ruleset


ACCEPTED = {
    "blast_shape": (58, "1d98833c3e8b7c5af97a31cb3e661d8d7a827209e79940e21a4eef04d3655bb5"),
    "percentage_damage": (37, "96c58209bb143413b6d2c8115c8e83200740f8827e83435be0b40bab4ca109fc"),
}


class SameFamilyStackConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.by_kind = collections.defaultdict(dict)
        for weapon, changes in cls.report["changed"].items():
            for change in changes:
                cls.by_kind[change[0]][weapon] = change[1:]

    def test_resolved_closures_are_fully_consolidated(self):
        bullets.validate_result()
        adjacent.validate_result()

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

        selected = set()
        for root, closure in bullets.ROOT_CLOSURES.items():
            selected.update({root, *closure})
        for root, (_, _, closure) in adjacent.SPECS.items():
            selected.update({root, *closure})
        self.assertEqual(selected, set(self.report["changed"]))

    def test_percentage_rounding_delta_never_exceeds_one_hp(self):
        deltas = []
        for changes in self.by_kind["percentage_damage"].values():
            for mismatch_rows in changes:
                deltas.extend(abs(before - after)
                              for _, before, after in mismatch_rows)
        self.assertEqual(1, max(deltas))

    def test_selected_armor_and_geometry_profiles_match_delivery_tier(self):
        rules = Ruleset(ROOT)
        selections = {
            root: ("Bullet_Medium", closure)
            for root, closure in bullets.ROOT_CLOSURES.items()
        }
        selections.update({
            root: (destination, closure)
            for root, (_, destination, closure) in adjacent.SPECS.items()
        })

        def node_fingerprint(node):
            return (node.key, node.value,
                    tuple(node_fingerprint(child) for child in node.children))

        for root, (destination, closure) in selections.items():
            canonical_weapon = rules.resolve_weapon(f"^Warhead_{destination}")
            canonical = next(
                child for child in canonical_weapon.children
                if child.key == f"Warhead@{destination}"
            )
            expected = {
                key: node_fingerprint(canonical.child(key))
                if canonical.child(key) is not None else None
                for key in ("Versus", "PercentageVersus")
            }
            expected.update({
                key: canonical.get(key)
                for key in ("Spread", "Falloff", "DamageTypes", "PercentageSpread")
            })
            for weapon in [root, *sorted(closure)]:
                resolved = rules.resolve_weapon(weapon)
                actual = next(
                    child for child in resolved.children
                    if child.key == f"Warhead@{destination}FlatCompatibility"
                )
                profile = {
                    key: node_fingerprint(actual.child(key))
                    if actual.child(key) is not None else None
                    for key in ("Versus", "PercentageVersus")
                }
                profile.update({
                    key: actual.get(key)
                    for key in ("Spread", "Falloff", "DamageTypes", "PercentageSpread")
                })
                self.assertEqual(expected, profile, weapon)

    def test_role_and_target_contract_hazards_remain_deferred(self):
        deferred = {
            "RA220mmrapid", "CabalCyborgChaingun", "TSDevoutChainguns",
            "CommandoRocketLauncher", "RocketsRA", "SheridanMissiles",
            "CabalRocketCyborgRockets", "CabalRocketCyborgRocketsUpgraded",
            "TSBikeMissile", "TigerCannon",
            "Type97Cannon", "TSZoneHellfireSonic",
        }
        selected = set(bullets.ROOT_CLOSURES) | set(adjacent.SPECS)
        self.assertTrue(deferred.isdisjoint(selected))


if __name__ == "__main__":
    unittest.main()
