#!/usr/bin/env python3
"""Audit the live folded percentage-damage runtime contract.

This report makes the intentional direct-hit activation and the repaired legacy
overflow cases visible. It also rejects rule shapes that would double-apply a
percentage hit or divide by an invalid denominator.
"""
from __future__ import annotations

import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

import effective_damage as ed  # noqa: E402
import percentage_damage as pd  # noqa: E402
from formula import parse_int32  # noqa: E402
from miniyaml import Ruleset  # noqa: E402
from survey_weapon_structure import weapon_reference_sets  # noqa: E402


def legacy_int32(value: int) -> int:
    return (value - pd.INT32_MIN) % (2 ** 32) + pd.INT32_MIN


def legacy_folded_units(damage: int, scale: int) -> int:
    numerator = legacy_int32(legacy_int32(damage * scale) + pd.FOLDED_ROUNDING_BIAS)
    return pd._truncate_div(numerator, pd.FOLDED_SCALE_DENOMINATOR)


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


def main() -> int:
    rules = Ruleset(ROOT)
    concrete = {
        name for name in rules.weapons
        if not name.startswith("^") and rules.resolve_weapon(name) is not None
    }
    _direct_armaments, reachable = weapon_reference_sets(rules, concrete)

    direct_rows = []
    overflow_rows = []
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

        for app in folded:
            old_units = legacy_folded_units(app["damage"], app["scale"])
            if old_units != app["runtime_units"]:
                overflow_rows.append((name, app["tag"], old_units, app["runtime_units"]))

    print("# Folded percentage runtime audit")
    print()
    direct_weapons = {name for name, _tag in direct_rows}
    print(f"- Reachable direct-hit weapons activated: **{len(direct_weapons)}**")
    print(f"- Folded direct-hit applications activated: **{len(direct_rows)}**")
    print(f"- Direct weapons also carrying standalone percentage hits: **{len(mixed)}**")
    print(f"- Direct weapons whose folded hit feeds physical state: **{len(state)}**")
    print(f"- Direct weapons whose folded hit feeds integrity: **{len(integrity)}**")
    print(f"- Legacy Int32 overflow applications repaired: **{len(overflow_rows)}**")
    print(f"- Non-default direct relationship sets: **{len(relationship_exceptions)}**")
    print(f"- Dispatch structural findings: **{len(dispatch)}**")
    print()

    print("## Repaired overflow cases")
    print()
    print("| weapon | warhead | legacy units | repaired units |")
    print("|---|---|---:|---:|")
    for name, tag, old, new in overflow_rows:
        print(f"| `{name}` | `{tag}` | {old} | {new} |")
    if not overflow_rows:
        print("| _none_ | | | |")
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
