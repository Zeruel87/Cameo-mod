#!/usr/bin/env python3
"""W13 step 1 — cluster the 2494-profile reference corpus into ARCHETYPES.

`extract_versus.py` gathered the raw profiles. This turns them into the thing
the warhead rebuild actually needs: **for each archetype, the median profile of
the mods that ship it** — never a global average.

W13 rule 4 is the whole reason this file exists. Averaging all three-class
profiles collapses the span to **24** against a field median of **87**: it
produces one mushy all-rounder and destroys exactly the rock-paper-scissors the
corpus was gathered to build. So every statistic here is a median WITHIN a
cluster, and the cluster key is the archetype.

    python tools/reference/cluster_versus.py                # summary
    python tools/reference/cluster_versus.py --write        # + markdown report
    python tools/reference/cluster_versus.py --archetype "INF>VEH>BLD sharp HE"

**Archetype = macro order x sharp/flat x HE/AP direction** (W13 rule 2).

⚠ **The air axis cannot come from this corpus.** The source engines share one
armor type between aircraft and ground vehicles, so 1348 of the 2494 rows use
the classic 11-armor set with no aircraft entry at all. Cameo's four dedicated
aircraft armors are a deliberate improvement (W13 rule 8), which means the air
POSITION of every archetype is a Cameo design decision, not a measurement. This
tool reports the ground archetype and says so rather than inventing an air value.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import statistics
import sys
from warhead_source_selection import selected_sources

ROOT = pathlib.Path(__file__).resolve().parents[2]
CORPUS = ROOT / "docs" / "reference" / "versus_raw.json"
OUT = ROOT / "docs" / "reference" / "versus_archetypes.md"

# Source armor vocabulary -> Cameo macro type. The classic Westwood 11-armor set
# (none/flak/plate/light/medium/heavy/wood/steel/concrete/drone/special) covers
# 1348 rows on its own; the rest are per-mod extras.
MACRO = {
    "none": "INF", "flak": "INF", "plate": "INF", "infantry": "INF",
    "light": "VEH", "medium": "VEH", "heavy": "VEH", "harvester": "VEH",
    "wood": "BLD", "steel": "BLD", "concrete": "BLD", "brick": "BLD",
    "building": "BLD", "defense": "BLD", "cy": "BLD",
    "aircraft": "AIR",
}
# Deliberately unmapped: `drone`, `special`, `rocket`, `invulnerable`. They are
# per-mod scratch armors with no stable meaning across sources — folding them
# into a macro type would corrupt the very medians this file exists to produce.

# Within a macro type, lightest -> heaviest, matching gen_weapon_template.LADDERS.
WEIGHT_ORDER = {
    "INF": ["none", "flak", "plate", "infantry"],
    "VEH": ["light", "medium", "heavy", "harvester"],
    "BLD": ["wood", "steel", "concrete", "brick", "building", "defense", "cy"],
}

# Span bands. "Sharp" is a real counter; "flat" is a deliberate all-rounder.
SHARP_MIN = 60
FLAT_MAX = 25

# ⚠ NOT every warhead in the corpus is a damage profile. 182 rows (7.3%) are
# ALL-ZERO and another 186 peak at <=5: death animations (`AvatarDeathWH`),
# dummies (`BioDummyWH`), repair guns, de-evolution and EMP-only effects. They
# carry no counter information at all, and counting them as "flat" is what makes
# the flat band look like a design choice when it is mostly plumbing.
# Everything here is measured on DAMAGE profiles only.
DAMAGE_FLOOR = 5


def macro_means(versus: dict) -> dict[str, float]:
    """Mean value per macro type, over the armors the row actually defines."""
    buckets: dict[str, list[float]] = collections.defaultdict(list)
    for armor, value in versus.items():
        macro = MACRO.get(armor.lower())
        if macro:
            buckets[macro].append(float(value))
    return {m: statistics.fmean(v) for m, v in buckets.items() if v}


def direction(versus: dict) -> str | None:
    """HE (better vs LIGHT armor) or AP (better vs HEAVY), measured on the
    vehicle ladder — the only ladder every source populates consistently."""
    vals = []
    for armor in WEIGHT_ORDER["VEH"][:3]:            # light, medium, heavy
        if armor in versus:
            vals.append(float(versus[armor]))
    if len(vals) < 2:
        return None
    if abs(vals[0] - vals[-1]) < 5:                  # flat across the ladder
        return "="
    return "HE" if vals[0] > vals[-1] else "AP"


def sharpness(span: float) -> str:
    if span >= SHARP_MIN:
        return "sharp"
    if span <= FLAT_MAX:
        return "flat"
    return "moderate"


def classify(row: dict) -> dict | None:
    versus = {k.lower(): v for k, v in (row.get("versus") or {}).items()}
    if not versus:
        return None
    if max(float(v) for v in versus.values()) <= DAMAGE_FLOOR:
        return None                                  # utility warhead, not a profile
    means = macro_means(versus)
    ground = {m: v for m, v in means.items() if m in ("INF", "VEH", "BLD")}
    if len(ground) < 2:                              # too thin to place
        return None
    order = ">".join(sorted(ground, key=lambda m: -ground[m]))
    values = [float(v) for v in versus.values()]
    span = max(values) - min(values)
    return {
        "warhead": row.get("warhead"),
        "order": order,
        "span": span,
        "sharp": sharpness(span),
        "dir": direction(versus) or "?",
        "means": means,
        "arity": row.get("arity"),
        "has_air": "AIR" in means,
    }


def load() -> list[dict]:
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    out = []
    for sid, entry in selected_sources(data["sources"]).items():
        for row in entry["rows"]:
            c = classify(row)
            if c:
                c["source"] = sid
                c["lineage"] = entry["lineage"]
                out.append(c)
    return out


def cluster(rows: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        groups[f"{r['order']} {r['sharp']} {r['dir']}"].append(r)
    return groups


def profile_of(members: list[dict]) -> dict:
    """The archetype's target profile: the MEDIAN per macro type across the mods
    that ship this archetype (rule 4 — median within the cluster, never a global
    average), plus how many distinct sources back it."""
    per_source = collections.defaultdict(lambda: collections.defaultdict(list))
    source_spans = collections.defaultdict(list)
    for m in members:
        for macro, value in m["means"].items():
            per_source[m["source"]][macro].append(value)
        source_spans[m["source"]].append(m["span"])
    per_macro: dict[str, list[float]] = collections.defaultdict(list)
    for values in per_source.values():
        for macro, samples in values.items():
            per_macro[macro].append(statistics.median(samples))
    return {
        "n": len(members),
        "sources": len({m["source"] for m in members}),
        "median_span": statistics.median([statistics.median(v) for v in source_spans.values()]),
        "macro": {k: round(statistics.median(v), 1) for k, v in sorted(per_macro.items())},
        "weighting": "median within each source, then equal-source median; source lineage independence not implied",
    }


def render(rows: list[dict], groups: dict[str, list[dict]]) -> str:
    total = len(rows)
    air = sum(1 for r in rows if r["has_air"])
    lines = [
        "# W13 — reference archetypes (clustered, never averaged)",
        "",
        "Generated by `tools/reference/cluster_versus.py` from",
        "`docs/reference/versus_raw.json`. **Every number is a median WITHIN a",
        "cluster.** Averaging the whole corpus gives span 24 against a field median",
        "of 87 — it deletes the rock-paper-scissors (W13 rule 4).",
        "",
        f"- profiles placed: **{total}**",
        f"- archetypes occupied by the field: **{len(groups)}**",
        f"- profiles that define ANY aircraft armor: **{air}** "
        f"({air / total:.1%}) — see the air caveat below",
        "",
        "## ⚠ The air axis is not measurable here",
        "",
        "The source engines share one armor type between aircraft and ground",
        "vehicles, so the corpus simply cannot express \"devastating vs aircraft,",
        "mediocre vs tanks\". Cameo's four dedicated aircraft armors are a",
        "deliberate improvement (W13 rule 8), which makes each archetype's AIR",
        "position a **design decision for the maintainer**, not a measurement.",
        "Everything below is therefore the GROUND archetype.",
        "",
        "## Archetypes by weight",
        "",
        "| archetype | n | sources | median span | INF | VEH | BLD |",
        "|---|--:|--:|--:|--:|--:|--:|",
    ]
    for key, members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        p = profile_of(members)
        m = p["macro"]
        lines.append(
            f"| `{key}` | {p['n']} | {p['sources']} | {p['median_span']:.0f} | "
            f"{m.get('INF', '—')} | {m.get('VEH', '—')} | {m.get('BLD', '—')} |")
    lines += ["", "## Distribution", ""]
    for label, counter in (("sharpness", collections.Counter(r["sharp"] for r in rows)),
                           ("direction", collections.Counter(r["dir"] for r in rows))):
        parts = ", ".join(f"{k} {v} ({v / total:.0%})"
                          for k, v in counter.most_common())
        lines.append(f"- **{label}**: {parts}")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help=f"write {OUT.relative_to(ROOT)}")
    ap.add_argument("--archetype", help="show the members of one archetype")
    args = ap.parse_args()

    if not CORPUS.exists():
        print(f"missing {CORPUS.relative_to(ROOT)} — run extract_versus.py first")
        return 1
    rows = load()
    groups = cluster(rows)

    if args.archetype:
        members = groups.get(args.archetype)
        if not members:
            print(f"no such archetype: {args.archetype}")
            print("known:", ", ".join(sorted(groups)[:12]), "...")
            return 1
        p = profile_of(members)
        print(f"{args.archetype}: {p['n']} profiles from {p['sources']} sources, "
              f"median span {p['median_span']:.0f}, macro medians {p['macro']}")
        for m in sorted(members, key=lambda m: -m["span"])[:25]:
            print(f"  {m['source']:20} {str(m['warhead'])[:28]:28} span {m['span']:5.0f}")
        return 0

    print(f"placed {len(rows)} profiles into {len(groups)} archetypes "
          f"(Cameo currently occupies 14)")
    sharp = collections.Counter(r["sharp"] for r in rows)
    print("  sharpness:", dict(sharp))
    print(f"  define an aircraft armor: {sum(1 for r in rows if r['has_air'])}")
    print()
    print(f"{'archetype':34} {'n':>5} {'src':>4} {'span':>5}  macro medians")
    for key, members in sorted(groups.items(), key=lambda kv: -len(kv[1]))[:20]:
        p = profile_of(members)
        print(f"{key:34} {p['n']:5} {p['sources']:4} {p['median_span']:5.0f}  {p['macro']}")
    if args.write:
        OUT.write_text(render(rows, groups), encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
