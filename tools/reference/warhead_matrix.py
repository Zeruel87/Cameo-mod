#!/usr/bin/env python3
"""warhead_matrix.py — the full warhead x armor matrix for each reference mod, and for Cameo.

Maintainer order (2026-09-21): *"create that excel spreadsheet with everything included with all
warheads and all armor types and create this big VS matrix (warheads x armors) for each reference
game and then we will try to do the same for cameo and fit those matrices together with best
mapping possible ... the geometric mean of each matrix must be at 100 so they are comparable ...
Only if all the versus values in a matrix multiply to 1 can we multiply the matrices together."*

THE NORMALISATION, and why it is the right one
----------------------------------------------
Each source matrix is divided by its own USAGE-WEIGHTED GEOMETRIC MEAN and re-expressed on a
100 scale. After that, `prod(cell / 100) == 1` over the weighted matrix, so composing two
matrices multiplies shapes without moving total magnitude. A warhead's row geometric mean is
then, directly, its factor: 70 means the warhead delivers 0.7x the mod's own average output,
and a reference Damage read off that warhead must be scaled by 0.70 to be comparable.

This is the MISSING INVERSE of an existing law. DESIGN.md §12.0 and
`tools/reference/aggregate_archetype.py` both normalise a reference profile and say outright
that *"absolute lethality still lives in Damage, never in the armor profile"* — but nothing ever
handed the discarded magnitude back to Damage. This tool measures exactly what was discarded.

⚠ WHY THIS DOES NOT REUSE `docs/reference/versus_raw.json`
----------------------------------------------------------
That file is fine for the INI sources' raw values and is left untouched, but it cannot answer
this question, for two measured reasons:

  1. **Its OpenRA reader does not resolve `Inherits:`.** It is a hand-rolled indentation scanner
     whose "warhead" key is really the nearest non-indented key — the WEAPON name. Combined Arms
     has 716 weapons of which 508 inherit; resolving them through `miniyaml.Ruleset` finds
     **654** warhead tables where the scanner found 378.
  2. **It models none of DTA's armor system.** DTA (Vinifera) declares eleven armor types with
     INHERITANCE and per-armor defaults — `[light] BaseArmor=wood`, `[concrete] BaseArmor=heavy`,
     `[medium] Modifier=1000%`. A DTA warhead writing four rows really resolves to eleven, and
     1000% is DTA's neutral (the whole mod runs on a x10 scale). Reading only the stated rows
     both truncates the matrix and mis-scales it.

Everything here is read-only. It writes one workbook and one JSON sidecar; it changes no yaml,
no ledger and no committed reference artifact. In particular it NEVER regenerates
`ini_corpus.json` (a re-extract loses the dummy-primary promotion).

    python tools/reference/warhead_matrix.py --summary
    python tools/reference/warhead_matrix.py --write
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from miniyaml import Ruleset  # noqa: E402
import percentage_damage as pdm  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

GITHUB = pathlib.Path.home() / "Documents" / "GitHub"
REFDIR = GITHUB / "Cameo-mod-reference"
DTA_INI = REFDIR / "DTA Developer Edition" / "INI"

OUT_JSON = ROOT / "docs" / "reference" / "warhead_matrix.json"
OUT_XLSX = ROOT / "docs" / "reference" / "warhead_matrix.xlsx"

# ── Zero handling (maintainer ruling 2026-09-21) ──────────────────────────────────────────────
# A geometric mean is zero if any cell is zero, and zeros are common: 50 of 162 DTA warheads and
# 48 of 378 CA warheads carry at least one. Ruled: FLOOR zeros at 1 and keep the geometric mean.
# "Immune" is then a very small number rather than an undefined one, and the warhead still ranks.
ZERO_FLOOR = 1.0

# ⚠ ...BUT THE FLOOR'S VALUE IS NOT SCALE-FREE, AND THE SOURCES ARE NOT ON ONE SCALE.
#
# A geometric mean is a mean of LOGS, so a floored cell's influence is set by how far below the
# mod's normal value the floor sits — and that distance depends on the mod's units:
#
#     source          positive median   floored cells   a floored cell is...
#     DTA                        750.0           12.4%   750x below median  (ln 6.6)
#     Combined Arms              100.0            3.9%   100x below median  (ln 4.6)
#     OpenRA RA / TD              75.0            0.0%   -
#     Cameo                       94.0            0.0%   -
#
# DTA runs on a x10 scale (its neutral is `Modifier=1000%`), so an absolute floor of 1 punishes
# DTA roughly 1.8x harder than Combined Arms for encoding the SAME idea. Measured: DTA's
# denominator moves 263 -> 322 and its rifle warhead `SA` moves 1.71 -> 1.40 when the floor is
# made scale-relative, while CA, OpenRA TD and Cameo do not move at all.
#
# `FLOOR_MODE = "relative"` puts the floor at 1% of each mod's own positive median, so a floored
# cell is exactly 100x below normal in EVERY source. `"absolute"` is the maintainer's literal
# 2026-09-21 ruling and stays the default until that ruling is revisited.
FLOOR_MODE = "window"
FLOOR_FRACTION = 0.01

# ── "window" — Cameo's OWN legal band, applied to the reference data (maintainer 2026-09-21) ──
#
#   *"Our maximum possible spread that we allow in cameo is 200% to 10% so it's 20x,
#     so you can try to apply that same logic here."*
#
# DESIGN.md §12.0 rule 4 puts every Cameo Versus value in `[10, 200]` about a centre of 100 — a
# 20:1 window. Reading a reference matrix through that same window solves the scale problem
# outright, because the window is defined RELATIVE TO THE MATRIX'S OWN CENTRE and therefore
# carries no units: a floored zero sits one tenth of centre in every mod, whether that centre is
# 75 (OpenRA) or 750 (DTA). It also stops the OTHER tail — a reference cell at 4x its mod's
# centre is outside anything Cameo could express, so importing it whole is claiming a precision
# our own ladder cannot carry.
#
# Centre and window are mutually dependent (clamping moves the mean, which moves the window), so
# it is solved as a FIXPOINT rather than in one pass. It converges in a handful of rounds.
# ── Armor rows the maintainer has RULED OUT of the matrix (2026-09-21) ───────────────────────
# Each of these is a targeting switch, a terrain class or an engine special case rather than a
# unit armour rung. Leaving one in does real damage: an all-zero column (`Invulnerable`) floors
# one cell of EVERY row at the window bottom, and a wall class imports a barrier reading into a
# building ladder. They are dropped from the matrix entirely, not floored.
#
# `drone` and `special` are the YR engine's equivalents and are excluded for the same reason.
# `aggregate_archetype.py` already documents why `drone` in particular must never be imported as
# a light-vehicle rung: RA2's `drone` exists to tune ONE unit, the Terror Drone, so mods put a
# large anti-drone bonus there — the Tesla Coil reads 200 vs drone against ~100 for everything
# else. Read as "scout vehicle", that 200 is not a statement about scout vehicles at all.
_YR_EXCLUDED = {"drone", "special"}

EXCLUDED_ARMORS: dict[str, set[str]] = {
    "dta_enhanced":  {"rocket", "special"},
    "dta_classic":   {"rocket", "special"},
    "mental_omega":     set(_YR_EXCLUDED),
    "cnc_reloaded":     set(_YR_EXCLUDED),
    "rise_of_the_east": set(_YR_EXCLUDED),
    "ra20xx":           set(_YR_EXCLUDED),
    "ra2_reborn":       set(_YR_EXCLUDED),
    "red_resurrection": set(_YR_EXCLUDED),
    # ⛔ R58 — SHATTERED PARADISE SHIPS FIVE DEAD ARMOUR TAGS, the same defect OpenRA's Dune 2000
    # has below and found the same way: count who WEARS each tag against who NAMES it.
    #
    #     InfantryArmor / BuildingArmor / VehicleArmor / DefenseArmor / ConcreteArmor
    #     named by 3 warheads each, worn by ZERO actors.
    #
    # They are a renamed vocabulary's leftovers, and the giveaway is that the same three warheads
    # carry BOTH sets with DIFFERENT numbers — `BlackholeblastFinal` states `Building: 20` and
    # `BuildingArmor: 80`, `Heavy: 10` and `VehicleArmor: 50`. The engine evaluates the live row
    # and ignores the other; this matrix was reading both, so three warheads got five extra
    # columns of an older draft averaged into their profile, and every other SP warhead got five
    # unstated-100 cells that drag the window centre.
    # ⚠ `Bike` and `None` are KEPT although no warhead names them: one actor wears each, so the
    # game really does evaluate them. The rule is "drop what the engine never looks at", not
    # "drop what is thin".
    "shattered_paradise": {"InfantryArmor", "BuildingArmor", "VehicleArmor",
                           "DefenseArmor", "ConcreteArmor"},
    "combined_arms": {"Brick", "Tree"},       # Brick = BRIK/CHAIN/FENC/SBAG/SWAL, walls only
    "openra_ra":     {"Tree", "truk"},
    "openra_td":     set(),
    # D2K: `Concrete` is the concrete SLAB foundation — 0 actors in OpenRA's D2K wear it, and it
    # is the SOFTEST class in the table (column gmean 87.4 against CY's 25.5). It is terrain.
    "d2k_mod":       {"Invulnerable", "Concrete"},
    # ⚠ OpenRA's Dune 2000 ships CASE-DUPLICATED armour tags, and the duplicates are DEAD.
    # `DamageWarhead.DamageVersus` looks the armour up in a plain dictionary
    # (`Versus.ContainsKey(a.Info.Type)`), which is case-SENSITIVE, while every actor declares the
    # lowercase spelling. So a warhead writing `Versus: Heavy: 25` does nothing at all — measured,
    # `None`/`Wood`/`Light`/`Heavy`/`Concrete` are named by warheads and worn by ZERO actors.
    # Keeping them would average a row the game never evaluates into a live ladder.
    "openra_d2k":    {"None", "Wood", "Light", "Heavy", "Concrete",
                      "concrete", "invulnerable"},
    "cameo":         {"wall", "invulnerable", "harvester"},   # 0 actors declare these
    "cameo_resolved": {"wall", "invulnerable", "harvester"},
}

WINDOW_LO = 0.10     # DESIGN.md §12.0 rule 4: floor 10 against a centre of 100
WINDOW_HI = 2.00     # ... and ceiling 200. 20:1.
_WINDOW_ROUNDS = 200
_WINDOW_TOL = 1e-12


def floor_for(values: list[float]) -> float:
    """The zero floor this matrix should use, under the active FLOOR_MODE.

    `window` needs the whole clamp, not just a floor, so it returns the floor that the converged
    window implies and `clamp_to_window` does the rest.
    """
    if FLOOR_MODE == "absolute":
        return ZERO_FLOOR
    positive = sorted(v for v in values if v is not None and v > 0)
    if not positive:
        return ZERO_FLOOR
    if FLOOR_MODE == "relative":
        return max(positive[len(positive) // 2] * FLOOR_FRACTION, 1e-9)
    return max(_window_centre(values) * WINDOW_LO, 1e-12)


def _window_centre(values: list[float], weights: list[float] | None = None) -> float:
    """The centre a 20:1 window settles on for this matrix — a fixpoint, not one pass.

    Start from the geometric mean of the strictly positive cells, clamp everything into
    `[centre/10, centre*2]`, take the geometric mean again, and repeat. Clamping pulls both tails
    inwards so the centre moves, which moves the window; iterating until it stops moving is the
    only self-consistent answer.
    """
    positive = [v for v in values if v is not None and v > 0]
    if not positive:
        return 1.0
    if weights is None:
        weights = [1.0] * len(values)
    centre = math.exp(sum(math.log(v) for v in positive) / len(positive))
    for _ in range(_WINDOW_ROUNDS):
        lo, hi = centre * WINDOW_LO, centre * WINDOW_HI
        num = den = 0.0
        for value, weight in zip(values, weights):
            if weight <= 0 or value is None or value <= 0:   # N/A and zeros do not vote
                continue
            num += weight * math.log(min(max(value, lo), hi))
            den += weight
        if den == 0:
            return centre
        nxt = math.exp(num / den)
        if abs(nxt - centre) <= _WINDOW_TOL * max(centre, 1.0):
            return nxt
        centre = nxt
    return centre


def clamp_to_window(values: list[float], centre: float) -> list[float]:
    """Pull a row into `[centre*0.10, centre*2.00]`, DESIGN.md §12.0 rule 4's band.

    A zero passes through untouched: it is an absence, not a value at the bottom of the band.
    """
    lo, hi = centre * WINDOW_LO, centre * WINDOW_HI
    return [None if v is None else (0.0 if v <= 0 else min(max(v, lo), hi)) for v in values]

# A warhead every one of whose cells is zero is a dummy (BioDummyWH and friends). It carries no
# design opinion at all, so it is recorded and EXCLUDED from the matrix rather than floored into
# a fake 1.0 row that would drag the mod's mean down.
# Negative values (DTA writes `Modifier.none=-10%` for a healing warhead) are likewise excluded:
# a heal is not a damage multiplier and has no logarithm.


# ⛔ THE FLOOR IS APPLIED EXACTLY ONCE, when a row is read (`build_matrix`), and never again.
# Flooring inside the mean looks harmless and silently breaks the invariant the whole method
# rests on: after normalisation a legitimately tiny cell is BELOW 1 (a raw 0 floored to 1, then
# divided by DTA's denominator of 263, is 0.38), so a second `max(v, 1)` inside the mean lifts it
# and the normalised matrix no longer has geometric mean 100 — measured 110.1 for DTA, 98.0 for
# Combined Arms. Both means below are therefore PURE: they take the values they are given.


# ⛔ A ZERO IS NOT A SMALL NUMBER, IT IS AN ABSENCE (maintainer ruling, 2026-09-21).
#
# "This warhead does nothing to that armour" is not a multiplier near the bottom of the scale —
# it is a cell with no multiplier at all. Both means below therefore SKIP zeros, and the window
# clamp leaves them at zero.
#
# This is not a preference, it is the only thing that works. Treating a zero as `centre x 0.10`
# makes the window a runaway: clamping the zeros drags the mean down, which lowers the floor,
# which drags it further. Measured on Mental Omega (20.8% zeros), the centre marched
# 32.3 -> 13.5 -> 4.1 -> 1.2 -> 0.2 and never settled; at the end a real 60 and a real 100 both
# clamped to the ceiling and the entire matrix flattened. Every source above ~13% zeros did it:
# Rise of the East 27.7%, Red Resurrection 23.6%, Mental Omega 20.8%, CnC Reloaded 16.2%,
# RA2 Reborn 15.3%, RA20XX 13.9%. Below ~8% (Combined Arms 3.6%, DTA 6.9%) it converged fine,
# which is exactly why the flaw stayed invisible until the YR mods were added.
#
# ⚠ AND THE OBVIOUS CHECK CANNOT SEE IT. "The normalised matrix has geometric mean 100 and lies
# in [10,200]" holds BY CONSTRUCTION, because the matrix is normalised by the very centre being
# checked. That check passed on all seven degenerate sources. `--check` (see `sanity_report`)
# compares the centre against the source's own positive median instead, which is an INDEPENDENT
# quantity the normalisation cannot move, and is the only check that catches this class.
#
# Composition is unaffected where it matters: 0 x anything is still 0, so a warhead that cannot
# hurt X still cannot hurt X after two matrices are multiplied.

def gmean(values: list[float]) -> float:
    """Geometric mean over the cells that carry a multiplier. Zeros are skipped, not floored."""
    live = [v for v in values if v is not None and v > 0]
    if not live:
        return float("nan")
    return math.exp(sum(math.log(v) for v in live) / len(live))


def weighted_gmean(pairs: list[tuple[float, float]]) -> float:
    """Geometric mean of (value, weight) pairs, skipping zeros and zero-weight rows."""
    num = 0.0
    den = 0.0
    for value, weight in pairs:
        if weight <= 0 or value is None or value <= 0:
            continue
        num += weight * math.log(value)
        den += weight
    if den == 0:
        return float("nan")
    return math.exp(num / den)


# ══════════════════════════════════════════════════════════════════════════════════════════════
# OpenRA sources — read through miniyaml.Ruleset so `Inherits:` is resolved
# ══════════════════════════════════════════════════════════════════════════════════════════════

OPENRA_SOURCES = [
    ("combined_arms", "Combined Arms", GITHUB / "CAmod", "ca"),
    ("openra_ra", "OpenRA Red Alert", GITHUB / "OpenRA", "ra"),
    ("openra_td", "OpenRA Tiberian Dawn", GITHUB / "OpenRA", "cnc"),
    ("openra_ts", "OpenRA Tiberian Sun", GITHUB / "OpenRA", "ts"),
    ("openra_d2k", "OpenRA Dune 2000", GITHUB / "OpenRA", "d2k"),
    ("romanovs_vengeance", "Romanov's Vengeance", GITHUB / "Romanovs-Vengeance", "rv"),
    ("shattered_paradise", "Shattered Paradise", GITHUB / "Shattered-Paradise-SDK", "sp"),
    # ⚠ Crystallized Nexus keeps its mod under a DOT directory, `.modsdk/mods/cn`, so a plain
    # `ls` of the repo shows only docs/launcher/tools and the mod looks absent. It is not.
    ("crystallized_nexus", "Crystallized Nexus",
     GITHUB / "crystallized-nexus" / ".modsdk", "cn"),
]

# OpenRA's own default: `DamageWarhead.DamageVersus` returns 100 for any armor the table does not
# name (DamageWarhead.cs:80 — `Util.ApplyPercentageModifiers(100, armor)` over matching entries
# only). So an UNSTATED row is 100, never absent. Verified from engine source, not assumed: nine
# OpenRA TD warheads state a single row, and reading only stated rows scores `Heavy: 25` as 25
# when the warhead really averages ~76.
OPENRA_UNSTATED = 100.0


# ── A damage warhead with NO table is FLAT 100, not missing data ──────────────────────────────
# `DamageWarhead.DamageVersus` returns 100 outright when the table is empty (DamageWarhead.cs:80),
# so a `SpreadDamage` warhead that writes no `Versus` block really does deal full damage to every
# armor. Dropping those rows is not neutral: they are the most GENERALIST profiles a mod ships, so
# removing them pulls the matrix centre down and makes every surviving warhead look stronger than
# it is. Measured: 92 of Combined Arms' 704 damage warheads, 10 of 82 in OpenRA RA, 3 of 57 in TD.
#
# Non-damage warheads (CreateEffect, LeaveSmudge, SpawnActor, ...) have no table because they deal
# no damage at all; those stay out. The test is the type name, which is how the engine names them.
def is_damage_warhead(type_name: str) -> bool:
    name = (type_name or "").strip()
    if not name or "Damage" not in name:
        return False
    # A percentage twin's table is a MAGNITUDE, not a shape (DESIGN.md §12.0h scope note), so it
    # is only admitted when it actually states one — never flat-filled.
    return True


def is_flat_fillable(type_name: str) -> bool:
    name = (type_name or "").strip()
    return is_damage_warhead(name) and "Percentage" not in name


# ══════════════════════════════════════════════════════════════════════════════════════════════
# ⛔ "CANNOT TARGET" IS NOT "DEALS FULL DAMAGE" — the Aircraft-148 defect
# ══════════════════════════════════════════════════════════════════════════════════════════════
#
# Maintainer, 2026-09-21: *"Aircraft148 is there always even if the unit cannot even hit air
# which is annoying and completely misrepresenting everything!"*
#
# Right, and the cause is a default nobody sees. `WeaponInfo.ValidTargets` and `Warhead.ValidTargets`
# BOTH default to `new("Ground", "Water")` (WeaponInfo.cs:116, Warhead.cs:30), so a weapon that
# never mentions targeting simply CANNOT hit air. 366 of Combined Arms' 695 weapons are in exactly
# that position. Filling their unstated Aircraft row with the engine's 100 was doubly wrong: the
# engine never evaluates that row, and a tank cannon was being entered into the corpus as a
# competent anti-air weapon. It polluted every air row, every group that contained one, and the
# whole AIR ladder.
#
# The rule: a cell is N/A — not zero, not 100 — when the warhead cannot target that armour's macro
# class at all. N/A and "immune" are both excluded from every mean, but they are different
# statements and the workbook shows them differently.
AIR_TOKENS = {"air", "airsmall", "icbm"}

ARMOR_MACRO = {
    # infantry
    "none": "GND", "flak": "GND", "plate": "GND", "heroic": "GND", "infantry": "GND",
    "cyborg": "GND",
    # vehicles
    "scout": "GND", "light": "GND", "medium": "GND", "heavy": "GND", "superheavy": "GND",
    "drone": "GND", "harvester": "GND", "vehicle": "GND",
    # buildings
    "wood": "GND", "steel": "GND", "concrete": "GND", "brick": "GND", "building": "GND",
    "defense": "GND", "cy": "GND", "wall": "GND",
    # aircraft
    "aircraft": "AIR", "fighter": "AIR", "bomber": "AIR", "helicopter": "AIR",
    "spaceship": "AIR", "airborne": "AIR",
}


def targetable_macros(node, weapon) -> set[str]:
    """Which macro classes this warhead can actually hit: {"GND"}, {"AIR"} or both.

    The warhead's own `ValidTargets` wins where stated, else the weapon's, else the engine
    default of Ground+Water — which is NOT "everything".
    """
    raw = node.get("ValidTargets") or (weapon.get("ValidTargets") if weapon else None)
    invalid = node.get("InvalidTargets") or (weapon.get("InvalidTargets") if weapon else None)
    tokens = {t.strip().lower() for t in (raw or "Ground, Water").split(",") if t.strip()}
    blocked = {t.strip().lower() for t in (invalid or "").split(",") if t.strip()}
    tokens -= blocked

    macros: set[str] = set()
    if tokens & AIR_TOKENS:
        macros.add("AIR")
    if tokens - AIR_TOKENS:
        macros.add("GND")
    # An exotic target set naming neither (`Repairable`, `Temporal`) is declining to say; do not
    # silently delete its whole profile on the strength of a guess.
    return macros or {"GND", "AIR"}


def target_tokens(node, weapon) -> tuple[set[str], set[str]]:
    """The warhead's effective (valid, invalid) target tokens, same precedence as above.

    `targetable_macros` reduces these to GND/AIR, which is all the N/A masking needs. The FOLD
    needs them raw: a warhead restricted to `Infantry` must not be summed into the Heavy or Wood
    columns just because Infantry is a ground class.
    """
    raw = node.get("ValidTargets") or (weapon.get("ValidTargets") if weapon else None)
    invalid = node.get("InvalidTargets") or (weapon.get("InvalidTargets") if weapon else None)
    valid = {t.strip().lower() for t in (raw or "Ground, Water").split(",") if t.strip()}
    blocked = {t.strip().lower() for t in (invalid or "").split(",") if t.strip()}
    return valid, blocked


def _weapon_votes(rs, actors=None) -> tuple[collections.Counter, list[dict]]:
    """Weapon-slot votes over buildable actors, one vote per DISTINCT weapon per actor.

    The maintainer's ruling is one vote per weapon slot — a tank with a cannon and an MG casts
    two. But OpenRA declares extra Armament nodes for MECHANICAL reasons, not for extra weapons:
    RA's rocket soldier `e3` ships `Armament@PRIMARY: RedEye`, `@SECONDARY: Dragon`,
    `@GARRISONED: RedEye`, `@GARRISONEDSECONDARY: Dragon` — the same two weapons, at different
    firing ports. Counting nodes doubles every garrisonable infantryman's vote.

    So the vote is per (actor, weapon) pair: different weapons on one actor still vote separately,
    the same weapon re-declared for a second firing context does not.
    """
    votes: collections.Counter = collections.Counter()
    rows: list[dict] = []
    for name in sorted(actors if actors is not None else rs.actors):
        if name.startswith("^") or name.startswith("-"):
            continue
        try:
            actor = rs.resolve(name)
        except Exception:
            continue
        if actor is None or not _is_buildable(actor):
            continue
        seen: set[str] = set()
        for arm in actor.children_named("Armament"):
            weapon = arm.get("Weapon")
            if not weapon or weapon in seen:
                continue
            seen.add(weapon)
            votes[weapon] += 1
            rows.append({"actor": name, "slot": arm.key, "weapon": weapon})
    return votes, rows


def _is_buildable(actor) -> bool:
    """A `Buildable` block that is not `~disabled`.

    OpenRA keeps a Buildable block on critters so the map editor can place them, and gates it
    behind the `~disabled` prerequisite. Counting those as buildable units pollutes the usage
    weights with animals.
    """
    block = actor.child("Buildable")
    if block is None:
        return False
    prereq = block.get("Prerequisites") or ""
    return "~disabled" not in prereq


def read_openra(root: pathlib.Path, mod_id: str) -> dict:
    rs = Ruleset(root, mod_id)

    # ── armor census over buildable actors ────────────────────────────────────────────────────
    census: collections.Counter = collections.Counter()
    census_all: collections.Counter = collections.Counter()
    hp_samples: dict[str, list[float]] = collections.defaultdict(list)

    for name in sorted(rs.actors):
        if name.startswith("^") or name.startswith("-"):
            continue
        try:
            actor = rs.resolve(name)
        except Exception:
            continue
        if actor is None:
            continue
        # ⛔ `children_named`, NEVER `child` — an actor can carry SEVERAL Armor traits
        # (`Armor@HAZMAT`, `Armor@COMPOSITE`), and the engine honours all of them:
        # DamageWarhead.DamageVersus multiplies the Versus rows of every enabled Armor trait
        # it finds. `child("Armor")` sees only the first and makes every plating look dead.
        types = [a.get("Type") for a in actor.children_named("Armor")]
        types = [t for t in types if t]
        if not types:
            continue
        buildable = _is_buildable(actor)
        for armor_type in types:
            census_all[armor_type] += 1
            if buildable:
                census[armor_type] += 1
        # ⚠ HP per armour class, needed to price PERCENTAGE warheads in absolute damage — see
        # `fold_by_weapon`. Buildable actors only, for the same reason the usage census is: a husk
        # or a crate effect is not something anybody shoots at.
        if buildable:
            health = actor.child("Health")
            if health is not None:
                try:
                    points = float(health.get("HP") or 0)
                except (TypeError, ValueError):
                    points = 0.0
                if points > 0:
                    tt = set()
                    for tgt in actor.children_named("Targetable"):
                        tt |= {x.strip().lower()
                               for x in (tgt.get("TargetTypes") or "").split(",") if x.strip()}
                    for armor_type in types:
                        hp_samples[armor_type].append((points, frozenset(tt)))

    usage, slot_rows = _weapon_votes(rs)

    # ── warhead tables ────────────────────────────────────────────────────────────────────────
    profiles: list[dict] = []
    for wname in sorted(rs.weapons):
        if wname.startswith("^") or wname.startswith("-"):
            continue
        try:
            weapon = rs.resolve_weapon(wname)
        except Exception:
            continue
        if weapon is None:
            continue
        for node in weapon.children:
            if node.key != "Warhead" and not node.key.startswith("Warhead@"):
                continue
            table = pdm.versus_table(node)
            if not table:
                if not is_flat_fillable(node.value):
                    continue
                table = {}          # flat 100 — every unstated row fills to OPENRA_UNSTATED
            try:
                damage = float(node.get("Damage") or 0)
            except (TypeError, ValueError):
                damage = 0.0
            profiles.append({
                "weapon": wname,
                "node": node.key,
                "warhead_type": node.value or "",
                "table": {k: float(v) for k, v in table.items()},
                "uses": usage.get(wname, 0),
                "targets": sorted(targetable_macros(node, weapon)),
                "target_tokens": [sorted(s) for s in target_tokens(node, weapon)],
                # ⚠ Needed to FOLD a weapon's warheads together — see `fold_by_weapon`. The unit
                # differs by warhead type: absolute HP for the SpreadDamage family, percent of
                # the victim's max HP for `HealthPercentageDamage` (it resolves as
                # `HP x Damage/100 x Versus/100`, so `Damage: 300` is a 3x-overkill one-shot,
                # not a 300 HP chip). The two are never summed together.
                "damage": damage,
                "percentage": "Percentage" in (node.value or ""),
            })

    # The typical unit behind each armour class. GEOMETRIC mean, like everything else here: HP
    # runs 5,000 to 100,000 on a multiplicative grid, so an arithmetic mean would let the
    # heaviest building set the number for the whole class.
    armor_hp = {armor: gmean([hp for hp, _ in s]) for armor, s in hp_samples.items() if s}
    armor_actors = {armor: [(hp, sorted(tt)) for hp, tt in s]
                    for armor, s in hp_samples.items() if s}

    return {
        "kind": "openra",
        "armor_census": dict(census.most_common()),
        "armor_census_all": dict(census_all.most_common()),
        "armor_hp": armor_hp,
        "armor_actors": armor_actors,
        "profiles": profiles,
        "slots": slot_rows,
        "unstated_default": OPENRA_UNSTATED,
    }


# ══════════════════════════════════════════════════════════════════════════════════════════════
# DTA — the Vinifera INI dialect, with its declared armor system
# ══════════════════════════════════════════════════════════════════════════════════════════════

SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]")
# ⚠ THE KEY MAY BE A NUMBER. `[ArmorTypes]`, `[VehicleTypes]` and every other engine registry is
# an INDEXED list — `0=medium`, `1=naval_light` — so a key pattern anchored on a letter silently
# reads those sections as EMPTY. That is not a parse error anywhere: DTA simply came back with
# the five built-in armors instead of eleven, and zero units, and the matrix still built.
# ⛔ `$` IS A LEGAL FIRST CHARACTER. DTA (Vinifera) inherits sections with `$Inherits=Parent`, and a
# pattern that starts at a letter dropped every one of those lines in silence: 790 DTA sections -
# 56 warheads, 132 weapons, 315 units - were read without their parent, so an inheriting warhead
# such as `E3APRA` (`$Inherits=E3AP`) measured FLAT 100% everywhere. `extract_ini_units.py` had
# already fixed the same regex in its own reader; this one never got the fix. `read_dta` resolves
# the directive (R63).
KEY_RE = re.compile(r"^\s*(\$?[A-Za-z0-9_][A-Za-z0-9_.]*)\s*=\s*(.*?)\s*(?:;.*)?$")

# The five armor types the Tiberian Sun engine ships built in. DTA comments them out of its
# `[ArmorTypes]` list (`;=none`) precisely because they are implicit, then appends its own.
TS_BUILTIN_ARMORS = ["none", "wood", "light", "heavy", "concrete"]

# DTA's neutral multiplier. The whole mod runs on a x10 scale -- `[medium] Modifier=1000%`,
# `[rocket] Modifier=1000%` -- so 1000% is DTA's "100%". Any armor with neither an explicit
# warhead row nor a `BaseArmor` chain falls here.
DTA_NEUTRAL = 1000.0

DTA_UNIT_LISTS = ("InfantryTypes", "VehicleTypes", "AircraftTypes", "BuildingTypes")
INI_LIST_BAND = {"InfantryTypes": "infantry", "VehicleTypes": "vehicle",
                 "AircraftTypes": "aircraft", "BuildingTypes": "defense"}


# ══════════════════════════════════════════════════════════════════════════════════════════════
# ⛔ THE WESTWOOD INI DIALECTS CARRY DELIVERY AND ELEMENT IN A DIFFERENT SHAPE
# ══════════════════════════════════════════════════════════════════════════════════════════════
#
# `compress_warheads` keys on `Projectile:` for delivery and `DamageTypes:` for element. The INI
# mods have NEITHER, and the obvious substitute is a trap: Mental Omega's 1,117 weapons name
# projectiles `InvisibleWork`, `InvisibleHigh`, `CannonInviso` — trajectory and rendering variants,
# not weapon classes. Nine sources therefore compressed to nothing but `Unknown`.
#
# The real signals are there, spread over three places, and every token below was COUNTED in the
# actual files rather than taken from documentation:
#
#   weapon flags      `IsLaser` (MO 145, TI 18), `IsBigLaser`, `IsElectricBolt` (MO 42),
#                     `IsRailgun` (TI 25), `IsDetachedRailgun` (MO 93), `IsRadBeam`, `Lobber`
#   [Projectile] sect `ROT` (homing -> a missile), `Arcing` (ballistic -> a shell),
#                     `Inviso` (MO 121 — hits instantly, so hitscan), `Vertical` (a bomb)
#   warhead flags     `Fire`, `Tiberium` (MO 48, TI 50), `EMEffect`, `Bullets` (MO 71),
#                     `Radiation`, `Sonic`, `Temporal`, and `InfDeath` (MO 343, TI 138)
#
# ⚠ `InfDeath` IS A DEATH ANIMATION, exactly like OpenRA's `*Death` tokens, and the same caution
# applies: only the codes whose meaning is unambiguous across TS and RA2 are used — 3 burn, 4
# electrocute, 6 and 7 the chemical/mutation pair. The rest say nothing about the element.
# ⛔ MEASURED, NOT ASSUMED (R51). This table used to read {3: Fire, 4: Tesla, 6: Toxin, 7: Toxin}
# on the stated grounds that those codes are "unambiguous across TS and RA2". They are not, and
# the table was off by one on both elements it claimed to know.
#
# Calibrated by correlating each code against warhead NAMES in AGGREGATE across all seven INI
# sources — which is sound because it identifies a CODE TABLE from hundreds of warheads, not an
# individual weapon from its name (the thing R21 forbids). The pattern is identical in every
# source, `ts` dialect included:
#
#     code   fire-named (7 sources)        tesla-named (7 sources)
#       3    0  0  0  1  0  0  0            1  1  2  3  2  1  3
#       4   18 13 26 18 10 16  9            0  0  3  4  0  1  0
#       5    0  0  0  0  0  0  1            5 11 26  3  2  5  1
#
# So 4 is FIRE and 5 is ELECTRO, corpus-wide. The old table put Fire on 3 — which has NO fire
# correlation anywhere and ~450 warheads behind it — and Tesla on 4, which is where the fire
# weapons actually live. In Red Resurrection alone that mislabelled 82 warheads as Fire and 16
# genuine flamethrowers (`FlamethrowerWH`, `DevilFlamerWH`, `FirestormWH`) as Tesla.
#
# Codes 6 and 7 are dropped: they showed NO toxin correlation in any source. Toxin has a real
# signal already, `Tiberium=yes`, carried by 7-132 warheads per source.
# R51 calibrated 4=Fire and 5=Tesla by correlating each code against warhead NAMES in aggregate
# across all seven INI sources. R56 adds 8 the same way: its 51 carriers are `PlagueWH`,
# `VirusGas`, `AnthraxWH1/2`, `ChemWH`, `DrThraxWH`, `ToxicMolesWH`, `Gas`, `ToxinWH`, `Virus`,
# `GooCannonWH`, `EradicatorWH` — code 8 is the die-of-gas animation, and it is the INI dialect's
# ONLY broad toxin signal now that `Tiberium=yes` has been retired (see `ini_element`).
# ⚠ It is a FALLBACK and sits below the explicit flags on purpose: Red Resurrection's
# `FusionRadWH` and `RadBeamWarhead` carry code 8 and nothing else, because radiation and poison
# kill the same slow way in RA2. They will read Toxin and need a per-weapon override (R52).
INI_INFDEATH_ELEMENT = {"4": "Fire", "5": "Tesla", "8": "Toxin"}


def _ini_yes(block: dict[str, str], key: str) -> bool:
    return str(block.get(key, "")).strip().lower() in ("yes", "true", "1")


def ini_delivery(weapon: dict[str, str], projectile: dict[str, str]) -> str:
    """One weapon's delivery, from its own flags and its projectile's behaviour."""
    if _ini_yes(weapon, "IsLaser") or _ini_yes(weapon, "IsBigLaser"):
        return "Laser"
    # ⛔ `IsDetachedRailgun` IS NOT A RAILGUN SIGNAL. In Ares it only MODIFIES `IsRailgun` —
    # it moves where the beam is drawn from — so on its own it does nothing, and the mods set it
    # on weapons that are not railguns at all. Measured across the corpus, the overlap with
    # `IsRailgun` is EXACTLY ZERO in all three sources that use it:
    #
    #     mental_omega       93 set, 93 without `IsRailgun`   (20mm, AGGattling, AKM, Vulcan2)
    #     rise_of_the_east  323 set, 323 without
    #     ra20xx             52 set,  52 without
    #
    # 468 weapons were therefore delivered as "Railgun" while being machine guns and assault
    # rifles, which is why Mental Omega's `RailgunKinetic_*` groups read ANTI-INFANTRY in 9 of 11
    # cases — the PROFILES were right all along, small arms really are anti-infantry, and it was
    # the label on top of them that was wrong. MO's genuine railguns (`MutationRailgun`,
    # `ScavengerRailgun`, `RuinerRay`, `AlizeGun`) all carry `IsRailgun` and are unaffected.
    #
    # ⚠ `IsBigLaser` is the same SHAPE of flag and is deliberately NOT changed here: it is used
    # mostly alongside `IsLaser` (cnc_reloaded 40 set, only 14 orphaned) so the evidence is mixed,
    # and `IsRadEruption` is genuinely standalone in Ares. One flag, one measurement, one fix.
    if _ini_yes(weapon, "IsRailgun"):
        return "Railgun"
    if _ini_yes(weapon, "IsElectricBolt"):
        return "Tesla"
    if _ini_yes(weapon, "IsRadBeam") or _ini_yes(weapon, "IsRadEruption"):
        return "Radiation"
    # R60 — the YR wave flags, censused over the seven INI sources before deciding:
    #
    #   `IsSonic`    19 weapons — SonicZap, SonicBreak, OldSonicZap, TumbGun, GeneticBeam. Every
    #                one a sonic weapon. It is the same KIND of engine flag as `IsLaser` and
    #                `IsRailgun` above, and its absence here was an oversight: Twisted
    #                Insurrection's three SonicZaps read `Hitscan/Plain` for want of it.
    #   `IsMagBeam`  48 weapons — NOT mapped. It is the magnetic-wave VISUAL, and its carriers are
    #                the Magnetron, tractor/scramble/slowdown waves and disk drains (mechanics)
    #                alongside real damage weapons (TSSonicZap, RaijinZapX, ShadrayWave). One
    #                visual over many roles names none of them — the `EnergyDeath` lesson (R54)
    #                wearing a weapon flag instead of a death animation.
    #   `AmbientDamage` alone — 221 weapons, railguns and vulcans included. Not a signal.
    if _ini_yes(weapon, "IsSonic"):
        return "Sonic"
    if _ini_yes(projectile, "Vertical"):
        return "Bomb"
    try:
        turn = float(projectile.get("ROT", 0) or 0)
    except ValueError:
        turn = 0.0
    if turn > 0:
        return "Missile"                       # it steers, so it is a missile
    if _ini_yes(projectile, "Arcing") or _ini_yes(weapon, "Lobber"):
        return "Bullet"                        # ballistic shell
    if _ini_yes(projectile, "Inviso"):
        return "Hitscan"
    return "Bullet"


def ini_element(warhead: dict[str, str]) -> str:
    """One warhead's element. Explicit flags first, the death animation only as a fallback."""
    if _ini_yes(warhead, "Radiation") or warhead.get("RadLevel"):
        return "Radiation"
    if _ini_yes(warhead, "Sonic"):
        return "Sonic"
    if _ini_yes(warhead, "Temporal"):
        return "Atomized"
    # R56 — the INI dialect's only EXPLICIT toxin flag. Tiny and perfect: 9 carriers across the
    # seven sources, 8 of them toxin-named (`VirusGas` in five mods, `PurpleGasWH`, `ToxinWH2`).
    # It sits above `Fire` because a poison weapon that also burns is a poison weapon.
    if _ini_yes(warhead, "Poison"):
        return "Toxin"
    if _ini_yes(warhead, "Fire"):
        return "Fire"
    # ⛔ `EMEffect` IS A MECHANIC, NOT AN ELEMENT — the same class of mistake as R48's
    # `IsDetachedRailgun`. In RA2 it makes a warhead disable vehicles; Cameo models that as
    # Integrity/PhysicalState, never as a Versus row. Censused over the seven INI sources, it
    # marks ordinary ordnance and almost never a tesla weapon:
    #
    #     ra20xx            248 of 684 warheads (36%)   2 tesla-NAMED
    #     red_resurrection  110 of 480 (23%)            5 tesla-named  (105mmWH, 120mmWH,
    #                                                                   155mmWH, ATGUNWH — tank
    #                                                                   cannons and artillery)
    #     mental_omega       36 of 731 (5%)             0 tesla-named
    #     the other four     ~0
    #
    # Reading it as Tesla made Red Resurrection look like a mod built almost entirely out of
    # electricity: Missile/Tesla 17 groups, Bullet/Tesla 17, Hitscan/Tesla 11. Genuine tesla
    # weapons are still caught, and caught better, at the DELIVERY level by `IsElectricBolt`
    # (23-298 weapons per source) — which is the right place for it, because being an electric
    # bolt is how the thing is delivered.
    #
    # ⛔ CLOSED BY R51, and the note that used to sit here said the opposite. It read *"OPEN, NOT
    # FIXED: the `InfDeath` fallback assumes 3=burn / 4=electrocute, and that table is NOT stable
    # across mods… a design decision, not a bug fix"* — written after measuring ONE source.
    # Measuring all seven showed the pattern identical everywhere: it is 4=Fire, 5=Tesla, 8=Toxin,
    # an ordinary wrong constant with a corpus-wide fix. The stale note survived R51 by three
    # rulings because nothing greps code comments for superseded claims.
    #
    # ⛔ `Tiberium=yes` IS NOT AN ELEMENT EITHER — R56, and the fifth instance of this exact class
    # after `IsDetachedRailgun`, `EMEffect`, the `InfDeath` offset and `FlameDeath`. In TS/RA2 it
    # means the warhead interacts with Tiberium — detonates a field, hurts tiberium-armoured
    # things — so the mods set it on anything with a real explosion. Censused over the seven INI
    # sources on REAL warheads (sections a weapon actually points at, not the `TIB01`–`TIB20`
    # field overlays that inflate a naive count to 198 in CnC Reloaded alone):
    #
    #     378 carriers, of which 15 are toxin-NAMED — 4%.
    #     rise_of_the_east 111, ra20xx 102, twisted_insurrection 50, mental_omega 48,
    #     cnc_reloaded 47, ra2_reborn 16, red_resurrection 4
    #     and they are ARTYHE, BlimpHE, NukeWH, 40MMHE, APOCHE, CRNUKEWH — artillery,
    #     bombs, nukes and autocannon.
    #
    # It made CnC Reloaded's artillery, mortars, a railgun prototype and a sonic warhead — all
    # named `*HE` — read as chemical weapons. Retiring it moves 333 warheads off a wrong Toxin
    # label; `Poison` and `InfDeath=8` above add 43 correct ones.
    #
    # ⚠ REMAINING GAP, recorded rather than papered over: Twisted Insurrection's real chem
    # weapons (`ChemBurst`, `ChemSpray`, `Gas`, `ToxinBomb`, `BlueTibWH`) carry `InfDeath=1` and
    # `Tiberium=no`, so they read `Plain` — and they DID BEFORE THIS CHANGE TOO. TI has no
    # machine-readable element signal for them at all; they will need per-weapon overrides when
    # TI is assigned, the same way Romanov's Vengeance's flamethrowers did (R55).
    # ⛔ R59 — `Bullets=yes` USED TO SIT ABOVE THE DEATH-CODE FALLBACK AND STEAL FROM IT. It is
    # the small-arms flag, the INI dialect's spelling of exactly the signal the OpenRA dialect
    # ranks DEAD LAST: `ELEMENT_ORDER` ends with `("Kinetic", "BulletDeath")` under the comment
    # *"weak: explosive payload vs solid slug, used only when no strong signal is present"*. The
    # two dialects were ranking one concept at opposite ends of the table.
    #
    # 28 warheads across five sources carry BOTH, and the specific signal is right nearly every
    # time: `SAFlame`, `SSABFlame`, `FLAMEWH2` and `InfernoWH` are flamethrowers reading KINETIC,
    # and `Virus` — the virus sniper's warhead, in THREE sources — read Kinetic too.
    #
    # ⚠ I nearly rejected this fix on two false losses, and the lesson is the older one: READ THE
    # WEAPON, DO NOT GUESS FROM THE NAME. `BORISWH` and `ThorSSA` looked like a commando's rifle
    # and a heavy gun being wrongly electrified. They are not. BORISWH is fired by `EMPAKM_N`
    # with `Report=BorisTeslaAttack`; ThorSSA carries `EMEffect=yes` with `AnimList=TCCLOUD1B`,
    # thunderclouds. Both really are electric, and the demotion CORRECTS them.
    fallback = INI_INFDEATH_ELEMENT.get(str(warhead.get("InfDeath", "")).strip())
    if fallback:
        return fallback
    if _ini_yes(warhead, "Bullets"):
        return "Kinetic"
    try:
        spread = float(warhead.get("CellSpread", 0) or 0)
    except ValueError:
        spread = 0.0
    return "HE" if spread > 0 else "Plain"
