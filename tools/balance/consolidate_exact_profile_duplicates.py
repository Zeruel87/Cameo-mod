#!/usr/bin/env python3
"""Collapse the last mechanically identical ordinary main-damage profiles.

Only full recursive profile duplicates are selected.  Damage and the folded
PercentageScale fields may differ; projectile, effect, percentage, status,
targeting, and descendant behavior are pinned by resolved-tree hashes.
"""
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
from consolidate_compatibility_profiles import flat_nodes, fingerprint  # noqa: E402
from consolidate_final_safe_cohorts import percentage_scale  # noqa: E402
from consolidate_reviewed_weapon_roots import block_bounds, resolved_flat_total  # noqa: E402
from miniyaml import Ruleset  # noqa: E402


RA2120_SELECTED = {
    "RA2120xmm", "RA2120xmm_elite", "RA2120xmm_fire",
    "RA2120xmm_fire_elite", "RA2120xmm_tesla", "RA2120xmm_tesla_elite",
}
RA2120_DESCENDANTS = RA2120_SELECTED - {"RA2120xmm"} | {
    "RA2120xmm_rad", "RA2120xmm_rad_elite",
}
FLAK_DESCENDANTS = {
    "AAGunBoatFlak", "AAGunBoatFlak_elite", "RA2FlakTrackAAGun",
    "RA2FlakTrackAAGun_elite", "RA2FlakTrackGun_elite",
}
TESLA_ARMOR = {
    "TeslaArmorDischargeArc", "TeslaArmorDischargeFragment1",
    "TeslaArmorDischargeFragment2",
}

# selected keys, destination key, total, folded PercentageScale
SPECS = {
    **{
        name: (
            {"CannonHE_Heavy", "CannonHE_HeavyFlatCompatibility"},
            "CannonHE_Heavy", 12000, 3325,
        )
        for name in RA2120_SELECTED
    },
    "RA2FlakTrackGun": (
        {"Flak_Medium", "Flak_MediumFlatCompatibility"},
        "Flak_Medium", 8000, 2488,
    ),
    "TSPulseCannon_EMP": (
        {"TeslaWeapon", "TeslaChargedWeapon"},
        "TeslaChargedWeapon", 20000, 0,
    ),
    "TeslaArmorDischargeArc": (
        {"LightMissile", "TeslaWeapon"}, "TeslaWeapon", 24000, 0,
    ),
    "TeslaArmorDischargeFragment1": (
        {"LightMissile", "TeslaWeapon"}, "TeslaWeapon", 12000, 0,
    ),
    "TeslaArmorDischargeFragment2": (
        {"LightMissile", "TeslaWeapon"}, "TeslaWeapon", 8000, 0,
    ),
}

# Hashes exclude only the selected ordinary mains.  They pin every percentage
# companion and every projectile/effect/status/relationship descendant field.
PRESERVED_HASHES = {
    "RA2120xmm": "d67388638aee17cf11036eb137630243943cb637e83b660e7853604805fc7861",
    "RA2120xmm_elite": "1c644e2f3d9935b4fe81566b7c48f08ace9dd5c5f645f4f6b3df09191f02df53",
    "RA2120xmm_fire": "3009fc8b632319618c83c7b1f050001a524b89c869484f6a27a6966b34a7e75a",
    "RA2120xmm_fire_elite": "5c549cbb86cc91046b5e93dda2d6c11e609b7c4253ea0666302f543823cbfc91",
    "RA2120xmm_tesla": "0d9570cf658c1fde88d0fbbfad8430565710d500152878cc2d4c087d1efc9fc0",
    "RA2120xmm_tesla_elite": "a538d971d04320c09efaf8cad970a5eee92daa89536e8ecfe75735693e085e1e",
    "RA2FlakTrackGun": "efa8f008172e35f9330dbd4c33e3a04380f9a39135d15a564cd57a9564ceb5ef",
    "TSPulseCannon_EMP": "14e7fa57163f8d0dac0d00cbe93c884276c116bd35e6806c998c3266a3438197",
    "TeslaArmorDischargeArc": "8f135ba858dbba4b8ea2c5f34fd53674f715a19675e04be3cacaa032c77ed05a",
    "TeslaArmorDischargeFragment1": "89e58222b175e91a1159b794ec943c1bf77663d23f511419d71d2dc2bbee4ef1",
    "TeslaArmorDischargeFragment2": "f60726e144e238cbf9ba289f1d4e40abdd41ee21d5bfb5063f8773634fec76f8",
}

