#!/usr/bin/env python3
"""Apply an increment's behaviour switches to a FROZEN A/B worktree (AI_MASTER_PLAN §1.2 step 6, amended 2026-10-01).

    python tools/ai/apply_increment_switches.py <worktree> --groups A_squad_tactics,B_ownership_engineers_missions
    python tools/ai/apply_increment_switches.py <worktree> --groups all --dry-run

Reads tools/ai/increment_switches.yaml from THIS repo and edits <worktree>/mods/cameo/ai/*.yaml in place: under every
instance of each named trait (`Trait:` or `Trait@name:`, except the `skip` list) it sets each field — replacing an
existing line of that field or inserting one right under the trait header. Prints every change; refuses to run on
the main checkout. Never commit the result: master keeps the defaults until the increment's A/B decides.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
SPEC = REPO / "tools" / "ai" / "increment_switches.yaml"


def load_spec(path: pathlib.Path) -> tuple[list[str], dict[str, dict[str, dict[str, str]]]]:
    """A tiny reader for this file's fixed shape (skip list + groups → trait → field: value); comments ignored."""
    skip: list[str] = []
    groups: dict[str, dict[str, dict[str, str]]] = {}
    group = trait = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, _, value = line.strip().partition(":")
        value = value.strip()
        if indent == 0 and key == "skip":
            skip = [s.strip() for s in value.strip("[]").split(",") if s.strip()]
        elif indent == 2:
            group = key
            groups[group] = {}
        elif indent == 4 and group:
            trait = key
            groups[group][trait] = {}
        elif indent == 6 and group and trait:
            groups[group][trait][key] = value
    return skip, groups


def apply(text: str, trait: str, fields: dict[str, str], skip: list[str]) -> tuple[str, list[str]]:
    """Set `fields` under every instance header of `trait` (tab-indented MiniYaml)."""
    lines = text.split("\n")
    changes: list[str] = []
    header = re.compile(rf"^\t({re.escape(trait)}(@[A-Za-z0-9_]+)?):\s*$")
    i = 0
    while i < len(lines):
        m = header.match(lines[i].rstrip("\r"))
        if not m or m.group(1) in skip:
            i += 1
            continue
        start = i + 1
        end = start
        while end < len(lines) and (lines[end].startswith("\t\t") or not lines[end].strip()):
            end += 1
        eol = "\r" if lines[i].endswith("\r") else ""
        for field, value in fields.items():
            hit = next((j for j in range(start, end) if re.match(rf"^\t\t{re.escape(field)}:", lines[j])), None)
            new = f"\t\t{field}: {value}{eol}"
            if hit is not None:
                if lines[hit] != new:
                    changes.append(f"{m.group(1)}.{field}: {lines[hit].strip()} -> {value}")
                    lines[hit] = new
            else:
                lines.insert(start, new)
                end += 1
                changes.append(f"{m.group(1)}.{field}: (default) -> {value}")
        i = end
    return "\n".join(lines), changes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("worktree", type=pathlib.Path)
    ap.add_argument("--groups", required=True, help="comma-separated group names, or 'all'")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--spec", type=pathlib.Path, default=SPEC,
                    help="switch spec to read (default: tools/ai/increment_switches.yaml); tune_build_order.py --propose writes experiment specs")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    tree = args.worktree.resolve()
    if (tree / ".git").is_dir():  # the main checkout has a .git DIRECTORY; worktrees have a .git file
        print("refusing: apply switches only to a frozen A/B worktree, never the main checkout", file=sys.stderr)
        return 2

    skip, groups = load_spec(args.spec)
    names = list(groups) if args.groups == "all" else args.groups.split(",")
    unknown = [n for n in names if n not in groups]
    if unknown:
        print(f"unknown group(s): {unknown}; known: {list(groups)}", file=sys.stderr)
        return 2

    wanted: dict[str, dict[str, str]] = {}
    for n in names:
        for trait, fields in groups[n].items():
            wanted.setdefault(trait, {}).update(fields)

    total = 0
    seen: set[str] = set()
    for f in sorted((tree / "mods" / "cameo" / "ai").glob("*.yaml")):
        text = f.read_text(encoding="utf-8")
        new = text
        for trait, fields in wanted.items():
            new, changes = apply(new, trait, fields, skip)
            for c in changes:
                print(f"{f.name}: {c}")
            total += len(changes)
            if changes:
                seen.add(trait)
        if new != text and not args.dry_run:
            f.write_text(new, encoding="utf-8", newline="")

    missing = sorted(set(wanted) - seen)
    if missing:
        print(f"WARNING: no instance changed for {missing} (already set, or trait not in ai yaml)")
    print(f"{total} change(s){' (dry run)' if args.dry_run else ''} for groups {names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
