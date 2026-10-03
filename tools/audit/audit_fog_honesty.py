#!/usr/bin/env python3
"""audit_fog_honesty — ratchet on global-actor-enumeration inside bot modules.

The acceptance contract (AI_ARCHITECTURE §0a, maintainer ruling 2026-09-28)
requires the candidate bot to fight WITHOUT map-wide vision. Nothing else
verifies that mechanically: a `World.Actors` scan in a targeting loop is an
omniscience leak whether or not anyone intended it.

This audit counts global-enumeration sites per bot-module source file and
compares them to a committed manifest
(tools/audit/fog_honesty_manifest.json):

  * a file's count INCREASING means a new unreviewed omniscience site — FAIL;
  * a count DECREASING is noted but does not fail (the manifest wants a
    deliberate `--write` so removals are recorded, not silent);
  * files in the Fransbot donor stack may not contain ANY unmanifested site —
    the donor is the fog-honest candidate in isolation.

What counts as a "site": `World.Actors`, `world.Actors`, `ActorsHavingTrait`,
`ActorsWithTrait` (missed until 2026-09-30: it sees every actor too), `ActorsInBox`, `FindActorsInCircle` on a World — enumerations that see every
actor regardless of shroud. Honest mechanisms (`Shroud.IsVisible`,
`CanBeViewedByPlayer`, `FrozenActor` memory, `Player.PlayerActor` scans) do not
match these patterns and are not counted. Sites inside `//` comments are
stripped before counting.

Second check (DESIGN §19.5, maintainer 2026-09-30): no module that can run for `genericbot` may switch a
visibility check off (`Check…Visibility: false`, `UseFoggedObservation: false`, `RespectShroud: false`) —
the allowed omniscient modules are `CaptureManagerBotModuleCA` (engineers route around the army to the
construction yard / tech centres) and `CratePickupBotModule` (a bot that lost its MCV finds a crate anywhere). `classic` is the omniscient A/B reference and is not checked.
`EngineerBotModule` (the ENG merge of the capture manager with the AS engineer module) is omniscient as a whole:
the maintainer ruled on 2026-09-30 that the engineer owner may see through fog for capture AND repair.

A count-only ratchet cannot tell "enumerating my own units" (honest — own
actors are always visible) from "enumerating enemy targets" (a cheat). It does
not try: the manifest freezes today's totals so any new site gets a human
review. Semantic review lives with the reviewer; the audit's job is to make
omniscience a deliberate act.

Third check (LC6): the runtime canaries — `CanaryObserved`/`CanaryObservedAll`
calls logging `FOGCANARY-VIOLATION` when a decision consumes an unseen actor —
are pinned per file by SITE NAME and count
(tools/audit/fog_canary_manifest.json). A name disappearing or its count
dropping means instrumentation was silently removed — FAIL. New sites or
higher counts are improvements the manifest only records after `--write`.

Usage:
  python tools/audit/audit_fog_honesty.py                # check
  python tools/audit/audit_fog_honesty.py --write        # re-baseline manifests
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = REPO / "tools" / "audit" / "fog_honesty_manifest.json"
CANARY_MANIFEST = REPO / "tools" / "audit" / "fog_canary_manifest.json"

# LC6 runtime canaries: a consumption point calls CanaryObserved(actor,
# "site-name")/CanaryObservedAll(list, "site-name") with a LITERAL site tag;
# the manifest pins each tag's count per file so a refactor cannot silently
# drop or rename instrumentation (the variable `site` inside CanaryObservedAll
# forwards — not a literal — and is not counted).
CANARY_SITE = re.compile(r'\bCanaryObserved(?:All)?\s*\([^,]+,\s*"([^"]+)"')

# Bot-module roots, relative to the repo. The engine copy is gitignored but
# present in built worktrees; a missing dir is skipped, not an error.
SCAN_ROOTS = [
    ("OpenRA.Mods.Fransbot/Traits", True),   # donor stack — strictest
    ("OpenRA.Mods.CA/Traits/BotModules", False),
    ("OpenRA.Mods.Cameo/Traits/BotModules", False),
    ("engine/OpenRA.Mods.Common/Traits/BotModules", False),
    ("engine/OpenRA.Mods.AS/Traits/BotModules", False),
]
# Cameo keeps bot traits at Traits/ root rather than BotModules/ — globbed.
SCAN_GLOBS = [
    ("OpenRA.Mods.Cameo/Traits", "*Bot*.cs"),
    ("OpenRA.Mods.Cameo/Traits", "Ai*Log*.cs"),
    ("OpenRA.Mods.Cameo/Traits", "AiSituation*.cs"),
    ("OpenRA.Mods.Cameo/Traits", "BeaconTracker.cs"),
]

PATTERNS = re.compile(
    r"\b(?:World|world)\.Actors\b"
    r"|\bActorsHavingTrait\b"
    r"|\bActorsWithTrait\b"
    r"|\bActorsInBox\b"
    r"|\bFindActorsInCircle\b"
    r"|\bWorld\.FindActorsInCircle\b"
)

LINE_COMMENT = re.compile(r"//.*$")


def iter_sources():
    seen = set()
    for rel, strict in SCAN_ROOTS:
        root = REPO / rel
        if not root.is_dir():
            continue
        for cs in sorted(root.rglob("*.cs")):
            relname = cs.relative_to(REPO).as_posix()
            if relname in seen:
                continue
            seen.add(relname)
            yield relname, strict
    for dirname, pattern in SCAN_GLOBS:
        root = REPO / dirname
        if not root.is_dir():
            continue
        for cs in sorted(root.glob(pattern)):
            relname = cs.relative_to(REPO).as_posix()
            if relname not in seen:
                seen.add(relname)
                yield relname, False


def count_sites(path: pathlib.Path) -> int:
    count = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        code = LINE_COMMENT.sub("", line)
        count += len(PATTERNS.findall(code))
    return count


def canary_sites(path: pathlib.Path) -> dict[str, int]:
    sites: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        code = LINE_COMMENT.sub("", line)
        for m in CANARY_SITE.finditer(code):
            sites[m.group(1)] = sites.get(m.group(1), 0) + 1
    return sites


# DESIGN §19.5 (maintainer 2026-09-30): the only modules of the Frankenstein bot allowed to see through fog —
# engineers routing around the army to capture, and crate pickup for a bot that lost its MCV.
# module -> the visibility switches it may turn off (None = any). DESIGN §19.5; the engineer owner is omniscient
# as a whole (maintainer 2026-09-30), so the ENG merge inherits the capture manager's exception whole.
ALLOWED_OMNISCIENT: dict[str, set[str] | None] = {
    "CaptureManagerBotModuleCA": None,
    "EngineerBotModule": None,
    "CratePickupBotModule": None,
}
VISIBILITY_SWITCH = re.compile(r"^(Check\w*Visibility|UseFoggedObservation|RespectShroud)$")
IDENT = re.compile(r"[A-Za-z_][\w\-.]*")

# A support-power decision carrying IgnoreVisibility: true strikes enemies the
# bot has never seen (engine-side SupportPowerBotASModule does
# `IgnoreVisibility || CanBeViewedByPlayer` over all IOccupySpace actors).
# §19.5's two sanctioned exceptions do not cover this class. The resolved
# Player carried 56 such decisions; RV2 (AI_MASTER_PLAN §3) flipped the 28
# genericbot-shared ones to seen/remembered-only — classic is unaffected at
# runtime because its RevealsMap leaves nothing invisible. The remaining 28
# live outside the merged AS block. A NEW invisible-strike decision fails
# the audit, removing one is free. (NOVA VERIFY_2026-09-30 finding 1; flip
# ruled by the maintainer-documented RV2 row.)
IGNORE_VISIBILITY_ENEMY_BASELINE = 28


def condition_active(expr: str, granted: set[str], known: set[str]) -> bool:
    """Can `expr` hold for a bot granted `granted`? Conditions no bot grants (prerequisites, personalities)
    count as possibly true, so the check errs toward flagging."""
    if not expr.strip():
        return True
    py = IDENT.sub(lambda m: "True" if m.group(0) in granted or m.group(0) not in known else "False", expr)
    py = py.replace("&&", " and ").replace("||", " or ").replace("!", " not ")
    return bool(eval(py, {"__builtins__": {}}))


def visibility_switch_failures() -> list[str]:
    """A genericbot module that turns a visibility check off (DESIGN §19.5) — only the capture manager may."""
    sys.path.insert(0, str(REPO / "tools" / "audit"))
    import miniyaml  # noqa: E402

    player = miniyaml.Ruleset(REPO).resolve("Player")
    if player is None:
        return ["Player actor does not resolve"]
    bots: dict[str, set[str]] = {}
    for c in player.children:
        if c.key.split("@", 1)[0] == "GrantConditionOnBotOwner":
            for b in (c.get("Bots") or "").split(","):
                bots.setdefault(b.strip(), set()).add(c.get("Condition") or "")
    known = set().union(*bots.values()) if bots else set()
    frankenstein = [conds for conds in bots.values() if "genericbot" in conds]

    failures = []
    for c in player.children:
        base = c.key.split("@", 1)[0]
        allowed = ALLOWED_OMNISCIENT.get(base, set())
        if c.key.startswith("-") or allowed is None:
            continue
        switches = [k for k in c.children if VISIBILITY_SWITCH.match(k.key)
                    and k.value.strip().lower() == "false" and k.key not in allowed]
        if not switches:
            continue
        expr = c.get("RequiresCondition") or ""
        if any(condition_active(expr, conds, known) for conds in frankenstein):
            for k in switches:
                failures.append(f"Player.{c.key}: {k.key}: false reaches genericbot ({expr or 'no condition'}) — "
                                f"only {', '.join(sorted(ALLOWED_OMNISCIENT))} may see through fog (DESIGN §19.5)")
    return failures


def count_ignore_visibility_enemy() -> int | None:
    """Resolved-Player count of IgnoreVisibility: true decisions whose
    Consideration targets Enemy. None when Player does not resolve."""
    sys.path.insert(0, str(REPO / "tools" / "audit"))
    import miniyaml  # noqa: E402

    player = miniyaml.Ruleset(REPO).resolve("Player")
    if player is None:
        return None

    hits = 0
    stack = list(player.children)
    while stack:
        node = stack.pop()
        iv = node.get("IgnoreVisibility")
        if isinstance(iv, str) and iv.strip().lower() == "true":
            if any(c.key.startswith("Consideration")
                   and isinstance(c.get("Against"), str)
                   and c.get("Against").strip().lower() == "enemy"
                   for c in node.children):
                hits += 1
        stack.extend(node.children)
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="re-baseline the manifest")
    args = ap.parse_args()

    current: dict[str, int] = {}
    canary_current: dict[str, dict[str, int]] = {}
    strict_files: set[str] = set()
    for rel, strict in iter_sources():
        n = count_sites(REPO / rel)
        if n:
            current[rel] = n
        canary = canary_sites(REPO / rel)
        if canary:
            canary_current[rel] = canary
        if strict:
            strict_files.add(rel)

    if args.write:
        MANIFEST.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        CANARY_MANIFEST.write_text(json.dumps(canary_current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {MANIFEST.name}: {len(current)} files, {sum(current.values())} sites")
        print(f"wrote {CANARY_MANIFEST.name}: {len(canary_current)} files, "
              f"{sum(sum(f.values()) for f in canary_current.values())} canary sites")
        return 0

    if not MANIFEST.is_file():
        print(f"FAIL: manifest missing ({MANIFEST}) — run with --write to seed it")
        return 1
    baseline = json.loads(MANIFEST.read_text(encoding="utf-8"))

    failures: list[str] = []
    notes: list[str] = []
    switch_failures = visibility_switch_failures()
    iv_count = count_ignore_visibility_enemy()
    if iv_count is None:
        switch_failures.append("Player actor does not resolve — IgnoreVisibility ratchet cannot run")
    elif iv_count > IGNORE_VISIBILITY_ENEMY_BASELINE:
        switch_failures.append(
            f"{iv_count} IgnoreVisibility(enemy) support-power decisions "
            f"(baseline {IGNORE_VISIBILITY_ENEMY_BASELINE}) — new invisible strikes need a §19.5 maintainer ruling")
    elif iv_count < IGNORE_VISIBILITY_ENEMY_BASELINE:
        notes.append(f"IgnoreVisibility(enemy) decisions: {IGNORE_VISIBILITY_ENEMY_BASELINE} -> "
                     f"{iv_count} (fewer invisible strikes — lower the baseline)")
    for rel, n in sorted(current.items()):
        base = baseline.get(rel)
        if base is None:
            kind = "NEW FILE (fransbot stack — no unmanifested sites allowed)" if rel in strict_files else "NEW FILE"
            if n > 0:
                failures.append(f"{rel}: {n} enumeration site(s), none manifested - {kind}")
        elif n > base:
            failures.append(f"{rel}: {base} -> {n} (+{n - base}) enumeration site(s) added - review for fog honesty")
        elif n < base:
            notes.append(f"{rel}: {base} -> {n} (sites removed - refresh manifest with --write)")
    for rel in baseline:
        if rel not in current:
            notes.append(f"{rel}: manifest entry stale (file gone or clean) - refresh with --write")

    # LC6 canary ratchet: every manifested site name must still exist with at
    # least its recorded call count — a vanished tag is coverage silently lost.
    if not CANARY_MANIFEST.is_file():
        failures.append(f"canary manifest missing ({CANARY_MANIFEST}) — run with --write to seed it")
    else:
        canary_baseline = json.loads(CANARY_MANIFEST.read_text(encoding="utf-8"))
        for rel, sites in sorted(canary_baseline.items()):
            got = canary_current.get(rel, {})
            for site, n in sites.items():
                if site not in got:
                    failures.append(f"{rel}: canary site \"{site}\" removed ({n} call(s) manifested)")
                elif got[site] < n:
                    failures.append(f"{rel}: canary site \"{site}\" {n} -> {got[site]} call(s) — coverage dropped")
                elif got[site] > n:
                    notes.append(f"{rel}: canary site \"{site}\" {n} -> {got[site]} call(s) — refresh with --write")
            for site in sorted(set(got) - set(sites)):
                notes.append(f"{rel}: new canary site \"{site}\" ({got[site]} call(s)) — refresh with --write")
        for rel in sorted(set(canary_current) - set(canary_baseline)):
            for site, n in sorted(canary_current[rel].items()):
                notes.append(f"{rel}: new canary site \"{site}\" ({n} call(s)) — refresh with --write")

    for note in notes:
        print(f"  note: {note}")
    for f in switch_failures:
        print(f"FAIL: {f}")
    if switch_failures and not failures:
        print(f"{len(switch_failures)} Frankenstein module(s) switch a visibility check off")
        return 1
    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        print(f"{len(failures)} file(s) gained unreviewed global-actor enumeration")
        return 1
    print(f"PASS: {len(current)} files, {sum(current.values())} manifested enumeration sites, no new omniscience")
    return 0


if __name__ == "__main__":
    sys.exit(main())
