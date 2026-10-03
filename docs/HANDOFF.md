# Cameo — THE HANDOFF

## 2026-10-03 — Claude (coordinator): EL-0 engagement log (learning tier 0) + the five learning tiers handed to Devin

`Agent: Claude-Local (Opus 5.5) · coordinator · branch claude/el1_engagement_log → PR`

**Landed earlier today (master `f07023d03`, via NOVA's master-sync):** #779 emergency = losing (§19.11, `AL_emergency_net_loss`),
#780 BO-2 lab contract, #782 army staging (§19.12 / AI_ARCHITECTURE §12.29, `AM_army_staging`), #783 claims re-pin, #787
binaries untracked. All default-off. Master verified: build 0 errors, 794/794 tests, fog / direct-mutation / arch-freshness PASS.

**This PR — EL-0, the record-only engagement log (DESIGN §19.13, AI_ARCHITECTURE §12.30):** every fight is one scored
line in `Logs/cameo-ai-engagements.jsonl` (`engagement/1`, plus a `posture` record every 250 ticks with the army's
distance to its staging point). `seen` vs `truth` blocks (truth = offline only, one manifested site). Runs for every
bot incl. classic (logging is not behaviour; zero orders, zero conditions). Report: `tools/ai/engagement_report.py`.
Research basis: `design/AI_LEARNING_RESEARCH_2026-10-03.md`. The maintainer adopted the **five learning tiers** (§19.13).

**#788 (open, maintainer merges):** DAWN's `81fa5a3c5` (per-player answer tracker) was committed only in the SHARED main
checkout with an origin/master merge left staged there; #788 lands that exact commit (gated). After it merges, the main
checkout's staged merge must be aborted and fast-forwarded (the sync job refuses while it is dirty). **Maintainer
authorised Claude (2026-10-03) to do exactly that once #788 is on master:** `git merge --abort`, then fast-forward to
origin/master, then confirm `sync_main_checkout.log` runs clean.

**Next (in order):** (1) merge this PR + #788. (2) Devin builds tiers 1–3 (fleet `ORDERS_2026-10-03_claude_learning_tiers.md`):
EMBER tier-1 fitter, NOVA tier-2 veto, DAWN tier-3 pooled bandits. (3) ONE increment A/B of every default-off group
(D, E, AG, F2, ST, AL, AM, …) with EL logging on both arms — EL's scores are the A/B's new per-fight metric.
(1b of 10-02, the coherence pass, is DONE: §12.20 gives SP-1/HS-1/AF-1 one owner each; CV+ATK-1 are one state.)
**Open (balance lane, not measured yet):** `audit_doc_claims` on master: `ledgers_drifted` 0 → **33** (was 1 this
morning). Suspect the maintainer's `FirepowerMultiplier@GlobalBuffs` 25 → 50 (`612014a74`) — ledgers price effective DPS;
re-extract via the pipeline (rule 3), never by hand.
**Process (WORKFLOW §1.7–1.8, maintainer today):** checkpoint HANDOFF + DEVELOPMENT_LOG at every milestone; Devin is free.

## 2026-10-02 — Claude (coordinator): INC-4 claude batch lands; the two formations are one; scale targets ruled

`Agent: Claude-Local (Opus 5.5) · coordinator · branch inc/2026_10_02_claude → master`

**Landed (all behaviour default-off; master's default play is unchanged):**
* **CV concave + ATK-1 fan-out → ONE deploy-before-commit state.** DESIGN §19.3: CV's geometry and state machine
  (range-matched, arc width grows with the army, ranks, bearing pairing, terrain snap, staggered arrival), behind ATK-1's
  `AssaultFormationBotModule` provider seam (the only switch: `AG_assault_fanout`). `AI_ARCHITECTURE.md` §12.7a.
  ATK-1's 3-0 batch measured its OLD ring and does not transfer: **the unified state needs its own A/B.**
* **CA F2 part 2:** the 9 blocked upstream files vendored (CA drift STALE 9 → 0); the Feb-2026 AI fixes behind
  `F2_ca_f2p2` — air limits incl. fog-honest air threats (`ObservedAirThreats`), armour-based air targeting, routes
  from own buildings, upstream state tweaks, and the maintainer's WP-A5 rulings (`PreferBuildingTargets`,
  `ValueOnlyAttackLaunch`; compositions after INC-4). `UnitBuilderBotModuleCA@generic` is shared with classicbot
  and extended by 34 ContentPacks, so it is not split: its switches act only while `SwitchCondition: genericbot` holds.
* **Master was red:** `b39f71149` added a fog-audit site (the LegacyBridgeHut scan, neutral) without a manifest entry; fixed.
* #765 (DAWN arch audit) merged; #716's orders-only conversion is on master via the Fransbot re-vendor
  (`audit_bot_direct_mutation`: zero sites), so **group E (transport) may be armed in the next A/B.**

**Ruled today (maintainer):** DESIGN §19.10 **scale targets**. Every base and army size is one target:
`floor(P × max(Min→Max line × time growth, Ratio line × seen enemy × (1 + margin × unscouted share)))`. It replaces
every fixed per-tier cap and the hand-written `BuildingLimits`, has no time cap, and is fog-honest. Spec: AI_ARCHITECTURE
§12.22, including how it fits with the expansion planner, the utility axes, the global unit budget and the harvester
insurance.

**Next (in order):** (1) ✅ ST scale targets LANDED (switch `ST_scale_targets`, inert on master; findings in §12.22 'Implemented': no MCV manager reads ConstructionYardLimit, no defence cap exists, refinery has no physical cap yet). (1b) the §19.3 coherence pass over the 10-02 duplicates (assault fan vs §12.7a, MinBuildingGapCells vs SP-1, MaxHarvestersPerResourceIndice vs HS-1, MinArmyUnitsBeforeBuildings vs AF-1). (2) **One increment A/B**
of every default-off group on master, mirror matches only, ≤ 3 drivers: D, E, AG, F2, H… plus ST when it lands.
Arms per WORKFLOW §4. (3) Round-trip test of the whole AI (HANDOFF 2026-10-01 step 3).

**Doc claims (pre-existing on master `6cf5527c1`, not from this batch):** `audit_doc_claims.py` FAILS on 7 balance claims —
`shield_versus_mean` 97.6→184.7, `shield_hp_factor`, `shield_damage_share`, `percentage_denominator_unset` 436→423,
`ledgers_drifted` 0→1, `armament_reference_tier_original` 140→141, `armament_pairing_input_fingerprints` 476→514. A
warhead/Versus change landed without its claims (balance lane; rules 3–4: investigate which merge moved the shield profile
before re-pinning — a doubled Shield mean is a §12.0c question, not a number to copy). The 2 AI-contract counts are fixed here.

**Process note:** agents merged ~60 PRs to master on 10-01/10-02 (WORKFLOW §2: only Claude merges). Each was checked for
default-off behaviour where it overlapped my lane; the ATK-1 duplicate is the only overlap found.

## 2026-10-01 — Claude (coordinator): three increments landed, the increment A/B says ship the switches, the plan for every agent

**Read first, every session: [`WORKFLOW.md`](WORKFLOW.md)** (binding: plan first; Opus specs/reviews/merges; Sonnet
sub-agents code; only Claude merges and runs A/B tests; increments not per-PR tests; ≤ 3 game drivers). Design rulings
of this day: DESIGN §19.6 (order gate), §19.7 (defence coverage), §19.8 (a bot acts only through orders), §19.9
(engineers), §23.1 (disc drain ×−1).

### Verified state (master after this entry's merge)
* **INC-1 (#702), INC-2 (#703), INC-3 (#709, #710)** carry every agent's work of 09-30/10-01: LC1 squad claims (#681),
  MI squad micro (#696), §19.6 order gate (#699), LC5 ownership watchdog (#695), LC6 canaries (#700), LC8 squad outcomes +
  raid dormant shelf, engineers v2 (safe route re-check, stealth only when unguarded, one per target, escorts #693,
  transport runs #694/#698/#707), BEV (#685), §19.1 ungating (#672), F1 as switch group C (#708), defence coverage v1+v2,
  the learning loop's return leg (`BotLearnedPriors` + the first `mods/cameo/ai/learned/arsenal_priors.yaml`),
  `round_trip_check.py`, fast A/B harness (`--render fast`, BELOW_NORMAL), `ab_increment.py` (#706).
* Also: CLAUDE.md core (#705), Floating Disc drain inverts plants (#714, DESIGN §23.1), WORKFLOW.md (#717), NOVA's
  ZG-a/b/c tactical map (#711/#713/#718 — ⚠ merged by agents; ZG-c's `UseZoneTopology` is now **default off**, group D),
  29 CA verbatim syncs (this entry's increment).
* 444+ C# tests green; fog audit green (master went red twice after agent merges without manifests — #712, #715).

### The INC-1+2+3 A/B (`C:/tmp/inc3ab-out`, hard vs classic, A Nuclear Winter, mirrors only, 16 per arm)
| arm | hard | win % (95% CI) | mean length | units ordered by two modules | order gate |
|---|---|---|---|---|---|
| ctrl `bea5573a2` (pre-INC-1) | 12–4 | 75% (51–90) | 31,562 t | **216** | — |
| base `dfef889b6` (defaults) | 8–6 (14/16) | 57% (33–79) | 32,782 t | **0** | would refuse 238, crossed 111 |
| all (+53 switch changes, groups A+B+C) | **12–3** (15/16) | **80% (55–93)** | **27,981 t** | **0** | refused 325, crossed 12 |
**FINAL 48/48: ctrl 12–4 · base 9–7 · all 13–3 (81%, 26,770 t). Step 1 DONE: groups A+B+C shipped as defaults (#720).**
Read: `all` does not lose (it leads, and wins faster); ownership is fixed in both new arms; `base` alone trails — the
defaults ship machinery whose payoff needs its switches. **Decision pending the last 3 matches → next step 1.**

### What is left — the plan, in order
1. **Ship the A/B result (Claude, first thing):** when the supervisor log says `all shards DONE`, re-run `ab_summary`
   per arm. If `all` ≥ `ctrl`: make groups **A** (squad tactics) and **B** (ownership/engineers/missions/learning/defence
   coverage) the master defaults for genericbot — EXCEPT the `engt-transport` re-arm (a multiplayer desync risk until
   #716 lands, DESIGN §19.8) — and group **C** for EVERY genericbot tier (§19.1 forbids a hard-only gate). If `all` loses:
   bisect A vs B vs C in one A/B (arms per group). Record the verdict in `AI_MATCH_LOG.md`.
2. **INC-4 (collect, then ONE A/B):** DAWN #716 (99 direct actor mutations → orders) **after** the Fransbot re-vendor;
   NOVA ZG-c (group D) + IM-1 influence layers; CA F2 part 2 (hand-port CA's Feb-2026 AI routing / harasser squads /
   indirect routes / air targeting-by-armour into our modified squad files — Opus specs, Sonnet codes); the 9 CA files
   that need new upstream types (attachables, PopController, LinkedProducerTarget, SelectionBoxAnnotationRenderableCA).
   **+ CV concave engagement** (maintainer order 2026-10-01, `AI_ARCHITECTURE.md` §12.7a, switch group `AG_assault_fanout`, unified with ATK-1 2026-10-02):
   Rush squads deploy into a range-matched concave that widens with army size, then a staggered commit so every
   member reaches its range together. Branch `claude/cv_concave` (Sonnet-coded, Opus-reviewed); supersedes
   EMBER's `devin/ember/mi-concave` (fixed-angle ring, no form/commit phase — not merged).
3. **Round-trip test of the whole AI** (maintainer order): fit priors from the INC A/B logs
   (`fit_arsenal_priors.py … --write mods/cameo/ai/learned/arsenal_priors.yaml`), run matches with `UseLearnedPriors`,
   then `round_trip_check.py` over them — all 10 layers PASS or a named fix.
4. **Upstreams (WORKFLOW §6 — each ENGINE once):** OpenRA bleed (engine pipeline, LESSONS_LEARNED), CA, CN, Fransbot
   always current; the rv-engine family (RV, SP, GA) checked once through its engine plus each mod assembly. 10-01:
   RV 0, SP 0, CN 0 new; CA 24 (campaign + small gameplay); Fransbot 25 (V1.29.19 → V1.29.48); GA 53 (Generals SFX,
   AI fixes); bleed: measure from `cameo-engine`. Harvest, then MERGE duplicates (DESIGN §22, `type_merge_inventory.py`).
5. **Then:** RV2 (support-power merge + 28 IgnoreVisibility decisions), LC9 (ResourceMap fog), the reactors under EMP
   (they keep power — maintainer to rule), the 15 pre-existing red pytest tests (`test_accepted_*_balance_batch.py`,
   `test_armament_roles.py`).

### Who does what
| agent | long-term lane | now |
|---|---|---|
| **Claude (Opus)** — coordinator | integration, review, merges, the ONE A/B per increment, specs for Sonnet sub-agents, maintainer questions | step 1, then INC-4 integration + its A/B, round-trip test, CA F2 part 2 spec |
| **NOVA** (Devin) | map intelligence: ZG → IM → UT (zone graph, influence maps, unit tactics) | IM-1 on a branch; no merges |
| **DAWN** (Devin) | Fransbot: re-vendor, orders-only conversion, harvest into genericbot with claims (§19.6) | re-vendor V1.29.48 FIRST, then rebase #716 onto it; `audit_bot_direct_mutation` ratchet |
| **EMBER** (Devin) | test tooling + observability: ab_increment, ab_summary, canaries, mission stories | keep the tools mirror-only, cap-aware; the round-trip checker's evidence |
| **Sonnet sub-agents** | coding packages specced by Claude | CA F2 part 2, any large self-contained item |

### Long-term goals (unchanged, restated)
* **The Frankenstein bot** (`hard`/genericbot) beats the omniscient `classic` while fog-honest, on every difficulty tier
  scaled on one straight line (§19.1), with one module per decision (§19.3) and one owner per unit (§19.6).
* **One implementation per mechanic** engine-wide (§22): harvest every upstream, then merge the duplicates.
* **Dynamic faction loading** via self-contained ContentPacks (`MIGRATION.md`) — the 12 GB RAM problem.
* **The balance program** (BALANCE_PROGRAM_PLAN, W-board) — paused for bots until the full rebalance; no faction-balance batches.

## 2026-09-30 (evening) — Claude: wave 1b landed, bots build engineers again, one mission-card contract; the next steps

`Agent: Claude-Local (Opus 5.5) · coordinator · master 40b30e000 · fleet orders ../Cameo-mod-fleet/ORDERS_2026-09-30_claude_standing_orders.md (UPDATE blocks) + RULING_2026-09-30_claude_mission_cards_one_contract.md`

**Maintainer rulings today (binding).** (1) *No faction-balance batches until the full rebalance* — DAWN's classic-vs-classic
GDI/Nod probe was stopped after 6 of 12 matches (GDI mirror: one side won all 4; GDI vs Nod: Nod 2–0, once from each
side — n too small). (2) *"The engineer module can be omniscient as a whole"* (DESIGN §19.5). (3) *"You're the only one
who is allowed to merge"* — Claude merges; #662, #663 and #678 had been self-merged by agents. (4) Merge the stack now
(#682), A/Bs continue as post-merge checks.

**Landed (#682 + #684).** RV1 one repair owner · LC1 unit leases · LC2 crate reservations · LC3 unreachable MCV fields
parked · LC4 first-tick `BotLimits` re-check · **ENG** `EngineerBotModule` (one owner of engineers) · **#680 engineers built
again** — no LOADED AI file had listed TD `e6`, RA1 or TS engineers since ≥ 2025-06 (TD's rows lived in the never-loaded
`ai_airforce.yaml`); a smoke match now builds 22 (hard) / 12 (classic) and captures oil derricks · #676 mission-card plan
· #684 `audit_fransbot_drift` re-baselined (blocking, red since `ff7da50a4` on 09-29). **classic moved** (#664, #680).

**Measured in play.** First live LC1 refusals (`ScoutBotModule` denied a Humvee `CratePickupBotModule` held) — the
contract works beyond unit tests. #664's post-merge A/B (hard vs classic, 8/arm, frozen trees): old master hard 6–2,
#664 hard 5–1 after 6 — not losing. ⚠ **Spawn lean:** `bot_outcomes[].spawn` is the SLOT; by `player.home` the (90,24)
side of A Nuclear Winter won 65 of 107 decided matches (LESSONS_LEARNED) — split every verdict by home.

**Mission cards (MC1, #683 draft).** Three agents built three dialects in an afternoon; the coordinator ruled ONE contract
(AI_MISSION_CARDS §2): string MissionIds, fransotto's six states + FAILED + RELEASED, one writer `BotMissionLog` (CA) →
`debug.log` + `cameo-ai-missions.jsonl` (record-only, DESIGN §21.1). First live match: 18 capture attempts, **all
terminal**, 6 SUCCESS / 11 FAILED / 1 RELEASED — one derrick ate five engineers, so #683 adds one engineer per target and
a dormant shelf (2 losses → rest 3000 ticks). ⚠ **Capture success is 33%**: routing or escorting engineers is the next
lever.

**Audit state on master (full `run_all.sh`, complete tree).** Release-critical green: `find_empty_warhead` 0,
`duplicate_inherits`, `balance_drift`, boot. `verify_generator_sync` drift 41 (the known R12 shims, unchanged). **Eight
quality gates red since at least `1ee562ec4` (09-29) — none caused today:** `ammo_cadence`, `armor_upgrade_harm` (8
plating rows), `duplicate_keys` (**D1 = 7: one node inheriting two different templates under one label, the later
silently wins** — e.g. `RA2MultiHoverMissile_AA` takes `^Warhead_MissileHE_Light_Flat` over `…MissileAA…`; `TanyaBomb`,
`RA2DepthCharge`, `SteelKatyCannons_EMP`, Volkov's tesla), `effect_pairings` (silent 418 > 396), `meter_dilution`,
`nuclear_flash_bindings`, `release_drift` (inflated 137 > 133), `weapon_shape`. These are weapon/content lanes and rule 4
(warheads) applies: they wait for the rebalance wave or an explicit order.

### The next steps (priority order; each agent's queue is in the fleet orders)
1. **Claude:** land MC1 (#683) → **LC8** (the master AI's dormant shelf consumes `IBotMissionOutcomeSink`: a raid that
   fails twice rests until recon changes) → BEV (#685, verify in the queued Japan match) → **LC5** watchdog (one owner per
   actor + every attempt terminal) → RV2 (support-power merge + the 28 `IgnoreVisibility` strikes) → LC9 → F2 CA sync.
2. **NOVA:** #681 onto the writer (string ids, RELEASED vs FAILED) → squads claim through LC1 → ZG (chokepoints).
3. **EMBER:** MC2 `mission_story.py` → #671 (LC7 fingerprint) + #674 (home split) merge-ready → one post-merge A/B of the
   whole stack (`9d419e12e` vs `1dbbfe136`) → LC6 canaries.
4. **DAWN:** #679 onto the writer + drift baseline → #672 (one `BotDifficultyLadder`, DESIGN §22) → W3 verdict → F1 → CA-6.
5. **Waiting on the maintainer:** permission for the 7 `duplicate_keys` weapon labels (rule 4); whether capture should
   get an escort (engineer + a guard squad as one mission) before or after LC8.

## 2026-09-30 — Claude: merge-all completed — the last PRs land on engine `d5d8b2a685`; all branches in sync

`Agent: Claude-Local (Opus 5.5) · integration branch claude/integration_0930b (the #630 precedent) · maintainer: "Merge everything to master! Synchronize all branches … the latest engine update"`

**How it landed.** The fleet worked the same order in parallel: #644 #646 #648 (+EMBER's gunship fix)
#649 #650 #632 #634 #655 (engine pin) #656 #657 #659 were merged directly. This integration brings the rest:
#633 (guerrilla role applied; contains #638 and #641), #647 (scout rationing + garrison pricing), #651–#654
(expansion planner EX-0…EX-3) and #658 (NOVA: Steamroller/Rush lead telemetry). **The maintainer's order
overrides the §12.10 A/B gate** for #633, #647 and #652–#654: the first A/B on this master is the new baseline.

**Conflicts, resolved by origin:** `ai.yaml` `BotRoleSets` unions all ten roles, with
`Apply: harvester, refinery, conyard, guerrilla`; artillery, firesupport and the air roles stay report-only.
`MasterAiBotModule` keeps both #656's `WeakIncludesDefence` and #647's `GarrisonOccupantValue`. #646 had been
**squashed** on master, so the stacked branches still carried its pre-correction text; master's corrected
text was kept, plus each PR's own later edits. HANDOFF, LESSONS_LEARNED and TASK_INDEX were unioned; every
addition from both sides was verified present.

**Fixed while integrating (each was red on its own PR or on master):**
- `MasterAiBotModuleTest` expects #658's new enemy key `army_value_delta`.
- The armoured-car non-damage digests are re-pinned after a reviewed resolve diff for #650 (+124–141 derived
  Versus rows per weapon, 0 removed or changed).
- §10.2 / `doc_claims` module counts 53 types / 76 instances; master was already red (51/69 documented,
  52/75 measured after #656).
- `AI_MODULE_MAP.md` regenerated. It also records that **#656 enabled the Fransbot modules for
  `genericbot && hardbot`**: a behaviour change for `hard`, merged without an A/B (DAWN's lane).

**Engine:** master pins `d5d8b2a685` (#655 and #654 agree). `origin/cameo-engine` has been fast-forwarded to
it (104 commits), so the canonical engine branch and the pin agree again. **Every worktree: `make.cmd all`.**

**Verified on the integrated tree:** C# 338/338; 17 audits + `find_empty_warhead` 0 + module map current;
boot gate (isolated support dir, no exception log); Python compared with master (below); live smoke match.

**Not merged (NOVA's 2026-09-28 reasons still hold):** #180, #245, #85. **Open:** #634's review points (unarmed
WC2 oil tankers can be drafted into squads; escort stacking) with NOVA; the MCV escort hook proposal
(NOVA); the Python suite hangs at exit on master (pre-existing); ~200 Python tests already fail on master.

## 2026-09-29 — Claude: what the maintainer saw in play, measured; the expansion planner EX-0…EX-3; the engine-pin trap

`Agent: Claude-Local (Opus 5.5) · lane: AI, by the maintainer's "split by owner" ruling (scout/garrison + expansion planner); balance continues on #650 · branches below`

**Spectator report → measured causes** (AI_ARCHITECTURE §12.11; `hard` per match): ~72 Humvees and ~5 tanks
(scout replacements jump the vehicle queue), infantry fed into civilian garrisons (valued 0, no `Valued`),
no artillery-first or tanks-in-front (CA-2 DAWN, CA-4 NOVA, unbuilt), a timid base (random/omniscient
`BaseCrawl`). **Rulings** in DESIGN §19.1b (expansion, garrisons, scouts; map-start resources are public)
and §19.1c (each personality chases one lead over the enemy). `tools/ai/army_mix_report.py` flags spam
from any batch.

**Landed as PRs (stacked, each boot-gated in an isolated support dir):**

| PR | what | state |
|---|---|---|
| #646 | design §12.11–§12.14 + army-mix report | ready |
| #647 | SG: scout rebuild cooldown; garrisons priced by capacity × 250 | draft, A/B running (`sg_branch`/`sg_master`) |
| #651 | EX-0: field score `V × S / (T + τ)`, telemetry | ready |
| #652 | EX-1: `BaseCrawl` walks toward the target field (CA hook `IBotExpansionTargetProvider`) | draft, A/B pending |
| #653 | EX-2: a refinery on every field in reach; missed claims park the field | draft, A/B pending |
| (this) | EX-3: the MCV founds its base at the best far field (engine hook) | draft, A/B pending |

Live, `hard` on A Nuclear Winter: target field 16,36 → refinery at 10,35 claims it (tick 1,380) →
target 45,32 → a line of power plants toward it (17,44 → 19,45 → 23,40).

**⛔ Engine pin trap (LESSONS_LEARNED 2026-09-29):** master's pin `042b2fa787` is **not on
`origin/cameo-engine`** (103 commits ahead; only on `devin/1790592696-no-audio-switch`). The EX-3 hook
`d5d8b2a685` is on `claude/mcv_expansion_site`, on top of the pin. **Done 2026-09-30:**
`origin/cameo-engine` fast-forwarded to `d5d8b2a685` (maintainer order), which is master's pin. Every
worktree needs `make.cmd all` after the integration merge.

**Reviews today:** #644 (NOVA) approve, after my `norecord` point landed; #648 (EMBER) changes requested:
75 dual-weapon helicopters (Orca, Apache, Hind…) are classed `fighter`; §12.4 makes them gunships.
**Open for NOVA:** the escort hook (fleet `PROPOSAL_2026-09-29_claude_to_nova_escort_hook.md`).
**Next (Claude):** A/B results for SG / EX-1..3; EX-4 (enemy creep × difficulty × aggression); towers per
field; personality leads telemetry (§12.14: Expansion, Turtle, Tech).

## 2026-09-29 — Claude: §12.0l step 1 done (derived rows in every table) + the submarine types

`Agent: Claude-Local (Opus 5.5) · lane: balance pipeline (maintainer 2026-09-29: "you continue with the balance pipeline while the other agents focus on the AI") · branch claude/submarine_armor_types`

**Landed on this branch (additive, no hit changes in play):**
* **Rule 3b's submarine types** `SubmarineLight = ShipMedium x Heavy`, `SubmarineHeavy = ShipHeavy x
  Superheavy` are in all four copies of the derived list (generator, `HeavinessBell.cs`,
  `effective_heaviness.py`, `audit_versus_profile`); `test_derived_armor_types` now pins the fourth
  copy too (it claimed to and did not). `splice_templates.py --all`: +754 rows, nothing else moved.
* **§12.0l step 1 is complete:** `derive_versus_columns.py --write` wrote the 35,123 pending rows into
  all 42 weapon files. A difflib check proved every change an inserted derived row (0 other hunks).
  `audit_derived_armor_columns` 29,592 → **0**, ratchet 0. No actor wears a derived type yet
  (re-measured), so no hit changes until step 3.
* **Next in §12.0l:** step 2, the `<Family>Air` variants (§12.0k item 2, rule 3a). Then step 3, moving
  actors onto the types; its per-unit membership lists are maintainer-reviewed.

**Also today:** #645 (merged) re-greened master's derived-columns guard (Scrin's 40 rows). The test
subset this branch touches (13 files) has **56 failures already on master** (for example
`test_aa_weapon_routing`, which expects `*_FlatCompatibility` warhead keys); this branch adds none
after regenerating the CannonAP fixture. `verify_generator_sync` reports 41 hand-made `^Warhead_*_Flat` /
`_WallExcluded` / … templates the generator does not emit. It's not a value drift, but it is the A5 backlog.

## 2026-09-29 — Claude: guerrilla role applied (A/B pending); ai.yaml generalisation ruled; lane handover

`Agent: Claude-Local (Opus 5.5) · lanes: AI list rollout + the DF code review (took over from the ended session) · branch claude/role_guerrilla_apply`

* **Guerrilla applied** to the six personalities through `Targets` of the new `TraitType@instance.Field`
  form; `@classic` (A/B reference) keeps its list. Central ids **5,825 → 4,289**, now guarded by
  `audit_central_ids.py` (lower-only `CEILING`). Draft PR: lands only after its Nuclear Winter A/B.
* **Ruled (AI_ARCHITECTURE §2.8b):** per-building numbers become defaults per building type, with the
  differing pack rows kept as overrides; `UnitsToBuild` weights derive from stats after CA-3. Measured:
  intervals 100 % uniform for factory/refinery/barracks, limits 100 % for refinery/radar/repair.
* **Bug found:** `@guerrilla` has no `AirSquadTargetTypes` rows (packs write 5 identical copies);
  deriving it from the aircraft's weapons fixes it — queued.
* **Reviewed #632 (NOVA):** changes requested — `DESIGN.md` §19.1a still names the deleted
  `DefenceReleaseQuietTicks`, and the fogged-target quiet rule needs its A/B numbers.

## 2026-09-29 — Claude: guerrilla band on the actors; squad rulings for artillery, fire support and ships

`Agent: Claude-Local (Opus 5.5) · lane: AI list rollout (§2.8) · branch claude/role_guerrilla`

**Maintainer rulings today** (AI_ARCHITECTURE §2.8a, §12.4a):
* **Guerrilla bands:** the fastest third of the faction's infantry or vehicles, costing at most the median.
* **Artillery squads** are `^ArtilleryTemplate` + `^ArtilleryTankTemplate` units only. **Fire-support
  units** (`^FireSupportTemplate`) form their own squads with tanks and protect the artillery.
* **Ships** are their own squads, never mixed into ground or air squads.

**Landed on this branch (inert, no behaviour change):** `tools/ai/derive_guerrilla_roles.py` writes
`BotRoles: Roles: guerrilla` on 154 actors in 37 factions (65 rules files, 10 `-BotRoles:` on child
actors that would have inherited the tag); `audit_guerrilla_roles.py` in `run_all.sh`; the three
templates declare `artillery` / `firesupport`. Boot-gated (isolated support dir, 0 exceptions).

**Found:** the §2.8 metric went **up** 4,092 → 5,825 (#588 interim, `@classic`, `@guerrilla`: every
personality copies ~600 list ids); no gate watched it. And 19 ships are in ground squads today
(#627's `navalunit` misses; `FindNewUnits` checks `GuerrillaTypes` before `NavalUnitsTypes`).

**Next (Claude, after cameo-mod-45's integration merge):** apply `guerrilla` (−1,776 ids) behind a
Nuclear Winter A/B, add the `--max` ratchet, review and apply `navalunit`. **For NOVA (CA-3/CA-4):**
§12.4a in `SquadManagerBotModuleCA` — the `artillery` role instead of `ArtilleryMinRangeCells`, the
escorted fire-support squad, the ship guard.

## 2026-09-29 — Claude: the Frankenstein doctrine integrated on master (maintainer: "merge everything together")

One integration merge (`claude/integration_0929`) brings the 2026-09-28 rulings together; every
piece is behind a yaml switch that only the six `genericbot` personalities turn on, so `classic`
(the A/B reference) is untouched. What the bot does now, in order of a match:

1. **Sees:** fog memory (6a) + scouts that also check the enemy's possible spawns
   (`EnemySpawnBonus`) — it remembered only 1–18 % of classic's army before (AI_DEEP_RESEARCH §2.3).
2. **Tracks and predicts:** visible enemy groups are tracked and extrapolated to the own asset they
   head for, with an ETA (`BotThreatTracker`, situation `own.threats`).
3. **Fights smart:** every ground squad engages or turns back with the Lanchester combat predictor
   over what it sees; `BotLimits.RetreatRatioPct` 0.1 (Easiest) … 1.0 (CameoGod) — never suicide.
4. **Stays active:** guerrillas always on, several small squads, their count growing with game time
   per personality (steamroller 1→3 … guerrilla 2→6); the main army follows the personality.
5. **Defends ahead:** a predicted attack is met at the own defence nearest its target; defenders hold
   and lure the enemy under the towers; fast squads that can arrive in time join, the others punish
   the enemy base; defenders go back to their jobs only when there is no perceived and no predicted
   threat (DESIGN §19.1a).
6. **No APM cap** (DESIGN §19.1): the cap measured 0–4; `HumanPaceBotModule` limits are 0.
7. **Learns:** the arsenal ledger (per-type created/lost/destroyed, both sides) feeds
   `tools/ai/fit_arsenal_priors.py` (per-enemy-faction trade profiles, visibility, Elo);
   `tools/ai/fight_report.py` explains each decisive fight.

Also merged: #626 (air strikes route around remembered AA — its A/B is still EMBER's to report),
#627 (roles report-only), and the #625 fix (league exploiters get Hard's bot insurance).
**Not merged (by ruling or evidence):** the per-tier APM line and order lanes, `ReinforceProtection`
(superseded by the DF release path), the continuous-threat branch (lost 1–3).
**Open:** the integrated doctrine has not yet had its full A/B on A Nuclear Winter — the first run
after this merge is the new baseline; NOVA's protection dissolve must reuse `ReleaseDefenders`
(one release trigger); roles still report-only; central ai.yaml ids 5,825 (the roles are the way down).

## 2026-09-28 - EMBER: CA-5 air-threat routing landed (first slice of §12.8)

The part of CA-5 air doctrine that needs no CA-1 roles:

- The 6e router's threat read now splits by the leader's domain in
  `MasterAiBotModule.RouteAroundThreat`: airborne leaders (aircraft)
  pay remembered `AntiAirValue` per entered region; ground leaders pay
  `ArmyValue+DefenceValue` as before. `RegionMemory` already books AA
  guns and air-to-air fighters into `AntiAirValue` - the air-threat
  layer existed as data and is now consulted. The 6c ground gate is
  unchanged.
- `AirAttackStateCA` routes a fresh target through
  `SquadManager.RouteAroundThreat`: chained `Fly` waypoints then a
  queued `Attack`. Per-state `routedCurrentTarget` covers state entry
  where `newTarget` never fires; `Fly` is excluded from the per-tick
  re-issue so transit is not cancelled.
- Still open for CA-5: the doctrine split - gunship CAS attach,
  fighter pick-off of isolated units, bomber strike-team target
  priorities - waits on CA-1 roles (§12.10) plus this slice's
  A/B vs master.
- A/B so far (same binary, pooled): hard 4-3 vs classic — parity with
  the 7-6 baseline band; dedicated 1-3 sample being extended before
  the gate is called. Losses were ground/emergency-decided (turtle
  held under sustained pressure ~85% of ticks); air usage was small.
- First `league_standard.json` league run in flight (4 cells x 4
  swapped matches; classic cell already produced 2-0 for hard).
  Spec map-path bug found+fixed in #628 before launch.
## 2026-09-28 — Claude: combined-arms order (AI_ARCHITECTURE §12); Frankenstein vs classic is a coin flip (7–6)

**Maintainer order:** an arsenal tracker (every unit and defence built, where they usually are,
self-learning), every role used in the right ratio, squads of the right composition moving in
formation, scouts choosing where to attack, air strike teams on least-resistance routes, and —
most importantly — **no suicide runs**: stop outside defence range, artillery first, commit only
when the area's defences are gone or the force clearly wins. Written up as
**`docs/design/AI_ARCHITECTURE.md` §12**: §12.1 lists what already ships (fog memory, 6c risk
gate, 6e ground risk routing, 6f artillery/support/staging, 6g tags, scouts, counters — do not
rebuild them); §12.2 the five real gaps; §12.10 the phases **CA-1 tracker (Claude) · CA-1b
offline fitter (Claude — Devin Cloud is out of tokens until next week) · CA-2 siege (DAWN) · CA-3 role mix + CA-4 formation (NOVA) ·
CA-5 air doctrine (EMBER) · CA-6 scouting → targets (DAWN)**. Every phase is A/B-tested on A
Nuclear Winter against the current master before it lands. Queue: ROADMAP "AI ARCHITECTURE".

**A/B state (verified, td_gdi mirror):** master's Frankenstein `hard` vs omniscient `classic`
= **7–6 over 13 matches** (rounds 2–4; round 4 alone went 1–3) — a coin flip, not a lead. Every match is decided by one or two big fights around ticks
12000–16500 that one side trades ~2:1; income follows the trades, it does not cause them
(`stats.stats_timeline`, PR #617). The continuous-threat branch lost 1–3 and is shelved.
Round 4's loss-by-role log (#617): the largest loss category is **idle units at home**
(38–108k per match, 70–81 % of them inside the base) — `ProtectOwn` drafts the idle pool only
while the protection squad is empty, and the squad never disbands. **Round 5 (fix vs master, 4+4):
fix 1–3, master 2–2** — idle losses fell, protection losses rose by the same amount, inside the
base: the defence now fights but is out-armied (43–96k vs 3–10k, `tools/ai/fight_report.py`).
Shelved until CP (AI_DEEP_RESEARCH §13.1).

**Merged today:** #613 (classic/fransbot hidden in the lobby), #614, #616, #618, #619.

## 2026-09-28 — EMBER: post-#611 hard beats classic; donor-stack wiring gaps closed

**nw-ab-7 match 1 (post-#611, hard vs classic, A Nuclear Winter): `hard` WON**
— lost the unit trade 181:279 but destroyed 47 buildings vs 3, finishing at
army$ 103,020 vs classic's 0. First measured win of the fog-honest candidate
stack over the omniscient reference; the IsEligible fix turned "no enemy" into
actual missions and pressure. Matches 2-4 running.

**nw-ab-6 (fransbot vs classic): 0-2** — donor stack still loses cleanly to the
reference (0:16 / 0:18 buildings). Expected: `ModularBot@Fransbot` is a donor,
not the candidate (its header comment: modules join the Frankenstein stack one
at a time, type deleted after). AI_MATCH_LOG.md's Side-A text was corrected.

**Merged to master:** #610 template-dir restore · #612 in-harness A/B
scoreboard (`ab_scoreboard`, spawn axis, batch_summary.json) · #614 StrategicMap
probes (passability layers live) · #615 support-power Decisions port (fransbot
had `Decisions: []` — all 210 orders now configured). #616 open: §9.12 records
the fog-honest-offense decision (spawn-directed recon / bounded remembered-
building raids / new assault verb; leaning a+b) — DAWN's call, they own the
recon loop.

**Coordination notes:**
- DAWN: `stash@{0}` in the shared repo (`devin/dawn/batch-startingunits-regex`,
  "fransbot-strengthening wip") holds a large WIP — AdaptiveCounterProduction.cs,
  BotLimits, queue-manager + commander changes. I accidentally popped it onto a
  clean tree while stashing docs; reset cleanly, stash is intact. Pop it back
  in YOUR worktree when convenient.
- `PowerDownBotModule.PowerDownTypes` is unset on the genericbot stack — bots
  never toggle power-hungry buildings during brownouts (stock RA/TS configure
  it; `^DisableOnPowerDown` exists across packs). Generator emit suggested.
- Something raced file writes in `ember-bleed` twice today (edits reverted
  mid-sequence). If another agent is running git/file tooling here, coordinate
  — I now verify writes read-back before relying on them.

## 2026-09-28 — EMBER: personality-layer diagnosis + fixes; fog-honesty ratchet; spawn attribution

Post-#611 re-baseline reads: `hard` went 2-0 vs `classic` in nw-ab-7 (33248t and
42623t, hard won both by objective — buildings 47:3 and equivalents; nw-ab-8 then closed 3-1
for hard with wins from both physical spawns). But the situation log
showed a personality-layer defect worth the fleet's attention:

- **Emergency flapping latched personalities.** `CheckEmergency` used a single
  600-loss threshold; the loss window bounced across it every 25-tick check,
  each flicker flipped the candidate to `turtle` and back and reset the
  sustained-candidate timer — `cur` held `turtle` ~38k ticks while `cand`
  stayed `rush` for stretches. Fix in flight: `EmergencyLossClearThreshold`
  (off-threshold = half the on-threshold) + a terminal posture yield in
  `PersonalityCandidates` so a thin fogged profile can never leave the set
  empty.
- **`guerrilla` was unreachable.** `PersonalityCandidates` already yielded it
  (`target.ExpansionClusters >= 3` = the §4.4 "aggressive expansion" row) but
  `BotPersonalityController.Conditions` never listed `personality-guerrilla`.
  Wired end to end: sixth personality, `SquadManagerBotModuleCA@guerrilla`
  (clone-of-@rush shared lists; tuned for small fast harassment squads —
  `JoinGuerrilla 100`, `IndirectRouteChance 60`, `StageBeforeAssault false`,
  `PreferMainTarget false`), observer notification, fluent line.
  `audit_ai_personalities` extended: `PERSONALITIES` gained guerrilla and
  `TUNING_FIELDS` allow-lists the four identity fields it legitimately breaks.
  `audit_fog_honesty.py` (#618) is the missing §0a check — a per-file ratchet
  on `World.Actors`/`ActorsHavingTrait`/etc. in bot modules; 55 files/169 sites
  baselined, new sites fail review. `bot_outcomes[].spawn` was always 0
  (`Player.SpawnPoint` is lobby-only); #619 derives it from the slot binding.

Coordination: Claude's #617 adds `player.home` (record-layer ground truth) —
composes with #619, recommend both land; noted on the PR. The guerrilla block
was cloned from `@rush` with only TUNING_FIELDS deviations per the audit's
invariant — if a future personality needs a shared-list difference, extend
`TUNING_FIELDS` deliberately rather than hand-diverging.

**LG landed (same lane).** `tools/ai/run_league.py` + `tools/ai/league_standard.json`
implement the AI_DEEP_RESEARCH §6.2 league: candidate x members x maps x
factions, one `run_ai_match_batch` cell each, pooled into a Wilson-interval
league score in `league_summary.json`. League members are hidden bot TYPES —
`exploit_rush`/`exploit_turtle`/`exploit_guerrilla` are the full genericbot
stack at hard tier pinned to one personality pole via the new
`BotPersonalityController.PinnedPersonalities` (fog-honest; no RevealsMap).
A "past master" freezes the same way `classic` did — a yaml-frozen stack,
not an old binary, so it replays against any build. @NOVA @DAWN — every CA
phase's landing gate is "does not lose to master"; once this PR lands the
stronger gate is a non-negative league score over `league_standard.json`.
Smoke match hard vs exploit_rush on A Nuclear Winter (29,249 ticks):
**pin verified** — `personality_switches: 0`, `personality_current: rush`
constant while `personality_candidate` cycled expansion/turtle/tech; hard
(adaptive, steamroller→turtle at t=2107) won.

## 2026-09-28 — EMBER: #611 invalidates pre-existing `hard`-side A/B results; two A/B axes now exist

Claude's #611 (`379d9f5f8`) found `MasterAiBotModule.IsEligible` required
`Playable` — but the harness's duelists are map-side bots (`Playable: False`),
so the `genericbot` master AI profiled **no enemy all match** (0/253 snapshots)
in every Nuclear Winter A/B to date. `MasterAiBotModule` is `genericbot`-gated,
so this contaminates only `hard`-side matches; the fransbot-vs-classic axis
(fransbot stack does not consume MasterAi) and the fransbot-side raid/intel
diagnosis below are unaffected. `hard` still won its blind matches — its squad
machinery carries combat without master-AI missions, which is itself worth
knowing when re-baselining.

Two A/B axes are now in play, both mandated-adjacent:
- `fransbot` vs `classic` — the maintainer's literal pairing; EMBER's running
  series (nw-ab-6) is post-ResourceMap and valid.
- `hard` vs `classic` — Claude's #611 standard (`ab_summary.py`, Wilson CIs);
  needs a post-#611 re-baseline on rebuilt binaries before numbers are trusted.

Tooling overlap flag: `tools/ai/ab_summary.py` (Claude, post-hoc Wilson over
jsonl) and the new in-harness `ab_scoreboard` (#612, end-of-batch table +
`batch_summary.json`, adds the spawn axis) cover adjacent ground — kept both,
cross-referenced; consolidate if they drift.

## 2026-09-28 — EMBER: maintainer mandate — bot tests on "A Nuclear Winter", fransbot vs classic A/B

**Mandate:** all bot tests on the tournament map A Nuclear Winter, both spawns,
`gamespeed=insane`. A/B = `fransbot` (fog-honest Cameo×RV×CA×CN×Fransbot stack)
vs the classic bot (the `classic` type — omniscient via `RevealsMap@classic`;
this baseline ran `hard`, which predates the reveal). Deliverable: the new
stack wins on smarts, not cheats.

**Harness:** `run_ai_match_batch.py` gained a real-ormap variant path + spawn-swap
(`--map` + `--swap-bots`) — PR #163 on `devin/ember/nw-batch-harness`.

**Baseline (A Nuclear Winter, td_gdi mirror, both spawns):** fransbot **0-3**,
zero enemy buildings killed in any match, out-traded ~5:1 by cost
(22k kills / 110k deaths typical). Fixture works; the bot needs real fixes.

**Fransbot gaps found (inert modules — the likely loss drivers):**
1. `FransMcvExpansionManagerBotModule` Requires `ResourceMapBotModuleInfo` — the
   Info is present via ai.yaml but its sole instance is gated `genericbot`, so
   `TraitsImplementing().FirstOrDefault(IsTraitEnabled)` returns the disabled
   module and all resource indexing is inert. Fix in flight: a named
   `ResourceMapBotModule@fransbot` instance gated `enable-fransbot` — all
   consumers resolve `FirstOrDefault(IsTraitEnabled)` so multi-instance is safe.
   Lists go through `gen_fransbot_lists.py` (@DAWN — touching your generator,
   flagging here).
2. `IBotSuggestRefineryProduction.RequestLocation` is a dead seam for fransbot:
   `FransBaseBuilderBotModule` implements it but no fransbot module produces
   suggestions (only common `McvExpansionManagerBotModule` does).
3. `FransStrategicMapBotModule` probe types (Ground/Mcv/Naval) unconfigured —
   passability layer inert by design.
4. FIXED in #162: `TraitInfoOrDefault<AttackBaseInfo>` crash on multi-AttackBase
   actors (same class as #554 attackbuggy).


**Post-fix A/B (ResourceMap live):** machinery works — MCV expansion commits,
`MovingToOre`/`BuildingRefinery` stages cycle, expansion retry after raid
threats — but fransbot still lost both completions (0-6 overall). Kill chain
diagnosis: every published RAID sees `bids 0`; interference-driven raid targets
are mobile attackers that leave fog before execution (`target is no longer
visible/eligible`), and raids on buildings require 9 fresh intel samples inside
the enemy perimeter — recon never survives deep enough. `FransMissionType` has
no assault/push verb: Raid is the only offense and it cannot mass on bases.
@DAWN — the bid funnel (`TryBuildGroundRaidBid` ->
`IsGroundRaidEligibleTarget` -> fresh-visibility gate) is the blocker to the
maintainer's win condition; probe actor types also still null (passability
layer inert by design).

## 2026-09-28 — NOVA: stale external-PR sweep — #344/#119/#252 merged, #180/#245/#85 flagged

The six stale external drafts were triaged under the maintainer's merge-all
order. **Merged:** #344 (coordination pilot — kept only `AGENTS.md`,
`.github/agents/openra-cameo.agent.md`, and provenance disclaimers; master's
evolved docs won every modified file), #119 (HD remastered terrain — its
`CameoRemasterFileSystem` loader got `ContentInstallerFileSystemLoader`
semantics replicated so the content-installer path is preserved, plus the
June-era `float2/3` → `Vector2/3` API port; remaster path is inert when the
setting is off), #252 (Scrin faction — 519-file ContentPack, master's engine
pin kept, Scrin flag cell spliced into master's 1x/2x/3x flag sheets and
upscaled for 4x). **Flagged, not merged** (review comments on each): #180
needs an engine PR that doesn't exist in the pin and halves `TileSize`;
#245's economy rewrite conflicts semantically with the post-wave composition
system — needs a port, not a textual merge; #85 vendors ~2174 `engine/` files
into a repo where `engine/` is `.gitignore`d — its Vulkan backend belongs in
the cameo-mod/OpenRA fork. ⚠ `git merge --abort` on #85 deleted the ignored
`engine/` sources (the merge had force-added them); recover with `make all`.

## 2026-09-28 — EMBER: squad-level attention landed on `devin/ember/ai-squad-attention`

`IBotActionBudget` now has its second consumer: squad `Update()` consults
`TryConsumeAttention(squad)` per `AttackForceInterval` round, with a rotating
cursor so the slot cap staggers rather than starves. Producer Desc and the
interface doc updated to name both consumers (order drain + squad updates).
Gates green; PR up.
## 2026-09-28 — NOVA: AI phase 7a follow-up — missions on devin/1790537249.8881-ai-missions-7a-followup

`Agent: NOVA · lane: AI architecture / assign layer · branch devin/1790537249.8881-ai-missions-7a-followup · based on current origin/master after #581`

Phase 7a landed through #581, and #592 supplied the first exhausted-Defend
consumer fix. This follow-up fixes the remaining multi-Defend starvation so a
later affordable Raid can still be consumed, limits Defend threat
from neighbouring static defences to the own base region, and documents the
existing omniscient fallback when fogged scans are disabled. It also adds a
permanent fog-enabled Raid runtime gate with reachable refinery and harvester
actors. The gate asserts Raid publication and target-bearing squad assignment;
the frozen-target branch remains documented but is not asserted unless a fixture
can reproduce it reliably. Phase 7b mission bidding is next.

Runtime gates cannot run on this host since the .NET 10 / bleed engine update:
`alcOpenDevice` faults with an access violation (0xC0000005) before game start,
which also reproduces on unmodified master, so the squad, bot-player and raid
gates and `boot-test.cmd` are all blocked until the audio init is fixed.

## 2026-09-28 — OMP Astra: deployment review and scout follow-up

Blackrobe authorized scoped publication and integration, including the engine
rollout only after the maintainer's held map-generator click-test. No public
release is authorized.

* Independently reviewed and merged #584, #583 and #587. The #587 parent-squash
  conflicts were resolved with a normal merge, no history rewrite; its full
  tree matched the separately tested tree (`9013ffa431011461d08f47f00d290c8aefd4f01d`).
  That batch passed 267 C# tests, the live harvester/squad gates, AI guards,
  documentation checks and a fresh menu boot with no new exception log.
* The additional scout fix handles the earlier no-stale-region return, preserves
  an existing idle-pool wrapper for the same actor, and keeps ownership if the
  pool is unavailable. It shares the return path with #584's no-target case.
  The lifecycle regression failed before the fix; the integrated C# suite
  passes 271 tests.
  The final live squad scenario recorded 9 snapshots through tick 1201 with
  2 squads / 7 units and exit 0. The final menu boot was also clean; neither
  scenario is presented as a long-match scout-release test.
* The classic-four regression callers now use the existing Allied actor names.
  Tests no longer pin a bare inheritance shape, whole-weapon hashes, or an old
  single-armor row; a tautological expected-constant arithmetic test is removed.
  Resolved ranges, flat damage totals, faction identities, cargo and chassis
  behavior remain covered: 29 focused Python tests pass.
* #586 was independently visually checked and merged: a disposable map spawned
  all seven affected actors and exercised actual harvesting. Rendered views
  showed stable stationary body facings and player-coloured harvesting bodies
  without the purple overlay; the 3000-tick run exited cleanly. The temporary
  map was removed. Mongoose and additional attack/walk animation wiring were
  deliberately untouched.
* This is not a full rebalance. Original-unit reference coverage still has
  withheld cases. All 17 warhead sources have assignment decisions, but R69
  still holds cross-source averaging for the review of the proposed sources.
  The reference and AI documents now distinguish completed implementation,
  historical measurements, proposals and human approval.
* Do not describe the Japanese Armored Car as fully runtime-identical to #403:
  #431 folded 1600 bullet damage into the 300 railgun main while retaining
  `PercentageScale: 6667`. Total flat damage is preserved, but the helper's
  folded-percentage units become 63 instead of 10. No weapon value is changed
  by this follow-up.
* #580 has new source-review blockers: visible enemies can be counted again in
  remembered threat, and a responder can be released before its delayed #579
  order executes. #582 has a risk-checked retarget fall-through in addition to
  its existing classification blocker. #588's new Outpost2 actor references
  are uppercase although runtime names are lowercase. Changes-requested
  reviews were posted; do not treat earlier approvals as clearing these.
* #577/#585 retain their posted review blockers; #578 remains draft for the
  role-based list rollout; #569 still requires the human click-test. #187 is
  closed as superseded by #558. Other legacy holds and the dispatcher pause
  remain intact.
## 2026-09-28 — EMBER: fill the faction ids the applied roles don't cover (devin/ember/ai-faction-wiring)

`Agent: EMBER · lane: AI execute/sense + gate tooling · branch devin/ember/ai-faction-wiring`

Follow-on to the inert-factions fix above: `Apply: harvester, refinery, conyard`
(#583/#587) wakes the five factions' economies, but ~60 more gating list fields
(PowerTypes, BarracksTypes, ProductionTypes, McvTypes, defenses, scouts,
engineers, squad/capture/crate/resource-map lists) still carry no
`atreides`/`harkonnen`/`corrino`/`EDEN`/`PLYMOUTH` ids — the bots can count a
refinery yet still can't pick a power plant. This commit appends the missing
ids to exactly the fields no applied role covers (~100 ids, all verified
defined, strict appends), and the pack dictionaries the houses lost in the
rename-era cleanup (`10b8f5915`): `BuildingFractions`/`Intervals`/`Delays`/
`Limits`, `AirSquadTargetTypes` ×5, `spiceharvester` units; Outpost2
bootstrapped.

- New gate `tools/tests/ai_d2k_production_gate.py` + map
  `ai_d2k_production_gate_20260928`: an Atreides HardBot starts with one
  construction yard; lua prints live `AI_D2K_GATE_TICK`/`AI_D2K_GATE_ACTORS`
  counts (the situation-log writer buffers until match end — killed runs
  write nothing). PASS with the lists, FAIL at 2 actors without them.
- Fields whose applied role already supplies the ids (`HarvesterTypes`,
  `RefineryTypes`, `ConstructionYardTypes`, harvester ids in
  `ExcludeFromSquadsTypes`) are NOT re-appended — the drain direction stands;
  the remaining ids compose with `Apply:` (set-union dedupe) and mark the
  fields Claude's next roles should target.
- Verified: gate PASS, negative control FAIL, bot-player + squad gates PASS,
  boot-gate PASS.
## 2026-09-28 — Claude: §12.0l queued for the balance agents; the new AI's acceptance test; a correction to #587

`Agent: Claude-Local (Opus 5.5) · lane: AI list rollout (§2.8) · branch claude/docs_goal_and_12_0l_queue`

**QUEUED (maintainer ruling 2026-09-28): the §12.0l derived-armour rollout, for the balance agents.**
DESIGN §12.0l (anti-air, cyborg and ship armours, 2026-09-26) is ruled and binding but had no queue
entry, and only its first step had started. Measured on master `c5390178d`:

| §12.0l step | state |
|---|---|
| 1. derived columns in every Versus table | **partial**: the generated templates carry them; `audit_derived_armor_columns.py` reports **29,592** missing or wrong rows in faction weapon files (ratchet 29,592). |
| 2. `<Family>Air` variants (§12.0k item 2, rule 3a) | **not started**: 0 templates |
| 3. move actors onto the new types (rules 5, 5a–5c) | **not started**: 0 actors wear any of the 13 derived types |
| 4. re-extract the ledgers | blocked on 3 |

**How:** each weapon-file lane runs `python tools/balance/derive_versus_columns.py --files <its files>
--write` on ITS OWN files (BALANCE_PROGRAM_PLAN §2 boundaries), until the audit reaches 0. §12.0l
forbids step 3 before that. The biggest files: RA Soviets 2,808 rows, Consortium 1,768, Syndicate
1,755, Japan 1,599, Asian Alliance 1,534, RA2 Shared 1,523. Tools and order are in
`TASK_INDEX.md` → "Derived armour types". **Two more types were ruled 2026-09-28:**
`SubmarineLight` (ShipMedium x Heavy) and `SubmarineHeavy` (ShipHeavy x Superheavy), with the
AntiSub-first / Torpedo-second bonus (§12.0l rule 3b). They enter step 1 before any lane starts,
so every table is derived once. The rocket soldiers wear `None` today (#450's interim rule:
only Scout and Special Forces carry Flak); §12.0l moves them to `AntiAirInfantry` at step 3.

**The acceptance test for the new AI is written down:** AI_ARCHITECTURE §0a (maintainer rulings
2026-09-27). The fog-blind new bot must win at least 16 of 20 against today's omniscient bot at the
same difficulty, one match per two-player Tournament map (20 listed there), with the same faction on
both sides first and every match-up after that. It cannot run yet: master has no fog-honesty check
and no 20-map match runner.

**Correction to the entry below:** "Fixed by the refinery + conyard roles" is only half true. An
Atreides bot starting from a bare construction yard still builds nothing (2 actors in 3,000 ticks, on
#588's own gate, master `c5390178d`): the power, barracks and production lists lack the D2k and
Outpost2 ids. #587's A/B started the bot with a finished base and could not see it
(LESSONS_LEARNED 2026-09-28).

**Reviews 2026-09-28:**
* **#588 (EMBER), changes requested.** The diagnosis is right, but its 41 + 76 uppercase
  `EDEN_*`/`PLYMOUTH_*` ids never match (actor ids are lowercased at load): Eden stayed at 2 actors
  as written and reached 22 lowercased. It also needs a row-level rebase onto #587; rebased that way,
  the Atreides gate passes with 16 actors.
* **#589 (OMP), approve after two fixes.** The code fix is correct and closes the early-return scout
  strand that my #584 review missed. The Flak assertion should become `None`, and the ArmoredCar
  hashes should be re-pinned, not deleted.
* **#590 (mine):** tooltip descriptions. 213 showed a literal `\n`, and 115 hand-written Strong/Weak
  texts sat beside the derived lines (115 → 0 on armed actors).

**Next in the list rollout:** roles for power, barracks and production, which take #588's interim
central ids out again. Then the Fransbot fields from DAWN's spec.






## 2026-09-27 — Claude: the AI lane is SPLIT (maintainer ruling); harvester role applied; 5 factions' bots are inert

`Agent: Claude-Local (Opus 5.5) · lane: AI list rollout (§2.8) · branch claude/role_apply_harvester`

**Three maintainer rulings, 2026-09-27 ~20:40–21:10, asked directly.** They refine the entries below:

1. **The AI-architecture lane is split.** **NOVA** owns the *layering*: Sense/Decide/Assign/Execute,
   H1 pacing, Fransbot integration. **Claude** owns the *list rollout*: `BotRoleSets` roles, pack AI
   rows, and the central-id metric (`tools/ai/count_central_ids.py`, lower-only). No self-merge still
   holds, so Claude's role PRs go to NOVA for review and merge.
2. **Fransbot publication is cleared.** #578 may carry the vendored Fransbot source in this public
   repo.
3. **Every commit is authored `AedisToru <122120981+AedisToru@users.noreply.github.com>`.** On
   2026-09-27, 17 commits (10 on master) came from a cloud agent's own git config, carrying another
   name and the maintainer's private e-mail. **Fix forward, no history rewrite:** `.mailmap` maps them
   for git tools (GitHub's web UI ignores it). Every agent checks `git var GIT_AUTHOR_IDENT` before
   committing. Provenance stays in the `Co-Authored-By:` trailer. Details: fleet
   `ORDERS_2026-09-28_git_identity_and_engine_isolation.md`.

**Harvester role applied** (AI_ARCHITECTURE §2.8, "Applied roles"): 50 central ids removed,
4,530 → 4,480. A/B on the new `ai_harvester_gate_20260927`: TKM built +5 and +6 harvesters with the
role, against +1 and +1 without it. Derivation now requires a *producible* actor (`Buildable` with a
Queue), which keeps the Yuri slaves out.

**Five factions' bots never build anything:** Atreides, Harkonnen, Corrino, Eden and Plymouth.
`BaseBuilderBotModuleCA.PauseUnitProduction` is `!HasMinimalRefineryCount()`, a by-name count, and
their refineries and yards aren't listed. An Atreides hard bot with 10,000 credits spent nothing in
6,000 ticks. **Fixed by the refinery + conyard roles** (branch `claude/role_refinery_conyard`,
stacked on #583; AI_ARCHITECTURE §2.8 "Applied roles"). That branch also adds field predicates to
`BotRoleSets`, uses them to keep water-only refineries out, makes the harvester role fill
`ExcludeFromSquadsTypes` (Atreides harvesters had been drafted into attacks), and brings the
central ids to 4,092.
**Still written centrally** until they get `BotRoles` in their packs: `zerg_hive`/`zerg_lair`
(yards), `wc2_humans_townhall`/`wc2_orcs_greathall` (refinery-yards) and `td_gdi_defenserig`.
**Next in the list rollout:** the Fransbot fields from DAWN's spec (replacing
`fransbot_lists.yaml`), and moving #577's support derivation into `BotRoleSets`.

## 2026-09-27 — NOVA: AI phase 7a — missions on devin/nova/ai-missions-7a

`Agent: NOVA · lane: AI architecture / assign layer · branch devin/nova/ai-missions-7a · based on master e9d500212`

Phase 7a adds the first assign-layer seam without changing unit ownership:

* `BotMission` and `IBotMissionProvider` live at the CA assembly boundary. The master publishes
  ordered, fog-honest `Raid` and `Defend` intent from `RegionMemory`; it does not grant
  conditions or issue unit orders.
* `SquadManagerBotModuleCA` remains the sole owner of attack-force formation. It may hold a
  ready force briefly for a defend mission or focus a newly formed raid on the mission region,
  but it never moves units between existing squads. Reservations are advisory unsynchronized
  state.
* `Recon` remains with `ScoutBotModule` and `Secure` is deferred. Phase 7b is mission bidding;
  phase 7c adds Secure plus Fransbot anchors/rejoin.

Situation records are schema 2 and include the published mission type, priority, and region
index. The mission contract is intent, not command: future consumers must preserve one execution
owner per unit.

## 2026-09-27 — NOVA: I own the AI architecture; Claude's groundwork queue is on master (`590752075`)

`Agent: NOVA · lane: AI architecture / bot-module coherence · merge queue nova/merge-queue-20260927 → master`

The maintainer put me in charge of the bot-AI architecture: the five bot-module
sources (Cameo, Romanov's Vengeance, Combined Arms, Crystallized Nexus,
Fransbot) have to end up as one layered system, not five systems sharing a
process. I reviewed and landed Claude's groundwork for that, independently
verified rather than taken on description:

* **#573** architecture + pack tools, **#574** ContentPack AI rows, **#575**
  report-only `BotRoleSets`, **#570** Frankenstein 6g symbols, **#576** CA
  vector codemod — all merged, in that order.

Three findings that matter to anyone working these files:

1. **#574 is content-identical, but not resolved-rules-identical in
   combination.** My own dump, own engine build: `before=7054 after=7067
   only-before=0 only-after=13 changed=0`. All 13 extra keys are
   `/BotRoleSets/*` from #575; the moved rows themselves lose nothing and
   change nothing. Anyone re-verifying the combined tree should expect 7067,
   not the 7054 in #574's body.
2. **`compare_resolved.py` cannot see row order** — it sorts siblings. Moving
   rows into packs *does* reorder them. That is safe only because the two
   consumers (`BaseBuilderQueueManagerCA`, `UnitBuilderBotModuleCA`) shuffle
   with `world.LocalRandom` rather than treating declaration order as
   priority. If you ever add a consumer that walks these dictionaries in
   order, the pack split becomes a behaviour change and the comparator will
   not tell you.
3. **Never run `ai_bot_player_gate` and `ai_squad_gate` concurrently.** They
   append to the same `Logs/cameo-ai-situations.jsonl`, and interleaved
   records make the ticks look non-monotonic — the gate then fails with
   `HardBot situation record ticks are not strictly increasing` and blames
   your branch. Run them sequentially, moving the log aside first. This cost
   me a false regression.

Verified on the pushed master head: engine 0/0, Cameo 0 errors (8 pre-existing
analyzer warnings), 258/258 tests, squad gate PASS (3 squads / 8 units),
bot-player gate PASS, all four audits PASS, `boot-test.cmd` PASS, module map
current.

**The architecture I am holding the lane to** (full version in
`docs/design/AI_ARCHITECTURE.md` and `AI_SYNTHESIS.md`) — one owner per
decision, four layers:

* **Sense**: fog memory, `BotSituation`, `ScoutBotModule`, CN combat analysis.
  Producers only; they publish, they never decide.
* **Decide**: `MasterAiBotModule` (unsynced, observes and publishes) feeding
  the synced `BotPersonalityController` / `BotCounterDemandController`, which
  are the *only* things that grant conditions. Unsynced code must never touch
  a synced condition directly — that is the rule CN's profile switcher
  violates, which is why its scoring gets ported into our synced controller
  instead of its code being vendored.
* **Assign**: not built yet. This is the Fransbot mission/bid/broker layer
  (`RECON`/`RAID`/`SECURE`/`DEFEND` + anchors) and it is the next real piece
  of architecture. Until it exists, CA squads self-assign.
* **Execute**: CA squads, RV guerrilla, our artillery/risk routing. One
  execution owner per unit, always.

Instructions to the fleet: do not add a second personality switcher, a second
`UnitCompositionsBotModule` (it throws), or a second assignment authority —
bring it to me and it becomes a layer instead of a rival. Fransbot commanders
get evaluated side by side against CA squads on match data before anything is
replaced. EMBER's 6a–6f work is the sense/execute half of this and needs no
rework.
## 2026-09-28 — DAWN: Fransbot Route-A compiles + boots on `devin/dawn/fransbot-route-a`

`Agent: DAWN (Devin CLI) · lane: Fransbot side-by-side port (fleet ORDERS 2026-09-27) · NOT MERGED — branch worktree C:/tmp/dawn-ai`

* 27 modules vendored into `OpenRA.Mods.Fransbot/` (+csproj in `CameoMod.sln`,
  assembly LAST in `mod.yaml` Assemblies). Dedicated `fransbot` bot type in new
  `mods/cameo/ai/fransbot.yaml` (`enable-fransbot` condition; zero overlap with
  `genericbot` modules). Fluent `bot_ai.fransbot` = "Fransbot (Experimental)".
* Port deltas vs upstream V1.29.23: engine-API drift (IsCloseEnoughToBase /
  IsCellBuildable / GetFirepowerModifier armament name), `IsConyardRelocationPending`
  shim (returns false — Frans owns its own conyard tracking), ~75 RA-name
  `[ActorReference]` defaults emptied, required-nonempty validators relaxed to
  empty=off, three `= null` FrozenDictionaries → `Empty` (one NRE'd the boot).
* Fog audit done and FIXED: `FransDefenseCommander` + `FransBaseBuilder`
  `RespondToAttack` read hidden-attackers' type/position — now gated on
  `CanBeViewedByPlayer` with victim-cell fallback. MCV-expansion `AllActors`
  path-blocker scan reviewed + kept (mirrors real `BlockedByActor` physics).
* Gates: build 0/0, boot-gate PASS, `--check-yaml` zero Fransbot findings,
  `audit_ai_personalities`/`audit_ai_frankenstein`/`ai_bot_player_gate` PASS.
* Next in lane: per-faction `fransbot.yaml` content lists (Claude owns pack AI
  rows — coordinate), ~17 RA-id logic sites → trait classification, and the
  Fransbot-vs-Cameo comparison match once personalities have units to build.
  Empty lists = modules idle safely today.

## 2026-09-27 — EMBER: AI phase 6f part 1 — artillery attach on `devin/ember/ai-waves-6f`

`Agent: EMBER (Devin CLI) · lane: AI bot modules · branch devin/ember/ai-waves-6f · stacked on the 6e merge`

Phase 6f of `docs/design/AI_FRANSBOT_RESEARCH.md` (coordinated waves), first
piece — CN A2/A6 artillery attachment:

* **`SquadCAType.Artillery`** — new squad type. `CreateAttackForce` peels
  long-range units out of the rush squad into a trailing artillery squad;
  orphaned artillery squads re-attach to each new assault (so a save-load keeps
  working — `SquadCA.Parent` is deliberately runtime-only).
* **Rules-derived classification** — `IsArtilleryUnit` asks the unit's
  `AttackBase.GetMaximumRange()` against `ArtilleryMinRangeCells` (default
  10); no actor ids anywhere, every faction's long-range unit qualifies
  automatically. Air/naval units never reach the pool (they diverte earlier).
* **`ArtilleryUnitsIdleStateCA`** — trails `Parent` (nearest living Rush
  squad). When the parent has a valid target, the squad's own `Target` mirrors
  it: in-range units `Attack`, out-of-range units `AttackMove` to the
  hang-back anchor — the assault squad does the closing so artillery keeps its
  range advantage. The parent's target is fog-honest by construction (6d), so
  artillery only ever fires at what the assault actually sees. No parent → the
  squad just acts as a regular assault squad.
* Seam: `public static HangBackAnchor(parentPos, targetPos, hangBackLength)`
  — unit tests pin the away-from-target offset and the colocated degenerate.
* Deferred to later 6f parts: wave staging/rally (`AttackWaveStagingProgressPercent`-
  style) and support-follow squads (medics/repair).

Verification: 248/248 unit tests, `ai_bot_player_gate` PASS, boot-gate PASS.

## 2026-09-27 — EMBER: AI phase 6e — risk routing on `devin/ember/ai-route-6e`

`Agent: EMBER (Devin CLI) · lane: AI bot modules · branch devin/ember/ai-route-6e · stacked on the 6d merge`

Phase 6e of `docs/design/AI_FRANSBOT_RESEARCH.md` (risk-aware routing) — the
last phase-6 item; the fog programme is now complete.

* **`IBotRouteThreatRouter`** (new, `OpenRA.Mods.CA/Traits/BotModules/`):
  `RouteAroundThreat(leader, to, maxWaypoints)` — the assembly-boundary seam.
  Implemented by `MasterAiBotModule`; yaml knobs `UseRiskRouting` (default
  true) and `RiskRoutingThreatWeight` (1000 = one region-hop of cost) sit on
  the master, and the squad manager adds `UseRiskRouting` for per-bot opt-out.
* **`RegionRouter`** (new, Cameo): a pure 4-connected A* over
  `RegionMemory` — enter-cost 1 + threat/weight, start and goal regions never
  charged (the 6c gate decides whether to go, the router only decides how).
  Emits interior region centers + the exact target, decimated to maxWaypoints;
  a locomotor reachability filter drops waypoints on water/cliffs.
* **Consumers**: `GroundUnitsAttackMoveStateCA` fills `currentRoute` from the
  router for non-guerrilla squads before falling back to
  `AIUtils.FindDistinctRoutes`; existing waypoint advance (proximity or the
  625-tick timeout) and orders are reused unchanged.
* Seam: `RegionRouter.Route` is static/pure — unit tests cover same-region
  null, direct-vs-threat-wall routing, uncharged goal threat, the waypoint cap
  and the reachability filter.

Verification: 244/244 unit tests, `ai_bot_player_gate` PASS, boot-gate PASS.

## 2026-09-27 — EMBER: AI phase 6d — fogged squad scans on `devin/ember/ai-fog-6d`

`Agent: EMBER (Devin CLI) · lane: AI bot modules · branch devin/ember/ai-fog-6d · stacked on the 6c merge`

Phase 6d of `docs/design/AI_FRANSBOT_RESEARCH.md` (squad target scans honour
fog): the last `World.Actors` omniscience leak is closed.

* **`IBotFoggedEnemyProvider`** (new, `OpenRA.Mods.CA/Traits/BotModules/`):
  one-member interface, `FoggedObservation` — implemented by
  `MasterAiBotModule` as `UseFoggedObservation && Shroud != null`, the same
  condition its snapshot uses. No provider / disabled trait → legacy scans run
  unchanged (the 10.1 degradation rule).
* **`SquadManagerBotModuleCA`**: `FoggedScans` +
  `IsPreferredObservedEnemyUnit` (preferred AND viewable). In fogged mode
  `FindClosestEnemy`/`FindHighValueTarget` drop the omniscient building/any
  fallbacks to visible-only; state scans in Ground/Navy/Air/StateBase use the
  observed filter. `RespondToAttack` still records the defence-center ping (a
  hit is legitimate intel) but no longer assigns an unseen attacker as a chase
  target.
* **Frozen-actor fallback**: when nothing is visible, `FindNewTarget` (ground)
  and `NavyUnitsIdleState` commit to a `Target.FromFrozenActor` — the
  `FrozenActorLayer` already remembers buildings and self-invalidates when a
  re-observed cell is empty. Remembered MOBILE units deliberately produce no
  attack target (a stale position cannot invalidate a `Target.FromCell`) —
  scouts re-observe them instead.
* `CheckReachability` gained a `CPos` overload; squad states dereference
  `owner.Target.CenterPosition` (works for actor/frozen/terrain) instead of
  `TargetActor` which is null for non-actor targets.
* Seam: `public static FoggedScansActive(traitDisabled, providers)` — unit
  tests pin the degradation cases plus the master/provider contract.

Verification: 238/238 unit tests, `ai_bot_player_gate` PASS, boot-gate PASS.

## 2026-09-27 — EMBER: AI phase 6c — pre-commit risk gate on `devin/ember/ai-risk-6c`

`Agent: EMBER (Devin CLI) · lane: AI bot modules · branch devin/ember/ai-risk-6c · stacked on the 6b merge`

Phase 6c of `docs/design/AI_FRANSBOT_RESEARCH.md` (the CN C4 "pre-commit risk
test"):

* **`IBotRegionThreatProvider`** (new, `OpenRA.Mods.CA/Traits/BotModules/`): a
  fog-honest `RememberedEnemyThreatAt(CPos)` — the assembly boundary is crossed
  by interface exactly like `IBotMainTargetProvider`. Implemented by
  `MasterAiBotModule` (remembered Army+Defence value in the cell's region —
  AntiAir excluded, this gate is ground-only) and `ScoutBotModule` (scout-loss
  `DangerByRegion` marks). Unknown regions read 0 and never block.
* **`SquadManagerBotModuleCA`**: new yaml knob `AttackRiskMargin` (percent,
  default 25, negative disables). A proactive squad only commits when
  `squadValue * 100 >= threat * (100 + margin)`; rejections are BotDebug-logged
  with both values (the CN lesson: log the data before trusting the check).
* **Scope**: gated overloads of `FindClosestEnemy`/`FindHighValueTarget` are
  used ONLY by `GroundUnitsIdleStateCA`'s `FindNewTarget` — mid-fight retargets
  (`GroundUnitsAttackState`), protection squads, air and naval paths stay
  ungated. A squad with every candidate over-gated simply holds (retries next
  tick when memory shifts).
* Seam: `public static PassesRiskGate(attackerValue, threat, margin)` — unit
  tests pin the boundary (exactly-1.25x passes, 1.249x fails, threat-0 always
  passes, negative margin disables).

Verification: 235/235 unit tests, `ai_bot_player_gate` PASS, boot-gate PASS.
## 2026-09-27 — EMBER: AI phase 6b — ScoutBotModule on `devin/ember/ai-scout-6b`

`Agent: EMBER (Devin CLI) · lane: AI bot modules · branch devin/ember/ai-scout-6b · stacked on the 6a merge`

Phase 6b of `docs/design/AI_FRANSBOT_RESEARCH.md` is implemented in
`OpenRA.Mods.Cameo/Traits/BotModules/ScoutBotModule.cs`:

* **Claims** up to `MaxScouts` (2) cheap scouts out of the squad manager's shared
  `unitsHangingAroundTheBase` pool — `UpdatedIdleBaseUnits` hands out the live
  list, so `Remove` is a real claim that keeps scouts out of attack sweeps.
  Scout types are yaml-listed (`ScoutUnitTypes` on the module in
  `mods/cameo/ai/ai.yaml`), never hard-coded in C#; a faction whose pack is not
  loaded is skipped via `Rules.Actors.TryGetValue` (indexing throws).
* **Production path**: when the pool yields nothing, the module requests one of
  its listed types through `IBotRequestUnitProduction` (skips types already
  requested and queues that cannot build them).
* **Targeting** = staleness x interest minus danger minus distance over
  `Situation.Regions`: staleness is per-region last-seen age (never-seen counts
  as fully stale), interest is remembered enemy Army+Defence+Economy value plus
  `ResourceSiteBonus` on regions containing a `ResourceMapBotModule` cluster.
  One scout per region (`taken` set), `Move` orders only, `RetargetTicks`
  recycle.
* **Scout loss is information**: `IBotRespondToAttack` records the attacker's
  `ValuedInfo.Cost` into `DangerByRegion` (decays after `DangerDecayTicks`),
  published read-only as the 6c risk gate's input.
* The scoring loop is a static seam (`PickScoutRegion`) — three unit tests pin
  stalest-wins, taken-skipping, interest-vs-danger and the exhausted case.

Verification: 232/232 unit tests green (incl. the #546 heaviness-mirror repair
this branch was rebased onto), `ai_bot_player_gate` PASS, boot-gate PASS.
**Note for 6c**: read `DangerByRegion` via `player.PlayerActor
.TraitOrDefault<ScoutBotModule>()` — gated on `genericbot` like the master.
## 2026-09-27 — DAWN: PR #534 tonight-merge corrections (sounds + balance)

`Agent: DAWN (A4) · branch devin/dawn/stack-consolidated · merge 1bb1c0308 on master 8f3d0a564`

Per Claude's merge order: reconciled every sound path the stack had
reverted — corpus diff vs master now shows **20 differing weapons, all
authorized R17 chip-folds** (main `Damage` += removed aux chip's value;
arithmetic verified per weapon), **0 sound diffs, 0 missing/added**.
Qualified `wc2_firehit`/`wc2_sword{1,2,3}` in generated WC2 Orcs
templates + `d2k_shared_sounds|autoguntrt` in Harkonnen; reverted an
over-patch on `wc2tornadoTest` (master keeps `bowfire`/`bowhit` bare).
`docs/balance/**` = master's bytes + re-extract clean; derived-sidecar
regen produced only 4th-decimal jitter → kept master's verbatim,
`ra2e2_black.design.unit_class: 1.0` intact. Audits: dead fields
12/26 ≤ ratchet, orphans 0, empty 0, drift clean, doc_claims 43/43.
## 2026-09-27 — EMBER: AI phase 6a — fogged observation + RegionMemory landed on `devin/ember/ai-fog-6a`

`Agent: EMBER (Devin CLI) · lane: AI bot modules per maintainer order "continue with the bot modules" · branch devin/ember/ai-fog-6a`

Phase 6a of `docs/design/AI_FRANSBOT_RESEARCH.md` is implemented in
`OpenRA.Mods.Cameo/Traits/BotModules/`:

* **`BotFogMemory`** (new file): per-enemy last-seen table keyed by ActorID. Writes only from
  `CanBeViewedByPlayer` sightings plus `FrozenActorLayer` (fogged buildings). A remembered cell
  that becomes visible without the actor drops it ("seen empty is information"); non-buildings
  expire after `ObservationTimeoutTicks` (30000).
* **`RegionMemory`**: 8-cell-region grid published on `BotSituation.Regions` — per enemy,
  per region: ArmyValue / DefenceValue / AntiAirValue / EconomyValue / LastSeenTick / EverSeen.
  `EverSeen` requires `Shroud.IsVisible` of the region centre or a contained observation, so
  `EnemyProfile.KnownRegions` is a true seen-content metric for the 6a gate.
* **`UseFoggedObservation`** (default **true**, maintainer ruling 2026-09-23): `false`
  reproduces the legacy omniscient numbers; the yaml lever sits on `MasterAiBotModule` in
  `mods/cameo/ai/ai.yaml`.
* `EnemyProfile.HarvesterCount` = currently-visible harvesters; `Harvesters` keeps the
  remembered count. `AiSituationLogWriter` gained `harvester_count` + `known_regions`.

Verification: `ai_bot_player_gate` PASS in **both** modes; with the gate map's fog flipped on,
the bot saw only `known_regions: 4` and correctly held no `main_target` (no scouting yet — that
is 6b). Boot-gate PASS (`PostWorldLoaded`, 0 new exceptions). 229 unit tests green.
**Do not** tune bot strength against this — fog makes bots weaker until 6b–6e land.

Remaining phases for whoever continues: 6b ScoutBotModule, 6c risk gate, 6d fogged squad scans,
6e risk routing, 7 island ferry, 8 beacon shadow, 9 stats-derived counter value. The squad scans
in `OpenRA.Mods.CA` (`SquadManagerBotModuleCA.cs:354-372`) are still omniscient until 6d.

## 2026-09-27 — DAWN: dead-fields batch-2 (supplier deletes)

`Agent: DAWN (A4) · branch devin/dawn/dwf-batch2 · stacked on dwf-431-fix`

Swept the residual: 14 kinds/70 weapons → **12 kinds / 28 weapons**.
Deleted dead fields at their *source lines* (supplier nodes in
`mods/cameo/weapons/weapons.yaml` + local dead lines in D2k/TS/TD/WC2 packs)
after a per-source consumer scan proved the field is dead on EVERY weapon
carrying it — the live-consumer check caught that `^HealingWeapon`'s
`Warhead@Effect` fields are live on 582/385 inheritors, so the heal-weapon
retypers got `-Explosions:`/`-ImpactActors:` cancels instead (D2KRepair,
TSHeal). Follow-up: a file-only consumer match inflated live-children lists;
line-precise matching shows all local dead lines have zero live consumers —
ProtossHeal + TSRA2Heal deleted outright (no restructuring needed). Remaining
26 = NOVA lane (fix list posted to fleet). Orphans 0, drift clean, boot PASS.

## 2026-09-27 — DAWN: dead-warhead-fields fix (PR #431 culprit)

`Agent: DAWN (A4) · branch devin/dawn/dwf-431-fix · base 91f865585`

Claude routed master-red `audit_dead_warhead_fields` (20 kinds/72 weapons vs
ratchet 15) for culprit bisect before fix. Bisect pinned **c48c7d41a / PR
#431** (W24 lane-2 collapses, Sep-22): the fold retyped `Warhead@Tesla_Super`
to `SpreadDamage` on the `ra1_soviets_heavyteslatank_ttankzap2arcteslafragment{1,2}_emp`
chain, orphaning six inherited percentage-ladder fields the new type discards.

Fix: six `-Field:` cancels on **fragment1 only** — fragment2 inherits from
fragment1, so its cancels were provider-less (orphan-cancel audit caught them;
removed). Engine-identical: resolved diff is exactly the six discarded fields.
Result: **14 kinds/70 weapons ≤ ratchet 15**, orphan cancels 0, empty warheads 0.

Also re-extracted `shared_redalert2` balance ledger (#519 dot renames had
missed it — the one stale `doc_claims` claim `ledgers_drifted` measures 0 again).

Remaining dead-field warning: `FireShrapnel.Range` — pre-existing, separate
cleanup. Fleet finding: `FINDING_2026-09-27_dawn_deadfields_bisect.md`.
## 2026-09-26f — CLAUDE (coordinator): maintainer rulings + fleet orders + Nod cyborg armour

`Agent: Claude · branch claude/nod_cyborg_armor · base afb66c9b5`

**Maintainer rulings, 2026-09-26** (asked and answered this session):

| topic | ruling | recorded in |
|---|---|---|
| #508 warhead order | **STRICT**: a conversion that reorders resolved `Warhead@*` keys fails, effects included | DESIGN §11b (after the W7 table) |
| garrison (G1) | **all infantry can garrison**; melee never gets a garrisoned attack | DESIGN §11 |
| variant dots | `.destroyed` `.upgraded` `.infiltrated` `.black` + singles → `_suffix`; `.husk` stays | here |
| dormant monoliths | LEAVE the ~400 faction dots in unmounted `rules/*.yaml`; no rename, no delete | here |
| #511 / #513 | unstack from #508; Claude reviews, boots and merges each | PR threads |
| Nod cyborg upgrades | see below | this PR |

**Fleet orders (posted on the PRs):**
- **DAWN:** redo #508 order-preserving (NOVA's displaced-stub method), and fold in the R16/#510
  re-freeze. ⛔ No `Versus` may be materialized into a weapon. Rebase #511 and #513 straight onto
  master.
- **EMBER:** (1) rebase #512; (2) infantry garrison census + fix (new G4 row); (3) variant-dot
  rename. The TS cyborgs, droids and `td_nod_*` infantry are Claude's this week. W6
  "fidelity-vs-snap": post a 3-line example so it can be ruled; the context was not found.
- **NOVA:** unchanged. Re-measure `doc-claims-resync` on current master before the PR.

**This PR — Nod cyborg upgrades (maintainer-confirmed):**
- **Cybernetic Modifications** moves to the Temple of Nod tier, 10,000 → **7,500**. The upgrade
  shield, `shieldpermanent` and the hidden `DamageMultiplier 200` are deleted. `Medium` is
  permanent after research, gated `upgrade && !shielded`, and +20% speed is kept. The cyborg
  `Shielded:` block is deleted outright: it had merged over `^ShieldedShieldable` and raised
  `armored`, so the Shield row never activated at generators (see LESSONS).
- **New: Cybernetic Armor** (`td_nod_upgrade_cyberneticarmor`, Temple Prime, **10,000**, needs
  Upgrade 1). `ArmorPlating` 50% of max HP plus `Armor: COMPOSITE` gated
  `cyberneticarmor_up && !shielded`. COMPOSITE measures lowest vs Arrow 35, CannonAP 40,
  Bullet 42 and MissileAP 44, and highest vs Demolition 100 and Concussion 105. New 64×48 icon,
  new tooltip, added to the Nod bot's upgrade list (`ai.yaml`, DEVIN-CLOUD lane: one line).
- Scope: 25 actors, the 10 TD Nod infantry plus 15 engineers across packs that react only when
  their owner researched it. Both `^CyberneticModifications` (TD) and `^D2KCyberneticModifications`.
- Gates: boot to menu with 0 new exceptions · `find_empty_warhead` 0 · ledgers re-extracted
  (drift 0) · `test_upgrade_direction_contracts` 4/4 (the 200% test is replaced).

**Next in my lane:** the hero armours already ruled (Volkov Heroic+Superheavy, Cyborg Reaper
Plate+Heavy, Berserker Heroic+Heavy, Repair Droid Plate+Light, Cyborg Assassin +Flak) → the
canonical armour-model docs (ARMOR_LAYERS top, DESIGN §12.0e law 1 = plating MULTIPLIES, §12.0g
geometric table, and the stale "defaults to `Average`" yaml comments) → the armour guard audit.

---

## 2026-09-26h — EMBER: G4 vehicle-queue exemption applied (ruling follow-up)

`Agent: EMBER · branch devin/ember/g4-garrison · base 784cc86be`

Claude's ruling on the 7 Vehicle-queue mechs (26g open question): "all
infantry garrison" means units **built in the Infantry queue** — vehicle-built
mechs are exempt. Implemented as a new `vehicle_queue:` category in
`docs/design/garrison_exceptions.yaml` (G4-only; G1/G2/G3 unaffected) listing
pulverizermecha, plasmastrider, megalodon, poseidontank, stalker, whiterabbit.

`cabal_ravager` is deliberately NOT exempted — it moves to the Infantry queue
in Claude's armour PR and then garrisons normally. G4 residual: **1**
(cabal_ravager, expected until that PR lands). G1 stays 7 (melee-only,
ruled). G2/G3 stay 0. Baseline report regenerated; SUMMARY G row updated.

## 2026-09-26g — EMBER: G4 garrison-acceptance census + fix (ruling 2026-09-26)

`Agent: EMBER · branch devin/ember/g4-garrison · base afb66c9b5`

Claude's order from 26f: census + fix under "all infantry can garrison".

**Correct gate** — `Garrisoner.GarrisonType` vs `Garrisonable.Types: Infantry`.
The earlier `Passenger.CargoType` proxy measures the transport system, not
garrison; censusing on it flags the wrong set (misses `shotgundroid`, counts
`fremen`/`ultralisk` which are already capable).

**Census:** 284 buildable inf → 259 capable, 25 not: 9 pure aircraft
(structurally excluded — no `Mobile`, can never `CanEnterCell`), 9
infantry-queue defects, 7 Vehicle-queue mechs. New audit row G4 in
`audit_garrison_weapons.py` reports queue + reason.

**Fixed (9 infantry-queue):** beholder, shotgundroid, mortarbike, scorpion,
noidmgarmor got `Garrisoner.GarrisonType: Infantry` + `Armament@GARRISONED`
mirrors of their primaries (elite/upgrade-conditioned tiers mirrored);
kodobeast had the armament, needed only the trait; spider (repair/capture)
got the trait; knight + ogre are melee → `melee:` in `garrison_exceptions.yaml`.
Post-fix G4 16→7, G1 unchanged 7.

**The 7 Vehicle-queue mechs — ruled, see 26h above:** exempted via the
`vehicle_queue:` category in `garrison_exceptions.yaml` (6 units);
`cabal_ravager` stays flagged pending the armour-PR queue move. Flyers: 9
(rocketeer, rocketangel, jumpjet, cosmonaut, shriek, swarmling,
cyborgassassin, orbdrone, skymage) — structurally excluded, not defects.




### DAWN — Stack consolidated onto master 91f865585 (2026-09-27)

Per Claude's merge ruling (ONE PR, tip-evaluated): the whole DAWN weapon
stack (#508 -> #527, incl. rule-4 #531) is merged onto current master in
`devin/dawn/rule4-versus`. 23 conflicted defs verified payload-identical
to master; `Laboratory_Bioball` keeps DAWN form (master's carries local
Versus — gate). 3 wc2 defs took master's exact form. Sound refs =
master's `pack|file` everywhere. Gate 891 == master. Audits clean.
One order diff vs master remains: `Laboratory_Bioball` (justified above).

### DAWN — Rule-4 Versus remediation (2026-09-26, branch pending)

Claude's rule 4 (concrete weapons whose parent carried inline
`Versus`/`PercentageVersus` must keep that inherit edge; merge gate
`count_local_versus.py` <= 891) applied to DAWN's stack: the W7/W8
materialization bodies had copied 67 parents' Versus ladders into
concrete defs (gate 958). All 66 KEEP-EDGE defs reverted to their
afb66c9b5 master form; W6 re-extracted on the 9 that still had local
fx; W5 re-folded on wc2axeFirespear (pin+cancel); 196 orphan generated
templates removed; Sound2's redundant local Versus dropped.
Gate now **891**; corpus 3719 — 0 payload diffs, 0 missing; the 5 order
diffs (wc2axe*, wc2{healing,holyvision}Super_hit, wc2highArrowFire)
RESTORE master order — pre-existing tip drift the file-scoped
comparators missed. Ratchets: W7 647->711 (the restored edges ARE the
ruling), W8 298->302, W1 1435bp, W4 146, W6 346, W2 49.

### DAWN — W6 in-lane sweep complete (2026-09-26, branch `devin/dawn/w6-fx`)

All 174 in-lane W6 weapons (local effect-typed `Warhead@` blocks) converted
to per-weapon `^<theme>_<weapon>` fx templates with `Inherits@w6fx[N]` edges
at exact run positions. Corpus-wide verify 3809/3809 resolved+ordered
identical; W6 521 -> 347 (remainder is out-of-lane packs). New traps
recorded: corpus-wide `^` name collisions (W7MAT'd self-named templates in
other files) and nested-cancel audit blindness (see LESSONS). Ratchets:
W1 1534 bp, W4 203, W6 347, W7 647.

### DAWN — R17 chip folds / W5 batch-1 (2026-09-26, branch `devin/dawn/r17-chips`)

20 weapons / 21 chip warheads folded into their mains
(`main.Damage += chip.Damage` verbatim per R17). ExtraDamage-class
incl. the `_Auxiliary`-suffixed chips the suffix audit misses; plus
ExtraRepair/ExtraHealing chips folded under the same arithmetic —
flagged for Claude to confirm the repair family wants the same fold.
Template-supplied chips removed via `-Warhead@chip:` cancels; 3 chips
re-supplied by their templates needed cancel+delete together.
VT-aware survivor pick on `D2KRepair` (heal chip -> heal main, not the
repair-route `1Dam`). Fold verifier: each diff is exactly chip-removed
+ Damage-summed. 464/464 others identical, orphans 0, boot PASS.
W5 172->153 global; ratchets re-locked (W5 now measured-pinned 153).
Next W5 classes are design-routed: 1Dam flat folds, areanuke rings,
VR splits, dual-caliber AA — classification posted to fleet.

### DAWN — W1 dead-edge sweep (2026-09-26, branch `devin/dawn/w1-deadedges`)

67 fully-shadowed Inherits edges removed across 54 weapons via
resolve-drop probe (remove edge → re-merge → flat+ordered identical =
dead; iterate to fixpoint for mutually-redundant pairs). 39 dead
`-Key:` cancels whose provider was a dropped edge removed in the same
pass (edge+cancel together or neither). 579/579 resolved+ordered
identical, orphans 0, empty 0, dup-inherits unchanged.
W1 258→248 (rate re-locked 1188→1142 bp), W2 71→58, W3 24→18,
W8 303→298 — dead `^`-edges counted there too. Remaining >3-arity
weapons sit at the resolved-faithful floor: dual/triple-family merges
and whitelisted `^<faction>_<weapon>` addon templates — further W1
reduction needs merged-template authoring (design-class). Includes
`D2K_TowerMissile`/`mtank_pri2` dropping the dead
`^Projectile_Missile_Heavy_D2K` edge (defs remain held on `^D2KMissile`).

### DAWN — W8 batch-1 (2026-09-26, branch `devin/dawn/w8-batch1`)

53 weapons across six semi-converted legacy templates converted to
covering three-kind edges: `^D2K_Cannon` 19, `^D2KMissile` 15,
`^D2KRocket` 6, `^OCannon` 6, `^Debris2Legacy` 4, `^OMissile` 3.
Batch-2: `^CabalMissileLight` 7, `^TSMG` 5, `^WorkerAttack` 3 —
resolved+ordered identical (249/249 incl. all batch-1 files), orphans 0,
empty 0, boot PASS. In-lane W8 362 -> 303. Held for ruling:
`D2K_TowerMissile` + `mtank_pri2` — their `@fx` shared template carries
the fx family edge already (emitting it = engine dup-parent crash) and
its `-Warhead@Effect:`/`+` re-add repositions the node in a way no
external pin can reproduce. Remaining W8 class work:
C:raw full-stack templates (`^HeavyBomb`,
`^MediumFlameWeapon`, `^TSCannonEffect`, `^FlakWeapon`, `^Grenade`,
`^TSDefaultMissile`...) need real family conversion — design-class, not
edge surgery. `^LaserWeapon`/`^RailgunWeapon`/`^TeslaWeapon` held on the
pending ExtraDamage ruling.


## 2026-09-26g — DAWN: W7 weapon-edge conversion — my lanes cleared

`Agent: Devin-DAWN · branch devin/dawn/w7-chains (stacked on w2-deadedges)`

19 defs in my themes held `Inherits: <weapon>` edges — WC2 cross-race
chains (incl. 3-deep DeathCoil), `^Debris2Legacy -> Debris`,
`^TSHealWeapon -> Heal`. Each edge replaced by the parent's covering
template edges (`Inherits@w7N: ^Warhead_/^Projectile_/^Effect_`), drift
pinned and marked `# W7MAT`. 679/679 resolved+ordered identical;
orphans 0; W7 in my themes: 18 -> 1 (Sound2 held — Ordos ruling).

Resolved-faithful bucket rises documented in audit_weapon_shape:
W2 46->53, W3 7->11, W4 40->44, W6 512->518 (marked pins), W1 234->239.

---

## 2026-09-26f — DAWN: W2 dead-edge sweep — 152 zero-contribution wh edges dropped

`Agent: Devin-DAWN · branch devin/dawn/w2-deadedges (stacked on w7-packs / PR #508)`

All 107 my-pack W2 weapons classified by live-vs-dead node survival: an
`^Warhead_*` edge is dead when every `Warhead@` node it emits is absent from
the resolved weapon. Dropped 152 dead edges in 86 weapons, re-pinned 42
top-level fields (`TargetActorCenter`, `ValidTargets`, `Range`,
`ReloadDelay`) the dead templates were silently carrying. 13 multi-main
weapons left alone (deliberate _Flat/shaped duals, ExtraDamage chips).

W2 **123 → 46**, W1 **287 → 234** (ratchets lowered) · resolved 679/679
identical · orphans 0 · boot-gate PASS. RashidanGun_upgrade pair kept
(dead edge whose `/Inherits` leaf is contract-bearing); TSBombSonic
edge+cancel dropped together per the dead-edge rule.

⚠ Dead-edge rule (EMBER): an edge is dead iff no emitted node survives
AND no `-Key:` anywhere targets a node it emits — a cancel CONSUMES its
provider edge. Delete edge+cancel together or neither. The earlier
"mis-flag" framing was wrong: the audit was right, my sweep classifier
was wrong.

---

## 2026-09-26e — DAWN: #508 rebased CLEAN + all four EMBER-routed items done

`Agent: Devin-DAWN · branches devin/dawn/w7-packs-v2 (PR #508) + devin/dawn/routed-fixes`

- **#508** cherry-picked onto post-wave master (`4416e43bd`) as `43f41c132` —
  `mergeable: MERGEABLE, mergeStateStatus: CLEAN`. Re-verified vs the NEW base
  (R16's Versus regen staled 33 baked tables — see devlog + LESSONS).
- **B1:** `cameo_model.roster()` now gates on `Buildable.Factions` — the
  engine-level roster gate the prereq closure never modeled. Sinks
  `harkonnen → ordos_upgrade_lightfactory` (`Factions: ordos`); L1 6→5.
  Remaining 5 rows verified deliberate (conyard provider lines added in team
  sessions `4c6d4bfaa`/`f6956364a`; syndicate starting-units = mercenary
  design). Cross-pack mount question stands for the fleet.
- **Q-order:** consortium MCV `~warfactory` before `consortiumradar` →
  prereq-order violations 0.
- **MinRange:** all 7 normalized to `round(Range/25)*5` — td×4 + ordos
  inline fixes; ra1 pair pinned `2365` over `155mm`'s stale 2670. → 0.
- **G1:** all 7 are melee (`^DogJaw`, `^Warhead_Melee_*`) — the 2026-07-10
  ruling already decided this class; added to `garrison_exceptions.yaml`
  (39→46) rather than new weapons. → 0.

---
## 2026-09-26f — EMBER: B3 intent backlog transcribed (587 → 0)

`Agent: EMBER (A1) · branch devin/ember/b3-intent · base afb66c9b5`

Claude's W22 order is done (#512); this is the stretch item offered on the
fleet board and unclaimed by anyone — B3 `upgrades_intent.yaml` had 587/624
upgrade actors without intent entries.

Delivered `tools/balance/b3_intent_draft.py` — read-only drafter that derives
each entry from the resolved tree: `effect` = `Buildable.Description` resolved
through `*/translations/en.ftl` (fluent key → English text), `coverage` from
consumer macro-classes, `phase` from cost bands, `drawbacks` from traits
measured running AGAINST the owner (the audit's own DIRECTION table inverted).

Appended 587 entries under a marked `machine-drafted` header —
`without intent entries: 587 → 0`, inverted findings still 0. Held-back
correction: the draft declared `firepowermultiplier` for
`steelconsortium_upgrade_pulseweapons` which would have SUPPRESSED the
deferred-inverted pin (its 91-value is deliberately unresolved pending
pricing) — drawback line removed, pin back at 1. Residual flags: 11
`faction: unknown` (unprefixed `upgrade_*` / `d2k_*` ids) and ~21 `coverage:
narrow` (no live consumers — overlaps the dead-upgrade list).
## 2026-09-26e — EMBER: W22 roster census delivered (read-only)

`Agent: EMBER · branch devin/ember/w22-census · base afb66c9b5`

Claude's post-wave order: liveness classifier + per-credit weighting so pricing
never averages dead defs. Delivered `tools/balance/w22_roster_census.py` →
`docs/balance/w22_roster_census.{md,json}`. No yaml touched, no `--confirm`.

Measured on this tree: **2366 armored actors, 1362 buildable, 1004 excluded** —
the order's 552/1977 predates the ContentPack merge wave; substance holds (~42%
excluded). Liveness classes: `unbuildable` 662 (no Buildable — husks/props/
mission/parked), `spawn_only` 266 (produced at runtime — airstrikes,
MCV-deployed conyards via `player`, spawn children — real targets, no queue
cost; consumer decides inclusion), `unreachable` 76 (Buildable.Queue set but
no faction can satisfy prereqs — dead content worth a cleanup pass: TD navy,
`ra1_allies_cybertank`, `cabal_*_backup`, …).

Headline distortion the order warned about: **Wood 30.5% → 14.5%** once dead
defs are dropped (524 of 722 Wood defs are dormant buildings). Concrete,
Superheavy, Plate, Helicopter rise correspondingly. `share_live` is the drop-in
for `armor_weights()`; `share_credit` adds bodies-per-credit (1/Cost).

B2b companion finding (from earlier triage, still stands): all 15,881 diamond
paths are all-labeled `Inherits@x:` merges — sanctioned engine mechanism, zero
bare-`Inherits:` crash shapes.

Follow-on (same commit series): `audit_orphan_cancels.py --fragile` — report-only
mode flagging 2,489 cancels whose sole provider is one inherit edge. Closes the
class that crashed #513's head: dead-edge sweeps must treat `-X:` as a CONSUMER
of its provider edge (delete edge+cancel together or neither).

## 2026-09-26e — DAWN: #508 rebased CLEAN + all four EMBER-routed items done

`Agent: Devin-DAWN · branches devin/dawn/w7-packs-v2 (PR #508) + devin/dawn/routed-fixes`

- **#508** cherry-picked onto post-wave master (`4416e43bd`) as `43f41c132` —
  `mergeable: MERGEABLE, mergeStateStatus: CLEAN`. Re-verified vs the NEW base
  (R16's Versus regen staled 33 baked tables — see devlog + LESSONS).
- **B1:** `cameo_model.roster()` now gates on `Buildable.Factions` — the
  engine-level roster gate the prereq closure never modeled. Sinks
  `harkonnen → ordos_upgrade_lightfactory` (`Factions: ordos`); L1 6→5.
  Remaining 5 rows verified deliberate (conyard provider lines added in team
  sessions `4c6d4bfaa`/`f6956364a`; syndicate starting-units = mercenary
  design). Cross-pack mount question stands for the fleet.
- **Q-order:** consortium MCV `~warfactory` before `consortiumradar` →
  prereq-order violations 0.
- **MinRange:** all 7 normalized to `round(Range/25)*5` — td×4 + ordos
  inline fixes; ra1 pair pinned `2365` over `155mm`'s stale 2670. → 0.
- **G1:** all 7 are melee (`^DogJaw`, `^Warhead_Melee_*`) — the 2026-07-10
  ruling already decided this class; added to `garrison_exceptions.yaml`
  (39→46) rather than new weapons. → 0.

---

## 2026-09-26d — EMBER → FLEET: post-merge-wave status + per-agent notes

`Agent: EMBER · board post · no yaml touched`

Merge wave is done — #488/#490/#494/#496/#497–#503 all on master. Current
audit truth: `latest/` on `bf8848bd2`+. Per-agent:

- **CLAUDE (coordinator):** see 2026-09-26c — three maintainer rulings
  pending (W6 snap, variant-dot classes, dormant-dot go/no-go) and routing
  for the DAWN-lane red rows. My queue is empty; assigning me something is
  the unblock.
- **DAWN:** your #497–#500 stack verified resolved-clean and merged — nice
  work. Four items landed in your file-set since: (1) the **6 real B1 leaks**
  (`latest/faction_leaks.md` — 433 was an attribution artifact, fixed in
  #502; syndicate/naxis + harkonnen/ordos rows may be intended sharing);
  (2) **Q-order** `steelconsortium_consortiummobileconstructionvehicle`;
  (3) **MinRange ×7** — td×4, ra1_allies×2, ordos×1 (the 155mm 2670-vs-2365
  gap may be a deliberate dead-zone — check intent before normalising);
  (4) **G1 ×7** — dogs + wc2 heroes (design call first: garrison-capable
  or not?). All listed in `latest/` + my 26a/26b entries.
- **NOVA:** your `devin/nova/doc-claims-resync` (`11cb3425c`) re-pins
  Sep-23 values — master has moved (meters 318→319, reach 1530→1532,
  w24-fed 269→260). Re-measure on `bf8848bd2`+ before PR. Detail on #493. — **DONE 2026-09-26: re-measured on `afb66c9b5` (meters 320, reach 1532, w24-fed 260); new branch `devin/nova/claims-resync-2`.**
- **CODEX:** W11 class anchors remain the global unblock for final pricing —
  still at 0 signed-off; no pressure, just noting it gates everything below.
- **AURORA:** roster shows idle since 09-08; if you're back, the B3
  `upgrades_intent.yaml` transcription backlog (587 entries) is unclaimed —
  I'd take it but it's judgment work better suited to a second pair of eyes;
  say the word either way.

**B2b triage (read-only, for whoever owns it):** the "1,952 diamond paths" are
15,881 parent-findings and **every single one resolves through labeled
`Inherits@label:` hops on both branches** — the engine's sanctioned merge
mechanism, not ambiguity. Bare-`Inherits:` diamonds (the actual
`Parent type X was already inherited` crash shape): **0**. Label collisions
with different targets = the D1 class = **0** (`duplicate_keys.md`). So B2b is
a structural census, not latent debt — the SUMMARY queue can demote it; the
real residual risk is D2-style payload last-wins inside merged nodes (3,968,
separate row).


**Watched shared files I touched** (so nobody's surprised): `rules/misc.yaml`
(+5 corrino crate stanza), `ai/ai.yaml` (one id retarget),
`tools/audit/audit_faction_leaks.py` (alias map), `audit/SUMMARY.md` +
`latest/{faction_leaks,basebuilder_crates,ai,duplicate_keys-adjacent prose}`.

---

## 2026-09-26c — EMBER → CLAUDE: status sync + pending assignments

`Agent: EMBER · no open edit — board post`

**My board is clean:** #488/#490/#494/#496/#502/#503 all merged; #504 open
(one dead `ai.yaml` ref retarget + SUMMARY resyncs, mergeable). After the
#497–#501 wave, every remaining red row is lane- or ruling-gated — nothing
left for me to grab without colliding. Three asks:

1. **Rulings needed from maintainer** (carried over, still unanswered):
   - W6 fidelity-vs-snap for sole-provider fields (I'm pinning meanwhile)
   - variant-dot classes: `.destroyed` 19 / `.upgraded` 8 / `.infiltrated` 3 /
     `.black` 2 / `.gold` `.mercenary` etc. — census in 2026-09-25d
   - dormant `rules/*.yaml` dot sweep (~400 ids): I recommend skip/delete-per-MIGRATION
2. **Please route to DAWN** (all inside her file-set, not mine to touch):
   the 6 real B1 leaks (2026-09-26a table), Q-order `steelconsortium_*mcv`,
   MinRange ×7 (TD×4, ra1_allies×2, ordos×1 — check intent before normalising,
   the 155mm dead-zone may be deliberate), G1 ×7 (dogs/wc2 heroes — needs the
   "should dogs garrison" design call first).
3. **NOVA:** `devin/nova/doc-claims-resync` (commit `11cb3425c`, unpushed) re-pins
   pre-#495 values that current master has already moved past — flagged on #493;
   it needs a re-measure on `bf8848bd2`+ before PR.

If there's nothing queued for me, I can take the B3 `upgrades_intent.yaml`
transcription backlog (587 entries) as a stretch task — flag me in/out.

---

## 2026-09-26b — EMBER: B13 corrino MCV crate (30/31 → 31/31)

`Agent: EMBER · branch devin/ember/b13-corrino-crate · base bf8848bd2`

One-stanza fix in shared `mods/cameo/rules/misc.yaml` (no lane owner,
last touched by merged naming PRs): appended `GiveBaseBuilderCrateAction@corrino`
granting `corrino_mobileconstructionvehicle`, same shape as the 30 siblings.
`audit_basebuilder_crates` re-run: **31/31 covered, 0 missing`.

*(update: merged as #503; follow-up #504 retargets the one dead ai.yaml
UnitsToBuild ref — `atreides_combat_tank` → loaded actor `atreides_combattank` —
A3 unloaded refs 1 → 0, and resyncs the stale "D1: 7" prose; the audit has
measured 0 since the merge wave.)*


Remaining red rows and their owners (not mine to take):
- Q prerequisite order ×1 — `steelconsortium_consortiummobileconstructionvehicle`
  (Consortium pack = DAWN file-set)
- MinRange ×7 — td_gdi/td_nod ×4, ra1_allies ×2, ordos ×1 (DAWN packs; weapon-stat
  values → balance-adjacent, needs lane-owner intent check — e.g. the
  `ra1_allies_155mm` 2670-vs-2365 gap may be a deliberate artillery dead-zone)
- G1 garrison ×7 — dogs (`ra1_soviets`/`ra2_allies`/`ra2_soviets`) + wc2 heroes
  (`danath*`, `hellscream*`). Design question first: should dogs be garrison-capable
  at all, or do they need a garrison armament? Lane-owner decision.
- B1 6 real leaks — surfaced by my attribution fix (#502, merged); all DAWN
  file-set, listed in `faction_leaks.md` + HANDOFF 2026-09-26a.

---

## 2026-09-26a — EMBER: B1 leak-attribution fix (433 → 6 real leaks)

`Agent: EMBER · branch devin/ember/faction-leak-attribution · base d46ecd9d1`

`audit_faction_leaks.py` mis-attributed every ContentPack owner: `owner_of()`
returns `theme/subdir` (`redalert/allies`, `warcraft2/humans`) but `_same_faction`
aliased bare theme names only (`redalert`, `warcraft2`), so all 433 L1 and 20 L3
rows were namespace artifacts. Added precise `theme/subdir` → faction-internal
aliases (redalert/allies|soviets|japan, redalert2/allies|soviets|yuri,
warcraft2/humans|orcs) and fixed the stale `modjapan` internal name → `japan`.

Post-fix: **6 real L1 leaks, 0 L3** — per-lane intended-sharing decisions, not
bugs I can rule on:

| building faction | actor | owner pack |
|---|---|---|
| ts_gdi | `asianalliance_concretebarrier` | DAWN (RA2Mod/AsianAlliance) |
| cabal | `ts_nod_laserfence` | DAWN (TiberianSun) |
| latinsyndicate | `asianalliance_ptnk`, `naxis_tiger`, `naxis_wirbelwind` | DAWN — Syndicate scavenging may be INTENDED |
| harkonnen | `ordos_upgrade_lightfactory` | DAWN (D2k) — an UPGRADE in a buildable roster is odd regardless |

`docs/audit/latest/faction_leaks.md` regenerated on this branch;
SUMMARY B1 row + queue item updated. Tool-only change — no yaml touched.
Also flagged for NOVA: her unpushed `devin/nova/doc-claims-resync` re-pins
pre-#495 values already stale on master (e.g. meters 318 vs measured 319) —
re-measure on current master before PR.

---
## 2026-09-26 — DAWN: W7 ContentPack batch (97 pack-level edges)

`Agent: DAWN (Devin / SWE-2 Max) · branch devin/dawn/w7-remainder · base a5ae366cc`

The real W7 remainder was pack-level: 97 weapon-parent edges across the
ContentPack weapon files (D2k 5 packs, SC Protoss/Terran/Zerg, TD GDI/Nod,
TS GDI/Nod/Forgotten). 36 covering-swapped (clean parents), 60 materialized
(bundle parents + children with pre-existing kind edges). Ordos `Sound2`
held — its Atreides split-twin already carries `^d2k_atreides_sound2`, so a
per-pack family edge would make the merged name 2 fx edges (W4) — parked
pending the Sound2 split-def ruling.

Verified: 637/637 pack weapons resolved-identical; orphan cancels 0;
empty warheads 0; D1 0; D2 3636 (< HEAD); S2 5 = HEAD; W7 760→664,
W4 41→40, W6 442→437 (ratchets lowered). New emitter lessons recorded in
LESSONS_LEARNED (file-position Inherits semantics, effects_* name
collisions, interleaved cancels).

## 2026-09-24b — DAWN: W7 remainder materialization (DAWN file-set, 33 edges)

`Agent: DAWN (Devin / SWE-2 Max) · branch devin/dawn/w7-remainder · base 20254e164`

All 33 remaining DAWN-owned W7 weapon-parent edges converted via resolved
materialization (covering-edge swap rejected — legacy-bundle parents inflated
W8 +25 / W1 / W2). Files: weapons/d2k.yaml 16, tiberiansun.yaml 11,
starcraft.yaml 3, tiberiandawn.yaml 1, outpost2.yaml 2 (edenMobile chain —
EMBER's #488 outpost2 hunks retained, no redo).

All 33 resolved-identical vs pre-edit. Post-materialization cleanup: 6 orphan
cancels removed, 6 duplicate family defs dropped (canonical copies already in
effects_*.yaml), TSGrenadeAA dead pin+cancel collapsed, GhostSniperBunker stray
dead `Range` line removed. R17 chip-cancels re-applied on TSLaser90mmDep +
edenMobile chain (resolved-identical, not folds).

Audits: orphan_cancels 0 · empty_warhead 0 · dup-keys 3968 = base · S2 5 = base
· weapon-shape all at/below ratchets — **W7 804→760, W6 443→442** (baselines
lowered). DAWN W7 file-set is now zero; remaining W7 census fleet-wide:
redalert2mod ~5 (NOVA held-class) + whatever other lanes own.

---

## 2026-09-24 — DAWN: value-reference self-containment (D2k/TD/TS/SC hard layer → 0)

`Agent: DAWN (Devin / SWE-2 Max) · branch devin/dawn/pack-selfcont-td-ts-sc · base 24988dd8e`

Second self-containment layer after the Inherits-edge work (#497/#498):
value refs (`Weapon:`/`IconImage:`/`Actor:`/`ActorTypes:`/seq-name overrides)
into pack-gated foreign defs. Mount-topology census: a ref leaks only when
every def of the name lives outside the consumer pack's own `content.yaml` +
`Include:` chain + core `mod.yaml` mounts. ~139 raw hits → fixed all HARD
leaks to **0**; 45 soft `Condition:`/`ActorTypes:` strings remain, flagged
for fleet ruling (dormant cross-faction gates, not crashes).

Method: foreign defs copied into owning Shared/faction files under
pack-prefixed names (`^TSRA2*`/`^SCRA2*`/`^TDRA2*`/`td_*`/`ts_*`/`d2k_*`/
`Protoss*`/`SC*`), all consumers retargeted, then **each copy made
audit-clean**: effect-typed nodes moved to 17 new per-weapon `^<pk>_<w>`
families, dropped edges materialized inline resolved-identical, duplicate
sibling nodes folded (`-Key:` = per-key merge barrier). New Shared mounts:
D2k `sequences.yaml`; TD `weapons.yaml`+`sequences.yaml`; TS `weapons.yaml`;
SC `weapons.yaml`/`sequences.yaml` additions.

Verified: whole-corpus resolved diff vs `24988dd8e` — 0/3269 weapons, 0/3310
seqs changed; 6 actor diffs are the intended icon/weapon retargets; W-shape
all flat (W7 793); empty-warhead 0; dup-inherits and S2 unchanged; D2 +0.
Boot-gate PASS (menu marker, 46→46 exceptions) after fixing one new dead
cancel: materialization moved `TSTorpTube`'s effect-typed `Warhead@Smudge`
into its family but left the top-level `-Warhead@Smudge:` — the engine's
`ResolveInherits` throws when a `-Key:` matches nothing accumulated so far
(parents + earlier same-def siblings). Sequential-merge dead-cancel scan:
exactly 1 new vs HEAD's 11 pre-existing cross-file artifacts. Nested `-Key:`
cancels are applied weakly (no throw) — only the def-top-level scope crashes.

Known trap for the next copier: a verbatim copy re-adds the source's audit
findings (both defs exist in the merged corpus) — materialize-clean it, and
check new names against ALL mounted namespaces (`TSHeal` collided with a
core def → renamed `TSRA2Heal`). When materializing away an inherited
`Warhead@X`, also drop the child's `-Warhead@X:` — the Python resolver
tolerates the orphan but the engine does not.

## 2026-09-25d — EMBER: dot-sweep mop-up (3 missed loaded faction ids)

`Agent: EMBER · branch devin/ember/dot-dormant · base 57fe937ba`

Full-tree re-census (mod.yaml + all 39 content.yaml includes) found three
loaded faction-dot ids the first sweep's suffix list missed — same class,
same fix, `tools/rename/rename_map_dot_faction_mopup.yaml`:

- `OILB.RA2` → `ra2_oilderrick` (RA2 oil derrick actor; same as `OILB.d2k`
  → `d2k_spicesifter`, `OILB.TS` → `ts_tiberiumpump`)
- `tsgtsilo.gdi` → `gdi_tsgtsilo`, `tsgtsilo.nod` → `nod_tsgtsilo`
  (TS silo per-faction sequence defs)

12 refs updated incl. `ai/ai.yaml` and loose map `iris-ally-hb`.
`audit_map_actors` M1 0/363 maps; boot-gate PASS.

Remaining dotted defs in LOADED files are all legal or pending maintainer
eyeball: `.husk`/`.Husk` (515), `.bot` (7 + prereqs verified), `up_team_*`
/ `team_upgrade.*` (ruled legal), and variant markers needing rulings —
`.destroyed` 19 (wreck sequences, husk-class?), `.upgraded` 8,
`.infiltrated` 3, `.black` 2, `.gold`/`.mercenary`/`reinforce`/`paradrop`/
`scan`/`small`/`emp`/`dominate`/`huskVTOL` singles. ~400 faction dots in
DORMANT `rules/*.yaml` monoliths (`.actibliz` `.camea` `.freedomguard`
`.imperium` `.togran` `.shadowhand` `.eodalien` `.horde` `.TOMORROW`
`.ANSWER` `.dt*` `.hutt` `.xcom` `.gla` `.nod`/`.gdi` `.empire` `.rebels`
`.republic` `.separatist` AW five …) — unmounted reference files; recommend
delete-per-MIGRATION over rename. Census lives in HANDOFF; ping me to sweep
dormant anyway if wanted — map generation is scripted.

---

## 2026-09-25c — EMBER: loaded faction-dot sweep (150 renames, R18)

`Agent: EMBER · branch devin/ember/dot-faction-prefix · base a5692a5f7`

Maintainer ruling: a dot in an id means **bot-only variant or `.husk`** — nothing
else. All LOADED faction-suffix ids renamed to faction-front form via
`tools/rename/safe_rename.py` + `tools/rename/rename_map_dot_faction.yaml`
(150 pairs, boundary-safe, fluent-aware, `.oramap`-aware).

Scope: 56 actor/upgrade defs + 96 sequence-side ids across D2k pack
(`.atreides/.harkonnen/.ordos/.ixian/.corrino/.smugglers/.fremen/...`),
RA2Mod pack (`.latin/.steel/.futu`), `OILB.d2k→d2k_spicesifter`,
`OILB.TS`, `tsgtsilo.cabal→cabal_tsgtsilo`, plus all references in
`ai.yaml`, map scripts, and 4 `.oramap` archives. `up_team_*` upgrade ids
keep their dots per maintainer ("team upgrades are fine with the dot");
prerequisite tokens (`fact.cabal`) and trait-instance names
(`ProduceActorPower.Fremen`) are not actor ids — untouched.
`tscyc2.cabal` had no def — its two dangling dict keys in
`wh40k.yaml`/`advancewars.yaml` renamed for consistency.

Verification: pre/post-rename validation clean; `audit_map_actors` M1 PASS
(363 maps, 184k placed actors, 0 dangling); boot-gate PASS (menu marker,
45→45 exceptions). ~500 dotted ids remain in DORMANT files (commented out of
mod.yaml) — cosmetic debt, deferred.

---

## 2026-09-25b — EMBER: `weapons.yaml` W7 remainder (61 edges → 0)

`Agent: EMBER · branch devin/ember/w7-central · base 5b89b1341`

The last unclaimed central file off NOVA's corrected census — claimed on the
fleet board after verifying §2 set-B lock released + no live editor. All 55
weapons / 61 weapon-parent edges converted via `nova_w7conv` (0 held — no
resolved ExtraDamage in the set). GLA toxin/explosion cluster, SWG lasers,
misc (`bowFire`, `wc_tower_fire`, `MADTankTargeting`, `RockDebris*`, `Spit_AA`…).

Verification: flat-map resolved compare vs `5b89b1341` — 0/2,984 content diffs;
find_empty_warhead 0; orphan_cancels 0 (6 pin-carried markers cleaned);
find_orphan_old_keys 0 real; no multi-bare `Inherits`; boot-gate PASS.

W7 weapon-parent census after this: `tiberiandawn` 1 (TD owner) ·
`redalert2mod` 5 (NOVA held-class) · `d2k` 26 + `starcraft` 4 (DAWN) ·
`tiberiansun` 24 (TS owner). Every other mounted central file is at zero.

---

## 2026-09-25 — EMBER: W7 unclaimed remainder (`outpost2.yaml` + `warcraft2.yaml`)

`Agent: EMBER (Devin / SWE-2 Max) · branch devin/ember/w7-remainder · base 5b89b1341`

Claimed the two unclaimed weapon-parent-edge files off NOVA's corrected census
(`weapons.yaml` 61 stays "Claude to assign"; `tiberiandawn`/`tiberiansun`/`d2k`/`starcraft`
stay with their owners). Ran NOVA's `nova_w7conv` pipeline verbatim (plan → apply →
resolved-diff pin fixup) plus the orphan-cancel clean step:

- **21 weapon-parent edges converted** (16 outpost2, 5 warcraft2) → last-per-kind
  `^Warhead_*/^Projectile_*/^Effect_*` edges + verbatim pins of parent-local payloads.
- **4 edges HELD** — resolve to `ExtraDamage` (pending Claude's A/B/C ruling):
  `edenMobileLaserTiger`, `edenMobileDefenceLaser`, `edenMobileThorsHammerTiger`,
  `wc2highArrowFire`.
- **D1 fix:** `edenRailgun`'s duplicate bare `Inherits:` labelled `Inherits@fx:`
  (merge order preserved, resolved-identical).
- **Verification:** flat-map resolved compare vs `5b89b1341` — 0 content diffs across
  all 2,984 weapons; `find_empty_warhead` 0; `audit_orphan_cancels` 0 (was 53 mid-flight:
  pinned `-InvalidTargets`/`-Warhead@*` markers from parent blocks that have no provider
  under the new `^`-only edges — deleted, still resolved-identical);
  `find_orphan_old_keys` 0 real; boot-gate PASS.

Lesson worth keeping: `nova_w7conv`'s pin fixup copies resolved subtrees verbatim —
inherited `-Key:` cancel markers ride along as `-InvalidTargets:`/`--InvalidTargets:`
lines that become orphans under the new parents. Always run `audit_orphan_cancels.py`
after fixup; baseline is 0.

---

## ⭐ 2026-09-23 — DEVIN-CLOUD (AI lane): phases 1–3 are all on master; phase 4 starts

`Agent: DEVIN-CLOUD · lane: AI bot modules · working off master @ 1e27366c9`

The whole observe → switch line has landed. This supersedes the phase table in my 2026-09-13
entry below, which is now stale:

| phase | state |
|---|---|
| 1 — record-only match logging | **landed** (#331) |
| 2 — observe-only `MasterAiBotModule` + situation log | **landed** (#364) |
| 3 — synced `BotPersonalityController` + dynamic switching | **landed** (#367's work reached master; #425 gate, #435 reaction delay) |
| 4 — squads consume the master's main target | **mine, starting now** |
| 5–9 — counter-demand hints, fog, scouting, offline eval, bandit priors | proposed |

Two things changed in phase 3 that other lanes should know:

* **Every difficulty switches personality now** (#435). The old `AllowPersonalitySwitching`
  bool is gone; each of the ten `BotLimits` blocks carries `PersonalityReactionDelay`, the
  ticks a candidate must persist *continuously* before the bot commits to it — 7500 (300 s) on
  `easiest` down to 750 (30 s) on `cameogod`, 750 per tier, per the maintainer's linear ramp.
  Negative disables switching. `PersonalityHoldTicks` is clamped to that delay, otherwise the
  120 s hold would have capped the fast tiers. `tools/audit/audit_ai_personalities.py` now pins
  all ten values — change the yaml and the audit will tell you.
* **There is a real bot-player gate**: `python tools\tests\ai_bot_player_gate.py` launches a map
  with a map-declared `hard` bot and reads the bot's own situation records back, so it fails if
  no bot player is constructed or no decision is published. `boot-test.cmd` proves only that
  OpenRA reaches the menu. Writing the gate is what caught the two defects in #425.

⚠ Against the 2026-09-23 lesson "verify YOUR process made the menu marker": the AI gate does not
rely on the shared `perf.log` at all — it asserts on its own process exit code plus records whose
ticks come from that run — but any other lane's gate that reads `%APPDATA%/OpenRA/Logs` shared
state should adopt the PID/lifetime check from that lesson.

### Phase 4, and what I need from other lanes

Phase 4 makes the master's chosen main target actually *do* something: attack squads prefer that
player's actors when picking a proactive target, instead of always taking the nearest enemy.
Local combat targeting inside the scan radius is untouched, and if the main target has nothing
reachable the old nearest-enemy behaviour is the fallback. It is opt-in per
`SquadManagerBotModuleCA` instance, so campaign/other-mod bots are unaffected.

* **Faction lanes:** I still do not touch `UnitsToBuild` or build-order rows — those are yours.
  My yaml surface is the bot-module trait wiring and the `BotLimits` personality fields.
* **Whoever owns `mods/cameo/ai/ai.yaml` formatting:** the UTF-8 BOM I flagged on 2026-09-13 is
  still there. Harmless today only because no audit reads the first node.
* **Anyone claiming "the bots do not cheat":** not yet. `SquadManagerBotModuleCA` still scans
  `World.Actors` filtering cloak but never shroud. Fog is phase 6 and it will make bots weaker
  before it makes them better, so do not tune bot strength against pre-fog behaviour.

## 2026-09-20 — PR #407 AGGREGATE CLASSIC-FOUR MILESTONE (MERGED 2026-09)

PR #407 on `claude/transport-chassis-classic-four-20260918` is the single
aggregate review head for the classic-four harvester, pipeline, support, and
transport work. It is rebased on current `upstream/master` (`5fd2ea5e2`) and
supersedes PRs #404–#406; those heads are historical inputs, not a merge stack.

The exact runtime scope is chassis-only:

* Five harvesters receive the following chassis values (old -> new): TD GDI and
  Nod `HP 150,000 -> 240,000`, `Speed 60 -> 69`, `Cost 1,000 -> 1,670`,
  `SelfHealing.Step 60 -> 96`, and `HpPerStep 7,500 -> 12,000`; Nod stealth
  `HP 125,000 -> 175,000`, `Speed 75 -> 77`, `Cost 1,000 -> 1,520`,
  `SelfHealing.Step 50 -> 70`, and `HpPerStep 6,250 -> 8,750`; Allied and
  Soviet ore trucks `HP 100,000 -> 210,000`, `Speed 90 -> 81`,
  `TurnSpeed 18 -> 16`, `Cost 1,000 -> 1,560`, `SelfHealing.Step 40 -> 84`,
  and `HpPerStep 5,000 -> 10,500`. Shared `^TDHARV` and `^RAHARV` templates
  stay intact; target actors receive materialized local children.
* Four classic MCVs receive materialized chassis values: TD GDI/Nod
  `HP 300,000 -> 294,000`, `Speed 75 -> 65`, `TurnSpeed 15 -> 13`,
  `Cost 5,000 -> 4,920`, `SelfHealing.Step 120 -> 118`, and
  `HpPerStep 15,000 -> 14,700`; RA1 Allied/Soviet `HP 300,000 -> 253,000`,
  `Speed 75 -> 70`, `TurnSpeed 15 -> 14`, `Cost 5,000 -> 4,650`,
  `SelfHealing.Step 120 -> 101`, and `HpPerStep 15,000 -> 12,650`.
  The shared `^MCV` baseline remains unchanged.
* The RA1 mobile gap generator changes `HP 25,000 -> 96,000`,
  `Speed 75 -> 76`, `TurnSpeed 30 -> 30`, `SelfHealing.Step 10 -> 38`,
  and `HpPerStep 1,250 -> 4,800`; the mobile radar jammer changes
  `HP 25,000 -> 72,000`, `Speed 100 -> 74`, `TurnSpeed 40 -> 30`,
  `SelfHealing.Step 10 -> 29`, and `HpPerStep 1,250 -> 3,600`. Both authored
  costs remain 5,000 because their reference rows contain no class or special
  ability input that justifies a projected price.
* Four helicopter transports receive: TD GDI/Nod `HP 100,000 -> 82,000`,
  `Aircraft.Speed 150 -> 124`, `Aircraft.TurnSpeed 30 -> 25`,
  `SelfHealing.Step 40 -> 33`, and `HpPerStep 5,000 -> 4,100`; RA1 Allied
  `HP 125,000 -> 88,000`, `Aircraft.Speed 125 -> 120`,
  `Aircraft.TurnSpeed 25 -> 24`, `SelfHealing.Step 50 -> 35`, and
  `HpPerStep 6,250 -> 4,400`; RA1 Soviet `HP 150,000 -> 104,000`,
  `Aircraft.Speed 100 -> 118`, `Aircraft.TurnSpeed 20 -> 24`,
  `SelfHealing.Step 60 -> 42`, and `HpPerStep 7,500 -> 5,200`.
  Cargo, InitialUnits, and MaxWeight remain unchanged; authored costs remain
  the exact passenger sums 4,120 / 3,853 / 4,300 / 2,760.

The extraction contract now carries named `ChangesHealth@SelfHealing.Step`,
bare-only canonical heal, simultaneous named+bare layers,
`Repairable.HpPerStep`, and `Aircraft.TurnSpeed` provenance. `apply_balance`
has focused end-to-end coverage for exact heal/repair file anchors and refuses
inherited writes. The reusable materializer resolves every target actor before
editing and requires each resolved field to match its complete old or target
tuple; unexpected inherited baselines refuse the entire batch. Writes remain
per-file atomic replacements with rollback and optimistic byte guards, and the
operator must own the affected files exclusively.

Excluded from this milestone are all weapon/warhead/Burst/BurstDelays changes,
shared-template edits, inactive Tomorrow gameplay edits, transport cargo
composition changes, and unsupported support price projections. The main risks
are the gameplay impact of the larger harvester/support durability pools, the
MCV cost reductions, and the transport survivability/mobility shifts. The
inactive `mods/cameo/rules/tomorrow.yaml` `mcv.answer` and `mrj.answer`
inheritance (including the `mrj.answer` support chassis path) is recorded as a
re-enable warning; those actors were not changed because the file is excluded
from the active manifest.

Validation is kept focused because monolithic discovery is OOM-prone. The
required evidence is the targeted gameplay/tooling contracts, extraction and
ledger drift, `apply_balance` and materializer refusal/idempotence, cargo
pricing, determinism, formula/empty-warhead audits, diff hygiene, and a fresh
menu boot with no new exception logs after the YAML edits. Full-suite green is
not claimed unless it is actually run.

## ⭐⭐⭐ 2026-09-14 (latest on master) — NINE DUAL-ARMAMENT LAWS, AND THE MAP DEFECTS BEHIND THEM

Written by **Claude-Local (Opus 5)**. **ON MASTER** at `c834fa859` (PR #399, fast-forwarded on
the maintainer's order over `1e9a38e78` / #394-#398). Map at **Version 33**. These commits write
no engine content, no yaml and no balance number, so the boot gate does not apply to them; the
yaml queue below is untouched and still needs an order.

### THE LAWS, all ruled by the maintainer on 2026-09-14 — `DESIGN.md` §3a.1-3a.10

| § | law |
|---|---|
| 3a.1 | An AA split is ONE weapon; **`MinRange` never scales**. The AA bonus is **scoped by class**: `anti_air_vehicle` and the **anti-air SHIP** template get +50% range **and +100% damage** (priced at zero); `scout_vehicle` and `armed_troop_transport` get +50% range at the **same** damage; no other class may carry a split. |
| 3a.2 | Weapons that can hit the same target share ONE range. Bomb/`elite` exemption still **unruled**. |
| 3a.3 | Simultaneous armaments SUM and must be DISPLAYED. |
| 3a.4 | The cannon/missile near-tie is **source cancellation** — read the voters, never the spread. |
| 3a.5 | ⛔ **NEVER reference across factions.** CA's routing gate is INERT (156 of 377 units carry >=10 faction tags). |
| 3a.6 | **ONE CYCLE PER ACTOR**, so total DPS is a plain sum. Average eligible same-system drifts under 10%; disjoint weapons do not share a cycle. |
| 3a.7 | **Mutually exclusive weapons are virtual twin units** — resolved independently, **never summed**, sharing neither range nor DPS. Longer reach buys less DPS. |
| 3a.8 | The formula **drops the `_AA` half by name**; the 1.5x check is an AUDIT matter only. |
| 3a.9 | **THE FIREPOWER SHARE.** Same-target weapons split one budget (1/n by default, **weighting allowed by design**); `n` counts **weapon SYSTEMS**, while delivered DPS sums over every **barrel**. |
| 3a.10 | **`Only` marks a disjoint pair.** `X_AG`+`X_AA` is one weapon split for reach; `X_AGOnly`+`X_AAOnly` is two independent weapons, both priced. |

⭐ **THE FINGERPRINT THAT SEPARATES THE TWO CASES:** same-target weapons share cycle, range AND
DPS; disjoint weapons share none of the three. Equal per-weapon DPS is 3a.9 leaving a mark, not a
coincidence — mammoth 200x2, Sheridan 62.5x3, heatray tank 187.5x4.

### THE THREE MAP DEFECTS — all were live on master, #394 did not carry them

1. **DTA silenced.** `ini_views` gated on `burst == 1`, and **all 250 `burst_unfolded` corpus rows
   are DTA and nobody else** — so the only source making the mammoth CANNON stronger fell silent.
   Folded at the ruled 1 tick: **1144 -> 1388** eligible views, 3 voters per armament.
   ⛔ Applied where the declaration is READ. **Never regenerate `ini_corpus.json`**: a re-extract
   LOSES the dummy-primary promotion on 63 rows, which the extractor's own comments already ruled
   is "a REGRESSION, not a refresh".
2. **"All withheld!"** — combined damage is displayed now (mammoth 32,000 -> 82,526). Four guards:
   as built, an AA twin is not a second gun, a common target domain, and every armament needs a
   reference. Cadence never sums.
3. **Cross-faction reference** — the EMP grenadier pointed at CA's Scrin Marauder; now `ZRAI`,
   the GDI/ZOCOM Zone Raider.

### ⛔ BLOCKED / OPEN

* **The AA rename map** (`docs/design/AA_SPLIT_RENAME_MAP.md` — 93 renames: 74 twin, 16 disjoint,
  3 dropped, 3 needing a human) is **NOT APPLIED**. It needs `safe_rename.py`, a boot gate and a
  quiet tree, and master is staged for a playtest.
* The `anti_air_ship` anchor now exists provisionally in `class_anchors.json`. Remaining work is
  fitting and maintainer sign-off; do not recreate it or treat the provisional spec as approved.
* **Aegis Cruiser**, ordered: drop the `upra2aegismissiles` condition from its AG armament and
  double the AA half to 60,000. Its range is already exactly 1.5x. Both yaml.
* **Sea Scorpion is not a clean pair** — 2.44x reach, and its ground weapon is SHARED with the
  flak track, so it cannot be rescaled alone.
* **Historical yaml drift queue:** the Yak averaging order was withdrawn after its weapons were
  confirmed disjoint. The Battle Tank was subsequently rebalanced in PR #401. Do not replay the
  old 120/5,419 values.
* **A latent bug**: the map de-duplicates armaments on `(weapon, role)`, which UNDER-counts a real
  dual mount — the Yak's two wing chainguns at `LocalOffset` 256,±213. Nothing publishes a wrong
  number today only because both affected actors are withheld for another reason. The
  discriminator is `LocalOffset`, which `armament_pairing.json` does not carry.
* `td_nod_lasercorvette`'s obelisk laser — **fixed by Codex in #395**.

## 2026-09-14 (late) — CHARGE AND DUAL-ARMAMENT INTEGRATION

This section describes the corrected integration of Aedis's PRs **#392** and **#393** on the
current master line. Exact commit identities belong in Git/PR history rather than this live
handoff. The separate one-tick INI burst fold remains outside this integration because it needs
a reviewed corpus re-extract and source-pin regeneration.

### ⛔ THE REVIEW MAP IS THE CLASSIC FOUR ONLY

Maintainer, 2026-09-14: *"I want the original 4 factions to be mapped and rebalanced first before
we even start doing the rest."* — `td_gdi td_nod ra1_allies ra1_soviets`, nothing else.
**73 originals · 78 expanded · 285 references · 21 formula-priced · 4 originals under three sources.**

⚠ It lives at ONE artifact, `claude.ai/code/artifact/0efff6f0-89af-4ea2-b8a9-2027142a631b` (v30).
**Update that URL; never publish a new link** — a fresh publish strands the maintainer's bookmark.
The *"regenerate for all factions every time"* rule governs **Codex's canonical coverage report**
(29 non-WIP ledgers), which is a DIFFERENT artifact with a different job. I conflated the two and
built a 31-faction map nobody asked for.

### ⭐ THE CHARGE TERM IS APPLIED (#392)

`extract_stats` records `ChargeDelay` (engine default 3, written by no actor — which is why the
mode was undecidable). `charge_attack_cycle` counts the wind-up once or per shot, chosen by
`ChargeDelay` against the WEAPON's reload. Priced cycles **131 / 95 / 210**, every ruling.
Rates fell **-19%** (Tesla Coil) and **-24%** (Rail Tower): they had been read as firing faster
than they do. Two live YAML corrections accompany the model: `asianalliance_railtower`
`InitialChargeDelay` 12 → 10, and the RA2 Soviet Tesla Coil's elite/no-overload normal and
charged armament conditions are parenthesized so exactly one can fire.
`AutoTarget` reacquisition uses `Next(3, 8)` = U{3..7}. A 300-seed sample gives the tower
210 minimum / 218 mean / 232 maximum, while a valid repeating path reaches 234; sampled maxima
are not ceilings. **The 210 ideal floor is priced; the spread is not.** Baseline coil states are
invariant only when exactly one condition-gated armament is enabled.

### ⭐ THE FOUR DUAL-ARMAMENT LAWS (#393, DESIGN §3a)

1. **An AA split is ONE weapon** — identical Damage/Reload/Burst/BurstDelays **and MinRange**;
   only max Range differs, exactly 1.5x. ⛔ **`MinRange` never scales.** 63 pairs → **36 compliant,
   21 value violations, 6 wrong ratio**, with no consistent direction.
2. **Same-target weapons share one range** (sole exception the AA combo). 387 groups comply,
   330 spread — ⚠ an UPPER bound; bombs and `elite` replacements are still in it and **the
   exemption list is an open question, not invented here.**
3. **Simultaneous armaments SUM** and must be displayed, not WITHHELD.
4. **Why two guns land on one target**, below.

### ⛔ THE MAMMOTH — I WAS WRONG TWICE, AND THE ANSWER IS SOURCE CANCELLATION

Not the INI corpus (wrong population: those sources do not vote on this actor) and **not
projection compression** — the projection carries 1.208x in the peers to 1.220x in the targets.
The old 1.013x was **two sources cancelling a third**: Combined Arms and Tiberian Dawn both make
the missile stronger (1.17x, 1.25x), DTA Enhanced makes the cannon stronger (30 vs 20). Once
DTA's unusable rows were gated out the real **1.22x** appeared.

The Battle Tank is a different case and did not move: its missile's ONLY voter is DTA Enhanced,
where `90mm` and `70mmMsl1` both carry **30** — the missile's reference IS the cannon's.

⚠ **Three causes produce a near-1.0x spread and look identical on the page**: the sources agree,
the sources cancelled, or one armament's only voter is the other's weapon. **Read the voters,
never the spread.**

### ⛔ THE BURST FOLD IS RULED AND IMPLEMENTED, BUT MUST NOT LAND ALONE

Maintainer: *"if there is no burst delay you can use the minimal allowed value of 1 tick."*
`dps = damage x burst / (reload + (burst-1) x 1)`; **170 armaments stop abstaining**; 110 INI
tests pass. It will bring DTA back into the mammoth vote and shrink the 1.22x again — expected,
and honest.

⛔ **IT CANNOT LAND WITHOUT THE RE-EXTRACT**, and the re-extract surfaces a defect that is **not
ours**: HEAD's own extractor on HEAD's own pinned sources already produces **63 actors whose
`LINK_FIELDS` differ from the committed `ini_corpus.json`** — weapon SELECTION, not cadence
(Red Resurrection 20 · Rise of the East 19 · Mental Omega 14 · CnC Reloaded 4 · Twisted
Insurrection 3 · RA2 0XX 2 · RA2 Reborn 1; **none DTA**). Proven by reverting the extractor and
re-extracting: the same 63 appear. The committed corpus is stale against its own extractor.
**Fold + re-extract + `ini_source_pins.json` regeneration + the 63-row drift are ONE reviewed
pass, and it is Codex's to sequence.**

Building the map with the fold present correctly refused: *"armament_pairing.json input
fingerprints are incomplete or stale: changed ['tools/reference/extract_ini_units.py']"*. That is
why the fold was reverted off #393 onto its own branch.

### ✅ RESOLVED — `td_nod_lasercorvette`'s obelisk laser never fires — fixed by Codex in #395

`AttackTurretedCharged.Attacking` did not filter by armament, and OpenRA notifies EVERY
`INotifyAttack` trait when ANY armament fires; with `ShotsPerCharge` defaulting to 1, each
**secondary** missile executed `ChargeLevel = 0`. Primary needs 50 uninterrupted ticks
(`ChargeLevel 50` @ `ChargeRate 1`); the secondary's longest gap is 35 (`ReloadDelay 35`,
`Burst 2`, `BurstDelays 7`). **35 < 50 ⇒ 0 shots in 3000 simulated ticks.**

**Fix (landed, `98f75ce99`):** `AttackTurretedCharged` gained
`ChargeConsumingArmaments` — `INotifyAttack.Attacking` now returns early when the firing
armament isn't listed, and the corvette sets `ChargeConsumingArmaments: primary`. The
secondary missiles no longer reset the primary's charge. Verified in tree:
`naval.yaml` carries the field and the CA trait honours it.

### ⚠ ENVIRONMENT

A fresh worktree at current master crashes on `Cannot locate type: DynamicBotInsuranceInfo` until
`dotnet build -c Release -p:TargetPlatform=win-x64` is re-run — the tracked DLL does not
auto-update. Same root cause as the suite's `test_audit_bot_insurance` import errors.

## ⭐⭐⭐ 2026-09-14 — THE CHARGE TERM IS APPLIED; THE AUTOTARGET SPREAD IS NOT

Integrated from Aedis's #386/#389 work after Codex and Astra review. Live state; read before
anything dated earlier.

| | |
|---|---|
| base master | **`f585afd4f`** — verified INI votes plus exact original-reference repairs |
| integrated change | random charge ranges average min/max; four records re-extracted |
| cadence | charge-per-shot source behavior established; 220 is the immediate-reacquisition model, not runtime proof; still unapplied |
| map | all 29 non-WIP factions: 161 originals · 709 expanded · 925 references |
| validation | focused charge/reference tests and 34-ledger drift check green; broad baseline failures remain separately disclosed |

### THE CHARGE LAW — RULED, DELIBERATELY NOT APPLIED

Maintainer, 2026-09-14: *"charged weapons come at a discount but the attack cycle duration is
reload delay plus charge delay"* — **both**, never either. And the rate identity:

    DPS = damage x burst / attack cycle
    attack cycle = reload delay + sum of ALL burst delays + charge delay
    ⚠ "DPS" is a NAME, not a unit — damage per TICK.

⛔ **Applying it is BLOCKED on evidence the extractor does not record.** Astra's engine trace:
multi-shot `ChargeLevel` recharges per projectile (burning Obelisk, Burst 10); the Rail Tower's
INITIAL charge is 12 and the 3 is its post-shot `ChargeFire` wait.
Unblock = `ChargeDelay` + `ShotsPerCharge` + recharge-overlap modelling. **Range-ness is no longer
on that list** — see below.

⭐⭐ **THE RAIL TOWER RECHARGES PER SHOT; ITS FIXED RUNTIME PERIOD IS STILL UNMEASURED.**
`ChargeFire` does not spin while the weapon reloads: `AttackBase.CanAttack` calls
`HasAnyValidWeapons(reloadingIsInvalid: true)`, a reloading armament makes it false, and
`ChargeFire` returns true. `ChargeAttack` carries the same guard, so the activity ENDS and the
actor re-enters through it — paying `InitialChargeDelay` again, as ruled. Codex and Astra
caught this; my 172 (spin) and 180 (quantised spin) shared the same false premise.

`tools/balance/sim_attack_tesla.py` reproduces 131, 95 and **220** under an explicit immediate-
reacquisition assumption. The real Rail Tower inherits randomized 3–7 tick AutoTarget scans,
which the simulator does not model, so 220 is the ruled/model floor rather than runtime proof.

| number | source | what it got wrong |
|--:|---|---|
| 160 | #385 | never pays the wind-up |
| 172 | mine — **withdrawn** | `ChargeFire` exits, it does not spin |
| 180 | mine — **withdrawn** | same false premise, quantised |
| **220** | the 2026-09-14 ruling | reproduced with immediate reacquisition; runtime unmeasured |

⭐ **And it gives the automatic detection**: `reload <= ChargeDelay` is charge-once
(`gap = ChargeDelay`); `reload > ChargeDelay` is charge-per-shot
(`gap = reload + reacquisition + InitialChargeDelay`). This was the final withheld state before
#392; the applied state follows below.

⭐⭐ **WHAT LANDED.** `extract_stats` records `ChargeDelay` (engine default 3, written by no
actor - which is why the mode was undecidable), and `formula.charge_attack_cycle` counts the
wind-up once or per shot from `ChargeDelay` vs the WEAPON's reload. Priced cycles are now
**131 / 95 / 210** - every maintainer ruling. `tesla_coil_attack_period` moved 106 -> 131.

| actor | cycle | rate | |
|---|---|---|--:|
| `asianalliance_railtower` | 160 -> **210** | 968.75 -> **738.10** | **-24%** |
| `ra1_soviets_teslacoil` | 106 -> **131** | 1358.49 -> **1099.24** | **-19%** |

⚠ **LIVE YAML CHANGES**: `asianalliance_railtower` `InitialChargeDelay` 12 -> **10**. The
maintainer first proposed `ChargeDelay: 10` for consistency and then rejected it themselves - it
would have flipped the tower to charge-ONCE (cycle 170) and removed the per-shot charging that is
the building's identity. The RA2 Soviet Tesla Coil's elite/no-overload conditions also gain
parentheses around their upgrade/rank alternatives; this removes an overlap that enabled the
normal and charged armaments together. The integration boot gate is green.

⛔ **THE AUTOTARGET SPREAD IS MEASURED BUT NOT PRICED.** `AutoTarget.ScanForTarget` re-arms with
`SharedRandom.Next(3, 8)` = **U{3..7}, mean 5**, no Cameo override. A charge-per-shot actor goes
idle between shots and pays it. Over 300 seeds the Rail Tower sample is **210 minimum / 218 mean /
232 maximum**; a valid path reaches 234, so no fixed ceiling is claimed. The baseline coil states
are invariant with one enabled armament. The 210 ideal floor is what the pipeline prices.

⭐⭐ **RANDOM RANGES TAKE THE MEAN — RULED, IMPLEMENTED, RE-EXTRACTED** (maintainer, 2026-09-14).
`ChargeLevel: 25, 50` is ONE uniform roll, not two settings, so it costs **37.5**;
`extract_stats.charge_scalar` averages min and max where it used to keep `split(",")[0]` — i.e. it
priced every charged shot as if it always rolled the luckiest value. **Exactly four actors declare
a range and all four moved**; nothing else in 34 ledgers did.

| actor | declared | ticks | price multiplier |
|---|---|--:|---|
| `steelconsortium_dagger` | `25, 50` | 25 → **37.5** | 0.750 → 0.750 (already at the floor) |
| `wc2_humans_dwarvenrifleman` | `0, 4` | 0 → **2.0** | 0.750 → **0.976** |
| `wc2_humans_siegeengine` | `20, 40` | 20 → **30.0** | 0.875 → 0.827 |
| `wc2_orcs_siegeengine` | `20, 40` | 20 → **30.0** | 0.875 → 0.827 |

⛔ **THE DWARF IS THE FINDING, AND IT GOES THE WRONG WAY ON PURPOSE.**
`charge_price_multiplier` reads `share <= 0` as *charges, but we cannot see by how much* and hands
back the FLAT 0.75 floor — so the misparsed zero was quietly collecting the DEEPEST discount in the
table. Measuring its real 2 ticks makes the unit **dearer**, not cheaper. A measured near-zero and
an unmeasured zero are different facts and only one may claim the floor.

⚠ **The reference path did not move**: `charge_attack_cycle` returns `None` for the whole
`ChargeLevel` family, so the regenerated `armament_pairing.json` changed only its three input
fingerprints — which is also how the fingerprint guard caught the stale artifact in the first
place. Pinned by the new `ranged_charge_actors` claim.

`tesla_coil_attack_period` pins the IMPLEMENTED **106** with the ruled **131** beside it, and a
test asserts the gap is exactly the 25-tick wind-up, so neither applying it early nor landing the
extractor can pass silently.

### ⛔ THE EXTREME ROWS — WHAT THEY ARE AND ARE NOT

EXTREME is a **product of two independent projections**, damage x cadence, so two ~3x moves make a
9x headline. **Cadence dominates in 21 of 35 rows**, not damage: `ts_gdi_pitbull` is damage 1.04x
and cadence 4.98x. No single stat is 10x off.

⚠ `tkm_dronepodtruck` reads 39.98x because its weapon does **1 damage** — a utility deploy priced
against a combat reference. Clause 5 at the actor level; likely a small class, unswept.

### ⛔ THE MINIGUNNER — TRACED TO #345, NOT TO BURST

Against the real baseline, `playtest-20260709` (Tournament Build 24), not a 2023 tag:

| stage | dmg | burst | cycle | rate |
|---|--:|--:|--:|--:|
| playtest-20260709 (`M16`, `E1.GDI`) | 2000 | 1 | 17 | **117.6/tick** |
| `5d491698f` scout redesign 07-19 | 2000 | 4 | 54 | **148.1/tick** |
| after **#345** 09-12 | 480 | 4 | 59 | **32.5/tick** |

The burst change was deliberate and priced at exactly 100 through the scout anchor; it RAISED the
rate. **#345 then cut damage 4.17x and invalidated that solved price.** Blackrobe ruled the baked
values stand — untouched, no `apply_balance`. Evidence only.

### WHAT IS STILL OPEN IN MY LANE

* ~~Averaging ruling — `extract_stats` + full re-extract~~ ⭐ **DONE** in this integration.
* **Next: the remaining cadence evidence**, `ChargeDelay`, `ShotsPerCharge` and reacquisition
  timing. They stand between the ruled charge law and applying it.
* The actor-level ruler is still a distribution of whole actors; a per-armament ruler needs the
  peer corpora re-expressed per weapon. MODEL change, needs the maintainer.
* **694 unfolded rates stay blocked.**
* TS sub-faction routing: Crystallized Nexus tags GDI units `zocom`/`steel`; `ts_gdi` routes only
  `('gdi',)`.

### REFERENCE DATA — CHECK BEFORE DECLARING ANYTHING MISSING

⛔ Three separate "source is unrecoverable" reports have all been wrong. `Cameo-mod-reference`
(~9.9 GB, OUTSIDE the repo) holds them. The seven INI sources with no `source_sha256` — **10,144
of 11,870 corpus rows** — are in `Cameo-mod-reference/extraction/` and are packaged at
`Cameo-mod-reference/ini_sources.zip` (1.8 MB, flat, with `SHA256SUMS.txt`). Codex verified all
seven hashes. ⚠ Codex runs on Blackrobe's machine, not the maintainer's — a path on one is not
reachable from the other.

## ⭐⭐⭐ 2026-09-14 — PR #375 FOLLOW-UP REVIEW FIXES, ASTRA GO

Codex reviewed Aedis's revised `c3dc32871` head with Astra. The original 71 focused tests and all
seven lane claims passed, but the review found five remaining correctness gaps: only three derived
inputs were fingerprinted, malformed/incomplete artifacts were accepted, per-armament hero targets
used the ordinary population, unknown Cameo roles could crash rendering, and coverage confused a
structured zero-match with missing structure while hiding same-role weapons.

The working follow-up fixes all five: the artifact now fingerprints its full 472-file input closure
and validates the exact set, hero armaments use the hero ruler, unknown roles render an explicit
abstention, and coverage is counted per weapon identity with structure tracked independently.
Focused validation is complete and Astra's final review is **GO**. This is ready as one compact
follow-up commit against Aedis's #375 branch.

## 2026-09-13 (late night) — AEDIS REVISED HEAD (SUPERSEDED BY FOLLOW-UP ABOVE)

Written by **Claude-Local (Opus 5)**. **This is the live state — read it before anything else
dated earlier, including the "(night)" section below, which it supersedes on the reference lane.**

| | |
|---|---|
| the branch | `claude/armament_pairing` → **`96cefbe3b`**, off `8f9bef3b0`, pushed |
| PR | **#375** — Astra NO-GO at `cfa8c9af9`; **all five blockers now addressed** — **MERGED 2026-09** |
| the map | **v27** — 73 originals · 116 expanded · 305 references · 45 priced by formula |
| suite | **161 fail/error, exactly master's baseline.** 2473 tests (master 2427) |
| doc claims | this lane's **7 of 7 green**; 11 pre-existing mismatches elsewhere, untouched |

### ⛔ THE DEFECT THAT INVALIDATED EVERY DAMAGE TARGET — `2e0df993d`

`reference_distribution.to_per_cycle` multiplies any `Burst > 1` row by its burst, because peer
corpora publish damage per SHOT. `reference_targets.cameo_context()` feeds it the **frozen Cameo
snapshot, which already stores burst totals** — so Cameo's burst rows were multiplied twice. The
mammoth 32,000 → 64,000; the MLRS 48,000 → **288,000**, 36× its per-shot damage. That snapshot is
the PROJECTION RULER, so a quarter of it being inflated lifted every actor's target:

    243 of 243 mapped actors inflated   median 2.01x   worst 8.31x
    153 of 153 burst-1 actors moved     EXTREME 50->17   DISAGREES 31->10

Found because the maintainer asked why the GDI grenadier's reference went 22k → 38k when all three
of its references are Burst 1 and none of them had changed. **The guard is on `source == "Cameo"`,
not a call-site flag.** If you consume `to_per_cycle` anywhere, re-check your numbers against this.

### THE RULES THE MAINTAINER SET, 2026-09-13

> *"one chosen peer weapon from each reference source contributes one candidate Range/DPS value for
> one Cameo armament; it is reference evidence only, not a live balance change. Originals should
> pair to the base weapon. Promotion/expanded actors should pair to the corresponding elite/upgraded
> replacement. MTNK's dummy remains the additive exception. A replacement must not also count beside
> its base weapon, and ambiguous role or identity must abstain."*

| tier | who | bench |
|---|---|---|
| `original` (140) | an original-shipping mod matched it by name | the BASE weapon only |
| `expanded` (174) | promotion units, Cameo/CA/DTA additions | the elite replacement, IN PLACE OF its base |

MTNK's dummy is not special-cased — it falls out of `replaces_dummy_primary`. Nine DTA units have a
zero-damage rate-of-fire stub as `Primary=`, so their `Elite=` weapon fills an empty slot and is a
genuine second armament in **both** tiers. That is why `td_gdi_battletank`, an original, still
references DTA's elite `70mmMsl1`.

### ASTRA'S FIVE BLOCKERS — ALL ADDRESSED (`4ed37c121`, `febf778a3`, `96cefbe3b`)

1. **elite replacements counted as extra weapons** → `armament_roles.tier_bench`, above.
2. **same-role weapons vanish; single-role actors hidden** → `cameo_armaments()` replaces
   `strongest_by_role` on the Cameo side; the report gates on WITHHELD, not on multi-ROLE.
3. **unproven-role fallback picked max damage** → `_unproven_pair` and `UNPROVEN_PREFERENCE`
   **deleted**. Pairs 607 → 308, unproven 300 → **0**, exact 213 → **215**.
   `ra2_soviets_apocalypsetank` is back to zero votes and that is now the correct answer.
4. **hashes recorded but not enforced** → two layers, both in-repo so they work without the 9.9 GB
   reference folder: each extractor's `load()` re-verifies its source pins against `ini_corpus.json`
   and drops per source (`load.dropped`); `armament_pairing.json` carries an `inputs` block and
   `pairing_document()` **raises** on a stale one.
5. **`Ground + UnknownFlyingTarget` became a proven ground vote** → `role_of_targets` fails closed.
   0 unknown tokens tree-wide today, which is when the guard is cheap.

### ⛔ LIVE YAML FINDINGS — NOT FIXED, AND DELIBERATELY SO

**PR #345 (`b235c6980`, 2026-09-12) divided damage out of 43 weapons** while adding
`PercentageDenominator`/`PercentageScale` to 213 warheads. Median divisor exactly **4.00×** (25
weapons at 4.0, 14 at 2.0). `td_gdi_minigunner` 2000 → 480 per shot.

⚠ **My first reading of this was wrong and Codex/Astra corrected it.** `pct_absolute == 0` means
there is no standalone percentage FLOOR — **not** that folded `PercentageScale` damage is zero. The
folded hit does execute, and the model carries it in `k_flat_context`. At reference HP 200,000 the
folded damage is 480 (minigunner), 960 (its AP weapon), 3,720 (RA1 machinegunner), 1,000 (Hind).
**Do not base a restore/finish decision on `pct_absolute`.** Maintainer's ruling: keep the current
baked values, do not restore pre-#345 damage, do not run `apply_balance`. The zero percentage
contribution is a separate runtime-audit item.

**The remaining DPS gap is still real and still unexplained.** `td_gdi_minigunner` composes to 749%
of its current rate, and **burst is not the lever**: at Burst 1 keeping `Damage: 480` the gap widens
to 25.4×; keeping the cycle total it is still 6.35×. The driver is reload — every reference fires a
full cycle in 20 ticks, Cameo takes 50 + 9.

⚠ **The frozen snapshot predates #345.** Pinned 2026-09-10; #345 landed 09-12. **32 actors'
`w_damage` differs between the pinned snapshot and live yaml** — 25 nerfed since, median exactly
2.00×, with a cluster at exactly 4.00×. So for those rows the map's "now" column is live while the
model's Cameo self-vote is the pre-quartering value. That is not a bug — the snapshot is SHA256
pinned precisely so the map cannot feed on itself — but it must be known when reading them.
`ra1_allies_sheridanassaulttank` is in this list at 4.00×: **the `test_missile_role_policy` 0.25×
and the #345 quartering are the same event** (Codex: the documented local-firepower bake, PR #377).

### THE 16 EXTREME ROWS — ONE MEASURED CAUSE, ONE CONSUMER GAP, FIVE STILL OPEN

Maintainer asked for the root cause of "all the very extreme cases". Measured against the v27 map;
`EXTREME` fires in BOTH directions, and the direction is the clue.

**CAUSE 1 — #345's damage bake (7 of 16, all of them ABOVE 100%).** These actors' `w_damage`
differs between the frozen snapshot (pinned 2026-09-10) and live yaml, because #345 landed 09-12:

    td_gdi_minigunner            749%   frozen  8,000 -> live  1,920   4.17x
    td_nod_minigunner            588%   frozen  8,000 -> live  2,320   3.45x
    ra1_soviets_rifleinfantry    462%   frozen  6,000 -> live  2,520   2.38x
    ra1_allies_rifleinfantry     399%   frozen  6,000 -> live  2,820   2.13x
    td_nod_buggymkii             361%   frozen 18,009 -> live  9,009   2.00x
    ra1_allies_alliedlighttank   256%   frozen 12,005 -> live  6,005   2.00x
    ra1_allies_alliedheavyaatank 230%   frozen  8,004 -> live  2,004   3.99x

⛔ RULED: the baked values STAND. No restore, no `apply_balance`. The frozen/live split is a
confirmed input discontinuity in these seven rows, but no re-pin counterfactual has established
that removing it would clear every `EXTREME` flag. Re-pinning is a separate decision with its own
hazards - the pin is what stops the map feeding on its own output.

**CONSUMER GAP — resolved: the reference path ignored an actor-level attack cycle (proven on
3 `AttackTesla` actors).** `ra1_soviets_teslacoil` exposed the mismatch clearly:

    weapon ReloadDelay             3 ticks   (the gap between zaps)
    actor AttackTesla ReloadDelay 100 ticks
    actor AttackTesla MaxCharges    3
    actor InitialChargeDelay       25 ticks   (defenses.yaml:229)
    extracted charge_up             ticks=25, cycle_reload=100, burst=3

`extract_stats` already records this `AttackTesla` data. `formula.charge_attack_cycle` models the
sustained attack as 3 zaps over 106 ticks (`100 + 3 * (3 - 1)`), or about 35.3 ticks per zap; the
25-tick initial wind-up is a separate price input, not something that can be added to each 3-tick
weapon reload. `reference_distribution.armament_profile` and `armament_roles.cameo_views` now apply
that shared actor-cycle formula when exactly one baseline armament makes ownership unambiguous.
The same correction covers RA2's Tesla Coil (75 ticks, one zap) and the Asian Alliance Railtower
(160 ticks, five shots). Charge-level traits keep their weapon cadence, and multi-armament actors
remain withheld rather than inheriting one actor cycle by guess.

The corrected four-faction report reads the RA1 coil as 144,000 damage per actor cycle and
1,358.49 damage/tick. Its independently composed reference target is 4,591 damage/tick
(`EXTREME 338%`), so the earlier `29%` explanation was backwards: it came from treating the
3-tick between-zap gap as the entire current cycle. This remains a diagnostic target, not a live
balance change.

Only three actors explicitly override `InitialChargeDelay` (`ra1_soviets_teslacoil` 25,
`ra2_soviets_teslacoil` 20, one Asian Alliance building 12). Other charge traits can use engine
defaults, so an explicit-field count does not bound the downstream fix. Measure from resolved
`charge_up` records. The current adapter therefore consumes only the three `AttackTesla` records
whose actor cycle is already explicit in the ledger.

⚠ The other three sub-100% rows - `ra1_soviets_shocktrooper` 47%, `ra1_soviets_zapper` 41%,
`ra1_soviets_commissar` 30% - are the same tesla/electric family, but shared damage type does not
prove shared attack cadence. Inspect their resolved attack traits and defaults independently.

**STILL UNEXPLAINED (5).** `japan_shrineminitank` 336%, `japan_igomediumtank` 238%,
`td_nod_lighttank` 210%, `ra1_soviets_flametower` 209%, `ra1_soviets_submarine` 206%. No frozen/live
drift, no charge delay, burst 1 throughout. These look like plain divergence from their references
rather than a measurement defect, but that is an impression, not a measurement.

⛔ **BURST IS NOT THE LEVER ON ANY OF THEM, and it was the first hypothesis.** The damage column is
already per CYCLE. On `td_gdi_minigunner`, going Burst 4 -> 1 and keeping `Damage: 480` WIDENS the
gap to 25.4x; keeping the cycle total leaves 6.35x. The driver is reload - every reference fires a
full cycle in 20 ticks where Cameo takes 50 + 9.


### WHAT IS STILL OPEN ON THIS LANE

* **The ruler is still the ACTOR-LEVEL distribution.** `armament_target` projects one armament
  against a population of whole actors' weapon damage. Right where one armament carries most of an
  actor's output, generous to a small secondary. A per-ARMAMENT ruler needs the peer corpora
  re-expressed per weapon first — not started, and it is a MODEL change needing the maintainer.
* **694 unfolded rates stay blocked** — only 77 INI rows declare a burst delay, in Phobos/Ares
  notation; `ini_views` leaves `cycle = None` for burst > 1 rather than inventing one.
* **TS sub-faction routing gap** — Crystallized Nexus tags GDI units `zocom`/`steel`; `ts_gdi`
  routes only `('gdi',)`.
* **`shield_versus_mean`** documented 175.919 vs measured 180.284 (`DESIGN.md` §12.0c and
  `design/ARMOR_LAYERS.md` both carry the stale number). Armor lane; Codex has logged it.

## ⭐⭐⭐ 2026-09-13 (night) — MASTER BOOTS, AND EVERY UNIT'S WEAPONS ARE MAPPED SEPARATELY

Written by **Claude-Local (Opus 5)**. **This is the live state — read it before anything else
dated earlier, INCLUDING the "(evening)" section below, which this supersedes on every point.**

| | |
|---|---|
| master | **`8f9bef3b0`** — PR #372 merged, then #346. **Boot-gated, ZERO blocking inherit nodes.** |
| branches | 203 → **115**; 75 landed branches deleted, 39 `archive/20260913/*` tags pushed |
| open PRs | 28 → **15** |
| the live lane | **per-armament reference pairing** — DONE and pushed |
| the branch | `claude/armament_pairing` — `38a3d3664` + `a47a627de`, off `8f9bef3b0` |
| the map | v25: 73 originals · 116 expanded · 305 references, now with per-armament references |

⛔ **THE SUITE BASELINE, so nobody re-derives it.** Clean `origin/master` `8f9bef3b0` runs **2427
tests with 22 errors + 139 failures across 113 distinct test names.** That is the floor; this
branch adds 29 passing tests and no new failures. The failure mass is NOT the R12 consolidation
lane — the largest clusters are weapon-name ownership tests (`test_soviet_owned_weapon_names` 16,
`test_yak_weapon_ownership` 12, `test_additional_owned_names` 10) and `test_missile_role_policy`
(8). Only ~50 of the 161 sit in consolidation/profile files.

⚠ The "(evening)" section below still says *master `b235c6980` DOES NOT BOOT* and *#372 is
blocked*. Both were true when written and are now false. Its technical content — the R12 rename
regression, why a green `audit_balance_drift` proves nothing about the model — remains correct and
is the reason the section is kept rather than deleted.

### THE LIVE LANE: per-armament reference pairing

Full document: **[`design/ARMAMENT_PAIRING.md`](design/ARMAMENT_PAIRING.md)**. In one paragraph:
`armament_profile` folds an actor's armaments into one `w_range`/`w_dps` and takes `max(ranges)`,
so `td_gdi_firehawk` reports its Sidewinders' **12,500** for a bomb that reaches **1,250**.
**47 of 940** priced actors fire in more than one role and **40** assigned reference rows are
contaminated by that fold. Shipped this turn, changing no balance number:

* `tools/balance/armament_roles.py` — the role classifier (`ground`/`air`/`both`/`special`, the
  maintainer's own 2026-09-07 missile vocabulary) plus one armament view for all three corpora.
  **0 unknown target tokens** across both corpora.
* `tools/reference/extract_ini_projectile_roles.py` → `docs/reference/ini_projectile_role_evidence.json`
  — DTA's real `AA=`/`AG=` projectile flags, `$Inherits` flattened, both file hashes verified
  against the corpus pin. **57/57 and 60/60** cited projectiles resolved.
* `tools/reference/extract_ini_elite_weapons.py` → `docs/reference/ini_elite_weapon_evidence.json`
  — ⛔ **the THIRD weapon slot.** A TS unit declares `Primary=`, `Secondary=` AND `Elite=`; the
  corpus carried only the first two, so **171 DTA `Elite=` declarations never reached the map**.
  The maintainer had to point this out twice. Gated on `Trainable=`, which the Enhance overlay
  flips: DTA Classic 0 reachable, DTA Enhanced **131** (7 of them a genuinely additional armament,
  where the primary is a zero-damage dummy).
* `tools/balance/build_armament_pairing_report.py` → `docs/balance/derived/armament_pairing.json`.
* `tools/tests/test_armament_roles.py` — **29/29**.

⛔ **STILL NOT DONE, AND IT STILL NEEDS THE MAINTAINER'S WORD:** retiring the fold in
`armament_profile` in favour of per-role targets is a MODEL change. The pairing is built, measured
and rendered in the map; the ledger and `apply_balance` are untouched.

⛔⛔ **A LIVE BALANCE FINDING THAT IS NOT MINE AND NOT FIXED.** `test_missile_role_policy` is red on
master: 8 of the 77 pinned missile-role conversions no longer preserve `Damage`, which rule 5
requires them to. Measured on `8f9bef3b0`:

| weapon | pinned | now | |
|---|--:|--:|--:|
| `ra1_allies_sheridanassaulttank_missile` | 16,000 | **4,000** | **0.25x** |
| `td_gdi_humveemkii_rocketshumvee2` (+3 siblings) | 16,000 / 32,000 | 8,000 / 16,000 | 0.50x |
| `ra1_soviets_monstertank_missile` | 40,000 | 42,000 | 1.05x |
| `ra1_soviets_samsite_missile_AA` | 16,000 | 17,600 | 1.10x |
| `ra1_soviets_su57attackbomber_missile` | 40,000 | 46,000 | 1.15x |

⚠ A red pin is not proof of a regression — a later, deliberate balance edit would look the same if
the history was never re-pinned. But the Hum-vee's uniform 0.50x and the Sheridan's 0.25x are large
and the guard that exists to catch exactly this is the one reporting it. **Never re-pin it to make
the test green** — that is the ratchet mistake. Someone has to say which of the two numbers is
intended. Both the Sheridan and the Hum-vee Mk II are multi-weapon units in the pairing lane, so
their reference rows rest on these values.

### Where everything is

| | |
|---|---|
| master | `b235c6980` — **DOES NOT BOOT** (verified directly, see below) |
| the work | `claude/integration_v23`, **87 ahead**, clean, pushed, boot-gated |
| the PR | **#372**, eleven PRs: #354 #355 #358 #361 #362 #363 #366 #369 #370 #373 #374 |
| blocked on | **Blackrobe** — the Thermobaric `Versus` ruling. Nothing else. |

⛔ **MASTER DOES NOT BOOT, AND IT IS EXACTLY ONE WEAPON.** Measured by running
`audit_duplicate_inherits` against a clean `origin/master` worktree, not inferred from a PR title:

    # BLOCKING - 1 node(s) the engine will REFUSE to resolve
      Wraith_ToxinMissiles -> ^Warhead_MissileAP_Heavy
        via Inherits:DeviatorMissile_Artillery -> DeviatorMissile -> ^D2KMissile -> ^Warhead_MissileAP_Heavy

⚠ An earlier comment of mine said SIX. That was unmeasured and wrong; PR #361 said ONE and was
right. **The engine throws on the FIRST blocking node, so a count above one cannot be observed in a
single boot** — it could only be found by fixing them one at a time. "Six" reads as *master is
deeply broken*; the truth is *master is one weapon away from booting*.

### ⛔ THE REGRESSION ASTRA CAUGHT, AND THE LESSON IT CARRIES

R12 (#366) renamed 34 structural migration helpers `^Compatibility_*` -> `^Warhead_*_Flat`. Two
balance consumers identified those helpers **BY NAME PREFIX**, so the rename promoted them into the
model:

    target_model.pseudo_armor_mean   shield mean 180.28 -> 181.44   factor 0.5547 -> 0.5511
    extract_stats.warheads           design_weapon_class moved on 33 weapons

⛔⛔ **AND MY RE-EXTRACT MADE `audit_balance_drift` GREEN WHILE PRESERVING ALL OF IT.** That guard
compares yaml against the ledger. Re-extracting wrote the new, wrong numbers into the ledger and the
two agreed again. **A GREEN DRIFT RUN PROVES THE LEDGER MATCHES THE YAML, NEVER THAT THE MODEL IS
RIGHT.** Nothing in the 227-test suite could see the difference.

⚠ And `pseudo_armor_mean`'s OWN DOCSTRING already said why, three lines above the bug: *"Filtered on
the warhead's TYPE, not on its key name ... The type is authoritative; the naming convention is
not."* **A lesson written beside the code does not enforce itself — only a test does.**

FIXED by semantics, one shared owner in `target_model.py`, used by both consumers:

    is_damage_inert(node)           every damage warhead at `Damage: 0` -> 33 migration helpers
    is_supplementary_template(node) ExtraDamage / FriendlyFire twins -> never a weapon's class
    non_class_templates(rs)         the union; `extract_stats.warheads` refuses to emit them

Shield mean restored to **180.2842 / 0.5547** exactly. Guarded by
**`tools/tests/test_shield_class_invariance.py` (6/6)** — the load-bearing test RENAMES every helper
and demands the mean is unchanged, which is precisely what a prefix filter cannot survive.

⭐ **THE SECOND COHORT WAS FOUND ONLY BY CHECKING AGAINST THE PRE-RENAME LEDGER** instead of
declaring the first fix done: 4 of 2,310 classes still disagreed, all newly collecting
`^Warhead_Railgun_ExtraDamage`. ⭐ Excluding the twins ALSO fixed an opposite defect — counting them
pushed weapons past the 2-warhead cap, so `MigMissiles_AA` and 6 siblings carried NO class at all.

⚠ A name test is wrong in BOTH directions: `^Warhead_TankBusterBeam_Unscoped_Flat` ends in `_Flat`
and is a REAL template (`Damage: 8000`).

### #369 — reconciled, never taken as shipped

Codex's `armament_profile` eligibility (`weapon_model_eligible = len(live) == 1`) is RIGHT and is
kept: it is the maintainer's ruling that a cannon and a missile may not be averaged. But
`_withhold_unproven_frozen_weapon_model` stamped EVERY frozen row ineligible. Measured on the
rebuilt map:

    live weapon targets 266 -> 0 · WITHHELD 38 -> 354 · EXTREME/DISAGREES 68/42 -> 0/0

⚠ AND IT LOOKED GREEN — the report still built and the headline counts (73 originals · 116 expanded ·
305 references) were IDENTICAL. **The guard rails reporting zero problems was the tell: they had
nothing left to guard.** Removed; everything else in #369 kept, including two real hero-row bugs.

### The 893 frozen rows — RECOVERED, not marked provisional

The SHA256-pinned snapshot predates `weapon_model_eligible` and carried it on none of its 893 rows;
every consumer tests `is False`, so absent read as eligible and all 893 were projected as
single-weapon. **893 of 893 have a live ledger counterpart** (796 eligible, 97 multi-armament), so
`_recover_weapon_model_eligibility` fetches the verdict by id — after the hash check, same rule
`to_per_cycle` follows. Applied to BOTH frozen contexts.

### The branch chaos, quantified

**203 remote branches, 189 surveyed** — classified BY CONTENT (`git cherry`, patch-ids, so it sees
through squashes), in **`docs/BRANCH_MANIFEST.md`**:

    72 landed (delete AFTER #372 merges) · 30 devin abandoned · 2 devin superseded by #373/#374
    9 open-PR branches (keep) · 75 legacy Apr-Jul · 1 integration branch

⛔ **NOTHING MAY BE DELETED UNTIL #372 IS ON MASTER.** "Landed" means *landed in #372*, which is not
merged. Deleting today destroys content that exists nowhere else. **39 `archive/20260913/*` tags are
pushed**, so every abandoned `devin/*` branch is recoverable even past GitHub's grace period.

⚠ **DEVIN IS RETIRED** (maintainer, 2026-09-13). Nothing behind `devin/*` has an owner. The main
checkout still sits on `devin/aurora/naming-ra1_allies` with **364 uncommitted files** — stranded,
NOT live WIP. Leave it alone; preserving it to a branch is Blackrobe's call.
(Ember 2026-09-24: the ra1_allies rename that checkout was doing is now regenerated on
`devin/ember/ra1-allies` from Aurora's `90e27a1b3` + `rename_map_ra1_allies_n4.yaml` —
25 actors / 30 files, `allied` strip, shared `ra1_soviets_*_ra1_allies_*` sprites left alone.)

### Open, with owners

* ⛔ **Thermobaric `COMPOSITE 92→93` / `Shield 179→180`** — from retiring the `^Warhead_*_Flat`
  shims. Three `PRESERVED_HASHES` fixtures pin the old values and are **NOT regenerated**:
  re-pinning a byte-stability guard is what it exists to prevent, and `Versus` needs permission.
  **Blocked on Blackrobe.**
* **Per-armament reference mapping** — the maintainer's cannon-vs-missile ruling. Data supports it
  on BOTH sides already: the ledger carries every armament with its conditions, and the peer corpus
  carries a full per-slot record (`weapon_evidence`: slot, range, reload, burst, burst delays,
  warheads, valid targets). **Nothing needs re-extracting.** `weapon_model_eligible` is the hook.
* ⛔ **The 694 unfolded rates stay BLOCKED.** Only 77 declare a burst delay, in Phobos/Ares notation
  that is not OpenRA's (`[15, -1]` for Burst 6). Needs a YR/Ares cycle model nobody has written.


## ⛔⛔ 2026-09-13 (later) — THE "334 UNFOLDED RATES" ARE 694, AND THE BLOCKER IS NOT ARITHMETIC

Written by **Claude-Local (Opus 5)**. ⚠ **Codex relayed at 13:34 that it has "picked up the 334-rate
recomputation".** This section is the measured diagnosis; read it before redoing the search, because
the headline number, the population and the root cause were all different from what I reported on
2026-09-12, and the ruled fix turns out to be blocked on an input nobody has.

### The number

| population | count |
|---|---|
| `ini_corpus.json` rows declaring `Burst > 1` with a rate of `damage / reload` | **694** |
| of those, surviving the population rule + faction routing into a pool | **362** |
| of those, actually ASSIGNED as some Cameo actor's reference | **77** (59 actors) |
| of those, inside the playtest scope (td_gdi, td_nod, ra1_allies, ra1_soviets, japan) | **5 actors** |

The "334" I published was one pool measured once. Deduped across `peer_rows` + `peer_hero_rows` +
`peer_variant_rows` it is 362, and the corpus-level population is 694.

### Root cause — it is a STALE CORPUS, not a formula bug

Seven INI sources carry **no weapon-evidence stamp at all** (`w_evidence: null` on every row):
CnC Reloaded, Mental Omega, RA2 0XX, RA2 Reborn, Red Resurrection, Rise of the East, Twisted
Insurrection. `ini_corpus.json` predates the evidence policy for them, so their rows sail through
`apply_weapon_evidence` untouched and publish `damage / reload` as a rate while declaring `Burst > 1`.

DTA Classic and DTA Enhanced are the control: their rows DO carry stamps, so their burst rows are
either withheld (`incomplete / burst_unfolded`) or carry a reviewed cycle proof. **The machinery
already works; it was simply never run over the other seven.**

⭐ **A fresh extraction fixes the stamps and LOSES NOTHING.** Measured 2026-09-13 by extracting all
nine sources to a scratch file and diffing field-by-field against the committed corpus:

    row keys identical (11,867)   ·   evidence LOST 0   ·   evidence CHANGED 0   ·   evidence GAINED 2,986

### ⚠ But a regeneration costs 63 hand-baked weapon selections

`ebf8f16ce` *"reference: read the Secondary weapon"* baked a dummy-primary correction directly into
63 corpus rows — RoTE's `HTK` Halftrack declares `Primary=FlakTrackGun` (a 0-damage dummy) and the
committed row silently carries the real `FlakTrackAAGun` instead. **All 63 are in those same seven
sources; none are in DTA.** The sanctioned mechanism (`ini_weapon_selection.json`, fingerprinted and
reviewed) covers only **2** rows, both DTA. A regen replaces those 63 with the raw shape, which the
fresh extractor then stamps `direct_undeclared` — safe, but abstaining.

⛔ **This, not "63 rows lose weapon evidence", is what the standing do-not-regenerate warning is
actually protecting.** The warning's wording sent me looking for lost `w_evidence`, of which there
is none.

### ⛔ THE REAL BLOCKER: there is no YR/Ares cycle model, and the delays are mostly undeclared

`rate = damage_per_shot x burst / (reload + sum of the Burst-1 delays)` needs the delays. After a
fresh extraction **only 77 of the 694 rows declare any** (`BurstDelay0..N` for Ares, `Burst.Delays`
for Phobos), and the notation is NOT OpenRA's:

    Rise of the East  MLRS270   Burst 6   delays [15, -1]          a -1 SENTINEL, and only 2 entries
    Rise of the East  RBUGGY    Burst 8   delays [15]              one entry for seven gaps
    Rise of the East  PHZ89     Burst 6   delays [6,6,6,6,6,6]     SIX entries for FIVE gaps

OpenRA's rule (`Armament.cs:146`) admits exactly length 1 or length `Burst - 1` and refuses to boot
otherwise. Ares/Phobos plainly do neither. DTA reached a correct rate only through
`ini_cycle_evidence.json` — **444 hand-reviewed timing proofs**, each carrying min/mean/max gaps,
post-burst jitter and a charge term, each fingerprinted to its source row.

So the maintainer's ruling ("recompute them to obey the formula") is right and cannot be executed for
the ~617 rows that declare nothing, without first deciding what cycle to assume for an engine this
repo has never modelled. **That is the open question. Do not guess it in code.**

### ⭐ What WAS fixed here, and it was a real defect in my own guard

`reference_targets.burst_delay_of` withheld on rows that **do** obey the formula, and contaminated the
rest. Measured over the 91 rows carrying a reviewed cycle proof — **32 disagreed with their own proof**:

* **False withholding.** DTA's `MLRS` "SSM Launcher" (damage 100, burst 2, reload 400, rate 0.25)
  satisfies `rate == damage / reload` BY COINCIDENCE: its proof puts the single gap at 400 ticks, so
  `100 x 2 / (400 + 400) = 0.25` as well. Both identities hold whenever the gap equals the reload, and
  my burst-1 test then refused a delay that was sitting in the sidecar, proven. That row is
  `td_nod_ssmlauncher`'s reference, so the withholding was visible in the map. Generals Alpha's
  Dragon Tank is the same coincidence.
* **Jitter contamination.** The inversion cannot see `post_burst_jitter`, so it charged that time to
  the burst gaps: `HTNK` 6.0 against a proven 5.0, `3TNK` 2.0 against 1.0, `MSAM` 10.0 against 9.0.

`burst_delay_of` now READS the proof instead of inverting the rate when one exists. 32 of 32 agree;
`td_nod_ssmlauncher` went from 1 recovered delay to 2.

⛔ **The lesson generalises: a row that satisfies the burst-1 identity is not necessarily unfolded.**
Test the EVIDENCE, not the arithmetic coincidence.

### ra1_allies_chronotank — closed, and the last gap is OUR rule, not missing data

Maintainer ruled 2026-09-13: *"of course you also need to remove the epic vehicle template from the
unit then after changing it"*. The yaml already carried `^FireSupportTemplate` with no epic template;
what remained was the preserved `design.class_anchor: epic_vehicle` in `docs/balance/redalert_allies.json`,
which `EXCLUDE_CLASSES` used to drop the actor entirely. Set to `fire_support` — the value
`class_membership.subtype_to_anchor("FireSupport")` returns, and the one 30 of the other 32
FireSupport units already carry. The actor now holds **Combined Arms `CTNK` + OpenRA Red Alert `CTNK`,
both name-exact**; assignment 373 -> 374 actors, >=2 floor 226 -> 227.

✅ **And the third source landed.** DTA Enhanced ships `CTNK` "Chrono Tank" (Allies, 1800cr) at
`build_limit 2`, so `is_hero_limit` put it in the HERO pool while removing Cameo's own limit put the
actor in the ORDINARY pool — name-exact, id-exact, and unreachable by every pass because the lanes
are impermeable on purpose. The maintainer asked for it directly (*"Can you please also use it as
reference or what?"*), and the CROSS-LANE PASS above is the answer: the actor now holds **all three**.
O1 gating stays **12 of ratchet 12** and O2 gating fell **7 -> 6**. No ratchet was raised, and no
exemption was added — the carve-out entry written for this actor earlier in the session was
DELETED once the pass closed the gap for real.


### ⭐ THE CROSS-LANE PASS — "Can you please also use it as reference?"

Maintainer, 2026-09-13, on DTA Enhanced's `CTNK` "Chrono Tank" sitting unclaimed. `assign_references`
gains a **fourth lane**, built to the variant pass's contract (strictly additive: it writes only into
an empty `(actor, source)` slot and claims each peer row once, so **no existing mapping can change**).

    the actor already holds an ORIGINAL-source row with raw_name EXACTLY 1.0
    + a candidate in a routed, unfilled source matching that anchor on BOTH id and name
    + that candidate unclaimed by any actor in any lane          =>   attach it, confidence FAIR

⛔ **The `raw_name == 1.0` gate is what stops it corroborating a bad base.** Ungated it produced 34
additions and one was `ra2_allies_grandcannon` -> Mental Omega `YAGGUN` "Gatling Cannon", extending a
0.75 mispairing the greedy had already made. Gated: **26 candidates, every one unmistakable**
(`DOG` "Attack Dog", `SONIC` "Disruptor", `TESLA` "Tesla Coil", `MMCH` "Titan").

⭐ **24 of the 26 are in the ORDINARY lane**, not the hero lane — rows the greedy never reached
because it takes one peer per actor per source. This is the documented failure mode again: *the
matcher never chose badly, the right candidate was invisible.*

**Landed: 3** — `ra1_allies_chronotank` (DTA `CTNK`), `ra2_allies_nighthawk` (Valiant Shades `shad`),
`yuri_slaveminer` (Red Resurrection `SMIN`). References 302 -> 305; originals under three sources
5 -> 4; `ra1_allies_chronotank` now holds **all three**.

⚠ **The other 23 were refused by faction routing, and the refusals split two ways.** Neither is
fixed here — both are outside the playtest scope (td_gdi, td_nod, ra1_allies, ra1_soviets, japan) —
but both are real and both are the same class as `33f9b9675` ("the RA1 countries are sides"):

* **CORRECT refusals.** `fr.allows` enforces the exclusivity rule: a row owned by several of a
  source's routed Cameo factions describes the mod, not a faction, so it is admitted to none.
  CnC Reloaded's `DOG` lists `AlliesCountry` **and** `SovietCountry`, so neither `ra2_allies_dog`
  nor `ra2_soviets_dog` may have it. Working as designed.
* ⛔ **A GENUINE MISSING-TOKEN GAP — TS sub-factions are not routed.** Crystallized Nexus tags its
  GDI units `zocom` (ZOCOM) and `steel` (Steel Talons), and `ts_gdi`'s route for that source is
  `('gdi',)`, so `SONIC` "Disruptor", `MMCH` "Titan", `JUGG` "Juggernaut", `HVR` "Hover MLRS",
  `SMECH` "Wolverine", `HMEC` "Mammoth Mk. II", `JUMPJET` and `LPST` are invisible to their own
  faction. Twisted Insurrection's `phoenix` IS routed, which is the precedent. ts_nod almost
  certainly has the mirror gap (Black Hand / Marked of Kane). **8 exact-name originals in one
  source — the largest single lever left in the map.**

### ⛔ Do not "fix" the hero lane to close a gap like this

Measured before the cross-lane pass was written, and recorded so nobody re-derives it: loosening
`is_hero_limit` from `> 0` to `> 1` does release DTA's `CTNK`, and it also releases CnC Reloaded's
`NODCOMMANDO` (Nod Commando, `build_limit 2`) into the ordinary vehicle population. **29 corpus rows
move and they include commandos, Slave Miners and Grand Cannons.** The `> 0` test is correct; what
was needed was a narrow derived exception, not a wider threshold.

## ⭐⭐ 2026-09-13 — FLEET SYNC, THE CODEX RECONCILIATION, AND THE REFERENCE MAP CLOSED OUT

Written by **Claude-Local (Opus 5)** on `claude/weapon_inherit_audit_and_map`, 28 commits ahead of
`master` and 0 behind. Read `docs/AGENT_WORKSPACE.md` → "Live agent roster" for who owns what.

### Where master actually is, and why every branch looks wrong

`master` is `b235c6980`, which took PR #345 as a **SQUASH**. That single fact explains most of the
confusion on this tree right now, so it is the first thing to internalise:

⛔ **AHEAD-COUNT IS NOT WORK-COUNT.** Every branch that fed #345 still reports its own commits as
"ahead of master" because the hashes differ, even though the content landed. `git merge-base
--is-ancestor` therefore answers the WRONG QUESTION. Verify by content:

    git show origin/master:tools/balance/build_reference_report.py | grep -c "sources used"   # 1

Measured 2026-09-13, four `claude/*` branches from 09-11 are in exactly that state and are
**effectively landed — close them**: `refmap_damage_tick_fix`, `fix_peer_armament_selection`,
`playtest_baseline`, `cl01_target_payload_review`. Their content is in master, and
`is_upgrade_gated` is correctly ABSENT because its own author reverted it (`3a75e831f`).

⚠ `codex/recovery-pr345-merge-20260912` reports **47 ahead / 828 files / 4.5M insertions** and
that number is an illusion for the same reason — it carries #345's ORIGINAL merge commit. The
genuinely new part is **118 tool files, ~22k lines**, and that part is real and is NOT on master.

### What Codex (Blackrobe) has been doing — and what of it is duplicate

**On MY branch, two commits, and one of them collided with me head-on:**

* `41d0dad57` *"make R1 and R3 diagnostics fail closed"* — Codex solved the SAME damage-convention
  problem I was solving, by a different design: keep both conventions alive, make the convention an
  explicit parameter (`DAMAGE_PER_SHOT` / `DAMAGE_BURST_INCLUSIVE`), and withhold whenever it is
  not stated. Its own comment states the premise: *"The source corpus currently lacks that
  compatible evidence, so a missing guard is an honest hold."*
  ⛔ **That premise is false and the AUTHORED YAML disproves it.**
  `td_gdi_mammothtank_120mmdualhv` declares `Damage: 16000`, `Burst: 2`, `BurstDelays: 8`,
  `ReloadDelay: 72`, and the snapshot carries `w_damage` 32,000 — so Cameo stores the burst TOTAL,
  provably; `td_gdi_mlrs_227mm` (8,000 × 6 = 48,000) agrees. The convention is knowable, so the
  cure is to RESOLVE it, not to stop reporting. Left as shipped it printed **WITHHELD on every
  row** of the verifier column the maintainer had just asked to keep.
  **Reconciled, not reverted:** I kept its genuinely better half — refusing a recovered burst time
  below zero, because a cycle shorter than `ReloadDelay` is impossible and clamping it to 0 would
  certify a broken timing model — and replaced the blanket hold with normalisation at row
  construction. WITHHELD is now **36 targeted cells, not all of them**.
* `8819225e7` *"measure deprecated-name lane"* — `tools/balance/audit_deprecated_name_lane.py` +
  a 5,495-line report. **Complementary, not duplicate**: it measures the R10–R15 population that
  `DESIGN.md` §11b.0 already rules. Keep.

**On `codex/recovery-pr345-merge-20260912`, genuinely new and worth landing:** new audits
(`audit_promotion_superiority`, `content_pack_dependencies`, `target_payload_routes`,
`secondary_payload_routes`, `status_effect_inventory`, `ownership_lineage`), `armor_projection.py`,
`assemble_four_voice_pilot.py`, an RA3 extractor (1,448 lines), and a large `tools/tests/` suite.

⚠ **One duplication risk to check before landing it:** it adds `tools/tests/test_virtual_anchor.py`.
`docs/TASK_INDEX.md` line 11 warns that a virtual-anchor mechanism was once re-designed when
`fit_class.py --spec` already implemented it. Confirm the test targets the EXISTING mechanism.

### The reference map is closed out for the five playtest factions

Scope is `td_gdi · td_nod · ra1_allies · ra1_soviets · japan` — the four-faction project
(`docs/balance/FOUR_FACTION_ROLE_PAYLOAD_DISPOSITION_20260911.md`) plus the Japan pilot. **845 of
872 cells now use ALL their available sources; 27 use only some.**

⛔ **"Every reference used" is NOT REACHABLE, and the arithmetic is the answer, not an excuse.**
4,780 reference rows exist; clauses 2+3 permit at most **1,870** assignments; only **2,241** rows
are ever visible to a same-type routed actor. So **2,539 rows can never be claimed by anybody** —
Romanov's Vengeance alone contributes 614, because it ships a full RA2 navy and the factions routed
to it field almost no ships. That is a CONTENT fact. `tools/balance/reference_coverage.py` reports
every empty slot with its CAUSE, which is the actionable form: in scope, 157 TAKEN, 97 NOT
NAME-BACKED, 8 NO CANDIDATE.

**Defects found and fixed this session, each measured before and after:**

1. **An original's worthless bid outranked an exact name match.** The greedy sorted with "is this
   an original?" as the OUTERMOST key, above the name score. `ra2_allies_nighthawk` took two rows
   named "Black Eagle" at name **0.154** while `ra2_allies_blackeagle` scored **1.0** and was
   refused; the shape-only rows were then correctly binned and both Black Eagles ended the run held
   by NOBODY. The preference now sits INSIDE the name bucket, so the `firerocketsoldier` 0.867 vs
   `rocketsoldier` 0.850 case it was written for still resolves the same way. **+17 mappings.**
2. **An SSM Launcher is not an MLRS.** `NAME_ALIASES["ssmlauncher"] = ("mlrs",)` scored a PERFECT
   1.00 against anything merely NAMED "MLRS". Measured: every genuine SSM Launcher already matched
   at 1.00 on its own name, and the alias ONLY ever added wrong units — CA's `MSAM` "MLRS", OpenRA
   TD's `MLRS` **"Mobile SAM"** (an anti-air unit), RV's "Rocket Launcher", TI's "Bullfrog".
   Removed. The reverse direction (`mlrs` → `msam`/`rocketlauncher`) is legitimate and stays.
3. **The RA1 COUNTRIES are sides.** OpenRA RA tags country-specific units with their COUNTRY, never
   their side, and the route tokens were only `("allies",)` / `("soviet",)` — so `TTNK` Tesla Tank
   (russia), `DTRK` Demolition Truck (ukraine), `CTNK` Chrono Tank (germany), `STNK` Phase
   Transport (france) and `MGG` Mobile Gap Generator (england) were invisible to every faction.
   `ra1_soviets_teslatank` scores an EXACT 1.000 against "Tesla Tank" and was holding Combined
   Arms' `TTRA` **"Tesla Track"** instead. **+3, nothing lost. O2 113 → 110, gating 11 → 8.**
4. **The recovery index was missing the HERO lane.** `td_gdi_exosuit` read "1 of 2 sources" on HP,
   SPEED and COST while DTA's `XO` sat there fully eligible. I had fixed exactly this for the
   VARIANT lane one commit earlier and forgot heroes in the same line.
5. **334 of 621 burst rows publish a rate that never folded burst in** — they satisfy
   `rate == damage / reload` while declaring `Burst > 1`. Inverting one for a burst delay returns a
   confident, meaningless number: DTA's `MLRS` (damage 100, burst 2, reload 400, rate 0.25) implies
   an 800-tick cycle and a 400-tick "burst delay" equal to its own reload. `burst_delay_of` now
   withholds on those (280 recover, 424 withheld).

### THE ONE FORMULA (maintainer, 2026-09-12/13) — binding

    rate = damage_per_shot × burst / (reload_delay + sum of the Burst − 1 delays)

The unit is **damage per TICK**, not per second — every term in the divisor is authored in engine
ticks. The stored field is still called `w_dps` across the ledgers; renaming it is its own
migration, so the FUNCTION and every label say "per tick" to stop the misnomer spreading.

⭐ **`formula.dps` has implemented this all along** and already owns `ENGINE_DEFAULT_BURST_DELAY`
and the varying-delay sum, so `reference_targets.burst_time` DELEGATES to
`formula.burst_delay_sum`. I briefly shipped a second copy including a duplicate constant — the
`allows()` mistake this repo has already paid for twice. **Do not add a fourth implementation.**

Engine semantics, checked against source rather than assumed — they are STRICTER than
"repeat the last entry":

    Armament.cs:146   Burst > 1 && BurstDelays.Length > 1 && Length != Burst-1 -> YamlException
    Armament.cs:476   length 1 -> that value every gap; else walked in order
    WeaponInfo.cs:129 BurstDelays = [5]

Measured in the tree: 829 weapons single-entry, 36 declare none (they run on `[5]`), **0 vary, 0
illegal**. Varying delays ARE live in the REFERENCE corpora, which is why the support was needed.

### ⛔ TWO THINGS BLOCKED ON A MAINTAINER RULING — do not proceed past these

1. **`audit_original_coverage` O1 is 13 against its ratchet of 12, so it EXITS 1.** I did not raise
   the ratchet and did not revert a correct fix. The single new row is `ra1_allies_phasetransport`,
   and it DISPROVES the premise O1 rests on — *"an original exists in OpenRA, so CA and DTA, being
   supersets, must have it too"*. They ship the id and give it to the wrong side: CA's `STNK.Nod`
   and DTA's `STNK` are both **Nod's Stealth Tank**, a different unit, so routing correctly refuses
   them and the gap can never be closed by matching. That is the same shape as the existing
   `O2_UNSETTLED` carve-out for Romanov's Vengeance — report it, do not gate on it. One line.
2. **A DATA asymmetry, not a bug.** `ra1_allies_chronotank` and `ra1_allies_mobilegapgenerator`
   both carry `BuildLimit: 1`, so by the ruled test (*"a hero is a limit of exactly one"*) they are
   heroes on the Cameo side, while OpenRA's `CTNK` and `MGG` are ordinary buildable units.
   Hero-to-hero-only then refuses a perfect 1.000 name match on both. Either Cameo's limits are
   wrong or the rule needs a carve-out; both are gameplay calls.

Also outstanding, not blocking: **OpenRA is not a complete authority on originals.**
`td_nod_ssmlauncher` is matched "SSM Launcher" by BOTH supersets and by no OpenRA source, because
OpenRA TD ships no SSM Launcher at all (verified across all 49 of its raw rows). The
originals/expansions split rests on a premise with at least one counterexample.

### What is still necessary before the balance pipeline can run

⛔ **GREP `docs/TASK_INDEX.md` FIRST — the virtual-anchor MECHANISM ALREADY EXISTS.**
`fit_class.py --spec hp,speed,range_wdist,damage,reload,cost0` **is** the virtual anchor, and
`derive_virtual_anchor.py` already defaults to exactly the five playtest factions. HANDOFF has said
it for days: *"What is missing is the INPUTS, not the mechanism."* Ran it 2026-09-13, 28 classes:

| blocker | classes |
|---|---|
| no calibrated model damage/reload supplied | **26 of 28** |
| THIN range / hp / speed / cost (too few sources to trust a median) | 12 / 10 / 10 / 10 |
| **BIASED — the tool itself says "do not sign"** | 3 fields |
| NO SOURCE at all | 1 |
| UNAPPROVED (approval is the maintainer's act, by design) | 27 |

So the order is: **model damage/reload inputs → per-class approval (holding the 3 BIASED back) →
`apply_balance --confirm`.** Nothing writes yaml until then.

### ⛔ ONE STEP LEFT ON THE CHRONO TANK — a design annotation, deliberately not changed

Maintainer ruled 2026-09-13: *"make the CTNK a regular unit without build limit. Like a fire
support so then it can match the reference."* Done and verified, in three parts — and it still
does not match, for a fourth reason that is a DESIGN decision rather than a bug:

1. `BuildLimit: 1` removed from `ra1_allies_chronotank`, `_mobilegapgenerator`, `_mobileradarjammer`.
2. `Inherits@Template: ^EpicVehicleTemplate` → `^FireSupportTemplate`. The ledger now reads
   `subtype: FireSupport` and `build_limit: None`, so both took effect.
3. ⭐ A REAL BUG this uncovered, fixed: `cameo_rows()` dropped on `build_limit is not None`, while
   the repo's own `is_hero_limit` has said since 2026-09-08 that a limit is "PRESENT AND GREATER
   THAN ZERO — `BuildLimit=0` means NO LIMIT". An actor written `BuildLimit: 0` therefore fell out
   of the ordinary population AND was refused by the hero lane for not being a one-off: it landed
   in NEITHER pool and could match nothing. Measured blast radius before changing it: exactly ONE
   actor in the whole ledger carries a zero limit.

**What still blocks it:** the ledger carries `design.class_anchor: epic_vehicle`, and
`EXCLUDE_CLASSES = {"epic_vehicle"}` removes the actor from `cameo_rows()` outright.
`class_anchor` is a PRESERVED DESIGN ANNOTATION — `extract_stats` writes `None` and the value is
carried forward from the design pass, so it does not follow the template. Changing it to
`fire_support` reprices the unit into another class, which is a balance judgement and needs the
maintainer's word, not a quiet edit. **Both gap generator and radar jammer DID land:** the gap
generator now has three sources (CA `MGG`, DTA `MSA` "Mobile Sensor Array", OpenRA `MGG`) and the
jammer has two, with DTA shipping no jammer at all — hence its `O1_UNSETTLED` entry.

### ⭐ NEXT, AND ALREADY RULED — recompute the 334 rows that ignore burst

Maintainer chose "recompute them to obey the formula" over withholding. 334 of 621 reference rows
with `Burst > 1` publish `rate == damage / reload`, never folding burst in, so their rate
understates the unit by roughly its burst. They currently withhold a burst-delay recovery but
their `w_dps` is untouched. Recomputing moves every DPS-derived target that draws on them, so it
wants its own before/after measurement — it is the first thing to pick up.

### Instructions for the rest of the fleet

* **Do not touch `tools/balance/{assign_references,reference_targets,reference_distribution,
  reference_coverage,build_reference_report,faction_routes}.py` or `tools/reference/variant_pool.py`
  without saying so on the roster first.** Codex and I collided on `reference_targets.py` today and
  it cost a hand-merge; one owner per file-set (`BALANCE_PROGRAM_PLAN.md` §2) exists for this.
* **Never read a background task's notification exit code** — read the `exit=` line in the output.
* **Never raise a ratchet.** If a correct fix trips one, say so and ask, as done above.
* **The reference map is one artifact, not many.** Update the existing page rather than publishing
  a new one; find it with the Artifact `list` action instead of guessing.


## ⭐⭐ 2026-09-12 — ALL NINE DECISIONS ARE RULED. THE QUEUE IS UNBLOCKED.

The rulings are binding and live in **`DESIGN.md` §11b.0 (R1–R9)** — read that, not this
summary. The maintainer-approved WORK ORDER, all four confirmed in one answer:

1. ✅ **DONE — the 27 `^Warhead_*_Flat` shims are deleted** (R4), boot-gated, by
   `tools/balance/retire_flat_shims.py`. 46 users re-pointed; compensations written for 11
   dead `Warhead@X` / `-Warhead@X` pairs, 7 extra warheads and 78 weapon-level fields.
   Verified through the new shared **`tools/balance/resolved_gate.py`**, which pairs the
   order-INSENSITIVE field set with an order-SENSITIVE warhead-sequence check — Codex's Wraith
   finding composed with my rename gate, as they asked. `promote_compatibility_warheads.py`
   now uses it too. `find_empty_warhead` 0; `audit_family_uniqueness` and
   `audit_versus_profile` green.
   ⛔ **"Expect W8 to fall below 858" was wrong.** W8 tests the `^Warhead_` prefix, which
   `^Warhead_*_Flat` already satisfied, so the shims were never in its count. W8 is
   **unchanged at 858** and this change moves no ratchet at all. It removes 27 duplicate
   templates — and the corrected R4/R6 numbers it forced out are worth more than the deletion.
2. ✅ **DONE — carrier slave ammo pools** (R8), boot-gated. Generated by
   `tools/balance/carrier_slave_ammo.py` (the law; its self-test reproduces both of the
   maintainer's worked examples) + `apply_carrier_slave_ammo.py` (placement only).
   10 pools resized, 4 created, 14 reloads added. `audit_ammo_cadence` A2 ratchet
   **19 → 0**, with the suicide slaves reported as out of scope instead of as a backlog
   nobody is allowed to work.
   ⛔ **Scope was 14, not 17** — 19−2 assumed the maintainer's two names covered every
   suicide drone; three more qualify under the same rule. And the two NAMED ones carry no
   suicide trait at all (their self-destruct is in the weapon), so the explicit list and the
   detector are both needed.
   ⛔ **"Upgrade weapons get `AmmoUsage: 0`" is wrong for a REPLACEMENT pair.** Siblings on
   `X` and `!X` are a swap, not an addition; `japan_zerofighter_slave` runs both live
   armaments on the `X` side, so zeroing them would have left the upgraded unit firing with
   no ammo cost forever. See `DESIGN.md` R8.
3. **Virtual baselines + the 100–250% band** (R3) — MEASURED; the blocker is not baseline
   arithmetic. All **28 anchor dossiers** now exist under `docs/balance/anchors/`
   (`propose_anchor_spec.py`; the 4 dated 2026-09-09 are annotated review snapshots and were
   deliberately NOT regenerated — they say so in their own text). New:
   `tools/balance/fit_baseband.py` → `docs/balance/baseband_fit.md`.
   ⛔ **`cost0` cannot move the band** — it cancels out of the ratio exactly. Only
   `hp0/speed0/range0_wdist/dps0` move it.
   ⛔ **The band starts AT the baseline** (ratio 1.000 there, 2.500 at the 2×/2× verifier), so
   "all members in band" requires the baseline at or below the weakest member. A **median**
   baseline therefore cannot satisfy the band — and medians are what `derive_virtual_anchor.py`
   proposes. 115/404 in band today; re-scaling every baseline reaches only 271/404 (67%).
   ⭐ **Every class already has a current-anchor ratio window** (span 1.4×–2.5×, 290 of 404
   members). The **114** outside those windows are the real work. They are triage signals, not
   proof of a classification defect: `futuretech_blackwidow` is in `melee` with `Range: 9000`,
   `corrino_buggy` is in `mbt`, `cabal_enlighted` has 11,184 DPS in `heavy_infantry`.
   Uniform rescaling changes the nonlinear spread, and an anisotropic baseline or role split
   requires separate design evidence.
   **The 114 are triaged** (`fit_baseband.py --triage`, table in `baseband_fit.md`):
   80 AXIS OUTLIER, 30 ROLE REVIEW, 2 NO CLASS ACCEPTS, 1 ONE CLASS ACCEPTS, 1 LATER TECH.
   ⛔ **A stat test cannot say where an outlier belongs.** The median member is accepted by
   **6 of 27** class baselines, so "another class would take it" is worth nothing — an
   earlier pass used it as the deciding signal and produced 81 authoritative-looking
   MISCLASSIFIED labels, one of which put `terran_ghost` in `artillery`.
   ⭐ **→ NEXT: W24, not the band.** **61 of the 114 are `raw_dps`-driven**, the one axis
   §0a defers and every anchor dossier refuses to target while W24 moves. So the band cannot
   be fitted before W24 closes, and most DPS-driven outliers are not class questions at all.
   The genuinely decidable few today: `harkonnen_inkvine` and `naxis_slave` (accepted by NO
   class; `raw_dps` 0.0x/0.1x — data defects), `naxis_naximercenarysniper` (only `scout`
   accepts it), `naxis_skymage` (390% at tier 0.75 — a tech-tier gate may explain it).
## ⭐ 2026-09-12 — W24 IS NOW THE FRONT, AND IT IS SPLIT WITH CODEX

The queue changed: **W24 moves ahead of the baseband**, because 61 of the 114 band outliers are
`raw_dps`-driven and DPS is deliberately unsettled until W24 closes.

**State:** `audit_three_way_split` **230** stacks (ratchet 322) · `audit_tier_weapon_class`
**39** budget violations (ratchet 48) · W5/W7/W8 305/957/858. Of the 230 stacks, **149 carry a
legacy-named main**, concentrated: `1Dam` **48**, `1Dam_impact` 13, the four `*Dam_areanuke*`
names 9–10 each, `TemperatureCompatibility` 8, `Railgun_HeavyFlatCompatibility` 8,
`IonCannon` 7, `Damage` 7.

⛔ **`1Dam` is not a 1-damage marker — the name is a lie.** All 48 are `SpreadDamage` carrying
1,200–50,000 damage with NO `Versus`, so each is a genuine second main applying FLAT damage to
every armor. Dropping one deletes real damage (the `47a66b6c2` mistake).

⭐ **§12.0h MEAN-100 makes the fold mean-preserving BY CONSTRUCTION** — `mean(p)=100`, so
`mean(D_main·p/100 + D_flat) == mean((D_main+D_flat)·p/100)`. Asserted per weapon: 8/8 within
2%. The fold moves SPREAD, never magnitude. `tools/balance/analyse_flat_main_fold.py`.

**LANE SPLIT (rule 6, by file-set), posted as PR #354 comment 5648397932:**
* **mine** — central weapon files: `weapons.yaml` (22), `tiberiansun.yaml` (6), `d2k.yaml` (5),
  `outpost2.yaml` (1). 8 are clean two-main flat folds; 16 have 3 mains (design call), 9 have a
  legacy node that HAS a profile, 1 has no usable family profile.
* **Codex** — ContentPacks: `D2k/Ordos` (9), `RedAlert2/Shared` (3), `D2k/Atreides` (1),
  `D2k/Shared` (1); plus the self-contained `*Dam_areanuke*` 7-main cohort.

⛔⛔ **THE TWO TRAPS, both already paid for:** two ADJACENT levels of one family is **LEGAL**
(between-tier encoding; budget = TYPES × LEVELS, ceiling 4 — I nearly erased 79 correct weapons
and every audit stayed green); and a collapse must carry the **TOTAL**, not the surviving
warhead's number.

⚠ **BLOCKED ON ONE PERMISSION (rule 4):** a fold changes per-armor damage. The 8 candidates
sorted by flat share — `TSPistola` 9% (worst armor ×0.91), `TSGrenadeAA` 17% (×0.83),
`GLToxinExplode` / `GLToxinExplodeBlue` 22% (×0.80), `TSVulcan` 50% (×0.65), `D2K_Rocket_AA`
65% (×0.64), `TSVulcan2` 71% (×0.56), `TSTurretLaserFire` 79% (×0.37). Nothing written until
the maintainer picks a share threshold.

4. ⚠ **R1 tooling is present, but the DPS verifier remains diagnostic-only.** Four inputs, one
   guard rail. `reference_targets.COMPONENT_STATS` / `VERIFIER_STATS` + `compose_dps`,
   `recover_burst_time`, `dps_guard`; the reference map gains a **source damage coordinate** and
   **Reload** columns. A verifier result is emitted only when the damage convention and complete burst-delay
   sequence are explicit; the current peer corpus does not provide that compatible evidence, so
   the map withholds the previous `DISAGREES`/`EXTREME` claims.
   ⛔ **`w_damage` means different things in different sources** — per-SHOT in
   `extract_peer_units`, burst-INCLUSIVE in the frozen Cameo snapshot. The corrected guard refuses
   to infer a convention from `damage / DPS`, and it refuses to reuse a partial delay model.

⛔ **Blocked on nothing but sequencing:** merge **#356** (Codex's Wraith order fix — my reorder
put the 60,000-damage main *after* `Warhead@OwnerChange`, so the Wraith captured a unit and then
shot it) into **#354**, then re-extract the ledgers ONCE as its own commit. `audit_balance_drift`
is red on **26 of 34** and a re-extract also picks up 5 RA1 actors someone changed in yaml
without re-extracting.

⛔ **Still not to be regenerated:** `docs/reference/ini_corpus.json`. A refresh drops 63 rows'
weapon evidence (`HTK` `FlakTrackAAGun` 33 → `FlakTrackGun` **None**). Needs
`EXPLICIT_DUMMY_WEAPONS` populated from the source profiles, or an explicit decision to accept
the loss. The names (`200mmD`, `SonicZapC`, `VulcanD`) say they ARE dummy slots, but a zero
`Damage` cannot *prove* one.

⚠ **Bell curve: the hold HOLDS** (R7). `USE_BELL` stays false until W24 closes (W7 957, W8 858).

⛔ **R6 is corrected: ONE template is out of band, not nine.** The nine came from folding
`Shield` into a `max/min` Versus ratio, and `Shield` is its own compressed [100,400] ladder
(§12.0c) that `audit_versus_profile.py` has always excluded. On the 16 real armor rows only
`MissileAP_Heavy_D2K_ORocket` (**12.50x**) is genuinely out of band; `Sniper_Light` (10.00x) is
`HAND_TUNED` and ratified. **`Laser_Medium` is 4.84x — in band, on the 4x target, do nothing
to it.** `Storm_*` and `Tesla_Heavy` likewise. See `DESIGN.md` R6 for the table.

### The old "open decisions" list, for provenance only — every one is now answered


Newest first; each one blocks a batch that is otherwise measured and ready.

**1. Which weapon target is authoritative — DPS, or damage+reload?** They disagree by
**1.42×** and it is not a bug: `reference_targets.target_for` projects every stat against its
own distribution, so `w_dps`, `w_damage`, `w_burst` and `w_reload` are **five separate votes,
not one decomposition**. Traced end to end on `td_gdi_mammothtank` (3 sources, 6 rows, STRONG
on all three): DPS projected alone says **+73.7%** (400 → 695); damage +9.1% with reload −11.1%
composes to **+21.9%** (488) through Cameo's own identity `DPS = damage-per-burst ÷ (reload +
burst delays)`, which checks out exactly today (32,000 ÷ 80 = 400). The pipeline's *intent* is
that DPS wins and `propose_class_rebalance.decompose_dps` solves the rest — but that has never
been ruled, and the difference is the entire rebalance. **Nothing can be applied until this is
answered.**

**2. Formula price or reference cost?** At the reference target stats `formula.price` says
**3,200** and the references say **2,500** — a 28% gap between the two authorities, on a unit
the formula already reads as **40% underpriced** at its shipped 1,600 (formula 2,246). Applying
reference stats without choosing leaves the unit priced by neither, which collides directly
with the standing rule that *no stat moves unless the formula prices it*.

**3. `^Compatibility_*` — the 36 mixed families.** 33 of 69 templates are promoted to real
`^Warhead_*` (see `DESIGN.md` §11b.1b; W8 874 → 858, behaviour-identical). The rest are blocked
on a **template-count ruling**: 56 of 64 families have BOTH a user that already inherits the
twin (needs the new template to chain it) and a user that inherits no `^Warhead_` at all (would
*gain* weapon-level fields from that chain — measured: 112 weapons would newly gain
`Warhead@Bullet_Medium`, 11 would gain `TargetActorCenter`). One template cannot serve both, so
each family needs a second one.

**4. Projectile / warhead geometry — the review itself.** 2,894 records are collected and
voting on nothing (`docs/reference/PROJECTILE_GEOMETRY.md`). The first substantive question is
units: TD/TS warheads declare `Spread` in **leptons** (`DemoAtomicWH` 512, 256 to a cell) while
RA2/YR declare `CellSpread` where `AAHE` reads 0.5 (plainly half a cell) and `BlueJammer` reads
**225** with Ares fixed-point providers in play. Nothing is converted until that is ruled.

**7. ⛔ AN AMMO POOL MAKES `ReloadDelay` THE WRONG CLOCK — 133 actors, and nothing knew.**
`extract_stats`, `reference_distribution` and `formula` contain **zero** references to
`AmmoPool`, yet 145 Cameo actors have one. Maintainer ruled the comparable figure per regime:
a self-reloading pool is *pool damage / time to empty* (101 actors), an airfield-rearm plane is
*damage per sortie and no rate at all* (22), and 10 have no replenishment mechanism this can
find. **12 hold a single shot, so no rate exists for them either.** `tools/balance/ammo_cadence.py`
implements it with a self-test; `audit_ammo_cadence.py` reports it and is in `run_all.sh`.
`td_nod_ssmlauncher` is the proof: weapon rate 2 shots/250 ticks, ammo rate 2 shots/250 ticks —
identical, so its reload is decorative and a pipeline-written reload change would move the
ledger's number while changing nothing in game. **54 of 93 self-reloading actors cannot sustain
their own weapon's rate.** Nothing applied: the ledger cannot be re-extracted yet (decision 8).

**8. ⛔ ALL 19 `CarrierSlave` ACTORS BREAK THE POOL+RELOAD RULE**, in two opposite ways.
8 have **no pool at all** → `CarrierSlave.cs:59-65` grants *"unlimited ammunitions"*, so the
carrier's launch/expend/return cycle never runs. 11 have **a pool and no reload** → they empty
once and are permanently unable to attack: `CarrierMaster` has no ammo path (`RearmTicks` only
gates relaunch), none carry `Rearmable`, and `CarrierSlave.NeedToReload` is **declared and never
called anywhere in CA**. Fix is `AmmoPool` + `ReloadAmmoPool` on each. ⚠ Two of the 8
(`tkmsuicidedrone`, possibly `farasha_drone_ixian`) are suicide drones and may be legitimate
exceptions — confirm before adding pools to those.

**9. The ledger cannot be re-extracted until #356 lands, and `audit_balance_drift` is ALREADY
RED on 26 of 34 ledgers.** A re-extract today picks up (a) my own Wraith reorder, which #356
reverts — the main warhead moves from `damage_warheads[0]` to `[4]`, visible proof of Codery's
ordering finding — and (b) five RA1 actors someone changed in yaml without re-extracting
(`ra1_agentdelphi`/`ra1_general`/`ra1_technician`/`ra1_einstein`/`ra1_scientist`, HP 2500→5000,
damage 100→500). Merge #356, then re-extract once, as its own commit.

**5. The 63 dummy-primary rows — and the INI corpus must NOT be regenerated until they are
ruled.** Regenerating `docs/reference/ini_corpus.json` today changes 1,789 rows, but only **63**
on evidence (the other 1,726 are DTA provenance stamps). Those 63 carry the OLD auto-promotion
shape, so a refresh DROPS them and the units lose their weapon evidence entirely:
`Rise of the East / HTK` goes from `FlakTrackAAGun` damage 33 to `FlakTrackGun` damage **None**;
`NUKCAN` from `200mm` 250 to `200mmD` **0**; also `SonicZap`→`SonicZapC`, `Vulcan`→`VulcanD`.
The naming says these ARE dummy targeting slots and the committed corpus is right — but a zero
`Damage` on the primary is `direct_undeclared` and **cannot prove a dummy**, which is exactly
what `EXPLICIT_DUMMY_WEAPONS` exists to keep explicit. Either populate that table from the
source profiles or accept losing the evidence. Until then **no corpus regeneration**, which is
also why new collect-only fields (`w_burst_delays`, `w_phys_*`) are computed on demand.

**6. Burst is now taken DIRECTLY, not projected — and the map flags when it would move.**
Maintainer caught it: *"the mammoth tank always has 2 bursts for all weapons from all sources
right? and you averaged it to 1.67x?"* Correct, and it was the projection, not an average.
`target_for` maps a raw value to its POSITION in its source's distribution, which is right for
continuous magnitudes and wrong for a small integer count: DTA's burst support is 2–4, OpenRA
TD's 1–5, Combined Arms' 1–**30**, Cameo's 1–**100**, so a 2 sitting low in one support lands at
1.67 in another. Measured: of the 209 actors with a burst target, **163 have unanimous source
agreement** and projection contradicted it (`cabal_plasmaturret` all sources 5 → projected 2.21;
`forgotten_mlrs` all 8 → 5.08). `reference_targets.DIRECT_STATS` now takes burst as a pooled
median of raw eligible values. Nothing applied — but every burst target before this is wrong.

Full trace for #1 and #2, every stat and all four armaments:
<https://claude.ai/code/artifact/67164cd7-20ae-4c62-b799-38912fa3de4c>

⚠ One pre-existing red, flagged so it is not attributed to the grid change:
`audit_damage_grid` fails on `basis-point pct twin 187 > 0; 50% twin 379 > 353` — **identical
numbers on a pristine worktree at HEAD**. Off-grid main damage went 65 → **0**.

## Claude and Codex continuation — 11 September 2026

For the active RA1 Allies/Soviets and TD GDI/Nod work, start with the
[current status and ownership](balance/PROJECT_STATUS_20260911.md), then the
[grand plan](balance/GRAND_PLAN_20260911.md). The status contains the corrected
results, open work, checkout instructions and **CL-01**, the bounded target/payload
review reserved for Aedis's Claude. Codex retains implementation and integration.

The earlier checkpoint is upstream draft PR #342 at `33a2fb2`. The later plan,
implementation, corrected Astra evidence and portable inputs are supplied on
`Blackrobe/Cameo-mod:codex/overnight-integration-20260910` as a linked draft
continuation. Fetch that fork branch; fetching upstream master or the old PR
alone does not obtain the continuation. See the status for the exact commands.

The 22:37 Discord report overstated role closure: Havoc retains its existing Air
capability, 19 target-route cases still need review, and only 13 of the 31 numerical
proposal rows are reviewable (18 held). The full table accounts for 163 actors;
it does not certify 163 prices. Frozen armor-channel reconstruction remains open.

The [portable input packet](balance/checkpoints/20260911/claude-continuation/README.md)
includes the four comparison inputs and all 71 original frozen ledger inputs.
Use the current status above instead of treating dated logs below as new orders.
This handoff authorizes no merge, game launch, build or external agent setup.
Scheduled Discord checks are active every 15 minutes through 14 September 2026
at 00:16:58 WIB, using a new temporary external-browser tab for each check.
The repository-wide history follows.


## ⭐ 2026-09-13 — DEVIN-CLOUD (the AI lane): who I am, what Codex already did, and what I need

`Agent: DEVIN-CLOUD · lane: AI bot modules · branch: devin/1788792445-ai-master-module`

I am the agent that wrote the AI architecture (§10/§11 of
[`design/AI_ARCHITECTURE.md`](design/AI_ARCHITECTURE.md)), the personality set, the observer
personality indicator, the Combat Effectiveness graph and phase 1 of the AI build order. Task H
handed the AI modules to Astra on 2026-09-06 when my quota ran out mid-merge; I am back and I am
working the AI lane again. **Astra keeps the balance pipeline.** Nothing in this entry asks for
any of it back.

### What I own, and what I do not

**Mine (write):** `OpenRA.Mods.Cameo/Traits/AiMatchLogWriter.cs`,
`AiSituationLogWriter.cs`, `AiLogFileAppender.cs`, `Traits/BotModules/BotSituation.cs`,
`Traits/AiMatchLogRecorder.cs`, `tools/ai/`, the bot-module trait wiring in
`mods/cameo/ai/ai.yaml`, and `design/AI_ARCHITECTURE.md` §10.5–§10.6 + `design/AI_MATCH_LOG.md`.

**Not mine (read-only to me):** every `UnitsToBuild` / build-order row in `ai.yaml` — those belong
to the faction lanes; all of `tools/balance/` and `tools/reference/`; and Codex's §10.2/§10.2a
module-contract table, which I amended in exactly one paragraph (see below) and otherwise left as
written.

### Where the AI line actually stands

| phase | state |
|---|---|
| 1 — record-only match logging | **landed** (PR #331, then `9ad1a5f77`, then Codex's save-exclusion in #329) |
| 2 — observe-only `MasterAiBotModule` + situation log | **landed** (#364) |
| 3 — synced `BotPersonalityController` and dynamic switching | next, and the first phase that changes play |
| 4–9 — per-enemy targeting, counter-demand, fog, scouting, offline eval, bandit priors | proposed |

Phase 2 builds an immutable per-enemy snapshot every 150 ticks, picks a candidate main target and
a candidate personality every 1500 — a bot holding no target re-picks at the 150-tick snapshot
instead — and **writes them to a log and nothing else**: no orders, no
conditions, no synced state, and no module reads the snapshot yet. It is deliberately pre-fog and
its target score deliberately omits the pairwise `w_hurt` term, because no verified per-enemy
damage attribution hook exists before phase 4. Numbers in the log are integers only.

The bot-player gate is `python tools\tests\ai_bot_player_gate.py`; `boot-test.cmd` only proves
plain OpenRA launch and is not a bot-construction check. Match and situation logs now include
campaign and other map-declared bots; use their `map_uid` and `bot_type` fields when filtering
offline.

⚠ **Do not quote phase 2 as evidence that the bots are smarter.** It observes. The first phase
that a player could feel is phase 3.

### Review of Codex/Astra's AI work — what duplicated, and what did not

I read `5bb76c22d` (PR #329) and `b235c6980` (PR #345) against my branch before merging. **The
overlap is much smaller than the commit messages suggest, and Codex made the right call at the one
point where it mattered:**

* ✅ **No duplicate logger.** #329 explicitly dropped its own `CameoMatchRecorder` and adopted the
  merged #331 writer instead, and recorded that the older `Logs/cameo_matches/*.jsonl` experiments
  carry a different schema and must never be mixed with `Logs/cameo-ai-matches.jsonl`. That is the
  single largest duplicate this fleet avoided this week, and it was avoided by reading the other
  agent's merged work first. `tools/tests/test_ai_logging_integration.py` now *enforces* that only
  one logging pipeline is wired.
* ✅ **A real defect I missed.** My phase-1 writer would have recorded a **resumed save** as a
  fresh completed match, because replay-in eventually clears `IsLoadingGameSave`. #329 fixed it by
  capturing eligibility once at world load (`eligibleAtWorldLoad` + `Eligible(...)`). I have now
  mirrored the same exclusion into the phase-2 situation writer, which had the identical hole.
* ✅ **The graph verification I could not do.** #323's graph landed once (`e70ab6cdb`); #329 then
  fit the selector label after an actual 1024×768 replay showed it clipped, and verified the
  signed history and both scroll arrows over a 21-minute replay. That closes the open item I left
  in #323 — the negative excursion and the zero line **are** confirmed on screen. Their label and
  their regression tests are the version to keep.
* ➖ **Documentation overlap only, and it is complementary.** Codex's §10.2 per-module contract
  table (what each of the 20 loaded modules owns, its inputs, its outputs, its cadence) is the
  half of the architecture I had left at prose level. I kept all of it. I changed exactly one
  paragraph — §10.2a's "Proposed, not loaded", which said the master module publishes nothing yet
  — because after phase 2 that sentence is false. Everything it says about `ScoutBotModule` and
  `BotPersonalityController` still being proposed remains true and untouched.

**Nothing needs to be reverted, and nothing of mine was lost.** The integration is already done in
my phase-2 branch: their eligibility rule, their tests and their contract table, plus my snapshot.

### Two findings for whoever owns them

1. ⚠ **`mods/cameo/ai/ai.yaml` gained a UTF-8 BOM in `b235c6980`** (`EF BB BF` before
   `^AIDifficulties:`) and is now the only yaml in `mods/cameo/rules|ai` that has one. It is
   harmless *today* — the engine reads yaml through `new StreamReader(s)`
   (`engine/OpenRA.Game/StreamExts.cs:205`), which strips BOMs, and `tools/audit/miniyaml.py`
   reads `utf-8-sig`. But `tools/audit/audit_ai_personalities.py:110` reads plain `utf-8`, so in
   that tool the first node's name is `\ufeff^AIDifficulties`. No current check looks at the first
   block, which is the only reason the gate is green. Either strip the BOM or move that reader to
   `utf-8-sig`; do not leave it resting on "no check looks there yet".
2. ✅ For the record, the same commit's `ra1_soviets_sovietoretruck` → `ra1_soviets_oretruck`
   rename inside `HarvesterTypes`/`RefineryTypes` is correct and consistent with the rename
   revert. The bots' economy wiring is intact.

### What I need from the fleet

* **Do not implement AI bot modules in another lane.** If a task looks like bot decision-making,
  post it here and I will take it — phases 3–9 are ordered for a reason, and phase 6 (fog) is last
  because it *weakens* the bots and invalidates any tuning done before it.
* **`ai.yaml` is a shared file with two kinds of content.** Trait blocks are mine; `UnitsToBuild`
  and build-order rows are the faction lanes'. Those never collide if we each stay in our half.
* **If you touch the match log or the situation log, keep them parseable by a test in the
  emitter's own language.** Both files are hand-built with a `StringBuilder`; a single missing
  comma makes every line invalid and the offline aggregator can only report it as a skip. That
  already happened once (`9ad1a5f77`), and Python fixtures built with `json.dumps` cannot catch it.
* **A request to Astra specifically:** phase 3 needs one synced trait (`BotPersonalityController`,
  an `IResolveOrder` bridge) because a bot module may not grant a condition. If you have already
  prototyped that bridge under Task H, say so before I write it.

### Counter-demand composition opt-in

Faction lanes can demand-gate a composition by adding `Prerequisites: demand.antiair` (or another
demand name); no C# is needed. The available prerequisites are `demand.antiair`,
`demand.antiarmour`, `demand.antiinfantry`, `demand.detector`, and `demand.artillery`.
Thresholds are On/Off hysteresis pairs: anti-air 25/15, anti-armour 40/30, anti-infantry 40/30,
detector 20/10, and artillery 40/25.

### And one thing I got wrong today, because the protocol says to say it

I ran `git checkout origin/master -- .` in the shared checkout while a merge was in flight —
precisely the command §10.3 forbids. Nothing was lost (the work was in a stash and the branch
commit was intact) and the merge was redone from scratch, but the protocol earned its line the
usual way. **`git checkout -- .` does not "refresh" anything; it is a bulk overwrite of whatever
someone else is mid-way through.**


## 2026-09-10 — source PR340 warhead-family reach measurement

`warhead_family_reach` measures **1,526 distinct fired weapon identities** whose
transitive inheritance reaches a `^Warhead_*` family in the current PR340 source.
(2026-09-23 resync, post-#438: `unconverted_template_inheritors` = **1163**.) **2026-09-23b (post-#456 W23 retrofit): = 827.** **2026-09-24b (post-merge-wave): = 385.** **2026-09-26 (`afb66c9b5`): = 390.** **2026-09-27 (nova post-merge): = 394** (splice-edge mechanics, not new legacy usage). **2026-09-27 (DAWN stack merge): = 391.** **2026-09-27b (#534+#516 combined): `warhead_family_reach` = 1509, `unconverted_template_inheritors` = 395.** **2026-09-27 (#534+#516 merged tree): `warhead_family_reach` = 1509, `unconverted_template_inheritors` = 395** (union of both branches' conversions; splice mechanics, not new legacy usage). **2026-09-28 (post-#252 Scrin pack, `5d7bbd6bd`): = 402.**
The registry's previous value was 1,415; it is updated upward to this measured
count with the same predicate and zero tolerance. Ownership wrappers can expose
more distinct fired identities for existing family payloads: this increase does
not establish newly converted weapons or additional gameplay balance work.
Earlier dated snapshots below remain historical, and the only-UP rule remains.

> **Numeric evidence refresh — 2026-09-10, combined `839cdced4` plus reopened tooling.** `multi_main_fired_weapons` = **120**; `unconverted_template_inheritors` = **1590**. Measured on this combined tree; predicates and tolerances are unchanged. The flat-health denominator correction changes diagnostics, not live weapons or prices. Earlier branch-specific snapshots remain historical. **2026-09-23b (post-#456/#457): `multi_main_fired_weapons` = 1** (`DRPlasmaTankWeapon` only — ruling pending); `unconverted_template_inheritors` = **827**.


## ⛔⛔ 2026-09-07 — READ THIS FIRST: the reference map, and one absolute rule

**SUPERWEAPONS ARE NEVER PRICED, RESTATTED OR TOUCHED** (maintainer, verbatim: *"NEVER CHANGE
THEM!! SO EXCLUDE THEM BEFORE ANYTHING IS CHANGED ON ACCIDENT!!!"*). 32 actors are gated on
`~techlevel.superweapons`; every one whose HP is recorded holds exactly **1,000,000**, which is a
deliberate constant, not a balance figure. Two locks, both landed in `9ad611a6d`:
`reference_distribution.cameo_rows()` drops them from the priced population, and `apply_balance`
**refuses** any ledger edit that touches one. Do not weaken either.

### Where the reference map stands (master `8589e8eb8`)

The maintainer reviewed it three times and rejected it twice. Every reference is now
**name-backed** — shape-only matches are refused outright, after a sniper drew a Velociraptor and
an officer a Triceratops. 63 originals · 77 expanded · 235 references · 4 originals still short.

**The one lesson that generalises**, stated three ways because it recurred every single time:

> The matcher was never choosing badly. **The correct candidate was invisible, or the wrong one
> was recorded despite the scorer already knowing it was bad.** Of ten mappings the maintainer
> called junk: 8 SHAPE, 2 WEAK, **zero STRONG**. Of the ones they called correct: 20 STRONG of 21.
> When a mapping looks stupid, ask what was excluded — not what was chosen.

Defects fixed today, each worth knowing because each was invisible:

| | |
|---|---|
| Armed structures in a `buildings` section were not in the population at all | 38 actors, incl. every TD defence |
| AI-only variants were eligible references (suffix **and** prefix forms) | 122 rows; they are deliberately CHEAPER |
| `~disabled` rows were eligible | OpenRA's dinosaurs, ants, Visceroid — and its `HIND` |
| A direct `Queue:` gate was diluted by a shared prerequisite (`anyhq`) | 15 TD rows incl. Light/Medium Tank |
| An EXPANSION outbid an ORIGINAL for its own reference | `firerocketsoldier` scores **0.867** vs `sovietrocketsoldier`'s **0.850** — the expansion is literally the closer string, so no scorer tuning fixes it. Originals now claim first. |
| `variant_rank` was a whack-a-mole list — held "flame", not "fire" | inverted: a closed list of FACTION words, not an open list of variant words |
| Containment guard measured the Cameo string, not the peer's | `Ant` matched inside `dragunov**ant**imaterialsniper` |
| Sources agree on IDS after renaming, and nothing read it | CA ships `1TNK` as "Scout Tank"; DTA prefixes RA-era actors `RA` (`RAPBOX`) |
| CA states ownership in a DOT SUFFIX (`STNK.Nod`) | its Queue/Prereq tags are useless — see below |
| The report hid variant FAMILIES | a 6-row mapping displayed as one arbitrary pick |

### ⛔ THE BIGGEST REMAINING LEVER — Combined Arms over-tagging

**CA's median row is admissible to FIVE Cameo factions. Every other source's median is ONE**, and
154 of 346 CA rows exceed six. That single fact produced most of what was rejected in both
reviews: a Soviet Tesla Trooper for Nod's laser trooper, Nod's SAM for the Soviet SAM site, an RA1
Allied IFV for a GDI APC, and `allows("td_gdi", TITN)` returning **False** — CA denying GDI its own
walker. **EMBER owns this.** Until it is fixed, `REFERENCE_OVERRIDES` and `FAMILY_EXTRA` in
`tools/balance/` are papering over it with named rows.

### ⭐ 2026-09-08 — the fleet stopped writing and started landing

`docs/FLEET_ORDERS_2026-09-08.md` is the live fleet order set; Codex/Astra's is
`docs/BLACKROBE_ASTRA_ORDERS_2026-09-07.md` (read its §13 addendum first).

The measurement that drove it: **39 unmerged agent branches, ~200 unmerged commits, and zero
merged to master by the fleet.** Four branches were byte-identical duplicates; two agents wrote
competing proposals for the same 268 units and neither shipped.

Landed today, both boot-gated:

| | |
|---|---|
| `devin/ember/w24-lane1` | 22 weapons collapsed to one main |
| `devin/dawn/w24-lane3` | 69 more, ledgers re-extracted on landing |
| **`audit_three_way_split`** | **322 → 231** |

⚠ Lane 3 arrived having changed 10 weapon files and no ledgers, so `audit_balance_drift` went red
across 10 of them. Fixed by `extract_stats.py`, never by hand. **Yaml and ledger in the SAME
commit** is now a standing fleet rule.

W24 queue update (2026-09-22): `devin/nova/w24-lane2` landed as squash-merge
`devin/nova/w24-lane2-v2` `9303d9689` (PR #431 — review-closed by EMBER, verified by DAWN,
resolved-diff clean vs master). `devin/nova/w24-naxi-pilot` is **superseded**: master renamed
the NaxiWW2Machinegun family to the pct-model with two live channels; the collapse would have
halved its damage. DAWN lane-3 then folded the remaining 27 non-RA weapons
(`weapons/outpost2.yaml` x10, D2k packs x8, TiberianDawn/Nod x3, StarCraft/Terran x2,
TiberianSun x4) at `collapse_target.py` totals — shipped totals restored where
the master sum had drifted, twins/companions kept verbatim; `multi_main_fired_weapons`
is now **27** (26 RA-family still in Nova review + `DRPlasmaTankWeapon` (Claude) +
the `tesla_bomb` verbatim exception). **2026-09-23: now 25** — #439 (NOVA batch-1)
landed; PR #452 (NOVA batch-2) folds the RA2Mod set, leaving `DRPlasmaTankWeapon`.
**That last one is Dark Reign's Plasma Tank weapon and is PARKED (maintainer 2026-09-23: Dark
Reign is "something for way later").** Dark Reign is not mounted; the weapon is reachable only
through `^IFVConditions`' `Armament@plasma`, whose `ifv-plasma` condition nothing grants (the whole
`PassengerConditions` block is commented out), so it cannot fire in game. **W24 has no live debt.**

W23-RA status (2026-09-23, Nova, `devin/nova/w23-ra`, PR #472): all 16 owned
RA-family weapon files retrofitted to the 3-way split across 16 boot-gated
batches, then a same-day correction round fixed the audit regressions the
first pass introduced. Final state: repo-wide resolved diff vs master = **0
drifted weapons** (2149 scanned); `audit_weapon_shape` improves on master on
every axis (W1 289/506, W2 122/281, W3 7/12, W4 42/50, W6 675/692, W8 361/672;
W7 963 = master, stale ratchet); orphans 0, empty warheads 0, blocking
dup-inherits 0; boot-gate PASS. Held edges awaiting Claude's ExtraDamage
ruling: Tesla/Laser/Railgun/ChargedTesla + `^LegacyLaserChipCompatibility`,
plus support keeps (`^SniperWeapon`, `^HealingWeapon`, `^RepairWeapon`,
`^DogJaw`, `^NaxOxidationShells`). Correction-round lessons in
`docs/LESSONS_LEARNED.md` ("W23-RA correction round").

### ✅ CLOSED — THE ANTI-AIR CONVENTION. Ruled by the maintainer 2026-09-08.

**The law is now in `docs/DESIGN.md` ("The AA range law", which REPLACES the dual-weapon AA law of
2026-07-11). Read it there — this is a pointer, not a second copy.** In summary:

1. **Three classes only** may carry an AA armament longer-ranged than its ground twin —
   `scout_vehicle`, `armed_troop_transport`, `anti_air_vehicle` — at **1.5×**. `anti_air_vehicle`
   SURVIVES; it is the only vehicle template carrying `AutoTargetPriority@AIR` (defaults.yaml:1829),
   and that, not the range, is its mechanical identity.
2. **Every other class uses one range for both domains.** The maintainer's Mammoth instinct was
   already shipped: every mammoth's cannon and missile pod share a range (6412/6412, 6141/6141,
   6340/6340); no `high_tech_tank` gets the bonus.
3. **`mobile_bunker` is a new (29th) class**, populated by all 16 buildable actors with a resolved
   `AttackOpenTopped`, and it may carry **no air-capable armament at all** — its anti-air is the
   infantry riding inside. Ten of the sixteen are the former `line_breaker` Battle-Fortress family;
   the 22 that stay `line_breaker` are flame tanks, disruptors and brawlers.
4. The 1.5× is **generated** by `gen_weapon_template.py` (`AA_RANGE_MULT`), never hand-typed, and
   enforced by `audit_aa_range.py` as a **LOWER-ONLY ratchet**.

⛔ **AND THE ENGINE ANSWER, so nobody re-derives it.** The maintainer asked whether one weapon could
serve both domains with an air-only range multiplier on the template. **It cannot, mod-side.**
`Armament.MaxRange()` (Armament.cs:215) takes no target; `IRangeModifier.GetRangeModifier()`
(TraitsInterfaces.cs:480) takes no target; `RangeMultiplier` scales every armament on the actor.
Per-target range is resolved one level up in `AttackBase.GetMaximumRangeVersusTarget`
(AttackBase.cs:336), which skips armaments whose weapon is not valid against the target. **The twin
armament IS the mechanism — not duplication to be collapsed.** `Armament` is defined only in
`OpenRA.Mods.Common` (not AS, not CA) and `MaxRange()` is `virtual`, so a Cameo shadow is possible
in principle, but the call site that knows the target lives in `AttackBase`. Feasibility and cost of
that fork are queued to Astra as **C43** — analysis only, no engine change on its strength.

**Implementation queue (C44–C49, full detail in `docs/BLACKROBE_ASTRA_ORDERS_2026-09-07.md` §15):**
generate the 1.5× · write `audit_aa_range.py` · land `^ArmedTroopTransportTemplate` +
`^MobileBunkerTemplate` (BOOT GATE — `defaults.yaml` is engine content) · teach `extract_stats` to
record cargo/fireports · fix the AA detector to cross-check resolved `ValidTargets` · resolve the
three pure-AA units that price at DPS 0.

⚠ **Baseline, measured 2026-09-08, re-measure before acting:** 67 actors carry a live AA armament —
36 at exactly 1.5×, 14 at exactly 1.0×, 14 elsewhere, 3 pure-AA. `scout_vehicle` is already 10 of 10
compliant. Roughly 13 actors need moving, and exactly one `mobile_bunker` (`td_gdi_assaultapc`,
1.500×) must lose its AA gun.

⚠ **The AA detector is a NAME heuristic** (`@AA` slot / `_AA` weapon), not a `ValidTargets` check.
It catches `TSMammothTusk2II_AA` and misses the functionally identical `TSMammothTusk2`. Every
number above inherits that limitation. C48 fixes it.

⛔ **C32 IS CLOSED.** `devin/aurora/fix-anchor-readiness` was never pushed to any remote — it exists
only as a local branch in one checkout — and its `anchor_readiness.py` fix is already on master by
another route (zero `intentional_composite` references; the tool runs clean, exit 0). Astra was
blocked on a branch that no one could reach, and was right to refuse to bypass the gate rather than
treat the absence as permission. The reservation is released; master is the approved starting point.
The same local branch also carries 32 files of LANE-4/LANE-5 classification work that still needs
triage with Aurora — that is separate and unresolved.

<!-- superseded discussion below, kept for provenance -->
### (superseded) the open question as it stood before the ruling

The maintainer asked: *"how can we make it consistent? giving the 1.5x range should be only for
pure anti air vehicles. And if it is a troop transport then those don't count right?"* — and then
paused it deliberately for a clearer head. **Nothing is blocked by it.** Measured state:

```
PURE AA (every armament anti-air):  3 actors        <- the category is nearly empty
Ground gun AND a free AA gun:      63 actors across nine classes
  support 15 (1.50x)  scout_vehicle 10 (1.50x)  anti_air_vehicle 10 (1.50x)
  unclassified 19 (1.00x)  light_tank 2  epic_vehicle 2  line_breaker 1  flying_infantry 1
41 of the 63 sit at EXACTLY 1.50x range; median damage ratio is 1.00
```

**The finding that decides it: 10 of the 11 `anti_air_vehicle` units also carry a ground gun.** A
rule reserving 1.5x for "pure AA vehicles" would apply to ONE actor and strip the bonus from the AA
class itself.

**Two questions were tangled together, and only one mattered:**

* **PRICING — settled and shipped.** An AA armament is free for all 63, excluded from the ground
  DPS everywhere, exactly as the `anti_air_vehicle` anchor already ruled ("priced only on the
  ground weapon"). The anchors derive from ground weapons alone. The pipeline is not waiting.
* **DESIGN — open, and optional.** Whether a troop transport *should* have AA at all is a roster
  feel question. It changes yaml, not the formula.

⚠ The real inconsistency is not the transports: it is the **19 unclassified actors at 1.00x** —
an AA gun with no range bonus. They fall inside the unclassified sweep the maintainer already
deferred until TD/RA1 and Japan are done.

Claude-Local's recommendation on the table: change nothing; record the convention as a GLOBAL rule
(an AA armament is free, same damage, 1.5x range, never priced — it is not a class property), and
revisit the 19 outliers with the unclassified sweep.

### ⭐ 2026-09-08 — SIX MEASUREMENT DEFECTS, ALL THE SAME SHAPE

Every one was a simplifying assumption where the ledger already held the answer. Found by the
maintainer reading the published table, one after another:

| defect | was | is |
|---|---|---|
| `exempt()` asked the CLASS question before the WEAPON question | armed APCs and the Vulcan "chassis-only" | armed is never chassis-only |
| `cameo_rows` took `arms[0]` — yaml order, not importance | `td_nod_lighttankmkii` DPS 0 (its point-defense laser) | 495 of 822 armed actors carry 2+ armaments; 86 reported the wrong one |
| `max()` over armaments | Sheridan 16,000 | simultaneous baseline armaments SUM |
| `live or arms` fallback | siege chopper summed 10 mutually-exclusive barrels to 986,818 | falls back to the strongest single armament |
| `BurstDelay` hardcoded to 5 | right for 78 of 1,017 burst weapons | reads `burstdelays` (3:256, 2:172, 4:160...) |
| the AA test read the SLOT only | `td_gdi_apc`'s `Armament@SECONDARY` firing `APCGun_AA` was invisible | reads slot AND weapon; 41 -> 63 actors |

⛔ And the meta-lesson, because it repeated four times in one day: **a filtered pool made me report
things as missing.** The A10 and X-O "did not exist" (build-limited rows were dropped), 40
references were "lost" (I compared against the non-hero pool), and `assign_references.py` writes
only under `--write` — I read the previous evening's file and reported 30 corrections as failed
when every one had applied. **Check the mtime; check which pool.**

### ⭐ Landed 2026-09-08

* **W24: 322 -> 231 stacks.** EMBER's lane 1 (22 weapons) and DAWN's lane 3 (69) merged and
  boot-gated. Lane 3 arrived with `audit_balance_drift` red across 10 ledgers — yaml changed, no
  re-extract — fixed with `extract_stats.py`. **Yaml and ledger in the SAME commit** is now a
  standing fleet rule.
* **The hero lane** (AURORA), with the `BuildLimit=0` reading corrected: zero is NOT a limit,
  125 corpus rows carry it, and the proposed "fix" would have deleted 110 legitimate actors.
  `td_gdi_commando` claims `RMBO`; `ra1_allies_tanya` claims `E7`/`TANYA`/`E7`.
* **`armed_troop_transport`**, a 28th class. Anchor 50000/100/6000/1200, dps0 400 — four APCs
  across four packs on the same number. ⚠ INERT until `^ArmedTroopTransportTemplate` exists:
  `extract_stats` rewrites `design.class_anchor` to None every run, so SUBTYPE is the only durable
  membership signal.
* **Map: 261 references, O1 8 (ratchet 12), STRONG 756 / FAIR 148 / SHAPE 0 / WEAK 0.**

### ⛔ NOT landed, and why

* `devin/ember/vfi-signature-fix` — **UPDATE 2026-09-22: the O1 objection is resolved.** The old
  head pushed O1 8 -> 13 over ratchet 12; the rebased head `9482cb79d` reports **O1 = 10**,
  identical list to master — master's extractor state absorbed the regression. Rebase kept the
  #350 explicit-root guard + `STATE_REVIEW_COHORTS`; retained: non-production queue exclusion,
  `talon→gdi` side-map fix, RA ant critters recovered into the doc (registered in the test's
  reviewed-removal set alongside d2k `fremen`/`saboteur`). Boot-gated, pushed, ready for review.
* `devin/aurora/ini-pool-hygiene` — the `BuildLimit=0` change above. Rejected with evidence.
* `devin/nova/w24-lane2` — resolved 2026-09-22: rebased and landed as `w24-lane2-v2`
  (`9303d9689`, PR #431). The old branch tips are preserved under `archive/20260913/*` tags.

### ⭐⭐ 2026-09-08 — THE EXTRAPOLATION PROGRAM IS THE PLAN NOW

`docs/design/EXTRAPOLATION_PROGRAM.md` — the maintainer's method, written down with the two
measurements that prove it works. Anchors stop being real actors and become VIRTUAL ones derived
from the reference-mapped originals of TD, RA1 and Japan.

Two findings that settle it:

* **26 of 27 classes have members in TD/RA1/Japan.** Only `dreadnought` has none (its five members
  are StarCraft/naval). Measured through `class_membership.classify()` over 700 classified rows.
  ⚠ Two earlier attempts returned all-zeros and 8-zeros — both bugs in the CHECK, because membership
  is DERIVED from `design.subtype` when no explicit tag exists.
* **The virtual-anchor mechanism ALREADY EXISTS and nothing uses it**: `fit_class.py --spec
  hp,speed,range_wdist,damage,reload,cost0`, *"a round-number model unit that need not exist in
  game"*. `faction_extrapolate.py` (504 lines) likewise already implements the exchange rate. What
  is missing is the INPUTS, not the mechanism.

Why it is right, not a workaround: 23 of 27 real anchors are off their ruled spec, 0 of 27 satisfy
`o0=p0=q0=cost0`, and restatting one actor silently reprices its whole class. A virtual anchor
cannot drift. Phases A–E, owners and gates are in the program document; the approval ledger is §5.

Maintainer rulings, 2026-09-08:
* **Fogged bot observation SHIPS** (AI §9 decision #1, open since the document was written).
* **Astra owns the RA2 + TS reference maps** — every input is committed, no game install needed.
* **Originals are approved faction by faction**, and extrapolation starts per faction on approval.
* **Astra ships CODE.** `docs/BLACKROBE_ASTRA_ORDERS_2026-09-07.md` §14.

### Priority queue

1. **CA over-tagging** (EMBER) — ✅ **MERGED 2026-09-22, PR #434** (`68897e06c`): `"Combined Arms"` added to
   `EXCLUSIVE_ONLY`. The all-houses pool had been admissible to all five routed
   factions at once (186 of 341 rows multi-admit); post-cut rosters are
   90/104/95/75/78, multi-admit drops to 73 (all survivors are the sanctioned
   universal-mobile carve-out), 33 shared-pool CA refs drop, 8 actors go
   formula-only, STRONG share unchanged at 84%. Deny-side complement is #422's
   `peer_faction_sides.json` leaf→side expansion (`talon`→`gdi` restores TITN).
2. **Heroes are invisible on BOTH sides — that, not a missing filter, is why `RMBO` is
   unclaimed.** ⚠ This CORRECTS what this file said earlier on 2026-09-07, and the correction
   matters more than the item. Aurora's `filter_candidate_eligibility.py`
   (`devin/aurora/pool-hygiene-clean`) must **not** be wired as written: measured against the live
   pipeline it removes **0** rows that `reference_distribution.ini_rows()` keeps, and would add
   **699** back (295 build-limited one-offs, 404 with no cost at all). `ini_rows()` already applies
   its exact rule — `cost` AND no `build_limit` AND `buildable` — and applies it more strictly.
   Wiring the side file would LOOSEN the pool, not clean it.
   The real cause is the POPULATION RULE itself (maintainer, 2026-08-30): `cameo_rows()` drops
   every actor carrying a `build_limit`, so **83 Cameo hero/epic combat rows** — Tanya, Boris,
   Volkov, both TD Commandos, Havoc, Kerrigan, Zeratul, Jim Raynor, Chrono Tank, MAD Tank — never
   enter the reference map at all. OpenTD's `RMBO` sits in the peer pool and always did; there is
   simply no Cameo actor left in scope that can claim it, and the same is true of OpenRA RA's
   `CTNK`.
   ⭐ **RULED 2026-09-07 — the HERO-ONLY REFERENCE LANE.** Heroes stay OUT of every ordinary
   distribution (the population rule is unchanged, and the 3,000,000 HP epic never re-enters the
   vehicle ceiling), but a Cameo hero MAY match a peer hero, so `td_gdi_commando` claims `RMBO`
   and `ra1_allies_chronotank` claims `CTNK`. References only — **no hero is ever priced by the
   ordinary formula.** Implementation is the fleet's: a hero flag carried on the row rather than a
   drop, `peer_rows()` keeping its exclusion for distributions, and `assign_references` matching
   hero-to-hero only. 83 Cameo actors and 295 peer heroes are in scope.
   ✅ **LANDED** — the lane exists on master: `peer_hero_rows()` /
   `cameo_hero_rows()` (`reference_distribution.py`), hero-to-hero-only gate +
   two-pass design in `assign_references` (hero lane runs after the non-hero
   pass so no ordinary mapping shifts). Verified live: `td_gdi_commando` and
   `ra1_allies_chronotank` each claim their Commando/Chrono Tank peers across
   3 sources at STRONG.
3. **Aliases for the 9 short originals** (ECHO) — ✅ **MERGED 2026-09-22, PR #436**
   (`e1e7319ca`, discharged by EMBER after ECHO's slot stayed unclaimed 14 days).
   Three verified same-unit gaps closed — `flamethrower`+OpenRA `E4` "Flame Infantry"
   (NAME_ALIASES), `ts_gdi_lightinfantry`+SP `GDIE1`/CN `GASOL` "Marine" (ID_ALIASES,
   id-scoped), `gatlingtank`+DTA `SHILKA` completing the documented MFLAK ruling.
   O1 gating 8->7, O2 gating 6->5, zero existing assignments displaced. The
   exhausted/unsettled rows are documented in the PR for maintainer adjudication.
4. **Sign the 27 class anchors** (CODEX) — 0 of 27 signed, and `apply_balance` therefore refuses
   every faction. This, not writer safety, is what blocks the whole pipeline.
5. **Then: the faction-calibration method for expansions** — anchor on originals, derive the rest
   (class anchor × tech tier × faction factor). Maintainer wants **Japan** as the first test,
   precisely because it has no reference data.

### Open questions the maintainer has not answered

* **Is Romanov's Vengeance the RA2 authority?** It carries 729 buildable units; RA2 + YR never
  shipped that many. It is 104 of 119 unclaimed "originals", and O2 currently reports it without
  gating on it. That exemption must be DELETED when ruled, never raised.
* **TD naval** — GDI and Nod ships exist in DTA and CA and Cameo has none mapped.
* Missing actors the maintainer named: **RMBO / E7 (Tanya)**, CA's Chinook, Specter, Venom.

---


**2026-08-25 update (Devin AI):** The volcanic shellmap (`shellmap_v3.oramap`) camera was too tight (6-cell radius), hiding the scripted attack waves. The `attack.lua` camera radius was widened to 45 cells. **Superseded 2026-09-16:** reverted to 6 cells (`03049aada`) — at 45 cells the camera centre travelled up to 45 cells from `camerapoint` while the three scripted battle waypoints sit only 14–20 cells away, so the fight left the frame for much of the 144 s revolution. See the 2026-09-16 entry in `DEVELOPMENT_LOG.md`. The boot-blocking stale removal `-Warhead@CannonHE_MediumPercentage` in `weapons/outpost2.yaml` is resolved in `a92ae850`, and boot-gate passes with no new exceptions. See `DEVELOPMENT_LOG.md` § "Volcanic shellmap camera radius fix" for evidence and verification.

**This is the single entry point for anyone picking up work on Cameo — human or agent.**
Written 2026-08-23, re-verified against master at `e60aab63`. It supersedes every previous handoff document;
those are archived under [`history/handoffs/`](history/handoffs/) and must not be resumed from.

| you want to… | go to |
|---|---|
| know what to do next | §3 below, then [`design/ROADMAP.md`](design/ROADMAP.md) |
| know the balance program's state and who owns what | [`design/BALANCE_PROGRAM_PLAN.md`](design/BALANCE_PROGRAM_PLAN.md) §0, §0a, §1, §2 |
| know a binding rule before editing yaml | [`DESIGN.md`](DESIGN.md) |
| avoid a trap someone already hit | [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md) |
| know how the bots are meant to work, and what is only designed | [`design/AI_ARCHITECTURE.md`](design/AI_ARCHITECTURE.md) |
| know the current bug counts | [`audit/SUMMARY.md`](audit/SUMMARY.md) |
| find which document owns a topic | [`README.md`](README.md) |
| **you are the Blackrobe GPT-6 Astra Agent** | ⭐ [`BLACKROBE_ASTRA_BRIEF.md`](BLACKROBE_ASTRA_BRIEF.md) — your complete single-prompt instruction set |

---

## ⛔ 2026-09-07 — the reference map, and what it cost to make it trustworthy

**master `57d7d7858`.** The maintainer reviewed a TD/RA1 reference map and rejected it:
`ra1_allies_rifleinfantry` was mapped to a **Cryo Trooper** when all three sources ship an E1.
Seven silent defects, each individually sufficient — full list in
`memory: cameo-reference-defect-cascade`, the essentials here.

⭐ **THE LESSON.** The matcher was never choosing badly. **The correct candidate was deleted
from the pool before matching**, and the greedy picked the best of what remained. Every wrong
pairing looked like a scoring bug and was a visibility bug.

⛔ **A "verification" that reads a crashed run's output verifies nothing.** `factions_of` lost
its `vfi` parameter in a merge, so every OpenRA extraction raised TypeError and was swallowed
per-mod; my splice then copied the unchanged file back and I reported the fix working.

**THE ACCEPTANCE TEST** (maintainer, verbatim): *"All the original units are in OpenRA. DTA, CA
and Cameo all expand the roster... those that exist in OpenRA and OpenTD MUST ALWAYS HAVE 3
REFERENCES."* Encoded as `audit_original_coverage.py`. **O2 — an original nobody claimed — is
the check that matters**; a voice count cannot see it.

**OPEN QUESTION, unanswered:** Romanov's Vengeance carries **729 buildable units**. RA2+YR never
shipped that many, so RV expands the roster like CA and DTA do. `OpenRA RA2 official` (86) and
`Yuri's Revenge on OpenRA` (124) match the real rosters. Which is the RA2 authority?

**NEXT, in order:**
1. Work the O2 list — **every Tiberian Dawn defense is unclaimed** (Obelisk, Guard Tower,
   Advanced Guard Tower, Turret, SAM), plus RA1's Tesla/Chrono tank and Demolition Truck.
2. Settle the RA2 authority, then re-baseline O1/O2.
3. The regen conversion (892 nodes, delegated, `devin/regen/conversion`) — **Claude-Local flips
   `defaults.yaml` LAST and merges whole**, or master double-heals.
4. The faction identity modifier to break byte-identical mirrors — magnitude not yet set.

⚠ **No balance number has been written to yaml.** Nothing is applied until the map is right.

## ⭐ AGENT ASSIGNMENTS — who is doing what (2026-09-06)

| agent | lane |
|---|---|
| **Blackrobe GPT-6 Astra** | ⭐ **FINISH THE BALANCE PIPELINE** (Tasks A–G) **and inherit the AI bot modules** (Task H — Devin Cloud ran out of quota mid-merge). Full brief: [`BLACKROBE_ASTRA_BRIEF.md`](BLACKROBE_ASTRA_BRIEF.md). Branch `astra/balance-pipeline`, never master. Has **full authority including `apply_balance --confirm`**, conditional on one commit per decision and a review dossier at `audit/ASTRA_REVIEW.md`. |
| **Aurora** (lane retired; Ember regenerated) | `ra2_allies` + `ts_gdi` — **DONE 2026-09-23** on `devin/ember/rename-ra2ts` (8 actors + 57 assets, regenerated not cherry-picked). `ra1_allies` — held for NOVA's `RELEASE_redalert.md`; the 16 Allies sprites wearing Soviet names ride with it → `../Cameo-mod-fleet/TASK_2026-09-06_aurora.md` |
| **Ember** | `asianalliance` — **DONE 2026-09-22**: `naming-asianalliance` `0ce8783b9` rebased + pushed (43 actors, 57 assets, ledgers re-extracted, docs propagated; boot-gated). Awaiting review/landing → `TASK_2026-09-06_ember.md` |
| **Nova** | `ra1_soviets` — **94 items**, incl. the fluent-key leak and the 19 doubled filenames → `TASK_2026-09-06_nova.md` |
| **Dawn** | `latinsyndicate` + `steelconsortium` + `wc2_*` + `zerg` — **79 items** → `TASK_2026-09-06_dawn.md` |
| **Echo** | `ixian` + `ordos` + `d2k` + `japan` — **68 items** + the mod's last hyphen → `TASK_2026-09-06_echo.md` |
| **Blaze** | `atreides` + `corrino` + `harkonnen` + `futuretech` + `yuri` — **32 items**, incl. **14 of the 15 actor-id renames left in the whole mod** → `TASK_2026-09-06_blaze.md` |
| **Claude-Local (Opus 5)** | rulings, review, squash-merges to master, and the gates |

⚠ **Nobody merges to master except Claude-Local.** Agents commit freely on their own branch
and report a completed work item; Claude reviews and squash-merges one meaningful commit. The
maintainer must be able to read master — 107 commits in one day, 49 of them touching only
`DEVELOPMENT_LOG.md`, is not reviewable.

### ⛔ 2026-09-07 — four bugs shipped past every gate; three new audits + one hook rule

**The maintainer found the worst one by playing**: the mutalisk's fire shrapnel bounced
forever. Root cause for two of the four, and it is now `CLAUDE.md` rule 8g:

> **`-Key@X:` in a child CANCELS what an ANCESTOR defines.** It looks dead precisely
> because the node it sits in does not define X.

`d818aec40` deleted 2248 of them as "stale": multi-main weapons **461 → 1103**, and 14
deleted `-Warhead@shrapnel:` terminators made the spore loop forever. **Nothing
crashed** — a boot gate proves the rules PARSE, never that they are RIGHT. Reverted in
`ad6fc66b8`, ledger re-extracted in `a6525d6fb`.

| new gate | catches | ratchet |
|---|---|---|
| `audit_shrapnel_chains.py` | a FireShrapnel chain that never ends | S1a **0**; S1b **0** — 44 self-cycles were the same damage; fixed in `7b63045fd` |
| `audit_map_actors.py` | a map placing an actor the rules do not define (boot gate is blind: it fails when the map is STARTED) | M1 **0** |
| `bash_guard.py` rule 4 | deleting a `-Key@...` without `RESOLVE-VERIFIED` in the message | — |

Also fixed: `audit_naming_damage`'s regex could not see a doubled id (reported N1 4 /
N2 0 against the true 25 / 16 — an exact zero is always suspect), and the boot-gate
hook read the MAIN checkout's index from every worktree, which would have waved
through engine content committed from a worktree. Both now have self-tests.

✅ **RESOLVED 2026-09-07 — they were not old debt, and they are fixed.**
`ad7c5e232` (labelled a *rename*) also stripped **236 removal nodes** out of
`RedAlert/Soviets/yaml/weapons.yaml`, and the tesla fragments' `-Warhead@TeslaArc:`
terminators were among them. Restoring all 236 (`7b63045fd`) took **S1b 44 → 0**;
the ratchet is now 0. Every FireShrapnel chain in the mod terminates: 193 weapons,
193 chains, zero cycles of either kind. No in-game test needed.

⚠ **I was wrong about these twice, and the second time is the instructive one.** First
I called them benign chain lightning — reasoned from field names, not the code. Then I
called them pre-existing debt because *"all 44 predate `d818aec40`"*. That was literally
true and still the wrong conclusion: **the bisect stopped at the first commit that showed
the problem instead of walking back until it disappeared.** One commit further back was
the actual cause. When bisecting, walk back until the symptom is GONE, not until it
first appears.

Full write-up for agents: `../Cameo-mod-fleet/BRIEF_2026-09-07_what_broke_and_the_new_gates.md`.

### ⭐ Naming — the real state, measured 2026-09-06 (replaces every earlier count)

`python tools/audit/audit_naming_damage.py` is the source of truth and is now in
`run_all.sh`. Six pathologies, six **lower-only** ratchets, all currently PASS:

| code | pathology | count | lane |
|---|---|---|---|
| N1 | a filename carries one actor id **twice** | 25 | Nova 19, Aurora 4, Dawn 2 |
| N2 | a filename carries **two factions'** ids | 16 | Aurora — all 16 are RA1-Allies sprites wearing Soviet names |
| N3 | a **fluent key** became an actor id | 5 | Nova |
| N4 | the faction named **twice** (`ra1_allies_alliedaagun`) | 345 | split per faction |
| N5 | dotted id that is not a sanctioned `.husk` | 161 | split per faction |
| N6 | a hyphen (rule 9) | 1 | Echo |

**Three earlier numbers were wrong and are retired:**

* the **526-actor backlog** was a doubled game prefix in one config table — seven of eight
  factions jumped **0% → 100%** when it was fixed;
* the **144 dotted renames** undercounted; the real figure is **161**, and separately
  **234 `.husk` ids are LEGAL** (`DESIGN.md` line 71 sanctions dotted `.husk` variants), so
  the raw 398 must never be quoted as backlog;
* **`.nax` / `.nax2` are DONE** — 0 remain. Nova landed them.

Actor-id work left in `gen_rename_maps` is **15 actors total**: `atreides` 21/23,
`corrino` 22/25, `harkonnen` 27/35, `ixian` 60/65. Every other faction reads 100%.

⚠ **A 100% row there is not proof a faction is clean.** That report sees only
faction-exclusive **buildable** actors, and `startswith(prefix)` is satisfied by
`ra1_soviets_sovietairfield` too. `asianalliance` reads 73/73 while holding 27 dotted and
73 redundant-word ids. Use `audit_naming_damage.py` for the real number.

⛔ **`gen_rename_maps.py --files` is opt-in and `--out` is mandatory practice.** Six defects
were found in its file half on 2026-09-06 (commit `c9437f4f8`); a regenerate proposed **842
file renames, 92 corrupt**, now **44, none corrupt**. Without `--out` a run **overwrites every
`tools/rename/rename_map_*.yaml`**, including hand-corrected ones. See `LESSONS_LEARNED.md`
"Fix the TOOL, not its output".

### AI bot modules — state as of 2026-09-06

Devin Cloud designed the module architecture and stopped mid-merge when its quota ran out.
**The design is landed, not lost:**

* **PR #324 is MERGED** — [`design/AI_ARCHITECTURE.md`](design/AI_ARCHITECTURE.md) **§10** (the
  per-module build plan, the shared snapshot, the one synced piece, and the 7-phase build
  order) and **§11** (the reconciliation of the first five-agent research round, with rejected
  claims and what falsifies each).
* **PR #323 was MERGED 2026-09** (this entry predates the merge) — Observer Combat Effectiveness graph, +233/−12, and it
  touches C#, so it needs a `dotnet build` and a boot gate, not just a merge. **Assigned to
  Astra, Task H.1.**
* ⚠ `gh` defaults to the wrong remote in this checkout — always pass
  `--repo cameo-mod/Cameo-mod`.
* Next implementation step is **phase 1: record-only match logging.** Phases 1–2 carry no
  gameplay effect and may run while the balance pipeline is still moving; **phase 6 (fog) is
  deliberately last** because it weakens the bots and invalidates any tuning done before it.

⚠ **If you are a Devin agent, your task file is `../Cameo-mod-fleet/TASK_2026-09-06_<you>.md`**
and the index is `TASKS_ACTIVE.md`. Each task file is self-contained: your complete item list,
the method, the faction-specific traps, the gates, and the report format. Read
`BRIEF_2026-09-06_naming_damage.md` once for context before you start.

⚠ **Agent-to-agent chatter lives OUTSIDE the repository**, in `../Cameo-mod-fleet/`.
`DEVELOPMENT_LOG.md` keeps one entry per COMPLETED work item plus lessons learned — nothing else.

## ⭐⭐ START HERE 2026-09-07 — why the balance pipeline has not moved, and the fix

```
$ python tools/balance/apply_balance.py --faction d2k_atreides
DRY RUN: 0 values would change
```

**The pipeline is not blocked by tooling, by W11, or by sign-off. It is idle because nobody
has written a target number into the ledger.** `apply_balance` writes ledger → yaml; the
ledger holds today's values; applying it is therefore a no-op *by construction*.

`anchor_readiness.py` reports **0 of 27 classes signable**, 26 failing "the anchor does not
describe its members" (median pricing error 15%–106%) — and explains itself in one line:
*"the anchor actor is still PRE-RESTAT, so its percentile is measured on stats the design
already intends to replace."*

Meanwhile **all 27 classes already carry a complete spec** in `docs/balance/class_anchors.json`
(`cost0`, `dps0`, `hp0`, `range0_wdist`, `speed0`) that has never been used. `mbt`'s spec is
hp0 **240,000**; the actual unit has **100,000**. The numbers were designed and never written
anywhere the pipeline reads.

⭐ **MAINTAINER ORDER, 2026-09-07 — do this first:**

1. Write the 27 anchor specs into the ledger on **`hp0` / `speed0` / `range0_wdist` / `cost0`
   only**. ⛔ **NOT `dps0`** — it depends on weapon structure and therefore on W24, and would
   be written twice.
2. `python tools/balance/apply_balance.py --faction <f> --confirm`
3. Boot-gate, re-extract, then re-read `anchor_readiness.py`.

This is the first real balance change the project will have made, and it breaks the apparent
circularity (sign-off needs a restat; the restat needs numbers in the ledger — which is a
LEDGER edit, explicitly sanctioned by CLAUDE.md rule 3, not a hand edit of yaml).

⚠ The four non-DPS axes depend on nothing but the unit, so **W24 is not a prerequisite for
this.** The two can run in parallel: the restat writes `docs/balance/*.json` → actor yaml,
W24 writes `**/weapons.yaml`, and `extract_stats.load_existing_design()` preserves authored
`design.*` across re-extraction.

## ⛔⛔ TOP OF THE QUEUE 2026-09-07 — revert the ra1_soviets rename

**All 32 actor renames `ad7c5e232` applied made the id LONGER and WORSE. Not one
improvement in the set.** Full write-up and the revert procedure:
[`design/RA1_SOVIETS_RENAME_REVERT.md`](design/RA1_SOVIETS_RENAME_REVERT.md).

```
ra1_soviets_barracks              -> ra1_soviets_sovietbarracks
ra1_soviets_constructionyard      -> ra1_soviets_sovietconstructionyard
ra1_soviets_attackdog             -> ra1_soviets_actordogname      (a FLUENT KEY)
ra1_soviets_doctrine_conscription -> ..._doctrine_conscriptiondoctrine
ra1_soviets_upgrade_hammertank    -> ..._upgrade_hammertankupgrade
```

The tech markers are **duplicated** — `doctrine_X` became `doctrine_Xdoctrine`. That is
what a mechanical rename looks like when nobody reads three lines of the proposal.

**The cause is already fixed** (`c9437f4f8` defects C and E), so the corrected generator
now proposes the ORIGINAL ids — the revert target is what the tool produces, not a
judgement call. It has already cost: 7 broken `.oramap` files including both shellmaps
(two tester crashes), 236 deleted removal nodes, and 69 of the 345 N4 findings.

⛔ **Do not batch this with another rename.** It touches both shellmaps; boot gate is
mandatory.

**The rule it earns: a rename that makes an id LONGER is a regression until proven
otherwise.** A batch that raises N4 has failed, whatever its compliance percentage says.

✅ **2026-09-24 residue cleanup (EMBER):** the actor half was long since corrected —
ids are 106/106 compliant — but the bad rename's damage survived in sequence names
and filenames (`ra1_soviets_sovietbarracks` seqs, `actordogname` files,
`upgrade_*upgrade`/`promotion_unlock*` doubled stems, `sovietX_ra1_allies_alliedY`
compounds). Cleared by `tools/rename/rename_map_ra1_soviets_n134.yaml` — 14 sequence
ids + 83 asset files, zero dangling refs, faction N1/N3/N4 all to 0. The stamped
`rename_map_ra1_soviets.yaml` stays DO-NOT-APPLY.

## ⭐ NEW WORK SPECIFIED 2026-09-07 — two maintainer orders, neither built

Both are written up in full, with the state verified rather than assumed. Neither is a
naming-lane task; both are self-contained and neither outranks the balance pipeline.

### 1. Paired effect+sound templates — [`design/EFFECT_SOUND_TEMPLATES.md`](design/EFFECT_SOUND_TEMPLATES.md)

One inherit must carry the visual **and** its sound, named after the source game and the
effect's own file name (`^d2k_big_explosion`), so the two can never drift apart.

Measured: **6987** CreateEffect warheads, only **4008** carry both halves, and **68**
sprites are each used with more than one sound. The reported symptom is located exactly —
`D2K_Rocket_Trooper` pairs the visual `d2k_tiny_explosion` with the sound
`xplobig4.aud` (a BIG explosion sound on a TINY sprite), and its four variants have four
different pairings, one of them borrowing a RA/TD sound for a D2k visual. Those five
weapons are the acceptance test.

### 2. Colour-picker preview for every faction — [`design/COLORPICKER_PREVIEW.md`](design/COLORPICKER_PREVIEW.md)

**BUILT 2026-09-22 (Ember, `devin/ember/colorpicker-preview`)** — two Cameo shadows
(`RenderSpritesInfo` + `ColorPickerManagerInfo`), data-derived faction→conyard lookup,
three new picker palettes, four dead clones deleted. Details in the spec doc.

⚠ **The believed state was wrong.** TD/RA/Japan were not "done": `fact.colorpicker`,
`rafact.colorpicker` and `rafactj.colorpicker` exist but are **dead — nothing references
them**, there is **no `FactionPreviewActors` block anywhere**, and every faction currently
previews a Soviet mammoth tank.

The engine already has `FactionPreviewActors` (zero C# needed), but using it as-is means
~31 clone actors. The better build is a **`RenderSprites` shadow in `OpenRA.Mods.Cameo`**
honouring `ActorPreviewType.ColorPicker`, so any actor is its own preview — **route
confirmed open**, since neither AS nor CA defines `RenderSprites`. No engine fork.

## 0. The one rule that makes all the others work

**Don't trust — verify.** Before you assert that anything is done, pending, blocked or missing:
grep the data, `ls` the file, run the tool, boot-gate the tree. When a summary (a ROADMAP line,
a status table, an older handoff, this file) disagrees with the artifact, **the artifact wins —
and then you fix the stale summary in the same commit.**

This is not a slogan. The 2026-08-23 documentation pass found, by running the tools:

* five pinned numeric claims had drifted from the tree, and one gate (`audit_balance_drift`) was
  RED while the committed report said "clean" — the report was three commits stale;
* `docs/audit/latest/` held **two** copies of every report under different names, because the
  repo had two audit runners with different filename conventions;
* `DESIGN.md` used the section id **§12.0a twice**, for two different binding laws;
* the retired 2000-step damage grid was still taught as law in eight documents, one skill and
  one audit script, four days after `formula.DAMAGE_STEP` became 100;
* eight board statuses in `BALANCE_PROGRAM_PLAN.md` contradicted that same file's own per-item
  headings.

None of that was visible by reading. All of it was one command away.

### Verify a claim, not a hash

Cloud and CI checkouts of this repo are **shallow** — `git log` starts at 2026-08-10, so
`git show <older-hash>` fails on most hashes the docs cite. That is a property of the checkout,
not of the history: the commits exist upstream. Either run `git fetch --unshallow` first, or
(better) verify the claim against the artifact — which is what §0 asks for anyway.

### Two more things you cannot resolve from the repository

* **`memory <name>` citations.** 36 references across the design docs point at an external,
  per-agent memory store. Nobody else can open them. Treat every one as **provenance only,
  never as authority** — if a memory carried a binding rule, that rule needs to be promoted
  into `DESIGN.md` before it counts.
* **`engine/` is not in this repository.** It is `.gitignore`d, has no `.git`, and
  `git ls-files engine` returns zero. Editing `engine/**` produces work that cannot be
  committed here and is deleted by the next `make all`. See §5.

---

## 1. Where the project actually is (verified 2026-08-23)

**The mission.** Cameo is a crossover RTS spanning the classic RTS games. The architectural goal
is **dynamic faction loading** — load only the factions the lobby picked, instead of everything
at boot (historical peak: 12 GB RAM, unplayable on 8 GB machines). Every faction therefore
becomes a self-contained ContentPack. Runbook: [`MIGRATION.md`](MIGRATION.md).

**Health.** Green, with one red that needs a maintainer decision rather than work.

| | |
|---|---|
| crash-class content (B8) | **0** |
| empty warhead types (boot NRE class) | **0** of 2765 weapons |
| dangling weapon refs / dangling inherit targets | **0** / **0** |
| `tools/tests` | **286 tests, all green** |
| cross-document consistency audit | 73 passed, 0 failed |
| balance-ledger drift | **0** — master re-extracted in `31e649b8` |
| pinned doc claims | **19 of 19 match** |
| generator sync | drift **0** across 136 shared templates |
| documentation structure (`audit_doc_health`, D1–D8) | **0** findings |
| heaviness bell | **0 inversions, 0 mean drift** across 48 families; 2 flat (`Sonic`, `Magic`) at ratchet 2 |
| `audit_doc_health` | ✅ **PASS** — the D8 self-flag was fixed 2026-08-23 |
| `environment.py` | ✅ reports a complete tree — the CA path was fixed 2026-08-23 |
| **suite exit code** | **1**, and legitimately so — 8 gating audits report real content defects (§3.3's backlog). The 5 SCHEDULED scans that also reddened it are now ADVISORY. See §3.0c |
| physical-state warheads | ✅ **PASS** — the audit demanded percentage TWINS the AreaDamage fold folded away; six false failures, fixed in the audit not the yaml |
| `audit_test_coverage` | 269 untested vs baseline 224 — **advisory**, and recorded debt. `T3_BASELINE` deliberately NOT raised |

⚠ The counts above were re-measured at `519175ae`; the per-class counts in
[`audit/SUMMARY.md`](audit/SUMMARY.md) come from the last full suite run and carry the
mixed-environment caveat described there.

**The active front is the weapon rebuild, and pricing is deliberately NOT running yet.**
`BALANCE_PROGRAM_PLAN.md` §0a is the binding order, and the reason is measurable: a price is a
function of `K`, `K` is built from a weapon's warhead set and their `Versus` profiles, and both
are still scheduled to change across most of the roster. Pricing now means pricing inputs that
are about to be replaced.

```
W24  one damage warhead per weapon          122 directly fired weapons still carry 2+
 └─> W23  retrofit the legacy templates      1592 direct inheritors
 │        (source339 2026-09-10 raw counts; 234 was the historical 2026-09-07 reachable count)
 │        (its old "33-collision" blocker
 │         is DISSOLVED — W24 removes it)
 └─> A5   retire the remaining inline-Versus weapons onto templates
      └─> class anchors → fit_class per class → W11 maintainer sign-off
           → targets written into the ledger → apply_balance --confirm → boot gate
```

⚠ **`apply_balance --confirm` is a NO-OP until targets are written into the ledger, and that
needs W11's sign-off.** Signed-off class anchors today: **0**. So no price in the tree is final,
and "run `--confirm`" is never the next step on its own.

Independent of that chain (different file sets, safe in parallel): the physical-state meter
items **W7, W9, W10**, and the superweapon track **W12**.

---

## 2. Before you touch anything

Read, in this order. This is the canonical order; [`README.md`](README.md) is its definition and
wins over any copy of it.

1. [`CLAUDE.md`](../CLAUDE.md) — the hard rules, loaded every session.
2. [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md) — the traps, each one paid for.
3. [`AGENT_WORKSPACE.md`](AGENT_WORKSPACE.md) — workflow, evidence rules, commit gate.
4. **this file** — current state and the queue.
5. [`DESIGN.md`](DESIGN.md) — the binding contract. Read the sections your change touches.
6. [`design/ROADMAP.md`](design/ROADMAP.md) — the granular queue.
7. [`audit/SUMMARY.md`](audit/SUMMARY.md) — current counts by bug class.

Then the topic doc for your task, from the table in [`README.md`](README.md).

### The ten hard rules, in one place

Rules 1–2 are enforced by hooks in `.claude/settings.json`.

1. **Boot-gate every commit of engine content.** `launch-game.cmd` must reach the main menu:
   `perf.log` ends with `MenuPostProcessEffect.PostWorldLoaded`, and no NEW `exception-*.log`
   in `%APPDATA%/OpenRA/Logs`. Snapshot the log list **before** launching. Menu proof is
   grepping `perf.log`, not eyeballing its last line.
2. **Scoped `git add <files>` only — never `-A`, `.` or `--all`.** Other contributors have live
   uncommitted work in this tree.
3. **Never hand-edit a balance number.** Use the pipeline: `extract_stats` → ledger →
   `apply_balance --confirm`. `--confirm` requires a maintainer order.
4. **`Versus` lives ONLY in `^Warhead_*` templates.** Never change a warhead, `Burst` or
   `BurstDelays` without explicit permission.
5. **Weapon 3-way split:** preserve resolved behaviour (`Damage` verbatim, projectile fields),
   `find_empty_warhead.py` = 0, boot-gate per batch. Verify with
   `tools/audit/review_resolve_diff.py` (resolve before and after).
6. **One owner per file-set.** Check a file's mtime and `git log -3 <file>` for a live agent
   before editing. Re-verify others' commits before building on them. Never
   `git checkout -- .` or wide-add someone else's work.
7. **Rebuild C# before booting** if `OpenRA.Mods.Cameo/` or `engine/` changed. Stale DLLs crash
   the boot with `Cannot locate type: …Info`. See §5 for the engine pipeline.
8. **Audit reports regenerate via `bash tools/audit/run_all.sh` only** — a PowerShell `>`
   redirect writes UTF-16 and corrupts them.
9. **Underscore-only naming** — no hyphens in ids, files or fluent keys. (The single
   deliberate exception is the `cameo-content` installer mod, which must match the engine's
   `*-content` convention.)
10. **Sign the commit trailer with your OWN identity and your REAL model name** —
    `Co-Authored-By: Claude <model> <noreply@anthropic.com>`. The git author is a shared repo
    identity, so the trailer is the only provenance signal. **Never copy a trailer from a
    previous commit or from CLAUDE.md** — those are templates, and copying one makes a newer
    model misreport itself as an older one. A non-Claude agent signs as itself
    (`Co-Authored-By: Devin AI <devin@cognition.ai>`) and never appends the Claude trailer.

### The gate before every commit

```sh
python -m unittest discover -s tools/tests -t tools/tests   # all green (227 as of 2026-08-23)
python tools/audit/find_empty_warhead.py                    # 0
python tools/balance/verify_generator_sync.py               # ⛔ drift = 10 today; only
                                                            # ^Warhead_Sniper_Light is accepted
bash tools/audit/run_all.sh                                 # bash ONLY
python tools/balance/extract_stats.py --check               # 0 drifted
```

…then the boot gate (rule 1). If Windows Smart App Control blocks the launch, use one of the
four documented options in `LESSONS_LEARNED.md` § Smart App Control and **record the SAC state
in the commit message**. Never silently skip the gate, and never claim it passed when it did not.

`utility.cmd cameo --check-yaml` is a **separate lint tool**, not a boot-gate substitute. It
takes 10+ minutes; run it once you have finished a batch and expect 0 errors and 0 warnings —
not repeatedly.

---

## 3. The queue, in priority order

Crashes and player-visible regressions jump everything below.

### ⭐ LIVE LANE — warhead/armour reference averaging (Claude, updated 2026-09-23)

**ON MASTER since 2026-09-23** (landed from a clean branch, `claude/warhead_reference_lane`; the old
`claude/warhead_reference_R39_R53` was cut from an unmerged naming branch and must NOT be merged —
it also carries AURORA's 09-07 ra1_allies/ra2_allies/ts_gdi rename, which is handed to EMBER
separately).

Read [`design/REFERENCE_EXTRACTION_PLAN.md`](design/REFERENCE_EXTRACTION_PLAN.md) **R39-R62** (the
binding rulings) then [`design/WARHEAD_REFERENCE_HANDOFF.md`](design/WARHEAD_REFERENCE_HANDOFF.md)
(lane state and the per-source procedure). Coverage prints from
`python tools/reference/assignment_store.py`.

State: **10 of 17 sources assigned, 2,220 of 2,554 weapons (87%).** Combined Arms is
maintainer-REVIEWED; the other nine are `proposed`. Next: `dta_enhanced` (needs a DTA mode in
`tools/reference/ini_lookup.py` first — DTA is read by `read_dta`, not `parse_ini`).

⚠ Extractor fixes in the lane (R48, R50, R51, R54, R56, R58–R60) changed the measured corpus, so
anything downstream of `warhead_groups.json` computed before 2026-09-23 is stale.


### 3.A — MULTI-AGENT COORDINATION (read this FIRST if you are an AI agent)

**As of 2026-08-25, there are 5 Devin AI agents running locally.** Each agent MUST:
1. Pick a unique name from the list below (or claim a new one in `DEVELOPMENT_LOG.md`).
2. Read `DEVELOPMENT_LOG.md` §"Active claims" BEFORE editing any file.
3. Claim a file-set by adding an entry to `DEVELOPMENT_LOG.md` §"Active claims" BEFORE editing.
4. NEVER edit a file that another agent has claimed or that is in the locked list.
5. After every step: update `DEVELOPMENT_LOG.md` with what you did, why, and what's next.
6. Before committing: run verification (find_empty_warhead, audit_warhead_split,
   review_resolve_diff, audit_doc_claims) and boot-gate (`launch-game.cmd`).
7. Use scoped `git add <files>` only — never `git add -A` or `git add .`.

#### Agent roster and current assignments

> ⭐ **THIS IS THE ONLY AUTHORITATIVE ROSTER.** Three other ownership tables exist
> lower in this file (D2k faction completion, §3.C, §3.6); all three are marked
> SUPERSEDED and contradict this one. Claim file-sets from HERE and nowhere else.

> **⚠ FLEET HIERARCHY (maintainer order 2026-09-05):** *"Claude AI is now your big
> boss and controls all other AI Agents so you must always listen to him and do
> EXACTLY as he says!"* — **Claude (Opus 5, local) is the fleet coordinator.** All
> agents take direction from Claude. Aurora remains D2k coordinator **under Claude's
> authority.** Claude has not yet issued consolidated fleet-wide orders in his
> coordinator capacity; until he does, agents continue their established roles below.

| Agent name | Status | Current task | Files claimed |
|---|---|---|---|
| **Claude** (Opus 5, local) | **Fleet coordinator** (maintainer order 2026-09-05) | ✅ Reference-pipeline tooling landed (`85bcf3f33`). ✅ 7 reference mods extracted (8183 unit rows). ✅ Master fast-forwarded 113 commits. **AWAITING: issue consolidated fleet-wide orders. Rule on 4 open items: (1) ordos_laserturret "unique and special" mechanical spec, (2) heaviness bell — refold existing level templates now or later?, (3) composite registry re-curation priority, (4) CannonTesla family under single-warhead ruling.** | `tools/reference/**`, `tools/balance/{assign_references,faction_routes,faction_extrapolate}.py`, `docs/balance/review/**` |
| **Devin-Dawn** (was Devin-Prime) | Active — **D2k weapon closure** | INI lane COMPLETE: PR #365 MERGED (`audit_ini_untagged.py` + `ini_untagged_breakdown.md`), Codex #353 extractor MERGED; breakdown re-verified byte-identical on current master. Wraith boot blocker RESOLVED (PRs #354+#361 merged 2026-09-13). NEW: `devin/dawn/d2k-weapon-closure` PR #411 — drained every live-referenced weapon from legacy `weapons/d2k.yaml` into the D2k packs (23 moved + 6 re-homed for cross-pack deps + 21 identical dupes deleted; mtank_pri's `VerticalRateOfTurn: 12` folded into Shared). Resolved weapon+actor dumps byte-identical; boot-gate PASS. ⚠ CROSSES LANES: touches Aurora's Atreides/Ordos/Shared-weapons, Blaze's Harkonnen/d2k.yaml, Echo's Ixian — needs their ACK. | `mods/cameo/ContentPacks/D2k/*/yaml/weapons.yaml`, `mods/cameo/weapons/d2k.yaml` |
| **Devin-Aurora** (SWE-1.7 Max / GLM-5.2 High) | Active — **D2k coordinator under Claude** | D2k Phase 0/1/2/3 coordinator. ✅ Ruling 7 EXECUTED: Factions: atreides (37 blocks) + Factions: ordos (72 blocks). ✅ Ruling 3 EXECUTED: Ordos Selectable + 3 sequence migrations. ✅ Ruling 5 EXECUTED: meter_dilution fix. ✅ Ruling 9 COMPLETE for my lane: 2 Atreides + 41 Ordos + 3 Shared weapons migrated; 13 Atreides + 4 Ordos sequences migrated. ✅ Ruling 10 EXECUTED: 0 Ixian cross-pack refs in Ordos. ✅ Ruling 13 W24: d2k_grenade re-collapsed correctly (`f901513a7`) — VERBATIM 10000, Concussion_Medium survivor. HMG collapse done by maintainer (`a16ee55fc`). ✅ **ra1_soviets rename** (`ad7c5e232`): 106/106 actors compliant, 105/105 icons, 181 asset git-mv, 8 .oramap repacked, boot-gate PASS. ✅ **Split-definition cleanup** (`a662a68f5`): 30 identical duplicate blocks deleted from legacy `weapons/d2k.yaml`; W2 201/213, W3 18/21, W4 58/61 (all below ratchet); boot-gate PASS. ⛔ **W24 collapse attempt on D2K_Rocket_Trooper_AA + AGOnly was WRONG — reverted.** The maintainer's `d818aec40` showed the correct approach is NOT to collapse but to remove stale `-Warhead@` markers and fix empty-type warheads. **AWAITING Claude ruling on how to handle multi-warhead weapons under the ONE-WARHEAD law. Do NOT collapse any more weapons without explicit Claude/maintainer instruction.** | `mods/cameo/ContentPacks/D2k/Atreides/`, `mods/cameo/ContentPacks/D2k/Ordos/`, `mods/cameo/ContentPacks/D2k/Shared/yaml/weapons.yaml`, `mods/cameo/bits/d2k/` |
| **Devin-Cyrus** (was Devin-Forge) | **RESOLVED** — WC2 hero pass committed by maintainer | WC2 hero weapon rework. Maintainer committed Cyrus's unfinished work as `d11b90720` (2026-08-25): 8 hero weapons + 8 hero actors across Humans and Orcs. Hellscream + elite verified: actors, weapons, sequences, icon all present. **Cyrus: stand down, this is done.** | `mods/cameo/ContentPacks/Warcraft2/Humans/`, `Warcraft2/Orcs/` |
| **Devin-Ember** (SWE-2 Max) | Active — **landing batch reconciled; queue items 1-3 discharged** | Landed: #421/#422/#423 + #434 (CA exclusive-only) + #436 (ECHO alias table, O1 8->7/O2 6->5); #432 closed as dup of #420. Open, all rebased on `1519a7582` + boot-gated: `naming-asianalliance` `e83a56087` (#424), `handoff-sync` `f77b71b76` (#426), `lane5-classes` `42e86d9ae` (#428). Parked/superseded: `ra6-collapse`, `rename-asianalliance` (subset), W24 Consortium lane (needs ExtraDamage ruling). Flagged master debt: `_model.json` census stale + 18 doc_claims mismatches post-landing (NOVA's #437 covers the ledger half). | rename maps + per-branch scope; no standing file-set claim beyond active branch work |
| **Devin-Echo** (SWE-1.7 Max) | Active — **review CABAL + Ixian** | Phase 2 Atreides done (`f07d8d35e`); auditing D2k weapons. **ORDER: 1. Review CABAL file after cabal_avatar patch landed (`e1552421f`). 2. Re-verify D2k/Ixian before Phase 4.** | `mods/cameo/ContentPacks/D2k/Atreides/`, `D2k/Ordos/`, `D2k/Ixian/`, `TiberianSun/CABAL/` |
| **Devin-Blaze** | Active — **D2k Shared consolidation** (maintainer priority) | Phase 1 Harkonnen complete (`afdaae46c`); Phase 4 shared/global. **ORDER: move remaining shared D2k content into `ContentPacks/D2k/Shared/`. Clean up legacy `d2k.yaml`/`rules/d2k.yaml` dead blocks. Verify no dangling refs.** | `mods/cameo/ContentPacks/D2k/Harkonnen/`, `ContentPacks/D2k/Shared/`, legacy `mods/cameo/weapons/d2k.yaml`, `mods/cameo/rules/d2k.yaml` |
| **Devin-Nova** (Devin CLI, SWE-1.7 Max) | Active — verifier/generator lane | Committed `7557c983d` (AreaDamageWarhead C# NRE fix), `b905d7679` (BulletChem generator spec), `85bcf3f33` (Claude's reference-pipeline tooling). **Relayed heaviness bell ruling.** ORDER: composite-registry re-curation (fixes `three_way_split` crash on `wc2deathknightFire` stale digest). `gen_weapon_template.py` REFLECTOR 75→74 sync. Help Ember. | `OpenRA.Mods.Cameo/Warheads/AreaDamageWarhead.cs`, `tools/balance/gen_weapon_template.py` |
| **Claude-Cloud** (Anthropic, cloud container) | Active — **rebase your branches** | Patches landed locally by Aurora. ORDER: rebase `claude/*` against current branch; extract specific files only, do NOT merge wholesale. | `claude/*` branches |


---

## ⭐ STANDING ORDERS — issued by Claude-Local, 2026-09-05 (maintainer put me in coordination)

The maintainer has asked me to coordinate this team and to review work as it completes.
These orders supersede any conflicting instruction in a SUPERSEDED table lower in this file.

### How we work (read once, then follow it)

1. **Your lane is exclusive.** Every incident today came from two agents needing one file —
   not from missing review. If your task needs a file outside your lane, **do not edit it**:
   post the request in `DEVELOPMENT_LOG.md` and I will reassign or arbitrate.
2. **You do NOT wait for me to commit.** Seven agents queued behind one reviewer has a
   throughput of one. Verify with the mechanical gates and commit:
   `find_empty_warhead.py` = 0, `audit_duplicate_inherits.py` exit 0,
   `audit_warhead_split.py` at or below its ratchet, `audit_balance_drift` clean,
   **and the boot gate** (`launch-game.cmd` reaching the main menu, no new `exception-*.log`).
   Scoped `git add <files>` only. Sign with your OWN `Co-Authored-By:`.
3. **When you finish, say so in `DEVELOPMENT_LOG.md` and paste the OUTPUT of your verify
   commands, not a summary of it.** I re-run them independently. I am not being pedantic:
   today produced four confidently-wrong claims, including two of my own
   ("MO is not recoverable", "CnC Reloaded is unextractable"). Claims here decay in hours.
4. **Never re-extract or hand-edit a balance number.** `extract_stats.py` -> ledger ->
   `apply_balance --confirm` (maintainer order only).
5. ⛔ **`git grep` and `miniyaml` BOTH silently under-read our weapons yaml** — several files
   carry non-UTF-8 bytes, so `git grep` skips them as binary and a miniyaml node count comes
   back short. For any presence/absence check use `git show <rev>:<file> | grep -a`.
   This nearly cost 30 live weapon nodes during the master merge.

### Ownership, de-conflicted (this replaces the overlapping claims)

Three stale tables in this file assigned D2k/Harkonnen to **two** agents and named **two**
different coordinators. Resolved against §3.A and against who has actually been committing:

| agent | lane — EXCLUSIVE | explicitly NOT yours |
|---|---|---|
| **Devin-Dawn** | `ContentPacks/D2k/Corrino/**`, `mods/cameo/weapons/tiberiansun.yaml` | Harkonnen, Atreides |
| **Devin-Aurora** | `ContentPacks/D2k/Atreides/**`, `ContentPacks/D2k/Ordos/**`, `bits/d2k/**`, `D2k/Shared/yaml/weapons.yaml` | the rest of `D2k/Shared/` (Blaze), Ixian (Echo) |
| **Devin-Cyrus** | `ContentPacks/Warcraft2/Humans/**`, `Warcraft2/Orcs/**` | **D2k/Harkonnen — that is Blaze's, despite the stale tables** |
| **Devin-Echo** | `ContentPacks/D2k/Ixian/**`, `TiberianSun/CABAL/**` | Atreides, Ordos (Aurora's) |
| **Devin-Blaze** | `ContentPacks/D2k/Harkonnen/**`, `D2k/Shared/**` except `yaml/weapons.yaml`, legacy `weapons/d2k.yaml`, `rules/d2k.yaml` | — |
| **Devin-Nova** | `OpenRA.Mods.Cameo/Warheads/**`, `tools/balance/gen_weapon_template.py`, `mods/cameo/weapons/weapons.yaml` | — |
| **Devin-Ember** | ~~`ContentPacks/RedAlert/{Allies,Shared,Japan}/yaml/weapons.yaml`~~ — broadcast-collapse lane **parked 2026-09-22** (superseded by §3a laws + W19 + master's restructures); currently no exclusive file-set — works task-scoped branches only | other agents' in-flight sweeps |
| **Claude-Local** | `tools/reference/**`, `tools/balance/{assign_references,faction_routes,faction_extrapolate}.py`, `docs/balance/review/**` | all `ContentPacks/**`, all `mods/cameo/weapons/**` |

### Orders, in priority order

**~~P0 — Devin-Cyrus: COMMIT THE WC2 HERO PASS~~ — RESOLVED (2026-09-06, Aurora verification)**
The WC2 hero pass was committed by the maintainer as `d11b90720` on 2026-08-25
("Picks up Devin-Cyrus's unfinished work"). Verified: hellscream + elite actors,
weapons, sequences, and icon all present. Dawn is **unblocked** for Corrino Phase 3.

**~~P0 — Devin-Nova: two correctness items~~ — RESOLVED (2026-09-06)**
1. ✅ **`weapons.yaml.rej` — DELETED.** `Test-Path` = False. REFLECTOR 75 stands, gen_sync drift = 0.
2. ✅ **`^Warhead_CannonTesla_*` — KEEP BOTH.** Nova's forensic (`a636756e5`) proved
   CannonTesla is a distinct generator-defined BLEND (50% Tesla + CannonAP), not a
   duplicate. Resolved rows differ from `^Warhead_Tesla_*` throughout. Sole consumer
   `RA2120mm_tesla` is coherent authored content. `audit_family_uniqueness` passes.
   The 0-reference `_Medium`/`_Heavy` levels are unused levels like any leveled family.

**P1 — Devin-Ember: own the red gates.** Run `bash tools/audit/run_all.sh` on a complete tree
and triage. `audit_doc_claims` is now **fully green (19/19)** — `ledgers_drifted` is 0 after the D2k re-extract, and `meters_filling_before_death` (269) and `multi_main_fired_weapons` (192) both match the committed tree. `audit_doc_health` D1 control chars in `DEVELOPMENT_LOG.md` are CLEAN (Aurora cleaned them 2026-09-06). Remaining D1 findings are 4 non-UTF-8 files in Claude-Local's reference docs (`scout_references.md`, `FACTION_REFERENCE_MATRIX.md`, `RTS_BALANCE_REFERENCE.md`, `WARHEAD_REFERENCE.md`) — route to Claude. ⚠ Read the `exit=` line in the output file; never trust
a background task's notification code.

**P1 — Devin-Blaze, Devin-Aurora, Devin-Echo: D2k faction completion** — the
maintainer's standing priority. Stay strictly in the lanes above. **Dawn's lane is now
INI reference extraction** (`devin/dawn/ini-untagged-breakdown-v2` PR #365). Corrino
Phase 3 remains with Blaze/Aurora per `docs/FLEET_ORDERS_2026-09-08.md`.

⛔ **Maintainer ruling for everyone, 2026-09-05:** the EBFD sprites were to be added as **NEW
actors only**; the **Ordos Face Dancer was the sole approved update to an existing actor.** An
audit found six pre-existing actors had their art changed — `combat_tank.harkonnen` was
repointed from `DATA.R16` to `harkonnen_assaulttank.png` with **no new actor created**, and its
husk followed. Ruled: **revert `combat_tank.harkonnen` + husk to `DATA.R16`** and wire
`harkonnen_assaulttank.png` to a genuinely new T2 Harkonnen heavy when the balance pipeline can
price it. `harkonnen_devestator.png` also carries a typo (devEstator). **Blaze owns this.**

**P2 — nobody claim these yet:** the heaviness-bell rollout stays OFF until W24 closes
(maintainer, today). Do NOT create new leveled families; do NOT flip `USE_BELL`.

### What I am doing, so nobody duplicates it

The reference/faction-routing lane. **Order item 3 is delivered:** 7 reference mods extracted to
`Cameo-mod-reference/extraction/` — 8183 unit rows, 1695 armor profiles (Rise of the East,
RA20XX, Mental Omega, CnC Reloaded, Red Resurrection, DTA Classic+Enhanced, RA2 Reborn). The
`REFERENCE_PIPELINE_HANDOFF.md` §1.3 claim that MO/CnCR data is "not recoverable" was wrong.
Next: an INI->corpus extractor so those rows reach `assign_references.py`, then per-class review
sheets. I also fast-forwarded `master` 113 commits — the UnitsToBuild merge-order blocker is gone.

#### Locked files (DO NOT TOUCH — another agent owns these)

- `mods/cameo/weapons/weapons.yaml` — template generator/family work; needs explicit sign-off. **Maintainer's Versus tweaks (HAZMAT/COMPOSITE/BLAST/REFLECTOR adjustments) are committed and final — do NOT revert.**
- `mods/cameo/weapons/tiberiansun.yaml` — Devin-Dawn owns TSLaser90mm family work.
- `mods/cameo/weapons/tiberiandawn.yaml` — may be open in an IDE tab.
- `mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/weapons.yaml` — may be open in an IDE tab.
- `mods/cameo/ContentPacks/RedAlert/Shared/yaml/weapons.yaml` — Devin-Dawn owns ATMine.
- `mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml` — **maintainer edit in progress** (KotinCannonNuclearShell cleanup). Aurora fixed `^Warhead_CannonTesla_Light` → `^Warhead_Tesla_Light` ref here.
- `mods/cameo/ContentPacks/RedAlert2/Soviets/yaml/weapons.yaml` — Aurora fixed missing `^Warhead_CannonTesla_Light` template ref (changed to `^Warhead_Tesla_Light`). **Do NOT revert this fix.**
- `mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml` — Devin-Echo owns D2K_APC_Rocket. **Maintainer added `ordos_laserturret` and `ordos_chemturret` actor definitions to `buildings.yaml` — these are final.**
- `mods/cameo/ContentPacks/D2k/Ixian/yaml/weapons.yaml` — Devin-Echo owns MongooseRocket/facedancer_grenade. **Uncommitted WIP — re-verify before Phase 4.**
- `mods/cameo/ContentPacks/Warcraft2/Humans/yaml/weapons.yaml` — Devin-Cyrus owns Alleria fix.
- `mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/weapons.yaml` — Devin-Cyrus owns Hellscream.
- `mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml` — Devin-Echo owns CABAL collapses. **Aurora removed orphaned `-Warhead@MissileHE_Light:` at line 2026 (CabalManticoreMissilesAA) to unblock boot.**
- `mods/cameo/ContentPacks/RedAlert/Japan/yaml/weapons.yaml` — **Aurora removed orphaned `-Warhead@Bullet_Light:` at line 1621 (HovercraftPlasmaCannon) to unblock boot.**
- `mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml` — **maintainer W24 collapses committed and verified (Bullet_Light+Bullet_Medium → Bullet_Medium). Do NOT revert.**

#### Unassigned tasks for the next available agent (Devin-Blaze or anyone free)

1. **~~StarCraft Protoss/Zerg bullet collapses~~** — **NO CANDIDATES FOUND.**
   Re-scanned 2026-09-05 by Devin-Aurora: zero weapons with 2+ same-family
   damage mains and positive Damage values in any StarCraft weapons.yaml.

2. **~~RedAlert2Mod/Naxis bullet collapses~~** — **DONE** by Devin-Aurora.

2b. **~~RedAlert (RA1) Allies + Soviets same-family collapses~~** — **DONE** by Devin-Aurora.

3. **~~RedAlert2Mod/Consortium missile/cannon collapses~~** — **NO CANDIDATES FOUND.**
   Re-scanned 2026-09-05 by Devin-Aurora: zero W24 candidates in Consortium.

4. **~~Audit/RedAlert2 dead-code cleanup~~** — **DONE.** `mods/cameo/weapons/redalert2.yaml`
   is marked DEPRECATED (line 4), load entry commented out in `mod.yaml` line 307.
   Verified dead: 0 unique templates, 0 unique weapons (Devin-Aurora 2026-08-25).

5. **W23 retrofit candidates** — **ALL DONE** (see `docs/audit/latest/phase_b_survey.md`):
   - ~~`ordos_laserturret` (D2k/Ordos)~~ — **DONE** by Devin-Aurora (`9cdfa40dd`). Converted from `^LaserWeapon` to `^Warhead_Laser_Heavy` + `^Projectile_Laser_Heavy` + `^Effect_Laser_Heavy`. Damage 10000 preserved verbatim.
   - ~~`HydraSpit` (StarCraft/Zerg)~~ — **DONE** by Devin-Aurora (`8748c68e4`). Converted from 4 old families (^LightChemicalWeapon, ^LightMissile, ^SmallArms, ^ArrowWeapon) to single ^Warhead_BulletChem_Light. Damage 18000 preserved verbatim. Generator spec landed by Nova (`b905d7679`).

**W24 safe pool status (2026-09-05): EXHAUSTED.** `plan_warhead_collapse.py` reports 193 directly actor-armed multi-main weapons, but the 85 HIGH-confidence weapons still carry mixed old families and compatibility warheads (e.g. `CommandoM16`, `DuelistTankCannon`). The plan explicitly warns that numeric-sum preservation does not preserve armor profile, geometry, relationships, or damage types, so these are design-review items, not safe mechanical collapses. `phase_b_survey` now shows 0 remaining concrete old-family weapons (both `ordos_laserturret` and `HydraSpit` DONE) and `find_mechanical_phase_a` reports 0 clean single-inherit candidates. The front moves to maintainer sign-off / ownership.

**⚠ NEW MAINTAINER RULING (2026-09-05, relayed by Devin-Nova):** *"we will only have a single warhead per type and no more light, medium and heavy! it will all be done with the heaviness bell curve!"* — The Light/Medium/Heavy level system is a TRANSITION state, not the target. The target: one `^Warhead_<Family>` per type, level behavior derived by the `Heaviness` bell transform. Do NOT create NEW leveled families. W23/W24 collapse queues still apply. The BulletChem family (commit `8748c68e4`) predates this ruling; whether it stays leveled or is refolded under heaviness is a later-wave decision.

6. **D2k faction completion** (Atreides/Harkonnen/Corrino) — see §3.7 below.
   This is the maintainer's priority task. All three factions are selectable but
   need unique weapons, full tech trees, and faction-specific actors.

---

### 3.7 — Dune 2000 faction completion: Atreides, Harkonnen, Corrino (2026-08-25)

⭐ **PRIORITY TASK — maintainer order 2026-08-25.** The three remaining D2k factions
must be fully built out so they are selectable and playable. Currently:

| faction | state | units | buildings | infantry | aircraft | weapons | upgrades | selectable |
|---|---|---|---|---|---|---|---|---|
| **Atreides** | FEATURE-COMPLETE (Aurora) | 11 vehicles (MCV, harvester, combat, sonic, missile, siege, sandbike, APC, repair, minotaurus, mongoose) | 15 (full set) | 4 (lightinfantry, rockettrooper, fremen, engineer) | 3 (ornithopter, airdrone, advanced carryall) | `weapons.yaml` active (155 lines, `876226947`) | 5 | **yes** (FactionCA active, StartingUnits set) |
| **Harkonnen** | complete in `afdaae46c` | 5+ (MCV, harvester, combat, missile, devastator, MCV) | full set | 3 (lightinfantry, rockettrooper, engineer) | 1 (carryall) | `weapons.yaml` active | 5+ | **yes** (FactionCA active, StartingUnits set) |
| **Corrino** | complete in `af3ff5f9d` | 5 (MCV, harvester, combat, buggy, BMP) | 13 | 3 (lightinfantry, engineer, sardaukar_bazooka) | 2 (carryall, transport) | active | 5 | **yes** (FactionCA active, StartingUnits set) |
| Ixian (reference) | complete | 16 | 18 | 6 | 11 | 32KB | 9 | yes |
| Ordos (reference) | complete | 17 | 16+ | 9 | 13 | 28KB | 11 | yes |

**Phase 0 boot-gate:** passed. The canonical rollout plan and agent instructions are in §3.B below. The table above is a snapshot; §3.B is the authoritative task queue.

**Reference templates:** use Ixian and Ordos as the structural pattern. Every
faction needs: `content.yaml`, `yaml/faction.yaml` (with `FactionCA@<Name>` and
`StartingUnits@<name>` entries), `yaml/buildings.yaml`, `yaml/infantry.yaml`,
`yaml/vehicles.yaml`, `yaml/aircraft.yaml`, `yaml/weapons.yaml`, `yaml/upgrades.yaml`,
`yaml/sequences.yaml`, `yaml/ai.yaml`, `translations/en.ftl`.

**D2k Shared content** (`ContentPacks/D2k/Shared/yaml/`): buildings (concrete slabs,
walls, oil derrick), vehicles (siege_tank, sandworm), infantry (light_inf, trooper,
fremen_creep, engineer). These are shared across all D2k factions — do NOT duplicate
them in faction packs. Reference them via `ProvidesPrerequisite` and `Buildable:
Prerequisites: ~d2k_barracks` etc.

#### Agent assignments for D2k faction completion


> ⛔ **SUPERSEDED — this ownership table is STALE. The single authoritative roster is
> §3.A "Agent roster and current assignments".** It is kept only as provenance; it
> contradicts §3.A on who owns D2k/Harkonnen and on who the coordinator is. Do NOT
> claim a file-set from this table.

| agent | faction | file-set | scope of work |
|---|---|---|---|
| **Devin-Aurora** (this agent) | **Atreides** (stub) | `mods/cameo/ContentPacks/D2k/Atreides/**` | Nearly everything needs to be built. Add: full building set (barracks, light factory, repair pad, outpost, gun turret, rocket turret, high tech factory, research center, starport, palace), infantry (light_inf, trooper, engineer, Fremen, kinjal), vehicles (MCV, spice harvester, combat tank, missile tank, sonic tank, trike/raider), aircraft (ornithopter, carryall), weapons, upgrades, sequences. Uncomment `FactionCA@Atreides` and set `Selectable: true`. Port Atreides-specific units/weapons/sequences from legacy `mods/cameo/weapons/d2k.yaml` and `mods/cameo/sequences/d2k.yaml`. |
| **Devin-Cyrus** | **Harkonnen** (partial) | `mods/cameo/ContentPacks/D2k/Harkonnen/**` | Buildings exist (16, full set). Add: infantry (light_inf, trooper, engineer, sardaukar), aircraft (carryall, gunship), upgrades (at least 5-8), more vehicles (siege tank via Shared, flame tank), weapons for new units, sequences for new units. Set `FactionCA@Harkonnen: Selectable: true` (currently false). Port remaining Harkonnen units from legacy `d2k.yaml` / `rules/d2k.yaml` / `sequences/d2k.yaml`. |
| **Devin-Dawn** | **Corrino** (new) | `mods/cameo/ContentPacks/D2k/Corrino/**` (create from scratch) | Create the entire faction directory + all yaml files. Copy the Ordos pack skeleton. Corrino is the Imperial faction: Sardaukar elite infantry, combat tank, missile tank, siege tank, carryall, palace with Death Hand support power. Register in `mod.yaml` (add `Include: ContentPacks/D2k/Corrino/content.yaml`). Set `FactionCA@Corrino: Selectable: true`. Add `StartingUnits@corrino` entries (already exist in Ixian faction.yaml as a placeholder using ixian MCV — replace with corrino MCV once created). |
| **Devin-Blaze** | **D2k Shared + legacy consolidation** | `mods/cameo/ContentPacks/D2k/Shared/yaml/**`, `mods/cameo/weapons/d2k.yaml`, `mods/cameo/rules/d2k.yaml` | Move all D2k units/weapons/sequences used by multiple factions into `ContentPacks/D2k/Shared/yaml/`. Update `Shared/content.yaml`. Remove or comment out dead blocks from legacy `d2k.yaml` and `rules/d2k.yaml` once content has moved. Verify no `Parent type ... not found` or dangling refs. |
| **Devin-Echo** | **coordinator** | verification & ledger sync | Maintain the plan in `DEVELOPMENT_LOG.md` and `HANDOFF.md`. Run `extract_stats`, `audit_doc_claims`, `audit_warhead_split`, and `find_empty_warhead` after each phase. Boot-gate the integrated tree. Commit each pack in a scoped batch. |

#### D2k faction unit rosters (from Dune 2000 source game)

**Atreides** (noble, air superiority, Fremen allies):
- Buildings: construction yard, wind trap, barracks, refinery, silo, light factory,
  heavy factory, repair pad, outpost, gun turret, rocket turret, high tech factory,
  research center, starport, palace
- Infantry: light infantry, trooper (rocket), engineer, Fremen, kinjal soldier
- Vehicles: MCV, spice harvester, combat tank, missile tank, sonic tank, trike/raider
- Aircraft: ornithopter (air superiority), carryall, gunship
- Upgrades: upgrade_conyard, upgrade_barracks, upgrade_lightfactory,
  upgrade_heavyfactory, upgrade_radar, upgrade_hightech
- Support powers: Ornithopter Airstrike, Fremen Guerilla

**Harkonnen** (brute force, atomic weapons):
- Buildings: already has 16 (full set) — verify completeness
- Infantry: light infantry, trooper, engineer, sardaukar (elite)
- Vehicles: MCV (has), combat tank (has), missile tank (has), devastator (has),
  siege tank (Shared), flame tank
- Aircraft: carryall, gunship
- Upgrades: upgrade_conyard, upgrade_barracks, upgrade_lightfactory,
  upgrade_heavyfactory, upgrade_radar, upgrade_hightech
- Support powers: Death Hand Missile

**Corrino** (imperial, Sardaukar):
- Buildings: construction yard, wind trap, barracks, refinery, silo, light factory,
  heavy factory, repair pad, outpost, gun turret, rocket turret, high tech factory,
  research center, starport, palace
- Infantry: light infantry, trooper, engineer, Sardaukar (elite imperial guard)
- Vehicles: MCV, spice harvester, combat tank, missile tank, siege tank (Shared)
- Aircraft: carryall
- Upgrades: upgrade_conyard, upgrade_barracks, upgrade_lightfactory,
  upgrade_heavyfactory, upgrade_radar, upgrade_hightech
- Support powers: Imperial Sardaukar reinforcement

#### Build order for all agents (parallel-safe)

1. **Phase 1 — scaffolding (Devin-Cyrus first, then all parallel):**
   - Devin-Cyrus: create `Corrino/` directory + `content.yaml` + register in `mod.yaml`.
   - All agents: create your faction's `faction.yaml` with `FactionCA` (Selectable: true)
     and `StartingUnits` entries.
   - Boot-gate after scaffolding to verify no crash.

2. **Phase 2 — buildings (parallel):**
   - Each agent builds their faction's `buildings.yaml`.
   - Use Ixian/Ordos buildings as the structural template (inherit `^D2KBuilding`,
     `^D2kUpgradeable`, `^D2KPaletteRender`, etc.).
   - Gate with `Prerequisites: ~<faction>_constructionyard` etc.
   - Boot-gate after buildings.

3. **Phase 3 — infantry + vehicles (parallel):**
   - Each agent builds their faction's `infantry.yaml` and `vehicles.yaml`.
   - Use D2k Shared infantry (light_inf, trooper, engineer) as the base — faction
     variants inherit from Shared or from `^D2KInfantry`.
   - Vehicles inherit from `^D2KTank`, `^CombatTank`, `^MainBattleTankTemplate`, etc.
   - Boot-gate after infantry + vehicles.

4. **Phase 4 — aircraft + weapons (parallel):**
   - Each agent builds their faction's `aircraft.yaml` and `weapons.yaml`.
   - Use the 3-way weapon split (`^Warhead_*`, `^Projectile_*`, `^Effect_*`).
   - Boot-gate after aircraft + weapons.

5. **Phase 5 — upgrades + sequences + AI (parallel):**
   - Each agent builds their faction's `upgrades.yaml` and `sequences.yaml`.
   - Devin-Cyrus wires AI build lists and regenerates the faction matrix.
   - Boot-gate after upgrades + sequences + AI.

6. **Phase 6 — final verification:**
   - All agents: `find_empty_warhead.py = 0`, `audit_doc_claims` green,
     `extract_stats --check` 0 drifted.
   - Boot-gate with all three factions selectable.
   - Regenerate `docs/factions/MATRIX.md`.
   - Update `DEVELOPMENT_LOG.md` with completion summary.

#### Critical rules for faction creation

- **Do NOT edit another agent's faction files.** Each agent owns exactly one
  faction's file-set. Devin-Blaze owns D2k/Shared only. Devin-Cyrus owns
  registration/AI files only.
- **Use the 3-way weapon split** for all new weapons (`^Warhead_*`, `^Projectile_*`,
  `^Effect_*`). No inline `Versus` — it lives only in `^Warhead_*` templates.
- **Use `^D2KPaletteRender`** for D2k sprites (palette: `d2kunit` or `playerd2k`).
- **Sequence files** must use `Filename: DATA.R16` with `Scale: 1.5` and
  `Remap: 54F94B` for D2k sprites (see existing Atreides/Harkonnen sequences).
- **Boot-gate after every phase.** The game must reach the main menu with no new
  `exception-*.log` files.
- **Scoped `git add` only.** Each agent commits only their own faction's files.
- **Naming convention:** `<faction>_<unitname>` (e.g. `atreides_lightinfantry`,
  `harkonnen_sardaukar`, `corrino_combattank`). Shared units keep their base
  name (e.g. `light_inf`, `siege_tank`).
- **Balance numbers** must go through the pipeline (`extract_stats` → ledger →
  `apply_balance --confirm`). Do NOT hand-edit balance values. For initial
  creation, use the same damage/HP/cost values as the equivalent Ixian/Ordos unit.

### 3.B — D2k Faction Rollout: Atreides / Harkonnen / Corrino (NEW — 2026-08-25)

**Coordinating agent:** Devin-Aurora (this session).
**Goal:** make Atreides, Harkonnen, and Corrino fully playable, self-contained Dune factions with **completely unique tech trees and no shared units/assets** with each other or with the existing Ixian/Ordos factions. This supersedes the older draft in `DEVELOPMENT_LOG.md` §"D2k faction rollout plan" because the user has now supplied harvester sprites and explicitly required uniqueness and asset isolation.

**New assets already in the repo (Phase 0):**
- `mods/cameo/bits/d2k/atreides_harvester.png` — 32-frame strip, 98×98 px/frame: 8 idle facings + 3 frames × 8 facings harvesting.
- `mods/cameo/bits/d2k/harkonnen_harvester.png` — 192-frame strip, 200×150 px/frame: 8 frames × 8 facings move, 64 one-frame idle facings, 8 frames × 8 facings harvest.
- No absolute local paths are recorded in any repository document.

**Agent assignments and detailed instructions:**

| Phase | Owner | File-set | What to build | Acceptance |
|---|---|---|---|---|
| **0 — Foundation** | **Devin-Aurora** (committed `f07d8d35e`) | `ContentPacks/D2k/Atreides/`, `ContentPacks/D2k/Harkonnen/`, `mods/cameo/bits/d2k/` | Wire the maintainer-supplied harvester PNGs (`atreides_harvester.png` and `harkonnen_harvester.png`) as `atreides_spiceharvester` and `harkonnen_spiceharvester` (actors + sequences + refinery `FreeActor`). Create `Atreides/yaml/weapons.yaml` and `Atreides/yaml/promotions.yaml` and load them from `Atreides/content.yaml`. Fix Atreides `^D2KVehicleHusk`/`^UpgradeTemplate` parents and `IconPalette` indentation. Do **not** enable `Selectable` yet. | `launch-game.cmd` reaches main menu with no new `exception-*.log`; commit `f07d8d35e`. |
| **1 — Harkonnen** | **Devin-Blaze** (committed `afdaae46c`) | `ContentPacks/D2k/Harkonnen/` | Complete Harkonnen as a brute-force, heavy-vehicle faction. Infantry (`harkonnen_lightinfantry`, `harkonnen_rockettrooper`, `harkonnen_engineer`), aircraft (`harkonnen_carryall`), vehicles, buildings, upgrades, sequences, StartingUnits (MCV/Light/Heavy). Replace remaining `ordos_*`/`ixian_*`/generic art refs as new `harkonnen_*` assets arrive. | Boot-gate passed; `utility.cmd cameo --check-yaml` follow-up for final lint. |
| **2 — Atreides** | **Devin-Aurora** (committed `f07d8d35e`) | `ContentPacks/D2k/Atreides/` | Complete Atreides as a noble/air/Fremen faction. Full building set, 4 infantry, 5 vehicles, ornithopter, 5 upgrades, sequences, StartingUnits (MCV/Light/Heavy). Theme: air superiority, faster construction, Fremen. | Same as phase 1. |
| **3 — Corrino** | **Devin-Cyrus** → **Devin-Aurora** (completed `af3ff5f9d` + `d519ceaf6`) | `ContentPacks/D2k/Corrino/` | Corrino is imperial/Sardaukar: 3 infantry, 5 vehicles (MCV, harvester, combat tank, buggy, BMP), 2 aircraft, 13 buildings, 5 upgrades, weapons, sequences, StartingUnits, translations. | Boot-gate passed; Phase 4 shared/global pass now active. |
| **4 — Shared/global pass** | **Devin-Aurora** + **Devin-Blaze** + **Devin-Echo** (IN PROGRESS) | `ContentPacks/D2k/Shared/yaml/`, `mods/cameo/weapons/d2k.yaml`, `mods/cameo/rules/d2k.yaml` | Add shared templates, fix cross-faction prerequisites, walls/turrets/superweapons/promotions. Remove dead legacy blocks from `mods/cameo/weapons/d2k.yaml` and `mods/cameo/rules/d2k.yaml`. Run `find_empty_warhead.py`, `review_resolve_diff`, `audit_warhead_split`, `extract_stats --check`, full `run_all.py`, and boot-gate. | All audits green; `multi_main_fired_weapons` not inflated. |

**Harkonnen build-option follow-up (2026-09-21):** `harkonnen_autogunturret` and
`harkonnen_rocketturret` had `Buildable` prerequisites but no production queue, so they were
absent from the Defence palette. Their existing faction prerequisites are unchanged; both now
declare the Defence queues and peer-matched palette order and icon palettes. The Rocket Turret
uses a Harkonnen-specific Fluent description.

**Hard constraints for every phase owner:**
1. **Unique and isolated.** Every actor, weapon, sequence, icon, and building in a new faction is prefixed with the faction name and lives inside that faction's pack. No references to `ordos_*`, `ixian_*`, or generic shared actors except through intentionally shared `^D2K*` templates in `ContentPacks/D2k/Shared/yaml/templates.yaml`.
2. **Assets in the repo only.** All new `.png`/`.shp` files go under `mods/cameo/bits/d2k/<faction>/` (or `ContentPacks/D2k/<Faction>/files/` if the `mod.yaml` package is updated). No absolute local paths in docs.
3. **W24 weapons.** Every new weapon has one main damage warhead. Run `find_empty_warhead.py`, `audit_warhead_split.py`, and `review_resolve_diff.py` per batch.
4. **Harvester rule.** Every refinery spawns `<faction>_spiceharvester` via `FreeActor`/`FreeActorWithDelivery`.
5. **Do not flip `Selectable: true` prematurely.** A faction is only selectable when it has a full minimum viable tech tree: con yard, wind trap, refinery, harvester, barracks, light vehicle factory, MCV, one anti-ground unit, and `StartingUnits`.
6. **Boot-gate and scoped commits.** `launch-game.cmd` before every commit; `git add <files>` only; never `-A`.

#### How to coordinate after every step

1. **Before editing**: check `DEVELOPMENT_LOG.md` §"Active claims" for file ownership.
2. **After editing**: add an entry to `DEVELOPMENT_LOG.md` with:
   - Your agent name
   - What file(s) you edited
   - What weapons you converted
   - Why you made each decision (which rule, which pattern, which precedent)
   - Verification results (find_empty_warhead, audit_warhead_split, review_resolve_diff)
   - What's next
3. **Before committing**: verify no other agent has uncommitted work in your file set
   (`git status --short` + `git diff --name-only`).
4. **After committing**: update your claim in `DEVELOPMENT_LOG.md` to say "COMMITTED"
   with the commit hash.

#### Devin-Prime handoff message (2026-08-25)

I am **Devin-Prime**, the agent that handled W24 A14. My work is currently in handoff. The
A14 changes are verified and staged in the history, but the working tree also contains
uncommitted work from other agents (D2k/Ordos `D2K_APC_Rocket`, `redalert2mod.yaml`, `d2k.yaml`,
Warcraft2 hero weapons, the rename map, and the `BROADCAST_BASELINE` 876 ratchet). **Do not**
`git add -A`; wait for each owning agent to finish and then commit in scoped batches.

If you are the next agent and your file-set is free, the safest next picks are in the
"Unassigned tasks" list above — especially the **StarCraft Protoss/Zerg bullet collapses** or
**RedAlert2Mod/Naxis** — because they are not currently claimed. If you touch a claimed or
locked file, first read `DEVELOPMENT_LOG.md` "Agent identity & handoff" and the latest
`git status --short` to see who owns it.

My single emergency exception: I had to repair `ContentPacks/Warcraft2/Humans/yaml/weapons.yaml`
because the new `wc2_orcs_zuljin_spear` inherited a missing `wc2_humans_alleria_arrow`, which
caused `OpenRA.YamlException: Parent type ... not found` and blocked the boot-gate. Devin-Forge
owns Warcraft2 and has since refined the Alleria numbers; I will not modify that file set again.

#### The established W24 bullet-collapse pattern (follow this exactly)

When a weapon has `Bullet_Light` + `Bullet_Medium` as two damage mains:
1. Drop `Inherits@wh: ^Warhead_Bullet_Light` (or `Inherits@wh2: ^Warhead_Bullet_Light`).
2. Repoint the remaining `Inherits@wh2: ^Warhead_Bullet_Medium` to `Inherits@wh`.
3. Remove the `Warhead@Bullet_Light:` block.
4. Sum the damage: `Warhead@Bullet_Medium: Damage: <Light + Medium>`.
5. Preserve any local `PercentageScale` on the surviving warhead — if the old
   Bullet_Light had a different `PercentageScale`, preserve the effective percentage
   (ask the formula: `actual_percent = Damage / 10000` regardless of `PercentageScale`).
6. Check children: if a child inherits this weapon, verify it doesn't override the
   old `Warhead@Bullet_Light` key (orphaned old key = double damage bug).
7. Run `review_resolve_diff.py` against HEAD — only the damage multiset should change.
8. Run `find_empty_warhead.py` — must be 0.
9. Boot-gate before committing.

### 3.C - D2k Atreides / Harkonnen / Corrino (legacy draft - superseded by §3.B)

**Coordinating agent:** Devin-Echo. See full plan and per-agent instructions in `DEVELOPMENT_LOG.md` §"D2k faction rollout plan — Atreides / Harkonnen / Corrino".


> ⛔ **SUPERSEDED — this ownership table is STALE. The single authoritative roster is
> §3.A "Agent roster and current assignments".** It is kept only as provenance; it
> contradicts §3.A on who owns D2k/Harkonnen and on who the coordinator is. Do NOT
> claim a file-set from this table.

| Agent | Pack | Key deliverable | Verification before commit |
|---|---|---|---|
| **Devin-Aurora** | `ContentPacks/D2k/Atreides/` | playable Atreides pack: `weapons.yaml`, unit/sequence/weapon port from legacy `d2k.yaml`/`rules/d2k.yaml`, `Atreides/files/icons/atreides_harvester.png` wired | `review_resolve_diff`, `find_empty_warhead=0`, `extract_stats --check=0`, boot-gate |
| **Devin-Cyrus** | `ContentPacks/D2k/Harkonnen/` | playable Harkonnen pack: complete actors/sequences, `Harkonnen/files/icons/harkonnen_harvester.png` wired | same |
| **Devin-Dawn** | `ContentPacks/D2k/Corrino/` | new Corrino pack created from Ordos skeleton, added to `mod.yaml`, units/sequences ported | same |
| **Devin-Blaze** | `ContentPacks/D2k/Shared/`, legacy `d2k.yaml`, `rules/d2k.yaml` | consolidate shared D2k content, remove dead blocks from `mods/cameo/weapons/d2k.yaml` and `mods/cameo/rules/d2k.yaml` | `audit_duplicate_inherits.py`, `find_orphan_old_keys.py`, boot-gate |
| **Devin-Echo** | coordinator | keep `DEVELOPMENT_LOG`/`HANDOFF` current, run audits, boot-gate final integration, commit scoped batches | full `run_all.py` + boot-gate |

**Rollout order:** Phase 0 inventory → Phase 1 pack content (parallel) → Phase 2 shared consolidation → Phase 3 integration/audits/commits.

### 3.0 — DO THIS FIRST

**a. ✅ RULED 2026-08-23 — the nine "broken ladders" were never broken. Nothing to do.**

`audit_level_ladder` required a family's effective damage to rise Light → Medium → Heavy → Super,
and **no law ever said so.** §12.0d makes the level a TILT, §12.0h makes `Damage` a separate free
knob, and 145 `^Warhead_*` templates carry only a placeholder `Damage: 2000` — the template holds
the SHAPE, the weapon holds the MAGNITUDE. The audit is retired and replaced by
`tools/audit/audit_heaviness_bell.py`.

⭐ **DESIGN §12.0i IS NOW COMPLETE (2026-08-24) — every constant ruled, nothing open.** The
2026-08-23 version of it is superseded in three places:

| | 2026-08-23 | ruled 2026-08-24 |
|---|---|---|
| x-axis | §12.0d's three coarse buckets, then a per-ladder 0..2 | **one global 13-slot scale**, step 1/6, every ladder centred on 1.000, one deliberate three-way tie (`Flak`=`Medium`=`Steel`=1.0) |
| peak | `centre_of_mass + SHIFT*(h-1)`, `SHIFT` 0.25 | **`mu = (h + centre_of_mass)/2`**; `SHIFT` deleted |
| swing | `LO` 0.80 (1.25x) | **`LO` 0.667 (1.50x)** = `1/TILT_RATIO`, so the continuous model keeps the differentiation the discrete tilt already ships |
| `sigma` | unruled, assumed 1.0 | **0.75** |

`audit_heaviness_bell.py` runs the ruled model over 48 families at h ∈ {0, 0.5, 1, 1.5, 2}: **0
ladder orderings changed, 0 weighted-mean drift**, 2 flat families at the ratchet.

⛔ Two 2026-08-23 conclusions are RETRACTED, both from the same cause — measurements taken before
§12.0d's rank restore was implemented in the audit. A tier-anchored peak was rejected for
"inverting 26 of 42 families"; with the restore it inverts **nothing**. And "ship it inert at h=1"
was unachievable under the family-anchored peak (all 48 families reshaped at h=1, worst row 13.5%),
which is why the peak formula changed rather than the requirement.

⭐ **Step 5 is the next action** — implement the bell in `gen_weapon_template.py` (replacing
`class_tilt`), then in `AreaDamageWarhead`. **DONE 2026-08-24:**
- The generator bell is in `tools/balance/gen_weapon_template.py`, OFF by default
  (`USE_BELL` controlled by `CAMEO_HEAVINESS_BELL=1`).
- The `AreaDamageWarhead` C# transform is in `OpenRA.Mods.Cameo/Warheads/HeavinessBell.cs`, wired
  at `RulesetLoaded`. `Heaviness` defaults to `0` (today's behaviour); non-zero values tilt `Versus`
  and `PercentageVersus` through the bell at load time.
- The continuous **Spread** scale is intentionally NOT wired yet — the mapping from `h` to
  `LEVEL_RADIUS_SCALE` (Light 2/3, Medium 1, Heavy 4/3, Super 5/3, Trace 1/2) is a separate design
  ruling and must not be guessed.

The acceptance test is `tools/balance/preview_bell.py` (tilt-to-tilt on the same base, the only
valid comparison): 130 of 136 profiles move, mean 8.3% row change, **0 ladder inversions**, worst
single row 32.0% on `Chemical_Medium`.

**Status 2026-08-24:** `AreaDamageWarhead` now applies the bell to both `Versus`/`PercentageVersus`
AND `Spread` (via `effectiveSpread`) when `Heaviness != 0`. `Spread` scales linearly
`2/3 -> 1 -> 4/3` as `h` goes `0 -> 1 -> 2` (Light/Medium/Heavy), which is the data-driven
interpolation of `LEVEL_RADIUS_SCALE`. `Trace`/`Super` are outside the ruled `h` range and remain
unhandled. No yaml sets `Heaviness` yet, so the change is inert. Both of `WEAPON_HEAVINESS.md` §9.6's original blockers are gone: #1 was retired by the
2026-08-23 ruling, and #2 (every family inside the 2x–8x spread band) had already been finished on
2026-08-22 without the document noticing — `audit_versus_profile` reports 46 in band at
`SPREAD_OFFENDERS_BASELINE = 0`.

⛔ **RETRACTED:** an earlier version of this section listed two permanent "known inversions" and a
gap in §9.4 needing new gradients authored. Both were artifacts of the audit skipping §12.0d's rank
restore. With the restore the bell changes **zero** ladder orderings (without it, 127 across 60
family/ladder pairs). Nothing needs authoring.

⛔ **STILL OPEN, and the reason to start a fresh session on it:** the maintainer wants every armor
to have its OWN unique continuous x — the interim per-ladder form is unique within a ladder but
collides across them (four armors on 0.0, four on 2.0). A global scale means ranking armors ACROSS
ladders, which §12.0d says the tilt is designed to change. Stated in full as an OPEN block in
DESIGN §12.0i. **Do not change the axis before it is ruled.**

**b. Three tooling defects formerly live on master — VERIFIED FIXED 2026-08-24. Fixes were reported in flight on 2026-08-23 from a
Windows session — the fixes landed; this section is now a verified-fixed record.**

| defect | effect | fix |
|---|---|---|
| `tools/audit/environment.py` now points at repo-root `OpenRA.Mods.CA` (fixed) | `OpenRA.Mods.CA` is **vendored at the repo root**, not under `engine/`, `incomplete()` now returns empty on a built tree and `latest/` is writable | `python tools/audit/environment.py` reports `complete environment` |
| `tools/audit/audit_unique_traits.py` `SOURCE_ROOTS` now uses repo-root `OpenRA.Mods.CA` | now scans all 139 trait types; CA path verified correct | `grep SOURCE_ROOTS` confirms the vendored path |
| `audit_doc_health` D8 no longer flags its own fixtures | `tools/tests/test_audit_doc_health.py` excludes `tools/tests/` and `tools/audit/audit_doc_health.py` from the D8 scan | `python tools/audit/audit_doc_health.py` **PASS** (0 D8 findings) |

`audit_dead_warhead_fields.py` and `audit_code_duplication.py` already had the CA path right, and
a sweep of `tools/**/*.py` finds no third instance — those two are the whole set.

⭐ Both of the second and third defects were introduced by the change that added the gate, and both
were "verified" before landing. How, is in [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md): a grep whose
filter excluded exactly the lines that would have disproved it, and a tracked-file scan run while
the new file was still untracked.

**c. `docs/audit/latest/` regenerated 2026-08-24 from a complete tree.**

Regenerated with `python tools/audit/run_all.py` (bash unavailable on this Windows shell) from a
complete tree (`engine/` built, `OpenRA.Mods.CA` at repo root, not shallow). The suite exited 1 on
the same pre-existing gating failures (`inherits`, `upgrades`, `sequences`, `fluent`,
`basebuilder_crates`, `buildable_order`, `weapon_suffixes`, `impact_glow_preservation`); the report
set is now a single-environment snapshot.

`run_all` now writes to `docs/audit/latest/` because `environment.py` no longer mis-reports
incomplete. The note below about `bash tools/audit/run_all.sh` is the canonical command; the Python
port `run_all.py` is equivalent and was used here. On a machine with `engine/` built:

```sh
git fetch --unshallow          # if the clone is shallow
bash tools/audit/run_all.sh    # writes latest/ only from a complete tree
```

Commit the result **whole**. Do not cherry-pick report files: Windows writes `mods\cameo\…` and
Linux writes `mods/cameo/…`, so a cross-platform diff is dirty even between two complete trees.

⚠ The suite also rewrites TRACKED files **outside** `audit/latest/` — `docs/factions/MATRIX.md`
and `tools/rename/rename_map_*.yaml` (`gen_rename_maps.py` writes those as a side effect of the
naming report). So `git status` after a suite run is not expected to be clean, and those files
belong in the same commit.

⚠ **Previous items here are DONE.** The 9 drifted balance ledgers (`31e649b8`), the 4 drifted doc
claims (`audit_doc_claims` is **19 of 19**), and the memory-citation promotion — **zero**
`memory <name>` pointers remain in the live document set; the two load-bearing ones were inlined
into `weapon_classes.yaml`'s header and `BALANCE_PROGRAM_PLAN.md` §7.

```sh
python tools/audit/audit_heaviness_bell.py  # WARN 2 flat, 0 inversions, 0 drift
python tools/audit/audit_doc_health.py     # PASS
python tools/audit/environment.py          # should print "complete" on a built tree
```

### 3.0c — What the suite's exit code does and does not mean (2026-08-24)

⛔ **Do not re-read a background task's notification exit code as the script's.** It reports the
wrapper (`cmd; echo "exit=$?"`), which is 0 whenever the trailing `echo` succeeds — i.e. always.
That is how "the suite is green" was reported repeatedly while `run_all.sh` was exiting 1 on every
run. Write `echo "exit=$?" >> "$OUT"` into the redirected file and read THAT line.

⛔ **AND THE COMMIT GATE WAS NEVER "the suite exits 0".** CLAUDE.md's gate is: boot to the main
menu with no new `exception-*.log`. An earlier draft of this section claimed a suite-green gate had
"been dead for a week" — there is no such gate, and saying so overstated the finding.

**What is actually red, measured audit by audit rather than by grepping reports for "FAIL":**
**13** audits exit non-zero, and every one of them predates this work.

* **5 are SCHEDULED scans** from [`audit/periodic.json`](audit/periodic.json) on 14–30 day cadences
  — `code_duplication`, `test_coverage`, `recent_changes`, `error_handling`, `security` — which were
  being run as per-commit gates. `test_coverage` alone drifted 223 → 235 → 249 → 257 → 270 untested
  modules against a baseline of 224 from 2026-08-16. **These are now advisory.**
* **8 are gating audits reporting REAL content defects** — `inherits`, `upgrades`, `sequences`,
  `fluent`, `basebuilder_crates`, `buildable_order`, `weapon_suffixes`,
  `impact_glow_preservation`. These are §3.3's bounded-bug backlog, and the advisory change neither
  fixes nor hides them: **the suite still exits 1, correctly.**

⚠ So "make the suite green" is a real work item, not a switch — it means clearing §3.3. What the
advisory change bought is narrower and still worth having: a *scheduled scan's* findings no longer
mix into the same signal as a content defect.

**Maintainer ruling: those five are ADVISORY.** They run and write full reports; they do not set
the suite's exit code. `run_all.sh` carries a second `for a in …; do` loop with `|| true`, and
`run_all.py` finds it by the `# ADVISORY audits` marker comment — by marker, not by index, so a
loop inserted between them cannot be mistaken for it. The calendar is still enforced by
`python tools/audit/audit_periodic_freshness.py` with no flag, and each script still exits 1 on
its own findings so CI can gate on one deliberately. `T3_BASELINE` was **not** raised.

The sixth was a real gate enforcing a retired design — `audit_physical_state_warheads` demanded
`Warhead@{Flame,Chemical}_{Level}_Percentage` twins that the AreaDamage fold folded into the main
warhead. Fixed in the audit. Full account in [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md), "An audit
is not evidence of a law".

⚠ **Found while verifying, and worth knowing:** `run_all.py` parses its audit list out of
`run_all.sh` so the two cannot drift — but `run_all.sh` is checked out CRLF, so a continuation is
`\` + CRLF and the parser stripped only `\` + LF. Every continuation survived as its own audit
name: **73 entries where 59 are real**, and the fallback runner tried `audit_\.py` fourteen times
and reported fourteen phantom FAILEDs. Latent for as long as the file has had continuations,
because nobody ever diffed the fallback against the canonical path. Fixed, with a regression test
in `tools/tests/test_audit_run_all_parser.py`.

### 3.0e — ⛔ The balance ledgers are stale on master (found 2026-08-28)

`python tools/balance/run_pipeline.py` — the new orchestrator — came back FAIL on its
first real run against `4643c3ee`:

| stage | result |
|---|--:|
| drift — yaml vs committed ledger | **FAIL: 22 of 33 raw ledgers stale, 5 model** |
| multiplier modifiers integer | PASS |
| generator reproduces every family | PASS — drift 0 across 139 templates |
| empty warhead types | PASS — 0 of 2839 |

`CLAUDE.md` rule 3 already warns that `audit_balance_drift` "only helps if someone
LOOKS", and that it had gone red twice for exactly this. **This is the third time.**
The last commit to re-extract was #293; something after it moved yaml without running
step 1.

**The remedy is one command**, and it belongs to whoever lands the next balance commit
rather than to a drive-by — the weapon-consolidation flow already re-extracts, and a
single commit that skipped it left 22 ledgers stale:

```sh
python tools/balance/extract_stats.py     # or: run_pipeline.py --extract
```

then commit the ledgers together with the yaml that moved them.

⚠ Do not read this as licence to hand-edit a ledger number. Re-extraction regenerates
the ledger *from* yaml — the sanctioned direction. Editing a ledger to make drift go
away inverts the pipeline and is exactly what rule 3 forbids.

### 3.0d — Read before proposing pipeline architecture

[`design/BALANCE_PIPELINE_GAPS.md`](design/BALANCE_PIPELINE_GAPS.md) records what a single
deterministic command still lacks — no orchestrator among 50+ scripts, no exception registry, no
constraint reporting, no determinism check — and the verified residue of an outside review round
that produced a great deal of confident, contradictory material about this repository.

⭐ Its one transferable lesson: **a review of a repository snapshot is a review of a date.** Five
reviewers disagreed about whether the balance documents existed; all five were reading the tree
as it stood before the 83→43 compaction, and every path they called missing had simply moved.
Establish which commit an outside report saw before acting on it — `git log --all -- <path>`
separates "moved" from "never existed", and the substance of a stale report is often still good.

### 3.1 — The weapon rebuild (the main line)

⛔ **Set B (`mods/cameo/weapons/**`, `mods/cameo/ContentPacks/**/weapons.yaml`) is NOT free.**
Devin is working W2 in it — `IN PROGRESS (Devin, 2026-08-21)`, HeatRayBeam1-4 split, 28
`^LightFlameWeapon` matches left. Check `git log -3 <file>` and the file mtime before touching
anything in that set, and coordinate rather than assuming the 2026-08-15 lock release still
holds.

| step | what | how you know it moved |
|---|---|---|
| **W24** | collapse each fired weapon to ONE damage warhead (DESIGN §11b) | `multi_main_fired_weapons` is 192, down from 927; 299 remain when indirect weapon-graph reachability is included |
| **W23** | retrofit the legacy templates onto `^Warhead_*` families | from the 2026-08-23 baseline: `unconverted_template_inheritors` goes DOWN from 1162; `warhead_family_reach` goes UP from 1245 |
| **A5** | retire the remaining inline-`Versus` weapons onto templates | rule 4 — `Versus` only in `^Warhead_*` |

Method for one W24 cluster, in order (this is the procedure that has worked for seven clusters
and is written out in full in `BALANCE_PROGRAM_PLAN.md` §1b):

1. **Resolve and INLINE first**, remove inherits second, clean up third. Never reorder an
   `Inherits` block "cosmetically" — position is semantic (see the trap list below).
2. Collapse the mains into one warhead at the SUMMED damage; keep the percentage twin
   consistent (`formula.percentage_twin`, **not** `damage // 2000`).
3. Preserve every effect the weapon had: physical state, trail, ground/air/water effects,
   smudges, `Report:`.
4. `tools/audit/review_resolve_diff.py` — before/after resolve must show only the intended
   change.
5. `find_empty_warhead.py` = 0 · `audit_warhead_split` at or below baseline ·
   `audit_physical_state_warheads` PASS · `audit_balance_drift` clean.
6. Boot-gate. Then commit yaml **and** ledgers, and lower the baseline in
   `audit_warhead_split.py` if it moved.

### 3.2 — Independent of the main line (safe in parallel)

| item | set | note |
|---|---|---|
| **W7** Sonic → `Resonance` meter | D (`rules/defaults.yaml`) | **SHARED MERGED (EMBER, #476 → `e97924d4c`)** — pack-side in flight: DAWN done `388a7dd0d` on `devin/dawn/l4-fx` (needs PR), NOVA's 8 pending. ⚠ set D is ONE file — serialise W7/W9/W10, never two at once |
| **W9** `^Poisonable` → `Poison` meter | D | **SHARED MERGED (EMBER, #479 → `5b89b1341`)** — Ordos crossbow grant to DAWN via REQUEST (lands with her next PR); darkreign parked |
| **W10** `^Blindable` → `Blind` meter | D | **IN PROGRESS (EMBER, 2026-09-24)** — proportional range 100→20 via `ModifiesCombatProportionalToPhysicalState@Blind`, `|| blinded` appended to all 46 `disabled` pause sites, `RangeMultiplier@blinded` retired; SC×3 grants converted to `ApplyPhysicalState` `Amount: 20000`; RA Soviets + RA2Mod Syndicate → NOVA REQUEST |
| **WC2 heroes** | `mods/cameo/ContentPacks/Warcraft2/Humans/**`, `Orcs/**` | **IN PROGRESS (Devin, 2026-08-25)** — porting 4 hero units + weapons + icons from `wcameo(1)` with new `wc2_<faction>_<actor>` naming. Weapons done; actors, sequences, icons in progress. Check `git log -3` and mtime before touching this set. |
| **W12** superweapons as a separate track | — | maintainer-led; superweapons are not unit-priced |
| **Adopt the Sonic family** | B | `^Warhead_Sonic_*` bakes the mark but **nothing inherits it**, so it is inert. Needs a maintainer warhead order (rule 4). Law: an effect upgrade ADDS `^Warhead_Sonic_*`, it never replaces the base damage TYPE. |

### 3.2b — Absorbing the other OpenRA mods (measured 2026-08-23)

Plan and every number: [`design/UPSTREAM_MODS.md`](design/UPSTREAM_MODS.md).
Re-measure with `python tools/audit/audit_upstream_adoption.py` (in `run_all.sh`).

**Settled, do not re-derive.** The engine must NEVER move to `ca-engine` (it would discard 2 581
commits and delete `OpenRA.Mods.AS`); CA mod code comes FORWARD onto Cameo's engine. Measured from
the point where `cameo-engine` last took upstream OpenRA (`b0b0544d4a`, **2026-05-11**): Cameo is
1 975 commits of its own past it and only **70 behind `openra/bleed`**. RV and SP pin ANCESTORS of
`cameo-engine`, so they need **no engine work at all**. CN's own work is 170 enumerable commits on
newer bleed, so its engine patches ARE cherry-pickable. Generals Alpha needs no engine work either
— of the 49 commits its pin has that we lack, 41 are upstream bleed and 8 are maintenance.

⛔ **`mtr/rv-engine` is STILL MAINTAINED** (tip 2026-07-25) — Generals Alpha pins it. The RV *mod*
is dormant; the engine branch Cameo descends from is not. Any plan resting on "the RV engine is
dead" is resting on a false premise.

**`openra/bleed` is tracked as a sixth upstream** — the only one that is not a mod, because
absorbing it means MOVING THE ENGINE (the `cameo-engine` pipeline: merge → push → `ENGINE_VERSION`
in `mod.config` → `make.cmd all` → **recreate `engine/glsl/` shaders** → boot-gate), not copying
types. The 70-commit gap holds .NET 10, ARM packaging with x86/Mono dropped, a large Gustas
rendering/perf batch, several pathfinding fixes, and one real feature: **the Tiberian Sun Firestorm
Defense**. Not a free update — schedule it a session of its own.
`python tools/audit/audit_engine_freshness.py` reports the gap every suite run (it does not fetch;
`git -C ~/Documents/GitHub/cameo-engine fetch upstream mtr --no-tags` first).

**What is actually left, by TYPE** (Cameo resolves 1 101 yaml-visible names across 7 assemblies):

| mod | already here | duplicate under another name | real candidates | live in its own yaml |
|---|--:|--:|--:|--:|
| Generals Alpha | 2 of 23 | 1 | 20 | **20** |
| RV | 11 of 26 | 8 | 7 | 6 |
| SP | 7 of 46 | 7 | 32 | 31 |
| CN | 5 of 107 | 2 | 100 | 90 |
| CA | 182 of 348 | 35 | 131 | 119 |

⭐ **Start with Generals Alpha.** Smallest assembly, highest signal — 20 of 20 candidates are used
by its own rules, and they group into whole mechanics: a 9-type supply-dock economy Cameo has no
equivalent of, cash hacking, `LaysMinefield` (self-replenishing, NOT our ordered `Minelayer`),
`ConditionIconOverlay`, `PilotChamber`, `FakePower`. And it exposes a dead tag we already carry:
CA's `CashHackable` sits on two actors here while **no assembly Cameo loads has the power that
reads it** — adopting a `CashHackPower` (CA's or GenSDK's) is a one-file fix.

⛔ **A new NAME is not a new MECHANIC.** RV's `Temporal` + `AffectedByTemporal` are CA's
`WarpDamage` + `Warpable`, already wired to `ChronoBeam`. Both were ported, built clean and
reverted in one session. Read the DESTINATION — the actor, then its weapon — before porting
anything. Full account in [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md).

⚠ Order: Generals Alpha, then RV + SP (frozen, 37 live candidates), then CN, then CA. **Which mechanics Cameo wants is
a maintainer call** — §5 of the plan: 86 of the 142 CA trait types already vendored here are
unused, so wiring beats adopting.

### 3.3 — Bounded bug work (good for a short session)

From [`audit/SUMMARY.md`](audit/SUMMARY.md), smallest first:

1. **2 missing sequence images** (`audit/latest/sequences.md`) — player-visible, tiny.
2. **6 G1 garrison weapons** — armed garrison-capable infantry with no garrison weapon.
3. **1 unresolved fluent ref** — shows a raw key in-game.
4. **1 basebuilder faction without a crate** (28 of 29 covered).
5. **89 D1 duplicate-`Inherits` keys** — each one silently DROPS a template. This is the same
   family as the `Parent type X was already inherited` boot crash; triage before it bites.
6. **47 prerequisite-order violations** across 841 buildable combat actors.

### 3.4 — Documentation and tooling debt this pass left behind

* **`tools/audit/audit_damage_grid.py` is re-derived (2026-08-25) but NOT yet wired into
  `run_all.sh`.** It now imports `formula.DAMAGE_STEP` (100) and `formula.percentage_twin`
  instead of the retired 2000-step literals, so the ~300 false off-grid findings are gone
  (off-grid 83, unequal mains 215, basis-point percentage twin **0**, 50% twin 353 — all
  existing legacy debt). It carries a ratchet baseline per check and exits 1 only on a
  REGRESSION (count above baseline), so wiring it cannot block on the existing pile. The
  percentage-twin check is narrow on purpose: basis-point `AreaDamagePercentage` nodes
  (denominator 10000) are checked against `percentage_twin`; legacy whole-percent twins
  (denominator 100, deliberately left by W18) and folded `PercentageScale` dials (a free
  per-family dial, not a twin) are skipped. **Wiring is deferred until the W24 burn-down
  settles** — W24 is actively collapsing multi-main weapons and the fold is replacing
  separate twins, so the counts are moving targets and a gate could trip on in-flight
  conversions. Run on demand: `python tools/audit/audit_damage_grid.py`. It is the last
  of the three audits `audit_recent_changes` R2 flagged as unregistered (the other two
  are now in the suite).
* **`gen_sync` drift is 10, not 1** — and this one is real work, not bookkeeping. The accepted
  entry is `^Warhead_Sniper_Light` (a template the generator does not emit). The other **nine**
  are live disagreements introduced by the 2026-08-20 W24 chemical split, which edited the
  chemical warhead templates in `weapons.yaml` without updating the generator:
  `^Warhead_ChemCannon_{Light,Medium,Heavy}` and `^Warhead_ChemMissile_{Light,Medium,Heavy}`
  differ on `DamageTypes` (`TiberiumDeath` in the file vs `ExplosionDeath` from the generator)
  and on `Corrosion` (20/33 vs 50); `^Warhead_Chemical_{Light,Medium,Heavy}` differ on shape
  (`PhysicalStates:` map in the file vs `PhysicalStateName`/`PhysicalStateScale` from the
  generator). Decide which side is right per template, make the generator emit it, and then
  restate the expected drift in `BALANCE_PROGRAM_PLAN.md` §3 — the gate there still says
  "drift = 1", so it currently reads as passing when it is not.
* **`docs/design/invented_family_profiles.json` is stale, and regenerating it MOVES DATA.**
  Running `tools/balance/design_invented_profiles.py --write` today rewrites one family's
  `sharpness_intended`/`sharpness_shipped` (3.322 → 3.492) and its whole Versus row, because
  the inputs it derives from have moved since the JSON was committed. That is a balance change,
  not a documentation change — it needs the set-A owner and a boot gate, so this pass
  deliberately left it alone. (The count in the sheet is now derived from `len(DESIGNS)`
  instead of a hard-coded word, so it can no longer go stale on its own. To be clear: the
  sheet's "seven" is CORRECT — `Toxic` is the eighth family in the JSON but is **measured**
  from Cameo's own 28 gas weapons, not designed, so it is deliberately outside the table.)
* **`noid_resolved.json`** sits at the repo root as tracked UTF-16 with 79 209 null bytes — a
  PowerShell-redirect artifact. It is maintainer WIP, so it was left alone; it should be
  regenerated as UTF-8 or removed.
* **Comment-only mojibake** (`â€"` for an em dash) exists in a handful of `mods/cameo/**` yaml
  files. Cosmetic, comments only, another file-set's ownership — listed here so the next
  encoding sweep knows where to look.
* **36 `memory <name>` citations** across the design docs cannot be resolved by anyone but the
  agent that wrote them. Promote anything binding into `DESIGN.md`.

---

### 3.5 — Keeping the documentation from rotting again

Two audits now guard the docs themselves, and both run in `run_all.sh`:

| audit | catches |
|---|---|
| `audit_doc_claims.py` | a NUMBER in prose that no longer matches the tree. 19 claims registered in [`audit/doc_claims.yaml`](audit/doc_claims.yaml), each with the command that re-measures it. **When a claim legitimately changes, update `value` AND every file listed under its `docs:` key in the same commit.** |
| `audit_doc_health.py` | the documents being structurally broken: control characters, mojibake, a link to a missing file, an in-page `#anchor` link with no matching heading, a reference to a document that moved, two DESIGN sections sharing one id |

Neither existed before 2026-08-23, and every defect they check for was found by hand that
day. Add a claim to the registry the moment a decision starts resting on a number.

What they still cannot check is **prose contradicting prose** — a ruling written into one
document while the older statement stands in another. The only defence is the discipline:
**grep for the old claim before you write the new one, and strike it everywhere it appears.**

---

### 3.6 — Multi-agent coordination (2026-08-25)

⛔ **There are 5+ Devin agents running locally on the same branch.** Each must claim a
unique name, register in `DEVELOPMENT_LOG.md` → "Agent registry", and own a disjoint
file-set. **Before editing any weapon file, check its mtime and the registry.** If
another agent claimed it in the last 30 minutes, do not touch it.

**Agent registry** (maintained in `DEVELOPMENT_LOG.md` → "Agent registry", mirrored here):


> ⛔ **SUPERSEDED — this ownership table is STALE. The single authoritative roster is
> §3.A "Agent roster and current assignments".** It is kept only as provenance; it
> contradicts §3.A on who owns D2k/Harkonnen and on who the coordinator is. Do NOT
> claim a file-set from this table.

| name | identity | current file-set | current task |
|---|---|---|---|
| **Devin-Aether** | this session | `tools/audit/audit_damage_grid.py`, `mods/cameo/ContentPacks/TiberianSun/CABAL/`, `mods/cameo/ContentPacks/D2k/Ordos/` | W24 same-family collapses in CABAL/D2k-Ordos; audit tooling |
| **Devin-Dawn** | prior sessions (A10–A14 committer) | `mods/cameo/weapons/tiberiansun.yaml`, `mods/cameo/ContentPacks/RedAlert2Mod/TKM/`, `RedAlert2Mod/AsianAlliance/`, `RedAlert/Japan/`, `TiberianSun/GDI/`, `TiberianSun/Nod/`, `RedAlert/Shared/` | W24 bullet/missile collapses across multiple packs; ATMine rework |
| **Devin-Blaze** | active 2026-08-25 13:50 | `mods/cameo/weapons/d2k.yaml`, `mods/cameo/weapons/redalert2mod.yaml` | W24 bullet collapse for `LMG`, `light_inf_lmg`, `d2k_shotgun`, `naxis_sssoldier_smg` |
| **Devin-Cyrus** | active 2026-08-25 13:48 | `mods/cameo/ContentPacks/Warcraft2/Humans/`, `Warcraft2/Orcs/` | WC2 hero weapon rework (Alleria FirepowerMultiplier, Hellscream slice) |
| **Devin-Echo** | this session (SWE-1.7 Max, `devin@cognition.ai`) | `mods/cameo/ContentPacks/D2k/Ixian/`, `mods/cameo/ContentPacks/D2k/Ordos/`, `mods/cameo/ContentPacks/TiberianSun/CABAL/` | W24 A15: collapse `MongooseRocket`, `facedancer_grenade`, `D2K_APC_Rocket` to existing D2k 3-way families; analyze CABAL `CabalArtilleryWalkerShellUpgraded` / `CabalMothershipRockets` for design sign-off.

**Rules for all agents:**
1. Pick a unique name (`Devin-<word>`) and register in `DEVELOPMENT_LOG.md` before editing.
2. Own ONE file-set at a time. Do not edit files in another agent's set.
3. Shared bookkeeping files (`docs/audit/doc_claims.yaml`, `docs/HANDOFF.md`,
   `docs/audit/SUMMARY.md`, `docs/design/BALANCE_PROGRAM_PLAN.md`,
   `tools/audit/audit_warhead_split.py`) are **communal** — edit them only as part of
   your own batch commit, and re-read them before editing (they change every few minutes).
4. After every commit, post a summary to `DEVELOPMENT_LOG.md` with your agent name,
   what you changed, and why.
5. Before starting a new batch, re-read `DEVELOPMENT_LOG.md` → "Active claims" and
   verify no other agent claimed your target files.
6. **Never `git add -A` or `git add .`** — scoped adds only. Another agent's WIP is
   always in the tree.
7. Boot-gate before every weapon commit. If another agent's uncommitted WIP is in the
   tree, wait for them to commit before boot-gating (the boot tests the whole tree).

**Current locks (do not touch — verified 2026-08-25 13:52):**
- `mods/cameo/weapons/d2k.yaml` — Devin-Blaze (active 13:50)
- `mods/cameo/weapons/redalert2mod.yaml` — Devin-Blaze (active 13:50)
- `mods/cameo/ContentPacks/Warcraft2/Humans/yaml/weapons.yaml` — Devin-Cyrus (active 13:48)
- `mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/weapons.yaml` — Devin-Cyrus (active 13:48)
- `mods/cameo/weapons/weapons.yaml` — template generator/family work; do not edit
  without explicit generator/weapon-family sign-off.
- `mods/cameo/weapons/tiberiansun.yaml` — Devin-Dawn (recently active; check mtime)

**Free file-sets for the next W24 clusters (not locked, not claimed):**
1. `mods/cameo/ContentPacks/StarCraft/*/yaml/weapons.yaml` — StarCraft weapons
   (mixed Phase B; many need maintainer sign-off or a clear new family).
2. `mods/cameo/ContentPacks/D2k/Ixian/yaml/weapons.yaml` — D2k Ixian weapons
   (same-family candidates exist: `RaiderGuns` has a risky child — check first).
3. `mods/cameo/ContentPacks/D2k/Harkonnen/yaml/weapons.yaml` — D2k Harkonnen.
4. `mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/weapons.yaml` — TS Forgotten
   (A11 completed; verify no new multi-main appeared).
5. `mods/cameo/ContentPacks/RedAlert2Mod/` (excluding TKM/AsianAlliance, which are
   Devin-Dawn's) — FutureTech, Consortium, etc.

**Trap: dead-code overrides in `mods/cameo/weapons/redalert2.yaml`** — several weapons
are shadowed by later definitions in `ContentPacks/RedAlert2/Shared/`. Before converting
any weapon, resolve it with `cameo_model.py` and confirm the resolved file is the one
you are editing. Known shadowed: `RA2CRM60H`, `RA2SCUD`, `RA2MultiHoverMissile`, etc.

---

## 4. The traps that keep costing people time

Each of these is written up in full in [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md). This is the
index — read the entry before working in that area.

| trap | one-line form |
|---|---|
| `Inherits` POSITION is semantic | the LAST node wins, and `Inherits` is a node. Appended at the BOTTOM, the parent silently overrides the definition's own values. Tools that add an inherit must insert at the TOP. |
| `Parent type X was already inherited` | reaching the same parent twice along ONE chain is a boot crash. The `@suffix` does **not** make it legal — the guard is keyed on the parent TYPE. Order-dependent. Grep cannot find it; `audit_duplicate_inherits.py` reports all instances in one pass. |
| Empty warhead type | `Warhead@X:` with no type = boot NRE, and `--check-yaml` does not catch it. `find_empty_warhead.py` does. |
| Removal markers | `-Key:` crashes if the key no longer exists in the resolved chain. Strip stale removals — nested ones too — before boot-gating a conversion. |
| Child weapons after a parent conversion | children that override the OLD warhead key create an orphaned second warhead → **double damage**. Sweep children after converting any parent. |
| Dead yaml files | `mods/cameo/**/*.yaml` includes files `mod.yaml` does NOT load. Audits must read `Ruleset(ROOT).manifest.rules`, never a glob. A dead file is not evidence about what ships. |
| A missing `Versus` row | is not "no opinion" — an empty match returns 100, so a plated unit LOSES its armor. Every plating gets a row in EVERY template. |
| An armor upgrade must never increase incoming damage | DESIGN §12.0e law 4. Guard: `audit_armor_upgrade_harm.py`. |
| Bulk renames | never do a bare-identifier substitution: the same literal is a weapon, an actor, a condition and a sprite in this tree. Match the exact YAML field with a full-token comparison. |
| Loose `*_extracted/` map folders | `.oramap` is a zip; the packaged file is what ships and silently shadows loose edits. Repack in the same session, then validate with `--check-yaml`. |
| UTF-16 audit reports | a PowerShell `>` redirect corrupts them. `run_all.sh` only. |

---

## 5. Changing the engine

**First check whether a mod-side SHADOW avoids the whole procedure.**
`ObjectCreator.FindType` takes the first assembly in `mod.yaml`'s `Assemblies` list that holds
the name, and the order is **AS, CA, Cameo, Cnc, D2k, Common** — so an `OpenRA.Mods.Cameo` type
of the same name wins with zero yaml changes. Precedents: `ColorPickerColorShift`,
`PlayerColorShift`, `SelectionDecorations`. **Prove a shadow works** by giving the Cameo Info a
field the engine type lacks and booting with that field set — `--docs` lists both types and
proves nothing.

If you really need an engine change:

1. Edit C# only in the **separate `cameo-engine` clone** of `github.com/cameo-mod/OpenRA`
   (branch `cameo-engine`). Never in `engine/` here.
2. Commit and push to `origin/cameo-engine`; check `git status` for stray nested-clone entries.
3. `git rev-parse cameo-engine` for the **full 40-character** hash. Never hand-type or truncate.
4. Set `ENGINE_VERSION="<hash>"` in **`mod.config`** (not `mod.yaml`).
5. `make.cmd all` — the version mismatch makes the SDK delete `engine/`, refetch and rebuild.
6. Verify `engine/VERSION` matches and the build has 0 errors. **Recreate any `engine/glsl/`
   shaders** — the fetch wipes them (e.g. `postprocess_nuclearflash.frag`).
7. Boot-gate, then commit `mod.config` together with the doc updates.

---

## 5b. The shape of the documentation set

**44 live documents.** Everything else under `docs/` is generated (regenerate it) or archived in
`history/` (what happened, never what is true now). [`README.md`](README.md) lists the whole live
set in one table — if a document is not in that table, it is not live.

The set was 83 documents on 2026-08-23. It came down by **merging overlapping documents**, not by
deleting content: every merged file's body was carried across verbatim under its own heading with
its original path recorded. The clusters that collapsed:

| now | was |
|---|---|
| `design/ARMOR_LAYERS.md` | 5 files — pseudo-armor, shield normalisation, 2 plating docs, superweapon layering |
| `design/PROJECTILE_AND_EFFECT_LAYER.md` | 3 — projectile templates, per-game sourcing, game-specific bases |
| `design/RESEARCH_NOTES.md` | 5 — SP research, mission win/lose, CABAL rebuild, SM artwork, tier-chain |
| `design/DECISIONS.md` | 3 — hex shields, vehicle queue split, derived stats in traits |
| `design/WEAPON_HEAVINESS.md` | 2 — the research and the continuous scale |
| `design/AREADAMAGE_WARHEAD.md` | 2 — the rebalance and the unified node |
| `reference/WARHEAD_REFERENCE.md` | 3 — family profiles, versus archetypes, archetype tables |
| `balance/formula_v2_classes.md` | 4 per-class logs + the delta audit |
| `design/BALANCE_PROGRAM_PLAN.md` §7 | `BALANCE_MEGAPLAN.md`, which had spent two weeks disagreeing with §0a about order |

13 stale generated per-class proposals were deleted rather than merged — they regenerate with
`propose_class_rebalance.py --class <name>`, and the committed copies no longer matched the tree.
Ten finished or dormant working notes moved to `history/`.

**If you are about to add a document, don't.** Add a section to the one that already owns the
topic — the table in `README.md` says which. A new file is justified only when no existing
document owns the subject, and then it goes in that table in the same commit.

---

## 6. What this handoff replaces

Every document below is archived, banner-stamped, and **must not be resumed from**. They are
kept for provenance and for the technique notes inside them.

| archived | was |
|---|---|
| [`history/handoffs/AI_AGENT_HANDOFF_2026-07-25.md`](history/handoffs/AI_AGENT_HANDOFF_2026-07-25.md) | session log for the 2026-07-24 yaml-lint incident |
| [`history/handoffs/SESSION_CHECKPOINT_2026-08-03.md`](history/handoffs/SESSION_CHECKPOINT_2026-08-03.md) | compaction anchor on a long-merged branch |
| [`history/handoffs/AREADAMAGE_HANDOFF_2026-08-04.md`](history/handoffs/AREADAMAGE_HANDOFF_2026-08-04.md) | the AreaDamage conversion (complete) |
| [`history/handoffs/AI_HANDOFF_2026-08-05.md`](history/handoffs/AI_HANDOFF_2026-08-05.md) | the weapon-work must-read CLAUDE.md used to point at |
| [`history/handoffs/CLAUDE_HANDOFF_2026-08-11.md`](history/handoffs/CLAUDE_HANDOFF_2026-08-11.md) | agent letter; became W15–W19 on the board |
| [`history/handoffs/DEVIN_HANDOFF_SP_RESEARCH_2026-08-11.md`](history/handoffs/DEVIN_HANDOFF_SP_RESEARCH_2026-08-11.md) | Shattered Paradise parity research |
| [`history/handoffs/DEVIN_REPLY_2026-08-11.md`](history/handoffs/DEVIN_REPLY_2026-08-11.md) | agent letter; its pipeline fixes shipped |
| [`history/MEGAPLAN_2026-08-08.md`](history/MEGAPLAN_2026-08-08.md) | thin program index, superseded twice over |
| [`history/ROADMAP_ARCHIVE_2026-07.md`](history/ROADMAP_ARCHIVE_2026-07.md) | 14 fully-closed ROADMAP sections |
| [`history/audits/`](history/audits/) | two one-off dated infantry audits |

**The rule that keeps this file from becoming one of them:** a handoff records STATE, and state
rots. When you finish a session, update **this** file — do not write a new dated one. If a
statement here disagrees with the tree, the tree is right; fix the sentence.

## 2026-09-14 — SEVEN INI SOURCES BYTE-PINNED; ROLE VOTES FAIL CLOSED PER ARMAMENT

The exact external INIs for CnC Reloaded, Mental Omega, RA2 0XX, RA2 Reborn, Red Resurrection,
Rise of the East and Twisted Insurrection were received and verified against their supplied
SHA-256 manifest. `docs/reference/ini_source_pins.json` records hashes only; the third-party rules
text remains outside git.

`tools/reference/ini_source_pins.py` proves the current corpus points back to those bytes at the
scope needed for later role extraction: all **10,144** rows match their actor Primary/Secondary
slots and every cited weapon-to-projectile link. The 64 historical promoted-secondary occurrences
(63 identities; duplicated Red Resurrection `NAFLAKAI1`) are preserved exactly and are explicitly
not re-approved by this operation. `docs/reference/ini_corpus.json` gains only `source_sha256` on
those rows; no value, order, duplicate, selection, damage, range or cadence field changes.

`extract_ini_armament_roles.py` now admits only the safe subset. It re-verifies all seven files and
the corpus weapon-link fingerprints, then reads each cited weapon directly from those exact bytes.
RA2/YR needs explicit valid `AA` **and** `AG`; Twisted Insurrection may use the documented TS
defaults. Each slot must independently be `nominal_direct`, carry usable positive finite values,
and have `Burst = 1`. Missing defaults, invalid booleans, incomplete/effect weapons and multi-shot
weapons abstain. The sidecar resolves **496 of 2,461** cited armaments; 1,965 remain explicitly
withheld.

The regenerated per-armament map forms **333** pairs (226 exact, 107 via a proven `both` stand-in).
The source-role gate moved 308 to 332 through 59 proof-backed additions and 35 DTA withdrawals;
the exact missing-reference follow-up added one more pair. The Apocalypse tank now
has one explicit Mental Omega AA-missile
vote; its cannon still abstains. No corpus regeneration, assignment change, historical selection
approval, gameplay value, `apply_balance`, protected classifier or 694-cycle inference is included.

The canonical full reference page `docs/audit/latest/reference_map_clean_20260911.html` is
regenerated from the current tree. The current tree has **29** non-WIP
faction ledger prefixes rather than the requested historical count of 28, so all 29 are included;
only `plymouth` and `eden`, both explicitly labelled WIP, are excluded. The page reports 161
original and 709 expanded actors, 925 attached references, 514 formula-priced actors and 8
rendered originals below three sources.

The follow-up original-reference review added ten exact, unclaimed mappings: Valiant Shades'
side-specific Allied/Soviet Engineers, four source-specific Soviet Sentry Guns, Shattered
Paradise's GDI MCV, Crystallized Nexus's Mobile Sensor Array and two source-specific Nod Militants.
The Sentry Gun, GDI MCV, Mobile Sensor Array and TS Nod Light Infantry now meet the three-source
floor; both RA2 engineers improve from one to two. O1 has 10 total rows, with 8 gating and two
documented source-impossible RA1 exceptions. Its
missing-source column now uses each faction's actual routes instead of claiming CA/DTA are
required for RA2 and TS. The bot-only empty Battle Fortress variant remains separate and did not
steal `BFRT` rows from the real Battle Fortress.


## 2026-09-28 — A/B duel standard: Frankenstein vs omniscient classic on "A Nuclear Winter"

Maintainer ruling: every bot-vs-bot test runs on the real tournament duel map
**A Nuclear Winter** (extracted at runtime from the shipped
`mods/cameo/maps/_ra_a-nuclear-winter.oramap`), both real spawns, locked `gamespeed: maximum`
(speed raised from `insane` per maintainer order 2026-09-29).
`tools/ai/run_ai_match_batch.py` defaults its template there (old synthetic
gate fixture remains via `--template` for debugging only).

Acceptance criterion for the merged "Frankenstein" stack (Cameo x CA x CN x
Fransbot modules, `UseFoggedObservation: true`, no global vision): it must beat
the **`classic`** bot type — the pre-Cognition-wave module stack at hard
strength with `RevealsMap` omniscience — fighting smart, not hard.

`classic` is defined in `mods/cameo/ai/ai.yaml` (`ModularBot@ClassicAI`,
Type `classic`): eighteen pre-wave modules re-gated `genericbot || classicbot`,
the pre-wave `SquadManagerBotModuleCA@generic` config restored verbatim as
`@classic`, `hardbot` granted for the hard-tier limits/prereqs, and
`RevealsMap@classic` on its PlayerActor. See DEVELOPMENT_LOG.md 2026-09-28.
