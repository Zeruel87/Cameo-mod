"""Unit tests for W15: percentage damage — the twin derivation and its reference HP.

Two maintainer rulings (2026-08-11) are pinned here:

1. The `*Percentage` twin must be CONTINUOUS in Damage. It used to be
   ``per // 2000``, so Damage 1999 produced a twin of 0 — not "a little damage"
   but hard immunity, arrived at purely by rounding. That is harmless only while
   every Damage value sits on the 2000 grid, which is exactly what W17 removes;
   hence this lands first.
2. `reference_hp` is a DESIGN constant of 200 000 — percentage damage is priced as
   if fired at an average baseline actor, not at the roster median (74 000, which
   infantry drag down). The measured figure stays reportable as a diagnostic.

The tests below deliberately assert BEHAVIOUR (monotonicity, no silent zero, the
constant's independence from the roster) rather than a table of magic numbers, so
they keep their meaning when the grid disappears.
"""

from __future__ import annotations

import pathlib
import sys
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import formula  # noqa: E402
import target_model  # noqa: E402


def _wh(tag, dmg, typ="SpreadDamage"):
    return {"tag": tag, "damage": str(dmg), "type": typ}


class PercentageTwinTest(unittest.TestCase):
    """`formula.percentage_twin` — the W15 fix itself."""

    def test_off_grid_damage_never_zeroes_the_twin(self):
        """THE bug. Integer division floored small values to 0 — not "a little
        damage" but hard immunity, in either unit."""
        self.assertEqual(formula.percentage_twin(1), 1)
        self.assertEqual(formula.percentage_twin(1, formula.BASIS_POINT_DENOMINATOR), 1)
        self.assertEqual(formula.percentage_twin(1999), 1)

    def test_twin_keeps_tracking_damage_between_grid_points(self):
        """The old floor gave 2000 and 3500 the SAME twin; the basis-point twin
        separates every single flat step."""
        bp = formula.BASIS_POINT_DENOMINATOR
        self.assertEqual(formula.percentage_twin(2000, bp), 20)
        self.assertEqual(formula.percentage_twin(3500, bp), 35)

    def test_no_main_damage_means_no_twin(self):
        """A floor of 1 must not conjure a twin out of nothing."""
        self.assertEqual(formula.percentage_twin(0), 0)
        self.assertEqual(formula.percentage_twin(-500), 0)

    def test_monotone_in_damage(self):
        """More damage never buys a smaller percentage — the property the grid
        removal depends on, checked densely rather than at a few points."""
        previous = 0
        for damage in range(1, 60_000, 37):     # a prime-ish stride: hits off-grid values
            twin = formula.percentage_twin(damage)
            self.assertGreaterEqual(twin, previous)
            previous = twin

    def test_rounding_is_half_up_not_bankers(self):
        """`round()` would send 25000 -> 2 but 35000 -> 4: both .5 cases, rounded in
        opposite directions. Half-up keeps the twin a function of size alone."""
        self.assertEqual(formula.percentage_twin(25000), 3)   # 2.5 -> 3, not 2
        self.assertEqual(formula.percentage_twin(35000), 4)   # 3.5 -> 4
        bp = formula.BASIS_POINT_DENOMINATOR
        self.assertEqual(formula.percentage_twin(250, bp), 3)  # 2.5 -> 3, not 2


