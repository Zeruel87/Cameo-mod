# TASK INDEX — read this BEFORE starting any task

_Maintainer order, 2026-09-06: **"every task must have a clear reference to the docs, so when
you start any task the correct document and the correct section is automatically read, so you
will never do duplicate work again that has already been done."**_

⛔ **THIS FILE EXISTS BECAUSE THE DUPLICATE WORK WAS REAL AND REPEATED.** Three examples from
one day, all caught only after the work was underway:

* A spec was written for a "resolver check" audit that **already exists twice**
  (`fit_class.py`, `check_band.py`), and for a "virtual anchor" mechanism that **is already
  implemented** as `fit_class.py --spec`.
* A whole session was once spent re-deriving a weapon-tier model that `DESIGN.md` §12.0h /
  §12.0c / §12.0d had already ruled **and shipped**.
* Three extracted reference mods sat unrouted for weeks because nothing said "check whether a
  source in the corpus is missing from `ROUTES`".

**So the rule is:** find your task below, read the **READ FIRST** column *before touching
anything*, and check the **ALREADY BUILT** column before writing a single new tool. If your
task is not listed, add a row when you finish it.

⚠ Guarded by [`tools/audit/audit_task_index.py`](../tools/audit/audit_task_index.py): every
document and every tool named here must exist, and every board item must be routed. Link and
anchor validity is enforced separately by `audit_doc_health` (D3/D4).

---

## How to use this in 30 seconds

1. Find the row for what you are about to do.
2. Open the **READ FIRST** document *at the named section*. Not the whole file — the section.
3. Run the **ALREADY BUILT** tools with `--help` before you write anything new.
4. If you still think something is missing, say so in `DEVELOPMENT_LOG.md` **before** building
   it. Every duplicate so far would have been caught by that one sentence.

---

## The routing table

