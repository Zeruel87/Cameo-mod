#!/usr/bin/env python3
"""audit_plating_exclusivity.py — no actor may ever wear two armor platings at once.

Maintainer, 2026-08-16: *"armor platings MUST be mutually exclusive like they
currently are for RA2 but team upgrades should still be able to add extra armor on
top which just increases the armor total amount but not the armor type!"*

Two rules, and this file checks both:

  **X1 — TWO PLATINGS MUST BE GATED APART.** A plating REPLACES the class armor
  (`AreaDamageWarhead.DamageVersus` selects it), so two ACTIVE platings mean two candidate
  rows for one hit. The C# takes the most protective, which is safe but is a BACKSTOP, not
  a design.

  ⚠ **Carrying two plating TRAITS is normal and correct** — that was the first version of
  this check and it was wrong. 32 actors carry both Soviet doctrine platings, or both
  Allied ones, precisely so the unit benefits from whichever branch the player picked. What
  must be impossible is both CONDITIONS being true, and RA2 enforces that with
  `ProductionIconMutualExclusion: Group` plus a `!<sibling>` prerequisite on each branch.

  So the real test is: every plating an actor can reach must come from an upgrade sharing
  one exclusion GROUP. Two platings from different groups (or from an upgrade with no group
  at all) can stack, and then the tie-break silently decides the matchup.

  **X2 — A PLATING IS A TYPE, NOT AN AMOUNT.** An upgrade that grants a plating must not
  also carry a large flat `DamageMultiplier`: the two compound (`0.85 x 0.70 = 0.595`, a
  40% cut where the branch intended 15%). Team/tech upgrades are the opposite case and
  are FINE — they carry a multiplier and no armor type, which is exactly the maintainer's
  "adds the amount, not the type".
"""
from __future__ import annotations

