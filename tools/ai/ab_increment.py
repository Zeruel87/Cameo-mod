#!/usr/bin/env python3
"""Increment A/B driver — one command runs the whole three-arm mirror-match experiment.

AI_MASTER_PLAN §1.2 step 6 (amended 2026-10-01): an increment lands on master behind
behaviour switches, then ONE A/B decides whether the switches stay. This driver is that
A/B. It freezes each arm in its own `git worktree`, applies the increment's switches
in-tree via tools/ai/apply_increment_switches.py (uncommitted edits — the design is that
master keeps the defaults until the A/B says otherwise), then runs mirror shards through
the arm's OWN run_ai_match_batch.py copy.

Arms:
    ctrl — --ctrl commit, no switches (the previous-master baseline)
    half — --cand commit + `--groups A_squad_tactics`  (override: --half-groups)
    all  — --cand commit + `--groups all`              (override: --groups)
--arms ctrl,all selects a subset (default: all three).

MIRROR-ONLY BY CONSTRUCTION (maintainer ruling 2026-10-01): cross-faction matches measure
faction balance, not the bot, so each arm runs its factions as SEPARATE shard batches —
`--factions td_gdi` and `--factions td_nod` in two invocations, NEVER the combined
`--factions td_gdi,td_nod` (which adds the cross pairing). enforce_single_faction() is
the belt: shard argv cannot carry a comma.

Each shard:
    python <tree>/tools/ai/run_ai_match_batch.py --factions <one> --bot-a hard
        --bot-b classic --repeats 8 --swap-bots --time-limit 3
        --support-dir <out>/<arm>_<faction>
with cwd = the arm's frozen tree. The runner resolves REPO_ROOT, mods/ and ./engine from
its own location, so invoking the TREE'S copy is what actually freezes the arm — tools/ai
is itself part of the batch fingerprint. 8 repeats x 2 factions = 16 matches per arm.

Frozen trees: `git worktree add --detach <out>/trees/<arm> <commit>`, then (switch arms)
the applier from THIS checkout — it reads THIS repo's increment_switches.yaml, which is
the spec the A/B was ordered under; the tree's own copy may be older. Engine: copy
engine/ from --engine-donor (a checkout with a built engine; the dir itself or its
parent both accepted), else `make.cmd all` in the tree; then always
`dotnet build CameoMod.sln -c Release --nologo -p:TargetPlatform=win-x64` with
DOTNET_ROLL_FORWARD=LatestMajor so the mod DLLs match the tree's C#. --skip-build reuses
already-prepared trees (switches are still re-applied — the applier is idempotent).

Capacity: at most --max-instances OpenRA.exe MACHINE-WIDE — the fleet shares the box, so
foreign matches count too. Each shard's batch runner is internally sequential (one game
instance per shard). A just-launched shard's OpenRA.exe takes a while to appear in
tasklist (variant write + mod load); launches are credited for --spawn-grace seconds so a
burst cannot overshoot the cap before the new processes become visible.

Phases:
  1. provision the arm trees (worktree add, switches, engine, dotnet build)
  2. --smoke: ONE match per arm first (repeats=1, first faction, own support dir under
     <out>/smoke/ so its different batch fingerprint can never pool into arm data).
     Verified: match records in Logs/cameo-ai-matches.jsonl AND a fingerprint in
     batch_results.jsonl; a dead/timed-out smoke aborts that arm loudly.
  3. full shards under the instance cap
  4. pooled readout: ab_summary.py per arm + <out>/increment_summary.json

Early stop: every --poll-seconds the driver re-tallies each arm's `hard` (bot-a) wins
from its shards' batch_results.jsonl (one row per consumed matchup — retried/aborted
attempts included, they still burn a planned match). A pair is decided when the trailer
cannot reach the leader even by winning every match it can still play
(`trailing_won + remaining < leading_won`; equality — a possible tie — keeps it live).
Then a subtlety the plain reading misses: with three arms, killing a decided pair's
shards would FREEZE the other pairs those arms still feed, biasing them. So an arm's
remaining shards are terminated only once EVERY pair touching it is decided — that is
the moment its data can no longer change any verdict. Decisions land in the run summary
as "early_stop" entries.

Resilience: a full shard whose batch driver exits before its plan played out is
relaunched into a fresh <support>_rN dir — up to --shard-retries times, replaying only
the unplayed remainder (--repeats = planned - played). Progress, fingerprints and the
pooled summary union across a shard's rounds. Early-stopped shards never retry; a dead
smoke aborts its arm. When tearing a shard down the driver kills the OpenRA.exe child
BEFORE the python parent (an orphaned game still holds an instance slot) and warns if a
live driver shows no OpenRA child — that invariant breaks silently if the batch runner
ever gains a shell wrapper.

Usage:
    python tools/ai/ab_increment.py --ctrl <sha> --cand <sha> --groups all --out C:/tmp/inc2ab-x
    python tools/ai/ab_increment.py --ctrl <sha> --cand <sha> --out ... \
        --arms ctrl,all --smoke --engine-donor C:/path/to/built/checkout --dry-run
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOLS_AI = pathlib.Path(__file__).resolve().parent
APPLIER = TOOLS_AI / "apply_increment_switches.py"
AB_SUMMARY = TOOLS_AI / "ab_summary.py"
BATCH_RUNNER_REL = pathlib.Path("tools") / "ai" / "run_ai_match_batch.py"

MATCH_LOG = "cameo-ai-matches.jsonl"
BATCH_RESULTS = "batch_results.jsonl"
ARM_NAMES = ("ctrl", "half", "all")


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def enforce_single_faction(faction: str) -> str:
    """Mirror-only by construction: a shard is exactly ONE faction's mirror batch.
    A comma here would smuggle the cross pairing the 2026-10-01 ruling excluded."""
    f = faction.strip()
    if not f or "," in f:
        fail(f"shard --factions must name exactly one faction, got {faction!r} "
             "(cross-faction matches measure faction balance, not the bot)")
    return f


def shard_argv(
    tree: pathlib.Path,
    *,
    faction: str,
    support: pathlib.Path,
    bot_a: str,
    bot_b: str,
    repeats: int,
    time_limit: int,
    stall_timeout: int,
) -> list[str]:
    """The exact batch-runner invocation for one shard — single faction enforced."""
    faction = enforce_single_faction(faction)
    return [
        sys.executable,
        str(tree / BATCH_RUNNER_REL),
        "--factions", faction,
        "--bot-a", bot_a,
        "--bot-b", bot_b,
        "--repeats", str(repeats),
        "--swap-bots",
        "--time-limit", str(time_limit),
        "--support-dir", str(support),
        "--stall-timeout", str(stall_timeout),
    ]


@dataclass
class Arm:
    name: str
    commit: str               # resolved sha after resolve_commits(); the given ref before
    groups: str | None        # applier --groups; None = ctrl (no switches)
    tree: pathlib.Path
    state: str = "pending"    # pending -> ready | aborted
    smoke_detail: str = ""


@dataclass
class Shard:
    arm: str
    faction: str
    kind: str                 # "smoke" | "full"
    planned: int              # matches this batch consumes when it runs to completion
    support: pathlib.Path
    argv: list[str]
    cwd: pathlib.Path
    label: str
    proc: subprocess.Popen | None = None
    launched_at: float = 0.0
    done: bool = False
    returncode: int | None = None
    early_stopped: bool = False
    log_handle: object = None
    attempt: int = 1           # relaunches go to <support>_rN; results pool across dirs
    dirs: list[pathlib.Path] = None

    def __post_init__(self):
        if self.dirs is None:
            self.dirs = [self.support]


def build_plan(args: argparse.Namespace) -> tuple[list[Arm], list[Shard], list[Shard]]:
    """(arms, full shards, smoke shards). Pure planning — touches nothing."""
    names = [n.strip() for n in args.arms.split(",") if n.strip()]
    if not names:
        fail("--arms needs at least one arm")
    unknown = [n for n in names if n not in ARM_NAMES]
    if unknown:
        fail(f"unknown arm(s) {unknown}; known: {list(ARM_NAMES)}")
    if len(set(names)) != len(names):
        fail(f"duplicate arm(s) in --arms {names}")

    factions = [f.strip() for f in args.factions.split(",") if f.strip()]
    if not factions:
        fail("--factions needs at least one faction id")
    for f in factions:
        enforce_single_faction(f)  # the driver list is per-shard specs, never one comma'd batch

    commit_and_groups = {
        "ctrl": (args.ctrl, None),
        "half": (args.cand, args.half_groups),
        "all": (args.cand, args.groups),
    }
    trees = args.out / "trees"
    arms = [Arm(n, commit_and_groups[n][0], commit_and_groups[n][1], trees / n) for n in names]

    common = {"bot_a": args.bot_a, "bot_b": args.bot_b,
              "time_limit": args.time_limit, "stall_timeout": args.stall_timeout}
    shards: list[Shard] = []
    for arm in arms:
        for faction in factions:
            support = args.out / f"{arm.name}_{faction}"
            shards.append(Shard(
                arm.name, faction, "full", args.repeats, support,
                shard_argv(arm.tree, faction=faction, support=support,
                           repeats=args.repeats, **common),
                arm.tree, f"{arm.name}_{faction}"))

    smoke: list[Shard] = []
    if args.smoke:
        # One match per arm on the FIRST faction — support under <out>/smoke/ so the
        # smoke batch's different config fingerprint can never pool into arm data.
        for arm in arms:
            faction = factions[0]
            support = args.out / "smoke" / f"{arm.name}_{faction}"
            smoke.append(Shard(
                arm.name, faction, "smoke", 1, support,
                shard_argv(arm.tree, faction=faction, support=support, repeats=1, **common),
                arm.tree, f"smoke_{arm.name}_{faction}"))
    return arms, shards, smoke


# --- capacity ---------------------------------------------------------------

def parse_tasklist_count(output: str) -> int:
    """Rows of `tasklist /fi "imagename eq OpenRA.exe" /fo csv /nh` that are an
    OpenRA.exe. The no-match line ('INFO: No tasks ...') parses to zero."""
    count = 0
    for row in csv.reader(io.StringIO(output)):
        if row and row[0].strip().lower() == "openra.exe":
            count += 1
    return count


def count_openra_processes() -> int:
    """Machine-wide OpenRA.exe count — ours AND foreign; the cap is shared."""
    if os.name == "nt":
        proc = subprocess.run(
            ["tasklist", "/fi", "imagename eq OpenRA.exe", "/fo", "csv", "/nh"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        if proc.returncode != 0:
            fail(f"tasklist failed ({proc.returncode}): {proc.stderr.strip()}")
        return parse_tasklist_count(proc.stdout)
    proc = subprocess.run(["pgrep", "-fc", "OpenRA"],
                          capture_output=True, text=True, timeout=30)
    try:
        return int(proc.stdout.strip())
    except ValueError:
        return 0


def recent_credit(running: list[Shard], grace: float) -> int:
    """Shards launched within `grace` seconds whose OpenRA child has not had time to
    appear in tasklist yet — counting them anyway is what keeps a launch burst under
    the cap (the machine count lags reality by the whole mod-load window)."""
    now = time.time()
    return sum(1 for s in running if now - s.launched_at < grace)


def openra_child_pids(parent_pid: int) -> list[int]:
    """PIDs of OpenRA.exe processes parented to a batch subprocess (Windows CIM)."""
    if os.name != "nt":
        return []
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='OpenRA.exe'\" "
             f"| Where-Object ParentProcessId -eq {int(parent_pid)} "
             "| Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return []
    return [int(tok) for tok in proc.stdout.split() if tok.isdigit()]


def terminate_shard(shard: Shard) -> None:
    """Kill a shard's OpenRA child THEN its batch subprocess — terminating only the
    python parent leaves the game orphaned and still holding an instance slot."""
    proc = shard.proc
    if proc is None:
        shard.done = True
        shard.early_stopped = True
        return
    if proc.poll() is not None:
        shard.done = True
        shard.returncode = proc.returncode
        return
    children = openra_child_pids(proc.pid)
    for pid in children:
        subprocess.run(["taskkill", "/f", "/t", "/pid", str(pid)],
                       capture_output=True, text=True)
    if not children:
        print(f"  warn: {shard.name} driver pid={proc.pid} is live but has no OpenRA.exe"
              " child — if run_ai_match_batch ever gains a shell wrapper, its game"
              " is now orphaned and still holds an instance slot", flush=True)
    proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    shard.early_stopped = True
    shard.done = True
    shard.returncode = proc.returncode


# --- progress + early stop ---------------------------------------------------

def shard_progress(shard: Shard, bot_a: str) -> tuple[int, int]:
    """(matches consumed, bot_a wins) from the shard's batch_results.jsonl. Every row
    is one matchup the batch will not revisit — retries collapse into the single row
    the batch appends per matchup, and drift tombstones still burned the slot."""
    played = won = 0
    for d in shard.dirs:
        path = d / BATCH_RESULTS
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            played += 1
            for bo in row.get("bot_outcomes") or []:
                if bo.get("bot_type") == bot_a and bo.get("outcome") == "won":
                    won += 1
                    break
    return played, won


def shard_remaining(shard: Shard) -> int:
    """Matches this shard can still play. An exited batch never returns to unplayed
    matchups — a dead shard contributes 0, which is what tightens catch-up math when
    a batch aborts early (fingerprint drift, external kill)."""
    if shard.done:
        return 0
    played, _ = shard_progress(shard, bot_a="")
    return max(0, shard.planned - played)


def shard_needs_retry(shard: Shard, played: int, shard_retries: int) -> bool:
    """A full shard whose driver exited before its plan played out gets relaunched
    into a fresh <support>_rN dir (results pool across dirs) until the retry budget
    is spent. Early-stopped shards never retry — that stop was deliberate; smoke
    shards never retry (a dead smoke aborts the arm loudly)."""
    return (shard.kind == "full" and not shard.early_stopped
            and played < shard.planned and shard.attempt <= shard_retries)


def arm_tally(arm: str, shards: list[Shard], bot_a: str) -> dict:
    """Pooled won/played/remaining over the arm's full shards."""
    played = won = remaining = 0
    for s in shards:
        if s.arm != arm or s.kind != "full":
            continue
        p, w = shard_progress(s, bot_a)
        played += p
        won += w
        remaining += shard_remaining(s)
    return {"won": won, "played": played, "remaining": remaining}


