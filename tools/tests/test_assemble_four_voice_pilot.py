"""Focused tests for the hand-authored four-voice pilot driver."""
import copy
import pathlib
import sys
import hashlib
import json
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import assemble_four_voice_pilot as pilot  # noqa: E402


def terms(seed):
    return {
        "None": {"A": seed, "B": 0.0},
        "Wood": {"A": seed + 1, "B": 0.0},
        "Concrete": {"A": seed + 2, "B": 0.0},
        "Light": {"A": seed + 3, "B": 0.01},
        "Heavy": {"A": seed + 4, "B": 0.02},
    }


def record(source, actor, weapon, *, status="RESOLVED", scenario="vehicle", seed=1):
    result = {
        "actor": actor,
        "weapon": weapon,
        "scenario": scenario,
        "status": status,
        "terms": terms(seed),
    }
    if source is not None:
        result["source"] = source
    return result


def datasets():
    return {
        "cameo": [record(None, "tank", "cameo-gun", seed=1)],
        "reference": [
            record("Combined Arms", "tank", "ca-gun", seed=2),
            record("OpenRA Red Alert", "tank", "ora-gun", seed=3),
        ],
        "dta": [record("DTA Enhanced", "tank", "dta-gun",
                       status="BASE_CHANNELS_RESOLVED",
                       scenario="eligible_unobstructed_impact", seed=4)],
    }


def manifest():
    return {
        "schema": 1,
        "policy": {"voice_weight": 0.25},
        "groups": [{
            "comparison_id": "tank/vehicle/base",
            "scenario": "vehicle",
            "state_key": "base",
            "voices": [
                {"voice": "Current Cameo", "dataset": "cameo", "record_index": 0,
                 "expected": {"actor": "tank", "weapon": "cameo-gun", "scenario": "vehicle"}},
                {"voice": "Combined Arms", "dataset": "reference", "record_index": 0,
                 "expected": {"actor": "tank", "weapon": "ca-gun", "scenario": "vehicle"}},
                {"voice": "DTA Enhanced", "dataset": "dta", "record_index": 0,
                 "record_scenario": "eligible_unobstructed_impact",
                 "status_alias": "DTA_BASE_CHANNELS_RESOLVED",
                 "expected": {"actor": "tank", "weapon": "dta-gun"}},
                {"voice": "OpenRA Red Alert", "dataset": "reference", "record_index": 1,
                 "expected": {"actor": "tank", "weapon": "ora-gun", "scenario": "vehicle"}},
            ],
        }],
    }


def bound_self_vote():
    return {"status": "RESOLVED", "basis": "test fixture"}


def reconstruction_evidence(root, baseline_sha256, dataset_sha256,
                            *, dataset_schema=1, source_hashes=None,
                            source_state=None):
    document = {
        "schema": 1,
        "review_status": "REVIEWED",
        "scope": "original current Cameo per-armor channel reconstruction",
        "method": "independent source closure with explicit channel mapping",
        "normalization": "none; source-local terms retained",
        "baseline_sha256": baseline_sha256,
        "dataset_sha256": dataset_sha256,
        "dataset_schema": dataset_schema,
        "source_state": (source_state if source_state is not None else
                          {"kind": "dirty_worktree", "commit": "d" * 40,
                           "dirty": True, "reconciled_to_snapshot": True}),
        "source_hashes": (source_hashes if source_hashes is not None
                           else {"source-closure.json": "c" * 64}),
    }
    path = pathlib.Path(root) / "reconstruction-evidence.json"
    data = json.dumps(document, sort_keys=True).encode("utf-8")
    path.write_bytes(data)
    return {"path": path.name, "sha256": hashlib.sha256(data).hexdigest()}


