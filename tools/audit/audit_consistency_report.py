#!/usr/bin/env python
"""audit_consistency_report.py — verify the fixes documented in
docs/audit/CONSISTENCY_REPORT.md are still in place.

This audit checks that the specific corrections made during the
2026-07-16 consistency check have not been regressed. Each check
corresponds to a numbered item in CONSISTENCY_REPORT.md.

Exit code 0 = all checks pass; 1 = one or more regressions detected.
"""
import os
import re
import sys

root = os.path.join(os.path.dirname(__file__), "..", "..")
failures = []
passes = 0


def check_file_contains(rel_path, needle, description, case_sensitive=True):
    """Check that a file contains a specific string."""
    global passes
    fpath = os.path.join(root, rel_path)
    try:
        content = open(fpath, encoding="utf-8").read()
    except FileNotFoundError:
        failures.append(f"[{description}] File missing: {rel_path}")
        return
    haystack = content if case_sensitive else content.lower()
    n = needle if case_sensitive else needle.lower()
    if n in haystack:
        passes += 1
    else:
        failures.append(f"[{description}] Expected '{needle[:60]}...' in {rel_path} — NOT FOUND")


def check_file_not_contains(rel_path, needle, description, case_sensitive=True):
    """Check that a file does NOT contain a specific string."""
    global passes
    fpath = os.path.join(root, rel_path)
    try:
        content = open(fpath, encoding="utf-8").read()
    except FileNotFoundError:
        failures.append(f"[{description}] File missing: {rel_path}")
        return
    haystack = content if case_sensitive else content.lower()
    n = needle if case_sensitive else needle.lower()
    if n not in haystack:
        passes += 1
    else:
        failures.append(f"[{description}] Stale value '{needle[:60]}...' still in {rel_path}")


def check_regex_not_match(rel_path, pattern, description):
    """Check that no line in a file matches a regex."""
    global passes
    fpath = os.path.join(root, rel_path)
    try:
        content = open(fpath, encoding="utf-8").read()
    except FileNotFoundError:
        failures.append(f"[{description}] File missing: {rel_path}")
        return
    if re.search(pattern, content):
        failures.append(f"[{description}] Regex /{pattern}/ still matches in {rel_path}")
    else:
        passes += 1


# ── Category 1: Naming convention drift ──────────────────────────────

# 1. ROADMAP WPN-MIGRATE uses _AA (uppercase) and includes _EMP
check_file_contains("docs/design/ROADMAP.md", "append `_AA`",
    "1: ROADMAP WPN-MIGRATE _AA uppercase")
check_file_contains("docs/design/ROADMAP.md", "append `_EMP`",
    "1: ROADMAP WPN-MIGRATE _EMP present")
# Ensure no lowercase _aa in WPN-MIGRATE context
check_regex_not_match("docs/design/ROADMAP.md",
    r"AA variants append `_aa`", "1: ROADMAP no lowercase _aa")

# 2. garrison_exceptions.yaml uses ra1_soviets_cyberdog (plural)
check_file_contains("docs/design/garrison_exceptions.yaml",
    "ra1_soviets_cyberdog", "2: garrison_exceptions plural soviets")
check_file_not_contains("docs/design/garrison_exceptions.yaml",
    "ra1_soviet_cyberdog", "2: garrison_exceptions no singular soviet")

# 3. MASTER_REPORT uses ra1_soviets (plural)
check_file_contains("docs/history/MASTER_REPORT_2026-07-08.md", "ra1_soviets_*",
    "3: MASTER_REPORT plural soviets")
check_file_not_contains("docs/history/MASTER_REPORT_2026-07-08.md", "ra1_soviet_*",
    "3: MASTER_REPORT no singular soviet")

# 4. ROADMAP E3 has deprecation note about E suffix
check_file_contains("docs/design/ROADMAP.md",
    "suffix convention has been superseded",
    "4: ROADMAP E3 deprecation note present")

# ── Category 2: Audit script scope mismatch ──────────────────────────

