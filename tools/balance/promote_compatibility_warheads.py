#!/usr/bin/env python3
"""Promote every ^Compatibility_* shim into a REAL ^Warhead_* template that INHERITS its twin.

    MAINTAINER, 2026-09-12:
      "Any of those silly compatibility warheads must be resolved and replaced by an
       actual new warhead"

WHY THIS IS A RENAME AND NOT ARITHMETIC. `DESIGN.md` recorded this slice as "damage-preserving
arithmetic per weapon, needs warhead permission", because the shim ships `Damage: 0` and yet 365
of its 416 users resolve a nonzero damage on that node. Half right: the shim IS the damage
carrier, so its inherit cannot simply be dropped. But it never followed that the damage has to
MOVE. `^Compatibility_<X>Flat` is the landing zone of an EARLIER W24 pass -- `YamatoCannon`:

    Warhead@Demolition_Heavy:  Damage: 20000
    Warhead@CannonHE_Heavy:    Damage: 20000
    -Warhead@CannonHE_Heavy:
    -Warhead@Demolition_Heavy:
    Warhead@CannonHE_HeavyFlatCompatibility:
        Damage: 40000              <- two mains, already folded into one, parked on the shim

The weapon is already single-main and already correct. Its only defect is that the template it
inherits is not spelled `^Warhead_`. So spell it `^Warhead_`: no damage moves, no Versus row
changes, and no warhead permission is needed because no warhead changes.

⛔ THE TRAP THAT BROKE ATTEMPT 1. The obvious follow-up -- "the real `^Warhead_` inherit is dead,
its node is deleted locally, drop it" -- is WRONG. A `^Warhead_` template carries WEAPON-LEVEL
fields too (`ValidTargets`, `ReloadDelay`, `Range`, `TargetActorCenter`), and the shim carries
NONE. Dropping the inherit silently stripped `TargetActorCenter` off 60+ weapons and left three
warheads with an EMPTY TYPE (the boot-NRE class). A node-level deadness test cannot see either.

SO THE NEW TEMPLATE INHERITS THE TWIN, and takes over the removal the weapon used to do:

    ^Warhead_CannonHE_Heavy_Flat:
        Inherits: ^Warhead_CannonHE_Heavy    <- weapon-level fields arrive through the chain
        -Warhead@CannonHE_Heavy:             <- the twin's main; the flat node replaces it
        Warhead@CannonHE_Heavy_Flat: AreaDamage
            ...the shim's own body, verbatim

and each user loses the now-redundant direct inherit and the removal line the template performs:

    SomeWeapon:                              SomeWeapon:
        Inherits@wh: ^Warhead_CannonHE_Heavy     Inherits@wh: ^Warhead_CannonHE_Heavy_Flat
        Inherits: ^Compatibility_CannonHE_HeavyFlat
        -Warhead@CannonHE_Heavy:
        Warhead@CannonHE_HeavyFlatCompatibility: Warhead@CannonHE_Heavy_Flat:
            Damage: 40000                            Damage: 40000

Both deletions are MANDATORY, not tidying:
  * keeping the direct inherit puts `^Warhead_CannonHE_Heavy` on a single root-to-ancestor path
    TWICE (`MiniYaml.cs:463-476` threads `inherited` DOWN), which is the `Parent type X was
    already inherited` BOOT CRASH. Two sibling shims sharing one twin is a diamond and stays
    legal -- only the root-to-ancestor repeat crashes.
  * keeping the weapon's `-Warhead@<twin>` line orphans it, because the template already removed
    that key, and `There are no elements with key X to remove` is the OTHER boot crash. The
    Python resolver CANNOT see this class: it reported 0 changed weapons once on a tree that
    would not start. Only the engine finds it, which is why the boot gate is not optional.

HOW IT GATES ITSELF. Heuristics are what produced attempt 1, so this run does not trust any.
It applies, then compares the RESOLVED node of every weapon against a pristine baseline
worktree, order-insensitively and through the name map. Any template whose users move CONTENT
is excluded and the whole edit is redone from clean, until the surviving set verifies EXACTLY.
Whatever lands is provably behaviour-identical; whatever cannot is reported, not forced.

Usage:
    python tools/balance/promote_compatibility_warheads.py --base <pristine-worktree> [--apply]
"""
from __future__ import annotations

