#!/usr/bin/env python3
"""Consolidate a reviewed artillery, bomb, missile, and state tranche."""
from __future__ import annotations

import argparse
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from audit_three_way_split import main_warheads  # noqa: E402
from consolidate_corroborated_role_profiles import (  # noqa: E402
    remove_local_compatibility_removal,
    set_state_scale,
)
from consolidate_final_safe_cohorts import (  # noqa: E402
    cleanup_duplicate_template_inherits,
    cleanup_stale_removals,
    ensure_template_inherit,
    flat_main_nodes,
    percentage_scale,
    set_scale,
)
from consolidate_reviewed_weapon_roots import (  # noqa: E402
    add_compatibility_templates,
    apply_compatibility_block,
    block_bounds,
)
from consolidate_rule_driven_energy_ordnance import (  # noqa: E402
    add_percentage_companions,
    digest,
    remove_batch_parent_percentage_companions,
)
from miniyaml import Ruleset  # noqa: E402
import percentage_damage as pd  # noqa: E402


GROUPS = {
    "CannonHE_Heavy": {
        "TSScoopDualTur", "RA2GrandCannonWeapon", "YamatoCannon",
    },
    "CannonHE_Medium": {
        "D2K_155mm", "D2K_155mm_turret", "HammerheadArtillery",
        "RA2MortarBike", "RA2MortarBike_elite",
        "SteelCruiserArtillery", "SteelCruiserArtillery_elite",
    },
    "Concussion_Medium": {
        "ArtilleryShell", "SpecterArtilleryShell", "D2K_155mm3",
        "Dune_SiegeMortar", "RA160mm", "RA160mmE_elite",
        "RA160mmE_fire_elite", "RA160mmE_tesla_elite", "RA160mm_fire",
        "RA160mm_tesla",
    },
    "Demolition_Heavy": {
        "AsianSubmarineBomb", "InfestedExplosion", "IvanBomb", "IvanBombAir",
        "SealBomb", "TanyaBomb", "ParaBomb", "bigshieemortar", "sandmarinemortar",
    },
    "Demolition_Light": {
        "LatinMonkeyGrenade1", "LatinMonkeyGrenade2", "LatinMonkeyGrenade3",
        "LatinMonkeyGrenadeExplode", "ReaperGrenade", "Debris2", "Debris3", "Debris4",
    },
    "MissileAP_Medium": {
        "BlackEagleMissiles", "BlackEagleMissiles_elite", "NaxiMissileUboat",
        "NaxShoeRocket", "RA2AkulaRockets",
    },
    "MissileAP_Heavy": {"YRBoomerSCUD"},
    "MissileHE_Heavy": {
        "BigShieeTusk", "Hellfire", "MonsterTankTusk", "SandmarineTusk",
        "SandmarineTuskCryo", "CabalHeavyReaperMissiles_AA",
    },
    "MissileHE_Medium": {
        "TSRuinerMissile", "TSSBoatTusk", "TSStankTusk",
        "CabalManticoreMissilesAA", "CabalReaperMissiles_AA",
    },
    "Chemical_Light": {"RA160mm_rad"},
    "Chemical_Medium": {
        "RA2120mm_rad", "RA2120mm_rad_elite", "TSInfantryMortarChem",
        "TSScoopDualChem",
    },
    "Chemical_Heavy": {"TS120mmxChem"},
    "Flame_Medium": {"105mmThermobaric"},
    "Flame_Heavy": {"Napalm"},
    "Thermobaric_Heavy": {
        "ra120mmThermobaric", "ra120mmThermobaricTargetingComputer",
        "ra120mm2Thermobaric", "ra120mm2ThermobaricTargetingComputer",
    },
    "CannonAP_Light": {
        "120mm_cobra", "120mm_cobra_deploy", "120mm_python", "120mm_python_deploy",
    },
    "Railgun_Heavy": {
        "DalekCannon", "DalekCannon_elite", "DalekCannonScatter",
        "DalekCannonScatterE",
    },
}

