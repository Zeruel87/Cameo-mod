"""Generated AI architecture evidence must match the tree it describes.

`docs/design/AI_MODULE_MAP.md` and `docs/design/AI_ARCH_COVERAGE.md` are generated
artifacts (their headers say "do not edit by hand; regenerate"). When C# AI traits,
yaml module instances or the seam surface change without regenerating them, the
committed map silently describes an older architecture — the post-merge review of
2026-10-02 (Codex finding P0-3.1) caught exactly that: the map predated several
types and seams that evening's merges had added, so drift-checking evidence was
itself drifting.

This audit gates on the two generators' own `--check` modes:

  python tools/audit/audit_ai_arch_freshness.py         # check (this audit)
  python tools/ai/ai_module_map.py --write              # regenerate the map
  python tools/ai/ai_arch_audit.py --write              # regenerate the coverage doc
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]

CHECKS = [
    ("AI_MODULE_MAP.md", [sys.executable, "tools/ai/ai_module_map.py", "--check"]),
    ("AI_ARCH_COVERAGE.md", [sys.executable, "tools/ai/ai_arch_audit.py", "--check"]),
]


def main() -> int:
    rows = []
    failed = 0
    for name, cmd in CHECKS:
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
        stale = proc.returncode != 0
        failed |= stale
        detail = ""
        if stale:
            first = next((ln for ln in proc.stdout.splitlines() if ln.startswith("STALE")), "")
            err = proc.stderr.strip().splitlines()
            detail = first or (err[-1] if err else f"exit {proc.returncode}")
            rows.append(f"| {name} | **FAIL** | {detail}; run the tool with `--write` |")
        else:
            rows.append(f"| {name} | PASS | generated file matches the tree |")

    print("# AI architecture freshness\n")
    print("| artifact | result | detail |")
    print("|---|---|---|")
    print("\n".join(rows))
    if failed:
        print("\n**Regenerate on the merged tree, not on an earlier branch baseline.**")
    return failed


if __name__ == "__main__":
    sys.exit(main())
