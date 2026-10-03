"""Assemble explicitly selected four-voice rows for the review gate.

The assembler is deliberately narrower than a source joiner.  Callers provide
the dataset name and record index for every voice, together with the group
comparison/scenario/state metadata.  No actor, weapon, scenario or state is
matched or inferred from the selected records.  The result can be passed to
``four_source_synthesis_gate.combine_group`` after the caller has reviewed the
retained raw evidence.
"""
from __future__ import annotations

import copy
from collections import Counter
from collections.abc import Mapping


REFERENCE_SOURCES = (
    "Combined Arms",
    "OpenRA Red Alert",
    "OpenRA Tiberian Dawn",
    "DTA Enhanced",
)
CURRENT_VOICE = "Current Cameo"
ALLOWED_VOICES = frozenset((CURRENT_VOICE, *REFERENCE_SOURCES))
IDENTITY_FIELDS = (
    "channel_identity",
    "identity",
    "actor",
    "source_actor",
    "reference_id",
    "id",
    "slot",
    "weapon",
    "warhead",
)
SCHEMA = 1
_MISSING = object()

# The DTA adapter deliberately uses a stronger status name than the generic
# gate.  It has resolved authored base channels, but it does not certify the
# installed client's runtime applicability.  A caller may admit that one
# status only with this explicit, per-selection alias; no status is inferred
# from the source name or dataset.
STATUS_ALIASES = {
    "DTA_BASE_CHANNELS_RESOLVED": {
        "voice": "DTA Enhanced",
        "raw_status": "BASE_CHANNELS_RESOLVED",
        "projected_status": "RESOLVED",
        "basis": "DTA authored base channels resolved by the retained adapter; runtime applicability remains out of scope.",
    },
}


def _copy(value):
    return copy.deepcopy(value)


def _missing(value):
    return value is None or value == ""


def _same(left, right):
    try:
        return left == right
    except (TypeError, ValueError):
        return repr(left) == repr(right)


def _identity(record):
    """Copy only explicitly present identity fields without deriving one."""
    return {
        field: _copy(record[field])
        for field in IDENTITY_FIELDS
        if field in record
    }


def _selection_record(selection, datasets, index):
    reasons = []
    if not isinstance(selection, Mapping):
        return None, [f"selection_not_object:{index}"]

    voice = selection.get("voice", _MISSING)
    dataset_name = selection.get("dataset", _MISSING)
    record_index = selection.get("record_index", _MISSING)
    if voice is _MISSING or _missing(voice):
        reasons.append(f"voice_required:{index}")
    elif not isinstance(voice, str) or voice not in ALLOWED_VOICES:
        reasons.append(f"unsupported_voice:{voice!r}")
    if dataset_name is _MISSING or _missing(dataset_name):
        reasons.append(f"dataset_required:{index}")
    elif not isinstance(dataset_name, str):
        reasons.append(f"dataset_invalid:{dataset_name!r}")
    elif dataset_name not in datasets:
        reasons.append(f"dataset_missing:{dataset_name!r}")
    if record_index is _MISSING:
        reasons.append(f"record_index_required:{index}")
    elif isinstance(record_index, bool) or not isinstance(record_index, int):
        reasons.append(f"record_index_invalid:{index}")
    elif record_index < 0:
        reasons.append(f"record_index_negative:{index}")

    if reasons:
        return None, reasons

    records = datasets[dataset_name]
    if not isinstance(records, list):
        return None, [f"dataset_not_list:{dataset_name!r}"]
    if record_index >= len(records):
        return None, [f"record_index_out_of_range:{dataset_name!r}:{record_index}"]
    record = records[record_index]
    if not isinstance(record, Mapping):
        return None, [f"record_not_object:{dataset_name!r}:{record_index}"]
    return record, []