# TS reads three weapon slots off a unit. `Elite=` is a real slot and was never extracted by the
# earlier reference pass (171 DTA declarations); it counts as a weapon slot like the other two.
DTA_WEAPON_SLOTS = ("Primary", "Secondary", "Elite")


def parse_ini(path: pathlib.Path) -> dict[str, dict[str, str]]:
    """{section: {key: value}}, comments skipped, later keys winning.

    DTA keeps ~186 commented-out `Verses=` lines as design history; a reader that does not skip
    comment lines would harvest a retired ruleset.
    """
    out: dict[str, dict[str, str]] = {}
    section = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lstrip().startswith(";"):
            continue
        head = SECTION_RE.match(line)
        if head:
            section = head.group(1)
            out.setdefault(section, {})
            continue
        if section is None:
            continue
        hit = KEY_RE.match(line)
        if hit:
            out[section][hit.group(1)] = hit.group(2)
    return out


def _registry_entries(ini: dict[str, dict[str, str]], section: str) -> list[str]:
    """Every actor/armor named by an engine registry section.

    ⚠ THE INDEX KEY IS NOT ALWAYS A NUMBER. Westwood's own files use `0=`, `1=`, but DTA labels
    its lists by faction — `[VehicleTypes]` reads `TD00=TDHARV`, `A_01=JEEP`, `B_01=BGGY`. A
    digits-only filter therefore returns ZERO vehicles out of 226 and the matrix still builds,
    just with every tank's warhead unweighted. Take the value of every key.
    """
    out: list[str] = []
    for value in (ini.get(section) or {}).values():
        name = value.split(";")[0].strip()
        if name:
            out.append(name)
    return out


