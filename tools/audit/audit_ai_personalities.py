#!/usr/bin/env python3
"""Validate the YAML-only AI personality wiring.

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
PERSONALITIES = ("rush", "turtle", "tech", "expansion", "steamroller")
CONDITIONS = {f"personality-{name}" for name in PERSONALITIES}
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
            current.append(line)
    if current_name is not None:
        fields[current_name] = "\n".join(current)
    return fields


def condition_values(block: list[str]) -> set[str]:
    for line in block:
        if line.startswith("\t\tConditions:"):
            return {value.strip() for value in line.split(":", 1)[1].split(",") if value.strip()}
    return set()


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


def main() -> int:
    lines = AI_PATH.read_text(encoding="utf-8").splitlines()
    failures: list[str] = []

    player = root_block(lines, "Player")
    if "\tInherits@aidifficulties: ^AIDifficulties" not in player:
        failures.append("Player does not inherit ^AIDifficulties")

    selector = lines_for_block(lines, "GrantRandomCondition@personality")
    granted = condition_values(selector)
    if granted != CONDITIONS:
        failures.append(f"selector conditions {sorted(granted)} != {sorted(CONDITIONS)}")

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

    if consumed != CONDITIONS:
        failures.append(f"consumed conditions {sorted(consumed)} != {sorted(CONDITIONS)}")

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

    print("# AI personality audit")
    print()
    print(f"- Selector conditions: `{', '.join(sorted(granted))}`")
    print(f"- Consumed conditions: `{', '.join(sorted(consumed))}`")
    print(f"- Personality blocks: {len([block for block in blocks.values() if block])}/5")
    print(f"- Personality notifications: {len(notification_names)}/5")
    print(f"- Explicit tuning allow-list: `{', '.join(sorted(TUNING_FIELDS))}`")
    print()
    if failures:
        print("## FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("## PASS")
    print("- Shared non-tuning fields are byte-identical across all five instances.")
    print("- GrantRandomCondition and squad-manager condition sets match exactly.")
    print("- Personality conditions have exactly one matching notification block each.")
    print("- No dead RushInterval/RushAttackScanRadius keys remain.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
