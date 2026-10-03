#!/usr/bin/env python3
"""Projectile and warhead GEOMETRY from the INI sources -- a SEPARATE review corpus.

    MAINTAINER, 2026-09-12:
      "check reference data for projectile speed, acceleration and spread and falloff"
      "those should all be also collected but not automatically be applied, only after I
       review and approve them"
      "all the requested data must always be collected for every unit"
      "it's for later when we review projectiles and warhead template spread and damage
       falloff but it has NOTHING to do with the unit itself. It's a SEPARATE review process."

So this is its own corpus, keyed by PROJECTILE and by WARHEAD, not a column on the unit row.
That distinction is the design, not tidiness: a projectile is shared by dozens of weapons
across dozens of units, so hanging its geometry off one unit duplicates it and implies the
unit owns it. What the units give us is COVERAGE -- every unit's weapon slots are walked, so
every projectile and warhead any unit can actually fire is in here, with the units listed
against it. `units` and `weapons` on a record are exactly that coverage evidence.

NOTHING HERE VOTES. `reference_distribution` builds its distributions from WEAPON_STATS and
ARMOR_STATS; no field below joins either, and `reference_targets.target_for` is only ever
called on those. Wiring any of this into a unit target is a separate, deliberate approval --
which is what the maintainer reserved.

VALUES ARE VERBATIM AND UNITS DIFFER PER ENGINE. Do not average across sources and do not
convert anything without a ruling:
  * TD/TS-era warheads (DTA, Twisted Insurrection) declare `Spread` in LEPTONS --
    `DemoAtomicWH` 512, `MultiClusterWH` 48, `NukeLaunchWH` 4; 256 leptons to a cell.
  * RA2/YR-era warheads declare `CellSpread` -- `BlueJammer` 225,
    `TrueSuperIronWeaponWH` 200. Those magnitudes are NOT plain cells; Ares fixed-point
    providers are in play. Deciding what 225 means IS the review this data is collected for.
`spread_key` records which key supplied the number, so a reviewer never has to guess which
engine's units they are reading.

WHERE EACH FIELD LIVES (measured over the corpus; Mental Omega / DTA Classic):
  Speed         on the WEAPON section        1037 /  212   the authored projectile speed, so
                                                           it is recorded PER WEAPON and
                                                           collected as a SET on the projectile
  Acceleration  on the PROJECTILE section     174 /   54
  ROT           on the PROJECTILE section     213 /   80   guided-missile turn rate -- the
                                                           movement model PROJECTILE_TRAVEL.md
                                                           names as still missing
  Arcing        on the PROJECTILE section      84 /   15   qualifiers: they say whether a
  Inaccurate    on the PROJECTILE section      66 /    8   speed number describes a straight line
  CellSpread    on the WARHEAD section        537 /   10
  Spread        on the WARHEAD section           - /  139  the TD-era spelling
  PercentAtMax  on the WARHEAD section        401 /    4   damage at the blast edge; the INI
                                                           analogue of Cameo's `Falloff` tail

Reads are EXACT-CASE like every read in `extract_ini_units` -- OpenTS looks INI names up by
raw bytes, so a near-miss spelling reads as absent rather than as a value.

Usage:  python tools/reference/extract_projectile_geometry.py [--source "Mental Omega"]
Writes: docs/reference/projectile_geometry_evidence.json  (JSONL, one record per line)
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import extract_ini_units as E  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "reference" / "projectile_geometry_evidence.json"


def load_source(label: str, spec: dict):
    """The same load path `extract_ini_units.extract` uses, including the vanilla-YR refusal
    and the fail-closed overlay -- reused rather than reimplemented so the two corpora can
    never disagree about what a source says."""
    path = E.REF / spec["file"]
    if not path.exists():
        return None, label + ": MISSING " + str(path)
    if hashlib.md5(path.read_bytes()).hexdigest() == E.VANILLA_YR_MD5:
        return None, label + ": REFUSED - vanilla Yuri" + chr(39) + "s Revenge"
    ini = E.resolve_inherits(E.read_ini(path))
    digests = {path.name: E.sha256_file(path)}
    if spec.get("overlay"):
        ov = E.REF / spec["overlay"]
        if not ov.exists():
            return None, label + ": REFUSED - overlay " + spec["overlay"] + " missing"
        ini = E.merge_overlay(ini, E.resolve_inherits(E.read_ini(ov)))
        digests[ov.name] = E.sha256_file(ov)
    return (ini, digests), None


def collect(label: str, spec: dict) -> tuple[list[dict], list[str]]:
    loaded, note = load_source(label, spec)
    if loaded is None:
        return [], [note]
    ini, digests = loaded
    rows = E.extract_rows_from_ini(ini, label, spec["engine"])

    # COVERAGE comes from the units: walk every unit's weapon slots, so every projectile and
    # warhead a unit can actually fire is represented, with the units listed against it.
    proj_use = collections.defaultdict(lambda: {"units": set(), "weapons": set(),
                                                "speeds": collections.Counter()})
    wh_use = collections.defaultdict(lambda: {"units": set(), "weapons": set()})
    for r in rows:
        for wkey, pkey, hkey in (("weapon", "w_projectile", "w_warhead"),
                                 ("w2_weapon", "w2_projectile", "w2_warhead")):
            wname = (r.get(wkey) or "").strip()
            if not wname:
                continue
            w = ini.get(wname) or {}
            speed = E.num(w.get("Speed"))
            p = (r.get(pkey) or "").strip()
            h = (r.get(hkey) or "").strip()
            if p:
                u = proj_use[p]
                u["units"].add(r["id"])
                u["weapons"].add(wname)
                if speed is not None:
                    u["speeds"][speed] += 1
            if h:
                wh_use[h]["units"].add(r["id"])
                wh_use[h]["weapons"].add(wname)

    out: list[dict] = []
    for name, use in sorted(proj_use.items()):
        sec = ini.get(name) or {}
        out.append({
            "kind": "projectile", "source": label, "engine": spec["engine"], "name": name,
            "declared": bool(sec),
            "accel": E.num(sec.get("Acceleration")),
            "rot": E.num(sec.get("ROT")),
            "arcing": E.bool_value(sec.get("Arcing")),
            "inaccurate": E.bool_value(sec.get("Inaccurate")),
            # Speed is authored on the WEAPON, so one projectile legitimately has several.
            # Recorded as {speed: how many weapons} -- never averaged.
            "weapon_speeds": {str(k): v for k, v in sorted(use["speeds"].items())},
            "weapons": sorted(use["weapons"]), "units": sorted(use["units"]),
            "source_sha256": digests,
        })
    for name, use in sorted(wh_use.items()):
        sec = ini.get(name) or {}
        key = "CellSpread" if "CellSpread" in sec else ("Spread" if "Spread" in sec else None)
        out.append({
            "kind": "warhead", "source": label, "engine": spec["engine"], "name": name,
            "declared": bool(sec),
            "spread": E.num(sec.get(key)) if key else None,
            "spread_key": key,
            "falloff_pct": E.num(sec.get("PercentAtMax")),
            "weapons": sorted(use["weapons"]), "units": sorted(use["units"]),
            "source_sha256": digests,
        })
    return out, []


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", action="append",
                    help="limit to these sources (default: all of them)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)

    specs = {k: v for k, v in E.SOURCES.items()
             if not args.source or k in args.source}
    if args.source and len(specs) != len(args.source):
        print("unknown source(s):", sorted(set(args.source) - set(specs)))
        return 2

    all_rows: list[dict] = []
    notes: list[str] = []
    for label, spec in specs.items():
        rows, ns = collect(label, spec)
        notes += ns
        all_rows += rows
        p = sum(1 for r in rows if r["kind"] == "projectile")
        h = len(rows) - p
        cov_a = sum(1 for r in rows if r["kind"] == "projectile" and r["accel"] is not None)
        cov_v = sum(1 for r in rows if r["kind"] == "projectile" and r["weapon_speeds"])
        cov_s = sum(1 for r in rows if r["kind"] == "warhead" and r["spread"] is not None)
        cov_f = sum(1 for r in rows if r["kind"] == "warhead" and r["falloff_pct"] is not None)
        print("%-24s projectiles %4d (speed %4d, accel %4d)   warheads %4d (spread %4d, falloff %4d)"
              % (label, p, cov_v, cov_a, h, cov_s, cov_f))

    # A PARTIAL RUN MUST NOT OVERWRITE THE WHOLE CORPUS. Same trap as `extract_ini_units`,
    # where `--source X --json <corpus>` once replaced every other source's rows with one
    # source's. Merge by source instead, keeping untouched sources intact.
    out_path = pathlib.Path(args.out)
    keep = []
    if out_path.exists() and args.source:
        for line in out_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("source") not in specs:
                keep.append(r)
        print("kept %d rows from sources not in this run" % len(keep))
    rows = keep + all_rows
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
                        encoding="utf-8")
    print("\nwrote %d records -> %s" % (len(rows), out_path.relative_to(ROOT)))
    for n in notes:
        print("  note:", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