def _ini_buildable(block: dict[str, str]) -> bool:
    """The reference pipeline's own population rule, matched exactly.

    `extract_ini_units.py` gates on the engine's two flags rather than on cost, because these
    mods price internal dummies at 1 credit. An ABSENT `TechLevel` counts as buildable: DTA sets
    much of it from injected map code, so treating "missing" as unbuildable would delete most of
    the roster. Keep this identical to `extract_ini_units.py` or the two disagree silently.
    """
    def num(token: str | None) -> float | None:
        if token is None:
            return None
        try:
            return float(token.strip())
        except ValueError:
            return None

    tech = num(block.get("TechLevel"))
    return not (
        (tech is not None and tech < 0)
        or (block.get("Selectable") or "").strip().lower() == "no"
        or (block.get("IsSelectableCombatant") or "").strip().lower() == "no")


def _pct(token: str) -> float | None:
    token = token.strip().rstrip("%").strip()
    try:
        return float(token)
    except ValueError:
        return None


def dta_armor_system(ini: dict[str, dict[str, str]]) -> tuple[list[str], dict[str, dict]]:
    """The declared armor ladder, plus each armor's `BaseArmor` parent and own default."""
    armors = list(TS_BUILTIN_ARMORS)
    for value in _registry_entries(ini, "ArmorTypes"):
        if value not in armors:
            armors.append(value)
    spec: dict[str, dict] = {}
    for armor in armors:
        block = ini.get(armor) or {}
        # `[special_heavy]` carries the section while `[ArmorTypes]` lists `special`; keep both
        # spellings resolvable rather than silently dropping one.
        if not block and armor + "_heavy" in ini:
            block = ini[armor + "_heavy"]
        spec[armor] = {
            "base": (block.get("BaseArmor") or "").strip() or None,
            "default": _pct(block.get("Modifier", "")) if block.get("Modifier") else None,
        }
    return armors, spec


