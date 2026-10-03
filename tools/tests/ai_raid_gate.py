"""Launch a fog-enabled match and verify the assign layer actually fires.

Companion to ai_squad_gate.py: that gate proves a squad forms at all, this one
proves the mission pipeline end to end — the strategist publishes a Raid mission
against a remembered enemy economy region, and the squad manager consumes it and
assigns a target in that region. The map carries a reachable enemy refinery and
harvesters, because Raid missions are only derived for regions with economy value.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys

TESTS_DIR = pathlib.Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from _bootstrap import REPO_ROOT


MAP = "ai_raid_gate_20260928"
SITUATION_LOG = "cameo-ai-situations.jsonl"
TIMEOUT_SECONDS = 240
CONFIG_KEYS = {"MOD_ID", "ENGINE_DIRECTORY"}


def fail(message: str, record=None) -> None:
    print(f"ASSERTION FAILED: {message}")
    if record is not None:
        print(f"Offending record: {json.dumps(record, sort_keys=True)}")
    raise SystemExit(1)


def read_config(path: pathlib.Path, values: dict[str, str]) -> None:
    if not path.is_file():
        return

    assignment = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = assignment.match(line)
        if not match or match.group(1) not in CONFIG_KEYS:
            continue

        value = match.group(2)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[match.group(1)] = value


def load_config() -> tuple[str, pathlib.Path]:
    values: dict[str, str] = {}
    read_config(REPO_ROOT / "mod.config", values)
    read_config(REPO_ROOT / "user.config", values)

    mod_id = values.get("MOD_ID")
    engine_directory = values.get("ENGINE_DIRECTORY")
    if not mod_id:
        fail("mod.config/user.config did not define MOD_ID")
    if not engine_directory:
        fail("mod.config/user.config did not define ENGINE_DIRECTORY")

    engine = pathlib.Path(engine_directory)
    if not engine.is_absolute():
        engine = REPO_ROOT / engine
    return mod_id, engine.resolve()


def support_directory(engine: pathlib.Path) -> pathlib.Path:
    local = engine / "Support"
    if local.is_dir():
        return local

    appdata = os.environ.get("APPDATA")
    if not appdata or not pathlib.Path(appdata).is_dir():
        fail("neither engine/Support nor a usable %APPDATA% resolves the OpenRA SupportDir")
    return pathlib.Path(appdata) / "OpenRA"


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
        fail(f"OpenRA timed out after {TIMEOUT_SECONDS}s\nOpenRA output tail:\n{output_tail(output)}")
    return process.returncode, output


def read_appended_records(log_path: pathlib.Path, before_length: int) -> list[dict]:
    if not log_path.is_file():
        fail(f"situation log was not written: {log_path}")

    try:
        appended = log_path.read_bytes()[before_length:].decode("utf-8")
    except UnicodeDecodeError as error:
        fail(f"appended situation log is not UTF-8: {error}")

    records = []
    for line_number, line in enumerate(appended.splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            fail(f"appended situation log line {line_number} is not JSON: {error}", line)
        if isinstance(record, dict) and record.get("kind") == "situation" and record.get("player") == "HardBot":
            records.append(record)
    return records


def main() -> int:
    mod_id, engine = load_config()
    executable = engine / "bin" / "OpenRA.exe"
    if not executable.is_file():
        fail(f"OpenRA executable is missing: {executable}; run make.cmd all first")

    support = support_directory(engine)
    log_path = support / "Logs" / SITUATION_LOG
    before_length = log_path.stat().st_size if log_path.is_file() else 0

    logs_dir = support / "Logs"
    exceptions_before = set()
    if logs_dir.is_dir():
        exceptions_before = {p.name for p in logs_dir.glob("exception-*.log")}

    args = [
        f"Game.Mod={mod_id}",
        "Sound.Device=none",
        "Engine.EngineDir=..",
        f"Engine.ModSearchPaths={REPO_ROOT / 'mods'},{engine / 'mods'}",
        f"Launch.Map={MAP}",
        "Launch.Benchmark=ai-raid-gate-",
    ]
    exit_code, output = run_openra(executable, args, engine)
    if exit_code != 0:
        fail(f"OpenRA exited with code {exit_code}\nOpenRA output tail:\n{output_tail(output)}")

    if logs_dir.is_dir():
        new_exceptions = sorted(
            p.name for p in logs_dir.glob("exception-*.log") if p.name not in exceptions_before
        )
        if new_exceptions:
            fail(f"new exception log(s) written: {new_exceptions}")

    records = read_appended_records(log_path, before_length)
    if not records:
        fail("no HardBot situation records were appended")

    raid_regions = {
        mission.get("region_index")
        for record in records
        for mission in [record.get("mission")]
        if isinstance(mission, dict) and mission.get("type") == "raid"
    }
    if not raid_regions:
        fail("no HardBot situation record published a Raid mission", records[-1])

    assignments = []
    for record in records:
        assignment = record.get("mission_assignment")
        own = record.get("own")
        squads = own.get("squad_count") if isinstance(own, dict) else None
        if (
            isinstance(assignment, dict)
            and assignment.get("type") == "raid"
            and assignment.get("region_index") in raid_regions
            and isinstance(squads, int)
            and not isinstance(squads, bool)
            and squads >= 1
        ):
            assignments.append((record, assignment))

    if not assignments:
        fail(
            "no Rush squad assignment was observed in a published Raid region",
            records[-1],
        )

    latest, assignment = assignments[-1]
    own = latest["own"]
    squads = own["squad_count"]

    print(
        "AI Raid mission gate PASS: "
        f"records={len(records)} process_exit={exit_code} last_tick={latest['tick']} "
        f"raid_regions={sorted(raid_regions)} assignment_region={assignment['region_index']} "
        f"frozen={assignment.get('frozen')} squads={squads} squad_units={own.get('squad_units')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