import collections
import pathlib
import re
import subprocess
import sys

sys.path[:0] = ["tools/audit"]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import miniyaml  # noqa: E402
import resolved_gate  # noqa: E402

ROOT = pathlib.Path(".").resolve()
COMPAT = "^Compatibility_"
# Stripping "Compatibility" off these lands on a key another node already uses; merging two
# nodes onto one key would silently combine them. The TEMPLATE key still renames.
INNER_SKIP = {"LaserExtraDamageCompatibility", "RailgunExtraDamageCompatibility"}
SUFFIXES = ("Flat", "ExtraDamage", "GroundSlice", "Composition")


def new_template_name(t: str) -> str:
    return "^Warhead_" + re.sub(r"(?<=[a-z])Flat\b", "_Flat", t[len(COMPAT):])


def new_inner_name(nm: str) -> str | None:
    if nm in INNER_SKIP or not nm.endswith("Compatibility"):
        return None
    return re.sub(r"(?<=[a-z])Flat$", "_Flat", nm[: -len("Compatibility")])


def twin_of(t: str, weapons) -> str | None:
    rest = t[len(COMPAT):]
    cands = [rest[: -len(s)].rstrip("_") for s in SUFFIXES if rest.endswith(s)]
    cands.append(rest)
    for c in list(cands):
        parts = c.split("_")
        if len(parts) > 2:
            cands.append("_".join(parts[:2]))
    for c in cands:
        if "^Warhead_" + c in weapons:
            return "^Warhead_" + c
    return None


# The comparator moved to tools/balance/resolved_gate.py, which pairs this module's
# order-INSENSITIVE field set with an order-SENSITIVE warhead-sequence check. A set alone
# cannot see a reorder: it accepted the Wraith change that moved a 60,000-damage main to
# AFTER `Warhead@OwnerChange`, so the unit captured a target and then shot it (found by
# Codex in review, PR #356). Both halves are now mandatory.