def dta_resolve_row(stated: dict[str, float], armor: str,
                    spec: dict[str, dict], _seen: frozenset = frozenset()) -> float:
    """One armor's multiplier for one warhead, following `BaseArmor` then the armor's default.

    Cycle-guarded: a `BaseArmor` loop would otherwise recurse forever, and DTA's chains are
    hand-maintained (naval_light -> light -> wood is three deep already).
    """
    if armor in stated:
        return stated[armor]
    if armor in _seen:
        return DTA_NEUTRAL
    info = spec.get(armor) or {}
    parent = info.get("base")
    if parent:
        return dta_resolve_row(stated, parent, spec, _seen | {armor})
    if info.get("default") is not None:
        return float(info["default"])
    return DTA_NEUTRAL


# ── Actors excluded from every census and every usage vote (maintainer rulings 2026-09-21) ────
# `CHECK*` are DTA's deploy-probe dummies: 100 hp, `Primary=DeployWeapon2`, no Name, no TechLevel.
# Verified individually — CHECKGDI/none, CHECKNOD/wood, CHECKALI/medium, CHECKSOV/heavy. Counting
# them puts an infantry reading into the wood, medium and heavy ladders from four fake units.
#
# VOLKOV and CYP are real, buildable HEROES (4000 and 4500 hp, cost 2000, tech 7) that borrow
# VEHICLE armour. The standing hero-lane ruling keeps heroes out of ordinary distributions, so
# they are excluded too — which leaves DTA with a single infantry rung, `none`, and that is the
# honest reading of the mod.
DTA_EXCLUDED_ACTORS = {"CHECKGDI", "CHECKNOD", "CHECKALI", "CHECKSOV", "VOLKOV", "CYP"}


