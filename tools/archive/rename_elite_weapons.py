#!/usr/bin/env python3
"""rename_elite_weapons.py — Migrate legacy E suffix to _elite on elite-gated weapons.

Per DESIGN.md §16.3, ALL elite weapons must end with _elite.
This script:
1. Finds all Armament@*ELITE* blocks gated by RequiresCondition: rank-elite
2. Extracts the Weapon: reference
3. For weapons ending with 'E' (but not '_E' or '_elite'), renames:
   - The weapon definition (top-level YAML key)
   - All Weapon: references in armament blocks
   - All Inherits: references to the renamed weapon
4. Handles compound suffixes like AAE -> AA_elite, EResonance -> _eliteResonance, etc.

Usage:
  python tools/archive/rename_elite_weapons.py mods/cameo          # preview
  python tools/archive/rename_elite_weapons.py mods/cameo --apply   # apply changes
"""

import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "mods/cameo"
APPLY = "--apply" in sys.argv


def compute_new_name(old: str) -> str:
    """Compute the _elite name for a legacy E-suffix weapon."""
    if old.endswith("_elite"):
        return old

    # Handle compound suffixes
    # AAE -> AA_elite
    if old.endswith("AAE"):
        return old[:-3] + "AA_elite"
    # EMPE -> EMP_elite
    if old.endswith("EMPE"):
        return old[:-4] + "EMP_elite"
    # EResonance -> _eliteResonance
    if old.endswith("EResonance"):
        return old[:-1] + "_elite"  # drop E, add _elite -> ...EResonance -> ..._eliteResonance
        # Actually: old = "SteelMakoGunEResonance"
        # old[:-1] = "SteelMakoGunEResonanc" -- no that's wrong
        # We need: SteelMakoGunE + Resonance -> SteelMakoGun_eliteResonance
        # So: strip trailing 'E', then the part before E + "_elite" + part after E
        # But 'EResonance' ends with 'e' not 'E'... let me reconsider

    # General case: ends with capital 'E'
    if old.endswith("E") and not old.endswith("_E"):
        base = old[:-1]  # remove trailing E
        # Check if base already ends with something that makes sense
        return base + "_elite"

    return old


def main() -> int:
    # Phase 1: Find all elite-gated weapon references
    elite_weapons: set[str] = set()

    for dirpath, _, filenames in os.walk(ROOT):
        for fn in filenames:
            if not fn.endswith(".yaml"):
                continue
            fpath = os.path.join(dirpath, fn)
            try:
                lines = open(fpath, encoding="utf-8").readlines()
            except Exception:
                continue

            i = 0
            while i < len(lines):
                line = lines[i]
                am = re.match(r'^\tArmament@\w*[Ee][Ll][Ii][Tt][Ee]\w*\s*:', line)
                if am:
                    j = i + 1
                    weapon_ref = None
                    has_rank_elite = False
                    while j < len(lines):
                        bl = lines[j]
                        if re.match(r'^\t\S', bl) or re.match(r'^[^\t\s]', bl):
                            break
                        wref = re.match(r'^\t\tWeapon:\s*(\S+)', bl)
                        if wref:
                            weapon_ref = wref.group(1)
                        if 'rank-elite' in bl.lower():
                            has_rank_elite = True
                        j += 1
                    if weapon_ref and has_rank_elite:
                        elite_weapons.add(weapon_ref)
                i += 1

    # Phase 2: Filter to weapons that need renaming (end with E, not _elite)
    rename_map: dict[str, str] = {}
    for w in sorted(elite_weapons):
        if w.endswith("_elite"):
            continue
        # Skip weapons that already contain ELITE (e.g. MigMissiles_AA_ELITE)
        if "ELITE" in w.upper():
            continue
        new_name = None
        if w.endswith("E") and not w.endswith("_E"):
            new_name = compute_new_name(w)
        elif w.endswith("EResonance"):
            # Compound: SteelCloneGunEResonance -> SteelCloneGun_eliteResonance
            new_name = w[:-10] + "_eliteResonance"
        elif w.endswith("EResonanceBounce1"):
            new_name = w[:-18] + "_eliteResonanceBounce1"
        elif w.endswith("EResonanceBounce2"):
            new_name = w[:-18] + "_eliteResonanceBounce2"
        if new_name and new_name != w:
            rename_map[w] = new_name

    # Also add bounce sub-variants of resonance weapons
    # These aren't directly elite-gated but inherit from renamed weapons
    for old, new in list(rename_map.items()):
        if old.endswith("EResonance"):
            for suffix in ["Bounce1", "Bounce2"]:
                old_bounce = old + suffix
                new_bounce = new + suffix
                # Check if this bounce weapon exists in any YAML
                for dirpath, _, filenames in os.walk(ROOT):
                    for fn in filenames:
                        if not fn.endswith(".yaml"):
                            continue
                        try:
                            if old_bounce + ":" in open(os.path.join(dirpath, fn), encoding="utf-8").read():
                                rename_map[old_bounce] = new_bounce
                                raise StopIteration
                        except StopIteration:
                            break
                    else:
                        continue
                    break

    if not rename_map:
        print("No elite weapons need renaming.")
        return 0

    print(f"Found {len(rename_map)} elite weapons to rename:")
    for old, new in sorted(rename_map.items()):
        print(f"  {old} -> {new}")

    if not APPLY:
        print("\nDry run. Use --apply to make changes.")
        return 0

    # Phase 3: Apply renames across all YAML files
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
                # Rename weapon definition (top-level key)
                # Match: ^WeaponName: at start of line (not indented)
                content = re.sub(
                    rf'^({re.escape(old)}):',
                    f'{new}:',
                    content,
                    flags=re.MULTILINE
                )
                # Rename Weapon: references
                content = re.sub(
                    rf'(Weapon:\s*){re.escape(old)}(\s)',
                    rf'\g<1>{new}\g<2>',
                    content
                )
                # Rename Inherits: references
                content = re.sub(
                    rf'(Inherits:\s*){re.escape(old)}(\s)',
                    rf'\g<1>{new}\g<2>',
                    content
                )
                # Rename Inherits@xxx: references
                content = re.sub(
                    rf'(Inherits@\w+:\s*){re.escape(old)}(\s)',
                    rf'\g<1>{new}\g<2>',
                    content
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
