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

`--fragile` additionally reports cancels whose sole provider is ONE parent
inherit edge (report-only, exit unchanged): dropping that edge orphans the
cancel, which is the W2 dead-edge sweep failure mode — a `-X:` is a CONSUMER
of its provider edge, so "nodes absent from resolved output" does not make
the edge dead. Run before any edge-deletion sweep; deleting a provider edge
must carry its cancels with it (or leave both).
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


def _check_level(raw_here: miniyaml.Node, parents: list[tuple[str, miniyaml.Node]],
                 path: tuple[str, ...], owner: str, out: list[str],
                 fragile: list[str] | None = None) -> None:
    avail: set[str] = set()
    earlier_own: set[str] = set()   # keys this node defines BEFORE the cursor
    for _, p in parents:
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
                if fragile is not None and target not in earlier_own:
                    # Provider provenance: a cancel whose sole provider is ONE
                    # parent edge becomes an orphan the moment that edge is
                    # dropped — exactly the W2 dead-edge sweep failure mode.
                    # (A later same-node redeclare does NOT rescue it: the
                    # engine applies own children in document order, so the
                    # cancel still needs the accumulated provider.)
                    providers = [k for k, p in parents
                                 if (pn := _find_path(p, path)) is not None
                                 and any(gc.key == target for gc in pn.children)]
                    if len(providers) == 1:
                        loc = f"{c.file}:{c.line}" if getattr(c, "file", None) else "?"
                        where = "/".join(path) or "."
                        fragile.append(
                            f"{loc} {owner}: {where}/-{target} fragile - sole "
                            f"provider is edge {providers[0]}; dropping it orphans the cancel")
        elif not c.key.startswith("Inherits"):
            avail.add(c.key)
            earlier_own.add(c.key)
    # Same-key siblings merge in the engine: a `-X` inside the second
    # `Projectile:` sees the first `Projectile:`'s fields. Group them so the
    # recursion checks each key against the union of all its siblings.
    groups: dict[str, miniyaml.Node] = {}
    group_order: list[str] = []
    for c in raw_here.children:
        if c.key.startswith("-") or c.key.startswith("Inherits"):
            continue
        if c.key not in groups:
            groups[c.key] = miniyaml.Node(key=c.key, value=c.value, children=[],
                                          file=c.file, line=c.line)
            group_order.append(c.key)
        groups[c.key].children.extend(c.children)
    for key in group_order:
        g = groups[key]
        if g.children:
            _check_level(g, parents, path + (key,), owner, out, fragile)


def _check_all(r: miniyaml.Ruleset, raw: dict[str, miniyaml.Node],
               resolve, label: str, out: list[str],
               fragile: list[str] | None = None) -> None:
    for name, node in raw.items():
        parents = []
        for inh_key, target in r.inherits_of(node):
            p = resolve(target)
            if p is not None:
                parents.append((f"{inh_key} -> {target}", p))
        _check_level(node, parents, (), f"{label}:{name}", out, fragile)


def main() -> int:
    r = miniyaml.Ruleset(str(ROOT))
    out: list[str] = []
    fragile: list[str] | None = [] if "--fragile" in sys.argv else None
    _check_all(r, r.weapons, r.resolve_weapon, "weapon", out, fragile)
    _check_all(r, r.actors, r.resolve, "actor", out, fragile)
    for line in out:
        print(line)
    print(f"orphan cancels: {len(out)}")
    if fragile is not None:
        for line in fragile:
            print(line)
        print(f"fragile cancels: {len(fragile)}")
    return 1 if out else 0


if __name__ == "__main__":
    sys.exit(main())
