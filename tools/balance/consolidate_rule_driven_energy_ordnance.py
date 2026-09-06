#!/usr/bin/env python3
"""Consolidate a reviewed energy, projectile, cannon, and bullet tranche.

This is an intentional role selection, not an equivalence rewrite.  Each
definition keeps its resolved flat total, delivery data, target route, and
percentage arithmetic while adopting one named canonical armor/blast profile.
Physical-state strength is damage-weighted onto the selected main.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from audit_three_way_split import main_warheads  # noqa: E402
from consolidate_final_safe_cohorts import (  # noqa: E402
    cleanup_duplicate_template_inherits,
    cleanup_stale_removals,
    ensure_template_inherit,
    flat_main_nodes,
    percentage_scale,
    set_scale,
)
from consolidate_corroborated_role_profiles import set_state_scale  # noqa: E402
from consolidate_reviewed_weapon_roots import (  # noqa: E402
    add_compatibility_templates,
    apply_compatibility_block,
    block_bounds,
    emit_node,
)
from miniyaml import Ruleset  # noqa: E402
import percentage_damage as pd  # noqa: E402
import effective_damage as ed  # noqa: E402


GROUPS = {
    "Tesla_Heavy": {
        "KamovTesla", "KamovTeslaArc", "KamovTeslaArcFragment1",
        "KamovTeslaArcFragment2", "YakTeslaGun", "YakTeslaGunArc",
        "YakTeslaArcFragment1", "YakTeslaArcFragment2", "TeslaMaverick",
        "TeslaMaverickFragment1", "TeslaMaverickFragment2",
    },
    "Railgun_Heavy": {
        "OrionRailgun", "OrionRailgun_elite", "TS120mmRail", "TS120mmTalRail",
    },
    "Laser_Heavy": {
        "schwarzermond_lunarsoldier_rifle",
        "schwarzermond_lunarsoldier_rifle_amplified",
        "schwarzermond_lunarsoldier_rifle_yellow",
        "schwarzermond_lunarsoldier_rifle_elite",
        "schwarzermond_lunarsoldier_rifle_amplified_elite",
        "schwarzermond_lunarsoldier_rifle_yellow_elite",
        "TSLaserTurretLaser", "TSTurretLaser", "TSCABALPlasmaFire",
        "ObeliskLaserFragment", "TurretLaserFragment", "CabalLegionGun",
        "CabalMantisGun", "TSLaserRaiderCannon", "RA2LasherLaser",
        "RA2LasherLaser_elite",
    },
    "MissileAP_Light": {
        "RA2HoverMissile", "RA2HoverMissile_elite", "RA2HoverMissile_AA",
        "RA2HoverMissile_AA_elite",
    },
    "MissileHE_Light": {
        "RA2MultiHoverMissile", "RA2MultiHoverMissile_elite",
        "RA2MultiHoverMissile_AA", "RA2MultiHoverMissile_AA_elite",
    },
    "MissileAP_Medium": {
        "MissileAttackRobotGun", "MissileAttackRobotGun_elite",
        "D2K_APC_Rocket", "D2K_APC_Rocket_AA", "ViperMissiles",
        "ViperMissilesCryo", "ViperMissilesTwin",
    },
    "MissileHE_Medium": {
        "CabalRocketCyborgRockets", "CabalRocketCyborgRocketsUpgraded",
        "TSBikeMissile", "CommandoRocketLauncher", "RocketsRA",
    },
    "MissileAP_Heavy": {
        "RocketsHumvee2AMT", "RocketsHumvee2AMT_AA", "NaxPlaneRockets_elite",
        "NaxInterceptorRockets", "D2K_Rocket_Trooper", "AsianPelicanMissile",
        "AsianPelicanMissile_elite", "AsianSmallTorpedo", "FutureMicrotorpedos",
        "RA2TorpTube", "RA2TorpTube_elite", "YRBoomerTorpedo",
    },
    "CannonAP_Light": {"NaxiJadgDestroyer", "NaxiJadgDestroyer_elite"},
    "CannonHE_Heavy": {
        "NaxBrummbarArty", "NaxBrummbarArty_elite", "RATurretGun",
        "TSRPGTower", "tkmtrenchcannon", "tkmtrenchdepcannon",
    },
    "Bullet_Medium": {
        "CabalCyborgChaingun", "RA220mmrapid", "TSDevoutChainguns", "TSSergGun",
    },
}

DESTINATION_OVERRIDES = {
    "D2K_APC_Rocket_AA": "MissileAA_Medium",
    "NaxInterceptorRockets": "MissileAA_Heavy",
    "RA2HoverMissile_AA": "MissileAA_Light",
    "RA2HoverMissile_AA_elite": "MissileAA_Light",
    "RA2MultiHoverMissile_AA": "MissileAA_Light",
    "RA2MultiHoverMissile_AA_elite": "MissileAA_Light",
    "RocketsHumvee2AMT_AA": "MissileAA_Heavy",
}
SOURCE_OVERRIDES = {
    "D2K_APC_Rocket_AA": "MissileAP_Medium",
    "NaxInterceptorRockets": "MissileAP_Heavy",
    "RA2HoverMissile_AA": "MissileAP_Light",
    "RA2HoverMissile_AA_elite": "MissileAP_Light",
    "RA2MultiHoverMissile_AA": "MissileHE_Light",
    "RA2MultiHoverMissile_AA_elite": "MissileHE_Light",
    "RocketsHumvee2AMT_AA": "MissileAP_Heavy",
}
SELECTED = {
    name: DESTINATION_OVERRIDES.get(name, destination)
    for destination, names in GROUPS.items() for name in names
}
BASE_DESTINATION = {
    name: destination for destination, names in GROUPS.items() for name in names
}
EXPECTED_COUNT = 75
BASELINE_DIGEST = "009d4f4d926026a9f2cecd415c53b09c0f94bb1f560e823d47868feaa30e8540"


def state_plan(nodes, total: int, destination: str):
    names = {
        str(node.get("PhysicalStateName"))
        for node in nodes.values() if node.get("PhysicalStateName")
    }
    if len(names) > 1:
        raise RuntimeError(f"mixed physical states: {sorted(names)}")
    if not names:
        return None
    state = next(iter(names))
    if nodes[destination].get("PhysicalStateName") != state:
        raise RuntimeError(
            f"{destination}: selected role does not carry inherited state {state}")
    weighted = 0
    for node in nodes.values():
        if node.get("PhysicalStateName") != state:
            continue
        damage = int(str(node.get("Damage") or 0))
        scale = int(str(node.get("PhysicalStateScale") or 100))
        weighted += damage * scale
    return state, math.ceil(weighted / total)


def baseline_rows(rs: Ruleset):
    rows = {}
    for name, destination in sorted(SELECTED.items()):
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            raise RuntimeError(f"{name}: missing weapon")
        mains = set(main_warheads(resolved))
        compatibility = f"{destination}FlatCompatibility"
        if mains == {compatibility}:
            rows[name] = None
            continue
        source = SOURCE_OVERRIDES.get(name, destination)
        if len(mains) < 2 or source not in mains:
            raise RuntimeError(
                f"{name}: expected stacked {destination} role; found {sorted(mains)}")
        nodes = flat_main_nodes(resolved, mains)
        if set(nodes) != mains:
            raise RuntimeError(f"{name}: non-flat selected main")
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
                        int(str(node.get("PercentageScale") or 0)),
                    )[1],
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
            "state": state_plan(nodes, total, source),
        }
    return rows


def digest(rows) -> str:
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def validate_selection() -> None:
    if len(SELECTED) != EXPECTED_COUNT:
        raise RuntimeError(f"expected {EXPECTED_COUNT} selections, found {len(SELECTED)}")
    duplicates = sum(len(names) for names in GROUPS.values()) - len(SELECTED)
    if duplicates:
        raise RuntimeError(f"selection has {duplicates} duplicate names")


def companion_lines(node, companion: str, spec) -> list[str]:
    """Translate one folded percentage route to an equivalent standalone hit."""
    omitted = {
        "Damage", "PercentageScale", "PercentageDenominator", "PercentageSpread",
        "PercentageVersus", "Versus", "Spread", "Falloff", "Range",
    }
    out = [f"\tWarhead@{companion}: AreaDamagePercentage\n"]
    for child in node.children:
        if child.key not in omitted:
            out.extend(emit_node(child, 2))
    out.extend([
        f"\t\tDamage: {spec['units']}\n",
        f"\t\tPercentageDenominator: {spec['denominator']}\n",
    ])
    percentage_versus = node.child("PercentageVersus")
    versus = (percentage_versus if percentage_versus is not None
              and percentage_versus.children else node.child("Versus"))
    if versus is not None:
        out.extend(emit_node(versus, 2, "Versus"))
    falloff, radii, _live = ed.falloff_and_radii(node)
    spread = int(str(node.get("PercentageSpread") or pd.DEFAULT_PERCENTAGE_SPREAD))
    clipped_falloff, clipped_radii = pd.clip_falloff(falloff, radii, spread)
    out.extend([
        "\t\tFalloff: " + ", ".join(str(int(round(v))) for v in clipped_falloff) + "\n",
        "\t\tRange: " + ", ".join(str(int(round(v))) for v in clipped_radii) + "\n",
    ])
    return out


def add_percentage_companions(changed, path: pathlib.Path, name: str,
                              resolved, plan) -> None:
    """Retain each source percentage route exactly as a zero-flat companion."""
    if not plan["percentage"]:
        return
    lines = changed.setdefault(
        path, path.read_text(encoding="utf-8-sig").splitlines(True))
    start, end = block_bounds(lines, name)
    insertion = end
    while insertion > start + 1 and not lines[insertion - 1].strip():
        insertion -= 1
    by_key = {
        child.key.split("@", 1)[1]: child for child in resolved.children
        if child.key.startswith("Warhead@")
    }
    payload = []
    for key, spec in plan["percentage"].items():
        # Include the concrete weapon name so parent and child companions
        # cannot merge through MiniYAML inheritance.
        companion = percentage_companion_name(name, key)
        if any(child.key == f"Warhead@{companion}" for child in resolved.children):
            raise RuntimeError(f"{name}: percentage companion {companion} exists")
        payload.extend(companion_lines(by_key[key], companion, spec))
    lines[insertion:insertion] = payload


def percentage_companion_name(name: str, key: str) -> str:
    weapon_tag = re.sub(r"[^A-Za-z0-9_]", "_", name)
    return f"Collapsed{weapon_tag}{key}Percentage"


def remove_batch_parent_percentage_companions(
        changed, path: pathlib.Path, name: str, rs: Ruleset, plans) -> None:
    """Remove companions generated on selected ancestors in this same batch.

    A selected child gets its own complete baseline-derived percentage plan. If
    it also inherits companions generated for a selected parent, those routes
    would be counted twice.
    """
    pending = [parent for _key, parent in rs.inherits_of(rs.weapon(name))]
    seen = set()
    companions = set()
    while pending:
        parent = pending.pop()
        if parent in seen:
            continue
        seen.add(parent)
        plan = plans.get(parent)
        if plan is not None:
            companions.update(
                percentage_companion_name(parent, key)
                for key in plan["percentage"])
        local = rs.weapon(parent)
        if local is not None:
            pending.extend(p for _key, p in rs.inherits_of(local))
    if not companions:
        return
    lines = changed.setdefault(
        path, path.read_text(encoding="utf-8-sig").splitlines(True))
    start, end = block_bounds(lines, name)
    insertion = end
    while insertion > start + 1 and not lines[insertion - 1].strip():
        insertion -= 1
    lines[insertion:insertion] = [
        f"\t-Warhead@{companion}:\n" for companion in sorted(companions)]


def isolate_viper_fire(changed, rs: Ruleset) -> None:
    """Keep the fire child on the exact pre-consolidation Viper payload."""
    local = rs.weapon("ViperMissiles")
    path = pathlib.Path(local.file)
    lines = changed.setdefault(
        path, path.read_text(encoding="utf-8-sig").splitlines(True))
    start, end = block_bounds(lines, "ViperMissiles")
    lines[start] = "^ViperMissilesLegacy:\n"
    lines[end:end] = [
        "ViperMissiles:\n",
        "\tInherits: ^ViperMissilesLegacy\n",
    ]
    start, end = block_bounds(lines, "ViperMissilesFire")
    matches = [i for i in range(start + 1, end)
               if lines[i].rstrip("\r\n") == "\tInherits: ViperMissiles"]
    if len(matches) != 1:
        raise RuntimeError("ViperMissilesFire inheritance fingerprint changed")
    lines[matches[0]] = "\tInherits: ^ViperMissilesLegacy\n"


def apply_changes(rs: Ruleset, rows) -> None:
    changed: dict[pathlib.Path, list[str]] = {}
    isolate_viper_fire(changed, rs)
    add_compatibility_templates(changed, rs, set(SELECTED.values()))
    for name in sorted(SELECTED):
        plan = rows[name]
        if plan is None:
            continue
        destination = plan["destination"]
        local = rs.weapon(name)
        if local is None:
            raise RuntimeError(f"{name}: missing local weapon")
        path = pathlib.Path(local.file)
        resolved = rs.resolve_weapon(name)
        remove_batch_parent_percentage_companions(
            changed, path, name, rs, rows)
        add_percentage_companions(changed, path, name, resolved, plan)
        ensure_template_inherit(changed, path, name, destination)
        apply_compatibility_block(
            changed, path, name, destination, set(plan["mains"]),
            plan["total"], plan["targets"],
            extra_removals=(
                {f"{BASE_DESTINATION[name]}FlatCompatibility"}
                if BASE_DESTINATION[name] != destination else set()),
            inherit_template=False)
        set_scale(changed, path, name, destination, plan["percentage_scale"])
        if plan["state"] is not None:
            _state, scale = plan["state"]
            set_state_scale(changed, path, name, destination, scale)
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")
    cleanup_stale_removals(set(SELECTED))
    cleanup_duplicate_template_inherits(set(SELECTED))


def validate_result() -> None:
    rs = Ruleset(ROOT)
    for name, destination in sorted(SELECTED.items()):
        resolved = rs.resolve_weapon(name)
        mains = set(main_warheads(resolved))
        expected = {f"{destination}FlatCompatibility"}
        if mains != expected:
            raise RuntimeError(f"{name}: expected {sorted(expected)}; found {sorted(mains)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    validate_selection()
    rs = Ruleset(ROOT)
    rows = baseline_rows(rs)
    states = {row is None for row in rows.values()}
    if states == {True}:
        validate_result()
        print(f"Already consolidated {len(SELECTED)} definitions")
        return 0
    if len(states) != 1:
        raise RuntimeError("partial energy/ordnance tranche detected")
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
