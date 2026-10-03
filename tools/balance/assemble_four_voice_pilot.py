#!/usr/bin/env python3
"""Run a hand-authored four-voice selection through the review gate.

The input manifest owns every dataset/index selection and the group metadata.
This driver only loads those records, checks optional manifest identity guards,
projects them with ``explicit_voice_group_assembler`` and passes the resulting
rows to the fail-closed four-voice gate.  It never joins actors or weapons,
normalizes source values, or writes gameplay data.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import string
import re
from collections.abc import Mapping
from pathlib import Path

import diagnostic_output
import explicit_voice_group_assembler as assembler
import four_source_synthesis_gate as gate
import source_channel_reducer as reducer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
import four_source_group_inventory as coverage_inventory  # noqa: E402

DEFAULT_MANIFEST = ROOT / "docs/balance/four_voice_selection_pilot_20260911.json"
DEFAULT_CAMEO_BASELINE = ROOT / "docs/reference/cameo_baselines/pre_reference_20260910.json"
EXTERNAL_VALIDATION = Path(
    "C:/Users/Blackrobe/Documents/agents/cameo-reference-sources-20260909/validation"
)
DEFAULT_CAMEO = EXTERNAL_VALIDATION / "cameo-channel-curves-20260911/cameo_channel_curves_passengers.json"
DEFAULT_REFERENCE = EXTERNAL_VALIDATION / "reference-channel-curves-20260911/reference_channel_curves_clamped.json"
DEFAULT_DTA = EXTERNAL_VALIDATION / "dta-channel-curves-20260911/dta_channel_curves_deduplicated.json"
DEFAULT_COVERAGE_MATRIX = (
    EXTERNAL_VALIDATION / "four-faction-sunday-pilot/warhead-reference-freshness/"
    "pilot-warhead-review.json"
)
DEFAULT_FROZEN_INPUT_ROOT = EXTERNAL_VALIDATION / "cameo-frozen-baseline-20260910"
_UNSET = object()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256(value) -> bool:
    return (isinstance(value, str) and len(value) == 64 and
            all(character in string.hexdigits for character in value))


def _is_git_commit(value) -> bool:
    return (isinstance(value, str) and len(value) == 40 and
            bool(re.fullmatch(r"[0-9a-fA-F]{40}", value)))


def _portable_evidence_path(root, value):
    """Resolve one evidence path under an explicit portable root."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        candidate = Path(value)
        if candidate.is_absolute():
            return None
        root = Path(root).resolve()
        resolved = (root / candidate).resolve()
        return resolved if resolved.is_relative_to(root) else None
    except (OSError, RuntimeError, ValueError):
        return None


