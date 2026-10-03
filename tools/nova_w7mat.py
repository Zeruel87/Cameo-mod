#!/usr/bin/env python3
"""nova_w7mat.py — materialize W7 weapon->weapon inherit edges.

For each named weapon W carrying `Inherits*: <concrete weapon>` edges, drop
those edges and re-emit the lost content as local pins so the weapon resolves
identical to its BASE resolution. Per the maintainer ruling, resolved
`Warhead@*ExtraDamage` chip nodes typed as damage warheads are FOLDED into the
effective main warhead's Damage (sum) instead of being re-emitted. Passengers
(`OpenToppedDamage` & other non-damage types) are never folded.

Why --base: converting parents and children in one batch breaks children if
targets are resolved on the live tree — a folded parent changes what a child
inherits (child's local main Damage then shadows the parent's folded value).
Targets and expectations are therefore resolved against an immutable BASE
worktree (--base, typically a `git worktree` at the pre-change commit).

Method per weapon:
  1. target  = base.resolve_weapon(W); parents = concrete Inherits* values
  2. replace each `Inherits*: P` line with a `#W7MAT:P` marker (keeps position)
  3. delete local `Warhead@*ExtraDamage` decls for folded chips (not pinned)
  4. drop orphan `-X:` cancels whose node no remaining provider supplies
  5. re-resolve on the live tree (inter); emit pins for every lost node/field:
       - warhead nodes whose first-supplier is a removed parent get a bare
         `Warhead@K:` stub at that parent's marker (first-seen position)
       - ALL field pins + the fold Damage bump go at the block tail so they
         merge last and win over surviving local decls
  6. re-resolve; verify unordered payload == fold(target) AND ordered warhead
     keys == target order minus folded chips

Every write re-locates block spans fresh — writing through pre-edit offsets
corrupts neighbouring blocks (DAWN batch-4 lesson).

Usage:
  python tools/nova_w7mat.py --base C:/tmp/w7head [--apply] [--no-fold] [--verbose] W [...]
"""
import argparse
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "audit"))
import miniyaml

ROOT = pathlib.Path(__file__).resolve().parent.parent

INHERIT = re.compile(r"^(\s*)Inherits[^:]*:\s*(\S+)")
CANCEL = re.compile(r"^\s*(-\S[^:]*):")
DAMAGE_TYPES = {"SpreadDamage", "AreaDamage", "TargetDamage", "HealthPercentageDamage"}
# block body runs through indented lines, blank lines, and `#`
# comment banners (they sit INSIDE logical blocks in these files)
BLOCK_RE = r"(?m)^{}:\n(?P<body>(?:[^\S\n][^\n]*\n|[ 	]*#[^\n]*\n|\s*\n)*)"
MARKER = re.compile(r"^\s*#W7MAT:(\S+)")
CHIP_KEY = re.compile(r"Warhead@.*ExtraDamage")
WARHEAD1 = re.compile(r"^\tWarhead(@\S+)?:[^:]*$")


def fresh_rs():
    return miniyaml.Ruleset(ROOT)


def payload_unsorted(node):
    return (node.value or "", tuple(sorted(
        (c.key, payload_unsorted(c)) for c in node.children)))


def warhead_order(node):
    return [c.key for c in node.children
            if c.key == "Warhead" or c.key.startswith("Warhead@")]


def weapon_files_blocks(rs, name):
    """[(path, start, end)] for every top-level def of `name` in weapon files."""
    out = []
    for entry in rs.manifest.weapons:
        path = pathlib.Path(str(entry))
        if not path.is_absolute():
            path = ROOT / path
        if not path.exists():
            continue
        txt = path.read_text(encoding="utf-8-sig", errors="replace")
        for m in re.finditer(BLOCK_RE.format(re.escape(name)), txt):
            span = txt[m.start(0):m.end(0)]
            bl = span.splitlines(keepends=True)
            while bl and (not bl[-1].strip() or bl[-1].lstrip().startswith("#")):
                bl.pop()
            out.append((path, m.start(0), m.start(0) + sum(len(x) for x in bl)))
    return out


def weapon_parents(rs, name):
    node = rs.weapon(name)
    if node is None:
        return []
    return [c.value for c in node.children
            if (c.key == "Inherits" or c.key.startswith("Inherits@"))
            and c.value and not c.value.startswith("^")]


def resolved_keys(rs, name):
    """Set of top-level child keys a named definition supplies, or ()."""
    n = rs.resolve_weapon(name)
    if n is None:
        n = rs.weapon(name)
    if n is None:
        return ()
    return tuple(c.key for c in n.children)


