#!/usr/bin/env python3
"""class_membership.py — THE one map from a unit's TEMPLATE to its balance CLASS.

PRIOR ART: `tools/audit/audit_class_templates.py` asks whether each buildable actor carries
EXACTLY ONE `Inherits@Template:` — a structural yes/no, and it never says which balance CLASS a
template belongs to. `tools/audit/audit_infantry_class_bands.py` asks whether a banded infantry
unit sits inside its FORMULA_V2 §6b range band, over four classes. `tools/balance/anchor_readiness.py`
CONSUMES `design.class_anchor` raw — it is one of the readers this module exists to feed, not a
duplicate of it. The real prior art is the THREE incomplete, mutually disagreeing copies of this
map inside `propose_class_rebalance.py`, `build_workbook.py` and `update_ranges.py`; consolidating
them is the entire point of this file.
"""

# ⛔ PRIORITY 0, item 1 (maintainer order 2026-09-02): "Finish all the class anchors." This module
# is what unblocks it, and the reason it was blocked is here rather than in any one anchor.
#
# ⭐ THE DIAGNOSIS. `anchor_readiness.py` reports 8 of 27 anchors signed and 336 of 1870 buildable
# units tagged (18%), so every anchor is fitted against 18% of its own population and 17 of 27
# anchors are not members of the class they anchor. That is not 1,534 missing hand-tags. The ledger
# already carries `design.subtype` -- the ^<Name>Template the actor inherits, RE-DERIVED FROM YAML
# on every extract, over all 2,099 rows. The class was always derivable. What was missing was a
# complete map from the template to the class.
#
# ⛔ AND THERE WERE THREE INCOMPLETE COPIES OF THAT MAP, WHICH DISAGREED:
#     propose_class_rebalance.py   17 entries -- the infantry set
#     build_workbook.py             5 entries
#     update_ranges.py              5 entries
# The two 5-entry copies know nothing about grenadier, mortar, heavy_infantry, melee, either
# sniper class, archer, support, commando or flying_infantry, and NONE of the three knows a single
# ground VEHICLE class -- though the ledger's own hand-tags map thirteen of them one-to-one.
#
# ⛔ AND ALL THREE CARRY A LIVE BUG: `linebreaker -> mbt`. `line_breaker` is its own class in
# class_anchors.json and the ledger tags 30 of 31 members `line_breaker`. The workbook and the
# range tool have been folding 40 line-breakers into the MBT population.
#
# ⚠ THE CONSUMERS THAT MATTER MOST NEVER CALLED ANY OF THEM. anchor_readiness, fit_class,
# check_band and band_granularity read `design.class_anchor` RAW, which is why the anchor board
# reads 18% while propose_class_rebalance sees far more. The 18% is a property of the READER.
#
#   python tools/balance/class_membership.py            # coverage report
#   python tools/balance/class_membership.py --gaps     # only what still has no class
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs" / "balance"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------------------
# THE MAP. subtype (the ^<Name>Template stem) -> class_anchors.json key.
#
# ⚠ EVIDENCE, NOT INVENTION. Every entry is either (a) confirmed by the existing hand tags, with
# the support count in the comment -- "28/28" means all 28 hand-tagged members of that subtype
# already carry that class -- or (b) a name identity so exact that inventing it is not possible
# (^ArcherInfantryTemplate -> archer). Where the hand tags DISAGREE the comment says so and the
# structural reading wins, because the hand tag is the drifted copy; that is the whole finding.
# ---------------------------------------------------------------------------
SUBTYPE_TO_CLASS: dict[str, str] = {
    # --- ground vehicles: the hand tags are effectively unanimous ------------------------------
    "mainbattletank": "mbt",                    # 42/43
    "artillery": "artillery",                   # 28/28
    "hightechtank": "high_tech_tank",           # 26/26
    "epicvehicle": "epic_vehicle",              # 24/24
    "lighttank": "light_tank",                  # 16/16
    "artillerytank": "artillery_tank",          # 14/14
    "missilevehicle": "missile_vehicle",        # 13/13
    "antiairvehicle": "anti_air_vehicle",       # 13/13
    "tankdestroyer": "tank_destroyer",          # 5/5
    "dreadnought": "dreadnought",               # 5/5
    "scoutvehicle": "scout_vehicle",            # 28/29
    "firesupport": "fire_support",              # 30/31
    # ⛔ THE CORRECTION. All three older copies said `mbt`. `line_breaker` is one of the 27
    # classes and the ledger tags 30 of 31 members `line_breaker`; folding them into MBT
    # inflated that population by 40 units in the workbook and the range tool.
    "linebreaker": "line_breaker",              # 30/31 -- was wrongly `mbt`
    "supportvehicle": "support",                # 1/1; support is ability-priced (FORMULA_V2 §6b)

    # --- infantry -----------------------------------------------------------------------------
    "scoutinfantry": "scout",
    "closecombatinfantry": "closecombat",       # 3/3
    "specialforcesinfantry": "special_forces",  # 3/3
    "heavyinfantry": "heavy_infantry",
    "meleeinfantry": "melee",
    "dog": "melee",                             # 4/4 -- ^DogTemplate inherits ^MeleeInfantryTemplate
    "grenadierinfantry": "grenadier",
    "mortarinfantry": "mortar",
    "sniperinfantry": "pure_sniper",
    "heavysniperinfantry": "heavy_sniper",
    "archerinfantry": "archer",
    "rockettrooperinfantry": "rocket_trooper",
    "supportinfantry": "support",
    "heroinfantry": "commando",
    "flyinginfantry": "flying_infantry",
    "medic": "support",                         # 3/3
    "mechanic": "support",                      # 2/2
    # ⚠ PROVISIONAL, and the biggest single judgement here: 43 units. The 2026-07-21 split
    # designed ^AntiTankAntiAirInfantryTemplate out of existence, into rocket_trooper + archer +
    # special_forces, and was never applied. The hand tags on its 10 tagged members split four
    # ways (special_forces 4, archer 3, support 2, heavy_sniper 1) -- that split showing through.
    # `rocket_trooper` is the majority destination and matches propose_class_rebalance. NOT a
    # ruling; see docs/design/CLASS_MOVES.md.
    "antitankantiairinfantry": "rocket_trooper",
}

