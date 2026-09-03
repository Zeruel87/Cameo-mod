import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from audit_three_way_split import main_warheads
from miniyaml import Node


def warhead(key, damage=None, kind="SpreadDamage", relationships=None):
    children = []
    if damage is not None:
        children.append(Node("Damage", str(damage)))
    if relationships is not None:
        children.append(Node("ValidRelationships", relationships))
    return Node(f"Warhead@{key}", kind, children)


class MainWarheadPredicateTests(unittest.TestCase):
    def test_only_positive_explicit_damage_is_a_main(self):
        resolved = Node("Weapon", "", [
            warhead("Missing"),
            warhead("Zero", 0),
            warhead("Healing", -100),
            warhead("Symbolic", "{damage}"),
            warhead("Live", 100),
        ])
        self.assertEqual(["Live"], main_warheads(resolved))

    def test_companions_and_friendly_fire_are_not_second_mains(self):
        resolved = Node("Weapon", "", [
            warhead("Main", 100),
            warhead("Main_Percentage", 5, "HealthPercentageDamage"),
            warhead("MainExtraDamage", 50),
            warhead("MainConcrete", 20),
            warhead("GrenadeFriendlyFire", 50),
            warhead("RelationshipTwin", 50, relationships="Ally"),
            warhead("Enemy", 100, relationships="Enemy"),
        ])
        self.assertEqual(["Main", "Enemy"], main_warheads(resolved))

    def test_non_damage_effect_is_not_a_main(self):
        resolved = Node("Weapon", "", [
            warhead("Main", 100),
            warhead("Effect", 100, "CreateEffect"),
        ])
        self.assertEqual(["Main"], main_warheads(resolved))


if __name__ == "__main__":
    unittest.main()