# These branches deliberately do not collapse with their parent.  Full resolved
# hashes make the converter restore their routing/profile behavior exactly.
BRANCH_HASHES = {
    "RA2120xmm_rad": "d5fe7864b7d66a5e456103b497b5aff210a128b248f09a60c90955449e64a8a4",
    "RA2120xmm_rad_elite": "82a22798e8c9f9785b51613dce5df897fc8b8a3d6ecc9f980035626d56919702",
    "RA2FlakTrackAAGun": "1ad8c6319e39e5be189d96ce21b53ad5cd3f27ccef8db7cf0fbfae06885ae902",
    "RA2FlakTrackAAGun_elite": "9ae7e8b0bda299b069740bf6ca3a93d8b542022cf7b0c9347c8603fc97ea70b1",
}

FLAK_BRANCH_PRESERVED_HASHES = {
    "RA2FlakTrackGun_elite": "4a6bc47b3d2a677a2394c554caddbe678fccadcd532c6b70db51dc79705c1176",
    "AAGunBoatFlak": "e0b8751f05235e6a9968f78adfa0a77c66009a1253c4fefdc3e858e6543f4575",
    "AAGunBoatFlak_elite": "25cd1fb56eb643ac44d3072d097f6df10437c698f93e8ae92c1b1b2b3f1fd2dc",
}


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


def node_payload(node):
    return [node.key, node.value, [node_payload(child) for child in node.children]]


def resolved_hash(rs: Ruleset, name: str, excluded: set[str] | None = None) -> str:
    resolved = rs.resolve_weapon(name)
    if resolved is None:
        raise RuntimeError(f"{name}: missing resolved weapon")
    excluded_keys = {f"Warhead@{key}" for key in (excluded or set())}
    payload = [node_payload(child) for child in resolved.children
               if child.key not in excluded_keys]
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def inspect(rs: Ruleset) -> bool:
    if descendants(rs, "RA2120xmm") != RA2120_DESCENDANTS:
        raise RuntimeError("RA2120xmm: descendant closure changed")
    if descendants(rs, "RA2FlakTrackGun") != FLAK_DESCENDANTS:
        raise RuntimeError("RA2FlakTrackGun: descendant closure changed")
    if descendants(rs, "TeslaArmorDischargeArc") != TESLA_ARMOR - {
            "TeslaArmorDischargeArc"}:
        raise RuntimeError("TeslaArmorDischargeArc: descendant closure changed")
    if descendants(rs, "TSPulseCannon_EMP"):
        raise RuntimeError("TSPulseCannon_EMP: unexpected descendants")

    states = set()
    for name, (old_keys, destination, total, scale) in SPECS.items():
        resolved = rs.resolve_weapon(name)
        mains = set(main_warheads(resolved))
        if mains == old_keys:
            states.add(False)
            nodes = flat_nodes(resolved)
            if not old_keys <= set(nodes):
                raise RuntimeError(f"{name}: selected main is not flat damage")
            if len({fingerprint(nodes[key]) for key in old_keys}) != 1:
                raise RuntimeError(f"{name}: selected profiles no longer match")
            if resolved_flat_total(resolved, old_keys) != total:
                raise RuntimeError(f"{name}: selected total changed")
            if percentage_scale(resolved, old_keys, total) != scale:
                raise RuntimeError(f"{name}: folded percentage scale changed")
        elif mains == {destination}:
            states.add(True)
            node = flat_nodes(resolved).get(destination)
            if node is None or int(str(node.get("Damage") or 0)) != total:
                raise RuntimeError(f"{name}: applied destination total changed")
            if scale and int(str(node.get("PercentageScale") or 0)) != scale:
                raise RuntimeError(f"{name}: applied PercentageScale changed")
        else:
            raise RuntimeError(
                f"{name}: expected {sorted(old_keys)} or {destination}; found {sorted(mains)}")

        actual = resolved_hash(rs, name, old_keys)
        if actual != PRESERVED_HASHES[name]:
            raise RuntimeError(f"{name}: preserved behavior hash changed")

    if len(states) != 1:
        raise RuntimeError("partial exact-profile consolidation detected")
    for name, expected in BRANCH_HASHES.items():
        if resolved_hash(rs, name) != expected:
            raise RuntimeError(f"{name}: protected descendant behavior changed")
    flak_keys = {"Flak_Medium", "Flak_MediumFlatCompatibility"}
    for name, expected in FLAK_BRANCH_PRESERVED_HASHES.items():
        if resolved_hash(rs, name, flak_keys) != expected:
            raise RuntimeError(f"{name}: protected non-damage behavior changed")

    expected_flak = {
        "RA2FlakTrackGun_elite": {
            "Flak_MediumFlatCompatibility": (8000, 2488, "Ground, Water")},
        "AAGunBoatFlak": {
            "Flak_Medium": (2000, 10000, "Ground, Water, Air"),
            "Flak_MediumFlatCompatibility": (6000, 0, "Ground, Water")},
        "AAGunBoatFlak_elite": {
            "Flak_Medium": (2000, 10000, "Ground, Water, Air"),
            "Flak_MediumFlatCompatibility": (6000, 0, "Ground, Water")},
    }
    for name, expected in expected_flak.items():
        nodes = flat_nodes(rs.resolve_weapon(name))
        actual = {
            key: (
                int(str(nodes[key].get("Damage") or 0)),
                int(str(nodes[key].get("PercentageScale") or 0)),
                str(nodes[key].get("ValidTargets") or ""),
            )
            for key in expected
        }
        if actual != expected or set(main_warheads(rs.resolve_weapon(name))) != set(expected):
            raise RuntimeError(f"{name}: protected ground/air split changed")
    return states == {True}


