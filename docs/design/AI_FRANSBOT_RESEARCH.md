# Fransbot research: what Cameo can take, and the phase-6+ handoff

_Written 2026-09-26 by Claude-Local (coordinator) for **Devin-Cloud (AI lane)** and the maintainer.
Sources: the maintainer's conversation with fransotto, author of FransBots, on 2026-09-24; the
maintainer's conversation with **Astor, author of Crystallized Nexus (CN), on 2026-09-11**; CN's
public source (`github.com/DoGyAUT/crystallized-nexus`, `main` = `30cf70a`, GPLv3, cloned at
`~/Documents/GitHub/crystallized-nexus`); and Cameo's own code on master `91f865585`. This document **amends** [`AI_ARCHITECTURE.md`](AI_ARCHITECTURE.md)
§10.6 phase 6 and adds phases 6c–10. It does not replace that document. Where the two disagree on
something already built, `AI_ARCHITECTURE.md` and the code win._

---

## 0. TL;DR (read this if you read nothing else)

1. **Source access is available.** The private `f850484/OpenRA-Fransbot` repository is
   accessible to the authorized collaborators; `V1.29.19-RC` was inspected at `094a4d4`.
   Source access is no longer the phase-F0 blocker. The side-by-side port is tracked in
   PR #578, which remains draft pending its role-based configuration work. See
   [`AI_SYNTHESIS.md`](AI_SYNTHESIS.md) §4 for the measured port contract.
2. **Phases 6a–6e have landed.** Cameo has `BotFogMemory`, `RegionMemory`,
   `ScoutBotModule`, the pre-commit risk gate, fogged squad scans, and risk routing.
   The work-plan bullets below describe their design, not an instruction to build
   duplicate implementations. Artillery attachment also exists; staging and
   support-follow remain under review in PR #577.
3. **Cameo retains cost-based threat estimates with spatial memory.**
   `MasterAiBotModule` publishes the shared situation, using observed actors and
   remembered contacts when `UseFoggedObservation` is enabled.
4. **Fogged targeting reaches squad consumers too.** The CA squad manager consults
   `IBotFoggedEnemyProvider`, filters visible candidates, and can use remembered
   frozen buildings. The legacy path remains available when fogged observation is
   disabled. The September-26 facts in §1.3 are historical evidence, not current
   shipping status.
5. **Reuse mechanisms, not RA-specific actor lists.** Cameo's role-based
   configuration is specified in `AI_ARCHITECTURE.md` §2.8. The Fransbot port must
   preserve one execution owner per unit and must not materialize a second central
   inventory of every faction's actors.
6. **Much of what Fransbot does already exists in public, GPLv3 code: CN's bot, and it is already
   cloned here.** The Astor conversation (§1.4) pointed at it, and the source confirms it (§3b):
   * `CNTacticalMapBotModule` splits the map into terrain **regions** bounded by chokepoints, with
     doors, adjacency and high ground. Those are better buckets for the value memory than a grid.
   * `CombatAnalysisBotModule` keeps per-role threat weights with decay and a **nemesis** player.
     That is the pairwise-attribution term `AI_ARCHITECTURE.md` §4.3 calls `w_hurt`.
   * CN's squad manager has **coordinated waves**: staging, rally, flank split across two doors,
     and wave size that **grows over time**. It also has **artillery that hangs back behind an
     assault squad and only fires at what that squad can see**, support squads that follow, APC
     and air transports, and **priority targets per squad**.

   CN's profile-switching mechanism stays forbidden (`AI_ARCHITECTURE.md` §1.6);
   adapt its useful mechanisms through Cameo's existing decision owners. Compare
   against both upstream sources and the current consumer before adding a module.

---

## 1. Provenance: what we know, and how sure we are of it

### 1.1 From the conversation (claims by the author, **not yet verified against source**)

| # | Claim (fransotto, 2026-09-24) | Confidence |
|---|---|---|
| C1 | Worked on bots for 3–4 years, **yaml only** at first; now C# written by ChatGPT/Codex from replay + screenshot + a **custom debug log** loop | author's account |
| C2 | Runs **without global vision**, on **any map including the map generator**, with fog of war | author's claim, the key one |
| C3 | Core: the bot keeps, per place, **the cash value of units and buildings it has seen**. It stays in memory until that area is scouted again | author's claim, repeated three times |
| C4 | Decisions are risk/reward on that memory: *"it does not send a squad with value 1000 against an area with value 5000"* | author's claim |
| C5 | Uses **native OpenRA orders**: Secure, Raid, Recon, Retreat. Routing is also a "risk-cash" analysis | author's claim |
| C6 | Reads **unit stats from the rules files**, with no per-unit hand-tuning (his hard rule) | author's claim, the most portable part |
| C7 | Understands **air vs AA**, but **not yet** "rocket soldiers are dangerous to tanks" (no general counter model) | author's own limitation |
| C8 | 10 bots on a Europe map, transports, raids and supplies, **without lag**. Close to or better than stock Normal AI | author's claim |
| C9 | **Beacons**: an allied beacon draws troops, a beacon on your own building draws a supply truck (**in progress**) | author's claim, WIP |
| C10 | Estimates every player's **harvester count**. Simple team chat ("I need cash", "enemy weak here", "spot has AA") is **paused**, next release | author's claim, not shipped |
| C11 | Several personalities with 6–7 `SquadManagerBotModule` instances each, which *"became quite hard to keep track on"* | author's account |
| C12 | **Island expansion and airdrops.** The maintainer asked how island expansion works. fransotto never answered the mechanism in the conversation, but lists "transports" in C8 | **unconfirmed**: must come from the source (§6) |

Public trail: FransBots on ModDB (`moddb.com/mods/fransbots`, e.g. `fransbots20251116`) and the
OpenRA forum (topics 21565 "FransBots 20231220" and 21988 "FransBots 20260122!"). Search-engine
summaries of those pages describe **10 AIs, yaml-only, no cheats, only build orders, squad
compositions and target priorities changed**, with specialist units (engineers, thieves, medics,
Tanya, nukes). That is the **old** line. The C# `V1.29.x` line described above is the new, private one.

