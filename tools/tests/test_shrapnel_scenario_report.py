import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "balance"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))
from miniyaml import Node
import shrapnel_scenario_report as report


def node(key, value="", children=()):
    return Node(key, value, list(children), pathlib.Path("fixture.yaml"), 1)


class ShrapnelScenarioReportTests(unittest.TestCase):
    def test_direct_payload_keeps_percentage_separate(self):
        weapon = node("A", children=[
            node("Warhead@flat", "AreaDamage", [node("Damage", "100")]),
            node("Warhead@folded", "AreaDamage", [
                node("Damage", "20"), node("PercentageScale", "10000")]),
        ])
        result = report.direct_payload(weapon)
        self.assertEqual(result["flat_damage"], 120)
        self.assertEqual(result["status"], "FLAT_PLUS_PERCENTAGE_UNRESOLVED")
        self.assertEqual(len(result["percentage_channels"]), 1)

    def test_zero_percentage_scale_is_flat_and_integrity_is_not_health(self):
        weapon = node("A", children=[
            node("Warhead@flat", "AreaDamage", [
                node("Damage", "100"), node("PercentageScale", "0")]),
            node("Warhead@integrity", "AffectsIntegrity", [node("Damage", "50")]),
        ])
        result = report.direct_payload(weapon)
        self.assertEqual(result["flat_damage"], 100)
        self.assertEqual(result["status"], "UNRESOLVED_CHANNEL")
        self.assertEqual(len(result["unsupported_channels"]), 1)

    def test_edge_credit_and_target_mask_are_explicit(self):
        parent = node("parent", children=[node("ValidTargets", "Ground, Air")])
        emitter = node("Warhead@parts", "FireShrapnel", [
            node("Weapon", "fragment"), node("Amount", "3"),
            node("AimChance", "50"), node("ThrowWithoutTarget", "false"),
        ])
        fragment = node("fragment", children=[node("ValidTargets", "Ground, Air")])
        edge = report._edge_record("parent", parent, emitter, fragment, "/Warhead@parts")
        self.assertEqual(edge["abundant_target_credit"], .75)
        self.assertEqual(edge["no_target_credit"], 0.0)
        self.assertEqual(edge["target_mask_status"], "MATCH")
        self.assertEqual(edge["expected_amount"], 3.0)

    def test_custom_mask_stays_review_required(self):
        parent = node("parent", children=[node("ValidTargets", "Ground, Infantry")])
        emitter = node("Warhead@parts", "FireShrapnel", [node("Weapon", "fragment")])
        fragment = node("fragment", children=[node("ValidTargets", "Ground, Infantry")])
        edge = report._edge_record("parent", parent, emitter, fragment, "path")
        self.assertEqual(edge["target_mask_status"], "CUSTOM_TAG_REVIEW")

    def test_safe_invalid_values_fail_closed(self):
        parent = node("parent")
        emitter = node("Warhead@parts", "FireShrapnel", [
            node("Weapon", "fragment"), node("Amount", "bad"),
            node("AimChance", "bad"), node("ThrowWithoutTarget", "bad"),
        ])
        fragment = node("fragment")
        edge = report._edge_record("parent", parent, emitter, fragment, "path")
        self.assertIsNone(edge["expected_amount"])
        self.assertIsNone(edge["aim_chance"])
        self.assertIsNone(edge["abundant_target_credit"])
        self.assertIsNone(edge["throw_without_target"])
        self.assertIsNone(edge["no_target_credit"])


if __name__ == "__main__":
    unittest.main()
