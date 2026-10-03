#!/usr/bin/env python3
"""audit_weapon_suffixes.py — DESIGN.md §1 weapon suffix detector.

Checks that weapon IDs follow the suffix conventions documented in
DESIGN.md §1:

  X1 Elite weapons: must end with _elite (legacy E suffix is deprecated)
     — only checks weapons referenced by Armament@*ELITE* blocks gated
     by RequiresCondition: rank-elite. Non-elite weapons that happen to
     end with E (e.g. PrismChargeE, EMP weapons) are NOT flagged.

  X2 EMP weapons: weapons whose name contains EMP (case-insensitive)
     but do NOT end with _EMP. These should be renamed to use the _EMP
     suffix. Excludes weapons that are sub-variants (e.g. _AA, _elite,
     _fire, Fragment, Arc, TeslaFragment) — only the base EMP weapon
     is flagged.

  X3 AA weapons: weapons that are the air-only sibling of a dual-weapon
     actor/template (e.g. an Anti-Air Tank with both a ground cannon and
     an AA missile, equipped via two separate Armament traits) whose name
     does not end with _AA (or _aa). Standalone AA-only weapons with no
     ground-capable sibling on the same actor (e.g. a SAM Site with a
     single weapon) are intentionally NOT flagged — the _AA suffix marks
     the air-only half of a pair, not merely "targets Air". Also excludes
     weapons whose base name already contains "Flak", "SAM",
     "Interceptor", "Patriot" (legacy naming that predates the
     convention).

  X4 Deprecated E suffix: weapons ending with capital E that are NOT
     elite variants (not gated by rank-elite) and NOT EMP weapons.
     These are likely either legacy elite weapons that need _elite
     migration, or coincidental E endings. Reported as informational.

  X5 Suffix ordering: weapons whose name contains two or more of
     `_EMP`, `_AA`, `_elite` but not in the canonical order
     `<base>_<doctrine/upgrade/variant>_EMP_AA_elite`. Per DESIGN.md §1,
     `_EMP` must come before `_AA`, and `_elite` must always be last.
"""

import os
import re
import sys

root = sys.argv[1] if len(sys.argv) > 1 else "mods/cameo"

# Suffixes that indicate a sub-variant of an EMP weapon — not the base
EMP_SUBVARIANT_SUFFIXES = (
    "_AA", "_aa", "_elite", "_fire", "_AG", "_G", "_Structure",
    "_Garrisoned", "_air", "_end", "_anim",
    "Fragment", "Arc", "TeslaFragment", "Missile", "Defender",
    "Patriot", "Mig", "Bomb",
)

# Full words legitimately ending in E — not a deprecated suffix marker.
# X4 is informational only, but these are common enough to be worth
# filtering out as noise.
X4_WHOLE_WORD_EXCLUSIONS = (
    "NUKE", "ZOMBIE", "CRATE", "ELITE", "GRENADE", "SMOKE", "STRIKE",
    # "HE" = High Explosive, an AMMUNITION type, not the deprecated elite `E`.
    # `SUSABurtonSniperHE` inherits `SUSABurtonSniper`, and `SUSAMLRSHE` sits
    # beside a correctly-suffixed `SUSAMLRS_EMP` — both were X4 false positives.
    # Safe because X4 only ever sees weapons that are NOT elite-gated.
    "HE",
)

# AA name keywords that predate the _AA convention.
# NOTE: bare "aa" is intentionally excluded — it would incorrectly
# exclude every weapon that already contains "AA" as a substring without
# a proper underscore (e.g. "SWAWingGunAA", "RA2HoverMissileAA_elite"),
# which is exactly the case X3 needs to catch and flag for correction.
AA_LEGACY_KEYWORDS = ("flak", "sam", "interceptor", "patriot",
                      "aagun", "aamissile", "aafortress")

# Weapons that target Air but also Ground/Water are dual-purpose, not AA variants
DUAL_PURPOSE_TARGETS = ("Ground", "Water", "Infantry", "Vehicle", "Building",
                        "Defense", "Structure", "Ship")