def trailing_cannot_catch_up(trailing_won: int, trailing_remaining: int, leading_won: int) -> bool:
    """Strictly unreachable: even winning EVERY match still to play leaves the trailer
    behind. Equality — a still-possible tie — is NOT a stop."""
    return trailing_won + trailing_remaining < leading_won


def decided_pair(a: dict, b: dict) -> str | None:
    """'a' if a leads hopelessly, 'b' if b does, None while either can still reach
    the other. a/b are arm_tally() dicts."""
    if trailing_cannot_catch_up(b["won"], b["remaining"], a["won"]):
        return "a"
    if trailing_cannot_catch_up(a["won"], a["remaining"], b["won"]):
        return "b"
    return None


def evaluate_early_stop(
    arms: list[Arm],
    shards: list[Shard],
    bot_a: str,
    decided: dict[tuple, dict],
) -> set[str]:
    """One evaluation pass. `decided` maps frozenset({a,b}) -> the recorded verdict and
    persists across calls. Returns arm names whose remaining shards may be torn down
    (every pair touching them decided)."""
    live = [a.name for a in arms if a.state != "aborted"]
    tallies = {n: arm_tally(n, shards, bot_a) for n in live}
    print("[poll] " + " | ".join(
        f"{n}: won={t['won']} played={t['played']} remaining={t['remaining']}"
        for n, t in tallies.items()), flush=True)

    for i, name_a in enumerate(live):
        for name_b in live[i + 1:]:
            key = frozenset((name_a, name_b))
            if key in decided:
                continue
            lead = decided_pair(tallies[name_a], tallies[name_b])
            if lead is None:
                continue
            leader, trailer = (name_a, name_b) if lead == "a" else (name_b, name_a)
            decided[key] = {
                "pair": sorted(key),
                "leader": leader,
                "leader_won": tallies[leader]["won"],
                "trailer": trailer,
                "trailer_won": tallies[trailer]["won"],
                "trailer_max_possible": tallies[trailer]["won"] + tallies[trailer]["remaining"],
            }
            print(f"[early-stop] pair {leader}>{trailer} decided: "
                  f"{tallies[trailer]['won']}+{tallies[trailer]['remaining']} "
                  f"< {tallies[leader]['won']} — trailer cannot catch up", flush=True)

    # An arm's shards die only when the arm can no longer swing ANY verdict —
    # i.e. every pair containing it is decided. Killing earlier would freeze a
    # still-live comparison on partial data and bias it.
    stoppable = {
        n for n in live
        if all(frozenset((n, o)) in decided for o in live if o != n) and len(live) > 1
    }
    for name in stoppable:
        for s in shards:
            if s.arm == name and s.kind == "full" and not s.done:
                if s.proc is not None and s.proc.poll() is None:
                    print(f"[early-stop] terminating {s.label} "
                          f"(all pairs on {name} decided)", flush=True)
                    terminate_shard(s)
                else:
                    s.done = True           # pending shard: never launched, never will be
                    s.early_stopped = True
    return stoppable


