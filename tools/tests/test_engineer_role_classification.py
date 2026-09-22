"""Recognize the explicit active D2K engineer role without guessing pack roles."""
import pathlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
sys.path.insert(0, str(ROOT / "tools/balance"))
from miniyaml import Node, Ruleset
import extract_stats as extract
import class_membership


class EngineerRoleTests(unittest.TestCase):
    def test_active_engineers_resolve_to_the_documented_support_role(self):
        rules = Ruleset(ROOT)
        for name in ("atreides_engineer", "corrino_engineer", "harkonnen_engineer"):
            with self.subTest(actor=name):
                subtype = extract.actor_subtype(rules, rules.actor(name), "infantry")
                self.assertEqual("EngineerInfantry", subtype)
                self.assertEqual(("support", "derived"), class_membership.classify({"subtype": subtype}))

    def test_inherited_pack_role_is_found_without_mutating_default_registry(self):
        nodes = {
            "unit": Node("unit", "", [Node("Inherits", "parent")]),
            "parent": Node("parent", "", [Node("Inherits@Template", "^EngineerInfantryTemplate")]),
            "^EngineerInfantryTemplate": Node("^EngineerInfantryTemplate", ""),
        }
        defaults = {}
        with patch.object(extract, "defaults_role_templates", return_value=defaults):
            self.assertEqual("EngineerInfantry", extract.actor_subtype(
                SimpleNamespace(actor=nodes.get), nodes["unit"], "infantry"))
        self.assertEqual({}, defaults)

    def test_missing_or_unrelated_pack_template_is_not_guessed(self):
        for role in ("^EngineerInfantryTemplate", "^ImaginaryInfantryTemplate"):
            nodes = {"unit": Node("unit", "", [Node("Inherits", role)])}
            if role.startswith("^Imaginary"):
                nodes[role] = Node(role, "")
            with self.subTest(role=role), patch.object(extract, "defaults_role_templates", return_value={}):
                self.assertEqual("Infantry", extract.actor_subtype(
                    SimpleNamespace(actor=nodes.get), nodes["unit"], "infantry"))


if __name__ == "__main__":
    unittest.main()
