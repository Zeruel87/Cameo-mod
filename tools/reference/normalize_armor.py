#!/usr/bin/env python3
"""normalize_armor.py — put every source's armor profile onto Cameo's four ladders.

Implements maintainer ruling R8 (2026-09-05), recorded in
`docs/design/REFERENCE_EXTRACTION_PLAN.md`:

    Every value a peer actually declares is a FIXED ANCHOR on its ladder; rungs between two
    anchors are interpolated; beyond the outermost anchor the value is held flat. A peer that
    declares only ONE rung on a ladder votes flat and is downgraded to low confidence.

⛔ The rejected alternative, recorded so it is not revisited: distributing a peer's value across
the rungs using Cameo's own §12.0i bell would give a full smooth profile every time, but it would
inject Cameo's own shape into what is supposed to be an INDEPENDENT outside voice — the reference
would then be partly a measurement of ourselves. Nothing here uses a Cameo curve.

HOW A TAG FINDS ITS RUNG. `docs/reference/peer_armor_map.yaml` maps a source's tag to a LADDER,
not to a rung, because most peers ship five or six tags total and claiming rung-level precision
would be a precision no peer has. So:

  * if the tag's NAME matches a rung on that ladder (`Light` -> VEH's `Light`), it anchors there;
  * otherwise it is LADDER-WIDE (Combined Arms' single `Aircraft` covers all of AIR) and votes
    flat across the ladder at low confidence.

Only `high` and `medium` confidence sources vote, per the map's own rule.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
MAP = ROOT / "docs" / "reference" / "peer_armor_map.yaml"

LADDERS = {
    "INF": ["None", "Flak", "Plate", "Heroic"],
    "VEH": ["Scout", "Light", "Medium", "Heavy", "Superheavy"],
    "AIR": ["Fighter", "Bomber", "Helicopter", "Spaceship"],
    "BLD": ["Wood", "Concrete", "Steel"],
}

# The INI sources are not in peer_armor_map.yaml — that file covers the OpenRA peers. RA2/YR's
# eleven slots are very nearly NAME-IDENTICAL to Cameo's own set, because Cameo's armor descends
# from the Attacque Superior lineage which descends from RA2. That makes them high confidence.
# `special_1`/`special_2` are per-mod scratch slots with no stable meaning — excluded.
INI_MAPS = {
    "ra2": {"confidence": "high",
            "map": {"none": "INF", "flak": "INF", "plate": "INF",
                    "light": "VEH", "medium": "VEH", "heavy": "VEH",
                    "wood": "BLD", "concrete": "BLD", "steel": "BLD",
                    "special_1": None, "special_2": None}},
    # Tiberian Sun ships five, and `light`/`heavy` are its whole vehicle ladder.
    "ts":  {"confidence": "medium",
            "map": {"none": "INF", "wood": "BLD", "concrete": "BLD",
                    "light": "VEH", "heavy": "VEH"}},
}

VOTING = ("high", "medium")


def load_map() -> dict:
    """Read the hand-authored peer map through a real YAML parser.

    A hand-rolled reader was tried first and got two things wrong that matter: it only handled
    INLINE `map: {...}` and so read Romanov's Vengeance — the highest-confidence source in the
    file — as ZERO tags, and it could not follow the anchors/aliases (`Valiant Shades:
    *as_lineage`, `OpenRA Tiberian Dawn: *westwood`) that give four sources their mapping.
    CLAUDE.md's rule against hand-parsing yaml applies to our own files too. `extract_peer_units.py`
    in this same folder already depends on PyYAML, so this adds nothing new.
    """
    import yaml
    doc = yaml.safe_load(MAP.read_text(encoding="utf-8")) or {}
    out: dict[str, dict] = {}
    for name, spec in (doc.get("sources") or {}).items():
        if not isinstance(spec, dict):
            continue
        # A YAML `None:` key parses to Python None — it is the armor tag "None", not a null key.
        tags = {("None" if k is None else str(k)): v for k, v in (spec.get("map") or {}).items()}
        out[str(name)] = {"confidence": spec.get("confidence"), "map": tags}
    return out


def place(profile: dict, tagmap: dict) -> dict[str, dict]:
    """Group a source's {tag: value} onto ladders, splitting rung-anchored from ladder-wide."""
    out: dict[str, dict] = {}
    for tag, value in profile.items():
        ladder = tagmap.get(tag) or tagmap.get(tag.lower()) or tagmap.get(tag.capitalize())
        if not ladder or ladder not in LADDERS:
            continue
        slot = out.setdefault(ladder, {"anchors": {}, "wide": []})
        rungs = LADDERS[ladder]
        match = next((r for r in rungs if r.lower() == tag.lower()), None)
        if match:
            slot["anchors"][rungs.index(match)] = float(value)
        else:
            slot["wide"].append(float(value))
    return out


