#!/usr/bin/env python3
"""Bounded DIAGNOSTIC Japan reference pilot — first testable pilot evidence, NOT a live rebalance.

For every Japan actor present in `reference_distribution.cameo_rows()` this shows the current
HP/speed/range/cost next to the R4 reference target, and derives an UNAPPROVED per-class
sensitivity from the classic originals (TD GDI/Nod, RA1 Allies/Soviets) only:

  * Donors are ORIGINAL actors (`build_reference_report.is_original`) of the four classic
    factions, strictly joined by source+ID through `faction_extrapolate.paired_rows` — the
    name fallback inside `reference_targets.attach` is deliberately NOT used.
  * The R4 target per axis is `reference_targets.target_for` over the strict rows and their
    `reference_targets.expand_families` families, against the `reference_distribution`
    aggregates (plus the cost distribution via `reference_targets.add_cost_distribution`).
  * Per current combat class (`class_membership.classify`) and axis, the exploratory ratio is
    the geometric mean over eligible donors of (R4 target / current). A pool needs
    >= 3 distinct donor originals from >= 2 classic factions, each donor axis value backed by
    >= 2 reference sources. No-class, support, pending-reclass and Japan donors are excluded;
    invalid/missing numbers are excluded per axis. Pools are built only for classes that
    actually occur among the Japan rows — deliberately bounded, no all-class sweep.
  * The ratio is applied ONLY to Japan's current HP/speed/range as UNAPPROVED sensitivity.
    One class ratio applied to every member preserves the existing relative positions inside
    the class; it does not invent an identity for Japan.

⛔ WHAT THIS IS NOT. Sensitivity only: this artifact proposes no price and changes no price —
the broader pipeline stays free to propose reference prices through its own authorized stages
(initial reference price placement, then joint stats-and-price grid fitting). None of that
happens here: no DPS target, no new-price target, no anchor fitted or signed, no apply
interface. The method preserves existing imbalances and is not proof against the reference.
Class tier, weapon structure and sign-off block application.

Output goes ONLY to an external directory through `diagnostic_output.write_outputs`,
deterministically (no timestamps, no fallbacks). Input provenance is fingerprinted
repo-relative for every file actually consumed — including the peer corpus, the Document-1
table, the extracted INI corpus, the ledger population and the code of the import closure —
and no lineage beyond that list is claimed. The pending-classes overlay is READ-ONLY input
(this tool never imports `pending_classes.py`, which writes files); an absent overlay is
reported as `NOT_CHECKED`, never as "no pending actors".

    python tools/balance/build_japan_pilot.py                       # report on stdout, no writes
    python tools/balance/build_japan_pilot.py --out <external dir>  # japan_reference_pilot.json/.md
    python tools/balance/build_japan_pilot.py --pending /tmp/pending_classes.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "audit"))

import build_reference_report as brr          # noqa: E402
import class_membership as cm                 # noqa: E402
import diagnostic_output                      # noqa: E402
import faction_extrapolate as fe              # noqa: E402
import faction_routes as fr                   # noqa: E402
import reference_distribution as rd           # noqa: E402
import reference_targets as rt                # noqa: E402

ROOT = rd.ROOT
ASSIGN = rt.ASSIGN

CLASSIC_FACTIONS = ("td_gdi", "td_nod", "ra1_allies", "ra1_soviets")
SUBJECT_FACTION = "japan"
AXES = ("hp", "speed", "w_range", "cost")
APPLY_AXES = ("hp", "speed", "w_range")
MIN_DISTINCT_DONORS = 3
MIN_DONOR_FACTIONS = 2
MIN_SOURCES_PER_AXIS = 2
OUT_BASENAME = "japan_reference_pilot"
AXIS_LABELS = (("hp", "hp"), ("speed", "speed"), ("w_range", "range"), ("cost", "cost"))
SENS_AXES = (("hp", "hp"), ("speed", "speed"), ("w_range", "range"))

LIMITATIONS = (
    "Sensitivity only: this diagnostic proposes no price and changes no price — the broader "
    "pipeline stays free to propose reference prices through its authorized stages.",
    "Preserves existing imbalances: one class ratio scales every member equally, keeping the "
    "current relative positions — it is NOT a proof against the reference.",
    "Class tier, weapon structure and sign-off block application; nothing here authorises a "
    "yaml change.",
    "No DPS targets, no anchors fitted or signed, no apply interface.",
    "A pool below the thresholds is THIN and withholds that axis rather than guessing.",
    "Per-axis (n) counts reference SOURCE votes — NOT independent lineage counts: family "
    "variants merge into one voice per source, and shared families vote once.",
    "No fitted proposal values until actual grid/weapon/tier evidence is supplied; the live "
    "pilot is NOT complete and this artifact must not be read as completed.",
    "Provenance covers the pilot's verified import and call graph, repo-relative: listed data "
    "files, ledgers, the derived assignment, the LIVE ruleset files via miniyaml's manifest, "
    "and the code closure. Anything not listed is not fingerprinted and no lineage beyond "
    "this verified list is claimed.",
    "The baseline pin is fingerprint-pinned INPUTS, not immutable data archival: the pinned "
    "run computes from byte-identical inputs, nothing archived is imported, and a mismatch "
    "refuses rather than reusing stale calibration.",
)

NOT_CHECKED = "NOT_CHECKED"

# ⛔ PROVENANCE IS VERIFIED, NOT ASSERTED — `test_import_closure_is_fully_fingerprinted`
# walks the actual module closure and refuses an unfingerprinted module. The list is the
# claim: the peer corpus and the hand-typed Document-1 table its loader re-parses
# (`reference_distribution.doc1_rows` -> `synthesize_reference.parse_doc1`), the extracted INI
# corpus and its armour normalisation (both read inside `peer_rows`), every ledger population
# `cameo_rows`/`class_membership.ledger_rows` reads, the one derived sidecar the strict join
# reads, the LIVE ruleset YAML (`rd.cameo_rows` resolves weapon ladders through the lazy
# `miniyaml.Ruleset` inside `cameo_weapon_ladders`, enumerated via miniyaml's own
# `load_manifest` chain), and the code files of the import closure.
PROVENANCE_DATA = (
    "docs/design/ORIGINAL_UNITS_PEER_OPENRA.md",
    "docs/design/ORIGINAL_UNITS_RAW.md",
    "docs/reference/ini_corpus.json",
    "docs/reference/armor_normalized.json",
    "docs/balance/derived/reference_assignment.json",
)
PROVENANCE_CODE = (
    "tools/balance/build_japan_pilot.py",
    "tools/balance/reference_distribution.py",
    "tools/balance/formula.py",
    "tools/balance/ini_cycle_evidence.py",
    "tools/balance/ini_range_evidence.py",
    "tools/balance/ini_weapon_selection.py",
    "tools/balance/peer_corpus.py",
    "tools/balance/peer_base_state.py",
    "tools/balance/peer_nominal_evidence.py",
    "tools/balance/peer_range_evidence.py",
    "tools/balance/reference_targets.py",
    "tools/balance/faction_extrapolate.py",
    "tools/balance/faction_routes.py",
    "tools/balance/class_membership.py",
    "tools/balance/build_reference_report.py",
    "tools/balance/synthesize_reference.py",
    "tools/balance/assign_references.py",
    "tools/balance/explain_unit.py",
    "tools/balance/reference_lineages.py",
    "tools/balance/diagnostic_output.py",
    # ⭐ THE PER-ARMAMENT PAIRING LANE ENTERED THIS CLOSURE, and the guard caught it rather than a
    # human noticing. `build_reference_report` imports `build_armament_pairing_report`, which
    # imports `armament_roles`, so both can change what the pilot reports and both must be
    # fingerprinted. Registering them is the fix; trimming the closure test would have been the
    # bug. (test_japan_pilot.InputFingerprintTests.test_import_closure_is_fully_fingerprinted)
    "tools/balance/build_armament_pairing_report.py",
    "tools/balance/armament_roles.py",
    "tools/audit/miniyaml.py",
)


def active_yaml_paths():
    """The LIVE ruleset files the pilot consumes through `reference_distribution`.

    `rd.cameo_rows` resolves weapon ladders via `miniyaml.Ruleset` (built lazily inside
    `cameo_weapon_ladders`), so the active YAML IS an input. Enumerated through miniyaml's
    OWN manifest machinery — `load_manifest` (mod.yaml + every Include'd content.yaml, the
    same chain the Ruleset merges) — never re-derived from a glob. Build failures raise
    instead of falling back: provenance must fail loudly, not silently shrink the claim.
    """
    import miniyaml
    manifest = miniyaml.load_manifest(ROOT)
    raw = [*manifest.rules, *manifest.weapons, *manifest.sequences, *manifest.sources]
    return sorted({p.relative_to(ROOT).as_posix() for p in raw if p.is_relative_to(ROOT)})


def _digest(name):
    try:
        return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    except OSError:
        return "MISSING"


def input_fingerprints(pending_path=None):
    """sha256 of every consumed input, keyed by path RELATIVE TO the repository.

    Data plus the code of the import closure plus the live ruleset files from miniyaml's
    manifest; anything else is not fingerprinted.
    """
    files = {name: _digest(name) for name in PROVENANCE_DATA}
    files.update({path.relative_to(ROOT).as_posix(): _digest(path.relative_to(ROOT).as_posix())
                  for path in rd.peer_corpus.input_paths(ROOT)})
    files.update({f"docs/balance/{p.name}": _digest(f"docs/balance/{p.name}")
                  for p in sorted((ROOT / "docs" / "balance").glob("*.json"))
                  if p.name != "class_anchors.json"})
    files.update({name: _digest(name) for name in active_yaml_paths()})
    files.update({name: _digest(name) for name in PROVENANCE_CODE})
    if pending_path is not None:
        try:
            files["pending_overlay"] = hashlib.sha256(
                pathlib.Path(pending_path).read_bytes()).hexdigest()
        except OSError:
            files["pending_overlay"] = "MISSING"
    return files


def input_evidence_changed(before, after):
    """The before/after fingerprint comparison backing the mid-collection refusal."""
    return before != after


def geo_spread(values):
    """Geometric standard deviation, the same law `faction_extrapolate.exchange_rates` uses
    for its exchange-rate spread: 1.0 means every value agrees on the scale. No confidence
    probability is built from it — it is reported, never acted on."""
    vals = [math.log(v) for v in values if v and v > 0]
    if len(vals) < 2:
        return None
    return math.exp(statistics.pstdev(vals))


def provenance_label(record):
    """original / analogue / unknown — from ACTUAL assignment metadata only.

    `is_original` (confidence STRONG/FAIR against an original-shipping source) proves the
    unit existed in the original game. A STRONG/FAIR match against only expansion mods is an
    ANALOGUE — a matched unit, not a proven original. Anything without a STRONG/FAIR record
    stays UNKNOWN: this diagnostic does not compute rank placements, so 'extrapolation' is
    never claimed from absent evidence.
    """
    if not isinstance(record, dict) or not record:
        return "unknown"
    if brr.is_original(record):
        return "original"
    if any((entry or {}).get("confidence") in ("STRONG", "FAIR")
           for entry in record.values()):
        return "analogue"
    return "unknown"


def source_disagreement(rows, cameo_row, axis, dist, cdist):
    """Per-source projected values and their geometric spread for one axis — pure reuse.

    The projected value per source is `reference_targets.target_for` called on THAT source's
    rows alone (same function, no second formula): its peers-only projection is what this
    source alone says, before the Cameo vote folds in. Disagreement is shown as the explicit
    per-source values, min/max range and geometric spread — never a fabricated confidence.
    Returns None below two reporting sources (nothing to disagree with).
    """
    sources = sorted({r["source"] for r in rows})
    if len(sources) < 2:
        return None
    values = {}
    for src in sources:
        peers_only, _with_cameo, _n = rt.target_for(
            [r for r in rows if r["source"] == src], cameo_row, axis, dist, cdist)
        if peers_only:
            values[src] = peers_only
    if len(values) < 2:
        return None
    ordered = [values[s] for s in sorted(values)]
    return {"values": {s: round6(v) for s, v in sorted(values.items())},
            "geo_spread": round6(geo_spread(ordered)),
            "min": round6(min(ordered)), "max": round6(max(ordered))}


def pin_baseline(path, doc):
    """Pin a previously captured pilot export: content-hash identity + fingerprint pin.

    The pin is INPUT FINGERPRINTS, not immutable data archival — the current run always
    recomputes, and the pinned calibration sections are cross-checked against that
    recomputation (byte-identical inputs make the two observationally identical; a
    neighbourhood mismatch despite matching fingerprints is a determinism failure and
    refuses).
    """
    raw_bytes = pathlib.Path(path).read_bytes()
    baseline = json.loads(raw_bytes.decode("utf-8-sig"))
    if (baseline.get("artifact") != OUT_BASENAME or baseline.get("unapproved") is not True
            or not isinstance(baseline.get("input_fingerprints"), dict)):
        raise ValueError("baseline must be a fingerprinted japan_reference_pilot export")
    if input_evidence_changed(baseline["input_fingerprints"], doc["input_fingerprints"]):
        raise ValueError("pinned input fingerprint mismatch — pinned inputs are NOT immutable "
                         "data archival; recompute the baseline on the current tree")
    for section in ("class_ratio_pools", "donors", "join_diagnostics"):
        if json.dumps(baseline.get(section), sort_keys=True, default=str) != \
                json.dumps(doc.get(section), sort_keys=True, default=str):
            raise ValueError(f"pinned baseline section {section} differs despite identical "
                             "input fingerprints — determinism invariant failed")
    return {"state": "PINNED", "content_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "note": "fingerprint-pinned inputs; the pilot recomputed from the identical "
                    "inputs and verified the pinned calibration — not archival reuse"}


def number(value):
    """float(value) when it is a finite positive number; None otherwise.

    Bools, non-finite floats, zero and negatives are all refusals — a bool is an int to
    Python and would silently read as 1, and a zero HP would read as a real measurement.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) and value > 0 else None


