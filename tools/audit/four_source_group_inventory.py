"""Coverage inventory for an explicit four-voice synthesis input matrix.

This module is review-only.  It reports which reference voices are present in
a matrix and whether the matrix carries the metadata and resolved terms
needed by Aedis's four-voice synthesis gate (Current Cameo plus three
references).  It never infers actor or weapon joins, scenarios, state keys,
armor axes, damage, or vote weights.
"""
from __future__ import annotations

import copy
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path


SOURCES = (
    "Combined Arms",
    "OpenRA Red Alert",
    "OpenRA Tiberian Dawn",
    "DTA Enhanced",
)
REFERENCE_SOURCES = SOURCES
CURRENT_VOICE = "Current Cameo"
SCHEMA = 1


def _copy(value):
    return copy.deepcopy(value)


def _nonempty(value):
    return value is not None and value != ""


def _explicit_value(container, field):
    """Return a direct field only; no value is derived from another field."""
    if isinstance(container, Mapping) and field in container and _nonempty(container[field]):
        return container[field]
    return None


def _channel_count(reference, field):
    value = reference.get(field) if isinstance(reference, Mapping) else None
    return len(value) if isinstance(value, list) else 0


def _reference_summary(reference):
    if not isinstance(reference, Mapping):
        return {
            "source": None,
            "id": None,
            "status": None,
            "channel_count": 0,
            "selected_channel_count": 0,
            "valid_object": False,
        }
    return {
        "source": _copy(reference.get("source")),
        "id": _copy(reference.get("id")),
        "status": _copy(reference.get("status")),
        "channel_count": _channel_count(reference, "channels"),
        "selected_channel_count": _channel_count(reference, "selected_weapon_channels"),
        "valid_object": True,
    }


def _gate_metadata(actor_row, references, current_voice):
    """Check only direct, explicit group fields and source terms.

    A common field on the actor row is accepted only when every voice is
    otherwise silent on that field.  A voice-level field must be present and
    equal for every supplied voice; this is an explicit assertion, not a join.
    """
    fields = ("comparison_id", "scenario", "state_key")
    values = {}
    missing = []
    conflicts = []
    for field in fields:
        actor_value = _explicit_value(actor_row, field)
        voice_values = [_explicit_value(current_voice, field)] if isinstance(current_voice, Mapping) else []
        voice_values.extend(_explicit_value(ref, field) for ref in references
                            if isinstance(ref, Mapping))
        present = [value for value in voice_values if value is not None]
        if actor_value is not None and present and any(value != actor_value for value in present):
            conflicts.append(f"{field}_actor_reference_conflict")
            continue
        candidates = present or ([actor_value] if actor_value is not None else [])
        if not candidates:
            missing.append(field)
        elif any(value != candidates[0] for value in candidates[1:]):
            conflicts.append(f"{field}_mismatch")
        else:
            values[field] = _copy(candidates[0])

    terms_missing = []
    unresolved_terms = []
    if not isinstance(current_voice, Mapping):
        terms_missing.append(CURRENT_VOICE)
        unresolved_terms.append(CURRENT_VOICE)
    else:
        if not isinstance(current_voice.get("terms"), Mapping) or not current_voice.get("terms"):
            terms_missing.append(CURRENT_VOICE)
        if current_voice.get("status") != "RESOLVED":
            unresolved_terms.append(CURRENT_VOICE)
    for reference in references:
        source = reference.get("source") if isinstance(reference, Mapping) else None
        status = reference.get("status") if isinstance(reference, Mapping) else None
        terms = reference.get("terms") if isinstance(reference, Mapping) else None
        if not isinstance(terms, Mapping) or not terms:
            terms_missing.append(source)
        if status != "RESOLVED":
            unresolved_terms.append(source)
    return {
        "values": values,
        "missing_fields": missing,
        "conflicts": conflicts,
        "terms_missing_sources": [_copy(value) for value in terms_missing],
        "unresolved_sources": [_copy(value) for value in unresolved_terms],
    }


