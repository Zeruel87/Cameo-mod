# Workflow — the standing operating rules (binding for every session and every agent)

Maintainer, 2026-10-01: *"Make this a standing rule that is always true and all agents will automatically follow,
so that we can survive this project with minimum tokens used with the utmost efficiency."* This file collects every
working rule ruled that day. `CLAUDE.md` (loaded into every Claude session) and `AGENTS.md` (every other agent) point
here; the SessionStart hook prints the pointer. Game/AI design rulings live in `docs/DESIGN.md` (§19.6–§19.9, §23).
Rules here change only by a maintainer ruling; record the quote and the date when one does.

## 1. Tokens first — plan, then delegate

1. **Plan before you build.** For any task bigger than a few edits, first write the plan (what changes, which files,
   what verifies it) and decide what to delegate. Planning is what makes delegation cheap.
2. **Opus (the coordinator) specs, reviews, merges. Sonnet sub-agents write the code.** Spawn sub-agents with
   `model: sonnet`, in the background, one per large self-contained task, several in parallel when independent.
   - Give each a **prepared worktree with the engine copied** (git worktrees have no `engine/`: `git worktree add`, then
     `robocopy <built>\engine <new>\engine /E`), exact files/anchors, acceptance tests, the commands to verify, and
     "do not commit, push, open PRs or launch the game". Ask for a report of ≤ 25 lines.
   - **Never delegate a 3-line edit** (a sub-agent re-reads its context cold; small jobs cost more delegated).
   - **Continue a finished sub-agent with SendMessage** for a follow-up (it keeps its context) instead of a new one.
   - **The coordinator reviews every diff** (today's reviews caught: a switch that would have changed `classic`, a
     scoring weight that inverted the maintainer's priority, a direct actor mutation that desyncs multiplayer).
3. **Read the minimum:** a doc SECTION via `docs/TASK_INDEX.md`, never whole files; grep before reading; the newest
   UPDATE block of the fleet orders only. Mechanical sweeps go into a script, never file-by-file reading.
4. **Wait without polling:** long jobs run in the background and wake you (a watcher loop or the job's own
   notification); never chain `sleep`s.
5. **Write short:** replies say what changed, what runs, what needs the maintainer. STATUS notes ≤ 15 lines with
   hashes; cite `path:line` and counts instead of pasting diffs or logs.
6. **Keep the always-loaded context small:** `CLAUDE.md` is a core (full text: `docs/AGENT_CONTRACT.md`); memory index
   lines stay one short line each.
7. **Checkpoint as you go — a session can be cut off at any moment** (maintainer 2026-10-03: *"always important to
   record everything in the handoff document and the development log … so that you can resume cleanly even when your
   tokens run out"*). After every milestone (sub-agent spawned, PR opened, ruling recorded) append 3–5 lines to
   `DEVELOPMENT_LOG.md` and refresh the `HANDOFF.md` "Next" line: worktree + branch, spec path (specs live in a file, not
   only in a prompt), open PRs, what is next. Recovering an uncheckpointed session from its transcript cost ~40 tool calls.
8. **Devin agents are free** (maintainer 2026-10-03: *"the 3 Devin agents will work for free so they are not limited to
   tokens"*): coding work that does not need the coordinator's tight review loop goes to NOVA / EMBER / DAWN through a
   fleet ORDERS file; Sonnet sub-agents are for work the coordinator must review inside the session.

## 2. Roles

* **Claude (Opus) is the coordinator:** the only one who **merges** to master, the only one who **runs A/B tests**,
  the integrator of increments, the reviewer of every PR. Maintainer decisions go to him as a question with 2–4 options.
* **Devin agents (NOVA, DAWN, EMBER) code:** branches + PRs only; no merges; no batches, smokes or leagues. Their only
  game launch is a boot gate (one instance, own PID, under the cap). Hand-in line in a STATUS note:
  `INC-N ready: <branch>@<hash> — switch: <name> (default off)` (or "no behaviour change"), with the fog audit run and
  its manifest + reasoning in the PR.
* **Sonnet sub-agents** are spawned by the coordinator for coding (§1.2).

## 3. Increments, not per-PR tests (AI_MASTER_PLAN §1.2 step 6, amended)

1. Every agent's open work goes into **one increment** (`inc/<date>[letter]`): merge each branch (`--no-ff`), resolve
   conflicts as a three-way merge (keep both behaviours), regenerate generated files (module map, fog manifest after
   review, Fransbot drift baseline), build, `dotnet test` (never `--no-build` after a branch switch), audits, boot gate.
2. **The increment lands on master** right away (master stays in sync with all branches). Every new behaviour sits
   behind a switch whose default keeps today's behaviour; anything `classic` shares (e.g. `UnitBuilderBotModuleCA@generic`,
   `BaseBuilderBotModuleCA@generic`) is switched only through a **genericbot-only provider** — classic never changes.
3. Switches are listed in `tools/ai/increment_switches.yaml` (groups) and applied to a FROZEN A/B tree by
   `tools/ai/apply_increment_switches.py` (refuses the main checkout). Verify every switch field exists on its trait
   Info (the engine drops unknown fields silently, CLAUDE.md 8b).
4. **Check for orphaned commits** before building an increment: a merged PR's branch can carry commits pushed after the
   merge (`git rev-list --count origin/master..origin/<branch>`).

## 4. The A/B protocol (only the coordinator runs it)

* **Arms:** `ctrl` (the previous master) / `base` (new master, defaults) / `all` (new master + every switch group).
  A losing increment is bisected by switch groups, never re-tested PR by PR.
* **Mirror matches only** until the rebalance: shard `--factions td_gdi` and `--factions td_nod` separately — never
  `td_gdi,td_nod` (that adds the cross pairing). Maintainer: *"Why would you run GDI vs Nod if they are not balanced
  yet? Nod is going to win every single time."* `--swap-bots`, ≥ 16 matches per arm, hard vs classic, A Nuclear Winter.
* **Fast render:** the harness default `--render fast` (VSync off, 640x480 window) and BELOW_NORMAL priority.
  Measured 2026-10-01: VSync-capped 50 ticks/s per game (best 236 at 5 games, collapse at 6); fast: 155 for one game,
  ~372 for three. The engine renders after every logic tick, so VSync caps the simulation; rendering never touches it.
* **Machine:** at most **3 game drivers** at once (4–5 only if the maintainer says the machine copes); stop the
  newest instance the moment the machine slows or he says it is unresponsive. Launch batches DETACHED
  (`Start-Process`) under a supervisor that caps **drivers**, not OpenRA processes (a driver is between matches for a
  moment, so counting games over-launches). Never kill processes by name — only your own PIDs, unless the maintainer orders it.
* **Smoke before soak:** boot the `all` tree's switched yaml first. Read results with `tools/ai/ab_summary.py`
  (ownership + order_gate per arm), `tools/ai/mission_story.py`, `tools/ai/round_trip_check.py`.

## 5. Gates that are easy to get wrong

* **Boot gate:** launch `engine/bin/OpenRA.exe` directly (`Game.Mod=cameo Engine.EngineDir=.. Engine.ModSearchPaths=…`)
  with the default support dir, snapshot `exception-*.log` first, wait for `MenuPostProcessEffect.PostWorldLoaded` in
  `perf.log`, kill your PID. NOT `launch-game.cmd` from Git Bash (MSYS `find` shadows cmd's — a false PASS was recorded).
  Under load allow up to 10 minutes. **Rebuild after every branch switch** — stale DLLs fail with "Cannot locate type".
* **Fog honesty (DESIGN §19.5):** run `audit_fog_honesty.py` on your branch; a new site needs `--write` plus the
  reasoning in the PR; master must never go red.
* **Never** parse yaml by hand (`miniyaml.Ruleset`), never `git stash`, never `git add -A`, sign commits as yourself.
* **Push/PR target is `cameo-mod/Cameo-mod` (origin) — pushing or opening PRs against `Zeruel87/Cameo-mod`
  (`upstream`) is FORBIDDEN unless the maintainer explicitly orders it** (maintainer ruling 2026-10-03; `upstream`
  is fetch-only provenance). Enforced: `remote.upstream.pushurl` is disabled and `.git/hooks/pre-push` rejects
  Zeruel87 URLs (bypass only with `NO_ZERUEL87_GUARD=1` on maintainer order). `gh repo set-default` is pinned to
  `cameo-mod/Cameo-mod` so `gh pr create` can never default to the fork parent again (wrong-repo PRs #178/#179).

## 6. Upstream references — keep them ALL current, harvest everything, check each ENGINE once (standing duty)

Maintainer, 2026-10-01: *"keep them always up to date and always try to harvest as much as possible from all of them,
then merge the traits that are doing the same thing or similar things"* — and *"only check and harvest each engine
once to prevent duplicates."* Registry and lineage: [`design/UPSTREAM_MODS.md`](design/UPSTREAM_MODS.md).

| upstream | clone (`../`) | what we take | how |
|---|---|---|---|
| **OpenRA bleed** (`OpenRA/OpenRA` `bleed`) | `OpenRA`, merged in `cameo-engine` | the ENGINE everything descends from | engine pipeline (LESSONS_LEARNED): `cameo-engine` → push → `mod.config` pin → `make.cmd all` → recreate `engine/glsl/` → boot |
| **rv-engine** (`MustaphaTR/OpenRA`) — ONE engine for **RV, Shattered Paradise, Generals Alpha** | via `cameo-engine` | `OpenRA.Mods.AS` and the RV engine work | checked ONCE through the engine, never three times |
| Romanov's Vengeance | `Romanovs-Vengeance` | `OpenRA.Mods.RA2` (32 files) | mod assembly only |
| Shattered Paradise | `Shattered-Paradise-SDK` | `OpenRA.Mods.Sp` (50) | mod assembly only |
| Generals Alpha | `Generals-Alpha` | `OpenRA.Mods.GenSDK` (33) + content | mod assembly only |
| **Combined Arms** (`Inq8/CAmod`) | `CAmod` | `OpenRA.Mods.CA` (vendored) | `audit_ca_drift.py` → `ca_vendor_sync.py --only STALE`; bot modules hand-ported |
| **Crystallized Nexus** | `crystallized-nexus` | `OpenRA.Mods.CN` (ZG/IM donor) | port per harvest pipeline |
| **Fransbot** (`f850484/OpenRA-Fransbot`) | `OpenRA-Fransbot` | `OpenRA.Mods.Fransbot` (vendored) | re-vendor to tip; `fransbot_drift_baseline.json` `upstream_ref` |

Rules: `git fetch` each clone and count commits since what Cameo absorbed (the drift audits / baselines above). A
mechanic that appears in several upstreams is harvested ONCE, from the best source, and the duplicates are MERGED
(DESIGN §22, `tools/audit/type_merge_inventory.py`). **Re-vendor first, then apply Cameo-side conversions** (never the
other way round). Port mechanics DERIVED from existing values, not copied literals (the disc drain: CA hard-codes −2x
per plant; Cameo uses a −100% multiplier). Status of 2026-10-01: RV 0, SP 0, CN 0 new; CA 24; Fransbot 25; GA 53.
