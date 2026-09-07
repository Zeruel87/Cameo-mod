# Cameo-mod

## ⚡ START HERE — read before acting (the rest of this file is the full contract)

**Don't trust, verify.** Before asserting anything is done / pending / blocked / missing,
check the artifact itself — grep the data, `ls` the file (incl. `~/Downloads`), run the tool,
boot-gate the tree. When a summary (ROADMAP line, handoff, memory, status table) disagrees with
the artifact, **the artifact wins — then fix the stale summary.**

**⛔ BEFORE STARTING ANY TASK: open `docs/TASK_INDEX.md` and find your task's row.** It names
the document AND SECTION to read first, and the tools that ALREADY EXIST for that task. It is
the standing defence against duplicate work — a spec was written for a resolver check that
exists twice, a virtual-anchor mechanism was re-designed when `fit_class.py --spec` already
implements it, and a whole session once re-derived a weapon-tier model DESIGN.md had shipped.
Guarded by `tools/audit/audit_task_index.py`.

**Must-read, in order:** this file → `docs/TASK_INDEX.md` → `docs/LESSONS_LEARNED.md` → `docs/AGENT_WORKSPACE.md` →
**`docs/HANDOFF.md`** (the entry point: verified current state + the priority-ordered queue;
it supersedes every dated handoff) → `docs/DESIGN.md` → `docs/design/ROADMAP.md` →
`docs/audit/SUMMARY.md`. `docs/README.md` is the canonical definition of that order — if any
copy disagrees, README wins.

