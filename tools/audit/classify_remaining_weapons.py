#!/usr/bin/env python3
"""Classify the active weapons that still use retired full-stack families.

This is a read-only triage tool.  It does not claim that a suggested destination is
safe to apply: each conversion still needs an in-memory/resolved comparison.  Its job
is to put the mechanically promising roots first and concentrate human review on
conflicting or exceptional cases.

Usage:
  python tools/audit/classify_remaining_weapons.py
  python tools/audit/classify_remaining_weapons.py --write
  python tools/audit/classify_remaining_weapons.py --check
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from miniyaml import Ruleset  # noqa: E402
from weapon_families import OLD_FAMILIES, weapon_files  # noqa: E402
import plan_warhead_collapse as planner  # noqa: E402
import percentage_damage as pd  # noqa: E402
import intentional_composites as reviewed  # noqa: E402
from extract_stats import warheads as inherited_warheads  # noqa: E402

OUT_MD = ROOT / "docs" / "audit" / "latest" / "remaining_weapon_classification.md"
OUT_JSON = ROOT / "docs" / "audit" / "latest" / "remaining_weapon_classification.json"
CANONICAL = re.compile(r"^\^Warhead_([A-Za-z]+)_(Light|Medium|Heavy|Super)$")
EXCEPTION_FAMILIES = {"^MagicWeapon", "^NuclearWarhead", "^LightFlameWeapon"}
FLAT_DAMAGE_TYPES = {"AreaDamage", "SpreadDamage"}
# These roots deliberately retain their historical multi-family profile after a
# resolved-gameplay review found that collapsing it changed live balance.
EXACT_REVIEWED_RESTORATIONS = {"HydraSpit"}


def damage(node) -> int:
    try:
        return int(str(node.get("Damage") or "0").strip())
    except ValueError:
        return 0


def positive_flat_keys(rs: Ruleset, family: str) -> set[str]:
    node = rs.resolve_weapon(family)
    if node is None:
        return {family.lstrip("^")}
    return {
        child.key.split("@", 1)[1]
        for child in node.children
        if child.key.startswith("Warhead@")
        and "Percentage" not in child.key
        and "Concrete" not in child.key
        and child.value in FLAT_DAMAGE_TYPES
        and damage(child) > 0
    }


def local_inherits(local) -> list[str]:
    return [
        str(child.value).strip()
        for child in local.children
        if child.key.split("@", 1)[0] == "Inherits" and child.value
    ]


def remaining_old_families(rs: Ruleset, local, flat_keys: dict[str, set[str]]) -> list[str]:
    deleted = {
        child.key.split("@", 1)[1]
        for child in local.children
        if child.key.startswith("-Warhead@")
    }
    return sorted(
        family for family in local_inherits(local)
        if family in OLD_FAMILIES and not flat_keys[family].issubset(deleted)
    )


def name_signal(name: str) -> tuple[str | None, str]:
    if name in planner.EXPLICIT:
        family, reason = planner.EXPLICIT[name]
        return family, f"explicit: {reason}"
    low = name.lower()
    if "photon" in low:
        return "Plasma", "family word 'photon'"
    for tier, label in ((planner.NAME_FAMILY_SPECIFIC, "family word"),
                        (planner.NAME_FAMILY_GENERIC, "delivery word")):
        for token, family in tier:
            if token in low:
                return family, f"{label} '{token}'"
    return None, ""


def legacy_signal(families: list[str]) -> tuple[str | None, str]:
    scores: collections.Counter[str] = collections.Counter()
    for family in families:
        if family in planner.LEGACY_FAMILY:
            candidate, weight = planner.LEGACY_FAMILY[family]
            scores[candidate] += weight
    if not scores:
        return None, "no mapped legacy signal"
    ranked = scores.most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        tied = "/".join(name for name, score in ranked if score == ranked[0][1])
        return None, f"legacy tie: {tied}"
    return ranked[0][0], f"legacy score {ranked[0][0]}={ranked[0][1]}"


def descendants(rs: Ruleset) -> dict[str, set[str]]:
    children: dict[str, set[str]] = collections.defaultdict(set)
    for name, local in rs.weapons.items():
        for parent in local_inherits(local):
            if parent in rs.weapons:
                children[parent].add(name)

    result: dict[str, set[str]] = {}
    for root in rs.weapons:
        seen: set[str] = set()
        stack = list(children.get(root, ()))
        while stack:
            child = stack.pop()
            if child in seen:
                continue
            seen.add(child)
            stack.extend(children.get(child, ()))
        result[root] = {name for name in seen if not name.startswith("^")}
    return result


def physical_state_ledger(node) -> list[dict[str, str]]:
    rows = []
    name = node.get("PhysicalStateName")
    if name:
        rows.append({"name": name, "scale": node.get("PhysicalStateScale") or "0",
                     "source": "singular"})
    states = node.child("PhysicalStates")
    if states is not None:
        for state in states.children:
            rows.append({"name": state.key, "scale": state.value or "0", "source": "map"})
    return rows


def hit_contract(child) -> dict[str, object]:
    return {
        "tag": child.key.split("@", 1)[1],
        "type": child.value,
        "targets": child.get("ValidTargets") or "*",
        "invalid_targets": child.get("InvalidTargets") or "",
        "relationships": child.get("ValidRelationships") or "Ally, Neutral, Enemy",
        "updates_statistics": (child.get("UpdatesUnitStatistics") or "true").lower() != "false",
        "friendly_damage": child.get("FriendlyFireDamage") or "100",
        "friendly_spread": child.get("FriendlyFireSpread") or "100",
        "physical_states": physical_state_ledger(child),
    }


def flat_ledger(node) -> list[dict[str, object]]:
    rows = []
    for child in node.children:
        if not child.key.startswith("Warhead@"):
            continue
        is_percentage = "Percentage" in child.key or child.value == "HealthPercentageDamage"
        if (is_percentage or "Concrete" in child.key
                or child.value not in FLAT_DAMAGE_TYPES or damage(child) <= 0):
            continue
        record = hit_contract(child)
        record["damage"] = damage(child)
        rows.append(record)
    return rows


def is_exact_reviewed_restoration(name: str, flat_tags: set[str]) -> bool:
    """Exclude a restoration only while its validated reviewed shape is exact."""
    if name not in EXACT_REVIEWED_RESTORATIONS:
        return False
    decision = reviewed.curated_decisions().get(name)
    return bool(
        decision
        and decision["category"] == "maintainer-approved role blend"
        and set(decision["mains"]) == flat_tags
    )


def percentage_ledger(node) -> list[dict[str, object]]:
    rows = []
    for application in pd.percentage_applications(node, 200_000):
        child = application["node"]
        record = hit_contract(child)
        record.update({
            "kind": application["kind"],
            "damage": application["damage"],
            "scale": application.get("scale"),
            "denominator": application["denominator"],
            "percentage_spread": application["percentage_spread"],
            "percentage_versus": application["versus"],
            "runtime_units": application["runtime_units"],
            "runtime_overflow": application.get("runtime_overflow", False),
        })
        rows.append(record)
    return rows


def choose_review_bucket(old: list[str], canonical_destinations: list[str],
                         canonical_families: list[str], name_family: str | None,
                         legacy_family: str | None,
                         legacy_reason: str) -> tuple[str, str | None, list[str]]:
    """Apply the conservative classification policy to already-extracted signals."""
    reasons = []
    if set(old) & EXCEPTION_FAMILIES:
        reasons.append("exception-bearing retired family")
    if len(canonical_destinations) > 1:
        reasons.append("multiple inherited family/tier destinations")
    if legacy_family is None:
        reasons.append(legacy_reason)
    if canonical_families and name_family and name_family not in canonical_families:
        reasons.append("name and canonical destination disagree")
    if canonical_families and legacy_family and legacy_family not in canonical_families:
        reasons.append("canonical and legacy signals disagree")
    if name_family and legacy_family and name_family != legacy_family:
        reasons.append("name and legacy signals disagree")

    if reasons:
        return ("human decision required",
                canonical_destinations[0] if len(canonical_destinations) == 1 else None,
                reasons)
    if len(canonical_destinations) == 1:
        return "one inherited destination", canonical_destinations[0], reasons
    if name_family and legacy_family == name_family:
        return "corroborated suggestion", name_family, reasons
    if legacy_family and not name_family:
        return "legacy-only suggestion", legacy_family, reasons
    reasons.append("no unique destination signal")
    return "human decision required", None, reasons


def classify(rs: Ruleset) -> list[dict[str, object]]:
    flat_keys = {family: positive_flat_keys(rs, family) for family in OLD_FAMILIES}
    closure = descendants(rs)
    active_files = {path.resolve() for path in weapon_files() if path.exists()}
    rows = []
    for name in sorted(rs.weapons):
        if name.startswith("^"):
            continue
        local = rs.weapon(name)
        resolved = rs.resolve_weapon(name)
        if local is None or resolved is None:
            continue
        if is_exact_reviewed_restoration(
                name, {hit["tag"] for hit in flat_ledger(resolved)}):
            continue
        local_path = (ROOT / local.file).resolve()
        if local_path not in active_files:
            continue
        old = remaining_old_families(rs, local, flat_keys)
        if not old:
            continue

        canonical = []
        for template in inherited_warheads(rs, name):
            match = CANONICAL.match(template)
            if match:
                canonical.append({"template": template, "family": match.group(1),
                                  "tier": match.group(2),
                                  "destination": f"{match.group(1)}_{match.group(2)}"})
        canonical_destinations = sorted({item["destination"] for item in canonical})
        canonical_families = sorted({item["family"] for item in canonical})
        name_family, name_reason = name_signal(name)
        legacy_family, legacy_reason = legacy_signal(old)
        bucket, candidate, reasons = choose_review_bucket(
            old, canonical_destinations, canonical_families, name_family,
            legacy_family, legacy_reason)

        all_old_keys = set().union(*(flat_keys[family] for family in old))
        descendant_overrides = []
        for child_name in sorted(closure[name]):
            child = rs.weapon(child_name)
            if child is None:
                continue
            keys = sorted(
                node.key.split("@", 1)[1]
                for node in child.children
                if node.key.startswith("Warhead@")
                and node.key.split("@", 1)[1] in all_old_keys
            )
            if keys:
                descendant_overrides.append({"weapon": child_name, "keys": keys})

        ledger = flat_ledger(resolved)
        percentage_hits = percentage_ledger(resolved)
        projectile = resolved.child("Projectile")
        rows.append({
            "weapon": name,
            "file": str(local_path.relative_to(ROOT)).replace("\\", "/"),
            "line": local.line,
            "bucket": bucket,
            "candidate_family": candidate,
            "old_families": old,
            "canonical_templates": canonical,
            "name_signal": {"family": name_family, "reason": name_reason},
            "legacy_signal": {"family": legacy_family, "reason": legacy_reason},
            "reasons": reasons,
            "projectile": projectile.value if projectile is not None else "",
            "valid_targets": resolved.get("ValidTargets") or "",
            "flat_hits": ledger,
            "percentage_hits": percentage_hits,
            "descendants": sorted(closure[name]),
            "descendant_old_flat_overrides": descendant_overrides,
        })
    return rows


def render_markdown(rows: list[dict[str, object]]) -> str:
    counts = collections.Counter(row["bucket"] for row in rows)
    lines = [
        "# Remaining Weapon Classification",
        "",
        "This report is read-only triage. A suggested destination is not approval to edit YAML;",
        "each group still needs a proposed resolved diff and the full behavior comparator.",
        "",
        f"Active concrete roots still using retired flat families: **{len(rows)}**.",
        "",
        "| review bucket | roots | meaning |",
        "|---|--:|---|",
        f"| one inherited destination | {counts['one inherited destination']} | one family and tier appears in the actual inheritance chain without conflicting evidence |",
        f"| corroborated suggestion | {counts['corroborated suggestion']} | weapon-name and weighted legacy evidence agree |",
        f"| legacy-only suggestion | {counts['legacy-only suggestion']} | one weighted legacy signal exists, but the name does not confirm it |",
        f"| human decision required | {counts['human decision required']} | conflicting, exceptional, or missing destination evidence |",
        "",
        "The machine-readable JSON includes every flat hit's targets, exclusions, relationships,",
        "score flag, friendly-fire modifiers, physical-state bindings, full percentage hits, descendant",
        "closure, and descendant overrides of retired flat keys.",
        "",
    ]
    for bucket in ("one inherited destination", "corroborated suggestion",
                   "legacy-only suggestion", "human decision required"):
        selected = [row for row in rows if row["bucket"] == bucket]
        lines += [f"## {bucket.title()} ({len(selected)})", "",
                  "| weapon | proposed family | retired families | descendants | old-key child overrides | evidence |",
                  "|---|---|---|--:|--:|---|"]
        for row in selected:
            canonical = ", ".join(item["template"] for item in row["canonical_templates"])
            evidence = canonical or row["name_signal"]["reason"] or row["legacy_signal"]["reason"]
            if row["reasons"]:
                evidence = "; ".join(row["reasons"])
            old = ", ".join(family.lstrip("^") for family in row["old_families"])
            lines.append(
                f"| `{row['weapon']}` | {row['candidate_family'] or '?'} | {old} | "
                f"{len(row['descendants'])} | {len(row['descendant_old_flat_overrides'])} | {evidence} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_json(rows: list[dict[str, object]]) -> str:
    return json.dumps({"roots": len(rows), "weapons": rows}, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write the tracked markdown and JSON reports")
    mode.add_argument("--check", action="store_true", help="fail when the tracked reports are stale")
    args = parser.parse_args()

    rows = classify(Ruleset(ROOT))
    markdown = render_markdown(rows)
    json_text = render_json(rows)
    counts = collections.Counter(row["bucket"] for row in rows)

    if args.write:
        OUT_MD.write_text(markdown, encoding="utf-8")
        OUT_JSON.write_text(json_text, encoding="utf-8")
        print(f"wrote {OUT_MD}")
        print(f"wrote {OUT_JSON}")
    elif args.check:
        stale = []
        for path, expected in ((OUT_MD, markdown), (OUT_JSON, json_text)):
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                stale.append(str(path.relative_to(ROOT)))
        if stale:
            print("stale classification report: " + ", ".join(stale))
            return 1
        print("classification reports match the active weapon tree")
    else:
        print(markdown)

    print(f"roots: {len(rows)}")
    for bucket in ("one inherited destination", "corroborated suggestion",
                   "legacy-only suggestion", "human decision required"):
        print(f"{bucket}: {counts[bucket]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
