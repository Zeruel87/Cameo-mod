#!/usr/bin/env python3
"""audit_upgrade_regression.py — is the UPGRADE actually better than the weapon it replaces?

    python tools/audit/audit_upgrade_regression.py [--armors Light,Medium,Heavy] [--baseline N]

⛔ WHY THIS EXISTS (maintainer, 2026-08-19), on the W24 A2 nuclear collapse:

    *"MonsterTank120mm -> CannonNuke_Heavy, MonsterTank120mmThermobaric -> CannonFire_Heavy
    don't make sense because the thermobaric version is the upgrade so it should be more powerful
    right? … the upgrade feels like a downgrade. We need to check all the upgrades like that so we
    don't accidentally downgrade the weapons."*

An upgrade is a PAIR of armaments on one actor, gated on the same condition — `!cond` fires as
built, `cond` fires once the upgrade lands. Nothing checked that the second is better than the
first. A W24 collapse can move the two halves onto families with OPPOSITE Versus profiles and
still pass every damage check, because the total is preserved on both sides.

MonsterTank is the case that prompted this: both halves land on the same geometry (Spread 800,
identical falloff) and the upgrade carries 1.5x the damage, so no damage guard fires — but
`CannonNuke` vs `CannonFire` is +43 Scout / +37 Light / +27 Medium against −49 None / −60 Flak.
The "upgrade" is +126% against infantry and +4% against the light vehicles a heavy tank exists to
kill. That is a role change sold as an upgrade.

WHAT IT MEASURES: centered per-shot damage at the shared 200,000-HP reference target,
including flat damage, folded ``PercentageScale`` damage, and standalone percentage
warheads. DPS uses the complete burst cycle (every inter-shot ``BurstDelays`` value plus
``ReloadDelay``). It flags an armor class where the upgrade is WEAKER, and calls the pair
ROLE-SHIFTED when it wins on some classes and loses on others.

⚠ NOT EVERY REGRESSION IS A BUG. A specialist upgrade may trade deliberately — an AA variant
should lose ground damage. This reports for review; `--baseline N` turns on the ratchet.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))
from cameo_model import Model  # noqa: E402
import effective_damage as ed  # noqa: E402
import formula  # noqa: E402
import percentage_damage as pd  # noqa: E402
import target_model as tm  # noqa: E402

# The armor classes a ground attacker is normally judged on. Air/ARMOR/HAZMAT are excluded from
# the VERDICT (an AA or anti-shield upgrade legitimately trades them) but still printed.
CORE = ("Scout", "Light", "Medium", "Heavy", "Superheavy", "Steel", "None", "Concrete", "Wood")
AIR = ("Fighter", "Bomber", "Helicopter", "Spaceship")
FLAT_TYPES = frozenset({"AreaDamage", "SpreadDamage", "TargetDamage"})


def _f(v, default=0.0) -> float:
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return default


def _enemy_damage(node) -> bool:
    relationships = (node.get("ValidRelationships") or "").strip()
    return not ("Ally" in relationships and "Enemy" not in relationships)


def _centered_parts(node, direct_actor: bool = False) -> tuple[int, list[int]]:
    """Centered falloff and each C# per-tick percentage modifier."""
    fo = radii = None
    live = True
    if node.value in {"AreaDamage", "AreaDamagePercentage", "SpreadDamage"}:
        # Ruleset validation happens even if the projectile later invokes the
        # direct-Actor DamageWarhead path.
        fo, radii, live = ed.falloff_and_radii(node)
        if node.value in {"AreaDamage", "AreaDamagePercentage"}:
            ticks = ed.area_tick_modifiers(node)
        else:
            ticks = [100]
    if direct_actor:
        # DamageWarhead's Actor-target path applies one full hit. It does not
        # enter AreaDamage's positional rings, so Falloff and Ticks are bypassed.
        return 100, [100]
    if node.value in {"TargetDamage", "HealthPercentageDamage"}:
        spread = _f(node.get("Spread"), 0.0)
        return (100, [100]) if spread > 0 else (0, [100])
    if not live:
        return 0, [100]
    falloff = ed.runtime_falloff(fo, radii, 0)
    return falloff, ticks


def _add_flat_armor_damage(per_armor: dict[str, float], node, damage: int,
                           versus: dict[str, float], direct_actor: bool = False) -> None:
    falloff, ticks = _centered_parts(node, direct_actor)
    for armor in set(CORE) | set(versus):
        armor_modifier = int(versus.get(armor, 100.0))
        dealt = sum(
            damage * falloff * tick * armor_modifier // 100 ** 3
            for tick in ticks)
        per_armor[armor] = per_armor.get(armor, 0.0) + dealt


