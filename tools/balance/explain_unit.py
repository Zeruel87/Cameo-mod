#!/usr/bin/env python3
"""Show EXACTLY how one Cameo actor's reference target is reached — every source, every coordinate.

PRIOR ART: `reference_distribution.py` computes the targets for all 302 matched actors and prints a
summary table; it deliberately shows no working. This shows the working for ONE actor, and adds the
routing variants that module does not implement. It imports that module wholesale rather than
re-deriving anything — the numbers here ARE that pipeline's numbers.

    python tools/balance/explain_unit.py ra2_soviets_conscript
    python tools/balance/explain_unit.py ra2_soviets_apocalypsetank --stat hp

MAINTAINER ORDER 2026-09-03, on reconciling the two routing rules:
*"I think we need a combination of all the above but let us first do some examples right? Starting
with 1 rifle unit and 1 main battle tank unit as an example and then see exactly what we should
do!"*

So this tool exists to make that decision on evidence rather than on principle. It prints the same
unit's target four ways and lets the difference be read off.
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import reference_distribution as rd  # noqa: E402

syn = rd.syn
gm = rd.gm

# ── The home sources per Cameo faction family (maintainer 2026-09-03) ────────────────────────
# ⚠ NAMES AS THE POOL SEES THEM. A label typed differently here silently routes to nothing —
# the exact failure `reference_lineages.py` was created to stop.
# ⭐ Mental Omega and CnC Reloaded were wired into the distribution layer 2026-09-03, so the RA2
# home set is now complete. DTA still contributes zero rows (no roster), so the TD/RA1 home set
# runs on three of its four named sources. The tool reports which named sources are missing rather
# than letting a routing quietly run on half its intended evidence.
HOME = {
    "ra2": ["CnC Reloaded", "Romanov's Vengeance", "Mental Omega", "Combined Arms"],
    "td_ra1": ["DTA", "OpenRA Tiberian Dawn", "OpenRA Red Alert", "Combined Arms"],
    "ts": ["Shattered Paradise", "Crystallized Nexus", "OpenRA Tiberian Sun"],
}
FAMILY_PREFIX = [
    ("ts", ("ts_", "forgotten_", "cabal_")),
    ("td_ra1", ("td_", "ra1_", "japan_")),
    ("ra2", ("ra2_", "yuri_", "naxis_", "asianalliance_", "steelconsortium_", "futuretech_",
             "latinsyndicate_", "schwarzermond_", "tkm_")),
]


def family_of(actor_id):
    for fam, prefixes in FAMILY_PREFIX:
        if actor_id.startswith(prefixes):
            return fam
    return None


def real_weapon(p, mapped):
    """Only weapons actually FIRED by a regular buildable unit or DEFENCE (maintainer 2026-09-03).

    ⛔ The armour condition is applied ONLY to sources whose armour vocabulary was mapped. Without
    that guard it conflates "this weapon does no damage" with "we could not map this mod's armour
    names", and deletes whole sources: Generals Alpha declares 37 armour types and maps none.
    """
    if p.get("type") == "building":                    # a superweapon/support STRUCTURE
        return False
    if not p.get("w_dps") or not p.get("w_damage"):    # does not actually fire
        return False
    if p["source"] in mapped and not any(p.get(f"dps_vs_{l}") for l in rd.LADDERS):
        return False                                   # instakill with no armour profile
    return True


WSTATS = {"w_range", "w_damage", "w_burst", "w_reload", "w_dps"}


def build(rows, mapped, filtered=True):
    out = collections.defaultdict(dict)
    keyed = collections.defaultdict(list)
    for r in rows:
        keyed[r["source"]].append(r)
    for src, items in keyed.items():
        pops = {"overall": [r for r in items if r["type"] in rd.COMBAT_TYPES]}
        for t in rd.POPULATIONS:
            pops[t] = [r for r in items if r["type"] == t]
        for pop, rs in pops.items():
            for stat in rd.ALL_STATS:
                use = [r for r in rs
                       if not (filtered and stat in WSTATS) or real_weapon(r, mapped)]
                agg = rd.aggregates([r.get(stat) for r in use])
                if agg:
                    out[src].setdefault(pop, {})[stat] = agg
    return out


def coords(x, agg):
    """The five relative values, low/high ends read at the 5th and 95th percentile."""
    if not agg or not x or x <= 0:
        return {}
    o = {k: x / agg[m] for k, m in (("r_med", "median"), ("r_am", "am"), ("r_gm", "gm"))
         if agg.get(m)}
    for k, m in (("r_p05", "p05"), ("r_p95", "p95")):
        if agg.get(m):
            o[k] = x / agg[m]
    return o


def project(c, agg):
    if not agg:
        return {}
    return {k: c[k] * agg[m] for k, m in (("r_med", "median"), ("r_am", "am"), ("r_gm", "gm"),
                                          ("r_p05", "p05"), ("r_p95", "p95"))
            if k in c and agg.get(m)}


def synthesize(matches, cameo_row, stat, pdist, cdist, cameo_votes):
    """(target, sources used). Cameo's own value is ONE vote and only when >=2 references exist."""
    pooled, used = collections.defaultdict(list), set()
    for p in matches:
        x = p.get(stat)
        if not x:
            continue
        for pop in ("overall", p["type"]):
            for k, v in coords(x, pdist.get(p["source"], {}).get(pop, {}).get(stat)).items():
                pooled[(pop, k)].append(v)
                used.add(p["source"])
    if len(used) < 2:            # the >=2 REFERENCE floor — see §3 of REFERENCE_METHOD.md
        return None, used
    synth = {key: gm(v) for key, v in pooled.items()}
    cands = []
    for pop in ("overall", cameo_row["type"]):
        cands += list(project({k: v for (pp, k), v in synth.items() if pp == pop},
                              cdist.get(pop, {}).get(stat)).values())
    cands = [c for c in cands if c and c > 0]
    if not cands:
        return None, used
    target = gm(cands)
    if cameo_votes and cameo_row.get(stat):
        # ONE vote among >=3, so Cameo weighs <=33% (maintainer 2026-09-03).
        target = gm([target] * len(used) + [cameo_row[stat]])
    return target, used


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("actor", help="Cameo actor id, e.g. ra2_soviets_conscript")
    ap.add_argument("--stat", action="append", help="restrict to these stats")
    ap.add_argument("--unfiltered", action="store_true",
                    help="keep dummy/superweapon rows in the weapon population")
    args = ap.parse_args()

    peers, cameo = rd.peer_rows(), rd.cameo_rows()
    mapped = {s for s in {p["source"] for p in peers}
              if sum(1 for p in peers if p["source"] == s
                     and any(p.get(f"dps_vs_{l}") for l in rd.LADDERS)) >= 8}
    pdist = build(peers, mapped, not args.unfiltered)
    cdist = build(cameo, mapped, not args.unfiltered)["Cameo"]

    row = next((c for c in cameo if c["id"] == args.actor), None)
    if not row:
        print(f"⛔ no Cameo actor {args.actor!r}")
        return 2
    by_name = collections.defaultdict(list)
    for r in peers:
        k = syn.norm(r["name"])
        if len(k) >= syn.MIN_KEY:
            by_name[k].append(r)
    akey = syn.norm(row["id"].split("_")[-1])
    matches = [p for k, pl in by_name.items() if akey.startswith(k) for p in pl]

    fam = family_of(row["id"])
    home = HOME.get(fam, [])
    present = {p["source"] for p in peers}
    missing = [h for h in home if h not in present]

    print(f"{row['id']}   type={row['type']}   family={fam or '—'}")
    print(f"home sources: {', '.join(home) or '—'}")
    if missing:
        print(f"  ⛔ NOT AVAILABLE (ruled in, not wired / no rows): {', '.join(missing)}")
    print(f"\nmatched reference rows ({len(matches)} from "
          f"{len({p['source'] for p in matches})} sources):")
    print(f"  {'source':<24}{'unit':<24}{'home?':<7}{'hp':>9}{'speed':>7}{'dmg':>9}{'range':>8}")
    for p in sorted(matches, key=lambda p: p["source"]):
        mark = "HOME" if p["source"] in home else ""
        print(f"  {p['source'][:23]:<24}{p['name'][:23]:<24}{mark:<7}"
              f"{(p.get('hp') or 0):>9.0f}{(p.get('speed') or 0):>7.0f}"
              f"{(p.get('w_damage') or 0):>9.0f}{(p.get('w_range') or 0):>8.0f}")

    stats = args.stat or ["hp", "speed", "w_damage", "w_range"]
    variants = [
        ("A  all sources",        lambda m: m),
        ("B  home only",          lambda m: [p for p in m if p["source"] in home]),
        ("C  home, else all",     lambda m: ([p for p in m if p["source"] in home]
                                             if len({p["source"] for p in m
                                                     if p["source"] in home}) >= 2 else m)),
    ]
    for cameo_votes in (False, True):
        label = "Cameo VOTES (<=33%)" if cameo_votes else "peers only"
        print(f"\n── target, {label} " + "─" * 30)
        print(f"  {'variant':<22}{'stat':<11}{'now':>10}{'target':>11}{'ratio':>8}  sources")
        for name, pick in variants:
            for stat in stats:
                sel = pick(matches)
                t, used = synthesize(sel, row, stat, pdist, cdist, cameo_votes)
                now = row.get(stat)
                if t is None:
                    why = f"only {len(used)} source(s) — under the >=2 floor" if used else "no data"
                    print(f"  {name:<22}{stat:<11}{(now or 0):>10.0f}{'—':>11}{'':>8}  {why}")
                else:
                    print(f"  {name:<22}{stat:<11}{(now or 0):>10.0f}{t:>11.0f}"
                          f"{(t/now if now else 0):>8.2f}  {', '.join(sorted(used))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
