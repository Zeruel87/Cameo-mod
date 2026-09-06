#!/usr/bin/env python3
"""Documents 2 and 3 of the three-document program (BALANCE_SYNTHESIS §15).

PRIOR ART: `tools/reference/aggregate_archetype.py` pools ONE WEAPON CONCEPT's Versus
profile across mods (W13). This pools UNIT STATS across sources. Different axis, no overlap.
`ORIGINAL_UNITS_RAW.md` (Document 1) is the input and is not regenerated here.

    python tools/balance/synthesize_reference.py            # write both documents
    python tools/balance/synthesize_reference.py --class mbt --dry-run

WHY THIS EXISTS
---------------
The PER-UNIT APPLICATION LAW (`anchor_decisions_log.md`, maintainer 2026-07-31) has three
steps, and only the first two were ever built:

  1. set the BASELINE ACTOR of each class to its ruled stats     (step 2c)
  2. the FORMULA takes its weights from that baseline            (`fit_class`)
  3. each MEMBER's stats come from SYNTHESIS — the old Cameo values, **every relative stat
     from the cross-game/mod data-mining**, and where the unit sits relative to its baseline

Step 3 is the "massive, compute-intensive pass" the law calls *the real 'apply the class'
work*. `BALANCE_SYNTHESIS.md` §15 specifies it as three documents; §16 proves it end-to-end
on the Apocalypse Tank. Document 1 exists. Documents 2 and 3 never got written — §15 ends
with "Next: run this generation over all units (tooling)". This is that tooling.

HOW THE AVERAGE IS TAKEN (maintainer override, 2026-08-30)
--------------------------------------------------------
This supersedes §15.6.1, §15.6.3 and §15.6.4 of BALANCE_SYNTHESIS. Maintainer: *"I want
averaging across ALL the reference documents ... use every single data set and then average them
with geometric mean and also convert everything to the cameo scale first ... apocalypse tank is
in RA2 YR, Romanov's Vengeance, cnc reloaded, mental omega, combined arms and of course our
existing balancing stats so take everything into your calculations."*

  * **Every source votes once.** No vanilla-family collapse, no remake down-weighting, no
    exclusion of a source for disagreeing. The earlier build did all three and produced a
    curated consensus; the maintainer wants the full spread.
  * **Cameo's own current stat is a data point**, pooled alongside the sources rather than only
    being the thing measured against.
  * **Convert to the Cameo scale FIRST**, through each source's own basic rifleman, then pool.
  * **Geometric mean**, not median and not arithmetic. Every value is a RATIO to a rifle, and in
    ratio space the multiplicative centre is the correct one: a source running 2x high and one
    running 2x low cancel to exactly 1.0, where an arithmetic mean returns 1.25 and biases every
    target upward. It is also the only mean under which "normalize then average" and "average
    then normalize" agree — which is precisely what makes converting first safe.

⚠ WHAT THIS DOES NOT DO. It does not touch Versus or damage magnitude. §15.4 is explicit that
raw Versus is NOT comparable across sources (Westwood routinely >100, DTA ×10 again, every
OpenRA mod its own scale) and must never be numerically averaged — only a warhead's relative
ORDER carries identity, and that is `aggregate_archetype.py`'s job. HP, cost and speed are
pooled here because they normalize cleanly to a rifle.

⚠ IT WRITES NO LEDGER AND NO YAML. Output is two documents. Step 3 of the law is a design
pass and a synthesized target is a PROPOSAL for the maintainer, not an applied number.
"""
import argparse
import collections
import json
import glob
import pathlib
import re
import math
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import reference_lineages  # noqa: E402  (the shared lineage rulings — data only)

ROOT = pathlib.Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs" / "balance"
DESIGN = ROOT / "docs" / "design"
DOC1 = DESIGN / "ORIGINAL_UNITS_RAW.md"
DOC2 = DESIGN / "ORIGINAL_UNITS_NORMALIZED.md"
DOC3 = DESIGN / "SYNTHESIS_DELTA.md"

# Cameo's normalization anchor — the `scout` class spec in class_anchors.json, which IS the
# basic rifle infantryman. BALANCE_SYNTHESIS §5/§12.2: "Cameo's rifle anchor = 20000 HP = 1.00x".
RIFLE_HP, RIFLE_COST, RIFLE_SPEED = 20000, 100, 60