def _dta_excluded(actor: str) -> bool:
    return actor.upper() in DTA_EXCLUDED_ACTORS


def load_dta_ini(rules: pathlib.Path, overlay: pathlib.Path | None) -> dict[str, dict[str, str]]:
    """DTA's INI as the game reads it: each file's `$Inherits=` flattened, then the overlay on top.

    The SAME order `extract_ini_units.py` uses (flatten per file, then `merge_overlay`), so the
    warhead matrix and the unit corpus cannot read one DTA section two different ways (R63).
    """
    from extract_ini_units import resolve_inherits  # the one flattener; do not grow a second

    ini = resolve_inherits(parse_ini(rules))
    if overlay is not None and overlay.exists():
        for section, keys in resolve_inherits(parse_ini(overlay)).items():
            ini.setdefault(section, {}).update(keys)
    return ini


def read_dta(rules: pathlib.Path, overlay: pathlib.Path | None) -> dict:
    """DTA Classic (`Rules.ini`) or Enhanced (`Rules.ini` + `Enhance.ini` on top)."""
    ini = load_dta_ini(rules, overlay)

    armors, spec = dta_armor_system(ini)

    # ── warheads: any section stating at least one `Modifier.<armor>` ─────────────────────────
    stated_by_warhead: dict[str, dict[str, float]] = {}
    for section, keys in ini.items():
        stated: dict[str, float] = {}
        for key, value in keys.items():
            if not key.lower().startswith("modifier."):
                continue
            armor = key.split(".", 1)[1].strip().lower()
            pct = _pct(value)
            if pct is not None:
                stated[armor] = pct
        if stated:
            stated_by_warhead[section] = stated

    # ── weapons -> warhead, units -> weapon slots ─────────────────────────────────────────────
    weapon_warhead: dict[str, str] = {}
    for section, keys in ini.items():
        warhead = (keys.get("Warhead") or "").strip()
        if warhead:
            weapon_warhead[section] = warhead

    units: list[str] = []
    unit_band: dict[str, str] = {}
    for list_name in DTA_UNIT_LISTS:
        entries = _registry_entries(ini, list_name)
        units.extend(entries)
        for entry in entries:
            unit_band.setdefault(entry, INI_LIST_BAND[list_name])

    usage: collections.Counter = collections.Counter()
    slot_rows: list[dict] = []
    warhead_bands: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    warhead_deliveries: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter)
    census: collections.Counter = collections.Counter()
    census_all: collections.Counter = collections.Counter()
    for unit in units:
        if _dta_excluded(unit):
            continue
        block = ini.get(unit)
        if block is None:
            continue
        armor = (block.get("Armor") or "").strip().lower()
        if armor:
            census_all[armor] += 1
        buildable = _ini_buildable(block)
        if buildable and armor:
            census[armor] += 1
        if not buildable:
            continue
        for slot in DTA_WEAPON_SLOTS:
            weapon = (block.get(slot) or "").strip()
            if not weapon:
                continue
            warhead = weapon_warhead.get(weapon)
            if not warhead:
                continue
            usage[warhead] += 1
            slot_rows.append({"actor": unit, "slot": slot,
                              "weapon": weapon, "warhead": warhead})
            # DTA is the Tiberian Sun dialect: same signal shape as the other INI mods.
            warhead_bands[warhead][unit_band.get(unit, "vehicle")] += 1
            wblock = ini.get(weapon) or {}
            pblock = ini.get((wblock.get("Projectile") or "").strip()) or {}
            warhead_deliveries[warhead][ini_delivery(wblock, pblock)] += 1

    # A warhead a weapon actually FIRES but which states no `Modifier.<armor>` at all is not
    # missing data either — it resolves entirely through `BaseArmor` and the per-armor defaults,
    # i.e. it is DTA's flat/neutral profile. Same omission as the OpenRA no-table case, same fix.
    # Measured: `HellfireRA` -> `BazAPRA`, `70mmMslRA` -> `E3APRA` and 20 more are reachable from
    # a buildable unit and were being dropped.
    for warhead in set(weapon_warhead.values()):
        if warhead and warhead in ini and warhead not in stated_by_warhead:
            stated_by_warhead[warhead] = {}

    profiles = []
    for warhead, stated in sorted(stated_by_warhead.items()):
        table = {armor: dta_resolve_row(stated, armor, spec) for armor in armors}
        deliveries = warhead_deliveries.get(warhead)
        bands = warhead_bands.get(warhead)
        profiles.append({
            "weapon": warhead,
            "node": warhead,
            "delivery": deliveries.most_common(1)[0][0] if deliveries else "Bullet",
            "element": ini_element(ini.get(warhead) or {}),
            "band": bands.most_common(1)[0][0] if bands else "unused",
            "warhead_type": "",
            "table": table,
            "stated": stated,
            "uses": usage.get(warhead, 0),
        })

    return {
        "kind": "ini",
        "armors": armors,
        "weapon_warhead": weapon_warhead,
        "armor_spec": spec,
        "armor_census": dict(census.most_common()),
        "armor_census_all": dict(census_all.most_common()),
        "profiles": profiles,
        "slots": slot_rows,
        "unstated_default": None,     # resolved per armor via BaseArmor / Modifier
    }


# ══════════════════════════════════════════════════════════════════════════════════════════════
# Westwood INI mods — the POSITIONAL `Verses=` dialect
# ══════════════════════════════════════════════════════════════════════════════════════════════
#
# ⛔ ORDER IS THE DATA. `Verses=100%,70%,...` is a positional list against the engine's armour
# enumeration, so decoding it against the wrong enumeration shifts every value by one armour and
# produces a table that looks entirely plausible and is entirely wrong. ARITY IS THEREFORE A HARD
# GUARD: a row whose value count matches no known enumeration is recorded as undecoded and
# dropped, never guessed at. Measured arities, 2026-09-21:
#   Mental Omega 731x11 · Red Resurrection 480x11 · RA2 Reborn 176x11   (clean)
#   CnC Reloaded 353x11 + one 13 + one 15        (Ares can add armour types)
#   Rise of the East 1050x11 + one 12
#   RA20XX 675x11 + two 10, one 12, six 21
#   Twisted Insurrection 154x5                   (Tiberian Sun engine)
YR_ARMORS = ("none", "flak", "plate", "light", "medium", "heavy",
             "wood", "steel", "concrete", "drone", "special")
TS_ARMORS = ("none", "wood", "light", "heavy", "concrete")
ARMOR_ORDERS = {"yr": {11: YR_ARMORS}, "ts": {5: TS_ARMORS}}


def read_ini_verses(path: pathlib.Path, engine: str) -> dict:
    """One Westwood INI mod: armour table, weapon->warhead chain and weapon-slot usage."""
    ini = parse_ini(path)
    orders = ARMOR_ORDERS[engine]
    armors = list(YR_ARMORS if engine == "yr" else TS_ARMORS)

    stated: dict[str, dict[str, float]] = {}
    undecoded = 0
    for section, keys in ini.items():
        raw = keys.get("Verses")
        if not raw:
            continue
        tokens = [t.strip() for t in raw.split(",")]
        order = orders.get(len(tokens))
        if order is None:
            undecoded += 1
            continue
        values = [_pct(t) for t in tokens]
        if any(v is None for v in values):
            undecoded += 1
            continue
        stated[section] = dict(zip(order, values))

    weapon_warhead = {sec: (k.get("Warhead") or "").strip()
                      for sec, k in ini.items() if (k.get("Warhead") or "").strip()}

    # A warhead a weapon FIRES but which states no Verses is the engine's neutral 100 against
    # everything — the same omission as the OpenRA no-table case, and the same fix.
    for warhead in set(weapon_warhead.values()):
        if warhead and warhead in ini and warhead not in stated:
            stated[warhead] = {a: 100.0 for a in armors}

    units: list[str] = []
    unit_band: dict[str, str] = {}
    for list_name in DTA_UNIT_LISTS:
        entries = _registry_entries(ini, list_name)
        units.extend(entries)
        for entry in entries:
            unit_band.setdefault(entry, INI_LIST_BAND[list_name])

    usage: collections.Counter = collections.Counter()
    slot_rows: list[dict] = []
    warhead_bands: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    warhead_deliveries: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter)
    census: collections.Counter = collections.Counter()
    census_all: collections.Counter = collections.Counter()
    for unit in units:
        block = ini.get(unit)
        if block is None:
            continue
        armor = (block.get("Armor") or "").strip().lower()
        if armor:
            census_all[armor] += 1
        buildable = _ini_buildable(block)
        if buildable and armor:
            census[armor] += 1
        if not buildable:
            continue
        seen: set[str] = set()
        for slot in DTA_WEAPON_SLOTS:
            weapon = (block.get(slot) or "").strip()
            if not weapon or weapon in seen:
                continue
            seen.add(weapon)
            warhead = weapon_warhead.get(weapon)
            if not warhead:
                continue
            usage[warhead] += 1
            slot_rows.append({"actor": unit, "slot": slot,
                              "weapon": weapon, "warhead": warhead})
            # A warhead's band is the band of the actors that FIRE it — the same rule the
            # OpenRA path uses — and its delivery comes from the weapon plus that weapon's
            # projectile BEHAVIOUR (see `ini_delivery`; the projectile NAME is useless here).
            warhead_bands[warhead][unit_band.get(unit, "vehicle")] += 1
            wblock = ini.get(weapon) or {}
            pblock = ini.get((wblock.get("Projectile") or "").strip()) or {}
            warhead_deliveries[warhead][ini_delivery(wblock, pblock)] += 1

    profiles = []
    for warhead, table in sorted(stated.items()):
        # ⚠ Several weapons can share one warhead and disagree about delivery — a laser and a
        # cannon both firing `HighExplosive`. The majority decides, as it does for the band.
        deliveries = warhead_deliveries.get(warhead)
        bands = warhead_bands.get(warhead)
        profiles.append({
            "weapon": warhead, "node": warhead, "warhead_type": "",
            "table": {a: float(table.get(a, 100.0)) for a in armors},
            "stated": table,
            "uses": usage.get(warhead, 0),
            "delivery": deliveries.most_common(1)[0][0] if deliveries else "Bullet",
            "element": ini_element(ini.get(warhead) or {}),
            "band": bands.most_common(1)[0][0] if bands else "unused",
        })

    return {
        "kind": "ini",
        "armors": armors,
        "armor_spec": {a: {"base": None, "default": None} for a in armors},
        "armor_census": dict(census.most_common()),
        "armor_census_all": dict(census_all.most_common()),
        "profiles": profiles,
        "slots": slot_rows,
        "weapon_warhead": weapon_warhead,
        "unstated_default": None,
        "undecoded_rows": undecoded,
    }


