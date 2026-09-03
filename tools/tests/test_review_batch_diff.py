"""Regression tests for the whole-tree weapon behavior comparator."""

from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

import review_batch_diff as review
from miniyaml import Node


def weapon(**overrides):
    value = {
        "damage": 1000,
        "percentage_damage": {20: 0, 200_000: 2000, 3_750_000: 37_500},
        "shape": ["100|-|-|-"],
        "valid_target_damage": (("Ground", 1000),),
        "invalid_target_damage": (("wall", 1000),),
        "relationship_stat_damage": ((('Enemy', True, 'Ground'), 1000),),
        "physical_state_bindings": (),
        "armor_profile": (("Main", 1000, (("Heavy", "100"),), ()),),
        "percentage_warheads": (),
        "Range": "5000",
        "ReloadDelay": "25",
        "Burst": None,
        "ValidTargets": "Ground",
        "InvalidTargets": "wall",
        "Report": "shot.aud",
        "StartBurstReport": None,
        "top_level": (("Range", "5000", ()),),
        "projectile": ("Projectile", "Bullet", ()),
        "non_damage_warheads": (),
    }
    value.update(overrides)
    return value


class ReviewBatchDiffTests(unittest.TestCase):
    def test_percentage_difference_at_non_reference_health_is_detected(self):
        before = weapon()
        after = weapon(percentage_damage={20: 0, 200_000: 2000, 3_750_000: -10})

        changed, removed, added = review.compare({"Gun": before}, {"Gun": after})

        self.assertEqual(removed, [])
        self.assertEqual(added, [])
        self.assertIn(["percentage_damage", [[3_750_000, 37_500, -10]]], changed["Gun"])

    def test_projectile_and_non_damage_changes_are_detected(self):
        before = weapon()
        after = weapon(
            projectile=("Projectile", "Bullet", (("Blockable", "true", ()),)),
            non_damage_warheads=(("Warhead@Effect", "CreateEffect", ()),),
        )

        changed, _, _ = review.compare({"Gun": before}, {"Gun": after})
        kinds = {finding[0] for finding in changed["Gun"]}

        self.assertIn("projectile", kinds)
        self.assertIn("non_damage_warheads", kinds)

    def test_damage_target_exclusion_change_is_detected(self):
        before = weapon()
        after = weapon(invalid_target_damage=())

        changed, _, _ = review.compare({"Gun": before}, {"Gun": after})

        self.assertIn("invalid_target_damage", {finding[0] for finding in changed["Gun"]})

    def test_relationship_and_statistics_accounting_change_is_detected(self):
        before = weapon()
        after = weapon(relationship_stat_damage=((('Enemy', False, 'Ground'), 1000),))

        changed, _, _ = review.compare({"Gun": before}, {"Gun": after})

        self.assertIn("relationship_stat_damage", {finding[0] for finding in changed["Gun"]})

    def test_physical_state_binding_change_is_detected(self):
        before = weapon(physical_state_bindings=((('Temperature', '100', 'AreaDamage', ('Ground',), ()), 1000),))
        after = weapon(physical_state_bindings=())

        changed, _, _ = review.compare({"Gun": before}, {"Gun": after})

        self.assertIn("physical_state_bindings", {finding[0] for finding in changed["Gun"]})

    def test_percentage_profile_change_is_detected_even_when_raw_hp_matches(self):
        before = weapon(percentage_warheads=(("AreaDamagePercentage", (("Spread", "75", ()),)),))
        after = weapon(percentage_warheads=(("AreaDamagePercentage", ()),))

        changed, _, _ = review.compare({"Gun": before}, {"Gun": after})

        self.assertIn("percentage_warheads", {finding[0] for finding in changed["Gun"]})

    def test_armor_profile_change_is_detected_even_when_total_matches(self):
        before = weapon()
        after = weapon(
            armor_profile=(("Main", 1000, (("Heavy", "125"),), ()),))

        changed, _, _ = review.compare({"Gun": before}, {"Gun": after})

        self.assertIn("armor_profile", {finding[0] for finding in changed["Gun"]})

    def test_omitted_physical_state_scale_is_disabled(self):
        omitted = Node("Warhead@Test", "AreaDamage", [Node("PhysicalStateName", "Temperature")])
        enabled = Node("Warhead@Test", "AreaDamage", [
            Node("PhysicalStateName", "Temperature"),
            Node("PhysicalStateScale", "100"),
        ])

        self.assertEqual((), review._physical_state_entries(omitted))
        self.assertEqual((("Temperature", "100"),), review._physical_state_entries(enabled))

    def test_physical_states_map_is_fingerprinted(self):
        mapped = Node("Warhead@Test", "AreaDamage", [
            Node("PhysicalStates", "", [
                Node("Corrosion", "100"),
                Node("Temperature", "0"),
            ]),
        ])

        self.assertEqual((("Corrosion", "100"),), review._physical_state_entries(mapped))


if __name__ == "__main__":
    unittest.main()
