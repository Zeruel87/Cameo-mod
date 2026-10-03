#!/usr/bin/env python3
"""Distribution-relative reference synthesis — the CHASSIS layer (HP, speed, turn rate).

PRIOR ART: `synthesize_reference.py` pools reference units as a ratio to each source's basic
RIFLEMAN. This replaces that transfer key rather than duplicating it — it imports that module's
document parsers and roster loader, and adds the distribution machinery the rifle method cannot
express. Weapons (damage, range, burst, reload, effective DPS) are a later layer, by maintainer
scoping; nothing here reads a weapon.

    python tools/balance/reference_distribution.py
    python tools/balance/reference_distribution.py --stat hp --type vehicle --limit 30

WHY THE RIFLE HAD TO GO (maintainer, 2026-08-30)
------------------------------------------------
*"What if that game doesn't have any infantry and only uses vehicles?"* — exactly. Anchoring every
comparison on one nominated actor has four failure modes, and this corpus hits all four:

  * a source with no infantry has no anchor at all;
  * "basic rifleman" is a different design object in each game — a 40 HP Marine, a 12,500 HP Light
    Infantry, a 125 HP Conscript — so the same ratio means different things;
  * one odd anchor silently rescales every unit measured against it;
  * it answers "how many riflemen is this worth", which is not a question anyone balances by.

The replacement is POSITION IN DISTRIBUTION. A unit is described by where it sits inside its
source's own spread, and that description is dimensionless, so it transfers to Cameo without ever
needing the two games to share a scale.

THE COORDINATE SYSTEM
---------------------
For each source S, each stat X, and each population P (the unit's TYPE, and the OVERALL combat
roster), compute five aggregates — min, max, median, arithmetic mean, geometric mean — and place
the unit against them:

    r_min = X/min · r_max = X/max · r_med = X/median · r_am = X/mean · r_gm = X/geomean
    p_rng = (X - min) / (max - min)                      # 0.0 at the floor, 1.0 at the ceiling

`p_rng` exists because ratios to MIN and MAX are not commensurate with the middle three: a source
whose floor is a 1 HP joke actor makes r_min read 35,000 while r_max reads 0.9. Keeping both means
the well-behaved coordinate is available when the ratio misbehaves, and the disagreement between
them is itself a signal that the source's floor or ceiling is junk.

SYNTHESIS
---------
Every coordinate is pooled across sources with the GEOMETRIC mean — these are ratios, and in ratio
space a source 2x high and one 2x low must cancel to 1.0, which only the geometric mean does.
`p_rng` is already bounded [0,1] and is pooled arithmetically; a geometric mean of a coordinate
that can legitimately be 0 is undefined.

⚠ NEVER GEOMETRIC-AVERAGE RAW STATS ACROSS SOURCES. 125 HP and 12,500 HP are the same design
intent at different scales; averaging them produces a number belonging to no game. Only the
dimensionless coordinates are pooled. This module never mixes raw values from two sources.

PROJECTION BACK
---------------
Each synthesized coordinate is multiplied by CAMEO's own matching aggregate, giving one candidate
absolute per coordinate; the final target is the geometric mean of those candidates. So a unit
that sits at 2.2x its source's vehicle median lands at 2.2x CAMEO's vehicle median.

⚠ THIS WRITES NO LEDGER, NO YAML AND NO ANCHOR. It is a measurement. The reference says what SHAPE
a unit has across the genre; `class_anchors` and Formula V2 still decide what Cameo ships, and
`docs/design/ORIGINAL_UNIT_STATS.md` is explicit that source games are an identity lookup, not a
prescription.
"""
import argparse
import collections
import json
import math
import re
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import reference_lineages  # noqa: E402  (the shared lineage rulings)
import peer_corpus  # noqa: E402
import peer_range_evidence  # noqa: E402
import ini_weapon_selection  # noqa: E402
import peer_nominal_evidence  # noqa: E402
import peer_base_state  # noqa: E402
import ini_range_evidence  # noqa: E402
import formula  # noqa: E402  (the canonical built-state condition evaluator)
import ini_cycle_evidence  # noqa: E402
import synthesize_reference as syn  # noqa: E402  (parsers + roster loader are reused wholesale)

ROOT = syn.ROOT
OUT_MD = ROOT / "docs" / "balance" / "REFERENCE_SYNTHESIS_REPORT.md"
OUT_JSON = ROOT / "docs" / "balance" / "derived" / "reference_distributions.json"
SIG_JSON = ROOT / "docs" / "balance" / "derived" / "reference_signatures.json"

# ── Lineage de-duplication (maintainer ruling, 2026-08-30) ────────────────────────────────────
# "RV is the OpenRA implementation of RA2 and YR so it already covers everything from the original
# RA2 and YR games ... there is no benefit in duplicating it."
#
# One vote per BALANCE LINEAGE, not per file. Measured before applying: the five vanilla copies
# agree with each other on 96% of shared units (118/123), which is what makes them one lineage.
# ⚠ Recorded caveat, because it is the maintainer's call and not the data's: RV is NOT a faithful
# copy. On the 86 units where the other copies agree and RV is present, RV is the SOLE dissenter
# on 39 of them (45%) — Kirov 32x vs 16x, Aegis Cruiser 3.2x vs 6.4x, Flak Track 2.4x vs 1.4x. So
# electing RV as the lineage's voice adopts RV's rebalance for those units rather than vanilla's
# consensus. That is a defensible choice (RV is the live, resolvable OpenRA codebase); it is just
# not a no-op, and this note exists so nobody later reads it as one.
# ⛔ A LINEAGE COLLAPSE **SELECTS** A REPRESENTATIVE. IT DOES NOT RELABEL AND MERGE.
# The first implementation renamed every RA2-family row to "Romanov's Vengeance", which quietly
# poured three rosters at INCOMPATIBLE SCALES into one distribution: RV runs 100..400,000 HP while
# OpenRA RA2 and YR-on-OpenRA run 25..2,000. The merged population's median/min came out at 100 —
# not because RV has a 100 HP prop (it has a Terror Drone, a perfectly legitimate unit) but
# because the low tail was full of Westwood-scale rows sitting under an OpenRA-scale ceiling.
# That is the exact failure this module's own header forbids: raw values from two sources must
# never share a statistic. Members are now DROPPED; only the representative's roster survives.
# ⛔ THIS LIST USED TO LIVE HERE, AND IT CARRIED A MEMBER THAT NEVER MATCHED: `"RA2/YR"`, while
# the parser labels that source `"RA2/YR (raw INI)"`. Three copies of the rulings existed and had
# drifted apart; they are now one, in `reference_lineages.py`, and `lineage_dedup.py` fails when a
# label there is absent from the corpus so the same typo cannot recur silently.
LINEAGE_MEMBERS = set(reference_lineages.superseded_map())

# ── THE POPULATION RULE (maintainer, 2026-08-30) ─────────────────────────────────────────────
# "Only use buildable units and no epic units with build limits! Only unlimited units / defenses
#  that can be built should be considered. Also Cameo's heroes and epic units must be excluded
#  since they will be balanced separately."
#
# So a row enters a distribution only if it is BUILDABLE and UNLIMITED. Three exclusions, and each
# has a distinct reason:
#
#   not buildable      — it never reaches a player's hands, so it is not part of the balance the
#                        roster expresses (husks, map props, campaign-only actors).
#   BuildLimit present — a one-off. `check_band.py:142` already defines Cameo's epic/hero
#                        predicate as exactly `bool(u.get("build_limit"))`, and that predicate is
#                        reused verbatim rather than restated.
#   epic_vehicle class — belt and braces on the Cameo side: an epic that somehow carries no
#                        build_limit is still an epic, and epics are balanced separately.
#
# ⚠ This is not merely a filter, it is a CORRECTION. Cameo's vehicle ceiling was a 3,000,000 HP
# epic, which made its max/median 35x against peers' 2.8-16x and inflated every projection through
# the max coordinate. Removing one-offs removes that distortion at the source rather than damping
# it downstream — which is why the percentile guard below is now a safety net rather than a crutch.
EXCLUDE_CLASSES = {"epic_vehicle"}

CHASSIS_STATS = ("hp", "speed", "turn_speed", "turn_ratio")

# ── The weapon layer, PART 1: the scale-free metrics ─────────────────────────────────────────
# These need no armor taxonomy, so they are measurable today. Armor-aware effective DPS is NOT
# here: across the 13 peers there are 76 distinct `Versus` tags and only FIVE — None, Light,
# Heavy, Wood, Concrete — are shared by six or more mods. Generals Alpha declares 37, some of them
# per-unit; OpenRA Dune II declares none; Dune 2000 ships both `none` and `None`. A universal
# mapping is not derivable from the data, so it must be hand-authored with per-source confidence.
# Shipping a guessed taxonomy would fabricate exactly the kind of number this project keeps
# getting burned by.
WEAPON_STATS = ("w_range", "w_damage", "w_burst", "w_reload", "w_dps")

# ── The weapon layer, PART 2: ARMOR-AWARE sustained output ───────────────────────────────────
# `dps_vs_<ladder>` = sustained DPS x that ladder's mean Versus fraction. Mapped to Cameo's FOUR
# LADDERS (DESIGN.md: INF None/Flak/Plate/Heroic · VEH Scout/Light/Medium/Heavy/Superheavy ·
# AIR Fighter/Bomber/Helicopter/Spaceship · BLD Wood/Concrete/Steel) rather than to its 16 rows,
# because most peers ship five or six tags in total. Claiming a peer's `Light` means Cameo's
# `Light` specifically would assert a precision no peer has; the ladder is the honest resolution
# and it is Cameo's own structure. The per-source tag mapping and its confidence live in
# `docs/reference/peer_armor_map.yaml` — data, because every entry is an arguable judgement.
ARMOR_STATS = ("dps_vs_INF", "dps_vs_VEH", "dps_vs_AIR", "dps_vs_BLD")
LADDERS = ("INF", "VEH", "AIR", "BLD")

# ── METRIC ELIGIBILITY CONTRACT ──────────────────────────────────────────────────────────────
# Every metric declares its own population predicate, because "which rows count" differs per stat
# and getting it wrong is silent. A unit with no weapon is not a unit with 0 DPS; a unit that
# cannot move is not a unit with speed 0. Folding those zeroes into a distribution drags every
# median and makes the geometric mean undefined outright.
#
#   zero_is_real  — is a literal 0 a meaningful value for this stat, or does it mean "absent"?
#   requires      — the row must have a positive value here to be eligible at all.
ELIGIBILITY = {
    "hp":         {"zero_is_real": False, "requires": "hp"},
    "speed":      {"zero_is_real": False, "requires": "speed"},
    "turn_speed": {"zero_is_real": False, "requires": "turn_speed"},
    "turn_ratio": {"zero_is_real": False, "requires": "turn_ratio"},
    "w_range":    {"zero_is_real": False, "requires": "w_dps"},
    "w_damage":   {"zero_is_real": False, "requires": "w_dps"},
    "w_burst":    {"zero_is_real": True,  "requires": "w_dps"},
    "w_reload":   {"zero_is_real": False, "requires": "w_dps"},
    "w_dps":      {"zero_is_real": False, "requires": "w_dps"},
    **{k: {"zero_is_real": False, "requires": k} for k in ARMOR_STATS},
}


def eligible(row, stat):
    """Does `row` belong in the population for `stat`? (see ELIGIBILITY)"""
    if row.get('reference_base_eligible') is False:
        return False
    # Cameo's ledger can aggregate several baseline armaments into one cycle-damage/rate total
    # while carrying Burst/Reload from only the selected primary. Those quantities do not form
    # one cadence and abstain from the one-armament component model. Peer rows omit this flag
    # because their extractor emits one selected weapon slot per row.
    if stat in WEAPON_STATS and row.get('weapon_model_eligible') is False:
        return False
    if stat == 'w_range' and 'w_range_usable' in row:
        # Independent, exact-row range proof never certifies damage or cadence.
        value = row.get(stat)
        return (row['w_range_usable'] is True
                and row.get('w_range_evidence') in (peer_range_evidence.VERDICT, peer_range_evidence.SELECTED_VERDICT, peer_nominal_evidence.RANGE_VERDICT, ini_range_evidence.VERDICT)
                and type(value) in (int, float) and math.isfinite(value) and value > 0)
    rule = ELIGIBILITY.get(stat)
    if not rule:
        return row.get(stat) is not None
    gate = row.get(rule["requires"])
    if gate is None or gate <= 0:
        return False
    v = row.get(stat)
    return v is not None and (v > 0 or rule["zero_is_real"])
