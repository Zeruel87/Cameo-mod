"""Regression contracts for the rule-driven heavy-explosive tranche."""

from __future__ import annotations

import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/rule_driven_heavy_explosives_manifest.json"
sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]

from audit_three_way_split import main_warhead_nodes, main_warheads  # noqa: E402
import consolidate_rule_driven_heavy_explosives as cohort  # noqa: E402
from miniyaml import Ruleset  # noqa: E402


EXPECTED_CHANGED = {
    "8Inch",
    "Short8Inch",
    "TSGrenade",
    "TSGrenadeAA",
    "TSGrenadeG",
}
EXPECTED_TOTALS = {
    "8Inch": 80000,
    "TSGrenade": 24000,
}


class RuleDrivenHeavyExplosivesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Ruleset(ROOT)
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_converter_is_fully_applied_with_pinned_totals(self):
        cohort.validate_result()
        self.assertEqual(EXPECTED_TOTALS, {
            name: int(main_warhead_nodes(self.rules.resolve_weapon(name))[0].get("Damage"))
            for name in sorted(cohort.SELECTED)
        })

    def test_whole_ruleset_change_scope_is_exact(self):
        self.assertEqual([], self.report["added"])
        self.assertEqual([], self.report["removed"])
        self.assertEqual(EXPECTED_CHANGED, set(self.report["changed"]))
        kinds = {
            kind
            for changes in self.report["changed"].values()
            for kind in changes
        }
        self.assertEqual(
            {"armor_profile", "blast_shape", "percentage_damage"},
            kinds,
        )

    def test_comparison_fingerprints_and_rounding_are_pinned(self):
        self.assertEqual(
            "024542f515f8538356dac921f99849c562339d311c8e1af3b07b2f59c851e93c",
            self.report["source_digest"],
        )
        self.assertEqual({
            "armor_profile": "bde982d5285d60e52510db153e613a14050a66084f773a0d494a485878b45b0b",
            "blast_shape": "4f8b0919785c36f227896d6e07d746de9a1f8f978b3fe8149394a2def747e0ba",
            "percentage_damage": "e207ad94113c0f4692b5b282aabd86194fcc0d992c6e68d9ee686e82e2d9aff2",
        }, self.report["change_kind_digests"])
        self.assertEqual(1, self.report["percentage_rounding"]["max_absolute_delta"])


if __name__ == "__main__":
    unittest.main()