def _source_matches(record, voice, index):
    """Validate declared source labels when a record supplies them.

    Current-Cameo reports use ``source: Cameo`` while the synthesis contract
    calls that voice ``Current Cameo``; both labels are accepted for that one
    explicit voice.  Missing source labels remain caller-owned evidence.
    """
    reasons = []
    for field in ("source", "voice"):
        if field not in record:
            continue
        actual = record[field]
        allowed = {voice}
        if voice == CURRENT_VOICE:
            allowed.add("Cameo")
        if not isinstance(actual, str) or actual not in allowed:
            reasons.append(f"{field}_mismatch:{index}:{actual!r}!={voice!r}")
    return reasons


def _record_axis_matches(record, selection, group, index):
    """Check optional raw axes without deriving or rewriting them.

    A reference report may use ``small_aircraft`` while the group policy uses
    ``aircraft``.  The caller can state that mapping with
    ``record_scenario``; otherwise a present raw scenario must equal the group
    scenario.  State keys follow the same explicit rule.
    """
    reasons = []
    for field, selection_field in (
        ("comparison_id", "record_comparison_id"),
        ("scenario", "record_scenario"),
        ("state_key", "record_state_key"),
    ):
        if field not in record:
            continue
        expected = selection.get(selection_field, group.get(field))
        if not _same(record.get(field), expected):
            reasons.append(f"record_{field}_mismatch:{index}")
    if "scenario" in selection and not _same(
            selection.get("scenario"), selection.get("record_scenario", group.get("scenario"))):
        reasons.append(f"selection_scenario_conflict:{index}")
    return reasons


def _status_resolution(record, voice, selection, index):
    """Resolve a status only through an explicit, whitelisted alias."""
    if not isinstance(record, Mapping):
        return "UNRESOLVED", None, []
    raw_status = record.get("status")
    if raw_status == "RESOLVED":
        if selection.get("status_alias") is not None:
            return "RESOLVED", None, [f"status_alias_unnecessary:{index}"]
        return "RESOLVED", None, []
    alias = selection.get("status_alias")
    if alias is None:
        return raw_status, None, []
    details = STATUS_ALIASES.get(alias)
    if details is None:
        return raw_status, None, [f"unsupported_status_alias:{alias!r}"]
    reasons = []
    if voice != details["voice"]:
        reasons.append(f"status_alias_voice_mismatch:{index}:{voice!r}")
    if raw_status != details["raw_status"]:
        reasons.append(
            f"status_alias_raw_status_mismatch:{index}:{raw_status!r}!={details['raw_status']!r}")
    if reasons:
        return raw_status, None, reasons
    return details["projected_status"], {
        "alias": alias,
        "raw_status": raw_status,
        "projected_status": details["projected_status"],
        "voice": voice,
        "basis": details["basis"],
    }, []


def _project_row(voice, selection, record, group, index, reasons, *,
                 effective_status=None, status_basis=None):
    raw = _copy(record) if isinstance(record, Mapping) else None
    row = {
        "source": _copy(voice),
        "comparison_id": _copy(group.get("comparison_id")),
        "scenario": _copy(group.get("scenario")),
        "state_key": _copy(group.get("state_key")),
        "status": (_copy(effective_status)
                   if effective_status is not None else
                   (_copy(record.get("status")) if isinstance(record, Mapping)
                    else "UNRESOLVED")),
        "terms": _copy(record.get("terms")) if isinstance(record, Mapping) else None,
        "raw_source": (_copy(record.get("source"))
                       if isinstance(record, Mapping) and "source" in record else None),
        "record_identity": _identity(record) if isinstance(record, Mapping) else {},
        "selection": _copy(selection),
        "raw_record": raw,
        "assembly_reasons": sorted(set(reasons)),
    }
    if isinstance(record, Mapping):
        row["raw_status"] = _copy(record.get("status"))
        if status_basis is not None:
            row["status_basis"] = _copy(status_basis)
        # Promote only explicit component evidence needed by the downstream
        # source reducer.  The raw record remains the authoritative copy.
        for field in ("clamped_hp_components", "direct_components",
                      "ambient_components", "direct_terms", "ambient_terms"):
            if field in record:
                row[field] = _copy(record[field])
        # Only an explicitly authored channel_identity/identity is promoted to
        # the gate's identity slot.  Actor/weapon fields remain provenance.
        if "channel_identity" in record:
            row["channel_identity"] = _copy(record["channel_identity"])
        elif "identity" in record:
            row["channel_identity"] = _copy(record["identity"])
    return row


