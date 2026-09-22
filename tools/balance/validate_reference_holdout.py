#!/usr/bin/env python3
"""validate_reference_holdout.py — bounded, read-only withheld-reference validation of the
reference-forecasting METHOD. A diagnostic, never live balance.

Aedis-approved suggestion 5 (2026-09-09): hold out one assigned reference source/axis per
trial, predict the withheld reference value from the actor's OTHER assigned sources, and
compare two log-ratio errors on the withheld value.

  prediction  — `reference_targets.target_for` exactly as the R4 pipeline runs it, but with
                the entire withheld SOURCE removed from the voices (not just one id), the
                withheld actor's whole `reference_targets.expand_families` family removed
                from every calibration population BEFORE any aggregate is computed, the
                withheld source's own calibration aggregates as the projection ruler, and
                NO Cameo current-stat input anywhere (target_for's peers-only leg; the
                withheld axis value is stripped before the row is ever passed).
  baseline    — the withheld source's heldout-excluded TYPE population median, the simplest
                guess available with the same information removed.

Error metric: log(predicted / actual) — dimensionless, so scale invariance holds.
A trial with exactly one remaining voice is reported as a LOW-EVIDENCE diagnostic, never
multi-source evidence; source count is not proof of independent lineage. No pass threshold
of any kind is applied: this measures method error and the baseline comparison, not proof
the game is balanced.

Scope: classic original Cameo actors — TD GDI, TD Nod, RA1 Allies, RA1 Soviets — classified
original via `build_reference_report.is_original`, strictly joined on source+ID through
`faction_extrapolate.paired_rows`; missing or ambiguous joins are refused, never guessed.
Axes: hp, speed, cost only — weapon statistics are incomplete in the legacy extract and are
deliberately not validated here.

Deterministic external-only output via `diagnostic_output.write_outputs` (exclusive
creation; never overwrites a differing existing artifact); in-repository paths are refused.
Source inputs are fingerprinted before and after the run through
`build_japan_pilot.input_fingerprints`; any change refuses the evidence.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import pathlib
import statistics
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "audit"))
import build_japan_pilot as fingerprint_module          # noqa: E402
import build_reference_report as brr                    # noqa: E402
import diagnostic_output                                # noqa: E402
import faction_extrapolate as fe                        # noqa: E402
import faction_routes as fr                             # noqa: E402
import reference_distribution as rd                     # noqa: E402
import reference_targets as rt                          # noqa: E402

ROOT = rd.ROOT
OUT_BASENAME = "reference_holdout_validation"
ASSIGN = ROOT / "docs" / "balance" / "derived" / "reference_assignment.json"

CLASSIC_FACTIONS = ("td_gdi", "td_nod", "ra1_allies", "ra1_soviets")
HOLDOUT_AXES = ("hp", "speed", "cost")
MIN_CALIBRATION_POP = 5          # a ruler population of two medians is not a distribution
DEFAULT_ACTOR_CAP = 20
MAX_ACTOR_CAP = 100

NOTES = (
    "bounded read-only diagnostic; this is NOT a calibration, a sign-off, or a live rebalance",
    "multi-source trials (>= 2 voices) are still method-error diagnostics — two voices do "
    "NOT mean verified calibration",
    "single-voice trials are low-evidence diagnostics with exactly one voice; they are "
    "not multi-source evidence — source count is not proof of independent lineage",
    "the signed median log-ratio is BIAS, not typical error; typical error is the median "
    "absolute log error, reported for prediction and baseline separately",
    "no pass threshold is applied anywhere; the artifact measures method error and the "
    "type-median baseline comparison only",
    "axes are hp/speed/cost only: weapon statistics are incomplete in the legacy extract "
    "and are deliberately not validated here",
    "results are log ratios against withheld reference values; they measure how the "
    "cross-source pooling transfers, never what a Cameo unit should be",
)


def log_error(predicted, actual):
    """log(predicted) - log(actual): the same log ratio, computed overflow-safe.

    A ratio can overflow to inf or underflow to 0 for perfectly representable inputs;
    a difference of logarithms cannot."""
    return math.log(predicted) - math.log(actual)


def refuse_evidence_change(before, after):
    """The input-fingerprint gate: a mid-run change of any consumed input refuses the run."""
    if before != after:
        differing = sorted(key for key in set(before) | set(after)
                           if before.get(key) != after.get(key))
        raise ValueError("input fingerprints changed during collection — evidence refused "
                         "for: " + ", ".join(differing))


def clamp_actor_cap(value):
    """The deterministic actor cap: default 20, hard ceiling 100 (time/memory bound)."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return DEFAULT_ACTOR_CAP
    if value < 0:
        return DEFAULT_ACTOR_CAP
    return min(value, MAX_ACTOR_CAP)


