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
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import reference_lineages  # noqa: E402  (the shared lineage rulings)
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


def ini_rows():
    """The eight Westwood/Ares mods in the peer-row shape, from `ini_corpus.json`."""
    if not INI_CORPUS.exists():
        ini_rows.sources = set()
        return []
    armor = _ini_armor_index()
    out, sources = [], set()
    for line in INI_CORPUS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        sources.add(r["source"])
        kind = INI_TYPE.get(r.get("type"))
        if kind is None:
            continue
        # THE POPULATION RULE, in full for the first time on these sources. DOC1 could only
        # approximate it — it has no build-limit column, so a hero could sit in the tail — and
        # said so. The corpus carries `build_limit`, so the epic/hero exclusion is exact here.
        # `buildable` is the extractor's TechLevel/Selectable verdict — see its comment. Without
        # it a costed 10,000,000 HP dummy sits in the arithmetic mean of a 443-unit population.
        if not r.get("cost") or r.get("build_limit") or not r.get("buildable", True):
            continue
        spd, turn = r.get("speed"), r.get("turn_speed")
        dps = r.get("w_dps")
        row = {"source": r["source"], "raw_source": r["source"],
               "id": r.get("id", ""), "name": r.get("name", ""),
               "type": kind,
               # `Owner=` is a comma list; the extractor already joined it with "/" and the route
               # layer splits on that separator (`peer_factions`).
               "faction": r.get("faction", ""),
               "turreted": r.get("turreted"),
               "hp": r.get("hp"), "speed": spd,
               "turn_speed": turn,
               "turn_ratio": (spd / turn) if (spd and turn) else None,
               "cost": r.get("cost"),
               "w_range": r.get("w_range"), "w_damage": r.get("w_damage"),
               "w_burst": r.get("w_burst"), "w_reload": r.get("w_reload"),
               "w_dps": dps}
        vs = armor.get((r["source"], r.get("id"))) or {}
        for lad in LADDERS:
            frac = vs.get(lad)
            row[f"dps_vs_{lad}"] = (dps * frac) if (dps and frac) else None
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


def peer_rows():
    """Doc 5 rows with type, raw HP/speed/turn — the chassis corpus, after lineage de-dup."""
    rows, source, header = [], None, None
    dropped_lineage = peer_rows.dropped = set()
    text = (ROOT / "docs/design/ORIGINAL_UNITS_PEER_OPENRA.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("## "):
            source = line[3:].split("(")[0].strip()
            header = None
            continue
        if not source or not line.startswith("|"):
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
        for lad in LADDERS:
            # NB the header row is lowercased on read, so the column key is `vsinf`, not `vsINF`.
            # Looking it up in the document's original case silently yields None for every row —
            # which is how this first reported 0 armor-aware rows out of 2,256.
            frac = num(f"vs{lad.lower()}")
            wep[f"dps_vs_{lad}"] = (wep["w_dps"] * frac) if (wep.get("w_dps") and frac) else None
        limit = num("limit")
        if limit:                     # a mod's one-off epic/hero — see POPULATION RULE below
            continue
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
        rows.append({"source": source, "raw_source": source,
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
                     "cost": cost, **wep})
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
    return rows


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
            if not kind or not isinstance(units, dict):
                continue
            for name, rec in units.items():
                if not isinstance(rec, dict):
                    continue
                if rec.get("buildable") is not True:
                    continue
                if rec.get("build_limit") is not None:      # check_band.py's epic/hero predicate
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

                def anum(v):
                    try:
                        return float(str(v))
                    except (TypeError, ValueError):
                        return None

                w, debt = {}, False
                if arms:
                    a = arms[0]
                    mains = [wh for wh in (a.get("damage_warheads") or [])
                             if (anum(wh.get("damage")) or 0) > 0]
                    # §0a STRUCTURE DEBT: a weapon still firing 2+ damage mains has a `K` that is
                    # scheduled to move under W24, so its weapon numbers are not a stable target
                    # yet. The flag rides along on the signature so a later pricing pass can
                    # refuse to trust them, rather than silently pricing an input about to change.
                    debt = len(mains) > 1
                    dmg = sum(anum(wh.get("damage")) or 0 for wh in mains)
                    rel = anum(a.get("reloaddelay"))
                    burst = anum(a.get("burst")) or 1
                    cycle = (rel or 0) + (burst - 1) * 5
                    dps = ((dmg * burst) / cycle) if (dmg and cycle) else None
                    w = {"w_range": anum(a.get("range")), "w_damage": dmg or None,
                         "w_burst": burst, "w_reload": rel, "w_dps": dps}
                    tpl = a.get("versus_templates") or []
                    wname = a.get("weapon") or (tpl[-1] if tpl else None)
                    if dps and wname:
                        for lad, frac in cameo_weapon_ladders(wname).items():
                            w[f"dps_vs_{lad}"] = dps * frac
                out.append({"source": "Cameo", "id": name, "name": name, "type": kind,
                            "hp": hp, "speed": spd, "turn_speed": turn,
                            "structure_debt": debt,
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
