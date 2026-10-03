#!/usr/bin/env python3
"""W13 step 2 — aggregate ONE weapon concept across every reference mod.

The maintainer's method (2026-08-15): *"research all the obelisk of light lasers
from all the mods and then see how that big laser versus values behaves against
all armor types … then try to extrapolate the values to all the cameo armor
types."* One concept at a time, two tables each:

  **Table A** — what each mod actually ships, in its OWN armor vocabulary.
  **Table B** — the same profiles mapped onto Cameo's 16 armor types.

    python tools/reference/aggregate_archetype.py obelisk
    python tools/reference/aggregate_archetype.py --list
    python tools/reference/aggregate_archetype.py --all --write

**How a warhead is identified matters more than the arithmetic.** For the INI
mods this TRACES the real chain — `[OBELISK] Primary=` -> `[weapon] Warhead=` ->
`[warhead] Verses=` — so what lands in the table is the weapon that building
actually fires, not a warhead whose name happened to contain "laser". A name
match would silently average an Obelisk with an infantry laser rifle, which is
precisely the flattening W13 exists to undo. OpenRA sources have no such flat
index here, so they use a curated warhead list, and every row says which method
produced it.

⚠ **Table B is EXTRAPOLATION, not measurement**, and it is labelled as such per
cell. Five of Cameo's 16 armors have no source equivalent — Heroic, Scout,
Superheavy and the four aircraft classes — because the Westwood engines carry
11 armors and share ONE of them between aircraft and ground vehicles.
Maintainer ruling 2026-08-15: *"some mods use light or heavy armor for aircraft
and you can translate that to our fighter, bomber, helicopter, spaceship"*, so
the air classes are read off the vehicle ladder by weight. The ladder ends
(Heroic / Scout / Superheavy) continue the ladder's own local slope.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import statistics
import sys
import warnings

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference"))
import extract_versus as ev  # noqa: E402

OUT = ROOT / "docs" / "reference" / "archetype_tables.md"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --------------------------------------------------------------------------- #
# Cameo's 16 armor types, in the ladder order gen_weapon_template.py uses.
# --------------------------------------------------------------------------- #
# ⚠ **HEROIC IS NOT THE TOP INFANTRY RUNG** (maintainer ruling, 2026-08-15).
# Putting it at the heavy end of the infantry ladder backfires: heroes would take
# the MOST damage from anti-armour weapons, which is the opposite of what an elite
# unit should feel like. Heroic is instead the BRIDGE between infantry Plate and
# vehicle Scout, and it is excluded from the INF ladder's ordering for that reason.
# `HEROIC_FROM` below says how its value is derived.
CAMEO_LADDERS = {
    "INF": ["None", "Flak", "Plate"],
    "VEH": ["Scout", "Light", "Medium", "Heavy", "Superheavy"],
    "BLD": ["Wood", "Steel", "Concrete"],
    "AIR": ["Fighter", "Bomber", "Helicopter", "Spaceship"],
}
# Display order: Heroic sits between the ladders it bridges.
CAMEO16 = (CAMEO_LADDERS["INF"] + ["Heroic"] + CAMEO_LADDERS["VEH"]
           + CAMEO_LADDERS["BLD"] + CAMEO_LADDERS["AIR"] + ["Airborne"])

# Source armor -> Cameo armor, where a real equivalent exists.
DIRECT = {
    "none": "None", "flak": "Flak", "plate": "Plate",
    "light": "Light", "medium": "Medium", "heavy": "Heavy",
    "wood": "Wood", "steel": "Steel", "concrete": "Concrete",
    # ⚠ `drone` is NOT mapped, and the reason is worth keeping.
    #
    # It looks like Cameo's Scout — RA2's light robotic armor — and an earlier
    # version mapped it that way. But RA2's `drone` exists to tune ONE unit, the
    # Terror Drone, so mods routinely put a huge anti-drone bonus there: the Tesla
    # Coil's `Electric` warhead reads `drone 200` against ~100 for everything else.
    # Imported as Scout, that 200 is not a statement about scout vehicles at all,
    # and it does not even stay put: the ordering pass sorts the values and
    # reassigns them, so the 200 landed on **Superheavy** and produced a Tesla
    # ladder of `Scout 63 · Light 67 · Medium 71 · Heavy 75 · Superheavy 200`.
    #
    # Scout is therefore extrapolated from the vehicle ladder like the other rungs
    # the corpus has no equivalent for, which is what makes the ladder end smoothly
    # (`Heavy 75 -> Superheavy ~79`) instead of jumping.
}
# Aircraft read off the VEHICLE ladder by weight, RUNG FOR RUNG (maintainer,
# 2026-08-15 — correcting an earlier draft that had Fighter and Helicopter both
# on Light and Spaceship on Heavy, which collapsed two air classes onto one
# vehicle rung and left Superheavy unused):
#   Fighter <- Light · Bomber <- Medium · Helicopter <- Heavy · Spaceship <- Superheavy
# The four air classes are a ladder of their own and map one-to-one onto the top
# four vehicle rungs.
AIR_FROM = {"Fighter": "Light", "Bomber": "Medium",
            "Helicopter": "Heavy", "Spaceship": "Superheavy"}

# ⚠ THE NORMALISATION LAW (maintainer, 2026-08-15):
#   *"everything needs to be normalized to 100% for the maximum versus value for
#    each game and each warhead from each game"*
#
# Every profile is rescaled so its OWN maximum is 100. This is per-WARHEAD, not
# per-source, and it is what makes cross-mod comparison mean anything:
#
#   * it removes engine scale differences outright — DTA runs on the Tiberian Sun
#     engine whose multipliers are x10 (measured median Versus 690 against 55-100
#     elsewhere), and a hand-maintained per-source divisor only ever fixed the
#     cases somebody had already noticed;
#   * it removes each mod's POWER LEVEL, which is not what we are borrowing. We
#     want the SHAPE — "twice as good against infantry as against tanks" — and a
#     mod that writes 200/100 and one that writes 100/50 are the same design;
#   * it makes the aggregate meaningful: averaging raw values weights whichever
#     mod happens to use the biggest numbers.
#
# What it deliberately discards is absolute lethality. That belongs to Damage and
# the level slope, not to the armor profile.
#
# ⚠ **REVISED 2026-08-15 — normalise to the MEDIAN, not the peak, and allow values
# above 100.** Anchoring on the peak looked safe and was not: RA2's Tesla warhead
# `Electric` reads `none 100 · plate 100 · medium 100 · heavy 100 · light 85 ·
# buildings 50 · DRONE 200`. The 200 is a niche anti-terror-drone bonus, but it is
# the row's maximum, so peak-normalisation halved every real armor and reported
# Tesla as 50-vs-infantry — a weapon famous for vaporising infantry. Mental Omega's
# `ElectricCoil` (drone 200 again) came out the same way, and the error survived
# into the family proposals as Tesla peaking on Superheavy with 30s everywhere else.
#
# One outlier must not be allowed to set the scale for fifteen other armors. The
# median is robust to exactly that: it says "100 is this weapon's TYPICAL
# effectiveness", and a genuine speciality is free to sit above it.
#
# Maintainer, 2026-08-15: *"should we be able to use maximum values above 100%? The
# old 100% upper limit was only because in the past we didn't have the versus values
# built into the weapon damage balance calculation, right?"* — exactly right. The K
# coefficient now measures the profile and prices it (W1), so a 200 is PAID FOR
# rather than free, and the cap was only ever protecting a formula that could not
# see it. The corpus itself runs to 320.
NORMALISE_REFERENCE = 100.0
# --------------------------------------------------------------------------- #
# THE VERSUS WINDOW (maintainer, 2026-08-15) — binding
# --------------------------------------------------------------------------- #
# *"the maximum versus value is 200 and the minimum versus value is 10 so the
#  normalized spread is 100-5 which is 20x"* — adopted.
#
# The ratio is the point, and it is unchanged: the old shape law's most extreme
# spread was peak 100 against floor 5, i.e. **20:1**, and `200 / 10` is the same
# 20:1 written on the median-100 scale that replaced the peak-100 one. So the
# window does not make weapons more specialised than the law already allowed; it
# fixes the SCALE the law is expressed on, which the move to median normalisation
# had left open-ended.
#
# ⚠ **20:1 is a legal maximum, never a target.** Measured across the corpus, the
# reference mods' own family profiles span only **1.3x to 7.2x** (`Laser/Heavy`
# 1.3, `MissileAP/Light` 7.2). Everything beyond that in a shipped profile comes
# from `shape_profile` stretching the measured shape onto the level's floor — a
# deliberate design step, not something the field said. Treating 20:1 as the goal
# would invent counter-play the reference does not support.
NORMALISE_CEILING = 200.0
# Nothing in a shipped profile may fall below this, including the DERIVED armors,
# which are products and so can land arbitrarily low on their own.
ABSOLUTE_FLOOR = 10.0

# Geometric mean cannot see a zero (any zero makes the whole product zero), and a
# hard 0 in a source means "immune". Clamping to 1 keeps the data point at
# "essentially immune" instead of deleting the row from the statistic.
GMEAN_FLOOR = 1.0

# Minimum separation between any two values in a profile. Maintainer, 2026-08-15:
# *"maybe make it steps of 2 instead of 1 for those? Minimum step of 2?"* — yes. A
# 1-point gap satisfies the no-ties rule on paper while being invisible in play;
# 2 is the smallest step a player could ever notice, so it is the smallest step
# worth spending a rung on.
MIN_GAP = 2.0

# --------------------------------------------------------------------------- #
# THE HEROIC RULE (maintainer, 2026-08-15)
# --------------------------------------------------------------------------- #
# *"I was thinking of making Heroic an in-between of infantry Plate and vehicle
#  Scout … when the versus values were still multiplied, combining plate and
#  scout would be almost perfect, because it combines both infantry and vehicle
#  and at the same time light and heavy — so most weapons which are only good
#  against one of them would deal low damage to our heroes, and only those good
#  against BOTH are good against heroes as well."*
#
# That property comes from MULTIPLYING, and averaging destroys it:
#
#     anti-infantry weapon   Plate 100 · Scout 30  ->  avg 65   product 30
#     anti-vehicle weapon    Plate  20 · Scout 90  ->  avg 55   product 18
#     good against both      Plate  80 · Scout 80  ->  avg 80   product 64
#
# The average says the two specialists are nearly as good against a hero as the
# generalist. The product says exactly what the maintainer wants: specialists
# fall off a cliff, only the generalist stays high.
#
# So Heroic's VALUE is the product of the weapon's Plate and Scout values
# (as fractions, re-expressed as a percentage) — the old two-armor multiplication
# collapsed into one armor type.
#
# ⚠ **This does NOT reintroduce the W20 squaring bug.** W20 was two `Armor`
# TRAITS multiplying at runtime on one actor, which nobody designed. This is a
# single armor type whose numbers are computed once, at generation time, from a
# formula the designer chose. One armor trait is still enabled per hit.
#
# ⚠ **THE PATTERN GENERALISES, and it is the real fix for the dual-armor stacks.**
# `^FlyingInfantryTemplate` carries TWO `Armor` traits today — `Scout` and
# `Fighter` — for exactly the same reason Heroic wanted two: a jetpack trooper is
# both infantry and aircraft, and multiplying the two made only a weapon good at
# BOTH dangerous to it. Averaging (W20) silently removed that. A DERIVED armor
# type restores the behaviour with one trait, so W20's "two traits must never
# multiply" and this design stop being in conflict.
#
# Maintainer 2026-08-15: *"we need a new armor type for the flying infantry which
# is between helicopter and scout armor multiplied (same as heroic is plate x
# scout)"*. Name `Airborne` is provisional — maintainer to confirm.
DERIVED_ARMORS = {
    "Heroic": ("Plate", "Scout"),
    "Airborne": ("Helicopter", "Scout"),
}
HEROIC_FROM = DERIVED_ARMORS["Heroic"]        # kept: referenced by DESIGN.md §12.0b

# --------------------------------------------------------------------------- #
# THE SPREAD RULE (maintainer, 2026-08-15)
# --------------------------------------------------------------------------- #
# *"I still want a ladder (no two values should be identical) but it no longer
#  needs to be perfectly linear. And 100-5 should be the most hardcore spread
#  ever … 5% should be more like the exception than the rule. For less
#  specialized warheads you should be between 10 and 25 for the lowest value."*
#
#   * top of every profile is 100 (the normalisation law);
#   * NO TWO VALUES IDENTICAL anywhere in the profile — plateaus are what make a
#     weapon unreadable, and a tie is a wasted rung;
#   * steps need NOT be equal. Even ramps are exactly the "moderate middle" W13
#     exists to avoid; uneven steps are how a weapon says where it really bites;
#   * floor 10-25 for a normal weapon; **5 only for a deliberately hyper-
#     specialised one**, and it is meant to stay rare.
FLOOR_BAND = (10, 25)
EXTREME_FLOOR = 5

# --------------------------------------------------------------------------- #
# The concepts. `ini` entries are ACTOR names traced through the rules; `openra`
# entries are warhead names, because those trees have no flat actor index here.
# --------------------------------------------------------------------------- #
ARCHETYPES = {
    # Actor ids below are VERIFIED present in the rules, not guessed: `OBLI` (DTA),
    # `TSOBEL`/`TSLASR`/`ROBOTOBELISK` (CnC Reloaded's TS content), and — the one that
    # would defeat any name search — the RA2 **Prism Tower is `[ATESLA]`**, "Allied
    # Tesla". Tracing the actor is what finds it; grepping for "prism" finds the
    # Mayan temple prop instead.
    "obelisk": {
        "what": "Obelisk of Light — the big defensive laser",
        "ini_actors": ["OBLI", "TSOBEL", "TSLASR", "ROBOTOBELISK", "NAOBEL"],
        "openra_warheads": ["Laser", "LaserTur", "IonBeamMini"],
        "cameo_family": "^Warhead_Laser_Heavy",
        "direction": "light",
    },
    "tesla_coil": {
        "what": "Tesla Coil — the big defensive electric weapon",
        "ini_actors": ["TESLA", "NATCOIL", "RATSLA"],
        "openra_warheads": ["TeslaZap", "PortaTesla", "CoilBolt", "PostBolt",
                            "^TeslaWeapon"],
        "cameo_family": "^Warhead_Tesla_Heavy",
        "direction": "heavy",
    },
    "prism_tower": {
        "what": "Prism Tower — the RA2-lineage counterpart of the Obelisk",
        "ini_actors": ["ATESLA"],
        "openra_warheads": ["PrismShot", "PrismWarhead"],
        "cameo_family": "^Warhead_Prism_Heavy",
        "direction": "light",
    },
    "he": {
        "what": "Generic HE — the canonical anti-light/anti-infantry profile",
        "ini_warheads": ["HE"],
        "openra_warheads": ["^Cannon", "ArtilleryShell"],
        "cameo_family": "^Warhead_CannonHE_Medium",
        "direction": "light",
    },
    "ap": {
        "what": "Generic AP — the canonical anti-heavy/armour-piercing profile",
        "ini_warheads": ["AP"],
        "openra_warheads": ["^ArmorPierceDamage", "sabot"],
        "cameo_family": "^Warhead_CannonAP_Medium",
        "direction": "heavy",
        # The one concept that earns the 5 floor: AP is the deliberate extreme,
        # near-useless against unarmoured infantry. Everything else sits 10-25.
        "specialised": True,
    },
    # Names below are verified present in the corpus, not guessed.
    "flame": {
        "what": "Flame — anti-infantry/anti-building, poor against armour",
        "ini_warheads": ["Fire", "Fire2", "SAFlame", "SSABFlame", "NapalmWH",
                         "Napalm1", "Napalm2", "FlamethWH1", "FlamethWH2"],
        "openra_warheads": ["^FlameWeapon", "^FireWeapon", "Napalm", "BigFlamer",
                            "Flamer", "TankNapalm", "FireballLauncher"],
        "cameo_family": "^Warhead_Flame_Medium",
        "direction": "light",
    },
    # ⚠ MEASURED LIMITATION, not a gap in the search: the RA2 lineage does NOT
    # separate missile-AP from cannon-AP — a Rhino shell and a tank-killer rocket
    # both carry the single `AP` warhead. Only the OpenRA sources ship distinct
    # missile families (`^AntiGroundMissile`, `^AntiAirMissile`, `Dragon`), so
    # these two concepts rest on fewer sources than the cannon pair and their `n`
    # column will say so. Cameo's split into MissileHE/MissileAP is an ADDITION to
    # the field, which means the corpus can inform the shape but cannot settle it.
    "missile_he": {
        "what": "Missile HE — the air-capable counterpart of the HE cannon",
        "ini_warheads": ["TripleRocketHE", "TSMultiMissileHE", "MultiMissileWH"],
        "openra_warheads": ["^AntiGroundMissile", "^MissileWeapon", "^Missile",
                            "^Rocket", "Rockets", "BikeRockets", "^DefaultMissile"],
        "cameo_family": "^Warhead_MissileHE_Medium",
        "direction": "light",
    },
    "missile_ap": {
        "what": "Missile AP — anti-tank missile (shares `AP` in the RA2 lineage)",
        "ini_warheads": ["AP"],
        "openra_warheads": ["Dragon", "120mmHEAT", "sabot", "StnkMissile"],
        "cameo_family": "^Warhead_MissileAP_Medium",
        "direction": "heavy",
    },
}

# ⚠ SOME INI SOURCES ARE DELTAS, NOT COMPLETE RULESETS.
# DTA ships one full ruleset (`Rules.ini`, 2321 sections) plus patch files that
# override PARTS of it: `Enhance.ini` is 471 sections and its `[OBLI]` carries 10
# keys with **no `Primary=` at all**, because it only restates what Enhanced
# changes. Tracing such a file alone finds nothing and the source silently
# vanishes from the comparison — which is exactly what happened to `dta_enhanced`
# until the maintainer noticed it missing. Reading the patch OVER its base makes
# the actor resolvable while the patch still wins wherever it speaks.
INI_BASE = {
    "dta_enhanced": "dta_classic",
    "dta_globalcode": "dta_classic",
}

INI_SECTION = re.compile(r"^\s*\[([^\]]+)\]")
INI_KEY = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_.]*)\s*=\s*(.+?)\s*(?:;.*)?$")


def read_ini(path: pathlib.Path) -> dict[str, dict[str, str]]:
    """Flat {section: {key: value}}; comment lines dropped like extract_versus."""
    out: dict[str, dict[str, str]] = {}
    section = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lstrip().startswith(";"):
            continue
        head = INI_SECTION.match(line)
        if head:
            section = head.group(1)
            out.setdefault(section, {})
            continue
        kv = INI_KEY.match(line)
        if kv and section is not None:
            out[section][kv.group(1).lower()] = kv.group(2)
    return out


def source_path(sid: str, sources: dict) -> pathlib.Path:
    """Use the corpus provenance path; legacy configuration only if unspecified."""
    recorded = sources.get(sid, {}).get("path")
    if recorded:
        return pathlib.Path(recorded)
    return next(p for s, _l, _k, p, _e in ev.SOURCES if s == sid)


def source_base_path(sid: str, sources: dict) -> pathlib.Path | None:
    recorded = sources.get(sid, {}).get("base_path")
    if recorded:
        return pathlib.Path(recorded)
    base_id = INI_BASE.get(sid)
    return source_path(base_id, sources) if base_id else None


def read_ini_resolved(sid: str, path: pathlib.Path,
                      sources: dict | None = None) -> dict[str, dict[str, str]]:
    """`read_ini`, but a DELTA source is laid over its base (see `INI_BASE`).

    Section-by-section overlay: the patch's keys win, the base supplies the rest,
    so `[OBLI]` keeps the `Primary=` it never restated while any stat Enhanced
    did change still comes from Enhanced.
    """
    base_id = INI_BASE.get(sid)
    if base_id is None:
        return read_ini(path)
    base_path = source_base_path(sid, sources or {})
    if base_path is None or not base_path.exists():
        raise FileNotFoundError(f"{sid}: required overlay base unavailable: {base_path}")
    merged = {s: dict(kv) for s, kv in read_ini(base_path).items()}
    for section, kv in read_ini(path).items():
        merged.setdefault(section, {}).update(kv)
    return merged


def trace_ini(ini: dict, actor: str) -> list[tuple[str, str]]:
    """[(weapon, warhead)] the actor actually fires — Primary and Secondary."""
    node = ini.get(actor)
    if node is None:
        return []
    found = []
    for slot in ("primary", "secondary", "elitesecondary", "eliteprimary"):
        weapon = node.get(slot)
        if not weapon:
            continue
        wnode = ini.get(weapon.strip())
        if not wnode:
            continue
        warhead = (wnode.get("warhead") or "").strip()
        if warhead:
            found.append((weapon.strip(), warhead))
    return found


def collect(concept: str) -> list[dict]:
    """One row per (source, warhead) that this concept resolves to."""
    spec = ARCHETYPES[concept]
    corpus = json.loads((ROOT / "docs/reference/versus_raw.json")
                        .read_text(encoding="utf-8"))
    from warhead_source_selection import selected_sources
    corpus["sources"] = selected_sources(corpus["sources"])
    rows = []
    for sid, lineage, kind, path, engine in ev.SOURCES:
        entry = corpus["sources"].get(sid)
        if not entry:
            continue
        path = source_path(sid, corpus["sources"])
        by_name = {str(r["warhead"]): r for r in entry["rows"] if "versus" in r}

        wanted: list[tuple[str, str]] = []          # (warhead, how)
        if kind == "ini":
            try:
                ini = read_ini_resolved(sid, path, corpus["sources"])
            except FileNotFoundError as exc:
                warnings.warn(f"{sid}: actor tracing unavailable: {exc}")
                ini = {}
            for actor in spec.get("ini_actors", []):
                for weapon, warhead in trace_ini(ini, actor):
                    wanted.append((warhead, f"traced [{actor}]->{weapon}"))
            for name in spec.get("ini_warheads", []):
                if name in by_name:
                    wanted.append((name, "named warhead"))
        else:
            for name in spec.get("openra_warheads", []):
                if name in by_name:
                    wanted.append((name, "curated name"))

        seen = set()
        for warhead, how in wanted:
            if warhead in seen or warhead not in by_name:
                continue
            seen.add(warhead)
            raw = {k: float(v) for k, v in by_name[warhead]["versus"].items()}
            rows.append({"source": sid, "lineage": lineage, "warhead": warhead,
                         "how": how, "raw": raw, "versus": normalise(raw)})
    return rows


def normalise(versus: dict[str, float]) -> dict[str, float]:
    """Rescale a profile so its MEDIAN is 100 (see the law above).

    Median over the POSITIVE entries only: a hard 0 means "immune", which is a
    statement about one armor, not evidence about the weapon's general level, and
    letting zeros drag the centre down would inflate everything else.
    """
    live = [v for v in versus.values() if v > 0]
    if not live:
        return dict(versus)
    centre = statistics.median(live)
    if centre <= 0:
        return dict(versus)
    factor = NORMALISE_REFERENCE / centre
    return {k: min(NORMALISE_CEILING, v * factor) for k, v in versus.items()}


# --------------------------------------------------------------------------- #
# Extrapolation to Cameo's 16
# --------------------------------------------------------------------------- #
def _extend(known: list[float], beyond_top: bool) -> float | None:
    """Continue a ladder by its own last step. Clamped at 0 — a negative
    multiplier is meaningless, and W13 rule 8 forbids a hard zero anyway.

    ⚠ **Needs TWO known values.** An earlier version returned the lone value
    unchanged when only one rung was defined, which quietly manufactured data:
    a source defining only `none` produced a `Heroic` equal to it, and a source
    defining only `heavy` produced a `Scout` equal to it. Those invented cells
    then entered the medians — Tesla's `Heroic` came out at 100 against a real
    infantry ladder of 100/55/50, i.e. the extrapolation contradicted the very
    rows it was built from. One rung is not a slope; return None and let the
    column report a smaller n.
    """
    vals = [v for v in known if v is not None]
    if len(vals) < 2:
        return None
    step = vals[-1] - vals[-2] if beyond_top else vals[0] - vals[1]
    base = vals[-1] if beyond_top else vals[0]
    return max(0.0, base + step)


def to_cameo(versus: dict) -> tuple[dict[str, float], dict[str, str]]:
    """(values per Cameo armor, provenance per Cameo armor)."""
    src = {k.lower(): float(v) for k, v in versus.items()}
    out: dict[str, float] = {}
    how: dict[str, str] = {}

    for skey, ckey in DIRECT.items():
        if skey in src:
            out[ckey] = src[skey]
            how[ckey] = "direct"

    # Ladder ends: continue the ladder's own slope.
    inf = [out.get(a) for a in ("None", "Flak", "Plate")]
    if any(v is not None for v in inf):
        v = _extend([x for x in inf if x is not None], beyond_top=True)
        if v is not None and "Heroic" not in out:
            out["Heroic"], how["Heroic"] = v, "extrapolated"

    veh_up = [out.get(a) for a in ("Light", "Medium", "Heavy")]
    if any(v is not None for v in veh_up):
        v = _extend([x for x in veh_up if x is not None], beyond_top=True)
        if v is not None and "Superheavy" not in out:
            out["Superheavy"], how["Superheavy"] = v, "extrapolated"
    if "Scout" not in out and any(v is not None for v in veh_up):
        v = _extend([x for x in veh_up if x is not None], beyond_top=False)
        if v is not None:
            out["Scout"], how["Scout"] = v, "extrapolated"

    for air, from_armor in AIR_FROM.items():
        if from_armor in out:
            out[air] = out[from_armor]
            how[air] = f"from {from_armor}"
    return out, how


def flag_scale_outliers(rows: list[dict]) -> None:
    """Mark rows that look like a different scale from their peers.

    `SOURCE_SCALE` fixes the two whole-source cases (DTA). What is left is
    per-ROW: a handful of OpenRA `^template` blocks carry values ten times their
    neighbours'. They are NOT dropped — a row discarded on suspicion is data
    lost silently, which is worse than a row shown with a warning — and the
    median is robust enough to survive a few. But they must be visible, because
    a reader comparing "1000" to "100" down a column will otherwise conclude the
    weapon is ten times stronger in that mod.
    """
    maxima = [max(r["versus"].values()) for r in rows if r["versus"]]
    if len(maxima) < 4:
        return
    typical = statistics.median(maxima)
    for r in rows:
        if r["versus"] and max(r["versus"].values()) > 4 * typical:
            r["how"] += " ⚠scale?"


# A profile needs at least this many DEFINED armors to enter an aggregate.
#
# ⚠ This filter fixes a wrong conclusion I drew and reported. A row defining a
# single armor (the OpenRA `^TeslaWeapon` template rows define only `none`)
# normalises to `none = 100` by definition — its one value IS its own maximum.
# Five such rows stacked the `None` column at 100 and made the Tesla median look
# anti-infantry, which I read as "Cameo's anti-heavy Tesla is inverted against
# the field". Per-mod inspection showed the opposite: 6 of the 9 mods that state
# a direction have Tesla RISING toward heavy armour, exactly like Cameo.
# One armor is not a profile, and normalisation turns it into a fake 100.
MIN_ARITY_FOR_AGGREGATE = 3


def buckets_of(rows: list[dict]) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {a: [] for a in CAMEO16}
    for r in rows:
        if len(r["versus"]) < MIN_ARITY_FOR_AGGREGATE:
            continue
        vals, _ = to_cameo(r["versus"])
        for armor, value in vals.items():
            out[armor].append(value)
    return {a: v for a, v in out.items() if v}


def aggregate(rows: list[dict], how: str) -> dict[str, float]:
    """One profile from many, three ways.

    * `median` — W13 rule 4's choice. Robust: one mod with an extreme profile
      cannot move it, so it answers "what does a typical mod ship?".
    * `mean` — the arithmetic average. Every source pulls proportionally to how
      far out it sits, so a single outlier drags the whole cell.
    * `gmean` — the geometric mean. The natural average for MULTIPLIERS, which
      is exactly what a Versus value is: averaging x2 and x0.5 arithmetically
      gives 1.25 (a net buff out of nowhere) where the geometric mean gives 1.0.
      It also sits below the arithmetic mean whenever the spread is wide, so the
      gap between the two columns is itself a readout of disagreement.
    """
    picked: dict[str, float] = {}
    for armor, values in buckets_of(rows).items():
        if how == "median":
            picked[armor] = statistics.median(values)
        elif how == "mean":
            picked[armor] = statistics.fmean(values)
        elif how == "gmean":
            picked[armor] = statistics.geometric_mean(
                [max(GMEAN_FLOOR, v) for v in values])
        else:
            raise ValueError(how)
    return {a: round(v, 1) for a, v in picked.items()}


# Keys that are not armor types — Cameo carries a few pseudo-armors on the same
# node (the shield layer, HAZMAT gating, Tesla's REFLECTOR). They must not enter
# a profile comparison or they distort the normalisation peak.
NON_ARMOR = {"shield", "hazmat", "reflector"}


def lawful_profile(profile: dict[str, float], direction: str) -> dict[str, float]:
    """Re-lay a measured profile so it obeys Cameo's ORDERING LAW.

    **Why this step has to exist.** The corpus and the law disagree, and both are
    right about different things. Measured across six independent RA2-lineage
    mods, the canonical `AP` warhead reads `none 25 · flak 25 · plate 15` — armour
    piercing doing LESS to plated infantry than to unplated. That is not noise,
    it is Westwood's design, reproduced by everyone who cloned it. But Cameo's
    ordering law (maintainer 2026-08-01, "the most important part") says an
    anti-HEAVY weapon must run `Heroic > Plate > Flak > None`, and the law wins:
    it is what makes a Cameo weapon *readable*, so a player can predict a
    matchup from the weapon's type instead of memorising 16 numbers each.

    So the corpus supplies the MAGNITUDES — how wide the spread is, where the
    plateaus and cliffs fall — and the law supplies the ORDER. That is W13 rule 6
    ("the ordering law still governs; it is what keeps wild coherent rather than
    random") made executable.

    Method: inside each macro ladder, keep the measured VALUES exactly, then
    reassign them along the ladder in the direction the law requires. Nothing is
    invented and nothing is averaged away — only the pairing changes. The macro
    blocks keep the priority the field gave them (their own mean), because THAT
    is a genuine measurement of what the weapon is for.
    """
    out: dict[str, float] = {}
    for ladder in CAMEO_LADDERS.values():
        present = [a for a in ladder if a in profile]
        if not present:
            continue
        values = sorted((profile[a] for a in present), reverse=True)
        # `heavy` = best against the heaviest rung, so the biggest value goes to
        # the END of the (lightest -> heaviest) ladder.
        targets = list(reversed(present)) if direction == "heavy" else present
        for armor, value in zip(targets, values):
            out[armor] = value
    return out


def derive_armors(profile: dict[str, float]) -> dict[str, float]:
    """Every DERIVED armor: the PRODUCT of its two parents (see the rule above).

    Both inputs are read as fractions OF THE PROFILE'S OWN PEAK, so the product is
    `A/top * B/top` re-expressed on the same scale, i.e. `A * B / top`. A weapon
    strong against exactly one parent collapses; only one strong against BOTH
    stays high — which is the entire point of a hybrid armor class.

    ⚠ **The divisor is the profile's peak, NOT the constant 100**, and the two
    stopped being the same thing when normalisation moved from peak to median
    (values above 100 became legal). Dividing by 100 while a parent sits at 137
    AMPLIFIES instead of collapsing: `Bullet_Light` produced `Plate 137 · Scout
    106 · Heroic 145`, i.e. heroes softer than either half — the exact inversion
    §12.0b exists to prevent, and it hit **36 of 60** derived cells. Against the
    peak the product can never exceed either parent, and whenever a profile does
    peak at 100 this reduces to the documented `A * B / 100` unchanged.
    """
    # ⚠ A derived armor may legitimately fall BELOW the field band's floor, and it
    # is the one exception to "automatic output stays inside the field interval".
    # The band is measured on source profiles that contain no derived armor at all,
    # so there is no field opinion to respect here — and clamping the product into
    # the band would break the §12.0b rule that produces it. A hybrid resisting
    # specialists harder than either parent IS the mechanic. The `[10, 200]` window
    # still binds; only the spread band is waived, and only for these cells.
    out = {}
    top = max((v for k, v in profile.items() if k not in DERIVED_ARMORS), default=100.0)
    top = max(top, 1.0)
    for name, (first, second) in DERIVED_ARMORS.items():
        a, b = profile.get(first), profile.get(second)
        if a is not None and b is not None:
            out[name] = round(a * b / top, 1)
    return out


# --------------------------------------------------------------------------- #
# THE TARGET SPREAD — measured, never invented (maintainer, 2026-08-15)
# --------------------------------------------------------------------------- #
# *"maximum legal spread != target spread … if you do something automatically it
#  should stay in the reference field's interval … only if something is
#  specifically designed otherwise should it be allowed."*
#
# So the window `[10, 200]` (20:1) says what MAY ship; this says what ships by
# DEFAULT. The two must never be confused — 20:1 as a target would invent
# counter-play no source mod expresses.
#
# Measured over **2402 individual reference warheads** carrying a real damage
# profile (>=3 armors, peak >5, so the death-animation and dummy plumbing that
# once faked a "20% of the field is flat" finding is excluded):
#
#     p10 1.0x · p25 1.9x · MEDIAN 4.0x · p75 7.5x · p90 15x · max 300x
#     26% exceed 7.2x · 6% exceed 20x
#
# ⚠ These are INDIVIDUAL warheads, and that distinction is the whole point. The
# per-family AGGREGATE spans only 1.3x-7.2x, because averaging across mods that
# disagree about a family's direction CANCELS the disagreement and flattens the
# result. Reading the aggregate as "the field's interval" would target a
# sharpness no real warhead has — the aggregate is an artifact of averaging, not
# a design any mod shipped. The interquartile range of the real warheads is the
# honest target band, and 20:1 lands at roughly the field's 94th percentile,
# which is exactly what a "legal but rare" maximum should look like.
# Maintainer, on seeing those numbers: *"flattest should be 2.0x while the
# sharpest should be 8.0x and the one in the center 4.0x — a beautiful
# distribution of 2x, 4x, 8x"*. Adopted. It is the measured distribution snapped
# to a DOUBLING ladder: p25 1.9 -> 2, median 4.0 -> 4 (exact), p75 7.5 -> 8. Each
# step is one doubling, which makes the whole scale memorable instead of a set of
# empirical decimals, and it costs at most 0.5x of fidelity at the edges.
# The ladder continues 2 · 4 · 8 · 16, and the legal maximum of 20:1 sits just past
# 16 — so the window is "one doubling beyond the sharpest default".
FIELD_RATIO_LOW = 2.0                              # p25 1.9, snapped
FIELD_RATIO_HIGH = 8.0                             # p75 7.5, snapped
FIELD_RATIO_MEDIAN = 4.0                           # median 4.0, exact

# Families the MAINTAINER has deliberately placed outside the field band. Empty by
# design: departing from the measured field is a design decision and belongs to a
# person, not to a default. `{family: target_ratio}`.
#
# Candidate #1 is `CannonAP`, and it is the clean example of why this table has to
# exist: DESIGN.md §12.0 names "CannonAP against unarmoured infantry" as the
# archetype for the 20:1 extreme, while the corpus measures CannonAP at just
# 1.8x-2.6x — the source engines write AP as ~100 against everything armoured, so
# averaging leaves it nearly flat. The field cannot supply a distinction it never
# drew; only a ruling can.
SPECIALIST_RATIOS: dict[str, float] = {}


def fit_ratio(profile: dict[str, float], target: float | None = None,
              low: float = FIELD_RATIO_LOW,
              high: float = FIELD_RATIO_HIGH) -> dict[str, float]:
    """Bring a profile's max:min ratio into the field's band, and no further.

    **Inside the band this is a no-op** — the measured shape ships verbatim,
    plateaus, cliffs and all. That is the strongest form of "the corpus supplies
    the magnitudes": most families are not touched at all.

    Outside it, the correction is a POWER LAW about the profile's geometric mean,
    `v' = G * (v/G) ** alpha`, rather than an affine rescale onto a floor. Three
    reasons the power law is the right instrument here:

      * it is scale-free, so it changes the RATIO without also deciding the
        absolute level — the level is the window's job, not the spread rule's;
      * it preserves the geometric mean, which is the correct centre for a set of
        MULTIPLIERS (an affine rescale onto a floor drags the mean down and would
        silently make every stretched family cheaper via K);
      * it is monotone, so the ordering law's sequence survives untouched.

    `alpha = log(target) / log(current)` hits the target ratio exactly.
    """
    values = [v for v in profile.values() if v > 0]
    if len(values) < 2:
        return dict(profile)
    lo, hi = min(values), max(values)
    if lo <= 0 or hi <= lo:
        return dict(profile)
    current = hi / lo
    if target is None:
        target = min(max(current, low), high)
    if abs(target - current) < 1e-9:
        return dict(profile)                       # already inside the band
    centre = statistics.geometric_mean(values)
    alpha = math.log(target) / math.log(current)
    return {k: centre * (max(v, GMEAN_FLOOR) / centre) ** alpha for k, v in profile.items()}


def fit_window(profile: dict[str, float]) -> dict[str, float]:
    """Slide the profile into `[ABSOLUTE_FLOOR, NORMALISE_CEILING]`, ratio intact.

    Scaling MULTIPLICATIVELY is what keeps the ratio — an affine squeeze onto the
    window would quietly change the spread that `fit_ratio` just set. Only when a
    profile is too WIDE for the window at all (ratio > 20:1) is the spread itself
    compressed, and then only to exactly the legal maximum.
    """
    values = [v for v in profile.values() if v > 0]
    if not values:
        return dict(profile)
    lo, hi = min(values), max(values)
    limit = NORMALISE_CEILING / ABSOLUTE_FLOOR     # 20:1, the legal maximum
    if hi / lo > limit:
        profile = fit_ratio(profile, target=limit)
        values = [v for v in profile.values() if v > 0]
        lo, hi = min(values), max(values)
    scale = 1.0
    if hi > NORMALISE_CEILING:
        scale = NORMALISE_CEILING / hi
    if lo * scale < ABSOLUTE_FLOOR:
        scale = ABSOLUTE_FLOOR / lo
    return {k: v * scale for k, v in profile.items()}


def shape_profile(profile: dict[str, float], floor: float,
                  target_ratio: float | None = None) -> dict[str, float]:
    """THE SPREAD RULE: field-band spread, inside the window, no two values equal.

    `floor` is retained for the families Cameo INVENTED, which have no measured
    ratio to fit and still take an explicit floor. For a measured family it is
    unused — its spread comes from the corpus, and its level from the window.
    """
    if not profile:
        return {}
    values = list(profile.values())
    lo, hi = min(values), max(values)
    if hi <= lo:                                   # a totally flat input
        return {k: max(floor, ABSOLUTE_FLOOR) for k in profile}
    return enforce_distinct(fit_window(fit_ratio(profile, target=target_ratio)))


def enforce_distinct(profile: dict[str, float], gap: float = MIN_GAP) -> dict[str, float]:
    """No two values identical — the maintainer's hard rule, applied last.

    Walks DOWN from the peak. Nudging upward instead pins ties against the 100
    cap, where clamping silently re-creates the duplicate it was removing (Tesla
    shipped `Plate 100` AND `Superheavy 100` that way). Descending has room by
    construction: 17 armors need 16 units of separation inside a >=75 range.

    ⚠ Must run AFTER the derived armors are added. `Heroic` and `Airborne` are
    computed from other cells, so they can land exactly on one — `missile_he`
    produced two 15.0s and `missile_ap` another. A rule enforced before the last
    value is written is not enforced.
    """
    order = sorted(profile, key=lambda k: -profile[k])
    out: dict[str, float] = {}
    previous = None
    for key in order:
        value = round(profile[key], 1)
        if previous is not None and value >= previous:
            value = round(previous - gap, 1)
        out[key] = value
        previous = value

    # The descent can push the tail under the window (`MissileAA_Heavy` landed a
    # derived `Heroic` on 9). Repair from the BOTTOM up, raising only what breaches
    # and leaving everything already inside untouched, so the measured shape above
    # the floor survives. Feasible by construction: 18 values at a gap of 2 need 34
    # points and the window is 190 wide.
    if out and min(out.values()) < ABSOLUTE_FLOOR:
        previous = None
        for key in reversed(order):
            lowest = ABSOLUTE_FLOOR if previous is None else round(previous + gap, 1)
            value = min(max(out[key], lowest), NORMALISE_CEILING)
            out[key] = round(value, 1)
            previous = out[key]
    return out


def order_violations(profile: dict[str, float], direction: str) -> list[str]:
    """Ladders where the measured profile disagrees with the law's direction."""
    bad = []
    for macro, ladder in CAMEO_LADDERS.items():
        present = [a for a in ladder if a in profile]
        if len(present) < 2:
            continue
        vals = [profile[a] for a in present]
        ok = (all(x <= y for x, y in zip(vals, vals[1:])) if direction == "heavy"
              else all(x >= y for x, y in zip(vals, vals[1:])))
        if not ok:
            bad.append(f"{macro} (" + " ".join(f"{a}={profile[a]:g}"
                                               for a in present) + ")")
    return bad


def cameo_profile(family: str) -> dict[str, float] | None:
    """Cameo's CURRENT profile for a `^Warhead_*` family, normalised the same way.

    Read from the resolved ruleset rather than the file, so inheritance is
    applied — the number compared is the one the game uses.
    """
    try:
        sys.path.insert(0, str(ROOT / "tools" / "audit"))
        from cameo_model import Model
    except ImportError:
        return None
    node = Model().rs.weapons.get(family)
    if node is None:
        return None
    for child in node.children:
        # the MAIN warhead only — not the _Percentage or _ExtraDamage twins
        if not child.key.startswith("Warhead@") or child.key.endswith(
                ("_Percentage", "_ExtraDamage", "_FriendlyFire")):
            continue
        for grand in child.children:
            if grand.key != "Versus":
                continue
            vals = {}
            for leaf in grand.children:
                if leaf.key.lower() in NON_ARMOR:
                    continue
                try:
                    vals[leaf.key] = float(leaf.value)
                except (TypeError, ValueError):
                    continue
            if vals:
                return {k: round(v, 1) for k, v in normalise(vals).items()}
    return None


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def render(concept: str, rows: list[dict]) -> str:
    spec = ARCHETYPES[concept]
    lines = [f"## `{concept}` — {spec['what']}", ""]
    if not rows:
        return "\n".join(lines + ["_No source resolves this concept._", ""])
    flag_scale_outliers(rows)

    lines += [f"Cameo family: `{spec['cameo_family']}` · sources: "
              f"**{len({r['source'] for r in rows})}** · profiles: **{len(rows)}**", ""]

    # --- Table A: original armor vocabulary --------------------------------- #
    armors: list[str] = []
    for r in rows:
        for a in r["versus"]:
            if a.lower() not in armors:
                armors.append(a.lower())
    lines += ["### Table A — as each mod ships it (original armor types)", "",
              "| source | warhead | how identified | " + " | ".join(armors) + " |",
              "|---|---|---|" + "--:|" * len(armors)]
    for r in sorted(rows, key=lambda r: (r["lineage"], r["source"])):
        cells = []
        for a in armors:
            v = {k.lower(): v for k, v in r["versus"].items()}.get(a)
            cells.append("—" if v is None else f"{v:g}")
        lines.append(f"| `{r['source']}` | `{r['warhead']}` | {r['how']} | "
                     + " | ".join(cells) + " |")

    # --- Table B: mapped onto Cameo's 16 ------------------------------------ #
    lines += ["", "### Table B — extrapolated onto Cameo's 16 armor types", "",
              "⚠ Direct where the source has the armor; **extrapolated** for the ladder",
              "ends (Heroic / Scout / Superheavy) by continuing the ladder's own step; the",
              "four aircraft classes are read off the vehicle ladder by weight",
              "(Fighter/Helicopter←Light, Bomber←Medium, Spaceship←Heavy).", "",
              "| source | " + " | ".join(CAMEO16) + " |",
              "|---|" + "--:|" * len(CAMEO16)]
    for r in sorted(rows, key=lambda r: (r["lineage"], r["source"])):
        vals, _ = to_cameo(r["versus"])
        cells = ["—" if vals.get(a) is None else f"{vals[a]:g}" for a in CAMEO16]
        lines.append(f"| `{r['source']}` | " + " | ".join(cells) + " |")

    counts = {a: len(v) for a, v in buckets_of(rows).items()}
    lines.append("| _n sources_ | "
                 + " | ".join(str(counts.get(a, 0)) for a in CAMEO16) + " |")

    # --- Table C: the three aggregations, against Cameo as it stands now ----- #
    aggs = {label: aggregate(rows, how) for label, how in
            (("median", "median"), ("arithmetic mean", "mean"),
             ("geometric mean", "gmean"))}
    cameo = cameo_profile(spec["cameo_family"])
    if cameo:
        aggs["CAMEO today"] = cameo

    lines += ["", "### Table C — three ways to aggregate, vs Cameo today", "",
              "All four rows are normalised to max = 100, so they compare SHAPE, not",
              "power level. `median` is robust to one weird mod; `arithmetic mean` lets",
              "every source pull proportionally; `geometric mean` is the correct average",
              "for MULTIPLIERS (averaging x2 and x0.5 arithmetically invents a net buff",
              "of 1.25 — geometrically it is 1.0). A wide mean-vs-gmean gap means the",
              "sources disagree about that armor.", "",
              "| aggregation | " + " | ".join(CAMEO16) + " | span |",
              "|---|" + "--:|" * (len(CAMEO16) + 1)]
    for label, prof in aggs.items():
        cells = ["—" if prof.get(a) is None else f"{prof[a]:g}" for a in CAMEO16]
        vals = list(prof.values())
        span = f"{max(vals) - min(vals):.0f}" if vals else "—"
        mark = "**" if label == "CAMEO today" else ""
        lines.append(f"| {mark}{label}{mark} | " + " | ".join(cells) + f" | {span} |")

    # --- Table D: the law-conformant synthesis ------------------------------ #
    direction = spec.get("direction", "light")
    med = aggs["median"]
    violations = order_violations(med, direction)
    lawful = lawful_profile(med, direction)
    floor = EXTREME_FLOOR if spec.get("specialised") else spec.get("floor", 15)
    lawful = shape_profile(lawful, floor)
    lawful.update(derive_armors(lawful))
    lawful = enforce_distinct(lawful)      # derived cells can land on an existing one
    lines += ["", f"### Table D — PROPOSED: field magnitudes, law order "
              f"(`{direction}`-favouring)", "",
              "The corpus and the ordering law disagree, and each is right about a",
              "different thing. The measured values are kept EXACTLY; only which armor",
              "they attach to changes, so the spread and the cliffs survive while the",
              "ladder reads the way the law requires (W13 rule 6).", ""]
    if violations:
        lines += ["⚠ The raw field median violates the law on: "
                  + "; ".join(f"**{v}**" for v in violations) + ".", "",
                  "For AP that is not a data error — six independent RA2-lineage mods all",
                  "write `none 25 · flak 25 · plate 15`, i.e. armour piercing doing LESS to",
                  "plated infantry than to unplated. It is Westwood's design, faithfully",
                  "cloned. Cameo's law inverts it so the weapon stays readable.", ""]
    else:
        lines += ["✅ The field median already obeys the law here — the reorder is a no-op.",
                  ""]
    lines += ["| profile | " + " | ".join(CAMEO16) + " |",
              "|---|" + "--:|" * len(CAMEO16),
              "| field median (raw) | "
              + " | ".join("—" if med.get(a) is None else f"{med[a]:g}"
                           for a in CAMEO16) + " |",
              "| **PROPOSED (law order)** | "
              + " | ".join("—" if lawful.get(a) is None else f"**{lawful[a]:g}**"
                           for a in CAMEO16) + " |"]
    if cameo:
        lines.append("| Cameo today | "
                     + " | ".join("—" if cameo.get(a) is None else f"{cameo[a]:g}"
                                  for a in CAMEO16) + " |")

    vals = list(med.values())
    if vals:
        lines += ["", f"**Reference span {max(vals) - min(vals):.0f}** "
                  f"(min {min(vals):g} · max {max(vals):g})."]
        if cameo:
            cvals = list(cameo.values())
            lines.append(f"**Cameo span {max(cvals) - min(cvals):.0f}** — "
                         + ("SHARPER than" if max(cvals) - min(cvals) >
                            max(vals) - min(vals) else "FLATTER than")
                         + " the field for this concept.")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("concept", nargs="?", help="which concept to aggregate")
    ap.add_argument("--list", action="store_true", help="list known concepts")
    ap.add_argument("--all", action="store_true", help="every concept")
    ap.add_argument("--write", action="store_true", help=f"write {OUT.relative_to(ROOT)}")
    args = ap.parse_args()

    if args.list:
        for name, spec in ARCHETYPES.items():
            print(f"  {name:14} {spec['what']}")
        return 0

    names = list(ARCHETYPES) if args.all else ([args.concept] if args.concept else [])
    if not names:
        ap.error("give a concept, --all, or --list")
    for name in names:
        if name not in ARCHETYPES:
            print(f"unknown concept: {name}; known: {', '.join(ARCHETYPES)}")
            return 1

    chunks = [render(n, collect(n)) for n in names]
    body = "\n\n".join(chunks)
    print(body)
    if args.write:
        header = [
            "# W13 — weapon-concept reference tables",
            "",
            "Generated by `tools/reference/aggregate_archetype.py` from",
            "`docs/reference/versus_raw.json` (16 mods, 3150 profiles).",
            "One concept at a time, per the maintainer's method: see what every mod ships",
            "for the SAME weapon, then extrapolate onto Cameo's armor set.",
            "",
            "For the INI mods the warhead is found by TRACING `[actor] Primary=` ->",
            "`[weapon] Warhead=`, so each row is the weapon that building actually fires",
            "rather than a warhead that merely has a matching name.",
            "",
        ]
        OUT.write_text("\n".join(header) + body + "\n", encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
