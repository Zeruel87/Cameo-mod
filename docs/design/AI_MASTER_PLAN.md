# The Frankenstein bot — master plan: six parents, measured status, every remaining step, effort

> **Maintainer order (2026-09-30):** *"our Frankenstein monster bot is meant to combine everything
> from OpenRA, Romanov's Vengeance, Cameo, Combined Arms, Crystallized Nexus and the Fransbot and
> add all the bot modules from those references one by one, merging them together so they will
> fit and match as well as possible … I need to see a complete plan."* Ruled in the same message:
> **all difficulties scale in equal steps**, which includes the Fransbot modules (§4).
>
> **What this document is.** It is the single work queue for the bot. The work lists in
> `AI_ARCHITECTURE.md` §12.10, `AI_DEEP_RESEARCH.md` §9 and `AI_SYNTHESIS.md` §7.4 are merged into
> one table here (§3), with owners, dependencies and a three-point estimate. Those documents keep
> the *designs*; this one keeps the *order and the state*. Update the state column here (and the
> ROADMAP line) in the PR that changes it.
>
> **Measured on master `bf2b30883`** (2026-09-30, after the merge-all integration #660).

---

## 0. The answer in six lines

1. **The method is a harvest, one module at a time.** For each layer of the bot (perception, space,
   threat, strategy, squads, economy, expansion, air, naval…) we pick the best parent's code by
   reading it, port it under Cameo's contracts, switch it on behind a yaml flag, and keep it only if it
   **wins a Nuclear Winter A/B** against master (§1).
2. **Harvest so far:** RV and CA are fully merged (140 protected symbols); Cameo's own phases 1–7a and
   the combined-arms foundations ship. From **CN only 1 of ~16 modules** runs as code
   (`CombatAnalysisBotModule`; three more re-implemented from its ideas). From **Fransbot, 8 of 24**
   modules run in the Frankenstein bot, and only as record-only services on `hard` (#656).
3. **Research status (§2):** of the research round's ten headline changes, **1 is done, 4 are
   partial, 5 are not started**. Of the twelve "beat the best humans" items, **0 are done, 9 are
   partial, 3 are not started**. The combined-arms phases are mostly partial or in flight.
4. **What is left:** 55 work items (§3), **~956 agent-hours expected (≈191 sessions of 5 h)**,
   520 h if everything goes well and 1,604 h if everything goes badly, plus **42 A/B gates**
   worth 60–120 hours of match compute on this machine.
5. **Calendar:** with four agents in parallel that is ~43 sessions each, **about 3–6 weeks** of
   fleet time at 1–2 sessions per agent per day. The real limits are A/B compute (one shared machine) and the order of the critical path
   (§4), not typing speed. The Devin fleet is booked until ~2026-10-22, so the plan puts the
   highest-value items first.
6. **Critical path:** CA-1 → CA-3 → CA-4 → **UT** (the utility strategist that unifies the squad
   managers) → DI/TC/§13, with **ZG → IM** (CN's chokepoint map) feeding UT. UT is the largest single
   item and the point where the six parents truly become one bot.

---

## 1. How the six parents become one bot

### 1.1 The parents

| Parent | How its code reaches Cameo | Harvested so far (measured 2026-09-30) | Its best, still unharvested parts |
|---|---|---|---|
| **OpenRA** (engine `OpenRA.Mods.Common` bot modules) | the engine pin (`mod.config`) | the base of the stack: harvester, support powers, repair, `McvExpansionManager` (+ the EX-3 site hook, `d5d8b2a685`) | unloaded, evaluated (RV1): `BevManager` (base-expansion vehicles: the decision EX and `McvExpansionManager` own, so merged into the MCV owner if ever needed, never loaded beside it), `SharedCargo` (for the returning Generals factions' GLA Tunnel Network, DESIGN §19.4). `CncEngineerManager` was loaded beside the CA capture manager until ENG merged the two into `EngineerBotModule` (DESIGN §19.3; `classic` keeps the CA copy alone). The double repair owner is fixed (RV1, #664): `genericbot` runs the merged `BaseRepairBotModule` (DESIGN §19.3); `SupportPowerBotModule` + `SupportPowerBotASModule` are the next duplicate (RV2) |
| **Romanov's Vengeance** (engine fork + `OpenRA.Mods.AS`) | the engine pin; RV features merged into the CA copies | guerrilla squads, stuck-kick / make-way, base expansion fields: **65 protected symbols** | — (merged) |
| **Combined Arms** (`OpenRA.Mods.CA`) | hand copy, `audit_ca_drift` + `ca_vendor_sync` | squad manager + states, base/unit builders, compositions, fuzzy attack-or-flee | **upstream drift not yet synced:** "Updated AI routing", "harasser squads", "AI updates" (2025-08), air fixes (F2) |
| **Crystallized Nexus** (GPLv3, `crystallized-nexus` `30cf70a`, unchanged upstream) | port by module | `CombatAnalysisBotModule` (code); staging, observer-gated artillery, priority tags (ideas) | **`CNTacticalMap`** (chokepoints and doors from the pathfinder graph → ZG), wave and pincer attacks, garrison, repair manager, bridge repair, cliff demolition, deploy, veinhole assault, stealth / subterranean / transport states |
| **Fransbot** (`OpenRA.Mods.Fransbot`, V1.29.31) | vendored whole (route A), harvested per module (route B) | 8 service modules on `hard` (combat intel, strategic map, risk model, mine clusters, economic saturation, commander core, command bid, general), record-only; the siege advisor seam (#656) | ForcePreservationGuard (CA-2), AirCommander strike logic (CA-5), **MCV island expansion + transports (13.5k lines)**, SpecOps, sea commander, support coordinator |
| **Cameo** (`OpenRA.Mods.Cameo`) | own | master module + fog memory + scouting + missions, personalities, counter demand, combat predictor, arsenal ledger, predictive defence, roles, expansion planner EX-0…3, scout/garrison fixes, lead telemetry | the rest of this plan |

### 1.2 The harvest pipeline: the same seven steps for every module

1. **Map it to a layer** in AI_SYNTHESIS §7.2's table, and name the Cameo owner of that decision.
   **One owner per decision** (AI_ARCHITECTURE §10.1): a harvested module *replaces* or *feeds* the
   current owner, never runs beside it. The double repair owner (fixed in RV1) showed what happens otherwise.
2. **Pick the best-of by reading the code** of every parent that has the layer. Record the pick and
   the reason in §7.2 before porting.
3. **Port under Cameo's contracts:**
   * **fog-honest:** `audit_fog_honesty` must stay green; every new enumeration site is a reviewed
     manifest entry;
   * **no faction ids:** rules-derived roles and tags (`BotRoleSets`, §2.8), never id lists;
   * **no cheats, host-only**, orders only (§1.1);
   * **claim before a long-lived assignment** (LC1): a module that sends an actor on a job claims it and releases it
     when the job ends; `Actor.IsIdle` is never ownership (AI_REVIEW_FRANSOTTO §1, P0b);
   * the **CA hand-copy stays protected:** new symbols go into `ai_frankenstein_manifest.json`;
   * the **engine** only via the canonical pipeline, preferring a small hook (the EX-3 pattern) or a
     Cameo shadow;
   * **licence:** keep the upstream header (GPLv3) and a "Ported from" line.
4. **Telemetry first:** the module logs its decisions (`debug.log`, situation log) and changes no
   behaviour.
5. **Behaviour behind a yaml switch**, default off in C#, on for `genericbot`; `classic` stays the
   untouched reference.
6. **A/B gate:** ≥ 8 matches per arm on A Nuclear Winter, both spawns, vs master in the same session,
   plus `army_mix_report.py` for composition sanity. From F3 on, also a league score. It lands only if
   it does not lose.
   **Amended by the maintainer, 2026-10-01 — the A/B unit is the INCREMENT, not the PR:** *"I don't have enough
   time to test every single little incremental step … the increments should include the work of all the agents
   combined … then create a new increment which should be A/B tested thoroughly."* Every agent's open work is merged
   into one increment (`inc/<date>`), which lands on master after build + tests + audits + boot gate with each new
   behaviour behind its switch; the increment's A/B then runs ALL its switches ON against the previous master
   (≥ 16 matches per arm, **MIRROR matches only** — `--factions td_gdi` and `--factions td_nod` as separate
   shards, never the cross pairing: *"Why would you run GDI vs Nod if they are not balanced yet? Nod is going to win
   every single time"* (maintainer, 2026-10-01) — swapped spawns, arms in parallel, early stop once the verdict cannot flip).
   Telemetry attributes inside the increment (`ownership`, `order_gate`, mission stories); a LOSING increment is
   bisected by switch groups, never re-tested PR by PR.
7. **Difficulty (§4):** its strength knobs go on the §19.1 line for all ten tiers. The donor's own
   copy is then deleted from the `fransbot` bot type; when nothing is left, the `fransbot` type goes
   too (§7.4 step 7).

### 1.3 Keeping the parents current

CA: `audit_ca_drift` + `ca_vendor_sync` (a standing duty). Fransbot: `fransbot_drift_baseline.json`
+ re-vendor (DAWN). CN: static since `30cf70a`, checked each month. OpenRA/RV: the engine pin; the
`cameo-engine` branch now equals the pin (`d5d8b2a685`), and LESSONS_LEARNED records the check.

---

## 2. Status of the research, measured

"Done" means it runs in `genericbot`; "partial" means some of it runs, or it runs record-only;
"none" means no code on master. Evidence is the class or tool named.

### 2.1 The research round's ten headline changes (AI_DEEP_RESEARCH §0)

| # | Change | Status | Evidence / what is missing |
|---|---|---|---|
| 1 | CP combat predictor as the single engage/retreat authority | **partial** | `BotCombatPredictor` drives squad engage/retreat (#623, `RetreatRatioPct` 0.1–1.0); learned per-type strengths missing |
| 2 | ZG zone graph (CN topology) | **none** | no port of `CNTacticalMap`; `RegionMemory` is still a square grid |
| 3 | IM influence layers | **none** | needs ZG |
| 4 | UT utility strategist (one squad manager) | **none** | six condition-gated personality squad managers (rush, turtle, tech, expansion, steamroller, guerrilla) + `@classic` |
| 5 | MI budgeted micro | **none** | `IBotActionBudget` exists; no focus-fire / kite / pull-back |
| 6 | OM opponent model + bandit | **partial** | `fit_arsenal_priors.py` (per-enemy-faction trade profiles, Elo); nothing read in-game; no bandit |
| 7 | LG league harness | **done** | `run_league.py`, `league_standard.json` (#625) |
| 8 | Difficulty = delays + self-preservation, no cheats | **partial** | 15 `BotLimits` fields on the §19.1 line; tier-gated modules break it (§4) |
| 9 | DI Director | **none** | — |
| 10 | LA offline analyst | **partial** | `fight_report.py`, `ab_summary.py`, `army_mix_report.py`; no analyst loop |

### 2.2 Beating the best humans (AI_DEEP_RESEARCH §13)

| # | Item | Status | Evidence / missing |
|---|---|---|---|
| 1 | discipline telemetry (idle queues, banked cash, brown-outs) | partial | `idle_queues`, banked cash in the stats timeline; brown-outs not tracked, nothing driven to zero |
| 2 | pressure on several fronts | partial | guerrillas always on, several squads (DESIGN §19.1a) |
| 3 | base trade and counter-attack | partial | DF-3/4 punish an army that left home |
| 4 | refuse the bait | partial | CP + siege telemetry (CA-2 behaviour off) |
| 5 | unpredictable on purpose | partial | random personality draw + switching; no opening/path distribution |
| 6 | hit power windows | none | — |
| 7 | superweapons both ways | partial | engine power targeting; no dispersal |
| 8 | keep veterans alive | none | — |
| 9 | map control and vision posts | partial | `ScoutBotModule` + spawn recon; no watcher posts |
| 10 | learn from our best humans | none | the match log records bots only |
| 11 | ratings | partial | Elo in `fit_arsenal_priors.py`; not tracked per bot version |
| 12 | robustness watchdogs | partial | RV stuck-kick / make-way; no idle-army watchdog |

### 2.3 The combined-arms phases and the other programmes (AI_ARCHITECTURE)

| Phase | Status | Evidence / missing |
|---|---|---|
| CA-1 arsenal tracker | partial | `BotArsenalLedger`, roles; in-match production weight missing |
| CA-1b offline fitter | partial | tool shipped; `mods/cameo/ai/learned/` does not exist yet |
| CA-2 siege | partial | `SiegeEvaluatorBotModule` telemetry + failure memory (#656); behaviour switched off |
| CA-3 role mix | in flight | `nova/ca3-role-mix`, `nova/ca3-stage-gate` (unmerged) |
| CA-4 formation | in flight | `nova/ca4-formation` (10 commits, unmerged) |
| CA-5 air doctrine | in flight | AA-aware air routing; roles applied to doctrine fields + role squads behind `AirDoctrineEnabled` (off) (#648, this PR) |
| CA-6 scouting → target | partial | spawn recon; `WeakIncludesDefence` knob off |
| DF predictive defence | done, A/B pending | `BotThreatTracker`, DF-1…4 |
| SG scouts + garrisons | done | #647 |
| EX expansion planner | partial | EX-0…3 (#651–#654); EX-4 creep, towers, MCV escort missing |
| PL personality leads | partial | Steamroller + Rush telemetry (#658); four personalities and every budget lean missing |
| TC Team Commander | none | — |
| §2.9 empty `ai.yaml` | partial | P0 equivalence gate; roles applied: harvester, refinery, conyard, guerrilla; P1–P7 open |
| §6.4 learning between matches | none | designed (L0–L5, §6.4a); serious training waits for the balance freeze (DESIGN §19.2) |
| human-like (AI_SYNTHESIS §5) | partial | action budget + `HumanPaceBotModule` (limits 0, no APM cap by ruling); no reaction delays or controlled mistakes |

---

## 3. Every remaining step

Hours are focused agent work, three-point PERT as in `BALANCE_PIPELINE_ESTIMATE.md`
(`E = (O + 4M + P) / 6`; a session is 5 h). A/B compute is counted separately (§4.1). Owners follow
AI_ARCHITECTURE §12.10 and the 2026-09-29 "split by owner" ruling; a lane may be re-assigned when an
agent leaves.

**Foundations (every harvest needs these)**, expected 89 h

| id | work | owner | needs | O | M | P | E |
|---|---|---|---|--:|--:|--:|--:|
| F1 | Difficulty: every module on every tier, strength on the §19.1 line (Fransbot service modules first) | Claude | A/B of #656 | 6 | 10 | 18 | 11 |
| F2 | CA upstream sync: routing, harasser squads, 'AI updates', air fixes (ca_vendor_sync + manual 3-way) | Claude | — | 8 | 16 | 30 | 17 |
| F3 | A/B throughput: nightly queue, league as the default gate, auto-summary (ab_summary + army_mix) on the PR | EMBER | — | 4 | 8 | 14 | 8 |
| F4 | §2.9 empty ai.yaml P1–P7 (roles replace every id list) | Claude | F1 | 30 | 50 | 90 | 53 |

**Combined arms (AI_ARCHITECTURE §12)**, expected 173 h

| id | work | owner | needs | O | M | P | E |
|---|---|---|---|--:|--:|--:|--:|
| CA-1 | finish: apply roles, in-match production weight | Claude | — | 8 | 14 | 24 | 15 |
| CA-1b | priors file from harness ledgers | Claude | F3 | 4 | 8 | 14 | 8 |
| CA-2 | siege behaviour on (advisor) + ForcePreservationGuard harvest | DAWN | CA-1 | 12 | 20 | 36 | 21 |
| CA-3 | role-mix production + squad composition (in flight) | NOVA | CA-1 | 10 | 16 | 28 | 17 |
| CA-4 | formation movement (in flight) | NOVA | CA-3 | 12 | 20 | 36 | 21 |
| CA-5 | air doctrine: gunship CAS, fighter pick-off, bomber strike teams (FransAirCommander) | EMBER | CA-1 | 16 | 28 | 48 | 29 |
| CA-6 | scouting decides the target (spawn recon, beatability) | DAWN | CA-1 | 8 | 14 | 24 | 15 |
| EX | EX-4 enemy creep × difficulty × aggression; towers per field; MCV escort (NOVA hook); income floor | Claude | — | 10 | 16 | 28 | 17 |
| PL | personality leads: Expansion/Turtle/Tech/Guerrilla telemetry + the budget lean for all six | Claude + NOVA + DAWN | — | 12 | 20 | 34 | 21 |
| DF | predictive defence: A/B + tuning | Claude | — | 4 | 8 | 14 | 8 |

**Research round 2 (AI_DEEP_RESEARCH §9, §11, §13)**, expected 273 h

| id | work | owner | needs | O | M | P | E |
|---|---|---|---|--:|--:|--:|--:|
| ZG | zone graph: port CN CNTacticalMap (chokepoints, doors), precomputed zone paths | NOVA | — | 20 | 36 | 60 | 37 |
| IM | influence layers on the zones (threat, strength, interest, decay) | NOVA | ZG | 12 | 20 | 36 | 21 |
| UT | utility strategist: one blended squad manager over the bipolar axes | NOVA | CP, IM, CA-3 | 30 | 50 | 90 | 53 |
| MI | budgeted micro: focus fire, kiting, pull back damaged, concave | EMBER | CP, CA-4 | 16 | 28 | 50 | 30 |
| CP | combat predictor: learned per-type strengths (the rest ships) | Claude | CA-1b | 6 | 10 | 18 | 11 |
| OM | opponent model: per-enemy-faction profiles + bandit openings | Claude | CA-1b | 10 | 18 | 30 | 19 |
| DI | Director: tension-curve pacing vs humans, no cheats | NOVA | UT | 10 | 16 | 28 | 17 |
| LA | offline analyst loop (agent reads logs, proposes knob changes) | Claude | F3 | 4 | 8 | 14 | 8 |
| TC | Team Commander + 2v2 harness | DAWN | UT | 20 | 32 | 56 | 34 |
| H13 | beat-humans list §13: power windows, superweapon dispersal, veterans, vision posts, human rows, ratings, watchdogs | all | UT, MI | 24 | 40 | 70 | 42 |

**Parent harvest (AI_SYNTHESIS §7.2)**, expected 181 h

| id | work | owner | needs | O | M | P | E |
|---|---|---|---|--:|--:|--:|--:|
| FB1 | Fransbot MCV/island expansion + transports + ground transfer (13.5k lines, V1.29.31) | DAWN | EX | 30 | 50 | 90 | 53 |
| FB2 | Fransbot SpecOps (capture, demolition, Tanya C4) — **incl. ENG-T** (maintainer 2026-09-30): implement `IBotCaptureTransportProvider` (CA; consumer `EngineerBotModule.TransportChance`, built) over `IFransCaptureTransportService`: a run carries 1–5 engineers into the enemy base around its army and defences, drops ONE next to each building and drives on (or unloads all at the first stop and each runs to its own building), then the A/B at `TransportChance: 25` | DAWN | CA-6 | 10 | 18 | 30 | 19 |
| FB3 | Fransbot sea commander (naval squads) | EMBER | CA-5 | 12 | 20 | 36 | 21 |
| FB4 | Fransbot support coordinator (powers timed with assaults) | EMBER | CA-5 | 6 | 10 | 18 | 11 |
| CN1 | CN waves + pincer attacks | NOVA | UT | 12 | 20 | 36 | 21 |
| CN2 | CN garrison + repair manager | DAWN | — | 6 | 10 | 18 | 11 |
| CN3 | CN bridge repair, cliff demolition, deploy, veinhole assault, stealth/subterranean/transport states — **deploy done (`M_cn3_deploy`); bridge repair done (`X_cn3_bridge_repair`, `devin/dawn/cn3-bridge-repair`, `BridgeRepairBotModule` — runs beside EngineerBotModule's own RepairBridge job only when armed); cliff demolition + veinhole assault content-blocked (no `CNDestroyableCliff` actors; `forgotten_veinhole` is a nuke silo); stealth/subterranean/transport states remain** | DAWN | — | 16 | 28 | 50 | 30 |
| RV1 | **done (#664, merged 2026-09-30 on the maintainer's order before its A/B finished; the A/B completes as a post-merge check):** `genericbot` runs `BaseRepairBotModule`, OpenRA + CA repair merged (DESIGN §19.3); classic runs only the CA copy, the OpenRA module is unloaded; BevManager and SharedCargo held for content (DESIGN §19.4); CncEngineer already loaded (§1.1) | Claude | — | 4 | 8 | 14 | 8 |
| RV2 | **implemented by EMBER (INC-ready, PR open — awaiting Claude merge):** merge `SupportPowerBotModule` (OpenRA, 9 powers, no condition: also runs for `fransbot`) into `SupportPowerBotASModule` (210 powers) — done yaml-only: OpenRA copy gated `classicbot` (classic keeps its copy), genericbot gets `SupportPowerBotASModule@wc2` holding all 9 WC2 decisions, the 28 `IgnoreVisibility: true` flipped false (seen/remembered only; classic unaffected under RevealsMap), ratchet re-baselined 56→28; the WC2 Blizzard and Death and Decay are in both today. Then review the 30 world-enumeration sites `audit_fog_honesty` began counting on 2026-09-30 (`ActorsWithTrait`) against DESIGN §19.5, and the **28 `IgnoreVisibility: true` power decisions** (NOVA, 2026-09-30: `SupportPowerBotASModule` then targets unseen enemies; EMBER's LC6 ratchet counts 56 resolved): for `genericbot` the merged owner targets seen or remembered (frozen) actors only; `classic` keeps its copy | Claude | — | 3 | 6 | 12 | 7 |

**Lifecycle hardening (the Fransbot author's review, [`AI_REVIEW_FRANSOTTO_2026-09-30.md`](AI_REVIEW_FRANSOTTO_2026-09-30.md))**,
expected 85 h. Every finding was verified in the code first (that document's §1); the review itself is the
author's own file, [`../FRANSBOT_AI_REVIEW_2026-09-30.md`](../FRANSBOT_AI_REVIEW_2026-09-30.md). **LC1 and LC5 gate the harvest
items** (CA-5's air commander, FB1–FB4, CN1–CN3): no more brains until ownership is a contract.

| id | work | owner | needs | O | M | P | E |
|---|---|---|---|--:|--:|--:|--:|
| LC1 | **contract + first consumers done 2026-09-30 (#668)** (`IBotUnitLeases`, `BotUnitLeaseRegistry` for genericbot; capture manager, crate pickup, scouts and beacon responders claim; scouts/responders renew as a heartbeat); still open: squads (NOVA's lane); the engineer module claims through ENG. Unit lease contract (`ActorID → owner, purpose, acquired tick, expiry`; `TryClaim` / `Release` / `IsClaimedByOther`), a small common service, first consumers engineer, capture, scout, beacon, crate; the SiegeEvaluator pattern (advisers advise, one module orders) | Claude | — | 8 | 14 | 24 | 15 |
| LC2 | **done 2026-09-30 (#667):** `CratePickupBotModule`: `alreadyPursuitCrates` → reservation `crate → collector + tick`, released when the crate or collector goes, the collector is claimed elsewhere, idles past a grace period, or times out | Claude | — | 1 | 2 | 4 | 2 |
| LC3 | **first half done 2026-09-30 (#667: path check + park after 3 hand-outs, `McvMaxSiteHandouts`)**; still open: EX-3 failure lifecycle via the engine: the planner checks the MCV's locomotor path to the field and parks a field it keeps handing out with no yard founded; then a candidate object (site, field id, kind, score, reachability) with accepted / unreachable / undeployable / reserved feedback via the engine hook; "not land-reachable" kept as a class for FB1 transports | Claude | — | 4 | 8 | 14 | 8 |
| LC4 | **done 2026-09-30 (#667 planner resource map; #677 `BotLimitsResolver`: squad, harvester and MCV managers re-check `BotLimits` on their first tick, logged — measured "kept" ×4, nothing stale; every other enabled-filtered lookup resolves at use):** first instance fixed 2026-09-30 (#667: `ExpansionPlannerBotModule.resourceMap` re-resolved at use); conditional-trait cache sweep: every `TraitsImplementing<T>()` filtered by enabled state and stored (the SiegeEvaluator bug class) — cache all instances and check at use, or refresh on transitions; assert single providers instead of trusting enumeration order | Claude | — | 3 | 6 | 12 | 7 |
| LC5 | ownership watchdog (debug/test builds): one exclusive owner per actor, every active actor owned, one squad manager per squad member, no dead actor reserved, released actors reach the idle pool. **Built 2026-09-30 (`claude/lc5_ownership_watchdog`):** `BotOwnershipWatchdog` (read-only, `genericbot || classicbot`, active in bot-only matches and with `Debug.BotDebug`) checks DOUBLE_OWNER / TWO_SQUADS / HELD_BY_DISABLED / DEAD_HELD / ORPHAN once per unit (`LC5 OWNERSHIP` in debug.log) and writes per-bot `ownership` counts into `cameo-ai-matches.jsonl`, so every A/B reports ownership health per arm. **First smoke (hard vs classic, td_gdi):** `CratePickupBotModule` leases squad members it found `IsIdle` (Guerrilla/Protection squads) — the review's P0b class, live; squads adopting LC1 (#681) closes it | Claude | LC1 | 6 | 10 | 18 | 11 |
| LC6 | semantic fog canaries: an unseen actor / crate / building must not change any decision until observed (the two DESIGN §19.5 exceptions excepted) | EMBER | — | 4 | 8 | 14 | 8 |
| LC7 | A/B fingerprint: mod commit, engine commit, resolved AI yaml/rules hash, map hash, bot type/personality config recorded per batch; any change mid-batch aborts it | EMBER | F3 | 3 | 5 | 10 | 6 |
| ENG | **done 2026-09-30 (#673, merged on the maintainer's order; A/B as a post-merge check; engineers are built again since #680 — no loaded AI file had listed TD/RA1/TS engineers since ≥ 2025-06):** `EngineerBotModule` (Cameo) — LC1 claim on every order, its own in-flight set (a same-owner re-claim cannot stop a module double-ordering itself), stuck engineers stopped and retried after `StuckRetryTicks`, capture ids read from the CA module (one copy in `ai.yaml`); omniscient as a whole (maintainer 2026-09-30, DESIGN §19.5). Merge `CaptureManagerBotModuleCA` + `CncEngineerBotModule` into one engineer owner (DESIGN §19.3) on LC1: capture routing (omniscient, §19.5), priority targets, hut/bridge repair, instant repair | Claude | LC1 | 4 | 8 | 14 | 8 |
| LC8 | failure write-back (the review's sixth boundary): every executor that fails an objective another layer chose reports the outcome to that layer — MCV site (LC3's engine half), capture target, refinery claim (EX-2's missed claim already parks), squad attack target; CA-2c's siege failure memory is the working pattern | Claude | LC1 | 3 | 6 | 12 | 7 |
| BEV | merge BevManager into the MCV owner: base-building vehicles (Japan's nanocores) deploy next to the base, MCVs and field-refineries (slave miner) go to fields; verify in a Japan match first | Claude | LC3 | 4 | 8 | 16 | 9 |
| LC9 | fog: `ResourceMapBotModule` (engine) counts enemy units and bases per resource field through fog (`FindActorsInCircle`, no visibility check), and the engine `McvExpansionManagerBotModule` scores expansion threat from those counts (NOVA's verification, 2026-09-30). The planner is already honest (`RememberedEnemyThreatAt`); fix the manager's input the same way — a Cameo shadow of `ResourceMapBotModule` that counts only seen or remembered enemies | Claude | BEV | 2 | 4 | 8 | 4 |

**Mission cards: one id from the strategist to the actors and back ([`AI_MISSION_CARDS.md`](AI_MISSION_CARDS.md), fransotto's
proposal 2026-09-30)**, expected 14 h. LC8 is the return path; MC gives it ids, states, a readable log and a format
Cameo and Fransbot can share. Learning across matches stays **OM**, under AI_ARCHITECTURE §6.1 (read at match
start, frozen, host-local): no new ruling needed.

| id | work | owner | needs | O | M | P | E |
|---|---|---|---|--:|--:|--:|--:|
| MC1 | **writer + first consumer built 2026-09-30 (`claude/mc1_mission_log`):** one vocabulary ruled for all three stacks (AI_MISSION_CARDS §2), `BotMissionLog` (CA) + `AiMissionLogWriter` (`cameo-ai-missions.jsonl`), capture cards from `EngineerBotModule`; squad raids = NOVA #681, Fransbot broker = DAWN #679, both switching to the writer. `MissionId` / `AttemptId`, the closed state set (Proposed … Dormant), `IBotMissionOutcomeSink` (executors report exactly one terminal state per attempt; the owner decides), lease `MissionId`, the General's plain-text log lines; first consumers MCV site, capture, refinery claim, squad raid | Claude | LC1, LC8 | 3 | 6 | 12 | 7 |
| MC2 | `tools/ai/mission_story.py` (per-mission story, success rate per type, missions without a terminal state) + situation-log schema 3; replay correlation by `game_uid` + tick | Claude | MC1 | 2 | 4 | 8 | 4 |
| MC3 | `mission_card.schema.json` (versioned, shared vocabulary, `x_` private reasons), per-match JSONL archive, the offer to fransotto | Claude | MC1 | 2 | 3 | 6 | 3 |

**Learning and feel (AI_ARCHITECTURE §6.4, AI_SYNTHESIS §5)**, expected 127 h

| id | work | owner | needs | O | M | P | E |
|---|---|---|---|--:|--:|--:|--:|
| L0 | learning L0: per-bot Info copy (host-only) + two-client desync test | Claude | F4 P0 | 12 | 20 | 36 | 21 |
| L1 | L1 measured priors (CA-1b), predictor strengths, enemy models | Claude | L0, CA-1b | 8 | 14 | 24 | 15 |
| L2 | L2 score + knob layer (identical dump with knobs at 1) | Claude | L1 | 8 | 14 | 24 | 15 |
| L3 | L3 knob training loop (per faction, family fallback) | Claude | L2, F3 | 10 | 18 | 32 | 19 |
| L4 | L4 personality/opening bandit | Claude | L3 | 6 | 10 | 18 | 11 |
| L5 | L5 raw numbers leave their knob; §6.4a weight combination (enemies × allies) | Claude | L4 | 14 | 26 | 48 | 28 |
| HL | human-like: staggered orders, reaction delays, controlled mistakes — scaled by difficulty | NOVA | F1 | 10 | 18 | 32 | 19 |

**Acceptance (AI_ARCHITECTURE §0a)**, expected 15 h

| id | work | owner | needs | O | M | P | E |
|---|---|---|---|--:|--:|--:|--:|
| ACC | acceptance: 20-map runner + the §0a test (fog-blind wins ≥16/20 vs omniscient classic) | EMBER | all above | 8 | 14 | 24 | 15 |

---

## 4. Effort, schedule and the critical path

### 4.1 The numbers

| | expected | range (all go well … all go badly) |
|---|--:|---|
| agent work, 55 items | **~956 h ≈ 191 sessions** | 520 h … 1,604 h |
| per agent, four in parallel (Claude, NOVA, EMBER, DAWN) | ~239 h ≈ 48 sessions | 130 h … 401 h |
| A/B gates | **42** (LC9 and MC1 change behaviour; MC2/MC3 are tools and a format) | — |
| A/B compute: 16 matches per gate, 20–40 min per match at maximum on this machine, 3 batches in parallel | **60–120 h of wall-clock** | more when other agents' batches share the machine |

Read the range, not the midpoint: the items are correlated (a slow UT delays DI, TC and §13), so the
real spread is closer to the O…P columns than the statistical ±. These are estimates, not commitments.

### 4.2 What actually sets the calendar

1. **The critical path**, from the dependency column: **CA-1 → CA-3 → CA-4 → UT → (DI, TC, §13)**, and
   **ZG → IM → UT** alongside it. UT alone is 50–90 h. Everything else can run in parallel lanes. **LC1 → LC5** gate
   the harvest items (the Fransbot author's order of work: ownership contracts before more brains).
2. **Machine time.** Every behaviour change needs its A/B, and this one machine ran ~11 matches at
   once on 2026-09-29, which made a 16-match gate take hours. F3 (a nightly queue with the league as the
   default gate) is therefore in the first wave.
3. **The balance freeze.** Learning (L1, L3–L5) can be built now, but serious training waits for the
   frozen balance (DESIGN §19.2). A rebalance invalidates what was learned (the fingerprints, §6.4).
4. **Fleet availability.** The Devin agents are booked until ~2026-10-22: 22 days. At 1–2 sessions
   per agent per day, four agents deliver 440–880 h. That covers waves 1–3 (~411 h with the hardening wave) with a
   little margin; all 939 h fit only at the fast end, and only if the A/B machine keeps up. Plan the rest past that date.

### 4.3 The waves (the order the fleet works in)

| Wave | Goal | Items | Expected |
|---|---|---|--:|
| **1: fair and fast to measure** | every tier on the line, A/B throughput, CA synced, known bugs fixed | F1, F2, F3, RV1, RV2, DF A/B, CA-1 | ~74 h |
| **1b: ownership before brains** (the Fransbot author's review) | one owner per actor and per decision, stale state and failure feedback fixed, fog canaries, fingerprinted A/B | LC1–LC9, ENG, BEV, MC1–MC3 | ~99 h |
| **2: win the fights** (the measured loss mode: fights traded 2:1) | siege, role mix, formation, air, scouting | CA-2, CA-3, CA-4, CA-5, CA-6, CP | ~114 h |
| **3: one brain on a real map** | CN chokepoints, influence, the utility strategist, micro | ZG, IM, UT, MI | ~142 h |
| **4: economy, expansion, map-wide play** | the rest of EX and the leads, Fransbot island/transports/SpecOps/sea/support, CN waves and utilities | EX, PL, FB1–FB4, CN1–CN3, §2.9 (F4) | ~257 h |
| **5: learn, pace, beat humans** | learning L0–L5, OM, Director, Team Commander, human-like feel, §13, the analyst | L0–L5, OM, DI, TC, HL, H13, LA, CA-1b | ~256 h |
| **6: acceptance** | the §0a test: fog-blind bot wins ≥ 16 of 20 on 20 Tournament maps vs omniscient `classic` | ACC | ~15 h + the run |

Waves overlap: a lane moves to the next wave as soon as its own items land.

---

## 5. The difficulty ruling applied (maintainer 2026-09-30, DESIGN §19.1)

*"I want all difficulties to scale in equal steps."*

* **No module is switched on per tier any more.** Today #656 arms eight Fransbot service modules on
  `genericbot && hardbot` only. Under this ruling every `genericbot` tier (easiest … god) loads every
  harvested module, and **its strength knobs** sit on the §19.1 line: Min at easiest, Max at
  cameogod, interpolated by tier index (the `DynamicBotInsurance` pattern).
* **Order (F1):** the #656 A/B first (does it help `hard`?). If yes, move the eight modules to all tiers
  with per-module strength knobs, and extend `audit_ai_personalities`'s `difficulty_scale_failures` to
  flag any tier-gated module condition (`hardbot`, `brutalbot`, …) in `ai.yaml` and `fransbot.yaml`. If
  no, the modules leave `hard` too, and are harvested again later as consumers (step 1 of §1.2).
* **What "strength" means for a module:** its reaction interval, its horizon or look-ahead, its
  share of the action budget, its self-preservation margin (Zero-K: difficulty = delays and
  self-preservation, never cheats; AI_DEEP_RESEARCH §0 #8). **Never** cheats, extra income or vision.
* `classic` stays outside the ladder: it is the A/B reference.

---

## 6. Risks and how the plan handles them

| Risk | Handling |
|---|---|
| Two modules claim one ACTOR (engineers: capture vs CncEngineer both read `IsIdle`) | LC1 lease, LC5 watchdog, ENG merge |
| A batch runs on files that changed under it (yaml re-read per match) | LC7 fingerprint aborts it |
| Two owners for one decision (as with the double repair module, fixed in RV1) | DESIGN §19.3 (one module per decision, merge duplicates); §1.2 step 1; the module map (`ai_module_map.py`) shows providers and consumers; RV2 fixes the support-power pair |
| A harvested module cheats (enumerates the world) | `audit_fog_honesty` manifest; every new site reviewed |
| A CA sync drops a merged feature | `audit_ai_frankenstein` (140 + protected symbols) |
| An engine change reverts the bleed sync | LESSONS_LEARNED "The pinned engine commit is NOT on `cameo-engine`"; the branch now equals the pin |
| A/B noise decides wrongly (8 v 8 is small) | the league as the default gate (F3); repeat the gate when it is close; `army_mix_report` as a second signal |
| Merges without A/B (tonight's merge-all) | the first A/B on master `bf2b30883` is the new baseline; every later gate compares with it |
| Learning trains on a moving balance | fingerprints + discount (§6.4); serious training after the freeze |

---

## 7. How to use this plan

* **Claim before starting:** a `CLAIM_…` note in the fleet folder naming the item id (e.g. `CA-3`),
  then a PR whose title starts with that id.
* **Update the status in the same PR:** the §2 row and the §3 row (the `E` column stays as it is; add
  the actual hours in the PR text for the next estimate).
* **Designs stay where they are:** AI_ARCHITECTURE (§12 and the phase designs), AI_DEEP_RESEARCH (the
  evidence), AI_SYNTHESIS (§7.2 the layer table and best-of picks). This file points to them and does
  not repeat them.
* **Re-measure this plan** (§2) whenever a wave closes: `git grep` for the named classes,
  `ai_module_map.py`, and the ROADMAP boxes (several were stale on 2026-09-30 and are corrected there).
