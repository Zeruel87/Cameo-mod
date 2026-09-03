---
description: Full task pipeline — read docs, do the work, verify, and prepare a reviewable commit (never auto-push)
---

# Task pipeline (run this shape for every task, big or small)

## 1. Start — load context (never skip, even for "small" tasks)

Read, in this exact order (see `docs/README.md` for the canonical definition):

1. `CLAUDE.md` (repo root)
2. `docs/LESSONS_LEARNED.md`
3. `docs/AGENT_WORKSPACE.md`
4. `docs/HANDOFF.md`  ← the entry point: current state + priority queue
5. `docs/DESIGN.md`
6. `docs/design/ROADMAP.md`
7. `docs/audit/SUMMARY.md`
8. Then the relevant topic doc(s) for the task at hand (table in `docs/README.md`).

If chat memory, old notes, or a prior session's assumptions conflict with these documents, the documents win. Record any newly discovered crash/regression/discrepancy in `docs/design/ROADMAP.md` before implementing a fix.

## 2. Sync with remote before starting real work

// turbo
1. `git fetch --all`

2. Review incoming changes (`git log HEAD..origin/<branch> --oneline`); if there are any, `git pull`/merge before proceeding. Resolve conflicts before continuing. Never let local work silently diverge from a co-maintainer's changes.
3. If `mod.config`'s `ENGINE_VERSION` changed as part of the merge, follow the engine update pipeline in `docs/LESSONS_LEARNED.md` (rebuild via `make.cmd all` before boot-gating).

## 3. Do the implementation work

- Prefer minimal, root-cause fixes (see global bug-fixing discipline).
- For bulk/mechanical changes, write or reuse a script under `tools/` rather than hand-editing many files — but verify its output structurally (see `docs/LESSONS_LEARNED.md` § Bulk YAML rename scripts for the corruption classes to avoid: blind substring/word-boundary substitution, namespace collisions, comment-style mismatches).
- Run the relevant targeted audit(s) (`tools/audit/audit_<name>.py`) as you go, not just at the end.

## 4. Verify before commit — the mandatory pre-commit gate

1. Update ALL affected documentation FIRST: `docs/design/ROADMAP.md`, `docs/DESIGN.md`, `docs/audit/SUMMARY.md`, `docs/LESSONS_LEARNED.md`, and regenerate `docs/audit/latest/*.md` reports touched by the change. A change without updated docs is incomplete.
2. Run the targeted audit(s) for the change, then the full suite when practical: **`bash tools/audit/run_all.sh`** — the canonical runner. `tools/audit/run_all.py` is a port for shells without `sh` and reads its audit list out of the `.sh`, so the two cannot drift. **Never a PowerShell `>` redirect**: it writes UTF-16 and corrupts every report. `docs/audit/latest/` is only written from a COMPLETE tree (`engine/` built, clone not shallow); anywhere else the suite still runs but writes to the untracked `docs/audit/degraded/` and says why, because an incomplete tree reports FEWER findings and still says PASS.
3. **Build**: run `make.cmd all` (fetches/rebuilds the engine + mod). Zero errors required. If C# sources changed, this step is mandatory — stale DLLs crash the boot with `Cannot locate type: …Info`.
4. **Boot-gate (never skip, never fake)**: snapshot the current file list in `%APPDATA%/OpenRA/Logs` (or use `boot-test.cmd`, which launches the game for ~30s and can be inspected afterward), then launch the game (`launch-game.cmd` or `boot-test.cmd`). Confirm:
   - `perf.log` ends with `MenuPostProcessEffect.PostWorldLoaded` (reached the main menu), and
   - no NEW `exception-*.log` files appeared, and
   - `debug.log` has no new `Exception`/`not found`/`FATAL` lines from this run.
   If the boot-gate fails, fix the regression and repeat this entire verification step — do not commit a broken boot. If Windows Smart App Control blocks a local build, see `docs/LESSONS_LEARNED.md` § Smart App Control for the four documented workarounds — never silently skip the gate, and record the SAC state in the commit message if a workaround was needed.

## 5. Commit — for review, never auto-push

1. Stage ONLY the files belonging to this change with a scoped `git add <files>` — never `git add -A` (the maintainer usually has other live uncommitted edits).
2. Write a self-explanatory commit title/body (no internal jargon like "Phase 5" or "A2 audit" without pointing to where it's defined — see `docs/AGENT_WORKSPACE.md` git rules).
3. Commit locally. **Do not push and do not open a PR unless the user explicitly asks for it** — the commit sits locally for the user to review first.
4. Tell the user: what changed, what was verified (audits + boot-gate result), and any known follow-ups or deferred items, so they can review the commit before deciding to push.