POPULATIONS = ("infantry", "vehicle", "aircraft", "ship", "defense")
# Buildings are excluded from OVERALL: they are not mobile combat units, they outnumber everything
# else in most rosters (1,137 of 2,568 peer rows), and letting them in would drag every median.
COMBAT_TYPES = set(POPULATIONS)

ALL_STATS = CHASSIS_STATS + WEAPON_STATS + ARMOR_STATS

CAMEO_SECTION_TYPE = {"infantry": "infantry", "vehicles": "vehicle", "aircraft": "aircraft",
                      "naval": "ship", "defenses": "defense"}


def gm(values):
    vals = [v for v in values if v and v > 0]
    return math.exp(sum(math.log(v) for v in vals) / len(vals)) if vals else None


def aggregates(values):
    """min / max / median / arithmetic mean / geometric mean over the positive values."""
    vals = sorted(v for v in values if v is not None and v > 0)
    if len(vals) < 3:                     # a distribution needs a population, not two points
        return None
    def pct(q):
        i = min(len(vals) - 1, max(0, int(round(q * (len(vals) - 1)))))
        return vals[i]
    return {"n": len(vals), "min": vals[0], "max": vals[-1],
            "p05": pct(0.05), "p95": pct(0.95),
            "median": statistics.median(vals),
            "am": statistics.fmean(vals), "gm": gm(vals)}


def coordinates(x, agg):
    """The six dimensionless positions of `x` inside the distribution `agg`."""
    if not agg or x is None or x <= 0:
        return {}
    out = {"r_med": x / agg["median"] if agg["median"] else None,
           "r_am": x / agg["am"] if agg["am"] else None,
           "r_gm": x / agg["gm"] if agg["gm"] else None,
           # DIAGNOSTIC ONLY — see `project()` for why these do not vote.
           "d_min": x / agg["min"] if agg["min"] else None,
           "d_max": x / agg["max"] if agg["max"] else None}
    span = agg["p95"] - agg["p05"]
    out["p_rng"] = ((x - agg["p05"]) / span) if span > 0 else None
    return {k: v for k, v in out.items() if v is not None}


def project(coord, agg):
    """One candidate absolute per coordinate, on the target distribution `agg`.

    ⚠ RATIOS TO RAW MIN AND MAX DO NOT VOTE, and this was measured rather than assumed. Both ends
    of a roster are single actors, so both are hostage to one oddity:

      * Romanov's Vengeance lists a 100 HP vehicle. Its vehicle median/min is therefore **100**,
        where Combined Arms runs 12 and OpenRA RA 11.6 — so `x/min` for an ordinary RV tank is in
        the hundreds, and projecting that onto Cameo's floor inflated targets roughly tenfold.
      * Cameo's own vehicle ceiling is an epic at 3,000,000 HP, making its max/median **35x**
        against peers' 2.8-16x. `x/max` then projects onto a ceiling no peer roster has.

    The middle three — median, arithmetic mean, geometric mean — are central statistics and
    survive one bad row, so they carry the projection. The min-max IDEA is kept as `p_rng`, but
    measured between the 5th and 95th PERCENTILES rather than the raw extremes: that preserves
    "where in the spread does this sit" while denying any single prop or epic the power to define
    the span. `d_min`/`d_max` are retained in the signature purely as diagnostics — when they
    disagree wildly with the middle three, the source's floor or ceiling is junk.
    """
    if not agg:
        return {}
    out = {}
    for key, metric in (("r_med", "median"), ("r_am", "am"), ("r_gm", "gm")):
        if key in coord and agg.get(metric):
            out[key] = coord[key] * agg[metric]
    if "p_rng" in coord and agg.get("p95") is not None:
        span = agg["p95"] - agg["p05"]
        if span > 0:
            out["p_rng"] = agg["p05"] + coord["p_rng"] * span
    return out


# ── Document 1: the hand-extracted INI mods (maintainer ruling 2026-09-03) ────────────────────
# *"MO + CnCR now, originals later"*. Mental Omega and CnC Reloaded are Ares/YR mods with no
# resolvable checkout, so they exist only as hand-typed tables in ORIGINAL_UNITS_RAW.md. That
# document carries `kind` — the unit TYPE — which is what makes them usable here: the type half of
# the ten relative values needs a population per type, and DOC4's tables have no type column at all.
#
# ⭐ THE UNITS DO NOT NEED CONVERTING. Every coordinate is dimensionless and every distribution is
# built from ONE source's own values, so MO's damage in Westwood points and Combined Arms' in
# OpenRA points never meet. DOC1 measures range in CELLS and reload in FRAMES where DOC5 uses world
# distance and ticks; the ratios are identical either way.
#
# ⚠ THREE HONEST LIMITS, none of them silent:
#   * no `Turret`, `Burst` or armour columns -> these sources abstain on turn_ratio, w_burst and
#     every `dps_vs_*` coordinate rather than contributing a guess;
#   * `w_dps` is derived as Damage/Reload, which is proportional to real DPS within a source and
#     therefore fine for a ratio, but is NOT comparable to DOC5's measured DPS as a raw number;
#   * ⛔ NO BUILD-LIMIT COLUMN, so THE POPULATION RULE CANNOT BE FULLY APPLIED. DOC5 rows drop
#     one-off epics and heroes via `Limit`; these cannot, so a hero may sit inside MO's or CnCR's
#     distribution and stretch its tail. `cost > 0` removes the decoys and campaign props (MO lists
#     a "Decoy Quetzal Eyes" at cost 0, damage 1, range 1), which is the best proxy available.
DOC1_SOURCES = {"Mental Omega", "CnC Reloaded"}


# ── The INI corpus: the eight Westwood/Ares mods, machine-extracted ───────────────────────────
# `tools/reference/extract_ini_units.py` reads the rules files directly, so these eight sources
# arrive complete instead of hand-typed. This is the loader that was missing: the routes in
# `faction_routes.py` have named these sources since 2026-09-05 and `--check` reported every one
# of them as "not in the de-duplicated corpus", because nothing here read the file.
#
# ⭐ IT SUPERSEDES DOCUMENT 1 FOR THE SOURCES IT COVERS, and that is not bookkeeping.
# `ORIGINAL_UNITS_RAW.md` carries Mental Omega and CnC Reloaded as HAND-TYPED tables written when
# no extraction existed. Measured against the extracted corpus (2026-09-06):
#
#     CnC Reloaded  309 of 316 rows matched by name, median HP ratio 1.000, 6 rows off by <5%
#     Mental Omega  263 of 306 rows matched by name, median HP ratio 1.000, but 99 rows disagree
#
# and the MO disagreements are TYPOS, checked against the rules file itself: the table gives the
# Lionheart Bomber 10,000 HP where `[LIONH] Strength=800` (12.5x), and the Dunerider 10 HP where
# `[DUNE] Strength=150` (0.07x). A 12.5x row is not noise — it lands in the tail that `d_max` and
# `p95` are computed from, which is precisely where a distribution is most easily poisoned.
# So DOC1 yields per source, computed rather than hardcoded: add a source to the extractor and its
# hand-typed table stands down automatically.
INI_CORPUS = ROOT / "docs" / "reference" / "ini_corpus.json"
INI_ARMOR = ROOT / "docs" / "reference" / "armor_normalized.json"

# ⚠ VOCABULARY MISMATCH, AND IT IS SILENT. The corpus types naval units `naval`; the populations
# here are named `ship` (POPULATIONS, and `CAMEO_SECTION_TYPE` maps Cameo's own `naval` section to
# `ship` for exactly the same reason). A row typed `naval` matches no population, is excluded from
# `overall` because it is not in COMBAT_TYPES, and is measured against nothing at all — the same
# failure mode as the armed buildings filed under `building`, which cost 94 rows.
INI_TYPE = {"infantry": "infantry", "vehicle": "vehicle", "aircraft": "aircraft",
            "naval": "ship", "defense": "defense", "building": "building"}

# A6 (`REFERENCE_EXTRACTION_PLAN.md`): "confidence gates voting; only high/medium vote." A ladder
# normalised from a SINGLE declared rung is held flat across every rung by R8 and marked `low`;
# letting it vote would enter a value the peer never declared.
ARMOR_VOTING_CONFIDENCE = {"high", "medium"}


def _ini_armor_index():
    """(source, actor id) -> {ladder: mean Versus FRACTION}, high/medium confidence only."""
    if not INI_ARMOR.exists():
        return {}
    out = {}
    for line in INI_ARMOR.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        ladders = {}
        for lad, spec in (r.get("ladders") or {}).items():
            if spec.get("confidence") not in ARMOR_VOTING_CONFIDENCE:
                continue
            vals = [v for v in (spec.get("values") or {}).values() if isinstance(v, (int, float))]
            if not vals:
                continue
            # ⚠ Westwood writes Verses as a PERCENT (100 = full damage) and can write it negative
            # (a healing warhead). DOC5's `vs*` columns are FRACTIONS. Convert, and clamp the
            # negatives to 0 — `eligible()` requires dps_vs_* > 0, so a heal is an abstention.
            ladders[lad] = max(0.0, statistics.fmean(vals) / 100.0)
        if ladders:
            out[(r.get("source"), r.get("id"))] = ladders
    return out


# ── THE CONSUMER-SIDE EVIDENCE POLICY (2026-09-09) ────────────────────────────────────────────
# The extractor (`tools/reference/extract_ini_units.py`) declares, per weapon slot, whether the
# plain Damage/ROF fold may be CONSUMED: `w_evidence`, `w_evidence_reason` and `w_dps_usable`
# (explicit unsupported verdicts fail closed; unlabeled legacy data retains compatibility),
# and the slot-prefixed twins (`w2_*` = secondary, `wdummy_*` = demoted primary) carry the same
# identity/status pair for the row's OTHER weapon identities. Labels assert WHAT WAS ASSESSED,
# never completeness:
#
# ⛔ THE CONSUMER BUG THIS POLICY FIXES: `ini_rows` and `peer_hero_rows` copied `w_dps` and the
# armor-adjusted `dps_vs_*` while dropping `w_evidence` — so a weapon the extractor itself
# declined to certify arrived downstream as an authoritative DPS target with the caveat
# deleted. A ratio built from damage the direct-channel fold cannot read is exactly the class
# of number this file's own header forbids.
#
# What each state does to the CONSUMER values (`w_dps`, `dps_vs_*`). It touches NOTHING else —
# hp, speed, cost survive verbatim, the other weapon fields (`w_range`/`w_damage`/`w_burst`/
# `w_reload`, which matching clause 5 uses to tell "armed" from "unarmed") survive too, and
# ELIGIBILITY's `requires: w_dps` then naturally abstains the row from every weapon-layer
# distribution while it keeps voting on the chassis:
#   * MISSING/absent on a legacy row -> "legacy-unassessed": ABSENT STATUS IS LEGACY —
#     the boolean behaviour of the committed corpus is retained verbatim (compatibility)
#     and the label asserts nothing; it is NEVER certified complete;
#   * the extractor's own verdicts, matched EXACTLY: `nominal_direct` (underscore — its
#     declared contract: w_dps is the plain direct Damage/ROF estimate, never a proven
#     total) and `supported`/`conventional` -> unchanged numeric behaviour, labelled with
#     the verdict itself;
#   * "incomplete"/"unverified" -> WITHHELD: the raw direct estimate moves to `w_dps_raw`
#     (kept separately for inspection, voting nowhere) and `w_dps` plus every `dps_vs_*` is
#     withheld;
#   * an EXPLICIT `w_dps_usable: False` -> withheld as well, whatever the label says;
#   * any OTHER explicit status -> withheld too, labelled AS ITSELF, UNNORMALIZED. The
#     contract is exact-string: an arbitrary unknown status is never harmlessly normalised
#     into a trusted one nor folded into another verdict — coordination is conservative in
#     the direction of trust: an explicit verdict the consumer does not know
#     is not proven evidence. `evidence_counts` reports the mix so a rename upstream cannot
#     hide here silently.
#
# ⛔ THE SLOT PREFIX NEVER GATES THE PRIMARY. A `wdummy_evidence: incomplete` describes the
# DEMOTED weapon, not the one voted on here — DTA's X-O Power Suit: the promoted machine gun
# keeps its own evidence verdict, and no comment here calls the promoted result a complete
# UNIT measurement, because Westwood Primary/Secondary is TARGET-SELECTED and the tie the
# slots have to each other is unresolved at extraction. Each slot keeps its verdict; the
# unit-level fold is a later layer's decision. Evidence and diagnostics are CARRIED, never
# silently dropped.
LEGACY_EVIDENCE = "legacy-unassessed"
# ⛔ EXACT STRINGS — the extractor's FINAL vocabulary. `nominal_direct` is one token with an
# UNDERSCORE; a near-miss spelling (`nominal-direct`, `Nominal_Direct`) is NOT this verdict
# and is withheld, reported by `evidence_counts`, never silently normalised.
SUPPORTED_EVIDENCE = frozenset(("supported", "conventional", "nominal_direct"))
WITHHELD_EVIDENCE = frozenset(("incomplete", "unverified"))
# Evidence and status fields, per SLOT; and the UNFOLDED raw channel/provenance diagnostics.
# The extractor's `relabel_weapon` spells the slot twins `w2_*`/`wdummy_*` (prefix + k[2:] of
# the `w_*` keys, except `weapon` -> `<prefix>weapon`); identity fields ride along with the
# statuses. Nothing numeric travels under these keys.
EVIDENCE_SLOT_FIELDS = ("evidence", "evidence_reason", "dps_usable", "channel_ambiguity",
                        "weapon")
