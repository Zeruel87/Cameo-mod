# AI synthesis: RV × CA × Cameo × CN × Fransbot, and a more human-like bot

_Written 2026-09-27 by Claude-Local (coordinator), from measurements taken the same day. It is
the plan for **combining** the five sources of Cameo's bot code. The binding design stays in
[`AI_ARCHITECTURE.md`](AI_ARCHITECTURE.md); the CN and Fransbot feature research is in
[`AI_FRANSBOT_RESEARCH.md`](AI_FRANSBOT_RESEARCH.md); how CA code is kept current is in
[`UPSTREAM_MODS.md`](UPSTREAM_MODS.md) §4a. Where they disagree about something already built,
the code wins._

> **2026-09-28 review: read §7 first.** It measures what actually runs in the Frankenstein
> `hard` bot today (0 Fransbot modules, 1 CN module), picks the best source per layer, lists
> two real defects, and gives the merge order that **supersedes §6**. Fransbot upstream is now
> V1.29.31 on `main`, not `V1.29.19-RC` as §1 says.

---

## 0. TL;DR

1. **Five sources, one bot.** Cameo's AI is already a deliberate "Frankenstein":
   * **RV-engine** bot modules (engine Common + AS), which update with the engine;
   * **CA** bot modules, which are copied by hand, with **RV features merged into them** (the
     guerrilla squads);
   * **Cameo's own** phases 1–6f (master module, personalities, counter demand, fog memory,
     scouting, risk gate, routing, artillery).

   Two more are now fully readable: **Crystallized Nexus** (public, GPLv3) and **Fransbot**
   (private; the maintainer has collaborator write access since 2026-09-27).
