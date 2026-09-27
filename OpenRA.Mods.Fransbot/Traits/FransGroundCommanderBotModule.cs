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
using System.Diagnostics;
using System.Linq;
using System.Runtime.CompilerServices;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	/// <summary>Read-only state exposed to production/base modules. It does not issue orders.</summary>
	public interface IFransGroundCommanderService
	{
		bool TryGetGroundDemandPoint(out CPos objective, out FransCommanderOrder order, out int startedWorldTick);
		IReadOnlyList<CPos> GetGroundRegroupPoints();
		bool IsGroundCombatUnitOwned(Actor actor);
		bool IsGroundCombatActorType(string actorType);
		bool IsGroundVehicleCombatUnitOwned(Actor actor);
		bool IsGroundCombatUnitMissionCommitted(Actor actor);
		bool IntersectsGroundStagingReservation(CPos topLeft, int width, int height);
	}

	/// <summary>
	/// Other specialist modules use this only to avoid stealing ordinary combat units from Ground Commander.
	/// </summary>
	public interface IFransGroundUnitReservationService
	{
		bool IsGroundUnitReserved(Actor actor);
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Fransbot Ground Commander. Strategic ATTACK is retired. Ground executes DEFEND/SECURE plus one-unit RECON and exact target-only RAID; local FIGHT/RETREAT remains tactical execution, RiskModel is consulted during strategic movement, territorial SECURE is persistent for expansion, and idle Ground uses only the fair-intel-selected Forward Anchor.")]
	public class FransGroundCommanderBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("World ticks between Ground Commander decisions.")]
		public readonly int ScanInterval = 25;

		[Desc("Unique key for this Ground bidder capacity.")]
		public readonly string BidderKey = "ground1";

		[Desc("Zero-based Ground capacity index. Only index 0 performs autonomous standby/right-of-way behavior outside General missions.")]
		public readonly int CommanderIndex = 0;

		[Desc("Maximum Ground units considered for one precision RAID bid. SECURE sizing is uncapped here and is driven by observed enemy tactical strength.")]
		public readonly int MaximumRaidUnitsPerMission = 32;

		[Desc("Distance in cells at which MOVE becomes FIGHT for a visible MISSION target.")]
		public readonly int FightTriggerRadius = 8;

		[Desc("Local radius used for FIGHT/DEFEND target micro.")]
		public readonly int FightMicroRadius = 14;

		[Desc("Maximum distance for a local crush maneuver inside FIGHT/DEFEND. Crush is a special-case plain Move and never creates its own mission.")]
		public readonly int LocalCrushRadius = 3;

		[Desc("Minimum world ticks before refreshing an unchanged commander movement order.")]
		public readonly int MoveRefreshInterval = 125;

		[Desc("Maximum cells a Ground RAID/SECURE marcher may get ahead of the trailing committed unit before it pauses for cohesion.")]
		public readonly int CohesionMaximumLeadCells = 4;

		[Desc("Temporary maximum lead allowed when the trailing committed unit is stalled in a chokepoint. Once it moves again the normal cohesion limit resumes and the group regroups.")]
		public readonly int CohesionChokepointLeadCells = 8;

		[Desc("Maximum cells a Ground DEFEND marcher may get ahead of the trailing committed unit. DEFEND is intentionally looser than RAID/SECURE so emergency response stays fast while the force still arrives as a group.")]
		public readonly int DefendCohesionMaximumLeadCells = 6;

		[Desc("Temporary Ground DEFEND lead allowed when the trailing committed unit is stalled in a chokepoint.")]
		public readonly int DefendCohesionChokepointLeadCells = 10;

		[Desc("Proposed Ground DEFEND package size that independently qualifies as large for force-preservation evaluation. Smaller packages remain eligible when their relative commitment is high and their resulting reserve is low.")]
		public readonly int DefendForcePreservationMinimumPackageUnits;

		[Desc("Proposed percentage of the eligible free Ground force that identifies a very large DEFEND commitment for force-preservation evaluation.")]
		public readonly int DefendForcePreservationTriggerCommitPercent;

		[Desc("Remaining eligible free Ground percentage below which a large DEFEND package is considered to leave too little reserve.")]
		public readonly int DefendForcePreservationLowReservePercent;

		[Desc("Remaining eligible free Ground unit count below which a large DEFEND package is considered to leave too little reserve.")]
		public readonly int DefendForcePreservationMinimumReserveUnits;

		[Desc("Ground reserve percentage retained when a negative-utility, long-ETA DEFEND package triggers force preservation.")]
		public readonly int DefendForcePreservationTargetReservePercent;

		[Desc("Minimum estimated DEFEND ETA considered long enough for force preservation. Shorter emergency responses remain unchanged.")]
		public readonly int DefendForcePreservationLongEtaMinimumTicks;

		[Desc("Radius around a shared Ground mission destination used to allocate distinct nearby formation cells instead of sending every unit to one exact cell.")]
		public readonly int CohesionFormationRadius = 4;

		[Desc("Minimum world ticks before refreshing an unchanged explicit FIGHT target.")]
		public readonly int FightRefreshInterval = 75;

		[Desc("How long FIGHT may continue toward the last visible target cell after contact is temporarily lost.")]
		public readonly int FightLostContactHoldTicks = 250;

		[Desc("Outer radius around a SECURE coordinate used for remembered enemy buildings and static control objects before ANCHOR is established.")]
		public readonly int SecureThreatRadius = 14;

		[Desc("Inner radius around the SECURE coordinate where visible mobile enemies may block initial CLEAR. Mobile enemies outside this radius are handled only when they directly attack the squad, preventing passing units on the outer control ring from pinning a major SECURE indefinitely.")]
		public readonly int SecureMobileThreatRadius = 8;

		[Desc("World ticks the full SECURE building/static-control radius must remain clear before mobile enemies stop blocking territorial completion. This converts recurring mobile contact into normal local combat instead of allowing transient units to pin a major SECURE forever.")]
		public readonly int SecureTerritorialClearHoldTicks = 250;

		[Desc("Radius around the SECURE objective used to confirm the Ground group has physically occupied the won area.")]
		public readonly int SecureAssemblyRadius = 8;



		[Desc("Tactical-value multiplier applied to fair known hostile combat strength when sizing Ground SECURE.")]
		public readonly int SecureKnownThreatMultiplierPercent;

		[Desc("Tactical combat value added to every Ground SECURE requirement for incomplete or aging local knowledge. This is personality uncertainty, not hidden enemy information.")]
		public readonly int SecureUncertaintyAllowanceValue;

		[Desc("Minimum tactical combat value needed to establish territorial control at a low/unknown-threat SECURE objective. This replaces the old free-army-share floor with an objective-sized bound.")]
		public readonly int SecureMinimumControlValue;

		[Desc("Quadratic opportunity-cost weight charged for SECURE package value above the objective requirement. Higher values make avoidable surplus less competitive while never limiting force required by known hostile strength.")]
		public readonly int SecureSurplusCostWeight;

		[Desc("Maximum cell distance between a published SECURE objective and the PRIMARY PIONEER SECURE REQUIRED objective for expansion-specific no-bid diagnostics.")]
		public readonly int PioneerSecureObjectiveMatchRadius = 12;

		[Desc("Maximum simultaneously active or freshly bid Ground SECURE missions. Keeping this at 1 concentrates the army into one territorial offensive while General may still publish several opportunities for choice.")]
		public readonly int MaximumConcurrentSecureMissions = 1;

		[Desc("Percentage of committed SECURE units that should physically assemble near the supplied ANCHOR before the long march begins. A bounded timeout prevents one straggler from freezing the offensive.")]
		public readonly int SecurePreMoveAssemblyPercent = 80;

		[Desc("Radius around the supplied Ground ANCHOR used for the initial SECURE assembly check.")]
		public readonly int SecurePreMoveAssemblyRadius = 8;

		[Desc("Maximum world ticks spent waiting for initial SECURE assembly before the committed force departs with normal cohesion movement.")]
		public readonly int SecurePreMoveAssemblyTimeout = 500;

		[Desc("World ticks a marching Ground SECURE may make no physical group-center progress toward its territorial objective before the assignment is released as stale. Combat/clear work near the objective does not use this watchdog.")]
		public readonly int SecureMarchNoProgressTimeout = 750;


		[Desc("Tactical combat-value multiplier applied to the infantry subtotal when a Ground squad contains at least InfantrySquadValueMinimumCount infantry. Vehicles keep raw Valued.Cost. 130 means two 300-value infantry count as 780 together while one still counts as 300.")]
		public readonly int InfantrySquadValuePercent = 130;

		[Desc("Minimum infantry count in one Ground tactical group before InfantrySquadValuePercent applies. Keep 2 for 1x solo infantry and 1.3x infantry subtotal from two units upward.")]
		public readonly int InfantrySquadValueMinimumCount = 2;



		[Desc("During an offensive campaign, retreat when surviving committed Ground combat value falls to this percentage or less of the highest combat value established by that campaign before RETREAT. Smaller follow-on fights never lower this baseline.")]
		public readonly int RetreatAtRemainingForcePercent = 50;

		[Desc("After RETREAT, ordinary offensive availability resumes only when combat value physically assembled around the retreat point reaches this percentage of the locked combat baseline.")]
		public readonly int ResumeOffenseAtOriginalForcePercent = 75;

		[Desc("Radius around the logical Anchor Point used to count physically regrouped combat value before offensive bidding resumes.")]
		public readonly int RetreatAssemblyRadius = 8;

		[Desc("Minimum radius from the logical Anchor Point used for individual Ground standby/recovery slots. Spreading units into an annulus prevents one exact Anchor cell from becoming a traffic jam.")]
		public readonly int RetreatRecoverySlotMinimumRadius = 3;

		[Desc("Recovery slots prefer to stay at least this many cells away from current ore/gem resource cells so regrouped combat units do not block harvesters.")]
		public readonly int RetreatResourceClearanceRadius = 2;

		[ActorReference]
		[Desc("Owned traffic-critical structures that Ground standby/recovery slots must not crowd. This protects refinery docking, production exits and MCV/repair traffic from large idle armies.")]
		public readonly FrozenSet<string> StandbyTrafficStructureTypes =
			FrozenSet<string>.Empty;

		[Desc("Minimum cell clearance around StandbyTrafficStructureTypes for Ground standby/recovery slots.")]
		public readonly int StandbyTrafficStructureClearanceRadius = 4;

		[Desc("Minimum live Ground combat-unit count before standby cells and an outward egress corridor become a hard building-placement reservation. Small groups do not reserve base real estate.")]
		public readonly int StagingReservationMinimumGroundUnits = 8;

		[Desc("Radius around the logical Ground standby center kept free of new buildings as a maneuver core while a large staged army is present.")]
		public readonly int StagingReservationCoreRadius = 2;

		[Desc("Length in cells of the reserved outward Ground egress corridor from a large-army staging center toward the current/strategic front.")]
		public readonly int StagingEgressLengthCells = 14;

		[Desc("Half-width in cells of the reserved Ground egress corridor. One creates a three-cell-wide lane where the map permits it.")]
		public readonly int StagingEgressHalfWidthCells = 1;

		[Desc("Maximum NEW/retry Ground blockers given MCV deploy right-of-way Move orders in one expensive clearance pass. Ownership suppression still covers every blocker; this only spreads path/order work across passes.")]
		public readonly int McvRightOfWayMaximumOrdersPerPass = 4;

		[ActorReference]
		[Desc("Actor types never owned by Ground Commander because they belong to economy, capture, transport or other specialist systems.")]
		public readonly FrozenSet<string> ExcludedGroundTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Ground infantry actor types that may still perform DEFEND/SECURE/RECON but are never eligible for RAID bids or RAID execution.")]
		public readonly FrozenSet<string> RaidExcludedInfantryTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Only these small Ground actors may perform persistent one-unit RECON. Heavy vehicles, tanks, ARTY/V2 and APCs remain available for combat missions instead of being consumed by ore-node patrols.")]
		public readonly FrozenSet<string> ReconEligibleGroundTypes =
			FrozenSet<string>.Empty;

		[Desc("Maximum active or freshly bid Ground RAID targets allowed during ordinary DEFEND pressure. Strategic/high-priority DEFEND suppresses new Ground RAID bids entirely and preempts an active RAID so committed actors can defend.")]
		public readonly int MaximumRaidMissionsDuringDefend = 2;

		[Desc("Normal maximum simultaneously active/fresh Ground RAID missions. This prevents the army from being fragmented across many tiny precision attacks.")]
		public readonly int MaximumConcurrentGroundRaidMissions = 2;

		[Desc("Maximum Ground RAID missions while a Ground SECURE is already active/fresh. One small RAID may run beside the major territorial offensive; additional Ground units reinforce the main operation instead.")]
		public readonly int MaximumGroundRaidMissionsDuringSecure = 1;

		[Desc("Adaptive Ground RAID strike-package floor as a percentage of currently free RAID-eligible combat value. Target damage remains mandatory; this only prevents technically sufficient but operationally tiny Ground raids.")]
		public readonly int GroundRaidExpeditionarySharePercent = 35;

		[Desc("Minimum number of Ground units in an ordinary Ground RAID when enough candidates exist. Specialist/Air/Sea RAID sizing is unchanged.")]
		public readonly int GroundRaidMinimumUnitCount = 3;

		[ActorReference]
		[Desc("Non-building mobile target types that Ground is allowed to RAID. Buildings are always eligible; Ground mobile RAID is deliberately limited to harvesters.")]
		public readonly FrozenSet<string> RaidEligibleMobileTargetTypes = FrozenSet<string>.Empty;

		[Desc("Minimum native Mobile.Speed required for a Ground vehicle to join RAID. Slower combat vehicles remain fully eligible for SECURE/DEFEND but never delay a precision RAID column.")]
		public readonly int RaidMinimumVehicleSpeed = 72;

		[Desc("Hard avoidance radius around remembered/visible non-AA static defenses for Ground RAID only. SECURE is deliberately exempt.")]
		public readonly int RaidStaticDefenseAvoidanceRadius = 6;

		[ActorReference]
		[Desc("Ground RAID actor types allowed to deliberately engage non-AA static defenses. These long-range breakers may also enter the RAID static-defense avoidance zone.")]
		public readonly FrozenSet<string> RaidStaticDefenseBreakerTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Static defenses exempt from Ground RAID avoidance because opening anti-air corridors is an explicit RAID role.")]
		public readonly FrozenSet<string> RaidStaticDefenseAlwaysAllowedTypes = FrozenSet<string>.Empty;

		[ActorReference]
		public readonly FrozenSet<string> NavalTypes = FrozenSet<string>.Empty;

		[ActorReference]
		public readonly FrozenSet<string> AirTypes = FrozenSet<string>.Empty;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			if (ScanInterval < 25 || string.IsNullOrWhiteSpace(BidderKey) || CommanderIndex < 0 || CommanderIndex > 9 || MaximumRaidUnitsPerMission <= 0 || FightTriggerRadius <= 0 || FightMicroRadius <= 0 ||
				LocalCrushRadius <= 0 || MoveRefreshInterval <= 0 || CohesionMaximumLeadCells <= 0 || CohesionChokepointLeadCells < CohesionMaximumLeadCells || DefendCohesionMaximumLeadCells <= 0 || DefendCohesionChokepointLeadCells < DefendCohesionMaximumLeadCells ||
				DefendForcePreservationMinimumPackageUnits <= 0 || DefendForcePreservationTriggerCommitPercent <= 0 || DefendForcePreservationTriggerCommitPercent > 100 || DefendForcePreservationLowReservePercent < 0 || DefendForcePreservationLowReservePercent > 100 || DefendForcePreservationMinimumReserveUnits < 0 || DefendForcePreservationTargetReservePercent <= DefendForcePreservationLowReservePercent || DefendForcePreservationTargetReservePercent >= 100 || DefendForcePreservationLongEtaMinimumTicks <= 0 ||
				CohesionFormationRadius <= 0 || RaidMinimumVehicleSpeed <= 0 || RaidStaticDefenseAvoidanceRadius <= 0 || MaximumRaidMissionsDuringDefend < 0 || MaximumConcurrentGroundRaidMissions <= 0 || MaximumGroundRaidMissionsDuringSecure < 0 || MaximumGroundRaidMissionsDuringSecure > MaximumConcurrentGroundRaidMissions || GroundRaidExpeditionarySharePercent <= 0 || GroundRaidExpeditionarySharePercent > 100 || GroundRaidMinimumUnitCount <= 0 ||
				FightRefreshInterval <= 0 || FightLostContactHoldTicks <= 0 || SecureThreatRadius <= 0 || SecureMobileThreatRadius <= 0 || SecureMobileThreatRadius > SecureThreatRadius || SecureTerritorialClearHoldTicks <= 0 || SecureAssemblyRadius <= 0 || SecureKnownThreatMultiplierPercent < 100 || SecureUncertaintyAllowanceValue < 0 || SecureMinimumControlValue <= 0 || SecureSurplusCostWeight < 0 || PioneerSecureObjectiveMatchRadius <= 0 || MaximumConcurrentSecureMissions <= 0 || SecurePreMoveAssemblyPercent <= 0 || SecurePreMoveAssemblyPercent > 100 || SecurePreMoveAssemblyRadius <= 0 || SecurePreMoveAssemblyTimeout <= 0 || SecureMarchNoProgressTimeout < ScanInterval || InfantrySquadValuePercent <= 0 || InfantrySquadValueMinimumCount <= 0 || RetreatAssemblyRadius <= 0 || RetreatRecoverySlotMinimumRadius < 0 || RetreatRecoverySlotMinimumRadius > RetreatAssemblyRadius || RetreatResourceClearanceRadius < 0 ||
				StandbyTrafficStructureClearanceRadius < 0 || StagingReservationMinimumGroundUnits <= 0 || StagingReservationCoreRadius < 0 || StagingEgressLengthCells <= 0 || StagingEgressHalfWidthCells < 0 || McvRightOfWayMaximumOrdersPerPass <= 0 ||
				RetreatAtRemainingForcePercent <= 0 || RetreatAtRemainingForcePercent >= 100 ||
				ResumeOffenseAtOriginalForcePercent <= RetreatAtRemainingForcePercent || ResumeOffenseAtOriginalForcePercent > 100)
				throw new YamlException("Frans Ground Commander timing/radius/retreat values are invalid.");
		}

		public override object Create(ActorInitializer init) { return new FransGroundCommanderBotModule(init.Self, this); }
	}

	public class FransGroundCommanderBotModule : ConditionalTrait<FransGroundCommanderBotModuleInfo>,
		IBotTick, IBotRespondToAttack, IFransGroundCommanderService, IFransGroundUnitReservationService
	{
		string BidderKey => Info.BidderKey;

		sealed class SharedSecureBidMemoState
		{
			public int WorldTick = -1;
			public int CombatIntelSnapshotWorldTick = -1;
			public int RiskRevision = -1;
			public readonly Dictionary<string, SecureBidPathMemo> Entries = [];
		}

		readonly record struct SecureBidPathMemo(bool Feasible, int RouteRisk, int Eta, int TravelCells, int Force, int Price);
		readonly record struct LstLossNativePathProofKey(uint SubjectActorId, CPos SubjectCell, CPos DestinationCell);
		static readonly ConditionalWeakTable<Player, SharedSecureBidMemoState> SharedSecureBidMemos = new();
		readonly Dictionary<uint, int> pioneerSecureNoBidDiagnosticNextTick = [];
		readonly Dictionary<uint, int> lstLossObjectiveDiagnosticNextTick = [];

		readonly World world;
		readonly Player player;
		readonly HashSet<Actor> managedUnits = [];
		readonly Dictionary<string, bool> managedGroundActorTypeCache = new(StringComparer.Ordinal);
		readonly HashSet<Actor> activeUnits = [];
		readonly Dictionary<Actor, CPos> lastMoveDestination = [];
		readonly Dictionary<Actor, int> lastMoveWorldTick = [];
		readonly Dictionary<Actor, uint> lastFightTarget = [];
		readonly Dictionary<Actor, int> lastFightOrderWorldTick = [];
		readonly HashSet<Actor> mcvRightOfWayUnits = [];
		readonly Dictionary<Actor, CPos> raidRecoveryOrigins = [];
		readonly HashSet<Actor> raidAttackMoveRecoveryActors = [];
		readonly Dictionary<Actor, CPos> raidMissionOrigins = [];
		readonly HashSet<Actor> cohesionHeldUnits = [];
		readonly Dictionary<Actor, CPos> cohesionFormationSlots = [];
		bool hasCohesionFormationObjective;
		CPos cohesionFormationObjective;
		readonly Dictionary<Actor, int> lastMcvRightOfWayOrderTick = [];
		readonly Dictionary<Actor, CPos> anchorStandbySlots = [];
		readonly List<Actor> staleActorCacheKeys = [];
		readonly HashSet<CPos> groundStagingReservationCells = [];
		int groundStagingReservationTick = int.MinValue;
		CPos[] standbyTrafficStructureCells = Array.Empty<CPos>();
		int standbyTrafficStructureSnapshotTick = int.MinValue;
		IResourceLayer resourceLayer;
		bool hasAnchorStandbyCenter;
		CPos anchorStandbyCenter;
		CPos? mcvRightOfWayCenter;
		int mcvRightOfWayRadius;
		int nextMcvRightOfWayClearTick;

		IFransCombatIntelService combatIntelService;
		IFransRiskModelService riskModelService;
		IFransCommandBidService commandBidService;
		IFransCommanderCoreService commanderCoreService;
		IFransGeneralService generalService;
		IFransStrategicMapService strategicMapService;
		IFransBaseBuilderService baseBuilderService;
		IFransExpansionStateService expansionStateService;
		IFransCaptureTransportService transportService;
		IFransGroundTransferService groundTransferService;
		IFransSupportCoordinatorService supportCoordinatorService;
		int nextNukeStageLogTick;

		int scanTicks;
		uint activeTargetActorId;
		uint combinedSecureHoldTargetActorId;
		int combinedSecureHoldUntilTick = -1;
		CPos activeObjective;
		FransCommanderOrder activeOrder = FransCommanderOrder.Move;
		FransMissionType activeMissionType = FransMissionType.Recon;
		int activeOrderStartedWorldTick;
		int lostContactSinceWorldTick = -1;
		readonly FransSearchSpiral reconSearchSpiral = new();
		readonly FransSearchSpiral raidSearchSpiral = new();
		Actor reconActor;
		CPos reconOrigin;
		CPos reconStart;
		CPos reconSearchWaypoint;
		bool hasReconSearchWaypoint;
		bool reconPioneerValidationActive;
		const int PioneerReconNoProgressTimeoutTicks = 750;
		int reconPioneerBestDistanceSquared = int.MaxValue;
		int reconPioneerLastProgressWorldTick = -1;
		int raidSearchStartedWorldTick = -1;
		CPos raidSearchWaypoint;
		bool hasRaidSearchWaypoint;
		readonly HashSet<uint> reconLoggedContactIds = [];
		Actor reconRetreatActor;
		CPos reconRetreatOrigin;
		bool hasLastSafeMoveAnchor;
		CPos lastSafeMoveAnchor;
		bool hasMissionAnchorPoint;
		CPos missionAnchorPoint;
		bool hasGroupMovePlanAttempt;
		bool groupMovePlanValid;
		CPos groupMovePlanObjective;
		CPos groupMovePlanDestination;
		int nextGroupMovePlanTick;
		bool retreatRecoveryActive;
		bool retreatRecoveryAllowsReinforcements = true;
		CPos retreatAnchorPoint;
		int retreatBaselineCombatValue;
		int retreatStartedWorldTick = -1;
		bool raidStrikeIssued;
		readonly HashSet<uint> raidKnownAdditionalDefenseIds = [];
		readonly Dictionary<uint, int> raidCommittedContributionByActor = [];
		readonly HashSet<uint> raidProgressiveAttackActorIds = [];
		bool raidFeasibilityRecheckRequested;
		int raidDefenseObservedWorldTick = -1;
		int raidLastValidatedSurvivorCount = -1;
		bool raidLocalDefenseActive;
		bool secureInitialAssemblyActive;
		int secureInitialAssemblyStartedTick = -1;
		int secureStaticClearSinceWorldTick = -1;
		int secureMarchBestDistanceSquared = int.MaxValue;
		int secureMarchLastProgressWorldTick = -1;
		CPos? secureRememberedObjective;
		uint secureStaticValidationTargetActorId;
		int secureStaticValidationCombatSnapshotWorldTick = -1;
		int secureStaticValidationRequiredContribution;
		int secureStaticValidationKnownThreat;
		string lastDefendBidDiagnosticSignature;

		public FransGroundCommanderBotModule(Actor self, FransGroundCommanderBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		protected override void Created(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;

			combatIntelService = self.Owner.PlayerActor.TraitsImplementing<IFransCombatIntelService>().FirstOrDefault()
				?? throw new InvalidOperationException("Ground Commander requires FransCombatIntelBotModule.");
			riskModelService = self.Owner.PlayerActor.TraitsImplementing<IFransRiskModelService>().FirstOrDefault()
				?? throw new InvalidOperationException("Ground Commander requires FransRiskModelBotModule.");
			commandBidService = self.Owner.PlayerActor.TraitsImplementing<IFransCommandBidService>().FirstOrDefault()
				?? throw new InvalidOperationException("Ground Commander requires FransCommandBidBotModule.");
			commanderCoreService = self.Owner.PlayerActor.TraitsImplementing<IFransCommanderCoreService>().FirstOrDefault()
				?? throw new InvalidOperationException("Ground Commander requires FransCommanderCoreBotModule.");
			generalService = self.Owner.PlayerActor.TraitsImplementing<IFransGeneralService>().FirstOrDefault()
				?? throw new InvalidOperationException("Ground Commander requires FransGeneralBotModule.");
			strategicMapService = self.Owner.PlayerActor.TraitsImplementing<IFransStrategicMapService>().FirstOrDefault()
				?? throw new InvalidOperationException("Ground Commander requires FransStrategicMapBotModule.");
			baseBuilderService = self.Owner.PlayerActor.TraitsImplementing<IFransBaseBuilderService>().FirstOrDefault()
				?? throw new InvalidOperationException("Ground Commander requires FransBaseBuilderBotModule.");
			expansionStateService = self.Owner.PlayerActor.TraitsImplementing<IFransExpansionStateService>().FirstOrDefault();
			resourceLayer = world.WorldActor.TraitOrDefault<IResourceLayer>();
			transportService = self.Owner.PlayerActor.TraitsImplementing<IFransCaptureTransportService>().FirstOrDefault();
			groundTransferService = self.Owner.PlayerActor.TraitsImplementing<IFransGroundTransferService>().FirstOrDefault();
			supportCoordinatorService = self.Owner.PlayerActor.TraitsImplementing<IFransSupportCoordinatorService>().FirstOrDefault();
		}

		protected override void TraitEnabled(Actor self)
		{
			// Spread the ten Ground capacities evenly across the configured scan cycle.
			// With ScanInterval 50 this produces one Ground Commander pass every 5 WT instead of
			// ten expensive mission/bid passes landing on the same tick.
			var basePhase = (int)((self.ActorID + 5u) % (uint)Info.ScanInterval);
			var commanderPhase = Info.CommanderIndex * Info.ScanInterval / 10;
			scanTicks = (basePhase + commanderPhase) % Info.ScanInterval + 1;
			hasLastSafeMoveAnchor = false;
			hasMissionAnchorPoint = false;
			missionAnchorPoint = default;
			hasGroupMovePlanAttempt = false;
			groupMovePlanValid = false;
			nextGroupMovePlanTick = 0;
			retreatRecoveryActive = false;
			retreatRecoveryAllowsReinforcements = true;
			anchorStandbySlots.Clear();
			groundStagingReservationCells.Clear();
			groundStagingReservationTick = int.MinValue;
			hasAnchorStandbyCenter = false;
			anchorStandbyCenter = default;
			retreatAnchorPoint = default;
			retreatBaselineCombatValue = 0;
			retreatStartedWorldTick = -1;
			ResetActiveMission();
			FransBotLog.BotDebug(world,
				"{0}: Ground Commander objective-sized SECURE/DEFEND model active for capacity {1} (index {2}). Ground SECURE concentrates into at most {3} active/fresh territorial mission(s) and requires max({4} minimum control value, known hostile tactical value x {5}% + {6} uncertainty), with quadratic surplus weight {7}. Before a distant SECURE march, {8}% of the committed force assembles within {9} cells of a force-aware ANCHOR selected from the exact committed snapshot, with a bounded {10}-WT timeout. Ground RAID is capped at {11} normally and {12} while SECURE is active, with a {13}% free-force operational package floor and {14}-unit minimum when available. DEFEND accepts observed danger directly and only strategic-critical DEFEND pressure globally preempts offense. Territorial SECURE bids are strictly same-landmass; GroundTransfer owns cross-water reinforcement, and a {15}-WT march no-progress watchdog releases stale SECURE ownership.",
				player, BidderKey, Info.CommanderIndex, Info.MaximumConcurrentSecureMissions, Info.SecureMinimumControlValue,
				Info.SecureKnownThreatMultiplierPercent, Info.SecureUncertaintyAllowanceValue, Info.SecureSurplusCostWeight,
				Info.SecurePreMoveAssemblyPercent, Info.SecurePreMoveAssemblyRadius, Info.SecurePreMoveAssemblyTimeout,
				Info.MaximumConcurrentGroundRaidMissions, Info.MaximumGroundRaidMissionsDuringSecure, Info.GroundRaidExpeditionarySharePercent, Info.GroundRaidMinimumUnitCount, Info.SecureMarchNoProgressTimeout);
		}

		protected override void TraitDisabled(Actor self)
		{
			anchorStandbySlots.Clear();
			groundStagingReservationCells.Clear();
			groundStagingReservationTick = int.MinValue;
			hasAnchorStandbyCenter = false;
			managedUnits.Clear();
			activeUnits.Clear();
			lastMoveDestination.Clear();
			lastMoveWorldTick.Clear();
			lastFightTarget.Clear();
			lastFightOrderWorldTick.Clear();
			mcvRightOfWayUnits.Clear();
			raidRecoveryOrigins.Clear();
			raidAttackMoveRecoveryActors.Clear();
			raidMissionOrigins.Clear();
			cohesionHeldUnits.Clear();
			cohesionFormationSlots.Clear();
			staleActorCacheKeys.Clear();
			hasCohesionFormationObjective = false;
			cohesionFormationObjective = default;
			lastMcvRightOfWayOrderTick.Clear();
			mcvRightOfWayCenter = null;
			mcvRightOfWayRadius = 0;
			nextMcvRightOfWayClearTick = 0;
			hasLastSafeMoveAnchor = false;
			hasMissionAnchorPoint = false;
			missionAnchorPoint = default;
			hasGroupMovePlanAttempt = false;
			groupMovePlanValid = false;
			nextGroupMovePlanTick = 0;
			retreatRecoveryActive = false;
			retreatRecoveryAllowsReinforcements = true;
			retreatAnchorPoint = default;
			retreatBaselineCombatValue = 0;
			retreatStartedWorldTick = -1;
			reconRetreatActor = null;
			reconRetreatOrigin = default;
			ResetReconState();
			commandBidService?.UpdateTransientActorReservations(FransCommanderKind.Ground, BidderKey, Array.Empty<uint>());
			ResetActiveMission();
		}

		void PruneDeadActorKeys<T>(Dictionary<Actor, T> map)
		{
			staleActorCacheKeys.Clear();
			foreach (var actor in map.Keys)
				if (actor == null || actor.IsDead)
					staleActorCacheKeys.Add(actor);

			foreach (var actor in staleActorCacheKeys)
				map.Remove(actor);
		}

		void PruneDeadActorOrderState()
		{
			PruneDeadActorKeys(lastMoveDestination);
			PruneDeadActorKeys(lastMoveWorldTick);
			PruneDeadActorKeys(lastFightTarget);
			PruneDeadActorKeys(lastFightOrderWorldTick);
			PruneDeadActorKeys(raidRecoveryOrigins);
			PruneDeadActorKeys(raidMissionOrigins);
			PruneDeadActorKeys(cohesionFormationSlots);
			PruneDeadActorKeys(lastMcvRightOfWayOrderTick);
			PruneDeadActorKeys(anchorStandbySlots);
			mcvRightOfWayUnits.RemoveWhere(a => a == null || a.IsDead);
			raidAttackMoveRecoveryActors.RemoveWhere(a => a == null || a.IsDead);
			cohesionHeldUnits.RemoveWhere(a => a == null || a.IsDead);
			staleActorCacheKeys.Clear();
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransGroundCommander.BotTick");
			if (player.WinState != WinState.Undefined)
				return;

			if (--scanTicks > 0)
				return;
			scanTicks = Info.ScanInterval;

			combatIntelService.EnsureCurrentSnapshot();
			PruneDeadActorOrderState();
			RefreshManagedUnits();
			MaintainReconRetreat(bot);
			MaintainRaidRecovery(bot);
			PublishTransientReservations();
			if (Info.CommanderIndex == 0)
				EnforceMcvDeployRightOfWay(bot);
			if (managedUnits.Count == 0)
			{
				if (commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.Ground, BidderKey,
					out _, out var emptyMission))
				{
					if (emptyMission.MissionType == FransMissionType.Recon)
					{
						commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, "RECON unit died; no managed Ground unit remains");
						FransBotLog.BotDebug(world,
							"{0}: Ground RECON MineCluster {1} lost its persistent scout; General keeps the target open for bounded rebid grace before slot rotation.",
							player, emptyMission.TargetActorId);
					}
					else if (emptyMission.MissionType == FransMissionType.Raid)
					{
						commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, "RAID force was wiped out");
					}
				}

				// a wiped Ground force ends the old RETREAT campaign completely.
				// Otherwise a zero baseline leaves recovery active and the first rebuilt unit
				// satisfies Math.Max(1, 0 * 75%), producing bogus 200/1-style recoveries.
				if (retreatRecoveryActive)
					FransBotLog.BotDebug(world,
						"{0}: Ground Commander RETREAT force was wiped out; closing the old regroup campaign so the next rebuilt army starts with a fresh combat-value baseline.",
						player);

				retreatRecoveryActive = false;
				retreatRecoveryAllowsReinforcements = true;
				retreatStartedWorldTick = -1;
				retreatAnchorPoint = default;
				retreatBaselineCombatValue = 0;
				ResetActiveMission();
				return;
			}

			// Resolve existing ownership before the collapse gate so only an accepted SECURE may
			// defer to ExecuteSecureMission. Stale local Secure/Fight state must not reach rebidding.
			var hasAcceptedMission = commandBidService.TryGetActiveMissionForBidder(
				FransCommanderKind.Ground, BidderKey, out var target, out var mission);
			var acceptedSecureOwnsFight = hasAcceptedMission &&
				activeMissionType == FransMissionType.Secure &&
				mission.MissionType == FransMissionType.Secure;

			// Check force collapse before asking the auction for a new mission. An accepted SECURE
			// performs its authoritative sufficiency/collapse checks in ExecuteSecureMission.
			if (!retreatRecoveryActive && activeOrder == FransCommanderOrder.Fight &&
				!acceptedSecureOwnsFight &&
				ShouldRetreatFromFight(out var collapsedFightValue))
			{
				BeginRetreat(bot, collapsedFightValue);
				return;
			}

			// ownership rule: RETREAT/recovery is committed survival work, not IDLE capacity.
			// DEFEND may recruit only IDLE capacity or preempt SECURE; it never interrupts recovery.
			if (retreatRecoveryActive)
			{
				ExecuteRetreatRecovery(bot);
				return;
			}

			// Accepted work normally owns its exact actor snapshot until mission end/RETREAT. DEFEND is
			// the deliberate strategic exception: strategic DEFEND pressure immediately releases SECURE
			// and RAID capacity so those actors can bid on base defense instead of finishing offensive work.
			if (hasAcceptedMission)
			{
				if (mission.MissionType == FransMissionType.Secure && commandBidService.ShouldPreemptSecureForDefend(FransCommanderKind.Ground, BidderKey, mission.LastVisibleTargetCell))
				{
					// Cancel the locally owned SECURE squad so the actors become available for strategic DEFEND.
					foreach (var unit in activeUnits.Where(a => a != null && a.IsInWorld && !a.IsDead).ToArray())
						unit.CancelActivity();
					commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, "SECURE preempted by active DEFEND pressure");
					FransBotLog.BotDebug(world,
						"{0}: Ground Commander {1} releases SECURE {2} because strategic DEFEND pressure reached the SECURE-preempt threshold; committed actors are freed for defense.",
						player, BidderKey, mission.TargetActorId);
					ResetActiveMission();
				}
				else if (mission.MissionType == FransMissionType.Raid && commandBidService.IsStrategicDefendPressureActive())
				{
					// A precision RAID is expendable strategic work. Under high-priority DEFEND pressure,
					// release its exact committed actors immediately instead of protecting an enemy HARV/building
					// while the home economy is under attack. RETREAT/recovery remains non-preemptible above.
					foreach (var unit in ResolveCommittedGroundActors(mission))
						unit.CancelActivity();
					commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, "RAID preempted by strategic DEFEND pressure");
					FransBotLog.BotDebug(world,
						"{0}: Ground Commander {1} releases RAID {2} because strategic DEFEND pressure is active; committed actors are freed for defense.",
						player, BidderKey, mission.TargetActorId);
					ResetActiveMission();
				}
				else
				{
					ExecuteMission(bot, target, mission);
					return;
				}
			}

			SubmitBids();
			if (commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.Ground, BidderKey,
				out target, out mission))
			{
				ExecuteMission(bot, target, mission);
				return;
			}

			if (activeMissionType == FransMissionType.Raid && activeTargetActorId != 0)
				StartRaidAttackMoveReturn(bot, "RAID mission disappeared / target completed");
			ResetActiveMission();
			if (Info.CommanderIndex == 0)
				ExecuteForwardMove(bot);
		}

		void PublishTransientReservations()
		{
			var ids = new HashSet<uint>();
			if (reconRetreatActor != null && reconRetreatActor.IsInWorld && !reconRetreatActor.IsDead)
				ids.Add(reconRetreatActor.ActorID);
			foreach (var actor in raidRecoveryOrigins.Keys)
				if (actor != null && actor.IsInWorld && !actor.IsDead)
					ids.Add(actor.ActorID);
			if (retreatRecoveryActive)
				foreach (var actor in activeUnits)
					if (actor != null && actor.IsInWorld && !actor.IsDead)
						ids.Add(actor.ActorID);
			commandBidService.UpdateTransientActorReservations(FransCommanderKind.Ground, BidderKey, ids);
		}

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			if (self == null || !managedUnits.Contains(self) || e.Attacker == null || IsNonCombatHusk(e.Attacker))
				return;

			var missionMember = activeUnits.Contains(self);
			if (!missionMember)
			{
				if (Info.CommanderIndex != 0)
					return;
				if (!commanderCoreService.IsActorAvailableForBidder(FransCommanderKind.Ground, BidderKey, self))
					return;
			}
			if (missionMember && activeMissionType == FransMissionType.Recon &&
				(activeOrder == FransCommanderOrder.Move || activeOrder == FransCommanderOrder.Search) && IsEnemyActor(e.Attacker))
			{
				// Being hit is itself fair information. RECON retreats without requiring LOS to or
				// using the position of a possibly hidden attacker.
				BeginReconRetreat(bot, self, "recon unit received hostile damage");
				return;
			}

			if (!IsVisibleEnemy(e.Attacker))
				return;

			if (missionMember && activeMissionType == FransMissionType.Raid)
			{
				var expected = commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.Ground, BidderKey, out _, out var raidMission) &&
					commanderCoreService.IsExpectedRaidContact(raidMission, e.Attacker);
				if (!expected)
				{
					if (raidKnownAdditionalDefenseIds.Add(e.Attacker.ActorID))
					{
						raidFeasibilityRecheckRequested = true;
						raidDefenseObservedWorldTick = Math.Max(raidDefenseObservedWorldTick, world.WorldTick);
						FransBotLog.BotDebug(world,
							"{0}: Ground RAID observes NEW defense {1} {2} after assignment because it attacked {3} {4}; mission ownership is preserved and Ground queues local feasibility revalidation instead of automatic RETREAT.",
							player, e.Attacker.Info.Name, e.Attacker.ActorID, self.Info.Name, self.ActorID);
					}
					else if (!raidFeasibilityRecheckRequested)
						raidLocalDefenseActive = true;
				}

				// The immutable RAID target never changes. A genuinely new attacker first goes
				// through fair-intel contribution/route revalidation; after PASS only those
				// validated local defenders may be fought temporarily before the original RAID resumes.
				return;
			}

			if (missionMember && activeOrder == FransCommanderOrder.Move)
			{
				BeginFight();
				FransBotLog.BotDebug(world,
					"{0}: Ground Commander MOVE -> FIGHT because {1} was attacked by visible {2} {3}; RiskModel is ignored from this point until the fight ends. Pre-fight combat value {4}, fallback {5}.",
					player, self, e.Attacker.Info.Name, e.Attacker.ActorID, retreatBaselineCombatValue, retreatAnchorPoint);
			}
			// damage callbacks may arrive every WT from several attackers. Once this actor
			// has received a local FIGHT order, do not switch targets again inside one Commander scan
			// interval. The normal FIGHT micro still refreshes/choses targets after that.
			if (lastFightOrderWorldTick.TryGetValue(self, out var recentFightOrder) &&
				world.WorldTick - recentFightOrder < Info.ScanInterval)
				return;

			else if (!missionMember)
				FransBotLog.BotDebug(world,
					"{0}: Ground Commander authorizes immediate local FIGHT for forward-moving {1} after visible {2} {3} attacks it; the shared auction will classify/dispatch the continuing mission.",
					player, self, e.Attacker.Info.Name, e.Attacker.ActorID);

			if (CanAttackActor(self, e.Attacker))
			{
				// Same-target refresh remains separately bounded by FightRefreshInterval.
				if (lastFightTarget.TryGetValue(self, out var oldTarget) && oldTarget == e.Attacker.ActorID &&
					lastFightOrderWorldTick.TryGetValue(self, out var last) && world.WorldTick - last < Info.FightRefreshInterval)
					return;

				bot.QueueOrder(new Order("Attack", self, Target.FromActor(e.Attacker), false));
				lastFightTarget[self] = e.Attacker.ActorID;
				lastFightOrderWorldTick[self] = world.WorldTick;
			}
		}

		bool IFransGroundCommanderService.TryGetGroundDemandPoint(out CPos objective, out FransCommanderOrder order, out int startedWorldTick)
		{
			if (retreatRecoveryActive)
			{
				objective = retreatAnchorPoint;
				order = FransCommanderOrder.Retreat;
				startedWorldTick = retreatStartedWorldTick;
				return true;
			}

			if (activeUnits.Count > 0)
			{
				objective = activeObjective;
				order = activeOrder;
				startedWorldTick = activeOrderStartedWorldTick;
				return true;
			}

			if (TryGetForwardObjective(out objective))
			{
				order = FransCommanderOrder.Move;
				startedWorldTick = world.WorldTick;
				return true;
			}

			objective = default;
			order = FransCommanderOrder.Move;
			startedWorldTick = -1;
			return false;
		}

		IReadOnlyList<CPos> IFransGroundCommanderService.GetGroundRegroupPoints()
		{
			var points = new List<CPos>(4);
			void AddPoint(CPos point)
			{
				if (!points.Contains(point))
					points.Add(point);
			}

			if (retreatRecoveryActive)
				AddPoint(retreatAnchorPoint);
			if (generalService.TryGetLatestGroundAnchor(out var latestGroundAnchor))
				AddPoint(latestGroundAnchor);
			if (hasLastSafeMoveAnchor)
				AddPoint(lastSafeMoveAnchor);

			return points;
		}

		bool IFransGroundCommanderService.IsGroundCombatUnitOwned(Actor actor) => IsManagedGroundCombatUnit(actor);

		bool IFransGroundCommanderService.IsGroundCombatActorType(string actorType) => IsManagedGroundCombatActorType(actorType);

		bool IFransGroundCommanderService.IsGroundVehicleCombatUnitOwned(Actor actor) =>
			IsManagedGroundCombatUnit(actor) && !IsGroundInfantryActor(actor);

		bool IFransGroundCommanderService.IsGroundCombatUnitMissionCommitted(Actor actor) =>
			actor != null && (activeUnits.Contains(actor) || raidRecoveryOrigins.ContainsKey(actor) || actor == reconRetreatActor);

		bool IFransGroundUnitReservationService.IsGroundUnitReserved(Actor actor) => IsManagedGroundCombatUnit(actor);

		void RefreshManagedUnits()
		{
			using var fransPerf = FransBotLog.Profile(world, player, "Ground.RefreshManagedUnits");
			// CommanderCore owns the shared fair-snapshot candidate roster and ActorID index. Each
			// Ground capacity keeps only its cheap configuration-specific filter plus the two live
			// logistics reservations that can change between sensor snapshots. Capture specialist
			// actor types are already excluded by ExcludedGroundTypes, so the old per-actor scan across
			// every SpecOps capacity was redundant. Reuse this HashSet instead of allocating a temporary
			// set + UnionWith on every staggered capacity pass.
			managedUnits.Clear();
			foreach (var actor in commanderCoreService.GetSharedGroundCombatRoster())
			{
				// The shared roster is bounded by the CombatIntel sensor interval. An actor may die after
				// the shared snapshot was built, so revalidate liveness at the capacity boundary.
				if (IsLiveActor(actor) && IsManagedGroundCombatActorType(actor.Info.Name) && !IsGroundLogisticsReserved(actor))
					managedUnits.Add(actor);
			}

			activeUnits.RemoveWhere(a => !managedUnits.Contains(a));
		}

		bool IsGroundLogisticsReserved(Actor actor)
		{
			return (transportService != null && transportService.IsTransportReserved(actor)) ||
				(groundTransferService != null && groundTransferService.IsGroundUnitTransferReserved(actor));
		}

		bool TryResolveManagedActor(uint actorId, out Actor actor)
		{
			actor = null;
			if (!commanderCoreService.TryGetSharedGroundCombatActor(actorId, out var sharedActor) ||
				!IsLiveActor(sharedActor) || !managedUnits.Contains(sharedActor))
				return false;

			actor = sharedActor;
			return true;
		}

		bool IsManagedGroundCombatUnit(Actor actor)
		{
			return actor != null && actor.IsInWorld && !actor.IsDead && actor.Owner == player && actor.OccupiesSpace != null &&
				IsManagedGroundCombatActorType(actor.Info.Name) && actor.TraitOrDefault<Aircraft>() == null;
		}

		bool IsManagedGroundCombatActorType(string actorType)
		{
			if (string.IsNullOrEmpty(actorType))
				return false;

			if (managedGroundActorTypeCache.TryGetValue(actorType, out var cached))
				return cached;

			var managed = world.Map.Rules.Actors.TryGetValue(actorType, out var actorInfo) &&
				actorInfo.HasTraitInfo<AttackBaseInfo>() && actorInfo.HasTraitInfo<MobileInfo>() && !actorInfo.HasTraitInfo<AircraftInfo>() &&
				!Info.ExcludedGroundTypes.Contains(actorType) && !Info.AirTypes.Contains(actorType) && !Info.NavalTypes.Contains(actorType);
			managedGroundActorTypeCache[actorType] = managed;
			return managed;
		}

		bool IsGroundRaidEligibleActor(Actor actor)
		{
			if (!IsManagedGroundCombatUnit(actor) || Info.RaidExcludedInfantryTypes.Contains(actor.Info.Name))
				return false;

			var mobile = actor.TraitOrDefault<Mobile>();
			return mobile != null && mobile.Info.Speed >= Info.RaidMinimumVehicleSpeed;
		}

		bool IsGroundInfantryActor(Actor actor) => actor != null && Info.RaidExcludedInfantryTypes.Contains(actor.Info.Name);

		bool IsRaidStaticDefenseBreaker(Actor actor) =>
			actor != null && Info.RaidStaticDefenseBreakerTypes.Contains(actor.Info.Name.ToLowerInvariant());

		bool IsRaidAlwaysAllowedStaticDefenseType(string actorType) =>
			!string.IsNullOrEmpty(actorType) && Info.RaidStaticDefenseAlwaysAllowedTypes.Contains(actorType.ToLowerInvariant());

		bool IsRestrictedGroundStaticDefense(Actor actor)
		{
			if (actor == null || IsRaidAlwaysAllowedStaticDefenseType(actor.Info.Name))
				return false;
			if (combatIntelService.TryGetEnemyCombatContact(actor.ActorID, out var contact))
				return contact.IsBuilding && contact.IsDefensiveBuilding;
			return actor.Info.HasTraitInfo<BuildingInfo>() && actor.Info.HasTraitInfo<AttackBaseInfo>();
		}

		bool IsGroundRaidCellClearOfRestrictedStaticDefense(Actor unit, CPos cell, uint targetActorId = 0)
		{
			if (IsRaidStaticDefenseBreaker(unit))
				return true;
			var radiusSq = Info.RaidStaticDefenseAvoidanceRadius * Info.RaidStaticDefenseAvoidanceRadius;
			return !combatIntelService.EnemyCombatContacts.Any(c =>
				c.ActorId != targetActorId &&
				c.IsBuilding && c.IsDefensiveBuilding &&
				!IsRaidAlwaysAllowedStaticDefenseType(c.ActorType) &&
				c.Owner != null && PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(c.Owner)) &&
				(c.LastSeenCell - cell).LengthSquared <= radiusSq);
		}

		bool CanGroundRaidActorEngageTarget(Actor actor, Actor target)
		{
			if (actor == null || target == null)
				return false;
			if (IsRestrictedGroundStaticDefense(target) && !IsRaidStaticDefenseBreaker(actor))
				return false;
			return CanAttackActor(actor, target);
		}

		bool IsGroundReconEligibleActor(Actor actor) => actor != null && IsManagedGroundCombatUnit(actor) && Info.ReconEligibleGroundTypes.Contains(actor.Info.Name);

		bool IsGroundRaidEligibleTarget(FransMission mission)
		{
			return mission.IsBuilding || Info.RaidEligibleMobileTargetTypes.Contains(mission.TargetActorType);
		}

		bool IsGroundRaidEligibleTarget(FransActiveMission mission)
		{
			return mission.TargetIsBuilding || Info.RaidEligibleMobileTargetTypes.Contains(mission.TargetActorType);
		}

		void EnforceMcvDeployRightOfWay(IBot bot)
		{
			mcvRightOfWayUnits.Clear();
			lastMcvRightOfWayOrderTick.Keys.Where(a => !managedUnits.Contains(a)).ToList()
				.ForEach(a => lastMcvRightOfWayOrderTick.Remove(a));

			if (expansionStateService == null ||
				!expansionStateService.TryGetMcvDeployRightOfWay(out var center, out var radius) || radius <= 0)
			{
				mcvRightOfWayCenter = null;
				mcvRightOfWayRadius = 0;
				nextMcvRightOfWayClearTick = 0;
				lastMcvRightOfWayOrderTick.Clear();
				return;
			}

			// A new deploy cell starts a new right-of-way episode. Old retry timestamps
			// must not suppress the first clear order at the next MCV site.
			if (!mcvRightOfWayCenter.HasValue || mcvRightOfWayCenter.Value != center || mcvRightOfWayRadius != radius)
			{
				mcvRightOfWayCenter = center;
				mcvRightOfWayRadius = radius;
				nextMcvRightOfWayClearTick = 0;
				lastMcvRightOfWayOrderTick.Clear();
			}

			var radiusSq = radius * radius;
			var blockers = managedUnits
				.Where(IsLiveActor)
				.Where(a => (a.Location - center).LengthSquared <= radiusSq)
				.OrderBy(a => (a.Location - center).LengthSquared)
				.ThenBy(a => a.ActorID)
				.ToArray();
			foreach (var blocker in blockers)
				mcvRightOfWayUnits.Add(blocker);

			// performance guard: the cheap ownership set above still refreshes
			// every normal Ground scan, so conflicting combat orders remain suppressed.
			// Expensive exit-cell/RiskModel work runs at most once per 125 WT; the same
			// blocker is retried only after 500 WT; spreads new path/order work over
			// the configured small per-pass budget instead of routing a 12-unit burst at once.
			if (blockers.Length == 0 || world.WorldTick < nextMcvRightOfWayClearTick)
				return;
			nextMcvRightOfWayClearTick = world.WorldTick + Math.Max(125, Info.ScanInterval * 5);

			var exitRing = world.Map.FindTilesInAnnulus(center, radius + 2, radius + 7)
				.Where(world.Map.Contains)
				.ToArray();
			var moved = 0;
			foreach (var blocker in blockers)
			{
				if (moved >= Info.McvRightOfWayMaximumOrdersPerPass)
					break;

				if (lastMcvRightOfWayOrderTick.TryGetValue(blocker, out var last) &&
					world.WorldTick - last < 500)
					continue;

				var mobile = blocker.TraitOrDefault<Mobile>();
				if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused)
					continue;

				var destination = exitRing
					.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
					.OrderBy(c => (c - blocker.Location).LengthSquared)
					.ThenByDescending(c => (c - center).LengthSquared)
					.ThenBy(c => c.X)
					.ThenBy(c => c.Y)
					.Take(24)
					.Select(c => (Cell: c, Risk: riskModelService.EvaluateCell(blocker, c, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced)))
					.Where(x => !x.Risk.IsCritical)
					.OrderBy(x => x.Risk.Score)
					.ThenBy(x => (x.Cell - blocker.Location).LengthSquared)
					.ThenByDescending(x => (x.Cell - center).LengthSquared)
					.ThenBy(x => x.Cell.X)
					.ThenBy(x => x.Cell.Y)
					.Select(x => (CPos?)x.Cell)
					.FirstOrDefault();
				if (!destination.HasValue)
					continue;

				bot.QueueOrder(new Order("Move", blocker, Target.FromCell(world, destination.Value), false));
				lastMcvRightOfWayOrderTick[blocker] = world.WorldTick;
				moved++;
			}

			if (moved > 0)
				FransBotLog.BotDebug(world,
					"{0}: Ground Commander bounded right-of-way pass clears {1} NEW/retry combat unit(s) from MCV deploy zone around {2} (radius {3}); ownership suppression stays active for every blocker while expensive reroutes are capped to {4} per 125 WT and 500 WT per actor.",
					player, moved, center, radius, Info.McvRightOfWayMaximumOrdersPerPass);
		}

		static int GetRaidTargetPriorityRank(string actorType) => actorType?.ToLowerInvariant() switch
		{
			// Ground is the dedicated air-defense breaker: known SAM/AA structures always occupy
			// the top RAID priority band so Ground can open safe corridors for Air Commander.
			"sam" => 0,
			"agun" => 0,
			"harv" => 1,
			"fact" => 2,
			"proc" => 50,
			_ => 20
		};

		static int ApplyRaidTargetPriorityToPrice(int basePrice, string actorType)
		{
			if (basePrice == int.MaxValue)
				return int.MaxValue;
			const int PriorityBandCost = 1000000;
			var ranked = (long)GetRaidTargetPriorityRank(actorType) * PriorityBandCost + Math.Max(1, basePrice);
			return (int)Math.Min(int.MaxValue - 1L, ranked);
		}

		bool TryBuildGroundRaidBid(FransMission mission, IReadOnlyList<Actor> availableMissionUnits, out FransCommanderBidReport report)
		{
			using var fransPerf = FransBotLog.Profile(world, player, "Ground.TryBuildRaidBid");
			report = default;
			if (mission.Type != FransMissionType.Raid || !IsGroundRaidEligibleTarget(mission))
				return false;

			var target = mission.Target;
			// A new RAID bid requires the fair visible target snapshot. Once the MISSION starts, bounded
			// General memory may keep the mission alive, but hidden live HP is never re-read.
			if (mission.IsRememberedIntel || target == null || !IsVisibleEnemy(target))
				return false;

			var required = commanderCoreService.GetMissionRequiredContribution(FransCommanderKind.Ground, mission);
			if (required == int.MaxValue)
				return false;

			var ranked = (availableMissionUnits ?? Array.Empty<Actor>())
				.Where(IsGroundRaidEligibleActor)
				.Where(a => !mcvRightOfWayUnits.Contains(a) && a != reconRetreatActor && !raidRecoveryOrigins.ContainsKey(a) && a.TraitOrDefault<Cargo>() == null && CanGroundRaidActorEngageTarget(a, target))
				.Select(a =>
				{
					var destination = FindGroundRaidApproachCell(a, target);
					if (!destination.HasValue)
						return (Actor: a, Destination: (CPos?)null, Eta: int.MaxValue, Contribution: 0, Price: int.MaxValue, Route: default(FransRouteRiskAssessment), Cost: 0);
					var route = EvaluateMoveRisk(a, a.Location, destination.Value);
					var eta = commanderCoreService.EstimateMoveEtaTicks(a, destination.Value);
					var contribution = commanderCoreService.EstimateRaidContribution(FransCommanderKind.Ground, a, target);
					var price = commanderCoreService.PriceBid(FransCommanderKind.Ground, route.PeakScore, eta, GetCombatValue(a));
					return (Actor: a, Destination: destination, Eta: eta, Contribution: contribution, Price: price, Route: route, Cost: GetCombatValue(a));
				})
				.Where(x => x.Destination.HasValue && x.Eta != int.MaxValue && x.Contribution > 0 && x.Price != int.MaxValue && !x.Route.IsCritical)
				.OrderBy(x => x.Price).ThenBy(x => x.Eta).ThenByDescending(x => x.Cost).ThenBy(x => x.Actor.ActorID)
				.Take(Info.MaximumRaidUnitsPerMission)
				.ToArray();
			if (ranked.Length == 0)
				return false;

			var availableRaidCombatValue = ranked.Sum(x => Math.Max(1, x.Cost));
			var raidOperationalFloor = Math.Max(1, availableRaidCombatValue * Info.GroundRaidExpeditionarySharePercent / 100);
			var raidMinimumCount = Math.Min(Info.GroundRaidMinimumUnitCount, ranked.Length);

			var chosen = new List<Actor>();
			var offered = 0;
			var slowestEta = 0;
			var peakRisk = 0;
			var travel = 0;
			var totalCost = 0;
			foreach (var x in ranked)
			{
				chosen.Add(x.Actor);
				offered = (int)Math.Min(int.MaxValue, (long)offered + x.Contribution);
				slowestEta = Math.Max(slowestEta, x.Eta);
				peakRisk = Math.Max(peakRisk, x.Route.PeakScore);
				travel = Math.Max(travel, Math.Abs(x.Destination.Value.X - x.Actor.Location.X) + Math.Abs(x.Destination.Value.Y - x.Actor.Location.Y));
				totalCost += x.Cost;
				if (offered >= required && chosen.Count >= raidMinimumCount && totalCost >= raidOperationalFloor)
					break;
			}
			if (offered < required || chosen.Count < raidMinimumCount || totalCost < raidOperationalFloor)
				return false;

			var groupPrice = commanderCoreService.PriceBid(FransCommanderKind.Ground, peakRisk, slowestEta, totalCost);
			if (groupPrice == int.MaxValue)
				return false;
			groupPrice = ApplyRaidTargetPriorityToPrice(groupPrice, mission.TargetActorType);
			report = new FransCommanderBidReport(
				FransCommanderKind.Ground, BidderKey, chosen[0].ActorID, chosen.Select(a => a.ActorID).ToArray(),
				groupPrice, peakRisk, travel, totalCost, slowestEta, offered, required, false);
			return true;
		}

		SharedSecureBidMemoState GetSharedSecureBidMemoState()
		{
			var state = SharedSecureBidMemos.GetValue(player, _ => new SharedSecureBidMemoState());

			var snapshotTick = combatIntelService.SnapshotWorldTick;
			var riskRevision = riskModelService.RiskRevision;
			// Never carry path/occupancy feasibility across simulation ticks. This keeps the
			// memo strictly semantics-preserving: only capacities evaluating the same world
			// state may share the expensive SECURE path analysis.
			if (state.WorldTick != world.WorldTick || state.CombatIntelSnapshotWorldTick != snapshotTick || state.RiskRevision != riskRevision)
			{
				state.WorldTick = world.WorldTick;
				state.CombatIntelSnapshotWorldTick = snapshotTick;
				state.RiskRevision = riskRevision;
				state.Entries.Clear();
			}

			return state;
		}

		static string BuildSecureBidMemoKey(uint targetActorId, CPos targetCell, IReadOnlyList<Actor> actors)
		{
			return targetActorId + ":" + targetCell.X + "," + targetCell.Y + ":" +
				string.Join(";", actors.Select(a => a.ActorID + "@" + a.Location.X + "," + a.Location.Y));
		}

		bool TryGetOrBuildSecureBidPathMemo(uint targetActorId, CPos targetCell, IReadOnlyList<Actor> chosen,
			out SecureBidPathMemo memo)
		{
			memo = default;
			if (chosen == null || chosen.Count == 0)
				return false;

			var state = GetSharedSecureBidMemoState();
			var key = BuildSecureBidMemoKey(targetActorId, targetCell, chosen);
			if (state.Entries.TryGetValue(key, out memo))
				return memo.Feasible;

			using var perf = FransBotLog.Profile(world, player, "Ground.SecureSharedAnalysis");
			var subject = chosen[0];
			// LANDMASS-SAFE SECURE: strategic reachability is authoritative. A failed Ground
			// sector route must never fall back to a straight-line RiskModel estimate because that
			// can price an impossible cross-water march as feasible. GroundTransfer owns all
			// cross-landmass movement.
			if (!strategicMapService.TryGetGroundLandmassId(subject.Location, out var sourceLandmass) ||
				!strategicMapService.TryGetGroundLandmassId(targetCell, out var targetLandmass) ||
				sourceLandmass != targetLandmass ||
				!strategicMapService.TryGetStrategicSectorRoute(subject.Location, targetCell, FransStrategicMovementLayer.Ground,
					FransStrategicRoutePolicy.Safe, out var secureRoute) || secureRoute == null || secureRoute.Count == 0)
			{
				memo = new SecureBidPathMemo(false, int.MaxValue, int.MaxValue, 0, 0, int.MaxValue);
				state.Entries[key] = memo;
				return false;
			}

			var route = riskModelService.EvaluateRoute(subject, secureRoute, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced);
			if (route.IsCritical)
			{
				memo = new SecureBidPathMemo(false, route.PeakScore, int.MaxValue, 0, 0, int.MaxValue);
				state.Entries[key] = memo;
				return false;
			}

			var eta = commanderCoreService.EstimateMoveEtaTicks(subject, targetCell);
			if (eta == int.MaxValue)
			{
				memo = new SecureBidPathMemo(false, route.PeakScore, eta, 0, 0, int.MaxValue);
				state.Entries[key] = memo;
				return false;
			}

			var travelCells = Math.Abs(targetCell.X - subject.Location.X) + Math.Abs(targetCell.Y - subject.Location.Y);
			var force = GetGroundTacticalGroupValue(chosen);
			var price = commanderCoreService.PriceBid(FransCommanderKind.Ground, route.PeakScore, eta, force);
			memo = new SecureBidPathMemo(price != int.MaxValue, route.PeakScore, eta, travelCells, force, price);
			state.Entries[key] = memo;
			return memo.Feasible;
		}

		bool IsPioneerExpansionSecure(CPos targetCell)
		{
			var objectives = expansionStateService?.SecureRequiredExpansionObjectives;
			if (objectives == null || objectives.Count == 0)
				return false;

			var radiusSq = Info.PioneerSecureObjectiveMatchRadius * Info.PioneerSecureObjectiveMatchRadius;
			return objectives.Any(objective => (objective - targetCell).LengthSquared <= radiusSq);
		}

		int GetSecurePackageRequirement(FransSiteIntel siteIntel, out int knownThreat, out int uncertainty)
		{
			var contributionMission = new FransMission(
				null, 0, null, null, siteIntel.Center, false, false, siteIntel,
				FransMissionType.Secure, 0, world.WorldTick);
			knownThreat = commanderCoreService.GetMissionRequiredContribution(FransCommanderKind.Ground, contributionMission);
			uncertainty = Info.SecureUncertaintyAllowanceValue;
			var threatRequirement = ((long)knownThreat * Info.SecureKnownThreatMultiplierPercent + 99L) / 100L;
			return (int)Math.Clamp(Math.Max((long)Info.SecureMinimumControlValue, threatRequirement + uncertainty), 1L, int.MaxValue);
		}

		int GetSecureSurplusCost(int selectedValue, int requiredValue)
		{
			var surplus = Math.Max(0, selectedValue - requiredValue);
			if (surplus == 0 || Info.SecureSurplusCostWeight == 0)
				return 0;
			var surplusPercent = ((long)surplus * 100L + requiredValue - 1L) / Math.Max(1, requiredValue);
			return (int)Math.Clamp(surplusPercent * surplusPercent * Info.SecureSurplusCostWeight / 100L, 0L, int.MaxValue);
		}

		int AddSecureSurplusCost(int basePrice, int selectedValue, int requiredValue)
		{
			if (basePrice == int.MaxValue)
				return basePrice;
			return (int)Math.Min(int.MaxValue - 1L, (long)basePrice + GetSecureSurplusCost(selectedValue, requiredValue));
		}

		void AddGroundTacticalActor(Actor actor, ref long infantryValue, ref int infantryCount, ref long otherValue)
		{
			if (actor == null || !actor.IsInWorld || actor.IsDead)
				return;
			var value = GetCombatValue(actor);
			if (IsGroundInfantryActor(actor))
			{
				infantryCount++;
				infantryValue += value;
			}
			else
				otherValue += value;
		}

		int GetGroundTacticalGroupValue(long infantryValue, int infantryCount, long otherValue)
		{
			if (infantryCount >= Math.Max(2, Info.InfantrySquadValueMinimumCount) && infantryValue > 0)
				infantryValue = infantryValue * Math.Max(100, Info.InfantrySquadValuePercent) / 100;
			return (int)Math.Clamp(infantryValue + otherValue, 0L, int.MaxValue);
		}

		void LogPioneerSecureNoBid(FransMission mission, CPos targetCell, string reason)
		{
			if (!IsPioneerExpansionSecure(targetCell))
				return;
			if (pioneerSecureNoBidDiagnosticNextTick.TryGetValue(mission.TargetActorId, out var nextTick) && world.WorldTick < nextTick)
				return;
			pioneerSecureNoBidDiagnosticNextTick[mission.TargetActorId] = world.WorldTick + 500;
			FransBotLog.BotDebug(world,
				"{0}: PIONEER SECURE NO-BID diagnostic capacity {1}, mission {2} at {3}: {4}.",
				player, BidderKey, mission.TargetActorId, targetCell, reason);
		}

		void SubmitBids()
		{
			using var fransPerf = FransBotLog.Profile(world, player, "Ground.SubmitBids");
			generalService.EnsureCurrentMissions();
			var missions = generalService.CurrentMissions
				.Where(m => m.TargetActorType != FransGeneralBotModule.SeaTransportBeachSecureTargetType)
				.ToArray();
			var defendPressureActive = commandBidService.IsDefendPressureActive();
			var strategicDefendPressureActive = commandBidService.IsStrategicDefendPressureActive();
			var secureCommitments = commandBidService.GetActiveOrFreshPendingMissionCount(FransCommanderKind.Ground, FransMissionType.Secure);

			// each Ground capacity owns at most one pending RAID bid and deliberately fans
			// out across distinct raw opportunities. A fresh full Ground bid from another capacity
			// reserves that target for the current bid window, so the next staggered capacity moves to
			// the next feasible target while preserving the global Commander-owned priority bands:
			// SAM/AA first, then HARV, FACT, then other buildings, with PROC explicitly last. General remains target-neutral.
			commandBidService.ClearPendingMissionBids(FransCommanderKind.Ground, BidderKey, FransMissionType.Raid);

			// PERFORMANCE-ONLY: late-game SECURE previously re-ran the full broker availability
			// scan for every actor in every mission. Build one actor snapshot for this capacity
			// and rebuild it only when CommandBid ownership/reservation state changes.
			Actor[] missionBidAvailableUnits = Array.Empty<Actor>();
			var missionBidAvailabilityRevision = int.MinValue;
			bool TryGetMissionBidAvailableUnits(out Actor[] available)
			{
				available = Array.Empty<Actor>();
				if (commandBidService.IsCapacityUnavailableForMissionBid(FransCommanderKind.Ground, BidderKey))
					return false;

				var revision = commandBidService.MissionBidAvailabilityRevision;
				if (revision != missionBidAvailabilityRevision)
				{
					using var availabilityPerf = FransBotLog.Profile(world, player, "Ground.AvailabilitySnapshot");
					missionBidAvailableUnits = managedUnits
						.Where(a => commanderCoreService.IsActorAvailableForMissionBid(FransCommanderKind.Ground, BidderKey, a))
						.ToArray();
					missionBidAvailabilityRevision = commandBidService.MissionBidAvailabilityRevision;
				}

				available = missionBidAvailableUnits;
				return available.Length > 0;
			}

			if (!TryGetMissionBidAvailableUnits(out _))
				return;

			var raidCommitments = commandBidService.GetActiveOrFreshPendingMissionCount(FransCommanderKind.Ground, FransMissionType.Raid);
			var raidLimit = strategicDefendPressureActive
				? 0
				: defendPressureActive
					? Info.MaximumRaidMissionsDuringDefend
					: secureCommitments > 0 ? Info.MaximumGroundRaidMissionsDuringSecure : Info.MaximumConcurrentGroundRaidMissions;
			if (raidCommitments < raidLimit)
			{
				var raidGroups = missions
					.Where(m => m.Type == FransMissionType.Raid && IsGroundRaidEligibleTarget(m))
					.GroupBy(m => GetRaidTargetPriorityRank(m.TargetActorType))
					.OrderBy(g => g.Key);
				foreach (var priorityGroup in raidGroups)
				{
					var feasible = new List<(FransMission Mission, FransCommanderBidReport Report)>();
					foreach (var raidMission in priorityGroup.OrderBy(m => m.TargetActorId))
					{
						if (commandBidService.HasFreshPendingMissionBid(FransCommanderKind.Ground, FransMissionType.Raid, raidMission.TargetActorId, BidderKey))
							continue;
						if (!TryGetMissionBidAvailableUnits(out var raidAvailableUnits))
							return;
						if (TryBuildGroundRaidBid(raidMission, raidAvailableUnits, out var raidReport))
							feasible.Add((raidMission, raidReport));
					}

					if (feasible.Count == 0)
						continue;

					var bestRaid = feasible
						.OrderBy(x => x.Report.TotalCost)
						.ThenBy(x => x.Report.EstimatedEtaTicks)
						.ThenBy(x => x.Report.RouteRisk)
						.ThenBy(x => x.Mission.TargetActorId)
						.First();
					commandBidService.SubmitMissionBid(bestRaid.Mission, bestRaid.Report);
					if (commandBidService.IsCapacityUnavailableForMissionBid(FransCommanderKind.Ground, BidderKey))
						return;
					break;
				}
			}

			foreach (var mission in missions)
			{
				if (mission.Type == FransMissionType.Raid)
					continue;

				using var missionBidPerf = FransBotLog.Profile(world, player, mission.Type switch
				{
					FransMissionType.Recon => "Ground.ReconBid",
					FransMissionType.Secure => "Ground.SecureBid",
					FransMissionType.Defend => "Ground.DefendBid",
					_ => "Ground.OtherBid"
				});
				var target = mission.Target;
				var targetCell = mission.LastVisibleTargetCell;

				if (mission.Type == FransMissionType.Recon)
				{
					if (!TryGetMissionBidAvailableUnits(out var reconAvailableUnits))
						return;
					var pioneerRecon = false;
					var reconTargetCell = targetCell;
					if (expansionStateService != null && expansionStateService.TryGetPioneerReconObjectiveNear(targetCell, out var pioneerReconObjective))
					{
						pioneerRecon = true;
						reconTargetCell = pioneerReconObjective;
					}
					var best = reconAvailableUnits
						.Where(IsGroundReconEligibleActor)
						.Where(commanderCoreService.IsReconCandidateOperational)
						.Where(a => !mcvRightOfWayUnits.Contains(a) && a != reconRetreatActor && a.TraitOrDefault<Cargo>() == null)
						.Where(a => !ReconHealthBelowRetreatThreshold(a, out _))
						.Select(a =>
						{
							var destination = FindGroundReconCell(a, reconTargetCell, pioneerRecon);
							if (!destination.HasValue)
								return (Actor: a, Destination: (CPos?)null, Eta: int.MaxValue, Price: int.MaxValue, Vision: 0);
							var eta = commanderCoreService.EstimateReconEtaTicks(a, destination.Value);
							var price = commanderCoreService.PriceReconBid(FransCommanderKind.Ground, a, eta);
							return (Actor: a, Destination: destination, Eta: eta, Price: price, Vision: commanderCoreService.GetReconVisionCells(a));
						})
						.Where(x => x.Destination.HasValue && x.Eta != int.MaxValue && x.Price != int.MaxValue && x.Vision > 0)
						.OrderBy(x => x.Price).ThenBy(x => x.Eta).ThenBy(x => x.Actor.ActorID).FirstOrDefault();
					if (best.Actor == null)
						continue;
					var destination = best.Destination.Value;
					var travel = Math.Abs(destination.X - best.Actor.Location.X) + Math.Abs(destination.Y - best.Actor.Location.Y);
					commandBidService.SubmitMissionBid(mission, new FransCommanderBidReport(
						FransCommanderKind.Ground, BidderKey, best.Actor.ActorID, new[] { best.Actor.ActorID },
						best.Price, 0, travel, GetCombatValue(best.Actor), best.Eta, 1, 1, false));
					if (commandBidService.IsCapacityUnavailableForMissionBid(FransCommanderKind.Ground, BidderKey))
						return;
					continue;
				}

				if (mission.Type == FransMissionType.Secure &&
					commandBidService.ShouldPreemptSecureForDefend(FransCommanderKind.Ground, BidderKey, mission.LastVisibleTargetCell))
				{
					LogPioneerSecureNoBid(mission, targetCell, "strategic DEFEND preemption currently owns this Ground capacity");
					continue;
				}
				if (mission.Type == FransMissionType.Secure && secureCommitments >= Info.MaximumConcurrentSecureMissions)
				{
					LogPioneerSecureNoBid(mission, targetCell, $"Ground SECURE concurrency is full at {secureCommitments}/{Info.MaximumConcurrentSecureMissions}");
					continue;
				}


				if (!TryGetMissionBidAvailableUnits(out var normalAvailableUnits))
					return;
				var eligibleCandidates = normalAvailableUnits
					.Where(a => !mcvRightOfWayUnits.Contains(a) && a != reconRetreatActor && !raidRecoveryOrigins.ContainsKey(a))
					.Where(a => mission.Type == FransMissionType.Defend || target == null || CanAttackActor(a, target))
					.OrderBy(a => (a.Location - targetCell).LengthSquared).ThenBy(a => a.ActorID);
				var candidates = eligibleCandidates.ToArray();
				if (mission.Type == FransMissionType.Secure && mission.TargetActorType == FransGeneralBotModule.TransportLossSecureTargetType)
				{
					if (!TryGetTransportLossGroundObjective(mission.TargetActorId, mission.LastVisibleTargetCell, mission.SiteIntel, candidates, out targetCell, out var nativeLandmassId))
						continue;

					candidates = candidates
						.Where(a => strategicMapService.TryGetGroundLandmassId(a.Location, out var lm) && lm == nativeLandmassId)
						.OrderBy(a => (a.Location - targetCell).LengthSquared).ThenBy(a => a.ActorID)
						.ToArray();
				}
				else if (mission.Type == FransMissionType.Secure)
				{
					if (!strategicMapService.TryGetGroundLandmassId(targetCell, out var targetLandmassId))
					{
						LogPioneerSecureNoBid(mission, targetCell, "SECURE objective has no valid Ground landmass");
						continue;
					}

					candidates = candidates
						.Where(a => strategicMapService.TryGetGroundLandmassId(a.Location, out var lm) && lm == targetLandmassId)
						.OrderBy(a => (a.Location - targetCell).LengthSquared).ThenBy(a => a.ActorID)
						.ToArray();
					if (candidates.Length == 0)
						LogPioneerSecureNoBid(mission, targetCell, $"no free Ground unit is already on target landmass {targetLandmassId}; GroundTransfer owns cross-landmass reinforcement");
				}
				if (candidates.Length == 0)
				{
					if (mission.Type == FransMissionType.Secure)
						LogPioneerSecureNoBid(mission, targetCell, "no currently available Ground candidate survives reservation/target filters");
					continue;
				}
				var chosenNormal = new List<Actor>();
				var offeredNormal = 0;
				int requiredNormal;
				if (mission.Type == FransMissionType.Defend)
				{
					var desiredUnitCount = commanderCoreService.GetDefendRequiredUnitCount(mission);
					var commitCount = Math.Min(desiredUnitCount, candidates.Length);
					chosenNormal.AddRange(candidates.Take(commitCount));
					offeredNormal = chosenNormal.Count;
					// Preserve the real 3x requirement in the bid, but submit the strongest available partial
					// Ground response when full coverage is impossible. The Broker already admits partial DEFEND
					// bids, allowing Ground to compete honestly with partial Air/Sea responses during emergencies.
					requiredNormal = desiredUnitCount;
				}
				else
				{
					var observedRequired = commanderCoreService.GetMissionRequiredContribution(FransCommanderKind.Ground, mission);
					if (mission.Type == FransMissionType.Secure)
						requiredNormal = GetSecurePackageRequirement(mission.SiteIntel, out _, out _);
					else
						requiredNormal = observedRequired;

					// Objective-sized SECURE doctrine commits enough tactical value for known hostile
					// strength plus uncertainty and a bounded control floor. It never derives demand
					// from the size of the currently free army.
					// When both infantry and vehicles are available, seed the immutable commitment
					// with one of each. Proximity fills an under-strength package, while the final
					// actor is chosen by increasing surplus cost so a needlessly large actor does not
					// consume capacity when a closer-fitting option is available.
					if (mission.Type == FransMissionType.Secure)
					{
						var packageCandidates = new FransGroundSecurePackageCandidate[candidates.Length];
						for (var i = 0; i < candidates.Length; i++)
						{
							var actor = candidates[i];
							packageCandidates[i] = new FransGroundSecurePackageCandidate(
								actor.ActorID,
								IsGroundInfantryActor(actor),
								GetCombatValue(actor),
								(actor.Location - targetCell).LengthSquared);
						}

						var selection = FransGroundSecurePackageSelector.Select(
							packageCandidates, requiredNormal, GetGroundTacticalGroupValue, GetSecureSurplusCost);
						foreach (var index in selection.CandidateIndexes)
							chosenNormal.Add(candidates[index]);
						offeredNormal = selection.OfferedValue;
					}
					else
					{
						foreach (var actor in candidates)
						{
							chosenNormal.Add(actor);
							offeredNormal = GetGroundTacticalGroupValue(chosenNormal);
							if (offeredNormal >= requiredNormal)
								break;
						}
					}
				}
				if (chosenNormal.Count == 0 ||
					(mission.Type != FransMissionType.Secure && mission.Type != FransMissionType.Defend && offeredNormal < requiredNormal))
					continue;

				var subject = chosenNormal[0];
				var defendMission = mission.Type == FransMissionType.Defend;
				int routeRisk;
				int travelCells;
				int force;
				int eta;
				int price;

				if (mission.Type == FransMissionType.Secure)
				{
					// Performance-only shared analysis: Ground capacities stagger their auctions, but
					// often evaluate the exact same immutable actor snapshot before CombatIntel or
					// RiskRevision changes. Reuse only when target, actor IDs AND actor cells match.
					// Any movement/reservation change naturally produces a different key and recomputes.
					if (!TryGetOrBuildSecureBidPathMemo(mission.TargetActorId, targetCell, chosenNormal, out var secureMemo))
					{
						LogPioneerSecureNoBid(mission, targetCell, "shared Ground SECURE route/risk/ETA proof is infeasible");
						continue;
					}
					routeRisk = secureMemo.RouteRisk;
					travelCells = secureMemo.TravelCells;
					force = secureMemo.Force;
					eta = secureMemo.Eta;
					price = AddSecureSurplusCost(secureMemo.Price, force, requiredNormal);
				}
				else
				{
					// DEFEND is an emergency response to observed pressure. It must not be vetoed or priced down
					// by the ordinary offensive RiskModel path planner: accepting danger is the point of DEFEND.
					if (!defendMission && !TryPlanGroundGroupDestination(chosenNormal, targetCell, out _))
						continue;
					routeRisk = 0;
					if (!defendMission)
					{
						var route = EvaluateMoveRisk(subject, subject.Location, targetCell);
						if (route.IsCritical)
							continue;
						routeRisk = route.PeakScore;
					}
					travelCells = defendMission
						? chosenNormal.Max(a => Math.Abs(targetCell.X - a.Location.X) + Math.Abs(targetCell.Y - a.Location.Y))
						: Math.Abs(targetCell.X - subject.Location.X) + Math.Abs(targetCell.Y - subject.Location.Y);
					force = GetGroundTacticalGroupValue(chosenNormal);
					eta = defendMission
						? chosenNormal.Max(a => commanderCoreService.EstimateMoveEtaTicks(a, targetCell))
						: commanderCoreService.EstimateMoveEtaTicks(subject, targetCell);
					if (eta == int.MaxValue)
						continue;
					price = commanderCoreService.PriceBid(FransCommanderKind.Ground, routeRisk, eta, force);
				}
				var defendScore = defendMission
					? commanderCoreService.ScoreDefendResponse(mission, offeredNormal, requiredNormal, eta, force)
					: default;
				var proposedDefendCount = chosenNormal.Count;
				var proposedDefendEta = eta;
				var proposedDefendScore = defendScore;
				var defendGuard = new FransGroundDefendForcePreservationDecision(
					FransGroundDefendForcePreservationAction.AcceptedUnchanged,
					chosenNormal.Count, 0, Math.Max(0, candidates.Length - chosenNormal.Count), 0);
				if (defendMission)
				{
					defendGuard = FransGroundDefendForcePreservationGuard.Evaluate(
						chosenNormal.Count,
						candidates.Length,
						defendScore.Utility,
						eta,
						Info.DefendForcePreservationMinimumPackageUnits,
						Info.DefendForcePreservationTriggerCommitPercent,
						Info.DefendForcePreservationLowReservePercent,
						Info.DefendForcePreservationMinimumReserveUnits,
						Info.DefendForcePreservationTargetReservePercent,
						Info.DefendForcePreservationLongEtaMinimumTicks);
					if (defendGuard.Action == FransGroundDefendForcePreservationAction.Reduced &&
						defendGuard.PackageCount < chosenNormal.Count)
					{
						if (defendGuard.PackageCount == 0)
						{
							chosenNormal.Clear();
							LogDefendBidDiagnostic(mission, normalAvailableUnits.Length, candidates.Length,
								proposedDefendCount, proposedDefendEta, proposedDefendScore,
								chosenNormal, eta, defendScore, defendGuard);
							continue;
						}

						chosenNormal.RemoveRange(defendGuard.PackageCount, chosenNormal.Count - defendGuard.PackageCount);
						offeredNormal = chosenNormal.Count;
						subject = chosenNormal[0];
						travelCells = chosenNormal.Max(a => Math.Abs(targetCell.X - a.Location.X) + Math.Abs(targetCell.Y - a.Location.Y));
						force = GetGroundTacticalGroupValue(chosenNormal);
						eta = chosenNormal.Max(a => commanderCoreService.EstimateMoveEtaTicks(a, targetCell));
						price = commanderCoreService.PriceBid(FransCommanderKind.Ground, routeRisk, eta, force);
						defendScore = commanderCoreService.ScoreDefendResponse(mission, offeredNormal, requiredNormal, eta, force);
					}
				}
				commandBidService.SubmitMissionBid(mission, new FransCommanderBidReport(
					FransCommanderKind.Ground, BidderKey, subject.ActorID, chosenNormal.Select(a => a.ActorID).ToArray(),
					price, routeRisk, travelCells, force, eta, offeredNormal, requiredNormal, false,
					defendScore.Utility, defendScore.StrengthScore, defendScore.UrgencyScore, defendScore.AssetRiskScore,
					defendScore.ResponseTimeCost, defendScore.OpportunityCost));
				if (defendMission)
					LogDefendBidDiagnostic(mission, normalAvailableUnits.Length, candidates.Length, proposedDefendCount,
						proposedDefendEta, proposedDefendScore, chosenNormal, eta, defendScore, defendGuard);
				if (mission.Type == FransMissionType.Secure)
					secureCommitments++;
				if (commandBidService.IsCapacityUnavailableForMissionBid(FransCommanderKind.Ground, BidderKey))
					return;
			}
		}

		void LogDefendBidDiagnostic(FransMission mission, int freeCount, int eligibleFreeCount,
			int proposedCount, int proposedEta, FransDefendResponseScore proposedScore,
			IReadOnlyCollection<Actor> selected, int eta, FransDefendResponseScore score,
			FransGroundDefendForcePreservationDecision guard)
		{
			var ownership = managedUnits
				.Select(a => commandBidService.TryGetActorMission(FransCommanderKind.Ground, a.ActorID, out var missionType, out _)
					? missionType.ToString()
					: "Free")
				.GroupBy(x => x)
				.OrderBy(g => g.Key, StringComparer.Ordinal)
				.Select(g => $"{g.Key}:{g.Count()}")
				.ToArray();
			var missionId = mission.MissionId != 0 ? mission.MissionId : mission.TargetActorId;
			var actorIds = string.Join(",", selected.OrderBy(a => a.ActorID).Select(a => a.ActorID));
			var finalReserve = Math.Max(0, eligibleFreeCount - selected.Count);
			var finalReservePercent = eligibleFreeCount > 0 ? finalReserve * 100 / eligibleFreeCount : 0;
			var signature = $"{missionId}|{mission.TargetActorId}|{freeCount}|{eligibleFreeCount}|{proposedCount}|{actorIds}|{eta}|{score.Utility}|{guard.Action}|{string.Join(",", ownership)}";
			if (signature == lastDefendBidDiagnosticSignature)
				return;
			lastDefendBidDiagnosticSignature = signature;
			FransBotLog.BotDebug(world,
				"{0}: [DEFEND FORCE GUARD] mission={1} representative={2} capacity={3} action={4} roster={5} free={6} ownership=[{7}] eligibleFree={8} proposed={9}/{8} proposedCommit={10}% proposedReserve={11}/{8} ({12}%) final={13}/{8} finalReserve={14}/{8} ({15}%) required={17} full={16} proposedEta={18} finalEta={19} proposedUtility={20} finalUtility={21} urgency={22} assetRisk={23} package=[{24}].",
				player, missionId, mission.TargetActorId, BidderKey, guard.Action, managedUnits.Count, freeCount,
				string.Join(",", ownership), eligibleFreeCount, proposedCount, guard.ProposedCommitPercent,
				guard.ProposedReserveCount, guard.ProposedReservePercent, selected.Count, finalReserve, finalReservePercent,
				proposedCount >= commanderCoreService.GetDefendRequiredUnitCount(mission), commanderCoreService.GetDefendRequiredUnitCount(mission),
				proposedEta, eta, proposedScore.Utility, score.Utility, score.UrgencyScore, score.AssetRiskScore, actorIds);
		}

		Actor[] ResolveCommittedGroundActors(FransActiveMission mission) => (mission.CommittedActorIds ?? Array.Empty<uint>())
			.Select(id => TryResolveManagedActor(id, out var actor) ? actor : null)
			.Where(a => a != null).ToArray();

		void ResetTacticalRetreatStateForNewMission()
		{
			// retreat strength and tactical safe-position memory belong to one MISSION.
			// Carrying either across auction ownership made a fresh SECURE inherit an old larger
			// combat baseline and/or retreat toward a stale point instead of its supplied ANCHOR.
			retreatBaselineCombatValue = 0;
			hasLastSafeMoveAnchor = false;
			lastSafeMoveAnchor = default;
			retreatAnchorPoint = hasMissionAnchorPoint ? missionAnchorPoint : default;
		}

		void ExecuteMission(IBot bot, Actor target, FransActiveMission mission)
		{
			using var fransPerf = FransBotLog.Profile(world, player, "Ground.ExecuteMission");
			RememberMissionAnchor(mission);
			if (mission.MissionType == FransMissionType.Secure)
			{
				ExecuteSecureMission(bot, mission);
				return;
			}

			if (mission.MissionType == FransMissionType.Recon)
			{
				ExecuteReconMission(bot, mission);
				return;
			}
			if (mission.MissionType == FransMissionType.Raid)
			{
				ExecuteRaidMission(bot, target, mission);
				return;
			}

			activeMissionType = mission.MissionType;
			ResetReconState();
			var changed = activeTargetActorId != mission.TargetActorId;
			if (changed)
			{
				ResetTacticalRetreatStateForNewMission();
				activeTargetActorId = mission.TargetActorId;
				activeObjective = mission.LastVisibleTargetCell;
				activeOrder = mission.InitialOrder;
				activeOrderStartedWorldTick = world.WorldTick;
				lostContactSinceWorldTick = -1;
				activeUnits.Clear();

				var committed = ResolveCommittedGroundActors(mission);
				if (committed.Length != mission.CommittedActorIds.Length || committed.Length == 0)
				{
					commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, "exact committed Ground actor snapshot is no longer available");
					ResetActiveMission();
					return;
				}
				foreach (var unit in committed)
					activeUnits.Add(unit);

				FransBotLog.BotDebug(world,
					"{0}: Ground Commander accepts MISSION {1} for target {2} at {3}; {4} unit(s), cost {5}. {6}",
					player, activeOrder, mission.TargetActorId, activeObjective, activeUnits.Count, mission.TotalCost,
					activeOrder == FransCommanderOrder.Move ? "RiskModel remains active during MOVE." : "RiskModel is ignored for DEFEND.");
			}
			if (target != null && IsVisibleEnemy(target))
			{
				activeObjective = target.Location;
				lostContactSinceWorldTick = -1;
			}
			else if (lostContactSinceWorldTick < 0)
				lostContactSinceWorldTick = world.WorldTick;
			if (activeOrder == FransCommanderOrder.Defend && target == null)
				activeObjective = mission.LastVisibleTargetCell;

			activeUnits.RemoveWhere(a => !managedUnits.Contains(a));
			if (activeUnits.Count == 0)
			{
				commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, "no live Ground Commander units remain");
				ResetActiveMission();
				return;
			}

			if (activeOrder == FransCommanderOrder.Move)
			{
				if (target != null && !activeUnits.Any(a => CanAttackActor(a, target)))
				{
					commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, "remembered target became visible but current Ground force cannot attack it");
					ResetActiveMission();
					return;
				}

				if (target != null && ShouldEnterFight(target))
				{
					BeginFight();
					FransBotLog.BotDebug(world,
						"{0}: Ground Commander MOVE -> FIGHT at {1} against visible {2} {3}; first-shot engagement begins. Pre-fight combat value {4}, fallback {5}.",
						player, activeObjective, target.Info.Name, target.ActorID, retreatBaselineCombatValue, retreatAnchorPoint);
					ExecuteFightMicro(bot, target);
					return;
				}

				ExecuteRiskPlannedMove(bot, activeObjective);
				return;
			}

			if (activeOrder == FransCommanderOrder.Defend)
			{
				// DEFEND has already accepted the danger. It never asks RiskModel for permission, but
				// the committed Ground force now uses a looser synchronized cohesion march so fast
				// vehicles do not arrive as a thin column far ahead of infantry/heavier units.
				if (target != null && IsVisibleEnemy(target))
				{
					if (ShouldEnterFight(target))
						ExecuteFightMicro(bot, target);
					else
						IssueGroundDefendCohesionMovement(bot, activeObjective);
				}
				else if (lostContactSinceWorldTick >= 0 && world.WorldTick - lostContactSinceWorldTick <= Info.FightLostContactHoldTicks)
					IssueGroundDefendCohesionMovement(bot, activeObjective);
				else
					// The Broker only retains this assignment while General's stable DEFEND incident is
					// authoritative. A missing representative is therefore lost tactical contact, not mission end.
					IssueGroundDefendCohesionMovement(bot, activeObjective);
				return;
			}

			if (activeOrder == FransCommanderOrder.Fight)
			{
				if (ShouldRetreatFromFight(out var currentFightValue))
				{
					BeginRetreat(bot, currentFightValue);
					return;
				}

				if (target != null && IsVisibleEnemy(target))
					ExecuteFightMicro(bot, target);
				else if (lostContactSinceWorldTick >= 0 && world.WorldTick - lostContactSinceWorldTick <= Info.FightLostContactHoldTicks)
					IssueAttackMoveGroup(bot, activeObjective, force: false);
				else
				{
					commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, "FIGHT contact cleared/lost");
					ResetActiveMission();
				}
				return;
			}

			if (activeOrder == FransCommanderOrder.Retreat)
				ExecuteRetreatRecovery(bot);
		}


		void ExecuteRaidMission(IBot bot, Actor target, FransActiveMission mission)
		{
			if (!IsGroundRaidEligibleTarget(mission))
			{
				commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, "Ground RAID target is neither a building nor HARV");
				ResetActiveMission();
				return;
			}

			var committedGroundActors = mission.CommittedActorIds
				.Select(id => TryResolveManagedActor(id, out var actor) ? actor : null)
				.Where(a => a != null)
				.ToArray();
			if (committedGroundActors.Any(a => !IsGroundRaidEligibleActor(a)))
			{
				commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, "Ground infantry is never eligible for RAID");
				ResetActiveMission();
				return;
			}

			var visibleTarget = target != null && IsVisibleEnemy(target);
			var selected = mission.CommittedActorIds
				.Select(id => TryResolveManagedActor(id, out var actor) && !raidRecoveryOrigins.ContainsKey(actor) &&
					(!visibleTarget || CanAttackActor(actor, target)) ? actor : null)
				.Where(a => a != null)
				.ToArray();
			if (selected.Length == 0)
			{
				CloseRaid(bot, "all committed Ground RAID units were lost/unavailable", true);
				return;
			}

			var required = mission.RequiredContribution;
			var damage = mission.OfferedContribution;
			// accepted ownership remains immutable, but the actor list is no longer
			// atomically brittle. Only surviving actors from the original committed IDs may
			// continue; Ground never recruits replacements into an accepted RAID.

			var changed = activeMissionType != FransMissionType.Raid || activeTargetActorId != mission.TargetActorId;
			if (changed)
			{
				ResetTacticalRetreatStateForNewMission();
				activeMissionType = FransMissionType.Raid;
				activeTargetActorId = mission.TargetActorId;
				activeObjective = visibleTarget ? target.Location : mission.LastVisibleTargetCell;
				activeOrder = FransCommanderOrder.Move;
				activeOrderStartedWorldTick = world.WorldTick;
				raidStrikeIssued = false;
				ResetRaidLostTargetSearch(false);
				activeUnits.Clear();
				raidMissionOrigins.Clear();
				raidKnownAdditionalDefenseIds.Clear();
				raidCommittedContributionByActor.Clear();
				raidProgressiveAttackActorIds.Clear();
				raidFeasibilityRecheckRequested = false;
				raidDefenseObservedWorldTick = -1;
				raidLastValidatedSurvivorCount = selected.Length;
				raidLocalDefenseActive = false;
				cohesionHeldUnits.Clear();
				cohesionFormationSlots.Clear();
				hasCohesionFormationObjective = false;
				foreach (var a in selected)
				{
					activeUnits.Add(a);
					raidMissionOrigins[a] = a.Location;
					if (visibleTarget)
						raidCommittedContributionByActor[a.ActorID] = commanderCoreService.EstimateRaidContribution(FransCommanderKind.Ground, a, target);
				}
				FransBotLog.BotDebug(world,
					visibleTarget
						? "{0}: Ground Commander accepts precision RAID {1} {2}: exact {3} units [{4}], current required strike {5}, estimated {6}. Synchronized cohesion Plain Move stages distinct firing cells; committed survivors progressively attack only the immutable target as they enter valid range."
						: "{0}: Ground Commander accepts precision RAID {1} {2}: exact {3} units [{4}], strike snapshot {6}/{5}. Target is currently unseen; force moves to LastVisibleTargetCell and performs bounded local plain-Move RECON before returning to ANCHOR if unreacquired.",
					player, mission.TargetActorType, mission.TargetActorId, activeUnits.Count,
					string.Join(",", activeUnits.OrderBy(a => a.ActorID).Select(a => a.ActorID)), required, damage);
			}
			else
			{
				activeUnits.RemoveWhere(a => !selected.Contains(a));
				foreach (var a in selected)
					activeUnits.Add(a);
			}

			if (activeUnits.Count == 0)
			{
				CloseRaid(bot, "all committed Ground RAID units were lost", true);
				return;
			}

			// A newly observed defender must be revalidated before lost-target RECON. Otherwise
			// an invisible immutable target could keep the force searching while fresh visible
			// defenders destroy it. When the target is unseen, validate the fair last-visible
			// corridor only; exact firing-position validation resumes after reacquisition.
			if (raidFeasibilityRecheckRequested && !visibleTarget)
			{
				if (combatIntelService.SnapshotWorldTick <= raidDefenseObservedWorldTick)
					return;

				var corridorChecks = activeUnits.OrderBy(a => a.ActorID)
					.Select(a => (Actor: a, Risk: EvaluateMoveRisk(a, a.Location, mission.LastVisibleTargetCell)))
					.ToArray();
				var critical = corridorChecks.FirstOrDefault(x => x.Risk.IsCritical);
				if (critical.Actor != null)
				{
					ReleaseRaidForRebid(bot, mission.TargetActorId,
						$"new defense makes last-visible Ground RAID corridor CRITICAL while target is unseen; peak {critical.Risk.PeakScore} at {critical.Risk.PeakCell}");
					return;
				}

				var peakRisk = corridorChecks.Length > 0 ? corridorChecks.Max(x => x.Risk.PeakScore) : 0;
				FransBotLog.BotDebug(world,
					"{0}: Ground RAID FEASIBILITY PASS after new defense while target is unseen: {1} committed survivor(s), last-visible corridor peak {2}; local self-defense is enabled before bounded target RECON continues.",
					player, activeUnits.Count, peakRisk);
				raidFeasibilityRecheckRequested = false;
				raidDefenseObservedWorldTick = -1;
				raidLocalDefenseActive = true;
			}

			if (!visibleTarget)
			{
				if (raidLocalDefenseActive && ExecuteRaidLocalSelfDefense(bot, target))
					return;
				ExecuteLostRaidTargetRecon(bot, mission);
				return;
			}

			if (raidSearchStartedWorldTick >= 0)
			{
				foreach (var a in activeUnits.Where(a => a != null && a.IsInWorld && !a.IsDead))
					a.CancelActivity();
				ResetRaidLostTargetSearch(false);
				raidStrikeIssued = false;
				raidProgressiveAttackActorIds.Clear();
				cohesionHeldUnits.Clear();
				cohesionFormationSlots.Clear();
				hasCohesionFormationObjective = false;
				FransBotLog.BotDebug(world, "{0}: Ground RAID reacquires exact target {1}; local RECON ends and the same RAID resumes.", player, mission.TargetActorId);
			}

			// Snapshot each committed actor's accepted strike contribution as soon as fair target
			// visibility permits it. This lets later casualty checks preserve the original accepted
			// target requirement without live-repricing target HP or recruiting replacements.
			foreach (var a in activeUnits.Where(a => !raidCommittedContributionByActor.ContainsKey(a.ActorID)))
				raidCommittedContributionByActor[a.ActorID] = commanderCoreService.EstimateRaidContribution(FransCommanderKind.Ground, a, target);

			var survivingContribution = (int)Math.Min(int.MaxValue, activeUnits.Sum(a =>
				(long)(raidCommittedContributionByActor.TryGetValue(a.ActorID, out var c) ? Math.Max(0, c) : 0)));
			var survivorCountChanged = activeUnits.Count != raidLastValidatedSurvivorCount;
			if (survivingContribution < required)
			{
				ReleaseRaidForRebid(bot, mission.TargetActorId,
					$"surviving committed Ground RAID strike contribution {survivingContribution}/{required} is no longer sufficient");
				return;
			}

			activeObjective = target.Location;
			if (raidFeasibilityRecheckRequested)
			{
				// The attack callback may fire after CombatIntel already sampled this world tick.
				// Wait for the next fair CombatIntel snapshot so the same RiskModel gate used by
				// bidding definitely includes every newly observed defender before we decide.
				if (combatIntelService.SnapshotWorldTick <= raidDefenseObservedWorldTick)
					return;

				var checks = activeUnits.OrderBy(a => a.ActorID).Select(a =>
				{
					var approach = FindGroundRaidApproachCell(a, target);
					var risk = approach.HasValue ? EvaluateMoveRisk(a, a.Location, approach.Value) : default(FransRouteRiskAssessment);
					return (Actor: a, Approach: approach, Risk: risk);
				}).ToArray();
				var unreachable = checks.FirstOrDefault(x => !x.Approach.HasValue);
				if (unreachable.Actor != null)
				{
					ReleaseRaidForRebid(bot, mission.TargetActorId,
						$"new defense revalidation found no reachable firing position for committed {unreachable.Actor.Info.Name} {unreachable.Actor.ActorID}");
					return;
				}

				var critical = checks.FirstOrDefault(x => x.Risk.IsCritical);
				if (critical.Actor != null)
				{
					ReleaseRaidForRebid(bot, mission.TargetActorId,
						$"new defense makes surviving committed Ground RAID route CRITICAL; peak {critical.Risk.PeakScore} at {critical.Risk.PeakCell}");
					return;
				}

				var peakRisk = checks.Length > 0 ? checks.Max(x => x.Risk.PeakScore) : 0;
				FransBotLog.BotDebug(world,
					"{0}: Ground RAID FEASIBILITY PASS after new defense: {1} surviving committed unit(s), immutable strike contribution {2}/{3}, route peak {4}; accepted mission continues target-only with no re-bid/recruitment.",
					player, activeUnits.Count, survivingContribution, required, peakRisk);
				raidFeasibilityRecheckRequested = false;
				raidDefenseObservedWorldTick = -1;
				raidLocalDefenseActive = true;
			}
			else if (survivorCountChanged)
			{
				FransBotLog.BotDebug(world,
					"{0}: Ground RAID SURVIVOR PASS: committed actor count changed to {1}, but surviving immutable strike contribution remains {2}/{3}; mission continues without replacing lost actors.",
					player, activeUnits.Count, survivingContribution, required);
			}
			raidLastValidatedSurvivorCount = activeUnits.Count;

			if (raidLocalDefenseActive && ExecuteRaidLocalSelfDefense(bot, target))
				return;

			// strike is progressive. Each immutable committed survivor attacks the
			// exact RAID target as soon as that actor enters its own valid weapon range. The
			// remaining survivors continue the synchronized cohesion approach instead of making
			// the whole group wait for the final slow/stalled unit.
			var inRange = activeUnits.Where(a => IsTargetWithinWeaponRange(a, target)).OrderBy(a => a.ActorID).ToArray();
			foreach (var a in inRange)
			{
				cohesionHeldUnits.Remove(a);
				raidProgressiveAttackActorIds.Add(a.ActorID);
				IssueExplicitAttack(bot, a, target, false);
			}

			if (inRange.Length > 0 && !raidStrikeIssued)
			{
				raidStrikeIssued = true;
				FransBotLog.BotDebug(world,
					"{0}: Ground RAID STRIKE NOW on {1} {2}: progressive target-only strike begins with {3}/{4} committed survivor(s) currently in range; estimated immutable strike snapshot {5}/{6}. Remaining survivors continue synchronized cohesion approach.",
					player, target.Info.Name, target.ActorID, inRange.Length, activeUnits.Count, damage, required);
			}

			var movers = activeUnits.Where(a => !IsTargetWithinWeaponRange(a, target)).OrderBy(a => a.ActorID).ToArray();
			foreach (var mover in movers)
				if (raidProgressiveAttackActorIds.Remove(mover.ActorID))
				{
					// Native Attack may chase a mobile exact target. Once that actor falls out of
					// valid range, force one fresh cohesion Move so a fast unit cannot drag the
					// formation forward by continuing its old chase activity.
					lastMoveDestination.Remove(mover);
					lastMoveWorldTick.Remove(mover);
				}
			if (movers.Length == 0)
				return;

			if (!TryBuildGroundRaidFormationDestinations(movers, target, out var destinations))
			{
				CloseRaid(bot, "target no longer has a reachable Ground firing position", true);
				return;
			}

			IssueGroundCohesionMovement(bot, movers, target.Location, destinations, attackMove: false);
		}

		void ExecuteLostRaidTargetRecon(IBot bot, FransActiveMission mission)
		{
			activeObjective = mission.LastVisibleTargetCell;
			// Once local RECON has started, its deadline is absolute. Waypoints may move the
			// group outside the 4-cell approach radius; that must never bypass the 400-WT bound.
			if (raidSearchStartedWorldTick >= 0 &&
				world.WorldTick - raidSearchStartedWorldTick >= commanderCoreService.RaidLostTargetReconTicks)
			{
				CloseRaid(bot, "exact target not reacquired during bounded local RECON", false);
				return;
			}

			var center = GetGroupCenter(activeUnits);
			if ((center - activeObjective).LengthSquared > 16)
			{
				activeOrder = FransCommanderOrder.Move;
				ExecuteRiskPlannedMove(bot, activeObjective);
				return;
			}

			if (raidSearchStartedWorldTick < 0)
			{
				var leader = activeUnits.OrderBy(a => a.ActorID).FirstOrDefault();
				if (leader == null)
				{
					CloseRaid(bot, "lost target search has no live Ground unit", true);
					return;
				}
				raidSearchStartedWorldTick = world.WorldTick;
				raidSearchSpiral.Reset(activeObjective, commanderCoreService.GetReconVisionCells(leader));
				hasRaidSearchWaypoint = false;
				activeOrder = FransCommanderOrder.Search;
				foreach (var a in activeUnits)
					a.CancelActivity();
				FransBotLog.BotDebug(world,
					"{0}: Ground RAID target {1} is gone/unseen at LastVisibleTargetCell {2}; begins {3}-WT local plain-Move RECON before ANCHOR return.",
					player, mission.TargetActorId, activeObjective, commanderCoreService.RaidLostTargetReconTicks);
			}

			if (hasRaidSearchWaypoint && activeUnits.Any(a => !a.IsIdle) && (center - raidSearchWaypoint).LengthSquared > 4)
				return;

			var lead = activeUnits.OrderBy(a => a.ActorID).FirstOrDefault();
			if (lead == null)
				return;
			var waypoints = new List<CPos>(Math.Min(4, commanderCoreService.ReconWaypointBatchSize));
			var cursor = center;
			for (var i = 0; i < Math.Min(4, commanderCoreService.ReconWaypointBatchSize); i++)
			{
				if (!raidSearchSpiral.TryGetNextWaypoint(world, c => FindGroundReconCell(lead, c), cursor, out var waypoint))
					break;
				waypoints.Add(waypoint);
				cursor = waypoint;
			}
			if (waypoints.Count == 0)
				return;
			foreach (var unit in activeUnits.OrderBy(a => a.ActorID))
				for (var i = 0; i < waypoints.Count; i++)
					bot.QueueOrder(new Order("Move", unit, Target.FromCell(world, waypoints[i]), i > 0));
			raidSearchWaypoint = waypoints[^1];
			hasRaidSearchWaypoint = true;
		}

		void ResetRaidLostTargetSearch(bool cancelActivities)
		{
			if (cancelActivities)
				foreach (var a in activeUnits.Where(a => a != null && a.IsInWorld && !a.IsDead))
					a.CancelActivity();
			raidSearchStartedWorldTick = -1;
			raidSearchWaypoint = default;
			hasRaidSearchWaypoint = false;
		}

		void ReleaseRaidForRebid(IBot bot, uint targetId, string reason)
		{
			commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, $"RAID RETREAT/re-bid: {reason}");
			if (targetId != 0)
				generalService.ReportRaidRetreat(targetId, $"Ground RAID: {reason}");
			if (activeMissionType == FransMissionType.Raid && activeTargetActorId == targetId)
				StartRaidRecovery(bot, $"RAID RETREAT/re-bid: {reason}");
			ResetActiveMission();
		}

		void CloseRaid(IBot bot, string reason, bool reportRetreat)
		{
			var targetId = activeTargetActorId;
			if (targetId != 0)
				commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, $"RAID ends: {reason}");
			if (reportRetreat && targetId != 0)
				generalService.ReportRaidRetreat(targetId, $"Ground RAID: {reason}");
			if (reportRetreat)
				StartRaidRecovery(bot, reason);
			else
				StartRaidAttackMoveReturn(bot, reason);
			ResetActiveMission();
		}

		void StartRaidAttackMoveReturn(IBot bot, string reason)
		{
			var returning = activeUnits.Where(a => a != null && a.IsInWorld && !a.IsDead).ToArray();
			foreach (var a in returning)
			{
				var origin = raidMissionOrigins.TryGetValue(a, out var saved) ? saved : a.Location;
				raidRecoveryOrigins[a] = origin;
				raidAttackMoveRecoveryActors.Add(a);
				IssueAttackMove(bot, a, origin, true);
			}
			if (returning.Length > 0)
			{
				PublishTransientReservations();
				FransBotLog.BotDebug(world,
					"{0}: Ground RAID normal completion sends {1} unit(s) by native AttackMove back to their individual RAID origin cells: {2}.",
					player, returning.Length, reason);
			}
			raidMissionOrigins.Clear();
		}

		void StartRaidRecovery(IBot bot, string reason)
		{
			var recovering = activeUnits.Where(a => a != null && a.IsInWorld && !a.IsDead).ToArray();
			foreach (var a in recovering)
			{
				raidAttackMoveRecoveryActors.Remove(a);
				var origin = raidMissionOrigins.TryGetValue(a, out var saved) ? saved : a.Location;
				var returnCell = hasMissionAnchorPoint ? missionAnchorPoint : origin;
				raidRecoveryOrigins[a] = returnCell;
				IssuePlainMove(bot, a, returnCell, true);
			}
			if (recovering.Length > 0)
			{
				PublishTransientReservations();
				FransBotLog.BotDebug(world, "{0}: Ground RAID return sends {1} unit(s) back to ANCHOR/fallback origin: {2}.", player, recovering.Length, reason);
			}
			raidMissionOrigins.Clear();
		}

		void MaintainRaidRecovery(IBot bot)
		{
			foreach (var a in raidRecoveryOrigins.Keys.ToArray())
			{
				if (a == null || !a.IsInWorld || a.IsDead || !managedUnits.Contains(a))
				{
					raidRecoveryOrigins.Remove(a);
					raidAttackMoveRecoveryActors.Remove(a);
					continue;
				}
				var origin = raidRecoveryOrigins[a];
				if ((a.Location - origin).LengthSquared <= 4)
				{
					raidRecoveryOrigins.Remove(a);
					raidAttackMoveRecoveryActors.Remove(a);
					continue;
				}
				if (raidAttackMoveRecoveryActors.Contains(a))
					IssueAttackMove(bot, a, origin, false);
				else
					IssuePlainMove(bot, a, origin, false);
			}
		}

		CPos? FindGroundRaidApproachCell(Actor unit, Actor target, ISet<CPos> reserved = null)
		{
			if (unit == null || !unit.IsInWorld || unit.IsDead || target == null || !target.IsInWorld || target.IsDead)
				return null;

			var mobile = unit.TraitOrDefault<Mobile>();
			if (mobile == null || !CanAttackActor(unit, target))
				return null;
			if (IsTargetWithinWeaponRange(unit, target) && (reserved == null || !reserved.Contains(unit.Location)) &&
				IsGroundRaidCellClearOfRestrictedStaticDefense(unit, unit.Location, target.ActorID))
				return unit.Location;
			var maxRangeCells = GetMaximumWeaponRangeCells(unit, target);
			if (maxRangeCells <= 0)
				return null;
			return world.Map.FindTilesInCircle(target.Location, Math.Min(Info.FightMicroRadius, maxRangeCells))
				.Where(world.Map.Contains)
				.Where(c => c != target.Location)
				.Where(c => reserved == null || !reserved.Contains(c))
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.Where(c => IsGroundRaidCellClearOfRestrictedStaticDefense(unit, c, target.ActorID))
				.Where(c => IsTargetWithinWeaponRangeFromCell(unit, target, c))
				.OrderBy(c => (c - unit.Location).LengthSquared)
				.ThenBy(c => (c - target.Location).LengthSquared)
				.ThenBy(c => c.X).ThenBy(c => c.Y)
				.Select(c => (CPos?)c).FirstOrDefault();
		}

		bool TryBuildGroundRaidFormationDestinations(Actor[] units, Actor target, out Dictionary<Actor, CPos> destinations)
		{
			destinations = [];
			if (target == null)
				return false;

			if (hasCohesionFormationObjective && cohesionFormationObjective == target.Location &&
				units.All(unit => cohesionFormationSlots.TryGetValue(unit, out var slot) &&
					IsGroundRaidCellClearOfRestrictedStaticDefense(unit, slot, target.ActorID) &&
					IsTargetWithinWeaponRangeFromCell(unit, target, slot)))
			{
				foreach (var unit in units)
					destinations[unit] = cohesionFormationSlots[unit];
				return true;
			}

			cohesionFormationSlots.Clear();
			hasCohesionFormationObjective = true;
			cohesionFormationObjective = target.Location;
			var reserved = new HashSet<CPos>();
			foreach (var unit in units.OrderBy(a => a.ActorID))
			{
				var destination = FindGroundRaidApproachCell(unit, target, reserved) ?? FindGroundRaidApproachCell(unit, target);
				if (!destination.HasValue)
					return false;
				destinations[unit] = destination.Value;
				cohesionFormationSlots[unit] = destination.Value;
				reserved.Add(destination.Value);
			}
			return true;
		}

		bool TryBuildGroundSecureFormationDestinations(Actor[] units, CPos center, out Dictionary<Actor, CPos> destinations)
		{
			destinations = [];
			if (hasCohesionFormationObjective && cohesionFormationObjective == center &&
				units.All(unit => cohesionFormationSlots.ContainsKey(unit)))
			{
				foreach (var unit in units)
					destinations[unit] = cohesionFormationSlots[unit];
				return true;
			}

			cohesionFormationSlots.Clear();
			hasCohesionFormationObjective = true;
			cohesionFormationObjective = center;
			var reserved = new HashSet<CPos>();
			foreach (var unit in units.OrderBy(a => a.ActorID))
			{
				var destination = FindGroundFormationCell(unit, center, reserved) ?? FindGroundFormationCell(unit, center, null);
				if (!destination.HasValue)
					return false;
				destinations[unit] = destination.Value;
				cohesionFormationSlots[unit] = destination.Value;
				reserved.Add(destination.Value);
			}
			return true;
		}

		CPos? FindGroundFormationCell(Actor unit, CPos center, ISet<CPos> reserved)
		{
			if (unit == null || !unit.IsInWorld || unit.IsDead || !world.Map.Contains(center))
				return null;

			var mobile = unit.TraitOrDefault<Mobile>();
			if (mobile == null)
				return null;
			var radius = Math.Max(1, Math.Min(Info.SecureAssemblyRadius, Info.CohesionFormationRadius));
			return world.Map.FindTilesInCircle(center, radius)
				.Where(world.Map.Contains)
				.Where(c => reserved == null || !reserved.Contains(c))
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.OrderBy(c => (c - center).LengthSquared)
				.ThenBy(c => (c - unit.Location).LengthSquared)
				.ThenBy(c => c.X).ThenBy(c => c.Y)
				.Select(c => (CPos?)c).FirstOrDefault();
		}

		CPos? FindRaidStaticDefenseEgressCell(Actor unit)
		{
			if (unit == null || !unit.IsInWorld || unit.IsDead)
				return null;

			var mobile = unit.TraitOrDefault<Mobile>();
			if (mobile == null)
				return null;
			var searchRadius = Math.Max(Info.RaidStaticDefenseAvoidanceRadius + 2, 8);
			return world.Map.FindTilesInCircle(unit.Location, searchRadius)
				.Where(world.Map.Contains)
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.Where(c => IsGroundRaidCellClearOfRestrictedStaticDefense(unit, c, activeTargetActorId))
				.OrderBy(c => (c - unit.Location).LengthSquared)
				.ThenBy(c => (c - activeObjective).LengthSquared)
				.ThenBy(c => c.X).ThenBy(c => c.Y)
				.Select(c => (CPos?)c).FirstOrDefault();
		}

		bool ExecuteRaidLocalSelfDefense(IBot bot, Actor raidTarget)
		{
			if (!raidLocalDefenseActive)
				return false;

			var radiusSq = Info.FightMicroRadius * Info.FightMicroRadius;
			var defenders = combatIntelService.VisibleEnemies
				.Where(IsVisibleEnemy)
				.Where(e => e != raidTarget && raidKnownAdditionalDefenseIds.Contains(e.ActorID))
				.Where(combatIntelService.IsTacticalCombatThreat)
				.Where(e => activeUnits.Any(a => CanAttackActor(a, e) && (e.Location - a.Location).LengthSquared <= radiusSq))
				.OrderByDescending(GetCombatValue)
				.ThenBy(e => e.ActorID)
				.ToArray();

			if (defenders.Length == 0)
			{
				raidLocalDefenseActive = false;
				foreach (var unit in activeUnits)
				{
					lastMoveDestination.Remove(unit);
					lastMoveWorldTick.Remove(unit);
				}
				FransBotLog.BotDebug(world,
					"{0}: Ground RAID LOCAL DEFENSE CLEAR; validated new defenders are no longer locally attackable/visible and the immutable RAID target {1} resumes.",
					player, activeTargetActorId);
				return false;
			}

			var restrictedStatic = defenders.Where(IsRestrictedGroundStaticDefense).ToArray();
			if (restrictedStatic.Length > 0 && !activeUnits.Any(IsRaidStaticDefenseBreaker))
			{
				ReleaseRaidForRebid(bot, activeTargetActorId,
					$"non-AA static defense is engaging the RAID and no ARTY/V2 breaker survives");
				return true;
			}

			foreach (var unit in activeUnits.OrderBy(a => a.ActorID))
			{
				var defender = defenders
					.Where(e => !IsRestrictedGroundStaticDefense(e) || IsRaidStaticDefenseBreaker(unit))
					.Where(e => CanAttackActor(unit, e) && (e.Location - unit.Location).LengthSquared <= radiusSq)
					.OrderBy(e => (e.Location - unit.Location).LengthSquared)
					.ThenBy(e => e.ActorID)
					.FirstOrDefault();
				if (defender != null)
				{
					cohesionHeldUnits.Remove(unit);
					IssueExplicitAttack(bot, unit, defender, false);
					continue;
				}

				if (!IsRaidStaticDefenseBreaker(unit) &&
					!IsGroundRaidCellClearOfRestrictedStaticDefense(unit, unit.Location, activeTargetActorId))
				{
					var egress = FindRaidStaticDefenseEgressCell(unit);
					if (egress.HasValue)
					{
						cohesionHeldUnits.Remove(unit);
						IssuePlainMove(bot, unit, egress.Value, false);
						continue;
					}
				}

				if (cohesionHeldUnits.Add(unit))
					bot.QueueOrder(new Order("Stop", unit, false));
			}

			return true;
		}

		int GetMaximumWeaponRangeCells(Actor attacker, Actor target)
		{
			if (attacker == null || !attacker.IsInWorld || attacker.IsDead || target == null || !target.IsInWorld || target.IsDead)
				return 0;

			var attackTarget = Target.FromActor(target);
			var range = attacker.TraitsImplementing<AttackBase>()
				.Where(a => !a.IsTraitDisabled && !a.IsTraitPaused)
				.SelectMany(a => a.Armaments)
				.Where(a => !a.IsTraitDisabled && !a.IsTraitPaused && a.Weapon.IsValidAgainst(attackTarget, world, attacker))
				.Select(a => a.MaxRange().Length).DefaultIfEmpty(0).Max();
			var cell = Math.Max(1, WDist.FromCells(1).Length);
			return Math.Max(0, (range + cell - 1) / cell);
		}

		bool IsTargetWithinWeaponRange(Actor attacker, Actor target)
		{
			if (!CanAttackActor(attacker, target))
				return false;

			return IsTargetWithinWeaponRangeAtPosition(attacker, target, attacker.CenterPosition);
		}

		bool IsTargetWithinWeaponRangeFromCell(Actor attacker, Actor target, CPos cell) =>
			IsTargetWithinWeaponRangeAtPosition(attacker, target, world.Map.CenterOfCell(cell));

		bool IsTargetWithinWeaponRangeAtPosition(Actor attacker, Actor target, WPos position)
		{
			if (!CanAttackActor(attacker, target))
				return false;
			var attackTarget = Target.FromActor(target);
			var distance = (target.CenterPosition - position).HorizontalLength;
			return attacker.TraitsImplementing<AttackBase>()
				.Where(a => !a.IsTraitDisabled && !a.IsTraitPaused)
				.SelectMany(a => a.Armaments)
				.Any(a => !a.IsTraitDisabled && !a.IsTraitPaused && a.Weapon.IsValidAgainst(attackTarget, world, attacker) && distance <= a.MaxRange().Length && (a.Weapon.MinRange == WDist.Zero || distance > a.Weapon.MinRange.Length));
		}

		bool HoldCombinedSecureUntilLaunch(FransActiveMission mission)
		{
			if (mission.CombinedSecureGroupSize <= 1 || world.WorldTick >= mission.ExecuteAfterWorldTick)
			{
				if (combinedSecureHoldTargetActorId == mission.TargetActorId)
				{
					combinedSecureHoldTargetActorId = 0;
					combinedSecureHoldUntilTick = -1;
				}
				return false;
			}

			if (combinedSecureHoldTargetActorId != mission.TargetActorId || combinedSecureHoldUntilTick != mission.ExecuteAfterWorldTick)
			{
				combinedSecureHoldTargetActorId = mission.TargetActorId;
				combinedSecureHoldUntilTick = mission.ExecuteAfterWorldTick;
				foreach (var unit in ResolveCommittedGroundActors(mission))
					unit.CancelActivity();
				FransBotLog.BotDebug(world,
					"{0}: Ground {1} holds COMBINED SECURE {2} until WT {3}; its ETA is {4} WT and {5} domains are timing departure toward the same area.",
					player, BidderKey, mission.TargetActorId, mission.ExecuteAfterWorldTick, mission.EstimatedEtaTicks, mission.CombinedSecureGroupSize);
			}
			return true;
		}

		void ReportSecureRetreatIfLast(uint targetActorId, string reason)
		{
			if (commandBidService.HasOtherActiveSecureMission(targetActorId, FransCommanderKind.Ground, BidderKey))
			{
				FransBotLog.BotDebug(world,
					"{0}: Ground {1} leaves COMBINED SECURE {2}: {3}. Another domain assignment remains active, so General does not reset the whole SECURE.",
					player, BidderKey, targetActorId, reason);
				return;
			}
			generalService.ReportSecureRetreat(targetActorId, reason);
		}

		bool AuthorizeSecureStaticDefenseFight(IBot bot, FransActiveMission mission)
		{
			// Reuse CombatIntel's authoritative sensor scan stamp. This revalidates at most once
			// per shared snapshot (not every Ground tick) and does not add a parallel revision model.
			combatIntelService.EnsureCurrentSnapshot();
			var combatSnapshotWorldTick = combatIntelService.SnapshotWorldTick;
			var survivingContribution = GetGroundTacticalGroupValue(activeUnits.Where(a => managedUnits.Contains(a)));
			var validationCurrent = secureStaticValidationTargetActorId == mission.TargetActorId &&
				secureStaticValidationCombatSnapshotWorldTick == combatSnapshotWorldTick;
			if (!validationCurrent)
			{
				if (!generalService.TryRefreshAcceptedSecureMission(mission.TargetActorId, out var currentMission) ||
					currentMission.Type != FransMissionType.Secure)
				{
					commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey,
						"SECURE authoritative mission/intel is unavailable before static-defense engagement");
					FransBotLog.BotDebug(world,
						"{0}: Ground SECURE {1} releases before static-defense FIGHT because General has no current authoritative SECURE mission/intel for contribution validation.",
						player, mission.TargetActorId);
					ResetActiveMission();
					return false;
				}

				secureStaticValidationRequiredContribution = GetSecurePackageRequirement(currentMission.SiteIntel,
					out secureStaticValidationKnownThreat, out _);
				secureStaticValidationTargetActorId = mission.TargetActorId;
				secureStaticValidationCombatSnapshotWorldTick = combatSnapshotWorldTick;
			}

			if (survivingContribution >= secureStaticValidationRequiredContribution)
				return true;

			// Reuse the existing RETREAT ownership/recovery lifecycle while leaving General's SECURE
			// opportunity open for a newly sized Ground bid. The current survivors remain reserved
			// during regroup and cannot be double-owned by the replacement auction.
			retreatBaselineCombatValue = Math.Max(1, survivingContribution);
			BeginRetreat(bot, survivingContribution,
				$"SECURE current Ground contribution {survivingContribution}/{secureStaticValidationRequiredContribution} is insufficient for refreshed authoritative static-defense intel (known threat {secureStaticValidationKnownThreat})",
				reportStrategicRetreat: false, allowFreeReinforcements: false);
			return false;
		}

		bool SecureMarchProgressTimedOut(CPos objective)
		{
			if (activeUnits.Count == 0)
				return false;
			var center = GetGroupCenter(activeUnits);
			var distanceSquared = (center - objective).LengthSquared;
			if (secureMarchLastProgressWorldTick < 0 || distanceSquared < secureMarchBestDistanceSquared)
			{
				secureMarchBestDistanceSquared = distanceSquared;
				secureMarchLastProgressWorldTick = world.WorldTick;
				return false;
			}
			return world.WorldTick - secureMarchLastProgressWorldTick >= Info.SecureMarchNoProgressTimeout;
		}

		void ResetSecureMarchProgress(CPos objective)
		{
			secureMarchBestDistanceSquared = activeUnits.Count == 0 ? int.MaxValue : (GetGroupCenter(activeUnits) - objective).LengthSquared;
			secureMarchLastProgressWorldTick = world.WorldTick;
		}

		void ExecuteSecureMission(IBot bot, FransActiveMission mission)
		{
			using var fransPerf = FransBotLog.Profile(world, player, "Ground.ExecuteSecure");
			if (HoldCombinedSecureUntilLaunch(mission))
				return;

			var changed = activeTargetActorId != mission.TargetActorId || activeMissionType != FransMissionType.Secure;
			activeMissionType = FransMissionType.Secure;
			ResetReconState();
			if (changed)
			{
				ResetTacticalRetreatStateForNewMission();
				secureStaticValidationTargetActorId = 0;
				secureStaticValidationCombatSnapshotWorldTick = -1;
				secureStaticValidationRequiredContribution = 0;
				secureStaticValidationKnownThreat = 0;
				activeTargetActorId = mission.TargetActorId;
				activeObjective = mission.LastVisibleTargetCell;
				activeOrder = FransCommanderOrder.Move;
				activeOrderStartedWorldTick = world.WorldTick;
				lostContactSinceWorldTick = -1;
				activeUnits.Clear();
				cohesionHeldUnits.Clear();
				cohesionFormationSlots.Clear();
				hasCohesionFormationObjective = false;
				var committed = ResolveCommittedGroundActors(mission);
				if (committed.Length != mission.CommittedActorIds.Length || committed.Length == 0)
				{
					ReportSecureRetreatIfLast(mission.TargetActorId, "Ground SECURE exact committed actor snapshot became unavailable");
					commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, "SECURE exact committed Ground actor snapshot is unavailable");
					ResetActiveMission();
					return;
				}

				if (mission.TargetActorType != FransGeneralBotModule.TransportLossSecureTargetType)
				{
					if (!strategicMapService.TryGetGroundLandmassId(mission.LastVisibleTargetCell, out var targetLandmassId) ||
						committed.Any(a => !strategicMapService.TryGetGroundLandmassId(a.Location, out var lm) || lm != targetLandmassId))
					{
						commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey,
							"SECURE assignment became cross-landmass; GroundTransfer owns ferry movement");
						FransBotLog.BotDebug(world,
							"{0}: Ground SECURE {1} releases before march because committed Ground is not physically on objective landmass {2}. Cross-landmass movement is delegated to GroundTransfer; SECURE stays available for native-land bidders.",
							player, mission.TargetActorId, targetLandmassId);
						ResetActiveMission();
						return;
					}
				}
				foreach (var unit in committed)
					activeUnits.Add(unit);

				if (mission.TargetActorType == FransGeneralBotModule.TransportLossSecureTargetType)
				{
					if (!TryGetTransportLossGroundObjective(mission.TargetActorId, mission.LastVisibleTargetCell, mission.SiteIntel, committed, out var nativeObjective, out _))
					{
						ReportSecureRetreatIfLast(mission.TargetActorId, "Ground LST-loss SECURE no longer has a native-land reachable Ground threat/objective");
						commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, "LST-loss SECURE requires native Ground access; GroundTransfer is deliberately forbidden from servicing this incident");
						ResetActiveMission();
						return;
					}

					activeObjective = nativeObjective;
				}
				secureMarchBestDistanceSquared = (GetGroupCenter(activeUnits) - activeObjective).LengthSquared;
				secureMarchLastProgressWorldTick = world.WorldTick;
				secureInitialAssemblyActive = hasMissionAnchorPoint &&
					(mission.LastVisibleTargetCell - missionAnchorPoint).LengthSquared > Info.SecurePreMoveAssemblyRadius * Info.SecurePreMoveAssemblyRadius;
				secureInitialAssemblyStartedTick = secureInitialAssemblyActive ? world.WorldTick : -1;
				secureRememberedObjective = null;
				var committedCombatValue = Math.Max(1, GetGroundTacticalGroupValue(activeUnits));
				var requiredValue = GetSecurePackageRequirement(mission.SiteIntel, out var knownThreat, out var uncertainty);
				var surplusCost = GetSecureSurplusCost(committedCombatValue, requiredValue);
				FransBotLog.BotDebug(world,
					"{0}: [SECURE PACKAGE] objective={1}#{2}@{3} knownThreat={4} uncertainty={5} requiredValue={6} selectedUnits={7} selectedValue={8} surplusCost={9}.",
					player, mission.TargetActorType, mission.TargetActorId, activeObjective, knownThreat, uncertainty,
					requiredValue, activeUnits.Count, committedCombatValue, surplusCost);
				if (mission.TargetActorType == FransGeneralBotModule.TransportLossSecureTargetType)
					FransBotLog.BotDebug(world,
						"{0}: Ground Commander accepts LST-loss SECURE {1}: {2} unit(s) already have native land access to Ground-relevant SiteIntel near loss cell {3}; local Ground objective {4}. GroundTransfer is not involved and no territorial ANCHOR will be created.",
						player, mission.TargetActorId, activeUnits.Count, mission.LastVisibleTargetCell, activeObjective);
				else
					FransBotLog.BotDebug(world,
						"{0}: Ground Commander accepts GENERAL SECURE {1} {2} at {3}; {4} unit(s), tactical combat value {5}, bid cost {6}. Doctrine: clear remembered buildings across {7} cells and mobile blockers inside {8} cells -> establish TERRITORIAL SECURE anchor -> release immediately; direct attackers are still fought wherever they engage the squad.",
						player, mission.TargetActorType == "fact" ? "enemy FACT" : "MineCluster", mission.TargetActorId, activeObjective, activeUnits.Count, committedCombatValue, mission.TotalCost,
						Info.SecureThreatRadius, Info.SecureMobileThreatRadius);
			}

			activeUnits.RemoveWhere(a => !managedUnits.Contains(a));
			if (activeUnits.Count == 0)
			{
				ReportSecureRetreatIfLast(mission.TargetActorId, "Ground SECURE has no live committed units");
				commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, "SECURE has no live Ground units");
				ResetActiveMission();
				return;
			}

			if (secureInitialAssemblyActive)
			{
				var preMoveAssemblyRadiusSq = Info.SecurePreMoveAssemblyRadius * Info.SecurePreMoveAssemblyRadius;
				var assembledCount = activeUnits.Count(a => (a.Location - missionAnchorPoint).LengthSquared <= preMoveAssemblyRadiusSq);
				var requiredAssemblyCount = Math.Max(1, (activeUnits.Count * Info.SecurePreMoveAssemblyPercent + 99) / 100);
				var timedOut = secureInitialAssemblyStartedTick >= 0 && world.WorldTick - secureInitialAssemblyStartedTick >= Info.SecurePreMoveAssemblyTimeout;
				if (assembledCount < requiredAssemblyCount && !timedOut)
				{
					activeOrder = FransCommanderOrder.Move;
					activeObjective = missionAnchorPoint;
					IssueSecureCohesionMove(bot, missionAnchorPoint);
					return;
				}

				secureInitialAssemblyActive = false;
				secureMarchBestDistanceSquared = (GetGroupCenter(activeUnits) - mission.LastVisibleTargetCell).LengthSquared;
				secureMarchLastProgressWorldTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					timedOut && assembledCount < requiredAssemblyCount
						? "{0}: Ground SECURE {1} bounded ANCHOR ASSEMBLE timeout: {2}/{3} units are staged near {4}; committed force departs now under normal cohesion instead of waiting for stragglers."
						: "{0}: Ground SECURE {1} ANCHOR ASSEMBLE complete: {2}/{3} units staged near {4}; territorial advance begins.",
					player, mission.TargetActorId, assembledCount, activeUnits.Count, missionAnchorPoint);
			}

			if (mission.TargetActorType != FransGeneralBotModule.TransportLossSecureTargetType)
				activeObjective = mission.LastVisibleTargetCell;
			if (supportCoordinatorService != null &&
				supportCoordinatorService.TryGetNukeExclusion(mission.TargetActorId, out var nukeCenter, out var nukeRadius))
			{
				StageSecureOutsideNukeExclusion(bot, mission, nukeCenter, nukeRadius);
				return;
			}

			var threatRadiusSq = Info.SecureThreatRadius * Info.SecureThreatRadius;
			var mobileThreatRadiusSq = Info.SecureMobileThreatRadius * Info.SecureMobileThreatRadius;

			// Territorial SECURE completion is governed by static control first. Visible enemy
			// buildings block across the full radius and remembered buildings still have to be
			// checked before the static-clear timer may mature. Mobile enemies can force local
			// combat early in the clear, but they are not allowed to reset the static-control
			// timer forever. Direct attackers remain handled by RespondToAttack at any range.
			var staticThreat = combatIntelService.VisibleEnemies
				.Where(IsVisibleEnemy)
				.Where(t => t.Info.HasTraitInfo<BuildingInfo>() &&
					(t.Location - mission.LastVisibleTargetCell).LengthSquared <= threatRadiusSq)
				.Where(t => activeUnits.Any(u => CanAttackActor(u, t)))
				.OrderByDescending(t => combatIntelService.IsTacticalCombatThreat(t))
				.ThenBy(t => (t.Location - mission.LastVisibleTargetCell).LengthSquared)
				.ThenBy(t => t.ActorID)
				.FirstOrDefault();

			if (staticThreat != null)
			{
				secureStaticClearSinceWorldTick = -1;
				secureRememberedObjective = null;
				ResetSecureMarchProgress(mission.LastVisibleTargetCell);
				if (combatIntelService.IsTacticalCombatThreat(staticThreat) &&
					!AuthorizeSecureStaticDefenseFight(bot, mission))
					return;
				if (activeOrder != FransCommanderOrder.Fight)
				{
					BeginFight();
					FransBotLog.BotDebug(world,
						"{0}: Ground SECURE initial CLEAR -> FIGHT against territorial building {2} {3} inside the full {1}-cell control radius. Static control must be removed before the territorial-clear hold can mature.",
						player, Info.SecureThreatRadius, staticThreat.Info.Name, staticThreat.ActorID);
				}
				else if (ShouldRetreatFromFight(out var currentFightValue))
				{
					BeginRetreat(bot, currentFightValue);
					return;
				}
				ExecuteFightMicro(bot, staticThreat);
				return;
			}

			if (activeOrder == FransCommanderOrder.Fight && ShouldRetreatFromFight(out var currentSecureFightValue))
			{
				BeginRetreat(bot, currentSecureFightValue);
				return;
			}

			if (strategicMapService.TryGetGroundLandmassId(activeObjective, out var secureObjectiveLandmassId) &&
				TrySelectRememberedSecureBuilding(mission.LastVisibleTargetCell, Info.SecureThreatRadius,
					secureObjectiveLandmassId, out var rememberedInitial))
			{
				secureStaticClearSinceWorldTick = -1;
				activeOrder = FransCommanderOrder.Move;
				var rememberedObjective = rememberedInitial.LastSeenCell;
				if (!secureRememberedObjective.HasValue || secureRememberedObjective.Value != rememberedObjective)
				{
					secureRememberedObjective = rememberedObjective;
					ResetSecureMarchProgress(rememberedObjective);
				}

				activeObjective = rememberedObjective;
				if (SecureMarchProgressTimedOut(activeObjective))
				{
					ReportSecureRetreatIfLast(mission.TargetActorId,
						$"Ground SECURE remembered-building march made no physical progress for {Info.SecureMarchNoProgressTimeout} WT");
					commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey,
						"SECURE remembered-building no-progress watchdog released stale assignment");
					FransBotLog.BotDebug(world,
						"{0}: Ground SECURE {1} REMEMBERED-BUILDING NO-PROGRESS watchdog releases stale assignment after {2} WT without group-center progress toward same-landmass objective {3}.",
						player, mission.TargetActorId, Info.SecureMarchNoProgressTimeout, activeObjective);
					ResetActiveMission();
					return;
				}

				IssueSecureCohesionMove(bot, activeObjective);
				return;
			}

			if (secureRememberedObjective.HasValue)
			{
				secureRememberedObjective = null;
				ResetSecureMarchProgress(mission.LastVisibleTargetCell);
			}

			var assemblyRadiusSq = Info.SecureAssemblyRadius * Info.SecureAssemblyRadius;
			var hasTerritorialPresence = activeUnits.Any(a =>
				(a.Location - mission.LastVisibleTargetCell).LengthSquared <= assemblyRadiusSq);
			if (!hasTerritorialPresence)
				secureStaticClearSinceWorldTick = -1;
			else if (secureStaticClearSinceWorldTick < 0)
				secureStaticClearSinceWorldTick = world.WorldTick;
			var staticClearHeldFor = secureStaticClearSinceWorldTick < 0
				? 0
				: world.WorldTick - secureStaticClearSinceWorldTick;
			var territorialClearMature = mission.TargetActorType != FransGeneralBotModule.TransportLossSecureTargetType &&
				hasTerritorialPresence && staticClearHeldFor >= Info.SecureTerritorialClearHoldTicks;

			var mobileThreat = combatIntelService.VisibleEnemies
				.Where(IsVisibleEnemy)
				.Where(t => !t.Info.HasTraitInfo<BuildingInfo>() &&
					(t.Location - mission.LastVisibleTargetCell).LengthSquared <= mobileThreatRadiusSq)
				.Where(t => activeUnits.Any(u => CanAttackActor(u, t)))
				.OrderByDescending(t => combatIntelService.IsTacticalCombatThreat(t))
				.ThenBy(t => (t.Location - mission.LastVisibleTargetCell).LengthSquared)
				.ThenBy(t => t.ActorID)
				.FirstOrDefault();

			if (mobileThreat != null && !territorialClearMature)
			{
				ResetSecureMarchProgress(mission.LastVisibleTargetCell);
				if (activeOrder != FransCommanderOrder.Fight)
				{
					BeginFight();
					FransBotLog.BotDebug(world,
						"{0}: Ground SECURE initial CLEAR -> FIGHT against mobile blocker {2} {3} inside {4} cells. Static territory has been clear for {5}/{6} WT; after the hold matures, recurring mobile contact no longer pins SECURE completion.",
						player, Info.SecureThreatRadius, mobileThreat.Info.Name, mobileThreat.ActorID, Info.SecureMobileThreatRadius,
						staticClearHeldFor, Info.SecureTerritorialClearHoldTicks);
				}
				ExecuteFightMicro(bot, mobileThreat);
				return;
			}

			if (activeOrder == FransCommanderOrder.Fight)
			{
				activeOrder = FransCommanderOrder.Move;
				activeOrderStartedWorldTick = world.WorldTick;
			}

			activeObjective = mission.LastVisibleTargetCell;
			var assembled = activeUnits.Where(a => (a.Location - activeObjective).LengthSquared <= assemblyRadiusSq).ToArray();
			var requiredCount = Math.Max(1, (activeUnits.Count * 3 + 3) / 4);
			if (assembled.Length < requiredCount)
			{
				if (SecureMarchProgressTimedOut(activeObjective))
				{
					ReportSecureRetreatIfLast(mission.TargetActorId, $"Ground SECURE march made no physical progress for {Info.SecureMarchNoProgressTimeout} WT");
					commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, "SECURE march no-progress watchdog released stale assignment");
					FransBotLog.BotDebug(world,
						"{0}: Ground SECURE {1} NO-PROGRESS watchdog releases stale assignment after {2} WT without group-center progress toward {3}. Units become free immediately; General may re-auction after normal RETREAT cooldown instead of pinning the only Ground SECURE slot.",
						player, mission.TargetActorId, Info.SecureMarchNoProgressTimeout, activeObjective);
					ResetActiveMission();
					return;
				}
				IssueSecureCohesionMove(bot, activeObjective);
				return;
			}

			var secureAnchorPoint = activeObjective;
			if (mission.TargetActorType == FransGeneralBotModule.TransportLossSecureTargetType)
			{
				if (!generalService.CompleteDomainSecureMission(mission.TargetActorId, FransCommanderKind.Ground, secureAnchorPoint,
					$"Ground cleared the reachable shore-side threat area and assembled {assembled.Length}/{activeUnits.Count} SECURE units") &&
					generalService.IsTransportLossSecure(mission.TargetActorId))
					return;

				FransBotLog.BotDebug(world,
					"{0}: Ground LST-loss SECURE {1} is CLEAR from native land access at {2}. Incident closes with no territorial ANCHOR/foothold and the squad is released immediately.",
					player, mission.TargetActorId, secureAnchorPoint);
				commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey,
					"LST-loss SECURE clear complete; no territorial ANCHOR; release immediately");
				ResetActiveMission();
				return;
			}

			if (!territorialClearMature)
			{
				// The force may finish assembling while the static-clear hold matures, but the
				// territorial mission itself cannot complete until static control has remained
				// absent for the bounded hold. This prevents a one-tick building disappearance
				// from prematurely establishing the ANCHOR.
				IssueSecureCohesionMove(bot, activeObjective);
				return;
			}

			secureAnchorPoint = mission.LastVisibleTargetCell;
			if (!generalService.EstablishSecureAnchor(mission.TargetActorId, secureAnchorPoint,
				$"Ground cleared {Info.SecureThreatRadius}-cell area and assembled {assembled.Length}/{activeUnits.Count} SECURE units"))
				return;

			hasLastSafeMoveAnchor = true;
			lastSafeMoveAnchor = secureAnchorPoint;
			retreatAnchorPoint = secureAnchorPoint;
			retreatBaselineCombatValue = 0;
			activeOrder = FransCommanderOrder.Move;
			activeOrderStartedWorldTick = world.WorldTick;
			FransBotLog.BotDebug(world,
				"{0}: Ground SECURE {1} territorial static-control area stayed clear for {4} WT across {2} cells. TERRITORIAL SECURE anchor is established at {3}; SECURE completes now even if transient mobile enemies remain nearby, while direct attackers still use normal local FIGHT after release.",
				player, mission.TargetActorId, Info.SecureThreatRadius, secureAnchorPoint, staticClearHeldFor);
			commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey,
				"SECURE clear complete; territorial SECURE anchor established; release immediately for next SECURE");
			ResetActiveMission();
		}

		void StageSecureOutsideNukeExclusion(IBot bot, FransActiveMission mission, CPos nukeCenter, int nukeRadius)
		{
			var marchers = activeUnits.Where(a => a != null && a.IsInWorld && !a.IsDead && !mcvRightOfWayUnits.Contains(a))
				.OrderBy(a => a.ActorID).ToArray();
			if (marchers.Length == 0)
				return;

			var representative = marchers.FirstOrDefault(a => a.TraitOrDefault<Mobile>() != null);
			if (representative == null)
				return;

			var mobile = representative.Trait<Mobile>();
			var groupCenter = GetGroupCenter(marchers);
			var inner = Math.Max(1, nukeRadius + 2);
			var outer = inner + 5;
			var stage = world.Map.FindTilesInAnnulus(nukeCenter, inner, outer)
				.Where(world.Map.Contains)
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.OrderBy(c => (c - groupCenter).LengthSquared)
				.ThenBy(c => c.Y).ThenBy(c => c.X)
				.Take(24)
				.Select(c => (Cell: c, Risk: riskModelService.EvaluateCell(representative, c, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced)))
				.Where(x => !x.Risk.IsCritical)
				.OrderBy(x => x.Risk.Score)
				.ThenBy(x => (x.Cell - groupCenter).LengthSquared)
				.ThenBy(x => x.Cell.Y).ThenBy(x => x.Cell.X)
				.Select(x => (CPos?)x.Cell)
				.FirstOrDefault();

			if (!stage.HasValue)
				return;

			activeOrder = FransCommanderOrder.Move;
			activeObjective = stage.Value;
			if (TryBuildGroundSecureFormationDestinations(marchers, stage.Value, out var formation))
				IssueGroundCohesionMovement(bot, marchers, stage.Value, formation, attackMove: false);
			else
				foreach (var unit in marchers)
					IssuePlainMove(bot, unit, stage.Value, force: false);

			if (world.WorldTick >= nextNukeStageLogTick)
			{
				nextNukeStageLogTick = world.WorldTick + 125;
				FransBotLog.BotDebug(world,
					"{0}: Ground SECURE {1} NUKE EVACUATION/STAGING: {2} committed unit(s) hold at {3}, outside strike {4} exclusion radius {5}. Plain Move is used until SupportCoordinator releases the same SECURE.",
					player, mission.TargetActorId, marchers.Length, stage.Value, nukeCenter, nukeRadius);
			}
		}

		bool TrySelectRememberedSecureBuilding(CPos center, int radiusCells, int groundLandmassId,
			out FransCombatIntelContact building)
		{
			var radiusSq = radiusCells * radiusCells;
			var candidates = combatIntelService.EnemyCombatContacts
				.Where(c => c.ActorId != 0 && c.IsBuilding)
				.Where(c => c.Owner != null && PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(c.Owner)))
				.Where(c => (c.LastSeenCell - center).LengthSquared <= radiusSq)
				.Where(c => strategicMapService.TryGetGroundLandmassId(c.LastSeenCell, out var rememberedLandmassId) &&
					rememberedLandmassId == groundLandmassId)
				.ToArray();


			building = candidates
				.OrderBy(c => (c.LastSeenCell - center).LengthSquared)
				.ThenBy(c => c.ActorId)
				.FirstOrDefault();
			return building.ActorId != 0;
		}

		void IssueSecureCohesionMove(IBot bot, CPos objective)
		{
			var marchers = activeUnits.Where(a => !mcvRightOfWayUnits.Contains(a)).OrderBy(a => a.ActorID).ToArray();
			if (marchers.Length == 0)
				return;
			if (!TryBuildGroundSecureFormationDestinations(marchers, objective, out var formation))
			{
				IssueAttackMoveGroup(bot, objective, force: false);
				return;
			}
			IssueGroundCohesionMovement(bot, marchers, objective, formation, attackMove: true);
		}

		void BeginFight()
		{
			activeOrder = FransCommanderOrder.Fight;
			activeOrderStartedWorldTick = world.WorldTick;
			lostContactSinceWorldTick = -1;

			// the high-water baseline is mission-local. ResetTacticalRetreatStateForNewMission
			// clears it whenever new auction ownership begins, while repeated FIGHTs inside the same
			// MISSION still preserve the highest pre-fight value so attrition cannot reset the trigger.
			var fightValue = Math.Max(1, GetGroundTacticalGroupValue(activeUnits));
			retreatBaselineCombatValue = Math.Max(retreatBaselineCombatValue, fightValue);
			// Retreat fallback is mission-local: latest safe position inside this mission, then
			// the ANCHOR supplied by General, then the current group center.
			retreatAnchorPoint = hasLastSafeMoveAnchor ? lastSafeMoveAnchor :
				hasMissionAnchorPoint ? missionAnchorPoint : GetGroupCenter(activeUnits);
		}

		bool ShouldRetreatFromFight(out int currentCombatValue)
		{
			currentCombatValue = GetGroundTacticalGroupValue(activeUnits.Where(a => managedUnits.Contains(a)));
			if (retreatBaselineCombatValue <= 0 || currentCombatValue <= 0)
				return false;
			var threshold = Math.Max(1, retreatBaselineCombatValue * Info.RetreatAtRemainingForcePercent / 100);
			return currentCombatValue <= threshold;
		}

		void BeginRetreat(IBot bot, int currentCombatValue, string reason = null,
			bool reportStrategicRetreat = true, bool allowFreeReinforcements = true)
		{
			// Keep only the exact surviving MISSION group. Ordinary collapse recovery may recruit
			// genuinely free reinforcements below; refreshed-threat SECURE rejection explicitly may not.
			activeUnits.RemoveWhere(a => a == null || !a.IsInWorld || a.IsDead || !managedUnits.Contains(a));
			var retreatMissionType = activeMissionType;
			var retreatTargetId = activeTargetActorId;
			var retreatReason = reason ?? $"Ground force collapse {currentCombatValue}/{retreatBaselineCombatValue}";
			if (reportStrategicRetreat && retreatMissionType == FransMissionType.Raid && retreatTargetId != 0)
				generalService.ReportRaidRetreat(retreatTargetId, retreatReason);
			else if (reportStrategicRetreat && retreatMissionType == FransMissionType.Secure && retreatTargetId != 0)
				ReportSecureRetreatIfLast(retreatTargetId, retreatReason);
			commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey,
				$"{retreatReason}; RETREAT owns regroup");
			retreatRecoveryActive = true;
			retreatRecoveryAllowsReinforcements = allowFreeReinforcements;
			EnsureAnchorStandbyCenter(retreatAnchorPoint);
			retreatStartedWorldTick = world.WorldTick;
			activeTargetActorId = 0;
			activeOrder = FransCommanderOrder.Retreat;
			activeOrderStartedWorldTick = world.WorldTick;
			activeObjective = retreatAnchorPoint;
			lostContactSinceWorldTick = -1;
			PublishTransientReservations();
			FransBotLog.BotDebug(world,
				allowFreeReinforcements
					? "{0}: Ground Commander -> RETREAT: {1}. Combat value {2}/{3}; ANCHOR POINT {4}. Exact MISSION survivors remain reserved; only genuinely free reinforcements may join until {5}% of the authoritative baseline is assembled."
					: "{0}: Ground Commander -> SURVIVOR-ONLY RETREAT: {1}. Combat value {2}/{3}; ANCHOR POINT {4}. Only the exact failed SECURE survivors remain reserved; no unrelated free Ground unit may join while the released SECURE rebids.",
				player, retreatReason, currentCombatValue, retreatBaselineCombatValue, retreatAnchorPoint, Info.ResumeOffenseAtOriginalForcePercent);
			foreach (var unit in activeUnits.Where(a => !mcvRightOfWayUnits.Contains(a)).OrderBy(a => a.ActorID))
				RouteRetreatUnit(bot, unit, true);
		}

		void ExecuteRetreatRecovery(IBot bot)
		{
			activeOrder = FransCommanderOrder.Retreat;
			activeObjective = retreatAnchorPoint;
			activeUnits.RemoveWhere(a => a == null || !a.IsInWorld || a.IsDead || !managedUnits.Contains(a));
			if (!retreatRecoveryAllowsReinforcements && activeUnits.Count == 0)
			{
				retreatRecoveryActive = false;
				retreatRecoveryAllowsReinforcements = true;
				retreatStartedWorldTick = -1;
				retreatBaselineCombatValue = 0;
				ResetActiveMission();
				PublishTransientReservations();
				return;
			}

			var reservedValue = GetGroundTacticalGroupValue(activeUnits);
			var recoveryBaseline = retreatRecoveryAllowsReinforcements
				? retreatBaselineCombatValue
				: Math.Min(retreatBaselineCombatValue, Math.Max(1, reservedValue));
			var requiredValue = Math.Max(1, recoveryBaseline * Info.ResumeOffenseAtOriginalForcePercent / 100);
			if (retreatRecoveryAllowsReinforcements && reservedValue < requiredValue)
			{
				foreach (var candidate in managedUnits
					.Where(a => !activeUnits.Contains(a) && a != reconRetreatActor && !raidRecoveryOrigins.ContainsKey(a) && !mcvRightOfWayUnits.Contains(a))
					.Where(a => commanderCoreService.IsActorAvailableForBidder(FransCommanderKind.Ground, BidderKey, a))
					.OrderBy(a => (a.Location - retreatAnchorPoint).LengthSquared).ThenByDescending(GetCombatValue).ThenBy(a => a.ActorID))
				{
					activeUnits.Add(candidate);
					reservedValue = GetGroundTacticalGroupValue(activeUnits);
					if (reservedValue >= requiredValue)
						break;
				}
			}

			PublishTransientReservations();
			foreach (var unit in activeUnits.Where(a => !mcvRightOfWayUnits.Contains(a)).OrderBy(a => a.ActorID))
				RouteRetreatUnit(bot, unit, false);

			var radiusSq = Info.RetreatAssemblyRadius * Info.RetreatAssemblyRadius;
			var assembledValue = GetGroundTacticalGroupValue(activeUnits
				.Where(IsGroundRecoveryReady)
				.Where(a => (a.Location - retreatAnchorPoint).LengthSquared <= radiusSq));
			if (assembledValue < requiredValue)
				return;

			FransBotLog.BotDebug(world,
				"{0}: Ground Commander RETREAT recovery complete at ANCHOR POINT {1}: assembled combat value {2}/{3} within {4} cells. Ordinary MISSION bidding resumes from this retained point.",
				player, retreatAnchorPoint, assembledValue, requiredValue, Info.RetreatAssemblyRadius);
			retreatRecoveryActive = false;
			retreatRecoveryAllowsReinforcements = true;
			retreatStartedWorldTick = -1;
			retreatBaselineCombatValue = 0;
			hasLastSafeMoveAnchor = true;
			lastSafeMoveAnchor = retreatAnchorPoint;
			ResetActiveMission();
			PublishTransientReservations();
		}

		static CPos GetGroupCenter(IEnumerable<Actor> units)
		{
			var live = units.Where(a => a != null && a.IsInWorld && !a.IsDead).ToArray();
			if (live.Length == 0)
				return default;
			return new CPos(live.Sum(a => a.Location.X) / live.Length, live.Sum(a => a.Location.Y) / live.Length);
		}

		static int CohesionCellDistance(CPos a, CPos b) =>
			Math.Max(Math.Abs(a.X - b.X), Math.Abs(a.Y - b.Y));

		void IssueGroundDefendCohesionMovement(IBot bot, CPos objective)
		{
			var marchers = activeUnits.Where(a => !mcvRightOfWayUnits.Contains(a)).OrderBy(a => a.ActorID).ToArray();
			if (marchers.Length == 0)
				return;

			if (!TryBuildGroundSecureFormationDestinations(marchers, objective, out var formation))
			{
				IssueAttackMoveGroup(bot, objective, force: false);
				return;
			}

			IssueGroundCohesionMovement(bot, marchers, objective, formation, attackMove: true,
				Info.DefendCohesionMaximumLeadCells, Info.DefendCohesionChokepointLeadCells);
		}

		void IssueGroundCohesionMovement(IBot bot, IReadOnlyCollection<Actor> units, CPos referenceObjective,
			IReadOnlyDictionary<Actor, CPos> destinations, bool attackMove, int? maximumLeadCells = null, int? chokepointLeadCells = null)
		{
			var live = units.Where(a => a != null && a.IsInWorld && !a.IsDead && destinations.ContainsKey(a))
				.OrderBy(a => a.ActorID).ToArray();
			if (live.Length == 0)
				return;

			cohesionHeldUnits.RemoveWhere(a => !live.Contains(a) && !activeUnits.Contains(a));

			if (live.Length == 1)
			{
				var only = live[0];
				var force = cohesionHeldUnits.Remove(only);
				if (attackMove)
					IssueAttackMove(bot, only, destinations[only], force);
				else
					IssuePlainMove(bot, only, destinations[only], force);
				return;
			}

			var trailer = live
				.OrderByDescending(a => CohesionCellDistance(a.Location, referenceObjective))
				.ThenBy(a => a.ActorID)
				.First();
			var normalLead = maximumLeadCells ?? Info.CohesionMaximumLeadCells;
			var chokeLead = chokepointLeadCells ?? Info.CohesionChokepointLeadCells;
			var trailerRemaining = CohesionCellDistance(trailer.Location, referenceObjective);
			var stalledTrailer = trailer.IsIdle && trailerRemaining > normalLead &&
				lastMoveWorldTick.TryGetValue(trailer, out var trailerLastMove) &&
				world.WorldTick - trailerLastMove >= Info.ScanInterval;
			var allowedLead = stalledTrailer ? chokeLead : normalLead;

			foreach (var unit in live)
			{
				var remaining = CohesionCellDistance(unit.Location, referenceObjective);
				var lead = trailerRemaining - remaining;
				if (lead > allowedLead)
				{
					if (cohesionHeldUnits.Add(unit))
						bot.QueueOrder(new Order("Stop", unit, false));
					continue;
				}

				var force = cohesionHeldUnits.Remove(unit);
				var destination = destinations[unit];
				if ((unit.Location - destination).LengthSquared <= 1)
					continue;
				if (attackMove)
					IssueAttackMove(bot, unit, destination, force);
				else
					IssuePlainMove(bot, unit, destination, force);
			}
		}

		bool ShouldEnterFight(Actor target)
		{
			var radiusSq = Info.FightTriggerRadius * Info.FightTriggerRadius;
			return activeUnits.Any(a => CanAttackActor(a, target) && (a.Location - target.Location).LengthSquared <= radiusSq);
		}

		void ExecuteRiskPlannedMove(IBot bot, CPos objective)
		{
			// one strategic route decision belongs to the Ground group, not to every soldier.
			// The same plan is reused for MoveRefreshInterval; native OpenRA movement owns execution
			// between those strategic refreshes.
			var movers = activeUnits.Where(a => !mcvRightOfWayUnits.Contains(a)).OrderBy(a => a.ActorID).ToArray();
			if (movers.Length == 0)
				return;

			hasLastSafeMoveAnchor = true;
			lastSafeMoveAnchor = GetGroupCenter(movers);

			if (!TryGetGroundGroupMovePlan(movers, objective, out var destination))
			{
				// Replace any stale dangerous group move once, then wait for the next bounded
				// strategic refresh instead of retrying the same plan every 25 WT.
				foreach (var unit in movers)
					IssueAttackMove(bot, unit, unit.Location, false);
				return;
			}

			foreach (var unit in movers)
				IssueAttackMove(bot, unit, destination, false);
		}

		bool TryGetGroundGroupMovePlan(Actor[] movers, CPos objective, out CPos destination)
		{
			if (hasGroupMovePlanAttempt && groupMovePlanObjective == objective && world.WorldTick < nextGroupMovePlanTick)
			{
				destination = groupMovePlanDestination;
				return groupMovePlanValid;
			}

			hasGroupMovePlanAttempt = true;
			groupMovePlanObjective = objective;
			nextGroupMovePlanTick = world.WorldTick + Info.MoveRefreshInterval;
			groupMovePlanValid = TryPlanGroundGroupDestination(movers, objective, out groupMovePlanDestination);
			destination = groupMovePlanDestination;
			return groupMovePlanValid;
		}

		void ExecuteFightMicro(IBot bot, Actor missionTarget)
		{
			using var fransPerf = FransBotLog.Profile(world, player, "Ground.FightMicro");
			// No RiskModel calls are allowed in this method.
			var visible = combatIntelService.VisibleEnemies.Where(IsVisibleEnemy).ToArray();
			var radiusSq = Info.FightMicroRadius * Info.FightMicroRadius;
			foreach (var unit in activeUnits.Where(IsLiveActor).Where(a => !mcvRightOfWayUnits.Contains(a)).OrderBy(a => a.ActorID))
			{
				var crush = FindLocalCrushTarget(unit, visible);
				if (crush != null)
				{
					// Local crush is an explicit FIGHT special case: no far-side target and no independent mission.
					bot.QueueOrder(new Order("Move", unit, Target.FromCell(world, crush.Location), false));
					continue;
				}

				var combatThreat = visible
					.Where(combatIntelService.IsTacticalCombatThreat)
					.Where(enemy => (enemy.Location - unit.Location).LengthSquared <= radiusSq && CanAttackActor(unit, enemy))
					.OrderBy(enemy => (enemy.Location - unit.Location).LengthSquared)
					.ThenBy(enemy => enemy.ActorID)
					.FirstOrDefault();
				var chosen = combatThreat ?? (missionTarget != null && IsVisibleEnemy(missionTarget) && CanAttackActor(unit, missionTarget)
					? missionTarget
					: visible.Where(enemy => (enemy.Location - unit.Location).LengthSquared <= radiusSq && CanAttackActor(unit, enemy))
						.OrderBy(enemy => (enemy.Location - unit.Location).LengthSquared).ThenBy(enemy => enemy.ActorID).FirstOrDefault());
				if (chosen == null)
					continue;

				if (lastFightTarget.TryGetValue(unit, out var oldTarget) && oldTarget == chosen.ActorID &&
					lastFightOrderWorldTick.TryGetValue(unit, out var last) && world.WorldTick - last < Info.FightRefreshInterval)
					continue;

				bot.QueueOrder(new Order("Attack", unit, Target.FromActor(chosen), false));
				lastFightTarget[unit] = chosen.ActorID;
				lastFightOrderWorldTick[unit] = world.WorldTick;
			}
		}

		Actor FindLocalCrushTarget(Actor crusher, IEnumerable<Actor> visible)
		{
			if (!IsLiveActor(crusher))
				return null;

			var radiusSq = Info.LocalCrushRadius * Info.LocalCrushRadius;
			return visible
				.Where(enemy => enemy.Info.HasTraitInfo<MobileInfo>() && (enemy.Location - crusher.Location).LengthSquared <= radiusSq)
				.Where(enemy => CanCrushTarget(crusher, enemy))
				.OrderBy(enemy => (enemy.Location - crusher.Location).LengthSquared)
				.ThenBy(enemy => enemy.ActorID)
				.FirstOrDefault();
		}

		static bool CanCrushTarget(Actor crusher, Actor target)
		{
			if (!IsLiveActor(crusher) || !IsLiveActor(target))
				return false;

			var mobile = crusher.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.Locomotor == null || mobile.Locomotor.Info.Crushes.IsEmpty)
				return false;
			foreach (var crushable in target.Crushables)
				if (crushable.CrushableBy(target, crusher, mobile.Locomotor.Info.Crushes))
					return true;
			return false;
		}

		void ExecuteForwardMove(IBot bot)
		{
			if (!TryGetForwardObjective(out var objective))
				return;

			var movers = managedUnits.Where(a => a.IsIdle && !mcvRightOfWayUnits.Contains(a) && a != reconRetreatActor && !raidRecoveryOrigins.ContainsKey(a) &&
				commanderCoreService.IsActorAvailableForBidder(FransCommanderKind.Ground, BidderKey, a)).OrderBy(a => a.ActorID).ToArray();
			if (movers.Length == 0 || !TryGetGroundGroupMovePlan(movers, objective, out var destination))
				return;

			activeObjective = objective;
			activeOrder = FransCommanderOrder.Move;
			activeOrderStartedWorldTick = world.WorldTick;
			var localStandbyRadius = Info.RetreatAssemblyRadius + 4;
			var localStandbyRadiusSq = localStandbyRadius * localStandbyRadius;
			foreach (var unit in movers)
			{
				var unitDestination = destination;
				// any idle Ground force that has reached its strategic waiting objective
				// spreads into traffic-safe standby slots instead of piling onto one exact cell.
				if ((unit.Location - objective).LengthSquared <= localStandbyRadiusSq)
					unitDestination = GetOrAssignAnchorStandbySlot(unit, objective);

				if ((unit.Location - unitDestination).LengthSquared <= 1)
					continue;
				IssueAttackMove(bot, unit, unitDestination, false);
			}
		}

		bool TryGetForwardObjective(out CPos objective)
		{
			// territorial SECURE and idle-army staging are separate. General exposes
			// a Forward Anchor only while fair CombatIntel still knows an enemy building or
			// Ground-combat contact near secured territory. Empty islands therefore keep MCV/
			// foothold permission without attracting the whole idle Ground army.
			if (generalService.TryGetLatestGroundAnchor(out objective))
				return true;

			// Before the first successful SECURE, use the existing strategic front fallbacks.
			if (baseBuilderService?.StrategicForwardTarget is CPos front)
			{
				objective = front;
				return true;
			}

			var priorities = strategicMapService?.GetStrategicPrioritySectors(1);
			if (priorities != null && priorities.Count > 0)
			{
				objective = priorities[0].Target;
				return true;
			}

			objective = default;
			return false;
		}

		void RememberMissionAnchor(FransActiveMission mission)
		{
			hasMissionAnchorPoint = mission.HasAnchorPoint;
			missionAnchorPoint = mission.HasAnchorPoint ? mission.AnchorPoint : default;
		}

		bool IsGroundRecoveryReady(Actor unit)
		{
			if (unit == null || !unit.IsInWorld || unit.IsDead)
				return false;
			// Infantry and other actors without native Repairable cannot use FIX and therefore
			// regroup normally. Repairable damaged actors count only after native repair finishes.
			return unit.TraitOrDefault<Repairable>() == null || unit.GetDamageState() <= DamageState.Undamaged;
		}

		void RouteRetreatUnit(IBot bot, Actor unit, bool forceMove)
		{
			if (!IsLiveActor(unit))
				return;

			var repairable = unit.TraitOrDefault<Repairable>();
			if (repairable != null && unit.GetDamageState() > DamageState.Undamaged)
			{
				var repairBuilding = repairable.FindRepairBuilding(unit);
				if (repairBuilding != null)
				{
					// Do not restart OpenRA's native repair/resupply activity while it is already moving/docked.
					if (unit.IsIdle)
						bot.QueueOrder(new Order("Repair", unit, Target.FromActor(repairBuilding), false));
					return;
				}
			}

			IssueAttackMove(bot, unit, GetOrAssignAnchorStandbySlot(unit, retreatAnchorPoint), forceMove);
		}

		void EnsureAnchorStandbyCenter(CPos anchor)
		{
			if (hasAnchorStandbyCenter && anchorStandbyCenter == anchor)
				return;
			anchorStandbySlots.Clear();
			groundStagingReservationTick = int.MinValue;
			hasAnchorStandbyCenter = true;
			anchorStandbyCenter = anchor;
		}

		CPos GetOrAssignAnchorStandbySlot(Actor unit, CPos anchor)
		{
			if (!IsLiveActor(unit))
				return anchor;

			EnsureAnchorStandbyCenter(anchor);
			if (anchorStandbySlots.TryGetValue(unit, out var existing) && IsUsableRecoverySlot(unit, existing, true))
				return existing;

			anchorStandbySlots.Remove(unit);
			var mobile = unit?.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused)
				return unit != null ? unit.Location : anchor;

			var used = anchorStandbySlots.Where(p => p.Key != null && p.Key.IsInWorld && !p.Key.IsDead)
				.Select(p => p.Value).ToHashSet();
			var allCandidates = world.Map.FindTilesInAnnulus(anchor, Info.RetreatRecoverySlotMinimumRadius, Info.RetreatAssemblyRadius)
				.Where(world.Map.Contains)
				.OrderBy(c => ((long)(c.X - anchor.X) * 73856093L + (long)(c.Y - anchor.Y) * 19349663L + unit.ActorID * 83492791L) & 0x7fffffff)
				.ThenBy(c => (c - unit.Location).LengthSquared)
				.ThenBy(c => c.X)
				.ThenBy(c => c.Y)
				.ToArray();
			var uniqueCandidates = allCandidates.Where(c => !used.Contains(c)).ToArray();

			// First choice: unique and fully traffic-safe -- passable, outside the active MCV lane,
			// away from FACT/PROC/production exits, and clear of resource cells + harvester margin.
			var slot = uniqueCandidates.Where(c => IsUsableRecoverySlot(unit, c, true)).Select(c => (CPos?)c).FirstOrDefault();
			if (!slot.HasValue)
				slot = uniqueCandidates.Where(c => IsUsableRecoverySlot(unit, c, false)).Select(c => (CPos?)c).FirstOrDefault();

			// Very large armies may exhaust unique cells. Reuse the least-crowded SAFE slot before
			// ever falling back onto the logical Anchor Point inside the economy.
			if (!slot.HasValue)
				slot = allCandidates.Where(c => IsUsableRecoverySlot(unit, c, true))
					.OrderBy(c => anchorStandbySlots.Values.Count(v => v == c))
					.ThenBy(c => (c - unit.Location).LengthSquared)
					.Select(c => (CPos?)c).FirstOrDefault();
			if (!slot.HasValue)
				slot = allCandidates.Where(c => IsUsableRecoverySlot(unit, c, false))
					.OrderBy(c => anchorStandbySlots.Values.Count(v => v == c))
					.ThenBy(c => (c - unit.Location).LengthSquared)
					.Select(c => (CPos?)c).FirstOrDefault();

			if (slot.HasValue)
			{
				anchorStandbySlots[unit] = slot.Value;
				groundStagingReservationTick = int.MinValue;
				return slot.Value;
			}

			// Never deliberately park a unit on an unsafe logical anchor. If no safe slot exists,
			// leave it where it is and retry after the world/traffic snapshot changes.
			return IsUsableRecoverySlot(unit, anchor, false) ? anchor : unit.Location;
		}

		void RefreshStandbyTrafficStructureCells()
		{
			combatIntelService.EnsureCurrentSnapshot();
			if (standbyTrafficStructureSnapshotTick == combatIntelService.SnapshotWorldTick)
				return;

			standbyTrafficStructureSnapshotTick = combatIntelService.SnapshotWorldTick;
			standbyTrafficStructureCells = combatIntelService.OwnedActors
				.Where(a => a != null && a.IsInWorld && !a.IsDead && Info.StandbyTrafficStructureTypes.Contains(a.Info.Name))
				.OrderBy(a => a.ActorID)
				.Select(a => a.Location)
				.ToArray();
		}

		bool IsUsableRecoverySlot(Actor unit, CPos cell, bool requireResourceMargin)
		{
			if (!IsLiveActor(unit))
				return false;

			var mobile = unit.TraitOrDefault<Mobile>();
			if (mobile == null || !world.Map.Contains(cell) ||
				!mobile.CanEnterCell(cell, check: BlockedByActor.Immovable) || !mobile.CanStayInCell(cell))
				return false;

			if (expansionStateService != null && expansionStateService.TryGetMcvDeployRightOfWay(out var mcvCenter, out var mcvRadius) &&
				(cell - mcvCenter).LengthSquared <= (mcvRadius + 1) * (mcvRadius + 1))
				return false;

			RefreshStandbyTrafficStructureCells();
			if (Info.StandbyTrafficStructureClearanceRadius > 0)
			{
				var structureRadiusSq = Info.StandbyTrafficStructureClearanceRadius * Info.StandbyTrafficStructureClearanceRadius;
				if (standbyTrafficStructureCells.Any(c => (c - cell).LengthSquared <= structureRadiusSq))
					return false;
			}

			if (resourceLayer == null)
				return true;
			if (resourceLayer.GetResource(cell).Type != null)
				return false;
			if (!requireResourceMargin || Info.RetreatResourceClearanceRadius <= 0)
				return true;

			return !world.Map.FindTilesInCircle(cell, Info.RetreatResourceClearanceRadius)
				.Where(world.Map.Contains)
				.Any(c => resourceLayer.GetResource(c).Type != null);
		}

		public bool IntersectsGroundStagingReservation(CPos topLeft, int width, int height)
		{
			if (width <= 0 || height <= 0)
				return false;

			RefreshGroundStagingReservation();
			if (groundStagingReservationCells.Count == 0)
				return false;

			for (var x = topLeft.X; x < topLeft.X + width; x++)
				for (var y = topLeft.Y; y < topLeft.Y + height; y++)
					if (groundStagingReservationCells.Contains(new CPos(x, y)))
						return true;

			return false;
		}

		void RefreshGroundStagingReservation()
		{
			if (groundStagingReservationTick == world.WorldTick)
				return;
			groundStagingReservationTick = world.WorldTick;
			groundStagingReservationCells.Clear();

			if (!hasAnchorStandbyCenter)
				return;

			var anchor = anchorStandbyCenter;
			var presenceRadius = Info.RetreatAssemblyRadius + 4;
			var presenceRadiusSq = presenceRadius * presenceRadius;
			var stagedUnitCount = managedUnits.Count(a => (a.Location - anchor).LengthSquared <= presenceRadiusSq);
			if (stagedUnitCount < Info.StagingReservationMinimumGroundUnits)
				return;

			// Keep the actual occupied/distributed standby cells and a small maneuver core free.
			foreach (var slot in anchorStandbySlots.Where(p => p.Key != null && p.Key.IsInWorld && !p.Key.IsDead &&
				(p.Key.Location - anchor).LengthSquared <= presenceRadiusSq).Select(p => p.Value))
				if (world.Map.Contains(slot))
					groundStagingReservationCells.Add(slot);
			foreach (var cell in world.Map.FindTilesInCircle(anchor, Info.StagingReservationCoreRadius).Where(world.Map.Contains))
				groundStagingReservationCells.Add(cell);

			if (!TryGetStagingEgressTarget(anchor, out var target))
				return;

			var dx = target.X - anchor.X;
			var dy = target.Y - anchor.Y;
			var denominator = Math.Max(Math.Abs(dx), Math.Abs(dy));
			if (denominator <= 0)
				return;

			for (var step = 0; step <= Info.StagingEgressLengthCells; step++)
			{
				var center = new CPos(
					anchor.X + (int)Math.Round((double)dx * step / denominator),
					anchor.Y + (int)Math.Round((double)dy * step / denominator));
				if (!world.Map.Contains(center))
					continue;

				for (var ox = -Info.StagingEgressHalfWidthCells; ox <= Info.StagingEgressHalfWidthCells; ox++)
					for (var oy = -Info.StagingEgressHalfWidthCells; oy <= Info.StagingEgressHalfWidthCells; oy++)
					{
						var cell = new CPos(center.X + ox, center.Y + oy);
						if (world.Map.Contains(cell))
							groundStagingReservationCells.Add(cell);
					}
			}
		}

		bool TryGetStagingEgressTarget(CPos anchor, out CPos target)
		{
			const int MinimumDirectionDistanceSquared = 16;
			if (activeTargetActorId != 0 && (activeObjective - anchor).LengthSquared > MinimumDirectionDistanceSquared)
			{
				target = activeObjective;
				return true;
			}

			if (baseBuilderService?.StrategicForwardTarget is CPos front &&
				(front - anchor).LengthSquared > MinimumDirectionDistanceSquared)
			{
				target = front;
				return true;
			}

			var priorities = strategicMapService?.GetStrategicPrioritySectors(3);
			if (priorities != null)
			{
				var priority = priorities.Where(p => (p.Target - anchor).LengthSquared > MinimumDirectionDistanceSquared).ToArray();
				if (priority.Length > 0)
				{
					target = priority[0].Target;
					return true;
				}
			}

			// Last deterministic fallback: reserve outward from the economic core. This is most
			// useful for a main-base staging point before the StrategicMap has a strong frontier.
			if (baseBuilderService != null)
			{
				var home = baseBuilderService.StrategicBaseCenter;
				var dx = anchor.X - home.X;
				var dy = anchor.Y - home.Y;
				if (dx != 0 || dy != 0)
				{
					var bounds = world.Map.Bounds;
					target = new CPos(
						Math.Clamp(anchor.X + dx * Info.StagingEgressLengthCells, bounds.Left, bounds.Right - 1),
						Math.Clamp(anchor.Y + dy * Info.StagingEgressLengthCells, bounds.Top, bounds.Bottom - 1));
					return target != anchor;
				}
			}

			target = default;
			return false;
		}

		void IssueAttackMoveGroup(IBot bot, CPos destination, bool force)
		{
			foreach (var unit in activeUnits.Where(a => !mcvRightOfWayUnits.Contains(a)).OrderBy(a => a.ActorID))
				IssueAttackMove(bot, unit, destination, force);
		}

		void IssueAttackMove(IBot bot, Actor unit, CPos destination, bool force)
		{
			if (!IsLiveActor(unit))
				return;

			if (!force && lastMoveDestination.TryGetValue(unit, out var old) && old == destination)
			{
				// native movement owns an in-progress MOVE. Never reset the same path
				// merely because the strategic refresh timer elapsed. Reassert only if the actor
				// has actually become idle/stalled, and even then respect the retry interval.
				if (!unit.IsIdle || (lastMoveWorldTick.TryGetValue(unit, out var last) && world.WorldTick - last < Info.MoveRefreshInterval))
					return;
			}
			bot.QueueOrder(new Order("AttackMove", unit, Target.FromCell(world, destination), false));
			lastMoveDestination[unit] = destination;
			lastMoveWorldTick[unit] = world.WorldTick;
		}

		bool TryGetTransportLossGroundObjective(uint incidentId, CPos lossCell, FransSiteIntel siteIntel, IReadOnlyCollection<Actor> candidates, out CPos objective, out int landmassId)
		{
			using var objectivePerf = FransBotLog.Profile(world, player, "Ground.LstLossObjective");
			var started = Stopwatch.GetTimestamp();
			var localUnitCount = 0;
			var destinationCellCount = 0;
			var logicalNativePathAttempts = 0;
			var physicalNativePathEvaluations = 0;
			var proofMemoHits = 0;
			var successfulAttemptIndex = 0;
			uint selectedSubjectActorId = 0;
			CPos? selectedObjective = null;
			var proofMemo = new Dictionary<LstLossNativePathProofKey, bool>();
			objective = default;
			landmassId = 0;
			if (candidates == null || candidates.Count == 0)
				return false;

			// A maritime loss does not itself prove Ground feasibility. Ground may bid only when
			// raw SiteIntel contains a Ground-located combat/defense contact and committed Ground
			// already exists on that same landmass with a safe native Ground route. GroundTransfer
			// explicitly ignores this mission type, preventing SECURE -> LST -> blocked SECURE loops.
			CPos[] threatCells;
			using (FransBotLog.Profile(world, player, "Ground.LstLossThreatSetup"))
				threatCells = (siteIntel.Actors ?? Array.Empty<FransSiteIntelActor>())
					.Where(a => a.IsCombatActor || a.IsDefensiveBuilding)
					.Where(a => strategicMapService.TryGetGroundLandmassId(a.Cell, out _))
					.OrderBy(a => (a.Cell - lossCell).LengthSquared)
					.ThenBy(a => a.ActorId)
					.Select(a => a.Cell)
					.Distinct()
					.ToArray();

			using (FransBotLog.Profile(world, player, "Ground.LstLossSubjectScan"))
			foreach (var threatCell in threatCells)
			{
				if (!strategicMapService.TryGetGroundLandmassId(threatCell, out var threatLandmass))
					continue;

				var localUnits = candidates
					.Where(IsLiveActor)
					.Where(a => strategicMapService.TryGetGroundLandmassId(a.Location, out var lm) && lm == threatLandmass)
					.OrderBy(a => (a.Location - threatCell).LengthSquared).ThenBy(a => a.ActorID)
					.ToArray();
				localUnitCount += localUnits.Length;
				if (localUnits.Length == 0)
					continue;

				foreach (var subject in localUnits)
				{
					var mobile = subject.TraitOrDefault<Mobile>();
					if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused)
						continue;

					var cells = new[] { threatCell }.Concat(world.Map.FindTilesInCircle(threatCell, Math.Min(4, Info.SecureThreatRadius)))
						.Where(world.Map.Contains)
						.Where(c => strategicMapService.TryGetGroundLandmassId(c, out var lm) && lm == threatLandmass)
						.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
						.OrderBy(c => (c - threatCell).LengthSquared)
						.ThenBy(c => (c - subject.Location).LengthSquared)
						.ThenBy(c => c.X).ThenBy(c => c.Y);

					foreach (var cell in cells)
					{
						destinationCellCount++;
						logicalNativePathAttempts++;
						var proofKey = new LstLossNativePathProofKey(subject.ActorID, subject.Location, cell);
						if (!proofMemo.TryGetValue(proofKey, out var feasible))
						{
							physicalNativePathEvaluations++;
							using (FransBotLog.Profile(world, player, "Ground.LstLossNativePathProbe"))
								feasible = TryPlanGroundGroupDestination(new[] { subject }, cell, out _);
							proofMemo.Add(proofKey, feasible);
						}
						else
							proofMemoHits++;
						if (feasible)
						{
							objective = cell;
							landmassId = threatLandmass;
							successfulAttemptIndex = logicalNativePathAttempts;
							selectedSubjectActorId = subject.ActorID;
							selectedObjective = cell;
							LogSummary();
							return true;
						}
					}
				}
			}

			LogSummary();
			return false;

			void LogSummary()
			{
				var elapsedMs = (Stopwatch.GetTimestamp() - started) * 1000.0 / Stopwatch.Frequency;
				if (elapsedMs < 2 ||
					(lstLossObjectiveDiagnosticNextTick.TryGetValue(incidentId, out var nextTick) && world.WorldTick < nextTick))
					return;

				lstLossObjectiveDiagnosticNextTick[incidentId] = world.WorldTick + 500;
				FransBotLog.BotDebug(world,
					"{0}: [LST-LOSS OBJECTIVE PERF] incident={1} lossCell={2} threatCells={3} candidates={4} localUnits={5} destinationCells={6} nativePathAttempts={7} logicalNativePathAttempts={8} physicalNativePathEvaluations={9} proofMemoHits={10} proofMemoEntries={11} successfulAttemptIndex={12} selectedSubject={13} selectedObjective={14} elapsedMs={15:F2}.",
					player, incidentId, lossCell, threatCells.Length, candidates.Count, localUnitCount, destinationCellCount,
					logicalNativePathAttempts, logicalNativePathAttempts, physicalNativePathEvaluations, proofMemoHits, proofMemo.Count,
					successfulAttemptIndex, selectedSubjectActorId, selectedObjective, elapsedMs);
			}
		}

		bool TryPlanGroundGroupDestination(IReadOnlyCollection<Actor> units, CPos objective, out CPos destination)
		{
			destination = objective;
			if (units == null || units.Count == 0)
				return false;

			var subject = units.OrderBy(a => (a.Location - objective).LengthSquared).ThenBy(a => a.ActorID).First();
			if (strategicMapService.TryGetStrategicSectorRoute(subject.Location, objective, FransStrategicMovementLayer.Ground,
				FransStrategicRoutePolicy.Safe, out var waypoints) && waypoints != null && waypoints.Count > 0)
			{
				var route = riskModelService.EvaluateRoute(subject, waypoints, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced);
				if (!route.IsCritical)
				{
					destination = waypoints.Count > 1 ? waypoints[1] : waypoints[0];
					return true;
				}
			}

			var direct = riskModelService.EvaluateDirectRoute(subject, subject.Location, objective,
				FransRiskRole.GroundCombat, FransRiskTolerance.Balanced);
			return !direct.IsCritical;
		}

		FransRouteRiskAssessment EvaluateMoveRisk(Actor subject, CPos from, CPos to)
		{
			if (strategicMapService.TryGetStrategicSectorRoute(from, to, FransStrategicMovementLayer.Ground,
				FransStrategicRoutePolicy.Safe, out var route) && route != null && route.Count > 0)
				return riskModelService.EvaluateRoute(subject, route, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced);
			return riskModelService.EvaluateDirectRoute(subject, from, to, FransRiskRole.GroundCombat, FransRiskTolerance.Balanced);
		}

		CPos? FindGroundReconCell(Actor unit, CPos desired, bool requireSameLandmass = false)
		{
			if (!IsLiveActor(unit))
				return null;

			var mobile = unit.TraitOrDefault<Mobile>();
			if (mobile == null)
				return null;

			var sourceLandmass = 0;
			if (requireSameLandmass &&
				(!strategicMapService.TryGetGroundLandmassId(unit.Location, out sourceLandmass) ||
				 !strategicMapService.TryGetGroundLandmassId(desired, out var targetLandmass) || targetLandmass != sourceLandmass))
				return null;

			if (world.Map.Contains(desired) &&
				(!requireSameLandmass || (strategicMapService.TryGetGroundLandmassId(desired, out var desiredLandmass) && desiredLandmass == sourceLandmass)) &&
				mobile.CanEnterCell(desired, check: BlockedByActor.Immovable) && mobile.CanStayInCell(desired))
				return desired;

			var radius = Math.Max(2, commanderCoreService.GetReconVisionCells(unit));
			return world.Map.FindTilesInCircle(desired, radius)
				.Where(world.Map.Contains)
				.Where(c => !requireSameLandmass || (strategicMapService.TryGetGroundLandmassId(c, out var landmass) && landmass == sourceLandmass))
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.OrderBy(c => (c - desired).LengthSquared)
				.ThenBy(c => (c - unit.Location).LengthSquared)
				.ThenBy(c => c.X)
				.ThenBy(c => c.Y)
				.Select(c => (CPos?)c)
				.FirstOrDefault();
		}

		void ResetPioneerReconProgress(Actor actor, CPos objective)
		{
			reconPioneerBestDistanceSquared = actor == null ? int.MaxValue : (actor.Location - objective).LengthSquared;
			reconPioneerLastProgressWorldTick = world.WorldTick;
		}

		bool PioneerReconProgressTimedOut(Actor actor, CPos objective)
		{
			if (!reconPioneerValidationActive || !IsLiveActor(actor))
				return false;

			var distanceSquared = (actor.Location - objective).LengthSquared;
			if (distanceSquared < reconPioneerBestDistanceSquared)
			{
				reconPioneerBestDistanceSquared = distanceSquared;
				reconPioneerLastProgressWorldTick = world.WorldTick;
				return false;
			}

			return reconPioneerLastProgressWorldTick >= 0 &&
				world.WorldTick - reconPioneerLastProgressWorldTick >= PioneerReconNoProgressTimeoutTicks;
		}

		void ExecuteReconMission(IBot bot, FransActiveMission mission)
		{
			var changed = activeTargetActorId != mission.TargetActorId || activeMissionType != FransMissionType.Recon;
			if (changed)
			{
				ResetReconState();
				ResetTacticalRetreatStateForNewMission();
				var committed = ResolveCommittedGroundActors(mission);
				var selected = committed.Length == 1 && committed[0] != reconRetreatActor && committed[0].TraitOrDefault<Cargo>() == null
					? committed[0] : null;
				if (selected == null)
				{
					AbortReconMission("selected Ground recon unit is no longer available");
					return;
				}

				var missionObjective = mission.LastVisibleTargetCell;
				reconPioneerValidationActive = false;
				if (expansionStateService != null &&
					expansionStateService.TryGetPioneerReconObjectiveNear(missionObjective, out var pioneerObjective))
				{
					reconPioneerValidationActive = true;
					missionObjective = pioneerObjective;
				}
				var start = FindGroundReconCell(selected, missionObjective, reconPioneerValidationActive);
				if (!start.HasValue)
				{
					AbortReconMission(reconPioneerValidationActive
						? "Ground cannot reach PIONEER exact-objective RECON; release for Air/other capability"
						: "selected Ground recon unit has no reachable patrol start cell");
					return;
				}

				activeTargetActorId = mission.TargetActorId;
				activeMissionType = FransMissionType.Recon;
				activeObjective = missionObjective;
				activeOrder = FransCommanderOrder.Move;
				activeOrderStartedWorldTick = world.WorldTick;
				activeUnits.Clear();
				activeUnits.Add(selected);
				reconActor = selected;
				if (reconPioneerValidationActive)
					ResetPioneerReconProgress(selected, missionObjective);
				selected.TraitOrDefault<AutoTarget>()?.SetStance(selected, UnitStance.HoldFire);
				reconOrigin = selected.Location;
				reconStart = start.Value;
				hasReconSearchWaypoint = false;
				reconLoggedContactIds.Clear();
				FransBotLog.BotDebug(world,
					"{0}: Ground Commander accepts persistent RECON MineCluster {1} with ONE {2} {3}; plain MOVE from {4} to patrol start {5}. The mission has no coverage-completion threshold.",
					player, mission.TargetActorId, selected.Info.Name, selected.ActorID, reconOrigin, reconStart);
			}

			if (reconActor == null || !reconActor.IsInWorld || reconActor.IsDead || !managedUnits.Contains(reconActor))
			{
				AbortReconMission("Ground recon unit died or left Commander ownership");
				return;
			}

			if (expansionStateService != null && expansionStateService.TryGetPioneerReconObjectiveNear(activeObjective, out var exactPioneerObjective))
			{
				var pioneerWasActive = reconPioneerValidationActive;
				reconPioneerValidationActive = true;
				if (exactPioneerObjective != activeObjective)
				{
					var redirected = FindGroundReconCell(reconActor, exactPioneerObjective, requireSameLandmass: true);
					if (!redirected.HasValue)
					{
						AbortReconMission("Ground cannot reach newly prioritized PIONEER exact objective; release for Air/other capability");
						return;
					}
					activeObjective = exactPioneerObjective;
					reconStart = redirected.Value;
					ResetPioneerReconProgress(reconActor, activeObjective);
					activeOrder = FransCommanderOrder.Move;
					hasReconSearchWaypoint = false;
					reconActor.CancelActivity();
					FransBotLog.BotDebug(world, "{0}: Ground RECON {1} redirects to PIONEER exact objective {2}; persistent fan probing is temporarily superseded until the exact ore cell is scout-cleared.", player, activeTargetActorId, activeObjective);
				}
				else if (!pioneerWasActive)
					ResetPioneerReconProgress(reconActor, activeObjective);
			}
			else if (reconPioneerValidationActive)
			{
				commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, "PIONEER exact-objective RECON completed");
				FransBotLog.BotDebug(world, "{0}: Ground PIONEER exact-objective RECON {1} completed at {2}; releases the one-shot validation mission and returns the scout to normal ownership.", player, activeTargetActorId, activeObjective);
				ResetActiveMission();
				return;
			}

			if (PioneerReconProgressTimedOut(reconActor, activeObjective))
			{
				AbortReconMission($"PIONEER exact-objective RECON made no approach progress for {PioneerReconNoProgressTimeoutTicks} WT; release for another capability");
				return;
			}

			if (ReconHealthBelowRetreatThreshold(reconActor, out var healthPercent))
			{
				BeginReconRetreat(bot, reconActor, $"health fell to {healthPercent}% (< {commanderCoreService.ReconRetreatHealthPercent}%)");
				return;
			}

			if (activeOrder == FransCommanderOrder.Move)
			{
				if ((reconActor.Location - reconStart).LengthSquared <= 1)
				{
					var vision = commanderCoreService.GetReconVisionCells(reconActor);
					if (vision <= 0)
					{
						AbortReconMission("Ground recon unit lost usable vision before patrol start");
						return;
					}
					reconSearchSpiral.Reset(reconStart, vision);
					activeOrder = FransCommanderOrder.Search;
					activeOrderStartedWorldTick = world.WorldTick;
					hasReconSearchWaypoint = false;
					FransBotLog.BotDebug(world,
						"{0}: Ground RECON {1} begins persistent probing at {2}: vision {3}, spiral spacing {4}, {5} queued plain-Move waypoints per packet. No coverage state is tracked.",
						player, activeTargetActorId, reconStart, vision, reconSearchSpiral.SpacingCells, commanderCoreService.ReconWaypointBatchSize);
				}
				else
					IssuePlainMove(bot, reconActor, reconStart, false);
				return;
			}

			if (activeOrder != FransCommanderOrder.Search)
				return;

			if (TryGetReconContact(reconActor, out var contact) && reconLoggedContactIds.Add(contact.ActorID))
				FransBotLog.BotDebug(world,
					"{0}: Ground RECON MineCluster {1} sees incidental enemy {2} {3} at {4}; plain-Move probing continues and RECON never attacks the contact.",
					player, activeTargetActorId, contact.Info.Name, contact.ActorID, contact.Location);

			// Commander is silent while OpenRA executes the queued packet. Refill only after the
			// final waypoint was reached or native movement became idle/stalled.
			if (hasReconSearchWaypoint && !reconActor.IsIdle &&
				(reconActor.Location - reconSearchWaypoint).LengthSquared > 1)
				return;

			if (TryQueueReconWaypointPacket(bot, reconActor, c => FindGroundReconCell(reconActor, c)))
				return;

			// A finite map can exhaust the unique spiral points. Restart the deterministic spiral
			// around the same MineCluster so RECON remains a persistent patrol instead of completing.
			var restartVision = commanderCoreService.GetReconVisionCells(reconActor);
			if (restartVision > 0)
			{
				reconSearchSpiral.Reset(reconStart, restartVision);
				hasReconSearchWaypoint = false;
				if (TryQueueReconWaypointPacket(bot, reconActor, c => FindGroundReconCell(reconActor, c)))
					return;
			}

			AbortReconMission("persistent Ground RECON has no reachable spiral waypoint");
		}

		bool TryGetReconContact(Actor unit, out Actor contact)
		{
			contact = null;
			var vision = commanderCoreService.GetReconVisionCells(unit);
			if (vision <= 0)
				return false;
			var radiusSq = vision * vision;
			contact = combatIntelService.VisibleEnemies
				.Where(IsVisibleEnemy)
				.Where(e => (e.Location - unit.Location).LengthSquared <= radiusSq)
				.OrderBy(e => (e.Location - unit.Location).LengthSquared)
				.ThenBy(e => e.ActorID)
				.FirstOrDefault();
			return contact != null;
		}

		bool ReconHealthBelowRetreatThreshold(Actor unit, out int percent)
		{
			percent = 100;
			if (!IsLiveActor(unit))
				return false;

			var health = unit.TraitOrDefault<Health>();
			if (health == null || health.MaxHP <= 0)
				return false;

			percent = Math.Clamp((int)((long)Math.Max(0, health.HP) * 100 / health.MaxHP), 0, 100);
			return (long)health.HP * 100 < (long)health.MaxHP * commanderCoreService.ReconRetreatHealthPercent;
		}

		bool TryQueueReconWaypointPacket(IBot bot, Actor unit, Func<CPos, CPos?> resolveWaypoint)
		{
			var waypoints = new List<CPos>(commanderCoreService.ReconWaypointBatchSize);
			var cursor = unit.Location;
			for (var i = 0; i < commanderCoreService.ReconWaypointBatchSize; i++)
			{
				if (!reconSearchSpiral.TryGetNextWaypoint(world, resolveWaypoint, cursor, out var waypoint))
					break;
				waypoints.Add(waypoint);
				cursor = waypoint;
			}

			if (waypoints.Count == 0)
				return false;

			for (var i = 0; i < waypoints.Count; i++)
				bot.QueueOrder(new Order("Move", unit, Target.FromCell(world, waypoints[i]), i > 0));

			reconSearchWaypoint = waypoints[^1];
			hasReconSearchWaypoint = true;
			lastMoveDestination[unit] = reconSearchWaypoint;
			lastMoveWorldTick[unit] = world.WorldTick;
			return true;
		}

		void BeginReconRetreat(IBot bot, Actor unit, string reason)
		{
			var targetId = activeTargetActorId;
			var origin = reconOrigin;
			commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, $"RECON -> RETREAT: {reason}");
			reconRetreatActor = unit;
			reconRetreatOrigin = origin;
			PublishTransientReservations();
			FransBotLog.BotDebug(world,
				"{0}: Ground persistent RECON {1} -> RETREAT; lone {2} {3} cancels its queued patrol and returns toward {4} with a non-queued plain Move: {5}. General keeps the RECON target open for a bounded rebid grace; General rotates the empty slot later if no Commander takes it.",
				player, targetId, unit.Info.Name, unit.ActorID, origin, reason);
			ResetActiveMission();
			IssuePlainMove(bot, unit, origin, true);
		}

		void MaintainReconRetreat(IBot bot)
		{
			if (reconRetreatActor == null)
				return;
			if (!reconRetreatActor.IsInWorld || reconRetreatActor.IsDead || !managedUnits.Contains(reconRetreatActor))
			{
				reconRetreatActor = null;
				return;
			}
			if ((reconRetreatActor.Location - reconRetreatOrigin).LengthSquared <= 4)
			{
				FransBotLog.BotDebug(world,
					"{0}: Ground RECON RETREAT complete for {1} at {2}. Unit returns to normal Commander ownership.",
					player, reconRetreatActor, reconRetreatActor.Location);
				reconRetreatActor = null;
				return;
			}
			IssuePlainMove(bot, reconRetreatActor, reconRetreatOrigin, false);
		}

		void AbortReconMission(string reason)
		{
			commandBidService.ReleaseMission(FransCommanderKind.Ground, BidderKey, reason);
			FransBotLog.BotDebug(world,
				"{0}: Ground persistent RECON MineCluster {1} mission aborted without General completion: {2}. Target remains eligible for bounded rebid grace before General slot rotation.",
				player, activeTargetActorId, reason);
			ResetActiveMission();
		}

		void IssueExplicitAttack(IBot bot, Actor unit, Actor target, bool force)
		{
			if (unit == null || target == null || !unit.IsInWorld || unit.IsDead || !IsVisibleEnemy(target))
				return;
			if (!force && lastFightTarget.TryGetValue(unit, out var oldTarget) && oldTarget == target.ActorID &&
				lastFightOrderWorldTick.TryGetValue(unit, out var last) && world.WorldTick - last < Info.FightRefreshInterval)
				return;
			bot.QueueOrder(new Order("Attack", unit, Target.FromActor(target), false));
			lastFightTarget[unit] = target.ActorID;
			lastFightOrderWorldTick[unit] = world.WorldTick;
		}

		void IssuePlainMove(IBot bot, Actor unit, CPos destination, bool force)
		{
			if (unit == null || !unit.IsInWorld || unit.IsDead)
				return;
			if (!force && lastMoveDestination.TryGetValue(unit, out var old) && old == destination)
			{
				if (!unit.IsIdle || (lastMoveWorldTick.TryGetValue(unit, out var last) && world.WorldTick - last < Info.MoveRefreshInterval))
					return;
			}
			bot.QueueOrder(new Order("Move", unit, Target.FromCell(world, destination), false));
			lastMoveDestination[unit] = destination;
			lastMoveWorldTick[unit] = world.WorldTick;
		}

		void ResetReconState()
		{
			// RECON temporarily suppresses native auto-targeting so its plain-Move doctrine cannot
			// turn into an incidental fight. Returning to normal ownership restores the global default.
			if (reconActor != null && reconActor.IsInWorld && !reconActor.IsDead)
			{
				reconActor.TraitOrDefault<AutoTarget>()?.SetStance(reconActor, UnitStance.AttackAnything);
				reconActor.CancelActivity();
			}
			reconActor = null;
			reconOrigin = default;
			reconStart = default;
			reconSearchWaypoint = default;
			hasReconSearchWaypoint = false;
			reconPioneerValidationActive = false;
			reconPioneerBestDistanceSquared = int.MaxValue;
			reconPioneerLastProgressWorldTick = -1;
			reconLoggedContactIds.Clear();
		}

		static bool IsNonCombatHusk(Actor actor)
		{
			// Aircraft crash husks (yak.husk, badr.husk, etc.) can legitimately deal impact
			// damage, but they are wreckage rather than a continuing combat threat. Damage still
			// applies normally; the callback simply must not fan out one Attack order per unit hit.
			return actor?.Info != null && (actor.Info.HasTraitInfo<HuskInfo>() || actor.Info.Name.EndsWith(".husk", StringComparison.OrdinalIgnoreCase));
		}

		static bool IsLiveActor(Actor actor) => actor != null && actor.IsInWorld && !actor.IsDead;

		bool CanAttackActor(Actor attacker, Actor target)
		{
			// Managed-unit snapshots are intentionally reused between bounded refreshes. A unit can
			// be destroyed after the snapshot was built, so never query traits from a stale actor.
			if (!IsLiveActor(attacker) || target == null || !IsVisibleEnemy(target))
				return false;
			var attackTarget = Target.FromActor(target);
			return attacker.TraitsImplementing<AttackBase>()
				.Any(attack => !attack.IsTraitDisabled && !attack.IsTraitPaused && attack.HasAnyValidWeapons(attackTarget));
		}

		bool IsEnemyActor(Actor target) => target?.Owner != null &&
			PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(target.Owner));

		bool IsVisibleEnemy(Actor target)
		{
			return target != null && target.IsInWorld && !target.IsDead && target.OccupiesSpace != null &&
				target.CanBeViewedByPlayer(player) && PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(target.Owner));
		}

		int GetGroundTacticalGroupValue(IEnumerable<Actor> actors)
		{
			long infantryValue = 0;
			long otherValue = 0;
			var infantryCount = 0;
			foreach (var actor in actors ?? Array.Empty<Actor>())
				AddGroundTacticalActor(actor, ref infantryValue, ref infantryCount, ref otherValue);
			return GetGroundTacticalGroupValue(infantryValue, infantryCount, otherValue);
		}

		static int GetCombatValue(Actor actor) => Math.Max(1, actor.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 1);

		void ResetActiveMission()
		{
			activeUnits.Clear();
			activeTargetActorId = 0;
			combinedSecureHoldTargetActorId = 0;
			combinedSecureHoldUntilTick = -1;
			activeObjective = default;
			activeOrder = FransCommanderOrder.Move;
			activeMissionType = FransMissionType.Recon;
			activeOrderStartedWorldTick = world.WorldTick;
			lostContactSinceWorldTick = -1;
			hasMissionAnchorPoint = false;
			missionAnchorPoint = default;
			ResetReconState();
			raidMissionOrigins.Clear();
			cohesionHeldUnits.Clear();
			cohesionFormationSlots.Clear();
			hasCohesionFormationObjective = false;
			cohesionFormationObjective = default;
			raidStrikeIssued = false;
			raidKnownAdditionalDefenseIds.Clear();
			raidCommittedContributionByActor.Clear();
			raidProgressiveAttackActorIds.Clear();
			raidFeasibilityRecheckRequested = false;
			raidDefenseObservedWorldTick = -1;
			raidLastValidatedSurvivorCount = -1;
			raidLocalDefenseActive = false;
			secureInitialAssemblyActive = false;
			secureInitialAssemblyStartedTick = -1;
			secureStaticClearSinceWorldTick = -1;
			secureMarchBestDistanceSquared = int.MaxValue;
			secureMarchLastProgressWorldTick = -1;
			secureRememberedObjective = null;
			secureStaticValidationTargetActorId = 0;
			secureStaticValidationCombatSnapshotWorldTick = -1;
			secureStaticValidationRequiredContribution = 0;
			secureStaticValidationKnownThreat = 0;
			ResetRaidLostTargetSearch(false);
			// do not erase the offensive high-water mark just because one target
			// disappeared or the auction moved to another target. That target churn was what
			// allowed repeated smaller FIGHTs to postpone RETREAT indefinitely.
		}
	}
}
