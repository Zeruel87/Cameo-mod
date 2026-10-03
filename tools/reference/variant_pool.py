#!/usr/bin/env python3
"""variant_pool.py — the CHASSIS VARIANTS the population rule drops, and only those.

⛔ WHY THIS EXISTS. `reference_distribution.peer_rows()` applies the maintainer's population
rule (2026-09-06, verbatim): *"Only use buildable units and no epic units with build limits!
Only unlimited units / defenses."* That rule is right for DISTRIBUTIONS — a unit nobody can
buy has no place in a ceiling or a mean. It is not automatically right for the ASSIGNMENT,
which is the same mistake the hero lane already had to correct: `peer_hero_rows()` exists
precisely because a build-limited row is excluded from the arithmetic and still wanted as a
reference.

This is the third population in that family, and the maintainer found it by eye:

    "there are some additional units from DTA that might be unbuildable ... Like I've seen a
     drone carrier and a missile humvee. Maybe useful for our promotion units?"

They are real. DTA ships `JEEPPTNK` "Rocket Hum-vee" — a Hum-vee hull carrying `APTusk`
instead of `RaiderCannon` — at TechLevel -1, so no sidebar ever offers it. Cameo ships
`td_gdi_humveemkii`. That is a counterpart, and the population rule had hidden it.

⛔ THE DANGER IS SPECIFIC AND ALREADY PAID FOR. The unbuildable band is where DTA keeps its
dinosaurs, its ants and its visceroids, and admitting it wholesale re-creates exactly the
defect `drop_unbacked_shape` was written to kill: `td_gdi_officer` drew a Triceratops and
`td_gdi_shotgunner` a Stegosaurus. So the gate below is a CONJUNCTION of ten tests, each one
excluding a population we can name, and the ones that matter are not the obvious ones:

  the faction test      critters carry no side at all. `ANT1`, `JPTREXW`, `VISC_LRG` and
                        `MINIMIG` all have `faction: None`; `JEEPPTNK` has
                        "GDI/Nod/Allies/Soviet" and `O279` has "Soviet". One field separates
                        the two populations exactly, and it is not a threshold anyone tuned.
  the base-id test      a chassis variant EXTENDS a buildable id (JEEP -> JEEPPTNK). A unit
                        nobody ships a base for is a one-off, not a variant.
  the weapon test       ⭐ THIS IS THE ONE THAT DOES THE WORK. Measured over every INI source,
                        407 rows extend a buildable id — and 294 of them carry THE SAME WEAPON
                        as their base. Those are RANK states (Rise of the East's `_E` elite
                        suffix is 74 rows on its own) and a promotion-scaling corpus, not unit
                        counterparts: pairing a Cameo unit to `SHK_E` when `SHK` is already
                        another Cameo unit's reference records the same unit twice. Requiring a
                        DIFFERENT weapon cuts 407 to 113 and is what makes this pool about
                        chassis rather than veterancy.
  the mode test         `THRASHERD` "(Deployed)", `HYDRASUB2` "(Submarine)" and `RA3APOC2`
                        "(Grinder mode)" are the SAME unit in another stance — the base row is
                        already in the pool, so admitting the stance double-counts it.
  the dummy test        `IFISTDUMMYDRONE` and `OROCHI2` carry `dummyoro2` — spawned minions
                        whose "weapon" is a placeholder. `CarrierSlave` units have no ammo pool
                        and no price anyone pays.

⚠ AI-ONLY DUPLICATES ARE NOT VARIANTS. DTA ships `AIJEEP`, `AIBFRT`, `AICTNK` and six more:
byte-identical stats to a row already in the pool, existing only so the bot can build one. They
would enter as a SECOND row for a unit already present and let one Cameo actor hold the same
reference twice under two ids — the `HTNK`/`4TNK` "two rows called Mammoth Tank" trap, in a
form the id key cannot catch.

Read-only. Writes nothing, decides nothing — `assign_references` consumes it.

    python tools/reference/variant_pool.py              # the pool, by source
    python tools/reference/variant_pool.py --source "DTA Enhanced"
    python tools/reference/variant_pool.py --rejected   # what each gate excluded, and why
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import reference_distribution as rd  # noqa: E402

INI_CORPUS = ROOT / "docs" / "reference" / "ini_corpus.json"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# The four types the assignment matches on. `building` is deliberately absent: a variant
# BUILDING is a construction state (`RAMSLOO` "Under-Construction Missile Silo"), never a unit.
UNIT_TYPES = ("infantry", "vehicle", "aircraft", "naval")

# A deploy/stance form of a row already in the pool. Matched on the NAME, which is where every
# source states it, and kept narrow on purpose — "mode" alone would eat "Mode Alpha".
MODE_RE = re.compile(r"\((?:[^)]*\b(?:deployed|submarine|mode|stance|land|sonar active|"
                     r"combat-ready|stealth mode)\b[^)]*)\)", re.I)
DUMMY_RE = re.compile(r"dummy|\bdrone\b", re.I)
# ⭐ THE RANK TEST, added after measuring the first pool. The weapon test alone cut 407 rows to
# 113 and STILL let 69 Rise of the East rows through, because RotE names a weapon PER VETERANCY
# RANK — `maraudergun` / `maraudergun2` / `maraudergun3` for Marauder Tank / (Elite) / (Heroic).
# Read as "a different weapon" those look like chassis variants and they are nothing of the kind:
# the same hull at a higher rank, which §12.0b already treats as a DERIVED column
# (Heroic = Plate x Scout / peak), never as a unit of its own. Admitting them would pair a Cameo
# unit to the ELITE FORM of a unit its neighbour already references — the same unit counted twice,
# with a veterancy multiplier baked into one of the two copies.
RANK_RE = re.compile(r"\b(?:elite|heroic|veteran|rookie|upgraded|downgraded|unused|"
                     r"upgrader|upgrade)\b|\(AI\)", re.I)
RANK_ID_RE = re.compile(r"(?:_E|_UP|_ST|AI)$", re.I)
MIN_BASE_ID = 3          # "2TNK" -> "2TNKMSL" is real; a 2-char prefix matches by accident
# ⭐ A CHASSIS SWAP DOES NOT MOVE A UNIT'S PRICE CLASS, and that turns out to be the cleanest way
# to throw out the last population the name tests cannot see: SPAWNED MINIONS. `DEST` (a 1000-odd
# credit destroyer) "extends" to `DESTPLANE` at 50, `CRFTCR` to `CRFTCRPLN` at 50, `HUMMER_N` to
# `HUMMER_N3` at cost 1 / hp 1. Those are the aircraft a carrier launches and a placeholder actor
# — priced at a rounding error because nobody ever buys one. A real variant sits beside its base:
# `JEEP` 400 -> `JEEPPTNK` 500 (1.25x), `HTNK` 1500 -> `HTNKARTY` 1700 (1.13x). The band below is
# wide enough that a genuinely cheaper or dearer variant survives and narrow enough that an
# order-of-magnitude gap does not.
#
# ⭐ IT IS A FLOOR, NOT A BAND, AND THE CORPUS DECIDED THAT — not a preference. Measured over
# every pair that reaches this gate, the two populations do not overlap and do not come close:
#
#     real variants     HTNK->HTNKARTY x1.13 · JEEP->JEEPPTNK x1.25 · TTNK->TTNKMSL x2.40
#                       2TNK->2TNKMSL x2.40 · LTNK->LTNKCRUS x2.50
#     spawned minions   DEST->DESTPLANE x0.05 · DOG->DOGGIE x0.05 · ZEP->ZEPDRONE x0.02
#                       CRFTCR->CRFTCRPLN x0.03 · HUMMER_N->HUMMER_N3 x0.00
#
# An UPPER bound is what an eye would reach for and it is exactly wrong: a Light Tank hull
# carrying a 105mm gun really does cost 2.5x the Light Tank, and my first attempt at (0.5, 2.0)
# threw out three of DTA's six — LTNKCRUS, TTNKMSL and 2TNKMSL — the artillery conversions that
# are the most interesting rows in the pool. The gap the data actually shows is BELOW: x0.05 to
# x1.13, twenty-fold and empty. So the floor sits in it and there is no ceiling.
COST_FLOOR = 0.5


def _rows():
    """Every raw INI record. ⚠ NEVER regenerate `ini_corpus.json` — a full re-run drops the
    weapon evidence on 63 rows (docs/design/REFERENCE_EXTRACTION_PLAN.md). Reading is safe."""
    return [json.loads(line) for line in
            INI_CORPUS.read_text(encoding="utf-8").splitlines() if line.strip()]


def _weapon(row):
    w = str(row.get("weapon") or "").strip().lower()
    return "" if w in ("", "none", "null") else w


def classify(rows=None):
    """(variants, rejected) — every row tested, and the FIRST gate that refused it.

    `rejected` is a Counter keyed by gate name. It is returned rather than logged because a
    population this tool silently drops is a population nobody can argue with later: the
    maintainer's question was "what ARE those", and a count per gate is the answer.
    """
    rows = _rows() if rows is None else rows
    by_source = collections.defaultdict(list)
    for r in rows:
        by_source[r.get("source")].append(r)

    # `is_ai_only`'s prefix test needs the source's own id roster to check for a sibling.
    source_ids = collections.defaultdict(set)
    for r in rows:
        source_ids[r.get("source")].add((r.get("id") or "").upper())

    variants, rejected = [], collections.Counter()
    for source, group in by_source.items():
        # The BUILDABLE roster of this source, by id — the only thing a variant may extend.
        base = {(r.get("id") or "").upper(): r for r in group
                if r.get("buildable") and not r.get("build_limit") and r.get("cost")}
        for r in group:
            rid = (r.get("id") or "").upper()
            if not r.get("cost"):
                rejected["no cost — not a priced unit"] += 1
                continue
            if r.get("build_limit"):
                rejected["build_limit — the HERO lane already carries it"] += 1
                continue
            if r.get("buildable", True):
                rejected["buildable — peer_rows() already has it"] += 1
                continue
            if r.get("type") not in UNIT_TYPES:
                rejected["not a unit type (building/defense)"] += 1
                continue
            if not r.get("faction"):
                rejected["no faction — critter, civilian or spawned minion"] += 1
                continue
            # ⛔ ASK `is_ai_only`, do not re-test the prefix here. `reference_distribution`
            # already owns this rule and owns the two corrections it took to get right: the
            # marker is a PREFIX as well as a suffix, and it is only safe to act on a prefix when
            # stripping it names a unit the source really ships (`AIHTNK2` beside `HTNK`, where
            # no `HTNK2` exists). A second implementation here would be the `allows()` mistake
            # again — a rule computed in one place and quietly skipped in another.
            if rd.is_ai_only(r, source_ids):
                rejected["AI-only duplicate of a row already in the pool"] += 1
                continue
            w = _weapon(r)
            if not w:
                rejected["unarmed — clause 5 refuses it anyway"] += 1
                continue
            name = str(r.get("name") or "")
            if MODE_RE.search(name):
                rejected["a deploy/stance form of a row already in the pool"] += 1
                continue
            # ⚠ THE ID CARRIES THE WORD THE NAME HIDES. `IFISTDUMMYDRONE`, `GRINDUMMYDRONE` and
            # `GRINSLOWDRONE` are all DISPLAYED as "Hornet" and all carry a real-looking weapon;
            # only the id says what they are. Testing name and weapon alone let all three in.
            if DUMMY_RE.search(name) or DUMMY_RE.search(w) or DUMMY_RE.search(rid):
                rejected["dummy weapon or spawned drone"] += 1
                continue
            if RANK_RE.search(name) or RANK_ID_RE.search(rid):
                rejected["a veterancy rank or an upgrade marker, not a chassis"] += 1
                continue
            cands = [b for b in base if b != rid and rid.startswith(b) and len(b) >= MIN_BASE_ID]
            if not cands:
                rejected["extends no buildable id — a one-off, not a variant"] += 1
                continue
            parent = max(cands, key=len)
            if _weapon(base[parent]) == w:
                rejected["same weapon as its base — a RANK state, not a chassis"] += 1
                continue
            bcost, vcost = base[parent].get("cost"), r.get("cost")
            if not bcost or vcost / bcost < COST_FLOOR:
                rejected["priced outside its base's class — a spawned minion or placeholder"] += 1
                continue
            variants.append({**r, "variant_of": parent,
                             "variant_base_weapon": _weapon(base[parent])})
    return variants, rejected


def _self_test():
    """Pins the five populations the gate exists to separate, on the real corpus.

    ⛔ Asserted against DTA Enhanced because the maintainer named it and because its answer is
    small enough to state exactly: SIX chassis variants, and every one of them is a real hull
    carrying another hull's weapon. A test that only checked a count would pass while the pool
    quietly filled with ants.
    """
    variants, rejected = classify()
    dta = {v["id"].upper() for v in variants if v["source"] == "DTA Enhanced"}
    want = {"JEEPPTNK", "HTNKARTY", "HTNKMSAM", "LTNKCRUS", "TTNKMSL", "2TNKMSL"}
    assert dta == want, f"DTA Enhanced chassis variants moved: {dta ^ want}"

    ids = {(v["source"], v["id"].upper()) for v in variants}
    for bad, why in (("ANT1", "an ant is a critter (no faction)"),
                     ("JPTREXW", "a dinosaur is a critter (no faction)"),
                     ("VISC_LRG", "a visceroid is a critter (no faction)"),
                     ("AIJEEP", "an AI-only duplicate"),
                     ("MINIMIG", "a spawned drone with a build limit"),
                     ("HUNTSEEK1", "a superweapon minion, extends no buildable id"),
                     ("BRIG", "build-limited — the hero lane's"),
                     ("JEEP", "buildable — peer_rows() already has it")):
        assert ("DTA Enhanced", bad) not in ids, f"{bad} must be excluded: {why}"

    jeep = [v for v in variants if v["id"].upper() == "JEEPPTNK"
            and v["source"] == "DTA Enhanced"][0]
    assert jeep["variant_of"] == "JEEP", jeep["variant_of"]
    assert jeep["variant_base_weapon"] != _weapon(jeep), "the weapon test did not apply"

    # The weapon test is the load-bearing one, so its effect is pinned as a number: without it
    # the pool is the 400-odd rows that merely extend a buildable id, most of them rank states.
    # ⚠ THESE TWO COUNTS ARE ORDER-DEPENDENT, and the order is the reason they look the way they
    # do. The rank-NAME gate runs first and absorbs 428 rows; the weapon test then uniquely
    # catches the 38 whose name says nothing (`DOGGIEBL`/`DOGGIERE` "Fiend", `SHKUP`). Before the
    # name gate existed the weapon test alone caught 289 — so reading either number as "how big
    # the rank population is" is wrong. What each assertion pins is that ITS gate still fires.
    assert rejected["a veterancy rank or an upgrade marker, not a chassis"] > 300, \
        "the rank-name gate stopped firing — Rise of the East elite rows are back in the pool"
    assert rejected["same weapon as its base — a RANK state, not a chassis"] > 20, \
        "the weapon test stopped separating — rank states whose NAME is silent are getting in"
    for bad, why in (("MARATNK2", "(Elite) is a rank, not a chassis"),
                     ("MARATNK3", "(Heroic) is a rank, not a chassis"),
                     ("SREF_UP", "an upgrade marker actor, not a unit"),
                     ("HELIXAI", "an AI-only row whose id the AI-prefix test cannot see")):
        assert ("Rise of the East", bad) not in ids, f"{bad} must be excluded: {why}"
    return variants, rejected


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", help="restrict the listing to one source")
    ap.add_argument("--rejected", action="store_true", help="show what each gate excluded")
    args = ap.parse_args()

    variants, rejected = _self_test()
    print(f"# Chassis variants the population rule drops — {len(variants)} rows\n")
    if args.rejected:
        print("## What the gates excluded\n")
        for why, n in rejected.most_common():
            print(f"  {n:6d}  {why}")
        print()

    by_source = collections.defaultdict(list)
    for v in variants:
        by_source[v["source"]].append(v)
    for source in sorted(by_source, key=lambda s: -len(by_source[s])):
        if args.source and source != args.source:
            continue
        group = by_source[source]
        print(f"## {source} — {len(group)}\n")
        for v in sorted(group, key=lambda v: -(v.get("cost") or 0)):
            print(f"  {v['variant_of']:<10} -> {v['id']:<16} {str(v.get('name'))[:34]:34s} "
                  f"{v['type']:<9} cost={str(v.get('cost')):>6} hp={str(v.get('hp')):>7}  "
                  f"{v['variant_base_weapon']} -> {_weapon(v)}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