2. **Fransbot is far easier to bring in than feared.** It is a standalone plug-in DLL
   (`Fransbot.OpenRA.dll`, 24 bot modules, 49,709 lines). Compiled **unchanged** against Cameo's
   engine, retargeted from .NET 10 to .NET 8, it produces **exactly one** error: Cameo's
   `IBotBaseExpansion` has one extra member, `IsConyardRelocationPending(Actor)`, added by Cameo
   (cameo-engine #90), not by bleed, so moving to bleed does not remove it. The engine is moving
   to current OpenRA bleed and .NET 10 anyway, by maintainer order (§4.4). That is Fransbot's
   native target, so the port no longer needs the retarget. The real work is content: 36 yaml-overridable
   Red Alert id lists to fill per faction, and ~17 places that hard-wire RA ids into logic.
3. **Recommended route: run Fransbot side by side first, then harvest.** Vendor it as its own
   project in Cameo's solution, give the lobby a second bot type, and let match logs decide which
   Fransbot systems replace which Cameo systems. Merging 50k lines into the CA squad manager
   first would be the most expensive and least informed option.
4. **CA sync is now tooled.** Cameo's engine is the RV fork, so CA fixes arrive only by copying.
   * `audit_ca_drift` (rewritten to use CA's history) classifies every file.
   * `ca_vendor_sync` applies the safe part and 3-way merges the rest.
   * **`audit_ai_frankenstein`** fails the moment a sync drops one of the **140** RV-merged or
     Cameo-added symbols in the bot modules.

   All **9** Frankenstein bot files conflict with upstream: they are merged by hand, one PR at a
   time (§3).
5. **"Human-like" is mostly limits and flaws, not more skill** (§5). The research is consistent:
   skill alone does not read as human. Cameo already has the perception half (fog, memory,
   scouting); the missing half is an **action budget without bursts**, **staggered orders**,
   **reaction delays for tactics** (not just personality), and **controlled mistakes**.

---

## 1. The five sources, measured

| Source | How it reaches Cameo | Size here | Strongest parts | Kept current by |
|---|---|---|---|---|
| **RV engine** (`engine/OpenRA.Mods.Common`, `engine/OpenRA.Mods.AS` bot modules) | the engine (`mod.config` `ENGINE_VERSION`) | engine-side | guerrilla squad states; stuck-unit kick / make-way; base expansion (`McvExpansionManagerBotModule`); `LoadCargo`, `ExternalBotOrdersManager`, `SendUnitToAttack`; `CncEngineerManagerBotModule` (bridge repair, loaded as `CncEngineerBotModule`); **unused**: `BevManagerBotModule`, `SharedCargoBotModule` (AI_MASTER_PLAN RV1) | engine updates (automatic) |
| **CA** (`OpenRA.Mods.CA/Traits/BotModules/`) | **copied by hand** | 24 files | squad manager and states, base/unit builders, compositions, fuzzy attack-or-flee | `audit_ca_drift` + `ca_vendor_sync` (§3) |
| **Cameo** (`OpenRA.Mods.Cameo/Traits/BotModules`, `Traits/Bot*`) | own | phases 1–6f | master module + snapshot, personality switching, counter demand, fog memory, `ScoutBotModule`, risk gate, risk routing, artillery squads, match logs | own |
| **Crystallized Nexus** (`~/Documents/GitHub/crystallized-nexus`, `30cf70a`, GPLv3) | not yet | 18 modules, ~20k lines | terrain topology (chokepoints and doors from the pathfinder graph), region roles, combat analysis + nemesis, coordinated and pincer waves, observer-gated artillery, transports | port by module |
| **Fransbot** (`~/Documents/GitHub/OpenRA-Fransbot`, branch `V1.29.19-RC` = V1.29.23, GPLv3 headers) | not yet | 24 modules, 49,709 lines | General → Broker → Commanders hierarchy; risk model; strategic map (from live Shroud); combat intel memory; economic saturation; **MCV expansion incl. sea / island (11,600 lines)**; transport, ground transfer, SpecOps; YAML personalities | its own git; the same drift tooling can track it |

### 1.1 The Frankenstein, located precisely

`tools/audit/audit_ai_frankenstein.py --write` produced `ai_frankenstein_manifest.json`:
**140 protected symbols in 18 CA bot files, 65 of RV origin and 75 Cameo's own.** Examples:

* **RV:** `GuerrillaTypes`, `JoinGuerrilla`, `MaxGuerrillaSize`, `GuerrillaUnitsHitState`,
  `GuerrillaUnitsRunState` (squad manager, squads, ground states), `KickStuckTicks`,
  `MaxMakeWayPossibility`, `MaxSquadStuckPossibility` (ground and naval states),
  `GetPathfindLeader`, `CheckReachability`, `ShouldFleeSimple` (state base), and the base-expansion
  fields in `BaseBuilderBotModuleCA`.
* **Cameo:** the phase 4–6f surface (`PreferMainTarget`, `AttackRiskMargin`, `UseRiskRouting`,
  the artillery fields, the fog and router interfaces), `SquadCAType.Guerrilla` and `.Artillery`.

Origin labels are best-effort (a name shared with RV code counts as RV). Every listed symbol is
protected either way.

### 1.2 What upstream CA added to the bot modules since Cameo copied them

`audit_ca_drift` lists the upstream commits per file. For the bot modules:

| Upstream change (date) | Files | Overlap with what Cameo already has |
|---|---|---|
| *Fix AI not repairing buildings* (2026-07-26) | `BuildingRepairBotModuleCA` | none; **verbatim sync, the only safe bot file** |
| *Skirmish AI indirect routes of attack* (2026-02-08) | squad manager, squad, ground, protection, state base | Cameo already has `IndirectRouteChance`: check whether it is this change, partly ported |
| *Updated AI routing* (2026-02-08) | squad manager, squad, ground, state base | **overlaps Cameo 6e risk routing**: pick one routing owner, never two |
| *AI harasser squads* (2026-02-08) | squad manager, squad, ground | **overlaps the RV guerrilla squads**: compare before taking; the likely answer is to keep guerrilla and take only what harassers add |
| *Compositions* (2026-02-09) | squad manager, ground | Cameo's compositions (phase 5 demand tokens) are already extended; merge carefully |
| *Fix AI aircraft limits* (2026-01-09), *aircraft target by armor type* (2025-05-26), *AI crash fix* (2025-06-08) | air states | take (bug fixes), but the crash fix first |
| *AI updates* (2025-08-10) | base builder, queue manager, navy, most states | large; read hunk by hunk |

---

## 2. One decision hierarchy

Fransbot's documented architecture is the cleanest of the five, and it maps onto what Cameo
already built:

```
Sensors / intelligence     →  General (strategy)  →  Broker (bids)  →  Commanders  →  execution  →  recovery
Cameo: BotFogMemory,          MasterAiBotModule       (none)            CA squads       orders
       ScoutBotModule         + BotPersonality-                          (+RV guerrilla,
CN:    TacticalMap, Combat-     Controller                               Cameo artillery)
       Analysis
Fransbot: StrategicMap,        FransGeneral           FransCommandBid   Ground/Air/Sea/
          CombatIntel, Risk-                                             SpecOps commanders
          Model
```

**Rules for the synthesis** (they extend `AI_ARCHITECTURE.md` §10.1, one owner per decision):

1. **One world model.** Cameo's `BotSituation` snapshot stays the single published view
   (`AI_ARCHITECTURE.md` §10.3). Sensors from CN or Fransbot feed it; they do not publish rival
   snapshots. Candidates, to be decided by match data rather than taste:
   * region set: CN topology regions vs Fransbot strategic map vs Cameo's 8×8 grid;
   * threat: Fransbot `RiskModel` vs CN `CombatAnalysis` vs Cameo fog memory.
2. **One strategist.** `MasterAiBotModule` + `BotPersonalityController` own posture and main
   target. Fransbot's General is the reference for **missions** (RECON / RAID / SECURE / DEFEND);
   CN's profile module is the reference for switching **numbers only** (its mechanism is
   forbidden, `AI_ARCHITECTURE.md` §1.6).
3. **One execution layer per unit.** A unit belongs to a CA squad **or** a Fransbot commander,
   never both. Side by side (§4, route A) guarantees that by construction: two separate bot types.
4. **Support systems are the easiest wins.** Fransbot's MCV expansion (sea and island), economic
   saturation and transport logic, CN's repair manager and garrison matching, and RV's unused
   bridge-repair module are self-contained. They can be adopted without deciding the
   squad-vs-commander question.

---

## 3. Syncing CA without breaking the Frankenstein (runbook)

Measured 2026-09-27 against CAmod `f31049d2`: 185 vendored files. 39 identical, **41 stale**
(safe verbatim syncs), 23 modified, **45 modified and changed upstream**, 12 moved or removed,
25 Cameo-only; **313 upstream files never copied**. `ca_vendor_sync` dry run: 41 verbatim + 16
clean 3-way merges + **21 conflicts** + **8 Frankenstein files skipped**, and **0 yaml field
losses**.

1. **Refresh and measure:** `git -C ~/Documents/GitHub/CAmod fetch` (a **full** clone:
   `fetch --unshallow` once), then `python tools/audit/audit_ca_drift.py`.
2. **Safe part, in a worktree:** `python tools/audit/ca_vendor_sync.py --apply` syncs stale files
   and clean merges, **skips Frankenstein files**, reports yaml field losses (the engine drops
   unknown fields in silence, CLAUDE.md rule 8b), then runs the Frankenstein guard. Then a C#
   build (a clean merge can still fail to compile: CA targets an older engine), boot to the menu,
   and one PR per area.
3. **Frankenstein files, one per PR:**
   `ca_vendor_sync.py --apply --include-frankenstein --path <file> --write-conflicts`, then
   resolve by hand using §1.2's overlap table. Before the PR:
   * `python tools/audit/audit_ai_frankenstein.py` is PASS: no RV or Cameo symbol lost;
   * `python tools/tests/test_ai_attackbase_lookup.py` passes;
   * `python tools/tests/ai_bot_player_gate.py` passes;
   * **a squad-forming match** (the gate alone never forms an army; see LESSONS_LEARNED) with a
     guerrilla-capable personality, checked in the logs for guerrilla squads, artillery attaching
     and the risk gate firing;
   * boot to the menu.
4. **Never** resolve a conflict by taking upstream's side of a hunk that contains a protected
   symbol. The guard catches a deleted name, but not a name that survives while its behaviour is
   bypassed; that is what the match check in step 3 is for.

### 3.1 Harasser squads (CA) and guerrilla squads (RV): two halves of one raid, not duplicates

Measured on master (`SquadManagerBotModuleCA.cs`, `Squads/States/GroundStatesCA.cs`) and on CA
`f31049d2`, where harasser squads arrived in `55e042954` (2026-02-03), after Cameo copied CA.

| | Guerrilla (RV, in Cameo today) | Harasser (CA upstream, not in Cameo) |
|---|---|---|
| Unit list | `GuerrillaTypes`: **254 ids** in each of the 5 personalities, nearly every combat unit including MLRS and battle tanks | `HarasserTypes`: **18 ids**, fast or light (bikes, light tanks, buggies, drones, a few infantry) |
| Assignment | **one** shared squad per bot. One roll per `FindNewUnits` pass; listed units join while the squad is at most `MaxGuerrillaSize` | deterministic: every listed unit, **one squad per actor type** (homogeneous), any number of squads |
| Launch | at once | waits: never below 3 units, 5 % at 3, 10 % at 4, always at 5+ |
| Target | closest enemy | a `HighValueTargetPriority` roll picks a random high-value actor (`FindHighValueTarget`), else the closest preferred building |
| Route | Cameo **already took CA's flank trick**: 3 distinct routes, pick among the 2 longest, exempt from 6e risk routing | 12 distinct routes, pick among the 2 longest, starting from the own building nearest the target |
| On contact | `GuerrillaUnitsHitState` ⇄ `GuerrillaUnitsRunState`: fight; on damage or a loss while locally outnumbered, run to a random own building for 2 ticks, then return. **Hit and run.** | ordinary `GroundUnitsAttackState`: fight, or fuzzy-flee like any squad |

**Answer:** harasser decides *where and when* (a soft or valuable target, reached the long way
round, only once enough units exist). Guerrilla decides *how to fight on arrival* (hit, run,
come back). They are complementary, not the same behaviour. They still cannot coexist as two
squad types. `FindNewUnits` is an if/else chain with guerrilla first, so a unit on both lists
always goes guerrilla, and harasser would only ever get the leftovers. **Plan for the CA
bot-file sync:**

1. Keep `SquadCAType.Guerrilla` and its Hit/Run states. They are protected RV symbols
   (`audit_ai_frankenstein.py`).
2. Port harasser's parts into guerrilla, each behind a field that defaults to today's behaviour:
   the launch threshold, the high-value target roll, the 12-route breadth, and grouping by actor
   type. Mixed speeds break hit and run.
3. Load `HarasserTypes` into the same set as `GuerrillaTypes`, so a verbatim CA yaml sync
   loses no field (CLAUDE.md rule 8b).
4. Which units belong in the list is a **design call for the maintainer**. A mammoth tank that
   runs home after every hit is not a guerrilla, and today's list holds 254 units against CA's 18.
   **Ruled 2026-09-27: fast/light units only.** Generate `GuerrillaTypes` per faction from traits
   (speed and cost bands), like CA's 18 harassers. Never hand-type it. **Bands ruled 2026-09-29:**
   fastest third of the faction's infantry or vehicles, cost at most the median; generated onto
   the actors by `tools/ai/derive_guerrilla_roles.py` (AI_ARCHITECTURE §2.8a).

**Found while measuring: `JoinGuerrilla` is inverted.** Its description says "possibility to
join", but the code joins when `rand(100) >= JoinGuerrilla`, so the join chance is
**100 − value**. The inversion came verbatim from the engine's own `SquadManagerBotModule.cs:355`
(RV lineage). Cameo's five values only read sensibly under the real meaning: rush 5 → **95 %**
join (max 16), expansion 15 → 85 %, tech 40 → 60 %, turtle 60 → 40 %, steamroller 100 → **0 %**
(one blob). The roll also happens once per pass, not once per unit. Do not flip the comparison
alone, because that silently inverts every personality. Either rename the field (e.g.
`GuerrillaSkipChance`), or flip the code **and** the five values in the same commit.
**Ruled 2026-09-27 and done:** code and values flipped together. The name now means join chance,
and the values are rush 95, expansion 85, tech 60, turtle 40, steamroller 0, so behaviour is
unchanged. Still open: `guerrillaForce == null` short-circuits the roll, so a bot with no guerrilla
squad always forms one, and steamroller's 0 % is "at most one squad" (`LESSONS_LEARNED.md`).

**Unused vendored code is the other half.** `python tools/audit/audit_ca_unused.py` lists every
type Cameo never uses and **what CA uses it for**. Today: 85 of 247 traits are unused and CA uses
57 of them (e.g. `ProvidesPrerequisiteValidatedFaction` 348×, `PeriodicProducerCA` 50×,
`SpawnRandomActorOnDeath` 45×, `DamageTypeDamageMultiplier` 27×, `TargetedAttackAbility` 9×).
Unused ≠ dead: implement the purpose, or delete only when CA doesn't use it either.

---

## 4. Bringing Fransbot in

### 4.1 Measured facts

* **Access:** `AedisToru` has `pull` + `push` + `triage` on `f850484/OpenRA-Fransbot` (private).
  Newest code: branch `V1.29.19-RC` (V1.29.23, 2026-09-26). Tags `V1.29.18-Baseline`,
  `V1.29.19-external-baseline`.
* **Integration contract** (`integration/README.md`): a separate assembly, added **last** to
  `Assemblies`, plus `rules/fransbot-ai.yaml` + `rules/fransbot-personalities.yaml` + a Fluent
  file. No engine edits.
* **Compile against Cameo's engine:** 1 error (the missing `IsConyardRelocationPending`), after
  retargeting `net10.0` → `net8.0`. The engine's own implementation
  (`McvExpansionManagerBotModule.cs:1042`) shows what it must answer.
* **Class names** all start with `Frans`, so there is no clash with AS, CA or Cameo types.
* **Fog honesty:** mostly true. Sensors check visibility (General, CombatIntel, SpecOps); the big
  world scans are of the bot's **own** units (21 of 22 in MCV expansion filter `Owner == player`).
  About 3 enemy-side scans lack a visibility check (MCV expansion, defense commander, base
  builder); audit them in the port. Its runtime baseline is "Explored Map ON + Fog ON": geography
  known, enemies not.
* **RA coupling:** 36 `[ActorReference]`-style default lists (`HarvesterTypes = {"harv"}`,
  `McvTypes = {"mcv"}`, radar threat lists …) that yaml overrides; ~17 logic sites comparing
  against RA ids, mostly the air commander's target preferences (`"fact"`, `"harv"`, `"mcv"`).
  The first set becomes per-faction yaml (generate it from traits: `BaseBuilding`, `Harvester`,
  `Transforms` into a construction yard …). The second set becomes trait-based classification.
* **Licence:** every file carries OpenRA's GPLv3 header; there is no repo LICENSE file. Credit
  fransotto in each vendored file and ask him to add a LICENSE.

### 4.2 Routes

| Route | What | Cost | Verdict |
|---|---|---|---|
| **A. Side by side** | vendor `src/Fransbot.OpenRA` as `OpenRA.Mods.Fransbot/` in `CameoMod.sln` (so it builds into `engine/bin` like the other mod assemblies), add it last to `Assemblies`, add a `fransbot` `ModularBot` in `ai.yaml`, fill the id lists per faction | 1 method + yaml + the ~17 logic sites; boot + matches | **Do first.** It gives a Cameo AI vs Fransbot comparison and doubles as the automatic balance-testing harness the maintainer asked about |
| B. Harvest | move individual Fransbot systems behind Cameo interfaces (MCV island expansion, economic saturation, risk model, transport) | per module | **Second**, chosen by route A's match data |
| C. Full merge | replace the CA squad layer with Fransbot's broker and commanders | very large | not now; revisit after B |

Upstream tracking: vendor at a recorded commit, and point the same history-aware drift approach
(`audit_ca_drift.py`, `ca_vendor_sync.py`) at the Fransbot clone when a second upstream needs it.
Fransbot keeps releasing (V1.29.20 → .23 in a week).

### 4.3 Personalities: CN × Fransbot × Cameo, merged by layer

Measured, not assumed:

* **Cameo:** 5 personalities (rush, turtle, tech, expansion, steamroller). Each is a set of
  condition-gated module instances (`SquadManagerBotModuleCA@rush`, …). `BotPersonalityController`
  switches between them through orders, which keeps it sync-safe (`AI_ARCHITECTURE.md` §4.2, §10.4).
* **CN** (`CNBotProfileBotModule.cs`, `30cf70a`): `BotProfile { Rush, Turtle, Tech, Expansion,
  Steamroller, Adaptive }`, the **same five names** plus a switcher. A profile moves **budgets**:
  expansion, tech, defence and production percentages, plus tech-stage timing.
  `Adaptive` re-scores the profiles with momentum, a minimum hold time, a cooldown, an emergency
  override and team coverage. It switches by granting conditions from unsynced code, which Cameo
  cannot copy (`AI_ARCHITECTURE.md` §1.6).
* **Fransbot** (`FransCommanderCoreBotModule.cs`): **one** profile, `PersonalityProfile:
  balanced`. By its own description it is a seam: "future personality presets should tune
  existing Commander/economy parameters through this profile instead of duplicating tactical
  logic". Its knobs are continuous weights on the commander auction: `RouteRiskWeight`,
  `EtaCostPerTick`, `ForceValueDivisor`, `Ground/Air/SeaFactorPercent`, the RAID and RECON
  margins and costs, and the ground commanders' secure and defend-preservation thresholds.
  `fransbot-personalities.yaml` sets these identically on all 10 ground commanders.

**They collide only if two of them act as the strategist.** Each answers a different question:
CN decides *which* posture and *when* to switch, Fransbot decides *how* a posture is executed, and
Cameo already owns the switch and the names. So a merged personality is **one record with three
blocks**, and each block feeds the module that already consumes it:

| Block | Source | Consumer |
|---|---|---|
| budgets + tech timing | CN profile | unit and base builders |
| execution weights | Fransbot knobs | Fransbot commanders, once they execute (route A) |
| squad parameters (guerrilla share, squad size, attack interval, indirect-route chance) | Cameo yaml today | the CA squad manager |

The switching rule is CN's `Adaptive` scoring, implemented inside Cameo's
`BotPersonalityController`, so the order bridge stays. The result is richer than either source:
a rush that is both lean on tech (CN) *and* cheap on ETA, bold on route risk and generous on raid
margin (Fransbot). A CN profile alone cannot express that, and Fransbot has only one profile.

Collision rules for whoever implements it:
* **One switcher.** CN's own `SwitchTo` is never ported. Fransbot's `PersonalityProfile` becomes
  a read-only mirror of Cameo's active personality.
* **One Fransbot instance, not five.** It reads its weight block from a table keyed by
  personality. Per-personality instances of 24 modules would repeat CN's stale-reference bug
  (§1.6 there).
* **Weights per personality, unit lists per faction.** Keep the two axes independent.
* Fransbot's `balanced` has no Cameo counterpart. Map it to the adaptive default rather than
  adding a sixth personality.

Sequencing: after DAWN's side-by-side port (route A). The execution block only matters once
Fransbot executes, and its match logs are what tune the weights.

### 4.4 Engine: moving to OpenRA bleed and .NET 10

Maintainer order, 2026-09-27. Measured: cameo-engine and OpenRA bleed share base `b0b0544d4a`
(2026-05-11). Bleed has **99** commits since then, against Cameo's 1,975. A merge gives **25
conflicted files, ~42 hunks**. The expensive parts are bleed's `float2`/`float3` →
`System.Numerics` `Vector2`/`Vector3` move (`90c4415b7e`), which also reaches the AS, CA and Cameo
assemblies, and the map generator's settings → options/parameters refactor.
`mods/cameo/rules/map_generators.yaml` needs bleed's `RenameMapGeneratorParameters` update rule:
3 `Settings` → `Options` and 116 → `Parameters`. The engine drops the old keys in silence, and
the utility cannot run the rule on Cameo (its loader rejects an unrelated blank line in
`weapons/redalert2mod.yaml`). Work branch: `cameo-mod/OpenRA` `bleed_sync_2026_09`. The claim
and gates are in the fleet folder.

### 4.5 Fransbot ↔ Cameo, layer by layer (from fransotto's own architecture chart)

fransotto (2026-09-27) sent his hand-drawn architecture as a chart, "Fransbot V1.25.x: Simple
Architecture and Mission Flow". His core loop is **Observe → Understand → Create mission → Bid →
Assign → Execute → Recover → Repeat**, and he said a lot of it "is named differently". This table
is the translation, checked against the V1.29.23 source. Several V1.25 chart modules have since
been merged or renamed, and V1.29 adds Defense, Transport and CommanderCore modules.

| Fransbot layer (his chart) | Fransbot V1.29 module | Cameo today | Gap |
|---|---|---|---|
| **1. World** (tick loop, fog, events) | — | same engine | — |
| **2. Sensors and intelligence** | `FransCombatIntel`, `FransStrategicMap`, `FransRiskModel`, `FransEconomicSaturation` | `BotFogMemory` (6a), `BotSituation` (8×8 regions), `ResourceMapBotModule` (RV), `CombatAnalysisBotModule` (#564, per-role threat + nemesis), `MasterAiBotModule` risk provider/router (6e) | different axes, no duplicate (#564 checked it) |
| **3. General** (big picture, priorities, target area, mission types; no micromanagement) | `FransGeneral` | `MasterAiBotModule` + `BotPersonalityController` + `BotCounterDemandController`: main target, posture, demand; never picks units | Cameo has no explicit **mission object** |
| Mission **RECON** | commanders + `CommanderCore` RECON pricing | `ScoutBotModule` (6b) | — |
| Mission **RAID** (hit a valuable target, leave) | commanders + RAID pricing | guerrilla squads (hit and run) + the harasser port (§3.1: high-value target roll, long routes) | being built |
| Mission **SECURE** (clear and hold) | `FransGroundCommander` SECURE | assault/rush squads; 6f staging rallies before the attack | no "hold", no forward anchor |
| Mission **DEFEND** | `FransDefenseCommander` | `Protection` squads | — |
| **4. Bid and broker** (commanders bid on score, risk, ETA, force; the best bid wins and reserves actors) | `FransCommandBid` | **none.** `SquadManagerBotModuleCA.FindNewUnits` assigns units to squads by static type lists when they are produced | **the main structural difference** |
| **5. Commanders** Ground / Air / Sea / SpecOps (+ Defense, Transport) | `Frans{Ground,Air,Sea,SpecOps,Defense,Transport}Commander` | `SquadCA` types Rush/Assault, Air, Naval, Guerrilla, Protection, Artillery; special ops spread over `CaptureManagerBotModuleCA`, `CncEngineerBotModule`, `SendUnitToAttackBotModule@chrono`; transport only `LoadCargoBotModule` | no transport/ferry commander (island expansion comes with Fransbot, §4.2) |
| **6. Execution + Anchor** (regroup/recovery point; SECURE creates a forward anchor; retreat to it; repaired units rejoin) | commanders | squad state machines; guerrillas flee to a random own building; 6f staging = a rally point before the assault | no **forward anchor**, no rejoin-from-anchor |
| **Support modules** Economy, BaseBuilder, UnitBuilder, MCV, GroundTransfer, SupportCoordinator, Capture | `FransBaseBuilder`, `FransUnitBuilder`, `FransMcvExpansionManager`, `FransGroundTransfer`, `FransSupportCoordinator`, `FransSupportPower`, `FransHarvester`, `FransMinelayer` | `BaseBuilderBotModuleCA`, `UnitBuilderBotModuleCA`, `McvExpansionManagerBotModule`, `SupportPowerBot(AS)Module`, `HarvesterBotModuleCA`, `MinelayerBotModule`, `CaptureManagerBotModuleCA` | ground transfer has no Cameo counterpart |

**What the architect takes from it.** Cameo already has Observe, Understand, Execute and part of
Recover. Its missing middle is **Create mission → Bid → Assign**. Units belong to a squad because of
their type, not because a mission needed them. Fransbot's broker is therefore the most valuable
single idea to import, and it fits the list ruling (§2.8 of AI_ARCHITECTURE, roles on actors):
**roles decide which units are eligible for a mission, and the broker decides which units a
mission gets.** That keeps one authority per decision (AI_ARCHITECTURE §10.1). The General (the
master module) creates missions, the broker allocates, and the commanders (squads) execute.
Sequencing: this comes after route A's side-by-side matches (§4.2), which show whether the broker
beats static assignment in play, before anything in the CA squad manager changes.

---

## 5. Making the bot more human-like: research and mapping

**What the research says.** Skill alone doesn't make an agent read as human; believability has
to be designed in ([Many Challenges of Human-Like Agents, 2025](https://arxiv.org/pdf/2505.20011)).
AlphaStar is the cautionary example. It needed an action cap **and** a rule against spending the
quota in superhuman bursts at critical moments, and a camera, meaning attention, restriction
([Irpan 2019](https://www.alexirpan.com/2019/02/22/alphastar.html),
[Wikipedia](https://en.wikipedia.org/wiki/AlphaStar_(software))). RTS work on human-like
movement finds humans move groups **non-simultaneously**, one after another
([ResearchGate](https://www.researchgate.net/publication/314886714_Real-time_strategy_games_bot_based_on_a_nonsimultaneous_human-like_movement_characteristic)).
Personality systems that are consistent but carry controlled randomness beat fixed scripts
([Combining AI methods for learning bots](https://www.researchgate.net/publication/26571503_Combining_AI_Methods_for_Learning_Bots_in_a_Real-Time_Strategy_Game)).

| Human trait | Mechanism | Cameo today | Best source to take from | Phase |
|---|---|---|---|---|
| Sees only what it scouted, remembers, can be wrong | fog-gated observation + decaying memory | ✅ 6a–6d, `ScoutBotModule` | Fransbot CombatIntel (mobile contacts decay, buildings stay) | done |
| Limited attention | a budget of "focus points" per decision tick (the camera analogue): at most N squads or places get new orders per tick | ⚙ producer | Fransbot broker (bids compete for commanders) | **H1 producer landed** 2026-09-28: `IBotActionBudget.TryConsumeAttention` consumed 2026-09-28: Cameo `ModularBot` shadow consults it per module per tick, round-robin start so slots rotate instead of starving the tail |
| Limited hands (APM) — ⛔ **dropped 2026-09-28: no APM cap** (DESIGN.md §19.1; a cap measured 0–4) | action budget over a sliding window, **no bursts** (the AlphaStar lesson) | ⚙ producer (cadences only) | new | **H1 producer landed** 2026-09-28: `IBotActionBudget.TryConsumeActions` consumed 2026-09-28: the shadow gates the per-tick order drain on it — denied orders stay queued (deferral is the stagger) |
| Moves groups one after another | stagger order issue across squads by a few ticks | ⚙ producer | new | **H1 consumed** 2026-09-28: attention slots cap modules per tick; the rotating start index spreads turns across ticks |
| Reacts with a delay | per-difficulty delay for tactical reactions (defend, retreat, retarget), not only personality switches | personality only (#435) | extend #435 | **H2** |
| Makes mistakes | controlled noise: occasional sub-optimal target, late expansion, imperfect split; scaled down with difficulty | ❌ | CN randomness exponent on template choice | **H2** |
| Adapts its strategy | posture switching on what it saw | ✅ phase 3 + counter demand (phase 5) | Fransbot risk/reward missions | done / 6c |
| Harasses, feints, attacks from two sides | raids on soft targets, multi-prong waves | guerrilla (RV), risk routing (6e) | CN pincer waves, CA harasser squads, Fransbot RAID | 6f / 6g |
| Retreats, regroups, repairs | pull damaged units, re-form, return | CA fuzzy flee | Fransbot RETREAT, CN repair manager | new: **H3** |
| Uses combined arms sensibly | artillery behind the line, support following, AA escort | ✅ 6f artillery | CN support attach, Fransbot air/ground coordination | 6f+ |
| Expands when safe, greedy when rich | economy state machine | caps only (`BotLimits`) | **Fransbot economic saturation** (throughput and cash, not building counts) | new: **H3** |
| Expands to islands | ferry the MCV | ❌ (dropped at `McvExpansionManagerBotModule.cs:470`) | **Fransbot MCV expansion (sea)**, CN transports | 7 |
| Talks to allies | beacons, simple chat ("need cash", "AA here") | ❌ | Fransbot (beacons WIP, chat planned) | 8 (approved) |
| Learns you across games | priors per matchup from logs | logs ✅, priors ❌ | `AI_ARCHITECTURE.md` §8 (bandit); case-based reasoning from human replays | 7 (existing) |

**How to measure "human-like"**, so it isn't judged by feel: the action rate and its burstiness
(max actions in any 2-second window vs the average), reaction latency distribution, how
simultaneous group orders are, and a blind test in which playtesters guess human vs bot from
replays. The match log (schema 2) is the place to record the first three.

---

## 6. Order of work

1. **CA bot sync, file by file** (§3), starting with `BuildingRepairBotModuleCA` (verbatim) and
   the air-state bug fixes. One owner at a time; the other AI lanes stay off those files during
   each PR.
2. **Fransbot route A** (§4.2): vendor, fix the one interface method, generate per-faction id
   lists, boot, a lobby bot type, first matches.
3. **Human-likeness H1** (action budget, attention, staggered orders), a small self-contained
   module between decision and `QueueOrder`.
4. Phases 6g → 7 (island, informed by Fransbot's MCV code) → 8 (beacons) → H2 / H3, and route B
   harvesting in the order route A's data suggests.

Lane assignments: `../Cameo-mod-fleet/ORDERS_2026-09-27_ai_next_lanes.md` (outside the repo).

---

## 7. Review, 2026-09-28: the Frankenstein today, layer by layer, and the best-of plan

_Maintainer order (2026-09-28): review the whole AI architecture against the plan — one
ultimate bot from RV × CA × CN × Fransbot (+ Cameo's own), **cherry-picking the best of each
and merging where possible**. Measured on master `fd852d2fe` + the A/B rounds 2–4._

### 7.1 The headline

* **The plan is right; the harvest has barely started.** RV and CA are merged (the 140
  protected symbols, §1.1). Cameo's own phases 1–6g all ship. From **CN only one module is
  ported as code** (`CombatAnalysisBotModule`); staging, observer-gated artillery and priority
  tags were re-implemented from CN's ideas (6f/6g). **From Fransbot, zero modules run in the
  Frankenstein bot:** all 24 are gated `enable-fransbot` and serve only the hidden donor type
  (route A, §4.2). Route B — harvesting one module at a time with an A/B each — has not begun.
* **Measured standing:** master's Frankenstein `hard` vs omniscient `classic` = **7–6** over 13
  matches on A Nuclear Winter (td_gdi mirror) — a coin flip. Each match is decided by one or two
  large fights traded ~2:1; income follows the trades. So the harvest should start with what
  wins fights (defence, siege, composition), not with economy or expansion.
* **Upstreams moved:** Fransbot is at **V1.29.31 on `main`** (we vendor V1.29.23 from
  `V1.29.19-RC`; the author's efficiency fix is V1.29.24) — re-vendor ordered to DAWN. CN is
  unchanged since `30cf70a`. CA drift is tracked by `audit_ca_drift`.

### 7.2 Layer by layer

"Best" is a judgement from the code read in §1, §4.5 and `AI_FRANSBOT_RESEARCH.md` §3/§3c,
**to be confirmed by an A/B** before it replaces anything. "Runs in `hard`" is measured
(`tools/ai/ai_module_map.py`, `mods/cameo/ai/*.yaml`).

| Layer | RV (engine/AS) | CA | CN | Fransbot | Cameo own | Runs in `hard` today | Best-of pick → action |
|---|---|---|---|---|---|---|---|
| Perception under fog | — | omniscient scans | fog-honest | fog-honest (live Shroud), ~3 enemy scans | `BotFogMemory` (6a), fogged scans (6d), `audit_fog_honesty` | Cameo | **keep Cameo**; hold every donor to the fog audit |
| Spatial model | — | — | **`CNTacticalMap`: chokepoints/doors from the pathfinder graph** | `FransStrategicMap`: sectors + passability layers | `RegionMemory`, a square grid, values overwritten on sight | Cameo grid | **CN topology** as the region set (§2 rule 1); grid stays the fallback. Add decay/averaging for "where they usually are" (§12.3) |
| Enemy force estimate | — | — | — | **`FransCombatIntel`: fair last-seen force estimate** | `EnemyProfile` from memory | Cameo | **harvest FransCombatIntel into CA-1** (the arsenal tracker) |
| Threat / risk | — | fuzzy flee | `CombatAnalysis` (ported) | **`FransRiskModel`: role-aware cell/route risk** | 6c gate, 6e router, threat level (shelved, lost 1–3) | Cameo + CN | **FransRiskModel** as the risk layer for CA-2 siege and CA-5 air routing; one publisher on the snapshot |
| Strategy / posture | — | — | `CNBotProfile` (numbers only, §1.6) | YAML personalities | master + 5 personalities, dynamic switching | Cameo | **keep Cameo**; bipolar axes (§4.6 of the threat branch) → one blended squad manager (CA-3) |
| Missions | — | — | — | **General → Broker → Commanders** (RECON/RAID/SECURE/DEFEND) | 7a missions (Raid/Defend/Recon/Secure) | Cameo | **keep Cameo's missions**, take Fransbot's SECURE/CLEAR validation and the §9 item 12 recon fix |
| Economy | `HarvesterBotModule` | `HarvesterBotModuleCA` | `CNHarvester` | **`FransEconomicSaturation`, `FransHarvester` (one-mine/one-PROC/one-HARV)** | harvester role, insurance | CA | A/B **FransEconomicSaturation** (self-contained, §2 rule 4) — after the fight-winning phases |
| Base building | `BaseBuilderBotModule` | **`BaseBuilderBotModuleCA` + queue manager** | `CNBaseBuilder` (4,347 lines) | `FransBaseBuilder` (Struggling/Growing/Prosperous/Surplus) | roles, BotLimits | CA | keep CA; mine `FransBaseBuilder`'s economic states and CN's defence placement for CA-2 |
| Expansion | `McvExpansionManager`, `BevManager` (unloaded) | — | `CNMcvExpansion` | **`FransMcvExpansion`: land + sea/island (13,500 lines at V1.29.31)** | — | RV | **Fransbot** for islands (phase 7) after the re-vendor |
| Production mix | `UnitBuilderBotModule` | **`UnitBuilderBotModuleCA`** + compositions | `CNUnitBuilder` | `FransUnitBuilder` (nearest-producer logic) | counter demand, `AdaptiveCounterProduction` (#605) | CA + Cameo | keep; add the role mix and learned weights (CA-1, CA-3) |
| Squads / tactics | **guerrilla states, stuck-kick, make-way** (merged) | **squad manager, fuzzy attack-or-flee** | waves, pincers, observer-gated artillery | Ground Commander FIGHT/RETREAT, **ForcePreservationGuard** | staging, artillery, support, risk gate, tags, attention budget | CA + RV + Cameo | keep the CA/RV core; **harvest ForcePreservationGuard (CA-2)**; CN pincer waves later |
| Base defence | — | `ProtectOwn` (drafts only an empty squad; never disbands) | `CNGarrison` | `FransDefenseCommander` (single owner of static defences) | **`ReinforceProtection` fix, A/B running** | CA | land the fix if it wins; compare `FransDefenseCommander` for static defences |
| Routing | — | "Updated AI routing" upstream (not synced) | door-aware paths | RiskModel routes, RoutineLand negative union (V1.29.24) | 6e region A* (ground only) | Cameo | one routing owner (§1.2): Cameo 6e now; evaluate Fransbot routes with the risk layer |
| Air | — | air states (upstream fixes unsynced) | — | **`FransAirCommander`** (SECURE/RECON/RAID, remembered buildings) | `AirPriorityTags`, `BigAirThreats` | CA | CA-5 air doctrine; harvest FransAirCommander's strike logic |
| Naval | — | navy states | — | `FransSeaCommander` | — | CA | later; Fransbot is the reference |
| Transports | `LoadCargo`, `SharedCargo` (unloaded) | — | `DeployBotModule` | **`FransTransport`, `FransGroundTransfer` (LST waves)** | — | RV | Fransbot, with the island work |
| SpecOps / capture | `CncEngineerManager` (bridge repair, loaded) | `CaptureManagerBotModuleCA` | `CNBridgeRepair`, `CNRepairManager` | `FransSpecOps` (capture, demo, Tanya C4) | — | RV + CA | later: FransSpecOps |
| Support powers | `SupportPowerBotModule` (WC2 powers, **ungated**) | — | — | `FransSupportPower`, `FransSupportCoordinator` (mission-aware) | — | RV + AS | take the Coordinator idea (powers timed with assaults) in CA-5 |
| Pacing / human-like | — | — | `CNBotPerf` idea | — | `HumanPace`, attention budget | Cameo | keep |
| Learning | — | — | — | LLM replay-tuning log | match + situation logs, stats timeline, losses by role, harness | Cameo | CA-1 / CA-1b (in-match weights + offline priors) |

### 7.3 Findings from this review (each has an owner)

1. **Double repair owner — a real bug.** `BuildingRepairBotModule` (Common) and
   `BuildingRepairBotModuleCA` are both loaded for `genericbot || classicbot` (`ai.yaml`, since
   #96). `RepairBuilding` is a **toggle** (`RepairableBuilding.RepairBuilding`: a second order
   removes the repairer), and each module queues it when `!RepairActive`. On a hit that jumps a
   building from Undamaged/Light straight to Medium or worse, both queue in the same pass and
   the second cancels the first. The same `!RepairActive` test also re-toggles a repair whose
   order has not resolved yet, or one the bot cannot pay for (it stays in `Repairers` while
   `RepairActive` is false). **Fixed 2026-09-30 (RV1, DESIGN §19.3):** the OpenRA module is
   unloaded, `classic` runs only the CA copy (as upstream CA), and `genericbot` runs
   `BaseRepairBotModule`, the two merged: CA's trigger at Light, OpenRA's repair-all sweep (now
   on the bot tick), and never a second order (`Repairers.Contains` + an in-flight window).
   Telemetry: situation log `own.repair_orders`, `repair_sweep_orders`, `repair_toggles_avoided`.
2. **Base defence never grows** (`ProtectOwn` drafts only into an empty squad; the squad never
   disbands). Found by #617's loss-by-role log: idle units at home were the biggest loss
   category. Fixed behind `ReinforceProtection` (Frankenstein personalities only); **A/B round 5
   running**.
3. **Fransbot contributes nothing to the candidate yet.** Proposed harvest order (each an A/B):
   ForcePreservationGuard + RiskModel (CA-2) → CombatIntel (into CA-1) → AirCommander strike
   logic (CA-5) → EconomicSaturation → MCV/island + transports (phase 7, after the V1.29.31
   re-vendor).
4. **CN's topology is the largest unharvested asset.** `RegionMemory` is a square grid; the
   §6a plan preferred CN regions. It matters for siege stand-off and routing (chokepoints).
   Owner: NOVA (layering) or whoever takes CA-2's routing part — claim it first.
5. **The module map is blind to Fransbot.** `ai_module_map.py` lists 34 loaded types but none
   of the Fransbot assembly, and the committed map is stale (`--check` fails on master).
   Owner: Devin Cloud (tooling), with the CA-1b work.
6. **Stale plan facts.** §1's table says CN/Fransbot "not yet" and names Fransbot branch
   `V1.29.19-RC`; §6's order of work predates 6a–6g, #605 and the A/B standard. §7 supersedes
   §6 for ordering; §12 of `AI_ARCHITECTURE.md` owns the combined-arms phases.
7. **Minor:** the WC2 `SupportPowerBotModule` is ungated and also runs for the `fransbot` donor,
   beside `FransSupportPowerBotModule` (two owners for WC2 powers there). `PlugSpawnerBotModuleCA`
   is not loaded, so bots never place plugs.

### 7.4 The best-of merge order (supersedes §6)

> **2026-09-30:** the order and the state now live in [`AI_MASTER_PLAN.md`](AI_MASTER_PLAN.md) (§3 the queue, §1.2 the harvest pipeline). The list below remains the reasoning behind it.

Ordered by what the A/B says loses matches — fights — and every step is an A/B against the
current master on A Nuclear Winter (≥ 8 matches, both spawns):

1. **Now:** `ReinforceProtection` (round 5) and the repair double-owner fix.
2. **CA-1** arsenal tracker, harvesting `FransCombatIntel` (Claude).
3. **CA-2** siege + force preservation, harvesting `FransGroundDefendForcePreservationGuard` +
   `FransRiskModel` (DAWN), then CN topology for chokepoints.
4. **CA-3/CA-4** role mix, one blended squad manager, formation (NOVA).
5. **CA-5** air doctrine, harvesting `FransAirCommander` strike logic (EMBER).
6. Economy (`FransEconomicSaturation`), then islands/transports (Fransbot V1.29.31), SpecOps,
   naval — each only after the earlier steps stop losing fights.
7. The `fransbot` bot type is deleted when nothing in it remains un-harvested or rejected.