EVIDENCE_CHANNEL_FIELDS = ("ambient_damage", "railgun", "fire_particles", "spark_particles",
                           "particle_system", "attached_particle_system")
EVIDENCE_PASSTHROUGH = (
    "w_evidence", "w_evidence_reason", "w_dps_usable", "w_channel_ambiguity",
    "w_from_secondary", "w_demoted_primary",
    # legacy extractor spellings kept for older in-memory fixtures
    "w_dummy_primary", "w_railgun_projectile",
    *(f"w_{f}" for f in EVIDENCE_CHANNEL_FIELDS),
    *(f"{p}{f}" for p in ("w2_", "wdummy_")
      for f in EVIDENCE_SLOT_FIELDS + EVIDENCE_CHANNEL_FIELDS),
)


def evidence_status(wev):
    """The consumer's evidence label for one row's PRIMARY weapon — EXACT, never normalised.

    An absent/None status is legacy-unassessed: ABSENT STATUS IS LEGACY. The label asserts
    nothing about what was measured and is NEVER certified complete. Any explicit verdict
    travels through verbatim so near-miss spellings cannot smuggle themselves into a
    trusted class.
    """
    if not wev:
        return LEGACY_EVIDENCE
    return wev


def apply_weapon_evidence(row, rec):
    """Stamp `row` with `rec`'s weapon evidence; return the CONSUMER-side w_dps.

    SHARED by `ini_rows` and `peer_hero_rows` — one policy, not two copies that drift (three
    drifted copies of LINEAGE_MEMBERS is already on record here). Slot identity/status ride
    along; slot statuses never gate the primary. Returns the w_dps the row may vote with:
    the raw value when the evidence is legacy/absent or explicitly supported AND
    `w_dps_usable` is not an explicit False, None when withheld — in which case the raw
    direct estimate is retained on `row["w_dps_raw"]`.
    """
    for key in EVIDENCE_PASSTHROUGH:
        v = rec.get(key)
        if v is not None:          # a False travels too
            row[key] = v
    status = evidence_status(rec.get("w_evidence"))
    row["w_evidence"] = status
    if rec.get("w_dps_usable") is False:
        row["w_evidence_reason"] = (rec.get("w_evidence_reason")
                                    or f"dps_unusable: {status}")
    dps = row.get("w_dps")
    if (status in WITHHELD_EVIDENCE
            or (status != LEGACY_EVIDENCE and status not in SUPPORTED_EVIDENCE)
            or rec.get("w_dps_usable") is False):
        if dps is not None:
            row["w_dps_raw"] = dps
            row["w_dps"] = None
        return None
    return dps


def evidence_counts(rows):
    """Counter of evidence statuses over rows ALREADY IN MEMORY — no corpus re-read.

    A row with no extracted evidence field (Doc 1 / Doc 5 hand-or-doc rows) counts as
    legacy-unassessed, so the reporting is honest without an expensive all-corpus loop.
    """
    return collections.Counter(r.get("w_evidence") or LEGACY_EVIDENCE for r in rows)


# ── DOC 5 EVIDENCE COLUMNS (2026-09-10) ───────────────────────────────────────────────────────
# The Doc 5 emitter (`extract_peer_units.py`) appends `Evidence | Reason` to every table so the
# OpenRA peers can carry the SAME verdict vocabulary the INI corpus does (`nominal_direct` /
# `incomplete` + reason). The table parser lowercases header cells and strips backticks, so the
# parsed row dict `d` keys are `evidence` / `reason` / `usable`; this mapper turns one row into
# the canonical rec shape `apply_weapon_evidence` consumes. The policy, its exact-string
# vocabulary and its fail-closed direction are defined THERE — no second copy lives here.
#
# The `—` cell is the emitter's empty convention (`str(value or "—")`), NOT a status: a
# placeholder or blank cell maps to ABSENT, and absent is legacy-unassessed. A legacy table
# predating the columns has no `evidence` key at all — same destination — so the committed
# corpus keeps its numeric behaviour verbatim until it is regenerated.
#
# ⛔ `usable`, WHEN the column exists, is parsed STRICTLY: exactly `True`/`true` or
# `False`/`false`. A string "False" is a FALSE, never a truthy string, and any other non-empty
# token (`yes`, `1`, a typo) FAILS CLOSED: the fold is withheld (`w_dps_usable: False`) with a
# diagnostic reason, because a boolean the consumer cannot parse is not evidence the fold may
# be consumed. An absent column, `—` cell or blank cell carries no usable verdict at all and
# leaves the evidence label alone in charge. (An emitter that adds this column must write the
# token `False` explicitly — the `or "—"` placeholder pattern would swallow a Python False.)
DOC5_EMPTY_CELL = "—"
DOC5_USABLE_TOKENS = {"true": True, "True": True, "false": False, "False": False}


def doc5_evidence_record(d):
    """One Doc 5 row's evidence headers -> the rec `apply_weapon_evidence` consumes.

    Shared by `peer_rows` and the Doc 5 half of `peer_hero_rows` so both lanes map the
    headers identically; legacy tables (no such headers) map to an EMPTY rec, which the
    shared helper reads as legacy-unassessed with untouched numerics.
    """
    rec = {}
    ev = (d.get("evidence") or "").strip()
    if ev and ev != DOC5_EMPTY_CELL:
        rec["w_evidence"] = ev
    reason = (d.get("reason") or "").strip()
    if reason and reason != DOC5_EMPTY_CELL:
        rec["w_evidence_reason"] = reason
    if "usable" in d:
        cell = (d.get("usable") or "").strip()
        if cell and cell != DOC5_EMPTY_CELL:
            parsed = DOC5_USABLE_TOKENS.get(cell)
            if parsed is None:      # malformed -> fail closed, with the refusal's reason
                rec["w_dps_usable"] = False
                note = f"dps_unusable: malformed_usable_cell {cell!r}"
                rec["w_evidence_reason"] = (f"{rec['w_evidence_reason']}; {note}"
                                            if rec.get("w_evidence_reason") else note)
            else:
                rec["w_dps_usable"] = parsed
    return rec


def _ini_burst(rec):
    """An absent `Burst=` is ONE SHOT, not an unknown.

    ⭐ The maintainer spotted this from the map itself (2026-09-13): *"still shows that not all
    the references were used for the burst"*. `td_gdi_minigunner` read "2/3 sources used" on burst
    while reading 3/3 on everything else, because DTA Enhanced abstained.

    ⛔ THIS IS NOT AN INFERENCE — it makes the corpus self-consistent. `extract_ini_units` reads
    `num(w.get("Burst"))`, so a weapon that never declares the key records None. But that row's
    OWN rate was already computed as one shot per cycle: DTA's `E1` carries the working
    `15 x 1 / 21 mean ticks = 0.714286`. The row rated itself at burst 1 and then withheld burst
    as a stat nobody could vote on. Only TWO DTA rows declare `Burst=1` explicitly, which is
    exactly what an omitted default looks like — authors do not write defaults.

    ⚠ SCOPED TO ROWS THE CORPUS ITSELF TREATED AS ONE SHOT. Anything flagged `burst_unfolded`
    declared `Burst > 1` and had its cadence withheld for that reason; those keep abstaining, and
    a row with no usable rate has nothing to be consistent with. Measured across the corpus:
    2,315 rows over all nine INI sources qualify and NONE are `burst_unfolded`.

    ⚠ Done at LOAD time, never by regenerating `ini_corpus.json` — a full re-run of that
    extractor drops the weapon evidence on 63 rows.
    """
    burst = rec.get("w_burst")
    if burst is not None or not rec.get("w_dps"):
        return burst
    if "burst_unfolded" in str(rec.get("w_evidence_reason") or ""):
        return None
    return 1


def ini_rows(*, variants=False):
    """The eight Westwood/Ares mods in the peer-row shape, from `ini_corpus.json`.

    `variants=True` INVERTS the population rule below instead of applying it, returning the
    chassis variants `tools/reference/variant_pool.py` certifies — rows the rule drops that are
    still unit counterparts (DTA's `JEEPPTNK` "Rocket Hum-vee": a Hum-vee hull carrying `APTusk`
    instead of `RaiderCannon`, at TechLevel -1 so no sidebar ever offers it). Everything else
    about the row is identical — same evidence path, same armor index, same selection profile —
    so a variant row and an ordinary row are comparable by construction.

    ⛔ THESE ROWS ARE FOR `assign_references` ONLY, exactly as `peer_hero_rows()` is. A variant is
    by definition unbuildable, so putting one into a DISTRIBUTION would price a ceiling against a
    unit nobody can buy — the same error as letting a 3,000,000 HP epic back into the vehicle mean.
    """
    if not INI_CORPUS.exists():
        ini_rows.sources = set()
        return []
    variant_ids = None
    if variants:
        sys.path.insert(0, str(ROOT / "tools" / "reference"))
        import variant_pool
        variant_ids = {(v["source"], (v.get("id") or "")): v["variant_of"]
                       for v in variant_pool.classify()[0]}
    armor = _ini_armor_index()
    selection_profile = ini_weapon_selection.load(ROOT)
    out, sources = [], set()
    ini_range_profile = ini_range_evidence.load(ROOT)
    ini_cycle_profile = ini_cycle_evidence.load(ROOT)
    for line in INI_CORPUS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw_record = json.loads(line)
        r = ini_weapon_selection.select(raw_record, selection_profile)
        sources.add(r["source"])
        kind = INI_TYPE.get(r.get("type"))
        if kind is None:
            continue
        # THE POPULATION RULE, in full for the first time on these sources. DOC1 could only
        # approximate it — it has no build-limit column, so a hero could sit in the tail — and
        # said so. The corpus carries `build_limit`, so the epic/hero exclusion is exact here.
        # `buildable` is the extractor's TechLevel/Selectable verdict — see its comment. Without
        # it a costed 10,000,000 HP dummy sits in the arithmetic mean of a 443-unit population.
        if variants:
            # The inverted rule: certified chassis variants only, and nothing the rule keeps.
            if (r["source"], r.get("id", "")) not in variant_ids:
                continue
        elif not r.get("cost") or r.get("build_limit") or not r.get("buildable", True):
            continue
        spd, turn = r.get("speed"), r.get("turn_speed")
        row = {"source": r["source"], "raw_source": r["source"],
               "id": r.get("id", ""), "name": r.get("name", ""),
               "type": kind,
               # `Owner=` is a comma list; the extractor already joined it with "/" and the route
               # layer splits on that separator (`peer_factions`).
               "faction": r.get("faction", ""),
               "turreted": r.get("turreted"),
               "weapon": r.get("weapon"),
               "hp": r.get("hp"), "speed": spd,
               "turn_speed": turn,
               "turn_ratio": (spd / turn) if (spd and turn) else None,
               "cost": r.get("cost"),
               "w_range": r.get("w_range"), "w_damage": r.get("w_damage"),
               "w_burst": _ini_burst(r), "w_reload": r.get("w_reload"),
               "w_dps": r.get("w_dps")}
        # Evidence BEFORE any consumer value is derived from the DPS (shared helper; see
        # the policy block above `LEGACY_EVIDENCE`).
        dps = apply_weapon_evidence(row, r)
        ini_range_evidence.apply(row, raw_record, ini_range_profile)
        cycle_applied = ini_cycle_evidence.apply(row, raw_record, ini_cycle_profile)
        if cycle_applied:
            dps = row["w_dps"]
        if (r['source'], r['id']) in selection_profile:
            row.update({k: v for k, v in r.items() if k.startswith(('wdummy_', 'w2_'))})
        # The retained armor table describes the original weapon. Never apply
        # its coefficients to a newly selected secondary weapon.
        vs = {} if cycle_applied or (r['source'], r['id']) in selection_profile else armor.get((r["source"], r.get("id"))) or {}
        for lad in LADDERS:
            frac = vs.get(lad)
            row[f"dps_vs_{lad}"] = (dps * frac) if (dps and frac) else None
        if variant_ids is not None:
            # ⭐ CARRY THE BASE ID. This is the whole reason the variant lane can be DERIVED
            # rather than scored: `JEEPPTNK` knows it is a variant of `JEEP`, and `td_gdi_humvee`
            # already holds `JEEP`, so `td_gdi_humveemkii` -> `JEEPPTNK` follows without anyone
            # scoring "Rocket Hum-vee" against "humveemkii" (which lands at 0.545 — under the
            # 0.6 name bucket, so the greedy saw a tie at zero and handed the Hum-vee MkII a
            # Heavy Artillery instead).
            row["variant_of"] = variant_ids.get((r["source"], r.get("id", "")))
        out.append(row)
    ini_rows.sources = sources
    return out


