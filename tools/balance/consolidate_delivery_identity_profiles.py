#!/usr/bin/env python3
"""Consolidate reviewed duplicate mains whose delivery identity is unambiguous."""
from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from audit_three_way_split import main_warheads  # noqa: E402
from consolidate_final_safe_cohorts import (  # noqa: E402
    cleanup_stale_removals,
    ensure_template_inherit,
    flat_main_nodes,
    percentage_scale,
    set_scale,
    tokens,
)
from consolidate_reviewed_weapon_roots import (  # noqa: E402
    add_compatibility_templates,
    apply_compatibility_block,
    resolved_flat_total,
)
from miniyaml import Ruleset  # noqa: E402


# Each choice is backed by the already-resolved projectile/effect identity:
# lightning/Tesla, flak, and chaingun bullets respectively.
ROOTS = {
    "BTRTeslaMachineGun": (
        "Tesla_Heavy",
        {"MissileAP_Light", "Tesla_Heavy"},
        {
            "BTRTeslaMachineGunArc", "BTRTeslaMachineGunArcFragment1",
            "BTRTeslaMachineGunArcFragment1AA", "BTRTeslaMachineGunArc_AA",
            "BTRTeslaMachineGun_AA",
        },
    ),
    "JapaneseHovercraftFlak": (
        "Flak_Medium",
        {"Bullet_Light", "Flak_Medium"},
        {
            "JapaneseHovercraftFlakAA", "JapaneseHovercraftFlakAAkWaveforce",
            "JapaneseHovercraftFlakWaveforce",
        },
    ),
    "SteelMantaHunterCannons": (
        "Bullet_Medium",
        {"Bullet_Medium", "Flak_Medium"},
        {
            "SteelMantaHunterCannonsAAResonanceBounce1",
            "SteelMantaHunterCannonsAAResonanceBounce2",
            "SteelMantaHunterCannonsAAResonance_AA",
            "SteelMantaHunterCannonsResonance",
            "SteelMantaHunterCannonsResonanceBounce1",
            "SteelMantaHunterCannonsResonanceBounce2",
            "SteelMantaHunterCannons_AA",
        },
    ),
}

DESTINATION_OVERRIDES = {
    "SteelMantaHunterCannons_AA": "Flak_Medium",
    "SteelMantaHunterCannonsAAResonance_AA": "Flak_Medium",
    "SteelMantaHunterCannonsAAResonanceBounce1": "Flak_Medium",
    "SteelMantaHunterCannonsAAResonanceBounce2": "Flak_Medium",
}

# This child starts the Manta's separately routed anti-air inheritance branch.
ROUTE_ROOTS = {"SteelMantaHunterCannons_AA": "Flak_Medium"}


def descendants(rs: Ruleset, root: str) -> set[str]:
    direct: dict[str, set[str]] = {}
    for name, node in rs.weapons.items():
        for _, parent in rs.inherits_of(node):
            if parent in rs.weapons:
                direct.setdefault(parent, set()).add(name)
    seen: set[str] = set()
    stack = list(direct.get(root, set()))
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        stack.extend(direct.get(name, set()))
    return {name for name in seen if not name.startswith("^")}


def selections(rs: Ruleset):
    selected = {}
    for root, (destination, pair, expected) in ROOTS.items():
        actual = descendants(rs, root)
        if actual != expected:
            raise RuntimeError(
                f"{root}: closure changed; added={sorted(actual - expected)}, "
                f"missing={sorted(expected - actual)}")
        for name in {root, *expected}:
            if name in selected:
                raise RuntimeError(f"{name}: selected through multiple roots")
            selected[name] = (DESTINATION_OVERRIDES.get(name, destination), pair, root)
    return selected


def inspect(rs: Ruleset, selected):
    plans = {}
    for name, (destination, pair, _root) in selected.items():
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            raise RuntimeError(f"{name}: missing resolved weapon")
        mains = set(main_warheads(resolved))
        compatibility = f"{destination}FlatCompatibility"
        if not (mains & pair) and compatibility in mains:
            plans[name] = None
            continue
        if not pair <= mains:
            raise RuntimeError(f"{name}: expected {sorted(pair)}; found {sorted(mains)}")
        nodes = flat_main_nodes(resolved, pair)
        if set(nodes) != pair:
            raise RuntimeError(f"{name}: selected profiles are not both flat damage")
        fields = (
            "ValidTargets", "InvalidTargets", "ValidRelationships",
            "InvalidRelationships", "AffectsParent", "TargetActorCenter",
        )
        if len({tuple(tokens(node.get(field)) for field in fields)
                for node in nodes.values()}) != 1:
            raise RuntimeError(f"{name}: selected target contracts differ")
        for tag, node in nodes.items():
            if any("PhysicalState" in child.key for child in node.children):
                raise RuntimeError(f"{name}: {tag} carries a physical-state hook")
        total = resolved_flat_total(resolved, pair)
        if total <= 0:
            raise RuntimeError(f"{name}: selected pair has no positive flat damage")
        plans[name] = {
            "total": total,
            "targets": str(nodes[destination].get("ValidTargets") or ""),
            "scale": percentage_scale(resolved, pair, total),
        }
    return plans, all(plan is None for plan in plans.values())


def validate_result() -> None:
    rules = Ruleset(ROOT)
    _plans, already = inspect(rules, selections(rules))
    if not already:
        raise RuntimeError("delivery-identity cohort remains unconsolidated")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rules = Ruleset(ROOT)
    selected = selections(rules)
    plans, already = inspect(rules, selected)
    if already:
        if args.apply:
            removed = cleanup_stale_removals(set(selected))
            validate_result()
            print(f"Removed {removed} stale descendant removals")
        print(f"Already consolidated {len(selected)} concrete definitions")
        return 0
    print(f"{len(ROOTS)} roots; {len(selected)} concrete definitions")
    if not args.apply:
        print("Dry run: closure, routing, state, and arithmetic guards pass")
        return 0

    changed: dict[pathlib.Path, list[str]] = {}
    add_compatibility_templates(
        changed, rules, {destination for destination, _pair, _root in selected.values()})
    for root, (destination, pair, children) in ROOTS.items():
        root_node = rules.weapon(root)
        if root_node is None:
            raise RuntimeError(f"{root}: missing source weapon")
        ensure_template_inherit(changed, pathlib.Path(root_node.file), root, destination)
        for name in {root, *children}:
            node = rules.weapon(name)
            if node is None:
                raise RuntimeError(f"{name}: missing source weapon")
            plan = plans[name]
            if plan is None:
                continue
            path = pathlib.Path(node.file)
            selected_destination = selected[name][0]
            if name in ROUTE_ROOTS:
                ensure_template_inherit(
                    changed, path, name, ROUTE_ROOTS[name])
            apply_compatibility_block(
                changed, path, name, selected_destination, pair,
                plan["total"], plan["targets"],
                extra_removals=(
                    {f"{destination}FlatCompatibility"}
                    if name in ROUTE_ROOTS else None),
                inherit_template=False)
            set_scale(changed, path, name, selected_destination, plan["scale"])
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")
    cleanup_stale_removals(set(selected))
    validate_result()
    print(f"Applied and validated {len(changed)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