import pathlib
import re
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
sys.path.insert(0, str(ROOT / "tools" / "audit"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import gen_weapon_template as _gen  # noqa: E402

PLATINGS = set(_gen.PLATING_CYCLE)
# Above this, a flat modifier stacked on a plating is double-dipping rather than flavour.
MULTIPLIER_FLOOR = 90

TRAIT = re.compile(r"^\t(\w+)(?:@[\w.]+)?:")


def scan():
    """{template or actor: [(plating, condition)]} and {name: [(modifier, condition)]}."""
    platings: dict[str, list[tuple[str, str]]] = defaultdict(list)
    mults: dict[str, list[tuple[int, str]]] = defaultdict(list)
    # ⚠ LIVE files only, from mod.yaml's Rules list. Globbing `mods/cameo/**/*.yaml`
    # looked equivalent and was not: `rules/redalert2.yaml` and its siblings are DEAD
    # copies kept on disk ("now loaded via include-only wrapper packs ... not loaded here
    # to avoid duplicate keys" — mod.yaml:176), and scanning them reported a stale flat
    # multiplier on a template whose live copy had already been retagged. A dead file is
    # not evidence about what ships.
    from miniyaml import Ruleset  # noqa: PLC0415
    for path in Ruleset(ROOT).manifest.rules:
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
        owner = None
        for i, line in enumerate(lines):
            if line and not line[0].isspace() and line.rstrip().endswith(":"):
                owner = line.rstrip()[:-1]
                continue
            m = TRAIT.match(line)
            if not m or owner is None:
                continue
            trait = m.group(1)
            if trait not in ("Armor", "DamageMultiplier"):
                continue
            kind = cond = None
            j = i + 1
            while j < len(lines) and lines[j].startswith("\t\t"):
                t = lines[j].strip()
                if t.startswith("Type:"):
                    kind = t.split(":", 1)[1].strip()
                elif t.startswith("Modifier:"):
                    kind = t.split(":", 1)[1].strip()
                elif t.startswith("RequiresCondition:"):
                    cond = t.split(":", 1)[1].strip()
                j += 1
            if trait == "Armor" and kind in PLATINGS:
                platings[owner].append((kind, cond or "<unconditional>"))
            elif trait == "DamageMultiplier" and kind and cond:
                try:
                    mults[owner].append((int(kind), cond))
                except ValueError:
                    pass
    return platings, mults


def exclusion_groups():
    """upgrade-actor name -> its ProductionIconMutualExclusion group (or None)."""
    from miniyaml import Ruleset  # noqa: PLC0415
    out: dict[str, str | None] = {}
    for path in Ruleset(ROOT).manifest.rules:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        owner = None
        in_excl = False
        for line in lines:
            if line and not line[0].isspace() and line.rstrip().endswith(":"):
                owner = line.rstrip()[:-1]
                in_excl = False
                continue
            if owner is None:
                continue
            if TRAIT.match(line):
                in_excl = line.strip().startswith("ProductionIconMutualExclusion")
                continue
            if in_excl and line.strip().startswith("Group:"):
                out[owner] = line.split(":", 1)[1].strip()
    return out


_IDENT = re.compile(r"(!?)\s*([A-Za-z_][\w\-.]*)")


def gated_apart(c1: str, c2: str) -> bool:
    """True when the two plating conditions can never hold together: one is a PURE conjunction
    (no `||`) that negates a positive term of the other — e.g. `hazmatsuits && !cyberneticarmor_up`
    against `cyberneticarmor_up && !shielded`. A condition gate is as sound as a shared
    ProductionIconMutualExclusion group; anything with `||` is not provably exclusive."""
    def terms(c):
        pos = {m.group(2) for m in _IDENT.finditer(c) if not m.group(1)}
        neg = {m.group(2) for m in _IDENT.finditer(c) if m.group(1)}
        return pos, neg
    p1, n1 = terms(c1)
    p2, n2 = terms(c2)
    return ("||" not in c1 and bool(n1 & p2)) or ("||" not in c2 and bool(n2 & p1))


def actor_platings():
    """concrete actor -> {plating: condition}, resolved transitively through Inherits."""
    from cameo_model import Model  # noqa: PLC0415
    actors = Model().rs.actors

    def parents(node):
        return [str(c.value).strip() for c in node.children
                if c.key.split("@")[0] == "Inherits" and c.value]

    cache: dict[str, dict[str, str]] = {}

    def walk(name, depth=0):
        if name in cache:
            return cache[name]
        node = actors.get(name)
        if node is None or depth > 25:
            return {}
        found: dict[str, str] = {}
        for c in node.children:
            if c.key.split("@")[0] != "Armor":
                continue
            kind = cond = None
            for g in c.children:
                if g.key == "Type":
                    kind = str(g.value).strip()
                elif g.key == "RequiresCondition":
                    cond = str(g.value).strip()
            if kind in PLATINGS:
                found[kind] = cond or "<unconditional>"
        for p in parents(node):
            for k, v in walk(p, depth + 1).items():
                found.setdefault(k, v)
        cache[name] = found
        return found

    return {n: walk(n) for n in actors if not n.startswith("^")}


def main() -> int:
    platings, mults = scan()
    failed = 0

    print("# audit_plating_exclusivity — one plating per actor, and a plating is a TYPE")
    print()
    print(f"Found **{sum(len(v) for v in platings.values())}** plating grant(s) across "
          f"**{len(platings)}** definition(s), over the "
          f"{len(PLATINGS)} platings ({', '.join(sorted(PLATINGS))}).")
    print()

    print("## X1 — every actor's platings must be gated apart")
    print()
    groups = exclusion_groups()
    per_actor = actor_platings()
    multi = {n: v for n, v in per_actor.items() if len(v) > 1}
    leaks = []
    for name, got in multi.items():
        gs = {groups.get(cond) for cond in got.values()}
        # A PAIR leaks unless its upgrades share one exclusion group, or its conditions are
        # gated apart (`!other` in a pure conjunction) — either makes both-active impossible.
        conds = list(got.values())
        pair_leak = any(
            not (groups.get(a) is not None and groups.get(a) == groups.get(b))
            and not gated_apart(a, b)
            for i, a in enumerate(conds) for b in conds[i + 1:])
        if pair_leak:
            leaks.append((name, got, gs))
    print(f"{len(multi)} actor(s) can reach more than one plating — normal, as long as one "
          f"exclusion group covers them all.")
    print()
    if leaks:
        failed = 1
        print(f"**FAIL — {len(leaks)} actor(s) can wear two platings at once.**")
        print()
        print("| actor | platings | exclusion groups |")
        print("|---|---|---|")
        for name, got, gs in sorted(leaks)[:30]:
            print(f"| `{name}` | {', '.join(sorted(got))} | "
                  + ", ".join(str(g) for g in sorted(gs, key=str)) + " |")
        if len(leaks) > 30:
            print()
            print(f"_... and {len(leaks) - 30} more._")
    else:
        print("_clean_ — every multi-plating actor's platings are gated apart (one exclusion "
              "group, or a `!condition` gate).")
    print()

    print("## X2 — a plating is a type, not an amount")
    print()
    bad = []
    for n, v in platings.items():
        for mod, cond in mults.get(n, []):
            if mod < MULTIPLIER_FLOOR and any(c == cond for _p, c in v):
                bad.append((n, mod, cond))
    if bad:
        failed = 1
        print(f"**FAIL — {len(bad)} plating(s) stacked with a large flat multiplier.**")
        print()
        print("| definition | Modifier | condition | combined |")
        print("|---|--:|---|--:|")
        for n, mod, cond in sorted(bad):
            print(f"| `{n}` | {mod} | `{cond}` | "
                  f"{mod * _gen.PLATING_TARGET_MEAN / 100:.0f}% |")
        print()
        print(f"The plating already averages {_gen.PLATING_TARGET_MEAN:g}%; a modifier "
              f"below {MULTIPLIER_FLOOR} compounds with it. Keep the small overall bonus "
              f"or the multiplier, not both.")
    else:
        print(f"_clean_ — no plating is stacked with a modifier below {MULTIPLIER_FLOOR}.")
    print()

    if platings:
        print("## The plating layer as it ships")
        print()
        print("| definition | plating | condition |")
        print("|---|---|---|")
        for n, v in sorted(platings.items()):
            for p, c in sorted(v):
                print(f"| `{n}` | **{p}** | `{c}` |")
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
