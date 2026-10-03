#!/usr/bin/env python3
"""Boot a worktree to the main menu and save every bot-module field the engine holds (AI_ARCHITECTURE.md §2.9 P0).

The equivalence gate of the empty-ai.yaml plan: the Python resolver cannot see what BotRoleSets (and
later the type defaults) fill at rules load, so the engine writes it out itself. Set
CAMEO_DUMP_BOT_MODULES=1 and `BotModuleFieldDump` logs one line per `Type@instance.Field = value`
into <support>/Logs/bot-modules.log. This script does the boot in an isolated support dir, closes the
game GRACEFULLY (a forced kill loses the buffered log), and writes the last complete dump to --out.

    python tools/ai/dump_bot_modules.py --out before.txt            # this worktree
    python tools/ai/dump_bot_modules.py --worktree C:/tmp/x --out after.txt
    python tools/ai/diff_bot_modules.py before.txt after.txt

The worktree needs its own built engine/ (see LESSONS_LEARNED: one engine copy per worktree).
"""
from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

REPO = pathlib.Path(__file__).resolve().parents[2]
HEADER = "=== bot-modules dump ==="
MENU = "MenuPostProcessEffect.PostWorldLoaded"


def last_dump(text: str) -> list[str]:
    """The lines of the last complete dump in a log (rules load more than once on the way to the menu)."""
    blocks, cur = [], None
    for raw in text.splitlines():
        line = raw.split("] ", 1)[1] if raw.startswith("[") and "] " in raw else raw  # tolerate timestamps
        if line == HEADER:
            cur = []
            blocks.append(cur)
        elif cur is not None and line.strip():
            cur.append(line)
    return blocks[-1] if blocks else []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--worktree", type=pathlib.Path, default=REPO, help="worktree to boot (default: this one)")
    ap.add_argument("--out", type=pathlib.Path, required=True, help="where to write the dump")
    ap.add_argument("--timeout", type=int, default=420, help="seconds to wait for the main menu")
    args = ap.parse_args()

    wt = args.worktree.resolve()
    exe = wt / "engine" / "bin" / ("OpenRA.exe" if os.name == "nt" else "OpenRA")
    if not exe.exists():
        print(f"FAIL: no built engine at {exe}")
        return 1

    support = pathlib.Path(tempfile.mkdtemp(prefix="bot-modules-"))
    env = dict(os.environ, CAMEO_DUMP_BOT_MODULES="1")
    cmd = [str(exe), "Game.Mod=cameo", "Engine.EngineDir=..", f"Engine.LaunchPath={wt / 'launch-game.cmd'}",
           f"Engine.ModSearchPaths={wt / 'mods'},./mods", f"Engine.SupportDir={support}{os.sep}"]
    proc = subprocess.Popen(cmd, cwd=wt / "engine", env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logs = support / "Logs"
    try:
        deadline = time.time() + args.timeout
        while time.time() < deadline and proc.poll() is None:
            perf = logs / "perf.log"
            if perf.exists() and MENU in perf.read_text(encoding="utf-8", errors="replace"):
                break
            time.sleep(3)
        else:
            print(f"FAIL: no main menu within {args.timeout}s (exit={proc.poll()})")
            return 1
    finally:
        if proc.poll() is None:
            if os.name == "nt":  # WM_CLOSE first: the log is flushed on a normal exit
                subprocess.run(["taskkill", "/PID", str(proc.pid)], capture_output=True)
            else:
                proc.terminate()
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()

    exceptions = sorted(p.name for p in logs.glob("exception-*.log"))
    dump_log = logs / "bot-modules.log"
    lines = last_dump(dump_log.read_text(encoding="utf-8", errors="replace")) if dump_log.exists() else []
    if exceptions:
        print(f"FAIL: boot wrote {exceptions} (support dir kept: {support})")
        return 1
    if not lines:
        print(f"FAIL: no dump in {dump_log} — is the Cameo DLL built from a tree with BotModuleFieldDump?")
        return 1

    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    shutil.rmtree(support, ignore_errors=True)
    print(f"{len(lines)} fields from {wt} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
