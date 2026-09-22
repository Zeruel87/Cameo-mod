# Shared Agent Workspace

This repository is the shared source of truth for maintainers and every AI agent. Do not create a second roadmap, audit tree, or design contract outside this repository.

## Source-of-truth map

| Need | Canonical location | Rule |
|---|---|---|
| Lessons learned / start protocol | `docs/LESSONS_LEARNED.md` | Read before every new task: accumulated pitfalls and safe defaults. (It carries a convenience copy of the reading order; `docs/README.md` is the canonical one.) |
| **Entry point: current state + priority queue** | `docs/HANDOFF.md` | The single handoff. Supersedes every dated one in `docs/history/handoffs/`; never resume from those. |
| Short project orientation | `docs/README.md` | One page for a first-time reader; every document above is authoritative over it. |
| Current work queue | `docs/design/ROADMAP.md` | Crashes and player-visible bugs are P0 and always jump the queue. Add new issues here before implementation. Closed July items live in `docs/history/ROADMAP_ARCHIVE_2026-07.md`. |
| Balance board, ownership, acceptance criteria | `docs/design/BALANCE_PROGRAM_PLAN.md` | W1–W26, file-set ownership (§2), and the binding order of operations (§0a). |
| Numeric claims that must not rot | `docs/audit/doc_claims.yaml` | Every number a DECISION rests on, with its re-measure command. Update `value` AND every doc under `docs:` in the same commit. |
| Binding rules and conventions | `docs/DESIGN.md` | Read before modifying YAML, assets, naming, weapons, balance, or descriptions. |
| Engine and custom-trait reference | `docs/Cameo_Knowledge_Base_Manual.md` | Consult before changing unfamiliar traits or C#-backed behavior. |
| Audit overview | `docs/audit/SUMMARY.md` | Read first for known issue classes and current audit status. |
| Detailed audit findings | `docs/history/audits/BASELINE_FINDINGS.md`, `docs/audit/CONSISTENCY_REPORT.md` | Update only from evidence produced by a current audit or engine boot. |
| Audit scripts | `tools/audit/` | Scripts are reusable tooling; do not duplicate them into personal-agent folders. |
| Generated audit output | `docs/audit/latest/` | Regenerate via `tools/audit/run_all.sh`; it is the current evidence set. |
| Baseline audit evidence | `docs/audit/baseline/` | Historical comparison only. |
| Faction reference | `docs/FACTIONS.md`, `docs/factions/MATRIX.md` | Use for display-name, faction-role, roster, and documentation checks. |
| Migration process | `docs/MIGRATION.md` | Use for naming, actor splits, asset movement, and Fluent migrations. |
| External-agent historical evidence | `docs/history/LEGACY_DEVIN_CABAL.md` | Historical register only. No external output is current until rerun in this repository. |
| Archived handoffs | `docs/history/handoffs/` | Dated session records. Provenance only — **never** resume work from one. |

## Live agent roster — WHO IS ON WHAT (update your own row before you start)

⛔ **This table is the shared identity board. Add or update YOUR OWN row and never rewrite
someone else's.** Agents forget their own names between sessions, which is why the local fleet
also keeps a `.agent-id` file on disk; this table is the repository-side copy so the maintainer
and every other agent can see the same picture without asking. If your row is stale, fix it.

| Agent | Model / host | Branch | File-set it owns | Status |
|---|---|---|---|---|
| **Claude-Local** | Opus 5, local CLI | `claude/weapon_inherit_audit_and_map` | the REFERENCE pipeline: `tools/balance/{assign_references,reference_targets,reference_distribution,reference_coverage,build_reference_report,faction_routes}.py`, `tools/reference/variant_pool.py` | ACTIVE 2026-09-13 |
| **Codex (Astra)** | GPT-6, Blackrobe's host | `codex/recovery-pr345-merge-20260912`, `codex/overnight-integration-20260910` | INI/DTA extraction, evidence gates, the four-faction review pipeline, `tools/tests/` | ACTIVE 2026-09-13 |
| Devin — Aurora | Devin AI | `devin/aurora/lane*` | AA range/audit lanes, extractor cargo | idle since 2026-09-08 |
| Devin — Ember | Devin AI | `devin/ember/consortium-*` | Steel Consortium W24 stacks, class templates | idle since 2026-09-08 |
| Devin — Nova | Devin AI | `devin/nova/*` | naming sweeps, AreaDamage class-2d, dead-field scales | idle since 2026-09-06 |