# 5. audit_missing_elite.py checks GainsExperienceRA2 only
check_file_contains("tools/audit/audit_missing_elite.py",
    "GainsExperienceRA2", "5: audit_missing_elite RA2-only scope")
check_file_not_contains("tools/audit/audit_missing_elite.py",
    "'GainsExperience' in stripped",
    "5: audit_missing_elite no broad GainsExperience check")

# 6. audit_faction_leaks.py has correct RA1/RA2 aliases
check_file_contains("tools/audit/audit_faction_leaks.py",
    '"ra1_soviets"', "6: faction_leaks RA1 soviets plural")
check_file_contains("tools/audit/audit_faction_leaks.py",
    '"ra2_allies"', "6: faction_leaks RA2 ra2allies")
check_file_contains("tools/audit/audit_faction_leaks.py",
    '"ra2_soviets"', "6: faction_leaks RA2 ra2soviets")
check_file_not_contains("tools/audit/audit_faction_leaks.py",
    '"ra2america"', "6: faction_leaks no stale ra2america")
check_file_not_contains("tools/audit/audit_faction_leaks.py",
    '"ra2russia"', "6: faction_leaks no stale ra2russia")

# 7. audit_rank_decoration.py has Terran and Protoss entries
check_file_contains("tools/audit/audit_rank_decoration.py",
    "TerranRankDecoration", "7: rank_decoration Terran entry")
check_file_contains("tools/audit/audit_rank_decoration.py",
    "ProtossRankDecoration", "7: rank_decoration Protoss entry")

# 8. audit_weapon_uniqueness.py has _upgraded in VARIANT_SUFFIXES
check_file_contains("tools/audit/audit_weapon_uniqueness.py",
    '"_upgraded"', "8: weapon_uniqueness _upgraded present")

# ── Category 3: Stale roadmap claims ─────────────────────────────────

# 9. ROADMAP CABAL backup says "avatar, widow" not "legion, avatar"
check_file_contains("docs/design/ROADMAP.md",
    "avatar, widow", "9: ROADMAP CABAL backup corrected")
check_file_not_contains("docs/design/ROADMAP.md",
    "legion, avatar", "9: ROADMAP no stale legion reference")

# 10. ROADMAP SC-RANKS has bug note on the [x] entry
check_file_contains("docs/design/ROADMAP.md",
    "incorrectly applied `^AlienRankDecoration`",
    "10: ROADMAP SC-RANKS bug note present")

# 11. ROADMAP E1 has scope change note
check_file_contains("docs/design/ROADMAP.md",
    "audit script was updated to only flag",
    "11: ROADMAP E1 scope change note present")

# ── Category 4: Missing roadmap items ────────────────────────────────

# 12. ROADMAP has user-reported issues section
check_file_contains("docs/design/ROADMAP.md",
    "User-reported issues (2026-07-15",
    "12: ROADMAP user-reported issues section present")
check_file_contains("docs/design/ROADMAP.md",
    "ixian_koda_tank", "12: ROADMAP koda_tank crash present")
check_file_contains("docs/design/ROADMAP.md",
    "Repair drone not repairing", "12: ROADMAP repair drone present")
check_file_contains("docs/design/ROADMAP.md",
    "Tarantula firing offset", "12: ROADMAP tarantula offset present")
check_file_contains("docs/design/ROADMAP.md",
    "Artillery spider firing offset", "12: ROADMAP artillery spider offset present")
check_file_contains("docs/design/ROADMAP.md",
    "magicnuke explosion", "12: ROADMAP magicnuke explosion present")
check_file_contains("docs/design/ROADMAP.md",
    "interceptor.nax", "12: ROADMAP interceptor rename present")
check_file_contains("docs/design/ROADMAP.md",
    "drone.nax", "12: ROADMAP drone move present")
check_file_contains("docs/design/ROADMAP.md",
    "CABAL Obelisk range", "12: ROADMAP CABAL obelisk present")
check_file_contains("docs/design/ROADMAP.md",
    "Eliminator 800 overpowered", "12: ROADMAP eliminator 800 present")

