"""Unit tests for tools/balance/effective_damage.py.

Pins the parts of the metric that must track the ENGINE rather than taste: the
falloff geometry (including the single-`Range` footgun that makes a warhead deal
zero damage) and the scatter model used for hit reliability.
"""

from __future__ import annotations

import math
import pathlib
import sys
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools" / "balance"))
import effective_damage as ed  # noqa: E402
import formula as balance_formula  # noqa: E402


class Node:
    """Minimal stand-in for a resolved yaml node (only `get` is used)."""

    def __init__(self, fields):
        self.fields = fields

    def get(self, key):
        return self.fields.get(key)


class ParseTest(unittest.TestCase):
    def test_plain_and_cell_notation(self):
        self.assertEqual(ed.parse_wdist("512"), 512)
        self.assertEqual(ed.parse_wdist("1c0"), 1024)
        self.assertEqual(ed.parse_wdist("1c512"), 1536)

    def test_negative_and_averaged_ranges(self):
        self.assertEqual(ed.parse_wdist("-256"), -256)
        self.assertEqual(ed.parse_wdist("180, 240", allow_distribution=True), 210)

    def test_wdist_parser_matches_engine_scalar_syntax(self):
        self.assertEqual(ed.parse_wdist("1C0"), 1024)
        self.assertEqual(ed.parse_wdist("+1c+512"), 1536)
        self.assertEqual(ed.parse_wdist("40 c 0"), 40960)
        self.assertEqual(ed.parse_wdist(40960.0), 40960)
        for invalid in ("c512", "1c", "1.5", 1.5, "2147483648", "1c2147483648"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    ed.parse_wdist(invalid)

    def test_wdist_distribution_requires_explicit_opt_in(self):
        with self.assertRaises(ValueError):
            ed.parse_wdist("180, 240")
        with self.assertRaises(ValueError):
            ed.parse_wdist("180, ", allow_distribution=True)

    def test_safe_shared_wdist_parser_handles_ledger_wrappers_and_invalid_values(self):
        self.assertEqual(balance_formula.wdist_value({"v": "40c0"}), 40960)
        self.assertEqual(balance_formula.wdist_value("41c0"), 41984)
        self.assertIsNone(balance_formula.wdist_value("not-a-range"))
        self.assertEqual(balance_formula.wdist_value(None, 0), 0)


class GeometryTest(unittest.TestCase):
    def test_missing_geometry_uses_the_runtime_area_defaults(self):
        fo, radii, live = ed.falloff_and_radii(Node({}))
        self.assertTrue(live)
        self.assertEqual(fo, [100, 37, 14, 5, 0])
        self.assertEqual(radii, [0, 43, 86, 129, 172])

    def test_explicit_spread_below_100_is_not_clamped(self):
        fo, radii, live = ed.falloff_and_radii(
            Node({"Spread": "20", "Falloff": "100, 0"}))
        self.assertTrue(live)
        self.assertEqual((fo, radii), ([100, 0], [0, 20]))

    def test_missing_falloff_uses_runtime_curve_with_authored_spread(self):
        fo, radii, live = ed.falloff_and_radii(Node({"Spread": "100"}))
        self.assertTrue(live)
        self.assertEqual(fo, [100, 37, 14, 5, 0])
        self.assertEqual(radii, [0, 100, 200, 300, 400])

    def test_spread_grid_when_no_range(self):
        fo, radii, live = ed.falloff_and_radii(Node({"Falloff": "100, 50, 0"}), 400)
        self.assertTrue(live)
        self.assertEqual((fo, radii), ([100, 50, 0], [0, 400, 800]))

    def test_explicit_ring_list_is_used_verbatim(self):
        fo, radii, live = ed.falloff_and_radii(Node({"Range": "0, 32", "Falloff": "100, 50"}), 500)
        self.assertTrue(live)
        self.assertEqual(radii, [0, 32])

    def test_single_range_is_a_dead_warhead(self):
        """Engine: effectiveRange has 1 entry -> GetDamageFalloff always returns 0."""
        _fo, _radii, live = ed.falloff_and_radii(
            Node({"Range": "500", "Falloff": "111, 33, 11, 3"}), 500)
        self.assertFalse(live)

    def test_one_falloff_entry_is_a_dead_warhead(self):
        _fo, _radii, live = ed.falloff_and_radii(Node({"Falloff": "100"}))
        self.assertFalse(live)

    def test_range_falloff_length_mismatch_is_invalid_not_synthetic(self):
        with self.assertRaisesRegex(ValueError, "Range length"):
            ed.falloff_and_radii(
                Node({"Range": "0, 50", "Falloff": "100, 50, 0"}))

    def test_nonzero_first_range_extrapolates_the_first_segment_inward(self):
        fo, radii, live = ed.falloff_and_radii(
            Node({"Range": "100, 200", "Falloff": "50, 0"}))
        self.assertTrue(live)
        self.assertEqual(ed.runtime_falloff(fo, radii, 0), 100)
        self.assertEqual(ed.runtime_falloff(fo, radii, 150), 25)

    def test_zero_spread_has_no_live_center(self):
        fo, radii, live = ed.falloff_and_radii(
            Node({"Spread": "0", "Falloff": "100, 0"}))
        self.assertTrue(live)
        self.assertEqual(ed.runtime_falloff(fo, radii, 0), 0)
        self.assertEqual(ed.footprint_cells2(fo, radii), 0)

    def test_tick_modifiers_match_signed_csharp_truncation(self):
        self.assertEqual(ed.area_tick_modifiers(Node({"Ticks": "0"})), [])
        self.assertEqual(
            ed.area_tick_modifiers(Node({"Ticks": "3", "TickDamage": "3, -1, 1"})),
            [100, -33, 33])
        with self.assertRaisesRegex(ValueError, "TickDamage length"):
            ed.area_tick_modifiers(Node({"Ticks": "2", "TickDamage": "1"}))

    def test_csharp_div_does_not_lose_precision_through_float(self):
        self.assertEqual(ed.csharp_div(10 ** 18 + 1, 3), 333333333333333333)
        self.assertEqual(ed.csharp_div(-(10 ** 18 + 1), 3), -333333333333333333)

    def test_folded_radius_cutoff_clips_but_does_not_expand(self):
        node = Node({"Spread": "100", "Falloff": "100, 100"})
        fo, radii, _live = ed.falloff_and_radii(node)
        half = ed.area_geometry_samples(node, fo, radii, 0, radius_scale=50)
        over = ed.area_geometry_samples(node, fo, radii, 0, radius_scale=150)
        self.assertAlmostEqual(half[0][2], math.pi * (50 / 1024) ** 2, places=4)
        self.assertAlmostEqual(over[0][2], math.pi * (100 / 1024) ** 2, places=4)

    def test_footprint_grows_with_spread(self):
        small = ed.footprint_cells2([100, 0], [0, 400])
        big = ed.footprint_cells2([100, 0], [0, 800])
        self.assertGreater(big, small)

    def test_footprint_of_a_flat_disc_matches_the_circle_area(self):
        """Falloff 100,100 over 0..1024 is a full-strength disc of radius 1 cell."""
        self.assertAlmostEqual(ed.footprint_cells2([100, 100], [0, 1024]), math.pi, places=4)


class ReliabilityTest(unittest.TestCase):
    FO = [100, 50, 25, 10, 0]
    RADII = [0, 400, 800, 1200, 1600]

    def test_perfect_accuracy_is_one(self):
        self.assertEqual(ed.reliability(self.FO, self.RADII, 0), 1.0)

    def test_reliability_falls_as_scatter_grows(self):
        values = [ed.reliability(self.FO, self.RADII, s) for s in (100, 400, 800, 1600, 3200)]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_reliability_stays_a_fraction(self):
        for sigma in (0, 50, 500, 5000, 50000):
            self.assertTrue(0.0 <= ed.reliability(self.FO, self.RADII, sigma) <= 1.0)

    def test_scatter_matches_the_engine_two_axis_triangular_pdf(self):
        """Mean miss radius must be ~0.52*sigma, NOT the 0.67 of a uniform disc."""
        step = 0.001
        mean = sum(t * ed.scatter_pdf(t) for t in
                   [i * step for i in range(1, int(math.sqrt(2) / step))]) * step
        self.assertAlmostEqual(mean, 0.52, delta=0.02)

    def test_scatter_pdf_is_normalised(self):
        step = 0.001
        total = sum(ed.scatter_pdf(t) for t in
                    [i * step for i in range(0, int(math.sqrt(2) / step))]) * step
        self.assertAlmostEqual(total, 1.0, delta=0.02)

    def test_scatter_pdf_is_zero_outside_its_support(self):
        self.assertEqual(ed.scatter_pdf(-0.1), 0.0)
        self.assertEqual(ed.scatter_pdf(math.sqrt(2) + 0.1), 0.0)


class ProjectileRuntimeDefaultTest(unittest.TestCase):
    class ProjectileNode:
        def __init__(self, projectile_type, weapon_range, fields=None):
            self.projectile = Node(fields or {})
            self.projectile.value = projectile_type
            self.weapon_range = weapon_range

        def child(self, key):
            return self.projectile if key == "Projectile" else None

        def get(self, *keys):
            if keys == ("Range",):
                return self.weapon_range
            if len(keys) == 2 and keys[0] == "Projectile":
                return self.projectile.get(keys[1])
            return None

    def test_bullet_without_yaml_speed_uses_runtime_default_17(self):
        root = self.ProjectileNode("Bullet", 1700)
        instant, sigma = ed.weapon_reliability_ctx(root)
        self.assertFalse(instant)
        self.assertEqual(sigma, 2000.0)

    def test_scaled_bullet_derives_speed_and_inaccuracy_from_range(self):
        root = self.ProjectileNode(
            "ScaledBullet", 5000,
            {"ProjectileSpeedPercentage": 10, "InaccuracyPercentage": 1})
        instant, sigma = ed.weapon_reliability_ctx(root)
        self.assertFalse(instant)
        self.assertEqual(sigma, 250.0)  # 50 inaccuracy + 200 travel drift

    def test_scaled_bullet_explicit_nondefault_values_win(self):
        root = self.ProjectileNode(
            "ScaledBullet", 5000,
            {"Speed": 500, "Inaccuracy": 25,
             "ProjectileSpeedPercentage": 2, "InaccuracyPercentage": 3})
        instant, sigma = ed.weapon_reliability_ctx(root)
        self.assertFalse(instant)
        self.assertEqual(sigma, 225.0)

    def test_missile_without_yaml_speed_uses_runtime_default_384(self):
        root = self.ProjectileNode("Missile", 3840)
        instant, sigma = ed.weapon_reliability_ctx(root)
        self.assertFalse(instant)
        self.assertEqual(sigma, 200.0)

    def test_positional_hitscan_keeps_authored_scatter(self):
        for projectile in ("InstantHit", "InstantHitWithFakeBullets", "Railgun"):
            with self.subTest(projectile=projectile):
                root = self.ProjectileNode(projectile, 5000, {"Inaccuracy": 40})
                instant, sigma = ed.weapon_reliability_ctx(root)
                self.assertTrue(instant)
                self.assertEqual(sigma, 40.0)

    def test_direct_center_hitscan_ignores_authored_scatter(self):
        root = self.ProjectileNode("InstantHit", 5000, {"Inaccuracy": 400})
        original_get = root.get

        def get(*keys):
            if keys == ("TargetActorCenter",):
                return "true"
            return original_get(*keys)

        root.get = get
        instant, sigma = ed.weapon_reliability_ctx(root)
        self.assertTrue(instant)
        self.assertEqual(sigma, 0.0)

    def test_laser_zap_tracking_controls_authored_scatter(self):
        tracked = self.ProjectileNode("LaserZap", 5000, {"Inaccuracy": 80})
        untracked = self.ProjectileNode(
            "LaserZap", 5000, {"Inaccuracy": 80, "TrackTarget": "false"})
        self.assertEqual(ed.weapon_reliability_ctx(tracked), (True, 0.0))
        self.assertEqual(ed.weapon_reliability_ctx(untracked), (True, 80.0))

    def test_per_cell_inaccuracy_uses_max_range_and_csharp_truncation(self):
        root = self.ProjectileNode(
            "Missile", 7130,
            {"Speed": 10000, "Inaccuracy": 30,
             "InaccuracyType": "PerCellIncrement"})
        instant, sigma = ed.weapon_reliability_ctx(root)
        self.assertFalse(instant)
        self.assertAlmostEqual(sigma, 208 + 0.2 * 100 * 7130 / 10000)

    def test_foreign_scalar_fields_do_not_change_non_scalar_trajectories(self):
        for projectile in ("GravityBomb", "NukeLaunch"):
            with self.subTest(projectile=projectile):
                root = self.ProjectileNode(
                    projectile, 5000, {"Speed": 150, "Inaccuracy": 400})
                self.assertEqual(ed.weapon_reliability_ctx(root), (False, 0.0))
                self.assertEqual(
                    ed.model_limitations(root),
                    [f"unmodeled_projectile_trajectory:{projectile}"])

    def test_always_locked_missile_uses_lock_on_inaccuracy(self):
        root = self.ProjectileNode(
            "Missile", 3840,
            {"Inaccuracy": 640, "LockOnProbability": 100,
             "LockOnInaccuracy": 480})
        _instant, sigma = ed.weapon_reliability_ctx(root)
        self.assertEqual(sigma, 680.0)  # 480 locked scatter + 200 travel heuristic

    def test_probabilistic_missile_lock_on_is_marked_provisional(self):
        root = self.ProjectileNode(
            "Missile", 3840,
            {"LockOnProbability": 50, "LockOnInaccuracy": 100})
        self.assertIn(
            "unmodeled_projectile_lock_on:Missile", ed.model_limitations(root))


class DamageValueTest(unittest.TestCase):
    def test_numeric_forms_parse(self):
        self.assertEqual(ed.damage_value("2000"), 2000)
        self.assertEqual(ed.damage_value(2000), 2000)
        with self.assertRaisesRegex(ValueError, "Damage must be an Int32"):
            ed.damage_value("2000.7")

    def test_non_numeric_is_none_not_an_exception(self):
        for bad in (None, "", "abc", "inherit"):
            self.assertIsNone(ed.damage_value(bad))


if __name__ == "__main__":
    unittest.main()
