#!/usr/bin/env python3
"""Engine-strict orphan-cancel check: every `-Key:` must have a provider.

OpenRA's MiniYaml.ResolveInherits (engine/OpenRA.Game/MiniYaml.cs) throws
"There are no elements with key `X` to remove" when a `-X:` cancel has no
matching node in the accumulated merge — that aborts ruleset load at boot.
The python resolver's _merge_into silently skips the same cancel, so a
strip/refactor can pass every resolve-diff and still crash the real game.
Found 2026-09-23 (W23 batch): a child weapon's `-Warhead@GrenadeFriendlyFire`
was legal while its parent's `^Grenade` supplied the node; stripping the
template made the cancel an orphan and the boot died mid-load. Nested
cancels (`-LaunchAngle:` inside `Projectile:`) hit the same rule.

Check: at each tree level the provider set is the union of every resolved
parent's children keys at that path, plus this node's own non-cancel
children *earlier in document order* (the engine merges inherited nodes
first, then applies own children in order). A `-Key` whose target is not
in that set is an orphan. `Inherits` keys are not cancelable.

Exit 1 when orphans exist (boot would crash); 0 when clean.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import miniyaml  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _find_path(node: miniyaml.Node, path: tuple[str, ...]) -> miniyaml.Node | None:
    for key in path:
        node = next((c for c in node.children if c.key == key), None)
        if node is None:
            return None
    return node


def _check_level(raw_here: miniyaml.Node, parents: list[miniyaml.Node],
                 path: tuple[str, ...], owner: str, out: list[str]) -> None:
    avail: set[str] = set()
    for p in parents:
        pn = _find_path(p, path)
        if pn is not None:
            avail |= {c.key for c in pn.children}
    for c in raw_here.children:
        if c.key.startswith("-"):
            target = c.key[1:]
            if target not in avail:
                loc = f"{c.file}:{c.line}" if getattr(c, "file", None) else "?"
                where = "/".join(path) or "."
                out.append(f"{loc} {owner}: {where}/-{target} has no provider")
            else:
                avail.discard(target)
        elif not c.key.startswith("Inherits"):
            avail.add(c.key)
    for c in raw_here.children:
        if c.children and not c.key.startswith("-") and not c.key.startswith("Inherits"):
            _check_level(c, parents, path + (c.key,), owner, out)


def _check_all(r: miniyaml.Ruleset, raw: dict[str, miniyaml.Node],
               resolve, label: str, out: list[str]) -> None:
    for name, node in raw.items():
        parents = []
        for _, target in r.inherits_of(node):
            p = resolve(target)
            if p is not None:
                parents.append(p)
        _check_level(node, parents, (), f"{label}:{name}", out)


def main() -> int:
    r = miniyaml.Ruleset(str(ROOT))
    out: list[str] = []
    _check_all(r, r.weapons, r.resolve_weapon, "weapon", out)
    _check_all(r, r.actors, r.resolve, "actor", out)
    for line in out:
        print(line)
    print(f"orphan cancels: {len(out)}")
    return 1 if out else 0


if __name__ == "__main__":
    sys.exit(main())
