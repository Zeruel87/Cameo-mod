# F2 part 2 inventory: upstream CA bot-module commits vs Cameo (read-only research, 2026-10-01)

Upstream = `C:/Users/AedisToru/Documents/GitHub/CAmod` (HEAD f31049d2d, 2026-09-14). Cameo = `OpenRA.Mods.CA/` on master 62547b159.
All Cameo cites are `OpenRA.Mods.CA/Traits/BotModules/...` unless a full path is given. Dates are the upstream AUTHOR dates from
`git log` (they differ by a few days from the dates in the task text: "indirect routes" is 2026-01-31, "harasser squads" 2026-02-03,
"Updated AI routing" 2026-02-06, "Compositions" 2026-02-08, "AI tweaks" 2026-02-12).
`audit_ca_drift` reports Cameo's SquadManager/Ground/Air/Navy/Protection/StateBase/SquadCA/BaseBuilder/QueueManager as
MODIFIED+STALE and Cameo's UnitBuilder/UnitCompositions/Harvester as MODIFIED with base_date 2026-02/04/08 (i.e. those three were
already re-synced past the upstream commits). Raw drift JSON: `<scratchpad>/ca_drift.json`.

HEADLINE: roughly 60 percent of the Feb-2026 work is already in Cameo (compositions, squad-value ramp, harasser squads, indirect/harass
routes, EnabledChance, BaseBuilder rally staggering, Harvester rewrite, BuildingRepair fix). What is genuinely MISSING is small:
air limits (71754fc06), air targeting by armor type (162f00bb6), the repairable-building preference, harass route start from the
nearest own building, a few state-machine details, and the debug overlay. The big b831676de mainline-squad refactor is SUPERSEDED
by Cameo's own pathfind-leader / fog / budget machinery and should NOT be ported wholesale.

## 1. Upstream commits (BotModules, after 2025-07-02, plus the two earlier air ones)

| hash | date | subject | BotModules files touched |
|---|---|---|---|
| b831676de | 2025-08-10 | AI updates | BaseBuilderBotModuleCA, BaseBuilderQueueManagerCA, HarvesterBotModuleCA, SquadManagerBotModuleCA, SquadCA, AirStatesCA, GroundStatesCA, NavyStatesCA, ProtectionStatesCA, StateBaseCA, UnitBuilderBotModuleCA (11 files, +1039/-510) |
| ea1b85108 | 2025-12-07 | Clean up trait lookups | BuildingRepairBotModuleCA |
| 71754fc06 | 2026-01-01 | Fix AI aircraft limits | AirStatesCA, UnitBuilderBotModuleCA |
| cdafd6c20 | 2026-01-09 | Remove bot debugging | UnitBuilderBotModuleCA (3 lines) |
| 9a68fea15 | 2026-01-31 | Skirmish AI indirect routes of attack | SquadManager, SquadCA, StateMachineCA, GroundStatesCA, ProtectionStatesCA, StateBaseCA (+empty HarrasserStates.cs) |
| 55e042954 | 2026-02-03 | AI harasser squads | SquadManager, SquadCA, GroundStatesCA |
| 461dde736 | 2026-02-04 | (V3/Ukraine yaml) | GroundStatesCA 4 lines (an unused-using cleanup) |
| 2bad89a77 | 2026-02-06 | Updated AI routing | SquadManager, SquadCA, GroundStatesCA, StateBaseCA |
| d3b5e8887 | 2026-02-08 | Compositions | SquadManager, GroundStatesCA, UnitBuilderBotModuleCA (+257), NEW UnitCompositionsBotModule.cs |
| 4e00d215b | 2026-02-09 | (IFV/Peacemaker) AI tweaks | SquadManager (value-ramp rename), UnitBuilder (field rename) |
| 1156c4eb3 | 2026-02-12 | AI tweaks | UnitBuilder (MaxCompositionSelectInterval 1500->7500, possibleActiveCompositions), UnitCompositions (EnabledChance) |
| b4f1f7c3a | 2026-02-12 | Yaml fix | UnitCompositions (non-Buildable unit: throw -> continue) |
| 22508a52e | 2026-02-20 | Mission crash fix (UnitCompositions) | UnitCompositions (`Composition` field "to suppress errors") |
| 0a863cc8e | 2026-04-23 | Fix bot crash (Naval AI) | UnitBuilder (null guard in AddToActiveCompositionProducedValue) |
| cb00e65f7 | 2026-07-26 | Fix AI not repairing buildings | BuildingRepairBotModuleCA |
| 356e0301a | 2025-06-07 | Engine update fixes part 2 | BEFORE the 2025-07-02 cutoff; deleted upstream CaptureManagerBotModuleCA, touched MCV/PowerDown/Navy/UnitBuilder/BaseBuilder. Listed for completeness (audit shows MCVManager/PowerDown 2025-07-02 base, CaptureManager = MOVED/REMOVED; Cameo keeps its own capture manager under the DESIGN 19.5 fog exception). |
| 162f00bb6 | 2025-05-26 | Skirmish AI aircraft target by armor type | SquadManager, AirStatesCA, mods/ca/rules/ai.yaml (124 lines) |
| e57ef1d39 | 2025-03-31 | AI air attacks by armor type or target type | NOT a bot-module commit (PlayerCAProperties.cs + campaign.lua only). Scripting, N/A to the bots. |

No BotModules commit exists upstream between 2026-07-26 and HEAD (2026-09-14).

