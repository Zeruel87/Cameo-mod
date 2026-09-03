#!/usr/bin/env python3
"""audit_engine_freshness — how far Cameo's engine has fallen behind the upstreams it tracks.

Cameo's engine is a fork of `MustaphaTR/OpenRA` branch `rv-engine`, which is itself a fork of
`OpenRA/OpenRA` branch `bleed`. Both keep moving, and nothing in the tree makes that visible:
`mod.config` pins one 40-char hash and says nothing about what has landed upstream since. This
audit turns "are we behind?" into one number per upstream.

It reads the SEPARATE `cameo-engine` clone (see docs/LESSONS_LEARNED.md, "The canonical engine
update pipeline") — never `engine/`, which is a gitignored build output with no `.git` of its own.

⚠ It does NOT fetch. It measures against whatever refs that clone already has, and prints the
date of each ref so a stale answer is obvious rather than silently wrong. Refresh with:

    git -C <clone> fetch upstream mtr --no-tags

INFORMATIONAL — it never fails a build. Moving the engine is a maintainer decision and a
multi-step pipeline (edit the clone -> push -> set ENGINE_VERSION in mod.config -> make.cmd all
-> recreate engine/glsl shaders -> boot-gate), never something a green audit should imply.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):          # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]

# (label, ref in the clone, what it is)
UPSTREAMS = [
    ("OpenRA bleed", "upstream/bleed", "the engine everything descends from"),
    ("MustaphaTR rv-engine", "mtr/rv-engine", "our direct parent branch; Generals Alpha pins its tip"),
]


def find_clone() -> pathlib.Path | None:
    for c in (os.environ.get("CAMEO_ENGINE_ROOT"),
              ROOT.parent / "cameo-engine",
              pathlib.Path.home() / "Documents" / "GitHub" / "cameo-engine"):
        if c and (pathlib.Path(c).expanduser() / ".git").is_dir():
            return pathlib.Path(c).expanduser()
    return None


def git(clone: pathlib.Path, *args: str) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(clone), *args],
                             capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    # strip("\n") only: a --format that indents its lines must keep the indent.
    return out.stdout.strip("\n") if out.returncode == 0 else None


def read_version_file(path: pathlib.Path) -> str | None:
    """engine/VERSION, decoded whatever the SDK wrote it as.

    ⚠ It is UTF-16 LE with a BOM here, because the SDK writes it from PowerShell and `>` writes
    UTF-16 (docs/LESSONS_LEARNED.md, the same hazard that forces `bash run_all.sh`). Reading it
    as UTF-8 yields NUL-separated digits that match nothing, which made this audit report a
    permanent, false "the built engine is not the pinned one".
    """
    if not path.is_file():
        return None
    raw = path.read_bytes()
    for encoding in ("utf-16", "utf-8-sig", "utf-8"):
        if encoding == "utf-16" and raw[:2] not in (b"\xff\xfe", b"\xfe\xff"):
            continue
        try:
            return raw.decode(encoding).strip().strip("﻿")
        except UnicodeDecodeError:
            continue
    return None


def pinned_version() -> str | None:
    cfg = ROOT / "mod.config"
    if not cfg.is_file():
        return None
    m = re.search(r'^ENGINE_VERSION="([0-9a-f]{40})"', cfg.read_text(encoding="utf-8", errors="replace"),
                  re.MULTILINE)
    return m.group(1) if m else None


def main() -> int:
    print("# audit_engine_freshness — Cameo's engine vs the upstreams it tracks\n")

    pin = pinned_version()
    built_hash = read_version_file(ROOT / "engine" / "VERSION")

    print("| | |")
    print("|---|---|")
    print(f"| `mod.config` pins | `{pin or 'UNREADABLE'}` |")
    print(f"| `engine/VERSION` (what is built) | `{built_hash or 'absent — engine/ not populated'}` |")
    if pin and built_hash and pin != built_hash:
        print(f"| **mismatch** | the built engine is NOT the pinned one — run `make.cmd all` |")
    print()

    clone = find_clone()
    if clone is None:
        print("_no `cameo-engine` clone found_ — set `CAMEO_ENGINE_ROOT`, or clone "
              "https://github.com/cameo-mod/OpenRA beside this repo.")
        print("\nNOT a clean result: this audit could not measure anything.")
        return 0
    print(f"Clone: `{clone}`\n")

    head = git(clone, "rev-parse", "cameo-engine") or git(clone, "rev-parse", "HEAD")
    if head is None:
        print("_the clone has no `cameo-engine` branch and no readable HEAD._")
        print("\nNOT a clean result: this audit could not measure anything.")
        return 0
    if pin and head != pin:
        print(f"⚠ The clone's `cameo-engine` is `{head[:10]}` but `mod.config` pins `{pin[:10]}` — "
              "the numbers below describe the CLONE, which is ahead of or behind what this repo "
              "actually builds.\n")

    print("| upstream | ref last seen | commits it has that we lack | what it is |")
    print("|---|---|--:|---|")
    rows = []
    for label, ref, what in UPSTREAMS:
        when = git(clone, "log", "-1", "--format=%cd", "--date=short", ref)
        if when is None:
            print(f"| {label} | _ref `{ref}` not in the clone_ | — | {what} |")
            continue
        behind = git(clone, "rev-list", "--count", "--no-merges", ref, "--not", head)
        rows.append((label, ref, int(behind) if behind and behind.isdigit() else None))
        print(f"| {label} | `{ref}` @ {when} | {behind if behind is not None else '?'} | {what} |")

    print("\n⚠ **The ref dates above are that commit's own date, NOT when the clone last "
          "fetched.** A number here is only as fresh as the last "
          "`git -C <clone> fetch upstream mtr --no-tags`.")

    for label, ref, behind in rows:
        if behind:
            print(f"\n### Behind {label} by {behind} commits\n")
            log = git(clone, "log", "--format=%h %ad %an | %s", "--date=short",
                      "--no-merges", "-15", ref, "--not", head)
            if log:
                print("```")
                print(log)
                print("```")
                if behind > 15:
                    print(f"_…and {behind - 15} more._")

    print("\n_Informational: catching up is the `cameo-engine` pipeline in "
          "docs/LESSONS_LEARNED.md, and a maintainer decision._")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
