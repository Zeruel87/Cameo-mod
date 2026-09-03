#!/usr/bin/env python3
"""run_pipeline.py — the single entry point for the balance pipeline.

`BALANCE_PIPELINE.md` §0 defines the loop as nine numbered steps plus two extra
proposal steps for a class rebalance. Every step already has a tool. What did not
exist was anything that runs them **in the documented order**, so the order lived in
prose and in whoever had read it most recently — which is how a commit lands with the
yaml moved and the ledger not re-extracted, and `audit_balance_drift` finds it later.

This runs the loop and stops where the law says to stop.

    python tools/balance/run_pipeline.py                 # verify: writes nothing
    python tools/balance/run_pipeline.py --extract       # + refresh the ledgers
    python tools/balance/run_pipeline.py --workbook      # + rebuild the workbooks
    python tools/balance/run_pipeline.py --determinism   # + extract twice and compare
    python tools/balance/run_pipeline.py --faction ra1_soviets

WHAT IT DELIBERATELY WILL NOT DO
================================

It never calls `apply_balance.py --confirm`, and there is no flag that makes it.

That is not timidity, it is the approval gate: CLAUDE.md rule 3 puts `--confirm`
behind an explicit maintainer order, and a wrapper that can reach it turns "a human
decided" into "a script was run". When the verify stage is clean the runner prints the
exact command to type; typing it stays the maintainer's act.

The same reasoning bars a `--yes`-style escape. An approval gate a tool can open on
its own is not a gate.

EXIT CODE
=========

The runner's exit code is the worst stage result, and a stage's result is that
subprocess's real return code. It is never the exit code of an `echo` that happened to
follow it — that mistake once had the suite reported green for a week while it was
exiting 1 on every run (`HANDOFF.md` §3.0c).
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "audit"))
import environment  # noqa: E402  (must follow the sys.path insert)

PYTHON = sys.executable

# Force UTF-8 out of every child regardless of the console codepage. A Windows console
# defaults to cp1252 and silently writes `—` as 0x97, which is how a tracked report
# ended up not being valid UTF-8 (CLAUDE.md rule 8).
CHILD_ENV = dict(__import__("os").environ, PYTHONIOENCODING="utf-8")


class Stage:
    """One documented step: what it is, what it runs, and whether it may write."""

    def __init__(self, step: str, name: str, cmd: list[str], *, writes: bool = False,
                 blocking: bool = True):
        self.step, self.name, self.cmd = step, name, cmd
        self.writes, self.blocking = writes, blocking
        self.code: int | None = None
        self.skipped = ""


def plan(args) -> list[Stage]:
    """The stages, in BALANCE_PIPELINE.md §0 order.

    Steps 2, 4 and 6 are human steps — edit the ledger, tune the sheet, order the
    apply. They are not automatable by definition, so they appear in the report as
    gaps rather than being silently skipped.
    """
    fac = ["--faction", args.faction] if args.faction else []
    stages = [
        Stage("7", "drift: yaml vs committed ledger",
              [PYTHON, "tools/balance/extract_stats.py", "--check", *fac]),
        Stage("8", "multiplier modifiers are integer percentages",
              [PYTHON, "tools/audit/audit_multiplier_modifiers.py"]),
        Stage("-", "balance-drift audit (the run_all gate)",
              [PYTHON, "tools/audit/audit_balance_drift.py"]),
        Stage("-", "generator reproduces every ^Warhead_ family",
              [PYTHON, "tools/balance/verify_generator_sync.py"]),
        Stage("-", "no empty warhead types (the boot-NRE class)",
              [PYTHON, "tools/audit/find_empty_warhead.py"]),
    ]
    if args.extract:
        # ⚠ Step 1 runs AFTER the step-7 drift check, not before it. `--check`
        # re-extracts in memory and diffs against the ledger ON DISK, so extracting
        # first overwrites the very thing the check compares against and the check
        # can never fail. Running the check first answers the question that matters —
        # "was the ledger stale?" — and the extract then fixes it.
        stages.insert(1, Stage("1", "extract: yaml -> raw + derived ledgers",
                               [PYTHON, "tools/balance/extract_stats.py", *fac],
                               writes=True))
        # A stale ledger is precisely what --extract exists to repair, so the check
        # reports it without failing the run. Every stage after the extract still gates.
        stages[0].blocking = False
    if args.workbook:
        stages.append(Stage("3", "build the faction/type workbooks",
                            [PYTHON, "tools/balance/build_workbook.py"], writes=True))
    if args.determinism:
        # Opt-in: it extracts twice, so it costs roughly two full runs. Last, because
        # it answers "is the compiler property holding" rather than "is the tree sane",
        # and there is no point asking that of a tree that already failed a gate.
        stages.append(Stage("-", "determinism: same inputs, same ledgers",
                            [PYTHON, "tools/balance/check_determinism.py", *fac]))
    return stages


def run(stage: Stage, dry: bool) -> None:
    if dry:
        stage.skipped = "dry-run"
        return
    stage.code = subprocess.run(stage.cmd, cwd=ROOT, env=CHILD_ENV).returncode


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--extract", action="store_true",
                    help="refresh docs/balance/*.json from yaml (writes tracked files)")
    ap.add_argument("--workbook", action="store_true",
                    help="rebuild the faction/type workbooks (writes tracked files)")
    ap.add_argument("--faction", help="ledger-name substring filter")
    ap.add_argument("--determinism", action="store_true",
                    help="also extract twice under different hash seeds and compare "
                         "(costs two full extractions)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan and run nothing")
    args = ap.parse_args()

    print("# balance pipeline\n")

    reasons = environment.incomplete()
    if reasons:
        print("⚠ **Incomplete environment.** These stages read only tracked files and are")
        print("unaffected, but a full `run_all.sh` from this tree would under-report:\n")
        for r in reasons:
            print(f"  * {r}")
        print()

    stages = plan(args)
    for s in stages:
        run(s, args.dry_run)

    print("| step | stage | writes | result |")
    print("|---|---|---|---|")
    worst = 0
    for s in stages:
        if s.skipped:
            result = f"_{s.skipped}_"
        elif s.code == 0:
            result = "PASS"
        else:
            result = f"**FAIL ({s.code})**"
            if s.blocking:
                worst = max(worst, s.code or 1)
        print(f"| {s.step} | {s.name} | {'yes' if s.writes else 'no'} | {result} |")

    print("\n## Steps this cannot do for you\n")
    print("| step | why |")
    print("|---|---|")
    print("| 2 · edit the ledger | a balance decision, not a transformation |")
    print("| 4 · tune Cost in the sheet | same |")
    print("| 5 · import the sheet | only meaningful after step 4; "
          "`import_workbook.py --workbook faction\\|type` |")
    print("| 6 · apply to yaml | **the approval gate** — see below |")

    if args.dry_run:
        print("\n_Dry run: nothing was executed._")
        return 0

    print()
    if worst:
        print(f"**FAIL** — the pipeline is not in a state to propose from. Fix the "
              f"failing stages above first; a target computed on a tree whose ledger "
              f"already disagrees with its yaml is a target for a game that does not "
              f"exist.")
        return worst

    print("**PASS** — yaml and the ledger agree, and the structural gates are clean.\n")
    print("Applying is the maintainer's act, not this runner's. When a target has been")
    print("written into the ledger and signed off (W11), the command is:\n")
    fac = f" --faction {args.faction}" if args.faction else " --faction <name>"
    print(f"    python tools/balance/apply_balance.py{fac} --confirm\n")
    print("then re-run this to verify, run `bash tools/audit/run_all.sh`, and boot-gate")
    print("before committing the yaml and the ledger together.")
    print("\n⚠ Signed-off class anchors today: check `docs/balance/class_anchors.json`. "
          "While that count is 0, `--confirm` is a no-op and no price in the tree is final.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
