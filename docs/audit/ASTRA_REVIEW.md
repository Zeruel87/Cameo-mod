# Astra implementation review

## Current integration: merged graph and AI logging (2026-09-07)

PR #329 is reconciled with upstream `9ad1a5f77`, including merged #323 and #331
and the subsequent AI JSON separator fix. The dated sections below preserve
prior evidence; they are not the current logging contract.

- Keep one graph implementation. Retain signed-range/sampling regressions, the
  label that fits at 1024x768, and enum/dropdown alignment: hotkeys index directly
  into the dropdown, so the two orders must agree.
- Retire `CameoMatchLog`, `CameoMatchRecorder`, its player-state trait and tests.
  Use upstream `AiMatchLogRecorder`/`AiMatchLogWriter` and its offline aggregator.
  Carry forward the permanent world-load save exclusion, with eligibility and
  active-YAML/source regression coverage. No second writer or second output schema.
- The retained writer is host-only and emits per-bot rows when all bots resolve
  or GameOver occurs. It is not the old completed-world/all-player dataset and has
  no rules hash, module IDs or lobby options. Old `cameo_matches` files must not
  be pooled into the new `cameo-ai-matches.jsonl` schema. Its file/record sizes are
  not bounded, missing counters are zero and personality ambiguity is not reported.
  Earlier match/replay recording evidence applies to the retired writer.
- Adopt Aedis's current total-output and missile-role laws. Retain useful document
  cleanup and module contracts without restoring the retired exemption command.
  The earlier Scooper/Apocalypse edits remain explicit merge-regression repairs,
  not output-preserving collapses; their exact five-definition comparison remains
  pinned. No new weapon-role or actor-stat changes are made by this integration.

Independent review challenged retirement, schema differences and save eligibility.
The integrated build passes (eight existing engine warnings), with a fresh DLL
containing the new eligibility field. All 70 current C# cases pass with no skips.
All 33 ledger checks have zero drift. A fresh 101.3-second menu/shellmap smoke
reached `MenuPostProcessEffect.PostWorldLoaded`, with no new exceptions; its owned
timed stop is not a completed-match exit. Sampled PC memory peaked at 71.8%.
Full Python and canonical audit results follow after completion; prior green
counts are not silently carried forward. A fresh bot-match/replay test of the
replacement writer remains unperformed by this integration pass.

The complete canonical audit refresh at source checkpoint `204fa6040` finished
in 779.8s (sampled Python tree 1505.7 MB, PC 49.0%) using bundled dependencies and
the complete engine environment. All reports are nonempty. Five newly wired
reports are included: missile roles, release drift, turning, original reference
coverage and stat uniqueness. The overall exit remains 1 for retained debt,
including the upstream missing Contents entry in `LESSONS_LEARNED.md`; no ceiling
was raised to pass integration. Registered document counts, glow, percentage
dispatch and structural ratchets pass. Empty-type warheads are zero; all 145
generated templates remain in sync. Engine-freshness limitations remain explicit.

Final frozen-source Python validation: **933 passed, 44 existing retired-feature
skips, zero failures**, all 100 modules (977 tests), with bundled dependencies.
The first run found only the new upstream `reference_assignment.json` cache being
mistaken for an orphan faction ledger. Its exact schema now has a narrow layout
check; unknown orphan files still fail. The complete rerun took 588s,
sampled tree peak 849.6 MB and PC peak 48.9%.
`latest/bounded_test_run.json` records that clean final rerun. A fresh fetch still
points to `9ad1a5f77`; the non-mutating merge check is clean. PR remains draft.

Whitespace caveat: the new upstream missile-role and release-drift generators
emit an extra blank line at EOF. Their reports are retained verbatim. Standard
`git diff --check` flags those two lines; checking with only `blank-at-eof`
disabled passes. No audit finding or generator threshold was edited to hide it.

## Window and scope

User-authorized three-hour run: 2026-09-07 03:18:43–06:18:43 WIB.
Branch `astra/balance-pipeline`, based on merged PR 328 (`291052380`).
Main checkout is not used for edits. This branch is published for coordinator
review, not directly to master. No pricing targets are inferred from authority.

## Foundation review

- Full audits and tests were completed against the identical source immediately
  before PR 328 merged; see `docs/design/PR328_UPSTREAM_INTEGRATION.md`. The suite
  remains red, with raw debt retained. Fresh upstream fetch still resolves to
  `291052380` at this run's start.
- Independent hand calculations agree with `formula.py` for MBT, archer and
  artillery: equal baseline ratios yield C0; doubling HP and DPS yields
  `(1.5 + 2 + 4) / 3 = 2.5 C0`, respectively 2000, 1250 and 1250.
- Independent unchanged Zerg ledger dry run reports zero changes and writes
  nothing. This does not exercise the unsafe confirmation path.
- Document-claims audit is not green; recorded upstream mismatches must not be
  waived or overwritten with guessed values.

## Completed: safe apply completion

Review found that the current apply command writes despite collected errors,
passes an obsolete positional repository argument to extraction, ignores child
exit codes, and silently discards some missing-warhead errors. Confirmation can
therefore report success while leaving stale ledgers. The first repair closes
these paths; no live balance target was applied to validate it.

Implemented: complete preflight, unambiguous fresh provenance, explicit
shared-consumer checks, staged extraction, exact raw-ledger agreement, checked
validation, and optimistic rollback checks that preserve detected external edits. Regression
tests exercise failure paths and preserve unrelated pending proposals.

