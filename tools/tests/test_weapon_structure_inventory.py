import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Ruleset
from survey_weapon_structure import (
    RAW_REACHABLE_BASELINE,
    RAW_REACHABLE_EXCESS_BASELINE,
    canonical_weapon_names,
    inventory,
    ratchet_errors,
    weapon_reference_sets,
)


class WeaponStructureInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.data = inventory(cls.rules)

    def test_partition_is_complete_and_disjoint(self):
        sets = self.data["sets"]
        direct = set(sets["direct_actor_armament"])
        indirect = set(sets["indirect_weapon_graph"])
        unreached = set(sets["unreached"])
        self.assertFalse(direct & indirect)
        self.assertFalse(direct & unreached)
        self.assertFalse(indirect & unreached)
        self.assertEqual(
            self.data["counts"]["stacked_main_all_concrete"],
            len(direct | indirect | unreached),
        )

    def test_direct_is_a_subset_of_transitive_reachability(self):
        counts = self.data["counts"]
        self.assertEqual(
            counts["stacked_main_transitive_weapon_graph"],
            counts["stacked_main_direct_actor_armament"]
            + counts["stacked_main_indirect_weapon_graph"],
        )

    def test_current_corrected_baseline(self):
        self.assertEqual(2346, self.data["counts"]["concrete_weapons"])
        self.assertEqual(340, self.data["counts"]["stacked_main_all_concrete"])
        self.assertEqual(190, self.data["counts"]["stacked_main_direct_actor_armament"])
        self.assertEqual(50, self.data["counts"]["stacked_main_indirect_weapon_graph"])
        self.assertEqual(240, self.data["counts"]["stacked_main_transitive_weapon_graph"])
        self.assertEqual(100, self.data["counts"]["stacked_main_unreached"])
        self.assertEqual(2626, self.data["counts"]["main_warhead_instances_all_concrete"])
        self.assertEqual(597, self.data["counts"]["excess_main_warhead_instances_all_concrete"])
        self.assertEqual(2200, self.data["counts"]["main_warhead_instances_transitive_weapon_graph"])
        self.assertEqual(452, self.data["counts"]["excess_main_warhead_instances_transitive_weapon_graph"])
        self.assertEqual(226, self.data["counts"]["reviewed_stacked_main_all_concrete"])
        self.assertEqual(178, self.data["counts"]["reviewed_stacked_main_direct_actor_armament"])
        self.assertEqual(48, self.data["counts"]["reviewed_stacked_main_indirect_weapon_graph"])
        self.assertEqual(226, self.data["counts"]["reviewed_stacked_main_transitive_weapon_graph"])
        self.assertEqual(114, self.data["counts"]["unreviewed_stacked_main_all_concrete"])
        self.assertEqual(14, self.data["counts"]["unreviewed_stacked_main_transitive_weapon_graph"])
        self.assertEqual(434, self.data["counts"]["reviewed_excess_main_warhead_instances_all_concrete"])
        self.assertEqual(434, self.data["counts"]["reviewed_excess_main_warhead_instances_transitive_weapon_graph"])
        self.assertEqual(163, self.data["counts"]["unreviewed_excess_main_warhead_instances_all_concrete"])
        self.assertEqual(18, self.data["counts"]["unreviewed_excess_main_warhead_instances_transitive_weapon_graph"])

    def test_raw_reachable_ratchets_match_the_checkpoint(self):
        self.assertEqual(240, RAW_REACHABLE_BASELINE)
        self.assertEqual(452, RAW_REACHABLE_EXCESS_BASELINE)
        self.assertEqual([], ratchet_errors(self.data))

    def test_engine_weapon_reference_fields_are_followed(self):
        reached = (set(self.data["sets"]["direct_actor_armament"])
                   | set(self.data["sets"]["indirect_weapon_graph"]))
        expected = {
            "Atomic", "CabalMagicNuke", "NaxiV1Rocket",
            "PulseMissile", "RAAtomic",
        }
        self.assertTrue(expected <= reached)
        self.assertTrue(expected.isdisjoint(self.data["sets"]["unreached"]))
        concrete = {
            name for name in self.rules.weapons
            if not name.startswith("^") and self.rules.resolve_weapon(name) is not None
        }
        _direct, reachable = weapon_reference_sets(self.rules, concrete)
        self.assertIn("AsianHowitzerSplash", reachable)
        self.assertIn("NaxisBlackBombSmaller", reachable)
        self.assertNotIn("NaxisBlackBombSmaller", reached)

    def test_weapon_references_match_definition_names_case_insensitively(self):
        concrete = {
            name for name in self.rules.weapons
            if not name.startswith("^") and self.rules.resolve_weapon(name) is not None
        }
        direct, reachable = weapon_reference_sets(self.rules, concrete)
        self.assertIn("Claw", direct)
        self.assertTrue({
            "AsianIonbeam", "Atomic", "Claw", "RAAtomic", "TSIonbeam",
        } <= reachable)

    def test_canonical_lookup_matches_engine_lowercase_semantics(self):
        self.assertEqual({"atomic": "Atomic"}, canonical_weapon_names({"Atomic"}))
        with self.assertRaisesRegex(ValueError, "differ only by letter case"):
            canonical_weapon_names({"Atomic", "atomic"})


if __name__ == "__main__":
    unittest.main()
