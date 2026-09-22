"""Preflight safety for the reusable classic-four materializer."""

from __future__ import annotations

import pathlib
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(ROOT / "tools" / "balance"))
import apply_harvester_durability as materializer  # noqa: E402


class _Child:
    def __init__(self, value):
        self.value = value

    def get(self, field):
        return self.value if field == "Cost" else None


class _Actor:
    def __init__(self, value):
        self.value = value

    def child(self, trait):
        return _Child(self.value) if trait == "Valued" else None


class _Rules:
    def __init__(self, values):
        self.values = values

    def resolve(self, actor):
        return _Actor(self.values[actor])


class ClassicFourMaterializerTests(unittest.TestCase):
    def test_inherited_baseline_refusal_leaves_every_file_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            first = root / "first.yaml"
            second = root / "second.yaml"
            first.write_bytes(b"actor_a:\n\tInherits: ^Template\n")
            second.write_bytes(b"actor_b:\n\tInherits: ^Template\n")
            specs = {
                "actor_a": (first, None, {"Valued": {"Cost": 2}}),
                "actor_b": (second, None, {"Valued": {"Cost": 4}}),
            }
            guards = {
                "actor_a": {"Valued.Cost": ("1", "2")},
                "actor_b": {"Valued.Cost": ("3", "4")},
            }
            old = {actor: {field: values[0] for field, values in fields.items()}
                   for actor, fields in guards.items()}
            before = {path: path.read_bytes() for path in (first, second)}
            # actor_a's inherited template was changed to an unapproved value;
            # actor_b is still valid.  Validation must reject the whole batch
            # before either actor gets a materialized child block.
            rules = _Rules({"actor_a": "9", "actor_b": "3"})
            with patch.object(materializer, "SPECS", specs), \
                    patch.object(materializer, "EXPECTED_RESOLVED", guards), \
                    patch.object(materializer, "EXPECTED_OLD", old), \
                    patch.object(materializer, "load_rules", return_value=rules):
                self.assertEqual(1, materializer.main())
            self.assertEqual(before, {path: path.read_bytes() for path in (first, second)})


if __name__ == "__main__":
    unittest.main()