def _validate_reconstruction_evidence(evidence, *, baseline_sha256,
                                     dataset_sha256, dataset_schema,
                                     evidence_root, snapshot_commit=_UNSET):
    """Validate a separately reviewed, portable reconstruction receipt.

    The receipt is an integrity and provenance contract, not a reconstruction
    engine.  Its explicit review marker and source hashes must be supplied by
    an independent review; this validator does not rederive historical armor
    channels or certify their substantive correctness.
    """
    if not isinstance(evidence, Mapping):
        return None, "reconstruction_evidence_contract_not_object"
    if not _is_sha256(baseline_sha256) or not _is_sha256(dataset_sha256):
        return None, "reconstruction_evidence_binding_hash_invalid"
    path = _portable_evidence_path(evidence_root, evidence.get("path"))
    if path is None:
        return None, "reconstruction_evidence_path_invalid"
    expected_sha = evidence.get("sha256")
    if not _is_sha256(expected_sha):
        return None, "reconstruction_evidence_hash_invalid"
    if not path.is_file():
        return None, "reconstruction_evidence_missing"
    actual_sha = _sha256(path)
    if actual_sha.lower() != expected_sha.lower():
        return None, "reconstruction_evidence_hash_mismatch"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, "reconstruction_evidence_malformed"
    if (not isinstance(document, Mapping)
            or type(document.get("schema")) is not int
            or document.get("schema") != 1):
        return None, "reconstruction_evidence_schema_invalid"
    if document.get("review_status") != "REVIEWED":
        return None, "reconstruction_evidence_review_status_missing"
    if document.get("baseline_sha256") != baseline_sha256:
        return None, "reconstruction_evidence_baseline_mismatch"
    if document.get("dataset_sha256") != dataset_sha256:
        return None, "reconstruction_evidence_dataset_mismatch"
    if dataset_schema is not None and document.get("dataset_schema") != dataset_schema:
        return None, "reconstruction_evidence_dataset_schema_mismatch"
    source_state = document.get("source_state")
    if not isinstance(source_state, Mapping):
        return None, "reconstruction_evidence_source_state_missing"
    if source_state.get("kind") not in ("clean_commit", "dirty_worktree"):
        return None, "reconstruction_evidence_source_state_kind_invalid"
    if not _is_git_commit(source_state.get("commit")):
        return None, "reconstruction_evidence_source_state_commit_invalid"
    if not isinstance(source_state.get("dirty"), bool):
        return None, "reconstruction_evidence_source_state_dirty_invalid"
    if ((source_state["kind"] == "clean_commit" and source_state["dirty"] is not False)
            or (source_state["kind"] == "dirty_worktree" and source_state["dirty"] is not True)):
        return None, "reconstruction_evidence_source_state_kind_dirty_mismatch"
    if source_state.get("reconciled_to_snapshot") is not True:
        return None, "reconstruction_evidence_source_state_not_reconciled"
    # The immutable actor snapshot records the checkout HEAD separately from
    # its content hash.  When present, a reconstruction receipt must name that
    # exact HEAD; otherwise a later checkout could be attested as the snapshot
    # source merely by matching the dataset and baseline hashes.  Older test
    # fixtures and snapshots without this field retain the hash-only contract.
    if snapshot_commit is not _UNSET:
        if not _is_git_commit(snapshot_commit):
            return None, "reconstruction_evidence_snapshot_commit_invalid"
        if source_state["commit"].lower() != snapshot_commit.lower():
            return None, "reconstruction_evidence_source_state_commit_mismatch"
    for field in ("scope", "method", "normalization"):
        if not isinstance(document.get(field), str) or not document[field].strip():
            return None, "reconstruction_evidence_" + field + "_missing"
    source_hashes = document.get("source_hashes")
    if not isinstance(source_hashes, Mapping) or not source_hashes:
        return None, "reconstruction_evidence_source_provenance_missing"
    if any(not isinstance(source, str) or not source.strip() or
           not _is_sha256(source_hash)
           for source, source_hash in source_hashes.items()):
        return None, "reconstruction_evidence_source_provenance_invalid"
    return {
        "path": str(path),
        "sha256": actual_sha,
        "schema": document["schema"],
        "review_status": document["review_status"],
        "scope": document["scope"],
        "method": document["method"],
        "normalization": document["normalization"],
        "baseline_sha256": document["baseline_sha256"],
        "dataset_sha256": document["dataset_sha256"],
        "dataset_schema": document.get("dataset_schema"),
        "source_state": dict(document["source_state"]),
        "source_hashes": dict(document["source_hashes"]),
    }, None


