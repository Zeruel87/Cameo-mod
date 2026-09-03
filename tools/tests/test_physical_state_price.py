"""Unit tests for E2 physical-state pricing (tools/balance/physical_state_price.py).

⛔ THE BUG THESE EXIST TO PREVENT, because it shipped twice and reached a maintainer ruling:

`PhysicalState.ApplyChange` health-scales through `ScaleChangeToHealth`

    (long)amount * range / health.MaxHP        where  range = MaxValue - MinValue

but `PhysicalStateInfo.RelativeToHealth`'s own [Desc] says *"divided by HP/10000"*. Trusting
that stale Desc produced a fill-race formula 2-4x too pessimistic, which produced the finding
"only 1 of 367 weapons ever reaches full effect", which produced the request for a bigger
constant, which the maintainer answered with 300. The arithmetic was wrong at every step and
nothing in the tree disagreed with it, because nothing in the tree computed it twice.

So T1/T2 below assert the divisor is the RESOLVED range, per meter, and T3 asserts the
property that makes the whole model tractable: the target's HP and the weapon's damage BOTH
cancel out of the damage-scaled form.

The rest pin the delivery model against the maintainer's ruling (2026-08-18): the 1.25x is
CONDITIONAL on delivery — *"IF it is able to completely freeze a unit BEFORE it dies"* — and
`PHYSICAL_STATE_SYSTEM.md` sharpens it to *"price a partial meter partially"*.
"""

from __future__ import annotations

import pathlib
import sys
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import formula  # noqa: E402
import physical_state_price as psp  # noqa: E402
from cameo_model import Model  # noqa: E402


_MODEL = None


def model():
    global _MODEL
    if _MODEL is None:
        _MODEL = Model()
    return _MODEL


class MeterGeometry(unittest.TestCase):
    """T1/T2 — the divisor is the meter's own range, measured, never a constant."""

    def setUp(self):
        self.geom = psp.meter_geometry(model().rs)

    def test_t1_temperature_is_signed_so_its_range_is_double(self):
        t = self.geom["Temperature"]
        self.assertEqual(t["min"], -20000)
        self.assertEqual(t["max"], 20000)
        self.assertEqual(t["range"], 40000, "Temperature is signed: range is 40000, not 20000")
        self.assertTrue(t["relative"], "the race only cancels HP while RelativeToHealth holds")

    def test_t1b_corrosion_is_symmetric_with_temperature(self):
        # Maintainer 2026-08-18: *"Temperature has negative values while corrosion doesn't. The
        # absolute maximum and minimum values are the same! cryo = -20k heat = 20k and
        # corrosion 20k"* — the meters are ONE shape by design. Corrosion shipped with
        # `MinValue: 0`, giving it half Temperature's `range`, and since the engine divides by
        # `range` the same Scale filled heat TWICE as fast. Fixed by making Corrosion signed.
        c, t = self.geom["Corrosion"], self.geom["Temperature"]
        self.assertEqual(c["range"], t["range"],
                         "the meters must share a range or one Scale means two things")
        self.assertEqual((c["min"], c["max"]), (-20000, 20000))

    def test_t2_ratio_uses_range_not_ten_thousand(self):
        # 50/Scale on BOTH meters. The old formula said 200/Scale — 4x too pessimistic — because
        # it trusted `RelativeToHealth`'s [Desc] ("divided by HP/10000") over the code.
        temp = psp.fill_ratio("scaled", 300, 0, self.geom["Temperature"])
        corr = psp.fill_ratio("scaled", 300, 0, self.geom["Corrosion"])
        self.assertAlmostEqual(temp, 50 / 300, places=9)
        self.assertAlmostEqual(corr, 50 / 300, places=9)
        self.assertAlmostEqual(corr, temp, places=9,
                               msg="one Scale must mean one fill rate on every meter")

    def test_t2b_the_original_scale_already_cleared_the_bar(self):
        # The 100 -> 300 change (354ed5ad3) was made to fix a shortfall that did not exist:
        # Scale 100 gives 0.50, comfortably inside the 0.75 bar, on both meters. (It did NOT
        # for Corrosion before the symmetry fix — that was the 1.00 that made the change look
        # necessary, and it was an artifact of the unsigned MinValue.)
        for meter in ("Temperature", "Corrosion"):
            self.assertLess(psp.fill_ratio("scaled", 100, 0, self.geom[meter]),
                            psp.FULL_EFFECT_BAR, meter)

    def test_t3_hp_and_damage_cancel_in_the_scaled_form(self):
        g = self.geom["Temperature"]
        ratios = {psp.fill_ratio("scaled", 150, dmg, g) for dmg in (1, 5000, 750000)}
        self.assertEqual(len(ratios), 1, "damage must cancel: the race is the constant alone")

    def test_t3b_damage_does_not_cancel_for_a_discrete_amount(self):
        # This is why the 166 discrete weapons fail: their Amount is a flat number set once,
        # so a big gun outruns its own meter.
        g = self.geom["Temperature"]
        weak = psp.fill_ratio("apply", 1200, 10000, g)
        strong = psp.fill_ratio("apply", 1200, 750000, g)
        self.assertLess(weak, strong)
        self.assertGreater(strong, 1.0, "a heavy discrete weapon kills long before it fills")


