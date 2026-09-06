#!/usr/bin/env python3
"""Render the unresolved reachable weapon backlog as family-level decisions."""

from __future__ import annotations

import argparse
import pathlib

from plan_reachable_stack_backlog import build
from intentional_composites import resolved_referrer_index
from miniyaml import Ruleset


ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/audit/latest/weapon_decision_bundle.md"

BUCKETS = (
    "target and state routing",
    "target routing",
    "state delivery",
    "legacy compatibility",
    "numbered warhead key",
    "no special mechanical signal",
)


def transitive_actor_referrers(index, weapon_names):
    """Resolve weapon-to-weapon delivery chains back to their active actors."""
    actors = set()
    stages = set()
    pending = list(weapon_names)
    seen = {name.lower() for name in weapon_names}
    while pending:
        current = pending.pop()
        for referrer in index.get(current.lower(), []):
            if referrer["kind"] == "actor":
                actors.add(referrer["name"])
                continue
            name = referrer["name"]
            stages.add(name)
            if name.lower() not in seen:
                seen.add(name.lower())
                pending.append(name)
    return sorted(actors), sorted(stages)


def source_scope(path):
    parts = str(path or "").replace("\\", "/").split("/")
    if "ContentPacks" in parts:
        start = parts.index("ContentPacks") + 1
        end = parts.index("yaml") if "yaml" in parts[start:] else len(parts) - 1
        return " / ".join(parts[start:end])
    if "rules" in parts:
        return "shared rules"
    return "shared content"


def actor_label(rules, name):
    actor = rules.resolve(name)
    tooltip = actor.child("Tooltip") if actor is not None else None
    display = tooltip.get("Name") if tooltip is not None else None
    if not display or display.startswith("actor_") or display.startswith("notification-"):
        display = name
    elif display.lower() != name.lower():
        display = f"{display} (`{name}`)"
    else:
        display = f"`{name}`"
    source = rules.actor(name)
    return f"{source_scope(source.file if source is not None else '')}: {display}"


def enrich_referrers(rows):
    rules = Ruleset(ROOT)
    index = resolved_referrer_index(rules)
    for row in rows:
        actors, stages = transitive_actor_referrers(index, row["members"])
        row["actor_count"] = len(actors)
        row["actors"] = [actor_label(rules, name) for name in actors]
        row["delivery_stages"] = stages
    return rows


def bucket(flags: dict[str, bool]) -> str:
    if flags["route_mixed"] and flags["state_or_integrity"]:
        return BUCKETS[0]
    if flags["route_mixed"]:
        return BUCKETS[1]
    if flags["state_or_integrity"]:
        return BUCKETS[2]
    if flags["legacy_bridge"]:
        return BUCKETS[3]
    if flags["numbered"]:
        return BUCKETS[4]
    return BUCKETS[5]


def decision_rows(data=None):
    data = build() if data is None else data
    rows = []
    covered = set()
    for group in data["groups"]:
        members = [member for member in group["members"] if not member["reviewed"]]
        if not members:
            continue
        names = [member["name"] for member in members]
        overlap = covered & set(names)
        if overlap:
            raise RuntimeError(f"unreviewed decision rows overlap: {sorted(overlap)}")
        covered.update(names)
        family_flags = {
            "air_only": all(member["flags"]["air_only"] for member in members),
            **{
                flag: any(member["flags"][flag] for member in members)
                for flag in (
                    "legacy_bridge", "numbered", "route_mixed",
                    "state_or_integrity")
            },
        }
        fingerprints = {}
        for member in members:
            fingerprint = tuple(sorted(member["mains"]))
            fingerprints.setdefault(fingerprint, []).append(member["name"])
        rows.append({
            "bucket": bucket(family_flags),
            "family": group["root"] if group["root"] in names else names[0],
            "members": names,
            "signals": [
                name.replace("_", " ") for name, enabled in family_flags.items()
                if enabled
            ] or ["none detected"],
            "fingerprints": [
                {"mains": list(mains), "members": fingerprint_members}
                for mains, fingerprint_members in sorted(fingerprints.items())
            ],
        })
    if len(covered) != data["unreviewed_reachable"]:
        raise RuntimeError(
            f"decision coverage {len(covered)}/{data['unreviewed_reachable']}")
    return rows, data