def verify_current_cameo_binding(baseline, cameo_document, cameo_sha256, *,
                                binding_contract=None, baseline_sha256=None,
                                evidence_root=None):
    """Prove that the selected Cameo channel dataset is the frozen self-vote.

    A baseline hash carried beside an unrelated live dataset is provenance, not
    a binding. A separately reviewed manifest contract may bind both artifacts;
    the original immutable actor baseline must never be edited to add a field.
    Such a contract records reviewed reconstruction evidence, not new authority
    to freeze a later live dataset as the original self-vote.
    """
    contract = (baseline.get("current_cameo_channel_vote")
                if isinstance(baseline, Mapping) else None)
    if binding_contract is not None:
        if (not isinstance(binding_contract, Mapping) or not baseline_sha256
                or binding_contract.get("baseline_sha256") != baseline_sha256
                or not binding_contract.get("reconstruction_evidence")):
            return {"status": "UNRESOLVED",
                    "reason": "channel_reconstruction_contract_invalid",
                    "dataset_sha256": cameo_sha256}
        contract = binding_contract
    if not isinstance(contract, Mapping):
        return {
            "status": "UNRESOLVED",
            "reason": "original_channel_reconstruction_not_verified",
            "dataset_sha256": cameo_sha256,
        }
    if (not _is_sha256(baseline_sha256)
            or contract.get("baseline_sha256") != baseline_sha256):
        return {
            "status": "UNRESOLVED",
            "reason": "baseline_channel_vote_baseline_hash_mismatch",
            "dataset_sha256": cameo_sha256,
        }
    expected_sha = contract.get("dataset_sha256")
    if not _is_sha256(expected_sha):
        return {
            "status": "UNRESOLVED",
            "reason": "baseline_channel_vote_hash_missing",
            "dataset_sha256": cameo_sha256,
        }
    if expected_sha.lower() != str(cameo_sha256).lower():
        return {
            "status": "UNRESOLVED",
            "reason": "baseline_channel_vote_hash_mismatch",
            "expected_dataset_sha256": expected_sha,
            "dataset_sha256": cameo_sha256,
        }
    expected_schema = contract.get("dataset_schema")
    actual_schema = (cameo_document.get("schema")
                     if isinstance(cameo_document, Mapping) else None)
    if expected_schema is not None and expected_schema != actual_schema:
        return {
            "status": "UNRESOLVED",
            "reason": "baseline_channel_vote_schema_mismatch",
            "expected_dataset_schema": expected_schema,
            "dataset_schema": actual_schema,
            "dataset_sha256": cameo_sha256,
        }
    evidence, evidence_reason = _validate_reconstruction_evidence(
        contract.get("reconstruction_evidence"),
        baseline_sha256=baseline_sha256,
        dataset_sha256=cameo_sha256,
        dataset_schema=expected_schema,
        evidence_root=(evidence_root if evidence_root is not None else ROOT),
        snapshot_commit=(baseline.get("worktree_head", _UNSET)
                         if isinstance(baseline, Mapping) else _UNSET),
    )
    if evidence_reason:
        return {
            "status": "UNRESOLVED",
            "reason": evidence_reason,
            "dataset_sha256": cameo_sha256,
        }
    return {
        "status": "RESOLVED",
        "basis": ("integrity-checked REVIEWED reconstruction contract links the frozen baseline "
                  "to the selected channel dataset; substantive reconstruction is not rederived here"),
        "dataset_sha256": cameo_sha256,
        "dataset_schema": actual_schema,
        "reconstruction_evidence": evidence,
    }


def recover_frozen_input_evidence(baseline, archive_root):
    """Verify the archived raw inputs without rebuilding or rebasing any value."""
    archive_root = Path(archive_root).resolve()
    inputs = baseline.get("inputs", {}) if isinstance(baseline, Mapping) else {}
    rows = []
    for name, expected in sorted(inputs.items()):
        path = (archive_root / name).resolve()
        if not path.is_relative_to(archive_root):
            raise ValueError("frozen input escapes archive: " + name)
        actual = _sha256(path) if path.is_file() else None
        rows.append({"input": name, "expected_sha256": expected,
                     "actual_sha256": actual,
                     "status": "MATCH" if actual == expected else "MISSING_OR_CHANGED"})
    return {
        "status": "VERIFIED" if rows and all(row["status"] == "MATCH" for row in rows)
                  else "UNRESOLVED",
        "archive_root": str(archive_root),
        "expected_inputs": len(rows),
        "matched_inputs": sum(row["status"] == "MATCH" for row in rows),
        "inputs": rows,
        "scope": "Original actor-stat and derived-ledger inputs only. Matching them does not recover missing per-armor warhead masks, Versus or scenario channels.",
    }


def _load_records(path: Path):
    document = json.loads(path.read_text(encoding="utf-8"))
    records = document.get("records") if isinstance(document, Mapping) else None
    if not isinstance(records, list):
        raise ValueError(f"{path}: records must be a list")
    return document, records


def _record_at(selection, datasets):
    if not isinstance(selection, Mapping):
        return None
    dataset = selection.get("dataset")
    index = selection.get("record_index")
    if not isinstance(dataset, str) or isinstance(index, bool) or not isinstance(index, int):
        return None
    records = datasets.get(dataset)
    if not isinstance(records, list) or index < 0 or index >= len(records):
        return None
    record = records[index]
    return record if isinstance(record, Mapping) else None


