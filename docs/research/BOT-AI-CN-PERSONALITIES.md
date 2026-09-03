# Crystallized Nexus bot personalities — what they are, and what porting them to Cameo actually costs

Evidence base: `DoGyAUT/crystallized-nexus` @ `30cf70a` (2026-08-20, *"Move to engine cn-20260820 for the bot name fix"*),
cloned at `C:\Users\Administrator\repos\crystallized-nexus`. Mod SDK content lives under `.modsdk\`; the trait assembly is
`.modsdk\OpenRA.Mods.CN`, the AI rules are `.modsdk\mods\cn\rules\ai\`. License: GPLv3, same as Cameo — copying code is fine
with attribution.

Note: the old `DoGyAUT/cd` repo I used in the first comparison report is the *predecessor* (Crystallized Doom) and has none of
this. The AI work is all in the new repo, and it is the single most developed bot codebase of any mod surveyed.

## 1. What CN's personality system is

Five fixed strategic profiles plus an adaptive one, exposed as **selectable bots in the lobby**:

```
mods\cn\rules\ai\bots.yaml
  ModularBot@bot-cn-ai        Type: cn             -> CNBotProfileBotModule@adaptive   Profile: Adaptive
  ModularBot@bot-cn-rush      Type: cn-rush        -> CNBotProfileBotModule@rush       Profile: Rush
  ModularBot@bot-cn-turtle    Type: cn-turtle      -> ...                              Profile: Turtle
  ModularBot@bot-cn-tech      Type: cn-tech        -> ...                              Profile: Tech
  ModularBot@bot-cn-expansion Type: cn-expansion   -> ...                              Profile: Expansion
  ModularBot@bot-cn-steamroller Type: cn-steamroller -> ...                            Profile: Steamroller
