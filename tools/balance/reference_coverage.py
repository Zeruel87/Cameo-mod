#!/usr/bin/env python3
"""reference_coverage.py — every empty slot in the reference map, and WHY it is empty.

⛔ THE QUESTION THIS ANSWERS, and the one it refuses to answer. Asked to make "all references
used", the first instinct is to fill blanks. The arithmetic says that is not a goal anyone can
reach, and saying so precisely is more useful than a map that hides it:

    reference rows in the corpus                                      4,748
    rows a routed Cameo actor of the SAME TYPE can even see           2,216
    assignments clauses 2+3 permit at all (actor x routed source)     1,867
    assignments that exist today                                        834

"Every reference used" needs >= 4,748 assignments and the ceiling is 1,867, so 2,530 rows can
never be claimed by anybody — not because the matcher failed but because no routed Cameo faction
fields a unit of that type. Romanov's Vengeance alone contributes 614 of them: it ships a full
RA2 navy and the RA2 Cameo factions have almost no ships. That is a CONTENT fact, and no amount
of matching changes it.

So the real question is the one underneath: of the slots that COULD be filled, which are empty
and why? Those split into populations that want completely different work, and lumping them
together is what makes "410 actors have no reference" read as one big failure:

  NO CANDIDATE     nothing of this actor's type in the routed pool. Content, not matching.
  NOT NAME-BACKED  candidates existed and every one was SHAPE or WEAK, so `drop_unbacked_shape`
                   refused them all. ⭐ THIS IS THE RESOLVABLE POPULATION — the maintainer's
                   own ruling ("an empty slot is a question; a Mobile Repair Ship is a wrong
                   answer that will be silently averaged into a price"). Each one is either a
                   naming alias nobody has taught the matcher, or a genuine absence.
  TAKEN            a name-backed candidate existed and another actor of the same faction got it
                   first (clause 3). Contested — a real ranking decision.
  UNROUTED         the faction has no route to any source at all: formula-only by clause 11.

Read-only. Writes nothing.

    python tools/balance/reference_coverage.py              # the summary
    python tools/balance/reference_coverage.py --json out.json
    python tools/balance/reference_coverage.py --faction td_gdi
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import assign_references as ar        # noqa: E402
import faction_routes as fr           # noqa: E402
import reference_distribution as rd   # noqa: E402


def measure():
    """The whole picture in one pass, so every number on the page comes from one run."""
    result, chassis_only, in_scope = ar.assign()
    formula_only = getattr(ar.assign, "formula_only", {})
    shape_only = getattr(ar.assign, "shape_only", {})

    peers = rd.peer_rows() + rd.peer_hero_rows() + rd.peer_variant_rows()
    led = ar.ledger()
    cameo = [c for c in rd.cameo_rows() if c["id"] in led] + \
            [c for c in rd.cameo_hero_rows() if c["id"] in led]

    by_source = collections.defaultdict(list)
    for p in peers:
        by_source[p["source"]].append(p)

    # ── pool utilisation ──────────────────────────────────────────────────────────────────
    used = collections.defaultdict(set)
    for cid, srcs in result.items():
        for src, row in srcs.items():
            used[src].add((row.get("id"), row.get("name")))

    scope = [c for c in cameo if fr.faction_of(c["id"]) and fr.routes_for(fr.faction_of(c["id"]))]
    cam_by_fac_type = collections.defaultdict(list)
    for c in scope:
        cam_by_fac_type[(fr.faction_of(c["id"]), c["type"])].append(c["id"])

    # ⚠ THE CEILING IS TYPE-AWARE OR IT IS FICTION. Counting actor x routed source gives 2,410
    # and quietly assumes an infantry actor can take a naval row. The matcher refuses cross-type
    # outright (§9), so the honest ceiling caps each (faction, source, type) cell at the smaller
    # of the two sides.
    ceiling, reachable = 0, collections.defaultdict(set)
    for fac in sorted({fr.faction_of(c["id"]) for c in scope}):
        for src, _toks in fr.routes_for(fac):
            pool = [p for p in by_source.get(src, ()) if fr.allows(fac, p)]
            types = {p["type"] for p in pool} | {t for (f, t) in cam_by_fac_type if f == fac}
            for typ in types:
                nref = [p for p in pool if p["type"] == typ]
                ncam = cam_by_fac_type.get((fac, typ), [])
                ceiling += min(len(ncam), len(nref))
                if ncam:
                    reachable[src] |= {(p.get("id"), p.get("name")) for p in nref}

    rows = {s: {(p.get("id"), p.get("name")) for p in ps} for s, ps in by_source.items()}
    pool = {"sources": {}, "ceiling": ceiling,
            "rows": sum(len(v) for v in rows.values()),
            "visible": sum(len(reachable.get(s, ())) for s in rows),
            "used": sum(len(used.get(s, ())) for s in rows)}
    for s in sorted(rows, key=lambda s: -len(rows[s])):
        pool["sources"][s] = {"rows": len(rows[s]), "visible": len(reachable.get(s, ())),
                              "used": len(used.get(s, ()))}

    # ── every empty slot, with its cause ──────────────────────────────────────────────────
    blanks = collections.Counter()
    detail = collections.defaultdict(list)
    for c in cameo:
        cid, fac = c["id"], fr.faction_of(c["id"])
        if cid in formula_only or not fac or not fr.routes_for(fac):
            blanks["UNROUTED"] += 1
            detail["UNROUTED"].append((cid, "-", "no route for this faction (clause 11)"))
            continue
        for src, _toks in fr.routes_for(fac):
            if result.get(cid, {}).get(src):
                continue
            same_type = [p for p in by_source.get(src, ())
                         if p["type"] == c["type"] and fr.allows(fac, p)]
            if not same_type:
                blanks["NO CANDIDATE"] += 1
                detail["NO CANDIDATE"].append((cid, src, f"no {c['type']} row in the routed pool"))
            elif src in shape_only.get(cid, {}):
                d = shape_only[cid][src]
                blanks["NOT NAME-BACKED"] += 1
                detail["NOT NAME-BACKED"].append(
                    (cid, src, f"best was {d.get('confidence')} — {d.get('name')}"))
            else:
                blanks["TAKEN"] += 1
                detail["TAKEN"].append((cid, src, "no unclaimed name-backed row left"))

    return {"pool": pool, "blanks": dict(blanks), "detail": {k: v for k, v in detail.items()},
            "result": result, "in_scope": in_scope,
            "chassis_only": len(chassis_only), "formula_only": len(formula_only),
            "variant_filled": getattr(ar.assign, "variant_filled", []),
            "variant_cameo": getattr(ar.assign, "variant_cameo", {})}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", help="write the full measurement to this path")
    ap.add_argument("--faction", help="list this faction's empty slots")
    args = ap.parse_args()

    m = measure()
    p = m["pool"]
    print("# Reference coverage\n")
    print(f"  reference rows in the corpus                    {p['rows']:6d}")
    print(f"  rows a same-type routed Cameo actor can see     {p['visible']:6d}")
    print(f"  assignments clauses 2+3 permit (type-aware)     {p['ceiling']:6d}")
    print(f"  assignments that exist today                    {p['used']:6d}")
    print(f"\n  -> 'every reference used' needs {p['rows']} and the ceiling is {p['ceiling']}: "
          f"{p['rows'] - p['visible']} rows can never be claimed by anybody.\n")

    print(f"{'source':26s} {'rows':>6} {'visible':>8} {'used':>6} {'unreachable':>12}")
    for s, d in p["sources"].items():
        print(f"{s[:26]:26s} {d['rows']:6d} {d['visible']:8d} {d['used']:6d} "
              f"{d['rows'] - d['visible']:12d}")

    print("\n## Empty slots by cause\n")
    for why, n in sorted(m["blanks"].items(), key=lambda kv: -kv[1]):
        print(f"  {n:6d}  {why}")

    if args.faction:
        print(f"\n## {args.faction} — empty slots\n")
        for why, entries in m["detail"].items():
            for cid, src, note in entries:
                if fr.faction_of(cid) == args.faction:
                    print(f"  {why:16s} {cid:36s} {src:22s} {note}")

    if args.json:
        out = {k: v for k, v in m.items() if k != "result"}
        pathlib.Path(args.json).write_text(json.dumps(out, indent=1, default=str),
                                           encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
