# Four-faction balance TODOs — 11 September 2026

This is the request and evidence inventory for the four-faction balance pass.
Use the [grand plan](GRAND_PLAN_20260911.md) for execution and the
[project status](PROJECT_STATUS_20260911.md) for current state and ownership.
Checked evidence items do not mean their larger gameplay deliverable is complete.
The original requests remain visible; this is not a diagnostic-only replacement
for the intended balanced candidate.

## Operating boundary

- Blackrobe resumed implementation and authorized scoped publication to the
  existing draft PR. Scheduled Discord monitoring is **ACTIVE** every 15 minutes
  through 14 September 2026 at 00:16:58 WIB. See the project status for current
  ownership and the CL-01 reservation.
- While monitoring is active, preserve native Discord **Reply** with the
  `[Codex]` prefix and substantive milestone-only communication. A completed
  small report does not automatically justify another message.
- Preserve the overnight worktree and frozen baseline artifacts. Stage only
  reviewed continuation files for publication to Blackrobe's fork; do not push
  to the upstream organization, reset, clean or merge.
- Current Cameo/base factory-ready states are the first comparison scope;
  upgrades, alternate factions, runtime playtest and loader work remain
  separate until their prerequisites are evidenced.

## Completion measure

The previous "half-done" criterion measured diagnostic preparation only and
is withdrawn as a project completion claim. It is not a trigger for resuming
Discord. Track M1–M5 in the grand plan; no overall percentage is currently assigned.

| Request area below | Execution task |
|---|---|
| 1, 1a, 5, 6, 7: identity, source evidence, presentation, projectiles and armor | GP-02, then GP-04 |
| 2, 3: targeting, roles and multiplier disposition | GP-03, then scoped GP-06 |
| 4, 8, 9, 12a: cargo, calibration, geometry and promotions | GP-01, GP-04 and GP-05 |
| 10: runtime and playtest; handoff/preservation | GP-07 and GP-08 |
| 10a, 11, 12, 13: survivability, loading, expanded states/factions and bots | Explicit follow-ons; retain their stated dependencies |

## Active checklist

### 1. Source identity and reference coverage — **done (diagnostic)**

- [x] Keep the 163-actor map, 282 identity links, 195 peer cycles and the
  Mammoth `4TNK` three-source mapping.
- [x] Keep the corrected contract: Current Cameo plus exactly three distinct
  reference voices; do not renormalize a missing voice.
- [x] Keep the coverage inventory that distinguishes candidates from
  gate-ready rows.
- [x] Correct the peer extractor's utility-first armament selection so a
  capture/repair weapon cannot erase a later positive-damage weapon; retain
  the unarmed fallback and focused regression checks.

Acceptance: the map and inventory remain reproducible without mutating source
or YAML data.

### 1a. Reference-map presentation — **done (diagnostic)**

- [x] Keep the actor map focused on HP, Speed, Range, DPS and Cost, showing
  current and reference values together.
- [x] Move class/mapping provenance and generic weapon, projectile, spread,
  falloff and delivery details into a separate expandable section.
- [x] Keep damage per shot, burst, burst delay and reload delay available as
  detail rather than additional actor-table columns.

Acceptance: `docs/audit/latest/reference_map_clean_20260911.html` renders the
five-stat table and separate generic evidence without changing source or YAML.

### 2. Targeting, roles and delivery elements — **partial**

- [x] Retain the 36-route targeting fixture, held-missile corrections and the
  Sonic family/delivery coverage report.
- [x] Refresh active target-mask and trait-level secondary-route receipts,
  retaining custom-tag, selection-only and unresolved-scope limitations.
- [x] Add the all-route FireShrapnel scenario receipt: recursive chains,
  AimChance/target-availability credits, flat versus percentage payload status,
  and parent/emitter/fragment mask evidence.
- [x] Add a read-only missile role/class triage receipt with inheritance,
  actor-consumer and custom-selector context for the remaining strict cases.
