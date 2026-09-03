#!/usr/bin/env python3
"""Consolidate explicitly reviewed same-family multi-main weapon stacks.

The selected roots already use the Medium bullet projectile/effect identity.  This
pass replaces their Light + Medium damage nodes with one Medium compatibility
node.  Folded percentage units are combined too: the reviewed contract permits at
most one HP of rounding drift across active health values and rejects larger drift
or overflow.

The root closure is an explicit fingerprint: discovering a new descendant fails
closed instead of silently rewriting it.
"""
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
    apply_compatibility_block,
    block_bounds,
    resolved_flat_total,
)
import percentage_damage as pd  # noqa: E402
from review_batch_diff import active_health_values  # noqa: E402

HEALTH_VALUES = active_health_values(ROOT)

OLD_KEYS = {"Bullet_Light", "Bullet_Medium"}
DESTINATION = "Bullet_Medium"
COMPATIBILITY_KEY = f"{DESTINATION}FlatCompatibility"

ROOT_CLOSURES = {
    "ACV_Machinegun": set(),
    "AsianKamikazeChaingun": set(),
    "BlackHawkCannon": set(),
    # CabalCyborgChaingun and TSDevoutChainguns are excluded: merging their
    # folded percentage hits overflows at active high-health values.
    "NaxiWW2KübelwagenMachinegun": set(),
    "OfficerMachineGun": set(),
    # RA220mmrapid is deliberately excluded: its Light slice can hit Air while
    # its Medium slice cannot, so choosing one target contract needs role review.
    "RA2GattlingInf": set(),
    "RA2vulcan": set(),
    "RAVulcan": set(),
    "SheridanVulcan": set(),
    "SteelCargoshipCannons": set(),
    "TSMutVulcanTurret": set(),
    "TSVulcanGun": set(),
    "tkmbunkmg": set(),
    "tkmquadcannonmg": set(),
    "RA2GattlingMG1": {
        "RA2GattlingMG1_AA", "RA2GattlingMG2", "RA2GattlingMG2_AA",
        "RA2GattlingMG3", "RA2GattlingMG3_AA", "YuriGatlingCannonMG1",
        "YuriGatlingCannonMG1_AA", "YuriGatlingCannonMG2",
        "YuriGatlingCannonMG2_AA", "YuriGatlingCannonMG3",
        "YuriGatlingCannonMG3_AA",
    },
    "NaxiWW2Machinegun": {
        "NaxiWW2MachinegunSmall", "NaxiWW2MachinegunSmall_AA",
        "NaxiWW2MachinegunTop", "NaxiWW2MachinegunTop_AA",
        "NaxiWW2Machinegun_AA", "NaxiWW2Machinegunner",
        "NaxiWW2Machinegunner_elite",
    },
    "RA2APCMachineGun": {
        "RA2APCMachineGun_AA", "RA2APCMachineGun_AA_elite",
        "RA2APCMachineGun_elite",
    },
    "GuardianGIMG": {"GuardianGIMG_elite", "RA2vulcan2", "RA2vulcan3"},
    "AsianLynxMG": {"AsianLynxMG_elite"},
    "BTRMachineGun": {"BTRMachineGun_AA"},
    "Future_Wheel_MG": {"Future_Wheel_MG_elite"},
    "LatinBuggyMG": {"LatinBuggyMG_elite"},
    "RA2NarcoAKM": {"RA2NarcoAKM_elite"},
    "naxis_sssoldier_smg": {"naxis_sssoldier_smg_elite"},
}


def descendants(rs: Ruleset) -> dict[str, set[str]]:
    direct: dict[str, set[str]] = collections.defaultdict(set)
    for name, local in rs.weapons.items():
        for _, parent in rs.inherits_of(local):
            if parent in rs.weapons:
                direct[parent].add(name)

    closure: dict[str, set[str]] = {}
    for root in ROOT_CLOSURES:
        seen: set[str] = set()
        stack = list(direct[root])
        while stack:
            name = stack.pop()
            if name in seen:
                continue
            seen.add(name)
            stack.extend(direct[name])
        closure[root] = {name for name in seen if not name.startswith("^")}
    return closure


def local_old_keys(node) -> set[str]:
    return {
        child.key.split("@", 1)[1]
        for child in node.children
        if child.key.startswith("Warhead@")
        and child.key.split("@", 1)[1] in OLD_KEYS
    }


def reintroduced_old_keys(rs: Ruleset, node, family_members: set[str]) -> set[str]:
    """Old flat keys introduced locally after the converted family parent."""
    keys = local_old_keys(node)
    for _, parent in rs.inherits_of(node):
        if parent in family_members:
            continue
        inherited = rs.resolve_weapon(parent)
        if inherited is not None:
            keys.update(positive_main_keys(inherited) & OLD_KEYS)
    return keys


def positive_main_keys(node) -> set[str]:
    keys = set()
    for child in node.children:
        if not child.key.startswith("Warhead@") or child.value not in {"AreaDamage", "SpreadDamage"}:
            continue
        if "Percentage" in child.key or "FriendlyFire" in child.key:
            continue
        try:
            damage = int(str(child.get("Damage") or "0"))
        except ValueError:
            continue
        if damage > 0:
            keys.add(child.key.split("@", 1)[1])
    return keys


def flat_targets(node) -> str:
    ordered = []
    for child in node.children:
        if not child.key.startswith("Warhead@"):
            continue
        if child.key.split("@", 1)[1] not in OLD_KEYS:
            continue
        for token in str(child.get("ValidTargets") or "").split(","):
            token = token.strip()
            if token and token not in ordered:
                ordered.append(token)
    if not ordered:
        raise RuntimeError(f"{node.key}: missing Light + Medium ValidTargets")
    return ", ".join(ordered)


