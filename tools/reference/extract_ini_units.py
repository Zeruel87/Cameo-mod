#!/usr/bin/env python3
"""extract_ini_units.py — read the Westwood/Ares INI reference mods into the peer schema.

Companion to `extract_peer_units.py`, which reads the OpenRA peers. Between them every
reference source lands in ONE schema so `assign_references.py` can treat them alike.

WHY A SECOND EXTRACTOR. The OpenRA peers are yaml with `Inherits:` chains and must be read
through `miniyaml.Ruleset`. These sources are Westwood INI: flat sections, no inheritance,
`Owner=` for faction, and armor expressed as `Verses=` (RA2/YR, 11 slots) or
`Modifier.<armor>=` (Tiberian Sun, named). Nothing about that fits the yaml resolver.

⛔ TRAPS THIS FILE EXISTS TO AVOID — each one already cost a wrong conclusion:
  * A mod's loose `rulesmd.ini` can be **vanilla Yuri's Revenge byte for byte** (Mental Omega's
    is; md5 cf7eb658327aff1fe7e6c4e7400eb87f). Harvesting it yields vanilla YR counted twice and
    zero mod data. `--verify` refuses that hash.
  * These files are NOT UTF-8. They are latin-1/cp1252 with CRLF. Decode as latin-1 so every
    byte round-trips; a UTF-8 read throws partway through several of them.
  * `Owner=` is the faction column and it is a COMMA LIST. A unit owned by six countries is six
    faction rows, not one.

Usage:
    python tools/reference/extract_ini_units.py --list
    python tools/reference/extract_ini_units.py --source "Mental Omega"
    python tools/reference/extract_ini_units.py --json docs/reference/ini_corpus.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REF = pathlib.Path.home() / "Documents" / "GitHub" / "Cameo-mod-reference" / "extraction"

# Vanilla Yuri's Revenge. Any source whose rules hash to this is not a mod at all.
VANILLA_YR_MD5 = "cf7eb658327aff1fe7e6c4e7400eb87f"

SOURCES = {
    "Rise of the East":  {"file": "rulesmd_RotE300c.ini",  "engine": "ra2"},
    "RA2 0XX":           {"file": "rulesmd_RA20XX108.ini", "engine": "ra2"},
    "Mental Omega":      {"file": "rulesmd_MO336.ini",     "engine": "ra2"},
    "CnC Reloaded":      {"file": "rulesmd_CnCR270.ini",   "engine": "ra2"},
    "Red Resurrection":  {"file": "rulesmd_RedRes2213.ini","engine": "ra2"},
    "RA2 Reborn":        {"file": "rulesmd_Reborn1031.ini","engine": "ra2"},
    "DTA Classic":       {"file": "rules_DTA_Classic.ini", "engine": "ts"},
    "DTA Enhanced":      {"file": "rules_DTA_Classic.ini", "engine": "ts",
                          "overlay": "rules_DTA_Enhance_overlay.ini"},
    # ⭐ Twisted Insurrection is the named fix for Cameo's `forgotten`: it is a Tiberian Sun mod
    # and it ships a MUTANT faction — its houses are GDI, Nod, GT, **Forsaken**, Phoenix, Sons.
    # ⚠ It declares them under `[Houses]`, not `[Countries]` like every other source here.
    "Twisted Insurrection": {"file": "rules_TwistedInsurrection.ini", "engine": "ts"},
}

# Which list section declares which unit type. `type` matches extract_peer_units' vocabulary.
TYPE_LISTS = {
    "InfantryTypes": "infantry",
    "VehicleTypes": "vehicle",
    "AircraftTypes": "aircraft",
    "BuildingTypes": "building",
}

# RA2/YR `Verses=` slot order. Fixed by the engine, not by the mod.
RA2_ARMOR = ["none", "flak", "plate", "light", "medium", "heavy",
             "wood", "steel", "concrete", "special_1", "special_2"]

SECTION = re.compile(r"^\s*\[([^\]]+)\]")
KV = re.compile(r"^\s*([A-Za-z0-9_.]+)\s*=\s*([^;]*)")


def read_ini(path: pathlib.Path) -> dict[str, dict[str, str]]:
    """{section: {key: value}}. latin-1 so every byte round-trips — these are not UTF-8."""
    out: dict[str, dict[str, str]] = {}
    cur: dict[str, str] | None = None
    for line in path.read_bytes().decode("latin-1").splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        m = SECTION.match(line)
        if m:
            cur = out.setdefault(m.group(1).strip(), {})
            continue
        if cur is None:
            continue
        m = KV.match(line)
        if m:
            cur[m.group(1).strip()] = m.group(2).strip()
    return out


def merge_overlay(base: dict, overlay: dict) -> dict:
    """DTA Enhanced = Classic + Enhance.ini, which is how the game loads it (DefaultIndex=1)."""
    out = {k: dict(v) for k, v in base.items()}
    for sec, kv in overlay.items():
        out.setdefault(sec, {}).update(kv)
    return out


def listed(ini: dict, section: str) -> list[str]:
    """A Westwood list section is `0=NAME`, `1=NAME`, ... — order is the registry order."""
    return [v.strip() for k, v in sorted(ini.get(section, {}).items(),
                                         key=lambda kv: int(kv[0]) if kv[0].isdigit() else 1 << 30)
            if v.strip()]


def num(v, default=None):
    if v is None:
        return default
    v = str(v).strip().rstrip("%")
    try:
        return float(v) if "." in v else int(v)
    except ValueError:
        return default


def versus_of(ini: dict, warhead: str, engine: str) -> tuple[dict, str]:
    """{armor: percent} for a warhead, plus which notation it came from."""
    wh = ini.get(warhead)
    if not wh:
        return {}, "missing"
    if "Verses" in wh:
        vals = [num(x, 0) for x in wh["Verses"].split(",")]
        # TS ships 5 slots, RA2/YR 11. Name them by the engine's own order; a TS file read as
        # RA2 would silently mislabel every row, which is why engine is threaded through.
        names = RA2_ARMOR if len(vals) >= 11 else ["none", "wood", "light", "concrete", "heavy"]
        return {n: v for n, v in zip(names, vals)}, "Verses"
    mods = {k.split(".", 1)[1].lower(): num(v, 0)
            for k, v in wh.items() if k.lower().startswith("modifier.")}
    if mods:
        return mods, "Modifier.*"
    return {}, "none"


def weapon_of(ini: dict, wname: str, engine: str) -> dict:
    """Scale-free numbers for one weapon, plus its warhead's armor profile."""
    w = ini.get(wname)
    if not w:
        return {"weapon": wname or None}
    dmg, rof = num(w.get("Damage")), num(w.get("ROF"))
    warhead = (w.get("Warhead") or "").strip()
    vs, notation = versus_of(ini, warhead, engine)
    return {
        "weapon": wname or None,
        "w_damage": dmg,
        "w_reload": rof,
        "w_range": num(w.get("Range")),
        "w_min_range": num(w.get("MinimumRange")),
        "w_burst": num(w.get("Burst")),
        # ROF is frames between shots; damage/ROF is the engine's own scale-free rate.
        "w_dps": (dmg / rof) if (dmg and rof) else None,
        "w_projectile": w.get("Projectile"),
        "w_warhead": warhead or None,
        "w_versus": vs or None,
        "w_versus_notation": notation,
    }