For weapon work also: `docs/design/WEAPON_3WAY_SPLIT.md`, `docs/design/WEAPON_TYPE_SYSTEM.md`,
`docs/design/BALANCE_PROGRAM_PLAN.md` (the board + §0a's binding order of operations), and
`docs/design/SPREAD_FALLOFF_PLAN.md` (Spread/Falloff: radius=(N-1)×Spread, shape=value spacing,
3-axis gameplay/physics/uniqueness). Effort planning: `docs/design/BALANCE_PIPELINE_ESTIMATE.md`.
⚠ The dated handoffs in `docs/history/handoffs/` are provenance ONLY — read them for technique,
never for status.

**Ten hard rules** (rules 1–2 are enforced by hooks in `.claude/settings.json`):
1. **Boot-gate every commit** of engine content — `launch-game.cmd` must reach the main menu
   (`perf.log` ends `MenuPostProcessEffect.PostWorldLoaded`, no new `exception-*.log`). Snapshot the
   log list + cutoff BEFORE launching; menu-proof is grepping `perf.log`, not its last line.
2. **Scoped `git add <files>` only — never `-A` / `.` / `--all`.** Several contributors have live WIP
   in this tree (AedisToru, Blackrobe, Elpollo315, Devin AI, and agents landing under the shared identity).
3. **Never hand-edit a balance number** — use the pipeline (`extract_stats` → ledger →
   `apply_balance --confirm`; `--confirm` needs a maintainer order).
4. **`Versus` lives ONLY in `^Warhead_*` templates.** Never change a warhead / `Burst` / `BurstDelays`
   without explicit permission.
5. **Weapon 3-way split:** preserve resolved behaviour (`Damage` verbatim, projectile fields — the
   Frankenstein merge), `find_empty_warhead.py = 0`, boot-gate per batch. Verify a conversion with
   `tools/audit/review_resolve_diff.py` (before/after resolve).
6. **Multi-agent tree** (maintainer, co-maintainer, other agents, you): **one owner per file-set.**
   Check a file's mtime and `git log -3 <file>` for a live agent before editing; re-verify others'
   commits before building on them; never `git checkout -- .` or wide-add someone else's WIP.
   The file-set boundaries are defined in `docs/design/BALANCE_PROGRAM_PLAN.md` §2.
7. **Rebuild C# before boot** if `OpenRA.Mods.Cameo/` or `engine/` changed
   (`DOTNET_ROLL_FORWARD=LatestMajor dotnet build -c Release --nologo -p:TargetPlatform=win-x64` → `engine/bin`).
   ⚠ **`engine/` IS NOT PART OF THIS REPO** — it is `.gitignore`d, has no `.git`/`.gitmodules`,
   and `git ls-files engine` returns **zero** files (`git` run from inside it silently targets
   the PARENT repo). Editing `engine/**` produces work that **cannot be committed here** and is
   **deleted by the next `make all`**. To change the engine, follow
   **`docs/LESSONS_LEARNED.md` → "The canonical engine update pipeline"**: edit the SEPARATE
   `cameo-engine` clone of `github.com/cameo-mod/OpenRA` → push → `git rev-parse cameo-engine`
   for the full 40-char hash → set `ENGINE_VERSION` in **`mod.config`** → `make.cmd all` →
   verify `engine/VERSION` + recreate `engine/glsl/` shaders → boot-gate → commit `mod.config`.
   **First check whether a mod-side SHADOW avoids all of that:** `ObjectCreator.FindType` takes
   the first assembly in `mod.yaml`'s `Assemblies` list (AS, CA, **Cameo**, Cnc, D2k, Common),
   so an `OpenRA.Mods.Cameo` type of the same name wins with zero yaml changes (precedent:
   `ColorPickerColorShift`, `PlayerColorShift`, `SelectionDecorations`). Prove a shadow with a
   Cameo-only field — `--docs` lists both types and proves nothing.
8. **Audit reports regenerate via `bash tools/audit/run_all.sh` only** (PowerShell `>` writes UTF-16),
   **and only from a COMPLETE tree** — `engine/` built, clone not shallow. Missing either makes a
   dozen audits scan a smaller corpus, report FEWER findings and still say PASS, so the commit
   deletes real evidence with a green run (`dead_warhead_fields` 27071 warhead nodes → 7014).
   `run_all` diverts to the untracked `docs/audit/degraded/` in that case and says why; `--force-latest`
   overrides. Refresh `latest/` WHOLE, from one machine — path separators alone make a
   cross-platform diff dirty. (`tools/audit/environment.py`, `docs/LESSONS_LEARNED.md`.)
8b. **The engine DROPS unknown yaml fields in silence.** `FieldLoader.Load` (FieldLoader.cs:676)
   iterates the TYPE's fields and never reads the leftover keys, and traits + warheads go through
   it (`WeaponInfo.cs:178`). Only `FieldLoader.LoadField` throws — that is the settings/linter
   path, and two Cameo docs used to claim otherwise. A misplaced field therefore costs nothing at
   boot and everything in play: 2059 warheads carried a `Falloff` their type has no field for.
   Run **`audit_dead_warhead_fields.py`** (LOWER-ONLY ratchet). ⚠ Reading C# to build a field set,
   match `public`, **not** `public readonly` — some AS warheads declare mutable public fields.
   The same trap exists one layer up: a weapon inheriting TWO `^Projectile_*` templates merges into
   ONE node whose TYPE is the last template's and whose FIELDS are the union of both.
8e. **NEVER hand-parse yaml — read through `miniyaml.Ruleset.resolve_weapon` / `.resolve`,**
   and pull Versus with `weapon_efficiency.versus_of(node)`. A bespoke line-scanner opened a dict
   on `Versus:` and never CLOSED it, so the `PercentageVersus:` rows the AreaDamage fold added
   INSIDE the same warhead overwrote the profile: every measured mean, spread, ratio and inversion
   count was internally consistent and wrong (reported "0 of 125 obey the MEAN-100 law"; the truth
   was **123 of 125**). A near-miss sibling name is the trap — `PercentageVersus` does not
   `startswith("Versus:")`, so the OPEN guard looked right; the bug was the missing CLOSE. If a
   hand parser is unavoidable, close every block the moment indentation returns to its level.
   Guarded by `audit_versus_profile.py`. And **a result that contradicts a binding law the
   generator implements is a contradiction, not a finding** — check before believing it.
8f. **GREP `docs/DESIGN.md` BEFORE DESIGNING ANYTHING.** It is required reading #4 and it is
   binding. §12.0h (MEAN-100: `K` is SHAPE-ONLY, `Damage` is the sole magnitude knob), §12.0c (the
   Shield ladder) and §12.0d (the CLASS TILT — each level tilts toward one end of every armor
   ladder and *"can never invert"*) were all already ruled and already shipped while days of design
   work re-derived them. A design question that feels novel usually is not.
8c. **A "derive unless overridden" default is invisible when something upstream always overrides.**
   `ScaledBullet` derived shell Inaccuracy/Speed from Range for weeks and reached zero weapons,
   because the templates also wrote literals and an explicit yaml value always wins. Assert the
   DERIVED value on a real resolved weapon, never that the knob is merely present.
8d. **Every warhead family must be unique** — no two may share both a radius and a curve
   (`audit_family_uniqueness.py`). Shape comes from `PHYSICS_SHAPES` in `gen_weapon_template.py`,
   the level scales the radius only, and blends cross their parents' shapes via `blend_shape()`.
   Radius = **(N-1) x Spread**, not N x Spread. Always `splice_templates.py --all`, never a subset:
   adding a family re-ranks the shield-coupling ladder and a partial splice leaves drift.
8g. **AN OVERRIDE IS A CANCELLATION — never judge it by the node it sits in.**
   `-Key@X:` in a child CANCELS what an ANCESTOR defines, so it looks dead *precisely
   because* the node it sits in does not define X. On 2026-09-06 `d818aec40` deleted
   **2248 `-Warhead@*` nodes as "stale"** and resurrected every cancelled warhead:
   weapons with more than one MAIN warhead went **461 → 1103**, and 14 deleted
   `-Warhead@shrapnel:` terminators turned the mutalisk's 3-bounce spore into an
   **infinite loop** the maintainer found in play. ⛔ **Nothing crashed** — a boot gate
   proves the rules PARSE, never that they are RIGHT. Resolve the chain and keep the
   node unless **no ancestor defines that key**; verify with
   `tools/audit/review_resolve_diff.py`, and note that a bulk delete is the wrong
   SHAPE for this cleanup — it must be per-node. Guarded by **`bash_guard.py` rule 4**
   (a staged yaml diff deleting a `-Key@...` needs `RESOLVE-VERIFIED` in the message)
   and by **`audit_shrapnel_chains.py`** (S1a multi-node cycles, ratchet 0). The same
   trap wears other clothes: a child's `Modifier: 100` is usually a cancellation of an
   inherited multiplier, not a no-op.
8h. **A RENAME BREAKS MAPS, and the boot gate cannot see it.** A `.oramap` lists placed
   actors; if a rename moves a type the map still asks for the old one, and the failure
   happens when that map is STARTED, not at boot. `1e30a1cb9` repaired seven maps by
   hand. Run **`audit_map_actors.py`** (M1 ratchet 0) after every rename batch.
9. **Underscore-only naming** — no hyphens in ids / files / fluent keys.
10. **Attribute the ACTUAL author in the commit trailer — never impersonate another agent.**
    Sign with **your own** identity, including your real model name:
    `Co-Authored-By: Claude <model> <noreply@anthropic.com>` — e.g. Opus 5 signs
    `Claude Opus 5`, Opus 4.8 signs `Claude Opus 4.8`. **Never copy the trailer from a
    previous commit or from this file** — it is a template, not a literal; a version pinned
    here goes stale the moment the model changes, and copying it makes a newer model
    misreport itself as an older one.
    **Any OTHER agent (Devin, Cascade, etc.) must use its OWN `Co-Authored-By:` line** (e.g.
    `Co-Authored-By: Devin AI <devin@cognition.ai>`) and must NOT append the Claude trailer — the
    git author is a shared repo identity, so the trailer is the only provenance signal and a wrong
    one pollutes history. If you are not Claude, do not sign as Claude.

**Work queue:** `docs/design/ROADMAP.md` (crashes jump the queue). **Effort estimate for the whole
balance program:** `docs/design/BALANCE_PIPELINE_ESTIMATE.md`.

---

## Mission & end goal (never lose sight of this)

Cameo is the ultimate crossover RTS between the classic RTS games and will
keep growing. The architecture goal is **dynamic faction loading**: load
only the factions picked in the lobby / needed by the shellmap, instead of
everything at boot (historical peak: 12 GB RAM — unplayable on 8 GB
machines). Every faction therefore becomes a fully self-contained
ContentPack: rules + weapons + sequences + its own ai.yaml + all assets
(sprites, voxels, icons, sounds) in per-type subfolders, zero cross-pack
dependencies, shared content only in theme Shared/ packs, and unused files
audited and deleted. Current progress + the exact runbook to continue:
**`docs/MIGRATION.md`**.

## Required reading, in order

This is the same list as the ⚡ START HERE block above, expanded.
**`docs/README.md` is the canonical definition** — if any copy disagrees with it,
README wins and the copy gets fixed.

1. **`docs/LESSONS_LEARNED.md`** — accumulated pitfalls and safe defaults.
2. **`docs/AGENT_WORKSPACE.md`** — mandatory workflow, evidence rules,
   incident protocol, and commit gate.
3. **`docs/HANDOFF.md`** — the entry point: verified current state, the
   priority-ordered queue, and what each stale document was replaced by.
   Supersedes every dated handoff in `docs/history/handoffs/`.
4. **`docs/DESIGN.md`** — the binding design contract (naming grammar, stat
   formulas, tech tiers, content-pack layout, description scheme, agent
   operating rules). Read it before touching any yaml.
5. **`docs/design/ROADMAP.md`** — the granular work queue; crashes always
   jump it.
6. **`docs/audit/SUMMARY.md`** — current known-issue state by bug class.

Then, as the task needs them:

* `docs/design/BALANCE_PROGRAM_PLAN.md` — the balance board (W1–W26), file-set
  ownership, and §0a's binding order of operations.
* `docs/Cameo_Knowledge_Base_Manual.md` — the ENGINE/CODE reference (v.0.5):
  custom traits, assemblies (OpenRA.Mods.Cameo/CA), activities, bot modules,
  UI internals. Consult it for any C#-side question (it lists code-derived
  identifiers); verify against source when in doubt — it is a contributor
  document, not the binding contract.