class EffectCurves(unittest.TestCase):
    """The consumer traits, not an assumption, decide what a partial meter is worth."""

    def setUp(self):
        rs = model().rs
        self.heat, _ = psp.effect_curve(rs, "^CryoFreezable", "Temperature", True)
        self.cryo, _ = psp.effect_curve(rs, "^CryoFreezable", "Temperature", False)
        self.corr, _ = psp.effect_curve(rs, "^Corrodible", "Corrosion", True)

    def test_t4_every_curve_is_full_at_a_full_meter(self):
        for name, curve in (("heat", self.heat), ("cryo", self.cryo), ("corr", self.corr)):
            self.assertAlmostEqual(curve(1.0), 1.0, places=6, msg=name)

    def test_t5_every_axis_opens_at_the_same_1_percent_deadzone(self):
        # `Corroding` shipped gated at LowerValue 10000 — HALF the meter — while `Overheating`
        # opened at 200. Maintainer 2026-08-18: *"then corrosion should also start at 1%
        # right?"* Yes. A gate difference of 50x between two axes of the same system is a
        # defect, and it made a corrosion weapon that 49%-filled deliver literally nothing.
        for name, curve in (("heat", self.heat), ("cryo", self.cryo), ("corr", self.corr)):
            self.assertEqual(curve(0.005), 0.0, f"{name} must respect the deadzone")
            self.assertGreater(curve(0.02), 0.0, f"{name} must open just past it")

    def test_t6_no_axis_opens_at_half_strength(self):
        # `ChangesHealthProportionalToPhysicalState` normalises over the FULL signed range and
        # has no `UseDeviationFromRelaxed` option, so a DoT written `DamageAtMinimum: 0` on a
        # signed meter opens at HALF its maximum the instant its condition is granted.
        # `DamageAtMinimum: -DamageAtMaximum` puts the zero back at a relaxed meter.
        for name, curve in (("heat", self.heat), ("corr", self.corr)):
            self.assertLess(curve(0.02), 0.1, f"{name} DoT still has a floor")

    def test_t7_every_axis_is_honestly_proportional(self):
        # All three now interpolate linearly in fill, which is the maintainer's mental model
        # ("completely freeze") and makes one Scale mean one thing across the whole system.
        for name, curve in (("heat", self.heat), ("cryo", self.cryo), ("corr", self.corr)):
            for x in (0.25, 0.5, 0.75):
                self.assertAlmostEqual(curve(x), x, places=6, msg=f"{name} at {x}")


class Pricing(unittest.TestCase):
    """The ruling: 1.25x at full delivery, proportionally less below it, never more."""

    def setUp(self):
        rs = model().rs
        self.geom = psp.meter_geometry(rs)
        self.exp = psp.exposure(rs)
        self.cryo, _ = psp.effect_curve(rs, "^CryoFreezable", "Temperature", False)
        self.corr, _ = psp.effect_curve(rs, "^Corrodible", "Corrosion", True)
        self.reference = psp.delivery(psp.FULL_EFFECT_BAR, self.cryo)

    def test_t8_a_weapon_meeting_the_bar_pays_exactly_the_ruling(self):
        w = psp.delivery_weight(psp.FULL_EFFECT_BAR, self.cryo, 1.0, self.reference)
        self.assertAlmostEqual(w, 1.0, places=6)
        self.assertAlmostEqual(formula.physical_state_price_multiplier(w), 1.25, places=6)

    def test_t9_filling_faster_than_the_bar_is_never_charged_more(self):
        for ratio in (0.5, 0.167, 0.01):
            w = psp.delivery_weight(ratio, self.cryo, 1.0, self.reference)
            self.assertLessEqual(formula.physical_state_price_multiplier(w), 1.25 + 1e-9)

    def test_t10_delivering_nothing_costs_nothing(self):
        w = psp.delivery_weight(400.0, self.corr, self.exp["Corrosion"], self.reference)
        self.assertAlmostEqual(formula.physical_state_price_multiplier(w), 1.0, places=3)

    def test_t11_exposure_holds_corrosion_below_the_ceiling(self):
        # Corrosion sits on 45% of priced actors, so even a corrosion weapon that fills its
        # meter three times over cannot earn a flame weapon's surcharge. Nothing in the price
        # model saw this term before 2026-08-18.
        ratio = psp.fill_ratio("scaled", 300, 0, self.geom["Corrosion"])
        w = psp.delivery_weight(ratio, self.corr, self.exp["Corrosion"], self.reference)
        mult = formula.physical_state_price_multiplier(w)
        self.assertGreater(mult, 1.0)
        self.assertLess(mult, 1.25)

    def test_t12_multiplier_is_monotone_in_the_weight(self):
        prev = 0.0
        for w in (0.0, 0.1, 0.4, 0.7, 1.0):
            cur = formula.physical_state_price_multiplier(w)
            self.assertGreaterEqual(cur, prev)
            prev = cur
        self.assertEqual(formula.physical_state_price_multiplier(0.0), 1.0)