def _actor_record(row):
    if not isinstance(row, Mapping):
        return {
            "actor": None,
            "valid_object": False,
            "references": [],
            "source_presence": {source: 0 for source in SOURCES},
            "missing_sources": list(SOURCES),
            "duplicate_sources": [],
            "complete_four_source": False,
            "complete_four_voice": False,
            "current_voice_present": False,
            "gate_ready": False,
            "gate_blockers": ["actor_row_not_object"],
        }

    raw_references = row.get("references")
    references = raw_references if isinstance(raw_references, list) else []
    summaries = [_reference_summary(reference) for reference in references]
    counts = Counter(summary["source"] for summary in summaries)
    presence = {source: counts.get(source, 0) for source in SOURCES}
    missing = [source for source in SOURCES if not counts.get(source)]
    duplicate = [source for source in SOURCES if counts.get(source, 0) > 1]
    unknown = sorted((source for source in counts
                      if source not in SOURCES), key=lambda value: repr(value))
    complete = not missing and not duplicate and not unknown and len(references) == len(SOURCES)

    cameo_channels = row.get("cameo_channels")
    cameo_channel_count = len(cameo_channels) if isinstance(cameo_channels, list) else 0
    current_voice = row.get("current_voice")
    current_voice_present = cameo_channel_count > 0
    reference_count = len(references)
    reference_sources = [summary["source"] for summary in summaries]
    reference_distinct = {source for source in reference_sources
                          if source in REFERENCE_SOURCES}
    four_voice_complete = (
        current_voice_present
        and reference_count == 3
        and len(reference_distinct) == 3
        and all(source in REFERENCE_SOURCES for source in reference_sources)
        and not any(count > 1 for source, count in counts.items()
                    if source in REFERENCE_SOURCES)
    )

    reference_blockers = []
    reference_blockers.extend(f"missing_reference_source:{source}" for source in missing)
    reference_blockers.extend(f"duplicate_reference_source:{source}" for source in duplicate)
    reference_blockers.extend(f"unsupported_reference_source:{source!r}" for source in unknown)
    if not complete:
        reference_blockers.append("all_reference_sources_coverage_incomplete")

    blockers = []
    if not current_voice_present:
        blockers.append("missing_voice:" + CURRENT_VOICE)
    if reference_count != 3:
        blockers.append(f"reference_voice_count:expected=3:actual={reference_count}")
    blockers.extend(f"duplicate_reference_voice:{source}" for source in duplicate
                    if source in REFERENCE_SOURCES)
    blockers.extend(f"unsupported_reference_voice:{source!r}" for source in unknown)
    if not four_voice_complete:
        blockers.append("four_voice_coverage_incomplete")

    metadata = _gate_metadata(row, references, current_voice)
    if metadata["missing_fields"]:
        blockers.append("explicit_group_metadata_missing")
        blockers.extend(f"missing_group_field:{field}" for field in metadata["missing_fields"])
    blockers.extend(f"group_metadata_conflict:{reason}" for reason in metadata["conflicts"])
    if metadata["terms_missing_sources"]:
        blockers.append("resolved_terms_missing")
    if metadata["unresolved_sources"]:
        blockers.append("reference_status_not_resolved")

    gate_ready = four_voice_complete and not blockers
    return {
        "actor": _copy(row.get("actor")),
        "valid_object": True,
        "references": summaries,
        "current_voice": {
            "source": CURRENT_VOICE,
            "channel_count": cameo_channel_count,
            "status": (_copy(current_voice.get("status"))
                       if isinstance(current_voice, Mapping) else None),
            "valid_object": isinstance(current_voice, Mapping),
        },
        "source_presence": presence,
        "missing_sources": missing,
        "duplicate_sources": duplicate,
        "unsupported_sources": unknown,
        "complete_four_source": complete,
        "complete_four_voice": four_voice_complete,
        "current_voice_present": current_voice_present,
        "reference_voice_sources": sorted(reference_distinct),
        "reference_voice_count": reference_count,
        "reference_coverage_blockers": sorted(set(reference_blockers)),
        "gate_ready": gate_ready,
        "gate_blockers": sorted(set(blockers)),
        "explicit_group": {
            "comparison_id": metadata["values"].get("comparison_id"),
            "scenario": metadata["values"].get("scenario"),
            "state_key": metadata["values"].get("state_key"),
            "missing_fields": metadata["missing_fields"],
            "conflicts": metadata["conflicts"],
            "terms_missing_sources": metadata["terms_missing_sources"],
            "unresolved_sources": metadata["unresolved_sources"],
        },
    }


