"""Focused checks for promotion discount candidate arithmetic."""
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import prepare_promotion_discount as proposal  # noqa: E402
import formula  # noqa: E402
import tier_chain  # noqa: E402


class Trait:
    def __init__(self, key, modifier):
        self.key = key
        self._modifier = modifier
        self.file = "defaults.yaml"
        self.line = 1

    def get(self, name):
        return self._modifier if name == "Modifier" else None


class Rules:
    def resolve(self, name):
        self.name = name
        return type("Resolved", (), {
            "children": [
                Trait("ReloadDelayMultiplier@PromotionUnit", "90"),
                Trait("SpeedMultiplier@PromotionUnit", "105"),
                Trait("RangeMultiplier@PromotionUnit", "105"),
                Trait("InaccuracyMultiplier@PromotionUnit", "90"),
            ],
            "file": "defaults.yaml",
            "line": 1,
        })()


class Model:
    rs = Rules()


def candidate(relative, plateau=False):
    return {
        "virtual_cost": 1000.0,
        "projected_multiplier": 1.0 - relative,
        "absolute_discount": relative,
        "relative_discount": relative,
        "no_change_due_to_plateau": plateau,
    }


class PromotionDiscountTests(unittest.TestCase):
    def test_summary_groups_by_promotion_tier(self):
        rows = [
            {"promotion_tier": 1, "candidates": {"per_tier_1500": candidate(0.1)}},
            {"promotion_tier": 1, "candidates": {"per_tier_1500": candidate(0.0, True)}},
            {"promotion_tier": 2, "candidates": {"per_tier_1500": candidate(0.3)}},
        ]
        result = proposal._summary(rows, "per_tier_1500")
        self.assertEqual(result["rows"], 3)
        self.assertAlmostEqual(result["relative_discount"]["mean"], 0.1333333333)
        self.assertEqual(result["by_promotion_tier"]["1"]["plateau_no_change"], 1)
        self.assertAlmostEqual(result["by_promotion_tier"]["2"]["median"], 0.3)

    def test_candidate_values_scale_only_with_authored_promotion_tier(self):
        self.assertEqual(proposal.POLICY_VALUES["per_tier_1000"](1), 1000.0)
        self.assertEqual(proposal.POLICY_VALUES["per_tier_1500"](3), 4500.0)
        self.assertEqual(proposal.POLICY_VALUES["per_tier_2000"](4), 8000.0)
        self.assertEqual(proposal.POLICY_VALUES["fixed_5000"](4), 5000.0)

    def test_buff_context_uses_only_resolved_active_traits(self):
        profile = proposal._promotion_buff_profile(Model())
        traits = {row["base_trait"] for row in profile["active_traits"]}
        self.assertNotIn("FirepowerMultiplier", traits)
        self.assertEqual(profile["formula_axes"]["speed"], 1.05)
        self.assertEqual(profile["formula_axes"]["range"], 1.05)
        self.assertAlmostEqual(profile["formula_axes"]["dps"], 1 / 0.9)
        impact = proposal._formula_buff_impact(profile, formula.class_baseline_price)
        self.assertEqual(impact["status"], "RESOLVED")
        self.assertLess(impact["equivalent_discount"], 0.165)

    def test_pricing_chain_adds_one_virtual_cost_without_changing_actual_cost(self):
        context = tier_chain.promotion_price_context(
            10000, ["promotion-tier-2"], {"promotion-tier-2": 2})
        self.assertEqual(context["chain_cost"], 10000)
        self.assertEqual(context["virtual_promotion_cost"], 3000)
        self.assertEqual(context["pricing_chain_cost"], 13000)
        self.assertEqual(context["promotion_tier"], 2)

    def test_pricing_chain_fails_closed_on_multiple_promotion_tokens(self):
        context = tier_chain.promotion_price_context(
            10000, ["p1", "p2"], {"p1": 1, "p2": 2})
        self.assertEqual(context["status"], "UNRESOLVED")
        self.assertIsNone(context["pricing_chain_cost"])

    def test_unknown_promotion_is_not_treated_as_no_promotion(self):
        for tokens in (["td_gdi_promotion_missing"],
                       ["known", "td_gdi_promotion_missing"]):
            result = tier_chain.promotion_price_context(10000, tokens, {"known": 1})
            self.assertEqual(result["status"], "UNRESOLVED")
            self.assertIsNone(result["pricing_chain_cost"])

    def test_cycles_and_missing_parents_invalidate_their_descendants_only(self):
        depths = tier_chain.resolve_promotion_depths({
            "a": ["b"], "b": ["a"], "child": ["a"],
            "missing": ["td_gdi_promotion_unknown"],
            "base": ["barracks"], "next": ["base"],
        })
        self.assertEqual(depths, {
            "a": None, "b": None, "child": None, "missing": None,
            "base": 1, "next": 2,
        })
        result = tier_chain.promotion_price_context(10000, ["child"], depths)
        self.assertIsNone(result["pricing_chain_cost"])

    def test_invalid_numeric_inputs_never_return_a_resolved_price(self):
        for actual, rate, depth in ((float('nan'), 1500, 1),
                                    (10000, float('inf'), 1),
                                    (-1, 1500, 1), (10000, -1500, 1),
                                    (10000, 1500, 0), (10000, 1500, 1.5),
                                    (True, 1500, 1)):
            with self.subTest(actual=actual, rate=rate, depth=depth):
                result = tier_chain.promotion_price_context(
                    actual, ["promotion"], {"promotion": depth}, rate)
                self.assertEqual(result["status"], "UNRESOLVED")
                self.assertIsNone(result["pricing_chain_cost"])


if __name__ == "__main__":
    unittest.main()
