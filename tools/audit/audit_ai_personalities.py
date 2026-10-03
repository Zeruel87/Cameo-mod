#!/usr/bin/env python3
"""Validate the AI personality wiring.

The five squad-manager instances intentionally duplicate their shared fields.
This audit compares every non-tuning field byte-for-byte and verifies that the
random selector's condition set exactly matches the conditions consumed by the
instances.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AI_PATH = ROOT / "mods" / "cameo" / "ai" / "ai.yaml"
CONTROLLER_PATH = ROOT / "OpenRA.Mods.Cameo" / "Traits" / "BotPersonalityController.cs"
PERSONALITIES = ("rush", "turtle", "tech", "expansion", "steamroller", "guerrilla")
CONDITIONS = {f"personality-{name}" for name in PERSONALITIES}
DIFFICULTIES = ("easiest", "veryeasy", "easy", "medium", "hard", "veryhard", "brutal", "challenger", "unbeatable", "god")
REACTION_DELAYS = (7500, 6750, 6000, 5250, 4500, 3750, 3000, 2250, 1500, 750)
TUNING_FIELDS = {
    "MinimumAttackForceDelay",
    "SquadSize",
    "SquadSizeRandomBonus",
    "SquadValue",
    "SquadValueMaxEarlyBonus",
    "SquadValueMinLateBonus",
    "SquadValueMaxLateBonus",
    "MaxIdleUnits",
    "AttackForceInterval",
    "JoinGuerrilla",
    "MaxGuerrillaSize",
    "DangerScanRadius",
    "ProtectionScanRadius",
    "ProtectUnitScanRadius",
    "IdleScanRadius",
    "MaxBaseRadius",
    # Personality-identity fields, allow-listed when guerrilla landed (2026-09-28):
    # its harassment semantics require no staging/rally and off-axis routes,
    # which the prior uniform values could not express.
    "PreferMainTarget",
    "StageBeforeAssault",
    "IndirectRouteChance",
    "HighValueTargetPriority",
    "HarasserTypes",
    # CA-3 (AI_ARCHITECTURE 12.5): the role mix IS the personality flavour -
    # compositions differ by design, and the stage/composition gate patience
    # scales with the personality's tempo.
    "RoleMix",
    "RoleMixRoleFloorPct",
    "StageCompositionTicks",
    "StageRequiredRoles",
    # CA-4 (AI_ARCHITECTURE 12.7): formation movement knobs; whether a personality
    # marches in formation and how far the vanguard may lead is its tempo.
    "FormationMovement",
    "FormationTrailCells",
    "FormationMaxLeadCells",
    "FormationMaxStalledLeadCells",
    # Fast-squad count per personality and game time (maintainer 2026-09-28, DESIGN §19.1a):
    # guerrilla at least twice steamroller's, which spends its units on the main army.
    "MaxGuerrillaSquads",
    "MaxGuerrillaSquadsLate",
}
DEAD_FIELDS = {"RushInterval", "RushAttackScanRadius"}


def lines_for_block(lines: list[str], header: str) -> list[str]:
    for index, line in enumerate(lines):
        if line == f"\t{header}:":
            end = len(lines)
            for candidate in range(index + 1, len(lines)):
                if re.match(r"^\t[A-Za-z0-9_^`-]+(?:@[^:]+)?:", lines[candidate]):
                    end = candidate
                    break
            return lines[index:end]
    return []


def root_block(lines: list[str], header: str) -> list[str]:
    for index, line in enumerate(lines):
        if line == f"{header}:":
            end = len(lines)
            for candidate in range(index + 1, len(lines)):
                if lines[candidate] and not lines[candidate].startswith(("\t", " ")):
                    end = candidate
                    break
            return lines[index:end]
    return []


def field_blocks(block: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    current_name = None
    current: list[str] = []
    for line in block[1:]:
        match = re.match(r"^\t\t([^:\s]+):", line)
        if match:
            if current_name is not None:
                fields[current_name] = "\n".join(current)
            current_name = match.group(1)
            current = [line]
        elif current_name is not None:
            # Comment-only lines must not become part of the previous field's value —
            # a documented field would read as "differs"/"incorrect RequiresCondition"
            # the moment a comment lands under it (2026-10-02 false FAIL on all six
            # personalities).
            if not line.lstrip().startswith("#"):
                current.append(line)
    if current_name is not None:
        fields[current_name] = "\n".join(current)
    return fields


def condition_values(block: list[str]) -> set[str]:
    for line in block:
        if line.startswith("\t\tConditions:"):
            return {value.strip() for value in line.split(":", 1)[1].split(",") if value.strip()}
    return set()


def controller_conditions() -> list[str]:
    source = CONTROLLER_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"public readonly string\[\] Conditions\s*=\s*\{(?P<body>.*?)\};",
        source,
        re.DOTALL,
    )
    if match is None:
        return []
    return re.findall(r'"([^"]+)"', match.group("body"))


def notification_blocks(block: list[str]) -> tuple[dict[str, list[str]], set[str]]:
    blocks: dict[str, list[str]] = {}
    duplicates: set[str] = set()
    for line in block:
        match = re.match(r"^\tObserverConditionNotification@([^:]+):$", line)
        if not match:
            continue

        name = match.group(1)
        if name in blocks:
            duplicates.add(name)
            continue

        blocks[name] = lines_for_block(block, f"ObserverConditionNotification@{name}")

    return blocks, duplicates


BOOLEAN_LIMIT_FIELDS = {"PrioritizeBarracksBeforeRefinery"}
PRODUCTION_TIERS = ("easiest", "veryeasy", "easy", "medium", "hard", "veryhard", "brutal", "challenger", "unbeatable", "cameogod")
FAIR_TIER = "hard"

# DESIGN §19.1 (binding, maintainer 2026-09-28): every module runs on EVERY difficulty and only
# its strength scales. A `RequiresCondition` that names a difficulty condition is a tier gate and
# is forbidden — difficulty-selective behaviour belongs in BotLimits fields, not in which modules
# exist.
TIER_CONDITIONS = {
    "easiestbot", "veryeasybot", "easybot", "mediumbot", "hardbot",
    "veryhardbot", "brutalbot", "challengerbot", "unbeatablebot", "cameogodbot",
}
# Structural nodes that legitimately reference a tier condition: the BotLimits ladder IS the
# strength scale, ProvidesPrerequisite exports each tier's `Xbotplayer` token, and
# GrantConditionOnBotOwner defines the tier conditions themselves.
TIER_GATE_ALLOW_PREFIXES = ("BotLimits@", "ProvidesPrerequisite@", "GrantConditionOnBotOwner@")


def on_line(values: list[int]) -> bool:
    """Equal steps from the first tier to the last; an integer may sit within 0.5 of the line (DESIGN §19.1)."""
    n = len(values) - 1
    return all(abs(v - (values[0] + (values[-1] - values[0]) * i / n)) <= 0.5 for i, v in enumerate(values))


def difficulty_scale_failures() -> list[str]:
    """DESIGN §19.1: every per-tier number lies on one straight line in equal steps, and is written in
    every tier (a missing field falls back to a C# default and breaks the line silently)."""
    sys.path.insert(0, str(ROOT / "tools" / "audit"))
    from miniyaml import Ruleset

    rules = Ruleset(ROOT)
    failures = []
    player = rules.resolve("player")
    limits = {c.key.split("@", 1)[1]: c for c in player.children if c.key.startswith("BotLimits@")}
    if [t for t in DIFFICULTIES if t in limits] != list(DIFFICULTIES):
        return [f"resolved BotLimits tiers {sorted(limits)} != {list(DIFFICULTIES)}"]

    fields = sorted({c.key for block in limits.values() for c in block.children} - {"RequiresCondition"} - BOOLEAN_LIMIT_FIELDS)
    for field in fields:
        raw = [limits[t].get(field) for t in DIFFICULTIES]
        missing = [t for t, v in zip(DIFFICULTIES, raw) if v is None]
        if missing:
            failures.append(f"BotLimits.{field} is not written for {missing}: that tier silently uses the C# default")
            continue
        values = [int(v) for v in raw]
        if not on_line(values):
            failures.append(f"BotLimits.{field} is not on one equal-step line: {values}")

    for flag in BOOLEAN_LIMIT_FIELDS:
        states = [(limits[t].get(flag) or "false").strip().lower() == "true" for t in DIFFICULTIES]
        if states != sorted(states):
            failures.append(f"BotLimits.{flag} is not a single threshold (off below, on from some tier up): {states}")

    behavior = rules.resolve("^BotProductionBehavior")
    for trait in ("ProductionTimeMultiplier", "ProductionCostMultiplier"):
        nodes = [behavior.child(f"{trait}@{t}botplayer") if behavior else None for t in PRODUCTION_TIERS]
        if any(n is None for n in nodes):
            failures.append(f"^BotProductionBehavior.{trait} is missing a tier")
            continue
        values = [int(n.get("Multiplier")) for n in nodes]
        if not on_line(values):
            failures.append(f"{trait} is not on one equal-step line: {values}")
        fair = values[PRODUCTION_TIERS.index(FAIR_TIER)]
        if fair != 100:
            failures.append(f"{trait}: the fair tier `{FAIR_TIER}` must be 100, is {fair}")
    return failures


SCALE_FIELDS = ("Min", "Max", "RatioMin", "RatioMax", "Margin", "Growth", "Floor", "TurtleRushLean", "TechRushExpansionLean")
SCALE_CATEGORIES = ("army", "harvester", "refinery", "production", "conyard", "tech", "superweapon", "defence", "aircraft")
# category -> the BotLimits number its minute-0, nothing-seen line must reproduce (DESIGN 19.1 table).
SCALE_VS_LIMITS = {
    "refinery": "RefineryLimit",
    "harvester": "HarvesterLimit",
    "production": "ProductionTypeLimit",
    "conyard": "ConstructionYardLimit",
}
TECH_LINE = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3]


