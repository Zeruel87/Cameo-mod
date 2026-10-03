"""The reference holdout validator: leakage laws first, then bounded corpus behaviour.

Covers, per the suggestion-5 order: changing the withheld truth alone must not move the
prediction or the baseline (only the log-ratio moves), the withheld row and its expanded
family are excluded from every calibration population, the entire held-out source is
excluded from the voices, no Cameo self vote anywhere in the inputs, scale invariance of
the prediction, single-voice low-evidence classification, join and thin-population
refusals, nonfinite/bool/zero refusal, totals reconciliation, determinism, external-only
output with exclusive creation, and the fingerprint gate.

Synthetic corpora only — no real corpus is loaded and no pass threshold is applied.
"""
from __future__ import annotations

import hashlib
import math
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))
import validate_reference_holdout as vh                     # noqa: E402
import build_reference_report as brr                        # noqa: E402
import faction_extrapolate as fe                            # noqa: E402
import reference_targets as rt                              # noqa: E402
import reference_distribution as rd                          # noqa: E402


def row(source, rid, hp, speed=10.0, cost=500.0):
    return {"source": source, "id": rid, "name": rid, "type": "vehicle",
            "hp": hp, "speed": speed, "cost": cost}


def filler(source, scale=1.0, count=19, base=900.0, step=100.0):
    """Deterministic filler vehicle rows for one source, positive on every axis."""
    return [{"source": source, "id": f"{source}_U{i}", "name": f"{source} filler {i}",
             "type": "vehicle", "hp": (base + i * step) * scale,
             "speed": 9.0 + i, "cost": (90.0 + i) * scale}
            for i in range(count)]


def corpus(withheld_hp=1000.0, backdrop=(1.0, 10.0, 20.0),
           sources=("S1", "S2", "S3")):
    """Three assigned sources holding the same design at different fixed scales.

    The withheld hp moves ONLY the S1-held row: the partners' values stay fixed so a
    change of the withheld truth alone cannot alter any partner voice or any calibration
    population. Returns (rows, assignment_result, joined_pairs, families)."""
    rows = []
    assignment = {}
    for idx, source in enumerate(sources):
        k = backdrop[idx]
        held_id = f"W{idx + 1}"
        held_hp = withheld_hp if idx == 0 else 1000.0 * k
        rows.append(row(source, held_id, held_hp, speed=10.0, cost=500.0 * k))
        assignment[source] = {"id": held_id, "confidence": "STRONG"}
        rows += filler(source, scale=k)
    result = {"td_gdi_testtank": assignment}
    joined = fe.paired_rows(result, rows, diagnostics={})
    families = rt.expand_families({cid: list(srcs.values())
                                   for cid, srcs in joined.items()}, rows)
    return rows, result, joined, families


def doc_for(axes=vh.HOLDOUT_AXES):
    rows, result, joined, families = corpus()
    return vh.holdout(joined, families, rows, ["td_gdi_testtank"], axes=axes)


def record_for(doc, axis, held_source):
    for rec in doc["multi_source"] + doc["low_evidence"]:
        if rec["axis"] == axis and rec["held_source"] == held_source:
            return rec
    return None


class WithheldTruthTests(unittest.TestCase):
    def test_changing_withheld_truth_alone_does_not_move_the_prediction(self):
        doc_a = doc_for()
        rec_a = record_for(doc_a, "hp", "S1")
        rows_b, res_b, joined_b, fams_b = corpus(withheld_hp=7500.0)
        doc_b = vh.holdout(joined_b, fams_b, rows_b, ["td_gdi_testtank"],
                           axes=vh.HOLDOUT_AXES)
        rec_b = record_for(doc_b, "hp", "S1")
        self.assertIsNotNone(rec_a)
        self.assertIsNotNone(rec_b)
        self.assertEqual(rec_a["predicted"], rec_b["predicted"])
        self.assertEqual(rec_a["type_median_baseline"], rec_b["type_median_baseline"])
        self.assertNotEqual(rec_a["held_value"], rec_b["held_value"])
        self.assertNotEqual(rec_a["log_ratio"], rec_b["log_ratio"])

    def test_calibration_population_excludes_the_withheld_and_family_rows(self):
        rows, result, joined, families = corpus(withheld_hp=1000.0)
        cid = "td_gdi_testtank"
        calib_rows = vh.calibration_rows(rows, families[cid])
        self.assertNotIn(joined[cid]["S1"], calib_rows)
        self.assertNotIn(joined[cid]["S2"], calib_rows)
        s1_ids = {row["id"] for row in calib_rows if row["source"] == "S1"}
        self.assertNotIn("W1", s1_ids)
        self.assertEqual(len(s1_ids), 19)
        computed = vh.calibration_distribution(calib_rows)
        recomputed = rd.aggregates([row["hp"] for row in rows
                                    if row["source"] == "S1" and row["id"] != "W1"
                                    and rd.eligible(row, "hp")])
        # The withheld value itself is out of the calibration aggregates.
        self.assertEqual(computed["S1"]["vehicle"]["hp"], recomputed)