* `docs/history/MASTER_REPORT_2026-07-08.md` — historical long-form analysis and the B1–B12 bug
  taxonomy, dated 2026-07-08. Read it for background; it is **not** binding and
  **not** a live roadmap.
* `docs/README.md` — one-page orientation for a first-time reader.

## Tooling

- `tools/audit/run_all.sh` — full audit suite, the canonical runner (run
  before/after changes; single checks: `python tools/audit/audit_<name>.py`).
  `tools/audit/run_all.py` is a Python port for shells without `sh`; it reads its
  audit list out of `run_all.sh`, so the two cannot drift apart.
- `tools/balance/run_with_guard.py` — syntax pre-check + timeout guard; run
  balance/audit scripts through it (`.windsurf/workflows/run_python_safe.md`).
- `tools/audit/find_empty_warhead.py` — the boot-NRE guard. Must print 0 after
  any bulk warhead edit; `--check-yaml` does NOT catch that class.
- `tools/audit/audit_duplicate_inherits.py` — the `Parent type X was already
  inherited` crash class. Grep cannot find it; this reports every instance at once.
- `tools/audit/review_resolve_diff.py` — before/after resolved diff for a weapon
  conversion (rule 5).
- `tools/audit/audit_doc_claims.py` + `docs/audit/doc_claims.yaml` — every numeric
  claim a DECISION rests on, with its re-measure command. When a claim legitimately
  changes, update `value` and every doc listed under `docs:` IN THE SAME COMMIT.
