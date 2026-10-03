#!/usr/bin/env python3
"""audit_duplicate_inherits.py — detect actors/templates that inherit the same
parent through more than one Inherits@ path.

The engine merges inherited subtrees by key. When the same parent is reached via
two different Inherits@ lines, its children can be merged twice, leading to
order-dependent overrides or, in the worst case, a boot-time YAML parse crash.

This is especially dangerous when adding a parent to a base template: the
children that already inherited that parent through another base now get it
from two paths. Grepping `Inherits:` cannot see it because the collision only
appears after resolution.
"""
from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).parent.parent / "tools" / "audit"),
                str(Path(__file__).parent.parent / "tools" / "balance")]

from cameo_model import Model


def collect_paths(rs, name, path_so_far: tuple[str, ...] = ()) -> list[tuple[str, tuple[str, ...]]]:
    """Return [(parent_target, inheritance_chain), ...] for name."""
    node = rs.actor(name)
    if node is None:
        return []
    if name.lower() in path_so_far:
        return []  # cycle guard
    current = path_so_far + (name.lower(),)
    out: list[tuple[str, tuple[str, ...]]] = []
    seen_here: set[str] = set()
    for key, target in rs.inherits_of(node):
        out.append((target.lower(), current + (f"{key}:{target}",)))
        seen_here.add(target.lower())
        out.extend(collect_paths(rs, target, current))
    return out


def audit(rs, templates_too: bool = False) -> dict[str, list[list[tuple[str, tuple[str, ...]]]]]:
    """For every actor/template, find any parent reached by more than one path."""
    dupes: dict[str, list[list[tuple[str, tuple[str, ...]]]]] = collections.defaultdict(list)
    names = sorted(rs.actors)
    if not templates_too:
        names = [n for n in names if not n.startswith("^")]
    for name in names:
        paths = collect_paths(rs, name)
        by_parent: dict[str, list[tuple[str, tuple[str, ...]]]] = collections.defaultdict(list)
        for target, chain in paths:
            by_parent[target].append((target, chain))
        for parent, chains in by_parent.items():
            if len(chains) > 1:
                dupes[name].append(chains)
    return dupes



# ── THE BLOCKING CLASS, SIMULATED THE WAY THE ENGINE ACTUALLY DOES IT ─────────
# `audit()` above reports every parent reached by more than one path. Most of those
# are DIAMONDS through sibling branches, which boot fine, so the report was advisory
# and `main()` always returned 0. Two things made that insufficient on 2026-09-12:
#
#   1. it walked ACTORS ONLY. Weapons are a separate namespace and the crash class is
#      identical there. Master `b235c698` ships exactly ONE blocking node and this audit
#      exited 0 on it; the game did not reach the menu. MEASURED 2026-09-13 by running this
#      file against a clean `origin/master` worktree:
#
#          # BLOCKING - 1 node(s) ...
#            Wraith_ToxinMissiles  ->  ^Warhead_MissileAP_Heavy
#              Wraith_ToxinMissiles -> Inherits:DeviatorMissile_Artillery
#                -> Inherits@3:DeviatorMissile -> Inherits@6:^D2KMissile
#                -> Inherits@wh:^Warhead_MissileAP_Heavy
#
#      ⚠ THIS LINE PREVIOUSLY SAID "SIX" AND THAT WAS WRONG — an unmeasured number written
#      alongside the fix. PR #361 said ONE, the two comments disagreed in the same tree, and
#      the measurement settles it in #361's favour. One weapon is enough: the engine throws on
#      the first, so a count above one could only ever be found by fixing them one at a time.
#   2. "reached twice" is not the engine's rule, so it could not be gated.
#
# MiniYaml.cs:463-476 is the rule. Resolving a node, `inherited` accumulates each
# DIRECT parent at that level and is threaded DOWN into each parent's own resolution;
# a sibling's subtree does NOT contribute back. So the error fires exactly when one
# name appears twice along a single ROOT-TO-ANCESTOR PATH — which is why a diamond
# through two siblings is legal and a direct-plus-inherited repeat is not.
#
# `-` overrides are irrelevant here: the throw happens during inherit expansion,
# before any removal is applied.
def blocking(rs, lookup, names):
    """[(name, parent, path)] for every node the engine would refuse to resolve."""
    out = []

    def walk(node, inherited, path, origin):
        for key, target in rs.inherits_of(node):
            if target.lower() in inherited:
                out.append((origin, target, path + [f"{key}:{target}"]))
                continue                       # report once; do not recurse into the loop
            parent = lookup(target)
            nxt = inherited | {target.lower()}
            if parent is not None:
                walk(parent, nxt, path + [f"{key}:{target}"], origin)
            inherited = nxt                    # accumulates across SIBLINGS, like the engine

    for name in names:
        node = lookup(name)
        if node is not None:
            walk(node, frozenset(), [name], name)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--templates", action="store_true", help="include ^ templates too")
    ap.add_argument("--parent", default="", help="only report a specific parent (e.g. ^Corrodible)")
    args = ap.parse_args()

    m = Model()

    # ⛔ THE GATE. Actors AND weapons — the crash class is namespace-agnostic and this
    # audit was blind to weapons until 2026-09-12.
    hard = (blocking(m.rs, m.rs.actor, sorted(m.rs.actors))
            + blocking(m.rs, m.rs.weapon, sorted(m.rs.weapons)))
    if hard:
        print(f"# BLOCKING — {len(hard)} node(s) the engine will REFUSE to resolve "
              f"(boot crash: 'Parent type X was already inherited by this yaml tree')")
        for name, parent, path in hard:
            print(f"  {name}  ->  {parent}")
            print(f"      {' -> '.join(path)}")
        print()
    else:
        print("_clean_ — no node reaches the same parent twice on one chain "
              "(actors and weapons).")

    dupes = audit(m.rs, templates_too=args.templates)
    if args.parent:
        dupes = {n: [chains for chains in chains_list if chains[0][0] == args.parent.lower()]
                 for n, chains_list in dupes.items()}
        dupes = {n: c for n, c in dupes.items() if c}

    if not dupes:
        print("_clean_ — no duplicate inheritance paths found.")
        return 1 if hard else 0

    print(f"# audit_duplicate_inherits — {len(dupes)} actor(s)/template(s) reach a parent through more than one path")
    for name in sorted(dupes):
        print(f"\n{name}:")
        for chains in dupes[name]:
            parent = chains[0][0]
            print(f"  parent ^^ {parent}  ({len(chains)} paths)")
            for _, chain in chains:
                print(f"    -> {' -> '.join(chain)}")

    # The DIAMOND report above is advisory: sibling-path duplicates boot fine. Only the
    # BLOCKING list gates, because only it is what the engine refuses.
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
