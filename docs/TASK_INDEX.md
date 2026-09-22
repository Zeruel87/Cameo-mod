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
| **Four-faction September balance continuation** | Current master first; [`balance/PLAYTEST_CLASSIC_FOUR_ACCEPTED_BATCH_20260915.md`](balance/PLAYTEST_CLASSIC_FOUR_ACCEPTED_BATCH_20260915.md) for the applied milestone; [`balance/GRAND_PLAN_20260911.md`](balance/GRAND_PLAN_20260911.md) and [`balance/PROJECT_STATUS_20260911.md`](balance/PROJECT_STATUS_20260911.md) as historical planning evidence | PR #401 applied 29 additional actors and repriced 11 carriers while retaining the newer Rocket Soldier result; the other 122 rows kept current values because no complete target existed. PR #402 made Yuri gatling range/firepower weapon-local. Do not use expired September 11 controls or old draft PRs as current authority. |
| **Weapon structure (W24 / W23 / A5)** | [`design/BALANCE_PROGRAM_PLAN.md`](design/BALANCE_PROGRAM_PLAN.md) §0a **order of operations** and §1b **W24 diagnosis**; [`design/WEAPON_3WAY_SPLIT.md`](design/WEAPON_3WAY_SPLIT.md) | ⛔ **`tools/audit/audit_weapon_shape.py` FIRST** — the ONE-WARHEAD / THREE-INHERIT law (maintainer 2026-09-06). The exemption registry was retired; [`DESIGN.md`](DESIGN.md) §11b.2 preserves historical intent and taxonomy, not exemptions. Follow current §11b.1 and review ambiguous conversions; the old registry `--snapshot` command no longer exists · `tools/audit/audit_split_definitions.py` (is the weapon defined in TWO live files?) · `tools/audit/audit_warhead_split.py` · `tools/audit/audit_three_way_split.py` · `tools/audit/audit_unconverted_templates.py` · `tools/audit/review_resolve_diff.py` · `tools/audit/find_empty_warhead.py` · ⛔ **`tools/audit/audit_release_drift.py`** — the only gate that measures against a SHIPPED build instead of against the tree itself; run it after EVERY collapse |
| **Warhead templates / families** | [`design/WEAPON_TYPE_SYSTEM.md`](design/WEAPON_TYPE_SYSTEM.md); [`DESIGN.md`](DESIGN.md) §12.0h MEAN-100, §12.0d class tilt, **the missile ROLE law** (ground->`MissileHE`, air->`MissileAA`, both->`MissileAP`; `MissileHE` never vs Air) | `tools/balance/gen_weapon_template.py` · `tools/balance/splice_templates.py` · `tools/balance/verify_generator_sync.py` · `tools/audit/audit_missile_role_family.py` |
| **Spread / Falloff** | [`design/SPREAD_FALLOFF_PLAN.md`](design/SPREAD_FALLOFF_PLAN.md) | `tools/balance/gen_weapon_template.py` (`PHYSICS_SHAPES`) |
| **Class anchors & sign-off (W11 / Phase D)** | [`design/BALANCE_PROGRAM_PLAN.md`](design/BALANCE_PROGRAM_PLAN.md) §0a; [`design/FORMULA_V2.md`](design/FORMULA_V2.md) | ⭐ `tools/balance/fit_class.py` (prices every class member; `--spec` **is** the virtual anchor) · `tools/balance/anchor_readiness.py` (why a class cannot be signed) · `tools/balance/check_band.py` (baseband check) · `tools/balance/derive_virtual_anchor.py` (unapproved current-ledger diagnostic candidates) · `tools/balance/propose_anchor_spec.py` (seven-section evidence dossiers; not sign-off — **all 28 exist under `docs/balance/anchors/`**; the 4 dated 2026-09-09 are ANNOTATED snapshots, generate fresh ones elsewhere and never overwrite them) · ⭐ `tools/balance/fit_baseband.py` (**can a class fit 100%-250% at all, and where the baseline goes** — `cost0` cannot move the band; report `docs/balance/baseband_fit.md`) |
| **Stage class proposal reports into ledgers** | [`BLACKROBE_ASTRA_ORDERS_2026-09-07.md`](BLACKROBE_ASTRA_ORDERS_2026-09-07.md) A4 “Make the report-to-ledger path actually work”; [`design/BALANCE_PIPELINE.md`](design/BALANCE_PIPELINE.md) §0 | `tools/balance/propose_class_rebalance.py` · `tools/balance/proposal_contract.py` · `tools/balance/_patch_ledgers_from_reports.py` (dry run by default; explicit `--write` stages ledgers, not YAML) |
| **Changing a balance number** | [`design/BALANCE_PIPELINE.md`](design/BALANCE_PIPELINE.md) §0 the core loop | `tools/balance/extract_stats.py` → ledger → `tools/balance/apply_balance.py --confirm` · `tools/audit/audit_balance_drift.py` |
| **The pricing formula itself** | [`design/FORMULA_V2.md`](design/FORMULA_V2.md) | `tools/balance/formula.py` · `tools/balance/propose_class_rebalance.py` |
| **A unit with TWO weapons (cannon + missile, bombs + AA)** | [`design/ARMAMENT_PAIRING.md`](design/ARMAMENT_PAIRING.md) §3 the pairing key, §3a/§3b why it replaces neither existing classifier, §4 the INI `AA=`/`AG=` half — ⛔ **the role vocabulary IS the maintainer's 2026-09-07 missile ruling; never invent a second one, and never classify an armament by its NAME** | `tools/balance/armament_roles.py` (role classifier + one armament view for all three corpora) · `tools/balance/build_armament_pairing_report.py` · `tools/reference/extract_ini_projectile_roles.py` · ⛔ `tools/reference/extract_ini_elite_weapons.py` (**a TS unit has THREE weapon slots — `Primary=`, `Secondary=` AND `Elite=`; `ini_corpus.json` carries only the first two**) · `tools/audit/audit_missile_role_family.py` (the ratchet-bearing audit — leave its deliberately narrower `weapon_role` alone) |
| **Reference data / faction routing** | [`design/REFERENCE_EXTRACTION_PLAN.md`](design/REFERENCE_EXTRACTION_PLAN.md) — holds rulings **R1–R15**; then [`design/REFERENCE_PIPELINE_HANDOFF.md`](design/REFERENCE_PIPELINE_HANDOFF.md) §8 **traps** (procedure only, never law) | `tools/reference/extract_ini_units.py` · `tools/reference/extract_peer_units.py` · `tools/reference/normalize_armor.py` · `tools/reference/faction_profile.py` · `tools/balance/faction_routes.py` · `tools/balance/reference_distribution.py` · `tools/balance/faction_extrapolate.py` · `tools/balance/assign_references.py` |
| **Armor / Versus profiles** | [`DESIGN.md`](DESIGN.md) §12.0c shield ladder, §12.0d class tilt; [`design/ARMOR_LAYERS.md`](design/ARMOR_LAYERS.md) | `tools/balance/weapon_efficiency.py` (`versus_of`) · `tools/audit/audit_versus_profile.py` |
| **RA3 / Dune source collection and INI evidence safety** | [`design/REFERENCE_EXTRACTION_PLAN.md`](design/REFERENCE_EXTRACTION_PLAN.md) September 9 follow-up rulings; [`balance/review/REFERENCE_COLLECTION_GUIDE_20260909.md`](balance/review/REFERENCE_COLLECTION_GUIDE_20260909.md); [`balance/review/DTA_INI_EXTRACTOR_RESEARCH_20260909.md`](balance/review/DTA_INI_EXTRACTOR_RESEARCH_20260909.md) | `tools/reference/extract_ra3_units.py` · `tools/reference/extract_opendune_units.py` · `tools/reference/extract_emperor_units.py` · `tools/reference/extract_ini_units.py` · `tools/balance/reference_distribution.py` (consumer evidence gate) |
| **Japan pilot and withheld-reference validation** | [`design/REFERENCE_EXTRACTION_PLAN.md`](design/REFERENCE_EXTRACTION_PLAN.md) September 9 follow-up rulings; [`balance/review/REFERENCE_COLLECTION_GUIDE_20260909.md`](balance/review/REFERENCE_COLLECTION_GUIDE_20260909.md) | `tools/balance/build_japan_pilot.py` (unapproved source/target diagnostic and input pin) · `tools/balance/validate_reference_holdout.py` (bounded transfer test, not gameplay approval) |
| **Continuous heaviness design review** | [`DESIGN.md`](DESIGN.md) §12.0i; [`design/WEAPON_HEAVINESS.md`](design/WEAPON_HEAVINESS.md) §9; [`balance/review/CONTINUOUS_HEAVINESS_REVIEW_20260910.md`](balance/review/CONTINUOUS_HEAVINESS_REVIEW_20260910.md) — remaining design decisions, no activation | `tools/balance/preview_bell.py` · `tools/audit/audit_heaviness_bell.py`; runtime/tool parity must be established before migration |
| **OpenRA reference weapon evidence** | [`balance/review/OPENRA_WEAPON_EVIDENCE_PLAN_20260910.md`](balance/review/OPENRA_WEAPON_EVIDENCE_PLAN_20260910.md); [`balance/review/BASE_OPENRA_STRUCTURED_EVIDENCE_20260910.md`](balance/review/BASE_OPENRA_STRUCTURED_EVIDENCE_20260910.md); [`reference/peer_corpus/README.md`](reference/peer_corpus/README.md); [`balance/review/AEDIS_OVERNIGHT_RULINGS_20260909.md`](balance/review/AEDIS_OVERNIGHT_RULINGS_20260909.md) September 10 follow-up | CA and base OpenRA TD/RA/TS/D2k structured inputs replace their Doc5 slices through `tools/balance/peer_corpus.py`; other sources remain legacy. Factory-ready and upgraded state certification remains pending; unknown conditions are not guessed |
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