# Direct-child keys that only appear on weapon definitions, never on actors,
# sequences, upgrades, or promotions. Used to reject false-positive matches
# like `td_nod_templeofnod` or `raharvempty` (substring "emp" in an actor
# or sequence id, not an actual weapon).
WEAPON_MARKER_KEYS = (
    "ReloadDelay:", "Projectile:", "Warhead", "MinRange:", "ValidTargets:",
    "Report:", "Range:", "Burst:", "TargetActorCenter:", "Inaccuracy:",
)

# Direct-child keys that only appear on actors/sequences/upgrades — if any
# of these are present, the block is definitely NOT a weapon definition.
# NOTE: "Inherits:" is NOT included here — both weapons (Inherits: ^SmallArms)
# and actors (Inherits: ^TDBuilding) use the bare Inherits: syntax.
NON_WEAPON_MARKER_KEYS = (
    "Tooltip:", "Buildable:", "RenderSprites", "Health:",
    "Mobile:", "Armament", "Filename:", "Facings:",
)


def find_non_elite_armament_weapons(root: str) -> set:
    """Weapons referenced by any non-elite Armament block.

    Ruling 2 (Claude-Local, 2026-09-06): a numbered weapon that is a rung on a
    ladder shared across actors (e.g. AsianRailTank2 is railguntank's ELITE
    armament AND heavyrailguntank's PRIMARY) cannot take the `_elite` suffix
    without lying about the actor that fires it as its primary armament. X1
    therefore exempts an elite-gated weapon that is also referenced by a
    non-elite armament anywhere.
    """
    shared = set()
    for dirpath, _, filenames in os.walk(root):
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
                am = re.match(r'^\tArmament(@(\w+))?\s*:', line)
                if am and 'elite' not in (am.group(2) or '').lower():
                    j = i + 1
                    while j < len(lines):
                        bl = lines[j]
                        if re.match(r'^\t\S', bl) or re.match(r'^[^\t\s]', bl):
                            break
                        wref = re.match(r'^\t\tWeapon:\s*(\S+)', bl)
                        if wref:
                            shared.add(wref.group(1))
                        j += 1
                i += 1
    return shared


def is_weapon_definition_body(body_lines: list) -> bool:
    """Heuristic: does this top-level YAML block look like a weapon def?"""
    has_weapon_marker = False
    for bl in body_lines:
        stripped = bl.strip()
        if any(stripped.startswith(k) for k in NON_WEAPON_MARKER_KEYS):
            return False
        if any(stripped.startswith(k) for k in WEAPON_MARKER_KEYS):
            has_weapon_marker = True
    return has_weapon_marker


def parse_weapon_targets(root: str) -> dict:
    """Scan every weapon definition and return {name: [effective ValidTargets]},
    resolving ValidTargets through the Inherits chain when a weapon doesn't
    declare it directly (e.g. inherits it from a ^Template)."""
    direct_targets = {}
    inherits_of = {}
    weapon_names = set()

    for dirpath, _, filenames in os.walk(root):
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
                wm = re.match(r'^([A-Za-z^][A-Za-z0-9_.\-]*):\s*$', line)
                if wm and not line.startswith('\t') and not line.strip().startswith('#'):
                    block_name = wm.group(1)
                    j = i + 1
                    valid_targets = []
                    parents = []
                    body_lines = []
                    while j < len(lines):
                        bl = lines[j]
                        if re.match(r'^[^\t\s]', bl) and not bl.strip().startswith('#'):
                            break
                        body_lines.append(bl)
                        vtm = re.match(r'^\tValidTargets:\s*(.+)', bl)
                        if vtm:
                            valid_targets = [t.strip() for t in vtm.group(1).split(",")]
                        im = re.match(r'^\tInherits(?:@\w+)?:\s*(\S+)\s*$', bl)
                        if im:
                            parents.append(im.group(1))
                        j += 1
                    if valid_targets:
                        direct_targets[block_name] = valid_targets
                    if parents:
                        inherits_of[block_name] = parents
                    if not block_name.startswith('^') and is_weapon_definition_body(body_lines):
                        weapon_names.add(block_name)
                i += 1

    def resolve(name: str, visited: set) -> list:
        if name in visited:
            return []
        visited.add(name)
        if name in direct_targets:
            return direct_targets[name]
        for parent in inherits_of.get(name, []):
            resolved = resolve(parent, visited)
            if resolved:
                return resolved
        return []

    return {name: resolve(name, set()) for name in weapon_names}


