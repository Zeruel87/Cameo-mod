import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

import classify_remaining_weapons as classifier
from miniyaml import Ruleset


class RemainingWeaponClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = classifier.classify(Ruleset(ROOT))

    def test_active_central_files_are_included_without_template_bleed(self):
        active_files = {path.resolve() for path in classifier.weapon_files()}
        self.assertIn((ROOT / "mods/cameo/weapons/d2k.yaml").resolve(), active_files)
        self.assertIn((ROOT / "mods/cameo/weapons/redalert2mod.yaml").resolve(), active_files)
        self.assertIn((ROOT / "mods/cameo/weapons/outpost2.yaml").resolve(), active_files)

    def test_reviewed_retired_flat_root_backlog_is_empty(self):
        self.assertEqual([], self.rows)

    def test_exact_reviewed_restoration_is_not_reopened_as_backlog(self):
        self.assertEqual({"HydraSpit"}, classifier.EXACT_REVIEWED_RESTORATIONS)
        self.assertNotIn("HydraSpit", {row["weapon"] for row in self.rows})
        exact = {"ArrowWeapon", "LightChemicalWeapon", "LightMissile", "SmallArms"}
        self.assertTrue(classifier.is_exact_reviewed_restoration("HydraSpit", exact))
        self.assertFalse(classifier.is_exact_reviewed_restoration(
            "HydraSpit", exact - {"SmallArms"}))

    def test_special_positive_damage_warheads_are_not_flat_health_slices(self):
        rules = Ruleset(ROOT)
        old_keys = classifier.positive_flat_keys(rules, "^SniperWeapon")
        self.assertIn("SniperWeapon", old_keys)
        self.assertNotIn("SniperWeaponExtraDamage", old_keys)

        weapon = rules.resolve_weapon("RA2CRM60H")
        flat_tags = {hit["tag"] for hit in classifier.flat_ledger(weapon)}
        self.assertNotIn("SniperWeaponExtraDamage", flat_tags)

    def test_ambiguous_signals_remain_human_reviewed(self):
        bucket, candidate, reasons = classifier.choose_review_bucket(
            ["^RailgunWeapon", "^MediumMissile"], [], [], "Railgun", "Missile",
            "legacy evidence is mixed")
        self.assertEqual("human decision required", bucket)
        self.assertIsNone(candidate)
        self.assertIn("name and legacy signals disagree", reasons)

    def test_multiple_canonical_tiers_remain_human_reviewed(self):
        bucket, candidate, reasons = classifier.choose_review_bucket(
            ["^MediumMissile"], ["MissileAP_Light", "MissileAP_Heavy"],
            ["MissileAP"], None, "MissileAP", "")
        self.assertEqual("human decision required", bucket)
        self.assertIsNone(candidate)
        self.assertIn("multiple inherited family/tier destinations", reasons)

    def test_exception_families_are_never_automatic(self):
        bucket, _, reasons = classifier.choose_review_bucket(
            ["^NuclearWarhead"], ["Nuclear_Super"], ["Nuclear"],
            "Nuclear", "Nuclear", "")
        self.assertEqual("human decision required", bucket)
        self.assertIn("exception-bearing retired family", reasons)

    def test_folded_percentage_hit_is_recorded_beside_its_flat_hit(self):
        weapon = Ruleset(ROOT).resolve_weapon("120mm_td")
        self.assertIn("CannonHE_Medium", {hit["tag"] for hit in classifier.flat_ledger(weapon)})
        folded = [hit for hit in classifier.percentage_ledger(weapon)
                  if hit["tag"] == "CannonHE_Medium" and hit["kind"] == "pct_folded"]
        self.assertEqual(1, len(folded))
        self.assertEqual(2499, folded[0]["scale"])
        self.assertEqual(10000, folded[0]["denominator"])
        self.assertIn("Shield", folded[0]["percentage_versus"])

    def test_percentage_physical_state_map_is_recorded(self):
        weapon = Ruleset(ROOT).resolve_weapon("120mm_td")
        states = [state for hit in classifier.percentage_ledger(weapon)
                  for state in hit["physical_states"]]
        self.assertIn({"name": "Corrosion", "scale": "100", "source": "map"}, states)

if __name__ == "__main__":
    unittest.main()