def lines_for(changed: dict[pathlib.Path, list[str]], rs: Ruleset, name: str):
    node = rs.weapon(name)
    if node is None:
        raise RuntimeError(f"{name}: source weapon missing")
    path = pathlib.Path(node.file)
    return path, changed.setdefault(
        path, path.read_text(encoding="utf-8-sig").splitlines(True))


def remove_line(lines: list[str], name: str, exact: str) -> None:
    start, end = block_bounds(lines, name)
    indexes = [i for i in range(start + 1, end)
               if lines[i].rstrip("\r\n") == exact]
    if len(indexes) != 1:
        raise RuntimeError(f"{name}: expected one {exact!r}")
    del lines[indexes[0]]


def remove_node(lines: list[str], name: str, key: str) -> None:
    start, end = block_bounds(lines, name)
    pattern = re.compile(r"^\t" + re.escape(key) + r":")
    indexes = [i for i in range(start + 1, end)
               if pattern.match(lines[i].rstrip("\r\n"))]
    if len(indexes) != 1:
        raise RuntimeError(f"{name}: expected one {key} node")
    first = indexes[0]
    last = end
    for i in range(first + 1, end):
        if lines[i].startswith("\t") and not lines[i].startswith("\t\t") \
                and lines[i].strip():
            last = i
            break
    del lines[first:last]


def set_field(lines: list[str], name: str, node_key: str, field: str,
              value: int) -> None:
    start, end = block_bounds(lines, name)
    marker = re.compile(r"^\tWarhead@" + re.escape(node_key) + r":")
    indexes = [i for i in range(start + 1, end)
               if marker.match(lines[i].rstrip("\r\n"))]
    if len(indexes) != 1:
        raise RuntimeError(f"{name}: expected one {node_key} override")
    node_start = indexes[0]
    node_end = end
    for i in range(node_start + 1, end):
        if lines[i].startswith("\t") and not lines[i].startswith("\t\t") \
                and lines[i].strip():
            node_end = i
            break
    field_rows = [i for i in range(node_start + 1, node_end)
                  if lines[i].lstrip().startswith(f"{field}:")]
    if len(field_rows) > 1:
        raise RuntimeError(f"{name}: duplicate {field}")
    if field_rows:
        lines[field_rows[0]] = f"\t\t{field}: {value}\n"
    else:
        lines.insert(node_end, f"\t\t{field}: {value}\n")