ARMAMENT_HEADER_RE = re.compile(r'^\tArmament(@\w+)?:\s*$')
ARMAMENT_WEAPON_RE = re.compile(r'^\t\tWeapon:\s*(\S+)\s*$')


def find_actor_paired_air_only_weapons(root: str, weapon_targets: dict) -> set:
    """A weapon only qualifies for the `_AA` suffix if some actor/template
    equips it (via Armament) ALONGSIDE a separate ground-capable weapon —
    e.g. an Anti-Air Tank with both a ground cannon and an AA missile.
    Standalone AA-only weapons (SAM Sites, dedicated AA turrets with a
    single weapon) are intentionally excluded per the documented
    convention — see docs/DESIGN.md §1."""
    paired = set()
    for dirpath, _, filenames in os.walk(root):
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
                bm = re.match(r'^([A-Za-z^][A-Za-z0-9_.\-]*):\s*$', line)
                if bm and not line.startswith('\t') and not line.strip().startswith('#'):
                    j = i + 1
                    block_weapons = []
                    while j < len(lines):
                        bl = lines[j]
                        if re.match(r'^[^\t\s]', bl) and not bl.strip().startswith('#'):
                            break
                        if ARMAMENT_HEADER_RE.match(bl):
                            k = j + 1
                            while k < len(lines) and re.match(r'^\t\t\S', lines[k]):
                                wmatch = ARMAMENT_WEAPON_RE.match(lines[k])
                                if wmatch:
                                    block_weapons.append(wmatch.group(1))
                                k += 1
                        j += 1
                    air_only = []
                    ground_capable = []
                    for w in block_weapons:
                        targets = weapon_targets.get(w)
                        if targets is None:
                            continue
                        is_dual = any(t in targets for t in DUAL_PURPOSE_TARGETS)
                        if "Air" in targets and not is_dual:
                            air_only.append(w)
                        elif "Ground" in targets:
                            ground_capable.append(w)
                    if air_only and ground_capable:
                        paired.update(air_only)
                    i = j
                else:
                    i += 1
    return paired


_EMP_TOKEN_RE = re.compile(r'(?:^|_)EMP(?:_|$|[A-Z0-9])')


def is_emp_weapon(name: str) -> bool:
    """Check if a weapon name contains EMP as a distinct uppercase token
    (start-of-name, after underscore, or camelCase-bounded). Excludes
    substring false positives like `Emperor`, `Empty`, `Temple` where
    "emp" is embedded in mixed/lowercase inside a longer word."""
    return bool(_EMP_TOKEN_RE.search(name))


def is_emp_subvariant(name: str) -> bool:
    """Check if a weapon is a sub-variant of an EMP weapon."""
    for suffix in EMP_SUBVARIANT_SUFFIXES:
        if name.endswith(suffix):
            return True
    # Also check for patterns like TSCABALEMPDisable.anim / .end
    if "." in name:
        return True
    return False


def check_suffix_order(name: str) -> str | None:
    """Return a violation description if _EMP/_AA/_elite are out of order."""
    emp_pos = name.find("_EMP")
    aa_pos = name.find("_AA")
    elite_pos = name.rfind("_elite")

    positions = []
    if emp_pos != -1:
        positions.append(("_EMP", emp_pos))
    if aa_pos != -1:
        positions.append(("_AA", aa_pos))
    if elite_pos != -1:
        positions.append(("_elite", elite_pos))

    if len(positions) < 2:
        return None

    order = {"_EMP": 0, "_AA": 1, "_elite": 2}
    sorted_by_pos = sorted(positions, key=lambda p: p[1])
    actual_order = [p[0] for p in sorted_by_pos]
    expected_order = sorted(actual_order, key=lambda s: order[s])

    if actual_order != expected_order:
        return f"found order {'/'.join(actual_order)}, expected {'/'.join(expected_order)}"
    return None


