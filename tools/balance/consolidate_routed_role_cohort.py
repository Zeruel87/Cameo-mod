#!/usr/bin/env python3
"""Collapse the reviewed routed missile/flame/corrosion role cohort."""
from __future__ import annotations

import argparse
import collections
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]

from audit_three_way_split import main_warheads  # noqa: E402
from consolidate_final_safe_cohorts import (  # noqa: E402
    HEALTH_VALUES, ensure_template_inherit, flat_main_nodes, percentage_scale,
)
from consolidate_reviewed_weapon_roots import (  # noqa: E402
    add_compatibility_templates, apply_compatibility_block, block_bounds,
    emit_node, resolved_flat_total,
)
from consolidate_role_complete_profiles import update_compatibility_block  # noqa: E402
from miniyaml import Ruleset  # noqa: E402
import percentage_damage as pd  # noqa: E402


# destination, exact descendants, root total, root scale
ROOTS = {
    "RA2MultiThunderboltMissile": ("MissileHE_Light", {
        "RA2MultiThunderboltMissile_AA", "RA2MultiThunderboltMissile_elite",
        "RA2MultiThunderboltMissile_AA_elite"}, 4000, 9975),
    "RA2ThunderboltMissile": ("MissileHE_Light", {
        "RA2ThunderboltMissile_AA", "RA2ThunderboltMissile_elite",
        "RA2ThunderboltMissile_AA_elite"}, 4000, 9975),
    "FireballLauncherBuggy2": ("Flame_Medium", set(), 6000, 9984),
    "MatadorFlamer": ("Flame_Heavy", set(), 6000, 9984),
    "SyndicateFireballLauncher": ("Flame_Heavy", {
        "SyndicateFireballLauncherExplode", "SyndicateFireballLauncher_elite"},
        6000, 9984),
    "NaxCorrosionRocket": ("MissileAP_Medium", {
        "NaxCorrosionBeast", "NaxCorrosionBeast_elite",
        "NaxCorrosionRocketTrooper_elite"}, 6000, 9984),
    "MarauderMissiles": ("MissileAP_Medium", set(), 30000, 3330),
    "TSStankTibTusk": ("MissileAP_Medium", set(), 35000, 2855),
    "RA2RBurritoRocket": ("CannonHE_Heavy", set(), 20000, 3995),
    "VultureGrenade": ("Demolition_Light", set(), 20000, 1995),
}
PINS = {
    "SyndicateFireballLauncherExplode": (18000, 3328),
}
AUTHORIZED_SUCCESSORS = {"NaxCorrosionRocketTrooper_elite"}

OLD_MAINS = {
    "RA2MultiThunderboltMissile": {"MissileHE_Heavy", "MissileHE_Light"},
    "RA2ThunderboltMissile": {"MissileHE_Heavy", "MissileHE_Light"},
    "FireballLauncherBuggy2": {"Flame_Light", "Flame_Medium", "Flame_Heavy"},
    "MatadorFlamer": {"Flame_Light", "Flame_Medium", "Flame_Heavy"},
    "SyndicateFireballLauncher": {"Flame_Light", "Flame_Medium", "Flame_Heavy"},
    "SyndicateFireballLauncherExplode": {"Flame_Light", "Flame_Medium", "Flame_Heavy", "LightFlameWeapon", "MediumFlameWeapon", "HeavyFlameWeapon"},
    "NaxCorrosionRocket": {"Concussion_Light", "MissileAP_Heavy", "MissileAP_Medium"},
    "MarauderMissiles": {"MissileAP_MediumFlatCompatibility", "CannonHE_Heavy"},
    "TSStankTibTusk": {"MissileAP_MediumFlatCompatibility", "CannonHE_Medium"},
    "RA2RBurritoRocket": {"CannonHE_HeavyFlatCompatibility", "Demolition_Light", "MissileAP_Heavy"},
    "VultureGrenade": {"Demolition_LightFlatCompatibility", "CannonHE_Medium"},
}

PINNED_AFTER_MAINS = {
    "SyndicateFireballLauncherExplode": {
        "PreservedFlat_Flame_Heavy", "PreservedFlat_Flame_Light",
        "PreservedFlat_Flame_Medium", "PreservedFlat_HeavyFlameWeapon",
        "PreservedFlat_LightFlameWeapon", "PreservedFlat_MediumFlameWeapon",
    },
}


def descendants(rs, root):
    direct = collections.defaultdict(set)
    for name, node in rs.weapons.items():
        for _, parent in rs.inherits_of(node):
            if parent in rs.weapons:
                direct[parent].add(name)
    seen, stack = set(), list(direct[root])
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name); stack.extend(direct[name])
    return {name for name in seen if not name.startswith("^")}


def selections(rs):
    result = {}
    for root, (dest, expected, total, scale) in ROOTS.items():
        actual = descendants(rs, root)
        if actual != expected:
            raise RuntimeError(f"{root}: closure changed; added={sorted(actual-expected)}, missing={sorted(expected-actual)}")
        for name in {root, *expected} - AUTHORIZED_SUCCESSORS:
            if name in PINS:
                result[name] = (None, *PINS[name])
            else:
                result[name] = (dest, total, scale)
    if len(result) != 20:
        raise RuntimeError(f"expected 20 closure members, found {len(result)}")
    return result


def expected_old(name, root):
    if name in OLD_MAINS:
        return OLD_MAINS[name]
    return OLD_MAINS[root]


