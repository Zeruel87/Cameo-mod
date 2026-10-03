#!/usr/bin/env python3
"""Map each reference source's armour rows onto Cameo's 16, and average the sources.

Two steps, and they are deliberately separate:

1. ANCHOR — each source armour is pinned to a POSITION on one of our ladders. Some pin exactly
   (`combined_arms.None` IS our `None`); some pin between rungs (`combined_arms.Light` sits at
   0.5 on the vehicle ladder, between Scout and Light); some pin flat across a whole ladder
   (`combined_arms.Aircraft`, the only source with a real air tag); some are excluded outright
   (walls, terrain, projectile-interception classes).

2. INTERPOLATE — the rungs a source did not pin are filled by LOG-LINEAR interpolation between
   its anchors, and extrapolation beyond the outermost pair. Log-linear because these are
   multipliers: the step from Light to Medium is a ratio, not a difference.

⚠ A ladder with ONE anchor cannot say anything about slope, so it fills only its own rung and
abstains on the rest — unless the mapping says `flat`. A ladder with NO anchor abstains entirely.
That is not the maintainer's "no abstention" ruling being ignored: that ruling was about not
DISCARDING a source whose mapping is awkward. A source that genuinely has no second infantry rung
(OpenRA Red Alert) has no opinion about Flak, and inventing one would be worse than silence.

⭐ `Heroic` is never interpolated. DESIGN.md §12.0b makes it a DERIVED column — `Plate x Scout /
peak` — so it is recomputed after the ladders are filled, from the result.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "reference"))

import warhead_matrix as wm  # noqa: E402

# Cameo's own ladders, from `tools/balance/armor_exposure.py` — the single definition.
LADDERS = {
    "INF": ["None", "Flak", "Plate"],
    "VEH": ["Scout", "Light", "Medium", "Heavy", "Superheavy"],
    "BLD": ["Wood", "Steel", "Concrete"],
    "AIR": ["Fighter", "Bomber", "Helicopter", "Spaceship"],
}
DERIVED = ["Heroic"]
# DESIGN.md §12.0 rule 4: a 20:1 window. Rows arrive normalised to a centre of 100.
WINDOW_LO, WINDOW_HI = 100 * wm.WINDOW_LO, 100 * wm.WINDOW_HI
CAMEO_ARMORS = [a for lad in LADDERS.values() for a in lad] + DERIVED

# ── THE ANCHOR TABLE ──────────────────────────────────────────────────────────────────────────
#
# `source armour -> [anchor, ...]`, where an anchor is one of
#     ("LADDER", index)      pin at that position; index may be fractional
#     ("LADDER", "flat")     the same value on every rung of that ladder
#     None                   excluded; this armour casts no vote at all
#
# One source armour may anchor SEVERAL ladders: Combined Arms' `Light` is both its middle infantry
# rung and its light-vehicle class, so it votes on both.
#
# ⚠ THE NAMES LIE. Dune 2000's `harvester` is its TOUGHEST armour, not a harvester class, and
# DTA's `light` is verified to be exactly JEEP/BGGY/BIKE/RAIDER/RANG — scouts, not the Tiberian
# Sun building class of the same name. Every row here was checked against the actors that declare
# it; see `warhead_workbook.ARMOR_PROPOSAL` for the prose reasoning behind each ruling.
EXCLUDE = None

ANCHORS: dict[str, dict[str, list | None]] = {
    "combined_arms": {
        "None": [("INF", 0)],
        "Light": [("INF", 1), ("VEH", 0.5)],
        "Heavy": [("INF", 2), ("VEH", 3.5)],
        "Wood": [("BLD", 0)],
        "Concrete": [("BLD", 2)],
        "Aircraft": [("AIR", "flat")],
        "Brick": EXCLUDE,      # walls and fences only
        "Tree": EXCLUDE,       # terrain
    },
    "openra_ra": {
        "None": [("INF", 0)],
        "Light": [("VEH", 0.5), ("AIR", 0)],
        "Heavy": [("VEH", 3.5), ("AIR", 3), ("BLD", 2)],
        "Wood": [("BLD", 0)],
        "Concrete": [("BLD", 2)],
        "Tree": EXCLUDE,
    },
    "openra_td": {
        "None": [("INF", 0)],
        "Light": [("VEH", 0.5), ("AIR", 0)],
        "Heavy": [("VEH", 3.5), ("AIR", 3)],
        "Wood": [("BLD", 0)],
        "Concrete": [("BLD", 2)],
    },
    "dta_enhanced": {
        "none": [("INF", 0)],
        "light": [("VEH", 0)],          # verified scouts, not the TS building class
        "medium": [("VEH", 2)],
        "heavy": [("VEH", 3), ("AIR", 3)],
        "wood": [("BLD", 0)],
        "concrete": [("BLD", 2)],
        "naval_light": EXCLUDE,         # ROADMAP: the naval ladder
        "naval_medium": EXCLUDE,
        "naval_heavy": EXCLUDE,
        "rocket": EXCLUDE,              # projectile-interception class, not a unit armour
        "special": EXCLUDE,
    },
    # ── The YR/RA2 dialect. Its nine armours ARE Cameo's nine ground rows, name for name —
    # which is not a coincidence: Cameo took the vocabulary from here. So the mapping is exact,
    # and only Scout and Superheavy (which RA2 has no equivalent of) are extrapolated.
    **{sid: {
        "none": [("INF", 0)], "flak": [("INF", 1)], "plate": [("INF", 2)],
        "light": [("VEH", 1)], "medium": [("VEH", 2)], "heavy": [("VEH", 3)],
        "wood": [("BLD", 0)], "steel": [("BLD", 1)], "concrete": [("BLD", 2)],
    } for sid in ("mental_omega", "cnc_reloaded", "rise_of_the_east",
                  "ra20xx", "ra2_reborn", "red_resurrection")},
    "romanovs_vengeance": {
        "None": [("INF", 0)], "Flak": [("INF", 1)], "Plate": [("INF", 2)],
        "Light": [("VEH", 1)], "Medium": [("VEH", 2)], "Heavy": [("VEH", 3)],
        "Wood": [("BLD", 0)], "Steel": [("BLD", 1)], "Concrete": [("BLD", 2)],
        "concrete": [("BLD", 2)],   # 8 buildable actors use the lowercase spelling as well
        "steel": EXCLUDE,           # 10 actors, 0 buildable — a dead spelling
        "Rocket": EXCLUDE,          # projectile-interception class, as DTA's
        "Drone": EXCLUDE,
    },
}
ANCHORS["dta_classic"] = ANCHORS["dta_enhanced"]

# ── Dune 2000, both readings. ⚠ THE NAMES LIE HERE MORE THAN ANYWHERE ELSE, and every row below
# was checked against the actors that declare it: `wood` is trike/raider/missile_tank — D2K's
# FAST vehicles, not a building class — and `harvester` is our Superheavy because role beats raw
# toughness (it measures only 3rd toughest but it is the biggest, slowest ground vehicle).
# `wall` anchors the heavy end of the building ladder alongside `cy` rather than taking a rung.
_D2K = {
    "none": [("INF", 0)],
    "wood": [("VEH", 0)],
    "light": [("VEH", 1), ("AIR", 0)],
    "heavy": [("VEH", 3), ("AIR", 3)],
    "harvester": [("VEH", 4)],
    "building": [("BLD", 1)],
    "cy": [("BLD", 2)],
    "wall": [("BLD", 2)],
    "concrete": EXCLUDE,        # terrain, not a unit armour
    "invulnerable": EXCLUDE,
}
ANCHORS["openra_d2k"] = {
    **_D2K,
    # Cased duplicates with zero buildable actors — dead spellings the mod never resolves to.
    "None": EXCLUDE, "Wood": EXCLUDE, "Light": EXCLUDE, "Heavy": EXCLUDE, "Concrete": EXCLUDE,
}
ANCHORS["d2k_mod"] = {k.title() if k != "cy" else "CY": v for k, v in _D2K.items()}

# ── Tiberian Sun dialect. ⚠ `light` here is NOT DTA's `light`. The DTA ruling verified that its
# `light` is exactly JEEP/BGGY/BIKE/RAIDER/RANG — pure scouts — but OpenRA TS puts the JUGGERNAUT,
# the Tick Tank and Artillery in `Light` alongside the Buggy, plus all six aircraft. Two mods on
# one engine, the same rung name, different meanings; so TS anchors our Light, not our Scout, and
# Scout is extrapolated below it. As in RA and TD, a TS aircraft IS `light`.
_TS = {
    "none": [("INF", 0)],
    "wood": [("BLD", 0)],
    "light": [("VEH", 1), ("AIR", 0)],
    "heavy": [("VEH", 3), ("AIR", 3), ("BLD", 2)],
    "concrete": [("BLD", 2)],
}
ANCHORS["twisted_insurrection"] = dict(_TS)
ANCHORS["openra_ts"] = {
    **{k.capitalize(): v for k, v in _TS.items()},
    # The lowercase spellings have 0 buildable actors each — dead rows, as in OpenRA Dune 2000.
    "none": EXCLUDE, "wood": EXCLUDE, "light": EXCLUDE,
    "heavy": EXCLUDE, "concrete": EXCLUDE,
}

# ── Shattered Paradise, ruled 2026-09-21. `Bike` is a single fast vehicle and anchors Scout;
# `Boss` is a campaign special and `Shield` is our shield LAYER, not an armour. The five `*Armor`
# rows have zero actors — dead spellings the mod never resolves to.
ANCHORS["shattered_paradise"] = {
    "Infantry": [("INF", 0)],
    "Bike": [("VEH", 0)],
    "Light": [("VEH", 1)],
    "Heavy": [("VEH", 3)],
    "Building": [("BLD", 0)],
    "Defense": [("BLD", 2)],
    "Concrete": [("BLD", 2)],
    "Aircraft": [("AIR", "flat")],
    "Shield": EXCLUDE, "Boss": EXCLUDE, "None": EXCLUDE,
    "InfantryArmor": EXCLUDE, "BuildingArmor": EXCLUDE, "VehicleArmor": EXCLUDE,
    "DefenseArmor": EXCLUDE, "ConcreteArmor": EXCLUDE,
}

# ── Crystallized Nexus. ⛔ IT HAS A TWO-LAYER ARMOUR SYSTEM and the two layers must not be read
# as one ladder. Every actor carries BOTH a macro tag (`Vehicle`, `Infantry`, `Building`,
# `Aircraft`) AND a weight class (`Light`..`Superheavy`), and OpenRA MULTIPLIES the Versus rows of
# every Armor trait a target has — so `BGGY` is `Light` AND `Vehicle` at once, and `Light` spans
# infantry, buildings and aircraft as well as vehicles. The weight classes are the real ladder;
# the macro tags are a plating layer on top of it, which is why `Vehicle` (29 actors) looks like
# it overlaps everything. Maintainer: *"we only need the 4 armor types"* — the four weight rungs.
ANCHORS["crystallized_nexus"] = {
    "Light": [("VEH", 1)], "Medium": [("VEH", 2)],
    "Heavy": [("VEH", 3)], "Superheavy": [("VEH", 4)],
    "Infantry": [("INF", 0)], "Building": [("BLD", 0)], "Aircraft": [("AIR", "flat")],
    "Vehicle": EXCLUDE,     # the macro LAYER, not a rung — it multiplies with the four above
    "Flora": EXCLUDE, "Shield": EXCLUDE, "Stability": EXCLUDE,
    "Cyborg": EXCLUDE, "None": EXCLUDE, "none": EXCLUDE,
}

# Cameo votes as one source among the twenty (maintainer's ruling, extending R20). Its own rows
# ARE our sixteen, so the mapping is the identity; `Heroic` is recomputed like every other source's.
_IDENTITY = {a: [(lad, i)] for lad, rungs in LADDERS.items() for i, a in enumerate(rungs)}
ANCHORS["cameo"] = {
    **_IDENTITY,
    # ⚠ NOT ARMOUR ROWS. `Shield` is its own compressed ladder (§12.0c) and HAZMAT / ARMOR /
    # REFLECTOR / COMPOSITE / BLAST are PLATINGS — a layer selected on top of an armour, not a
    # rung on any ladder (`tools/balance/gen_weapon_template.NON_ARMOR_ROWS`). `Heroic` is the
    # derived column and is recomputed, never voted on.
    "Heroic": EXCLUDE, "Shield": EXCLUDE, "HAZMAT": EXCLUDE, "ARMOR": EXCLUDE,
    "REFLECTOR": EXCLUDE, "COMPOSITE": EXCLUDE, "BLAST": EXCLUDE,
}
ANCHORS["cameo_resolved"] = ANCHORS["cameo"]

# ── ONE MOD, ONE VOTE ─────────────────────────────────────────────────────────────────────────
#
# Every source counts once whatever its size: Combined Arms' 550 weapons and OpenRA Tiberian
# Dawn's handful weigh the same. Combination is GEOMETRIC, because these are multipliers.
#
# ⚠ TWO ENTRIES ARE THE SAME MOD READ TWICE. `dta_classic` is DTA again (Enhanced is canonical)
# and `cameo_resolved` is Cameo again — R20 casts Cameo's vote through its `^Warhead_*` TEMPLATES,
# not its resolved weapons, whose un-retrofitted legacy tail would be a vote for the status quo.
# Counting either would hand one mod a double vote.
DOUBLE_COUNTED = {"dta_classic", "cameo_resolved"}

UNRULED: dict[str, str] = {}

# Sources whose mapping is NOT yet ruled. They are measured and waiting, not forgotten — running
# the engine reports them rather than guessing, because in every source checked so far at least
# one armour name meant something other than it said.
_UNRULED_RESOLVED = {
    "openra_ts": "cased and lowercase spellings coexist (`Wood` 20 buildable vs `wood` 0); and "
                 "whether TS `light` is our Scout (as ruled for DTA) or our Light is undecided",
    "twisted_insurrection": "same TS dialect and the same open question about `light`",
    "shattered_paradise": "`Infantry`/`Building`/`Defense`/`Bike`/`Boss` need rungs, `Shield` is "
                          "our shield LAYER not an armour, and five `*Armor` rows have 0 actors",
    "crystallized_nexus": "`Vehicle` (29 actors) overlaps Light/Medium/Heavy/Superheavy; "
                          "`Flora`, `Shield` and `Stability` are not unit armours",
}


# ── HOW MUCH DOES A SOURCE ACTUALLY KNOW ABOUT A LADDER? ──────────────────────────────────────
#
# An armour tag that anchors two ladders contributes ONE measured number to both, and that number
# is dominated by whichever macro type wears the tag most. Combined Arms is the worked example:
# its `Heavy` anchors our Plate infantry rung AND the top of the vehicle ladder, but of its 101
# wearers **98 are vehicles and 3 are cyborgs** — so the Plate rung was being set by a number that
# describes heavy tanks. CA is the only source of eighteen that inverts its own infantry ladder,
# and this is why.
#
# ⭐ CYBORGS COUNT HALF TO EACH (maintainer's ruling, 2026-09-21). DESIGN.md's cyborg dual-armor
# rule is explicit: a CABAL cyborg keeps its infantry-class `Armor` and adds a vehicle
# `Armor@<role>`, "so cyborgs count as both infantry and vehicles for weapon Versus tables", and
# the two rows are combined by their GEOMETRIC mean (`MultiArmorCombination: Geometric` since
# 2026-09-25 — `Plate` 88 with `Superheavy` 10 resolves to 30; it was the arithmetic 49 before). A cyborg is infantry x vehicle, so it casts half a vote on each ladder.
#
# The result weights a source's opinion about a LADDER by how much real evidence it has for that
# ladder's rungs. Nothing is discarded — CA still speaks about infantry, just quietly.
CYBORG_TOKENS = {"cyborg", "healablecyborg"}
AIR_TOKENS = {"air", "airsmall"}
BLD_TOKENS = {"structure", "building"}


def macro_shares(actors: list) -> dict[str, float]:
    """{ladder: share of this armour's wearers}, cyborgs counting half INF and half VEH."""
    tally = collections.Counter()
    for _hp, targets in actors:
        tokens = {t.lower() for t in targets}
        if tokens & AIR_TOKENS:
            tally["AIR"] += 1
        elif tokens & CYBORG_TOKENS:
            tally["INF"] += 0.5
            tally["VEH"] += 0.5
        elif "infantry" in tokens:
            tally["INF"] += 1
        elif tokens & BLD_TOKENS:
            tally["BLD"] += 1
        else:
            tally["VEH"] += 1
    total = sum(tally.values())
    return {k: v / total for k, v in tally.items()} if total else {}


def ladder_confidence(source: str, armor_actors: dict) -> dict[str, float]:
    """How strongly a source speaks about each ladder, from its anchors' wearer mix.

    A source with no actor census (the INI dialects, the transcribed table) speaks at full
    strength: its armour names are already per-macro-type, so there is nothing to discount.
    """
    table = ANCHORS.get(source) or {}
    if not armor_actors:
        return {ladder: 1.0 for ladder in LADDERS}

    lower = {k.lower(): v for k, v in armor_actors.items()}
    out: dict[str, float] = {}
    for ladder in LADDERS:
        shares = []
        for armor, spec in table.items():
            if not spec or not any(l == ladder for l, _ in spec):
                continue
            actors = lower.get(armor.lower())
            if actors:
                shares.append(max(macro_shares(actors).get(ladder, 0.0), 0.01))
        out[ladder] = wm.gmean(shares) if shares else 1.0
        if not math.isfinite(out[ladder]) or out[ladder] <= 0:
            out[ladder] = 1.0
    return out


def interpolate_ladder(rung_count: int, anchors: list[tuple[float, float]]) -> list[float | None]:
    """Fill a ladder from its anchors, log-linear, extrapolating past the ends.

    `anchors` is [(index, value), ...]. One anchor fills only its own rung — a single point
    carries no slope, so inventing the rest would be inventing the source's opinion.
    """
    live = [(i, v) for i, v in anchors if v is not None and v > 0]
    if not live:
        return [None] * rung_count
    live.sort()
    if len(live) == 1:
        index, value = live[0]
        out: list[float | None] = [None] * rung_count
        nearest = min(range(rung_count), key=lambda r: abs(r - index))
        if abs(nearest - index) <= 0.5:
            out[nearest] = value
        return out

    logs = [(i, math.log(v)) for i, v in live]
    out = []
    for rung in range(rung_count):
        if rung <= logs[0][0]:
            (x0, y0), (x1, y1) = logs[0], logs[1]
        elif rung >= logs[-1][0]:
            (x0, y0), (x1, y1) = logs[-2], logs[-1]
        else:
            k = next(j for j in range(len(logs) - 1) if logs[j][0] <= rung <= logs[j + 1][0])
            (x0, y0), (x1, y1) = logs[k], logs[k + 1]
        slope = 0.0 if x1 == x0 else (y1 - y0) / (x1 - x0)
        out.append(math.exp(y0 + slope * (rung - x0)))
    # ⚠ EXTRAPOLATION MUST BE CLAMPED TO THE DESIGN WINDOW. A source that anchors only two
    # ADJACENT rungs of a ladder has a slope but no evidence that it continues, and pushing that
    # slope outward compounds it: the transcribed Dune 2000 table pins its building ladder at
    # Steel and Concrete only, and extrapolating down to Wood produced 250 — past the 200 ceiling
    # DESIGN.md §12.0 rule 4 sets for the whole 20:1 window. The rows are normalised to a centre
    # of 100, so the window is [10, 200] here.
    return [min(max(v, WINDOW_LO), WINDOW_HI) for v in out]


def map_row(source: str, armors: list[str], values: list[float | None]) -> dict[str, float | None]:
    """One source's armour row -> Cameo's 16."""
    table = ANCHORS.get(source)
    if table is None:
        raise KeyError(source)
    by_ladder: dict[str, list[tuple[float, float]]] = collections.defaultdict(list)
    flat: dict[str, list[float]] = collections.defaultdict(list)

    for armor, value in zip(armors, values):
        spec = table.get(armor, "unmapped")
        if spec == "unmapped":
            raise KeyError(f"{source}: no anchor declared for armour {armor!r}")
        if spec is EXCLUDE or value is None or value <= 0:
            continue
        for ladder, where in spec:
            if where == "flat":
                flat[ladder].append(value)
            else:
                by_ladder[ladder].append((float(where), value))

    out: dict[str, float | None] = {}
    for ladder, rungs in LADDERS.items():
        if ladder in flat:
            value = wm.gmean(flat[ladder])
            for rung in rungs:
                out[rung] = value
            continue
        filled = interpolate_ladder(len(rungs), by_ladder.get(ladder, []))
        for rung, value in zip(rungs, filled):
            out[rung] = value
    # §12.0b: Heroic is DERIVED, never interpolated.
    plate, scout = out.get("Plate"), out.get("Scout")
    peak = max((v for v in out.values() if v), default=0)
    out["Heroic"] = (plate * scout / peak) if (plate and scout and peak) else None
    return out


def report() -> str:
    data = wm.collect()
    lines = [f"## Armour interpolation — {len(ANCHORS)} of {len(data)} sources mapped", "",
             "| source | armours | " + " | ".join(CAMEO_ARMORS) + " |",
             "|---|--:|" + "--:|" * len(CAMEO_ARMORS)]
    mapped_rows: dict[str, dict] = {}
    confidence: dict[str, dict] = {}
    for sid, matrix in data.items():
        if sid not in ANCHORS:
            continue
        armors = matrix["armors"]
        # the source's own centre row: the usage-weighted gmean of every weapon, per armour
        centre = []
        for i in range(len(armors)):
            cells = [(r["scaled"][i], float(r["uses"]))
                     for r in matrix["rows"] if r["scaled"][i]]
            if not cells or not any(w > 0 for _, w in cells):
                cells = [(v, 1.0) for v, _ in cells]
            centre.append(wm.weighted_gmean(cells) if cells else None)
        mapped = map_row(sid, armors, centre)
        mapped_rows[sid] = mapped
        confidence[sid] = ladder_confidence(sid, matrix.get("armor_actors") or {})
        cells = " | ".join("n/a" if mapped[a] is None else f"{mapped[a]:.0f}"
                           for a in CAMEO_ARMORS)
        note = "  *(not counted — same mod twice)*" if sid in DOUBLE_COUNTED else ""
        lines.append(f"| `{sid}`{note} | {len(armors)} | {cells} |")

    combined = average(mapped_rows, confidence)
    lines += ["", "### The averaged target — one mod one vote, geometric", "",
              "| armour | value | voters | shape | abstained |", "|---|--:|--:|--:|---|"]
    for armor in CAMEO_ARMORS:
        entry = combined[armor]
        missing = ", ".join(f"`{s}`" for s in entry["abstained"]) or "—"
        value = "n/a" if entry["value"] is None else f"{entry['value']:g}"
        lines.append(f"| **{armor}** | {value} | {entry['voters']} | {entry['shape_voters']} | {missing} |")

    if UNRULED:
        lines += ["", f"### {len(UNRULED)} sources still need an armour ruling", ""]
        for sid, why in sorted(UNRULED.items()):
            lines.append(f"* **`{sid}`** — {why}")
    return "\n".join(lines)


def average(rows: dict[str, dict[str, float | None]],
            confidence: dict[str, dict[str, float]] | None = None) -> dict[str, dict]:
    """Combine the mapped sources into one target matrix, one vote each. See DOUBLE_COUNTED.

    ⛔ SHAPE AND LEVEL ARE AVERAGED SEPARATELY, because the sources do not all vote on every rung.
    A plain per-cell mean compares populations of different size and invents an inversion that no
    source contains: `None` had 18 voters and `Flak` only 9, the nine extra `None`-only voters
    were the low sources (Tiberian Sun 81, Tiberian Dawn 89, Dune 2000 91), and the average came
    out `None` 109.4 BELOW `Flak` 119.9 — an inverted infantry ladder that 8 of the 9 sources with
    an opinion on both rungs individually contradict. DESIGN.md §12.0d says a ladder can never
    invert, so that was a broken measurement, not a finding.

    So: a source that pinned two or more rungs of a ladder votes on that ladder's SHAPE (its own
    rungs normalised to a geometric mean of 1, which makes every source comparable no matter which
    rungs it reached); every source that pinned any rung at all votes on the ladder's LEVEL. The
    result is shape x level, so nobody's data is discarded and nobody's absence distorts a rung.
    """
    out: dict[str, dict] = {}
    confidence = confidence or {}
    live = {sid: row for sid, row in rows.items() if sid not in DOUBLE_COUNTED}

    for ladder, rungs in LADDERS.items():
        shapes: dict[str, list[tuple[float, float]]] = {rung: [] for rung in rungs}
        levels: list[float] = []
        shape_voters = 0
        for sid, row in live.items():
            pinned = [(rung, row[rung]) for rung in rungs if row.get(rung)]
            if not pinned:
                continue
            levels.append(wm.gmean([v for _, v in pinned]))
            if len(pinned) < 2:
                continue                      # one rung carries level, but no shape
            centre = wm.gmean([v for _, v in pinned])
            # ⭐ Weighted by how much this source really knows about THIS ladder — see
            # `ladder_confidence`. Combined Arms' Plate rung rests on 3 cyborgs among 101
            # vehicle wearers, so its infantry shape vote is quiet without being silenced.
            weight = confidence.get(sid, {}).get(ladder, 1.0)
            shape_voters += 1
            for rung, value in pinned:
                shapes[rung].append((value / centre, weight))
        level = wm.gmean(levels) if levels else None
        for rung in rungs:
            votes = [row[rung] for row in live.values() if row.get(rung)]
            shape = wm.weighted_gmean(shapes[rung]) if shapes[rung] else None
            value = (level * shape) if (level and shape) else (wm.gmean(votes) if votes else None)
            out[rung] = {
                "value": round(value, 1) if value else None,
                "voters": len(votes),
                "shape_voters": shape_voters,
                "abstained": sorted(sid for sid, row in live.items() if not row.get(rung)),
            }

    for armor in DERIVED:
        votes = [row[armor] for row in live.values() if row.get(armor)]
        out[armor] = {"value": round(wm.gmean(votes), 1) if votes else None,
                      "voters": len(votes), "shape_voters": 0,
                      "abstained": sorted(sid for sid, row in live.items() if not row.get(armor))}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    text = report()
    print(text)
    if args.write:
        out = ROOT / "docs" / "reference" / "armor_interpolation.json"
        data = wm.collect()
        payload = {}
        for sid, matrix in data.items():
            if sid not in ANCHORS:
                continue
            payload[sid] = {"armors": matrix["armors"],
                            "anchors": {k: v for k, v in ANCHORS[sid].items()}}
        out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
        print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