def extract(label: str, spec: dict) -> tuple[list[dict], list[str]]:
    notes: list[str] = []
    path = REF / spec["file"]
    if not path.exists():
        return [], [f"{label}: MISSING {path}"]
    digest = hashlib.md5(path.read_bytes()).hexdigest()
    if digest == VANILLA_YR_MD5:
        return [], [f"{label}: REFUSED — this file is vanilla Yuri's Revenge (md5 {digest})"]

    ini = read_ini(path)
    if spec.get("overlay"):
        ov = REF / spec["overlay"]
        if ov.exists():
            ini = merge_overlay(ini, read_ini(ov))
            notes.append(f"{label}: applied overlay {spec['overlay']}")

    engine = spec["engine"]
    # ⚠ `[Countries]` is the RA2/YR spelling; Tiberian Sun mods use `[Houses]`. Reading only the
    # first left `countries` empty for a TS source, which silently disabled the filter below
    # rather than failing — the owners were kept unvalidated. Read both.
    countries = set(listed(ini, "Countries")) | set(listed(ini, "Houses"))
    rows: list[dict] = []
    for list_sec, utype in TYPE_LISTS.items():
        for actor in listed(ini, list_sec):
            a = ini.get(actor)
            if not a:
                continue
            prim = (a.get("Primary") or "").strip()
            wep = weapon_of(ini, prim, engine) if prim else {"weapon": None}
            owners = [o.strip() for o in (a.get("Owner") or "").split(",") if o.strip()]
            rows.append({
                "source": label,
                "engine": engine,
                "id": actor,
                "name": a.get("Name") or a.get("UIName") or actor,
                "type": utype,
                # ⭐ the faction column — a comma list, and every owner is its own vote
                "faction": "/".join(o for o in owners if not countries or o in countries),
                "owners": owners,
                "hp": num(a.get("Strength")),
                "cost": num(a.get("Cost")),
                "speed": num(a.get("Speed")),
                "armor": (a.get("Armor") or "").strip() or None,
                "sight": num(a.get("Sight")),
                # ⭐ `ROT` is the Westwood rate of turn and it is the CHASSIS stat every INI
                # source was abstaining on — `reference_distribution` scores `turn_speed` and
                # `turn_ratio`, and with no ROT column all eight sources contributed nothing to
                # either. Higher is faster in both Westwood and OpenRA, and every coordinate is
                # built inside ONE source, so the two scales never have to meet.
                "turn_speed": num(a.get("ROT")),
                "turreted": (a.get("Turret") or "").strip().lower() in ("yes", "true"),
                "tech_level": num(a.get("TechLevel")),
                "prerequisite": a.get("Prerequisite"),
                "build_limit": num(a.get("BuildLimit")),
                "power": num(a.get("Power")),
                "build_time": num(a.get("BuildTimeMultiplier")),
                "secondary": (a.get("Secondary") or "").strip() or None,
                "naval": (a.get("Naval") or "").strip().lower() in ("yes", "true"),
                # ⛔ `cost > 0` IS NOT A BUILDABILITY TEST IN THESE MODS. They price internal
                # dummies at 1 credit, and the result poisons exactly the tail a distribution is
                # most sensitive to: CnC Reloaded's `TSCARRYALL_DUMMY` ("Call Carryall from the
                # sky", Selectable=no, Armor=unkillable_armor) is a costed 10,000,000 HP row
                # against a real ceiling of 6,000 — a 1,667x outlier sitting in the arithmetic
                # mean of a 443-unit population. Two of the engine's OWN flags settle it:
                #   TechLevel = -1        Westwood for "the player can never build this". It also
                #                         removes the elite/upgraded DUPLICATES these mods ship as
                #                         separate actors (RotE's `RANGER_E`, `MINDUP_E`), which
                #                         would otherwise double-count their own base unit.
                #   Selectable = no  /  IsSelectableCombatant = no
                #                         not something a player commands.
                # Measured max HP before -> after: CnCR 10,000,000 -> 6,000, RotE 15,000 -> 2,000,
                # RA2 0XX 9,999 -> 3,000, MO 6,000 -> 2,500. DTA's `civilian` roster goes to zero,
                # which is the right answer. The rows are KEPT and FLAGGED rather than dropped —
                # R6 says collect everything; the population rule belongs to the consumer.
                "buildable": not (
                    (num(a.get("TechLevel")) is not None and num(a.get("TechLevel")) < 0)
                    or (a.get("Selectable") or "").strip().lower() == "no"
                    or (a.get("IsSelectableCombatant") or "").strip().lower() == "no"),
                **wep,
            })
    for r in rows:
        # RA2 INI has no naval or defence list — ships live in VehicleTypes and turrets in
        # BuildingTypes. The maintainer's profile groups need them separated, so derive:
        #   naval   = a vehicle flagged Naval=yes
        #   defense = a building that actually carries a weapon
        if r["type"] == "vehicle" and r.get("naval"):
            r["type"] = "naval"
        elif r["type"] == "building":
            r["type"] = "defense" if r.get("weapon") else "building"
    return rows, notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", action="append", help="limit to these sources (repeatable)")
    ap.add_argument("--json", help="write the corpus to this path")
    ap.add_argument("--list", action="store_true", help="list sources and exit")
    args = ap.parse_args()

    if args.list:
        for k, v in SOURCES.items():
            mark = "OK " if (REF / v["file"]).exists() else "-- "
            print(f"  {mark}{k:<20} {v['engine']:<4} {v['file']}")
        return 0

    wanted = args.source or list(SOURCES)
    all_rows, all_notes = [], []
    for label in wanted:
        spec = SOURCES.get(label)
        if not spec:
            print(f"  unknown source {label!r}", file=sys.stderr)
            continue
        rows, notes = extract(label, spec)
        all_rows += rows
        all_notes += notes
        armed = sum(1 for r in rows if r.get("w_versus"))
        print(f"  {label:<20} {len(rows):>5} actors   "
              f"{sum(1 for r in rows if r['cost']):>5} costed   "
              f"{armed:>5} with an armor profile   "
              f"{len({f for r in rows for f in r['owners']}):>3} owners")
    for n in all_notes:
        print(f"  ! {n}")
    print(f"\n  TOTAL {len(all_rows)} rows from {len(wanted)} source(s)")

    if args.json:
        out = pathlib.Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        # One row per line: a changed unit is a one-line diff, and it greps. An indented
        # 10k-row array is neither reviewable nor small.
        lines = [
            # `buildable` is named explicitly because it is the one field whose FALSE is the
            # signal — a row that survives the filter is worth nothing without it.
            json.dumps({k: v for k, v in r.items()
                        if k == "buildable" or v not in (None, "", [])},
                       sort_keys=True, separators=(",", ":"))
            for r in all_rows
        ]
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
