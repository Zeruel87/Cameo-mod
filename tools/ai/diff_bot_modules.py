#!/usr/bin/env python3
"""Compare two bot-module dumps (AI_ARCHITECTURE.md §2.9 P0, the equivalence gate).

Each phase of the empty-ai.yaml plan must leave the engine's bot-module fields identical, except for
the deliberate changes it lists. This prints every field that exists on one side only, and for every
changed field which list entries were added or removed (sets and dictionaries are compared by entry,
so a reordered set is not a change — the dump already sorts them).

    python tools/ai/diff_bot_modules.py before.txt after.txt          # exit 1 on any difference
    python tools/ai/diff_bot_modules.py before.txt after.txt --allow 'SquadManagerBotModuleCA@*.GuerrillaTypes'

--allow takes shell-style patterns of fields whose change is the phase's declared, deliberate one;
they are still printed, but do not fail the gate.
"""
from __future__ import annotations

import argparse
import fnmatch
import pathlib
import sys


def load(path: pathlib.Path) -> dict[str, str]:
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if " = " in line:
            key, value = line.split(" = ", 1)
            fields[key] = value
    return fields


def entries(value: str) -> list[str] | None:
    """The entries of a set `[..]` or dictionary `{..}`; None for a scalar or an ordered list."""
    if len(value) >= 2 and value[0] in "[{" and value[-1] == {"[": "]", "{": "}"}[value[0]]:
        inner = value[1:-1]
        sep = "; " if value[0] == "{" else ", "
        return [e for e in inner.split(sep) if e] if inner else []
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("before", type=pathlib.Path)
    ap.add_argument("after", type=pathlib.Path)
    ap.add_argument("--allow", action="append", default=[], help="field pattern whose change is deliberate")
    ap.add_argument("--show", type=int, default=12, help="entries to print per side of a changed field")
    args = ap.parse_args()

    a, b = load(args.before), load(args.after)
    allowed = lambda k: any(fnmatch.fnmatchcase(k, p) for p in args.allow)  # noqa: E731
    failing = 0

    def report(key: str, text: str) -> None:
        nonlocal failing
        ok = allowed(key)
        failing += not ok
        print(f"{'ALLOWED' if ok else 'CHANGED'} {key}: {text}")

    for key in sorted(a.keys() - b.keys()):
        report(key, "only before")
    for key in sorted(b.keys() - a.keys()):
        report(key, "only after")
    for key in sorted(a.keys() & b.keys()):
        if a[key] == b[key]:
            continue
        ea, eb = entries(a[key]), entries(b[key])
        if ea is None or eb is None:
            report(key, f"{a[key][:120]!r} -> {b[key][:120]!r}")
            continue
        gone, new = sorted(set(ea) - set(eb)), sorted(set(eb) - set(ea))
        report(key, f"-{len(gone)} +{len(new)}"
               + (f"; removed: {', '.join(gone[:args.show])}{' ...' if len(gone) > args.show else ''}" if gone else "")
               + (f"; added: {', '.join(new[:args.show])}{' ...' if len(new) > args.show else ''}" if new else ""))

    same = sum(1 for k in a.keys() & b.keys() if a[k] == b[k])
    print(f"\n{len(a)} fields before, {len(b)} after; {same} identical; {failing} unexplained difference(s)")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