- `tools/rename/safe_rename.py` + `rename_map_<faction>.yaml` — naming migration
  (replaces the deprecated `apply.py`).
- `tools/packs/split_faction.py` — ContentPack extraction.
- `tools/audit/dump_resolved.py` — resolved-ruleset snapshots; refactors
  must diff empty.
- Recurring code-health audits and freshness policy: `docs/audit/PERIODIC.md`
  and `docs/audit/periodic.json`.

## Commit gate (absolute — no exceptions)

**Never commit without booting the game first.** Run `launch-game.cmd`
and confirm it reaches the main menu with NO new `exception-*.log` in
`%APPDATA%/OpenRA/Logs` (snapshot the log list BEFORE launching; menu
proof: perf.log ends with `MenuPostProcessEffect.PostWorldLoaded`).
The Python resolver does not catch junk trait nodes — only the engine
does, and it parses every faction at boot. If C# sources changed or
were pulled, rebuild first (`dotnet build -c Release --nologo
-p:TargetPlatform=win-x64`); stale DLLs crash the boot with
`Cannot locate type: …Info`. Commit with scoped `git add <files>`,
never `git add -A` — the maintainer usually has live uncommitted edits.

## Balance changes: the pipeline, never by hand

**Never hand-edit a balance number in yaml.** The sanctioned loop
(full spec: `docs/design/BALANCE_PIPELINE.md`):

