#!/usr/bin/env python3
"""audit_central_ids — the §2.8 progress metric as a LOWER-ONLY ratchet.

AI_ARCHITECTURE.md §2.8: faction actor ids leave the central mods/cameo/ai/ai.yaml (dictionary rows
into their ContentPacks, lists into roles on the actors) until the count is 0. Nothing watched it,
and it rose 4,092 -> 5,825 in two days: every new personality block copied ~600 list ids
(`@classic` +580, `@guerrilla` +644). This fails when the count rises above CEILING.

When a change LOWERS the count, lower CEILING to the new value in the same commit.
Never raise it: add a role (BotRoleSets) or a pack row instead of a central id.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "ai" / "count_central_ids.py"
CEILING = 4289  # 2026-09-29: the guerrilla role applied (5,825 -> 4,289)


def main() -> int:
    print("# Central ai.yaml actor ids — lower-only ratchet (AI_ARCHITECTURE §2.8)\n")
    r = subprocess.run([sys.executable, str(TOOL), "--max", str(CEILING)], capture_output=True, text=True, cwd=REPO)
    print(r.stdout.strip() or "(no output)")
    print(f"\nceiling: {CEILING}")
    if r.returncode != 0:
        print(r.stderr.strip())
        print("\nFAIL — the central file gained actor ids. Use a role on the actors (BotRoleSets) or a pack row.")
        return 1
    print("\nPASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
