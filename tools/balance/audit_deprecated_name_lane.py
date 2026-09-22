#!/usr/bin/env python3
"""Read-only R10-R15 audit for Codex's ContentPacks lane.

The report measures what can be acted on without guessing a family or changing a warhead:

* R10/R12: compatibility-template users in the four assigned ContentPacks;
* R11: `Warhead@1Dam` nodes that are the sole resolved positive damage main and already have
  exactly one inherited `^Warhead_*` family candidate;
* R13: compatibility templates with no matching generated family in the current tree;
* R14: the imported `*Dam_areanuke*` / `Damage` cohort, with its resolved geometry and timing
  fields for human review.

It never edits YAML, deletes templates, chooses a family, or folds damage.  The output is a
measured handoff for the lane split in PR #354.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))

from audit_three_way_split import main_warheads  # noqa: E402
from miniyaml import Ruleset  # noqa: E402


OWNED_FILES = (
    "mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml",
    "mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml",
    "mods/cameo/ContentPacks/D2k/Atreides/yaml/weapons.yaml",
    "mods/cameo/ContentPacks/D2k/Shared/yaml/weapons.yaml",
)
COMPAT = "^Compatibility_"
WARHEAD_TEMPLATE = re.compile(r"^\^Warhead_[A-Za-z0-9]+_[A-Za-z0-9]+$")
NUKE_RING_KEYS = {
    "4Dam_areanuke1", "7Dam_areanuke2", "8Dam_areanuke2",
    "10Dam_areanuke3", "11Dam_areanuke3",
}
NUKE_COMPANION_KEYS = NUKE_RING_KEYS | {"1Dam_impact", "Damage"}


def norm(path: str) -> str:
    p = pathlib.Path(path)
    if p.is_absolute():
        try:
            p = p.resolve().relative_to(ROOT.resolve())
        except ValueError:
            pass
    return p.as_posix()


def inherits(node) -> list[str]:
    return [str(c.value).strip() for c in node.children
            if c.key.split("@")[0] == "Inherits" and c.value]


def inherited_templates(rs: Ruleset, name: str, seen: set[str] | None = None) -> set[str]:
    seen = set() if seen is None else seen
    if name in seen:
        return set()
    seen.add(name)
    node = rs.weapons.get(name)
    if node is None:
        return set()
    out: set[str] = set()
    for parent in inherits(node):
        if WARHEAD_TEMPLATE.match(parent):
            out.add(parent)
        out |= inherited_templates(rs, parent, seen)
    return out


def local_owned_weapons(rs: Ruleset):
    owned = set(OWNED_FILES)
    for name, node in rs.weapons.items():
        if name.startswith("^") or norm(node.file) not in owned:
            continue
        yield name, node


def compatibility_lane(rs: Ruleset):
    rows = []
    for name, node in local_owned_weapons(rs):
        direct = inherits(node)
        nodes = [c.key for c in node.children if "Compatibility" in c.key]
        parents = [p for p in direct if p.startswith(COMPAT)]
        if not nodes and not parents:
            continue
        rows.append({"weapon": name, "file": norm(node.file), "parents": parents,
                     "local_nodes": nodes, "line": node.line})
    return rows


def one_dam_lane(rs: Ruleset):
    rows = []
    for name, node in local_owned_weapons(rs):
        if not any(c.key == "Warhead@1Dam" for c in node.children):
            continue
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            rows.append({"weapon": name, "file": norm(node.file), "status": "unresolved",
                         "line": node.line})
            continue
        mains = main_warheads(resolved)
        if mains != ["1Dam"]:
            rows.append({"weapon": name, "file": norm(node.file), "status": "not_sole_main",
                         "mains": mains, "line": node.line})
            continue
        candidates = sorted(inherited_templates(rs, name))
        status = "rename_candidate" if len(candidates) == 1 else (
            "no_family_candidate" if not candidates else "ambiguous_family")
        rows.append({"weapon": name, "file": norm(node.file), "status": status,
                     "family_candidates": candidates, "mains": mains, "line": node.line})
    return rows


def compatibility_templates(rs: Ruleset):
    users = direct_template_users(rs)
    out = []
    for name, node in sorted(rs.weapons.items()):
        if not name.startswith(COMPAT):
            continue
        rest = name[len(COMPAT):]
        candidates = [f"^Warhead_{rest}"]
        for suffix in ("Flat", "ExtraDamage", "GroundSlice", "Composition"):
            if rest.endswith(suffix):
                candidates.insert(0, f"^Warhead_{rest[:-len(suffix)].rstrip('_')}")
        if rest.endswith("FlatCompatibility"):
            candidates.insert(0, f"^Warhead_{rest[:-len('FlatCompatibility')].rstrip('_')}_Flat")
        twin = next((c for c in candidates if c in rs.weapons), None)
        out.append({"template": name, "file": norm(node.file), "line": node.line,
                    "users": users.get(name, []), "owned_users": [u for u in users.get(name, [])
                    if u["file"] in OWNED_FILES], "matching_family": twin})
    return out


def direct_template_users(rs: Ruleset):
    """Return direct `Inherits: ^Compatibility_*` users, excluding inherited closure."""
    users = {}
    for name, node in rs.weapons.items():
        if name.startswith("^"):
            continue
        for parent in inherits(node):
            if parent.startswith(COMPAT):
                users.setdefault(parent, []).append({"weapon": name, "file": norm(node.file)})
    return users


def has_nuclear_ring(resolved) -> bool:
    keys = {c.key[len("Warhead@"):]
            for c in resolved.children if c.key.startswith("Warhead@")}
    return bool(keys & NUKE_RING_KEYS)


def payload_row(name: str, node, resolved, child) -> dict:
    projectile = resolved.child("Projectile")
    return {"weapon": name, "file": norm(node.file), "warhead": child.key,
            "type": child.value, "damage": child.get("Damage"),
            "spread": child.get("Spread"), "falloff": child.get("Falloff"),
            "valid_targets": child.get("ValidTargets"),
            "valid_relationships": child.get("ValidRelationships"),
            "delay": child.get("Delay"),
            "reload_delay": resolved.get("ReloadDelay"),
            "burst": resolved.get("Burst"),
            "burst_delays": resolved.get("BurstDelays"),
            "projectile": projectile.value if projectile is not None else None,
            "payload_order": [c.key for c in resolved.children
                              if c.key.startswith("Warhead@")],
            "line": child.line}


def nuke_cohort(rs: Ruleset):
    rows = []
    for name, node in sorted(rs.weapons.items()):
        if name.startswith("^"):
            continue
        resolved = rs.resolve_weapon(name)
        if resolved is None:
            continue
        # Generic `Damage` / `1Dam_impact` nodes are only R14 companions when the same weapon
        # also carries at least one of the imported expanding-ring keys.  Chrono/EMP/veins/
        # spell effects that merely happen to use a legacy name stay out of this cohort.
        if not has_nuclear_ring(resolved):
            continue
        for child in resolved.children:
            if (not child.key.startswith("Warhead@") or
                    child.key[len("Warhead@"):] not in NUKE_COMPANION_KEYS):
                continue
            rows.append(payload_row(name, node, resolved, child))
    return rows


def build_report(rs: Ruleset) -> dict:
    compat = compatibility_lane(rs)
    one_dam = one_dam_lane(rs)
    templates = compatibility_templates(rs)
    nuke = nuke_cohort(rs)
    return {
        "schema": 1,
        "scope": "PR #354 Codex ContentPacks lane; read-only R10-R15 audit",
        "owned_files": list(OWNED_FILES),
        "counts": {
            "compatibility_lane_weapons": len(compat),
            "one_dam_rows": len(one_dam),
            "r11_rename_candidates": sum(r["status"] == "rename_candidate" for r in one_dam),
            "compatibility_templates": len(templates),
            "compatibility_templates_with_owned_users": sum(bool(t["owned_users"]) for t in templates),
            "compatibility_orphans": sum(t["matching_family"] is None for t in templates),
            "nuke_geometry_rows": len(nuke),
        },
        "compatibility_lane": compat,
        "r11_one_dam": one_dam,
        "compatibility_templates": templates,
        "r14_nuke_cohort": nuke,
    }


def markdown(report: dict) -> str:
    c = report["counts"]
    lines = [
        "# R10-R15 ContentPacks lane audit",
        "",
        "**Read-only measurement.** This report does not rename, fold, delete, generate, or alter YAML.",
        "It measures the four files assigned to Codex in PR #354 and inventories the self-contained R14 cohort.",
        "The R10/R11 counts are local-definition inventories, not complete inherited consumer closures; "
        "the R12/R13 user count is direct owned users; matching-family counts are name-based screens, not semantic equivalence proofs.",
        "",
        "## Counts",
        "",
        "| measure | count |",
        "|---|---:|",
        f"| local compatibility-bearing definitions in owned files (R10/R12) | {c['compatibility_lane_weapons']} |",
        f"| local `Warhead@1Dam` definitions in owned files | {c['one_dam_rows']} |",
        f"| R11 candidates with exactly one inherited `^Warhead_*` family | {c['r11_rename_candidates']} |",
        f"| `^Compatibility_*` templates in the ruleset | {c['compatibility_templates']} |",
        f"| templates with at least one direct owned user | {c['compatibility_templates_with_owned_users']} |",
        f"| compatibility templates with no matching family | {c['compatibility_orphans']} |",
        f"| R14 resolved nuclear-ring payload rows | {c['nuke_geometry_rows']} |",
        "",
        "R11 is a conservative local-definition screen only: a candidate needs a sole resolved positive damage main and exactly one inherited `^Warhead_*` family. It does not prove that the complete inherited consumer closure has no other issue. `no_family_candidate`, `ambiguous_family`, and `not_sole_main` remain review holds.",
        "The existing `promote_compatibility_warheads.py --base <pristine 415071925 worktree>` dry run on this snapshot routes **0/36** remaining compatibility templates automatically; all 36 are mixed and skipped. That is measured evidence for keeping R12 per-user closure decisions separate from the R10 pure-rename lane.",
        "",
        "## R11 rows",
        "",
        "| status | weapon | file | family candidates | mains |",
        "|---|---|---|---|---|",
    ]
    for row in report["r11_one_dam"]:
        lines.append(f"| `{row['status']}` | `{row['weapon']}` | `{row['file']}` | "
                     f"{', '.join(row.get('family_candidates', [])) or '—'} | "
                     f"{', '.join(row.get('mains', [])) or '—'} |")
    lines += ["", "## R10/R12 owned compatibility users", "",
              "| weapon | file | compatibility parents | local compatibility nodes |",
              "|---|---|---|---|"]
    for row in report["compatibility_lane"]:
        lines.append(f"| `{row['weapon']}` | `{row['file']}` | "
                     f"{', '.join(row['parents']) or '—'} | "
                     f"{', '.join(row['local_nodes']) or '—'} |")
    lines += ["", "## R14 geometry inventory", "",
        "This is evidence for review only; matching geometry does not authorize conversion. The cohort is selected by the presence of an expanding-ring key; generic legacy names outside that cohort are excluded.",
        "", "| weapon | file | warhead | type | Damage | Spread | Falloff | ValidTargets | Delay | ReloadDelay | Burst | BurstDelays | Projectile | ordered payloads |",
              "|---|---|---|---|---:|---|---|---|---|---|---:|---|---|---|"]
    for row in report["r14_nuke_cohort"]:
        lines.append(f"| `{row['weapon']}` | `{row['file']}` | `{row['warhead']}` | `{row['type']}` | "
                     f"{row.get('damage') or '—'} | {row.get('spread') or '—'} | "
                     f"{row.get('falloff') or '—'} | {row.get('valid_targets') or '—'} | "
                     f"{row.get('delay') or '—'} | {row.get('reload_delay') or '—'} | "
                     f"{row.get('burst') or '—'} | {row.get('burst_delays') or '—'} | "
                     f"{row.get('projectile') or '—'} | {' → '.join(row.get('payload_order') or [])} |")
    lines += ["", "Absent timing fields are reported as unspecified; engine defaults are not inferred. R12/R13 template deletion/generation remains separate: the template closure and per-weapon suppression lines must be measured on the complete ruleset before any write.", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", type=pathlib.Path)
    parser.add_argument("--markdown", type=pathlib.Path)
    args = parser.parse_args(argv)
    report = build_report(Ruleset(str(ROOT)))
    if args.json:
        (ROOT / args.json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown:
        (ROOT / args.markdown).write_text(markdown(report), encoding="utf-8")
    if not args.json and not args.markdown:
        print(markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