1. `python tools/balance/extract_stats.py` — refresh the ledger
   (`docs/balance/*.json`, raw stats + provenance).
2. Edit the LEDGER, or generate the workbench
   (`tools/balance/build_workbook.py` →
   `docs/design/cameo_balance_v2.xlsx` — ⚠ **tracked in git**, despite older
   notes calling it gitignored; regenerating it produces a real diff), edit
   the unlocked input cells there, and read it back with
   `tools/balance/import_workbook.py`.
3. `python tools/balance/apply_balance.py --faction X --confirm` —
   ledger → yaml (dry run without --confirm). **Maintainer order
   required for --confirm.**
4. Re-run `extract_stats.py`, run audits + BOOT GATE, commit yaml and
   ledger TOGETHER.

`audit_balance_drift` (in run_all.sh) fails red whenever yaml and the
committed ledger disagree — hand edits cannot land silently. ⚠ It only helps if
someone LOOKS: it has gone red twice now because yaml commits landed without a
re-extract. Re-extract before every commit that moves a balance number, not at the
end of a session.

**The damage grid is 100, not 2000.** `formula.DAMAGE_STEP = 100` (W15), and
`FirepowerMultiplier` is retired as a pricing/fine-tuning knob (W17): `apply_balance`
cannot write it, and `propose_class_rebalance.decompose_dps` always solves at
`fp = 1.0`. Older documents that teach the 2000-step grid plus an FP fine-tune are
describing a retired law.

The LEGACY workbook `docs/design/cameo_armor_system.xlsx` remains the
reference for design judgments until the Phase-3 discrepancy triage
completes (docs/balance/discrepancies.md). If `~$cameo_armor_system.xlsx`
exists, the workbook is open in Excel: don't write it; queue and say so.

## Memory

If your harness has a per-agent memory store, read the memory that covers a command
(build, engine sync, git) in full before running it.

⚠ **A memory is not a repository document.** It is private to one agent: nobody else —
maintainer, co-maintainer, another agent — can open it. Thirty-six `memory <name>` citations
once sat in the design docs pointing at things no reader could resolve; they were promoted
out on 2026-08-23 and the live set now holds **zero**. Keep it that way. So:

* treat a memory as **provenance, never authority**;
* the moment a memory carries a rule, a number or a decision that others must follow,
  **promote it into the repository** (`DESIGN.md` for law, `LESSONS_LEARNED.md` for a trap,
  `docs/audit/doc_claims.yaml` for a number that must not rot) in the same session;
* never resolve a contradiction in favour of a memory. The artifact wins, then the
  repository documents, then everything else.

## Work queue & token efficiency

- The ordered work queue lives in **`docs/design/ROADMAP.md`** — pick
  from the top (crashes always jump the queue), update it as you go.
- Model/effort cannot be switched by the agent itself (the user picks
  the model). To spend fewer tokens WITHOUT losing quality:
  - batch mechanical sweeps into scripts over the model/registry, never
    file-by-file reading;
  - keep rules in DESIGN.md and plans in ROADMAP.md instead of
    re-deriving them each session; read them FIRST;
  - bundle many small design orders into one implementation pass;
  - verify with the audit suite (cheap) rather than re-reading yaml;
  - subagents on cheaper models are only worth it for self-contained
    batch jobs big enough to amortize their cold-start context.