def combined_percentage_scale(node, total_damage: int) -> int:
    units = sum(
        int(app["runtime_units"])
        for app in pd.percentage_applications(node, 200_000)
        if app["tag"] in OLD_KEYS
    )
    if units <= 0:
        return 0
    estimate = max(1, units * pd.FOLDED_SCALE_DENOMINATOR // total_damage)
    for scale in range(max(1, estimate - 200), estimate + 201):
        if pd.folded_units(total_damage, scale)[1] != units:
            continue
        for hp in HEALTH_VALUES:
            before = sum(
                int(app["runtime_hp"])
                for app in pd.percentage_applications(node, hp)
                if app["tag"] in OLD_KEYS
            )
            after = pd.runtime_percentage_hp(hp, units, pd.FOLDED_DEFAULT_DENOMINATOR)
            if abs(before - after) > 1:
                raise RuntimeError(
                    f"{node.key}: folded percentage merge changes {hp} HP target "
                    f"from {before} to {after}")
        return scale
    raise RuntimeError(f"{node.key}: cannot preserve {units} folded percentage units")


def set_percentage_scale(changed: dict[pathlib.Path, list[str]], path: pathlib.Path,
                         weapon: str, scale: int) -> None:
    lines = changed[path]
    start, end = block_bounds(lines, weapon)
    marker = f"\tWarhead@{COMPATIBILITY_KEY}:"
    indexes = [i for i in range(start + 1, end) if lines[i].rstrip("\r\n") == marker]
    if len(indexes) != 1:
        raise RuntimeError(f"{weapon}: expected one local compatibility block")
    wh_start = indexes[0]
    wh_end = end
    for i in range(wh_start + 1, end):
        if lines[i].startswith("\t") and not lines[i].startswith("\t\t") and lines[i].strip():
            wh_end = i
            break
    scale_rows = [i for i in range(wh_start + 1, wh_end)
                  if lines[i].lstrip().startswith("PercentageScale:")]
    if len(scale_rows) != 1:
        raise RuntimeError(f"{weapon}: expected one PercentageScale override")
    lines[scale_rows[0]] = f"\t\tPercentageScale: {scale}\n"


def validate_baseline(rs: Ruleset) -> dict[str, set[str]]:
    closure = descendants(rs)
    for root, expected in ROOT_CLOSURES.items():
        if closure[root] != expected:
            added = sorted(closure[root] - expected)
            missing = sorted(expected - closure[root])
            raise RuntimeError(f"{root}: inheritance closure changed; added={added}, missing={missing}")
        resolved = rs.resolve_weapon(root)
        if resolved is None:
            raise RuntimeError(f"{root}: missing resolved weapon")
        mains = positive_main_keys(resolved)
        already = COMPATIBILITY_KEY in mains and not (OLD_KEYS & mains)
        if not already and not OLD_KEYS <= mains:
            raise RuntimeError(f"{root}: expected Light + Medium bullet mains, found {sorted(mains)}")
    return closure


def validate_result() -> None:
    rs = Ruleset(ROOT)
    closure = validate_baseline(rs)
    for root, children in closure.items():
        for name in [root, *sorted(children)]:
            resolved = rs.resolve_weapon(name)
            if resolved is None:
                raise RuntimeError(f"{name}: missing after rewrite")
            mains = positive_main_keys(resolved)
            if OLD_KEYS & mains or COMPATIBILITY_KEY not in mains:
                raise RuntimeError(f"{name}: unresolved consolidation: {sorted(mains)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rs = Ruleset(ROOT)
    closure = validate_baseline(rs)
    changed: dict[pathlib.Path, list[str]] = {}
    summary = []

    for root, children in closure.items():
        local = rs.weapon(root)
        resolved = rs.resolve_weapon(root)
        if local is None or resolved is None:
            raise RuntimeError(f"{root}: missing source or resolved weapon")
        mains = positive_main_keys(resolved)
        already = COMPATIBILITY_KEY in mains and not (OLD_KEYS & mains)
        if not already:
            total = resolved_flat_total(resolved, OLD_KEYS)
            if total <= 0:
                raise RuntimeError(f"{root}: no positive Light + Medium flat total")
            path = pathlib.Path(local.file)
            apply_compatibility_block(
                changed, path, root, DESTINATION, OLD_KEYS,
                total, flat_targets(resolved))
            set_percentage_scale(
                changed, path, root, combined_percentage_scale(resolved, total))

        repaired = 0
        family_members = {root, *children}
        for name in sorted(children):
            child_local = rs.weapon(name)
            child_resolved = rs.resolve_weapon(name)
            if child_local is None or child_resolved is None:
                raise RuntimeError(f"{root}: missing descendant {name}")
            child_mains = positive_main_keys(child_resolved)
            if COMPATIBILITY_KEY in child_mains and not (OLD_KEYS & child_mains):
                continue
            removals = reintroduced_old_keys(rs, child_local, family_members)
            if not removals:
                continue
            child_total = resolved_flat_total(child_resolved, OLD_KEYS)
            if child_total <= 0:
                raise RuntimeError(f"{name}: no positive descendant flat total")
            path = pathlib.Path(child_local.file)
            apply_compatibility_block(
                changed, path, name, DESTINATION,
                removals, child_total, flat_targets(child_resolved),
                inherit_template=False)
            set_percentage_scale(
                changed, path, name,
                combined_percentage_scale(child_resolved, child_total))
            repaired += 1
        state = "already consolidated; " if already else ""
        summary.append((root, f"{state}{1 + len(children)} definitions; {repaired} local overrides"))

    for root, result in summary:
        print(f"{root}: {result}")
    print(f"{sum(1 + len(v) for v in closure.values())} reviewed concrete definitions")

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
