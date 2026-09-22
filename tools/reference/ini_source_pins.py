#!/usr/bin/env python3
"""Verify external INI bytes against the committed corpus weapon links.

The third-party rules files stay outside git.  The repository stores only their SHA-256
digests and a fingerprint of the corpus fields whose provenance is being certified here:
actor Primary/Secondary selection and weapon -> projectile links.  This deliberately does
not certify cadence, damage completeness, engine defaults, or the historical decision to
promote a secondary weapon over a dummy primary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from extract_ini_units import read_ini, resolve_inherits  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parents[2]
RELATIVE = pathlib.Path("docs/reference/ini_source_pins.json")
CORPUS_RELATIVE = pathlib.Path("docs/reference/ini_corpus.json")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
LINK_FIELDS = (
    "source",
    "id",
    "secondary",
    "weapon",
    "w_projectile",
    "w2_weapon",
    "w2_projectile",
    "w_from_secondary",
    "w_dummy_primary",
)


def file_sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corpus_rows(root=ROOT) -> list[dict]:
    path = pathlib.Path(root) / CORPUS_RELATIVE
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def source_rows(source: str, root=ROOT) -> list[dict]:
    return [row for row in corpus_rows(root) if row.get("source") == source]


def weapon_link_fingerprint(rows: list[dict]) -> str:
    """Fingerprint the ordered corpus identities and links, preserving duplicate rows."""
    digest = hashlib.sha256()
    for row in rows:
        record = {key: row.get(key) for key in LINK_FIELDS}
        digest.update(json.dumps(record, sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=False).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def load(root=ROOT) -> dict[str, dict]:
    path = pathlib.Path(root) / RELATIVE
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema") != 1:
        raise ValueError("unsupported INI source-pin schema")
    result = {}
    for entry in doc.get("sources", ()):
        source = entry.get("source")
        filename = entry.get("file")
        digest = entry.get("rules_sha256")
        if not isinstance(source, str) or not source or source in result:
            raise ValueError("duplicate or missing INI source label")
        if not isinstance(filename, str) or pathlib.Path(filename).name != filename:
            raise ValueError(f"{source}: source pin must use a flat filename")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise ValueError(f"{source}: invalid rules_sha256")
        if entry.get("engine") not in ("ra2", "ts"):
            raise ValueError(f"{source}: invalid engine profile")
        rows = source_rows(source, root)
        if entry.get("row_count") != len(rows):
            raise ValueError(f"{source}: corpus row count moved")
        if entry.get("corpus_weapon_links_sha256") != weapon_link_fingerprint(rows):
            raise ValueError(f"{source}: corpus weapon links moved")
        promoted = [row for row in rows if row.get("w_from_secondary") is True]
        if entry.get("preserved_secondary_occurrences") != len(promoted):
            raise ValueError(f"{source}: preserved secondary occurrence count moved")
        if entry.get("preserved_secondary_identities") != len({row["id"] for row in promoted}):
            raise ValueError(f"{source}: preserved secondary identity count moved")
        result[source] = entry
    return result


def _value(section: dict | None, key: str):
    if not section:
        return None
    value = (section.get(key) or "").strip()
    return value or None


def verify_entry(entry: dict, ini_dir: pathlib.Path, root=ROOT) -> dict:
    source = entry["source"]
    path = ini_dir / entry["file"]
    if not path.is_file():
        raise ValueError(f"{source}: missing {path}")
    actual = file_sha256(path)
    if actual != entry["rules_sha256"]:
        raise ValueError(f"{source}: SHA-256 is {actual}, expected {entry['rules_sha256']}")

    ini = resolve_inherits(read_ini(path))
    rows = source_rows(source, root)
    checked_projectiles = 0
    for index, row in enumerate(rows, 1):
        actor = ini.get(row["id"])
        if actor is None:
            raise ValueError(f"{source}/{row['id']} row {index}: actor section is absent")
        primary = _value(actor, "Primary")
        secondary = _value(actor, "Secondary")
        if row.get("secondary") != secondary:
            raise ValueError(f"{source}/{row['id']} row {index}: Secondary link moved")

        if row.get("w_from_secondary") is True:
            expected = (secondary, primary, None)
            actual_slots = (row.get("weapon"), row.get("w_dummy_primary"),
                            row.get("w2_weapon"))
            if actual_slots != expected:
                raise ValueError(f"{source}/{row['id']} row {index}: promoted slots moved")
        else:
            expected = (primary, secondary)
            actual_slots = (row.get("weapon"), row.get("w2_weapon"))
            if actual_slots != expected:
                raise ValueError(f"{source}/{row['id']} row {index}: weapon slots moved")

        for weapon_key, projectile_key in (("weapon", "w_projectile"),
                                           ("w2_weapon", "w2_projectile")):
            weapon = row.get(weapon_key)
            if not weapon:
                continue
            projectile = _value(ini.get(weapon), "Projectile")
            if row.get(projectile_key) != projectile:
                raise ValueError(
                    f"{source}/{row['id']} row {index}: {weapon} projectile moved")
            checked_projectiles += 1

    if file_sha256(path) != actual:
        raise ValueError(f"{source}: source changed during verification")

    return {"source": source, "rows": len(rows),
            "weapon_projectile_links": checked_projectiles}


def verify_all(ini_dir: pathlib.Path, root=ROOT) -> list[dict]:
    ini_dir = pathlib.Path(ini_dir).resolve()
    if not ini_dir.is_dir():
        raise ValueError(f"INI directory is absent: {ini_dir}")
    return [verify_entry(entry, ini_dir, root) for entry in load(root).values()]


def stamp_corpus(ini_dir: pathlib.Path, root=ROOT) -> tuple[int, list[dict]]:
    """Add only source_sha256 to covered rows after full external verification."""
    root = pathlib.Path(root)
    verified = verify_all(ini_dir, root)
    configured = load(root)
    path = root / CORPUS_RELATIVE
    rows = corpus_rows(root)
    for source, entry in configured.items():
        covered = [row for row in rows if row.get("source") == source]
        stamped = sum(row.get("source_sha256") == entry["rules_sha256"] for row in covered)
        if stamped not in (0, len(covered)):
            raise ValueError(f"{source}: source pin is partial")
    changed = 0
    for row in rows:
        entry = configured.get(row.get("source"))
        if entry is None:
            continue
        expected = entry["rules_sha256"]
        existing = row.get("source_sha256")
        if existing not in (None, expected):
            raise ValueError(f"{row['source']}/{row.get('id')}: conflicting source_sha256")
        if existing is None:
            row["source_sha256"] = expected
            changed += 1

    # Re-check every byte pin immediately before the repository write.
    ini_dir = pathlib.Path(ini_dir).resolve()
    for entry in configured.values():
        if file_sha256(ini_dir / entry["file"]) != entry["rules_sha256"]:
            raise ValueError(f"{entry['source']}: source changed before corpus write")

    # Match the corpus generator's ASCII-escaped JSONL so stamping provenance does not create
    # unrelated encoding churn or break older default-encoding readers on Windows.
    lines = [json.dumps(row, sort_keys=True, separators=(",", ":"),
                        ensure_ascii=True, allow_nan=False) for row in rows]
    temporary = path.with_name(path.name + ".pinning.tmp")
    if temporary.exists():
        raise ValueError(f"temporary output already exists: {temporary}")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)
    return changed, verified


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ini-dir", required=True, type=pathlib.Path,
                        help="external flat directory containing the pinned INI files")
    parser.add_argument("--write", action="store_true",
                        help="add only source_sha256 to the verified corpus rows")
    args = parser.parse_args(argv)
    try:
        if args.write:
            changed, results = stamp_corpus(args.ini_dir)
        else:
            changed, results = None, verify_all(args.ini_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    for result in results:
        print(f"OK {result['source']}: {result['rows']} corpus rows, "
              f"{result['weapon_projectile_links']} weapon/projectile links")
    print(f"verified {len(results)} byte-pinned INI sources")
    if args.write:
        print(f"stamped {changed} corpus rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
