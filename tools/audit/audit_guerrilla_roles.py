#!/usr/bin/env python3
"""audit_guerrilla_roles — drift guard for the generated `guerrilla` BotRoles on the actors.

tools/ai/derive_guerrilla_roles.py writes `BotRoles: Roles: guerrilla` on every actor in the ruled
band (AI_ARCHITECTURE.md §2.8a: the fastest third of its faction's infantry or vehicles, costing at
most the median). A new unit, a speed or cost change, or a template change moves the band; without
a regenerate the tags go stale silently. This reruns the generator in --check mode and FAILS when
any actor's RESOLVED roles disagree with a fresh band (a missing tag, a stale one, or one inherited
from a parent actor).

Fix: python tools/ai/derive_guerrilla_roles.py --write   (then boot-gate, then commit)
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
GEN = REPO / "tools" / "ai" / "derive_guerrilla_roles.py"


def main() -> int:
    print("# Guerrilla bot role — drift check\n")
    if not GEN.exists():
        print(f"FAIL: generator missing: {GEN.relative_to(REPO)}")
        return 1
    r = subprocess.run([sys.executable, str(GEN), "--check"], capture_output=True, text=True, cwd=REPO)
    print(r.stdout.strip() or "(no output)")
    if r.returncode != 0:
        print(r.stderr.strip())
        print("\nFAIL — regenerate with `python tools/ai/derive_guerrilla_roles.py --write`")
        return 1
    print("\nPASS — every actor's guerrilla role matches the ruled band")
    return 0


if __name__ == "__main__":
    sys.exit(main())
