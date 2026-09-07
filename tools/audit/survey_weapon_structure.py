#!/usr/bin/env python3
"""Inventory stacked-main weapons by how live rules can reach them.

The three sets are deliberately separate:

* ``all_concrete``: every non-template weapon definition in the active ruleset;
* ``direct_actor_armament``: named by an actor Armament's Weapon field;
* ``transitive_weapon_graph``: named anywhere in a resolved actor through a
  weapon-reference field, then closed over the same fields in resolved weapons.

This is a reachability inventory, not deletion authorization.  Definitions outside
the modeled graph are reported as ``unreached`` rather than declared dead.

Usage:
  python tools/audit/survey_weapon_structure.py
  python tools/audit/survey_weapon_structure.py --write
  python tools/audit/survey_weapon_structure.py --check
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "audit" / "latest" / "weapon_structure_inventory.json"
# Historical lower-only thresholds; retirement of exemptions does not raise them.
RAW_REACHABLE_BASELINE = 240
RAW_REACHABLE_EXCESS_BASELINE = 452
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from audit_three_way_split import (  # noqa: E402
    main_warhead_nodes,
    main_warheads,
)
from miniyaml import Ruleset  # noqa: E402


WEAPON_REF_FIELDS = {
    "Weapon", "Weapons", "TriggeredWeapon", "FallbackWeapon",
    "EmptyWeapon", "Explosion", "CasingWeapon", "ImpactWeapon",
    "TeleportWeapon", "DemolishWeapon", "HelixWeapon", "TriggerWeapon",
    "ThumpDamageWeapon", "DetonationWeapon", "MissileWeapon",
}
WEAPON_REF_MAP_FIELDS = {"MissileWeapons"}


def walk(node):
    for child in node.children:
        yield child
        yield from walk(child)


def canonical_weapon_names(known: set[str]) -> dict[str, str]:
    """Map case-insensitive weapon references to their canonical definition names."""
    canonical = {name.lower(): name for name in known}
    if len(canonical) != len(known):
        raise ValueError("weapon definitions differ only by letter case")
    return canonical


def weapon_references(node, known_by_case: dict[str, str]) -> set[str]:
    refs = set()
    for child in walk(node):
        field = child.key.split("@", 1)[0]
        values = []
        if field in WEAPON_REF_FIELDS and child.value:
            values.append(child.value)
        elif field in WEAPON_REF_MAP_FIELDS:
            if child.value:
                values.append(child.value)
            values.extend(descendant.value for descendant in walk(child)
                          if descendant.value)
        for raw in values:
            for value in str(raw).split(","):
                name = value.strip()
                canonical = known_by_case.get(name.lower())
                if canonical is not None:
                    refs.add(canonical)
    return refs


def direct_armament_references(
        rules: Ruleset, known_by_case: dict[str, str]) -> set[str]:
    refs = set()
    for name in rules.actors:
        if name.startswith("^"):
            continue
        resolved = rules.resolve(name)
        if resolved is None:
            continue
        for armament in resolved.children_named("Armament"):
            weapon = str(armament.get("Weapon") or "").strip()
            canonical = known_by_case.get(weapon.lower())
            if canonical is not None:
                refs.add(canonical)
    return refs


def weapon_reference_sets(rules: Ruleset, concrete: set[str]) -> tuple[set[str], set[str]]:
    """Return direct Armament references and the full modeled weapon closure."""
    known_by_case = canonical_weapon_names(concrete)
    direct_refs = direct_armament_references(rules, known_by_case)
    actor_refs = set()
    for name in rules.actors:
        if name.startswith("^"):
            continue
        resolved = rules.resolve(name)
        if resolved is not None:
            actor_refs.update(weapon_references(resolved, known_by_case))

    graph = {
        name: weapon_references(rules.resolve_weapon(name), known_by_case)
        for name in concrete
    }
    reachable = set(actor_refs)
    pending = list(actor_refs)
    while pending:
        name = pending.pop()
        for target in graph.get(name, ()):
            if target not in reachable:
                reachable.add(target)
                pending.append(target)
    return direct_refs, reachable


def inventory(rules: Ruleset) -> dict[str, object]:
    concrete = {
        name for name in rules.weapons
        if not name.startswith("^") and rules.resolve_weapon(name) is not None
    }
    violations = {
        name for name in concrete
        if len(main_warheads(rules.resolve_weapon(name))) > 1
    }
    # Upstream retired composite exemptions. Keep legacy partition field names
    # for report readers, but never exempt a stack or consult the deleted registry.
    reviewed_violations = set()
    direct_refs, reachable = weapon_reference_sets(rules, concrete)

    main_counts = {
        name: len(main_warhead_nodes(rules.resolve_weapon(name)))
        for name in concrete
    }

    direct = violations & direct_refs
    transitive = violations & reachable
    indirect = transitive - direct
    unreached = violations - transitive
    reviewed_direct = direct & reviewed_violations
    reviewed_indirect = indirect & reviewed_violations
    reviewed_unreached = unreached & reviewed_violations
    unreviewed_direct = direct - reviewed_direct
    unreviewed_indirect = indirect - reviewed_indirect
    unreviewed_unreached = unreached - reviewed_unreached
    assert violations == direct | indirect | unreached
    assert not (direct & indirect or direct & unreached or indirect & unreached)

    def excess(names):
        return sum(max(0, main_counts[name] - 1) for name in names)

    return {
        "exemption_policy": "retired; reviewed partitions are empty and all raw stacks remain counted",
        "predicate": (
            "positive Damage on AreaDamage, SpreadDamage, HealthPercentageDamage, or "
            "TargetDamage; excludes designed companions and friendly-fire twins"
        ),
        "reference_fields": sorted(WEAPON_REF_FIELDS),
        "reference_map_fields": sorted(WEAPON_REF_MAP_FIELDS),
        "counts": {
            "concrete_weapons": len(concrete),
            "stacked_main_all_concrete": len(violations),
            "stacked_main_direct_actor_armament": len(direct),
            "stacked_main_indirect_weapon_graph": len(indirect),
            "stacked_main_transitive_weapon_graph": len(transitive),
            "stacked_main_unreached": len(unreached),
            "reviewed_stacked_main_all_concrete": len(reviewed_violations),
            "reviewed_stacked_main_direct_actor_armament": len(reviewed_direct),
            "reviewed_stacked_main_indirect_weapon_graph": len(reviewed_indirect),
            "reviewed_stacked_main_transitive_weapon_graph": (
                len(reviewed_direct | reviewed_indirect)),
            "reviewed_stacked_main_unreached": len(reviewed_unreached),
            "unreviewed_stacked_main_all_concrete": (
                len(violations - reviewed_violations)),
            "unreviewed_stacked_main_direct_actor_armament": len(unreviewed_direct),
            "unreviewed_stacked_main_indirect_weapon_graph": len(unreviewed_indirect),
            "unreviewed_stacked_main_transitive_weapon_graph": (
                len(unreviewed_direct | unreviewed_indirect)),
            "unreviewed_stacked_main_unreached": len(unreviewed_unreached),
            "main_warhead_instances_all_concrete": sum(main_counts.values()),
            "excess_main_warhead_instances_all_concrete": excess(concrete),
            "main_warhead_instances_transitive_weapon_graph": sum(
                main_counts[name] for name in reachable),
            "excess_main_warhead_instances_transitive_weapon_graph": excess(reachable),
            "excess_main_warhead_instances_direct_actor_armament": excess(direct_refs),
            "excess_main_warhead_instances_indirect_weapon_graph": excess(
                reachable - direct_refs),
            "excess_main_warhead_instances_unreached": excess(concrete - reachable),
            "reviewed_excess_main_warhead_instances_all_concrete": excess(
                reviewed_violations),
            "reviewed_excess_main_warhead_instances_transitive_weapon_graph": excess(
                reviewed_direct | reviewed_indirect),
            "unreviewed_excess_main_warhead_instances_all_concrete": excess(
                violations - reviewed_violations),
            "unreviewed_excess_main_warhead_instances_transitive_weapon_graph": excess(
                unreviewed_direct | unreviewed_indirect),
        },
        "sets": {
            "direct_actor_armament": sorted(direct),
            "indirect_weapon_graph": sorted(indirect),
            "unreached": sorted(unreached),
            "reviewed_direct_actor_armament": sorted(reviewed_direct),
            "reviewed_indirect_weapon_graph": sorted(reviewed_indirect),
            "reviewed_unreached": sorted(reviewed_unreached),
            "unreviewed_direct_actor_armament": sorted(unreviewed_direct),
            "unreviewed_indirect_weapon_graph": sorted(unreviewed_indirect),
            "unreviewed_unreached": sorted(unreviewed_unreached),
        },
    }


def serialized(data: dict[str, object]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def ratchet_errors(data: dict[str, object]) -> list[str]:
    counts = data["counts"]
    errors = []
    actual = counts["stacked_main_transitive_weapon_graph"]
    if actual > RAW_REACHABLE_BASELINE:
        errors.append(
            f"raw reachable stacks increased: {actual}/{RAW_REACHABLE_BASELINE}")
    excess = counts["excess_main_warhead_instances_transitive_weapon_graph"]
    if excess > RAW_REACHABLE_EXCESS_BASELINE:
        errors.append(
            "raw reachable excess mains increased: "
            f"{excess}/{RAW_REACHABLE_EXCESS_BASELINE}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()

    data = inventory(Ruleset(ROOT))
    errors = ratchet_errors(data)
    if errors:
        print("FAIL weapon structure ratchets")
        for error in errors:
            print(f"- {error}")
        return 1
    text = serialized(data)
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text, encoding="utf-8")
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