def _empty_result(reasons, *, matrix=None):
    return {
        "schema": SCHEMA,
        "status": "UNRESOLVED",
        "reasons": sorted(set(reasons)),
        "matrix": _copy(matrix),
        "actors": [],
        "summary": {
            "actors": 0,
            "complete_four_source": 0,
            "complete_four_voice": 0,
            "gate_ready": 0,
            "current_voice_present": 0,
            "missing_by_source": {source: 0 for source in SOURCES},
            "duplicate_by_source": {source: 0 for source in SOURCES},
            "status_counts": {},
            "channel_bearing_actors": 0,
            "selected_channel_bearing_actors": 0,
            "gate_blockers": {},
        },
    }


def inventory_matrix(matrix):
    """Return deterministic source-coverage evidence for one matrix object."""
    if not isinstance(matrix, Mapping):
        return _empty_result(["matrix_not_object"], matrix=matrix)
    rows = matrix.get("rows")
    if not isinstance(rows, list):
        return _empty_result(["rows_not_list"], matrix=matrix)

    actor_records = [_actor_record(row) for row in rows]
    actor_records.sort(key=lambda record: (str(record.get("actor")),
                                           not record.get("valid_object", False)))
    summary = {
        "actors": len(actor_records),
        "complete_four_source": sum(record["complete_four_source"] for record in actor_records),
        "complete_four_voice": sum(record["complete_four_voice"] for record in actor_records),
        "gate_ready": sum(record["gate_ready"] for record in actor_records),
        "current_voice_present": sum(record["current_voice_present"] for record in actor_records),
        "missing_by_source": {
            source: sum(source in record["missing_sources"] for record in actor_records)
            for source in SOURCES
        },
        "duplicate_by_source": {
            source: sum(source in record["duplicate_sources"] for record in actor_records)
            for source in SOURCES
        },
        "status_counts": dict(sorted(
            Counter(summary["status"] for record in actor_records
                    for summary in record["references"] if summary["status"] is not None).items(),
            key=lambda item: repr(item[0]))),
        "channel_bearing_actors": sum(
            any(summary["channel_count"] for summary in record["references"])
            for record in actor_records),
        "selected_channel_bearing_actors": sum(
            any(summary["selected_channel_count"] for summary in record["references"])
            for record in actor_records),
        "gate_blockers": dict(sorted(
            Counter(blocker for record in actor_records
                    for blocker in record["gate_blockers"]).items(),
            key=lambda item: item[0])),
        "reference_gate_blockers": dict(sorted(
            Counter(blocker for record in actor_records
                    for blocker in record["reference_coverage_blockers"]).items(),
            key=lambda item: item[0])),
    }
    return {
        "schema": SCHEMA,
        "status": "RESOLVED",
        "scope": _copy(matrix.get("scope")),
        "matrix_summary": _copy(matrix.get("summary")),
        "actors": actor_records,
        "summary": summary,
        "method": [
            "Source presence is counted from explicit reference.source values.",
            "Four-voice coverage requires one explicit Current Cameo channel-bearing row plus exactly three distinct reference.source values.",
            "Gate readiness additionally requires explicit comparison_id, scenario, state_key and nonempty RESOLVED terms on every voice; no fields are inferred.",
        ],
    }


def inventory_path(path):
    """Load a JSON matrix and return fail-closed inventory evidence."""
    path = Path(path)
    try:
        matrix = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return _empty_result([f"matrix_load_failed:{type(error).__name__}"])
    return inventory_matrix(matrix)