def round6(value):
    return None if value is None else round(float(value), 6)


def load_pending(path):
    """The optional C46 overlay (actor -> class, trailing '?' marks a contested reclass)."""
    if path is None:
        return {}
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise ValueError("pending overlay must be a JSON object of actor -> class string")
    return data


def donor_rejection(actor, faction, cls, pending):
    """Why this actor may not donate a ratio, or None when it may."""
    if faction == SUBJECT_FACTION:
        return "japan_donor"
    if faction not in CLASSIC_FACTIONS:
        return "faction_out_of_scope"
    if pending is not None:
        return "pending_reclass"
    if cls is None:
        return "no_class"
    if cls == "support":
        return "support_class"
    return None


def collect_axis_candidates(donors, axis, min_sources=MIN_SOURCES_PER_AXIS):
    """(candidates, skipped) for one axis — pure, no I/O.

    A donor = {actor, faction, current, target, n_sources, family_rows}. Invalid bool/
    non-finite/zero numbers, a missing per-axis value, and a source count below the floor are
    all SKIPPED WITH A REASON, never silently dropped and never replaced by a fallback.

    ⛔ ONE VOTE PER DONOR AND PER CONTRIBUTING AXIS REFERENCE. An actor appearing twice casts
    one ratio vote, not two (`duplicate_actor`). Reference identity is computed PER AXIS over
    the donor's CONTRIBUTING expanded family rows — a row that carries no positive value on
    this axis could not have pooled a coordinate for it (`target_for` skips it), so such a row
    reserves no vote (`irrelevant refs do not block`), while two donors whose EXPANDED FAMILY
    ROWS overlap on a row that does carry this axis's value are the same reference evidence
    (`duplicate_reference_vote`). `target_for` pools variants inside ONE source as one voice,
    so sharing a family row is what makes the vote shared, not sharing the joined id alone.
    """
    candidates, skipped = [], []
    seen_actors, seen_refs = set(), set()
    for donor in donors:
        actor = donor.get("actor")
        if actor in seen_actors:
            skipped.append({"actor": actor, "reason": "duplicate_actor"})
            continue
        raw_target = (donor.get("target") or {}).get(axis)
        if raw_target is None:
            skipped.append({"actor": actor, "reason": "no_reference_target"})
            continue
        target = number(raw_target)
        if target is None:
            skipped.append({"actor": actor, "reason": "invalid_target"})
            continue
        now = number((donor.get("current") or {}).get(axis))
        if now is None:
            skipped.append({"actor": actor, "reason": "invalid_current"})
            continue
        n = (donor.get("n_sources") or {}).get(axis)
        if not isinstance(n, int) or isinstance(n, bool) or n < min_sources:
            skipped.append({"actor": actor, "reason": "thin_sources", "n_sources": n})
            continue
        identity = {(row["source"], str(row.get("id")))
                    for row in (donor.get("family_rows") or ())
                    if isinstance(row, dict) and row.get("source")
                    and number(row.get(axis)) is not None}
        if identity & seen_refs:
            skipped.append({"actor": actor, "reason": "duplicate_reference_vote",
                            "shared": sorted(f"{s}:{i}" for s, i in identity & seen_refs)})
            continue
        seen_actors.add(actor)
        seen_refs |= identity
        candidates.append({"actor": actor, "faction": donor["faction"],
                           "ratio": target / now, "n_sources": n})
    return candidates, skipped