def scale_line(lo: int, hi: int, steps: int = 10) -> list[int]:
    """The synced math, in Python: thousandths, linear on tier/9, ONE floor at the end (ScaleTargetsEval)."""
    return [(lo + (hi - lo) * t // (steps - 1)) // 1000 for t in range(steps)]


def scale_target_failures() -> list[str]:
    """AI_ARCHITECTURE 12.22 / DESIGN 19.10: every ScaleTargetsBotModule category writes every field, Min <= Max, the tech
    line floors to 1 1 1 1 2 2 2 2 3 3, and at minute 0 with nothing seen each line equals the DESIGN 19.1 table."""
    sys.path.insert(0, str(ROOT / "tools" / "audit"))
    from miniyaml import Ruleset

    rules = Ruleset(ROOT)
    player = rules.resolve("player")
    module = player.child("ScaleTargetsBotModule") if player else None
    if module is None:
        return ["Player has no ScaleTargetsBotModule block (AI_ARCHITECTURE 12.22)"]

    failures = []
    categories = module.child("Categories")
    if categories is None:
        return ["ScaleTargetsBotModule has no Categories block"]

    written = {c.key: c for c in categories.children}
    for name in SCALE_CATEGORIES:
        if name not in written:
            failures.append(f"ScaleTargetsBotModule.Categories.{name} is missing: every category is written (DESIGN 19.1)")
    for name in sorted(set(written) - set(SCALE_CATEGORIES)):
        failures.append(f"ScaleTargetsBotModule.Categories.{name} is not a known category")

    values: dict[str, dict[str, int]] = {}
    for name in SCALE_CATEGORIES:
        node = written.get(name)
        if node is None:
            continue
        missing = [f for f in SCALE_FIELDS if node.get(f) is None]
        if missing:
            failures.append(f"ScaleTargetsBotModule.Categories.{name} does not write {missing}: the field silently uses the C# default")
            continue
        try:
            values[name] = {f: int(node.get(f)) for f in SCALE_FIELDS}
        except ValueError:
            failures.append(f"ScaleTargetsBotModule.Categories.{name}: every field is an integer in thousandths")
            continue
        if values[name]["Min"] > values[name]["Max"]:
            failures.append(f"ScaleTargetsBotModule.Categories.{name}: Min {values[name]['Min']} is above Max {values[name]['Max']}")
        if values[name]["RatioMin"] > values[name]["RatioMax"]:
            failures.append(f"ScaleTargetsBotModule.Categories.{name}: RatioMin is above RatioMax")

    if "tech" in values:
        line = scale_line(values["tech"]["Min"], values["tech"]["Max"])
        if line != TECH_LINE:
            failures.append(f"ScaleTargetsBotModule tech line floors to {line}, not {TECH_LINE}")

    limits = {c.key.split("@", 1)[1]: c for c in player.children if c.key.startswith("BotLimits@")}
    for category, field in SCALE_VS_LIMITS.items():
        if category not in values or [t for t in DIFFICULTIES if t in limits] != list(DIFFICULTIES):
            continue
        expected = [int(limits[t].get(field)) for t in DIFFICULTIES]
        line = scale_line(values[category]["Min"], values[category]["Max"])
        if line != expected:
            failures.append(f"ScaleTargetsBotModule {category}: minute-0 nothing-seen line {line} != BotLimits.{field} {expected} (DESIGN 19.1)")
    return failures


def tier_gate_failures() -> list[str]:
    """DESIGN §19.1: no module is switched on per tier. Any `RequiresCondition` on the resolved
    Player that names a difficulty condition is a violation — the module either runs everywhere
    (strength scaled through BotLimits / per-tier fields) or it is removed."""
    sys.path.insert(0, str(ROOT / "tools" / "audit"))
    from miniyaml import Ruleset

    rules = Ruleset(ROOT)
    failures = []
    for node in rules.resolve("player").children:
        if node.key.startswith(TIER_GATE_ALLOW_PREFIXES):
            continue
        condition = node.get("RequiresCondition")
        if not condition:
            continue
        tiers = sorted(set(re.findall(r"[A-Za-z0-9_-]+", condition)) & TIER_CONDITIONS)
        if tiers:
            failures.append(
                f"{node.key} gates on tier condition(s) {tiers} — DESIGN 19.1: modules run on "
                f"every difficulty; scale strength via BotLimits/per-tier fields, not RequiresCondition"
            )
    return failures


def main() -> int:
    lines = AI_PATH.read_text(encoding="utf-8").splitlines()
    failures: list[str] = []

    player = root_block(lines, "Player")
    if "\tInherits@aidifficulties: ^AIDifficulties" not in player:
        failures.append("Player does not inherit ^AIDifficulties")

    selector = lines_for_block(lines, "GrantRandomCondition@personality")
    controller = lines_for_block(player, "BotPersonalityController")
    source_conditions = controller_conditions()
    granted = condition_values(selector) if selector else set(source_conditions)
    if selector:
        failures.append("legacy GrantRandomCondition@personality remains")
    if not controller:
        failures.append("Player does not wire BotPersonalityController")
    if not source_conditions or len(source_conditions) != len(set(source_conditions)) or set(source_conditions) != CONDITIONS:
        failures.append(f"controller conditions {sorted(set(source_conditions))} != {sorted(CONDITIONS)}")

    bot_limits = [
        match.group(1)
        for line in lines
        if (match := re.match(r"^\tBotLimits@([^:]+):$", line))
    ]
    if bot_limits != list(DIFFICULTIES):
        failures.append(f"BotLimits difficulty order {bot_limits} != {list(DIFFICULTIES)}")
    for name, expected_delay in zip(bot_limits, REACTION_DELAYS):
        block = lines_for_block(lines, f"BotLimits@{name}")
        fields = field_blocks(block)
        expected = f"PersonalityReactionDelay: {expected_delay}"
        if fields.get("PersonalityReactionDelay", "").strip() != expected:
            failures.append(f"{name} has incorrect PersonalityReactionDelay")

    blocks = {
        name: lines_for_block(lines, f"SquadManagerBotModuleCA@{name}")
        for name in PERSONALITIES
    }
    missing = [name for name, block in blocks.items() if not block]
    if missing:
        failures.append(f"missing personality blocks: {', '.join(missing)}")

    if "\tSquadManagerBotModuleCA@generic:" in lines:
        failures.append("legacy SquadManagerBotModuleCA@generic block remains")

    notification_blocks_by_name, duplicate_notifications = notification_blocks(player)
    expected_notification_names = {f"personality-{name}" for name in PERSONALITIES}
    notification_names = set(notification_blocks_by_name)
    missing_notifications = expected_notification_names - notification_names
    orphan_notifications = notification_names - expected_notification_names
    if missing_notifications:
        failures.append(f"missing personality notifications: {', '.join(sorted(missing_notifications))}")
    if orphan_notifications:
        failures.append(f"orphan personality notifications: {', '.join(sorted(orphan_notifications))}")
    if duplicate_notifications:
        failures.append(f"duplicate personality notifications: {', '.join(sorted(duplicate_notifications))}")

    for name in PERSONALITIES:
        notification = notification_blocks_by_name.get(f"personality-{name}")
        if notification is None:
            continue

        fields = field_blocks(notification)
        required = f"genericbot && personality-{name}"
        if fields.get("RequiresCondition", "").strip() != f"RequiresCondition: {required}":
            failures.append(f"{name} notification has incorrect RequiresCondition")
        expected_notification = f"Notification: notification-bot-personality-{name}"
        if fields.get("Notification", "").strip() != expected_notification:
            failures.append(f"{name} notification has incorrect Notification")

    consumed = set()
    parsed_fields = {}
    for name, block in blocks.items():
        fields = field_blocks(block)
        parsed_fields[name] = fields
        required = f"genericbot && personality-{name}"
        if fields.get("RequiresCondition", "").strip() != f"RequiresCondition: {required}":
            failures.append(f"{name} has incorrect RequiresCondition")
        consumed.add(f"personality-{name}")
        dead = DEAD_FIELDS.intersection(fields)
        if dead:
            failures.append(f"{name} retains dead fields: {', '.join(sorted(dead))}")

    if consumed != set(source_conditions):
        failures.append(f"consumed conditions {sorted(consumed)} != {sorted(set(source_conditions))}")

    if parsed_fields:
        reference_name = PERSONALITIES[0]
        reference = parsed_fields[reference_name]
        for name in PERSONALITIES[1:]:
            current = parsed_fields[name]
            shared_names = (set(reference) | set(current)) - TUNING_FIELDS - {"RequiresCondition"}
            for field in sorted(shared_names):
                if reference.get(field, "").rstrip("\n") != current.get(field, "").rstrip("\n"):
                    failures.append(f"shared field {field} differs between {reference_name} and {name}")
            if (set(reference) - TUNING_FIELDS - {"RequiresCondition"}) != (
                set(current) - TUNING_FIELDS - {"RequiresCondition"}
            ):
                failures.append(f"shared field set differs between {reference_name} and {name}")

    failures.extend(difficulty_scale_failures())
    failures.extend(scale_target_failures())
    failures.extend(tier_gate_failures())

    print("# AI personality audit")
    print()
    print(f"- Selector conditions: `{', '.join(sorted(granted))}`")
    print(f"- Consumed conditions: `{', '.join(sorted(consumed))}`")
    print(f"- Personality blocks: {len([block for block in blocks.values() if block])}/{len(PERSONALITIES)}")
    print(f"- Personality notifications: {len(notification_names)}/{len(PERSONALITIES)}")
    print(f"- BotLimits reaction delays: `{', '.join(str(delay) for delay in REACTION_DELAYS)}`")
    print(f"- Explicit tuning allow-list: `{', '.join(sorted(TUNING_FIELDS))}`")
    print()
    if failures:
        print("## FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("## PASS")
    print("- Shared non-tuning fields are byte-identical across all personality instances.")
    print("- BotPersonalityController and squad-manager condition sets match exactly.")
    print("- Personality conditions have exactly one matching notification block each.")
    print("- No dead RushInterval/RushAttackScanRadius keys remain.")
    print("- Every per-tier BotLimits number and production multiplier lies on one equal-step line (DESIGN §19.1).")
    print("- ScaleTargetsBotModule writes every category and field, Min <= Max, the tech line is 1 1 1 1 2 2 2 2 3 3 and minute 0 equals the DESIGN 19.1 table (AI_ARCHITECTURE 12.22).")
    print("- No module gates on a difficulty-tier condition (DESIGN §19.1); strength scales via BotLimits.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
