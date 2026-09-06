#!/usr/bin/env python3
"""Consolidate the final large legacy-energy families for the below-300 goal."""
from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from audit_three_way_split import main_warheads  # noqa: E402
from consolidate_corroborated_role_profiles import (  # noqa: E402
    remove_local_compatibility_removal,
    set_state_scale,
    update_existing_compatibility,
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
)
from consolidate_rule_driven_blast_ordnance import (  # noqa: E402
    isolate_legacy_root,
    set_state_name,
    weighted_state_plan,
)
from consolidate_rule_driven_energy_ordnance import (  # noqa: E402
    add_percentage_companions,
    digest,
    remove_batch_parent_percentage_companions,
)
from miniyaml import Ruleset  # noqa: E402
import percentage_damage as pd  # noqa: E402


DESTINATIONS = {
    # Asian Alliance route-specific energy closure (14).
    "AsianPhotonCannon": "Plasma_Heavy",
    "AsianPhotonCannon_EMP": "Quantum_Heavy",
    "AsianMaidenBow": "Arrow_Light",
    "AsianMaidenBow_elite": "Arrow_Light",
    "AsianPunisherAG": "MissileAP_Medium",
    "AsianPunisherAG_EMP": "MissileQuantum_Medium",
    "AsianQuasarAG": "Plasma_Heavy",
    "AsianQuasarAG_EMP": "Quantum_Heavy",
    "AsianQuasarBoatAG": "Plasma_Heavy",
    "AsianQuasarBoatAG_EMP": "Quantum_Heavy",
    "AsianQuasarBoat_AA": "MissileAA_Medium",
    "AsianQuasarBoat_EMP_AA": "MissileQuantum_Medium",
    "AsianQuasar_AA": "MissileAA_Medium",
    "AsianQuasar_EMP_AA": "MissileQuantum_Medium",
    # Lunar/Naxis 105 mm closure (10).
    "Lunar_Green105mm": "Tesla_Heavy",
    "Lunar_Green105mm_elite": "Tesla_Heavy",
    "Lunar_AmplifiedUbermenschLaser": "Laser_Heavy",
    "Lunar_AmplifiedUbermenschLaser_elite": "Laser_Heavy",
    "Lunar_YellowUbermenschLaser": "Laser_Heavy",
    "Lunar_YellowUbermenschLaser_elite": "Laser_Heavy",
    "NaxiAlienPistol": "Laser_Heavy",
    "NaxiAlienPistol_elite": "Laser_Heavy",
    "UbermenschLaser": "Laser_Heavy",
    "UbermenschLaser_elite": "Laser_Heavy",
    # Consortium runner closure (8).
    "SteelRunnerPistols": "Tesla_Heavy",
    "SteelRunnerPistols_elite": "Tesla_Heavy",
    "SteelRunnerPistolsResonance": "Tesla_Heavy",
    "SteelRunnerPistolsResonance_elite": "Tesla_Heavy",
    "SteelRunnerPistolsResonanceBounce1": "Tesla_Heavy",
    "SteelRunnerPistolsResonanceBounce1_elite": "Tesla_Heavy",
    "SteelRunnerPistolsResonanceBounce2": "Tesla_Heavy",
    "SteelRunnerPistolsResonanceBounce2_elite": "Tesla_Heavy",
    # Naxis MP40 laser closure (6).
    "NaxiMP40Laser": "Laser_Heavy",
    "NaxiMP40Laser_elite": "Laser_Heavy",
    "Lunar_AmplifiedMP40Laser": "Laser_Heavy",
    "Lunar_AmplifiedMP40Laser_elite": "Laser_Heavy",
    "Lunar_YellowMP40Laser": "Laser_Heavy",
    "Lunar_YellowMP40Laser_elite": "Laser_Heavy",
    # Steel railgun/EMP closure (6).
    "SteelInfRailgun": "Railgun_Heavy",
    "SteelInfRailgun_elite": "Railgun_Heavy",
    "SteelInfRailgun_EMP": "Quantum_Heavy",
    "SteelInfRailgun_EMP_elite": "Quantum_Heavy",
    "SteelScalpelRailgunAA": "Flak_Medium",
    # The paid EMP replacement remains an AA weapon. Keep the Flak profile so
    # it cannot regress against Fighters while retaining its EMP payload.
    "SteelScalpelRailgun_EMP_AA": "Flak_Medium",
    # Asian plasma closure (5).
    "AsianSinglePlasma": "Plasma_Heavy",
    "AsianSinglePlasma_elite": "Plasma_Heavy",
    "AsianTurretPlasma": "Plasma_Heavy",
    "AsianTwinPlasma": "Plasma_Heavy",
    "AsianTwinPlasma_elite": "Plasma_Heavy",
    # Seven complete four-definition families (28).
    "LunarNaxiJadgDestroyer": "CannonAP_Light",
    "LunarNaxiJadgDestroyer_elite": "CannonAP_Light",
    "Lunar_GreenJadgDestroyer": "Tesla_Heavy",
    "Lunar_GreenJadgDestroyer_elite": "Tesla_Heavy",
    "MutaliskSpore": "Chemical_Medium",
    "MutaBounce1": "Chemical_Medium",
    "MutaBounce2": "Chemical_Medium",
    "SCDevourerAA": "Chemical_Medium",
    "PhotonCannon": "Plasma_Heavy",
    "ArbiterCannon": "Plasma_Heavy",
    "DragoonCannon": "Plasma_Heavy",
    "GladiusCannon": "Plasma_Heavy",
    "SkyHawkArrows": "Arrow_Light",
    "ZeroFighterArrows": "Arrow_Light",
    "SkyHawkArrowsEnergized": "Arrow_Medium",
    "ZeroFighterArrowsEnergized": "Arrow_Medium",
    "SteelKatyCannons": "CannonFire_Heavy",
    "SteelKatyCannons_elite": "CannonFire_Heavy",
    "SteelKatyCannons_EMP": "Quantum_Medium",
    "SteelKatyCannons_EMP_elite": "Quantum_Medium",
    "SteelMakoGun": "Railgun_Heavy",
    "SteelMakoGun_elite": "Railgun_Heavy",
    "SteelMakoGun_EMP": "Quantum_Medium",
    "SteelMakoGun_EMP_elite": "Quantum_Medium",
    "SteelQuantumCannon": "Quantum_Heavy",
    "SteelQuantumCannon_elite": "Quantum_Heavy",
    "SteelQuantumCannonScatter_elite": "Quantum_Heavy",
    "SteelQuantumCannon_EMP": "Quantum_Heavy",
}