DESTINATION_OVERRIDES = {
    "CabalHeavyReaperMissiles_AA": "MissileAA_Heavy",
    "CabalManticoreMissilesAA": "MissileAA_Medium",
    "CabalReaperMissiles_AA": "MissileAA_Medium",
    "RA160mmE_fire_elite": "CannonFire_Heavy",
    "RA160mm_fire": "CannonFire_Heavy",
    "RA160mmE_tesla_elite": "Tesla_Heavy",
    "RA160mm_tesla": "Tesla_Heavy",
    "RA2MortarBike": "Concussion_Medium",
    "RA2MortarBike_elite": "Concussion_Medium",
    "SandmarineTuskCryo": "MissileCryo_Heavy",
}
SOURCE_OVERRIDES = {
    "CabalHeavyReaperMissiles_AA": "MissileHE_Heavy",
    "CabalManticoreMissilesAA": "MissileHE_Medium",
    "CabalReaperMissiles_AA": "MissileHE_Medium",
    "RA160mmE_fire_elite": "Concussion_Medium",
    "RA160mm_fire": "Concussion_Medium",
    "RA160mmE_tesla_elite": "Concussion_Medium",
    "RA160mm_tesla": "Concussion_Medium",
    "RA2MortarBike": "CannonHE_MediumFlatCompatibility",
    "RA2MortarBike_elite": "CannonHE_MediumFlatCompatibility",
    "SandmarineTuskCryo": "MissileHE_Heavy",
    "ra120mmThermobaric": "Flame_Heavy",
    "ra120mmThermobaricTargetingComputer": "Flame_Heavy",
    "ra120mm2Thermobaric": "Flame_Heavy",
    "ra120mm2ThermobaricTargetingComputer": "Flame_Heavy",
}
SELECTED = {
    name: DESTINATION_OVERRIDES.get(name, destination)
    for destination, names in GROUPS.items() for name in names
}
BASE_DESTINATION = {
    name: destination for destination, names in GROUPS.items() for name in names
}
INHERITED_COMPAT_REMOVALS = {
    "RA160mm_rad": {"Concussion_MediumFlatCompatibility"},
}
DESTINATION_STATE_SUPPRESSIONS = {"SandmarineTuskCryo"}
EXPECTED_COUNT = 74
BASELINE_DIGEST = "c07c136a2f6ab3db561af3fedc4aff9659a449c0c87b851dacfe13e650665323"

# root: (abstract legacy name, direct children that retain the old payload)
ISOLATIONS = {
    "D2K_155mm": ("^D2K155mmLegacy", {"D2K_SiegeQuad"}),
    "Debris2": (
        "^Debris2Legacy", {"ExplosiveDebris", "DeathHandCluster", "oDeathHandCluster"}),
    "ParaBomb": ("^ParaBombLegacy", {"GLToxinBomb"}),
    "RA160mm": ("^RA160mmLegacy", {"RA160mm_rad"}),
    "RA160mm_rad": ("^RA160mmRadLegacy", {"RA160mmE_rad_elite"}),
    "SandmarineTusk": (
        "^SandmarineTuskLegacy", {"SandmarineTuskFire", "SandmarineTuskTwin"}),
    "SpecterArtilleryShell": (
        "^SpecterArtilleryShellLegacy", {"SpecterArtilleryShellUpgrade"}),
}


def weighted_state_plan(nodes, total: int):
    names = {
        str(node.get("PhysicalStateName"))
        for node in nodes.values() if node.get("PhysicalStateName")
    }
    if len(names) > 1:
        raise RuntimeError(f"mixed physical states: {sorted(names)}")
    if not names:
        return None
    state = next(iter(names))
    weighted = sum(
        int(str(node.get("Damage") or 0))
        * int(str(node.get("PhysicalStateScale") or 100))
        for node in nodes.values()
        if node.get("PhysicalStateName") == state
    )
    return state, math.ceil(weighted / total)


