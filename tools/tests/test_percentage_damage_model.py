"""Fixture-only tests for percentage damage and burst-aware balance analysis."""

from __future__ import annotations

import pathlib
import sys
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import audit_upgrade_regression as upgrade  # noqa: E402
import audit_k_linearity as linearity  # noqa: E402
import check_band  # noqa: E402
import effective_damage as ed  # noqa: E402
import extract_stats  # noqa: E402
import formula  # noqa: E402
from miniyaml import Node  # noqa: E402
import percentage_damage as pd  # noqa: E402
import weapon_efficiency as we  # noqa: E402


REFERENCE_HP = 200_000


def field(key: str, value="", children=None) -> Node:
    return Node(key, str(value), list(children or []))


def table(key: str, **values) -> Node:
    return field(key, children=[field(name, value) for name, value in values.items()])


def warhead(tag: str, warhead_type: str, damage: int, *extra: Node) -> Node:
    return field(f"Warhead@{tag}", warhead_type, [field("Damage", damage), *extra])


def weapon(*children: Node) -> Node:
    return field("FixtureWeapon", children=children)


class PercentageArithmeticTest(unittest.TestCase):
    def test_folded_rounding_matches_the_engine_expression(self):
        continuous, rounded = pd.folded_units(2010, 10_000)
        self.assertEqual(continuous, 100.5)
        self.assertEqual(rounded, 101, "the engine rounds a half unit upward")
        self.assertEqual(pd.folded_units(2001, 10_000), (100.05, 100))

    def test_folded_arithmetic_uses_wide_intermediates(self):
        self.assertEqual(pd.folded_units(240_000, 10_000), (12_000, 12_000))
        self.assertEqual(pd.folded_units(600_000, 10_000), (30_000, 30_000))

    def test_percentage_runtime_mirror_uses_wide_intermediates(self):
        with self.assertRaisesRegex(OverflowError, "runtime Int32"):
            pd.runtime_percentage_hp(pd.INT32_MAX, 200, 100)
        with self.assertRaisesRegex(OverflowError, "runtime Int32"):
            pd.folded_units(pd.INT32_MAX, pd.INT32_MAX)
        self.assertEqual(pd.runtime_percentage_hp(3_750_000, 30_000, 200), 562_500_000)

    def test_percentage_runtime_mirror_truncates_negative_healing_toward_zero(self):
        self.assertEqual(pd.runtime_percentage_hp(101, -1, 100), -1)

    def test_folded_runtime_mirror_truncates_negative_values_toward_zero(self):
        self.assertEqual(pd.folded_units(-20, 10_000), (-1.0, 0))

    def test_folded_default_and_explicit_denominators(self):
        default = weapon(warhead(
            "Main", "AreaDamage", 2000,
            field("PercentageScale", 10_000)))
        explicit = weapon(warhead(
            "Main", "AreaDamage", 2000,
            field("PercentageScale", 10_000), field("PercentageDenominator", 20_000)))
        self.assertEqual(pd.percentage_applications(default, REFERENCE_HP)[0]["runtime_hp"], 2000)
        self.assertEqual(pd.percentage_applications(explicit, REFERENCE_HP)[0]["runtime_hp"], 1000)

    def test_nonstandard_denominator_uses_runtime_integer_truncation(self):
        root = weapon(warhead(
            "Main", "AreaDamage", 2000,
            field("PercentageScale", 10_000), field("PercentageDenominator", 30_000)))
        app = pd.percentage_applications(root, REFERENCE_HP)[0]
        self.assertEqual(app["runtime_hp"], 666)
        self.assertAlmostEqual(app["continuous_hp"], 2000 / 3)

    def test_alternate_damage_recomputes_denominator_truncation(self):
        root = weapon(warhead(
            "Main", "AreaDamage", 2000,
            field("PercentageScale", 10_000), field("PercentageDenominator", 30_000)))
        result = we.analyse(root, damage_total=4000)
        folded = next(p for p in result["parts"] if p["kind"] == pd.PCT_FOLDED)
        self.assertAlmostEqual(
            folded["rounding_share"] * result["flat_total"], -1 / 3)

    def test_percentage_versus_overrides_and_empty_table_falls_back(self):
        override = weapon(warhead(
            "Main", "AreaDamage", 2000,
            field("PercentageScale", 10_000), table("Versus", **{"None": 80}),
            table("PercentageVersus", **{"None": 25})))
        fallback = weapon(warhead(
            "Main", "AreaDamage", 2000,
            field("PercentageScale", 10_000), table("Versus", **{"None": 80}),
            field("PercentageVersus")))
        self.assertEqual(pd.percentage_applications(override, REFERENCE_HP)[0]["versus"]["None"], 25)
        self.assertEqual(pd.percentage_applications(fallback, REFERENCE_HP)[0]["versus"]["None"], 80)

    def test_percentage_versus_tables_reject_fractional_engine_values(self):
        root = weapon(warhead(
            "Main", "AreaDamage", 2000,
            field("PercentageScale", 10_000),
            table("PercentageVersus", **{"None": "12.5"})))
        with self.assertRaisesRegex(ValueError, "PercentageVersus.None must be an Int32"):
            pd.percentage_applications(root, REFERENCE_HP)

    def test_folded_spread_clips_instead_of_compressing_the_curve(self):
        fo, radii = pd.clip_falloff([100, 50, 0], [0, 100, 200], 75)
        self.assertEqual(radii, [0.0, 100.0, 150.0])
        self.assertEqual(fo, [100.0, 50.0, 25.0])

    def test_standalone_is_detected_by_type_not_tag(self):
        root = weapon(warhead("SmallArmsPercentage", "AreaDamagePercentage", 1))
        apps = pd.percentage_applications(root, REFERENCE_HP)
        self.assertEqual([(a["kind"], a["tag"]) for a in apps],
                         [(pd.PCT_STANDALONE, "SmallArmsPercentage")])
        self.assertEqual(apps[0]["runtime_hp"], 2000)

    def test_standalone_basis_point_denominator_is_honored(self):
        root = weapon(warhead(
            "AnyTag", "AreaDamagePercentage", 160,
            field("PercentageDenominator", 10_000)))
        self.assertEqual(pd.percentage_applications(root, REFERENCE_HP)[0]["runtime_hp"], 3200)

    def test_mixed_and_multiple_folded_applications_are_not_deduplicated(self):
        root = weapon(
            warhead("A", "AreaDamage", 2000, field("PercentageScale", 10_000)),
            warhead("B", "AreaDamage", 4000, field("PercentageScale", 5000)),
            warhead("LegacyPercentage", "AreaDamagePercentage", 1))
        apps = pd.percentage_applications(root, REFERENCE_HP)
        self.assertEqual([a["kind"] for a in apps],
                         [pd.PCT_FOLDED, pd.PCT_FOLDED, pd.PCT_STANDALONE])
        self.assertEqual([a["runtime_hp"] for a in apps], [2000, 2000, 2000])

    def test_missing_or_zero_scale_produces_no_folded_application(self):
        root = weapon(
            warhead("Missing", "AreaDamage", 2000),
            warhead("Zero", "AreaDamage", 2000, field("PercentageScale", 0)))
        self.assertEqual(pd.percentage_applications(root, REFERENCE_HP), [])

    def test_area_damage_denominator_is_validated_even_when_folded_hit_is_inert(self):
        for damage, scale in ((0, 10_000), (2000, 0)):
            root = weapon(warhead(
                "Main", "AreaDamage", damage,
                field("PercentageScale", scale), field("PercentageDenominator", 0)))
            with self.subTest(damage=damage, scale=scale):
                with self.assertRaisesRegex(ValueError, "must be positive"):
                    pd.percentage_applications(root, REFERENCE_HP)

    def test_standalone_area_percentage_rejects_invalid_pipeline_shape(self):
        invalid_denominator = weapon(warhead(
            "Standalone", "AreaDamagePercentage", 0,
            field("PercentageDenominator", 0)))
        double_percentage = weapon(warhead(
            "Standalone", "AreaDamagePercentage", 1,
            field("PercentageScale", 10_000)))
        with self.assertRaisesRegex(ValueError, "must be positive"):
            pd.percentage_applications(invalid_denominator, REFERENCE_HP)
        with self.assertRaisesRegex(ValueError, "cannot also set PercentageScale"):
            pd.percentage_applications(double_percentage, REFERENCE_HP)

    def test_health_percentage_uses_fixed_runtime_denominator(self):
        root = weapon(warhead(
            "Standalone", "HealthPercentageDamage", 1,
            field("PercentageDenominator", 10_000)))
        app = pd.percentage_applications(root, REFERENCE_HP)[0]
        self.assertEqual(app["denominator"], 100)
        self.assertEqual(app["runtime_hp"], 2000)

    def test_percentage_int_fields_reject_non_int32_values(self):
        fixtures = (
            weapon(warhead(
                "Main", "AreaDamage", 2000,
                field("PercentageScale", 10_000),
                field("PercentageDenominator", "2.5"))),
            weapon(warhead(
                "Main", "AreaDamage", 2000,
                field("PercentageScale", "1.5"))),
            weapon(warhead(
                "Main", "AreaDamage", 2000,
                field("PercentageScale", 10_000),
                field("PercentageSpread", "1.5"))),
            weapon(warhead(
                "Standalone", "AreaDamagePercentage", 1,
                field("PercentageDenominator", 2 ** 31))),
        )
        for root in fixtures:
            with self.subTest(root=root):
                with self.assertRaisesRegex(ValueError, "Int32"):
                    pd.percentage_applications(root, REFERENCE_HP)

    def test_other_engine_int_fields_reject_fractional_numeric_text(self):
        fractional_damage = weapon(warhead(
            "Main", "SpreadDamage", "100.5"))
        fractional_missile = weapon(
            field("Projectile", "Missile", [field("LockOnProbability", "99.5")]),
            warhead("Main", "SpreadDamage", 100))
        with self.assertRaisesRegex(ValueError, "Damage must be an Int32"):
            ed.effective_damage(fractional_damage)
        with self.assertRaisesRegex(ValueError, "LockOnProbability must be an Int32"):
            ed.effective_damage(fractional_missile)

    def test_engine_boolean_fields_reject_non_boolean_aliases(self):
        malformed = weapon(
            field("TargetActorCenter", "yes"),
            field("Projectile", "InstantHit"),
            warhead("Main", "AreaDamage", 100))
        with self.assertRaisesRegex(ValueError, "must be true or false"):
            we.analyse(malformed)

    def test_folded_damage_is_scalable_and_never_the_absolute_floor(self):
        root = weapon(warhead(
            "Main", "AreaDamage", 2000,
            field("Spread", 100), field("Falloff", "100, 0"),
            field("PercentageScale", 10_000)))
        result = we.analyse(root)
        self.assertIsNotNone(result)
        self.assertEqual(result["pct_absolute"], 0)
        self.assertTrue(any(p["kind"] == pd.PCT_FOLDED for p in result["parts"]))
        self.assertGreater(result["k_flat"], 1.0)

    def test_large_folded_damage_remains_linear(self):
        root = weapon(warhead(
            "Main", "AreaDamage", 240_000,
            field("PercentageScale", 10_000)))
        result = we.analyse(root)
        folded = next(p for p in result["parts"] if p["kind"] == pd.PCT_FOLDED)
        self.assertEqual(folded["rounding_share"], 0)
        self.assertNotIn(
            "nonlinear_folded_percentage_overflow",
            result["model_limitations"])

    def test_health_percentage_damage_has_direct_target_geometry(self):
        root = weapon(
            field("TargetActorCenter", "true"),
            field("Projectile", "InstantHit"),
            warhead("AnyTag", "HealthPercentageDamage", 1))
        result = we.analyse(root)
        part = next(p for p in result["parts"] if p["kind"] == pd.PCT_STANDALONE)
        self.assertEqual(part["rel"], 1.0)
        self.assertEqual(part["secondary"], 0.0)
        self.assertEqual(part["footprint"], 0.0)

    def test_health_percentage_damage_spread_retains_projectile_miss_reliability(self):
        root = weapon(
            field("Range", 1000),
            field("Projectile", "Bullet", [
                field("Speed", 100), field("Inaccuracy", 500)]),
            warhead("AnyTag", "HealthPercentageDamage", 1,
                    field("Spread", 500)))
        result = we.analyse(root)
        part = next(p for p in result["parts"] if p["kind"] == pd.PCT_STANDALONE)
        self.assertLess(part["rel"], 1.0)
        self.assertGreater(part["rel"], 0.0)
        self.assertGreater(part["footprint"], 0.0)

    def test_positional_target_damage_without_spread_deals_zero(self):
        root = weapon(
            field("Projectile", "InstantExplode"),
            warhead("Flat", "TargetDamage", 100),
            warhead("Percentage", "HealthPercentageDamage", 1))
        result = we.analyse(root)
        self.assertFalse(result["direct_actor"])
        for part in result["parts"]:
            self.assertEqual(part["rel"], 0.0)
            self.assertEqual(part["secondary"], 0.0)
            self.assertEqual(part["footprint"], 0.0)

        effective, base, footprint, reliability, _sigma = ed.effective_damage(root)
        self.assertEqual(base, 100)
        self.assertEqual(effective, 0.0)
        self.assertEqual(footprint, 0.0)
        self.assertEqual(reliability, 0.0)

    def test_positional_target_damage_with_spread_is_uniform(self):
        root = weapon(
            field("Projectile", "InstantExplode"),
            warhead("Flat", "TargetDamage", 100, field("Spread", 500)))
        result = we.analyse(root)
        part = result["parts"][0]
        self.assertEqual(part["rel"], 1.0)
        self.assertGreater(part["footprint"], 0.0)

    def test_health_percentage_spread_has_uniform_area_geometry(self):
        root = weapon(warhead(
            "AnyTag", "HealthPercentageDamage", 1, field("Spread", 1024)))
        result = we.analyse(root)
        part = next(p for p in result["parts"] if p["kind"] == pd.PCT_STANDALONE)
        self.assertGreater(part["footprint"], 3.0)
        self.assertGreater(part["secondary"], 0.0)

    def test_target_center_hitscan_bypasses_area_geometry_for_every_damage_part(self):
        root = weapon(
            field("TargetActorCenter", "true"),
            field("Projectile", "InstantHitWithFakeBullets"),
            warhead("Main", "AreaDamage", 2000,
                    field("Spread", 1024), field("Falloff", "50, 0"),
                    field("Ticks", 4), field("PercentageScale", 10_000)),
            warhead("Standalone", "AreaDamagePercentage", 1,
                    field("Spread", 1024), field("Falloff", "50, 0")))
        result = we.analyse(root)
        self.assertTrue(result["direct_actor"])
        self.assertEqual(
            [part["kind"] for part in result["parts"]],
            ["flat", pd.PCT_FOLDED, pd.PCT_STANDALONE])
        for part in result["parts"]:
            self.assertEqual(part["rel"], 1.0)
            self.assertEqual(part["secondary"], 0.0)
            self.assertEqual(part["footprint"], 0.0)

    def test_instant_positional_impact_uses_authored_center_falloff(self):
        root = weapon(
            field("Projectile", "InstantExplode"),
            warhead("Main", "AreaDamage", 100,
                    field("Spread", 100), field("Falloff", "50, 0"),
                    field("PercentageScale", 10_000)),
            warhead("Standalone", "AreaDamagePercentage", 1,
                    field("Spread", 100), field("Falloff", "50, 0")))

        result = we.analyse(root)
        self.assertFalse(result["direct_actor"])
        self.assertTrue(result["instant"])
        for part in result["parts"]:
            self.assertEqual(part["rel"], 0.5)

        effective, base, footprint, reliability, sigma = ed.effective_damage(root)
        self.assertEqual(base, 100)
        self.assertEqual(reliability, 0.5)
        self.assertEqual(sigma, 0.0)
        self.assertAlmostEqual(
            effective, base * (0.5 + ed.SWARM_W * footprint))

    def test_missing_area_geometry_uses_runtime_defaults_for_all_damage_parts(self):
        root = weapon(
            field("Projectile", "InstantExplode"),
            warhead("Main", "AreaDamage", 100,
                    field("PercentageScale", 10_000)),
            warhead("Standalone", "AreaDamagePercentage", 1))

        result = we.analyse(root)
        expected_radii = [
            i * ed.DEFAULT_AREA_SPREAD for i in range(len(ed.DEFAULT_AREA_FALLOFF))]
        expected_footprint = ed.footprint_cells2(
            list(ed.DEFAULT_AREA_FALLOFF), expected_radii)
        parts = {part["kind"]: part for part in result["parts"]}
        self.assertEqual(parts["flat"]["rel"], 1.0)
        self.assertAlmostEqual(parts["flat"]["footprint"], expected_footprint)
        self.assertEqual(parts[pd.PCT_STANDALONE]["rel"], 1.0)
        self.assertAlmostEqual(
            parts[pd.PCT_STANDALONE]["footprint"], expected_footprint)
        self.assertGreater(parts[pd.PCT_FOLDED]["footprint"], 0.0)
        self.assertLess(parts[pd.PCT_FOLDED]["footprint"], expected_footprint)

    def test_hitscan_without_target_center_keeps_positional_area_geometry(self):
        root = weapon(
            field("Projectile", "InstantHitWithFakeBullets"),
            warhead("Main", "AreaDamage", 2000,
                    field("Spread", 1024), field("Falloff", "100, 0")))
        result = we.analyse(root)
        self.assertFalse(result["direct_actor"])
        self.assertGreater(result["parts"][0]["footprint"], 0.0)

    def test_area_beam_uses_direct_warhead_geometry(self):
        root = weapon(
            field("Projectile", "AreaBeam", [
                field("Duration", 60), field("DamageInterval", 4)]),
            warhead("Main", "AreaDamage", 2000,
                    field("Spread", 1024), field("Falloff", "100, 0"),
                    field("PercentageScale", 10_000)))
        result = we.analyse(root)
        self.assertTrue(result["direct_actor"])
        self.assertTrue(any(
            part["kind"] == pd.PCT_FOLDED for part in result["parts"]))
        self.assertTrue(all(part["footprint"] == 0.0 for part in result["parts"]))
        self.assertEqual(result["projectile_impact_multiplier"], 15)
        self.assertEqual(
            result["model_limitations"],
            ["unmodeled_projectile_geometry:AreaBeam"])
        legacy_effective, legacy_base, _footprint, legacy_rel, _sigma = \
            ed.effective_damage(root)
        self.assertEqual(legacy_effective, 30_000)
        self.assertEqual(legacy_base, 2_000)
        self.assertLessEqual(legacy_rel, 1.0)

        single = we.analyse(weapon(
            field("Projectile", "AreaBeam", [
                field("Duration", 4), field("DamageInterval", 4)]),
            warhead("Main", "AreaDamage", 2000,
                    field("PercentageScale", 10_000))))
        self.assertAlmostEqual(result["effective"], single["effective"] * 15)

        derived = extract_stats.derived_metrics(
            root, {"burst": {"v": "1"}, "reloaddelay": {"v": "60"}})
        self.assertEqual(derived["projectile_impact_multiplier"], 15)
        self.assertAlmostEqual(derived["effective_dps"], result["effective"] / 60, places=2)

    def test_area_beam_nonintegral_cadence_is_flagged_as_phase_average(self):
        root = weapon(
            field("Projectile", "AreaBeam", [
                field("Duration", 10), field("DamageInterval", 3)]),
            warhead("Main", "AreaDamage", 2000))
        result = we.analyse(root)
        self.assertAlmostEqual(result["projectile_impact_multiplier"], 10 / 3)
        self.assertIn(
            "phase_averaged_projectile_cadence:AreaBeam",
            result["model_limitations"])

    def test_tracked_area_beam_cannot_miss_its_selected_actor(self):
        root = weapon(
            field("Range", 6000),
            field("Projectile", "AreaBeam", [
                field("Speed", 128), field("Inaccuracy", 900),
                field("TrackTarget", "true"), field("Duration", 4),
                field("DamageInterval", 4)]),
            warhead("Main", "AreaDamage", 2000,
                    field("Falloff", "50, 0")))
        result = we.analyse(root)
        self.assertFalse(result["instant"])
        self.assertTrue(result["direct_actor"])
        self.assertEqual(result["sigma"], 0.0)
        self.assertEqual(result["parts"][0]["rel"], 1.0)

    def test_lightning_damage_duration_counts_every_runtime_impact(self):
        root = weapon(
            field("Projectile", "LightningZap", [
                field("Duration", 5), field("DamageDuration", 3)]),
            warhead("Main", "AreaDamage", 2000,
                    field("PercentageScale", 10_000)))
        result = we.analyse(root)
        self.assertEqual(result["projectile_impact_multiplier"], 3.0)

        clipped = weapon(
            field("Projectile", "LightningZap", [
                field("Duration", 2), field("DamageDuration", 5)]),
            warhead("Main", "AreaDamage", 2000))
        self.assertEqual(we.analyse(clipped)["projectile_impact_multiplier"], 2.0)

        disabled = weapon(
            field("Projectile", "LightningZap", [field("DamageDuration", 0)]),
            warhead("Main", "AreaDamage", 2000))
        self.assertEqual(we.analyse(disabled)["effective"], 0.0)

    def test_laser_zap_damage_interval_counts_runtime_impacts(self):
        def result(projectile_type="LaserZap", **fields):
            return we.analyse(weapon(
                field("Projectile", projectile_type, [
                    field(name, value) for name, value in fields.items()]),
                warhead("Main", "AreaDamage", 2000)))

        self.assertEqual(result()["projectile_impact_multiplier"], 1.0)
        self.assertEqual(result(
            Duration=10, DamageDuration=5,
            DamageInterval=2)["projectile_impact_multiplier"], 3.0)
        self.assertEqual(result(
            Duration=3, DamageDuration=20,
            DamageInterval=2)["projectile_impact_multiplier"], 2.0)
        self.assertEqual(result(
            DamageDuration=4, DamageInterval=0)["projectile_impact_multiplier"], 4.0)
        self.assertEqual(result(
            projectile_type="LaserZapCA", DamageDuration=0)["effective"], 0.0)

    def test_laser_zap_hitanim_extension_is_explicitly_provisional(self):
        root = weapon(
            field("Projectile", "LaserZap", [
                field("Duration", 3), field("DamageDuration", 20),
                field("DamageInterval", 2), field("HitAnim", "spark")]),
            warhead("Main", "AreaDamage", 2000))
        result = we.analyse(root)
        self.assertEqual(result["projectile_impact_multiplier"], 2.0)
        self.assertIn(
            "unmodeled_projectile_hitanim_lifetime:LaserZap",
            result["model_limitations"])

    def test_invalid_area_beam_cadence_is_rejected(self):
        root = weapon(
            field("Projectile", "AreaBeam", [field("DamageInterval", 0)]),
            warhead("Main", "AreaDamage", 2000))
        with self.assertRaisesRegex(ValueError, "AreaBeam cadence must be positive"):
            we.analyse(root)

    def test_sprite_athena_laser_exposes_nominal_corridor_cadence(self):
        root = weapon(
            field("Range", 5376),
            field("Projectile", "SpriteAthenaLaser", [
                field("Speed", 52), field("ExplosionInterval", 3),
                field("StayTicks", 5)]),
            warhead("Main", "AreaDamage", 100))
        result = we.analyse(root)
        self.assertEqual(result["nominal_projectile_impacts"], 36)
        self.assertEqual(result["projectile_impact_multiplier"], 1.0)
        self.assertEqual(result["model_limitations"], [
            "unmodeled_projectile_cadence:SpriteAthenaLaser",
            "unmodeled_projectile_geometry:SpriteAthenaLaser",
        ])

        disabled = weapon(
            field("Range", 5376),
            field("Projectile", "SpriteAthenaLaser", [
                field("Speed", 52), field("ExplosionInterval", 9999),
                field("StayTicks", 5)]),
            warhead("Main", "AreaDamage", 100))
        disabled_result = we.analyse(disabled)
        self.assertEqual(disabled_result["nominal_projectile_impacts"], 0)
        self.assertEqual(disabled_result["projectile_impact_multiplier"], 0.0)
        self.assertEqual(disabled_result["effective"], 0.0)

    def test_railgun_is_direct_only_when_line_damage_is_enabled(self):
        def result(enabled):
            return we.analyse(weapon(
                field("Projectile", "Railgun", [field("DamageActorsInLine", enabled)]),
                warhead("Main", "AreaDamage", 2000,
                        field("Spread", 1024), field("Falloff", "100, 0"))))

        enabled = result("true")
        self.assertTrue(enabled["direct_actor"])
        self.assertEqual(
            enabled["model_limitations"],
            ["unmodeled_projectile_geometry:Railgun.line"])
        self.assertFalse(result("false")["direct_actor"])

    def test_sprite_railguns_are_direct_only_with_positive_line_width(self):
        for projectile_type in ("SpriteRailgun", "SmokeParticleRailgun"):
            with self.subTest(projectile=projectile_type):
                def result(width):
                    return we.analyse(weapon(
                        field("Projectile", projectile_type, [field("LineWidth", width)]),
                        warhead("Main", "AreaDamage", 2000,
                                field("Spread", 1024), field("Falloff", "100, 0"))))

                enabled = result(1)
                self.assertTrue(enabled["direct_actor"])
                self.assertEqual(
                    enabled["model_limitations"],
                    [f"unmodeled_projectile_geometry:{projectile_type}.line"])
                self.assertFalse(result(0)["direct_actor"])

    def test_shaped_linear_pulse_uses_direct_warhead_geometry(self):
        def result(impact_type):
            return we.analyse(weapon(
                field("Range", 4096),
                field("Projectile", "LinearPulse", [
                    field("Speed", 512), field("ImpactType", impact_type)]),
                warhead("Standalone", "AreaDamagePercentage", 1,
                        field("Spread", 1024), field("Falloff", "100, 0"))))

        cone = result("Cone")
        standard = result("StandardImpact")
        self.assertTrue(cone["direct_actor"])
        self.assertLess(cone["parts"][0]["rel"], 1.0)
        self.assertEqual(cone["parts"][0]["footprint"], 0.0)
        self.assertEqual(
            cone["model_limitations"],
            ["unmodeled_projectile_geometry:LinearPulse.Cone"])
        derived = extract_stats.derived_metrics(
            weapon(
                field("Range", 4096),
                field("Projectile", "LinearPulse", [
                    field("Speed", 512), field("ImpactType", "Cone")]),
                warhead("Standalone", "AreaDamagePercentage", 1)),
            {"burst": {"v": "1"}, "reloaddelay": {"v": "60"}})
        self.assertEqual(derived["model_status"], "provisional")
        self.assertEqual(
            derived["model_limitations"],
            ["unmodeled_projectile_geometry:LinearPulse.Cone"])
        self.assertFalse(standard["direct_actor"])
        self.assertGreater(standard["parts"][0]["footprint"], 0.0)

    def test_legacy_effective_damage_uses_the_same_direct_actor_classifier(self):
        root = weapon(
            field("TargetActorCenter", "true"),
            field("Projectile", "InstantHit"),
            warhead("Main", "AreaDamage", 2000,
                    field("Spread", 1024), field("Falloff", "100, 0")))
        _effective, _base, footprint, reliability, _sigma = ed.effective_damage(root)
        self.assertEqual(footprint, 0.0)
        self.assertEqual(reliability, 1.0)

    def test_expanding_area_rings_are_tick_weighted_for_flat_and_percentage(self):
        def scored(kind, max_radius=None):
            extra = [field("Spread", 100), field("Falloff", "100, 0"), field("Ticks", 2)]
            if max_radius is not None:
                extra.append(field("MaxRadius", max_radius))
            root = weapon(warhead("Main", kind, 2000 if kind == "AreaDamage" else 1, *extra))
            return we.analyse(root)["parts"][0]

        for kind in ("AreaDamage", "AreaDamagePercentage"):
            static = scored(kind)
            expanding = scored(kind, 100)
            self.assertLess(expanding["footprint"], static["footprint"])
            self.assertLessEqual(expanding["secondary"], static["secondary"])

    def test_inert_area_nodes_still_validate_ruleset_geometry(self):
        invalid_geometry = (
            weapon(warhead(
                "Flat", "SpreadDamage", 0,
                field("Falloff", "100, 0"), field("Range", "100, 200, 300"))),
            weapon(warhead(
                "Flat", "AreaDamage", 0,
                field("Falloff", "100, 0"), field("Range", "100, 200, 300"))),
            weapon(warhead(
                "Standalone", "AreaDamagePercentage", 0,
                field("Falloff", "100, 0"), field("Range", "100, 200, 300"))),
        )
        for root in invalid_geometry:
            with self.subTest(kind=root.children[0].value):
                with self.assertRaisesRegex(ValueError, "Range length"):
                    we.analyse(root)
                with self.assertRaisesRegex(ValueError, "Range length"):
                    ed.effective_damage(root)

        invalid_ticks = weapon(warhead(
            "Flat", "AreaDamage", 0,
            field("Ticks", 2), field("TickDamage", "100")))
        with self.assertRaisesRegex(ValueError, "TickDamage length"):
            we.analyse(invalid_ticks)
        with self.assertRaisesRegex(ValueError, "TickDamage length"):
            ed.effective_damage(invalid_ticks)

    def test_zero_flat_damage_still_reports_the_standalone_floor(self):
        root = weapon(
            warhead("Main", "AreaDamage", 2000),
            warhead("Standalone", "AreaDamagePercentage", 1))
        result = we.analyse(root, damage_total=0)
        self.assertIsNone(result["k"])
        self.assertGreater(result["pct_absolute_context"], 0)
        self.assertAlmostEqual(result["effective"], result["pct_absolute_context"])

    def test_percentage_only_weapon_does_not_invent_flat_damage(self):
        root = weapon(warhead("Standalone", "AreaDamagePercentage", 1))
        result = we.analyse(root)
        self.assertEqual(result["flat_total"], 0)
        self.assertEqual(result["damage_total"], 0)
        self.assertIsNone(result["k"])
        self.assertIsNone(result["k_context"])
        self.assertEqual(result["k_flat"], 0)
        self.assertGreater(result["pct_absolute_context"], 0)
        self.assertAlmostEqual(result["effective"], result["pct_absolute_context"])

        derived = extract_stats.derived_metrics(
            root, {"burst": {"v": "1"}, "reloaddelay": {"v": "60"}})
        self.assertNotIn("k", derived)
        self.assertNotIn("k_context", derived)
        self.assertNotIn("avg_versus", derived)
        self.assertGreater(derived["effective_per_shot"], 0)
        self.assertEqual(derived["effective_dps"], derived["dps_floor"])

    def test_independent_inventory_sees_forbidden_double_percentage_shape(self):
        root = weapon(warhead(
            "Double", "AreaDamagePercentage", 1,
            field("PercentageScale", 10_000)))
        self.assertEqual(
            linearity.runtime_percentage_inventory(root),
            {(pd.PCT_STANDALONE, "Double"): 1, (pd.PCT_FOLDED, "Double"): 1})

    def test_inventory_includes_folded_hit_for_direct_actor_runtime(self):
        root = weapon(
            field("TargetActorCenter", "true"),
            field("Projectile", "InstantHit"),
            warhead("Main", "AreaDamage", 2000,
                    field("PercentageScale", 10_000)),
            warhead("Standalone", "AreaDamagePercentage", 1))
        self.assertEqual(
            linearity.runtime_percentage_inventory(root),
            {(pd.PCT_FOLDED, "Main"): 1,
             (pd.PCT_STANDALONE, "Standalone"): 1})

    def test_linearity_scaling_keeps_engine_int32_damage(self):
        root = weapon(warhead(
            "Main", "AreaDamage", 2000,
            field("PercentageScale", 10_000)))
        scaled = linearity.scale_flat(root, 2)
        damage = scaled.child("Warhead@Main").get("Damage")
        self.assertEqual(damage, "4000")
        self.assertIsNotNone(we.analyse(scaled))


