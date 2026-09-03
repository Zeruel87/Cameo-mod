"""Unit tests for tools/balance/check_determinism.py.

The failure mode for a determinism checker is that it always says PASS. It runs, it
looks green, and the property it claims to guard was never measured. So the tests here
are mostly about the machinery that decides FAIL, plus the two design choices the whole
thing rests on:

  * two SEPARATE processes with different `PYTHONHASHSEED`. Within one interpreter the
    seed is fixed, so set and dict iteration order is stable by accident and an
    ordering leak is invisible. One process = a checker that cannot fail.
  * nothing written under `docs/balance/`. A tool that verifies the ledgers must never
    be able to be the thing that moved them.
"""

from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

import _bootstrap  # noqa: F401 — sys.path side effect

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "balance"))
import check_determinism as cd  # noqa: E402


class Design(unittest.TestCase):
    def test_the_driver_never_writes_into_the_tracked_ledgers(self):
        # It dumps to $CAMEO_DUMP, a temp dir. If this ever gained a docs/balance
        # path the verifier could corrupt what it verifies.
        self.assertIn("CAMEO_DUMP", cd.DRIVER)
        self.assertNotIn("docs/balance", cd.DRIVER)
        self.assertNotIn("docs\\balance", cd.DRIVER)

    def test_the_driver_reuses_the_real_serializer(self):
        # Serialization must be inside what is tested, not beside it — otherwise a
        # change to how ledgers are written is invisible to the check.
        self.assertIn("es.serialize", cd.DRIVER)
        self.assertIn("build_both", cd.DRIVER)

    def test_it_covers_raw_derived_and_model(self):
        for prefix in ("raw__", "derived__", "model___model"):
            self.assertIn(prefix, cd.DRIVER)


class FirstDifference(unittest.TestCase):
    """The report has to name a line. 'Hashes differ' sends someone hunting."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())

    def write(self, name, text):
        p = self.tmp / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_names_the_first_differing_line(self):
        a = self.write("a", "same\nsame\nALPHA\nsame\n")
        b = self.write("b", "same\nsame\nBRAVO\nsame\n")
        out = cd.first_difference(a, b)
        self.assertIn("line 3", out)
        self.assertIn("ALPHA", out)
        self.assertIn("BRAVO", out)

    def test_reports_a_length_difference_when_the_prefix_matches(self):
        a = self.write("a", "one\ntwo\n")
        b = self.write("b", "one\ntwo\nthree\n")
        out = cd.first_difference(a, b)
        self.assertIn("lengths differ", out)
        self.assertIn("2", out)
        self.assertIn("3", out)

    def test_byte_difference_with_no_differing_line(self):
        # Trailing-newline / line-ending differences produce equal splitlines().
        a = self.write("a", "one\ntwo\n")
        b = self.write("b", "one\ntwo")
        self.assertIn("bytes differ", cd.first_difference(a, b))

    def test_identical_files_have_equal_digests(self):
        a = self.write("a", "identical\n")
        b = self.write("b", "identical\n")
        self.assertEqual(cd.digest(a), cd.digest(b))

    def test_different_files_have_different_digests(self):
        a = self.write("a", "left\n")
        b = self.write("b", "right\n")
        self.assertNotEqual(cd.digest(a), cd.digest(b))


class SeedVariation(unittest.TestCase):
    """The seeds must actually differ, or the check is theatre."""

    def test_the_two_documented_runs_use_different_seeds_and_zones(self):
        src = pathlib.Path(cd.__file__).read_text(encoding="utf-8")
        self.assertIn('one_run(a, "0", "UTC"', src)
        # Any second seed is fine; it must not be 0, and the zone must not be UTC.
        self.assertRegex(src, r'one_run\(b, "(?!0")\d+", "(?!UTC")[\w/]+"')

    def test_a_run_pins_the_environment_it_claims_to_pin(self):
        import inspect
        src = inspect.getsource(cd.one_run)
        for key in ("PYTHONHASHSEED", "TZ", "LC_ALL", "PYTHONIOENCODING"):
            self.assertIn(key, src)

    def test_a_failed_extraction_is_not_reported_as_determinism(self):
        # If extraction itself breaks, saying "not reproducible" would be a lie about
        # which property failed.
        import inspect
        src = inspect.getsource(cd.one_run)
        self.assertIn("extraction failed", src)


if __name__ == "__main__":
    unittest.main()
