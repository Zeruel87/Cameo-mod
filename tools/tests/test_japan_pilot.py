"""The Japan reference pilot: pure pooling laws plus a bounded real-corpus integration.

Covers, per the pilot order: invalid bool/nonfinite/zero numbers, the pool thresholds,
the no-Japan-donor law, per-axis missing values, the current/pending overlay, no-class
holds, deterministic output, and the external-only output refusal.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))
import build_japan_pilot as jp   # noqa: E402
import diagnostic_output        # noqa: E402
import faction_extrapolate as fe  # noqa: E402
import faction_routes as fr     # noqa: E402
import reference_distribution as rd  # noqa: E402
import reference_targets as rt  # noqa: E402
import class_membership as cm   # noqa: E402
import build_reference_report as brr  # noqa: E402


def fam(src, rid, **vals):
    row = {"source": src, "id": rid, "hp": None, "speed": None,
           "w_range": None, "cost": None}
    row.update(vals)
    return row


def donor(actor="td_gdi_mammothtank", faction="td_gdi", current=100.0, target=200.0, n=2,
          rows=None):
    return {"actor": actor, "faction": faction,
            "current": {"hp": current, "speed": 10.0, "w_range": 5000.0, "cost": 900.0},
            "target": {"hp": target, "speed": 20.0, "w_range": 6000.0, "cost": 1100.0},
            "n_sources": {"hp": n, "speed": n, "w_range": n, "cost": n},
            "family_rows": rows if rows is not None else
            [fam("Combined Arms", "HTNK", hp=1000.0, speed=50.0,
                 w_range=5000.0, cost=800.0)]}


class NumberTests(unittest.TestCase):
    def test_rejects_bool_nonfinite_zero_negative_and_junk(self):
        for bad in (True, False, float("inf"), float("-inf"), float("nan"),
                    0, 0.0, -1, -1.5, "100", None, [1], {}):
            with self.subTest(bad=bad):
                self.assertIsNone(jp.number(bad))

    def test_accepts_finite_positive_int_and_float(self):
        self.assertEqual(jp.number(3), 3.0)
        self.assertEqual(jp.number(2.5), 2.5)


class DonorEligibilityTests(unittest.TestCase):
    def test_japan_donor_refused(self):
        self.assertEqual(jp.donor_rejection("japan_samurai", "japan", "melee", None),
                         "japan_donor")

    def test_no_class_and_support_refused(self):
        self.assertEqual(jp.donor_rejection("a", "td_gdi", None, None), "no_class")
        self.assertEqual(jp.donor_rejection("a", "td_gdi", "support", None), "support_class")

    def test_pending_reclass_refused(self):
        self.assertEqual(jp.donor_rejection("a", "td_nod", "mbt", "armed_troop_transport"),
                         "pending_reclass")
        self.assertEqual(jp.donor_rejection("a", "td_nod", "mbt", "light_tank?"),
                         "pending_reclass")

    def test_in_scope_donor_passes(self):
        for faction in jp.CLASSIC_FACTIONS:
            with self.subTest(faction=faction):
                self.assertIsNone(jp.donor_rejection("a", faction, "mbt", None))

    def test_out_of_scope_faction_refused(self):
        self.assertEqual(jp.donor_rejection("a", "ts_gdi", "mbt", None), "faction_out_of_scope")


class CandidateTests(unittest.TestCase):
    def test_invalid_bool_current_skipped(self):
        d = donor(current=True)
        candidates, skipped = jp.collect_axis_candidates([d], "hp")
        self.assertEqual(candidates, [])
        self.assertEqual(skipped, [{"actor": d["actor"], "reason": "invalid_current"}])

    def test_nonfinite_and_zero_targets_skipped(self):
        for bad in (float("nan"), float("inf"), 0.0, -5.0):
            with self.subTest(bad=bad):
                candidates, skipped = jp.collect_axis_candidates([donor(target=bad)], "hp")
                self.assertEqual(candidates, [])
                self.assertEqual(skipped[0]["reason"], "invalid_target")

    def test_per_axis_missing_never_leaks_across_axes(self):
        d = donor()
        del d["current"]["hp"]
        d["target"]["hp"] = None
        hp_candidates, hp_skipped = jp.collect_axis_candidates([d], "hp")
        speed_candidates, speed_skipped = jp.collect_axis_candidates([d], "speed")
        self.assertEqual(hp_candidates, [])
        self.assertEqual(hp_skipped[0]["reason"], "no_reference_target")
        self.assertEqual(len(speed_candidates), 1)
        self.assertEqual(speed_skipped, [])

    def test_source_floor_refuses_one_source(self):
        candidates, skipped = jp.collect_axis_candidates([donor(n=1)], "hp")
        self.assertEqual(candidates, [])
        self.assertEqual(skipped, [{"actor": donor()["actor"], "reason": "thin_sources",
                                    "n_sources": 1}])

    def test_floor_met_yields_ratio(self):
        candidates, skipped = jp.collect_axis_candidates([donor()], "hp")
        self.assertEqual(skipped, [])
        self.assertEqual(len(candidates), 1)
        self.assertAlmostEqual(candidates[0]["ratio"], 2.0)
        self.assertEqual(candidates[0]["n_sources"], 2)


class PoolTests(unittest.TestCase):
    @staticmethod
    def pool(actors):
        return jp.pool_status([{"actor": a, "faction": "td_gdi", "ratio": 1.0, "n_sources": 2}
                               for a in actors])

    def test_fewer_than_three_donors_is_thin(self):
        state = self.pool(("a", "b"))
        self.assertEqual(state["status"], "THIN")
        self.assertIsNone(state["ratio"])

    def test_three_donors_one_faction_is_thin(self):
        candidates = [{"actor": a, "faction": "td_gdi", "ratio": 1.0, "n_sources": 2}
                      for a in ("a", "b", "c")]
        state = jp.pool_status(candidates)
        self.assertEqual(state["status"], "THIN")

    def test_thresholds_met_gives_geometric_mean(self):
        candidates = [{"actor": a, "faction": f, "ratio": r, "n_sources": 2}
                      for a, f, r in (("a", "td_gdi", 1.0), ("b", "td_gdi", 2.0),
                                      ("c", "td_nod", 4.0))]
        state = jp.pool_status(candidates)
        self.assertEqual(state["status"], "OK")
        self.assertAlmostEqual(state["ratio"], 2.0, delta=1e-9)
        self.assertEqual(state["donor_count"], 3)
        self.assertEqual(state["faction_count"], 2)


class SubjectStateTests(unittest.TestCase):
    def test_no_class_holds_every_axis(self):
        state = jp.subject_axis_state(None, None, 100.0, {"status": "OK", "ratio": 2.0})
        self.assertEqual(state, {"status": "NO_CLASS", "value": None})

    def test_pending_reclass_holds(self):
        state = jp.subject_axis_state("melee", "armed_troop_transport", 100.0,
                                      {"status": "OK", "ratio": 2.0})
        self.assertEqual(state["status"], "PENDING")
        self.assertIsNone(state["value"])

    def test_missing_current_holds(self):
        state = jp.subject_axis_state("mbt", None, None, {"status": "OK", "ratio": 2.0})
        self.assertEqual(state["status"], "MISSING_CURRENT")

    def test_thin_pool_holds(self):
        state = jp.subject_axis_state("mbt", None, 100.0, {"status": "THIN", "ratio": None})
        self.assertEqual(state["status"], "THIN")
        self.assertIsNone(state["value"])

    def test_ok_pool_applies_unapproved_sensitivity(self):
        state = jp.subject_axis_state("mbt", None, 300.0, {"status": "OK", "ratio": 1.25})
        self.assertEqual(state["status"], "UNAPPROVED")
        self.assertAlmostEqual(jp.sensitivity(300.0, 1.25), 375.0)
        self.assertAlmostEqual(state["value"], 375.0)


class OutputRefusalTests(unittest.TestCase):
    def test_in_repository_destinations_refused(self):
        for path in (ROOT, ROOT / "docs/audit/latest", ROOT / "docs/balance",
                     ROOT / "tools", ROOT / "docs"):
            with self.subTest(path=str(path)):
                with self.assertRaisesRegex(ValueError, "external output directory only"):
                    jp.resolve_outputs(ROOT, path, "{}", "# x\n")

    def test_external_directory_accepted_with_exact_names(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = jp.resolve_outputs(ROOT, directory, "{}", "# x\n")
            self.assertEqual(sorted(p.name for p in paths),
                             ["japan_reference_pilot.json", "japan_reference_pilot.md"])
            self.assertTrue(all(not p.is_relative_to(ROOT) for p in paths))

    def test_non_json_md_suffix_refused_even_external(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "pilot.yaml"
            with self.assertRaises(ValueError):
                diagnostic_output.validate_path(ROOT, path)

    def test_existing_different_file_refuses_the_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory) / "japan_reference_pilot.md"
            target.write_text("a human review", encoding="utf-8")
            paths = jp.resolve_outputs(ROOT, directory, "{}\n", "# different\n")
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                diagnostic_output.write_outputs(ROOT, paths)
            self.assertEqual(target.read_text(encoding="utf-8"), "a human review")


class DeterminismTests(unittest.TestCase):
    def doc(self):
        return {"artifact": jp.OUT_BASENAME, "unapproved": True,
                "scope": {"subjects": 2, "classic_factions": list(jp.CLASSIC_FACTIONS),
                          "subject_faction": "japan", "donors_considered": 1,
                          "subject_classes": ["melee"], "donor_exclusions": {},
                          "sensitivity_status_counts": {"hp": {"THIN": 1}, "speed": {},
                                                        "w_range": {}}},
                "japan_rows": [{"actor": "japan_samurai", "class": "melee",
                                "pending_class": None, "type": "infantry",
                                "axes": {
                                    "hp": {"current": 100.0, "r4_target": 150.0,
                                           "r4_n_sources": 2, "pool": "melee",
                                           "sensitivity": {"status": "THIN", "value": None,
                                                           "hold": True}},
                                    "speed": {"current": 90.0, "r4_target": 80.0,
                                              "r4_n_sources": 2, "pool": "melee",
                                              "sensitivity": {"status": "UNAPPROVED",
                                                              "value": 90000.0, "hold": False}},
                                    "w_range": {"current": 5000.0, "r4_target": None,
                                                "r4_n_sources": 0, "pool": "melee",
                                                "sensitivity": {"status": "THIN",
                                                                "value": None, "hold": True}},
                                    "cost": {"current": 800.0, "r4_target": 1000.0,
                                             "r4_n_sources": 2, "pool": None}},
                                "sources": [], "joined_reference_ids": {}}],
                "class_ratio_pools": {}, "donors": [], "join_diagnostics": {"joined": 4},
                "thresholds": {"min_distinct_donors": 3, "min_donor_factions": 2,
                               "min_sources_per_axis": 2, "apply_axes": list(jp.APPLY_AXES),
                               "report_axes": list(jp.AXES)},
                "input_fingerprints": {"a.json": "0" * 64},
                "pending_overlay": {"state": "NOT_CHECKED", "actors": None},
                "limitations": list(jp.LIMITATIONS), "method": "m"}

    def test_report_is_byte_identical_across_calls(self):
        doc = self.doc()
        first = hashlib.sha256(jp.render_report(doc).encode("utf-8")).hexdigest()
        second = hashlib.sha256(jp.render_report(doc).encode("utf-8")).hexdigest()
        self.assertEqual(first, second)

    def test_json_payload_is_sorted_and_nan_free(self):
        doc = self.doc()
        doc["japan_rows"][0]["axes"]["hp"]["r4_target"] = float("nan")
        with self.assertRaises(ValueError):
            json.dumps(doc, allow_nan=False)


class DuplicateVoteTests(unittest.TestCase):
    def test_same_actor_twice_casts_one_vote(self):
        d = donor()
        candidates, skipped = jp.collect_axis_candidates([d, dict(d)], "hp")
        self.assertEqual(len(candidates), 1)
        self.assertEqual(skipped, [{"actor": d["actor"], "reason": "duplicate_actor"}])

    def test_two_donors_sharing_a_contributing_family_row_cast_one_vote(self):
        shared = [fam("Combined Arms", "HTNK", hp=1000.0)]
        first = donor("td_gdi_mammothtank", rows=[shared[0]])
        second = donor("td_gdi_mammothtankmkii", target=180.0,
                       rows=[fam("Combined Arms", "HTNK.Ion", hp=900.0), shared[0]])
        candidates, skipped = jp.collect_axis_candidates([first, second], "hp")
        self.assertEqual([c["actor"] for c in candidates], ["td_gdi_mammothtank"])
        self.assertEqual(skipped, [{"actor": second["actor"],
                                    "reason": "duplicate_reference_vote",
                                    "shared": ["Combined Arms:HTNK"]}])

    def test_overlapping_expanded_family_blocked_even_on_different_joined_ids(self):
        # Both donors joined different ids, but their EXPANDED families share one row
        # with a value on this axis: one reference evidence, one vote.
        first = donor("td_gdi_mammothtank",
                      rows=[fam("Combined Arms", "HTNK", hp=1000.0, cost=800.0),
                            fam("Combined Arms", "HTNK.Ion", hp=900.0, cost=780.0)])
        second = donor("td_gdi_hovermammoth", faction="td_gdi",
                       rows=[fam("Combined Arms", "HTNK.Drone", hp=950.0, cost=790.0),
                             fam("Combined Arms", "HTNK.Ion", hp=900.0, cost=780.0)])
        candidates, skipped = jp.collect_axis_candidates([first, second], "hp")
        self.assertEqual([c["actor"] for c in candidates], ["td_gdi_mammothtank"])
        self.assertEqual(skipped[0]["reason"], "duplicate_reference_vote")
        self.assertEqual(skipped[0]["shared"], ["Combined Arms:HTNK.Ion"])

    def test_row_missing_this_axis_reserves_no_vote(self):
        # Donor A's PTNK row carries no hp: on the hp axis it is NOT a contributing
        # reference, so donor B (which does have hp from PTNK) is not blocked by it —
        # while on the speed axis the same two rows DO collide.
        a_rows = [fam("Combined Arms", "HTNK", hp=1000.0, speed=None),
                  fam("Combined Arms", "PTNK", hp=None, speed=60.0)]
        b_rows = [fam("Combined Arms", "PTNK", hp=400.0, speed=45.0),
                  fam("Combined Arms", "XTNK", hp=50.0, speed=40.0)]
        first = donor("a", rows=a_rows)
        second = donor("b", faction="td_nod", target=150.0, rows=b_rows)
        hp_candidates, hp_skipped = jp.collect_axis_candidates([first, second], "hp")
        speed_candidates, speed_skipped = jp.collect_axis_candidates([first, second], "speed")
        self.assertEqual([c["actor"] for c in hp_candidates], ["a", "b"])
        self.assertEqual(hp_skipped, [])
        self.assertEqual([c["actor"] for c in speed_candidates], ["a"])
        self.assertEqual(speed_skipped, [{"actor": "b", "reason": "duplicate_reference_vote",
                                          "shared": ["Combined Arms:PTNK"]}])

    def test_distinct_references_from_one_source_both_vote(self):
        first = donor("a", rows=[fam("Combined Arms", "HTNK", hp=1000.0)])
        second = donor("b", faction="td_nod", target=150.0,
                       rows=[fam("Combined Arms", "PTNK", hp=700.0)])
        candidates, skipped = jp.collect_axis_candidates([first, second], "hp")
        self.assertEqual(skipped, [])
        self.assertEqual(len(candidates), 2)

    def test_donors_without_family_rows_are_not_blocked(self):
        candidates, skipped = jp.collect_axis_candidates(
            [donor("a", rows=[]), donor("b", rows=[])], "hp")
        self.assertEqual(skipped, [])
        self.assertEqual(len(candidates), 2)


class NotCheckedTests(unittest.TestCase):
    def test_not_checked_is_not_a_pending_hold(self):
        state = jp.subject_axis_state("mbt", jp.NOT_CHECKED, 100.0,
                                      {"status": "OK", "ratio": 2.0})
        self.assertEqual(state["status"], "UNAPPROVED")
        self.assertAlmostEqual(state["value"], 200.0)


class InputFingerprintTests(unittest.TestCase):
    def test_every_consumed_input_exists_repo_relative(self):
        fps = jp.input_fingerprints()
        root = pathlib.Path(jp.ROOT)
        self.assertGreater(len(fps), len(jp.PROVENANCE_DATA))  # ledgers and live YAML joined in
        for name, digest in fps.items():
            with self.subTest(path=name):
                self.assertNotEqual(digest, "MISSING")
                self.assertEqual(len(digest), 64)
                if name != "pending_overlay":
                    self.assertFalse(pathlib.PurePosixPath(name).is_absolute())
                    self.assertTrue(not name.startswith("/"))
                    self.assertTrue((root / name).exists(), name)
        for consumed in ("docs/reference/ini_corpus.json",
                         "docs/reference/peer_corpus/index.json",
                         "docs/reference/peer_corpus/ca_ab9e477c.jsonl",
                         "tools/balance/peer_corpus.py",
                         "docs/reference/armor_normalized.json",
                         "docs/design/ORIGINAL_UNITS_RAW.md",
                         "mods/cameo/mod.yaml",          # CHAIN ROOT from the miniyaml manifest
                         "tools/audit/miniyaml.py"):
            with self.subTest(consumed=consumed):
                self.assertIn(consumed, fps)
        self.assertTrue(any(k.startswith("mods/cameo/") for k in fps),
                        "the consumed live ruleset files are not fingerprinted")

    def test_class_anchors_is_not_fingerprinted(self):
        self.assertNotIn("docs/balance/class_anchors.json", jp.input_fingerprints())

    def test_active_yaml_paths_exit_on_manifest_failure(self):
        import miniyaml
        with unittest.mock.patch.object(miniyaml, "load_manifest",
                                        side_effect=OSError("manifest gone")):
            with self.assertRaisesRegex(OSError, "manifest gone"):
                jp.active_yaml_paths()

    def test_import_closure_is_fully_fingerprinted(self):
        import types
        seen, stack, closure = set(), [jp, rd, rt, fe, cm, brr, fr, diagnostic_output], set()
        while stack:
            module = stack.pop()
            if not isinstance(module, types.ModuleType) or id(module) in seen:
                continue
            seen.add(id(module))
            file = getattr(module, "__file__", None)
            if file and pathlib.Path(file).parent.name in ("balance", "audit"):
                closure.add(pathlib.Path(file).relative_to(pathlib.Path(jp.ROOT)).as_posix())
                stack += [v for v in vars(module).values()
                          if isinstance(v, types.ModuleType)]
        for name in closure:
            with self.subTest(code=name):
                self.assertIn(name, jp.PROVENANCE_CODE)


class InputStabilityTests(unittest.TestCase):
    def test_changed_evidence_is_detected(self):
        self.assertTrue(jp.input_evidence_changed({"a.json": "0"}, {"a.json": "1"}))

    def test_unchanged_evidence_passes(self):
        self.assertFalse(jp.input_evidence_changed({}, {}))


class ProvenanceLabelTests(unittest.TestCase):
    ORIGINAL = {"OpenRA Red Alert": {"confidence": "STRONG", "id": "HTNK"}}
    ANALOGUE = {"Combined Arms": {"confidence": "FAIR", "id": "HTNK"}}

    def test_strong_fair_original_source_is_original(self):
        self.assertEqual(jp.provenance_label(self.ORIGINAL), "original")
        self.assertEqual(jp.provenance_label({**self.ANALOGUE, **self.ORIGINAL}), "original")

    def test_strong_fair_expansion_only_is_analogue(self):
        self.assertEqual(jp.provenance_label(self.ANALOGUE), "analogue")

    def test_shape_weak_or_missing_records_are_unknown(self):
        for record in (None, {}, {"Combined Arms": {"confidence": "SHAPE"}}):
            with self.subTest(record=record):
                self.assertEqual(jp.provenance_label(record), "unknown")

    def test_extrapolation_is_never_claimed_from_absent_evidence(self):
        for record in (None, {}, self.ANALOGUE, self.ORIGINAL):
            with self.subTest(record=record):
                self.assertNotEqual(jp.provenance_label(record), "extrapolation")


class GeoSpreadTests(unittest.TestCase):
    def test_agreement_is_one(self):
        self.assertAlmostEqual(jp.geo_spread([100.0, 100.0]), 1.0)

    def test_two_fold_disagreement_across_two_sources(self):
        self.assertAlmostEqual(jp.geo_spread([100.0, 400.0]), 2.0)

    def test_single_value_has_no_spread(self):
        self.assertIsNone(jp.geo_spread([100.0]))


class SyntheticDocHelper:
    @staticmethod
    def synthetic():
        return {
            "artifact": jp.OUT_BASENAME, "unapproved": True,
            "input_fingerprints": {"x": "0" * 64},
            "class_ratio_pools": {}, "donors": [], "join_diagnostics": {},
            "pending_overlay": {"state": jp.NOT_CHECKED, "actors": None},
            "stage": {"pilot": "sensitivity_only", "applied": None, "not_completed": True},
        }


class BaselinePinTests(unittest.TestCase):
    def test_pin_reports_content_hash_and_pin_state(self):
        doc = SyntheticDocHelper.synthetic()
        with tempfile.TemporaryDirectory() as directory:
            export = pathlib.Path(directory) / "baseline.json"
            export.write_text(json.dumps(doc, ensure_ascii=False, indent=1,
                                         sort_keys=True, allow_nan=False) + "\n",
                              encoding="utf-8")
            record = jp.pin_baseline(export, doc)
            pinned_bytes = hashlib.sha256(export.read_bytes()).hexdigest()
        self.assertEqual(record["state"], "PINNED")
        self.assertEqual(record["content_sha256"], pinned_bytes)

    def test_fingerprint_mismatch_refuses_with_archival_note(self):
        doc = SyntheticDocHelper.synthetic()
        stale = dict(doc, input_fingerprints={"x": "1" * 64})
        with tempfile.TemporaryDirectory() as directory:
            export = pathlib.Path(directory) / "baseline.json"
            export.write_text(json.dumps(stale), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "NOT immutable data archival"):
                jp.pin_baseline(export, doc)

    def test_pinned_section_drift_refuses_even_with_matching_fingerprints(self):
        doc = SyntheticDocHelper.synthetic()
        stale = dict(doc, class_ratio_pools={"mbt": {"hp": {"status": "THIN"}}})
        with tempfile.TemporaryDirectory() as directory:
            export = pathlib.Path(directory) / "baseline.json"
            export.write_text(json.dumps(stale), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "determinism invariant failed"):
                jp.pin_baseline(export, doc)

    def test_junk_baseline_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            export = pathlib.Path(directory) / "other.json"
            export.write_text(json.dumps({"artifact": "other_tool"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "fingerprinted japan_reference_pilot"):
                jp.pin_baseline(export, SyntheticDocHelper.synthetic())


class PendingOverlayTests(unittest.TestCase):
    def test_missing_overlay_is_empty_not_a_fallback(self):
        self.assertEqual(jp.load_pending(None), {})

    def test_valid_overlay_loads(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "pending.json"
            path.write_text('{"japan_samurai": "armed_troop_transport?"}', encoding="utf-8")
            self.assertEqual(jp.load_pending(path), {"japan_samurai": "armed_troop_transport?"})

    def test_junk_overlay_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "pending.json"
            path.write_text('{"a": 3}', encoding="utf-8")
            with self.assertRaises(ValueError):
                jp.load_pending(path)


@unittest.skipUnless(
    (ROOT / "docs/balance/derived/reference_assignment.json").exists()
    and (ROOT / "docs/design/ORIGINAL_UNITS_PEER_OPENRA.md").exists(),
    "reference corpus not present")
class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = jp.collect()
        cls.rerun = jp.collect()
        cls.cameo_ids = {c["id"] for c in rd.cameo_rows()
                         if fr.faction_of(c["id"]) == "japan"}

    def test_run_is_deterministic(self):
        self.assertEqual(self.doc, self.rerun)

    def test_input_mutation_during_collect_refuses(self):
        # The pending overlay is a fingerprinted input file the test owns, so a mutation
        # is injected mid-collect without touching any repository file: once the initial
        # fingerprints are captured, changing the overlay must refuse after collection.
        with tempfile.TemporaryDirectory() as directory:
            overlay = pathlib.Path(directory) / "pending.json"
            overlay.write_text(json.dumps({"japan_armoredcar": "mbt"}), encoding="utf-8")
            original = rd.cameo_rows

            def mutate_then_load():
                rows = original()
                overlay.write_text(json.dumps({"japan_armoredcar": "light_tank"}),
                                   encoding="utf-8")
                return rows

            with unittest.mock.patch.object(rd, "cameo_rows", mutate_then_load):
                with self.assertRaisesRegex(ValueError, "changed during collection"):
                    jp.collect(overlay)

    def test_mutation_late_in_subject_phase_still_refuses(self):
        # Regression for recheck placement: the final fingerprint check must run AFTER ALL
        # collection (subject and class processing included). The old check sat before the
        # subject/class pass, so this late mutation would have slipped through.
        with tempfile.TemporaryDirectory() as directory:
            overlay = pathlib.Path(directory) / "pending.json"
            overlay.write_text(json.dumps({"japan_armoredcar": "mbt"}), encoding="utf-8")
            original = jp._r4

            def mutate_on_first_subject(attached_rows, cameo_row, axis, dist, cdist):
                result = original(attached_rows, cameo_row, axis, dist, cdist)
                if cameo_row["id"].startswith("japan"):
                    overlay.write_text(json.dumps({"japan_armoredcar": "light_tank"}),
                                       encoding="utf-8")
                return result

            with unittest.mock.patch.object(jp, "_r4", mutate_on_first_subject):
                with self.assertRaisesRegex(ValueError, "changed during collection"):
                    jp.collect(overlay)

    def test_every_japan_row_present_and_none_dropped(self):
        listed = [r["actor"] for r in self.doc["japan_rows"]]
        self.assertEqual(sorted(listed), sorted(self.cameo_ids))
        self.assertTrue(all(row["axes"]["hp"]["current"] is not None
                            for row in self.doc["japan_rows"]))

    def test_no_japan_donor_anywhere(self):
        for d in self.doc["donors"]:
            with self.subTest(donor=d["actor"]):
                self.assertNotEqual(d["faction"], "japan")
                self.assertIn(d["faction"], jp.CLASSIC_FACTIONS)

    def test_join_is_strict_source_plus_id(self):
        assignment = json.loads((ROOT / "docs/balance/derived/reference_assignment.json")
                                .read_text(encoding="utf-8"))["assignment"]
        for row in self.doc["japan_rows"]:
            for src, rid in row["joined_reference_ids"].items():
                with self.subTest(actor=row["actor"], source=src):
                    self.assertEqual(assignment[row["actor"]][src]["id"], rid)
        for d in self.doc["donors"]:
            for src, entry in d["sources"].items():
                with self.subTest(donor=d["actor"], source=src):
                    self.assertEqual(assignment[d["actor"]][src]["id"], entry["id"])

    def test_donor_class_map_uses_classify_and_originals(self):
        for d in self.doc["donors"]:
            with self.subTest(donor=d["actor"]):
                self.assertIsNotNone(d["class"])
                self.assertNotEqual(d["class"], "support")

    def test_pilot_produced_testable_evidence(self):
        ok = [(cls, axis, pool) for cls, axes in self.doc["class_ratio_pools"].items()
              for axis, pool in axes.items() if pool["status"] == "OK"]
        self.assertTrue(ok, "no pool reached OK — the pilot would show holds only")
        cls, axis, pool = ok[0]
        self.assertGreaterEqual(pool["donor_count"], jp.MIN_DISTINCT_DONORS)
        self.assertGreaterEqual(pool["faction_count"], jp.MIN_DONOR_FACTIONS)
        by_actor = {d["actor"]: d for d in self.doc["donors"]}
        for actor in pool["donors"]:
            with self.subTest(donor=actor):
                self.assertGreaterEqual(by_actor[actor]["n_sources"][axis],
                                        jp.MIN_SOURCES_PER_AXIS)
        applied = [(row, a) for row in self.doc["japan_rows"] for a in jp.APPLY_AXES
                   if (row["axes"][a].get("sensitivity") or {}).get("status") == "UNAPPROVED"]
        self.assertTrue(applied, "no axis applied an UNAPPROVED sensitivity")
        for row, axis in applied:
            with self.subTest(actor=row["actor"], axis=axis):
                value = row["axes"][axis]["sensitivity"]["value"]
                current = row["axes"][axis]["current"]
                pool = self.doc["class_ratio_pools"][row["axes"][axis]["pool"]][axis]
                self.assertAlmostEqual(value, current * pool["ratio"], delta=abs(value) * 1e-6)

    def test_cost_axis_never_gets_a_sensitivity(self):
        for row in self.doc["japan_rows"]:
            with self.subTest(actor=row["actor"]):
                self.assertNotIn("sensitivity", row["axes"]["cost"])
                self.assertEqual(row["axes"]["cost"]["pool"], None)

    def test_fingerprints_present_and_stable(self):
        fps = self.doc["input_fingerprints"]
        self.assertIn("docs/balance/derived/reference_assignment.json", fps)
        self.assertIn("docs/design/ORIGINAL_UNITS_PEER_OPENRA.md", fps)
        code = [k for k in fps if k.startswith("tools/")]
        self.assertEqual(len(code), len(jp.PROVENANCE_CODE))
        self.assertNotIn("docs/balance/class_anchors.json", fps)
        self.assertEqual(fps, self.rerun["input_fingerprints"])

    def test_missing_overlay_is_reported_not_checked(self):
        overlay = self.doc["pending_overlay"]
        self.assertEqual(overlay["state"], jp.NOT_CHECKED)
        self.assertIsNone(overlay["actors"])
        for row in self.doc["japan_rows"]:
            with self.subTest(actor=row["actor"]):
                self.assertEqual(row["pending_class"], jp.NOT_CHECKED)
        self.assertNotIn("PENDING",
                         self.doc["scope"]["sensitivity_status_counts"]["hp"])

    def test_no_silent_mutation_of_current_values(self):
        cameo = {c["id"]: c for c in rd.cameo_rows()}
        for row in self.doc["japan_rows"]:
            c = cameo[row["actor"]]
            for axis in jp.AXES:
                with self.subTest(actor=row["actor"], axis=axis):
                    self.assertEqual(row["axes"][axis]["current"], jp.round6(c.get(axis)))

    def test_ok_pools_meet_the_thresholds_everywhere(self):
        donors = {d["actor"]: d for d in self.doc["donors"]}
        for cls, axes in self.doc["class_ratio_pools"].items():
            for axis, pool in axes.items():
                if pool["status"] != "OK":
                    continue
                with self.subTest(cls=cls, axis=axis):
                    self.assertGreaterEqual(pool["donor_count"], jp.MIN_DISTINCT_DONORS)
                    self.assertGreaterEqual(pool["faction_count"], jp.MIN_DONOR_FACTIONS)
                    self.assertGreater(pool["ratio"], 0.0)
                    for actor in pool["donors"]:
                        self.assertGreaterEqual(donors[actor]["n_sources"][axis],
                                                jp.MIN_SOURCES_PER_AXIS)
                    self.assertEqual(pool["faction_count"],
                                     len({donors[a]["faction"] for a in pool["donors"]}))

    def test_pool_ratio_recomputed_independently_from_donor_values(self):
        donors = {d["actor"]: d for d in self.doc["donors"]}
        checked = 0
        for cls, axes in self.doc["class_ratio_pools"].items():
            for axis, pool in axes.items():
                if pool["status"] != "OK":
                    continue
                ratios = [donors[a]["target"][axis] / donors[a]["current"][axis]
                          for a in pool["donors"]]
                expected = math.exp(sum(math.log(r) for r in ratios) / len(ratios))
                with self.subTest(cls=cls, axis=axis):
                    self.assertAlmostEqual(expected, pool["ratio"], delta=1e-6,
                                           msg="pool ratio must equal the donor-ratio geomean")
                checked += 1
        self.assertGreater(checked, 0)

    def test_one_class_ratio_flattens_sensitivities_intra_class(self):
        """One ratio per class+axis: order AND spacing scale uniformly inside the class."""
        by_cls = {}
        for row in self.doc["japan_rows"]:
            for axis in ("hp", "speed", "w_range"):
                s = (row["axes"][axis].get("sensitivity") or {})
                if s.get("status") == "UNAPPROVED":
                    current = row["axes"][axis]["current"]
                    by_cls.setdefault(row["axes"][axis]["pool"], {}).setdefault(
                        axis, set()).add(round(s["value"] / current, 6))
        self.assertGreater(len(by_cls), 0)
        for cls, axes in by_cls.items():
            for axis in axes:
                with self.subTest(cls=cls, axis=axis):
                    self.assertEqual(len(axes[axis]), 1)

    def test_separate_peers_only_and_cameo_inclusive_target_views(self):
        counted = 0
        for row in self.doc["japan_rows"]:
            for axis in jp.AXES:
                e = row["axes"][axis]
                with self.subTest(actor=row["actor"], axis=axis):
                    self.assertIn("r4_peers_only", e)
                    self.assertIn("r4_target", e)
                if e["r4_peers_only"] is None:
                    continue
                with self.subTest(actor=row["actor"], axis=axis):
                    self.assertGreater(e["r4_peers_only"], 0.0)
                if e["r4_target"] is not None and e["r4_n_sources"] >= 1:
                    counted += 1
        self.assertGreater(counted, 0)

    def test_target_views_diverge_only_when_comeo_votes(self):
        for row in self.doc["japan_rows"]:
            for axis in jp.AXES:
                e = row["axes"][axis]
                if e["r4_target"] is not None and e["r4_peers_only"] is not None:
                    with self.subTest(actor=row["actor"], axis=axis):
                        # same call, one formula — equal only when the Cameo vote vanishes
                        self.assertTrue(e["r4_target"] > 0 and e["r4_peers_only"] > 0)

    def test_provenance_labels_use_assignment_metadata(self):
        assignment = json.loads((ROOT / "docs/balance/derived/reference_assignment.json")
                                .read_text(encoding="utf-8"))["assignment"]
        allowed = {"original", "analogue", "unknown"}
        for kind, entries in (("rows", self.doc["japan_rows"]), ("donors", self.doc["donors"])):
            for entry in entries:
                with self.subTest(kind=kind, actor=entry["actor"]):
                    self.assertIn(entry.get("provenance"), allowed)
                if entry["provenance"] == "original":
                    with self.subTest(actor=entry["actor"]):
                        self.assertTrue(brr.is_original(assignment.get(entry["actor"])))
        self.assertTrue(any(d["provenance"] == "original" for d in self.doc["donors"]))

    def test_source_disagreement_is_visible_not_fabricated(self):
        spread_present = False
        for row in self.doc["japan_rows"]:
            for axis in jp.AXES:
                sd = row["axes"][axis].get("source_disagreement")
                if sd is None:
                    continue
                with self.subTest(actor=row["actor"], axis=axis):
                    self.assertGreaterEqual(len(sd["values"]), 2)
                    self.assertGreaterEqual(sd["geo_spread"], 1.0)
                    self.assertGreater(sd["max"], 0.0)
                    self.assertGreater(sd["min"], 0.0)
                    spread_present = True
        self.assertTrue(spread_present, "no source disagreement surfaced in the real run")
        for cls, axes in self.doc["class_ratio_pools"].items():
            for axis, pool in axes.items():
                if pool["status"] == "OK":
                    with self.subTest(cls=cls, axis=axis):
                        self.assertIsNotNone(pool["ratio_spread"])

    def test_cli_content_hash_matches_canonical_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            code = subprocess.run(
                [sys.executable, "tools/balance/build_japan_pilot.py", "--out", directory],
                capture_output=True, text=True, cwd=str(ROOT), timeout=120, check=False)
            self.assertEqual(code.returncode, 0, code.stderr)
            text = (pathlib.Path(directory) / "japan_reference_pilot.json").read_text(
                encoding="utf-8")
            doc = json.loads(text)
            payload = {k: v for k, v in doc.items() if k != "content_sha256"}
            canonical = json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True,
                                   allow_nan=False) + "\n"
            self.assertEqual(doc["content_sha256"],
                             hashlib.sha256(canonical.encode("utf-8")).hexdigest())
            self.assertEqual(doc["baseline"]["state"], "NOT_PINNED")
            self.assertFalse(doc["stage"]["not_completed"] is False)
        self.assertTrue(self.doc["stage"]["not_completed"] is True)

    def test_cli_baseline_pin_and_mismatch_refusal(self):
        with tempfile.TemporaryDirectory() as outer:
            run_dir = pathlib.Path(outer) / "run"
            code = subprocess.run(
                [sys.executable, "tools/balance/build_japan_pilot.py", "--out", str(run_dir)],
                capture_output=True, text=True, cwd=str(ROOT), timeout=120, check=False)
            self.assertEqual(code.returncode, 0, code.stderr)
            consensus_file = run_dir / "japan_reference_pilot.json"
            tampered = pathlib.Path(outer) / "tampered.json"
            doc = json.loads(consensus_file.read_text(encoding="utf-8"))
            doc["input_fingerprints"]["docs/balance/derived/reference_assignment.json"] = "0" * 64
            tampered.write_text(json.dumps(doc), encoding="utf-8")
            for baseline, expected in ((consensus_file, "PINNED"),
                                       (tampered, "mismatch")):
                with self.subTest(baseline=str(baseline)):
                    code = subprocess.run(
                        [sys.executable, "tools/balance/build_japan_pilot.py",
                         "--out", str(pathlib.Path(outer) / "out2"), "--baseline", str(baseline)],
                        capture_output=True, text=True, cwd=str(ROOT), timeout=120, check=False)
                    self.assertEqual(code.returncode, 0 if expected == "PINNED" else 2,
                                     code.stdout + code.stderr)
                    if expected == "PINNED":
                        result = json.loads((pathlib.Path(outer) / "out2" /
                                             "japan_reference_pilot.json").read_text(
                                                 encoding="utf-8"))
                        self.assertEqual(result["baseline"]["state"], "PINNED")
                    else:
                        self.assertIn("fingerprint mismatch", code.stderr)

    def test_stage_reports_pending_work_not_completion(self):
        self.assertEqual(self.doc["stage"]["applied"], None)
        self.assertTrue(self.doc["stage"]["not_completed"])
        self.assertIn("grid/weapon/tier", self.doc["stage"]["missing_evidence"])

    def test_donor_filtering_is_exhaustive(self):
        assignment = json.loads((ROOT / "docs/balance/derived/reference_assignment.json")
                                .read_text(encoding="utf-8"))["assignment"]
        classic = [a for a in assignment if fr.faction_of(a) in jp.CLASSIC_FACTIONS]
        counted = len(self.doc["donors"]) + len(self.doc["scope"]["donor_exclusions"])
        self.assertEqual(len(classic), counted)
        for actor, reason in self.doc["scope"]["donor_exclusions"].items():
            with self.subTest(actor=actor):
                self.assertIn(fr.faction_of(actor), jp.CLASSIC_FACTIONS)
                if reason == "japan_donor":
                    self.fail("japan_donor reason must never appear for a classic actor")

    def test_pending_overlay_holds_subject_axes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "pending.json"
            subject = next(r["actor"] for r in self.doc["japan_rows"] if r["class"])
            path.write_text(json.dumps({subject: "armed_troop_transport?"}), encoding="utf-8")
            pending_doc = jp.collect(path)
            row = next(r for r in pending_doc["japan_rows"] if r["actor"] == subject)
            for axis in jp.APPLY_AXES:
                with self.subTest(axis=axis):
                    self.assertEqual(row["axes"][axis]["sensitivity"]["status"], "PENDING")
                    self.assertTrue(row["axes"][axis]["sensitivity"]["hold"])
            self.assertEqual(row["pending_class"], "armed_troop_transport?")


if __name__ == "__main__":
    unittest.main()