### 1.2 Licence and consent

Fransbot is a fork of OpenRA, which is GPLv3, so its C# is GPLv3 and compatible with this repo.
fransotto also said he wants to *"give back to the OpenRA community"* and *"cannot claim any
ownership"*. **Still: credit him by name** in any ported file header and PR body
(`Ported from FransBots by fransotto, <commit/tag>`), and do not import anything until the
maintainer has the source with his consent. A private repo is not consent to copy.

### 1.3 Cameo facts (verified on master `91f865585`, 2026-09-26)

| Fact | Evidence |
|---|---|
| Bot omniscience is **code-level, not a rule**: no map reveal or bot shroud override in `player.yaml` or `ai.yaml` | grep of `RevealsMap`/`ExploredMap`/`Shroud` in `mods/cameo/rules/player.yaml`, `mods/cameo/ai/ai.yaml` |
| Master snapshot scans all actors | `OpenRA.Mods.Cameo/Traits/BotModules/BotSituation.cs:219` `player.World.Actors.Where(...)` |
| Value = production cost | `BotSituation.cs:847` `ValuedInfo.Cost` |
| Per-enemy profile already has Army / Inf / Veh / Air / Naval / Defence / Pressure values | `BotSituation.cs:24-38`, built at `:388-430` |
| Squad target search is omniscient | `SquadManagerBotModuleCA.cs:354-372` (`World.Actors.Where(IsPreferredEnemyUnit)`) |
| Only cloak and submersion are respected (`IVisibilityModifier`), never shroud | `AI_ARCHITECTURE.md` §0, `SquadManagerBotModuleCA.cs` `IsNotHiddenUnit` |
| Squads already have **local** fight-or-flee, but only once enemies are near | `Squads/AttackOrFleeFuzzyCA.cs:166` `CanAttack`, used at `States/GroundStatesCA.cs:23,90`; air flees on AA count `States/AirStatesCA.cs:210-212` |
| **No pre-commit risk test** (before a squad is sent) and **no risk-aware routing** | absent from `SquadManagerBotModuleCA.cs` / `Squads/**` |
| Island patches are **silently dropped**: expansion skips unreachable resources | `engine/OpenRA.Mods.Common/Traits/BotModules/McvExpansionManagerBotModule.cs:470-472` (`path == PathFinder.NoPath`), also `:830-833`, `:958` |
| MCVs are carryable cargo: ~37 MCV-like actors, cargo type `Vehicle`, most `Carryable` | resolver scan (`miniyaml.Ruleset.resolve`), 2026-09-26 |
| `Passenger.Weight` defaults to **0** in this engine | `engine/OpenRA.Mods.Common/Traits/Passenger.cs:31` |
| Vehicle-carrying transports exist in many factions. Naval: `ra1_navaltransport`, `td_gdi_landingcraft`, `td_nod_transportsubmarine`, `ra2lcrf`, `ra2sapc`, `cabal_lcraft`, `forgotten_lcraft`, `asianalliance_panth`. Air: `ra2_soviets_transportkirov`, `naxis_transportzeppelin`, `schwarzermond_spacezeppelin`, `protoss_shuttle`, `terran_dropship`, `steelconsortium_cargoship`. Plus 13 `Carryall` actors (D2k houses, TS GDI, Forgotten, Syndicate Hind) | same scan. **Faction coverage is uneven: list the factions with NO MCV ferry before promising island expansion for all** |
| Airdrop / unload mechanic already exists (dummy weapon or on-damage unload) through `ExternalBotOrdersManager` + `IssueOrderToBot` | `engine/OpenRA.Mods.AS/Traits/BotModules/ExternalBotOrdersManager.cs:120-149`; 15 `IssueOrderToBot` uses in `mods/cameo/ContentPacks/**` |
| Cargo loading bots exist, but only for infantry / bunkers / battery | `ai.yaml` `LoadCargoBotModule@Infantry/@TankBunker/@Battery` (~line 3725) |
| Beacons are **invisible to bots**: `Beacon` keeps `owner` and position **private**, and `PlaceBeacon.ResolveOrder` only runs on the placing player's actor | `engine/OpenRA.Mods.Common/Effects/Beacon.cs:20-24`, `engine/OpenRA.Mods.Common/Traits/Player/PlaceBeacon.cs:47-71` |
| The engine **already remembers fogged buildings** per player (frozen actors). Units are not remembered | `engine/OpenRA.Game/Traits/Player/FrozenActorLayer.cs:363,371` (`FrozenActorsInRegion/InCircle`), `Actor.CanBeViewedByPlayer` (`engine/OpenRA.Game/Actor.cs:510`), `Shroud.IsVisible/IsExplored` (`Shroud.cs:413-463`) |
| Match and situation logs already exist (phases 1–2) | `OpenRA.Mods.Cameo/Traits/AiMatchLogWriter.cs`, `AiSituationLogWriter.cs`, `docs/design/AI_MATCH_LOG.md` |

### 1.4 From the Astor (CN) conversation, 2026-09-11, checked against CN source

