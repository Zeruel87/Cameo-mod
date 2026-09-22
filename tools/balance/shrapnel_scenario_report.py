#!/usr/bin/env python3
"""Build a review-only FireShrapnel scenario receipt.

The report answers the narrow question that the balance model previously left
implicit: how many child emissions are credited when AimChance and target
availability are explicit?  It walks the resolved active ruleset, preserves
raw parent/emitter/fragment masks, and reports a flat-damage projection for
two named scenarios.  Percentage damage, armor, falloff, geometry, source
selection and runtime target availability remain separate limitations.

No result from this module is a price, a DPS vote or a YAML recommendation.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import pathlib
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
sys.path.insert(0, str(ROOT / "tools/balance"))

import diagnostic_output
from miniyaml import Ruleset
import shrapnel_damage


RANDOM_HIT_CREDIT = 0.5
DAMAGE_TYPES = {
    "AreaDamage",
    "SpreadDamage",
    "AreaDamagePercentage",
    "AffectsIntegrity",
}
DEFAULT_TARGETS = "Ground, Water"
DOMAIN_TAGS = {"Ground", "Water", "Air"}


def _sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _tokens(value):
    return {token.strip() for token in str(value).split(",") if token.strip()}


def _raw_target_tags(node):
    """Return raw and domain-level tags while retaining absent versus empty."""
    valid = node.child("ValidTargets") if node is not None else None
    invalid = node.child("InvalidTargets") if node is not None else None
    valid_raw = valid.value if valid is not None else None
    invalid_raw = invalid.value if invalid is not None else None
    allowed = _tokens(valid_raw if valid is not None else DEFAULT_TARGETS)
    excluded = _tokens(invalid_raw if invalid is not None else "")
    custom = sorted((allowed | excluded) - DOMAIN_TAGS)
    return {
        "valid_targets": valid_raw,
        "invalid_targets": invalid_raw,
        "allowed_tags": sorted(allowed),
        "invalid_tags": sorted(excluded),
        "domain_tags": sorted((allowed - excluded) & DOMAIN_TAGS),
        "custom_target_tags": custom,
        "excluded_custom_tags": sorted(excluded - DOMAIN_TAGS),
        "requires_custom_tag_review": bool(custom),
    }


def _safe_int(raw, default=None):
    try:
        return int(str(raw).strip()) if raw is not None else default
    except (TypeError, ValueError):
        return None


def _safe_bool(raw, default=True):
    if raw is None:
        return default
    text = str(raw).strip().lower()
    if text == "true":
        return True
    if text == "false":
        return False
    return None


def direct_payload(node):
    """Summarize authored damage channels without collapsing their semantics."""
    flat = 0.0
    flat_channels = []
    percentage_channels = []
    unsupported_channels = []
    for child in node.children:
        if child.key.split("@", 1)[0] != "Warhead" or child.value not in DAMAGE_TYPES:
            continue
        raw_damage = child.get("Damage")
        damage = _finite(raw_damage)
        record = {
            "warhead": child.key,
            "type": child.value,
            "damage_raw": raw_damage,
            "file": child.file,
            "line": child.line,
        }
        if child.value == "AffectsIntegrity":
            record["status"] = "INTEGRITY_CHANNEL_UNRESOLVED"
            unsupported_channels.append(record)
            continue
        if damage is None or damage < 0:
            record["status"] = "UNRESOLVED_DAMAGE"
            unsupported_channels.append(record)
            continue
        # An AreaDamage with PercentageScale has an automatic max-HP component;
        # keep its authored Damage in the flat projection but mark the missing
        # target-HP component explicitly.
        percentage_scale = _finite(child.get("PercentageScale"))
        has_percentage = child.value == "AreaDamagePercentage" or (
            percentage_scale is not None and percentage_scale != 0
        )
        if child.value != "AreaDamagePercentage" and child.get("PercentageScale") is not None and percentage_scale is None:
            has_percentage = True
        if has_percentage:
            record["status"] = "PERCENTAGE_OR_FOLDED"
            record["percentage_scale_raw"] = child.get("PercentageScale")
            percentage_channels.append(record)
        else:
            record["status"] = "FLAT_AUTHORED"
            flat_channels.append(record)
        flat += damage
    status = "FLAT_ONLY"
    if percentage_channels and flat_channels:
        status = "FLAT_PLUS_PERCENTAGE_UNRESOLVED"
    elif percentage_channels:
        status = "PERCENTAGE_COMPONENT_UNRESOLVED"
    if unsupported_channels:
        status = "UNRESOLVED_CHANNEL"
    return {
        "flat_damage": flat,
        "flat_channels": flat_channels,
        "percentage_channels": percentage_channels,
        "unsupported_channels": unsupported_channels,
        "status": status,
    }


def _edge_record(parent_name, parent, warhead, fragment, path):
    amount_raw = warhead.get("Amount")
    chance_raw = warhead.get("AimChance")
    throw_raw = warhead.get("ThrowWithoutTarget")
    try:
        amount = shrapnel_damage.expected_amount(amount_raw)
        amount_status = "RESOLVED"
    except (TypeError, ValueError):
        amount = None
        amount_status = "UNRESOLVED"
    chance = _safe_int(chance_raw, 0)
    throw = _safe_bool(throw_raw, True)
    parent_tags = _raw_target_tags(parent)
    fragment_tags = _raw_target_tags(fragment)
    parent_domains = set(parent_tags["domain_tags"])
    fragment_domains = set(fragment_tags["domain_tags"])
    if parent_tags["requires_custom_tag_review"] or fragment_tags["requires_custom_tag_review"]:
        mask_status = "CUSTOM_TAG_REVIEW"
    elif parent_domains == fragment_domains:
        mask_status = "MATCH"
    else:
        mask_status = "MISMATCH"
    if chance is None or chance < -2147483648 or chance > 2147483647:
        chance_status = "UNRESOLVED"
        abundant_credit = None
        no_target_credit = None
    else:
        chance_status = "RESOLVED"
        bounded = min(100, max(0, chance)) / 100.0
        abundant_credit = bounded + (1.0 - bounded) * RANDOM_HIT_CREDIT
        no_target_credit = (RANDOM_HIT_CREDIT if throw is True else 0.0
                            if throw is False else None)
    return {
        "parent": parent_name,
        "warhead": warhead.key,
        "fragment": fragment.key if fragment is not None else warhead.get("Weapon"),
        "path": path,
        "amount_raw": amount_raw,
        "expected_amount": amount,
        "amount_status": amount_status,
        "aim_chance_raw": chance_raw,
        "aim_chance": chance,
        "aim_chance_status": chance_status,
        "throw_without_target_raw": throw_raw,
        "throw_without_target": throw,
        "random_hit_credit": RANDOM_HIT_CREDIT,
        "abundant_target_credit": abundant_credit,
        "no_target_credit": no_target_credit,
        "parent_target_tags": parent_tags,
        "emitter_target_tags": _raw_target_tags(warhead),
        "fragment_target_tags": fragment_tags,
        "target_mask_status": mask_status,
        "file": warhead.file,
        "line": warhead.line,
    }


def _direct_bindings(rs):
    bindings = defaultdict(list)
    for actor_name in rs.actors:
        if actor_name.startswith("^"):
            continue
        actor = rs.resolve(actor_name)
        if actor is None:
            continue
        for trait in actor.children:
            if trait.key.split("@", 1)[0] != "Armament":
                continue
            weapon_name = trait.get("Weapon")
            if weapon_name:
                resolved = rs.weapon(weapon_name)
                if resolved is not None:
                    bindings[resolved.key].append({
                        "actor": actor_name,
                        "armament": trait.key,
                        "requires_condition": trait.get("RequiresCondition"),
                    })
    return bindings


def _chains(rs, weapon_name, *, _path=(), _seen=None):
    """Return all reachable FireShrapnel edges with explicit paths."""
    seen = set(_seen or ())
    node = rs.resolve_weapon(weapon_name)
    if node is None or weapon_name.lower() in seen:
        return []
    seen.add(weapon_name.lower())
    records = []
    for child in node.children:
        if child.key.split("@", 1)[0] != "Warhead" or child.value != "FireShrapnel":
            continue
        fragment_name = child.get("Weapon")
        fragment = rs.resolve_weapon(fragment_name) if fragment_name else None
        edge = _edge_record(weapon_name, node, child, fragment,
                            "/".join((*_path, child.key)))
        records.append(edge)
        if fragment_name and fragment is not None:
            records.extend(_chains(rs, fragment_name, _path=(*_path, fragment_name), _seen=seen))
    return records


def _scenario_totals(rs, weapon_name):
    """Run only the flat-authored projection for abundant and isolated targets."""
    def flat_damage(node):
        return direct_payload(node)["flat_damage"]

    def all_targets(_node, _warhead):
        return None

    def no_targets(_node, _warhead):
        return 0

    out = {}
    for label, eligible in (("abundant_targets", all_targets),
                            ("no_eligible_targets", no_targets)):
        try:
            result = shrapnel_damage.damage_tree(
                weapon_name,
                rs.resolve_weapon,
                flat_damage,
                random_hit_credit=RANDOM_HIT_CREDIT,
                eligible_targets=eligible,
            )
            out[label] = {
                "status": "SCENARIO_ONLY",
                "direct_flat_damage": result["direct"],
                "shrapnel_flat_damage": result["shrapnel"],
                "total_flat_projection": result["total"],
            }
        except (TypeError, ValueError) as error:
            out[label] = {"status": "UNRESOLVED", "reason": str(error)}
    return out


def _source_metadata(rs):
    manifest = getattr(rs, "manifest", None)
    if manifest is None:
        return {"generated_from": None, "source_file_count": 0, "source_sha256": {}}
    hashes = {}
    repo = pathlib.Path(rs.repo_root).resolve()
    for path in list(manifest.rules) + list(manifest.weapons):
        path = pathlib.Path(path).resolve()
        try:
            key = path.relative_to(repo).as_posix()
        except ValueError:
            key = path.as_posix()
        hashes[key] = _sha256(path)
    return {
        "generated_from": repo.as_posix(),
        "source_file_count": len(hashes),
        "source_sha256": dict(sorted(hashes.items())),
    }


def build_report(rs):
    bindings = _direct_bindings(rs)
    weapon_rows = []
    edges = []
    for name in sorted(rs.weapons):
        if name.startswith("^"):
            continue
        node = rs.resolve_weapon(name)
        if node is None:
            continue
        fire_edges = _chains(rs, name)
        if not fire_edges:
            continue
        payload = direct_payload(node)
        scenario = _scenario_totals(rs, name)
        row = {
            "weapon": name,
            "bindings": bindings.get(name, []),
            "binding_count": len(bindings.get(name, [])),
            "file": node.file,
            "line": node.line,
            "direct_payload": payload,
            "scenarios": scenario,
            "edge_count": len(fire_edges),
            "max_chain_depth": max(
                (item["path"].count("/") + 1 for item in fire_edges),
                default=0,
            ),
            "edges": fire_edges,
        }
        weapon_rows.append(row)
        edges.extend(fire_edges)
    mask_counts = Counter(edge["target_mask_status"] for edge in edges)
    payload_counts = Counter(row["direct_payload"]["status"] for row in weapon_rows)
    depth_counts = Counter(row["max_chain_depth"] for row in weapon_rows)
    bound_rows = [row for row in weapon_rows if row["binding_count"]]
    return {
        "schema": 1,
        "status": "SCENARIO_ONLY",
        "scope": "Resolved active FireShrapnel weapon definitions and direct armament bindings.",
        "policy": {
            "random_hit_credit": RANDOM_HIT_CREDIT,
            "abundant_targets": "unlimited eligible targets supplied to the diagnostic helper",
            "no_eligible_targets": "zero eligible actors; ThrowWithoutTarget is honored",
            "burst_and_reload": "not multiplied for child emissions; child Burst/ReloadDelay are not an emitter firing cycle",
            "writeback": False,
        },
        "metadata": {
            "tool": "tools/balance/shrapnel_scenario_report.py",
            "tool_sha256": _sha256(pathlib.Path(__file__).resolve()),
            **_source_metadata(rs),
        },
        "summary": {
            "fire_shrapnel_weapons": len(weapon_rows),
            "bound_fire_shrapnel_weapons": len(bound_rows),
            "bound_actor_bindings": sum(row["binding_count"] for row in weapon_rows),
            "fire_shrapnel_edges": len(edges),
            "target_mask_status": dict(sorted(mask_counts.items())),
            "direct_payload_status": dict(sorted(payload_counts.items())),
            "max_chain_depth": max((row["max_chain_depth"] for row in weapon_rows), default=0),
            "chain_depth_counts": dict(sorted((str(k), v) for k, v in depth_counts.items())),
            "percentage_limited_weapons": sum(
                row["direct_payload"]["status"] != "FLAT_ONLY" for row in weapon_rows
            ),
        },
        "weapons": weapon_rows,
        "limits": [
            "The flat projection omits target-HP percentage components, armor, falloff, footprint geometry and status effects.",
            "AimChance and random-hit credit are explicit scenario conventions; they are not measured hit probabilities.",
            "A no-target random throw still needs a valid impact position and is not proof of damage in a live match.",
            "Target masks are preserved with a domain comparison; custom tags require human/runtime review.",
            "Actor bindings do not prove that a route fires in every state, that descendants have eligible victims, or that a source vote is valid.",
            "No balance formula, price, DPS vote, YAML, runtime or Versus value is changed.",
        ],
    }


def render_markdown(report):
    summary = report["summary"]
    policy = report["policy"]
    lines = [
        "# FireShrapnel scenario receipt",
        "",
        "**SCENARIO ONLY.** This receipt exposes recursive child emissions and "
        "explicit target-availability assumptions. It is not a price, DPS vote, "
        "armor result or gameplay recommendation.",
        "",
        "## Coverage",
        "",
        f"- FireShrapnel weapons: **{summary['fire_shrapnel_weapons']}**; bound weapon definitions: **{summary['bound_fire_shrapnel_weapons']}**; actor bindings: **{summary['bound_actor_bindings']}**.",
        f"- Reachable FireShrapnel edges: **{summary['fire_shrapnel_edges']}**; maximum observed chain depth: **{summary['max_chain_depth']}**.",
        f"- Target-mask statuses: `{summary['target_mask_status']}`.",
        f"- Direct payload statuses: `{summary['direct_payload_status']}`; percentage-limited roots: **{summary['percentage_limited_weapons']}**.",
        "",
        "## Scenarios",
        "",
        f"- Random-hit credit: **{policy['random_hit_credit']:.2f}** for an untargeted attempt.",
        "- `abundant_targets`: unlimited eligible targets; aimed and fallback emissions are credited by the helper.",
        "- `no_eligible_targets`: zero eligible actors; `ThrowWithoutTarget:false` contributes no child emission, while the default true remains a random-position scenario.",
        "- Child `Burst` and `ReloadDelay` are not multiplied into an emission; the parent firing cycle remains outside this receipt.",
        "",
        "## Review boundaries",
        "",
        "- Parent, emitter and fragment masks, raw tokens and source locations are retained in the JSON.",
        "- Flat damage is shown separately from percentage/folded channels; target HP, armor, falloff, geometry and status effects remain unresolved.",
        "- No row authorizes repricing, YAML edits, Versus changes, runtime claims or publication.",
        "",
        "Full per-weapon and per-edge evidence is in the paired JSON receipt.",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--markdown", type=pathlib.Path, required=True)
    args = parser.parse_args(argv)
    try:
        out = diagnostic_output.validate_path(ROOT, args.out)
        markdown = diagnostic_output.validate_path(ROOT, args.markdown)
        if out == markdown:
            raise ValueError("JSON and Markdown outputs must differ")
        report = build_report(Ruleset(ROOT))
        diagnostic_output.write_outputs(ROOT, {
            out: json.dumps(report, indent=2, sort_keys=True) + "\n",
            markdown: render_markdown(report),
        })
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