def main() -> int:
    x1_rows = []  # elite weapons not ending _elite
    x2_rows = []  # EMP weapons not ending _EMP
    x3_rows = []  # AA weapons not ending _AA
    x4_rows = []  # deprecated E suffix (informational)
    x5_rows = []  # suffix ordering violations

    # Track which weapons are elite-gated (to exclude from X4)
    elite_weapons: set[str] = set()

    # X3 only flags the air-only sibling of a dual-weapon actor (e.g. an
    # Anti-Air Tank with both a ground cannon and an AA missile) — never a
    # standalone AA-only weapon (e.g. a SAM Site).
    weapon_targets = parse_weapon_targets(root)
    paired_air_only = find_actor_paired_air_only_weapons(root, weapon_targets)
    shared_rung_weapons = find_non_elite_armament_weapons(root)
    # Same ruling, one rung up: a weapon whose numbered siblings are shared
    # rungs (e.g. LatinMonkeyGrenade3 is only an elite weapon, but Grenade1/2
    # are the same actor's PRIMARY/SECONDARY) is still a rung of that ladder —
    # `_elite` would mislabel it identically.
    shared_rung_families = {
        re.sub(r'\d+$', '', w) for w in shared_rung_weapons
        if re.search(r'\d+$', w)
    }
    x1_shared_rung = 0  # elite-gated weapons exempt per Ruling 2 (shared rung)

    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if not fn.endswith(".yaml"):
                continue
            fpath = os.path.join(dirpath, fn)
            try:
                lines = open(fpath, encoding="utf-8").readlines()
            except Exception:
                continue

            # --- Parse weapon definitions ---
            i = 0
            while i < len(lines):
                line = lines[i]
                # Top-level weapon definition (no leading tab, not a comment)
                wm = re.match(r'^([A-Za-z][A-Za-z0-9_.\-]*):\s*$', line)
                if wm and not line.startswith('\t') and not line.strip().startswith('#'):
                    weapon_name = wm.group(1)

                    # Skip templates
                    if weapon_name.startswith('^'):
                        i += 1
                        continue

                    # Parse weapon body
                    j = i + 1
                    valid_targets = []
                    body_lines = []
                    while j < len(lines):
                        bl = lines[j]
                        if re.match(r'^[^\t\s]', bl) and not bl.strip().startswith('#'):
                            break
                        body_lines.append(bl)
                        vtm = re.match(r'^\tValidTargets:\s*(.+)', bl)
                        if vtm:
                            valid_targets = [t.strip() for t in vtm.group(1).split(",")]
                        j += 1

                    is_weapon = is_weapon_definition_body(body_lines)

                    # X2: EMP weapons not ending _EMP
                    if is_weapon and is_emp_weapon(weapon_name) and not is_emp_subvariant(weapon_name):
                        if not weapon_name.endswith('_EMP') and not weapon_name.endswith('_emp'):
                            short = fpath.replace("\\", "/").replace("mods/cameo/", "")
                            x2_rows.append((short, i + 1, weapon_name))

                    # X3: AA weapons not ending _AA — only the air-only
                    # sibling of a dual-weapon actor (see
                    # find_actor_paired_air_only_weapons); standalone
                    # AA-only weapons (SAM Sites, etc.) are intentionally
                    # excluded per the documented convention.
                    if is_weapon and weapon_name in paired_air_only:
                        has_legacy = any(kw in weapon_name.lower() for kw in AA_LEGACY_KEYWORDS)
                        if not has_legacy:
                            already_compliant = (
                                weapon_name.endswith('_AA') or weapon_name.endswith('_aa')
                                or '_AA_' in weapon_name or '_aa_' in weapon_name
                            )
                            if not already_compliant:
                                short = fpath.replace("\\", "/").replace("mods/cameo/", "")
                                x3_rows.append((short, i + 1, weapon_name, ", ".join(valid_targets)))

                    # X4: Deprecated E suffix (not elite, not EMP)
                    if is_weapon and weapon_name.endswith('E') and not weapon_name.endswith('_E'):
                        if weapon_name not in elite_weapons and not is_emp_weapon(weapon_name):
                            # Exclude common non-weapon patterns and whole
                            # words that legitimately end in E
                            is_whole_word = any(
                                weapon_name.upper().endswith(w) for w in X4_WHOLE_WORD_EXCLUSIONS
                            )
                            if not weapon_name.endswith(('ChargeE', 'ScatterE')) and not is_whole_word:
                                short = fpath.replace("\\", "/").replace("mods/cameo/", "")
                                x4_rows.append((short, i + 1, weapon_name))

                    # X5: Suffix ordering violations
                    if is_weapon:
                        order_issue = check_suffix_order(weapon_name)
                        if order_issue:
                            short = fpath.replace("\\", "/").replace("mods/cameo/", "")
                            x5_rows.append((short, i + 1, weapon_name, order_issue))

                # --- Parse Armament@*ELITE* blocks for X1 ---
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
                        # RequiresCondition matching: `rank-elite` must appear
                        # UNnegated — `!rank-elite && upgrade` marks a
                        # NON-elite (upgrade) armament, not an elite one
                        # (steelconsortium_megalodon's Armament@ELITE was a
                        # false positive this way).
                        for mm in re.finditer(r'rank-elite', bl.lower()):
                            if mm.start() == 0 or bl.lower()[mm.start() - 1] != '!':
                                has_rank_elite = True
                                break
                        j += 1
                    if weapon_ref and has_rank_elite:
                        elite_weapons.add(weapon_ref)
                        if weapon_ref.endswith('_elite'):
                            pass
                        elif (weapon_ref in shared_rung_weapons
                              or re.sub(r'\d+$', '', weapon_ref) in shared_rung_families
                              and re.search(r'\d+$', weapon_ref)):
                            x1_shared_rung += 1
                        else:
                            actor_name = "?"
                            for k in range(i - 1, -1, -1):
                                actm = re.match(r'^(\S+):', lines[k])
                                if actm and not lines[k].startswith('\t') and not lines[k].strip().startswith('#'):
                                    actor_name = actm.group(1)
                                    break
                            trait_name = am.group(0).strip().rstrip(':')
                            short = fpath.replace("\\", "/").replace("mods/cameo/", "")
                            x1_rows.append((short, i + 1, actor_name, trait_name, weapon_ref))

                i += 1

    # Re-scan X4 now that we know which weapons are elite-gated
    # (already filtered during first pass via elite_weapons set, but
    #  some elite weapons may be defined after their armament ref)

    print("# Weapon suffix audit (DESIGN.md §1)\n")
    print(f"X1 elite weapons not ending _elite: **{len(x1_rows)}**"
          f" (+{x1_shared_rung} exempt shared-rung weapons, Ruling 2)")
    print(f"X2 EMP weapons not ending _EMP: **{len(x2_rows)}**")
    print(f"X3 AA weapons not ending _AA: **{len(x3_rows)}**")
    print(f"X4 deprecated E suffix (informational): **{len(x4_rows)}**")
    print(f"X5 suffix ordering violations: **{len(x5_rows)}**\n")

    if x1_rows:
        print("## X1 — Elite weapons not following _elite convention")
        print("| File | Line | Actor | Trait | Weapon |")
        print("|---|---|---|---|---|")
        for fpath, line, actor, trait, weapon in sorted(x1_rows):
            print(f"| {fpath} | {line} | {actor} | {trait} | {weapon} |")
        print()

    if x2_rows:
        print("## X2 — EMP weapons not following _EMP convention")
        print("| File | Line | Weapon |")
        print("|---|---|---|")
        for fpath, line, weapon in sorted(x2_rows):
            print(f"| {fpath} | {line} | {weapon} |")
        print()

    if x3_rows:
        print("## X3 — AA-only weapons not following _AA convention")
        print("| File | Line | Weapon | ValidTargets |")
        print("|---|---|---|---|")
        for fpath, line, weapon, vt in sorted(x3_rows):
            print(f"| {fpath} | {line} | {weapon} | {vt} |")
        print()

    if x4_rows:
        print("## X4 — Weapons with deprecated E suffix (informational)")
        print("| File | Line | Weapon |")
        print("|---|---|---|")
        for fpath, line, weapon in sorted(x4_rows):
            print(f"| {fpath} | {line} | {weapon} |")
        print()

    if x5_rows:
        print("## X5 — Suffix ordering violations (expected `_EMP_AA_elite`)")
        print("| File | Line | Weapon | Issue |")
        print("|---|---|---|---|")
        for fpath, line, weapon, issue in sorted(x5_rows):
            print(f"| {fpath} | {line} | {weapon} | {issue} |")
        print()

    return 1 if x1_rows else 0


if __name__ == "__main__":
    sys.exit(main())