SOURCES = {
    **{name: "PreservedFlat_MagicWeapon" for name in (
        "AsianPhotonCannon", "AsianQuasarAG", "AsianQuasarBoatAG")},
    **{name: "PreservedFlat_TeslaWeapon" for name in (
        "AsianPhotonCannon_EMP", "AsianQuasarAG_EMP", "AsianQuasarBoatAG_EMP")},
    "AsianMaidenBow": "Arrow_LightFlatCompatibility",
    "AsianMaidenBow_elite": "Arrow_LightFlatCompatibility",
    "AsianPunisherAG": "PreservedFlat_MediumMissile",
    "AsianPunisherAG_EMP": "PreservedFlat_MediumMissile",
    "AsianQuasarBoat_AA": "PreservedFlat_FlakWeapon",
    "AsianQuasarBoat_EMP_AA": "PreservedFlat_FlakWeapon",
    "AsianQuasar_AA": "PreservedFlat_FlakWeapon",
    "AsianQuasar_EMP_AA": "PreservedFlat_FlakWeapon",
    **{name: "Tesla_Heavy" for name in (
        "Lunar_AmplifiedUbermenschLaser", "Lunar_AmplifiedUbermenschLaser_elite",
        "Lunar_YellowUbermenschLaser", "Lunar_YellowUbermenschLaser_elite",
        "NaxiAlienPistol", "NaxiAlienPistol_elite", "UbermenschLaser",
        "UbermenschLaser_elite")},
    **{name: "PreservedFlat_TeslaWeapon" for name in (
        "SteelRunnerPistols", "SteelRunnerPistols_elite",
        "SteelRunnerPistolsResonance", "SteelRunnerPistolsResonance_elite",
        "SteelRunnerPistolsResonanceBounce1",
        "SteelRunnerPistolsResonanceBounce1_elite",
        "SteelRunnerPistolsResonanceBounce2",
        "SteelRunnerPistolsResonanceBounce2_elite")},
    "SteelInfRailgun_EMP": "Railgun_Heavy",
    "SteelInfRailgun_EMP_elite": "Railgun_Heavy",
    "SteelScalpelRailgun_EMP_AA": "Flak_Medium",
    **{name: "CannonHE_Heavy" for name in (
        "AsianSinglePlasma", "AsianSinglePlasma_elite", "AsianTurretPlasma",
        "AsianTwinPlasma", "AsianTwinPlasma_elite")},
    "Lunar_GreenJadgDestroyer": "Tesla_Heavy",
    "Lunar_GreenJadgDestroyer_elite": "Tesla_Heavy",
    "PhotonCannon": "PreservedFlat_MediumCannon",
    "ArbiterCannon": "PreservedFlat_MediumCannon",
    "DragoonCannon": "PreservedFlat_MediumCannon",
    "GladiusCannon": "Plasma_HeavyFlatCompatibility",
    "SkyHawkArrowsEnergized": "Arrow_MediumFlatCompatibility",
    "ZeroFighterArrowsEnergized": "Arrow_MediumFlatCompatibility",
    "SteelKatyCannons": "Flame_Heavy",
    "SteelKatyCannons_elite": "Flame_Heavy",
    "SteelKatyCannons_EMP": "Quantum_MediumFlatCompatibility",
    "SteelKatyCannons_EMP_elite": "Quantum_MediumFlatCompatibility",
    "SteelMakoGun_EMP": "Quantum_MediumFlatCompatibility",
    "SteelMakoGun_EMP_elite": "Quantum_MediumFlatCompatibility",
    "SteelQuantumCannon": "Railgun_Heavy",
    "SteelQuantumCannon_elite": "Railgun_Heavy",
    "SteelQuantumCannonScatter_elite": "Railgun_Heavy",
    "SteelQuantumCannon_EMP": "Railgun_Heavy",
}