EXTRACTION = REFDIR / "extraction"
INI_SOURCES = [
    ("mental_omega", "Mental Omega 3.3.6", EXTRACTION / "rulesmd_MO336.ini", "yr"),
    ("cnc_reloaded", "CnC Reloaded 2.7.0", EXTRACTION / "rulesmd_CnCR270.ini", "yr"),
    # 3.0.6, extracted from the 3.0.0c->3.0.6 patch's expandmd89.mix with extraction/deep_mix.py.
    # Its own header reads "This RULESMD.INI belongs to Rise of the East v3.0.6"; 1064 Verses
    # rows against 3.0.0c's 1051.
    ("rise_of_the_east", "Rise of the East 3.0.6", EXTRACTION / "rulesmd_RotE306.ini", "yr"),
    ("ra20xx", "RA20XX 1.0.8", EXTRACTION / "rulesmd_RA20XX108.ini", "yr"),
    ("ra2_reborn", "RA2 Reborn 1.0.31", EXTRACTION / "rulesmd_Reborn1031.ini", "yr"),
    ("red_resurrection", "Red Resurrection 2.2.13", EXTRACTION / "rulesmd_RedRes2213.ini", "yr"),
    ("twisted_insurrection", "Twisted Insurrection 0.9",
     EXTRACTION / "rules_TwistedInsurrection.ini", "ts"),
]


# ══════════════════════════════════════════════════════════════════════════════════════════════
# STATIC sources — a table supplied by hand because no rules file is on disk
# ══════════════════════════════════════════════════════════════════════════════════════════════
#
# ⚠ HAND-TRANSCRIBED FROM A SCREENSHOT, 2026-09-21. Every other source in this file is READ from
# a rules file, so a mistake there is a parser bug somebody can find twice. This one is a row of
# digits a human copied off an image, and nothing downstream can detect a wrong digit. It is kept
# separate, labelled, and must be re-verified against the mod's own rules file before it is
# allowed to move a balance number.
#
# ⚠ AND IT HAS NO USAGE DATA. The unit list was not supplied, so this source cannot be
# usage-weighted like the others; `build_matrix` falls back to an UNWEIGHTED centre and says so.
# Supplying the mod's rules file upgrades it automatically.
#
# Source: a Dune 2000 mod's armour/warhead editor, showing 10 of 64 armour slots and 14 of 64
# warhead slots — i.e. the base Dune 2000 vocabulary, with room the mod has not used yet.
# `Radius` and `InfDth` are the editor's own extra columns, kept because SPREAD_FALLOFF_PLAN.md
# wants measured blast radii; they are NOT armour rows and never enter the matrix.

D2K_ARMORS = ["None", "Wall", "Building", "Wood", "Light", "Heavy",
              "Concrete", "Invulnerable", "CY", "Harvester"]

# warhead: [the 10 armour values] + (radius, infantry death type)
D2K_ROWS: dict[str, tuple[list[float], int, int]] = {
    "W_FIRE":         ([90,   5,  65,  50,  40,  30, 100, 0,  20,  25], 64, 0),
    "W_DEVIATE":      ([20,  20,  20,  20,  20,  20,  20, 0,  20,  20], 20, 0),
    "W_SPECIAL":      ([90,  50,  75,  60,  60,  60, 100, 0,  25,  60], 64, 0),
    "W_WORM":         ([100,  5,   0,   0,   0,   0,   0, 0,   0,   0],  1, 0),
    "W_NOTHING":      ([0,    0,   0,   0,   0,   0,   0, 0,   0,   0], 15, 0),
    "W_BULLET":       ([100, 10,  25,  75,  40,  20, 100, 0,  20,  25], 15, 1),
    "W_AT":           ([20,  50,  50,  60, 100,  75, 100, 0,  20,  50], 32, 2),
    "W_GT_AT":        ([25, 100,  50,  65, 100,  50, 100, 0,  20,  50], 32, 2),
    "W_AT_MIS":       ([15,  75,  60,  65,  90, 100, 100, 0,  30,  50], 32, 2),
    "W_BAZOOKA":      ([8,   75,  40,  45,  70, 100, 100, 0,  20,  50], 32, 2),
    "W_PLASMA":       ([50, 100,  75,  60, 100, 100, 100, 0,  40, 100], 32, 2),
    "W_PLASMA_DEATH": ([100,100, 100, 100, 100, 100, 100, 0, 100, 100], 96, 2),
    "W_SONIC":        ([100, 50,  60, 100, 100,  60, 100, 0,  20,  50], 64, 3),
    "W_HE":           ([125,100, 100,  70,  30,  20, 100, 0,  20,  25], 64, 3),
}

# `Invulnerable` is zero for every warhead in the table — it is the engine's "cannot be hurt"
# class, not an armour rung, and an all-zero COLUMN would floor one cell of every row at the
# window bottom for no design reason. Excluded like DTA's `rocket`/`special`.
D2K_EXCLUDE_ARMORS = {"Invulnerable"}


def read_d2k_mod() -> dict:
    armors = [a for a in D2K_ARMORS if a not in D2K_EXCLUDE_ARMORS]
    keep = [i for i, a in enumerate(D2K_ARMORS) if a not in D2K_EXCLUDE_ARMORS]
    profiles = []
    for warhead, (values, radius, infdth) in D2K_ROWS.items():
        profiles.append({
            "weapon": "",
            "node": warhead,
            "warhead_type": "",
            "table": {armors[j]: float(values[i]) for j, i in enumerate(keep)},
            "stated": {armors[j]: float(values[i]) for j, i in enumerate(keep)},
            "uses": 0,                      # no unit list supplied — see the note above
            "radius": radius,
            "infantry_death": infdth,
        })
    return {
        "kind": "ini",                      # complete rows, nothing to fill in
        "armors": armors,
        "armor_spec": {a: {"base": None, "default": None} for a in armors},
        "armor_census": {},                 # unknown: no unit list
        "armor_census_all": {},
        "profiles": profiles,
        "slots": [],
        "unstated_default": None,
        "transcribed": True,
    }


# ══════════════════════════════════════════════════════════════════════════════════════════════
# Cameo — our own matrix, read the same way
# ══════════════════════════════════════════════════════════════════════════════════════════════

def read_cameo(granularity: str = "template") -> dict:
    """Cameo's own matrix.

    `granularity="template"` is the one to MAP AGAINST: the rows are the `^Warhead_<Family>_<Level>`
    templates, which are Cameo's actual warhead vocabulary (DESIGN.md §12.0h normalises exactly
    these). Usage flows up from the concrete weapons that inherit each template, so a template on
    twenty units weighs twenty.

    `granularity="resolved"` is the ground truth underneath it — one row per concrete weapon's
    warhead node. It exists so the template view can be checked against what actually ships, and
    because 1,463 concrete weapons still inherit NO `^Warhead_*` template at all (the W23/A5
    retrofit backlog) and are therefore invisible to the template view.
    """
    rs = Ruleset(ROOT, "cameo")
    census: collections.Counter = collections.Counter()
    census_all: collections.Counter = collections.Counter()
    for name in sorted(rs.actors):
        if name.startswith("^") or name.startswith("-"):
            continue
        try:
            actor = rs.resolve(name)
        except Exception:
            continue
        if actor is None:
            continue
        # ⛔ `children_named`, NEVER `child` — an actor can carry SEVERAL Armor traits
        # (`Armor@HAZMAT`, `Armor@COMPOSITE`), and the engine honours all of them:
        # DamageWarhead.DamageVersus multiplies the Versus rows of every enabled Armor trait
        # it finds. `child("Armor")` sees only the first and makes every plating look dead.
        types = [a.get("Type") for a in actor.children_named("Armor")]
        types = [t for t in types if t]
        if not types:
            continue
        buildable = _is_buildable(actor)
        for armor_type in types:
            census_all[armor_type] += 1
            if buildable:
                census[armor_type] += 1

    usage, slot_rows = _weapon_votes(rs)

    # Votes flow from the concrete weapon up to every `^Warhead_*` template it inherits.
    template_votes: collections.Counter = collections.Counter()
    template_members: dict[str, list[str]] = collections.defaultdict(list)
    for wname, raw in rs.weapons.items():
        if wname.startswith("^") or wname.startswith("-"):
            continue
        for _, parent in rs.inherits_of(raw):
            if parent.startswith("^Warhead_"):
                template_votes[parent] += usage.get(wname, 0)
                template_members[parent].append(wname)

    profiles = []
    if granularity == "template":
        for wname in sorted(rs.weapons):
            if not wname.startswith("^Warhead_"):
                continue
            try:
                weapon = rs.resolve_weapon(wname)
            except Exception:
                continue
            if weapon is None:
                continue
            for node in weapon.children:
                if node.key != "Warhead" and not node.key.startswith("Warhead@"):
                    continue
                table = pdm.versus_table(node)
                if not table:
                    if not is_flat_fillable(node.value):
                        continue
                    table = {}
                profiles.append({
                    "weapon": wname,
                    "node": node.key,
                    "warhead_type": node.value or "",
                    "table": {k: float(v) for k, v in table.items()},
                    "uses": template_votes.get(wname, 0),
                    "members": len(template_members.get(wname, [])),
                    "targets": sorted(targetable_macros(node, weapon)),
                    "target_tokens": [sorted(s) for s in target_tokens(node, weapon)],
                })
    else:
        for wname in sorted(rs.weapons):
            if wname.startswith("^") or wname.startswith("-"):
                continue
            try:
                weapon = rs.resolve_weapon(wname)
            except Exception:
                continue
            if weapon is None:
                continue
            for node in weapon.children:
                if node.key != "Warhead" and not node.key.startswith("Warhead@"):
                    continue
                table = pdm.versus_table(node)
                if not table:
                    if not is_flat_fillable(node.value):
                        continue
                    table = {}
                profiles.append({
                    "weapon": wname,
                    "node": node.key,
                    "warhead_type": node.value or "",
                    "table": {k: float(v) for k, v in table.items()},
                    "uses": usage.get(wname, 0),
                    "targets": sorted(targetable_macros(node, weapon)),
                    "target_tokens": [sorted(s) for s in target_tokens(node, weapon)],
                })

    return {
        "kind": "openra",
        "armor_census": dict(census.most_common()),
        "armor_census_all": dict(census_all.most_common()),
        "profiles": profiles,
        "slots": slot_rows,
        "unstated_default": OPENRA_UNSTATED,
    }