| task | READ FIRST | ALREADY BUILT — check before writing anything |
|---|---|---|
| **Anything at all, first session** | [`README.md`](README.md) → [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md) → [`AGENT_WORKSPACE.md`](AGENT_WORKSPACE.md) → [`HANDOFF.md`](HANDOFF.md) → [`DESIGN.md`](DESIGN.md) | — |
| **Picking up work** | [`HANDOFF.md`](HANDOFF.md) §3.A, then [`design/ROADMAP.md`](design/ROADMAP.md) | — |
| **Weapon structure (W24 / W23 / A5)** | [`design/BALANCE_PROGRAM_PLAN.md`](design/BALANCE_PROGRAM_PLAN.md) §0a **order of operations** and §1b **W24 diagnosis**; [`design/WEAPON_3WAY_SPLIT.md`](design/WEAPON_3WAY_SPLIT.md) | `tools/audit/audit_warhead_split.py` · `tools/audit/audit_three_way_split.py` · `tools/audit/audit_unconverted_templates.py` · `tools/audit/review_resolve_diff.py` · `tools/audit/find_empty_warhead.py` |
| **Warhead templates / families** | [`design/WEAPON_TYPE_SYSTEM.md`](design/WEAPON_TYPE_SYSTEM.md); [`DESIGN.md`](DESIGN.md) §12.0h MEAN-100, §12.0d class tilt | `tools/balance/gen_weapon_template.py` · `tools/balance/splice_templates.py` · `tools/balance/verify_generator_sync.py` |
| **Spread / Falloff** | [`design/SPREAD_FALLOFF_PLAN.md`](design/SPREAD_FALLOFF_PLAN.md) | `tools/balance/gen_weapon_template.py` (`PHYSICS_SHAPES`) |
| **Class anchors & sign-off (W11 / Phase D)** | [`design/BALANCE_PROGRAM_PLAN.md`](design/BALANCE_PROGRAM_PLAN.md) §0a; [`design/FORMULA_V2.md`](design/FORMULA_V2.md) | ⭐ `tools/balance/fit_class.py` (prices every class member; `--spec` **is** the virtual anchor) · `tools/balance/anchor_readiness.py` (why a class cannot be signed) · `tools/balance/check_band.py` (50–400% baseband) |
| **Changing a balance number** | [`design/BALANCE_PIPELINE.md`](design/BALANCE_PIPELINE.md) §0 the core loop | `tools/balance/extract_stats.py` → ledger → `tools/balance/apply_balance.py --confirm` · `tools/audit/audit_balance_drift.py` |
| **The pricing formula itself** | [`design/FORMULA_V2.md`](design/FORMULA_V2.md) | `tools/balance/formula.py` · `tools/balance/propose_class_rebalance.py` |
| **Reference data / faction routing** | [`design/REFERENCE_EXTRACTION_PLAN.md`](design/REFERENCE_EXTRACTION_PLAN.md) — holds rulings **R1–R15** | `tools/reference/extract_ini_units.py` · `tools/reference/extract_peer_units.py` · `tools/reference/normalize_armor.py` · `tools/reference/faction_profile.py` · `tools/balance/faction_routes.py` · `tools/balance/reference_distribution.py` · `tools/balance/faction_extrapolate.py` · `tools/balance/assign_references.py` |
| **Armor / Versus profiles** | [`DESIGN.md`](DESIGN.md) §12.0c shield ladder, §12.0d class tilt; [`design/ARMOR_LAYERS.md`](design/ARMOR_LAYERS.md) | `tools/balance/weapon_efficiency.py` (`versus_of`) · `tools/audit/audit_versus_profile.py` |
| **ContentPack split / faction migration** | [`MIGRATION.md`](MIGRATION.md) §"The per-faction pipeline" | `tools/packs/split_faction.py` · `tools/audit/audit_faction_leaks.py` |
| **Renaming anything** | [`DESIGN.md`](DESIGN.md) naming grammar | `tools/rename/safe_rename.py` + `rename_map_<faction>.yaml` |
| **AI / bot behaviour** | [`design/AI_ARCHITECTURE.md`](design/AI_ARCHITECTURE.md) | — |
| **Engine / C# change** | [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md) "The canonical engine update pipeline" | ⚠ try a mod-side **shadow** first — assembly order puts Cameo before Common |
| **Running the gates** | [`audit/PERIODIC.md`](audit/PERIODIC.md); [`HANDOFF.md`](HANDOFF.md) §3.0c on exit codes | `bash tools/audit/run_all.sh` (the ONLY sanctioned runner) |
| **Refactor that must not change behaviour** | — | `tools/audit/dump_resolved.py` — diff must be empty |
| **Reading yaml from Python** | [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md) "NEVER HAND-PARSE YAML" | `tools/audit/miniyaml.py` — ⛔ `children_named()`, never `child()`, for `@suffixed` traits |
| **A number quoted in a document** | [`audit/doc_claims.yaml`](audit/doc_claims.yaml) | `tools/audit/audit_doc_claims.py` — update `value` and every listed doc in the SAME commit |

---

## The five release-critical gates

Everything else is a quality gate and does **not** block a playtest build.

| gate | command |
|---|---|
| empty warheads = 0 | `python tools/audit/find_empty_warhead.py` |
| duplicate inherits | `python tools/audit/audit_duplicate_inherits.py` |
| ledger vs yaml | `python tools/audit/audit_balance_drift.py` |
| generator sync | `python tools/balance/verify_generator_sync.py` |
| **the boot gate** | `launch-game.cmd` → `perf.log` must contain `MenuPostProcessEffect.PostWorldLoaded`, no new `exception-*.log` |

---

## Where each kind of statement lives

Put a new fact in exactly one of these. A fact in two places is a future contradiction.

| kind of statement | its home |
|---|---|
| binding law (naming, formulas, tiers, armor) | `DESIGN.md` |
| a trap that cost someone time | `LESSONS_LEARNED.md` |
| a number a decision rests on | `docs/audit/doc_claims.yaml` |
| current state + priority queue | `HANDOFF.md` |
| the granular task list | `design/ROADMAP.md` |
| a reference-pipeline ruling (R1–R15) | `design/REFERENCE_EXTRACTION_PLAN.md` |
| the weapon/pricing board (W1–W26) | `design/BALANCE_PROGRAM_PLAN.md` |
| what an agent did, and agent-to-agent messages | `DEVELOPMENT_LOG.md` |
| provenance only, never authority | `docs/history/**` |