Validation:

- `python tools/tests/test_apply_balance.py`: 35 tests pass, including interruptions,
  disk/audit/extraction failures, shared consumers, stale provenance, unsupported
  leaf deletions, comments/BOM/newlines, and staged-output input isolation.
- Sequential full test run: 89/89 modules, 800 tests, zero skipped, 43 failed
  modules. Compared with merged PR 328's 766-test baseline, both failing-module
  and failing-method identities are identical. The full run contains 34 apply
  tests; the final missing-ledger case and deletion subcase were rerun in the
  35-test focused validation afterwards. This is not an 800-pass claim.
- Real `extract_stats.py --output-dir` verification: 67 raw/derived artifacts
  semantically identical to the baseline; all live ledger bytes unchanged.
  The initial byte comparison detected checkout CRLF versus generated LF, so
  publication now avoids rewriting semantically unchanged JSON.
- Live `apply_balance.py --faction starcraft_zerg`: zero planned changes,
  zero inherited skips, exit 0; no writes. Peak process tree 783.1 MB.
- Canonical `bash tools/audit/run_all.sh`: completed exit 1, 713.9 seconds,
  no zero-byte reports. Existing upstream debt remains visible. Peak process
  tree 1119.2 MB; peak PC memory 52.5% under the 84% guard.
- After staging the new source files, direct security/error-handling scans
  confirmed no additional findings; unchecked-subprocess flags drop by two.
  Generated audit snapshots will be refreshed for the complete follow-up PR.
- Independent review approved the writer scope after challenging deletion,
  interruption, concurrent-edit and Windows temporary-file cases.
- A second independent real integration test in a disposable copy applied one
  Heavy Sniper HP edit (25000 to 26000) with `--confirm`, then checked all 33
  ledgers with zero drift. Exactly one YAML line changed. Percentage-model
  sidecars changed consistently with the population HP input. This was not an
  approved or applied live balance change. Peak process tree 1594.6 MB, PC 51.4%.

Revert: revert the dedicated safe-apply commit; no live YAML needs reverting.
Limits: exception-safe, not filesystem-wide atomic; no concurrent game reader;
hard kills retain printed recovery originals; map/script references still require
review. Byte comparisons are not an OS lock or atomic compare-and-swap: another
writer can race between checking and replacing a file. Run only with exclusive
ownership of the affected files, as BALANCE_PIPELINE requires. The concurrency
tests prove detection/recovery cases, not race-free simultaneous writing.
Existing unrelated upstream test/audit failures are not waived.

## Completed: readiness reporting and ruled Heavy Sniper membership

The readiness command crashed because it called the removed
`intentional_composite` exemption. It now uses the shared resolved main-warhead
predicate without subtracting reviewed exceptions, and reports unavailable
weapons or active-rule resolution failures rather than silently clearing them.
Low pricing residuals and absence of stacked mains no longer claim sign-off or
complete structural clearance. Missing baseline/stat data is explicit, and all
27 anchor actors are inspected even when their fitted baseline is absent.

The sole ledger edit sets `td_gdi_heavysniper.design.class_anchor` to
`heavy_sniper`, implementing the existing FORMULA_V2 section 6b heavy-sniper
override. It preserves the live SniperInfantry template, every numeric stat and
weapon. This is metadata classification, not a gameplay rebalance.

Validation: nine focused readiness tests pass; the existing 13 class-membership
tests pass; helper/data inspection finds 27/27 anchors in class
and zero signed anchors. Its buildable denominator is explicitly 1956 ledger
rows, including structures/upgrades: 632 classified rows is not claimed as unit
coverage. Every class still has a raw stacked-main finding. Extraction check:
33 ledgers, zero drift; 778.3 MB peak process memory and 51.0% PC memory.
Independent review challenged and corrected missing-stat handling and misleading
formula/sign-off wording. Candidate ranking remains diagnostic, not clearance.

No anchors are signed and no faction is repriced: unresolved weapon structure
and unapproved/missing anchor inputs remain prerequisites, not waived gates.
Revert the dedicated readiness/classification commit to undo this item.

## Completed: packaged shellmap rename fallout repair

The required graph boot test failed with `No rules definition for unit
ra1_soviets_barracks`. This was reproduced against the unchanged upstream map
payloads: desert-shellmap-2 had 15 missing placed actors and shellmap_v3 had ten.
The exact replacements are actor-key renames from upstream `ad7c5e232`, not new
naming decisions. The related Lua spawns and map-local rule overrides needed the
same correction; survival's script also retained four renamed upgrade actors.

Reference-only archive edits: desert-shellmap-2 (22 replacements), shellmap_v3
(45), survival (15), total 82. ZIP member order, timestamps, compression metadata,
archive comments and every unchanged member's bytes are preserved. No map terrain,
damage, cost, HP, durability or spawn timing changed. Original archives were saved
outside the worktree for recovery; the main checkout and its maps were not touched.

The shared MiniYAML reader now accepts archive text via `load_text`, using the
same parser as file loading. Eleven parser tests and two packaged-shellmap tests
pass. The tests check every packaged shellmap's placed actor references and Soviet
actor literals in those scripts plus survival; they do not claim full Lua execution.
Menu boot after repair: `MenuPostProcessEffect.PostWorldLoaded`, zero new exception
logs, 43.2 seconds, peak PC memory 69.2%. The owned test game was stopped immediately
after proof. Revert the dedicated map-reference commit to undo this repair.