def doc1_rows():
    """Mental Omega and CnC Reloaded in the peer-row shape, from Document 1."""
    out = []
    superseded = getattr(ini_rows, "sources", set())
    doc1_rows.superseded = sorted(DOC1_SOURCES & superseded)
    for source, r in syn.parse_doc1():
        if source not in DOC1_SOURCES or source in superseded:
            continue
        kind = (r.get("kind") or "").strip().lower()
        if kind not in COMBAT_TYPES and kind != "defense":
            continue
        hp, cost = syn.num(r.get("HP")), syn.num(r.get("Cost"))
        if not hp or not cost:                 # cost 0 == decoy / prop / not really built
            continue
        dmg, rld, rng = (syn.num(r.get(c)) for c in ("Dmg", "Rld", "Rng"))
        row = {"source": source, "raw_source": source,
               "id": r.get("Unit", ""), "name": r.get("Unit", ""),
               "type": kind, "turreted": None,
               "hp": hp, "speed": syn.num(r.get("Spd")),
               "turn_speed": None, "turn_ratio": None,
               "cost": cost,
               "w_range": rng, "w_damage": dmg, "w_burst": None, "w_reload": rld,
               "w_dps": (dmg / rld) if (dmg and rld) else None,
               # DOC1 alone carries a role and a best-guess Cameo template; DOC5 has neither, so
               # these two sources can answer the cascade's ROLE step where the other thirteen
               # cannot. Carried rather than dropped, and never inferred for the rest.
               "role": (r.get("Role") or "").strip(),
               "category": (r.get("**Category**") or "").strip()}
        for lad in LADDERS:
            row[f"dps_vs_{lad}"] = None        # no armour columns — abstain, never guess
        out.append(row)
    return out


# ⛔ AI-ONLY VARIANTS ARE NOT REFERENCES (maintainer, 2026-09-07). Several mods ship a duplicate
# actor that only the computer player can build — DTA's `TWR_AI`/`GUN1_AI`, CnC Reloaded's
# `NABNKR_AI` ("Soviet Battle Bunker (for AI)"), Red Resurrection's "AI ONLY" rows. They are
# balance crutches for the bot, not units a player ever faces on equal terms, and the real actor
# they shadow is sitting right next to them in the same source. The assignment was handing
# `td_gdi_guardtower` DTA's `TWR1_AI` while DTA's actual `TWR` went unused.
#
# ⚠ THE TEST MUST NOT BE `id.endswith("AI")`. Shattered Paradise's `ORCAI` is an Orca Interceptor
# and Combined Arms' `ZRAI` is a Zone Raider — real units whose names simply end in those letters.
# A separator before the suffix (`_AI`, `.AI`) is what marks the variant, and the mods that use a
# bare suffix say so in the NAME instead ("(AI)", "AI ONLY", "for AI").
_AI_ID = re.compile(r"[._]AI\d*$", re.I)
_AI_NAME = re.compile(r"\(\s*AI\s*\)|AI[- ]ONLY|for AI", re.I)


def is_ai_only(row, source_ids=None):
    """True when a corpus row is an AI-exclusive duplicate and must never be a reference.

    ⚠ THE MARKER IS ALSO A PREFIX, not only a suffix. DTA ships 37 of them — `AIMSAM`, `AIMLRS`,
    `AILTNK`, `AIMTNK` — beside the real `MSAM`, `MLRS`, `LTNK`, `MTNK`, and the first pass of
    this filter looked only for a trailing `_AI`, so every one of them stayed in the pool. Here
    the sibling test is REQUIRED rather than advisory: `AI` at the front of an id is far too
    common to act on alone (a bare prefix rule would strike `AIRCRAFT`), so the row is refused
    only when stripping the prefix names a unit the same source actually ships.
    """
    if _AI_ID.search(row.get("id") or "") or _AI_NAME.search(row.get("name") or ""):
        return True
    rid = (row.get("id") or "").upper()
    if source_ids and rid.startswith("AI") and len(rid) > 3:
        known = source_ids.get(row.get("source"), ())
        base = rid[2:]
        # ⚠ AND THE SIBLING MAY CARRY A TRAILING INDEX THE REAL UNIT DOES NOT. DTA ships
        # `AIHTNK2` beside `HTNK` — there is no `HTNK2` — so an exact sibling test let it through
        # and `td_gdi_mammothtankmkiii` drew an AI-only Mammoth. The maintainer's objection is the
        # substantive one: AI variants are deliberately CHEAPER, so using one as a price reference
        # is worse than having no reference at all.
        return base in known or base.rstrip("0123456789") in known
    return False


def structured_peer_rows(corpora, *, heroes=False):
    """Adapt stable numeric fields without discarding nested source evidence."""
    rows = []
    range_profile = peer_range_evidence.load(ROOT)
    nominal_profile = peer_nominal_evidence.load(ROOT)
    base_profile = peer_base_state.load(ROOT)
    for source, (_meta, records) in corpora.items():
        if source in LINEAGE_MEMBERS:
            continue
        for record in records:
            # Aedis 2026-09-11: TD's unlimited Commando is the named hero counterpart
            # for both Cameo commandos. Preserve its actual limit; separate its model lane.
            named_hero = (source, record.get('id')) == ('OpenRA Tiberian Dawn', 'RMBO')
            if bool(is_hero_limit(record.get("limit")) or named_hero) != heroes:
                continue
            row = dict(record)
            row.pop("record", None)
            row.update(source=source, raw_source=source)
            peer_base_state.apply(row, record, base_profile)
            peer_range_evidence.apply(row, record, range_profile)
            if heroes:
                row["hero"] = named_hero or is_one_off(record.get("limit"))
                if named_hero:
                    row['hero_lane_reason'] = 'Explicit shared Commando identity ruling; source build limit remains unchanged.'
            speed, turn = row.get("speed"), row.get("turn_speed")
            row["turn_ratio"] = speed / turn if speed and turn else None
            if row.get("type") == "building" and row.get("w_damage"):
                row["type"] = "defense"
            dps = apply_weapon_evidence(row, record)
            reviewed_nominal = peer_nominal_evidence.apply(row, record, nominal_profile)
            if reviewed_nominal:
                dps = row['w_dps']
            for ladder in LADDERS:
                fraction = None if reviewed_nominal else record.get(f"eff_vs_{ladder}")
                row[f"dps_vs_{ladder}"] = dps * fraction if dps and fraction else None
            rows.append(row)
    return rows


