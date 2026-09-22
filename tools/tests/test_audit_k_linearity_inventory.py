"""Focused fixture tests for the k-linearity L0 shared-mode inventory correction."""

from __future__ import annotations

from collections import Counter
import pathlib
import sys
import unittest

import _bootstrap  # noqa: F401 - sys.path side effect

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import audit_k_linearity as linearity  # noqa: E402
import effective_heaviness as eh  # noqa: E402
import percentage_damage as pd  # noqa: E402
from miniyaml import Node  # noqa: E402


REFERENCE_HP = 200_000


def field(key: str, value="", children=None) -> Node:
    return Node(key, str(value), list(children or []))


def weapon(*children: Node) -> Node:
    return field("FixtureWeapon", children=list(children))


class InventoryFixtureTest(unittest.TestCase):
    def inventory(self, *children: Node) -> dict:
        # Counters compare equal to plain dicts with the same key counts.
        return dict(linearity.runtime_percentage_inventory(weapon(*children)))

    def modeled(self, *children: Node) -> dict:
        root = weapon(*children)
        return dict(Counter((part["kind"], part["tag"])
                            for part in pd.percentage_applications(root, REFERENCE_HP)))

    def shared(self, heaviness: int, *extra: Node) -> Node:
        return field(
            "Warhead@Main", "AreaDamage",
            [field("Damage", 3000), field("PercentageScale", 2000),
             field("Heaviness", heaviness),
             field("HeavinessMode", "SharedVersus"), *extra])

    def test_active_zero_heaviness_excludes_the_folded_hit(self):
        # corrino_buggy_gun shape: ACTIVE h = 0 - the SHARED folded units are
        # Damage x Scale x h / (200000 x 2000) = exactly zero, so nothing
        # (folded or otherwise) is expected from the warhead.
        self.assertEqual(self.inventory(self.shared(0)), {})
        self.assertEqual(self.modeled(self.shared(0)), {})

    def test_positive_heaviness_includes_one_folded_application(self):
        expect = {(pd.PCT_FOLDED, "Main"): 1}
        self.assertEqual(self.inventory(self.shared(1000)), expect)
        self.assertEqual(self.modeled(self.shared(1000)), expect)

    def test_tiny_positive_continuous_kept_when_runtime_rounds_to_zero(self):
        # Shared: Damage 1 x Scale 2000 x h 1000 = 2000000 over
        # the 400-million step - positive, though ONE half-up runtime step
        # rounds to 0. The model keeps the CONTINUOUS coefficient
        # independently of the runtime quantisation, so the hit is retained.
        tiny = field("Warhead@Tiny", "AreaDamage", [
            field("Damage", 1), field("PercentageScale", 2000),
            field("Heaviness", 1000),
            field("HeavinessMode", "SharedVersus")])
        expect = {(pd.PCT_FOLDED, "Tiny"): 1}
        self.assertEqual(self.inventory(tiny), expect)
        self.assertEqual(self.modeled(tiny), expect)
        # Legacy twin: Damage x Scale / 200000 is also tiny-but-positive and
        # the legacy behavior (retained on Scale > 0 alone) is unchanged.
        legacy_tiny = field("Warhead@Tiny", "AreaDamage", [
            field("Damage", 1), field("PercentageScale", 1)])
        self.assertEqual(self.inventory(legacy_tiny), expect)
        self.assertEqual(self.modeled(legacy_tiny), expect)

    def test_legacy_inventory_behavior_is_unchanged(self):
        with_scale = field("Warhead@Main", "AreaDamage", [
            field("Damage", 2000), field("PercentageScale", 10_000)])
        expect = {(pd.PCT_FOLDED, "Main"): 1}
        self.assertEqual(self.inventory(with_scale), expect)
        self.assertEqual(self.modeled(with_scale), expect)
        without_scale = field("Warhead@Main", "AreaDamage", [
            field("Damage", 2000)])
        self.assertEqual(self.inventory(without_scale), {})
        self.assertEqual(self.modeled(without_scale), {})

    def test_synthetic_mixed_weapon_agrees_with_the_model(self):
        # Synthetic mixed shape, not an assertion about today's RA2sabot.
        sabot = field("Warhead@CannonAP_Light", "AreaDamage", [
            field("Damage", 80000), field("Heaviness", 0),
            field("HeavinessMode", "SharedVersus")])
        standalone = field(
            "Warhead@CannonAP_Light_Percentage", "HealthPercentageDamage",
            [field("Damage", 40)])
        expect = {(pd.PCT_STANDALONE, "CannonAP_Light_Percentage"): 1}
        self.assertEqual(self.inventory(sabot, standalone), expect)
        self.assertEqual(self.modeled(sabot, standalone), expect)

    def test_unknown_heaviness_mode_fails_closed(self):
        bogus = field("Warhead@Main", "AreaDamage", [
            field("Damage", 3000), field("PercentageScale", 2000),
            field("HeavinessMode", "Bogus")])
        with self.assertRaisesRegex(ValueError, "Unknown HeavinessMode"):
            self.inventory(bogus)

    def test_shared_without_heaviness_fails_closed(self):
        omitted = field("Warhead@Main", "AreaDamage", [
            field("Damage", 3000), field("PercentageScale", 2000),
            field("HeavinessMode", "SharedVersus")])
        with self.assertRaisesRegex(eh.HeavinessError, "requires an active"):
            self.inventory(omitted)

    def test_shared_with_percentage_tables_fails_closed(self):
        mixed = self.shared(1000, field("PercentageVersus", children=[
            Node("None", "75", [])]))
        with self.assertRaisesRegex(eh.HeavinessError, "rejects"):
            self.inventory(mixed)

    def test_shared_on_the_area_damage_percentage_subclass_fails_closed(self):
        node = field("Warhead@Main", "AreaDamagePercentage", [
            field("Damage", 3000), field("PercentageScale", 2000),
            field("Heaviness", 0), field("HeavinessMode", "SharedVersus")])
        with self.assertRaisesRegex(eh.HeavinessError, "AreaDamagePercentage"):
            self.inventory(node)

    def test_zero_damage_does_not_hide_invalid_mode(self):
        node = self.shared(0)
        node.child("Damage").value = "0"
        node.child("HeavinessMode").value = "Bogus"
        with self.assertRaises(ValueError):
            self.inventory(node)

    def test_negative_damage_is_rejected_even_at_zero_heaviness(self):
        node = self.shared(0)
        node.child("Damage").value = "-1"
        with self.assertRaises(eh.HeavinessError):
            self.inventory(node)


if __name__ == "__main__":
    unittest.main()