class VoiceExclusionTests(unittest.TestCase):
    def test_entire_held_out_source_excluded_from_voices(self):
        rows, result, joined, families = corpus(withheld_hp=1000.0)
        cid = "td_gdi_testtank"
        voices = vh.partner_rows(families[cid], "S1")
        self.assertTrue(voices)
        self.assertFalse([v for v in voices if v["source"] == "S1"])
        self.assertTrue(all(v["source"] in ("S2", "S3") for v in voices))

    def test_no_cameo_input_exists_in_the_trial_input(self):
        rows, result, joined, families = corpus(withheld_hp=1000.0)
        blob = repr(rows) + repr(result) + repr(joined) + repr(families)
        self.assertNotIn("Cameo", blob)
        self.assertNotIn("cameo", blob)


class EvidenceClassTests(unittest.TestCase):
    def test_two_remaining_voices_are_multi_source_diagnostics(self):
        doc = doc_for(axes=("hp", "speed", "cost"))
        for axis in ("hp", "speed", "cost"):
            for held_source in ("S1", "S2", "S3"):
                rec = record_for(doc, axis, held_source)
                self.assertIsNotNone(rec, axis)
                self.assertGreaterEqual(rec["voices"], 2, axis)
                self.assertLess(abs(rec["log_ratio"]), 0.05, axis)
        self.assertEqual(doc["totals"]["eligible"], 9)   # 3 holdouts x 3 axes

    def test_single_remaining_voice_is_low_evidence_not_multi_source(self):
        rows = [row("S1", "W1", 1000.0), row("S2", "W2", 10000.0)] \
            + filler("S1", 1.0) + filler("S2", 10.0, base=9000.0, step=1000.0)
        result = {"td_gdi_testtank": {"S1": {"id": "W1", "confidence": "STRONG"},
                                      "S2": {"id": "W2", "confidence": "STRONG"}}}
        joined = fe.paired_rows(result, rows, diagnostics={})
        families = rt.expand_families({cid: list(srcs.values())
                                       for cid, srcs in joined.items()}, rows)
        doc = vh.holdout(joined, families, rows, ["td_gdi_testtank"], axes=("hp",))
        self.assertEqual(doc["totals"]["eligible"], 2)
        self.assertFalse(doc["multi_source"])
        self.assertEqual(len(doc["low_evidence"]), 2)
        self.assertEqual(doc["low_evidence"][0]["voices"], 1)

    def test_no_remaining_voice_refused(self):
        rows = [row("S1", "W1", 1000.0)] + filler("S1", 1.0)
        result = {"td_gdi_testtank": {"S1": {"id": "W1", "confidence": "STRONG"}}}
        joined = fe.paired_rows(result, rows, diagnostics={})
        families = rt.expand_families({cid: list(voices.values())
                                       for cid, voices in joined.items()}, rows)
        doc = vh.holdout(joined, families, rows, ["td_gdi_testtank"], axes=("hp",))
        self.assertEqual(doc["totals"]["eligible"], 1)
        self.assertFalse(doc["multi_source"])
        self.assertFalse(doc["low_evidence"])
        self.assertEqual(doc["excluded_trials"][0]["reason"], "no_remaining_voice")


class JoinRefusalTests(unittest.TestCase):
    def test_ambiguous_join_never_becomes_a_trial(self):
        rows = [row("S1", "W1", 1000.0), row("S1", "W1", 1234.5)] \
            + filler("S1", 1.0) + filler("S2", 10.0, base=9000.0, step=1000.0)
        result = {"td_gdi_testtank": {"S1": {"id": "W1", "confidence": "STRONG"}}}
        diagnostics = {}
        joined = fe.paired_rows(result, rows, diagnostics=diagnostics)
        self.assertTrue(diagnostics.get("ambiguous_id"))
        families = rt.expand_families({cid: list(srcs.values())
                                       for cid, srcs in joined.items()}, rows)
        doc = vh.holdout(joined, families, rows, ["td_gdi_testtank"], axes=("hp",))
        self.assertEqual(doc["totals"]["eligible"], 0)
        self.assertFalse(doc["multi_source"])
        self.assertFalse(doc["low_evidence"])

    def test_join_refusals_are_reported(self):
        self.assertEqual(vh.join_summary({"missing_id": [1], "ambiguous_id": [1, 2]}),
                         {"ambiguous_id": 2, "missing_id": 1})


