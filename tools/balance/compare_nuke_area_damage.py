#!/usr/bin/env python3
"""R14: test whether the legacy nuclear-ring cohort fits current AreaDamage fields.

Read-only.  It consumes the R10-R15 census, checks the engine implementation contract, and
reports structural equivalence limits.  It never edits YAML or proposes approximate damage.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[2]
INPUT = ROOT / "docs" / "audit" / "latest" / "deprecated_name_lane_20260913.json"
ENGINE = ROOT / "OpenRA.Mods.Cameo" / "Warheads" / "AreaDamageWarhead.cs"
PAYLOAD_KEYS = {
    "Warhead@Damage",
    "Warhead@1Dam_impact",
    "Warhead@4Dam_areanuke1",
    "Warhead@7Dam_areanuke2",
    "Warhead@8Dam_areanuke2",
    "Warhead@10Dam_areanuke3",
    "Warhead@11Dam_areanuke3",
}


def number(value):
    if value in (None, ""):
        return None
    return int(str(value).strip())


def wdist(value):
    if value in (None, ""):
        return None
    text = str(value).strip()
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    match = re.fullmatch(r"(-?\d+)c(\d+)", text)
    if match:
        return int(match.group(1)) * 1024 + int(match.group(2))
    return None


def falloff(value):
    if value in (None, ""):
        return None
    try:
        return tuple(int(part.strip()) for part in str(value).split(","))
    except ValueError:
        return None


def falloff_at(spread: int, curve: list[int], distance: int) -> int:
    """OpenRA SpreadDamageWarhead.GetDamageFalloff, including integer truncation."""
    inner = 0
    for index in range(1, len(curve)):
        outer = index * spread
        if outer > distance:
            numerator = (curve[index] - curve[index - 1]) * (distance - inner)
            return curve[index - 1] + int(numerator / (outer - inner))
        inner = outer
    return 0


def ratio_witness(profiles: list[dict]):
    """Find two ticks whose positive spatial profiles are not proportional.

    One AreaDamage tick uses a shared falloff shape. This records differing sampled shapes for
    review; integer damage rounding and unknown/same-time scheduling remain outside the proof.
    """
    for left_index, left in enumerate(profiles):
        if left["spread"] is None or not left["falloff"]:
            continue
        for right in profiles[left_index + 1:]:
            if right["spread"] is None or not right["falloff"]:
                continue
            limit = min(left["outer_radius"], right["outer_radius"])
            points = {0}
            if limit > 1:
                points.add(limit // 2)
            for row in (left, right):
                points.update(i * row["spread"] for i in range(1, len(row["falloff"])))
            ordered = sorted(point for point in points if 0 <= point < limit)
            ordered += sorted({(a + b) // 2 for a, b in zip(ordered, ordered[1:])
                               if a < (a + b) // 2 < b})
            ordered = sorted(set(ordered))
            for first_index, first in enumerate(ordered):
                lf = falloff_at(left["spread"], left["falloff"], first)
                rf = falloff_at(right["spread"], right["falloff"], first)
                if lf <= 0 or rf <= 0:
                    continue
                for second in ordered[first_index + 1:]:
                    ls = falloff_at(left["spread"], left["falloff"], second)
                    rs = falloff_at(right["spread"], right["falloff"], second)
                    if ls <= 0 or rs <= 0:
                        continue
                    if lf * rs != ls * rf:
                        return {
                            "left": left["warhead"], "right": right["warhead"],
                            "distances": [first, second],
                            "left_falloff": [lf, ls], "right_falloff": [rf, rs],
                        }
    return None


def target_witness(profiles: list[dict]):
    seen = {}
    for row in profiles:
        targets = frozenset(part.strip() for part in (row["valid_targets"] or "").split(",")
                            if part.strip())
        if not targets:
            continue
        for other_targets, other in seen.items():
            if targets != other_targets:
                return {
                    "left": other["warhead"], "right": row["warhead"],
                    "left_targets": sorted(other_targets), "right_targets": sorted(targets),
                }
        seen[targets] = row
    return None


def engine_contract() -> dict:
    source = ENGINE.read_text(encoding="utf-8")
    required = {
        "uniform_delay": "t * TickDelay",
        "linear_radius": "(effectiveMaxRadius.Length - effectiveMinRadius.Length) * (tick + 1) / Ticks",
        "shared_falloff": "GetDamageFalloff(falloffDistance)",
        "integer_tick_weights": "100 * TickDamage[tick] / tickDamageTotal",
    }
    missing = [name for name, text in required.items() if text not in source]
    if missing:
        raise RuntimeError("AreaDamage implementation contract changed: " + ", ".join(missing))
    return {
        "delay": "one initial Delay plus uniform TickDelay multiples",
        "radius": "one linear MinRadius-to-MaxRadius progression",
        "falloff": "one shared Falloff/Spread or Range profile for every tick",
        "targets": "one shared ValidTargets set for every tick",
        "damage": "one tick scalar per impact; the scalar is shared across every distance",
    }


def analyse_weapon(name: str, rows: list[dict]) -> dict:
    selected = [row for row in rows if row["warhead"] in PAYLOAD_KEYS]
    selected.sort(key=lambda row: (number(row.get("delay")) is None,
                                   number(row.get("delay")) or 0,
                                   row["warhead"]))
    profiles = []
    for row in selected:
        spread = wdist(row.get("spread"))
        curve = falloff(row.get("falloff"))
        outer = spread * (len(curve) - 1) if spread is not None and curve else None
        profiles.append({
            "warhead": row["warhead"],
            "damage": number(row.get("damage")),
            "delay": number(row.get("delay")),
            "spread": spread,
            "falloff": list(curve) if curve else None,
            "outer_radius": outer,
            "valid_targets": row.get("valid_targets"),
            "type": row.get("type"),
        })

    missing = sorted(PAYLOAD_KEYS - {row["warhead"] for row in profiles})
    limitations = []
    if missing:
        limitations.append(f"incomplete seven-payload evidence ({len(profiles)}/{len(PAYLOAD_KEYS)})")

    delays = [row["delay"] for row in profiles]
    if any(value is None for value in delays):
        limitations.append("one or more payload delays are unspecified")
    elif len(delays) > 2 and len(set(b - a for a, b in zip(delays, delays[1:]))) != 1:
        limitations.append("payload delays are not a uniform sequence")

    spatial = ratio_witness(profiles)
    targets = target_witness(profiles)
    differences = []
    if spatial:
        differences.append("sampled payloads have non-proportional Spread/Falloff shapes")
    if targets:
        differences.append("authored ValidTargets sets differ across payloads")

    return {
        "weapon": name,
        "file": rows[0]["file"],
        "rings": profiles,
        "missing_payloads": missing,
        "observed_differences": differences,
        "spatial_ratio_witness": spatial,
        "target_witness": targets,
        "screen_limitations": limitations,
        "status": "requires_review",
    }


def build_report() -> dict:
    contract = engine_contract()
    census = json.loads(INPUT.read_text(encoding="utf-8"))
    grouped = collections.defaultdict(list)
    for row in census["r14_nuke_cohort"]:
        grouped[row["weapon"]].append(row)
    weapons = [analyse_weapon(name, rows) for name, rows in sorted(grouped.items())]
    return {
        "schema": 1,
        "scope": "R14 exact expressibility under the current AreaDamage implementation",
        "engine_contract": contract,
        "weapons": weapons,
        "counts": {
            "weapons": len(weapons),
            "requires_review": len(weapons),
        },
        "conclusion": (
            "No exact conversion candidate is established by this bounded screen. The measured "
            "falloff-shape and target-set differences require full predicate, timing and integer-"
            "damage review before any conversion."
        ),
    }


def markdown(report: dict) -> str:
    counts = report["counts"]
    lines = [
        "# R14 nuclear-ring versus current AreaDamage",
        "",
        "**Read-only exact-equivalence review. No YAML or runtime code is changed.**",
        "",
        f"Weapons reviewed: **{counts['weapons']}**; requiring further review: "
        f"**{counts['requires_review']}**.",
        "",
        "## Result",
        "",
        report["conclusion"],
        "",
        "Current `AreaDamage` provides one uniform tick interval, one shared falloff profile and "
        "one shared target set. The table records sampled differences against those fields. It does "
        "not claim an impossibility proof: integer damage rounding, target predicates, same-time or "
        "unknown scheduling, and explicit `Range` remain outside this screen.",
        "",
        "| weapon | file | status | observed differences | limitations |",
        "|---|---|---|---|---|",
    ]
    for row in report["weapons"]:
        evidence = []
        spatial = row["spatial_ratio_witness"]
        if spatial:
            evidence.append(
                f"`{spatial['left']}` vs `{spatial['right']}` at "
                f"{spatial['distances'][0]}/{spatial['distances'][1]} WDist: "
                f"{spatial['left_falloff'][0]}:{spatial['left_falloff'][1]} vs "
                f"{spatial['right_falloff'][0]}:{spatial['right_falloff'][1]}")
        target = row["target_witness"]
        if target:
            evidence.append(
                f"`{target['left']}` targets {', '.join(target['left_targets'])}; "
                f"`{target['right']}` targets {', '.join(target['right_targets'])}")
        reasons = "; ".join(evidence) or "none observed by this screen"
        limitations = "; ".join(row["screen_limitations"]) or "—"
        lines.append(f"| `{row['weapon']}` | `{row['file']}` | "
                     f"`{row['status']}` | {reasons} | {limitations} |")

    lines += ["", "## Ring evidence", ""]
    for row in report["weapons"]:
        lines += [f"### `{row['weapon']}`", "",
                  "| warhead | Delay | Damage | Spread | derived outer radius | Falloff | ValidTargets |",
                  "|---|---:|---:|---:|---:|---|---|"]
        for ring in row["rings"]:
            lines.append(f"| `{ring['warhead']}` | {ring['delay'] if ring['delay'] is not None else 'unspecified'} | "
                         f"{ring['damage'] if ring['damage'] is not None else 'unspecified'} | "
                         f"{ring['spread'] if ring['spread'] is not None else 'unspecified'} | "
                         f"{ring['outer_radius'] if ring['outer_radius'] is not None else 'unspecified'} | "
                         f"{', '.join(map(str, ring['falloff'])) if ring['falloff'] else 'unspecified'} | "
                         f"{ring['valid_targets'] or 'unspecified'} |")
        lines.append("")
    lines += [
        "## Decision boundary",
        "",
        "R14 remains open. These measurements do not certify a conversion or prove impossibility. "
        "Any candidate must still compare resolved predicates, timing, integer damage and complete "
        "spatial behavior; an approximation or new per-tick semantics is a separate engine/design "
        "decision and needs its own gameplay review.",
        "",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", type=pathlib.Path)
    parser.add_argument("--markdown", type=pathlib.Path)
    args = parser.parse_args(argv)
    report = build_report()
    if args.json:
        (ROOT / args.json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")
    if args.markdown:
        (ROOT / args.markdown).write_text(markdown(report), encoding="utf-8")
    if not args.json and not args.markdown:
        print(markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
