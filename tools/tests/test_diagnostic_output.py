"""Read-only reports must never overwrite gameplay, ledgers or human reviews."""
import contextlib
import io
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/balance"))
import diagnostic_output as output
import derive_virtual_anchor as virtual
import anchor_readiness as readiness


class DiagnosticOutputTests(unittest.TestCase):
    def test_gameplay_and_ledger_destinations_refused(self):
        for path in ("mods/cameo/rules/test.json", "docs/balance/class_anchors.json",
                     "docs/balance/mbt.json", "tools/test.md", "out.json"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                output.validate_path(ROOT, ROOT / path)

    def test_diagnostic_folders_and_explicit_external_outputs_allowed(self):
        for path in ("docs/balance/anchors/mbt.json", "docs/audit/latest/readiness.json"):
            self.assertEqual(output.validate_path(ROOT, ROOT / path), (ROOT / path).resolve())
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory) / "out.json"
            self.assertEqual(output.validate_path(ROOT, target), target.resolve())

    def test_existing_different_file_refuses_entire_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            one, two = (pathlib.Path(directory) / name for name in ("one.md", "two.md"))
            two.write_text("human judgement", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "existing different"):
                output.write_outputs(ROOT, {one: "new", two: "replacement"})
            self.assertFalse(one.exists())
            self.assertEqual(two.read_text(), "human judgement")

    def test_identical_output_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory) / "out.json"
            output.write_outputs(ROOT, {target: '{"a":1}\n'})
            before = target.stat().st_mtime_ns
            output.write_outputs(ROOT, {target: '{"a":1}\n'})
            self.assertEqual(target.stat().st_mtime_ns, before)

    def test_aliases_cannot_hide_duplicate_destinations(self):
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory) / "out.json"
            alias = pathlib.Path(directory) / "sub/../out.json"
            with self.assertRaisesRegex(ValueError, "duplicate"):
                output.write_outputs(ROOT, {target: "one", alias: "two"})
            self.assertFalse(target.exists())

    def test_no_yaml_extension_even_outside_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                output.write_outputs(ROOT, {pathlib.Path(directory) / "file.yaml": "text"})

    def test_readiness_cli_refuses_registry_before_loading(self):
        with patch.object(sys, "argv", ["readiness", "--json", str(ROOT / "docs/balance/class_anchors.json")]), \
                patch.object(readiness, "load_units") as loader, \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            readiness.main()
        loader.assert_not_called()

    def test_virtual_cli_refuses_ledger_directory_before_loading(self):
        with patch.object(virtual, "load_evidence") as loader, \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            virtual.main(["--all", "--out", str(ROOT / "docs/balance")])
        loader.assert_not_called()


if __name__ == "__main__":
    unittest.main()
