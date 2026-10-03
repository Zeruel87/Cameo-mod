# Cameo-mod — core rules (loaded every session; keep it short)

**Full text of every rule below: [`docs/AGENT_CONTRACT.md`](docs/AGENT_CONTRACT.md)** (moved verbatim 2026-10-01 to cut
the always-loaded context — the rules did not change). Rule numbers are stable: tools cite "CLAUDE.md rule N".

**Don't trust, verify:** the artifact (data, file, tool output, boot) beats any summary; then fix the stale summary.
**Before any task:** find its row in `docs/TASK_INDEX.md` (the doc SECTION to read + the tools that already exist).
Reading order (canonical: `docs/README.md`): `docs/LESSONS_LEARNED.md` → `docs/AGENT_WORKSPACE.md` → **`docs/HANDOFF.md`**
→ `docs/DESIGN.md` → `docs/design/ROADMAP.md` → `docs/audit/SUMMARY.md`. Read SECTIONS, not whole files.
Weapon work: also `docs/design/WEAPON_3WAY_SPLIT.md`, `WEAPON_TYPE_SYSTEM.md`, `BALANCE_PROGRAM_PLAN.md` §0a, `SPREAD_FALLOFF_PLAN.md`.
Dated handoffs in `docs/history/handoffs/` are provenance only, never status.

## The rules (1–2 hook-enforced)
1. **Boot-gate every commit of engine content** — the game reaches the main menu (`perf.log` shows
   `MenuPostProcessEffect.PostWorldLoaded`), no new `exception-*.log` (snapshot the list first).
2. **Scoped `git add <files>` only** — never `-A` / `.` / `--all`; never `git stash` or `checkout -- .` (shared tree).
3. **Never hand-edit a balance number** — `extract_stats` → ledger → `apply_balance --confirm` (maintainer order).
4. **`Versus` lives only in `^Warhead_*` templates**; never change a warhead / `Burst` / `BurstDelays` without permission.
5. **Weapon 3-way split preserves resolved behaviour**; `find_empty_warhead.py` = 0; verify with `review_resolve_diff.py`.
6. **One owner per file-set** (`BALANCE_PROGRAM_PLAN.md` §2): check `git log -3 <file>` + mtime before editing.
7. **Rebuild C# before boot** (`DOTNET_ROLL_FORWARD=LatestMajor dotnet build -c Release --nologo -p:TargetPlatform=win-x64`).
   `engine/` is NOT in this repo (gitignored build output): engine changes go through the `cameo-engine` clone + the
   `mod.config` pin (LESSONS_LEARNED "canonical engine update pipeline") — first try a mod-side SHADOW type.
8. **Audit reports regenerate only via `bash tools/audit/run_all.sh`, only from a complete tree** (engine built, not shallow).
   8b. The engine **drops unknown yaml fields silently** — run `audit_dead_warhead_fields.py`; verify field names exist.
   8c. A "derive unless overridden" default is invisible when upstream always overrides — assert the DERIVED value.
   8d. Every warhead family is unique (`audit_family_uniqueness.py`); radius = (N-1) x Spread; `splice_templates.py --all`.
   8e. **Never hand-parse yaml** — `miniyaml.Ruleset.resolve*`, `weapon_efficiency.versus_of`; a result contradicting a law is a bug.
   8f. **Grep `docs/DESIGN.md` before designing anything** (§12.0h MEAN-100, §12.0c Shield, §12.0d class tilt are ruled).
   8g. **An override is a cancellation** — keep `-Key@X:` unless no ancestor defines it; `RESOLVE-VERIFIED`; `audit_shrapnel_chains.py`.
   8h. **A rename breaks maps** — `audit_map_actors.py` after every rename batch.
9. **Underscore-only naming** — no hyphens in ids, files, fluent keys.
10. **Sign as yourself:** `Co-Authored-By: Claude <your real model> <noreply@anthropic.com>`; other agents use their own
    trailer (e.g. `Co-Authored-By: Devin AI <devin@cognition.ai>`). Never copy a trailer from history.

## How we work (maintainer rulings 2026-10-01)
* **Increments, not per-PR A/Bs** (AI_MASTER_PLAN §1.2 step 6): every agent's work is merged into one increment that
  lands on master (behaviour behind switches), then ONE A/B with `tools/ai/apply_increment_switches.py`.
  **A/B = mirror matches only** (`--factions td_gdi` and `--factions td_nod` as separate shards) until the rebalance.
* **⛔ STANDING WORKFLOW — [`docs/WORKFLOW.md`](docs/WORKFLOW.md), binding in every session, every agent (maintainer
  2026-10-01: "survive this project with minimum tokens"):** **plan first**, then delegate — **Opus plans, specs,
  reviews, merges; Sonnet sub-agents (`model: sonnet`, background) write the code** in prepared worktrees (engine
  copied — git worktrees have no `engine/`) and never commit; resume a sub-agent with SendMessage; never delegate tiny
  edits. Read sections not files, scripts over reading, short replies, wait in the background — never poll.
  **Only Claude merges and runs A/B tests**; Devin agents only code (hand in "INC-N ready"). Machine: ≤ 3 game
  drivers, `--render fast`, stop the newest game if the PC slows. Boot gates run `OpenRA.exe` directly; rebuild after
  every branch switch.
* **Balance:** the pipeline only; damage grid `formula.DAMAGE_STEP = 10`; `FirepowerMultiplier` is retired (W17).
* **Memory is provenance, not authority** — promote anything binding into DESIGN / LESSONS_LEARNED / `doc_claims.yaml`.
* **Mission:** dynamic faction loading via self-contained ContentPacks (`docs/MIGRATION.md`). Work queue:
  `docs/design/ROADMAP.md` + `docs/design/AI_MASTER_PLAN.md` §3. Engine/C# reference: `docs/Cameo_Knowledge_Base_Manual.md`.