def build_plan(rs, excluded: set[str]):
    """(ops, meta) -- ops: file -> {line: [operation, ...]}; operations are
    ('sub', old, new) | ('del',) | ('ins', [text, ...])."""
    ops: dict[str, dict[int, list]] = collections.defaultdict(lambda: collections.defaultdict(list))
    templates = [t for t in sorted(rs.weapons) if t.startswith(COMPAT) and t not in excluded]
    tmap = {t: new_template_name(t) for t in templates}
    twin = {t: twin_of(t, rs.weapons) for t in templates}

    # ---- route each template ---------------------------------------------- #
    # One template CANNOT serve both populations, and that is the whole difficulty:
    #   * a user that already inherits the twin wants the new template to CHAIN it, so the
    #     weapon-level fields (Range, ReloadDelay, ValidTargets, TargetActorCenter) keep
    #     arriving once its own duplicate inherit is dropped;
    #   * a user that inherits NO ^Warhead_ at all would GAIN those fields from the chain --
    #     measured: 112 weapons newly gained `Warhead@Bullet_Medium`, 11 gained
    #     `TargetActorCenter`. A behaviour change, so those families stay standalone.
    # CHAIN only where EVERY user already inherits the twin; RENAME where NO user inherits a
    # ^Warhead_ at all; SKIP the mixed families -- 56 of 64 are mixed, and each needs a
    # per-weapon decision plus a SECOND template per family. That is a separate change.
    users_of = collections.defaultdict(list)
    for w, node in rs.weapons.items():
        if w.startswith("^"):
            continue
        inh = {c.value.strip() for c in node.children
               if c.key.split("@")[0] == "Inherits"}
        for v in inh:
            if v in tmap:
                users_of[v].append(inh)

    mode = {}
    for t in templates:
        us = users_of.get(t, [])
        tw = twin[t]
        if tw and us and all(tw in inh for inh in us):
            mode[t] = "chain"
        elif not any(v.startswith("^Warhead_") for inh in us for v in inh):
            mode[t] = "rename"
        else:
            mode[t] = "skip"
    for t in [k for k, v in mode.items() if v == "skip"]:
        del tmap[t]
    templates = [t for t in templates if mode[t] != "skip"]

    # imap is built AFTER the routing on purpose. Built before, it renamed the inner node of
    # a SKIPPED template too, and `d2k_airdefenseplatform` -- which inherits from the WEAPON
    # `HMG_turret` (a W7 violation) and declares `Warhead@Bullet_MediumFlatCompatibility`
    # BARE -- lost its warhead type. One weapon, and it was the only failure in the pass.
    imap: dict[str, str] = {}
    for t in templates:
        for c in rs.weapons[t].children:
            if c.key.startswith("Warhead@"):
                nn = new_inner_name(c.key[len("Warhead@"):])
                if nn:
                    imap[c.key[len("Warhead@"):]] = nn

    # ---- the templates themselves ---------------------------------------- #
    chained = []
    for t in templates:
        top = rs.weapons[t]
        ops[top.file][top.line].append(("sub", t, tmap[t]))
        if mode[t] != "chain":
            continue
        if any(c.key.split("@")[0] == "Inherits" for c in top.children):
            chained.append(t)          # already has a parent; do not add a second
            continue
        # NO `-Warhead@<twin>` inserted here: the users keep their own removal lines.
        # Inserting it killed a LIVE twin main on 25mm and left a bare local override with
        # an EMPTY warhead type -- the boot-NRE class.
        ops[top.file][top.line].append(("ins", ["	Inherits: " + twin[t]]))

    # ---- every reference, corpus-wide ------------------------------------ #
    users: dict[str, list[str]] = collections.defaultdict(list)

    def walk(node, depth=0):
        for c in node.children:
            base = c.key.lstrip("-")
            if base.startswith("Warhead@"):
                nn = imap.get(base[len("Warhead@"):])
                if nn:
                    ops[c.file][c.line].append(("sub", base[len("Warhead@"):], nn))
            if depth < 1:
                walk(c, depth + 1)

    for w, node in rs.weapons.items():
        walk(node)
        if w.startswith("^"):
            continue
        inh = [(c, c.value.strip()) for c in node.children
               if c.key.split("@")[0] == "Inherits"]
        mine = [(c, v) for c, v in inh if v in tmap]
        if not mine:
            continue
        for c, v in mine:
            ops[c.file][c.line].append(("sub", v, tmap[v]))
            users[v].append(w)
        # The twin's direct inherit now arrives through the chained template. Keeping it as
        # well puts one parent on a single root-to-ancestor path TWICE, which is the
        # `Parent type X was already inherited` boot crash. The weapon's own
        # `-Warhead@<twin>` line STAYS -- the template does not remove that node.
        twins = {twin[v] for _, v in mine
                 if mode.get(v) == "chain" and twin[v] and v not in chained}
        for c, v in inh:
            if v in twins:
                ops[c.file][c.line].append(("del",))
    return ops, {"tmap": tmap, "imap": imap, "twin": twin, "users": users,
                 "chained": chained, "mode": mode}


def apply_ops(ops) -> int:
    n = 0
    for f, per_line in ops.items():
        p = ROOT / f
        raw = p.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.split(nl)
        for line in sorted(per_line, reverse=True):
            idx = line - 1
            drop = False
            ins: list[str] = []
            for op in per_line[line]:
                if op[0] == "sub":
                    if op[1] in lines[idx]:
                        lines[idx] = lines[idx].replace(op[1], op[2])
                        n += 1
                elif op[0] == "del":
                    drop = True
                elif op[0] == "ins":
                    ins.extend(op[1])
            if ins:
                lines[idx:idx + 1] = [lines[idx]] + ins
                n += len(ins)
            if drop:
                del lines[idx]
                n += 1
        p.write_bytes(nl.join(lines).encode("utf-8"))
    return n


def restore(paths: list[str]) -> None:
    subprocess.run(["git", "checkout", "--"] + paths, cwd=ROOT, check=True,
                   capture_output=True)


