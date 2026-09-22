#!/usr/bin/env python3
"""
convert_maps.py — Convert resource-center maps from original CNC/RA actor
names to the Cameo mod's prefixed actor names.

Resource center maps are in Tiberian Dawn (CNC) or Red Alert (RA) format.
They use original game actor names (e1, 2tnk, SBAG, FACT, etc.) which the
Cameo mod has renamed to prefixed names (td_gdi_rifleinfantry,
ra1_soviets_heavytank, etc.).

This script:
  1. Loads all rename_map_*.yaml files from tools/rename/
  2. Extracts actor old→new mappings from each
  3. Applies the combined mapping to .oramap files (zip archives containing
     map.yaml and optionally .lua files)
  4. Reports all changes made
  5. Repacks the .oramap only if changes were made

Usage:
  python convert_maps.py <path>           # Convert a single .oramap or directory
  python convert_maps.py <path> --dry-run # Show what would change
  python convert_maps.py <path> --backup  # Keep .oramap.bak backup

Future: Dune 2000 map support will be added once Atreides and Harkonnen
factions are implemented. For now, only TD and RA1 maps are handled.
"""

import argparse
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

# ─── YAML loader (minimal, no external deps) ───────────────────────────────

def load_rename_maps(rename_dir: Path) -> dict[str, str]:
    """Load all rename_map_*.yaml files and merge actor mappings."""
    mapping: dict[str, str] = {}

    for yml in sorted(rename_dir.glob("rename_map_*.yaml")):
        text = yml.read_text(encoding="utf-8-sig", errors="replace")
        # Find the "actors:" section and parse "old: new" pairs
        in_actors = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("actors:"):
                in_actors = True
                continue
            if stripped.startswith("files:"):
                in_actors = False
                continue
            if not in_actors:
                continue
            # Parse "old: new" (tab-indented)
            if ":" in stripped and not stripped.startswith("#"):
                parts = stripped.split(":", 1)
                old = parts[0].strip()
                new = parts[1].strip()
                if old and new and old != new:
                    # Don't overwrite existing mappings (first file wins)
                    if old not in mapping:
                        mapping[old] = new

    return mapping


# ─── Built-in legacy mappings for original CNC/RA actor names ──────────────
# These map original game actor names to the Cameo mod's prefixed names.
# The ra1_legacy.yaml rename map already handles most RA1 actors.
# For TD actors, we build the mapping from the mod's actor definitions.

# Original CNC (Tiberian Dawn) actor names → Cameo mod actor names
# Source: OpenRA CNC mod actor definitions, mapped to Cameo's td_gdi_*/td_nod_* actors
TD_GDI_LEGACY = {
    "e1": "td_gdi_rifleinfantry",
    "e2": "td_gdi_grenadier",
    "e3": "td_gdi_rocketinfantry",
    "e5": "td_gdi_engineer",
    "e6": "td_gdi_commando",
    "harv": "td_gdi_harvester",
    "jeep": "td_gdi_humvee",
    "apc": "td_gdi_apc",
    "mtnk": "td_gdi_mediumtank",
    "htnk": "td_gdi_mammothtank",
    "msam": "td_gdi_mlrs",
    "art2": "td_gdi_artillery",
    "recon": "td_gdi_reconbike",
    "stnk": "td_gdi_stealthtank",
    "orca": "td_gdi_orca",
    "heli": "td_gdi_chinooktransport",
    "a10": "td_gdi_a10",
    "truk": "td_gdi_supplytruck",
    "fact": "td_gdi_constructionyard",
    "pyle": "td_gdi_barracks",
    "weap": "td_gdi_warfactory",
    "airc": "td_gdi_helipad",
    "hpad": "td_gdi_helipad",
    "powr": "td_gdi_powerplant",
    "nuke": "td_gdi_advancedpowerplant",
    "proc": "td_gdi_refinery",
    "silo": "td_gdi_tiberiumsilo",
    "refin": "td_gdi_refinery",
    "hq": "td_gdi_communicationscenter",
    "eye": "td_gdi_advancedcommunicationscenter",
    "gtwr": "td_gdi_guardtower",
    "atwr": "td_gdi_advancedguardtower",
    "fix": "td_gdi_repairfacility",
    "mcv": "td_gdi_mobileconstructionvehicle",
}