def interpolate(rungs: list[str], anchors: dict[int, float]) -> list[float]:
    """R8: interpolate between anchors, hold flat beyond the outermost."""
    idx = sorted(anchors)
    out: list[float] = []
    for i in range(len(rungs)):
        if i in anchors:
            out.append(anchors[i])
        elif i < idx[0]:
            out.append(anchors[idx[0]])            # flat below the lowest anchor
        elif i > idx[-1]:
            out.append(anchors[idx[-1]])           # flat above the highest
        else:
            lo = max(j for j in idx if j < i)
            hi = min(j for j in idx if j > i)
            t = (i - lo) / (hi - lo)
            out.append(anchors[lo] + t * (anchors[hi] - anchors[lo]))
    return out


def normalize(profile: dict, tagmap: dict, confidence: str) -> dict:
    """One source's armor profile -> {ladder: {rung: value}} with a per-ladder confidence."""
    placed = place(profile, tagmap)
    result: dict[str, dict] = {}
    for ladder, slot in placed.items():
        rungs = LADDERS[ladder]
        anchors, wide = slot["anchors"], slot["wide"]
        if len(anchors) >= 2:
            vals, conf, how = interpolate(rungs, anchors), confidence, "interpolated"
        elif len(anchors) == 1:
            only = next(iter(anchors.values()))
            vals, conf, how = [only] * len(rungs), "low", "flat_single_anchor"
        elif wide:
            avg = sum(wide) / len(wide)
            vals, conf, how = [avg] * len(rungs), "low", "flat_ladder_wide"
        else:
            continue
        result[ladder] = {
            "values": {r: round(v, 2) for r, v in zip(rungs, vals)},
            "confidence": conf,
            "method": how,
            "anchored_rungs": [rungs[i] for i in sorted(anchors)],
        }
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="docs/reference/ini_corpus.json")
    ap.add_argument("--json", help="write normalized armor profiles here")
    ap.add_argument("--sample", type=int, default=4)
    args = ap.parse_args()

    peer_map = load_map()
    print(f"peer map: {len(peer_map)} sources")
    for name, spec in sorted(peer_map.items()):
        vote = "VOTES" if spec["confidence"] in VOTING else "silent"
        print(f"   {name:<24} {str(spec['confidence']):<8} {vote:<7} {len(spec['map'])} tags")

    corpus = pathlib.Path(args.corpus)
    if not corpus.exists():
        print(f"\n  no corpus at {corpus}", file=sys.stderr)
        return 1

    out_rows, stats = [], {"normalized": 0, "skipped_no_profile": 0, "by_method": {}}
    for line in corpus.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        prof = r.get("w_versus")
        if not prof:
            stats["skipped_no_profile"] += 1
            continue
        engine = r.get("engine", "ra2")
        spec = INI_MAPS.get(engine)
        if not spec or spec["confidence"] not in VOTING:
            continue
        norm = normalize(prof, spec["map"], spec["confidence"])
        if not norm:
            continue
        stats["normalized"] += 1
        for ladder, v in norm.items():
            stats["by_method"][v["method"]] = stats["by_method"].get(v["method"], 0) + 1
        out_rows.append({"source": r["source"], "id": r["id"], "warhead": r.get("w_warhead"),
                         "ladders": norm})

    print(f"\nnormalized {stats['normalized']} armor profiles "
          f"({stats['skipped_no_profile']} rows had none)")
    print("  per-ladder method counts:")
    for k, v in sorted(stats["by_method"].items(), key=lambda kv: -kv[1]):
        print(f"     {k:<22} {v}")

    for r in out_rows[:args.sample]:
        print(f"\n  {r['source']} / {r['id']} / {r['warhead']}")
        for ladder, v in r["ladders"].items():
            print(f"     {ladder:<4} {v['method']:<20} conf={v['confidence']:<6} "
                  f"anchors={v['anchored_rungs']}")
            print(f"          {v['values']}")

    if args.json:
        out = pathlib.Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(json.dumps(r, sort_keys=True, separators=(",", ":"))
                                 for r in out_rows) + "\n", encoding="utf-8")
        print(f"\n  wrote {out}  ({len(out_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