**Signing rule (restating `CLAUDE.md` rule 10 because it keeps being got wrong):** sign with your
OWN identity and your REAL model name. Claude Opus 5 signs `Co-Authored-By: Claude Opus 5
<noreply@anthropic.com>`; Devin signs `Co-Authored-By: Devin AI <devin@cognition.ai>`; Codex signs
as itself. Never copy a trailer from a previous commit — a version pinned anywhere goes stale the
moment the model changes, and copying it makes a newer model misreport itself as an older one.

### Branch hygiene, measured 2026-09-13

⚠ **Ahead-count is not work-count, and reading it as one wastes a day.** `master` took PR #345 as
a SQUASH (`b235c6980`), so every branch that contributed to it now shows its own commits as
"ahead" even though the CONTENT landed. Verify by content, never by `git merge-base`:

    git show origin/master:<file> | grep -c "<the thing you added>"

Four `claude/*` branches from 2026-09-11 are in exactly that state — `refmap_damage_tick_fix`,
`fix_peer_armament_selection`, `playtest_baseline`, `cl01_target_payload_review`. Their content IS
in master (`sources used` present, DTA `$Inherits` present) and `is_upgrade_gated` is correctly
ABSENT because its own author reverted it. **They are landed and can be closed.**

## Required operating sequence

1. Read in this order before touching rules or assets: `docs/LESSONS_LEARNED.md` → this file → `docs/HANDOFF.md` → `docs/DESIGN.md` (the sections your change touches) → `docs/design/ROADMAP.md` → `docs/audit/SUMMARY.md`, then the relevant section of `docs/Cameo_Knowledge_Base_Manual.md`. **`docs/README.md` defines that order and wins over any copy of it, including this one.**
2. Record a newly discovered crash, regression, or suspected discrepancy in `docs/design/ROADMAP.md` before proposing a fix.
3. Treat release builds, engine logs, resolved-ruleset diffs, and current audit output as evidence. Do not promote an old raw `.txt` result to a live finding without rerunning its audit.
4. For refactors, compare `tools/audit/dump_resolved.py` output before and after (for a single weapon conversion, `tools/audit/review_resolve_diff.py`). For content changes, run the targeted audit first and the full suite when practical.
5. Before every commit, boot-gate with `launch-game.cmd` — launch the game, wait for the main menu (perf.log ends with `MenuPostProcessEffect.PostWorldLoaded`), kill the process, then check for NEW `exception-*.log` files in `%APPDATA%/OpenRA/Logs`. Fix any crashes before committing. Stage only the files belonging to the change. **SAC note**: If Windows Smart App Control (Enforcement mode) blocks the boot-gate, see `docs/LESSONS_LEARNED.md` § Smart App Control for four options to enable testing (EA cache workaround, Evaluation mode via WinRE, VM, or code signing). Never silently skip the boot-gate — record the SAC state in the commit/PR description.
6. `utility.cmd cameo --check-yaml` is a **linting/YAML validation tool**, NOT a boot-gate substitute. Use it for: verifying cosmetic refactors (actor/template renames), checking broken prerequisites, and detecting gameplay-relevant YAML issues. **Goal: 0 errors AND 0 warnings.** The utility takes a VERY LONG TIME (10+ minutes) — only run it when you have completed ALL connected tasks from the last report and expect 0 errors/warnings to confirm. Do NOT run it repeatedly. Keep findings from the last report in ROADMAP and docs so they can be fixed without re-running. It is ABSOLUTELY NECESSARY — just choose wisely WHEN to run it.
7. After any bulk YAML lint cleanup, run `python tools/audit/audit_nuclear_flash_bindings.py`. It resolves the active `mod.yaml` graph and blocks removal of the RA1, Ixian, or CABAL directional flash warhead. The full audit suite includes the same check.

