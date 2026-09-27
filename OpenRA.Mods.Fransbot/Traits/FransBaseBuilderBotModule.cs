#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System;
using System.Collections.Frozen;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Linq;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Pathfinder;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	/// <summary>
	/// Small coordination surface used by FransUnitBuilder and FransMcvExpansionManager.
	/// It replaces the older opening-only coordination service.
	/// </summary>
	public interface IFransBaseBuilderService
	{
		bool AllowAutomaticHarvesterDemand { get; }
		bool AllowExpansionMcvProduction { get; }
		bool PauseOrdinaryVehicleProduction { get; }
		bool PauseOrdinaryInfantryProduction { get; }
		bool OpeningComplete { get; }
		bool OpeningMcvCompleted { get; }
		bool OpeningLocked { get; }
		bool ReadyForFirstExpansionRefineryPrebuild { get; }
		CPos? StrategicForwardTarget { get; }
		CPos StrategicBaseCenter { get; }
		void CaptureExistingProductionForExpansionLock();
		void DrainExistingProductionForExpansionLock(IBot bot);
		bool HasExpansionLockDrainOwnership(Actor queueActor);
		bool TryGetSecureFootholdProduction(CPos securePoint, out Actor production);
		bool TryGetStrategicDefenseQueueRequest(out string actorType);
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Fransbot base builder. Deterministic opening is preserved; after the opening, explicit Struggling/Growing/Prosperous/Surplus policy and named strategic needs are the only normal build paths.")]
	public class FransBaseBuilderBotModuleInfo : ConditionalTraitInfo, NotBefore<ResourceMapBotModuleInfo>, NotBefore<IResourceLayerInfo>
	{
		[ActorReference] public readonly FrozenSet<string> ConstructionYardTypes = FrozenSet<string>.Empty;
		[ActorReference] public readonly FrozenSet<string> RefineryTypes = FrozenSet<string>.Empty;
		[ActorReference] public readonly FrozenSet<string> PowerTypes = FrozenSet<string>.Empty;
		[ActorReference] public readonly FrozenSet<string> ProductionTypes = FrozenSet<string>.Empty;
		[ActorReference] public readonly FrozenSet<string> TechTypes = FrozenSet<string>.Empty;
		[ActorReference] public readonly FrozenSet<string> NavalProductionTypes = FrozenSet<string>.Empty;
		[ActorReference]
		[Desc("Military production buildings controlled by explicit economy-state capacity policy. Prosperous may duplicate each relevant category toward two; true Surplus expands toward the larger configured targets.")]
		public readonly FrozenSet<string> SurplusProductionBuildingTypes = FrozenSet<string>.Empty;
		[ActorReference]
		[Desc("Air-production actor types sharing one combined capacity target. Prosperous may duplicate this category to two; true Surplus continues toward the long-run target. AirAI prioritizes this category first.")]
		public readonly FrozenSet<string> SurplusAirProductionTypes = FrozenSet<string>.Empty;
		[Desc("Long-run combined airfield/helipad target during sustained true Surplus.")] public readonly int SurplusAirProductionTarget = 8;
		[Desc("Long-run combined WEAP target during sustained true Surplus.")] public readonly int SurplusWarFactoryTarget = 4;
		[Desc("Long-run combined TENT/BARR target during sustained true Surplus.")] public readonly int SurplusInfantryProductionTarget = 8;
		[Desc("Long-run combined SPEN/SYRD target during sustained true Surplus.")] public readonly int SurplusNavalProductionTarget = 2;
		[Desc("AirAI Surplus priority weight for airfields/helipads.")] public readonly int SurplusAirProductionPriority = 400;
		[Desc("AirAI Surplus priority weight for WEAP.")] public readonly int SurplusWarFactoryPriority = 350;
		[Desc("AirAI Surplus priority weight for naval producers.")] public readonly int SurplusNavalProductionPriority = 200;
		[Desc("AirAI Surplus priority weight for infantry producers.")] public readonly int SurplusInfantryProductionPriority = 100;
		[ActorReference] public readonly FrozenSet<string> SiloTypes = FrozenSet<string>.Empty;
		[ActorReference] public readonly FrozenSet<string> BarracksTypes = FrozenSet<string>.Empty;
		[ActorReference] public readonly FrozenSet<string> WarFactoryTypes = FrozenSet<string>.Empty;

		[Desc("Maximum distance in cells from the active SECURE point for TENT/BARR/WEAP to count as the foothold's required local production building.")]
		public readonly int SecureFootholdProductionRadius = 14;

		[Desc("When true, a missing SECURE foothold producer prefers WEAP once the shared economy is Prosperous or Surplus; lower economy prefers faction-available TENT/BARR. Existing local TENT/BARR/WEAP always satisfies the requirement.")]
		public readonly bool SecureFootholdPreferWarFactoryAtProsperous = true;
		[ActorReference] public readonly FrozenSet<string> HarvesterTypes = FrozenSet<string>.Empty;
		[ActorReference] public readonly FrozenSet<string> RepairTypes = FrozenSet<string>.Empty;
		[ActorReference] public readonly FrozenSet<string> McvTypes = FrozenSet<string>.Empty;
		[ActorReference] public readonly FrozenSet<string> RadarTypes = FrozenSet<string>.Empty;
		[ActorReference]
		[Desc("Faction advanced-tech centers that are strategically prioritized after a physical Radar Dome while the economy is Prosperous or Surplus.")]
		public readonly FrozenSet<string> AdvancedTechCenterTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Strategic superweapon structures prioritized immediately after the faction advanced-tech center becomes physical. Buildable prerequisites remain authoritative.")]
		public readonly FrozenSet<string> StrategicSuperweaponTypes = FrozenSet<string>.Empty;


		[ActorReference]
		[Desc("Enemy structures/units that count as legitimately observed radar-tech pressure. Hidden live actors are never queried; structure memory comes from FransStrategicMap and mobile units must be currently visible.")]
		public readonly FrozenSet<string> RadarEnemyTechTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Observed enemy air-production structures or visible aircraft that justify the strongest early anti-air/air-tech parity response.")]
		public readonly FrozenSet<string> RadarEnemyAirThreatTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Enemy defensive structures that immediately make Radar Dome a tactical prerequisite so artillery/V2 or air support can be fielded before a ground assault attacks that defended area.")]
		public readonly FrozenSet<string> RadarEnemyDefenseTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Air-production structures to prioritize immediately after Radar Dome when available for the faction and power/economy allow.")]
		public readonly FrozenSet<string> RadarFollowupAirProductionTypes = FrozenSet<string>.Empty;

		[Desc("Allow the first AFLD/HPAD after a physical Radar Dome while the throughput economy is still Struggling, provided the physical PROC/HARV maturity thresholds below are met. Later air-producer growth still follows the normal economy-state rules.")]
		public readonly bool FirstAirProductionAllowPhysicalMaturityFallback = true;

		[Desc("Minimum physical refineries required by the Struggling-only first-air-production maturity fallback.")]
		public readonly int FirstAirProductionMinimumRefineries = 3;

		[Desc("Minimum physical harvesters required by the Struggling-only first-air-production maturity fallback.")]
		public readonly int FirstAirProductionMinimumHarvesters = 3;

		[Desc("Local enemy combat value at or above this level blocks the first Radar-followup AFLD/HPAD even when economy/maturity otherwise permits it.")]
		public readonly int FirstAirProductionMaximumLocalPressureValue = 8000;

		[Desc("World ticks between cached Radar Dome readiness evaluations. This is only a scan interval, never a tech timing trigger.")]
		public readonly int RadarDecisionInterval = 125;

		[Desc("Radius around the main base used for local visible/remembered combat pressure when deciding whether Prosperous teching is tactically safe.")]
		public readonly int RadarPressureRadiusCells = 28;

		[Desc("Estimated local enemy combat value at or above this level blocks normal tech unless the stronger preferred economy rule is satisfied below it.")]
		public readonly int RadarHighPressureValue = 4500;

		[Desc("Estimated local enemy combat value at or above this level blocks Radar Dome even as a tech-parity response.")]
		public readonly int RadarCriticalPressureValue = 8000;


		[Desc("After a harvester/refinery or base production building is attacked, postpone normal Radar Dome tech for this many world ticks.")]
		public readonly int RadarRecentEconomicAttackHoldTicks = 2500;

		[Desc("Minimum remembered enemy-structure confidence for that structure to count as observed enemy tech.")]
		public readonly int RadarEnemyTechMemoryConfidencePercent = 35;


		public readonly FrozenSet<string> BuildingQueues = new HashSet<string> { "Building" }.ToFrozenSet();
		public readonly int MinBaseRadius = 2;
		public readonly int MaxBaseRadius = 20;
		[Desc("Preferred empty-cell gap between ordinary base structures. If the ideal gap is impossible, FransBaseBuilder chooses the legal site with the greatest available clearance instead of immediately packing the structure against the base.")]
		public readonly int MinimumStructureSpacingCells = 1;
		public readonly int MinimumExcessPower = 0;
		public readonly int MaximumExcessPower = 200;
		public readonly int ExcessPowerIncrement = 40;
		public readonly int ExcessPowerIncreaseThreshold = 4;
		public readonly int InitialMinimumRefineryCount = 0;
		public readonly int AdditionalMinimumRefineryCount = 2;
		public readonly int StructureProductionInactiveDelay = 125;
		public readonly int StructureProductionActiveDelay = 25;
		public readonly int StructureProductionResumeDelay = 1500;
		public readonly int MaximumFailedPlacementAttempts = 3;
		public readonly int MaxResourceCellsToCheck = 3;
		public readonly int CheckForNewBasesDelay = 1500;
		[Desc("Chance that a reliable Strategic Map front/chokepoint anchor biases defenses and fallback front/rear placement. 0 disables directional placement; 100 always uses it when available.")]
		public readonly int DirectionalPlacementChance = 100;
		public readonly int RallyPointScanRadius = 8;
		[Desc("Minimum confidence of a legitimately remembered enemy structure before it may define the enemy-base direction for production placement.")]
		public readonly int EnemyBaseDirectionMinimumConfidencePercent = 40;
		[Desc("Directional weight for WEAP placement toward the best legitimately known enemy construction/base cluster. 0 disables; 100 strongly prefers the enemy side of the base.")]
		public readonly int WarFactoryEnemyDirectionWeightPercent = 90;
		[Desc("Weaker directional weight for BARR/TENT placement toward the enemy side. Refineries never use this bias.")]
		public readonly int BarracksEnemyDirectionWeightPercent = 40;
		[ActorReference]
		[Desc("Completed structures that may hold their preferred placement while ordinary friendly mobile blockers are moved away first.")]
		public readonly FrozenSet<string> FootprintClearanceBuildingTypes = FrozenSet<string>.Empty;
		[Desc("Extra cells around a blocked preferred footprint that ordinary friendly blockers should clear.")]
		public readonly int BuildingFootprintClearanceRadius = 2;
		[Desc("World ticks between re-issued blocker-clear moves for the same completed structure.")]
		public readonly int BuildingFootprintClearanceRetryTicks = 25;
		[Desc("Maximum world ticks to hold a completed structure while clearing friendly blockers before normal placement fallback is allowed.")]
		public readonly int BuildingFootprintClearanceMaximumWaitTicks = 150;
		[Desc("Maximum preferred candidate cells inspected for friendly-blocker evidence before falling back to ordinary placement.")]
		public readonly int BuildingFootprintClearanceCandidateCount = 64;
		[ActorReference]
		[Desc("Ordinary production structures that should prefer the strategic front/chokepoint side of the base.")]
		public readonly FrozenSet<string> ForwardStructureTypes = FrozenSet<string>.Empty;
		[Desc("Minimum sector knowledge required before a Strategic Map chokepoint may steer building/rally placement.")]
		public readonly int StrategicChokeMinimumKnowledgePercent = 80;
		[Desc("Minimum number of world ticks to keep a selected strategic front anchor before switching to a different valid anchor.")]
		public readonly int StrategicAnchorMinimumHoldTicks = 750;
		[Desc("If the current front temporarily disappears from the strategic snapshot, keep it for this many world ticks before falling back.")]
		public readonly int StrategicAnchorLostGraceTicks = 500;
		[Desc("When the current choke is still valid, a replacement choke must beat its score by at least this amount before the anchor switches.")]
		public readonly int StrategicAnchorSwitchScoreMargin = 150;
		[Desc("Additional score margin per cell of anchor movement. Large cross-map theatre switches therefore require much stronger evidence.")]
		public readonly int StrategicAnchorSwitchDistancePenaltyPerCell = 8;
		[Desc("Minimum distance from a producer for a strategic rally point. Helps keep newly produced units from piling up at the factory door.")]
		public readonly int StrategicRallyMinimumDistance = 4;
		[Desc("Number of top strategic rally candidates shared deterministically between producers to spread forward exit positions.")]
		public readonly int StrategicRallyCandidateCount = 6;
		public readonly int CheckForWaterRadius = 8;
		public readonly FrozenSet<string> WaterTerrainTypes = new HashSet<string> { "Water" }.ToFrozenSet();
		public readonly FrozenDictionary<string, int> BuildingLimits = new Dictionary<string, int>().ToFrozenDictionary();
		public readonly FrozenDictionary<string, int> BuildingDelays = new Dictionary<string, int>().ToFrozenDictionary();
		public readonly int ProductionMinCashRequirement = 500;
		public readonly int AssignRallyPointsInterval = 100;
		public readonly int CheckBestResourceLocationInterval = 151;
		public readonly int SellRefineryInterval = 5000;
		public readonly int SellRefineryTooCloseCellDistance = 6;
		public readonly int SellRefineryNoResourceDistance = 12;
		public readonly int MaxRefineryPerIndice = 2;
		public readonly ImmutableArray<int> ExpansionTolerate = [1];
		public readonly ImmutableArray<int> ForceExpansionTolerate = [2];
		public readonly int PerExpansionTolerateOnCash = 12000;
		[Desc("Opening state scan interval in world ticks.")]
		public readonly int OpeningScanInterval = 25;
		[Desc("Minimum world ticks before BaseBuilder may re-issue placement for the same completed queue item. Prevents per-tick BuildingInfluence/PlaceBuilding churn while OpenRA resolves the previous order.")]
		public readonly int CompletedPlacementRetryTicks = 25;
		[Desc("World ticks after an issued PlaceBuilding/PlacePlug order before a still-READY queue item counts as an unconfirmed placement attempt. This is intentionally much longer than the normal retry interval so native order processing can settle before deadlock recovery starts.")]
		public readonly int CompletedPlacementConfirmationTimeoutTicks = 500;
		[Desc("Maximum unconfirmed placement attempts for one completed Building-queue item before the stale READY item is cancelled. This is a generic final guard against valid-looking placement orders silently holding the shared queue forever.")]
		public readonly int CompletedPlacementConfirmationMaximumRetries = 4;
		[Desc("If an opening structure was ordered but neither queued nor placed for this long, clear the latch and retry.")]
		public readonly int OpeningOrderRetryTimeout = 1500;
		[Desc("World ticks between diagnostics while the one-shot opening MCV request exists but native vehicle production has not started.")]
		public readonly int OpeningMcvDiagnosticInterval = 250;
		[Desc("Recovery timeout for an ore-mine PROC claim when FransHarvester still reports that mine unpaired and no refinery is queued/in production. This prevents a dead claim if a nearby physical PROC was deterministically paired to a different mine.")]
		public readonly int OreMineRefineryClaimRecoveryTimeout = 1500;
		[Desc("Minimum world ticks before re-issuing PlaceBuilding for the same completed post-opening ore-node PROC. This is deliberately longer than generic placement retry so OpenRA can materialize the first accepted placement without a duplicate order 25 WT later.")]
		public readonly int OreMineRefineryPlacementPendingRetryTicks = 250;

		[Desc("Maximum world ticks a completed WEAP/BARR item that must be placed at an expansion FACT may hold the shared Building queue after that FACT disappears. On expiry the stale item is cancelled; future production remains blocked until a valid expansion FACT exists again.")]
		public readonly int ExpansionPlacementCompletedHoldTimeoutTicks = 3000;
		[Desc("After the first expansion refinery reservation has priority, finish the post-MCV production tail until this many power structures exist. Emergency low-power construction may still precede the reserved refinery. Set 0 to disable.")]
		public readonly int PostMcvOpeningPowerTarget = 3;

		[Desc("After the first expansion refinery reservation has priority, finish the post-MCV production tail until this many barracks/tents exist. Set 0 to disable.")]
		public readonly int PostMcvOpeningBarracksTarget = 2;

		[Desc("Reserve the shared Building queue immediately after the first MCV starts until the first expansion refinery raises the total refinery count to this target. The MCV manager pre-builds and holds this refinery for the expansion FACT. Set 0 to disable.")]
		public readonly int PostMcvOpeningFirstExpansionRefineryTarget = 3;

		[Desc("Maximum number of WEAP structures that may use ordinary/main-base placement. Once this many exist, additional WEAP must be placed beside a live expansion FACT. Set -1 to disable this routing rule.")]
		public readonly int MaximumMainBaseWarFactories = 2;

		[Desc("Maximum combined number of TENT/BARR structures that may use ordinary/main-base placement. Once this many exist, additional infantry producers must be placed beside a live expansion FACT. Set -1 to disable this routing rule.")]
		public readonly int MaximumMainBaseBarracks = 3;

		[Desc("At Prosperous or Surplus economy, route newly required PWR/APWR to a live expansion FACT area when one exists, spreading vulnerable infrastructure instead of stacking all power at the original base.")]
		public readonly bool PreferExpansionPowerPlacementAtProsperousOrBetter = true;

		[Desc("Minimum placement radius around the selected expansion FACT for surplus WEAP/TENT/BARR production structures.")]
		public readonly int ExpansionProductionPlacementMinRadius = 2;

		[Desc("Maximum placement radius around the selected expansion FACT for surplus WEAP/TENT/BARR production structures.")]
		public readonly int ExpansionProductionPlacementMaxRadius = 10;

		[Desc("When true, a FACT on a different ground landmass from the oldest/main FACT becomes a REMOTE BASE after it has a local refinery. It must then gain local military production instead of relying indefinitely on LST reinforcement from the main base.")]
		public readonly bool EnableRemoteBaseLocalProduction = true;

		[Desc("Maximum distance in cells from a remote FACT for its local refinery and local TENT/BARR/WEAP to count toward REMOTE BASE maturity.")]
		public readonly int RemoteBaseProductionRadius = 12;

		[ActorReference]
		[Desc("Faction tech structures that unlock capital naval bombardment ships (ATEK for Cruiser, STEK for Missile Submarine).")]
		public readonly FrozenSet<string> NavalCapitalTechTypes = FrozenSet<string>.Empty;


		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			if (BuildingQueues.Count == 0)
				throw new YamlException("FransBaseBuilder needs at least one Building queue.");
			if (OpeningScanInterval < 25 || CompletedPlacementRetryTicks <= 0 ||
				CompletedPlacementConfirmationTimeoutTicks < CompletedPlacementRetryTicks || CompletedPlacementConfirmationMaximumRetries <= 0 ||
				OpeningOrderRetryTimeout <= 0 || OpeningMcvDiagnosticInterval < 25 ||
				OreMineRefineryClaimRecoveryTimeout <= 0 || OreMineRefineryPlacementPendingRetryTicks < CompletedPlacementRetryTicks ||
				ExpansionPlacementCompletedHoldTimeoutTicks <= 0)
				throw new YamlException("FransBaseBuilder recurring opening work must be at least 25 WT and placement/watchdog intervals must be positive.");
			if (MaximumFailedPlacementAttempts <= 0 || StructureProductionActiveDelay < 0 || StructureProductionInactiveDelay < 0 ||
				StructureProductionResumeDelay < 0 || CheckForNewBasesDelay < 0 || AssignRallyPointsInterval <= 0 ||
				CheckBestResourceLocationInterval <= 0)
				throw new YamlException("FransBaseBuilder production/scan timing is invalid.");
			if (MinBaseRadius < 0 || MaxBaseRadius < MinBaseRadius || RallyPointScanRadius < 0 || CheckForWaterRadius < 0 ||
				MaxResourceCellsToCheck <= 0 || MaxRefineryPerIndice <= 0 || InitialMinimumRefineryCount < 0 ||
				AdditionalMinimumRefineryCount < 0 || ProductionMinCashRequirement < 0 || PerExpansionTolerateOnCash < 0 ||
				SellRefineryTooCloseCellDistance < 0 || SellRefineryNoResourceDistance < 0)
				throw new YamlException("FransBaseBuilder radius/resource/refinery settings are invalid.");
			if (MinimumExcessPower > MaximumExcessPower || ExcessPowerIncrement < 0 || ExcessPowerIncreaseThreshold <= 0)
				throw new YamlException("FransBaseBuilder excess-power settings are invalid.");
			if (MinimumStructureSpacingCells < 0)
				throw new YamlException("FransBaseBuilder structure spacing cannot be negative.");
			if (DirectionalPlacementChance < 0 || DirectionalPlacementChance > 100)
				throw new YamlException($"{nameof(DirectionalPlacementChance)} must be between 0 and 100.");
			if (StrategicChokeMinimumKnowledgePercent < 0 || StrategicChokeMinimumKnowledgePercent > 100)
				throw new YamlException($"{nameof(StrategicChokeMinimumKnowledgePercent)} must be between 0 and 100.");
			if (StrategicAnchorMinimumHoldTicks < 0 || StrategicAnchorLostGraceTicks < 0 || StrategicAnchorSwitchScoreMargin < 0 ||
				StrategicAnchorSwitchDistancePenaltyPerCell < 0)
				throw new YamlException("Strategic anchor hysteresis settings cannot be negative.");
			if (StrategicRallyMinimumDistance < 0 || StrategicRallyMinimumDistance > RallyPointScanRadius)
				throw new YamlException($"{nameof(StrategicRallyMinimumDistance)} must be between 0 and {nameof(RallyPointScanRadius)}.");
			if (StrategicRallyCandidateCount <= 0)
				throw new YamlException($"{nameof(StrategicRallyCandidateCount)} must be greater than zero.");
			if (MaximumMainBaseWarFactories < -1 || MaximumMainBaseBarracks < -1 || ExpansionProductionPlacementMinRadius < 0 ||
				ExpansionProductionPlacementMaxRadius < ExpansionProductionPlacementMinRadius || SecureFootholdProductionRadius <= 0 || RemoteBaseProductionRadius <= 0)
				throw new YamlException("FransBaseBuilder main-base production caps/expansion placement settings are invalid.");
			if (EnemyBaseDirectionMinimumConfidencePercent is < 0 or > 100 || WarFactoryEnemyDirectionWeightPercent is < 0 or > 100 ||
				BarracksEnemyDirectionWeightPercent is < 0 or > 100 || BuildingFootprintClearanceRadius < 0 ||
				BuildingFootprintClearanceRetryTicks <= 0 || BuildingFootprintClearanceMaximumWaitTicks < BuildingFootprintClearanceRetryTicks ||
				BuildingFootprintClearanceCandidateCount <= 0 ||
				SurplusAirProductionTarget <= 0 || SurplusWarFactoryTarget <= 0 || SurplusInfantryProductionTarget <= 0 || SurplusNavalProductionTarget <= 0 ||
				SurplusAirProductionPriority < 0 || SurplusWarFactoryPriority < 0 || SurplusNavalProductionPriority < 0 || SurplusInfantryProductionPriority < 0)
				throw new YamlException("FransBaseBuilder directional/footprint-clearance/Surplus-production settings are invalid.");
			if (RadarDecisionInterval <= 0 || RadarPressureRadiusCells < 0 ||
				RadarHighPressureValue < 0 || RadarCriticalPressureValue < RadarHighPressureValue ||
				RadarRecentEconomicAttackHoldTicks < 0 || RadarEnemyTechMemoryConfidencePercent < 0 || RadarEnemyTechMemoryConfidencePercent > 100 ||
				FirstAirProductionMinimumRefineries < 0 || FirstAirProductionMinimumHarvesters < 0 || FirstAirProductionMaximumLocalPressureValue < 0)
				throw new YamlException("FransBaseBuilder Radar/first-air-production settings are invalid.");
		}

		public override object Create(ActorInitializer init) { return new FransBaseBuilderBotModule(init.Self, this); }
	}

	public class FransBaseBuilderBotModule : ConditionalTrait<FransBaseBuilderBotModuleInfo>, IGameSaveTraitData,
		IBotTick, IBotPositionsUpdated, IBotRespondToAttack, IBotRequestPauseUnitProduction, IBotSuggestRefineryProduction,
		INotifyActorDisposing, IResolveOrder, IFransBaseBuilderService
	{
		const string OrdinaryStartProductionAcknowledgedOrder = "FransBaseBuilderStartProductionAcknowledged";
		enum OpeningStage
		{
			Power1,
			Barracks1,
			Refinery1,
			Refinery2,
			Power2,
			WarFactory,
			Repair,
			Mcv,
			Complete
		}

		enum FransBuildingType { Building, Refinery }
		enum FransWaterCheck { NotChecked, EnoughWater, NotEnoughWater, DontCheck }

		readonly World world;
		readonly Player player;
		PowerManager playerPower;
		PlayerResources playerResources;
		IResourceLayer resourceLayer;
		IPathFinder pathFinder;
		IFransStrategicMapService strategicMapService;
		IFransCombatIntelService combatIntelService;
		IFransCommanderCoreService groundCommanderService;
		IFransRiskModelService riskModelService;
		IFransEconomicSaturationService economicStateService;
		IFransOreEconomyService oreEconomyService;
		IFransExpansionStateService expansionStateService;
		IFransGeneralService generalService;
		IFransGroundUnitReservationService groundUnitReservationService;
		IFransCaptureSecurityService[] captureSecurityServices;
		IFransCaptureTransportService transportService;
		IFransOpeningUnitPlanService openingUnitPlanService;
		IBotPositionsUpdated[] positionsUpdatedModules;
		IBotRequestUnitProduction[] requestUnitProduction;
		CPos initialBaseCenter;
		readonly Stack<TraitPair<RallyPoint>> rallyPoints = [];
		int assignRallyPointsTicks;
		int checkBestResourceLocationTicks;
		int sellRefineryTick;
		int openingScanTicks;
		bool firstTick = true;
		readonly FransBaseBuilderQueueManager[] builders;
		int currentBuilderIndex;
		OpeningStage openingStage = OpeningStage.Power1;
		bool openingEverInitialized;
		bool firstExpansionRefineryTargetReached;
		bool openingStructureIssued;
		string openingStructureType;
		int openingStructureIssuedTick;
		bool openingUnitBaselineInitialized;
		int openingMcvBaseline;
		int openingConyardBaseline;
		bool openingMcvRequestIssued;
		int openingMcvRequestTick;
		int openingMcvLastDiagnosticTick = -1;
		bool openingMcvCompleted;
		int lastStrategicSnapshotTick = -1;
		CPos? strategicForwardTarget;
		string strategicForwardSource;
		int strategicForwardSectorId = -1;
		int strategicForwardScore = int.MinValue;
		int strategicAnchorChangedTick = -1;
		int strategicLastReliableTick = -1;
		int strategicAnchorRevision;
		int lastRadarDecisionTick = int.MinValue;
		bool radarDecisionAllowed;
		bool radarDecisionEnemyTechResponse;
		string radarDecisionReason = "not evaluated";
		int lastRadarEconomicAttackTick = int.MinValue;
		int lastRadarDecisionLogTick = int.MinValue;
		string lastRadarDecisionLoggedState;
		CPos? oreMineRefineryTarget;
		int oreMineRefineryClaimTick = -1;

		public CPos? DefenseCenter { get; private set; }
		public CPos? ResourceConyardCenter;
		public Dictionary<string, int> BuildingsBeingProduced = [];
		public Dictionary<Actor, (CPos ConyardLoc, CPos ResourceLoc)> RequestedRefineries = [];
		public IBotBaseExpansion[] BaseExpansionModules;
		public ResourceMapBotModule ResourceMapModule;
		public readonly ActorIndex.OwnerAndNamesAndTrait<BuildingInfo> RefineryBuildings;
		readonly ActorIndex.OwnerAndNamesAndTrait<BuildingInfo> powerBuildings;
		public readonly ActorIndex.OwnerAndNamesAndTrait<BuildingInfo> ConstructionYardBuildings;
		public readonly ActorIndex.OwnerAndNamesAndTrait<BuildingInfo> ProductionBuildings;

		public bool OpeningComplete => openingStage == OpeningStage.Complete;
		public bool OpeningMcvCompleted => openingMcvCompleted;
		public bool OpeningLocked => !openingMcvCompleted;
		public bool ReadyForFirstExpansionRefineryPrebuild =>
			OpeningComplete &&
			!firstExpansionRefineryTargetReached &&
			Info.PostMcvOpeningFirstExpansionRefineryTarget > 0 &&
			CountOwned(Info.RefineryTypes) < Info.PostMcvOpeningFirstExpansionRefineryTarget &&
			expansionStateService?.FirstExpansionRefineryPrebuildAllowed != false;
		public bool AllowAutomaticHarvesterDemand => OpeningMcvCompleted;
		public bool AllowExpansionMcvProduction => !OpeningLocked;
		public bool PauseOrdinaryVehicleProduction => openingStage == OpeningStage.Mcv;
		public bool PauseOrdinaryInfantryProduction => false;
		public CPos? StrategicForwardTarget => strategicForwardTarget;
		public CPos StrategicBaseCenter => GetBaseCenter();

		public bool TryGetStrategicDefenseQueueRequest(out string actorType)
		{
			actorType = null;
			if (OpeningLocked || economicStateService == null || !economicStateService.IsProsperousOrBetter ||
				CountOwned(Info.RadarTypes) == 0 || CountOwned(Info.AdvancedTechCenterTypes) == 0 ||
				CountOwned(Info.StrategicSuperweaponTypes) > 0 || Info.StrategicSuperweaponTypes.Any(IsQueued))
				return false;

			actorType = Info.StrategicSuperweaponTypes
				.Where(BelowLimit)
				.OrderBy(type => type)
				.FirstOrDefault();
			return actorType != null;
		}

		public FransBaseBuilderBotModule(Actor self, FransBaseBuilderBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			builders = new FransBaseBuilderQueueManager[info.BuildingQueues.Count];
			RefineryBuildings = new ActorIndex.OwnerAndNamesAndTrait<BuildingInfo>(world, info.RefineryTypes, player);
			powerBuildings = new ActorIndex.OwnerAndNamesAndTrait<BuildingInfo>(world, info.PowerTypes, player);
			ConstructionYardBuildings = new ActorIndex.OwnerAndNamesAndTrait<BuildingInfo>(world, info.ConstructionYardTypes, player);
			ProductionBuildings = new ActorIndex.OwnerAndNamesAndTrait<BuildingInfo>(world, info.ProductionTypes, player);
		}

		protected override void Created(Actor self)
		{
			playerPower = self.Owner.PlayerActor.TraitOrDefault<PowerManager>();
			playerResources = self.Owner.PlayerActor.Trait<PlayerResources>();
			resourceLayer = self.World.WorldActor.TraitOrDefault<IResourceLayer>();
			pathFinder = self.World.WorldActor.TraitOrDefault<IPathFinder>();
			strategicMapService = self.Owner.PlayerActor.TraitsImplementing<IFransStrategicMapService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransBaseBuilderBotModule requires FransStrategicMapBotModule.");
			combatIntelService = self.Owner.PlayerActor.TraitsImplementing<IFransCombatIntelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransBaseBuilderBotModule requires FransCombatIntelBotModule.");
			groundCommanderService = self.Owner.PlayerActor.TraitsImplementing<IFransCommanderCoreService>().FirstOrDefault();
			riskModelService = self.Owner.PlayerActor.TraitsImplementing<IFransRiskModelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransBaseBuilderBotModule requires FransRiskModelBotModule.");
			economicStateService = self.Owner.PlayerActor.TraitsImplementing<IFransEconomicSaturationService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransBaseBuilderBotModule requires FransEconomicSaturationBotModule.");
			oreEconomyService = self.Owner.PlayerActor.TraitsImplementing<IFransOreEconomyService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransBaseBuilderBotModule requires FransHarvesterBotModule ore-economy service.");
			expansionStateService = self.Owner.PlayerActor.TraitsImplementing<IFransExpansionStateService>().FirstOrDefault();
			generalService = self.Owner.PlayerActor.TraitsImplementing<IFransGeneralService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransBaseBuilderBotModule requires FransGeneralBotModule for SECURE foothold production.");
			groundUnitReservationService = self.Owner.PlayerActor.TraitsImplementing<IFransGroundUnitReservationService>().FirstOrDefault();
			captureSecurityServices = self.Owner.PlayerActor.TraitsImplementing<IFransCaptureSecurityService>().ToArray();
			transportService = self.Owner.PlayerActor.TraitsImplementing<IFransCaptureTransportService>().FirstOrDefault();
			openingUnitPlanService = self.Owner.PlayerActor.TraitsImplementing<IFransOpeningUnitPlanService>().FirstOrDefault();
			positionsUpdatedModules = self.Owner.PlayerActor.TraitsImplementing<IBotPositionsUpdated>().ToArray();
			BaseExpansionModules = self.Owner.PlayerActor.TraitsImplementing<IBotBaseExpansion>().ToArray();
			requestUnitProduction = self.Owner.PlayerActor.TraitsImplementing<IBotRequestUnitProduction>().ToArray();

			var i = 0;
			foreach (var building in Info.BuildingQueues.OrderBy(x => x))
				builders[i++] = new FransBaseBuilderQueueManager(this, building, player, playerPower, playerResources, resourceLayer);
		}

		protected override void TraitEnabled(Actor self)
		{
			foreach (var builder in builders)
				builder.ClearExpansionLockDrain();

			assignRallyPointsTicks = Math.Max(1, Info.AssignRallyPointsInterval);
			checkBestResourceLocationTicks = Math.Max(1, Info.CheckBestResourceLocationInterval);
			sellRefineryTick = Info.SellRefineryInterval < 0 ? 0 : Math.Max(1, Info.SellRefineryInterval);
			openingScanTicks = 1;

			// frans-expansion-lock temporarily disables this trait while an expansion FACT uses the
			// shared Building queue. Re-enabling must NEVER restart the opening, otherwise every
			// expansion requests another opening HARV/MCV and repeats PWR/TENT/PROC/WEAP.
			if (!openingEverInitialized)
			{
				openingEverInitialized = true;
				openingStage = OpeningStage.Power1;
				openingStructureIssued = false;
				openingUnitBaselineInitialized = false;
				openingMcvCompleted = false;
				FransBotLog.BotDebug(world,
					"{0}: FransBaseBuilder MCV -> FIRST PROC CRITICAL PATH active. Deterministic opening remains PWR -> TENT/BARR -> PROC -> PROC -> PWR -> WEAP -> FIX -> physical MCV. After that MCV exists, the reserved first expansion PROC is the first normal Building item; only genuine low-power recovery may precede it. Normal post-opening Navy/Radar/tech/capacity resumes after the PROC reservation is satisfied.",
					player);
			}
			else
				FransBotLog.BotDebug(world, "{0}: FransBaseBuilder resumed after expansion lock; opening state remains {1}.", player, openingStage);
		}

		void IBotPositionsUpdated.UpdatedBaseCenter(CPos newLocation) { initialBaseCenter = newLocation; }
		void IBotPositionsUpdated.UpdatedDefenseCenter(CPos newLocation) { DefenseCenter = newLocation; }
		bool IBotRequestPauseUnitProduction.PauseUnitProduction => !IsTraitDisabled && !HasMinimalRefineryCount();

		void IFransBaseBuilderService.CaptureExistingProductionForExpansionLock()
		{
			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			foreach (var builder in builders)
				builder.CaptureExistingProductionForExpansionLock(queuesByCategory);
		}

		void IFransBaseBuilderService.DrainExistingProductionForExpansionLock(IBot bot)
		{
			if (bot == null || world.Type == WorldType.Editor || player.WinState != WinState.Undefined)
				return;

			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			foreach (var builder in builders)
				builder.DrainExistingProductionForExpansionLock(bot, queuesByCategory);
		}

		bool IFransBaseBuilderService.HasExpansionLockDrainOwnership(Actor queueActor)
		{
			return queueActor != null && builders.Any(builder => builder.HasExpansionLockDrainOwnership(queueActor.ActorID));
		}

		void IResolveOrder.ResolveOrder(Actor self, Order order)
		{
			if (order.OrderString != OrdinaryStartProductionAcknowledgedOrder)
				return;

			foreach (var builder in builders)
				if (builder.AcknowledgeOrdinaryStartProductionDispatch(order.ExtraData, order.TargetString, order.ExtraLocation.X))
					break;
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransBaseBuilder.BotTick");
			if (world.Type == WorldType.Editor || player.WinState != WinState.Undefined)
				return;

			// Once the first-expansion refinery target has physically existed, never reopen the
			// one-shot reservation merely because a refinery is destroyed later. Without this
			// latch BaseBuilder could hold an empty Building queue forever while the MCV manager
			// correctly considers its first-expansion reservation already completed.
			if (!firstExpansionRefineryTargetReached && OpeningComplete &&
				Info.PostMcvOpeningFirstExpansionRefineryTarget > 0 &&
				CountOwned(Info.RefineryTypes) >= Info.PostMcvOpeningFirstExpansionRefineryTarget)
			{
				firstExpansionRefineryTargetReached = true;
				FransBotLog.BotDebug(world,
					"{0}: Fast Expansion first-refinery target is physically established; the one-shot Building-queue reservation is permanently released.",
					player);
			}
			if (firstTick)
			{
				ResourceMapModule = bot.Player.PlayerActor.TraitsImplementing<ResourceMapBotModule>().FirstOrDefault(t => t.IsTraitEnabled());
				firstTick = false;
			}

			RefreshStrategicPositioningSnapshot();
			RefreshOreMineRefineryClaim();

			if (openingStage != OpeningStage.Complete && --openingScanTicks <= 0)
			{
				openingScanTicks = Info.OpeningScanInterval;
				UpdateOpening(bot);
			}

			UpdateOpeningMcvCompletion();
			TickRallyPoints(bot);
			UpdateBestResourceBase();
			RefreshBuildingsBeingProduced();
			TickOneBuilder(bot);

			if (Info.SellRefineryInterval >= 0 && --sellRefineryTick <= 0)
			{
				SellUselessRefinery(bot);
				sellRefineryTick = Info.SellRefineryInterval;
			}
		}

		void UpdateOpening(IBot bot)
		{
			if (openingStage == OpeningStage.Complete)
				return;

			if (openingStructureIssued && world.WorldTick - openingStructureIssuedTick >= Info.OpeningOrderRetryTimeout &&
				!IsQueued(openingStructureType) && !OpeningTargetSatisfied())
			{
				FransBotLog.BotDebug(world, "{0}: opening order {1} disappeared before completion; clearing latch and retrying.", player, openingStructureType);
				openingStructureIssued = false;
				openingStructureType = null;
			}

			var before = openingStage;
			switch (openingStage)
			{
				case OpeningStage.Power1:
					if (CountOwned(Info.PowerTypes) >= 1) AdvanceOpening();
					break;
				case OpeningStage.Barracks1:
					if (CountOwned(Info.BarracksTypes) >= 1) AdvanceOpening();
					break;
				case OpeningStage.Refinery1:
					if (CountOwned(Info.RefineryTypes) >= 1) AdvanceOpening();
					break;
				case OpeningStage.Refinery2:
					if (CountOwned(Info.RefineryTypes) >= 2) AdvanceOpening();
					break;
				case OpeningStage.Power2:
					if (CountOwned(Info.PowerTypes) >= 2) AdvanceOpening();
					break;
				case OpeningStage.WarFactory:
					if (CountOwned(Info.WarFactoryTypes) >= 1) AdvanceOpening();
					break;
				case OpeningStage.Repair:
					if (CountOwned(Info.RepairTypes) >= 1) AdvanceOpening();
					break;
				case OpeningStage.Mcv:
					// Fast Expansion vehicle sequence is one light map-control vehicle -> one manually built ore truck -> MCV.
					// makes the last arrow physical: the deterministic opening does not finish merely
					// because StartProduction was accepted. UnitBuilder cash-locks the opening MCV until it exists.
					if (openingUnitPlanService != null && !openingUnitPlanService.OpeningVehicleEconomyReadyForMcv)
						break;

					// Snapshot the already-owned main FACT/MCVs BEFORE checking for the new MCV.
					EnsureOpeningMcvBaseline();
					UpdateOpeningMcvCompletion();
					if (!openingMcvCompleted)
						ManageOpeningMcv(bot);
					if (openingMcvCompleted)
						AdvanceOpening();
					break;
			}

			if (before != openingStage)
				FransBotLog.BotDebug(world, "{0}: FransBaseBuilder opening advanced {1} -> {2}.", player, before, openingStage);
		}

		void AdvanceOpening()
		{
			openingStage++;
			openingStructureIssued = false;
			openingStructureType = null;
			openingUnitBaselineInitialized = false;
			openingMcvRequestIssued = false;
			openingMcvRequestTick = 0;
			openingMcvLastDiagnosticTick = -1;
			if (openingStage == OpeningStage.Complete)
				FransBotLog.BotDebug(world, "{0}: Fast Expansion core opening complete; the first opening MCV is physically present. Expansion planning and post-opening BaseBuilder policy are now unlocked.", player);
		}

		void EnsureOpeningMcvBaseline()
		{
			if (openingUnitBaselineInitialized)
				return;

			openingMcvBaseline = CountOwned(Info.McvTypes);
			openingConyardBaseline = CountOwned(Info.ConstructionYardTypes);
			openingUnitBaselineInitialized = true;
		}

		void ManageOpeningMcv(IBot bot)
		{
			EnsureOpeningMcvBaseline();

			// Same one-shot rule as the opening HARV. The MCV request must survive the short
			// UnitBuilder -> ProductionQueue hand-off window without being duplicated.
			if (openingMcvRequestIssued)
			{
				LogOpeningMcvWaitDiagnostic(bot);
				return;
			}

			if (RequestOne(bot, Info.McvTypes, "Fast Expansion MCV after FIX, one light vehicle and one manual ore truck"))
			{
				openingMcvRequestIssued = true;
				openingMcvRequestTick = world.WorldTick;
				openingMcvLastDiagnosticTick = world.WorldTick;
			}
		}

		void LogOpeningMcvWaitDiagnostic(IBot bot)
		{
			if (world.WorldTick - openingMcvLastDiagnosticTick < Info.OpeningMcvDiagnosticInterval)
				return;

			openingMcvLastDiagnosticTick = world.WorldTick;
			if (openingUnitPlanService?.OpeningMcvProductionStarted == true)
			{
				FransBotLog.BotDebug(world,
					"{0}: opening MCV production is active; waiting {1} WT since the original request for physical completion. UnitBuilder cash lock remains engaged.",
					player, world.WorldTick - openingMcvRequestTick);
				return;
			}

			var type = Info.McvTypes.OrderBy(x => x).FirstOrDefault(world.Map.Rules.Actors.ContainsKey);
			var unitBuilder = requestUnitProduction?.FirstEnabledTraitOrDefault();
			var requested = type == null || unitBuilder == null ? 0 : unitBuilder.RequestedProductionCount(bot, type);
			var queued = type != null && IsQueued(type);
			combatIntelService.EnsureCurrentSnapshot();
			var queues = combatIntelService.OwnedActors
				.SelectMany(a => a.TraitsImplementing<ProductionQueue>())
				.Where(q => q.Enabled)
				.OrderBy(q => q.Info.Type)
				.Select(q => $"{q.Info.Type}:[{string.Join(",", q.AllQueued().Select(i => i.Item))}]")
				.ToArray();
			FransBotLog.BotDebug(world,
				"{0}: opening MCV request still waiting {1} WT for native production start; type {2}, cash {3}, UnitBuilder outstanding {4}, native queued {5}, enabled queues {6}. Diagnostic only; does not change opening queue priority.",
				player, world.WorldTick - openingMcvRequestTick, type ?? "none", playerResources.GetCashAndResources(), requested, queued,
				queues.Length == 0 ? "none" : string.Join(";", queues));
		}

		void UpdateOpeningMcvCompletion()
		{
			if (openingMcvCompleted || !openingUnitBaselineInitialized)
				return;

			// Physical completion is the only end of the deterministic opening. Do not infer this from
			// ProductionQueue.Enabled/AllQueued(): active native production is not represented reliably
			// enough there for this state transition. A produced MCV or already-deployed extra FACT is proof.
			if (CountOwned(Info.McvTypes) <= openingMcvBaseline &&
				CountOwned(Info.ConstructionYardTypes) <= openingConyardBaseline)
				return;

			openingMcvCompleted = true;
			FransBotLog.BotDebug(world,
				"{0}: first opening MCV is physically complete; deterministic MCV cash lock releases and post-opening economy/expansion policy unlocks.", player);
		}

		bool RequestOne(IBot bot, FrozenSet<string> types, string reason)
		{
			var unitBuilder = requestUnitProduction?.FirstEnabledTraitOrDefault();
			if (unitBuilder == null)
				return false;
			var type = types.OrderBy(x => x).FirstOrDefault(world.Map.Rules.Actors.ContainsKey);
			if (type == null || IsQueued(type) || unitBuilder.RequestedProductionCount(bot, type) > 0)
				return false;
			FransBotLog.BotDebug(world, "{0}: FransBaseBuilder requests one {1}: {2}.", player, type, reason);
			unitBuilder.RequestUnitProduction(bot, type);
			return true;
		}

		bool IsQueued(string type)
		{
			if (string.IsNullOrEmpty(type)) return false;
			combatIntelService.EnsureCurrentSnapshot();
			return combatIntelService.OwnedActors
				.SelectMany(a => a.TraitsImplementing<ProductionQueue>())
				.Any(q => q.Enabled && q.AllQueued().Any(item => item.Item == type));
		}

		int CountOwned(FrozenSet<string> types)
		{
			combatIntelService.EnsureCurrentSnapshot();
			return combatIntelService.OwnedActors.Count(a => types.Contains(a.Info.Name));
		}

		int CountOwnedOrQueued(FrozenSet<string> types) => CountOwned(types) +
			BuildingsBeingProduced.Where(p => types.Contains(p.Key)).Sum(p => p.Value);

		bool BelowHardBuildingLimit(string name)
		{
			if (!Info.BuildingLimits.TryGetValue(name, out var limit))
				return true;
			combatIntelService.EnsureCurrentSnapshot();
			var current = combatIntelService.OwnedActors.Count(a => a.Info.Name == name) +
				(BuildingsBeingProduced.TryGetValue(name, out var q) ? q : 0);
			return current < limit;
		}

		public bool TryGetSecureFootholdProduction(CPos securePoint, out Actor production)
		{
			production = null;
			var radiusSquared = Info.SecureFootholdProductionRadius * Info.SecureFootholdProductionRadius;
			production = ProductionBuildings.Actors
				.Where(a => a != null && a.IsInWorld && !a.IsDead &&
					(Info.BarracksTypes.Contains(a.Info.Name) || Info.WarFactoryTypes.Contains(a.Info.Name)) &&
					(a.Location - securePoint).LengthSquared <= radiusSquared)
				.OrderBy(a => (a.Location - securePoint).LengthSquared).ThenBy(a => a.ActorID).FirstOrDefault();
			return production != null;
		}

		bool TryGetSecureFootholdFact(CPos securePoint, out Actor fact)
		{
			fact = null;
			var radiusSquared = Info.SecureFootholdProductionRadius * Info.SecureFootholdProductionRadius;
			fact = ConstructionYardBuildings.Actors
				.Where(a => a != null && a.IsInWorld && !a.IsDead &&
					(a.Location - securePoint).LengthSquared <= radiusSquared)
				.OrderBy(a => (a.Location - securePoint).LengthSquared).ThenBy(a => a.ActorID).FirstOrDefault();
			return fact != null;
		}

		bool TryGetSecureFootholdProductionNeed(out uint secureTargetId, out CPos secureCenter, out bool preferWarFactory)
		{
			secureTargetId = 0;
			secureCenter = default;
			preferWarFactory = false;
			if (!OpeningComplete || generalService == null)
				return false;

			// multiple military SECURE wins may await autonomous footholds at once.
			// Do not let the oldest no-FACT point block a later pending point whose physical FACT
			// already exists and is ready for its required local production building.
			foreach (var foothold in generalService.PendingSecureFootholds)
			{
				if (!generalService.IsSecureFootholdDevelopmentReady(foothold.TargetActorId))
					continue;
				if (TryGetSecureFootholdProduction(foothold.Cell, out _) ||
					!TryGetSecureFootholdFact(foothold.Cell, out _))
					continue;

				secureTargetId = foothold.TargetActorId;
				secureCenter = foothold.Cell;
				preferWarFactory = Info.SecureFootholdPreferWarFactoryAtProsperous && economicStateService.IsProsperousOrBetter;
				return true;
			}

			return false;
		}

		bool TryGetRemoteBaseProductionNeed(out Actor remoteFact, out bool needWarFactory, out bool needBarracks)
		{
			remoteFact = null;
			needWarFactory = false;
			needBarracks = false;
			if (!Info.EnableRemoteBaseLocalProduction || !OpeningComplete || strategicMapService == null)
				return false;

			var facts = ConstructionYardBuildings.Actors
				.Where(a => a != null && a.IsInWorld && !a.IsDead)
				.OrderBy(a => a.ActorID)
				.ToArray();
			if (facts.Length <= 1 || !strategicMapService.TryGetGroundLandmassId(facts[0].Location, out var mainLandmass))
				return false;

			var radiusSq = Info.RemoteBaseProductionRadius * Info.RemoteBaseProductionRadius;
			var candidates = facts.Skip(1)
				.Where(f => strategicMapService.TryGetGroundLandmassId(f.Location, out var landmass) && landmass != mainLandmass)
				.Where(f => RefineryBuildings.Actors.Any(r => r != null && r.IsInWorld && !r.IsDead && (r.Location - f.Location).LengthSquared <= radiusSq))
				.Select(f => new
				{
					Fact = f,
					HasWarFactory = ProductionBuildings.Actors.Any(p => p != null && p.IsInWorld && !p.IsDead && Info.WarFactoryTypes.Contains(p.Info.Name) && (p.Location - f.Location).LengthSquared <= radiusSq),
					HasBarracks = ProductionBuildings.Actors.Any(p => p != null && p.IsInWorld && !p.IsDead && Info.BarracksTypes.Contains(p.Info.Name) && (p.Location - f.Location).LengthSquared <= radiusSq)
				})
				.Where(x => economicStateService.IsProsperousOrBetter ? (!x.HasWarFactory || !x.HasBarracks) : (!x.HasWarFactory && !x.HasBarracks))
				.OrderBy(x => strategicForwardTarget.HasValue ? (x.Fact.Location - strategicForwardTarget.Value).LengthSquared : 0)
				.ThenByDescending(x => x.Fact.ActorID)
				.ToArray();

			if (candidates.Length == 0)
				return false;

			var selected = candidates[0];
			remoteFact = selected.Fact;
			if (economicStateService.IsProsperousOrBetter)
			{
				needWarFactory = !selected.HasWarFactory;
				needBarracks = !selected.HasBarracks;
			}
			else
			{
				// Growing/Struggling remote bases need one cheap local producer first.
				needBarracks = true;
			}

			return needWarFactory || needBarracks;
		}

		bool RequiresExpansionProductionPlacement(string actorType)
		{
			if (!OpeningComplete || actorType == null)
				return false;

			if (Info.WarFactoryTypes.Contains(actorType) && Info.MaximumMainBaseWarFactories >= 0)
				return CountOwned(Info.WarFactoryTypes) >= Info.MaximumMainBaseWarFactories;

			if (Info.BarracksTypes.Contains(actorType) && Info.MaximumMainBaseBarracks >= 0)
				return CountOwned(Info.BarracksTypes) >= Info.MaximumMainBaseBarracks;

			if (Info.PreferExpansionPowerPlacementAtProsperousOrBetter && Info.PowerTypes.Contains(actorType) &&
				economicStateService.IsProsperousOrBetter)
				return TryGetExpansionProductionCenter(out _);

			return false;
		}

		bool TryGetExpansionProductionCenter(out CPos center)
		{
			center = default;
			var conyards = ConstructionYardBuildings.Actors
				.Where(a => a != null && a.IsInWorld && !a.IsDead)
				.OrderBy(a => a.ActorID)
				.ToArray();
			if (conyards.Length <= 1)
				return false;

			// The oldest FACT is the permanent main base. Every later live FACT is an
			// expansion candidate. Prefer the expansion closest to the current strategic
			// front so new production capacity follows the active theatre; otherwise use
			// the newest live expansion FACT.
			var expansions = conyards.Skip(1);
			var selected = strategicForwardTarget.HasValue
				? expansions.OrderBy(a => (a.Location - strategicForwardTarget.Value).LengthSquared).ThenByDescending(a => a.ActorID).First()
				: expansions.OrderByDescending(a => a.ActorID).First();

			center = selected.Location;
			return true;
		}

		bool CanQueueProductionAtCurrentBaseState(string actorType) =>
			!RequiresExpansionProductionPlacement(actorType) || TryGetExpansionProductionCenter(out _);

		bool OpeningTargetSatisfied()
		{
			return openingStage switch
			{
				OpeningStage.Power1 => CountOwned(Info.PowerTypes) >= 1,
				OpeningStage.Barracks1 => CountOwned(Info.BarracksTypes) >= 1,
				OpeningStage.Refinery1 => CountOwned(Info.RefineryTypes) >= 1,
				OpeningStage.Refinery2 => CountOwned(Info.RefineryTypes) >= 2,
				OpeningStage.Power2 => CountOwned(Info.PowerTypes) >= 2,
				OpeningStage.WarFactory => CountOwned(Info.WarFactoryTypes) >= 1,
				OpeningStage.Repair => CountOwned(Info.RepairTypes) >= 1,
				_ => true
			};
		}

		public ActorInfo ChooseOpeningBuilding(IEnumerable<ActorInfo> buildables, string category)
		{
			if (OpeningComplete || !Info.BuildingQueues.Contains(category))
				return null;

			if (!ConstructionYardBuildings.Actors.Any(a => a.IsInWorld && !a.IsDead))
				return null;

			if (openingStructureIssued)
				return null;

			FrozenSet<string> wanted = openingStage switch
			{
				OpeningStage.Power1 => Info.PowerTypes,
				OpeningStage.Barracks1 => Info.BarracksTypes,
				OpeningStage.Refinery1 => Info.RefineryTypes,
				OpeningStage.Refinery2 => Info.RefineryTypes,
				OpeningStage.Power2 => Info.PowerTypes,
				OpeningStage.WarFactory => Info.WarFactoryTypes,
				OpeningStage.Repair => Info.RepairTypes,
				_ => null
			};
			if (wanted == null)
				return null;

			return buildables.Where(a => wanted.Contains(a.Name) && BelowLimit(a.Name))
				.OrderBy(a => a.Name)
				.FirstOrDefault();
		}

		public void NotifyOpeningBuildingQueued(string type)
		{
			if (OpeningComplete || type == null)
				return;
			openingStructureIssued = true;
			openingStructureType = type;
			openingStructureIssuedTick = world.WorldTick;
			FransBotLog.BotDebug(world, "{0}: FransBaseBuilder opening queued exactly one {1} for stage {2}.", player, type, openingStage);
		}

		public void NotifyOpeningBuildingFailed(string type)
		{
			if (OpeningComplete || openingStructureType != type)
				return;
			openingStructureIssued = false;
			openingStructureType = null;
			openingStructureIssuedTick = 0;
		}

		public CPos GetBaseCenter()
		{
			var conyard = ConstructionYardBuildings.Actors.Where(a => !a.IsDead && a.IsInWorld)
				.OrderBy(a => a.ActorID).FirstOrDefault();
			return conyard?.Location ?? initialBaseCenter;
		}
		public bool BelowLimit(string name)
		{
			if (Info.SurplusAirProductionTypes.Contains(name) && CountOwnedOrQueued(Info.SurplusAirProductionTypes) >= Info.SurplusAirProductionTarget)
				return false;
			if (Info.WarFactoryTypes.Contains(name) && CountOwnedOrQueued(Info.WarFactoryTypes) >= Info.SurplusWarFactoryTarget)
				return false;
			if (Info.BarracksTypes.Contains(name) && CountOwnedOrQueued(Info.BarracksTypes) >= Info.SurplusInfantryProductionTarget)
				return false;
			if (Info.NavalProductionTypes.Contains(name) && CountOwnedOrQueued(Info.NavalProductionTypes) >= Info.SurplusNavalProductionTarget)
				return false;

			if (!Info.BuildingLimits.TryGetValue(name, out var limit))
				return true;
			combatIntelService.EnsureCurrentSnapshot();
			var current = combatIntelService.OwnedActors.Count(a => a.Info.Name == name) +
				(BuildingsBeingProduced.TryGetValue(name, out var q) ? q : 0);
			return current < limit;
		}

		void RefreshStrategicPositioningSnapshot()
		{
			if (strategicMapService.SnapshotWorldTick < 0 ||
				strategicMapService.SnapshotWorldTick == lastStrategicSnapshotTick)
				return;

			lastStrategicSnapshotTick = strategicMapService.SnapshotWorldTick;
			var baseCenter = GetBaseCenter();
			var priorities = strategicMapService.GetStrategicPrioritySectors(6);
			var priorityOptions = priorities
				.Where(p => p.IsFrontlineSector || p.EnemyControlScore > 0 ||
					p.EnemyStrategicObjectiveCount > 0)
				.ToArray();

			CPos? proposedTarget = null;
			string proposedSource = null;
			var proposedSectorId = -1;
			var proposedScore = int.MinValue;
			var currentAnchorStillReliable = false;
			var currentAnchorRecomputedScore = strategicForwardScore;

			CPos? referenceTarget = priorityOptions.Length > 0 ? priorityOptions[0].Target : null;
			var referencePriority = priorityOptions.Length > 0 ? priorityOptions[0] : default;
			if (!referenceTarget.HasValue && strategicMapService.KnownEnemyStructures.Count > 0)
				referenceTarget = strategicMapService.KnownEnemyStructures
					.OrderBy(e => (e.LastKnownLocation - baseCenter).LengthSquared)
					.ThenBy(e => e.ActorId)
					.First().LastKnownLocation;

			var commanderTarget = default(CPos);
			var referenceFromCommander = groundCommanderService != null &&
				groundCommanderService.TryGetGroundDemandPoint(out commanderTarget, out _, out _);
			if (referenceFromCommander)
				referenceTarget = commanderTarget;

			if (referenceTarget.HasValue)
			{
				var forwardVector = referenceTarget.Value - baseCenter;
				HashSet<int> routeSectorIds = null;
				if (strategicMapService.TryGetStrategicSectorRoute(
					baseCenter, referenceTarget.Value, FransStrategicMovementLayer.Ground,
					FransStrategicRoutePolicy.Assault, out var routeWaypoints))
				{
					routeSectorIds = [];
					foreach (var waypoint in routeWaypoints)
						if (strategicMapService.TryGetSector(waypoint, out var routeSector))
							routeSectorIds.Add(routeSector.Id);
					if (strategicMapService.TryGetSector(baseCenter, out var baseSector))
						routeSectorIds.Add(baseSector.Id);
					if (strategicMapService.TryGetSector(referenceTarget.Value, out var targetSector))
						routeSectorIds.Add(targetSector.Id);
				}

				var chokeOptions = strategicMapService.Sectors
					.Where(sector => sector != null && sector.GroundCenter.HasValue && sector.TotalCellCount > 0 &&
						sector.Id >= 0 && sector.Id < strategicMapService.SectorMetrics.Count &&
						sector.KnownCellCount * 100 / sector.TotalCellCount >= Info.StrategicChokeMinimumKnowledgePercent)
					.Select(sector =>
					{
						var metrics = strategicMapService.SectorMetrics[sector.Id];
						var vector = sector.GroundCenter.Value - baseCenter;
						var sameDirection = (long)vector.X * forwardVector.X + (long)vector.Y * forwardVector.Y > 0;
						var onAssaultRoute = routeSectorIds == null || routeSectorIds.Count == 0 || routeSectorIds.Contains(sector.Id);
						var score =
							metrics.GroundChokeScore * 20 +
							(metrics.IsGroundArticulationPoint ? 1000 : 0) +
							metrics.FrontlineScore * 5 +
							metrics.EnemyControlScore * 2 -
							vector.Length * 3 -
							(sector.GroundCenter.Value - referenceTarget.Value).Length * 2;
						return (Sector: sector, Metrics: metrics, SameDirection: sameDirection, OnAssaultRoute: onAssaultRoute, Score: score);
					})
					.Where(x => x.SameDirection && x.OnAssaultRoute && x.Metrics.GroundChokeScore > 0)
					.OrderByDescending(x => x.Score)
					.ThenByDescending(x => x.Metrics.IsGroundArticulationPoint)
					.ThenBy(x => (x.Sector.GroundCenter.Value - baseCenter).LengthSquared)
					.ThenBy(x => x.Sector.Id)
					.ToArray();

				var choke = chokeOptions.FirstOrDefault();
				if (choke.Sector != null)
				{
					proposedTarget = choke.Sector.GroundCenter.Value;
					proposedSectorId = choke.Sector.Id;
					proposedScore = choke.Score;
					var knowledge = choke.Sector.KnownCellCount * 100 / choke.Sector.TotalCellCount;
					proposedSource = $"choke sector {choke.Sector.Id}, choke {choke.Metrics.GroundChokeScore}, articulation {choke.Metrics.IsGroundArticulationPoint}, knowledge {knowledge}%";
				}
				else
				{
					proposedTarget = referenceTarget;
					proposedSectorId = !referenceFromCommander && priorityOptions.Length > 0 ? referencePriority.SectorId : -1;
					proposedScore = referenceFromCommander ? 5000 : priorityOptions.Length > 0 ? referencePriority.TotalScore * 10 : 0;
					proposedSource = referenceFromCommander
						? "active Ground Commander objective"
						: priorityOptions.Length > 0
							? $"strategic priority sector {referencePriority.SectorId}"
							: "remembered enemy structure";
				}

				if (strategicForwardTarget.HasValue && strategicForwardSectorId >= 0)
				{
					var current = chokeOptions.FirstOrDefault(x => x.Sector.Id == strategicForwardSectorId);
					if (current.Sector != null)
					{
						currentAnchorStillReliable = true;
						currentAnchorRecomputedScore = current.Score;
						strategicLastReliableTick = world.WorldTick;
					}
				}
			}

			// Same anchor: refresh confidence without generating a new revision or new rally orders.
			var sameAnchor = proposedTarget.HasValue && strategicForwardTarget.HasValue &&
				((proposedSectorId >= 0 && proposedSectorId == strategicForwardSectorId) ||
					proposedTarget.Value == strategicForwardTarget.Value);
			if (sameAnchor)
			{
				strategicForwardScore = proposedScore;
				strategicLastReliableTick = world.WorldTick;
				return;
			}

			if (strategicForwardTarget.HasValue)
			{
				var heldTicks = strategicAnchorChangedTick < 0 ? int.MaxValue : world.WorldTick - strategicAnchorChangedTick;
				var withinMinimumHold = heldTicks < Info.StrategicAnchorMinimumHoldTicks;

				// A valid current choke is intentionally sticky. This prevents adjacent sectors
				// with nearly equal scores from making producer rally directions oscillate.
				if (currentAnchorStillReliable)
				{
					strategicForwardScore = currentAnchorRecomputedScore;
					var movementPenalty = proposedTarget.HasValue
						? (proposedTarget.Value - strategicForwardTarget.Value).Length * Info.StrategicAnchorSwitchDistancePenaltyPerCell
						: 0;
					var requiredSwitchMargin = Info.StrategicAnchorSwitchScoreMargin + movementPenalty;
					if (withinMinimumHold ||
						(proposedTarget.HasValue && proposedScore < currentAnchorRecomputedScore + requiredSwitchMargin))
						return;
				}
				else
				{
					var recentlyReliable = strategicLastReliableTick >= 0 &&
						world.WorldTick - strategicLastReliableTick <= Info.StrategicAnchorLostGraceTicks;
					if (withinMinimumHold || (!proposedTarget.HasValue && recentlyReliable))
						return;
				}
			}

			if (proposedTarget.HasValue)
			{
				strategicForwardTarget = proposedTarget;
				strategicForwardSource = proposedSource;
				strategicForwardSectorId = proposedSectorId;
				strategicForwardScore = proposedScore;
				strategicAnchorChangedTick = world.WorldTick;
				strategicLastReliableTick = world.WorldTick;
				strategicAnchorRevision++;

				FransBotLog.BotDebug(world,
					"{0}: Strategic Positioning stable front anchor {1} from {2}; revision {3}. BARR/TENT/WEAP and defenses use this strategic direction; physical producer rally points are resolved separately onto open forward cells.",
					player, strategicForwardTarget.Value, strategicForwardSource, strategicAnchorRevision);
			}
			else if (strategicForwardTarget.HasValue)
			{
				strategicForwardTarget = null;
				strategicForwardSource = null;
				strategicForwardSectorId = -1;
				strategicForwardScore = int.MinValue;
				strategicAnchorChangedTick = world.WorldTick;
				strategicAnchorRevision++;

				FransBotLog.BotDebug(world,
					"{0}: Strategic Positioning stable front anchor expired after hysteresis; using baseline placement/rally fallback (revision {1}).",
					player, strategicAnchorRevision);
			}
		}

		bool UseDirectionalPlacement() =>
			Info.DirectionalPlacementChance >= 100 ||
			(Info.DirectionalPlacementChance > 0 && world.LocalRandom.Next(100) < Info.DirectionalPlacementChance);

		CPos StrategicRearTarget(CPos baseCenter)
		{
			if (!strategicForwardTarget.HasValue)
				return baseCenter;

			var forward = strategicForwardTarget.Value - baseCenter;
			var bounds = world.Map.Bounds;
			return new CPos(
				Math.Clamp(baseCenter.X - forward.X, bounds.Left, bounds.Right - 1),
				Math.Clamp(baseCenter.Y - forward.Y, bounds.Top, bounds.Bottom - 1));
		}

		bool TryGetEnemyBaseDirectionTarget(out CPos target, out string source)
		{
			var known = strategicMapService.KnownEnemyStructures
				.Where(s => s.ConfidencePercent >= Info.EnemyBaseDirectionMinimumConfidencePercent)
				.ToArray();
			var construction = known.Where(s => s.Category == FransKnownStructureCategory.Construction)
				.OrderByDescending(s => s.ConfidencePercent).ThenByDescending(s => s.LastSeenWorldTick).ThenBy(s => s.ActorId).FirstOrDefault();
			if (construction.ActorId != 0)
			{
				target = construction.LastKnownLocation;
				source = $"remembered enemy construction {construction.ActorType} ({construction.ConfidencePercent}% confidence)";
				return true;
			}

			var cluster = known.Where(s => s.Category is FransKnownStructureCategory.Production or FransKnownStructureCategory.Economy or FransKnownStructureCategory.Strategic)
				.OrderByDescending(s => s.ConfidencePercent).ThenByDescending(s => s.LastSeenWorldTick).Take(6).ToArray();
			if (cluster.Length > 0)
			{
				target = new CPos((int)Math.Round(cluster.Average(s => s.LastKnownLocation.X)), (int)Math.Round(cluster.Average(s => s.LastKnownLocation.Y)));
				source = $"centroid of {cluster.Length} legitimately remembered enemy base/economy structure(s)";
				return true;
			}

			if (strategicForwardTarget.HasValue)
			{
				target = strategicForwardTarget.Value;
				source = "stable StrategicMap front anchor";
				return true;
			}

			target = default;
			source = null;
			return false;
		}

		int ProductionDirectionWeight(string actorType)
		{
			if (Info.WarFactoryTypes.Contains(actorType))
				return Info.WarFactoryEnemyDirectionWeightPercent;
			if (Info.BarracksTypes.Contains(actorType))
				return Info.BarracksEnemyDirectionWeightPercent;
			return 0;
		}

		bool IntersectsGroundStagingReservation(CPos cell, BuildingInfo buildingInfo) =>
			buildingInfo != null && groundCommanderService != null &&
			groundCommanderService.IntersectsGroundStagingReservation(cell, buildingInfo.Dimensions.X, buildingInfo.Dimensions.Y);

		bool CanDisplaceBuildingBlocker(Actor actor)
		{
			if (actor == null || !actor.IsInWorld || actor.IsDead || actor.Owner != player || !actor.IsIdle ||
				actor.TraitOrDefault<Mobile>() == null || actor.TraitOrDefault<Aircraft>() != null ||
				actor.TraitOrDefault<Harvester>() != null || actor.TraitOrDefault<Minelayer>() != null ||
				actor.Info.TraitInfos<CargoInfo>().Any() || actor.Info.TraitInfos<CapturesInfo>().Any() ||
				actor.Info.TraitInfos<TransformsInfo>().Any())
				return false;
			if (groundUnitReservationService != null && groundUnitReservationService.IsGroundUnitReserved(actor))
				return false;
			if (captureSecurityServices != null && captureSecurityServices.Any(s => s.IsCaptureMissionActor(actor)))
				return false;
			if (transportService != null && transportService.IsTransportReserved(actor))
				return false;
			return true;
		}

		bool QueueBuildingBlockerRiskAwareMove(Actor actor, CPos destination)
		{
			var mobile = actor?.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused || mobile.PathFinder is not PathFinder actorPathFinder)
				return false;
			int CustomCost(CPos cell) => cell == mobile.ToCell ? 0 : riskModelService.GetPathCost(actor, cell, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced);
			var initialPath = actorPathFinder.FindPathToTargetCell(actor, [mobile.ToCell], destination, BlockedByActor.Immovable, CustomCost, laneBias: false);
			if (initialPath == null || initialPath.Count == 0 || riskModelService.EvaluateRoute(actor, initialPath, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced).IsCritical)
				return false;
			actor.QueueActivity(false, new Move(actor, check =>
			{
				if (mobile.ToCell == destination)
					return (true, new List<CPos>());
				if (mobile.PathFinder is not PathFinder dynamicPathFinder)
					return (false, new List<CPos>());
				var path = dynamicPathFinder.FindPathToTargetCell(actor, [mobile.ToCell], destination, check, CustomCost, laneBias: false);
				return (false, path);
			}));
			return true;
		}

		void TickRallyPoints(IBot bot)
		{
			if (--assignRallyPointsTicks <= 0)
			{
				assignRallyPointsTicks = Math.Max(2, Info.AssignRallyPointsInterval);
				foreach (var rp in world.ActorsWithTrait<RallyPoint>().Where(rp => rp.Actor.Owner == player).OrderBy(rp => rp.Actor.ActorID))
				rallyPoints.Push(rp);
			}
			else
			{
				var updateCount = Exts.IntegerDivisionRoundingAwayFromZero(rallyPoints.Count, assignRallyPointsTicks);
				for (var i = 0; i < updateCount && rallyPoints.Count > 0; i++)
				{
					var rp = rallyPoints.Pop();
					if (rp.Actor.Owner == player && !rp.Actor.Disposed)
						SetRallyPoint(bot, rp);
				}
			}
		}

		void UpdateBestResourceBase()
		{
			if (--checkBestResourceLocationTicks > 0 || resourceLayer == null)
				return;
			checkBestResourceLocationTicks = Info.CheckBestResourceLocationInterval;

			if (ResourceMapModule != null)
				foreach (var mcv in RequestedRefineries.Keys.ToList())
					if (ResourceMapModule.FindClosestIndiceFromCPos(RequestedRefineries[mcv].ResourceLoc).PlayerRefineryCount >= Info.MaxRefineryPerIndice)
						RequestedRefineries.Remove(mcv);

			Actor bestConyard = null;
			var bestScore = int.MinValue;
			foreach (var conyard in ConstructionYardBuildings.Actors.Where(a => !a.IsDead && a.IsInWorld).OrderBy(a => a.ActorID))
			{
				if (!world.Map.FindTilesInAnnulus(conyard.Location, Info.MinBaseRadius, Info.MaxBaseRadius)
					.Any(c => ResourceMapModule != null ? ResourceMapModule.Info.ValuableResourceTypes.Contains(resourceLayer.GetResource(c).Type) : resourceLayer.GetResource(c).Type != null))
					continue;
				var refs = world.FindActorsInCircle(conyard.CenterPosition, WDist.FromCells(Info.MaxBaseRadius))
					.Count(a => a.Owner == player && Info.RefineryTypes.Contains(a.Info.Name));
				// Resource-base selection must never inspect hidden actors directly. The unified
				// RiskModel already combines only fair visible/memorized/strategic evidence.
				var localRisk = riskModelService.EvaluateStrategicCell(conyard.Location,
					FransRiskRole.BuildingPlacement, FransRiskTolerance.Cautious);
				var score = -localRisk.Score - refs * 25;
				if (score > bestScore)
				{
					bestScore = score;
					bestConyard = conyard;
				}
			}
			ResourceConyardCenter = bestConyard?.Location;
		}

		void RefreshBuildingsBeingProduced()
		{
			BuildingsBeingProduced.Clear();
			if (playerResources.GetCashAndResources() < Info.ProductionMinCashRequirement)
				return;
			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			foreach (var builder in builders)
				foreach (var queue in queuesByCategory[builder.Category])
				{
					var producing = queue.AllQueued().FirstOrDefault();
					if (producing == null) continue;
					BuildingsBeingProduced[producing.Item] = BuildingsBeingProduced.TryGetValue(producing.Item, out var n) ? n + 1 : 1;
				}
		}

		void RefreshRadarTechDecision()
		{
			if (lastRadarDecisionTick != int.MinValue && world.WorldTick - lastRadarDecisionTick < Info.RadarDecisionInterval)
				return;

			lastRadarDecisionTick = world.WorldTick;
			radarDecisionAllowed = false;
			radarDecisionEnemyTechResponse = false;

			if (!OpeningComplete)
			{
				radarDecisionReason = "Fransbot opening is still active";
				return;
			}

			if (CountOwned(Info.RadarTypes) > 0 || Info.RadarTypes.Any(IsQueued))
			{
				radarDecisionReason = "Radar Dome already owned/queued";
				return;
			}

			var localPressure = 0;
			var visiblePressure = 0;
			var rememberedPressureUnits = 0;
			if (combatIntelService.SnapshotWorldTick >= 0)
				localPressure = combatIntelService.EstimateEnemyCombatValueNear(GetBaseCenter(), Info.RadarPressureRadiusCells, null, out visiblePressure, out rememberedPressureUnits);

			var recentEconomicAttack = lastRadarEconomicAttackTick != int.MinValue &&
				world.WorldTick - lastRadarEconomicAttackTick < Info.RadarRecentEconomicAttackHoldTicks;
			var enemyDefenseObserved = HasLegitimatelyObservedEnemyDefense();
			var enemyAirThreatObserved = HasLegitimatelyObservedEnemyAirThreat();
			var enemyTechObserved = HasLegitimatelyObservedEnemyRadarTech();
			var physicalRadarMaturity = CountOwned(Info.RefineryTypes) >= 3 && CountOwned(Info.HarvesterTypes) >= 3;

			if (economicStateService.IsStruggling && !physicalRadarMaturity)
			{
				radarDecisionReason = $"shared economy state {economicStateService.State}: optional Radar waits for Growing or physical maturity of at least 3 PROC + 3 HARV";
				LogRadarDecisionIfUseful(localPressure, visiblePressure, rememberedPressureUnits, recentEconomicAttack);
				return;
			}

			if (localPressure >= Info.RadarCriticalPressureValue ||
				(recentEconomicAttack && localPressure >= Info.RadarHighPressureValue))
			{
				radarDecisionReason = $"Radar maturity gate is satisfied, but immediate survival pressure is too high (local value {localPressure}, recent eco attack {recentEconomicAttack})";
				LogRadarDecisionIfUseful(localPressure, visiblePressure, rememberedPressureUnits, recentEconomicAttack);
				return;
			}

			radarDecisionAllowed = true;
			radarDecisionEnemyTechResponse = enemyDefenseObserved || enemyAirThreatObserved || enemyTechObserved;


			var observedReason = enemyAirThreatObserved ? "enemy air observed" :
				enemyDefenseObserved ? "enemy defenses observed" :
				enemyTechObserved ? "enemy advanced tech observed" : "normal Radar tech progression";
			var maturityReason = economicStateService.IsStruggling
				? "physical maturity fallback is satisfied with at least 3 PROC + 3 HARV despite Struggling"
				: "shared economy is Growing or better";
			radarDecisionReason = $"{observedReason}; {maturityReason}; local pressure {localPressure}";
			LogRadarDecisionIfUseful(localPressure, visiblePressure, rememberedPressureUnits, recentEconomicAttack);
		}

		bool HasLegitimatelyObservedEnemyDefense()
		{
			foreach (var enemy in combatIntelService.VisibleEnemies)
				{
					if (enemy == null || enemy.IsDead || !enemy.IsInWorld)
						continue;
					if (Info.RadarEnemyDefenseTypes.Contains(enemy.Info.Name))
						return true;
				}

			return strategicMapService.KnownEnemyStructures.Any(s =>
					s.ConfidencePercent >= Info.RadarEnemyTechMemoryConfidencePercent &&
					(s.Category == FransKnownStructureCategory.Defense || Info.RadarEnemyDefenseTypes.Contains(s.ActorType)));
		}

		bool HasLegitimatelyObservedEnemyAirThreat()
		{
			foreach (var enemy in combatIntelService.VisibleEnemies)
				{
					if (enemy == null || enemy.IsDead || !enemy.IsInWorld)
						continue;
					if (Info.RadarEnemyAirThreatTypes.Contains(enemy.Info.Name))
						return true;
				}

			return strategicMapService.KnownEnemyStructures.Any(s =>
					s.ConfidencePercent >= Info.RadarEnemyTechMemoryConfidencePercent &&
					Info.RadarEnemyAirThreatTypes.Contains(s.ActorType));
		}

		bool HasLegitimatelyObservedEnemyRadarTech()
		{
			foreach (var enemy in combatIntelService.VisibleEnemies)
				{
					if (enemy == null || enemy.IsDead || !enemy.IsInWorld)
						continue;
					if (Info.RadarEnemyTechTypes.Contains(enemy.Info.Name))
						return true;
				}

			return strategicMapService.KnownEnemyStructures.Any(s =>
					s.ConfidencePercent >= Info.RadarEnemyTechMemoryConfidencePercent &&
					Info.RadarEnemyTechTypes.Contains(s.ActorType));
		}

		void LogRadarDecisionIfUseful(int localPressure, int visiblePressure, int rememberedPressureUnits, bool recentEconomicAttack)
		{
			var state = $"{radarDecisionAllowed}/{radarDecisionEnemyTechResponse}/{radarDecisionReason}";
			if (state == lastRadarDecisionLoggedState && world.WorldTick - lastRadarDecisionLogTick < 1500)
				return;

			lastRadarDecisionLoggedState = state;
			lastRadarDecisionLogTick = world.WorldTick;
			FransBotLog.BotDebug(world,
				"{0}: Radar Tech Decision: {1}; allowed {2}, parity {3}, pressure {4} (visible {5}, remembered units {6}), recent economy attack {7}.",
				player, radarDecisionReason, radarDecisionAllowed, radarDecisionEnemyTechResponse, localPressure, visiblePressure, rememberedPressureUnits, recentEconomicAttack);
		}

		public bool RadarTechAllowed(out bool enemyTechResponse, out string reason)
		{
			RefreshRadarTechDecision();
			enemyTechResponse = radarDecisionEnemyTechResponse;
			reason = radarDecisionReason;
			return radarDecisionAllowed;
		}

		public bool ShouldExploitRadarWithAirProduction()
		{
			if (!OpeningComplete || CountOwned(Info.RadarTypes) == 0 ||
				CountOwned(Info.RadarFollowupAirProductionTypes) > 0)
				return false;

			// Radar may legitimately exist while the throughput detector is still Struggling.
			// Do not leave that physical tech investment dead: one first AFLD/HPAD may use the same
			// kind of physical-economy maturity fallback. This exception is ONLY for the first air
			// producer; normal producer growth remains governed by the existing economy-state rules.
			var physicalMaturity = CountOwned(Info.RefineryTypes) >= Info.FirstAirProductionMinimumRefineries &&
				CountOwned(Info.HarvesterTypes) >= Info.FirstAirProductionMinimumHarvesters;
			if (economicStateService.IsStruggling &&
				(!Info.FirstAirProductionAllowPhysicalMaturityFallback || !physicalMaturity))
				return false;

			var localPressure = 0;
			if (combatIntelService.SnapshotWorldTick >= 0)
				localPressure = combatIntelService.EstimateEnemyCombatValueNear(GetBaseCenter(), Info.RadarPressureRadiusCells, null, out _, out _);

			return localPressure < Info.FirstAirProductionMaximumLocalPressureValue;
		}

		void TickOneBuilder(IBot bot)
		{
			if (builders.Length == 0)
				return;
			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			var found = false;
			for (var i = 0; i < builders.Length; i++)
			{
				currentBuilderIndex = (currentBuilderIndex + 1) % builders.Length;
				--builders[currentBuilderIndex].WaitTicks;
				if (queuesByCategory[builders[currentBuilderIndex].Category].Any())
				{
					found = true;
					break;
				}
			}
			if (found)
				builders[currentBuilderIndex].Tick(bot, queuesByCategory);
		}

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			if (e.Attacker == null || e.Attacker.Disposed || e.Attacker.Owner.RelationshipWith(self.Owner) != PlayerRelationship.Enemy ||
				!e.Attacker.Info.HasTraitInfo<ITargetableInfo>())
				return;

			if (Info.HarvesterTypes.Contains(self.Info.Name) || Info.RefineryTypes.Contains(self.Info.Name) ||
				Info.ProductionTypes.Contains(self.Info.Name))
				lastRadarEconomicAttackTick = world.WorldTick;


			// Being hit is fair information, but a hidden attacker must not leak its live
			// position into defense placement. Anchor at the victim's own cell instead
			// (same fog convention as FransMinelayerBotModule.RespondToAttack).
			if (self.Info.HasTraitInfo<BuildingInfo>())
			{
				var defenseCenter = e.Attacker.CanBeViewedByPlayer(player) &&
					e.Attacker.IsInWorld && !e.Attacker.IsDead && e.Attacker.OccupiesSpace != null
					? e.Attacker.Location
					: self.Location;
				foreach (var n in positionsUpdatedModules)
					n.UpdatedDefenseCenter(defenseCenter);
			}
		}

		void SetRallyPoint(IBot bot, TraitPair<RallyPoint> rp)
		{
			var strategicRally = TryGetRallyDirectionTarget(out _) && Info.ForwardStructureTypes.Contains(rp.Actor.Info.Name);
			if (strategicRally)
			{
				var desired = ChooseRallyLocationNear(rp.Actor);
				var needsStrategicUpdate = rp.Trait.Path.Count == 0 || rp.Trait.Path[0] != desired;
				if (!needsStrategicUpdate)
				{
					var locomotors = LocomotorsForProducibles(rp.Actor);
					needsStrategicUpdate = !IsRallyPointValid(rp.Actor.Location, rp.Trait.Path[0], locomotors, rp.Actor.Info.TraitInfoOrDefault<BuildingInfo>());
				}

				if (needsStrategicUpdate)
					bot.QueueOrder(new Order("SetRallyPoint", rp.Actor, Target.FromCell(world, desired), false) { SuppressVisualFeedback = true });
				return;
			}

			var needs = rp.Trait.Path.Count == 0;
			if (!needs)
			{
				var locomotors = LocomotorsForProducibles(rp.Actor);
				needs = !IsRallyPointValid(rp.Actor.Location, rp.Trait.Path[0], locomotors, rp.Actor.Info.TraitInfoOrDefault<BuildingInfo>());
			}
			if (needs)
				bot.QueueOrder(new Order("SetRallyPoint", rp.Actor, Target.FromCell(world, ChooseRallyLocationNear(rp.Actor)), false) { SuppressVisualFeedback = true });
		}

		CPos ChooseRallyLocationNear(Actor producer)
		{
			var locomotors = LocomotorsForProducibles(producer);
			var possible = world.Map.FindTilesInCircle(producer.Location, Info.RallyPointScanRadius)
				.Where(c => IsRallyPointValid(producer.Location, c, locomotors, producer.Info.TraitInfoOrDefault<BuildingInfo>()))
				.Where(c => !riskModelService.EvaluateStrategicCell(c, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced).IsCritical)
				.ToList();
			if (possible.Count == 0)
				return producer.Location;

			// Ground Commander objective is the primary rally direction while a real MOVE/FIGHT/DEFEND mission exists.
			// Otherwise the stable strategic front is used. Rally is only a local producer exit hint; it never owns units.
			if (!TryGetRallyDirectionTarget(out var rallyTarget) || !Info.ForwardStructureTypes.Contains(producer.Info.Name))
				return possible.Random(world.LocalRandom);

			var forward = rallyTarget - producer.Location;
			var minDistanceSquared = Info.StrategicRallyMinimumDistance * Info.StrategicRallyMinimumDistance;
			var strategic = possible
				.Where(c => (c - producer.Location).LengthSquared >= minDistanceSquared)
				.Select(c =>
				{
					var delta = c - producer.Location;
					var projection = (long)delta.X * forward.X + (long)delta.Y * forward.Y;
					var risk = riskModelService.EvaluateStrategicCell(c, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced);
					var score = projection * 100 + delta.LengthSquared * 5 -
						(c - rallyTarget).LengthSquared - risk.Score * 20L;
					return (Cell: c, Score: score);
				})
				.Where(x => x.Score > 0)
				.OrderByDescending(x => x.Score)
				.ThenBy(x => x.Cell.X)
				.ThenBy(x => x.Cell.Y)
				.Take(Info.StrategicRallyCandidateCount)
				.Select(x => x.Cell)
				.ToArray();

			if (strategic.Length == 0)
				return possible.Random(world.LocalRandom);

			return strategic[(int)(producer.ActorID % (uint)strategic.Length)];
		}

		bool TryGetRallyDirectionTarget(out CPos target)
		{
			if (groundCommanderService != null &&
				groundCommanderService.TryGetGroundDemandPoint(out target, out _, out _))
				return true;

			if (strategicForwardTarget.HasValue)
			{
				target = strategicForwardTarget.Value;
				return true;
			}

			target = default;
			return false;
		}

		Locomotor[] LocomotorsForProducibles(Actor producer)
		{
			var productions = producer.TraitsImplementing<Production>();
			if (!productions.Any())
				productions = producer.World.ActorsWithTrait<Production>().Where(x => x.Actor.Owner != producer.Owner).Select(x => x.Trait);
			var produces = productions.SelectMany(p => p.Info.Produces).ToHashSet();
			if (produces.Count == 0) return Array.Empty<Locomotor>();
			var queues = producer.TraitsImplementing<ProductionQueue>();
			if (!queues.Any()) queues = producer.Owner.PlayerActor.TraitsImplementing<ProductionQueue>();
			var locomotorNames = queues.Where(q => produces.Contains(q.Info.Type)).SelectMany(q => q.BuildableItems())
				.Select(p => p.TraitInfoOrDefault<MobileInfo>()).Where(mi => mi != null).Select(mi => mi.Locomotor).ToHashSet();
			return world.WorldActor.TraitsImplementing<Locomotor>().Where(l => locomotorNames.Contains(l.Info.Name)).ToArray();
		}

		bool IsRallyPointValid(CPos producerLocation, CPos rallyPointLocation, Locomotor[] locomotors, BuildingInfo buildingInfo)
		{
			if (expansionStateService != null &&
				expansionStateService.TryGetMcvDeployRightOfWay(out var mcvCenter, out var mcvRadius) &&
				(rallyPointLocation - mcvCenter).LengthSquared <= mcvRadius * mcvRadius)
				return false;

			return (pathFinder == null || locomotors.All(l =>
				pathFinder.PathMightExistForLocomotorBlockedByImmovable(l, producerLocation, rallyPointLocation))) &&
				(buildingInfo == null || world.IsCellBuildable(rallyPointLocation, rallyPointLocation, null, buildingInfo));
		}

		void RefreshOreMineRefineryClaim()
		{
			if (!oreMineRefineryTarget.HasValue || oreEconomyService == null)
				return;

			var mine = oreMineRefineryTarget.Value;
			if (!oreEconomyService.UnpairedMineLocations.Contains(mine))
			{
				FransBotLog.BotDebug(world,
					"{0}: ore-node PROC claim for mine {1} released only after FransHarvester verified that the mine is physically paired.", player, mine);
				oreMineRefineryTarget = null;
				oreMineRefineryClaimTick = -1;
				return;
			}

			if (oreMineRefineryClaimTick < 0 || world.WorldTick - oreMineRefineryClaimTick < Info.OreMineRefineryClaimRecoveryTimeout)
				return;

			var refineryWorkPending = Info.RefineryTypes.Any(IsQueued) ||
				BuildingsBeingProduced.Any(kv => Info.RefineryTypes.Contains(kv.Key) && kv.Value > 0);
			if (refineryWorkPending)
				return;

			var radiusSq = oreEconomyService.ResourceControlRadius * oreEconomyService.ResourceControlRadius;
			var physicalInRadius = RefineryBuildings.Actors.Any(a => a != null && a.IsInWorld && !a.IsDead &&
				(a.Location - mine).LengthSquared <= radiusSq);
			FransBotLog.BotDebug(world,
				physicalInRadius
					? "{0}: stale ore-node PROC claim for mine {1} recovered after {2} WT: FransHarvester still reports this mine unpaired despite a physical PROC inside control radius, so that PROC must currently be paired elsewhere. Mine may be reconsidered."
					: "{0}: stale ore-node PROC claim for mine {1} recovered after {2} WT because no physical in-radius PROC and no queued/in-production refinery remains. Mine may be reconsidered.",
				player, mine, world.WorldTick - oreMineRefineryClaimTick);
			oreMineRefineryTarget = null;
			oreMineRefineryClaimTick = -1;
		}

		bool TryGetMineNeedingRefinery(string refineryType, out CPos mineLocation)
		{
			mineLocation = default;
			if (oreMineRefineryTarget.HasValue)
				return false;
			if (!OpeningMcvCompleted || oreEconomyService == null || oreEconomyService.UnpairedMineLocations.Count == 0 ||
				string.IsNullOrEmpty(refineryType) || !world.Map.Rules.Actors.ContainsKey(refineryType))
				return false;

			var yards = ConstructionYardBuildings.Actors
				.Where(a => a != null && a.IsInWorld && !a.IsDead && a.OccupiesSpace != null)
				.OrderBy(a => a.ActorID)
				.ToArray();
			if (yards.Length == 0)
				return false;

			// one ore-mine -> one physical PROC is a placement invariant, not only a
			// production intention. Do not queue a PROC merely because a FACT is vaguely nearby.
			// The exact actor footprint must have at least one legal, non-critical cell that is
			// BOTH inside native build radius and inside FransHarvester's ResourceControlRadius.
			// Mines without such a site are left to autonomous MCV expansion instead of creating
			// an endless stream of refineries that never pair with the requested mine.
			foreach (var mine in oreEconomyService.UnpairedMineLocations
				.OrderBy(m => yards.Min(y => (y.Location - m).LengthSquared))
				.ThenBy(m => m.X)
				.ThenBy(m => m.Y))
			{
				if (!HasLegalOreMineRefineryPlacement(refineryType, mine, yards))
					continue;

				mineLocation = mine;
				return true;
			}

			return false;
		}

		bool HasLegalOreMineRefineryPlacement(string refineryType, CPos mineLocation, IReadOnlyCollection<Actor> yards)
		{
			var actorInfo = world.Map.Rules.Actors[refineryType];
			var buildingInfo = actorInfo.TraitInfoOrDefault<BuildingInfo>();
			if (buildingInfo == null)
				return false;

			var controlRadiusSquared = oreEconomyService.ResourceControlRadius * oreEconomyService.ResourceControlRadius;
			foreach (var yard in yards)
				foreach (var cell in world.Map.FindTilesInAnnulus(yard.Location, Info.MinBaseRadius, Info.MaxBaseRadius)
					.Where(c => (c - mineLocation).LengthSquared <= controlRadiusSquared)
					.OrderBy(c => (c - mineLocation).LengthSquared)
					.ThenBy(c => (c - yard.Location).LengthSquared)
					.ThenBy(c => c.X)
					.ThenBy(c => c.Y))
				{
					if (IntersectsGroundStagingReservation(cell, buildingInfo) ||
						!world.CanPlaceBuilding(cell, actorInfo, buildingInfo, null) ||
						!buildingInfo.IsCloseEnoughToBase(world, player, actorInfo, null, cell))
						continue;

					if (riskModelService.EvaluateStrategicCell(
						cell, FransRiskRole.BuildingPlacement, FransRiskTolerance.Cautious).IsCritical)
						continue;

					return true;
				}

			return false;
		}

		public bool HasAdequateRefineryCount() => Info.RefineryTypes.Count == 0 || AIUtils.CountActorByCommonName(RefineryBuildings) >= OptimalRefineryCount() ||
			AIUtils.CountActorByCommonName(powerBuildings) == 0 || AIUtils.CountActorByCommonName(ConstructionYardBuildings) == 0;
		int OptimalRefineryCount() => AIUtils.CountActorByCommonName(ProductionBuildings) > 0 ? Info.InitialMinimumRefineryCount + Info.AdditionalMinimumRefineryCount : Info.InitialMinimumRefineryCount;
		bool HasMinimalRefineryCount() => AIUtils.CountActorByCommonName(RefineryBuildings) >= Info.InitialMinimumRefineryCount;

		List<MiniYamlNode> IGameSaveTraitData.IssueTraitData(Actor self)
		{
			if (IsTraitDisabled) return null;
			return [new("InitialBaseCenter", FieldSaver.FormatValue(initialBaseCenter)), new("DefenseCenter", FieldSaver.FormatValue(DefenseCenter))];
		}

		void IGameSaveTraitData.ResolveTraitData(Actor self, MiniYaml data)
		{
			if (self.World.IsReplay) return;
			var initial = data.NodeWithKeyOrDefault("InitialBaseCenter");
			if (initial != null) initialBaseCenter = FieldLoader.GetValue<CPos>("InitialBaseCenter", initial.Value.Value);
			var defense = data.NodeWithKeyOrDefault("DefenseCenter");
			if (defense != null) DefenseCenter = FieldLoader.GetValue<CPos>("DefenseCenter", defense.Value.Value);
		}

		void SellUselessRefinery(IBot bot)
		{
			// Never undo active Struggling recovery by selling freshly added resource throughput.
			// Normal proximity/no-resource cleanup resumes after the measured economy stabilizes.
			if (economicStateService?.IsStruggling == true)
				return;

			var refineries = world.ActorsHavingTrait<Refinery>().Where(a => a.Owner == player).OrderBy(a => a.ActorID).ToArray();
			if (refineries.Length <= Info.InitialMinimumRefineryCount + Info.AdditionalMinimumRefineryCount) return;
			for (var i = 0; i < refineries.Length; i++)
			{
				for (var j = i + 1; j < refineries.Length; j++)
					if ((refineries[i].Location - refineries[j].Location).LengthSquared <= Info.SellRefineryTooCloseCellDistance * Info.SellRefineryTooCloseCellDistance)
					{
						bot.QueueOrder(new Order("Sell", refineries[i], Target.FromActor(refineries[i]), false));
						return;
					}
				if (ResourceMapModule != null && resourceLayer != null &&
					!world.Map.FindTilesInAnnulus(refineries[i].Location, 0, Info.SellRefineryNoResourceDistance).Any(c => ResourceMapModule.Info.ValuableResourceTypes.Contains(resourceLayer.GetResource(c).Type)) &&
					!world.FindActorsInCircle(refineries[i].CenterPosition, WDist.FromCells(Info.SellRefineryNoResourceDistance)).Any(a => ResourceMapModule.Info.ResourceCreatorTypes.Contains(a.Info.Name)))
				{
					bot.QueueOrder(new Order("Sell", refineries[i], Target.FromActor(refineries[i]), false));
					return;
				}
			}
		}

		void INotifyActorDisposing.Disposing(Actor self)
		{
			RefineryBuildings.Dispose(); powerBuildings.Dispose(); ConstructionYardBuildings.Dispose(); ProductionBuildings.Dispose();
		}

		void IBotSuggestRefineryProduction.RequestLocation(CPos refineryLocation, CPos conyardLocation, Actor expandActor)
		{
			if (ResourceMapModule == null || ResourceMapModule.FindClosestIndiceFromCPos(refineryLocation).PlayerRefineryCount < Info.MaxRefineryPerIndice)
				RequestedRefineries[expandActor] = (conyardLocation, refineryLocation);
		}
		sealed class FransBaseBuilderQueueManager
		{
			sealed class OrdinaryStartIntent
			{
				public readonly string Item;
				public readonly int BufferedTick;
				public ProductionItem NativeItem;
				public int NativeMaterializedTick = -1;
				public bool DispatchAcknowledged;
				public int DispatchAcknowledgedTick = -1;

				public OrdinaryStartIntent(string item, int bufferedTick)
				{
					Item = item;
					BufferedTick = bufferedTick;
				}
			}

			sealed class ExpansionLockLifecycleDiagnostic
			{
				public readonly uint QueueActorId;
				public readonly string Item;
				public readonly int IntentBufferedTick;
				public ProductionItem NativeItem;
				public string State;
				public int StateStartedTick;
				public int LastProgressTick;
				public int LastRemainingCost;
				public int LastRemainingTime;
				public int LongestNoProgressTicks;
				public int LongestNoProgressCash = -1;
				public string LongestNoProgressPower = "UNKNOWN";
				public bool CancellationIssued;
				public CPos? PlacementLocation;

				public ExpansionLockLifecycleDiagnostic(uint queueActorId, string item, int intentBufferedTick,
					ProductionItem nativeItem, int worldTick)
				{
					QueueActorId = queueActorId;
					Item = item;
					IntentBufferedTick = intentBufferedTick;
					NativeItem = nativeItem;
					StateStartedTick = worldTick;
					LastProgressTick = worldTick;
					LastRemainingCost = nativeItem?.RemainingCost ?? -1;
					LastRemainingTime = nativeItem?.RemainingTime ?? -1;
				}
			}

			public readonly string Category;
			public int WaitTicks;
			readonly FransBaseBuilderBotModule baseBuilder;
			readonly World world;
			readonly Player player;
			readonly PowerManager playerPower;
			readonly PlayerResources playerResources;
			readonly IResourceLayer resourceLayer;
			Actor[] playerBuildings = [];
			int failCount;
			int failRetryTicks;
			string lastFailedBuilding;
			readonly Dictionary<string, int> navalPlacementBlockedUntilTick = [];
			readonly Dictionary<string, int> navalPlacementPrecheckRetryTick = [];
			// Sole operational owner of native or pending Phase 4E drain work by queue actor.
			readonly Dictionary<uint, string> expansionLockDrainItems = [];
			// Exact buffered intent and FIFO dispatch acknowledgement used to bind or authoritatively
			// release a pending expansionLockDrainItems owner. This never owns work independently.
			readonly Dictionary<uint, OrdinaryStartIntent> ordinaryStartIntents = [];
			readonly List<ExpansionLockLifecycleDiagnostic> expansionLockLifecycleDiagnostics = [];
			int checkForBasesTicks;
			int cachedBases;
			int cachedBuildings;
			int minimumExcessPower;
			CPos? baseCenterKeepsFailing;
			bool itemQueuedThisTick;
			string footprintClearanceBuilding;
			CPos? footprintClearanceCell;
			int footprintClearanceStartedTick;
			int nextFootprintClearanceOrderTick;
			string observedTimingItem;
			uint observedTimingQueueActorId;
			bool observedTimingDoneLogged;
			int observedTimingDoneTick = -1;
			string placementPendingItem;
			uint placementPendingQueueActorId;
			int placementPendingIssuedTick = -1;
			int placementPendingConfirmationRetries;
			uint secureProductionTargetId;
			CPos secureProductionCenter;
			string secureProductionItem;
			uint remoteProductionFactActorId;
			CPos remoteProductionCenter;
			string remoteProductionItem;
			FransWaterCheck waterState = FransWaterCheck.NotChecked;

			public FransBaseBuilderQueueManager(FransBaseBuilderBotModule parent, string category, Player p, PowerManager pm, PlayerResources pr, IResourceLayer rl)
			{
				baseBuilder = parent; world = p.World; player = p; playerPower = pm; playerResources = pr; resourceLayer = rl; Category = category;
				minimumExcessPower = baseBuilder.Info.MinimumExcessPower;
				if (baseBuilder.Info.NavalProductionTypes.Count == 0) waterState = FransWaterCheck.DontCheck;
			}

			public bool HasExpansionLockDrainOwnership(uint queueActorId)
			{
				return expansionLockDrainItems.ContainsKey(queueActorId);
			}

			public bool AcknowledgeOrdinaryStartProductionDispatch(uint queueActorId, string item, int intentTick)
			{
				if (!ordinaryStartIntents.TryGetValue(queueActorId, out var intent) || intent.Item != item || intent.BufferedTick != intentTick)
					return false;

				intent.DispatchAcknowledged = true;
				intent.DispatchAcknowledgedTick = world.WorldTick;
				var queue = AIUtils.FindQueuesByCategory(player)[Category]
					.FirstOrDefault(candidate => candidate.Actor.ActorID == queueActorId);
				var items = queue?.AllQueued().ToArray() ?? [];
				FransBotLog.BotDebug(world,
					"[BUILDING QUEUE HANDOFF] Tick={0} Player={1} Module=BaseBuilder Event=StartProductionDispatchAcknowledged Owner=BaseBuilderOrdinary Queue={2} QueueActor={3} Requested={4} IntentTick={5} NativeItems={6} Head={7} DrainOwner={8} LockActive={9}",
					world.WorldTick, player, Category, queueActorId, item, intentTick, FormatNativeItems(items),
					FormatNativeItem(items.FirstOrDefault()), expansionLockDrainItems.TryGetValue(queueActorId, out var drainItem) ? drainItem : "NONE",
					baseBuilder.IsTraitDisabled);
				return true;
			}

			public void ClearExpansionLockDrain()
			{
				foreach (var lifecycle in expansionLockLifecycleDiagnostics.ToArray())
					LogExpansionLockLifecycleTransition(lifecycle, null, "LifecycleReleased", "ExpansionLockEnded");

				expansionLockLifecycleDiagnostics.Clear();
				expansionLockDrainItems.Clear();
			}

			public void CaptureExistingProductionForExpansionLock(ILookup<string, ProductionQueue> queuesByCategory)
			{
				expansionLockLifecycleDiagnostics.Clear();
				expansionLockDrainItems.Clear();
				foreach (var queue in queuesByCategory[Category].OrderBy(q => q.Actor.ActorID))
				{
					var items = queue.AllQueued().ToArray();
					UpdateOrdinaryStartIntentMaterialization(queue, items);
					var current = items.FirstOrDefault();
					ordinaryStartIntents.TryGetValue(queue.Actor.ActorID, out var precedingIntent);
					var unmatchedIntent = precedingIntent != null && precedingIntent.NativeMaterializedTick < 0 &&
						!items.Any(item => item.Item == precedingIntent.Item) ? precedingIntent : null;
					var capturedItem = current?.Item ?? unmatchedIntent?.Item;
					var capturedState = current != null ? "Native" : unmatchedIntent != null ? "PendingIntent" : "NONE";
					if (capturedItem != null)
						expansionLockDrainItems[queue.Actor.ActorID] = capturedItem;

					FransBotLog.BotDebug(world,
						"[BUILDING QUEUE HANDOFF] Tick={0} Player={1} Module=BaseBuilder Event=ExpansionLockCapture Queue={2} QueueActor={3} NativeItems={4} Head={5} Captured={6} CapturedState={7} UnmatchedOrdinaryIntent={8} LockActive={9} Cash={10} Power={11} ExcessPower={12}",
						world.WorldTick, player, Category, queue.Actor.ActorID, FormatNativeItems(items), FormatNativeItem(current),
						capturedItem ?? "NONE", capturedState, unmatchedIntent != null ? $"{unmatchedIntent.Item}@{unmatchedIntent.BufferedTick}" : "NONE",
						baseBuilder.IsTraitDisabled, playerResources.GetCashAndResources(), playerPower?.PowerState.ToString() ?? "UNKNOWN",
						playerPower?.ExcessPower ?? 0);

					if (current != null)
					{
						var capturedLifecycle = new ExpansionLockLifecycleDiagnostic(queue.Actor.ActorID, current.Item,
							precedingIntent?.Item == current.Item ? precedingIntent.BufferedTick : -1, current, world.WorldTick);
						expansionLockLifecycleDiagnostics.Add(capturedLifecycle);
						var state = CurrentLifecycleState(queue, current);
						LogExpansionLockLifecycleTransition(capturedLifecycle, queue, state, "CapturedNativeHead");
					}

					if (unmatchedIntent != null)
					{
						var pendingLifecycle = new ExpansionLockLifecycleDiagnostic(queue.Actor.ActorID, unmatchedIntent.Item,
							unmatchedIntent.BufferedTick, null, world.WorldTick);
						expansionLockLifecycleDiagnostics.Add(pendingLifecycle);
						LogExpansionLockLifecycleTransition(pendingLifecycle, queue, "PendingIntent", "BufferedBeforeExpansionLock");
					}
				}
			}

			public void DrainExistingProductionForExpansionLock(IBot bot, ILookup<string, ProductionQueue> queuesByCategory)
			{
				ObserveExpansionLockLifecycles(queuesByCategory);

				if (expansionLockDrainItems.Count == 0)
					return;

				if (WaitTicks > 0)
				{
					WaitTicks--;
					return;
				}

				baseBuilder.combatIntelService.EnsureCurrentSnapshot();
				playerBuildings = baseBuilder.combatIntelService.OwnedActors
					.Where(a => a.Info.HasTraitInfo<BuildingInfo>()).ToArray();
				var excessBonus = baseBuilder.Info.ExcessPowerIncrement * (playerBuildings.Length / baseBuilder.Info.ExcessPowerIncreaseThreshold.Clamp(1, int.MaxValue));
				minimumExcessPower = (baseBuilder.Info.MinimumExcessPower + excessBonus).Clamp(baseBuilder.Info.MinimumExcessPower, baseBuilder.Info.MaximumExcessPower);
				itemQueuedThisTick = false;

				var queues = queuesByCategory[Category].OrderBy(q => q.Actor.ActorID).ToArray();
				var liveQueueIds = queues.Select(q => q.Actor.ActorID).ToHashSet();
				foreach (var staleQueueActorId in expansionLockDrainItems.Keys.Where(id => !liveQueueIds.Contains(id)).ToArray())
				{
					var staleItem = expansionLockDrainItems[staleQueueActorId];
					expansionLockDrainItems.Remove(staleQueueActorId);
					FransBotLog.BotDebug(world,
						"[BASEBUILDER DRAIN] Tick={0} Player={1} structure={2} queue={3} queueActor={4} action=LifecycleReleased reason=QueueActorUnavailable",
						world.WorldTick, player, staleItem, Category, staleQueueActorId);
				}

				var active = false;
				foreach (var queue in queues)
				{
					if (!expansionLockDrainItems.TryGetValue(queue.Actor.ActorID, out var capturedItem))
						continue;

					var current = queue.AllQueued().FirstOrDefault();
					if (current == null)
					{
						var pendingIntent = ordinaryStartIntents.TryGetValue(queue.Actor.ActorID, out var intent) &&
							intent.Item == capturedItem && intent.NativeItem == null ? intent : null;
						if (pendingIntent != null)
						{
							if (!pendingIntent.DispatchAcknowledged)
							{
								active = true;
								continue;
							}

							expansionLockDrainItems.Remove(queue.Actor.ActorID);
							ReleasePendingLifecycleDiagnostic(queue, capturedItem,
								"StartProductionDispatchAcknowledgedWithoutNativeItem");
							ordinaryStartIntents.Remove(queue.Actor.ActorID);
							FransBotLog.BotDebug(world,
								"[BASEBUILDER DRAIN] Tick={0} Player={1} structure={2} queue={3} queueActor={4} state=PendingIntent action=LifecycleReleased reason=StartProductionRejected dispatchAcknowledgedTick={5}",
								world.WorldTick, player, capturedItem, Category, queue.Actor.ActorID, pendingIntent.DispatchAcknowledgedTick);
							continue;
						}

						var placementWasPending = placementPendingItem == capturedItem &&
							placementPendingQueueActorId == queue.Actor.ActorID && placementPendingIssuedTick >= 0;
						TickQueue(bot, queue, allowNewProduction: false, drainingUnderExpansionLock: true);
						expansionLockDrainItems.Remove(queue.Actor.ActorID);
						FransBotLog.BotDebug(world,
							placementWasPending
								? "[BASEBUILDER DRAIN] Tick={0} Player={1} structure={2} queue={3} queueActor={4} action=PlacementCompleted queueState=Released"
								: "[BASEBUILDER DRAIN] Tick={0} Player={1} structure={2} queue={3} queueActor={4} action=LifecycleReleased queueState=Empty",
							world.WorldTick, player, capturedItem, Category, queue.Actor.ActorID);
						continue;
					}

					if (current.Item != capturedItem)
					{
						expansionLockDrainItems.Remove(queue.Actor.ActorID);
						FransBotLog.BotDebug(world,
							"[BASEBUILDER DRAIN] Tick={0} Player={1} structure={2} queue={3} queueActor={4} action=LifecycleReleased reason=QueueItemChanged current={5}",
							world.WorldTick, player, capturedItem, Category, queue.Actor.ActorID, current.Item);
						continue;
					}

					if (TickQueue(bot, queue, allowNewProduction: false, drainingUnderExpansionLock: true))
						active = true;
				}

				WaitTicks = active ? baseBuilder.Info.StructureProductionActiveDelay : baseBuilder.Info.StructureProductionInactiveDelay;
			}

			static string FormatNativeItems(ProductionItem[] items)
			{
				return items.Length == 0 ? "NONE" : string.Join(">", items.Select(item => item.Item));
			}

			static string FormatNativeItem(ProductionItem item)
			{
				return item == null ? "NONE" :
					$"{item.Item}[Started={item.Started},Done={item.Done},Paused={item.Paused},RemainingCost={item.RemainingCost},RemainingTime={item.RemainingTime},RemainingTimeActual={item.RemainingTimeActual}]";
			}

			void UpdateOrdinaryStartIntentMaterialization(ProductionQueue queue, ProductionItem[] items)
			{
				if (!ordinaryStartIntents.TryGetValue(queue.Actor.ActorID, out var intent))
					return;

				if (intent.NativeItem == null)
				{
					var nativeItem = items.FirstOrDefault(item => item.Item == intent.Item);
					if (nativeItem == null)
					{
						if (intent.DispatchAcknowledged)
						{
							ordinaryStartIntents.Remove(queue.Actor.ActorID);
							FransBotLog.BotDebug(world,
								"[BUILDING QUEUE HANDOFF] Tick={0} Player={1} Module=BaseBuilder Event=StartProductionRejected Owner=BaseBuilderOrdinary Queue={2} QueueActor={3} Requested={4} IntentTick={5} DispatchAcknowledgedTick={6} NativeItems={7} LockActive={8}",
								world.WorldTick, player, Category, queue.Actor.ActorID, intent.Item, intent.BufferedTick,
								intent.DispatchAcknowledgedTick, FormatNativeItems(items), baseBuilder.IsTraitDisabled);
						}

						return;
					}

					intent.NativeItem = nativeItem;
					intent.NativeMaterializedTick = world.WorldTick;
					FransBotLog.BotDebug(world,
						"[BUILDING QUEUE HANDOFF] Tick={0} Player={1} Module=BaseBuilder Event=NativeMaterialized Owner=BaseBuilderOrdinary Queue={2} QueueActor={3} Requested={4} IntentTick={5} NativeItems={6} Head={7} LockActive={8} Cash={9} Power={10} ExcessPower={11}",
						world.WorldTick, player, Category, queue.Actor.ActorID, intent.Item, intent.BufferedTick,
						FormatNativeItems(items), FormatNativeItem(items.FirstOrDefault()), baseBuilder.IsTraitDisabled,
						playerResources.GetCashAndResources(), playerPower?.PowerState.ToString() ?? "UNKNOWN", playerPower?.ExcessPower ?? 0);
				}
				else if (!items.Any(item => ReferenceEquals(item, intent.NativeItem)) && !baseBuilder.IsTraitDisabled)
					ordinaryStartIntents.Remove(queue.Actor.ActorID);
			}

			void RecordOrdinaryStartProductionIntent(ProductionQueue queue, string item)
			{
				var items = queue.AllQueued().ToArray();
				var intent = new OrdinaryStartIntent(item, world.WorldTick);
				ordinaryStartIntents[queue.Actor.ActorID] = intent;
				FransBotLog.BotDebug(world,
					"[BUILDING QUEUE HANDOFF] Tick={0} Player={1} Module=BaseBuilder Event=StartProductionIntentBuffered Owner=BaseBuilderOrdinary OrdinaryWork=True Queue={2} QueueActor={3} Requested={4} NativeItems={5} Head={6} LockActive={7} Cash={8} Power={9} ExcessPower={10}",
					world.WorldTick, player, Category, queue.Actor.ActorID, item, FormatNativeItems(items),
					FormatNativeItem(items.FirstOrDefault()), baseBuilder.IsTraitDisabled, playerResources.GetCashAndResources(),
					playerPower?.PowerState.ToString() ?? "UNKNOWN", playerPower?.ExcessPower ?? 0);
			}

			string CurrentLifecycleState(ProductionQueue queue, ProductionItem item)
			{
				if (item.Paused)
					return "Paused";

				if (!item.Done)
					return "Building";

				if (placementPendingItem == item.Item && placementPendingQueueActorId == queue.Actor.ActorID && placementPendingIssuedTick >= 0)
					return "PlacementIssued";

				return "ReadyToPlace";
			}

			void ObserveExpansionLockLifecycles(ILookup<string, ProductionQueue> queuesByCategory)
			{
				if (expansionLockLifecycleDiagnostics.Count == 0)
					return;

				var queues = queuesByCategory[Category].OrderBy(q => q.Actor.ActorID).ToArray();
				foreach (var lifecycle in expansionLockLifecycleDiagnostics.ToArray())
				{
					var queue = queues.FirstOrDefault(candidate => candidate.Actor.ActorID == lifecycle.QueueActorId);
					if (queue == null)
					{
						LogExpansionLockLifecycleTransition(lifecycle, null, "LifecycleReleased", "QueueActorUnavailable");
						expansionLockLifecycleDiagnostics.Remove(lifecycle);
						continue;
					}

					var items = queue.AllQueued().ToArray();
					var nativeItem = lifecycle.NativeItem == null
						? items.FirstOrDefault(item => item.Item == lifecycle.Item)
						: items.FirstOrDefault(item => ReferenceEquals(item, lifecycle.NativeItem));
					if (nativeItem == null)
					{
						if (lifecycle.NativeItem == null)
							continue;

						var reason = lifecycle.CancellationIssued ? "AfterCancellationIssued" :
							lifecycle.PlacementLocation.HasValue && HasOwnedStructureAt(lifecycle.Item, lifecycle.PlacementLocation.Value)
								? "PhysicalStructurePresentAtIssuedCell" :
							lifecycle.PlacementLocation.HasValue ? "AfterPlacementIssuedUnconfirmed" : "NativeItemRemoved";
						LogExpansionLockLifecycleTransition(lifecycle, queue, "Absent", reason);
						expansionLockLifecycleDiagnostics.Remove(lifecycle);
						continue;
					}

					if (lifecycle.NativeItem == null)
					{
						lifecycle.NativeItem = nativeItem;
						lifecycle.LastRemainingCost = nativeItem.RemainingCost;
						lifecycle.LastRemainingTime = nativeItem.RemainingTime;
						lifecycle.LastProgressTick = world.WorldTick;
						if (ordinaryStartIntents.TryGetValue(lifecycle.QueueActorId, out var intent) &&
							intent.Item == lifecycle.Item && intent.BufferedTick == lifecycle.IntentBufferedTick)
						{
							intent.NativeItem = nativeItem;
							intent.NativeMaterializedTick = world.WorldTick;
						}

						LogExpansionLockLifecycleTransition(lifecycle, queue, "NativeMaterialized", "MaterializedAfterExpansionLockCapture");
					}

					var progressed = nativeItem.RemainingCost < lifecycle.LastRemainingCost || nativeItem.RemainingTime < lifecycle.LastRemainingTime;
					if (progressed)
						lifecycle.LastProgressTick = world.WorldTick;
					else
					{
						var noProgressTicks = world.WorldTick - lifecycle.LastProgressTick;
						if (noProgressTicks > lifecycle.LongestNoProgressTicks)
						{
							lifecycle.LongestNoProgressTicks = noProgressTicks;
							lifecycle.LongestNoProgressCash = playerResources.GetCashAndResources();
							lifecycle.LongestNoProgressPower = playerPower?.PowerState.ToString() ?? "UNKNOWN";
						}
					}
					lifecycle.LastRemainingCost = nativeItem.RemainingCost;
					lifecycle.LastRemainingTime = nativeItem.RemainingTime;

					var nativeIndex = Array.FindIndex(items, item => ReferenceEquals(item, nativeItem));
					var state = nativeIndex > 0 ? "QueuedBehind" : CurrentLifecycleState(queue, nativeItem);
					LogExpansionLockLifecycleTransition(lifecycle, queue, state, progressed ? "NativeProgressObserved" : "NativeStateObserved");
				}
			}

			void ReleasePendingLifecycleDiagnostic(ProductionQueue queue, string item, string reason)
			{
				foreach (var lifecycle in expansionLockLifecycleDiagnostics.Where(candidate =>
					candidate.QueueActorId == queue.Actor.ActorID && candidate.Item == item && candidate.NativeItem == null).ToArray())
				{
					LogExpansionLockLifecycleTransition(lifecycle, queue, "LifecycleReleased", reason);
					expansionLockLifecycleDiagnostics.Remove(lifecycle);
				}
			}

			bool HasOwnedStructureAt(string item, CPos location)
			{
				return world.ActorsHavingTrait<Building>().Any(actor => actor.IsInWorld && !actor.IsDead &&
					actor.Owner == player && actor.Info.Name == item && actor.Location == location);
			}

			void LogExpansionLockLifecycleTransition(ExpansionLockLifecycleDiagnostic lifecycle, ProductionQueue queue,
				string state, string reason)
			{
				if (lifecycle.State == state)
					return;

				var previousState = lifecycle.State ?? "NONE";
				var previousStateAge = world.WorldTick - lifecycle.StateStartedTick;
				var items = queue?.AllQueued().ToArray() ?? [];
				var nativeItem = lifecycle.NativeItem == null ? null : items.FirstOrDefault(item => ReferenceEquals(item, lifecycle.NativeItem));
				var nativeIndex = nativeItem == null ? -1 : Array.FindIndex(items, item => ReferenceEquals(item, nativeItem));
				lifecycle.State = state;
				lifecycle.StateStartedTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					"[BUILDING QUEUE HANDOFF] Tick={0} Player={1} Module=BaseBuilder Event=LifecycleTransition Queue={2} QueueActor={3} Item={4} IntentTick={5} Previous={6} State={7} PreviousStateAge={8} LastProgressAge={9} LongestNoProgress={10} LongestNoProgressCash={11} LongestNoProgressPower={12} NativeIndex={13} NativeItems={14} Head={15} ItemState={16} Reason={17} LockActive={18} Cash={19} Power={20} ExcessPower={21}",
					world.WorldTick, player, Category, lifecycle.QueueActorId, lifecycle.Item, lifecycle.IntentBufferedTick,
					previousState, state, previousStateAge, world.WorldTick - lifecycle.LastProgressTick,
					lifecycle.LongestNoProgressTicks, lifecycle.LongestNoProgressCash, lifecycle.LongestNoProgressPower, nativeIndex,
					FormatNativeItems(items), FormatNativeItem(items.FirstOrDefault()), FormatNativeItem(nativeItem), reason,
					baseBuilder.IsTraitDisabled, playerResources.GetCashAndResources(), playerPower?.PowerState.ToString() ?? "UNKNOWN",
					playerPower?.ExcessPower ?? 0);
			}

			void MarkTrackedCancellationIssued(ProductionQueue queue, ProductionItem item, string reason)
			{
				foreach (var lifecycle in expansionLockLifecycleDiagnostics.Where(candidate => candidate.QueueActorId == queue.Actor.ActorID &&
					(candidate.NativeItem == null ? candidate.Item == item.Item : ReferenceEquals(candidate.NativeItem, item))))
				{
					lifecycle.CancellationIssued = true;
					LogExpansionLockLifecycleTransition(lifecycle, queue, "CancellationIssued", reason);
				}
			}

			void MarkTrackedPlacementIssued(ProductionQueue queue, ProductionItem item, CPos location)
			{
				foreach (var lifecycle in expansionLockLifecycleDiagnostics.Where(candidate => candidate.QueueActorId == queue.Actor.ActorID &&
					(candidate.NativeItem == null ? candidate.Item == item.Item : ReferenceEquals(candidate.NativeItem, item))))
				{
					lifecycle.PlacementLocation = location;
					LogExpansionLockLifecycleTransition(lifecycle, queue, "PlacementIssued", $"Location={location}");
				}
			}

			public void Tick(IBot bot, ILookup<string, ProductionQueue> queuesByCategory)
			{
				if (failCount >= baseBuilder.Info.MaximumFailedPlacementAttempts)
				{
					if (baseBuilder.BaseExpansionModules != null && baseCenterKeepsFailing != null)
					{
						var stuck = baseBuilder.ConstructionYardBuildings.Actors.Where(a => !a.IsDead)
							.OrderBy(a => (a.Location - baseCenterKeepsFailing.Value).LengthSquared).ThenBy(a => a.ActorID).FirstOrDefault();
						if (stuck != null) foreach (var be in baseBuilder.BaseExpansionModules) be.UpdateExpansionParams(bot, false, true, stuck);
						failCount = 0;
					}
					else if ((baseBuilder.BaseExpansionModules == null || baseBuilder.BaseExpansionModules.Length == 0) && --failRetryTicks <= 0)
					{
						baseBuilder.combatIntelService.EnsureCurrentSnapshot();
						var currentBuildings = baseBuilder.combatIntelService.OwnedActors.Count(a => a.Info.HasTraitInfo<BuildingInfo>());
						var providers = world.ActorsHavingTrait<BaseProvider>().Count(a => a.Owner == player);
						if (currentBuildings < cachedBuildings || providers > cachedBases) failCount = 0;
						else failRetryTicks = baseBuilder.Info.StructureProductionResumeDelay;
					}
					if (failCount >= baseBuilder.Info.MaximumFailedPlacementAttempts) return;
				}

				if (waterState == FransWaterCheck.NotChecked)
				{
					if (AIUtils.IsAreaAvailable<BaseProvider>(world, player, world.Map, baseBuilder.Info.MaxBaseRadius, baseBuilder.Info.WaterTerrainTypes)) waterState = FransWaterCheck.EnoughWater;
					else { waterState = FransWaterCheck.NotEnoughWater; checkForBasesTicks = baseBuilder.Info.CheckForNewBasesDelay; }
				}
				if (waterState == FransWaterCheck.NotEnoughWater && --checkForBasesTicks <= 0)
				{
					var currentBases = world.ActorsHavingTrait<BaseProvider>().Count(a => a.Owner == player);
					if (currentBases > cachedBases) { cachedBases = currentBases; waterState = FransWaterCheck.NotChecked; }
				}

				if (WaitTicks > 0) return;
				baseBuilder.combatIntelService.EnsureCurrentSnapshot();
				playerBuildings = baseBuilder.combatIntelService.OwnedActors
					.Where(a => a.Info.HasTraitInfo<BuildingInfo>()).ToArray();
				var excessBonus = baseBuilder.Info.ExcessPowerIncrement * (playerBuildings.Length / baseBuilder.Info.ExcessPowerIncreaseThreshold.Clamp(1, int.MaxValue));
				minimumExcessPower = (baseBuilder.Info.MinimumExcessPower + excessBonus).Clamp(baseBuilder.Info.MinimumExcessPower, baseBuilder.Info.MaximumExcessPower);
				itemQueuedThisTick = false;
				var active = false;
				foreach (var queue in queuesByCategory[Category].OrderBy(q => q.Actor.ActorID)) if (TickQueue(bot, queue)) active = true;

				var openingBuildingQueue = !baseBuilder.OpeningComplete && baseBuilder.Info.BuildingQueues.Contains(Category);
				WaitTicks = openingBuildingQueue
					? Math.Max(1, baseBuilder.Info.OpeningScanInterval)
					: active ? baseBuilder.Info.StructureProductionActiveDelay : baseBuilder.Info.StructureProductionInactiveDelay;
			}

			void ClearFootprintClearanceState()
			{
				footprintClearanceBuilding = null;
				footprintClearanceCell = null;
				footprintClearanceStartedTick = 0;
				nextFootprintClearanceOrderTick = 0;
			}

			bool FootprintContains(CPos origin, BuildingInfo info, CPos cell, int extra = 0) =>
				cell.X >= origin.X - extra && cell.Y >= origin.Y - extra &&
				cell.X <= origin.X + info.Dimensions.X - 1 + extra &&
				cell.Y <= origin.Y + info.Dimensions.Y - 1 + extra;

			int StructureClearance(CPos cell, BuildingInfo candidateInfo)
			{
				var candidateMinX = cell.X; var candidateMinY = cell.Y;
				var candidateMaxX = cell.X + candidateInfo.Dimensions.X - 1;
				var candidateMaxY = cell.Y + candidateInfo.Dimensions.Y - 1;
				var minimum = int.MaxValue;
				foreach (var existing in playerBuildings)
				{
					if (existing == null || existing.IsDead || !existing.IsInWorld) continue;
					var info = existing.Info.TraitInfoOrDefault<BuildingInfo>(); if (info == null) continue;
					var exMinX = existing.Location.X; var exMinY = existing.Location.Y;
					var exMaxX = exMinX + info.Dimensions.X - 1; var exMaxY = exMinY + info.Dimensions.Y - 1;
					var gapX = candidateMaxX < exMinX ? exMinX - candidateMaxX - 1 : exMaxX < candidateMinX ? candidateMinX - exMaxX - 1 : 0;
					var gapY = candidateMaxY < exMinY ? exMinY - candidateMaxY - 1 : exMaxY < candidateMinY ? candidateMinY - exMaxY - 1 : 0;
					minimum = Math.Min(minimum, Math.Max(gapX, gapY));
					if (minimum == 0) break;
				}
				return minimum == int.MaxValue ? baseBuilder.Info.MinimumStructureSpacingCells : minimum;
			}

			IEnumerable<CPos> OrderPlacementCells(CPos center, CPos target, int weightPercent, int minRange, int maxRange)
			{
				var cells = world.Map.FindTilesInAnnulus(center, minRange, maxRange);
				if (center == target || weightPercent <= 0)
					return cells.OrderBy(c => (c - center).LengthSquared).ThenBy(c => c.X).ThenBy(c => c.Y);
				var w = weightPercent.Clamp(0, 100);
				return cells.OrderBy(c => (long)(100 - w) * (c - center).LengthSquared + (long)w * (c - target).LengthSquared)
					.ThenBy(c => (c - center).LengthSquared).ThenBy(c => c.X).ThenBy(c => c.Y);
			}

			CPos? FindBlockedPreferredPlacementCandidate(string actorType, FransBuildingType type)
			{
				if (!baseBuilder.Info.FootprintClearanceBuildingTypes.Contains(actorType)) return null;
				var actorInfo = world.Map.Rules.Actors[actorType];
				var bi = actorInfo.TraitInfoOrDefault<BuildingInfo>(); if (bi == null) return null;

				var center = baseBuilder.GetBaseCenter();
				var target = center;
				var weight = 0;
				var minRange = baseBuilder.Info.MinBaseRadius;
				var maxRange = baseBuilder.Info.MaxBaseRadius;

				// Respect the same producer-routing rule as normal placement. A WEAP/BARR that has
				// exceeded its main-base cap must never use blocker clearance as a back door to
				// place another producer in the main base.
				if (type == FransBuildingType.Building && baseBuilder.RequiresExpansionProductionPlacement(actorType))
				{
					if (!baseBuilder.TryGetExpansionProductionCenter(out center)) return null;
					target = center;
					minRange = baseBuilder.Info.ExpansionProductionPlacementMinRadius;
					maxRange = baseBuilder.Info.ExpansionProductionPlacementMaxRadius;
					weight = baseBuilder.ProductionDirectionWeight(actorType);
					if (weight > 0 && baseBuilder.TryGetEnemyBaseDirectionTarget(out var expansionEnemyTarget, out _))
						target = expansionEnemyTarget;
				}
				else if (type == FransBuildingType.Refinery && resourceLayer != null)
				{
					var requestRef = baseBuilder.RequestedRefineries.Keys.OrderBy(a => a.ActorID).FirstOrDefault();
					if (requestRef != null)
					{
						center = baseBuilder.RequestedRefineries[requestRef].ConyardLoc;
						target = baseBuilder.RequestedRefineries[requestRef].ResourceLoc;
						weight = 100;
					}
					else
					{
						center = baseBuilder.ResourceConyardCenter ?? center;
						var resource = world.Map.FindTilesInAnnulus(center, minRange, maxRange)
							.Where(c => baseBuilder.ResourceMapModule != null ? baseBuilder.ResourceMapModule.Info.ValuableResourceTypes.Contains(resourceLayer.GetResource(c).Type) : resourceLayer.GetResource(c).Type != null)
							.OrderBy(c => (c - center).LengthSquared).ThenBy(c => c.X).ThenBy(c => c.Y).FirstOrDefault();
						if (resource != default) { target = resource; weight = 100; }
					}
				}
				else
				{
					weight = baseBuilder.ProductionDirectionWeight(actorType);
					if (weight > 0 && baseBuilder.TryGetEnemyBaseDirectionTarget(out var enemyTarget, out _)) target = enemyTarget;
				}

				CPos? bestBlockedFallback = null;
				var bestBlockedClearance = -1;
				var bestLegalClearance = -1;
				foreach (var cell in OrderPlacementCells(center, target, weight, minRange, maxRange).Take(baseBuilder.Info.BuildingFootprintClearanceCandidateCount))
				{
					if (!bi.IsCloseEnoughToBase(world, player, actorInfo, null, cell)) continue;
					if (baseBuilder.IntersectsGroundStagingReservation(cell, bi)) continue;
					if (baseBuilder.riskModelService.EvaluateStrategicCell(cell, FransRiskRole.BuildingPlacement, FransRiskTolerance.Cautious).IsCritical) continue;
					var clearance = StructureClearance(cell, bi);
					if (world.CanPlaceBuilding(cell, actorInfo, bi, null))
					{
						// Normal placement will immediately take the first ideal-spacing legal site.
						if (clearance >= baseBuilder.Info.MinimumStructureSpacingCells) return null;
						bestLegalClearance = Math.Max(bestLegalClearance, clearance);
						continue;
					}

					baseBuilder.combatIntelService.EnsureCurrentSnapshot();
					var blockers = baseBuilder.combatIntelService.OwnedActors.Where(baseBuilder.CanDisplaceBuildingBlocker)
						.Where(a => FootprintContains(cell, bi, a.Location)).OrderBy(a => a.ActorID).ToArray();
					if (blockers.Length == 0) continue;
					// Passing one actor as the CanPlaceBuilding ignore actor gives exact evidence for the common
					// one-blocker case. With several ordinary units we allow one bounded clearance attempt,
					// then re-check the real engine rule before placement.
					if (!blockers.Any(b => world.CanPlaceBuilding(cell, actorInfo, bi, b)) && blockers.Length <= 1) continue;

					if (clearance >= baseBuilder.Info.MinimumStructureSpacingCells)
						return cell;
					if (clearance > bestBlockedClearance)
					{
						bestBlockedClearance = clearance;
						bestBlockedFallback = cell;
					}
				}

				// MinimumStructureSpacingCells is an ideal, not a hard rule. If neither blocked nor
				// already-legal candidates can achieve it, clear a unit only when doing so preserves
				// at least as much structural clearance as the ordinary legal fallback.
				return bestBlockedFallback.HasValue && bestBlockedClearance >= bestLegalClearance ? bestBlockedFallback : null;
			}

			int MoveFootprintBlockers(ActorInfo actorInfo, CPos cell)
			{
				var bi = actorInfo.TraitInfoOrDefault<BuildingInfo>(); if (bi == null) return 0;
				baseBuilder.combatIntelService.EnsureCurrentSnapshot();
				var blockers = baseBuilder.combatIntelService.OwnedActors.Where(baseBuilder.CanDisplaceBuildingBlocker)
					.Where(a => FootprintContains(cell, bi, a.Location, baseBuilder.Info.BuildingFootprintClearanceRadius))
					.OrderBy(a => a.ActorID).Take(12).ToArray();
				var moved = 0;
				var radius = Math.Max(bi.Dimensions.X, bi.Dimensions.Y) + baseBuilder.Info.BuildingFootprintClearanceRadius;
				foreach (var actor in blockers)
				{
					var mobile = actor.TraitOrDefault<Mobile>(); if (mobile == null) continue;
					var destination = world.Map.FindTilesInAnnulus(cell, radius + 1, radius + 7)
						.Where(c => world.Map.Contains(c) && !FootprintContains(cell, bi, c, baseBuilder.Info.BuildingFootprintClearanceRadius))
						.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
						.Select(c => (Cell: c, Risk: baseBuilder.riskModelService.EvaluateCell(actor, c, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced)))
						.Where(x => !x.Risk.IsCritical).OrderBy(x => x.Risk.Score).ThenBy(x => (x.Cell - actor.Location).LengthSquared)
						.ThenBy(x => x.Cell.X).ThenBy(x => x.Cell.Y).Select(x => (CPos?)x.Cell).FirstOrDefault();
					if (destination.HasValue && baseBuilder.QueueBuildingBlockerRiskAwareMove(actor, destination.Value)) moved++;
				}
				return moved;
			}

			bool TryManageFootprintClearance(IBot bot, string actorType, FransBuildingType type, out CPos? readyLocation)
			{
				readyLocation = null;
				if (!baseBuilder.Info.FootprintClearanceBuildingTypes.Contains(actorType)) { ClearFootprintClearanceState(); return false; }
				var actorInfo = world.Map.Rules.Actors[actorType]; var bi = actorInfo.TraitInfoOrDefault<BuildingInfo>(); if (bi == null) return false;
				if (footprintClearanceBuilding != actorType || !footprintClearanceCell.HasValue)
				{
					ClearFootprintClearanceState();
					var candidate = FindBlockedPreferredPlacementCandidate(actorType, type);
					if (!candidate.HasValue) return false;
					var moved = MoveFootprintBlockers(actorInfo, candidate.Value);
					if (moved <= 0) return false;
					footprintClearanceBuilding = actorType; footprintClearanceCell = candidate; footprintClearanceStartedTick = world.WorldTick;
					nextFootprintClearanceOrderTick = world.WorldTick + baseBuilder.Info.BuildingFootprintClearanceRetryTicks;
					FransBotLog.BotDebug(world, "{0}: FransBaseBuilder holds completed {1} at preferred site {2} and moves {3} ordinary friendly blocker(s) first; fallback placement is delayed for up to {4} WT.", player, actorType, candidate.Value, moved, baseBuilder.Info.BuildingFootprintClearanceMaximumWaitTicks);
					return true;
				}

				var cell = footprintClearanceCell.Value;
				if (!baseBuilder.IntersectsGroundStagingReservation(cell, bi) &&
					world.CanPlaceBuilding(cell, actorInfo, bi, null) && bi.IsCloseEnoughToBase(world, player, actorInfo, null, cell))
				{
					readyLocation = cell; ClearFootprintClearanceState();
					FransBotLog.BotDebug(world, "{0}: friendly blockers cleared preferred {1} footprint at {2}; placing there instead of using the earlier fallback.", player, actorType, cell);
					return false;
				}
				if (world.WorldTick - footprintClearanceStartedTick >= baseBuilder.Info.BuildingFootprintClearanceMaximumWaitTicks)
				{
					FransBotLog.BotDebug(world, "{0}: preferred {1} footprint at {2} is still unavailable after {3} WT; bounded clearance ends and ordinary placement fallback may proceed.", player, actorType, cell, baseBuilder.Info.BuildingFootprintClearanceMaximumWaitTicks);
					ClearFootprintClearanceState(); return false;
				}
				if (world.WorldTick >= nextFootprintClearanceOrderTick)
				{
					var moved = MoveFootprintBlockers(actorInfo, cell);
					nextFootprintClearanceOrderTick = world.WorldTick + baseBuilder.Info.BuildingFootprintClearanceRetryTicks;
					if (moved == 0)
					{
						baseBuilder.combatIntelService.EnsureCurrentSnapshot();
						if (!baseBuilder.combatIntelService.OwnedActors.Where(baseBuilder.CanDisplaceBuildingBlocker).Any(a => FootprintContains(cell, bi, a.Location, baseBuilder.Info.BuildingFootprintClearanceRadius)))
						{ ClearFootprintClearanceState(); return false; }
					}
				}
				return true;
			}

			bool TickQueue(IBot bot, ProductionQueue queue, bool allowNewProduction = true, bool drainingUnderExpansionLock = false)
			{
				var nativeItems = queue.AllQueued().ToArray();
				UpdateOrdinaryStartIntentMaterialization(queue, nativeItems);
				var current = nativeItems.FirstOrDefault();
				if (current == null)
				{
					observedTimingItem = null;
					observedTimingQueueActorId = 0;
					observedTimingDoneLogged = false;
					observedTimingDoneTick = -1;
					placementPendingItem = null;
					placementPendingQueueActorId = 0;
					placementPendingIssuedTick = -1;
					placementPendingConfirmationRetries = 0;
					secureProductionTargetId = 0;
					secureProductionCenter = default;
					secureProductionItem = null;
					remoteProductionFactActorId = 0;
					remoteProductionCenter = default;
					remoteProductionItem = null;
				}
				else if (observedTimingItem != current.Item || observedTimingQueueActorId != queue.Actor.ActorID)
				{
					observedTimingItem = current.Item;
					observedTimingQueueActorId = queue.Actor.ActorID;
					observedTimingDoneLogged = false;
					observedTimingDoneTick = -1;
					placementPendingItem = null;
					placementPendingQueueActorId = 0;
					placementPendingIssuedTick = -1;
					placementPendingConfirmationRetries = 0;
				}

				if (current == null && failCount < baseBuilder.Info.MaximumFailedPlacementAttempts)
				{
					if (!allowNewProduction)
						return false;

					var openingBuildingPriority = !baseBuilder.OpeningComplete && baseBuilder.Info.BuildingQueues.Contains(Category);
					// Opening structures are queued immediately even when the bank is below the normal
					// BaseBuilder cash threshold. OpenRA's production queue then consumes income as it arrives.
					// This prevents ordinary unit spending from delaying mandatory opening structures.
					if ((!openingBuildingPriority && playerResources.GetCashAndResources() < baseBuilder.Info.ProductionMinCashRequirement) || itemQueuedThisTick)
						return false;
					var item = ChooseBuildingToBuild(queue);
					if (item == null) return false;
					RecordOrdinaryStartProductionIntent(queue, item.Name);
					bot.QueueOrder(Order.StartProduction(queue.Actor, item.Name, 1));
					bot.QueueOrder(new Order(OrdinaryStartProductionAcknowledgedOrder, player.PlayerActor, false)
					{
						TargetString = item.Name,
						ExtraData = queue.Actor.ActorID,
						ExtraLocation = new CPos(world.WorldTick, 0)
					});
					FransBotLog.BotDebug(world,
						"{0}: BUILD TIMING production START {1} on {2} queue actor {3} at WT {4}.",
						player, item.Name, Category, queue.Actor.ActorID, world.WorldTick);
					itemQueuedThisTick = true;
					if (!baseBuilder.OpeningComplete && baseBuilder.Info.BuildingQueues.Contains(Category)) baseBuilder.NotifyOpeningBuildingQueued(item.Name);
				}
				else if (current != null && current.Done)
				{
					if (!observedTimingDoneLogged)
					{
						observedTimingDoneLogged = true;
						observedTimingDoneTick = world.WorldTick;
						FransBotLog.BotDebug(world,
							"{0}: BUILD TIMING production COMPLETE {1} on {2} queue actor {3} at WT {4}; placement ownership/geometry is now the only remaining delay.",
							player, current.Item, Category, queue.Actor.ActorID, world.WorldTick);
					}

					// A normal first-expansion PROC reservation owns the completed Building item until
					// its real ore FACT exists. Naval-support suspension is different: it evicts that
					// exact refinery so SPEN/SYRD can use the shared Building queue. Queue the same
					// cancellation here as ExpansionManager so trait tick ordering cannot race a READY
					// PROC into ordinary main-base placement.
					if (baseBuilder.Info.RefineryTypes.Contains(current.Item) &&
						baseBuilder.expansionStateService?.FirstExpansionRefinerySuspendedForInfrastructure == true)
					{
						MarkTrackedCancellationIssued(queue, current, "FirstExpansionRefinerySuspendedForInfrastructure");
						bot.QueueOrder(Order.CancelProduction(queue.Actor, current.Item, 1));
						return true;
					}

					if (baseBuilder.ReadyForFirstExpansionRefineryPrebuild &&
						baseBuilder.Info.RefineryTypes.Contains(current.Item))
						return true;

					var secureProductionReservation = secureProductionTargetId != 0 && secureProductionItem == current.Item;
					Actor secureProductionFact = null;
					if (secureProductionReservation)
					{
						if (!baseBuilder.generalService.TryGetSecureDefensePoint(secureProductionTargetId, out var liveSecureCenter, out _))
						{
							secureProductionTargetId = 0;
							secureProductionItem = null;
							secureProductionReservation = false;
						}
						else
						{
							secureProductionCenter = liveSecureCenter;
							// a SECURE producer is legal only while the physical FACT
							// that requested it still exists. No travelling-MCV reservation remains.
							if (!baseBuilder.TryGetSecureFootholdFact(secureProductionCenter, out secureProductionFact))
							{
								FransBotLog.BotDebug(world,
									"{0}: SECURE producer reservation {1} for target {2} lost its physical FACT; cancelling the stale queue item so Building production cannot deadlock.",
									player, current.Item, secureProductionTargetId);
								MarkTrackedCancellationIssued(queue, current, "SecureProducerFactLost");
								bot.QueueOrder(Order.CancelProduction(queue.Actor, current.Item, 1));
								secureProductionTargetId = 0;
								secureProductionItem = null;
								return true;
							}
						}
					}

					var remoteProductionReservation = remoteProductionFactActorId != 0 && remoteProductionItem == current.Item;
					Actor remoteProductionFact = null;
					if (remoteProductionReservation)
					{
						remoteProductionFact = baseBuilder.ConstructionYardBuildings.Actors
							.Where(a => a != null && a.IsInWorld && !a.IsDead && a.ActorID == remoteProductionFactActorId)
							.FirstOrDefault();
						if (remoteProductionFact == null)
						{
							FransBotLog.BotDebug(world,
								"{0}: REMOTE BASE producer reservation {1} lost FACT {2}; cancelling stale queue item rather than placing it back at the main base.",
								player, current.Item, remoteProductionFactActorId);
							MarkTrackedCancellationIssued(queue, current, "RemoteProducerFactLost");
							bot.QueueOrder(Order.CancelProduction(queue.Actor, current.Item, 1));
							remoteProductionFactActorId = 0;
							remoteProductionItem = null;
							return true;
						}
						remoteProductionCenter = remoteProductionFact.Location;
					}

					// Never violate the main-base producer caps because an expansion FACT repacked
					// between production start and completion. The queue hold is bounded, however:
					// once the FACT has been absent long enough, cancel the stale completed item.
					// CanQueueProductionAtCurrentBaseState prevents a new copy from being queued until
					// a valid expansion FACT exists again.
					if (!secureProductionReservation && !remoteProductionReservation && baseBuilder.RequiresExpansionProductionPlacement(current.Item) &&
						!baseBuilder.TryGetExpansionProductionCenter(out _))
					{
						if (observedTimingDoneTick >= 0 &&
							world.WorldTick - observedTimingDoneTick >= baseBuilder.Info.ExpansionPlacementCompletedHoldTimeoutTicks)
						{
							FransBotLog.BotDebug(world,
								"{0}: expansion-routed completed {1} lost every valid expansion FACT for {2} WT; cancelling the stale Building-queue item instead of deadlocking production.",
								player, current.Item, baseBuilder.Info.ExpansionPlacementCompletedHoldTimeoutTicks);
							MarkTrackedCancellationIssued(queue, current, "ExpansionPlacementFactUnavailable");
							bot.QueueOrder(Order.CancelProduction(queue.Actor, current.Item, 1));
						}
						return true;
					}

					var placementRetryTicks = baseBuilder.Info.CompletedPlacementRetryTicks;
					if (baseBuilder.Info.RefineryTypes.Contains(current.Item) && baseBuilder.oreMineRefineryTarget.HasValue)
						placementRetryTicks = Math.Max(placementRetryTicks, baseBuilder.Info.OreMineRefineryPlacementPendingRetryTicks);

					var samePendingPlacement = placementPendingItem == current.Item && placementPendingQueueActorId == queue.Actor.ActorID &&
						placementPendingIssuedTick >= 0;
					if (samePendingPlacement)
					{
						var pendingAge = world.WorldTick - placementPendingIssuedTick;
						var confirmationTimeout = Math.Max(placementRetryTicks, baseBuilder.Info.CompletedPlacementConfirmationTimeoutTicks);
						if (pendingAge < confirmationTimeout)
							return true;

						placementPendingConfirmationRetries++;
							if (placementPendingConfirmationRetries >= baseBuilder.Info.CompletedPlacementConfirmationMaximumRetries)
							{
								FransBotLog.BotDebug(world,
									"{0}: completed Building-queue item {1} on actor {2} remained READY after {3} unconfirmed native placement attempts; cancelling the stale item so the shared Building queue cannot deadlock.",
									player, current.Item, queue.Actor.ActorID, placementPendingConfirmationRetries);
								MarkTrackedCancellationIssued(queue, current, "PlacementConfirmationRetriesExhausted");
								bot.QueueOrder(Order.CancelProduction(queue.Actor, current.Item, 1));
								placementPendingItem = null;
								placementPendingQueueActorId = 0;
								placementPendingIssuedTick = -1;
								placementPendingConfirmationRetries = 0;
								lastFailedBuilding = current.Item;
								baseBuilder.NotifyOpeningBuildingFailed(current.Item);
								if (baseBuilder.Info.NavalProductionTypes.Contains(current.Item))
								{
									var retryTicks = Math.Max(1, baseBuilder.Info.StructureProductionResumeDelay);
									navalPlacementBlockedUntilTick[current.Item] = world.WorldTick + retryTicks;
									navalPlacementPrecheckRetryTick.Remove(current.Item);
								}
								return true;
							}

						// Retry from a fresh location/BuildingInfluence snapshot. The retry counter stays
						// attached to this exact queue item until it physically disappears or is cancelled.
						placementPendingIssuedTick = -1;
					}

					var type = FransBuildingType.Building;
					CPos? location = null;
					var variant = 0;
					var orderString = "PlaceBuilding";
					var actorInfo = world.Map.Rules.Actors[current.Item];
					var plugInfo = actorInfo.TraitInfoOrDefault<PlugInfo>();
					if (plugInfo != null)
					{
						var possible = world.ActorsWithTrait<Pluggable>().FirstOrDefault(a => a.Actor.Owner == player && a.Trait.AcceptsPlug(plugInfo.Type));
						if (possible.Actor != null) { orderString = "PlacePlug"; location = possible.Actor.Location + possible.Trait.Info.Offset; }
					}
					else
					{
						if (baseBuilder.Info.RefineryTypes.Contains(actorInfo.Name)) type = FransBuildingType.Refinery;
						if (secureProductionReservation && secureProductionFact != null)
						{
							(location, baseCenterKeepsFailing, variant) = ChooseBuildLocation(current.Item, true, type, secureProductionFact.Location);
						}
						else if (remoteProductionReservation && remoteProductionFact != null)
						{
							(location, baseCenterKeepsFailing, variant) = ChooseBuildLocation(current.Item, true, type, remoteProductionFact.Location);
						}
						else if (baseBuilder.Info.NavalProductionTypes.Contains(current.Item))
						{
							if (baseBuilder.expansionStateService?.TryGetNavalProductionLocation(current.Item, out var navalLocation) == true)
							{
								location = navalLocation;
								baseCenterKeepsFailing = navalLocation;
							}
						}
						else
						{
							if (TryManageFootprintClearance(bot, current.Item, type, out var clearedPreferred))
								return true;
							if (clearedPreferred.HasValue)
							{
								location = clearedPreferred.Value;
								baseCenterKeepsFailing = baseBuilder.GetBaseCenter();
							}
							else
								(location, baseCenterKeepsFailing, variant) = ChooseBuildLocation(current.Item, true, type);
						}
					}
					if (location == null)
					{
						if (++failCount >= baseBuilder.Info.MaximumFailedPlacementAttempts)
						{
							FransBotLog.BotDebug(world, "{0}: FransBaseBuilder has nowhere to place {1}.", player, current.Item);
							MarkTrackedCancellationIssued(queue, current, "MaximumPlacementFailuresReached");
							bot.QueueOrder(Order.CancelProduction(queue.Actor, current.Item, 1));
							lastFailedBuilding = current.Item;

							if (baseBuilder.Info.NavalProductionTypes.Contains(current.Item))
							{
								var retryTicks = Math.Max(1, baseBuilder.Info.StructureProductionResumeDelay);
								var blockedUntil = world.WorldTick + retryTicks;
								navalPlacementBlockedUntilTick[current.Item] = blockedUntil;
								navalPlacementPrecheckRetryTick.Remove(current.Item);
								FransBotLog.BotDebug(world,
									"{0}: naval producer {1} placement failed after production; exact-type rebuild blocked for {2} WT until {3}, then legal placement must be re-verified before production can restart.",
									player, current.Item, retryTicks, blockedUntil);

								// Naval placement failure is local to this exact producer type. Do not feed the
								// generic expansion/stuck-base recovery path, which can immediately clear the
								// failure and recreate the same expensive SPEN/SYRD loop.
								failCount = 0;
								baseCenterKeepsFailing = null;
							}
							else
							{
								baseBuilder.NotifyOpeningBuildingFailed(current.Item);
								if (baseBuilder.BaseExpansionModules == null || baseBuilder.BaseExpansionModules.Length == 0)
								{
									baseBuilder.combatIntelService.EnsureCurrentSnapshot();
									cachedBuildings = baseBuilder.combatIntelService.OwnedActors.Count(a => a.Info.HasTraitInfo<BuildingInfo>());
									cachedBases = world.ActorsHavingTrait<BaseProvider>().Count(a => a.Owner == player);
								}
							}
						}
					}
					else
					{
						ClearFootprintClearanceState();
						failCount = 0;
						FransBotLog.BotDebug(world,
							"{0}: BUILD TIMING placement ISSUED {1} at {2} from {3} queue actor {4} at WT {5}; complete-to-place delay {6} WT.",
							player, current.Item, location.Value, Category, queue.Actor.ActorID, world.WorldTick,
							observedTimingDoneTick >= 0 ? world.WorldTick - observedTimingDoneTick : -1);
						if (drainingUnderExpansionLock)
							FransBotLog.BotDebug(world,
								"[BASEBUILDER DRAIN] Tick={0} Player={1} structure={2} queue={3} queueActor={4} state=ReadyToPlace action=PlacementIssued location={5}",
								world.WorldTick, player, current.Item, Category, queue.Actor.ActorID, location.Value);
						MarkTrackedPlacementIssued(queue, current, location.Value);
						if (placementPendingItem != current.Item || placementPendingQueueActorId != queue.Actor.ActorID)
							placementPendingConfirmationRetries = 0;
						placementPendingItem = current.Item;
						placementPendingQueueActorId = queue.Actor.ActorID;
						placementPendingIssuedTick = world.WorldTick;
						bot.QueueOrder(new Order(orderString, player.PlayerActor, Target.FromCell(world, location.Value), false)
						{
							TargetString = current.Item,
							ExtraLocation = new CPos(variant, 0),
							ExtraData = queue.Actor.ActorID,
							SuppressVisualFeedback = true
						});

						if (baseBuilder.Info.ProductionTypes.Contains(current.Item) || baseBuilder.Info.TechTypes.Contains(current.Item) || baseBuilder.Info.RefineryTypes.Contains(current.Item))
						{
							var numRef = baseBuilder.RefineryBuildings.Actors.Count(a => !a.IsDead) + (baseBuilder.Info.RefineryTypes.Contains(current.Item) ? 1 : 0);
							var numProd = baseBuilder.ProductionBuildings.Actors.Count(a => !a.IsDead) + (baseBuilder.Info.ProductionTypes.Contains(current.Item) ? 1 : 0);
							var numTech = playerBuildings.Count(a => baseBuilder.Info.TechTypes.Contains(a.Info.Name)) + (baseBuilder.Info.TechTypes.Contains(current.Item) ? 1 : 0);
							var tolerateOnCash = playerResources.GetCashAndResources() / Math.Max(baseBuilder.Info.PerExpansionTolerateOnCash, 1);
							var expansionTol = baseBuilder.Info.ExpansionTolerate.Length > 0 ? baseBuilder.Info.ExpansionTolerate[0] : 0;
							var forceTol = baseBuilder.Info.ForceExpansionTolerate.Length > 0 ? baseBuilder.Info.ForceExpansionTolerate[0] : 0;
							if (numRef >= baseBuilder.Info.InitialMinimumRefineryCount + baseBuilder.Info.AdditionalMinimumRefineryCount && numProd > 0 && numProd + numTech - expansionTol - tolerateOnCash >= numRef)
							{
								var force = numProd + numTech - forceTol - tolerateOnCash >= numRef;
								foreach (var be in baseBuilder.BaseExpansionModules ?? Array.Empty<IBotBaseExpansion>()) be.UpdateExpansionParams(bot, true, force, null);
							}
						}
						return true;
					}
				}
				return true;
			}

			ActorInfo ChooseBuildingToBuild(ProductionQueue queue)
			{
				var buildables = queue.BuildableItems().ToList();
				var opening = baseBuilder.ChooseOpeningBuilding(buildables, Category);
				if (!baseBuilder.OpeningComplete && baseBuilder.Info.BuildingQueues.Contains(Category))
				{
					if (opening != null)
						return opening;

					// OpeningStage.Mcv has no remaining mandatory structure, and intentionally
					// waits for the MCV to become physical. Let genuine emergency
					// low power break through this one stage so the MCV cannot spend thousands of WT
					// crawling at reduced production speed. No other dynamic building is unlocked.
					if (baseBuilder.openingStage == OpeningStage.Mcv)
					{
						var power = GetBestProducible(baseBuilder.Info.PowerTypes, buildables,
							a => a.TraitInfos<PowerInfo>().Where(i => i.EnabledByDefault).Sum(p => p.Amount));
						if (playerPower != null && playerPower.ExcessPower < minimumExcessPower &&
							power != null && PowerAmount(power) > 0)
							return LogChoice(queue, power, "emergency low power during opening MCV");
					}

					return null;
				}
				return ChooseDynamicBuilding(queue, buildables);
			}

			ActorInfo ChooseDynamicBuilding(ProductionQueue queue, List<ActorInfo> buildables)
			{
				var power = GetBestProducible(baseBuilder.Info.PowerTypes, buildables, a => a.TraitInfos<PowerInfo>().Where(i => i.EnabledByDefault).Sum(p => p.Amount));
				if (playerPower != null && playerPower.ExcessPower < minimumExcessPower && power != null && PowerAmount(power) > 0)
					return LogChoice(queue, power, "low power");

				// immediately after the first physical PIONEER-MCV, the reserved
				// expansion PROC is the first normal Building item. SECURE producer, Navy, Radar,
				// tech and capacity growth all wait behind it; only genuine low-power recovery above
				// may precede this economic critical path. ExpansionManager owns StartProduction.
				if (baseBuilder.ReadyForFirstExpansionRefineryPrebuild)
					return null;

				if (baseBuilder.TryGetSecureFootholdProductionNeed(out var secureTargetId, out var secureCenter, out var preferWarFactory))
				{
					ActorInfo secureProducer = null;
					if (preferWarFactory)
						secureProducer = buildables.Where(a => baseBuilder.Info.WarFactoryTypes.Contains(a.Name) && baseBuilder.BelowHardBuildingLimit(a.Name))
							.OrderBy(a => a.Name).FirstOrDefault();
					secureProducer ??= buildables.Where(a => baseBuilder.Info.BarracksTypes.Contains(a.Name) && baseBuilder.BelowHardBuildingLimit(a.Name))
						.OrderBy(a => a.Name).FirstOrDefault();
					if (secureProducer == null && !preferWarFactory)
						secureProducer = buildables.Where(a => baseBuilder.Info.WarFactoryTypes.Contains(a.Name) && baseBuilder.BelowHardBuildingLimit(a.Name))
							.OrderBy(a => a.Name).FirstOrDefault();

					if (secureProducer != null && HasSufficientPower(secureProducer))
					{
						secureProductionTargetId = secureTargetId;
						secureProductionCenter = secureCenter;
						secureProductionItem = secureProducer.Name;
						return LogChoice(queue, secureProducer, preferWarFactory
							? "SECURE foothold requires local WEAP at Prosperous/Surplus economy"
							: "SECURE foothold requires local TENT/BARR before completion");
					}
					if (secureProducer != null && power != null && !HasSufficientPower(secureProducer))
						return LogChoice(queue, power, "power before mandatory SECURE foothold production building");
				}

				// NAVAL SUPPORT/coastal staging is strategic state, not Building-queue ownership.
				// Do not freeze Radar/tech merely because an MCV is searching for shoreline build radius.
				// Yield only when there is a concrete, currently placeable naval-producer job. The MCV
				// manager still owns the exact SPEN/SYRD item through frans-expansion-lock once it starts.
				var concreteMissionCriticalNavalJob =
					baseBuilder.expansionStateService?.MissionCriticalNavalAccessRequired == true &&
					baseBuilder.expansionStateService?.NavalProductionOpportunityAvailable == true &&
					baseBuilder.CountOwnedOrQueued(baseBuilder.Info.NavalProductionTypes) == 0;
				if (concreteMissionCriticalNavalJob)
				{
					var navalProducer = buildables
						.Where(a => baseBuilder.Info.NavalProductionTypes.Contains(a.Name) && baseBuilder.BelowLimit(a.Name))
						.Where(a => baseBuilder.CanQueueProductionAtCurrentBaseState(a.Name))
						.Where(a => CanStartNavalProducer(a.Name))
						.OrderBy(a => a.Name)
						.FirstOrDefault();
					if (navalProducer != null && HasSufficientPower(navalProducer))
						return LogChoice(queue, navalProducer, "mission-critical NAVAL SUPPORT naval producer: legal shoreline exists now");
					if (navalProducer != null && power != null && !HasSufficientPower(navalProducer))
						return LogChoice(queue, power, "power before mission-critical NAVAL SUPPORT naval producer");
				}



				if (baseBuilder.TryGetRemoteBaseProductionNeed(out var remoteFact, out var remoteNeedsWarFactory, out var remoteNeedsBarracks))
				{
					ActorInfo remoteProducer = null;
					if (remoteNeedsWarFactory)
						remoteProducer = buildables.Where(a => baseBuilder.Info.WarFactoryTypes.Contains(a.Name) && baseBuilder.BelowHardBuildingLimit(a.Name))
							.OrderBy(a => a.Name).FirstOrDefault();
					if (remoteProducer == null && remoteNeedsBarracks)
						remoteProducer = buildables.Where(a => baseBuilder.Info.BarracksTypes.Contains(a.Name) && baseBuilder.BelowHardBuildingLimit(a.Name))
							.OrderBy(a => a.Name).FirstOrDefault();

					if (remoteProducer != null && HasSufficientPower(remoteProducer))
					{
						remoteProductionFactActorId = remoteFact.ActorID;
						remoteProductionCenter = remoteFact.Location;
						remoteProductionItem = remoteProducer.Name;
						return LogChoice(queue, remoteProducer, remoteNeedsWarFactory
							? "REMOTE BASE on separate landmass requires local WEAP before relying on main-base/LST reinforcement"
							: "REMOTE BASE on separate landmass requires local TENT/BARR before relying on main-base/LST reinforcement");
					}
					if (remoteProducer != null && power != null && !HasSufficientPower(remoteProducer))
						return LogChoice(queue, power, "power before mandatory REMOTE BASE local production");
				}

				if (baseBuilder.OpeningComplete && baseBuilder.CountOwned(baseBuilder.Info.RadarTypes) > 0 &&
					baseBuilder.economicStateService.IsProsperousOrBetter)
				{
					if (baseBuilder.CountOwnedOrQueued(baseBuilder.Info.AdvancedTechCenterTypes) == 0)
					{
						var advancedTech = buildables
							.Where(a => baseBuilder.Info.AdvancedTechCenterTypes.Contains(a.Name) && baseBuilder.BelowLimit(a.Name))
							.OrderBy(a => a.Name).FirstOrDefault();
						if (advancedTech != null && HasSufficientPower(advancedTech))
							return LogChoice(queue, advancedTech, "Prosperous tech progression: physical Radar + sustainable economy unlock faction advanced-tech center");
						if (advancedTech != null && power != null && !HasSufficientPower(advancedTech))
							return LogChoice(queue, power, "power before Prosperous advanced-tech center");
					}

					// MSLO is a Defense-queue structure in current RA. BaseBuilder owns the strategic
					// decision through TryGetStrategicDefenseQueueRequest; DefenseCommander remains
					// the sole physical owner of Defense queue StartProduction/PlaceBuilding orders.
				}

				if (baseBuilder.CountOwned(baseBuilder.Info.WarFactoryTypes) >= 1 && baseBuilder.CountOwned(baseBuilder.Info.RadarTypes) == 0)
				{
					var radar = buildables.Where(a => baseBuilder.Info.RadarTypes.Contains(a.Name) && baseBuilder.BelowLimit(a.Name))
						.OrderBy(a => a.Name).FirstOrDefault();
					if (radar != null && baseBuilder.RadarTechAllowed(out var parityResponse, out var radarReason))
					{
						if (HasSufficientPower(radar))
							return LogChoice(queue, radar, parityResponse ? $"enemy-tech radar parity: {radarReason}" : $"Growing radar progression: {radarReason}");
						if (power != null)
							return LogChoice(queue, power, "power before Growing radar progression");
					}
				}

				// A completed Radar Dome should be exploited promptly instead of becoming dead capital.
				// Faction prerequisites decide whether HPAD or AFLD is actually buildable.
				if (baseBuilder.ShouldExploitRadarWithAirProduction())
				{
					var airProduction = buildables
						.Where(a => baseBuilder.Info.RadarFollowupAirProductionTypes.Contains(a.Name) && baseBuilder.BelowLimit(a.Name))
						.OrderBy(a => a.Name).FirstOrDefault();
					if (airProduction != null && HasSufficientPower(airProduction))
						return LogChoice(queue, airProduction, baseBuilder.economicStateService.IsStruggling
							? "first-air capability: physical Radar + PROC/HARV maturity fallback despite Struggling"
							: "immediate Radar Dome exploitation with first air production");
					if (airProduction != null && power != null && !HasSufficientPower(airProduction))
						return LogChoice(queue, power, "power before Radar Dome air-production follow-up");
				}

				// Observed enemy radar tech is allowed to interrupt the optional post-MCV production tail.
				// This is the guide's simplest tech-parity rule: respond when the opponent proves the need.
				if (baseBuilder.CountOwned(baseBuilder.Info.WarFactoryTypes) >= 1 && baseBuilder.CountOwned(baseBuilder.Info.RadarTypes) == 0)
				{
					var parityRadar = buildables.Where(a => baseBuilder.Info.RadarTypes.Contains(a.Name) && baseBuilder.BelowLimit(a.Name))
						.OrderBy(a => a.Name).FirstOrDefault();
					if (parityRadar != null && baseBuilder.RadarTechAllowed(out var parityNow, out var parityReason) && parityNow)
					{
						if (HasSufficientPower(parityRadar))
							return LogChoice(queue, parityRadar, $"enemy-tech radar parity: {parityReason}");
						if (power != null)
							return LogChoice(queue, power, "power before enemy-tech radar parity");
					}
				}

				// The first expansion refinery reservation above has precedence. Once it no longer
				// owns the critical path, finish only the configured post-MCV tail. keeps the
				// opening infantry producer count at one; duplication belongs to Prosperous->Surplus pressure.
				if (baseBuilder.OpeningComplete)
				{
					if (baseBuilder.Info.PostMcvOpeningPowerTarget > 0 &&
						baseBuilder.CountOwned(baseBuilder.Info.PowerTypes) < baseBuilder.Info.PostMcvOpeningPowerTarget &&
						power != null)
						return LogChoice(queue, power, "Fransbot opening post-MCV power tail");

					if (baseBuilder.Info.PostMcvOpeningBarracksTarget > 0 &&
						baseBuilder.CountOwned(baseBuilder.Info.BarracksTypes) < baseBuilder.Info.PostMcvOpeningBarracksTarget)
					{
						var barracks = buildables
							.Where(a => baseBuilder.Info.BarracksTypes.Contains(a.Name) && baseBuilder.BelowLimit(a.Name))
							.OrderBy(a => a.Name)
							.FirstOrDefault();
						if (barracks != null && HasSufficientPower(barracks))
							return LogChoice(queue, barracks, "Fransbot opening post-MCV infantry-production tail");
						if (barracks != null && power != null && !HasSufficientPower(barracks))
							return LogChoice(queue, power, "power before Fransbot opening infantry-production tail");
					}

				}

				// Preserve the proven opening/explicit MCV-expansion refinery requests. After the
				// opening MCV physically exists, generic refinery counts no longer create PROC demand.
				if (baseBuilder.RequestedRefineries.Count > 0 ||
					(!baseBuilder.OpeningMcvCompleted && !baseBuilder.HasAdequateRefineryCount()))
				{
					var refinery = GetBestProducible(baseBuilder.Info.RefineryTypes, buildables);
					if (refinery != null && HasSufficientPower(refinery)) return LogChoice(queue, refinery, "opening/explicit expansion refinery need");
					if (power != null && refinery != null && !HasSufficientPower(refinery)) return LogChoice(queue, power, "power before opening/explicit expansion refinery");
				}

				if (baseBuilder.OpeningComplete &&
					baseBuilder.CountOwned(baseBuilder.Info.WarFactoryTypes) >= 1 &&
					baseBuilder.CountOwnedOrQueued(baseBuilder.Info.NavalProductionTypes) == 0 &&
					baseBuilder.expansionStateService?.NavalCapabilityDemandActive == true &&
					baseBuilder.expansionStateService?.NavalProductionOpportunityAvailable == true)
				{
					var firstNavalProducer = buildables
						.Where(a => baseBuilder.Info.NavalProductionTypes.Contains(a.Name) && baseBuilder.BelowLimit(a.Name))
						.Where(a => baseBuilder.CanQueueProductionAtCurrentBaseState(a.Name))
						.Where(a => CanStartNavalProducer(a.Name))
						.OrderBy(a => a.Name)
						.FirstOrDefault();
					if (firstNavalProducer != null && HasSufficientPower(firstNavalProducer))
						return LogChoice(queue, firstNavalProducer, "first naval capability: topology/mission-proven demand is active and legal shoreline exists");
					if (firstNavalProducer != null && power != null && !HasSufficientPower(firstNavalProducer))
						return LogChoice(queue, power, "power before topology/mission-proven naval-production capability");
				}

				// Post-opening PROC demand is mine-first. One visible relevant ore-mine may own one physical
				// PROC. Naval production may pre-empt this only while topology/mission-proven naval demand is
				// active; shoreline opportunity by itself never outranks the 1 ore-mine -> 1 PROC economy model.
				var oreNodeRefinery = GetBestProducible(baseBuilder.Info.RefineryTypes, buildables);
				if (oreNodeRefinery != null &&
					baseBuilder.TryGetMineNeedingRefinery(oreNodeRefinery.Name, out var oreMineTarget))
				{
					if (HasSufficientPower(oreNodeRefinery))
					{
						baseBuilder.oreMineRefineryTarget = oreMineTarget;
						baseBuilder.oreMineRefineryClaimTick = world.WorldTick;
						return LogChoice(queue, oreNodeRefinery, $"ore-node PROC for physically serviceable mine at {oreMineTarget}");
					}

					if (power != null && !HasSufficientPower(oreNodeRefinery))
						return LogChoice(queue, power, $"power before ore-node PROC for physically serviceable mine at {oreMineTarget}");
				}

				// Growing must keep developing the core base instead of leaving the Building queue idle
				// while Radar is still economically gated. Establish the configured main-base WEAP
				// capacity first; later WEAP still use normal maturity and expansion placement.
				if (baseBuilder.Info.MaximumMainBaseWarFactories > 0 &&
					baseBuilder.expansionStateService?.NavalCapabilityDemandActive != true &&
					baseBuilder.CountOwned(baseBuilder.Info.WarFactoryTypes) < baseBuilder.Info.MaximumMainBaseWarFactories)
				{
					var coreWarFactory = buildables
						.Where(a => baseBuilder.Info.WarFactoryTypes.Contains(a.Name) && baseBuilder.BelowLimit(a.Name))
						.OrderBy(a => a.Name).FirstOrDefault();
					if (coreWarFactory != null && HasSufficientPower(coreWarFactory))
						return LogChoice(queue, coreWarFactory, "Growing core vehicle-production capacity");
					if (coreWarFactory != null && power != null && !HasSufficientPower(coreWarFactory))
						return LogChoice(queue, power, "power before Growing core vehicle-production capacity");
				}

				if (baseBuilder.economicStateService.IsProsperousOrBetter &&
					waterState == FransWaterCheck.EnoughWater &&
					baseBuilder.CountOwned(baseBuilder.Info.NavalProductionTypes) > 0 &&
					baseBuilder.CountOwned(baseBuilder.Info.NavalCapitalTechTypes) == 0)
				{
					var navalTech = buildables
						.Where(a => baseBuilder.Info.NavalCapitalTechTypes.Contains(a.Name) && baseBuilder.BelowLimit(a.Name))
						.OrderBy(a => a.Name)
						.FirstOrDefault();
					if (navalTech != null && HasSufficientPower(navalTech))
						return LogChoice(queue, navalTech, "Prosperous economy unlocks naval capital-ship tech for long-range shore bombardment");
					if (navalTech != null && power != null && !HasSufficientPower(navalTech))
						return LogChoice(queue, power, "power before naval capital-ship tech");
				}

				if (baseBuilder.economicStateService.IsProsperousOrBetter)
				{
					// Explicit four-state policy: Prosperous duplicates each relevant military producer
					// category toward two; true Surplus grows toward the larger configured targets.
					// Growing never reaches this block, so there is no hidden half-state.
					var fullSurplus = baseBuilder.economicStateService.IsSurplus;
					var production = GetEconomicCapacityProductionCandidate(buildables, fullSurplus);
					if (production != null && HasSufficientPower(production))
						return LogChoice(queue, production, fullSurplus
							? "Surplus snowball: grow production toward long-run throughput targets"
							: "Prosperous policy: duplicate military production capacity toward two per category");
					if (power != null && production != null && !HasSufficientPower(production))
						return LogChoice(queue, power, fullSurplus
							? "power before Surplus producer snowball"
							: "power before Prosperous producer duplication");
				}

				if (playerResources.ResourceCapacity > 0 && playerResources.Resources > 0.8 * playerResources.ResourceCapacity)
				{
					var silo = GetBestProducible(baseBuilder.Info.SiloTypes, buildables);
					if (silo != null && HasSufficientPower(silo)) return LogChoice(queue, silo, "resource storage");
				}

				// No generic weighted fallback exists. If no explicit strategic/economy-state rule
				// above requests a structure, leave the Building queue free for the next explicit need.
				return null;
			}

			ActorInfo LogChoice(ProductionQueue queue, ActorInfo actor, string reason)
			{
				FransBotLog.BotDebug(world, "{0}: FransBaseBuilder chooses {1}: {2}.", queue.Actor.Owner, actor.Name, reason);
				return actor;
			}

			int PowerAmount(ActorInfo a) => a.TraitInfos<PowerInfo>().Where(i => i.EnabledByDefault).Sum(p => p.Amount);
			bool HasSufficientPower(ActorInfo a) => playerPower == null || PowerAmount(a) + playerPower.ExcessPower >= baseBuilder.Info.MinimumExcessPower;

			ActorInfo GetBestProducible(FrozenSet<string> actors, IEnumerable<ActorInfo> buildables, Func<ActorInfo, int> score = null)
			{
				var available = buildables.Where(a => actors.Contains(a.Name) && baseBuilder.BelowLimit(a.Name));
				return score == null ? available.OrderBy(a => a.Name).FirstOrDefault() : available.OrderByDescending(score).ThenBy(a => a.Name).FirstOrDefault();
			}


			bool CanStartNavalProducer(string actorType)
			{
				if (!baseBuilder.Info.NavalProductionTypes.Contains(actorType))
					return true;

				if (navalPlacementBlockedUntilTick.TryGetValue(actorType, out var blockedUntil))
				{
					if (world.WorldTick < blockedUntil)
						return false;

					navalPlacementBlockedUntilTick.Remove(actorType);
				}

				if (navalPlacementPrecheckRetryTick.TryGetValue(actorType, out var retryAt) && world.WorldTick < retryAt)
					return false;

				// FransMcvExpansionManager owns the sole SPEN/SYRD placement resolver. BaseBuilder
				// uses that exact result both before production and again after the item completes,
				// so the two modules cannot disagree and create a produce/cancel loop.
				var verified = baseBuilder.expansionStateService?.TryGetNavalProductionLocation(actorType, out _) == true;
				if (verified)
				{
					navalPlacementPrecheckRetryTick.Remove(actorType);
					return true;
				}

				// A negative exact-footprint probe is cheap state, not a production attempt. Avoid
				// rescanning every Building tick, but retry soon enough to notice a newly opened coast.
				navalPlacementPrecheckRetryTick[actorType] = world.WorldTick + Math.Max(1, Math.Min(250, baseBuilder.Info.StructureProductionResumeDelay));
				return false;
			}

			ActorInfo GetEconomicCapacityProductionCandidate(IEnumerable<ActorInfo> buildables, bool fullSurplus)
			{
				var categories = new[]
				{
					(Types: baseBuilder.Info.SurplusAirProductionTypes, Target: baseBuilder.Info.SurplusAirProductionTarget, Priority: baseBuilder.Info.SurplusAirProductionPriority, Name: "air"),
					(Types: baseBuilder.Info.WarFactoryTypes, Target: baseBuilder.Info.SurplusWarFactoryTarget, Priority: baseBuilder.Info.SurplusWarFactoryPriority, Name: "vehicle"),
					(Types: baseBuilder.Info.NavalProductionTypes, Target: baseBuilder.Info.SurplusNavalProductionTarget, Priority: baseBuilder.Info.SurplusNavalProductionPriority, Name: "naval"),
					(Types: baseBuilder.Info.BarracksTypes, Target: baseBuilder.Info.SurplusInfantryProductionTarget, Priority: baseBuilder.Info.SurplusInfantryProductionPriority, Name: "infantry")
				};

				foreach (var item in categories
					.Select(c => (Category: c, Count: baseBuilder.CountOwnedOrQueued(c.Types), EffectiveTarget: fullSurplus ? c.Target : Math.Min(2, c.Target)))
					.Where(x => x.Count < x.EffectiveTarget)
					.OrderByDescending(x => (x.EffectiveTarget - x.Count) * 1000 / Math.Max(1, x.EffectiveTarget))
					.ThenByDescending(x => x.Category.Priority)
					.ThenBy(x => x.Category.Name))
				{
					var category = item.Category;
					var effectiveTarget = item.EffectiveTarget;
					if (category.Name == "naval" && (waterState != FransWaterCheck.EnoughWater ||
						!AIUtils.IsAreaAvailable<GivesBuildableArea>(world, player, world.Map, baseBuilder.Info.CheckForWaterRadius, baseBuilder.Info.WaterTerrainTypes)))
						continue;
					if (baseBuilder.CountOwnedOrQueued(category.Types) >= effectiveTarget)
						continue;

					var candidate = buildables
						.Where(a => category.Types.Contains(a.Name) && baseBuilder.Info.SurplusProductionBuildingTypes.Contains(a.Name))
						.Where(a => baseBuilder.BelowLimit(a.Name) && baseBuilder.CanQueueProductionAtCurrentBaseState(a.Name))
						.Where(a => category.Name != "naval" || CanStartNavalProducer(a.Name))
						.Where(a => !baseBuilder.Info.BuildingDelays.TryGetValue(a.Name, out var delay) || delay <= world.WorldTick)
						.OrderBy(a => CountStructureAndVariants(a.Name))
						.ThenBy(a => a.Name)
						.FirstOrDefault();
					if (candidate != null)
					{
						FransBotLog.BotDebug(world,
							"{0}: {1} capacity selects {2} category actor {3}; current combined count {4}/{5}, normalized capacity deficit; personality priority tiebreak {6}.",
							player, fullSurplus ? "Surplus" : "Prosperous", category.Name, candidate.Name,
							baseBuilder.CountOwnedOrQueued(category.Types), effectiveTarget, category.Priority);
						return candidate;
					}
				}

				return null;
			}

			int CountStructureAndVariants(string name)
			{
				var actorInfo = world.Map.Rules.Actors[name];
				var variants = actorInfo.TraitInfoOrDefault<PlaceBuildingVariantsInfo>()?.Actors ?? [];
				return playerBuildings.Count(a => a.Info.Name == name || variants.Contains(a.Info.Name)) + (baseBuilder.BuildingsBeingProduced.TryGetValue(name, out var n) ? n : 0);
			}

			(CPos? Location, CPos? BaseCenter, int Variant) ChooseBuildLocation(string actorType, bool distanceToBaseIsImportant, FransBuildingType type, CPos? localProductionFactCenter = null)
			{
				var actorInfo = world.Map.Rules.Actors[actorType];
				var bi = actorInfo.TraitInfoOrDefault<BuildingInfo>();
				if (bi == null) return (null, null, 0);

				(CPos? Location, CPos Center, int Variant) FindPos(CPos center, CPos target, int minRange, int maxRange, int? maintainRange = null, int directionWeightPercent = 100, Func<CPos, bool> cellFilter = null)
				{
					var cells = world.Map.FindTilesInAnnulus(center, minRange, maxRange);
					if (center != target)
					{
						if (maintainRange == null)
						{
							var w = directionWeightPercent.Clamp(0, 100);
							cells = cells.OrderBy(c => (long)(100 - w) * (c - center).LengthSquared + (long)w * (c - target).LengthSquared)
								.ThenBy(c => (c - center).LengthSquared).ThenBy(c => c.X).ThenBy(c => c.Y);
						}
						else
						{
							var theta = maintainRange.Value;
							var delta = (target - center).Length - maintainRange.Value;
							cells = cells.OrderBy(c => delta * (c - target).LengthSquared + theta * (c - center).LengthSquared).ThenBy(c => c.X).ThenBy(c => c.Y);
						}
					}
					else cells = cells.OrderBy(c => (c - center).LengthSquared).ThenBy(c => c.X).ThenBy(c => c.Y);

					// Spacing: treat MinimumStructureSpacingCells as an ideal rather than a hard
					// hard target and then fell straight back to the first compact legal cell. In RA,
					// normal RequiresBuildableArea has a short adjacency range, so a requested four-cell
					// lane is often impossible. That made most non-refinery structures end up touching.
					//
					// Keep the configured gap as the ideal, but if it cannot be reached then choose the
					// legal cell with the largest ACTUAL clearance from existing friendly buildings.
					// This preserves normal OpenRA placement rules while spreading the base as much as
					// the current buildable-area chain permits.
					CPos? bestLegalSpacedLocation = null;
					var bestLegalSpacedVariant = 0;
					var bestLegalClearance = -1;

					foreach (var cell in cells)
					{
						if (cellFilter != null && !cellFilter(cell))
							continue;

						var variant = 0;
						var variantInfo = actorInfo;
						var variantBuildingInfo = bi;
						var variants = actorInfo.TraitInfoOrDefault<PlaceBuildingVariantsInfo>();
						if (variants?.Actors != null && variants.Facings != null && variants.Facings.Length > 0 && center != target)
						{
							var vector = world.Map.CenterOfCell(target) - world.Map.CenterOfCell(center);
							var desired = new WAngle(WAngle.ArcSin((int)((long)Math.Abs(vector.X) * 1024 / Math.Max(1, vector.Length))).Angle);
							if (vector.X > 0 && vector.Y >= 0) desired = new WAngle(512) - desired;
							else if (vector.X < 0 && vector.Y >= 0) desired = new WAngle(512) + desired;
							else if (vector.X < 0 && vector.Y < 0) desired = -desired;
							var bestDelta = int.MaxValue;
							for (var i = 0; i < variants.Facings.Length; i++)
							{
								var d = Math.Min((desired - variants.Facings[i]).Angle, (variants.Facings[i] - desired).Angle);
								if (d < bestDelta) { bestDelta = d; variant = i; }
							}
						}
						if (variant != 0 && variants?.Actors != null && variant - 1 < variants.Actors.Length)
						{
							variantInfo = world.Map.Rules.Actors[variants.Actors[variant - 1]];
							variantBuildingInfo = variantInfo.TraitInfoOrDefault<BuildingInfo>();
						}
						if (baseBuilder.IntersectsGroundStagingReservation(cell, variantBuildingInfo)) continue;
						if (!world.CanPlaceBuilding(cell, variantInfo, variantBuildingInfo, null)) continue;
						if (distanceToBaseIsImportant && !variantBuildingInfo.IsCloseEnoughToBase(world, player, variantInfo, null, cell)) continue;

						// Unified risk ownership: placement code may optimize geometry/spacing, but it
						// no longer invents its own threat model. Defensive structures tolerate a hot
						// frontline; economy/production/tech structures reject critical cells.
						var placementTolerance = FransRiskTolerance.Cautious;
						if (baseBuilder.riskModelService.EvaluateStrategicCell(
							cell, FransRiskRole.BuildingPlacement, placementTolerance).IsCritical)
							continue;

						// Prefer generous lanes between normal structures and a smaller lane around
						// base defenses. This remains a preference, not a hard rule: constrained maps
						// must still be able to fall back to any legal compact placement.
						var preferredGap = baseBuilder.Info.MinimumStructureSpacingCells;

						if (preferredGap <= 0)
							return (cell, center, variant);

						var candidateDimensions = variantBuildingInfo.Dimensions;
						var candidateMinX = cell.X;
						var candidateMinY = cell.Y;
						var candidateMaxX = cell.X + candidateDimensions.X - 1;
						var candidateMaxY = cell.Y + candidateDimensions.Y - 1;
						var minimumClearance = int.MaxValue;

						foreach (var existing in playerBuildings)
						{
							if (existing == null || existing.IsDead || !existing.IsInWorld)
								continue;

							var existingBuildingInfo = existing.Info.TraitInfoOrDefault<BuildingInfo>();
							if (existingBuildingInfo == null)
								continue;

							var existingMinX = existing.Location.X;
							var existingMinY = existing.Location.Y;
							var existingMaxX = existingMinX + existingBuildingInfo.Dimensions.X - 1;
							var existingMaxY = existingMinY + existingBuildingInfo.Dimensions.Y - 1;

							// Number of completely empty cells between the two footprint rectangles on
							// each axis. A touching edge therefore has clearance 0. For diagonal
							// separation, the larger axis determines how far an expanded candidate
							// rectangle can grow before it intersects the existing structure.
							var gapX = candidateMaxX < existingMinX
								? existingMinX - candidateMaxX - 1
								: existingMaxX < candidateMinX ? candidateMinX - existingMaxX - 1 : 0;
							var gapY = candidateMaxY < existingMinY
								? existingMinY - candidateMaxY - 1
								: existingMaxY < candidateMinY ? candidateMinY - existingMaxY - 1 : 0;
							var clearance = Math.Max(gapX, gapY);
							minimumClearance = Math.Min(minimumClearance, clearance);

							if (minimumClearance == 0)
								break;
						}

						// No existing building means there is nothing to space against.
						if (minimumClearance == int.MaxValue)
							minimumClearance = preferredGap;

						// Preserve the original center/target ordering when the ideal gap is actually
						// available. Otherwise keep scanning and remember the most open legal cell.
						if (minimumClearance >= preferredGap)
							return (cell, center, variant);

						if (minimumClearance > bestLegalClearance)
						{
							bestLegalClearance = minimumClearance;
							bestLegalSpacedLocation = cell;
							bestLegalSpacedVariant = variant;
						}
					}

					if (bestLegalSpacedLocation != null)
					{
						FransBotLog.BotDebug(world,
							"{0}: FransBaseBuilder spacing fallback for {1}: preferred {2} empty cells, best legal clearance {3}; using {4}.",
							player, actorType,
							baseBuilder.Info.MinimumStructureSpacingCells,
							bestLegalClearance, bestLegalSpacedLocation.Value);
						return (bestLegalSpacedLocation.Value, center, bestLegalSpacedVariant);
					}

					return (null, center, 0);
				}

				(CPos? Location, CPos? BaseCenter, int Variant) FindStockNativeMultiFactFallback()
				{
					// final placement authority for ordinary Building-queue structures.
					// Frans preferred placement still runs first (direction, spacing, RiskModel). If that
					// cannot find a cell, mirror stock BaseBuilder's native legality test around EVERY
					// live FACT instead of treating the oldest/main FACT as the whole buildable base.
					// Ground staging reservations remain protected because they are an explicit Frans
					// ownership constraint rather than a placement preference.
					foreach (var yard in baseBuilder.ConstructionYardBuildings.Actors
						.Where(a => a != null && a.IsInWorld && !a.IsDead && a.OccupiesSpace != null)
						.OrderBy(a => a.ActorID))
					{
						var cells = world.Map.FindTilesInAnnulus(yard.Location,
							baseBuilder.Info.MinBaseRadius, baseBuilder.Info.MaxBaseRadius)
							.OrderBy(c => (c - yard.Location).LengthSquared)
							.ThenBy(c => c.X).ThenBy(c => c.Y);

						foreach (var cell in cells)
						{
							if (baseBuilder.IntersectsGroundStagingReservation(cell, bi))
								continue;
							if (!world.CanPlaceBuilding(cell, actorInfo, bi, null))
								continue;
							if (distanceToBaseIsImportant && !bi.IsCloseEnoughToBase(world, player, actorInfo, null, cell))
								continue;

							FransBotLog.BotDebug(world,
								"{0}: FransBaseBuilder STOCK-NATIVE fallback places {1} at {2} using FACT {3}; preferred spacing/direction/risk search had no legal result.",
								player, actorType, cell, yard.Location);
							return (cell, yard.Location, 0);
						}
					}

					return (null, baseBuilder.GetBaseCenter(), 0);
				}

				if (localProductionFactCenter.HasValue && type == FransBuildingType.Building &&
					(baseBuilder.Info.BarracksTypes.Contains(actorType) || baseBuilder.Info.WarFactoryTypes.Contains(actorType)))
				{
					var localPlacement = FindPos(localProductionFactCenter.Value, localProductionFactCenter.Value,
						baseBuilder.Info.ExpansionProductionPlacementMinRadius, baseBuilder.Info.ExpansionProductionPlacementMaxRadius);
					if (localPlacement.Location.HasValue)
						FransBotLog.BotDebug(world,
							"{0}: LOCAL FACT production routes mandatory producer {1} to FACT area {2}; placement {3}.",
							player, actorType, localProductionFactCenter.Value, localPlacement.Location.Value);
					return localPlacement;
				}

				if (type == FransBuildingType.Building && baseBuilder.RequiresExpansionProductionPlacement(actorType))
				{
					if (!baseBuilder.TryGetExpansionProductionCenter(out var expansionCenter))
						return (null, null, 0);

					var expansionTarget = expansionCenter;
					var expansionWeight = baseBuilder.ProductionDirectionWeight(actorType);
					if (expansionWeight > 0 && baseBuilder.TryGetEnemyBaseDirectionTarget(out var knownEnemyBase, out _))
						expansionTarget = knownEnemyBase;
					var expansionPlacement = FindPos(expansionCenter, expansionTarget,
						baseBuilder.Info.ExpansionProductionPlacementMinRadius,
						baseBuilder.Info.ExpansionProductionPlacementMaxRadius, null, expansionWeight);
					if (expansionPlacement.Location.HasValue)
						FransBotLog.BotDebug(world,
							"{0}: main-base production cap routes {1} to expansion FACT area {2}; placement {3}.",
							player, actorType, expansionCenter, expansionPlacement.Location.Value);
					return expansionPlacement;
				}

				var baseCenter = baseBuilder.GetBaseCenter();
				switch (type)
				{

					case FransBuildingType.Refinery:
						var requestRef = baseBuilder.RequestedRefineries.Keys.OrderBy(a => a.ActorID).FirstOrDefault();
						var oreMineTarget = requestRef == null ? baseBuilder.oreMineRefineryTarget : null;

						// post-opening ore-node PROC placement is an exact one-to-one
						// economic-node operation. Search every live FACT, but accept only a legal
						// placement inside FransHarvester's control radius of the requested mine.
						// Never fall back to a distant generic refinery placement.
						if (oreMineTarget.HasValue && baseBuilder.oreEconomyService != null)
						{
							var controlRadius = baseBuilder.oreEconomyService.ResourceControlRadius;
							var controlRadiusSquared = controlRadius * controlRadius;
							Func<CPos, bool> mineControlFilter = c =>
								(c - oreMineTarget.Value).LengthSquared <= controlRadiusSquared;

							foreach (var yard in baseBuilder.ConstructionYardBuildings.Actors
								.Where(a => a != null && a.IsInWorld && !a.IsDead && a.OccupiesSpace != null)
								.OrderBy(a => (a.Location - oreMineTarget.Value).LengthSquared)
								.ThenBy(a => a.ActorID))
							{
								var found = FindPos(yard.Location, oreMineTarget.Value,
									baseBuilder.Info.MinBaseRadius, baseBuilder.Info.MaxBaseRadius,
									cellFilter: mineControlFilter);
								if (!found.Location.HasValue)
									continue;

								FransBotLog.BotDebug(world,
									"{0}: ore-node PROC placement {1} is physically within control radius {2} of requested mine {3}; holding the mine claim until FransHarvester verifies a physical pairing.",
									player, found.Location.Value, controlRadius, oreMineTarget.Value);
								return found;
							}

							// A dynamic blocker can invalidate the site between production selection and
							// placement. Keep this completed PROC pending until a valid in-radius cell
							// reopens; do not dump it elsewhere and request another PROC for the mine.
							return (null, baseCenter, 0);
						}

						// Explicit opening/MCV refinery requests retain their proven placement path.
						if (resourceLayer != null)
						{
							var resourceBaseCenter = failCount > 0 ? baseCenter : requestRef != null
								? baseBuilder.RequestedRefineries[requestRef].ConyardLoc
								: baseBuilder.ResourceConyardCenter ?? baseCenter;
							var nearby = world.Map.FindTilesInAnnulus(resourceBaseCenter, baseBuilder.Info.MinBaseRadius, baseBuilder.Info.MaxBaseRadius)
								.Where(c => baseBuilder.ResourceMapModule != null ? baseBuilder.ResourceMapModule.Info.ValuableResourceTypes.Contains(resourceLayer.GetResource(c).Type) : resourceLayer.GetResource(c).Type != null);
							var closestRef = failCount <= 0 ? baseBuilder.RefineryBuildings.Actors.Where(a => !a.IsDead).OrderBy(a => (a.Location - resourceBaseCenter).LengthSquared).ThenBy(a => a.ActorID).FirstOrDefault() : null;
							IEnumerable<CPos> resources;
							if (requestRef != null) resources = nearby.OrderBy(c => (c - baseBuilder.RequestedRefineries[requestRef].ResourceLoc).LengthSquared).ThenBy(c => c.X).ThenBy(c => c.Y).Take(baseBuilder.Info.MaxResourceCellsToCheck);
							else if (closestRef == null) resources = nearby.OrderBy(c => (c - resourceBaseCenter).LengthSquared).ThenBy(c => c.X).ThenBy(c => c.Y).Take(baseBuilder.Info.MaxResourceCellsToCheck);
							else resources = nearby.OrderByDescending(c => (c - closestRef.Location).LengthSquared).ThenBy(c => c.X).ThenBy(c => c.Y).Take(baseBuilder.Info.MaxResourceCellsToCheck);

							foreach (var r in resources)
							{
								var found = FindPos(resourceBaseCenter, r, baseBuilder.Info.MinBaseRadius, baseBuilder.Info.MaxBaseRadius);
								if (!found.Location.HasValue)
									continue;

								if (requestRef != null) baseBuilder.RequestedRefineries.Remove(requestRef);
								return found;
							}
						}

						if (requestRef != null)
							baseBuilder.RequestedRefineries.Remove(requestRef);
						return FindPos(baseCenter, baseCenter, baseBuilder.Info.MinBaseRadius, baseBuilder.Info.MaxBaseRadius);

					default:
					var productionDirectionWeight = baseBuilder.ProductionDirectionWeight(actorType);
					if (productionDirectionWeight > 0 && baseBuilder.TryGetEnemyBaseDirectionTarget(out var enemyBaseTarget, out var enemyBaseSource))
					{
						FransBotLog.BotDebug(world, "{0}: directional placement biases {1} toward {2} at {3} with weight {4}%.", player, actorType, enemyBaseSource, enemyBaseTarget, productionDirectionWeight);
						var preferred = FindPos(baseCenter, enemyBaseTarget, baseBuilder.Info.MinBaseRadius,
							distanceToBaseIsImportant ? baseBuilder.Info.MaxBaseRadius : world.Map.Grid.MaximumTileSearchRange,
							null, productionDirectionWeight);
						if (preferred.Location.HasValue)
							return preferred;
					}

					if (baseBuilder.strategicForwardTarget.HasValue && !baseBuilder.Info.NavalProductionTypes.Contains(actorType) && baseBuilder.UseDirectionalPlacement())
					{
						var target = baseBuilder.Info.ForwardStructureTypes.Contains(actorType)
							? baseBuilder.strategicForwardTarget.Value
							: baseBuilder.StrategicRearTarget(baseCenter);
						var preferred = FindPos(baseCenter, target, baseBuilder.Info.MinBaseRadius,
							distanceToBaseIsImportant ? baseBuilder.Info.MaxBaseRadius : world.Map.Grid.MaximumTileSearchRange);
						if (preferred.Location.HasValue)
							return preferred;
					}

					var localPreferred = FindPos(baseCenter, baseCenter, baseBuilder.Info.MinBaseRadius,
						distanceToBaseIsImportant ? baseBuilder.Info.MaxBaseRadius : world.Map.Grid.MaximumTileSearchRange);
					if (localPreferred.Location.HasValue)
						return localPreferred;

					return FindStockNativeMultiFactFallback();
				}
			}
		}
	}
}