def _unresolved_group(spec, source_rows, reasons, *, selections=None):
    return {
        "schema": SCHEMA,
        "comparison_id": _copy(spec.get("comparison_id")) if isinstance(spec, Mapping) else None,
        "scenario": _copy(spec.get("scenario")) if isinstance(spec, Mapping) else None,
        "state_key": _copy(spec.get("state_key")) if isinstance(spec, Mapping) else None,
        "status": "UNRESOLVED",
        "reasons": sorted(set(reasons)),
        "source_rows": _copy(source_rows),
        "selections": _copy(selections if selections is not None else
                             spec.get("voices") if isinstance(spec, Mapping) else None),
        "provenance": {
            "assembly": "caller-selected dataset and record_index",
            "joins": "disabled; no actor, weapon, scenario or state matching",
            "metadata": "caller-supplied comparison_id, scenario and state_key",
            "raw_records": "retained verbatim under each source row",
            "writeback": False,
        },
    }


def assemble_group(spec, datasets):
    """Project one explicit Aedis four-voice selection into gate rows.

    The function resolves only the selection/assembly layer.  It does not
    normalize armor axes or compute means; callers should pass the returned
    ``source_rows`` to the existing synthesis gate for that later check.
    """
    if not isinstance(spec, Mapping):
        return _unresolved_group({}, [], ["group_spec_not_object"])
    if not isinstance(datasets, Mapping):
        return _unresolved_group(spec, [], ["datasets_not_object"])

    reasons = []
    for field in ("comparison_id", "scenario", "state_key"):
        if _missing(spec.get(field)):
            reasons.append(f"{field}_required")
    selections = spec.get("voices")
    if not isinstance(selections, list):
        return _unresolved_group(spec, [], reasons + ["voices_not_list"])

    rows_by_voice = {}
    selected_keys = {}
    for index, selection in enumerate(selections):
        record, selection_reasons = _selection_record(selection, datasets, index)
        voice = (selection.get("voice") if isinstance(selection, Mapping)
                 else None)
        try:
            hash(voice)
            voice_key = voice
        except (TypeError, ValueError):
            voice_key = f"__invalid_voice_{index}"
        if voice_key in rows_by_voice:
            reasons.append(f"duplicate_voice:{voice}")
        row_reasons = list(selection_reasons)
        effective_status, status_basis, status_reasons = (
            _status_resolution(record, voice, selection, index)
            if record is not None and not selection_reasons
            else ("UNRESOLVED", None, []))
        if record is not None and not selection_reasons:
            row_reasons.extend(_source_matches(record, voice, index))
            row_reasons.extend(_record_axis_matches(record, selection, spec, index))
            row_reasons.extend(status_reasons)
            if effective_status != "RESOLVED":
                row_reasons.append(f"status_not_resolved:{index}:{record.get('status')!r}")
            if "terms" not in record or not isinstance(record.get("terms"), Mapping):
                row_reasons.append(f"terms_missing_or_invalid:{index}")
            dataset_name = selection.get("dataset")
            record_index = selection.get("record_index")
            if (dataset_name, record_index) in selected_keys:
                row_reasons.append(
                    f"duplicate_record_selection:{selected_keys[(dataset_name, record_index)]},{index}")
            else:
                selected_keys[(dataset_name, record_index)] = index
        elif record is None:
            row_reasons.extend(selection_reasons)

        row = _project_row(voice, selection, record, spec, index, row_reasons,
                           effective_status=effective_status,
                           status_basis=status_basis)
        # Keep the first row for a duplicate voice and retain later rows in the
        # evidence list; the group remains unresolved either way.
        if voice_key not in rows_by_voice:
            rows_by_voice[voice_key] = row
        else:
            rows_by_voice.setdefault("__duplicate_rows__", []).append(row)
        reasons.extend(row_reasons)

    if len(selections) != 4:
        reasons.append(f"voice_row_count:expected=4:actual={len(selections)}")
    current_count = sum(voice == CURRENT_VOICE for voice in rows_by_voice)
    if current_count != 1:
        reasons.append(f"current_voice_count:expected=1:actual={current_count}")
    reference_voices = [voice for voice in rows_by_voice
                        if isinstance(voice, str) and voice in REFERENCE_SOURCES]
    if len(reference_voices) != 3:
        reasons.append(f"reference_voice_count:expected=3:actual={len(reference_voices)}")
    unknown = [voice for voice in rows_by_voice
               if voice not in ALLOWED_VOICES and voice != "__duplicate_rows__"]
    reasons.extend(f"unsupported_voice:{voice!r}" for voice in unknown)

    order = [CURRENT_VOICE] + sorted(voice for voice in REFERENCE_SOURCES
                                     if voice in rows_by_voice)
    order.extend(sorted(
        (voice for voice in rows_by_voice
         if voice not in order and voice != "__duplicate_rows__"),
        key=repr,
    ))
    source_rows = [rows_by_voice[voice] for voice in order
                   if voice in rows_by_voice]
    source_rows.extend(rows_by_voice.get("__duplicate_rows__", []))
    if reasons:
        return _unresolved_group(spec, source_rows, reasons, selections=selections)

    return {
        "schema": SCHEMA,
        "comparison_id": _copy(spec["comparison_id"]),
        "scenario": _copy(spec["scenario"]),
        "state_key": _copy(spec["state_key"]),
        "status": "RESOLVED",
        "reasons": [],
        "source_rows": source_rows,
        "selections": _copy(selections),
        "provenance": {
            "assembly": "caller-selected dataset and record_index",
            "joins": "disabled; no actor, weapon, scenario or state matching",
            "metadata": "caller-supplied comparison_id, scenario and state_key",
            "raw_records": "retained verbatim under each source row",
            "status_aliases": "only caller-authored whitelisted aliases; raw status retained",
            "writeback": False,
        },
    }


