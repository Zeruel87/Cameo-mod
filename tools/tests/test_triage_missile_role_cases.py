import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "balance"))

from miniyaml import Node
import triage_missile_role_cases as triage


class FakeRules:
    def __init__(self, weapons, actors=None):
        self.weapons = weapons
        self.actors = actors or {}

    def weapon(self, name):
        return self.weapons.get(name)

    def resolve_weapon(self, name):
        return self.weapons.get(name)

    def resolve(self, name):
        return self.actors.get(name)

    def inherits_of(self, node):
        return [(c.key, c.value) for c in node.children if c.key == "Inherits" or c.key.startswith("Inherits@")]


class MissileRoleTriageTests(unittest.TestCase):
    def test_custom_bucket_preserves_naval_and_recipient_selectors(self):
        self.assertEqual(triage.custom_role_bucket("Water, Underwater, Bridge", None), "water-or-underwater")
        self.assertEqual(triage.custom_role_bucket("Ground, Ship, Garrisoned", None), "recipient-type-selector")
        self.assertEqual(triage.custom_role_bucket("Air", "Air"), "empty-after-invalid")

    def test_scan_records_strict_role_and_consumer(self):
        weapon = Node(
            "demo",
            "",
            [
                Node("ValidTargets", "Ground, Water"),
                Node("Warhead@MissileAP_Heavy", "AreaDamage"),
            ],
            "demo.yaml",
            10,
        )
        actor = Node("actor", "", [Node("Armament", "", [Node("Weapon", "demo", [], "actor.yaml", 4)])])
        receipt = triage.scan(FakeRules({"demo": weapon}, {"actor": actor}))
        row = receipt["strict_findings"]["R1"][0]
        self.assertEqual(row["expected"], "MissileHE")
        self.assertEqual(row["actor_consumers"][0]["actor"], "actor")
        self.assertEqual(row["review_status"], "REVIEW_REQUIRED")

    def test_inheritance_chain_is_document_ordered(self):
        parent = Node("parent", "", [], "parent.yaml", 1)
        child = Node("child", "", [Node("Inherits", "parent")], "child.yaml", 2)
        rules = FakeRules({"child": child, "parent": parent})
        self.assertEqual(triage.inheritance_chain(rules, "child"), ["parent"])


if __name__ == "__main__":
    unittest.main()
