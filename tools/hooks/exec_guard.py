#!/usr/bin/env python3
"""PreToolUse exec guard for Cameo-mod (Devin CLI).

Enforces the same two hard rules as bash_guard.py but reads the Devin CLI
hook format (tool_name = "exec", tool_input.command).

  1. SCOPED ADDS ONLY -- block `git add -A` / `--all` / `.`
  2. BOOT-GATE BEFORE COMMITTING ENGINE CONTENT -- block `git commit` when
     staged engine content is newer than the last successful boot.

Emits a JSON decision on stdout.  No output = allow.
"""
import sys
import os
import re
import json
import subprocess
import pathlib


def block(reason):
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return  # can't parse -> allow
    cmd = (data.get("tool_input") or {}).get("command", "") or ""

    # (1) Scoped adds only
    if re.search(r"(?:^|[\n;&|(])\s*git\s+add\s+(?:-A\b|--all\b|\.(?:\s|$))", cmd):
        block("Scoped adds only -- never `git add -A/--all/.` (the maintainer "
              "and other agents have live uncommitted WIP that a wide add would "
              "capture or clobber). Stage explicit paths: `git add <file> [<file> ...]`.")

    # (2) Boot-gate before committing engine-loaded content
    if re.search(r"\bgit\s+commit\b", cmd):
        # `rev-parse --show-toplevel` gives the worktree actually being committed
        # to; every check below then keys off that. (Ported from bash_guard.py --
        # without it a worktree commit is judged against the main tree's index,
        # so any lane's staged files block every other lane's commit.)
        root = pathlib.Path(os.environ.get("DEVIN_PROJECT_DIR", "")).resolve()
        if not root.exists():
            root = pathlib.Path(__file__).resolve().parents[2]
        where = data.get("cwd") or str(root)
        # The shell cwd resets between tool calls, so an agent working in a worktree
        # writes `cd <worktree> && git commit ...`. That `cd` is INSIDE the command
        # string and invisible to the hook's own `cwd` field -- without reading it,
        # every worktree commit is judged against the main tree's index.
        # Anchor at a COMMAND POSITION, same reason rule (1) does: a commit message
        # that merely MENTIONS `git -C <dir>` in prose must not read as a real flag.
        cmd_pos = r"(?:^|[\n;&|(]|&&|\|\|)\s*"
        m_cd = re.search(cmd_pos + r"cd\s+(\"[^\"]+\"|'[^']+'|\S+)", cmd)
        if m_cd:
            where = m_cd.group(1).strip("\"'")
        m_c = re.search(cmd_pos + r"git\s+-C\s+(\S+)", cmd)   # `git -C <dir> commit`
        if m_c:                                               # explicit -C wins
            where = m_c.group(1).strip("\"'")
        # git-bash hands out MSYS paths (`/c/tmp/x`) but git.exe only understands
        # `C:/tmp/x`, so an unnormalised path silently fails to resolve and the
        # check falls back to the main tree -- the false BLOCK all over again.
        m_msys = re.match(r"^/([a-zA-Z])/(.*)$", where)
        if m_msys:
            where = f"{m_msys.group(1).upper()}:/{m_msys.group(2)}"
        try:
            top = subprocess.run(
                ["git", "-C", str(where), "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, timeout=15)
            if top.returncode == 0 and top.stdout.strip():
                root = pathlib.Path(top.stdout.strip())
        except Exception:
            pass  # fall back to the main checkout -- never less strict than before
        try:
            staged = subprocess.run(
                ["git", "-C", str(root), "diff", "--cached", "--name-only"],
                capture_output=True, text=True, timeout=15).stdout.split()
        except Exception:
            return  # git unavailable -> don't block
        engine_prefixes = ("mods/", "OpenRA.Mods.Cameo/", "engine/")
        eng = [f for f in staged if f.startswith(engine_prefixes)]
        if not eng:
            return  # docs/tools-only commit -- boot not required
        newest = 0.0
        for f in eng:
            p = root / f
            if p.exists():
                newest = max(newest, p.stat().st_mtime)
        perf = pathlib.Path(os.environ.get("APPDATA", "")) / "OpenRA" / "Logs" / "perf.log"
        if not perf.exists():
            block("Boot-gate required: you are committing engine content ("
                  + eng[0]
                  + (" +%d more" % (len(eng) - 1) if len(eng) > 1 else "")
                  + ") but no perf.log was found. Run launch-game.cmd to the "
                  "main menu (perf.log must end with "
                  "MenuPostProcessEffect.PostWorldLoaded), confirm no new "
                  "exception-*.log, then commit.")
        try:
            tail = perf.read_text(errors="ignore").splitlines()[-40:]
        except Exception:
            tail = []
        booted = any("MenuPostProcessEffect.PostWorldLoaded" in ln for ln in tail)
        fresh = perf.stat().st_mtime >= newest - 1  # 1s slack
        if not (booted and fresh):
            why = []
            if not booted:
                why.append("perf.log doesn't show MenuPostProcessEffect.PostWorldLoaded")
            if not fresh:
                why.append("perf.log is older than your staged engine changes")
            block("Boot-gate required before committing engine content -- "
                  + "; ".join(why)
                  + ". Run launch-game.cmd to the menu, confirm no new "
                  "exception-*.log, then commit.")


if __name__ == "__main__":
    main()