def positive_number(value):
    """True only for a real, finite, strictly positive non-bool number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if not math.isfinite(value) or value <= 0:
        return False
    return True


def classic_actors(result):
    """[(cid, record)] — the classic original actors, scope-checked, sorted (deterministic)."""
    out = []
    for cid, record in result.items():
        if fr.faction_of(cid) not in CLASSIC_FACTIONS:
            continue
        if not brr.is_original(record):
            continue
        out.append((cid, record))
    return sorted(out)


def round_robin_actors(result, cap):
    """(selected cids, selected per faction, excluded by cap) — deterministic ROUND ROBIN
    across the four classic factions, taken level by level in declared faction order, so a
    small cap never degenerates into one alphabetical slice of the scope."""
    queues = collections.defaultdict(list)
    for cid, _record in classic_actors(result):
        queues[fr.faction_of(cid)].append(cid)
    in_scope = sum(len(queue) for queue in queues.values())
    selected, selected_by_faction, depth = [], collections.Counter(), 0
    while len(selected) < cap and depth < max((len(q) for q in queues.values()), default=0):
        for faction in CLASSIC_FACTIONS:
            if len(selected) >= cap:
                break
            if depth < len(queues[faction]):
                selected.append(queues[faction][depth])
                selected_by_faction[faction] += 1
        depth += 1
    return selected, dict(sorted(selected_by_faction.items())), in_scope - len(selected)


def self_fingerprint():
    """sha256 of THIS module — the imported pilot helper does not fingerprint it."""
    return hashlib.sha256(pathlib.Path(__file__).resolve().read_bytes()).hexdigest()


def trial_list(cids, pairs):
    """[(cid, source)] — one candidate holdout per strictly-joined assigned source, sorted."""
    return [(cid, src) for cid in cids for src in sorted(pairs.get(cid, {}))]


def calibration_rows(peers, family):
    """The corpus with the held actor's whole expanded reference family removed.

    Removed by OBJECT IDENTITY — the family rows are the corpus's own dict objects, so the
    withheld unit (its assigned row and every variant, in every source) is absent from the
    calibration populations while any aggregate over them is computed."""
    removed = {id(row) for row in family}
    return [row for row in peers if id(row) not in removed]


def calibration_distribution(calib_rows):
    """{source: {population: {stat: aggregates}}} — the leakage-free calibration corpus."""
    dist = rd.build_distributions(calib_rows)
    rt.add_cost_distribution(dist, calib_rows)
    return dist


def partner_rows(family, held_source):
    """The actor's reference rows from every source EXCEPT the held-out one.

    The entire source is excluded from the voices, not just the one assigned id — any other
    row of that source is the same game's opinion and must not vote either."""
    return [row for row in family if row["source"] != held_source]


def score_trial(cid, held_source, axis, held_row, family, calib):
    """(record, None) for a scored trial — or (None, refusal reason).

    The prediction is `reference_targets.target_for`'s PEERS-ONLY leg (the Cameo-vote leg is
    never read) run on the positive partner rows against the calibration distributions,
    with the withheld source's heldout-excluded aggregates as the projection ruler — so the
    coordinate machinery lands the prediction in the withheld source's own units, where the
    withheld actual lives. `held_view` strips the axis value itself: no withheld current
    statistic enters the prediction, and no Cameo row is ever passed."""
    if not positive_number(held_row.get(axis)):
        return None, "invalid_withheld_value"
    partners = partner_rows(family, held_source)
    if not partners:
        return None, "no_remaining_voice"
    positive_partners = [row for row in partners if positive_number(row.get(axis))]
    if not positive_partners:
        return None, "partners_lack_axis"
    ruler = calib.get(held_source) or {}
    for pop in ("overall", held_row.get("type")):
        agg = ruler.get(pop, {}).get(axis)
        if agg is None or agg.get("n", 0) < MIN_CALIBRATION_POP:
            return None, "thin_population:" + str(pop)
    held_view = dict(held_row)
    held_view[axis] = None
    predicted, _, voices = rt.target_for(positive_partners, held_view, axis, calib, ruler)
    if predicted is None or not positive_number(predicted):
        return None, "degenerate_prediction"
    held_value = float(held_row[axis])
    baseline = ruler[held_row["type"]][axis]["median"]
    if not positive_number(baseline):
        return None, "degenerate_baseline"
    prediction_lr = log_error(predicted, held_value)
    baseline_lr = log_error(baseline, held_value)
    return {
        "actor": cid,
        "held_source": held_source,
        "held_id": held_row.get("id"),
        "axis": axis,
        "type": held_row.get("type"),
        "held_value": held_value,
        "predicted": predicted,
        "type_median_baseline": baseline,
        "log_ratio": prediction_lr,
        "abs_log_error": abs(prediction_lr),
        "baseline_log_ratio": baseline_lr,
        "baseline_abs_log_error": abs(baseline_lr),
        "voices": voices,
    }, None


