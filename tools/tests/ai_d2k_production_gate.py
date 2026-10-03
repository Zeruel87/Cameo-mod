#!/usr/bin/env python3
"""Runtime gate: a D2k content-pack bot must grow its base.

Launches ``mods/cameo/maps/ai_d2k_production_gate_20260928`` (HardBot plays
``atreides``, the human anchor plays ``harkonnen``) and asserts that the
bot's owned-actor count, printed by the map's lua as
``AI_D2K_GATE_ACTORS=<n>``, grows past its single starting construction yard.

Regression class: the ContentPack split left ``atreides``, ``harkonnen``,
``corrino``, ``EDEN`` and ``PLYMOUTH`` out of the central ``*Types`` actor
lists (PowerTypes, RefineryTypes, BarracksTypes, ProductionTypes, ...), so
BaseBuilderQueueManagerCA.GetProducibleBuilding always returned null and the
bot never produced anything. The TD gate factions were unaffected, so every
gate stayed green while the houses went inert.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

MAP = "ai_d2k_production_gate_20260928"
TIMEOUT_SECONDS = 300
# Starting actors: one construction yard. A working bot produces a windtrap,
# a refinery and more inside the gate window; an inert one stays at 1.
MIN_TOTAL_ACTORS = 4
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def fail(message: str, output: str = "") -> None:
    print(f"AI d2k production gate FAIL: {message}", file=sys.stderr)
    if output:
        print(output_tail(output), file=sys.stderr)
    sys.exit(1)


def read_config(path: pathlib.Path, values: dict[str, str]) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")


def load_config() -> tuple[str, pathlib.Path]:
    values: dict[str, str] = {}
    read_config(REPO_ROOT / "mod.config", values)
    read_config(REPO_ROOT / "user.config", values)
    mod_id = values.get("MOD_ID", "cameo")
    engine_directory = values.get("ENGINE_DIRECTORY", "./engine")
    engine = pathlib.Path(engine_directory)
    if not engine.is_absolute():
        engine = REPO_ROOT / engine
    return mod_id, engine.resolve()


def output_tail(output: str) -> str:
    lines = output.splitlines()
    if len(lines) > 40:
        lines = lines[-40:]
    return "\n".join(lines)


def run_openra(executable: pathlib.Path, args: list[str], engine: pathlib.Path) -> tuple[int, str]:
    try:
        process = subprocess.Popen(
            [str(executable), *args],
            cwd=engine,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as error:
        fail(f"could not launch OpenRA: {error}")
    try:
        output, _ = process.communicate(timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            output, _ = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate()
        fail(f"OpenRA timed out after {TIMEOUT_SECONDS}s", output)
    return process.returncode, output


def main() -> int:
    mod_id, engine = load_config()
    executable = engine / "bin" / "OpenRA.exe"
    if not executable.is_file():
        fail(f"OpenRA executable is missing: {executable}; run make.cmd all first")

    args = [
        f"Game.Mod={mod_id}",
        "Sound.Device=none",
        "Engine.EngineDir=..",
        f"Engine.ModSearchPaths={REPO_ROOT / 'mods'},{engine / 'mods'}",
        f"Launch.Map={MAP}",
        "Launch.Benchmark=ai-d2k-production-gate-",
    ]
    exit_code, output = run_openra(executable, args, engine)
    if exit_code != 0:
        fail(f"OpenRA exited with code {exit_code}", output)
    if "AI_D2K_PRODUCTION_GATE_COMPLETED" not in output:
        fail("map lua never printed the completion marker", output)

    match = re.search(r"AI_D2K_GATE_ACTORS=(\d+)", output)
    if match is None:
        fail("map lua never printed AI_D2K_GATE_ACTORS", output)
    actors = int(match.group(1))
    if actors < MIN_TOTAL_ACTORS:
        fail(
            f"bot owned only {actors} actors at gate end (minimum {MIN_TOTAL_ACTORS}); "
            "the *Types actor lists are not covering atreides",
            output,
        )

    ticks = [int(t) for t in re.findall(r"AI_D2K_GATE_TICK (\d+)", output)]
    print(
        "AI d2k production gate PASS: "
        f"process_exit={exit_code} last_tick={ticks[-1] if ticks else '?'} "
        f"bot_actors={actors} (started with 1 construction yard)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