# ══════════════════════════════════════════════════════════════════════════════════════════════
# Matrix assembly
# ══════════════════════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════════════════════
# ⛔ A WEAPON'S PROFILE IS THE SUM OF ITS WARHEADS, NOT ITS BIGGEST ONE — the false-immunity defect
# ══════════════════════════════════════════════════════════════════════════════════════════════
#
# Maintainer, 2026-09-21, reviewing the Combined Arms groups, four separate times:
#   *"why is light immune? this doesn't make any sense and is a bug"*   (BulletFire_Veh)
#   *"how is the damage so low against None?"*                          (BombAP_Air)
#   *"none immune is a bug, this can't be right?"*                      (BulletAP_Air_2)
#   *"are you sure that anti light is only at 18 while the rest is all at 176?"* (Radiation_Veh)
#
# All four are the same defect, and it is mine. `compress_warheads` reduced each weapon to ONE
# warhead (rightly — DESIGN.md §11b, and the maintainer had asked for it after seeing groups that
# mixed unrelated things) but it picked that warhead by NAME, `Warhead@1Dam` first. In Combined
# Arms that convention does not mean "the main one". 116 of 466 armed weapons carry more than one
# damage warhead, and they are routinely COMPLEMENTARY — each covers the armour classes the other
# zeroes out, because OpenRA fires every warhead on every hit:
#
#   FireballLauncher  @1Dam Light=0   + @2Dam Light=50, everything else 0  -> NOT Light-immune
#   JDAM              @1Dam None=0    + @2Dam None=100, everything else 0  -> NOT infantry-immune
#   MaverickSU        @1Dam None=0    + @2Dam None=100, everything else 0  -> NOT infantry-immune
#   ApocRadBeamWeapon @1Dam is a `HealthPercentageDamage` INFANTRY-ONLY rider stating one row
#                     (`Light: 10`); the weapon's real table is on @2Dam.
#
# Picking one and discarding the rest reports a false ZERO — the single worst kind of error here,
# because the whole point of this pipeline is that time-to-kill survives the compression, and a
# zero says "this matchup never ends".
#
# So: fold, do not pick. Effective damage against armour A is what the engine actually inflicts,
#   effective(A) = SUM over warheads w that can reach A of  damage_w x versus_w(A) / 100
# and the weapon's folded Versus row is that expressed against its own total damage,
#   versus(A) = 100 x effective(A) / D,   D = SUM of damage_w
# so a warhead that cannot reach A contributes 0 to the numerator and still counts in D. That
# keeps the RATIOS between armour rows equal to the ratios of real effective damage, which is
# the quantity the whole exercise is trying to preserve. (Dividing by a per-armour denominator
# instead — a plain weighted average — silently flattens exactly the weapons that split their
# target sets: it reports ApocRadBeamWeapon at 2.14x infantry-vs-light where the truth is 2.64x.)
#
# ── A PERCENTAGE WARHEAD IS PRICED THROUGH THE TYPICAL UNIT IT HITS ──────────────────────────
#
# Maintainer, 2026-09-21: *"percentage warheads need to be regarded as a flat damage against the
# average unit of that armor type, so for example 300% against the average of 50k HP light armor
# means it's 150k damage against light right?"* — yes, and the first version of this fold ducked
# the question by excluding percentage warheads entirely, which is its own misreport: a sniper
# whose whole anti-infantry punch is a 300%-of-HP warhead read as a mild anti-vehicle gun.
#
# `HealthPercentageDamage` resolves as `HP x Damage/100 x Versus/100` (HealthPercentageDamageWarhead.cs),
# so its damage against armour class `A` is `avgHP(A) x Damage/100` — armour-DEPENDENT, unlike a
# flat warhead. That dependence is the point: a percentage weapon really is relatively better
# against a heavy class than a light one, and pricing it through `avgHP(A)` is what puts that in
# the row. `avgHP` is the geometric mean HP of the buildable actors declaring that armour.
#
# ⚠ Overkill is deliberately NOT modelled, on the maintainer's instruction ("300% ... means it's
# 150k damage"). A 300% warhead reads as three kills' worth of damage. This is consistent with
# the flat side, where a 25,000-damage shell aimed at a 5,000 HP infantryman also reads at full
# value; capping only one of the two would bias the comparison rather than fix it.
def fold_by_weapon(rows: list[dict], armors: list[str],
                   armor_hp: dict[str, float] | None = None,
                   armor_actors: dict[str, list] | None = None) -> list[dict]:
    """One row per weapon: its warheads summed by effective damage. See the notes above."""
    by_weapon: dict[str, list[dict]] = collections.defaultdict(list)
    for row in rows:
        by_weapon[row["weapon"] or row["node"]].append(row)

    hp_ci = {k.lower(): v for k, v in (armor_hp or {}).items()}
    actors_ci = {k.lower(): v for k, v in (armor_actors or {}).items()}
    # One scalar reference for the DENOMINATOR. It must not vary by armour: a per-armour
    # denominator is the weighted average that flattens split-target weapons (see above).
    hp_ref = gmean(list(hp_ci.values())) if hp_ci else 0.0

    # ⛔ "GROUND" IS NOT FINE-GRAINED ENOUGH FOR THE FOLD.
    # The N/A masking only has to answer GND-or-AIR, so `targetable_macros` reduces the target
    # set to that. The fold cannot: 380mm's second warhead deals 70,000 with `ValidTargets:
    # Infantry`, and summing that into the Heavy and Wood columns — both "ground" — turns a
    # siege gun into a tank killer. The same masking bug is what made the percentage warheads
    # read as anti-building: 300% of Wood's 89,166 HP is enormous, and the sniper's infantry-only
    # rider was landing there. So resolve reachability per ARMOUR CLASS, against the target types
    # the buildable actors of that class actually declare, and take the typical HP from the
    # subset a given warhead can really hit.
    def _hittable(row: dict, armor: str) -> list[float]:
        pool = actors_ci.get(armor.lower())
        tokens = row.get("target_tokens")
        if not pool:
            return []
        if not tokens:
            return [hp for hp, _ in pool]
        valid, blocked = set(tokens[0]), set(tokens[1])
        hits = [hp for hp, tt in pool
                if (set(tt) & valid) and not (set(tt) & blocked)]
        # An exotic target set naming nothing an actor declares (`Repairable`, `Mine`) is
        # declining to say rather than saying "nothing" — same reasoning as targetable_macros.
        return hits if hits else []

    def coverage(row: dict, armor: str) -> float:
        """What FRACTION of that armour class this warhead can actually hit.

        ⚠ Reachability alone is not enough, because a Versus row is a per-CLASS multiplier. Three
        of Combined Arms' 63 Light-armour actors are cyborgs declaring `Infantry`, so a sniper's
        infantry-only rider was reaching the Light column and landing there at full strength —
        putting `Light` ABOVE `None` on a sniper. A warhead that can touch 3 of 63 contributes
        3/63 of its damage to what the class as a whole expects.
        """
        pool = actors_ci.get(armor.lower())
        if not pool:
            return 1.0
        return len(_hittable(row, armor)) / len(pool)

    def reaches(row: dict, index: int, armor: str) -> bool:
        if row["values_raw"][index] is None:
            return False
        return coverage(row, armor) > 0 if actors_ci else True

    def damage_against(row: dict, armor: str) -> float:
        """What this warhead actually inflicts on that armour class, in HP."""
        damage = float(row.get("damage") or 0)
        if not row.get("percentage"):
            return damage
        hits = _hittable(row, armor)
        typical = gmean(hits) if hits else hp_ci.get(armor.lower(), hp_ref)
        return typical * damage / 100.0

    def damage_nominal(row: dict) -> float:
        """The same, against the typical unit THIS warhead can hit — the row's scale constant.

        ⚠ It must be one scalar (a per-armour denominator flattens split-target weapons), but it
        must not be the mod-wide average either: an infantry-only 300%-of-HP rider is 300% of an
        INFANTRYMAN, and pricing it against the mod's 30,000 HP average made the sniper's whole
        row collapse to a third of its true magnitude. So: the typical unit across everything the
        warhead actually reaches, pooled over armour classes.
        """
        damage = float(row.get("damage") or 0)
        if not row.get("percentage"):
            return damage
        reachable = [hp for armor in armors for hp in _hittable(row, armor)]
        typical = gmean(reachable) if reachable else hp_ref
        return typical * damage / 100.0

    folded: list[dict] = []
    for weapon, group in by_weapon.items():
        # Friendly-fire twins are the same warhead aimed at your own side at a fraction of the
        # damage. They are not extra reach and must not enter the sum.
        live = [r for r in group if "friendlyfire" not in r["node"].lower()] or group
        # A percentage warhead can only be priced where an HP census exists (the OpenRA sources).
        usable = [r for r in live
                  if float(r.get("damage") or 0) > 0 and (hp_ci or not r.get("percentage"))]
        pool = usable or live
        if len(pool) == 1:
            folded.append(pool[0])
            continue

        total = sum(damage_nominal(r) for r in pool)
        if total <= 0:
            folded.append(max(pool, key=damage_nominal))
            continue

        values: list[float | None] = []
        for i, armor in enumerate(armors):
            reach = [r for r in pool if reaches(r, i, armor)]
            if not reach:
                values.append(None)          # nothing this weapon carries can touch that class
                continue
            values.append(sum(coverage(r, armor) * damage_against(r, armor) * r["values_raw"][i]
                              for r in reach) / total)

        lead = max(pool, key=damage_nominal)
        folded.append({
            **lead,
            "name": f"{weapon}:folded",
            "node": "folded",
            "values_raw": values,
            "damage": total,
            # ⚠ `folded_from` IS LOAD-BEARING, not provenance decoration. The element a weapon
            # belongs to is read from `DamageTypes`, which is keyed by (weapon, NODE) — and the
            # folded row has no node of its own. Consumers must resolve the element over these
            # original nodes; the first version of this fold did not, so every folded weapon
            # came back `Plain` and the flamethrowers landed in the plain-Bullet group.
            "folded_from": [r["node"] for r in pool],
        })
    return folded


# ══════════════════════════════════════════════════════════════════════════════════════════════
# ⛔ AN AA ARMAMENT IS NOT A SEPARATE WEAPON — the split-armament artifact
# ══════════════════════════════════════════════════════════════════════════════════════════════
#
# Combined Arms gives a dual-purpose unit two armaments, one for ground and one for air. Cameo
# does not: the shipped dual-armament law is *"AA split = one weapon"*, with the air side earning
# a 1.5x range bonus and anti-air vehicles a +100% firepower bonus — a MODIFIER layer, not a
# second warhead. Counting CA's halves as separate weapons therefore invents a distinction our
# own rules say does not exist, and it invents it at scale:
#
#   MissileAA   43 weapons, of which 39 are the AA half of a dual-purpose unit  (3 dedicated)
#   Flak         9 weapons, of which  7 are the AA half of a dual-purpose unit  (2 dedicated)
#   Laser        6 AIR-only members, of which 5 are halves                      (1 dedicated)
#
# So MissileAA was the third-largest family in the map and almost all of it was a yaml convention.
# Folding the pair restores both truths at once: the dedicated-AA families shrink to the SAM sites
# and flak guns that really are AA-only, and every dual-purpose ground weapon stops reporting
# `n/a` in the Aircraft column for an aircraft it can plainly shoot down.
#
# ⚠ ONLY AN UNAMBIGUOUS PAIR IS FOLDED (maintainer's ruling, 2026-09-21). The Venom carries one
# ground laser and one air laser and the pairing is obvious; the IFV carries thirty ground weapons
# and four AA ones, and choosing a partner there would be a guess the data does not support. Those
# stay separate.
def fold_aa_armaments(rows: list[dict], armors: list[str], slots: list[dict]) -> list[dict]:
    """Merge each unambiguous ground+AA armament pair into the one weapon Cameo would ship."""
    macro = [ARMOR_MACRO.get(a.lower(), "GND") for a in armors]

    def reach(row: dict) -> set[str]:
        return {macro[i] for i, v in enumerate(row["values_raw"]) if v is not None}

    by_name = {r["weapon"]: r for r in rows if r.get("weapon")}
    by_actor: dict[str, set[str]] = collections.defaultdict(set)
    for slot in slots:
        by_actor[slot["actor"]].add(slot["weapon"])

    # air weapon -> the ground weapon it pairs with, agreed by EVERY actor that fires it
    def shape_key(row: dict) -> tuple:
        """A weapon's armour profile, rounded — its identity for pairing purposes."""
        return tuple(None if v is None else round(v, 3) for v in row["values_raw"])

    partner: dict[str, str | None] = {}
    for actor, weapons in by_actor.items():
        known = [(w, reach(by_name[w])) for w in weapons if w in by_name]
        ground = [w for w, m in known if m == {"GND"}]
        air = [w for w, m in known if m == {"AIR"}]
        # ⚠ COUNT DISTINCT PROFILES, NOT DISTINCT NAMES. OpenRA gives one logical weapon several
        # armament entries for mechanical reasons — firing ports, left/right mounts, garrison
        # slots. The Yak carries `ChainGun.Yak.L` and `ChainGun.Yak.R`, byte-identical profiles on
        # two wing mounts, and counting them as two ground weapons made the actor look ambiguous
        # and blocked the fold of its perfectly obvious `ChainGun.Yak.AA`.
        ground_shapes = {shape_key(by_name[w]) for w in ground}
        air_shapes = {shape_key(by_name[w]) for w in air}
        if len(ground_shapes) != 1 or len(air_shapes) != 1 or not ground or not air:
            continue
        lead_ground = min(ground)               # stable pick among identical twins
        for air_weapon in air:
            if partner.setdefault(air_weapon, lead_ground) != lead_ground:
                partner[air_weapon] = None      # two actors disagree; refuse to guess

    # ⚠ ONE GROUND WEAPON CAN ABSORB SEVERAL AIR VARIANTS. `HellfireAG` pairs with both
    # `HellfireAA` and `HellfireAA.Cryo`, and emitting one merged row per AIR weapon produced two
    # rows both claiming to be `HellfireAG` — a duplicate weapon key that every consumer keyed by
    # weapon name would silently collapse. Group by the GROUND weapon and merge once.
    adopted: dict[str, list[str]] = collections.defaultdict(list)
    for air_weapon, ground_weapon in partner.items():
        if ground_weapon is not None:
            adopted[ground_weapon].append(air_weapon)

    merged: list[dict] = []
    absorbed: set[str] = set()
    for ground_weapon, air_weapons in adopted.items():
        ground = by_name[ground_weapon]
        air_rows = [by_name[w] for w in sorted(air_weapons)]
        air = max(air_rows, key=lambda r: float(r["uses"]))
        values = [g if g is not None else a
                  for g, a in zip(ground["values_raw"], air["values_raw"])]

        # ⭐ MAGNITUDE IS A USAGE-WEIGHTED MEAN OF THE TWO ARMAMENTS (maintainer's ruling).
        # It cannot be a sum: the two never fire at the same target, so adding them would
        # overstate the weapon against both. The row's SHAPE already carries how the air side
        # compares to the ground side, so this is a uniform rescale and no ratio moves.
        weights = [(gmean(ground["values_raw"]), float(ground["uses"]) or 1.0),
                   (gmean(air["values_raw"]), float(air["uses"]) or 1.0)]
        target = weighted_gmean([(v, w) for v, w in weights if v > 0 and math.isfinite(v)])
        natural = gmean(values)
        if target > 0 and natural > 0 and math.isfinite(target) and math.isfinite(natural):
            scale = target / natural
            values = [None if v is None else v * scale for v in values]

        merged.append({
            **ground,
            "name": f"{ground_weapon}+{'+'.join(sorted(air_weapons))}",
            "values_raw": values,
            # One weapon, so one vote — the actors that carry the pair, not both halves counted.
            "uses": max([ground["uses"]] + [r["uses"] for r in air_rows]),
            "aa_armament": sorted(air_weapons),
        })
        absorbed.update(air_weapons)
        absorbed.add(ground_weapon)

    return [r for r in rows if r.get("weapon") not in absorbed] + merged