def peer_rows():
    """Doc 5 rows with type, raw HP/speed/turn — the chassis corpus, after lineage de-dup."""
    corpora = peer_corpus.load(ROOT)
    rows, source, header = structured_peer_rows(corpora), None, None
    dropped_lineage = peer_rows.dropped = set()
    text = (ROOT / "docs/design/ORIGINAL_UNITS_PEER_OPENRA.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("## "):
            source = line[3:].split("(")[0].strip()
            header = None
            continue
        if not source or source in corpora or not line.startswith("|"):
            continue
        cells = [c.strip().strip("`") for c in line.split("|")[1:-1]]
        if not cells:
            continue
        if cells[0].lower() == "id":
            header = [c.lower() for c in cells]
            continue
        if not header or len(cells) != len(header) or set("".join(cells)) <= set("-: "):
            continue
        d = dict(zip(header, cells))
        def num(key):
            v = (d.get(key) or "").replace(",", "")
            try:
                return float(v)
            except ValueError:
                return None
        hp, spd, turn = num("hp"), num("speed"), num("turn")
        # ⚠ Cost was in the document and dropped on read. The matching cascade's last tie-break is
        # cost proximity, and without this it was available for two of fifteen sources.
        cost = num("cost")
        wep = {k: num(c) for k, c in (("w_range", "range"), ("w_damage", "dmg"),
                                      ("w_burst", "burst"), ("w_reload", "reload"),
                                      ("w_dps", "dps"))}
        limit = num("limit")
        if limit:                     # a mod's one-off epic/hero — see POPULATION RULE below
            continue                  # peer_hero_rows() picks these up under the SAME
                                      # evidence policy, so no verdict is lost on the hero lane
        # ⛔ AN ARMED BUILDING IS A DEFENCE (2026-09-03). Found when the maintainer asked why
        # Mental Omega and CnC Reloaded showed no defences: the corpus HAS them, typed `building`.
        # 73 defence-named ARMED rows (Obelisk of Light, Flamer Tower, Gattling Tower...) sat in
        # `building` against 21 in `defense`, and 94 armed rows are typed `building` overall.
        # ⚠ THAT IS A VOTE LOST ENTIRELY, not merely misfiled: buildings are excluded from the
        # `overall` population by design and `defense` is its own population, so an armed structure
        # typed `building` was measured against NOTHING. The type comes from the mod's queue name
        # (`TYPE_TOKENS` in extract_peer_units.py), so a mod that files turrets under a "Building"
        # queue lost every one of them.
        # The test is the weapon, not the name: a structure that shoots is a defence.
        if d.get("type", "").strip().lower() == "building" and wep.get("w_damage"):
            d["type"] = "defense"

        if source in LINEAGE_MEMBERS:
            # A member is dropped, never relabelled — see the header. Its representative keeps
            # the lineage's single vote.
            dropped_lineage.add(source)
            continue
        row = {"source": source, "raw_source": source,
               "id": d.get("id", ""), "name": d.get("unit", ""),
               "type": d.get("type", "other"),
               # ⚠ SAME CLASS OF BUG AS `cost` ABOVE: the faction column was added to the
               # document by `extract_peer_units.py` and dropped here on read, so the
               # routing ruling had no data to route on. A column that exists upstream and
               # is not carried is indistinguishable from a column that was never extracted.
               "faction": d.get("faction", ""),
               "turreted": (d.get("turret", "").lower() == "y"),
               "hp": hp, "speed": spd, "turn_speed": turn,
               "turn_ratio": (spd / turn) if (spd and turn) else None,
               "cost": cost, **wep}
        # Evidence BEFORE any consumer value is derived from the DPS — the same shared helper
        # `ini_rows` uses (see the policy block above `LEGACY_EVIDENCE`; `doc5_evidence_record`
        # maps the emitter's Evidence/Reason/Usable headers onto it). The armor ladders are
        # then derived from the dps THAT policy returns, so a withheld weapon withholds every
        # `dps_vs_*` with it, and the raw direct estimate stays on `w_dps_raw`.
        dps = apply_weapon_evidence(row, doc5_evidence_record(d))
        for lad in LADDERS:
            # NB the header row is lowercased on read, so the column key is `vsinf`, not `vsINF`.
            # Looking it up in the document's original case silently yields None for every row —
            # which is how this first reported 0 armor-aware rows out of 2,256.
            frac = num(f"vs{lad.lower()}")
            row[f"dps_vs_{lad}"] = (dps * frac) if (dps and frac) else None
        rows.append(row)
    # The extracted INI corpus joins here, and it is read FIRST: `doc1_rows()` asks it which
    # sources it covers, so the order is a dependency, not a preference.
    for row in ini_rows():
        if row["source"] in LINEAGE_MEMBERS:
            dropped_lineage.add(row["source"])
            continue
        rows.append(row)
    # Document 1's remaining hand-typed mods join here so they pass through the SAME lineage
    # de-duplication and land in the same distributions. Appended rather than merged: they are
    # separate sources.
    for row in doc1_rows():
        if row["source"] in LINEAGE_MEMBERS:
            dropped_lineage.add(row["source"])
            continue
        rows.append(row)
    # Applied once, here, so EVERY consumer sees the same corpus: the assignment, the coverage
    # audit and the distributions alike. An AI-only row must not shape a distribution either.
    by_src = collections.defaultdict(set)
    for r in rows:
        rid = (r.get("id") or "").strip().upper()
        if rid:
            by_src[r["source"]].add(rid)
    peer_rows.ai_only = [r for r in rows if is_ai_only(r, by_src)]
    # Peers store damage PER SHOT; the referenced coordinate is per CYCLE (see `to_per_cycle`).
    return to_per_cycle([r for r in rows if not is_ai_only(r, by_src)])


# Cameo's own 16 armor rows, grouped by the ladder DESIGN.md puts them in.
CAMEO_LADDER = {}
for _lad, _rows in (("INF", ("None", "Flak", "Plate", "Heroic")),
                    ("VEH", ("Scout", "Light", "Medium", "Heavy", "Superheavy")),
                    ("AIR", ("Fighter", "Bomber", "Helicopter", "Spaceship")),
                    ("BLD", ("Wood", "Concrete", "Steel"))):
    for _r in _rows:
        CAMEO_LADDER[_r] = _lad

_CAMEO_RULES = None


def cameo_weapon_ladders(weapon_name):
    """{ladder: mean Versus fraction} for one Cameo weapon, read through the resolver.

    ⚠ §12.0h normalises every `^Warhead_*` main to arithmetic MEAN 100 across its 16 rows, so the
    four ladder means hover near 1.0 by construction. That is not a bug and it is not noise — the
    CLASS TILT (§12.0d) is precisely the DEVIATION between ladders, so comparing a weapon's
    vs-VEH against its vs-INF is the signal, while its absolute level is fixed by law.
    """
    global _CAMEO_RULES
    if _CAMEO_RULES is None:
        sys.path.insert(0, str(ROOT / "tools" / "audit"))
        import miniyaml
        _CAMEO_RULES = miniyaml.Ruleset(ROOT)
    try:
        w = _CAMEO_RULES.resolve_weapon(weapon_name)
    except Exception:
        return {}
    if w is None:
        return {}
    hits = {}
    for c in w.children:
        if not c.key.startswith("Warhead"):
            continue
        try:
            if float(str(c.get("Damage") or 0)) <= 0:
                continue
        except ValueError:
            continue
        for x in c.children:
            if x.key != "Versus":
                continue
            for row in x.children:
                lad = CAMEO_LADDER.get(row.key)
                if not lad:
                    continue
                try:
                    hits.setdefault(lad, []).append(float(str(row.value)))
                except (TypeError, ValueError):
                    pass
    return {k: sum(v) / len(v) / 100.0 for k, v in hits.items() if v}


AA_SLOT = re.compile(r"(^|[@_.])aa($|[0-9_.])", re.I)


def is_anti_air_armament(arm):
    """An `@AA` armament engages a different DOMAIN and must not be summed with the ground gun.

    ⛔ FOUND ON `ra1_soviets_btr80` (maintainer, 2026-09-08). Its two unconditional armaments are
    `Armament` (ground) and `Armament@AA`, each 4,000 x burst 4 = 16,000, and summing them reported
    32,000 for a transport whose ground gun delivers 16,000. They can never fire at the same
    target: one shoots aircraft, the other cannot.

    ⭐ THIS IS NOT A NEW RULE, it is one DESIGN.md already made. The `anti_air_vehicle` anchor
    reads: "Dedicated AA; keeps a SEPARATE FREE air weapon (+50% range/+100% dmg) priced only on
    the ground weapon." Pricing on the ground weapon is the ruling; this makes the measurement obey
    it. 63 of 2,245 priced armaments are affected.

    ⛔ AND THE TEST MUST READ THE WEAPON, NOT ONLY THE SLOT. The first version matched the slot
    alone and missed `td_gdi_apc`, whose AA gun sits in a slot called `Armament@SECONDARY` while
    the WEAPON is `APCGun_AA` — range 8,502 against the primary's 5,668, which is 1.500 exactly.
    The maintainer spotted it immediately: *"I'm pretty sure they have Anti Air and also the +50%
    range against air right?"* They do. Matching the slot name alone is the same name-blocklist
    mistake this file warns about elsewhere; `_AA` on the weapon is the normalised convention here.

    ⚠ A unit whose armaments are ALL anti-air keeps them — that is its weapon, not a bonus. Exactly
    one actor is in that state today (`tkm_quadturretbunker`), and a dedicated AA unit reporting
    zero DPS would be the same class of error this whole sequence has been about.
    """
    return bool(AA_SLOT.search(str(arm.get("slot") or ""))
                or AA_SLOT.search(str(arm.get("weapon") or "")))


def burst_cycle(arm, anum):
    """Ticks between the START of one burst and the next: ReloadDelay + (Burst-1) x BurstDelay.

    ⛔ `BurstDelay` WAS HARDCODED TO 5 AND THE LEDGER CARRIES IT. Measured 2026-09-08 after the
    maintainer said the Sheridan number "has to do with our burst values": 1,017 priced armaments
    declare a burst, and their `burstdelays` are 3 (256 of them), 2 (172), 4 (160), 5 (78), 1 (62),
    0 (55), 8 (36)... so the hardcoded 5 was right for 78 weapons and wrong for the rest. A burst
    of 4 at delay 2 finishes in 6 ticks, not 15, and the DPS was understated by the difference.

    DESIGN.md's burst rule is the authority: "sheet ReloadDelay = weapon ReloadDelay + (bursts - 1)
    x BurstDelay". OpenRA cycles through several delays when several are given, so their mean is
    the honest single number.
    """
    rel = anum(arm.get("reloaddelay")) or 0
    burst = anum(arm.get("burst")) or 1
    if burst <= 1:
        return rel or None
    raw = str(arm.get("burstdelays") or "").replace(",", " ").split()
    delays = [d for d in (anum(x) for x in raw) if d is not None]
    delay = (sum(delays) / len(delays)) if delays else 5.0   # OpenRA's own default
    return rel + (burst - 1) * delay


def is_upgrade_gated(arm):
    """True when the armament is inactive in the canonical built state.

    This helper keeps its historical name for callers, but requirement shape is not enough to
    identify a baseline weapon: a Tesla Coil has numeric charge alternatives, and an IFV has
    mutually exclusive passenger modes.  The formula module owns the shared built-state rule
    (all named conditions false, malformed expressions fail closed), so this selector must use
    that same evaluator instead of independently treating every positive token as an upgrade.
    """
    return not formula.condition_holds_by_default(arm.get("requires"))


def default_active_armaments(arms):
    """Every priced armament active in the shared canonical built state, before role filtering."""
    return [a for a in arms if formula.condition_holds_by_default(a.get("requires"))]


def baseline_armaments(arms):
    """The armaments a unit fires AT ONCE with no upgrades and no rank.

    ⛔ `max()` WAS WRONG AND THE MAINTAINER CAUGHT IT (2026-09-08): *"What if there are two weapons
    that are fired at the same time? Like the GDI battle tank with cannon + rocket or the Sheridan
    that even has 3 parallel weapons all active at the same time!"* Measured on exactly those:

        td_gdi_battletank             cannon 8000 (!highvelocitycannons)
                                    + missiles 8000 (!advancedmissiletargeting)   = 16000, max gave 8000
        ra1_allies_sheridanassaulttank  16000 + 16000 + 4000, all `!cryomissiles`  = 36000, max gave 16000

    So simultaneous armaments SUM. What must never be summed is the alternatives: an upgraded
    barrel, an elite rank, or `ra2_allies_ifv`'s 39 passenger weapons, which are mutually exclusive
    at runtime. `requires` separates the two exactly, and the baseline set is also the right
    comparison for the references, which record un-upgraded weapons.
    """
    # Evaluate every armament against one shared built-state assignment before separating the
    # ground and AA domains.  A satisfiability test per arm would admit mutually exclusive modes
    # (Tesla charged/un-charged variants or every IFV passenger) and sum them as if they fired
    # together.  The formula evaluator is also the one used by fit_class.pricing_armaments.
    live = default_active_armaments(arms)
    ground = [a for a in live if not is_anti_air_armament(a)]
    if ground:
        return ground            # price on the ground weapon (DESIGN, anti_air_vehicle anchor)
    if live:
        return live              # a dedicated AA unit keeps its only weapon
    # ⛔ EVERY ARMAMENT IS CONDITIONAL — so fall back to the STRONGEST ONE, never to the sum.
    # `ra2_soviets_siegechopper` is the case: it has no unconditional armament at all, because
    # each is gated on a MODE and a doctrine and a rank at once
    # (`!rank-elite && !doctrine_nuclearmunitions && ... && deployed`). Returning the whole set
    # summed 10 mutually-exclusive barrels into 986,818 damage for a unit that fires one. A
    # fallback that is too PERMISSIVE is as wrong as a guard that is too restrictive; when the
    # data cannot say which armament is live, the honest answer is the single best one.
    return [max(arms, key=_armament_damage)]


def armament_profile(arms, anum, charge_up=None):
    """(w_range, w_damage, w_burst, w_reload, w_dps, debt, primary) over the BASELINE set.

    `AttackTesla` replaces a weapon's cadence with one actor-level cycle. The ledger already
    records that cycle in `charge_up`; using the weapon's reload by itself treats the gap between
    zaps as the full reload. Apply the shared formula only when one baseline armament makes the
    ownership unambiguous. Other charge traits return no cadence override, and multi-armament
    actors keep the existing fail-closed component verdict.
    """
    active = default_active_armaments(arms)
    live = baseline_armaments(arms)
    charged_cycle = None
    if len(active) == 1 and len(live) == 1 and active[0] is live[0]:
        weapon_reload = anum(live[0].get("reloaddelay"))
        charged_cycle = formula.charge_attack_cycle(charge_up, weapon_reload)
    dps_total, dmg_total, debt = 0.0, 0.0, False
    for a in live:
        mains = [wh for wh in (a.get("damage_warheads") or [])
                 if (anum(wh.get("damage")) or 0) > 0]
        if len(mains) > 1:
            debt = True          # §0a structure debt: `K` moves under W24
        # ⛔ DAMAGE IS PER SHOT; A BURST FIRES SEVERAL. DESIGN.md's burst rule is explicit —
        # "sheet Damage = single-burst damage x bursts" — and this used to apply the burst to the
        # DPS but not to the damage column, so a 4-shot machine gun reported a quarter of what it
        # delivers. The Sheridan read 36,000 (16,000 + 16,000 + 4,000) when its MG alone puts out
        # 4,000 x 4.
        dmg = sum(anum(wh.get("damage")) or 0 for wh in mains)
        burst = anum(a.get("burst")) or 1
        cycle = burst_cycle(a, anum)
        if charged_cycle is not None:
            cycle, burst = charged_cycle
        per_cycle = dmg * burst
        if per_cycle and cycle:
            dps_total += per_cycle / cycle
        dmg_total += per_cycle
    primary = max(live, key=lambda a: sum(anum(wh.get("damage")) or 0
                                          for wh in (a.get("damage_warheads") or [])
                                          if (anum(wh.get("damage")) or 0) > 0))
    ranges = [anum(a.get("range")) for a in live if anum(a.get("range"))]
    return {"w_range": max(ranges) if ranges else None,
            "w_damage": dmg_total or None,
            "w_burst": charged_cycle[1] if charged_cycle is not None
                       else anum(primary.get("burst")) or 1,
            "w_reload": (anum(charge_up.get("cycle_reload")) if charged_cycle is not None
                         else anum(primary.get("reloaddelay"))),
            "w_dps": dps_total or None,
            "weapon_model_eligible": len(live) == 1}, debt, primary


def _armament_damage(arm):
    """Total damage over an armament's POSITIVE main warheads."""
    total = 0.0
    for wh in (arm.get("damage_warheads") or []):
        try:
            d = float(str(wh.get("damage")))
        except (TypeError, ValueError):
            continue
        if d > 0:
            total += d
    return total


def primary_armament(arms):
    """The armament that represents this actor's firepower: the HARDEST-HITTING one.

    ⛔ THIS USED TO BE `arms[0]` AND THAT IS YAML ORDER, NOT IMPORTANCE. Found by the maintainer
    2026-09-08 on `td_nod_lighttankmkii`, whose reported DPS was 0: its first priced armament is
    `Armament@pointdefense` firing `PDLaserLTNK2` for **1** damage, while the actual gun
    (`LightTank2Cannon`) and missiles (`LightTank2Missiles`) each deal 8,000. The table was showing
    a point-defense laser as the tank's weapon.

    Measured across the tree: 822 buildable actors carry a priced armament, **495 of them carry
    more than one**, and on **86** the first armament deals under half what the best one does. So
    this was never one unit — it is a sixth of every armed actor reporting the wrong weapon.

    ⚠ MAX, NEVER SUM. `ra2_allies_ifv` has THIRTY-NINE priced armaments — one per passenger type,
    mutually exclusive at runtime. Summing them would claim 200,000+ damage for a transport that
    can only ever fire one. The maintainer's own framing is the rule: the conditional armaments
    exist, but only one of them is the unit's weapon at any moment.
    """
    return max(arms, key=_armament_damage)


# ⛔⛔ SUPERWEAPONS ARE NEVER PRICED, NEVER RESTATTED, NEVER TOUCHED (maintainer, 2026-09-07):
#
#     "exclude super weapons from this balance formula since they are all fixed HP!
#      NEVER CHANGE THEM!! SO EXCLUDE THEM BEFORE ANYTHING IS CHANGED ON ACCIDENT!!!"
#
# They are gated on `~techlevel.superweapons` (or a `_swlimit` negation), and that prerequisite is
# the mechanical test — 32 actors carry it, and EVERY one whose HP is recorded holds exactly
# 1,000,000. That uniform value is the point: it is a deliberate constant, not a balance figure,
# and a pipeline that treats it as a stat to normalise would drag it toward a building average
# and quietly destroy it.
#
# Excluded HERE, at the single point every consumer reads, so the reference map, the
# distributions, the targets and the uniqueness audit all agree that these actors do not exist.
SUPERWEAPON_TOKENS = ("techlevel.superweapon", "swlimit")


def is_superweapon(rec):
    """True when a ledger record is gated on a superweapon prerequisite."""
    for pre in (rec.get("prerequisites") or []):
        low = str(pre).lower()
        if any(tok in low for tok in SUPERWEAPON_TOKENS):
            return True
    return False


def to_per_cycle(rows):
    """Express every row's `w_damage` as damage PER FULL CYCLE (the whole burst).

    ⛔ PER SHOT IS THE FORMULA'S INPUT AND THE WRONG THING TO COMPARE — maintainer, 2026-09-13:
    *"if our mammoth tank is burst 2 and the reference is the ion mammoth or the railgun mammoth
    with burst 1 it would give the wrong value ... it should reference the total damage including
    all bursts right?"*. Correct, and the corpus shows it plainly: Shattered Paradise ships the
    Mammoth Mk. II at Burst 4 and OpenRA TS ships it at Burst 2. Per shot BOTH read 4,000, so a
    per-shot comparison calls them identical while their real output per cycle is 16,000 against
    8,000 — a 2x difference the reference would have hidden.

    Burst is a DELIVERY choice; damage per cycle is the magnitude. So the referenced coordinate is
    per cycle, and per-shot is derived from it by dividing by whichever burst the unit ends up with.

    ⚠ THIS IS THE OPPOSITE OF WHAT I SHIPPED THIS MORNING, and the reversal is the point. I had
    normalised everything DOWN to per shot, which made the one formula apply literally but made
    the projection compare the wrong quantity. The formula is unaffected either way:
    `per_shot x burst / cycle` and `cycle_damage / cycle` are the same number.

    Cameo's frozen snapshot already stores the burst TOTAL (verified against the authored yaml:
    `td_gdi_mammothtank_120mmdualhv` declares `Damage: 16000` with `Burst: 2` and the snapshot
    carries 32,000), so Cameo rows pass through untouched. Every peer corpus stores damage per
    SHOT, so a peer row is multiplied by its own burst.

    ⛔⛔ THE SENTENCE ABOVE WAS THE DOCSTRING AND NOT THE CODE, AND THAT COST A FACTOR OF 2.4.
    Maintainer, 2026-09-13: *"the GDI grenadier reference damage per shot went up from 22k to 38k
    per cycle but why? ... the grenadier only shoots a single grenade so the numbers should not
    change right?"* Right, and the grenadier's own numbers did NOT change — all three of its
    references are Burst 1. What changed was the RULER it is measured against.

    The loop below multiplied EVERY row with `Burst > 1`, and `reference_targets.cameo_context()`
    feeds it the frozen Cameo snapshot, which is exactly the corpus the docstring says is already
    per cycle. So Cameo's burst rows were multiplied A SECOND TIME:

        td_gdi_mammothtank  yaml 16,000 x Burst 2  snapshot 32,000  ->  64,000
        td_gdi_mlrs         yaml  8,000 x Burst 6  snapshot 48,000  -> 288,000   (36x the shot)

    245 of the 893 frozen rows, and 24 of the 83 hero rows. That snapshot is the PROJECTION
    RULER — the distribution every damage target is projected onto — so inflating a quarter of it
    lifted the damage target of every Cameo actor, including the single-shot ones that have no
    burst anywhere near them. Cameo's infantry ruler read median 25,200 / mean 60,189 / gm 26,071
    where the truth is 20,010 / 28,049 / 18,539, and td_gdi_grenadier projected 38,451 instead of
    21,631.

    ⚠ THE GUARD IS THE SOURCE, NOT A FLAG AT THE CALL SITE. Both frozen snapshots are 100% rows
    of `source == "Cameo"` (893 and 83, measured), Cameo is the one corpus that stores the burst
    total, and a parameter would have to be passed correctly at every future call site to work.
    This way a Cameo row is safe wherever it is handed in, including mixed with peers.
    """
    out = []
    for r in rows:
        d, burst = r.get("w_damage"), float(r.get("w_burst") or 1)
        if d and burst > 1 and r.get("source") != "Cameo":
            r = dict(r, w_damage=float(d) * burst, w_damage_per_shot=d)
        elif d and burst > 1:
            # Already a cycle total. Only the derived per-SHOT figure is attached.
            r = dict(r, w_damage_per_shot=float(d) / burst)
        else:
            r = dict(r, w_damage_per_shot=d)
        out.append(r)
    return out


def cameo_rows():
    """Cameo's own roster in the same shape, so it has real distributions to project onto."""
    out = []
    for path in sorted((ROOT / "docs/balance").glob("*.json")):
        if "class_anchors" in path.name:
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        for section, units in (doc.get("sections") or {}).items():
            kind = CAMEO_SECTION_TYPE.get(section)
            # ⛔ `buildings` has NO entry in CAMEO_SECTION_TYPE, and for most of its contents that
            # is right — a refinery is not a combat unit. But Cameo files its defences by pack
            # CONVENTION, not by rule: the RedAlert packs have a `defenses.yaml`, the TiberianDawn
            # ones keep theirs in `buildings.yaml`. Gating on the section name alone therefore
            # dropped every armed structure in the second group — 38 buildable actors, INCLUDING
            # ALL SEVEN TD DEFENCES (Obelisk, both Guard Towers, Gun Turret, SAM, Skyshield).
            # They were not mismatched; they never entered the population, so nothing could claim
            # OpenTD's OBLI/GTWR/ATWR/GUN/SAM and audit_original_coverage reported them unclaimed.
            # This is the SAME rule the peer side already applies (see the `building` -> `defense`
            # retype below): armed means defence, on BOTH sides, or Cameo's `defense` population is
            # measured against a peer population built to a wider definition.
            if (kind is None and section != "buildings") or not isinstance(units, dict):
                continue
            for name, rec in units.items():
                if not isinstance(rec, dict):
                    continue
                if rec.get("buildable") is not True:
                    continue
                if is_superweapon(rec):
                    continue
                # ⛔ ZERO IS NOT A LIMIT, and this line said otherwise. `is_hero_limit` has
                # documented the rule since 2026-09-08 — "PRESENT AND GREATER THAN ZERO ...
                # `BuildLimit=0` means NO LIMIT in Westwood INI, not 'one only'" — but this drop
                # tested PRESENCE, so an actor written `BuildLimit: 0` fell out of the ordinary
                # population while `cameo_hero_rows` also refused it for not being a one-off. It
                # landed in NEITHER pool and could match nothing at all.
                #
                # Found when the maintainer ruled the Chrono Tank back to an unlimited unit
                # (2026-09-13). It inherits `^EpicVehicleTemplate`, so the limit cannot simply be
                # deleted from the actor — `BuildLimit: 0` is the cancellation MiniYaml supports —
                # and that spelling hit this bug. Measured blast radius: ONE actor in the whole
                # ledger carries a zero limit, so this aligns the test with its own stated rule
                # and changes nothing else.
                if is_hero_limit((rec.get("build_limit") or {}).get("v")
                                 if isinstance(rec.get("build_limit"), dict)
                                 else rec.get("build_limit")):
                    continue
                if ((rec.get("design") or {}).get("class_anchor")) in EXCLUDE_CLASSES:
                    continue
                def val(field):
                    slot = rec.get(field)
                    if isinstance(slot, dict):
                        slot = slot.get("v")
                    try:
                        return float(str(slot))
                    except (TypeError, ValueError):
                        return None
                hp = val("hp")
                spd = val("speed") or val("speed_air")
                turn = val("turn_speed") or val("turn_speed_air")
                if hp is None:
                    continue
                # Cameo's weapon numbers come from the ledger's own armaments, resolved the same
                # way as the peers': damage summed over POSITIVE mains, burst inside the cycle.
                arms = [a for a in (rec.get("armaments") or [])
                        if isinstance(a, dict) and a.get("pricing")]
                # An actor from `buildings` earns a place only by being armed; production and
                # economy structures stay out. `row_kind` is local because `kind` is the section's
                # and must not leak from one actor to the next.
                row_kind = kind
                if row_kind is None:
                    if not arms:
                        continue
                    row_kind = "defense"

                def anum(v):
                    try:
                        return float(str(v))
                    except (TypeError, ValueError):
                        return None

                w, debt = {}, False
                if arms:
                    w, debt, a = armament_profile(arms, anum, rec.get("charge_up"))
                    dps = w["w_dps"]
                    tpl = a.get("versus_templates") or []
                    wname = a.get("weapon") or (tpl[-1] if tpl else None)
                    if dps and wname:
                        for lad, frac in cameo_weapon_ladders(wname).items():
                            w[f"dps_vs_{lad}"] = dps * frac
                # ⭐ COST. Every PEER row has carried a price since extraction; Cameo's did not,
                # so a price target had nothing on this side to normalise onto and every cost
                # column came out empty — reading as "no reference data" when the references had
                # it all along. `cost` is not in ALL_STATS (this module is the chassis layer), so
                # a consumer that wants price must build that aggregate itself; carrying the value
                # here is what makes that possible at all.
                # ⛔ NORMALISED TO DAMAGE PER SHOT RIGHT HERE, so that every corpus in the
                # project speaks one language and ONE formula applies to all of them (maintainer,
                # 2026-09-12: "I want this formula to be used universally no matter what the
                # reference is. Any OpenRA mod or cnc based ini mod should work the same way").
                #
                # Cameo's frozen snapshot stores `w_damage` as the WHOLE BURST; every other
                # corpus stores it per SHOT. Verified against the AUTHORED YAML rather than
                # inferred: `td_gdi_mammothtank_120mmdualhv` declares `Damage: 16000` with
                # `Burst: 2`, and the snapshot carries 32,000.
                #
                # ⚠ CONVERTING HERE RATHER THAN AT THE POINT OF USE IS THE WHOLE FIX. A flag read
                # by the last consumer looked equivalent and is not: the DISTRIBUTIONS and every
                # projection through `target_for` are built from these rows, so leaving them in
                # burst-total units means a projected damage target comes back in burst-total
                # units too, and the formula then multiplies by burst a second time. Normalising
                # at construction makes per-shot the only convention that exists downstream.
                #
                # The authored per-cycle figure is kept beside it for display — it is what the
                # ledger holds — but nothing computes from it.
                # Cameo already stores the burst TOTAL, which IS the referenced coordinate
                # (see `to_per_cycle`). Kept as authored; the per-shot figure is derived.
                w_cycle = w.get("w_damage")
                burst = float(w.get("w_burst") or 1)
                per_shot = (float(w_cycle) / burst) if (w_cycle and burst > 1) else w_cycle
                out.append({"source": "Cameo", "id": name, "name": name, "type": row_kind,
                            "hp": hp, "speed": spd, "turn_speed": turn, "cost": val("cost"),
                            "structure_debt": debt, "w_damage_per_shot": per_shot,
                            "turn_ratio": (spd / turn) if (spd and turn) else None, **w})
    return out


def is_one_off(limit):
    """A HERO is a limit of exactly one. A cap of 2+ is a scarce unit, not a one-off.

    Maintainer's ruling 2026-09-08: build-limited rows all become visible to the assignment,
    TAGGED — heroes (limit 1) match only Cameo heroes, while a capped unit matches normally.
    DTA's `A10` A-10 Warthog is capped at 3 and is an ordinary GDI aircraft; its `XO` X-O Power
    Suit is capped at 1 and is a one-off. Both were invisible before, which is why the maintainer
    had to point out twice that they exist.

    ⚠ Neither ever enters a pricing DISTRIBUTION — `ini_rows`/`peer_rows` still drop every
    build-limited row, so the population rule is untouched and the 3,000,000 HP epic cannot
    distort a ceiling. This flag governs MATCHING only.
    """
    try:
        return limit is not None and float(limit) == 1
    except (TypeError, ValueError):
        return False


def is_hero_limit(limit):
    """A one-off is `BuildLimit` PRESENT AND GREATER THAN ZERO. Zero is not a limit.

    ⛔ MEASURED 2026-09-08, and it is the difference between a hero lane and deleting 110 units.
    125 corpus rows carry `build_limit == 0`: Mental Omega's Flame Tower (400cr), Instant Shelter
    (500cr) and Deployed Grumble (2000cr), DTA's `RAAGUN_AI`, and Twisted Insurrection's deployed
    forms. Ordinary buildable units at ordinary prices — `BuildLimit=0` means NO LIMIT in Westwood
    INI, not "one only".

    A proposed fix read the falsy-zero as a bug and changed `ini_rows`' test to `is not None`,
    which would have dropped all 110 costed, buildable ones out of every distribution. The truthy
    test was right. Heroes are `> 0`, and this function is the only place that decides it.
    """
    try:
        return limit is not None and float(limit) > 0
    except (TypeError, ValueError):
        return False


def peer_hero_rows():
    """Hero/epic peer rows that peer_rows() drops, with a `hero` flag.

    The population rule excludes heroes from distributions (a 3,000,000 HP epic
    must never re-enter the vehicle ceiling), but the ASSIGNMENT may see them so
    a Cameo hero matches a peer hero. This returns the rows peer_rows() drops
    -- Doc 5 rows with `limit`, INI rows with `build_limit` -- flagged `hero: True`.

    These rows are for assign_references ONLY. Distributions still call
    peer_rows(), which excludes them. Wiring them into distributions would
    re-enter the epic into the vehicle ceiling.
    """
    corpora = peer_corpus.load(ROOT)
    rows = structured_peer_rows(corpora, heroes=True)
    hero_range_profile = ini_range_evidence.load(ROOT)
    hero_cycle_profile = ini_cycle_evidence.load(ROOT)
    # Doc 5 heroes: rows with `limit` present (peer_rows drops at line 508)
    source, header = None, None
    text = (ROOT / "docs/design/ORIGINAL_UNITS_PEER_OPENRA.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("## "):
            source = line[3:].split("(")[0].strip()
            header = None
            continue
        if not source or source in corpora or not line.startswith("|"):
            continue
        cells = [c.strip().strip("`") for c in line.split("|")[1:-1]]
        if not cells:
            continue
        if cells[0].lower() == "id":
            header = [c.lower() for c in cells]
            continue
        if not header or len(cells) != len(header) or set("".join(cells)) <= set("-: "):
            continue
        d = dict(zip(header, cells))
        def num(key):
            v = (d.get(key) or "").replace(",", "")
            try:
                return float(v)
            except ValueError:
                return None
        limit = num("limit")
        if not is_hero_limit(limit):      # ONLY heroes -- the rows peer_rows() drops
            continue
        if source in LINEAGE_MEMBERS:
            continue
        hp, spd, turn = num("hp"), num("speed"), num("turn")
        cost = num("cost")
        wep = {k: num(c) for k, c in (("w_range", "range"), ("w_damage", "dmg"),
                                      ("w_burst", "burst"), ("w_reload", "reload"),
                                      ("w_dps", "dps"))}
        if d.get("type", "").strip().lower() == "building" and wep.get("w_damage"):
            d["type"] = "defense"
        row = {"source": source, "raw_source": source,
               "id": d.get("id", ""), "name": d.get("unit", ""),
               "type": d.get("type", "other"),
               "faction": d.get("faction", ""),
               "turreted": (d.get("turret", "").lower() == "y"),
               "hp": hp, "speed": spd, "turn_speed": turn,
               "turn_ratio": (spd / turn) if (spd and turn) else None,
               "cost": cost, "hero": is_one_off(limit), **wep}
        # The evidence policy, shared with `ini_rows` and `peer_rows`, BEFORE any `dps_vs_*`
        # is derived. `doc5_evidence_record` maps the emitter's Evidence/Reason/Usable
        # headers: a table WITH those columns gates these rows exactly as it gates the
        # ordinary ones; a legacy table without them maps to absent -> legacy-unassessed and
        # keeps its existing numeric behaviour.
        dps = apply_weapon_evidence(row, doc5_evidence_record(d))
        for lad in LADDERS:
            frac = num(f"vs{lad.lower()}")
            row[f"dps_vs_{lad}"] = (dps * frac) if (dps and frac) else None
        rows.append(row)
    # INI heroes: rows with build_limit present (ini_rows drops at line 366)
    if INI_CORPUS.exists():
        armor = _ini_armor_index()
        for line in INI_CORPUS.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            kind = INI_TYPE.get(r.get("type"))
            if kind is None:
                continue
            bl = r.get("build_limit")
            if not is_hero_limit(bl):       # ONLY heroes -- the rows ini_rows() drops
                continue
            if not r.get("cost") or not r.get("buildable", True):
                continue
            if r["source"] in LINEAGE_MEMBERS:
                continue
            spd, turn = r.get("speed"), r.get("turn_speed")
            row = {"source": r["source"], "raw_source": r["source"],
                   "id": r.get("id", ""), "name": r.get("name", ""),
                   "type": kind,
                   "faction": r.get("faction", ""),
                   "turreted": r.get("turreted"),
                   "weapon": r.get("weapon"),
                   "hp": r.get("hp"), "speed": spd,
                   "turn_speed": turn,
                   "turn_ratio": (spd / turn) if (spd and turn) else None,
                   "cost": r.get("cost"), "hero": is_one_off(bl),
                   "w_range": r.get("w_range"), "w_damage": r.get("w_damage"),
                   "w_burst": _ini_burst(r), "w_reload": r.get("w_reload"),
                   "w_dps": r.get("w_dps")}
            # Same shared evidence policy as `ini_rows`, before any `dps_vs_*` derives.
            dps = apply_weapon_evidence(row, r)
            ini_range_evidence.apply(row, r, hero_range_profile)
            cycle_applied = ini_cycle_evidence.apply(row, r, hero_cycle_profile)
            if cycle_applied:
                dps = row["w_dps"]
            vs = {} if cycle_applied else armor.get((r["source"], r.get("id"))) or {}
            for lad in LADDERS:
                frac = vs.get(lad)
                row[f"dps_vs_{lad}"] = (dps * frac) if (dps and frac) else None
            rows.append(row)
    # Apply the same AI-only filter as peer_rows()
    by_src = collections.defaultdict(set)
    for r in rows:
        rid = (r.get("id") or "").strip().upper()
        if rid:
            by_src[r["source"]].add(rid)
    rows = [r for r in rows if not is_ai_only(r, by_src)]
    # Peers store damage PER SHOT; the referenced coordinate is per CYCLE (see `to_per_cycle`).
    return to_per_cycle(rows)


def peer_variant_rows():
    """Chassis-variant peer rows that `peer_rows()` drops, flagged `variant: True`.

    The THIRD population in the family `peer_rows()` / `peer_hero_rows()` already established,
    and it exists for the same reason the hero lane does: the maintainer's population rule is a
    statement about DISTRIBUTIONS, and the assignment keeps inheriting it by accident. A unit
    nobody can buy has no place in a ceiling. It can still be the unit a Cameo actor IS.

    The maintainer found this one by eye, 2026-09-12:

        "there are some additional units from DTA that might be unbuildable. What are those and
         can some of them be mapped? Like I've seen a drone carrier and a missile humvee.
         Maybe useful for our promotion units?"

    They were right, and the population is small and sharp: 40 rows across nine sources, six of
    them DTA's. `variant_pool.py` carries the ten gates that get it from 11,000 raw records down
    to those 40 and the count each one refused — the important ones being that critters carry no
    faction at all, and that a RANK state (Rise of the East's `_E` elite suffix, 418 rows) is not
    a chassis. Read that module before widening anything here.
    """
    rows = [dict(r, variant=True) for r in ini_rows(variants=True)
            if r["source"] not in LINEAGE_MEMBERS]
    by_src = collections.defaultdict(set)
    for r in rows:
        rid = (r.get("id") or "").strip().upper()
        if rid:
            by_src[r["source"]].add(rid)
    return to_per_cycle([r for r in rows if not is_ai_only(r, by_src)])


def cameo_hero_rows():
    """Hero/epic Cameo rows that cameo_rows() drops, with a `hero` flag.

    cameo_rows() drops every actor with `build_limit` (line 677) -- the 83 hero/epic
    combat rows the maintainer ruled are balanced separately. This returns them
    flagged `hero: True` so assign_references can match hero-to-hero only.

    NO EXCLUDE_CLASSES FILTER: the hero lane is specifically for heroes and epics,
    which `epic_vehicle` class_anchor marks. cameo_rows() excludes them from the
    normal population; the hero lane includes them so a Cameo epic can match a
    peer epic.
    """
    out = []
    for path in sorted((ROOT / "docs/balance").glob("*.json")):
        if "class_anchors" in path.name:
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        for section, units in (doc.get("sections") or {}).items():
            kind = CAMEO_SECTION_TYPE.get(section)
            if (kind is None and section != "buildings") or not isinstance(units, dict):
                continue
            for name, rec in units.items():
                if not isinstance(rec, dict):
                    continue
                if rec.get("buildable") is not True:
                    continue
                if is_superweapon(rec):
                    continue
                if not is_hero_limit((rec.get("build_limit") or {}).get("v")
                                     if isinstance(rec.get("build_limit"), dict)
                                     else rec.get("build_limit")):   # ONLY heroes
                    continue
                def val(field):
                    slot = rec.get(field)
                    if isinstance(slot, dict):
                        slot = slot.get("v")
                    try:
                        return float(str(slot))
                    except (TypeError, ValueError):
                        return None
                hp = val("hp")
                spd = val("speed") or val("speed_air")
                turn = val("turn_speed") or val("turn_speed_air")
                if hp is None:
                    continue
                arms = [a for a in (rec.get("armaments") or [])
                        if isinstance(a, dict) and a.get("pricing")]
                row_kind = kind
                if row_kind is None:
                    if not arms:
                        continue
                    row_kind = "defense"
                def anum(v):
                    try:
                        return float(str(v))
                    except (TypeError, ValueError):
                        return None
                w, debt = {}, False
                if arms:
                    w, debt, a = armament_profile(arms, anum, rec.get("charge_up"))
                    dps = w["w_dps"]
                    tpl = a.get("versus_templates") or []
                    wname = a.get("weapon") or (tpl[-1] if tpl else None)
                    if dps and wname:
                        for lad, frac in cameo_weapon_ladders(wname).items():
                            w[f"dps_vs_{lad}"] = dps * frac
                cycle_damage = w.get("w_damage")
                burst = float(w.get("w_burst") or 1)
                per_shot = (float(cycle_damage) / burst
                            if cycle_damage and burst > 1 else cycle_damage)
                out.append({"source": "Cameo", "id": name, "name": name, "type": row_kind,
                            "hp": hp, "speed": spd, "turn_speed": turn, "cost": val("cost"),
                            "structure_debt": debt, "hero": True,
                            "w_damage_per_shot": per_shot,
                            "turn_ratio": (spd / turn) if (spd and turn) else None, **w})
    return out


def build_distributions(rows):
    """{source: {population: {stat: aggregates}}}, population = a type, or 'overall'."""
    by_source = collections.defaultdict(list)
    for r in rows:
        by_source[r["source"]].append(r)
    dist = {}
    for source, items in by_source.items():
        pops = {"overall": [r for r in items if r["type"] in COMBAT_TYPES]}
        for t in POPULATIONS:
            pops[t] = [r for r in items if r["type"] == t]
        entry = {}
        for pop, members in pops.items():
            stats = {}
            for stat in ALL_STATS:
                agg = aggregates([m.get(stat) for m in members if eligible(m, stat)])
                if agg:
                    stats[stat] = agg
            if stats:
                entry[pop] = stats
        dist[source] = entry
    return dist


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stat", choices=CHASSIS_STATS, default="hp")
    ap.add_argument("--type", dest="kind", choices=POPULATIONS)
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    peers = peer_rows()
    cameo = cameo_rows()
    dist = build_distributions(peers)
    cameo_dist = build_distributions(cameo)["Cameo"]

    dropped = sorted(peer_rows.dropped)
    print(f"peer rows           : {len(peers)}   sources after lineage de-dup: {len(dist)}")
    if dropped:
        # ⚠ The representative is looked up per source, not hardcoded. There is more than one
        # lineage now, and printing every collapse as "-> Romanov's Vengeance" would misreport
        # the moment a second one has a member in this layer.
        collapse = reference_lineages.superseded_map()
        for source in dropped:
            print(f"lineage-collapsed   : {source} -> {collapse[source]}")
    print(f"Cameo rows          : {len(cameo)}")
    counts = evidence_counts(peers)
    print("weapon evidence     : "
          + ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
          + "   (counts EVERY peer row - OpenRA Doc 5 + INI corpus + Doc 1; "
            "legacy-unassessed = no extractor verdict present, absent status is legacy, "
            "never certified)")

    # index peers by normalized name so a Cameo actor can find its counterparts
    by_name = collections.defaultdict(list)
    for r in peers:
        key = syn.norm(r["name"])
        if len(key) >= syn.MIN_KEY:
            by_name[key].append(r)

    signatures, report_rows = {}, []
    for c in cameo:
        akey = syn.norm(c["id"].split("_")[-1])
        peers_for = [p for k, plist in by_name.items() if akey.startswith(k) for p in plist]
        if not peers_for:
            continue
        sig, targets = {}, {}
        for stat in ALL_STATS:
            pooled = collections.defaultdict(list)
            used = set()
            for p in peers_for:
                x = p.get(stat)
                if not x:
                    continue
                d = dist.get(p["source"], {})
                for pop in ("overall", p["type"]):
                    agg = d.get(pop, {}).get(stat)
                    for k, v in coordinates(x, agg).items():
                        pooled[(pop, k)].append(v)
                        used.add(p["source"])
            if not pooled:
                continue
            synth = {}
            for (pop, k), vals in pooled.items():
                # p_rng is bounded [0,1] and can legitimately be 0, where a geometric mean is
                # undefined; every other coordinate is a ratio and pools geometrically.
                synth[(pop, k)] = (statistics.fmean(vals) if k == "p_rng" else gm(vals))
            cands = []
            for pop in ("overall", c["type"]):
                coord = {k: v for (p_, k), v in synth.items() if p_ == pop}
                cands += list(project(coord, cameo_dist.get(pop, {}).get(stat)).values())
            target = gm(cands)
            if target:
                sig[stat] = {f"{p_}.{k}": round(v, 4) for (p_, k), v in sorted(synth.items())}
                targets[stat] = {"target": round(target, 1),
                                 "now": c.get(stat), "sources": len(used),
                                 "confidence": ("HIGH" if len(used) >= 3 else
                                                "MEDIUM" if len(used) == 2 else "LOW")}
        if targets:
            signatures[c["id"]] = {"type": c["type"], "targets": targets, "signature": sig,
                                   "structure_debt": bool(c.get("structure_debt"))}
            report_rows.append((c, targets))

    print(f"Cameo actors with a reference signature: {len(report_rows)}")
    stat = args.stat
    rows = [(c, t) for c, t in report_rows if stat in t and (not args.kind or c["type"] == args.kind)]
    rows.sort(key=lambda r: -abs(math.log((r[1][stat]["target"] or 1) / (r[1][stat]["now"] or 1)))
              if r[1][stat]["now"] else 0)
    for c, t in rows[:args.limit]:
        e = t[stat]
        now = e["now"] or 0
        print(f"  {c['type']:<9} {c['id']:<34} {stat} {now:>10,.0f} -> {e['target']:>10,.0f}"
              f"  ({e['sources']} src, {e['confidence']})")

    if args.dry_run:
        return 0
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"peers": dist, "cameo": cameo_dist}, indent=1, sort_keys=True,
                                   default=float) + "\n", encoding="utf-8")
    SIG_JSON.write_text(json.dumps(signatures, indent=1, sort_keys=True, default=float) + "\n",
                        encoding="utf-8")
    write_report(dist, cameo_dist, report_rows, dropped)
    print(f"wrote {OUT_MD.relative_to(ROOT)}, {OUT_JSON.relative_to(ROOT)}, "
          f"{SIG_JSON.relative_to(ROOT)}")
    return 0


