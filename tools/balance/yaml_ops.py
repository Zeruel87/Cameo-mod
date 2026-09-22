#!/usr/bin/env python3
"""yaml_ops.py — line-addressed edits to MiniYaml files, applied bottom-up.

A plan is `{relative_path: {line: [op, ...]}}` with 1-based lines taken from
`miniyaml` node `.file` / `.line`, and ops:

    ("sub", old, new)   replace `old` with `new` on that line, if present
    ("ins", [lines])    insert after that line, verbatim (tabs included)
    ("delline",)        delete that one line
    ("delblock", end)   delete lines[line-1 : end]  (see `block_extent`)
    ("delsub",)         delete that node and every line indented deeper (see `sub_extent`)

⚠ BOTTOM-UP IS NOT AN OPTIMISATION. Every line number in the plan was captured against the
ORIGINAL file, so applying edits in descending line order is what keeps the not-yet-applied
numbers valid. Applying top-down shifts every later target by the lines already inserted or
deleted, and the corruption lands quietly in the middle of unrelated actors.

⚠ WHERE TO INSERT INTO A WEAPON OR ACTOR BLOCK: after the LAST `Inherits` line, never at the
top. Children resolve in document order, so a node declared before the inherit is appended to
the accumulator first and the parent then merges INTO that early slot — which moves a warhead's
position in the FIRING ORDER. For the same reason a `-Key` removal placed before the inherit
that supplies the key removes nothing at all.
"""
from __future__ import annotations

import collections
import pathlib
import subprocess


def new_plan():
    return collections.defaultdict(lambda: collections.defaultdict(list))


def read_lines(path: pathlib.Path) -> tuple[list[str], str]:
    raw = path.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    return raw.split(nl), nl


def block_extent(path: pathlib.Path, start: int) -> int:
    """0-based exclusive end of the TOP-LEVEL block whose first line is 1-based `start`.

    Runs to the next column-0 non-blank line; trailing blanks are given back so a block never
    swallows the separator that ends it.
    """
    lines, _ = read_lines(path)
    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].strip() and not lines[i][0].isspace():
            end = i
            break
    while end > start and not lines[end - 1].strip():
        end -= 1
    return end


def sub_extent(lines: list[str], idx: int) -> int:
    """0-based exclusive end of the child block at `lines[idx]`: it plus deeper-indented lines."""
    depth = len(lines[idx]) - len(lines[idx].lstrip("\t"))
    end, i = idx + 1, idx + 1
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if len(ln) - len(ln.lstrip("\t")) <= depth:
            break
        end = i = i + 1
    return end


def apply_plan(plan, root: pathlib.Path) -> int:
    """Apply every op. Returns the number of line-level changes made."""
    n = 0
    for rel, per_line in plan.items():
        path = root / rel
        lines, nl = read_lines(path)
        for line in sorted(per_line, reverse=True):
            idx = line - 1
            ins, cut = [], None
            for op in per_line[line]:
                if op[0] == "sub":
                    if op[1] in lines[idx]:
                        lines[idx] = lines[idx].replace(op[1], op[2])
                        n += 1
                elif op[0] == "ins":
                    ins.extend(op[1])
                elif op[0] == "delline":
                    cut = idx + 1
                elif op[0] == "delblock":
                    cut = op[1]
                elif op[0] == "delsub":
                    cut = sub_extent(lines, idx)
                else:
                    raise ValueError(f"unknown op {op[0]}")
            if ins:
                lines[idx:idx + 1] = [lines[idx]] + ins
                n += len(ins)
            if cut is not None:
                del lines[idx:cut]
                n += cut - idx
        path.write_bytes(nl.join(lines).encode("utf-8"))
    return n


def git_restore(root: pathlib.Path, paths: list[str]) -> None:
    """`git checkout --` the given paths. Scoped by construction: it takes an explicit list.

    ⛔ Never widen this to `.` or `-A`. Several contributors keep live WIP in this tree.
    """
    if not paths:
        return
    subprocess.run(["git", "checkout", "--", *paths], cwd=root, check=True, capture_output=True)


def insert_after_inherits(node) -> int:
    """The line to insert a new local declaration after. See the module warning."""
    inherits = [c.line for c in node.children if c.key.split("@")[0] == "Inherits"]
    return max(inherits) if inherits else node.line
