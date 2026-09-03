#!/usr/bin/env python3
"""Apply the audited final retired-family root mappings.

This deliberately consolidates only ordinary flat health-damage slices.  Legacy
percentage applications remain separate so the shipped runtime keeps its per-node
rounding and overflow behaviour.  Special warheads such as OpenToppedDamage and
AffectsIntegrity are not flattened into health damage.

Role mappings inferred from weapon identity and actor use are explicit below and
must pass the merged-baseline behavior comparison. Exceptional mixed
roots use exact local compatibility slices so no arbitrary balance ruling is hidden
inside this structural pass.  Descendant overrides are repaired explicitly.

Two separately reviewed operations complete the original 99-root batch:
RA2CRM60H's sniper splash is collapsed to a point-like bullet slice, and the
unreferenced HueyFireMissiles definition is removed. Their applied-state invariants
are verified whenever this tool runs.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))
from miniyaml import Node, Ruleset  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/audit/latest/remaining_weapon_classification.json"
FLAT_TYPES = {"AreaDamage", "SpreadDamage"}

# Identity-first inferences from active actor/armament review. Each entry is an
# explicit accepted-change declaration, not a claim of individual maintainer input.
# Pricing is intentionally absent.
ROLE = {
    "AsianMLRS": "MissileAA_Medium",
    "AsianChemical": "Chemical_Medium",
    "AsianMaidenBow": "Arrow_Light",
    "AthenaLaser": "Laser_Heavy",
    "BCLaser": "Laser_Heavy",
    "BallistaMultiShotEnergized": "Arrow_Medium",
    "BuggyPlasmaGrenade": "Plasma_Light",
    "BoxerCannonAG": "Bullet_Medium",
    "CabalBeholderLaser": "Laser_Heavy",
    "CabalArtilleryWalkerShellUpgraded": "CannonHE_Heavy",
    "CabalCommandoPlasmaMk2Neutron": "Plasma_Heavy",
    "CabalCommandoPlasmaNeutron": "Plasma_Heavy",
    "CabalMothershipRockets": "MissileTesla_Heavy",
    "ConsortiumMissileSystem": "MissileAA_Medium",
    "CryoLegionnaireAttack": "Cryo_Light",
    # DuelistTankCannon is intentionally left out: the maintainer already accepted
    # its versatile mixed profile as-is, so it needs a bespoke preservation split.
    "FutureTankCannons": "CannonHE_Heavy",
    "FutureHarbingerCannon": "Plasma_Heavy",
    "Future_Cryocopter_Cryo": "Cryo_Medium",
    "Future_MultiMissile_Sigma": "MissileTesla_Medium",
    "GladiusCannon": "Plasma_Heavy",
    "GradHeavyRockets": "MissileHE_Heavy",
    "GrenadeThermobaric": "Thermobaric_Light",
    "HeavyAATankCannonAG": "Bullet_Medium",
    "HovercraftCannon": "Bullet_Medium",
    "HovercraftPlasmaCannon": "Plasma_Medium",
    "JapanMaidenBowEnergized": "Arrow_Light",
    "KamovMissilesTesla": "MissileTesla_Medium",
    "IxianBomb_EMP": "Demolition_Heavy",
    "LatinSmokerCannon": "CannonHE_Medium",
    "LunarTigerCannon": "CannonHE_Medium",
    "MammothTuskTesla": "MissileTesla_Heavy",
    "MonsterTankTuskTesla": "MissileTesla_Heavy",
    "NaxMausCannon": "CannonHE_Heavy",
    "NaxRatteCannon": "CannonHE_Heavy",
    "NaxiShrek": "MissileAP_Medium",
    "NaxiShrekCons": "MissileAP_Medium",
    "NaxisBlackBombSmaller": "Demolition_Medium",
    "NanoSmokeAG": "Chemical_Medium",
    "OISmallPlasmaCannon": "Plasma_Medium",
    "ParaBombNuke": "Nuclear_Super",
    "PositronGrenade": "Quantum_Medium",
    "RA2120xmm": "CannonHE_Heavy",
    "RA2120xmm_rad": "CannonChem_Heavy",
    "RA2CosmonautLaser": "Laser_Light",
    "RA2FlakTrackGun": "Flak_Medium",
    "RA2FreedomAK47": "Bullet_Medium",
    "RA2FreedomRocket": "MissileAP_Medium",
    "RA2GrandCannonWeapon": "CannonHE_Heavy",
    "RA2HeavyMirageGun": "CannonAP_Light",
    "RA2LasherToxicMortar": "CannonChem_Medium",
    "RA2MirageGun": "CannonAP_Light",
    "RA2MortarBike": "CannonHE_Medium",
    "RA2SCUD_rad": "MissileChem_Heavy",
    "RA2Virusgun": "Sniper_Light",
    "RocketAngelRockets": "MissileAA_Light",
    "ShotgunAttackRobotGun": "Bullet_Light",
    "SiegeEngineCannon": "CannonHE_Heavy",
    "SiegeTankSiegeCannon": "CannonHE_Heavy",
    "SkyHawkArrowsEnergized": "Arrow_Medium",
    "SpecterArtilleryShellUpgrade": "CannonHE_Heavy",
    "StarshipSovereignBeam": "Laser_Heavy",
    "SteelKatyCannons_EMP": "Quantum_Medium",
    "SteelAirTurret": "Laser_Heavy",
    "SteelMakoGun_EMP": "Quantum_Medium",
    "SteelMegaSword": "Melee_Heavy",
    "SteelMegaSword_EMP": "Quantum_Heavy",
    "SteelQuantumTurretRail": "Quantum_Heavy",
    "SteelStalkerRailgun": "Railgun_Heavy",
    "TSChem120mmx": "CannonChem_Heavy",
    "TSRPGTowerRail": "Railgun_Heavy",
    "TSTurretLaserFire": "Laser_Medium",
    "Tentacle": "Melee_Heavy",
    "TurretGunBlackMarket": "Concussion_Medium",
    "Type89PlasmaCannon": "Plasma_Medium",
    "VoidRayBeam": "Prism_Heavy",
    "VultureGrenade": "Demolition_Light",
    "VolkovMagneticWeapon": "Railgun_Heavy",
    "VolkovMagneticWeaponIncendiaryNuclearShells": "CannonNuke_Heavy",
    "VolkovMagneticWeaponIncendiaryTesla": "Quantum_Heavy",
    "WaveforceCannonDistortedBeam1": "Waveforce_Heavy",
    "bfg10kCannon": "Plasma_Heavy",
    "edenRailgun": "Railgun_Heavy",
    "ixian_farasha": "Laser_Medium",
    "ra1_allies_chronovortex": "Magic_Heavy",
    "ra2roktgun": "Bullet_Medium",
    "wc2gryphonFireVisible": "MissileTesla_Medium",
    "YakNuclearBomb": "Nuclear_Super",
}

# These weapons intentionally combine several damage identities or act as broad
# inheritance hubs.  Forcing them into one canonical family would invent a balance
# ruling.  Instead, retain each resolved flat slice under a neutral compatibility
# key while leaving the percentage/status/projectile/effect layers untouched.
EXACT_PRESERVE = {
    "AsianPhotonCannon",
    "AsianSinglePlasma",
    "DuelistTankCannon",
    "MedicFlare",
    "PhotonCannon",
    "Rammax_Sabot",
    "SamuraiBladeCharged",
    "SteelInfRailgun_EMP",
    "SteelRunnerPistols",
    "YakTeslaBomb",
}

# Descendants whose role differs from the parent flat slice.  Unlisted descendants
# use the parent's reviewed role.  Already-consolidated children are detected from
# their local roleflat inherit and only mask the newly inherited parent slice.
CHILD_ROLE = {
    "AsianSpitfireRockets": "MissileAA_Medium",
    "BCYamatoCannon": "Plasma_Heavy",
    "BoxerCannon_AA": "Flak_Medium",
    "ConsortiumMissileSystem_EMP": "MissileQuantum_Medium",
    "HeavyAATankCannon_AA": "Flak_Medium",
    "RA2120xmm_rad": "CannonChem_Heavy",
    "RA2CosmonautLaser": "Laser_Light",
    "SteelAirTurret_EMP": "Quantum_Heavy",
    "SteelAirTurret_elite": "Quantum_Heavy",
    "SteelAirTurretEScatter": "Quantum_Heavy",
    "SteelStalkerRailgun_EMP": "Quantum_Heavy",
    "SteelStalkerRailgun_elite": "Quantum_Heavy",
    "SteelStalkerRailgunEScatter": "Quantum_Heavy",
    "VolkovMagneticWeaponIncendiaryNuclearShells": "CannonNuke_Heavy",
    "VolkovMagneticWeaponIncendiaryTesla": "Quantum_Heavy",
}

# Reviewed totals for roots whose already-consolidated ancestor contributes a
# separate canonical flat slice.  The remaining retired slices must be measured
# against the complete resolved baseline, not only the root's own old families.
COMPATIBILITY_TOTAL_OVERRIDE = {
    "HovercraftPlasmaCannon": 19000,
    "RA2120xmm_rad": 12000,
    "RA2CosmonautLaser": 11600,
    "VolkovMagneticWeaponIncendiaryNuclearShells": 60000,
    "VolkovMagneticWeaponIncendiaryTesla": 16000,
}

# These weapons already carry deliberate fixed ApplyPhysicalState warheads.  Do
# not add the canonical family's damage-scaled state a second time.
STRIP_COMPATIBILITY_PHYSICAL_STATE = {
    "CryoLegionnaireAttack",
    "Future_Cryocopter_Cryo",
    "StarshipSovereignBeam",
}

MANUAL_ROOTS = {"RA2CRM60H", "HueyFireMissiles"}


def walk(node: Node):
    yield node
    for child in node.children:
        yield from walk(child)


def verify_manual_steps(rs: Ruleset) -> None:
    """Verify the two reviewed operations that sit outside the generic mapper."""
    if rs.weapon("HueyFireMissiles") is not None:
        raise RuntimeError("HueyFireMissiles: orphan definition has not been removed")
    for collection in (rs.actors, rs.weapons):
        for root in collection.values():
            if any(node.value.strip() == "HueyFireMissiles" for node in walk(root)):
                raise RuntimeError(f"HueyFireMissiles: still referenced by {root.key}")

    local = rs.weapon("RA2CRM60H")
    resolved = rs.resolve_weapon("RA2CRM60H")
    if local is None or resolved is None:
        raise RuntimeError("RA2CRM60H: reviewed weapon is missing")
    local_keys = {child.key for child in local.children}
    required = {"-Warhead@SniperWeapon", "Warhead@Bullet_MediumFlatCompatibility"}
    if not required <= local_keys:
        raise RuntimeError("RA2CRM60H: reviewed point-damage collapse is incomplete")
    if any(child.key == "Warhead@SniperWeapon" and child.value in FLAT_TYPES
           for child in resolved.children):
        raise RuntimeError("RA2CRM60H: sniper splash main still resolves")
    if not any(child.key == "Warhead@SniperWeaponPercentage"
               for child in resolved.children):
        raise RuntimeError("RA2CRM60H: independently rounded percentage slice was lost")


def block_bounds(lines: list[str], name: str) -> tuple[int, int]:
    header = re.compile(rf"^{re.escape(name)}:\s*$")
    starts = [i for i, line in enumerate(lines) if header.match(line.rstrip("\r\n"))]
    if len(starts) != 1:
        raise RuntimeError(f"expected one source block for {name}, found {len(starts)}")
    start = starts[0]
    end = len(lines)
    for i in range(start + 1, len(lines)):
        raw = lines[i].rstrip("\r\n")
        if raw and not raw[0].isspace() and re.match(r"^[^:#]+:\s*$", raw):
            end = i
            break
    return start, end


def emit_node(node: Node, indent: int = 0, key: str | None = None,
              overrides: dict[str, str] | None = None) -> list[str]:
    """Serialize a resolved MiniYAML node, overriding direct scalar children."""
    overrides = overrides or {}
    prefix = "\t" * indent
    line = f"{prefix}{key or node.key}:"
    if node.value:
        line += f" {node.value}"
    out = [line + "\n"]
    seen = set()
    for child in node.children:
        if child.key in overrides:
            out.append(f"{prefix}\t{child.key}: {overrides[child.key]}\n")
            seen.add(child.key)
        else:
            out.extend(emit_node(child, indent + 1))
    for child_key, value in overrides.items():
        if child_key not in seen:
            out.append(f"{prefix}\t{child_key}: {value}\n")
    return out


def positive_flat_keys(rs: Ruleset, family: str) -> set[str]:
    node = rs.resolve_weapon(family)
    if node is None:
        raise RuntimeError(f"missing retired family {family}")
    keys = set()
    for child in node.children:
        if not child.key.startswith("Warhead@") or child.value not in FLAT_TYPES:
            continue
        try:
            damage = int(str(child.get("Damage") or "0"))
        except ValueError:
            continue
        if damage > 0:
            keys.add(child.key.split("@", 1)[1])
    return keys


def add_compatibility_templates(changed: dict[pathlib.Path, list[str]], rs: Ruleset,
                                destinations: set[str],
                                header: list[str] | None = None) -> None:
    path = ROOT / "mods/cameo/weapons/weapons.yaml"
    lines = changed.setdefault(path, path.read_text(encoding="utf-8-sig").splitlines(True))
    payload = []
    for destination in sorted(destinations):
        compatibility = f"^Compatibility_{destination}Flat"
        if rs.weapon(compatibility) is not None:
            continue
        source_template = rs.resolve_weapon(f"^Warhead_{destination}")
        if source_template is None:
            raise RuntimeError(f"missing destination family ^Warhead_{destination}")
        source_key = f"Warhead@{destination}"
        source = next((child for child in source_template.children
                       if child.key == source_key), None)
        if source is None:
            raise RuntimeError(f"{destination}: family lacks {source_key}")
        payload.extend([
            "\n",
            f"{compatibility}:\n",
        ])
        payload.extend(emit_node(
            source, 1, f"Warhead@{destination}FlatCompatibility",
            {"Damage": "0", "PercentageScale": "0"}))
    if payload:
        if lines and lines[-1].strip():
            lines.append("\n")
        lines.extend(header or [
            "# Percentage-inert flat compatibility profiles for the final reviewed\n",
            "# retired-family consolidation. Percentage applications stay on their\n",
            "# legacy nodes to preserve shipped per-node rounding and overflow.\n",
        ])
        lines.extend(payload)


def resolved_flat_total(node: Node, keys: set[str]) -> int:
    total = 0
    for child in node.children:
        if (not child.key.startswith("Warhead@") or child.value not in FLAT_TYPES
                or child.key.split("@", 1)[1] not in keys
                or child.key.endswith("FriendlyFire")):
            continue
        try:
            total += int(str(child.get("Damage") or "0"))
        except ValueError:
            pass
    return total


def resolved_flat_nodes(node: Node, keys: set[str]) -> dict[str, Node]:
    return {
        child.key.split("@", 1)[1]: child
        for child in node.children
        if child.key.startswith("Warhead@")
        and child.value in FLAT_TYPES
        and child.key.split("@", 1)[1] in keys
    }


def comparable_node(node: Node) -> tuple[str, ...]:
    return tuple(emit_node(node, key="Warhead@PreservedFlat"))


def apply_exact_preservation_block(
        changed: dict[pathlib.Path, list[str]], path: pathlib.Path, weapon: str,
        old_keys: set[str], replacements: dict[str, Node],
        inherited_tags: set[str] | None = None,
        remove_retired: bool = True) -> None:
    """Replace retired flat keys with byte-equivalent resolved local slices."""
    lines = changed.setdefault(path, path.read_text(encoding="utf-8-sig").splitlines(True))
    start, end = block_bounds(lines, weapon)
    if any("Warhead@PreservedFlat_" in line for line in lines[start + 1:end]):
        raise RuntimeError(f"{weapon}: exact-preservation bridge already exists")

    existing_removals = {
        match.group(1)
        for i in range(start + 1, end)
        if (match := re.match(r"^\t-Warhead@([^:]+):", lines[i]))
    }
    insertion = end
    while insertion > start + 1 and not lines[insertion - 1].strip():
        insertion -= 1

    payload = ([f"\t-Warhead@{key}:\n" for key in sorted(old_keys)
                if key not in existing_removals]
               if remove_retired else [])
    for tag in sorted(set(inherited_tags or ()) - set(replacements)):
        payload.append(f"\t-Warhead@PreservedFlat_{tag}:\n")
    for tag, node in sorted(replacements.items()):
        payload.extend(emit_node(node, 1, f"Warhead@PreservedFlat_{tag}"))
    lines[insertion:insertion] = payload


def apply_compatibility_block(changed: dict[pathlib.Path, list[str]], path: pathlib.Path,
                              weapon: str, destination: str, removals: set[str],
                              total: int, targets: str,
                              extra_removals: set[str] | None = None,
                              inherit_template: bool = True) -> None:
    targets = targets.strip()
    if not targets or targets == "*":
        raise RuntimeError(f"{weapon}: compatibility target mask is empty")
    lines = changed.setdefault(path, path.read_text(encoding="utf-8-sig").splitlines(True))
    start, end = block_bounds(lines, weapon)
    template = f"^Compatibility_{destination}Flat"
    if total > 0 and inherit_template:
        inherit_present = any(
            re.match(r"^\tInherits(?:@[^:]+)?:\s*" + re.escape(template) + r"\s*$",
                     lines[i].rstrip("\r\n"))
            for i in range(start + 1, end)
        )
        if not inherit_present:
            lines.insert(start + 1, f"\tInherits@roleflat: {template}\n")
            end += 1

    all_removals = set(removals) | set(extra_removals or ())
    existing_removals = {
        match.group(1)
        for i in range(start + 1, end)
        if (match := re.match(r"^\t-Warhead@([^:]+):", lines[i]))
    }
    insertion = end
    while insertion > start + 1 and not lines[insertion - 1].strip():
        insertion -= 1
    removal_lines = [f"\t-Warhead@{key}:\n" for key in sorted(all_removals)
                     if key not in existing_removals]
    lines[insertion:insertion] = removal_lines
    insertion += len(removal_lines)
    if total > 0:
        selected_key = f"{destination}FlatCompatibility"
        compatibility_lines = [
            f"\tWarhead@{selected_key}:\n",
            f"\t\tValidTargets: {targets}\n",
            f"\t\tDamage: {total}\n",
            "\t\tPercentageScale: 0\n",
        ]
        if weapon in STRIP_COMPATIBILITY_PHYSICAL_STATE:
            compatibility_lines.extend([
                "\t\t-PhysicalStateName:\n",
                "\t\t-PhysicalStateScale:\n",
            ])
        lines[insertion:insertion] = compatibility_lines
    changed[path] = lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rs = Ruleset(ROOT)
    verify_manual_steps(rs)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    rows = {row["weapon"]: row for row in report["weapons"]}
    active_roles = set(ROLE) & set(rows)
    active_exact = EXACT_PRESERVE & set(rows)
    if not active_roles and not active_exact:
        print("No mapped roots remain in the refreshed survey")
        return 0

    changed: dict[pathlib.Path, list[str]] = {}
    required_destinations = {ROLE[weapon] for weapon in active_roles}
    for weapon in active_roles:
        for child in rows[weapon]["descendant_old_flat_overrides"]:
            required_destinations.add(CHILD_ROLE.get(child["weapon"], ROLE[weapon]))
    add_compatibility_templates(changed, rs, required_destinations)

    parent_compat_removals: dict[str, set[str]] = {}
    for parent in active_roles:
        parent_key = f"{ROLE[parent]}FlatCompatibility"
        for child in rows[parent]["descendant_old_flat_overrides"]:
            child_name = child["weapon"]
            if child_name in active_roles and CHILD_ROLE.get(child_name, ROLE[parent]) != ROLE[parent]:
                parent_compat_removals.setdefault(child_name, set()).add(parent_key)

    summary = []
    for weapon in sorted(active_roles):
        destination = ROLE[weapon]
        row = rows[weapon]
        old_keys = set().union(*(positive_flat_keys(rs, family)
                                 for family in row["old_families"]))
        flats = [hit for hit in row["flat_hits"]
                 if hit["type"] in FLAT_TYPES and hit["tag"] in old_keys]
        total = sum(int(hit["damage"]) for hit in flats
                    if not hit["tag"].endswith("FriendlyFire"))
        if weapon in COMPATIBILITY_TOTAL_OVERRIDE:
            resolved = rs.resolve_weapon(weapon)
            if resolved is None:
                raise RuntimeError(f"{weapon}: cannot validate compatibility total")
            baseline_retired_total = resolved_flat_total(resolved, old_keys)
            override = COMPATIBILITY_TOTAL_OVERRIDE[weapon]
            if override != baseline_retired_total:
                raise RuntimeError(
                    f"{weapon}: compatibility total {override} does not match "
                    f"resolved retired slice total {baseline_retired_total}")
            total = override
        if total <= 0:
            raise RuntimeError(f"{weapon}: no positive ordinary flat damage")

        root_targets = str(row["valid_targets"]).strip()
        if not root_targets or root_targets == "*":
            hit_targets = {str(hit["targets"]).strip() for hit in flats
                           if str(hit["targets"]).strip()}
            if len(hit_targets) != 1:
                raise RuntimeError(
                    f"{weapon}: flat slices have incompatible target masks {sorted(hit_targets)}")
            root_targets = hit_targets.pop()

        apply_compatibility_block(
            changed, ROOT / row["file"], weapon, destination, old_keys, total,
            root_targets, parent_compat_removals.get(weapon))

        parent_key = f"{destination}FlatCompatibility"
        repaired_children = 0
        for child_info in row["descendant_old_flat_overrides"]:
            child_name = child_info["weapon"]
            if child_name in active_roles:
                continue
            child_local = rs.weapon(child_name)
            child_node = rs.resolve_weapon(child_name)
            if child_local is None or child_node is None:
                raise RuntimeError(f"{weapon}: missing descendant {child_name}")
            child_role = CHILD_ROLE.get(child_name, destination)
            child_total = resolved_flat_total(child_node, old_keys)
            child_has_own_role = any(
                child.key.startswith("Inherits@roleflat")
                for child in child_local.children)
            extra = {parent_key} if child_role != destination or child_has_own_role else set()
            if child_has_own_role:
                child_total = 0
            # The converted parent already removes inherited legacy slices.
            # Only remove keys that the child reintroduces locally; requesting
            # removal of an already-absent inherited key is a runtime MiniYAML
            # error even though the audit resolver tolerates it.
            child_removals = set(child_info["keys"])
            apply_compatibility_block(
                changed, ROOT / child_local.file, child_name, child_role,
                child_removals,
                child_total, child_node.get("ValidTargets") or row["valid_targets"], extra,
                inherit_template=child_role != destination)
            repaired_children += 1
        summary.append((weapon, destination, f"{len(flats)} slices -> {total}"))
        if repaired_children:
            summary.append((weapon, destination, f"repaired {repaired_children} descendants"))

    for weapon in sorted(active_exact):
        row = rows[weapon]
        old_keys = set().union(*(positive_flat_keys(rs, family)
                                 for family in row["old_families"]))
        root_local = rs.weapon(weapon)
        root_node = rs.resolve_weapon(weapon)
        if root_local is None or root_node is None:
            raise RuntimeError(f"missing exceptional root {weapon}")
        root_flats = resolved_flat_nodes(root_node, old_keys)
        if not root_flats:
            raise RuntimeError(f"{weapon}: no retired flat slices to preserve")
        apply_exact_preservation_block(
            changed, ROOT / root_local.file, weapon, old_keys, root_flats)

        repaired_descendants = 0
        root_fingerprints = {tag: comparable_node(node)
                             for tag, node in root_flats.items()}
        override_names = {entry["weapon"]
                          for entry in row["descendant_old_flat_overrides"]}
        for child_name in row["descendants"]:
            child_local = rs.weapon(child_name)
            child_node = rs.resolve_weapon(child_name)
            if child_local is None or child_node is None:
                raise RuntimeError(f"{weapon}: missing descendant {child_name}")
            child_flats = resolved_flat_nodes(child_node, old_keys)
            child_fingerprints = {tag: comparable_node(node)
                                  for tag, node in child_flats.items()}
            child_has_own_role = any(
                child.key.startswith("Inherits@roleflat")
                for child in child_local.children)
            if (child_name not in override_names and not child_has_own_role
                    and child_fingerprints == root_fingerprints):
                continue
            apply_exact_preservation_block(
                changed, ROOT / child_local.file, child_name, old_keys, child_flats,
                set(root_flats), remove_retired=False)
            repaired_descendants += 1
        summary.append((weapon, "exact compatibility", f"preserved {len(root_flats)} slices"))
        if repaired_descendants:
            summary.append((weapon, "exact compatibility",
                            f"repaired {repaired_descendants} descendants"))

    for weapon, destination, result in summary:
        print(f"{weapon}: {destination}: {result}")
    if args.apply:
        for path, lines in changed.items():
            path.write_text("".join(lines), encoding="utf-8", newline="\n")
        print(f"APPLIED {len(active_roles) + len(active_exact)} roots "
              f"across {len(changed)} files")
    else:
        print("DRY RUN; pass --apply to write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