def axis_summary(records):
    """{axis: {...}} over multi-source (>= 2 voice) records only — descriptive measures,
    no threshold."""
    buckets = collections.defaultdict(list)
    for rec in records:
        buckets[rec["axis"]].append(rec)
    out = {}
    for axis in HOLDOUT_AXES:
        rows = buckets.get(axis, [])
        if not rows:
            continue
        lrs = [row["log_ratio"] for row in rows]
        abses = [row["abs_log_error"] for row in rows]
        blrs = [row["baseline_log_ratio"] for row in rows]
        babses = [row["baseline_abs_log_error"] for row in rows]
        wins = sum(1 for a, b in zip(lrs, blrs) if abs(a) < abs(b))
        out[axis] = {
            "tested": len(rows),
            # signed median = bias; the typical |error| sits beside it, never merged.
            "median_log_ratio": statistics.median(lrs),
            "median_abs_log_error": statistics.median(abses),
            "median_baseline_log_ratio": statistics.median(blrs),
            "median_baseline_abs_log_error": statistics.median(babses),
            "prediction_beats_baseline": wins,
            "beats_share": wins / len(rows),
        }
    return out


def low_evidence_summary(records):
    buckets = collections.defaultdict(list)
    for rec in records:
        buckets[rec["axis"]].append(rec)
    return {axis: {
        "count": len(rows),
        "median_log_ratio": statistics.median([row["log_ratio"] for row in rows]),
        "median_abs_log_error": statistics.median([row["abs_log_error"] for row in rows]),
    } for axis, rows in buckets.items()}


def holdout(pairs, attached, peers, held_actors, axes=HOLDOUT_AXES):
    """Run every (held actor, assigned source, axis) trial — pure and deterministic.

    Refusals and scored outcomes are both reported, and the totals reconcile:
    eligible = tested + held_low_evidence + excluded. Joins refused by
    `faction_extrapolate.paired_rows` never enter the eligible set."""
    totals = collections.Counter()
    excluded_reasons = collections.Counter()
    withheld_missing = collections.defaultdict(collections.Counter)
    multi_source, low_evidence, refused = [], [], []
    calibs = {}
    for cid in held_actors:
        joined = pairs.get(cid)
        if not joined:
            continue                                  # refused join: already surfaced
        family = attached[cid]
        if cid not in calibs:
            calibs[cid] = calibration_distribution(calibration_rows(peers, family))
        for held_source in sorted(joined):
            held_row = joined[held_source]
            for axis in axes:
                totals["eligible"] += 1
                rec, reason = score_trial(cid, held_source, axis, held_row, family, calibs[cid])
                if reason is not None:
                    totals["excluded"] += 1
                    excluded_reasons[reason] += 1
                    refused.append({"actor": cid, "held_source": held_source,
                                    "axis": axis, "reason": reason})
                    if reason == "invalid_withheld_value":
                        # the ACTUAL missing count in that source on that axis
                        withheld_missing[held_source][axis] += 1
                elif rec["voices"] < 2:
                    totals["held_low_evidence"] += 1
                    low_evidence.append(rec)
                else:
                    totals["tested"] += 1
                    multi_source.append(rec)
    return {
        "axes": list(axes),
        "totals": {key: totals[key] for key in
                   ("eligible", "tested", "held_low_evidence", "excluded")},
        "excluded_trials": refused,
        "excluded_reasons": dict(sorted(excluded_reasons.items())),
        "withheld_missing": {source: dict(sorted(counter.items()))
                             for source, counter in sorted(withheld_missing.items())},
        "multi_source": multi_source,
        "low_evidence": low_evidence,
        "multi_source_summary": axis_summary(multi_source),
        "low_evidence_summary": low_evidence_summary(low_evidence),
        "reconciles": totals["eligible"] == totals["tested"]
        + totals["held_low_evidence"] + totals["excluded"],
        "notes": NOTES,
        "sample_cap": {"held_out_actors": len(held_actors),
                       "actor_cap_default": DEFAULT_ACTOR_CAP,
                       "actor_cap_maximum": MAX_ACTOR_CAP},
    }