- [x] Group the strict role findings into a review-only decision packet,
  merging the duplicate R3/R4 rows and separating absolute-rule, single-domain,
  custom-selector and V2 policy lanes.
- [ ] Resolve the remaining global role/class cases, including the V2 Tesla
  SCUD parent Air role, missile HE/AA/AP ancestry and anti-ground/AA edge
  cases.
- [x] Finish the bespoke Sonic/Cryo/status-effect route audit before any role
  vote; keep status valuation, uptime and resistance as a separate deferred
  decision.
- [x] Tag point-defense interception as armament-level support pricing, retain
  its resolved payload for route evidence, and fail closed when a buildable
  actor has no priced non-support positive armament.
- [x] Correct the shared `PDLaser` warhead mask to cover grounded and airborne
  projectile target states without adding ordinary-aircraft splash eligibility;
  retain runtime interception as a separate unverified engine path.

Acceptance: every changed route has an explicit source or policy reason, and
unresolved global cases remain visible rather than being forced into a class.

### 3. Firepower model and multiplier retirement — **diagnostic worklist done**

- [x] Keep the 30-actor/100-context explicit-damage pilot and the 10-credit
  grid result.
- [x] Generate `docs/balance/firepower_retirement.md` for all 404 main
  warheads on 122 actors carrying unconditional `FirepowerMultiplier`.
- [x] Record the worklist's 404 flat-grid folds (392 exact, all within its 1%
  arithmetic tolerance). This is not shared-consumer or full-payload behavior
  proof; do not apply a global retirement from this count.
- [ ] Obtain separate content authorization before editing set-B weapon YAML;
  do not bulk-edit it from this checklist.

Acceptance: the report separates exact/within-1% folds from damage decisions
and contains no gameplay writeback.

### 4. Cargo and pricing — **done (proposal)**

- [x] Keep all 11 valid full-load price matches and the three 10-credit-grid
  passenger corrections.
- [x] Keep the explicit naval-empty, air-one-each and varied-advanced-load
  policy in `cargo-load-proposal-20260911.json`.
- [ ] Prepare and apply the later named load/capacity/cost batch after
  implementation resumes and its specific content scope is established. Preserve
  accepted cargo policy and previously corrected costs; do not reapprove or replay
  completed work.

Acceptance: modeled load weight equals declared capacity; exceptions are
  named and remain `NOT_APPLICABLE` where policy says so.

### 5. DTA preprocessing and armor fallback — **done (static evidence)**

- [x] Keep the generated-key closure, 194-row armor evidence and authored
  Damage attachment.
- [x] Keep the Tesla additional-payload trace and the explicit limitations on
  installed-binary applicability and cadence.
- [x] Verify the guarded single-source DTA extraction path against the corrected
  Rules.ini/Enhance.ini pair; resolve `$Inherits=` per file before overlay,
  refresh only the 1,726 DTA rows with provenance, and regenerate the static map.
  The destructive merged-file replacement and the current-base-compatible merge
  are documented in `docs/audit/latest/dta_refresh_readiness_20260912.md`.
- [x] Refresh the derived faction/armor profiles and close the Japan-pilot
  provenance list for the evidence helpers they transitively consume. Keep
  unmapped TS extension armor tags explicit until their ladder semantics are
  reviewed.
- [ ] Resolve the remaining runtime/client-version and secondary-payload
  uncertainties before using DTA as a gameplay-equivalence claim.

Acceptance: inherited keys and fallback routes are hash-backed, and original
declared coefficients remain unchanged.

### 6. Projectile and geometry evidence — **done (static evidence)**

- [x] Keep the 598 peer, 343 Cameo and 123 DTA projectile records and 624
  first-impact timing records.
- [x] Keep the geometry inventory and source-position/instant-hit caveats.
- [ ] Complete guided arrival, DTA frame-period and shrapnel/scenario
  integration before using projectile travel in DPS votes.

Acceptance: unsupported guided or secondary behavior stays unresolved; no
  speed/DPS vote is changed by the diagnostic.

