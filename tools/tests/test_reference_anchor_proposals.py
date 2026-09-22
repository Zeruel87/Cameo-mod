"""Focused diagnostics for the unapproved reference-anchor proposal report."""
import contextlib
import copy
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import propose_reference_anchors as proposals  # noqa: E402


def fixture_result():
    dps = proposals.dps_diagnostics(500, 750, 500, 600)
    contributor = {
        "actor": "td_gdi_shocktrooper",
        "target": {"hp": 10000, "speed": 50, "w_range": 4000, "w_dps": 600, "cost": 500},
        "projected_inputs": [10000, 50, 4000, 600, 1, 1, 1],
        "template_class": "heavy_infantry",
        "explicit_class": "light_infantry",
        "explicit_class_tag": "light_infantry",
        "external_source_counts": {"hp": 3, "speed": 3, "w_range": 3, "w_dps": 3, "cost": 3},
        "dps_diagnostics": dps,
        "warnings": dps["warnings"] + ["EXPLICIT_CLASS_DISAGREES_WITH_TEMPLATE"],
        "explicit_template_disagreement": True,
        "candidate_price_at_projected_stats": 550,
        "relative_cost_residual": 0.1,
    }
    return {
        "schema": 1,
        "scope": "Unapproved nominal class-anchor proposals",
        "summary": {"classes": 1, "contributors": 1, "excluded": 0},
        "candidates": [{
            "class": "light_infantry",
            "status": "UNAPPROVED",
            "contributor_count": 1,
            "thin": True,
            "spec": {"hp0": 10000, "speed0": 50, "range0_wdist": 4000, "dps0": 600, "cost0": 500},
            "warning_summary": proposals.class_warning_summary([contributor], True),
            "contributors": [contributor],
        }],
    }


class DpsDiagnosticTests(unittest.TestCase):
    def test_one_mismatched_contributor_holds_every_row_using_the_fitted_class(self):
        clean = {"warnings": [], "relative_cost_residual": 0.1}
        bad = {"warnings": ["R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE"],
               "relative_cost_residual": 0.1}
        summary = proposals.class_warning_summary([clean, clean, bad], False)
        for row in (clean, bad):
            self.assertEqual(proposals.proposal_disposition(summary, row),
                             "HOLD_CLASS_DPS_METRIC_BASIS")

    def test_mismatch_preserves_each_basis_and_labels_ratios(self):
        result = proposals.dps_diagnostics(500, 750, 500, 600)
        self.assertEqual(result["frozen_r4_dps"], 500)
        self.assertEqual(result["current_r4_dps"], 750)
        self.assertEqual(result["current_fitting_dps"], 500)
        self.assertEqual(result["projected_dps"], 600)
        self.assertEqual(result["ratios"]["current_r4_over_frozen_r4"], 1.5)
        self.assertEqual(result["ratios"]["current_fitting_over_current_r4"], 2 / 3)
        self.assertTrue(result["mismatches"]["current_r4_vs_frozen_r4"])
        self.assertTrue(result["mismatches"]["current_r4_vs_current_fitting"])
        self.assertIn("R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE", result["warnings"])
        self.assertIn("UNAPPROVED", result["basis_warning"])

    def test_equal_dps_is_within_the_documented_tight_tolerance(self):
        result = proposals.dps_diagnostics(375, 375, 375, 375)
        self.assertEqual(result["mismatches"], {
            "current_r4_vs_frozen_r4": False,
            "current_r4_vs_current_fitting": False,
        })
        self.assertEqual(result["warnings"], [])
        self.assertEqual(result["ratios"]["projected_over_current_fitting"], 1.0)
        self.assertEqual(result["mismatch_tolerance"]["relative"], 1e-6)

    def test_missing_or_zero_dps_denominators_make_ratios_unavailable(self):
        result = proposals.dps_diagnostics(None, 0, 0, None)
        self.assertTrue(all(value is None for value in result["ratios"].values()))
        self.assertEqual(result["mismatches"]["current_r4_vs_frozen_r4"], None)
        self.assertIn("DPS_RATIO_UNAVAILABLE", result["warnings"])
        self.assertEqual(proposals.safe_ratio(0, 10), 0.0)
        self.assertIsNone(proposals.safe_ratio(10, 0))

    def test_per_unit_disposition_fails_closed_on_thin_or_mismatched_inputs(self):
        contributor = {"warnings": [], "relative_cost_residual": 0.1}
        self.assertEqual(
            proposals.proposal_disposition({"thin_cohort": True}, contributor),
            "HOLD_THIN_CLASS_COHORT",
        )
        contributor["warnings"] = ["R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE"]
        self.assertEqual(
            proposals.proposal_disposition({"thin_cohort": False}, contributor),
            "HOLD_DPS_METRIC_BASIS",
        )
        contributor["warnings"] = []
        self.assertEqual(
            proposals.proposal_disposition({"thin_cohort": False}, contributor),
            "REVIEWABLE_NO_AUTOMATIC_WRITE",
        )
        self.assertEqual(
            proposals.direction_summary({"hp": 100}, {"hp": 120})["hp"],
            "increase",
        )