def require_clean_checkout() -> None:
    """Refuse the mutate/restore workflow when any worktree state is dirty.

    ``main`` rewrites active weapon files, then restores them with
    ``git checkout --`` during a dry run or a failed verification pass.  That
    restoration is safe only when the caller has no edits to preserve.
    """
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT, check=True, capture_output=True, text=True)
    if result.stdout.strip():
        raise RuntimeError(
            "refusing compatibility promotion in a dirty checkout; "
            "use a clean temporary worktree")


def verify(base_root: str, meta) -> list[tuple[str, dict]]:
    """Resolved-behaviour comparison against a pristine worktree.

    Returns [(weapon, diff)] for every weapon whose behaviour moved. The rename map is
    applied to the BASELINE, so the question is "is the new tree what the old tree would be
    called under the new names" — mapping the candidate instead would accept a name the map
    does not cover. Both halves of `resolved_gate.compare` run: the field set AND the
    warhead firing order.
    """
    base = miniyaml.Ruleset(base_root)
    cur = miniyaml.Ruleset(str(ROOT))
    ren = dict(meta["tmap"])
    for a, b in meta["imap"].items():
        ren["Warhead@" + a] = "Warhead@" + b
        ren["-Warhead@" + a] = "-Warhead@" + b

    bad: list[tuple[str, dict]] = []
    for w in sorted(base.weapons):
        if w.startswith("^"):
            continue
        if w not in cur.weapons:
            bad.append((w, {"lost": ["the whole weapon"], "gained": []}))
            continue
        diff = resolved_gate.compare(base.resolve_weapon(w), cur.resolve_weapon(w), ren)
        if diff:
            bad.append((w, diff))
    return bad


def main() -> int:
    if "--base" not in sys.argv:
        print(__doc__.strip().splitlines()[-2])
        return 2
    base_root = sys.argv[sys.argv.index("--base") + 1]
    apply_it = "--apply" in sys.argv

    try:
        require_clean_checkout()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    rs0 = miniyaml.Ruleset(str(ROOT))
    paths = sorted({str(p.relative_to(ROOT)).replace("\\", "/")
                    for p in rs0.manifest.weapons})
    excluded: set[str] = set()

    for attempt in range(1, 7):
        rs = miniyaml.Ruleset(str(ROOT))
        ops, meta = build_plan(rs, excluded)
        n = apply_ops(ops)
        bad = verify(base_root, meta)
        print(f"pass {attempt}: templates {len(meta['tmap'])}  users "
              f"{sum(len(v) for v in meta['users'].values())}  edits {n}  "
              f"weapons whose content moved: {len(bad)}")
        if not bad:
            print("\nVERIFIED behaviour-identical.")
            m = meta["mode"]
            print("   routed: chain %d  rename %d  skipped(mixed) %d"
                  % (sum(1 for v in m.values() if v == "chain"),
                     sum(1 for v in m.values() if v == "rename"),
                     sum(1 for v in m.values() if v == "skip")))
            for t in sorted(meta["chained"]):
                print("   chained already, twin not added:", t)
            if excluded:
                print(f"\nEXCLUDED {len(excluded)} template(s) that could not verify:")
                for t in sorted(excluded):
                    print("   ", t, "->", ", ".join(sorted(meta["users"].get(t, []))[:4]))
            if not apply_it:
                restore(paths)
                print("\ndry run - tree restored. Re-run with --apply, then BOOT GATE.")
            return 0
        # attribute each failure to the template(s) it inherits, and exclude those
        blame: set[str] = set()
        for w, _diff in bad:
            node = rs.weapon(w)
            if node is None:
                continue
            for c in node.children:
                if c.key.split("@")[0] == "Inherits" and c.value.strip() in meta["tmap"]:
                    blame.add(c.value.strip())
        if not blame:
            print("  cannot attribute the failures to a template - aborting, tree restored.")
            for w, diff in bad[:15]:
                for line in resolved_gate.describe(w, diff):
                    print("   " + line)
            restore(paths)
            return 1
        print("  excluding:", ", ".join(sorted(blame)))
        excluded |= blame
        restore(paths)
    print("did not converge in 6 passes - tree restored.")
    restore(paths)
    return 1


if __name__ == "__main__":
    sys.exit(main())