def baseline_rows(rs: Ruleset):
    rows = {}
    for name, destination in sorted(SELECTED.items()):
        resolved = rs.resolve_weapon(name)
        mains = set(main_warheads(resolved))
        compatibility = f"{destination}FlatCompatibility"
        if mains == {compatibility}:
            rows[name] = None
            continue
        source = SOURCE_OVERRIDES.get(name, destination)
        if len(mains) < 2 or source not in mains:
            raise RuntimeError(f"{name}: expected {source} in {sorted(mains)}")
        nodes = flat_main_nodes(resolved, mains)
        if set(nodes) != mains:
            raise RuntimeError(f"{name}: selected main is not flat damage")
        total = sum(int(str(node.get("Damage") or 0)) for node in nodes.values())
        targets = str(nodes[source].get("ValidTargets") or "").strip()
        if total <= 0 or not targets or targets == "*":
            raise RuntimeError(f"{name}: invalid total or target route")
        try:
            folded_scale = percentage_scale(resolved, mains, total)
            standalone = {}
        except RuntimeError:
            folded_scale = 0
            standalone = {
                key: {
                    "units": pd.folded_units(
                        int(str(node.get("Damage") or 0)),
                        int(str(node.get("PercentageScale") or 0)))[1],
                    "denominator": int(str(
                        node.get("PercentageDenominator")
                        or pd.FOLDED_DEFAULT_DENOMINATOR)),
                }
                for key, node in sorted(nodes.items())
                if int(str(node.get("PercentageScale") or 0)) != 0
            }
        rows[name] = {
            "destination": destination,
            "mains": sorted(mains),
            "total": total,
            "targets": targets,
            "percentage_scale": folded_scale,
            "percentage": standalone,
            "state": weighted_state_plan(nodes, total),
        }
    return rows


def isolate_legacy_root(changed, rs: Ruleset, root: str,
                        legacy: str, children: set[str]) -> None:
    local = rs.weapon(root)
    path = pathlib.Path(local.file)
    lines = changed.setdefault(
        path, path.read_text(encoding="utf-8-sig").splitlines(True))
    start, end = block_bounds(lines, root)
    lines[start] = f"{legacy}:\n"
    lines[end:end] = [f"{root}:\n", f"\tInherits: {legacy}\n"]
    for child in sorted(children):
        child_local = rs.weapon(child)
        child_path = pathlib.Path(child_local.file)
        child_lines = changed.setdefault(
            child_path, child_path.read_text(encoding="utf-8-sig").splitlines(True))
        start, end = block_bounds(child_lines, child)
        matches = [i for i in range(start + 1, end)
                   if child_lines[i].strip().endswith(f": {root}")]
        if len(matches) != 1:
            raise RuntimeError(f"{child}: inheritance fingerprint changed")
        prefix = child_lines[matches[0]].split(":", 1)[0]
        child_lines[matches[0]] = f"{prefix}: {legacy}\n"


def set_state_name(changed, path: pathlib.Path, name: str,
                   destination: str, state: str) -> None:
    lines = changed[path]
    start, end = block_bounds(lines, name)
    marker = f"\tWarhead@{destination}FlatCompatibility:"
    rows = [i for i in range(start + 1, end)
            if lines[i].rstrip("\r\n") == marker]
    if len(rows) != 1:
        raise RuntimeError(f"{name}: expected one compatibility override")
    node_start = rows[0]
    node_end = end
    for i in range(node_start + 1, end):
        if lines[i].startswith("\t") and not lines[i].startswith("\t\t") \
                and lines[i].strip():
            node_end = i
            break
    matches = [i for i in range(node_start + 1, node_end)
               if re.match(r"^\t\tPhysicalStateName:", lines[i])]
    if len(matches) > 1:
        raise RuntimeError(f"{name}: duplicate PhysicalStateName")
    if matches:
        lines[matches[0]] = f"\t\tPhysicalStateName: {state}\n"
    else:
        lines.insert(node_end, f"\t\tPhysicalStateName: {state}\n")


