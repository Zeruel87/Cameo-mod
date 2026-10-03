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
using OpenRA.Mods.Common.Pathfinder;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	/// <summary>
	/// Read-only reservation surface. Ground Commander uses this to leave transfer-owned units alone
	/// until the landing wave has regrouped and ordinary Ground mission ownership can resume.
	/// </summary>
	public interface IFransGroundTransferService
	{
		bool IsGroundUnitTransferReserved(Actor actor);
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Ground logistics convoy service. Moves ordinary Ground combat units between fair-known static land masses in concentrated demand-sized LST waves. GroundTransfer owns Ground passengers and LST logistics only; Sea combat ships remain under Sea Commander and may independently answer a Sea-only SECURE around the destination landing shore. It creates no new Ground strategic MISSION.")]
	public class FransGroundTransferBotModuleInfo : ConditionalTraitInfo, Requires<PlayerResourcesInfo>
	{
		[Desc("World ticks between state-machine updates.")]
		public readonly int ScanInterval = 25;

		[Desc("World ticks between attempts to create a new transfer convoy while idle.")]
		public readonly int PlanningInterval = 250;

		[ActorReference]
		[Desc("Landing craft types usable for ordinary Ground transfer waves.")]
		public readonly FrozenSet<string> LandingCraftTypes = FrozenSet<string>.Empty;

		[Desc("Production queue category used by landing craft.")]
		public readonly string LandingCraftQueueCategory = "Ship";

		[Desc("Minimum cash/resources before GroundTransfer asks UnitBuilder for additional landing craft.")]
		public readonly int MinimumCashForLandingCraftRequest = 1200;

		[Desc("World ticks between repeated GroundTransfer landing-craft production requests.")]
		public readonly int LandingCraftProductionRequestCooldown = 250;


		[Desc("Maximum landing craft participating in one concentrated transfer convoy.")]
		public readonly int MaximumConvoyLandingCraft = 3;

		[Desc("Approximate compatible units per landing craft used only to size the desired convoy. CargoInfo remains authoritative for actual loading.")]
		public readonly int DesiredUnitsPerLandingCraft = 5;

		[Desc("Maximum radius used to assign distinct LST water staging cells around embark and landing shorelines.")]
		public readonly int NavalFormationRadius = 4;

		[Desc("Lease duration in world ticks refreshed while a GroundTransfer wave is active for the independent Sea-only SECURE around the destination landing shore.")]
		public readonly int SeaSecureLeaseTicks = 500;

		[ActorReference]
		[Desc("Owned structures that mark a land mass as an established base. Such a source keeps SourceBaseReserveUnits behind.")]
		public readonly FrozenSet<string> SourceBaseAnchorTypes = FrozenSet<string>.Empty;

		[Desc("Minimum ordinary Ground units for an emergency DEFEND ferry. If fewer transferable units exist, all available units may still evacuate/respond.")]
		public readonly int MinimumDefendWaveUnits = 2;

		[Desc("Minimum ordinary Ground units for a SECURE/Forward-Anchor convoy. If fewer transferable units exist on the whole safe source landmass, all of them may still move.")]
		public readonly int MinimumStrategicWaveUnits = 6;

		[Desc("Ground units deliberately left behind on a source land mass that contains an established base anchor.")]
		public readonly int SourceBaseReserveUnits = 4;

		[Desc("Minimum friendly Ground purchase-value desired on a DEFEND/SECURE destination even when raw SiteIntel is smaller.")]
		public readonly int MinimumMissionGroundValue = 2000;

		[Desc("SECURE destination force target as percentage of raw observed tactical SiteIntel value. 500 preserves Ground Commander's 5x doctrine.")]
		public readonly int SecureForceMultiplierPercent = 500;

		[Desc("DEFEND destination force target as percentage of raw observed tactical SiteIntel value.")]
		public readonly int DefendForceMultiplierPercent = 200;

		[Desc("Minimum total friendly Ground purchase-value desired on a remote SECURE landmass before follow-on reinforcement stops. This prevents a token first landing from making a still-active foreign front look complete.")]
		public readonly int RemoteSecureDesiredGroundValue = 6000;

		[Desc("Follow-on SECURE reinforcement target as percentage of the normal 5x SECURE requirement.")]
		public readonly int SecureFollowOnReinforcementPercent = 150;

		[Desc("Diagnostic/minimum Ground purchase-value for Forward Anchor redeployment. Safe surplus on obsolete remote land masses keeps returning toward the current Forward Anchor even after this floor is met.")]
		public readonly int ForwardAnchorDesiredGroundValue = 6000;

		[Desc("Maximum cells from a unit's assigned embark slot considered assembled for initial convoy staging diagnostics.")]
		public readonly int BoardingAssemblyRadius = 3;

		[Desc("Broad ground-side embark zone around the selected amphibious handoff. Units inside this zone may receive native EnterTransport directly without waiting on an exact staging slot.")]
		public readonly int BoardingZoneRadius = 8;

		[Desc("Maximum cells an LST may be from its assigned source naval slot and still count as ready for streaming boarding. One ready LST is enough to start loading; later LSTs join as they arrive.")]
		public readonly int LandingCraftBoardingReadyRadius = 4;

		[Desc("Maximum radius used to assign distinct Ground staging/regroup cells around a shoreline handoff.")]
		public readonly int StagingSlotRadius = 4;

		[Desc("Target-side regroup radius before Ground Commander ownership is restored.")]
		public readonly int RegroupRadius = 8;

		[Desc("Percentage of surviving wave units that must reach target regroup before handoff.")]
		public readonly int RegroupRequiredPercent = 75;

		[Desc("World ticks with no physical progress before a crossing/return movement leg is treated as stalled.")]
		public readonly int StallTimeout = 250;

		[Desc("Same cached crossing-leg retries before a bounded local alternate landing cell is tried around the already selected handoff.")]
		public readonly int CrossingSameLegRetries = 2;

		[Desc("Maximum bounded local alternate naval cells tried before the convoy retreats to its embark shore instead of remaining stalled.")]
		public readonly int MaximumCrossingRecoveryAttempts = 3;

		[Desc("Radius around the already selected source/target naval cell used for bounded crossing/return recovery. Never triggers a full shoreline replan.")]
		public readonly int CrossingRecoveryRadius = 6;

		[Desc("Maximum local naval cells considered by one bounded crossing/return recovery scan.")]
		public readonly int CrossingRecoveryCandidateLimit = 6;

		[Desc("Maximum pre-boarding stall retries before a wave is abandoned or launches only the passengers that successfully boarded.")]
		public readonly int MaximumPreBoardingStallRetries = 3;

		[Desc("World ticks between scans for a newly free LST boarding slot. This no longer cancels an already-issued native EnterTransport order.")]
		public readonly int BoardingRetryInterval = 75;

		[Desc("Maximum world ticks one native EnterTransport attempt may make no physical cell progress before that one passenger is cancelled and returned to the dynamic boarding queue. Progress extends native ownership; this is not a blind order timeout.")]
		public readonly int BoardingNativeTimeout = 250;

		[Desc("Hard boarding deadline for ordinary SECURE/Forward-Anchor convoys. At the deadline a sufficiently loaded convoy departs and stragglers are released instead of waiting indefinitely.")]
		public readonly int StrategicBoardingDeadline = 1250;

		[Desc("Hard boarding deadline for emergency DEFEND ferries.")]
		public readonly int DefendBoardingDeadline = 750;

		[Desc("Minimum percentage of surviving planned passengers that must be loaded when a strategic boarding deadline expires before the convoy is allowed to depart without stragglers.")]
		public readonly int StrategicDepartureLoadedPercent = 65;

		[Desc("Minimum percentage of surviving planned passengers that must be loaded when an emergency DEFEND boarding deadline expires.")]
		public readonly int DefendDepartureLoadedPercent = 50;

		[Desc("Known local tactical enemy value multiplier retained on a source landmass before surplus Ground units may be exported. Strategic DEFEND/SECURE demand can require a larger reserve. This replaces the old all-or-nothing source block.")]
		public readonly int SourceTacticalReservePercent = 150;

		[Desc("World ticks between native Unload retries at the destination landing handoff.")]
		public readonly int UnloadRetryInterval = 75;

		[Desc("World ticks with no decrease in one LST's cargo count before GroundTransfer treats that craft as unload-stalled and tries a bounded alternate landing slot.")]
		public readonly int UnloadStallTimeout = 150;

		[Desc("Maximum bounded alternate landing-slot recovery moves for one LST before it keeps retrying native Unload in place.")]
		public readonly int MaximumUnloadRecoveryAttempts = 3;

		[Desc("Radius around the selected landing naval cell used for bounded alternate unload slots after a stalled native Unload.")]
		public readonly int UnloadRecoveryRadius = 4;

		[Desc("Minimum cells inland from the landing ground cell used for target-side staging slots so freshly unloaded units clear LST ramps instead of blocking following cargo.")]
		public readonly int BeachClearDistance = 3;

		[Desc("Maximum world ticks to wait for target-side regroup before releasing survivors to Ground Commander anyway.")]
		public readonly int RegroupTimeout = 750;

		[Desc("Cooldown after a completed/aborted convoy before another convoy may be planned.")]
		public readonly int WaveCooldown = 250;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			if (ScanInterval <= 0 || PlanningInterval <= 0 || string.IsNullOrEmpty(LandingCraftQueueCategory) ||
				MinimumCashForLandingCraftRequest < 0 || LandingCraftProductionRequestCooldown <= 0 ||
				MaximumConvoyLandingCraft <= 0 || DesiredUnitsPerLandingCraft <= 0 ||
				NavalFormationRadius <= 0 || SeaSecureLeaseTicks <= ScanInterval ||
				MinimumDefendWaveUnits <= 0 || MinimumStrategicWaveUnits <= 0 || SourceBaseReserveUnits < 0 ||
				MinimumMissionGroundValue <= 0 || SecureForceMultiplierPercent <= 0 || DefendForceMultiplierPercent <= 0 ||
				ForwardAnchorDesiredGroundValue <= 0 || BoardingAssemblyRadius <= 0 || BoardingZoneRadius <= 0 ||
				LandingCraftBoardingReadyRadius <= 0 || StagingSlotRadius <= 0 ||
				RegroupRadius <= 0 || RegroupRequiredPercent <= 0 || RegroupRequiredPercent > 100 || StallTimeout <= 0 ||
				CrossingSameLegRetries < 0 || MaximumCrossingRecoveryAttempts < 0 || CrossingRecoveryRadius <= 0 || CrossingRecoveryCandidateLimit <= 0 ||
				MaximumPreBoardingStallRetries < 0 || BoardingRetryInterval <= 0 || BoardingNativeTimeout <= 0 ||
				StrategicBoardingDeadline <= 0 || DefendBoardingDeadline <= 0 ||
				StrategicDepartureLoadedPercent <= 0 || StrategicDepartureLoadedPercent > 100 ||
				DefendDepartureLoadedPercent <= 0 || DefendDepartureLoadedPercent > 100 || SourceTacticalReservePercent < 100 ||
				RemoteSecureDesiredGroundValue < MinimumMissionGroundValue || SecureFollowOnReinforcementPercent < 100 || UnloadRetryInterval <= 0 ||
				UnloadStallTimeout <= 0 || MaximumUnloadRecoveryAttempts < 0 || UnloadRecoveryRadius <= 0 || BeachClearDistance <= 0 ||
				RegroupTimeout <= 0 || WaveCooldown < 0)
				throw new YamlException("FransGroundTransferBotModule has invalid timing/capacity configuration.");
		}

		public override object Create(ActorInitializer init) { return new FransGroundTransferBotModule(init.Self, this); }
	}

	public class FransGroundTransferBotModule : ConditionalTrait<FransGroundTransferBotModuleInfo>,
		IBotTick, IBotEnabled, IFransGroundTransferService
	{
		const string LivenessDiagnosticPrefix = "[GROUND TRANSFER LIVENESS]";
		const string PlanningDiagnosticPrefix = "[GROUND TRANSFER PLAN]";

		enum TransferState
		{
			Assemble,
			Boarding,
			Crossing,
			Returning,
			Unloading,
			Regroup
		}

		readonly record struct RegionalLandingCraftSupply(
			int NavalRegionId,
			int PhysicalCount,
			int RegionBoundQueuedCount,
			bool HasEligibleProducer,
			string EligibleProducerActorIds)
		{
			public int GuaranteedCount => PhysicalCount + RegionBoundQueuedCount;
		}

		enum LandingCraftCorridorState
		{
			SafeCommonRegion,
			TopologyUnresolved,
			NoCommonNavalRegion,
			TransportLossBlocked
		}

		sealed class TransferWave
		{
			public FransMissionType? MissionType;
			public uint TargetActorId;
			public CPos TargetCell;
			public int SourceLandmassId;
			public int TargetLandmassId;
			public FransGroundShoreAccess SourceShore;
			public FransGroundShoreAccess TargetShore;
			public readonly List<Actor> Crafts = [];
			public readonly List<Actor> Units = [];
			public readonly Dictionary<Actor, Actor> UnitCraft = [];
			public readonly Dictionary<Actor, CPos> SourceUnitSlots = [];
			public readonly Dictionary<Actor, CPos> TargetUnitSlots = [];
			public readonly Dictionary<Actor, CPos> SourceCraftSlots = [];
			public readonly Dictionary<Actor, CPos> TargetCraftSlots = [];
			public readonly HashSet<Actor> UnloadIssued = [];
			public readonly HashSet<Actor> BeachClearMoveIssued = [];
			public readonly Dictionary<Actor, int> LastCraftCargoCount = [];
			public readonly Dictionary<Actor, int> LastCraftUnloadProgressTick = [];
			public readonly Dictionary<Actor, int> CraftUnloadRecoveryAttempts = [];
			public readonly Dictionary<Actor, CPos> CraftUnloadRecoveryCell = [];
			public readonly Dictionary<Actor, int> BoardingReservationSinceTick = [];
			public readonly Dictionary<Actor, int> BoardingOrderUntilTick = [];
			public readonly Dictionary<Actor, CPos> BoardingLastProgressCell = [];
			public readonly Dictionary<Actor, int> BoardingLastProgressTick = [];
			public readonly Dictionary<Actor, CPos> CrossingLastProgressCell = [];
			public readonly Dictionary<Actor, int> CrossingLastProgressTick = [];
			public readonly Dictionary<Actor, int> CrossingSameLegRetryCount = [];
			public readonly Dictionary<Actor, int> CrossingRecoveryAttempts = [];
			public readonly HashSet<Actor> ReturnUnloadIssued = [];
			public readonly Dictionary<Actor, int> ReturnLastCargoCount = [];
			public readonly Dictionary<Actor, int> ReturnLastCargoProgressTick = [];
			// Diagnostic-only objective/cargo progress epochs. Gameplay continues to use the
			// existing Crossing*/Return* fields above; these values only make a final fallback
			// distinguishable from slow but real progress in a fresh runtime packet.
			public readonly Dictionary<Actor, CPos> ReturnDiagnosticTarget = [];
			public readonly Dictionary<Actor, int> ReturnBestDistanceSquared = [];
			public readonly Dictionary<Actor, int> ReturnLastDistanceProgressTick = [];
			public readonly Dictionary<Actor, int> ReturnUnloadLastRealProgressTick = [];
			public readonly Dictionary<Actor, int> ReturnUnloadNextDiagnosticTick = [];
			public readonly Dictionary<Actor, int> DestinationUnloadLastRealProgressTick = [];
			public bool ReturnUnloadPhaseLogged;
			public TransferState State;
			public int StartedTick;
			public int StateStartedTick;
			public int LastProgressTick;
			public long LastMovementMetric = long.MaxValue;
			public int LastAssembledCount = -1;
			public int LastLoadedCount = -1;
			public int LastBoardingReservedCount = -1;
			public int LastRegroupedCount = -1;
			public int StallRetries;
			public int NextBoardingRetryTick;
			public int NextUnloadRetryTick;
			public bool TransportsReleased;
			public FransRiskAssessment LandingRisk;
			public uint SeaSupportRequestId;
			public int TransportLossExclusionRevision;
		}

		readonly World world;
		FransQueueDomains queueDomains;
		FransQueueDomains QueueDomains => queueDomains ??= FransQueueDomains.For(world.Map.Rules);

		// The configured landing-craft queue name plus every naval-domain queue alias the
		// ruleset declares — resolves in classic ("Ship") and hybrid ("RANaval") modes.
		FrozenSet<string> ShipQueueNames() =>
			QueueDomains.Naval.Union(new[] { Info.LandingCraftQueueCategory })
				.ToFrozenSet(StringComparer.OrdinalIgnoreCase);
		readonly Player player;

		readonly HashSet<Actor> pendingStopOrders = [];
		IBot orderBot;

		void IBotEnabled.BotEnabled(IBot bot)
		{
			orderBot = bot;
		}

		// §19.6: a bot runs on the host alone and may touch actors ONLY through orders — a
		// direct CancelActivity/QueueActivity desyncs a multiplayer game. With no live bot
		// sink the request parks in the pending sets; FlushPendingSynchronizedActions
		// replays it on this module's own tick, keeping issuer/holder pairing correct.
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
				sink.QueueOrder(new Order("Stop", actor, false));
				return;
			}

			pendingStopOrders.Add(actor);
		}

		void FlushPendingSynchronizedActions(IBot bot)
		{
			if (bot == null || pendingStopOrders.Count == 0)
				return;

			foreach (var actor in pendingStopOrders.OrderBy(a => a.ActorID).ToArray())
				if (IsValidOrderSubject(actor))
					bot.QueueOrder(new Order("Stop", actor, false));

			pendingStopOrders.Clear();
		}

		Actor reservationOwner;
		IFransStrategicMapService strategicMap;
		IFransGeneralService general;
		IFransCombatIntelService combatIntel;
		IFransGroundCommanderService[] groundCommanders;
		IFransCaptureSecurityService[] captureSecurity;
		IFransCaptureTransportService transportService;
		IFransAmphibiousExpansionService amphibiousExpansion;
		IFransRiskModelService riskModel;
		IBotRequestUnitProduction[] requestUnitProduction;
		PlayerResources playerResources;
		readonly HashSet<Actor> reservedGroundUnits = [];
		TransferWave activeWave;
		int scanTicks;
		int nextPlanningTick;
		int nextLandingCraftProductionRequestTick;
		string lastPlanningDiagnosticSignature;
		int lastPlanningDiagnosticTick = -1;

		public FransGroundTransferBotModule(Actor self, FransGroundTransferBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		protected override void Created(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;

			reservationOwner = self;
			strategicMap = self.TraitsImplementing<IFransStrategicMapService>().FirstOrDefault()
				?? throw new InvalidOperationException("Ground Transfer requires FransStrategicMapBotModule.");
			general = self.TraitsImplementing<IFransGeneralService>().FirstOrDefault()
				?? throw new InvalidOperationException("Ground Transfer requires FransGeneralBotModule.");
			combatIntel = self.TraitsImplementing<IFransCombatIntelService>().FirstOrDefault()
				?? throw new InvalidOperationException("Ground Transfer requires FransCombatIntelBotModule.");
			groundCommanders = self.TraitsImplementing<IFransGroundCommanderService>().ToArray();
			if (groundCommanders.Length == 0)
				throw new InvalidOperationException("Ground Transfer requires at least one FransGroundCommanderBotModule.");
			captureSecurity = self.TraitsImplementing<IFransCaptureSecurityService>().ToArray();
			transportService = self.TraitsImplementing<IFransCaptureTransportService>().FirstOrDefault()
				?? throw new InvalidOperationException("Ground Transfer requires FransTransportCommanderBotModule for shared LST reservation.");
			amphibiousExpansion = self.TraitsImplementing<IFransAmphibiousExpansionService>().FirstOrDefault();
			riskModel = self.TraitsImplementing<IFransRiskModelService>().FirstOrDefault()
				?? throw new InvalidOperationException("Ground Transfer requires FransRiskModelBotModule.");
			requestUnitProduction = self.TraitsImplementing<IBotRequestUnitProduction>().ToArray();
			playerResources = self.Trait<PlayerResources>();
		}

		protected override void TraitEnabled(Actor self)
		{
			scanTicks = (int)((self.ActorID + 17u) % (uint)Info.ScanInterval) + 1;
			nextPlanningTick = world.WorldTick;
			nextLandingCraftProductionRequestTick = world.WorldTick;
			FransBotLog.BotDebug(world,
				"{0}: Ground Transfer FOLLOW-ON REINFORCEMENT active. GroundTransfer owns Ground passengers + LST logistics only. One ready LST may begin streaming boarding immediately; passengers use a broad embark zone and dynamically choose the nearest compatible ready LST with free Cargo instead of being permanently locked to one craft. Busy/reserved LSTs remain part of the shared bounded pool, so logistics waits for reuse instead of manufacturing replacement craft. Sea remains fully decoupled and supports only through the independent destination-shore SECURE.",
				player);
		}

		protected override void TraitDisabled(Actor self)
		{
			pendingStopOrders.Clear();
			ReleaseWave(cancelActivities: false, "trait disabled");
			reservedGroundUnits.Clear();
		}

		bool IFransGroundTransferService.IsGroundUnitTransferReserved(Actor actor) =>
			actor != null && reservedGroundUnits.Contains(actor);


		void IBotTick.BotTick(IBot bot)
		{
			FlushPendingSynchronizedActions(bot);
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransGroundTransfer.BotTick");
			if (world.Type == WorldType.Editor || player.WinState != WinState.Undefined)
				return;

			if (--scanTicks > 0)
				return;
			scanTicks = Info.ScanInterval;
			FransBotLog.SetPerfContext(world, $"GROUND-XFER:{player.PlayerActor.ActorID}",
				activeWave == null
					? "Idle"
					: $"wave={WaveDiagnosticId(activeWave)} {activeWave.State} src={activeWave.SourceLandmassId} dst={activeWave.TargetLandmassId} lst=[{ActorIds(activeWave.Crafts)}] sea-secure={activeWave.SeaSupportRequestId} units={activeWave.Units.Count}");

			combatIntel.EnsureCurrentSnapshot();
			if (activeWave != null)
			{
				RefreshSeaSupportLease();
				ManageWave(bot);
				return;
			}

			if (world.WorldTick < nextPlanningTick)
				return;
			nextPlanningTick = world.WorldTick + Info.PlanningInterval;
			using var planPerf = FransBotLog.Profile(world, player, "GroundTransfer.Plan");
			TryStartWave(bot);
		}

		void TryStartWave(IBot bot)
		{
			if (!TrySelectDemand(out var missionType, out var targetActorId, out var targetCell, out var targetLandmassId,
				out var requiredTargetValue, out var currentTargetValue, out var reason, out var demandDiagnostic))
			{
				LogPlanningOutcome(null, 0, default, 0,
					"Reject", "NoRemoteDemand", demandDiagnostic);
				return;
			}

			var allSourceGroups = EligibleGroundUnits()
				.Select(a => strategicMap.TryGetGroundLandmassId(a.Location, out var landmassId) ? (Actor: a, LandmassId: landmassId) : default)
				.Where(x => x.Actor != null && x.LandmassId != targetLandmassId)
				.GroupBy(x => x.LandmassId, x => x.Actor)
				.Select(g =>
				{
					var units = g.OrderBy(a => a.ActorID).ToArray();
					var reserveCount = HasEstablishedBase(g.Key) ? Info.SourceBaseReserveUnits : 0;
					var reserveValue = RequiredSourceReserveValue(g.Key);
					var transferable = SelectTransferableSurplusUnits(units, reserveCount, reserveValue);
					return new { LandmassId = g.Key, Units = units, Transferable = transferable, ReserveCount = reserveCount, ReserveValue = reserveValue };
				})
				.OrderByDescending(g => g.Transferable.Sum(GetUnitValue))
				.ThenByDescending(g => g.Transferable.Length)
				.ThenBy(g => g.LandmassId)
				.ToArray();
			var sourceGroups = allSourceGroups.Where(group => group.Transferable.Length > 0).ToArray();
			if (sourceGroups.Length == 0)
			{
				var pool = transportService.GetLandingCraftPoolDiagnostic(bot);
				var sourceState = allSourceGroups.Length == 0
					? "none"
					: string.Join(";", allSourceGroups.Select(source =>
						$"sourceLM={source.LandmassId}:eligible={source.Units.Length}/{source.Units.Sum(GetUnitValue)}," +
						$"reserve={source.ReserveCount}/{source.ReserveValue},transferable={source.Transferable.Length}/{source.Transferable.Sum(GetUnitValue)}"));
				LogPlanningOutcome(missionType, targetActorId, targetCell, targetLandmassId,
					"Reject", "NoTransferableSource",
					$"targetValue={currentTargetValue}/{requiredTargetValue} sources=[{sourceState}] {pool.Details} physicalEligibility=[{LandingCraftInventoryDiagnostic()}]");
				return;
			}

			var sourceRejections = new List<string>();

			foreach (var source in sourceGroups)
			{
				var transferable = source.Transferable;
				if (transferable.Length == 0)
					continue;

				var emergencyDefend = missionType == FransMissionType.Defend;
				var desiredCraftCount = DesiredCraftCount(transferable.Length);
				var sourceHint = new CPos((int)transferable.Average(a => a.Location.X), (int)transferable.Average(a => a.Location.Y));
				var supplyDiagnostic = EnsureLandingCraftCapacity(bot, desiredCraftCount, source.LandmassId, targetLandmassId, sourceHint, targetCell,
					missionType, targetActorId);
				var sourceDiagnostic = SourcePlanningDiagnostic(source.LandmassId, source.Units, transferable,
					source.ReserveCount, source.ReserveValue, desiredCraftCount, supplyDiagnostic);

				if (!TryChooseConvoyAndShorePair(source.LandmassId, targetLandmassId, transferable, targetCell,
					desiredCraftCount, emergencyDefend, out var crafts, out var sourceShore, out var targetShore, out var landingRisk,
					out var convoyDiagnostic))
				{
					sourceRejections.Add($"{sourceDiagnostic} convoy=[{convoyDiagnostic}]");
					continue;
				}

				if (!TryBuildUnitCraftAssignments(transferable, sourceShore.GroundCell, crafts, out var selected, out var unitCraft))
				{
					sourceRejections.Add($"{sourceDiagnostic} convoy=[{convoyDiagnostic}] result=NoCompatibleUnitCraftAssignment");
					continue;
				}

				var minimumUnits = emergencyDefend ? Info.MinimumDefendWaveUnits : Info.MinimumStrategicWaveUnits;
				var effectiveMinimumUnits = Math.Min(minimumUnits, transferable.Length);
				if (selected.Length < effectiveMinimumUnits)
				{
					sourceRejections.Add($"{sourceDiagnostic} convoy=[{convoyDiagnostic}] result=BelowMinimumWave selected={selected.Length}/{effectiveMinimumUnits}");
					continue;
				}

				var usedCrafts = unitCraft.Values.Distinct().OrderBy(a => a.ActorID).ToArray();
				// Do not launch a deliberately under-capacity convoy. Production demand is derived
				// from the currently transferable passengers, so wait for that exact capacity.
				if (usedCrafts.Length < desiredCraftCount)
				{
					sourceRejections.Add($"{sourceDiagnostic} convoy=[{convoyDiagnostic}] result=InsufficientRegionalCraftCapacity usedCrafts={usedCrafts.Length}/{desiredCraftCount} selectedUnits={selected.Length}");
					continue;
				}

				if (!TryAssignNavalSlots(usedCrafts, sourceShore.NavalCell, sourceShore.NavalRegionId, Info.NavalFormationRadius, out var sourceCraftSlots))
				{
					sourceRejections.Add($"{sourceDiagnostic} convoy=[{convoyDiagnostic}] result=NoSourceNavalFormationSlots crafts=[{ActorIds(usedCrafts)}]");
					continue;
				}
				if (!TryAssignNavalSlots(usedCrafts, targetShore.NavalCell, targetShore.NavalRegionId, Info.NavalFormationRadius, out var targetCraftSlots))
				{
					sourceRejections.Add($"{sourceDiagnostic} convoy=[{convoyDiagnostic}] result=NoTargetNavalFormationSlots crafts=[{ActorIds(usedCrafts)}]");
					continue;
				}

				var reservedCrafts = new List<Actor>();
				var reserveFailed = false;
				uint reserveFailedCraftId = 0;
				foreach (var craft in usedCrafts)
				{
					if (!transportService.TryReserveExternalTransport(craft, reservationOwner))
					{
						reserveFailed = true;
						reserveFailedCraftId = craft.ActorID;
						break;
					}
					reservedCrafts.Add(craft);
				}
				if (reserveFailed)
				{
					foreach (var craft in reservedCrafts)
						transportService.ReleaseExternalTransport(craft, reservationOwner);
					sourceRejections.Add($"{sourceDiagnostic} convoy=[{convoyDiagnostic}] result=ExternalReservationRejected craft={reserveFailedCraftId} releasedPartial=[{ActorIds(reservedCrafts)}]");
					continue;
				}

				var wave = new TransferWave
				{
					MissionType = missionType,
					TargetActorId = targetActorId,
					TargetCell = targetCell,
					SourceLandmassId = source.LandmassId,
					TargetLandmassId = targetLandmassId,
					SourceShore = sourceShore,
					TargetShore = targetShore,
					State = TransferState.Assemble,
					StartedTick = world.WorldTick,
					StateStartedTick = world.WorldTick,
					LastProgressTick = world.WorldTick,
					LandingRisk = landingRisk,
					TransportLossExclusionRevision = general.TransportLossExclusionRevision
				};
				wave.Crafts.AddRange(usedCrafts);
				wave.Units.AddRange(selected);
				foreach (var pair in unitCraft)
					if (selected.Contains(pair.Key) && usedCrafts.Contains(pair.Value))
						wave.UnitCraft[pair.Key] = pair.Value;
				foreach (var pair in sourceCraftSlots)
					wave.SourceCraftSlots[pair.Key] = pair.Value;
				foreach (var pair in targetCraftSlots)
					wave.TargetCraftSlots[pair.Key] = pair.Value;
				AssignGroundSlots(wave, sourceSide: true);
				AssignGroundSlots(wave, sourceSide: false);
				foreach (var unit in wave.Units)
					reservedGroundUnits.Add(unit);
				activeWave = wave;
				wave.SeaSupportRequestId = wave.Crafts.Min(a => a.ActorID);
				general.RequestSeaTransportBeachSecure(wave.SeaSupportRequestId, wave.TargetShore.NavalCell, world.WorldTick + Info.SeaSecureLeaseTicks);

				IssueAssembleOrders(bot, wave, force: true);
				FransBotLog.BotDebug(world,
					"{0}: GROUND TRANSFER CONVOY starts {1}-unit wave {2}->{3} using {4} LST(s) [{5}], embark {6}/{7}, landing {8}/{9}; target {10} ({11}), local value {12}/{13}, landing risk {14}/{15}. {16}. Sea combat is fully decoupled: General opened independent Sea-only SECURE {17} at the destination landing shore; no Sea ship is reserved or ordered by GroundTransfer.",
					player, wave.Units.Count, wave.SourceLandmassId, wave.TargetLandmassId, wave.Crafts.Count,
					string.Join(",", wave.Crafts.Select(a => a.ActorID)), wave.SourceShore.GroundCell, wave.SourceShore.NavalCell,
					wave.TargetShore.NavalCell, wave.TargetShore.GroundCell, targetCell, missionType?.ToString() ?? "ForwardAnchor",
					currentTargetValue, requiredTargetValue, landingRisk.Score, landingRisk.CriticalThreshold, reason, wave.SeaSupportRequestId);
				FransBotLog.BotDebug(world,
					"{0}: {1} wave={2} transition=None->Assemble reason=acquired mission={3}/{4} groundActors=[{5}] crafts=[{6}] sourceShore={7}/{8} destinationShore={9}/{10} seaLease={11} {12}.",
					player, LivenessDiagnosticPrefix, WaveDiagnosticId(wave), missionType?.ToString() ?? "ForwardAnchor", targetActorId,
					ActorIds(wave.Units), ActorIds(wave.Crafts), wave.SourceShore.GroundCell, wave.SourceShore.NavalCell,
					wave.TargetShore.GroundCell, wave.TargetShore.NavalCell, wave.SeaSupportRequestId, ReservationDiagnostic(wave));
				LogPlanningOutcome(missionType, targetActorId, targetCell, targetLandmassId,
					"Acquire", "NoneToAssemble",
					$"{sourceDiagnostic} convoy=[{convoyDiagnostic}] selectedUnits=[{ActorIds(selected)}] reservedCrafts=[{ActorIds(usedCrafts)}]");
				return;
			}

			LogPlanningOutcome(missionType, targetActorId, targetCell, targetLandmassId,
				"Reject", "AllSourcesRejected",
				$"targetValue={currentTargetValue}/{requiredTargetValue} sources=[{string.Join(" || ", sourceRejections)}]");
		}

		string SourcePlanningDiagnostic(int sourceLandmassId, Actor[] eligible, Actor[] transferable,
			int reserveCount, int reserveValue, int desiredCraftCount, string supplyDiagnostic) =>
			$"sourceLM={sourceLandmassId} eligibleUnits={eligible.Length} transferableUnits={transferable.Length}" +
			$"/{transferable.Sum(GetUnitValue)} reserve={reserveCount}/{reserveValue} desiredCrafts={desiredCraftCount} supply=[{supplyDiagnostic}]";

		void LogPlanningOutcome(FransMissionType? missionType, uint targetActorId, CPos targetCell,
			int targetLandmassId, string result, string rejectionReason, string details)
		{
			var signature = $"mission={missionType}/{targetActorId}|target={targetCell}/{targetLandmassId}|result={result}|reason={rejectionReason}|{details}";
			var heartbeat = Math.Max(1000, Info.PlanningInterval * 4);
			if (signature == lastPlanningDiagnosticSignature && lastPlanningDiagnosticTick >= 0 &&
				world.WorldTick - lastPlanningDiagnosticTick < heartbeat)
				return;

			lastPlanningDiagnosticSignature = signature;
			lastPlanningDiagnosticTick = world.WorldTick;
			FransBotLog.BotDebug(world,
				"{0}: {1} mission={2}/{3} targetCell={4} targetLM={5} result={6} reason={7} {8}.",
				player, PlanningDiagnosticPrefix, missionType?.ToString() ?? "ForwardAnchor", targetActorId,
				targetCell, targetLandmassId, result, rejectionReason, details);
		}

		int DesiredCraftCount(int transferableUnits)
		{
			// LST count is pure passenger demand, never a standing convoy target.
			// CargoInfo remains authoritative at assignment time; this only sizes production.
			var byUnits = Math.Max(1, (transferableUnits + Info.DesiredUnitsPerLandingCraft - 1) / Info.DesiredUnitsPerLandingCraft);
			return Math.Min(byUnits, Info.MaximumConvoyLandingCraft);
		}

		string EnsureLandingCraftCapacity(IBot bot, int desiredCraftCount, int sourceLandmassId, int targetLandmassId,
			CPos sourceHint, CPos targetHint, FransMissionType? missionType, uint targetActorId)
		{
			var pool = transportService.GetLandingCraftPoolDiagnostic(bot);
			var nonStrategicCap = transportService.MaximumNonStrategicLandingCraftPool;
			var desiredBoundedCount = Math.Min(desiredCraftCount, nonStrategicCap);
			string SupplyState(string outcome, string detail) =>
				$"outcome={outcome} desired={desiredBoundedCount} global={pool.AuthoritativeCount}/{nonStrategicCap}" +
				$" hardCap={transportService.MaximumLandingCraftPool} {pool.Details} {detail}";

			if (amphibiousExpansion?.HasStrategicLandingCraftProductionDemand == true)
			{
				nextLandingCraftProductionRequestTick = world.WorldTick + Info.LandingCraftProductionRequestCooldown;
				return SupplyState("McvStrategicProductionPriority", "new GroundTransfer production yielded");
			}

			if (desiredCraftCount <= 0)
				return SupplyState("NoCraftDemand", "no production requested");
			if (playerResources == null || playerResources.GetCashAndResources() < Info.MinimumCashForLandingCraftRequest)
				return SupplyState("InsufficientBudget", $"minimumCash={Info.MinimumCashForLandingCraftRequest}");

			var corridorState = ClassifyLandingCraftProductionCorridor(sourceLandmassId, targetLandmassId, sourceHint, targetHint,
				out var safeNavalRegions, out var sourceShoreCandidates, out var targetShoreCandidates,
				out var commonShorePairs, out var lossSafeShorePairs, out var blockerAttribution);
			if (corridorState == LandingCraftCorridorState.TransportLossBlocked)
			{
				nextLandingCraftProductionRequestTick = world.WorldTick + Info.LandingCraftProductionRequestCooldown;
				FransBotLog.BotDebug(world,
					"{0}: GROUND TRANSFER suppresses new LST production for mission {1}/{2}, landmass {3} -> {4}; all fair-known common shoreline corridors intersect an active LST-loss SECURE exclusion. Existing combat SECURE work may clear it; logistics retries after cooldown/revision change. {5}",
					player, missionType?.ToString() ?? "ForwardAnchor", targetActorId, sourceLandmassId, targetLandmassId,
					blockerAttribution);
				return SupplyState("TransportLossCorridorBlocked",
					$"sourceShores={sourceShoreCandidates} targetShores={targetShoreCandidates} commonPairs={commonShorePairs} lossSafePairs={lossSafeShorePairs} regions=[{string.Join(",", safeNavalRegions)}] {blockerAttribution}");
			}
			if (corridorState == LandingCraftCorridorState.NoCommonNavalRegion)
			{
				nextLandingCraftProductionRequestTick = world.WorldTick + Info.LandingCraftProductionRequestCooldown;
				return SupplyState("NoCommonNavalRegion",
					$"sourceShores={sourceShoreCandidates} targetShores={targetShoreCandidates} commonPairs=0; known shoreline topology cannot execute this corridor");
			}

			var unitBuilder = requestUnitProduction?.FirstEnabledTraitOrDefault();
			if (unitBuilder == null)
				return SupplyState("NoUnitBuilder", "production service unavailable");

			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			var shipQueueNames = ShipQueueNames();
			var shipQueues = shipQueueNames.SelectMany(name => queuesByCategory[name]).Where(q => q.Enabled).Distinct().ToArray();
			if (shipQueues.Length == 0)
				return SupplyState("NoEnabledShipQueue", "no Ship queue can receive LST production");

			var craftType = Info.LandingCraftTypes.OrderBy(x => x).FirstOrDefault(type =>
				world.Map.Rules.Actors.TryGetValue(type, out var actorInfo) &&
				actorInfo.TraitInfoOrDefault<BuildableInfo>() is BuildableInfo buildable &&
				buildable.Queue.Any(shipQueueNames.Contains) &&
				shipQueues.Any(q => q.BuildableItems().Any(i => i.Name == type)));
			if (craftType == null)
				return SupplyState("NoBuildableLandingCraftType", "configured LST types expose no Ship buildable");

			var regionSupplies = safeNavalRegions
				.Select(region => GetRegionalLandingCraftSupply(shipQueues, craftType, region))
				.ToArray();
			var unboundSharedQueued = CountUnboundSharedLandingCraftProduction(shipQueues);
			var regionalDetails = regionSupplies.Length == 0
				? "none"
				: string.Join(";", regionSupplies.Select(s =>
					$"region={s.NavalRegionId}:physical={s.PhysicalCount},regionBoundQueued={s.RegionBoundQueuedCount}," +
					$"producerAvailable={s.HasEligibleProducer},producerActors={s.EligibleProducerActorIds}"));

			if (regionSupplies.Any(s => s.GuaranteedCount >= desiredBoundedCount))
			{
				nextLandingCraftProductionRequestTick = world.WorldTick + Info.LandingCraftProductionRequestCooldown;
				return SupplyState("RegionalSupplySatisfied",
					$"sourceShores={sourceShoreCandidates} targetShores={targetShoreCandidates} commonPairs={commonShorePairs} lossSafePairs={lossSafeShorePairs} " +
					$"unboundSharedQueued={unboundSharedQueued} regional=[{regionalDetails}]");
			}

			if (pool.AuthoritativeCount >= nonStrategicCap)
			{
				nextLandingCraftProductionRequestTick = world.WorldTick + Info.LandingCraftProductionRequestCooldown;
				return SupplyState("RegionalSupplyMissingAtNonStrategicCap",
					$"regions=[{regionalDetails}] wrong-region/global supply cannot create another non-strategic LST");
			}

			if (unboundSharedQueued > 0)
			{
				nextLandingCraftProductionRequestTick = world.WorldTick + Info.LandingCraftProductionRequestCooldown;
				return SupplyState("AwaitingUnboundSharedProduction",
					$"unboundSharedQueued={unboundSharedQueued} regions=[{regionalDetails}]; producer region becomes authoritative only after delivery");
			}

			if (world.WorldTick < nextLandingCraftProductionRequestTick)
				return SupplyState("ProductionCooldown",
					$"untilWT={nextLandingCraftProductionRequestTick} regions=[{regionalDetails}]");

			// GroundTransfer may use any common source/destination naval region. Prefer an
			// already-partially-supplied region so the convoy's exact craft count can eventually
			// be satisfied in one sea; otherwise use the best loss-safe common region with a
			// producer. StrategicMap remains the sole topology authority.
			RegionalLandingCraftSupply? selectedRegionalSupply = regionSupplies
				.Where(s => s.HasEligibleProducer)
				.OrderByDescending(s => s.GuaranteedCount)
				.ThenBy(s => Array.IndexOf(safeNavalRegions, s.NavalRegionId))
				.Select(s => (RegionalLandingCraftSupply?)s)
				.FirstOrDefault();

			if (selectedRegionalSupply.HasValue)
			{
				var selected = selectedRegionalSupply.Value;
				if (!TryQueueLandingCraftSupply(bot, shipQueues, craftType, selected.NavalRegionId,
					out var producerBinding, out var queueState))
				{
					nextLandingCraftProductionRequestTick = world.WorldTick + Info.LandingCraftProductionRequestCooldown;
					return SupplyState("RegionalQueueRejected",
						$"requiredRegion={selected.NavalRegionId} regions=[{regionalDetails}] queue={queueState}");
				}

				nextLandingCraftProductionRequestTick = world.WorldTick + Info.LandingCraftProductionRequestCooldown;
				FransBotLog.BotDebug(world,
					"{0}: GROUND TRANSFER logistics demand queues {1} for naval region {2}; producerBinding={3}. Global non-strategic pool {4}/{5}, hard cap {6}, guaranteed regional supply {7}/{8}. Wrong-region craft remain reusable but do not satisfy this exact corridor.",
					player, craftType, selected.NavalRegionId, producerBinding, pool.AuthoritativeCount, nonStrategicCap,
					transportService.MaximumLandingCraftPool, selected.GuaranteedCount, desiredBoundedCount);
				return SupplyState(producerBinding == "RegionBound" ? "RegionBoundProductionStarted" : "UnboundProductionRequested",
					$"requiredRegion={selected.NavalRegionId} unboundSharedQueued={unboundSharedQueued} regions=[{regionalDetails}] queue={queueState}");
			}

			if (corridorState == LandingCraftCorridorState.SafeCommonRegion)
			{
				nextLandingCraftProductionRequestTick = world.WorldTick + Info.LandingCraftProductionRequestCooldown;
				return SupplyState("NoRegionalProducer",
					$"regions=[{regionalDetails}] no safe/common region has an enabled Ship producer for the missing supply");
			}

			// Preserve the prior fallback only while one side has no known shore access. If both
			// shore sets are known then a zero-region intersection is an authoritative current
			// topology rejection, not a reason to produce an unplaceable generic LST.
			if (pool.AuthoritativeCount >= desiredBoundedCount || pool.AuthoritativeCount >= nonStrategicCap)
			{
				nextLandingCraftProductionRequestTick = world.WorldTick + Info.LandingCraftProductionRequestCooldown;
				return SupplyState("GlobalSupplySatisfiedTopologyUnresolved",
					$"sourceShores={sourceShoreCandidates} targetShores={targetShoreCandidates} commonPairs={commonShorePairs}");
			}

			nextLandingCraftProductionRequestTick = world.WorldTick + Info.LandingCraftProductionRequestCooldown;
			unitBuilder.RequestUnitProduction(bot, craftType);
			FransBotLog.BotDebug(world,
				"{0}: GROUND TRANSFER logistics demand requests {1}; non-strategic physical+queued+requested LST pool {2}/{3}, global hard cap {4}, convoy demand {5}. The final pool slot stays reserved for PIONEER regional sea supply; all existing craft remain reusable when strategically free.",
				player, craftType, pool.AuthoritativeCount, nonStrategicCap, transportService.MaximumLandingCraftPool, desiredBoundedCount);
			return SupplyState("GenericRequestTopologyUnresolved",
				$"sourceShores={sourceShoreCandidates} targetShores={targetShoreCandidates} commonPairs={commonShorePairs}");
		}

		LandingCraftCorridorState ClassifyLandingCraftProductionCorridor(int sourceLandmassId, int targetLandmassId,
			CPos sourceHint, CPos targetHint, out int[] safeNavalRegions,
			out int sourceShoreCandidates, out int targetShoreCandidates,
			out int commonShorePairs, out int lossSafeShorePairs, out string blockerAttribution)
		{
			var allSourceAccess = strategicMap.GetGroundShoreAccess(sourceLandmassId);
			var allTargetAccess = strategicMap.GetGroundShoreAccess(targetLandmassId);
			var blockers = new Dictionary<uint, string>();
			var safeRegionScores = new Dictionary<int, long>();
			sourceShoreCandidates = allSourceAccess.Count;
			targetShoreCandidates = allTargetAccess.Count;
			commonShorePairs = 0;
			lossSafeShorePairs = 0;
			if (allSourceAccess.Count == 0 || allTargetAccess.Count == 0)
			{
				safeNavalRegions = Array.Empty<int>();
				blockerAttribution = "[TRANSPORT-LOSS BLOCKER] attribution=None";
				return LandingCraftCorridorState.TopologyUnresolved;
			}

			var commonRegions = allSourceAccess.Select(access => access.NavalRegionId)
				.Intersect(allTargetAccess.Select(access => access.NavalRegionId))
				.OrderBy(region => region)
				.ToArray();
			if (commonRegions.Length == 0)
			{
				safeNavalRegions = Array.Empty<int>();
				blockerAttribution = "[TRANSPORT-LOSS BLOCKER] attribution=None";
				return LandingCraftCorridorState.NoCommonNavalRegion;
			}

			foreach (var regionId in commonRegions)
				foreach (var source in allSourceAccess.Where(access => access.NavalRegionId == regionId)
					.OrderBy(access => (access.GroundCell - sourceHint).LengthSquared)
					.ThenBy(access => access.NavalCell.X).ThenBy(access => access.NavalCell.Y).Take(8))
				foreach (var target in allTargetAccess.Where(access => access.NavalRegionId == regionId)
					.OrderBy(access => (access.GroundCell - targetHint).LengthSquared)
					.ThenBy(access => access.NavalCell.X).ThenBy(access => access.NavalCell.Y).Take(8))
				{
					commonShorePairs++;
					if (general.IsTransportLossCorridorAllowed(source.NavalCell, target.NavalCell))
					{
						lossSafeShorePairs++;
						var score = (long)(source.GroundCell - sourceHint).LengthSquared +
							(target.GroundCell - targetHint).LengthSquared;
						if (!safeRegionScores.TryGetValue(source.NavalRegionId, out var previous) || score < previous)
							safeRegionScores[source.NavalRegionId] = score;
						continue;
					}
					if (general.TryGetTransportLossCorridorBlocker(source.NavalCell, target.NavalCell, out var blocker) &&
						!blockers.ContainsKey(blocker.IncidentId))
						blockers.Add(blocker.IncidentId,
							$"[TRANSPORT-LOSS BLOCKER] incident={blocker.IncidentId},incidentCell={blocker.IncidentCell}," +
							$"latestLossCell={blocker.LatestLossCell},blockingCorridorCell={blocker.BlockingRouteCell}," +
							$"radius={blocker.ExclusionRadius},state={blocker.LifecycleState},owner={blocker.Owner}," +
							$"corridor={source.NavalCell}->{target.NavalCell}");
				}

			safeNavalRegions = safeRegionScores
				.OrderBy(pair => pair.Value)
				.ThenBy(pair => pair.Key)
				.Select(pair => pair.Key)
				.ToArray();

			blockerAttribution = blockers.Count == 0
				? "[TRANSPORT-LOSS BLOCKER] attribution=None"
				: string.Join(" | ", blockers.OrderBy(kv => kv.Key).Select(kv => kv.Value));
			return safeNavalRegions.Length > 0
				? LandingCraftCorridorState.SafeCommonRegion
				: LandingCraftCorridorState.TransportLossBlocked;
		}

		RegionalLandingCraftSupply GetRegionalLandingCraftSupply(ProductionQueue[] shipQueues, string craftType, int navalRegionId)
		{
			combatIntel.EnsureCurrentSnapshot();
			var physical = combatIntel.OwnedActors.Count(actor =>
				actor != null && !actor.Disposed && actor.IsInWorld && !actor.IsDead && actor.Owner == player &&
				Info.LandingCraftTypes.Contains(actor.Info.Name) &&
				actor.TraitOrDefault<Mobile>() is Mobile mobile &&
				strategicMap.TryGetNavalRegionId(mobile.ToCell, out var region) && region == navalRegionId);
			var regionBoundQueued = shipQueues.Sum(queue => queue.AllQueued().Count(item =>
				Info.LandingCraftTypes.Contains(item.Item) &&
				TryGetRegionBoundProductionQueueNavalRegion(queue, item.Item, out var region) && region == navalRegionId));
			var eligibleProducers = GetEligibleLandingCraftProducers(shipQueues, craftType, navalRegionId);
			return new RegionalLandingCraftSupply(navalRegionId, physical, regionBoundQueued,
				eligibleProducers.Length > 0,
				eligibleProducers.Length == 0 ? "none" : string.Join(",", eligibleProducers.Select(a => a.ActorID)));
		}

		int CountUnboundSharedLandingCraftProduction(IEnumerable<ProductionQueue> shipQueues) => shipQueues
			.Sum(queue => queue.AllQueued().Count(item => Info.LandingCraftTypes.Contains(item.Item) &&
				!TryGetRegionBoundProductionQueueNavalRegion(queue, item.Item, out _)));

		bool TryQueueLandingCraftSupply(IBot bot, ProductionQueue[] shipQueues, string craftType,
			int navalRegionId, out string producerBinding, out string state)
		{
			var producers = GetEligibleLandingCraftProducers(shipQueues, craftType, navalRegionId);
			var queue = shipQueues
				.Where(q => TryGetRegionBoundProductionQueueNavalRegion(q, craftType, out var region) && region == navalRegionId)
				.Where(q => producers.Contains(q.Actor))
				.Where(q => q.BuildableItems().Any(item => item.Name == craftType))
				.OrderBy(q => q.AllQueued().Count())
				.ThenBy(q => q.Actor.ActorID)
				.FirstOrDefault();
			if (queue != null)
			{
				producerBinding = "RegionBound";
				state = $"queueActor={queue.Actor.ActorID}/{queue.Actor.Info.Name},producerBinding=RegionBound,region={navalRegionId}";
			}
			else
			{
				queue = shipQueues
					.Where(q => !TryGetRegionBoundProductionQueueNavalRegion(q, craftType, out _))
					.Where(q => q.BuildableItems().Any(item => item.Name == craftType))
					.OrderBy(q => q.AllQueued().Count())
					.ThenBy(q => q.Actor.ActorID)
					.FirstOrDefault();
				if (queue == null || producers.Length == 0)
				{
					producerBinding = "Unavailable";
					state = $"no eligible producer in naval region {navalRegionId} is backed by an enabled Ship queue for {craftType}";
					return false;
				}

				producerBinding = "UnboundUntilDelivery";
				state = $"queueActor={queue.Actor.ActorID}/{queue.Actor.Info.Name},producerBinding=UnboundUntilDelivery," +
					$"candidateProducerActors={string.Join(",", producers.Select(a => a.ActorID))},desiredRegion={navalRegionId}";
			}

			bot.QueueOrder(Order.StartProduction(queue.Actor, craftType, 1));
			return true;
		}

		Actor[] GetEligibleLandingCraftProducers(IEnumerable<ProductionQueue> shipQueues, string craftType, int navalRegionId)
		{
			var queues = shipQueues.Where(queue => queue.Enabled &&
				queue.BuildableItems().Any(item => item.Name == craftType)).ToArray();
			var productionType = world.Map.Rules.Actors[craftType].TraitInfo<BuildableInfo>().BuildAtProductionType ??
				queues.Select(queue => queue.Info.Type).FirstOrDefault();
			var boundProducers = queues
				.Where(queue => TryGetRegionBoundProductionQueueNavalRegion(queue, craftType, out var region) &&
					region == navalRegionId)
				.Where(queue => queue.Actor.TraitsImplementing<Production>().Any(production =>
					!production.IsTraitDisabled && !production.IsTraitPaused && production.Info.Produces.Contains(productionType)))
				.Select(queue => queue.Actor);
			var sharedProductionTypes = queues
				.Where(queue => !TryGetRegionBoundProductionQueueNavalRegion(queue, craftType, out _))
				.Select(queue => world.Map.Rules.Actors[craftType].TraitInfo<BuildableInfo>().BuildAtProductionType ?? queue.Info.Type)
				.ToHashSet();
			var sharedQueueProducers = world.ActorsWithTrait<Production>()
				.Where(pair => pair.Actor.Owner == player && pair.Actor.IsInWorld && !pair.Actor.IsDead &&
					!pair.Trait.IsTraitDisabled && !pair.Trait.IsTraitPaused &&
					pair.Trait.Info.Produces.Any(sharedProductionTypes.Contains) &&
					TryGetNavalRegionNearActor(pair.Actor, out var region) && region == navalRegionId)
				.Select(pair => pair.Actor);
			return boundProducers.Concat(sharedQueueProducers)
				.Distinct()
				.OrderBy(actor => actor.ActorID)
				.ToArray();
		}

		bool TryGetRegionBoundProductionQueueNavalRegion(ProductionQueue queue, string craftType, out int navalRegionId)
		{
			navalRegionId = -1;
			if (queue == null || !queue.Enabled || !world.Map.Rules.Actors.TryGetValue(craftType, out var actorInfo) ||
				actorInfo.TraitInfoOrDefault<BuildableInfo>() is not BuildableInfo buildable)
				return false;

			var productionType = buildable.BuildAtProductionType ?? queue.Info.Type;
			var queueOwnsProducer = queue.Actor.TraitsImplementing<Production>()
				.Any(production => production.Info.Produces.Contains(productionType));
			return queueOwnsProducer && TryGetNavalRegionNearActor(queue.Actor, out navalRegionId);
		}

		bool TryGetNavalRegionNearActor(Actor actor, out int navalRegionId)
		{
			navalRegionId = -1;
			if (actor == null || !actor.IsInWorld || actor.IsDead || actor.OccupiesSpace == null)
				return false;
			if (strategicMap.TryGetNavalRegionId(actor.Location, out navalRegionId))
				return true;

			foreach (var cell in world.Map.FindTilesInCircle(actor.Location, 3)
				.Where(world.Map.Contains)
				.OrderBy(c => (c - actor.Location).LengthSquared)
				.ThenBy(c => c.X)
				.ThenBy(c => c.Y))
				if (strategicMap.TryGetNavalRegionId(cell, out navalRegionId))
					return true;

			return false;
		}

		bool TrySelectDemand(out FransMissionType? missionType, out uint targetActorId, out CPos targetCell,
			out int targetLandmassId, out int requiredValue, out int currentValue, out string reason,
			out string diagnostic)
		{
			missionType = null;
			targetActorId = 0;
			targetCell = default;
			targetLandmassId = 0;
			requiredValue = 0;
			currentValue = 0;
			reason = null;
			diagnostic = null;

			general.EnsureCurrentMissions();
			var missionEvaluations = new List<string>();
			foreach (var mission in general.CurrentMissions
				.Where(m => (m.Type == FransMissionType.Defend || m.Type == FransMissionType.Secure) &&
					m.TargetActorType != FransGeneralBotModule.SeaTransportBeachSecureTargetType &&
					m.TargetActorType != FransGeneralBotModule.TransportLossSecureTargetType)
				.OrderByDescending(m => m.Type == FransMissionType.Defend)
				.ThenByDescending(m => m.StrategicPriority)
				.ThenBy(m => m.TargetActorId))
			{
				if (!strategicMap.TryGetGroundLandmassId(mission.LastVisibleTargetCell, out var landmassId))
				{
					missionEvaluations.Add($"{mission.Type}/{mission.TargetActorId}:NoTargetLandmass cell={mission.LastVisibleTargetCell}");
					continue;
				}

				var observedTacticalValue = (mission.SiteIntel.Actors ?? Array.Empty<FransSiteIntelActor>())
					.Where(a => a.IsCombatActor || a.IsDefensiveBuilding)
					.Sum(a => Math.Max(0, a.ObservedValue));
				var multiplier = mission.Type == FransMissionType.Secure
					? Info.SecureForceMultiplierPercent
					: Info.DefendForceMultiplierPercent;
				var needed = Math.Max(Info.MinimumMissionGroundValue,
					(int)Math.Min(int.MaxValue, (long)observedTacticalValue * multiplier / 100));
				if (mission.Type == FransMissionType.Secure)
					needed = Math.Max(Info.RemoteSecureDesiredGroundValue,
						(int)Math.Min(int.MaxValue, (long)needed * Info.SecureFollowOnReinforcementPercent / 100));
				var local = GroundValueOnLandmass(landmassId);
				if (local >= needed)
				{
					missionEvaluations.Add($"{mission.Type}/{mission.TargetActorId}:LocalValueSufficient landmass={landmassId} value={local}/{needed}");
					continue;
				}

				missionType = mission.Type;
				targetActorId = mission.TargetActorId;
				targetCell = mission.LastVisibleTargetCell;
				targetLandmassId = landmassId;
				requiredValue = needed;
				currentValue = local;
				reason = $"General {mission.Type} demand is understrength on another landmass";
				diagnostic = $"selected={mission.Type}/{mission.TargetActorId} targetLM={landmassId} value={local}/{needed}";
				return true;
			}

			if (!general.TryGetLatestGroundAnchor(out var anchor))
			{
				diagnostic = $"missions=[{string.Join(";", missionEvaluations)}] forwardAnchor=Unavailable";
				return false;
			}
			if (!strategicMap.TryGetGroundLandmassId(anchor, out var anchorLandmass))
			{
				diagnostic = $"missions=[{string.Join(";", missionEvaluations)}] forwardAnchor={anchor}:NoTargetLandmass";
				return false;
			}

			var anchorValue = GroundValueOnLandmass(anchorLandmass);
			targetCell = anchor;
			targetLandmassId = anchorLandmass;
			requiredValue = Math.Max(Info.ForwardAnchorDesiredGroundValue, anchorValue == int.MaxValue ? int.MaxValue : anchorValue + 1);
			currentValue = anchorValue;
			reason = "Forward Anchor redeployment/remote-landmass evacuation";
			diagnostic = $"selected=ForwardAnchor/0 targetLM={anchorLandmass} value={anchorValue}/{requiredValue}";
			return true;
		}

		IEnumerable<Actor> EligibleGroundUnits()
		{
			foreach (var actor in combatIntel.OwnedActors.OrderBy(a => a.ActorID))
			{
				if (actor == null || actor.Disposed || !actor.IsInWorld || actor.IsDead || !actor.IsIdle)
					continue;
				if (!groundCommanders.Any(g => g.IsGroundCombatUnitOwned(actor)) ||
					groundCommanders.Any(g => g.IsGroundCombatUnitMissionCommitted(actor)))
					continue;
				if (captureSecurity.Any(s => s.IsCaptureMissionActor(actor)))
					continue;
				if (actor.Info.TraitInfoOrDefault<PassengerInfo>() == null)
					continue;
				yield return actor;
			}
		}

		int GroundValueOnLandmass(int landmassId)
		{
			long total = 0;
			foreach (var actor in combatIntel.OwnedActors)
			{
				if (actor == null || actor.Disposed || !actor.IsInWorld || actor.IsDead ||
					!groundCommanders.Any(g => g.IsGroundCombatUnitOwned(actor)) ||
					!strategicMap.TryGetGroundLandmassId(actor.Location, out var actorLandmass) || actorLandmass != landmassId)
					continue;
				total += actor.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 1;
				if (total >= int.MaxValue)
					return int.MaxValue;
			}
			return (int)total;
		}

		bool HasEstablishedBase(int landmassId) => combatIntel.OwnedActors.Any(a =>
			a != null && a.IsInWorld && !a.IsDead && Info.SourceBaseAnchorTypes.Contains(a.Info.Name) &&
			strategicMap.TryGetGroundLandmassId(a.Location, out var lm) && lm == landmassId);

		int GetUnitValue(Actor actor) => Math.Max(1, actor?.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 1);

		int RequiredSourceReserveValue(int landmassId)
		{
			long tactical = 0;
			foreach (var contact in combatIntel.EnemyCombatContacts)
				if (contact.EstimatedValue > 0 && (!contact.IsBuilding || contact.IsDefensiveBuilding) &&
					strategicMap.TryGetGroundLandmassId(contact.LastSeenCell, out var lm) && lm == landmassId)
					tactical += contact.EstimatedValue;

			var tacticalReserve = (int)Math.Min(int.MaxValue, tactical * Info.SourceTacticalReservePercent / 100L);
			var strategicReserve = 0;
			foreach (var mission in general.CurrentMissions.Where(m =>
				(m.Type == FransMissionType.Defend || m.Type == FransMissionType.Secure) &&
				m.TargetActorType != FransGeneralBotModule.SeaTransportBeachSecureTargetType &&
				m.TargetActorType != FransGeneralBotModule.TransportLossSecureTargetType &&
				strategicMap.TryGetGroundLandmassId(m.LastVisibleTargetCell, out var lm) && lm == landmassId))
			{
				var observed = (mission.SiteIntel.Actors ?? Array.Empty<FransSiteIntelActor>())
					.Where(a => a.IsCombatActor || a.IsDefensiveBuilding)
					.Sum(a => Math.Max(0, a.ObservedValue));
				var multiplier = mission.Type == FransMissionType.Secure ? Info.SecureForceMultiplierPercent : Info.DefendForceMultiplierPercent;
				var needed = Math.Max(Info.MinimumMissionGroundValue, (int)Math.Min(int.MaxValue, (long)observed * multiplier / 100));
				strategicReserve = Math.Max(strategicReserve, needed);
			}

			return Math.Max(tacticalReserve, strategicReserve);
		}

		Actor[] SelectTransferableSurplusUnits(Actor[] units, int reserveCount, int reserveValue)
		{
			if (units == null || units.Length == 0)
				return Array.Empty<Actor>();

			var keep = new HashSet<Actor>();
			long keptValue = 0;
			foreach (var unit in units.OrderByDescending(GetUnitValue).ThenBy(a => a.ActorID))
			{
				if (keep.Count >= reserveCount && keptValue >= reserveValue)
					break;
				keep.Add(unit);
				keptValue += GetUnitValue(unit);
			}

			return units.Where(a => !keep.Contains(a)).OrderBy(a => a.ActorID).ToArray();
		}

		bool TryChooseConvoyAndShorePair(int sourceLandmassId, int targetLandmassId, Actor[] sourceUnits, CPos targetCell,
			int desiredCraftCount, bool emergencyDefend, out Actor[] crafts, out FransGroundShoreAccess sourceShore,
			out FransGroundShoreAccess targetShore, out FransRiskAssessment landingRisk, out string diagnostic)
		{
			using var fransPerf = FransBotLog.Profile(world, player, "GroundTransfer.ShoreSelect");
			crafts = Array.Empty<Actor>();
			sourceShore = default;
			targetShore = default;
			landingRisk = default;
			diagnostic = null;
			var sourceAccess = strategicMap.GetGroundShoreAccess(sourceLandmassId);
			var targetAccess = strategicMap.GetGroundShoreAccess(targetLandmassId);
			var commonRegions = sourceAccess.Select(access => access.NavalRegionId)
				.Intersect(targetAccess.Select(access => access.NavalRegionId))
				.OrderBy(region => region)
				.ToArray();
			if (sourceAccess.Count == 0)
			{
				diagnostic = $"result=NoSourceShoreAccess sourceShores=0 targetShores={targetAccess.Count} commonRegions=[] physical=[{LandingCraftInventoryDiagnostic()}]";
				return false;
			}
			if (targetAccess.Count == 0)
			{
				diagnostic = $"result=NoTargetShoreAccess sourceShores={sourceAccess.Count} targetShores=0 commonRegions=[] physical=[{LandingCraftInventoryDiagnostic()}]";
				return false;
			}

			var available = combatIntel.OwnedActors.Where(IsAvailableLandingCraft).OrderBy(a => a.ActorID).ToArray();
			if (available.Length == 0)
			{
				diagnostic = $"result=NoAvailablePhysicalLandingCraft sourceShores={sourceAccess.Count} targetShores={targetAccess.Count} commonRegions=[{string.Join(",", commonRegions)}] physical=[{LandingCraftInventoryDiagnostic()}]";
				return false;
			}

			var centroid = new CPos((int)sourceUnits.Average(a => a.Location.X), (int)sourceUnits.Average(a => a.Location.Y));
			var bestScore = long.MaxValue;
			var bestRegion = 0;
			var hasBestRegion = false;
			FransRiskAssessment bestRisk = default;
			var regionResolvedCrafts = 0;
			var commonRegionCrafts = 0;
			var consideredShorePairs = 0;
			var legalShorePairs = 0;
			var nativeRoutePairs = 0;
			var transportLossSafePairs = 0;
			var nonCriticalPairs = 0;
			var routeRejections = new HashSet<string>();
			foreach (var seed in available)
			{
				var mobile = seed.TraitOrDefault<Mobile>();
				if (mobile == null || !strategicMap.TryGetNavalRegionId(mobile.ToCell, out var regionId))
					continue;
				regionResolvedCrafts++;
				if (!commonRegions.Contains(regionId))
					continue;
				commonRegionCrafts++;

				// Both sides are bounded alternative sets. The old single-source-shore choice
				// could permanently reject a same-region convoy when only the nearest embark
				// cell was blocked even though a later source shore was executable.
				foreach (var source in sourceAccess.Where(a => a.NavalRegionId == regionId)
					.OrderBy(a => (a.GroundCell - centroid).LengthSquared)
					.ThenBy(a => a.NavalCell.X).ThenBy(a => a.NavalCell.Y).Take(8))
					foreach (var target in targetAccess.Where(a => a.NavalRegionId == regionId)
						.OrderBy(a => (a.GroundCell - targetCell).LengthSquared)
						.ThenBy(a => a.NavalCell.X).ThenBy(a => a.NavalCell.Y).Take(8))
					{
						if (source.GroundLandmassId == 0 || target.GroundLandmassId == 0)
							continue;
						consideredShorePairs++;
						if (!mobile.CanEnterCell(source.NavalCell, check: BlockedByActor.Immovable) || !mobile.CanStayInCell(source.NavalCell) ||
							!mobile.CanEnterCell(target.NavalCell, check: BlockedByActor.Immovable) || !mobile.CanStayInCell(target.NavalCell))
							continue;
						legalShorePairs++;
						if (!HasTransportLossSafeNavalRoute(seed, mobile, source.NavalCell, target.NavalCell,
							out var nativeRouteFound, out var routeRejection))
						{
							if (nativeRouteFound)
								nativeRoutePairs++;
							if (!string.IsNullOrEmpty(routeRejection))
								routeRejections.Add(routeRejection);
							continue;
						}
						nativeRoutePairs++;
						transportLossSafePairs++;

						var risk = riskModel.EvaluateStrategicCell(target.NavalCell, FransRiskRole.NavalTransport,
							emergencyDefend ? FransRiskTolerance.Balanced : FransRiskTolerance.Cautious);
						if (risk.IsCritical)
							continue;
						nonCriticalPairs++;
						var score = (long)(seed.Location - source.NavalCell).LengthSquared +
							(source.GroundCell - centroid).LengthSquared + (target.GroundCell - targetCell).LengthSquared +
							(long)risk.Score * 64;
						if (score >= bestScore)
							continue;
						bestScore = score;
						bestRegion = regionId;
						hasBestRegion = true;
						sourceShore = source;
						targetShore = target;
						bestRisk = risk;
					}
			}

			if (!hasBestRegion || sourceShore.GroundLandmassId == 0 || targetShore.GroundLandmassId == 0)
			{
				var rejection = commonRegions.Length == 0
					? "NoCommonNavalRegion"
					: regionResolvedCrafts == 0
						? "NoCraftNavalRegion"
						: commonRegionCrafts == 0
							? "NoUsableCraftInCommonNavalRegion"
							: consideredShorePairs == 0
								? "NoShorePairInCraftRegion"
								: legalShorePairs == 0
									? "NoLegalShoreCells"
									: nativeRoutePairs == 0
										? "NoNativeRoute"
										: transportLossSafePairs == 0
											? "TransportLossExclusion"
											: nonCriticalPairs == 0 ? "CriticalLandingRisk" : "NoSelectableShorePair";
				diagnostic = $"result={rejection} sourceShores={sourceAccess.Count} targetShores={targetAccess.Count}" +
					$" commonRegions=[{string.Join(",", commonRegions)}] available=[{ActorIds(available)}]" +
					$" regionResolvedCrafts={regionResolvedCrafts} commonRegionCrafts={commonRegionCrafts}" +
					$" consideredPairs={consideredShorePairs} legalPairs={legalShorePairs} nativeRoutePairs={nativeRoutePairs}" +
					$" transportLossSafePairs={transportLossSafePairs} nonCriticalPairs={nonCriticalPairs}" +
					$" routeRejections=[{string.Join(";", routeRejections.OrderBy(reason => reason))}] physical=[{LandingCraftInventoryDiagnostic()}]";
				return false;
			}

			var selectedSourceNavalCell = sourceShore.NavalCell;
			crafts = available.Where(a =>
			{
				var mobile = a.TraitOrDefault<Mobile>();
				return mobile != null && strategicMap.TryGetNavalRegionId(mobile.ToCell, out var region) && region == bestRegion;
			})
			.OrderBy(a => (a.Location - selectedSourceNavalCell).LengthSquared)
			.ThenBy(a => a.ActorID)
			.Take(Math.Min(Info.MaximumConvoyLandingCraft, desiredCraftCount))
			.ToArray();
			landingRisk = bestRisk;
			diagnostic = $"result=Selected region={bestRegion} sourceShores={sourceAccess.Count} targetShores={targetAccess.Count}" +
				$" commonRegions=[{string.Join(",", commonRegions)}] consideredPairs={consideredShorePairs}" +
				$" legalPairs={legalShorePairs} nativeRoutePairs={nativeRoutePairs} transportLossSafePairs={transportLossSafePairs}" +
				$" nonCriticalPairs={nonCriticalPairs} routeRejections=[{string.Join(";", routeRejections.OrderBy(reason => reason))}]" +
				$" source={sourceShore.GroundCell}/{sourceShore.NavalCell} target={targetShore.GroundCell}/{targetShore.NavalCell}" +
				$" selectedCrafts=[{ActorIds(crafts)}] physical=[{LandingCraftInventoryDiagnostic()}]";
			return true;
		}

		bool HasTransportLossSafeNavalRoute(Actor craft, Mobile mobile, CPos source, CPos destination) =>
			HasTransportLossSafeNavalRoute(craft, mobile, source, destination, out _, out _);

		bool HasTransportLossSafeNavalRoute(Actor craft, Mobile mobile, CPos source, CPos destination,
			out bool nativeRouteFound, out string rejection)
		{
			nativeRouteFound = false;
			rejection = null;
			if (craft == null || mobile == null || mobile.PathFinder is not PathFinder pathFinder)
			{
				rejection = "NativePathFinderUnavailable";
				return false;
			}

			int NoExtraCost(CPos cell) => 0;
			var path = pathFinder.FindPathToTargetCell(craft, [source], destination,
				BlockedByActor.Immovable, NoExtraCost, laneBias: false);
			if (path == null || path.Count == 0)
			{
				rejection = $"NoNativeRoute:{source}->{destination}";
				return false;
			}

			nativeRouteFound = true;
			if (general.IsTransportLossRouteAllowed(path))
				return true;

			rejection = general.TryGetTransportLossRouteBlocker(path, out var blocker)
				? $"TransportLossExclusion:incident={blocker.IncidentId},latestLossCell={blocker.LatestLossCell}," +
					$"blockingRouteCell={blocker.BlockingRouteCell},state={blocker.LifecycleState},owner={blocker.Owner}"
				: $"TransportLossExclusion:incident=Unresolved,route={source}->{destination}";
			return false;
		}

		bool TryBuildUnitCraftAssignments(Actor[] candidates, CPos embarkGroundCell, Actor[] crafts,
			out Actor[] selected, out Dictionary<Actor, Actor> assignments)
		{
			assignments = [];
			var usedWeight = crafts.ToDictionary(c => c, _ => 0);
			var cargoInfo = crafts.ToDictionary(c => c, c => c.Info.TraitInfoOrDefault<CargoInfo>());
			var assignedCount = crafts.ToDictionary(c => c, _ => 0);
			foreach (var unit in candidates.OrderBy(a => (a.Location - embarkGroundCell).LengthSquared).ThenBy(a => a.ActorID))
			{
				var passenger = unit.Info.TraitInfoOrDefault<PassengerInfo>();
				if (passenger == null)
					continue;
				var craft = crafts
					.Where(c => cargoInfo[c] != null && cargoInfo[c].Types.Contains(passenger.CargoType) &&
						usedWeight[c] + passenger.Weight <= cargoInfo[c].MaxWeight)
					.OrderBy(c => assignedCount[c])
					.ThenBy(c => usedWeight[c])
					.ThenBy(c => c.ActorID)
					.FirstOrDefault();
				if (craft == null)
					continue;
				assignments[unit] = craft;
				usedWeight[craft] += passenger.Weight;
				assignedCount[craft]++;
			}
			selected = assignments.Keys.OrderBy(a => a.ActorID).ToArray();
			return selected.Length > 0;
		}

		bool TryAssignNavalSlots(IEnumerable<Actor> actors, CPos center, int navalRegionId, int radius,
			out Dictionary<Actor, CPos> assigned, IEnumerable<CPos> extraUsed = null)
		{
			assigned = [];
			var used = extraUsed == null ? new HashSet<CPos>() : extraUsed.ToHashSet();
			foreach (var actor in actors.OrderBy(a => a.ActorID))
			{
				var mobile = actor.TraitOrDefault<Mobile>();
				if (mobile == null)
					return false;
				var slot = new[] { center }
					.Concat(world.Map.FindTilesInAnnulus(center, 1, radius))
					.Where(world.Map.Contains)
					.Where(c => !used.Contains(c))
					.Where(c => strategicMap.TryGetNavalRegionId(c, out var region) && region == navalRegionId)
					.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
					.OrderBy(c => (c - center).LengthSquared).ThenBy(c => c.X).ThenBy(c => c.Y)
					.Select(c => (CPos?)c).FirstOrDefault();
				if (!slot.HasValue)
					return false;
				assigned[actor] = slot.Value;
				used.Add(slot.Value);
			}
			return true;
		}

		bool IsAvailableLandingCraft(Actor actor)
		{
			// Strategic MCV demand arbitrates new LST production in EnsureLandingCraftCapacity.
			// Physical ownership is actor-specific: canonical Transport reservations and the
			// exact expansion-pending predicate below decide whether this craft may be used.
			return LandingCraftAvailabilityReason(actor) == "Available";
		}

		string LandingCraftAvailabilityReason(Actor actor)
		{
			if (actor == null)
				return "MissingActor";
			if (actor.Disposed)
				return "Disposed";
			if (!actor.IsInWorld)
				return "NotInWorld";
			if (actor.IsDead)
				return "Dead";
			if (actor.Owner != player)
				return "WrongOwner";
			if (!actor.IsIdle)
				return $"NonIdle({actor.CurrentActivity?.GetType().Name ?? "None"})";
			if (!Info.LandingCraftTypes.Contains(actor.Info.Name))
				return "WrongType";
			if (transportService.IsTransportReserved(actor))
				return "TransportReserved";
			if (amphibiousExpansion?.IsLandingCraftPendingForExpansion(actor) ?? false)
				return "McvExactPending";

			var cargo = actor.TraitOrDefault<Cargo>();
			var mobile = actor.TraitOrDefault<Mobile>();
			if (cargo == null)
				return "MissingCargo";
			if (cargo.IsTraitDisabled)
				return "CargoDisabled";
			if (!cargo.IsEmpty())
				return $"CargoNotEmpty({cargo.Passengers.Count()})";
			if (mobile == null)
				return "MissingMobile";
			if (mobile.IsTraitDisabled)
				return "MobileDisabled";
			if (mobile.IsTraitPaused)
				return "MobilePaused";
			return "Available";
		}

		string LandingCraftInventoryDiagnostic()
		{
			var crafts = combatIntel.OwnedActors
				.Where(actor => actor != null && Info.LandingCraftTypes.Contains(actor.Info.Name))
				.OrderBy(actor => actor.ActorID)
				.Select(actor =>
				{
					var mobile = actor.TraitOrDefault<Mobile>();
					var region = mobile != null && strategicMap.TryGetNavalRegionId(mobile.ToCell, out var navalRegion)
						? navalRegion.ToString()
						: "Unknown";
					var cargo = actor.TraitOrDefault<Cargo>();
					var cargoState = cargo == null
						? "Missing"
						: cargo.IsTraitDisabled
							? "Disabled"
							: $"Count{cargo.Passengers.Count()}";
					return $"{actor.ActorID}/{actor.Info.Name}:cell={actor.Location},region={region},idle={actor.IsIdle}," +
						$"activity={actor.CurrentActivity?.GetType().Name ?? "None"},cargo={cargoState}," +
						$"transportReserved={transportService.IsTransportReserved(actor)}," +
						$"mcvPending={(amphibiousExpansion?.IsLandingCraftPendingForExpansion(actor) ?? false)}," +
						$"availability={LandingCraftAvailabilityReason(actor)}";
				})
				.ToArray();
			return crafts.Length == 0 ? "none" : string.Join(";", crafts);
		}

		void AssignGroundSlots(TransferWave wave, bool sourceSide)
		{
			var center = sourceSide ? wave.SourceShore.GroundCell : wave.TargetShore.GroundCell;
			var landmassId = sourceSide ? wave.SourceLandmassId : wave.TargetLandmassId;
			var assigned = sourceSide ? wave.SourceUnitSlots : wave.TargetUnitSlots;
			var used = new HashSet<CPos>();
			foreach (var unit in wave.Units.OrderBy(a => a.ActorID))
			{
				var mobile = unit.TraitOrDefault<Mobile>();
				IEnumerable<CPos> candidates = sourceSide
					? new[] { center }.Concat(world.Map.FindTilesInAnnulus(center, 1, Info.StagingSlotRadius))
					: world.Map.FindTilesInAnnulus(center, Info.BeachClearDistance, Info.BeachClearDistance + Info.StagingSlotRadius);
				var slot = candidates
					.Where(world.Map.Contains)
					.Where(c => !used.Contains(c))
					.Where(c => strategicMap.TryGetGroundLandmassId(c, out var lm) && lm == landmassId)
					.Where(c => mobile != null && mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
					.OrderBy(c => sourceSide ? (c - center).LengthSquared : (c - wave.TargetCell).LengthSquared)
					.ThenBy(c => c.X).ThenBy(c => c.Y)
					.Select(c => (CPos?)c).FirstOrDefault();

				// Extremely cramped handoffs may not expose an inland slot. Fall back to the old
				// close staging ring rather than rejecting an otherwise valid convoy.
				if (!slot.HasValue && !sourceSide)
					slot = new[] { center }.Concat(world.Map.FindTilesInAnnulus(center, 1, Info.StagingSlotRadius))
						.Where(world.Map.Contains)
						.Where(c => !used.Contains(c))
						.Where(c => strategicMap.TryGetGroundLandmassId(c, out var lm) && lm == landmassId)
						.Where(c => mobile != null && mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
						.OrderBy(c => (c - center).LengthSquared).ThenBy(c => c.X).ThenBy(c => c.Y)
						.Select(c => (CPos?)c).FirstOrDefault();

				var chosen = slot ?? center;
				assigned[unit] = chosen;
				used.Add(chosen);
			}
		}

		void ManageWave(IBot bot)
		{
			if (!RefreshCraftLosses(bot))
				return;

			var survivors = activeWave.Units.Where(IsSurvivingPassenger).ToArray();
			if (survivors.Length == 0)
			{
				ReleaseWave(cancelActivities: false, "all wave units were lost");
				return;
			}

			switch (activeWave.State)
			{
				case TransferState.Assemble:
					ManageAssemble(bot, survivors);
					break;
				case TransferState.Boarding:
					ManageBoarding(bot, survivors);
					break;
				case TransferState.Crossing:
					ManageCrossing(bot, survivors);
					break;
				case TransferState.Returning:
					ManageReturning(bot, survivors);
					break;
				case TransferState.Unloading:
					ManageUnloading(bot, survivors);
					break;
				case TransferState.Regroup:
					ManageRegroup(bot, survivors);
					break;
			}
		}

		bool RefreshCraftLosses(IBot bot)
		{
			var wave = activeWave;
			var lost = wave.Crafts.Where(a => a == null || a.Disposed || !a.IsInWorld || a.IsDead).ToArray();
			if (lost.Length == 0)
				return true;

			if (wave.State == TransferState.Assemble || wave.State == TransferState.Boarding)
			{
				ReleaseWave(cancelActivities: true, $"{lost.Length} LST(s) lost before convoy departure");
				return false;
			}

			foreach (var craft in lost)
			{
				wave.Crafts.Remove(craft);
				wave.SourceCraftSlots.Remove(craft);
				wave.TargetCraftSlots.Remove(craft);
				wave.UnloadIssued.Remove(craft);
				wave.LastCraftCargoCount.Remove(craft);
				wave.LastCraftUnloadProgressTick.Remove(craft);
				wave.CraftUnloadRecoveryAttempts.Remove(craft);
				wave.CraftUnloadRecoveryCell.Remove(craft);
				wave.CrossingLastProgressCell.Remove(craft);
				wave.CrossingLastProgressTick.Remove(craft);
				wave.CrossingSameLegRetryCount.Remove(craft);
				wave.CrossingRecoveryAttempts.Remove(craft);
				wave.ReturnUnloadIssued.Remove(craft);
				wave.ReturnLastCargoCount.Remove(craft);
				wave.ReturnLastCargoProgressTick.Remove(craft);
				if (!wave.TransportsReleased && craft != null)
					transportService.ReleaseExternalTransport(craft, reservationOwner);
			}

			foreach (var unit in wave.Units.ToArray())
				if (wave.UnitCraft.TryGetValue(unit, out var craft) && lost.Contains(craft) && unit.IsInWorld && !unit.IsDead)
				{
					wave.Units.Remove(unit);
					wave.UnitCraft.Remove(unit);
					reservedGroundUnits.Remove(unit);
				}

			if (wave.Crafts.Count == 0)
			{
				ReleaseWave(cancelActivities: false, "all convoy LSTs were lost");
				return false;
			}

			// A destroyed sister craft may have created a fresh LST-loss SECURE in this same tick.
			// Re-evaluate every surviving physical LST immediately instead of waiting for the next
			// periodic crossing revision check. If the new incident blocks the remaining leg, the
			// convoy retreats as one unit and does not feed the second/third craft into the same kill zone.
			wave.TransportLossExclusionRevision = general.TransportLossExclusionRevision;
			if (wave.State == TransferState.Crossing)
				foreach (var craft in wave.Crafts.Where(IsLiveActor).OrderBy(a => a.ActorID))
				{
					if (!wave.TargetCraftSlots.TryGetValue(craft, out var targetSlot))
						continue;
					var mobile = craft.TraitOrDefault<Mobile>();
					if (mobile != null && !HasTransportLossSafeNavalRoute(craft, mobile, craft.Location, targetSlot))
					{
						FransBotLog.BotDebug(world,
							"{0}: GROUND TRANSFER sister-LST safety reacts immediately after {1} convoy loss(es): surviving craft {2} now crosses the fresh LST-loss SECURE, so the convoy returns instead of continuing into the same incident.",
							player, lost.Length, craft.ActorID);
						BeginConvoyReturn(bot, craft.ActorID,
							"sister LST loss created or refreshed a blocking transport-loss exclusion");
						return true;
					}
				}

			FransBotLog.BotDebug(world,
				"{0}: GROUND TRANSFER convoy lost {1} LST(s) after departure; {2} craft remain and continue the fixed crossing/landing with surviving cargo after immediate loss-zone revalidation.",
				player, lost.Length, wave.Crafts.Count);
			return true;
		}

		void ManageAssemble(IBot bot, Actor[] survivors)
		{
			var wave = activeWave;
			var radiusSq = Info.BoardingAssemblyRadius * Info.BoardingAssemblyRadius;
			var assembled = survivors.Count(a => a.IsInWorld && wave.SourceUnitSlots.TryGetValue(a, out var slot) && (a.Location - slot).LengthSquared <= radiusSq);
			var craftReadyRadiusSq = Info.LandingCraftBoardingReadyRadius * Info.LandingCraftBoardingReadyRadius;
			var readyCrafts = wave.Crafts.Count(c => wave.SourceCraftSlots.TryGetValue(c, out var slot) &&
				(c.Location - slot).LengthSquared <= craftReadyRadiusSq);
			var craftReady = readyCrafts > 0;
			var metric = CraftMetric(wave.Crafts, wave.SourceCraftSlots);
			if (metric < wave.LastMovementMetric || assembled != wave.LastAssembledCount)
			{
				wave.LastMovementMetric = metric;
				wave.LastAssembledCount = assembled;
				wave.LastProgressTick = world.WorldTick;
				wave.StallRetries = 0;
			}

			// do not wait for every ground unit or LST to stand on a perfect staging slot.
			// Once the naval side is ready, switch to streaming BOARDING: ready passengers enter
			// immediately while stragglers keep moving toward their own slots.
			if (craftReady)
			{
				wave.State = TransferState.Boarding;
				wave.StateStartedTick = world.WorldTick;
				wave.LastProgressTick = world.WorldTick;
				wave.LastLoadedCount = -1;
				wave.LastBoardingReservedCount = -1;
				wave.LastMovementMetric = BoardingMetric(wave, survivors);
				wave.StallRetries = 0;
				wave.NextBoardingRetryTick = 0;
				IssueBoardingOrders(bot, survivors);
				LogWaveTransition(wave, TransferState.Assemble, TransferState.Boarding,
					"first compatible LST entered the boarding-ready radius");
				FransBotLog.BotDebug(world,
					"{0}: GROUND TRANSFER dynamic BOARDING begins as soon as {1}/{2} LST(s) are inside the boarding-ready radius; {3}/{4} passengers are already near staging. Remaining LSTs and passengers may keep approaching while ready Cargo starts loading.",
					player, readyCrafts, wave.Crafts.Count, assembled, survivors.Length);
				return;
			}

			if (world.WorldTick - wave.LastProgressTick >= Info.StallTimeout)
			{
				wave.StallRetries++;
				if (wave.StallRetries > Info.MaximumPreBoardingStallRetries)
				{
					ReleaseWave(cancelActivities: true, "ASSEMBLE naval staging stalled before streaming boarding");
					return;
				}
				wave.LastProgressTick = world.WorldTick;
				IssueAssembleOrders(bot, wave, force: true);
			}
		}

		void IssueAssembleOrders(IBot bot, TransferWave wave, bool force)
		{
			foreach (var craft in wave.Crafts.Where(IsLiveActor).OrderBy(a => a.ActorID))
				if (wave.SourceCraftSlots.TryGetValue(craft, out var slot) && (craft.Location - slot).LengthSquared > 1 && (force || craft.IsIdle))
					bot.QueueOrder(new Order("Move", craft, Target.FromCell(world, slot), false));


			foreach (var unit in wave.Units.Where(a => a != null && a.IsInWorld && !a.IsDead).OrderBy(a => a.ActorID))
			{
				if (!wave.SourceUnitSlots.TryGetValue(unit, out var slot) || (unit.Location - slot).LengthSquared <= 1)
					continue;
				if (force || unit.IsIdle)
					bot.QueueOrder(new Order("Move", unit, Target.FromCell(world, slot), false));
			}
		}

		void ManageBoarding(IBot bot, Actor[] survivors)
		{
			var wave = activeWave;
			foreach (var loadedUnit in survivors.Where(IsLoadedIntoAssignedCraft))
				ClearBoardingTracking(wave, loadedUnit);

			var loaded = survivors.Count(IsLoadedIntoAssignedCraft);
			var reserved = survivors.Count(a =>
			{
				if (!a.IsInWorld || IsLoadedIntoAssignedCraft(a))
					return false;
				var passenger = a.TraitOrDefault<Passenger>();
				return passenger?.ReservedCargo != null;
			});
			var metric = BoardingMetric(wave, survivors);

			foreach (var unit in survivors.Where(a => a.IsInWorld && !IsLoadedIntoAssignedCraft(a)).OrderBy(a => a.ActorID))
			{
				var passenger = unit.TraitOrDefault<Passenger>();
				var hasNativeOwnership = passenger?.ReservedCargo != null || wave.BoardingOrderUntilTick.ContainsKey(unit);
				if (!hasNativeOwnership)
				{
					ClearBoardingTracking(wave, unit);
					continue;
				}

				if (!wave.BoardingLastProgressCell.TryGetValue(unit, out var lastCell))
				{
					wave.BoardingLastProgressCell[unit] = unit.Location;
					wave.BoardingLastProgressTick[unit] = world.WorldTick;
				}
				else if (lastCell != unit.Location)
				{
					wave.BoardingLastProgressCell[unit] = unit.Location;
					wave.BoardingLastProgressTick[unit] = world.WorldTick;
					wave.BoardingOrderUntilTick[unit] = world.WorldTick + Info.BoardingNativeTimeout;
					if (passenger?.ReservedCargo != null)
						wave.BoardingReservationSinceTick[unit] = world.WorldTick;
					wave.LastProgressTick = world.WorldTick;
				}

				if (passenger?.ReservedCargo != null && !wave.BoardingReservationSinceTick.ContainsKey(unit))
					wave.BoardingReservationSinceTick[unit] = world.WorldTick;

				var lastProgress = wave.BoardingLastProgressTick.TryGetValue(unit, out var progressTick) ? progressTick : world.WorldTick;
				if (world.WorldTick - lastProgress < Info.BoardingNativeTimeout)
					continue;

				// Native EnterTransport owns the passenger for as long as the actor is physically
				// progressing. Only a real no-cell-progress timeout may cancel that one attempt.
				QueueStopOrder(bot, unit);
				ClearBoardingTracking(wave, unit);
				TryRelocateBoardingSlot(wave, unit);
				wave.LastProgressTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					"{0}: GROUND TRANSFER passenger {1} made no native boarding cell progress for {2} WT; only that EnterTransport is cancelled, the passenger returns to the dynamic queue and may use another free LST.",
					player, unit.ActorID, Info.BoardingNativeTimeout);
			}

			if (loaded != wave.LastLoadedCount || reserved != wave.LastBoardingReservedCount || metric < wave.LastMovementMetric)
			{
				wave.LastLoadedCount = loaded;
				wave.LastBoardingReservedCount = reserved;
				wave.LastMovementMetric = metric;
				wave.LastProgressTick = world.WorldTick;
				wave.StallRetries = 0;
			}

			if (loaded == survivors.Length)
			{
				BeginCrossing(bot, survivors.Length);
				return;
			}

			var boardingDeadline = wave.MissionType == FransMissionType.Defend ? Info.DefendBoardingDeadline : Info.StrategicBoardingDeadline;
			if (world.WorldTick - wave.StateStartedTick >= boardingDeadline)
			{
				var requiredPercent = wave.MissionType == FransMissionType.Defend ? Info.DefendDepartureLoadedPercent : Info.StrategicDepartureLoadedPercent;
				if (loaded > 0 && loaded * 100 >= survivors.Length * requiredPercent)
				{
					ReleaseBoardingStragglersAndDepart(bot, survivors, loaded,
						$"hard boarding deadline {boardingDeadline} WT reached with {loaded}/{survivors.Length} loaded ({requiredPercent}% required)");
					return;
				}

				ReleaseWave(cancelActivities: true,
					$"boarding deadline {boardingDeadline} WT expired with only {loaded}/{survivors.Length} loaded (<{requiredPercent}%)");
				return;
			}

			if (world.WorldTick >= wave.NextBoardingRetryTick)
			{
				wave.NextBoardingRetryTick = world.WorldTick + Info.BoardingRetryInterval;
				IssueBoardingOrders(bot, survivors);
			}

			if (world.WorldTick - wave.LastProgressTick >= Info.StallTimeout)
			{
				wave.StallRetries++;
				wave.LastProgressTick = world.WorldTick;
				if (wave.StallRetries > Info.MaximumPreBoardingStallRetries)
				{
					var unboarded = survivors.Where(a => !IsLoadedIntoAssignedCraft(a)).ToArray();
					var nativeBoardingActive = unboarded.Any(unit =>
					{
						var passenger = unit.TraitOrDefault<Passenger>();
						return passenger?.ReservedCargo != null || wave.BoardingOrderUntilTick.ContainsKey(unit);
					});
					if (nativeBoardingActive)
					{
						// A moving native EnterTransport actor owns its activity until its own no-progress
						// watchdog or the hard convoy deadline fires.
						wave.StallRetries = 0;
						return;
					}
					if (loaded == 0)
					{
						ReleaseWave(cancelActivities: true, "BOARDING made no progress");
						return;
					}
					ReleaseBoardingStragglersAndDepart(bot, survivors, loaded, "streaming boarding stall budget exhausted");
					return;
				}
				IssueBoardingOrders(bot, survivors);
			}
		}

		void ClearBoardingTracking(TransferWave wave, Actor unit)
		{
			wave.BoardingReservationSinceTick.Remove(unit);
			wave.BoardingOrderUntilTick.Remove(unit);
			wave.BoardingLastProgressCell.Remove(unit);
			wave.BoardingLastProgressTick.Remove(unit);
		}

		void ReleaseBoardingStragglersAndDepart(IBot bot, Actor[] survivors, int loaded, string reason)
		{
			var wave = activeWave;
			var unboarded = survivors.Where(a => !IsLoadedIntoAssignedCraft(a)).ToArray();
			foreach (var unit in unboarded)
			{
				if (unit.IsInWorld)
					QueueStopOrder(bot, unit);
				wave.Units.Remove(unit);
				wave.UnitCraft.Remove(unit);
				ClearBoardingTracking(wave, unit);
				reservedGroundUnits.Remove(unit);
			}
			FransBotLog.BotDebug(world,
				"{0}: GROUND TRANSFER BOUNDED DEPARTURE launches {1} loaded passenger(s) and releases {2} straggler(s): {3}. A useful convoy leaves instead of waiting indefinitely for a perfect manifest.",
				player, loaded, unboarded.Length, reason);
			BeginCrossing(bot, loaded);
		}

		long BoardingMetric(TransferWave wave, IEnumerable<Actor> survivors)
		{
			long metric = 0;
			foreach (var unit in survivors)
			{
				if (!unit.IsInWorld || IsLoadedIntoAssignedCraft(unit))
					continue;
				var passenger = unit.TraitOrDefault<Passenger>();
				if (passenger?.ReservedCargo != null)
					continue;
				metric += (unit.Location - wave.SourceShore.GroundCell).LengthSquared;
			}
			return metric;
		}

		void IssueBoardingOrders(IBot bot, IEnumerable<Actor> survivors)
		{
			var wave = activeWave;
			var zoneRadiusSq = Info.BoardingZoneRadius * Info.BoardingZoneRadius;
			var craftReadyRadiusSq = Info.LandingCraftBoardingReadyRadius * Info.LandingCraftBoardingReadyRadius;

			// LSTs that were still approaching when the first craft opened the boarding phase keep
			// joining independently. If native Move ended short, reissue only that same cached slot.
			foreach (var approachingCraft in wave.Crafts.Where(IsLiveActor).OrderBy(a => a.ActorID))
				if (wave.SourceCraftSlots.TryGetValue(approachingCraft, out var approachSlot) &&
					(approachingCraft.Location - approachSlot).LengthSquared > craftReadyRadiusSq && approachingCraft.IsIdle)
					bot.QueueOrder(new Order("Move", approachingCraft, Target.FromCell(world, approachSlot), false));

			// Native Cargo is serial per LST, but assignment is now dynamic. A craft is busy only
			// while one current passenger owns/has just received EnterTransport for it.
			var busyCrafts = survivors
				.Where(a => a.IsInWorld && !IsLoadedIntoAssignedCraft(a) &&
					(a.TraitOrDefault<Passenger>()?.ReservedCargo != null ||
					(wave.BoardingOrderUntilTick.TryGetValue(a, out var until) && world.WorldTick < until)))
				.Select(a => wave.UnitCraft.TryGetValue(a, out var c) ? c : null)
				.Where(IsLiveActor)
				.ToHashSet();

			var readyCrafts = wave.Crafts
				.Where(IsLiveActor)
				.Where(c => wave.SourceCraftSlots.TryGetValue(c, out var slot) &&
					(c.Location - slot).LengthSquared <= craftReadyRadiusSq)
				.OrderBy(c => c.ActorID)
				.ToArray();

			if (readyCrafts.Length == 0)
				return;

			foreach (var unit in survivors.Where(a => a != null && a.IsInWorld && !a.IsDead).OrderBy(a => a.ActorID))
			{
				if (IsLoadedIntoAssignedCraft(unit))
					continue;
				var passenger = unit.TraitOrDefault<Passenger>();
				if (passenger == null || passenger.ReservedCargo != null)
					continue;

				// Outside the broad embark zone, keep ordinary ground movement simple and loose.
				// Exact per-unit staging slots are only a traffic aid, never a prerequisite to board.
				if ((unit.Location - wave.SourceShore.GroundCell).LengthSquared > zoneRadiusSq)
				{
					if (wave.SourceUnitSlots.TryGetValue(unit, out var slot) && unit.IsIdle)
						bot.QueueOrder(new Order("Move", unit, Target.FromCell(world, slot), false));
					continue;
				}

				var passengerInfo = unit.Info.TraitInfoOrDefault<PassengerInfo>();
				if (passengerInfo == null)
					continue;

				var craft = readyCrafts
					.Where(c => !busyCrafts.Contains(c))
					.Where(c =>
					{
						var cargo = c.TraitOrDefault<Cargo>();
						var info = c.Info.TraitInfoOrDefault<CargoInfo>();
						return cargo != null && !cargo.IsTraitDisabled && info != null &&
							info.Types.Contains(passengerInfo.CargoType) && cargo.HasSpace(passengerInfo.Weight);
					})
					.OrderBy(c => c.TraitOrDefault<Cargo>()?.PassengerCount ?? int.MaxValue)
					.ThenBy(c => (c.Location - unit.Location).LengthSquared)
					.ThenBy(c => c.ActorID)
					.FirstOrDefault();
				if (craft == null)
					continue;

				// Rebind the load-balancing preference to the craft that can actually accept this
				// passenger now. Once EnterTransport starts, native Cargo owns the final approach.
				wave.UnitCraft[unit] = craft;
				if (!unit.IsIdle)
					QueueStopOrder(bot, unit);
				bot.QueueOrder(new Order("EnterTransport", unit, Target.FromActor(craft), false));
				wave.BoardingOrderUntilTick[unit] = world.WorldTick + Info.BoardingNativeTimeout;
				wave.BoardingLastProgressCell[unit] = unit.Location;
				wave.BoardingLastProgressTick[unit] = world.WorldTick;
				busyCrafts.Add(craft);
			}
		}

		void TryRelocateBoardingSlot(TransferWave wave, Actor unit)
		{
			var mobile = unit?.TraitOrDefault<Mobile>();
			if (mobile == null)
				return;
			var used = wave.SourceUnitSlots.Where(kv => kv.Key != unit).Select(kv => kv.Value).ToHashSet();
			var center = wave.SourceShore.GroundCell;
			var slot = world.Map.FindTilesInAnnulus(center, 1, Info.StagingSlotRadius + 2)
				.Where(world.Map.Contains)
				.Where(c => !used.Contains(c))
				.Where(c => strategicMap.TryGetGroundLandmassId(c, out var lm) && lm == wave.SourceLandmassId)
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.OrderBy(c => (c - unit.Location).LengthSquared)
				.ThenBy(c => (c - center).LengthSquared).ThenBy(c => c.X).ThenBy(c => c.Y)
				.Select(c => (CPos?)c).FirstOrDefault();
			if (slot.HasValue)
				wave.SourceUnitSlots[unit] = slot.Value;
		}

		void BeginCrossing(IBot bot, int loadedCount)
		{
			var wave = activeWave;
			wave.State = TransferState.Crossing;
			wave.StateStartedTick = world.WorldTick;
			wave.LastProgressTick = world.WorldTick;
			wave.LastMovementMetric = CraftMetric(wave.Crafts, wave.TargetCraftSlots);
			wave.StallRetries = 0;
			ResetCrossingProgress(wave);
			IssueCrossingOrders(bot, force: true);
			LogWaveTransition(wave, TransferState.Boarding, TransferState.Crossing,
				$"convoy departed with {loadedCount} loaded passenger(s)");
			FransBotLog.BotDebug(world,
				"{0}: GROUND TRANSFER convoy fully/partially boarded ({1} passenger(s)); {2} LST(s) cross toward cached landing slots around {3}. uses bounded recovery: same leg -> local landing alternatives -> retreat to embark shore, never indefinite crossing stall.",
				player, loadedCount, wave.Crafts.Count, wave.TargetShore.NavalCell);
		}

		void ResetCrossingProgress(TransferWave wave)
		{
			wave.CrossingLastProgressCell.Clear();
			wave.CrossingLastProgressTick.Clear();
			wave.CrossingSameLegRetryCount.Clear();
			wave.CrossingRecoveryAttempts.Clear();
			foreach (var craft in wave.Crafts.Where(IsLiveActor))
			{
				wave.CrossingLastProgressCell[craft] = craft.Location;
				wave.CrossingLastProgressTick[craft] = world.WorldTick;
				wave.CrossingSameLegRetryCount[craft] = 0;
				wave.CrossingRecoveryAttempts[craft] = 0;
			}
		}

		void IssueCrossingOrders(IBot bot, bool force)
		{
			var wave = activeWave;
			foreach (var craft in wave.Crafts.Where(IsLiveActor).OrderBy(a => a.ActorID))
				if (wave.TargetCraftSlots.TryGetValue(craft, out var slot) && (force || craft.IsIdle))
					bot.QueueOrder(new Order("Move", craft, Target.FromCell(world, slot), false));
		}

		void ManageCrossing(IBot bot, Actor[] survivors)
		{
			var wave = activeWave;
			if (wave.TransportLossExclusionRevision != general.TransportLossExclusionRevision)
			{
				wave.TransportLossExclusionRevision = general.TransportLossExclusionRevision;
				foreach (var craft in wave.Crafts.Where(IsLiveActor).OrderBy(a => a.ActorID))
				{
					if (!wave.TargetCraftSlots.TryGetValue(craft, out var targetSlot))
						continue;
					var mobile = craft.TraitOrDefault<Mobile>();
					if (mobile != null && !HasTransportLossSafeNavalRoute(craft, mobile, craft.Location, targetSlot))
					{
						FransBotLog.BotDebug(world,
							"{0}: GROUND TRANSFER aborts active crossing because a new LST-loss SECURE now blocks the cached sea leg for craft {1}; convoy returns toward embark instead of feeding more transports through the unresolved incident.",
							player, craft.ActorID);
						BeginConvoyReturn(bot, craft.ActorID,
							"transport-loss exclusion revision blocked the cached crossing leg");
						return;
					}
				}
			}
			foreach (var craft in wave.Crafts.Where(IsLiveActor).OrderBy(a => a.ActorID))
			{
				if (!wave.TargetCraftSlots.TryGetValue(craft, out var slot))
					continue;
				if ((craft.Location - slot).LengthSquared <= 1)
				{
					wave.CrossingLastProgressCell[craft] = craft.Location;
					wave.CrossingLastProgressTick[craft] = world.WorldTick;
					continue;
				}

				if (!wave.CrossingLastProgressCell.TryGetValue(craft, out var lastCell) || craft.Location != lastCell)
				{
					wave.CrossingLastProgressCell[craft] = craft.Location;
					wave.CrossingLastProgressTick[craft] = world.WorldTick;
					wave.CrossingSameLegRetryCount[craft] = 0;
					continue;
				}

				if (!wave.CrossingLastProgressTick.TryGetValue(craft, out var progressTick))
				{
					wave.CrossingLastProgressTick[craft] = world.WorldTick;
					continue;
				}
				if (world.WorldTick - progressTick < Info.StallTimeout)
					continue;

				var sameRetries = wave.CrossingSameLegRetryCount.TryGetValue(craft, out var retry) ? retry : 0;
				if (sameRetries < Info.CrossingSameLegRetries)
				{
					wave.CrossingSameLegRetryCount[craft] = sameRetries + 1;
					wave.CrossingLastProgressTick[craft] = world.WorldTick;
					QueueStopOrder(bot, craft);
					bot.QueueOrder(new Order("Move", craft, Target.FromCell(world, slot), false));
					FransBotLog.BotDebug(world,
						"{0}: GROUND TRANSFER LST {1} crossing stalled; cached-leg retry {2}/{3} toward {4}.",
						player, craft.ActorID, sameRetries + 1, Info.CrossingSameLegRetries, slot);
					continue;
				}

				var recoveryAttempt = wave.CrossingRecoveryAttempts.TryGetValue(craft, out var attempt) ? attempt : 0;
				if (recoveryAttempt < Info.MaximumCrossingRecoveryAttempts && TryFindCrossingRecoveryCell(craft, false, recoveryAttempt, out var alternate))
				{
					wave.CrossingRecoveryAttempts[craft] = recoveryAttempt + 1;
					wave.CrossingSameLegRetryCount[craft] = 0;
					wave.TargetCraftSlots[craft] = alternate;
					wave.CrossingLastProgressCell[craft] = craft.Location;
					wave.CrossingLastProgressTick[craft] = world.WorldTick;
					QueueStopOrder(bot, craft);
					bot.QueueOrder(new Order("Move", craft, Target.FromCell(world, alternate), false));
					FransBotLog.BotDebug(world,
						"{0}: GROUND TRANSFER LST {1} switches to bounded local landing recovery {2}/{3} at {4}. At most {5} cells are considered; no full shoreline replan.",
						player, craft.ActorID, recoveryAttempt + 1, Info.MaximumCrossingRecoveryAttempts, alternate, Info.CrossingRecoveryCandidateLimit);
					continue;
				}

				BeginConvoyReturn(bot, craft.ActorID, "destination crossing recovery exhausted");
				return;
			}

			var arrived = wave.Crafts.All(c => wave.TargetCraftSlots.TryGetValue(c, out var target) && (c.Location - target).LengthSquared <= 1);
			if (!arrived)
				return;

			wave.State = TransferState.Unloading;
			wave.StateStartedTick = world.WorldTick;
			wave.LastProgressTick = world.WorldTick;
			wave.NextUnloadRetryTick = world.WorldTick + Info.UnloadRetryInterval;
			LogWaveTransition(wave, TransferState.Crossing, TransferState.Unloading,
				"all surviving LSTs reached their cached destination slots");
			BeginUnload(bot);
		}

		bool TryFindCrossingRecoveryCell(Actor craft, bool sourceSide, int attempt, out CPos cell)
		{
			cell = default;
			var wave = activeWave;
			var mobile = craft?.TraitOrDefault<Mobile>();
			if (wave == null || mobile == null)
				return false;
			var shore = sourceSide ? wave.SourceShore : wave.TargetShore;
			var slots = sourceSide ? wave.SourceCraftSlots : wave.TargetCraftSlots;
			if (!strategicMap.TryGetNavalRegionId(shore.NavalCell, out var regionId))
				return false;

			var used = slots.Where(kv => kv.Key != craft).Select(kv => kv.Value).ToHashSet();
			var candidates = world.Map.FindTilesInAnnulus(shore.NavalCell, 1, Info.CrossingRecoveryRadius)
				.Where(world.Map.Contains)
				.Where(c => !used.Contains(c) && c != craft.Location)
				.Where(c => strategicMap.TryGetNavalRegionId(c, out var region) && region == regionId)
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.Where(c => !riskModel.EvaluateCell(craft, c, FransRiskRole.NavalTransport, FransRiskTolerance.Balanced).IsCritical)
				.OrderBy(c => (c - shore.GroundCell).LengthSquared)
				.ThenBy(c => (c - craft.Location).LengthSquared)
				.ThenBy(c => c.X).ThenBy(c => c.Y)
				.Take(Info.CrossingRecoveryCandidateLimit)
				.ToArray();
			if (candidates.Length == 0)
				return false;

			cell = candidates[Math.Min(attempt, candidates.Length - 1)];
			return true;
		}

		void BeginConvoyReturn(IBot bot, uint stalledCraftId, string reason)
		{
			var wave = activeWave;
			var previousState = wave.State;
			var stalledCraft = wave.Crafts.FirstOrDefault(c => c != null && c.ActorID == stalledCraftId);
			var sameLegRetries = stalledCraft != null && wave.CrossingSameLegRetryCount.TryGetValue(stalledCraft, out var retries) ? retries : 0;
			var recoveryAttempts = stalledCraft != null && wave.CrossingRecoveryAttempts.TryGetValue(stalledCraft, out var attempts) ? attempts : 0;
			var seaLeaseBefore = wave.SeaSupportRequestId;
			wave.State = TransferState.Returning;
			wave.StateStartedTick = world.WorldTick;
			wave.LastProgressTick = world.WorldTick;
			wave.ReturnUnloadIssued.Clear();
			wave.ReturnLastCargoCount.Clear();
			wave.ReturnLastCargoProgressTick.Clear();
			wave.ReturnDiagnosticTarget.Clear();
			wave.ReturnBestDistanceSquared.Clear();
			wave.ReturnLastDistanceProgressTick.Clear();
			wave.ReturnUnloadLastRealProgressTick.Clear();
			wave.ReturnUnloadNextDiagnosticTick.Clear();
			wave.ReturnUnloadPhaseLogged = false;
			if (wave.SeaSupportRequestId != 0)
			{
				general.ReleaseSeaTransportBeachSecure(wave.SeaSupportRequestId);
				wave.SeaSupportRequestId = 0;
			}
			ResetCrossingProgress(wave);
			foreach (var craft in wave.Crafts.Where(IsLiveActor).OrderBy(a => a.ActorID))
				if (wave.SourceCraftSlots.TryGetValue(craft, out var slot))
				{
					RebaseReturnDiagnostic(wave, craft, slot);
					QueueStopOrder(bot, craft);
					bot.QueueOrder(new Order("Move", craft, Target.FromCell(world, slot), false));
				}
			FransBotLog.BotDebug(world,
				"{0}: {1} wave={2} transition={3}->Returning reason={4} triggerCraft={5} sameLegRetries={6}/{7} alternateAttempts={8}/{9} returnTargets=[{10}] groundActors=[{11}] crafts=[{12}] seaLeaseBefore={13} seaLeaseHeld=False {14}; native Moves queued for the exact surviving convoy.",
				player, LivenessDiagnosticPrefix, WaveDiagnosticId(wave), previousState, reason, stalledCraftId,
				sameLegRetries, Info.CrossingSameLegRetries, recoveryAttempts, Info.MaximumCrossingRecoveryAttempts,
				CraftTargets(wave, wave.SourceCraftSlots), ActorIds(wave.Units), ActorIds(wave.Crafts), seaLeaseBefore,
				ReservationDiagnostic(wave));
		}

		void ManageReturning(IBot bot, Actor[] survivors)
		{
			var wave = activeWave;
			var allAtSource = true;
			foreach (var craft in wave.Crafts.Where(IsLiveActor).OrderBy(a => a.ActorID))
			{
				if (!wave.SourceCraftSlots.TryGetValue(craft, out var slot))
					continue;
				var distanceSquared = (craft.Location - slot).LengthSquared;
				ObserveReturnDiagnosticProgress(wave, craft, slot, distanceSquared);
				if (distanceSquared <= 1)
				{
					wave.CrossingLastProgressCell[craft] = craft.Location;
					wave.CrossingLastProgressTick[craft] = world.WorldTick;
					continue;
				}
				allAtSource = false;

				if (!wave.CrossingLastProgressCell.TryGetValue(craft, out var lastCell) || craft.Location != lastCell)
				{
					wave.CrossingLastProgressCell[craft] = craft.Location;
					wave.CrossingLastProgressTick[craft] = world.WorldTick;
					wave.CrossingSameLegRetryCount[craft] = 0;
					continue;
				}
				if (!wave.CrossingLastProgressTick.TryGetValue(craft, out var progressTick) || world.WorldTick - progressTick < Info.StallTimeout)
					continue;

				var sameRetries = wave.CrossingSameLegRetryCount.TryGetValue(craft, out var retry) ? retry : 0;
				if (sameRetries < Info.CrossingSameLegRetries)
				{
					wave.CrossingSameLegRetryCount[craft] = sameRetries + 1;
					wave.CrossingLastProgressTick[craft] = world.WorldTick;
					var activity = craft.CurrentActivity?.GetType().Name ?? "None";
					QueueStopOrder(bot, craft);
					bot.QueueOrder(new Order("Move", craft, Target.FromCell(world, slot), false));
					LogReturnMoveReissue(wave, craft, slot, sameRetries + 1, false,
						"SameLegRetry", activity);
					continue;
				}

				var recoveryAttempt = wave.CrossingRecoveryAttempts.TryGetValue(craft, out var attempt) ? attempt : 0;
				if (recoveryAttempt < Info.MaximumCrossingRecoveryAttempts && TryFindCrossingRecoveryCell(craft, true, recoveryAttempt, out var alternate))
				{
					wave.CrossingRecoveryAttempts[craft] = recoveryAttempt + 1;
					wave.CrossingSameLegRetryCount[craft] = 0;
					wave.SourceCraftSlots[craft] = alternate;
					wave.CrossingLastProgressCell[craft] = craft.Location;
					wave.CrossingLastProgressTick[craft] = world.WorldTick;
					RebaseReturnDiagnostic(wave, craft, alternate);
					var activity = craft.CurrentActivity?.GetType().Name ?? "None";
					QueueStopOrder(bot, craft);
					bot.QueueOrder(new Order("Move", craft, Target.FromCell(world, alternate), false));
					LogReturnMoveReissue(wave, craft, alternate, 0, false,
						$"AlternateReturn{recoveryAttempt + 1}", activity);
					continue;
				}

				// Return is already the safe fallback. Keep the final bounded source-side slot and
				// re-issue it instead of starting another expensive strategic replan.
				wave.CrossingLastProgressTick[craft] = world.WorldTick;
				var finalActivity = craft.CurrentActivity?.GetType().Name ?? "None";
				QueueStopOrder(bot, craft);
				bot.QueueOrder(new Order("Move", craft, Target.FromCell(world, slot), false));
				LogReturnMoveReissue(wave, craft, slot, sameRetries, true,
					"FinalReturnReissue", finalActivity);
			}

			if (!allAtSource)
				return;

			IssueReturnBeachClearOrders(bot, survivors);
			if (!wave.ReturnUnloadPhaseLogged)
			{
				wave.ReturnUnloadPhaseLogged = true;
				FransBotLog.BotDebug(world,
					"{0}: {1} wave={2} state=Returning event=ReturnShoreReached crafts=[{3}] cargo={4} {5}.",
					player, LivenessDiagnosticPrefix, WaveDiagnosticId(wave), ActorIds(wave.Crafts),
					wave.Crafts.Where(IsLiveActor).Sum(c => c.TraitOrDefault<Cargo>()?.PassengerCount ?? 0),
					ReservationDiagnostic(wave));
			}
			var loaded = survivors.Count(IsLoadedIntoAssignedCraft);
			if (loaded == 0)
			{
				FransBotLog.BotDebug(world,
					"{0}: GROUND TRANSFER retreat completed: convoy returned to embark landmass {1}, unloaded surviving Ground cargo, and releases it back to Ground Commander.",
					player, wave.SourceLandmassId);
				ReleaseWave(cancelActivities: false, "crossing recovery exhausted; convoy safely returned and unloaded");
				return;
			}

			foreach (var craft in wave.Crafts.Where(IsLiveActor).OrderBy(a => a.ActorID))
			{
				var cargo = craft.TraitOrDefault<Cargo>();
				if (cargo == null || cargo.IsTraitDisabled || cargo.PassengerCount == 0)
					continue;
				var count = cargo.PassengerCount;
				if (!wave.ReturnLastCargoCount.TryGetValue(craft, out var oldCount) || count < oldCount)
				{
					wave.ReturnLastCargoCount[craft] = count;
					wave.ReturnLastCargoProgressTick[craft] = world.WorldTick;
					wave.ReturnUnloadLastRealProgressTick[craft] = world.WorldTick;
				}
				if (!wave.ReturnLastCargoProgressTick.TryGetValue(craft, out var cargoTick))
					wave.ReturnLastCargoProgressTick[craft] = cargoTick = world.WorldTick;
				if (!wave.ReturnUnloadLastRealProgressTick.TryGetValue(craft, out var realProgressTick))
					wave.ReturnUnloadLastRealProgressTick[craft] = realProgressTick = world.WorldTick;
				var canUnload = cargo.CanUnload();
				var shouldIssueUnload = (!wave.ReturnUnloadIssued.Contains(craft) || world.WorldTick - cargoTick >= Info.UnloadStallTimeout) && canUnload;
				var currentActivity = craft.CurrentActivity?.GetType().Name ?? "None";
				if (shouldIssueUnload)
				{
					QueueStopOrder(bot, craft);
					bot.QueueOrder(new Order("Unload", craft, false));
					wave.ReturnUnloadIssued.Add(craft);
					wave.ReturnLastCargoProgressTick[craft] = world.WorldTick;
				}

				var diagnosticDue = !wave.ReturnUnloadNextDiagnosticTick.TryGetValue(craft, out var nextDiagnosticTick) ||
					world.WorldTick >= nextDiagnosticTick;
				if (shouldIssueUnload || (diagnosticDue && (!canUnload || world.WorldTick - realProgressTick >= Info.UnloadStallTimeout)))
				{
					wave.ReturnUnloadNextDiagnosticTick[craft] = world.WorldTick + Info.UnloadStallTimeout;
					FransBotLog.BotDebug(world,
						"{0}: {1} wave={2} state=Returning event=ReturnUnload craft={3}:{4} cell={5} cargo={6} canUnload={7} lastCargoProgressWT={8} noCargoProgressWT={9} unloadEverIssued={10} unloadQueued={11} currentActivity={12} isIdle={13} {14}.",
						player, LivenessDiagnosticPrefix, WaveDiagnosticId(wave), craft.ActorID, craft.Info.Name,
						craft.Location, count, canUnload, realProgressTick, world.WorldTick - realProgressTick,
						wave.ReturnUnloadIssued.Contains(craft), shouldIssueUnload, currentActivity, craft.IsIdle,
						ReservationDiagnostic(wave));
				}
			}
		}

		void IssueReturnBeachClearOrders(IBot bot, IEnumerable<Actor> survivors)
		{
			var wave = activeWave;
			foreach (var unit in survivors.Where(a => a != null && a.IsInWorld && !a.IsDead && !IsLoadedIntoAssignedCraft(a)).OrderBy(a => a.ActorID))
			{
				if (!wave.SourceUnitSlots.TryGetValue(unit, out var slot) || (unit.Location - slot).LengthSquared <= 1)
					continue;
				if (unit.IsIdle)
					bot.QueueOrder(new Order("Move", unit, Target.FromCell(world, slot), false));
			}
		}

		void BeginUnload(IBot bot)
		{
			var wave = activeWave;
			foreach (var craft in wave.Crafts.Where(IsLiveActor).OrderBy(a => a.ActorID))
			{
				var cargo = craft.TraitOrDefault<Cargo>();
				if (cargo == null || cargo.IsTraitDisabled)
					continue;
				wave.LastCraftCargoCount[craft] = cargo.PassengerCount;
				wave.LastCraftUnloadProgressTick[craft] = world.WorldTick;
				wave.DestinationUnloadLastRealProgressTick[craft] = world.WorldTick;
				wave.CraftUnloadRecoveryAttempts[craft] = 0;
				if (!cargo.CanUnload())
					continue;
				QueueStopOrder(bot, craft);
				bot.QueueOrder(new Order("Unload", craft, false));
				wave.UnloadIssued.Add(craft);
			}
			FransBotLog.BotDebug(world,
				"{0}: GROUND TRANSFER convoy reached landing screen at {1}/{2}; native Unload is issued independently to {3} craft. tracks cargo progress per LST and may use bounded alternate landing slots if one ramp stalls.",
				player, wave.TargetShore.NavalCell, wave.TargetShore.GroundCell, wave.UnloadIssued.Count);
		}

		void ManageUnloading(IBot bot, Actor[] survivors)
		{
			var wave = activeWave;
			IssueBeachClearOrders(bot, survivors);

			var loaded = survivors.Count(IsLoadedIntoAssignedCraft);
			if (loaded != wave.LastLoadedCount)
			{
				wave.LastLoadedCount = loaded;
				wave.LastProgressTick = world.WorldTick;
			}
			if (loaded == 0)
			{
				ReleaseTransports();
				wave.State = TransferState.Regroup;
				wave.StateStartedTick = world.WorldTick;
				wave.LastProgressTick = world.WorldTick;
				wave.LastRegroupedCount = -1;
				LogWaveTransition(wave, TransferState.Unloading, TransferState.Regroup,
					"all surviving passengers left their assigned LSTs");
				IssueRegroupOrders(bot, survivors, force: true);
				return;
			}

			foreach (var craft in wave.Crafts.Where(IsLiveActor).OrderBy(a => a.ActorID))
			{
				var cargo = craft.TraitOrDefault<Cargo>();
				if (cargo == null || cargo.IsTraitDisabled || cargo.PassengerCount == 0)
					continue;

				var count = cargo.PassengerCount;
				if (!wave.LastCraftCargoCount.TryGetValue(craft, out var oldCount) || count < oldCount)
				{
					wave.LastCraftCargoCount[craft] = count;
					wave.LastCraftUnloadProgressTick[craft] = world.WorldTick;
					wave.DestinationUnloadLastRealProgressTick[craft] = world.WorldTick;
					wave.CraftUnloadRecoveryAttempts[craft] = 0;
					wave.CraftUnloadRecoveryCell.Remove(craft);
				}

				if (!wave.LastCraftUnloadProgressTick.TryGetValue(craft, out var progressTick))
				{
					progressTick = world.WorldTick;
					wave.LastCraftUnloadProgressTick[craft] = progressTick;
				}

				if (wave.CraftUnloadRecoveryCell.TryGetValue(craft, out var recoveryCell))
				{
					if ((craft.Location - recoveryCell).LengthSquared <= 1 || craft.IsIdle)
					{
						wave.CraftUnloadRecoveryCell.Remove(craft);
						if (cargo.CanUnload())
						{
							QueueStopOrder(bot, craft);
							bot.QueueOrder(new Order("Unload", craft, false));
							wave.LastCraftUnloadProgressTick[craft] = world.WorldTick;
						}
					}
					continue;
				}

				if (world.WorldTick - progressTick >= Info.UnloadStallTimeout)
				{
					var attempt = wave.CraftUnloadRecoveryAttempts.TryGetValue(craft, out var a) ? a : 0;
					if (attempt < Info.MaximumUnloadRecoveryAttempts && TryFindUnloadRecoveryCell(craft, attempt, out var alternate))
					{
						wave.CraftUnloadRecoveryAttempts[craft] = attempt + 1;
						wave.CraftUnloadRecoveryCell[craft] = alternate;
						wave.LastCraftUnloadProgressTick[craft] = world.WorldTick;
						QueueStopOrder(bot, craft);
						bot.QueueOrder(new Order("Move", craft, Target.FromCell(world, alternate), false));
						FransBotLog.BotDebug(world,
							"{0}: GROUND TRANSFER LST {1} unload stalled with {2} passenger(s); bounded landing recovery {3}/{4} moves to alternate naval cell {5} before another native Unload.",
							player, craft.ActorID, count, attempt + 1, Info.MaximumUnloadRecoveryAttempts, alternate);
						continue;
					}

					// If no alternate is legal, force one clean retry at the current landing cell instead
					// of waiting forever for IsIdle. A currently progressing Unload is never touched
					// because this branch only runs after UnloadStallTimeout without cargo decrease.
					wave.LastCraftUnloadProgressTick[craft] = world.WorldTick;
					var canUnload = cargo.CanUnload();
					var currentActivity = craft.CurrentActivity?.GetType().Name ?? "None";
					var unloadQueued = false;
					if (canUnload)
					{
						QueueStopOrder(bot, craft);
						bot.QueueOrder(new Order("Unload", craft, false));
						unloadQueued = true;
					}
					var realProgressTick = wave.DestinationUnloadLastRealProgressTick.TryGetValue(craft, out var lastRealProgress)
						? lastRealProgress : wave.StateStartedTick;
					var target = wave.TargetCraftSlots.TryGetValue(craft, out var targetSlot) ? targetSlot : wave.TargetShore.NavalCell;
					FransBotLog.BotDebug(world,
						"{0}: {1} wave={2} state=Unloading event=FinalUnloadRetry craft={3}:{4} cell={5} target={6} distanceSq={7} cargo={8} bestCargo={9} canUnload={10} lastCargoProgressWT={11} noCargoProgressWT={12} alternateAttempts={13}/{14} alternateExhausted=True unloadQueued={15} currentActivity={16} isIdle={17} {18}.",
						player, LivenessDiagnosticPrefix, WaveDiagnosticId(wave), craft.ActorID, craft.Info.Name,
						craft.Location, target, (craft.Location - target).LengthSquared, count,
						wave.LastCraftCargoCount.TryGetValue(craft, out var bestCargo) ? bestCargo : count,
						canUnload, realProgressTick, world.WorldTick - realProgressTick, attempt,
						Info.MaximumUnloadRecoveryAttempts, unloadQueued, currentActivity, craft.IsIdle,
						ReservationDiagnostic(wave));
				}
				else if (world.WorldTick >= wave.NextUnloadRetryTick && craft.IsIdle && cargo.CanUnload())
					bot.QueueOrder(new Order("Unload", craft, false));
			}

			if (world.WorldTick >= wave.NextUnloadRetryTick)
				wave.NextUnloadRetryTick = world.WorldTick + Info.UnloadRetryInterval;
		}

		void IssueBeachClearOrders(IBot bot, IEnumerable<Actor> survivors)
		{
			var wave = activeWave;
			foreach (var unit in survivors.Where(a => a != null && a.IsInWorld && !a.IsDead && !IsLoadedIntoAssignedCraft(a)).OrderBy(a => a.ActorID))
			{
				if (!wave.TargetUnitSlots.TryGetValue(unit, out var slot) || (unit.Location - slot).LengthSquared <= 1)
					continue;

				// As soon as a passenger materializes at the landing handoff, queue its native Move behind
				// the current unload/disembark activity. This clears the LST ramp without waiting
				// for IsIdle, while preserving OpenRA's native Unload sequencing. Idle units still
				// receive an immediate non-queued retry if their first landing-clear order finished
				// before reaching the assigned inland slot.
				if (!wave.BeachClearMoveIssued.Contains(unit))
				{
					bot.QueueOrder(new Order("Move", unit, Target.FromCell(world, slot), !unit.IsIdle));
					wave.BeachClearMoveIssued.Add(unit);
				}
				else if (unit.IsIdle)
					bot.QueueOrder(new Order("Move", unit, Target.FromCell(world, slot), false));
			}
		}

		bool TryFindUnloadRecoveryCell(Actor craft, int attempt, out CPos cell)
		{
			cell = default;
			var mobile = craft?.TraitOrDefault<Mobile>();
			if (mobile == null || !strategicMap.TryGetNavalRegionId(activeWave.TargetShore.NavalCell, out var targetRegion))
				return false;

			var candidates = world.Map.FindTilesInAnnulus(activeWave.TargetShore.NavalCell, 1, Info.UnloadRecoveryRadius)
				.Where(world.Map.Contains)
				.Where(c => strategicMap.TryGetNavalRegionId(c, out var region) && region == targetRegion)
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.Where(c => !riskModel.EvaluateCell(craft, c, FransRiskRole.NavalTransport, FransRiskTolerance.Cautious).IsCritical)
				.OrderBy(c => (c - activeWave.TargetShore.GroundCell).LengthSquared)
				.ThenBy(c => c.X).ThenBy(c => c.Y)
				.ToArray();
			if (candidates.Length == 0)
				return false;

			cell = candidates[Math.Min(attempt, candidates.Length - 1)];
			if (cell == craft.Location && candidates.Length > 1)
				cell = candidates[Math.Min(attempt + 1, candidates.Length - 1)];
			return cell != craft.Location;
		}

		void ManageRegroup(IBot bot, Actor[] survivors)
		{
			var wave = activeWave;
			var inWorld = survivors.Where(a => a.IsInWorld).ToArray();
			var radiusSq = Info.RegroupRadius * Info.RegroupRadius;
			var regrouped = inWorld.Count(a => (a.Location - wave.TargetShore.GroundCell).LengthSquared <= radiusSq);
			if (regrouped != wave.LastRegroupedCount)
			{
				wave.LastRegroupedCount = regrouped;
				wave.LastProgressTick = world.WorldTick;
			}
			var required = Math.Max(1, (inWorld.Length * Info.RegroupRequiredPercent + 99) / 100);
			if (regrouped >= required || world.WorldTick - wave.StateStartedTick >= Info.RegroupTimeout)
			{
				FransBotLog.BotDebug(world,
					"{0}: GROUND TRANSFER CONVOY handoff complete on landmass {1}: {2}/{3} surviving units regrouped near {4}. Ground reservations release now; ordinary Ground Commanders resume mission ownership.",
					player, wave.TargetLandmassId, regrouped, inWorld.Length, wave.TargetShore.GroundCell);
				ReleaseWave(cancelActivities: false, "target regroup handoff complete");
				return;
			}
			if (world.WorldTick - wave.LastProgressTick >= Info.StallTimeout)
			{
				wave.LastProgressTick = world.WorldTick;
				IssueRegroupOrders(bot, inWorld, force: false);
			}
		}

		void IssueRegroupOrders(IBot bot, IEnumerable<Actor> survivors, bool force)
		{
			var wave = activeWave;
			foreach (var unit in survivors.Where(a => a != null && a.IsInWorld && !a.IsDead).OrderBy(a => a.ActorID))
			{
				if (!wave.TargetUnitSlots.TryGetValue(unit, out var slot) || (unit.Location - slot).LengthSquared <= 1)
					continue;
				if (force || unit.IsIdle)
					bot.QueueOrder(new Order("Move", unit, Target.FromCell(world, slot), false));
			}
		}

		void RefreshSeaSupportLease()
		{
			var wave = activeWave;
			if (wave == null || wave.SeaSupportRequestId == 0)
				return;
			general.RequestSeaTransportBeachSecure(wave.SeaSupportRequestId, wave.TargetShore.NavalCell, world.WorldTick + Info.SeaSecureLeaseTicks);
		}

		void ReleaseTransports()
		{
			var wave = activeWave;
			if (wave == null || wave.TransportsReleased)
				return;
			foreach (var craft in wave.Crafts)
				if (craft != null)
					transportService.ReleaseExternalTransport(craft, reservationOwner);
			wave.TransportsReleased = true;
		}

		long CraftMetric(IEnumerable<Actor> actors, IReadOnlyDictionary<Actor, CPos> slots)
		{
			long total = 0;
			foreach (var actor in actors.Where(IsLiveActor))
				if (slots.TryGetValue(actor, out var slot))
					total += (actor.Location - slot).LengthSquared;
			return total;
		}

		string WaveDiagnosticId(TransferWave wave) =>
			$"{player.PlayerActor.ActorID}:{wave.StartedTick}:{wave.SourceLandmassId}>{wave.TargetLandmassId}:{wave.TargetActorId}";

		static string ActorIds(IEnumerable<Actor> actors) =>
			string.Join(",", actors.Where(a => a != null).OrderBy(a => a.ActorID).Select(a => a.ActorID));

		static string CraftTargets(TransferWave wave, IReadOnlyDictionary<Actor, CPos> targets) =>
			string.Join(",", wave.Crafts.Where(a => a != null).OrderBy(a => a.ActorID)
				.Select(a => targets.TryGetValue(a, out var target) ? $"{a.ActorID}:{target}" : $"{a.ActorID}:none"));

		string ReservationDiagnostic(TransferWave wave) =>
			$"groundReservations={wave.Units.Count(reservedGroundUnits.Contains)}/{wave.Units.Count} " +
			$"transportReservations={wave.Crafts.Count(c => c != null && transportService.IsTransportReserved(c))}/{wave.Crafts.Count} " +
			$"seaLeaseHeld={wave.SeaSupportRequestId != 0} seaLease={wave.SeaSupportRequestId}";

		void LogWaveTransition(TransferWave wave, TransferState previous, TransferState current, string reason)
		{
			FransBotLog.BotDebug(world,
				"{0}: {1} wave={2} transition={3}->{4} reason={5} ageWT={6} stateAgeWT={7} groundActors=[{8}] crafts=[{9}] {10}.",
				player, LivenessDiagnosticPrefix, WaveDiagnosticId(wave), previous, current, reason,
				world.WorldTick - wave.StartedTick, world.WorldTick - wave.StateStartedTick,
				ActorIds(wave.Units), ActorIds(wave.Crafts), ReservationDiagnostic(wave));
		}

		void RebaseReturnDiagnostic(TransferWave wave, Actor craft, CPos target)
		{
			var distanceSquared = (craft.Location - target).LengthSquared;
			wave.ReturnDiagnosticTarget[craft] = target;
			wave.ReturnBestDistanceSquared[craft] = distanceSquared;
			wave.ReturnLastDistanceProgressTick[craft] = world.WorldTick;
		}

		void ObserveReturnDiagnosticProgress(TransferWave wave, Actor craft, CPos target, int distanceSquared)
		{
			if (!wave.ReturnDiagnosticTarget.TryGetValue(craft, out var previousTarget) || previousTarget != target ||
				!wave.ReturnBestDistanceSquared.TryGetValue(craft, out var bestDistanceSquared))
			{
				RebaseReturnDiagnostic(wave, craft, target);
				return;
			}

			if (distanceSquared < bestDistanceSquared)
			{
				wave.ReturnBestDistanceSquared[craft] = distanceSquared;
				wave.ReturnLastDistanceProgressTick[craft] = world.WorldTick;
			}
		}

		void LogReturnMoveReissue(TransferWave wave, Actor craft, CPos target, int sameLegRetries,
			bool alternateExhausted, string outcome, string currentActivity)
		{
			var distanceSquared = (craft.Location - target).LengthSquared;
			var bestDistanceSquared = wave.ReturnBestDistanceSquared.TryGetValue(craft, out var best) ? best : distanceSquared;
			var lastProgressTick = wave.ReturnLastDistanceProgressTick.TryGetValue(craft, out var progressTick)
				? progressTick : wave.StateStartedTick;
			var recoveryAttempts = wave.CrossingRecoveryAttempts.TryGetValue(craft, out var attempts) ? attempts : 0;
			FransBotLog.BotDebug(world,
				"{0}: {1} wave={2} state=Returning event=MoveReissue outcome={3} craft={4}:{5} cell={6} target={7} distanceSq={8} bestDistanceSq={9} lastProgressWT={10} noProgressWT={11} sameLegRetries={12}/{13} alternateAttempts={14}/{15} alternateExhausted={16} moveReissued=True currentActivity={17} isIdle={18} {19}.",
				player, LivenessDiagnosticPrefix, WaveDiagnosticId(wave), outcome, craft.ActorID, craft.Info.Name,
				craft.Location, target, distanceSquared, bestDistanceSquared, lastProgressTick,
				world.WorldTick - lastProgressTick, sameLegRetries, Info.CrossingSameLegRetries,
				recoveryAttempts, Info.MaximumCrossingRecoveryAttempts, alternateExhausted,
				currentActivity, craft.IsIdle, ReservationDiagnostic(wave));
		}


		bool IsLoadedIntoAssignedCraft(Actor actor)
		{
			if (activeWave == null || actor == null || actor.Disposed || actor.IsDead || actor.IsInWorld)
				return false;
			var passenger = actor.TraitOrDefault<Passenger>();
			var craft = passenger?.Transport;
			return craft != null && activeWave.Crafts.Contains(craft) && IsLoadedInto(actor, craft);
		}

		bool IsSurvivingPassenger(Actor actor) => actor != null && !actor.Disposed && !actor.IsDead;
		bool IsLiveActor(Actor actor) => actor != null && !actor.Disposed && actor.IsInWorld && !actor.IsDead;

		static bool IsLoadedInto(Actor passengerActor, Actor craft)
		{
			if (passengerActor == null || craft == null || passengerActor.Disposed || passengerActor.IsDead || passengerActor.IsInWorld ||
				craft.Disposed || !craft.IsInWorld || craft.IsDead)
				return false;
			var passenger = passengerActor.TraitOrDefault<Passenger>();
			var cargo = craft.TraitOrDefault<Cargo>();
			return passenger?.Transport == craft && cargo != null && cargo.Passengers.Contains(passengerActor);
		}

		void ReleaseWave(bool cancelActivities, string reason)
		{
			var wave = activeWave;
			if (wave == null)
				return;
			var waveId = WaveDiagnosticId(wave);
			var state = wave.State;
			var groundActorIds = ActorIds(wave.Units);
			var craftIds = ActorIds(wave.Crafts);
			var seaSupportRequestId = wave.SeaSupportRequestId;
			var seaLeaseReleased = seaSupportRequestId == 0;

			if (cancelActivities)
			{
				foreach (var unit in wave.Units.Where(a => a != null && a.IsInWorld && !a.IsDead))
					QueueStopOrder(null, unit);
				foreach (var craft in wave.Crafts.Where(IsLiveActor))
					QueueStopOrder(null, craft);
			}

			foreach (var unit in wave.Units)
				reservedGroundUnits.Remove(unit);
			ReleaseTransports();
			if (wave.SeaSupportRequestId != 0)
			{
				general.ReleaseSeaTransportBeachSecure(wave.SeaSupportRequestId);
				seaLeaseReleased = true;
			}
			FransBotLog.BotDebug(world,
				"{0}: GROUND TRANSFER CONVOY closes wave {1}->{2}: {3}. LSTs={4}, Sea support request={5}, reserved Ground survivors released={6}.",
				player, wave.SourceLandmassId, wave.TargetLandmassId, reason, wave.Crafts.Count, wave.SeaSupportRequestId,
				wave.Units.Count(a => a != null && !a.Disposed && !a.IsDead));
			FransBotLog.BotDebug(world,
				"{0}: {1} wave={2} transition={3}->Released reason={4} groundActors=[{5}] crafts=[{6}] groundReservationsAfter={7} transportReservationsAfter={8} seaLeaseReleased={9} seaLease={10}.",
				player, LivenessDiagnosticPrefix, waveId, state, reason, groundActorIds, craftIds,
				wave.Units.Count(reservedGroundUnits.Contains),
				wave.Crafts.Count(c => c != null && transportService.IsTransportReserved(c)),
				seaLeaseReleased, seaSupportRequestId);
			activeWave = null;
			nextPlanningTick = world.WorldTick + Info.WaveCooldown;
		}
	}
}