class PercentageGranularityTest(unittest.TestCase):
    """The percentage law (maintainer 2026-08-11/12, grid retired 2026-09-12):
    the flat grid is retired (DAMAGE_STEP = 1 — every integer legal), while the
    percentage ratio stands — **100 flat damage == 0.01% of max health**."""

    def test_the_law_in_one_line(self):
        """The twin is literally Damage/100 in basis points and can never drift
        from the weapon it belongs to; at step 1 the one-step==one-unit
        identity holds via the never-zero floor, not the ratio."""
        self.assertEqual(formula.DAMAGE_STEP, 1)
        self.assertEqual(
            formula.percentage_twin(formula.DAMAGE_STEP, formula.BASIS_POINT_DENOMINATOR), 1)
        for damage in (100, 2500, 16000, 123_400):
            with self.subTest(damage=damage):
                self.assertEqual(
                    formula.percentage_twin(damage, formula.BASIS_POINT_DENOMINATOR),
                    damage // 100)

    def test_basis_points_resolve_what_whole_percent_cannot(self):
        """15000 and 17000 damage are both "2%" in whole percent; basis points tell
        them apart (1.50% vs 1.70%). That is the granularity that was asked for."""
        self.assertEqual(formula.percentage_twin(15000), formula.percentage_twin(17000))
        self.assertEqual(
            formula.percentage_twin(15000, formula.BASIS_POINT_DENOMINATOR), 150)
        self.assertEqual(
            formula.percentage_twin(17000, formula.BASIS_POINT_DENOMINATOR), 170)

    def test_versus_band_is_multiples_of_five(self):
        """The x5 rebase of the old 1..17 band. Which 17-step window a family uses
        (5..85 preserves today's balance, 20..100 is the generalist band) is a W13
        profile decision — the STEP is the law."""
        self.assertEqual(formula.PERCENTAGE_VERSUS_STEP, 5)
        low, high = formula.PERCENTAGE_VERSUS_BOUNDS
        self.assertEqual((low, high), (5, 100))
        for band_start in (5, 10, 15, 20):
            band = [band_start + i * formula.PERCENTAGE_VERSUS_STEP for i in range(17)]
            with self.subTest(band=f"{band[0]}..{band[-1]}"):
                self.assertLessEqual(band[-1], high)
                self.assertGreaterEqual(band[0], low)

    def test_denominator_comes_from_the_node_not_a_guess(self):
        """A wrong denominator is a silent 10x error, so it is threaded explicitly."""
        self.assertEqual(formula.twin_denominator({}), 100)
        self.assertEqual(formula.twin_denominator({"percentage_denominator": 10000}), 10000)
        self.assertEqual(formula.twin_denominator({"percentage_denominator": "10000"}), 10000)

    def test_a_broken_denominator_falls_back_to_whole_percent(self):
        """0 would divide by zero and a negative would invert the twin; the safe
        fallback is the engine default, which is also what the C# rejects at load."""
        for bad in (0, -100, "nonsense", None):
            with self.subTest(bad=bad):
                self.assertEqual(
                    formula.twin_denominator({"percentage_denominator": bad}), 100)


class DistributeDamageTwinTest(unittest.TestCase):
    """The twin as `distribute_damage` writes it — the path yaml actually takes."""

    def test_distribute_uses_the_continuous_twin(self):
        whs = [_wh("m", 4000), _wh("mpercentage", 1, "AreaDamagePercentage")]
        whs[1]["percentage_denominator"] = formula.BASIS_POINT_DENOMINATOR
        self.assertEqual(formula.distribute_damage(16000, whs)["mpercentage"], 160)

    def test_distribute_writes_each_twin_in_its_own_unit(self):
        """A basis-point node and a whole-percent node in the same weapon each get the
        value THEY read as 1.60% — the ledger carries the unit per warhead, and the
        coarse one can only manage 2%."""
        stock = _wh("apercentage", 1, "HealthPercentageDamage")
        fine = _wh("bpercentage", 1, "AreaDamagePercentage")
        fine["percentage_denominator"] = formula.BASIS_POINT_DENOMINATOR
        result = formula.distribute_damage(16000, [_wh("m", 4000), stock, fine])
        self.assertEqual(result["apercentage"], 2)
        self.assertEqual(result["bpercentage"], 160)

    def test_distribute_never_writes_a_zero_twin_for_a_live_warhead(self):
        """Post-W17 a main can legally be small; the twin must survive it."""
        whs = [_wh("m", 1000), _wh("mpercentage", 1, "HealthPercentageDamage")]
        for total in (500, 1500, 1999, 2001, 3999):
            with self.subTest(total=total):
                self.assertGreaterEqual(
                    formula.distribute_damage(total, whs)["mpercentage"], 1)

    def test_other_twins_are_untouched_by_the_fix(self):
        """FF and ExtraDamage stay at 50% — W15 changes ONE derivation only."""
        whs = [_wh("m", 4000), _wh("mfriendlyfire", 1), _wh("mextradamage", 1),
               _wh("mpercentage", 1, "HealthPercentageDamage")]
        result = formula.distribute_damage(16000, whs)
        self.assertEqual(result["mfriendlyfire"], 8000)
        self.assertEqual(result["mextradamage"], 8000)


class ReferenceHpTest(unittest.TestCase):
    """`target_model.reference_hp` — design constant vs measured roster."""

    def test_reference_hp_is_the_design_constant(self):
        self.assertEqual(target_model.reference_hp(), 200_000)
        self.assertEqual(target_model.reference_hp(), target_model.REFERENCE_HP)

    def test_reference_hp_does_not_depend_on_the_roster(self):
        """The VERIFY that matters: it is a constant, so clearing the roster
        caches cannot move it. A measured value would drift with the tree."""
        before = target_model.reference_hp()
        target_model.measured_reference_hp.cache_clear()
        self.assertEqual(target_model.reference_hp(), before)

    def test_measured_value_is_still_reportable(self):
        """Kept as a diagnostic — the gap to the constant is information."""
        measured = target_model.measured_reference_hp()
        self.assertGreater(measured, 0)
        self.assertLess(measured, target_model.REFERENCE_HP,
                        "roster median has caught up with the design constant — "
                        "the constant wants a maintainer re-ruling (W15)")


if __name__ == "__main__":
    unittest.main()
