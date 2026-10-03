#!/usr/bin/env python3
"""Report balance-class coverage over the active faction roster.

Unlike class_membership.py's ledger-wide census, this uses the active mod
manifest and faction prerequisite closure. It is diagnostic only: closure also
includes starting and power-granted actors, and unit_type can call technical
actors units. Neither this tool nor a class mapping approves a Formula V2 price.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from cameo_model import Model  # noqa: E402
from class_membership import classify  # noqa: E402
from extract_stats import actor_subtype  # noqa: E402


SECTIONS = {"inf": "infantry", "veh": "vehicles", "air": "aircraft", "nav": "naval"}


def collect(model: Model) -> tuple[list[str], dict[str, dict]]:
    """Return selectable faction IDs and distinct, statically reachable units."""
    factions = sorted(f.internal for f in model.real_factions() if f.selectable)
    records: dict[str, dict] = {}
    for faction in factions:
        tokens = model.faction_tokens(faction)
        for actor in model.buildable_roster(faction):
            kind = model.unit_type(actor)
            if kind not in SECTIONS:
                continue
            raw = model.rs.actor(actor)
            resolved = model.rs.resolve(actor)
            if raw is None or resolved is None:
                continue
            subtype = actor_subtype(model.rs, raw, SECTIONS[kind])
            cls, reason = classify({"subtype": subtype})
            prereqs = model.positive_prereqs(resolved)
            direct = all(token in tokens or token.startswith(model.OPTION_TOKEN_PREFIXES)
                         for token in prereqs)
            if actor not in records:
                source = pathlib.Path(raw.file).resolve().relative_to(ROOT)
                records[actor] = {
                    "kind": kind,
                    "subtype": subtype,
                    "class": cls,
                    "reason": reason,
                    "direct_prerequisites_satisfied": False,
                    "has_health": bool(resolved.get("Health", "HP")),
                    "queue": resolved.get("Buildable", "Queue") or "",
                    "source": source.as_posix(),
                    "factions": [],
                }
            records[actor]["direct_prerequisites_satisfied"] |= direct
            records[actor]["factions"].append(faction)
    return factions, dict(sorted(records.items()))


def summary(factions: list[str], records: dict[str, dict]) -> dict:
    reasons = collections.Counter(row["reason"] for row in records.values())
    gap_kinds = collections.Counter(row["kind"] for row in records.values()
                                    if row["reason"] == "no-template")
    return {
        "selectable_factions": len(factions),
        "distinct_roster_candidates": len(records),
        "reasons": dict(sorted(reasons.items())),
        "no_template_kinds": dict(sorted(gap_kinds.items())),
    }


def markdown(info: dict, records: dict[str, dict]) -> str:
    lines = [
        "# Active balance-class coverage (static faction closure)",
        "",
        "The active `mod.yaml` includes and selectable, non-meta factions define the scope.",
        "A roster candidate can enter by production, starting units, or a power; this",
        "report is not an in-game build-menu test. It ignores ledger hand tags so it",
        "measures role-template coverage rather than preserving explicit overrides.",
        "",
        f"Selectable factions: **{info['selectable_factions']}**; distinct candidate actors: "
        f"**{info['distinct_roster_candidates']}**.",
        "",
        "| Classification | Actors |",
        "|---|---:|",
    ]
    for reason, count in info["reasons"].items():
        lines.append(f"| `{reason}` | {count} |")
    lines.extend([
        "",
        "`no-template` candidates need actor-by-actor triage. Technical actors,",
        "building cores, transports, and ability units must not be forced into a",
        "combat price formula solely to eliminate this diagnostic count.",
        "",
        "| Actor | Kind | Queue | Direct prerequisites | Health | Source |",
        "|---|---|---|---|---|---|",
    ])
    for actor, row in records.items():
        if row["reason"] != "no-template":
            continue
        lines.append(
            f"| `{actor}` | {row['kind']} | `{row['queue']}` | "
            f"{'yes' if row['direct_prerequisites_satisfied'] else 'no'} | "
            f"{'yes' if row['has_health'] else 'no'} | `{row['source']}` |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable results")
    args = parser.parse_args()
    factions, records = collect(Model(ROOT))
    info = summary(factions, records)
    if args.json:
        print(json.dumps({"summary": info, "actors": records}, indent=2))
    else:
        print(markdown(info, records), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
