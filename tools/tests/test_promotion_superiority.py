"""Focused pure checks for the promotion replacement audit."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
import audit_promotion_superiority as audit  # noqa: E402


class PromotionSuperiorityTests(unittest.TestCase):
    def test_negative_prerequisite_parser_accepts_openra_forms(self):
        self.assertEqual(audit.parse_negative_promotion_token("~!foo"), "foo")
        self.assertEqual(audit.parse_negative_promotion_token("!foo"), "foo")
        self.assertIsNone(audit.parse_negative_promotion_token("~foo"))

    def test_numeric_comparison_is_explicit(self):
        self.assertEqual(audit.compare_value(10, 12)["status"], "UP")
        self.assertEqual(audit.compare_value(10, 10)["status"], "SAME")
        self.assertEqual(audit.compare_value(10, 8)["status"], "DOWN")
        self.assertEqual(audit.compare_value(None, 8)["status"], "UNRESOLVED")

    def test_warhead_classes_are_compared_as_labels_not_strength_ranks(self):
        result = audit.compare_warheads(
            ["^Warhead_CannonHE_Medium"], ["^Warhead_Railgun_Heavy"])
        self.assertEqual(result["status"], "DIFFERENT_LABELS")
        self.assertNotIn("base_rank", result)

    def test_armor_comparison_does_not_cross_unit_types(self):
        result = audit.compare_armor("inf", "veh", "Heroic", "Light")
        self.assertEqual(result["status"], "CROSS_TYPE")

    def test_armor_labels_do_not_claim_universal_strength(self):
        self.assertEqual(audit.compare_armor("veh", "veh", "Light", "Heavy")["status"],
                         "DIFFERENT_LABELS")

    def test_interceptor_weapon_name_is_not_a_point_defense_slot(self):
        self.assertFalse(audit._is_non_offensive_armament({
            "slot": "Armament", "weapon": "fighter_interceptor_cannon"}))

    def test_shared_token_uses_explicit_pair_without_cross_join(self):
        result = audit.replacement_disposition(
            "td_gdi_promotion_havocandexosuit",
            ["td_gdi_commando"],
            ["td_gdi_exosuit", "td_gdi_havoc"],
        )
        self.assertEqual(result["pairs"], [{
            "base_actor": "td_gdi_commando",
            "promotion_actor": "td_gdi_havoc",
        }])
        self.assertEqual(result["additional_options"], ["td_gdi_exosuit"])

    def test_weapon_metrics_and_identity_share_the_selected_armament(self):
        unit = {"armaments": [
            {
                "slot": "Armament@pointdefense", "armament_name": "pointdefense",
                "weapon": "PDLaserLTNK2", "range": "4903", "reloaddelay": "25",
                "damage_warheads": [{"type": "SpreadDamage", "damage": "1"}],
            },
            {
                "slot": "Armament", "weapon": "td_nod_lighttankmkii_lighttank2cannon",
                "range": "4903", "reloaddelay": "35",
                "damage_warheads": [{"type": "AreaDamage", "damage": "8000"}],
                "warheads": ["^Warhead_CannonHE_Medium"],
            },
        ]}
        metrics = audit.offensive_armament_metrics(unit)
        self.assertEqual(
            metrics["armament"]["weapon"],
            "td_nod_lighttankmkii_lighttank2cannon",
        )
        self.assertGreater(metrics["dps"], 1)


if __name__ == "__main__":
    unittest.main()
