"""Unit tests for tools/audit/miniyaml.py (the MiniYAML subset the audits rely on)."""

from __future__ import annotations

import pathlib
import tempfile
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

import miniyaml


def write(tmp: str, name: str, text: str) -> pathlib.Path:
    path = pathlib.Path(tmp) / name
    path.write_text(text, encoding="utf-8")
    return path


class LoadTest(unittest.TestCase):
    def test_archive_text_uses_same_parser_and_preserves_source(self):
        text = "\ufeffactor:\r\n\tTrait@one:\r\n\t\tField: 5 # note\r\n"
        parsed = miniyaml.load_text(text, "fixture.oramap/rules.yaml")
        with tempfile.TemporaryDirectory() as tmp:
            loaded = miniyaml.load(write(tmp, "rules.yaml", text))
        self.assertEqual(parsed[0].get("Trait@one", "Field"),
                         loaded[0].get("Trait@one", "Field"))
        self.assertEqual(parsed[0].children[0].children[0].line, 3)
        self.assertEqual(parsed[0].file, "fixture.oramap/rules.yaml")

    def test_parses_nesting_values_and_line_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "a.yaml",
                         "actor:\n\tTrait:\n\t\tField: 5\n\tOther: x\n")
            doc = miniyaml.load(path)

        self.assertEqual([n.key for n in doc], ["actor"])
        trait, other = doc[0].children
        self.assertEqual((trait.key, trait.value), ("Trait", ""))
        self.assertEqual((other.key, other.value), ("Other", "x"))
        self.assertEqual(trait.children[0].line, 3)
        self.assertEqual(doc[0].get("Trait", "Field"), "5")

    def test_strips_comments_but_keeps_escaped_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "a.yaml",
                         "# leading\nactor:\n\tName: Hi # trailing\n\tHash: a\\#b\n")
            doc = miniyaml.load(path)

        self.assertEqual(doc[0].get("Name"), "Hi")
        self.assertEqual(doc[0].get("Hash"), "a#b")

    def test_blank_lines_do_not_break_indentation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "a.yaml", "actor:\n\tA: 1\n\n\tB: 2\nother:\n\tC: 3\n")
            doc = miniyaml.load(path)

        self.assertEqual([n.key for n in doc], ["actor", "other"])
        self.assertEqual([c.key for c in doc[0].children], ["A", "B"])


class NodeTest(unittest.TestCase):
    def test_children_named_matches_suffixed_instances(self):
        node = miniyaml.Node("a", "", [
            miniyaml.Node("Armament", ""),
            miniyaml.Node("Armament@SECONDARY", ""),
            miniyaml.Node("ArmamentOther", ""),
        ])
        self.assertEqual([c.key for c in node.children_named("Armament")],
                         ["Armament", "Armament@SECONDARY"])

    def test_deep_copy_is_independent(self):
        node = miniyaml.Node("a", "", [miniyaml.Node("B", "1")])
        clone = node.deep_copy()
        clone.children[0].value = "2"
        self.assertEqual(node.children[0].value, "1")

    def test_get_returns_none_for_missing_path(self):
        node = miniyaml.Node("a", "", [miniyaml.Node("B", "", [])])
        self.assertIsNone(node.get("B", "C"))
        self.assertIsNone(node.get("Missing"))


class MergeTest(unittest.TestCase):
    def test_override_value_wins_and_new_keys_append(self):
        base = [miniyaml.Node("Trait", "", [miniyaml.Node("Field", "1")])]
        override = [miniyaml.Node("Trait", "", [miniyaml.Node("Field", "2"),
                                                miniyaml.Node("Extra", "x")]),
                    miniyaml.Node("New", "y")]
        merged = miniyaml.merge_children(base, override)

        self.assertEqual([n.key for n in merged], ["Trait", "New"])
        self.assertEqual(merged[0].get("Field"), "2")
        self.assertEqual(merged[0].get("Extra"), "x")

    def test_empty_override_value_keeps_the_base_value(self):
        base = [miniyaml.Node("Trait", "Explode")]
        merged = miniyaml.merge_children(base, [miniyaml.Node("Trait", "")])
        self.assertEqual(merged[0].value, "Explode")

    def test_removal_key_deletes_the_node(self):
        base = [miniyaml.Node("A", "1"), miniyaml.Node("B", "2")]
        merged = miniyaml.merge_children(base, [miniyaml.Node("-A", "")])
        self.assertEqual([n.key for n in merged], ["B"])

    def test_merge_does_not_mutate_the_source_lists(self):
        base = [miniyaml.Node("Trait", "", [miniyaml.Node("Field", "1")])]
        miniyaml.merge_children(base, [miniyaml.Node("Trait", "",
                                                     [miniyaml.Node("Field", "2")])])
        self.assertEqual(base[0].get("Field"), "1")


if __name__ == "__main__":
    unittest.main()