def write_report(dist, cameo_dist, report_rows, dropped):
    o = ["# Reference synthesis — the chassis layer (HP, speed, turn rate)", "",
         "_AUTO-GENERATED by `tools/balance/reference_distribution.py`. Do not hand-edit._", "",
         "**This changes no balance number.** It measures where each Cameo unit sits inside the "
         "genre's distributions and where the reference consensus would put it. "
         "`class_anchors.json` and Formula V2 still decide what ships.", "",
         "## The method, and why the rifleman was retired", "",
         "Every unit used to be described as a multiple of its source's basic rifleman. That "
         "breaks whenever a source has no infantry, and it silently rescales everything when the "
         "nominated anchor is unusual. Instead each unit is now placed inside its own source's "
         "**distribution**, twice: against its **type** (infantry / vehicle / aircraft / ship / "
         "defense) and against the **overall** combat roster.", "",
         "For each population the five aggregates are `min`, `max`, `median`, arithmetic mean and "
         "geometric mean, and the unit gets six dimensionless coordinates against them — five "
         "ratios plus `p_rng`, its position in the min-max span. `p_rng` is kept because ratios "
         "to min and max are not commensurate with the middle three: a source whose floor is a "
         "1 HP prop makes `r_min` read in the thousands while `r_max` reads 0.9.", "",
         "Coordinates are pooled across sources with the **geometric** mean (they are ratios: a "
         "source 2× high and one 2× low must cancel to 1.0, which only the geometric mean does); "
         "`p_rng` is bounded [0,1] and is pooled arithmetically. Each pooled coordinate is then "
         "multiplied by **Cameo's own** matching aggregate, and the final target is the geometric "
         "mean of those candidates.", "",
         "⚠ Raw stats are never averaged across sources. 125 HP and 12,500 HP are the same design "
         "intent at different scales; their mean belongs to no game.", "",
         "⚠ Buildings are excluded from the `overall` population — they are not mobile combat "
         "units and they outnumber everything else in most rosters, so including them would drag "
         "every median.", ""]
    if dropped:
        o += ["## Lineage de-duplication", "",
              "Maintainer ruling: one vote per **balance lineage**, not per file. Collapsed into "
              "`Romanov's Vengeance`: " + ", ".join(f"`{d}`" for d in dropped) + ".", "",
              "Measured first: those five vanilla copies agree with each other on **96%** of "
              "shared units (118/123), which is what makes them one lineage. ⚠ But RV is **not** "
              "a faithful copy — on the 86 units where the others agree and RV is present, RV is "
              "the **sole dissenter on 39 (45%)**: Kirov 32× vs 16×, Aegis Cruiser 3.2× vs 6.4×, "
              "Flak Track 2.4× vs 1.4×. Electing RV as the lineage's voice therefore adopts RV's "
              "rebalance on those units rather than vanilla's consensus. Defensible — RV is the "
              "live, resolvable OpenRA codebase — but not a no-op.", ""]
    o += ["## Source distributions", "",
          "| source | population | stat | n | min | median | geo-mean | max |",
          "|---|---|---|--:|--:|--:|--:|--:|"]
    for source in sorted(dist):
        for pop in ("overall", "vehicle", "infantry"):
            agg = dist[source].get(pop, {}).get("hp")
            if agg:
                o.append(f"| {source} | {pop} | hp | {agg['n']} | {agg['min']:,.0f} | "
                         f"{agg['median']:,.0f} | {agg['gm']:,.0f} | {agg['max']:,.0f} |")
    o += ["", "### Cameo's own distributions", "",
          "| population | stat | n | min | median | geo-mean | max |", "|---|---|--:|--:|--:|--:|--:|"]
    for pop in ("overall",) + POPULATIONS:
        for stat in CHASSIS_STATS:
            agg = cameo_dist.get(pop, {}).get(stat)
            if agg:
                o.append(f"| {pop} | {stat} | {agg['n']} | {agg['min']:,.0f} | "
                         f"{agg['median']:,.0f} | {agg['gm']:,.0f} | {agg['max']:,.0f} |")
    # calibration: is the model centred, or does it systematically push one way?
    o += ["", "## Calibration — is the model centred?", "",
          "If Cameo were wildly out of step with the genre, the target/now ratio would sit far "
          "from 1.0. It does not, and that is the strongest evidence that the coordinate system "
          "is sound rather than merely self-consistent:", "",
          "| stat | HIGH-confidence rows | median ratio | geo-mean ratio | within 2× |",
          "|---|--:|--:|--:|--:|"]
    for stat in CHASSIS_STATS:
        lr = [math.log(e["target"] / e["now"]) for _, t in report_rows
              for st, e in t.items() if st == stat and e["now"] and e["confidence"] == "HIGH"]
        if len(lr) >= 20:
            o.append(f"| {stat} | {len(lr)} | {math.exp(statistics.median(lr)):.2f}× | "
                     f"{math.exp(statistics.fmean(lr)):.2f}× | "
                     f"{sum(1 for x in lr if abs(x) < math.log(2)) / len(lr) * 100:.0f}% |")
    o += ["", "⭐ **The turn law reproduces itself out of the reference data.** `turn_ratio` is "
          "`speed / turn_speed` — the divisor in Cameo's own law (turreted ground `Speed/5`, "
          "turretless `2×Speed/5`, helicopters and spaceships `Speed/5`, planes `Speed/15`). The "
          "reference consensus lands the Apocalypse at **5 → 5** and the Nod Buggy at **5 → 5**, "
          "and the whole HIGH-confidence population at a median of ~1.0×. Cameo legislated that "
          "divisor; thirteen independent rosters agree with it. That is a law confirmed from "
          "outside, not an artifact of the measurement.", "",
          f"## Reference targets — {len(report_rows)} Cameo actors with a signature", "",
          "`now` is the live ledger value; `target` is the reference consensus re-projected onto "
          "Cameo's distributions. Confidence is the number of independent sources that matched: "
          "HIGH ≥3, MEDIUM 2, LOW 1. A LOW row is one mod's opinion, not the genre's.", "",
          "| actor | type | stat | now | target | ratio | sources | confidence |",
          "|---|---|---|--:|--:|--:|--:|---|"]
    flat = []
    for c, t in report_rows:
        for stat, e in t.items():
            if e["now"]:
                flat.append((abs(math.log(e["target"] / e["now"])), c, stat, e))
    for _, c, stat, e in sorted(flat, key=lambda r: -r[0])[:120]:
        o.append(f"| `{c['id']}` | {c['type']} | {stat} | {e['now']:,.0f} | {e['target']:,.0f} | "
                 f"{e['target'] / e['now']:.2f}× | {e['sources']} | {e['confidence']} |")
    o += ["", "## Not in this layer, by scoping", "",
          "Weapons — damage, range, burst, burst delays, reload, effective DPS and the "
          "armor-aware effective damage behind it — are the next layer. Turn rate is here rather "
          "than there because Cameo's turn law is **relative to speed** (turreted ground "
          "`Speed/5`, turretless `2×Speed/5`, helicopters and spaceships `Speed/5`, planes "
          "`Speed/15`), so `turn_ratio = speed / turn_speed` is a chassis property and is "
          "measured as one.", ""]
    OUT_MD.write_text("\n".join(o) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