# ─────────────────────────────────────────────────────────────────────────────────────────────
# MAINTAINER OVERRIDE, 2026-08-30. This supersedes §15.6.1, §15.6.3 and §15.6.4.
#
#   "I want averaging across ALL the reference documents ... use every single data set and then
#    average them with geometric mean and also convert everything to the cameo scale first ...
#    apocalypse tank is in RA2 YR, Romanov's Vengeance, cnc reloaded, mental omega, combined arms
#    and of course our existing balancing stats so take everything into your calculations."
#
# The previous implementation followed §15.6 literally: it pooled the vanilla family to ONE vote,
# EXCLUDED wide-gap outliers, and took a MEDIAN. That is now retired. Every source votes once,
# nothing is down-weighted for being a remake, no source is dropped for disagreeing, Cameo's own
# current value is itself a data point, and the average is GEOMETRIC.
#
# Why geometric is the right mean here, not a nicety: every value is a RATIO to a rifle. In ratio
# space the natural centre is multiplicative — a source running 2x high and one running 2x low
# should cancel exactly, and only the geometric mean does that (sqrt(2 * 0.5) = 1, while the
# arithmetic mean gives 1.25 and silently biases every target upward). It is also the only mean
# for which "normalize then average" and "average then normalize" agree, which is what makes
# converting to the Cameo scale FIRST safe.
# ─────────────────────────────────────────────────────────────────────────────────────────────

# The ONE exclusion that survives the override, and it is not a judgement about balance:
# Document 1 contains junk rows. `Virus` is listed at 114,514 HP = 558.6x rifle — a joke number,
# on a row carrying no weapon at all — and left in it proposed an 11,172,000 HP target. A
# geometric mean resists it better than an arithmetic one but still cannot survive it. Pass
# --include-junk to switch this off and see the raw pool.
MAX_XRIFLE = 60.0

# A reference name must be at least this long to match by prefix.
MIN_KEY = 4

# ── The reference corpus ──────────────────────────────────────────────────────────────────────
# Two documents hold per-unit source stats, and they cover different games. Everything is
# converted to Cameo's scale through each source's OWN basic rifleman before anything is pooled
# (§15.6.2), because the sources do not share a power level: Romanov's Vengeance runs a 12,500 HP
# rifle, Combined Arms 5,000, Shattered Paradise 15,000, Mental Omega ~205, vanilla RA2 125.
#
# DOC1 = ORIGINAL_UNITS_RAW.md — 1,021 rows, five RA2-family sources, and it already carries a
#        per-row `×rifle` column so its HP needs no anchor here.
# DOC4 = ORIGINAL_UNIT_STATS.md — the wider corpus: StarCraft, Warcraft 2, Red Alert 1, Tiberian
#        Dawn, Tiberian Sun + Firestorm, RA2 + Yuri's Revenge, and DTA. Its tables are per-game
#        with differing columns, so each section declares its own rifle anchor and cost rule.
#
# ⚠ Combined Arms and Shattered Paradise are in ORIGINAL_UNIT_STATS.md but only as ROLE BANDS
# ("basic rifle 5000", "heavy trooper 7500-9000"), never as per-unit rows, so they cannot vote on
# a named unit. The single CA per-unit figure anywhere in the tree is the Apocalypse at 130,000 HP
# quoted in BALANCE_SYNTHESIS §16, and it is prose, not a dataset. CA_ROLE_BANDS below carries the
# role table so the gap is visible rather than silently absent.
DOC4 = DESIGN / "ORIGINAL_UNIT_STATS.md"

# DOC5 = ORIGINAL_UNITS_PEER_OPENRA.md — Combined Arms and Shattered Paradise, extracted per-unit
# from their own checkouts by `tools/reference/extract_peer_units.py` through the resolver. Before
# it existed these two could not vote on any named unit: the older documents carry them as ROLE
# BANDS only. Its rows already carry `×rifle`, each against that mod's own verified anchor
# (CA `E1` = 5,000 HP, SP `E1` = 12,500 HP).
DOC5 = DESIGN / "ORIGINAL_UNITS_PEER_OPENRA.md"

# ⚠ THE SAME MOD MUST NOT VOTE TWICE, AND NEITHER MAY THE SAME ROSTER.
# ⛔ MAINTAINER ORDER 2026-09-03, superseding the "no collapsing" note on `pool()` below for
# DUPLICATES specifically: *"All data needs to be unique and then used as a geometric mean for the
# design."* The 2026-08-30 override was about not curating away sources that DISAGREE; it was never
# a licence for one roster to cast five votes. Both now hold: a disagreeing source keeps its vote,
# a duplicate roster does not.
#
# Measured before applying (`tools/balance/lineage_dedup.py`): the RA2 lineage casts a MEDIAN 50%
# of all votes on the 128 multi-source units it touches, and an outright MAJORITY on 45 of them.
# Collapsing it to one vote moves the synthesized HP target by more than 10% on 52% of those units,
# by more than 25% on 29, and by up to 1.77x.
#
# The rulings themselves are in `reference_lineages.py` — one list, read by this module,
# `reference_distribution.py` and `lineage_dedup.py`, because three private copies is what produced
# a member label (`"RA2/YR"`) that matched no source and silently never collapsed.
SUPERSEDED = reference_lineages.superseded_map()

