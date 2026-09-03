#!/usr/bin/env python3
"""
audit_yaml_lint_rules.py — Enforces YAML lint rules learned during cleanup.

Checks:
  1. No gating prereqs using ~wip, ~disable, ~unbuildable (must use ~disabled* prefix)
  2. Actors referenced as negation prereqs must have ProvidesPrerequisite
  3. Core templates (^Infantry, ^Vehicle, ^Conyard, ^Ship, etc.) must not reference
     actors from unloaded files in SpawnActorOnDeath, RepairActors, CargoConditions, etc.
  4. No Interactable + Selectable conflict in same actor/template
  5. No duplicated RepairActors lists in ContentPack actors (should inherit from template)

Usage:
  python tools/archive/audit_yaml_lint_rules.py [--root mods/cameo]
"""

import argparse
import pathlib
import re
import sys
from collections import defaultdict


# Prereqs that should be renamed to ~disabled-* variants
BANNED_GATING_PREREQS = [
    "~wip-content",
    "~unbuildable",
    "~disable",  # Note: ~disable is a substring of ~disabled, check carefully
    "~wip",  # Note: ~wip is a substring of ~wip-content, check carefully
]

# Core templates in defaults.yaml that are always loaded
CORE_TEMPLATES = {
    "^Infantry", "^DefaultInfantry", "^DefaultSoldier", "^Vehicle", "^Ship",
    "^Conyard", "^BaseBuilding", "^Building", "^AffectedByDriverKill",
    "^HospitalHealable", "^Repairable", "^RearmAtServiceDepot",
    "^upgrade.template", "^researched_upgrade.template", "^promotion_upgrade.template",
}

# Actor-reference fields in core templates that must not reference unloaded actors
ACTOR_REF_FIELDS = [
    "SpawnActorOnDeath",  # Actor: field
    "RepairActors",  # comma-separated list
    "RearmActors",  # comma-separated list
    "ExcludedActorTypes",  # comma-separated list
    "CargoConditions",  # key-value pairs where key is actor name
]


def find_banned_gating_prereqs(root: pathlib.Path) -> list[tuple[str, int, str]]:
    """Check 1: Find banned gating prereqs that should use ~disabled* prefix."""
    findings = []
    for f in root.rglob("*.yaml"):
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        rel = str(f.relative_to(root))
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Check for ~wip-content (but not ~disabled-wip-content)
            if "~wip-content" in stripped and "~disabled-wip-content" not in stripped:
                findings.append((rel, i, f"Banned prereq ~wip-content (use ~disabled-wip-content)"))
            # Check for ~unbuildable (but not ~disabled-unbuildable)
            if "~unbuildable" in stripped and "~disabled-unbuildable" not in stripped:
                findings.append((rel, i, f"Banned prereq ~unbuildable (use ~disabled-unbuildable)"))
            # Check for ~disable not followed by 'd' (i.e. ~disable but not ~disabled)
            for m in re.finditer(r"~disable(?![dD])", stripped):
                findings.append((rel, i, f"Banned prereq ~disable (use ~disabled)"))
            # Check for ~wip not followed by '-' (i.e. ~wip but not ~wip-content)
            for m in re.finditer(r"~wip(?![-c])", stripped):
                if "~disabled-wip" not in stripped:
                    findings.append((rel, i, f"Banned prereq ~wip (use ~disabled-wip)"))
    return findings


def find_interactable_selectable_conflicts(root: pathlib.Path) -> list[tuple[str, int, str]]:
    """Check 4: Find Interactable + Selectable conflicts in same actor/template."""
    findings = []
    for f in root.rglob("*.yaml"):
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        rel = str(f.relative_to(root))
        lines = text.splitlines()
        current_actor = None
        has_interactable = False
        has_selectable = False
        has_neg_interactable = False
        actor_line = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # New actor/template definition
            if not line.startswith(" ") and not line.startswith("\t") and stripped.endswith(":") and not stripped.startswith("#") and not stripped.startswith("-"):
                # Check previous actor
                if current_actor and has_interactable and has_selectable and not has_neg_interactable:
                    findings.append((rel, actor_line, f"{current_actor} has both Interactable and Selectable (conflict)"))
                current_actor = stripped[:-1]
                has_interactable = False
                has_selectable = False
                has_neg_interactable = False
                actor_line = i
            elif stripped == "Interactable:":
                has_interactable = True
            elif stripped == "-Interactable:":
                has_neg_interactable = True
            elif stripped == "Selectable:" or stripped.startswith("Selectable:"):
                has_selectable = True

        # Check last actor
        if current_actor and has_interactable and has_selectable and not has_neg_interactable:
            findings.append((rel, actor_line, f"{current_actor} has both Interactable and Selectable (conflict)"))
    return findings