def join_summary(diagnostics):
    """{reason: count} from `faction_extrapolate.paired_rows` — every refused join named."""
    return dict(sorted((reason, len(entries))
                       for reason, entries in sorted((diagnostics or {}).items())))


def load_corpus():
    """Peers + assignment + strict source+ID joins + expanded families + join refusals."""
    peers = rd.peer_rows()
    result = json.loads(ASSIGN.read_text(encoding="utf-8"))["assignment"]
    diagnostics = {}
    pairs = fe.paired_rows(result, peers, diagnostics=diagnostics)
    attached = rt.expand_families({cid: list(rows.values()) for cid, rows in pairs.items()},
                                  peers)
    return peers, result, pairs, attached, join_summary(diagnostics)


def holdout_document(max_actors):
    """One full read-only run: fingerprints (corpus + this file), corpus, capped
    round-robin held-out sweep, fingerprints again. Any mid-run change of a consumed
    input — or of this module — refuses the evidence."""
    before = fingerprint_module.input_fingerprints()
    self_before = self_fingerprint()
    peers, result, pairs, attached, joins = load_corpus()
    cap = clamp_actor_cap(max_actors)
    held, selected_by_faction, excluded_by_cap = round_robin_actors(result, cap)
    doc = holdout(pairs, attached, peers, held)
    after = fingerprint_module.input_fingerprints()
    self_after = self_fingerprint()
    refuse_evidence_change(before, after)
    refuse_evidence_change({"validator_source": self_before},
                           {"validator_source": self_after})
    doc["scope"] = {
        "classic_factions": list(CLASSIC_FACTIONS),
        "selection": "deterministic round-robin across the four classic factions",
        "original_actors_in_scope": sum(selected_by_faction.values()) + excluded_by_cap,
        "actors_held_out": len(held),
        "selected_by_faction": selected_by_faction,
        "excluded_by_cap": excluded_by_cap,
        "actor_cap_applied": cap,
        "refused_joins": joins,
        "joined_sources": sorted({src for cid in held for src in pairs.get(cid, {})}),
    }
    doc["fingerprints"] = {
        "before": before,
        "after": after,
        "unchanged": before == after,
        "helper": "build_japan_pilot.input_fingerprints",
        "self_helper": "this module's own sha256 (not covered by the pilot helper)",
        "self_before": self_before,
        "self_after": self_after,
        "self_unchanged": self_before == self_after,
    }
    return doc


def resolve_outputs(out_dir, json_text, md_text):
    """External output directory ONLY — anything inside the repository is refused."""
    resolved = pathlib.Path(out_dir).expanduser().resolve()
    if ROOT in resolved.parents:
        raise ValueError("external output directory only — in-repository writes are refused "
                         "for this diagnostic")
    paths = {resolved / f"{OUT_BASENAME}.json": json_text,
             resolved / f"{OUT_BASENAME}.md": md_text}
    for path in paths:
        diagnostic_output.validate_path(ROOT, path)
    return paths


