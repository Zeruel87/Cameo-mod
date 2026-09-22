#!/usr/bin/env python3
"""Audit the live folded percentage-damage runtime contract.

This report makes the intentional direct-hit activation and the repaired legacy
Int32 overflow cases visible. Overflow is judged ONLY against the wide legacy
folded units, never against shared-mode runtime units (shared halving is a
design scale change, not overflow). It also carries a separate SharedVersus
inventory that keeps zero-unit authored profiles visible. It also rejects rule
shapes that would double-apply a percentage hit or divide by an invalid
denominator.
"""
from __future__ import annotations

import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import effective_damage as ed  # noqa: E402
import effective_heaviness as eh  # noqa: E402
import percentage_damage as pd  # noqa: E402
from formula import parse_int32  # noqa: E402
from miniyaml import Ruleset  # noqa: E402
from survey_weapon_structure import weapon_reference_sets  # noqa: E402


def legacy_int32(value: int) -> int:
    return (value - pd.INT32_MIN) % (2 ** 32) + pd.INT32_MIN


def legacy_folded_units(damage: int, scale: int) -> int:
    numerator = legacy_int32(legacy_int32(damage * scale) + pd.FOLDED_ROUNDING_BIAS)
    return pd._truncate_div(numerator, pd.FOLDED_SCALE_DENOMINATOR)


def overflow_repairs(applications) -> list[tuple[dict, int, int]]:
    """Only a legacy Int32 wrap counts as an overflow repair.

    The old implementation wrapped ``damage * scale`` in Int32; the wide legacy
    result (``pd.folded_units``) does not. Their difference — independent of
    SharedVersus or Heaviness — is the sole overflow signal. An ordinary
    shared-mode halving (e.g. 60 wide-legacy units vs 30 shared runtime units,
    where Scale itself moved 10000 -> 2000) is a DESIGN scale change and must
    not be mislabelled as one.
    """
    rows = []
    for app in applications:
        if app.get("kind") != pd.PCT_FOLDED:
            continue
        old_units = legacy_folded_units(app["damage"], app["scale"])
        wide_units = pd.folded_units(app["damage"], app["scale"])[1]
        if old_units != wide_units:
            rows.append((app, old_units, wide_units))
    return rows


def has_physical_state(node) -> bool:
    scale = parse_int32(node.get("PhysicalStateScale"), default=0)
    states = node.child("PhysicalStates")
    return bool((node.get("PhysicalStateName") and scale) or
                (states is not None and any(parse_int32(c.value, default=0)
                                            for c in states.children)))


def dispatch_findings() -> list[str]:
    """Guard the split that prevents direct omissions and positional double hits."""
    area_path = ROOT / "OpenRA.Mods.Cameo" / "Warheads" / "AreaDamageWarhead.cs"
    standalone_path = (ROOT / "OpenRA.Mods.Cameo" / "Warheads" /
                       "AreaDamagePercentageWarhead.cs")
    area = area_path.read_text(encoding="utf-8")
    standalone = standalone_path.read_text(encoding="utf-8")
    findings = []

    ring = area[area.index("void ApplyRing"):area.index("void InflictPercentage")]
    if ring.count("InflictPrimaryDamage(") != 1 or ring.count("InflictPercentage(") != 1:
        findings.append("ApplyRing must call primary damage and folded percentage exactly once")
    if "InflictDamage(victim" in ring:
        findings.append("ApplyRing must not call the direct-hit wrapper")

    wrapper = area[area.index("protected override void InflictDamage"):
                   area.index("protected virtual void InflictPrimaryDamage")]
    if wrapper.count("InflictPrimaryDamage(") != 1 or wrapper.count("InflictPercentage(") != 1:
        findings.append("direct-hit wrapper must call primary and folded damage exactly once")

    if "protected override void InflictPrimaryDamage" not in standalone:
        findings.append("AreaDamagePercentage must override only the primary damage hook")
    if "protected override void InflictDamage" in standalone:
        findings.append("AreaDamagePercentage must not bypass the direct-hit wrapper")
    return findings


def shared_inventory_rows(node) -> list[dict]:
    """Enumerate authored SharedVersus AreaDamage warheads on a weapon.

    Includes valid zero-unit profiles (Damage=0, Scale=0, or h=0) that
    ``percentage_applications`` omits, so nothing authored is invisible.
    Zero-unit rows count separately and are never reported as percentage hits.
    """
    rows = []
    for child in node.children:
        if not child.key.startswith("Warhead") or child.value != "AreaDamage":
            continue
        tag = child.key.split("@", 1)[1] if "@" in child.key else child.key
        mode, heaviness = eh.heaviness_profile_config(
            child,
            pd.versus_table(child, "PercentageVersusLight"),
            pd.versus_table(child, "PercentageVersus"),
            pd.versus_table(child, "PercentageVersusHeavy"))
        if mode != eh.MODE_SHARED:
            continue
        damage = parse_int32(child.get("Damage"), default=0)
        scale = parse_int32(child.get("PercentageScale"), default=0)
        eh.validate_shared_numeric(mode, heaviness, pd.versus_table(child), damage, scale)
        continuous, runtime = pd.shared_folded_units(damage, scale, heaviness)
        rows.append({
            "tag": tag,
            "heaviness": heaviness,
            "damage": damage,
            "scale": scale,
            "runtime_units": runtime,
            "continuous_units": continuous,
            "zero_unit": runtime == 0,
        })
    return rows


