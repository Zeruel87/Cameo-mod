#!/usr/bin/env python3
"""Measure the complete R12 compatibility-template consumer closure.

Read-only.  The report distinguishes concrete weapon users from template users and
simulates the proposed "chain the matching twin, drop the duplicate direct inherit"
rewrite in memory.  It does not edit YAML.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools" / "audit"), str(ROOT / "tools" / "balance")]

from miniyaml import Node, Ruleset  # noqa: E402
from promote_compatibility_warheads import new_template_name, twin_of  # noqa: E402
from resolved_gate import compare  # noqa: E402


COMPATIBILITY_PREFIX = "^Compatibility_"


def norm(path) -> str:
    value = pathlib.Path(path)
    if value.is_absolute():
        value = value.resolve().relative_to(ROOT.resolve())
    return value.as_posix()


def inherits(node) -> list[tuple[Node, str]]:
    return [
        (child, str(child.value).strip())
        for child in node.children
        if child.key.split("@")[0] == "Inherits"
    ]


def relationship_rows(rs: Ruleset) -> list[dict]:
    templates = {name for name in rs.weapons if name.startswith(COMPATIBILITY_PREFIX)}
    rows = []
    for consumer, node in sorted(rs.weapons.items()):
        direct = [value for _child, value in inherits(node)]
        for template in direct:
            if template not in templates:
                continue
            twin = twin_of(template, rs.weapons)
            rows.append({
                "consumer": consumer,
                "consumer_kind": "template" if consumer.startswith("^") else "weapon",
                "file": norm(node.file),
                "line": node.line,
                "compatibility_template": template,
                "matching_twin": twin,
                "classification": (
                    "missing_twin" if twin is None else
                    "already_inherits_twin" if twin in direct else
                    "exposed_without_twin"
                ),
            })
    return rows


def simulated_chain_diffs(before: Ruleset, relationships: list[dict]) -> dict[str, dict]:
    """Return concrete resolved diffs for the literal R12 chain proposal.

    The compatibility template inherits its twin before its local payload.  A consumer
    that already directly inherits the twin loses one direct twin inherit.  This mirrors
    the structural proposal without renaming keys, so every reported delta is behavioral.
    """
    candidate = Ruleset(str(ROOT))
    for template in sorted({row["compatibility_template"] for row in relationships}):
        twin = twin_of(template, candidate.weapons)
        if twin is None:
            continue
        candidate.weapons[template].children.insert(
            0, Node("Inherits@R12Twin", twin, file="<R12 simulation>", line=0))

    for row in relationships:
        if row["classification"] != "already_inherits_twin":
            continue
        node = candidate.weapons[row["consumer"]]
        twin = row["matching_twin"]
        removed = False
        kept = []
        for child in node.children:
            is_target = (
                child.key.split("@")[0] == "Inherits"
                and str(child.value).strip() == twin
            )
            if is_target and not removed:
                removed = True
                continue
            kept.append(child)
        if not removed:
            raise RuntimeError(f"simulation could not remove {twin} from {row['consumer']}")
        node.children = kept

    candidate._resolve_cache.clear()
    out = {}
    for weapon in sorted(before.weapons):
        if weapon.startswith("^"):
            continue
        diff = compare(before.resolve_weapon(weapon), candidate.resolve_weapon(weapon))
        if diff:
            out[weapon] = diff
    return out


def proposed_inner_name(old: str) -> str:
    """Remove Compatibility while keeping collision-prone auxiliary payloads distinct."""
    if not old.endswith("Compatibility"):
        raise ValueError(f"not a compatibility payload: {old}")
    new = old[:-len("Compatibility")]
    if new.endswith("Flat"):
        new = new[:-len("Flat")] + "_Flat"
    if new in {"LaserExtraDamage", "RailgunExtraDamage"}:
        new += "_Auxiliary"
    return new


def simulated_pure_rename_diffs(before: Ruleset) -> tuple[dict[str, dict], dict, dict]:
    """Rename deprecated template/payload keys in memory without changing inheritance."""
    candidate = Ruleset(str(ROOT))
    templates = sorted(name for name in before.weapons if name.startswith(COMPATIBILITY_PREFIX))
    template_map = {name: new_template_name(name) for name in templates}
    collisions = sorted(name for name in template_map.values() if name in before.weapons)
    if collisions:
        raise RuntimeError(f"proposed template name collision: {collisions}")

    inner_map = {}
    for template in templates:
        for child in before.weapons[template].children:
            base = child.key.lstrip("-")
            if base.startswith("Warhead@") and base.endswith("Compatibility"):
                old = base[len("Warhead@"):]
                inner_map[old] = proposed_inner_name(old)

    for old, new in template_map.items():
        node = candidate.weapons.pop(old)
        node.key = new
        candidate.weapons[new] = node

    def walk(node):
        for child in node.children:
            if child.key.split("@")[0] == "Inherits":
                inherited = str(child.value).strip()
                if inherited in template_map:
                    child.value = template_map[inherited]
            negative = child.key.startswith("-")
            base = child.key[1:] if negative else child.key
            if base.startswith("Warhead@"):
                old = base[len("Warhead@"):]
                if old in inner_map:
                    child.key = ("-" if negative else "") + "Warhead@" + inner_map[old]
            walk(child)

    for node in candidate.weapons.values():
        walk(node)
    candidate._resolve_cache.clear()

    rename_map = dict(template_map)
    for old, new in inner_map.items():
        rename_map["Warhead@" + old] = "Warhead@" + new
        rename_map["-Warhead@" + old] = "-Warhead@" + new
    diffs = {}
    for weapon in sorted(before.weapons):
        if weapon.startswith("^"):
            continue
        diff = compare(before.resolve_weapon(weapon), candidate.resolve_weapon(weapon), rename_map)
        if diff:
            diffs[weapon] = diff
    return diffs, template_map, inner_map


def summarize_diffs(diffs: dict[str, dict]) -> dict:
    def pure_reorder(diff: dict) -> bool:
        return (
            diff.get("reordered_only") is True
            and not diff.get("lost")
            and not diff.get("gained")
        )

    return {
        "changed_concrete_weapons_in_full_descendant_closure": len(diffs),
        "field_pairs_lost": sum(len(diff.get("lost", ())) for diff in diffs.values()),
        "field_pairs_gained": sum(len(diff.get("gained", ())) for diff in diffs.values()),
        "warhead_order_changes": sum("order_before" in diff for diff in diffs.values()),
        "pure_warhead_reorders": sum(pure_reorder(diff) for diff in diffs.values()),
    }


def summarize_direct_groups(relationships: list[dict], diffs: dict[str, dict]) -> dict:
    out = {}
    for classification in (
        "already_inherits_twin", "exposed_without_twin", "missing_twin"
    ):
        consumers = {
            row["consumer"] for row in relationships
            if row["consumer_kind"] == "weapon"
            and row["classification"] == classification
        }
        changed = consumers & set(diffs)
        out[classification] = {
            "distinct_direct_weapons": len(consumers),
            "changed_direct_weapons": len(changed),
            "warhead_order_changes": sum("order_before" in diffs[name] for name in changed),
            "pure_warhead_reorders": sum(
                diffs[name].get("reordered_only") is True
                and not diffs[name].get("lost")
                and not diffs[name].get("gained")
                for name in changed),
            "with_field_deltas": sum(
                bool(diffs[name].get("lost") or diffs[name].get("gained"))
                for name in changed),
        }
    return out


def build_report() -> dict:
    rs = Ruleset(str(ROOT))
    relationships = relationship_rows(rs)
    by_class = collections.Counter(row["classification"] for row in relationships)
    concrete = [row for row in relationships if row["consumer_kind"] == "weapon"]
    template_users = [row for row in relationships if row["consumer_kind"] == "template"]
    templates = sorted(name for name in rs.weapons if name.startswith(COMPATIBILITY_PREFIX))
    per_template = []
    for template in templates:
        mine = [row for row in relationships if row["compatibility_template"] == template]
        classes = collections.Counter(row["classification"] for row in mine)
        per_template.append({
            "compatibility_template": template,
            "matching_twin": twin_of(template, rs.weapons),
            "relationships": len(mine),
            "weapon_consumers": sum(row["consumer_kind"] == "weapon" for row in mine),
            "template_consumers": sum(row["consumer_kind"] == "template" for row in mine),
            "already_inherits_twin": classes["already_inherits_twin"],
            "exposed_without_twin": classes["exposed_without_twin"],
            "missing_twin": classes["missing_twin"],
        })

    diffs = simulated_chain_diffs(rs, relationships)
    rename_diffs, template_map, inner_map = simulated_pure_rename_diffs(rs)
    return {
        "schema": 1,
        "scope": "R12 complete direct consumer inventory plus in-memory descendant-closure simulation; read-only",
        "counts": {
            "compatibility_templates": len(templates),
            "all_direct_relationships": len(relationships),
            "concrete_weapon_relationships": len(concrete),
            "template_relationships": len(template_users),
            "distinct_concrete_weapons": len({row["consumer"] for row in concrete}),
            "distinct_template_consumers": len({row["consumer"] for row in template_users}),
            "already_inherits_twin_all_consumers": by_class["already_inherits_twin"],
            "exposed_without_twin_all_consumers": by_class["exposed_without_twin"],
            "missing_twin_all_consumers": by_class["missing_twin"],
        },
        "simulation": {
            **summarize_diffs(diffs),
            "direct_consumer_groups": summarize_direct_groups(relationships, diffs),
        },
        "pure_rename_simulation": {
            "changed_concrete_weapons": len(rename_diffs),
            "template_renames": template_map,
            "payload_renames": inner_map,
            "collision_avoidance": {
                "LaserExtraDamageCompatibility": inner_map.get("LaserExtraDamageCompatibility"),
                "RailgunExtraDamageCompatibility": inner_map.get("RailgunExtraDamageCompatibility"),
            },
        },
        "template_consumers": template_users,
        "templates": per_template,
        "decision": (
            "The historical 369/139/214/16 figures count concrete weapon relationships only. "
            "Complete direct closure adds one template consumer, ^Warhead_IncendiaryYakComposition, "
            "which already inherits the matching twin. A uniform twin-before-payload chain "
            "position reorders warheads for 30 direct consumers that already inherit their twin; "
            "the exposed-user changes are the expected input to measured suppression. A separate "
            "pure-rename simulation removes the Compatibility names owned by this 36-template "
            "cohort with zero "
            "resolved field or order changes by keeping the two collision-prone extra-damage payloads "
            "distinct as _Auxiliary. This is the safest implementation candidate, but it needs a "
            "maintainer ruling because it deliberately does not add twin chaining."
        ),
    }


def markdown(report: dict) -> str:
    c = report["counts"]
    s = report["simulation"]
    already = s["direct_consumer_groups"]["already_inherits_twin"]
    exposed = s["direct_consumer_groups"]["exposed_without_twin"]
    rename = report["pure_rename_simulation"]
    lines = [
        "# R12 compatibility consumer closure",
        "",
        "**Read-only. The simulation edits only an in-memory ruleset.**",
        "",
        report["decision"],
        "",
        "## Inventory",
        "",
        f"- Compatibility templates: **{c['compatibility_templates']}**",
        f"- Direct relationships: **{c['all_direct_relationships']}** = "
        f"**{c['concrete_weapon_relationships']}** concrete + "
        f"**{c['template_relationships']}** template",
        f"- Distinct concrete weapons: **{c['distinct_concrete_weapons']}**",
        f"- Already inherits matching twin: **{c['already_inherits_twin_all_consumers']}**",
        f"- Exposed without matching twin: **{c['exposed_without_twin_all_consumers']}**",
        f"- Missing matching twin: **{c['missing_twin_all_consumers']}**",
        "",
        "The extra non-concrete edge is "
        "`^Warhead_IncendiaryYakComposition -> ^Compatibility_Flame_LightFlat`; "
        "the consumer also directly inherits `^Warhead_Flame_Light`.",
        "",
        "## Literal chain simulation",
        "",
        "The simulation makes every matched compatibility template inherit its twin before "
        "the local payload and removes one duplicate direct twin inherit from each already-twin "
        "consumer. It then compares every resolved concrete weapon, including descendants.",
        "",
        f"- Changed concrete weapons: **{s['changed_concrete_weapons_in_full_descendant_closure']}**",
        f"- Warhead-order changes: **{s['warhead_order_changes']}** "
        f"({s['pure_warhead_reorders']} pure reorders)",
        f"- Resolved field pairs gained/lost: **{s['field_pairs_gained']} / {s['field_pairs_lost']}**",
        f"- Already-twin direct consumers changed: **{already['changed_direct_weapons']} / "
        f"{already['distinct_direct_weapons']}**; all "
        f"**{already['warhead_order_changes']}** include a warhead-order change",
        f"- Exposed direct consumers changed: **{exposed['changed_direct_weapons']} / "
        f"{exposed['distinct_direct_weapons']}**; these are the inputs whose local "
        "suppressions must be measured",
        "",
        "This is a blocking correctness result for a bulk writer, not evidence that the debt "
        "should remain. The writer must preserve each consumer's original parent ordering, "
        "measure exposed-user suppressions from resolved diffs, and verify the complete concrete "
        "descendant closure with both field and warhead-order comparisons.",
        "",
        "The Python resolver is a planning gate. It does not certify engine duplicate-inheritance "
        "or removal legality; those remain separate blocking audits and one cohort boot after a "
        "candidate exists.",
        "",
        "## Zero-behavior alternative",
        "",
        f"A pure rename of **{len(rename['template_renames'])}** template keys and "
        f"**{len(rename['payload_renames'])}** payload keys changes "
        f"**{rename['changed_concrete_weapons']}** resolved concrete weapons.",
        "",
        "`LaserExtraDamageCompatibility` and `RailgunExtraDamageCompatibility` cannot collapse "
        "onto their existing unsuffixed keys: inherited payload/removal keys already use those "
        "names, and the direct unsuffixed proposal suppresses the renamed payload on fifteen "
        "resolved weapons. The exact rename therefore uses `LaserExtraDamage_Auxiliary` and "
        "`RailgunExtraDamage_Auxiliary`. This removes the deprecated word while preserving the "
        "two distinct payloads and their original firing positions.",
        "",
        "This candidate resolves the maintainer's deprecated-name goal with no behavior change, "
        "but it does not implement the current R12 text's twin chaining. Do not write YAML until "
        "the maintainer confirms that name retirement, rather than twin chaining itself, is the "
        "binding outcome.",
        "",
        "## Per-template direct relationships",
        "",
        "| template | twin | relationships | concrete | template | already | exposed | missing |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["templates"]:
        lines.append(
            f"| `{row['compatibility_template']}` | `{row['matching_twin'] or 'none'}` | "
            f"{row['relationships']} | {row['weapon_consumers']} | {row['template_consumers']} | "
            f"{row['already_inherits_twin']} | {row['exposed_without_twin']} | "
            f"{row['missing_twin']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", type=pathlib.Path)
    parser.add_argument("--markdown", type=pathlib.Path)
    args = parser.parse_args(argv)
    report = build_report()
    if args.json:
        (ROOT / args.json).write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown:
        (ROOT / args.markdown).write_text(markdown(report), encoding="utf-8")
    if not args.json and not args.markdown:
        print(markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
