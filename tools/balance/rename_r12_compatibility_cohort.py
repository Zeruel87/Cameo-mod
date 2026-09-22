#!/usr/bin/env python3
"""Rename the R12 36-template compatibility cohort without changing resolved behavior.

The writer is transactional over affected active rules/weapon files. It compares canonical
resolved dumps for every active weapon definition (templates included), with the approved name map
applied to the baseline, and refuses any remaining reference to an old cohort name.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools" / "audit"), str(ROOT / "tools" / "balance")]

from miniyaml import Ruleset  # noqa: E402
from promote_compatibility_warheads import new_template_name  # noqa: E402
from reconcile_r12_consumer_closure import proposed_inner_name  # noqa: E402
from resolved_gate import apply_map  # noqa: E402


PREFIX = "^Compatibility_"
RUNTIME_SOURCE_SUFFIXES = {
    ".config", ".cs", ".ftl", ".json", ".lua", ".toml", ".xml", ".yaml", ".yml",
}
RUNTIME_SOURCE_PREFIXES = ("engine/", "mods/", "OpenRA.Mods.")
PYTHON_REFERENCE_ALLOWLIST = ROOT / "tools" / "balance" / "r12_python_legacy_references.json"
GENERATED_PYTHON_LEGACY_FRAGMENTS = ("^Compatibility_", "FlatCompatibility")


def norm(path: pathlib.Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def rename_maps(rs: Ruleset) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    templates = sorted(name for name in rs.weapons if name.startswith(PREFIX))
    template_map = {name: new_template_name(name) for name in templates}
    inner_map = {}
    for template in templates:
        for child in rs.weapons[template].children:
            base = child.key.lstrip("-")
            if base.startswith("Warhead@") and base.endswith("Compatibility"):
                old = base[len("Warhead@"):]
                inner_map[old] = proposed_inner_name(old)
    if len(template_map) != 36 or len(inner_map) != 36:
        raise RuntimeError(
            f"R12 cohort drift: expected 36 templates/payloads, got "
            f"{len(template_map)}/{len(inner_map)}")
    if len(set(template_map.values())) != len(template_map):
        raise RuntimeError("proposed template names are not unique")
    if len(set(inner_map.values())) != len(inner_map):
        raise RuntimeError("proposed payload names are not unique")
    template_collisions = sorted(set(template_map.values()) & set(rs.weapons))
    if template_collisions:
        raise RuntimeError(f"proposed template name collision: {template_collisions}")
    full_map = dict(template_map)
    for old, new in inner_map.items():
        full_map["Warhead@" + old] = "Warhead@" + new
        full_map["-Warhead@" + old] = "-Warhead@" + new
    return template_map, inner_map, full_map


def source_replacements(template_map: dict[str, str], inner_map: dict[str, str]) -> dict[str, str]:
    out = dict(template_map)
    for old, new in inner_map.items():
        out["Warhead@" + old] = "Warhead@" + new
    return out


def active_sources(rs: Ruleset) -> list[pathlib.Path]:
    return sorted(set(rs.manifest.rules + rs.manifest.weapons))


def tracked_runtime_sources() -> list[pathlib.Path]:
    """Tracked runtime/configuration sources that may name a weapon template or payload.

    This deliberately includes dormant mod YAML and C# outside the active manifest. A resolved
    weapon dump cannot see those consumers, so the rename must refuse them for separate review.
    """
    proc = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True)
    paths = []
    for raw in proc.stdout.decode("utf-8").split("\0"):
        if not raw:
            continue
        path = ROOT / raw
        if path.suffix.lower() not in RUNTIME_SOURCE_SUFFIXES:
            continue
        if raw == "mod.config" or raw.startswith(RUNTIME_SOURCE_PREFIXES):
            paths.append(path)
    return sorted(paths)


def tracked_python_sources() -> list[pathlib.Path]:
    """Tracked Python tooling that may retain historical or generated cohort identifiers."""
    proc = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True)
    return sorted(
        ROOT / raw for raw in proc.stdout.decode("utf-8").split("\0")
        if raw.startswith("tools/") and raw.endswith(".py"))


def python_reference_records(paths: list[pathlib.Path], template_map: dict[str, str],
                             inner_map: dict[str, str]) -> dict[str, list[str]]:
    """Exact source lines that retain literal or generated legacy R12 identifiers."""
    tokens = tuple(template_map) + tuple(inner_map)
    records: dict[str, list[str]] = {}
    for path in paths:
        found = []
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if any(token in line for token in tokens) or any(
                    fragment in line for fragment in GENERATED_PYTHON_LEGACY_FRAGMENTS):
                found.append(line.strip())
        if found:
            records[norm(path)] = sorted(found)
    return records


def python_reference_digest(lines: list[str]) -> str:
    payload = json.dumps(lines, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def python_reference_issues(paths: list[pathlib.Path], template_map: dict[str, str],
                            inner_map: dict[str, str],
                            allowlist_path: pathlib.Path = PYTHON_REFERENCE_ALLOWLIST) -> list[dict]:
    """Reject new, removed, or changed legacy references outside the reviewed inventory."""
    records = python_reference_records(paths, template_map, inner_map)
    try:
        allowlist = json.loads(allowlist_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"could not load Python legacy-reference allowlist: {allowlist_path}") from exc
    if allowlist.get("schema") != 1 or not isinstance(allowlist.get("files"), dict):
        raise RuntimeError("invalid Python legacy-reference allowlist schema")

    expected = allowlist["files"]
    issues = []
    for path in sorted(set(records) | set(expected)):
        actual_lines = records.get(path)
        pinned = expected.get(path)
        if actual_lines is None:
            issues.append({"file": path, "issue": "stale allowlist entry"})
            continue
        if pinned is None:
            issues.append({"file": path, "issue": "unreviewed legacy reference"})
            continue
        actual_digest = python_reference_digest(actual_lines)
        if (pinned.get("count") != len(actual_lines)
                or pinned.get("sha256") != actual_digest
                or not str(pinned.get("reason") or "").strip()):
            issues.append({
                "file": path,
                "issue": "reviewed legacy references changed",
                "expected_count": pinned.get("count"),
                "actual_count": len(actual_lines),
                "expected_sha256": pinned.get("sha256"),
                "actual_sha256": actual_digest,
            })
    return issues


def tracked_oramap_archives() -> list[pathlib.Path]:
    proc = subprocess.run(
        ["git", "ls-files", "*.oramap", "-z"], cwd=ROOT,
        check=True, capture_output=True)
    return sorted(ROOT / raw for raw in proc.stdout.decode("utf-8").split("\0") if raw)


def stale_oramap_references(paths: list[pathlib.Path], template_map: dict[str, str],
                            inner_map: dict[str, str]) -> list[dict]:
    """Old cohort IDs inside tracked map-package text members."""
    tokens = list(template_map) + list(inner_map)
    out = []
    for path in paths:
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                if pathlib.PurePosixPath(member).suffix.lower() not in RUNTIME_SOURCE_SUFFIXES:
                    continue
                try:
                    text = archive.read(member).decode("utf-8-sig")
                except UnicodeDecodeError as exc:
                    raise RuntimeError(
                        f"could not decode tracked map member {norm(path)}!{member}") from exc
                for line_no, line in enumerate(text.splitlines(), 1):
                    found = [token for token in tokens if token in line]
                    if found:
                        out.append({
                            "file": norm(path), "member": member,
                            "line": line_no, "tokens": found,
                        })
    return out


def affected_sources(paths: list[pathlib.Path], replacements: dict[str, str]) -> list[pathlib.Path]:
    needles = tuple(old.encode("utf-8") for old in replacements)
    return [path for path in paths if any(needle in path.read_bytes() for needle in needles)]


def dirty_paths(paths: list[pathlib.Path]) -> list[str]:
    if not paths:
        return []
    rel = [norm(path) for path in paths]
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1", "--", *rel], cwd=ROOT,
        check=True, capture_output=True, text=True, encoding="utf-8")
    return [line for line in proc.stdout.splitlines() if line.strip()]


def rewrite(paths: list[pathlib.Path], replacements: dict[str, str]) -> dict[str, int]:
    counts = {old: 0 for old in replacements}
    ordered = sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True)
    for path in paths:
        raw = path.read_text(encoding="utf-8-sig")
        for old, new in ordered:
            found = raw.count(old)
            if found:
                raw = raw.replace(old, new)
                counts[old] += found
        path.write_text(raw, encoding="utf-8", newline="")
    return counts


def canonical_node(node, name_map: dict[str, str]):
    return [
        apply_map(str(node.key), name_map),
        apply_map(str(node.value or "").strip(), name_map),
        [canonical_node(child, name_map) for child in node.children],
    ]


def resolved_dump(rs: Ruleset, name_map: dict[str, str]) -> bytes:
    rows = {}
    for name in sorted(rs.weapons):
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            raise RuntimeError(f"could not resolve active weapon definition {name}")
        mapped_name = apply_map(name, name_map)
        if mapped_name in rows:
            raise RuntimeError(f"resolved dump name collision: {mapped_name}")
        rows[mapped_name] = canonical_node(resolved, name_map)
    return (json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8")


def stale_source_references(paths: list[pathlib.Path], template_map: dict[str, str],
                            inner_map: dict[str, str]) -> list[dict]:
    tokens = list(template_map) + list(inner_map)
    out = []
    for path in paths:
        for line_no, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            found = [token for token in tokens if token in line]
            if found:
                out.append({"file": norm(path), "line": line_no, "tokens": found})
    return out


def proof_report(before: Ruleset, after: Ruleset, paths: list[pathlib.Path], counts: dict[str, int],
                 template_map: dict[str, str], inner_map: dict[str, str],
                 full_map: dict[str, str]) -> dict:
    baseline = resolved_dump(before, full_map)
    candidate = resolved_dump(after, {})
    stale = stale_source_references(active_sources(after), template_map, inner_map)
    concrete = sum(not name.startswith("^") for name in after.weapons)
    templates = len(after.weapons) - concrete
    return {
        "schema": 1,
        "scope": "R12 36-template pure rename across active rules and weapons",
        "counts": {
            "active_weapon_definitions": len(after.weapons),
            "active_concrete_weapons": concrete,
            "active_weapon_templates": templates,
            "template_renames": len(template_map),
            "payload_renames": len(inner_map),
            "affected_active_files": len(paths),
            "source_replacements": sum(counts.values()),
            "stale_old_name_references": len(stale),
        },
        "resolved_dump": {
            "byte_identical_after_baseline_name_map": baseline == candidate,
            "bytes": len(candidate),
            "mapped_baseline_sha256": hashlib.sha256(baseline).hexdigest(),
            "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
        },
        "affected_files": [norm(path) for path in paths],
        "replacement_counts": counts,
        "template_renames": template_map,
        "payload_renames": inner_map,
        "stale_references": stale,
        "conclusion": (
            "The candidate is acceptable only when the canonical resolved dumps are byte-identical "
            "after applying the 36-template/36-payload name map to the baseline and no active "
            "source retains an old cohort name."
        ),
    }


def run(*, apply: bool, proof_path: pathlib.Path | None = None) -> dict:
    before = Ruleset(str(ROOT))
    template_map, inner_map, full_map = rename_maps(before)
    replacements = source_replacements(template_map, inner_map)
    runtime_replacements = {**replacements, **inner_map}
    sources = active_sources(before)
    affected = affected_sources(sources, replacements)
    runtime_sources = tracked_runtime_sources()
    active_set = {path.resolve() for path in sources}
    outside_runtime_consumers = [
        path for path in affected_sources(runtime_sources, runtime_replacements)
        if path.resolve() not in active_set
    ]
    if outside_runtime_consumers:
        names = "\n".join(norm(path) for path in outside_runtime_consumers)
        raise RuntimeError(
            "old cohort names exist outside active rule/weapon sources; review these runtime "
            f"consumers before renaming:\n{names}")
    python_issues = python_reference_issues(
        tracked_python_sources(), template_map, inner_map)
    if python_issues:
        names = "\n".join(
            f"{row['file']}: {row['issue']}" for row in python_issues)
        raise RuntimeError(
            "old cohort identifiers in Python tooling differ from the reviewed historical "
            f"inventory; classify them before renaming:\n{names}")
    archive_consumers = stale_oramap_references(
        tracked_oramap_archives(), template_map, inner_map)
    if archive_consumers:
        names = "\n".join(
            f"{row['file']}!{row['member']}:{row['line']}"
            for row in archive_consumers)
        raise RuntimeError(
            "old cohort names exist inside tracked map archives; review these consumers "
            f"before renaming:\n{names}")
    proof_target = (ROOT / proof_path).resolve() if proof_path else None
    if proof_target is not None and proof_target in {path.resolve() for path in sources}:
        raise RuntimeError(f"proof output overlaps active source: {proof_target}")
    dirty = dirty_paths(affected)
    if dirty:
        raise RuntimeError("affected active files are dirty:\n" + "\n".join(dirty))
    snapshots = {path: path.read_bytes() for path in affected}
    completed = False
    try:
        counts = rewrite(affected, replacements)
        after = Ruleset(str(ROOT))
        report = proof_report(
            before, after, affected, counts, template_map, inner_map, full_map)
        if not report["resolved_dump"]["byte_identical_after_baseline_name_map"]:
            raise RuntimeError("resolved dump changed outside the approved name map")
        if report["counts"]["stale_old_name_references"]:
            raise RuntimeError(
                f"{report['counts']['stale_old_name_references']} stale old-name references remain")
        if proof_target:
            proof_target.parent.mkdir(parents=True, exist_ok=True)
            proof_target.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not apply:
            for path, raw in snapshots.items():
                path.write_bytes(raw)
        completed = True
        return report
    finally:
        if not completed:
            for path, raw in snapshots.items():
                path.write_bytes(raw)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--proof", type=pathlib.Path)
    args = parser.parse_args(argv)
    try:
        report = run(apply=args.apply, proof_path=args.proof)
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"mode": "apply" if args.apply else "dry-run", **report["counts"],
                      **report["resolved_dump"]}, indent=2, sort_keys=True))
    if not args.apply:
        print("dry run: affected files restored byte-for-byte")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