class ScaleInvarianceTests(unittest.TestCase):
    def test_scaling_a_whole_source_does_not_move_the_prediction(self):
        doc_a = doc_for()
        rec_a = record_for(doc_a, "hp", "S1")
        rows_b, res_b, joined_b, fams_b = corpus(
            withheld_hp=1000.0, backdrop=(1.0, 70.0, 20.0))
        doc_b = vh.holdout(joined_b, fams_b, rows_b, ["td_gdi_testtank"], axes=("hp",))
        rec_b = record_for(doc_b, "hp", "S1")
        self.assertIsNotNone(rec_a)
        self.assertIsNotNone(rec_b)
        self.assertAlmostEqual(rec_a["log_ratio"], rec_b["log_ratio"], delta=1e-9)
        self.assertAlmostEqual(rec_a["predicted"], rec_b["predicted"], delta=1e-6)


class ThinPopulationTests(unittest.TestCase):
    def test_thin_calibration_population_refused(self):
        rows = [row("S1", "W1", 1000.0)] + filler("S1", 1.0, count=3) \
            + [row("S2", "W2", 10000.0)] + filler("S2", 10.0, base=9000.0, step=1000.0)
        result = {"td_gdi_testtank": {"S1": {"id": "W1", "confidence": "STRONG"},
                                      "S2": {"id": "W2", "confidence": "STRONG"}}}
        joined = fe.paired_rows(result, rows, diagnostics={})
        families = rt.expand_families({cid: list(voices.values())
                                       for cid, voices in joined.items()}, rows)
        doc = vh.holdout(joined, families, rows, ["td_gdi_testtank"], axes=("hp",))
        self.assertFalse(doc["multi_source"])
        self.assertTrue(any(r["reason"].startswith("thin_population")
                            for r in doc["excluded_trials"]))

    def test_baseline_is_the_heldout_excluded_type_median(self):
        rows, result, joined, families = corpus(withheld_hp=1000.0)
        cid = "td_gdi_testtank"
        calib_rows = vh.calibration_rows(rows, families[cid])
        computed = vh.calibration_distribution(calib_rows)["S1"]["vehicle"]["hp"]["median"]
        doc = vh.holdout(joined, families, rows, ["td_gdi_testtank"], axes=("hp",))
        rec = record_for(doc, "hp", "S1")
        self.assertEqual(rec["type_median_baseline"], computed)


class TotalsReconciliationTests(unittest.TestCase):
    def test_eligible_equals_tested_plus_low_evidence_plus_excluded(self):
        doc = doc_for()
        totals = doc["totals"]
        self.assertEqual(totals["eligible"],
                         totals["tested"] + totals["held_low_evidence"]
                         + totals["excluded"])
        self.assertTrue(doc["reconciles"])


class DeterminismTests(unittest.TestCase):
    def test_repeated_runs_are_identical(self):
        self.assertEqual(doc_for(), doc_for())

    def test_actor_cap_is_clamped_deterministically(self):
        self.assertEqual(vh.clamp_actor_cap(0), 0)
        self.assertEqual(vh.clamp_actor_cap(7), 7)
        self.assertEqual(vh.clamp_actor_cap(999), vh.MAX_ACTOR_CAP)
        self.assertEqual(vh.clamp_actor_cap(-3), vh.DEFAULT_ACTOR_CAP)
        self.assertEqual(vh.clamp_actor_cap("junk"), vh.DEFAULT_ACTOR_CAP)


class ValueRefusalTests(unittest.TestCase):
    def test_nonfinite_bool_zero_negative_and_junk_withheld_values_refused(self):
        for bad in (float("nan"), float("inf"), float("-inf"), 0, -500.0, True,
                    False, "1000", None):
            with self.subTest(bad=bad):
                bad_row = row("S1", "W1", bad)
                rec, reason = vh.score_trial("cid", "S1", "hp", bad_row, [bad_row], {})
                self.assertIsNone(rec)
                self.assertEqual(reason, "invalid_withheld_value")


class OutputBoundaryTests(unittest.TestCase):
    def test_in_repository_output_directory_refused(self):
        with self.assertRaises(ValueError):
            vh.resolve_outputs(str(ROOT), "j", "m")

    def test_external_output_paths_accepted_and_differences_never_overwritten(self):
        import diagnostic_output
        with tempfile.TemporaryDirectory() as tmp:
            outside = pathlib.Path(tmp).resolve()
            outputs = vh.resolve_outputs(str(outside), '{"kind": "one"}', "# one")
            self.assertTrue(all(str(path).startswith(str(outside))
                                for path in outputs))
            diagnostic_output.write_outputs(ROOT, outputs)
            self.assertTrue(all(path.exists() for path in outputs))
            json_path = next(path for path in outputs if path.suffix == ".json")
            with self.assertRaises(ValueError):
                diagnostic_output.write_outputs(ROOT, {json_path: '{"kind": "two"}'})


