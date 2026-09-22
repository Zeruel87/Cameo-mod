"""Focused pure checks for promotion upgrade interaction classification."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import prepare_promotion_upgrade_interactions as audit  # noqa: E402


class Node:
    def __init__(self, key, **values):
        self.key = key
        self.values = values
        self.file = "fixture.yaml"
        self.line = 1

    def get(self, name):
        return self.values.get(name)


class PromotionUpgradeInteractionTests(unittest.TestCase):
    def test_token_kind_separates_faction_and_promotion_hooks(self):
        self.assertEqual(audit.token_kind("~td_gdi_promotion_sniper", "td_gdi"), "promotion")
        self.assertEqual(audit.token_kind("td_gdi_upgrade_cuttingedgeequipment", "td_gdi"), "upgrade_or_doctrine")
        self.assertEqual(audit.token_kind("ra1_soviets_upgrade_heavyarmor", "td_gdi"), "other_faction_upgrade_or_doctrine")
        self.assertEqual(audit.token_kind("rank1", "td_gdi"), "other")

    def test_normalize_token_strips_openra_prefixes(self):
        self.assertEqual(audit.normalize_token("~!td_gdi_promotion_sniper"), "td_gdi_promotion_sniper")

    def test_numeric_literals_are_not_condition_identifiers(self):
        self.assertEqual(
            audit.condition_identifiers("ammo >= 2 && !rank-elite"),
            ["ammo", "rank-elite"],
        )

    def test_different_case_is_not_silently_the_same_condition(self):
        resolved = type("Resolved", (), {"children": [
            Node("ExternalCondition@test", Condition="Cloaked"),
            Node("DamageMultiplier@test", Modifier="90",
                 RequiresCondition="Cloaked && cloaked"),
        ]})()
        _, stats = audit._condition_inventory(resolved, "td_gdi")
        self.assertEqual(stats[0]["unresolved_condition_identifiers"], ["cloaked"])

    def test_mixed_known_and_unknown_identifiers_remain_individually_visible(self):
        resolved = type("Resolved", (), {"children": [
            Node(
                "GrantConditionOnPrerequisite@upgrade",
                Condition="upgrade-on",
                Prerequisites="td_gdi_upgrade_targeting",
            ),
            Node("ExternalCondition@rank", Condition="rank-veteran"),
            Node(
                "FirepowerMultiplier@test",
                Modifier="110",
                RequiresCondition="upgrade-on && missing-state && rank-veteran >= 1",
            ),
        ]})()
        _, stats = audit._condition_inventory(resolved, "td_gdi")
        stat = stats[0]
        self.assertEqual(stat["condition_identifiers"], [
            "missing-state", "rank-veteran", "upgrade-on",
        ])
        self.assertEqual(stat["unresolved_condition_identifiers"], ["missing-state"])
        self.assertIn("prerequisite_upgrade_or_doctrine", stat["source_kinds"])
        self.assertIn("rank", stat["source_kinds"])
        self.assertIn("unknown", stat["source_kinds"])


if __name__ == "__main__":
    unittest.main()
