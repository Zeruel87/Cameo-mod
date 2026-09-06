#!/usr/bin/env python3
"""audit_buildable_order.py — verify buildable actor prerequisites and palette order.

Prerequisite order rule (per faction unit): production-building token(s) with ~
come first, then tech-building token(s), then promotion/anti-promotion tokens
(~promotion or !promotion) last.

Build palette order rule: within each production queue and faction, actors are
sorted by tech tier (lowest first), then by cost (cheapest first). This audit
reports any actor whose BuildPaletteOrder does not follow that order.
"""

from __future__ import annotations

import re
import sys

from cameo_model import Model
from report import h1, h2, table


def production_building_names(rs) -> set[str]:
    """Actors that have a ProductionQueue or Production trait are producers."""
    out: set[str] = set()
    for name, node in rs.actors.items():
        if name.startswith("^"):
            continue
        res = rs.resolve(name)
        if res is None:
            continue
        # ⛔ `Node.child()` IS AN EXACT KEY MATCH AND EVERY ONE OF THESE TRAITS IS @SUFFIXED.
        # Real keys are `ProductionQueue@INFANTRY`, `Production@NORMAL`,
        # `Production@CLASSICPRODUCTIONQUEUES` — so `child("ProductionQueue")` returned None for
        # essentially the whole mod. Measured at the moment of the fix: this function saw **9**
        # producers where the tree has **279**, i.e. it missed 97% of them, and every tech tier
        # this audit computes was derived from that 3%. Not a D2k problem — `td_gdi_barracks`,
        # `ts_gdi_barracks` and the rest were all invisible too.
        # ⚠ THE SAME `.child()` TRAP PRODUCED THE BUG REPORT THAT FOUND THIS ONE: a probe using
        # `res.child("ProductionQueue")` concluded "no D2k building has ProductionQueue", when
        # every barracks has one. Use `children_named()` for any trait that can carry an @suffix,
        # which is nearly all of them.
        if res.children_named("ProductionQueue") or res.children_named("Production"):
            out.add(name.lower())
    return out


def is_production_token(token: str, producers: set[str]) -> bool:
    """A factory / production structure prerequisite is prefixed with ~ and names a producer."""
    if not token.startswith("~"):
        return False
    stripped = token.lstrip("~!").lower()
    return stripped in producers and not is_promotion_token(token)


def is_promotion_token(token: str) -> bool:
    """Promotion, anti-promotion, doctrine, or upgrade tokens."""
    t = token.lower()
    if any(k in t for k in ("promotion", "doctrine", "upgrade")):
        return True
    if token.startswith("!"):
        return True
    # ~!foo is an anti-promotion/self-limiting token.
    if token.startswith("~!"):
        return True
    return False


def is_tech_token(token: str, producers: set[str]) -> bool:
    """Tech/building tokens are not production and not promotion."""
    return not is_production_token(token, producers) and not is_promotion_token(token)


def validate_prereq_order(prereqs: str, producers: set[str]) -> list[str]:
    """Return a list of problems with the prerequisite order."""
    if not prereqs:
        return []
    tokens = [t.strip() for t in prereqs.split(",") if t.strip()]
    problems = []
    seen_production = False
    seen_tech = False
    seen_promotion = False
    for raw in tokens:
        prod = is_production_token(raw, producers)
        tech = is_tech_token(raw, producers)
        promo = is_promotion_token(raw)
        if not (prod or tech or promo):
            tech = True
        if prod:
            seen_production = True
            if seen_tech or seen_promotion:
                problems.append(f"production token '{raw}' appears after tech/promotion token")
        elif tech:
            seen_tech = True
            if seen_promotion:
                problems.append(f"tech token '{raw}' appears after promotion token")
        elif promo:
            seen_promotion = True
    return problems