def _expected_reasons(spec, datasets):
    """Check caller-authored identity guards without matching across voices."""
    reasons = []
    selections = spec.get("voices") if isinstance(spec, Mapping) else None
    if not isinstance(selections, list):
        return reasons
    for index, selection in enumerate(selections):
        if not isinstance(selection, Mapping):
            continue
        expected = selection.get("expected")
        if expected is None:
            continue
        if not isinstance(expected, Mapping):
            reasons.append(f"expected_identity_not_object:{index}")
            continue
        record = _record_at(selection, datasets)
        if record is None:
            reasons.append(f"expected_identity_record_unavailable:{index}")
            continue
        for field, value in expected.items():
            if field not in record or record.get(field) != value:
                reasons.append(
                    f"expected_identity_mismatch:{index}:{field}:{record.get(field)!r}!={value!r}")
    return reasons


def _guard_failure(result, reasons):
    """Turn a computed result into fail-closed evidence after a guard miss."""
    result = copy.deepcopy(result)
    result["status"] = "UNRESOLVED"
    result["reasons"] = sorted(set((result.get("reasons") or []) + reasons))
    for field in ("sources", "normalized_terms", "means", "components"):
        result.pop(field, None)
    return result


def _finite(value):
    """Return a finite float, or ``None`` for an invalid channel value."""
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if number == number and abs(number) != float("inf") else None


def _channel_term_terms(channel):
    """Project one adapter channel into the reducer's explicit A/B shape.

    Current Cameo exposes ``flat_terms``/``percentage_terms``, the reference
    adapters expose ``A``/``B``, and DTA exposes direct/ambient terms.  These
    are source-authored shapes; this function only translates their labels and
    never derives a missing axis or target behavior.
    """
    if not isinstance(channel, Mapping):
        return None, "channel_not_object"
    pairs = None
    if isinstance(channel.get("A"), Mapping) and isinstance(channel.get("B"), Mapping):
        pairs = (channel["A"], channel["B"])
    elif (isinstance(channel.get("flat_terms"), Mapping)
          and isinstance(channel.get("percentage_terms"), Mapping)):
        pairs = (channel["flat_terms"], channel["percentage_terms"])
    elif (isinstance(channel.get("direct_terms"), Mapping)
          and isinstance(channel.get("ambient_terms"), Mapping)):
        # DTA's ambient contribution is an explicit second component of the
        # direct HP channel, not a max-HP fraction.
        direct, ambient = channel["direct_terms"], channel["ambient_terms"]
        if set(direct) != set(ambient):
            return None, "direct_ambient_axes_mismatch"
        terms = {}
        for axis in direct:
            left, right = _finite(direct[axis]), _finite(ambient[axis])
            if left is None or right is None or left < 0 or right < 0:
                return None, f"direct_ambient_value_invalid:{axis}"
            terms[axis] = {"A": left + right, "B": 0.0}
        return terms, None
    else:
        return None, "channel_terms_shape_unsupported"

    if set(pairs[0]) != set(pairs[1]):
        return None, "channel_axes_mismatch"
    terms = {}
    for axis in pairs[0]:
        a, b = _finite(pairs[0][axis]), _finite(pairs[1][axis])
        if a is None or b is None or a < 0 or b < 0:
            return None, f"channel_value_invalid:{axis}"
        terms[axis] = {"A": a, "B": b}
    return terms, None


def _same_terms(left, right):
    """Compare two term maps without accepting missing or nonnumeric values."""
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        return False
    if set(left) != set(right):
        return False
    for axis in left:
        if not isinstance(left[axis], Mapping) or not isinstance(right[axis], Mapping):
            return False
        for label in ("A", "B"):
            a, b = _finite(left[axis].get(label)), _finite(right[axis].get(label))
            if a is None or b is None:
                return False
            if abs(a - b) > max(1e-9, abs(b) * 1e-9):
                return False
    return True