### 7. Channel and armor synthesis — **in progress (critical path)**

- [x] Keep the explicit slot/state/target selector and source-channel reducer.
- [x] Keep the four-source gate and Aedis-directed infantry, vehicle/ship and
  aircraft ladders as opt-in policies.
- [x] Add explicit DTA base-channel status handling, hand-author a core
  selection manifest and run the four-voice gate on 12 groups.
- [x] After the gate cohort is accepted, reduce each selected source from its
  explicit `channel_terms` before the vote; preserve max-HP, direct and
  ambient components separately and compare the sum with adapter `terms`.
- [x] Extend the resolved cohort with nine hand-authored base infantry groups
  and record the explicit None/Flak/Plate ladder beside the vehicle ladder.
- [x] Extend the same contract with eight hand-authored aircraft-target groups
  and preserve the explicit Fighter/Bomber/Helicopter/Spaceship interpolation.

Acceptance: the manifest is caller-owned, every row has a reviewed index and
metadata, channel sums are checked before the gate, and missing/unsupported
status or axes fail closed. Receipts:
`docs/audit/latest/four_voice_pilot_v6_20260911.json` (12 vehicle groups) and
`docs/audit/latest/four_voice_pilot_v7_20260911.json` (21 groups including nine
infantry groups) and
`docs/audit/latest/four_voice_pilot_v8_20260911.json` (29 groups including
eight aircraft-target groups).

### 8. Calibration, anchors and band triage — **partial**

- [x] Keep the band-scope report, 31 reference-complete contributors and the
  explicit R4-versus-fitting metric-basis diagnostics.
- [x] Classify all 37 current band flags into hard/soft threshold and review
  lanes, retaining derived-class, source-limit and unsigned-anchor blockers.
- [ ] Review the 37 provisional flags in 14 of 23 evaluated classes after source
  coverage and role validity improve.
- [ ] Decide anchors and cost residual handling only after the four-voice
  cohort is resolved; do not force prices to fit incomplete coverage.

Acceptance: every proposed anchor names its metric basis and exclusions; no
  frozen self-vote baseline is silently rebased.

### 9. Incoming geometry and defense factors — **partial**

- [x] Keep the one-application-per-channel/tick shape review and the Bastion
  50% / Soviet-Nod SAM 75% inactive-factor evidence.
- [x] Adopt the static shape policy: retain realistic hitboxes and do not apply
  a universal HP or incoming multiplier; any area-damage-only compensation
  requires a separate pilot and explicit approval.

Acceptance: no HP conversion or incoming factor becomes live without an
  explicit policy decision and interaction review.

### 10. Runtime and playtest — **pending**

- [ ] After static candidate evidence is complete, run the authorized
  four-faction Sunday playtest with current Cameo as the permanent voice.
- [ ] Record player/PvP findings, runtime target behavior and regressions
  separately from static arithmetic.

Acceptance: runtime results identify build/engine state and scenario; static
evidence is never described as gameplay certification.

### 10a. Infantry late-game artillery pressure — **diagnostic complete; policy pending**

- [x] Add explicit center-impact pressure examples for one base infantry target
  and one representative area weapon per four current factions, keeping flat
  and max-HP components separate.
- [ ] Choose and playtest any survivability policy (cover, armor layers,
  regeneration, piercing or bypass) without weakening artillery by default.

Acceptance: the pressure receipt states target HP, source record indices and
all excluded falloff, cadence, armor, movement and secondary-payload assumptions.
Receipt:
`docs/audit/latest/infantry_artillery_pressure_20260911.json`.

### 11. Loader and content-pack scope — **deferred**

- [ ] Revisit selective faction/content-pack loading after the balance
  candidate is stable. The current audit is proposal-only.

Acceptance: loader changes remain isolated from the current balance pass and
  are reviewed for dependency and startup behavior first.

### 12. Upgrades, status valuation and expanded factions — **deferred**

- [ ] Finish Cryo/Sonic status valuation, upgrade pricing and maximum-upgrade
  models after base/factory-ready rows are resolved.
