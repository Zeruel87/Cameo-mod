#!/usr/bin/env python3
"""Collapse the final reviewed, mechanically safe multi-main cohorts.

These selections passed delivery/effect identity, targeting, relationship,
percentage-rounding, overflow, semantic-name, and complete-closure screens.  The
conversion deliberately adopts the selected canonical armor/blast profile while
preserving nominal flat damage and the folded percentage result within one HP.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from miniyaml import Ruleset  # noqa: E402
from audit_three_way_split import main_warheads  # noqa: E402
from consolidate_reviewed_weapon_roots import (  # noqa: E402
    add_compatibility_templates,
    apply_compatibility_block,
    block_bounds,
    resolved_flat_total,
)
import percentage_damage as pd  # noqa: E402
from review_batch_diff import active_health_values  # noqa: E402

HEALTH_VALUES = active_health_values(ROOT)

# Root closures are explicit so a newly inherited variant fails closed.
ROOTS = {
    "APCGun": ("Flak_Medium", {"APCGun_AA"}),
    "APCGunAllies": ("Flak_Medium", {"APCGunAllies_AA"}),
    "NaxHaenebuQuadCannon": ("Flak_Medium", {"NaxHaenebuQuadCannon_elite"}),
    "TKMQuadCannonAG": ("Flak_Medium", {"TKMQuadCannonAA"}),
    "TKMZazaCannonAG": ("Flak_Medium", {"TKMZazaCannonAA"}),
    "CorsairFlash": ("Flak_Medium", set()),
    "RA2FlakTrackGun_elite": ("Flak_Medium", set()),
    "TKMAATurretCannon": ("Flak_Medium", set()),
    "TS30mm": ("Flak_Medium", set()),
    "TSAAPCCannon": ("Flak_Medium", set()),
    "TSMutApcCannon": ("Flak_Medium", set()),
    "BorisAKM": ("Bullet_Medium", {"BorisAKM2", "BorisAKM_elite"}),
    "asianalliance_fanatic_shotgun": (
        "Bullet_Medium",
        {"asianalliance_fanatic_shotgun_elite", "asianalliance_fanatic_shotgun_upgrade"},
    ),
    "ASDFGun": ("Bullet_Medium", {"ASDFGun2"}),
    "CHGuardRifle": ("Bullet_Medium", set()),
    "NaxPlanegun_elite": ("Bullet_Medium", set()),
    "RA2CRM60": ("Bullet_Medium", set()),
    "TSAssaultCannon": ("Bullet_Medium", set()),
    "TSBowlerCannon": ("Bullet_Medium", set()),
    "TSJumpCannon": ("Bullet_Medium", set()),
    "elitecadregun": ("Bullet_Medium", set()),
    "ra1_soviets_ak47conscript_rifle": ("Bullet_Medium", set()),
    "td_gdi_shotgunner_shotgun": ("Bullet_Medium", set()),
    "HindMissiles": ("MissileAP_Medium", set()),
    "HueyTwinMissiles": ("MissileAP_Medium", set()),
    "RA2HornetMissile": ("MissileAP_Medium", set()),
    "RA2Gren60mm": ("CannonAP_Light", {"RA2Gren60mm_elite"}),
    "TS70mmTur": ("CannonAP_Light", set()),
}

# These two nested compatibility folds are authored by the companion converter
# but share the same post-apply stale-removal cleanup requirement.
COMPATIBILITY_NESTED = {"DeviatorMissile_Artillery", "wc2highArrowFire"}


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
    result: dict[str, str] = {}
    for root, (destination, expected) in ROOTS.items():
        actual = descendants(rs, root)
        if actual != expected:
            raise RuntimeError(
                f"{root}: closure changed; added={sorted(actual - expected)}, "
                f"missing={sorted(expected - actual)}")
        for name in {root, *expected}:
            if name in result and result[name] != destination:
                raise RuntimeError(f"{name}: conflicting destinations")
            result[name] = destination
    return result


def tokens(raw) -> tuple[str, ...]:
    return tuple(sorted(token.strip() for token in str(raw or "").split(",") if token.strip()))


def flat_main_nodes(resolved, keys: set[str]):
    return {
        child.key.split("@", 1)[1]: child
        for child in resolved.children
        if child.key.startswith("Warhead@")
        and child.key.split("@", 1)[1] in keys
        and child.value in {"AreaDamage", "SpreadDamage"}
    }


def percentage_scale(resolved, keys: set[str], total: int) -> int:
    units = sum(
        int(app["runtime_units"])
        for app in pd.percentage_applications(resolved, 200_000)
        if app["tag"] in keys
    )
    if units <= 0:
        return 0
    estimate = max(1, units * pd.FOLDED_SCALE_DENOMINATOR // total)
    for scale in range(max(1, estimate - 1000), estimate + 1001):
        try:
            if pd.folded_units(total, scale)[1] != units:
                continue
        except (OverflowError, ValueError):
            continue
        if all(
            abs(sum(
                int(app["runtime_hp"])
                for app in pd.percentage_applications(resolved, hp)
                if app["tag"] in keys
            ) - pd.runtime_percentage_hp(
                hp, units, pd.FOLDED_DEFAULT_DENOMINATOR)) <= 1
            for hp in HEALTH_VALUES
        ):
            return scale
    raise RuntimeError(f"{resolved.key}: no safe folded percentage scale")


def inspect_baseline(rs: Ruleset, selected: dict[str, str]):
    plans = {}
    for name, destination in selected.items():
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            raise RuntimeError(f"{name}: missing resolved weapon")
        mains = set(main_warheads(resolved))
        compatibility = f"{destination}FlatCompatibility"
        if mains == {compatibility}:
            plans[name] = None
            continue
        if destination not in mains or len(mains) < 2:
            raise RuntimeError(
                f"{name}: expected multi-main weapon containing {destination}; "
                f"found {sorted(mains)}")
        nodes = flat_main_nodes(resolved, mains)
        if set(nodes) != mains:
            raise RuntimeError(f"{name}: unsupported non-flat main in {sorted(mains)}")
        contract_fields = (
            "ValidTargets", "InvalidTargets", "ValidRelationships",
            "InvalidRelationships", "AffectsParent", "TargetActorCenter",
        )
        contracts = {
            tuple(tokens(node.get(field)) for field in contract_fields)
            for node in nodes.values()
        }
        if len(contracts) != 1:
            raise RuntimeError(f"{name}: main target contracts differ")
        total = resolved_flat_total(resolved, mains)
        if total <= 0:
            raise RuntimeError(f"{name}: no positive flat total")
        plans[name] = {
            "keys": mains,
            "total": total,
            "targets": str(nodes[destination].get("ValidTargets") or ""),
            "scale": percentage_scale(resolved, mains, total),
        }
    states = {plan is None for plan in plans.values()}
    if len(states) > 1:
        raise RuntimeError("partial final-cohort consolidation detected")
    return plans, states == {True}


def ensure_template_inherit(changed: dict[pathlib.Path, list[str]], path: pathlib.Path,
                            weapon: str, destination: str) -> None:
    lines = changed.setdefault(path, path.read_text(encoding="utf-8-sig").splitlines(True))
    start, end = block_bounds(lines, weapon)
    template = f"^Compatibility_{destination}Flat"
    if any(
        re.match(r"^\tInherits(?:@[^:]+)?:\s*" + re.escape(template) + r"\s*$",
                 lines[index].rstrip("\r\n"))
        for index in range(start + 1, end)
    ):
        return
    if any(re.match(r"^\tInherits@finalmain:", lines[index])
           for index in range(start + 1, end)):
        raise RuntimeError(f"{weapon}: Inherits@finalmain already used")
    lines.insert(start + 1, f"\tInherits@finalmain: {template}\n")


def set_scale(changed: dict[pathlib.Path, list[str]], path: pathlib.Path,
              weapon: str, destination: str, scale: int) -> None:
    lines = changed[path]
    start, end = block_bounds(lines, weapon)
    marker = f"\tWarhead@{destination}FlatCompatibility:"
    rows = [index for index in range(start + 1, end)
            if lines[index].rstrip("\r\n") == marker]
    if len(rows) != 1:
        raise RuntimeError(f"{weapon}: expected one final compatibility block")
    block_start = rows[0]
    block_end = end
    for index in range(block_start + 1, end):
        if lines[index].startswith("\t") and not lines[index].startswith("\t\t") \
                and lines[index].strip():
            block_end = index
            break
    scale_rows = [index for index in range(block_start + 1, block_end)
                  if lines[index].lstrip().startswith("PercentageScale:")]
    if len(scale_rows) != 1:
        raise RuntimeError(f"{weapon}: expected one PercentageScale")
    lines[scale_rows[0]] = f"\t\tPercentageScale: {scale}\n"


def cleanup_stale_removals(names: set[str]) -> int:
    """Drop redundant descendant removals after their parent has been converted."""
    rules = Ruleset(ROOT)
    changed: dict[pathlib.Path, list[str]] = {}
    removed = 0
    for name in sorted(names):
        local = rules.weapon(name)
        if local is None:
            raise RuntimeError(f"{name}: missing cleanup source")
        removals = {
            child.key[1:] for child in local.children
            if child.key.startswith("-Warhead@")
        }
        available = {
            child.key for child in local.children
            if child.key.startswith("Warhead@")
        }
        for child in local.children:
            if child.key != "Inherits" and not child.key.startswith("Inherits@"):
                continue
            parent = rules.resolve_weapon(str(child.value))
            if parent is not None:
                available.update(
                    item.key for item in parent.children
                    if item.key.startswith("Warhead@"))
        stale = removals - available
        if not stale:
            continue
        path = pathlib.Path(local.file)
        lines = changed.setdefault(
            path, path.read_text(encoding="utf-8-sig").splitlines(True))
        start, end = block_bounds(lines, name)
        markers = {f"\t-{key}:" for key in stale}
        indexes = [index for index in range(start + 1, end)
                   if lines[index].rstrip("\r\n") in markers]
        if len(indexes) != len(stale):
            raise RuntimeError(f"{name}: stale-removal source fingerprint changed")
        for index in reversed(indexes):
            del lines[index]
            removed += 1
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")
    return removed


def cleanup_duplicate_template_inherits(names: set[str]) -> int:
    """Remove direct compatibility inherits already supplied by an ancestor."""
    rules = Ruleset(ROOT)
    changed: dict[pathlib.Path, list[str]] = {}
    removed = 0

    def ancestors(name: str) -> set[str]:
        seen: set[str] = set()
        stack = [parent for _, parent in rules.inherits_of(rules.weapon(name))
                 if parent in rules.weapons]
        while stack:
            parent = stack.pop()
            if parent in seen:
                continue
            seen.add(parent)
            stack.extend(
                grandparent for _, grandparent in rules.inherits_of(rules.weapon(parent))
                if grandparent in rules.weapons)
        return seen

    for name in sorted(names):
        local = rules.weapon(name)
        if local is None:
            raise RuntimeError(f"{name}: missing duplicate-inherit source")
        direct = [child for child in local.children if child.key == "Inherits@finalmain"]
        if not direct:
            continue
        if len(direct) != 1:
            raise RuntimeError(f"{name}: duplicate local Inherits@finalmain")
        template = str(direct[0].value)
        inherited = any(
            any(child.key.startswith("Inherits") and str(child.value) == template
                for child in rules.weapon(parent).children)
            for parent in ancestors(name)
        )
        if not inherited:
            continue
        path = pathlib.Path(local.file)
        lines = changed.setdefault(
            path, path.read_text(encoding="utf-8-sig").splitlines(True))
        start, end = block_bounds(lines, name)
        marker = f"\tInherits@finalmain: {template}"
        indexes = [index for index in range(start + 1, end)
                   if lines[index].rstrip("\r\n") == marker]
        if len(indexes) != 1:
            raise RuntimeError(f"{name}: duplicate-inherit source fingerprint changed")
        del lines[indexes[0]]
        removed += 1
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")
    return removed


def validate_result() -> None:
    rs = Ruleset(ROOT)
    selected = selections(rs)
    _plans, already = inspect_baseline(rs, selected)
    if not already:
        raise RuntimeError("final cohort remains partially consolidated")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rs = Ruleset(ROOT)
    selected = selections(rs)
    plans, already = inspect_baseline(rs, selected)
    if already:
        if args.apply:
            removed = cleanup_stale_removals(set(selected) | COMPATIBILITY_NESTED)
            duplicate_inherits = cleanup_duplicate_template_inherits(set(selected))
            validate_result()
            print(f"Removed {removed} stale descendant removals and "
                  f"{duplicate_inherits} duplicate template inherits")
        print(f"Already consolidated {len(selected)} concrete definitions")
        return 0
    print(f"{len(ROOTS)} roots; {len(selected)} concrete definitions")
    if not args.apply:
        print("Dry run: closure and arithmetic guards pass")
        return 0

    changed: dict[pathlib.Path, list[str]] = {}
    add_compatibility_templates(
        changed, rs, {destination for destination, _closure in ROOTS.values()})
    for name in sorted(selected):
        destination = selected[name]
        plan = plans[name]
        if plan is None:
            continue
        local = rs.weapon(name)
        if local is None:
            raise RuntimeError(f"{name}: missing source weapon")
        path = pathlib.Path(local.file)
        ensure_template_inherit(changed, path, name, destination)
        compatibility = f"{destination}FlatCompatibility"
        apply_compatibility_block(
            changed, path, name, destination, plan["keys"] - {compatibility},
            plan["total"], plan["targets"], inherit_template=False)
        set_scale(changed, path, name, destination, plan["scale"])
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")
    cleanup_stale_removals(set(selected) | COMPATIBILITY_NESTED)
    cleanup_duplicate_template_inherits(set(selected))
    validate_result()
    print(f"Applied and validated {len(changed)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