def _add_percentage_armor_damage(per_armor: dict[str, float], app: dict,
                                 reference_hp: int,
                                 direct_actor: bool = False) -> None:
    node = app["node"]
    units = int(app["runtime_units"])
    denominator = int(app["denominator"])
    versus = app["versus"]
    falloff, ticks = _centered_parts(node, direct_actor)
    for armor in set(CORE) | set(versus):
        armor_modifier = int(versus.get(armor, 100.0))
        if node.value == "HealthPercentageDamage":
            dealt = reference_hp * units * falloff * armor_modifier // 100 ** 3
        else:
            dealt = 0
            for tick in ticks:
                intermediate = (
                    reference_hp * falloff * tick * units * armor_modifier // 100 ** 4)
                dealt += intermediate * 100 // denominator
        per_armor[armor] = per_armor.get(armor, 0.0) + dealt


def cycle_rate(node) -> float:
    """Projectiles per tick using the engine's complete burst cycle."""
    raw_reload = node.get("ReloadDelay")
    reload_ = 1.0 if raw_reload is None or str(raw_reload).strip() == "" else _f(raw_reload)
    if reload_ <= 0:
        return 0.0
    burst = max(int(_f(node.get("Burst"), 1.0) or 1.0), 1)
    cycle = formula.eff_reload(reload_, burst, node.get("BurstDelays"))
    return burst / cycle if cycle > 0 else 0.0


def _numbers(raw) -> list[int]:
    if raw is None or str(raw).strip() == "":
        return []
    try:
        return [int(float(part.strip())) for part in str(raw).split(",")]
    except (TypeError, ValueError):
        return []


def centered_multiplier(node) -> float:
    """Continuous centered multiplier; per-armor totals truncate each tick."""
    falloff, ticks = _centered_parts(node)
    return falloff * sum(ticks) / 10_000.0


def weapon_profile(rs, name: str) -> dict | None:
    """Centered runtime damage by armor + the cadence needed for DPS."""
    node = rs.resolve_weapon(name)
    if node is None:
        return None
    direct_actor = ed.direct_actor_impact(node)
    impact_multiplier = ed.projectile_impact_multiplier(node)
    per_armor: dict[str, float] = {}
    utility: set[tuple[str, str]] = set()
    for wh in node.children:
        if not wh.key.startswith("Warhead") or "Concrete" in wh.key:
            continue
        if wh.value in {"AffectsIntegrity", "GrantExternalCondition"}:
            utility.add((wh.value, wh.get("Condition") or ""))
        if wh.get("PhysicalStateName") or wh.child("PhysicalStates") is not None:
            utility.add(("PhysicalState", wh.get("PhysicalStateName") or "map"))
        if wh.value not in FLAT_TYPES or not _enemy_damage(wh):
            continue
        d = int(_f(wh.get("Damage")))
        if d <= 0:
            continue
        _add_flat_armor_damage(
            per_armor, wh, d, pd.versus_table(wh), direct_actor)

    reference_hp = tm.reference_hp()
    for app in pd.percentage_applications(node, reference_hp):
        wh = app["node"]
        if "Concrete" in wh.key or not _enemy_damage(wh):
            continue
        _add_percentage_armor_damage(
            per_armor, app, int(reference_hp), direct_actor)

    if abs(impact_multiplier - 1.0) > 1e-9:
        per_armor = {
            armor: damage * impact_multiplier
            for armor, damage in per_armor.items()
        }

    total = max(per_armor.values(), default=0.0)
    if total <= 0:
        return None
    valid_targets = {
        target.strip() for target in (node.get("ValidTargets") or "").split(",")
        if target.strip()
    }
    air_only = "Air" in valid_targets and not valid_targets.intersection({"Ground", "Water"})
    return {"total": total, "per_armor": per_armor, "rate": cycle_rate(node),
            "projectile_impact_multiplier": impact_multiplier, "air_only": air_only,
            "utility": utility}


def armament_profile(rs, names: tuple[str, ...]) -> dict | None:
    """Combined weapon-only DPS for weapons that fire together through one armament name.

    OpenRA permits multiple ``Armament`` traits with the same ``Name``.  They
    fire together, so judging only the last trait can turn a multi-beam upgrade
    into a false downgrade.  Different names (for example ``primary`` and
    ``garrisoned``) are separate firing modes and must not be combined.
    """
    per_armor: dict[str, float] = {}
    found = False
    air_only = True
    utility: set[tuple[str, str]] = set()
    for name in names:
        profile = weapon_profile(rs, name)
        if profile is None:
            continue
        found = True
        air_only = air_only and profile["air_only"]
        utility.update(profile["utility"])
        for armor, damage in profile["per_armor"].items():
            per_armor[armor] = per_armor.get(armor, 0.0) + damage * profile["rate"]
    return {"per_armor": per_armor, "air_only": air_only,
            "utility": utility} if found else None


def verdict_armors(base_profile: dict, requested_armors):
    """Judge a replacement on the target role of its base weapon."""
    return AIR if base_profile["air_only"] else requested_armors


def _csv(raw: str | None, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    if raw is None or not str(raw).strip():
        return default
    return tuple(part.strip().lower() for part in str(raw).split(",") if part.strip())


def _normal_attack_names(node) -> set[str]:
    """Return armament names routed by ordinary actor AttackBase traits."""
    names: set[str] = set()
    excluded = {"AttackMove", "AttackSounds", "AttackWander", "AttackGarrisoned"}
    for trait in node.children:
        trait_type = trait.key.split("@", 1)[0]
        if not trait_type.startswith("Attack") or trait_type in excluded:
            continue
        # OpenRA AttackBaseInfo defaults to primary + secondary.
        names.update(_csv(trait.get("Armaments"), ("primary", "secondary")))
    return names


def pairs(rs):
    """Pair condition-swapped weapons by their runtime firing route.

    Same-name replacements are always comparable. Cross-name replacements are
    paired only when both names are ordinary AttackBase routes, the condition
    comes from a prerequisite purchase, and one unambiguous half remains.
    """
    for actor in sorted(rs.actors):
        if actor.startswith("^"):
            continue
        node = rs.resolve(actor)
        if node is None:
            continue
        armaments = []
        for arm in node.children:
            if not arm.key.startswith("Armament"):
                continue
            weapon = (arm.get("Weapon") or "").strip()
            cond = (arm.get("RequiresCondition") or "").strip()
            if not weapon or not cond or "&&" in cond or "||" in cond:
                continue
            neg = cond.startswith("!")
            key = cond[1:].strip() if neg else cond
            armament_name = (arm.get("Name") or "primary").strip().lower()
            armaments.append((key, armament_name, "base" if neg else "up", weapon))

        prerequisite_conditions = {
            (trait.get("Condition") or "").strip()
            for trait in node.children
            if trait.key.split("@", 1)[0] == "GrantConditionOnPrerequisite"
        }
        normal_names = _normal_attack_names(node)
        by_name: dict[tuple[str, str], dict[str, list[str]]] = {}
        for cond, name, half_name, weapon in armaments:
            by_name.setdefault((cond, name), {"base": [], "up": []})[half_name].append(weapon)

        unmatched: dict[str, dict[str, list[tuple[str, str]]]] = {}
        for (cond, name), half in by_name.items():
            base, up = tuple(half["base"]), tuple(half["up"])
            if base and up:
                if base and up and base != up:
                    yield actor, base, up, cond, name
                continue
            if name in normal_names:
                side = "base" if base else "up"
                for weapon in base or up:
                    unmatched.setdefault(cond, {"base": [], "up": []})[side].append((name, weapon))

        for cond, half in unmatched.items():
            if cond not in prerequisite_conditions:
                continue
            if len(half["base"]) == len(half["up"]) == 1:
                _base_name, base_weapon = half["base"][0]
                _up_name, up_weapon = half["up"][0]
                if base_weapon != up_weapon:
                    yield actor, (base_weapon,), (up_weapon,), cond, "attack"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--armors", default=",".join(CORE))
    ap.add_argument("--baseline", type=int, default=None)
    a = ap.parse_args()
    armors = [s.strip() for s in a.armors.split(",") if s.strip()]

    rs = Model().rs
    weaker, shifted, marginal, npairs = [], [], [], 0

    for actor, base_w, up_w, cond, armament_name in pairs(rs):
        b, u = armament_profile(rs, base_w), armament_profile(rs, up_w)
        if not b or not u:
            continue
        npairs += 1
        losses, gains = [], []
        # Judge on the role of the weapon being replaced. Becoming all-target
        # must not hide a regression in an Air-only base weapon.
        judged_armors = verdict_armors(b, armors)
        for armor in judged_armors:
            bd = b["per_armor"].get(armor, 0.0)
            ud = u["per_armor"].get(armor, 0.0)
            if bd <= 0:
                continue
            ratio = ud / bd
            (losses if ratio < 0.995 else gains).append((armor, ratio))
        row = (actor, base_w, up_w, cond, armament_name,
               sorted(losses, key=lambda x: x[1]), gains)
        if losses:
            added_utility = bool(u["utility"] - b["utility"])
            (shifted if gains or added_utility else weaker).append(row)
            continue
        # No outright loss — but an upgrade that is +4% on the armor the unit exists to fight and
        # +126% on something else has still changed the unit's ROLE and will FEEL like a downgrade.
        # Maintainer 2026-08-19 on MonsterTank: *"the upgrade feels like a downgrade."*
        ratios = [r for _a, r in gains]
        if len(ratios) >= 3 and min(ratios) < 1.10 and max(ratios) / min(ratios) >= 2.0:
            marginal.append((actor, base_w, up_w, cond, armament_name,
                             sorted(gains, key=lambda x: x[1])[:4], max(ratios)))

    print("# audit_upgrade_regression — is the upgrade better than what it replaces?\n")
    print(f"Reference target HP: **{tm.reference_hp():,}**; centered impact; full burst cycle; "
          "weapon profile only (actor multipliers excluded).\n")
    print(f"Gated armament pairs found: **{npairs}**\n")

    def table(rows, title, note):
        print(f"## {title} ({len(rows)})\n")
        print(f"{note}\n")
        if not rows:
            print("_none_\n")
            return
        print("| actor | base → upgrade | condition | worst losses (upgrade DPS ÷ base DPS) |")
        print("|---|---|---|---|")
        for actor, bw, uw, cond, armament_name, losses, _g in rows[:40]:
            worst = ", ".join(f"{ar} {rt:.2f}x" for ar, rt in losses[:4])
            base_label, up_label = " + ".join(bw), " + ".join(uw)
            mode = f" ({armament_name})" if armament_name != "primary" else ""
            print(f"| `{actor}` | `{base_label}` → `{up_label}` | `{cond}`{mode} | {worst} |")
        if len(rows) > 40:
            print(f"\n_… {len(rows) - 40} more_")
        print()

    table(weaker, "⛔ STRICTLY WEAKER — the upgrade loses on every core armor it changes",
          "No trade-off to justify these: the player pays for the upgrade and gets less.")
    table(shifted, "⚠ ROLE-SHIFTED — wins on some armor classes, loses on others",
          "Legitimate for a specialist (an AA variant should lose ground damage). A REGRESSION "
          "when the losses land on the armor classes the unit exists to fight — MonsterTank "
          "trading Scout/Light/Medium for infantry is the case that prompted this audit.")

    print(f"## ⚠ THIN MARGIN — wins everywhere, but barely where it counts ({len(marginal)})\n")
    print("The upgrade never loses, so no damage or regression check fires — yet it is worth only a "
          "few percent on some core armor classes while multiplying on others. That is a ROLE change "
          "wearing an upgrade's clothes, and the player feels it as a downgrade in the fight the unit "
          "was built for.\n")
    if marginal:
        print("| actor | base → upgrade | weakest core gains | best |")
        print("|---|---|---|--:|")
        for actor, bw, uw, _c, _armament_name, worst, best in marginal[:40]:
            w = ", ".join(f"{ar} {rt:.2f}x" for ar, rt in worst)
            print(f"| `{actor}` | `{' + '.join(bw)}` → `{' + '.join(uw)}` | {w} | {best:.2f}x |")
        if len(marginal) > 40:
            print(f"\n_… {len(marginal) - 40} more_")
        print()
    else:
        print("_none_\n")

    total = len(weaker) + len(shifted) + len(marginal)
    print(f"**total findings: {total}** ({len(weaker)} strictly weaker, {len(shifted)} role-shifted, "
          f"{len(marginal)} thin-margin)")
    if a.baseline is None:
        print("\n_no baseline set — reporting only. Measure on a settled tree, then ratchet DOWN._")
        return 0
    if total > a.baseline:
        print(f"\n**FAIL — {total} exceeds the baseline of {a.baseline}.**")
        return 1
    print(f"\n_at or below baseline ({a.baseline})._")
    return 0


if __name__ == "__main__":
    sys.exit(main())