# ── Category 5: Incomplete documentation ─────────────────────────────

# 13. DESIGN.md §1 variant list includes _EMP, _AA, _upgraded
check_file_contains("docs/DESIGN.md", "_EMP _AA _upgraded",
    "13: DESIGN.md variant list complete")

# 14. MASTER_REPORT variant list includes new suffixes
check_file_contains("docs/history/MASTER_REPORT_2026-07-08.md", "_EMP",
    "14a: MASTER_REPORT variant _EMP")
check_file_contains("docs/history/MASTER_REPORT_2026-07-08.md", "_AA",
    "14b: MASTER_REPORT variant _AA")
check_file_contains("docs/history/MASTER_REPORT_2026-07-08.md", "_upgraded",
    "14c: MASTER_REPORT variant _upgraded")

# 15. backlog_weapon_rename.md has new variant markers
check_file_contains("docs/history/backlog_weapon_rename.md",
    "_EMP", "15a: backlog_weapon_rename _EMP")
check_file_contains("docs/history/backlog_weapon_rename.md",
    "_AA", "15b: backlog_weapon_rename _AA")
check_file_contains("docs/history/backlog_weapon_rename.md",
    "_upgraded", "15c: backlog_weapon_rename _upgraded")

# 16. audit README.md has the newer audit scripts
check_file_contains("tools/audit/README.md",
    "audit_weapon_uniqueness.py", "16a: README weapon_uniqueness")
check_file_contains("tools/audit/README.md",
    "audit_balance_sheet.py", "16b: README balance_sheet")
check_file_contains("tools/audit/README.md",
    "audit_weapon_suffixes.py", "16c: README weapon_suffixes")
check_file_contains("tools/audit/README.md",
    "audit_missing_elite.py", "16d: README missing_elite")
check_file_contains("tools/audit/README.md",
    "audit_rank_decoration.py", "16e: README rank_decoration")

# 17. run_all.sh includes balance_sheet
check_file_contains("tools/audit/run_all.sh",
    "balance_sheet", "17: run_all.sh balance_sheet present")

# 18. run_all.sh includes createeffect_image and ce_image_usage
check_file_contains("tools/audit/run_all.sh",
    "createeffect_image", "18a: run_all.sh createeffect_image present")
check_file_contains("tools/audit/run_all.sh",
    "ce_image_usage", "18b: run_all.sh ce_image_usage present")

# ── Category 6: Cross-document consistency invariants ────────────────

# Suffix ordering: _EMP_AA_elite (EMP before AA, elite always last)
check_file_contains("docs/DESIGN.md", "_EMP_AA_elite",
    "C1: DESIGN.md suffix ordering _EMP_AA_elite")

# ra1_soviets (plural) in DESIGN.md
check_file_contains("docs/DESIGN.md", "ra1_soviets",
    "C2: DESIGN.md ra1_soviets plural")

# cabal_legion_backup does NOT exist in tiberiansun.yaml
check_file_not_contains("mods/cameo/rules/tiberiansun.yaml",
    "cabal_legion_backup", "C3: no cabal_legion_backup actor")

# cabal_widow_backup exists (migrated to CABAL content pack)
check_file_contains("mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/husks.yaml",
    "cabal_widow_backup", "C4: cabal_widow_backup actor exists")

# cabal_artilleryspider_backup has Repairable trait
check_file_contains("mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/husks.yaml",
    "cabal_artilleryspider_backup", "C5: cabal_artilleryspider_backup exists")

# ── Category C6-C8: Faction InternalName ↔ actor prefix consistency ──

# C6: TD faction InternalNames match actor prefixes
check_file_contains("mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/faction.yaml",
    "InternalName: td_gdi", "C6: TD GDI InternalName is td_gdi")
check_file_not_contains("mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/faction.yaml",
    "InternalName: gdi", "C6: TD GDI no stale InternalName: gdi")
check_file_contains("mods/cameo/ContentPacks/TiberianDawn/Nod/yaml/faction.yaml",
    "InternalName: td_nod", "C6: TD Nod InternalName is td_nod")

