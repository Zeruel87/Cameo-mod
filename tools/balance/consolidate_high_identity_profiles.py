#!/usr/bin/env python3
"""Collapse the delivery-aligned subset of plan_warhead_collapse HIGH roots."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from audit_three_way_split import main_warheads  # noqa: E402
from consolidate_compatibility_profiles import flat_nodes  # noqa: E402
from consolidate_final_safe_cohorts import percentage_scale, set_scale, tokens  # noqa: E402
from consolidate_reviewed_weapon_roots import (  # noqa: E402
    add_compatibility_templates,
    apply_compatibility_block,
    resolved_flat_total,
)
from miniyaml import Ruleset  # noqa: E402


# root: destination, old mains, exact descendants, total, folded scale
SPECS = {
    "AsianGrenade": (
        "Concussion_Medium", {"CannonHE_Medium", "Concussion_Medium"},
        {"AsianGrenade_elite"}, 8000, 9988,
    ),
    "asianalliance_asianmilitia_grenade": (
        "Concussion_Medium", {"CannonHE_Medium", "Concussion_Medium"},
        {"asianalliance_asianmilitia_grenade_elite"}, 8000, 9988,
    ),
    "IxRailgunDroneBullet": (
        "Railgun_Heavy", {"CannonHE_Medium", "Railgun_Heavy"}, set(),
        24000, 2496,
    ),
    "TSAssaultCannonTalSonic": (
        "Sonic_Medium", {"Bullet_Medium", "Sonic_Medium"}, set(),
        16000, 6244,
    ),
}

PRESERVED_HASHES = {
    "AsianGrenade": "366e5420ab6bdde5ba2affddb704ba6f3e2716f69a42e363cad26d8545f2f5a0",
    "AsianGrenade_elite": "36892662d67269b7a95aad83211f8730d0294ac20a66e70eeeff6fe3490f39ab",
    "asianalliance_asianmilitia_grenade": "efc2a6ac497014679c90e887d3b7dd9cbcb60f4c231897daccfd134edef1420d",
    "asianalliance_asianmilitia_grenade_elite": "bcb0ae17f7673a55b7127faef9f93d1d212b1aa8f440de9e4203d901cb1dc2ff",
    "IxRailgunDroneBullet": "8f6f05b056d48d7a61c623779ea6b3115aef386a6c10a681e7ad94a92ebb96b1",
    # Post-consolidation correction: Wolverine Mk II keeps its advertised weak
    # AA role after Sonic Weaponry replaces the base armament.
    "TSAssaultCannonTalSonic": "6351589c35a2e3c2e9dac7dce494ecaed4be168eea38f407dda8affe87125e08",
}

CANONICAL = re.compile(r"^\^Warhead_([A-Za-z]+)_(\w+)$")
CONTRACT_FIELDS = (
    "ValidTargets", "InvalidTargets", "ValidRelationships",
    "InvalidRelationships", "AffectsParent", "TargetActorCenter",
)


def descendants(rs: Ruleset, root: str) -> set[str]:
    direct: dict[str, set[str]] = collections.defaultdict(set)
    for name, node in rs.weapons.items():
        for _, parent in rs.inherits_of(node):
            if parent in rs.weapons:
                direct[parent].add(name)
    seen: set[str] = set()
    stack = list(direct[root])
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        stack.extend(direct[name])
    return {name for name in seen if not name.startswith("^")}


def selections(rs: Ruleset) -> dict[str, tuple[str, set[str], int, int]]:
    selected = {}
    for root, (destination, old_keys, expected, total, scale) in SPECS.items():
        actual = descendants(rs, root)
        if actual != expected:
            raise RuntimeError(
                f"{root}: closure changed; added={sorted(actual - expected)}, "
                f"missing={sorted(expected - actual)}")
        local = rs.weapon(root)
        canonical = {
            "_".join(match.group(1, 2))
            for child in local.children
            if child.key == "Inherits" or child.key.startswith("Inherits@")
            if child.value and (match := CANONICAL.match(str(child.value).strip()))
        }
        if canonical != {destination}:
            raise RuntimeError(
                f"{root}: expected sole canonical destination {destination}; "
                f"found {sorted(canonical)}")
        for name in {root, *expected}:
            if name in selected:
                raise RuntimeError(f"{name}: selected through multiple roots")
            selected[name] = (destination, old_keys, total, scale)
    return selected


def node_payload(node):
    return [node.key, node.value, [node_payload(child) for child in node.children]]


def resolved_hash(rs: Ruleset, name: str, old_keys: set[str], destination: str) -> str:
    resolved = rs.resolve_weapon(name)
    excluded = {f"Warhead@{key}" for key in old_keys}
    excluded.add(f"Warhead@{destination}FlatCompatibility")
    payload = [node_payload(child) for child in resolved.children
               if child.key not in excluded]
    return hashlib.sha256(
        json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def inspect(rs: Ruleset) -> bool:
    selected = selections(rs)
    states = set()
    for name, (destination, old_keys, total, expected_scale) in selected.items():
        resolved = rs.resolve_weapon(name)
        mains = set(main_warheads(resolved))
        compatibility = f"{destination}FlatCompatibility"
        if mains == old_keys:
            states.add(False)
            if any(key.startswith("PreservedFlat") or key == "1Dam"
                   for key in mains):
                raise RuntimeError(f"{name}: special main entered selected cohort")
            nodes = flat_nodes(resolved)
            if not old_keys <= set(nodes):
                raise RuntimeError(f"{name}: selected main is not flat damage")
            contracts = {
                tuple(tokens(nodes[key].get(field)) for field in CONTRACT_FIELDS)
                for key in old_keys
            }
            if len(contracts) != 1:
                raise RuntimeError(f"{name}: selected route contracts differ")
            for key in old_keys:
                if any("PhysicalState" in child.key or child.key == "IntegrityScale"
                       for child in nodes[key].children):
                    raise RuntimeError(f"{name}: {key} carries a state hook")
            if resolved_flat_total(resolved, old_keys) != total:
                raise RuntimeError(f"{name}: selected total changed")
            if percentage_scale(resolved, old_keys, total) != expected_scale:
                raise RuntimeError(f"{name}: folded percentage arithmetic changed")
        elif mains == {compatibility}:
            states.add(True)
            node = flat_nodes(resolved).get(compatibility)
            if node is None or int(str(node.get("Damage") or 0)) != total:
                raise RuntimeError(f"{name}: applied destination total changed")
            if int(str(node.get("PercentageScale") or 0)) != expected_scale:
                raise RuntimeError(f"{name}: applied PercentageScale changed")
        else:
            raise RuntimeError(
                f"{name}: expected {sorted(old_keys)} or {compatibility}; "
                f"found {sorted(mains)}")
        if resolved_hash(rs, name, old_keys, destination) != PRESERVED_HASHES[name]:
            raise RuntimeError(f"{name}: non-selected behavior hash changed")
    if len(states) != 1:
        raise RuntimeError("partial HIGH identity consolidation detected")
    return states == {True}


def apply_changes(rs: Ruleset) -> None:
    selected = selections(rs)
    changed: dict[pathlib.Path, list[str]] = {}
    add_compatibility_templates(
        changed, rs, {destination for destination, _keys, _total, _scale
                      in selected.values()})
    for root, (destination, old_keys, _expected, total, scale) in SPECS.items():
        node = rs.weapon(root)
        path = pathlib.Path(node.file)
        resolved = rs.resolve_weapon(root)
        target_node = flat_nodes(resolved)[destination]
        apply_compatibility_block(
            changed, path, root, destination, old_keys, total,
            str(target_node.get("ValidTargets") or ""))
        set_scale(changed, path, root, destination, scale)
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")


def validate_result() -> None:
    if not inspect(Ruleset(ROOT)):
        raise RuntimeError("HIGH identity cohort remains unconsolidated")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    rules = Ruleset(ROOT)
    already = inspect(rules)
    if already:
        print(f"Already consolidated {len(selections(rules))} concrete definitions")
        return 0
    print(f"{len(SPECS)} roots; {len(selections(rules))} concrete definitions")
    if not args.apply:
        print("Dry run: identities, closures, routes, states, percentages, and hashes pass")
        return 0
    apply_changes(rules)
    validate_result()
    print("Applied and validated 3 weapon files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
