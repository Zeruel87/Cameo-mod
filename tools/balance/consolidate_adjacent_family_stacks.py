#!/usr/bin/env python3
"""Consolidate reviewed adjacent-tier stacks onto their existing delivery tier."""
from __future__ import annotations

import argparse
import collections
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from miniyaml import Ruleset  # noqa: E402
from consolidate_reviewed_weapon_roots import (  # noqa: E402
    add_compatibility_templates,
    apply_compatibility_block,
    block_bounds,
    resolved_flat_total,
)
import percentage_damage as pd  # noqa: E402
from review_batch_diff import active_health_values  # noqa: E402

HEALTH_VALUES = active_health_values(ROOT)


# root: (retired main keys, selected delivery/effect tier, exact descendants)
SPECS = {
    # Higher-damage missile/cannon/sonic candidates are intentionally excluded:
    # merging their folded percentage hits overflows at active high-health values.
    "CycloneRockets": ({"MissileHE_Light", "MissileHE_Medium"}, "MissileHE_Light", {"CycloneRocketsLockOn"}),
    "RA2Chemspray2": ({"Chemical_Medium", "Chemical_Heavy"}, "Chemical_Heavy", {"RA2Chemspray_elite"}),
}


def all_descendants(rs: Ruleset) -> dict[str, set[str]]:
    direct: dict[str, set[str]] = collections.defaultdict(set)
    for name, local in rs.weapons.items():
        for _, parent in rs.inherits_of(local):
            if parent in rs.weapons:
                direct[parent].add(name)
    result = {}
    for root in SPECS:
        seen: set[str] = set()
        stack = list(direct[root])
        while stack:
            name = stack.pop()
            if name in seen:
                continue
            seen.add(name)
            stack.extend(direct[name])
        result[root] = {name for name in seen if not name.startswith("^")}
    return result


def positive_main_keys(node) -> set[str]:
    keys = set()
    for child in node.children:
        if not child.key.startswith("Warhead@") or child.value not in {"AreaDamage", "SpreadDamage"}:
            continue
        if "Percentage" in child.key or "FriendlyFire" in child.key:
            continue
        try:
            amount = int(str(child.get("Damage") or "0"))
        except ValueError:
            continue
        if amount > 0:
            keys.add(child.key.split("@", 1)[1])
    return keys


def local_old_keys(node, old_keys: set[str]) -> set[str]:
    return {
        child.key.split("@", 1)[1]
        for child in node.children
        if child.key.startswith("Warhead@") and child.key.split("@", 1)[1] in old_keys
    }


def reintroduced_old_keys(rs: Ruleset, node, old_keys: set[str], family: set[str]) -> set[str]:
    keys = local_old_keys(node, old_keys)
    for _, parent in rs.inherits_of(node):
        if parent in family:
            continue
        inherited = rs.resolve_weapon(parent)
        if inherited is not None:
            keys.update(positive_main_keys(inherited) & old_keys)
    return keys


def flat_targets(node, old_keys: set[str]) -> str:
    ordered = []
    for child in node.children:
        if not child.key.startswith("Warhead@") or child.key.split("@", 1)[1] not in old_keys:
            continue
        for token in str(child.get("ValidTargets") or "").split(","):
            token = token.strip()
            if token and token not in ordered:
                ordered.append(token)
    if not ordered:
        raise RuntimeError(f"{node.key}: missing old-family ValidTargets")
    return ", ".join(ordered)