# C7: RA1/RA2 faction InternalNames match actor prefixes (migrated to ContentPacks)
check_file_contains("mods/cameo/ContentPacks/RedAlert/Shared/yaml/faction.yaml",
    "InternalName: ra1_allies", "C7: RA1 allies InternalName is ra1_allies")
check_file_contains("mods/cameo/ContentPacks/RedAlert/Shared/yaml/faction.yaml",
    "InternalName: ra1_soviets", "C7: RA1 soviets InternalName is ra1_soviets")
check_file_contains("mods/cameo/rules/redalert2.yaml",
    "InternalName: ra2_allies", "C7: RA2 allies InternalName is ra2_allies")
check_file_contains("mods/cameo/rules/redalert2.yaml",
    "InternalName: ra2_soviets", "C7: RA2 soviets InternalName is ra2_soviets")

# C8: TS faction InternalNames match actor prefixes
check_file_contains("mods/cameo/rules/tiberiansun.yaml",
    "InternalName: ts_gdi", "C8: TS GDI InternalName is ts_gdi")
check_file_contains("mods/cameo/rules/tiberiansun.yaml",
    "InternalName: ts_nod", "C8: TS Nod InternalName is ts_nod")

# C9: WC2 faction InternalNames and actor prefixes
check_file_contains("mods/cameo/rules/warcraft2.yaml",
    "InternalName: wc2_humans", "C9: WC2 humans InternalName is wc2_humans")
check_file_contains("mods/cameo/rules/warcraft2.yaml",
    "InternalName: wc2_orcs", "C9: WC2 orcs InternalName is wc2_orcs")
check_file_not_contains("mods/cameo/rules/warcraft2.yaml",
    "warcraft_humans_", "C9: no stale warcraft_humans_ prefix in rules")
check_file_not_contains("mods/cameo/rules/warcraft2.yaml",
    "warcraft_orcs_", "C9: no stale warcraft_orcs_ prefix in rules")
check_file_not_contains("mods/cameo/sequences/warcraft2.yaml",
    "warcraft_humans_", "C9: no stale warcraft_humans_ prefix in sequences")
check_file_not_contains("mods/cameo/sequences/warcraft2.yaml",
    "warcraft_orcs_", "C9: no stale warcraft_orcs_ prefix in sequences")

# C10: RA2 mod faction InternalNames
check_file_contains("mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/faction.yaml",
    "InternalName: asianalliance", "C10: AsianAlliance InternalName is asianalliance")
check_file_contains("mods/cameo/ContentPacks/RedAlert2Mod/Consortium/yaml/faction.yaml",
    "InternalName: steelconsortium", "C10: Consortium InternalName is steelconsortium")
check_file_contains("mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/faction.yaml",
    "InternalName: latinsyndicate", "C10: Syndicate InternalName is latinsyndicate")

# C11: No underscores within faction names (underscores separate sections only)
check_file_not_contains("mods/cameo/rules/defaults.yaml",
    "asian_alliance_", "C11: no asian_alliance_ in defaults (should be asianalliance_)")
check_file_not_contains("mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/faction.yaml",
    "asian_alliance", "C11: no asian_alliance in AsianAlliance faction yaml")
check_file_not_contains("mods/cameo/sequences/redalert2mod.yaml",
    "asian_alliance_", "C11: no asian_alliance_ in sequences")

# ── Report ───────────────────────────────────────────────────────────

print("# Consistency report audit (CONSISTENCY_REPORT.md)\n")
print(f"Checks passed: **{passes}**")
print(f"Checks failed: **{len(failures)}**\n")

if failures:
    print("## Regressions detected\n")
    print("| # | Description |")
    print("|---|---|")
    for i, f in enumerate(failures, 1):
        print(f"| {i} | {f} |")
    print()
    sys.exit(1)
else:
    print("All consistency fixes from CONSISTENCY_REPORT.md are still in place.\n")
    sys.exit(0)