class BurstCycleTest(unittest.TestCase):
    def test_default_single_and_list_delays(self):
        self.assertEqual(formula.eff_reload(60, 3, None), 70)
        self.assertEqual(formula.eff_reload(60, 3, 2), 64)
        self.assertEqual(formula.eff_reload(60, 3, "2, 7"), 69)
        self.assertEqual(formula.eff_reload(60, 3, 0), 60)

    def test_delay_lists_are_integer_only_and_round_trip_cleanly(self):
        self.assertEqual(formula.burst_delay_values("2"), [2])
        self.assertEqual(formula.burst_delay_values("2, 7"), [2, 7])
        self.assertEqual(formula.burst_delays_text("2.0, 7"), "2, 7")
        for invalid in ("2.5", "2, nope", "", 2 ** 31):
            self.assertIsNone(formula.burst_delay_values(invalid))

    def test_check_band_preserves_raw_scalar_and_list_delays(self):
        def inputs(delay):
            unit = {
                "hp": {"v": "1000"},
                "speed": {"v": "100"},
                "armaments": [{
                    "pricing": True,
                    "damage_warheads": [{
                        "tag": "Main", "type": "SpreadDamage", "damage": "100"}],
                    "reloaddelay": "60", "burst": "3", "burstdelays": delay,
                    "range": "5000",
                }],
            }
            return check_band.unit_inputs(unit)[3]

        self.assertAlmostEqual(inputs("2"), 300 / 64)
        self.assertAlmostEqual(inputs("2, 7"), 300 / 69)
        self.assertAlmostEqual(inputs(None), 300 / 70)