# Reported, not merged: same underlying game, different extraction, and MEASURABLY not a copy.
# ⭐ Tiberian Dawn ~ OpenRA TD agrees on only 41% of shared units and Red Alert 1 ~ OpenRA RA on
# 35% — OpenRA rebalances TD and RA1 as it ports them, so both keep a vote. It does NOT rebalance
# TS (96%), which is why TS is a lineage and these are not.
NEAR_DUPLICATES = reference_lineages.NEAR_DUPLICATES

# section heading prefix -> (source label, rifle HP, rifle cost, cost rule)
# cost rule: "direct" = credits already; "sc" = 4*minerals + 8*vespene; "wc" = 4*gold + 8*wood
DOC4_SOURCES = [
    ("## StarCraft: Brood War",      "StarCraft BW",      40,   200, "sc"),
    ("## Warcraft 2",                "Warcraft 2",        60,  2400, "wc"),
    ("## Red Alert 1",               "Red Alert 1",       50,   100, "direct"),
    ("## Tiberian Dawn",             "Tiberian Dawn",     50,   100, "direct"),
    ("## Tiberian Sun",              "Tiberian Sun",     125,    50, "direct"),
    ("## Red Alert 2 + Yuri",        "RA2/YR (raw INI)", 125,   100, "direct"),
    ("## Dawn of the Tiberium Age",  "DTA",               50,   100, "direct"),
]

# §15.5, VERIFIED against the ledger: StarCraft `credits = 4*minerals + 8*vespene` fits Wraith
# 150/100 -> 1400, Battlecruiser 400/300 -> 4000 and Science Vessel 100/225 -> 2200 exactly.
# Warcraft's `4*gold + 8*wood` is by symmetry and is flagged as unverified in the output.


def norm(name):
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def parse_doc1():
    """[(source, {column: cell})] from Document 1."""
    rows, source, header = [], None, None
    for line in DOC1.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            source = line[3:].split("(")[0].strip()
            continue
        if not line.startswith("|") or "---" in line:
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if cells and cells[0] == "Unit":
            header = cells
            continue
        if header and len(cells) == len(header):
            rows.append((source, dict(zip(header, cells))))
    return rows


def num(cell):
    if cell is None:
        return None
    s = str(cell).strip().strip("`*").split()[0] if str(cell).strip() else ""
    s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def rifle_of(rows, source):
    """Each source's own rifle stats, for §15.6.2 per-source normalization.

    Document 1 already carries `×rifle` for HP, but not for cost or speed, so those are
    normalized here against the source's own basic rifleman — found by the row whose ×rifle
    is 1.0, which is how Document 1 defines the anchor for that source.
    """
    best = None
    for src, r in rows:
        if src != source:
            continue
        if abs((num(r.get("×rifle")) or 0) - 1.0) < 1e-9:
            cost, spd = num(r.get("Cost")), num(r.get("Spd"))
            if cost and spd:
                best = {"cost": cost, "speed": spd}
                break
    return best


def parse_doc4():
    """[(source, unit, hp, cost, speed)] from ORIGINAL_UNIT_STATS.md.

    Its tables are per-game with different columns — StarCraft prints `Cost m/g`, Warcraft
    `Gold/Wood`, the Westwood games plain `Cost` — so the header row is read per table rather
    than assumed, and each section declares its own rifle anchor in DOC4_SOURCES.
    """
    if not DOC4.exists():
        return []
    out, source, anchor, header = [], None, None, None
    lines = DOC4.read_text(encoding="utf-8").splitlines()
    for line in lines:
        if line.startswith("## "):
            source = anchor = None
            for prefix, label, rhp, rcost, rule in DOC4_SOURCES:
                if line.startswith(prefix):
                    source, anchor = label, (rhp, rcost, rule)
                    break
            header = None
            continue
        if not source or not line.startswith("|"):
            continue
        cells = [c.strip().strip("*") for c in line.split("|")[1:-1]]
        if not cells:
            continue
        low = [c.lower() for c in cells]
        if "unit" in low[0] or "/" in cells[0] and "hp" in " ".join(low):
            header = low
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        if not header or len(cells) != len(header):
            continue
        row = dict(zip(header, cells))
        unit = cells[0].split("(")[0].split("/")[0].strip()
        hp = num(row.get("hp"))
        rhp, rcost, rule = anchor
        cost = None
        if rule == "sc" or rule == "wc":
            raw = row.get("cost m/g") or row.get("gold/wood") or ""
            parts = re.split(r"[/]", raw)
            if len(parts) == 2:
                a, b = num(parts[0]), num(parts[1])
                if a is not None and b is not None:
                    cost = 4 * a + 8 * b
        else:
            cost = num(row.get("cost"))
        spd = num(row.get("spd") or row.get("speed"))
        if unit and hp:
            out.append({"source": source, "unit": unit,
                        "x_hp": hp / rhp,
                        "hp": hp / rhp * RIFLE_HP,
                        "x_cost": (cost / rcost) if cost else None,
                        "cost": (cost / rcost * RIFLE_COST) if cost else None,
                        "x_speed": None, "speed": None, "raw_speed": spd,
                        "role": row.get("role", "") or row.get("weapon", ""),
                        "kind": "", "category": ""})
    return out


