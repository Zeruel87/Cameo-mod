#!/usr/bin/env python3
"""Build exact armament-role evidence for the seven externally pinned INI sources.

The corpus already records which actor slot names which weapon and projectile.  PR #387
bound those links to the exact external source bytes.  This extractor completes the next
gate without regenerating the corpus: it reads the same verified bytes, accepts a targeting
role only when the projectile flags are provable for that engine, and accepts weapon numbers
only under ``extract_ini_units.weapon_of``'s ``nominal_direct`` contract.

RA2/YR defaults are deliberately not guessed.  Both resolved ``AA`` and ``AG`` values must
be declared and valid.  Tiberian Sun may use the documented BulletTypeClass defaults.  Any
missing section, invalid boolean, incomplete weapon, or multi-shot weapon abstains.

    python tools/reference/extract_ini_armament_roles.py \
        --ini-dir "<flat directory containing the seven pinned INIs>" --write
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import ini_source_pins as pins  # noqa: E402
from extract_ini_projectile_roles import (DEFAULT_AA, DEFAULT_AG,  # noqa: E402
                                          _verified_sources, role_of, target_bool)
from extract_ini_units import read_ini, resolve_inherits, weapon_of  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "reference" / "ini_armament_role_evidence.json"


def projectile_verdict(ini: dict, projectile: str | None, engine: str) -> tuple[dict | None, str | None]:
    """Return an exact role verdict, or a named abstention reason."""
    section = ini.get(projectile or "")
    if section is None:
        return None, "projectile_section_absent"

    aa, aa_state = target_bool(section.get("AA"))
    ag, ag_state = target_bool(section.get("AG"))
    if "invalid" in (aa_state, ag_state):
        return None, "invalid_target_boolean"

    if engine == "ra2":
        # No RA2/YR engine-default source is pinned in this repository.  A single declared
        # flag cannot distinguish air from both, or ground from special, so it must abstain.
        if aa_state != "declared" or ag_state != "declared":
            return None, "ra2_target_default_unverified"
        basis = "resolved projectile AA and AG declarations"
    elif engine == "ts":
        aa = DEFAULT_AA if aa_state == "absent" else aa
        ag = DEFAULT_AG if ag_state == "absent" else ag
        basis = "resolved declarations plus TS BulletTypeClass defaults"
    else:
        return None, "unsupported_engine"

    return {
        "role": role_of(bool(aa), bool(ag)),
        "aa": bool(aa),
        "ag": bool(ag),
        "declared": sorted(k for k, state in (("AA", aa_state), ("AG", ag_state))
                           if state == "declared"),
        "target_basis": basis,
    }, None


def referenced_armaments(source: str, root=ROOT) -> list[tuple[str, str]]:
    """Unique weapon/projectile links cited by either baseline corpus slot."""
    found: dict[str, str] = {}
    canonical: dict[str, str] = {}
    for row in pins.source_rows(source, root):
        for weapon_key, projectile_key in (("weapon", "w_projectile"),
                                           ("w2_weapon", "w2_projectile")):
            weapon = row.get(weapon_key)
            if not weapon:
                continue
            folded = str(weapon).lower()
            previous_case = canonical.setdefault(folded, str(weapon))
            if previous_case != str(weapon):
                raise ValueError(
                    f"{source}: ambiguous weapon case aliases {previous_case!r}/{weapon!r}")
            projectile = row.get(projectile_key)
            previous = found.setdefault(str(weapon), str(projectile or ""))
            if previous != str(projectile or ""):
                raise ValueError(f"{source}/{weapon}: corpus cites conflicting projectiles")
    return sorted(found.items(), key=lambda item: item[0].lower())


def armament_records(ini: dict, source: str, engine: str, root=ROOT) -> dict[str, dict]:
    records = {}
    for weapon, projectile in referenced_armaments(source, root):
        extracted = weapon_of(ini, weapon, engine)
        actual_projectile = str(extracted.get("w_projectile") or "")
        if actual_projectile != projectile:
            raise ValueError(
                f"{source}/{weapon}: source projectile {actual_projectile!r} != corpus {projectile!r}")

        target, target_reason = projectile_verdict(ini, projectile or None, engine)
        status = "resolved"
        reason = None
        raw_burst = extracted.get("w_burst")
        burst = 1 if raw_burst is None else raw_burst
        numeric = (extracted.get("w_damage"), extracted.get("w_reload"),
                   extracted.get("w_range"))
        numbers_ok = all(isinstance(value, (int, float)) and not isinstance(value, bool)
                         and math.isfinite(value) and value > 0 for value in numeric)
        burst_ok = (isinstance(burst, (int, float)) and not isinstance(burst, bool)
                    and math.isfinite(burst) and float(burst).is_integer() and int(burst) == 1)
        if target is None:
            status, reason = "abstained", target_reason
        elif (extracted.get("w_evidence") != "nominal_direct"
              or extracted.get("w_dps_usable") is not True):
            status = "abstained"
            reason = extracted.get("w_evidence_reason") or "weapon_evidence_incomplete"
        elif not burst_ok:
            status, reason = "abstained", "invalid_or_unfolded_burst"
        elif not numbers_ok:
            status, reason = "abstained", "invalid_direct_weapon_numbers"

        record = {
            "weapon": weapon,
            "projectile": projectile or None,
            "status": status,
            "reason": reason,
            "weapon_evidence": extracted.get("w_evidence"),
            "weapon_evidence_reason": extracted.get("w_evidence_reason"),
            "w_dps_usable": extracted.get("w_dps_usable"),
        }
        if target is not None:
            record.update(target)
        if status == "resolved":
            # These values come from the verified source bytes, not the older corpus columns.
            record.update({
                "damage": extracted.get("w_damage"),
                "reload": extracted.get("w_reload"),
                "range": extracted.get("w_range"),
                "burst": int(burst),
            })
        records[weapon] = record
    return records


def build(ini_dir: pathlib.Path, root=ROOT) -> dict:
    root = pathlib.Path(root)
    ini_dir = pathlib.Path(ini_dir).resolve()
    verified = {row["source"]: row for row in pins.verify_all(ini_dir, root)}
    configured = pins.load(root)
    sources = []
    for source, spec in configured.items():
        if source not in verified:
            raise ValueError(f"{source}: external verification did not complete")
        path = ini_dir / spec["file"]
        if pins.file_sha256(path) != spec["rules_sha256"]:
            raise ValueError(f"{source}: source changed before armament extraction")
        ini = resolve_inherits(read_ini(path))
        if pins.file_sha256(path) != spec["rules_sha256"]:
            raise ValueError(f"{source}: source changed during armament extraction")
        records = armament_records(ini, source, spec["engine"], root)
        sources.append({
            "source": source,
            "engine": spec["engine"],
            "rules_sha256": spec["rules_sha256"],
            "overlay_sha256": None,
            "corpus_weapon_links_sha256": spec["corpus_weapon_links_sha256"],
            "referenced_armaments": len(records),
            "resolved_armaments": sum(r["status"] == "resolved" for r in records.values()),
            "armaments": records,
        })
    for source, spec in configured.items():
        if pins.file_sha256(ini_dir / spec["file"]) != spec["rules_sha256"]:
            raise ValueError(f"{source}: source changed before evidence publication")
    return {
        "schema": 1,
        "scope": ("Exact baseline armament role/range/direct-damage evidence for the seven "
                  "byte-pinned external INI sources. RA2 defaults, incomplete weapons, and "
                  "multi-shot cadence abstain."),
        "ts_engine_default": {
            "AA": DEFAULT_AA,
            "AG": DEFAULT_AG,
            "basis": "TS BulletTypeClass field defaults (AA=no, AG=yes); declared, not observed",
        },
        "ra2_default_policy": "unverified defaults abstain; both AA and AG must resolve explicitly",
        "sources": sources,
    }


def load(root=ROOT) -> dict[tuple[str, str, str], dict]:
    """Resolved exact ``(source, weapon, projectile)`` evidence for ``ini_views``."""
    root = pathlib.Path(root)
    path = root / "docs" / "reference" / "ini_armament_role_evidence.json"
    if not path.exists():
        load.dropped = []
        return {}
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema") != 1:
        raise ValueError("unsupported INI armament-role evidence")

    configured = pins.load(root)
    verified, dropped = _verified_sources(doc, root)
    kept = []
    for entry in verified:
        current = configured.get(entry.get("source"))
        if current is None:
            dropped.append((entry.get("source"), "source pin sidecar is absent"))
            continue
        if entry.get("corpus_weapon_links_sha256") != current["corpus_weapon_links_sha256"]:
            dropped.append((entry.get("source"), "corpus weapon links moved"))
            continue
        if entry.get("engine") != current["engine"]:
            dropped.append((entry.get("source"), "engine policy moved"))
            continue
        kept.append(entry)
    load.dropped = dropped

    out = {}
    for entry in kept:
        source = entry["source"]
        armaments = entry.get("armaments", {})
        if (entry.get("referenced_armaments") != len(armaments)
                or entry.get("resolved_armaments") !=
                sum(record.get("status") == "resolved" for record in armaments.values())):
            raise ValueError(f"{source}: armament evidence counts are inconsistent")
        expected_links = set(referenced_armaments(source, root))
        actual_links = {(weapon, str(record.get("projectile") or ""))
                        for weapon, record in armaments.items()}
        if actual_links != expected_links:
            raise ValueError(f"{source}: armament evidence bindings moved")
        for weapon, record in armaments.items():
            if record.get("weapon") != weapon:
                raise ValueError(f"{source}/{weapon}: armament identity is inconsistent")
            if record.get("status") != "resolved":
                continue
            projectile = str(record.get("projectile") or "")
            numeric = (record.get("damage"), record.get("reload"), record.get("range"))
            declared = record.get("declared")
            if (not isinstance(declared, list) or len(declared) != len(set(declared))
                    or not set(declared) <= {"AA", "AG"}):
                raise ValueError(f"{source}/{weapon}: invalid targeting declaration evidence")
            engine = configured[source]["engine"]
            if engine == "ra2" and set(declared) != {"AA", "AG"}:
                raise ValueError(f"{source}/{weapon}: RA2 targeting defaults are unverified")
            if engine == "ts":
                if "AA" not in declared and record.get("aa") is not DEFAULT_AA:
                    raise ValueError(f"{source}/{weapon}: TS AA default is inconsistent")
                if "AG" not in declared and record.get("ag") is not DEFAULT_AG:
                    raise ValueError(f"{source}/{weapon}: TS AG default is inconsistent")
            burst = record.get("burst")
            if (record.get("weapon_evidence") != "nominal_direct"
                    or record.get("w_dps_usable") is not True
                    or not all(isinstance(value, (int, float)) and not isinstance(value, bool)
                               and math.isfinite(value) and value > 0 for value in numeric)
                    or isinstance(burst, bool) or burst != 1
                    or not isinstance(record.get("aa"), bool)
                    or not isinstance(record.get("ag"), bool)
                    or record.get("role") != role_of(record["aa"], record["ag"])):
                raise ValueError(f"{source}/{weapon}: resolved evidence violates its contract")
            out[(source, weapon, projectile)] = record
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ini-dir", required=True, type=pathlib.Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        doc = build(args.ini_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    for entry in doc["sources"]:
        reasons = {}
        for record in entry["armaments"].values():
            if record["status"] != "resolved":
                reasons[record["reason"]] = reasons.get(record["reason"], 0) + 1
        print(f"{entry['source']}: {entry['resolved_armaments']}/"
              f"{entry['referenced_armaments']} armaments resolved"
              + (f"; abstained {reasons}" if reasons else ""))
    if args.write:
        OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
