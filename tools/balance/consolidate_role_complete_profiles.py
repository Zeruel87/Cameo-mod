#!/usr/bin/env python3
"""Finish reviewed role profiles that still resolve multiple damage mains.

This cohort deliberately makes the selected delivery profile authoritative.
It preserves cadence, targeting, nominal flat damage, effects, and all unrelated
warheads.  The Manta's separately routed ground and air weapons use different
profiles; the other roots finish compatibility folds started by earlier passes.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from audit_three_way_split import main_warheads  # noqa: E402
from consolidate_final_safe_cohorts import (  # noqa: E402
    cleanup_stale_removals,
    ensure_template_inherit,
    flat_main_nodes,
    set_scale,
    tokens,
)
from consolidate_reviewed_weapon_roots import (  # noqa: E402
    apply_compatibility_block,
    block_bounds,
    resolved_flat_total,
)
from miniyaml import Ruleset  # noqa: E402


# destination, baseline mains, expected descendants, flat total, folded scale,
# optional authored DamageTypes override.  Explicit closures fail closed when a
# new variant appears.
ROOTS = {
    "RA2MirageGun": (
        "CannonAP_Light",
        {"CannonAP_Light", "CannonAP_LightFlatCompatibility"},
        {"RA2MirageGun_elite"}, 25000, 3196,
        "Prone75Percent, TriggerProne, FireDeath"),
    "RA2HeavyMirageGun": (
        "CannonAP_Light",
        {"CannonAP_Light", "CannonAP_LightFlatCompatibility"},
        {"RA2HeavyMirageGun_elite"}, 33000, 2422,
        "Prone75Percent, TriggerProne, FireDeath"),
    "RA2PsychicJab": (
        "CannonHE_Medium",
        {"CannonHE_Medium", "CannonHE_MediumFlatCompatibility"},
        {"RA2PsychicJab_elite"}, 8000, 2488,
        "Prone75Percent, TriggerProne, FireDeath, Incendiary"),
    "ixian_airdrone": (
        "MissileAP_Heavy",
        {"MissileAP_Heavy", "MissileAP_HeavyFlatCompatibility"},
        {"ordos_airmine"}, 12000, 1659,
        "Prone75Percent, TriggerProne, FireDeath, Incendiary"),
    "NaxMausCannon": (
        "CannonHE_Heavy",
        {"CannonHE_Medium", "CannonHE_HeavyFlatCompatibility"},
        {"NaxMausCannon_elite"}, 60000, 1665, None),
    "NaxRatteCannon": (
        "CannonHE_Heavy",
        {"CannonHE_Medium", "CannonHE_HeavyFlatCompatibility"},
        {"NaxRatteCannon_elite"}, 150000, 3333, None),
}

MANTA_ROOT = "SteelMantaAG"
MANTA_AA_ROOT = "SteelManta_AA"
MANTA_MAINS = {"MissileAP_Light", "Bullet_Light", "Flak_Medium", "Bullet_Medium"}
MANTA_AG = {
    "SteelMantaAG", "SteelMantaAGResonance",
    "SteelMantaAGResonanceBounce1", "SteelMantaAGResonanceBounce2",
}
MANTA_AA = {
    "SteelManta_AA", "SteelMantaAAResonance_AA",
    "SteelMantaAAResonanceBounce1", "SteelMantaAAResonanceBounce2",
}
MANTA_TOTAL = 8000
MANTA_SCALE = 9988


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
    for root, (destination, _mains, expected, _total, _scale, _types) in ROOTS.items():
        actual = descendants(rs, root)
        if actual != expected:
            raise RuntimeError(
                f"{root}: closure changed; added={sorted(actual - expected)}, "
                f"missing={sorted(expected - actual)}")
        for name in {root, *expected}:
            selected[name] = destination
    manta_closure = descendants(rs, MANTA_ROOT)
    expected_manta = (MANTA_AG | MANTA_AA) - {MANTA_ROOT}
    if manta_closure != expected_manta:
        raise RuntimeError(
            f"{MANTA_ROOT}: closure changed; added={sorted(manta_closure - expected_manta)}, "
            f"missing={sorted(expected_manta - manta_closure)}")
    for name in MANTA_AG:
        selected[name] = "Bullet_Medium"
    for name in MANTA_AA:
        selected[name] = "Flak_Medium"
    if len(selected) != 20:
        raise RuntimeError(f"expected 20 selected definitions, found {len(selected)}")
    return selected


def expected_plan(name: str, destination: str):
    if name in MANTA_AG | MANTA_AA:
        return MANTA_MAINS, MANTA_TOTAL, MANTA_SCALE, None
    for root, (dest, mains, children, total, scale, damage_types) in ROOTS.items():
        if name == root or name in children:
            if dest != destination:
                raise RuntimeError(f"{name}: destination mismatch")
            return mains, total, scale, damage_types
    raise RuntimeError(f"{name}: no plan")


def inspect(rs: Ruleset, selected: dict[str, str]):
    plans = {}
    for name, destination in selected.items():
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            raise RuntimeError(f"{name}: missing resolved weapon")
        baseline_mains, expected_total, expected_scale, damage_types = expected_plan(
            name, destination)
        mains = set(main_warheads(resolved))
        compatibility = f"{destination}FlatCompatibility"
        expected_after = {compatibility} | ({"1Dam"} if name == "ordos_airmine" else set())
        if mains == expected_after:
            node = flat_main_nodes(resolved, {compatibility}).get(compatibility)
            if node is None:
                raise RuntimeError(f"{name}: missing final compatibility main")
            if int(str(node.get("Damage") or "0")) != expected_total:
                raise RuntimeError(f"{name}: applied flat total drifted")
            if int(str(node.get("PercentageScale") or "0")) != expected_scale:
                raise RuntimeError(f"{name}: applied percentage scale drifted")
            if damage_types and str(node.get("DamageTypes") or "") != damage_types:
                raise RuntimeError(f"{name}: applied DamageTypes drifted")
            plans[name] = None
            continue
        expected_before = set(baseline_mains) | ({"1Dam"} if name == "ordos_airmine" else set())
        if mains != expected_before:
            raise RuntimeError(
                f"{name}: expected {sorted(expected_before)}; found {sorted(mains)}")
        nodes = flat_main_nodes(resolved, set(baseline_mains))
        if set(nodes) != set(baseline_mains):
            raise RuntimeError(f"{name}: selected mains are not all flat damage")
        fields = (
            "ValidTargets", "InvalidTargets", "ValidRelationships",
            "InvalidRelationships", "AffectsParent", "TargetActorCenter",
        )
        if len({tuple(tokens(node.get(field)) for field in fields)
                for node in nodes.values()}) != 1:
            raise RuntimeError(f"{name}: selected target contracts differ")
        for tag, node in nodes.items():
            if any("PhysicalState" in child.key or child.key == "IntegrityScale"
                   for child in node.children):
                raise RuntimeError(f"{name}: {tag} carries a state hook")
        source_scales = {
            tag: int(str(node.get("PercentageScale") or "0"))
            for tag, node in nodes.items()
        }
        expected_source_scales = {
            tag: (0 if tag.endswith("FlatCompatibility") else 10000)
            for tag in baseline_mains
        }
        if source_scales != expected_source_scales:
            raise RuntimeError(
                f"{name}: source PercentageScale fingerprint changed; "
                f"expected {expected_source_scales}, found {source_scales}")
        total = resolved_flat_total(resolved, set(baseline_mains))
        if total != expected_total:
            raise RuntimeError(
                f"{name}: source total changed; expected {expected_total}, found {total}")
        target_key = (destination if destination in nodes
                      else f"{destination}FlatCompatibility")
        plans[name] = {
            "keys": set(baseline_mains),
            "targets": str(nodes[target_key].get("ValidTargets") or ""),
            "total": total,
            "scale": expected_scale,
            "damage_types": damage_types,
        }
    states = {plan is None for plan in plans.values()}
    if len(states) > 1:
        raise RuntimeError("partial role-complete profile consolidation detected")
    return plans, states == {True}


def add_removal(lines: list[str], weapon: str, key: str) -> None:
    start, end = block_bounds(lines, weapon)
    marker = f"\t-Warhead@{key}:"
    if any(lines[index].rstrip("\r\n") == marker for index in range(start + 1, end)):
        return
    insertion = end
    while insertion > start + 1 and not lines[insertion - 1].strip():
        insertion -= 1
    lines.insert(insertion, marker + "\n")


def update_compatibility_block(lines: list[str], weapon: str, destination: str,
                               total: int, scale: int,
                               damage_types: str | None) -> None:
    start, end = block_bounds(lines, weapon)
    marker = f"\tWarhead@{destination}FlatCompatibility:"
    rows = [index for index in range(start + 1, end)
            if lines[index].rstrip("\r\n") == marker]
    if len(rows) != 1:
        raise RuntimeError(f"{weapon}: expected one existing compatibility block")
    block_start = rows[0]
    block_end = end
    for index in range(block_start + 1, end):
        if lines[index].startswith("\t") and not lines[index].startswith("\t\t") \
                and lines[index].strip():
            block_end = index
            break
    replacements = {"Damage": str(total), "PercentageScale": str(scale)}
    if damage_types:
        replacements["DamageTypes"] = damage_types
    seen = set()
    for index in range(block_start + 1, block_end):
        match = re.match(r"^\t\t([^:]+):", lines[index])
        if match and match.group(1) in replacements:
            key = match.group(1)
            lines[index] = f"\t\t{key}: {replacements[key]}\n"
            seen.add(key)
    insertion = block_end
    while insertion > block_start + 1 and not lines[insertion - 1].strip():
        insertion -= 1
    for key in ("Damage", "PercentageScale", "DamageTypes"):
        if key in replacements and key not in seen:
            lines.insert(insertion, f"\t\t{key}: {replacements[key]}\n")
            insertion += 1


def apply_existing_roots(rs: Ruleset, plans, changed) -> None:
    for root, (destination, mains, _children, total, scale, damage_types) in ROOTS.items():
        node = rs.weapon(root)
        if node is None:
            raise RuntimeError(f"{root}: missing source")
        path = pathlib.Path(node.file)
        lines = changed.setdefault(path, path.read_text(encoding="utf-8-sig").splitlines(True))
        update_compatibility_block(lines, root, destination, total, scale, damage_types)
        canonical = next(key for key in mains if not key.endswith("FlatCompatibility"))
        add_removal(lines, root, canonical)


def apply_manta(rs: Ruleset, plans, changed) -> None:
    root_node = rs.weapon(MANTA_ROOT)
    if root_node is None:
        raise RuntimeError(f"{MANTA_ROOT}: missing source")
    path = pathlib.Path(root_node.file)
    ensure_template_inherit(changed, path, MANTA_ROOT, "Bullet_Medium")
    plan = plans[MANTA_ROOT]
    apply_compatibility_block(
        changed, path, MANTA_ROOT, "Bullet_Medium", MANTA_MAINS,
        plan["total"], plan["targets"], inherit_template=False)
    set_scale(changed, path, MANTA_ROOT, "Bullet_Medium", MANTA_SCALE)

    # The AA branch replaces the ground profile at its route root; all AA
    # resonance descendants inherit this override.
    ensure_template_inherit(changed, path, MANTA_AA_ROOT, "Flak_Medium")
    apply_compatibility_block(
        changed, path, MANTA_AA_ROOT, "Flak_Medium", set(), MANTA_TOTAL,
        plans[MANTA_AA_ROOT]["targets"],
        extra_removals={"Bullet_MediumFlatCompatibility"},
        inherit_template=False)
    set_scale(changed, path, MANTA_AA_ROOT, "Flak_Medium", MANTA_SCALE)


def validate_result() -> None:
    rs = Ruleset(ROOT)
    _plans, already = inspect(rs, selections(rs))
    if not already:
        raise RuntimeError("role-complete cohort remains unconsolidated")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rs = Ruleset(ROOT)
    selected = selections(rs)
    plans, already = inspect(rs, selected)
    if already:
        if args.apply:
            removed = cleanup_stale_removals(set(selected))
            validate_result()
            print(f"Removed {removed} stale descendant removals")
        print(f"Already consolidated {len(selected)} concrete definitions")
        return 0
    print(f"7 roots; {len(selected)} concrete definitions")
    if not args.apply:
        print("Dry run: closure, role, contract, state, and source-total guards pass")
        return 0

    changed: dict[pathlib.Path, list[str]] = {}
    apply_existing_roots(rs, plans, changed)
    apply_manta(rs, plans, changed)
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")
    cleanup_stale_removals(set(selected))
    validate_result()
    print(f"Applied and validated {len(changed)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