def assemble_groups(specs, datasets):
    """Assemble a deterministic batch while retaining unresolved groups."""
    if not isinstance(specs, list):
        raise ValueError("group specs must be a list")
    results = [assemble_group(spec, datasets) for spec in specs]
    counts = Counter(result.get("status", "UNRESOLVED") for result in results)
    return {
        "schema": SCHEMA,
        "status": "RESOLVED" if not counts["UNRESOLVED"] else "UNRESOLVED",
        "scope": "Review-only explicit four-voice row assembly; no source joins or writeback.",
        "method": [
            "Every voice is selected by caller-supplied dataset and record_index.",
            "A group requires Current Cameo plus exactly three distinct reference voices.",
            "comparison_id, scenario and state_key come only from the group spec.",
            "Raw records and explicit identity fields are retained; no actor or weapon match is inferred.",
            "A DTA base-channel status is admitted only through the explicit DTA_BASE_CHANNELS_RESOLVED selection alias; raw status remains recorded.",
        ],
        "groups": results,
        "summary": {
            "groups": len(results),
            "resolved": counts["RESOLVED"],
            "unresolved": counts["UNRESOLVED"],
        },
    }


__all__ = [
    "ALLOWED_VOICES",
    "CURRENT_VOICE",
    "REFERENCE_SOURCES",
    "SCHEMA",
    "STATUS_ALIASES",
    "assemble_group",
    "assemble_groups",
]