def parse_doc5():
    """[(row)] from ORIGINAL_UNITS_PEER_OPENRA.md — the two OpenRA peer crossovers."""
    if not DOC5.exists():
        return []
    out, source, header = [], None, None
    for line in DOC5.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            source = line[3:].split("(")[0].strip()
            header = None
            continue
        if not source or not line.startswith("|"):
            continue
        cells = [c.strip().strip("`") for c in line.split("|")[1:-1]]
        if not cells:
            continue
        if cells[0].lower() == "id":
            header = [c.lower() for c in cells]
            continue
        if set("".join(cells)) <= set("-: ") or not header or len(cells) != len(header):
            continue
        row = dict(zip(header, cells))
        xhp, xcost = num(row.get("×rifle")), num(row.get("×rifle cost"))
        if not xhp:
            continue
        out.append({"source": source, "unit": row.get("unit") or row.get("id"),
                    "kind": "", "role": "", "category": "",
                    "x_hp": xhp, "hp": xhp * RIFLE_HP,
                    "x_cost": xcost, "cost": (xcost * RIFLE_COST) if xcost else None,
                    "x_speed": None, "speed": None})
    return out


def geometric_mean(values):
    """The multiplicative centre of a set of ratios.

    Every value pooled here is a ratio to a rifle, and in ratio space the arithmetic mean is
    simply the wrong operator: a source running 2x high and one running 2x low should cancel to
    1.0, and only the geometric mean does that — the arithmetic mean returns 1.25 and biases
    every target upward. It is also the only mean under which "convert to the Cameo scale, then
    average" and "average, then convert" agree, which is what makes converting first safe.
    """
    vals = [v for v in values if v and v > 0]
    if not vals:
        return None
    return math.exp(sum(math.log(v) for v in vals) / len(vals))


def pool(per_source, key):
    """Every source votes once. No collapsing, no exclusions, no down-weighting.

    MAINTAINER OVERRIDE 2026-08-30 — this replaces §15.6's vanilla-family collapse, its outlier
    exclusion and its median. A remake now votes like any other source and a disagreeing source
    is kept, because the maintainer wants the full spread represented rather than a curated one.

    ⚠ NARROWED 2026-09-03, AND THE TWO RULES DO NOT CONFLICT. "No collapsing" is about not
    curating away sources that DISAGREE; it was never a licence for one ROSTER to cast five votes.
    De-duplication now happens upstream of here, at row level against `SUPERSEDED`, so by the time
    a vote reaches this function every source in it is a distinct roster. This function still does
    no collapsing of its own — that is the point, and it is why the dedup is visible in `main()`'s
    output rather than buried in the mean.
    """
    return {s: v[key] for s, v in per_source.items() if v.get(key)}


def load_roster():
    """{actor: record} plus {actor: class} over every ledger."""
    units, cls = {}, {}
    for f in sorted(glob.glob(str(LEDGER / "*.json"))):
        if "class_anchors" in f:
            continue
        try:
            doc = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        except ValueError:
            continue
        for sec in (doc.get("sections") or {}).values():
            if not isinstance(sec, dict):
                continue
            for name, rec in sec.items():
                if isinstance(rec, dict) and "cost" in rec:
                    units[name] = rec
                    ca = (rec.get("design") or {}).get("class_anchor")
                    if ca:
                        cls[name] = ca
    return units, cls


