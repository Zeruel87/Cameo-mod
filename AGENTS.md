# Cameo shared agent entry point

Read `docs/AGENT_WORKSPACE.md` for the canonical coordination design and its activation status.
The Project is preparatory until the three developers agree to activate the pilot. Current human
task instructions remain controlling; this proposal does not revoke existing assignments.
Provider files add technical context and should point here for collaboration procedure.

## Start every task

0. **Read `docs/WORKFLOW.md` — the standing operating rules (binding, maintainer 2026-10-01):** plan first; the
   coordinator (Claude) is the only one who merges and runs A/B tests; Devin agents code on branches and hand in
   "INC-N ready: <branch>@<hash> — switch: <name>"; work goes into increments, not per-PR tests; ≤ 3 game drivers on
   the machine; boot gates launch `OpenRA.exe` directly; minimum tokens (read sections, script sweeps, short notes).
1. Read `docs/TASK_INDEX.md`, then the exact sections and existing tools it routes for the task.
2. Inspect the current checkout, branch, remotes, worktrees, open task record, and related pull
   requests before deciding that work is missing.
3. Treat repository source and current generated evidence as stronger than chat, agent memory,
   dated orders, or old handoffs. Correct stale summaries instead of following them.
4. Verify the human-authorized outcome and scope before editing. During the active pilot, record
   the approved claim as described in `docs/AGENT_WORKSPACE.md`.

## Live task and claim state

- The organization GitHub Project and its linked issue or draft item are the live task ledger once
  the workflow is activated. `docs/HANDOFF.md` and `docs/design/ROADMAP.md` retain project context
  and priorities; they do not grant a write claim.
- A Project item is a coordination record, not an atomic lock. Aedis's designated coordinator
  agent approves task claims and reviews work. Blackrobe takes over when that agent runs out of
  quota. Record the active approver and explicit takeover/handback per `docs/AGENT_WORKSPACE.md`.
- Each outcome has one task record, human owner and current approver. Each independent writer has its
  own branch and isolated worktree; research-only tasks need no branch or pull request.
- Record the provider/session identity, base commit, exact writable paths, excluded paths,
  dependencies, acceptance evidence, runtime impact, and an explicit claim-expiry timestamp.
- Expiry never transfers ownership automatically. The current approver must release or reassign a stale
  claim after inspecting its branch, commits, worktree, and handoff evidence.
- Read-only investigation may overlap. Write scopes may not. Stop and contact the current approver when
  scopes overlap or the task record is missing, stale, or ambiguous.

Do not infer activation from the existence of a Project or issue form. The team must record its
go-live decision in `docs/AGENT_WORKSPACE.md` and the Project README.

## Git and worktree isolation

- Never perform agent work in another person's dirty checkout or another task's worktree.
- Create an isolated worktree from the approved base ref. Re-check the base and active claims
  immediately before the first edit.
- Use a provider-prefixed branch containing the task number and subject, such as
  `codex/123-fix-description` or `claude/123-fix-description`.
- After activation, for tasks migrated into the Project, and after the current approver approves a
  write claim, create an empty claim commit and push the
  branch ref to the agreed remote. A local branch name alone is not a verifiable claim. If push
  authorization or connectivity is missing, remain read-only and record the blocker.
- Stage named paths only. Never broadly stage, reset, clean, restore, rebase, delete, or move work
  that may belong to another person or agent.
- Keep each branch to one sentence-worth of purpose. Before an overnight handoff, publish a draft
  pull request or provide a recoverable commit/patch reference as authorized by the human owner.
- Aedis's designated agent (or Blackrobe during quota fallback) approves technical readiness
  within the human-authorized scope. An agent may execute an explicitly authorized merge, but
  cannot expand that authority or infer it from green checks. Preserve explicit
  HOLD, no-merge, and review-only instructions.

## Engine and validation boundaries

- Treat `engine/` as a fetched build input, not the authoritative engine repository. Engine source
  changes belong in the separate `cameo-mod/OpenRA` repository and require their own task and pull
  request before a Cameo engine-pin update.
- Never change `mod.config`, `ENGINE_VERSION`, or `engine/VERSION` without explicit maintainer
  authorization and a verified upstream engine commit.
- Follow the validation and engine procedure in `docs/AGENT_WORKSPACE.md`, using technical checks
  routed by `docs/TASK_INDEX.md`. State what was proven statically, by build/boot, and in game.
- Do not claim gameplay or visual approval from static checks. The human maintainer makes the final
  gameplay and visual call.
- Do not run `--check-yaml` or `make test` (which invokes it). Continuous Integration is disabled
  in GitHub; use relevant local validation and human review. Do not enable or replace CI unless
  a human explicitly requests it. CI is not a coordination-pilot activation prerequisite.

## Handoff and communication

- Put binding decisions in their canonical repository document and implementation evidence in the
  linked pull request. Use the task item for ownership and status only.
- Report milestones, blockers, decisions needed, and completion receipts. Do not stream internal
  reasoning or duplicate the same status across documents and chat systems.
- Discord, MCP, ACP, AionUI, and provider-native agent teams are optional interfaces. They do not
  override the GitHub task record, grant write scope, or authorize a merge.
- Never place tokens, SSH details, private conversation text, or other credentials in public task
  records, pull requests, logs, or repository files.