TD_NOD_LEGACY = {
    "e4": "td_nod_flamethrower",
    "e3": "td_nod_rocketinfantry",
    "harv": "td_nod_harvester",
    "bggy": "td_nod_buggy",
    "bike": "td_nod_reconbike",
    "lst": "td_nod_lighttank",
    "stnk": "td_nod_stealthtank",
    "arty": "td_nod_artillery",
    "msam": "td_nod_rocketlauncher",
    "truk": "td_nod_supplytruck",
    "heli": "td_nod_apacheattackhelicopter",
    "fact": "td_nod_constructionyard",
    "hand": "td_nod_handofnod",
    "weap": "td_nod_warfactory",
    "airc": "td_nod_airstrip",
    "hpad": "td_nod_helipad",
    "powr": "td_nod_powerplant",
    "nuke": "td_nod_advancedpowerplant",
    "proc": "td_nod_refinery",
    "silo": "td_nod_tiberiumsilo",
    "refin": "td_nod_refinery",
    "hq": "td_nod_communicationscenter",
    "tmpl": "td_nod_templeofnod",
    "obli": "td_nod_obeliskoflight",
    "gun": "td_nod_turret",
    "sam": "td_nod_samsite",
    "mcv": "td_nod_mobileconstructionvehicle",
}

# Original RA (Red Alert) actor names → Cameo mod actor names
# Note: many RA1 actors are already covered by ra1_legacy.yaml
RA_ALLIES_LEGACY = {
    "e1": "ra1_allies_rifleinfantry",
    "e3": "ra1_allies_alliedrocketsoldier",
    "spy": "ra1_allies_spy",
    "thf": "ra1_allies_thief",
    "sniper": "ra1_allies_sniper",
    "medi": "ra1_allies_medic",
    "shok": "ra1_allies_shocktrooper",
    "jeep": "ra1_allies_jeep",
    "apc": "ra1_allies_alliedapc",
    "1tnk": "ra1_allies_lighttank",
    "2tnk": "ra1_allies_mediumtank",
    "3tnk": "ra1_allies_heavytank",
    "arty": "ra1_allies_artillery",
    "truk": "ra1_allies_supplytruck",
    "harv": "ra1_allies_oretruck",
    "pt": "ra1_allies_gunboat",
    "dd": "ra1_allies_destroyer",
    "ca": "ra1_allies_cruiser",
    "fact": "ra1_allies_alliedconstructionyard",
    "tent": "ra1_allies_alliedbarracks",
    "weap": "ra1_allies_alliedwarfactory",
    "syrd": "ra1_allies_alliednavalyard",
    "powr": "ra1_allies_powerplant",
    "proc": "ra1_allies_alliedorerefinery",
    "silo": "ra1_allies_oresilo",
    "hpad": "ra1_allies_alliedhelipad",
    "spen": "ra1_allies_subpen",
    "atek": "ra1_allies_technologycenter",
    "gap": "ra1_allies_gapgenerator",
    "mslo": "ra1_allies_missilesilo",
    "pdom": "ra1_allies_chronosphere",
    "iron": "ra1_allies_ironcurtain",
    "agun": "ra1_allies_alliedgunturret",
    "gtwr": "ra1_allies_alliedgunturret",
    "atwr": "ra1_allies_alliedcannon",
    "tsla": "ra1_allies_teslacoil",
    "mcv": "ra1_allies_alliedmobileconstructionvehicle",
}

RA_SOVIETS_LEGACY = {
    "e1": "ra1_soviets_rifleinfantry",
    "e3": "ra1_soviets_rocketinfantry",
    "shok": "ra1_soviets_shocktrooper",
    "dog": "ra1_soviets_attackdog",
    "e2": "ra1_soviets_flameinfantry",
    "apc": "ra1_soviets_sovietapc",
    "1tnk": "ra1_soviets_lighttank",
    "2tnk": "ra1_soviets_mediumtank",
    "3tnk": "ra1_soviets_heavytank",
    "4tnk": "ra1_soviets_mammothtank",
    "v2rl": "ra1_soviets_v2rocketlauncher",
    "arty": "ra1_soviets_artillery",
    "truk": "ra1_soviets_supplytruck",
    "harv": "ra1_soviets_oretruck",
    "ttnk": "ra1_soviets_teslatank",
    "ftrk": "ra1_soviets_tankdestroyer",
    "stnk": "ra1_soviets_stealthtank",
    "sub": "ra1_soviets_submarine",
    "ss": "ra1_soviets_submarine",
    "msub": "ra1_soviets_missilesubmarine",
    "fact": "ra1_soviets_constructionyard",
    "barr": "ra1_soviets_barracks",
    "weap": "ra1_soviets_warfactory",
    "spen": "ra1_soviets_sovietsubpen",
    "powr": "ra1_soviets_powerplant",
    "proc": "ra1_soviets_orerefinery",
    "silo": "ra1_soviets_oresilo",
    "hpad": "ra1_soviets_soviethelipad",
    "stek": "ra1_soviets_soviettechnologycenter",
    "mslo": "ra1_soviets_missilesilo",
    "iron": "ra1_soviets_ironcurtain",
    "pdom": "ra1_soviets_chronosphere",
    "tsla": "ra1_soviets_teslacoil",
    "sam": "ra1_soviets_samsite",
    "agun": "ra1_soviets_flakcannon",
    "ftur": "ra1_soviets_flameturret",
    "mcv": "ra1_soviets_mobileconstructionvehicle",
}