def pool_status(candidates):
    """THIN below the thresholds; otherwise the geometric mean of the donor ratios."""
    donor_ids = sorted({c["actor"] for c in candidates})
    factions = sorted({c["faction"] for c in candidates})
    base = {"donor_count": len(donor_ids), "faction_count": len(factions)}
    if len(donor_ids) < MIN_DISTINCT_DONORS or len(factions) < MIN_DONOR_FACTIONS:
        return {**base, "status": "THIN", "ratio": None}
    ratio = rd.gm([c["ratio"] for c in candidates])
    if ratio is None:
        return {**base, "status": "THIN", "ratio": None}
    return {**base, "status": "OK", "ratio": ratio}


def sensitivity(current, ratio):
    """current x ratio — the UNAPPROVED sensitivity value, preserving the current ordering."""
    return current * ratio


def subject_axis_state(cls, pending_class, current_value, pool):
    """One Japan row's state on one axis, holds before values.

    ⛔ `NOT_CHECKED` is not a pending reclass: with no overlay supplied, the pending C46
    truth is unknown, so the axis does NOT take a PENDING hold — it proceeds on the current
    class and the row itself carries `NOT_CHECKED` so no reader mistakes the absent overlay
    for "no pending actors".
    """
    if cls is None:
        return {"status": "NO_CLASS", "value": None}
    if pending_class == NOT_CHECKED:
        pending_class = None
    if pending_class:
        return {"status": "PENDING", "value": None}
    if current_value is None:
        return {"status": "MISSING_CURRENT", "value": None}
    if pool["status"] != "OK" or pool["ratio"] is None:
        return {"status": "THIN", "value": None}
    return {"status": "UNAPPROVED", "value": sensitivity(current_value, pool["ratio"])}