## Completed: observer combat-value graph integration from PR 323

Adapted Devin AI's graph implementation from PR 323 head
`053e7eeac6f930ef3e178e964a3091d2527cc81a`. The original PR is open/conflicting;
its only merge conflict with this branch was the accumulated lessons document.
This follow-up carries the feature for coordinator review; it does not merge or
modify the original PR. Original authorship is preserved in the commit trailer.

Integration corrections: enum and dropdown ordering now agree for hotkeys; the
axis says value destroyed minus value lost, not enemy-only damage (the pinned
PlayerStatistics accounting can include non-neutral friendly victims). Signed
scaling retains positive-only behavior and continues sampling zero/flat results.
New tests cover ranges, cadence, initial/signed/flat samples and panel indices.

Fresh `make.ps1 all`: zero errors; eight existing engine warnings. The updated
Cameo DLL timestamp and its unique UTF-8 description marker were verified. All
63 Cameo C# tests passed before the separate telemetry tests were introduced.
The repaired tree passed the menu boot described above. Independent source review
approved the graph and map changes; the implementer's own review was not counted
as the independent approval. No live prices, weapons or AI decisions change.

At this initial checkpoint, signed labels, scrolling and clipping had not yet
been reviewed in an actual observer match. See the runtime follow-up below;
a menu boot alone is loading proof, not graph visual approval. Revert
the dedicated observer-graph commit to remove this feature.

## Completed on this branch: record-only match telemetry and AI contracts

Implemented Aedis H.4 phase one, not adaptive AI. The active Player observer reads
existing personality conditions; the active World recorder writes one bounded,
versioned local JSONL file at completed-match notification. Records contain slots,
factions, bot identifiers, team/alliance metadata, initial/final personality status,
outcomes and existing accounting totals. No orders, conditions, prices or decision
logic are changed. Disk failures are non-fatal and do not recurse into disk logging.

The rules fingerprint covers ordered raw Rules/Weapons inputs at world load,
including map overrides; it is explicitly not a whole-runtime hash. Module MVIDs
cover Game/Cameo/Common only. Records are capped at 256 KiB, published without
overwriting old files, and contain no player display names or account identifiers.
Each client may record a match: consumers must deduplicate and inspect metadata.
Completed-world coverage excludes shellmaps, replays, editors and loaded saves;
abandoned matches without GameOver, episode histories and pairwise attribution
remain unavailable. Unknown values stay unknown rather than becoming zero.

Validation:

- All 76 Cameo C# tests pass, including 13 new telemetry cases covering serialization,
  limits, failure handling, fingerprints, eligibility and personality ambiguity.
- Fresh build: zero errors, eight existing engine warnings; bounded tree 967.7 MB,
  PC 48.6%. Runtime DLL freshness checked before the game tests.
- A temporary deterministic playable map completed normally: one match record,
  human Won, medium bot Lost, observed personality, expected 100 value lost, 101
  ticks at 40 ms, populated source fingerprint; zero new exception logs.
- The normally completed match's replay exited normally, produced no new record
  and no exception/desync report. This is a short single-client regression, not
  multiplayer stress certification. An earlier force-stopped recording produced
  an incomplete replay and is not counted as a replay pass.
- Final menu/shellmap boot with telemetry enabled: required menu marker, zero new
  exceptions and no match records; 41.9 seconds. Maximum PC memory across these
  runtime checks was 71.6%, below the 84% guard and user's 90% ceiling.
- Test fixture, two synthetic records, two test replays and benchmark CSVs were
  moved out of game directories into the owned temporary evidence folder. They
  remain recoverable; no Jungle archive or real match record was removed.
- Independent source review challenged the hash scope and disk-error fallback;
  those limitations and the non-recursive failure path were corrected.

H.2 extends the existing AI_ARCHITECTURE document with ownership, current inputs,
future read-only hints, cadence, synchronization and failure contracts for the
measured scoped module inventory. H.3's five differentiated round-two briefs are
written; external services have not been contacted and answers are still pending.
Conflicting learning-stage numbering and stale current PR status were clarified.
This is not completion of all Task H acceptance gates or a merge approval.

Revert the dedicated telemetry/AI-contract commit to remove these additions.
Next runtime work is the observe-only master after review, not dynamic switching.

## Additional readiness and neighboring-PR review

Coverage now separates structures/upgrades from buildable unit-like ledger rows:
632 classified out of 886 non-structural buildable rows (71.3%); 55 have no usable
template, 199 lack a class in the current taxonomy. The all-buildable denominator
remains visible (1956). These are ledger rows, including variants, not deduplicated
units. This is a denominator correction, not hundreds of new classifications.
Unreadable ledgers fail closed. Eleven readiness and 13 class-membership tests pass.
All 27 anchors are assigned to their stated classes, but none are signed and every
class still has a raw stacked-main finding; no prices are authorized by coverage.

PR 321 remains open at `e42eb9914972346f77a931385da62d741f22ae35`.
Its old stat/converter/insurance proposals are not imported. Shared document files
need reconciliation if both PRs proceed, but no shared runtime implementation file
conflict was found in this checkpoint. The original PR was not changed or merged.

## Completed: exact active D2K engineer classification

Task B review identified three unequivocal missed roles: `atreides_engineer`,
`corrino_engineer` and `harkonnen_engineer` inherit `^EngineerInfantryTemplate` from
the active D2K shared pack. The extractor's defaults-only registry missed that
template. Formula V2 section 6b explicitly assigns engineers to support.