# These definitions intentionally adopt the destination family's state rather
# than migrating a contradictory legacy state from the flattened stack.
USE_DESTINATION_STATE = {
    name for name, destination in DESTINATIONS.items()
    if destination in {
        "Plasma_Heavy", "Quantum_Heavy", "Quantum_Medium",
        "MissileQuantum_Medium", "MissileAA_Medium", "CannonFire_Heavy",
    }
} | {
    "Lunar_AmplifiedUbermenschLaser", "Lunar_AmplifiedUbermenschLaser_elite",
    "Lunar_YellowUbermenschLaser", "Lunar_YellowUbermenschLaser_elite",
    "NaxiAlienPistol", "NaxiAlienPistol_elite", "UbermenschLaser",
    "UbermenschLaser_elite", "SteelRunnerPistols", "SteelRunnerPistols_elite",
    "SteelRunnerPistolsResonance", "SteelRunnerPistolsResonance_elite",
    "SteelRunnerPistolsResonanceBounce1", "SteelRunnerPistolsResonanceBounce1_elite",
    "SteelRunnerPistolsResonanceBounce2", "SteelRunnerPistolsResonanceBounce2_elite",
    "SteelScalpelRailgun_EMP_AA",
}

EXPECTED_COUNT = 77
BASELINE_DIGEST = "0a9981a377cf2a014f4bb2f8c81c8ba101967e35b9c78c9ede48132510d3c66c"