def class_map():
    klass = {}
    for actor, design in cm.ledger_rows():
        cls, _why = cm.classify(design)
        if cls:
            klass[actor] = cls
    return klass


def _load_inputs():
    peers = rd.peer_rows()
    cameo = rd.cameo_rows()
    dist = rd.build_distributions(peers)
    rt.add_cost_distribution(dist, peers)
    cdist = rt.cameo_context()
    assignment = json.loads(ASSIGN.read_text(encoding="utf-8-sig"))["assignment"]
    crows = {c["id"]: c for c in cameo}
    return peers, cameo, dist, cdist, assignment, crows


def _r4(attached_rows, cameo_row, axis, dist, cdist):
    """(cameo_inclusive, peers_only, n_sources) — both target views, one call, one formula."""
    peers_only, with_cameo, n_sources = rt.target_for(
        attached_rows, cameo_row, axis, dist, cdist)
    return with_cameo, peers_only, n_sources


def collect(pending_path=None):
    """The whole pilot over the real committed corpus, as one deterministic document.

    ⛔ INPUT STABILITY: the fingerprints are captured BEFORE any input is read and re-checked
    AFTER the whole collection — a change during collection raises and refuses the output
    rather than letting one run silently mix two input states.
    """
    fingerprints_before = input_fingerprints(pending_path)
    pending = load_pending(pending_path)
    if pending_path is None:
        overlay = {"state": NOT_CHECKED, "actors": None,
                   "note": "no overlay supplied — pending reclass holds were NOT evaluated"}
    else:
        overlay = {"state": "CHECKED", "actors": len(pending),
                   "sha256": fingerprints_before["pending_overlay"]}
    peers, cameo, dist, cdist, assignment, crows = _load_inputs()
    klass = class_map()

    scope = {actor: rec for actor, rec in assignment.items()
             if fr.faction_of(actor) in CLASSIC_FACTIONS + (SUBJECT_FACTION,)}
    notes = {}
    pairs = fe.paired_rows(scope, peers, notes)
    attached = rt.expand_families({cid: list(srcs.values()) for cid, srcs in pairs.items()}, peers)

    subjects = sorted(c["id"] for c in cameo if fr.faction_of(c["id"]) == SUBJECT_FACTION)
    subject_classes = sorted({klass.get(a) for a in subjects} - {None})

    donors, exclusions = [], {}
    for actor in sorted(scope):
        faction = fr.faction_of(actor)
        if faction not in CLASSIC_FACTIONS:
            continue
        if not brr.is_original(scope[actor]):
            exclusions[actor] = "not_original"
            continue
        cls = klass.get(actor)
        reject = donor_rejection(actor, faction, cls, pending.get(actor))
        if reject:
            exclusions[actor] = reject
            continue
        row = crows.get(actor)
        if row is None:
            exclusions[actor] = "not_in_cameo_population"
            continue
        current = {axis: row.get(axis) for axis in AXES}
        target, peer_target, n_sources = {}, {}, {}
        for axis in AXES:
            target[axis], peer_target[axis], n_sources[axis] = _r4(
                attached.get(actor) or [], row, axis, dist, cdist)
        disagreement = {axis: source_disagreement(
            attached.get(actor) or [], row, axis, dist, cdist) for axis in AXES}
        sources = {}
        for src, peer in sorted((pairs.get(actor) or {}).items()):
            sources[src] = {"id": peer.get("id"),
                            "confidence": (scope[actor].get(src) or {}).get("confidence"),
                            "family": sorted({str(r.get("id"))
                                              for r in (attached.get(actor) or [])
                                              if r["source"] == src
                                              and r.get("id") != peer.get("id")})}
        donors.append({"actor": actor, "faction": faction, "class": cls,
                       "provenance": provenance_label(scope.get(actor)),
                       "sources": sources,
                       "family_rows": [{"source": r["source"], "id": r.get("id"),
                                        "hp": r.get("hp"), "speed": r.get("speed"),
                                        "w_range": r.get("w_range"), "cost": r.get("cost")}
                                       for r in (attached.get(actor) or [])],
                       "current": {a: round6(current[a]) for a in AXES},
                       "target": {a: round6(target[a]) for a in AXES},
                       "peer_target": {a: round6(peer_target[a]) for a in AXES},
                       "source_disagreement": disagreement,
                       "n_sources": n_sources})

    for donor in donors:
        if donor["faction"] == SUBJECT_FACTION:
            raise ValueError(f"japan donor reached a pool: {donor['actor']}")

    pools = {}
    for cls in subject_classes:
        members = [d for d in donors if d["class"] == cls]
        per_axis = {}
        for axis in AXES:
            candidates, skipped = collect_axis_candidates(members, axis)
            state = pool_status(candidates)
            per_axis[axis] = {
                "status": state["status"], "ratio": round6(state["ratio"]),
                "ratio_spread": round6(geo_spread([c["ratio"] for c in candidates])),
                "donor_count": state["donor_count"], "faction_count": state["faction_count"],
                "donors": sorted(c["actor"] for c in candidates),
                "skipped": skipped,
            }
        pools[cls] = per_axis

    doc_donors = [{k: v for k, v in d.items() if k != "family_rows"} for d in donors]

    rows = []
    sens_counts = {a: {} for a in APPLY_AXES}
    default_pending = NOT_CHECKED if pending_path is None else None
    for actor in subjects:
        c = crows[actor]
        cls = klass.get(actor)
        pending_class = pending.get(actor, default_pending)
        per_axis = {}
        for axis in AXES:
            tgt, peer_tgt, n = _r4(attached.get(actor) or [], c, axis, dist, cdist)
            state = subject_axis_state(cls, pending_class, number(c.get(axis)),
                                       pools.get(cls, {}).get(axis, {"status": "THIN", "ratio": None})
                                       ) if axis in APPLY_AXES else None
            per_axis[axis] = {
                "current": round6(c.get(axis)),
                "r4_target": round6(tgt), "r4_peers_only": round6(peer_tgt),
                "r4_n_sources": n,
                "source_disagreement": source_disagreement(
                    attached.get(actor) or [], c, axis, dist, cdist),
                "pool": cls if axis in APPLY_AXES else None,
            }
            if state is not None:
                per_axis[axis]["sensitivity"] = {
                    "status": state["status"], "value": round6(state["value"]),
                    "hold": state["status"] in ("NO_CLASS", "PENDING", "THIN",
                                                "MISSING_CURRENT"),
                }
                key = state["status"]
                sens_counts[axis][key] = sens_counts[axis].get(key, 0) + 1
        joined = pairs.get(actor) or {}
        rows.append({
            "actor": actor, "type": c["type"], "class": cls, "pending_class": pending_class,
            "provenance": provenance_label(assignment.get(actor)),
            "axes": per_axis,
            "sources": sorted({p["source"] for p in (attached.get(actor) or [])}),
            "joined_reference_ids": {src: peer.get("id") for src, peer in sorted(joined.items())},
        })

    if input_evidence_changed(fingerprints_before, input_fingerprints(pending_path)):
        raise ValueError("input evidence changed during collection; retry on a stable tree")

    return {
        "artifact": OUT_BASENAME,
        "unapproved": True,
        "method": (
            "Sensitivity only — UNAPPROVED diagnostic evidence, no price proposed or changed "
            "here. Donors: ORIGINAL actors of td_gdi/td_nod/ra1_allies/ra1_soviets "
            "(build_reference_report.is_original), strictly joined by source+ID "
            "(faction_extrapolate.paired_rows — never a name fallback). Per axis TWO target "
            "views from the SAME call of reference_targets.target_for come back: r4_target "
            "(cameo-inclusive, R4 equal-thirds) and r4_peers_only (source-relative, no Cameo "
            "vote). Pool: per current combat class (class_membership.classify) and axis, the "
            "geometric mean of distinct donor R4/current ratios — one vote per donor actor, "
            "one per contributing per-axis reference (expanded family rows included). "
            "Provenance labels come from actual assignment metadata only "
            "(original/analogue, never extrapolated from absent evidence). Source "
            "disagreement is shown as explicit projected per-source values, min/max and "
            "geometric spread. Sensitivity: Japan current HP/speed/range x class ratio, "
            "UNAPPROVED."),
        "limitations": LIMITATIONS,
        "thresholds": {"min_distinct_donors": MIN_DISTINCT_DONORS,
                       "min_donor_factions": MIN_DONOR_FACTIONS,
                       "min_sources_per_axis": MIN_SOURCES_PER_AXIS,
                       "apply_axes": list(APPLY_AXES), "report_axes": list(AXES)},
        "pending_overlay": overlay,
        "baseline": {"state": "NOT_PINNED"},
        "stage": {
            "pilot": "sensitivity_only",
            "applied": None,
            "not_completed": True,
            "missing_evidence": "grid/weapon/tier evidence not supplied — no fitted proposal "
                                "values are emitted and the live pilot is NOT complete",
        },
        "input_fingerprints": fingerprints_before,
        "scope": {
            "classic_factions": list(CLASSIC_FACTIONS), "subject_faction": SUBJECT_FACTION,
            "subjects": len(rows),
            "donors_considered": len(donors),
            "donor_exclusions": {a: r for a, r in sorted(exclusions.items())},
            "subject_classes": subject_classes,
            "sensitivity_status_counts": {a: dict(sorted(sens_counts[a].items()))
                                          for a in APPLY_AXES},
        },
        "join_diagnostics": {k: len(v) for k, v in sorted(notes.items())},
        "class_ratio_pools": pools,
        "japan_rows": rows,
        "donors": doc_donors,
    }


