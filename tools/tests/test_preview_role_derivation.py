"""Unit tests for tools/ai/derive_roles_preview.py — the pure functions only.

The full-ruleset preview needs a complete tree (engine/ sources for the
trait table), so the ruleset-level mirror is exercised by hand; these tests
lock the no-variables condition evaluator, the FieldPredicate grammar, the
`any`/`only` match semantics and the C#-default tokenizer — the pieces a
typo or operator bug can silently turn into an empty role set.
"""

from __future__ import annotations

import pathlib
import sys
import unittest

import _bootstrap  # noqa: F401 — tools/audit on sys.path

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/ai"))

import derive_roles_preview as pr


class EvalNoVariablesTest(unittest.TestCase):
    """Mirrors BooleanExpression.Evaluate(VariableExpression.NoVariables):
    every identifier is false, so the expression collapses to a literal."""

    def test_bare_and_negated_tokens(self):
        self.assertFalse(pr.eval_no_variables("deployed"))
        self.assertTrue(pr.eval_no_variables("!deployed"))

    def test_hyphenated_token_names(self):
        # Real conditions use hyphenated tokens (e.g. `!upgrade-token`).
        self.assertTrue(pr.eval_no_variables("!upgrade-token"))
        self.assertFalse(pr.eval_no_variables("upgrade-token && !other-token"))

    def test_conjunction_and_disjunction(self):
        self.assertFalse(pr.eval_no_variables("a && b"))
        self.assertFalse(pr.eval_no_variables("a || b"))
        self.assertTrue(pr.eval_no_variables("!a && !b"))
        self.assertTrue(pr.eval_no_variables("!a || !b"))
        self.assertTrue(pr.eval_no_variables("a || !b"))
        self.assertFalse(pr.eval_no_variables("a && !b"))
        self.assertFalse(pr.eval_no_variables("enabled && !disabled"))

    def test_parens(self):
        self.assertTrue(pr.eval_no_variables("!(a && b)"))
        self.assertTrue(pr.eval_no_variables("!(a || b)"))
        self.assertFalse(pr.eval_no_variables("(a || b) && !c"))

    def test_equality(self):
        self.assertFalse(pr.eval_no_variables("a == true"))
        self.assertTrue(pr.eval_no_variables("!a == true"))
        self.assertTrue(pr.eval_no_variables("a != true"))
        self.assertTrue(pr.eval_no_variables("a == false"))

    def test_literals(self):
        self.assertTrue(pr.eval_no_variables("true"))
        self.assertFalse(pr.eval_no_variables("false"))
        self.assertTrue(pr.eval_no_variables("1"))
        self.assertFalse(pr.eval_no_variables("0"))

    def test_right_operand_always_parsed(self):
        # Short-circuiting must not leave tokens unconsumed — a stale position
        # once made these return None instead of a bool.
        self.assertFalse(pr.eval_no_variables("a && b && c"))
        self.assertTrue(pr.eval_no_variables("!a || !b || !c"))

    def test_relational_is_decidable(self):
        # Every identifier is 0 under NoVariables, so relations collapse too.
        self.assertFalse(pr.eval_no_variables("charge > 1"))
        self.assertTrue(pr.eval_no_variables("charge < 1"))
        self.assertTrue(pr.eval_no_variables("charge <= 0"))
        self.assertTrue(pr.eval_no_variables("charge >= 0"))
        self.assertFalse(pr.eval_no_variables("charge > 1 && !b"))
        self.assertTrue(pr.eval_no_variables("charge == 0"))

    def test_long_nested_condition(self):
        # The teslacoil armaments' shape — deep parens, && || == > — must not
        # blow up the lexer and must evaluate, not return None.
        # ((1&&1)||(0&&0)) && ((0&&1)||(1&&0)) = 1 && 0 = false
        expr = ("((!charge && !unpowered) || (charge == 1 && unpowered)) && "
                "((upg && !rank-elite) || (!upg && rank-elite))")
        self.assertFalse(pr.eval_no_variables(expr))
        expr2 = ("((charge && !unpowered) || (charge > 1 && unpowered)) && "
                 "(upg && rank-elite)")
        self.assertFalse(pr.eval_no_variables(expr2))

    def test_undecidable_operators(self):
        self.assertIsNone(pr.eval_no_variables("~a"))
        self.assertIsNone(pr.eval_no_variables("a & b"))
        self.assertIsNone(pr.eval_no_variables("a | b"))
        self.assertIsNone(pr.eval_no_variables("a + b > 2"))
        self.assertIsNone(pr.eval_no_variables("unbalanced ( a"))

    def test_empty(self):
        self.assertIsNone(pr.eval_no_variables(""))
        self.assertIsNone(pr.eval_no_variables("   "))


