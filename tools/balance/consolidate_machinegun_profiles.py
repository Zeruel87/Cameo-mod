#!/usr/bin/env python3
"""Consolidate reviewed duplicate light/medium machine-gun profiles.

The selected roots use both canonical bullet profiles for the same hit.  This
pass keeps their summed flat and percentage damage but selects the profile that
matches the weapon's authored role.  Split air/ground routing and incomplete
damage definitions are deliberately excluded.
"""
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
    apply_compatibility_block,
    resolved_flat_total,
)
from miniyaml import Ruleset  # noqa: E402


PAIR = {"Bullet_Light", "Bullet_Medium"}
FINALIZED_DOWNSTREAM = {
    "JHighVWaveforce": ("Waveforce_HeavyFlatCompatibility", 12000, 8325),
    "JapanSpeedBoatGunWaveforce": (
        "Waveforce_HeavyFlatCompatibility", 6000, 9984),
    "light_inf_lmg_ordos_upgrade": ("Laser_HeavyFlatCompatibility", 6000, 9984),
}

# Every inheritance closure is explicit.  New descendants fail closed instead
# of silently inheriting a role choice that was never reviewed.
ROOTS = {
    "HMG_turret": (
        "Bullet_Medium", {"HMG_turret_upgrade", "d2k_airdefenseplatform"}),
    "HMGstealth": ("Bullet_Medium", {"HMGstealth_upgrade"}),
    "JHighV": ("Bullet_Medium", {"JHighVWaveforce"}),
    "JapanSpeedBoatGun": ("Bullet_Medium", {"JapanSpeedBoatGunWaveforce"}),
    "RaiderGuns": ("Bullet_Medium", {"RaiderGuns_upgrade"}),
    "light_inf_lmg": ("Bullet_Light", {"light_inf_lmg_ordos_upgrade"}),
}


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


def selections(rs: Ruleset) -> dict[str, str]:
    selected: dict[str, str] = {}
    for root, (destination, expected) in ROOTS.items():
        actual = descendants(rs, root)
        if actual != expected:
            raise RuntimeError(
                f"{root}: closure changed; added={sorted(actual - expected)}, "
                f"missing={sorted(expected - actual)}")
        for name in {root, *expected}:
            if name in selected:
                raise RuntimeError(f"{name}: selected through multiple roots")
            selected[name] = destination
    return selected


def inspect(rs: Ruleset, selected: dict[str, str]):
    plans = {}
    for name, destination in selected.items():
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            raise RuntimeError(f"{name}: missing resolved weapon")
        mains = set(main_warheads(resolved))
        compatibility = f"{destination}FlatCompatibility"
        if name in FINALIZED_DOWNSTREAM:
            final_key, final_damage, final_scale = FINALIZED_DOWNSTREAM[name]
            if mains != {final_key}:
                raise RuntimeError(f"{name}: downstream final main changed: {sorted(mains)}")
            node = flat_main_nodes(resolved, mains)[final_key]
            if int(str(node.get("Damage") or 0)) != final_damage:
                raise RuntimeError(f"{name}: downstream final damage changed")
            if int(str(node.get("PercentageScale") or 0)) != final_scale:
                raise RuntimeError(f"{name}: downstream final percentage changed")
            plans[name] = None
            continue
        if not (mains & PAIR) and compatibility in mains:
            plans[name] = None
            continue
        if not PAIR <= mains:
            raise RuntimeError(f"{name}: expected both bullet profiles; found {sorted(mains)}")
        nodes = flat_main_nodes(resolved, PAIR)
        if set(nodes) != PAIR:
            raise RuntimeError(f"{name}: bullet profiles are not both flat damage")
        contract_fields = (
            "ValidTargets", "InvalidTargets", "ValidRelationships",
            "InvalidRelationships", "AffectsParent", "TargetActorCenter",
        )
        contracts = {
            tuple(tokens(node.get(field)) for field in contract_fields)
            for node in nodes.values()
        }
        if len(contracts) != 1:
            raise RuntimeError(f"{name}: bullet target contracts differ")
        for tag, node in nodes.items():
            if any("PhysicalState" in child.key for child in node.children):
                raise RuntimeError(f"{name}: {tag} carries a physical-state hook")
        total = resolved_flat_total(resolved, PAIR)
        if total <= 0:
            raise RuntimeError(f"{name}: bullet pair has no positive flat damage")
        plans[name] = {
            "total": total,
            "targets": str(nodes[destination].get("ValidTargets") or ""),
            "scale": percentage_scale(resolved, PAIR, total),
        }
    states = {plan is None for plan in plans.values()}
    if len(states) > 1:
        raise RuntimeError("partial machine-gun cohort consolidation detected")
    return plans, states == {True}


def validate_result() -> None:
    rules = Ruleset(ROOT)
    selected = selections(rules)
    _plans, already = inspect(rules, selected)
    if not already:
        raise RuntimeError("machine-gun cohort remains unconsolidated")


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
    for root, (destination, children) in ROOTS.items():
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
            apply_compatibility_block(
                changed, path, name, destination, PAIR,
                plan["total"], plan["targets"], inherit_template=False)
            set_scale(changed, path, name, destination, plan["scale"])
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")
    cleanup_stale_removals(set(selected))
    validate_result()
    print(f"Applied and validated {len(changed)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