def val(rec, field):
    slot = rec.get(field)
    if isinstance(slot, dict):
        return num(slot.get("v"))
    return num(slot)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--class", dest="cls", help="restrict Document 3 to one class")
    ap.add_argument("--dry-run", action="store_true", help="report, write nothing")
    ap.add_argument("--include-junk", action="store_true",
                    help="keep source rows above the %gx-rifle sanity ceiling (see MAX_XRIFLE)"
                         % MAX_XRIFLE)
    args = ap.parse_args()

    rows = parse_doc1()
    sources = sorted({s for s, _ in rows})
    rifles = {s: rifle_of(rows, s) for s in sources}

    # ---- Document 2: every (unit x source) row on Cameo's scale
    norm_rows, junk = [], []
    for src, r in rows:
        xr = num(r.get("×rifle"))
        if xr and xr > MAX_XRIFLE and not args.include_junk:
            junk.append(f"{src}: {r.get('Unit')} at {xr:.1f}x rifle")
            continue
        rf = rifles.get(src) or {}
        cost, spd = num(r.get("Cost")), num(r.get("Spd"))
        norm_rows.append({
            "source": src, "unit": r.get("Unit", ""), "kind": r.get("kind", ""),
            "x_hp": xr,
            "hp": (xr * RIFLE_HP) if xr else None,
            "x_cost": (cost / rf["cost"]) if (cost and rf.get("cost")) else None,
            "cost": (cost / rf["cost"] * RIFLE_COST) if (cost and rf.get("cost")) else None,
            "x_speed": (spd / rf["speed"]) if (spd and rf.get("speed")) else None,
            "speed": (spd / rf["speed"] * RIFLE_SPEED) if (spd and rf.get("speed")) else None,
            "role": r.get("Role", ""), "category": r.get("**Category**", ""),
        })

    # ---- pool the same unit across sources
    doc4 = parse_doc4() + parse_doc5()
    present = {r["source"] for r in doc4}
    dropped_dupes = {}
    for r in doc4:
        if r["x_hp"] and r["x_hp"] > MAX_XRIFLE and not args.include_junk:
            junk.append(f"{r['source']}: {r['unit']} at {r['x_hp']:.1f}x rifle")
            continue
        norm_rows.append(r)
    # drop a superseded source only when the thing that supersedes it is actually present
    kept = []
    for r in norm_rows:
        winner = SUPERSEDED.get(r["source"])
        if winner and winner in present:
            dropped_dupes[r["source"]] = winner
            continue
        kept.append(r)
    norm_rows = kept
    sources = sorted({r["source"] for r in norm_rows})

    # A reference name matches an actor when it is a PREFIX of the actor's last segment.
    # Exact equality was too strict and it broke the spec's own worked example: the vanilla,
    # CnC Reloaded and Romanov's Vengeance rows are all named "Apocalypse" while the Cameo actor
    # is `ra2_soviets_apocalypsetank`, so §16's three 6.4x votes were never pooled and the target
    # came only from the two rows that happen to be spelled "Apocalypse Tank". Prefix in this
    # direction — reference ⊆ actor — also keeps the pooling honest the other way: "Apocalypse
    # Prototype" and "Virus Boss Brute" are NOT prefixes of "apocalypsetank"/"virus", so a
    # differently-named unit cannot leak into another unit's vote.
    by_ref = collections.defaultdict(lambda: collections.defaultdict(dict))
    units, classes = load_roster()
    actor_key = {a: norm(a.split("_")[-1]) for a in units}
    ref_names = sorted({norm(nr["unit"]) for nr in norm_rows if len(norm(nr["unit"])) >= MIN_KEY})
    for actor, akey in actor_key.items():
        for rn in ref_names:
            if akey.startswith(rn):
                for nr in norm_rows:
                    if norm(nr["unit"]) == rn:
                        by_ref[actor][nr["source"]].setdefault(rn, nr)

    synth = []
    for actor, per_src in sorted(by_ref.items()):
        # one row per source: if a source names the concept twice, take its median vote
        per_source = {}
        for src, named in per_src.items():
            picks = list(named.values())
            per_source[src] = dict(picks[0])
            for stat in ("hp", "cost", "speed"):
                vals = [p[stat] for p in picks if p.get(stat)]
                per_source[src][stat] = statistics.median(vals) if vals else None
        # MAINTAINER ORDER: "and of course our existing balancing stats" — Cameo's own current
        # value is a data point in the pool, not merely the thing measured against. It votes once,
        # like every other source, which is why a unit with a single reference row still moves
        # only halfway toward it rather than snapping to it.
        rec_now = units[actor]
        per_source["Cameo (current)"] = {
            "unit": actor, "kind": "", "role": "", "category": "",
            "hp": val(rec_now, "hp"), "cost": val(rec_now, "cost"),
            "speed": val(rec_now, "speed"),
            "x_hp": (val(rec_now, "hp") or 0) / RIFLE_HP or None,
            "x_cost": None, "x_speed": None,
        }
        key = actor_key[actor]
        actors = [actor]
        targets, contributors = {}, {}
        for stat in ("hp", "cost", "speed"):
            votes = pool(per_source, stat)
            targets[stat] = geometric_mean(votes.values())
            contributors[stat] = votes
        for actor in actors:
            rec = units[actor]
            synth.append({
                "actor": actor, "key": key,
                "unit": next(iter(per_source.values()))["unit"],
                "class": classes.get(actor, ""),
                "sources": sorted(per_source),
                "targets": targets, "contributors": contributors,
                "now": {"hp": val(rec, "hp"), "cost": val(rec, "cost"),
                        "speed": val(rec, "speed")},
            })

    matched = [s for s in synth if s["class"]]
    if args.cls:
        matched = [s for s in matched if s["class"] == args.cls]

    print(f"Document 1 rows      : {len(rows)} across {len(sources)} sources")
    print(f"junk rows dropped    : {len(junk)}" + (f"  ({junk[0]})" if junk else ""))
    for old, new in dropped_dupes.items():
        # Two different reasons, and printing one label for both hides which rule fired: an
        # EXTRACT is the same mod extracted twice, a LINEAGE is a different mod that is the same
        # roster. Only the first is a no-op; the second adopts the representative's rebalance.
        why = ("same mod, live checkout wins"
               if old in reference_lineages.SUPERSEDED_EXTRACTS else
               "one vote per lineage — see reference_lineages.py")
        print(f"superseded           : {old!r} -> {new!r} ({why})")
    print(f"matched to the roster: {len(synth)}  (class-tagged: {len(matched)})")

    if args.dry_run:
        for s in sorted(matched, key=lambda r: r["class"])[:25]:
            t, n = s["targets"], s["now"]
            print(f"  {s['class']:<18} {s['actor']:<34} "
                  f"hp {n['hp'] or 0:>9,.0f} -> {t['hp'] or 0:>9,.0f}   "
                  f"cost {n['cost'] or 0:>6,.0f} -> {t['cost'] or 0:>6,.0f}")
        return 0

    write_doc2(norm_rows, sources)
    write_doc3(synth, matched, sources)
    print(f"wrote {DOC2.relative_to(ROOT)} and {DOC3.relative_to(ROOT)}")
    return 0