## 2. Per-hunk inventory

Status: PORTED / PARTIAL / MISSING / SUPERSEDED / N/A.

| commit | file / function | status | Cameo cite | notes |
|---|---|---|---|---|
| 9a68fea15 | SquadManager `IndirectRouteChance` (default 50) | PORTED | SquadManagerBotModuleCA.cs:405 (default 0) | Cameo defaults to 0 in C#, but `mods/cameo/ai/ai.yaml:3566,3625,3684,3743,3802,3861,3933` set 30/60 on the tiers, so it is LIVE on master. |
| 9a68fea15 | SquadCA `GetLeader()/NewLeader()/LeaderLocomotor` (min-terrain-speeds locomotor, min speed, centre unit) | SUPERSEDED | Squads/States/StateBaseCA.cs:301 `GetPathfindLeader(squad, locomotorTypes)`; Info `SuggestedGroundLeaderLocomotor` (SquadManager:399), `SuggestedNavyLeaderLocomotor` (:402); wrapper type `UnitWposWrapper` (SquadCA.cs:23) | Different mechanism, same job (pick a leader every unit can follow). Cameo is yaml-configured by locomotor name; upstream auto-derives from TerrainSpeeds.Count. Not worth porting. |
| 9a68fea15 | `StateMachineCA.CurrentState` getter | PORTED | Squads/StateMachineCA.cs:18 | file IDENTICAL to upstream (drift audit). |
| 9a68fea15 | `SquadRouteInfo` class + `GroundUnitsAttackMoveStateCA.GetRouteInfo()`; `GroundStateBaseCA`/`StateBaseCA` made `public` | MISSING | n/a (Cameo AttackMove state is internal, route fields at GroundStatesCA.cs:300-304) | Exists only to feed upstream `Traits/SquadPathOverlay.cs` (debug overlay, section 3 pack P7). No gameplay effect. |
| 9a68fea15 | AttackMove state: compute `FindDistinctRoutes`, pick random non-direct route, follow waypoints (<16 sq cells or 250-tick timeout) | PORTED (own style) | Squads/States/GroundStatesCA.cs:528-595 (compute on target change `lastRoutingTarget`, waypoint advance :581-589 with 625-tick timeout, `routeTarget` :592) | Cameo adds 6e `RouteAroundThreat` first (:541) and a remembered-threat router; the leader is a `UnitWposWrapper`. Upstream follows a route only if `currentRoute.Count > 2`; Cameo `> 1` (:592). Minor. |
| 9a68fea15 | skip straggler regroup while following a route; regroup AttackMove for stragglers | SUPERSEDED | GroundStatesCA.cs:430-520 (leader waits `leaderWaitCheck`, `unitsHurryUp` AttackMove :618-619, makeWay/kickStuck) | Cameo has the older CA pathfind-leader stuck machinery which upstream deleted in the mainline refactor. Keep Cameo's. |
| 9a68fea15 | idle-drop timeout 63 -> 100 ticks ("4 seconds") in AttackMove and Attack states | MISSING (Attack state) / SUPERSEDED (AttackMove) | GroundStatesCA.cs:831 still `+ 63` in `GroundUnitsAttackState`; AttackMove uses stuck-kick instead | 1-token change, but it changes squad abandonment timing; ship behind a switch (WP-A5). |
| 9a68fea15 | `ProtectionStatesCA` uses `owner.GetLeader()` | N/A | n/a | consequence of the leader refactor. |
| 55e042954 | `HarasserTypes` Info + `SquadCAType.Harass` + FindNewUnits wiring | PORTED | SquadManager.cs:202 (`HarasserTypes`), :1527 `AddToHarassSquad`, :1550, :2162; SquadCA.cs:19,67 | Cameo also adds `HarassMinLaunchSize` (:205), `HarassRouteCount` (:209), `HarassPriorityTags` (:338): not upstream, Cameo-only knobs. |
| 55e042954 | `HarasserUnitsIdleStateCA` (quorum roll 3 units 5 pct, 4 units 10 pct, 5+ always) | PORTED (generalised) | GroundStatesCA.cs:979-1015 `ShouldHarass(count, minSize, roll)` | Same table shifted by `HarassMinLaunchSize`. Adds risk-gated HV retarget. |
| 55e042954 | Harass: `NewLeaderAndFindClosestEnemy(owner, highValueCheck: Harass)` | PORTED | GroundStatesCA.cs:325 (`FindNewTarget(owner, highValueCheck: true, riskCheck: true)` for Harass) | |
| 55e042954 | Harass: route start = closest FRIENDLY BUILDING to target (else leader); `friendlyBuildings = World.Actors.Where(own && BuildingInfo)` | MISSING | Cameo starts the route at `leader.Actor.Location` (GroundStatesCA.cs:562) | In 2bad89a77 this was extended to all squad types and to `RepairableBuildingInfo` plus the leader as candidates. Needs an own-building source that does NOT add a `World.Actors` site (see risks, WP-A3). |
| 2bad89a77 | `SquadValueRandomEarlyBonus/LateBonus` (later renamed in 4e00d215b to `SquadValueMaxEarlyBonus/MinLateBonus/MaxLateBonus`) | PORTED | SquadManager.cs:256-262, validation :425-433, `SetNextDesiredAttackForce` :2407-2430 | Cameo ALSO keeps legacy `SquadValueRandomBonus` (:253) and refuses to combine them. |
| 2bad89a77 | `cachedUnitValues` for idle value sum | PORTED | SquadManager.cs:554, :1357, :1904, :2196 | |
| 2bad89a77 | Remove `SquadSize`/`SquadSizeRandomBonus` and the `desiredAttackForceSize` gate (value-only) | MISSING (deliberately?) | Cameo keeps `SquadSize` (SquadManager.cs:63), `desiredAttackForceSize` (:552, gate at :2206, set at :2407) | Behaviour decision: upstream attack force launches on value alone. Needs a ruling; if wanted: `UseValueOnlyAttackForce` switch (WP-A5). Likely N/A because Cameo yaml tunes both. |
| 2bad89a77 | `IsPreferredEnemyBuilding`: `BuildingInfo` -> `RepairableBuildingInfo` | MISSING | SquadManager.cs:656 (`HasTraitInfo<BuildingInfo>`) | Stops squads target-locking walls/non-repairable decoration. One token. Cameo walls/fences rely on BuildingInfo today, so measure first (WP-A5). |
| 2bad89a77 | SquadCA: `leastCommonDenominator` locomotor filter commented out ("not really necessary for CA") | N/A | n/a | refers to upstream GetLeader only. |
| 2bad89a77 | AttackMove: opportunity-target pre-check; routes computed from `ClosestToIgnoringPath(ownBuildings + leader, target)`; harass uses `maxRoutes=10`(12 in d3b5e8887), others 7 if indirect roll else 2; excl. direct route when `maxRoutes>2` | PARTIAL | GroundStatesCA.cs:545-575 (Harass: `HarassRouteCount`, last 2 routes :564; Guerrilla 3; indirect 7, skip first :566) | Only the route START (own building) is missing. |
| 2bad89a77 | Attack state: when target invalid, grab opportunity target in AttackScanRadius else go to AttackMove state (instead of re-target + Flee) | MISSING | GroundStatesCA.cs:816-822 (`!IsTargetValid && !FindNewTarget -> Flee`) | Behaviour change (fewer flee/idle cycles). WP-A5. |
| 2bad89a77 | `StateBaseCA.GoToRandomOwnBuilding`: `Move` -> `AttackMove` | MISSING | Squads/States/StateBaseCA.cs:27 (`new Order("Move", ...)`) | 1 word. Retreating squads would shoot on the way home. WP-A5. |
| d3b5e8887 | SquadManager `cachedUnitValues` tidy | PORTED | SquadManager.cs:1357 | |
| d3b5e8887 | GroundStates `useIndirectRoutes` flag, harass picks randomly among the LAST 2 routes | PORTED | GroundStatesCA.cs:545,561-567 | |
| d3b5e8887 | `UnitBuilderBotModuleCA` compositions (UseCompositions, Min/MaxCompositionSelectInterval, baseline, ChooseActiveComposition, interval/time/prereq checks, MaxDuration/MaxProducedValue, save/load CompositionLastUsed) | PORTED | UnitBuilderBotModuleCA.cs:77-99 (Info), :112-191, :249 `UpdateComposition`, :343,362; `ActiveCompositionId` + event :119-120 (Cameo-only, match log) | Cameo default `UseCompositions = false` (:79, upstream true) and NO composition blocks in `mods/cameo/ai/*.yaml` (grep: none) so it ships inert. Cameo-only `IBotEnemyCompositionProvider` (:145,170). |
| d3b5e8887 | NEW `UnitCompositionsBotModule.cs` | PORTED | Traits/BotModules/UnitCompositionsBotModule.cs (drift: MODIFIED 7 lines) | Cameo uses `TryGetValue` (:97) instead of the indexer, `.ToArray()` on prereqs; carries b4f1f7c3a / 22508a52e fixes. |
| 4e00d215b | value-ramp rename; `compositions` -> `compositionsModule` | PORTED | SquadManager.cs:256-262; UnitBuilder.cs:127 | |
| 1156c4eb3 | `MaxCompositionSelectInterval` 7500, `possibleActiveCompositions`, `EnabledChance` | PORTED | UnitBuilder.cs:85,128,183-188; UnitCompositionsBotModule.cs:42 | |
| b4f1f7c3a / 22508a52e / 0a863cc8e | non-Buildable composition unit -> skip; `Composition` suppress field; null-guard in `AddToActiveCompositionProducedValue` | PORTED | UnitCompositionsBotModule.cs:70,96-100; UnitBuilder.cs:776-779 | |
| cb00e65f7 / ea1b85108 | BuildingRepair: look up `RepairableBuilding` per damaged building (cached copy on the Player actor left the module inert) | PORTED | BuildingRepairBotModuleCA.cs:~35-48 (explicit comment) | Cameo also null-guards `e.Attacker`. |
| 71754fc06 | `CanBuildMoreOfAircraft`: count QUEUED aircraft (own + allied queues), split air-to-air vs non-air-to-air, `AirToAirUnits` limit uses allied A2A count + queue, enemy `AirThreatUnits` count, `MaxAirSuperiority` cap | MISSING | UnitBuilderBotModuleCA.cs:793-820 (old logic, no queue counting; `numFriendlyAirToAirUnits` etc.) | Real bug upstream: AI over-built aircraft because queued ones were not counted. WP-A1. |
| 71754fc06 | AirStates: evaluate `canBuildMoreOfAircraft` lazily AFTER the unit loop (`Func<bool>`), `firstUnit` computed after loop; condition `(noPatience \|\| !canBuild())` | MISSING | Squads/States/AirStatesCA.cs:395-411 (eager, before loop, `Owner.SquadManager.CanBuildMoreOfAircraft` every tick), :495 | WP-A1. Also removes a per-tick scan. |
| cdafd6c20 | remove `TextNotificationsManager.Debug` line from CanBuildMoreOfAircraft | N/A | n/a | Cameo never had the debug line; do not add it. |
| 162f00bb6 | `AirSquadTargetTypes` (TargetableType BitSet) -> `AirSquadTargetArmorTypes` (armor names via `ArmorInfo.Type`), `IsAirSquadTargetType` -> `IsAirSquadTargetArmorType` | MISSING | SquadManager.cs:390 (`AirSquadTargetTypes`), :669 `IsAirSquadTargetType`; callers AirStatesCA.cs:136,286,370; AirDoctrineStatesCA.cs:81,207,266 | Upstream picks air targets by the armor class the weapon is good against. Cameo yaml uses `AirSquadTargetTypes` in many ContentPack ai.yaml (`mods/cameo/ai/ai.yaml` + about 10 ContentPacks), keyed by Cameo unit ids, so a yaml translation is needed. WP-A2. |
| b831676de | SquadManager: `FindEnemies`/`ClosestTo` with weapon-range reachable OFFSETS (`(Actor, WVec)` targets, 9-point range ring pathing check) | SUPERSEDED / PARTIAL | `FindClosestEnemy(Actor, SquadCA)` SquadManager.cs:1264-1300 (+risk-gated overload :1306), `CheckReachability(Actor, CPos)` StateBaseCA.cs:339, reachability gate GroundStatesCA.cs:319 / NavyStatesCA.cs:141 | Cameo's targeting is memory/fog/risk-gated and tag-preferring; it has NO offset target for units that can shoot from range but not reach the cell (ships vs inland, artillery). That one capability is MISSING (WP-A6, optional, large). |
| b831676de | `FindClosestEnemy` prefers closest BUILDING first ("CA: Prioritize buildings over other enemy units") | MISSING | SquadManager.cs:1274-1275 (visible units closest first, buildings only as non-fogged fallback) | Real behavioural difference. Cameo's `PreferSquadTargets` (tags) shapes it instead. Needs maintainer ruling; DO NOT port without A/B. |
| b831676de | `IsValidEnemyUnit` folds in `IsNotHiddenUnit`; `IsNotHiddenUnit` via `IVisibilityModifier` | SUPERSEDED | SquadManager.cs:1104 `IsPreferredObservedEnemyUnit`, :693 `IsNotHiddenUnit` (`CanBeViewedByPlayer`), `FoggedScans` :1135 | Cameo fog model is stricter (frozen-actor memory). |
| b831676de | `squadsPendingUpdate` stack: spread squad updates over ticks | SUPERSEDED | SquadManager.cs:1956-1982 (`IBotActionBudget` attention budget + `squadCursor` rotation) | Same PERF goal. |
| b831676de | `constructionYardBuildings` ActorIndex, `UnregisterSquad`, `INotifyActorDisposing` | PORTED / SUPERSEDED | SquadManager.cs:500,595,2590 (`OwnerAndNamesAndTrait`); Cameo has `DismissSquad` :1876 | |
| b831676de | `ProtectionTypes`, `AircraftTargetType` (unused upstream), `RushInterval`/`RushAttackScanRadius` (unused upstream) | PORTED / N/A | `ProtectionTypes` SquadManager.cs:59; the other three are dead fields upstream (grep HEAD: declared, never read) | skip the dead ones. |
| b831676de | SquadCA: `Units` List -> `HashSet`, `Target` as `(Actor,Offset)`, `IsTargetValid(squadUnit)` re-resolving reachable offset, serialization `ActorToTarget`/`TargetOffset`, `CenterUnit()`, `CenterPosition()` | SUPERSEDED | SquadCA.cs:23 `List<UnitWposWrapper> Units`, :126 `IsTargetValid`, `Serialize` | Pervasive; Cameo has its own save format. Do not port. |
| b831676de | StateBase `ShouldFlee`: scan around squad CENTER not a random unit; `IsRearming` via `ActivitiesImplementing<Resupply/ReturnToBase>` | PARTIAL | StateBaseCA.cs:150-176 (`ShouldFleeSimple` around `Units[0]`; uses observed-enemy), `IsRearming` :178-198 (checks only current + next activity) | The `IsRearming` deep-chain fix is a 1-line gain (WP-A4); centre-of-squad scan is N/A to Cameo's `ShouldFlee` variants (CombatPredictor). |
| b831676de | AirStates: `Where(IsPreferredEnemyUnit).ToList()`, `leader = owner.CenterUnit()`, drop `continue` after Attack order | PARTIAL | AirStatesCA.cs:286, :395 | The `continue` removal means a unit that was just ordered to attack is no longer added to Rearming/Waiting bookkeeping the same tick. Tiny; fold into WP-A1. |
| b831676de | NavyStates: `FindClosestEnemy(first).Actor`, `CenterUnit()` leaders | SUPERSEDED | NavyStatesCA.cs:88,139 (pathfind leader) | |
| b831676de | ProtectionStates: `owner.Target` + leader based | SUPERSEDED | ProtectionStatesCA.cs (uses `IBotProtectionRequestProvider`, :53) | |
| b831676de | BaseBuilder: `AssignRallyPointsInterval` + `Stack<TraitPair<RallyPoint>>` staggered rally assignment, `LocomotorsForProducibles`, `IsRallyPointValid` (path + buildable), `IBotRequestPauseUnitProduction` (`!HasAdequateRefineryCount()`), ActorIndex building sets, `GetMinCashRequirement` | PORTED | BaseBuilderBotModuleCA.cs:175,325,411,453-470,653-725,426 (`HasMinimalRefineryCount`), :342-366 | Cameo is AHEAD (opening, expansion, refinery planner). |
| b831676de | QueueManager: `Tick(IBot, ILookup queuesByCategory)`, `GetCashAndResources()`, `HasAdequateRefineryCount()` call | PARTIAL | BotModuleLogic/BaseBuilderQueueManagerCA.cs:100 (`Tick(IBot)`), :197 `AIUtils.FindQueues(player, Category)` per tick; `GetCashAndResources` :226,353,401; `HasAdequateRefineryCount()` :454 | The cached `queuesByCategory` is a PERF-only item (BaseBuilderBotModuleCA.cs:529 and :861 and UnitBuilder :267/:285/:320/:385 also use `FindQueues`). Optional WP-A7. |
| b831676de | UnitBuilder: `queuesByCategory`, `BuildRandomUnit`, share-error unit selection (`desiredError`), `ActorIndex.OwnerAndNames unitsToBuild`, min-cash gate hoisted to top of BotTick | SUPERSEDED / PARTIAL | UnitBuilderBotModuleCA.cs:249-330, :434-460 (`ChooseRandomUnitToBuild` uses `unitsToBuildShares` + `unitsToBuild` index :124,191), cash gate :296 | Cameo is already on the index + share model, plus counter-production / role-mix. Only the `FindQueuesByCategory` caching is missing (WP-A7). |
| b831676de | Harvester rewrite (stack of harvesters needing orders, one FindNextResource per tick, `resourceTypesByCell`, `NoResourcesCooldown`, `ScanIntervalMultiplerWhenNoResources`, binned enemy-avoidance cost) | PORTED | HarvesterBotModuleCA.cs:47,59,79,95-98,157-169,196,231,404-419,427-470 | NB `ActorsInBox` enemy scan at :456 is an omniscient read in the avoidance cost (identical upstream); already counted in `fog_honesty_manifest.json` presumably. Verify before touching. |
| 356e0301a (pre-cutoff) | engine-update fixes (CaptureManager removed upstream) | N/A | CaptureManagerBotModuleCA.cs kept (MOVED/REMOVED in audit) | Cameo keeps its own, fog exception DESIGN 19.5. |
| 9a68fea15 | NEW upstream `Traits/SquadPathOverlay.cs` (143 lines, `IRenderAnnotations` + `IChatCommand` `/squadpaths`, world trait in `mods/ca/rules/world.yaml:445`) | MISSING | none | Debug overlay. Needs `SquadRouteInfo`/`GetRouteInfo` + public state classes. See WP-A7. |