def suppress_destination_state(changed, path: pathlib.Path, name: str,
                               destination: str) -> None:
    """Keep an existing fixed state payload from being applied a second time."""
    lines = changed[path]
    start, end = block_bounds(lines, name)
    marker = f"\tWarhead@{destination}FlatCompatibility:"
    rows = [i for i in range(start + 1, end)
            if lines[i].rstrip("\r\n") == marker]
    if len(rows) != 1:
        raise RuntimeError(f"{name}: expected one compatibility override")
    node_end = end
    for i in range(rows[0] + 1, end):
        if lines[i].startswith("\t") and not lines[i].startswith("\t\t") \
                and lines[i].strip():
            node_end = i
            break
    lines.insert(node_end, "\t\t-PhysicalStates:\n")


def apply_changes(rs: Ruleset, rows) -> None:
    changed: dict[pathlib.Path, list[str]] = {}
    for root, (legacy, children) in ISOLATIONS.items():
        isolate_legacy_root(changed, rs, root, legacy, children)
    add_compatibility_templates(changed, rs, set(SELECTED.values()))
    for name in sorted(SELECTED):
        plan = rows[name]
        destination = plan["destination"]
        local = rs.weapon(name)
        path = pathlib.Path(local.file)
        resolved = rs.resolve_weapon(name)
        remove_batch_parent_percentage_companions(
            changed, path, name, rs, rows)
        add_percentage_companions(changed, path, name, resolved, plan)
        remove_local_compatibility_removal(
            changed, path, name, destination)
        ensure_template_inherit(changed, path, name, destination)
        apply_compatibility_block(
            changed, path, name, destination, set(plan["mains"]),
            plan["total"], plan["targets"],
            extra_removals=(
                ({f"{BASE_DESTINATION[name]}FlatCompatibility"}
                 if BASE_DESTINATION[name] != destination else set())
                | INHERITED_COMPAT_REMOVALS.get(name, set())),
            inherit_template=False)
        set_scale(changed, path, name, destination, plan["percentage_scale"])
        if plan["state"] is not None:
            state, scale = plan["state"]
            set_state_name(changed, path, name, destination, state)
            set_state_scale(changed, path, name, destination, scale)
        if name in DESTINATION_STATE_SUPPRESSIONS:
            suppress_destination_state(changed, path, name, destination)
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")
    cleanup_stale_removals(set(SELECTED))
    cleanup_duplicate_template_inherits(set(SELECTED))


def validate_result() -> None:
    rs = Ruleset(ROOT)
    for name, destination in sorted(SELECTED.items()):
        mains = set(main_warheads(rs.resolve_weapon(name)))
        expected = {f"{destination}FlatCompatibility"}
        if mains != expected:
            raise RuntimeError(f"{name}: expected {sorted(expected)}; found {sorted(mains)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if len(SELECTED) != EXPECTED_COUNT:
        raise RuntimeError(f"expected {EXPECTED_COUNT}, found {len(SELECTED)}")
    rs = Ruleset(ROOT)
    rows = baseline_rows(rs)
    states = {row is None for row in rows.values()}
    if states == {True}:
        validate_result()
        print(f"Already consolidated {len(SELECTED)} definitions")
        return 0
    if len(states) != 1:
        raise RuntimeError("partial blast/ordnance tranche detected")
    current_digest = digest(rows)
    print(f"{len(SELECTED)} definitions; baseline digest {current_digest}")
    if BASELINE_DIGEST and current_digest != BASELINE_DIGEST:
        raise RuntimeError("baseline fingerprint changed")
    if not args.apply:
        print("Dry run: totals, routes, percentage arithmetic, and states pass")
        return 0
    if not BASELINE_DIGEST:
        raise RuntimeError("pin BASELINE_DIGEST before applying")
    apply_changes(rs, rows)
    validate_result()
    print(f"Applied and validated {len(SELECTED)} definitions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
