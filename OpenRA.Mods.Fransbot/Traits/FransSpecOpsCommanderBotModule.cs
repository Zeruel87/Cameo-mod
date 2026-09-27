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
using System.Linq;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Pathfinder;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	public enum FransSpecOpsMissionMode
	{
		Capture,
		Demolition,
		C4Demolition
	}

	public interface IFransCaptureSecurityService
	{
		bool IsCaptureMissionActor(Actor actor);
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Fransbot SpecOps Commander. Uses the same General -> CommandBid -> Commander mission architecture as Ground/Air/Sea, but bids only on configurable undefended RAID targets. Capture roles use native CaptureActor; Demo Truck uses native Attack; Tanya C4 uses native C4/Demolition. Production is demand-only.")]
	public class FransSpecOpsCommanderBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Independent CommandBid capacity key for this SpecOps role, analogous to an Air wing bidder key.")]
		public readonly string BidderKey = "specops";

		[Desc("Unique zero-based SpecOps capacity index across all e6/thf/dtrk capacities. uses 0..9 exactly once each.")]
		public readonly int CommanderIndex = 0;

		[Desc("Zero-based capacity index inside this specialist role. Only RoleIndex 0 performs demand-production, capture-retention and autonomous neutral objectives; every capacity may bid on General RAID missions.")]
		public readonly int RoleIndex = 0;

		[Desc("World ticks between SpecOps Commander mission-board/mission scans. Keep this at or below CommandBid's bid window so SpecOps competes in the same auction window as Ground/Air/Sea.")]
		public readonly int ScanInterval = 25;

		[Desc("How this SpecOps role resolves a RAID mission.")]
		public readonly FransSpecOpsMissionMode MissionMode = FransSpecOpsMissionMode.Capture;

		[ActorReference]
		[Desc("General RAID target actor types this SpecOps role may bid on. Empty disables mission-board RAID bidding for this role.")]
		public readonly FrozenSet<string> RaidTargetTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Neutral capture target types this role may still handle opportunistically outside the enemy RAID board. Intended for map objectives such as Oil Derricks. Empty disables autonomous neutral capture work.")]
		public readonly FrozenSet<string> AutonomousNeutralCaptureTargetTypes = FrozenSet<string>.Empty;

		[Desc("SpecOps definition of local RAID-defense radius. This is deliberately independent of General's broader negligible-defense screen.")]
		public readonly int RaidDefenseRadius = 10;

		[Desc("Maximum fresh visible/recent tactical defense actors allowed for a SpecOps RAID bid. Zero means literally undefended.")]
		public readonly int RaidMaximumDefenseUnits = 0;

		[Desc("Maximum summed fresh visible/recent defense value allowed for a SpecOps RAID bid. Zero means literally undefended.")]
		public readonly int RaidMaximumDefenseCombatValue = 0;

		[Desc("Reject a RAID target if any fresh visible/recent defensive building is inside RaidDefenseRadius, regardless of the mobile-defense allowance.")]
		public readonly bool RaidRejectAnyDefensiveBuilding = false;

		[Desc("C4-only exception: a nearby observed defensive building may be bypassed for bidding when reusable transport is available and at least one locally passable, preferred-risk Tanya approach cell exists around the demolition target. The static defense is not counted as a tolerated mobile guard; the final route/abort checks still apply.")]
		public readonly bool AllowTransportedC4DefensiveBuildingBypass = false;

		[Desc("Maximum observed defensive buildings inside RaidDefenseRadius that Tanya may bypass using the transported-C4 exception. Mobile guards are still evaluated by the insertion-cell RiskModel; additional static defense restores the hard rejection.")]
		public readonly int MaximumTransportedC4BypassedDefensiveBuildings = 1;

		[Desc("Planning ETA used for a Tanya C4 bid when reusable Jeep/TRAN insertion is available. This replaces the misleading on-foot ETA for broker eligibility; live transport/path/risk checks still govern execution.")]
		public readonly int TransportPlanningEtaTicks = 400;

		[Desc("Minimum ticks before repeating an unchanged demolition/C4 order. Tanya normally finishes before this expires; it is only a recovery guard if the native order was interrupted.")]
		public readonly int DemolitionAttackRefreshInterval = 125;

		[Desc("Actor types owned by this SpecOps role. Capture mode requires Captures; Demo Truck demolition requires Mobile/Attack; C4Demolition requires the native Demolition trait.")]
		public readonly FrozenSet<string> ManagedActorTypes = FrozenSet<string>.Empty;

		[Desc("Actor types that may be selected as capture targets. Leave empty to include every compatible target.")]
		public readonly FrozenSet<string> CapturableActorTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Capture targets that consume one Frans Construction Yard capacity slot. These are rejected while the shared MCV/FACT slot budget is full.")]
		public readonly FrozenSet<string> ConstructionYardCaptureTypes = FrozenSet<string>.Empty;

		[Desc("Cadence used by capture-retention/security bookkeeping. Mission-board bidding and active MISSION execution use ScanInterval like the other Commanders.")]
		public readonly int MinimumCaptureDelay = 20;

		[Desc("Maximum number of lightweight target candidates passed to expensive route and safety evaluation.")]
		public readonly int MaximumCaptureTargetOptions = 10;

		[Desc("Unified RiskModel tolerance for ordinary engineer/thief capture missions. Target cells and planned approach routes must remain preferred.")]
		public readonly FransRiskTolerance MissionRiskTolerance = FransRiskTolerance.Cautious;

		[Desc("Unified RiskModel tolerance for the first bold neutral-oil attempt. This is still fair-information only; it merely accepts slightly more uncertainty/risk.")]
		public readonly FransRiskTolerance BoldFirstCaptureRiskTolerance = FransRiskTolerance.Balanced;

		[Desc("Unified RiskModel tolerance for immediate abort/escape decisions.")]
		public readonly FransRiskTolerance AbortRiskTolerance = FransRiskTolerance.Cautious;

		[Desc("If true, enemy and ordinary capture targets must currently be visible. Neutral oil derricks remain valid once their map cell is explored.")]
		public readonly bool CheckCaptureTargetsForVisibility = true;

		[Desc("If true, neutral Oil Derricks present in the map at match start are legitimate static map knowledge when Explore Map is enabled. Their later hidden ownership is not queried; visible ownership still overrides the stale neutral assumption.")]
		public readonly bool UseExploredMapStaticObjectiveKnowledge = true;

		[ActorReference]
		[Desc("Actor types treated as Oil Derricks for explored-map static objective knowledge and first-capture/recapture classification. This is capture metadata only; the removed legacy local-guard system is not restored.")]
		public readonly FrozenSet<string> OilDerrickTypes = FrozenSet<string>.Empty;

		[Desc("Player relationships that capturers should attempt to target.")]
		public readonly PlayerRelationship CapturableRelationships = PlayerRelationship.Enemy | PlayerRelationship.Neutral;

		[Desc("Radius in cells searched for an emergency escape cell when enemies get too close.")]
		public readonly int EscapeSearchRadius = 10;

		[Desc("Prefer the nearest safe target instead of target sell value. Useful for thieves hunting harvesters.")]
		public readonly bool PreferNearestTarget = false;

		[Desc("Maximum radius around a capture target used to find a safe staging cell before the final capture order.")]
		public readonly int SafeApproachRadius = 4;

		[Desc("Minimum ticks between expensive full-path route rechecks while a threat-aware capturer is already moving.")]
		public readonly int RouteRecheckInterval = 125;

		[Desc("If true, this SpecOps role may request its managed specialist from UnitBuilder when a real configured RAID or autonomous-neutral opportunity exists.")]
		public readonly bool EnableDemandDrivenProduction = false;

		[ActorReference]
		[Desc("Actor type requested for demand-driven production. Intended to be one of ManagedActorTypes.")]
		public readonly string DemandProductionActorType = null;

		[ActorReference]
		[Desc("Target types that may increase demand for this specialist. Enemy demand comes only from live General RAID missions; configured autonomous-neutral capture targets may also count.")]
		public readonly FrozenSet<string> DemandProductionTargetTypes = FrozenSet<string>.Empty;

		[Desc("Maximum total number of owned, queued, transported, or requested specialists for this SpecOps role.")]
		public readonly int MaximumDemandCapturers = 1;

		[Desc("How many safe demand targets justify one specialist. For example 1 means two safe targets can justify two specialists, up to MaximumDemandCapturers.")]
		public readonly int DemandTargetsPerCapturer = 1;

		[Desc("Ticks between cheap scans for demand-production SpecOps opportunities.")]
		public readonly int DemandProductionScanInterval = 125;

		[Desc("Minimum ticks between issuing new demand-production requests.")]
		public readonly int DemandProductionCooldown = 125;

		[Desc("If true, demand production only counts opportunities inside the unified RiskModel's preferred risk band.")]
		public readonly bool DemandProductionRequiresSafeTarget = true;

		[Desc("World ticks a currently visible, safe General RAID opportunity may remain as production-only SpecOps demand memory after that short-lived RAID mission disappears. This memory may justify building/retaining ready specialist capacity, but it never authorizes a bid, target order or hidden-state query.")]
		public readonly int DemandOpportunityMemoryTicks = 1500;

		[Desc("If true, this primary SpecOps role may also request one support Mechanic when damaged Ground combat vehicles create a real repair-support need. The Mechanic remains support-only and is not added to RAID bidding.")]
		public readonly bool EnableSupportMechanicDemand = false;

		[ActorReference]
		[Desc("Mechanic/support actor type requested through the SpecOps production mailbox.")]
		public readonly string SupportMechanicActorType = null;

		[Desc("A Ground combat vehicle below this HP percentage counts as damaged enough to justify Mechanic demand.")]
		public readonly int SupportMechanicDamagedVehicleHealthPercent = 90;

		[Desc("Minimum number of damaged Ground combat vehicles required before support Mechanic demand is published.")]
		public readonly int SupportMechanicMinimumDamagedVehicles = 1;

		[Desc("Maximum owned, queued or mailbox-requested support Mechanics.")]
		public readonly int MaximumSupportMechanics = 1;

		[Desc("Minimum ticks between support Mechanic production requests.")]
		public readonly int SupportMechanicProductionCooldown = 250;

		[Desc("World ticks between aggregate SpecOps utilization diagnostics. Diagnostics are read-only and expose ready capacity plus why compatible RAID missions did not receive a bid.")]
		public readonly int UtilizationLogInterval = 750;

		[Desc("Allow this SpecOps capture role to hand selected specialists to FransTransportCommanderBotModule.")]
		public readonly bool EnableTransportSupport = false;

		[ActorReference]
		[Desc("Only these capture target types may trigger transport use. Empty means every configured capture target.")]
		public readonly FrozenSet<string> TransportTargetTypes = FrozenSet<string>.Empty;

		[Desc("Prefer a transport for otherwise-safe land missions at least this many cells away. Unreachable targets may force transport regardless of distance.")]
		public readonly int MinimumTransportDistance = 30;

		[Desc("Use the Ground Commander objective plus Strategic Map control/threat when deciding whether capture targets can realistically be held.")]
		public readonly bool EnableStrategicCaptureSecurity = false;

		[ActorReference]
		[Desc("Target types that normally require strategic support. A never-attempted neutral oil derrick may bypass this gate when BoldFirstNeutralOilCapture is enabled; recaptures remain strategic.")]
		public readonly FrozenSet<string> StrategicSecurityTargetTypes = FrozenSet<string>.Empty;

		[Desc("Let the first real AirAI attempt on a neutral oil derrick ignore hidden/full-map threat knowledge and strategic holdability. Visible enemy threats still block or abort that first mission. After the first mission starts, later attempts use normal capture security and threat-aware safety.")]
		public readonly bool BoldFirstNeutralOilCapture = true;

		[Desc("Own combat-unit radius that counts as immediate local military support for a capture target.")]
		public readonly int StrategicCaptureLocalSupportRadius = 10;

		[Desc("Maximum distance from the current Ground Commander objective that counts as Ground Commander support.")]
		public readonly int StrategicCaptureCommanderSupportRadius = 14;

		[Desc("Allow strategically supported targets this many cells beyond the current stable front before treating them as overextended.")]
		public readonly int StrategicCaptureFrontMarginCells = 6;

		[Desc("World ticks to ignore a structure after AirAI loses it for the first time.")]
		public readonly int FirstRecaptureCooldown = 3000;

		[Desc("World ticks to ignore a structure after repeated losses inside the escalation window.")]
		public readonly int RepeatedRecaptureCooldown = 6000;

		[Desc("Losses farther apart than this many world ticks start a new recapture-loss sequence.")]
		public readonly int RecaptureEscalationWindow = 10000;

		[Desc("After holding a previously contested structure this long, its repeated-loss history is cleared.")]
		public readonly int RecaptureHistoryResetAfterHeldTicks = 10000;

		[Desc("At this many repeated losses, recapture requires strong nearby or Ground Commander support.")]
		public readonly int StronglyContestedLossCount = 3;

		[Desc("Minimum local friendly ground-combat units that make an ordinary strategically gated capture supportable.")]
		public readonly int StrategicCaptureMinimumLocalSupport = 1;

		[Desc("Minimum local friendly ground-combat units that make a recapture supportable.")]
		public readonly int StrategicRecaptureMinimumLocalSupport = 1;

		[Desc("Minimum local friendly ground-combat units required for a strongly contested recapture.")]
		public readonly int StronglyContestedMinimumLocalSupport = 2;

		[Desc("Minimum planned units at nearby Ground Commander objective that support an ordinary new capture.")]
		public readonly int StrategicCaptureMinimumCommanderSupportUnits = 1;

		[Desc("Minimum planned units at nearby Ground Commander objective that support a recapture.")]
		public readonly int StrategicRecaptureMinimumCommanderSupportUnits = 2;

		[Desc("Minimum planned units at nearby Ground Commander objective required for a strongly contested recapture.")]
		public readonly int StronglyContestedMinimumCommanderSupportUnits = 4;

		[Desc("Maximum enemy-control score advantage tolerated for a new strategically gated capture when the target is otherwise behind the stable front.")]
		public readonly int StrategicCaptureEnemyControlMargin = 25;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);

			if (string.IsNullOrWhiteSpace(BidderKey))
				throw new YamlException($"{nameof(BidderKey)} must not be empty.");
			if (CommanderIndex < 0 || CommanderIndex > 9 || RoleIndex < 0 || RoleIndex > 9)
				throw new YamlException("SpecOps CommanderIndex/RoleIndex must be in the 0..9 range.");
			if (ScanInterval < 25)
				throw new YamlException($"{nameof(ScanInterval)} must be at least 25 world ticks.");
			if (RaidDefenseRadius <= 0 || RaidMaximumDefenseUnits < 0 || RaidMaximumDefenseCombatValue < 0 || DemolitionAttackRefreshInterval <= 0)
				throw new YamlException("SpecOps RAID defense/timing settings are invalid.");

			if (MinimumCaptureDelay <= 0)
				throw new YamlException($"{nameof(MinimumCaptureDelay)} must be greater than zero.");

			if (MaximumCaptureTargetOptions <= 0)
				throw new YamlException($"{nameof(MaximumCaptureTargetOptions)} must be greater than zero.");








			if (EscapeSearchRadius <= 0)
				throw new YamlException($"{nameof(EscapeSearchRadius)} must be greater than zero.");



			if (SafeApproachRadius <= 0 || MaximumTransportedC4BypassedDefensiveBuildings < 0 || TransportPlanningEtaTicks <= 0)
				throw new YamlException($"{nameof(SafeApproachRadius)} and {nameof(TransportPlanningEtaTicks)} must be greater than zero and {nameof(MaximumTransportedC4BypassedDefensiveBuildings)} must be non-negative.");

			if (RouteRecheckInterval <= 0)
				throw new YamlException($"{nameof(RouteRecheckInterval)} must be greater than zero.");

			if (EnableTransportSupport && MinimumTransportDistance < 0)
				throw new YamlException($"{nameof(MinimumTransportDistance)} cannot be negative.");

			if (EnableStrategicCaptureSecurity &&
				(StrategicCaptureLocalSupportRadius <= 0 ||
				 StrategicCaptureCommanderSupportRadius <= 0 ||
				 StrategicCaptureFrontMarginCells < 0 ||
				 FirstRecaptureCooldown < 0 ||
				 RepeatedRecaptureCooldown < 0 ||
				 RecaptureEscalationWindow <= 0 ||
				 RecaptureHistoryResetAfterHeldTicks <= 0 ||
				 StronglyContestedLossCount <= 0 || StrategicCaptureMinimumLocalSupport < 0 || StrategicRecaptureMinimumLocalSupport < 0 ||
				 StronglyContestedMinimumLocalSupport < 0 || StrategicCaptureMinimumCommanderSupportUnits < 0 || StrategicRecaptureMinimumCommanderSupportUnits < 0 ||
				 StronglyContestedMinimumCommanderSupportUnits < 0 || StrategicCaptureEnemyControlMargin < 0))
				throw new YamlException("Strategic capture security settings are invalid.");

			if (UtilizationLogInterval <= 0 || DemandOpportunityMemoryTicks < 0)
				throw new YamlException("SpecOps demand-memory/utilization settings are invalid.");

			if (EnableDemandDrivenProduction)
			{
				if (string.IsNullOrWhiteSpace(DemandProductionActorType))
					throw new YamlException($"{nameof(DemandProductionActorType)} must be set when demand-driven production is enabled.");

				if (!ManagedActorTypes.Contains(DemandProductionActorType.ToLowerInvariant()))
					throw new YamlException($"{nameof(DemandProductionActorType)} must also be present in {nameof(ManagedActorTypes)}.");

				if (DemandProductionTargetTypes.Count == 0)
					throw new YamlException($"{nameof(DemandProductionTargetTypes)} must contain at least one target type when demand-driven production is enabled.");

				if (MaximumDemandCapturers <= 0)
					throw new YamlException($"{nameof(MaximumDemandCapturers)} must be greater than zero.");

				if (DemandTargetsPerCapturer <= 0)
					throw new YamlException($"{nameof(DemandTargetsPerCapturer)} must be greater than zero.");

				if (DemandProductionScanInterval <= 0)
					throw new YamlException($"{nameof(DemandProductionScanInterval)} must be greater than zero.");

				if (DemandProductionCooldown < 0)
					throw new YamlException($"{nameof(DemandProductionCooldown)} cannot be negative.");

			}

			if (EnableSupportMechanicDemand && (string.IsNullOrWhiteSpace(SupportMechanicActorType) ||
				SupportMechanicDamagedVehicleHealthPercent <= 0 || SupportMechanicDamagedVehicleHealthPercent > 100 ||
				SupportMechanicMinimumDamagedVehicles <= 0 || MaximumSupportMechanics <= 0 || SupportMechanicProductionCooldown < 0))
				throw new YamlException("SpecOps support Mechanic demand settings are invalid.");
		}

		public override object Create(ActorInitializer init) { return new FransSpecOpsCommanderBotModule(init.Self, this); }
	}

	public class FransSpecOpsCommanderBotModule : ConditionalTrait<FransSpecOpsCommanderBotModuleInfo>,
		IBotTick, IBotRespondToAttack, INotifyActorDisposing, IFransCaptureSecurityService
	{
		readonly World world;
		readonly Player player;
		readonly ActorIndex.OwnerAndNames managedActors;
		readonly Dictionary<Actor, Actor> missions = [];
		readonly Dictionary<Actor, CPos> waypoints = [];
		readonly Dictionary<Actor, Actor> activeCaptureOrders = [];
		readonly Dictionary<Actor, int> nextRouteRecheckTick = [];
		readonly int maximumCaptureTargetOptions;

		IFransSpecOpsProductionMailbox specOpsProductionMailbox;
		IFransCaptureTransportService transportService;
		IFransCombatIntelService combatIntelService;
		IFransStrategicMapService strategicMapService;
		IFransBaseBuilderService baseBuilderService;
		IFransCommanderCoreService commanderCoreService;
		IFransExpansionStateService expansionStateService;
		IFransRiskModelService riskModelService;
		IFransCommandBidService commandBidService;
		IFransGeneralService generalService;

		readonly Dictionary<Actor, uint> demolitionTargets = [];
		readonly Dictionary<Actor, int> lastDemolitionOrderTick = [];
		// Once reusable insertion has physically handed Tanya back, the same reserved Jeep/TRAN
		// remains owned by Transport for extraction but must no longer block the C4 phase.
		readonly HashSet<uint> completedReusableInsertionActorIds = [];
		readonly Dictionary<uint, int> recoveryReservationsUntil = [];
		readonly FransSearchSpiral raidSearchSpiral = new();
		int raidSearchStartedWorldTick = -1;
		CPos raidSearchWaypoint;
		bool hasRaidSearchWaypoint;

		readonly record struct DemandOpportunityMemory(string TargetActorType, CPos LastVisibleCell, int LastSeenWorldTick);
		readonly Dictionary<uint, DemandOpportunityMemory> demandOpportunityMemory = [];
		readonly HashSet<uint> utilizationCompatibleRaidTargets = [];
		readonly HashSet<uint> utilizationDefendedTargets = [];
		readonly HashSet<uint> utilizationNoActorTargets = [];
		readonly HashSet<uint> utilizationCapabilityRejectedTargets = [];
		readonly HashSet<uint> utilizationRouteRejectedTargets = [];
		readonly HashSet<uint> utilizationBidTargets = [];
		int nextUtilizationLogTick;

		readonly Dictionary<Actor, Player> lastTrackedOwners = [];
		readonly Dictionary<Actor, CaptureRetentionState> captureRetention = [];
		readonly Dictionary<Actor, Actor> boldFirstCaptureMissions = [];
		readonly HashSet<uint> exploredMapInitialNeutralOilDerricks = [];
		bool exploredMapStaticKnowledgeSeeded;

		int scanTicks;
		int demandProductionScanTicks;
		int nextDemandProductionRequestTick;
		int nextSupportMechanicRequestTick;
		int captureSecurityScanTicks;

		sealed class CaptureRetentionState
		{
			public int LossCount;
			public int LastLossTick = int.MinValue;
			public int CooldownUntilTick;
			public int LastCapturedTick = int.MinValue;
			public bool FirstAttemptConsumed;
		}

		readonly record struct MissionChoice(Actor Target, CPos? Waypoint, bool UseTransport,
			bool LandPathAvailable, int TargetRiskScore, int RoutePeakRisk, int Value, long DistanceSquared);

		readonly record struct TargetCandidate(Actor Target, int Value, long DistanceSquared);
		readonly record struct RiskAwarePathMemoKey(int WorldTick, uint ActorId, CPos StartCell,
			uint TargetActorId, CPos TargetCell, FransRiskTolerance Tolerance, int SafeApproachRadius,
			int RiskRevision, int TerrainKnowledgeVersion);
		readonly record struct RiskAwarePathMemoResult(bool Available, CPos ApproachCell, CPos[] Path);
		readonly Dictionary<RiskAwarePathMemoKey, RiskAwarePathMemoResult> riskAwarePathMemo = [];


		public FransSpecOpsCommanderBotModule(Actor self, FransSpecOpsCommanderBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;

			if (world.Type == WorldType.Editor)
				return;

			maximumCaptureTargetOptions = Math.Max(1, Info.MaximumCaptureTargetOptions);
			managedActors = new ActorIndex.OwnerAndNames(world, Info.ManagedActorTypes, player);
		}

		protected override void Created(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;

			specOpsProductionMailbox = self.Owner.PlayerActor.TraitsImplementing<IFransSpecOpsProductionMailbox>().FirstOrDefault()
				?? throw new InvalidOperationException("FransSpecOpsCommanderBotModule requires FransUnitBuilderBotModule SpecOps production mailbox.");
			transportService = self.Owner.PlayerActor.TraitsImplementing<IFransCaptureTransportService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransSpecOpsCommanderBotModule requires FransTransportCommanderBotModule.");
			combatIntelService = self.Owner.PlayerActor.TraitsImplementing<IFransCombatIntelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransSpecOpsCommanderBotModule requires FransCombatIntelBotModule.");
			strategicMapService = self.Owner.PlayerActor.TraitsImplementing<IFransStrategicMapService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransSpecOpsCommanderBotModule requires FransStrategicMapBotModule.");
			baseBuilderService = self.Owner.PlayerActor.TraitsImplementing<IFransBaseBuilderService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransSpecOpsCommanderBotModule requires FransBaseBuilderBotModule.");
			commanderCoreService = self.Owner.PlayerActor.TraitsImplementing<IFransCommanderCoreService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransSpecOpsCommanderBotModule requires FransCommanderCoreBotModule.");
			expansionStateService = self.Owner.PlayerActor.TraitsImplementing<IFransExpansionStateService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransSpecOpsCommanderBotModule requires FransMcvExpansionManagerBotModule expansion-state service.");
			riskModelService = self.Owner.PlayerActor.TraitsImplementing<IFransRiskModelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransSpecOpsCommanderBotModule requires FransRiskModelBotModule.");
			commandBidService = self.Owner.PlayerActor.TraitsImplementing<IFransCommandBidService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransSpecOpsCommanderBotModule requires FransCommandBidBotModule.");
			generalService = self.Owner.PlayerActor.TraitsImplementing<IFransGeneralService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransSpecOpsCommanderBotModule requires FransGeneralBotModule.");
		}

		protected override void TraitEnabled(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;

			scanTicks = world.LocalRandom.Next(0, Info.ScanInterval);
			if (Info.EnableDemandDrivenProduction)
				demandProductionScanTicks = world.LocalRandom.Next(0, Info.DemandProductionScanInterval);
			if (Info.EnableStrategicCaptureSecurity)
				captureSecurityScanTicks = world.LocalRandom.Next(0, Math.Max(1, Info.MinimumCaptureDelay));

			recoveryReservationsUntil.Clear();
			ResetRaidLostTargetSearch(false);
			commandBidService?.UpdateTransientActorReservations(FransCommanderKind.SpecOps, Info.BidderKey, Array.Empty<uint>());

			exploredMapStaticKnowledgeSeeded = false;
			exploredMapInitialNeutralOilDerricks.Clear();
			demandOpportunityMemory.Clear();
			ClearUtilizationCounters();
			nextUtilizationLogTick = world.WorldTick + Math.Max(1, Info.UtilizationLogInterval);
			nextSupportMechanicRequestTick = world.WorldTick;

			FransBotLog.BotDebug(world,
				"{0}: SpecOps Commander TRANSPORT-AWARE {1} capacity {2}/9 role-index {3} active: mode {4}, actors {5}, RAID targets {6}. Demand production still uses UnitBuilder's explicit mailbox. Tanya C4 may now bid through a reusable Jeep/TRAN insertion when direct target defense or on-foot ETA would reject the mission, while local insertion risk and live abort checks remain mandatory.",
				player, Info.BidderKey, Info.CommanderIndex, Info.RoleIndex, Info.MissionMode,
				string.Join(",", Info.ManagedActorTypes.OrderBy(x => x)), string.Join(",", Info.RaidTargetTypes.OrderBy(x => x)));
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransSpecOpsCommander.BotTick");
			riskAwarePathMemo.Clear();
			if (player.WinState != WinState.Undefined)
				return;

			PublishRecoveryReservations();

			if (Info.RoleIndex == 0)
			{
				PruneDemandOpportunityMemory();
				MaybeLogUtilization(bot);
			}

			if (Info.RoleIndex == 0 && Info.MissionMode == FransSpecOpsMissionMode.Capture)
			{
				SeedExploredMapStaticCaptureKnowledge();
				if (Info.EnableStrategicCaptureSecurity && --captureSecurityScanTicks <= 0)
				{
					captureSecurityScanTicks = Math.Max(1, Info.MinimumCaptureDelay);
					UpdateCaptureRetentionState();
				}
			}

			if (Info.RoleIndex == 0 && Info.EnableDemandDrivenProduction && --demandProductionScanTicks <= 0)
			{
				demandProductionScanTicks = Info.DemandProductionScanInterval;
				ManageDemandDrivenProduction(bot);
				if (Info.EnableSupportMechanicDemand)
					ManageSupportMechanicDemand(bot);
			}

			if (--scanTicks > 0)
				return;
			scanTicks = Info.ScanInterval;
			if (Info.ManagedActorTypes.Count == 0)
				return;

			Actor[] actors;
			using (FransBotLog.Profile(world, player, "SpecOps.ScanPreparation"))
			{
				generalService.EnsureCurrentMissions();
				combatIntelService.EnsureCurrentSnapshot();
				actors = managedActors.Actors
					.Where(a => a != null && !a.IsDead)
					.OrderBy(a => a.ActorID)
					.ToArray();
				RemoveStaleState(actors.Where(a => a.IsInWorld));
				foreach (var stale in demolitionTargets.Keys.Where(a => a == null || a.IsDead || !actors.Contains(a)).ToArray())
				{
					demolitionTargets.Remove(stale);
					lastDemolitionOrderTick.Remove(stale);
				}
			}

			if (commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.SpecOps, Info.BidderKey,
				out var target, out var mission))
			{
				ExecuteRaidMission(bot, target, mission, actors);
				return;
			}

			SubmitBids(actors);
			if (commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.SpecOps, Info.BidderKey,
				out target, out mission))
			{
				ExecuteRaidMission(bot, target, mission, actors);
				return;
			}

			// Neutral map objectives are not enemy RAID missions. Preserve the proven E6 Oil Derrick behavior
			// as a local SpecOps capture task, but never let it consume an actor that is already bidding/mission-committed.
			if (Info.RoleIndex == 0 && Info.MissionMode == FransSpecOpsMissionMode.Capture && Info.AutonomousNeutralCaptureTargetTypes.Count > 0)
				using (FransBotLog.Profile(world, player, "SpecOps.AutonomousCapture"))
				{
					foreach (var actor in actors.Where(a => a.IsInWorld && !a.IsDead))
					{
						if (missions.TryGetValue(actor, out var existing) && existing != null &&
							player.RelationshipWith(existing.Owner) != PlayerRelationship.Neutral)
							ClearMission(actor);
						ManageCapturer(bot, actor, allowAutonomousNeutral: true);
					}
				}
		}

		void PublishRecoveryReservations()
		{
			foreach (var pair in recoveryReservationsUntil.ToArray())
			{
				var actor = world.GetActorById(pair.Key);
				if (pair.Value <= world.WorldTick || actor == null || !actor.IsInWorld || actor.IsDead || actor.Owner != player)
					recoveryReservationsUntil.Remove(pair.Key);
			}

			commandBidService.UpdateTransientActorReservations(FransCommanderKind.SpecOps, Info.BidderKey,
				recoveryReservationsUntil.Keys.OrderBy(id => id).ToArray());
		}

		void SubmitBids(IReadOnlyCollection<Actor> actors)
		{
			using var perf = FransBotLog.Profile(world, player, "SpecOps.SubmitBids");
			if (Info.RaidTargetTypes.Count == 0 || actors == null)
				return;

			var raidMissions = generalService.CurrentMissions
				.Where(j => j.Type == FransMissionType.Raid && !j.IsRememberedIntel && j.Target != null)
				.Where(j => Info.RaidTargetTypes.Contains(j.TargetActorType.ToLowerInvariant()));
			if (Info.MissionMode == FransSpecOpsMissionMode.C4Demolition)
				raidMissions = raidMissions
					.OrderByDescending(j => GetC4TargetPriority(j.TargetActorType))
					.ThenByDescending(j => j.StrategicPriority)
					.ThenBy(j => j.TargetActorId)
					.Take(maximumCaptureTargetOptions);
			else
				raidMissions = raidMissions.OrderByDescending(j => j.StrategicPriority).ThenBy(j => j.TargetActorId);

			foreach (var mission in raidMissions)
			{
				utilizationCompatibleRaidTargets.Add(mission.TargetActorId);
				var target = mission.Target;
				if (!IsVisibleEnemyRaidTarget(target))
					continue;

				var defenseEligible = TryEvaluateRaidDefenseEligibility(
					mission.SiteIntel, mission.TargetActorId, target.Location,
					out var requiresReusableTransport, out _, out _);
				var ordinarilyUndefended = defenseEligible && !requiresReusableTransport;

				var operationalActors = actors
					.Where(IsManagedSpecOpsActorOperational)
					.Where(a => commanderCoreService.IsActorAvailableForMissionBid(FransCommanderKind.SpecOps, Info.BidderKey, a))
					.OrderBy(a => a.ActorID)
					.ToArray();
				if (operationalActors.Length == 0)
				{
					utilizationNoActorTargets.Add(mission.TargetActorId);
					continue;
				}

				(Actor Actor, int Price, int RouteRisk, int Eta, int Travel, int Force)? best = null;
				var hadTargetCapability = false;
				var hadDefenseEligibleActor = ordinarilyUndefended;
				foreach (var actor in operationalActors)
				{
					if (Info.MissionMode == FransSpecOpsMissionMode.Capture)
					{
						var captureManager = actor.TraitOrDefault<CaptureManager>();
						if (captureManager == null || !IsEligibleTarget(actor, captureManager, target) || IsTargetReservedByOther(actor, target))
							continue;
					}
					else if (Info.MissionMode == FransSpecOpsMissionMode.Demolition)
					{
						if (!CanDemolitionAttackTarget(actor, target))
							continue;
					}
					else if (!CanC4Target(actor, target))
						continue;

					hadTargetCapability = true;
					if (!defenseEligible)
						continue;

					if (!TryEvaluateRaidApproach(actor, target, out var routeRisk, out var eta, out var travel,
						forceReusableTransport: requiresReusableTransport))
						continue;
					hadDefenseEligibleActor = true;

					var actorValue = commanderCoreService.GetActorValue(actor);
					var price = commanderCoreService.PriceBid(FransCommanderKind.SpecOps, routeRisk, eta, actorValue);
					if (Info.MissionMode == FransSpecOpsMissionMode.C4Demolition)
						price = Math.Max(0, price - GetC4TargetPriority(target.Info.Name));
					var candidate = (actor, price, routeRisk, eta, travel, actorValue);
					if (!best.HasValue || candidate.price < best.Value.Price ||
						(candidate.price == best.Value.Price && actor.ActorID < best.Value.Actor.ActorID))
						best = (actor, price, routeRisk, eta, travel, actorValue);
				}

				if (!best.HasValue)
				{
					if (!ordinarilyUndefended && hadTargetCapability && !hadDefenseEligibleActor)
						utilizationDefendedTargets.Add(mission.TargetActorId);
					else if (hadTargetCapability)
						utilizationRouteRejectedTargets.Add(mission.TargetActorId);
					else
						utilizationCapabilityRejectedTargets.Add(mission.TargetActorId);
					continue;
				}

				var chosen = best.Value;
				commandBidService.SubmitMissionBid(mission, new FransCommanderBidReport(
					FransCommanderKind.SpecOps, Info.BidderKey, chosen.Actor.ActorID, new[] { chosen.Actor.ActorID },
					chosen.Price, chosen.RouteRisk, chosen.Travel, chosen.Force, chosen.Eta, 1, 1, true));
				utilizationBidTargets.Add(mission.TargetActorId);
			}
		}

		bool IsManagedSpecOpsActorOperational(Actor actor)
		{
			if (actor == null || !actor.IsInWorld || actor.IsDead || actor.Owner != player ||
				!Info.ManagedActorTypes.Contains(actor.Info.Name.ToLowerInvariant()))
				return false;
			var mobile = actor.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused)
				return false;
			if (missions.ContainsKey(actor) || waypoints.ContainsKey(actor) || activeCaptureOrders.ContainsKey(actor) ||
				demolitionTargets.ContainsKey(actor) || transportService?.IsHandlingPassenger(actor) == true)
				return false;
			if (Info.MissionMode == FransSpecOpsMissionMode.Capture)
				return actor.TraitOrDefault<CaptureManager>() != null;
			if (Info.MissionMode == FransSpecOpsMissionMode.C4Demolition)
				return HasC4OrderCapability(actor);
			return actor.TraitsImplementing<AttackBase>()
				.Any(attack => !attack.IsTraitDisabled && !attack.IsTraitPaused);
		}

		static bool HasC4OrderCapability(Actor actor)
		{
			return actor != null && actor.TraitsImplementing<IIssueOrder>()
				.SelectMany(issueOrder => issueOrder.Orders)
				.Any(orderTargeter => orderTargeter.OrderID == "C4");
		}

		bool CanDemolitionAttackTarget(Actor actor, Actor target)
		{
			if (actor == null || target == null)
				return false;
			var attackTarget = Target.FromActor(target);
			return actor.TraitsImplementing<AttackBase>()
				.Any(attack => !attack.IsTraitDisabled && !attack.IsTraitPaused && attack.HasAnyValidWeapons(attackTarget));
		}

		bool CanC4Target(Actor actor, Actor target)
		{
			if (actor == null || target == null || actor.Disposed || target.Disposed || !actor.IsInWorld || actor.IsDead ||
				!target.IsInWorld || target.IsDead || actor.Owner != player || target.Owner == null ||
				player.RelationshipWith(target.Owner) != PlayerRelationship.Enemy)
				return false;

			var orderTarget = Target.FromActor(target);
			foreach (var issueOrder in actor.TraitsImplementing<IIssueOrder>())
			{
				foreach (var orderTargeter in issueOrder.Orders)
				{
					if (orderTargeter.OrderID != "C4")
						continue;

					var modifiers = TargetModifiers.None;
					string cursor = null;
					if (orderTargeter.CanTarget(actor, orderTarget, ref modifiers, ref cursor))
						return true;
				}
			}

			return false;
		}

		static int GetC4TargetPriority(string actorType)
		{
			return actorType?.ToLowerInvariant() switch
			{
				"mslo" or "iron" or "pdox" => 1000,
				"atek" or "stek" or "fact" => 800,
				"weap" or "afld" or "hpad" or "spen" or "syrd" => 600,
				"dome" or "fix" => 400,
				"proc" => 250,
				_ => 0
			};
		}

		bool IsVisibleEnemyRaidTarget(Actor target)
		{
			return target != null && target.IsInWorld && !target.IsDead && target.Owner != player &&
				player.RelationshipWith(target.Owner) == PlayerRelationship.Enemy && target.CanBeViewedByPlayer(player);
		}

		bool IsEngineerCaptureRole => Info.MissionMode == FransSpecOpsMissionMode.Capture &&
			Info.ManagedActorTypes.Contains("e6");

		bool IsEngineerCaptureTargetLocallyClear(Actor target)
		{
			if (!IsEngineerCaptureRole || target == null)
				return true;
			var radiusSq = Info.RaidDefenseRadius * Info.RaidDefenseRadius;
			if (combatIntelService.VisibleEnemies.Any(e =>
				e != null && e.IsInWorld && !e.IsDead && e.ActorID != target.ActorID &&
				combatIntelService.IsTacticalCombatThreat(e) &&
				(e.Location - target.Location).LengthSquared <= radiusSq))
				return false;
			return !combatIntelService.EnemyCombatContacts.Any(c =>
				c.ActorId != target.ActorID && c.IsBuilding && c.IsDefensiveBuilding &&
				c.Owner != null && PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(c.Owner)) &&
				(c.LastSeenCell - target.Location).LengthSquared <= radiusSq);
		}

		bool IsSpecOpsRaidTargetUndefended(FransSiteIntel siteIntel, uint targetActorId, CPos targetCell,
			out int defenseUnits, out int defenseValue)
		{
			defenseUnits = 0;
			defenseValue = 0;
			var radiusSq = Info.RaidDefenseRadius * Info.RaidDefenseRadius;
			foreach (var observed in siteIntel.Actors ?? Array.Empty<FransSiteIntelActor>())
			{
				if (observed.ActorId == targetActorId || observed.Owner == null ||
					!PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(observed.Owner)) ||
					(!observed.IsCombatActor && !observed.IsDefensiveBuilding) ||
					(observed.Cell - targetCell).LengthSquared > radiusSq)
					continue;

				defenseUnits++;
				defenseValue = (int)Math.Min(int.MaxValue, (long)defenseValue + Math.Max(1, observed.ObservedValue));
				if (Info.RaidRejectAnyDefensiveBuilding && observed.IsDefensiveBuilding)
					return false;
			}
			return defenseUnits <= Info.RaidMaximumDefenseUnits && defenseValue <= Info.RaidMaximumDefenseCombatValue;
		}

		bool TryEvaluateRaidDefenseEligibility(FransSiteIntel siteIntel, uint targetActorId, CPos targetCell,
			out bool requiresReusableTransport, out int defenseUnits, out int defenseValue)
		{
			requiresReusableTransport = false;
			if (IsSpecOpsRaidTargetUndefended(siteIntel, targetActorId, targetCell, out defenseUnits, out defenseValue))
				return true;

			if (!CanAttemptTransportedC4Bypass(siteIntel, targetActorId, targetCell))
				return false;

			requiresReusableTransport = true;
			return true;
		}

		bool CanAttemptTransportedC4Bypass(FransSiteIntel siteIntel, uint targetActorId, CPos targetCell)
		{
			if (Info.MissionMode != FransSpecOpsMissionMode.C4Demolition || !Info.AllowTransportedC4DefensiveBuildingBypass)
				return false;

			var radiusSq = Info.RaidDefenseRadius * Info.RaidDefenseRadius;
			var staticDefenses = (siteIntel.Actors ?? Array.Empty<FransSiteIntelActor>()).Count(observed =>
				observed.ActorId != targetActorId && observed.Owner != null &&
				PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(observed.Owner)) &&
				observed.IsDefensiveBuilding && (observed.Cell - targetCell).LengthSquared <= radiusSq);

			return staticDefenses <= Info.MaximumTransportedC4BypassedDefensiveBuildings;
		}

		bool TryEvaluateRaidApproach(Actor actor, Actor target, out int routeRisk, out int eta, out int travel, bool forceReusableTransport = false)
		{
			using var perf = FransBotLog.Profile(world, player, "SpecOps.RaidApproachEvaluation");
			routeRisk = int.MaxValue;
			eta = int.MaxValue;
			travel = int.MaxValue;
			if (actor == null || target == null)
				return false;
			var mobile = actor.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused)
				return false;

			var targetRisk = riskModelService.EvaluateCell(actor, target.Location, FransRiskRole.Capturer, Info.MissionRiskTolerance);
			var landPathAvailable = TryFindRiskAwareApproachPath(actor, mobile, target, Info.MissionRiskTolerance,
				out _, out var path);
			var canTransport = false;
			var wantsTransport = forceReusableTransport || ShouldUseTransport(actor, target, landPathAvailable);
			if (wantsTransport)
			{
				using (FransBotLog.Profile(world, player, "SpecOps.TransportFeasibility"))
				{
					if (Info.MissionMode == FransSpecOpsMissionMode.Capture)
						canTransport = transportService.CanPotentiallyTransport(actor, target, landPathAvailable);
					else if (Info.MissionMode == FransSpecOpsMissionMode.C4Demolition)
						canTransport = transportService.CanPotentiallyTransportReusable(actor, target, landPathAvailable);
				}
			}

			if (forceReusableTransport)
			{
				if (!canTransport || !TryFindPreferredLocalC4ApproachCell(actor, mobile, target, out var forcedInsertionCell))
					return false;
				routeRisk = riskModelService.EvaluateCell(actor, forcedInsertionCell, FransRiskRole.Capturer, Info.MissionRiskTolerance).Score;
			}
			else
			{
				if (!landPathAvailable && !canTransport)
					return false;

				if (!targetRisk.IsPreferred)
				{
					if (!(Info.MissionMode == FransSpecOpsMissionMode.C4Demolition &&
						Info.AllowTransportedC4DefensiveBuildingBypass && canTransport &&
						TryFindPreferredLocalC4ApproachCell(actor, mobile, target, out var safeInsertionCell)))
						return false;
					routeRisk = riskModelService.EvaluateCell(actor, safeInsertionCell, FransRiskRole.Capturer, Info.MissionRiskTolerance).Score;
				}
				else
					routeRisk = landPathAvailable && path != null && path.Count > 0
						? riskModelService.EvaluateRoute(actor, path, FransRiskRole.Capturer, Info.MissionRiskTolerance).PeakScore
						: targetRisk.Score;
			}
			travel = Math.Abs(target.Location.X - actor.Location.X) + Math.Abs(target.Location.Y - actor.Location.Y);
			var directEta = commanderCoreService.EstimateMoveEtaTicks(actor, target.Location);
			eta = canTransport && wantsTransport
				? Math.Min(directEta, Info.TransportPlanningEtaTicks)
				: directEta;
			return commanderCoreService.IsRaidEtaEligible(eta);
		}



		bool TryFindPreferredLocalC4ApproachCell(Actor actor, Mobile mobile, Actor target, out CPos cell)
		{
			cell = default;
			if (actor == null || mobile == null || target == null)
				return false;

			var found = world.Map.FindTilesInAnnulus(target.Location, 1, Info.SafeApproachRadius)
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.Select(c => (Cell: c, Risk: riskModelService.EvaluateCell(actor, c, FransRiskRole.Capturer, Info.MissionRiskTolerance)))
				.Where(x => x.Risk.IsPreferred)
				.OrderBy(x => x.Risk.Score)
				.ThenBy(x => (x.Cell - target.Location).LengthSquared)
				.ThenBy(x => x.Cell.X).ThenBy(x => x.Cell.Y)
				.FirstOrDefault();
			if (!found.Risk.IsPreferred)
				return false;
			cell = found.Cell;
			return true;
		}

		void ExecuteRaidMission(IBot bot, Actor visibleTarget, FransActiveMission mission, IReadOnlyCollection<Actor> actors)
		{
			using var perf = FransBotLog.Profile(world, player, "SpecOps.ExecuteRaidMission");
			if (mission.MissionType != FransMissionType.Raid || !mission.IsSpecialistCapability)
			{
				commandBidService.ReleaseMission(FransCommanderKind.SpecOps, Info.BidderKey, "SpecOps accepts RAID capability missions only");
				ResetRaidLostTargetSearch(false);
				return;
			}

			if (mission.CommittedActorIds == null || mission.CommittedActorIds.Length != 1 ||
				mission.CommittedActorIds[0] != mission.SubjectActorId)
			{
				commandBidService.ReleaseMission(FransCommanderKind.SpecOps, Info.BidderKey, "SpecOps winning bid must contain exactly its committed specialist actor");
				generalService.ReportRaidRetreat(mission.TargetActorId, "SpecOps winning bid snapshot became invalid");
				ResetRaidLostTargetSearch(false);
				return;
			}

			var rawTarget = world.GetActorById(mission.TargetActorId);
			var targetGone = rawTarget == null || !rawTarget.IsInWorld || rawTarget.IsDead;
			var captureSucceeded = Info.MissionMode == FransSpecOpsMissionMode.Capture &&
				rawTarget != null && rawTarget.IsInWorld && !rawTarget.IsDead && rawTarget.Owner == player;

			var actor = world.GetActorById(mission.CommittedActorIds[0]);
			if (captureSucceeded)
			{
				FinishRaidMission(bot, actor, mission,
					$"SpecOps capture changed ownership of {rawTarget.Info.Name} {rawTarget.ActorID}");
				return;
			}
			if (Info.MissionMode == FransSpecOpsMissionMode.C4Demolition && targetGone)
			{
				FinishRaidMission(bot, actor, mission, $"C4 target {mission.TargetActorId} is physically destroyed");
				return;
			}

			// A native Cargo passenger is temporarily absent from World.GetActorById(). Preserve the
			// immutable SpecOps assignment while FransTransport still owns that exact passenger ID.
			// After unload the same ActorID resolves again and normal capture/C4 execution resumes.
			if ((actor == null || !actor.IsInWorld) &&
				(Info.MissionMode == FransSpecOpsMissionMode.Capture || Info.MissionMode == FransSpecOpsMissionMode.C4Demolition) &&
				transportService.IsHandlingPassenger(mission.CommittedActorIds[0]))
				return;

			if (actor == null || !actor.IsInWorld || actor.IsDead || actor.Owner != player ||
				!Info.ManagedActorTypes.Contains(actor.Info.Name.ToLowerInvariant()))
			{
				commandBidService.ReleaseMission(FransCommanderKind.SpecOps, Info.BidderKey, "committed SpecOps actor is unavailable");
				// Demo Truck RAID is sacrificial by design. If both exact target and committed truck are
				// physically gone, treat that as normal mission end rather than a RETREAT cooldown.
				if (!(Info.MissionMode == FransSpecOpsMissionMode.Demolition && targetGone))
					generalService.ReportRaidRetreat(mission.TargetActorId, "committed SpecOps actor became unavailable");
				ResetRaidLostTargetSearch(false);
				return;
			}

			if (visibleTarget == null || !IsVisibleEnemyRaidTarget(visibleTarget))
			{
				ExecuteLostRaidTargetRecon(bot, actor, mission);
				return;
			}

			if (raidSearchStartedWorldTick >= 0)
			{
				actor.CancelActivity();
				ResetRaidLostTargetSearch(false);
				FransBotLog.BotDebug(world,
					"{0}: SpecOps {1} RAID reacquires exact target {2}; bounded local RECON ends and the same RAID resumes.",
					player, Info.BidderKey, mission.TargetActorId);
			}

			if (!Info.RaidTargetTypes.Contains(visibleTarget.Info.Name.ToLowerInvariant()))
			{
				AbortRaidMission(bot, actor, mission, "target type is no longer valid for this SpecOps RAID profile");
				return;
			}

			// The committed actor list/force snapshot is immutable, but capability may fall when new raw INTEL arrives.
			// General does not interpret that INTEL: SpecOps reapplies the same ordinary/bypass eligibility gate used for bidding.
			var capabilityIntel = mission.SiteIntel;
			if (generalService.TryGetMission(mission.TargetActorId, out var refreshedMission) && refreshedMission.Type == FransMissionType.Raid)
				capabilityIntel = refreshedMission.SiteIntel;
			if (!TryEvaluateRaidDefenseEligibility(capabilityIntel, mission.TargetActorId, visibleTarget.Location,
				out var requiresReusableTransport, out var defenseUnits, out var defenseValue))
			{
				AbortRaidMission(bot, actor, mission,
					$"current raw SiteIntel is outside SpecOps RAID defense eligibility ({defenseUnits} defense actor(s)/value {defenseValue})");
				return;
			}

			if (Info.MissionMode == FransSpecOpsMissionMode.Capture)
				ExecuteCaptureRaidMission(bot, actor, visibleTarget, mission);
			else if (Info.MissionMode == FransSpecOpsMissionMode.C4Demolition)
				ExecuteC4RaidMission(bot, actor, visibleTarget, mission, requiresReusableTransport);
			else
				ExecuteDemolitionRaidMission(bot, actor, visibleTarget, mission);
		}

		void ExecuteLostRaidTargetRecon(IBot bot, Actor actor, FransActiveMission mission)
		{
			if (actor == null || !actor.IsInWorld || actor.IsDead)
				return;

			if (transportService?.IsHandlingPassenger(actor) == true)
				return;

			// Once local RECON has started, the deadline is absolute even if a queued waypoint
			// carries the specialist outside the initial 4-cell target-area radius.
			if (raidSearchStartedWorldTick >= 0 &&
				world.WorldTick - raidSearchStartedWorldTick >= commanderCoreService.RaidLostTargetReconTicks)
			{
				FinishRaidMission(bot, actor, mission, "exact target not reacquired during bounded local RECON");
				return;
			}

			ClearMission(actor);
			demolitionTargets.Remove(actor);
			lastDemolitionOrderTick.Remove(actor);
			var mobile = actor.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused)
			{
				AbortRaidMission(bot, actor, mission, "lost-target local RECON has no operational Mobile");
				return;
			}

			var center = mission.LastVisibleTargetCell;
			if ((actor.Location - center).LengthSquared > 16)
			{
				var approach = ResolveRaidReconWaypoint(actor, center);
				if (!approach.HasValue)
				{
					AbortRaidMission(bot, actor, mission, "last-visible RAID target area has no safe reachable local-RECON cell");
					return;
				}
				if (actor.IsIdle || !hasRaidSearchWaypoint || raidSearchWaypoint != approach.Value)
				{
					actor.CancelActivity();
					bot.QueueOrder(new Order("Move", actor, Target.FromCell(world, approach.Value), false));
					raidSearchWaypoint = approach.Value;
					hasRaidSearchWaypoint = true;
				}
				return;
			}

			if (raidSearchStartedWorldTick < 0)
			{
				raidSearchStartedWorldTick = world.WorldTick;
				raidSearchSpiral.Reset(center, commanderCoreService.GetReconVisionCells(actor));
				hasRaidSearchWaypoint = false;
				actor.CancelActivity();
				FransBotLog.BotDebug(world,
					"{0}: SpecOps {1} RAID target {2} is gone/unseen at LastVisibleTargetCell {3}; begins {4}-WT local plain-Move RECON before ANCHOR return.",
					player, Info.BidderKey, mission.TargetActorId, center, commanderCoreService.RaidLostTargetReconTicks);
			}

			if (hasRaidSearchWaypoint && !actor.IsIdle && (actor.Location - raidSearchWaypoint).LengthSquared > 4)
				return;

			var waypoints = new List<CPos>(Math.Min(4, commanderCoreService.ReconWaypointBatchSize));
			var cursor = actor.Location;
			for (var i = 0; i < Math.Min(4, commanderCoreService.ReconWaypointBatchSize); i++)
			{
				if (!raidSearchSpiral.TryGetNextWaypoint(world, c => ResolveRaidReconWaypoint(actor, c), cursor, out var waypoint))
					break;
				waypoints.Add(waypoint);
				cursor = waypoint;
			}
			if (waypoints.Count == 0)
				return;

			for (var i = 0; i < waypoints.Count; i++)
				bot.QueueOrder(new Order("Move", actor, Target.FromCell(world, waypoints[i]), i > 0));
			raidSearchWaypoint = waypoints[^1];
			hasRaidSearchWaypoint = true;
		}

		CPos? ResolveRaidReconWaypoint(Actor actor, CPos requested)
		{
			var mobile = actor?.TraitOrDefault<Mobile>();
			if (mobile == null)
				return null;
			return world.Map.FindTilesInCircle(requested, 3)
				.Where(world.Map.Contains)
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.Where(c => riskModelService.EvaluateCell(actor, c, FransRiskRole.Capturer, Info.MissionRiskTolerance).IsPreferred)
				.OrderBy(c => (c - requested).LengthSquared)
				.ThenBy(c => (c - actor.Location).LengthSquared)
				.ThenBy(c => c.X).ThenBy(c => c.Y)
				.Select(c => (CPos?)c).FirstOrDefault();
		}

		void ResetRaidLostTargetSearch(bool cancelActivity, Actor actor = null)
		{
			if (cancelActivity && actor != null && actor.IsInWorld && !actor.IsDead)
				actor.CancelActivity();
			raidSearchStartedWorldTick = -1;
			raidSearchWaypoint = default;
			hasRaidSearchWaypoint = false;
		}

		void ExecuteCaptureRaidMission(IBot bot, Actor actor, Actor target, FransActiveMission mission)
		{
			if (target.Owner == player)
			{
				FinishRaidMission(bot, actor, mission, $"{actor.Info.Name} {actor.ActorID} captured {target.Info.Name} {target.ActorID}");
				return;
			}
			var captureManager = actor.TraitOrDefault<CaptureManager>();
			if (captureManager == null || !IsEligibleTarget(actor, captureManager, target))
			{
				AbortRaidMission(bot, actor, mission, "capture target/actor is no longer eligible");
				return;
			}
			if (!missions.TryGetValue(actor, out var missionTarget) || missionTarget != target)
			{
				ClearMission(actor);
				missions[actor] = target;
				FransBotLog.BotDebug(world,
					"{0}: SpecOps {1} accepts RAID {2} {3} with {4} {5}; action is CaptureActor, not combat.",
					player, Info.BidderKey, target.Info.Name, target.ActorID, actor.Info.Name, actor.ActorID);
			}
			ManageCapturer(bot, actor, allowAutonomousNeutral: false);
			if (target.IsInWorld && !target.IsDead && target.Owner == player)
			{
				ClearMission(actor);
				FinishRaidMission(bot, actor, mission, $"{actor.Info.Name} {actor.ActorID} captured {target.Info.Name} {target.ActorID}");
				return;
			}
			if (!missions.ContainsKey(actor) && !HasQueuedOrActiveCapture(actor) && !transportService.IsHandlingPassenger(actor))
				AbortRaidMission(bot, actor, mission, "SpecOps capture mission could not maintain a safe eligible route");
		}

		void ExecuteC4RaidMission(IBot bot, Actor actor, Actor target, FransActiveMission mission, bool requiresReusableTransport)
		{
			if (!CanC4Target(actor, target))
			{
				AbortRaidMission(bot, actor, mission, "Tanya C4 target no longer supports native demolition");
				return;
			}

			if (transportService.TryConsumeCompletedReusableInsertion(actor, out var transportedTarget))
			{
				if (transportedTarget != target)
				{
					AbortRaidMission(bot, actor, mission, "Tanya reusable transport handed back a different target");
					return;
				}
				completedReusableInsertionActorIds.Add(actor.ActorID);
				FransBotLog.BotDebug(world, "{0}: Tanya {1} completed reusable insertion for C4 RAID {2} {3}; native C4 phase begins while the exact transport remains reserved for extraction.",
					player, actor.ActorID, target.Info.Name, target.ActorID);
			}

			var reusableInsertionCompleted = completedReusableInsertionActorIds.Contains(actor.ActorID);
			// Transport ownership is a hard commitment from acceptance through Waiting/Pickup/Move/Drop.
			// Do not re-evaluate ShouldUseTransport() and fall through to foot-C4 while Tanya is still
			// physically in-world and boarding. After the explicit Handoff above, Standby is allowed
			// to coexist with native C4 because the vehicle is now reserved only for extraction.
			if (transportService.IsHandlingPassenger(actor) && !reusableInsertionCompleted)
				return;

			var mobile = actor.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused)
			{
				AbortRaidMission(bot, actor, mission, "Tanya mobility is unavailable");
				return;
			}

			var immediate = riskModelService.EvaluateImmediateRisk(actor, actor.Location, FransRiskRole.Capturer, Info.AbortRiskTolerance);
			if (immediate.IsCritical)
			{
				AbortRaidMission(bot, actor, mission, $"Tanya C4 route became critical risk {immediate.Score}");
				return;
			}

			var landPathAvailable = TryFindRiskAwareApproachPath(actor, mobile, target, Info.MissionRiskTolerance, out _, out _);
			if (reusableInsertionCompleted && !landPathAvailable && Info.AllowTransportedC4DefensiveBuildingBypass &&
				TryFindPreferredLocalC4ApproachCell(actor, mobile, target, out var localC4Approach))
			{
				if ((actor.Location - localC4Approach).LengthSquared > 1)
				{
					if (actor.IsIdle)
						bot.QueueOrder(new Order("Move", actor, Target.FromCell(world, localC4Approach), false));
					return;
				}
				landPathAvailable = true;
			}
			if (!reusableInsertionCompleted && (requiresReusableTransport || ShouldUseTransport(actor, target, landPathAvailable)))
			{
				if (transportService.IsHandlingPassenger(actor))
					return;
				if (transportService.TryRequestReusableTransport(bot, actor, target, landPathAvailable))
				{
					FransBotLog.BotDebug(world, "{0}: Tanya {1} hands C4 RAID {2} {3} to reusable insertion-extraction transport.",
						player, actor.ActorID, target.Info.Name, target.ActorID);
					return;
				}

				if (requiresReusableTransport)
				{
					AbortRaidMission(bot, actor, mission, "defended Tanya C4 RAID requires a reusable transport, but none is currently legal or available");
					return;
				}
			}
			if (!reusableInsertionCompleted && !landPathAvailable)
			{
				AbortRaidMission(bot, actor, mission, "Tanya has neither a preferred safe land approach nor reusable transport");
				return;
			}

			var sameTarget = demolitionTargets.TryGetValue(actor, out var existingTarget) && existingTarget == target.ActorID;
			if (sameTarget && lastDemolitionOrderTick.TryGetValue(actor, out var last) &&
				world.WorldTick - last < Info.DemolitionAttackRefreshInterval)
				return;

			if (!sameTarget)
				actor.CancelActivity();
			bot.QueueOrder(new Order("C4", actor, Target.FromActor(target), false));
			demolitionTargets[actor] = target.ActorID;
			lastDemolitionOrderTick[actor] = world.WorldTick;
			if (!sameTarget)
				FransBotLog.BotDebug(world, "{0}: Tanya {1} begins native C4 demolition against {2} {3}; she is reusable and extraction remains reserved when insertion used transport.",
					player, actor.ActorID, target.Info.Name, target.ActorID);
		}

		void ExecuteDemolitionRaidMission(IBot bot, Actor actor, Actor target, FransActiveMission mission)
		{
			var mobile = actor.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused || !CanDemolitionAttackTarget(actor, target))
			{
				AbortRaidMission(bot, actor, mission, "demolition actor movement/attack capability is unavailable");
				return;
			}
			var immediate = riskModelService.EvaluateImmediateRisk(actor, actor.Location, FransRiskRole.Capturer, Info.AbortRiskTolerance);
			if (immediate.IsCritical)
			{
				AbortRaidMission(bot, actor, mission, $"demolition route became critical risk {immediate.Score}");
				return;
			}
			if (!TryEvaluateRaidApproach(actor, target, out _, out _, out _))
			{
				AbortRaidMission(bot, actor, mission, "demolition target no longer has a preferred safe approach");
				return;
			}

			var sameTarget = demolitionTargets.TryGetValue(actor, out var existingTarget) && existingTarget == target.ActorID;
			if (sameTarget && !actor.IsIdle && lastDemolitionOrderTick.TryGetValue(actor, out var last) &&
				world.WorldTick - last < Info.DemolitionAttackRefreshInterval)
				return;
			if (!sameTarget)
				actor.CancelActivity();
			bot.QueueOrder(new Order("Attack", actor, Target.FromActor(target), false));
			demolitionTargets[actor] = target.ActorID;
			lastDemolitionOrderTick[actor] = world.WorldTick;
			if (!sameTarget)
				FransBotLog.BotDebug(world,
					"{0}: SpecOps {1} accepts RAID {2} {3} with Demo Truck {4}; native Attack triggers the stock DemoTruckTargeting/KillsSelf demolition behavior.",
					player, Info.BidderKey, target.Info.Name, target.ActorID, actor.ActorID);
		}

		void ReturnRaidActorToAnchor(IBot bot, Actor actor, FransActiveMission mission)
		{
			var extractionStarted = actor != null && Info.MissionMode == FransSpecOpsMissionMode.C4Demolition &&
				transportService?.TryBeginReusableExtraction(bot, actor) == true;
			if (!extractionStarted && transportService != null)
			{
				if (actor != null && transportService.IsHandlingPassenger(actor))
					transportService.CancelCaptureTransport(bot, actor);
				else if (actor == null && mission.CommittedActorIds != null && mission.CommittedActorIds.Length == 1)
					transportService.CancelCaptureTransport(bot, mission.CommittedActorIds[0]);
			}

			if (actor == null)
				return;
			ClearMission(actor);
			demolitionTargets.Remove(actor);
			lastDemolitionOrderTick.Remove(actor);
			if (!actor.IsInWorld || actor.IsDead || actor.Owner != player)
				return;

			var reservationTicks = Math.Max(250, Info.RouteRecheckInterval * 2);
			if (extractionStarted)
			{
				recoveryReservationsUntil[actor.ActorID] = world.WorldTick + Math.Max(reservationTicks, 1500);
				FransBotLog.BotDebug(world, "{0}: Tanya {1} finishes C4 mission and begins reserved reusable-transport extraction instead of walking back to MISSION ANCHOR.", player, actor.ActorID);
				return;
			}

			actor.CancelActivity();
			var mobile = actor.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused)
				return;
			if (mission.HasAnchorPoint && riskModelService.EvaluateCell(actor, mission.AnchorPoint,
				FransRiskRole.Capturer, Info.AbortRiskTolerance).IsPreferred)
			{
				bot.QueueOrder(new Order("Move", actor, Target.FromCell(world, mission.AnchorPoint), false));
				var eta = commanderCoreService.EstimateMoveEtaTicks(actor, mission.AnchorPoint);
				reservationTicks = Math.Max(reservationTicks, eta + 250);
			}
			else
				QueueEscape(bot, actor, mobile);

			recoveryReservationsUntil[actor.ActorID] = world.WorldTick + reservationTicks;
		}

		void AbortRaidMission(IBot bot, Actor actor, FransActiveMission mission, string reason)
		{
			ReturnRaidActorToAnchor(bot, actor, mission);
			commandBidService.ReleaseMission(FransCommanderKind.SpecOps, Info.BidderKey, reason);
			generalService.ReportRaidRetreat(mission.TargetActorId, $"SpecOps {Info.BidderKey}: {reason}");
			ResetRaidLostTargetSearch(false);
			PublishRecoveryReservations();
			FransBotLog.BotDebug(world,
				"{0}: SpecOps {1} aborts RAID {2} into RETREAT/ANCHOR return: {3}.",
				player, Info.BidderKey, mission.TargetActorId, reason);
		}

		void FinishRaidMission(IBot bot, Actor actor, FransActiveMission mission, string reason)
		{
			ReturnRaidActorToAnchor(bot, actor, mission);
			commandBidService.ReleaseMission(FransCommanderKind.SpecOps, Info.BidderKey, reason);
			ResetRaidLostTargetSearch(false);
			PublishRecoveryReservations();
			FransBotLog.BotDebug(world,
				"{0}: SpecOps {1} ends RAID {2} normally: {3}. Surviving specialist returns toward MISSION ANCHOR; no General cooldown is applied.",
				player, Info.BidderKey, mission.TargetActorId, reason);
		}

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			if (self == null || !Info.ManagedActorTypes.Contains(self.Info.Name.ToLowerInvariant()) || e.Attacker == null ||
				player.RelationshipWith(e.Attacker.Owner) != PlayerRelationship.Enemy)
				return;

			// AttackInfo may surface player/system actors as the damage source. Only a live physical
			// enemy actor that is legitimately visible may prove that the C4/capture corridor is
			// defended. Hidden/non-spatial damage is still reflected by RiskModel and normal HP loss,
			// but it does not fabricate a "visible attacker" abort.
			if (!e.Attacker.IsInWorld || e.Attacker.IsDead || e.Attacker.OccupiesSpace == null ||
				!e.Attacker.CanBeViewedByPlayer(player))
				return;
			if (!commandBidService.TryGetActorMission(FransCommanderKind.SpecOps, self.ActorID, out var kind, out var bidder) ||
				kind != FransMissionType.Raid || bidder != Info.BidderKey)
				return;
			if (!commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.SpecOps, Info.BidderKey, out _, out var mission))
				return;
			AbortRaidMission(bot, self, mission,
				$"specialist was attacked by visible {e.Attacker.Info.Name} {e.Attacker.ActorID}; SpecOps RAID requires an undefended target/corridor");
		}

		public bool IsCaptureMissionActor(Actor actor)
		{
			if (actor == null)
				return false;

			if (Info.MissionMode == FransSpecOpsMissionMode.Capture && commandBidService != null &&
				commandBidService.TryGetActorMission(FransCommanderKind.SpecOps, actor.ActorID, out var kind, out var bidder) &&
				kind == FransMissionType.Raid && bidder == Info.BidderKey)
				return true;
			return missions.ContainsKey(actor) || waypoints.ContainsKey(actor) || activeCaptureOrders.ContainsKey(actor) ||
				boldFirstCaptureMissions.ContainsKey(actor) || transportService?.IsHandlingPassenger(actor) == true;
		}

		void SeedExploredMapStaticCaptureKnowledge()
		{
			if (exploredMapStaticKnowledgeSeeded)
				return;

			exploredMapStaticKnowledgeSeeded = true;
			if (!Info.UseExploredMapStaticObjectiveKnowledge || strategicMapService == null || !strategicMapService.ExploreMapEnabled)
				return;

			foreach (var target in world.Actors
				.Where(a => a != null && a.IsInWorld && !a.IsDead && a.OccupiesSpace != null)
				.Where(a => Info.OilDerrickTypes.Contains(a.Info.Name.ToLowerInvariant()))
				.Where(a => player.RelationshipWith(a.Owner) == PlayerRelationship.Neutral))
			{
				exploredMapInitialNeutralOilDerricks.Add(target.ActorID);
				// Seed only the map-start neutral ownership that the map itself exposes.
				// Later hidden ownership changes are deliberately not read here.
				lastTrackedOwners[target] = target.Owner;
			}

			if (exploredMapInitialNeutralOilDerricks.Count > 0)
				FransBotLog.BotDebug(world,
					"{0}: Explore Map static knowledge seeds {1} map-start neutral Oil Derrick objective(s); E6 may plan toward them immediately without waiting for a scout to reveal the already-known map object.",
					player, exploredMapInitialNeutralOilDerricks.Count);
		}

		bool IsExploredMapStaticOilDerrick(Actor target)
		{
			return Info.UseExploredMapStaticObjectiveKnowledge && strategicMapService != null &&
				strategicMapService.ExploreMapEnabled && target != null &&
				exploredMapInitialNeutralOilDerricks.Contains(target.ActorID) &&
				Info.OilDerrickTypes.Contains(target.Info.Name.ToLowerInvariant());
		}

		bool IsTargetRelationshipEligible(Actor target)
		{
			if (target == null)
				return false;

			// A hidden map-start Oil Derrick is still a legitimate stale neutral objective.
			// Do not inspect a later hidden owner to decide whether to send the engineer.
			if (!target.CanBeViewedByPlayer(player) && IsExploredMapStaticOilDerrick(target))
				return Info.CapturableRelationships.HasRelationship(PlayerRelationship.Neutral);

			return Info.CapturableRelationships.HasRelationship(player.RelationshipWith(target.Owner));
		}

		void UpdateCaptureRetentionState()
		{
			if (!Info.EnableStrategicCaptureSecurity)
				return;
			using var perf = FransBotLog.Profile(world, player, "SpecOps.CaptureRetention");

			var tracked = world.ActorsHavingTrait<CaptureManager>()
				.Where(a => a != null && a.IsInWorld && !a.IsDead &&
					(Info.CapturableActorTypes.Count == 0 || Info.CapturableActorTypes.Contains(a.Info.Name.ToLowerInvariant())))
				.ToArray();

			var current = tracked.ToHashSet();
			foreach (var stale in lastTrackedOwners.Keys.Where(a => !current.Contains(a)).ToArray())
				lastTrackedOwners.Remove(stale);
			foreach (var stale in captureRetention.Keys.Where(a => !current.Contains(a)).ToArray())
				captureRetention.Remove(stale);

			foreach (var target in tracked)
			{
				var ownershipVisible = target.CanBeViewedByPlayer(player);
				if (!lastTrackedOwners.TryGetValue(target, out var previousOwner))
				{
					// Dynamic ownership is not map-file knowledge. Do not initialize a hidden
					// enemy/neutral owner from the live Actor. Explored-map Oil Derricks were
					// seeded separately from their legitimate map-start neutral state.
					if (!ownershipVisible)
						continue;

					lastTrackedOwners[target] = target.Owner;
					if (target.Owner == player)
					{
						var initialState = GetOrCreateRetentionState(target);
						initialState.LastCapturedTick = world.WorldTick;
						initialState.FirstAttemptConsumed = true;
					}

					continue;
				}

				if (!ownershipVisible)
				{
					// Dynamic hidden ownership is never queried. If a previously owned objective
					// changes hands outside current vision, SpecOps waits until that fact is
					// legitimately visible again before updating retention/recapture state.
					continue;
				}

				if (previousOwner == target.Owner)
				{
					if (target.Owner == player &&
						captureRetention.TryGetValue(target, out var heldState) &&
						heldState.LossCount > 0 &&
						heldState.LastCapturedTick != int.MinValue &&
						world.WorldTick - heldState.LastCapturedTick >= Info.RecaptureHistoryResetAfterHeldTicks)
					{
						heldState.LossCount = 0;
						heldState.CooldownUntilTick = 0;
						FransBotLog.BotDebug(world,
							"{0}: capture security cleared contested history for {1} after holding it for {2} world ticks.",
							player, target, Info.RecaptureHistoryResetAfterHeldTicks);
					}

					continue;
				}

				lastTrackedOwners[target] = target.Owner;
				var state = GetOrCreateRetentionState(target);

				if (previousOwner == player && target.Owner != player)
				{
					if (state.LastLossTick == int.MinValue ||
						world.WorldTick - state.LastLossTick > Info.RecaptureEscalationWindow)
						state.LossCount = 1;
					else
						state.LossCount++;

					state.LastLossTick = world.WorldTick;
					var cooldown = state.LossCount <= 1 ? Info.FirstRecaptureCooldown : Info.RepeatedRecaptureCooldown;
					state.CooldownUntilTick = world.WorldTick + cooldown;

					FransBotLog.BotDebug(world,
						"{0}: capture security marked {1} contested after loss #{2}; recapture blocked until WT {3}.",
						player, target, state.LossCount, state.CooldownUntilTick);
				}
				else if (target.Owner == player)
				{
					state.LastCapturedTick = world.WorldTick;
					state.FirstAttemptConsumed = true;
					FransBotLog.BotDebug(world,
						"{0}: capture security observed successful ownership of {1}; capture retention/recapture logic is now active.",
						player, target);
				}
			}
		}

		CaptureRetentionState GetOrCreateRetentionState(Actor target)
		{
			if (!captureRetention.TryGetValue(target, out var state))
			{
				state = new CaptureRetentionState();
				captureRetention[target] = state;
			}

			return state;
		}

		bool IsNeverAttemptedNeutralOilDerrick(Actor target)
		{
			if (!Info.BoldFirstNeutralOilCapture || target == null || !target.IsInWorld || target.IsDead ||
				!Info.OilDerrickTypes.Contains(target.Info.Name.ToLowerInvariant()))
				return false;

			var knownNeutral = target.CanBeViewedByPlayer(player)
				? player.RelationshipWith(target.Owner) == PlayerRelationship.Neutral
				: IsExploredMapStaticOilDerrick(target);
			if (!knownNeutral)
				return false;

			return !captureRetention.TryGetValue(target, out var state) || !state.FirstAttemptConsumed;
		}

		bool IsActiveBoldFirstCapture(Actor capturer, Actor target)
		{
			return Info.BoldFirstNeutralOilCapture && capturer != null && target != null &&
				boldFirstCaptureMissions.TryGetValue(capturer, out var boldTarget) && boldTarget == target;
		}

		bool IsBoldFirstCaptureTarget(Actor target)
		{
			return IsNeverAttemptedNeutralOilDerrick(target) || boldFirstCaptureMissions.Values.Contains(target);
		}

		void StartBoldFirstCaptureMission(Actor capturer, Actor target)
		{
			if (!IsNeverAttemptedNeutralOilDerrick(target))
				return;

			var state = GetOrCreateRetentionState(target);
			state.FirstAttemptConsumed = true;
			boldFirstCaptureMissions[capturer] = target;
			FransBotLog.BotDebug(world,
				"{0}: bold first capture started for known neutral oil derrick {1}; strategic holdability is ignored for this first mission, but visible threats still matter.",
				player, target);
		}

		bool IsCaptureSecurityEligible(Actor target)
		{
			if (!Info.EnableStrategicCaptureSecurity || target == null)
				return true;

			if (IsBoldFirstCaptureTarget(target))
				return true;

			var type = target.Info.Name.ToLowerInvariant();
			var hasLossHistory = captureRetention.TryGetValue(target, out var state) && state.LossCount > 0;
			if (hasLossHistory && world.WorldTick < state.CooldownUntilTick)
				return false;

			var requiresStrategicSupport = hasLossHistory || Info.StrategicSecurityTargetTypes.Contains(type);
			if (!requiresStrategicSupport)
				return true;

			return IsStrategicallySupportableCapture(target, hasLossHistory,
				hasLossHistory && state.LossCount >= Info.StronglyContestedLossCount);
		}

		bool IsStrategicallySupportableCapture(Actor target, bool isRecapture, bool stronglyContested)
		{
			var localSupport = CountOwnGroundCombatSupport(target.CenterPosition, Info.StrategicCaptureLocalSupportRadius);

			var commanderNearby = false;
			var commanderSupport = localSupport;
			if (commanderCoreService != null &&
				commanderCoreService.TryGetGroundDemandPoint(out var commanderCenter, out _, out _))
			{
				var radiusSquared = Info.StrategicCaptureCommanderSupportRadius * Info.StrategicCaptureCommanderSupportRadius;
				commanderNearby = (commanderCenter - target.Location).LengthSquared <= radiusSquared;
			}

			var metrics = default(FransStrategicSectorMetrics);
			var metricsKnown = strategicMapService.TryGetSectorMetrics(target.Location, out metrics);
			var threatAcceptable = riskModelService.EvaluateStrategicCell(target.Location,
				FransRiskRole.Capturer, Info.MissionRiskTolerance).IsPreferred;
			var controlFavorable = metricsKnown &&
				metrics.OwnControlScore >= metrics.EnemyControlScore;
			var controlNotEnemyDominated = !metricsKnown ||
				metrics.EnemyControlScore <= metrics.OwnControlScore + Info.StrategicCaptureEnemyControlMargin;

			var behindStableFront = IsOnOrBehindStableFront(target.Location);
			var groundConnected = strategicMapService.TryGetStrategicSectorRoute(
				baseBuilderService.StrategicBaseCenter,
				target.Location,
				FransStrategicMovementLayer.Ground,
				FransStrategicRoutePolicy.Fast,
				out _);

			if (stronglyContested)
			{
				if (localSupport >= Info.StronglyContestedMinimumLocalSupport)
					return true;

				return commanderNearby && commanderSupport >= Info.StronglyContestedMinimumCommanderSupportUnits && threatAcceptable;
			}

			var requiredLocalSupport = isRecapture ? Info.StrategicRecaptureMinimumLocalSupport : Info.StrategicCaptureMinimumLocalSupport;
			if (localSupport >= requiredLocalSupport)
				return true;

			var requiredCommanderSupport = isRecapture ? Info.StrategicRecaptureMinimumCommanderSupportUnits : Info.StrategicCaptureMinimumCommanderSupportUnits;
			if (commanderNearby && commanderSupport >= requiredCommanderSupport)
				return true;

			if (!behindStableFront || !groundConnected || !threatAcceptable)
				return false;

			return isRecapture ? controlFavorable : controlNotEnemyDominated;
		}

		bool IsOnOrBehindStableFront(CPos target)
		{
			if (!baseBuilderService.StrategicForwardTarget.HasValue)
				return false;

			var origin = baseBuilderService.StrategicBaseCenter;
			var front = baseBuilderService.StrategicForwardTarget.Value;
			var fx = front.X - origin.X;
			var fy = front.Y - origin.Y;
			var tx = target.X - origin.X;
			var ty = target.Y - origin.Y;

			var frontLengthSquared = (long)fx * fx + (long)fy * fy;
			if (frontLengthSquared <= 0)
				return false;

			var projection = (long)tx * fx + (long)ty * fy;
			var scale = Math.Max(Math.Abs(fx), Math.Abs(fy));
			var marginProjection = (long)Info.StrategicCaptureFrontMarginCells * Math.Max(1, scale);
			return projection <= frontLengthSquared + marginProjection;
		}

		int CountOwnGroundCombatSupport(WPos position, int radius)
		{
			return world.FindActorsInCircle(position, WDist.FromCells(radius))
				.Count(a => a != null &&
					a.IsInWorld &&
					!a.IsDead &&
					a.Owner == player &&
					a.Info.HasTraitInfo<AttackBaseInfo>() &&
					!Info.ManagedActorTypes.Contains(a.Info.Name.ToLowerInvariant()));
		}

		void ManageCapturer(IBot bot, Actor capturer, bool allowAutonomousNeutral = false)
		{
			if (Info.EnableTransportSupport &&
				transportService.TryConsumeCompletedCaptureTransport(capturer, out var transportedTarget) &&
				transportedTarget != null)
			{
				missions[capturer] = transportedTarget;
				waypoints.Remove(capturer);
				activeCaptureOrders.Remove(capturer);
				nextRouteRecheckTick.Remove(capturer);
				AIUtils.BotDebug("{0}: {1} returned from Frans transport; resuming capture target {2} through unified RiskModel.",
					player, capturer, transportedTarget);
			}

			var captureManager = capturer.TraitOrDefault<CaptureManager>();
			var mobile = capturer.TraitOrDefault<Mobile>();
			if (captureManager == null || mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused)
			{
				ClearMission(capturer);
				return;
			}

			var transportHandling = Info.EnableTransportSupport &&
				transportService.IsHandlingPassenger(capturer);
			var immediateRisk = riskModelService.EvaluateImmediateRisk(capturer, capturer.Location,
				FransRiskRole.Capturer, Info.AbortRiskTolerance);
			if (immediateRisk.IsCritical)
			{
				if (transportHandling)
					transportService.CancelCaptureTransport(bot, capturer);
				ClearMission(capturer);
				if (QueueEscape(bot, capturer, mobile))
					AIUtils.BotDebug("{0}: {1} aborts capture activity: unified RiskModel immediate risk {2} >= critical {3}.",
						player, capturer, immediateRisk.Score, immediateRisk.CriticalThreshold);
				return;
			}

			if (transportHandling)
				return;

			if (waypoints.TryGetValue(capturer, out var activeWaypoint))
			{
				if (mobile.ToCell == activeWaypoint)
				{
					waypoints.Remove(capturer);
					nextRouteRecheckTick.Remove(capturer);
				}
				else if (!capturer.IsIdle)
				{
					if (!nextRouteRecheckTick.TryGetValue(capturer, out var nextCheck) || world.WorldTick >= nextCheck)
					{
						nextRouteRecheckTick[capturer] = world.WorldTick + Info.RouteRecheckInterval;
						var tolerance = CurrentCaptureTolerance(capturer);
						var route = riskModelService.EvaluateDirectRoute(capturer, capturer.Location, activeWaypoint,
							FransRiskRole.Capturer, tolerance);
						if (route.IsCritical)
						{
							capturer.CancelActivity();
							waypoints.Remove(capturer);
							activeCaptureOrders.Remove(capturer);
							AIUtils.BotDebug("{0}: {1} cancels a capture approach after unified RiskModel route risk rose to {2} at {3}.",
								player, capturer, route.PeakScore, route.PeakCell);
						}
					}
					return;
				}
				else
				{
					waypoints.Remove(capturer);
					activeCaptureOrders.Remove(capturer);
					nextRouteRecheckTick.Remove(capturer);
				}
			}

			if (activeCaptureOrders.TryGetValue(capturer, out var activeCaptureTarget))
			{
				if (!missions.TryGetValue(capturer, out var trackedTarget) || trackedTarget != activeCaptureTarget ||
					!IsEligibleTarget(capturer, captureManager, activeCaptureTarget))
					activeCaptureOrders.Remove(capturer);
				else if (HasQueuedOrActiveCapture(capturer))
					return;
				else
					activeCaptureOrders.Remove(capturer);
			}

			if (missions.TryGetValue(capturer, out var missionTarget))
			{
				if (IsTargetReservedByEarlierCapturer(capturer, missionTarget) ||
					!IsEligibleTarget(capturer, captureManager, missionTarget))
				{
					ClearMission(capturer);
					return;
				}

				var tolerance = CurrentCaptureTolerance(capturer);
				var targetRisk = riskModelService.EvaluateCell(capturer, missionTarget.Location, FransRiskRole.Capturer, tolerance);
				if (!targetRisk.IsPreferred)
				{
					AIUtils.BotDebug("{0}: {1} abandons capture target {2}: unified RiskModel target risk {3} exceeds preferred {4}.",
						player, capturer, missionTarget, targetRisk.Score, targetRisk.PreferredThreshold);
					ClearMission(capturer);
					return;
				}

				if (!capturer.IsIdle && !IsAtSafeCaptureApproach(capturer, missionTarget))
					return;

				if (!capturer.IsIdle)
					capturer.CancelActivity();

				var landPathAvailable = TryFindRiskAwareApproachPath(capturer, mobile, missionTarget, tolerance,
					out var approachCell, out _);
				if (ShouldUseTransport(capturer, missionTarget, landPathAvailable) &&
					TryStartTransport(bot, capturer, missionTarget, landPathAvailable))
					return;

				if (!landPathAvailable)
				{
					ClearMission(capturer);
					return;
				}

				QueueRiskAwareMoveAndCapture(bot, capturer, mobile, approachCell, missionTarget, tolerance,
					"uses the shared risk layer for its final approach");
				return;
			}

			if (!capturer.IsIdle)
				return;

			if (!allowAutonomousNeutral || Info.AutonomousNeutralCaptureTargetTypes.Count == 0)
				return;

			if (!TryFindBestMission(capturer, captureManager, mobile, out var choice))
				return;

			missions[capturer] = choice.Target;
			StartBoldFirstCaptureMission(capturer, choice.Target);
			AIUtils.BotDebug("{0}: {1} reserves capture target {2}; unified RiskModel target risk {3}, route peak {4}.",
				player, capturer, choice.Target, choice.TargetRiskScore, choice.RoutePeakRisk);

			if (choice.UseTransport && TryStartTransport(bot, capturer, choice.Target, choice.LandPathAvailable))
				return;

			if (!choice.LandPathAvailable || !choice.Waypoint.HasValue)
			{
				ClearMission(capturer);
				return;
			}

			QueueRiskAwareMoveAndCapture(bot, capturer, mobile, choice.Waypoint.Value, choice.Target,
				CurrentCaptureTolerance(capturer), "starts a risk-aware capture mission");
		}

		bool TryFindBestMission(Actor capturer, CaptureManager captureManager, Mobile mobile, out MissionChoice choice)
		{
			using var perf = FransBotLog.Profile(world, player, "SpecOps.CaptureTargetSelection");
			IEnumerable<Actor> candidateActors = combatIntelService.VisibleActors;
			if (Info.UseExploredMapStaticObjectiveKnowledge && strategicMapService.ExploreMapEnabled)
				candidateActors = candidateActors.Concat(exploredMapInitialNeutralOilDerricks
					.Select(world.GetActorById)
					.Where(a => a != null && a.IsInWorld && !a.IsDead && IsExploredMapStaticOilDerrick(a)));

			var lightweightCandidates = candidateActors
				.Distinct()
				.Where(target => target != null && Info.AutonomousNeutralCaptureTargetTypes.Contains(target.Info.Name.ToLowerInvariant()))
				.Where(target => (!target.CanBeViewedByPlayer(player) && IsExploredMapStaticOilDerrick(target)) ||
					player.RelationshipWith(target.Owner) == PlayerRelationship.Neutral)
				.Where(target => IsEligibleTarget(capturer, captureManager, target))
				.Where(target => !IsTargetReservedByOther(capturer, target))
				.Select(target => new TargetCandidate(target, target.GetSellValue(),
					(target.CenterPosition - capturer.CenterPosition).HorizontalLengthSquared));

			var orderedCandidates = Info.PreferNearestTarget
				? lightweightCandidates.OrderBy(c => c.DistanceSquared).ThenByDescending(c => c.Value).ThenBy(c => c.Target.ActorID)
				: lightweightCandidates.OrderByDescending(c => c.Value).ThenBy(c => c.DistanceSquared).ThenBy(c => c.Target.ActorID);

			var candidates = orderedCandidates.Take(maximumCaptureTargetOptions).ToArray();
			var choices = new List<MissionChoice>(candidates.Length);
			foreach (var candidate in candidates)
			{
				var target = candidate.Target;
				var tolerance = IsNeverAttemptedNeutralOilDerrick(target)
					? Info.BoldFirstCaptureRiskTolerance : Info.MissionRiskTolerance;
				var targetRisk = riskModelService.EvaluateCell(capturer, target.Location, FransRiskRole.Capturer, tolerance);
				if (!targetRisk.IsPreferred)
					continue;

				var landPathAvailable = TryFindRiskAwareApproachPath(capturer, mobile, target, tolerance,
					out var approachCell, out var path);
				var useTransport = ShouldUseTransport(capturer, target, landPathAvailable) &&
					transportService.CanPotentiallyTransport(capturer, target, landPathAvailable);
				if (!landPathAvailable && !useTransport)
					continue;

				var routePeak = 0;
				if (landPathAvailable && path != null && path.Count > 0)
					routePeak = riskModelService.EvaluateRoute(capturer, path, FransRiskRole.Capturer, tolerance).PeakScore;

				choices.Add(new MissionChoice(target, landPathAvailable ? approachCell : null, useTransport,
					landPathAvailable, targetRisk.Score, routePeak, candidate.Value, candidate.DistanceSquared));
			}

			IOrderedEnumerable<MissionChoice> ordered;
			if (Info.PreferNearestTarget)
				ordered = choices.OrderBy(c => c.TargetRiskScore).ThenBy(c => c.RoutePeakRisk)
					.ThenBy(c => c.DistanceSquared).ThenByDescending(c => c.Value).ThenBy(c => c.Target.ActorID);
			else
				ordered = choices.OrderBy(c => c.TargetRiskScore).ThenBy(c => c.RoutePeakRisk)
					.ThenByDescending(c => c.Value).ThenBy(c => c.DistanceSquared).ThenBy(c => c.Target.ActorID);

			var best = ordered.FirstOrDefault();
			if (best.Target == null)
			{
				choice = default;
				return false;
			}

			choice = best;
			return true;
		}

		bool IsTargetReservedByOther(Actor capturer, Actor target)
		{
			if (missions.Any(mission =>
				mission.Key != capturer &&
				mission.Value == target &&
				mission.Key.IsInWorld &&
				!mission.Key.IsDead))
				return true;

			return Info.EnableTransportSupport &&
				transportService.IsCaptureTargetReserved(target, capturer);
		}



		bool ShouldUseTransport(Actor capturer, Actor target, bool landPathAvailable)
		{
			if (!Info.EnableTransportSupport || Info.ManagedActorTypes.Count == 0)
				return false;

			if (Info.TransportTargetTypes.Count > 0 &&
				!Info.TransportTargetTypes.Contains(target.Info.Name.ToLowerInvariant()))
				return false;

			if (!landPathAvailable)
				return true;

			if (Info.MinimumTransportDistance <= 0)
				return true;

			var min = WDist.FromCells(Info.MinimumTransportDistance).Length;
			return (target.CenterPosition - capturer.CenterPosition).HorizontalLength >= min;
		}

		bool TryStartTransport(IBot bot, Actor capturer, Actor target, bool landPathAvailable)
		{
			if (!ShouldUseTransport(capturer, target, landPathAvailable) ||
				!transportService.TryRequestCaptureTransport(bot, capturer, target, landPathAvailable))
				return false;

			// The target reservation stays in `missions` while the engineer is waiting to
			// board. Once Cargo removes the actor from the world, transportService itself
			// keeps the target reserved until unload/handoff.
			waypoints.Remove(capturer);
			activeCaptureOrders.Remove(capturer);
			nextRouteRecheckTick.Remove(capturer);
			capturer.CancelActivity();

			AIUtils.BotDebug("{0}: {1} handed capture target {2} to FransTransportCommanderBotModule.",
				player, capturer, target);
			return true;
		}


		bool IsTargetReservedByEarlierCapturer(Actor capturer, Actor target)
		{
			foreach (var mission in missions)
			{
				if (mission.Key == capturer || mission.Value != target)
					continue;

				if (mission.Key.IsInWorld && !mission.Key.IsDead &&
					mission.Key.ActorID < capturer.ActorID)
					return true;
			}

			return false;
		}

		bool IsKnownCaptureTarget(Actor target)
		{
			if (!Info.CheckCaptureTargetsForVisibility || target.CanBeViewedByPlayer(player))
				return true;

			// Explore Map exposes static map objects from match start. The seeded actor id/location
			// is fair map knowledge; later hidden ownership is deliberately not queried here.
			return IsExploredMapStaticOilDerrick(target);
		}

		bool IsEligibleTarget(Actor capturer, CaptureManager capturerCaptureManager, Actor target)
		{
			if (!target.IsInWorld || target.IsDead || target == capturer)
				return false;

			if (!IsTargetRelationshipEligible(target))
				return false;

			if (!IsKnownCaptureTarget(target))
				return false;

			var targetType = target.Info.Name.ToLowerInvariant();
			if (Info.CapturableActorTypes.Count > 0 && !Info.CapturableActorTypes.Contains(targetType))
				return false;

			if (Info.ConstructionYardCaptureTypes.Contains(targetType) && expansionStateService != null &&
				!expansionStateService.CanAcquireConstructionYardSlot)
				return false;

			if (!IsEngineerCaptureTargetLocallyClear(target))
				return false;

			if (!IsCaptureSecurityEligible(target))
				return false;

			var targetCaptureManager = target.TraitOrDefault<CaptureManager>();
			if (targetCaptureManager == null)
				return false;

			// A hidden Explore-Map Oil Derrick is pursued from its legitimate map-start
			// neutral state. Do not let CanTarget leak a later hidden owner relationship;
			// once the engineer reveals the objective, normal owner/CanTarget checks resume.
			if (!target.CanBeViewedByPlayer(player) && IsExploredMapStaticOilDerrick(target))
				return true;

			return capturerCaptureManager.CanTarget(targetCaptureManager);
		}

		bool IsAtSafeCaptureApproach(Actor capturer, Actor target)
		{
			var maxDistance = WDist.FromCells(Info.SafeApproachRadius).Length;
			return (target.CenterPosition - capturer.CenterPosition).HorizontalLength <= maxDistance;
		}

		FransRiskTolerance CurrentCaptureTolerance(Actor capturer)
		{
			return missions.TryGetValue(capturer, out var target) && IsActiveBoldFirstCapture(capturer, target)
				? Info.BoldFirstCaptureRiskTolerance : Info.MissionRiskTolerance;
		}

		bool TryFindRiskAwareApproachPath(Actor capturer, Mobile mobile, Actor target, FransRiskTolerance tolerance,
			out CPos approachCell, out List<CPos> path)
		{
			using var perf = FransBotLog.Profile(world, player, "SpecOps.RiskAwarePath");
			var key = new RiskAwarePathMemoKey(world.WorldTick, capturer.ActorID, mobile.ToCell,
				target.ActorID, target.Location, tolerance, Info.SafeApproachRadius,
				riskModelService.RiskRevision, strategicMapService.TerrainKnowledgeVersion);
			if (riskAwarePathMemo.TryGetValue(key, out var cached))
			{
				approachCell = cached.ApproachCell;
				path = cached.Path == null ? null : new List<CPos>(cached.Path);
				return cached.Available;
			}

			var available = ComputeRiskAwareApproachPath(capturer, mobile, target, tolerance, out approachCell, out path);
			riskAwarePathMemo[key] = new RiskAwarePathMemoResult(available, approachCell, path?.ToArray());
			return available;
		}

		bool ComputeRiskAwareApproachPath(Actor capturer, Mobile mobile, Actor target, FransRiskTolerance tolerance,
			out CPos approachCell, out List<CPos> path)
		{
			using var perf = FransBotLog.Profile(world, player, "SpecOps.RiskAwarePath.Compute");
			var candidateCells = world.Map.FindTilesInAnnulus(target.Location, 1, Info.SafeApproachRadius)
				.Where(cell => mobile.CanEnterCell(cell, check: BlockedByActor.Immovable) && mobile.CanStayInCell(cell))
				.Where(cell => riskModelService.EvaluateCell(capturer, cell, FransRiskRole.Capturer, tolerance).IsPreferred)
				.ToArray();
			if (candidateCells.Length == 0 || mobile.PathFinder is not PathFinder pathFinder)
			{
				approachCell = default;
				path = null;
				return false;
			}

			var pathMightExist = candidateCells.Any(cell =>
				pathFinder.PathMightExistForLocomotorBlockedByImmovable(
					mobile.Locomotor, mobile.ToCell, cell));
			if (!pathMightExist)
			{
				approachCell = default;
				path = null;
				return false;
			}

			path = riskModelService.ExecuteWithPreparedPathCost(capturer,
				FransRiskRole.Capturer, tolerance, preparedPathCost =>
				{
					int CustomCost(CPos cell) => cell == mobile.ToCell ? 0 : preparedPathCost(cell);
					return pathFinder.FindPathToTargetCells(capturer, mobile.ToCell, candidateCells,
						BlockedByActor.Immovable, CustomCost, laneBias: false);
				});
			if (path == null || path.Count == 0)
			{
				approachCell = default;
				return false;
			}

			var route = riskModelService.EvaluateRoute(capturer, path, FransRiskRole.Capturer, tolerance);
			if (route.IsCritical)
			{
				approachCell = default;
				return false;
			}

			approachCell = path[0];
			return true;
		}

		static bool HasQueuedOrActiveCapture(Actor capturer)
		{
			return capturer.CurrentActivity?.ActivitiesImplementing<CaptureActor>().Any() == true;
		}

		void QueueRiskAwareMoveAndCapture(IBot bot, Actor capturer, Mobile mobile, CPos destination,
			Actor target, FransRiskTolerance tolerance, string reason)
		{
			waypoints[capturer] = destination;
			activeCaptureOrders[capturer] = target;
			nextRouteRecheckTick[capturer] = world.WorldTick + Info.RouteRecheckInterval;
			int CustomCost(CPos cell) => cell == mobile.ToCell ? 0 :
				riskModelService.GetPathCost(capturer, cell, FransRiskRole.Capturer, tolerance);

			AIUtils.BotDebug("{0}: {1} {2}; unified RiskModel Move -> CaptureActor via {3} to {4}.",
				player, capturer, reason, destination, target);
			capturer.QueueActivity(false, new Move(capturer, check =>
			{
				if (mobile.ToCell == destination)
					return (true, new List<CPos>());
				if (mobile.PathFinder is not PathFinder pathFinder)
					return (false, new List<CPos>());
				var path = pathFinder.FindPathToTargetCell(capturer, [mobile.ToCell], destination,
					check, CustomCost, laneBias: false);
				return (false, path);
			}));
			capturer.QueueActivity(true, new OpenRA.Activities.CallFunc(() =>
			{
				waypoints.Remove(capturer);
				nextRouteRecheckTick.Remove(capturer);
			}));
			bot.QueueOrder(new Order("CaptureActor", capturer, Target.FromActor(target), true));
		}

		bool QueueEscape(IBot bot, Actor capturer, Mobile mobile)
		{
			var candidates = world.Map.FindTilesInAnnulus(capturer.Location, 2, Info.EscapeSearchRadius)
				.Where(cell => mobile.CanEnterCell(cell, check: BlockedByActor.Immovable) && mobile.CanStayInCell(cell))
				.Select(cell => (Cell: cell, Risk: riskModelService.EvaluateCell(capturer, cell,
					FransRiskRole.Capturer, Info.AbortRiskTolerance)))
				.Where(x => !x.Risk.IsCritical)
				.OrderBy(x => x.Risk.Score)
				.ThenBy(x => (x.Cell - capturer.Location).LengthSquared)
				.Take(16)
				.ToArray();
			if (candidates.Length == 0 || mobile.PathFinder is not PathFinder pathFinder)
				return false;

			foreach (var candidate in candidates)
			{
				int CustomCost(CPos cell) => cell == mobile.ToCell ? 0 :
					riskModelService.GetPathCost(capturer, cell, FransRiskRole.Capturer, Info.AbortRiskTolerance);
				var path = pathFinder.FindPathToTargetCell(capturer, [mobile.ToCell], candidate.Cell,
					BlockedByActor.Immovable, CustomCost, laneBias: false);
				if (path == null || path.Count == 0)
					continue;
				capturer.CancelActivity();
				capturer.QueueActivity(false, new Move(capturer, check =>
				{
					var dynamicPath = pathFinder.FindPathToTargetCell(capturer, [mobile.ToCell], candidate.Cell,
						check, CustomCost, laneBias: false);
					return (false, dynamicPath);
				}));
				return true;
			}
			return false;
		}


		void ManageDemandDrivenProduction(IBot bot)
		{
			using var perf = FransBotLog.Profile(world, player, "SpecOps.DemandProduction");
			if (!Info.EnableDemandDrivenProduction || player.WinState != WinState.Undefined ||
				world.WorldTick < nextDemandProductionRequestTick || specOpsProductionMailbox == null)
				return;

			var actorType = Info.DemandProductionActorType;
			if (!world.Map.Rules.Actors.TryGetValue(actorType, out var actorInfo))
				return;

			var buildableInfo = actorInfo.TraitInfoOrDefault<BuildableInfo>();
			if (buildableInfo == null)
				return;

			var queuesByCategory = AIUtils.FindQueuesByCategory(player);

			// Only create a request when a currently enabled producer can actually build
			// the specialist. This avoids leaving a stale request queued for many minutes
			// on maps/factions that do not yet have a compatible producer.
			var hasCompatibleProducer = buildableInfo.Queue
				.Distinct()
				.SelectMany(category => queuesByCategory[category])
				.Any(queue => queue.Enabled && queue.Actor.IsInWorld && !queue.Actor.IsDead &&
					queue.BuildableItems().Any(item => item.Name == actorType));

			if (!hasCompatibleProducer)
				return;

			var referenceSpecialist = managedActors.Actors
				.FirstOrDefault(a => a.IsInWorld && !a.IsDead && a.Info.Name == actorType);

			var safeDemandTargets = CountSafeDemandTargets(referenceSpecialist);
			if (safeDemandTargets <= 0)
				return;

			var desiredCapturers = Math.Min(
				Info.MaximumDemandCapturers,
				(safeDemandTargets + Info.DemandTargetsPerCapturer - 1) / Info.DemandTargetsPerCapturer);

			var ownedCapturers = managedActors.Actors
				.Count(a => a.IsInWorld && !a.IsDead && a.Info.Name == actorType);

			if (Info.EnableTransportSupport)
				ownedCapturers += transportService.CountTransportedPassengers(actorType);

			var queuedCapturers = buildableInfo.Queue
				.Distinct()
				.SelectMany(category => queuesByCategory[category])
				.Where(queue => queue.Enabled)
				.Sum(queue => queue.AllQueued().Count(item => item.Item == actorType));

			var requestedCapturers = specOpsProductionMailbox.RequestedSpecOpsProductionCount(bot, actorType);
			var totalCommittedCapturers = ownedCapturers + queuedCapturers + requestedCapturers;

			if (totalCommittedCapturers >= desiredCapturers)
				return;

			specOpsProductionMailbox.RequestSpecOpsProduction(bot, actorType);
			nextDemandProductionRequestTick = world.WorldTick + Info.DemandProductionCooldown;

			FransBotLog.BotDebug(world, "{0}: SpecOps {1} demand-production requested {2}: {3} safe/current-or-memory opportunity(ies), " +
				"{4} owned/queued/requested, desired {5}; production memory {6} WT never authorizes a bid/order.",
				player, Info.BidderKey, actorType, safeDemandTargets, totalCommittedCapturers, desiredCapturers, Info.DemandOpportunityMemoryTicks);
		}

		void ManageSupportMechanicDemand(IBot bot)
		{
			using var perf = FransBotLog.Profile(world, player, "SpecOps.SupportDemand");
			if (!Info.EnableSupportMechanicDemand || specOpsProductionMailbox == null ||
				world.WorldTick < nextSupportMechanicRequestTick || player.WinState != WinState.Undefined)
				return;

			var actorType = Info.SupportMechanicActorType;
			if (!world.Map.Rules.Actors.TryGetValue(actorType, out var actorInfo))
				return;

			var buildableInfo = actorInfo.TraitInfoOrDefault<BuildableInfo>();
			if (buildableInfo == null)
				return;

			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			var compatibleQueues = buildableInfo.Queue.Distinct()
				.SelectMany(category => queuesByCategory[category])
				.Where(q => q.Enabled && q.Actor.IsInWorld && !q.Actor.IsDead)
				.ToArray();
			if (!compatibleQueues.Any(q => q.BuildableItems().Any(item => item.Name == actorType)))
				return;

			combatIntelService.EnsureCurrentSnapshot();
			var damagedGroundVehicles = combatIntelService.OwnedActors.Count(a =>
			{
				if (a == null || !a.IsInWorld || a.IsDead || !commanderCoreService.IsGroundVehicleCombatUnitOwned(a))
					return false;
				var health = a.TraitOrDefault<Health>();
				return health != null && health.MaxHP > 0 &&
					(long)health.HP * 100 < (long)health.MaxHP * Info.SupportMechanicDamagedVehicleHealthPercent;
			});

			if (damagedGroundVehicles < Info.SupportMechanicMinimumDamagedVehicles)
				return;

			var owned = combatIntelService.OwnedActors.Count(a => a != null && a.IsInWorld && !a.IsDead && a.Info.Name == actorType);
			var queued = compatibleQueues.Sum(q => q.AllQueued().Count(item => item.Item == actorType));
			var requested = specOpsProductionMailbox.RequestedSpecOpsProductionCount(bot, actorType);
			if (owned + queued + requested >= Info.MaximumSupportMechanics)
				return;

			specOpsProductionMailbox.RequestSpecOpsProduction(bot, actorType);
			nextSupportMechanicRequestTick = world.WorldTick + Info.SupportMechanicProductionCooldown;
			FransBotLog.BotDebug(world,
				"{0}: SPECOPS SUPPORT REQUEST publishes {1}: {2} Ground combat vehicle(s) are below {3}% HP; owned/queued/requested {4}/{5}. Mechanic remains support-only and is not a RAID actor.",
				player, actorType, damagedGroundVehicles, Info.SupportMechanicDamagedVehicleHealthPercent,
				owned + queued + requested, Info.MaximumSupportMechanics);
		}

		int CountSafeDemandTargets(Actor referenceSpecialist)
		{
			var requiredForMaximum = Info.MaximumDemandCapturers * Info.DemandTargetsPerCapturer;
			var countedTargets = new HashSet<uint>();
			PruneDemandOpportunityMemory();

			// Enemy specialist production is derived from the same fair General RAID board that the
			// physical specialist will later bid on. Do not create a private full-map enemy planner here.
			// Every safe current opportunity refreshes production-only memory before older memory is counted.
			generalService.EnsureCurrentMissions();
			combatIntelService.EnsureCurrentSnapshot();
			foreach (var mission in generalService.CurrentMissions
				.Where(j => j.Type == FransMissionType.Raid && !j.IsRememberedIntel && j.Target != null)
				.Where(j => Info.RaidTargetTypes.Contains(j.TargetActorType.ToLowerInvariant()))
				.Where(j => Info.DemandProductionTargetTypes.Contains(j.TargetActorType.ToLowerInvariant()))
				.OrderByDescending(j => j.StrategicPriority)
				.ThenBy(j => j.TargetActorId))
			{
				var target = mission.Target;
				if (!IsVisibleEnemyRaidTarget(target) || !IsSpecOpsRaidTargetUndefended(mission.SiteIntel, mission.TargetActorId, target.Location, out _, out _))
					continue;

				if (Info.MissionMode == FransSpecOpsMissionMode.Capture)
				{
					var targetType = target.Info.Name.ToLowerInvariant();
					if ((Info.CapturableActorTypes.Count > 0 && !Info.CapturableActorTypes.Contains(targetType)) ||
						target.TraitOrDefault<CaptureManager>() == null || !IsTargetRelationshipEligible(target) ||
						(Info.ConstructionYardCaptureTypes.Contains(targetType) && expansionStateService != null &&
							!expansionStateService.CanAcquireConstructionYardSlot) || !IsCaptureSecurityEligible(target))
						continue;
				}
				else if (Info.MissionMode == FransSpecOpsMissionMode.C4Demolition && !target.Info.HasTraitInfo<DemolishableInfo>())
					continue;

				if (Info.DemandProductionRequiresSafeTarget && !IsDemandProductionTargetSafe(target, referenceSpecialist))
					continue;

				countedTargets.Add(target.ActorID);
				RememberDemandOpportunity(target.ActorID, target.Info.Name.ToLowerInvariant(), target.Location);
				if (countedTargets.Count >= requiredForMaximum)
					return countedTargets.Count;
			}

			// production-only memory bridges General's intentionally short fresh RAID lifetime
			// and real unit build time. It never becomes a bid/order target: only fresh CurrentMissions may bid.
			foreach (var targetId in demandOpportunityMemory.Keys.OrderBy(id => id))
			{
				countedTargets.Add(targetId);
				if (countedTargets.Count >= requiredForMaximum)
					return countedTargets.Count;
			}

			// Neutral map objectives are deliberately outside the enemy RAID board. E6 may keep the
			// proven Explore-Map Oil Derrick path when the YAML profile explicitly opts into it.
			if (Info.MissionMode == FransSpecOpsMissionMode.Capture && Info.AutonomousNeutralCaptureTargetTypes.Count > 0)
				foreach (var target in world.ActorsHavingTrait<CaptureManager>()
					.OrderBy(a => a.ActorID))
				{
					if (!target.IsInWorld || target.IsDead || countedTargets.Contains(target.ActorID))
						continue;
					var targetType = target.Info.Name.ToLowerInvariant();
					if (!Info.AutonomousNeutralCaptureTargetTypes.Contains(targetType) ||
						!Info.DemandProductionTargetTypes.Contains(targetType) ||
						!IsTargetRelationshipEligible(target) ||
						!IsKnownCaptureTarget(target) || !IsCaptureSecurityEligible(target))
						continue;

					if (Info.DemandProductionRequiresSafeTarget && !IsDemandProductionTargetSafe(target, referenceSpecialist))
						continue;

					countedTargets.Add(target.ActorID);
					if (countedTargets.Count >= requiredForMaximum)
						break;
				}

			return countedTargets.Count;
		}

		void RememberDemandOpportunity(uint targetActorId, string targetActorType, CPos lastVisibleCell)
		{
			if (Info.DemandOpportunityMemoryTicks <= 0)
				return;
			demandOpportunityMemory[targetActorId] = new DemandOpportunityMemory(targetActorType, lastVisibleCell, world.WorldTick);
		}

		void PruneDemandOpportunityMemory()
		{
			if (demandOpportunityMemory.Count == 0)
				return;
			if (Info.DemandOpportunityMemoryTicks <= 0)
			{
				demandOpportunityMemory.Clear();
				return;
			}

			foreach (var stale in demandOpportunityMemory
				.Where(kv => world.WorldTick - kv.Value.LastSeenWorldTick > Info.DemandOpportunityMemoryTicks)
				.Select(kv => kv.Key)
				.ToArray())
				demandOpportunityMemory.Remove(stale);
		}

		void MaybeLogUtilization(IBot bot)
		{
			if (world.WorldTick < nextUtilizationLogTick)
				return;
			using var perf = FransBotLog.Profile(world, player, "SpecOps.UtilizationReport");
			nextUtilizationLogTick = world.WorldTick + Math.Max(1, Info.UtilizationLogInterval);

			var actorType = Info.DemandProductionActorType;
			var owned = managedActors.Actors.Count(a => a != null && a.IsInWorld && !a.IsDead);
			var operational = managedActors.Actors.Count(IsManagedSpecOpsActorOperational);
			var missionCommitted = commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.SpecOps, Info.BidderKey, out _, out _) ? 1 : 0;
			var ready = Math.Max(0, operational - missionCommitted);
			var requested = 0;
			var queued = 0;
			if (!string.IsNullOrWhiteSpace(actorType) && world.Map.Rules.Actors.TryGetValue(actorType, out var actorInfo))
			{
				if (specOpsProductionMailbox != null)
					requested = specOpsProductionMailbox.RequestedSpecOpsProductionCount(bot, actorType);
				var buildableInfo = actorInfo.TraitInfoOrDefault<BuildableInfo>();
				if (buildableInfo != null)
				{
					var queuesByCategory = AIUtils.FindQueuesByCategory(player);
					queued = buildableInfo.Queue.Distinct()
						.SelectMany(category => queuesByCategory[category])
						.Where(queue => queue.Enabled)
						.Sum(queue => queue.AllQueued().Count(item => item.Item == actorType));
				}
			}

			FransBotLog.BotDebug(world,
				"{0}: SPECOPS UTILIZATION {1}: owned {2}, operational {3}, mission-committed {4}, ready {5}, queued {6}, requested {7}, demand-memory {8}; interval compatible RAID {9}, bids {10}, rejected defended {11}, no-actor {12}, capability {13}, route/ETA/risk {14}.",
				player, Info.BidderKey, owned, operational, missionCommitted, ready, queued, requested, demandOpportunityMemory.Count,
				utilizationCompatibleRaidTargets.Count, utilizationBidTargets.Count, utilizationDefendedTargets.Count,
				utilizationNoActorTargets.Count, utilizationCapabilityRejectedTargets.Count, utilizationRouteRejectedTargets.Count);
			ClearUtilizationCounters();
		}

		void ClearUtilizationCounters()
		{
			utilizationCompatibleRaidTargets.Clear();
			utilizationDefendedTargets.Clear();
			utilizationNoActorTargets.Clear();
			utilizationCapabilityRejectedTargets.Clear();
			utilizationRouteRejectedTargets.Clear();
			utilizationBidTargets.Clear();
		}

		bool IsDemandProductionTargetSafe(Actor target, Actor referenceSpecialist)
		{
			if (Info.MissionMode == FransSpecOpsMissionMode.C4Demolition && Info.AllowTransportedC4DefensiveBuildingBypass)
			{
				if (referenceSpecialist != null)
				{
					var mobile = referenceSpecialist.TraitOrDefault<Mobile>();
					if (mobile != null && TryFindPreferredLocalC4ApproachCell(referenceSpecialist, mobile, target, out _))
						return true;
				}
				else
				{
					var strategicSafeApproach = world.Map.FindTilesInAnnulus(target.Location, 1, Info.SafeApproachRadius)
						.Where(world.Map.Contains)
						.Any(c => riskModelService.EvaluateStrategicCell(c, FransRiskRole.Capturer, Info.MissionRiskTolerance).IsPreferred);
					if (strategicSafeApproach)
						return true;
				}
			}
			var tolerance = IsNeverAttemptedNeutralOilDerrick(target)
				? Info.BoldFirstCaptureRiskTolerance : Info.MissionRiskTolerance;
			if (referenceSpecialist != null)
				return riskModelService.EvaluateCell(referenceSpecialist, target.Location,
					FransRiskRole.Capturer, tolerance).IsPreferred;

			// No specialist exists yet. Use only fair strategic/remembered risk; the produced unit
			// will perform actor-specific weapon-validity/path checks before a real mission.
			return riskModelService.EvaluateStrategicCell(target.Location,
				FransRiskRole.Capturer, tolerance).IsPreferred;
		}


		void ClearMission(Actor capturer)
		{
			if (capturer != null)
				completedReusableInsertionActorIds.Remove(capturer.ActorID);
			boldFirstCaptureMissions.Remove(capturer);
			missions.Remove(capturer);
			waypoints.Remove(capturer);
			activeCaptureOrders.Remove(capturer);
			nextRouteRecheckTick.Remove(capturer);
		}

		void RemoveStaleState(IEnumerable<Actor> currentCapturers)
		{
			var current = currentCapturers.ToHashSet();
			foreach (var capturer in missions.Keys.Where(a => !current.Contains(a)).ToArray())
				missions.Remove(capturer);

			foreach (var capturer in boldFirstCaptureMissions.Keys.Where(a => !current.Contains(a)).ToArray())
			{
				if (Info.EnableTransportSupport && transportService.IsHandlingPassenger(capturer))
					continue;

				boldFirstCaptureMissions.Remove(capturer);
			}

			foreach (var capturer in waypoints.Keys.Where(a => !current.Contains(a)).ToArray())
				waypoints.Remove(capturer);

			foreach (var capturer in activeCaptureOrders.Keys.Where(a => !current.Contains(a)).ToArray())
				activeCaptureOrders.Remove(capturer);

			foreach (var capturer in nextRouteRecheckTick.Keys.Where(a => !current.Contains(a)).ToArray())
				nextRouteRecheckTick.Remove(capturer);
	
			foreach (var actorId in completedReusableInsertionActorIds.ToArray())
			{
				var actor = world.GetActorById(actorId);
				if (actor == null || actor.Disposed || actor.IsDead || actor.Owner != player)
					completedReusableInsertionActorIds.Remove(actorId);
			}
		}

		void INotifyActorDisposing.Disposing(Actor self)
		{
			managedActors?.Dispose();
		}
	}
}