def _fmt(value):
    return f"{value:,.0f}" if value is not None else "—"


def _fmt6(value):
    return f"{value:.6f}" if value is not None else "—"


def render_report(doc):
    """The deterministic markdown report — pure over the document, no clock, no environment."""
    out = []
    w = out.append
    w("# Japan reference pilot — bounded DIAGNOSTIC artifact (UNAPPROVED)")
    w("")
    w("First testable pilot evidence, NOT a live rebalance. Nothing here is applied, no anchor")
    w("is fitted or signed, and there is no apply interface. Every sensitivity below is")
    w("UNAPPROVED and withholds rather than guesses wherever its pool is thin.")
    w("")
    w("## Method")
    w("")
    w("- Donors: ORIGINAL actors (`build_reference_report.is_original`) of "
      + ", ".join(doc["scope"]["classic_factions"])
      + " present in `reference_distribution.cameo_rows()`.")
    w("- Join: strict source+ID via `faction_extrapolate.paired_rows` — never a name fallback.")
    w("- R4 target per axis: `reference_targets.target_for` over `reference_targets."
      "expand_families` of the strict rows, on the `reference_distribution` aggregates plus the "
      "cost distribution.")
    w("- Pools: per current combat class (`class_membership.classify`) and axis, the geometric "
      "mean of donor R4/current ratios, built ONLY for the classes that occur among the Japan "
      "rows.")
    w(f"- Thresholds: >= {doc['thresholds']['min_distinct_donors']} distinct donor originals "
      f"from >= {doc['thresholds']['min_donor_factions']} classic factions, each donor axis "
      f"value backed by >= {doc['thresholds']['min_sources_per_axis']} reference sources; "
      "no-class/support/pending-reclass donors and Japan donors excluded; invalid/missing "
      "numbers excluded per axis.")
    w("")
    w("## What this does NOT claim")
    w("")
    for line in doc["limitations"]:
        w(f"- {line}")
    w("")
    t = doc["thresholds"]
    pending_entry = doc.get("pending_overlay") or {"state": NOT_CHECKED, "actors": None}
    w(f"Scope: {doc['scope']['subjects']} Japan rows (none dropped), "
      f"{doc['scope']['donors_considered']} donors, "
      f"{len(doc['scope']['subject_classes'])} subject classes, "
      f"join diagnostics {doc['join_diagnostics']}.")
    w("")
    state = pending_entry["state"]
    if state == NOT_CHECKED:
        w(f"Pending C46 overlay: {NOT_CHECKED} — no overlay was supplied, so rows showing "
          "NOT_CHECKED are unverified, NOT known to have no pending reclass.")
    else:
        w(f"Pending C46 overlay: CHECKED — {pending_entry['actors']} pending actors supplied; "
          "a row with — was checked and has no pending reclass.")
    w("")
    w("## Japan roster")
    w("")
    w("| actor | prov | type | class | pending C46 | hp now | hp -> (n) | speed now "
      "| speed -> (n) "
      "| range now | range -> (n) | cost now | cost -> (n) | sens hp | sens speed | sens range |")
    w("|---|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for row in doc["japan_rows"]:
        def r4cell(axis):
            e = row["axes"][axis]
            if e["r4_target"] is None:
                return "—"
            spread = (e.get("source_disagreement") or {}).get("geo_spread")
            tag = f", x{spread:.2f}" if spread is not None else ""
            return _fmt(e["r4_target"]) + f" ({e['r4_n_sources']}{tag})"
        cells = [f"`{row['actor']}`", row.get("provenance") or "unknown", row["type"],
                 row["class"] or "—",
                 row["pending_class"] if row["pending_class"] else "—"]
        for axis, label in AXIS_LABELS:
            e = row["axes"][axis]
            cells += [_fmt(e["current"]), r4cell(axis)]
        for axis, label in SENS_AXES:
            s = (row["axes"][axis].get("sensitivity") or {})
            value = s.get("value")
            if s.get("status") == "UNAPPROVED":
                cells.append(_fmt(value))
            elif s:
                cells.append(s["status"])
            else:
                cells.append("—")
        w("| " + " | ".join(cells) + " |")
    w("")
    w("Sensitivity counts per axis: "
      + "; ".join(f"{axis}: {doc['scope']['sensitivity_status_counts'][axis]}"
                  for axis, _label in SENS_AXES) + ".")
    w("")
    w("## Class ratio pools (subject classes only)")
    w("")
    for cls in sorted(doc["class_ratio_pools"]):
        w(f"### {cls}")
        w("")
        w("| axis | status | ratio | spread | donors | donor factions | skipped |")
        w("|---|---|--:|--:|--:|--:|--:|")
        for axis in doc["thresholds"]["report_axes"]:
            p = doc["class_ratio_pools"][cls][axis]
            skip = "; ".join(f"{r} x{sum(1 for s in p['skipped'] if s['reason'] == r)}"
                             for r in sorted({s["reason"] for s in p["skipped"]}))
            spread = p.get("ratio_spread")
            w(f"| {axis} | {p['status']} | {_fmt6(p['ratio'])} "
              f"| {f'x{spread:.2f}' if spread is not None else '—'} | {p['donor_count']} "
              f"| {p['faction_count']} | {skip or '—'} |")
        w("")
        for axis in doc["thresholds"]["report_axes"]:
            p = doc["class_ratio_pools"][cls][axis]
            donors = ", ".join(p["donors"]) or "—"
            w(f"- {axis}: donors {donors}")
            for s in p["skipped"]:
                extra = f" (n_sources={s['n_sources']})" if "n_sources" in s else ""
                w(f"  - skipped {s['actor']}: {s['reason']}{extra}")
        w("")
    w("## Donors (exact sources)")
    w("")
    for d in doc["donors"]:
        refs = "; ".join(
            f"{src}:{entry['id']}" + (f" (+{len(entry['family'])} variants)" if entry["family"] else "")
            for src, entry in sorted(d["sources"].items())) or "— (no strict join)"
        w(f"- `{d['actor']}` ({d['faction']}, {d['class']}, {d.get('provenance') or 'unknown'}): {refs}")
    w("")
    w("## Donor exclusions")
    w("")
    for actor, reason in doc["scope"]["donor_exclusions"].items():
        w(f"- `{actor}`: {reason}")
    if not doc["scope"]["donor_exclusions"]:
        w("- none")
    w("")
    w("## Join diagnostics (strict source+ID)")
    w("")
    for reason, count in doc["join_diagnostics"].items():
        w(f"- {reason}: {count}")
    if not doc["join_diagnostics"]:
        w("- none")
    w("")
    w("## Input fingerprints (deterministic; no timestamps)")
    w("")
    w("Every input the pilot consumes, repo-relative — data plus the code of its import "
      "closure plus the live ruleset. Anything not listed is not fingerprinted and no "
      "lineage beyond this list is claimed.")
    w("")
    for name, digest in sorted(doc["input_fingerprints"].items()):
        w(f"- {name}: `{digest}`")
    w("")
    stage = doc.get("stage") or {}
    w("## Calibration stage")
    w("")
    w(f"- Sensitivity pilot: {stage.get('pilot', 'sensitivity_only')}; applied changes: "
      f"{stage.get('applied')}. The live pilot is NOT complete.")
    w(f"- {stage.get('missing_evidence')}")
    w("- Per-axis (n) counts reference SOURCE votes, which are NOT independent lineage "
      "counts: family variants merge into one voice per source and shared families vote "
      "once.")
    w("")
    b = doc.get("baseline") or {"state": "NOT_PINNED"}
    w("## Baseline pin and content identity")
    w("")
    content = doc.get("content_sha256")
    w(f"- content_sha256 (canonical payload): {content and '`' + content + '`'}")
    if b.get("state") == "PINNED":
        w(f"- BASELINE: PINNED ({b.get('content_sha256')}) — {b.get('note')}")
    else:
        w("- BASELINE: NOT PINNED — no captured export was supplied (--baseline); the pin is "
          "fingerprint-pinned inputs, NOT immutable data archival.")
    w("")
    return "\n".join(out)


def resolve_outputs(root, out_dir, json_text, md_text):
    """External output directory ONLY — anything inside the repository is refused."""
    resolved_root = pathlib.Path(root).resolve()
    resolved = pathlib.Path(out_dir).expanduser().resolve()
    if resolved == resolved_root or resolved_root in resolved.parents:
        raise ValueError("external output directory only — in-repository writes are refused "
                         "for this pilot")
    paths = {resolved / f"{OUT_BASENAME}.json": json_text,
             resolved / f"{OUT_BASENAME}.md": md_text}
    for path in paths:
        diagnostic_output.validate_path(root, path)
    return paths


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", help="external output directory for "
                                      f"{OUT_BASENAME}.json / .md (no in-repository path)")
    parser.add_argument("--pending", help="optional pending-classes overlay JSON "
                                          "(actor -> class, trailing '?' = contested)")
    parser.add_argument("--baseline", help="a previously captured pilot export to PIN "
                                           "against: input fingerprints must match byte-"
                                           "for-byte or the run refuses")
    args = parser.parse_args(argv)
    try:
        doc = collect(args.pending)
        if args.baseline:
            doc["baseline"] = pin_baseline(args.baseline, doc)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
        return
    payload = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True,
                         allow_nan=False) + "\n"
    doc["content_sha256"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    md = render_report(doc)
    if not args.out:
        print(md, end="")
        return 0
    payload = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True,
                         allow_nan=False) + "\n"
    try:
        diagnostic_output.write_outputs(ROOT, resolve_outputs(ROOT, args.out, payload, md))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
