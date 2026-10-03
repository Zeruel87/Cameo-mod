#!/usr/bin/env python3
"""warhead_workbook.py — write `warhead_matrix` out as the reviewable Excel workbook.

Separated from `warhead_matrix.py` on purpose: the matrix is the MEASUREMENT and must stay
importable without openpyxl, the workbook is one PRESENTATION of it. Anything that changes a
number belongs next door; this file only lays numbers out.

    python tools/reference/warhead_workbook.py            # -> docs/reference/warhead_matrix.xlsx
    python tools/reference/warhead_workbook.py --out X.xlsx

SHEETS
  README          the method, the rulings it implements, and every caveat that bites
  Summary         one line per source
  <MOD>           the matrix: warheads x armors, NORMALISED (left block) and RAW (right block)
  Armor_Map       every armor type of every source, with a PROPOSED Cameo mapping to correct
  Warhead_Map     every warhead with its factor, and a PROPOSED Cameo family to correct
  Provenance      which actor / slot / weapon put weight on which warhead
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference"))

import warhead_matrix as wm  # noqa: E402

from openpyxl import Workbook  # noqa: E402
from openpyxl.formatting.rule import ColorScaleRule  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT_XLSX = ROOT / "docs" / "reference" / "warhead_matrix.xlsx"

SHEET = {
    "dta_classic": "DTA_Classic",
    "dta_enhanced": "DTA_Enhanced",
    "combined_arms": "CA",
    "openra_ra": "OpenRA_RA",
    "openra_td": "OpenRA_TD",
    "cameo": "Cameo",
    "cameo_resolved": "Cameo_Resolved",
    "d2k_mod": "D2K_Mod",
    "openra_ts": "OpenRA_TS",
    "openra_d2k": "OpenRA_D2K",
    "romanovs_vengeance": "Romanovs_Vengeance",
    "shattered_paradise": "Shattered_Paradise",
    "crystallized_nexus": "Crystallized_Nexus",
    "mental_omega": "Mental_Omega",
    "cnc_reloaded": "CnC_Reloaded",
    "rise_of_the_east": "Rise_of_the_East",
    "ra20xx": "RA20XX",
    "ra2_reborn": "RA2_Reborn",
    "red_resurrection": "Red_Resurrection",
    "twisted_insurrection": "Twisted_Insurrection",
}

HEAD_FILL = PatternFill("solid", fgColor="1F3A5F")
HEAD_FONT = Font(color="FFFFFF", bold=True, size=10)
SUB_FILL = PatternFill("solid", fgColor="E8EDF3")
DECIDE_FILL = PatternFill("solid", fgColor="FFF4CE")
TITLE_FONT = Font(bold=True, size=13)
NOTE_FONT = Font(italic=True, size=9, color="606060")

# ── Cameo's own ladders, from DESIGN.md, so a proposal can name a real target ──────────────────
LADDERS = {
    "INF": ["None", "Flak", "Plate", "Heroic"],
    "VEH": ["Scout", "Light", "Medium", "Heavy", "Superheavy"],
    "BLD": ["Wood", "Steel", "Concrete"],
    "AIR": ["Fighter", "Bomber", "Helicopter", "Spaceship"],
}

# ── THE ARMOR MAPPING, AS RULED BY THE MAINTAINER (2026-09-21) ───────────────────────────────
# These are DECISIONS, not proposals. Two principles run through all of them:
#
#   1. A SOURCE TAG IS READ THROUGH THE ACTOR KIND THAT CARRIES IT. Combined Arms puts `Light` on
#      55 vehicles, 5 ships AND 3 infantry (BRUT/CDOG/ENFO); OpenRA RA puts `Heavy` on 10
#      vehicles, 4 ships and 8 DEFENSIVE BUILDINGS. One tag therefore votes on more than one
#      ladder, split by what actually wears it. Reading the tag alone puts a pillbox's armour
#      into the tank ladder.
#   2. ANCHOR, THEN INTERPOLATE GEOMETRICALLY. A source names fewer rungs than we ship, so its
#      tags anchor specific rungs of ours and the gaps are filled in LOG space (see
#      warhead_matrix.interpolate) — these are multipliers, so the midpoint of 50 and 200 is 100,
#      not 125. Ends beyond the outermost anchor continue the same log-slope.
ARMOR_PROPOSAL: dict[str, dict[str, tuple[str, str]]] = {
    "combined_arms": {
        "None": ("INF None (anchor)", "77 ordinary infantry."),
        "Light": ("INF Flak (anchor, 3 inf) + VEH @0.5 Scout..Light (55 veh, 5 ships)",
                  "RULED: CA's infantry ladder is None -> Light -> Heavy, which maps 1:1 onto "
                  "None -> Flak -> Plate. The same tag also anchors the vehicle ladder between "
                  "our Scout and Light. Ships vote on VEH where they fit."),
        "Heavy": ("INF Plate (anchor, 3 inf) + VEH @3.5 Heavy..Superheavy (89 veh, 8 ships)",
                  "ENLI/REAP/RMBC are CA's heaviest infantry -> our Plate."),
        "Aircraft": ("AIR all four, FLAT", "RULED: CA is the only source with a real air tag; "
                     "37 buildable aircraft, mapped flat to Fighter/Bomber/Helicopter/Spaceship."),
        "Wood": ("BLD Wood (anchor)", "70 ordinary buildings."),
        "Concrete": ("BLD Concrete (anchor)", "23 defences; Steel interpolated between."),
        "Brick": ("EXCLUDED", "RULED: BRIK/CHAIN/FENC/SBAG/SWAL - walls and fences only."),
        "Tree": ("EXCLUDED", "Terrain; 0 buildable actors."),
    },
    "openra_ra": {
        "None": ("INF None (anchor)", "15 infantry; RA has no second infantry rung, so Flak and "
                 "Plate get no RA vote and are carried by CA and Cameo."),
        "Light": ("VEH @0.5 Scout..Light + AIR Fighter (anchor)",
                  "RULED: RA's aircraft (HELI, MH60, MIG, TRAN, YAK) literally ARE `Light`; the "
                  "air ladder is anchored Light->Fighter, Heavy->Spaceship, rest interpolated."),
        "Heavy": ("VEH @3.5 Heavy..Superheavy + AIR Spaceship + BLD heavy end (8 defences)",
                  "RULED: a source's DEFENCE armour anchors the heavy end of our building "
                  "ladder, not a named rung - our defences are Concrete 63 / Steel 27, so "
                  "picking one would overstate what RA says."),
        "Wood": ("BLD Wood (anchor)", "32 ordinary buildings."),
        "Concrete": ("BLD heavy end (with Heavy)", "Only ONE buildable actor (BRIK) - it shares "
                     "the heavy-end anchor with RA's defence armour rather than standing alone."),
        "Tree": ("EXCLUDED", "Terrain."),
    },
    "openra_td": {
        "None": ("INF None (anchor)", "7 infantry; no second rung, as RA."),
        "Light": ("VEH @0.5 Scout..Light + AIR Fighter (anchor)",
                  "TD's aircraft (HELI, ORCA, TRAN) are `Light`, as in RA. Also on 2 fences."),
        "Heavy": ("VEH @3.5 Heavy..Superheavy + AIR Spaceship (anchor)", "7 vehicles."),
        "Wood": ("BLD Wood (anchor)", "14 ordinary buildings."),
        "Concrete": ("BLD Concrete (anchor)", "6 defences - TD's defence armour IS Concrete, so "
                     "here the heavy-end anchor and Concrete coincide."),
    },
    "dta_enhanced": {
        "none": ("INF None (anchor)", "RULED: after excluding the CHECK* dummies and the two "
                 "heroes, `none` is DTA's ONLY infantry armour - 19 units. No Flak/Plate vote."),
        "light": ("VEH Scout (anchor)", "RULED: verified as exactly JEEP, BGGY, BIKE, RAIDER, "
                  "RANG - scout vehicles, not the TS building class. Enhanced assigns it; "
                  "Classic leaves it empty, which is one more reason Enhanced is canonical."),
        "medium": ("VEH Medium (anchor)", "14 vehicles - MSAM, ARTY, MLRS, STNK, DISCARTY."),
        "heavy": ("VEH Heavy (anchor) + AIR Spaceship", "22 vehicles - MTNK, HTNK, APC, LTNK. "
                  "Our Light interpolated, Superheavy extrapolated. DTA's aircraft are `heavy`."),
        "wood": ("BLD Wood (anchor)", "49 buildings once CHECKNOD (a 100 hp dummy) is dropped."),
        "concrete": ("BLD Concrete (anchor)", "0 buildable actors, but the warhead rows exist - "
                     "RULED: no abstention, use what is there."),
        "naval_light": ("ROADMAP - naval programme", "Deferred; not mapped now."),
        "naval_medium": ("ROADMAP - naval programme", "Deferred; not mapped now."),
        "naval_heavy": ("ROADMAP - naval programme", "Deferred; not mapped now."),
        "rocket": ("EXCLUDED", "RULED: projectile-interception class, not a unit armour."),
        "special": ("EXCLUDED", "RULED: engine special case."),
    },
    # ── Dune 2000, RULED 2026-09-21 ───────────────────────────────────────────────────────────
    # ⚠ THE NAMES LIE HERE MORE THAN ANYWHERE ELSE, so every row was checked against OpenRA's
    # D2K census before it was mapped. `wood` is not a building class: it is worn by the trike,
    # raider, stealth_raider, missile_tank and deviator. Mapping it by NAME would have put a
    # trike's damage profile into our building ladder.
    "d2k_mod": {
        "None": ("INF None (anchor)", "Infantry - light_inf, trooper, sardaukar, engineer, "
                 "grenadier, thumper. D2K's only infantry class."),
        "Wood": ("VEH Scout (anchor)", "RULED: follow the ACTORS, not the name - trike, raider, "
                 "stealth_raider, missile_tank, deviator. D2K's fast/light vehicles."),
        "Light": ("VEH Light (anchor) + AIR Fighter (anchor)",
                  "quad and MCV, plus D2K's aircraft (carryall, ornithopter) - the same "
                  "situation as OpenRA RA and TD, and ruled the same way."),
        "Heavy": ("VEH Heavy (anchor) + AIR Spaceship (anchor)",
                  "combat_tank x3 and devastator. Our Medium interpolates between Light "
                  "and Heavy; Bomber and Helicopter interpolate on the air ladder."),
        "Harvester": ("VEH Superheavy (anchor)", "RULED: role beats raw toughness. It measures "
                      "3rd toughest (column gmean 44.4, behind CY 25.5 and Wall 38.1), but it "
                      "is the biggest, slowest ground vehicle and that decides the ladder."),
        "Building": ("BLD Steel (anchor)", "barracks, heavy_factory, light_factory, "
                     "high_tech_factory, refinery, outpost, repair_pad - the ordinary "
                     "production buildings, so the MIDDLE building rung."),
        "CY": ("BLD Concrete (anchor)", "The Construction Yard, and the toughest class in the "
               "game (column gmean 25.5). Our heaviest building rung."),
        "Wall": ("BLD heavy end (with CY)", "RULED: KEPT, not dropped - two of its three "
                 "buildable actors are large_gun_turret and medium_gun_turret, so it is mostly "
                 "DEFENCES, and a source's defence armour anchors the heavy end of BLD. Second "
                 "toughest class at 38.1."),
        "Concrete": ("EXCLUDED", "The concrete SLAB foundation - terrain. Zero actors wear it "
                     "and it is the SOFTEST class in the table (87.4 against CY's 25.5)."),
        "Invulnerable": ("EXCLUDED", "Zero against every warhead - an all-zero COLUMN, and the "
                         "engine's cannot-be-hurt class rather than an armour rung."),
    },
    # OpenRA's Dune 2000 uses the same vocabulary in lowercase, so it takes the same mapping.
    "openra_d2k": {
        "none": ("INF None (anchor)", "As D2K_Mod."),
        "wood": ("VEH Scout (anchor)", "As D2K_Mod - trike, raider, missile_tank, deviator."),
        "light": ("VEH Light (anchor) + AIR Fighter", "quad, mcv, carryall, ornithopter."),
        "heavy": ("VEH Heavy (anchor) + AIR Spaceship", "combat_tank x3, devastator."),
        "harvester": ("VEH Superheavy (anchor)", "harvester."),
        "building": ("BLD Steel (anchor)", "The production buildings."),
        "cy": ("BLD Concrete (anchor)", "construction_yard."),
        "wall": ("BLD heavy end (with cy)", "wall + large_gun_turret + medium_gun_turret."),
        "concrete": ("EXCLUDED", "Zero actors."),
        "invulnerable": ("EXCLUDED", "Engine special case; 0 buildable actors."),
        "None": ("EXCLUDED - DEAD ROW", "⚠ CASE-DUPLICATE. OpenRA matches armour through a "
                 "case-SENSITIVE dictionary lookup and every actor declares the lowercase "
                 "spelling, so this row is written by warheads and evaluated by the engine "
                 "NEVER. Zero actors wear it."),
        "Wood": ("EXCLUDED - DEAD ROW", "Case-duplicate; 0 actors."),
        "Light": ("EXCLUDED - DEAD ROW", "Case-duplicate; 0 actors."),
        "Heavy": ("EXCLUDED - DEAD ROW", "Case-duplicate; 0 actors."),
        "Concrete": ("EXCLUDED - DEAD ROW", "Case-duplicate; 0 actors."),
    },
}
ARMOR_PROPOSAL["dta_classic"] = ARMOR_PROPOSAL["dta_enhanced"]

# Cameo's own armors need no mapping, but they do need CLASSIFYING, because five of them are not
# class armors at all and must not be fitted against a peer ladder.
CAMEO_ARMOR_KIND = {
    **{a: ("INF ladder", "DESIGN.md class armor") for a in LADDERS["INF"]},
    **{a: ("VEH ladder", "DESIGN.md class armor") for a in LADDERS["VEH"]},
    **{a: ("BLD ladder", "DESIGN.md class armor") for a in LADDERS["BLD"]},
    **{a: ("AIR ladder", "DESIGN.md class armor") for a in LADDERS["AIR"]},
    "Shield": ("NOT a class armor", "§12.0c — its own compressed [100,400] ladder."),
    "HAZMAT": ("PLATING layer", "§12.0e — selected ahead of the class row, not on the axis."),
    "COMPOSITE": ("PLATING layer", "§12.0e."),
    "BLAST": ("PLATING layer", "§12.0e."),
    "REFLECTOR": ("PLATING layer", "§12.0e."),
    "ARMOR": ("PLATING layer", "§12.0e."),
    "wall": ("DEAD ROW", "0 actors declare it — a D2K import leftover in warhead tables only."),
    "invulnerable": ("DEAD ROW", "0 actors declare it — D2K import leftover."),
    "harvester": ("DEAD ROW", "0 actors declare it — D2K import leftover."),
}

# ── The PROPOSED warhead family, from the corpus classifier ───────────────────────────────────
# Same regexes `tools/reference/survey_platforms.py` uses, kept deliberately broad: this is a
# STARTING POINT for the maintainer's ruling, not a verdict.
FAMILY_PATTERNS = [
    ("Laser/Prism", r"laser|lasr|obel|beam|prism|photon|ion"),
    ("Tesla", r"tesla|zap|bolt|electric|lightn|coil"),
    ("Flame", r"flame|fire|napalm|burn|incend"),
    ("Nuclear", r"nuke|nuclear|atom"),
    ("Chemical", r"chem|tiberium|toxin|poison|viral|bio"),
    ("MissileAA", r"\baa\b|antiair|sam\b|redeye|stinger|nike"),
    ("Missile*", r"missile|rocket|heat|dragon|sabot|tow\b|hellfire|maverick"),
    ("Cannon*", r"cannon|shell|105mm|120mm|90mm|155mm|227mm|75mm|\bap\b|\bhe\b|artillery"),
    ("Bullet", r"mg\b|machine|vulcan|gatling|carbine|rifle|minigun|chain|\bsa\b|pistol"),
    ("Demolition", r"demo|c4|bomb|grenade|mine\b"),
    ("Sonic", r"sonic|sound|wave"),
    ("Railgun", r"rail|gauss"),
    ("Melee", r"melee|claw|bite|punch|sword"),
]


def propose_family(name: str) -> str:
    low = name.lower()
    for family, pattern in FAMILY_PATTERNS:
        if re.search(pattern, low):
            return family
    return ""


# ══════════════════════════════════════════════════════════════════════════════════════════════

def _style_header(ws, row: int, ncols: int) -> None:
    for col in range(1, ncols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = HEAD_FILL
        cell.font = HEAD_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 30


def _widths(ws, widths: dict[int, int]) -> None:
    for col, width in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = width


def write_matrix_sheet(wb: Workbook, sid: str, entry: dict) -> None:
    ws = wb.create_sheet(SHEET.get(sid, sid)[:31])
    armors = entry["armors"]
    n = len(armors)

    ws["A1"] = f"{entry['label']} — warhead x armor matrix"
    ws["A1"].font = TITLE_FONT
    weighted = "usage-weighted" if entry["usage_weighted"] else "UNWEIGHTED (no usage resolved)"
    ws["A2"] = (f"Normalised so the {weighted} geometric mean of the whole matrix = 100, "
                f"so every cell is a multiplier against this mod's own average output. "
                f"Raw {weighted} gmean = {entry['denominator_raw']:.2f}. "
                f"Zeros floored at {wm.ZERO_FLOOR:g} before any log. "
                f"{len(entry['dropped'])} rows dropped (all-zero dummies / negative heals).")
    ws["A2"].font = NOTE_FONT
    ws["A3"] = ("Uses = weapon slots on BUILDABLE actors, one vote per distinct weapon per actor. "
                "Factor = row gmean / 100: 0.70 means this warhead delivers 0.7x the mod average, "
                "so a reference Damage read off it must be scaled by 0.70 to compare.")
    ws["A3"].font = NOTE_FONT

    meta = ["Warhead", "Weapon", "Warhead type", "Uses", "Profile #"]
    head_row = 5
    # Group banner
    ws.cell(row=head_row - 1, column=len(meta) + 1, value="NORMALISED  (matrix gmean = 100)")
    ws.cell(row=head_row - 1, column=len(meta) + 1).font = Font(bold=True, size=9)
    ws.cell(row=head_row - 1, column=len(meta) + n + 2, value="RAW  (as the mod writes it)")
    ws.cell(row=head_row - 1, column=len(meta) + n + 2).font = Font(bold=True, size=9)

    header = meta + armors + [""] + armors + ["GM norm", "Factor", "GM raw"]
    for i, title in enumerate(header, start=1):
        ws.cell(row=head_row, column=i, value=title)
    _style_header(ws, head_row, len(header))

    # Profile ids so identical rows are visible and collapsible by filter.
    seen: dict[tuple, int] = {}
    for row in entry["rows"]:
        key = tuple(None if v is None else round(v, 4) for v in row["values"])
        row["_pid"] = seen.setdefault(key, len(seen) + 1)

    ordered = sorted(entry["rows"], key=lambda r: (-r["uses"], r["name"].lower()))
    r = head_row + 1
    for row in ordered:
        ws.cell(row=r, column=1, value=row["name"])
        ws.cell(row=r, column=2, value=row["weapon"])
        ws.cell(row=r, column=3, value=row["warhead_type"])
        ws.cell(row=r, column=4, value=row["uses"])
        ws.cell(row=r, column=5, value=row["_pid"])
        for i, value in enumerate(row["scaled"]):
            # ⚠ N/A is not 0 and not blank-by-accident: the warhead cannot target this armour's
            # macro class, so it has no opinion. Written as the text "n/a" so a reader cannot
            # mistake it for a number, and so it never enters a spreadsheet average.
            c = ws.cell(row=r, column=len(meta) + 1 + i,
                        value="n/a" if value is None else round(value, 2))
            if value is not None:
                c.number_format = "0.0"
        for i, value in enumerate(row["values_raw"]):
            c = ws.cell(row=r, column=len(meta) + n + 2 + i,
                        value="n/a" if value is None else round(value, 2))
            if value is not None:
                c.number_format = "0.0"
        gm_norm = row["factor"] * 100.0
        ws.cell(row=r, column=len(meta) + 2 * n + 2, value=round(gm_norm, 2)).number_format = "0.0"
        ws.cell(row=r, column=len(meta) + 2 * n + 3,
                value=round(row["factor"], 4)).number_format = "0.000"
        ws.cell(row=r, column=len(meta) + 2 * n + 4,
                value=round(row["row_gmean_raw"], 2)).number_format = "0.0"
        r += 1

    first = get_column_letter(len(meta) + 1)
    last = get_column_letter(len(meta) + n)
    if r > head_row + 1:
        ws.conditional_formatting.add(
            f"{first}{head_row + 1}:{last}{r - 1}",
            ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                           mid_type="num", mid_value=100, mid_color="FFEB84",
                           end_type="num", end_value=200, end_color="63BE7B"))
    ws.freeze_panes = ws.cell(row=head_row + 1, column=len(meta) + 1)
    ws.auto_filter.ref = f"A{head_row}:{get_column_letter(len(header))}{max(r - 1, head_row)}"
    _widths(ws, {1: 34, 2: 26, 3: 22, 4: 7, 5: 9})


def write_summary(wb: Workbook, data: dict) -> None:
    ws = wb.create_sheet("Summary")
    ws["A1"] = "Sources, coverage and the normaliser"
    ws["A1"].font = TITLE_FONT
    header = ["source", "label", "armor types", "warheads", "dropped", "weapon slots",
              "raw weighted gmean", "usage weighted?", "rows with uses > 0", "distinct profiles",
              "zero floor", "floor mode"]
    for i, title in enumerate(header, start=1):
        ws.cell(row=3, column=i, value=title)
    _style_header(ws, 3, len(header))
    r = 4
    for sid, entry in data.items():
        distinct = len({tuple(None if v is None else round(v, 4) for v in row["values"])
                        for row in entry["rows"]})
        used = sum(1 for row in entry["rows"] if row["uses"] > 0)
        for i, value in enumerate([sid, entry["label"], len(entry["armors"]),
                                   len(entry["rows"]), len(entry["dropped"]),
                                   entry["total_slots"], round(entry["denominator_raw"], 2),
                                   "yes" if entry["usage_weighted"] else "NO",
                                   used, distinct,
                                   round(entry["floor"], 3), entry["floor_mode"]], start=1):
            ws.cell(row=r, column=i, value=value)
        r += 1
    _widths(ws, {1: 18, 2: 24, 3: 12, 4: 11, 5: 10, 6: 13, 7: 18, 8: 16, 9: 17, 10: 16,
                 11: 11, 12: 12})


def write_armor_map(wb: Workbook, data: dict) -> None:
    ws = wb.create_sheet("Armor_Map")
    ws["A1"] = "Every armor type of every source — and where it should land in Cameo"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = ("The PROPOSAL columns are a starting point drawn from docs/reference/"
                "peer_armor_map.yaml and from DTA's own [ArmorTypes] block. "
                "The yellow DECISION column is what binds — fill it in and it wins.")
    ws["A2"].font = NOTE_FONT
    ws["A3"] = ("'census (buildable)' counts actors a player can build; 'census (all)' includes "
                "campaign/critter/dummy actors. An armor with a 0 census that still appears in "
                "warhead tables is a DEAD ROW the mod writes against nothing.")
    ws["A3"].font = NOTE_FONT

    header = ["source", "armor tag", "census (buildable)", "census (all)",
              "warheads stating it", "RULED Cameo target", "reason", "CORRECTION"]
    for i, title in enumerate(header, start=1):
        ws.cell(row=5, column=i, value=title)
    _style_header(ws, 5, len(header))

    r = 6
    for sid, entry in data.items():
        stated: dict[str, int] = {}
        for row in entry["rows"]:
            for armor in row["stated"]:
                stated[armor] = stated.get(armor, 0) + 1
        for armor in entry["armors"]:
            if sid.startswith("cameo"):
                target, reason = CAMEO_ARMOR_KIND.get(armor, ("", "unclassified — please rule"))
            else:
                target, reason = ARMOR_PROPOSAL.get(sid, {}).get(armor, ("", "no proposal"))
            values = [sid, armor,
                      entry["armor_census"].get(armor, 0),
                      entry["armor_census_all"].get(armor, 0),
                      stated.get(armor, 0), target, reason, ""]
            for i, value in enumerate(values, start=1):
                ws.cell(row=r, column=i, value=value)
            ws.cell(row=r, column=8).fill = DECIDE_FILL
            if values[3] == 0:
                for i in range(1, 9):
                    ws.cell(row=r, column=i).font = Font(color="A03020")
            r += 1
        r += 1     # blank line between sources

    ws.freeze_panes = "A6"
    _widths(ws, {1: 18, 2: 18, 3: 18, 4: 14, 5: 19, 6: 26, 7: 72, 8: 24})


def write_warhead_map(wb: Workbook, data: dict) -> None:
    ws = wb.create_sheet("Warhead_Map")
    ws["A1"] = "Every warhead, its factor, and which Cameo family it should map to"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = ("Factor = row geometric mean / matrix geometric mean. It is the number to "
                "MULTIPLY a reference Damage by. The PROPOSED family comes from the same name "
                "regexes survey_platforms.py uses and is deliberately broad — correct it.")
    ws["A2"].font = NOTE_FONT
    header = ["source", "warhead", "weapon", "uses", "factor", "GM raw",
              "PROPOSED Cameo family", "DECISION family", "DECISION level"]
    for i, title in enumerate(header, start=1):
        ws.cell(row=4, column=i, value=title)
    _style_header(ws, 4, len(header))

    r = 5
    for sid, entry in data.items():
        if sid == "cameo_resolved":
            continue           # the template sheet is the vocabulary; 9k rows would drown this
        ordered = sorted(entry["rows"], key=lambda x: (-x["uses"], x["name"].lower()))
        for row in ordered:
            label = row["node"] if not row["weapon"] else row["name"]
            values = [sid, row["name"], row["weapon"], row["uses"],
                      round(row["factor"], 4), round(row["row_gmean_raw"], 2),
                      propose_family(label), "", ""]
            for i, value in enumerate(values, start=1):
                ws.cell(row=r, column=i, value=value)
            ws.cell(row=r, column=5).number_format = "0.000"
            ws.cell(row=r, column=8).fill = DECIDE_FILL
            ws.cell(row=r, column=9).fill = DECIDE_FILL
            r += 1
        r += 1

    ws.freeze_panes = "A5"
    ws.auto_filter.ref = f"A4:I{max(r - 1, 5)}"
    _widths(ws, {1: 18, 2: 40, 3: 26, 4: 7, 5: 9, 6: 9, 7: 22, 8: 20, 9: 16})


def write_provenance(wb: Workbook, data: dict) -> None:
    ws = wb.create_sheet("Provenance")
    ws["A1"] = "Which actor, in which weapon slot, put weight on which weapon"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = ("One row per vote. Same weapon twice on one actor (OpenRA's @GARRISONED "
                "duplicates) is listed once — see _weapon_votes in warhead_matrix.py.")
    ws["A2"].font = NOTE_FONT
    header = ["source", "actor", "slot", "weapon", "warhead (INI only)"]
    for i, title in enumerate(header, start=1):
        ws.cell(row=4, column=i, value=title)
    _style_header(ws, 4, len(header))
    r = 5
    for sid, entry in data.items():
        for slot in entry.get("slots", []):
            for i, value in enumerate([sid, slot.get("actor"), slot.get("slot"),
                                       slot.get("weapon"), slot.get("warhead", "")], start=1):
                ws.cell(row=r, column=i, value=value)
            r += 1
    ws.freeze_panes = "A5"
    ws.auto_filter.ref = f"A4:E{max(r - 1, 5)}"
    _widths(ws, {1: 18, 2: 30, 3: 26, 4: 28, 5: 24})


README_LINES = [
    ("Warhead x armor matrices — reference mods and Cameo", "title"),
    ("", ""),
    ("WHAT THIS IS", "h"),
    ("For each mod: every warhead it ships, every armor type it declares, and the full "
     "Versus matrix between them. Each matrix is normalised so the usage-weighted GEOMETRIC "
     "MEAN of the whole matrix is 100. After that normalisation the cells of the weighted "
     "matrix multiply to 1, which is the condition for composing two matrices without moving "
     "total magnitude — so the matrices are directly comparable and can be fitted together.", ""),
    ("", ""),
    ("WHY IT EXISTS", "h"),
    ("DESIGN.md §12.0 and tools/reference/aggregate_archetype.py both normalise a reference "
     "profile and state that 'absolute lethality still lives in Damage, never in the armor "
     "profile' — but nothing ever handed the discarded magnitude back to Damage. A warhead's "
     "row geometric mean is exactly what was discarded. 70 means 0.7x, and a reference Damage "
     "read off that warhead must be multiplied by 0.70 before it is comparable.", ""),
    ("", ""),
    ("RULINGS THIS IMPLEMENTS (maintainer, 2026-09-21)", "h"),
    ("1. THE 20:1 WINDOW. Every matrix is read through Cameo's own legal band — DESIGN.md "
     "§12.0 rule 4 puts every Versus value in [10, 200] about a centre of 100. Because the band "
     "is defined relative to each matrix's OWN centre it carries no units, which is what makes "
     "DTA (centre ~417) and OpenRA TD (centre ~60) comparable at all. Centre and band are "
     "mutually dependent, so they are solved as a fixpoint. Result, verified: every source lands "
     "in exactly [10, 200] with a usage-weighted geometric mean of exactly 100. An absolute "
     "floor of 1 was tried first and rejected: it is not scale-free, and it penalised DTA ~1.8x "
     "harder than Combined Arms for encoding the same idea on a x10 scale.", ""),
    ("2. Usage weight = ONE VOTE PER WEAPON SLOT on a buildable actor. Refined to one vote per "
     "DISTINCT weapon per actor, because OpenRA re-declares the same weapon as @GARRISONED and "
     "counting nodes double-weights every garrisonable infantryman.", ""),
    ("2b. DTA ENHANCED IS CANONICAL. DTA ships two rulesets; Enhance.ini layered on Rules.ini is "
     "the live one and the only one that uses DTA's `light` armor rung (14 buildable actors "
     "against 0 in Classic). DTA_Classic is a comparison sheet and must not feed the factors.", ""),
    ("3. The per-warhead row mean is FLAT across that mod's armor rows — not weighted by how "
     "common each armor is inside the mod.", ""),
    ("4. The armor mapping is NOT decided here. Every armor type of every source is listed on "
     "Armor_Map with a proposal and a blank DECISION column.", ""),
    ("", ""),
    ("WHAT IS EXCLUDED, AND WHY", "h"),
    ("All-zero dummy warheads (BioDummyWH and friends) carry no design opinion and would drag "
     "the mod mean down; they are counted on Summary as 'dropped'. Negative rows are heals "
     "(DTA writes Modifier.none=-10%), not damage multipliers, and have no logarithm.", ""),
    ("", ""),
    ("THINGS THAT WILL BITE YOU", "h"),
    ("* In OpenRA an UNSTATED armor row is 100, not absent (DamageWarhead.cs:80). Nine OpenRA TD "
     "warheads state a single row; reading only stated rows scores 'Heavy: 25' as 25 when the "
     "warhead really averages ~76.", ""),
    ("* DTA declares ELEVEN armor types with INHERITANCE — [light] BaseArmor=wood, [concrete] "
     "BaseArmor=heavy, [naval_medium] BaseArmor=medium — and per-armor defaults of 1000%. DTA's "
     "neutral is 1000%, not 100%: the whole mod runs on a x10 scale. A warhead writing four rows "
     "really resolves to eleven.", ""),
    ("* DTA's registry sections use NON-NUMERIC keys (A_01=JEEP, TD00=TDHARV). A digits-only "
     "reader returns zero vehicles out of 226 and still builds a plausible-looking matrix.", ""),
    ("* Cameo's rows are ARITHMETIC-mean-100 (DESIGN.md §12.0h), not geometric. By AM-GM every "
     "non-flat row has a geometric mean below 100, and Cameo's template matrix measures 78.7 — "
     "so the gap is real and is exactly why both sides must be re-normalised before fitting.", ""),
    ("* Five Cameo 'armors' are not class armors: Shield is its own ladder (§12.0c) and the five "
     "ALL-CAPS platings are layers (§12.0e). Three more — wall, invulnerable, harvester — are "
     "declared by ZERO actors and are D2K import leftovers. See Armor_Map.", ""),
    ("* Cameo_Resolved carries 9,179 concrete weapon warheads; Cameo carries the 161 "
     "^Warhead_* template warheads. 1,463 concrete weapons still inherit NO ^Warhead_* template "
     "(the W23/A5 retrofit backlog) and are therefore invisible to the template sheet.", ""),
    ("", ""),
    ("REGENERATE", "h"),
    ("python tools/reference/warhead_workbook.py", ""),
    ("Read-only over the mod trees. Writes this workbook only; changes no yaml, no ledger, and "
     "never regenerates ini_corpus.json.", ""),
]


def write_readme(wb: Workbook) -> None:
    ws = wb.create_sheet("README", 0)
    r = 1
    for text, kind in README_LINES:
        cell = ws.cell(row=r, column=1, value=text)
        if kind == "title":
            cell.font = Font(bold=True, size=14)
        elif kind == "h":
            cell.font = Font(bold=True, size=11, color="1F3A5F")
        else:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        r += 1
    ws.column_dimensions["A"].width = 118


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_XLSX))
    ap.add_argument("--floor", choices=("absolute", "relative", "window"), default=None,
                    help="zero-floor mode; 'relative' = 1%% of each mod's own positive "
                         "median, which removes DTA's x10-scale penalty")
    args = ap.parse_args()
    if args.floor:
        wm.FLOOR_MODE = args.floor

    data = wm.collect()
    wb = Workbook()
    wb.remove(wb.active)
    write_readme(wb)
    write_summary(wb, data)
    for sid in data:
        write_matrix_sheet(wb, sid, data[sid])
    write_armor_map(wb, data)
    write_warhead_map(wb, data)
    write_provenance(wb, data)

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(wm.summarise(data))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