class ParsePredicatesTest(unittest.TestCase):
    def test_any(self):
        self.assertEqual(
            pr.parse_predicates("Weapons.ValidTargets any Air|Aircraft"),
            ("Weapons", "ValidTargets", False, {"Air", "Aircraft"}))

    def test_only(self):
        self.assertEqual(
            pr.parse_predicates("Building.TerrainTypes only Water"),
            ("Building", "TerrainTypes", True, {"Water"}))

    def test_dotted_trait_name_splits_on_last_dot(self):
        self.assertEqual(
            pr.parse_predicates("Aircraft.CanHover any True"),
            ("Aircraft", "CanHover", False, {"True"}))

    def test_rejects_malformed(self):
        for bad in ("Weapons.ValidTargets Air", "Field any", "a.b c d e",
                    "a.b some x", "any x", ""):
            with self.assertRaises(ValueError, msg=bad):
                pr.parse_predicates(bad)


class PredicateMatchTest(unittest.TestCase):
    def test_any_and_only(self):
        self.assertTrue(pr.predicate_match({"air", "ground"}, False, {"air"}))
        self.assertFalse(pr.predicate_match({"ground"}, False, {"air"}))
        self.assertTrue(pr.predicate_match({"water"}, True, {"water"}))
        self.assertFalse(pr.predicate_match({"water", "land"}, True, {"water"}))

    def test_case_insensitive(self):
        self.assertTrue(pr.predicate_match({"Naval"}, False, {"naval"}))
        self.assertTrue(pr.predicate_match({"True"}, False, {"true"}))

    def test_empty_values_never_match(self):
        self.assertFalse(pr.predicate_match(set(), False, {"air"}))
        self.assertFalse(pr.predicate_match(set(), True, {"water"}))


class DefaultTokensTest(unittest.TestCase):
    def test_implicit_defaults(self):
        self.assertEqual(pr.default_tokens("bool", None), {"False"})
        self.assertEqual(pr.default_tokens("int", None), {"0"})
        self.assertEqual(pr.default_tokens("string", None), set())
        self.assertEqual(pr.default_tokens("FrozenSet<string>", None), set())

    def test_explicit_initializers(self):
        self.assertEqual(pr.default_tokens("bool", "true"), {"True"})
        self.assertEqual(pr.default_tokens("bool", "false"), {"False"})
        self.assertEqual(pr.default_tokens("int", "42"), {"42"})
        self.assertEqual(pr.default_tokens("string", '"naval"'), {"naval"})

    def test_non_literal_initializers(self):
        self.assertEqual(pr.default_tokens("FrozenSet<string>", "FrozenSet<string>.Empty"), set())
        self.assertEqual(pr.default_tokens("object", "new object()"), set())
        self.assertEqual(pr.default_tokens("int", "default"), set())


class ExpandTypeNamesTest(unittest.TestCase):
    PARENTS = {
        "AttackAircraftInfo": "AttackFollowInfo",
        "AttackFollowInfo": "AttackBaseInfo",
        "AttackBaseInfo": "ConditionalTraitInfo",
        "MobileInfo": "ConditionalTraitInfo",
        "D2kMobileInfo": "MobileInfo",
    }

    def test_walks_to_traitinfo_root(self):
        self.assertEqual(
            pr.expand_type_names("AttackAircraft", self.PARENTS),
            {"AttackAircraft", "AttackFollow", "AttackBase"})

    def test_mid_chain_entry(self):
        self.assertEqual(
            pr.expand_type_names("D2kMobile", self.PARENTS),
            {"D2kMobile", "Mobile"})

    def test_unknown_trait_yields_itself(self):
        self.assertEqual(pr.expand_type_names("Lonesome", {}), {"Lonesome"})


if __name__ == "__main__":
    unittest.main()