def apply_changes(rs: Ruleset) -> None:
    changed: dict[pathlib.Path, list[str]] = {}

    _path, lines = lines_for(changed, rs, "RA2120xmm")
    remove_line(lines, "RA2120xmm",
                "\tInherits@roleflat: ^Compatibility_CannonHE_HeavyFlat")
    remove_node(lines, "RA2120xmm", "Warhead@CannonHE_HeavyFlatCompatibility")
    set_field(lines, "RA2120xmm", "CannonHE_Heavy", "Damage", 12000)
    set_field(lines, "RA2120xmm", "CannonHE_Heavy", "PercentageScale", 3325)
    _path, lines = lines_for(changed, rs, "RA2120xmm_rad")
    remove_line(lines, "RA2120xmm_rad",
                "\t-Warhead@CannonHE_HeavyFlatCompatibility:")
    set_field(lines, "RA2120xmm_rad", "CannonHE_Heavy", "PercentageScale", 10000)

    _path, lines = lines_for(changed, rs, "RA2FlakTrackGun")
    remove_line(lines, "RA2FlakTrackGun",
                "\tInherits@roleflat: ^Compatibility_Flak_MediumFlat")
    remove_node(lines, "RA2FlakTrackGun", "Warhead@Flak_MediumFlatCompatibility")
    set_field(lines, "RA2FlakTrackGun", "Flak_Medium", "Damage", 8000)
    set_field(lines, "RA2FlakTrackGun", "Flak_Medium", "PercentageScale", 2488)

    _path, lines = lines_for(changed, rs, "RA2FlakTrackGun_elite")
    start, _end = block_bounds(lines, "RA2FlakTrackGun_elite")
    lines.insert(start + 2,
                 "\tInherits@finalmain: ^Compatibility_Flak_MediumFlat\n")
    _path, lines = lines_for(changed, rs, "RA2FlakTrackAAGun")
    remove_line(lines, "RA2FlakTrackAAGun",
                "\t-Warhead@Flak_MediumFlatCompatibility:")

    _path, lines = lines_for(changed, rs, "AAGunBoatFlak")
    start, _end = block_bounds(lines, "AAGunBoatFlak")
    lines.insert(start + 2,
                 "\tInherits@groundflat: ^Compatibility_Flak_MediumFlat\n")
    set_field(lines, "AAGunBoatFlak", "Flak_Medium", "Damage", 2000)
    set_field(lines, "AAGunBoatFlak", "Flak_Medium", "PercentageScale", 10000)
    start, end = block_bounds(lines, "AAGunBoatFlak")
    insertion = end
    while insertion > start + 1 and not lines[insertion - 1].strip():
        insertion -= 1
    lines[insertion:insertion] = [
        "\tWarhead@Flak_MediumFlatCompatibility:\n",
        "\t\tValidTargets: Ground, Water\n",
        "\t\tDamage: 6000\n",
        "\t\tPercentageScale: 0\n",
    ]

    _path, lines = lines_for(changed, rs, "TSPulseCannon_EMP")
    remove_node(lines, "TSPulseCannon_EMP", "Warhead@TeslaWeapon")
    set_field(lines, "TSPulseCannon_EMP", "TeslaChargedWeapon", "Damage", 20000)

    for name, total in (
            ("TeslaArmorDischargeArc", 24000),
            ("TeslaArmorDischargeFragment1", 12000),
            ("TeslaArmorDischargeFragment2", 8000)):
        _path, lines = lines_for(changed, rs, name)
        remove_node(lines, name, "Warhead@LightMissile")
        set_field(lines, name, "TeslaWeapon", "Damage", total)

    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")


def validate_result() -> None:
    if not inspect(Ruleset(ROOT)):
        raise RuntimeError("exact-profile duplicate cohort remains unconsolidated")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    rules = Ruleset(ROOT)
    already = inspect(rules)
    if already:
        print(f"Already consolidated {len(SPECS)} concrete definitions")
        return 0
    print(f"4 roots; {len(SPECS)} concrete definitions")
    if not args.apply:
        print("Dry run: exact profiles, closures, percentages, and branch hashes pass")
        return 0
    apply_changes(rules)
    validate_result()
    print("Applied and validated 4 files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