def tech_tier(actor_resolved, producers: set[str]) -> int:
    """Infer tech tier from prerequisites.

    NOTE: This is a simplified 3-level model for build-palette ordering only.
    audit_stat_formulas.py uses a 5+ level data-driven tier model
    (TierContext) for defense/promotion gating checks. Do not assume
    the tier numbers are interchangeable between the two audits.

    Tier 1: only production building(s) required.
    Tier 2: at least one tech building required.
    Tier 3: at least one promotion/doctrine/upgrade required.
    """
    prereqs = (actor_resolved.get("Buildable", "Prerequisites") or "").strip()
    if not prereqs:
        return 1
    tokens = [t.strip() for t in prereqs.split(",") if t.strip()]
    if any(is_promotion_token(t) for t in tokens):
        return 3
    if any(is_tech_token(t, producers) for t in tokens):
        return 2
    return 1


def main() -> int:
    m = Model()
    rs = m.rs
    producers = production_building_names(rs)

    UNIT_TYPES = {"inf", "veh", "air", "nav"}
    buildable: list[tuple[str, object]] = []
    for name, node in rs.actors.items():
        if name.startswith("^") or name.startswith("camera."):
            continue
        if node.child("Buildable") is None or node.child("Health") is None:
            continue
        if m.unit_type(name) not in UNIT_TYPES:
            continue
        buildable.append((name, node))

    # 1. prerequisite order
    prereq_rows = []
    for name, node in sorted(buildable, key=lambda x: x[0]):
        prereqs = (node.get("Buildable", "Prerequisites") or "").strip()
        problems = validate_prereq_order(prereqs, producers)
        if problems:
            prereq_rows.append([name, node.get("Buildable", "Queue") or "",
                                prereqs, "; ".join(problems)])

    # 2. build palette order per queue per faction
    palette_rows = []
    for faction in sorted(f.internal for f in m.real_factions()):
        roster = m.buildable_roster(faction)
        by_queue: dict[str, list[tuple[str, int, int, int]]] = {}
        for lname in roster:
            res = rs.resolve(lname)
            if res is None:
                continue
            if m.unit_type(lname) not in UNIT_TYPES:
                continue
            queues = [q.strip() for q in (res.get("Buildable", "Queue") or "").split(",") if q.strip()]
            cost_str = (res.get("Valued", "Cost") or "0").strip()
            try:
                cost = int(cost_str)
            except ValueError:
                cost = 0
            tier = tech_tier(res, producers)
            bpo_str = (res.get("Buildable", "BuildPaletteOrder") or "0").strip()
            try:
                bpo = int(bpo_str)
            except ValueError:
                bpo = 0
            for queue in queues:
                by_queue.setdefault(queue, []).append((lname, tier, cost, bpo))

        for queue, actors in sorted(by_queue.items()):
            expected = sorted(actors, key=lambda x: (x[1], x[2], x[0]))
            expected_order = {a[0]: i for i, a in enumerate(expected)}
            # ⚠ Iterate in a DETERMINISTIC order, not `actors`' own. `queues` is a set, so the
            # build order of `actors` varies between runs — and because the inner loop `break`s on
            # the first offender it finds, both the row order AND the "should be before X" text
            # changed run to run. docs/audit/latest/ is TRACKED evidence (CLAUDE.md rule 8), so
            # that churn made ~1400 lines diff on every regeneration and hid real changes.
            for name, tier, cost, bpo in expected:
                for other_name, _, _, other_bpo in expected:
                    if other_name == name:
                        continue
                    if expected_order[other_name] < expected_order[name] and other_bpo > bpo:
                        palette_rows.append([faction, queue, name, tier, cost, bpo,
                                             f"should be before {other_name} (tier/cost order)"])
                        break

    print(h1("audit_buildable_order — buildable actor order checks"))
    print(f"Buildable combat actors checked: **{len(buildable)}**")
    print(f"Prerequisite order violations: **{len(prereq_rows)}**")
    print(f"Build palette order violations: **{len(palette_rows)}**\n")

    print(h2("Prerequisite order violations"))
    print(table(["actor", "queue", "prerequisites", "problem"], prereq_rows))

    print(h2("Build palette order violations"))
    print(table(["faction", "queue", "actor", "tier", "cost", "BPO", "problem"], palette_rows))

    return 1 if prereq_rows or palette_rows else 0


if __name__ == "__main__":
    sys.exit(main())