| # | Astor said | CN source says (`.modsdk/OpenRA.Mods.CN/Traits/BotModules/`) |
|---|---|---|
| A1 | Steamroller gets wave sizes that grow the longer the game goes | ✅ `AttackWaveSizeGrowthInterval` / `AttackWaveSizeGrowthAmount`, capped by `AttackWaveMaxMinReadySquads` (`Squads/CNSquadManagerBotModule.cs:440-480`). Cameo's #276 time-scaled squad value threshold is a partial equivalent |
| A2 | Artillery squads coordinate with assault squads: artillery fires first, then the assault goes in after some time | ✅ in shape, ⚠ **not** as a timer. `CNSquadType.ArtilleryAssault` *"follows Assault squads, hangs back, bombards"* (`Squads/CNSquadType.cs`). States Idle → HangBack (`ArtilleryHangBackCells` 8 behind the leader) → Bombard when enemies are in range → Flee (`Squads/States/ArtilleryStates.cs:20-498`). The sequencing comes from staging: the wave holds at `AttackWaveStagingProgressPercent` 65 % of the way and rallies. No fixed "artillery first, assault after X" delay was found |
| A3 | Each squad can be given priority targets | ✅ `PriorityTargetCapabilities` per squad template, first match wins, matching actors tagged `BotCapabilities: <tag>` (`CNSquadManagerBotModule.cs:106-110`; `Traits/BotCapabilities.cs`) |
| A4 | (maintainer asked) air squads to counter enemy artillery | ✅ expressible: `AircraftRaider` (*"priority target strike, then return to rearm"*) and `Raider` (*"targets soft units (harvesters, arty), flees on resistance"*) plus a priority tag on artillery |
| A5 | (maintainer asked) do they use formations? | ❌ unanswered. No bot formation code in CN (it uses steering movement, `Activities/CNSteeredMove.cs`). Cameo has player-side Custom Formations (`OpenRA.Mods.Cameo/Orders/CustomFormations*`) that no bot uses |
| A6 | (not claimed, found) fog-honest artillery | ✅ `ArtilleryStates.cs:209-240` `FindCoordinatedTarget`: the attached frontline squad is the **observer**, and a target must pass `CanBeViewedByPlayer`, with a deterministic `ActorID` tie-break |
| A7 | (not claimed, found) risk gate | ⚠ `WaveAbortThreatPerUnit` (`CNSquadManagerBotModule.cs:368-373`) holds a wave back when defensive fire per unit is too high. It is **off by default**: CN's author had only failed waves to calibrate from, and logs "wave strength" on every launch to fit it later. Same idea as Fransbot C4, and the same calibration lesson applies to Cameo |
| A8 | (not claimed, found) defence memory under fog | ✅ `EnemyDefenseMemoryInterval` (`:306-310`), already analysed in `AI_ARCHITECTURE.md` §1.6 |

Non-AI parts of that conversation (infantry cover, late-game infantry vs artillery, armour layers,
mobs) are not the AI lane's job. They are recorded for the maintainer in **Appendix A**.

---

## 2. Fransbot's core model, restated precisely enough to build

Everything here comes from C2–C5. Treat it as a **spec to implement and then diff against the
source**, not as a description of the source.

**Value memory ("threat map").** Divide the map into coarse regions (suggestion: 8×8-cell buckets;
tune it). For each region, keep per enemy player:

```
RegionMemory { int ArmyValue; int DefenceValue; int AAValue; int EconomyValue;
               int LastSeenTick; bool EverSeen; }
```

* **Write** only from what the bot's player can see: `actor.CanBeViewedByPlayer(player)` for units,
  and `player.FrozenActorLayer` for fogged buildings (the engine already keeps those).
* **Keep** the values when the region goes dark. That is the "sticks in memory until it scans that
  area again" behaviour, and it is what lets the bot be wrong. Do **not** decay the value itself.
  Keep `LastSeenTick`, and let **confidence** = f(age) damp decisions (`AI_ARCHITECTURE.md` §3.1
  already specifies this).
* **Overwrite** a region's values when it is visible again, including to zero. Seen empty is information.
* Units move, so an unseen unit's value would otherwise count twice: once where it was last seen,
  and again wherever it turns up. Per-actor last-seen positions (keyed by `ActorID`) fix that. Move a
  known actor's value when it is re-seen elsewhere, and drop it after a long timeout.

**Risk gate.** Before committing a squad to a target region, compare the squad's value with the
remembered hostile value in and around the target:

```
commit if  squadValue * RiskAppetite(personality)  >=  remembered(target) + remembered(route)
```

`RiskAppetite` is per personality. Rush is high, Turtle low, Steamroller commits only with a large
margin. The emergency path of §4.5 in `AI_ARCHITECTURE.md` (defend the base) **bypasses** the gate:
you do not get to refuse a fight in your own base.

**Order vocabulary** (C5), mapped onto what Cameo squads already do:

| Fransbot | Meaning | Cameo equivalent today |
|---|---|---|
| Recon | refresh an unknown or stale region | **none**: the new `ScoutBotModule` |
| Raid | hit a soft, valuable target (harvesters, expansions) | `SquadManagerBotModuleCA` guerrilla knobs (`JoinGuerrilla`, `MaxGuerrillaSize`), a candidate that is computed but not grantable (§10.6 item 3) |
| Secure | take and hold a region (expansion site, choke) | protection squads (`States/ProtectionStatesCA.cs`), partly |
| Retreat | leave when the risk turns | `AttackOrFleeFuzzyCA` local flee, but only once engaged |

**Risk routing** (C5). Pick a waypoint path that minimises the sum of remembered hostile value
along it, then issue ordinary move / attack-move orders through the waypoints. The pathfinder itself
must **not** be replaced (that is engine code and synced). This is a coarse A* over the region grid,
in unsynced bot code, and the result is only a list of waypoints.