def rendered(data=None) -> str:
    rows, data = decision_rows(data)
    enrich_referrers(rows)
    lines = [
        "# Remaining reachable weapon decisions",
        "",
        "This report compresses the honest unreviewed backlog into inheritance",
        "families. It is a review queue, not conversion authority. Reviewed exact",
        "composites remain in the raw structural count but are excluded here.",
        "Three independent reviews found no mechanically exact fold in this",
        "remaining set; each row requires an armor, geometry, targeting, state,",
        "or progression decision before its live behavior can be changed.",
        "The player-facing recommendation for every family is maintained in",
        "`docs/design/WEAPON_REDESIGN_RECOMMENDATIONS.md`.",
        "",
        f"- Raw reachable stacked definitions: **{data['reachable_stacked']}**",
        f"- Exact reviewed composites: **{data['reviewed_reachable']}**",
        f"- Unreviewed reachable definitions: **{data['unreviewed_reachable']}**",
        f"- Unreviewed inheritance families: **{len(rows)}**",
        "",
        "The buckets describe why automatic consolidation is unsafe. They do not",
        "decide the eventual damage family.",
        "A bold family label is an unreviewed planning root; only the definitions",
        "listed after the colon remain open decisions.",
        "",
        "| decision bucket | families | definitions |",
        "|---|---:|---:|",
    ]
    for name in BUCKETS:
        selected = [row for row in rows if row["bucket"] == name]
        lines.append(
            f"| {name} | {len(selected)} | "
            f"{sum(len(row['members']) for row in selected)} |")
    for name in BUCKETS:
        selected = [row for row in rows if row["bucket"] == name]
        noun = "family" if len(selected) == 1 else "families"
        lines.extend(["", f"## {name.title()} ({len(selected)} {noun})", ""])
        for row in selected:
            members = ", ".join(f"`{member}`" for member in row["members"])
            signals = ", ".join(row["signals"])
            lines.append(
                f"- **`{row['family']}`** ({len(row['members'])}; {signals}): "
                f"{members}")
            actors = row["actors"][:8]
            actor_text = "; ".join(actors) if actors else "weapon-chain only"
            if row["actor_count"] > len(actors):
                actor_text += f"; and {row['actor_count'] - len(actors)} more actors"
            lines.append(f"  - active users: {actor_text}")
            if row["delivery_stages"]:
                stages = row["delivery_stages"][:8]
                stage_text = ", ".join(f"`{stage}`" for stage in stages)
                if len(row["delivery_stages"]) > len(stages):
                    stage_text += (
                        f", and {len(row['delivery_stages']) - len(stages)} more stages")
                lines.append(f"  - transitive delivery: {stage_text}")
            for fingerprint in row["fingerprints"]:
                mains = " + ".join(fingerprint["mains"])
                fingerprint_members = ", ".join(
                    f"`{member}`" for member in fingerprint["members"])
                lines.append(f"  - mains `{mains}`: {fingerprint_members}")
    lines.extend(["", "## Maintainer decision shape", "", (
        "For each family, the eventual question is: which authored main defines the "
        "unit's role, and may its armor, splash, target route, and state delivery be "
        "applied to the full nominal damage? Paid replacements and mixed target routes "
        "must be reviewed as complete closures."
    ), ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = rendered()
    if args.write:
        OUT.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {OUT.relative_to(ROOT)}")
        return 0
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print(f"FAIL {OUT.relative_to(ROOT)} is stale; run with --write")
            return 1
        print(f"PASS {OUT.relative_to(ROOT)} matches live rules")
        return 0
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
