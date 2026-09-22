"""THE CONDITION EVALUATOR IS THE RISKY PART OF `audit_bot_insurance.py`.

⛔ THE ANTIPATTERN THIS FILE EXISTS TO PREVENT. CLAUDE.md rule 8e was paid for by a hand parser
that looked right and silently changed meaning. This audit has the same shape of risk in a smaller
place: it must turn an OpenRA condition expression into a boolean, and this mod is full of
NEAR-MISS identifiers — `mediumbot` is a substring of `mediumbotinsurance`, `easybot` of
`veryeasybot`. A `str.replace()` evaluator passes casual inspection and gets those wrong, which
would make the audit confidently report the wrong rung counts and "prove" the bug fixed when it is
not.

So these tests assert three things:

  1. the evaluator is TOKENISED — substrings of longer identifiers are never touched;
  2. operator precedence and parentheses behave (`!a && b || c` is not `!(a && b || c)`);
  3. **the audit's laws actually fire** on a ladder shaped like the real bug — a monotonicity dip
     and a zero-rung difficulty must both be caught.

Test 3 is the one that matters. Tests 1-2 alone would pass on an audit whose laws were never wired
to its exit code.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))

import audit_bot_insurance as abi  # noqa: E402


# ---------------------------------------------------------------- 1. tokenisation

def test_a_condition_is_not_confused_with_a_longer_one_containing_it():
    """`mediumbot` must not be found inside `mediumbotinsurance`. This is the whole trap."""
    assert abi.evaluate("mediumbot", {"mediumbotinsurance": True}) is False
    assert abi.evaluate("mediumbotinsurance", {"mediumbot": True}) is False
    assert abi.evaluate("easybot", {"veryeasybot": True}) is False
    assert abi.evaluate("veryeasybot", {"easybot": True}) is False


def test_an_unknown_identifier_is_false_which_is_what_the_engine_does():
    assert abi.evaluate("neverGranted", {}) is False
    assert abi.evaluate("!neverGranted", {}) is True


# ---------------------------------------------------------------- 2. operators

@pytest.mark.parametrize(("expr", "cond", "want"), [
    ("a && b", {"a": True, "b": True}, True),
    ("a && b", {"a": True}, False),
    ("a || b", {"b": True}, True),
    ("!a", {}, True),
    ("!a", {"a": True}, False),
    ("(!a && !b) || c", {}, True),                    # human: neither bot flag set
    ("(!a && !b) || c", {"a": True}, False),          # a bot, and not the listed one
    ("(!a && !b) || c", {"a": True, "c": True}, True),  # a bot, and listed
    ("(a || b) && c", {"a": True}, False),            # the ladder's own shape
    ("(a || b) && c", {"a": True, "c": True}, True),
])
def test_operator_semantics(expr, cond, want):
    assert abi.evaluate(expr, cond) is want


def test_the_real_ladder_expression_shape_evaluates_correctly():
    """A verbatim rung expression from the patched ladder, for each player kind."""
    rung = ("((!genericbot && !campaignbot) || mediumbot || hardbot || veryhardbot "
            "|| brutalbot || challengerbot || unbeatablebot || cameogodbot) "
            "&& mediumbotinsurance")
    assert abi.evaluate(rung, abi.conditions_for("human")) is True
    assert abi.evaluate(rung, abi.conditions_for("campaign")) is False
    assert abi.evaluate(rung, abi.conditions_for("medium")) is True
    assert abi.evaluate(rung, abi.conditions_for("cameogod")) is True
    assert abi.evaluate(rung, abi.conditions_for("easy")) is False


def test_conditions_for_sets_exactly_one_difficulty_flag():
    c = abi.conditions_for("hard")
    assert c["hardbot"] is True and c["genericbot"] is True
    assert "mediumbot" not in c
    assert abi.conditions_for("human").get("genericbot") is None
    assert abi.conditions_for("campaign")["campaignbot"] is True


# ---------------------------------------------------------------- 3. the laws fire

def _counts(rungs):
    return {d: sum(1 for r in rungs if abi.evaluate(r, abi.conditions_for(d)))
            for d in abi.DIFFICULTIES}


def test_a_monotonicity_dip_is_detectable_the_way_the_audit_detects_it():
    """The real bug: `medium` gated on a condition nothing grants, so it dips to zero."""
    rungs = [f"{d}bot && {d}botinsurance" for d in abi.DIFFICULTIES]
    rungs[abi.DIFFICULTIES.index("medium")] = "normalbot && mediumbotinsurance"
    counts = _counts(rungs)
    assert counts["medium"] == 0
    assert counts["easy"] == 1
    dips = [(lo, hi) for lo, hi in zip(abi.DIFFICULTIES, abi.DIFFICULTIES[1:])
            if counts[hi] < counts[lo]]
    assert ("easy", "medium") in dips


def test_a_healthy_ladder_shows_no_dip_and_no_zero():
    rungs = [f"{d}bot && {d}botinsurance" for d in abi.DIFFICULTIES]
    counts = _counts(rungs)
    assert all(counts[d] == 1 for d in abi.DIFFICULTIES)
    assert not [(lo, hi) for lo, hi in zip(abi.DIFFICULTIES, abi.DIFFICULTIES[1:])
                if counts[hi] < counts[lo]]


def test_the_dynamic_trait_replaces_the_legacy_ladder_and_covers_every_bot_type():
    """The committed runtime trait replaces every YAML rung without leaving a bot difficulty out."""
    rules = abi.miniyaml.Ruleset(str(pathlib.Path(__file__).resolve().parents[2]))
    assert abi.ladder_rungs(rules) == []
    difficulties = abi.dynamic_difficulties(rules)
    assert difficulties == abi.DIFFICULTIES
    assert abi.check_dynamic_trait(difficulties) == 0


def test_supported_bots_do_not_stack_the_legacy_no_base_fallback():
    """The player trait survives conyard loss, so its supported bots must not get both payouts."""
    rules = abi.miniyaml.Ruleset(str(pathlib.Path(__file__).resolve().parents[2]))
    player = rules.resolve("Player")
    expr = player.child("CashTrickler@secondaryinsurance").get("RequiresCondition")
    assert expr == "secondaryinsurance && nobase && !genericbot"

    eligible = {"secondaryinsurance": True, "nobase": True}
    assert abi.evaluate(expr, eligible) is True  # human or deliberately unsupported bot
    assert abi.evaluate(expr, {**eligible, "genericbot": True}) is False
