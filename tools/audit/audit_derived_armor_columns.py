#!/usr/bin/env python3
"""audit_derived_armor_columns.py — every Versus table must carry the DESIGN §12.0l derived rows.

A unit that wears a derived armour type (`CyborgLight`, `AntiAirVehicle`, `ShipHeavy`, …) is hit
for a flat 100% by any weapon whose table lacks that row — the engine answers an absent row with
100. The generator writes the rows into every table it emits; `derive_versus_columns.py` writes
them into the rest (hand-kept templates, legacy inline-Versus weapons).

This audit counts the rows STILL MISSING or WRONG, per file, using the tool's own planner, so the
two can never disagree. LOWER-ONLY ratchet: it may only fall. It must reach 0 before any unit is
moved onto a derived type (DESIGN §12.0l order of work, step 3).

Fix: `python tools/balance/derive_versus_columns.py --files <your weapon files> --write`
(idempotent; each lane runs it on its own files).
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))
import miniyaml  # noqa: E402
import derive_versus_columns as D  # noqa: E402

# Measured 2026-09-26 after weapons/weapons.yaml was written (30,445 -> 27,944), then RE-PINNED
# once to 30,229 the same day because the MEASURE grew, not the debt: the maintainer added a
# 13th derived column (`Airborne` = geomean of Scout, Flak, Helicopter), so every pack table owes
# one more row. That is the only legitimate raise — a new column ruled into §12.0l. LOWER ONLY.
# 2026-09-27: re-landing #523/#532 onto master after #534 found 24 NEW pack tables (#534's folds)
# without the rows; the rows were written into exactly those tables (312), which lowered it.
# 2026-09-27b: post-#516 merge — the merged pack tables' derived rows were written
# (2,886 rows across 15 files: only tables whose pending count grew vs ccfd7830a);
# the merges also cleared 923 pre-existing pending rows. Landing: 29,592.
# 2026-09-29: the two rule-3b submarine columns joined GEO_DERIVED and the tool wrote EVERY
# pending row in all 42 weapon files (35,123, purely additive; the 754 template rows came from
# `splice_templates.py --all`). Landing: 0 — from here any table without its rows fails.
RATCHET = 0


def main() -> int:
    rs = miniyaml.Ruleset(ROOT)
    man = miniyaml.load_manifest(ROOT)
    rows = []
    for entry in man.weapons:
        p = pathlib.Path(str(entry))
        p = p if p.is_absolute() else ROOT / p
        if not p.exists():
            continue
        n = len(D.plan_file(rs, p))
        if n:
            rows.append((p.relative_to(ROOT).as_posix(), n))
    total = sum(n for _, n in rows)
    print("# audit_derived_armor_columns — DESIGN §12.0l derived rows in every Versus table\n")
    print(f"missing or wrong derived rows: **{total}** (ratchet {RATCHET})\n")
    if rows:
        print("| file | rows |\n|---|--:|")
        for f, n in sorted(rows, key=lambda r: -r[1]):
            print(f"| `{f}` | {n} |")
        print("\nFix: `python tools/balance/derive_versus_columns.py --files <file> --write`")
    if total > RATCHET:
        print(f"\n**FAIL** — {total} > ratchet {RATCHET}: a new table was written without the "
              "derived rows. Run the tool on it; never raise the ratchet.")
        return 1
    if total < RATCHET:
        print(f"\n**PASS** — below the ratchet; lower RATCHET to {total}.")
    else:
        print("\n**PASS** — at the ratchet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
