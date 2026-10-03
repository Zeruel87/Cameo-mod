"""Focused fixtures for the engine-blocking inheritance audit."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from audit_duplicate_inherits import blocking  # noqa: E402


class Node:
    def __init__(self, name):
        self.name = name


class Ruleset:
    def __init__(self, parents):
        self.nodes = {name: Node(name) for name in parents}
        self.parents = parents

    def inherits_of(self, node):
        return [(f"Inherits@{i}", target)
                for i, target in enumerate(self.parents[node.name])]

    def lookup(self, name):
        return self.nodes.get(name)


def findings(parents):
    rules = Ruleset(parents)
    return blocking(rules, rules.lookup, ["Root"])


def test_sibling_diamond_is_legal():
    assert findings({"Root": ["Left", "Right"], "Left": ["Shared"],
                     "Right": ["Shared"], "Shared": []}) == []


def test_accumulated_parent_repeat_is_blocking():
    found = findings({"Root": ["Shared", "Base"], "Base": ["Shared"], "Shared": []})
    assert [(name, parent) for name, parent, _path in found] == [("Root", "Shared")]


def test_thin_alias_preserves_legal_paths():
    assert findings({"Root": ["Alias", "Base"], "Alias": ["Shared"],
                     "Base": ["Shared"], "Shared": []}) == []


if __name__ == "__main__":
    test_sibling_diamond_is_legal()
    test_accumulated_parent_repeat_is_blocking()
    test_thin_alias_preserves_legal_paths()
    print("duplicate-inheritance blocking fixtures: PASS")
