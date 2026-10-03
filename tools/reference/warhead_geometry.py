#!/usr/bin/env python3
"""Blast RADIUS and damage FALLOFF for every reference weapon, joined to its Cameo family. Read-only.

Maintainer, 2026-09-23: *"find a way to not only get the versus values and the damage but also the
spread of the weapon like how big is the radius and how big is the damage falloff"*. Standing
order of 2026-09-12 still applies: this is COLLECTED FOR REVIEW, never applied automatically.

One record per weapon the warhead-family assignment knows (`warhead_groups.json`), in one common
unit so sources can be compared:

  radius_wdist   OpenRA world units (1 cell = 1024).
  falloff        damage percentages from the centre outwards, OpenRA `Falloff` form.
  basis          which source key produced it, so nothing is read on trust.

HOW EACH ENGINE IS READ
  * OpenRA sources (Combined Arms, Romanov's Vengeance, Shattered Paradise, Crystallized Nexus,
    vanilla RA/TD/TS/D2k): the main damage warhead's `Spread` and `Falloff`, resolved through
    `miniyaml` (never by hand). OpenRA places falloff point i at `i x Spread`, so the radius is
    `(N-1) x Spread` for an N-point falloff (Cameo rule 8d). An explicit `Range:` list wins.
  * RA2/YR-era INI sources: `CellSpread` in CELLS -> x1024, and `PercentAtMax` (damage at the
    edge; linear from 100 at the centre) -> falloff `[100, PercentAtMax]` (default 100 = flat).
    MEASURED, 2026-09-23: CellSpread medians are 1.0-1.5 cells and p90 3-4.5 in every RA2-era
    source, so they ARE cells. Values >= 200 (RA 20XX 255, Red Resurrection 256) are whole-map
    sentinels on superweapon / jammer effects and are reported as `map_wide`, not as a radius.
  * TD/TS-era INI sources (DTA, Twisted Insurrection) declare `Spread` - a quantity whose engine
    formula is NOT verified here (medians 3-4, max 512). It is kept VERBATIM as `raw_spread` with
    `basis: "td_spread_unverified"` and NO radius, until its meaning is established.

INI geometry is read from `projectile_geometry_evidence.json` (the 2026-09-12 corpus), keyed by
warhead name - the same names `warhead_groups.json` uses for INI sources.

    python tools/reference/warhead_geometry.py                 # per-family summary
    python tools/reference/warhead_geometry.py --write         # also writes warhead_geometry.json
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools" / "audit"))

import assignment_store as store  # noqa: E402
import warhead_matrix as wm  # noqa: E402
from miniyaml import Ruleset  # noqa: E402

GROUPS = ROOT / "docs" / "reference" / "warhead_groups.json"
INI_EVIDENCE = ROOT / "docs" / "reference" / "projectile_geometry_evidence.json"
OUT = ROOT / "docs" / "reference" / "warhead_geometry.json"
CELL = 1024
MAP_WIDE_CELLS = 200

# `projectile_geometry_evidence.json` labels sources by display name.
INI_LABEL = {
    "mental_omega": "Mental Omega", "cnc_reloaded": "CnC Reloaded", "rise_of_the_east": "Rise of the East",
    "ra20xx": "RA2 0XX", "ra2_reborn": "RA2 Reborn", "red_resurrection": "Red Resurrection",
    "twisted_insurrection": "Twisted Insurrection", "dta_enhanced": "DTA Enhanced", "dta_classic": "DTA Classic",
}


def _num(v):
    try:
        return float(str(v).strip().rstrip("%"))
    except (TypeError, ValueError):
        return None


def _wdist(v) -> float | None:
    """OpenRA WDist text ('1c512', '768', '0') -> world units."""
    if v is None:
        return None
    s = str(v).strip()
    if "c" in s:
        cells, _, rest = s.partition("c")
        try:
            return int(cells or 0) * CELL + int(rest or 0)
        except ValueError:
            return None
    return _num(s)


def ini_records() -> dict[str, dict[str, dict]]:
    out: dict[str, dict[str, dict]] = collections.defaultdict(dict)
    label_to_sid = {v: k for k, v in INI_LABEL.items()}
    for line in INI_EVIDENCE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("kind") != "warhead":
            continue
        sid = label_to_sid.get(r.get("source"))
        if sid is None:
            continue
        key, spread, pct = r.get("spread_key"), _num(r.get("spread")), _num(r.get("falloff_pct"))
        rec = {"basis": None, "radius_wdist": None, "falloff": None, "raw_spread": r.get("spread"),
               "raw_key": key, "raw_percent_at_max": r.get("falloff_pct")}
        if key == "CellSpread" and spread is not None:
            if spread >= MAP_WIDE_CELLS:
                rec["basis"] = "map_wide"
            else:
                rec["basis"] = "CellSpread_cells"
                rec["radius_wdist"] = round(spread * CELL)
                rec["falloff"] = [100.0, pct if pct is not None else 100.0]
        elif key == "Spread":
            rec["basis"] = "td_spread_unverified"
        elif key is None:
            # RA2/YR `CellSpread` defaults to 0: the warhead hits its target cell only.
            rec["basis"] = "point_default"
            rec["radius_wdist"] = 0
            rec["falloff"] = [100.0]
        out[sid][r["name"]] = rec
    return out


def openra_records(sid: str, names: set[str]) -> dict[str, dict]:
    src = next(s for s in wm.OPENRA_SOURCES if s[0] == sid)
    rs = Ruleset(src[2], src[3])
    out = {}
    for name in names:
        node = rs.resolve_weapon(name)
        if node is None:
            continue
        best = None
        for c in node.children:
            if not c.key.startswith("Warhead@"):
                continue
            dmg = _num(c.get("Damage"))
            if dmg and dmg > 0 and (best is None or dmg > best[0]):
                best = (dmg, c)
        if best is None:
            continue
        wh = best[1]
        # OpenRA's SpreadDamageWarhead defaults (engine `SpreadDamageWarhead.cs`): Spread 43 and
        # Falloff [100, 37, 14, 5, 0] - FIVE points, so an unset falloff spans 4 x Spread. An
        # earlier draft assumed "100, 0" and measured every default-falloff weapon 4x too small.
        falloff = [x for x in (_num(t) for t in (wh.get("Falloff") or "100, 37, 14, 5, 0").split(",")) if x is not None]
        explicit = wh.get("Range")
        if explicit:
            ranges = [_wdist(t) for t in explicit.split(",")]
            radius, basis = (max(r for r in ranges if r is not None) if any(ranges) else None), "Range"
        else:
            spread = _wdist(wh.get("Spread") or "43")  # OpenRA's SpreadDamageWarhead default
            radius = spread * (len(falloff) - 1) if spread is not None and len(falloff) > 1 else spread
            basis = "Spread_x_(N-1)"
        out[name] = {"basis": basis, "radius_wdist": radius, "falloff": falloff,
                     "raw_spread": wh.get("Spread"), "raw_key": wh.value}
    return out


def build() -> dict:
    groups = json.loads(GROUPS.read_text(encoding="utf-8"))
    assignments = store.load()
    ini = ini_records()
    openra_ids = {s[0] for s in wm.OPENRA_SOURCES}
    data = {}
    for sid, doc in sorted(assignments.items()):
        if sid not in groups:
            continue
        family = {}
        for g in groups[sid]["groups"]:
            row = (doc.get("groups") or {}).get(g["name"], {})
            for w in g["weapons"]:
                family[w] = row.get("family")
        for w, r in (doc.get("overrides") or {}).items():
            if w in family:
                family[w] = r.get("family")
        geo = openra_records(sid, set(family)) if sid in openra_ids else ini.get(sid, {})
        data[sid] = {w: {"family": f, **geo.get(w, {"basis": "not_found"})} for w, f in family.items()}
    return data


def cameo_radius() -> dict[str, int]:
    """Cameo's base blast radius per family, from the generator's PHYSICS_SHAPES (read-only)."""
    sys.path.insert(0, str(ROOT / "tools" / "balance"))
    try:
        import gen_weapon_template as g
    except Exception:
        return {}
    return {k: v[0] for k, v in getattr(g, "PHYSICS_SHAPES", {}).items()
            if isinstance(v, tuple) and isinstance(v[0], (int, float))}


def summary(data: dict) -> str:
    fam = collections.defaultdict(list)
    counts = collections.Counter()
    for sid, rows in data.items():
        for w, r in rows.items():
            counts[r.get("basis")] += 1
            f = r.get("family") or ""
            if f.startswith("(") or r.get("radius_wdist") is None:
                continue
            fam[f].append((r["radius_wdist"], (r.get("falloff") or [100])[-1], sid))
    cameo = cameo_radius()
    lines = [f"records by basis: {dict(counts)}", "",
             "radius in world units (1 cell = 1024); `Cameo` = today's PHYSICS_SHAPES base radius",
             f"{'family':<16}{'n':>5}{'sources':>8}{'radius p25':>12}{'median':>9}{'p75':>9}{'edge % median':>15}{'Cameo':>8}"]
    for f, v in sorted(fam.items(), key=lambda x: -len(x[1])):
        rad = sorted(x[0] for x in v)
        edge = statistics.median(x[1] for x in v)
        q = lambda p: rad[min(len(rad) - 1, int(len(rad) * p))]
        lines.append(f"{f:<16}{len(v):>5}{len({x[2] for x in v}):>8}{q(0.25):>12.0f}{statistics.median(rad):>9.0f}"
                     f"{q(0.75):>9.0f}{edge:>15.0f}{cameo.get(f, ''):>8}")
    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true", help="write docs/reference/warhead_geometry.json")
    args = ap.parse_args()
    data = build()
    print(summary(data))
    if args.write:
        OUT.write_text(json.dumps(data, indent=1, sort_keys=True, default=float) + "\n", encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