class FingerprintGateTests(unittest.TestCase):
    def test_changed_fingerprints_refuse_the_evidence(self):
        vh.refuse_evidence_change({"a": "1"}, {"a": "1"})
        with self.assertRaises(ValueError):
            vh.refuse_evidence_change({"a": "1"}, {"a": "2"})


class RoundRobinTests(unittest.TestCase):
    RESULT_SOURCE = "OpenRA Tiberian Dawn"

    def fake_scope(self, per_faction=5):
        result = {}
        for i in range(per_faction):
            for faction in vh.CLASSIC_FACTIONS:
                result[f"{faction}_u{i}"] = {
                    self.RESULT_SOURCE: {"confidence": "STRONG"}}
        return result

    def test_round_robin_balances_all_factions_under_the_cap(self):
        with mock.patch.object(brr, "ORIGINAL_SOURCES", (self.RESULT_SOURCE,)):
            held, by_faction, excluded = vh.round_robin_actors(self.fake_scope(), 8)
        self.assertEqual(len(held), 8)
        self.assertEqual(by_faction, {f: 2 for f in vh.CLASSIC_FACTIONS})
        self.assertEqual(excluded, 12)
        # Not lexicographic: the first four come one from each faction, in declared order.
        self.assertEqual([vh.fr.faction_of(cid) for cid in held[:4]],
                         list(vh.CLASSIC_FACTIONS))

    def test_single_actor_factions_are_never_starved_by_a_big_one(self):
        result = {f"td_gdi_x{i}": {self.RESULT_SOURCE: {"confidence": "STRONG"}}
                  for i in range(10)}
        for faction in ("td_nod", "ra1_allies", "ra1_soviets"):
            result[f"{faction}_only"] = {self.RESULT_SOURCE: {"confidence": "STRONG"}}
        with mock.patch.object(brr, "ORIGINAL_SOURCES", (self.RESULT_SOURCE,)):
            held, by_faction, excluded = vh.round_robin_actors(result, 4)
        self.assertEqual(by_faction, {f: 1 for f in vh.CLASSIC_FACTIONS})
        self.assertEqual(excluded, 9)
        self.assertEqual([vh.fr.faction_of(cid) for cid in held],
                         list(vh.CLASSIC_FACTIONS))

    def test_cap_zero_selects_nothing_and_reports_everything_excluded(self):
        with mock.patch.object(brr, "ORIGINAL_SOURCES", (self.RESULT_SOURCE,)):
            held, by_faction, excluded = vh.round_robin_actors(self.fake_scope(), 0)
        self.assertEqual(held, [])
        self.assertEqual(by_faction, {})
        self.assertEqual(excluded, 20)


class CancelBiasTests(unittest.TestCase):
    def test_opposing_errors_cancel_bias_but_not_absolute_error(self):
        records = [
            {"axis": "hp", "log_ratio": 1.5, "abs_log_error": 1.5,
             "baseline_log_ratio": 0.0, "baseline_abs_log_error": 0.0},
            {"axis": "hp", "log_ratio": -1.5, "abs_log_error": 1.5,
             "baseline_log_ratio": 0.0, "baseline_abs_log_error": 0.0},
        ]
        summary = vh.axis_summary(records)
        self.assertEqual(summary["hp"]["median_log_ratio"], 0.0)   # bias is zero
        self.assertEqual(summary["hp"]["median_abs_log_error"], 1.5)  # typical error is not
        self.assertEqual(summary["hp"]["prediction_beats_baseline"], 0)


