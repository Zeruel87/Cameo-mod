#!/usr/bin/env python3
"""Find `-Warhead@X:` removals with no accumulated target (engine semantics).

`MiniYaml.ResolveInherits` applies a `-Key` removal against the nodes
accumulated SO FAR, in order: parent nodes merged at each `Inherits`, local
declarations as they appear, `-` removals when reached. A `-Warhead@X:` whose
key was never accumulated raises
`There are no elements with key 'Warhead@X' to remove` at boot.

This replays that accumulation per weapon (parents applied in `Inherits`
order, then the block's own nodes top-to-bottom) and reports every removal
that would have nothing to remove. Typical cause: deleting a local
`Warhead@X:` declaration while leaving its same-block `-Warhead@X:` behind.

Exit 0 = clean; exit 1 = orphans found (boot would crash).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from miniyaml import Ruleset  # noqa: E402


def main() -> int:
    rs = Ruleset(Path.cwd())
    memo: dict[str, set[str]] = {}
    orphans: list[str] = []

    def resolved_keys(name: str) -> set[str]:
        if name in memo:
            return memo[name]
        memo[name] = set()
        src = rs.weapons.get(name)
        if src is None:
            return set()
        acc: set[str] = set()
        for c in src.children:
            k = c.key
            if k.startswith("Inherits") and c.value:
                acc |= resolved_keys(str(c.value).strip())
            elif k.startswith("-"):
                t = k[1:]
                if t in acc:
                    acc.discard(t)
                else:
                    orphans.append(f"{name}: -{t} (no accumulated target)")
            else:
                acc.add(k)
        memo[name] = acc
        return acc

    for name in list(rs.weapons):
        if not name.startswith("^"):
            resolved_keys(name)

    for p in orphans:
        print(p)
    print(f"\n{len(orphans)} orphan removals (engine semantics)")
    return 1 if orphans else 0


if __name__ == "__main__":
    raise SystemExit(main())
