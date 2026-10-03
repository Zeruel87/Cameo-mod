#!/usr/bin/env python3
"""audit_fransbot_lists — drift guard for mods/cameo/ai/fransbot_lists.yaml.

The generated file fills the Fransbot modules' [ActorReference] list fields with
actor ids derived from resolved ruleset traits (tools/ai/gen_fransbot_lists.py).
If actor rules change without a regenerate, the lists go stale silently — this
audit reruns the generator in --check mode and FAILS when the committed file
does not match a fresh generate.

Fix: python tools/ai/gen_fransbot_lists.py   (then boot-gate, then commit)
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
GEN = REPO / "tools" / "ai" / "gen_fransbot_lists.py"
OUT = REPO / "mods" / "cameo" / "ai" / "fransbot_lists.yaml"


def main() -> int:
    print("# Fransbot generated lists — drift check\n")
    if not GEN.exists():
        print(f"FAIL: generator missing: {GEN.relative_to(REPO)}")
        return 1
    if not OUT.exists():
        print(f"FAIL: generated file missing: {OUT.relative_to(REPO)}")
        print("Fix: run `python tools/ai/gen_fransbot_lists.py`")
        return 1
    r = subprocess.run([sys.executable, str(GEN), "--check"],
                       capture_output=True, text=True, cwd=REPO)
    print(r.stdout.strip() or "(no output)")
    if r.returncode != 0:
        print(r.stderr.strip())
        print("\nFAIL — regenerate with `python tools/ai/gen_fransbot_lists.py`")
        return 1
    print("\nPASS — generated file matches the resolved ruleset")
    return 0


if __name__ == "__main__":
    sys.exit(main())
