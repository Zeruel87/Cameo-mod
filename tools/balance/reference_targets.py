#!/usr/bin/env python3
"""reference_targets.py — the R4 synthesis for real actors: 3 references + Cameo, one vote each.

PRIOR ART, and why this is not a fourth copy of it:
  * `assign_references.py` chooses WHICH reference units a Cameo actor may use. It stops at the
    pairing and stores only the reference's name/hp/cost.
  * `reference_distribution.py` owns the coordinate machinery (`aggregates`, `coordinates`,
    `project`, `gm`) and builds every source's own distributions. All of it is imported here.
  * `explain_unit.py` shows ONE actor's working, and re-matches with the superseded prefix test
    rather than reading the assignment.
This module is the missing join: the ASSIGNMENT's pairs, run through the DISTRIBUTION's
coordinates, for a whole faction at a time.

⛔ R4 — EQUAL THIRDS, AND CAMEO ALWAYS VOTES (maintainer, `REFERENCE_EXTRACTION_PLAN.md`):
   `Cameo TD GDI = DTA GDI x Combined Arms GDI x current Cameo TD GDI`, each 1/3, geometric mean.
   Generalised: every voice is equal, so with 3 references Cameo is 1 of 4 = 25%.

⛔ RAW STATS ARE NEVER AVERAGED ACROSS SOURCES. DTA runs ~2,500 HP vehicles and Combined Arms
~30,000; their mean belongs to no game. Only the DIMENSIONLESS coordinates are pooled, then
projected onto Cameo's own distribution. See `REFERENCE_METHOD.md` §1-§2.

    python tools/balance/reference_targets.py --faction td_gdi td_nod ra1_allies ra1_soviets
    python tools/balance/reference_targets.py --faction td_gdi --md docs/balance/targets_td.md
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))
import reference_distribution as rd  # noqa: E402

ROOT = rd.ROOT
ASSIGN = ROOT / "docs" / "balance" / "derived" / "reference_assignment.json"
STATS = ("hp", "speed", "w_range", "w_dps", "cost")


def add_cost_distribution(dist, rows):
    """Fold a `cost` distribution into `dist` in place.

    ⛔ `reference_distribution.ALL_STATS` is CHASSIS + WEAPON + ARMOR and deliberately has no
    `cost` — the module is the CHASSIS layer and never priced anything. Asking it for a cost
    target therefore returns nothing, silently, for every actor: an empty column that reads as
    "no reference data" when the data is right there in every row. Price is a first-class
    reference stat here, so the aggregate is built the same way for the same populations.
    """
    by_source = collections.defaultdict(list)
    for r in rows:
        by_source[r["source"]].append(r)
    for source, items in by_source.items():
        pops = {"overall": [r for r in items if r["type"] in rd.COMBAT_TYPES]}
        for t in rd.POPULATIONS:
            pops[t] = [r for r in items if r["type"] == t]
        for pop, members in pops.items():
            agg = rd.aggregates([m.get("cost") for m in members
                                 if m.get("cost") and rd.eligible(m, "cost")])
            if agg:
                dist.setdefault(source, {}).setdefault(pop, {})["cost"] = agg


def peer_index(peers):
    idx = collections.defaultdict(list)
    for p in peers:
        idx[(p["source"], (p.get("name") or "").strip())].append(p)
    return idx


def attach(assignment, idx):
    """{actor: [peer row, ...]} — the assignment stores a NAME; recover the row it meant.

    ⚠ Two rows in one source can share a name (a variant), so the hp/cost the assignment
    recorded disambiguates; a name-only hit is the fallback rather than a dropped pair.
    """
    out = {}
    for actor, srcs in assignment.items():
        rows = []
        for src, rec in srcs.items():
            hits = idx.get((src, (rec.get("name") or "").strip()))
            if not hits:
                continue
            best = hits[0]
            for h in hits:
                if h.get("hp") == rec.get("hp") and h.get("cost") == rec.get("cost"):
                    best = h
                    break
            rows.append(best)
        if rows:
            out[actor] = rows
    return out


def target_for(rows, cameo_row, stat, dist, cdist):
    """(peers_only, with_cameo, n_sources) on one stat, or (None, None, 0)."""
    pooled, used = collections.defaultdict(list), set()
    for r in rows:
        x = r.get(stat)
        if not x or x <= 0:
            continue
        for pop in ("overall", r["type"]):
            agg = dist.get(r["source"], {}).get(pop, {}).get(stat)
            for k, v in rd.coordinates(float(x), agg).items():
                pooled[(pop, k)].append(v)
                used.add(r["source"])
    if not pooled:
        return None, None, 0
    # p_rng is a bounded [0,1] position and can legitimately be 0, where a geometric mean is
    # undefined; every other coordinate is a ratio and pools geometrically.
    synth = {pk: (statistics.fmean(v) if pk[1] == "p_rng" else rd.gm(v)) for pk, v in pooled.items()}
    cands = []
    for pop in ("overall", cameo_row["type"]):
        coord = {k: v for (p_, k), v in synth.items() if p_ == pop}
        cands += list(rd.project(coord, cdist.get(pop, {}).get(stat)).values())
    cands = [c for c in cands if c and c > 0]
    if not cands:
        return None, None, 0
    peers_only = rd.gm(cands)
    now = cameo_row.get(stat)
    with_cameo = rd.gm([peers_only] * len(used) + [now]) if now and now > 0 else peers_only
    return peers_only, with_cameo, len(used)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--faction", nargs="+", required=True)
    ap.add_argument("--md", help="write the table to this path")
    args = ap.parse_args()

    peers = rd.peer_rows()
    cameo = rd.cameo_rows()
    dist = rd.build_distributions(peers)
    add_cost_distribution(dist, peers)
    cameo_dist_all = rd.build_distributions(cameo)
    add_cost_distribution(cameo_dist_all, cameo)
    cdist = cameo_dist_all["Cameo"]
    assignment = json.loads(ASSIGN.read_text(encoding="utf-8"))["assignment"]
    attached = attach(assignment, peer_index(peers))
    crows = {c["id"]: c for c in cameo}

    out = ["# Reference targets — R4 synthesis (references + Cameo, one vote each)", ""]
    for fac in args.faction:
        members = sorted(a for a in crows if a.startswith(fac + "_"))
        out += [f"## {fac} — {len(members)} actors", "",
                "| actor | src | hp now | hp -> | speed now | speed -> | range now | range -> "
                "| dps now | dps -> | cost now | cost -> |",
                "|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|"]
        for a in members:
            rows = attached.get(a)
            c = crows[a]
            if not rows:
                out.append(f"| `{a}` | **0** | " + " | ".join(
                    [f"{c.get(s) or 0:,.0f}" + " | —" for s in STATS]) + " |")
                continue
            cells, nsrc = [], 0
            for s in STATS:
                _, t, n = target_for(rows, c, s, dist, cdist)
                nsrc = max(nsrc, n)
                now = c.get(s)
                cells.append(f"{now:,.0f}" if now else "—")
                cells.append(f"**{t:,.0f}**" if t else "—")
            out.append(f"| `{a}` | {nsrc} | " + " | ".join(cells) + " |")
        out.append("")

    text = "\n".join(out)
    if args.md:
        p = ROOT / args.md
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.md}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