def _f(v, spec=",.0f"):
    return format(v, spec) if isinstance(v, float) else "—"


def write_doc2(norm_rows, sources):
    out = ["# Document 2 — Original units, NORMALIZED to Cameo's scale", "",
           "_AUTO-GENERATED by `tools/balance/synthesize_reference.py` from "
           "[`ORIGINAL_UNITS_RAW.md`](ORIGINAL_UNITS_RAW.md) (Document 1). "
           "Spec: [`BALANCE_SYNTHESIS.md`](BALANCE_SYNTHESIS.md) §15.2. Do not hand-edit._", "",
           "Every source unit with each stat put on **Cameo's** scale, so a source unit and a "
           "Cameo unit can be read in the same column. The anchor is the basic rifleman: "
           f"**{RIFLE_HP:,} HP / {RIFLE_COST} credits / speed {RIFLE_SPEED}** — the `scout` class "
           "spec in `class_anchors.json`.", "",
           "Each source is normalized to **its own** rifle first (§15.6.2): the sources do not "
           "share a scale — Romanov's Vengeance runs a 12,500 HP rifle, Mental Omega 205, "
           "vanilla RA2 125 — so an un-normalized comparison between them is meaningless.", "",
           "⚠ **No damage or Versus column, deliberately.** §15.4: raw Versus is not comparable "
           "across sources and must never be numerically averaged; only a warhead's relative "
           "ORDER carries identity. That is `tools/reference/aggregate_archetype.py`'s job.", ""]
    for src in sources:
        rs = [r for r in norm_rows if r["source"] == src]
        rf = "yes" if any(r["x_cost"] for r in rs) else "**no rifle row found — HP only**"
        out += [f"## {src}  ({len(rs)} units · cost/speed normalized: {rf})", "",
                "| unit | kind | ×rifle HP | HP (Cameo) | ×rifle cost | cost (Cameo) | "
                "×rifle spd | spd (Cameo) | role |",
                "|---|---|--:|--:|--:|--:|--:|--:|---|"]
        for r in sorted(rs, key=lambda x: -(x["x_hp"] or 0)):
            out.append(f"| {r['unit']} | {r['kind']} | {_f(r['x_hp'], '.2f')} | "
                       f"{_f(r['hp'])} | {_f(r['x_cost'], '.2f')} | {_f(r['cost'])} | "
                       f"{_f(r['x_speed'], '.2f')} | {_f(r['speed'], '.0f')} | {r['role']} |")
        out.append("")
    DOC2.write_text("\n".join(out) + "\n", encoding="utf-8")