class Scan(unittest.TestCase):
    """The census must see all three binding shapes, or E2 undercounts itself again."""

    def test_t13_all_three_binding_shapes_are_counted(self):
        rows, _ref, _geom, _exp, _curves = psp.scan(model().rs)
        kinds = {r["kind"] for r in rows}
        self.assertEqual(kinds, {"scaled", "apply"})
        self.assertGreaterEqual(len({r["weapon"] for r in rows}), 370,
                                "counting one shape gave 89, two gave 367, three give 372")

    def test_t14_a_blend_with_no_PhysicalStateName_is_still_found(self):
        # `^Warhead_Plasma_*` carries a `PhysicalStates:` dict and NO PhysicalStateName; keying
        # on the name is what hid every blend family from the first two E2 censuses.
        rs = model().rs
        _dmg, bindings = psp.weapon_bindings(rs, "^Warhead_Plasma_Heavy")
        self.assertTrue(bindings, "blend PhysicalStates dict was not picked up")


class FedDamageShare(unittest.TestCase):
    """W24. The term that made every earlier delivery number wrong.

    The maintainer found it by PLAYTEST, not by any guard in this tree: a Chemical Stealth
    Tank kills a harvester but never fills its corrosion bar, because the weapon fires three
    main warheads and only one carries the meter. Nothing here checked whether the damage
    FEEDING the meter is the damage doing the KILLING — doc_claims counts bindings, T1-T3 pin
    arithmetic, the boot gate proves it loads. So these pin the term itself.
    """

    def test_t15_ratio_scales_inversely_with_fed_share(self):
        geom = {"max": 20000, "min": -20000, "range": 40000}
        full = psp.fill_ratio("scaled", 100, 9000, geom, fed_share=1.0)
        third = psp.fill_ratio("scaled", 100, 9000, geom, fed_share=1 / 3)
        self.assertAlmostEqual(full, 0.5, places=6)
        self.assertAlmostEqual(third, 1.5, places=6,
                               msg="one of three mains feeding = 3x the hits to fill")
        self.assertAlmostEqual(third, full * 3, places=6)

    def test_t15b_a_weapon_whose_meter_warhead_deals_no_damage_cannot_fill(self):
        geom = {"max": 20000, "min": -20000, "range": 40000}
        self.assertIsNone(psp.fill_ratio("scaled", 100, 9000, geom, fed_share=0.0))

    def test_t16_apply_is_exempt_because_a_flat_Amount_lands_per_hit(self):
        # A discrete ApplyPhysicalState warhead does not read damage at all, so splitting the
        # damage across mains cannot dilute it. Pricing it down would be a second error.
        geom = {"max": 20000, "min": -20000, "range": 40000}
        a = psp.fill_ratio("apply", 4000, 9000, geom, fed_share=1.0)
        b = psp.fill_ratio("apply", 4000, 9000, geom, fed_share=0.25)
        self.assertEqual(a, b)

    def test_t17_damage_split_matches_weapon_bindings_exclusions(self):
        # Friendly-fire twins and Percentage warheads must be excluded on BOTH sides or the
        # share is computed against a denominator the binding census never saw.
        rs = model().rs
        total, fed = psp.damage_split(rs, "ChemRockets")
        self.assertGreater(total, 0)
        self.assertGreater(total, fed, "this weapon is the reported multi-main case")
        self.assertLess(fed / total, 0.75)

    def test_t18_the_single_warhead_cancellation_still_holds_where_it_applies(self):
        # T3 asserts HP and damage cancel. That is TRUE — but only at fed_share == 1.0, which
        # is what the old signature silently assumed for every weapon.
        geom = {"max": 20000, "min": -20000, "range": 40000}
        for damage in (2000, 9000, 40000):
            self.assertAlmostEqual(
                psp.fill_ratio("scaled", 100, damage, geom, fed_share=1.0), 0.5, places=6)


if __name__ == "__main__":
    unittest.main()