The existing extractor now recognizes this exact template when active; arbitrary
pack template names are not inferred as roles. The shared class map maps
EngineerInfantry to support. Three inheritance regressions pass (live actors,
inherited role with no cache mutation, missing/unrelated template rejection).
Independent review also ran nine resolved-firepower and 14 assignment regressions.
Full extraction comparison across 67 artifacts changes exactly three subtype
strings in the D2K raw ledgers, no numeric value or derived artifact.

Before/after: support members 112 to 115; other classes unchanged. Buildable
classified rows 632 to 635, out of 886 non-structural rows (71.3% to 71.7%);
no-template buildable rows 55 to 52. This is a small real classification repair,
not completion of Task B's wider coverage objective. Air/naval/economy taxonomy
gaps and subjective roles are deliberately not guessed. Revert the dedicated
engineer-classification commit and its three ledger strings to undo it.

The final live readiness invocation also exposed two CLI-only defects missed by
the earlier helper tests: formatting missing cost baselines raised TypeError, and
the stacked-main table reused `rows`, replacing the JSON fit rows with the last
class's weapon list. Both are repaired with command-level JSON regression coverage.
The previous statement that the CLI completed was too broad: helper/data results
were valid, but the final missing-baseline table failed. The corrected full command
is rerun as part of final validation; unavailable baselines stay explicit.

## Brief reconciliation: physical-state pricing is already implemented

Task E's claim that status-effect delivery is priced at zero is stale in this base.
`physical_state_price.py`, `formula.physical_state_price_multiplier`, extraction's
derived physical-state fields, and `fit_class.price_unit` already implement the
documented bounded delivery multiplier. The existing 22 physical-state tests pass.
No duplicate weight path or second coefficient was introduced. Model limitations,
including relaxation and changing weapon structure, remain limitations rather than
grounds to apply unsupported prices. Current measured reports take precedence over
the brief's historical binding counts.

## Completed: fail-closed ledger claims and equivalent source cleanup

The `ledgers_drifted` prose measurement previously interpreted any missing drift
marker as zero, including a failed child audit. It now requires a successful,
unique, positive-population clean marker or a consistent explicit drift result.
Unknown output, contradictory markers, zero ledgers and child failures stay
unavailable. Three test methods exercise 15 scenarios using the actual registry
measurement. No documented target or audit ratchet was raised.

`D2K_APC_Rocket_AA` repeated the same compatibility warhead key in two source
blocks. Their disjoint fields are now together in the first block. Comparing all
2,894 active resolved weapon definitions, including values and child order,
finds zero changes. The focused inheritance regression passes and duplicate-key
findings decrease from 261 to the existing ceiling of 260. This is weapon YAML
source cleanup, not a damage, targeting or physical-state rebalance. Extraction
still reports 33 ledgers with zero drift. The post-edit menu gate passed in 36.1
seconds with no new exceptions (63.6% sampled PC memory).

Two existing regression references now use the exact upstream Soviet Barracks
rename already repaired in the packaged maps. Their assertions are unchanged;
all ten weapon-correctness follow-up tests pass. The missing Kotin weapon test is
not mechanically renamed: upstream also changed its profile and operation, so its
remaining failure needs a separate role review. Two readiness test reads now use
explicit UTF-8. Revert the dedicated cleanup/guard commits to undo these repairs.

## Final automated checkpoint (2026-09-07)

- Full isolated Python suite: 93/93 modules, 823 tests run, zero skipped, 42 failed
  modules; final rerun 510.7 seconds, 884.7 MB sampled process-tree peak, 62.0% PC peak.
  Merged PR 328's report has 766 tests, 88 modules and 43 failed modules.
  Independent method-identity comparison finds zero newly failing methods and
  four resolved failure identities. This is not an 823-pass claim: setup/import
  failures and upstream structural/role-contract debt remain visible in the JSON.
- All 76 Cameo C# tests pass. The latest C# sources match the freshly built and
  runtime-verified DLLs; no engine source or pin changes were made.
- Complete canonical audits: final rerun exit 1, 781.8 seconds, 1,119.3 MB process-tree
  peak, 61.9% PC peak, no empty report files. Percentage-runtime passes, 33 ledgers have
  zero drift, and generated templates remain synchronized. Raw document and
  structural findings remain failures; no registry exemptions were restored.
- Fresh structure check fails honestly at 967 reachable stacks against 240 and
  3,577 excess mains against 452. The retired decision-report module is absent;
  its stale test remains an explicit import failure, not a current decision audit
  pass. Older generated decision artifacts must not be treated as current approval.
- Error-handling raw counts improve: discarded errors 88 to 86, unchecked child
  calls 20 to 18; missing-encoding findings remain 92, not hidden by a raised limit.
  All three new AI inventory claims measure exactly (21 types, 36 Player modules,
  one World module); other pre-existing document mismatches remain visible.
- Independent final source/scope review found no new blocker and confirmed the
  unchanged-assertion repairs. Coordinator review remains required before merge.

PR 321 remains unchanged. After the document reconciliation, its five overlapping
paths are DESIGN, LESSONS_LEARNED, doc_claims, and the Atreides/Harkonnen ledgers.
The document changes need manual reconciliation against current authority. The ledgers overlap
only our engineer subtype metadata: preserve both sides' intended metadata and
regenerate, rather than choosing an entire ledger. No shared runtime implementation
file conflict was found. PR 323 also remains unchanged; its graph adaptation is
contained here with attribution.