- [ ] Expand the same evidence contract to Japan and other loose-reference
  factions later.

Acceptance: base values are not mixed with upgrade values, and unsupported
factions remain explicitly out of scope.

### 12a. Promotion-unit discount — **pilot direction accepted; evidence repairs complete**

- [x] Trace the existing prerequisite-chain tier curve and promotion-column
  depth across the four current factions; compare fixed 5000 and 1000/1500/2000
  virtual-credit candidates without changing promotion inherits or costs.
- [x] Record Aedis's 17:32 native Reply accepting the 1500-per-tier pilot
  proposed at 17:30; retain 2000-per-tier only as sensitivity context.
- [x] Inventory authored replacement markers and compare the resolved
  promotion/base pairs on HP, speed, range, nominal primary DPS, armor and
  recognized warhead class. **The resulting verdicts are unreliable:** the
  inventory needs the E2–E3 mapping/metric corrections in the grand plan.
- [x] Inventory resolved promotion/upgrade condition hooks and conditional
  stat traits. **This does not certify a fresh state:** E4 repairs partial
  unknown-expression handling and classification limits.
- [x] Correct E1–E4: remove the inactive-firepower rationale, resolve explicit
  replacement identities, bind metrics to their weapon, and retain individual
  unknown condition identifiers. Use the GP-01 successor receipts.
- [x] Define the exact pilot inherit-removal and pricing scope in
  `PROMOTION_CARGO_BATCH_20260911.md`; application waits for final GP-04 prices.
  Revisit the accepted coefficient
  only if corrected impact materially changes the proposal; no blanket approval
  request for ordinary tool corrections.
- [x] Check the approved 1500-per-tier batch against the current GP-04 table;
  the readiness receipt records 0/40 promotion consumers ready, so no partial
  gameplay batch is safe. See
  `docs/audit/latest/promotion_batch_readiness_20260912.md`.

Acceptance: the candidate reports preserve `C`, `f(C)`, promotion tier,
relative discount and the C <= B plateau explicitly, and separate the 40
promotion-unit inherits from nine non-promotion inherits in the current
factions. Shared `~!promotion` tokens identify candidate edges, not every unit's
replacement. Use explicit replacement identity and consistent combat metrics.
The following receipts are historical pending GP-01 correction:
`docs/audit/latest/promotion_discount_20260911.json` and
`docs/audit/latest/promotion_superiority_v3_20260911.json` and
`docs/audit/latest/promotion_upgrade_interactions_20260911.json`.

### 13. Bot-module fairness and architecture — **deferred dependency**

- [x] Capture the supplied Astor/Aedis brainstorming as a bounded Cameo 1.1
  backlog with deterministic squad, formation, target-priority, coordination,
  wave, air-response, telemetry and profiling stages.
- [ ] After the rebalancing candidate is stable, inventory current bot modules
  and identify which advantages are policy/configuration (map vision,
  production speed, cost, passive income) versus architecture limitations.
- [ ] Produce a bounded feasibility estimate and a staged parity plan before
  changing bot behavior; keep any machine-learning question separate from the
  deterministic module work.

Acceptance: no bot change is mixed into the balance/playtest candidate, and
the estimate names the existing module boundaries, likely runtime scope and
player-impact risks. Backlog:
`docs/balance/CAMEO_1_1_BOT_MODULE_BACKLOG_20260911.md`.

## Aedis history intake through 10 September

The DM review confirmed these requests and their current disposition:

- Three-reference coverage and base-only states are inventoried. The frozen
  actor-stat self-vote remains valid for the five-stat pipeline, but the armor
  channel pilot never bound its later Cameo dataset to the immutable baseline;
  the consolidated successor therefore fails all 29 channel votes closed.
- Warhead-versus armor comparison, source aggregation, arithmetic/geometric
  means and separate infantry/vehicle/aircraft ladders: gate and the
  29-group mixed pilot are implemented; full roster synthesis, target-HP
  scenarios and live Versus proposals remain open.
