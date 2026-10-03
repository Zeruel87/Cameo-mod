#!/usr/bin/env python3
"""Match reference warhead groups to Cameo families by Versus shape — A MEASURED DEAD END.

⛔ READ THIS BEFORE USING THE OUTPUT. Shape matching DOES NOT WORK for family assignment, and
this file is kept because proving that took a day and the harness is what proves it. Its
`--validate` is the evidence; its `--all` output is NOT an assignment and must never be written
into `warhead_family_assignment.yaml`.

    propagate_families   group -> family by delivery/element/band triple      19%  (R39)
    fit_families         group -> family by nearest Versus shape               2%  (R40)
    ...the same, plus a delivery-compatibility penalty                        4-6%  (R40)

THE REASON IS STRUCTURAL, NOT A BUG. Two measurements, either one fatal:

  1. **Cameo's family shapes are not distinguishable.** Over the 150 live templates, 27 PAIRS sit
     closer than 0.05 RMS log distance and `Magic` / `Sonic` have IDENTICAL centroids (0.000).
     Nearest-neighbour among 51 families is then a coin flip inside a cluster of near-duplicates,
     whatever the query.

  2. **The target table is already made of the thing being matched to it.** Cameo's shipped Versus
     rows come from `docs/reference/family_profiles.json` — the reference corpus — via
     `gen_weapon_template.py`. Matching reference groups against them is CIRCULAR where a family
     was measured, and meaningless where it was not, because the generator's fallback for an
     unmeasured family is `table()`, a LINEAR RAMP. Of the 51 live families, **10 are
     reference-derived, 8 are hand-designed (`docs/design/invented_family_profiles.json`), and 33
     — nearly two thirds — are that linear ramp.** The ramps are why `Magic` and `Sonic` coincide:
     they are the same generated ladder at the same level.

⭐ WHAT THIS MAKES THE REAL TASK. Finding (2) is not an obstacle, it is the deliverable. The
reference pipeline exists to REPLACE those 33 ramps with measured profiles. The unit of work is
therefore the CAMEO FAMILY (51 rows), which is exactly the maintainer's "drive from Cameo's
families outward" — not the 1,712 reference groups. Routing runs family -> groups by categorical
identity (a `MissileCryo` is delivery Missile, element Cryo), which is tractable, rather than
group -> family by resemblance, which is not.

`family_profiles.json` shipped its 10 families under `min_rows: 8, min_mods: 3` from an older
extractor (`propose_family_profiles.py` over `survey_platforms.py`, which reads `~/Downloads` and
runs on one machine). The current pipeline has 20 sources and 1,712 groups at tau 0.20, so that
gate should now clear for many more families.

WHAT IS STILL USEFUL HERE:
  * `split_template()`  — the family/level parser, which must locate the LEVEL token (see below).
  * `cameo_families()`  — every live template as a shape on Cameo's 16 rungs, via `map_row`.
  * `--validate`        — the held-out score against the maintainer's 118 reviewed CA groups.

    python tools/reference/fit_families.py --validate      # reproduce the 2% result
    python tools/reference/fit_families.py --source X      # inspect one source (diagnostic only)
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "reference"))

import armor_interpolate as ai  # noqa: E402
import cameo_families as cf  # noqa: E402
import warhead_matrix as wm  # noqa: E402

GROUPS = ROOT / "docs" / "reference" / "warhead_groups.json"
DOC = ROOT / "docs" / "reference" / "warhead_family_assignment.yaml"
OUT = ROOT / "docs" / "reference" / "warhead_family_fit.json"

# A distance needs this many shared rungs before it means anything. Below it, two profiles can
# agree on a handful of cells by accident: a source that only ever states an infantry opinion
# would otherwise "match" every family that happens to tilt the same way on three rungs.
MIN_SHARED_RUNGS = 6

# Above this RMS log distance the nearest family is not a resemblance, it is just the closest of
# a bad set. 0.50 is one e-fold of average per-rung disagreement -- the same scale `tau` uses for
# clustering, where it was chosen as "well below a real profile difference".
MAX_ACCEPTABLE_DISTANCE = 0.50

# Sources that are not fitted, and why.
SKIP = {
    "cameo": "IS the target table -- a `^Warhead_<Family>_<Level>` template is its own family (R37)",
    "d2k_mod": "a transcribed table with no actors; it votes on the armour ladder only (R38)",
}


# The template name is `^Warhead_<Family>_<Level>[_<Variant>]` and the parser lives in
# `cameo_families`; see its docstring for why splitting on the last underscore is wrong.
LEVELS = cf.LEVELS


def split_template(name: str) -> tuple:
    """`^Warhead_CannonHE_Heavy_D2K_DevBullet` -> ("CannonHE", "Heavy")."""
    family, level, _variant = cf.split_template(name)
    return family, level


def normalise(profile: dict) -> dict:
    """Re-express a profile as pure shape: positive cells only, geometric mean 1."""
    cells = {k: v for k, v in profile.items() if isinstance(v, (int, float)) and v > 0}
    if not cells:
        return {}
    centre = wm.gmean(list(cells.values()))
    if not centre or centre != centre:
        return {}
    return {k: v / centre for k, v in cells.items()}


def distance(a: dict, b: dict):
    """RMS log difference over the rungs both profiles state. None if too few overlap."""
    shared = [k for k in a if k in b]
    if len(shared) < MIN_SHARED_RUNGS:
        return None
    diffs = [math.log(a[k] / b[k]) for k in shared]
    return math.sqrt(sum(d * d for d in diffs) / len(diffs))


def cameo_families(data: dict) -> list:
    """[(family, level, shape, uses)] from Cameo's own `^Warhead_<Family>_<Level>` templates.

    Pushed through `map_row` like every reference row, so both sides of the comparison have been
    through identical machinery. A template whose profile does not survive normalisation (an
    all-zero or single-cell row) is dropped rather than matched against.
    """
    entry = data["cameo"]
    armors = entry["armors"]
    out = []
    for row in entry["rows"]:
        name = row["weapon"]
        if not name.startswith("^Warhead_"):
            continue
        family, level = split_template(name)
        try:
            mapped = ai.map_row("cameo", armors, row["values"])
        except KeyError:
            continue
        shape = normalise(mapped)
        if len(shape) >= MIN_SHARED_RUNGS:
            out.append((family, level, shape, row.get("uses", 0)))
    return out


def fit_source(sid: str, groups: list, reference: list) -> list:
    """Assign every group of one source to its nearest Cameo family."""
    rows = []
    for group in groups:
        try:
            mapped = ai.map_row(sid, group["armors"], group.get("profile") or [])
        except KeyError as exc:
            rows.append({"group": group["name"], "family": "?", "status": "proposed",
                         "why": f"armour not anchored: {exc}", "uses": group["uses"],
                         "weapons": group["weapons"]})
            continue
        shape = normalise(mapped)
        ranked = sorted(
            (d, fam, lvl) for fam, lvl, ref, _ in reference
            if (d := distance(shape, ref)) is not None
        )
        if not ranked:
            rows.append({"group": group["name"], "family": "?", "status": "proposed",
                         "why": f"profile states fewer than {MIN_SHARED_RUNGS} comparable rungs",
                         "uses": group["uses"], "weapons": group["weapons"]})
            continue

        best_d, best_fam, best_lvl = ranked[0]
        # Collapse the ranking to families, keeping each family's best distance, so the runner-up
        # is a different FAMILY and not merely the same family at another level.
        by_family: dict = {}
        for d, fam, _lvl in ranked:
            if fam not in by_family:
                by_family[fam] = d
        others = [(f, d) for f, d in by_family.items() if f != best_fam]
        margin = (others[0][1] - best_d) if others else float("inf")

        rows.append({
            "group": group["name"],
            "family": best_fam if best_d <= MAX_ACCEPTABLE_DISTANCE else "?",
            "status": "proposed",
            "level_hint": best_lvl,
            "distance": round(best_d, 3),
            "margin": round(margin, 3) if margin != float("inf") else None,
            "why": ("nearest Cameo family by measured shape"
                    if best_d <= MAX_ACCEPTABLE_DISTANCE
                    else f"nearest family is {best_d:.2f} away, beyond {MAX_ACCEPTABLE_DISTANCE}"),
            "runners_up": {f: round(d, 3) for f, d in sorted(others, key=lambda x: x[1])[:3]},
            "delivery": group.get("delivery"), "element": group.get("element"),
            "band": group.get("band"), "uses": group["uses"],
            "factor": group.get("factor"),
            "weapons": group["weapons"],
        })
    return rows


def validate(data: dict, groups_all: dict, reference: list) -> str:
    """Score the fit against the 118 Combined Arms groups the maintainer reviewed by hand."""
    import yaml
    doc = yaml.safe_load(DOC.read_text(encoding="utf-8"))
    reviewed = {name: row["family"] for name, row in doc["groups"].items()}
    rows = fit_source("combined_arms", groups_all["combined_arms"]["groups"], reference)

    hits = total = unmatched = 0
    misses = []
    for row in rows:
        actual = reviewed.get(row["group"])
        if actual is None:
            continue
        total += 1
        if row["family"] == "?":
            unmatched += 1
            misses.append((row["uses"], row["group"], "(no match)", actual, row.get("distance")))
        elif row["family"] == actual:
            hits += 1
        else:
            misses.append((row["uses"], row["group"], row["family"], actual, row.get("distance")))

    lines = ["## Shape fit scored against the maintainer's Combined Arms review", "",
             "⚠ NOT a held-out test, and that is the point (R40): Cameo's shipped Versus rows",
             "come from the reference corpus via `family_profiles.json`, so for the 10 measured",
             "families this is partly circular -- and it STILL scores near zero, because 33 of the",
             "51 families carry a generated linear ramp that resembles every query equally.", "",
             f"scored     : {total} reviewed groups",
             f"top-1      : {hits} correct ({hits / max(total, 1):.0%})",
             f"no match   : {unmatched} beyond the {MAX_ACCEPTABLE_DISTANCE} distance cutoff",
             f"baseline   : 19% (propagation by delivery/element/band, R39)", ""]
    if misses:
        lines += ["| uses | group | fitted | reviewed | distance |", "|--:|---|---|---|--:|"]
        for uses, name, got, want, dist in sorted(misses, reverse=True)[:20]:
            lines.append(f"| {uses} | `{name}` | {got} | {want} | "
                         f"{dist if dist is not None else '-'} |")
    return "\n".join(lines)


def report(sid: str, rows: list) -> str:
    matched = [r for r in rows if r["family"] != "?"]
    lines = [f"### `{sid}` — {len(matched)} of {len(rows)} groups fitted", "",
             "| uses | group | family | level hint | dist | margin | runner-up |",
             "|--:|---|---|---|--:|--:|---|"]
    for row in sorted(rows, key=lambda r: -r["uses"])[:40]:
        runner = next(iter(row.get("runners_up") or {}), "-")
        lines.append(f"| {row['uses']} | `{row['group']}` | {row['family']} | "
                     f"{row.get('level_hint') or '-'} | {row.get('distance', '-')} | "
                     f"{row.get('margin', '-')} | {runner} |")
    if len(rows) > 40:
        lines.append(f"| … | | | | | | _{len(rows) - 40} more_ |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default="combined_arms")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    data = wm.collect()
    groups_all = json.load(GROUPS.open(encoding="utf-8"))
    reference = cameo_families(data)
    print(f"Cameo target table: {len(reference)} templates, "
          f"{len({f for f, _, _, _ in reference})} distinct families\n")

    if args.validate:
        print(validate(data, groups_all, reference))
        return 0

    targets = [s for s in groups_all if s not in SKIP] if args.all else [args.source]
    out = {}
    for sid in targets:
        if sid not in groups_all:
            print(f"unknown source {sid}")
            return 2
        rows = fit_source(sid, groups_all[sid]["groups"], reference)
        out[sid] = {"groups": rows,
                    "fitted": sum(1 for r in rows if r["family"] != "?"),
                    "total": len(rows)}
        print(report(sid, rows))
        print()

    if args.all:
        fitted = sum(v["fitted"] for v in out.values())
        total = sum(v["total"] for v in out.values())
        print(f"**{fitted} of {total} groups fitted ({fitted / max(total, 1):.0%}).** "
              f"Every row is `proposed` and awaits review.")
    if args.write:
        OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=float) + "\n",
                       encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