def ancestor_supplies(rs, weapon_node, removed_parents, node_key):
    """Would anything still supply `node_key` such that `-node_key:` is load-bearing?
    Sources: (a) any remaining ancestor's resolved tree, (b) a local declaration
    in this weapon's own merged block (kill-the-local-decl idiom)."""
    for c in weapon_node.children:
        if c.key == node_key:
            return True
    seen = set()

    def supplies(n, depth):
        if n is None or depth > 12:
            return False
        for c in n.children:
            if c.key == node_key:
                return True
            if (c.key == "Inherits" or c.key.startswith("Inherits@")) and c.value:
                if c.value.lower() in seen:
                    continue
                seen.add(c.value.lower())
                if c.value not in removed_parents and supplies(rs.weapon(c.value), depth + 1):
                    return True
        return False

    for c in weapon_node.children:
        if (c.key == "Inherits" or c.key.startswith("Inherits@")) and c.value \
                and c.value not in removed_parents:
            seen.add(c.value.lower())
            if supplies(rs.weapon(c.value), 0):
                return True
    return False


def diff_node(target, got):
    """Pin-fragment needed to close got -> target, or None.
    Children present in `got` but absent in `target` emit `-key:` cancels:
    surviving providers resurrect content a removed parent had suppressed."""
    if got is None:
        return target
    missing = []
    tkeys = {c.key for c in target.children}
    for tc in target.children:
        gc = next((c for c in got.children if c.key == tc.key), None)
        if gc is None:
            missing.append(tc)
        else:
            sub = diff_node(tc, gc)
            if sub is not None:
                missing.append(sub)
    for gc in got.children:
        if gc.key not in tkeys and not gc.key.startswith("-"):
            missing.append(miniyaml.Node("-" + gc.key, None, []))
    if (got.value or "") != (target.value or "") or missing:
        return miniyaml.Node(target.key, target.value, missing)
    return None


def emit_node(node, depth, lines):
    if node.children:
        lines.append("\t" * depth + f"{node.key}:{(' ' + node.value) if node.value else ''}\n")
        for c in node.children:
            emit_node(c, depth + 1, lines)
    else:
        if node.value:
            lines.append("\t" * depth + f"{node.key}: {node.value}\n")
        else:
            lines.append("\t" * depth + f"{node.key}:\n")


