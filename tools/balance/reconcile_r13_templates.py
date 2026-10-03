#!/usr/bin/env python3
"""Reconcile R13's missing-template count against the current resolved ruleset.

Read-only. Distinguishes missing template definitions from the direct users they serve and
checks whether an exact legacy payload already exists elsewhere.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools" / "audit"), str(ROOT / "tools" / "balance")]

from miniyaml import Ruleset  # noqa: E402
from promote_compatibility_warheads import twin_of  # noqa: E402
from resolved_gate import pairs  # noqa: E402


FAMILY_LEVEL = re.compile(r"^\^Warhead_[A-Za-z0-9]+_(?:Trace|Light|Medium|Heavy|Super)$")


def norm(path) -> str:
    value = pathlib.Path(path)
    if value.is_absolute():
        value = value.resolve().relative_to(ROOT.resolve())
    return value.as_posix()


def normalized_inner_key(key: str) -> str:
    return key.replace("Compatibility", "")


def payload_signature(node) -> tuple[str, frozenset[str]]:
    """Warhead class plus recursive fields; the outer node key is intentionally excluded."""
    return str(node.value or "").strip(), frozenset(pairs(node))


def direct_users(rs: Ruleset, template: str) -> list[dict]:
    out = []
    for name, node in sorted(rs.weapons.items()):
        if name.startswith("^"):
            continue
        if any(child.key.split("@")[0] == "Inherits" and
               str(child.value).strip() == template for child in node.children):
            out.append({"weapon": name, "file": norm(node.file), "line": node.line})
    return out


def exact_legacy_providers(rs: Ruleset, inner) -> list[dict]:
    wanted = normalized_inner_key(inner.key)
    expected = payload_signature(inner)
    out = []
    for name, node in sorted(rs.weapons.items()):
        if not name.startswith("^") or name.startswith("^Compatibility_"):
            continue
        child = node.child(wanted)
        if child is None:
            continue
        out.append({"template": name, "file": norm(node.file), "line": child.line,
                    "payload_identical": payload_signature(child) == expected})
    return out


def build_report() -> dict:
    rs = Ruleset(str(ROOT))
    rows = []
    for name, node in sorted(rs.weapons.items()):
        if not name.startswith("^Compatibility_") or twin_of(name, rs.weapons):
            continue
        inner = next((child for child in node.children if child.key.startswith("Warhead@")), None)
        if inner is None:
            continue
        providers = exact_legacy_providers(rs, inner)
        users = direct_users(rs, name)
        rows.append({
            "compatibility_template": name,
            "file": norm(node.file),
            "line": node.line,
            "inner_key": inner.key,
            "renamed_inner_key": normalized_inner_key(inner.key),
            "direct_users": users,
            "direct_user_count": len(users),
            "exact_legacy_providers": providers,
            "family_level_generator_target": bool(FAMILY_LEVEL.match(name.replace("^Compatibility_", "^Warhead_"))),
            "classification": ("exact_auxiliary_payload_without_standalone_template"
                               if any(item["payload_identical"] for item in providers)
                               else "special_payload_without_standalone_template"),
        })
    distinct_users = {user["weapon"] for row in rows for user in row["direct_users"]}
    return {
        "schema": 1,
        "scope": "R13 current-tree count and payload reconciliation; read-only",
        "counts": {
            "missing_template_definitions": len(rows),
            "direct_relationships": sum(row["direct_user_count"] for row in rows),
            "distinct_weapons": len(distinct_users),
            "with_exact_legacy_payload": sum(any(p["payload_identical"]
                                                  for p in row["exact_legacy_providers"])
                                             for row in rows),
            "family_level_generator_targets": sum(row["family_level_generator_target"] for row in rows),
        },
        "templates": rows,
        "conclusion": (
            "The current tree has three unmatched compatibility template definitions, sixteen "
            "direct template-weapon relationships, and fourteen distinct weapons. This reconciles "
            "the current count but does not prove what the historical wording meant. None of the "
            "three definitions is a standard family-level generator target."
        ),
    }


def markdown(report: dict) -> str:
    counts = report["counts"]
    lines = [
        "# R13 missing-template reconciliation",
        "",
        "**Read-only current-tree measurement. No YAML or generator output is changed.**",
        "",
        report["conclusion"],
        "",
        f"Missing definitions: **{counts['missing_template_definitions']}**; direct relationships: "
        f"**{counts['direct_relationships']}** across **{counts['distinct_weapons']}** distinct weapons; "
        f"field/type-identical legacy payload already exists for "
        f"**{counts['with_exact_legacy_payload']}**; standard family-level generator targets: "
        f"**{counts['family_level_generator_targets']}**.",
        "",
        "| compatibility template | direct relationships | renamed inner key | field/type-identical legacy provider | classification |",
        "|---|---:|---|---|---|",
    ]
    for row in report["templates"]:
        providers = ", ".join(
            f"`{provider['template']}` ({'identical' if provider['payload_identical'] else 'different'})"
            for provider in row["exact_legacy_providers"]) or "none"
        lines.append(f"| `{row['compatibility_template']}` | {row['direct_user_count']} | "
                     f"`{row['renamed_inner_key']}` | {providers} | `{row['classification']}` |")
    lines += ["", "## Direct users", ""]
    for row in report["templates"]:
        lines.append(f"### `{row['compatibility_template']}`")
        lines.append("")
        for user in row["direct_users"]:
            lines.append(f"- `{user['weapon']}` — `{user['file']}`")
        lines.append("")
    lines += [
        "## Decision boundary",
        "",
        "Do not ask `gen_weapon_template.py` to emit sixteen family/level templates. The two "
        "extra-damage cases are exact auxiliary payloads embedded in legacy templates, and the "
        "TankBuster case is a one-user special slice. R13 must be composed with R12's per-user "
        "closure so the new standalone names do not preserve or create a second warhead inherit. "
        "Any writer still needs resolved field/order comparison and a cohort boot gate.",
        "",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", type=pathlib.Path)
    parser.add_argument("--markdown", type=pathlib.Path)
    args = parser.parse_args(argv)
    report = build_report()
    if args.json:
        (ROOT / args.json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")
    if args.markdown:
        (ROOT / args.markdown).write_text(markdown(report), encoding="utf-8")
    if not args.json and not args.markdown:
        print(markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
