"""Keep both historical raw inventories while explaining their differences."""
import unittest
from types import SimpleNamespace
import _bootstrap  # noqa: F401
import audit_weapon_shape as shape
from miniyaml import Node


def wh(name, damage, kind="AreaDamage", relationships=None):
    children = [] if damage is None else [Node("Damage", str(damage))]
    if relationships:
        children.append(Node("ValidRelationships", relationships))
    return Node("Warhead@" + name, kind, children)


class ReconciliationTests(unittest.TestCase):
    def test_zero_healing_and_friendly_nodes_are_explained_not_hidden(self):
        weapons = {"zero": Node("zero", "", [wh("main", 100), wh("empty", 0)]),
                   "heal": Node("heal", "", [wh("one", -100), wh("two", -50)]),
                   "ally": Node("ally", "", [wh("main", 100), wh("ally", 50, relationships="Ally")]),
                   "both": Node("both", "", [wh("a", 100), wh("b", 100)])}
        rules = SimpleNamespace(weapons=weapons, resolve_weapon=weapons.get)
        result = shape.compare_split(rules)
        self.assertEqual((result["shape_count"], result["split_count"]), (4, 1))
        self.assertEqual(result["shape_only"], ["ally", "heal", "zero"])
        self.assertTrue(all(row["differing_nodes"] for row in result["differences"]))
        self.assertEqual(len(shape.resolved_mains(rules)), 4)

    def test_target_damage_difference_is_reported_in_reverse_direction(self):
        weapon = Node("target", "", [wh("flat", 100), wh("direct", 100, "TargetDamage")])
        rules = SimpleNamespace(weapons={"target": weapon}, resolve_weapon=lambda _: weapon)
        result = shape.compare_split(rules)
        self.assertEqual(result["split_only"], ["target"])
        self.assertEqual(result["differences"][0]["differing_nodes"][0]["reasons"],
                         ["type outside W5 flat-damage types"])

    def test_companion_twins_agree_and_templates_are_not_concrete(self):
        weapon = Node("one", "", [wh("main", 100), wh("mainExtraDamage", 50)])
        template = Node("^T", "", [wh("a", 100), wh("b", 100)])
        weapons = {"one": weapon, "^T": template}
        result = shape.compare_split(SimpleNamespace(weapons=weapons, resolve_weapon=weapons.get))
        self.assertEqual(result["differences"], [])
        self.assertEqual((result["shape_count"], result["split_count"]), (0, 0))