class UpgradeRegressionFixtureTest(unittest.TestCase):
    class Rules:
        def __init__(self, nodes):
            self.nodes = nodes

        def resolve_weapon(self, name):
            return self.nodes.get(name)

    @staticmethod
    def _gun(damage: int, percentage_versus: int) -> Node:
        return weapon(
            field("ReloadDelay", 60), field("Burst", 2), field("BurstDelays", 2),
            warhead(
                "Main", "AreaDamage", damage,
                field("PercentageScale", 10_000),
                table("PercentageVersus", **{"None": percentage_versus})))

    def test_folded_damage_changes_a_false_downgrade_into_a_slight_gain(self):
        rules = self.Rules({"base": self._gun(10_000, 10), "upgrade": self._gun(9700, 14)})
        base = upgrade.weapon_profile(rules, "base")
        upgraded = upgrade.weapon_profile(rules, "upgrade")
        self.assertAlmostEqual(9700 / 10_000, 0.97)
        ratio = upgraded["per_armor"]["None"] / base["per_armor"]["None"]
        self.assertGreater(ratio, 1.0)
        self.assertLess(ratio, 1.01)
        self.assertAlmostEqual(base["rate"], 2 / 62)
        self.assertAlmostEqual(upgraded["rate"], 2 / 62)

    def test_cycle_uses_runtime_reload_default(self):
        self.assertEqual(upgrade.cycle_rate(weapon()), 1.0)
        self.assertEqual(upgrade.cycle_rate(weapon(field("ReloadDelay", 0))), 0.0)

    def test_continuous_center_multiplier_includes_falloff_and_tick_split(self):
        area = warhead(
            "Main", "AreaDamage", 100,
            field("Falloff", "50, 0"), field("Ticks", 3))
        self.assertAlmostEqual(upgrade.centered_multiplier(area), 0.495)

        rules = self.Rules({"area": weapon(field("ReloadDelay", 1), area)})
        profile = upgrade.weapon_profile(rules, "area")
        self.assertEqual(profile["per_armor"]["None"], 48)

    def test_direct_actor_upgrade_profile_bypasses_area_ticks_and_falloff(self):
        direct = weapon(
            field("ReloadDelay", 1), field("TargetActorCenter", "true"),
            field("Projectile", "InstantHit"),
            warhead("Main", "AreaDamage", 100,
                    field("Falloff", "50, 0"), field("Ticks", 3),
                    field("PercentageScale", 10_000)))
        profile = upgrade.weapon_profile(self.Rules({"direct": direct}), "direct")
        self.assertEqual(profile["per_armor"]["None"], 200)

    def test_area_beam_duration_downgrade_is_visible_to_upgrade_guard(self):
        def beam(duration):
            return weapon(
                field("ReloadDelay", 60),
                field("Projectile", "AreaBeam", [
                    field("Duration", duration), field("DamageInterval", 4)]),
                warhead("Main", "AreaDamage", 2000))

        rules = self.Rules({"base": beam(60), "upgrade": beam(4)})
        base = upgrade.weapon_profile(rules, "base")
        upgraded = upgrade.weapon_profile(rules, "upgrade")
        self.assertEqual(base["projectile_impact_multiplier"], 15)
        self.assertEqual(upgraded["projectile_impact_multiplier"], 1)
        self.assertAlmostEqual(
            upgraded["per_armor"]["None"] / base["per_armor"]["None"],
            1 / 15)


if __name__ == "__main__":
    unittest.main()