# ⛔ NOT A CLASS: extract_stats.SECTION_DEFAULT_SUBTYPE. An actor lands here when it inherits NO
# role template at all, which is exactly PRIORITY 0 item 2. Mapping these to a class would launder
# a template defect into a fake tag. Counted, never mapped.
NO_TEMPLATE = {"infantry", "vehicle", "aircraft", "ship", "misc", "unclassified"}

# Not units at all. The balance classes are about UNITS, so these leave the coverage denominator
# rather than counting as failures.
NOT_A_UNIT = {
    "building", "basicdefense", "advanceddefense", "defense", "antiairdefense", "superdefense",
    "bunker", "researchedupgrade", "promotionupgrade", "unitupgrade", "techupgrade", "doctrine",
    "teamupgrade", "upgrade", "promotion", "faction",
}

# ⛔ THE REAL GAP, and it is a DESIGN question rather than a mapping one: class_anchors.json holds
# 27 classes and NOT ONE of them is an air or a naval class. These are real units with real
# templates and no class to belong to, so the pipeline cannot price them at all. Enumerated so the
# gap is not rediscovered; each needs a maintainer ruling before it can become a map entry.
NEEDS_A_NEW_CLASS = {
    "helicopter": "air",
    "unarmedtransporthelicopter": "air -- a sub-template of ^HelicopterTemplate",
    "bomber": "air",
    "fighter": "air",
    "spaceship": "air",
    "scoutship": "naval",
    "artilleryship": "naval",
    "battleship": "naval",
    "harvester": "economy -- FORMULA_V2 §6c does not cover it",
}


def _norm(subtype) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", str(subtype or "")).casefold()


# ── Stat-identical variants, folded into their parent (maintainer 2026-09-03) ─────────────────
# *"If they are some sort of weird duplicate then only the main unit should be counted and the
#   duplicates are counted as the same as the main variant ... since they just inherited the main
#   variant it doesn't make sense to give them different stats."*
#
# THE TEST, and it is mechanical rather than a judgement: does the variant OVERRIDE any balance
# trait of the actor it inherits — Health, Valued, Mobile, Aircraft, Armor, Armament, Turreted,
# RevealsShroud, Attack*, Cargo, Passenger? If it overrides none, it cannot differ from its parent
# and is the parent under another name. Measured over the buildable roster: 45 actors inherit
# another actor, 37 override at least one balance trait and stay distinct, and these 8 do not.
#
# ⚠ THIS IS A COUNTING RULE, NOT A DELETION. The actors stay in the game and in the ledger; they
# simply stop being counted as separate members of a class, because a class is a PRICING archetype
# and there is only one thing here to price.
# ⚠ Re-derive rather than trust: `tools/balance/assign_references.py` recomputes the override set
# from the resolved rules, so a variant that later gains its own stats leaves this list by itself.
FOLD_INTO_PARENT = {
    "ts_gdi_engineer": "TSENGINEER",
    "ts_nod_engineer": "TSENGINEER",
    "forgotten_engineer": "TSENGINEER",
    "ts_gdi_lightinfantry": "TSE1",
    "wc2_humans_elvenranger": "wc2_humans_elvenarcher",
    "wc2_orcs_trollberserker": "wc2_orcs_trollaxethrower",
    "forgotten_tiberiumspike": "OILB.TS",
    "zerg_creepcolony_defense": "zerg_creepcolony",
}


def fold(actor):
    """The actor a stat-identical variant should be COUNTED AS. Identity for everything else."""
    return FOLD_INTO_PARENT.get(actor, actor)


def is_folded(actor):
    """True when this actor is a duplicate that another actor already represents."""
    return actor in FOLD_INTO_PARENT


