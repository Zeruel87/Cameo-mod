"""Launch two hard bots with a refinery each and count the harvesters they keep.

HarvesterBotModuleCA counts and builds harvesters BY NAME from HarvesterTypes, and counts
refineries by name from RefineryTypes (AI_ARCHITECTURE.md §2.8). The map pairs a TKM bot
(refinery listed, harvester not: fixed by the harvester role) with an Atreides bot (neither
listed: needs the refinery role too). Prints each bot's count at ticks 1500 and 3000 from
lua.log. A refinery gives its harvesters away, so the number that matters is `extra`: harvesters
minus the refineries' free ones, i.e. harvesters the bot BUILT. `--min BOT=N` floors a bot's last extra.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

TESTS_DIR = pathlib.Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from _bootstrap import REPO_ROOT  # noqa: E402
import ai_squad_gate as gate  # noqa: E402

MAP = "ai_harvester_gate_20260927"
SAMPLE = re.compile(r"AI_HARVESTER_GATE_SAMPLE bot=(\w+) tick=(\d+) harvesters=(\d+) refineries=(\d+) extra=(-?\d+) actors=(\d+) far=(\d+)")
TIMEOUT_SECONDS = 600  # 6000 ticks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--min", action="append", default=[], metavar="BOT=N",
                        help="fail if BOT built fewer than N harvesters (extra) by the last sample (repeatable)")
    parser.add_argument("--min-actors", action="append", default=[], metavar="BOT=N",
                        help="fail if BOT owns fewer than N actors at the last sample: an inert bot keeps only what the map gave it")
    args = parser.parse_args()

    mod_id, engine = gate.load_config()
    executable = engine / "bin" / "OpenRA.exe"
    if not executable.is_file():
        gate.fail(f"OpenRA executable is missing: {executable}; run make.cmd all first")

    logs_dir = gate.support_directory(engine) / "Logs"
    exceptions_before = {p.name for p in logs_dir.glob("exception-*.log")} if logs_dir.is_dir() else set()
    lua_log = logs_dir / "lua.log"

    gate.TIMEOUT_SECONDS = TIMEOUT_SECONDS
    exit_code, output = gate.run_openra(executable, [
        f"Game.Mod={mod_id}",
        "Sound.Device=none",
        "Engine.EngineDir=..",
        f"Engine.ModSearchPaths={REPO_ROOT / 'mods'},{engine / 'mods'}",
        f"Launch.Map={MAP}",
        "Launch.Benchmark=ai-harvester-gate-",
    ], engine)
    if exit_code != 0:
        gate.fail(f"OpenRA exited with code {exit_code}\nOpenRA output tail:\n{gate.output_tail(output)}")

    if logs_dir.is_dir():
        new_exceptions = sorted(p.name for p in logs_dir.glob("exception-*.log") if p.name not in exceptions_before)
        if new_exceptions:
            gate.fail(f"new exception log(s) written: {new_exceptions}")

    # Only this run's lines: everything after the last STARTED marker (lua.log may be appended or rewritten).
    text = lua_log.read_text(encoding="utf-8", errors="replace") if lua_log.is_file() else ""
    text = text[text.rfind("AI_HARVESTER_GATE_STARTED"):] if "AI_HARVESTER_GATE_STARTED" in text else ""
    samples: dict[str, list[tuple[int, int, int, int, int, int]]] = {}
    for bot, tick, harvesters, refineries, extra, actors, far in SAMPLE.findall(text):
        samples.setdefault(bot, []).append((int(tick), int(harvesters), int(refineries), int(extra), int(actors), int(far)))
    if not samples:
        gate.fail(f"no AI_HARVESTER_GATE_SAMPLE lines in {lua_log}")

    report = "; ".join(f"{bot} " + " ".join(f"t{t}={h}h/{r}r/+{x}/{a}a/{f}far" for t, h, r, x, a, f in s) for bot, s in samples.items())
    for floor in args.min:
        bot, _, n = floor.partition("=")
        if bot not in samples:
            gate.fail(f"--min names {bot!r}, which reported no samples: {report}")
        if samples[bot][-1][3] < int(n):
            gate.fail(f"{bot} built {samples[bot][-1][3]} harvesters by the last sample (< {n}): {report}")

    for floor in args.min_actors:
        bot, _, n = floor.partition("=")
        if bot not in samples:
            gate.fail(f"--min-actors names {bot!r}, which reported no samples: {report}")
        if samples[bot][-1][4] < int(n):
            gate.fail(f"{bot} owns {samples[bot][-1][4]} actors at the last sample (< {n}): {report}")

    print(f"AI harvester gate PASS: process_exit={exit_code} {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
