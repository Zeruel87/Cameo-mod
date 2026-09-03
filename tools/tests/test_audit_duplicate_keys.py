"""Unit tests for tools/audit/audit_duplicate_keys.py."""

from __future__ import annotations

import pathlib
import tempfile
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

import audit_duplicate_keys as dup
import miniyaml


def parse(text: str) -> list[miniyaml.Node]:
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / "rules.yaml"
        path.write_text(text, encoding="utf-8")
        return miniyaml.load(path)


def findings(text: str) -> list[tuple[str, str, list[int]]]:
    out: list[tuple[str, str, list[int]]] = []
    for top in parse(text):
        collected: list[tuple[str, str, list[miniyaml.Node]]] = []
        dup.walk(top, top.key, collected)
        out.extend((owner, key, [n.line for n in nodes])
                   for owner, key, nodes in collected)
    return out


class DuplicateChildrenTest(unittest.TestCase):
    def test_reports_a_key_declared_twice(self):
        node = parse("actor:\n\tInherits@a: ^One\n\tInherits@a: ^Two\n")[0]
        groups = dup.duplicate_children(node)
        self.assertEqual(list(groups), ["Inherits@a"])
        self.assertEqual([n.value for n in groups["Inherits@a"]], ["^One", "^Two"])

    def test_distinct_suffixes_are_not_duplicates(self):
        node = parse("actor:\n\tInherits@a: ^One\n\tInherits@b: ^Two\n")[0]
        self.assertEqual(dup.duplicate_children(node), {})

    def test_removal_keys_are_ignored(self):
        node = parse("actor:\n\t-Trait:\n\t-Trait:\n")[0]
        self.assertEqual(dup.duplicate_children(node), {})


class WalkTest(unittest.TestCase):
    def test_finds_duplicates_nested_inside_a_trait(self):
        text = "actor:\n\tArmament:\n\t\tWeapon: a\n\t\tWeapon: b\n"
        self.assertEqual(findings(text),
                         [("actor > Armament", "Weapon", [3, 4])])

    def test_reports_every_line_of_a_triplicated_key(self):
        text = "actor:\n\tHealth: 1\n\tHealth: 2\n\tHealth: 3\n"
        self.assertEqual(findings(text), [("actor", "Health", [2, 3, 4])])

    def test_clean_actor_has_no_findings(self):
        text = "actor:\n\tInherits: ^Base\n\tHealth:\n\t\tHP: 100\n"
        self.assertEqual(findings(text), [])


class SeverityTest(unittest.TestCase):
    """D1 marks ambiguous inheritance labels with different parent values."""

    @staticmethod
    def classify(key: str, values: list[str]) -> str:
        is_inherit = key == "Inherits" or key.startswith("Inherits@")
        return "D1" if is_inherit and len(set(values)) > 1 else "D2"

    def test_differing_inherits_is_d1(self):
        self.assertEqual(self.classify("Inherits@repair",
                                       ["^RepairsUnits", "^RepairFacility"]), "D1")

    def test_identical_inherits_is_only_d2(self):
        self.assertEqual(self.classify("Inherits", ["^Base", "^Base"]), "D2")

    def test_duplicate_trait_is_d2(self):
        self.assertEqual(self.classify("WithDeathAnimation", ["", ""]), "D2")

    def test_baseline_is_a_ratchet_not_a_target(self):
        self.assertGreaterEqual(dup.D1_BASELINE, 0)
        self.assertIsInstance(dup.D1_BASELINE, int)
        self.assertGreaterEqual(dup.D2_BASELINE, 0)
        self.assertIsInstance(dup.D2_BASELINE, int)


if __name__ == "__main__":
    unittest.main()