## Completed: remove conflicting operational document directions

Independent review confirmed four concrete authority/routing contradictions:
TASK_INDEX combined the retired registry with a keep-exemption instruction and a
nonexistent snapshot option; DESIGN's older collapse paragraph prescribed SUM
below the newer VERBATIM ruling; the split plan still taught two warheads/four
inherits; and the program plan still recommended SUM for duplicated mains.

These now point to the current DESIGN section 11b.1. Older implementation plans
and dated examples remain explicitly historical, not executable directions. The
text distinguishes a retained per-main value from the former raw aggregate and
does not call either arithmetic shortcut proof of unchanged delivered behaviour.
No new family choice, damage value or staged-payload policy is inferred. This is
a scoped contradiction repair, not certification of every document in the repo.

## NEEDS A MAINTAINER RULING

The safe choice for this run is no live repricing and no speculative weapon
collapse. All 27 anchors remain unsigned; unequal, target-routed, delayed or
companion payload conversions require reviewed intent, not a bulk sum/drop rule.
The three classified engineers do not settle the remaining 52 no-template and
199 no-class buildable unit-like rows. Broader air/naval/economy taxonomy choices
remain open. External research briefs are prepared but answers are not available.
Coordinator review of PR 329 is the next publication gate, not automatic merge.

### Per-class sign-off disposition at this checkpoint

Command: `python tools/balance/anchor_readiness.py` (complete invocation, exit 0).
Every class is held under the structure-before-pricing gate, with the observed
stacked-main member counts below. These denominators are all class-tagged ledger
members, including non-buildable rows, not the buildable-only coverage denominator.
Counts are review evidence, not an instruction to collapse those weapons blindly.

| Class | Members with stacked mains / tagged members | Decision |
|---|---:|---|
| anti_air_vehicle | 13 / 14 | Hold: unresolved weapon structure |
| archer | 2 / 4 | Hold: unresolved weapon structure |
| artillery | 22 / 35 | Hold: unresolved weapon structure |
| artillery_tank | 7 / 14 | Hold: unresolved weapon structure |
| closecombat | 3 / 5 | Hold: unresolved weapon structure |
| commando | 15 / 30 | Hold: unresolved weapon structure |
| dreadnought | 4 / 5 | Hold: unresolved weapon structure |
| epic_vehicle | 16 / 24 | Hold: unresolved weapon structure |
| fire_support | 13 / 31 | Hold: unresolved weapon structure |
| flying_infantry | 6 / 11 | Hold: unresolved weapon structure; speed input unavailable |
| grenadier | 6 / 7 | Hold: unresolved weapon structure |
| heavy_infantry | 25 / 41 | Hold: unresolved weapon structure |
| heavy_sniper | 3 / 3 | Hold: unresolved weapon structure; only two scored members |
| high_tech_tank | 20 / 26 | Hold: unresolved weapon structure |
| light_tank | 9 / 16 | Hold: unresolved weapon structure |
| line_breaker | 15 / 33 | Hold: unresolved weapon structure; fitted/spec cost differs |
| mbt | 26 / 51 | Hold: unresolved weapon structure; actor restat deferred |
| melee | 8 / 49 | Hold: unresolved weapon structure |
| missile_vehicle | 10 / 14 | Hold: unresolved weapon structure |
| mortar | 4 / 5 | Hold: unresolved weapon structure |
| pure_sniper | 3 / 16 | Hold: unresolved weapon structure |
| rocket_trooper | 15 / 45 | Hold: unresolved weapon structure |
| scout | 12 / 33 | Hold: unresolved weapon structure |
| scout_vehicle | 43 / 52 | Hold: unresolved weapon structure |
| special_forces | 13 / 16 | Hold: unresolved weapon structure |
| support | 32 / 115 | Hold: unresolved structure; no fit, ability-pricing review needed |
| tank_destroyer | 4 / 5 | Hold: unresolved weapon structure |

This records a reason for each refusal, not 27 rejected anchor identities. The
diagnostic HP percentiles and price residuals do not authorize replacing anchors.
Twenty-five classes lack a fitted or target cost baseline in the current report;
23 anchor actors are off their recorded specs. No `fit_class --anchor` write-back
or `signed_off` mutation was performed to conceal those prerequisites.

### Brief delivery status

| Task | Result in this bounded run |
|---|---|
| A: foundation | Formula/round-trip verified; audit defects recorded; unsafe writer repaired and real nonzero throwaway apply verified |
| B: coverage | Ruled Heavy Sniper metadata and three engineer roles repaired; all anchors are members; broader taxonomy remains open |
| C: anchor sign-off | All 27 explicitly held with measured reasons above; no unsupported approval |
| D: faction pricing | Not applied: no signed class; writer implementation is now exercised, not merely a no-op dry run |
| E: physical states | Existing implementation and 22 regressions verified; stale gap claim reconciled, no duplicate pricing path |
| F: weapon shape | One behaviour-equivalent source-key repair; broad role/profile conversions not attempted |
| G: reference synthesis | Not completed; no new per-class reference targets or corpus-grounded anchor percentiles claimed |
| H: AI integration | Graph adaptation, record-only telemetry, scoped module contracts and five research briefs delivered for review; external answers and later decision phases pending |

## Final runtime follow-up