def scan_block(block):
    """Classify a pre-strip block: edges in order, local warhead decl lines."""
    edges = []        # [(idx, value)]
    local_wh = {}     # warhead key -> first decl line idx
    for i, line in enumerate(block.splitlines()):
        m = INHERIT.match(line)
        if m:
            edges.append((i, m.group(2)))
        wm = WARHEAD1.match(line)
        if wm:
            key = "Warhead" + (wm.group(1) or "")
            local_wh.setdefault(key, i)
    return edges, local_wh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("weapons", nargs="*")
    ap.add_argument("--base", required=True, help="pristine worktree path (HEAD)")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--no-fold", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    base = miniyaml.Ruleset(pathlib.Path(args.base).resolve())
    results = []
    for w in args.weapons:
        target = base.resolve_weapon(w)
        if target is None:
            results.append((w, "MISSING"))
            print(f"{w}: MISSING")
            continue
        parents = weapon_parents(base, w)
        if not parents:
            results.append((w, "NO-WEAPON-PARENT"))
            print(f"{w}: NO-WEAPON-PARENT")
            continue
        if not weapon_files_blocks(base, w):
            results.append((w, "NO-BLOCK"))
            print(f"{w}: NO-BLOCK")
            continue

        # foldable chips: resolved Warhead@*ExtraDamage nodes typed as damage
        # warheads with a Damage. OpenToppedDamage twins must not fold.
        chips = [c for c in target.children
                 if CHIP_KEY.match(c.key) and c.get("Damage")
                 and (c.value in DAMAGE_TYPES)]
        chip_sum = 0 if args.no_fold else sum(int(c.get("Damage")) for c in chips)
        chip_keys = set() if args.no_fold else {c.key for c in chips}
        main_node = None
        if chips and not args.no_fold:
            mains = [c for c in target.children
                     if (c.key == "Warhead" or c.key.startswith("Warhead@"))
                     and (c.value in DAMAGE_TYPES)
                     and c.key not in chip_keys and c.get("Damage")]
            mains.sort(key=lambda c: int(c.get("Damage") or 0), reverse=True)
            main_node = mains[0] if mains else None
            if main_node is None:
                results.append((w, "FOLD-NO-MAIN"))
                print(f"{w}: FOLD-NO-MAIN")
                continue

        state = {"rs": fresh_rs()}

        def rewrite_blocks(mutate):
            """Re-find W's blocks fresh, mutate each, write back per file."""
            dirty = {}
            for path, s0, e0 in weapon_files_blocks(state["rs"], w):
                txt = path.read_text(encoding="utf-8-sig", errors="replace")
                nb = mutate(txt[s0:e0])
                if nb != txt[s0:e0]:
                    dirty.setdefault(path, []).append((s0, e0, nb))
            for path, edits in dirty.items():
                txt = path.read_text(encoding="utf-8-sig", errors="replace")
                for s0, e0, nb in sorted(edits, key=lambda e: -e[0]):
                    txt = txt[:s0] + nb + txt[e0:]
                path.write_text(txt, encoding="utf-8", newline="")
            if dirty:
                state["rs"] = fresh_rs()
            return bool(dirty)

        # anchor map: which marker each displaced warhead node hangs on.
        # Computed on the CURRENT block (post-reset == base shape).
        blocks0 = weapon_files_blocks(state["rs"], w)
        edge_order = []          # [(edge_idx_in_block_order, value)]
        local_wh = {}
        if blocks0:
            txt0 = blocks0[-1][0].read_text(encoding="utf-8-sig", errors="replace")
            block0 = txt0[blocks0[-1][1]:blocks0[-1][2]]
            edges, local_wh = scan_block(block0)
            edge_order = edges

        # 1) strip Inherits*: <weapon-parent> lines -> markers
        def strip_pass(block):
            out = []
            for line in block.splitlines(keepends=True):
                m = INHERIT.match(line)
                if m and m.group(2) in parents:
                    out.append("\t#W7MAT:" + m.group(2) + "\n")
                else:
                    out.append(line)
            return "".join(out)

        rewrite_blocks(strip_pass)
        rs2 = state["rs"]
        inter = rs2.resolve_weapon(w)
        if inter is None:
            results.append((w, "VANISHED-AFTER-STRIP"))
            print(f"{w}: VANISHED-AFTER-STRIP")
            continue

        # 2) delete local Warhead@*ExtraDamage decls for folded chips
        if chip_keys:
            chip_re = re.compile(
                r"^\tWarhead@(?:" + "|".join(
                    re.escape(k.split("@", 1)[1]) for k in chip_keys) + r"):")

            def drop_chip_decls(block):
                out, skip_depth = [], 0
                for line in block.splitlines(keepends=True):
                    depth = len(line) - len(line.lstrip())
                    if skip_depth and depth > skip_depth:
                        continue
                    skip_depth = 0
                    if depth == 1 and chip_re.match(line):
                        skip_depth = depth
                        continue
                    out.append(line)
                return "".join(out)
            rewrite_blocks(drop_chip_decls)
            rs2 = state["rs"]
            inter = rs2.resolve_weapon(w)

        # 3) prune orphan cancels (their providers are gone)
        wnode = rs2.weapon(w)
        if wnode is not None:
            def drop_orphans(block):
                blines = block.splitlines(keepends=True)
                kv = re.compile(r'^\s*(-?\S[^:]*?):')
                # per line: enclosing depth-1 node key (for nested cancels)
                owner = []
                cur = None
                for line in blines:
                    d = len(line) - len(line.lstrip())
                    m = kv.match(line)
                    if d == 1 and m and not line.lstrip().startswith('#'):
                        cur = m.group(1).lstrip('-')
                    owner.append(cur)
                def subtree_has(n, k):
                    return n is not None and any(
                        c.key == k or subtree_has(c, k) for c in n.children)
                out = []
                for i, line in enumerate(blines):
                    mc = CANCEL.match(line)
                    if not mc:
                        out.append(line)
                        continue
                    key = mc.group(1)[1:]
                    d = len(line) - len(line.lstrip())
                    if d == 1:
                        if ancestor_supplies(rs2, wnode, set(parents), key):
                            out.append(line)
                        continue
                    # nested cancel: dead iff the enclosing node's post-strip
                    # subtree has no `key` left to cancel (inter resolve)
                    enc = owner[i]
                    inode = next((c for c in inter.children if c.key == enc), None) if enc else None
                    if enc is not None and subtree_has(inode, key):
                        out.append(line)
                    # else drop the dead cancel
                return ''.join(out)
            rewrite_blocks(drop_orphans)
            rs2 = state["rs"]
            inter = rs2.resolve_weapon(w)

        # 4) anchor resolution on BASE: for each warhead key in target order,
        # find the first supplier among block edges (document order) or the
        # local decl, whichever comes first.
        sup = {v: set(resolved_keys(base, v)) for _, v in edge_order}
        anchors = {}   # warhead key -> parent value (marker) or None
        t_order = {c.key: i for i, c in enumerate(target.children)}
        for tc in target.children:
            if not (tc.key == "Warhead" or tc.key.startswith("Warhead@")):
                continue
            if tc.key in chip_keys:
                continue
            first_edge = None
            for ei, v in edge_order:
                if tc.key in sup.get(v, ()):
                    first_edge = v
                    break
            decl = local_wh.get(tc.key)
            # anchor at the marker only if the supplying edge precedes the
            # local decl (or there is none) and that edge is being removed
            if first_edge is not None and first_edge in parents \
                    and (decl is None or decl > next(i for i, v in edge_order if v == first_edge)):
                anchors[tc.key] = first_edge

        # 5) field pins for every lost node/field (tail) + stubs at markers
        pins = []
        for tc in target.children:
            if tc.key in chip_keys:
                continue
            gc = next((c for c in inter.children if c.key == tc.key), None)
            d = diff_node(tc, gc)
            if d is not None:
                pins.append(d)
        # folded chips a surviving provider still re-supplies need `-key:` kills
        for ck in chip_keys:
            if any(c.key == ck for c in inter.children):
                pins.append(miniyaml.Node("-" + ck, None, []))
        if main_node is not None and chip_sum:
            bumped = str(int(main_node.get("Damage")) + chip_sum)
            for p in pins:
                if p.key == main_node.key:
                    idx = next((j for j, c in enumerate(p.children) if c.key == "Damage"), None)
                    if idx is None:
                        p.children.append(miniyaml.Node("Damage", bumped))
                    else:
                        p.children[idx] = miniyaml.Node("Damage", bumped)
                    break
            else:
                pins.append(miniyaml.Node(main_node.key, "",
                    [miniyaml.Node("Damage", bumped)]))

        tkeys = {c.key for c in target.children}
        for c in inter.children:
            if c.key not in tkeys and not c.key.startswith("-"):
                pins.append(miniyaml.Node("-" + c.key, None, []))

        stub_groups = {}
        for k, pv in anchors.items():
            stub_groups.setdefault(pv, []).append(k)
        for pv in stub_groups:
            stub_groups[pv].sort(key=lambda k: t_order[k])

        def emit_pins(block):
            lines = block.splitlines(keepends=True)
            out = []
            for line in lines:
                mm = MARKER.match(line)
                if mm:
                    for k in stub_groups.get(mm.group(1), []):
                        out.append("\t" + k + ":\n")
                    # marker consumed
                    continue
                out.append(line)
            if pins:
                if out and not out[-1].endswith("\n"):
                    out[-1] += "\n"
                pl = []
                for p in pins:
                    emit_node(p, 1, pl)
                out.extend(pl)
            return "".join(out)

        rewrite_blocks(emit_pins)

        # 6) verify on a fresh live resolve
        rs3 = fresh_rs()
        got = rs3.resolve_weapon(w)
        expect_children = []
        for c in target.children:
            if c.key in chip_keys:
                continue
            if main_node is not None and chip_sum and c.key == main_node.key:
                bumped = c.deep_copy()
                for cc in bumped.children:
                    if cc.key == "Damage":
                        cc.value = str(int(c.get("Damage")) + chip_sum)
                expect_children.append(bumped)
            else:
                expect_children.append(c)
        expect = miniyaml.Node(target.key, target.value, expect_children)
        if got is None:
            results.append((w, "VANISHED"))
            print(f"{w}: VANISHED  parents={parents}")
            continue
        if payload_unsorted(got) != payload_unsorted(expect):
            results.append((w, "PAYLOAD-MISMATCH"))
            print(f"{w}: PAYLOAD-MISMATCH  parents={parents} pins={len(pins)}")
            continue
        if warhead_order(got) != warhead_order(expect):
            results.append((w, "ORDER-DIFF"))
            print(f"{w}: ORDER-DIFF  parents={parents}")
            continue
        results.append((w, "OK"))
        print(f"{w}: OK  parents={parents} pins={len(pins)} stubs={sum(len(v) for v in stub_groups.values())} folded={chip_sum}")
    return results


if __name__ == "__main__":
    sys.exit(0 if all(r[1] in ("OK", "NO-WEAPON-PARENT") for r in main()) else 1)