def subtype_to_anchor(subtype) -> str | None:
    """The class a template implies, or None when nothing legitimately maps.

    None means one of three DIFFERENT things, and `classify` reports which: the actor has no
    template (PRIORITY 0 item 2), its template's class does not exist yet (NEEDS_A_NEW_CLASS),
    or it is not a unit at all.
    """
    return SUBTYPE_TO_CLASS.get(_norm(subtype))


def classify(design: dict) -> tuple[str | None, str]:
    """(class, why) for one ledger `design` block. An explicit hand tag always wins.

    ⚠ The hand tag winning is deliberate even though it is the drifted copy: a maintainer
    override must survive a re-derivation. Disagreements are REPORTED, never silently resolved
    in either direction.
    """
    explicit = (design or {}).get("class_anchor")
    if explicit:
        return explicit, "explicit"
    sub = _norm((design or {}).get("subtype"))
    if sub in NOT_A_UNIT:
        return None, "not-a-unit"
    if sub in NO_TEMPLATE:
        return None, "no-template"
    if sub in NEEDS_A_NEW_CLASS:
        return None, "no-class-exists"
    derived = SUBTYPE_TO_CLASS.get(sub)
    return (derived, "derived") if derived else (None, "unmapped")


def ledger_rows():
    """(actor, design) for every ledger row; the ledgers are docs/balance/<faction>.json."""
    for path in sorted(LEDGER.glob("*.json")):
        if "class_anchors" in path.name:
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for section in (doc.get("sections") or {}).values():
            for actor, unit in section.items():
                yield actor, (unit.get("design") or {})


def main() -> int:
    ap = argparse.ArgumentParser(description="template -> balance class, and the coverage it buys")
    ap.add_argument("--gaps", action="store_true", help="only what still has no class")
    args = ap.parse_args()

    rows = list(ledger_rows())
    why = collections.Counter()
    per_reason = collections.defaultdict(collections.Counter)
    disagree = collections.Counter()
    for _actor, design in rows:
        cls, reason = classify(design)
        why[reason] += 1
        per_reason[reason][design.get("subtype")] += 1
        if reason == "explicit":
            derived = subtype_to_anchor(design.get("subtype"))
            if derived and derived != cls:
                disagree[(design.get("subtype"), cls, derived)] += 1

    units = sum(n for r, n in why.items() if r != "not-a-unit") or 1
    classed = why["explicit"] + why["derived"]

    out = []
    w = out.append
    w("# Class membership - deriving the balance class from the unit template\n")
    w("⛔ PRIORITY 0 item 1. `anchor_readiness.py` reports **336 of 1870 buildable units tagged")
    w("(18%)** and fits every anchor against that 18%. The class was always derivable from")
    w("`design.subtype` - the `^<Name>Template` the actor inherits - and three incomplete,")
    w("mutually disagreeing copies of the map were the reason it was not derived.\n")
    w(f"* ledger rows: **{len(rows)}**, of which **{why['not-a-unit']}** are buildings, defences")
    w(f"  or upgrades - leaving **{units}** units\n")
    w(f"* **CLASSED: {classed} of {units} ({classed / units:.0%})** - "
      f"{why['explicit']} explicit + **{why['derived']} newly derived**")
    w(f"* ⛔ no template at all (PRIORITY 0 item 2): **{why['no-template']}**")
    w(f"* ⛔ template exists, but no class exists for it: **{why['no-class-exists']}**")
    w(f"* ⚠ template mapped to nothing here: **{why['unmapped']}**\n")

    if disagree:
        w(f"## ⚠ Hand tag disagrees with the template - {sum(disagree.values())} rows\n")
        w("The explicit tag WINS (a maintainer override must survive a re-derivation), so these")
        w("are reported, never auto-resolved. They are where the 18% copy drifted.\n")
        w("| subtype | hand tag | template implies | rows |")
        w("|---|---|---|--:|")
        for (sub, tag, der), n in disagree.most_common():
            w(f"| `{sub}` | {tag} | **{der}** | {n} |")
        w("")

    for reason, title in (("no-class-exists", "⛔ Real units with no class to belong to"),
                          ("no-template", "⛔ No unit template at all - PRIORITY 0 item 2"),
                          ("unmapped", "⚠ Unmapped templates")):
        if not per_reason[reason]:
            continue
        w(f"## {title} - {why[reason]} units\n")
        if reason == "no-class-exists":
            w("`class_anchors.json` holds 27 classes and **not one of them is an air or a naval")
            w("class**. These are real units with real templates; the pipeline cannot price them")
            w("until the classes exist. Each needs a maintainer ruling.\n")
        w("| subtype | units | note |")
        w("|---|--:|---|")
        for sub, n in per_reason[reason].most_common():
            w(f"| `{sub}` | {n} | {NEEDS_A_NEW_CLASS.get(_norm(sub), '')} |")
        w("")

    if not args.gaps:
        w("## Coverage by class\n")
        by_class = collections.Counter()
        for _actor, design in rows:
            cls, _r = classify(design)
            if cls:
                by_class[cls] += 1
        w("| class | units |")
        w("|---|--:|")
        for cls, n in by_class.most_common():
            w(f"| `{cls}` | {n} |")
        w("")

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