class AssembleFourVoicePilotTests(unittest.TestCase):
    def test_separate_reconstruction_contract_does_not_require_mutating_baseline(self):
        baseline_sha = "a" * 64
        dataset_sha = "b" * 64
        with tempfile.TemporaryDirectory() as directory:
            baseline = {"rows": [], "inputs": {}}
            before = copy.deepcopy(baseline)
            evidence = reconstruction_evidence(directory, baseline_sha, dataset_sha)
            contract = {"baseline_sha256": baseline_sha, "dataset_sha256": dataset_sha,
                        "reconstruction_evidence": evidence}
            bound = pilot.verify_current_cameo_binding(
                baseline, {"schema": 1}, dataset_sha,
                binding_contract=contract, baseline_sha256=baseline_sha,
                evidence_root=directory)
            self.assertEqual(bound["status"], "RESOLVED")
            self.assertEqual(bound["reconstruction_evidence"]["source_state"],
                             {"kind": "dirty_worktree", "commit": "d" * 40,
                              "dirty": True, "reconciled_to_snapshot": True})
            self.assertEqual(baseline, before)
            clean_state = {"kind": "clean_commit", "commit": "e" * 40,
                           "dirty": False, "reconciled_to_snapshot": True}
            clean_evidence = reconstruction_evidence(
                directory, baseline_sha, dataset_sha, source_state=clean_state)
            clean_contract = {"baseline_sha256": baseline_sha,
                              "dataset_sha256": dataset_sha,
                              "reconstruction_evidence": clean_evidence}
            clean_bound = pilot.verify_current_cameo_binding(
                baseline, {"schema": 1}, dataset_sha,
                binding_contract=clean_contract, baseline_sha256=baseline_sha,
                evidence_root=directory)
            self.assertEqual(clean_bound["status"], "RESOLVED")
            self.assertEqual(clean_bound["reconstruction_evidence"]["source_state"],
                             clean_state)
            rejected = pilot.verify_current_cameo_binding(
                baseline, {"schema": 1}, "c" * 64,
                binding_contract=contract, baseline_sha256=baseline_sha,
                evidence_root=directory)
            self.assertEqual(rejected["status"], "UNRESOLVED")

    def test_reconstruction_evidence_string_is_rejected(self):
        result = pilot.verify_current_cameo_binding(
            {"rows": [], "inputs": {}}, {"schema": 1}, "b" * 64,
            binding_contract={"baseline_sha256": "a" * 64,
                              "dataset_sha256": "b" * 64,
                              "reconstruction_evidence": "reviewed.json"},
            baseline_sha256="a" * 64)
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertEqual(result["reason"], "reconstruction_evidence_contract_not_object")

    def test_reconstruction_evidence_rejects_missing_changed_and_escaping_files(self):
        baseline_sha = "a" * 64
        dataset_sha = "b" * 64
        with tempfile.TemporaryDirectory() as directory:
            evidence = reconstruction_evidence(directory, baseline_sha, dataset_sha)
            contract = {"baseline_sha256": baseline_sha, "dataset_sha256": dataset_sha,
                        "reconstruction_evidence": evidence}
            evidence_path = pathlib.Path(directory) / evidence["path"]
            evidence_path.write_bytes(evidence_path.read_bytes() + b"changed")
            changed = pilot.verify_current_cameo_binding(
                {}, {"schema": 1}, dataset_sha, binding_contract=contract,
                baseline_sha256=baseline_sha, evidence_root=directory)
            self.assertEqual(changed["reason"], "reconstruction_evidence_hash_mismatch")
            evidence["path"] = "../outside.json"
            escaping = pilot.verify_current_cameo_binding(
                {}, {"schema": 1}, dataset_sha, binding_contract=contract,
                baseline_sha256=baseline_sha, evidence_root=directory)
            self.assertEqual(escaping["reason"], "reconstruction_evidence_path_invalid")
            evidence["path"] = "missing.json"
            missing = pilot.verify_current_cameo_binding(
                {}, {"schema": 1}, dataset_sha, binding_contract=contract,
                baseline_sha256=baseline_sha, evidence_root=directory)
            self.assertEqual(missing["reason"], "reconstruction_evidence_missing")

    def test_reconstruction_evidence_rejects_noninteger_schema_and_empty_provenance(self):
        baseline_sha = "a" * 64
        dataset_sha = "b" * 64
        with tempfile.TemporaryDirectory() as directory:
            evidence = reconstruction_evidence(directory, baseline_sha, dataset_sha)
            path = pathlib.Path(directory) / evidence["path"]
            document = json.loads(path.read_text(encoding="utf-8"))
            for schema in (True, 1.0):
                document["schema"] = schema
                data = json.dumps(document, sort_keys=True).encode("utf-8")
                path.write_bytes(data)
                evidence["sha256"] = hashlib.sha256(data).hexdigest()
                contract = {"baseline_sha256": baseline_sha, "dataset_sha256": dataset_sha,
                            "reconstruction_evidence": evidence}
                result = pilot.verify_current_cameo_binding(
                    {}, {"schema": 1}, dataset_sha, binding_contract=contract,
                    baseline_sha256=baseline_sha, evidence_root=directory)
                self.assertEqual(result["reason"], "reconstruction_evidence_schema_invalid")
            evidence = reconstruction_evidence(directory, baseline_sha, dataset_sha,
                                                source_hashes={})
            contract["reconstruction_evidence"] = evidence
            result = pilot.verify_current_cameo_binding(
                {}, {"schema": 1}, dataset_sha, binding_contract=contract,
                baseline_sha256=baseline_sha, evidence_root=directory)
            self.assertEqual(result["reason"], "reconstruction_evidence_source_provenance_missing")

    def test_reconstruction_evidence_rejects_wrong_identity_or_incomplete_provenance(self):
        baseline_sha = "a" * 64
        dataset_sha = "b" * 64
        with tempfile.TemporaryDirectory() as directory:
            evidence = reconstruction_evidence(directory, "d" * 64, dataset_sha)
            contract = {"baseline_sha256": baseline_sha, "dataset_sha256": dataset_sha,
                        "reconstruction_evidence": evidence}
            wrong_baseline = pilot.verify_current_cameo_binding(
                {}, {"schema": 1}, dataset_sha, binding_contract=contract,
                baseline_sha256=baseline_sha, evidence_root=directory)
            self.assertEqual(wrong_baseline["reason"], "reconstruction_evidence_baseline_mismatch")
            evidence = reconstruction_evidence(directory, baseline_sha, dataset_sha,
                                                source_hashes={"source": "not-a-sha"})
            contract["reconstruction_evidence"] = evidence
            incomplete = pilot.verify_current_cameo_binding(
                {}, {"schema": 1}, dataset_sha, binding_contract=contract,
                baseline_sha256=baseline_sha, evidence_root=directory)
            self.assertEqual(incomplete["reason"], "reconstruction_evidence_source_provenance_invalid")

    def test_reconstruction_evidence_requires_reconciled_source_state(self):
        baseline_sha = "a" * 64
        dataset_sha = "b" * 64
        with tempfile.TemporaryDirectory() as directory:
            evidence = reconstruction_evidence(directory, baseline_sha, dataset_sha)
            path = pathlib.Path(directory) / evidence["path"]
            document = json.loads(path.read_text(encoding="utf-8"))
            for source_state in (
                None,
                {"kind": "clean_commit", "commit": "d" * 40,
                 "dirty": False, "reconciled_to_snapshot": False},
                {"kind": "clean_commit", "commit": "not-a-commit",
                 "dirty": False, "reconciled_to_snapshot": True},
                {"kind": "dirty_worktree", "commit": "d" * 40,
                 "dirty": "yes", "reconciled_to_snapshot": True},
                {"kind": "clean_commit", "commit": "d" * 40,
                 "dirty": True, "reconciled_to_snapshot": True},
                {"kind": "dirty_worktree", "commit": "d" * 40,
                 "dirty": False, "reconciled_to_snapshot": True},
                {"kind": "other", "commit": "d" * 40,
                 "dirty": False, "reconciled_to_snapshot": True},
                {"kind": "clean_commit", "commit": "d" * 40,
                 "dirty": 0, "reconciled_to_snapshot": True},
            ):
                if source_state is None:
                    document.pop("source_state", None)
                else:
                    document["source_state"] = source_state
                data = json.dumps(document, sort_keys=True).encode("utf-8")
                path.write_bytes(data)
                evidence["sha256"] = hashlib.sha256(data).hexdigest()
                contract = {"baseline_sha256": baseline_sha, "dataset_sha256": dataset_sha,
                            "reconstruction_evidence": evidence}
                result = pilot.verify_current_cameo_binding(
                    {}, {"schema": 1}, dataset_sha, binding_contract=contract,
                    baseline_sha256=baseline_sha, evidence_root=directory)
                if source_state is None:
                    expected = "reconstruction_evidence_source_state_missing"
                elif source_state.get("kind") not in ("clean_commit", "dirty_worktree"):
                    expected = "reconstruction_evidence_source_state_kind_invalid"
                elif not isinstance(source_state.get("dirty"), bool):
                    expected = "reconstruction_evidence_source_state_dirty_invalid"
                elif source_state.get("reconciled_to_snapshot") is not True:
                    expected = "reconstruction_evidence_source_state_not_reconciled"
                elif not pilot._is_git_commit(source_state.get("commit")):
                    expected = "reconstruction_evidence_source_state_commit_invalid"
                elif ((source_state["kind"] == "clean_commit" and source_state["dirty"] is not False)
                      or (source_state["kind"] == "dirty_worktree" and source_state["dirty"] is not True)):
                    expected = "reconstruction_evidence_source_state_kind_dirty_mismatch"
                else:
                    expected = "reconstruction_evidence_source_state_dirty_invalid"
                self.assertEqual(result["reason"], expected)

    def test_reconstruction_evidence_commit_matches_snapshot_head(self):
        baseline_sha = "a" * 64
        dataset_sha = "b" * 64
        snapshot_head = "d" * 40
        with tempfile.TemporaryDirectory() as directory:
            evidence = reconstruction_evidence(directory, baseline_sha, dataset_sha)
            contract = {"baseline_sha256": baseline_sha,
                        "dataset_sha256": dataset_sha,
                        "reconstruction_evidence": evidence}
            baseline = {"worktree_head": snapshot_head}
            accepted = pilot.verify_current_cameo_binding(
                baseline, {"schema": 1}, dataset_sha,
                binding_contract=contract, baseline_sha256=baseline_sha,
                evidence_root=directory)
            self.assertEqual(accepted["status"], "RESOLVED")

            path = pathlib.Path(directory) / evidence["path"]
            document = json.loads(path.read_text(encoding="utf-8"))
            document["source_state"]["commit"] = "e" * 40
            data = json.dumps(document, sort_keys=True).encode("utf-8")
            path.write_bytes(data)
            evidence["sha256"] = hashlib.sha256(data).hexdigest()
            rejected = pilot.verify_current_cameo_binding(
                baseline, {"schema": 1}, dataset_sha,
                binding_contract=contract, baseline_sha256=baseline_sha,
                evidence_root=directory)
            self.assertEqual(
                rejected["reason"],
                "reconstruction_evidence_source_state_commit_mismatch",
            )

            baseline["worktree_head"] = "not-a-commit"
            document["source_state"]["commit"] = snapshot_head
            data = json.dumps(document, sort_keys=True).encode("utf-8")
            path.write_bytes(data)
            evidence["sha256"] = hashlib.sha256(data).hexdigest()
            invalid_snapshot = pilot.verify_current_cameo_binding(
                baseline, {"schema": 1}, dataset_sha,
                binding_contract=contract, baseline_sha256=baseline_sha,
                evidence_root=directory)
            self.assertEqual(
                invalid_snapshot["reason"],
                "reconstruction_evidence_snapshot_commit_invalid",
            )

            baseline["worktree_head"] = None
            null_snapshot = pilot.verify_current_cameo_binding(
                baseline, {"schema": 1}, dataset_sha,
                binding_contract=contract, baseline_sha256=baseline_sha,
                evidence_root=directory)
            self.assertEqual(
                null_snapshot["reason"],
                "reconstruction_evidence_snapshot_commit_invalid",
            )

    def test_frozen_recovery_checks_bytes_without_certifying_channel_votes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "ledger.json"
            path.write_bytes(b'{"sections": {}}')
            snapshot = {"inputs": {"ledger.json": hashlib.sha256(path.read_bytes()).hexdigest()}}
            result = pilot.recover_frozen_input_evidence(snapshot, directory)
            self.assertEqual(result["matched_inputs"], 1)
            self.assertEqual(result["status"], "VERIFIED")
            path.write_bytes(b'changed')
            self.assertEqual(pilot.recover_frozen_input_evidence(snapshot, directory)["status"],
                             "UNRESOLVED")

    def test_manifest_builds_one_resolved_equal_vote_group(self):
        source = datasets()
        before = copy.deepcopy(source)
        result = pilot.build_document(
            manifest(), source, self_vote_binding=bound_self_vote())

        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["summary"], {
            "groups": 1, "assembly_resolved": 1,
            "aggregation_resolved": 1, "aggregation_unresolved": 0,
            "gate_resolved": 1, "gate_unresolved": 0,
        })
        gate_result = result["groups"][0]["gate"]
        self.assertEqual(gate_result["policy"]["voice_weights"], {
            "Current Cameo": 0.25,
            "Combined Arms": 0.25,
            "DTA Enhanced": 0.25,
            "OpenRA Red Alert": 0.25,
        })
        dta_row = gate_result["source_rows"]["DTA Enhanced"]
        self.assertEqual(dta_row["raw_status"], "BASE_CHANNELS_RESOLVED")
        self.assertEqual(source, before)

    def test_explicit_channel_terms_are_reduced_and_checked_against_record_terms(self):
        source = datasets()
        source["cameo"][0]["channel_terms"] = [{
            "identity": "cameo-channel",
            "status": "RESOLVED",
            "flat_terms": {axis: values["A"] for axis, values in terms(1).items()},
            "percentage_terms": {axis: values["B"] for axis, values in terms(1).items()},
        }]
        result = pilot.build_document(
            manifest(), source, self_vote_binding=bound_self_vote())
        item = result["groups"][0]
        self.assertEqual(item["aggregation_status"], "RESOLVED")
        self.assertEqual(item["source_aggregation"]["Current Cameo"]["provenance"]["channel_projection"]["mode"],
                         "explicit_channel_terms")
        self.assertEqual(item["source_aggregation"]["Current Cameo"]["provenance"]["input_row_count"], 1)
        self.assertEqual(item["source_aggregation"]["Current Cameo"]["component_summary"]["channel_count"], 1)
        self.assertEqual(item["source_aggregation"]["Current Cameo"]["component_summary"]["max_hp_fraction_terms_B"]["Light"],
                         0.01)

    def test_channel_sum_mismatch_fails_closed_before_gate(self):
        source = datasets()
        source["cameo"][0]["channel_terms"] = [{
            "identity": "wrong-channel",
            "status": "RESOLVED",
            "flat_terms": {axis: values["A"] + 1 for axis, values in terms(1).items()},
            "percentage_terms": {axis: values["B"] for axis, values in terms(1).items()},
        }]
        result = pilot.build_document(
            manifest(), source, self_vote_binding=bound_self_vote())
        item = result["groups"][0]
        self.assertEqual(item["aggregation_status"], "UNRESOLVED")
        self.assertIn("Current Cameo:channel_sum_mismatch:selected_record_terms",
                      item["aggregation_reasons"])
        self.assertEqual(item["gate"]["status"], "UNRESOLVED")

    def test_missing_self_vote_binding_fails_closed(self):
        result = pilot.build_document(manifest(), datasets())
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertEqual(result["summary"]["gate_resolved"], 0)
        self.assertIn(
            "current_cameo_self_vote_unbound:current_cameo_self_vote_binding_not_supplied",
            result["groups"][0]["gate"]["reasons"],
        )

    def test_baseline_must_explicitly_bind_channel_dataset_hash(self):
        missing = pilot.verify_current_cameo_binding({}, {"schema": 1}, "abc")
        self.assertEqual(missing["status"], "UNRESOLVED")
        bound = pilot.verify_current_cameo_binding(
            {"current_cameo_channel_vote": {
                "dataset_sha256": "abc", "dataset_schema": 1,
            }},
            {"schema": 1},
            "abc",
        )
        self.assertEqual(bound["status"], "UNRESOLVED")

    def test_embedded_contract_must_match_the_supplied_baseline_hash(self):
        result = pilot.verify_current_cameo_binding(
            {"current_cameo_channel_vote": {
                "baseline_sha256": "d" * 64,
                "dataset_sha256": "b" * 64,
                "reconstruction_evidence": {},
            }},
            {"schema": 1}, "b" * 64, baseline_sha256="a" * 64)
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertEqual(result["reason"], "baseline_channel_vote_baseline_hash_mismatch")

    def test_expected_identity_guard_fails_closed(self):
        spec = manifest()
        spec["groups"][0]["voices"][0]["expected"]["weapon"] = "wrong"
        result = pilot.build_document(spec, datasets())
        item = result["groups"][0]

        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIn("expected_identity_mismatch:0:weapon:'cameo-gun'!='wrong'",
                      item["assembly_reasons"])
        self.assertEqual(item["gate"]["status"], "UNRESOLVED")
        self.assertNotIn("means", item["gate"])

    def test_dta_alias_is_required_by_the_driver(self):
        spec = manifest()
        spec["groups"][0]["voices"][2].pop("status_alias")
        result = pilot.build_document(spec, datasets())
        item = result["groups"][0]

        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIn("status_not_resolved:2:'BASE_CHANNELS_RESOLVED'",
                      item["assembly_reasons"])
        self.assertEqual(item["gate"]["status"], "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
