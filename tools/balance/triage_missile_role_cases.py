#!/usr/bin/env python3
"""Read-only triage for the remaining missile role/class decisions.

``audit_missile_role_family.py`` intentionally answers only one narrow
question: whether a resolved weapon's role agrees with its MissileHE/AA/AP
family.  This companion receipt adds the context needed before a correction:
inheritance provenance, resolved field locations, concrete actor consumers and
custom target vocabularies.  It never edits YAML, changes a role, or proposes
an automatic conversion.

The role ruling is still caller-owned policy.  A strict finding is therefore a
review lane, not a fix.  Blend families (Tesla, Cryo, Chemical, and so on)
and custom selectors are retained as separate evidence instead of being
forced into the three-domain rule.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import re
import sys
from typing import Iterable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "audit"))

import miniyaml
from audit_missile_role_family import (
    DAMAGE_TYPES,
    FAMILY_RE,
    ROLE_FAMILY,
    ROLE_FAMILIES,
    TWIN_MARKERS,
    main_families,
    weapon_role,
)


ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_JSON = ROOT / "docs" / "audit" / "latest" / "missile_role_triage_20260911.json"
DEFAULT_MD = ROOT / "docs" / "audit" / "latest" / "missile_role_triage_20260911.md"


def _value(node: miniyaml.Node, key: str) -> str | None:
    """Return a resolved direct child value, preserving empty as ``None``."""

    for child in node.children:
        if child.key == key:
            return child.value or None
    return None


def _field_source(node: miniyaml.Node, key: str) -> dict[str, object] | None:
    for child in node.children:
        if child.key == key:
            return {"value": child.value, "file": child.file, "line": child.line}
    return None


def inheritance_chain(rules: miniyaml.Ruleset, name: str, limit: int = 64) -> list[str]:
    """Return raw inheritance names in document order, with a cycle guard."""

    result: list[str] = []
    seen: set[str] = set()

    def visit(current: str) -> None:
        if len(result) >= limit:
            result.append("<depth-limit>")
            return
        node = rules.weapon(current)
        if node is None:
            return
        folded = current.lower()
        if folded in seen:
            result.append(f"<cycle:{current}>")
            return
        seen.add(folded)
        for _key, parent in rules.inherits_of(node):
            if not parent:
                continue
            result.append(parent)
            visit(parent)

    visit(name)
    return result


def _walk(node: miniyaml.Node, path: tuple[str, ...] = ()) -> Iterable[tuple[miniyaml.Node, tuple[str, ...]]]:
    for child in node.children:
        child_path = path + (child.key,)
        yield child, child_path
        yield from _walk(child, child_path)


def build_actor_consumer_index(rules: miniyaml.Ruleset) -> dict[str, list[dict[str, object]]]:
    """Index every resolved actor ``Weapon:`` route once for the whole scan."""

    index: dict[str, list[dict[str, object]]] = collections.defaultdict(list)
    for actor in sorted(rules.actors):
        if actor.startswith("^"):
            continue
        resolved = rules.resolve(actor)
        if resolved is None:
            continue
        for child, path in _walk(resolved):
            if child.key != "Weapon" or not (child.value or "").strip():
                continue
            index[child.value.strip().lower()].append(
                {
                    "actor": actor,
                    "route": ".".join(path[:-1]) or "<root>",
                    "source": {"file": child.file, "line": child.line},
                }
            )
    return index


def actor_consumers(
    rules: miniyaml.Ruleset,
    weapon: str,
    index: dict[str, list[dict[str, object]]] | None = None,
) -> list[dict[str, object]]:
    """Find resolved actor traits that name ``weapon``.

    This deliberately records every ``Weapon:`` route, including death and
    support traits.  A consumer is evidence of reachability, not proof that a
    route is active in a normal combat state.
    """

    if index is not None:
        return list(index.get(weapon.lower(), []))
    target = weapon.lower()
    rows: list[dict[str, object]] = []
    for actor in sorted(rules.actors):
        if actor.startswith("^"):
            continue
        resolved = rules.resolve(actor)
        if resolved is None:
            continue
        for child, path in _walk(resolved):
            if child.key != "Weapon" or (child.value or "").strip().lower() != target:
                continue
            rows.append(
                {
                    "actor": actor,
                    "route": ".".join(path[:-1]) or "<root>",
                    "source": {"file": child.file, "line": child.line},
                }
            )
    return rows


def custom_role_bucket(valid: str | None, invalid: str | None) -> str:
    """Explain why a selector is withheld from the three-domain role rule."""

    valid_tokens = {token.strip() for token in (valid or "").split(",") if token.strip()}
    invalid_tokens = {token.strip() for token in (invalid or "").split(",") if token.strip()}
    effective_tokens = valid_tokens - invalid_tokens
    if not effective_tokens:
        return "empty-after-invalid"
    if effective_tokens <= {"Water", "Underwater", "Bridge"}:
        return "water-or-underwater"
    if effective_tokens <= {"Ground", "Water", "Air"}:
        return "domain-empty-or-invalid"
    if effective_tokens & {"Ship", "Submarine"} and not effective_tokens & {"Air", "Ground"}:
        return "naval-recipient"
    if effective_tokens & {"lockon", "Vehicle", "Structure", "Garrisoned", "Infantry", "Monster"}:
        return "recipient-type-selector"
    if invalid_tokens:
        return "custom-invalid-targets"
    return "custom-vocabulary"


def _family_sources(node: miniyaml.Node) -> list[dict[str, object]]:
    rows = []
    for child in node.children:
        if not child.key.startswith("Warhead@"):
            continue
        if (child.value or "").strip() not in DAMAGE_TYPES:
            continue
        if any(marker in child.key.lower() for marker in TWIN_MARKERS):
            continue
        match = FAMILY_RE.match(child.key)
        if match:
            rows.append(
                {
                    "family": match.group(1),
                    "key": child.key,
                    "type": child.value,
                    "file": child.file,
                    "line": child.line,
                }
            )
    return rows


def _role_finding(
    rules: miniyaml.Ruleset,
    name: str,
    role: str,
    family: str,
    code: str,
    consumer_index: dict[str, list[dict[str, object]]],
) -> dict[str, object]:
    node = rules.resolve_weapon(name)
    assert node is not None
    valid = _value(node, "ValidTargets")
    invalid = _value(node, "InvalidTargets")
    return {
        "code": code,
        "weapon": name,
        "role": role,
        "flies": family,
        "expected": ROLE_FAMILY[role],
        "valid_targets": valid or "Ground, Water (engine default)",
        "invalid_targets": invalid or "",
        "valid_targets_source": _field_source(node, "ValidTargets"),
        "invalid_targets_source": _field_source(node, "InvalidTargets"),
        "family_sources": _family_sources(node),
        "weapon_source": {"file": node.file, "line": node.line},
        "inheritance_chain": inheritance_chain(rules, name),
        "actor_consumers": actor_consumers(rules, name, consumer_index),
        "review_status": "REVIEW_REQUIRED",
    }


def scan(rules: miniyaml.Ruleset) -> dict[str, object]:
    findings: dict[str, list[dict[str, object]]] = collections.defaultdict(list)
    custom: list[dict[str, object]] = []
    blends: collections.Counter[str] = collections.Counter()
    scanned = 0
    conforming = 0
    consumer_index = build_actor_consumer_index(rules)

    for name in sorted(rules.weapons):
        if name.startswith("^"):
            continue
        node = rules.resolve_weapon(name)
        if node is None:
            continue
        families = main_families(node)
        if not families:
            continue
        scanned += 1
        role = weapon_role(node)
        if role == "custom":
            valid = _value(node, "ValidTargets")
            invalid = _value(node, "InvalidTargets")
            custom.append(
                {
                    "weapon": name,
                    "valid_targets": valid or "Ground, Water (engine default)",
                    "invalid_targets": invalid or "",
                    "bucket": custom_role_bucket(valid, invalid),
                    "family_sources": _family_sources(node),
                    "inheritance_chain": inheritance_chain(rules, name),
                    "actor_consumers": actor_consumers(rules, name, consumer_index),
                    "review_status": "DOMAIN_REVIEW_REQUIRED",
                }
            )
            continue
        expected = ROLE_FAMILY[role]
        for family in sorted(families):
            if family not in ROLE_FAMILIES:
                blends[family] += 1
                continue
            if family == expected:
                conforming += 1
                continue
            code = {"ground": "R1", "air": "R2", "both": "R3"}[role]
            finding = _role_finding(rules, name, role, family, code, consumer_index)
            findings[code].append(finding)
            if family == "MissileHE" and role in ("air", "both"):
                findings["R4"].append({**finding, "code": "R4"})

    questions: list[dict[str, object]] = []
    v2 = [
        row
        for rows in findings.values()
        for row in rows
        if "v2rocketlauncher_scudtesla" in str(row["weapon"]).lower()
    ]
    # The Tesla V2 is a known policy question even though its blend family is
    # outside the strict HE/AA/AP gate.  Pull its resolved parent and all
    # consumer routes into the same receipt instead of hiding it in prose.
    v2_names = sorted(
        name
        for name in rules.weapons
        if "v2rocketlauncher_scudtesla" in name.lower()
    )
    for name in v2_names:
        node = rules.resolve_weapon(name)
        if node is None:
            continue
        questions.append(
            {
                "subject": "V2 Tesla SCUD parent Air role",
                "weapon": name,
                "valid_targets": _value(node, "ValidTargets") or "Ground, Water (engine default)",
                "invalid_targets": _value(node, "InvalidTargets") or "",
                "inheritance_chain": inheritance_chain(rules, name),
                "actor_consumers": actor_consumers(rules, name, consumer_index),
                "evidence": "The Tesla child inherits the SCUD parent and keeps Air excluded on its resolved damage channels; deciding whether the parent should expose Air is a policy/runtime question.",
                "review_status": "POLICY_REVIEW_REQUIRED",
            }
        )

    strict = {code: sorted(rows, key=lambda row: row["weapon"]) for code, rows in findings.items()}
    return {
        "summary": {
            "scanned_missile_weapons": scanned,
            "conforming_role_family_pairs": conforming,
            "strict_counts": {code: len(strict.get(code, [])) for code in ("R1", "R2", "R3", "R4")},
            "custom_selector_count": len(custom),
            "blend_family_counts": dict(sorted(blends.items())),
            "policy_question_count": len(questions),
        },
        "strict_findings": strict,
        "custom_selectors": sorted(custom, key=lambda row: row["weapon"]),
        "policy_questions": questions,
        "scope": "active concrete resolved weapons and resolved actor Weapon routes",
        "limitations": [
            "A consumer route is reachability evidence, not proof of active combat activation.",
            "Custom recipient tags, spawned actors, map-local weapons and runtime target filters remain unresolved.",
            "The receipt proposes no family, ValidTargets, InvalidTargets, damage, projectile or Versus edit.",
        ],
    }


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_receipt(root: pathlib.Path = ROOT) -> dict[str, object]:
    rules = miniyaml.Ruleset(root)
    result = scan(rules)
    tool_path = pathlib.Path(__file__).resolve()
    source_paths = [root / "mods" / "cameo" / "mod.yaml"] + list(rules.manifest.weapons)
    source_hashes = {
        str(path.relative_to(root)).replace("\\", "/"): _sha256(path)
        for path in source_paths
        if path.exists()
    }
    result["metadata"] = {
        "tool": "tools/balance/triage_missile_role_cases.py",
        "tool_sha256": _sha256(tool_path),
        "generated_from": str(root),
        "source_file_count": len(source_hashes),
        "source_sha256": source_hashes,
    }
    return result


def _md_source(source: dict[str, object] | None) -> str:
    if not source:
        return ""
    path = str(source.get("file", "")).replace(str(ROOT) + "\\", "").replace("\\", "/")
    return f"`{path}:{source.get('line', '')}`"


def render_markdown(receipt: dict[str, object]) -> str:
    summary = receipt["summary"]
    out = [
        "# Missile role and class triage",
        "",
        "This is a read-only review receipt. Strict findings are policy lanes;",
        "they do not authorize a family, target-mask, damage or Versus edit.",
        "",
        "## Current counts",
        "",
        "| code | review lane | count |",
        "|---|---|---:|",
        f"| R1 | ground-only route flying MissileAA/AP | {summary['strict_counts']['R1']} |",
        f"| R2 | air-only route flying MissileHE/AP | {summary['strict_counts']['R2']} |",
        f"| R3 | dual-domain route flying MissileHE/AA | {summary['strict_counts']['R3']} |",
        f"| R4 | MissileHE reachable against Air | {summary['strict_counts']['R4']} |",
        f"| custom | recipient or non-domain selector | {summary['custom_selector_count']} |",
        "",
        f"Scanned **{summary['scanned_missile_weapons']}** concrete weapons; **{summary['conforming_role_family_pairs']}** recognized role/family pairs conform. The receipt also records **{summary['policy_question_count']}** explicit policy question(s).",
        "",
    ]
    for code in ("R1", "R2", "R3", "R4"):
        rows = receipt["strict_findings"].get(code, [])
        out += [f"## {code} strict findings", "", "| weapon | role | flies | expected | consumers | resolved family source |", "|---|---|---|---|---:|---|"]
        if not rows:
            out.append("| _none_ |  |  |  | 0 |  |")
        for row in rows:
            sources = ", ".join(
                _md_source({"file": item["file"], "line": item["line"]})
                for item in row["family_sources"]
                if item["family"] == row["flies"]
            )
            out.append(
                f"| `{row['weapon']}` | {row['role']} | {row['flies']} | {row['expected']} | {len(row['actor_consumers'])} | {sources} |"
            )
        out += ["", "Each row retains its valid/invalid target fields, inheritance chain and consumer routes in the JSON receipt.", ""]
    out += ["## Custom selectors", "", "| weapon | selector | bucket | consumers |", "|---|---|---|---:|"]
    for row in receipt["custom_selectors"]:
        selector = row["valid_targets"] + (f" / invalid {row['invalid_targets']}" if row["invalid_targets"] else "")
        out.append(f"| `{row['weapon']}` | `{selector}` | {row['bucket']} | {len(row['actor_consumers'])} |")
    if not receipt["custom_selectors"]:
        out.append("| _none_ |  |  | 0 |")
    out += ["", "Custom selectors need recipient-type or runtime evidence; they are not silently classified as ground, air or dual.", ""]
    out += ["## Explicit policy questions", "", "| subject | weapon | resolved selector | status |", "|---|---|---|---|"]
    for row in receipt["policy_questions"]:
        out.append(f"| {row['subject']} | `{row['weapon']}` | `{row['valid_targets']}` | {row['review_status']} |")
    if not receipt["policy_questions"]:
        out.append("| _none_ |  |  |  |")
    out += ["", "The V2 Tesla SCUD row preserves the SCUD inheritance and Air exclusions so a parent-role decision can be made explicitly.", ""]
    out += ["## Limits", ""]
    out.extend(f"- {limit}" for limit in receipt["limitations"])
    out += ["", "JSON receipt: `docs/audit/latest/missile_role_triage_20260911.json`. "]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--json", type=pathlib.Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown", type=pathlib.Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)
    receipt = build_receipt(args.root.resolve())
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(render_markdown(receipt), encoding="utf-8")
    print(json.dumps(receipt["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