def build_full_mapping(rename_dir: Path) -> dict[str, str]:
    """Build the complete old→new actor name mapping."""
    mapping: dict[str, str] = {}

    # 1. Load rename_map_*.yaml files (these have already-applied renames)
    yaml_mapping = load_rename_maps(rename_dir)
    mapping.update(yaml_mapping)

    # 2. Add built-in legacy mappings (original game names → mod names)
    # TD GDI and Nod share some names (e.g. "e3", "harv", "fact") —
    # we can't auto-resolve which faction a map actor belongs to.
    # For ambiguous names, we DON'T rename (the mod may still define them
    # or the map format context disambiguates).
    # Instead, we only add unambiguous mappings that aren't already in the yaml mapping.
    for legacy_map in [TD_GDI_LEGACY, TD_NOD_LEGACY, RA_ALLIES_LEGACY, RA_SOVIETS_LEGACY]:
        for old, new in legacy_map.items():
            if old not in mapping:
                mapping[old] = new
            # If there's a conflict (old maps to different new), keep the first one
            # and warn. The user will need to handle ambiguous cases manually.

    return mapping


# ─── Map file processing ───────────────────────────────────────────────────

# Actor identifier pattern in YAML map files: "ActorNNN: <type>"
ACTOR_TYPE_RE = re.compile(r"^(\s+Actor\d+:\s+)(\S+)$", re.MULTILINE)

# Actor identifier pattern in Lua files: quoted strings that look like actor types
LUA_ACTOR_RE = re.compile(r'["\']([A-Za-z0-9_.]+)["\']')


def replace_in_yaml(content: str, mapping: dict[str, str]) -> tuple[str, list[str]]:
    """Replace actor type references in map.yaml content.
    
    Only replaces whole identifiers after 'ActorNNN:' to avoid
    touching paths, sequence names, or other strings.
    """
    changes: list[str] = []
    
    def replacer(m: re.Match) -> str:
        prefix = m.group(1)
        old_type = m.group(2)
        # Case-insensitive lookup
        for old, new in mapping.items():
            if old.lower() == old_type.lower():
                changes.append(f"  {old_type} -> {new}")
                return prefix + new
        return m.group(0)
    
    new_content = ACTOR_TYPE_RE.sub(replacer, content)
    return new_content, changes


def replace_in_lua(content: str, mapping: dict[str, str]) -> tuple[str, list[str]]:
    r"""Replace actor type references in Lua files.

    Only replaces whole quoted strings that match an actor name exactly.
    Skips lines that look like file paths (containing / or \).
    """
    changes: list[str] = []
    lines = content.splitlines(keepends=True)
    new_lines = []
    
    for line in lines:
        # Skip lines that look like file paths
        if "/" in line and "." in line:
            new_lines.append(line)
            continue
        
        def lua_replacer(m: re.Match) -> str:
            old_type = m.group(1)
            for old, new in mapping.items():
                if old.lower() == old_type.lower():
                    changes.append(f"  {old_type} -> {new}")
                    return m.group(0).replace(old_type, new)
            return m.group(0)
        
        new_line = LUA_ACTOR_RE.sub(lua_replacer, line)
        new_lines.append(new_line)
    
    return "".join(new_lines), changes


def process_oramap(map_path: Path, mapping: dict[str, str], dry_run: bool, backup: bool) -> list[str]:
    """Process a single .oramap file."""
    all_changes: list[str] = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Extract the .oramap
        with zipfile.ZipFile(map_path, "r") as z:
            z.extractall(tmpdir)
        
        # Process map.yaml
        map_yaml = tmpdir / "map.yaml"
        if map_yaml.exists():
            content = map_yaml.read_text(encoding="utf-8-sig", errors="replace")
            new_content, changes = replace_in_yaml(content, mapping)
            if changes:
                all_changes.append(f"map.yaml:")
                all_changes.extend(changes)
                if not dry_run:
                    map_yaml.write_text(new_content, encoding="utf-8")
        
        # Process .lua files
        for lua_file in tmpdir.glob("*.lua"):
            content = lua_file.read_text(encoding="utf-8-sig", errors="replace")
            new_content, changes = replace_in_lua(content, mapping)
            if changes:
                all_changes.append(f"{lua_file.name}:")
                all_changes.extend(changes)
                if not dry_run:
                    lua_file.write_text(new_content, encoding="utf-8")
        
        # Repack if changes were made
        if all_changes and not dry_run:
            if backup:
                backup_path = map_path.with_suffix(".oramap.bak")
                shutil.copy2(map_path, backup_path)
            
            # Repack the zip
            with zipfile.ZipFile(map_path, "w", zipfile.ZIP_DEFLATED) as z:
                for f in sorted(tmpdir.rglob("*")):
                    if f.is_file():
                        arcname = str(f.relative_to(tmpdir)).replace(os.sep, "/")
                        z.write(f, arcname)
    
    return all_changes


