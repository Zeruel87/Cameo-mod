#!/usr/bin/env python3
"""Prepare a review-only promotion-unit discount proposal.

Promotion units currently inherit ``^PromotionUnitBuff``. This receipt models
removing that hidden stat buff and adding a virtual prerequisite cost to the
existing prerequisite-chain tier curve. It does not edit promotion inherits,
costs, YAML or runtime behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FACTIONS = ("ra1_allies", "ra1_soviets", "td_gdi", "td_nod")
POLICY_VALUES = {
    "fixed_5000": lambda tier: 5000.0,
    "per_tier_1000": lambda tier: 1000.0 * tier,
    "per_tier_1500": lambda tier: 1500.0 * tier,
    "per_tier_2000": lambda tier: 2000.0 * tier,
}

FORMULA_BUFF_AXES = {
    "SpeedMultiplier": "speed",
    "RangeMultiplier": "range",
    "FirepowerMultiplier": "firepower",
    "ReloadDelayMultiplier": "reload",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite(value):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if number == number and abs(number) != float("inf") else None


def _promotion_depths(model, faction: str):
    """Return promotion-token -> column depth from authored prerequisites."""
    promotions = {}
    for actor in model.rs.actors:
        if not actor.startswith(faction + "_promotion_"):
            continue
        resolved = model.rs.resolve(actor)
        if resolved is None:
            continue
        parents = [token for token in model.positive_prereqs(resolved)
                   if token.startswith(faction + "_promotion_")]
        promotions[actor] = parents

    from tier_chain import resolve_promotion_depths
    return resolve_promotion_depths(promotions)


def _unit_rows(model, tier_chain, faction: str, tier_multiplier):
    depths = _promotion_depths(model, faction)
    rows = []
    for actor in sorted(model.rs.actors):
        if not actor.startswith(faction + "_") or "_promotion_" in actor:
            continue
        resolved = model.rs.resolve(actor)
        if resolved is None:
            continue
        buildable = resolved.child("Buildable")
        if buildable is None or not buildable.get("Queue"):
            continue
        promotion_tokens = [token for token in model.positive_prereqs(resolved)
                            if token in depths]
        if len(promotion_tokens) != 1:
            # Multiple promotion tokens or none is not a single tiered unit
            # and should not be assigned a guessed discount.
            continue
        promotion = promotion_tokens[0]
        promotion_tier = depths[promotion]
        if promotion_tier is None:
            continue
        chain_cost = _finite(tier_chain.chain_cost(actor))
        if chain_cost is None:
            continue
        base_multiplier = tier_multiplier(chain_cost)
        candidates = {}
        for name, value in POLICY_VALUES.items():
            virtual_cost = value(promotion_tier)
            projected_multiplier = tier_multiplier(chain_cost + virtual_cost)
            candidates[name] = {
                "virtual_cost": virtual_cost,
                "projected_multiplier": projected_multiplier,
                "absolute_discount": 1.0 - projected_multiplier,
                "relative_discount": (
                    1.0 - projected_multiplier / base_multiplier
                    if base_multiplier else None
                ),
                "no_change_due_to_plateau": (
                    projected_multiplier == base_multiplier
                ),
            }
        rows.append({
            "faction": faction,
            "actor": actor,
            "promotion": promotion,
            "promotion_tier": promotion_tier,
            "chain_cost": chain_cost,
            "base_multiplier": base_multiplier,
            "candidates": candidates,
        })
    return rows


def _buff_scope(model, promotion_rows):
    """Count direct PromotionUnitBuff inherits and separate non-promotion uses."""
    promotion_actors = {row["actor"] for row in promotion_rows}
    direct = []
    for faction in FACTIONS:
        for actor in model.rs.actors:
            if not actor.startswith(faction + "_") or actor.startswith("^"):
                continue
            raw = model.rs.actor(actor)
            if raw is None:
                continue
            if any(
                child.key.lower().startswith("inherits")
                and "promotionunitbuff" in (child.value or "").lower()
                for child in raw.children
            ):
                direct.append(actor)
    direct_set = set(direct)
    return {
        "direct_inherit_actors": len(direct),
        "direct_inherit_promotion_units": len(direct_set & promotion_actors),
        "direct_inherit_nonpromotion_actors": len(direct_set - promotion_actors),
        "promotion_units_without_direct_inherit": len(promotion_actors - direct_set),
        "direct_inherit_actor_names": sorted(direct_set),
    }


def _active_buff_scope(model):
    """Count the same distinction across the complete active include graph."""
    direct = set()
    promotion_units = set()
    for actor in model.rs.actors:
        if actor.startswith("^"):
            continue
        raw = model.rs.actor(actor)
        if raw is not None and any(
            child.key.lower().startswith("inherits")
            and "promotionunitbuff" in (child.value or "").lower()
            for child in raw.children
        ):
            direct.add(actor)
        resolved = model.rs.resolve(actor)
        if resolved is None:
            continue
        buildable = resolved.child("Buildable")
        if buildable is not None and buildable.get("Queue") and any(
            "_promotion_" in token.lower()
            for token in model.positive_prereqs(resolved)
        ):
            promotion_units.add(actor)
    return {
        "direct_inherit_actors": len(direct),
        "direct_inherit_promotion_units": len(direct & promotion_units),
        "direct_inherit_nonpromotion_actors": len(direct - promotion_units),
        "promotion_units_without_direct_inherit": len(promotion_units - direct),
    }


def _promotion_buff_profile(model):
    """Resolve the active promotion template and describe its priced subset.

    Commented traits are absent from the resolved MiniYAML node, so this avoids
    preserving historical modifiers in the calculation by hand.
    """
    resolved = model.rs.resolve("^PromotionUnitBuff")
    if resolved is None:
        return {
            "status": "UNRESOLVED",
            "template": "^PromotionUnitBuff",
            "active_traits": [],
            "formula_axes": None,
        }

    active_traits = []
    axes = {"speed": 1.0, "range": 1.0, "firepower": 1.0, "reload": 1.0}
    for child in resolved.children:
        base_trait = child.key.split("@", 1)[0]
        modifier = _finite(child.get("Modifier"))
        if modifier is None:
            continue
        axis = FORMULA_BUFF_AXES.get(base_trait)
        if axis == "reload":
            if modifier <= 0:
                return {
                    "status": "UNRESOLVED",
                    "template": "^PromotionUnitBuff",
                    "reason": f"invalid reload modifier {modifier}",
                    "active_traits": active_traits,
                    "formula_axes": None,
                }
            axes[axis] *= modifier / 100.0
        elif axis:
            axes[axis] *= modifier / 100.0
        active_traits.append({
            "trait": child.key,
            "base_trait": base_trait,
            "modifier": modifier,
            "formula_axis": axis,
            "included_in_price_context": axis is not None,
            "source": {"file": str(child.file), "line": child.line},
        })

    axes["dps"] = axes["firepower"] / axes["reload"]
    return {
        "status": "RESOLVED",
        "template": "^PromotionUnitBuff",
        "source": {"file": str(resolved.file), "line": resolved.line},
        "active_traits": active_traits,
        "formula_axes": axes,
    }


def _formula_buff_impact(profile, price_function):
    """Return formula context for the resolved speed/range/DPS axes."""
    axes = profile.get("formula_axes")
    if profile.get("status") != "RESOLVED" or not axes:
        return {"status": "UNRESOLVED", "price_factor": None,
                "equivalent_discount": None}
    base_price = price_function(1, 1, 1, 1, 1, 1, 1, 1, 1)
    buff_price = price_function(
        1, axes["speed"], axes["range"], axes["dps"],
        1, 1, 1, 1, 1,
    )
    factor = buff_price / base_price
    return {
        "status": "RESOLVED",
        "price_factor": factor,
        "equivalent_discount": 1.0 - 1.0 / factor,
        "formula_axes": dict(axes),
    }


def _summary(rows, candidate):
    by_tier = defaultdict(list)
    for row in rows:
        value = row["candidates"][candidate]["relative_discount"]
        if value is not None:
            by_tier[row["promotion_tier"]].append(value)

    def stats(values):
        if not values:
            return {"count": 0}
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "minimum": min(values),
            "maximum": max(values),
            "plateau_no_change": sum(value == 0.0 for value in values),
        }

    return {
        "rows": len(rows),
        "relative_discount": stats([
            row["candidates"][candidate]["relative_discount"]
            for row in rows
            if row["candidates"][candidate]["relative_discount"] is not None
        ]),
        "by_promotion_tier": {
            str(tier): stats(values)
            for tier, values in sorted(by_tier.items())
        },
    }


def build_report(model, tier_chain, tier_multiplier, *, tool_path=None):
    rows = []
    for faction in FACTIONS:
        rows.extend(_unit_rows(model, tier_chain, faction, tier_multiplier))

    import formula
    buff_profile = _promotion_buff_profile(model)
    buff_impact = _formula_buff_impact(
        buff_profile, formula.class_baseline_price)

    candidate_summary = {
        candidate: _summary(rows, candidate)
        for candidate in POLICY_VALUES
    }
    faction_summary = {}
    for faction in FACTIONS:
        faction_rows = [row for row in rows if row["faction"] == faction]
        faction_summary[faction] = {
            candidate: _summary(faction_rows, candidate)
            for candidate in POLICY_VALUES
        }
    buff_scope = _buff_scope(model, rows)
    active_buff_scope = _active_buff_scope(model)

    return {
        "schema": 2,
        "status": "REVIEW_ONLY",
        "scope": "Current RA1 Allies, RA1 Soviets, TD GDI and TD Nod promotion-unlocked buildable actors with one explicit promotion prerequisite; no YAML or runtime writeback.",
        "method": [
            "Promotion tier is the authored prerequisite-column depth, from 1 through 4; no tier is inferred from actor strength.",
            "The existing prerequisite-chain cost is read through tools/balance/tier_chain.py and formula.tier_multiplier.",
            "Each virtual prerequisite candidate is evaluated as f(C + virtual_cost) relative to f(C).",
            "Resolve ^PromotionUnitBuff from the active include graph. Only active speed, range, firepower and reload modifiers feed the formula context; other active traits are listed without assigning them a price.",
        ],
        "policy": {
            "formula": "f(C) = 1 / (1 + (C - B) / S), clamped at 1.0 for C <= B",
            "candidate_values": {
                "fixed_5000": "5000 virtual credits for every promotion unit",
                "per_tier_1000": "1000 virtual credits times promotion tier",
                "per_tier_1500": "1500 virtual credits times promotion tier",
                "per_tier_2000": "2000 virtual credits times promotion tier",
            },
            "recommendation": "Use per_tier_1500 as the maintainer-accepted first bounded playtest candidate; retain per_tier_2000 as an upper sensitivity case. Neither is a final universal value until explicit replacement mappings and playtest outcomes are reviewed.",
            "reason": "The 1500-per-tier value is the accepted pilot direction. The formula response to the currently active PromotionUnitBuff traits is reported as context, not as the selection rationale; the rational curve can leave some early units on its C <= B plateau, so a virtual cost is not a guaranteed nonzero discount.",
            "writeback": False,
        },
        "formula_constants": {
            "tier_B": getattr(formula, "TIER_B", None),
            "tier_S": getattr(formula, "TIER_S", None),
            "promotion_buff_profile": buff_profile,
            "promotion_buff_formula_context": buff_impact,
        },
        "inputs": {
            "tool": str(tool_path) if tool_path else None,
            "factions": list(FACTIONS),
            "model_scope": "active mods/cameo include graph",
        },
        "summary": {
            "promotion_units": len(rows),
            "promotion_tier_counts": dict(sorted(Counter(
                row["promotion_tier"] for row in rows
            ).items())),
            "buff_scope": buff_scope,
            "active_include_buff_scope": active_buff_scope,
            "candidate_summary": candidate_summary,
            "faction_summary": faction_summary,
        },
        "rows": rows,
    }


def _pct(value):
    return "—" if value is None else f"{value:.1%}"


def render_markdown(report):
    policy = report["policy"]
    summary = report["summary"]
    lines = [
        "# Promotion-unit discount proposal",
        "",
        "**REVIEW ONLY.** This receipt models virtual prerequisite costs for "
        "promotion-unlocked units. It does not remove `^PromotionUnitBuff`, "
        "change costs, edit YAML or claim playtest results.",
        "",
        "## Recommendation",
        "",
        f"- First bounded candidate: **1500 virtual credits per promotion tier**.",
        f"- Upper sensitivity case: **2000 virtual credits per promotion tier**.",
        f"- Formula-only equivalent discount for the active priced subset of `^PromotionUnitBuff`: **{_pct(report.get('formula_constants', {}).get('promotion_buff_formula_context', {}).get('equivalent_discount'))}**.",
        f"- Promotion units evaluated: **{summary.get('promotion_units', 0)}** across the four current factions.",
        f"- Direct `^PromotionUnitBuff` inherits in those factions: **{summary.get('buff_scope', {}).get('direct_inherit_actors', 0)}** actors (**{summary.get('buff_scope', {}).get('direct_inherit_promotion_units', 0)}** promotion units and **{summary.get('buff_scope', {}).get('direct_inherit_nonpromotion_actors', 0)}** non-promotion actors).",
        f"- Complete active include graph: **{summary.get('active_include_buff_scope', {}).get('direct_inherit_actors', 0)}** direct inherits; **{summary.get('active_include_buff_scope', {}).get('direct_inherit_promotion_units', 0)}** are on promotion-token units and **{summary.get('active_include_buff_scope', {}).get('direct_inherit_nonpromotion_actors', 0)}** are not.",
        "",
        policy["reason"],
        "",
        "## Candidate summary",
        "",
        "| candidate | rows | mean relative discount | median | range | plateau rows |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    candidate_summary = summary.get("candidate_summary", {})
    for candidate in POLICY_VALUES:
        stats = (candidate_summary.get(candidate, {}).get("relative_discount") or {})
        lines.append(
            f"| `{candidate}` | {stats.get('count', 0)} | {_pct(stats.get('mean'))} | {_pct(stats.get('median'))} | {_pct(stats.get('minimum'))}–{_pct(stats.get('maximum'))} | {stats.get('plateau_no_change', 0)} |"
        )

    lines += [
        "",
        "## Per-unit evidence",
        "",
        "| faction | actor | promotion tier | C | f(C) | 1500×tier discount | 2000×tier discount |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in report.get("rows", []):
        lines.append(
            f"| {row['faction']} | `{row['actor']}` | {row['promotion_tier']} | {row['chain_cost']:.0f} | {row['base_multiplier']:.4f} | {_pct(row['candidates']['per_tier_1500']['relative_discount'])} | {_pct(row['candidates']['per_tier_2000']['relative_discount'])} |"
        )
    lines += [
        "",
        "## Guardrails",
        "",
        "- This is a proposal for the next playtest, not permission to remove promotion inherits or rewrite costs.",
        "- The rational tier curve has a C <= B plateau; virtual credits below that boundary produce no discount. Do not force a discount by changing B or S.",
        "- Promotion superiority, prerequisite-column tier correctness, upgrade interactions and the Sunday no-upgrade scope remain separate checks.",
        "- Seven promotion-gated units in this scan have no direct `^PromotionUnitBuff` inherit; do not treat every promotion unit as a removal target. The nine non-promotion direct inherits need a separate disposition.",
        "- Active vision, detection and inaccuracy modifiers are disclosed in the JSON profile but are not assigned a value by the current price formula.",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args(argv)

    import sys
    sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]
    from cameo_model import Model
    from tier_chain import TierChain
    from formula import tier_multiplier

    model = Model()
    report = build_report(model, TierChain(model), tier_multiplier,
                          tool_path=Path(__file__).resolve())
    report["inputs"]["tool_sha256"] = _sha256(Path(__file__).resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "promotion_units": report["summary"]["promotion_units"],
        "promotion_tier_counts": report["summary"]["promotion_tier_counts"],
        "recommendation": report["policy"]["recommendation"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