A three-minute scripted match completed with 24 real kills and a final human
value trade of +600 (1,500 destroyed, 900 lost). Its valid replay was inspected
through Computer Use at 1024x768: the graph showed +300, then -600, then +600,
with flat segments and both sides of the zero line visible. The original selector
label clipped; it was shortened to `Combat Value (graph)`. Its fresh menu gate
passed with no new exceptions. The replay produced no additional match record.

An earlier interrupted long fixture left an unreadable replay and is NOT a pass.
A subsequent full long fixture completed normally after 21 simulated minutes:
31,501 ticks at 40 ms, all 80 real kills, human Won with 5,000 value destroyed and
3,000 lost; opponent Lost with the reciprocal accounting. Exactly one completed
record was written, no new exceptions, 1,300.7 seconds wall time, 63.1% PC peak.
It generated a complete 411,828-byte replay for the final scrolling inspection.
The rebuilt replay shows the shortened selector label fully within its button and
the long match's -2,000 segment correctly below zero at 1024x768. After replay
completion, Computer Use verified the default 40-sample viewport: the left arrow
changed the visible minute range from 1–21 to 0–20, and the right arrow restored
1–21. The +2,000 plateau remained readable. This covers those arrow controls,
signed plotting and label fit at 1024x768, not thumb dragging, every resolution
or multiplayer stress. The replay added no match record and no new exception.

The final provenance-comment correction does not change graph logic. Following
the build skill, both pin preflights passed before a fresh build: zero errors,
eight existing engine warnings, 46.5 seconds, 966.0 MB process tree, 44.2% PC peak.
All 76 C# tests then passed again with zero skips. The runtime Cameo DLL timestamp
advanced and its unique telemetry description was verified by UTF-8 byte scan.

Final automated report provenance: canonical refresh through source checkpoint
`a6db521f1`; later source edits are explanatory comments/docstrings only, with
writer's 35 focused tests and all 76 C# tests rerun. Reports are not CI approval.
The recent-changes report retains 32 review-only attribution findings, including
truthful Codex trailers under Blackrobe's author identity; zero R3 findings block.
No attribution was changed to pretend another agent authored this work.

The final post-build menu gate passed in 41.2 seconds with zero new exceptions
and no new match records (64.6% PC peak). Owned test processes were closed.
Thirty graph-test artifacts were moved out of game folders, recoverably: two
maps, six replays (including interrupted attempts), two synthetic match records
and 20 benchmark CSVs. They are in
`%TEMP%/astra_graph_evidence_2b672d603a8e4de29bf5154b37caec45`.
Earlier telemetry smoke evidence remains in its separate owned temporary folder.
No real match record, user map or dirty-main edit was removed. Highest sampled
PC memory across the run remained 71.6%, below the 84% guard and 90% user ceiling.

## September 7 follow-up: upstream integration and writer safety

This section supersedes earlier checkpoint counts, not the limitations attached
to the earlier runtime evidence. PR #329 remains open for coordinator review.

- Integrated upstream `648f62f7c6d8760232a2a5a4c161d545ca07bedf`, including
  the merged headquarters protection from #330 and upstream warhead restorations.
  Both append-only log conflicts retain both sides. The Ordos APC AA weapon keeps
  its restored cancellation node and our duplicate-key cleanup. Its complete
  resolved tree, including child order, equals upstream; the focused behavioural
  comparison also passes. No engine pin changed.
- Corrected the reported Bastion capacity text to five soldiers and the
  Schwarzer Mond Laser Tower description to state that it can attack aircraft.
  Existing laser and upgrade wording is retained. Two resolved-inheritance tests
  check the capacity, loaded translation key and all three air-targeting weapons.
- Balance writes now validate each field's engine type, not merely whether text
  resembles a numeric scalar. Fractional integer fields, integer overflow, WDist
  in integer fields and invalid burst cadence are refused before YAML writes.
  Signed healing damage and the `BuildDuration=-1` sentinel remain supported.
  Writer coverage is 39 tests, including unchanged-file and no-subprocess checks
  when a proposal contains both a valid edit and a later invalid edit.
- Readiness now reads aircraft speed, parses cell-based range and accounts for
  the complete burst cycle. Explicit malformed delay arrays are unavailable,
  not silently defaulted or truncated. Its 16 tests cover these paths. This is
  peak nominal single-armament DPS, not live aggregate damage or a matchup model;
  activation conditions, charge traits and actor modifiers remain unmodeled.
  No numeric unit stats, prices or anchor approvals were changed.
- Regenerated `firepower_inputs.json` with its existing generator against the
  verified current ledgers. It still covers 770 changed actor entries; previously
  stored DPS values predated upstream weapon changes. All nine firepower-input
  tests pass after regeneration. The report does not propose new actor costs.
- Regenerated the raw weapon inventory: 2,367 concrete definitions, 327 stacks
  (239 reachable: 189 direct plus 50 indirect; 88 unreached), and 432 excess mains
  in the reachable graph. Existing raw ratchets pass. Upstream's generator now
  labels the exemption policy retired and counts every stack; no exception was
  hidden. The old test's fixed checkpoint expectations remain failing, rather
  than being mechanically updated as an implicit gameplay approval.

The independent reviewer challenged both changes and found the malformed-delay
fallback; it was corrected and regression-tested before publication. Together
with the two tooltip tests, the focused set contains 57 passing tests.

