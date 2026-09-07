"""A failed drift command must not turn the documented zero-drift claim green."""
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
import audit_doc_claims as claims


class LedgerDriftMeasurementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snippet = next(row["measure"] for row in claims.load_registry(
            ROOT / "docs/audit/doc_claims.yaml") if row["id"] == "ledgers_drifted")

    def measure(self, output, exit_code):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            script = root / "tools/audit/audit_balance_drift.py"
            script.parent.mkdir(parents=True)
            script.write_text("import sys\nprint(" + repr(output) + ")\nsys.exit(" +
                              str(exit_code) + ")\n", encoding="utf-8")
            with patch.object(claims, "ROOT", root):
                return claims.measure(self.snippet)

    def test_real_clean_marker_returns_zero(self):
        self.assertEqual((0.0, ""), self.measure(
            "_clean_ — 33 ledgers match the live rules exactly.", 0))

    def test_positive_drift_preserves_count(self):
        self.assertEqual((7.0, ""), self.measure("**7 ledger(s) drifted** — details", 1))

    def test_failure_missing_or_contradictory_evidence_is_unavailable(self):
        clean = "_clean_ — 33 ledgers match the live rules exactly."
        drift = "**7 ledger(s) drifted** — details"
        cases = [("Traceback: crash", 1), ("", 0), ("unexpected", 0),
                 (clean, 1), (drift, 0), (drift, 2), (clean, 2),
                 (clean + "\n" + drift, 0), (clean + "\n" + drift, 1),
                 ("**0 ledger(s) drifted**", 1),
                 ("_clean_ — 0 ledgers match the live rules exactly.", 0),
                 (clean + "\n" + clean, 0), (drift + "\n" + drift, 1)]
        for output, code in cases:
            with self.subTest(output=output, code=code):
                value, error = self.measure(output, code)
                self.assertIsNone(value)
                self.assertIn("measurement unavailable", error)


if __name__ == "__main__":
    unittest.main()