class ReviewOutputTests(unittest.TestCase):
    def test_defenses_aircraft_and_harvesters_have_their_actual_model_routes(self):
        roster = {'defense': 'def', 'aircraft': 'air', 'harvester': 'veh'}
        units = {'defense': {'design': {'subtype': 'AntiAirDefense'}},
                 'aircraft': {'design': {'subtype': 'Bomber'}},
                 'harvester': {'design': {'subtype': 'Harvester'}}}
        rows = proposals.complete_roster_rows(roster, units, [], [])
        self.assertEqual({row['actor']: row['disposition'] for row in rows}, {
            'defense': 'STATIC_DEFENSE_MODEL_REQUIRED',
            'aircraft': 'AIR_OR_NAVAL_CLASS_DESIGN_REQUIRED',
            'harvester': 'ECONOMY_MANUAL_REVIEW',
        })

    def test_full_roster_keeps_omitted_units_and_distinct_pricing_exceptions(self):
        roster = {'hero': 'inf', 'transport': 'air', 'ship': 'nav',
                  'bunker': 'def', 'unmapped': 'veh', 'missing': 'veh'}
        base = {'hp': {'v': '100'}, 'cost': {'v': '200'}, 'design': {}}
        units = {name: copy.deepcopy(base) for name in roster if name != 'missing'}
        units['hero']['build_limit'] = {'v': '1'}
        for actor in ('transport', 'ship', 'bunker'):
            units[actor]['cargo_capacity'] = {'v': '4'}
        rows = proposals.complete_roster_rows(roster, units, [], [])
        by_actor = {row['actor']: row for row in rows}
        self.assertEqual(set(by_actor), set(roster))
        expected = {'hero': 'LIMITED_UNIT_SEPARATE_REVIEW',
                    'transport': 'CARGO_AWAITS_FINAL_PASSENGER_PRICES',
                    'ship': 'NAVAL_NO_INITIAL_LOAD',
                    'bunker': 'GARRISON_DEFENSE_SEPARATE_REVIEW',
                    'unmapped': 'CLASS_MEMBERSHIP_REQUIRED',
                    'missing': 'MISSING_LEDGER_ROW'}
        for actor, disposition in expected.items():
            self.assertEqual(by_actor[actor]['disposition'], disposition)
            self.assertIsNone(by_actor[actor]['target'])

    def test_class_summary_and_markdown_expose_warnings_without_mutating_values(self):
        result = fixture_result()
        before = copy.deepcopy(result)
        summary = result["candidates"][0]["warning_summary"]
        self.assertTrue(summary["thin_cohort"])
        self.assertEqual(summary["max_abs_cost_residual"], 0.1)
        self.assertEqual(summary["explicit_template_disagreements"], 1)
        self.assertIn("R4_VS_FITTING_MISMATCH_NOT_DIRECTLY_COMPARABLE",
                      summary["warning_counts"])
        self.assertIn("EXPLICIT_CLASS_DISAGREES_WITH_TEMPLATE", summary["warning_counts"])
        text = proposals.render_markdown(result)
        self.assertIn("frozen R4 DPS", text)
        self.assertIn("current fitting DPS", text)
        self.assertIn("THIN_COHORT", text)
        self.assertIn("Equal DPS does not prove full combat equivalence", text)
        self.assertEqual(result, before)

    def test_same_resolved_json_and_markdown_path_is_rejected_before_build(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            out = root / "review.json"
            alias = root / "nested" / ".." / "review.json"
            with patch.object(proposals, "build") as build, \
                    contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    proposals.main(["--out", str(out), "--markdown", str(alias)])
            build.assert_not_called()
            self.assertFalse(out.exists())

    def test_differing_existing_companion_blocks_the_whole_output_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            out = root / "review.json"
            markdown = root / "review.md"
            markdown.write_text("maintainer review\n", encoding="utf-8")
            with patch.object(proposals, "build", return_value=fixture_result()), \
                    contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    proposals.main(["--out", str(out), "--markdown", str(markdown)])
            self.assertFalse(out.exists())
            self.assertEqual(markdown.read_text(encoding="utf-8"), "maintainer review\n")

    def test_main_writes_json_and_optional_markdown_as_one_validated_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            out = root / "review.json"
            markdown = root / "review.md"
            with patch.object(proposals, "build", return_value=fixture_result()), \
                    contextlib.redirect_stdout(io.StringIO()):
                proposals.main(["--out", str(out), "--markdown", str(markdown)])
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["summary"]["classes"], 1)
            self.assertIn("# Reference anchor proposal review", markdown.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
