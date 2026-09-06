#!/usr/bin/env python3
"""Consolidate a reviewed naval-artillery and grenade tranche.

The selected roots have one unambiguous delivery role.  The conversion keeps
their resolved flat total, target route, percentage arithmetic, and all
non-damage behavior while selecting one canonical armor/blast profile.
"""
from __future__ import annotations

import argparse
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
sys.path.insert(0, str(ROOT / "tools" / "balance"))

from audit_three_way_split import main_warheads  # noqa: E402
from consolidate_final_safe_cohorts import (  # noqa: E402
    cleanup_duplicate_template_inherits,
    cleanup_stale_removals,
    ensure_template_inherit,
    flat_main_nodes,
    percentage_scale,
    set_scale,
)
from consolidate_reviewed_weapon_roots import (  # noqa: E402
    add_compatibility_templates,
    apply_compatibility_block,
    block_bounds,
)
from consolidate_rule_driven_energy_ordnance import (  # noqa: E402
    add_percentage_companions,
    digest,
    remove_batch_parent_percentage_companions,
)
from miniyaml import Ruleset  # noqa: E402
import percentage_damage as pd  # noqa: E402


GROUPS = {
    "Demolition_Heavy": {
        "8Inch",
    },
    "Concussion_Medium": {"TSGrenade"},
}
SELECTED = {
    name: destination
    for destination, names in GROUPS.items()
    for name in names
}
EXPECTED_COUNT = 2
BASELINE_DIGEST = "db8f9d608b88e9c692576e290b243e97dd1ff7c4745a23cf5b5d8da913c800ce"

# root: (abstract legacy name, direct children that retain the old payload)
ISOLATIONS = {}


def baseline_rows(rs: Ruleset):
    rows = {}
    for name, destination in sorted(SELECTED.items()):
        resolved = rs.resolve_weapon(name)
        mains = set(main_warheads(resolved))
        compatibility = f"{destination}FlatCompatibility"
        if mains == {compatibility}:
            rows[name] = None
            continue
        if len(mains) < 2 or destination not in mains:
            raise RuntimeError(
                f"{name}: expected stacked {destination}; found {sorted(mains)}")
        nodes = flat_main_nodes(resolved, mains)
        if set(nodes) != mains:
            raise RuntimeError(f"{name}: selected main is not flat damage")
        total = sum(int(str(node.get("Damage") or 0)) for node in nodes.values())
        targets = str(nodes[destination].get("ValidTargets") or "").strip()
        if total <= 0 or not targets or targets == "*":
            raise RuntimeError(f"{name}: invalid total or target route")
        try:
            folded_scale = percentage_scale(resolved, mains, total)
            standalone = {}
        except RuntimeError:
            folded_scale = 0
            standalone = {
                key: {
                    "units": pd.folded_units(
                        int(str(node.get("Damage") or 0)),
                        int(str(node.get("PercentageScale") or 0)),
                    )[1],
                    "denominator": int(str(
                        node.get("PercentageDenominator")
                        or pd.FOLDED_DEFAULT_DENOMINATOR)),
                }
                for key, node in sorted(nodes.items())
                if int(str(node.get("PercentageScale") or 0)) != 0
            }
        rows[name] = {
            "destination": destination,
            "mains": sorted(mains),
            "total": total,
            "targets": targets,
            "percentage_scale": folded_scale,
            "percentage": standalone,
        }
    return rows


def isolate_legacy_root(changed, rs: Ruleset, root: str,
                        legacy: str, children: set[str]) -> None:
    local = rs.weapon(root)
    path = pathlib.Path(local.file)
    lines = changed.setdefault(
        path, path.read_text(encoding="utf-8-sig").splitlines(True))
    start, end = block_bounds(lines, root)
    lines[start] = f"{legacy}:\n"
    lines[end:end] = [f"{root}:\n", f"\tInherits: {legacy}\n"]
    for child in sorted(children):
        child_local = rs.weapon(child)
        child_path = pathlib.Path(child_local.file)
        child_lines = changed.setdefault(
            child_path,
            child_path.read_text(encoding="utf-8-sig").splitlines(True))
        start, end = block_bounds(child_lines, child)
        matches = [
            i for i in range(start + 1, end)
            if child_lines[i].strip().endswith(f": {root}")
        ]
        if len(matches) != 1:
            raise RuntimeError(f"{child}: inheritance fingerprint changed")
        prefix = child_lines[matches[0]].split(":", 1)[0]
        child_lines[matches[0]] = f"{prefix}: {legacy}\n"


def apply_changes(rs: Ruleset, rows) -> None:
    changed: dict[pathlib.Path, list[str]] = {}
    for root, (legacy, children) in ISOLATIONS.items():
        isolate_legacy_root(changed, rs, root, legacy, children)
    add_compatibility_templates(changed, rs, set(SELECTED.values()))
    for name in sorted(SELECTED):
        plan = rows[name]
        destination = plan["destination"]
        local = rs.weapon(name)
        path = pathlib.Path(local.file)
        resolved = rs.resolve_weapon(name)
        remove_batch_parent_percentage_companions(
            changed, path, name, rs, rows)
        add_percentage_companions(changed, path, name, resolved, plan)
        ensure_template_inherit(changed, path, name, destination)
        apply_compatibility_block(
            changed, path, name, destination, set(plan["mains"]),
            plan["total"], plan["targets"], inherit_template=False)
        set_scale(changed, path, name, destination, plan["percentage_scale"])
    for path, lines in changed.items():
        path.write_text("".join(lines), encoding="utf-8", newline="\n")
    cleanup_stale_removals(set(SELECTED))
    cleanup_duplicate_template_inherits(set(SELECTED))


def validate_result() -> None:
    rs = Ruleset(ROOT)
    for name, destination in sorted(SELECTED.items()):
        mains = set(main_warheads(rs.resolve_weapon(name)))
        expected = {f"{destination}FlatCompatibility"}
        if mains != expected:
            raise RuntimeError(
                f"{name}: expected {sorted(expected)}; found {sorted(mains)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if len(SELECTED) != EXPECTED_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_COUNT} selections, found {len(SELECTED)}")
    rs = Ruleset(ROOT)
    rows = baseline_rows(rs)
    states = {row is None for row in rows.values()}
    if states == {True}:
        validate_result()
        print(f"Already consolidated {len(SELECTED)} definitions")
        return 0
    if len(states) != 1:
        raise RuntimeError("partial heavy-explosive tranche detected")
    current_digest = digest(rows)
    print(f"{len(SELECTED)} definitions; baseline digest {current_digest}")
    if BASELINE_DIGEST and current_digest != BASELINE_DIGEST:
        raise RuntimeError("baseline fingerprint changed")
    if not args.apply:
        print("Dry run: totals, routes, and percentage arithmetic pass")
        return 0
    if not BASELINE_DIGEST:
        raise RuntimeError("pin BASELINE_DIGEST before applying")
    apply_changes(rs, rows)
    validate_result()
    print(f"Applied and validated {len(SELECTED)} definitions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