def _channel_rows(row):
    """Build caller-owned reducer rows from one selected record's channels."""
    raw = row.get("raw_record") if isinstance(row, Mapping) else None
    channels = raw.get("channel_terms") if isinstance(raw, Mapping) else None
    if not isinstance(channels, list) or not channels:
        # Some adapters can provide a resolved aggregate without channel
        # detail.  Keep that explicit limitation in the aggregation evidence.
        return [copy.deepcopy(row)], {
            "mode": "selected_record_terms",
            "reason": "channel_terms_missing_or_empty",
        }

    rows = []
    for index, channel in enumerate(channels):
        terms, reason = _channel_term_terms(channel)
        item = {
            "source": copy.deepcopy(row.get("source")),
            "comparison_id": copy.deepcopy(row.get("comparison_id")),
            "scenario": copy.deepcopy(row.get("scenario")),
            "state_key": copy.deepcopy(row.get("state_key")),
            "status": (channel.get("status") if isinstance(channel, Mapping)
                        else "UNRESOLVED"),
            "terms": terms,
            "channel_identity": (copy.deepcopy(channel.get("identity"))
                                 if isinstance(channel, Mapping)
                                 and "identity" in channel else None),
            "channel_index": index,
            "channel_record": copy.deepcopy(channel),
        }
        if reason:
            item["channel_projection_reason"] = reason
        # Keep group-level component evidence once; per-channel DTA evidence is
        # also retained as channel_record above.
        if index == 0:
            for field in ("clamped_hp_components", "direct_components",
                          "ambient_components"):
                if field in row:
                    item[field] = copy.deepcopy(row[field])
        rows.append(item)
    return rows, {"mode": "explicit_channel_terms", "channel_count": len(rows)}


def _aggregate_source_row(row):
    """Reduce one source row before it enters the four-voice gate."""
    channel_rows, mode = _channel_rows(row)
    aggregation = reducer.reduce_source_group(
        channel_rows,
        row.get("source"),
        row.get("comparison_id"),
        row.get("scenario"),
        row.get("state_key"),
    )
    aggregation["provenance"]["channel_projection"] = mode
    if aggregation.get("status") == "RESOLVED":
        aggregation["component_summary"] = {
            "channel_count": mode.get("channel_count", 1),
            "flat_terms_A": {
                axis: values.get("A")
                for axis, values in aggregation["terms"].items()
            },
            "max_hp_fraction_terms_B": {
                axis: values.get("B")
                for axis, values in aggregation["terms"].items()
            },
            "direct_components": copy.deepcopy(aggregation.get("direct_components", [])),
            "ambient_components": copy.deepcopy(aggregation.get("ambient_components", [])),
            "clamped_hp_components": copy.deepcopy(
                aggregation.get("clamped_hp_components", [])),
            "policy": "A/B, direct, ambient and clamped components remain separate diagnostic evidence.",
        }
    if aggregation.get("status") == "RESOLVED" and mode.get("mode") == "explicit_channel_terms":
        if not _same_terms(aggregation.get("terms"), row.get("terms")):
            aggregation["status"] = "UNRESOLVED"
            aggregation["reasons"] = sorted(set(
                list(aggregation.get("reasons", []))
                + ["channel_sum_mismatch:selected_record_terms"]))
            aggregation["terms"] = None
    projected = copy.deepcopy(row)
    if aggregation.get("status") == "RESOLVED":
        projected["terms"] = copy.deepcopy(aggregation["terms"])
        for field in ("clamped_hp_components", "direct_components",
                      "ambient_components"):
            projected[field] = copy.deepcopy(aggregation.get(field, []))
    else:
        projected["status"] = "UNRESOLVED"
        projected["aggregation_reasons"] = copy.deepcopy(aggregation.get("reasons", []))
    return projected, aggregation


