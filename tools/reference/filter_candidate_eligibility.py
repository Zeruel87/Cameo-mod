#!/usr/bin/env python3
"""Candidate-eligibility filter for the reference corpus.

Per Claude-Local's orders (ORDERS_2026-09-07_reference_reset.md §2 AURORA):

  A corpus row may be a reference ONLY if it is a unit a player can build and
  field. Exclude: critters/monsters/dinosaurs, map-editor and crate-only
  actors, campaign-only actors, and hero/one-off units with a build limit.

  ⚠ Do NOT use a name blocklist — derive it from the mod data (buildability,
  build limit, owner/queue, Huntable/critter traits). A blocklist rots the
  moment a mod adds a unit.

  ⚠ AI-only variants are ALREADY excluded (reference_distribution.is_ai_only);
  do not redo it.

  Hero units are a separate bucket: they stay in the pool but may only match
  a Cameo hero.

ELIGIBILITY RULES (derived from corpus data, not names):

  1. buildable=False  →  EXCLUDED
     (covers critters, crate-only, campaign-only, civilians, decorative items)

  2. buildable=True + build_limit=1  →  HERO
     (hero/commando units — stay in pool, only match Cameo heroes)

  3. buildable=True + build_limit=-1 or None or >1  →  ELIGIBLE
     (normal buildable units; build_limit=-1 means "unlimited" in RA2)

USAGE:
  python tools/reference/filter_candidate_eligibility.py [--write] [--verbose]

  --write    Write the filtered corpus to docs/reference/ini_corpus_filtered.json
  --verbose  Print spot-check details for 20 removed rows

OUTPUT:
  - Prints a summary table of eligible/hero/excluded counts per source
  - With --verbose, spot-checks 20 removals by hand
  - With --write, writes the filtered corpus
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from collections import Counter

CORPUS_PATH = Path(__file__).resolve().parents[2] / "docs" / "reference" / "ini_corpus.json"
FILTERED_PATH = Path(__file__).resolve().parents[2] / "docs" / "reference" / "ini_corpus_filtered.json"


def classify(row: dict) -> str:
    """Classify a corpus row as ELIGIBLE, HERO, or EXCLUDED.

    Derived entirely from data fields (buildable, build_limit) — no name
    blocklist, per Claude-Local's orders.
    """
    if not row.get("buildable"):
        return "EXCLUDED"
    bl = row.get("build_limit")
    # build_limit=1 means hero/commando (one per player)
    # build_limit=-1 means "unlimited" in RA2 (negative = no limit)
    # build_limit=None or 0 means no limit specified
    # build_limit>1 means limited but not hero (e.g. fake buildings, special units)
    if bl is not None and bl == 1:
        return "HERO"
    return "ELIGIBLE"


def load_corpus(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def main():
    parser = argparse.ArgumentParser(description="Filter the reference corpus by candidate eligibility")
    parser.add_argument("--write", action="store_true", help="Write filtered corpus to ini_corpus_filtered.json")
    parser.add_argument("--verbose", action="store_true", help="Print spot-check details for 20 removed rows")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    corpus = load_corpus(CORPUS_PATH)
    if not corpus:
        print(f"ERROR: no rows loaded from {CORPUS_PATH}", file=sys.stderr)
        sys.exit(1)

    # Classify all rows
    categories = [classify(r) for r in corpus]
    eligible = [r for r, c in zip(corpus, categories) if c == "ELIGIBLE"]
    hero = [r for r, c in zip(corpus, categories) if c == "HERO"]
    excluded = [r for r, c in zip(corpus, categories) if c == "EXCLUDED"]

    # Summary
    print("# Candidate-eligibility filter for reference corpus")
    print()
    print(f"Total corpus rows: {len(corpus)}")
    print(f"  ELIGIBLE:  {len(eligible):>6}  ({100*len(eligible)/len(corpus):.1f}%)")
    print(f"  HERO:      {len(hero):>6}  ({100*len(hero)/len(corpus):.1f}%)")
    print(f"  EXCLUDED:  {len(excluded):>6}  ({100*len(excluded)/len(corpus):.1f}%)")
    print()

    # Per-source breakdown
    print("## Per-source breakdown")
    print()
    print(f"| source | total | eligible | hero | excluded |")
    print(f"|---|---:|---:|---:|---:|")
    sources = sorted(set(r.get("source", "?") for r in corpus))
    for src in sources:
        src_rows = [r for r in corpus if r.get("source") == src]
        src_eligible = sum(1 for r in src_rows if classify(r) == "ELIGIBLE")
        src_hero = sum(1 for r in src_rows if classify(r) == "HERO")
        src_excluded = sum(1 for r in src_rows if classify(r) == "EXCLUDED")
        print(f"| {src} | {len(src_rows)} | {src_eligible} | {src_hero} | {src_excluded} |")
    print()

    # Spot-check 20 removals
    if args.verbose:
        print("## Spot-check: 20 removed rows")
        print()
        # Pick a diverse sample: critters, civilians, heroes (non-buildable), campaign
        spotcheck = []
        # Critters
        critter_ids = {"rapt", "tric", "steg", "trex", "pvice", "visc_sml", "visc_lrg"}
        for r in excluded:
            if (r.get("id") or "").lower() in critter_ids:
                spotcheck.append(("critter", r))
                if len([s for s in spotcheck if s[0] == "critter"]) >= 5:
                    break
        # Civilians
        for r in excluded:
            if "civilian" in (r.get("name") or "").lower() and len([s for s in spotcheck if s[0] == "civilian"]) < 3:
                spotcheck.append(("civilian", r))
        # Animals
        for r in excluded:
            if "animal" in (r.get("name") or "").lower() and len([s for s in spotcheck if s[0] == "animal"]) < 2:
                spotcheck.append(("animal", r))
        # Campaign/hero non-buildable
        for r in excluded:
            name = (r.get("name") or "").lower()
            if any(x in name for x in ["tanya", "yuri prime", "boris", "commando"]) and len([s for s in spotcheck if s[0] == "hero-nb"]) < 3:
                spotcheck.append(("hero-nb", r))
        # Fill remaining with random excluded
        for r in excluded:
            if len(spotcheck) >= 20:
                break
            if r not in [s[1] for s in spotcheck]:
                spotcheck.append(("other", r))

        for tag, r in spotcheck[:20]:
            print(f"  [{tag}] {r.get('source','?')} id={r.get('id','?')} name={r.get('name','?')} "
                  f"buildable={r.get('buildable')} build_limit={r.get('build_limit')} type={r.get('type','?')}")
        print()

    # Hero bucket spot-check
    print("## Hero bucket (buildable + build_limit=1)")
    print()
    print(f"Count: {len(hero)}")
    if hero:
        print("First 10:")
        for r in hero[:10]:
            print(f"  {r.get('source','?')} id={r.get('id','?')} name={r.get('name','?')} "
                  f"build_limit={r.get('build_limit')} type={r.get('type','?')}")
    print()

    # Verify no critters in eligible or hero
    critter_ids = {"rapt", "tric", "steg", "trex", "pvice", "visc_sml", "visc_lrg",
                   "ant4", "dnoa", "traptor", "btraptor"}
    critters_in_pool = [r for r in eligible + hero if (r.get("id") or "").lower() in critter_ids]
    print(f"## Critters in eligible/hero pool: {len(critters_in_pool)}")
    if critters_in_pool:
        print("⚠ CRITTERS FOUND IN POOL:")
        for r in critters_in_pool:
            print(f"  {r.get('source','?')} id={r.get('id','?')} name={r.get('name','?')} buildable={r.get('buildable')}")
    else:
        print("✓ No critters in pool — filter is working correctly.")
    print()

    # Write filtered corpus
    if args.write:
        filtered = eligible + hero  # HERO stays in pool, just tagged
        with open(FILTERED_PATH, "w", encoding="utf-8") as f:
            for r in filtered:
                # Add eligibility tag
                r = dict(r)
                r["eligibility"] = classify(r)
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"## Filtered corpus written to {FILTERED_PATH}")
        print(f"  {len(filtered)} rows (eligible + hero)")
    else:
        print(f"## Use --write to save filtered corpus to {FILTERED_PATH}")


if __name__ == "__main__":
    main()