The integrated build passed with zero errors and eight existing engine warnings.
All 76 Cameo C# tests passed with zero skips, and the fresh runtime DLL contains
the telemetry description marker. The earlier menu/replay evidence predates this
upstream merge: **an integrated game boot is still pending**. No game was launched
for this follow-up, and those older tests are not claimed as new runtime proof.

The upstream comparison worktree has the same tracked tree as `648f62f7c6`.
Its bounded suite completed 807 tests in 89 modules, 44 skipped, with 38 failing
test identities in 30 modules. The final integrated run completed 874 tests in
95 modules, 44 skipped, with 33 failing identities in 28 modules. All 33 are
shared with upstream: no new failing identity and five removed failures, not
an all-green claim. Import failures from retired audit symbols, stale actor
identities, role contracts and fixed-count expectations remain visible.
The final run took 497.8 seconds, with a sampled process-tree peak of 871.3 MB
and PC-memory peak of 52.7%; the upstream comparison peaked at 57.7% PC memory.
Each suite used the 2 GB process-tree limit and 84% PC-memory guard.

The raw and derived ledger check passes for all 33 ledgers with zero drift.
Upstream's new map audit reports zero dangling actors across 363 maps; shrapnel
auditing reports zero cycles or dangling children across 193 chains. The naming
audit passes its existing ratchets but retains its raw findings. Canonical audits
remain red overall; no thresholds or reviewed exceptions were adjusted to hide
debt. All 27 class anchors remain unsigned; this follow-up does not authorize
faction repricing.

The final canonical refresh completed through source checkpoint `dcd26b4cb` in
the complete local environment, without an override. No Markdown report is
empty. It exits nonzero for retained findings; the recent-history audit alone
retains 22 ledger-history findings and four unwired-audit findings, with zero
blocking attribution findings. Its stderr also records historical actor lookups
with no prior definition, not a successful historical lookup for every actor.
Upstream master was rechecked after the refresh and remains `648f62f7c6`.

## September 7: integrated runtime and inherited-test reconciliation

Blackrobe authorized both the integrated runtime smoke and triage of the 33
inherited failing test identities, with a two-hour limit. This section supersedes
the pending-runtime and failing-suite status above. The PR stays draft/unmerged.
Upstream remains `648f62f7c6`; the follow-up started at `b05f184750`.

### Actual merge regressions, not a new balance prescription

Two alternative branches of weapon work were combined in merge `4fd9937f3`.
The repairs restore Aedis's authored role definitions, not the numerically larger
union of both parents:

| Live route | Broken merged flat payload | Repaired payload |
|---|---|---|
| Scooper chemical upgrade, `TSScoopDualChem` | two separate 30,000 mains | one CannonChem_Medium main, 30,000, Corrosion 100 |
| Apocalypse base/elite, `RA2120xmm` | CannonAP 2,000 plus incomplete CannonHE 12,000 | one CannonAP_Light main, 12,000 |
| Apocalypse radiation/elite, `RA2120xmm_rad` | three mains totaling 16,000, with mixed legacy percentage companions | one CannonChem_Light main, 16,000, Corrosion 100 |

Scooper's source is Aedis commit `a92a4bc1bf`; both Apocalypse roots match the
authored definitions in `4fd9937f3^1` (`a92ae850f`) under current templates.
These are gameplay repairs: armor profiles, blast shape, state application and
Apocalypse percentage behavior change. Apocalypse also regains its authored
Inaccuracy 150 and impact/air-effect overrides. Range, reload, burst, burst delays,
report and projectile speed are unchanged. No actor cost, HP, movement speed,
anchor approval, Hydralisk definition, or engine pin changes.

The full-roster comparison covers 2,367 concrete weapons and 156 active/design HP
values. Exactly five concrete weapon definitions change, with none added or removed.
Its generic preservation gate deliberately exits 1: the three flat-damage
changes and four percentage changes above are real, not a pure structural fold.
The exact generated payload and current head snapshot are pinned in tests:
`latest/merge_payload_repair_comparison.json`.

Restoring the authored local Apocalypse effects initially exceeded existing
effect-structure ratchets. Two faction-local effect compositions now own those
overrides; they contain no primary damage or radiation mechanic. The radiation
mechanic remains a separate explicit inherit. The four resolved definitions
retain every authored field. Only four cosmetic nodes in the radiation variants
move before the deterministic radiation update; their relative order is retained.
The test permits that exact permutation, not arbitrary reordering. Independent
engine inspection checked the local/shared randomness boundary for that move.

The complete audit subsequently caught two glow-tier inheritance paths in those
new compositions. Their already-resolved non-glow nodes are now explicit, in
the same order, with one heavy `^ImpactGlow` parent. Both explosion roots are
explicitly classified as emissive, not exempted. The full ordered reference test
still passes and the glow audit has zero findings. This bounded duplication keeps
the authored effects visible rather than weakening the single-glow-path rule.

### Tests reconciled without making old converters permissive

- Retired exemption symbols no longer prevent 14 modules from importing. Raw
  inventory tests count every stack; historical PR320 artifacts stay untouched.
- Current identity/role tests follow the renamed Soviet Mammoth and Outpost2 EMP
  routes, the deliberately self-contained Ordos air mine, the already-consolidated
  D2K shotgun parent, and Kotin's authored nuclear upgrade, including death routing.
- A test-only historical view asserts each exact modern field value, reverses
  only the independently reviewed delta in a copy, then runs the original stored
  fingerprints. This covers explicit Corrosion-binding cleanup, generated armor
  coupling cells, LatinSmoker's authored effect-parent removal and TSPulse's dead
  Falloff field. Converter source/guards and historical hashes remain unchanged.