def build_document(manifest, datasets, *, input_provenance=None,
                   self_vote_binding=None):
    if not isinstance(manifest, Mapping):
        raise ValueError("manifest must be an object")
    groups = manifest.get("groups")
    if not isinstance(groups, list) or not groups:
        raise ValueError("manifest.groups must be a nonempty list")
    if not isinstance(datasets, Mapping):
        raise ValueError("datasets must be an object")
    binding = (copy.deepcopy(self_vote_binding)
               if isinstance(self_vote_binding, Mapping) else {
                   "status": "UNRESOLVED",
                   "reason": "current_cameo_self_vote_binding_not_supplied",
               })
    binding_reasons = []
    if binding.get("status") != "RESOLVED":
        binding_reasons.append(
            "current_cameo_self_vote_unbound:" +
            str(binding.get("reason") or "unresolved"))

    results = []
    for spec in groups:
        if not isinstance(spec, Mapping):
            spec = {"voices": []}
        assembly = assembler.assemble_group(spec, datasets)
        expected_reasons = _expected_reasons(spec, datasets)
        assembly_reasons = sorted(set(
            assembly.get("reasons", []) + expected_reasons + binding_reasons))
        assembly_status = assembly.get("status")
        if assembly_reasons:
            assembly_status = "UNRESOLVED"

        aggregation_results = {}
        aggregation_reasons = []
        gate_rows = []
        for row in assembly.get("source_rows", []):
            projected, aggregation = _aggregate_source_row(row)
            source = projected.get("source")
            aggregation_results[source] = aggregation
            if aggregation.get("status") != "RESOLVED":
                aggregation_reasons.extend(
                    f"{source}:{reason}"
                    for reason in aggregation.get("reasons", []))
            gate_rows.append(projected)
        gate_input = {
            "comparison_id": assembly.get("comparison_id"),
            "scenario": assembly.get("scenario"),
            "state_key": assembly.get("state_key"),
            "source_rows": gate_rows,
        }
        gated = gate.combine_group(gate_input, scenario_policy=True,
                                   voice_policy=True)
        all_reasons = expected_reasons + aggregation_reasons + binding_reasons
        if all_reasons:
            gated = _guard_failure(gated, all_reasons)
        if aggregation_reasons:
            assembly_reasons.extend(aggregation_reasons)
        aggregation_resolved = sum(
            item.get("status") == "RESOLVED" for item in aggregation_results.values())
        results.append({
            "comparison_id": spec.get("comparison_id"),
            "scenario": spec.get("scenario"),
            "state_key": spec.get("state_key"),
            "review_note": spec.get("review_note"),
            "selection": copy.deepcopy(spec.get("voices")),
            "assembly_status": assembly_status,
            "assembly_reasons": assembly_reasons,
            "aggregation_status": ("RESOLVED" if aggregation_resolved == len(aggregation_results)
                                    else "UNRESOLVED"),
            "aggregation_reasons": sorted(set(aggregation_reasons)),
            "source_aggregation": aggregation_results,
            "gate": gated,
        })

    resolved = sum(item["gate"].get("status") == "RESOLVED" for item in results)
    assembly_resolved = sum(item["assembly_status"] == "RESOLVED" for item in results)
    aggregation_resolved = sum(item["aggregation_status"] == "RESOLVED" for item in results)
    return {
        "schema": 2,
        "status": "RESOLVED" if resolved == len(results) else "UNRESOLVED",
        "scope": "Review-only hand-authored Current Cameo plus three-reference scenario-aware gate with explicit per-source channel reduction; no source joins or writeback.",
        "method": [
            "Every voice is selected by manifest dataset and record_index.",
            "Manifest expected fields are identity guards only; they do not match voices or infer joins.",
            "DTA_BASE_CHANNELS_RESOLVED is admitted only through the assembler's explicit selection alias, with raw status retained.",
            "Each assembled group uses scenario_policy=True and voice_policy=True; missing or unresolved inputs remain unresolved.",
            "Each source is reduced from its explicit channel_terms when available; selected-record fallback is retained as a named limitation.",
            "Channel sums are checked against the adapter's selected-record terms before the gate; clamped, direct and ambient evidence stays separate.",
            "Arithmetic/geometric means are diagnostic summaries; no balance values are emitted or written.",
            "Current Cameo votes require a verified original-channel binding. Reconstruction evidence may live in a separate manifest contract; never edit the immutable actor snapshot or substitute a later live dataset.",
        ],
        "manifest": {
            "scope": copy.deepcopy(manifest.get("scope")),
            "policy": copy.deepcopy(manifest.get("policy")),
        },
        "inputs": copy.deepcopy(input_provenance or {}),
        "current_cameo_self_vote_binding": binding,
        "summary": {
            "groups": len(results),
            "assembly_resolved": assembly_resolved,
            "aggregation_resolved": aggregation_resolved,
            "aggregation_unresolved": len(results) - aggregation_resolved,
            "gate_resolved": resolved,
            "gate_unresolved": len(results) - resolved,
        },
        "groups": results,
    }