def _manifest_actor_groups(manifest):
    """Index explicitly guarded Current Cameo selections by actor."""
    by_actor = {}
    groups = manifest.get("groups") if isinstance(manifest, Mapping) else None
    for group in groups if isinstance(groups, list) else []:
        if not isinstance(group, Mapping):
            continue
        voices = group.get("voices")
        current = next((voice for voice in voices
                        if isinstance(voice, Mapping)
                        and voice.get("voice") == CURRENT_VOICE), None) \
            if isinstance(voices, list) else None
        expected = current.get("expected") if isinstance(current, Mapping) else None
        actor = expected.get("actor") if isinstance(expected, Mapping) else None
        if not isinstance(actor, str) or not actor:
            continue
        by_actor.setdefault(actor, []).append({
            "comparison_id": _copy(group.get("comparison_id")),
            "scenario": _copy(group.get("scenario")),
            "state_key": _copy(group.get("state_key")),
        })
    return by_actor


def reconcile_candidate_coverage(matrix, manifest, self_vote_binding):
    """Give every matrix actor a named, non-inferred coverage disposition."""
    inventory = inventory_matrix(matrix)
    if inventory.get("status") != "RESOLVED":
        return _empty_result(["candidate_matrix_inventory_unresolved"], matrix=matrix)
    groups_by_actor = _manifest_actor_groups(manifest)
    binding_status = (self_vote_binding.get("status")
                      if isinstance(self_vote_binding, Mapping) else "UNRESOLVED")
    rows = []
    matrix_actors = {row.get("actor") for row in inventory["actors"]}
    for actor in inventory["actors"]:
        actor_name = actor.get("actor")
        groups = groups_by_actor.get(actor_name, [])
        if groups:
            disposition = ("EXPLICIT_GROUPS_BOUND" if binding_status == "RESOLVED"
                           else "EXPLICIT_GROUPS_SELF_VOTE_UNBOUND")
        elif actor.get("complete_four_voice"):
            disposition = "THREE_REFERENCE_CANDIDATE_NEEDS_EXPLICIT_GROUP"
        elif actor.get("current_voice_present"):
            disposition = "UNRESOLVED_REFERENCE_COVERAGE"
        else:
            disposition = "UNRESOLVED_CURRENT_CAMEO_HP_CHANNEL"
        rows.append({
            "actor": actor_name,
            "disposition": disposition,
            "explicit_groups": _copy(groups),
            "current_cameo_channel_count": actor["current_voice"]["channel_count"],
            "reference_voice_count": actor["reference_voice_count"],
            "reference_voice_sources": _copy(actor["reference_voice_sources"]),
            "remaining_evidence": _copy(actor["gate_blockers"]),
        })
    disposition_counts = Counter(row["disposition"] for row in rows)
    manifest_missing = sorted(actor for actor in groups_by_actor
                              if actor not in matrix_actors)
    return {
        "schema": 1,
        "status": "REVIEW_ONLY",
        "scope": "Actor-level disposition for every four-faction candidate-matrix row. Scenario coverage is explicit only for reviewed manifest groups; no missing scenario or voice is inferred as N/A.",
        "current_cameo_self_vote_status": binding_status,
        "summary": {
            "required_actor_rows": len(rows),
            "accounted_actor_rows": len(rows),
            "explicit_manifest_groups": sum(len(value) for value in groups_by_actor.values()),
            "explicit_manifest_actors": len(groups_by_actor),
            "manifest_actors_missing_from_matrix": manifest_missing,
            "disposition_counts": dict(sorted(disposition_counts.items())),
            "explicit_not_applicable": 0,
        },
        "method": [
            "The 163-row candidate matrix defines the actor roster for this coverage receipt.",
            "Reviewed manifest membership comes only from the Current Cameo voice's explicit expected.actor guard.",
            "Rows outside the reviewed manifest remain named candidates or unresolved evidence; none is silently treated as equivalent or not applicable.",
        ],
        "actors": rows,
    }


__all__ = ["SOURCES", "inventory_matrix", "inventory_path",
           "reconcile_candidate_coverage"]
