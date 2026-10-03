#!/usr/bin/env python3
"""audit_bot_direct_mutation — multiplayer-desync ratchet on bot modules.

A bot runs on the host alone and may touch actors ONLY through orders —
the order stream is what every client simulates. A direct
`actor.CancelActivity()`, `actor.QueueActivity(...)`, or a trait-level
`autoTarget.SetStance(actor, ...)` inside a bot module bypasses the order
gate's issuer/lease accounting (DESIGN §19.6) AND desyncs
a multiplayer game — the synchronized paths are `Order("Stop")` /
`Order("Move"...)` / `Order("SetUnitStance")`. The INC-3b review found 94
`CancelActivity`, 5 `QueueActivity` and 8 `SetStance` leftovers in the
vendored Fransbot stack; this audit pins the count at zero so the pattern
cannot creep back in.

Scanned (must stay at ZERO calls, `//` comments excluded):

  * `OpenRA.Mods.Fransbot/Traits/**`      — the vendored donor stack
  * `OpenRA.Mods.CA/Traits/BotModules/**`
  * `OpenRA.Mods.Cameo/Traits/BotModules/**` and `*Bot*.cs` at Traits/ root

Not scanned on purpose: `engine/` (upstream order-resolution traits legitimately
call CancelActivity while *implementing* orders — that is the engine's job) and
non-bot traits elsewhere in the mod (spawner/deploy traits own their actor's
activity directly; they are not bot logic). If a bot module ever NEEDS a
direct call, add the file to ALLOWLIST below with a maintainer-visible reason —
like the fog-honesty manifest, an exception must be a deliberate act.

Usage:
  python tools/audit/audit_bot_direct_mutation.py
"""

from __future__ import annotations

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]

SCAN_DIRS = [
    "OpenRA.Mods.Fransbot/Traits",
    "OpenRA.Mods.CA/Traits/BotModules",
    "OpenRA.Mods.Cameo/Traits/BotModules",
]
SCAN_GLOBS = [
    ("OpenRA.Mods.Cameo/Traits", "*Bot*.cs"),
]

PATTERN = re.compile(r"\.(?:CancelActivity|QueueActivity|SetStance)\s*\(")
LINE_COMMENT = re.compile(r"//.*$")

# Deliberate exceptions — {repo-relative path: (max_sites, reason)}. Empty today.
ALLOWLIST: dict[str, tuple[int, str]] = {}


def iter_sources():
    seen: set[str] = set()
    for rel in SCAN_DIRS:
        root = REPO / rel
        if not root.is_dir():
            continue
        for cs in sorted(root.rglob("*.cs")):
            relname = cs.relative_to(REPO).as_posix()
            if relname not in seen:
                seen.add(relname)
                yield relname, cs
    for dirname, pattern in SCAN_GLOBS:
        root = REPO / dirname
        if not root.is_dir():
            continue
        for cs in sorted(root.glob(pattern)):
            relname = cs.relative_to(REPO).as_posix()
            if relname not in seen:
                seen.add(relname)
                yield relname, cs


def find_sites(path: pathlib.Path):
    for lineno, line in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
    ):
        code = LINE_COMMENT.sub("", line)
        for m in PATTERN.finditer(code):
            yield lineno, m.group(0), line.strip()


def main() -> int:
    failures: list[str] = []
    scanned = 0
    for relname, path in iter_sources():
        scanned += 1
        sites = list(find_sites(path))
        allowed, _reason = ALLOWLIST.get(relname, (0, ""))
        for lineno, call, text in sites[: allowed]:
            pass  # within the allowlisted count
        for lineno, call, text in sites[allowed:]:
            failures.append(f"{relname}:{lineno}: `{text}`")

    print("# audit_bot_direct_mutation")
    print()
    print(f"Scanned {scanned} bot-module source files for direct actor "
          "`CancelActivity`/`QueueActivity`/`SetStance` calls.")
    print()
    if not failures:
        print("PASS — zero direct-activity sites. Bots drive actors exclusively "
              "through the order stream; multiplayer stays in sync and the "
              "order gate (§19.6) sees every issuer/lease pairing.")
        return 0

    print(f"FAIL — {len(failures)} direct-activity site(s) in bot modules "
          "(bots run on the host alone; these desync multiplayer and evade "
          "the order gate):")
    print()
    for f in failures:
        print(f"- {f}")
    print()
    print("Convert to `bot.QueueOrder(new Order(\"Stop\", actor, false))` / "
          "`\"Move\"` orders (see QueueStopOrder/QueueMoveOrder in the Fransbot "
          "commander modules). A genuinely trait-internal exception belongs in "
          "this audit's ALLOWLIST with a reason.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