def render_markdown(document):
    summary = document.get("summary") or {}
    binding = document.get("current_cameo_self_vote_binding") or {}
    scenario_policies = {}
    for item in document.get("groups", []):
        scenario = item.get("scenario")
        policy = (item.get("gate") or {}).get("policy") or {}
        name = policy.get("scenario_policy_name")
        mapping = policy.get("axis_mapping")
        if scenario and name:
            scenario_policies.setdefault(scenario, (name, mapping))
    lines = [
        "# Explicit four-voice pilot gate",
        "",
        "**Review-only.** The manifest supplies every record index and group key.",
        "DTA base-channel admission is explicit and raw status remains visible.",
        "No source join, normalization writeback or gameplay value is produced.",
        "",
        "## Summary",
        "",
        f"- Groups: **{summary.get('groups', 0)}**; assembly resolved: **{summary.get('assembly_resolved', 0)}**; channel aggregation resolved: **{summary.get('aggregation_resolved', 0)}**; gate resolved: **{summary.get('gate_resolved', 0)}**; gate unresolved: **{summary.get('gate_unresolved', 0)}**.",
        f"- Permanent Current Cameo self-vote binding: **{binding.get('status', 'UNRESOLVED')}** ({binding.get('basis') or binding.get('reason') or 'no evidence'}).",
        "- Scenario policies:",
    ]
    recovery = document.get("frozen_input_recovery") or {}
    if recovery:
        lines.insert(-1, f"- Archived actor-stat inputs verified: **{recovery.get('matched_inputs', 0)}/{recovery.get('expected_inputs', 0)}**. This does not certify original per-armor channels.")
    for scenario in sorted(scenario_policies):
        name, mapping = scenario_policies[scenario]
        lines.append(f"  - **{scenario}** (`{name}`): {mapping}")
    lines += [
        "- Voice policy: one Current Cameo row plus exactly three distinct reference voices at equal 0.25 weight.",
        "",
        "| comparison | status | voices | reasons |",
        "|---|---|---|---|",
    ]
    for item in document.get("groups", []):
        gated = item.get("gate") or {}
        voices = ", ".join(gated.get("sources", []))
        reasons = list(item.get("assembly_reasons", [])) + list(gated.get("reasons", []))
        reason_text = "; ".join(dict.fromkeys(reasons)) or "—"
        lines.append(
            f"| {item.get('comparison_id', '—')} | {gated.get('status', '—')} | {voices or '—'} | {reason_text.replace('|', r'\\|')} |"
        )
    coverage = document.get("candidate_coverage")
    if isinstance(coverage, Mapping):
        coverage_summary = coverage.get("summary") or {}
        lines += [
            "",
            "## Candidate roster disposition",
            "",
            f"- Actor rows accounted: **{coverage_summary.get('accounted_actor_rows', 0)}/{coverage_summary.get('required_actor_rows', 0)}**; explicit manifest groups: **{coverage_summary.get('explicit_manifest_groups', 0)}** across **{coverage_summary.get('explicit_manifest_actors', 0)}** actors.",
            f"- Explicit N/A dispositions: **{coverage_summary.get('explicit_not_applicable', 0)}**. Missing channels or scenarios remain unresolved rather than inferred as N/A.",
            "",
            "| actor | disposition | explicit groups | current channels | reference voices |",
            "|---|---|---|---:|---:|",
        ]
        for actor in coverage.get("actors", []):
            group_ids = ", ".join(
                str(group.get("comparison_id"))
                for group in actor.get("explicit_groups", [])) or "—"
            lines.append(
                f"| `{actor.get('actor')}` | {actor.get('disposition')} | {group_ids} | "
                f"{actor.get('current_cameo_channel_count', 0)} | "
                f"{actor.get('reference_voice_count', 0)} |"
            )
    lines += [
        "",
        "Resolved means are diagnostic only; target eligibility, cadence, secondary payloads, runtime applicability and gameplay review remain separate.",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--cameo", type=Path, default=DEFAULT_CAMEO)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--dta", type=Path, default=DEFAULT_DTA)
    parser.add_argument("--cameo-baseline", type=Path, default=DEFAULT_CAMEO_BASELINE)
    parser.add_argument("--frozen-input-root", type=Path, default=DEFAULT_FROZEN_INPUT_ROOT)
    parser.add_argument("--coverage-matrix", type=Path,
                        default=DEFAULT_COVERAGE_MATRIX)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)
    try:
        out_path = diagnostic_output.validate_path(ROOT, args.out)
        markdown_path = (diagnostic_output.validate_path(ROOT, args.markdown)
                         if args.markdown else None)
        if markdown_path is not None and markdown_path == out_path:
            raise ValueError("JSON and Markdown outputs must use different resolved paths")
        manifest_path = args.manifest.resolve()
        if not manifest_path.is_file():
            raise ValueError("manifest does not exist: " + str(manifest_path))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        datasets, dataset_documents, provenance = {}, {}, {}
        for name, path in (("cameo", args.cameo), ("reference", args.reference), ("dta", args.dta)):
            path = path.resolve()
            if not path.is_file():
                raise ValueError(f"{name} input does not exist: {path}")
            document, records = _load_records(path)
            datasets[name] = records
            dataset_documents[name] = document
            provenance[name] = {"path": str(path), "sha256": _sha256(path),
                                "records": len(records),
                                "document_schema": document.get("schema")}
        baseline_path = args.cameo_baseline.resolve()
        if not baseline_path.is_file():
            raise ValueError("Cameo baseline does not exist: " + str(baseline_path))
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        if not isinstance(baseline, Mapping) or not isinstance(baseline.get("rows"), list):
            raise ValueError("Cameo baseline rows must be a list")
        from reference_targets import FROZEN_CAMEO_SHA256
        if _sha256(baseline_path) != FROZEN_CAMEO_SHA256:
            raise ValueError("permanent Cameo actor snapshot changed")
        provenance["current_cameo_baseline"] = {
            "path": str(baseline_path),
            "sha256": _sha256(baseline_path),
            "captured_at": baseline.get("captured_at"),
            "rows": len(baseline["rows"]),
            "scope": baseline.get("scope"),
        }
        provenance["manifest"] = {"path": str(manifest_path),
                                   "sha256": _sha256(manifest_path),
                                   "groups": len(manifest.get("groups", []))
                                   if isinstance(manifest, Mapping) else None}
        provenance["tools"] = {
            str(Path(__file__).resolve()): _sha256(Path(__file__).resolve()),
            str(Path(coverage_inventory.__file__).resolve()):
                _sha256(Path(coverage_inventory.__file__).resolve()),
        }
        self_vote_binding = verify_current_cameo_binding(
            baseline,
            dataset_documents.get("cameo"),
            provenance["cameo"]["sha256"],
            binding_contract=(manifest.get("policy") or {}).get("current_cameo_channel_vote"),
            baseline_sha256=provenance["current_cameo_baseline"]["sha256"],
            evidence_root=ROOT,
        )
        result = build_document(
            manifest, datasets, input_provenance=provenance,
            self_vote_binding=self_vote_binding,
        )
        result["frozen_input_recovery"] = recover_frozen_input_evidence(
            baseline, args.frozen_input_root)
        coverage_path = args.coverage_matrix.resolve()
        if not coverage_path.is_file():
            raise ValueError("coverage matrix does not exist: " + str(coverage_path))
        coverage_matrix = json.loads(coverage_path.read_text(encoding="utf-8"))
        result["inputs"]["coverage_matrix"] = {
            "path": str(coverage_path),
            "sha256": _sha256(coverage_path),
            "rows": len(coverage_matrix.get("rows", []))
            if isinstance(coverage_matrix, Mapping) else None,
        }
        result["candidate_coverage"] = coverage_inventory.reconcile_candidate_coverage(
            coverage_matrix, manifest, self_vote_binding)
        outputs = {out_path: json.dumps(result, indent=2, ensure_ascii=False,
                                        allow_nan=False) + "\n"}
        if markdown_path is not None:
            outputs[markdown_path] = render_markdown(result)
        diagnostic_output.write_outputs(ROOT, outputs)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(result["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