## Git workflow and commit rules (binding, 2026-07-24)

**Multiple developers and agents work on this repository.** Committing identities seen in the
log: **AedisToru** (maintainer — also lands most agent work under the shared repo identity),
**Blackrobe** (co-maintainer), **Elpollo315**, **Zan Yewang**, **Devin AI**. Because the git
author is often the shared identity, the `Co-Authored-By:` **trailer** is the only reliable
record of which agent wrote a change — see CLAUDE.md rule 10.

1. **Always fetch, pull, and merge before any commit.** The remote may have changes from other developers. If the engine pin (`mod.config` `ENGINE_VERSION`) changed, always run `make all` to fetch and build the new engine before boot-gating. Never skip the boot-gate.
2. **Always boot-gate before committing.** Launch the game with `launch-game.cmd`, wait for the main menu (perf.log ends with `MenuPostProcessEffect.PostWorldLoaded`), kill the process, then check for NEW `exception-*.log` files in `%APPDATA%/OpenRA/Logs`. A commit that breaks the boot is not acceptable. (`utility.cmd cameo --check-yaml` is a separate linting tool — see step 6 above.) **If SAC blocks the boot-gate**, see `docs/LESSONS_LEARNED.md` § Smart App Control for options; record the SAC state in the commit/PR description.
3. **Always update ALL relevant documentation files BEFORE committing.** This includes `docs/design/ROADMAP.md`, `docs/DESIGN.md`, `docs/audit/SUMMARY.md`, `docs/LESSONS_LEARNED.md`, and any other docs affected by the change. Check old docs for outdated information, inconsistencies, and contradictions — fix them. A commit without updated docs is an incomplete commit.
4. **Do not spam commits on upstream master.** Use a pull request (PR) for cleaner commit history. Create a feature branch, push it, open a PR, and merge only after verification.
5. **Only merge a PR if either:** (a) you no longer detect regression caused by the changes, or (b) launching the game no longer results in a crash. Commits that do not break the master branch are a naturally acceptable outcome.
6. **Commit titles must be self-explanatory to all developers.** Terms like "Phase 5", "A2 audit", "Fix B5", or "X/Y law" are only understood internally by Aedis and their agent. If such internal pointers are necessary, elaborate where to find the definition (e.g. "see docs/audit/SUMMARY.md bug class B5") and what kind of project it links to.
7. **When a task is completely done, merge the feature branch to master.** Do not leave completed work stranded on a feature branch. Ensure boot-gate passes and docs are updated before merging.

## Documentation rules

- **Never use absolute local file paths in any repository document.** Always use relative paths from the repository root (e.g. `mods/cameo/rules/defaults.yaml`, not `C:\Users\...\mods\cameo\rules\defaults.yaml`). Other contributors and AI agents have different local paths. Absolute paths leak personal filesystem information and break on other machines.
- External personal folders are referenced by name only (e.g. "the external DevinCameoProject folder"), never by absolute path.

## Audit organization

- `tools/audit/`: executable detectors and shared parsing/model infrastructure.
- `docs/audit/latest/`: generated current reports; overwrite only by running the suite.
- `docs/audit/baseline/`: immutable-ish baseline snapshots.
- `docs/audit/`: human-maintained summaries, decisions, consistency records, and imported historical registers.
- External personal folders: scratch space only. They must link to this file and must not be treated as authoritative.

## Current incident protocol

For an engine crash or player-visible visual regression:

1. Preserve the exact exception and failing asset/actor/sequence.
2. Compare the affected actor, sequence key, asset filename, and tooltip/display references against the last known-good release.
3. Add an evidence-backed P0 item to `docs/design/ROADMAP.md`.
4. Do not modify unrelated palette, template, or naming data while root cause is unproven.
5. Verify with a boot test before considering the incident resolved.