def baseline_rows(rs: Ruleset):
    rows = {}
    for name, destination in sorted(DESTINATIONS.items()):
        resolved = rs.resolve_weapon(name)
        mains = set(main_warheads(resolved))
        compatibility = f"{destination}FlatCompatibility"
        if mains == {compatibility}:
            rows[name] = None
            continue
        source = SOURCES.get(name, destination)
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
            "state": (None if name in USE_DESTINATION_STATE
                      else weighted_state_plan(nodes, total)),
        }
    return rows


def apply_changes(rs: Ruleset, rows) -> None:
    changed: dict[pathlib.Path, list[str]] = {}
    isolate_legacy_root(
        changed, rs, "PhotonCannon", "^PhotonCannonLegacy", {"IdolCannon"})
    add_compatibility_templates(changed, rs, set(DESTINATIONS.values()))
    for name, destination in sorted(DESTINATIONS.items()):
        plan = rows[name]
        local = rs.weapon(name)
        path = pathlib.Path(local.file)
        resolved = rs.resolve_weapon(name)
        remove_batch_parent_percentage_companions(
            changed, path, name, rs, rows)
        add_percentage_companions(changed, path, name, resolved, plan)
        remove_local_compatibility_removal(changed, path, name, destination)
        ensure_template_inherit(changed, path, name, destination)
        compatibility = f"{destination}FlatCompatibility"
        local_has_compatibility = any(
            child.key == f"Warhead@{compatibility}" for child in local.children)
        parent_removals = {
            f"{DESTINATIONS[parent]}FlatCompatibility"
            for _key, parent in rs.inherits_of(local)
            if parent in DESTINATIONS and DESTINATIONS[parent] != destination
        }
        apply_compatibility_block(
            changed, path, name, destination,
            set(plan["mains"]) - {compatibility},
            0 if local_has_compatibility else plan["total"], plan["targets"],
            extra_removals=parent_removals,
            inherit_template=False)
        if local_has_compatibility:
            update_existing_compatibility(
                changed, path, name, destination, plan["total"],
                plan["percentage_scale"], plan["targets"])
        else:
            set_scale(changed, path, name, destination, plan["percentage_scale"])
        if plan["state"] is not None:
            state, scale = plan["state"]
            set_state_name(changed, path, name, destination, state)
            set_state_scale(changed, path, name, destination, scale)
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")
    cleanup_stale_removals(set(DESTINATIONS))
    cleanup_duplicate_template_inherits(set(DESTINATIONS))


def validate_result() -> None:
    rs = Ruleset(ROOT)
    for name, destination in sorted(DESTINATIONS.items()):
        mains = set(main_warheads(rs.resolve_weapon(name)))
        expected = {f"{destination}FlatCompatibility"}
        if mains != expected:
            raise RuntimeError(f"{name}: expected {sorted(expected)}; found {sorted(mains)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if len(DESTINATIONS) != EXPECTED_COUNT:
        raise RuntimeError(f"expected {EXPECTED_COUNT}, found {len(DESTINATIONS)}")
    rs = Ruleset(ROOT)
    rows = baseline_rows(rs)
    states = {row is None for row in rows.values()}
    if states == {True}:
        validate_result()
        print(f"Already consolidated {len(DESTINATIONS)} definitions")
        return 0
    if len(states) != 1:
        raise RuntimeError("partial legacy-energy tranche detected")
    current_digest = digest(rows)
    print(f"{len(DESTINATIONS)} definitions; baseline digest {current_digest}")
    if BASELINE_DIGEST and current_digest != BASELINE_DIGEST:
        raise RuntimeError("baseline fingerprint changed")
    if not args.apply:
        print("Dry run: totals, routes, percentage arithmetic, and states pass")
        return 0
    if not BASELINE_DIGEST:
        raise RuntimeError("pin BASELINE_DIGEST before applying")
    apply_changes(rs, rows)
    validate_result()
    print(f"Applied and validated {len(DESTINATIONS)} definitions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