def render_report(doc):
    t = doc["totals"]
    out = ["# Reference holdout validation — bounded read-only diagnostic", ""]
    out += [f"> {note}" for note in doc["notes"]]
    out += ["", "## Totals (must reconcile)", "",
            "| eligible | tested (>= 2 voices) | held low-evidence | excluded |",
            "|--:|--:|--:|--:|",
            f"| {t['eligible']} | {t['tested']} | {t['held_low_evidence']} "
            f"| {t['excluded']} |",
            "", f"Totals reconcile: **{doc['reconciles']}**.", ""]
    joins = doc.get("excluded_reasons", {})
    if joins:
        out += ["Refusals by reason: " + ", ".join(
            f"`{reason}` {count}" for reason, count in sorted(joins.items())), ""]
    missing = doc.get("withheld_missing", {})
    if missing:
        out += ["Actual missing withheld values by held source (counted, not guessed):"]
        out += [f"- `{source}`: " + ", ".join(f"{axis} {count}"
                                              for axis, count in sorted(counter.items()))
                for source, counter in sorted(missing.items())]
        out.append("")
    out += ["## Tested multi-source diagnostics (>= 2 remaining voices)", ""]
    summary = doc["multi_source_summary"]
    if not summary:
        out += ["None.", ""]
    else:
        out += ["| axis | tested | median bias (signed) | median ABS log error "
                "| baseline median bias | baseline median ABS log error "
                "| prediction beats baseline | share |",
                "|---|--:|--:|--:|--:|--:|--:|--:|"]
        for axis, entry in summary.items():
            out.append(f"| {axis} | {entry['tested']} | "
                       f"{entry['median_log_ratio']:+.6f} | "
                       f"{entry['median_abs_log_error']:.6f} | "
                       f"{entry['median_baseline_log_ratio']:+.6f} | "
                       f"{entry['median_baseline_abs_log_error']:.6f} | "
                       f"{entry['prediction_beats_baseline']}/{entry['tested']} | "
                       f"{entry['beats_share']:.6f} |")
        out += ["", "Per trial:", ""]
        for rec in doc["multi_source"]:
            out.append(
                f"- `{rec['actor']}` — held out `{rec['held_source']}` "
                f"`{rec['axis']}`: actual {rec['held_value']:,.4g}; predicted "
                f"{rec['predicted']:,.4g} (log {rec['log_ratio']:+.4f}); type-median "
                f"baseline {rec['type_median_baseline']:,.4g} "
                f"(log {rec['baseline_log_ratio']:+.4f}); voices {rec['voices']}")
        out.append("")
    out += ["## Low-evidence diagnostics (exactly 1 remaining voice — NOT multi-source "
            "evidence)", ""]
    low = doc["low_evidence_summary"]
    if not low:
        out += ["None.", ""]
    else:
        out += ["| axis | count | median bias (signed) | median ABS log error |",
                "|---|--:|--:|--:|"]
        for axis, entry in low.items():
            out.append(f"| {axis} | {entry['count']} | "
                       f"{entry['median_log_ratio']:+.6f} | "
                       f"{entry['median_abs_log_error']:.6f} |")
        out.append("")
    out += ["## Excluded trials", ""]
    for rec in doc["excluded_trials"]:
        out.append(f"- `{rec['actor']}` `{rec['held_source']}` `{rec['axis']}`: "
                   f"`{rec['reason']}`")
    if not doc["excluded_trials"]:
        out.append("None.")
    out += ["", "## Boundaries", "",
            "- Held-out actors are chosen by deterministic round-robin across the four "
            "classic factions (cap default 20, hard maximum 100; no randomness, no "
            "sampling); the report shows the selected count per faction and how many "
            "fell beyond the cap.",
            "- Outputs are deterministic; an existing different artifact is never overwritten "
            "(exclusive creation via `diagnostic_output`).",
            "- Source inputs are fingerprinted before and after the run "
            "(`build_japan_pilot.input_fingerprints`) plus this module's own sha256; a "
            "change of either refuses the evidence.",
            "- There is no pass threshold in this report and nothing here proves any "
            "implementation, class, lineage or game balanced.",
            ""]
    return "\n".join(out)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out",
                        help="external output directory only (in-repository paths are refused)")
    parser.add_argument("--max-actors", type=int, default=DEFAULT_ACTOR_CAP,
                        help="held-out actor cap (default 20, hard maximum 100)")
    args = parser.parse_args(argv)

    try:
        doc = holdout_document(args.max_actors)
        doc["content_sha256"] = hashlib.sha256(
            json.dumps({k: v for k, v in doc.items() if k != "content_sha256"},
                       ensure_ascii=False, sort_keys=True)
            .encode("utf-8")).hexdigest()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
        return
    md = render_report(doc)
    if not args.out:
        print(md, end="")
        return 0
    json_text = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True,
                           allow_nan=False) + "\n"
    try:
        diagnostic_output.write_outputs(ROOT, resolve_outputs(args.out, json_text, md))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