def combined_percentage_scale(node, old_keys: set[str], total: int) -> int:
    units = sum(int(app["runtime_units"])
                for app in pd.percentage_applications(node, 200_000)
                if app["tag"] in old_keys)
    if units <= 0:
        return 0
    estimate = max(1, units * pd.FOLDED_SCALE_DENOMINATOR // total)
    for scale in range(max(1, estimate - 200), estimate + 201):
        if pd.folded_units(total, scale)[1] != units:
            continue
        for hp in HEALTH_VALUES:
            before = sum(
                int(app["runtime_hp"])
                for app in pd.percentage_applications(node, hp)
                if app["tag"] in old_keys
            )
            after = pd.runtime_percentage_hp(hp, units, pd.FOLDED_DEFAULT_DENOMINATOR)
            if abs(before - after) > 1:
                raise RuntimeError(
                    f"{node.key}: folded percentage merge changes {hp} HP target "
                    f"from {before} to {after}")
        return scale
    raise RuntimeError(f"{node.key}: cannot preserve {units} folded percentage units")


def set_percentage_scale(changed: dict[pathlib.Path, list[str]], path: pathlib.Path,
                         weapon: str, destination: str, scale: int) -> None:
    lines = changed[path]
    start, end = block_bounds(lines, weapon)
    marker = f"\tWarhead@{destination}FlatCompatibility:"
    indexes = [i for i in range(start + 1, end) if lines[i].rstrip("\r\n") == marker]
    if len(indexes) != 1:
        raise RuntimeError(f"{weapon}: expected one compatibility block")
    for i in range(indexes[0] + 1, end):
        if lines[i].startswith("\t") and not lines[i].startswith("\t\t") and lines[i].strip():
            break
        if lines[i].lstrip().startswith("PercentageScale:"):
            lines[i] = f"\t\tPercentageScale: {scale}\n"
            return
    raise RuntimeError(f"{weapon}: missing compatibility PercentageScale")


def validate(rs: Ruleset) -> dict[str, set[str]]:
    closures = all_descendants(rs)
    for root, (old_keys, destination, expected) in SPECS.items():
        if closures[root] != expected:
            raise RuntimeError(
                f"{root}: closure changed; added={sorted(closures[root] - expected)}, "
                f"missing={sorted(expected - closures[root])}")
        resolved = rs.resolve_weapon(root)
        if resolved is None:
            raise RuntimeError(f"{root}: missing")
        mains = positive_main_keys(resolved)
        compatibility = f"{destination}FlatCompatibility"
        already = compatibility in mains and not (old_keys & mains)
        if not already and not old_keys <= mains:
            raise RuntimeError(f"{root}: expected {sorted(old_keys)}, found {sorted(mains)}")
    return closures


def validate_result() -> None:
    rs = Ruleset(ROOT)
    closures = validate(rs)
    for root, (old_keys, destination, _) in SPECS.items():
        expected = f"{destination}FlatCompatibility"
        for name in [root, *sorted(closures[root])]:
            node = rs.resolve_weapon(name)
            mains = positive_main_keys(node)
            if expected not in mains or old_keys & mains:
                raise RuntimeError(f"{name}: unresolved consolidation: {sorted(mains)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    rs = Ruleset(ROOT)
    closures = validate(rs)
    changed: dict[pathlib.Path, list[str]] = {}
    add_compatibility_templates(
        changed, rs, {spec[1] for spec in SPECS.values()},
        header=[
            "# Compatibility profiles for reviewed same-family consolidation.\n",
            "# Concrete weapons combine folded percentage units; the converter bounds\n",
            "# active-health rounding drift and rejects runtime overflow.\n",
        ])
    total_definitions = 0

    for root, (old_keys, destination, _) in SPECS.items():
        local = rs.weapon(root)
        resolved = rs.resolve_weapon(root)
        compatibility = f"{destination}FlatCompatibility"
        mains = positive_main_keys(resolved)
        already = compatibility in mains and not (old_keys & mains)
        if not already:
            total = resolved_flat_total(resolved, old_keys)
            path = pathlib.Path(local.file)
            apply_compatibility_block(changed, path, root, destination, old_keys,
                                      total, flat_targets(resolved, old_keys))
            set_percentage_scale(changed, path, root, destination,
                                 combined_percentage_scale(resolved, old_keys, total))

        family = {root, *closures[root]}
        repaired = 0
        for name in sorted(closures[root]):
            child_local = rs.weapon(name)
            child = rs.resolve_weapon(name)
            child_mains = positive_main_keys(child)
            if compatibility in child_mains and not (old_keys & child_mains):
                continue
            removals = reintroduced_old_keys(rs, child_local, old_keys, family)
            if not removals:
                continue
            total = resolved_flat_total(child, old_keys)
            path = pathlib.Path(child_local.file)
            apply_compatibility_block(changed, path, name, destination, removals,
                                      total, flat_targets(child, old_keys),
                                      inherit_template=False)
            set_percentage_scale(changed, path, name, destination,
                                 combined_percentage_scale(child, old_keys, total))
            repaired += 1
        count = 1 + len(closures[root])
        total_definitions += count
        print(f"{root} -> {destination}: {count} definitions; {repaired} local overrides")

    print(f"{total_definitions} reviewed concrete definitions")
    if not args.apply:
        print(f"Dry run: {len(changed)} files would change")
        return 0
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8")
    validate_result()
    print(f"Applied and validated {len(changed)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
