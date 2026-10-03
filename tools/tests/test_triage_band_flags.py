"""Focused tests for review-only baseband flag classification."""
import copy
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import triage_band_flags as triage  # noqa: E402


def row(ratio=0.6, **overrides):
    value = {
        "actor": "unit",
        "class": "mbt",
        "ratio": ratio,
        "flagged": True,
        "class_source": "explicit",
        "signed_off": False,
        "band_exempt": False,
        "active_source_limitations": [],
        "inactive_variant_limitations": [],
        "actual_cost": "1000",
        "modeled_price": 600,
        "comparison_domain": "ground",
    }
    value.update(copy.deepcopy(overrides))
    return value


class TriageTests(unittest.TestCase):
    def test_hard_soft_and_high_thresholds_are_distinct(self):
        self.assertEqual(triage.classify_row(row(0.49))["band"], "HARD_LOW")
        self.assertEqual(triage.classify_row(row(0.50))["band"], "SOFT_LOW")
        self.assertEqual(triage.classify_row(row(3.5))["band"], "IN_BAND")
        self.assertEqual(triage.classify_row(row(3.51))["band"], "HARD_HIGH")

    def test_blockers_keep_derived_and_payload_scope_visible(self):
        result = triage.classify_row(row(
            0.6, class_source="derived",
            inactive_variant_limitations=["unmodeled_secondary_payload:FireShrapnel"]))
        self.assertEqual(result["review_lane"], "CLASS_MEMBERSHIP")
        self.assertIn("DERIVED_CLASS_MEMBERSHIP", result["reasons"])
        self.assertIn("INACTIVE_VARIANT_LIMITATION", result["reasons"])
        self.assertIn("CLASS_ANCHOR_NOT_SIGNED_OFF", result["reasons"])

    def test_active_source_limitation_takes_source_model_lane(self):
        result = triage.classify_row(row(0.8, active_source_limitations=["missing_curve"]))
        self.assertEqual(result["band"], "IN_BAND")
        self.assertEqual(result["review_lane"], "SOURCE_MODEL")
        self.assertEqual(result["decision"], "HOLD")

    def test_build_report_counts_only_flagged_rows_and_preserves_input(self):
        document = {"summary": {"band_flags": 1}, "rows": [row(0.4), row(1.0, flagged=False)]}
        before = copy.deepcopy(document)
        result = triage.build_report(document, input_path="band.json", input_sha256="abc")
        self.assertEqual(result["summary"]["input_rows"], 2)
        self.assertEqual(result["summary"]["flagged_rows"], 1)
        self.assertEqual(result["summary"]["band_counts"], {"HARD_LOW": 1})
        self.assertEqual(result["rows"][0]["decision"], "HOLD")
        self.assertEqual(document, before)

    def test_malformed_ratio_fails_closed(self):
        result = triage.classify_row(row("nan"))
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertEqual(result["review_lane"], "INPUT_SHAPE")
        self.assertEqual(result["decision"], "HOLD")


if __name__ == "__main__":
    unittest.main()