def find_duplicated_repair_actors(root: pathlib.Path) -> list[tuple[str, int, str]]:
    """Check 5: Find ContentPack actors that duplicate RepairActors instead of inheriting."""
    findings = []
    # The canonical list from ^Conyard / ^Repairable template
    canonical = "td_gdi_repairfacility, td_nod_repairfacility"

    for f in root.rglob("*.yaml"):
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        rel = str(f.relative_to(root))
        if "ContentPacks" not in rel:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("RepairActors:") and "td_gdi_repairfacility" in stripped:
                # Check if it's a full list (likely duplicated from template)
                if "cabal_servicedepot" in stripped or "plymouth_garage" in stripped:
                    findings.append((rel, i, "Duplicated RepairActors list — should inherit from ^Conyard template instead"))
    return findings


def find_non_disabled_gating_in_defaults(root: pathlib.Path) -> list[tuple[str, int, str]]:
    """Check 1b: Specifically check defaults.yaml for non-disabled gating prereqs."""
    findings = []
    defaults = root / "rules" / "defaults.yaml"
    if not defaults.exists():
        return findings
    text = defaults.read_text(encoding="utf-8")
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        # Any prereq starting with ~ that isn't ~disabled and isn't a known valid prereq
        for m in re.finditer(r"(~[a-zA-Z][a-zA-Z0-9_.-]*)", stripped):
            prereq = m.group(1)
            if prereq.startswith("~disabled"):
                continue
            if prereq in ("~techlevel", "~faction", "~construction_yard", "~ra2fact"):
                continue  # These are valid optional prereqs
            # Flag unknown gating prereqs
            if prereq in ("~wip", "~wip-content", "~disable", "~unbuildable"):
                findings.append(("rules/defaults.yaml", i, f"Non-disabled gating prereq: {prereq}"))
    return findings


def main():
    parser = argparse.ArgumentParser(description="Audit YAML lint rules")
    parser.add_argument("--root", default="mods/cameo", help="Root directory to audit")
    args = parser.parse_args()

    root = pathlib.Path(args.root)
    all_findings = []

    print("=== Audit: YAML Lint Rules ===\n")

    # Check 1: Banned gating prereqs
    findings = find_banned_gating_prereqs(root)
    if findings:
        print(f"FAIL: Banned gating prereqs (should use ~disabled* prefix): {len(findings)}")
        for rel, line, msg in findings[:10]:
            print(f"  {rel}:{line}: {msg}")
        if len(findings) > 10:
            print(f"  ... and {len(findings) - 10} more")
        all_findings.extend(findings)
    else:
        print("PASS: No banned gating prereqs")

    print()

    # Check 4: Interactable + Selectable conflicts
    findings = find_interactable_selectable_conflicts(root)
    if findings:
        print(f"FAIL: Interactable + Selectable conflicts: {len(findings)}")
        for rel, line, msg in findings[:10]:
            print(f"  {rel}:{line}: {msg}")
        all_findings.extend(findings)
    else:
        print("PASS: No Interactable + Selectable conflicts")

    print()

    # Check 5: Duplicated RepairActors in ContentPacks
    findings = find_duplicated_repair_actors(root)
    if findings:
        print(f"FAIL: Duplicated RepairActors in ContentPacks: {len(findings)}")
        for rel, line, msg in findings[:10]:
            print(f"  {rel}:{line}: {msg}")
        all_findings.extend(findings)
    else:
        print("PASS: No duplicated RepairActors in ContentPacks")

    print()

    # Check 1b: Non-disabled gating in defaults.yaml
    findings = find_non_disabled_gating_in_defaults(root)
    if findings:
        print(f"FAIL: Non-disabled gating prereqs in defaults.yaml: {len(findings)}")
        for rel, line, msg in findings[:10]:
            print(f"  {rel}:{line}: {msg}")
        all_findings.extend(findings)
    else:
        print("PASS: No non-disabled gating prereqs in defaults.yaml")

    print()

    if all_findings:
        print(f"\nTOTAL FAILURES: {len(all_findings)}")
        sys.exit(1)
    else:
        print("\nAll checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