def write_doc3(synth, matched, sources):
    out = ["# Document 3 — Synthesis and delta", "",
           "_AUTO-GENERATED by `tools/balance/synthesize_reference.py`. "
           "Spec: [`BALANCE_SYNTHESIS.md`](BALANCE_SYNTHESIS.md) §15.3, worked end-to-end on the "
           "Apocalypse Tank in §16. Do not hand-edit._", "",
           "**This is step 3 of the PER-UNIT APPLICATION LAW** (`anchor_decisions_log.md`, "
           "maintainer 2026-07-31): the class baseline actor is set by step 2c and the formula "
           "takes its weights from it, but each MEMBER's stats come from *synthesis* — the "
           "cross-game reference, not a copy of the baseline's ratios. The law's stated goal is "
           "**more uniqueness between units of a class**, so these targets are deliberately a "
           "SPREAD, not a convergence.", "",
           "⚠ **PROPOSALS, not applied numbers.** Nothing here is written to a ledger or to yaml. "
           "A synthesized target is an input to the maintainer's judgement (§15.6.4: *\"the "
           "compromise is a judgement, not a mean\"*), and pricing still runs through "
           "`fit_class` → sign-off → `apply_balance --confirm` → boot gate.", "",
           "## How each target is reached", "",
           "**Maintainer override, 2026-08-30 — this supersedes §15.6.1, §15.6.3 and §15.6.4.** "
           "The previous build pooled the vanilla family to one vote, excluded wide-gap outliers "
           "and took a median; that produced a *curated* consensus. The instruction is to use "
           "every dataset, include Cameo's own stats, convert to the Cameo scale first, and take "
           "a **geometric mean**.", "",
           "1. Every source is converted to **Cameo's scale first**, through its own basic "
           "rifleman — the sources do not share a power level (Romanov's Vengeance runs a 12,500 "
           "HP rifle, Combined Arms 5,000, Shattered Paradise 15,000, Mental Omega ~205, vanilla "
           "RA2 125, Cameo 20,000), so an un-normalized comparison is meaningless.",
           "2. **Every source votes once.** No family collapse, no remake down-weighting, no "
           "exclusion for disagreeing.",
           "3. **Cameo's own current value is one of the votes**, not merely the thing measured "
           "against — so a unit with a single reference row moves halfway toward it, never snaps.",
           "4. The target is the **geometric mean** of the votes. Every value is a ratio to a "
           "rifle, and in ratio space the multiplicative centre is the correct one: a source "
           "running 2× high and one running 2× low cancel to exactly 1.0, where an arithmetic "
           "mean returns 1.25 and biases every target upward. It is also the only mean under "
           "which *normalize-then-average* and *average-then-normalize* agree, which is what "
           "makes converting to the Cameo scale first safe.", "",
           f"The one surviving exclusion is not a balance judgement: source rows above "
           f"**{MAX_XRIFLE:.0f}× rifle** are dropped as data errors (Document 1 lists `Virus` at "
           "114,514 HP = 558.6× — a joke number on a row with no weapon). `--include-junk` "
           "disables it.", ""]

    n_multi = sum(1 for s in matched if len(s["contributors"].get("hp") or {}) > 1)
    out += ["## Coverage", "",
            f"* Document 1 sources: **{len(sources)}** — {', '.join(sources)}",
            f"* reference units matched to a Cameo actor: **{len(synth)}**",
            f"* of those, carrying a class tag: **{len(matched)}**",
            f"* pooling two or more independent HP votes: **{n_multi}**", "",
            "The pool draws on **two** documents: `ORIGINAL_UNITS_RAW.md` (the five RA2-family "
            "sources, which already carry a per-row ×rifle column) and `ORIGINAL_UNIT_STATS.md` "
            "(StarCraft, Warcraft 2, Red Alert 1, Tiberian Dawn, Tiberian Sun + Firestorm, the "
            "raw RA2/YR INIs, and DTA). StarCraft and Warcraft costs use §15.5's conversion — "
            "`credits = 4×minerals + 8×vespene`, VERIFIED to three exact fits; the Warcraft "
            "`4×gold + 8×wood` is by symmetry and is **not** independently verified.", "",
            "✅ **The OpenRA peer crossovers now vote per-unit.** They used to appear "
            "only as ROLE BANDS (*\"basic rifle 5000\"*, *\"heavy trooper 7500–9000\"*), so they "
            "could not be matched to a named actor; `tools/reference/extract_peer_units.py` now "
            "reads their own checkouts through `miniyaml.Ruleset` and emits "
            "`ORIGINAL_UNITS_PEER_OPENRA.md` — **2,568 units across fifteen OpenRA mods**, "
            "every one cloned from its own repository and read through the resolver: Romanov's "
            "Vengeance 729, Combined Arms 382, Shattered Paradise 306, Valiant Shades 163, "
            "Generals Alpha 153, Yuri's Revenge on OpenRA 124, OpenHV 115, Crystallized Nexus "
            "97, OpenRA Red Alert 94, OpenRA RA2 86, OpenE2140 84, Tiberian Sun 74, Tiberian "
            "Dawn 56, Dune 2000 56, Dune II 49. Anchors are verified against the checkout, not "
            "trusted from a document: CA `E1` = **5,000 HP** (matches what was documented), SP "
            "`E1` (Light Infantry) = **12,500** — `ORIGINAL_UNIT_STATS.md` said 15,000, and the "
            "checkout wins — and CN `GASOL` (Marine) = **125**, a classic-Westwood-sized scale "
            "which is exactly why per-mod rifle normalization is not optional.", "",
            "⚠ **Crystallized Nexus needed its own health trait.** CN ships `CNHealth` instead of "
            "`Health`, so a reader hardcoding `Health` finds 610 actors and **zero** with hit "
            "points — an empty result that reads like *\"this mod has no data\"* rather than like "
            "a bug. Each peer now declares which traits carry its stats.", "",
            "⚠ **Sources that cover the same underlying game, kept separate on purpose.** "
            + "; ".join("/".join(f"`{x}`" for x in grp) for grp in NEAR_DUPLICATES)
            + ". A game and its OpenRA re-implementation are not the same balance — OpenRA "
            "rebalances as it ports — so both keep a vote and the overlap is reported rather "
            "than resolved. **Exact** duplicates are merged instead: Romanov's Vengeance was in "
            "the pool twice, as a Document 1 hand-extract and as a live clone, and the two "
            "agreed exactly (Apocalypse 6.4× in both), which is what proved them one source. "
            "The live checkout wins.", "",
            "⛔ **Fractured Realms (`Logue-Yne/Fractured-Realms`) cannot vote, and that is a "
            "finding rather than a missing extraction.** It resolves cleanly — 488 actors, 191 "
            "weapons — but only **23** actors carry both `Health` and `Valued`, and **18 of those "
            "are buildings** (walls, gates, power plants, a forge). What is left is a dozer, a "
            "transport ship, an MCV, one bomber and one scout. There is no basic rifleman, so "
            "there is nothing to normalize against, and inventing an anchor would fabricate every "
            "ratio derived from it. Last pushed 2023-10; it reads as an early prototype rather "
            "than a balanced mod. It stays declared in `extract_peer_units.py` so the check "
            "re-runs automatically if it ever grows a roster.", "",
            "That extraction also confirms a number that had only ever been prose: "
            "`BALANCE_SYNTHESIS.md` §16 cites CA's Apocalypse at 130,000 HP = 26× rifle. CA's "
            "`APOC` resolves to exactly **130,000**, and 130,000 / 5,000 = **26.0×**.", "",
            "⚠ **`versus_raw.json` holds 16 sources — including Combined Arms, all three DTA "
            "variants, Shattered Paradise, RA2 Reborn and Red Resurrection — but it carries "
            "WARHEAD/Versus rows only, no unit HP, cost or speed.** It cannot feed this pool. It "
            "is the right corpus for weapon identity (`aggregate_archetype.py`), the wrong one "
            "for unit stats.", ""]

    for cls in sorted({s["class"] for s in matched}):
        rs = [s for s in matched if s["class"] == cls]
        out += [f"## `{cls}` — {len(rs)} member(s) with reference data", "",
                "| actor | source unit | HP now | HP target | Δ HP | cost now | "
                "cost target | Δ cost | sources pooled for HP |",
                "|---|---|--:|--:|--:|--:|--:|--:|---|"]
        for s in sorted(rs, key=lambda r: r["actor"]):
            t, n = s["targets"], s["now"]
            dhp = (t["hp"] - n["hp"]) if (t["hp"] and n["hp"]) else None
            dc = (t["cost"] - n["cost"]) if (t["cost"] and n["cost"]) else None
            votes = s["contributors"].get("hp") or {}
            o = ", ".join(f"{k} {v / RIFLE_HP:.1f}×" for k, v in sorted(votes.items())) or "—"
            out.append(f"| `{s['actor']}` | {s['unit']} | "
                       f"{_f(n['hp'])} | {_f(t['hp'])} | {_f(dhp, '+,.0f')} | "
                       f"{_f(n['cost'])} | {_f(t['cost'])} | {_f(dc, '+,.0f')} | {o} |")
        out.append("")

    ranked = sorted((s for s in matched if s["targets"]["hp"] and s["now"]["hp"]),
                    key=lambda s: -abs(s["targets"]["hp"] / s["now"]["hp"] - 1))
    out += ["## Ranked — how far each Cameo unit sits from its synthesized HP target", "",
            "The §15.3 payoff report. A large gap is not automatically a defect: Cameo "
            "deliberately allows more spread than the tight sources (§12.4), and a unit may have "
            "been moved on purpose. It is a list of places where the reference and the roster "
            "disagree enough to deserve a look.", "",
            "| # | actor | class | HP now | HP target | ratio |", "|--:|---|---|--:|--:|--:|"]
    for i, s in enumerate(ranked[:60], 1):
        r = s["targets"]["hp"] / s["now"]["hp"]
        out.append(f"| {i} | `{s['actor']}` | `{s['class']}` | {_f(s['now']['hp'])} | "
                   f"{_f(s['targets']['hp'])} | {r:.2f}× |")
    out.append("")
    DOC3.write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