def main() -> int:
    rules = Ruleset(ROOT)
    concrete = {
        name for name in rules.weapons
        if not name.startswith("^") and rules.resolve_weapon(name) is not None
    }
    _direct_armaments, reachable = weapon_reference_sets(rules, concrete)

    direct_rows = []
    overflow_rows = []
    shared_rows = []
    zero_unit_rows = []
    dispatch = dispatch_findings()
    invalid = list(dispatch)
    mixed = set()
    state = set()
    integrity = set()
    relationship_exceptions = set()

    for name in sorted(reachable):
        node = rules.resolve_weapon(name)
        applications = pd.percentage_applications(node, 200_000)
        folded = [a for a in applications if a["kind"] == pd.PCT_FOLDED]
        standalone = [a for a in applications if a["kind"] == pd.PCT_STANDALONE]

        for child in node.children:
            if not child.key.startswith("Warhead"):
                continue
            denominator = parse_int32(child.get("PercentageDenominator"), default=None)
            if denominator is not None and denominator <= 0:
                invalid.append(f"{name}:{child.key} has non-positive PercentageDenominator")
            if child.value == "AreaDamagePercentage" and \
                    parse_int32(child.get("PercentageScale"), default=0) > 0:
                invalid.append(f"{name}:{child.key} combines AreaDamagePercentage and PercentageScale")

        if ed.direct_actor_impact(node) and folded:
            direct_rows.extend((name, app["tag"]) for app in folded)
            if standalone:
                mixed.add(name)
            for app in folded:
                warhead = app["node"]
                if has_physical_state(warhead):
                    state.add(name)
                if parse_int32(warhead.get("IntegrityScale"), default=0) != 0:
                    integrity.add(name)
                relationships = warhead.get("ValidRelationships") or "Ally, Neutral, Enemy"
                if relationships.replace(" ", "") != "Ally,Neutral,Enemy":
                    relationship_exceptions.add(name)

        for app, old_units, wide_units in overflow_repairs(folded):
            overflow_rows.append(
                (name, app["tag"], old_units, wide_units, app["runtime_units"]))

        for row in shared_inventory_rows(node):
            shared_rows.append((name, *row.values()))
            if row["zero_unit"]:
                zero_unit_rows.append(
                    (name, row["tag"], row["heaviness"],
                     row["damage"], row["scale"]))

    print("# Folded percentage runtime audit")
    print()
    direct_weapons = {name for name, _tag in direct_rows}
    print(f"- Reachable direct-hit weapons activated: **{len(direct_weapons)}**")
    print(f"- Folded direct-hit applications activated: **{len(direct_rows)}**")
    print(f"- Direct weapons also carrying standalone percentage hits: **{len(mixed)}**")
    print(f"- Direct weapons whose folded hit feeds physical state: **{len(state)}**")
    print(f"- Direct weapons whose folded hit feeds integrity: **{len(integrity)}**")
    print(f"- Legacy Int32 overflow applications repaired: **{len(overflow_rows)}**")
    print(f"- Authored shared-mode (SharedVersus) applications: **{len(shared_rows)}** "
          f"(of which zero-unit: **{len(zero_unit_rows)}** — "
          "visibly listed, not counted as percentage hits)")
    print(f"- Non-default direct relationship sets: **{len(relationship_exceptions)}**")
    print(f"- Dispatch structural findings: **{len(dispatch)}**")
    print()

    print("## Repaired overflow cases")
    print()
    print("A repair is ONLY a legacy Int32 wrap independent of SharedVersus. "
          "The `runtime units` column shows the value actually applied today; "
          "for shared-mode rows it already carries the approved h/2 design "
          "scale (Scale itself moved 10000 -> 2000), so that column alone is "
          "NOT the before-migration value.")
    print()
    print("| weapon | warhead | legacy Int32 units | wide legacy units | runtime units |")
    print("|---|---|---:|---:|---:|")
    for name, tag, old, wide, current in overflow_rows:
        print(f"| `{name}` | `{tag}` | {old} | {wide} | {current} |")
    if not overflow_rows:
        print("| _none_ | | | | |")
    print()

    print("## Shared-mode inventory")
    print()
    print("Every authored reachable SharedVersus AreaDamage application, "
          "including zero-unit profiles. Zero-unit rows are authored "
          "configurations with no effective percentage hit, NOT activated "
          "percentage hits.")
    print()
    print("| weapon | warhead | h | Damage | Scale | shared runtime units |")
    print("|---|---|---:|---:|---:|---:|")
    for name, tag, heaviness, damage, scale, runtime, _cont, _zero in shared_rows:
        print(f"| `{name}` | `{tag}` | {heaviness} | {damage} | {scale} | {runtime} |")
    if not shared_rows:
        print("| _none_ | | | | | |")
    print()

    print("## Zero-unit shared applications")
    print()
    if zero_unit_rows:
        for name, tag, heaviness, damage, scale in zero_unit_rows:
            print(f"- `{name}`:`{tag}` (h={heaviness}, Damage={damage}, "
                  f"Scale={scale}) — shared units 0")
    else:
        print("_none_")
    print()

    print("## Direct-hit mixed effects")
    print()
    print(f"- Standalone plus folded: {', '.join(f'`{n}`' for n in sorted(mixed)) or '_none_'}")
    print(f"- Physical state: {', '.join(f'`{n}`' for n in sorted(state)) or '_none_'}")
    print(f"- Integrity: {', '.join(f'`{n}`' for n in sorted(integrity)) or '_none_'}")
    print()

    if invalid:
        print("## Blocking invalid rules")
        print()
        for finding in invalid:
            print(f"- {finding}")
        return 1

    print("_PASS — the active rules contain no invalid or double-percentage shapes._")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