```

A profile is two things:

1. **A budget split.** Each profile names four percentages — expansion / tech / defense / production — plus a harvester
   target multiplier and per-profile tech-stage timings (`MidTechTicks`, `LateTechTicks`). Rush is 12/8/8/42; Turtle is
   30/14/42/14; Steamroller is 12/10/8/70. Difficulty is a *separate* axis: `TechBudgetDifficultyScale` and
   `TechTickDifficultyScale` scale those numbers per handicap tier (Easy 70 % / Normal 100 % / Hard 130 % / Brutal 160 %).
2. **A condition that swaps whole module instances.** `CNBotProfileBotModule` grants `cn-profile-<name>`, and each
   personality has its own `CNSquadManagerBotModule` instance gated on it:
   `RequiresCondition: enable-cn-rush || cn-profile-rush` — one ~15 KB file per profile
   (`squads-rush.yaml`, `squads-turtle.yaml`, `squads-tech.yaml`, `squads-expansion.yaml`, `squads-steamroller.yaml`).

The adaptive profile scores all five every `AdaptiveSwitchCooldownTicks` (1500) against live game state — danger score,
army size relative to its own rush threshold, cash *trend* per minute, tech stage, count of enemy emplacements it has
personally seen, and what its allied bots are doing — with momentum hysteresis so it doesn't oscillate, plus an emergency
path that can flip to Turtle off-cadence when it's being attacked hard. Team coordination is explicit: bots are pushed
apart onto different profiles (`TeamAdaptiveCoverageWeight`), the most-threatened bot on a team is nudged into Turtle and
the safest into Steamroller/Tech.

Worth reading the `[Desc]`s in `CNBotProfileBotModule.cs` before designing our own: they record measured failures of
earlier tunings (Tech was never once chosen at its original weight; Steamroller's absolute army threshold was
unreachable; the danger threshold was on a scale that no longer existed, making profile choice a readout of one number).
That's a free list of the mistakes this design invites.

## 2. Why it is not a drop-in port

The budget snapshot is only worth anything if something spends it. In CN, four modules read `CurrentStrategy` /
`ActiveProfile`: `CNBaseBuilderBotModule` (23 references), `CNUnitBuilderBotModule` (7), `CNHarvesterBotModule` (3),
`CNMcvExpansionManagerBotModule` (3). All four are CN forks. Cameo's equivalents are the CA/engine modules
(`BaseBuilderBotModuleCA`, `UnitBuilderBotModuleCA`, `HarvesterBotModuleCA`, `McvExpansionManagerBotModule`) and they have
no budget concept at all.

So porting `CNBotProfileBotModule` alone gets us a trait that computes a strategy nobody consumes. Taking the consumers
too means replacing Cameo's entire bot stack — including its squad manager, since CN's is a different design (squad
templates with roles/tags, `NeedRules` keyed on enemy capabilities, staged attack waves) rather than a tuning of CA's.

Two further CN pieces need *engine* changes, so they can't be lifted as-is either:

- `BotPlayerNames` (deterministic faction-flavoured bot names) implements `IResolvePlayerName`, which does not exist in
  our engine fork — CN added it to theirs.
- `CNHandicapTiers` + the four `CNHandicap*Multiplier` traits assume the lobby handicap is four named tiers. Ours is
  stock OpenRA's 0–95 % in 5 % steps (`LobbyUtils.ShowHandicapDropDown`).

## 3. What I'd actually build for Cameo

The transplantable part is the **architecture**, not the code: personality = a condition, and each personality gets its
own instance of the bot modules we already ship. Cameo's CA modules already expose the knobs a personality needs —
`SquadSize`, `SquadValue`, `RushInterval`, `MinimumAttackForceDelay`, `MaxIdleUnits`, `JoinGuerrilla`,
`Min/MaximumDefenseRadius`, `PlaceDefenseTowardsEnemyChance`, `BaseCrawlChance`, `RefineriesPerBase`,
`ExpansionTolerate`, `NewProductionCashThreshold`, and the per-queue `BuildingIntervals`. No C# is required for fixed
personalities.

Tier 1 — **fixed personalities, YAML only.** Duplicate `SquadManagerBotModuleCA` (and optionally
`BaseBuilderBotModuleCA` / `UnitBuilderBotModuleCA`) once per personality with different tuning, gated on a personality
condition. Cost is data, not code, and the honest downside is duplication: each instance needs its own copy of the long
actor-type lists (`ConstructionYardTypes`, `AirUnitsTypes`, …), because YAML inheritance keys on the trait suffix and
can't share field values between two live instances. CN pays exactly this cost — 5 × ~15 KB.

Tier 2 — **how a personality gets chosen.** Two options, and this is the one real design decision:
  - *New bot types* (CN's way): `ModularBot@RushAI` etc. But Cameo's bot type **is** its difficulty — we ship ten, from
    Easiest to CameoGod — so a personality axis multiplies the lobby list (10 × 5 = 50 entries). Unacceptable as-is;
    it'd mean personalities only at selected difficulties.
  - *Random personality per bot per match*: keep the ten difficulty bots, and have each bot draw a personality at game
    start from `World.SharedRandom` (sync-safe). Needs one small new trait, ~60 lines, modelled on
    `GrantConditionOnBotOwnerCA` — we have no random-condition trait today. This keeps the lobby unchanged and makes
    repeat matches vary, which I think is the better fit for Cameo.

Tier 3 — **adaptive switching.** Only worth it after Tier 1/2 exist, and only in a Cameo-native form: score the
personalities from data our modules already have rather than porting CN's readers. Real work, and it should be judged
after we see whether fixed personalities feel different in play.

## 4. CN's other AI modules (not personalities, but from the same stack)

| module | what it does | portability |
|---|---|---|
| `CNTacticalMapBotModule` | Cartographs chokepoints (bridges, cliff ramps, narrow passages) and high-ground edges from the hierarchical pathfinder's abstract graph, once per match | high value, deep engine coupling |
| `CNRegionManagerBotModule` | Tracks which map regions the bot holds and what each is for; reads the shared region graph | depends on the above |
| `CombatAnalysisBotModule` | Per-role threat weights and a "nemesis" player from observed enemy attack patterns | fairly self-contained; feeds base builder + squads |
| `CNGarrisonBotModule` | Fills own garrisonable buildings with idle infantry, matching specialization to local threat, swapping mismatches out | needs a garrison capability tag; Cameo has `LoadGarrisonerBotModuleCA` already |
| `CNBridgeRepairBotModule` | Sends engineers into damaged bridge huts, requests replacements | small, self-contained |
| `CNRepairManagerBotModule` | Sends damaged idle base units to repair facilities | small, self-contained |
| `CNCliffDemolitionBotModule` | Shoots destroyable cliffs open to join up its own ground or open a new attack lane | needs CN's destroyable-cliff terrain system |
| `CNVeinholeAssaultBotModule` | Force-fires veinholes down, gated by faction doctrine | TS-specific; needs veins |
| `CNBotLog` / `CNBotPerf` | Per-module bot logging and per-tick perf sampling | small, and it's what let them tune the above honestly |
| `BotPlayerNames` | Deterministic faction-specific bot names + bot-type labels | needs engine `IResolvePlayerName` |
| `CNHandicapTiers` + 4 multipliers | Named handicap tiers (Easy/Normal/Hard/Brutal) scaling damage, firepower, income, production time | needs engine lobby change |

`CNBotLog`/`CNBotPerf` deserve a mention out of proportion to their size: every tuning claim in CN's `[Desc]`s cites
measurements over 50–200 evaluations, which is only possible because the instrumentation exists.
