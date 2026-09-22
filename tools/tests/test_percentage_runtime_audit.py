"""Focused tests for the shared-mode audit correction (bounded, fixture-only)."""

from __future__ import annotations

import pathlib
import sys
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import audit_percentage_runtime as audit  # noqa: E402
import percentage_damage as pd  # noqa: E402
from miniyaml import Node  # noqa: E402


def field(key: str, value="", children=None) -> Node:
    return Node(key, str(value), list(children or []))


def folded_app(damage: int, scale: int) -> dict:
    return {
        "kind": pd.PCT_FOLDED,
        "tag": "Main",
        "node": field("Warhead@Main", "AreaDamage"),
        "damage": damage,
        "scale": scale,
    }


class OverflowClassificationTest(unittest.TestCase):
    def test_shared_halving_is_not_overflow(self):
        # TS90mm-family shape: Scale 10000 -> 2000 (design scale), h=1000.
        # legacy Int32 == wide legacy == 60; shared runtime units differ.
        apps = [folded_app(6000, 2000)]
        self.assertEqual(audit.legacy_folded_units(6000, 2000), 60)
        self.assertEqual(pd.folded_units(6000, 2000)[1], 60)
        self.assertEqual(
            pd.shared_folded_units(6000, 2000, 1000), (30.0, 30))
        self.assertEqual(audit.overflow_repairs(apps), [])

    def test_true_int32_wrap_is_still_reported(self):
        # 240000 * 10000 wraps an Int32 product; the wide legacy result does not.
        apps = [folded_app(240_000, 10_000)]
        self.assertLess(audit.legacy_folded_units(240_000, 10_000), 0)
        self.assertEqual(pd.folded_units(240_000, 10_000)[1], 12_000)
        rows = audit.overflow_repairs(apps)
        self.assertEqual(len(rows), 1)
        app, old_units, wide_units = rows[0]
        self.assertEqual(old_units, -9474)
        self.assertEqual(wide_units, 12_000)
        self.assertEqual(app["damage"], 240_000)

    def test_non_wrapping_values_are_not_overflow_at_any_scale(self):
        self.assertEqual(audit.overflow_repairs([folded_app(2000, 10_000)]), [])


class SharedInventoryTest(unittest.TestCase):
    def shared_weapon(self, *children) -> Node:
        return field("FixtureWeapon", children=[
            field("Warhead@Main", "AreaDamage", list(children))])

    def test_shared_row_reports_authored_fields_and_runtime_units(self):
        node = self.shared_weapon(
            field("Damage", 6000),
            field("PercentageScale", 2000),
            field("Heaviness", 1000),
            field("HeavinessMode", "SharedVersus"))
        rows = audit.shared_inventory_rows(node)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["heaviness"], 1000)
        self.assertEqual(rows[0]["damage"], 6000)
        self.assertEqual(rows[0]["scale"], 2000)
        self.assertEqual(rows[0]["runtime_units"], 30)
        self.assertFalse(rows[0]["zero_unit"])

    def test_zero_unit_shared_stays_visible(self):
        node = self.shared_weapon(
            field("Damage", 80_000),
            field("PercentageScale", 2000),
            field("Heaviness", 0),
            field("HeavinessMode", "SharedVersus"))
        rows = audit.shared_inventory_rows(node)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["runtime_units"], 0)
        self.assertTrue(rows[0]["zero_unit"])

    def test_positive_estimate_rounded_to_zero_is_runtime_zero(self):
        node = self.shared_weapon(
            field("Damage", 1), field("PercentageScale", 2000),
            field("Heaviness", 1000), field("HeavinessMode", "SharedVersus"))
        rows = audit.shared_inventory_rows(node)
        self.assertEqual(rows[0]["runtime_units"], 0)
        self.assertTrue(rows[0]["zero_unit"])

    def test_absent_heaviness_mode_is_not_shared(self):
        legacy = self.shared_weapon(
            field("Damage", 2000), field("PercentageScale", 10_000))
        self.assertEqual(audit.shared_inventory_rows(legacy), [])

    def test_invalid_mode_is_not_silently_hidden(self):
        unknown = self.shared_weapon(
            field("Damage", 2000), field("PercentageScale", 10_000),
            field("HeavinessMode", "Bogus"))
        with self.assertRaises(ValueError):
            audit.shared_inventory_rows(unknown)

    def test_negative_inputs_are_not_reported_as_valid_zero_rows(self):
        for damage, scale in ((-1, 2000), (2000, -1)):
            with self.subTest(damage=damage, scale=scale):
                node = self.shared_weapon(
                    field("Damage", damage), field("PercentageScale", scale),
                    field("Heaviness", 0), field("HeavinessMode", "SharedVersus"))
                with self.assertRaises(ValueError):
                    audit.shared_inventory_rows(node)


if __name__ == "__main__":
    unittest.main(verbosity=2)
