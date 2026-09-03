#!/usr/bin/env python3
"""Apply and verify the maintainer-authorized remaining live role profiles.

This cohort deliberately excludes pricing, unreached definitions, and the
three Cryo progression holds.  Independently rounded percentage routes are
materialized as zero-flat companions instead of being approximated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/audit"), str(ROOT / "tools/balance")]

from audit_three_way_split import main_warheads  # noqa: E402
from consolidate_final_safe_cohorts import (  # noqa: E402
    cleanup_duplicate_template_inherits, cleanup_stale_removals,
    ensure_template_inherit, flat_main_nodes, percentage_scale, set_scale,
)
from consolidate_laser_heavy_routes import set_field  # noqa: E402
from consolidate_reviewed_weapon_roots import (  # noqa: E402
    add_compatibility_templates, apply_compatibility_block, block_bounds,
)
from consolidate_rule_driven_energy_ordnance import (  # noqa: E402
    add_percentage_companions,
)
from miniyaml import Ruleset  # noqa: E402
import percentage_damage as pd  # noqa: E402


# name: (destination, retained mains, total, targets, folded scale, friendly fire)
SELECTED = {
    "RA160mmE_rad_elite": ("Chemical_Light", {"Nuclear_Super"}, 108000,
                            "Ground, Water", 0, None),
    "CabalReaperMissiles": ("MissileHE_Medium", set(), 32000,
                             "Ground, Water", 0, None),
    "CabalHeavyReaperMissiles": ("MissileHE_Heavy", set(), 48000,
                                  "Ground, Water", 0, None),
    "HMG_fremen": ("Bullet_Medium", set(), 6000,
                    "Ground, Water, Air", 0, 67),
    "NaxCorrosionRocketTrooper_elite": ("MissileAP_Medium", set(), 16000,
                                         "Ground, Water, Air", 0, 75),
    "RashidanGun_upgrade": ("Bullet_Medium", {"RashidanGroundCompatibility"},
                             12000, "Ground, Water, Air", 0, 67),
    "SteelHoverMissile_elite": ("MissileAP_Light", set(), 16000,
                                 "Ground, Water, Air", 0, 75),
    "LatinBuggyChaingun": ("Bullet_Medium", set(), 8000,
                            "Ground, Water, Air", 0, None),
    "LatinBuggyRocket": ("MissileAP_Medium", set(), 40000,
                          "Ground, Water, Air", 0, None),
    "SCScourgeDroneExplosion": ("Demolition_Heavy", set(), 20000,
                                 "Ground, Water, Air", 9995, None),
    "SCScourgeExplosion": ("MissileAA_Heavy", set(), 100000,
                            "Air", 9999, None),
    "tkmjuggap": ("CannonAP_Light", set(), 8000,
                   "Ground, Water", 9988, None),
    "110mm_Gun": ("CannonAP_Light", set(), 30000,
                   "Ground, Water", 9997, None),
    "GlaveCanon": ("Railgun_Heavy", set(), 16000,
                    "Ground, Water", 9994, None),
    "ScoutMG": ("Bullet_Medium", set(), 4000,
                 "Ground, Water", 9975, None),
    "SiegeTankCannon": ("CannonHE_Heavy", set(), 30000,
                         "Ground, Water", 9997, None),
    "TSBomb": ("Demolition_Heavy", set(), 20000,
                "Ground, Ship", 9995, None),
    "TSBombSonic": ("Demolition_Heavy", {"Sonic_Heavy"}, 20000,
                     "Ground, Ship", 4995, None),
    "YakovlevCannon": ("Bullet_Medium", set(), 8000,
                        "Ground, Water, Air", 0, None),
    "YakovlevCannon_elite": ("Bullet_Medium", set(), 8000,
                              "Ground, Water, Air", 0, None),
    "t30shell": ("Railgun_Heavy", set(), 80000,
                  "Ground, Water", 3000, None),
}

EXPECTED_BASELINE_DIGEST = "e099df1c4dd010165663ab68b7f4877f545bf80bafbd1c3b8c93e3e2545a3c8c"

FORCE_PERCENTAGE_COMPANIONS = {
    "RA160mmE_rad_elite", "CabalReaperMissiles",
    "CabalHeavyReaperMissiles", "HMG_fremen",
    "NaxCorrosionRocketTrooper_elite", "RashidanGun_upgrade",
    "SteelHoverMissile_elite",
    "LatinBuggyChaingun", "LatinBuggyRocket",
    "YakovlevCannon", "YakovlevCannon_elite",
}

SOURCE_TOTAL_OVERRIDES = {"TSBombSonic": 10000}

CLEANUP_NAMES = set(SELECTED) | {
    "NaxGrilleArty", "NaxSturmArty", "SkyHawkCannon",
    "SkyHawkPlasmaCannon", "GrenadeRA", "LightTank2Missiles",
    "TSChem120mmx", "facedancer_grenade", "TS120mmx",
    "SteelVulcan", "SandmarineTuskFire", "GradRockets",
    "Future_Cryocopter_Rocket", "GLBarrelExplode", "GuardianShoot",
    "Tentacle", "v1rockets", "TSAegisMissile", "RA2Terrorist",
}


def plans(rs: Ruleset):
    result = {}
    for name, (destination, retained, total, targets, scale, _ff) in SELECTED.items():
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            raise RuntimeError(f"{name}: missing weapon")
        mains = set(main_warheads(resolved))
        expected = retained | {f"{destination}FlatCompatibility"}
        if mains == expected:
            result[name] = None
            continue
        collapse = mains - retained
        nodes = flat_main_nodes(resolved, collapse)
        if set(nodes) != collapse:
            raise RuntimeError(f"{name}: non-flat main in {sorted(collapse)}")
        actual_total = sum(int(str(node.get("Damage") or 0)) for node in nodes.values())
        source_total = SOURCE_TOTAL_OVERRIDES.get(name, total)
        if actual_total != source_total:
            raise RuntimeError(
                f"{name}: expected source total {source_total}, found {actual_total}")
        try:
            if name in FORCE_PERCENTAGE_COMPANIONS:
                raise RuntimeError("preserve distinct percentage profiles")
            computed_scale = percentage_scale(resolved, collapse, total)
            standalone = {}
        except RuntimeError:
            computed_scale = 0
            standalone = {
                key: {
                    "units": pd.folded_units(
                        int(str(node.get("Damage") or 0)),
                        int(str(node.get("PercentageScale") or 0)),
                    )[1],
                    "denominator": int(str(node.get("PercentageDenominator")
                                               or pd.FOLDED_DEFAULT_DENOMINATOR)),
                }
                for key, node in sorted(nodes.items())
                if int(str(node.get("PercentageScale") or 0)) != 0
            }
        if standalone:
            computed_scale = 0
        # T-30's exact recombination rounds to 2999, but the documented 3000
        # expresses the intended 15% folded railgun contribution and produces
        # the same 1200 runtime units at Damage 80000.
        accepted_scale = (name == "t30shell" and computed_scale == 2999 and scale == 3000)
        if computed_scale != scale and not accepted_scale:
            raise RuntimeError(
                f"{name}: expected folded scale {scale}, found {computed_scale}")
        result[name] = {
            "destination": destination,
            "mains": sorted(collapse),
            "total": total,
            "targets": targets,
            "percentage_scale": scale,
            "percentage": standalone,
        }
    return result


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def cleanup_removed_local_nodes(rs: Ruleset) -> None:
    """Delete local overrides masked by a removal in the same weapon block."""
    changed: dict[pathlib.Path, list[str]] = {}
    for name in sorted(CLEANUP_NAMES):
        local = rs.weapon(name)
        if local is None:
            continue
        path = pathlib.Path(local.file)
        lines = changed.setdefault(
            path, path.read_text(encoding="utf-8-sig").splitlines(True))
        start, end = block_bounds(lines, name)
        removals = {
            match.group(1)
            for line in lines[start + 1:end]
            if (match := re.match(r"^\t-Warhead@([^:]+):", line))
        }
        spans = []
        for key in removals:
            marker = re.compile(r"^\tWarhead@" + re.escape(key) + r":")
            indexes = [i for i in range(start + 1, end) if marker.match(lines[i])]
            for node_start in indexes:
                node_end = end
                for i in range(node_start + 1, end):
                    if lines[i].startswith("\t") and not lines[i].startswith("\t\t") \
                            and lines[i].strip():
                        node_end = i
                        break
                spans.append((node_start, node_end))
        for node_start, node_end in sorted(spans, reverse=True):
            del lines[node_start:node_end]

    # These descendants should inherit the newly consolidated parent verbatim.
    for name, keys in {
        "GradHeavyRockets": {"MissileHE_Heavy", "Concussion_Medium"},
        "tkmtechnicalmgap": {"Bullet_Light", "Demolition_Light"},
    }.items():
        local = rs.weapon(name)
        path = pathlib.Path(local.file)
        lines = changed.setdefault(
            path, path.read_text(encoding="utf-8-sig").splitlines(True))
        start, end = block_bounds(lines, name)
        spans = []
        for key in keys:
            marker = re.compile(r"^\tWarhead@" + re.escape(key) + r":")
            for node_start in [i for i in range(start + 1, end) if marker.match(lines[i])]:
                node_end = end
                for i in range(node_start + 1, end):
                    if lines[i].startswith("\t") and not lines[i].startswith("\t\t") \
                            and lines[i].strip():
                        node_end = i
                        break
                spans.append((node_start, node_end))
        for node_start, node_end in sorted(spans, reverse=True):
            del lines[node_start:node_end]

    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")


def apply(rs: Ruleset, rows) -> None:
    changed: dict[pathlib.Path, list[str]] = {}
    add_compatibility_templates(changed, rs, {row[0] for row in SELECTED.values()})
    for name, plan in rows.items():
        if plan is None:
            continue
        local = rs.weapon(name)
        path = pathlib.Path(local.file)
        resolved = rs.resolve_weapon(name)
        add_percentage_companions(changed, path, name, resolved, plan)
        ensure_template_inherit(changed, path, name, plan["destination"])
        apply_compatibility_block(
            changed, path, name, plan["destination"], set(plan["mains"]),
            plan["total"], plan["targets"], inherit_template=False)
        set_scale(changed, path, name, plan["destination"],
                  plan["percentage_scale"])
        if name == "t30shell":
            key = f"{plan['destination']}FlatCompatibility"
            set_field(changed[path], name, key, "Spread", 512)
        ff = SELECTED[name][5]
        if ff is not None:
            key = f"{plan['destination']}FlatCompatibility"
            set_field(changed[path], name, key, "FriendlyFireDamage", ff)
            set_field(changed[path], name, key, "FriendlyFireSpread", ff)
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")
    cleanup_stale_removals(set(SELECTED))
    cleanup_duplicate_template_inherits(set(SELECTED))


def inspect(rs: Ruleset) -> bool:
    for name, (destination, retained, total, targets, scale, ff) in SELECTED.items():
        resolved = rs.resolve_weapon(name)
        expected = retained | {f"{destination}FlatCompatibility"}
        if set(main_warheads(resolved)) != expected:
            return False
        node = resolved.child(f"Warhead@{destination}FlatCompatibility")
        if (int(str(node.get("Damage"))) != total
                or str(node.get("ValidTargets")) != targets
                or int(str(node.get("PercentageScale") or 0)) != scale):
            return False
        if name == "t30shell" and int(str(node.get("Spread"))) != 512:
            return False
        if ff is not None and (int(str(node.get("FriendlyFireDamage"))) != ff
                               or int(str(node.get("FriendlyFireSpread"))) != ff):
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--print-digest", action="store_true")
    args = parser.parse_args()
    rs = Ruleset(ROOT)
    if inspect(rs):
        print("Authorized remaining profiles are already applied.")
        return 0
    rows = plans(rs)
    current_digest = digest(rows)
    if args.print_digest:
        print(current_digest)
        print(json.dumps(rows, indent=2, sort_keys=True))
        return 0
    if current_digest != EXPECTED_BASELINE_DIGEST:
        raise RuntimeError(
            f"baseline fingerprint changed: {current_digest} != {EXPECTED_BASELINE_DIGEST}")
    if not args.apply:
        print("Authorized remaining profiles are pending; rerun with --apply.")
        return 1
    cleanup_removed_local_nodes(rs)
    cleanup_stale_removals(CLEANUP_NAMES | {"GradHeavyRockets", "tkmtechnicalmgap"})
    rs = Ruleset(ROOT)
    apply(rs, rows)
    if not inspect(Ruleset(ROOT)):
        raise RuntimeError("authorized remaining profile validation failed")
    print(f"Applied {len(SELECTED)} authorized profile roots.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
