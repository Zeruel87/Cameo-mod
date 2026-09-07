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
import faction_routes as fr  # noqa: E402
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
            # The ID is the only reliable key — see the note in assign_references. hp/cost is the
            # fallback for assignments written before the id was recorded.
            best = None
            if rec.get("id"):
                best = next((h for h in hits if h.get("id") == rec["id"]), None)
            if best is None:
                best = next((h for h in hits if h.get("hp") == rec.get("hp")
                             and h.get("cost") == rec.get("cost")), hits[0])
            rows.append(best)
        if rows:
            out[actor] = rows
    return out


# ⭐ FAMILY MEMBERS THAT DO NOT SHARE THE ID STEM (maintainer, 2026-09-07). The family rule finds
# `4TNK.ATOMIC` and `4TNK.ERAD` from `4TNK` because Combined Arms suffixes the variant onto the
# base id. It cannot find the Apocalypse or the Overlord, which are the SAME tier of Soviet super-
# heavy under their own names, and the maintainer wants them counted with the rest. Named rows
# only — this is a list of units, not a pattern anyone can widen by accident.
FAMILY_EXTRA = {
    ("ra1_soviets_siegemammothtank", "Combined Arms"): ("APOC", "OVLD"),
    # GDI's super-heavy tier is split across two chassis names: the Mammoth line and the Titan
    # walkers. Both are 110,000 HP / 2,000cr in Combined Arms and both belong with the Mk III.
    # ⚠ `allows("td_gdi", TITN)` currently returns FALSE — CA's broad faction tagging denies GDI
    # its own walker — so these rows are unreachable through routing and can only arrive here.
    # That is a symptom, not a fix: EMBER owns the CA over-tagging, and when it is corrected these
    # two entries should be re-checked to see whether the family rule finds them unaided.
    ("td_gdi_mammothtankmkiii", "Combined Arms"): ("TITN", "TITN.RAIL"),
}


def expand_families(attached, peers):
    """Replace each assigned row with its whole variant family from that source."""
    by_source = collections.defaultdict(list)
    for p in peers:
        by_source[p["source"]].append(p)
    out = {}
    for actor, rows in attached.items():
        faction = fr.faction_of(actor)
        grown, seen = [], set()
        for r in rows:
            for f in family_rows(r, by_source, faction):
                key = (f["source"], f.get("id"), f.get("name"))
                if key in seen:
                    continue
                seen.add(key)
                grown.append(f)
        for (a_id, src), ids in FAMILY_EXTRA.items():
            if a_id != actor:
                continue
            for extra in by_source.get(src, ()):
                if (extra.get("id") or "").upper() not in ids:
                    continue
                key = (extra["source"], extra.get("id"), extra.get("name"))
                if key not in seen:
                    seen.add(key)
                    grown.append(extra)
        out[actor] = grown
    return out


def family_rows(assigned, peers_by_source, faction):
    """Every VARIANT of the assigned reference, from that same source — one voice between them.

    ⛔ MAINTAINER 2026-09-07: *"if more than one variant exists just use all of them as reference
    since they would otherwise not be mapped... but weight it still only the mean from CA as one
    voice compared to our existing Cameo one."*

    Combined Arms routes FOUR mammoths to GDI — `HTNK`, `HTNK.Hover`, `HTNK.Ion`, `HTNK.Drone` —
    and clause 2 lets an actor take only one per source, so three of them describe nothing and a
    Cameo add-on above the Mammoth has almost no evidence to sit on. Taking all four and averaging
    them inside the source keeps R4 intact: Combined Arms still casts ONE vote, it is just a better
    informed one.

    The grouping signal is the mod's own naming, not a similarity guess: these mods suffix a
    variant onto the base actor id after a dot, so `HTNK.Ion` belongs to `HTNK`. A row is admitted
    only if routing already allows this faction to see it.
    """
    base = (assigned.get("id") or "").split(".")[0]
    if not base:
        return [assigned]
    out = [r for r in peers_by_source.get(assigned["source"], ())
           if (r.get("id") or "").split(".")[0] == base and fr.allows(faction, r)]
    # ⚠ DTA ships AI duplicates of its own units (`AIHTNK`, `AIHTNK2`) with identical stats.
    # They are not variants and must not weight the source's mean toward one design twice.
    seen, uniq = set(), []
    for r in out:
        key = (r.get("name"), r.get("hp"), r.get("cost"), r.get("w_damage"))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    return uniq or [assigned]


def target_for(rows, cameo_row, stat, dist, cdist):
    """(peers_only, with_cameo, n_sources) on one stat, or (None, None, 0).

    ⭐ POOLED PER SOURCE FIRST. Every source casts exactly ONE vote however many of its rows are
    in play, so a mod that happens to ship four variants of a unit cannot outvote one that ships
    a single unit. Without this, expanding to variant families would quietly re-weight R4.
    """
    per_source = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        x = r.get(stat)
        if not x or x <= 0:
            continue
        for pop in ("overall", r["type"]):
            agg = dist.get(r["source"], {}).get(pop, {}).get(stat)
            for k, v in rd.coordinates(float(x), agg).items():
                per_source[r["source"]][(pop, k)].append(v)
    pooled, used = collections.defaultdict(list), set()
    for source, coords in per_source.items():
        used.add(source)
        for key, vals in coords.items():
            # p_rng is a bounded position and averages arithmetically; the rest are ratios.
            pooled[key].append(statistics.fmean(vals) if key[1] == "p_rng" else rd.gm(vals))
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
    attached = expand_families(attach(assignment, peer_index(peers)), peers)
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
        p.write_text(text.rstrip() + "\n", encoding="utf-8")
        print(f"wrote {args.md}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
