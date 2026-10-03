#!/usr/bin/env python3
"""Move one ContentPack's AI dictionary rows out of mods/cameo/ai/ai.yaml into the pack's ai.yaml.

Why: the end goal is dynamic faction loading (docs/MIGRATION.md), so a faction's AI must ship
inside its pack. A pack can ADD rows to a dictionary field that the central file declares: the
rows union (AI_ARCHITECTURE.md §1.2, case 1). A row the central file keeps always wins, so the
move is subtractive on the central file.

What moves: every row, with its subtree, under `Player: > <Trait@instance>: > <Field>:` in the
central file whose KEY is an actor DEFINED in the pack's own yaml. Lists (comma-separated values)
never move: packs cannot append to a list (AI_ARCHITECTURE.md §2.8).

Gate after --apply (the tool prints the commands):
  utility.cmd cameo --resolved-rules Player   before and after, compared as CONTENT with
  tools/packs/compare_resolved.py (dictionary order changes by design, §1.2 ordering caveat).

Usage:
  python tools/packs/split_ai_rows.py --pack TiberianDawn/GDI            # dry run: what would move
  python tools/packs/split_ai_rows.py --pack TiberianDawn/GDI --apply
  python tools/packs/split_ai_rows.py --all                              # dry-run census of every pack
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "audit"))
import miniyaml  # noqa: E402

PACKS = REPO / "mods" / "cameo" / "ContentPacks"
CENTRAL = REPO / "mods" / "cameo" / "ai" / "ai.yaml"

# Dictionary fields whose row keys are NOT actor ids, even when one happens to equal an actor name.
NOT_ACTOR_KEYED = {"Decisions"}

HEADER = """# AI configuration owned by this ContentPack ({pack}).
#
# Why this file exists: a faction's AI must ship inside its own pack, so that a game which does
# not load this faction carries no AI rows naming its actors (docs/MIGRATION.md, "Why
# ContentPacks"). Rows here are MERGED into the bot modules that mods/cameo/ai/ai.yaml declares:
# a pack can ADD dictionary rows (they union), but it can never override or remove a key the
# central file sets (docs/design/AI_ARCHITECTURE.md §1.2). Lists of actor ids cannot be
# appended from a pack and stay central until §2.8 lands.
#
# Moved from the central file by tools/packs/split_ai_rows.py. Edit rows HERE, never there.
"""


def pack_dirs():
    return sorted(p.parent for p in PACKS.rglob("content.yaml"))


def pack_actors() -> dict[str, str]:
    """actor -> pack (relative dir). Only real actors (no ^templates), defined in exactly one pack."""
    owner: dict[str, set[str]] = collections.defaultdict(set)
    for d in pack_dirs():
        rel = d.relative_to(PACKS).as_posix()
        for y in (d / "yaml").glob("*.yaml") if (d / "yaml").is_dir() else []:
            if y.name in ("ai.yaml", "weapons.yaml", "sequences.yaml"):
                continue
            try:
                nodes = miniyaml.load(y)
            except Exception:
                continue
            for n in nodes:
                k = n.key.lstrip("-")
                if k and not k.startswith("^") and k not in ("Player", "World", "EditorWorld"):
                    owner[k].add(rel)
    return {a: next(iter(p)) for a, p in owner.items() if len(p) == 1}


def depth(line: str) -> int:
    return len(line) - len(line.lstrip("\t"))


def plan(pack: str, owners: dict[str, str]):
    """Return (moves, keep_lines). moves: list of (trait, field, [lines]) in file order."""
    raw = CENTRAL.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.split(nl)
    keep, moves = [], []
    top = trait = field = None
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s or s.startswith("#"):
            keep.append(line)
            i += 1
            continue
        d = depth(line)
        key = s.split(":", 1)[0]
        if d == 0:
            top, trait, field = key, None, None
        elif d == 1:
            trait, field = key, None
        elif d == 2:
            field = key
        elif d == 3 and top == "Player" and trait and field and field not in NOT_ACTOR_KEYED and owners.get(key) == pack:
            # the row plus its subtree: following non-blank lines indented deeper than the row
            block = [line]
            j = i + 1
            while j < len(lines) and lines[j].strip() and depth(lines[j]) > 3:
                block.append(lines[j])
                j += 1
            moves.append((trait, field, block))
            i = j
            continue
        keep.append(line)
        i += 1
    return moves, keep, nl


def ensure_included(pack: str) -> None:
    """A pack ai.yaml that content.yaml does not list is never loaded: its rows would vanish.
    Append it as the last Rules entry (13 packs had no ai.yaml at all, 2026-09-27)."""
    cy = PACKS / pack / "content.yaml"
    raw = cy.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    entry = f"\tContentPacks|{pack}/yaml/ai.yaml"
    lines = raw.split(nl)
    if any(l.strip() == entry.strip() for l in lines):
        return
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == "Rules:" and not l.startswith("\t"))
    except StopIteration:
        raise SystemExit(f"{cy}: no top-level Rules: block; add the include by hand")
    end = start + 1
    while end < len(lines) and lines[end].startswith("\t"):
        end += 1
    lines.insert(end, entry)
    cy.write_bytes(nl.join(lines).encode("utf-8"))
    print(f"added {entry.strip()} to {cy.relative_to(REPO)}")


def render_pack(pack: str, moves, nl: str) -> str:
    out = HEADER.format(pack=pack).split("\n")
    out.append("Player:")
    grouped: dict[str, dict[str, list[str]]] = collections.OrderedDict()
    for trait, field, block in moves:
        grouped.setdefault(trait, collections.OrderedDict()).setdefault(field, []).extend(block)
    for trait, fields in grouped.items():
        out.append(f"\t{trait}:")
        for field, rows in fields.items():
            out.append(f"\t\t{field}:")
            out.extend(rows)
    return nl.join(out) + nl


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pack")
    g.add_argument("--all", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    owners = pack_actors()
    if a.all:
        total = 0
        for d in pack_dirs():
            rel = d.relative_to(PACKS).as_posix()
            moves, _, _ = plan(rel, owners)
            if moves:
                per = collections.Counter(f for _, f, _ in moves)
                total += len(moves)
                print(f"{len(moves):5} rows  {rel:40} {dict(per.most_common(4))}")
        print(f"{total:5} rows movable in total")
        return 0

    pack = a.pack.strip("/")
    if not (PACKS / pack / "content.yaml").is_file():
        print(f"no ContentPack at {PACKS / pack}")
        return 2
    moves, keep, nl = plan(pack, owners)
    per = collections.Counter(f"{t} > {f}" for t, f, _ in moves)
    print(f"{pack}: {len(moves)} rows would move")
    for k, n in per.most_common():
        print(f"  {n:4}  {k}")
    if not a.apply or not moves:
        return 0

    target = PACKS / pack / "yaml" / "ai.yaml"
    old = target.read_bytes().decode("utf-8") if target.is_file() else ""
    live = [l for l in old.splitlines() if l.strip() and not l.strip().startswith("#")]
    if live and live != ["Player:"]:
        print(f"{target} already holds live config; refusing to overwrite (merge by hand)")
        return 1
    ensure_included(pack)
    target.write_bytes(render_pack(pack, moves, nl).encode("utf-8"))
    CENTRAL.write_bytes(nl.join(keep).encode("utf-8"))
    print(f"wrote {target.relative_to(REPO)} and {CENTRAL.relative_to(REPO)}")
    print("NEXT: dump `--resolved-rules Player` after, and compare with tools/packs/compare_resolved.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
