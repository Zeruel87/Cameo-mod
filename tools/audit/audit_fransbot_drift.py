#!/usr/bin/env python3
"""audit_fransbot_drift — vendored-source drift guard for OpenRA.Mods.Fransbot.

The Route-A port vendored 29 files from upstream Fransbot
(github.com/OpenRA-Fransbot @ 9150ded, "V1.29.48 — Native Amphibious
Handoffs + Ferry Liveness") into OpenRA.Mods.Fransbot/Traits/. Every local
delta is deliberate (RA-id list empties, validator relaxes, engine-API
drift fixes, fog fixes, order-gate conversion). This audit
diffs the vendored files against the upstream clone and FAILS when:

  * a vendored file is added or dropped without re-baselining, or
  * a file's per-file added/removed line counts vs upstream move away from
    the recorded baseline (someone edited vendored code silently).

Baseline: tools/ai/fransbot_drift_baseline.json  (committed)
Upstream location: --upstream PATH, or env FRANSBOT_UPSTREAM, or
<repo-parent>/OpenRA-Fransbot.

Usage:
  python tools/audit/audit_fransbot_drift.py             # check vs baseline
  python tools/audit/audit_fransbot_drift.py --write-baseline
  python tools/audit/audit_fransbot_drift.py --upstream D:/path/to/OpenRA-Fransbot
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
VENDORED = REPO / "OpenRA.Mods.Fransbot" / "Traits"
BASELINE = REPO / "tools" / "ai" / "fransbot_drift_baseline.json"
UPSTREAM_SUBDIR = pathlib.Path("src") / "Fransbot.OpenRA" / "Traits"
UPSTREAM_REF = "9150ded (V1.29.48, 'Native Amphibious Handoffs + Ferry Liveness')"


def find_upstream(arg: str | None) -> pathlib.Path | None:
    cands = []
    if arg:
        cands.append(pathlib.Path(arg))
    env = os.environ.get("FRANSBOT_UPSTREAM")
    if env:
        cands.append(pathlib.Path(env))
    cands.append(REPO.parent / "OpenRA-Fransbot")
    cands.append(pathlib.Path.home() / "Documents" / "GitHub" / "OpenRA-Fransbot")
    for c in cands:
        if (c / UPSTREAM_SUBDIR).is_dir():
            return c / UPSTREAM_SUBDIR
        if c.name == "Traits" and c.is_dir():
            return c
    return None


def diff_counts(vendored: pathlib.Path, upstream: pathlib.Path) -> dict[str, list[int]]:
    """Per-file [added, removed] unified-diff body line counts (context excluded)."""
    out: dict[str, list[int]] = {}
    up_files = {p.name: p for p in upstream.glob("*.cs")}
    for vf in sorted(VENDORED.glob("*.cs")):
        uf = up_files.get(vf.name)
        if uf is None:
            out[vf.name] = [-1, -1]
            continue
        a = vf.read_text(encoding="utf-8", errors="replace").splitlines()
        b = uf.read_text(encoding="utf-8", errors="replace").splitlines()
        add = rem = 0
        for line in difflib.unified_diff(b, a, lineterm="", n=0):
            if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
                continue
            if line.startswith("+"):
                add += 1
            elif line.startswith("-"):
                rem += 1
        out[vf.name] = [add, rem]
    for name in sorted(up_files):
        if name not in out and not (VENDORED / name).exists():
            out[f"+{name}"] = [-2, -2]  # upstream-only file, not vendored
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", help="path to the OpenRA-Fransbot clone (or its Traits dir)")
    ap.add_argument("--check", action="store_true", help="default: compare vs baseline")
    ap.add_argument("--write-baseline", action="store_true")
    args = ap.parse_args()

    print("# Fransbot vendored-source drift check\n")
    upstream = find_upstream(args.upstream)
    if upstream is None:
        print("SKIP: upstream clone not found (set FRANSBOT_UPSTREAM or --upstream).")
        print("Expected src/Fransbot.OpenRA/Traits under a sibling OpenRA-Fransbot clone.")
        return 0
    print(f"Upstream: {upstream}  (base ref {UPSTREAM_REF})\n")

    counts = diff_counts(VENDORED, upstream)
    vendored_names = sorted(p.name for p in VENDORED.glob("*.cs"))
    print(f"Vendored files: {len(vendored_names)}")

    if args.write_baseline:
        BASELINE.write_text(json.dumps(
            {"upstream_ref": UPSTREAM_REF, "files": counts}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        print(f"\nBaseline written: {BASELINE.relative_to(REPO)}")
        return 0

    if not BASELINE.exists():
        print("\nFAIL: no baseline. Run with --write-baseline against the vendored upstream ref.")
        return 1

    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    bfiles: dict = base.get("files", {})
    problems: list[str] = []
    for name, cnt in sorted(counts.items()):
        b = bfiles.get(name)
        if b is None:
            problems.append(f"{name}: not in baseline ({'upstream-only' if cnt[0] == -2 else 'new vendored file' if cnt[0] == -1 else 'baseline gap'})")
        elif cnt != b:
            problems.append(f"{name}: diff vs upstream moved {b} -> {cnt} (+added/-removed lines)")
    for name in sorted(set(bfiles) - set(counts)):
        problems.append(f"{name}: in baseline but missing from vendored tree")

    if problems:
        print("\nFAIL — vendored deltas changed since baseline:")
        for p in problems:
            print(f"  - {p}")
        print("\nIf the change is intentional (new port fix or upstream re-vendor),")
        print("re-run with --write-baseline and commit the baseline with the code.")
        return 1

    total_add = sum(c[0] for c in counts.values() if c[0] > 0)
    total_rem = sum(c[1] for c in counts.values() if c[1] > 0)
    print(f"Per-file deltas vs upstream: +{total_add}/-{total_rem} lines — all match baseline")
    print("\nPASS — vendored set and per-file deltas unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