- Projectile speed, spread and falloff: reference-only inventories are done;
  guided arrival and runtime timing remain open.
- FireShrapnel parent matching, aim chance, target availability and recursive
  chains: static route and scenario receipt is now done; armor/falloff,
  runtime eligibility and pricing integration remain open.
- Cargo passenger-sum pricing, varied early/late loads and capacity matching:
  proposal and static checks are done; YAML/load publication remains separately
  authorized work.
- Hidden multipliers, status valuation, upgrades, Japan and loader work: kept
  isolated or deferred according to the recorded four-faction test scope.
- Sonic/Cryo status routing: active emitters, condition consumers and the
  physical-state double-application guard are now receipt-backed; scalar
  valuation and runtime uptime remain deferred.
- New bot-module question (11 September 16:00 WIB): estimate fairness-removal
  effort after rebalancing; no implementation belongs in this pass yet.

## Immediate execution order

Follow the live ownership table in [project status](PROJECT_STATUS_20260911.md).
The Astra review corrects GP-01/helper edge cases, withdraws the GP-03 completion
claim and reverses the Havoc role regression. GP-02 has 71/71 original ledger
inputs recovered, with original per-armor semantics still unverified. GP-04
now propagates class-level DPS holds (13 reviewable, 18 held); GP-05 remains
non-live until final prices. The complete `astra_review_20260911/candidate_proposals`
table covers all 163 actors, including separate economy, support, cargo,
garrison, limited-unit and air/naval/defense-model routes. The Discord heartbeat
is active every 15 minutes through 14 September 2026 at 00:16:58 WIB and uses a
new temporary external-browser tab for each check.

The support-pricing correction now marks nine point-defense armament routes on
eight actors as support-only, keeps their payload evidence, and guards against
buildable actors with no priced non-support positive armament. It changes no
pricing values; the same batch adds the shared `PDLaser` projectile-target
mask correction, with runtime interception still unverified.

Reference-map tooling now labels its source-local rate as `damage/tick`, applies
the accepted all-17 cargo-class move in the pending review map, and writes its
pending artifact through the Windows OS temp directory. The condition-gating
rewrite from PR #347 remains excluded; the reference selector now uses the
shared built-state evaluator and has focused Tesla Coil, IFV and GDI battle-tank
regressions. Its existing strongest-armament fallback remains a diagnostic
limitation when no priced armament is active. The four-faction HTML map was
regenerated from this selector (66 originals, 82 expanded, 270 references, 23
formula-priced rows) and is still review-only.

## Current state

The full balance candidate is **incomplete**. The historical diagnostic milestone
does not establish 50% overall completion. The firepower worklist is written, and the
explicit DTA-backed cohort is now 29/29 assembled, channel-aggregated and
gate-resolved with no errors across vehicle, infantry and aircraft-target
scenarios. The current receipt is
`docs/audit/latest/four_voice_pilot_v8_20260911.json` (the readable summary is
the paired `.md` file); v6 remains the vehicle-only component and v7 the
vehicle-plus-infantry component. The all-route FireShrapnel receipt is
`docs/audit/latest/shrapnel_scenario_20260911.json`. Milestone-only Aedis
Replies have been sent for the resolved cohort results. Calibration, armor-component,
runtime, bot-module and other deferred tracks stay open. The current
role/class triage receipt is
`docs/audit/latest/missile_role_triage_20260911.json`; it records 28 strict
findings, 27 custom selectors and three V2 Tesla SCUD policy rows without
changing any role or target mask.
The grouped review packet is
`docs/audit/latest/missile_role_decisions_20260911.json` (with a Markdown
summary); it merges the five R3/R4 duplicates, leaving 28 unique strict cases
in five absolute-rule and 23 single-domain review lanes. It is not a role
conversion proposal. The FirepowerMultiplier disposition is recorded in
`docs/balance/firepower_retirement.md`: its flat rounding result is not complete
behavior-preservation evidence or authorization for a global YAML batch.