# --- smoke -------------------------------------------------------------------

def smoke_verified(support: pathlib.Path) -> tuple[bool, str]:
    """The smoke contract: real match records appended AND a batch fingerprint
    landed — proves the arm's tree/engine/mod pipeline runs end to end."""
    log = support / "Logs" / MATCH_LOG
    records = 0
    if log.is_file():
        records = sum(
            1 for line in log.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip())
    if records < 1:
        return False, f"no match records in {log}"
    results = support / BATCH_RESULTS
    fingerprints: set[str] = set()
    if results.is_file():
        for line in results.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("fingerprint"):
                fingerprints.add(row["fingerprint"])
    if not fingerprints:
        return False, f"no fingerprint in {results}"
    return True, f"{records} record(s), fingerprint(s) {', '.join(sorted(fingerprints))}"


# --- provisioning --------------------------------------------------------------

def resolve_commit(ref: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--verify", f"{ref}^{{commit}}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        fail(f"cannot resolve commit {ref!r}: {proc.stderr.strip()}")
    return proc.stdout.strip()


def validate_groups(args: argparse.Namespace, arms: list[Arm]) -> None:
    """Check applier group names against increment_switches.yaml BEFORE the slow
    tree checkouts — a typo'd group should fail in seconds, not after two clones."""
    if not any(a.groups for a in arms):
        return
    sys.path.insert(0, str(TOOLS_AI))
    import apply_increment_switches as applier
    if not applier.SPEC.is_file():
        fail(f"increment switch spec missing: {applier.SPEC}")
    _, groups = applier.load_spec(applier.SPEC)
    wanted: set[str] = set()
    for a in arms:
        if a.groups and a.groups != "all":
            wanted.update(g.strip() for g in a.groups.split(",") if g.strip())
    unknown = sorted(wanted - set(groups))
    if unknown:
        fail(f"unknown switch group(s) {unknown}; spec knows {list(groups)}")


def run_step(cmd: list, what: str, cwd: pathlib.Path | None = None, env: dict | None = None) -> None:
    print(f"  $ {' '.join(str(c) for c in cmd)}" + (f"   (cwd={cwd})" if cwd else ""), flush=True)
    proc = subprocess.run([str(c) for c in cmd], cwd=cwd, env=env)
    if proc.returncode != 0:
        fail(f"{what} failed with exit {proc.returncode}")


def provision_arm(arm: Arm, args: argparse.Namespace) -> None:
    """Worktree -> switches -> engine -> mod DLLs. --skip-build reuses the tree
    (switches still re-applied: the applier only writes lines that differ)."""
    tree = arm.tree
    print(f"[provision] {arm.name}: commit={arm.commit} groups={arm.groups or '-'} tree={tree}", flush=True)
    if args.skip_build:
        if not tree.is_dir():
            fail(f"--skip-build needs a prepared tree at {tree}")
    else:
        if tree.exists():
            fail(f"tree path already exists: {tree} (use --skip-build to reuse prepared trees)")
        tree.parent.mkdir(parents=True, exist_ok=True)
        run_step(["git", "-C", str(REPO_ROOT), "worktree", "add", "--detach", str(tree), arm.commit],
                 f"worktree add for arm {arm.name}")
    if arm.groups:
        run_step([sys.executable, str(APPLIER), str(tree), "--groups", arm.groups],
                 f"apply_increment_switches {arm.groups} for arm {arm.name}",
                 cwd=REPO_ROOT)
    if args.skip_build:
        arm.state = "ready"
        return
    if args.engine_donor:
        donor = args.engine_donor
        engine_src = donor / "engine" if (donor / "engine").is_dir() else donor
        if not (engine_src / "bin" / "OpenRA.exe").is_file():
            fail(f"--engine-donor {donor} has no built engine (missing {engine_src / 'bin' / 'OpenRA.exe'})")
        print(f"[provision] {arm.name}: copying engine from {engine_src} ...", flush=True)
        shutil.copytree(engine_src, tree / "engine")
    else:
        run_step([os.environ.get("COMSPEC", "cmd.exe"), "/c", "make.cmd", "all"],
                 f"make.cmd all for arm {arm.name}", cwd=tree)
    run_step(["dotnet", "build", "CameoMod.sln", "-c", "Release", "--nologo",
              "-p:TargetPlatform=win-x64"],
             f"dotnet build for arm {arm.name}", cwd=tree,
             env={**os.environ, "DOTNET_ROLL_FORWARD": "LatestMajor"})
    arm.state = "ready"


# --- driving -------------------------------------------------------------------

def launch_shard(shard: Shard) -> None:
    shard.support.mkdir(parents=True, exist_ok=True)
    log = open(shard.support / "batch_stdout.log", "w", encoding="utf-8")
    shard.log_handle = log
    shard.proc = subprocess.Popen(
        [str(c) for c in shard.argv], cwd=shard.cwd,
        stdout=log, stderr=subprocess.STDOUT)
    shard.launched_at = time.time()


def drive(shards: list[Shard], args: argparse.Namespace,
          stop_ctx: tuple | None = None) -> None:
    """Run shards under the instance cap; reap, launch, and (with stop_ctx =
    (arms, all_full_shards, decided)) evaluate the early-stop rule each
    --poll-seconds."""
    pending = collections.deque(shards)
    running: list[Shard] = []
    last_eval = 0.0
    while pending or running:
        for s in list(running):
            if s.proc.poll() is not None:
                s.done = True
                s.returncode = s.proc.returncode
                if s.log_handle:
                    s.log_handle.close()
                    s.log_handle = None
                running.remove(s)
                played, _ = shard_progress(s, args.bot_a)
                tail = 'early-stopped' if s.early_stopped else 'finished'
                if shard_needs_retry(s, played, args.shard_retries):
                    # Driver died short of its plan — relaunch the remainder into a
                    # fresh _rN dir (results pool across dirs; matches Claude's
                    # supervisor semantics, minus re-playing finished matchups).
                    s.attempt += 1
                    s.support = s.dirs[0].parent / f"{s.dirs[0].name}_r{s.attempt}"
                    s.dirs.append(s.support)
                    remaining = s.planned - played
                    s.argv = shard_argv(s.cwd, faction=s.faction, support=s.support,
                                        repeats=remaining, bot_a=args.bot_a,
                                        bot_b=args.bot_b, time_limit=args.time_limit,
                                        stall_timeout=args.stall_timeout)
                    s.done = False
                    s.returncode = None
                    pending.append(s)
                    tail = f'retrying ({played}/{s.planned} played, attempt {s.attempt})'
                print(f"[done] {s.label} exit={s.returncode} ({tail})", flush=True)
        if stop_ctx is not None and time.monotonic() - last_eval >= args.poll_seconds:
            last_eval = time.monotonic()
            arms, all_shards, decided = stop_ctx
            stopped = evaluate_early_stop(arms, all_shards, args.bot_a, decided)
            for s in list(pending):
                if s.arm in stopped:
                    pending.remove(s)   # already marked done+early_stopped inside evaluate
        while pending:
            load = count_openra_processes() + recent_credit(running, args.spawn_grace)
            if load >= args.max_instances:
                break
            shard = pending.popleft()
            launch_shard(shard)
            running.append(shard)
            load += 1
            tail = " ".join(str(c) for c in shard.argv[2:])
            print(f"[launch] {shard.label}: {tail}\n"
                  f"         (cwd={shard.cwd}; instances≈{load}/{args.max_instances})", flush=True)
        if pending or running:
            time.sleep(5)


# --- readout -------------------------------------------------------------------

def iter_match_records(dirs: list[pathlib.Path]):
    for d in dirs:
        for f in sorted(d.rglob(MATCH_LOG)):
            for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def arm_stats(records) -> dict:
    """Pooled per-bot W-L-draw + watchdog totals for one arm — same rules as
    ab_summary.py: a match whose two records both say 'lost' is a timeout draw;
    ownership/order_gate sum their numeric keys (absent in older records)."""
    games = collections.defaultdict(list)
    for r in records:
        games[r.get("game_uid")].append(r)
    bots = collections.defaultdict(lambda: {"won": 0, "lost": 0, "draw": 0})
    ownership: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    order_gate: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for recs in games.values():
        if len(recs) != 2:
            continue
        draw = all((r.get("player") or {}).get("outcome") != "won" for r in recs)
        for r in recs:
            player = r.get("player") or {}
            bot = player.get("bot_type") or "?"
            cell = bots[bot]
            if draw:
                cell["draw"] += 1
            elif player.get("outcome") == "won":
                cell["won"] += 1
            else:
                cell["lost"] += 1
            own = r.get("ownership")
            if isinstance(own, dict):
                for k, v in own.items():
                    if k != "by_type" and isinstance(v, int):
                        ownership[bot][k] += v
            gate = r.get("order_gate")
            if isinstance(gate, dict):
                for k, v in gate.items():
                    if isinstance(v, int):
                        order_gate[bot][k] += v
    return {
        "matches": len(games),
        "per_bot": {b: s for b, s in sorted(bots.items())},
        "ownership": {b: dict(c) for b, c in sorted(ownership.items())},
        "order_gate": {b: dict(c) for b, c in sorted(order_gate.items())},
    }


def shard_fingerprints(shard: Shard) -> list[str]:
    """Distinct fingerprint ids in one shard's batch_results.jsonl — one expected
    per shard (the batch aborts on drift); drift tombstones still count as sightings."""
    fps: set[str] = set()
    for d in shard.dirs:
        path = d / BATCH_RESULTS
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("fingerprint"):
                fps.add(row["fingerprint"])
    return sorted(fps)


def summarize(out: pathlib.Path, arms: list[Arm], shards: list[Shard],
              smoke: list[Shard], args: argparse.Namespace,
              decided: dict, started: float) -> int:
    """ab_summary per arm (both faction shards pooled) + increment_summary.json."""
    summary = {
        "driver": "tools/ai/ab_increment.py",
        "created": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "wall_seconds": int(time.monotonic() - started),
        "ctrl": args.ctrl, "cand": args.cand,
        "groups": args.groups, "half_groups": args.half_groups,
        "bot_a": args.bot_a, "bot_b": args.bot_b,
        "repeats": args.repeats, "time_limit": args.time_limit,
        "factions": [s.faction for s in shards if s.arm == arms[0].name] if arms else [],
        "max_instances": args.max_instances,
        "arms": {},
        "early_stop": [v for _, v in sorted(decided.items(), key=lambda kv: sorted(kv[0]))],
    }
    worst = 0
    for arm in arms:
        arm_shards = [s for s in shards if s.arm == arm.name]
        dirs = [d for s in arm_shards for d in s.dirs]
        print(f"\n===== arm {arm.name} ({arm.commit[:12] if arm.commit else '?'}, "
              f"groups={arm.groups or '-'}) =====", flush=True)
        rc = None
        if arm.state != "aborted" and any(d.is_dir() for d in dirs):
            proc = subprocess.run(
                [sys.executable, str(AB_SUMMARY), *[str(d) for d in dirs]],
                capture_output=True, text=True, encoding="utf-8", errors="replace")
            sys.stdout.write(proc.stdout)
            if proc.stderr:
                sys.stderr.write(proc.stderr)
            rc = proc.returncode
            if rc != 0:
                worst = 1  # ab_summary 1 = mixed fingerprints within one arm
        stats = arm_stats(iter_match_records(dirs))
        arm_fps = sorted({fp for s in arm_shards for fp in shard_fingerprints(s)})
        summary["arms"][arm.name] = {
            "commit": arm.commit,
            "groups": arm.groups,
            "tree": str(arm.tree),
            "state": arm.state,
            "smoke": arm.smoke_detail or None,
            "fingerprints": arm_fps,
            "ab_summary_rc": rc,
            "stats": stats,
            "shards": {
                s.label: {
                    "faction": s.faction,
                    "support": [str(d) for d in s.dirs],
                    "attempts": s.attempt,
                    "returncode": s.returncode,
                    "early_stopped": s.early_stopped,
                    "played": shard_progress(s, args.bot_a)[0],
                    "won": shard_progress(s, args.bot_a)[1],
                    "fingerprints": shard_fingerprints(s),
                } for s in arm_shards
            },
        }
        if arm.state == "aborted":
            worst = 1
        for s in arm_shards:
            if s.returncode not in (0, None) and not s.early_stopped:
                worst = 1
    path = out / "increment_summary.json"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nincrement summary written to {path}", flush=True)
    return worst


def print_plan(args: argparse.Namespace, arms: list[Arm],
               shards: list[Shard], smoke: list[Shard]) -> None:
    print("increment A/B plan")
    for arm in arms:
        print(f"  arm {arm.name}: commit={arm.commit} groups={arm.groups or '-'} "
              f"tree={arm.tree}")
    mode = ("reuse (--skip-build)" if args.skip_build
            else f"copy from donor {args.engine_donor}" if args.engine_donor
            else "make.cmd all")
    print(f"  engine: {mode}; then dotnet build CameoMod.sln -c Release "
          f"(DOTNET_ROLL_FORWARD=LatestMajor)")
    for s in smoke:
        print(f"  smoke {s.label}: {' '.join(str(c) for c in s.argv[2:])}  (cwd={s.cwd})")
    for s in shards:
        print(f"  shard {s.label}: {' '.join(str(c) for c in s.argv[2:])}  (cwd={s.cwd})")
    print(f"  schedule: at most {args.max_instances} OpenRA.exe machine-wide "
          f"(+{args.spawn_grace}s launch credit), early-stop poll every {args.poll_seconds}s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ctrl", required=True, help="previous-master commit for the ctrl arm")
    parser.add_argument("--cand", required=True, help="candidate commit for the switch arms")
    parser.add_argument("--groups", default="all",
                        help="applier groups for the 'all' arm (default: all)")
    parser.add_argument("--half-groups", default="A_squad_tactics",
                        help="applier groups for the 'half' arm (default: A_squad_tactics)")
    parser.add_argument("--arms", default=",".join(ARM_NAMES),
                        help="comma subset of ctrl,half,all (default: all three)")
    parser.add_argument("--out", type=pathlib.Path, required=True,
                        help="run directory: trees/, <arm>_<faction>/ shard dirs, increment_summary.json")
    parser.add_argument("--factions", default="td_gdi,td_nod",
                        help="comma-separated factions, ONE SHARD EACH — never one "
                             "comma'd batch (default: td_gdi,td_nod)")
    parser.add_argument("--bot-a", default="hard", help="candidate bot type (default: hard)")
    parser.add_argument("--bot-b", default="classic", help="reference bot type (default: classic)")
    parser.add_argument("--repeats", type=int, default=8,
                        help="matches per mirror shard; x2 factions = per-arm total (default: 8)")
    parser.add_argument("--time-limit", type=int, default=3,
                        choices=sorted({0, 1, 2, 3, 4, 6, 9}))
    parser.add_argument("--stall-timeout", type=int, default=400,
                        help="forwarded to run_ai_match_batch (default: 400)")
    parser.add_argument("--shard-retries", type=int, default=2,
                        help="relaunch a full shard whose driver exits before its plan "
                             "is played out, into a fresh <support>_rN dir; results pool "
                             "across dirs (default: 2, matching supervisor rounds)")
    parser.add_argument("--max-instances", type=int, default=3,
                        help="machine-wide OpenRA.exe cap, ours + foreign "
                             "(default: 3 — maintainer ruling 2026-10-01)")
    parser.add_argument("--spawn-grace", type=float, default=120,
                        help="seconds a launched shard counts against the cap before "
                             "its OpenRA.exe can appear in tasklist (default: 120)")
    parser.add_argument("--poll-seconds", type=float, default=60,
                        help="early-stop evaluation interval (default: 60)")
    parser.add_argument("--engine-donor", type=pathlib.Path, default=None,
                        help="checkout (or engine dir) to copy engine/ from instead of make.cmd all")
    parser.add_argument("--skip-build", action="store_true",
                        help="reuse already-prepared trees (switches still re-applied)")
    parser.add_argument("--smoke", action="store_true",
                        help="run one verified match per arm before the full shards")
    parser.add_argument("--dry-run", action="store_true",
                        help="print trees, shard commands and the schedule; launch nothing")
    return parser


def main() -> int:
    # Windows consoles default to cp1252; a shard label with a non-ASCII character crashed the driver before any launch.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args()
    args.out = args.out.resolve()
    arms, shards, smoke = build_plan(args)
    validate_groups(args, arms)
    for arm in arms:
        arm.commit = resolve_commit(arm.commit)
    print_plan(args, arms, shards, smoke)
    if args.dry_run:
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    for arm in arms:
        provision_arm(arm, args)

    decided: dict[tuple, dict] = {}
    if smoke:
        print("\n=== smoke: one match per arm ===", flush=True)
        drive(list(smoke), args)
        for arm in arms:
            shard = next(s for s in smoke if s.arm == arm.name)
            ok, detail = smoke_verified(shard.support)
            if ok and shard.returncode == 0:
                arm.smoke_detail = f"ok: {detail}"
                print(f"[smoke] {arm.name}: PASS ({detail})", flush=True)
            else:
                arm.state = "aborted"
                arm.smoke_detail = f"FAILED: {detail}; exit={shard.returncode}"
                print(f"[smoke] {arm.name}: FAILED — arm aborted "
                      f"({detail}; exit={shard.returncode})", flush=True)

    aborted = {a.name for a in arms if a.state == "aborted"}
    live_shards = [s for s in shards if s.arm not in aborted]
    skipped = [s for s in shards if s.arm in aborted]
    for s in skipped:
        s.done = True  # arm aborted in smoke: its shards never enter the queue
    print(f"\n=== full shards: {len(live_shards)} queued "
          f"({len(skipped)} skipped on smoke-aborted arms) ===", flush=True)
    drive(live_shards, args, stop_ctx=(arms, shards, decided))

    return summarize(args.out, arms, shards, smoke, args, decided, started)


if __name__ == "__main__":
    sys.exit(main())