class LogErrorTests(unittest.TestCase):
    def test_log_error_survives_ratio_overflow_and_underflow_extremes(self):
        big, small = 1e308, 1e-308
        self.assertEqual(small / big, 0.0)             # the ratio underflows to zero
        overflow = vh.log_error(big, small)
        self.assertTrue(math.isfinite(overflow))
        self.assertAlmostEqual(overflow, math.log(big) - math.log(small))
        underflow = vh.log_error(small, big)
        self.assertTrue(math.isfinite(underflow))
        self.assertAlmostEqual(underflow, -(overflow))

    def test_score_trial_validates_prediction_and_baseline_before_scoring(self):
        def agg(median):
            return {"n": 20, "median": median, "am": median, "gm": median,
                    "min": 1.0, "max": 100.0, "p05": median / 2,
                    "p95": median * 1.5}
        family = [row("S1", "W1", 1000.0),
                  row("S2", "W2", 10000.0), row("S3", "W3", 20000.0)]
        alts = {"S2": {"overall": {"hp": agg(10000.0)}, "vehicle":
                       {"hp": agg(10000.0)}},
                "S3": {"overall": {"hp": agg(20000.0)}, "vehicle":
                       {"hp": agg(20000.0)}}}
        healthy = {"S1": {"overall": {"hp": agg(1000.0)}, "vehicle":
                          {"hp": agg(1000.0)}}, **alts}
        rec, reason = vh.score_trial("cid", "S1", "hp", family[0], family, healthy)
        self.assertIsNone(reason)
        self.assertAlmostEqual(rec["log_ratio"], 0.0, places=12)
        self.assertAlmostEqual(rec["abs_log_error"], 0.0, places=12)
        poisoned = {"S1": {"overall": {"hp": agg(1000.0)}, "vehicle":
                           {"hp": dict(agg(1000.0), median=float("inf"))}}, **alts}
        rec_bad, reason_bad = vh.score_trial("cid", "S1", "hp", family[0], family,
                                             poisoned)
        self.assertIsNone(rec_bad)
        self.assertEqual(reason_bad, "degenerate_prediction")
        rec_nan, reason_nan = vh.score_trial(
            "cid", "S1", "hp", family[0], family,
            {"S1": {"overall": {"hp": agg(1000.0)}, "vehicle":
                    {"hp": dict(agg(1000.0), median=float("nan"))}}, **alts})
        # The poisoned median leaves the prediction finite (middle three survive) but
        # invalidates the baseline — the scoring gate refuses it before scoring.
        self.assertIsNone(rec_nan)
        self.assertEqual(reason_nan, "degenerate_baseline")


class MissingCountTests(unittest.TestCase):
    def test_actual_missing_withheld_values_are_counted_not_guessed(self):
        rows = [row("S1", "W1", None), row("S2", "W2", 10000.0), row("S3", "W3", 20000.0)] \
            + filler("S1", 1.0) + filler("S2", 10.0, base=9000.0, step=1000.0) \
            + filler("S3", 20.0, base=18000.0, step=2000.0)
        result = {"td_gdi_testtank": {"S1": {"id": "W1", "confidence": "STRONG"},
                                      "S2": {"id": "W2", "confidence": "STRONG"},
                                      "S3": {"id": "W3", "confidence": "STRONG"}}}
        joined = fe.paired_rows(result, rows, diagnostics={})
        families = rt.expand_families({cid: list(srcs.values())
                                       for cid, srcs in joined.items()}, rows)
        doc = vh.holdout(joined, families, rows, ["td_gdi_testtank"], axes=("hp",))
        self.assertEqual(doc["withheld_missing"], {"S1": {"hp": 1}})
        self.assertEqual(doc["excluded_reasons"], {"invalid_withheld_value": 1})


class SelfFingerprintTests(unittest.TestCase):
    def test_self_fingerprint_covers_this_module_and_refuses_changes(self):
        expected = hashlib.sha256(
            pathlib.Path(vh.__file__).resolve().read_bytes()).hexdigest()
        self.assertEqual(vh.self_fingerprint(), expected)
        vh.refuse_evidence_change(
            {"validator_source": vh.self_fingerprint()},
            {"validator_source": vh.self_fingerprint()})
        with self.assertRaises(ValueError):
            vh.refuse_evidence_change(
                {"validator_source": "0" * 64},
                {"validator_source": vh.self_fingerprint()})


class ReportLabelTests(unittest.TestCase):
    def test_report_never_labels_results_calibrated(self):
        doc = doc_for()
        report = vh.render_report(doc)
        self.assertNotIn("alibrated", report)
        self.assertIn("## Tested multi-source diagnostics (>= 2 remaining voices)",
                      report)
        self.assertIn("tested (>= 2 voices)", report)

    def test_json_keys_use_multi_source_never_calibrated(self):
        doc = doc_for()
        self.assertIn("multi_source", doc)
        self.assertIn("multi_source_summary", doc)
        self.assertNotIn("calibrated", doc)
        self.assertNotIn("calibrated_summary", doc)

    def test_record_keys_keep_the_metric_names(self):
        doc = doc_for(("hp",))
        rec = doc["multi_source"][0]
        self.assertIn("log_ratio", rec)
        self.assertIn("abs_log_error", rec)


if __name__ == "__main__":
    unittest.main()
