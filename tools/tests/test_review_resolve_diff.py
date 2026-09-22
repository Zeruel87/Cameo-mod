import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from miniyaml import Node  # noqa: E402
from review_resolve_diff import ordered_warhead_differences  # noqa: E402


def warhead(key, kind, *fields):
    return Node(key, kind, [Node(name, value) for name, value in fields])


def weapon(*children):
    return Node("weapon", "", list(children))


class OrderedResolveDiffTests(unittest.TestCase):
    def test_identical_ordered_payload_passes(self):
        node = weapon(
            warhead("Warhead@Damage", "AreaDamage", ("Damage", "10")),
            warhead("Warhead@Owner", "ChangeOwner", ("Owner", "Neutral")),
        )
        self.assertEqual([], ordered_warhead_differences(node, node))

    def test_declared_key_rename_passes_without_payload_change(self):
        base = weapon(warhead("Warhead@Old", "AreaDamage", ("Damage", "10")))
        head = weapon(warhead("Warhead@New", "AreaDamage", ("Damage", "10")))
        self.assertEqual(
            [], ordered_warhead_differences(
                base, head, {"Warhead@Old": "Warhead@New"}))

    def test_declared_nested_key_rename_is_applied_to_complete_payload(self):
        base = weapon(Node(
            "Warhead@Outer", "AreaDamage",
            [Node("Warhead@Inner", "CreateEffect", [Node("Image", "fx")])]))
        head = weapon(Node(
            "Warhead@Outer", "AreaDamage",
            [Node("Warhead@InnerRenamed", "CreateEffect", [Node("Image", "fx")])]))
        self.assertEqual(
            [], ordered_warhead_differences(
                base, head, {"Warhead@Inner": "Warhead@InnerRenamed"}))

    def test_swapping_damage_and_owner_is_executable_order_failure(self):
        base = weapon(
            warhead("Warhead@Damage", "AreaDamage", ("Damage", "10")),
            warhead("Warhead@Owner", "ChangeOwner", ("Owner", "Neutral")),
        )
        head = weapon(
            warhead("Warhead@Owner", "ChangeOwner", ("Owner", "Neutral")),
            warhead("Warhead@Damage", "AreaDamage", ("Damage", "10")),
        )
        differences = ordered_warhead_differences(base, head)
        self.assertTrue(any("executable warhead order changed" in d for d in differences))

    def test_dropped_payload_field_is_not_hidden_by_key_equality(self):
        base = weapon(warhead(
            "Warhead@Damage", "AreaDamage", ("Damage", "10"), ("Spread", "50")))
        head = weapon(warhead("Warhead@Damage", "AreaDamage", ("Damage", "10")))
        differences = ordered_warhead_differences(base, head)
        self.assertTrue(any("warhead payload changed" in d for d in differences))

    def test_bare_warhead_payload_is_checked(self):
        base = weapon(Node("Warhead", "AreaDamage", [Node("Damage", "10")]))
        head = weapon(Node("Warhead", "AreaDamage", [Node("Damage", "99")]))
        differences = ordered_warhead_differences(base, head)
        self.assertTrue(any("warhead payload changed" in d for d in differences))

    def test_reordered_fields_are_reported_separately(self):
        base = weapon(warhead(
            "Warhead@Damage", "AreaDamage", ("Damage", "10"), ("Spread", "50")))
        head = weapon(warhead(
            "Warhead@Damage", "AreaDamage", ("Spread", "50"), ("Damage", "10")))
        differences = ordered_warhead_differences(base, head)
        self.assertTrue(any("field order changed" in d for d in differences))

    def test_ambiguous_rename_is_rejected(self):
        base = weapon(warhead("Warhead@One", "AreaDamage"))
        head = weapon(warhead("Warhead@Two", "AreaDamage"))
        with self.assertRaisesRegex(ValueError, "ambiguous rename target"):
            ordered_warhead_differences(
                base, head,
                {"Warhead@One": "Warhead@Two", "Warhead@Other": "Warhead@Two"})

    def test_non_warhead_rename_is_rejected(self):
        base = weapon(warhead("Warhead@One", "AreaDamage", ("Damage", "10")))
        head = weapon(warhead("Warhead@One", "AreaDamage", ("Damage", "99")))
        with self.assertRaisesRegex(ValueError, "warhead nodes"):
            ordered_warhead_differences(base, head, {"Damage": "Spread"})


if __name__ == "__main__":
    unittest.main()
