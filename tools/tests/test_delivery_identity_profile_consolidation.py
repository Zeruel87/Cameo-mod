import collections
import hashlib
import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/machinegun_profile_comparison.json"
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import consolidate_delivery_identity_profiles as delivery
import consolidate_machinegun_profiles as machineguns
from audit_three_way_split import RAW_SPLIT_BASELINE, main_warheads
from audit_warhead_split import BROADCAST_BASELINE
from miniyaml import Ruleset


ACCEPTED = {
    "blast_shape": (
        31, "52ddc6c3670fd48cc02c82d4de5491d9278004f6e51828f3004471ac6f58690a"),
    "percentage_damage": (
        29, "b947767d35f79bac2e778cd02d3d371ba3ab43f7bcf7a68d040d5fe4663d52c6"),
}


class DeliveryIdentityProfileConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.by_kind = collections.defaultdict(dict)
        for weapon, changes in cls.report["changed"].items():
            for change in changes:
                cls.by_kind[change[0]][weapon] = change[1:]

    def test_converters_are_fully_applied(self):
        machineguns.validate_result()
        delivery.validate_result()

    def test_report_covers_exactly_the_selected_definitions(self):
        selected = set(machineguns.selections(self.rules)) | set(delivery.selections(self.rules))
        self.assertEqual(31, len(selected))
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

    def test_percentage_delta_is_bounded_to_one_hp(self):
        deltas = []
        for changes in self.by_kind["percentage_damage"].values():
            for mismatch_rows in changes:
                deltas.extend(abs(before - after)
                              for _hp, before, after in mismatch_rows)
        self.assertEqual(1, max(deltas))

    def test_manta_ground_and_air_routes_keep_distinct_profiles(self):
        ground = {
            "SteelMantaHunterCannons", "SteelMantaHunterCannonsResonance",
            "SteelMantaHunterCannonsResonanceBounce1",
            "SteelMantaHunterCannonsResonanceBounce2",
        }
        air = {
            "SteelMantaHunterCannons_AA", "SteelMantaHunterCannonsAAResonance_AA",
            "SteelMantaHunterCannonsAAResonanceBounce1",
            "SteelMantaHunterCannonsAAResonanceBounce2",
        }
        for weapon in ground:
            mains = main_warheads(self.rules.resolve_weapon(weapon))
            self.assertIn("Bullet_MediumFlatCompatibility", mains, weapon)
            self.assertNotIn("Flak_MediumFlatCompatibility", mains, weapon)
        for weapon in air:
            mains = main_warheads(self.rules.resolve_weapon(weapon))
            self.assertIn("Flak_MediumFlatCompatibility", mains, weapon)
            self.assertNotIn("Bullet_MediumFlatCompatibility", mains, weapon)

    def test_selected_old_profile_pairs_are_absent(self):
        for weapon, destination in machineguns.selections(self.rules).items():
            mains = set(main_warheads(self.rules.resolve_weapon(weapon)))
            self.assertTrue(mains.isdisjoint(machineguns.PAIR), weapon)
            expected = machineguns.FINALIZED_DOWNSTREAM.get(
                weapon, (f"{destination}FlatCompatibility", 0, 0))[0]
            self.assertIn(expected, mains, weapon)
        for weapon, (destination, pair, _root) in delivery.selections(self.rules).items():
            mains = set(main_warheads(self.rules.resolve_weapon(weapon)))
            self.assertTrue(mains.isdisjoint(pair), weapon)
            self.assertIn(f"{destination}FlatCompatibility", mains, weapon)

    def test_routing_and_overflow_hazards_remain_unconverted(self):
        deferred = {
            "AlliedTankDestroyerCannon",
        }
        for weapon in deferred:
            self.assertGreater(len(main_warheads(self.rules.resolve_weapon(weapon))), 1, weapon)

        # This AA child still carries the deferred route-specific Medium nodes,
        # but they have no Damage and therefore are not active second mains.
        # Guard their continued presence without corrupting the shared damage
        # predicate to keep the old survey count.
        humvee = self.rules.resolve_weapon("MachineGunHumvee2_AA")
        keys = {child.key for child in humvee.children}
        self.assertIn("Warhead@Bullet_Light", keys)
        self.assertIn("Warhead@Bullet_Medium", keys)

    def test_ratchets_match_the_live_reduction(self):
        # Upstream retired exemptions: enforce the raw ceiling, never subtract reviewed stacks.
        self.assertLessEqual(RAW_SPLIT_BASELINE, 322)
        self.assertLessEqual(BROADCAST_BASELINE, 69)


if __name__ == "__main__":
    unittest.main()
