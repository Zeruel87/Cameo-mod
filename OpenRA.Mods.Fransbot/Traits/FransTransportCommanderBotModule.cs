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
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Pathfinder;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	/// <summary>
	/// Small AirAI-only coordination surface used by FransSpecOps Commander and the
	/// amphibious MCV manager. It does not add or alter any actor rules.
	/// </summary>
	public interface IFransCaptureTransportService
	{
		bool IsHandlingPassenger(Actor passenger);
		bool IsHandlingPassenger(uint passengerActorId);
		bool IsCaptureTargetReserved(Actor target, Actor exceptPassenger);
		bool CanPotentiallyTransport(Actor passenger, Actor target, bool landPathAvailable);
		bool TryRequestCaptureTransport(IBot bot, Actor passenger, Actor target, bool landPathAvailable);
		bool TryConsumeCompletedCaptureTransport(Actor passenger, out Actor target);

		// Reusable SpecOps transport (currently Tanya): insertion keeps the exact physical transport
		// reserved near the drop area, then the specialist can request extraction back toward the
		// original pickup. This reuses the same bounded/cached route planning as capture transport.
		bool CanPotentiallyTransportReusable(Actor passenger, Actor target, bool landPathAvailable);
		bool TryRequestReusableTransport(IBot bot, Actor passenger, Actor target, bool landPathAvailable);
		bool TryConsumeCompletedReusableInsertion(Actor passenger, out Actor target);
		bool TryBeginReusableExtraction(IBot bot, Actor passenger);

		void CancelCaptureTransport(IBot bot, Actor passenger);
		void CancelCaptureTransport(IBot bot, uint passengerActorId);
		int CountTransportedPassengers(string actorType);

		bool IsTransportReserved(Actor transport);
		int MaximumLandingCraftPool { get; }
		int MaximumNonStrategicLandingCraftPool { get; }
		int CountLandingCraftPool(IBot bot);
		bool CanStrategicExpansionClaimTransport(Actor transport);
		bool TryReserveStrategicExpansionTransport(Actor transport, Actor reservationOwner);
		bool TryReserveExternalTransport(Actor transport, Actor reservationOwner);
		void ReleaseExternalTransport(Actor transport, Actor reservationOwner);
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("AirAI-only transport coordinator. Moves real capture units in stock APC/LST/TRAN Cargo, " +
		"then hands the same passenger actor back to FransSpecOps Commander after unloading.")]
	public class FransTransportCommanderBotModuleInfo : ConditionalTraitInfo, Requires<PlayerResourcesInfo>
	{
		[ActorReference]
		[Desc("Passenger actor types this module may transport for SpecOps capture/C4 missions.")]
		public readonly FrozenSet<string> PassengerTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Air transports. Stock RA TRAN accepts Infantry and can land for Cargo loading/unloading.")]
		public readonly FrozenSet<string> AirTransportTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Ground transports used for long same-land capture missions.")]
		public readonly FrozenSet<string> GroundTransportTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Landing craft used when the passenger and target are separated by water.")]
		public readonly FrozenSet<string> LandingCraftTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Transport preference order when more than one type is usable.")]
		public readonly string[] PreferredTransportTypes = [];

		[ActorReference]
		[Desc("Preferred transport order for reusable SpecOps specialists. Remaining normal transport candidates are capability-checked as fallbacks by the same bounded target-owned planner.")]
		public readonly string[] ReusablePreferredTransportTypes = [];

		[Desc("World ticks a reusable SpecOps transport may wait reserved near the insertion point for extraction before releasing itself. Zero disables the timeout.")]
		public readonly int ReusableStandbyTimeout = 3000;

		[Desc("Maximum simultaneous capture-transport missions.")]
		public readonly int MaximumActiveMissions = 2;

		[Desc("Minimum cash plus stored resources before requesting a new transport.")]
		public readonly int MinimumCashForTransportProduction = 1200;

		[Desc("Minimum ticks between repeated production requests for one waiting mission.")]
		public readonly int ProductionRequestCooldown = 250;

		[Desc("Global hard physical+pending TRAN cap shared by reusable SpecOps and ordinary capture transport demand. Once this pool is full, new capture missions wait for an existing transport instead of crowding the Aircraft queue with more identical transports.")]
		public readonly int MaximumAirTransports = 3;

		[Desc("Stricter physical+pending TRAN cap for reusable SpecOps insertion/extraction demand inside the global pool.")]
		public readonly int MaximumReusableSpecOpsAirTransports = 2;

		[Desc("Maximum owned physical + pending ground transports of one capture transport type (Jeep/APC) that capture/SpecOps demand may tolerate before it stops producing more of that type. Existing combat-owned craft still count: capture waits for one to become available or tries another transport domain instead of flooding the Vehicle queue.")]
		public readonly int MaximumGroundTransportsPerType = 2;

		[Desc("Global physical + queued + requested LST pool cap shared by capture, GroundTransfer and strategic expansion. Busy/reserved landing craft still count toward the pool: logistics must reuse or wait instead of growing the fleet simply because existing craft are occupied.")]
		public readonly int MaximumLandingCraftPool = 3;

		[Desc("Distinct bounded LST route proofs that may fail for one passenger/target mission before LST is rejected for that mission. This prevents one impossible capture corridor from repeatedly manufacturing replacement landing craft.")]
		public readonly int LandingCraftFailureProofLimit = 2;

		[Desc("Distinct physical air transports that may fail the same reusable SpecOps passenger/target route proof before that transport type is treated as impossible for the current mission. A later mission may retry after normal pair cooldown/reconsideration.")]
		public readonly int ReusableSpecOpsAirTransportFailureProofLimit = 2;

		[Desc("Ticks between active mission state checks.")]
		public readonly int MissionUpdateInterval = 25;

		[Desc("World ticks before a failed passenger/target/transport plan may be path-tested again if mission endpoint geometry has not materially changed. Equivalent LSTs and same-landmass Jeep/APC craft share the negative proof, so producing a new actor does not bypass the cooldown.")]
		public readonly int TransportPlanFailureRetryCooldown = 1500;

		[Desc("Cell movement beyond this distance invalidates a cached failed transport plan and permits one fresh bounded plan attempt.")]
		public readonly int TransportPlanCacheMovementTolerance = 2;

		[Desc("Abort a mission phase that makes no progress within this many world ticks. Set 0 to disable.")]
		public readonly int MissionTimeout = 3000;

		[Desc("World ticks allowed for a loaded transport RETREAT before a fresh local safe-drop plan may be forced.")]
		public readonly int RetreatTimeout = 750;

		[Desc("Radius around a loaded transport searched for a legal RETREAT unload cell.")]
		public readonly int RetreatSearchRadius = 18;

		[Desc("Minimum world ticks between RETREAT safe-drop replans when the transport is stalled.")]
		public readonly int RetreatReplanInterval = 250;

		[Desc("World ticks without changing cell before an assigned transport may have its current move reissued once. No expensive route search runs at this cadence.")]
		public readonly int TransportStallReplanTicks = 125;

		[Desc("Consecutive WAITING timeouts for the same engineer/target before the route is put on cooldown.")]
		public readonly int WaitingForTransportFailureLimit = 2;
		[Desc("World ticks to suppress the same engineer/target transport pair after repeated WAITING failures.")]
		public readonly int WaitingForTransportFailureCooldown = 10000;

		[Desc("World ticks to suppress the same engineer/target pair after a loaded capture transport RETREAT safely unloads and cancels the mission. This prevents immediate re-entry into the same newly proven dangerous corridor.")]
		public readonly int AbortedLoadedMissionRetryCooldown = 3000;

		[Desc("Maximum cell distance accepted as 'transport reached pickup'.")]
		public readonly int PickupArrivalRadius = 2;

		[Desc("World ticks between ownership watchdog checks while an engineer is moving toward an assigned transport pickup. If it stops making progress or is diverted by a stale order, FransTransport cancels that activity and reasserts the RiskModel-routed pickup move.")]
		public readonly int PassengerPickupReassertInterval = 100;

		[Desc("Maximum cell distance accepted as 'transport reached drop'.")]
		public readonly int DropArrivalRadius = 1;

		[Desc("Radius around an engineer searched for a ground-transport pickup cell.")]
		public readonly int GroundPickupSearchRadius = 3;

		[Desc("Maximum distance from engineer to search for an LST pickup Beach.")]
		public readonly int LandingCraftPickupSearchRadius = 24;

		[Desc("Minimum distance from capture target for transport drop planning.")]
		public readonly int MinimumDropRadius = 3;

		[Desc("Maximum distance from capture target for transport drop planning.")]
		public readonly int MaximumDropRadius = 8;

		[Desc("Maximum distance from a capture target to search for an LST landing Beach.")]
		public readonly int LandingCraftDropSearchRadius = 18;

		[Desc("Maximum radius around the target that the unloaded engineer must be able to path into.")]
		public readonly int PassengerTargetApproachRadius = 4;

		[Desc("Maximum pickup/drop cells path-tested for one transport plan.")]
		public readonly int MaximumCellCandidates = 32;

		[Desc("Maximum source beach cells path-tested by one LST capture route proof. bounds the expensive pickup x drop fan-out.")]
		public readonly int LandingCraftMaximumPickupCandidates = 3;

		[Desc("Maximum destination beach cells path-tested for each accepted LST pickup candidate.")]
		public readonly int LandingCraftMaximumDropCandidates = 3;

		[Desc("hard cap on APC pickup candidates. Ground capture planning must never expand into an unbounded pickup x drop search.")]
		public readonly int GroundTransportMaximumPickupCandidates = 4;

		[Desc("hard cap on APC drop candidates. Target-side reachability is topology-filtered before any route proof.")]
		public readonly int GroundTransportMaximumDropCandidates = 4;

		[Desc("Maximum legal E6 approach cells considered when resolving the target ground landmass for bounded APC planning.")]
		public readonly int GroundTransportMaximumApproachCandidates = 8;

		[Desc("Ticks before retrying EnterTransport if a previous boarding activity ended without loading.")]
		public readonly int BoardingRetryInterval = 75;

		[Desc("Ticks before retrying Unload if the unload activity ended but the passenger is still cargo.")]
		public readonly int UnloadRetryInterval = 75;

		[Desc("Ticks to wait for capture ownership to settle after the engineer leaves the world before treating the attempt as failed.")]
		public readonly int CaptureCompletionGraceTicks = 50;

		[Desc("Radius in cells around the engineer in which a reserved APC may actively engage visible mobile combat threats while waiting for capture completion.")]
		public readonly int CaptureEscortThreatRadius = 8;

		[Desc("If true, TRAN capture missions use the shared fair-information RiskModel for bounded strategic corridor selection. Native aircraft movement owns the actual flight path.")]
		public readonly bool EnableAirTransportRiskRouting = true;

		[Desc("World ticks between bounded in-flight TRAN corridor checks. Replanning occurs only for newly critical risk, never merely because a route is no longer Preferred.")]
		public readonly int AirTransportStrategicRiskRecheckInterval = 125;

		[Desc("Maximum deterministic midpoint detour candidates tested when a direct TRAN corridor contains critical known risk.")]
		public readonly int AirTransportMaximumDetourCandidates = 12;

		[Desc("Maximum midpoint detour offset in cells for bounded TRAN corridor planning.")]
		public readonly int AirTransportDetourRadius = 18;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);

			// Cameo port: PassengerTypes/PreferredTransportTypes/ReusablePreferredTransportTypes
			// ship empty until per-faction ContentPack wiring fills them; empty lists leave
			// transport missions inactive instead of failing the ruleset.
			if (ReusableStandbyTimeout < 0 || MaximumGroundTransportsPerType <= 0 ||
				MaximumLandingCraftPool <= 0 || LandingCraftFailureProofLimit <= 0)
				throw new YamlException("Reusable SpecOps/ground/LST transport settings are invalid.");

			if (MaximumActiveMissions <= 0 || MissionUpdateInterval < 25 || TransportPlanFailureRetryCooldown < 0 || TransportPlanCacheMovementTolerance < 0)
				throw new YamlException("Transport mission/cache limits are invalid; recurring MissionUpdateInterval must respect the Fransbot 25-WT floor.");

			if (MinimumCashForTransportProduction < 0 || ProductionRequestCooldown < 25 || MaximumAirTransports <= 0 ||
				MaximumReusableSpecOpsAirTransports <= 0 || ReusableSpecOpsAirTransportFailureProofLimit <= 0)
				throw new YamlException("Transport production settings are invalid; reusable SpecOps air-transport caps/proof limits must be positive and recurring production retry cadence must respect the 25-WT floor.");

			if (MissionTimeout < 0 || RetreatTimeout <= 0 || RetreatSearchRadius <= 0 || RetreatReplanInterval < 25 ||
				TransportStallReplanTicks < 25 || PickupArrivalRadius < 0 || PassengerPickupReassertInterval < 25 || DropArrivalRadius < 0 ||
				WaitingForTransportFailureLimit <= 0 || WaitingForTransportFailureCooldown < 0 || AbortedLoadedMissionRetryCooldown < 0)
				throw new YamlException("Transport timeout/arrival/RETREAT settings are invalid or violate the 25-WT floor.");

			if (GroundPickupSearchRadius <= 0 || LandingCraftPickupSearchRadius <= 0 ||
				MinimumDropRadius < 0 || MaximumDropRadius < MinimumDropRadius ||
				LandingCraftDropSearchRadius <= 0 || PassengerTargetApproachRadius <= 0 ||
				MaximumCellCandidates <= 0 || LandingCraftMaximumPickupCandidates <= 0 || LandingCraftMaximumDropCandidates <= 0 || GroundTransportMaximumPickupCandidates <= 0 ||
				GroundTransportMaximumDropCandidates <= 0 || GroundTransportMaximumApproachCandidates <= 0 ||
				BoardingRetryInterval < 25 || UnloadRetryInterval < 25 ||
				CaptureCompletionGraceTicks < 0 || CaptureEscortThreatRadius <= 0)
				throw new YamlException("Transport planning settings are invalid or a recurring retry cadence violates the 25-WT floor.");

			if (AirTransportStrategicRiskRecheckInterval < 25 || AirTransportMaximumDetourCandidates <= 0 ||
				AirTransportDetourRadius <= 0)
				throw new YamlException("Air transport bounded-corridor settings are invalid or violate the 25-WT floor.");
		}

		public override object Create(ActorInitializer init) { return new FransTransportCommanderBotModule(init.Self, this); }
	}

	public class FransTransportCommanderBotModule : ConditionalTrait<FransTransportCommanderBotModuleInfo>,
		IBotEnabled, IBotTick, IFransCaptureTransportService
	{
		enum MissionState
		{
			Waiting,
			Pickup,
			Move,
			Drop,
			Handoff,
			Escort,
			Return,
			Standby,
			ExtractPickup,
			ExtractReturn,
			ExtractDrop,
			Retreat
		}

		sealed class TransportMission
		{
			public readonly Actor Passenger;
			public readonly Actor Target;
			public readonly int MissionStartedTick;
			public int StartedTick;
			public int LastProductionRequestTick = -1;
			public readonly bool LandPathAvailable;
			public readonly bool ReusableRoundTrip;
			public readonly HashSet<string> FailedTransportTypes = [];
			public readonly Dictionary<string, HashSet<uint>> FailedReusableAirPlanActorIdsByType = [];
			public readonly Dictionary<string, int> FailedLandingCraftPlanProofsByType = [];

			public MissionState State;
			public Actor Transport;
			public string RequestedTransportType;
			public CPos PickupPassengerCell;
			public CPos PickupTransportCell;
			public CPos DropTransportCell;
			public int NextProductionRequestTick;
			public int NextPassengerPickupReassertTick;
			public int LastPassengerPickupDistanceSquared = int.MaxValue;
			public int NextBoardingRetryTick;
			public bool BoardingOrderIssued;
			public int NextUnloadRetryTick;
			public Actor UnloadStopOrderTransport;
			public int PassengerMissingSinceTick = -1;
			public UnitStance? OriginalTransportStance;
			public bool EscortHoldFireApplied;
			public Actor EscortThreat;

			// Route planning is memoized per physical actor for successful/exact geometry.
			// Failed LST and ground-transport proofs additionally feed domain-level shared caches,
			// so a new actor ID cannot bypass a negative route proof for unchanged endpoints.
			public readonly Dictionary<uint, CachedTransportPlan> PlanCache = [];

			// at most one bounded strategic detour waypoint plus the final destination.
			// Native OpenRA movement owns all cell-by-cell flight/pathfinding.
			public List<CPos> AirWaypoints = [];
			public int AirWaypointIndex;
			public CPos AirDestination;
			public int NextAirRiskCheckTick;
			public int LastAirRiskRevision = -1;

			// LSTs use plain native Move once a fair-intel route has been accepted.
			// These fields only gate cheap endpoint risk checks; no route A* runs on cadence.
			public int NextNavalRiskCheckTick;
			public int LastNavalRiskRevision = -1;
			public int LastTransportLossExclusionRevision = -1;
			public bool LandingCraftLegValidationPending;
			public int LastProductionLossBlockRevision = -1;

			public CPos LastTransportProgressCell;
			public int LastTransportProgressTick;
			public bool CancelAfterDrop;
			public CPos? RetreatDropCell;
			public int NextRetreatPlanTick;
			public CPos ExtractionPassengerCell;
			public CPos ExtractionTransportCell;
			public int StandbyStartedTick;

			public TransportMission(Actor passenger, Actor target, bool landPathAvailable, int startedTick, bool reusableRoundTrip = false)
			{
				Passenger = passenger;
				Target = target;
				MissionStartedTick = startedTick;
				LandPathAvailable = landPathAvailable;
				ReusableRoundTrip = reusableRoundTrip;
				StartedTick = startedTick;
				State = MissionState.Waiting;
			}
		}

		readonly record struct TransportPlan(CPos PickupPassengerCell, CPos PickupTransportCell, CPos DropTransportCell);

		sealed class PassengerTargetProofKey : IEquatable<PassengerTargetProofKey>
		{
			public readonly uint PassengerActorId;
			public readonly CPos Source;
			public readonly CPos[] OrderedApproachCells;
			readonly int hashCode;

			public PassengerTargetProofKey(uint passengerActorId, CPos source, IReadOnlyList<CPos> orderedApproachCells)
			{
				PassengerActorId = passengerActorId;
				Source = source;
				OrderedApproachCells = orderedApproachCells?.ToArray();

				unchecked
				{
					var hash = ((int)passengerActorId * 397) ^ source.GetHashCode();
					if (OrderedApproachCells == null)
						hash = hash * 397 - 1;
					else
						foreach (var cell in OrderedApproachCells)
							hash = hash * 397 ^ cell.GetHashCode();
					hashCode = hash;
				}
			}

			public bool Equals(PassengerTargetProofKey other)
			{
				if (other == null || PassengerActorId != other.PassengerActorId || Source != other.Source)
					return false;
				if (OrderedApproachCells == null || other.OrderedApproachCells == null)
					return OrderedApproachCells == other.OrderedApproachCells;
				if (OrderedApproachCells.Length != other.OrderedApproachCells.Length)
					return false;

				for (var i = 0; i < OrderedApproachCells.Length; i++)
					if (OrderedApproachCells[i] != other.OrderedApproachCells[i])
						return false;

				return true;
			}

			public override bool Equals(object obj) => Equals(obj as PassengerTargetProofKey);
			public override int GetHashCode() => hashCode;
		}

		sealed class PassengerTargetProofPlanningPass
		{
			readonly Dictionary<PassengerTargetProofKey, bool> memo = [];
			readonly Dictionary<string, int> physicalCandidatesByType = [];

			public readonly string[] OrderedCandidateTypes;
			public int RetainedPickupCount;
			public int RetainedDropCount;
			public int TargetApproachCount;
			public int ExitSourceCount;
			public int LogicalRequests;
			public int PhysicalPathSearches;
			public int MemoHits;
			public long NativePathCostCallbackCalls;
			public int LogicalFirstSuccessPosition;
			public Actor SelectedTransport;
			public CPos SelectedPickup;
			public CPos SelectedDrop;
			public bool Success;

			public int MemoEntries => memo.Count;

			public PassengerTargetProofPlanningPass(IEnumerable<string> orderedCandidateTypes)
			{
				OrderedCandidateTypes = orderedCandidateTypes.ToArray();
				foreach (var type in OrderedCandidateTypes)
					physicalCandidatesByType[type] = 0;
			}

			public void RecordPhysicalCandidate(string type)
			{
				physicalCandidatesByType.TryGetValue(type, out var count);
				physicalCandidatesByType[type] = count + 1;
			}

			public string FormatPhysicalCandidates() => string.Join(",",
				OrderedCandidateTypes.Select(type => $"{type}:{physicalCandidatesByType.GetValueOrDefault(type)}"));

			public bool TryGet(PassengerTargetProofKey key, out bool result)
			{
				if (!memo.TryGetValue(key, out result))
					return false;

				MemoHits++;
				return true;
			}

			public void Store(PassengerTargetProofKey key, bool result) => memo.Add(key, result);

			public void RecordLogicalResult(bool result)
			{
				if (result && LogicalFirstSuccessPosition == 0)
					LogicalFirstSuccessPosition = LogicalRequests;
			}
		}

		sealed class CachedTransportPlan
		{
			public readonly bool Success;
			public readonly TransportPlan Plan;
			public readonly CPos PassengerCell;
			public readonly CPos TargetCell;
			public readonly CPos TransportCell;
			public readonly int TestedTick;

			public CachedTransportPlan(bool success, TransportPlan plan, CPos passengerCell, CPos targetCell, CPos transportCell, int testedTick)
			{
				Success = success;
				Plan = plan;
				PassengerCell = passengerCell;
				TargetCell = targetCell;
				TransportCell = transportCell;
				TestedTick = testedTick;
			}
		}

		readonly record struct SharedLandingCraftFailureKey(
			string TransportType,
			uint PassengerActorId,
			uint TargetActorId,
			int SourceLandmassId,
			int TargetLandmassId,
			int NavalRegionId,
			int TerrainKnowledgeVersion);

		readonly record struct SharedGroundTransportFailureKey(
			string TransportType,
			uint PassengerActorId,
			uint TargetActorId,
			int TransportLandmassId,
			int SourceLandmassId,
			int TargetLandmassId,
			int TerrainKnowledgeVersion);

		sealed class SharedGroundTransportFailureState
		{
			public readonly CPos PassengerCell;
			public readonly CPos TargetCell;
			public readonly int RetryAfterTick;

			public SharedGroundTransportFailureState(CPos passengerCell, CPos targetCell, int retryAfterTick)
			{
				PassengerCell = passengerCell;
				TargetCell = targetCell;
				RetryAfterTick = retryAfterTick;
			}
		}

		readonly record struct AirCorridorTickCacheKey(string TransportType, CPos From, CPos To, int RiskRevision);
		readonly record struct PendingMoveOrder(CPos Destination, bool Queued);

		sealed class AirCorridorTickCacheValue
		{
			public readonly bool Success;
			public readonly CPos[] Waypoints;

			public AirCorridorTickCacheValue(bool success, IEnumerable<CPos> waypoints)
			{
				Success = success;
				Waypoints = waypoints?.ToArray() ?? Array.Empty<CPos>();
			}
		}

		sealed class WaitingTransportFailureState
		{
			public int ConsecutiveFailures;
			public int CooldownUntil;
		}

		readonly World world;
		readonly Player player;

		readonly Dictionary<Actor, TransportMission> missions = [];
		readonly Dictionary<Actor, Actor> transportReservations = [];
		readonly Dictionary<(uint PassengerId, uint TargetId), WaitingTransportFailureState> waitingTransportFailures = [];
		readonly Dictionary<SharedLandingCraftFailureKey, int> sharedLandingCraftFailureUntil = [];
		readonly HashSet<SharedLandingCraftFailureKey> sharedLandingCraftTopologyFailures = [];
		readonly Dictionary<SharedGroundTransportFailureKey, SharedGroundTransportFailureState> sharedGroundTransportFailures = [];
		readonly HashSet<SharedGroundTransportFailureKey> sharedGroundTransportTopologyFailures = [];
		int sharedLandingCraftTopologyVersion = -1;
		int sharedGroundTransportTopologyVersion = -1;
		readonly Dictionary<AirCorridorTickCacheKey, AirCorridorTickCacheValue> airCorridorTickCache = [];
		readonly HashSet<Actor> pendingStopOrders = [];
		readonly Dictionary<Actor, PendingMoveOrder> pendingMoveOrders = [];
		readonly Dictionary<Actor, UnitStance> pendingStanceOrders = [];
		int airCorridorTickCacheWorldTick = -1;
		int nextTransportPlanPerfLogTick;

		IBot orderBot;
		IBotRequestUnitProduction[] requestUnitProduction;
		PlayerResources playerResources;
		IFransRiskModelService riskModelService;
		IFransCombatIntelService combatIntelService;
		IFransStrategicMapService strategicMapService;
		IFransGeneralService generalService;
		IFransCommandBidService commandBidService;
		IFransAmphibiousExpansionService amphibiousExpansionService;
		int missionTicks;

		public FransTransportCommanderBotModule(Actor self, FransTransportCommanderBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		protected override void Created(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;

			requestUnitProduction = self.TraitsImplementing<IBotRequestUnitProduction>().ToArray();
			playerResources = self.Trait<PlayerResources>();
			riskModelService = self.TraitsImplementing<IFransRiskModelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransTransportCommanderBotModule requires FransRiskModelBotModule.");
			combatIntelService = self.TraitsImplementing<IFransCombatIntelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransTransportCommanderBotModule requires FransCombatIntelBotModule.");
			strategicMapService = self.TraitsImplementing<IFransStrategicMapService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransTransportCommanderBotModule requires FransStrategicMapBotModule.");
			generalService = self.TraitsImplementing<IFransGeneralService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransTransportCommanderBotModule requires FransGeneralBotModule.");
			commandBidService = self.TraitsImplementing<IFransCommandBidService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransTransportCommanderBotModule requires FransCommandBidBotModule.");
			amphibiousExpansionService = self.TraitsImplementing<IFransAmphibiousExpansionService>().FirstOrDefault();
		}

		void IBotEnabled.BotEnabled(IBot bot)
		{
			orderBot = bot;
		}

		protected override void TraitEnabled(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;

			// deterministic phase spreading; cadence remains the configured >=25 WT.
			missionTicks = (int)((self.ActorID + 23u) % (uint)Info.MissionUpdateInterval) + 1;
			FransBotLog.BotDebug(world,
				"{0}: FransTransportCommander SINGLE-OWNER TRANSPORT CORE active: native EnterTransport/SpecOps HoldFire/forced Unload behavior is unchanged. Negative route proofs are shared across equivalent transports where geometry permits: LST by passenger/target + landmasses + naval region, and Jeep/APC by passenger/target + transport/source/target ground landmass. Native LST route search is hard-bounded to {2} pickup x {3} drop candidates. Loaded RETREAT cooldown {1} WT remains. Capture/SpecOps TRAN demand uses physical+pending cap {4} (reusable {5}); ground capture production is capped at {6} physical+pending craft per type; the shared LST pool is capped at {7} physical+queued+requested craft. Physical transport ownership remains single-owner; a committed MCV sea expansion has HARD priority over empty pre-load capture or reusable SpecOps LST ownership, while loaded/insertion-completed transports are never preempted.",
				player, Info.AbortedLoadedMissionRetryCooldown, Info.LandingCraftMaximumPickupCandidates, Info.LandingCraftMaximumDropCandidates,
				Info.MaximumAirTransports, Info.MaximumReusableSpecOpsAirTransports, Info.MaximumGroundTransportsPerType, Info.MaximumLandingCraftPool);
		}

		protected override void TraitDisabled(Actor self)
		{
			foreach (var mission in missions.Values.ToArray())
				ReleaseTransport(mission);

			missions.Clear();
			transportReservations.Clear();
			waitingTransportFailures.Clear();
			sharedLandingCraftFailureUntil.Clear();
			sharedLandingCraftTopologyFailures.Clear();
			sharedGroundTransportFailures.Clear();
			sharedGroundTransportTopologyFailures.Clear();
			sharedLandingCraftTopologyVersion = -1;
			sharedGroundTransportTopologyVersion = -1;
			airCorridorTickCache.Clear();
			airCorridorTickCacheWorldTick = -1;
			pendingStopOrders.Clear();
			pendingMoveOrders.Clear();
			pendingStanceOrders.Clear();
		}

		bool IsValidOrderSubject(Actor actor)
		{
			return actor != null && !actor.Disposed && actor.IsInWorld && !actor.IsDead && actor.Owner == player;
		}

		void QueueStopOrder(IBot bot, Actor actor)
		{
			if (!IsValidOrderSubject(actor))
				return;

			var sink = bot ?? orderBot;
			if (sink != null)
			{
				pendingStopOrders.Remove(actor);
				pendingMoveOrders.Remove(actor);
				sink.QueueOrder(new Order("Stop", actor, false));
				return;
			}

			pendingMoveOrders.Remove(actor);
			pendingStopOrders.Add(actor);
		}

		void QueueMoveOrder(IBot bot, Actor actor, CPos destination, bool queued = false)
		{
			if (!IsValidOrderSubject(actor) || !world.Map.Contains(destination) || actor.TraitOrDefault<Mobile>() == null)
				return;

			var sink = bot ?? orderBot;
			if (sink != null)
			{
				pendingStopOrders.Remove(actor);
				pendingMoveOrders.Remove(actor);
				sink.QueueOrder(new Order("Move", actor, Target.FromCell(world, destination), queued));
				return;
			}

			pendingStopOrders.Remove(actor);
			pendingMoveOrders[actor] = new PendingMoveOrder(destination, queued);
		}

		void QueueSetUnitStanceOrder(IBot bot, Actor actor, UnitStance stance)
		{
			if (!IsValidOrderSubject(actor) || actor.TraitOrDefault<AutoTarget>() == null)
				return;

			var sink = bot ?? orderBot;
			if (sink != null)
			{
				pendingStanceOrders.Remove(actor);
				sink.QueueOrder(new Order("SetUnitStance", actor, false) { ExtraData = (uint)stance });
				return;
			}

			pendingStanceOrders[actor] = stance;
		}

		void FlushPendingSynchronizedActions(IBot bot)
		{
			if (bot == null || pendingStopOrders.Count == 0 && pendingMoveOrders.Count == 0 && pendingStanceOrders.Count == 0)
				return;

			var actors = pendingStopOrders
				.Concat(pendingMoveOrders.Keys)
				.Concat(pendingStanceOrders.Keys)
				.Distinct()
				.OrderBy(actor => actor.ActorID)
				.ToArray();

			foreach (var actor in actors)
			{
				if (!IsValidOrderSubject(actor))
					continue;

				if (pendingStopOrders.Contains(actor))
					bot.QueueOrder(new Order("Stop", actor, false));
				else if (pendingMoveOrders.TryGetValue(actor, out var move) && world.Map.Contains(move.Destination) &&
					actor.TraitOrDefault<Mobile>() != null)
					bot.QueueOrder(new Order("Move", actor, Target.FromCell(world, move.Destination), move.Queued));

				if (pendingStanceOrders.TryGetValue(actor, out var stance) && actor.TraitOrDefault<AutoTarget>() != null)
					bot.QueueOrder(new Order("SetUnitStance", actor, false) { ExtraData = (uint)stance });
			}

			pendingStopOrders.Clear();
			pendingMoveOrders.Clear();
			pendingStanceOrders.Clear();
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransTransportCommander.BotTick");
			if (world.Type == WorldType.Editor || player.WinState != WinState.Undefined)
				return;

			FlushPendingSynchronizedActions(bot);

			if (--missionTicks > 0)
				return;

			missionTicks = Info.MissionUpdateInterval;

			var perfLstStates = missions.Values
				.Where(m => m.Transport != null && !m.Transport.Disposed && Info.LandingCraftTypes.Contains(m.Transport.Info.Name))
				.OrderBy(m => m.Passenger.ActorID)
				.Take(4)
				.Select(m => $"{m.State}:LST{m.Transport.ActorID}/P{m.Passenger.ActorID}");
			FransBotLog.SetPerfContext(world, $"TRANSPORT:{player.PlayerActor.ActorID}",
				$"{player}:missions={missions.Count},lst=[{string.Join(",", perfLstStates)}]");

			foreach (var mission in missions.Values
				.OrderBy(m => m.Passenger.ActorID)
				.ToArray())
				ManageMission(bot, mission);
		}

		bool IsMissionCompatibleTransportRequest(Actor passenger, Actor target)
		{
			if (passenger == null || target == null || commandBidService == null ||
				!commandBidService.TryGetActorActiveMission(passenger.ActorID, out var active))
				return true;

			// Once the broker has committed an actor, Transport is a service of that exact mission,
			// never an independent owner. This closes the reverse race where an E6/Thief/Tanya
			// could be assigned to target A, then accepted for transport toward target B before
			// its Commander consumed the broker assignment.
			return active.Commander == FransCommanderKind.SpecOps && active.TargetActorId == target.ActorID;
		}

		bool IFransCaptureTransportService.IsHandlingPassenger(Actor passenger)
		{
			return passenger != null && missions.TryGetValue(passenger, out var mission) && IsHandlingPassengerMission(mission);
		}

		bool IFransCaptureTransportService.IsHandlingPassenger(uint passengerActorId)
		{
			// Native Cargo removes a loaded passenger from World.GetActorById(), but this module
			// intentionally retains the exact Actor reference. Expose immutable ActorID ownership so
			// SpecOps does not mistake a correctly loaded Tanya/E6 for a dead specialist.
			return passengerActorId != 0 && missions.Values.Any(m =>
				m.Passenger != null && m.Passenger.ActorID == passengerActorId && IsHandlingPassengerMission(m));
		}

		static bool IsHandlingPassengerMission(TransportMission mission)
		{
			return mission != null && mission.State is MissionState.Waiting or MissionState.Pickup or MissionState.Move or
				MissionState.Drop or MissionState.Handoff or MissionState.Standby or MissionState.ExtractPickup or
				MissionState.ExtractReturn or MissionState.ExtractDrop or MissionState.Retreat;
		}

		bool IFransCaptureTransportService.IsCaptureTargetReserved(Actor target, Actor exceptPassenger)
		{
			if (target == null)
				return false;

			return missions.Values.Any(m =>
				m.Passenger != null && !m.Passenger.Disposed &&
				m.Passenger != exceptPassenger &&
				m.State != MissionState.Retreat &&
				m.Target == target &&
				!m.Passenger.IsDead);
		}

		bool CanAcceptTransportRequest(Actor passenger, Actor target, bool reusableRoundTrip, out TransportMission existing)
		{
			existing = null;
			if (!IsValidPassenger(passenger) || !IsValidCaptureTarget(target) ||
				!IsMissionCompatibleTransportRequest(passenger, target) || IsWaitingTransportPairCoolingDown(passenger, target))
				return false;

			if (missions.TryGetValue(passenger, out existing))
				return existing.Target == target && existing.ReusableRoundTrip == reusableRoundTrip;

			return missions.Count < Info.MaximumActiveMissions;
		}

		bool HasPotentialTransport(Actor passenger, Actor target, bool landPathAvailable, bool reusableRoundTrip, out TransportMission existing)
		{
			if (!CanAcceptTransportRequest(passenger, target, reusableRoundTrip, out existing))
				return false;
			if (existing != null)
				return true;

			foreach (var type in PreferredTransportTypesFor(reusableRoundTrip))
			{
				if (!IsConfiguredTransportType(type))
					continue;
				if (FindAvailableTransports(type).Any(t => IsCheaplyCompatibleTransport(t, passenger, target, landPathAvailable)) ||
					CanRequestTransportType(type, passenger, target, landPathAvailable))
					return true;
			}

			return false;
		}

		bool IFransCaptureTransportService.CanPotentiallyTransport(Actor passenger, Actor target, bool landPathAvailable) =>
			HasPotentialTransport(passenger, target, landPathAvailable, reusableRoundTrip: false, out _);

		bool IFransCaptureTransportService.CanPotentiallyTransportReusable(Actor passenger, Actor target, bool landPathAvailable) =>
			HasPotentialTransport(passenger, target, landPathAvailable, reusableRoundTrip: true, out _);

		bool IFransCaptureTransportService.TryRequestReusableTransport(
			IBot bot, Actor passenger, Actor target, bool landPathAvailable)
		{
			if (!HasPotentialTransport(passenger, target, landPathAvailable, reusableRoundTrip: true, out var existing))
				return false;
			if (existing != null)
				return true;

			var mission = new TransportMission(passenger, target, landPathAvailable, world.WorldTick, reusableRoundTrip: true);
			missions[passenger] = mission;
			FransBotLog.BotDebug(world, "{0}: reusable SpecOps transport accepted {1} for insertion toward {2}.", player, passenger, target);
			if (!TryAssignExistingTransport(bot, mission))
				RequestBestTransport(bot, mission, landPathAvailable);
			return true;
		}

		bool IFransCaptureTransportService.TryConsumeCompletedReusableInsertion(Actor passenger, out Actor target)
		{
			target = null;
			if (passenger == null || !missions.TryGetValue(passenger, out var mission) || !mission.ReusableRoundTrip ||
				mission.State != MissionState.Handoff)
				return false;

			target = mission.Target;
			mission.State = MissionState.Standby;
			mission.StandbyStartedTick = world.WorldTick;
			mission.StartedTick = world.WorldTick;
			if (mission.Transport != null && !mission.Transport.Disposed && mission.Transport.IsInWorld && !mission.Transport.IsDead)
			{
				mission.Transport.CancelActivity();
				if (Info.GroundTransportTypes.Contains(mission.Transport.Info.Name))
					ApplyCaptureEscortHoldFire(mission);
			}

			FransBotLog.BotDebug(world, "{0}: reusable SpecOps insertion completed for {1}; {2} stays reserved near the drop area for extraction.",
				player, passenger, mission.Transport);
			return true;
		}

		bool IFransCaptureTransportService.TryBeginReusableExtraction(IBot bot, Actor passenger)
		{
			if (passenger == null || !missions.TryGetValue(passenger, out var mission) || !mission.ReusableRoundTrip ||
				mission.State != MissionState.Standby || passenger.Disposed || !passenger.IsInWorld || passenger.IsDead ||
				!ValidateAssignedTransport(mission))
				return false;

			if (!TryResolveExtractionPickup(mission, out var passengerCell, out var transportCell))
				return false;

			mission.ExtractionPassengerCell = passengerCell;
			mission.ExtractionTransportCell = transportCell;
			mission.State = MissionState.ExtractPickup;
			mission.StartedTick = world.WorldTick;
			mission.NextBoardingRetryTick = 0;
			mission.BoardingOrderIssued = false;
			mission.NextPassengerPickupReassertTick = world.WorldTick + Info.PassengerPickupReassertInterval;
			mission.LastPassengerPickupDistanceSquared = (passenger.Location - passengerCell).LengthSquared;
			ResetTransportMoveState(mission);
			if (!IsLandingCraftLegStillSafe(mission, mission.ExtractionTransportCell, out var landingCraftFailure))
			{
				FransBotLog.BotDebug(world,
					"{0}: reusable SpecOps LST extraction pickup rejects {1} for {2}: {3}.",
					player, mission.Transport, mission.Passenger, landingCraftFailure);
				((IFransCaptureTransportService)this).CancelCaptureTransport(bot, mission.Passenger);
				return false;
			}
			if (Info.GroundTransportTypes.Contains(mission.Transport.Info.Name))
				ApplyCaptureEscortHoldFire(mission);
			QueueExtractionPickupMoves(bot, mission);
			FransBotLog.BotDebug(world, "{0}: reusable SpecOps extraction begins for {1} with {2}; rendezvous {3}/{4} then return toward {5}.",
				player, passenger, mission.Transport, passengerCell, transportCell, mission.PickupTransportCell);
			return true;
		}

		bool IFransCaptureTransportService.TryRequestCaptureTransport(
			IBot bot, Actor passenger, Actor target, bool landPathAvailable)
		{
			if (!HasPotentialTransport(passenger, target, landPathAvailable, reusableRoundTrip: false, out var existing))
				return false;

			if (existing != null)
				return true;

			var mission = new TransportMission(passenger, target, landPathAvailable, world.WorldTick, reusableRoundTrip: false);
			missions[passenger] = mission;

			FransBotLog.BotDebug(world, "{0}: Frans transport accepted capture passenger {1} for target {2}.",
				player, passenger, target);

			if (!TryAssignExistingTransport(bot, mission))
				RequestBestTransport(bot, mission, landPathAvailable);

			return true;
		}

		bool IFransCaptureTransportService.TryConsumeCompletedCaptureTransport(Actor passenger, out Actor target)
		{
			target = null;
			if (passenger == null || !missions.TryGetValue(passenger, out var mission) ||
				mission.State != MissionState.Handoff)
				return false;

			target = mission.Target;

			// APCs stay reserved after DROP so they can escort the same engineer until
			// ownership is physically confirmed. TRAN/LST are released immediately.
			if (mission.Transport != null && !mission.Transport.Disposed &&
				Info.GroundTransportTypes.Contains(mission.Transport.Info.Name))
				mission.State = MissionState.Escort;
			else
				missions.Remove(passenger);

			return true;
		}

		int IFransCaptureTransportService.CountTransportedPassengers(string actorType)
		{
			return missions.Values.Count(m =>
				m.Passenger != null &&
				!m.Passenger.Disposed &&
				!m.Passenger.IsDead &&
				!m.Passenger.IsInWorld &&
				m.Passenger.Info.Name == actorType);
		}

		void IFransCaptureTransportService.CancelCaptureTransport(IBot bot, Actor passenger)
		{
			if (passenger == null || !missions.TryGetValue(passenger, out var mission))
				return;

			var transport = mission.Transport;
			if (transport != null && (transport.Disposed || !transport.IsInWorld || transport.IsDead))
			{
				FransBotLog.BotDebug(world,
					"{0}: capture transport cancellation found vanished/destroyed transport {1} for {2}; mission is released without reading traits from the destroyed actor.",
					player, transport, passenger);
				if (!passenger.Disposed && passenger.IsInWorld && !passenger.IsDead)
					passenger.CancelActivity();

				ReleaseTransport(mission);
				missions.Remove(passenger);
				return;
			}

			if (IsPassengerLoaded(mission))
			{
				BeginRetreat(bot, mission, "capture mission was cancelled while E6 was already aboard");
				return;
			}

			if (!passenger.Disposed && passenger.IsInWorld && !passenger.IsDead)
				passenger.CancelActivity();
			if (transport != null && !transport.Disposed && transport.IsInWorld && !transport.IsDead)
				transport.CancelActivity();

			ReleaseTransport(mission);
			missions.Remove(passenger);
		}

		void IFransCaptureTransportService.CancelCaptureTransport(IBot bot, uint passengerActorId)
		{
			if (passengerActorId == 0)
				return;

			var passenger = missions.Keys.FirstOrDefault(candidate =>
				candidate != null && candidate.ActorID == passengerActorId);
			if (passenger != null)
				((IFransCaptureTransportService)this).CancelCaptureTransport(bot, passenger);
		}

		bool IFransCaptureTransportService.IsTransportReserved(Actor transport)
		{
			return transport != null && transportReservations.ContainsKey(transport);
		}

		int IFransCaptureTransportService.MaximumLandingCraftPool => Info.MaximumLandingCraftPool;
		int IFransCaptureTransportService.MaximumNonStrategicLandingCraftPool => Math.Max(0, Info.MaximumLandingCraftPool - 1);

		int IFransCaptureTransportService.CountLandingCraftPool(IBot bot)
		{
			var live = Info.LandingCraftTypes.Sum(CountLiveOwnedTransportType);
			var unitBuilder = requestUnitProduction?.FirstEnabledTraitOrDefault();
			if (unitBuilder == null)
				return live;

			return live + Info.LandingCraftTypes.Sum(type => CountPendingProduction(bot, unitBuilder, type));
		}

		bool TryGetPreemptableCaptureLandingCraftMission(Actor transport, out TransportMission mission)
		{
			mission = null;
			if (!IsLiveOwnedTransport(transport) || !Info.LandingCraftTypes.Contains(transport.Info.Name))
				return false;

			var cargo = transport.TraitOrDefault<Cargo>();
			if (cargo == null || cargo.IsTraitDisabled || !cargo.IsEmpty())
				return false;

			mission = missions.Values.FirstOrDefault(candidate =>
				candidate.Transport == transport && IsPreLoadLandingCraftMissionPreemptible(candidate));
			return mission != null;
		}

		bool IsPreLoadLandingCraftMissionPreemptible(TransportMission mission)
		{
			if (mission == null || IsPassengerLoaded(mission))
				return false;

			return !mission.ReusableRoundTrip || mission.State is MissionState.Waiting or MissionState.Pickup;
		}

		bool IFransCaptureTransportService.CanStrategicExpansionClaimTransport(Actor transport)
		{
			if (!IsLiveOwnedTransport(transport) || !Info.LandingCraftTypes.Contains(transport.Info.Name))
				return false;

			if (!transportReservations.ContainsKey(transport))
				return true;

			return TryGetPreemptableCaptureLandingCraftMission(transport, out _);
		}

		bool IFransCaptureTransportService.TryReserveStrategicExpansionTransport(Actor transport, Actor reservationOwner)
		{
			if (!IsLiveOwnedTransport(transport) || reservationOwner == null ||
				!Info.LandingCraftTypes.Contains(transport.Info.Name))
				return false;

			if (!transportReservations.TryGetValue(transport, out var currentOwner))
				return TryReserveTransport(transport, reservationOwner);
			if (currentOwner == reservationOwner)
				return true;

			if (!TryGetPreemptableCaptureLandingCraftMission(transport, out var mission))
				return false;

			if (!ResetMissionForStrategicLSTPreemption(null, mission, transport))
				return false;

			if (!TryReserveTransport(transport, reservationOwner))
				return false;

			FransBotLog.BotDebug(world,
				"{0}: MCV STRATEGIC LST PRIORITY preempts empty pre-load transport LST {1} from passenger {2}. The passenger mission remains alive in WAITING and may use another transport after the MCV expansion claim.",
				player, transport, mission.Passenger);
			return true;
		}

		bool ResetMissionForStrategicLSTPreemption(IBot bot, TransportMission mission, Actor transport)
		{
			if (mission?.Passenger == null || mission.Transport != transport || !IsLiveOwnedTransport(transport) ||
				!Info.LandingCraftTypes.Contains(transport.Info.Name) || !IsPreLoadLandingCraftMissionPreemptible(mission))
				return false;

			var cargo = transport.TraitOrDefault<Cargo>();
			if (cargo == null || cargo.IsTraitDisabled || !cargo.IsEmpty())
				return false;

			QueueStopOrder(bot, mission.Passenger);
			QueueStopOrder(bot, transport);
			RestoreCaptureEscortStance(mission);
			ReleaseTransportReservation(transport, mission.Passenger);
			mission.Transport = null;
			mission.RequestedTransportType = null;
			mission.State = MissionState.Waiting;
			mission.StartedTick = world.WorldTick;
			mission.NextProductionRequestTick = world.WorldTick + Info.ProductionRequestCooldown;
			mission.NextBoardingRetryTick = 0;
			mission.BoardingOrderIssued = false;
			mission.NextUnloadRetryTick = 0;
			mission.UnloadStopOrderTransport = null;
			mission.CancelAfterDrop = false;
			mission.RetreatDropCell = null;
			mission.AirWaypoints.Clear();
			mission.AirWaypointIndex = 0;
			return true;
		}

		bool TryReserveTransport(Actor transport, Actor owner)
		{
			if (!IsLiveOwnedTransport(transport) || owner == null)
				return false;

			if (transportReservations.TryGetValue(transport, out var currentOwner))
				return currentOwner == owner;

			transportReservations[transport] = owner;
			return true;
		}

		void ReleaseTransportReservation(Actor transport, Actor owner)
		{
			if (transport == null || owner == null)
				return;

			if (transportReservations.TryGetValue(transport, out var currentOwner) && currentOwner == owner)
				transportReservations.Remove(transport);
		}

		bool IFransCaptureTransportService.TryReserveExternalTransport(Actor transport, Actor reservationOwner) =>
			TryReserveTransport(transport, reservationOwner);

		void IFransCaptureTransportService.ReleaseExternalTransport(Actor transport, Actor reservationOwner) =>
			ReleaseTransportReservation(transport, reservationOwner);

		bool IsWaitingTransportPairCoolingDown(Actor passenger, Actor target)
		{
			if (passenger == null || target == null)
				return false;

			var key = (passenger.ActorID, target.ActorID);
			if (!waitingTransportFailures.TryGetValue(key, out var state))
				return false;

			return world.WorldTick < state.CooldownUntil;
		}

		void RegisterWaitingTransportFailure(TransportMission mission)
		{
			var key = (mission.Passenger.ActorID, mission.Target.ActorID);
			if (!waitingTransportFailures.TryGetValue(key, out var state))
			{
				state = new WaitingTransportFailureState();
				waitingTransportFailures[key] = state;
			}

			state.ConsecutiveFailures++;
			if (state.ConsecutiveFailures < Info.WaitingForTransportFailureLimit)
				return;

			state.CooldownUntil = world.WorldTick + Info.WaitingForTransportFailureCooldown;
			FransBotLog.BotDebug(world,
				"{0}: capture transport suppresses repeated impossible route {1} -> {2} for {3} WT after {4} WAITING failures; engineer is released for normal reconsideration.",
				player, mission.Passenger, mission.Target, Info.WaitingForTransportFailureCooldown, state.ConsecutiveFailures);
		}

		void RegisterAbortedLoadedMissionCooldown(TransportMission mission)
		{
			if (Info.AbortedLoadedMissionRetryCooldown <= 0 || mission?.Passenger == null || mission.Target == null)
				return;

			var key = (mission.Passenger.ActorID, mission.Target.ActorID);
			if (!waitingTransportFailures.TryGetValue(key, out var state))
			{
				state = new WaitingTransportFailureState();
				waitingTransportFailures[key] = state;
			}

			state.ConsecutiveFailures = 0;
			state.CooldownUntil = Math.Max(state.CooldownUntil, world.WorldTick + Info.AbortedLoadedMissionRetryCooldown);
			FransBotLog.BotDebug(world,
				"{0}: capture transport cools RETREAT-aborted pair {1} -> {2} through WT {3} ({4} WT); the engineer may pursue other targets but this newly proven dangerous corridor cannot be re-entered immediately.",
				player, mission.Passenger, mission.Target, state.CooldownUntil, Info.AbortedLoadedMissionRetryCooldown);
		}

		void ClearWaitingTransportFailure(Actor passenger, Actor target)
		{
			if (passenger != null && target != null)
				waitingTransportFailures.Remove((passenger.ActorID, target.ActorID));
		}

		bool IsPassengerLoaded(TransportMission mission)
		{
			if (mission?.Passenger == null || mission.Transport == null)
				return false;

			var passenger = mission.Passenger;
			var transport = mission.Transport;
			if (passenger.Disposed || passenger.IsDead || passenger.IsInWorld ||
				transport.Disposed || !transport.IsInWorld || transport.IsDead)
				return false;

			var passengerTrait = passenger.TraitOrDefault<Passenger>();
			var cargo = transport.TraitOrDefault<Cargo>();
			return passengerTrait?.Transport == transport && cargo != null && cargo.Passengers.Contains(passenger);
		}

		void ManageMission(IBot bot, TransportMission mission)
		{
			using var fransPerfBlock = FransBotLog.Profile(world, player, "Transport.ManageMission");
			if (mission.State == MissionState.Escort)
			{
				ManageEscort(bot, mission);
				return;
			}

			if (mission.State == MissionState.Return)
			{
				ManageReturnHome(bot, mission);
				return;
			}
			if (mission.State == MissionState.Standby)
			{
				ManageReusableStandby(mission);
				return;
			}
			if (mission.State == MissionState.ExtractPickup)
			{
				ManageExtractionPickup(bot, mission);
				return;
			}
			if (mission.State == MissionState.ExtractReturn)
			{
				ManageExtractionReturn(bot, mission);
				return;
			}
			if (mission.State == MissionState.ExtractDrop)
			{
				ManageExtractionDrop(bot, mission);
				return;
			}

			var passenger = mission.Passenger;
			if (passenger == null || passenger.Disposed || passenger.IsDead)
			{
				ReleaseTransport(mission);
				if (passenger != null)
					missions.Remove(passenger);
				return;
			}

			// a retreat-triggered native Unload changes the phase to DROP while
			// CancelAfterDrop remains latched. Do not re-enter RETREAT every mission scan
			// just because the original capture target is still invalid; DROP owns the
			// passenger until physical unload succeeds or the normal phase timeout fires.
			if (!mission.ReusableRoundTrip && mission.State != MissionState.Retreat && !mission.CancelAfterDrop && !IsValidCaptureTarget(mission.Target))
			{
				if (IsPassengerLoaded(mission))
				{
					BeginRetreat(bot, mission, "capture target is no longer valid while E6 is aboard");
					return;
				}

				FransBotLog.BotDebug(world, "{0}: capture transport released {1}; target {2} is no longer capturable.",
					player, passenger, mission.Target);
				ReleaseTransport(mission);
				missions.Remove(passenger);
				return;
			}

			var phaseTimeout = mission.State == MissionState.Retreat ? Info.RetreatTimeout : Info.MissionTimeout;
			var timeoutStartedTick = mission.State == MissionState.Waiting ? mission.MissionStartedTick : mission.StartedTick;
			if (phaseTimeout > 0 && world.WorldTick - timeoutStartedTick >= phaseTimeout)
			{
				if (mission.State == MissionState.Retreat)
				{
					ManageRetreatTimeout(bot, mission);
					return;
				}

				FransBotLog.BotDebug(world,
					"{0}: capture transport mission for {1} timed out in state {2} after {3} WT without progress.",
					player, passenger, mission.State, world.WorldTick - timeoutStartedTick);

				if (mission.State == MissionState.Waiting)
					RegisterWaitingTransportFailure(mission);

				if (IsPassengerLoaded(mission))
				{
					BeginRetreat(bot, mission, "mission timeout while E6 was already aboard");
					return;
				}

				((IFransCaptureTransportService)this).CancelCaptureTransport(bot, passenger);
				return;
			}

			switch (mission.State)
			{
				case MissionState.Waiting:
					ManageWaitingForTransport(bot, mission);
					break;
				case MissionState.Pickup:
					ManagePickup(bot, mission);
					break;
				case MissionState.Move:
					ManageMove(bot, mission);
					break;
				case MissionState.Drop:
					ManageDrop(bot, mission);
					break;
				case MissionState.Handoff:
				case MissionState.Standby:
				case MissionState.ExtractPickup:
				case MissionState.ExtractReturn:
				case MissionState.ExtractDrop:
					break;
				case MissionState.Retreat:
					ManageRetreat(bot, mission);
					break;
			}
		}

		void ManageWaitingForTransport(IBot bot, TransportMission mission)
		{
			if (!mission.Passenger.IsInWorld)
				return;

			if (TryAssignExistingTransport(bot, mission))
				return;

			if (world.WorldTick >= mission.NextProductionRequestTick)
				RequestBestTransport(bot, mission, mission.LandPathAvailable);
		}

		IEnumerable<string> PreferredTransportTypesFor(bool reusableRoundTrip) =>
			reusableRoundTrip
				? Info.ReusablePreferredTransportTypes.Concat(Info.PreferredTransportTypes).Distinct()
				: Info.PreferredTransportTypes;

		IEnumerable<string> PreferredTransportTypesFor(TransportMission mission) =>
			PreferredTransportTypesFor(mission != null && mission.ReusableRoundTrip);

		bool TryAssignExistingTransport(IBot bot, TransportMission mission)
		{
			var planningPass = new PassengerTargetProofPlanningPass(PreferredTransportTypesFor(mission));
			var stopwatch = Stopwatch.StartNew();
			var success = TryAssignExistingTransportCore(bot, mission, planningPass);
			stopwatch.Stop();
			LogTransportPlanPerf(mission, planningPass, stopwatch.Elapsed.TotalMilliseconds);
			return success;
		}

		bool TryAssignExistingTransportCore(IBot bot, TransportMission mission,
			PassengerTargetProofPlanningPass planningPass)
		{
			foreach (var type in planningPass.OrderedCandidateTypes)
			{
				if (mission.FailedTransportTypes.Contains(type) || !IsConfiguredTransportType(type))
					continue;

				foreach (var transport in FindAvailableTransports(type))
				{
					planningPass.RecordPhysicalCandidate(type);
					// a physical transport actor is route-tested at most once for this
					// mission until PASSENGER/TARGET geometry changes or the long retry cooldown
					// expires. The transport driving around no longer invalidates a negative proof.
					if (!TryGetCachedOrPlanTransport(mission, transport, planningPass, out var plan))
					{
						RecordReusableAirTransportPlanFailure(mission, transport);
						continue;
					}

					if (!TryReserveTransport(transport, mission.Passenger))
						continue;

					mission.Transport = transport;
					mission.RequestedTransportType = null;
					mission.PickupPassengerCell = plan.PickupPassengerCell;
					mission.PickupTransportCell = plan.PickupTransportCell;
					mission.DropTransportCell = plan.DropTransportCell;
					mission.StartedTick = world.WorldTick;
					mission.State = MissionState.Pickup;
					mission.NextBoardingRetryTick = 0;
					mission.BoardingOrderIssued = false;
					mission.NextUnloadRetryTick = 0;
					mission.CancelAfterDrop = false;
					mission.NextPassengerPickupReassertTick = world.WorldTick + Info.PassengerPickupReassertInterval;
					mission.LastPassengerPickupDistanceSquared = mission.Passenger.IsInWorld
						? (mission.Passenger.Location - mission.PickupPassengerCell).LengthSquared
						: int.MaxValue;
					ResetTransportMoveState(mission);
					ClearWaitingTransportFailure(mission.Passenger, mission.Target);

					if (Info.GroundTransportTypes.Contains(transport.Info.Name))
						ApplyCaptureEscortHoldFire(mission);

					planningPass.Success = true;
					planningPass.SelectedTransport = transport;
					planningPass.SelectedPickup = plan.PickupTransportCell;
					planningPass.SelectedDrop = plan.DropTransportCell;

					FransBotLog.BotDebug(world, mission.ReusableRoundTrip
						? "{0}: reusable SpecOps transport assigned {1} to {2}; pickup {3}/{4}, insertion {5}, target {6}."
						: "{0}: capture transport assigned {1} to {2}; pickup {3}/{4}, drop {5}, target {6}.",
						player, transport, mission.Passenger, plan.PickupPassengerCell,
						plan.PickupTransportCell, plan.DropTransportCell, mission.Target);

					QueuePickupMoves(bot, mission);
					return true;
				}
			}

			return false;
		}

		void LogTransportPlanPerf(TransportMission mission, PassengerTargetProofPlanningPass planningPass, double elapsedMs)
		{
			if (mission == null || planningPass == null || !mission.ReusableRoundTrip ||
				(planningPass.PhysicalPathSearches == 0 && elapsedMs < 10.0) ||
				world.WorldTick < nextTransportPlanPerfLogTick)
				return;

			nextTransportPlanPerfLogTick = world.WorldTick + 250;
			try
			{
				var passenger = mission.Passenger;
				var target = mission.Target;
				var selected = planningPass.SelectedTransport;
				var selectedActor = selected == null ? "none" : selected.ActorID.ToString();
				var selectedType = selected?.Info.Name ?? "none";
				var selectedPickup = planningPass.Success ? planningPass.SelectedPickup.ToString() : "none";
				var selectedDrop = planningPass.Success ? planningPass.SelectedDrop.ToString() : "none";
				OpenRA.Log.Write("debug",
					$"[TRANSPORT PLAN PERF][WT {world.WorldTick}] passenger={passenger.ActorID}/{passenger.Info.Name}/{passenger.Location} " +
					$"target={target.ActorID}/{target.Info.Name}/{target.Location} reusable={mission.ReusableRoundTrip} " +
					$"orderedCandidateTransportTypes=[{string.Join(",", planningPass.OrderedCandidateTypes)}] " +
					$"physicalCandidateCountByType=[{planningPass.FormatPhysicalCandidates()}] " +
					$"retainedPickupCount={planningPass.RetainedPickupCount} retainedDropCount={planningPass.RetainedDropCount} " +
					$"targetApproachCount={planningPass.TargetApproachCount} exitSourceCount={planningPass.ExitSourceCount} " +
					$"logicalPassengerTargetProofRequests={planningPass.LogicalRequests} " +
					$"physicalPassengerTargetPathSearches={planningPass.PhysicalPathSearches} " +
					$"passengerTargetProofMemoHits={planningPass.MemoHits} passengerTargetProofMemoEntries={planningPass.MemoEntries} " +
					$"nativePathCostCallbackCalls={planningPass.NativePathCostCallbackCalls} logicalFirstSuccessPosition={planningPass.LogicalFirstSuccessPosition} " +
					$"selectedTransport={selectedActor}/{selectedType} selectedPickup={selectedPickup} selectedDrop={selectedDrop} " +
					$"result={(planningPass.Success ? "success" : "failure")} elapsedMs={elapsedMs:0.00}");
			}
			catch
			{
				// Aggregate diagnostics must never affect transport selection or mission ownership.
			}
		}

		void RecordReusableAirTransportPlanFailure(TransportMission mission, Actor transport)
		{
			if (mission == null || transport == null || !mission.ReusableRoundTrip ||
				!Info.AirTransportTypes.Contains(transport.Info.Name))
				return;

			var type = transport.Info.Name;
			if (!mission.FailedReusableAirPlanActorIdsByType.TryGetValue(type, out var failedActors))
			{
				failedActors = [];
				mission.FailedReusableAirPlanActorIdsByType[type] = failedActors;
			}

			if (!failedActors.Add(transport.ActorID) ||
				failedActors.Count < Info.ReusableSpecOpsAirTransportFailureProofLimit)
				return;

			if (mission.FailedTransportTypes.Add(type))
				FransBotLog.BotDebug(world,
					"{0}: reusable SpecOps route {1} -> {2} rejects transport type {3} for this mission after {4} distinct physical craft failed the bounded route proof. No more identical {3} production will be requested for this passenger/target attempt.",
					player, mission.Passenger, mission.Target, type, failedActors.Count);
		}

		int CountLiveOwnedTransportType(string type) =>
			world.Actors.Count(a => IsLiveOwnedTransport(a) && a.Info.Name == type);

		bool QueueGroundRiskAwareMove(Actor actor, CPos destination, FransRiskRole role, FransRiskTolerance tolerance)
		{
			var mobile = actor?.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused ||
				mobile.PathFinder is not PathFinder pathFinder || !world.Map.Contains(destination))
				return false;

			int CustomCost(CPos cell) => cell == mobile.ToCell ? 0 : riskModelService.GetPathCost(actor, cell, role, tolerance);
			var initialPath = pathFinder.FindPathToTargetCell(actor, [mobile.ToCell], destination,
				BlockedByActor.Immovable, CustomCost, laneBias: false);
			if (initialPath == null || initialPath.Count == 0 ||
				riskModelService.EvaluateRoute(actor, initialPath, role, tolerance).IsCritical)
				return false;

			// PathFinder returns target-to-source. Preserve the accepted risk-aware route with a
			// bounded native waypoint packet instead of installing a custom synchronized activity.
			var orderedPath = initialPath
				.AsEnumerable()
				.Reverse()
				.Where(cell => cell != mobile.ToCell)
				.ToArray();
			if (orderedPath.Length == 0)
			{
				QueueMoveOrder(null, actor, destination);
				return true;
			}

			const int MaximumMoveWaypoints = 4;
			var waypointCount = Math.Min(MaximumMoveWaypoints, orderedPath.Length);
			var queued = false;
			for (var i = 1; i <= waypointCount; i++)
			{
				var index = (int)((long)i * orderedPath.Length / waypointCount) - 1;
				QueueMoveOrder(null, actor, orderedPath[index], queued);
				queued = true;
			}

			return true;
		}

		void QueueTransportMove(IBot bot, Actor transport, CPos destination)
		{
			if (transport == null || transport.Disposed || !transport.IsInWorld || transport.IsDead)
				return;

			if (Info.AirTransportTypes.Contains(transport.Info.Name))
			{
				bot.QueueOrder(new Order("Land", transport, Target.FromCell(world, destination), false));
				return;
			}

			if (Info.LandingCraftTypes.Contains(transport.Info.Name))
			{
				// The capture-transport planner has already proven this pickup/drop naval leg using
				// fair RiskModel intel. Native Move now owns cell-by-cell LST path execution.
				// Do not install a dynamic Frans GetPathCost callback while the craft is moving.
				QueueMoveOrder(bot, transport, destination);
				return;
			}

			QueueGroundRiskAwareMove(transport, destination, TransportRiskRole(transport), FransRiskTolerance.Cautious);
		}

		void QueuePlainRetreatMove(IBot bot, Actor transport, CPos destination)
		{
			if (transport == null || transport.Disposed || !transport.IsInWorld || transport.IsDead || !world.Map.Contains(destination))
				return;

			if (IsAirTransport(transport))
				bot.QueueOrder(new Order("Land", transport, Target.FromCell(world, destination), false));
			else
				QueueMoveOrder(bot, transport, destination);
		}

		void QueuePickupMoves(IBot bot, TransportMission mission)
		{
			var passenger = mission.Passenger;
			var transport = mission.Transport;

			if (passenger.IsInWorld && passenger.Location != mission.PickupPassengerCell)
				QueueGroundRiskAwareMove(passenger, mission.PickupPassengerCell, FransRiskRole.Capturer, FransRiskTolerance.Cautious);

			if (transport.IsInWorld && transport.Location != mission.PickupTransportCell)
			{
				if (IsAirTransport(transport) && Info.EnableAirTransportRiskRouting)
				{
					if (!StartAirMove(bot, mission, mission.PickupTransportCell, "pickup"))
						FailAssignedTransport(mission);
				}
				else
					QueueTransportMove(bot, transport, mission.PickupTransportCell);
			}
		}

		void ManagePickup(IBot bot, TransportMission mission)
		{
			if (!ValidateAssignedTransport(mission))
			{
				FailAssignedTransport(mission);
				return;
			}

			if (IsPassengerLoaded(mission))
			{
				mission.BoardingOrderIssued = false;
				BeginLoadedMove(bot, mission);
				return;
			}

			var passenger = mission.Passenger;
			var transport = mission.Transport;
			var passengerTrait = passenger.TraitOrDefault<Passenger>();
			if (passengerTrait == null)
			{
				FailAssignedTransport(mission);
				return;
			}

			if (!passenger.IsInWorld)
				return;

			if (Info.GroundTransportTypes.Contains(transport.Info.Name))
				ApplyCaptureEscortHoldFire(mission);

			// once native EnterTransport has been issued, boarding owns the passenger.
			// ReservedCargo is the strongest signal, but the queued activity may need a few ticks
			// before that reservation appears. Do not let the pickup-progress watchdog cancel or
			// replace native boarding during that window. Only retry after the native activity has
			// actually ended (passenger idle, no reservation) and the normal retry interval elapsed.
			if (mission.BoardingOrderIssued || passengerTrait.ReservedCargo != null)
			{
				if (passengerTrait.ReservedCargo != null || !passenger.IsIdle || world.WorldTick < mission.NextBoardingRetryTick)
					return;

				mission.BoardingOrderIssued = false;
			}

			var passengerPickupDistanceSquared = (passenger.Location - mission.PickupPassengerCell).LengthSquared;
			var passengerAtPickup = passengerPickupDistanceSquared <= Info.PickupArrivalRadius * Info.PickupArrivalRadius;
			if (!passengerAtPickup)
			{
				var watchdogDue = world.WorldTick >= mission.NextPassengerPickupReassertTick;
				var notMakingProgress = watchdogDue && passengerPickupDistanceSquared >= mission.LastPassengerPickupDistanceSquared;
				if (watchdogDue && (passenger.IsIdle || notMakingProgress))
					QueueGroundRiskAwareMove(passenger, mission.PickupPassengerCell, FransRiskRole.Capturer, FransRiskTolerance.Cautious);

				if (watchdogDue)
				{
					mission.LastPassengerPickupDistanceSquared = passengerPickupDistanceSquared;
					mission.NextPassengerPickupReassertTick = world.WorldTick + Info.PassengerPickupReassertInterval;
				}
			}

			var transportAtPickup =
				(transport.Location - mission.PickupTransportCell).LengthSquared <= Info.PickupArrivalRadius * Info.PickupArrivalRadius;
			if (!transportAtPickup)
			{
				if (IsAirTransport(transport) && Info.EnableAirTransportRiskRouting)
				{
					if (!ManageAirMove(bot, mission, mission.PickupTransportCell, "pickup", loaded: false))
					{
						FransBotLog.BotDebug(world,
							"{0}: capture TRAN {1} cannot keep a non-critical bounded corridor to pickup {2}; releasing it and trying another transport.",
							player, transport, mission.PickupTransportCell);
						FailAssignedTransport(mission);
						return;
					}
				}
				else
					ManageNonAirMove(bot, mission, mission.PickupTransportCell);
			}

			if (!passengerAtPickup || !transportAtPickup || !passenger.IsIdle || world.WorldTick < mission.NextBoardingRetryTick)
				return;

			var cargo = transport.TraitOrDefault<Cargo>();
			if (cargo == null || cargo.IsTraitDisabled || !cargo.Info.Types.Contains(passengerTrait.Info.CargoType) ||
				!cargo.HasSpace(passengerTrait.Info.Weight))
			{
				FailAssignedTransport(mission);
				return;
			}

			if (Info.LandingCraftTypes.Contains(transport.Info.Name) && IsPendingExpansionLandingCraft(transport))
			{
				if (ResetMissionForStrategicLSTPreemption(bot, mission, transport))
					FransBotLog.BotDebug(world,
						"{0}: final MCV strategic LST priority check releases empty pre-load transport LST {1} from passenger {2} immediately before EnterTransport. The passenger mission remains active in WAITING.",
						player, transport, passenger);
				return;
			}

			if (mission.NextBoardingRetryTick == 0)
				FransBotLog.BotDebug(world, "{0}: {1} is boarding capture transport {2}; native EnterTransport now owns the passenger until load or a clean failed retry.", player, passenger, transport);
			mission.BoardingOrderIssued = true;
			mission.NextBoardingRetryTick = world.WorldTick + Info.BoardingRetryInterval;
			bot.QueueOrder(new Order("EnterTransport", passenger, Target.FromActor(transport), false));
		}

		void BeginLoadedMove(IBot bot, TransportMission mission)
		{
			mission.BoardingOrderIssued = false;
			if (mission.Transport != null && Info.GroundTransportTypes.Contains(mission.Transport.Info.Name))
				ApplyCaptureEscortHoldFire(mission);
			mission.StartedTick = world.WorldTick;
			mission.State = MissionState.Move;
			ResetTransportMoveState(mission);
			RefreshMovingTargetGroundDropAtBoarding(mission);
			if (!IsLandingCraftLegStillSafe(mission, mission.DropTransportCell, out var landingCraftFailure))
			{
				BeginRetreat(bot, mission, landingCraftFailure);
				return;
			}
			FransBotLog.BotDebug(world, "{0}: {1} loaded into {2}; MOVE begins toward {3}.",
				player, mission.Passenger, mission.Transport, mission.DropTransportCell);

			if (IsAirTransport(mission.Transport) && Info.EnableAirTransportRiskRouting)
			{
				if (!StartAirMove(bot, mission, mission.DropTransportCell, "loaded capture"))
					BeginRetreat(bot, mission, "no non-critical bounded corridor remained after E6 boarded");
			}
			else
				QueueTransportMove(bot, mission.Transport, mission.DropTransportCell);
		}

		void RefreshMovingTargetGroundDropAtBoarding(TransportMission mission)
		{
			if (mission?.Target == null || mission.Target.Disposed || !mission.Target.IsInWorld || mission.Target.IsDead ||
				mission.Target.Info.HasTraitInfo<BuildingInfo>() || mission.Transport == null ||
				!Info.GroundTransportTypes.Contains(mission.Transport.Info.Name))
				return;

			var transport = mission.Transport;
			var transportMobile = transport.TraitOrDefault<Mobile>();
			var passengerMobile = mission.Passenger?.TraitOrDefault<Mobile>();
			if (transportMobile == null || passengerMobile == null || transportMobile.IsTraitDisabled || transportMobile.IsTraitPaused)
				return;

			var targetCell = mission.Target.Location;
			var targetLandmassKnown = strategicMapService.TryGetGroundLandmassId(targetCell, out var targetLandmassId);
			foreach (var drop in world.Map.FindTilesInAnnulus(targetCell, Info.MinimumDropRadius, Info.MaximumDropRadius)
				.Where(c => world.Map.Contains(c) && transportMobile.CanEnterCell(c, check: BlockedByActor.Immovable) &&
					transportMobile.CanStayInCell(c) &&
					!riskModelService.EvaluateCell(transport, c, FransRiskRole.SupportVehicle, FransRiskTolerance.Cautious).IsCritical)
				.Where(c => !targetLandmassKnown ||
					(strategicMapService.TryGetGroundLandmassId(c, out var id) && id == targetLandmassId))
				.OrderBy(c => (c - targetCell).LengthSquared).ThenBy(c => c.Y).ThenBy(c => c.X)
				.Take(Info.GroundTransportMaximumDropCandidates))
			{
				if (!AdjacentCells(drop).Any(c => passengerMobile.CanEnterCell(c, check: BlockedByActor.Immovable) && passengerMobile.CanStayInCell(c)) ||
					!TryFindPath(transport, transportMobile, transportMobile.ToCell, drop, out _))
					continue;

				if (mission.DropTransportCell != drop)
					FransBotLog.BotDebug(world,
						"{0}: moving SpecOps target {1} refreshed ground-transport drop at boarding: {2} -> {3}. Transport now commits to this intercept; after unload the specialist resumes native pursuit/capture.",
						player, mission.Target, mission.DropTransportCell, drop);
				mission.DropTransportCell = drop;
				return;
			}
		}

		void ManageMove(IBot bot, TransportMission mission)
		{
			if (!ValidateAssignedTransport(mission))
			{
				ReleaseTransport(mission);
				missions.Remove(mission.Passenger);
				return;
			}

			if (!IsPassengerLoaded(mission))
			{
				if (mission.Passenger.IsInWorld)
				{
					FransBotLog.BotDebug(world,
						"{0}: capture passenger {1} left transport {2} before DROP; mission is released for SpecOps reconsideration.",
						player, mission.Passenger, mission.Transport);
					ReleaseTransport(mission);
					missions.Remove(mission.Passenger);
				}
				return;
			}

			var transport = mission.Transport;
			if (Info.GroundTransportTypes.Contains(transport.Info.Name))
				ApplyCaptureEscortHoldFire(mission);
			if (!IsLandingCraftLegStillSafe(mission, mission.DropTransportCell, out var landingCraftFailure))
			{
				BeginRetreat(bot, mission, landingCraftFailure);
				return;
			}

			var distanceSquared = (transport.Location - mission.DropTransportCell).LengthSquared;
			if (distanceSquared > Info.DropArrivalRadius * Info.DropArrivalRadius)
			{
				if (IsAirTransport(transport) && Info.EnableAirTransportRiskRouting)
				{
					if (!ManageAirMove(bot, mission, mission.DropTransportCell, "loaded capture", loaded: true))
						BeginRetreat(bot, mission, "newly critical known risk blocks the remaining capture corridor");
				}
				else
					ManageNonAirMove(bot, mission, mission.DropTransportCell);
				return;
			}

			if (Info.GroundTransportTypes.Contains(transport.Info.Name))
			{
				// arrival owns the transition. A stale auto-target/move activity must
				// never keep Tanya/E6/Thief trapped in Cargo at the drop point.
				ApplyCaptureEscortHoldFire(mission);
				BeginDrop(bot, mission);
				return;
			}

			if (!transport.IsIdle)
				return;

			BeginDrop(bot, mission);
		}

		bool WaitForSynchronizedIdleBeforeUnload(IBot bot, TransportMission mission, bool issueStop)
		{
			var transport = mission?.Transport;
			if (transport == null || transport.Disposed || !transport.IsInWorld || transport.IsDead)
				return true;

			if (transport.IsIdle)
			{
				if (mission.UnloadStopOrderTransport == transport)
					mission.UnloadStopOrderTransport = null;
				return false;
			}

			if (issueStop && mission.UnloadStopOrderTransport != transport)
			{
				QueueStopOrder(bot, transport);
				mission.UnloadStopOrderTransport = transport;
			}

			return true;
		}

		void BeginDrop(IBot bot, TransportMission mission)
		{
			var transport = mission.Transport;
			if (transport == null || transport.Disposed || !transport.IsInWorld || transport.IsDead)
			{
				ReleaseTransport(mission);
				if (mission.Passenger != null)
					missions.Remove(mission.Passenger);
				return;
			}

			if (Info.GroundTransportTypes.Contains(transport.Info.Name))
				ApplyCaptureEscortHoldFire(mission);

			if (WaitForSynchronizedIdleBeforeUnload(bot, mission, issueStop: true))
				return;

			var cargo = transport.TraitOrDefault<Cargo>();
			if (cargo == null || !cargo.CanUnload())
				return;

			mission.StartedTick = world.WorldTick;
			mission.State = MissionState.Drop;
			mission.NextUnloadRetryTick = world.WorldTick + Info.UnloadRetryInterval;
			FransBotLog.BotDebug(world, "{0}: capture transport {1} begins DROP; issuing one native Unload for {2}.",
				player, mission.Transport, mission.Passenger);
			bot.QueueOrder(new Order("Unload", mission.Transport, false));
		}

		void ManageDrop(IBot bot, TransportMission mission)
		{
			var passenger = mission.Passenger;
			var transport = mission.Transport;
			if (passenger == null || passenger.Disposed || passenger.IsDead || transport == null ||
				transport.Disposed || !transport.IsInWorld || transport.IsDead)
			{
				ReleaseTransport(mission);
				if (passenger != null)
					missions.Remove(passenger);
				return;
			}

			var passengerTrait = passenger.TraitOrDefault<Passenger>();
			if (passengerTrait == null)
			{
				ReleaseTransport(mission);
				missions.Remove(passenger);
				return;
			}

			if (passenger.IsInWorld && passengerTrait.Transport == null)
			{
				CompleteUnload(mission);
				return;
			}

			var cargo = transport.TraitOrDefault<Cargo>();
			if (cargo == null || world.WorldTick < mission.NextUnloadRetryTick)
				return;

			if (passengerTrait.Transport == transport && cargo.Passengers.Contains(passenger) && cargo.CanUnload())
			{
				if (Info.GroundTransportTypes.Contains(transport.Info.Name))
					ApplyCaptureEscortHoldFire(mission);
				if (!transport.IsIdle)
					return;

				mission.NextUnloadRetryTick = world.WorldTick + Info.UnloadRetryInterval;
				bot.QueueOrder(new Order("Unload", transport, false));
			}
		}

		void CompleteUnload(TransportMission mission)
		{
			if (mission.CancelAfterDrop)
			{
				FransBotLog.BotDebug(world,
					"{0}: {1} safely unloaded from {2} after transport RETREAT; capture mission {3} is cancelled and may be reconsidered later.",
					player, mission.Passenger, mission.Transport, mission.Target);
				RegisterAbortedLoadedMissionCooldown(mission);
				ReleaseTransport(mission);
				missions.Remove(mission.Passenger);
				return;
			}

			if (mission.ReusableRoundTrip)
			{
				FransBotLog.BotDebug(world, "{0}: reusable SpecOps {1} unloaded from {2}; insertion handoff begins while the exact transport remains reserved for extraction.",
					player, mission.Passenger, mission.Transport);
				mission.StartedTick = world.WorldTick;
				mission.State = MissionState.Handoff;
				return;
			}

			FransBotLog.BotDebug(world, "{0}: {1} unloaded from {2}; handing the same actor back to FransSpecOps Commander for target {3}.",
				player, mission.Passenger, mission.Transport, mission.Target);

			var keepGroundEscort = mission.Transport != null && !mission.Transport.Disposed &&
				Info.GroundTransportTypes.Contains(mission.Transport.Info.Name);
			if (!keepGroundEscort)
			{
				ReleaseTransport(mission);
				mission.Transport = null;
			}
			else if (!mission.Passenger.Disposed && mission.Passenger.IsInWorld && !mission.Passenger.IsDead &&
				!mission.Transport.Disposed && mission.Transport.IsInWorld && !mission.Transport.IsDead)
			{
				mission.Transport.CancelActivity();
				ApplyCaptureEscortHoldFire(mission);
			}

			mission.StartedTick = world.WorldTick;
			mission.State = MissionState.Handoff;
		}

		void ManageReusableStandby(TransportMission mission)
		{
			if (!ValidateAssignedTransport(mission))
			{
				if (mission.Passenger != null)
					missions.Remove(mission.Passenger);
				return;
			}

			if (Info.GroundTransportTypes.Contains(mission.Transport.Info.Name))
				ApplyCaptureEscortHoldFire(mission);

			if (Info.ReusableStandbyTimeout > 0 && mission.StandbyStartedTick > 0 &&
				world.WorldTick - mission.StandbyStartedTick >= Info.ReusableStandbyTimeout)
			{
				FransBotLog.BotDebug(world, "{0}: reusable SpecOps transport {1} timed out waiting for extraction of {2}; releasing transport reservation while specialist remains free in the field.",
					player, mission.Transport, mission.Passenger);
				ReleaseTransport(mission);
				missions.Remove(mission.Passenger);
			}
		}

		bool TryResolveExtractionPickup(TransportMission mission, out CPos passengerCell, out CPos transportCell)
		{
			passengerCell = default;
			transportCell = default;
			if (mission?.Passenger == null || mission.Transport == null || !mission.Passenger.IsInWorld || mission.Passenger.IsDead ||
				!mission.Transport.IsInWorld || mission.Transport.IsDead)
				return false;

			var passenger = mission.Passenger;
			var transport = mission.Transport;
			var passengerMobile = passenger.TraitOrDefault<Mobile>();
			if (passengerMobile == null || passengerMobile.IsTraitDisabled || passengerMobile.IsTraitPaused)
				return false;

			if (IsAirTransport(transport))
			{
				var aircraft = transport.TraitOrDefault<Aircraft>();
				if (aircraft == null)
					return false;
				foreach (var cell in world.Map.FindTilesInAnnulus(passenger.Location, 1, Math.Max(2, Info.GroundPickupSearchRadius))
					.Where(world.Map.Contains)
					.Where(c => aircraft.CanLand(c, blockedByMobile: false))
					.Where(c => !riskModelService.EvaluateCell(transport, c, FransRiskRole.Aircraft, FransRiskTolerance.Cautious).IsCritical)
					.OrderBy(c => (c - passenger.Location).LengthSquared)
					.ThenBy(c => c.X).ThenBy(c => c.Y))
				{
					foreach (var adjacent in AdjacentCells(cell).Where(c => world.Map.Contains(c) &&
						passengerMobile.CanEnterCell(c, check: BlockedByActor.Immovable) && passengerMobile.CanStayInCell(c) &&
						!riskModelService.EvaluateCell(passenger, c, FransRiskRole.Capturer, FransRiskTolerance.Cautious).IsCritical))
					{
						passengerCell = adjacent;
						transportCell = cell;
						return true;
					}
				}
				return false;
			}

			var transportMobile = transport.TraitOrDefault<Mobile>();
			if (transportMobile == null || transportMobile.IsTraitDisabled || transportMobile.IsTraitPaused)
				return false;
			var landingCraft = Info.LandingCraftTypes.Contains(transport.Info.Name);
			var transportRegion = 0;
			var hasTransportRegion = landingCraft &&
				strategicMapService.TryGetNavalRegionId(transportMobile.ToCell, out transportRegion);
			var candidateLimit = landingCraft ? Info.LandingCraftMaximumPickupCandidates : int.MaxValue;
			var pickupSearchRadius = landingCraft ? Info.LandingCraftPickupSearchRadius : Math.Max(2, Info.GroundPickupSearchRadius);
			foreach (var cell in world.Map.FindTilesInAnnulus(passenger.Location, 1, pickupSearchRadius)
				.Where(world.Map.Contains)
				.Where(c => !landingCraft || IsBeach(c))
				.Where(c => transportMobile.CanEnterCell(c, check: BlockedByActor.Immovable) && transportMobile.CanStayInCell(c))
				.Where(c => !landingCraft || !hasTransportRegion ||
					(strategicMapService.TryGetNavalRegionId(c, out var region) && region == transportRegion))
				.Where(c => !riskModelService.EvaluateCell(transport, c, TransportRiskRole(transport), FransRiskTolerance.Cautious).IsCritical)
				.OrderBy(c => (c - passenger.Location).LengthSquared)
				.ThenBy(c => c.X).ThenBy(c => c.Y)
				.Take(candidateLimit))
			{
				if (landingCraft &&
					(!TryFindPath(transport, transportMobile, transportMobile.ToCell, cell, out _) ||
					 !TryFindPath(transport, transportMobile, cell, mission.PickupTransportCell, out _)))
					continue;

				foreach (var adjacent in AdjacentCells(cell).Where(c => world.Map.Contains(c) &&
					passengerMobile.CanEnterCell(c, check: BlockedByActor.Immovable) && passengerMobile.CanStayInCell(c) &&
					!riskModelService.EvaluateCell(passenger, c, FransRiskRole.Capturer, FransRiskTolerance.Cautious).IsCritical &&
					(!landingCraft || HasPassengerPath(passenger, passengerMobile, passengerMobile.ToCell, c))))
				{
					passengerCell = adjacent;
					transportCell = cell;
					return true;
				}
			}
			return false;
		}

		void QueueExtractionPickupMoves(IBot bot, TransportMission mission)
		{
			if (mission.Passenger != null && mission.Passenger.IsInWorld && !mission.Passenger.IsDead)
				QueueGroundRiskAwareMove(mission.Passenger, mission.ExtractionPassengerCell, FransRiskRole.Capturer, FransRiskTolerance.Cautious);
			if (mission.Transport != null && mission.Transport.IsInWorld && !mission.Transport.IsDead)
			{
				if (IsAirTransport(mission.Transport) && Info.EnableAirTransportRiskRouting)
				{
					if (!StartAirMove(bot, mission, mission.ExtractionTransportCell, "reusable extraction pickup"))
						mission.Transport.CancelActivity();
				}
				else
					QueueTransportMove(bot, mission.Transport, mission.ExtractionTransportCell);
			}
		}

		void ManageExtractionPickup(IBot bot, TransportMission mission)
		{
			if (!ValidateAssignedTransport(mission) || mission.Passenger == null || mission.Passenger.Disposed || mission.Passenger.IsDead)
			{
				ReleaseTransport(mission);
				if (mission.Passenger != null) missions.Remove(mission.Passenger);
				return;
			}
			if (Info.GroundTransportTypes.Contains(mission.Transport.Info.Name))
				ApplyCaptureEscortHoldFire(mission);
			if (IsPassengerLoaded(mission))
			{
				mission.BoardingOrderIssued = false;
				mission.State = MissionState.ExtractReturn;
				mission.StartedTick = world.WorldTick;
				ResetTransportMoveState(mission);
				if (!IsLandingCraftLegStillSafe(mission, mission.PickupTransportCell, out var returnFailure))
				{
					BeginRetreat(bot, mission, returnFailure);
					return;
				}
				if (IsAirTransport(mission.Transport) && Info.EnableAirTransportRiskRouting)
				{
					if (!StartAirMove(bot, mission, mission.PickupTransportCell, "reusable extraction return"))
						mission.Transport.CancelActivity();
				}
				else
					QueueTransportMove(bot, mission.Transport, mission.PickupTransportCell);
				return;
			}
			if (!IsLandingCraftLegStillSafe(mission, mission.ExtractionTransportCell, out var landingCraftFailure))
			{
				FransBotLog.BotDebug(world,
					"{0}: reusable SpecOps LST extraction pickup releases {1} for {2}: {3}.",
					player, mission.Transport, mission.Passenger, landingCraftFailure);
				((IFransCaptureTransportService)this).CancelCaptureTransport(bot, mission.Passenger);
				return;
			}

			var passenger = mission.Passenger;
			var passengerTrait = passenger.TraitOrDefault<Passenger>();
			if (passengerTrait == null || !passenger.IsInWorld)
				return;

			if (mission.BoardingOrderIssued || passengerTrait.ReservedCargo != null)
			{
				if (passengerTrait.ReservedCargo != null || !passenger.IsIdle || world.WorldTick < mission.NextBoardingRetryTick)
					return;
				mission.BoardingOrderIssued = false;
			}

			var passengerAtPickup = (passenger.Location - mission.ExtractionPassengerCell).LengthSquared <= Info.PickupArrivalRadius * Info.PickupArrivalRadius;
			var transportAtPickup = (mission.Transport.Location - mission.ExtractionTransportCell).LengthSquared <= Info.PickupArrivalRadius * Info.PickupArrivalRadius;
			if (!passengerAtPickup && passenger.IsIdle)
				QueueGroundRiskAwareMove(passenger, mission.ExtractionPassengerCell, FransRiskRole.Capturer, FransRiskTolerance.Cautious);
			if (!transportAtPickup)
			{
				if (IsAirTransport(mission.Transport) && Info.EnableAirTransportRiskRouting)
					ManageAirMove(bot, mission, mission.ExtractionTransportCell, "reusable extraction pickup", loaded: false);
				else
					ManageNonAirMove(bot, mission, mission.ExtractionTransportCell);
			}
			if (!passengerAtPickup || !transportAtPickup || !passenger.IsIdle || world.WorldTick < mission.NextBoardingRetryTick)
				return;
			var cargo = mission.Transport.TraitOrDefault<Cargo>();
			if (cargo == null || cargo.IsTraitDisabled || !cargo.Info.Types.Contains(passengerTrait.Info.CargoType) || !cargo.HasSpace(passengerTrait.Info.Weight))
				return;
			mission.BoardingOrderIssued = true;
			mission.NextBoardingRetryTick = world.WorldTick + Info.BoardingRetryInterval;
			bot.QueueOrder(new Order("EnterTransport", passenger, Target.FromActor(mission.Transport), false));
		}

		void ManageExtractionReturn(IBot bot, TransportMission mission)
		{
			if (!ValidateAssignedTransport(mission))
			{
				if (mission.Passenger != null) missions.Remove(mission.Passenger);
				return;
			}
			if (!IsPassengerLoaded(mission))
				return;
			if (!IsLandingCraftLegStillSafe(mission, mission.PickupTransportCell, out var landingCraftFailure))
			{
				BeginRetreat(bot, mission, landingCraftFailure);
				return;
			}
			var distanceSquared = (mission.Transport.Location - mission.PickupTransportCell).LengthSquared;
			if (distanceSquared > Info.DropArrivalRadius * Info.DropArrivalRadius)
			{
				if (IsAirTransport(mission.Transport) && Info.EnableAirTransportRiskRouting)
					ManageAirMove(bot, mission, mission.PickupTransportCell, "reusable extraction return", loaded: true);
				else
					ManageNonAirMove(bot, mission, mission.PickupTransportCell);
				return;
			}
			var groundTransport = Info.GroundTransportTypes.Contains(mission.Transport.Info.Name);
			if (groundTransport)
				ApplyCaptureEscortHoldFire(mission);

			if (WaitForSynchronizedIdleBeforeUnload(bot, mission, issueStop: groundTransport))
				return;

			var cargo = mission.Transport.TraitOrDefault<Cargo>();
			if (cargo == null || !cargo.CanUnload())
				return;
			mission.State = MissionState.ExtractDrop;
			mission.StartedTick = world.WorldTick;
			mission.NextUnloadRetryTick = world.WorldTick + Info.UnloadRetryInterval;
			bot.QueueOrder(new Order("Unload", mission.Transport, false));
		}

		void ManageExtractionDrop(IBot bot, TransportMission mission)
		{
			var passenger = mission.Passenger;
			var transport = mission.Transport;
			if (passenger == null || passenger.Disposed || passenger.IsDead || transport == null || transport.Disposed || transport.IsDead)
			{
				ReleaseTransport(mission);
				if (passenger != null) missions.Remove(passenger);
				return;
			}
			var passengerTrait = passenger.TraitOrDefault<Passenger>();
			if (passenger.IsInWorld && passengerTrait?.Transport == null)
			{
				FransBotLog.BotDebug(world, "{0}: reusable SpecOps extraction completed: {1} returned with {2} and is available for another mission.", player, passenger, transport);
				ReleaseTransport(mission);
				missions.Remove(passenger);
				return;
			}
			var cargo = transport.TraitOrDefault<Cargo>();
			if (cargo != null && world.WorldTick >= mission.NextUnloadRetryTick && cargo.CanUnload())
			{
				if (Info.GroundTransportTypes.Contains(transport.Info.Name))
					ApplyCaptureEscortHoldFire(mission);
				if (!transport.IsIdle)
					return;
				mission.NextUnloadRetryTick = world.WorldTick + Info.UnloadRetryInterval;
				bot.QueueOrder(new Order("Unload", transport, false));
			}
		}

		void ManageEscort(IBot bot, TransportMission mission)
		{
			var transport = mission.Transport;
			if (transport == null || transport.Disposed || !transport.IsInWorld || transport.IsDead)
			{
				ReleaseTransport(mission);
				missions.Remove(mission.Passenger);
				return;
			}

			if (mission.Target != null && !mission.Target.Disposed && mission.Target.IsInWorld && !mission.Target.IsDead && mission.Target.Owner == player)
			{
				BeginReturnHome(bot, mission, "capture confirmed complete");
				return;
			}

			if (mission.Target == null || mission.Target.Disposed || !mission.Target.IsInWorld || mission.Target.IsDead || !IsValidCaptureTarget(mission.Target))
			{
				BeginReturnHome(bot, mission, "capture target was lost");
				return;
			}

			if (mission.Passenger == null || mission.Passenger.Disposed || mission.Passenger.IsDead)
			{
				BeginReturnHome(bot, mission, "engineer was lost before capture completed");
				return;
			}

			if (!mission.Passenger.IsInWorld)
			{
				if (mission.PassengerMissingSinceTick < 0)
					mission.PassengerMissingSinceTick = world.WorldTick;
				if (world.WorldTick - mission.PassengerMissingSinceTick >= Info.CaptureCompletionGraceTicks)
					BeginReturnHome(bot, mission, "engineer left the world but capture was not confirmed");
				return;
			}

			mission.PassengerMissingSinceTick = -1;
			ApplyCaptureEscortHoldFire(mission);

			if (mission.EscortThreat != null)
			{
				if (!IsActiveThreatAgainstEngineer(mission.EscortThreat, mission.Passenger) ||
					(mission.EscortThreat.Location - mission.Passenger.Location).LengthSquared >
						Info.CaptureEscortThreatRadius * Info.CaptureEscortThreatRadius)
				{
					transport.CancelActivity();
					mission.EscortThreat = null;
					ApplyCaptureEscortHoldFire(mission);
				}
				else
					return;
			}

			if (transport.IsIdle)
				TryEngageCaptureEscortThreat(bot, mission);
		}

		void ApplyCaptureEscortHoldFire(TransportMission mission)
		{
			var transport = mission.Transport;
			if (transport == null || transport.Disposed || !transport.IsInWorld || transport.IsDead)
				return;

			var autoTarget = transport.TraitOrDefault<AutoTarget>();
			if (autoTarget == null)
				return;

			if (!mission.EscortHoldFireApplied)
			{
				mission.OriginalTransportStance = autoTarget.Stance;
				mission.EscortHoldFireApplied = true;
				QueueSetUnitStanceOrder(null, transport, UnitStance.HoldFire);
			}
		}

		void RestoreCaptureEscortStance(TransportMission mission)
		{
			if (mission == null || !mission.EscortHoldFireApplied)
				return;

			var transport = mission.Transport;
			if (transport != null && !transport.Disposed && transport.IsInWorld && !transport.IsDead)
			{
				var autoTarget = transport.TraitOrDefault<AutoTarget>();
				if (autoTarget != null && mission.OriginalTransportStance.HasValue)
					QueueSetUnitStanceOrder(null, transport, mission.OriginalTransportStance.Value);
			}

			mission.EscortThreat = null;
			mission.EscortHoldFireApplied = false;
			mission.OriginalTransportStance = null;
		}

		bool IsActiveThreatAgainstEngineer(Actor threat, Actor engineer)
		{
			if (threat == null || engineer == null || threat.Disposed || engineer.Disposed || !threat.IsInWorld || threat.IsDead ||
				!engineer.IsInWorld || engineer.IsDead || threat.Owner == null ||
				player.RelationshipWith(threat.Owner) != PlayerRelationship.Enemy || !threat.CanBeViewedByPlayer(player))
				return false;

			var attackFollow = threat.TraitOrDefault<AttackFollow>();
			if (attackFollow != null)
			{
				if (attackFollow.RequestedTarget.Type == TargetType.Actor && attackFollow.RequestedTarget.Actor == engineer)
					return true;
				if (attackFollow.OpportunityTarget.Type == TargetType.Actor && attackFollow.OpportunityTarget.Actor == engineer)
					return true;
			}

			var activity = threat.CurrentActivity;
			return activity != null && activity.GetTargets(threat)
				.Any(t => t.Type == TargetType.Actor && t.Actor == engineer);
		}

		void TryEngageCaptureEscortThreat(IBot bot, TransportMission mission)
		{
			var transport = mission.Transport;
			var passenger = mission.Passenger;
			if (transport == null || passenger == null || transport.Disposed || passenger.Disposed || !transport.IsInWorld || transport.IsDead ||
				!passenger.IsInWorld || passenger.IsDead)
				return;

			var threat = world.FindActorsInCircle(passenger.CenterPosition, WDist.FromCells(Info.CaptureEscortThreatRadius))
				.Where(a => a != null && !a.Disposed && a.IsInWorld && !a.IsDead && a != mission.Target &&
					a.Owner != null && player.RelationshipWith(a.Owner) == PlayerRelationship.Enemy &&
					a.CanBeViewedByPlayer(player) && !a.Info.HasTraitInfo<BuildingInfo>() &&
					a.TraitOrDefault<Mobile>() != null && a.Info.HasTraitInfo<AttackBaseInfo>() &&
					IsActiveThreatAgainstEngineer(a, passenger))
				.OrderBy(a => (a.Location - passenger.Location).LengthSquared)
				.ThenBy(a => a.ActorID)
				.FirstOrDefault();

			if (threat == null)
				return;

			mission.EscortThreat = threat;
			FransBotLog.BotDebug(world,
				"{0}: capture APC {1} remains silent until {2} targets engineer {3}; now engaging only that threat while capture target {4} remains protected from APC fire.",
				player, transport, threat, passenger, mission.Target);
			bot.QueueOrder(new Order("Attack", transport, Target.FromActor(threat), false));
		}

		void BeginReturnHome(IBot bot, TransportMission mission, string reason)
		{
			var transport = mission.Transport;
			if (transport == null || transport.Disposed || !transport.IsInWorld || transport.IsDead)
			{
				ReleaseTransport(mission);
				missions.Remove(mission.Passenger);
				return;
			}

			mission.State = MissionState.Return;
			mission.StartedTick = world.WorldTick;
			ResetTransportMoveState(mission);
			FransBotLog.BotDebug(world, "{0}: capture APC {1} is returning home to {2} because {3}.",
				player, transport, mission.PickupTransportCell, reason);
			QueueTransportMove(bot, transport, mission.PickupTransportCell);
		}

		void ManageReturnHome(IBot bot, TransportMission mission)
		{
			var transport = mission.Transport;
			if (transport == null || transport.Disposed || !transport.IsInWorld || transport.IsDead)
			{
				ReleaseTransport(mission);
				missions.Remove(mission.Passenger);
				return;
			}

			var distanceSquared = (transport.Location - mission.PickupTransportCell).LengthSquared;
			if (distanceSquared <= Info.PickupArrivalRadius * Info.PickupArrivalRadius)
			{
				transport.CancelActivity();
				ReleaseTransport(mission);
				missions.Remove(mission.Passenger);
				return;
			}

			ManageNonAirMove(bot, mission, mission.PickupTransportCell);
		}

		void ResetTransportMoveState(TransportMission mission)
		{
			mission.AirWaypoints.Clear();
			mission.AirWaypointIndex = 0;
			mission.AirDestination = default;
			mission.NextAirRiskCheckTick = world.WorldTick;
			mission.LastAirRiskRevision = -1;
			mission.NextNavalRiskCheckTick = world.WorldTick + Math.Max(250, Info.TransportStallReplanTicks);
			mission.LastNavalRiskRevision = riskModelService?.RiskRevision ?? -1;
			// A new LST leg must prove its own destination even when global loss/risk
			// revisions were already consumed by the preceding leg.
			mission.LandingCraftLegValidationPending = true;
			mission.RetreatDropCell = null;
			if (mission.Transport != null)
			{
				mission.LastTransportProgressCell = mission.Transport.Location;
				mission.LastTransportProgressTick = world.WorldTick;
			}
		}

		bool IsLandingCraftLegStillSafe(TransportMission mission, CPos destination, out string failureReason)
		{
			failureReason = null;
			var transport = mission?.Transport;
			if (transport == null || !Info.LandingCraftTypes.Contains(transport.Info.Name))
				return true;

			var mobile = transport.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused)
			{
				failureReason = "LST mobility is unavailable for the remaining naval transport leg";
				return false;
			}

			var initialLegValidation = mission.LandingCraftLegValidationPending;
			if (initialLegValidation || mission.LastTransportLossExclusionRevision != generalService.TransportLossExclusionRevision)
			{
				mission.LastTransportLossExclusionRevision = generalService.TransportLossExclusionRevision;
				if (!IsLandingCraftRouteLossSafe(transport, mobile, mobile.ToCell, destination))
				{
					failureReason = "new LST-loss SECURE blocks the remaining naval transport leg";
					return false;
				}
			}

			if (!initialLegValidation && world.WorldTick < mission.NextNavalRiskCheckTick)
				return true;

			mission.NextNavalRiskCheckTick = world.WorldTick + Math.Max(250, Info.TransportStallReplanTicks);
			if (!initialLegValidation && riskModelService.RiskRevision == mission.LastNavalRiskRevision)
				return true;

			mission.LastNavalRiskRevision = riskModelService.RiskRevision;
			var immediateRisk = riskModelService.EvaluateImmediateRisk(transport, transport.Location,
				FransRiskRole.NavalTransport, FransRiskTolerance.Cautious);
			var destinationRisk = riskModelService.EvaluateCell(transport, destination,
				FransRiskRole.NavalTransport, FransRiskTolerance.Cautious);
			if (immediateRisk.IsCritical || destinationRisk.IsCritical)
			{
				failureReason = "newly CRITICAL fair-intel pressure reached the LST or its destination endpoint";
				return false;
			}

			mission.LandingCraftLegValidationPending = false;
			return true;
		}

		bool TransportMadeProgress(TransportMission mission)
		{
			var transport = mission.Transport;
			if (transport == null)
				return false;
			if (transport.Location == mission.LastTransportProgressCell)
				return false;
			mission.LastTransportProgressCell = transport.Location;
			mission.LastTransportProgressTick = world.WorldTick;
			return true;
		}

		bool IsTransportStalled(TransportMission mission)
		{
			TransportMadeProgress(mission);
			return world.WorldTick - mission.LastTransportProgressTick >= Info.TransportStallReplanTicks;
		}

		void ManageNonAirMove(IBot bot, TransportMission mission, CPos destination)
		{
			var transport = mission.Transport;
			if (transport == null || transport.Disposed || !transport.IsInWorld || transport.IsDead)
				return;

			if (!IsTransportStalled(mission))
				return;

			QueueTransportMove(bot, transport, destination);
			mission.LastTransportProgressCell = transport.Location;
			mission.LastTransportProgressTick = world.WorldTick;
		}

		void RequestBestTransport(IBot bot, TransportMission mission, bool landPathAvailable)
		{
			if (playerResources == null ||
				playerResources.GetCashAndResources() < Info.MinimumCashForTransportProduction ||
				world.WorldTick < mission.NextProductionRequestTick)
				return;

			var unitBuilder = requestUnitProduction?.FirstEnabledTraitOrDefault();
			if (unitBuilder == null)
				return;

			foreach (var type in PreferredTransportTypesFor(mission))
			{
				if (mission.FailedTransportTypes.Contains(type) ||
					!CanRequestTransportType(type, mission.Passenger, mission.Target, landPathAvailable))
					continue;

				if (Info.LandingCraftTypes.Contains(type) &&
					!HasLossSafeLandingCraftProductionCorridor(mission.Passenger, mission.Target))
				{
					mission.NextProductionRequestTick = world.WorldTick + Info.ProductionRequestCooldown;
					if (mission.LastProductionLossBlockRevision != generalService.TransportLossExclusionRevision)
					{
						mission.LastProductionLossBlockRevision = generalService.TransportLossExclusionRevision;
						FransBotLog.BotDebug(world,
							"{0}: capture/SpecOps transport does not request a fresh {1} for {2} -> {3}; every fair-known common shoreline corridor currently intersects an active LST-loss SECURE exclusion. Air/ground alternatives may still be considered, and LST demand retries automatically when the incident revision changes.",
							player, type, mission.Passenger, mission.Target);
					}
					continue;
				}

				if (Info.LandingCraftTypes.Contains(type) &&
					IsLandingCraftProductionSuppressed(type, mission.Passenger, mission.Target, out var structuralLandingFailure))
				{
					if (structuralLandingFailure)
						mission.FailedTransportTypes.Add(type);
					if (mission.RequestedTransportType != type)
						FransBotLog.BotDebug(world,
							structuralLandingFailure
								? "{0}: capture/SpecOps rejects fresh {1} production for {2} -> {3}; no common fair-known naval region connects the passenger and target shore networks. This mission will not manufacture replacement LSTs."
								: "{0}: capture/SpecOps suppresses fresh {1} production for {2} -> {3}; every common naval region is still covered by the shared negative LST route proof. Existing craft may be retried only after the bounded proof cooldown/topology change.",
							player, type, mission.Passenger, mission.Target);
					mission.RequestedTransportType = type;
					mission.NextProductionRequestTick = world.WorldTick + Info.ProductionRequestCooldown;
					continue;
				}

				var pendingProduction = CountPendingProduction(bot, unitBuilder, type);
				if (Info.GroundTransportTypes.Contains(type))
				{
					if (IsGroundTransportProductionSuppressed(type, mission.Passenger, mission.Target))
					{
						if (mission.RequestedTransportType != type)
							FransBotLog.BotDebug(world,
								"{0}: capture/SpecOps ground transport does not request another {1} for {2} -> {3}; an equivalent same-landmass {1} already proved this endpoint route impossible and the shared negative proof is still valid. Another transport type may be tried without flooding the Vehicle queue.",
								player, type, mission.Passenger, mission.Target);
						mission.RequestedTransportType = type;
						mission.NextProductionRequestTick = world.WorldTick + Info.ProductionRequestCooldown;
						continue;
					}

					var physicalGround = CountLiveOwnedTransportType(type);
					var totalGround = physicalGround + pendingProduction;
					if (totalGround >= Info.MaximumGroundTransportsPerType)
					{
						if (mission.RequestedTransportType != type)
							FransBotLog.BotDebug(world,
								"{0}: capture/SpecOps ground transport demand holds at physical+pending {1} pool {2}/{3} for {4} -> {5}; no additional identical vehicle is produced. Existing craft must become available or another transport type must serve the mission.",
								player, type, totalGround, Info.MaximumGroundTransportsPerType, mission.Passenger, mission.Target);
						mission.RequestedTransportType = type;
						mission.NextProductionRequestTick = world.WorldTick + Info.ProductionRequestCooldown;
						continue;
					}
				}

				if (Info.AirTransportTypes.Contains(type))
				{
					var physical = CountLiveOwnedTransportType(type);
					var totalAirTransports = physical + pendingProduction;
					var cap = mission.ReusableRoundTrip
						? Math.Min(Info.MaximumAirTransports, Info.MaximumReusableSpecOpsAirTransports)
						: Info.MaximumAirTransports;
					if (totalAirTransports >= cap)
					{
						if (mission.RequestedTransportType != type)
							FransBotLog.BotDebug(world, mission.ReusableRoundTrip
								? "{0}: reusable SpecOps transport demand holds at shared physical+pending {1} pool {2}/{3} for {4} -> {5}; existing craft must succeed, fail the route proof, or free up. No additional identical transport is produced."
								: "{0}: capture transport demand holds at shared physical+pending {1} pool {2}/{3} for {4} -> {5}; capture waits for an existing craft instead of producing another TRAN.",
								player, type, totalAirTransports, cap, mission.Passenger, mission.Target);
						mission.RequestedTransportType = type;
						mission.NextProductionRequestTick = world.WorldTick + Info.ProductionRequestCooldown;
						return;
					}
				}

				if (Info.LandingCraftTypes.Contains(type))
				{
					var landingCraftService = (IFransCaptureTransportService)this;
					var totalLandingCraft = landingCraftService.CountLandingCraftPool(bot);
					var nonStrategicCap = landingCraftService.MaximumNonStrategicLandingCraftPool;
					if (totalLandingCraft >= nonStrategicCap)
					{
						if (mission.RequestedTransportType != type)
							FransBotLog.BotDebug(world,
								"{0}: capture/SpecOps LST production holds at non-strategic pool {1}/{2} (global hard cap {3}) for {4} -> {5}. The final pool slot is reserved for PIONEER regional sea-expansion supply; existing craft remain reusable by capture when strategically free.",
								player, totalLandingCraft, nonStrategicCap, Info.MaximumLandingCraftPool, mission.Passenger, mission.Target);
						mission.RequestedTransportType = type;
						mission.NextProductionRequestTick = world.WorldTick + Info.ProductionRequestCooldown;
						return;
					}
				}

				// Pending production is authoritative, and every transport domain now has an explicit
				// physical+pending fleet bound so busy or route-incompatible craft cannot trigger
				// unbounded duplicate production.
				if (pendingProduction > 0)
				{
					mission.RequestedTransportType = type;
					mission.NextProductionRequestTick = world.WorldTick + Info.ProductionRequestCooldown;
					return;
				}

				if (Info.LandingCraftTypes.Contains(type) &&
					amphibiousExpansionService?.HasStrategicLandingCraftProductionDemand == true)
				{
					FransBotLog.BotDebug(world,
						"{0}: capture/SpecOps transport yields ALL new LST assignment/production to the strategic MCV sea expansion. Passenger {1} waits for another transport type or until the MCV claim closes.",
						player, mission.Passenger);
					continue;
				}

				unitBuilder.RequestUnitProduction(bot, type);
				mission.LastProductionRequestTick = world.WorldTick;
				mission.RequestedTransportType = type;
				mission.NextProductionRequestTick = world.WorldTick + Info.ProductionRequestCooldown;

				FransBotLog.BotDebug(world, mission.ReusableRoundTrip
					? "{0}: reusable SpecOps transport requested {1} for specialist {2} targeting {3}."
					: "{0}: capture transport requested {1} for engineer {2} targeting {3}.",
					player, type, mission.Passenger, mission.Target);
				return;
			}
		}

		bool HasLossSafeLandingCraftProductionCorridor(Actor passenger, Actor target)
		{
			if (passenger == null || target == null || strategicMapService == null || generalService == null ||
				!strategicMapService.TryGetGroundLandmassId(passenger.Location, out var sourceLandmass) ||
				!strategicMapService.TryGetGroundLandmassId(target.Location, out var targetLandmass))
				return true;

			var source = strategicMapService.GetGroundShoreAccess(sourceLandmass)
				.OrderBy(s => (s.GroundCell - passenger.Location).LengthSquared)
				.ThenBy(s => s.NavalCell.X).ThenBy(s => s.NavalCell.Y).Take(8).ToArray();
			var destination = strategicMapService.GetGroundShoreAccess(targetLandmass)
				.OrderBy(s => (s.GroundCell - target.Location).LengthSquared)
				.ThenBy(s => s.NavalCell.X).ThenBy(s => s.NavalCell.Y).Take(8).ToArray();
			var foundCommonNavalRegion = false;
			foreach (var pickup in source)
				foreach (var drop in destination)
				{
					if (pickup.NavalRegionId != drop.NavalRegionId)
						continue;
					foundCommonNavalRegion = true;
					if (generalService.IsTransportLossCorridorAllowed(pickup.NavalCell, drop.NavalCell))
						return true;
				}

			// Preserve pre-existing behavior when static topology itself is unresolved; the physical
			// transport planner remains authoritative once a craft exists. Only a positively known
			// common naval corridor that is blocked by loss memory suppresses production here.
			return !foundCommonNavalRegion;
		}

		bool IsLandingCraftProductionSuppressed(string type, Actor passenger, Actor target, out bool structuralFailure)
		{
			structuralFailure = false;
			if (!Info.LandingCraftTypes.Contains(type) || passenger == null || target == null ||
				!strategicMapService.TryGetGroundLandmassId(passenger.Location, out var sourceLandmass) ||
				!strategicMapService.TryGetGroundLandmassId(target.Location, out var targetLandmass))
				return false;

			var terrainVersion = strategicMapService.TerrainKnowledgeVersion;
			if (sharedLandingCraftTopologyVersion != terrainVersion)
			{
				sharedLandingCraftTopologyVersion = terrainVersion;
				sharedLandingCraftTopologyFailures.Clear();
				sharedLandingCraftFailureUntil.Clear();
			}

			var sourceRegions = strategicMapService.GetGroundShoreAccess(sourceLandmass)
				.Select(s => s.NavalRegionId).Distinct().ToHashSet();
			var commonRegions = strategicMapService.GetGroundShoreAccess(targetLandmass)
				.Select(s => s.NavalRegionId).Distinct().Where(sourceRegions.Contains).OrderBy(x => x).ToArray();
			if (commonRegions.Length == 0)
			{
				structuralFailure = true;
				return true;
			}

			var anyOpenRegion = false;
			foreach (var navalRegion in commonRegions)
			{
				var key = new SharedLandingCraftFailureKey(type, passenger.ActorID, target.ActorID,
					sourceLandmass, targetLandmass, navalRegion, terrainVersion);
				if (sharedLandingCraftTopologyFailures.Contains(key))
					continue;
				if (sharedLandingCraftFailureUntil.TryGetValue(key, out var until))
				{
					if (world.WorldTick < until)
						continue;
					sharedLandingCraftFailureUntil.Remove(key);
				}
				anyOpenRegion = true;
				break;
			}

			return !anyOpenRegion;
		}

		int CountPendingProduction(IBot bot, IBotRequestUnitProduction unitBuilder, string type)
		{
			// This helper counts only pending/requested production. RequestBestTransport combines it
			// with authoritative physical counts for transport domains that have a hard production cap.
			var requested = unitBuilder.RequestedProductionCount(bot, type);
			if (!world.Map.Rules.Actors.TryGetValue(type, out var info))
				return requested;

			var buildable = info.TraitInfoOrDefault<BuildableInfo>();
			if (buildable == null)
				return requested;

			var queues = AIUtils.FindQueuesByCategory(player);
			var queued = buildable.Queue
				.Distinct()
				.SelectMany(category => queues[category])
				.Where(q => q.Enabled)
				.Sum(q => q.AllQueued().Count(item => item.Item == type));

			return requested + queued;
		}

		bool CanRequestTransportType(string type, Actor passenger, Actor target, bool landPathAvailable)
		{
			if (!IsConfiguredTransportType(type) ||
				!world.Map.Rules.Actors.TryGetValue(type, out var info))
				return false;

			var cargoInfo = info.TraitInfoOrDefault<CargoInfo>();
			var passengerInfo = passenger.Info.TraitInfoOrDefault<PassengerInfo>();
			var buildable = info.TraitInfoOrDefault<BuildableInfo>();
			if (cargoInfo == null || passengerInfo == null || buildable == null ||
				!cargoInfo.Types.Contains(passengerInfo.CargoType) ||
				cargoInfo.MaxWeight < passengerInfo.Weight)
				return false;

			// APC only makes sense when a land route exists. TRAN is geography-independent.
			// LST production is only requested when both the engineer and target have nearby Beach.
			if (Info.GroundTransportTypes.Contains(type) && !landPathAvailable)
				return false;

			if (Info.LandingCraftTypes.Contains(type) &&
				(!HasNearbyBeach(passenger.Location, Info.LandingCraftPickupSearchRadius) ||
				 !HasNearbyBeach(target.Location, Info.LandingCraftDropSearchRadius)))
				return false;

			var queues = AIUtils.FindQueuesByCategory(player);
			return buildable.Queue
				.Distinct()
				.SelectMany(category => queues[category])
				.Any(q => q.Enabled && q.Actor.IsInWorld && !q.Actor.IsDead &&
					q.BuildableItems().Any(item => item.Name == type));
		}

		bool IsPendingExpansionLandingCraft(Actor transport)
		{
			return transport != null && !transport.Disposed && Info.LandingCraftTypes.Contains(transport.Info.Name) &&
				amphibiousExpansionService?.IsLandingCraftPendingForExpansion(transport) == true;
		}

		IEnumerable<Actor> FindAvailableTransports(string type)
		{
			if (Info.LandingCraftTypes.Contains(type) &&
				amphibiousExpansionService?.HasStrategicLandingCraftProductionDemand == true)
				return Enumerable.Empty<Actor>();

			combatIntelService.EnsureCurrentSnapshot();
			return combatIntelService.OwnedActors
				.Where(a => !a.Disposed && a.IsInWorld && !a.IsDead && a.Info.Name == type)
				.Where(a => !transportReservations.ContainsKey(a))
				.Where(a => !IsPendingExpansionLandingCraft(a))
				.Where(a =>
				{
					var cargo = a.TraitOrDefault<Cargo>();
					return cargo != null && !cargo.IsTraitDisabled && cargo.IsEmpty();
				})
				.OrderBy(a => a.ActorID);
		}

		bool IsCheaplyCompatibleTransport(Actor transport, Actor passenger, Actor target, bool landPathAvailable)
		{
			if (!IsLiveOwnedTransport(transport) || passenger == null || target == null)
				return false;

			var passengerTrait = passenger.TraitOrDefault<Passenger>();
			var cargo = transport.TraitOrDefault<Cargo>();
			if (passengerTrait == null || cargo == null || cargo.IsTraitDisabled ||
				!cargo.Info.Types.Contains(passengerTrait.Info.CargoType) || !cargo.HasSpace(passengerTrait.Info.Weight))
				return false;

			if (Info.GroundTransportTypes.Contains(transport.Info.Name))
				return landPathAvailable;

			if (Info.LandingCraftTypes.Contains(transport.Info.Name))
				return HasNearbyBeach(passenger.Location, Info.LandingCraftPickupSearchRadius) &&
					HasNearbyBeach(target.Location, Info.LandingCraftDropSearchRadius);

			return true;
		}

		bool CachedPlanGeometryStillMatches(CachedTransportPlan cached, Actor passenger, Actor target, Actor transport)
		{
			var toleranceSquared = Info.TransportPlanCacheMovementTolerance * Info.TransportPlanCacheMovementTolerance;
			if ((passenger.Location - cached.PassengerCell).LengthSquared > toleranceSquared ||
				(target.Location - cached.TargetCell).LengthSquared > toleranceSquared)
				return false;

			// a FAILED route proof describes this mission endpoint pair for this
			// physical transport. Letting the idle/borrowed transport wander a few cells must
			// not trigger another 80-90 ms proof. A successful plan still requires the exact
			// transport geometry to remain close enough because its pickup route was accepted.
			return !cached.Success ||
				(transport.Location - cached.TransportCell).LengthSquared <= toleranceSquared;
		}

		bool TryGetCachedOrPlanTransport(TransportMission mission, Actor transport,
			PassengerTargetProofPlanningPass planningPass, out TransportPlan plan)
		{
			plan = default;
			if (mission == null || transport == null || transport.Disposed || !transport.IsInWorld || transport.IsDead)
				return false;

			SharedGroundTransportFailureKey sharedGroundKey = default;
			var hasSharedGroundKey = false;
			if (Info.GroundTransportTypes.Contains(transport.Info.Name) &&
				TryGetGroundTransportTopologyKey(mission.Passenger, mission.Target, transport, out sharedGroundKey, out var groundTopologyImpossible))
			{
				hasSharedGroundKey = true;
				var terrainVersion = strategicMapService.TerrainKnowledgeVersion;
				if (sharedGroundTransportTopologyVersion != terrainVersion)
				{
					sharedGroundTransportTopologyVersion = terrainVersion;
					sharedGroundTransportTopologyFailures.Clear();
					sharedGroundTransportFailures.Clear();
				}

				if (sharedGroundTransportTopologyFailures.Contains(sharedGroundKey))
					return false;

				if (groundTopologyImpossible)
				{
					sharedGroundTransportTopologyFailures.Add(sharedGroundKey);
					FransBotLog.BotDebug(world,
						"{0}: capture ground-transport topology-negative cache latches {1} -> {2} with {3}: transport/source/target ground landmasses {4}/{5}/{6} cannot form one ground corridor. This topology key will not be reconsidered until TerrainKnowledgeVersion changes.",
						player, mission.Passenger, mission.Target, transport.Info.Name, sharedGroundKey.TransportLandmassId, sharedGroundKey.SourceLandmassId, sharedGroundKey.TargetLandmassId);
					return false;
				}

				if (sharedGroundTransportFailures.TryGetValue(sharedGroundKey, out var groundFailure))
				{
					if (SharedGroundFailureGeometryStillMatches(groundFailure, mission.Passenger, mission.Target) &&
						world.WorldTick < groundFailure.RetryAfterTick)
						return false;

					sharedGroundTransportFailures.Remove(sharedGroundKey);
				}
			}

			SharedLandingCraftFailureKey sharedKey = default;
			var hasSharedKey = false;
			if (Info.LandingCraftTypes.Contains(transport.Info.Name) &&
				TryGetLandingCraftTopologyKey(mission.Passenger, mission.Target, transport, out sharedKey, out var topologyImpossible))
			{
				hasSharedKey = true;
				var terrainVersion = strategicMapService.TerrainKnowledgeVersion;
				if (sharedLandingCraftTopologyVersion != terrainVersion)
				{
					sharedLandingCraftTopologyVersion = terrainVersion;
					sharedLandingCraftTopologyFailures.Clear();
					sharedLandingCraftFailureUntil.Clear();
				}

				if (sharedLandingCraftTopologyFailures.Contains(sharedKey))
					return false;

				if (topologyImpossible)
				{
					sharedLandingCraftTopologyFailures.Add(sharedKey);
					FransBotLog.BotDebug(world,
						"{0}: capture LST topology-negative cache latches {1} -> {2} with {3}: source/target shore access cannot share naval region {4}. This exact topology key will not be reconsidered until TerrainKnowledgeVersion changes.",
						player, mission.Passenger, mission.Target, transport.Info.Name, sharedKey.NavalRegionId);
					return false;
				}
				if (sharedLandingCraftFailureUntil.TryGetValue(sharedKey, out var until) && world.WorldTick < until)
					return false;
			}

			if (mission.PlanCache.TryGetValue(transport.ActorID, out var cached) &&
				CachedPlanGeometryStillMatches(cached, mission.Passenger, mission.Target, transport))
			{
				if (cached.Success)
				{
					plan = cached.Plan;
					return true;
				}

				if (world.WorldTick - cached.TestedTick < Info.TransportPlanFailureRetryCooldown)
					return false;
			}

			var success = TryPlanTransport(mission.Passenger, mission.Target, transport, planningPass, out plan);
			mission.PlanCache[transport.ActorID] = new CachedTransportPlan(success, plan,
				mission.Passenger.Location, mission.Target.Location, transport.Location, world.WorldTick);
			if (hasSharedGroundKey)
			{
				if (success)
					sharedGroundTransportFailures.Remove(sharedGroundKey);
				else
					sharedGroundTransportFailures[sharedGroundKey] = new SharedGroundTransportFailureState(
						mission.Passenger.Location, mission.Target.Location, world.WorldTick + Info.TransportPlanFailureRetryCooldown);
			}

			if (hasSharedKey)
			{
				if (success)
					sharedLandingCraftFailureUntil.Remove(sharedKey);
				else
					sharedLandingCraftFailureUntil[sharedKey] = world.WorldTick + Info.TransportPlanFailureRetryCooldown;
			}

			if (sharedLandingCraftFailureUntil.Count > 256)
				foreach (var stale in sharedLandingCraftFailureUntil.Where(kv => kv.Value <= world.WorldTick).Select(kv => kv.Key).Take(128).ToArray())
					sharedLandingCraftFailureUntil.Remove(stale);

			if (sharedGroundTransportFailures.Count > 256)
				foreach (var stale in sharedGroundTransportFailures
					.Where(kv => kv.Value.RetryAfterTick <= world.WorldTick)
					.Select(kv => kv.Key).Take(128).ToArray())
					sharedGroundTransportFailures.Remove(stale);

			if (!success)
			{
				if (hasSharedKey)
				{
					var type = transport.Info.Name;
					mission.FailedLandingCraftPlanProofsByType.TryGetValue(type, out var proofFailures);
					proofFailures++;
					mission.FailedLandingCraftPlanProofsByType[type] = proofFailures;
					if (proofFailures >= Info.LandingCraftFailureProofLimit && mission.FailedTransportTypes.Add(type))
						FransBotLog.BotDebug(world,
							"{0}: capture/SpecOps route {1} -> {2} rejects landing-craft type {3} for this mission after {4} bounded LST route proofs failed. The mission may try another transport type, but it will not manufacture more {3} for the same failed corridor.",
							player, mission.Passenger, mission.Target, type, proofFailures);
				}

				if (hasSharedGroundKey)
					FransBotLog.BotDebug(world,
						"{0}: capture ground-transport cached failed route proof for {1} -> {2} with {3} through WT {4}; equivalent {5} craft on ground landmass {6} share this negative proof while endpoint geometry is unchanged.",
						player, mission.Passenger, mission.Target, transport, world.WorldTick + Info.TransportPlanFailureRetryCooldown, transport.Info.Name, sharedGroundKey.TransportLandmassId);
				else if (hasSharedKey)
					FransBotLog.BotDebug(world,
						"{0}: capture LST cached failed route proof for {1} -> {2} with {3} through WT {4}; equivalent LSTs in the same fair-known source/target landmass + naval region share this negative proof until terrain/topology changes or the bounded cooldown expires.",
						player, mission.Passenger, mission.Target, transport, world.WorldTick + Info.TransportPlanFailureRetryCooldown);
				else
					FransBotLog.BotDebug(world,
						"{0}: capture transport cached failed route proof for {1} -> {2} with {3} through WT {4}; this physical actor is not re-tested until the bounded cooldown expires or mission endpoint geometry changes.",
						player, mission.Passenger, mission.Target, transport, world.WorldTick + Info.TransportPlanFailureRetryCooldown);
			}
			return success;
		}

		bool SharedGroundFailureGeometryStillMatches(SharedGroundTransportFailureState failure, Actor passenger, Actor target)
		{
			if (failure == null || passenger == null || target == null)
				return false;

			var toleranceSquared = Info.TransportPlanCacheMovementTolerance * Info.TransportPlanCacheMovementTolerance;
			return (passenger.Location - failure.PassengerCell).LengthSquared <= toleranceSquared &&
				(target.Location - failure.TargetCell).LengthSquared <= toleranceSquared;
		}

		bool TryGetGroundTransportTopologyKey(Actor passenger, Actor target, Actor transport,
			out SharedGroundTransportFailureKey key, out bool topologyImpossible)
		{
			key = default;
			topologyImpossible = false;
			if (passenger == null || target == null || transport == null ||
				!strategicMapService.TryGetGroundLandmassId(transport.Location, out var transportLandmass) ||
				!strategicMapService.TryGetGroundLandmassId(passenger.Location, out var sourceLandmass) ||
				!strategicMapService.TryGetGroundLandmassId(target.Location, out var targetLandmass))
				return false;

			key = new SharedGroundTransportFailureKey(transport.Info.Name, passenger.ActorID, target.ActorID,
				transportLandmass, sourceLandmass, targetLandmass, strategicMapService.TerrainKnowledgeVersion);
			topologyImpossible = transportLandmass != sourceLandmass || sourceLandmass != targetLandmass;
			return true;
		}

		bool IsGroundTransportProductionSuppressed(string transportType, Actor passenger, Actor target)
		{
			if (passenger == null || target == null || !Info.GroundTransportTypes.Contains(transportType) ||
				!strategicMapService.TryGetGroundLandmassId(passenger.Location, out var sourceLandmass) ||
				!strategicMapService.TryGetGroundLandmassId(target.Location, out var targetLandmass))
				return false;

			var terrainVersion = strategicMapService.TerrainKnowledgeVersion;
			if (sharedGroundTransportTopologyVersion != terrainVersion)
			{
				sharedGroundTransportTopologyVersion = terrainVersion;
				sharedGroundTransportTopologyFailures.Clear();
				sharedGroundTransportFailures.Clear();
			}

			var matchingKeys = sharedGroundTransportFailures.Keys
				.Where(k => k.TransportType == transportType && k.PassengerActorId == passenger.ActorID &&
					k.TargetActorId == target.ActorID && k.TransportLandmassId == sourceLandmass &&
					k.SourceLandmassId == sourceLandmass && k.TargetLandmassId == targetLandmass &&
					k.TerrainKnowledgeVersion == terrainVersion)
				.ToArray();

			foreach (var key in matchingKeys)
			{
				var failure = sharedGroundTransportFailures[key];
				if (SharedGroundFailureGeometryStillMatches(failure, passenger, target) && world.WorldTick < failure.RetryAfterTick)
					return true;

				sharedGroundTransportFailures.Remove(key);
			}

			return false;
		}

		bool TryGetLandingCraftTopologyKey(Actor passenger, Actor target, Actor transport,
			out SharedLandingCraftFailureKey key, out bool topologyImpossible)
		{
			key = default;
			topologyImpossible = false;
			if (passenger == null || target == null || transport == null ||
				!strategicMapService.TryGetGroundLandmassId(passenger.Location, out var sourceLandmass) ||
				!strategicMapService.TryGetGroundLandmassId(target.Location, out var targetLandmass) ||
				!strategicMapService.TryGetNavalRegionId(transport.Location, out var navalRegion))
				return false;

			key = new SharedLandingCraftFailureKey(transport.Info.Name, passenger.ActorID, target.ActorID,
				sourceLandmass, targetLandmass, navalRegion, strategicMapService.TerrainKnowledgeVersion);
			var sourceHasShore = strategicMapService.GetGroundShoreAccess(sourceLandmass).Any(s => s.NavalRegionId == navalRegion);
			var targetHasShore = strategicMapService.GetGroundShoreAccess(targetLandmass).Any(s => s.NavalRegionId == navalRegion);
			topologyImpossible = !sourceHasShore || !targetHasShore;
			return true;
		}

		bool TryPlanTransport(Actor passenger, Actor target, Actor transport,
			PassengerTargetProofPlanningPass planningPass, out TransportPlan plan)
		{
			using var fransPerfBlock = FransBotLog.Profile(world, player, "Transport.TryPlan");
			plan = default;
			if (!IsValidPassenger(passenger) || !IsValidCaptureTarget(target) ||
				!IsLiveOwnedTransport(transport))
				return false;

			var passengerTrait = passenger.TraitOrDefault<Passenger>();
			var passengerMobile = passenger.TraitOrDefault<Mobile>();
			var cargo = transport.TraitOrDefault<Cargo>();
			if (passengerTrait == null || passengerMobile == null || cargo == null ||
				cargo.IsTraitDisabled || !cargo.Info.Types.Contains(passengerTrait.Info.CargoType) ||
				!cargo.HasSpace(passengerTrait.Info.Weight))
				return false;

			if (Info.AirTransportTypes.Contains(transport.Info.Name))
				return TryPlanAirTransport(passenger, passengerMobile, target, transport, planningPass, out plan);

			if (Info.LandingCraftTypes.Contains(transport.Info.Name))
				return TryPlanLandingCraft(passenger, passengerMobile, target, transport, planningPass, out plan);

			if (Info.GroundTransportTypes.Contains(transport.Info.Name))
				return TryPlanGroundTransport(passenger, passengerMobile, target, transport, planningPass, out plan);

			return false;
		}

		bool TryPlanAirTransport(Actor passenger, Mobile passengerMobile, Actor target,
			Actor transport, PassengerTargetProofPlanningPass planningPass, out TransportPlan plan)
		{
			plan = default;
			var aircraft = transport.TraitOrDefault<Aircraft>();
			if (aircraft == null)
				return false;

			// endpoint planning is bounded too. Test at most the same small
			// candidate budget used by strategic detours, rather than combining every
			// pickup/drop cell or running a private A* for each pair.
			var endpointBudget = Math.Max(1, Math.Min(Info.MaximumCellCandidates, Info.AirTransportMaximumDetourCandidates));
			var pickupCandidates = world.Map.FindTilesInAnnulus(
					passenger.Location, 1, Info.GroundPickupSearchRadius)
				.Where(world.Map.Contains)
				.Where(c => aircraft.CanLand(c, blockedByMobile: false))
				.Where(c => !Info.EnableAirTransportRiskRouting ||
					!riskModelService.EvaluateCell(transport, c, FransRiskRole.Aircraft, FransRiskTolerance.Cautious).IsCritical)
				.OrderBy(c => (c - passenger.Location).LengthSquared)
				.Take(endpointBudget)
				.ToArray();

			var dropCandidates = world.Map.FindTilesInAnnulus(
					target.Location, Info.MinimumDropRadius, Info.MaximumDropRadius)
				.Where(world.Map.Contains)
				.Where(c => aircraft.CanLand(c, blockedByMobile: false))
				.Where(c => !Info.EnableAirTransportRiskRouting ||
					!riskModelService.EvaluateCell(transport, c, FransRiskRole.Aircraft, FransRiskTolerance.Cautious).IsCritical)
				.OrderBy(c => (c - target.Location).LengthSquared)
				.Take(endpointBudget)
				.ToArray();
			planningPass.RetainedPickupCount += pickupCandidates.Length;
			planningPass.RetainedDropCount += dropCandidates.Length;

			foreach (var pickup in pickupCandidates)
			{
				var passengerPickup = AdjacentCells(pickup)
					.Where(c => passengerMobile.CanEnterCell(c, check: BlockedByActor.Immovable) &&
						passengerMobile.CanStayInCell(c))
					.OrderBy(c => (c - passenger.Location).LengthSquared)
					.Cast<CPos?>()
					.FirstOrDefault(c => HasPassengerPath(passenger, passengerMobile,
						passengerMobile.ToCell, c.Value));

				if (!passengerPickup.HasValue)
					continue;

				if (Info.EnableAirTransportRiskRouting &&
					!TryPlanBoundedAirCorridor(transport, transport.Location, pickup, out _))
					continue;

				foreach (var drop in dropCandidates)
				{
					if (FindPassengerExitCell(passenger, passengerMobile, drop, target, planningPass) == null)
						continue;

					if (Info.EnableAirTransportRiskRouting &&
						!TryPlanBoundedAirCorridor(transport, pickup, drop, out _))
						continue;

					plan = new TransportPlan(passengerPickup.Value, pickup, drop);
					return true;
				}
			}

			return false;
		}

		bool TryPlanGroundTransport(Actor passenger, Mobile passengerMobile, Actor target,
			Actor transport, PassengerTargetProofPlanningPass planningPass, out TransportPlan plan)
		{
			plan = default;
			var transportMobile = transport.TraitOrDefault<Mobile>();
			if (transportMobile == null || transportMobile.IsTraitDisabled || transportMobile.IsTraitPaused)
				return false;

			// APC capture is a same-landmass optimization. Resolve the target
			// component once from a small deterministic E6 approach set. A proven component
			// mismatch rejects the APC before any A* can run.
			var approachCells = world.Map.FindTilesInAnnulus(target.Location, 1, Info.PassengerTargetApproachRadius)
				.Where(c => world.Map.Contains(c) &&
					passengerMobile.CanEnterCell(c, check: BlockedByActor.Immovable) &&
					passengerMobile.CanStayInCell(c))
				.OrderBy(c => (c - target.Location).LengthSquared)
				.ThenBy(c => c.Y)
				.ThenBy(c => c.X)
				.Take(Info.GroundTransportMaximumApproachCandidates)
				.ToArray();
			if (approachCells.Length == 0)
				return false;

			var passengerLandmassKnown = strategicMapService.TryGetGroundLandmassId(passenger.Location, out var passengerLandmassId);
			var transportLandmassKnown = strategicMapService.TryGetGroundLandmassId(transport.Location, out var transportLandmassId);
			if (passengerLandmassKnown && transportLandmassKnown && passengerLandmassId != transportLandmassId)
				return false;

			int? targetLandmassId = null;
			foreach (var approach in approachCells)
				if (strategicMapService.TryGetGroundLandmassId(approach, out var landmassId) &&
					(!passengerLandmassKnown || landmassId == passengerLandmassId))
				{
					targetLandmassId = landmassId;
					break;
				}

			if (passengerLandmassKnown && !targetLandmassId.HasValue)
				return false;

			var pickupCandidates = world.Map.FindTilesInAnnulus(passenger.Location, 1, Info.GroundPickupSearchRadius)
				.Where(c => world.Map.Contains(c) &&
					transportMobile.CanEnterCell(c, check: BlockedByActor.Immovable) &&
					transportMobile.CanStayInCell(c) &&
					!riskModelService.EvaluateCell(transport, c, FransRiskRole.SupportVehicle, FransRiskTolerance.Cautious).IsCritical)
				.Where(c => !passengerLandmassKnown ||
					(strategicMapService.TryGetGroundLandmassId(c, out var id) && id == passengerLandmassId))
				.OrderBy(c => (c - transport.Location).LengthSquared)
				.ThenBy(c => c.Y)
				.ThenBy(c => c.X)
				.Take(Info.GroundTransportMaximumPickupCandidates)
				.ToArray();

			if (pickupCandidates.Length == 0)
				return false;

			var dropCandidates = world.Map.FindTilesInAnnulus(target.Location, Info.MinimumDropRadius, Info.MaximumDropRadius)
				.Where(c => world.Map.Contains(c) &&
					transportMobile.CanEnterCell(c, check: BlockedByActor.Immovable) &&
					transportMobile.CanStayInCell(c) &&
					!riskModelService.EvaluateCell(transport, c, FransRiskRole.SupportVehicle, FransRiskTolerance.Cautious).IsCritical)
				.Where(c => !targetLandmassId.HasValue ||
					(strategicMapService.TryGetGroundLandmassId(c, out var id) && id == targetLandmassId.Value))
				.OrderBy(c => (c - target.Location).LengthSquared)
				.ThenBy(c => c.Y)
				.ThenBy(c => c.X)
				.Take(Info.GroundTransportMaximumDropCandidates)
				.ToArray();
			planningPass.RetainedPickupCount += pickupCandidates.Length;
			planningPass.RetainedDropCount += dropCandidates.Length;

			if (dropCandidates.Length == 0)
				return false;

			// Find one reachable pickup. Every retained target-side cell belongs to the same
			// StrategicMap component, so target reachability is not recomputed for every
			// pickup x drop pair. Worst case here is four pickup proofs plus four transfer proofs.
			CPos? reachablePickup = null;
			foreach (var pickup in pickupCandidates)
				if (TryFindPath(transport, transportMobile, transportMobile.ToCell, pickup, out _))
				{
					reachablePickup = pickup;
					break;
				}

			if (!reachablePickup.HasValue)
				return false;

			foreach (var drop in dropCandidates)
			{
				if (!TryFindPath(transport, transportMobile, reachablePickup.Value, drop, out _))
					continue;

				if (!FindBoundedGroundPassengerExitCell(passenger, passengerMobile, drop, approachCells,
					targetLandmassId, planningPass).HasValue)
					continue;

				plan = new TransportPlan(passenger.Location, reachablePickup.Value, drop);
				return true;
			}

			return false;
		}

		CPos? FindBoundedGroundPassengerExitCell(Actor passenger, Mobile passengerMobile, CPos transportCell,
			IReadOnlyList<CPos> approachCells, int? targetLandmassId, PassengerTargetProofPlanningPass planningPass)
		{
			var exits = AdjacentCells(transportCell)
				.Where(c => passengerMobile.CanEnterCell(c, check: BlockedByActor.Immovable) &&
					passengerMobile.CanStayInCell(c))
				.OrderBy(c => approachCells.Min(a => (c - a).LengthSquared))
				.ThenBy(c => c.Y)
				.ThenBy(c => c.X)
				.ToArray();

			if (targetLandmassId.HasValue)
				foreach (var exit in exits)
					if (strategicMapService.TryGetGroundLandmassId(exit, out var id) && id == targetLandmassId.Value)
						return exit;

			// Partial terrain-knowledge fallback: at most two target proofs per bounded drop,
			// never once per pickup x drop combination.
			foreach (var exit in exits.Take(2))
			{
				planningPass.ExitSourceCount++;
				if (CanPassengerReachTargetApproach(passenger, passengerMobile, exit, approachCells, planningPass))
					return exit;
			}

			return null;
		}

		bool TryPlanLandingCraft(Actor passenger, Mobile passengerMobile, Actor target,
			Actor transport, PassengerTargetProofPlanningPass planningPass, out TransportPlan plan)
		{
			plan = default;
			var craftMobile = transport.TraitOrDefault<Mobile>();
			if (craftMobile == null || craftMobile.IsTraitDisabled || craftMobile.IsTraitPaused)
				return false;

			var hasTransportRegion = strategicMapService.TryGetNavalRegionId(craftMobile.ToCell, out var transportRegion);
			foreach (var pickupBeach in world.Map.FindTilesInAnnulus(
					passenger.Location, 1, Info.LandingCraftPickupSearchRadius)
				.Where(IsBeach)
				.Where(c => !hasTransportRegion || (strategicMapService.TryGetNavalRegionId(c, out var region) && region == transportRegion))
				.Where(c => craftMobile.CanEnterCell(c, check: BlockedByActor.Immovable) &&
					craftMobile.CanStayInCell(c) &&
					!riskModelService.EvaluateCell(transport, c, FransRiskRole.NavalTransport, FransRiskTolerance.Cautious).IsCritical)
				.OrderBy(c => (c - passenger.Location).LengthSquared)
				.Take(Info.LandingCraftMaximumPickupCandidates))
			{
				planningPass.RetainedPickupCount++;
				if (!TryFindPath(transport, craftMobile, craftMobile.ToCell, pickupBeach, out _))
					continue;

				CPos? passengerPickup = AdjacentCells(pickupBeach)
					.Where(c => passengerMobile.CanEnterCell(c, check: BlockedByActor.Immovable) &&
						passengerMobile.CanStayInCell(c))
					.OrderBy(c => (c - passenger.Location).LengthSquared)
					.Cast<CPos?>()
					.FirstOrDefault(c => HasPassengerPath(passenger, passengerMobile, passengerMobile.ToCell, c.Value));

				if (!passengerPickup.HasValue)
					continue;

				foreach (var dropBeach in world.Map.FindTilesInAnnulus(
						target.Location, 1, Info.LandingCraftDropSearchRadius)
					.Where(IsBeach)
					.Where(c => !hasTransportRegion || (strategicMapService.TryGetNavalRegionId(c, out var region) && region == transportRegion))
					.Where(c => craftMobile.CanEnterCell(c, check: BlockedByActor.Immovable) &&
						craftMobile.CanStayInCell(c) &&
						!riskModelService.EvaluateCell(transport, c, FransRiskRole.NavalTransport, FransRiskTolerance.Cautious).IsCritical)
					.OrderBy(c => (c - target.Location).LengthSquared)
					.Take(Info.LandingCraftMaximumDropCandidates))
				{
					planningPass.RetainedDropCount++;
					if (!TryFindPath(transport, craftMobile, pickupBeach, dropBeach, out _))
						continue;

					if (FindPassengerExitCell(passenger, passengerMobile, dropBeach, target, planningPass) == null)
						continue;

					plan = new TransportPlan(passengerPickup.Value, pickupBeach, dropBeach);
					return true;
				}
			}

			return false;
		}

		CPos? FindPassengerExitCell(Actor passenger, Mobile passengerMobile, CPos transportCell, Actor target,
			PassengerTargetProofPlanningPass planningPass)
		{
			foreach (var exit in AdjacentCells(transportCell)
				.Where(c => passengerMobile.CanEnterCell(c, check: BlockedByActor.Immovable) &&
					passengerMobile.CanStayInCell(c))
				.OrderBy(c => (c - target.Location).LengthSquared))
			{
				planningPass.ExitSourceCount++;
				if (CanPassengerReachTargetApproach(passenger, passengerMobile, exit, target, planningPass))
					return exit;
			}

			return null;
		}

		bool CanPassengerReachTargetApproach(Actor passenger, Mobile mobile, CPos source, Actor target,
			PassengerTargetProofPlanningPass planningPass)
		{
			var approachCells = world.Map.FindTilesInAnnulus(target.Location, 1, Info.PassengerTargetApproachRadius)
				.Where(c => world.Map.Contains(c) &&
					mobile.CanEnterCell(c, check: BlockedByActor.Immovable) &&
					mobile.CanStayInCell(c))
				.Take(Info.MaximumCellCandidates)
				.ToArray();

			return CanPassengerReachTargetApproach(passenger, mobile, source, approachCells, planningPass);
		}

		bool CanPassengerReachTargetApproach(Actor passenger, Mobile mobile, CPos source,
			IReadOnlyList<CPos> approachCells, PassengerTargetProofPlanningPass planningPass)
		{
			using var fransPerfBlock = FransBotLog.Profile(world, player, "Transport.PassengerTargetProof");
			if (approachCells == null || approachCells.Count == 0 || mobile.PathFinder is not PathFinder pathFinder)
				return false;

			planningPass.TargetApproachCount = Math.Max(planningPass.TargetApproachCount, approachCells.Count);
			planningPass.LogicalRequests++;
			var key = new PassengerTargetProofKey(passenger.ActorID, source, approachCells);
			if (planningPass.TryGet(key, out var cached))
			{
				planningPass.RecordLogicalResult(cached);
				return cached;
			}

			planningPass.PhysicalPathSearches++;
			IReadOnlyList<CPos> path;
			using (FransBotLog.Profile(world, player, "Transport.PassengerTargetPathSearch"))
				path = riskModelService.ExecuteWithPreparedPathCost(passenger,
					FransRiskRole.Capturer, FransRiskTolerance.Cautious, preparedPathCost =>
					{
						int CountedPathCost(CPos cell)
						{
							planningPass.NativePathCostCallbackCalls++;
							return preparedPathCost(cell);
						}

						return pathFinder.FindPathToTargetCells(passenger, source, approachCells,
							BlockedByActor.Immovable, CountedPathCost, laneBias: false);
					});

			var result = approachCells.Contains(source) || (path != null && path.Count > 0);
			planningPass.Store(key, result);
			planningPass.RecordLogicalResult(result);
			return result;
		}

		bool HasPassengerPath(Actor passenger, Mobile mobile, CPos source, CPos destination)
		{
			if (source == destination)
				return true;

			if (mobile.PathFinder is not PathFinder pathFinder)
				return false;

			int CustomCost(CPos cell) => riskModelService.GetPathCost(passenger, cell, FransRiskRole.Capturer, FransRiskTolerance.Cautious);
			var path = pathFinder.FindPathToTargetCell(passenger, [source], destination,
				BlockedByActor.Immovable, CustomCost, laneBias: false);
			return path != null && path.Count > 0;
		}

		FransRiskRole TransportRiskRole(Actor actor)
		{
			if (actor != null && Info.AirTransportTypes.Contains(actor.Info.Name))
				return FransRiskRole.Aircraft;
			if (actor != null && Info.LandingCraftTypes.Contains(actor.Info.Name))
				return FransRiskRole.NavalTransport;
			return FransRiskRole.SupportVehicle;
		}

		bool IsLandingCraftRouteLossSafe(Actor actor, Mobile mobile, CPos source, CPos destination)
		{
			if (actor == null || mobile == null || mobile.PathFinder is not PathFinder pathFinder)
				return false;

			int NoExtraCost(CPos cell) => 0;
			var path = pathFinder.FindPathToTargetCell(actor, [source], destination,
				BlockedByActor.Immovable, NoExtraCost, laneBias: false);
			return path != null && path.Count > 0 && generalService.IsTransportLossRouteAllowed(path);
		}

		bool TryFindPath(Actor actor, Mobile mobile, CPos source, CPos destination, out int length)
		{
			using var fransPerfBlock = FransBotLog.Profile(world, player, "Transport.Path");
			length = int.MaxValue;
			if (source == destination)
			{
				length = 0;
				return true;
			}

			if (mobile.PathFinder is not PathFinder pathFinder)
				return false;

			var role = TransportRiskRole(actor);
			int CustomCost(CPos cell) => riskModelService.GetPathCost(actor, cell, role, FransRiskTolerance.Cautious);
			var path = pathFinder.FindPathToTargetCell(actor, [source], destination,
				BlockedByActor.Immovable, CustomCost, laneBias: false);
			if (path == null || path.Count == 0)
				return false;

			if (Info.LandingCraftTypes.Contains(actor.Info.Name) && !generalService.IsTransportLossRouteAllowed(path))
				return false;

			var routeRisk = riskModelService.EvaluateRoute(actor, path, role, FransRiskTolerance.Cautious);
			if (routeRisk.IsCritical)
				return false;

			length = path.Count;
			return true;
		}

		IEnumerable<CPos> AdjacentCells(CPos cell)
		{
			return Util.AdjacentCells(world, Target.FromCell(world, cell))
				.Where(c => c != cell && world.Map.Contains(c));
		}

		bool IsBeach(CPos cell)
		{
			return world.Map.Contains(cell) && world.Map.GetTerrainInfo(cell).Type == "Beach";
		}

		bool HasNearbyBeach(CPos cell, int radius)
		{
			return world.Map.FindTilesInAnnulus(cell, 1, radius).Any(IsBeach);
		}

		bool IsAirTransport(Actor transport)
		{
			return transport != null && Info.AirTransportTypes.Contains(transport.Info.Name);
		}

		bool StartAirMove(IBot bot, TransportMission mission, CPos destination, string phase)
		{
			var transport = mission.Transport;
			if (!IsAirTransport(transport) || !Info.EnableAirTransportRiskRouting)
			{
				QueueTransportMove(bot, transport, destination);
				return true;
			}

			if (!TryPlanBoundedAirCorridor(transport, transport.Location, destination, out var waypoints))
				return false;

			mission.AirWaypoints = waypoints;
			mission.AirWaypointIndex = 0;
			mission.AirDestination = destination;
			mission.NextAirRiskCheckTick = world.WorldTick + Info.AirTransportStrategicRiskRecheckInterval;
			mission.LastAirRiskRevision = riskModelService.RiskRevision;
			mission.LastTransportProgressCell = transport.Location;
			mission.LastTransportProgressTick = world.WorldTick;
			IssueAirMoveLeg(bot, mission);

			if (waypoints.Count > 1)
				FransBotLog.BotDebug(world,
					"{0}: capture TRAN {1} selects one bounded RiskModel detour for {2} toward {3}; native aircraft movement owns the actual flight path.",
					player, transport, phase, destination);

			return true;
		}

		bool ManageAirMove(IBot bot, TransportMission mission, CPos destination, string phase, bool loaded)
		{
			var transport = mission.Transport;
			if (!IsAirTransport(transport) || !Info.EnableAirTransportRiskRouting)
				return true;

			if (loaded && riskModelService.EvaluateImmediateRisk(transport, transport.Location,
				FransRiskRole.Aircraft, FransRiskTolerance.Cautious).IsCritical)
				return false;

			if (mission.AirWaypoints.Count == 0 || mission.AirDestination != destination)
				return StartAirMove(bot, mission, destination, phase);

			AdvanceAirWaypointIfReached(bot, mission);
			TransportMadeProgress(mission);

			if (world.WorldTick >= mission.NextAirRiskCheckTick)
			{
				mission.NextAirRiskCheckTick = world.WorldTick + Info.AirTransportStrategicRiskRecheckInterval;
				if (riskModelService.RiskRevision != mission.LastAirRiskRevision)
				{
					mission.LastAirRiskRevision = riskModelService.RiskRevision;
					if (RemainingAirCorridorIsCritical(transport, mission))
					{
						if (!TryPlanBoundedAirCorridor(transport, transport.Location, destination, out var replanned))
							return false;

						mission.AirWaypoints = replanned;
						mission.AirWaypointIndex = 0;
						mission.AirDestination = destination;
						mission.LastTransportProgressCell = transport.Location;
						mission.LastTransportProgressTick = world.WorldTick;
						IssueAirMoveLeg(bot, mission);
						FransBotLog.BotDebug(world,
							"{0}: capture TRAN {1} found newly CRITICAL shared risk on its remaining {2} corridor; one bounded strategic replan replaces the current flight order.",
							player, transport, phase);
					}
				}
			}

			if (mission.AirWaypointIndex >= mission.AirWaypoints.Count)
				return true;

			if (IsTransportStalled(mission))
			{
				IssueAirMoveLeg(bot, mission);
				mission.LastTransportProgressCell = transport.Location;
				mission.LastTransportProgressTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					"{0}: capture TRAN {1} stalled for {2} WT during {3}; reissuing only the current native movement leg without a new route search.",
					player, transport, Info.TransportStallReplanTicks, phase);
			}

			return true;
		}

		void AdvanceAirWaypointIfReached(IBot bot, TransportMission mission)
		{
			var transport = mission.Transport;
			if (transport == null || transport.Disposed || !transport.IsInWorld || transport.IsDead ||
				mission.AirWaypointIndex >= mission.AirWaypoints.Count)
				return;

			var target = mission.AirWaypoints[mission.AirWaypointIndex];
			var finalLeg = mission.AirWaypointIndex == mission.AirWaypoints.Count - 1;
			var radius = finalLeg ? Info.DropArrivalRadius : 2;
			if ((transport.Location - target).LengthSquared > radius * radius || (finalLeg && !transport.IsIdle))
				return;

			mission.AirWaypointIndex++;
			if (mission.AirWaypointIndex < mission.AirWaypoints.Count)
				IssueAirMoveLeg(bot, mission);
		}

		void IssueAirMoveLeg(IBot bot, TransportMission mission)
		{
			var transport = mission.Transport;
			if (transport == null || transport.Disposed || !transport.IsInWorld || transport.IsDead ||
				mission.AirWaypointIndex >= mission.AirWaypoints.Count)
				return;

			var destination = mission.AirWaypoints[mission.AirWaypointIndex];
			var finalLeg = mission.AirWaypointIndex == mission.AirWaypoints.Count - 1;
			bot.QueueOrder(new Order(finalLeg ? "Land" : "Move", transport, Target.FromCell(world, destination), false));
		}

		bool RemainingAirCorridorIsCritical(Actor transport, TransportMission mission)
		{
			if (mission.AirWaypointIndex >= mission.AirWaypoints.Count)
				return false;

			var from = transport.Location;
			for (var i = mission.AirWaypointIndex; i < mission.AirWaypoints.Count; i++)
			{
				var to = mission.AirWaypoints[i];
				if (riskModelService.EvaluateDirectRoute(transport, from, to,
					FransRiskRole.Aircraft, FransRiskTolerance.Cautious).IsCritical)
					return true;
				from = to;
			}

			return false;
		}

		bool TryPlanBoundedAirCorridor(Actor transport, CPos from, CPos to, out List<CPos> waypoints)
		{
			waypoints = [];
			if (!world.Map.Contains(from) || !world.Map.Contains(to))
				return false;

			if (!Info.EnableAirTransportRiskRouting || !IsAirTransport(transport))
			{
				waypoints.Add(to);
				return true;
			}

			// Performance-only memoization. RiskModel air-route evaluation is keyed by actor type,
			// and during one WorldTick the same transport type + endpoints + RiskRevision describes
			// the exact same bounded corridor proof. Never reuse this across ticks or risk revisions.
			if (airCorridorTickCacheWorldTick != world.WorldTick)
			{
				airCorridorTickCache.Clear();
				airCorridorTickCacheWorldTick = world.WorldTick;
			}

			var riskRevision = riskModelService.RiskRevision;
			var cacheKey = new AirCorridorTickCacheKey(transport.Info.Name, from, to, riskRevision);
			if (airCorridorTickCache.TryGetValue(cacheKey, out var cached))
			{
				waypoints.AddRange(cached.Waypoints);
				return cached.Success;
			}

			if (riskModelService.EvaluateCell(transport, to, FransRiskRole.Aircraft, FransRiskTolerance.Cautious).IsCritical)
			{
				airCorridorTickCache[cacheKey] = new AirCorridorTickCacheValue(false, waypoints);
				return false;
			}

			var direct = riskModelService.EvaluateDirectRoute(transport, from, to,
				FransRiskRole.Aircraft, FransRiskTolerance.Cautious);
			if (!direct.IsCritical)
			{
				waypoints.Add(to);
				airCorridorTickCache[cacheKey] = new AirCorridorTickCacheValue(true, waypoints);
				return true;
			}

			CPos? best = null;
			long bestScore = long.MaxValue;
			foreach (var candidate in BoundedAirDetourCandidates(from, to))
			{
				var cellRisk = riskModelService.EvaluateCell(transport, candidate,
					FransRiskRole.Aircraft, FransRiskTolerance.Cautious);
				if (cellRisk.IsCritical)
					continue;

				var first = riskModelService.EvaluateDirectRoute(transport, from, candidate,
					FransRiskRole.Aircraft, FransRiskTolerance.Cautious);
				if (first.IsCritical)
					continue;

				var second = riskModelService.EvaluateDirectRoute(transport, candidate, to,
					FransRiskRole.Aircraft, FransRiskTolerance.Cautious);
				if (second.IsCritical)
					continue;

				var detour = (candidate - from).LengthSquared + (to - candidate).LengthSquared;
				var score = (long)Math.Max(first.PeakScore, second.PeakScore) * 100000L +
					first.TotalScore + second.TotalScore + detour;
				if (score >= bestScore)
					continue;

				bestScore = score;
				best = candidate;
			}

			if (!best.HasValue)
			{
				airCorridorTickCache[cacheKey] = new AirCorridorTickCacheValue(false, waypoints);
				return false;
			}

			waypoints.Add(best.Value);
			waypoints.Add(to);
			airCorridorTickCache[cacheKey] = new AirCorridorTickCacheValue(true, waypoints);
			return true;
		}

		IEnumerable<CPos> BoundedAirDetourCandidates(CPos from, CPos to)
		{
			var midpoint = new CPos((from.X + to.X) / 2, (from.Y + to.Y) / 2);
			var distance = Math.Max(Math.Abs(to.X - from.X), Math.Abs(to.Y - from.Y));
			var outer = Math.Max(4, Math.Min(Info.AirTransportDetourRadius, Math.Max(4, distance / 3)));
			var inner = Math.Max(3, outer / 2);
			var seen = new HashSet<CPos>();
			var yielded = 0;

			foreach (var radius in new[] { inner, outer })
			{
				var offsets = new[]
				{
					new CPos(radius, 0), new CPos(-radius, 0), new CPos(0, radius), new CPos(0, -radius),
					new CPos(radius, radius), new CPos(radius, -radius), new CPos(-radius, radius), new CPos(-radius, -radius)
				};

				foreach (var offset in offsets)
				{
					var candidate = new CPos(midpoint.X + offset.X, midpoint.Y + offset.Y);
					if (candidate == from || candidate == to || !world.Map.Contains(candidate) || !seen.Add(candidate))
						continue;
					yield return candidate;
					if (++yielded >= Info.AirTransportMaximumDetourCandidates)
						yield break;
				}
			}
		}

		void BeginRetreat(IBot bot, TransportMission mission, string reason)
		{
			var transport = mission.Transport;
			if (!ValidateAssignedTransport(mission) || !IsPassengerLoaded(mission))
			{
				ReleaseTransport(mission);
				missions.Remove(mission.Passenger);
				return;
			}

			mission.State = MissionState.Retreat;
			mission.StartedTick = world.WorldTick;
			mission.CancelAfterDrop = true;
			mission.AirWaypoints.Clear();
			mission.AirWaypointIndex = 0;
			mission.RetreatDropCell = null;
			mission.UnloadStopOrderTransport = null;
			mission.NextRetreatPlanTick = world.WorldTick + Info.RetreatReplanInterval;
			mission.LastTransportProgressCell = transport.Location;
			mission.LastTransportProgressTick = world.WorldTick;

			var cargo = transport.TraitOrDefault<Cargo>();
			if (cargo != null && cargo.CanUnload())
			{
				FransBotLog.BotDebug(world,
					"{0}: capture transport {1} MOVE -> RETREAT for loaded {2}: {3}; current cell {4} permits native unload, so synchronized Stop -> idle -> DROP preparation begins immediately.",
					player, transport, mission.Passenger, reason, transport.Location);
				BeginDrop(bot, mission);
				return;
			}

			if (TryFindRetreatDrop(mission, requireNonCritical: true, out var safeDrop) ||
				TryFindRetreatDrop(mission, requireNonCritical: false, out safeDrop))
			{
				mission.DropTransportCell = safeDrop;
				mission.RetreatDropCell = safeDrop;
				FransBotLog.BotDebug(world,
					"{0}: capture transport {1} MOVE -> RETREAT for loaded {2}: {3}; one plain native escape move is issued toward unload cell {4}. RiskModel selects the destination but never vetoes the escape route.",
					player, transport, mission.Passenger, reason, safeDrop);
				QueuePlainRetreatMove(bot, transport, safeDrop);
				return;
			}

			FransBotLog.BotDebug(world,
				"{0}: capture transport {1} enters RETREAT for loaded {2}: {3}; no legal unload cell is currently available, so it holds and retries only after the bounded RETREAT interval.",
				player, transport, mission.Passenger, reason);
			transport.CancelActivity();
		}

		void ManageRetreat(IBot bot, TransportMission mission)
		{
			if (!ValidateAssignedTransport(mission))
			{
				ReleaseTransport(mission);
				missions.Remove(mission.Passenger);
				return;
			}

			if (!IsPassengerLoaded(mission))
			{
				if (mission.Passenger.IsInWorld)
					CompleteUnload(mission);
				return;
			}

			var transport = mission.Transport;
			var cargo = transport.TraitOrDefault<Cargo>();
			if (transport.IsIdle && cargo != null && cargo.CanUnload())
			{
				BeginDrop(bot, mission);
				return;
			}

			var stalled = IsTransportStalled(mission);
			if (!stalled || world.WorldTick < mission.NextRetreatPlanTick)
				return;

			mission.NextRetreatPlanTick = world.WorldTick + Info.RetreatReplanInterval;
			if (TryFindRetreatDrop(mission, requireNonCritical: true, out var safeDrop) ||
				TryFindRetreatDrop(mission, requireNonCritical: false, out safeDrop))
			{
				mission.DropTransportCell = safeDrop;
				mission.RetreatDropCell = safeDrop;
				QueuePlainRetreatMove(bot, transport, safeDrop);
				mission.LastTransportProgressCell = transport.Location;
				mission.LastTransportProgressTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					"{0}: capture transport {1} RETREAT stalled; one fresh plain escape move is issued toward unload cell {2}. No full-map route search is performed.",
					player, transport, safeDrop);
			}
		}

		void ManageRetreatTimeout(IBot bot, TransportMission mission)
		{
			var transport = mission.Transport;
			if (transport == null || transport.Disposed || !transport.IsInWorld || transport.IsDead)
			{
				ReleaseTransport(mission);
				missions.Remove(mission.Passenger);
				return;
			}

			var cargo = transport.TraitOrDefault<Cargo>();
			if (cargo == null)
			{
				ReleaseTransport(mission);
				missions.Remove(mission.Passenger);
				return;
			}

			if (cargo.CanUnload())
			{
				FransBotLog.BotDebug(world,
					"{0}: capture transport RETREAT watchdog begins synchronized Stop -> idle -> native unload preparation at {1} for {2}.",
					player, transport.Location, mission.Passenger);
				BeginDrop(bot, mission);
				return;
			}

			mission.StartedTick = world.WorldTick;
			mission.NextRetreatPlanTick = world.WorldTick + Info.RetreatReplanInterval;
			if (TryFindRetreatDrop(mission, requireNonCritical: false, out var fallback))
			{
				mission.DropTransportCell = fallback;
				mission.RetreatDropCell = fallback;
				mission.UnloadStopOrderTransport = null;
				QueuePlainRetreatMove(bot, transport, fallback);
				mission.LastTransportProgressCell = transport.Location;
				mission.LastTransportProgressTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					"{0}: capture transport RETREAT watchdog chooses nearest reachable legal unload fallback {1} for {2}; escape routing remains plain/native.",
					player, fallback, mission.Passenger);
			}
			else
				transport.CancelActivity();
		}

		bool TryFindRetreatDrop(TransportMission mission, bool requireNonCritical, out CPos drop)
		{
			drop = default;
			var transport = mission.Transport;
			var passenger = mission.Passenger;
			if (transport == null || passenger == null || transport.Disposed || passenger.Disposed || !transport.IsInWorld || transport.IsDead || passenger.IsDead)
				return false;

			var passengerMobile = passenger.TraitOrDefault<Mobile>();
			if (passengerMobile == null)
				return false;

			if (IsAirTransport(transport))
			{
				var aircraft = transport.TraitOrDefault<Aircraft>();
				if (aircraft == null)
					return false;

				var candidates = world.Map.FindTilesInAnnulus(transport.Location, 1, Info.RetreatSearchRadius)
					.Where(world.Map.Contains)
					.Where(c => aircraft.CanLand(c, blockedByMobile: false) && HasAnyPassengerExitCell(passengerMobile, c))
					.OrderBy(c => (c - transport.Location).LengthSquared)
					.Take(Info.MaximumCellCandidates * 2)
					.Select(c => (Cell: c, Risk: riskModelService.EvaluateCell(transport, c,
						FransRiskRole.Aircraft, FransRiskTolerance.Balanced)))
					.Where(x => !requireNonCritical || !x.Risk.IsCritical)
					.OrderBy(x => x.Risk.Score)
					.ThenBy(x => (x.Cell - transport.Location).LengthSquared);

				foreach (var candidate in candidates)
				{
					drop = candidate.Cell;
					return true;
				}

				return false;
			}

			var mobile = transport.TraitOrDefault<Mobile>();
			if (mobile == null || mobile.IsTraitDisabled || mobile.IsTraitPaused || mobile.PathFinder is not PathFinder pathFinder)
				return false;

			var role = Info.LandingCraftTypes.Contains(transport.Info.Name) ? FransRiskRole.NavalTransport : FransRiskRole.SupportVehicle;
			foreach (var candidate in world.Map.FindTilesInAnnulus(transport.Location, 1, Info.RetreatSearchRadius)
				.Where(world.Map.Contains)
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.Where(c => HasAnyPassengerExitCell(passengerMobile, c))
				.OrderBy(c => (c - transport.Location).LengthSquared)
				.Take(Info.MaximumCellCandidates * 2))
			{
				var risk = riskModelService.EvaluateCell(transport, candidate, role, FransRiskTolerance.Balanced);
				if (requireNonCritical && risk.IsCritical)
					continue;
				var path = pathFinder.FindPathToTargetCell(transport, [mobile.ToCell], candidate,
					BlockedByActor.Immovable, laneBias: false);
				if (path == null || path.Count == 0)
					continue;
				drop = candidate;
				return true;
			}

			return false;
		}

		bool HasAnyPassengerExitCell(Mobile passengerMobile, CPos transportCell)
		{
			return AdjacentCells(transportCell).Any(c =>
				world.Map.Contains(c) && passengerMobile.CanEnterCell(c, check: BlockedByActor.Immovable) && passengerMobile.CanStayInCell(c));
		}

		void ReleaseTransport(TransportMission mission)
		{
			if (mission?.Transport == null)
				return;

			RestoreCaptureEscortStance(mission);
			ReleaseTransportReservation(mission.Transport, mission.Passenger);
		}

		void FailAssignedTransport(TransportMission mission)
		{
			if (mission.Transport != null)
			{
				if (!mission.Transport.Disposed)
					mission.FailedTransportTypes.Add(mission.Transport.Info.Name);
				ReleaseTransport(mission);
			}

			mission.Transport = null;
			mission.AirWaypoints.Clear();
			mission.AirWaypointIndex = 0;
			mission.CancelAfterDrop = false;
			mission.BoardingOrderIssued = false;
			mission.RetreatDropCell = null;
			mission.State = MissionState.Waiting;
			mission.StartedTick = world.WorldTick;
		}

		bool ValidateAssignedTransport(TransportMission mission)
		{
			return mission.Transport != null &&
				IsLiveOwnedTransport(mission.Transport) &&
				transportReservations.TryGetValue(mission.Transport, out var owner) &&
				owner == mission.Passenger;
		}

		bool IsConfiguredTransportType(string type)
		{
			return Info.AirTransportTypes.Contains(type) ||
				Info.GroundTransportTypes.Contains(type) ||
				Info.LandingCraftTypes.Contains(type);
		}

		bool IsLiveOwnedTransport(Actor actor)
		{
			return actor != null && !actor.Disposed && actor.IsInWorld && !actor.IsDead && actor.Owner == player &&
				IsConfiguredTransportType(actor.Info.Name);
		}

		bool IsValidPassenger(Actor actor)
		{
			return actor != null && !actor.Disposed && !actor.IsDead && actor.Owner == player &&
				Info.PassengerTypes.Contains(actor.Info.Name) &&
				(actor.IsInWorld || actor.TraitOrDefault<Passenger>()?.Transport != null);
		}

		bool IsValidCaptureTarget(Actor actor)
		{
			if (actor == null || actor.Disposed || !actor.IsInWorld || actor.IsDead)
				return false;

			var relationship = player.RelationshipWith(actor.Owner);
			return PlayerRelationship.Enemy.HasRelationship(relationship) ||
				PlayerRelationship.Neutral.HasRelationship(relationship);
		}
	}
}