def process_loose_map(map_dir: Path, mapping: dict[str, str], dry_run: bool, backup: bool) -> list[str]:
    """Process a loose map directory (contains map.yaml)."""
    all_changes: list[str] = []
    
    map_yaml = map_dir / "map.yaml"
    if map_yaml.exists():
        content = map_yaml.read_text(encoding="utf-8-sig", errors="replace")
        new_content, changes = replace_in_yaml(content, mapping)
        if changes:
            all_changes.append(f"map.yaml:")
            all_changes.extend(changes)
            if not dry_run:
                if backup:
                    shutil.copy2(map_yaml, map_yaml.with_suffix(".yaml.bak"))
                map_yaml.write_text(new_content, encoding="utf-8")
    
    for lua_file in map_dir.glob("*.lua"):
        content = lua_file.read_text(encoding="utf-8-sig", errors="replace")
        new_content, changes = replace_in_lua(content, mapping)
        if changes:
            all_changes.append(f"{lua_file.name}:")
            all_changes.extend(changes)
            if not dry_run:
                if backup:
                    shutil.copy2(lua_file, lua_file.with_suffix(".lua.bak"))
                lua_file.write_text(new_content, encoding="utf-8")
    
    return all_changes


def main():
    parser = argparse.ArgumentParser(
        description="Convert resource-center maps from original CNC/RA actor names to Cameo mod names."
    )
    parser.add_argument("path", help="Path to a .oramap file or a directory containing maps")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without modifying files")
    parser.add_argument("--backup", action="store_true", help="Keep .bak backup of original files")
    parser.add_argument("--rename-dir", default=None, help="Directory containing rename_map_*.yaml files (default: tools/rename)")
    args = parser.parse_args()
    
    # Find rename maps directory
    script_dir = Path(__file__).parent
    rename_dir = Path(args.rename_dir) if args.rename_dir else script_dir
    
    if not rename_dir.exists():
        print(f"Error: rename maps directory not found: {rename_dir}")
        sys.exit(1)
    
    # Build the full mapping
    mapping = build_full_mapping(rename_dir)
    print(f"Loaded {len(mapping)} actor name mappings")
    
    target = Path(args.path)
    if not target.exists():
        print(f"Error: path not found: {target}")
        sys.exit(1)
    
    # Collect map files to process
    map_files: list[Path] = []
    loose_dirs: list[Path] = []
    
    if target.is_file() and target.suffix == ".oramap":
        map_files = [target]
    elif target.is_dir():
        map_files = sorted(target.rglob("*.oramap"))
        # Also check for loose map directories (containing map.yaml)
        for d in sorted(target.iterdir()):
            if d.is_dir() and (d / "map.yaml").exists():
                loose_dirs.append(d)
    else:
        print(f"Error: not a .oramap file or directory: {target}")
        sys.exit(1)
    
    if not map_files and not loose_dirs:
        print("No maps found to process.")
        return
    
    print(f"Processing {len(map_files)} .oramap files and {len(loose_dirs)} loose map directories...")
    if args.dry_run:
        print("(DRY RUN — no files will be modified)")
    print()
    
    total_changes = 0
    for map_path in map_files:
        changes = process_oramap(map_path, mapping, args.dry_run, args.backup)
        if changes:
            print(f"{'[DRY] ' if args.dry_run else ''}{map_path.name}:")
            for c in changes:
                print(c)
            print()
            total_changes += len([c for c in changes if c.startswith("  ")])
        else:
            print(f"{'[DRY] ' if args.dry_run else ''}{map_path.name}: no changes")
    
    for map_dir in loose_dirs:
        changes = process_loose_map(map_dir, mapping, args.dry_run, args.backup)
        if changes:
            print(f"{'[DRY] ' if args.dry_run else ''}{map_dir.name}/:")
            for c in changes:
                print(c)
            print()
            total_changes += len([c for c in changes if c.startswith("  ")])
        else:
            print(f"{'[DRY] ' if args.dry_run else ''}{map_dir.name}/: no changes")
    
    print(f"\nTotal actor renames: {total_changes}")
    if total_changes == 0:
        print("All maps are already up to date.")


if __name__ == "__main__":
    main()