def build_matrix(source: dict, sid: str = "") -> dict:
    """Collapse a source's warhead tables into one matrix, normalised to weighted gmean 100."""
    excluded = EXCLUDED_ARMORS.get(sid, set())
    if source["kind"] == "ini":
        armors = [a for a in source["armors"] if a not in excluded]
    else:
        # Every armor any ACTOR declares, plus any armor only a warhead table names (a row the
        # mod writes against nothing — DTA's `concrete` is exactly that, 4 warheads and 0 units).
        armors = [a for a in source["armor_census_all"] if a not in excluded]
        for profile in source["profiles"]:
            for armor in profile["table"]:
                if armor not in armors and armor not in excluded:
                    armors.append(armor)

    # ── pass 1: read every row RAW, and drop the ones that carry no damage opinion ────────────
    rows: list[dict] = []
    dropped: list[dict] = []
    for profile in source["profiles"]:
        table = profile["table"]
        if source["kind"] == "ini":
            values = [table[a] for a in armors]
        else:
            values = [float(table.get(a, source["unstated_default"])) for a in armors]

        # ⛔ N/A, not 100: blank out the macro classes this warhead cannot target at all.
        targets = profile.get("targets")
        if targets:
            values = [v if ARMOR_MACRO.get(a.lower(), "GND") in targets else None
                      for a, v in zip(armors, values)]

        if any(v is not None and v < 0 for v in values):
            dropped.append({**profile, "reason": "negative row (a heal, not a multiplier)"})
            continue
        if all(v is None or v == 0 for v in values):
            dropped.append({**profile, "reason": "no targetable armour with damage"})
            continue

        name = profile["node"] if source["kind"] == "ini" else (
            f"{profile['weapon']}:{profile['node']}")
        rows.append({
            "name": name,
            "weapon": profile["weapon"],
            "node": profile["node"],
            "warhead_type": profile.get("warhead_type", ""),
            "uses": profile["uses"],
            "values_raw": values,
            "damage": profile.get("damage", 0.0),
            "percentage": profile.get("percentage", False),
            "target_tokens": profile.get("target_tokens"),
            # The INI dialects carry their own delivery/element/band (they have no `Projectile:`
            # or `DamageTypes:` for `compress_warheads` to read) — see `ini_delivery`.
            "delivery": profile.get("delivery"),
            "element": profile.get("element"),
            "band": profile.get("band"),
            "stated": (sorted(table.keys()) if source["kind"] != "ini"
                       else sorted(profile.get("stated", {}).keys())),
        })

    # One row per WEAPON, its warheads summed — see `fold_by_weapon`. The INI dialects declare one
    # warhead per entry and one entry per weapon already, so there is nothing to fold there.
    if source["kind"] != "ini":
        rows = fold_by_weapon(rows, armors, source.get("armor_hp"),
                              source.get("armor_actors"))
        rows = fold_aa_armaments(rows, armors, source.get("slots") or [])

    # ── pass 2: the BAND, chosen from the whole matrix, once ──────────────────────────────────
    # Per row would let a row's own zeros set their own penalty. Weights are the usage votes, so
    # the window is centred on the mod as it is actually PLAYED, not on its unused weapon list.
    all_cells = [v for row in rows for v in row["values_raw"]]
    all_weights = [float(row["uses"]) for row in rows for _ in row["values_raw"]]
    # ⚠ THE WINDOW AND THE DENOMINATOR MUST USE THE SAME WEIGHTS, or the band does not close.
    # A source with no unit list (the transcribed D2K table) has every weight at zero: the window
    # centre then silently falls back to the UNWEIGHTED mean while the denominator was still
    # computed weighted, the two disagree, and the normalised matrix runs past the ceiling —
    # measured 230.5 against a supposed maximum of 200. Decide weighted-vs-unweighted ONCE, here.
    weighted = any(w > 0 for w in all_weights)
    if not weighted:
        all_weights = [1.0] * len(all_cells)
    ceiling = None
    if FLOOR_MODE == "window":
        centre = _window_centre(all_cells, all_weights)
        floor, ceiling = centre * WINDOW_LO, centre * WINDOW_HI
        for row in rows:
            row["values"] = clamp_to_window(row["values_raw"], centre)
    else:
        floor = floor_for(all_cells)
        for row in rows:
            row["values"] = [None if v is None else max(v, floor) for v in row["values_raw"]]

    # ── the normaliser: one weighted geometric mean over every CELL of the matrix ─────────────
    # Weight is the warhead's weapon-slot count, so a warhead on twenty units counts twenty
    # times and a warhead on none counts zero. Rows with zero uses stay IN the matrix (they are
    # part of what the mod ships) but do not move the denominator.
    cells: list[tuple[float, float]] = []
    for row in rows:
        w = float(row["uses"]) if weighted else 1.0
        for value in row["values"]:
            cells.append((value, w))
    denominator = weighted_gmean(cells)
    if not math.isfinite(denominator) or denominator <= 0:
        denominator = gmean([v for row in rows for v in row["values"]])

    scale = 100.0 / denominator
    for row in rows:
        row["scaled"] = [None if v is None else v * scale for v in row["values"]]
        row["row_gmean_raw"] = gmean(row["values"])
        row["factor"] = row["row_gmean_raw"] / denominator

    return {
        "armors": armors,
        "floor": floor,
        "ceiling": ceiling,
        "floor_mode": FLOOR_MODE,
        "rows": rows,
        "dropped": dropped,
        "denominator_raw": denominator,
        "usage_weighted": weighted,
        "armor_actors": source.get("armor_actors") or {},
        "armor_census": source["armor_census"],
        "armor_census_all": source["armor_census_all"],
        "slots": source["slots"],
        "weapon_warhead": source.get("weapon_warhead", {}),
        "total_slots": len(source["slots"]),
    }


def collect() -> dict:
    out: dict[str, dict] = {}
    for sid, label, root, mod_id in OPENRA_SOURCES:
        if not (root / "mods" / mod_id / "mod.yaml").exists():
            print(f"  MISSING {sid}: {root / 'mods' / mod_id}")
            continue
        out[sid] = {"label": label, **build_matrix(read_openra(root, mod_id), sid)}

    rules = DTA_INI / "Rules.ini"
    if rules.exists():
        # ⭐ ENHANCED IS CANONICAL (maintainer ruling, 2026-09-21). DTA ships two rulesets;
        # `Enhance.ini` layered on `Rules.ini` is the live one, and it is the only one that
        # actually uses DTA's `light` armor rung (14 buildable actors against 0 in Classic).
        # Classic is kept as a comparison sheet and must NOT feed the factors.
        enhance = DTA_INI / "Enhance.ini"
        out["dta_enhanced"] = {"label": "DTA Enhanced (CANONICAL)",
                               **build_matrix(read_dta(rules, enhance), "dta_enhanced")}
        out["dta_classic"] = {"label": "DTA Classic (comparison only)",
                              **build_matrix(read_dta(rules, None), "dta_classic")}
    else:
        print(f"  MISSING dta: {rules}")

    for sid, label, path, engine in INI_SOURCES:
        if not path.exists():
            print(f"  MISSING {sid}: {path}")
            continue
        out[sid] = {"label": label, **build_matrix(read_ini_verses(path, engine), sid)}

    out["d2k_mod"] = {"label": "Dune 2000 mod (transcribed)",
                      **build_matrix(read_d2k_mod(), "d2k_mod")}

    out["cameo"] = {"label": "Cameo templates", **build_matrix(read_cameo("template"), "cameo")}
    out["cameo_resolved"] = {"label": "Cameo resolved weapons",
                             **build_matrix(read_cameo("resolved"), "cameo_resolved")}
    return out


def summarise(data: dict) -> str:
    lines = ["| source | armors | warheads | dropped | weapon slots | weighted gmean | weighted? |",
             "|---|--:|--:|--:|--:|--:|---|"]
    for sid, entry in data.items():
        lines.append(
            f"| `{sid}` | {len(entry['armors'])} | {len(entry['rows'])} | "
            f"{len(entry['dropped'])} | {entry['total_slots']} | "
            f"{entry['denominator_raw']:.1f} | {'yes' if entry['usage_weighted'] else 'NO'} |")
    return "\n".join(lines)


def sanity_report(data: dict) -> tuple[str, int]:
    """The check that can actually FAIL — the one the gmean-100 invariant cannot.

    A matrix is normalised BY its own centre, so "geometric mean is 100, range is [10,200]" is
    true by construction and stays true when the centre is nonsense. The independent quantity is
    the source's own POSITIVE MEDIAN: if a mod's typical working value does not fit inside its own
    window, the window has collapsed and the matrix has lost its shape.
    """
    lines = ["| source | zero % | n/a % | positive median | centre | ceiling | verdict |",
             "|---|--:|--:|--:|--:|--:|---|"]
    failures = 0
    for sid, entry in data.items():
        raw = [v for row in entry["rows"] for v in row["values_raw"]]
        positive = sorted(v for v in raw if v is not None and v > 0)
        if not positive:
            continue
        median = positive[len(positive) // 2]
        centre = entry["denominator_raw"]
        ceiling = centre * WINDOW_HI
        ok = median < ceiling
        failures += 0 if ok else 1
        # Separate the two kinds of missing cell: an immune 0 and an un-targetable N/A.
        na = sum(1 for v in raw if v is None)
        zeros = (len(raw) - len(positive) - na) / len(raw) * 100
        lines.append(f"| `{sid}` | {zeros:.1f}% | {na / len(raw) * 100:.1f}% | {median:.0f} | "
                     f"{centre:.2f} | {ceiling:.2f} | "
                     f"{'ok' if ok else '**DEGENERATE**'} |")
    lines.append("")
    lines.append(f"**{failures} degenerate source(s)** — a source is degenerate when its own "
                 f"typical working value does not fit inside its own window.")
    return "\n".join(lines), failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="independent sanity check; exits 1 if any matrix has collapsed")
    ap.add_argument("--write", action="store_true", help="write the JSON sidecar")
    ap.add_argument("--summary", action="store_true", help="print coverage only")
    ap.add_argument("--floor", choices=("absolute", "relative", "window"), default=None,
                    help="zero-floor mode; 'relative' = 1%% of each mod's own positive "
                         "median, which removes DTA's x10-scale penalty")
    args = ap.parse_args()
    if args.floor:
        global FLOOR_MODE
        FLOOR_MODE = args.floor

    data = collect()

    if args.check:
        report, failures = sanity_report(data)
        print(report)
        return 1 if failures else 0

    print(summarise(data))

    if args.write:
        OUT_JSON.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n",
                            encoding="utf-8")
        print(f"\nwrote {OUT_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
