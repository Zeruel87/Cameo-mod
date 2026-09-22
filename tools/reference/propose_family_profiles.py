#!/usr/bin/env python3
"""W13 step 3 — a proposed Versus profile for every `^Warhead_<Family>_<Level>`.

This is where the three laws meet. For each Cameo family and level:

  1. **Platform** (DESIGN.md §12.0a) picks the reference rows — a family's LEVEL
     tracks the platform tier, so `_Light` learns from infantry and small turrets
     and `_Heavy` from heavy vehicles and big defences. Pooling all "lasers"
     together mixes a rifle with an Obelisk, which is the flattening W13 exists
     to undo.
  2. **The ordering law** (`gen_weapon_template.py`) places the values: macro
     priority x light/heavy direction. The corpus supplies magnitudes, never order.
  3. **The shape law** (DESIGN.md §12.0) finishes it: peak 100, no two values
     identical, uneven steps allowed, floor 10-25 (5 only for the deliberate
     extreme), then the derived armors.

    python tools/reference/propose_family_profiles.py
    python tools/reference/propose_family_profiles.py --family Laser
    python tools/reference/propose_family_profiles.py --write

⚠ **Families with no reference coverage are reported, not invented.** Melee,
Arrow, Magic, Sonic, Nuclear and the rest have no cross-mod equivalent to learn
from — they are Cameo's own inventions — so this prints "no source" for them
rather than borrowing a neighbouring family's numbers and calling it evidence.

⚠ **KNOWN LIMITATION — compressed blocks need a DESIGN decision, not more data.**
Where the corpus does not differentiate the rungs inside a macro block, the
no-ties rule can only separate them by its minimum step, and the output looks
like `Scout 96 · Light 97 · Medium 98 · Heavy 99 · Superheavy 100`. That is
honest — the canonical `AP` warhead really is ~100 against every armoured
target, because the source games never needed to tell a medium tank from a heavy
one — but it is not a usable Cameo ladder: five rungs spanning four points is
flat in everything but the letter of the law.

Read those blocks as *"the field says: all of these are top targets"* and let the
DESIGN spread them. The corpus cannot supply a distinction it never drew, and
padding one in here would disguise a design choice as a measurement.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import aggregate_archetype as ag  # noqa: E402
import gen_weapon_template as gwt  # noqa: E402
import survey_platforms as sp  # noqa: E402

OUT = ROOT / "docs" / "reference" / "family_profiles.md"
# The FROZEN export the weapon generator consumes. It has to exist as a committed
# artifact because the corpus itself does not: `survey_platforms` traces the source
# mods' INI files out of `~/Downloads`, which nobody else has. Freezing the derived
# numbers keeps `gen_weapon_template.py` hermetic and reproducible on any clone.
OUT_JSON = ROOT / "docs" / "reference" / "family_profiles.json"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Cameo family -> (corpus family, law direction). Direction mirrors
# gen_weapon_template.py so the two cannot drift.
FAMILY_SOURCE = {
    "Bullet": ("bullet", "light"),
    "CannonHE": ("cannon", "light"),
    "CannonAP": ("cannon", "heavy"),
    "MissileHE": ("missile", "light"),
    "MissileAP": ("missile", "heavy"),
    "MissileAA": ("missile", "heavy"),
    "Laser": ("laser", "heavy"),
    "Prism": ("laser", "light"),
    "Flame": ("flame", "light"),
    "Tesla": ("tesla", "heavy"),
}
# Cameo's own inventions — no cross-mod equivalent, so no proposal is offered.
NO_SOURCE = ["Flak", "Chemical", "Melee", "Arrow", "Magic", "Demolition",
             "Concussion", "Sonic", "Railgun", "Nuclear"]

# LEVEL -> the platform tiers it learns from. A level is a statement about how
# big the weapon is, and platform is the only thing in the corpus that says so.
LEVEL_PLATFORMS = {
    "Light": ("infantry", "vehicle_light", "defense_small"),
    "Medium": ("vehicle_medium", "defense_small"),
    "Heavy": ("vehicle_heavy", "defense_big"),
    "Super": ("defense_big",),
}
# Floor by level: heavier weapons are allowed to be more specialised.
LEVEL_FLOOR = {"Light": 25, "Medium": 20, "Heavy": 15, "Super": 10}

# The law's direction word, as `survey_platforms.direction` reports it.
DIRECTION_WORD = {"light": "anti-LIGHT", "heavy": "anti-HEAVY"}
# Below this, a tier is reported as thin rather than treated as settled.
MIN_ROWS = 8
# ...and below EITHER of these it is not shipped at all — the tier inherits the
# nearest measured tier's shape instead. One mod's opinion is not a measurement,
# and the aggregate is what makes the corpus trustworthy: `MIN_ARITY_FOR_AGGREGATE`
# already refuses to average a profile that states only one armor, for exactly the
# reason that burned us on Tesla (a single-armor row normalises to 100 by
# definition and then stacks that column). The same logic applies one level up.
# Measured 2026-08-15: only `Bullet/Heavy` (n=1, mods=1) and `Flame/Heavy`
# (n=15, mods=2) fail; every other family-level has >=3 independent mods.
SHIP_MIN_ROWS = 8
SHIP_MIN_MODS = 3
# `Super` is included for the EXPORT only, never for the markdown comparison: only
# `Tesla` among the measured families has that tier, and its platform set
# (`defense_big`) is a subset of Heavy's, so it is usually thin and inherits. Left
# out, `^Warhead_Tesla_Super` silently kept the even ramp and shipped at 1.8x while
# every other Tesla level was rebuilt.
LEVEL_ORDER = ("Light", "Medium", "Heavy", "Super")

# Which aggregation the proposals use — the maintainer's blend (median + mean +
# gmean) / 3, chosen on measured behaviour across all 10 families x 3 levels:
#
#   aggregation   median span   flat blocks   AP vs None
#   median            118            8            78
#   mean              128            3            51
#   gmean             102            5            40
#   blend             112            3            52
#
# `flat blocks` counts vehicle ladders spanning under 20 - the unusable-ladder
# problem - and blend ties mean for the fewest. `AP vs None` should be LOW, since
# armour-piercing against unarmoured infantry is the anti-armour extreme, and
# blend's 52 fixes median's 78 (which contradicted AP's whole identity).
#
# ⚠ This also corrects a prediction I made: I argued gmean would produce the
# SHARPEST profiles. It produces the FLATTEST overall span (102), because pulling
# high values toward the geometric centre shrinks the top end even while it drops
# the bottom. gmean is the sharpest on any single specialised cell and the least
# sharp overall — the opposite of what I claimed, and only measuring showed it.
AGGREGATION = "blend"

# --------------------------------------------------------------------------- #
# Flat-block spreading — OPT-IN, because it is DESIGN, not measurement.
# --------------------------------------------------------------------------- #
# The corpus routinely fails to separate rungs inside a macro block: the
# canonical `AP` warhead is ~100 against every armoured target, because the
# source games never needed to tell a medium tank from a heavy one. The no-ties
# rule then separates them by its minimum step and CannonAP's vehicle block
# reads `96 · 97 · 98 · 99 · 100` — distinct, and useless.
#
# `--spread-flat-blocks` fixes that by widening any block whose internal span is
# under `MIN_BLOCK_SPAN`, redistributing its values around their own mean so the
# block keeps the POSITION the macro priority gave it while its rungs become
# readable. Nothing else moves.
#
# It is off by default on purpose. The default output is what the field says; the
# flag is Cameo choosing something the field never expressed, and the two should
# never be confused in a document someone later mines for evidence.
MIN_BLOCK_SPAN = 20.0


def spread_flat_blocks(profile: dict[str, float], order: list[str],
                       min_span: float = MIN_BLOCK_SPAN) -> dict[str, float]:
    """Widen any macro block the corpus left effectively flat.

    Operates per macro ladder, in the sequence `order` already fixed, so the
    ranking is never changed — only the spacing. The block is re-spread around
    its own mean, which keeps its centre of mass and therefore its standing
    relative to the other blocks; a block that the field placed low stays low.

    Blocks the corpus DID differentiate (span >= min_span) are left untouched,
    so real measured shape always wins over the synthetic spread.
    """
    out = dict(profile)
    for ladder in ag.CAMEO_LADDERS.values():
        present = [a for a in order if a in ladder and a in profile]
        if len(present) < 2:
            continue
        values = [profile[a] for a in present]
        span = max(values) - min(values)
        if span >= min_span:
            continue                        # the field said something; keep it
        # Anchor at the block's OWN top and widen downward. Centering on the mean
        # and spreading both ways looks fairer but pushes the upper rungs past
        # 100, where the clamp flattens them back into ties that `enforce_distinct`
        # then separates by 1 — reproducing the exact problem this exists to fix
        # (`Scout 88 · Light 93 · Medium 97 · Heavy 99 · Superheavy 100`).
        # The top of a block is also what ranks it against the other blocks, so
        # holding it fixed keeps the macro priority the field measured.
        top = max(values)
        step = min_span / (len(present) - 1)
        for i, armor in enumerate(present):
            out[armor] = round(max(1.0, top - i * step), 1)
    return out


def combine(values: list[float], how: str) -> float:
    """One number from many, four ways.

    `blend` is the maintainer's proposal — the mean of all three estimators.
    It is a real compromise rather than a fudge, because the three fail in
    DIFFERENT directions: AM-GM guarantees `gmean <= mean` always, so the pair
    brackets the answer, and the median arbitrates between them without being
    dragged by either tail. Averaging them keeps the mean's sensitivity to how far
    outliers sit while diluting it to a third, and keeps the gmean's pull toward
    sharpness without letting one near-zero source dominate.

    ⚠ Blending happens PER ARMOR, before the ordering pass. Blending finished
    profiles instead would average values that the sort had already moved onto
    different armors for different reasons.
    """
    if how == "median":
        return statistics.median(values)
    if how == "mean":
        return statistics.fmean(values)
    if how == "gmean":
        return statistics.geometric_mean([max(1.0, v) for v in values])
    if how == "blend":
        return statistics.fmean([
            statistics.median(values),
            statistics.fmean(values),
            statistics.geometric_mean([max(1.0, v) for v in values]),
        ])
    raise ValueError(how)


def rows_for(corpus_family: str, level: str) -> list[dict]:
    wanted = set(LEVEL_PLATFORMS[level])
    return [r for r in sp.survey(corpus_family) if r["platform"] in wanted]


def source_balanced_buckets(rows: list[dict]) -> dict[str, list[float]]:
    """One median per source/armor, so roster size does not weight a source twice.

    Source identifiers are not proof of independent balance lineages. Resolve
    lineage membership upstream; preserve missing armor axes as missing here.
    """
    sources = collections.defaultdict(lambda: collections.defaultdict(list))
    for row in rows:
        mapped, _ = ag.to_cameo(row["versus"])
        for armor, value in mapped.items():
            sources[row["source"]][armor].append(value)
    buckets = collections.defaultdict(list)
    for axes in sources.values():
        for armor, values in axes.items():
            buckets[armor].append(statistics.median(values))
    return dict(buckets)


def profile_for(family: str, level: str, cache: dict,
                spread: bool = False) -> tuple[dict, int, int] | None:
    corpus_family, direction = FAMILY_SOURCE[family]
    if corpus_family not in cache:
        cache[corpus_family] = sp.survey(corpus_family)
    wanted = set(LEVEL_PLATFORMS[level])
    rows = [r for r in cache[corpus_family] if r["platform"] in wanted]

    # ⚠ ROLE FILTER — maintainer: *"you need to be very careful when you compare
    # versus values from different units because we need to first make sure they
    # have the same role as in cameo."*
    #
    # The corpus family is only half the match. `cannon` covers both the infantry
    # bazooka that shreds troops and the tank gun that kills armour, and Cameo
    # splits those into CannonHE and CannonAP. Feeding every cannon row into
    # CannonAP and then REORDERING it heavy-first does not produce an anti-armour
    # weapon — it produces an anti-infantry weapon wearing an anti-armour ladder,
    # which is how `Plate` came out at 100 on a family whose whole point is that
    # infantry are a bad target for it.
    #
    # So a row only teaches a family if the row's own measured direction agrees
    # with the family's. `flat` rows are kept as neutral evidence; they carry
    # magnitude information without arguing for either direction.
    matching = [r for r in rows
                if sp.direction(r["versus"]) in (DIRECTION_WORD[direction], "flat")]
    rows = matching  # No matching role is missing evidence, not permission to invert it.
    if not rows:
        return None

    buckets = source_balanced_buckets(rows)
    # Three aggregations, so the choice is the maintainer's and not buried in code.
    # `median` is robust to one weird mod; `mean` lets every source pull
    # proportionally; `gmean` is the correct average for MULTIPLIERS (averaging x2
    # and x0.5 arithmetically invents a net buff of 1.25 — geometrically it is 1.0).
    median = {a: combine(v, AGGREGATION) for a, v in buckets.items() if v}
    if len(median) < 4:
        return None

    # ⚠ ORDER COMES FROM THE GENERATOR, not from a per-ladder sort.
    #
    # `ag.lawful_profile` sorts within each macro ladder independently, so each
    # ladder keeps its own peak — which meant `Plate` came out at 100 on
    # CannonAP, a family whose entire premise is that infantry are a poor target.
    # The macro PRIORITY (`VEH > BLD > INF > AIR`) was never applied.
    #
    # `gen_weapon_template.build_order()` already produces the full 16-armor
    # sequence from exactly that priority plus the light/heavy direction — it is
    # the ordering law in code. Reading it from there rather than re-deriving it
    # also means this tool cannot drift from the generator it feeds.
    blocks, gen_direction, _air, _levels = gwt.WEAPONS[family]
    order = gwt.build_order(blocks, gen_direction)
    values = sorted((median[a] for a in order if a in median), reverse=True)
    lawful = {a: v for a, v in zip([a for a in order if a in median], values)}
    lawful = ag.shape_profile(lawful, LEVEL_FLOOR[level])
    if spread:
        lawful = spread_flat_blocks(lawful, order)
    lawful.update(ag.derive_armors(lawful))
    lawful = ag.enforce_distinct(lawful)
    return lawful, len(rows), len({r["source"] for r in rows})


def frozen_profiles(cache: dict | None = None) -> dict:
    """The export the weapon generator consumes: family -> level -> profile.

    Two things happen here that the markdown comparison deliberately does not do,
    because this output is what SHIPS rather than what is being weighed up:

    1. **A tier too thin to be evidence inherits the nearest measured tier.**
       `Bullet/Heavy` rests on ONE row from ONE mod, which is an anecdote wearing
       a table's clothes. Inheriting `Bullet/Medium`'s shape and re-applying the
       Heavy floor is the honest answer — the level slope still differentiates it,
       and the JSON records that the tier was inherited so nobody later mines the
       number as a measurement.
    2. **Provenance travels with the values.** `n`, `mods` and `origin` sit next to
       every profile, so a reader can tell a 151-row / 8-mod consensus from a
       3-mod one without re-running a corpus they cannot reproduce.
    """
    cache = {} if cache is None else cache
    measured: dict[str, dict[str, tuple]] = {}
    for family in FAMILY_SOURCE:
        measured[family] = {}
        # Only the levels the generator actually emits for this family — asking for
        # a `Super` profile for a family that has no Super tier would freeze a row
        # nothing ever reads.
        family_levels = [lv for lv in LEVEL_ORDER if lv in gwt.WEAPONS[family][3]]
        for level in family_levels:
            payload = profile_for(family, level, cache)
            if payload is None:
                continue
            profile, n, mods = payload
            measured[family][level] = (profile, n, mods,
                                       n >= SHIP_MIN_ROWS and mods >= SHIP_MIN_MODS)

    families: dict[str, dict] = {}
    for family, levels in measured.items():
        solid = [lv for lv in LEVEL_ORDER if lv in levels and levels[lv][3]]
        out: dict[str, dict] = {}
        for level in [lv for lv in LEVEL_ORDER if lv in gwt.WEAPONS[family][3]]:
            entry = levels.get(level)
            if entry is not None and entry[3]:
                profile, n, mods, _ = entry
                origin = "measured"
            else:
                if not solid:
                    continue                     # nothing in this family to lean on
                # Nearest measured tier, by distance along Light < Medium < Heavy.
                idx = LEVEL_ORDER.index(level)
                donor = min(solid, key=lambda lv: abs(LEVEL_ORDER.index(lv) - idx))
                profile = dict(measured[family][donor][0])
                n, mods = (entry[1], entry[2]) if entry else (0, 0)
                origin = f"inherited:{donor}"
                # Re-apply THIS level's floor, then re-derive and re-separate: the
                # donor was shaped to its own floor, and the derived armors are
                # products of cells the rescale just moved.
                profile = ag.shape_profile(profile, LEVEL_FLOOR[level])
                profile.update(ag.derive_armors(profile))
                profile = ag.enforce_distinct(profile)
            out[level] = {"origin": origin, "n": n, "mods": mods,
                          "profile": {a: round(v, 1) for a, v in sorted(profile.items())}}
        if out:
            families[family] = out
    return {
        "_generated_by": "tools/reference/propose_family_profiles.py --json",
        "_aggregation": AGGREGATION,
        "_source_weighting": "median per source/armor, then one value per source; lineage independence requires upstream selection",
        "_normalisation": (
            "each source profile normalised so its MEDIAN is 100; values above 100 "
            f"are legal up to {ag.NORMALISE_CEILING:g} (K prices the profile, so a "
            "200 is paid for rather than free)"),
        "_pipeline": ("reference rows at the family's PLATFORM tier -> aggregate -> "
                      "ordering law (gen_weapon_template.build_order) -> shape law "
                      "(LEVEL_FLOOR, min gap 2) -> derived armors -> no-ties"),
        "_level_floor": LEVEL_FLOOR,
        "_ship_thresholds": {"min_rows": SHIP_MIN_ROWS, "min_mods": SHIP_MIN_MODS},
        "_derived_armors": {k: list(v) for k, v in ag.DERIVED_ARMORS.items()},
        "families": families,
    }


def render_comparison() -> str:
    """Every family x level x aggregation, so the choice can be made by eye."""
    global AGGREGATION
    lines = [
        "# W13 — proposed Versus profiles, three aggregations side by side",
        "",
        "Generated by `tools/reference/propose_family_profiles.py --write`.",
        "",
        "Pipeline per row: reference rows for that family at that PLATFORM TIER ->",
        "aggregate -> ordering law (`gen_weapon_template.build_order`) -> shape law",
        "(floor by level, min gap 2) -> derived armors (Heroic, Airborne) -> no-ties.",
        "",
        "**Normalised so the MEDIAN of each source profile is 100**, and values above",
        "100 are legal: K prices the profile now, so a 200 is paid for rather than free.",
        "",
        "| aggregation | robust to | biased by |",
        "|---|---|---|",
        "| `median` | one mod with an extreme profile | nothing — but it ignores how far out the others sit |",
        "| `mean` | nothing | a single outlier drags the cell |",
        "| `gmean` | outliers, and it is the correct average for MULTIPLIERS | sits below the mean whenever sources disagree, so a wide mean-gmean gap = disagreement |",
        "",
    ]
    for family in FAMILY_SOURCE:
        corpus_family, direction = FAMILY_SOURCE[family]
        lines += [f"## {family}  ({corpus_family}, dir={direction})", "",
                  "| level | agg | n | mods | " + " | ".join(ag.CAMEO16) + " |",
                  "|---|---|--:|--:|" + "--:|" * len(ag.CAMEO16)]
        for level in ("Light", "Medium", "Heavy"):
            for agg_name in ("median", "mean", "gmean", "blend"):
                AGGREGATION = agg_name
                payload = profile_for(family, level, {})
                if payload is None:
                    continue
                profile, n, mods = payload
                cells = ["--" if profile.get(a) is None else f"{profile[a]:g}"
                         for a in ag.CAMEO16]
                mark = "**" if agg_name == "blend" else ""
                lines.append(f"| {mark}{level}{mark} | {agg_name} | {n} | {mods} | "
                             + " | ".join(cells) + " |")
        lines.append("")
    lines += ["## No reference coverage", "",
              "Cameo inventions with no cross-mod equivalent — hand-designed, not borrowed:",
              "", "- " + ", ".join(f"`{f}`" for f in NO_SOURCE), ""]
    return chr(10).join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family", help="one family only")
    ap.add_argument("--write", action="store_true", help=f"write {OUT.relative_to(ROOT)}")
    ap.add_argument("--json", action="store_true",
                    help=f"write {OUT_JSON.relative_to(ROOT)} (the frozen export "
                         "gen_weapon_template.py consumes)")
    ap.add_argument("--aggregation", choices=("median", "mean", "gmean", "blend"),
                    default="blend", help="how to combine the reference rows")
    ap.add_argument("--spread-flat-blocks", action="store_true",
                    help="DESIGN step: widen macro blocks the corpus left flat")
    args = ap.parse_args()

    families = [args.family] if args.family else list(FAMILY_SOURCE)
    for family in families:
        if family not in FAMILY_SOURCE:
            print(f"unknown family {family}; known: {', '.join(FAMILY_SOURCE)}")
            return 1

    global AGGREGATION
    AGGREGATION = args.aggregation
    cache: dict = {}
    results: dict = {}
    for family in families:
        levels = {}
        for level in ("Light", "Medium", "Heavy"):
            levels[level] = profile_for(family, level, cache,
                                        spread=args.spread_flat_blocks)
        results[family] = levels

    for family, levels in results.items():
        print(f"\n{family}  (from `{FAMILY_SOURCE[family][0]}`, "
              f"dir={FAMILY_SOURCE[family][1]})")
        for level, payload in levels.items():
            if payload is None:
                print(f"   {level:7} no reference rows at this platform tier")
                continue
            profile, n, mods = payload
            key = ("None", "Plate", "Scout", "Light", "Medium", "Heavy",
                   "Superheavy", "Concrete", "Helicopter")
            shown = " ".join(f"{a[:4]}={profile[a]:.0f}" for a in key if a in profile)
            print(f"   {level:7} n={n:3} mods={mods}  {shown}")
    if args.write:
        OUT.write_text(render_comparison(), encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(ROOT)}")
    if args.json:
        payload = frozen_profiles(cache)
        OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        n_lv = sum(len(v) for v in payload["families"].values())
        inherited = [f"{f}/{lv}" for f, lvs in payload["families"].items()
                     for lv, d in lvs.items() if d["origin"] != "measured"]
        print(f"\nwrote {OUT_JSON.relative_to(ROOT)}: "
              f"{len(payload['families'])} families, {n_lv} family-levels"
              + (f"; inherited (too thin to ship): {', '.join(inherited)}" if inherited else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
