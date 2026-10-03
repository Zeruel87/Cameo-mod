#!/usr/bin/env python3
"""Extract raw Emperor: Battle for Dune unit stats from an archived Rules.txt into JSON.

    python tools/reference/extract_emperor_units.py --source <Rules.txt> --out <external.json>
    python tools/reference/extract_emperor_units.py --source <Rules.txt> --out -   # stdout
    python tools/reference/extract_emperor_units.py --source <Rules.txt> --dry-run

`--source` and `--out` are REQUIRED; there are no personal-path defaults. The
output must be stdout or a path OUTSIDE this repository and outside the
source tree; creation is EXCLUSIVE (an existing file is never overwritten —
identical content is a no-op, differing content is a refusal).

SCOPE AND HONESTY CONTRACT
--------------------------
* The source is a single archived `Rules.txt` downloaded from
  https://dune2k.com/Download/15. Its own `[General] Version = 1.23` is a FILE
  label — recorded, never claimed as an established retail patch
  (`archived-original/unverified patch` in provenance). The file header
  self-describes as an example demonstrating the building/unit hierarchies
  and the Group mechanism; that caveat travels with the data.
* Native values only: Cost, BuildTime, Health, Speed, TurnRate, ReloadCount,
  bullet Damage / MaxRange / MinRange / Speed are copied verbatim. There is
  **no** seconds/DPS conversion, no armor interpolation, no Cameo routing, no
  pricing. `Armour = None, 50, InfRock` triples are recorded RAW — the
  meaning of the middle/last tokens is NOT interpreted anywhere. The source
  is parsed as text, never executed.
* Inheritance/group/type: Emperor has no per-unit inheritance keyword. The
  hierarchy is (a) ordered DECLARATION sections — `[UnitTypes]`,
  `[TurretTypes]`, `[BulletTypes]`, `[WarheadTypes]` repeat through the file
  and APPEND in file order (the source's own comment marks the tail additions
  as save-game-order-sensitive) — and (b) named groups (`UnitGroupTypes`,
  `BuildingGroupTypes`) that stop icon duplication. Both are extracted
  explicitly; a declared type with no definition section is an issue, a
  definition with no declaration is an issue, and nothing is silently
  flattened.
* Weapon variants are NOT flattened. `TurretAttach = A, B` yields one weapon
  variant per turret ref, each keeping its own Bullet ref, ReloadCount,
  turret params and resolved bullet stats (Damage/MaxRange/Warhead/Versus
  rows). Commented-out `Bullet =` lines are recorded as unresolved refs, not
  as data.
* Buildability is NEVER proven by `Cost > 0` alone: the rule requires a
  `PrimaryBuilding` as well, so priced story/incidental units (e.g. an
  Incidental-house unit with `Cost = 850` and no production building) come
  out non-buildable with the rule that fired recorded on the record.
* MCV/harvester(+carryall) records are manual_review_only, never
  balance-eligible; palace superweapon units (DeathHand / BeamWeapon /
  HawkWeapon) are collection-only. `AiSpecial` alone does NOT mark a
  superweapon — normal units carry it too.
* NO record is certified balance-eligible. Every record is a **reference
  collection candidate only** (`collection_candidate: true`); a
  `buildable_candidate` is production EVIDENCE from the archive, not
  certification — its `balance_eligible` stays null because the version label
  is unverified and activation context (palace triggers, starport, skirmish
  gating) is not in this file.
* Repeated veterancy-level keys (Health/ExtraDamage/... under
  VeterancyLevel blocks) are the archive's EXPECTED shape: categorized
  contextually as `repeated_level_field` with every raw occurrence kept in
  `repeated_level_values` — nothing hidden; `conflicting_key` is reserved for
  genuinely conflicting repeats outside that context.
* Output is deterministic (no timestamps, sorted keys); source hashes are
  taken BEFORE and AFTER the parse to prove the raw original was never
  modified; no copyrighted source text is copied into this repository (tests
  use synthetic fixtures only; real-source integration tests are opt-in via
  the `CAMEO_REFERENCE_RAW_SOURCES` environment variable, never a personal
  path).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXPECTED_SHA256 = "A1DE5044AEBC837D439892A081674CEB919007B87887ABDF999CF099FF5F692D"
SOURCE_URL = "https://dune2k.com/Download/15"

SCHEMA_VERSION = 1

DECLARATION_SECTIONS = {
    "HouseTypes", "TerrainTypes", "ArmourTypes", "ExplosionTypes",
    "SpiceMoundTypes", "SplatTypes", "CrateTypes", "DebrisTypes",
    "WarheadTypes", "BulletTypes", "BuildingGroupTypes", "BuildingTypes",
    "UnitGroupTypes", "UnitTypes", "TurretTypes",
}
UNIT_DECL_SECTION = "UnitTypes"
TURRET_DECL_SECTION = "TurretTypes"
BULLET_DECL_SECTION = "BulletTypes"
WARHEAD_DECL_SECTION = "WarheadTypes"

SUPERWEAPON_FLAGS = ("DeathHand", "BeamWeapon", "HawkWeapon")
ECONOMY_FLAGS = {"Harvester": "economy_unit", "MCV": "economy_unit",
                 "Carryall": "transport_unit"}
WORM_FLAG = "Worm"
TRANSPORT_NAMES = {"Frigate", "StuntFrigate"}
STORM_NAMES = {"StormUnit"}

BULLET_NUMERIC = ("Damage", "MaxRange", "MinRange", "Speed", "BlastRadius",
                  "FriendlyDamageAmount")
BULLET_BOOL = ("Homing", "AntiAircraft", "AntiGround", "Trajectory", "BlowUp")


# ── A tolerant Emperor-INI section parser ────────────────────────────────────

def parse_ini(text: str, issues: list):
    """[{name, pairs, comments, line}, ...]

    * `//` comments (full-line and inline) are stripped from values.
    * Full-line comments are kept per section in `comments` (stripped of the
      leading `//`) — declaration sections need them, because a commented-out
      declaration names a real unit this file does NOT define.
    * Section headers may be indented and may carry a trailing comment.
    * Repeated KEYS are kept in order (VeterancyLevel blocks depend on it).
    * Lines without `=` (e.g. two-token directives) are kept with
      implicit=True — never dropped, never guessed into a shape.
    """
    sections = []
    current = None

    def flush():
        nonlocal current
        if current is not None:
            sections.append(current)
        current = None

    for line_no, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if stripped.startswith("//") or not stripped:
            if current is not None and stripped.startswith("//"):
                current["comments"].append(
                    {"line": line_no, "text": stripped[2:].strip()})
            continue
        line = raw.split("//", 1)[0].strip()
        if not line:
            # inline-only comment line like `code //comment`
            continue
        if line.startswith("["):
            name = line[1:].split("]", 1)[0].strip()
            flush()
            current = {"name": name, "pairs": [], "comments": [], "line": line_no}
            continue
        if current is None:
            issues.append({"severity": "malformed_source",
                           "detail": f"line {line_no}: key line outside any section",
                           "line": line_no})
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            current["pairs"].append((key.strip(), value.strip(), False, line_no))
        else:
            parts = line.split(None, 1)
            key = parts[0]
            value = parts[1] if len(parts) > 1 else ""
            current["pairs"].append((key, value, True, line_no))
    flush()
    return sections


# ── Declaration handling ─────────────────────────────────────────────────────

def collect_declarations(sections, issues):
    """Declaration lists per section kind, in file order.

    Returns {kind: {"entries": [(name, line_no)], "commented": [(name, text,
    line_no)], "batches": n}}. Commented-out declaration lines are recovered
    from the section's comments: a full-line comment whose first token is a
    bare identifier inside a declaration section names a type this file does
    NOT define (real units — Scout, Thumper, Scavenger — are shipped that
    way). They are recorded as data-absence markers, never as stats.
    """
    declared: dict = {}
    _IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")
    for section in sections:
        kind = section["name"]
        if kind not in DECLARATION_SECTIONS:
            continue
        bucket = declared.setdefault(
            kind, {"entries": [], "commented": [], "batches": 0})
        bucket["batches"] += 1
        for key, value, implicit, line_no in section["pairs"]:
            if not implicit:
                issues.append({"severity": "malformed_declaration",
                               "detail": f"[{kind}] line {line_no}: {key} = {value}"})
                continue
            bucket["entries"].append((key, line_no))
        for comment in section["comments"]:
            head = comment["text"].split("//", 1)[0].strip()
            if head and _IDENT_RE.match(head):
                bucket["commented"].append(
                    {"name": head, "text": comment["text"], "line": comment["line"]})
    return declared


def first_section_map(sections, declared_names, issues):
    """{name: section} for DEFINITION sections whose name is a declared type.

    Duplicate definition sections are an issue (first occurrence kept,
    all occurrences counted) — the source contains several (e.g. fx
    sections declared twice) and silently merging them would fabricate data.
    """
    out: dict = {}
    occurrences: dict = {}
    for section in sections:
        name = section["name"]
        if name in DECLARATION_SECTIONS:
            continue
        occurrences.setdefault(name, []).append(section["line"])
        if name in out:
            issues.append({"severity": "duplicate_section",
                           "detail": f"[{name}] redefined at line "
                                     f"{section['line']}; first definition kept"})
            continue
        if name in declared_names:
            out[name] = section
    # Sections that are neither declarations nor declared types are simply not
    # records; but a declared type with NO definition is an issue.
    for name in sorted(declared_names):
        if name not in out:
            issues.append({"severity": "dangling_declaration",
                           "detail": f"declared type {name!r} has no definition section"})
    return out, occurrences


# ── Field helpers ────────────────────────────────────────────────────────────

def _int(value):
    try:
        return int(str(value), 0)
    except (TypeError, ValueError):
        return None


def _num(value):
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _bool(value):
    low = str(value).strip().lower()
    if low in ("true", "1"):
        return True
    if low in ("false", "0"):
        return False
    return None


def raw_list(value):
    return [t.strip() for t in str(value).split(",") if t.strip()]


# ── Weapon chain: TurretAttach -> turret -> bullet -> warhead ────────────────

def resolve_weapon_variant(turret_ref, turret_map, bullet_map, warhead_map,
                           armour_types, unit_id, issues):
    variant = {
        "turret": turret_ref,
        "turret_found": turret_ref in turret_map,
        "turret_params": {},
        "bullet": None,
        "bullet_found": False,
        "reload_count": None,
        "bullet_commented_out": False,
        "damage": None,
        "max_range": None,
        "min_range": None,
        "bullet_speed": None,
        "blast_radius": None,
        "friendly_damage_amount": None,
        "homing": None,
        "anti_aircraft": None,
        "anti_ground": None,
        "trajectory": None,
        "warhead": None,
        "versus": {},
        "turret_next_joint": None,
        "range_semantics": "native MaxRange in tiles (unconverted)",
        "reload_semantics": "native ReloadCount ticks (unconverted)",
    }
    turret = turret_map.get(turret_ref)
    if turret is None:
        issues.append({"severity": "unresolved_ref",
                       "detail": f"{unit_id}: TurretAttach {turret_ref!r} has no "
                                 "[TurretTypes] section"})
        return variant
    values: dict = {}
    for key, value, _implicit, _line in turret["pairs"]:
        values.setdefault(key, value)
    variant["reload_count"] = _int(values.get("ReloadCount"))
    if variant["reload_count"] is None:
        issues.append({"severity": "missing_field",
                       "detail": f"turret {turret_ref!r} has no ReloadCount"})
    variant["turret_next_joint"] = values.get("TurretNextJoint")
    for key, value in sorted(values.items()):
        if key in ("ReloadCount", "TurretNextJoint"):
            continue
        if key == "Bullet":
            continue  # handled below, with commented-line awareness
        variant["turret_params"][key] = value
    if "Bullet" in values:
        variant["bullet"] = values["Bullet"]
    else:
        # The comment-stripping parser cannot see `//Bullet = X`; a turret with
        # no Bullet key at all is recorded honestly as unarmed/unknown.
        variant["bullet_commented_out"] = True
        issues.append({"severity": "missing_field",
                       "detail": f"turret {turret_ref!r} defines no live Bullet key "
                                 "(commented-out or absent)"})
        return variant

    bullet_ref = variant["bullet"]
    bullet = bullet_map.get(bullet_ref)
    if bullet is None:
        issues.append({"severity": "unresolved_ref",
                       "detail": f"turret {turret_ref!r}: bullet {bullet_ref!r} has no "
                                 "[BulletTypes] section"})
        return variant
    variant["bullet_found"] = True
    bvalues: dict = {}
    for key, value, _implicit, _line in bullet["pairs"]:
        bvalues.setdefault(key, value)
    for key in BULLET_NUMERIC:
        variant[{  # noqa: B905 — plain dict, keys are literals
            "Damage": "damage", "MaxRange": "max_range", "MinRange": "min_range",
            "Speed": "bullet_speed", "BlastRadius": "blast_radius",
            "FriendlyDamageAmount": "friendly_damage_amount"}[key]] = _int(bvalues.get(key))
    for key in BULLET_BOOL:
        variant[{  # noqa: B905
            "Homing": "homing", "AntiAircraft": "anti_aircraft",
            "AntiGround": "anti_ground", "Trajectory": "trajectory",
            "BlowUp": "blow_up"}[key]] = _bool(bvalues.get(key))
    warhead_ref = bvalues.get("Warhead")
    variant["warhead"] = warhead_ref
    if warhead_ref:
        warhead = warhead_map.get(warhead_ref)
        if warhead is None:
            issues.append({"severity": "unresolved_ref",
                           "detail": f"bullet {bullet_ref!r}: warhead {warhead_ref!r} "
                                     "has no section"})
        else:
            for key, value, _implicit, _line in warhead["pairs"]:
                pct = _int(value)
                if pct is None:
                    issues.append({"severity": "malformed_source",
                                   "detail": f"warhead {warhead_ref!r}: row {key!r} = "
                                             f"{value!r} is not an integer"})
                    continue
                if armour_types and key not in armour_types:
                    issues.append({"severity": "undeclared_armour_row",
                                   "detail": f"warhead {warhead_ref!r}: armour {key!r} "
                                             "not in [ArmourTypes]"})
                variant["versus"][key] = pct
    return variant


# ── Veterancy blocks (ordered, never flattened) ──────────────────────────────

VETERANCY_FIELDS = ("Health", "ExtraDamage", "ExtraArmour", "CanSelfRepair",
                    "Elite", "ExtraRange")
VETERANCY_LEVEL_KEYS = {"VeterancyLevel", "Health", "ExtraDamage",
                        "ExtraArmour", "CanSelfRepair", "Elite", "ExtraRange"}
VETERANCY_KEY = {"Health": "health", "ExtraDamage": "extra_damage",
                 "ExtraArmour": "extra_armour", "CanSelfRepair": "can_self_repair",
                 "Elite": "elite", "ExtraRange": "extra_range"}


def parse_veterancy(pairs, unit_id, issues):
    """Ordered per-level dicts. A field repeated INSIDE one VeterancyLevel is
    an explicit ambiguity: the FIRST value is kept and the repetition is
    reported — never silently overwritten (the raw occurrence stays in the
    record's repeated_level_values).
    """
    levels = []
    current = None
    for key, value, implicit, line_no in pairs:
        if key == "VeterancyLevel" and not implicit:
            current = {"score_required": _int(value), "line": line_no}
            levels.append(current)
            continue
        if current is None:
            continue
        if key in VETERANCY_FIELDS:
            out_key = VETERANCY_KEY[key]
            if out_key in current:
                issues.append({"severity": "ambiguous_level_field",
                               "detail": f"{unit_id}: {key!r} repeated inside "
                                         f"VeterancyLevel={current['score_required']} "
                                         f"(line {line_no}); first kept"})
                continue
            current[out_key] = (_bool(value) if out_key in ("can_self_repair", "elite")
                                else _int(value))
    if levels and levels[0]["score_required"] is None:
        issues.append({"severity": "malformed_source",
                       "detail": f"{unit_id}: VeterancyLevel without a score"})
    return levels


# ── Classification (documented, conservative — nothing guessed) ──────────────

CLASSIFICATION_RULE = (
    "wildlife if Worm==TRUE; starport_transport if name in (Frigate, "
    "StuntFrigate); storm_event if name==StormUnit; superweapon if any of "
    "(DeathHand, BeamWeapon, HawkWeapon)==TRUE; economy_unit/transport_unit if "
    "Harvester/MCV/Carryall==TRUE (manual_review_only); buildable if "
    "PrimaryBuilding present AND Cost>0; else nonbuildable — Cost>0 alone is "
    "never a buildability proof"
)


def classify(name, values):
    flags = {k: _bool(v) for k, v in values.items()
             if k in SUPERWEAPON_FLAGS or k in ECONOMY_FLAGS or k == WORM_FLAG}
    if flags.get(WORM_FLAG):
        return "wildlife", flags
    if name in TRANSPORT_NAMES:
        return "starport_transport", flags
    if name in STORM_NAMES:
        return "storm_event", flags
    for flag in SUPERWEAPON_FLAGS:
        if flags.get(flag):
            return "superweapon", flags
    for flag, cls in ECONOMY_FLAGS.items():
        if flags.get(flag):
            return cls, flags
    return None, flags


def buildability(values, rec_class):
    """(buildable, rule, issue_detail) — PrimaryBuilding AND Cost>0 required."""
    primary = [t for t in raw_list(values.get("PrimaryBuilding", "")) if t]
    cost = _int(values.get("Cost"))
    if rec_class in ("superweapon", "wildlife", "starport_transport",
                     "storm_event"):
        return False, f"collection_only_class:{rec_class}", None
    if rec_class in ECONOMY_FLAGS.values():
        return False, f"manual_review_only_class:{rec_class}", None
    if primary and cost is not None and cost > 0:
        return True, "primary_building_and_positive_cost", None
    if not primary:
        detail = ("positive cost without any PrimaryBuilding — cost alone is "
                  "not a buildability proof")
        return False, "no_production_building", detail
    if cost is None:
        return False, "cost_missing", "no Cost key; buildability unknown->false"
    return False, "zero_cost", "PrimaryBuilding present but Cost is 0"


def eligibility(final_class, buildable):
    """(balance_eligible, manual_review_only, collection_only) — nothing certified.

    NO record is certified balance-eligible: the version label is unverified
    and activation/context (palace specials, starport, skirmish gating) is
    incomplete, so every record is a **reference collection candidate only**.
    A `buildable_candidate` (production building + Cost>0 in the archive) is
    NOT auto-certified — `balance_eligible` stays null. Explicit False only
    where the data rules it out: nonbuildable records, manual_review_only
    economy/transport, and collection-only specials.
    """
    if final_class in ("superweapon", "wildlife", "starport_transport",
                       "storm_event"):
        return False, False, True
    if final_class in ECONOMY_FLAGS.values():
        return False, True, False
    if final_class == "nonbuildable":
        return False, False, False
    return None, False, False   # buildable_candidate: NOT certified


# ── Provenance ───────────────────────────────────────────────────────────────

def sha256_of(path: pathlib.Path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_provenance(source: pathlib.Path, sha_before: str, sha_after: str,
                     bytes_count: int):
    return {
        "source_game": "Emperor: Battle for Dune",
        "source_kind": "archived-original/unverified patch — single Rules.txt",
        "source_file": str(source),
        "sha256_before": sha_before,
        "sha256_after": sha_after,
        "unchanged_during_run": sha_before == sha_after,
        "sha256_expected": EXPECTED_SHA256,
        "sha256_matches_expected": sha_after.upper() == EXPECTED_SHA256,
        "bytes": bytes_count,
        "download_url": SOURCE_URL,
        "license": "unverified — no license statement in the file; treated as "
                   "archived game data, quoted only in extract form",
        "version_notes": [
            "The file's own [General] Version = 1.23 is a FILE label; it is NOT "
            "established as any retail patch version.",
            "The file header self-describes as an example demonstrating the "
            "building and unit hierarchies and how the Group type stops icon "
            "duplication; treat roster completeness with that caveat.",
            "Several [UnitTypes] entries are commented out (e.g. Scout, "
            "Thumper, Scavenger) and therefore carry no stats in this file; "
            "they are recorded under declared.unit_types with declared=false.",
            "There is no per-unit inheritance keyword; hierarchy is via "
            "repeated declaration sections (append order, save-game-sensitive) "
            "plus named UnitGroupTypes/BuildingGroupTypes.",
        ],
        "unavailable_axes": [
            "art / voxel / sound / voice assets (not in Rules.txt)",
            "strings.txt texts (AlertString references kept raw)",
            "retail-patch provenance of Version=1.23 (unverified)",
            "activation context: palace specials' trigger rules, starport "
            "stock and skirmish gating live outside this file's unit rows",
            "engine tick length: no seconds conversion anywhere by design "
            "(BuildTime/ReloadCount/Speed/TurnRate stay native)",
            "AI internals (AiThreat etc. recorded raw, no interpretation)",
        ],
        "classification_rule": CLASSIFICATION_RULE,
        "eligibility_policy": (
            "no record is certified balance-eligible; every record is a "
            "reference collection candidate only; buildable_candidate is "
            "production evidence, never certification; harvester/MCV "
            "manual_review_only"),
    }


# ── Extraction ───────────────────────────────────────────────────────────────

def extract(source: pathlib.Path, issues: list):
    if source.is_dir():
        source = source / "Rules.txt"
    if not source.is_file():
        issues.append({"severity": "source_missing",
                       "detail": f"required source file missing: {source}"})
        return None

    # Hash BEFORE reading (proves the parse left nothing behind) ...
    sha_before = sha256_of(source)
    text = source.read_text(encoding="utf-8", errors="replace")
    sections = parse_ini(text, issues)

    declared = collect_declarations(sections, issues)
    unit_decl = declared.get(UNIT_DECL_SECTION, {"entries": [], "commented": []})
    turret_decl = declared.get(TURRET_DECL_SECTION, {"entries": []})
    bullet_decl = declared.get(BULLET_DECL_SECTION, {"entries": []})
    warhead_decl = declared.get(WARHEAD_DECL_SECTION, {"entries": []})
    house_decl = declared.get("HouseTypes", {"entries": []})
    armour_decl = declared.get("ArmourTypes", {"entries": []})
    unit_group_decl = declared.get("UnitGroupTypes", {"entries": []})

    declared_units = [name for name, _line in unit_decl["entries"]]
    turret_names = [n for n, _l in turret_decl["entries"]]
    turret_map, _turret_occ = first_section_map(sections, set(turret_names), issues)
    bullet_map, _bullet_occ = first_section_map(
        sections, set(n for n, _l in bullet_decl["entries"]), issues)
    warhead_map, _warhead_occ = first_section_map(
        sections, set(n for n, _l in warhead_decl["entries"]), issues)
    armour_types = {name for name, _line in armour_decl["entries"]}
    house_types = [name for name, _line in house_decl["entries"]]
    unit_groups = [name for name, _line in unit_group_decl["entries"]]
    # ... and AFTER the whole parse (source integrity, both recorded).
    provenance = build_provenance(source, sha_before, sha256_of(source),
                                  source.stat().st_size)

    unit_map, _unit_occ = first_section_map(sections, set(declared_units), issues)

    referenced_turrets: set = set()
    referenced_bullets: set = set()
    referenced_warheads: set = set()

    general_values: dict = {}
    for section in sections:
        if section["name"] == "General":
            for key, value, _implicit, _line in section["pairs"]:
                general_values.setdefault(key, value)

    # House-token sanity: a unit's House must be one of the declared houses.
    known_houses = set(house_types)

    records = []
    for name in declared_units:
        section = unit_map.get(name)
        if section is None:
            continue  # dangling_declaration issue already recorded
        values: dict = {}
        occurrences = 0
        repeated_values: dict = {}
        # VeterancyLevel BOUNDARIES, not key vocabulary: each VeterancyLevel
        # pair opens a new level block; -1 is base context before any level.
        # Repetitions across distinct blocks are the archive's expected
        # shape; a conflict before any level, or a repetition inside ONE
        # block, is an explicit ambiguity — never silently merged.
        occ_levels: dict = {}     # key -> [(context, value), ...]
        current_level = -1
        for key, value, _implicit, _line in section["pairs"]:
            occurrences += 1
            if key == "VeterancyLevel":
                current_level += 1
            context = "base" if current_level == -1 else f"level{current_level}"
            if key in values:
                repeated_values.setdefault(key, [values[key]]).append(value)
                occ = occ_levels.setdefault(key, [])
                previous_context = occ[-1][0] if occ else context
                previous_value = occ[-1][1] if occ else values[key]
                occ.append((context, value))
                if context == "base" and previous_context == "base":
                    # Both occurrences before ANY VeterancyLevel: a genuine
                    # conflict only when the values differ.
                    if values[key] != value:
                        issues.append({
                            "severity": "conflicting_key",
                            "detail": f"[{name}] {key!r} repeated with "
                                      f"{value!r} (first {values[key]!r}) "
                                      "before any VeterancyLevel"})
                elif context == previous_context:
                    # Same VeterancyLevel block: explicit ambiguity, first
                    # value kept, never silently overwritten.
                    issues.append({
                        "severity": "ambiguous_level_field",
                        "detail": f"[{name}] {key!r} repeated within the same "
                                  f"veterancy context ({context}): {value!r} "
                                  f"(previous kept {previous_value!r})"})
                else:
                    # base -> levelN override, or two distinct level blocks:
                    # the archive's expected shape.
                    issues.append({
                        "severity": "repeated_level_field",
                        "detail": f"[{name}] {key!r} repeated across distinct "
                                  f"veterancy contexts ({previous_context} -> "
                                  f"{context}): {value!r}"})
                continue
            values.setdefault(key, value)
            occ_levels.setdefault(key, []).append((context, value))

        house = raw_list(values.get("House", "")) if values.get("House") else []
        for token in house:
            if known_houses and token not in known_houses:
                issues.append({"severity": "undeclared_house",
                               "detail": f"[{name}] House {token!r} not in "
                                         "[HouseTypes]"})

        rec_class, class_flags = classify(name, values)
        buildable, rule, build_issue = buildability(values, rec_class)
        final_class = rec_class or ("buildable_candidate" if buildable
                                    else "nonbuildable")
        eligible, review_only, collection_only = eligibility(final_class, buildable)

        rec_issues = []
        if build_issue:
            rec_issues.append({"code": "buildability", "detail": build_issue})
        if not house:
            rec_issues.append({"code": "house_missing",
                               "detail": "no House key; native default unknown — "
                                         "recorded as null, not guessed"})
        for flag in SUPERWEAPON_FLAGS:
            if class_flags.get(flag) and _int(values.get("Cost")) == 0:
                rec_issues.append({"code": "superweapon_zero_cost",
                                   "detail": f"{flag}=TRUE with Cost=0 corroborates "
                                             "superweapon classification"})
                break

        turret_attach = raw_list(values.get("TurretAttach", ""))
        weapon_variants = [
            resolve_weapon_variant(ref, turret_map, bullet_map, warhead_map,
                                   armour_types, name, issues)
            for ref in turret_attach
        ]
        if turret_attach and not weapon_variants:
            rec_issues.append({"code": "no_weapon_variant_resolved",
                               "detail": "TurretAttach present but no turret resolved"})

        records.append({
            "id": name,
            "declaration_line": dict(unit_decl["entries"]).get(name),
            "house": house or None,
            "cost": _int(values.get("Cost")),
            "build_time": _int(values.get("BuildTime")),
            "health": _int(values.get("Health")),
            "speed": values.get("Speed"),
            "speed_semantics": "game coords per update (native, unconverted)",
            "turn_rate": values.get("TurnRate"),
            "turn_rate_semantics": "radians per update (native, unconverted)",
            "mech_speed": values.get("MechSpeed"),
            "armour": raw_list(values.get("Armour", "")) or None,
            "armour_semantics": ("raw tokens; single name or triple — the "
                                 "triple's extra tokens are NOT interpreted"),
            "tech_level": _int(values.get("TechLevel")),
            "size": _int(values.get("Size")),
            "score": _int(values.get("Score")),
            "starportable": _bool(values.get("Starportable")),
            "reinforcement_value": _int(values.get("ReinforcementValue")),
            "primary_building": raw_list(values.get("PrimaryBuilding", "")) or None,
            "secondary_building": raw_list(values.get("SecondaryBuilding", "")) or None,
            "upgraded_primary_required": _bool(values.get("UpgradedPrimaryRequired")),
            "unit_group": values.get("UnitGroup"),
            "terrain": raw_list(values.get("Terrain", "")) or None,
            "view_range": raw_list(values.get("ViewRange", "")) or None,
            "view_range_semantics": "raw tokens; NOT interpreted",
            "turret_attach": turret_attach or None,
            "weapon_variants": weapon_variants,
            "veterancy": parse_veterancy(section["pairs"], name, issues),
            "class_flags": class_flags,
            "buildable": buildable,
            "buildability_rule": rule,
            "extraction_class": final_class,
            "collection_candidate": True,
            "balance_eligible": eligible,
            "eligibility_note": (
                "null = NOT certified: archived-original/unverified patch, "
                "Version label unverified, activation context incomplete; "
                "reference collection candidate only" if eligible is None else
                "false by task rule: manual_review_only" if review_only else
                "false by task rule: collection-only class" if collection_only else
                "false by data rule: no production building / Cost is not proof"),
            "manual_review_only": review_only,
            "collection_only": collection_only,
            "repeated_level_values": {k: v for k, v in sorted(repeated_values.items())
                                      if k in VETERANCY_LEVEL_KEYS} or None,
            "repeated_values": {k: v for k, v in sorted(repeated_values.items())
                                if k not in VETERANCY_LEVEL_KEYS} or None,
            "misc": {k: v for k, v in sorted(values.items())
                     if k not in RESERVED_KEYS},
            "key_lines": occurrences,
            "issues": rec_issues,
        })

    weapons_corpus = {
        "turrets": {name: {"line": sec["line"],
                           "pairs": [[k, v, implicit, line]
                                     for k, v, implicit, line in sec["pairs"]]}
                    for name, sec in sorted(turret_map.items())},
        "bullets": {name: {"line": sec["line"],
                           "pairs": [[k, v, implicit, line]
                                     for k, v, implicit, line in sec["pairs"]]}
                    for name, sec in sorted(bullet_map.items())},
        "warheads": {name: {"line": sec["line"],
                            "pairs": [[k, v, implicit, line]
                                      for k, v, implicit, line in sec["pairs"]]}
                     for name, sec in sorted(warhead_map.items())},
    }

    declared_out = {
        "unit_types": [{"name": name, "line": line} for name, line in unit_decl["entries"]],
        "unit_types_commented_out": list(unit_decl.get("commented", [])),
        "house_types": [{"name": name, "line": line} for name, line in house_decl["entries"]],
        "unit_groups": [{"name": name, "line": line} for name, line in unit_group_decl["entries"]],
        "armour_types": [{"name": name, "line": line} for name, line in armour_decl["entries"]],
        "turret_types": [name for name, _l in turret_decl["entries"]],
        "bullet_types": [name for name, _l in bullet_decl["entries"]],
        "warhead_types": [name for name, _l in warhead_decl["entries"]],
        "declaration_batches": {kind: bucket["batches"]
                                for kind, bucket in sorted(declared.items())},
    }
    for record in records:
        for variant in record["weapon_variants"]:
            referenced_turrets.add(variant["turret"])
            if variant["bullet"]:
                referenced_bullets.add(variant["bullet"])
            if variant["warhead"]:
                referenced_warheads.add(variant["warhead"])

    turret_names_set = set(turret_names)
    counts = {
        "unit_records": len(records),
        "buildable": sum(1 for r in records if r["buildable"]),
        "superweapons": sum(1 for r in records
                            if r["extraction_class"] == "superweapon"),
        "economy_units": sum(1 for r in records
                             if r["extraction_class"] in ECONOMY_FLAGS.values()),
        "turrets": len(turret_map),
        "bullets": len(bullet_map),
        "warheads": len(warhead_map),
        "unreferenced_turrets": len(turret_names_set - referenced_turrets),
        "unreferenced_bullets": len(set(bullet_map) - referenced_bullets),
        "unreferenced_warheads": len(set(warhead_map) - referenced_warheads),
        "commented_out_unit_declarations": len(unit_decl.get("commented", [])),
        "general_version_label": general_values.get("Version"),
    }
    return {
        "provenance": provenance,
        "records": records,
        "weapons": weapons_corpus,
        "declared": declared_out,
        "general": general_values,
        "counts": counts,
    }


RESERVED_KEYS = {
    "House", "Cost", "BuildTime", "Health", "Speed", "TurnRate", "MechSpeed",
    "Armour", "TechLevel", "Size", "Score", "Starportable",
    "ReinforcementValue", "PrimaryBuilding", "SecondaryBuilding",
    "UpgradedPrimaryRequired", "UnitGroup", "Terrain", "ViewRange",
    "TurretAttach", "VeterancyLevel", "ExtraDamage", "ExtraArmour",
    "CanSelfRepair", "Elite", "ExtraRange",
}


# ── Output plumbing ──────────────────────────────────────────────────────────

def canonical_json(payload):
    return json.dumps(payload, sort_keys=True, indent=1, ensure_ascii=True) + "\n"


STDOUT_OUT = "-"


def validate_out(out: pathlib.Path, source: pathlib.Path):
    """The JSON may go to stdout or to an EXTERNAL file — nothing else.

    Refuses: paths inside THIS repository, paths inside the source tree, and
    the source file/dir itself.
    """
    if out == pathlib.Path(STDOUT_OUT):
        return
    out = out.expanduser().resolve()
    repo = REPO_ROOT.resolve()
    if out == repo or repo in out.parents:
        raise SystemExit(f"refusing output inside this repository: {out}")
    source_root = (source.parent if source.is_file() else source).resolve()
    if out == source_root or source_root in out.parents:
        raise SystemExit(f"refusing output inside the source tree: {out}")
    if out == (source if source.is_file() else source_root):
        raise SystemExit("refusing output equal to the source")
    parent = out.parent
    if parent.exists() and not parent.is_dir():
        raise SystemExit(f"output parent is not a directory: {parent}")


def write_exclusive(out: pathlib.Path, text: str):
    """Create-or-refuse. Never truncates, never overwrites, race-safe.

    `O_EXCL` guarantees a single creator even under concurrent runs; a loser
    that arrives after creation compares content: identical -> already current
    (exit 0), differing -> refusal (exit 3). No force path exists by design.
    """
    data = text.encode("utf-8")
    try:
        fd = os.open(str(out), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        existing = out.read_bytes() if out.is_file() else None
        if existing == data:
            print(f"already current (not rewritten): {out}")
            return 0
        print(f"REFUSING: {out} already exists with DIFFERENT content "
              f"(existing bytes={len(existing) if existing is not None else '?'}, "
              f"new bytes={len(data)}); delete it explicitly first", file=sys.stderr)
        return 3
    except OSError as exc:
        print(f"cannot create {out}: {exc}", file=sys.stderr)
        return 2
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)   # bytes: text mode would translate \n to \r\n on Windows
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", type=pathlib.Path, required=True,
                    help="Rules.txt path or its directory (read-only; no default)")
    ap.add_argument("--out", type=pathlib.Path, required=True,
                    help=f"external JSON path outside repo and source tree, "
                         f"or '{STDOUT_OUT}' for stdout")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    source = args.source.expanduser().resolve()
    if not source.exists():
        print(f"source does not exist: {source}", file=sys.stderr)
        return 2
    out = args.out.expanduser()
    if out != pathlib.Path(STDOUT_OUT):
        out = out.resolve()
    validate_out(out, source)

    issues: list = []
    data = extract(source, issues)
    if data is None:
        for issue in issues:
            print(f"ISSUE [{issue.get('severity')}] {issue.get('detail')}",
                  file=sys.stderr)
        return 2

    sha = data["provenance"]["sha256_after"]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "tool": "tools/reference/extract_emperor_units.py",
        "provenance": data["provenance"],
        "counts": data["counts"],
        "records": data["records"],
        "weapons": data["weapons"],
        "declared": data["declared"],
        "general": data["general"],
        "issues": sorted(issues, key=lambda i: (i.get("severity", ""),
                                                i.get("detail", ""))),
    }
    text = canonical_json(payload)

    if args.dry_run:
        print(f"dry run: {data['counts']} · {len(issues)} issues · "
              f"would write {out if out != pathlib.Path(STDOUT_OUT) else 'stdout'}")
        return 0

    if out == pathlib.Path(STDOUT_OUT):
        sys.stdout.write(text)
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    code = write_exclusive(out, text)

    if not args.quiet:
        print(f"source : {source}")
        print(f"sha256 : {sha}")
        print(f"records: {data['counts']}")
        print(f"issues : {len(issues)}")
        print(f"wrote  : {out}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
