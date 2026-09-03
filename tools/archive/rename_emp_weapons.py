#!/usr/bin/env python3
"""rename_emp_weapons.py — Normalize EMP weapon suffixes to _EMP.

Per DESIGN.md §1, weapons whose primary function is EMP disable must
append _EMP. This script renames:
  - Weapons ending with EMP (no underscore) -> _EMP
  - Weapons ending with Emp -> _EMP
  - Weapons ending with emp (lowercase) -> _EMP
  - Compound: EMPAA -> _EMP_AA, EMPAG -> _EMP_AG

Only processes top-level weapon definitions (not actors, sequences, etc.)
Skips:
  - Weapons already ending with _EMP
  - Weapons starting with EMP (like EMPGrenade) — EMP is a prefix, not suffix
  - Sub-variants (ArcTeslaFragment, Bounce, etc.)

Usage:
  python tools/archive/rename_emp_weapons.py mods/cameo          # preview
  python tools/archive/rename_emp_weapons.py mods/cameo --apply   # apply changes
"""

import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "mods/cameo"
APPLY = "--apply" in sys.argv

# Suffixes that indicate a sub-variant — not the base EMP weapon
SUBVARIANT_SUFFIXES = (
    "Bounce1", "Bounce2",
    "Explode",
)

# Compound suffixes to split: EMPAA -> _EMP_AA, EMPAG -> _EMP_AG
COMPOUND_EMP_SUFFIXES = ("EMPAA", "EMPAG", "EMPStructure", "EMPGarrisoned")


def compute_new_name(old: str) -> str | None:
    """Compute the _EMP name for a weapon, or None if it shouldn't be renamed."""
    if old.endswith("_EMP"):
        return None
    if old.startswith("EMP") and old.endswith("Grenade"):
        return None  # EMPGrenade — EMP is prefix, not suffix
    if old.startswith("EMP") and old.endswith("GrenadeExplode"):
        return None

    # Skip sub-variants
    for suffix in SUBVARIANT_SUFFIXES:
        if old.endswith(suffix):
            return None

    # Skip false positives where emp is part of another word
    if "Empty" in old or "empty" in old:
        return None
    if "EMPulse" in old:
        # TSEMPulseCannon -> TS_EMP_PulseCannon
        new_name = old.replace("EMPulse", "_EMP_Pulse")
        if new_name.startswith("_"):
            new_name = new_name[1:]
        return new_name if new_name != old else None
    if "Empress" in old or "empress" in old:
        return None
    if "Templar" in old or "templar" in old:
        return None
    if "Template" in old or "template" in old:
        return None
    if "Harvester" in old or "harvester" in old:
        return None

    # Handle EMP anywhere in the name (not just suffix)
    # Pattern: <prefix>EMP<suffix> -> <prefix>_EMP_<suffix>
    # But only if EMP is not already preceded by underscore
    match = re.search(r'(?<!_)EMP(?![a-z])', old)
    if not match:
        match = re.search(r'(?<!_)Emp(?!emp)', old)
    if not match:
        match = re.search(r'(?<!_)emp(?!emp)', old)

    if match:
        emp_type = match.group(0)  # EMP, Emp, or emp
        start = match.start()
        end = match.end()

        # Build new name: prefix + _EMP + rest
        prefix = old[:start]
        rest = old[end:]

        # If prefix is empty, EMP is a prefix — skip (like EMPGrenade)
        if not prefix:
            return None

        # Don't add underscore if prefix already ends with one
        if prefix.endswith("_"):
            new_name = prefix + "_EMP" + rest
        else:
            new_name = prefix + "_EMP" + rest

        # Clean up: if rest starts with a capital letter, add underscore
        if rest and rest[0].isupper() and not rest.startswith("_"):
            new_name = prefix + "_EMP_" + rest if not prefix.endswith("_") else prefix + "_EMP_" + rest

        # Handle compound: EMPAA -> _EMP_AA, EMPAG -> _EMP_AG
        if rest in ("AA", "AG", "Structure", "Garrisoned"):
            if prefix.endswith("_"):
                new_name = prefix + "_EMP_" + rest
            else:
                new_name = prefix + "_EMP_" + rest

        return new_name if new_name != old else None

    return None


def is_weapon_file(fpath: str) -> bool:
    """Check if file is likely to contain weapon definitions."""
    # Files named weapons.yaml in ContentPacks
    if os.path.basename(fpath) == "weapons.yaml":
        return True
    # Files in the weapons/ directory
    if os.sep + "weapons" + os.sep in fpath or "/weapons/" in fpath.replace("\\", "/"):
        return True
    return False


def main() -> int:
    rename_map: dict[str, str] = {}

    # Phase 1: Find all top-level weapon definitions containing EMP
    for dirpath, _, filenames in os.walk(ROOT):
        for fn in filenames:
            if not fn.endswith(".yaml"):
                continue
            fpath = os.path.join(dirpath, fn)
            if not is_weapon_file(fpath):
                continue
            try:
                lines = open(fpath, encoding="utf-8").readlines()
            except Exception:
                continue

            for i, line in enumerate(lines):
                # Top-level key (no leading tab, not a comment)
                wm = re.match(r'^([A-Za-z][A-Za-z0-9_.\-]*):\s*$', line)
                if wm and not line.startswith('\t') and not line.strip().startswith('#'):
                    name = wm.group(1)
                    if name.startswith('^'):
                        continue
                    # Check if it contains EMP/emp/Emp
                    if not re.search(r'[Ee][Mm][Pp]', name):
                        continue
                    new_name = compute_new_name(name)
                    if new_name and new_name != name:
                        rename_map[name] = new_name

    if not rename_map:
        print("No EMP weapons need renaming.")
        return 0

    print(f"Found {len(rename_map)} EMP weapons to rename:")
    for old, new in sorted(rename_map.items()):
        print(f"  {old} -> {new}")

    if not APPLY:
        print("\nDry run. Use --apply to make changes.")
        return 0

    # Phase 2: Apply renames across all YAML files
    total_changes = 0
    for dirpath, _, filenames in os.walk(ROOT):
        for fn in filenames:
            if not fn.endswith(".yaml"):
                continue
            fpath = os.path.join(dirpath, fn)
            try:
                content = open(fpath, encoding="utf-8").read()
            except Exception:
                continue

            original = content
            for old, new in rename_map.items():
                # Global case-insensitive replacement of the weapon name as a whole word.
                # This catches all reference patterns: top-level keys, Weapon: refs,
                # Weapons: list entries, Inherits: refs, etc.
                # Use word boundaries that handle dots in weapon names (e.g. TSCABALEMPDisable.anim)
                pattern = re.escape(old)
                # Allow the name to be followed by colon, whitespace, or end-of-line
                content = re.sub(
                    rf'(?<![A-Za-z0-9_]){pattern}(?![A-Za-z0-9_])',
                    new,
                    content,
                    flags=re.IGNORECASE
                )

            if content != original:
                open(fpath, "w", encoding="utf-8", newline="").write(content)
                short = fpath.replace("\\", "/").replace("mods/cameo/", "")
                changes = sum(1 for o, n in zip(original.split('\n'), content.split('\n')) if o != n)
                print(f"  Updated {short} ({changes} lines)")
                total_changes += changes

    print(f"\nTotal: {total_changes} lines changed across all files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
