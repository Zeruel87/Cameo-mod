#!/usr/bin/env python3
"""The rosters do not line up 1:1 — so measure the EXCHANGE RATE and let the leftovers speak.

PRIOR ART, and what each piece does NOT do:
  * `reference_distribution.py` builds per-SOURCE distributions and synthesizes a target for a
    Cameo unit that HAS a name counterpart. It cannot say anything about a unit with none, and its
    distributions are whole-mod, not per-faction. Its `aggregates`/`coordinates`/`project` are
    imported here rather than reimplemented.
  * `assign_references.py` produces the 1:1 pairs under the routing law. It stops at the pair; the
    reference units it did NOT use are discarded.
  * `faction_routes.py` says which reference faction a Cameo faction may see. It is data only.
This module is the layer none of them has: it turns the pairs into a measured scale factor, and
then uses that factor on the UNPAIRED reference units — the ones the assignment threw away.

⛔ THE PROBLEM, stated by the maintainer 2026-09-04:
   *"not all reference factions have all the units from our factions or they have additional units
   we don't have. It might even be that only a small portion of the units could be mapped but
   that's still okay because we can use reasoning and our existing stats and the unused extra
   reference units from their factions to somehow extrapolate something that roughly makes sense."*

Measured, that mismatch is real in BOTH directions (`--report`):
   447 routed Cameo units · 325 paired (73%) · **557 reference rows unused**
   and the reverse where the reference roster is smaller — `ordos` 25 Cameo units against 7
   reference rows, `yuri` 19 against 15.

⭐ THE METHOD, in three steps, each measured rather than assumed.

1. **THE EXCHANGE RATE.** For one (Cameo faction, reference source) route and one stat, the pairs
   the assignment DID make give the scale between the two rosters:

       k = geometric mean over pairs of ( cameo_stat / reference_stat )

   That is "use our existing stats" in one number. It is per stat, because HP and range do not
   scale together across mods, and per route, because two reference sources disagree.

2. **THE UNUSED REFERENCE UNITS BECOME VIRTUAL MEMBERS.** Every unpaired reference row, times `k`,
   is a Cameo-scale data point. It is evidence about the SHAPE of the population — where the
   ceiling is, how wide the spread runs, whether the reference faction fields something Cameo
   does not — and it is NEVER a shipped stat for any actor.

3. **AN UNPAIRED CAMEO UNIT IS PLACED BY RANK.** Its percentile inside its own (faction, type)
   population is read off the COMBINED real+virtual distribution. So a unit with no counterpart
   still moves, and it moves because of units that do exist, not because of a forced pairing.

⚠ WHAT THIS IS NOT. It is not a price and it is not a target to apply. It says where a unit sits
in its class's distribution; `formula.py` still prices it, and `apply_balance --confirm` still
needs a maintainer order.

⛔ CONFIDENCE IS THE PAIR COUNT, and it must not be smoothed away. A route with one pair has an
exchange rate resting on one unit; the number still computes and means almost nothing. Rates are
reported with `n`, and `--min-pairs` refuses to emit below a floor.

    python tools/balance/faction_extrapolate.py --report          # the mismatch, per faction
    python tools/balance/faction_extrapolate.py --rates           # the measured exchange rates
    python tools/balance/faction_extrapolate.py --faction ts_gdi  # one faction, in full
    python tools/balance/faction_extrapolate.py --write           # save the derived JSON
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))
import assign_references as ar        # noqa: E402
import faction_routes as fr           # noqa: E402
import reference_distribution as rd   # noqa: E402
import class_membership as cm         # noqa: E402

ROOT = rd.ROOT
# ⚠ THE LEADING UNDERSCORE IS A CONVENTION, NOT A STYLE CHOICE. Everything in `derived/` is a
# SIDECAR to a raw ledger of the same name, and `test_ledger_split.test_every_sidecar_has_a_raw_
# counterpart` enforces it; `_`-prefixed files are the exemption for artifacts that cut across all
# of them, as `_model.json` does. This one is per-FACTION, not per-ledger.
OUT = ROOT / "docs" / "balance" / "derived" / "_faction_extrapolation.json"

# The stats an exchange rate is measured on. Deliberately the five a placement decision rests on —
# `turn_speed`/`turn_ratio`/`w_burst`/`w_reload` are shape details that ride on these.
RATE_STATS = ("hp", "speed", "w_range", "w_dps", "cost")

MIN_PAIRS_DEFAULT = 3

# Virtual members required in a (faction, type) population before a rank placement means
# anything at all — below this the pool is the unit's own roster and the placement is identity.
MIN_VIRTUAL = 3

# Members required on EACH side before a rank placement is meaningful.
MIN_POPULATION = 3

# Distinct values the reference population must hold before it can place anything: a
# distribution that is one repeated number is a point, and a point cannot rank anybody.
MIN_DISTINCT = 3


def _num(rec, key):
    v = rec.get(key)
    if isinstance(v, dict):
        v = v.get("v")
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


def paired_rows(result, peers):
    """{cameo id: {source: peer row}} — re-attach the assignment's chosen rows to the corpus.

    ⚠ The assignment stores the reference unit's NAME, not the row. Two rows in one source can
    share a name (a variant), so the lookup takes the row whose stats the assignment recorded —
    matching on hp and cost — and falls back to the first name hit rather than dropping the pair.
    """
    idx = collections.defaultdict(list)
    for p in peers:
        idx[(p["source"], (p.get("name") or "").strip())].append(p)
    out = {}
    for cid, srcs in result.items():
        for src, m in srcs.items():
            cands = idx.get((src, (m.get("name") or "").strip()))
            if not cands:
                continue
            best = next((p for p in cands
                         if p.get("hp") == m.get("hp") and p.get("cost") == m.get("cost")),
                        cands[0])
            out.setdefault(cid, {})[src] = best
    return out


def exchange_rates(pairs, cameo_by_id, min_pairs=MIN_PAIRS_DEFAULT):
    """{(faction, source): {stat: {k, n, spread}}} — the measured scale between two rosters.

    `spread` is the geometric standard deviation of the per-pair ratios: 1.0 means every pair
    agrees on the scale, and a large value means the two rosters do not scale by one number at all.
    ⚠ It is reported, not acted on — an honest wide rate is more useful than a hidden one.
    """
    ratios = collections.defaultdict(list)
    for cid, srcs in pairs.items():
        fac = fr.faction_of(cid)
        cam = cameo_by_id.get(cid)
        if not fac or not cam:
            continue
        for src, p in srcs.items():
            for stat in RATE_STATS:
                a, b = _num(cam, stat), _num(p, stat)
                if a and b:
                    ratios[(fac, src, stat)].append(a / b)
    out = {}
    for (fac, src, stat), vals in ratios.items():
        if len(vals) < min_pairs:
            continue
        k = rd.gm(vals)
        if not k:
            continue
        logs = [statistics.fmean([math.log(v) for v in vals])]
        sd = (statistics.pstdev([math.log(v) for v in vals]) if len(vals) > 1 else 0.0)
        out.setdefault((fac, src), {})[stat] = {
            "k": k, "n": len(vals), "spread": math.exp(sd),
            "_mean_log": logs[0],
        }
    return out


def virtual_members(rates, pairs, peers):
    """The UNUSED reference rows, converted to Cameo scale. {faction: [row, ...]}

    ⛔ These are evidence, never stats. A virtual member never becomes an actor and is never
    written to yaml; it exists so a class population reflects what the reference faction actually
    fields, including the units Cameo has no counterpart for.
    """
    used = set()
    for cid, srcs in pairs.items():
        for src, p in srcs.items():
            used.add(id(p))
    out = collections.defaultdict(list)
    for fac in sorted(fr.ROUTES):
        for src, toks in fr.routes_for(fac):
            rate = rates.get((fac, src))
            if not rate:
                continue
            for p in peers:
                if p.get("source") != src or id(p) in used:
                    continue
                if not (fr.peer_factions(p) & toks):
                    continue
                # ⛔ COMBAT TYPES ONLY. Unfiltered, the leftovers are mostly the reference mod's
                # ECONOMY: 36 of Shattered Paradise's 48 unused `gdi` rows are buildings, and a
                # construction yard is not evidence about a tank. It also removes the whole
                # shared-content problem for free — the 9 rows in the corpus tagged with ≥80% of
                # their own source's factions (`C.A.B.A.L. Construction Yard` carries all five of
                # Shattered Paradise's, so every route admits it) are ALL buildings. Measured, not
                # assumed; if a non-building ever joins that set it needs its own rule.
                if p.get("type") not in rd.COMBAT_TYPES:
                    continue
                row = {"source": src, "name": p.get("name"), "type": p.get("type"),
                       "virtual": True}
                got = False
                for stat, ent in rate.items():
                    v = _num(p, stat)
                    if v:
                        row[stat] = v * ent["k"]
                        got = True
                if got:
                    out[fac].append(row)
    return out


def converted_pool(faction, rates, peers):
    """{(type, stat): [values in CAMEO scale]} — the routed reference roster, times its own rate.

    ⛔ THE WHOLE ROSTER, NOT THE LEFTOVERS. The first version of this pooled only the UNUSED
    reference rows, on the reasoning that the paired ones had already spoken. Measured, that
    emptied the pool exactly where it was needed most: infantry is where 1:1 name matching
    succeeds, so almost no infantry row is left over — and infantry is 59 of the 122 unpaired
    Cameo units. A distribution is made of all its members; a row does not leave it by having been
    matched.

    ⚠ Each source is converted by ITS OWN rate before pooling. Two sources of one faction disagree
    about scale, and averaging their raw values would put the disagreement inside the distribution
    instead of in the rates where it is visible.
    """
    pool = collections.defaultdict(list)
    for src, toks in fr.routes_for(faction):
        rate = rates.get((faction, src))
        if not rate:
            continue
        for p in peers:
            if p.get("source") != src or not (fr.peer_factions(p) & toks):
                continue
            if p.get("type") not in rd.COMBAT_TYPES:
                continue
            for stat, ent in rate.items():
                v = _num(p, stat)
                if v:
                    pool[(p["type"], stat)].append(v * ent["k"])
    return pool


def quantile(sorted_vals, q):
    """The value at percentile `q`, INTERPOLATED between reference points in LOG space.

    ⛔ SNAPPING TO THE NEAREST POINT COLLAPSES A SMALL ROSTER. OpenE2140's `ed` offers four
    infantry rows, and nearest-point placement put SIX Naxis infantry — percentiles 0.25 through
    1.00, spanning 20,000 to 96,000 HP — on the single value 15,014. The reference is genuinely
    only four points of information, but it is not a claim that six units are identical, and a
    placement that erases Cameo's own ordering is worse than no placement at all.

    ⚠ Log space, because every aggregate in this pipeline is geometric: interpolating 1,000 and
    100,000 at the midpoint gives 10,000, not 50,500.
    """
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    pos = min(1.0, max(0.0, q)) * (n - 1)
    lo = int(math.floor(pos))
    hi = min(n - 1, lo + 1)
    frac = pos - lo
    a, b = sorted_vals[lo], sorted_vals[hi]
    if frac == 0.0 or a == b:
        return a          # exact on a reference point: exp(log(16)) is 15.999999999999998
    if a > 0 and b > 0:
        return math.exp(math.log(a) + frac * (math.log(b) - math.log(a)))
    return a + frac * (b - a)


def place_unpaired(faction, cameo_rows_in, pool, paired_ids):
    """Rank-place every unpaired Cameo unit of `faction` onto the converted reference roster.

    The unit's percentile inside its own (faction, type) population is read off the reference
    faction's distribution in Cameo scale. So a unit with no counterpart still moves, and it moves
    because of units that DO exist — including the ones the reference faction fields and Cameo
    does not, which is the whole point of pooling the roster rather than the matches.

    ⚠ Rank, not rank-preserving-in-place: if Cameo's 3rd-heaviest tank sits at the 60th percentile
    of its own roster, it is placed at the 60th percentile of the reference roster. The reference
    decides the SPREAD; Cameo's own roster decides the ORDER.
    """
    out = {}
    by_type = collections.defaultdict(list)
    for c in cameo_rows_in:
        by_type[c["type"]].append(c)
    for kind, members in by_type.items():
        for stat in RATE_STATS:
            own = sorted(x for x in (_num(m, stat) for m in members) if x)
            ref = sorted(pool.get((kind, stat), ()))
            # a distribution needs a population on BOTH sides, not two points
            if len(own) < MIN_POPULATION or len(ref) < MIN_POPULATION:
                continue
            # ⛔ A REFERENCE POPULATION WITH NO SPREAD CARRIES NO PLACEMENT, and it is not obvious
            # from the row count. OpenE2140's `ed` fields four infantry — Androids A01-A04 — at
            # HP 28/28/28/20 and speed 50/50/50/50. Placing Naxis's nine infantry (HP 8,000 to
            # 96,000) against that put six of them on ONE value and every one of them on ONE
            # speed: the reference would have DELETED a roster's variety while looking like
            # evidence. A reference faction can be uninformative for a whole type, and the tool
            # has to say so rather than average it away.
            if len(set(ref)) < MIN_DISTINCT:
                continue
            for m in members:
                if m["id"] in paired_ids:
                    continue
                x = _num(m, stat)
                if not x:
                    continue
                q = min(1.0, sum(1 for v in own if v < x) / max(1, len(own) - 1))
                out.setdefault(m["id"], {})[stat] = {
                    "now": x, "placed": quantile(ref, q), "pct": round(q, 3),
                    "ref_n": len(ref), "own_n": len(own),
                }
    return out


def build(min_pairs=MIN_PAIRS_DEFAULT):
    peers = rd.peer_rows()
    cameo = rd.cameo_rows()
    result, _, _ = ar.assign()
    cameo_by_id = {c["id"]: c for c in cameo}
    pairs = paired_rows(result, peers)
    rates = exchange_rates(pairs, cameo_by_id, min_pairs)
    virt = virtual_members(rates, pairs, peers)
    # ⛔ PLACEMENT USES THE SAME SCOPE AS THE ASSIGNMENT — clause 10's exemptions included.
    # Without this the rank-placer happily placed MCVs, carryalls and drone miners: 41 placements,
    # every one on an actor the assignment had already ruled out of the reference system. The
    # report counted them as 0 because IT applies the exemption, so the tool disagreed with itself
    # — which is the only reason the bug was visible at all.
    led = ar.ledger()
    scope = [c for c in cameo
             if c["id"] in led and not ar.exempt(c["id"], led[c["id"]])]
    placements = {}
    for fac in sorted(fr.ROUTES):
        members = [c for c in scope if fr.faction_of(c["id"]) == fac]
        if not members:
            continue
        placements.update(place_unpaired(fac, members, converted_pool(fac, rates, peers),
                                         set(pairs)))
    return peers, cameo, pairs, rates, virt, placements


def _report(peers, cameo, pairs, rates, virt, placements):
    led = ar.ledger()
    print(f"{'faction':<17}{'cameo':>6}{'paired':>7}{'ref':>5}{'unused':>7}{'virtual':>8}"
          f"{'rates':>6}{'placed':>7}")
    tot = collections.Counter()
    for fac in sorted(fr.ROUTES):
        members = [c for c in cameo if fr.faction_of(c["id"]) == fac
                   and c["id"] in led and not ar.exempt(c["id"], led[c["id"]])]
        if not members:
            continue
        ref = sum(1 for p in peers if fr.allows(fac, p))
        pd = sum(1 for c in members if c["id"] in pairs)
        used = sum(len(v) for cid, v in pairs.items() if fr.faction_of(cid) == fac)
        nrate = sum(1 for key in rates if key[0] == fac)
        placed = sum(1 for c in members if c["id"] in placements)
        print(f"{fac:<17}{len(members):>6}{pd:>7}{ref:>5}{ref - used:>7}"
              f"{len(virt.get(fac, [])):>8}{nrate:>6}{placed:>7}")
        tot.update({"cam": len(members), "pd": pd, "ref": ref, "un": ref - used,
                    "virt": len(virt.get(fac, [])), "rate": nrate, "placed": placed})
    print(f"{'TOTAL':<17}{tot['cam']:>6}{tot['pd']:>7}{tot['ref']:>5}{tot['un']:>7}"
          f"{tot['virt']:>8}{tot['rate']:>6}{tot['placed']:>7}")
    print(f"\ncoverage: {tot['pd']} paired + {tot['placed']} rank-placed = "
          f"{tot['pd'] + tot['placed']} of {tot['cam']} routed Cameo units")


def by_class(pairs, placements):
    """Per-CLASS grounding — the report that says where the anchors can actually be fitted.

    ⛔ THREE ZEROES HERE ARE THE RULES WORKING, NOT HOLES, and each is measured rather than
    assumed. Reading them as defects is the trap this function exists to prevent:

      * `support` — 105 members, ALL exempt under clause 10 (MCV, engineer, harvester,
        transports, detectors). They never consume a reference by design.
      * `commando` and `epic_vehicle` — 27 and 24 members, and **100% of each carries
        `build_limit`**. The maintainer's population rule (2026-08-30) excludes one-offs from the
        corpus on BOTH sides: *"Cameo's heroes and epic units must be excluded since they will be
        balanced separately."* So there is no peer row to match AND no Cameo row to match it to.
        Both classes reading zero is that ruling, executing.

    What IS a finding is a class with routed members and no grounding for some other reason.
    """
    led = ar.ledger()
    rows = []
    for klass in sorted({cm.classify(u.get("design") or {})[0] for u in led.values()} - {None}):
        members = [n for n, u in led.items()
                   if cm.classify(u.get("design") or {})[0] == klass and u.get("buildable") is True]
        if not members:
            continue
        scope = [m for m in members if not ar.exempt(m, led[m])]
        routed = [m for m in scope
                  if fr.faction_of(m) and fr.routes_for(fr.faction_of(m))]
        rows.append({
            "class": klass, "members": len(members),
            "exempt": len(members) - len(scope),
            "routed": len(routed),
            "paired": sum(1 for m in routed if m in pairs),
            "placed": sum(1 for m in routed if m in placements),
            "two_plus": sum(1 for m in routed if len(pairs.get(m, {})) >= 2),
            "build_limited": sum(1 for m in members if led[m].get("build_limit")),
        })
    rows.sort(key=lambda r: -(r["paired"] + r["placed"]))
    return rows


def _by_class(rows):
    print(f"  {'class':<18}{'memb':>5}{'exmpt':>6}{'limit':>6}{'routed':>7}{'paired':>7}"
          f"{'placed':>7}{'>=2':>5}   grounded")
    tot = collections.Counter()
    for r in rows:
        g = r["paired"] + r["placed"]
        note = ""
        if r["routed"] and not g:
            note = ("  ✅ excluded by the population rule (all build-limited)"
                    if r["build_limited"] == r["members"] else "  ⛔ routed but NOT grounded")
        elif r["exempt"] == r["members"]:
            note = "  ✅ wholly exempt (clause 10)"
        pct = f"{g / r['routed']:.0%}" if r["routed"] else "—"
        print(f"  {r['class']:<18}{r['members']:>5}{r['exempt']:>6}{r['build_limited']:>6}"
              f"{r['routed']:>7}{r['paired']:>7}{r['placed']:>7}{r['two_plus']:>5}{pct:>8}{note}")
        for k in ("members", "exempt", "routed", "paired", "placed", "two_plus"):
            tot[k] += r[k]
    print(f"  {'TOTAL':<18}{tot['members']:>5}{tot['exempt']:>6}{'':>6}{tot['routed']:>7}"
          f"{tot['paired']:>7}{tot['placed']:>7}{tot['two_plus']:>5}")
    print(f"\n  grounded: {tot['paired']} paired + {tot['placed']} rank-placed = "
          f"{tot['paired'] + tot['placed']} of {tot['routed']} routed class members")
    # ⚠ THIS LINE USED TO SAY the count "does not move until MO / CnC Reloaded / DTA land".
    # They landed — the INI extraction brought in all three plus RA2 Reborn, Red Resurrection,
    # RA2 0XX and Rise of the East — and the sentence stayed, telling every reader the number was
    # still blocked. A hardcoded blocker in a REPORT outlives the blocker itself; name the
    # measured shortfall instead, so the text cannot rot while the number moves.
    short = [r for r in rows if r["routed"] and r["two_plus"] < r["routed"]]
    print(f"  ⚠ only {tot['two_plus']} of {tot['routed']} routed members reach the >=2 reference "
          f"floor; {len(short)} classes are still short of it.")


def _rates(rates):
    print(f"  {'faction':<17}{'source':<24}{'stat':<9}{'k':>10}{'n':>5}{'spread':>9}")
    for (fac, src) in sorted(rates):
        for stat in RATE_STATS:
            ent = rates[(fac, src)].get(stat)
            if not ent:
                continue
            warn = "  ⚠ wide" if ent["spread"] > 3 else ""
            print(f"  {fac:<17}{src[:23]:<24}{stat:<9}{ent['k']:>10.3f}{ent['n']:>5}"
                  f"{ent['spread']:>9.2f}{warn}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", action="store_true", help="the roster mismatch, per faction")
    ap.add_argument("--by-class", action="store_true",
                    help="per-CLASS grounding: where the anchors can actually be fitted")
    ap.add_argument("--rates", action="store_true", help="the measured exchange rates")
    ap.add_argument("--faction", help="one faction, in full")
    ap.add_argument("--min-pairs", type=int, default=MIN_PAIRS_DEFAULT,
                    help=f"pairs required before a rate is emitted (default {MIN_PAIRS_DEFAULT})")
    ap.add_argument("--write", action="store_true", help="save the derived JSON")
    args = ap.parse_args()

    peers, cameo, pairs, rates, virt, placements = build(args.min_pairs)
    if args.by_class:
        _by_class(by_class(pairs, placements))
    elif args.rates:
        _rates(rates)
    elif args.faction:
        fac = args.faction
        if fac not in fr.ROUTES:
            print(f"⛔ {fac} has no route. "
                  f"{fr.UNROUTED.get(fac, 'not a declared Cameo faction')}")
            return 1
        print(f"{fac}  routes: "
              + ", ".join(f"{s} {'/'.join(sorted(t))}" for s, t in fr.routes_for(fac)))
        _rates({k: v for k, v in rates.items() if k[0] == fac})
        members = [c for c in cameo if fr.faction_of(c["id"]) == fac]
        print(f"\n  paired {sum(1 for c in members if c['id'] in pairs)} · "
              f"rank-placed {sum(1 for c in members if c['id'] in placements)} · "
              f"virtual members {len(virt.get(fac, []))}")
        print(f"\n  {'unit':<34}{'stat':<9}{'now':>11}{'placed':>11}{'pct':>7}{'ref':>6}")
        for c in sorted(members, key=lambda c: c["id"]):
            for stat, e in (placements.get(c["id"]) or {}).items():
                print(f"  {c['id'][:33]:<34}{stat:<9}{e['now']:>11,.0f}{e['placed']:>11,.0f}"
                      f"{e['pct']:>7.2f}{e['ref_n']:>6}")
    else:
        _report(peers, cameo, pairs, rates, virt, placements)

    if args.write:
        doc = {
            "rates": {f"{fac}|{src}": {s: {k: (round(v, 4) if isinstance(v, float) else v)
                                           for k, v in ent.items() if not k.startswith("_")}
                                       for s, ent in stats.items()}
                      for (fac, src), stats in rates.items()},
            "virtual_members": {fac: rows for fac, rows in sorted(virt.items())},
            "placements": placements,
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(doc, indent=1, sort_keys=True, default=float) + "\n",
                       encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