- Exact Flak damage/percentage/target tuples and all unaffected descendant
  closures remain checked. The independent reviewer found those checks missing
  from an early migration; they were restored before publication.
- Derived-DPS tests retain their live role/geometry/upgrade guarantees and compare
  extracted values with the current model, rather than freezing an older census.
  The ledger layout test recognizes the two existing reference sidecars explicitly;
  an unknown orphan still fails.
- New regressions pin both repaired weapon families, effect ownership, and the
  historical-view helper's rejection of unreviewed values and missing fields.

Raw inventory is now 322 stacks: 234 reachable (184 direct plus 50 indirect) and 88
unreached; reachable excess mains 425. The preceding integrated measurement was
327/239/432, so this work removes five reachable stacks and seven excess mains.
Raw/broadcast/reachable ceilings only move down. The separate weapon-shape audit
uses a different predicate and reports 389 multi-main weapons; it is not relabeled
as 322. Its six current buckets are 576/210/12/51/389/694, all within tightened limits.

### Runtime evidence and limitations

The integrated menu/shellmap rendered at 1024x768. Fresh three-minute fixture
matches exercised 24 real attacks/kills, normal completion and match recording:
4,501 ticks at 40ms, 180,040ms simulation, value destroyed 1,500 versus lost 900.
The observer replay showed positive and negative values and the final +600 plateau;
the complete Combat Value label fits at 1024x768. Replay completion did not create
a duplicate match record. This is an integrated smoke, not long-match, multiplayer,
AI-personality, or whole-roster balance proof.

One intermediate repair boot failed on obsolete Scooper removal nodes. They were
removed only after confirming their targets disappeared with the retired parents,
and are now guarded explicitly. Python resolved equivalence had missed that strict
engine error. The repaired match/replay subsequently exited normally with no new
exceptions; the final effect extraction also passed the actual menu boot marker.
Owned temporary maps/replays/records are recoverable in the local Temp evidence
folder, not published as gameplay content or left in the normal match corpus.

Before the field/order-identical single-glow materialization, the effect-template
tree completed a fresh match in 220.1s and its
replay in 217.6s, both normal exit 0 with no new exceptions. There was exactly one
match record before and after replay. Its captured source hash is
`8035f04237e923c35be1f4e97b614108814bcbaaa77d405088604c940671d0ed`.
The local evidence is under
`%TEMP%/astra_pr329_runtime_evidence_20260907/final`; cleanup restored zero test
records in the normal match corpus and removed the fixture from the mod.

The final single-glow source checkpoint `6d0219550` independently passed a fresh
menu/shellmap boot: the actual `MenuPostProcessEffect.PostWorldLoaded` marker is
present, with no new exceptions. The owned process was stopped at 100.6s, not
reported as a normal match exit. Both effect templates and all four weapons have
identical resolved fields and child order to the match-tested checkpoint, as
independently verified. The new boot's sampled PC peak was 72.7%.

All 76 Cameo C# tests pass with no skips.
Raw and derived extraction checks pass for all 33 ledgers with zero drift; only
the Soviet RA2 and Forgotten ledgers/sidecars have content changes. The percentage
runtime audit reports zero dispatch findings. Sampled PC memory has stayed below
73% through these runs, with an 84% stop guard and 2 GB Python-tree guard.
The earlier dependency-enabled full run completed all 98 modules: **930 passed,
44 retired-feature skips, zero failures** (974 tests). This also runs the 15 cases
that the default interpreter skipped for optional dependencies. It took 583.4s,
with sampled tree peak 863.9 MB and PC peak 50.1%. No packages were installed.

A follow-up run correctly detected a source-comment edit during a converter's
read-only byte check. That interfered run was stopped, not counted as a passing
run. Source was frozen and the complete suite restarted; final results follow.

That final frozen-source run completed at `6d0219550`: **930 passed, 44 existing
retired-feature skips, zero failures**, all 98 modules (974 tests). All optional
dependency tests ran. Duration 600.6s; sampled Python tree peak 889.8 MB and PC
peak 52.1%. `latest/bounded_test_run.json` contains this final run, not the
interfered run. No source changes followed it.

The first canonical refresh used an interpreter without openpyxl and would have
replaced the balance-sheet evidence with a dependency error. That partial run was
discarded as publication evidence. The final complete canonical run at source
checkpoint `6d0219550` used the bundled dependencies and the complete engine
environment, without a force-latest override. It finished in 730.0s, sampled tree
peak 1506.0 MB and PC peak 52.2%. All reports are nonempty and the full workbook
comparison is retained. Overall exit 1 remains honest: inherited nuclear-flash,
split-definition and other backlog findings are not waived. The new glow and
registered-count findings are fixed; structural ratchets and percentage dispatch
pass, empty-type warheads are zero, and all 145 generated templates have zero
drift. Engine freshness still discloses the clone/pin mismatch and unavailable
`mtr/rv-engine` ref; it is not an upstream-engine freshness certification.

Revert boundary: revert this follow-up's implementation commit together with its
generated ledger changes and associated regression/ratchet updates. To revert
only one gameplay decision, restore that faction's weapon block and re-extract
its ledgers, then regenerate comparison evidence and adjust the corresponding
tests honestly. Do not replay any historical converter over current upstream.