## 3. MISSING / PARTIAL work packages (proposed ports)

Order = value / risk. Every package must ship DEFAULT-OFF behind a switch added to `tools/ai/increment_switches.yaml` under a new group
(suggest `F_ca_f2p2`), with the C# field defaulting to the OLD behaviour so master is unchanged until the increment A/B.

### WP-A1 Air limits fix (71754fc06)  -- highest value
- What: `CanBuildMoreOfAircraft` counts aircraft already in production queues and treats air-to-air vs other aircraft as separate pools; AirStates stops calling the limit check before the loop on every tick and short-circuits it.
- Upstream: `UnitBuilderBotModuleCA.CanBuildMoreOfAircraft` (UnitBuilder ~302-368 at 71754fc06), `AirStatesCA.Tick` (~230-310).
- Cameo sites: `UnitBuilderBotModuleCA.cs:793-820`, `Squads/States/AirStatesCA.cs:395-411,495`. Also `SquadManagerBotModuleCA.CanBuildMoreOfAircraft` :2576 (passthrough, unchanged).
- Size: about 75 lines in UnitBuilder, about 25 in AirStates.
- Dependencies: `AIUtils.FindQueuesByCategory(IEnumerable<Player>)` (engine OpenRA.Mods.Common; Cameo already uses the `Player` overload at UnitBuilder.cs:674), `ProductionQueue.AllQueued()`. No new Info fields. No yaml. `Info.MaxAircraft/MaintainAirSuperiority/AirToAirUnits/AirThreatUnits/MaxAirSuperiority` all exist (UnitBuilder.cs:57-75).
- Risks: (a) FOG: the upstream code (and Cameo's current code) counts `player.World.Actors` where `Owner` is Enemy and name in `AirThreatUnits` (omniscient read of enemy composition). Do it through observed memory: Cameo already has `IBotEnemyCompositionProvider` (UnitBuilder.cs:145,170,221) which the port should use for the enemy-air count, falling back to the old call only under `classic`. A new `World.Actors` site raises the `fog_honesty_manifest.json` count and FAILS `audit_fog_honesty.py`, so use `AIUtils.GetActorsWithTrait`/ActorIndex for OWN aircraft. (b) orders only: no mutation, fine. (c) none. (d) switch.
- Switch: `UnitBuilderBotModuleCA.CountQueuedAircraft` (bool, default false) and `AirSquadsLazyLimitCheck` shares it. Group `F_ca_f2p2`.

### WP-A2 Air targeting by armor type (162f00bb6)
- What: air squads choose targets whose ARMOR class matches the aircraft's per-type list instead of targetable-type overlap.
- Upstream: `SquadManagerBotModuleCA.IsAirSquadTargetArmorType`, Info `AirSquadTargetArmorTypes: Dictionary<string, BitSet<TargetableType>>` (key actor id, value armor type names, compared as strings via `ArmorInfo.Type`), AirStates call sites; the yaml at `mods/ca/rules/ai.yaml:2208,2336,2464`.
- Cameo sites: `SquadManagerBotModuleCA.cs:390,669-685`; `AirStatesCA.cs:136,286,370`; `AirDoctrineStatesCA.cs:81,207,266` (Cameo-only doctrine states that also call the old predicate: update all three).
- Size: 15 lines C#, plus yaml translation. The CODE is trivial; the yaml is the work: each Cameo aircraft in about 11 `ai.yaml` files (`mods/cameo/ai/ai.yaml`, ContentPacks D2k/RedAlert/RedAlert2/...) needs an armor list in Cameo's armor vocabulary (the 13-slot axis, DESIGN 12.0i). Do NOT translate CA names (Heavy/Light/Wood/Concrete): Cameo armor ids differ.
- Dependencies: none new in C#. Yaml: new key `AirSquadTargetArmorTypes`.
- Risks: (a) the new predicate reads `a.Info.TraitInfos<ArmorInfo>()` of a candidate the caller has already filtered with `IsPreferredEnemyUnit`/observed; static rules data, not a world scan: fog-safe. Keep the callers' existing observed filters. (b),(c) none. (d) the new predicate applies only when a unit id has an `AirSquadTargetArmorTypes` entry; empty dict = old behaviour, so default-off is automatic. Ship C# first with NO yaml, then add yaml per faction in a separate A/B step.
- Switch: yaml-driven (empty by default). No code switch needed.

### WP-A3 Harass/indirect route start from nearest own building (2bad89a77)
- What: route planning starts at the own building closest to the target (or the leader if closer), so a flanking route is planned from base, not from wherever the squad is.
- Upstream: `GroundUnitsAttackMoveStateCA.Tick`, `startActor = WorldUtils.ClosestToIgnoringPath(friendlyBuildings.Concat(new[]{leader}), owner.TargetActor)`.
- Cameo site: `Squads/States/GroundStatesCA.cs:562` (`FindDistinctRoutes(..., leader.Actor.Location, ...)`). Note Cameo's route block also takes Guerrilla/Harass last-2 routes.
- Size: about 10 lines.
- Dependencies: need a list of own base buildings WITHOUT a new `World.Actors` site. Use `SquadManager`'s `constructionYardBuildings`/`BaseBuilder.ProductionBuildings` ActorIndex (public at BaseBuilderBotModuleCA.cs:344,347) via a new accessor on SquadManager; `WorldUtils.ClosestToIgnoringPath(IEnumerable<Actor>, Actor)` exists in engine (`engine/OpenRA.Game/WorldUtils.cs:26`).
- Risks: (a) own-actor read, honest, but `World.Actors` would still trip the manifest; use the index. Pathing from a far building can fail on islands: keep the leader as a candidate and fall back to leader when `FindDistinctRoutes` returns empty. (b) orders only: fine. (c) none. (d) switch.
- Switch: `SquadManagerBotModuleCAInfo.RouteFromNearestOwnBuilding` (bool, default false).

### WP-A4 Small state-machine fixes (batch)
All one-liners, each independently switchable only if you want them separate; recommend ONE switch `F_ca_f2p2.StateMachineTweaks`.
- (1) `IsRearming` deep chain: replace the current+next check at `StateBaseCA.cs:178-198` with `!a.IsIdle && a.CurrentActivity.ActivitiesImplementing<Resupply>().Any() || ...ReturnToBase`. Upstream `StateBaseCA.IsRearming` (b831676de). 1 line.
- (2) `GoToRandomOwnBuilding` `Move` -> `AttackMove` (`StateBaseCA.cs:27`; upstream 2bad89a77). 1 word.
- (3) `IsPreferredEnemyBuilding` `BuildingInfo` -> `RepairableBuildingInfo` (`SquadManagerBotModuleCA.cs:656`; upstream 2bad89a77). 1 token. RISK: Cameo walls, fences, decorative blockers lose their "building" status in squad targeting; measure with a rules scan first (which Cameo `BuildingInfo` actors lack `RepairableBuilding`).
- (4) Attack-state idle drop 63 -> 100 ticks (`GroundStatesCA.cs:831`; upstream 9a68fea15).
- (5) Attack state target-invalid path: opportunity target in `AttackScanRadius` else `AttackMove` state instead of Flee (`GroundStatesCA.cs:816-822`; upstream 2bad89a77 `GroundUnitsAttackState.Tick`). About 12 lines. Use `FindClosestEnemy(leader.Actor, WDist, owner)` (the existing observed overload) so it stays fog-honest.
- Risks: (a) none new if (5) uses the observed overload; (b),(c) none; (d) single switch `UseUpstreamStateTweaks` default false.

### WP-A5 Decisions that need a maintainer ruling BEFORE any code (do not port blind)
- Building-first targeting in `FindClosestEnemy` (upstream "CA: Prioritize buildings over other enemy units"). Cameo prefers closest VISIBLE unit and has `PreferSquadTargets`/tags. Behavioural, A/B-only. Switch if wanted: `SquadManagerBotModuleCA.PreferBuildingsFirst`.
- Value-only attack force (drop `SquadSize` gate, `SquadManager.cs:63,552,2206,2407`). Switch if wanted: `UseValueOnlyAttackForce`.
- Cameo default of `UseCompositions` (false) vs upstream true, and authoring composition yaml (Cameo has none).

### WP-A6 Weapon-range reachable-offset targeting (b831676de core) -- OPTIONAL, large
- What: `(Actor, WVec offset)` targets so ships/artillery pick targets they can hit from a reachable cell; `IsTargetValid(squadUnit)` re-resolves the offset each tick.
- Upstream: `SquadManagerBotModuleCA.FindEnemies`, `ClosestTo`, `FindClosestEnemy(Actor, bool)`, `SquadCA.SetActorToTarget/IsTargetValid/CenterUnit`, all state files.
- Cameo: would touch `SquadCA.Target`, 1300 lines of GroundStates, Navy, Air, Protection, the 6c/6d/6e fog + risk overloads and mission/lease code. Engine helpers already exist (`WithPathFrom`, `WithPathTo`, `ClosestToWithPathToAny`, `ClosestToWithPathFrom` in `engine/OpenRA.Mods.Common/WorldExtensions.cs:28-183`).
- Size: 600+ lines, high conflict. Recommend NOT porting; if a gap shows (ships idling vs inland targets) build a SHADOW helper `FindEnemiesReachableByRange` in a new Cameo file used only by `NavyStatesCA`, behind `NavalRangeTargeting` (default false). Risk (a) high: upstream `FindEnemies` takes `IEnumerable<Actor>` from `World.Actors`; the shadow must take the already-observed candidate list.

### WP-A7 Perf/debug extras -- LOW priority
- `queuesByCategory` caching (`AIUtils.FindQueuesByCategory(player)` once per tick, passed to `BaseBuilderQueueManagerCA.Tick(bot, queuesByCategory)` and UnitBuilder): sites BaseBuilderQueueManagerCA.cs:100,197; BaseBuilderBotModuleCA.cs:529,861; UnitBuilderBotModuleCA.cs:267,285,320,385. About 30 lines, pure perf, no behaviour change so no switch strictly required.
- `SquadPathOverlay` + `SquadRouteInfo`/`GetRouteInfo`/public state classes: about 143 + 25 lines; needs `IRenderAnnotations`, `IChatCommand`, a fluent key `description-squadpaths-debug-overlay` (underscores law: rename to `description_squadpaths_debug_overlay` if Cameo keys forbid hyphens, CLAUDE.md rule 9), world.yaml entry. Debug only; skip unless the maintainer wants route visualisation. Reads only the squad's own route list; honest.

Suggested sequencing: WP-A1 -> WP-A4 -> WP-A3 -> WP-A2 (C#) -> yaml for A2 -> optional A7. WP-A5 and A6 wait for rulings.
Total realistic port size: about 250 lines C# (A1 100, A2 15, A3 10, A4 30, A7 30+) plus per-faction yaml for A2.

## 4. The 9 non-bot CA files blocked at INC-4a

Source: `docs/HANDOFF.md:41`, commit 9cbbc49ae message. The 9 are the remaining `STALE` rows of `audit_ca_drift` (Cameo copy == upstream base, diff_lines 0, upstream newer): confirmed by `ca_drift.json`.

| # | file (Cameo path) | missing type / API | self-contained upstream file? | notes |
|---|---|---|---|---|
| 1 | `Traits/AttachOnCreation.cs` | new `AttachableTo.CanAttach(Attachable)` and `Attach(Actor, Attachable)` | no: tied to the Attachable cluster | cluster = Attachable.cs (535 lines upstream vs 223 Cameo), AttachableTo.cs (267 vs 183), AttachOnCreation, AttachOnTransform, InfiltrateToAttach |
| 2 | `Traits/AttachOnTransform.cs` | same + `INotifyAttachedTo` | same cluster | |
| 3 | `Traits/AttachableTo.cs` | `INotifyAttachedTo`, `INotifyExitedCargo/EnteredCargo`, `INotifyCenterPositionChanged`, `INotifySold`, `INotifyTransform` (engine interfaces exist; `INotifyAttachedTo` is a CA interface in `TraitsInterfaces.cs`, MISSING in Cameo) and a breaking yaml change: `Limits`/`LimitConditions` dictionaries become `Type` (required), `Limit`, `LimitBehaviour`, `AttachedCondition`, `LimitCondition` | cluster | Cameo yaml has ZERO uses of `AttachableTo`, `AttachOnCreation`, `AttachOnTransform`, `InfiltrateToAttach` (grep over `mods/`); only `DelayedWeaponAttachable` (ivan/plague/lockdown, `mods/cameo/rules/defaults.yaml:7073,7159`) which is a different trait. So vendoring the cluster is safe and no yaml migration is needed. |
| 4 | `Traits/Infiltration/InfiltrateToAttach.cs` | `AttachableTo.CanAttach`, `Attachable` | cluster | also new `PlayerExperience` field use (`PlayerExperience` trait exists in CA) |
| 5 | `Traits/PopControlled.cs` | `PopController` (new player trait, 88 lines, `Traits/Player/PopController.cs`) | YES: PopController is self-contained (uses `Passenger`, `PopControlled`, engine only) | PopControlled changes `Limit` -> `Type`, and the cull moves into the PopController `Limits` dictionary (player trait). Cameo yaml: only a commented `#PopControlled:` at `mods/cameo/rules/defaults.yaml:9040`, no live use: vendor PopController + PopControlled verbatim; add the player trait to the player template only if a unit later uses PopControlled. |
| 6 | `Traits/ProductionQueueFromSelectionCA.cs` | `LinkedProducerTarget` (346 lines) which pulls `LinkedProducerSource` (240) and `Effects/LinkedProducerIndicator` (138); engine `ProductionQueue.AnyItemsToBuild()` (EXISTS in `engine/OpenRA.Mods.Common/Traits/Player/ProductionQueue.cs`) | YES, as a 3-file set (`LinkedProducer{Source,Target}.cs`, `LinkedProducerIndicator.cs`) using only engine types (`Orders`, `Effects`, `Activities`) | new `AllySelection` field default false, so existing yaml (1 use) is unchanged. Compile to confirm. |
| 7 | `Traits/Render/WithColoredSelectionBox.cs` | `OpenRA.Mods.CA.Graphics.SelectionBoxAnnotationRenderableCA` (66 lines, `Graphics/SelectionBoxAnnotationRenderableCA.cs`, with `Thickness`) | YES: one 66-line file, engine-only deps | new fields `Thickness`, `Bounds`, `BoundsPadding`, `Interactable` instead of `Selectable`. Cameo yaml: 9 uses of WithColoredSelectionBox, no breakage since all new fields default to old behaviour. |
| 8 | `Traits/Modifiers/WithPalettedOverlay.cs` | `IActorPreviewRenderModifierInfo` / `IActorPreviewRenderModifier` (upstream `TraitsInterfaces.cs`: Cameo's copy lacks them, 3-line Cameo diff to hand-merge), `WithPalettedOverlayPreviewModifier` (defined in the same upstream file) | YES once the two interfaces are added to `TraitsInterfaces.cs` (upstream consumers are `ActorPreviewCAWidget`, `WithColoredOverlayCA`, `WithPreviewDecoration`: only the interfaces are required for this file to compile) | new `ValidRelationships`, `VisibleThroughFog`, `ShowInPreview` (default false). Cameo yaml: 0 uses. |
| 9 | `Traits/Player/LobbyPrerequisiteDropdown.cs` | `KeyCollection.ToHashSet()` | trivial: the only upstream change is deleting `using System.Linq;` (line 53 `Values.Keys.ToHashSet()` is identical in both). Upstream compiles it through its implicit usings; Cameo's csproj has no implicit `System.Linq` so the verbatim copy broke the build. | FIX: keep Cameo's `using System.Linq;` and take the Desc whitespace line only. No vendoring needed. |

Vendoring verdict: files 5, 6, 7, 8, 9 are low-risk (PopController 88 lines; LinkedProducer set 3 files; SelectionBoxAnnotationRenderableCA 66; interface add; a using). Files 1-4 are one cluster (Attachable 535 + AttachableTo 267 + 3 small files + `INotifyAttachedTo`): vendor the whole cluster verbatim together with the interface, nothing in Cameo yaml depends on the old Limits keys. Compile after each file group (`DOTNET_ROLL_FORWARD=LatestMajor dotnet build -c Release --nologo -p:TargetPlatform=win-x64`) and run the boot gate (CLAUDE.md rules 1, 7).
Note Cameo's Attachable.cs / AttachableTo.cs are "MODIFIED+STALE" in the drift table (Attachable 4 diff lines vs its 2023 base): hand-check those 4 lines before overwriting.

## 5. Cross-cutting rules for whoever codes this
- Fog audit: `tools/audit/audit_fog_honesty.py` counts `World.Actors`, `ActorsHavingTrait`, `ActorsWithTrait`, `ActorsInBox`, `FindActorsInCircle` per bot file against `tools/audit/fog_honesty_manifest.json`; any increase FAILS. Every upstream hunk above that reads `world.Actors` (harass start building scan, aircraft counts, building lists) must use an ActorIndex or the observed helpers (`IsPreferredObservedEnemyUnit`, `FindFrozenEnemyTarget`).
- Run `python tools/audit/audit_ai_frankenstein.py` (bot modules protected) after any bot-file edit.
- Orders only: all upstream hunks queue `Order`s; none mutates actors. Nothing here needs an exception.
- Switch plumbing: add a group (e.g. `F_ca_f2p2`) in `tools/ai/increment_switches.yaml`; C# defaults keep the old behaviour (WORKFLOW 3).
- Verified facts: engine already has `WithPathFrom`/`WithPathTo`/`ClosestToWithPathFrom`/`ClosestToWithPathToAny`/`ClosestToIgnoringPath(tuple selector)`, so no engine change is needed for any of the above (rule 7).

## 6. Maintainer rulings (2026-10-01)

* WP-A5.1 buildings-first `FindClosestEnemy`: **port behind a switch** -> `SquadManagerBotModuleCA.PreferBuildingTargets` (group `F2_ca_f2p2`).
* WP-A5.2 value-only attack launch: **port behind a switch** -> `SquadManagerBotModuleCA.ValueOnlyAttackLaunch`.
* WP-A5.3 compositions default: **after INC-4** (no genericbot recipes yet; code stays inert).
* `UnitBuilderBotModuleCA@generic` is shared with classicbot and extended by 34 ContentPacks, so it is NOT split; its switches are gated by `SwitchCondition: genericbot`.