**Stats-driven valuation** (C6, C7). Value alone cannot see that rocket infantry beat tanks, and
fransotto says Fransbot cannot see it either. Cameo can go further than Fransbot here, because the
warhead system already encodes it: every weapon's damage per armour ladder is derivable from
`^Warhead_*` Versus (`DESIGN.md` §12.0h, and the derived damage-% tooltip landed in #445). Phase 9
below turns that into an effective-value multiplier. Do **not** re-derive Versus by hand: the
weapon and armour data come from rules at load time.

---

## 3. Feature-by-feature: Fransbot vs Cameo today vs what to do

| Feature | Fransbot (claimed) | Cameo today | Gap / route | Phase |
|---|---|---|---|---|
| No global vision | yes (C2) | omniscient master + squads (§1.3) | fogged observation for the master **and** the squad scans | **6a** |
| Spatial value memory | yes, the core (C3) | per-enemy totals only, no spatial part, no memory | `RegionMemory` grid in `MasterAiBotModule`, exposed on the snapshot | **6a** |
| Scouting | Recon order (C5) | none (`AI_ARCHITECTURE.md` §3.1: "Cameo has no scouting behaviour at all") | `ScoutBotModule`: target the stalest high-interest regions; unit choice through compositions or prerequisites, no hard-coded ids | **6b** |
| Pre-commit risk test | yes (C4) | none; local fuzzy flee only | risk gate in `SquadManagerBotModuleCA` target choice, reading the snapshot | **6c** |
| Squad target scans honour fog | implied by C2 | `World.Actors` at `SquadManagerBotModuleCA.cs:354-372` | read visible actors plus memory; fall back to today's behaviour when the snapshot is missing (§10.1 degradation rule) | **6d** |
| Risk-aware routing | yes (C5) | direct paths | region-grid A* → waypoints → existing orders | **6e** |
| Island expansion | unconfirmed (C12) | unreachable patches dropped (`McvExpansionManagerBotModule.cs:470`) | new Cameo module: find unreachable resource clusters → pick a ferry the faction owns (naval `Cargo` with `Vehicle`, or `Carryall`) → load, move, unload, deploy. Do **not** edit the engine module; it is `engine/` and not in this repo | **7** |
| Airdrops | yes (C8) | yes: `ExternalBotOrdersManager` + `IssueOrderToBot` unload on dummy weapon or damage | nothing to take; reuse the plumbing for the island ferry | — |
| Beacon response | WIP (C9) | bots cannot see beacons (§1.3) | shadow `PlaceBeacon` in `OpenRA.Mods.Cameo` (assembly order puts Cameo before Common, CLAUDE.md rule 7). Record `(owner, pos, tick)` into a world-level `BeaconTracker`, and have a bot module react to **allied** beacons only | **8** |
| Counter awareness (AT vs armour) | air/AA only (C7) | phase 5 counter demand drives builds from class **totals** | effective value = cost × damage-vs-armour factor from resolved Versus; feeds the risk gate and counter demand | **9** |
| Harvester estimate / economy proxy | yes (C10) | `EnemyProfile` has no economy field; omniscient own counts only | visible-harvester count per enemy in `RegionMemory`, fogged | 6a (field only) |
| Team chat | paused (C10) | none for skirmish bots (the survival map has Lua general chat) | low priority; unsynced chat lines are possible, but they are UX, not strength | later |
| LLM replay-tuning log | custom debug log (C1) | JSONL match and situation logs (phases 1–2) | compare formats in F0; adopt any field Fransbot logs that we do not | F0 |
| Many squad modules per personality | 6–7 (C11) | 5 personality-gated `SquadManagerBotModuleCA` | **don't copy**: it is his own stated pain point, and Cameo's master and snapshot design exists to avoid it | — |
| Performance at 10 bots | yes (C8) | scan cadence in `AI_ARCHITECTURE.md` §10.5 | the memory update must be O(visible actors) per rebuild, never O(map cells) per tick | all |

---

## 3b. CN modules worth porting (public, GPLv3, shares the 2026-05-11 engine base with cameo-engine)

| CN module (lines) | What it gives | Cameo use | Port cost |
|---|---|---|---|
| `CNTacticalMapBotModule.cs` (3055) | terrain regions bounded by chokepoints, doors, adjacency, high-ground edges; **computed once per world and shared** (`ConditionalWeakTable<World, …>` at `:367`, an unsynced cache) | the region set for `RegionMemory` (6a), the graph for risk routing (6e), scout targets (6b) | port the **topology** part only; leave out CN-specific rendering and base-role logic |
| `CNRegionManagerBotModule.cs` (639) | what each held region is for (main, economy, military, outpost), security score per door | later: expansion and defence placement hints | later, not this month |
| `CombatAnalysisBotModule.cs` (369) | threat weight per attacker role (air / inf / vehicle), value-scaled, decaying; **nemesis** player | `w_hurt` in main-target scoring (§4.3). Fog-honest by construction, because it is fed by being attacked | small; `IBotRespondToAttack` + `IBotTick`. **PORTED** 2026-09-28: `OpenRA.Mods.Cameo/Traits/BotModules/CombatAnalysisBotModule.cs` + `IBotThreatAnalysis` (CA), producer-only; consumer wiring is a later lane |
| `Squads/States/ArtilleryStates.cs` (514) | hang-back, observer-gated bombard | 6f | medium: needs a squad "attach to" notion in `SquadCA` |
| `Squads/States/CNWaveStates.cs` (348) + wave fields | staged, rallied, optionally pincer waves; growth over time | 6f; Steamroller wave growth (A1) | medium to large |
| `Squads/States/TransportStates.cs` (2268) | APC load → move on pinned waypoints → unload → return; `AirTransport` avoids AA | the ferry in phase 7 (island expansion) | large; read it before designing phase 7 |
| `Traits/BotCapabilities.cs` | yaml capability tags on actors | priority targets (A3) | ⚠ Cameo has **3474** actors. Derive tags from traits and templates (Harvester, Production, artillery weapon ranges) instead of hand-tagging, or put them on the shared `^` templates |

Every module above issues orders and keeps local state. None grants conditions from bot code
(checked by grep for `GrantCondition` / `RevokeCondition` in those files). **CN's profile module is
the exception, and it stays forbidden** (`AI_ARCHITECTURE.md` §1.6). Credit CN (Astor / DoGyAUT,
commit `30cf70a`) in each ported file header.

### 3c. The whole CN bot, module by module, against Cameo

Astor sent the complete module list on 2026-09-11. Every row below was checked in
`.modsdk/OpenRA.Mods.CN/Traits/BotModules/` (the line count is the file size) and against Cameo's
loaded modules (`mods/cameo/ai/ai.yaml`, `AI_ARCHITECTURE.md` §10.2).

| CN module (lines) | What it does (verified) | Cameo counterpart | Verdict |
|---|---|---|---|
| `CNBotProfileBotModule` (924) | profiles Rush / Turtle / Tech / Expansion / Steamroller / Adaptive; **tech stage Early / Mid / Late** (`enum TechStage`, `:20`) shifts rush thresholds; budget split (expansion, tech, defence, production) + harvester target % | `BotPersonalityController` + `MasterAiBotModule` (phase 3); `BotLimits` caps | **Numbers and safeguards only**; its switch mechanism is forbidden (§1.6). Worth taking: an **own tech stage** in the snapshot (Cameo counts only the *enemy's* `TechBuildings`, `BotSituation.cs:33`) |
| `CombatAnalysisBotModule` (369) | threat weight per role, value-scaled and decaying; nemesis player; feeds the base builder and squads | `IBotThreatAnalysis` + `CombatAnalysisBotModule` (producer landed 2026-09-28; no consumer yet) | **DONE** — consumer wiring (`w_hurt`) remains open |
| `CNTacticalMapBotModule` (3055) | chokepoints and high-ground edges from the **hierarchical pathfinder's abstract graph** (cut edges and articulation points), rebuilt on bridge changes | none | **Port the topology.** The API it needs exists in Cameo's engine: `PathFinder.GetOverlayDataForLocomotor` (`engine/OpenRA.Mods.Common/Traits/World/PathFinder.cs:59`), called at CN `:699`. **No engine change** |
| `CNRegionManagerBotModule` (639) | held regions, ground value, role Core / Economy / Military / Outpost; `cntopo` chat debug overlay | none | later; the debug overlay is worth copying with the topology, for replay review |
| `CNResourceMapBotModule` (390) | resource + refinery map shared by economy modules | `ResourceMapBotModule` (Common) | skip unless the harvester port needs it |
| `CNBaseBuilderBotModule` + `QueueManager` (4347 + 4482) | self-clustering placement (`NearBuilding`, `ClusterGroupSize`/spacing); **threat-driven defence roles** (`enum DefenseRole`, capped % per role, `:206`) | `BaseBuilderBotModuleCA@generic` | **Idea only**: defence roles driven by `CombatAnalysis` threat. ⚠ Blackrobe's #245 edits the Cameo base builder; coordinate first |
| `CNHarvesterBotModule` (1063) | refinery-aware field distribution; rebuilds harvesters per refinery count | `HarvesterBotModuleCA` | later; economy, not this month |
| `CNMcvExpansionManagerBotModule` (1998) | CN's expansion manager | `McvExpansionManagerBotModule` (Common) | **read before phase 7**: check whether it already handles unreachable patches |
| `CNRepairManagerBotModule` (218) | sends damaged idle units to allied repair facilities | `BuildingRepairBotModule` (+CA) repair **buildings** only | small port candidate |
| `CNBridgeRepairBotModule` (209) | engineers into bridge huts | SHIPPED 2026-09-27: AS `CncEngineerManagerBotModule` now loaded for bridge repair only (`RepairableHutActorTypes: bridgehut, bridgehut.small`); capture stays with `CaptureManagerBotModuleCA` (both claim idle engineers only, first order wins) | shipped |
| `CNUnitBuilderBotModule` (1393) | **squad-demand driven**: reinforces damaged squads first, then fills missing templates, then ratios (`:26-27`, `:857`) | `UnitBuilderBotModuleCA` + compositions + phase 5 counter demand | idea for 6f: reinforce existing squads before starting new ones |
| `CNSquadManagerBotModule` (4923) | template and slot squads (`AllowedTypes`, `Count`, `Optional`, `MinSlotsToActivate`), own state machine, fuzzy attack-or-flee, 15 squad types | `SquadManagerBotModuleCA` ×5 personalities | **pieces**, not the whole (§3b); phases 6c–6g |
| `CNGarrisonBotModule` (353) | fills garrisonable buildings with the infantry type the **local threat** calls for; swaps mismatches out | `LoadGarrisonerBotModuleCA@Infantry` (no threat matching) | later: threat matching once `CombatAnalysis` is ported. Cameo has 11 yaml files with garrisons |
| `CNCliffDemolitionBotModule` (326) | shoots destroyable cliffs open, only to join own ground or open a way into ground it is attacking | **no destroyable cliffs in Cameo** (0 yaml hits) | **skip** |
| `CNVeinholeAssaultBotModule` (232) | force-fires veinholes, gated by side (GDI burns them, Nod keeps them for weed) | none; Cameo has veinhole content (8 yaml files) from the TS factions | small candidate for TS GDI and Nod |
| `DeployBotModule` (517) | deploy behaviour per actor group (artillery and similar) | nothing loaded | candidate: many Cameo siege units deploy, and a bot that never deploys them wastes them |
| `CNBotPerf` (159), `CNBotLog` (38) | per-module timing and logging | `AiMatchLogWriter`, `AiSituationLogWriter` (no timing) | **cheap and useful**: 25 factions and several bots per match; measure before 6a–6e add scans (Fransbot C8 claims 10 bots without lag) |

**Configuration layout.** CN defines six `ModularBot`s (`cn`, `cn-rush`, `cn-turtle`, `cn-tech`,
`cn-expansion`, `cn-steamroller`) and splits its AI yaml by concern into 11 files, 3829 lines in
total (`.modsdk/mods/cn/rules/ai/`: `bots`, `profiles`, `base-building`, `economy`, `production`,
`support`, and one `squads-<profile>.yaml` per profile). Cameo's is one `mods/cameo/ai/ai.yaml`
of more than 6000 lines. Splitting it by concern is a maintainability win, but a new file means a
`mod.yaml` manifest entry, and **`mod.yaml` belongs to DAWN**. Ask before doing it. Cameo's
personalities are one bot with switching (phase 3), not six separate bots; keep it that way.

---

## 4. The work plan for Devin-Cloud (amends `AI_ARCHITECTURE.md` §10.6)

One PR per sub-phase. Each is shippable alone, and each honours the **degradation rule**
(§10.1: a missing snapshot means today's behaviour). The window closes **~2026-10-22**, so the
order below is also the priority order: stop wherever time runs out, and leave §7's handoff.

**Shipping-state checkpoint (2026-09-28):** 6a–6e and 6f artillery attachment
are implemented. The following bullets retain the original design requirements;
they are not an unstarted-work queue. Staging/support-follow, the Fransbot port,
and beacon response remain separately reviewed work. Consult the current PR
head and `HANDOFF.md` before claiming any of those files.

### 6a. Fogged snapshot + region value memory (C#: `OpenRA.Mods.Cameo/Traits/BotModules/`)

_**Status: implemented 2026-09-27** (`BotFogMemory` + `RegionMemory`, `UseFoggedObservation`
default true, `EnemyProfile.HarvesterCount`/`KnownRegions`, situation log fields
`harvester_count`/`known_regions`). Memory does not yet survive save/load — candidate follow-up._

* Replace the omniscient scan at `BotSituation.cs:219` with visible actors
  (`CanBeViewedByPlayer`), plus frozen actors for buildings, plus the per-actor last-seen table.
* Add the `RegionMemory` (§2) and publish it on `BotSituation` as a read-only view. **Prefer CN's
  terrain regions** (`CNTacticalMapBotModule` topology, §3b) as the buckets; fall back to the
  8×8-cell grid only if the port does not fit in the window.
  `EnemyProfile` values become sums over remembered regions, so the phase 3–5 consumers keep working
  unchanged.
* Add `UseFoggedObservation` (bool, **default true**, per the maintainer ruling of 2026-09-23 on
  PR #455). `false` must reproduce today's numbers exactly. That is the A/B lever for tuning.
* Add `EnemyProfile.HarvesterCount` (visible only).
* **Gate**: `python tools/tests/ai_bot_player_gate.py` in both modes; log how many regions are known
  at 5 / 10 / 20 minutes. A fogged bot that knows zero regions at 10 minutes means scouting is
  broken, not that fog works.

### 6b. `ScoutBotModule`

* Pick targets by **staleness × interest**: expansion sites (resource clusters from
  `ResourceMapBotModule`), the last-known enemy base, and choke regions on the route to the main target.
* Choose the unit through the existing path: a composition or prerequisite token such as
  `demand.scout`, following phase 5's `BotCounterDemandController` pattern. **No actor ids in C#**,
  because there are 25 factions.
* Hold at most N scouts, cheap and fast. Losing a scout is information: write the killer's value
  into the region.

### 6c. Risk gate in the squad manager

* In `SquadManagerBotModuleCA` attack-target selection, refuse (or re-target to a softer region)
  when `squadValue × RiskAppetite < remembered(target)`. `RiskAppetite` is a field per personality
  instance, in yaml.
* Home defence and the §4.5 emergency override bypass the gate.
* Precedent: CN's `WaveAbortThreatPerUnit` (§1.4 A7). Ship the gate **with its threshold logged on
  every launch** and a permissive default, then fit it from match logs. CN had to leave its version
  off because nobody had logged successful waves.
* ⚠ This file lives in `OpenRA.Mods.CA/`, **outside the lane as written on #435** (see §7). Phase 4
  already had to touch CA (`IBotMainTargetProvider.cs`); the lane is corrected below.

### 6d. Fogged squad scans

* `FindClosestEnemy` and the high-value scan (`SquadManagerBotModuleCA.cs:354-372`) read the
  snapshot's visible-plus-remembered set instead of `World.Actors`. A remembered target is a
  **position**, not an actor, so squads attack-move to it and re-acquire on arrival.
* This is the change that actually removes the maintainer's "bot artillery always fires at max
  range" complaint. 6a alone does not.

### 6e. Risk routing

* Coarse A* over `RegionMemory` from the squad's centroid to the target, costed by remembered hostile
  value. Emit 1–4 waypoints and reuse the existing move / attack-move orders. Unsynced only.

### Quick wins (any time, small PRs)

* ~~Load AS `CncEngineerManagerBotModule` for bridge repair~~ SHIPPED: bridge-repair only
  (`RepairableHutActorTypes` set, capture/base-repair lists empty → no fight with
  `CaptureManagerBotModuleCA`, which claims idle engineers first-come-first-served anyway).
* ~~Port `CNBotPerf`-style per-module timing~~ SHIPPED: `OpenRA.Mods.Cameo.Traits.ModularBot`
  shadows Common's `ModularBot` and reports per-module tick cost to `debug.log` every
  `ModulePerfReportIntervalTicks` (default 1500; `ModularBot@HardAI` uses 300).

### 6f. Coordinated waves: artillery, support, growth (Astor's points)

* Artillery squads **attach** to an assault squad, hang back N cells, and bombard only targets the
  assault squad can see (CN A2/A6) — **shipped** in #554 (hang-back anchor, `FindAttachableAssault`).
* Waves stage partway to the target and rally before committing (CN
  `AttackWaveStagingProgressPercent`) — **shipped**: `GroundUnitsStageStateCA` rallies Rush squads
  at the own building nearest the target, commits when `StageAssemblePercent` arrive or
  `StageTimeoutTicks` lapses, and fights early on contact. `StageBeforeAssault` gates it in yaml.
  Steamroller's wave threshold already grows via #276's `SquadValueRamp*` fields (checked — no
  second mechanism added).
* Support squads (medics, repair) follow an attack squad (CN `Support`, `SupportFollowRangeCells`) —
  **shipped**: `SquadCAType.Support`, `SupportUnitsIdleStateCA` trails `Parent` within
  `SupportFollowRangeCells`, holding near base with no assault. Unit list is yaml
  (`SupportUnitTypes`, same pattern as the other type lists — no actor ids in C#).

### 6g. Priority targets per squad, and air vs artillery — **implemented**

* `OpenRA.Mods.CA/Traits/BotModules/BotTargetTags.cs` derives the tags from rules at load
  time (§3b note), no actor ids: `artillery` = any `Armament` whose weapon out-ranges the
  assault threshold (currently the longest-ranged ground armaments), `harvester` = any
  `Harvester` trait, `production` = `Production`/`ProductionQueue` owners, `superweapon` =
  actor names appearing in support-power `Prerequisites`.
* `SquadCA.PriorityTags` carries the per-squad-instance list (CN A3). The fields are
  `AssaultPriorityTags`, `RushPriorityTags`, `ArtilleryPriorityTags`, `NavalPriorityTags`,
  `AirPriorityTags`, `GuerrillaPriorityTags`, and `ProtectionPriorityTags`.
  `PriorityTagsFor` selects the set; `RegisterNewSquad` assigns it. Unset keeps the
  current order.
* `PreferSquadTargets` puts matching-tag actors first at its wired call sites,
  preserving within-group order. It does not govern the separate
  `FindHighValueTarget` lottery; do not claim priority tags apply to every scan.
* `AirPriorityTags: artillery, harvester` on all five personalities answers the maintainer's
  question A4 (air raiders hunt enemy artillery). Verified: `BotTargetTagsTest` (5 tests),
  `tools/tests/ai_squad_gate.py` PASS, boot-gate PASS.
* Deferred: the harasser type is proposed in PR #582. Its priority set belongs in
  `PriorityTagsFor`; there is no `GroundPriorityTags` field or `AssignPriorityTags`
  method to wire.

### 7. Island expansion (new Cameo module)

* Candidates: resource clusters for which `McvExpansionManagerBotModule` would get
  `PathFinder.NoPath` for the MCV locomotor, but which a ferry can reach.
* Ferry choice from rules at load time: any buildable actor with a `Cargo` whose `Types` include the
  MCV's `Passenger.CargoType` (and weight fits), or a `Carryall` where the MCV is `Carryable`.
  **First, list per faction which ferry exists**, since some factions will have none (§1.3), and
  skip those factions cleanly.
* Sequence: request the ferry (a production request through `IBotRequestUnitProduction`, like the
  engine modules), then load, move to the shore cell nearest the patch, unload, and let the existing
  MCV manager deploy.
* Map test: `mods/cameo/maps/ai_*` is lane-owned. Add a small island map if none exists.
* **Read CN's `TransportStates.cs` first** (§3b): it already solves loading, the pinned-waypoint
  approach, unloading and returning, and its air variant avoids AA. Fransbot's version (C12) is
  unknown until F0.

### 7b. Harasser port (fleet-consensus shape)

* Upstream CA `Harass` squads = *where/when* (quorum launch, high-value targets,
  12-route flank pick); Cameo guerrilla = *how to fight* (hit/run states).
  They are complementary roles, not duplicates (REVIEW_2026-09-28_dawn_bot_modules §2).
* **Ported behind default-off fields:** `HarasserTypes` (empty = off) +
  `HarassMinLaunchSize`/`HarassRouteCount`/`HarassPriorityTags` — the field names
  stay CA-compatible so Claude's vendor sync stays lossless. `FindNewUnits`
  checks `HarasserTypes` before `GuerrillaTypes` (list membership is
  deterministic, not subject to `JoinGuerrilla` chance); keep the lists disjoint.
* Reuses the 6g `PriorityTags` seam and 6c risk gate via
  `FindNewTarget(highValueCheck, riskCheck)`; exempt from `RouteAroundThreat`
  like guerrilla (unpredictability is the point). Launch quorum is upstream's
  ramp: <min never, min→5%, min+1→10%, above→always.

### 8. Beacon response

* Shadow `PlaceBeacon` in `OpenRA.Mods.Cameo` with the **same type name**, and **prove the shadow**
  with a Cameo-only field (CLAUDE.md rule 7: `--docs` proves nothing). It must still create the
  identical beacon, and additionally append `(owner, pos, tick)` to a world trait `BeaconTracker`.
  Writing in synced code and reading in unsynced bot code is safe, but **never** let bot code write
  back.
* Bot module: an allied beacon near **enemy** memory sends the nearest free squad (risk gate
  applies). An allied beacon on the **ally's own building** sends support (a repair or supply unit
  if the faction has one; skip otherwise).
* ✅ Maintainer ruling 2026-09-27: **the `PlaceBeacon` shadow is approved** — the earlier lane
  caveat is resolved. The shadow still must be proven with a Cameo-only field before merging.
* **SHIPPED 2026-09-28 (EMBER):** `OpenRA.Mods.Cameo/Traits/PlaceBeacon.cs` shadows the trait
  verbatim plus `TrackForBots` (the Cameo-only proof field); `BeaconTracker` (WorldActor)
  records `(owner, pos, tick)`; `BeaconResponderBotModule` answers allied beacons — remembered
  or visible hostiles near the ping pull up to `MaxResponseUnits` idle combat units through the
  risk gate, a ping on an allied building pulls a repair unit (`RepairsUnits`/`InstantlyRepairs`/
  `RepairsBridges` trait-detected, skipped if the faction has none). Responders are claimed from
  the squad manager's idle pool and released on death, squad claim, or idle after
  `ReleaseAfterTicks`. `PlaceBeaconShadowTest` guards the shadow field-superset (rule 8b).

### 9. Stats-derived effective value (optional this month)

* Effective value of an enemy unit against *our* squad = cost × (our weakness to its weapons).
  Precompute a per-actor-type table at load from resolved weapons and armour. Read Versus through
  the rules the engine loaded, not by parsing yaml.
* Feeds 6c (gate) and phase 5 (counter demand). This is where Cameo can **beat** Fransbot (C7).

### F0. Source analysis (access available; §6)

---

## 5. What NOT to take, and why

* **Build orders, compositions, `UnitsToBuild` rows.** RA-only actor ids, and Cameo's composition
  system is prerequisite-token based (`AI_ARCHITECTURE.md` §1.4).
* **Six or seven squad managers per personality.** His own pain point (C11), and a `TraitOrDefault`
  crash risk in this tree (`AI_ARCHITECTURE.md` §1.3).
* **Anything that reads `World.Actors` for enemy information.** It defeats the whole point.
* **Map-specific data.** He trained on uploaded maps, but claims generality (C2). If the source
  contains per-map tables, leave them out.
* **CN's profile switching and its one-module-per-profile layout.** The first mutates synced state
  from bot code; the second produced CN's own documented stale-reference bug
  (`AI_ARCHITECTURE.md` §1.6).
* **Engine edits.** `engine/` is not in this repo (CLAUDE.md rule 7). If Fransbot patches Common bot
  modules, port the change as a Cameo-side module or shadow.

---

## 6. Phase F0: when the source arrives

**Access checkpoint (2026-09-28):** the authorized source checkout is available.
The earlier collaborator/expired-download blocker is resolved. Keep the checkout
outside this repository and follow `AI_SYNTHESIS.md` §4 for the active port.

For a new source revision, retain this analysis order:

1. Identify its upstream base and compare the standalone `Fransbot.OpenRA`
   project against the recorded vendor baseline. Do not assume its implementation
   lives in the stock `OpenRA.Mods.Common` bot directory.
2. Find the value memory: grep for `LastSeen`, `Memory`, `Threat`, `Risk`, `Value`, `Recon`,
   `Raid`, `Secure`. Record its region size, decay rule, and how moving units are de-duplicated.
3. Find the island and transport logic (C12): grep `Cargo`, `Passenger`, `Transport`, `Island`,
   `NoPath`, `Unload`. This is the maintainer's original question.
4. Find the debug log format and compare it with `AiSituationLogWriter` (§3, last rows).
5. For each of 6a–8: note where his implementation differs from §2, and whether the difference is
   better. **Update this document**; do not fork a second one.
6. Check determinism: `HashSet` or `Dictionary` iteration driving orders, `Random` vs
   `World.LocalRandom`, anything in `ITick` (synced) rather than `IBotTick`. A yaml-first author's
   AI-written C# is exactly where a rare desync hides.

Questions to ask fransotto, so nobody has to guess: region size; how the memory handles units seen
once and never again; how Recon picks targets; whether island expansion is naval, air, or both; and
what the debug log contains.

---

## 7. Constraints for whoever implements this

* **Lane files (corrected).** PR #435's orders list `mods/cameo/rules/ai.yaml`; the real file is
  **`mods/cameo/ai/ai.yaml`**. 6c/6d need **`OpenRA.Mods.CA/Traits/BotModules/**`**, which phase 4
  already touched. Both are granted to the AI lane by these orders. Still outside the lane: the
  `PlaceBeacon` shadow (phase 8), `engine/**` (never), and weapons and warheads (never).
* **Overlap.** PR #245 (`codex/hard-bot-projects`, Blackrobe, idle since 2026-09-17) edits
  `BaseBuilderBotModuleCA.cs`, `BaseBuilderQueueManagerCA.cs`, `UnitBuilderBotModuleCA.cs`,
  `BotGlobalUnitBudget.cs`, `ai.yaml`, `defaults.yaml`. Phases 6a–6e do not need those builder
  files; if you must touch them, say so in the PR.
* **Sync rules** (lessons from #458): bot logic is unsynced and acts only through orders
  (`AI_ARCHITECTURE.md` §1.1); never iterate a `HashSet<string>` to drive orders or synced state;
  declare granted conditions with `[GrantedConditionReference]`; a shadowing trait must re-declare
  its interfaces.
* **Gates per PR:** C# build (`dotnet build -c Release`), `python tools/tests/ai_bot_player_gate.py`
  (running it starts a match; it has no `--help`), and a boot to the main menu with `perf.log`
  **newer than your pre-launch snapshot**. Put the gate numbers in the PR body.
* **Sign** `Co-Authored-By: Devin AI <devin@cognition.ai>`.
* **Before 2026-10-20:** a short handoff in `docs/HANDOFF.md` (the AI lane section) saying which of
  6a–9 landed and what is open, and tick the phases in `AI_ARCHITECTURE.md` §10.6.

---

## Appendix A. Non-AI takeaways from the Astor conversation (for the maintainer, NOT the AI lane)

These came up in the same 2026-09-11 conversation. Each is a gameplay or balance decision, so each
needs a maintainer ruling before any agent builds it. None is assigned to Devin-Cloud.

| Topic | What Astor said | Evidence | Cameo today | Open question |
|---|---|---|---|---|
| Late-game infantry collapse | The maintainer's problem: infantry is useful early, then shut down by late-game artillery. CN has "high fatality" and some "power infantry" | conversation | not written down in `DESIGN.md` or `ROADMAP.md` (grep, 2026-09-26) | is this a design goal to fix? It interacts with the warhead and armour laws, so it goes through `DESIGN.md` first |
| Infantry cover | CN infantry moves through trees and gets defence plus camouflage there. Planned: cover next to tanks and buildings, disabled against a structure the unit is attacking (for melee units like the Samurai) | CN `Traits/World/ForestCoverSystem.cs`: a condition granted in forest cells through a cell influence map | no cover system (only the Hydralisk lab notes mention cover) | the maintainer's own objection stands: barren and Arrakis maps have no trees. Adjacency cover would work on every map |
| Armour layers | CN: armour class (inf / structure / vehicle) + weight (light … superheavy) + secondary HP (ablative, shields), piercing and armour bypass | conversation | Cameo already has 17 armour types plus a separate shield ladder, and the W21 stack Shield → Integrity → Armor → Health (`design/ARMOR_LAYERS.md`; `GrantsShield`, `Integrity`, `ArmorPlating` traits) | nothing to take without a specific gap. Compare CN's piercing and bypass with Cameo's Armor Piercing tag (#445) if one is found |
| Regeneration | CN: veterans only. Cameo: all units, slowly (100 s from 0 to full) | conversation | `ScaledSelfHeal`; ruled in `DESIGN.md` | none, a different design choice |
| Mobs (squad infantry, restorable in barracks) | CN uses the Generals Alpha mob system as a base, fixed and extended; "runs well in CN" | CN `Traits/MobSpawner/MobSpawnerMaster.cs` (850 lines) + slave, selection decoration | Cameo tried the Generals Alpha mobs before: bad lag, and "stupid" individual units (the zombie horde faction) | worth a performance test of CN's version before anyone ports it. `design/UPSTREAM_MODS.md` is where upstream ports are triaged |
