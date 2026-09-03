#!/usr/bin/env python3
"""Group the live reachable stacked-weapon backlog by inheritance root.

This is a planning inventory, not conversion authority.  It always resolves
the current active rules rather than consuming the tracked survey snapshot.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from audit_three_way_split import main_warhead_nodes, main_warheads
from miniyaml import Ruleset
from survey_weapon_structure import inventory


def descendants(rules, names):
    children = {}
    parents = {}
    for name, node in rules.weapons.items():
        for _key, parent in rules.inherits_of(node):
            if parent not in rules.weapons:
                continue
            children.setdefault(parent, set()).add(name)
            parents.setdefault(name, set()).add(parent)
    return children, parents


def walk_closure(root, children, selected):
    seen = set()
    pending = list(children.get(root, set()))
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        pending.extend(children.get(name, set()))
    return seen & selected


def route(node):
    def normalized(field, default=""):
        child = node.child(field)
        raw = default if child is None else (child.value or "")
        return tuple(sorted(
            token.strip() for token in str(raw).split(",") if token.strip()))

    return (
        normalized("ValidTargets", "Ground, Water"),
        normalized("InvalidTargets"),
        normalized("ValidRelationships", "Ally, Neutral, Enemy"),
        normalized("InvalidRelationships"),
    )


def flags(nodes):
    tags = [node.key.split("@", 1)[-1] for node in nodes]
    routes = {route(node) for node in nodes}
    state = any(
        node.get("PhysicalStateName")
        or node.child("PhysicalStates") is not None
        or node.get("IntegrityScale")
        for node in nodes
    )
    return {
        "air_only": all(
            {token.strip() for token in (node.get("ValidTargets") or "").split(",")
             if token.strip()} == {"Air"}
            for node in nodes
        ),
        "legacy_bridge": any(
            "PreservedFlat" in tag or "Compatibility" in tag for tag in tags),
        "numbered": any(re.match(r"^\d", tag) for tag in tags),
        "route_mixed": len(routes) > 1,
        "state_or_integrity": state,
    }


def build():
    rules = Ruleset(ROOT)
    survey = inventory(rules)
    selected = set(survey["sets"]["direct_actor_armament"])
    selected.update(survey["sets"]["indirect_weapon_graph"])
    reviewed = set(survey["sets"]["reviewed_direct_actor_armament"])
    reviewed.update(survey["sets"]["reviewed_indirect_weapon_graph"])
    children, parents = descendants(rules, selected)

    roots = sorted(
        name for name in selected
        if not any(parent in selected for parent in parents.get(name, set()))
    )
    candidate_members = {
        root: {root, *walk_closure(root, children, selected)}
        for root in roots
    }
    candidate_roots = {name: [] for name in selected}
    for root, members in candidate_members.items():
        for name in members:
            candidate_roots[name].append(root)
    missing = {name for name, owners in candidate_roots.items() if not owners}
    if missing:
        raise RuntimeError(f"root partition incomplete: missing={sorted(missing)}")

    # Selected weapons can share a descendant through multiple inheritance.
    # Assign each one to a single deterministic planning root; retain aliases
    # as metadata instead of silently duplicating the weapon across groups.
    owner = {
        name: (name if name in roots else min(candidate_roots[name]))
        for name in selected
    }
    groups = []
    for root in roots:
        members = {name for name, assigned in owner.items() if assigned == root}
        member_rows = []
        aggregate_flags = {
            "air_only": True,
            "legacy_bridge": False,
            "numbered": False,
            "route_mixed": False,
            "state_or_integrity": False,
        }
        for name in sorted(members):
            nodes = main_warhead_nodes(rules.resolve_weapon(name))
            member_flags = flags(nodes)
            aggregate_flags["air_only"] &= member_flags["air_only"]
            for key in aggregate_flags.keys() - {"air_only"}:
                aggregate_flags[key] |= member_flags[key]
            member_rows.append({
                "name": name,
                "mains": main_warheads(rules.resolve_weapon(name)),
                "flags": member_flags,
                "reviewed": name in reviewed,
                "alternate_roots": sorted(
                    candidate for candidate in candidate_roots[name]
                    if candidate != root),
            })
        groups.append({
            "root": root,
            "size": len(members),
            "flags": aggregate_flags,
            "members": member_rows,
        })

    flattened = [
        member["name"] for group in groups for member in group["members"]
    ]
    if len(flattened) != len(selected) or set(flattened) != selected:
        raise RuntimeError(
            f"root partition invalid: missing={sorted(selected - set(flattened))}, "
            f"duplicate_count={len(flattened) - len(set(flattened))}, "
            f"extra={sorted(set(flattened) - selected)}")
    groups.sort(key=lambda row: (-row["size"], row["root"]))
    return {
        "reachable_stacked": len(selected),
        "reviewed_reachable": len(reviewed),
        "unreviewed_reachable": len(selected - reviewed),
        "root_count": len(groups),
        "groups": groups,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    data = build()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    print(f"reachable stacked: {data['reachable_stacked']}")
    print(f"reviewed / unreviewed: {data['reviewed_reachable']} / "
          f"{data['unreviewed_reachable']}")
    print(f"inheritance roots: {data['root_count']}")
    for group in data["groups"][:args.limit]:
        flags_text = ", ".join(key for key, value in group["flags"].items() if value) or "ordinary"
        print(f"\n{group['size']:>2}  {group['root']}  [{flags_text}]")
        for member in group["members"]:
            marker = "reviewed" if member["reviewed"] else "unreviewed"
            print(f"    {member['name']} [{marker}]: {' + '.join(member['mains'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
