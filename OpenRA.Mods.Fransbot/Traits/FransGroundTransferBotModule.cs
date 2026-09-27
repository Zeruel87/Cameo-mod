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
	[Desc("Ground logistics convoy service. Moves ordinary Ground combat units between fair-known static land masses in concentrated demand-sized LST waves. GroundTransfer owns Ground passengers and LST logistics only; Sea combat ships remain under Sea Commander and may independently answer a Sea-only SECURE around the destination beach. It creates no new Ground strategic MISSION.")]
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

		[Desc("Lease duration in world ticks refreshed while a GroundTransfer wave is active for the independent Sea-only SECURE around the destination beach.")]
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

		[Desc("Broad ground-side embark zone around the selected beach. Units inside this zone may receive native EnterTransport directly without waiting on an exact staging slot.")]
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

		[Desc("Same cached crossing-leg retries before a bounded local alternate landing cell is tried around the already selected beach.")]
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

		[Desc("World ticks between native Unload retries at the destination beach.")]
		public readonly int UnloadRetryInterval = 75;

		[Desc("World ticks with no decrease in one LST's cargo count before GroundTransfer treats that craft as unload-stalled and tries a bounded alternate beach slot.")]
		public readonly int UnloadStallTimeout = 150;

		[Desc("Maximum bounded alternate beach-slot recovery moves for one LST before it keeps retrying native Unload in place.")]
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
		IBotTick, IFransGroundTransferService
	{
		enum TransferState
		{
			Assemble,
			Boarding,
			Crossing,
			Returning,
			Unloading,
			Regroup
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
		readonly Player player;
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
				"{0}: Ground Transfer FOLLOW-ON REINFORCEMENT active. GroundTransfer owns Ground passengers + LST logistics only. One ready LST may begin streaming boarding immediately; passengers use a broad embark zone and dynamically choose the nearest compatible ready LST with free Cargo instead of being permanently locked to one craft. Busy/reserved LSTs remain part of the shared bounded pool, so logistics waits for reuse instead of manufacturing replacement craft. Sea remains fully decoupled and supports only through the independent destination-beach SECURE.",
				player);
		}

		protected override void TraitDisabled(Actor self)
		{
			ReleaseWave(cancelActivities: false, "trait disabled");
			reservedGroundUnits.Clear();
		}

		bool IFransGroundTransferService.IsGroundUnitTransferReserved(Actor actor) =>
			actor != null && reservedGroundUnits.Contains(actor);


		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransGroundTransfer.BotTick");
			if (world.Type == WorldType.Editor || player.WinState != WinState.Undefined)
				return;

			if (--scanTicks > 0)
				return;
			scanTicks = Info.ScanInterval;
			FransBotLog.SetPerfContext(world, $"GROUND-XFER:{player.PlayerActor.ActorID}",
				activeWave == null
					? "Idle"
					: $"{activeWave.State} src={activeWave.SourceLandmassId} dst={activeWave.TargetLandmassId} lst=[{string.Join(",", activeWave.Crafts.Select(a => a?.ActorID ?? 0))}] sea-secure={activeWave.SeaSupportRequestId} units={activeWave.Units.Count}");

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
				out var requiredTargetValue, out var currentTargetValue, out var reason))
				return;

			var sourceGroups = EligibleGroundUnits()
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
				.Where(g => g.Transferable.Length > 0)
				.OrderByDescending(g => g.Transferable.Sum(GetUnitValue))
				.ThenByDescending(g => g.Transferable.Length)
				.ThenBy(g => g.LandmassId)
				.ToArray();

			foreach (var source in sourceGroups)
			{
				var transferable = source.Transferable;
				if (transferable.Length == 0)
					continue;

				var emergencyDefend = missionType == FransMissionType.Defend;
				var desiredCraftCount = DesiredCraftCount(transferable.Length);
				var sourceHint = new CPos((int)transferable.Average(a => a.Location.X), (int)transferable.Average(a => a.Location.Y));
				EnsureLandingCraftCapacity(bot, desiredCraftCount, source.LandmassId, targetLandmassId, sourceHint, targetCell);

				if (!TryChooseConvoyAndShorePair(source.LandmassId, targetLandmassId, transferable, targetCell,
					desiredCraftCount, emergencyDefend, out var crafts, out var sourceShore, out var targetShore, out var landingRisk))
					continue;

				if (!TryBuildUnitCraftAssignments(transferable, sourceShore.GroundCell, crafts, out var selected, out var unitCraft))
					continue;

				var minimumUnits = emergencyDefend ? Info.MinimumDefendWaveUnits : Info.MinimumStrategicWaveUnits;
				var effectiveMinimumUnits = Math.Min(minimumUnits, transferable.Length);
				if (selected.Length < effectiveMinimumUnits)
					continue;

				var usedCrafts = unitCraft.Values.Distinct().OrderBy(a => a.ActorID).ToArray();
				// Do not launch a deliberately under-capacity convoy. Production demand is derived
				// from the currently transferable passengers, so wait for that exact capacity.
				if (usedCrafts.Length < desiredCraftCount)
					continue;

				if (!TryAssignNavalSlots(usedCrafts, sourceShore.NavalCell, sourceShore.NavalRegionId, Info.NavalFormationRadius, out var sourceCraftSlots) ||
					!TryAssignNavalSlots(usedCrafts, targetShore.NavalCell, targetShore.NavalRegionId, Info.NavalFormationRadius, out var targetCraftSlots))
					continue;

				var reservedCrafts = new List<Actor>();
				var reserveFailed = false;
				foreach (var craft in usedCrafts)
				{
					if (!transportService.TryReserveExternalTransport(craft, reservationOwner))
					{
						reserveFailed = true;
						break;
					}
					reservedCrafts.Add(craft);
				}
				if (reserveFailed)
				{
					foreach (var craft in reservedCrafts)
						transportService.ReleaseExternalTransport(craft, reservationOwner);
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
					"{0}: GROUND TRANSFER CONVOY starts {1}-unit wave {2}->{3} using {4} LST(s) [{5}], embark {6}/{7}, landing {8}/{9}; target {10} ({11}), local value {12}/{13}, landing risk {14}/{15}. {16}. Sea combat is fully decoupled: General opened independent Sea-only SECURE {17} at the destination beach; no Sea ship is reserved or ordered by GroundTransfer.",
					player, wave.Units.Count, wave.SourceLandmassId, wave.TargetLandmassId, wave.Crafts.Count,
					string.Join(",", wave.Crafts.Select(a => a.ActorID)), wave.SourceShore.GroundCell, wave.SourceShore.NavalCell,
					wave.TargetShore.NavalCell, wave.TargetShore.GroundCell, targetCell, missionType?.ToString() ?? "ForwardAnchor",
					currentTargetValue, requiredTargetValue, landingRisk.Score, landingRisk.CriticalThreshold, reason, wave.SeaSupportRequestId);
				return;
			}
		}

		int DesiredCraftCount(int transferableUnits)
		{
			// LST count is pure passenger demand, never a standing convoy target.
			// CargoInfo remains authoritative at assignment time; this only sizes production.
			var byUnits = Math.Max(1, (transferableUnits + Info.DesiredUnitsPerLandingCraft - 1) / Info.DesiredUnitsPerLandingCraft);
			return Math.Min(byUnits, Info.MaximumConvoyLandingCraft);
		}

		void EnsureLandingCraftCapacity(IBot bot, int desiredCraftCount, int sourceLandmassId, int targetLandmassId, CPos sourceHint, CPos targetHint)
		{
			if (amphibiousExpansion?.HasStrategicLandingCraftProductionDemand == true)
			{
				nextLandingCraftProductionRequestTick = world.WorldTick + Info.LandingCraftProductionRequestCooldown;
				return;
			}

			if (desiredCraftCount <= 0 || world.WorldTick < nextLandingCraftProductionRequestTick ||
				playerResources == null || playerResources.GetCashAndResources() < Info.MinimumCashForLandingCraftRequest)
				return;

			if (!HasLossSafeLandingCraftProductionCorridor(sourceLandmassId, targetLandmassId, sourceHint, targetHint))
			{
				nextLandingCraftProductionRequestTick = world.WorldTick + Info.LandingCraftProductionRequestCooldown;
				FransBotLog.BotDebug(world,
					"{0}: GROUND TRANSFER suppresses new LST production for landmass {1} -> {2}; all fair-known common shoreline corridors intersect an active LST-loss SECURE exclusion. Existing combat SECURE work may clear it; logistics retries after cooldown/revision change.",
					player, sourceLandmassId, targetLandmassId);
				return;
			}

			var unitBuilder = requestUnitProduction?.FirstEnabledTraitOrDefault();
			if (unitBuilder == null)
				return;

			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			var shipQueues = queuesByCategory[Info.LandingCraftQueueCategory].Where(q => q.Enabled).ToArray();
			if (shipQueues.Length == 0)
				return;

			var craftType = Info.LandingCraftTypes.OrderBy(x => x).FirstOrDefault(type =>
				world.Map.Rules.Actors.TryGetValue(type, out var actorInfo) &&
				actorInfo.TraitInfoOrDefault<BuildableInfo>() is BuildableInfo buildable &&
				buildable.Queue.Contains(Info.LandingCraftQueueCategory));
			if (craftType == null)
				return;

			var sharedPoolCount = transportService.CountLandingCraftPool(bot);
			var nonStrategicCap = transportService.MaximumNonStrategicLandingCraftPool;
			var desiredBoundedCount = Math.Min(desiredCraftCount, nonStrategicCap);
			if (sharedPoolCount >= desiredBoundedCount || sharedPoolCount >= nonStrategicCap)
			{
				nextLandingCraftProductionRequestTick = world.WorldTick + Info.LandingCraftProductionRequestCooldown;
				return;
			}

			nextLandingCraftProductionRequestTick = world.WorldTick + Info.LandingCraftProductionRequestCooldown;
			unitBuilder.RequestUnitProduction(bot, craftType);
			FransBotLog.BotDebug(world,
				"{0}: GROUND TRANSFER logistics demand requests {1}; non-strategic physical+queued+requested LST pool {2}/{3}, global hard cap {4}, convoy demand {5}. The final pool slot stays reserved for PIONEER regional sea supply; all existing craft remain reusable when strategically free.",
				player, craftType, sharedPoolCount, nonStrategicCap, transportService.MaximumLandingCraftPool, desiredBoundedCount);
		}

		bool HasLossSafeLandingCraftProductionCorridor(int sourceLandmassId, int targetLandmassId, CPos sourceHint, CPos targetHint)
		{
			var sourceAccess = strategicMap.GetGroundShoreAccess(sourceLandmassId)
				.OrderBy(s => (s.GroundCell - sourceHint).LengthSquared)
				.ThenBy(s => s.NavalCell.X).ThenBy(s => s.NavalCell.Y).Take(8).ToArray();
			var targetAccess = strategicMap.GetGroundShoreAccess(targetLandmassId)
				.OrderBy(s => (s.GroundCell - targetHint).LengthSquared)
				.ThenBy(s => s.NavalCell.X).ThenBy(s => s.NavalCell.Y).Take(8).ToArray();
			var foundCommonNavalRegion = false;
			foreach (var source in sourceAccess)
				foreach (var target in targetAccess)
				{
					if (source.NavalRegionId != target.NavalRegionId)
						continue;
					foundCommonNavalRegion = true;
					if (general.IsTransportLossCorridorAllowed(source.NavalCell, target.NavalCell))
						return true;
				}

			return !foundCommonNavalRegion;
		}

		bool TrySelectDemand(out FransMissionType? missionType, out uint targetActorId, out CPos targetCell,
			out int targetLandmassId, out int requiredValue, out int currentValue, out string reason)
		{
			missionType = null;
			targetActorId = 0;
			targetCell = default;
			targetLandmassId = 0;
			requiredValue = 0;
			currentValue = 0;
			reason = null;

			general.EnsureCurrentMissions();
			foreach (var mission in general.CurrentMissions
				.Where(m => (m.Type == FransMissionType.Defend || m.Type == FransMissionType.Secure) &&
					m.TargetActorType != FransGeneralBotModule.SeaTransportBeachSecureTargetType &&
					m.TargetActorType != FransGeneralBotModule.TransportLossSecureTargetType)
				.OrderByDescending(m => m.Type == FransMissionType.Defend)
				.ThenByDescending(m => m.StrategicPriority)
				.ThenBy(m => m.TargetActorId))
			{
				if (!strategicMap.TryGetGroundLandmassId(mission.LastVisibleTargetCell, out var landmassId))
					continue;

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
					continue;

				missionType = mission.Type;
				targetActorId = mission.TargetActorId;
				targetCell = mission.LastVisibleTargetCell;
				targetLandmassId = landmassId;
				requiredValue = needed;
				currentValue = local;
				reason = $"General {mission.Type} demand is understrength on another landmass";
				return true;
			}

			if (!general.TryGetLatestGroundAnchor(out var anchor) ||
				!strategicMap.TryGetGroundLandmassId(anchor, out var anchorLandmass))
				return false;

			var anchorValue = GroundValueOnLandmass(anchorLandmass);
			targetCell = anchor;
			targetLandmassId = anchorLandmass;
			requiredValue = Math.Max(Info.ForwardAnchorDesiredGroundValue, anchorValue == int.MaxValue ? int.MaxValue : anchorValue + 1);
			currentValue = anchorValue;
			reason = "Forward Anchor redeployment/remote-landmass evacuation";
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
			out FransGroundShoreAccess targetShore, out FransRiskAssessment landingRisk)
		{
			using var fransPerf = FransBotLog.Profile(world, player, "GroundTransfer.ShoreSelect");
			crafts = Array.Empty<Actor>();
			sourceShore = default;
			targetShore = default;
			landingRisk = default;
			var sourceAccess = strategicMap.GetGroundShoreAccess(sourceLandmassId);
			var targetAccess = strategicMap.GetGroundShoreAccess(targetLandmassId);
			if (sourceAccess.Count == 0 || targetAccess.Count == 0)
				return false;

			var available = combatIntel.OwnedActors.Where(IsAvailableLandingCraft).OrderBy(a => a.ActorID).ToArray();
			if (available.Length == 0)
				return false;

			var centroid = new CPos((int)sourceUnits.Average(a => a.Location.X), (int)sourceUnits.Average(a => a.Location.Y));
			var bestScore = long.MaxValue;
			var bestRegion = 0;
			var hasBestRegion = false;
			FransRiskAssessment bestRisk = default;
			foreach (var seed in available)
			{
				var mobile = seed.TraitOrDefault<Mobile>();
				if (mobile == null || !strategicMap.TryGetNavalRegionId(mobile.ToCell, out var regionId))
					continue;

				var source = sourceAccess.Where(a => a.NavalRegionId == regionId)
					.OrderBy(a => (a.GroundCell - centroid).LengthSquared)
					.ThenBy(a => a.NavalCell.X).ThenBy(a => a.NavalCell.Y).FirstOrDefault();
				if (source.GroundLandmassId == 0)
					continue;

				foreach (var target in targetAccess.Where(a => a.NavalRegionId == regionId)
					.OrderBy(a => (a.GroundCell - targetCell).LengthSquared)
					.ThenBy(a => a.NavalCell.X).ThenBy(a => a.NavalCell.Y).Take(8))
				{
					if (target.GroundLandmassId == 0 ||
						!mobile.CanEnterCell(source.NavalCell, check: BlockedByActor.Immovable) || !mobile.CanStayInCell(source.NavalCell) ||
						!mobile.CanEnterCell(target.NavalCell, check: BlockedByActor.Immovable) || !mobile.CanStayInCell(target.NavalCell) ||
						!HasTransportLossSafeNavalRoute(seed, mobile, source.NavalCell, target.NavalCell))
						continue;

					var risk = riskModel.EvaluateStrategicCell(target.NavalCell, FransRiskRole.NavalTransport,
						emergencyDefend ? FransRiskTolerance.Balanced : FransRiskTolerance.Cautious);
					if (risk.IsCritical)
						continue;
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
				return false;

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
			return true;
		}

		bool HasTransportLossSafeNavalRoute(Actor craft, Mobile mobile, CPos source, CPos destination)
		{
			if (craft == null || mobile == null || mobile.PathFinder is not PathFinder pathFinder)
				return false;

			int NoExtraCost(CPos cell) => 0;
			var path = pathFinder.FindPathToTargetCell(craft, [source], destination,
				BlockedByActor.Immovable, NoExtraCost, laneBias: false);
			return path != null && path.Count > 0 && general.IsTransportLossRouteAllowed(path);
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
			if (amphibiousExpansion?.HasStrategicLandingCraftProductionDemand == true)
				return false;

			if (actor == null || actor.Disposed || !actor.IsInWorld || actor.IsDead || actor.Owner != player || !actor.IsIdle ||
				!Info.LandingCraftTypes.Contains(actor.Info.Name) || transportService.IsTransportReserved(actor) ||
				(amphibiousExpansion?.IsLandingCraftPendingForExpansion(actor) ?? false))
				return false;
			var cargo = actor.TraitOrDefault<Cargo>();
			var mobile = actor.TraitOrDefault<Mobile>();
			return cargo != null && !cargo.IsTraitDisabled && cargo.IsEmpty() && mobile != null && !mobile.IsTraitDisabled && !mobile.IsTraitPaused;
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

				// Extremely cramped beaches may not expose an inland slot. Fall back to the old
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
						BeginConvoyReturn(bot, craft.ActorID);
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
				unit.CancelActivity();
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
					unit.CancelActivity();
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
					unit.CancelActivity();
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
			FransBotLog.BotDebug(world,
				"{0}: GROUND TRANSFER convoy fully/partially boarded ({1} passenger(s)); {2} LST(s) cross toward cached landing slots around {3}. uses bounded recovery: same leg -> local beach alternatives -> retreat to embark shore, never indefinite crossing stall.",
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
						BeginConvoyReturn(bot, craft.ActorID);
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
					craft.CancelActivity();
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
					craft.CancelActivity();
					bot.QueueOrder(new Order("Move", craft, Target.FromCell(world, alternate), false));
					FransBotLog.BotDebug(world,
						"{0}: GROUND TRANSFER LST {1} switches to bounded local landing recovery {2}/{3} at {4}. At most {5} cells are considered; no full shoreline replan.",
						player, craft.ActorID, recoveryAttempt + 1, Info.MaximumCrossingRecoveryAttempts, alternate, Info.CrossingRecoveryCandidateLimit);
					continue;
				}

				BeginConvoyReturn(bot, craft.ActorID);
				return;
			}

			var arrived = wave.Crafts.All(c => wave.TargetCraftSlots.TryGetValue(c, out var target) && (c.Location - target).LengthSquared <= 1);
			if (!arrived)
				return;

			wave.State = TransferState.Unloading;
			wave.StateStartedTick = world.WorldTick;
			wave.LastProgressTick = world.WorldTick;
			wave.NextUnloadRetryTick = world.WorldTick + Info.UnloadRetryInterval;
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

		void BeginConvoyReturn(IBot bot, uint stalledCraftId)
		{
			var wave = activeWave;
			wave.State = TransferState.Returning;
			wave.StateStartedTick = world.WorldTick;
			wave.LastProgressTick = world.WorldTick;
			wave.ReturnUnloadIssued.Clear();
			wave.ReturnLastCargoCount.Clear();
			wave.ReturnLastCargoProgressTick.Clear();
			if (wave.SeaSupportRequestId != 0)
			{
				general.ReleaseSeaTransportBeachSecure(wave.SeaSupportRequestId);
				wave.SeaSupportRequestId = 0;
			}
			ResetCrossingProgress(wave);
			foreach (var craft in wave.Crafts.Where(IsLiveActor).OrderBy(a => a.ActorID))
				if (wave.SourceCraftSlots.TryGetValue(craft, out var slot))
				{
					craft.CancelActivity();
					bot.QueueOrder(new Order("Move", craft, Target.FromCell(world, slot), false));
				}
			FransBotLog.BotDebug(world,
				"{0}: GROUND TRANSFER crossing ABORTS after LST {1} exhausted bounded destination recovery. Surviving convoy retreats to embark shore and unloads its Ground cargo instead of waiting/dying in place.",
				player, stalledCraftId);
		}

		void ManageReturning(IBot bot, Actor[] survivors)
		{
			var wave = activeWave;
			var allAtSource = true;
			foreach (var craft in wave.Crafts.Where(IsLiveActor).OrderBy(a => a.ActorID))
			{
				if (!wave.SourceCraftSlots.TryGetValue(craft, out var slot))
					continue;
				if ((craft.Location - slot).LengthSquared <= 1)
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
					craft.CancelActivity();
					bot.QueueOrder(new Order("Move", craft, Target.FromCell(world, slot), false));
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
					craft.CancelActivity();
					bot.QueueOrder(new Order("Move", craft, Target.FromCell(world, alternate), false));
					continue;
				}

				// Return is already the safe fallback. Keep the final bounded source-side slot and
				// re-issue it instead of starting another expensive strategic replan.
				wave.CrossingLastProgressTick[craft] = world.WorldTick;
				craft.CancelActivity();
				bot.QueueOrder(new Order("Move", craft, Target.FromCell(world, slot), false));
			}

			if (!allAtSource)
				return;

			IssueReturnBeachClearOrders(bot, survivors);
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
				}
				if (!wave.ReturnLastCargoProgressTick.TryGetValue(craft, out var cargoTick))
					wave.ReturnLastCargoProgressTick[craft] = cargoTick = world.WorldTick;
				if ((!wave.ReturnUnloadIssued.Contains(craft) || world.WorldTick - cargoTick >= Info.UnloadStallTimeout) && cargo.CanUnload())
				{
					craft.CancelActivity();
					bot.QueueOrder(new Order("Unload", craft, false));
					wave.ReturnUnloadIssued.Add(craft);
					wave.ReturnLastCargoProgressTick[craft] = world.WorldTick;
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
				wave.CraftUnloadRecoveryAttempts[craft] = 0;
				if (!cargo.CanUnload())
					continue;
				craft.CancelActivity();
				bot.QueueOrder(new Order("Unload", craft, false));
				wave.UnloadIssued.Add(craft);
			}
			FransBotLog.BotDebug(world,
				"{0}: GROUND TRANSFER convoy reached landing screen at {1}/{2}; native Unload is issued independently to {3} craft. tracks cargo progress per LST and may use bounded alternate beach slots if one ramp stalls.",
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
							craft.CancelActivity();
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
						craft.CancelActivity();
						bot.QueueOrder(new Order("Move", craft, Target.FromCell(world, alternate), false));
						FransBotLog.BotDebug(world,
							"{0}: GROUND TRANSFER LST {1} unload stalled with {2} passenger(s); bounded beach recovery {3}/{4} moves to alternate naval cell {5} before another native Unload.",
							player, craft.ActorID, count, attempt + 1, Info.MaximumUnloadRecoveryAttempts, alternate);
						continue;
					}

					// If no alternate is legal, force one clean retry at the current beach instead
					// of waiting forever for IsIdle. A currently progressing Unload is never touched
					// because this branch only runs after UnloadStallTimeout without cargo decrease.
					wave.LastCraftUnloadProgressTick[craft] = world.WorldTick;
					if (cargo.CanUnload())
					{
						craft.CancelActivity();
						bot.QueueOrder(new Order("Unload", craft, false));
					}
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

				// As soon as a passenger materializes on the beach, queue its native Move behind
				// the current unload/disembark activity. This clears the LST ramp without waiting
				// for IsIdle, while preserving OpenRA's native Unload sequencing. Idle units still
				// receive an immediate non-queued retry if their first beach-clear order finished
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

			if (cancelActivities)
			{
				foreach (var unit in wave.Units.Where(a => a != null && a.IsInWorld && !a.IsDead))
					unit.CancelActivity();
				foreach (var craft in wave.Crafts.Where(IsLiveActor))
					craft.CancelActivity();
			}

			foreach (var unit in wave.Units)
				reservedGroundUnits.Remove(unit);
			ReleaseTransports();
			if (wave.SeaSupportRequestId != 0)
				general.ReleaseSeaTransportBeachSecure(wave.SeaSupportRequestId);
			FransBotLog.BotDebug(world,
				"{0}: GROUND TRANSFER CONVOY closes wave {1}->{2}: {3}. LSTs={4}, Sea support request={5}, reserved Ground survivors released={6}.",
				player, wave.SourceLandmassId, wave.TargetLandmassId, reason, wave.Crafts.Count, wave.SeaSupportRequestId,
				wave.Units.Count(a => a != null && !a.Disposed && !a.IsDead));
			activeWave = null;
			nextPlanningTick = world.WorldTick + Info.WaveCooldown;
		}
	}
}
