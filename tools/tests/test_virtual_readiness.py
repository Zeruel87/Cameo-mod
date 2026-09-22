"""Virtual diagnostics must not silently turn current medians into approval."""
import contextlib
import copy
import io
import json
import math
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/balance"))
import anchor_readiness as readiness
import derive_virtual_anchor as virtual
import formula


def member(actor, hp=100000, cls="mbt"):
    unit = dict(hp={"v": hp}, speed={"v": 100}, cost={"v": 800},
                armaments=[dict(weapon="Gun", range=4000)])
    return dict(actor=actor, faction="tiberiandawn_gdi", cls=cls, unit=unit,
                **virtual.stat_values(unit))


class VirtualReadinessTests(unittest.TestCase):
    def test_same_derivation_and_ground_domain_signed_gap(self):
        members = [member("a"), member("b"), member("c")]
        live = copy.deepcopy(members[0]["unit"])
        live["hp"]["v"] = 50000
        live["armaments"].append(dict(weapon="Gun_AA", range=6000))
        anchors = {"mbt": dict(anchor_actor="a", signed_off=False)}
        before = copy.deepcopy(anchors)
        row = readiness.virtual_comparison(anchors, {"a": live}, members, {})[0]
        self.assertEqual(row["candidate"], virtual.derive("mbt", members, {}))
        self.assertEqual(row["comparison"]["hp"]["gap_pct"], -50)
        self.assertEqual(row["comparison"]["range_wdist"], dict(ledger=4000, virtual=4000, gap_pct=0))
        self.assertEqual(anchors, before)
        self.assertNotIn("dps0", json.dumps(row))
        self.assertNotIn("command", row["candidate"])
        self.assertIsNone(row["candidate"]["verifier"])

    def test_missing_anchor_and_no_source_are_not_zero_gap(self):
        rows = readiness.virtual_comparison({"dreadnought": {"anchor_actor": "absent"}}, {}, [], {})
        self.assertEqual(rows[0]["candidate"]["status"], ["NO SOURCE"])
        self.assertFalse(rows[0]["anchor_present"])
        self.assertTrue(all(c["gap_pct"] is None for c in rows[0]["comparison"].values()))
        text = io.StringIO()
        with contextlib.redirect_stdout(text):
            readiness.print_virtual_comparison(rows)
        self.assertIn("NO SOURCE", text.getvalue())
        self.assertIn("ANCHOR MISSING", text.getvalue())
        self.assertIn("unavailable", text.getvalue())

    def test_support_has_no_synthetic_range(self):
        source = member("engineer", cls="support")
        source["unit"]["armaments"] = []
        source.update(virtual.stat_values(source["unit"]))
        row = readiness.virtual_comparison({"support": {"anchor_actor": "engineer"}},
                {"engineer": source["unit"]}, [source], {})[0]
        self.assertIsNone(row["comparison"]["range_wdist"]["virtual"])
        self.assertIn("ABILITY PRICED — no combat verifier", row["candidate"]["status"])

    def test_missing_assignment_is_not_formula_only(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(OSError):
                virtual.load_evidence(pathlib.Path(directory))

    def test_evidence_mutation_is_rejected(self):
        with patch.object(virtual, "input_fingerprints", side_effect=[{}, {"changed": True}]), \
                patch.object(virtual, "load_members", return_value=[]):
            with self.assertRaisesRegex(ValueError, "changed during collection"):
                virtual.load_evidence(readiness.LEDGER)

    def test_cli_failure_is_visible_and_json_retains_old_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "out.json"
            output = io.StringIO()
            with patch.object(sys, "argv", ["readiness", "--json", str(path)]), \
                    patch.object(virtual, "load_evidence", side_effect=ValueError("bad assignment")), \
                    patch.object(readiness, "three_way_split_gate", return_value=(({}, {}), None)), \
                    contextlib.redirect_stdout(output):
                self.assertEqual(readiness.main(), 1)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(data["rows"])
            self.assertEqual(data["virtual_comparison"], [])
            self.assertIn("bad assignment", data["virtual_error"])
            self.assertIn("no virtual comparison", output.getvalue())

    def test_committed_cli_matches_direct_derivation_and_has_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "out.json"
            with patch.object(sys, "argv", ["readiness", "--json", str(path)]), \
                    patch.object(readiness, "three_way_split_gate", return_value=(({}, {}), None)), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(readiness.main(), 0)
            data = json.loads(path.read_text(encoding="utf-8"))
            members, assignments, provenance = virtual.load_evidence(readiness.LEDGER)
            self.assertEqual(data["virtual_provenance"], provenance)
            for row in data["virtual_comparison"]:
                self.assertEqual(row["candidate"], virtual.derive(row["cls"], members, assignments))
            self.assertIsNone(data["virtual_error"])
            # C5 correction: stored-fit evidence is additive JSON, schema-valid only.
            self.assertEqual(set(data["stored_fit"]),
                             {row["cls"] for row in data["virtual_comparison"]})
            self.assertTrue(all(
                ev.get("status") in ("complete", "absent", "partial", "invalid")
                and set(ev["fields"]) == set(readiness.FIT_FIELDS)
                for ev in data["stored_fit"].values()))


class StoredFitReportingTests(unittest.TestCase):
    """C5/C6 bounded reporting correction: classify STORED fit fields as they sit
    in the ledger; never present the legacy stored-value equality as the FINAL
    normalized identity test, a fresh fit of today's YAML, or a causal step-2c
    proof; nothing here approves or fails any class."""

    def evidence(self, **fields):
        return readiness.stored_fit_evidence(dict(fields))

    def test_all_fields_absent_is_classified_absent(self):
        ev = readiness.stored_fit_evidence({"spec": {"cost0": 800}})
        self.assertEqual(ev["status"], "absent")
        self.assertTrue(all(f["status"] == "absent" for f in ev["fields"].values()))
        self.assertFalse(ev["legacy_stored_equality"])
        self.assertEqual(readiness.stored_fit_reason(ev),
                         "stored fit absent: cost0, o0, p0, q0 absent or null")

    def test_partial_fields_classified_partial(self):
        ev = self.evidence(cost0=800, o0=920)
        self.assertEqual(ev["status"], "partial")
        self.assertEqual(ev["fields"]["cost0"]["status"], "present")
        self.assertEqual(ev["fields"]["p0"]["status"], "absent")
        self.assertFalse(ev["legacy_stored_equality"])
        self.assertEqual(readiness.stored_fit_reason(ev),
                         "stored fit partial: absent p0, q0")

    def test_invalid_nonfinite_bool_and_nonpositive_fields(self):
        for stored, reason in ((float("nan"), "nonfinite"), (float("inf"), "nonfinite"),
                               (float("-inf"), "nonfinite"), (True, "not-a-number"),
                               ("800", "not-a-number"), (0, "nonpositive"),
                               (-5, "nonpositive")):
            with self.subTest(stored=stored):
                ev = self.evidence(cost0=800, o0=920, p0=978, q0=stored)
                self.assertEqual(ev["status"], "invalid")
                self.assertEqual(ev["fields"]["q0"]["reason"], reason)
                self.assertEqual(ev["fields"]["q0"]["stored"],
                                 readiness._json_safe(stored))
        text = json.dumps(self.evidence(cost0=800, o0=920, p0=978, q0=float("nan")))
        self.assertNotIn("NaN", text)
        self.assertNotIn("Infinity", text)

    def test_complete_unequal_raw_fields_are_still_complete(self):
        ev = self.evidence(cost0=800, o0=946.79, p0=1093.58, q0=1387.16)
        self.assertEqual(ev["status"], "complete")
        self.assertTrue(all(f["status"] == "present" for f in ev["fields"].values()))
        self.assertFalse(ev["legacy_stored_equality"])

    def test_synthetic_counterexample_both_identities_hold(self):
        # A complete stored entry with unequal raw fields: the tuple's last bool is
        # False, yet both pricing identities hold exactly — so that bool proves
        # neither a failed baseline nor a failed fit.
        anchors = {"mbt": {"anchor_actor": "synthetic", "spec": {"cost0": 800},
                           "cost0": 800, "o0": 920.0, "p0": 978.0, "q0": 300.96}}
        row = readiness.anchor_actor_vs_spec(anchors, {})[0]
        self.assertFalse(row[7])
        self.assertEqual(readiness.stored_fit_evidence(anchors["mbt"])["status"],
                         "complete")
        # legacy raw-normalizer form: self-normalized, the unit prices at cost0
        self.assertAlmostEqual(formula.class_anchor_price(
            920.0, 978.0, 300.96, 920.0, 978.0, 300.96, 800), 800)
        # FINAL normalized form: o = p = q = cost0 exactly at its own baseline
        self.assertEqual(formula.class_baseline_estimators(
            240000, 95, 5500, 30, 240000, 95, 5500, 30, 800), (800, 800, 800))
        self.assertAlmostEqual(formula.class_baseline_price(
            240000, 95, 5500, 30, 240000, 95, 5500, 30, 800), 800)

    def test_report_wording_stays_measured_and_unapproved(self):
        spec_rows = [
            ("mbt", "synthetic", True, 800.0, 800, 1.0, [], False),
            ("support", "other", True, None, 500, None,
             ["hp unavailable (measured)"], False),
        ]
        fit_evidence = {
            "mbt": readiness.stored_fit_evidence(
                {"cost0": 800, "o0": 920, "p0": 978, "q0": 300.96}),
            "support": readiness.stored_fit_evidence({}),
        }
        text = io.StringIO()
        with contextlib.redirect_stdout(text):
            readiness.print_anchor_vs_spec(spec_rows, fit_evidence)
        out = text.getvalue()
        # corrected claims present
        self.assertIn("NOT the FINAL normalized identity check", out)
        self.assertIn("STORED ledger values from a prior fit run", out)
        self.assertIn("NOT freshly fitted from today's YAML", out)
        self.assertIn("not, by itself, proof that application-law step 2c never ran", out)
        self.assertIn("resolved dossier", out)
        self.assertIn("1 complete", out)
        self.assertIn("1 absent", out)
        self.assertIn("`support`: stored fit absent", out)
        # the raw-equality statistic is removed entirely; the disclaimer stands alone
        self.assertNotIn("satisfying the baseline identity", out)
        self.assertNotIn("legacy stored-value equality", out)
        self.assertIn("not scored here", out)
        self.assertIn("FINAL normalization comes from `spec.*`", out)
        self.assertIn("numerically complete legacy normalizer", out)
        self.assertIn("not evidence of freshness or approval", out)
        self.assertIn("why stored fit fields are unavailable", out)
        self.assertIn("absent or null", out)
        # measured comparisons preserved; no approval or failure verdict inferred
        self.assertIn("| unavailable | 500 |", out)
        lowered = out.lower()
        self.assertNotIn("approved", lowered)
        self.assertNotIn("sign-off ready", lowered)
        self.assertNotIn("failed", lowered)
