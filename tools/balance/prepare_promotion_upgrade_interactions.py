#!/usr/bin/env python3
"""Inventory upgrade hooks on the current promotion-unit cohort.

This is a review-only companion to the promotion discount and superiority
receipts.  It records which resolved conditions and stat multipliers are
upgrade/doctrine driven, without valuing them or changing YAML.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
from cameo_model import Model  # noqa: E402
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import diagnostic_output  # noqa: E402


FACTIONS = ("ra1_allies", "ra1_soviets", "td_gdi", "td_nod")
STAT_TRAITS = {
    "FirepowerMultiplier", "ReloadDelayMultiplier", "DamageMultiplier",
    "SpeedMultiplier", "RangeMultiplier", "InaccuracyMultiplier",
    "RevealsShroudMultiplier", "DetectCloakedMultiplier",
}
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*")
CONDITION_PRODUCERS = {
    "ExternalCondition",
    "GrantCondition",
    "GrantConditionOnActivity",
    "GrantConditionOnAttack",
    "GrantConditionOnBotOwner",
    "GrantConditionOnCombatantOwner",
    "GrantConditionOnDamage",
    "GrantConditionOnDamageState",
    "GrantConditionOnDeploy",
    "GrantConditionOnInfiltration",
    "GrantConditionOnInternalOwner",
    "GrantConditionOnMovement",
    "GrantConditionOnPhysicalState",
    "GrantConditionOnPowerState",
    "GrantConditionOnPrerequisite",
    "GrantConditionOnTerrain",
}


def finite(value):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def normalize_token(raw):
    """Normalize a prerequisite token without discarding its negation."""
    return (raw or "").strip().lstrip("~!").lower()


def token_kind(token, faction):
    """Classify a prerequisite token for the interaction inventory."""
    value = normalize_token(token)
    if value.startswith(faction + "_promotion_") or "_promotion_" in value:
        return "promotion"
    if value.startswith(faction + "_upgrade_") or value.startswith(faction + "_doctrine_"):
        return "upgrade_or_doctrine"
    if "_upgrade_" in value or "_doctrine_" in value:
        return "other_faction_upgrade_or_doctrine"
    return "other"


def condition_identifiers(expression):
    """Return condition names, excluding numeric literals and operators."""
    ignored = {"and", "or", "not", "true", "false"}
    return sorted({match.group(0) for match in
                   IDENT_RE.finditer(expression or "")
                   if match.group(0).lower() not in ignored})


def _rank_condition(identifier):
    value = identifier.lower()
    return value.startswith("rank-") or value.startswith("rank_")


def _prerequisite_source_kinds(raw_tokens, faction):
    return sorted({"prerequisite_" + token_kind(token, faction)
                   for token in raw_tokens})


def direct_promotion_buff(raw_actor):
    """Whether the authored actor directly inherits the hidden buff."""
    return any(child.key.lower().startswith("inherits") and
               "promotionunitbuff" in (child.value or "").lower()
               for child in raw_actor.children)


def _promotion_tokens(model, faction):
    tokens = set()
    for actor in model.rs.actors:
        if not actor.startswith(faction + "_promotion_"):
            continue
        resolved = model.rs.resolve(actor)
        if resolved is None:
            continue
        for child in resolved.children_named("ProvidesPrerequisite"):
            tokens.add((child.get("Prerequisite") or actor).strip().lower())
    return tokens


def _promotion_units(model, faction):
    tokens = _promotion_tokens(model, faction)
    rows = []
    for actor in sorted(model.rs.actors):
        if not actor.startswith(faction + "_") or "_promotion_" in actor:
            continue
        resolved = model.rs.resolve(actor)
        if resolved is None or not model.is_buildable(resolved):
            continue
        matched = [token for token in model.positive_prereqs(resolved) if token in tokens]
        if len(matched) != 1:
            continue
        rows.append((actor, matched[0], resolved))
    return rows


def _condition_inventory(resolved, faction):
    condition_rows = []
    condition_sources = defaultdict(list)
    for child in resolved.children:
        base = child.key.split("@", 1)[0]
        if base not in CONDITION_PRODUCERS:
            continue
        condition_expression = (child.get("Condition") or "").strip()
        identifiers = condition_identifiers(condition_expression)
        if not identifiers:
            continue
        raw_tokens = []
        if base == "GrantConditionOnPrerequisite":
            raw_tokens = [item.strip() for item in
                          (child.get("Prerequisites") or "").split(",")
                          if item.strip()]
            source_kinds = _prerequisite_source_kinds(raw_tokens, faction)
        elif any(_rank_condition(identifier) for identifier in identifiers):
            source_kinds = ["rank"]
        elif base == "ExternalCondition":
            source_kinds = ["external_state"]
        else:
            source_kinds = ["runtime_state"]
        row = {
            "trait": child.key,
            "condition": condition_expression,
            "condition_identifiers": identifiers,
            "prerequisites": raw_tokens,
            "source_kinds": source_kinds,
            "source": {"file": str(child.file), "line": child.line},
        }
        condition_rows.append(row)
        for identifier in identifiers:
            condition_sources[identifier].append(row)

    stat_rows = []
    for child in resolved.children:
        base = child.key.split("@", 1)[0]
        if base not in STAT_TRAITS:
            continue
        requires = (child.get("RequiresCondition") or "").strip()
        if not requires:
            continue
        identifiers = condition_identifiers(requires)
        resolutions = []
        unresolved_identifiers = []
        for identifier in identifiers:
            sources = condition_sources.get(identifier, [])
            source_kinds = sorted({kind for source in sources
                                   for kind in source["source_kinds"]})
            if not source_kinds:
                source_kinds = ["unknown"]
                unresolved_identifiers.append(identifier)
            resolutions.append({
                "identifier": identifier,
                "source_kinds": source_kinds,
                "sources": [{"trait": source["trait"],
                             "file": source["source"]["file"],
                             "line": source["source"]["line"]}
                            for source in sources],
            })
        source_kinds = sorted({kind for item in resolutions
                               for kind in item["source_kinds"]})
        stat_rows.append({
            "trait": child.key,
            "base_trait": base,
            "modifier": finite(child.get("Modifier")),
            "requires_condition": requires,
            "condition_identifiers": identifiers,
            "condition_resolution": resolutions,
            "source_kinds": source_kinds,
            "unresolved_condition_identifiers": unresolved_identifiers,
            "source": {"file": str(child.file), "line": child.line},
        })
    return condition_rows, stat_rows


def build_report(model=None, *, root=ROOT, tool_path=None):
    model = model or Model(root)
    rows = []
    for faction in FACTIONS:
        for actor, token, resolved in _promotion_units(model, faction):
            raw = model.rs.actor(actor)
            condition_rows, stat_rows = _condition_inventory(resolved, faction)
            promotion_conditions = [row for row in condition_rows
                                    if "prerequisite_promotion" in row["source_kinds"]]
            upgrade_conditions = [row for row in condition_rows
                                  if "prerequisite_upgrade_or_doctrine" in row["source_kinds"]]
            upgrade_stats = [row for row in stat_rows
                             if "prerequisite_upgrade_or_doctrine" in row["source_kinds"]]
            unresolved_stats = [row for row in stat_rows
                                if row["unresolved_condition_identifiers"]]
            rows.append({
                "faction": faction,
                "actor": actor,
                "promotion_token": token,
                "unit_type": model.unit_type(actor),
                "direct_promotion_unit_buff": direct_promotion_buff(raw),
                "source": {"file": str(raw.file), "line": raw.line},
                "promotion_condition_hooks": promotion_conditions,
                "upgrade_condition_hooks": upgrade_conditions,
                "condition_source_hooks": condition_rows,
                "conditional_stat_traits": stat_rows,
                "upgrade_conditioned_stat_traits": upgrade_stats,
                "unresolved_condition_stat_traits": unresolved_stats,
            })

    trait_counts = Counter()
    upgrade_trait_counts = Counter()
    hook_counts = Counter()
    source_kind_counts = Counter()
    unresolved_identifier_counts = Counter()
    for row in rows:
        for trait in row["conditional_stat_traits"]:
            trait_counts[trait["base_trait"]] += 1
        for trait in row["upgrade_conditioned_stat_traits"]:
            upgrade_trait_counts[trait["base_trait"]] += 1
        hook_counts["promotion"] += len(row["promotion_condition_hooks"])
        hook_counts["upgrade_or_doctrine"] += len(row["upgrade_condition_hooks"])
        for hook in row["condition_source_hooks"]:
            source_kind_counts.update(hook["source_kinds"])
        for trait in row["unresolved_condition_stat_traits"]:
            unresolved_identifier_counts.update(
                trait["unresolved_condition_identifiers"])

    return {
        "schema": 2,
        "status": "REVIEW_ONLY",
        "scope": "Current RA1 Allies, RA1 Soviets, TD GDI and TD Nod buildable actors with exactly one explicit promotion prerequisite; no YAML or runtime writeback.",
        "policy": {
            "decision": "HOLD",
            "meaning": "This receipt inventories condition wiring and stat hooks. It does not remove PromotionUnitBuff, price upgrades, or decide whether any multiplier is fair.",
            "promotion_test_scope": "This inventory does not certify a factory-ready state. It separates prerequisite upgrade wiring, ranks, external/runtime states and individually unknown identifiers so a later comparison can define its state explicitly.",
        },
        "method": [
            "Resolve the active include graph through cameo_model.",
            "Select only buildable actors with one explicit promotion-token prerequisite.",
            "Classify prerequisite-driven conditions separately from rank, external and runtime state producers.",
            "Parse case-sensitive condition names without treating numeric comparison literals as identifiers. Resolve each identifier independently so one known name cannot hide another unknown name in the same expression.",
        ],
        "inputs": {
            "factions": list(FACTIONS),
            "model_scope": "active mods/cameo include graph",
            "tool": str(tool_path) if tool_path else None,
        },
        "summary": {
            "promotion_units": len(rows),
            "direct_promotion_unit_buff": sum(row["direct_promotion_unit_buff"] for row in rows),
            "promotion_units_without_direct_buff": sum(not row["direct_promotion_unit_buff"] for row in rows),
            "promotion_condition_hooks": hook_counts["promotion"],
            "upgrade_or_doctrine_condition_hooks": hook_counts["upgrade_or_doctrine"],
            "conditional_stat_traits": sum(trait_counts.values()),
            "upgrade_conditioned_stat_traits": sum(upgrade_trait_counts.values()),
            "unresolved_condition_stat_traits": sum(len(row["unresolved_condition_stat_traits"]) for row in rows),
            "unresolved_condition_identifiers": sum(unresolved_identifier_counts.values()),
            "unique_unresolved_condition_identifiers": len(unresolved_identifier_counts),
            "unresolved_condition_identifier_counts": dict(sorted(unresolved_identifier_counts.items())),
            "condition_source_kind_counts": dict(sorted(source_kind_counts.items())),
            "conditional_stat_trait_counts": dict(sorted(trait_counts.items())),
            "upgrade_conditioned_stat_trait_counts": dict(sorted(upgrade_trait_counts.items())),
        },
        "rows": rows,
    }


def render_markdown(report):
    summary = report["summary"]
    lines = [
        "# Promotion and upgrade interaction inventory",
        "",
        "**REVIEW ONLY.** This receipt inventories condition sources and stat "
        "hooks for the current promotion cohort. It does not certify a "
        "factory-ready state, remove "
        "`^PromotionUnitBuff`, change prices or claim upgrade balance.",
        "",
        "## Summary",
        "",
        f"- Promotion units: **{summary['promotion_units']}**; direct `^PromotionUnitBuff`: **{summary['direct_promotion_unit_buff']}**; without the direct inherit: **{summary['promotion_units_without_direct_buff']}**.",
        f"- Promotion prerequisite hooks: **{summary['promotion_condition_hooks']}**; current-faction upgrade/doctrine hooks: **{summary['upgrade_or_doctrine_condition_hooks']}**.",
        f"- Conditional stat traits: **{summary['conditional_stat_traits']}**; upgrade/doctrine-conditioned traits: **{summary['upgrade_conditioned_stat_traits']}**; traits with at least one unresolved identifier: **{summary['unresolved_condition_stat_traits']}**.",
        f"- Individually unresolved identifier occurrences: **{summary['unresolved_condition_identifiers']}** across **{summary['unique_unresolved_condition_identifiers']}** names. Numeric comparison literals are excluded.",
        "- Conditions are wiring evidence only. Prerequisite upgrades, ranks, external/runtime states and unknown sources remain separate; mixed expressions retain every unresolved identifier.",
        "",
        "## Per-unit inventory",
        "",
        "| faction | actor | direct buff | promotion hooks | upgrade hooks | upgrade-conditioned stat traits | traits with unknown identifiers | unknown identifiers |",
        "|---|---|:---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["rows"]:
        lines.append(
            f"| `{row['faction']}` | `{row['actor']}` | {'yes' if row['direct_promotion_unit_buff'] else 'no'} | "
            f"{len(row['promotion_condition_hooks'])} | {len(row['upgrade_condition_hooks'])} | "
            f"{len(row['upgrade_conditioned_stat_traits'])} | {len(row['unresolved_condition_stat_traits'])} | "
            f"{sum(len(trait['unresolved_condition_identifiers']) for trait in row['unresolved_condition_stat_traits'])} |"
        )
    lines += [
        "",
        "## Guardrails",
        "",
        "- This inventory does not prove that a condition is active in a particular match; it reports authored wiring and condition references.",
        "- Unknown identifiers are unresolved evidence items, not implementation blockers or proof of broken gameplay.",
        "- Promotion-unit direct-buff counts are separate from the nine non-promotion direct inherits recorded by the discount receipt.",
        "- Upgrade valuation, status uptime, and runtime interactions remain deferred until the base/factory-ready candidate is stable.",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        out = diagnostic_output.validate_path(ROOT, args.out)
        markdown = diagnostic_output.validate_path(ROOT, args.markdown)
        if out == markdown:
            raise ValueError("JSON and Markdown outputs must be different paths")
        tool = Path(__file__).resolve()
        report = build_report(tool_path=tool)
        report["inputs"]["tool_sha256"] = hashlib.sha256(tool.read_bytes()).hexdigest()
        diagnostic_output.write_outputs(ROOT, {
            out: json.dumps(report, indent=2, sort_keys=True) + "\n",
            markdown: render_markdown(report),
        })
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