def root_of(name):
    for root, (_dest, children, _total, _scale) in ROOTS.items():
        if name == root or name in children:
            return root
    raise KeyError(name)


def inspect(rs):
    states = set()
    for name, (dest, total, scale) in selections(rs).items():
        resolved = rs.resolve_weapon(name)
        mains = set(main_warheads(resolved))
        old = expected_old(name, root_of(name))
        if name in PINS:
            after = mains == PINNED_AFTER_MAINS[name]
            before = mains == old
            if not (before or after) or resolved_flat_total(resolved, mains) != total:
                raise RuntimeError(f"{name}: preservation fingerprint changed: {sorted(mains)}")
            states.add(after)
            continue
        compatibility = f"{dest}FlatCompatibility"
        before, after = mains == old, mains == {compatibility}
        if not (before or after):
            raise RuntimeError(f"{name}: unexpected mains {sorted(mains)}")
        states.add(after)
        nodes = flat_main_nodes(resolved, mains)
        if set(nodes) != mains or resolved_flat_total(resolved, mains) != total:
            raise RuntimeError(f"{name}: flat total changed")
        if before:
            actual_scale = percentage_scale(resolved, mains, total)
            if actual_scale != scale:
                raise RuntimeError(f"{name}: scale changed: {actual_scale}")
            old_hp = [sum(int(a["runtime_hp"]) for a in pd.percentage_applications(resolved, hp)
                          if a["tag"] in mains) for hp in HEALTH_VALUES]
            units = pd.folded_units(total, scale)[1]
            new_hp = [pd.runtime_percentage_hp(hp, units, pd.FOLDED_DEFAULT_DENOMINATOR)
                      for hp in HEALTH_VALUES]
            if any(value < 0 for value in old_hp + new_hp):
                raise RuntimeError(f"{name}: percentage overflow")
            if max(abs(a-b) for a, b in zip(old_hp, new_hp)) > 1:
                raise RuntimeError(f"{name}: percentage drift exceeds one HP")
        else:
            node = nodes[compatibility]
            if int(str(node.get("PercentageScale") or 0)) != scale:
                raise RuntimeError(f"{name}: applied scale changed")
    if len(states) != 1:
        raise RuntimeError("partial routed-role consolidation detected")
    return states == {True}


def local_has(lines, weapon, marker):
    start, end = block_bounds(lines, weapon)
    return any(lines[i].rstrip("\r\n") == marker for i in range(start + 1, end))


def add_removal(lines, weapon, key):
    marker = f"\t-Warhead@{key}:"
    if local_has(lines, weapon, marker):
        return
    _start, end = block_bounds(lines, weapon)
    while not lines[end-1].strip(): end -= 1
    lines.insert(end, marker + "\n")


def convert(rs, changed, name, dest, total, scale, removals, inherit=True):
    path = pathlib.Path(rs.weapon(name).file)
    lines = changed.setdefault(path, path.read_text(encoding="utf-8-sig").splitlines(True))
    key = f"{dest}FlatCompatibility"
    if not local_has(lines, name, f"\tWarhead@{key}:"):
        apply_compatibility_block(changed, path, name, dest, removals, total,
                                  str(rs.resolve_weapon(name).get("ValidTargets") or ""),
                                  inherit_template=inherit)
    else:
        if inherit: ensure_template_inherit(changed, path, name, dest)
        for removal in removals: add_removal(lines, name, removal)
    update_compatibility_block(lines, name, dest, total, scale, None)


def preserve_member(rs, changed, name, local_removals, inherited_compat):
    path = pathlib.Path(rs.weapon(name).file)
    lines = changed.setdefault(path, path.read_text(encoding="utf-8-sig").splitlines(True))
    resolved = rs.resolve_weapon(name)
    nodes = flat_main_nodes(resolved, OLD_MAINS[name])
    for key in local_removals:
        add_removal(lines, name, key)
    add_removal(lines, name, inherited_compat)
    _start, end = block_bounds(lines, name)
    while not lines[end-1].strip(): end -= 1
    payload = []
    for key in sorted(nodes):
        payload.extend(emit_node(nodes[key], 1, f"Warhead@PreservedFlat_{key}"))
    lines[end:end] = payload


def apply_changes(rs):
    changed = {}
    add_compatibility_templates(changed, rs, {v[0] for v in ROOTS.values()})
    for root, (dest, _children, total, scale) in ROOTS.items():
        compat = f"{dest}FlatCompatibility"
        convert(rs, changed, root, dest, total, scale, OLD_MAINS[root] - {compat})
    preserve_member(rs, changed, "SyndicateFireballLauncherExplode",
                    {"LightFlameWeapon", "MediumFlameWeapon", "HeavyFlameWeapon"},
                    "Flame_HeavyFlatCompatibility")
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")


def validate_result():
    if not inspect(Ruleset(ROOT)):
        raise RuntimeError("routed-role cohort remains unconsolidated")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(); rs = Ruleset(ROOT); already = inspect(rs)
    if already:
        print("Already consolidated 21 closure members (19 reductions)"); return 0
    print("10 roots; 21 closure members; 19 reductions")
    if not args.apply:
        print("Dry run: closures, totals, percentages, overflow and preservation pass"); return 0
    apply_changes(rs); validate_result(); print("Applied and validated routed-role cohort"); return 0


if __name__ == "__main__": raise SystemExit(main())
