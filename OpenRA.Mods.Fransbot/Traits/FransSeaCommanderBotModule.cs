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
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Fransbot Sea Commander. Uses the same General auction/mission lifecycle as Ground for DEFEND/SECURE/RECON/RAID. Sea SECURE owns a naval-domain CLEAR check: remembered buildings block only when the committed fleet can physically influence them from reachable water. OpenRA-native naval movement and combat execution.")]
	public class FransSeaCommanderBotModuleInfo : ConditionalTraitInfo
	{
		[ActorReference]
		public readonly FrozenSet<string> ManagedNavalCombatTypes = FrozenSet<string>.Empty;

		[Desc("Unique bidder-capacity key. Ten independent Sea capacities use sea1..sea10 in.")]
		public readonly string BidderKey = "sea1";

		[Desc("Zero-based Sea Commander capacity index. Only index 0 may issue non-General local reaction orders for otherwise-free ships.")]
		public readonly int CommanderIndex = 0;


		[Desc("World ticks between Sea Commander decisions.")]
		public readonly int ScanInterval = 50;

		[Desc("World ticks between expensive full mission-board bid scans while this Sea capacity is idle. Active mission execution remains on ScanInterval; strategic DEFEND bypasses this throttle.")]
		public readonly int IdleBidInterval = 150;

		[Desc("Maximum combat ships committed to the Sea Commander's current General mission.")]
		public readonly int MaximumShipsPerMission = 32;

		[Desc("For normal Sea SECURE, minimum percentage of currently free/reachable Sea combat value committed in addition to 5x observed enemy value. Keeps an existing fleet active instead of sending one-ship probes against nearly empty coasts.")]
		public readonly int SecureFreeFleetCommitPercent = 55;

		[Desc("World ticks a Sea SECURE may make no assembly-count progress before its cached formation is invalidated and cohesion is temporarily relaxed. This watchdog uses cheap cell progress only and never runs pathfinding every tick.")]
		public readonly int SecureAssemblyNoProgressTimeout = 750;

		[Desc("World ticks cohesion holding is bypassed after a Sea SECURE assembly stall so every committed ship may advance toward its own cached/replanned support cell.")]
		public readonly int SecureCohesionBypassTicks = 500;

		[Desc("Distance in cells from the planned sea/support destination at which MOVE becomes FIGHT.")]
		public readonly int FightTriggerRadius = 4;

		[Desc("Local radius used to prefer visible combat threats during FIGHT/DEFEND.")]
		public readonly int FightMicroRadius = 16;

		[Desc("Water-search radius around a land target/objective for a reachable naval support cell.")]
		public readonly int ShoreBombardmentSupportRadius = 18;

		[ActorReference]
		[Desc("Naval combat actor types that may treat a remembered land building as a Sea SECURE blocker when a reachable water firing cell exists within the ship's native maximum weapon range. Pure ship-only submarines are intentionally excluded.")]
		public readonly FrozenSet<string> SecureShoreBombardmentTypes = FrozenSet<string>.Empty;

		[Desc("Maximum age in world ticks of a stationary remembered building RAID that Sea may still bid. The target had to be visible when General originally published the RAID; execution remains bounded local RECON if it is still unseen on arrival.")]
		public readonly int RememberedRaidMaximumAge = 3000;

		[Desc("Minimum number of shore-capable combat ships used for an unseen remembered-building Sea RAID when that many are currently free/reachable.")]
		public readonly int RememberedRaidMinimumShips = 3;

		[Desc("Minimum percentage of currently free/reachable remembered-RAID-capable fleet value committed to one unseen remembered-building Sea RAID. This is a package-sizing floor, not hidden damage estimation.")]
		public readonly int RememberedRaidFreeFleetCommitPercent = 35;

		[Desc("Minimum world ticks before refreshing an unchanged MOVE order.")]
		public readonly int MoveRefreshInterval = 125;

		[Desc("Maximum cells a Sea RAID/SECURE marcher may get ahead of the trailing committed ship before it pauses for cohesion.")]
		public readonly int CohesionMaximumLeadCells = 4;

		[Desc("Temporary maximum lead allowed while the trailing committed ship is stalled in a naval chokepoint; normal cohesion resumes once it moves again.")]
		public readonly int CohesionChokepointLeadCells = 8;

		[Desc("Radius used when assigning distinct nearby naval formation/support cells instead of driving every ship toward the same exact cell.")]
		public readonly int CohesionFormationRadius = 4;

		[Desc("Minimum world ticks before refreshing an unchanged FIGHT attack order.")]
		public readonly int FightRefreshInterval = 75;

		[Desc("How long FIGHT may hold the last visible target cell after contact disappears.")]
		public readonly int FightLostContactHoldTicks = 250;

		[Desc("Cells a combat ship tries to move directly away from a visible land-based attacker each time that attacker damages it.")]
		public readonly int LandFireBackoffCells = 6;

		[Desc("Quiet world ticks without new visible land fire before a ship leaves local backoff mode and resumes its General mission from the new offshore position.")]
		public readonly int LandFireQuietTicks = 125;

		[Desc("Radius around a SECURE objective used to detect visible attackable enemy combat presence.")]
		public readonly int SecureThreatRadius = 14;

		[Desc("Radius around the SECURE objective in which a reachable naval support cell must exist and at least 75 percent of the committed Sea mission group must assemble.")]
		public readonly int SecureAssemblyRadius = 8;

		[Desc("Minimum distance in cells Sea ships keep from a GroundTransfer transport-beach SECURE center so they do not block LST unload ramps. Must be smaller than SecureAssemblyRadius.")]
		public readonly int TransportBeachKeepClearRadius = 5;

		[Desc("World ticks a SECURE area must remain clear while the Sea group is assembled.")]
		public readonly int SecureClearHoldTicks = 250;

		[Desc("World ticks a Sea SECURE reachability/support-cell proof may be reused while target/topology and ship geometry remain stable.")]
		public readonly int SecureCellCacheDuration = 750;

		[Desc("Ship movement in cells beyond this distance invalidates its cached Sea SECURE support-cell proof.")]
		public readonly int SecureCellCacheMovementTolerance = 8;

		[Desc("During FIGHT, retreat when surviving committed Sea combat value falls to this percentage or less of the campaign high-water value.")]
		public readonly int RetreatAtRemainingForcePercent = 50;

		[Desc("After RETREAT, ordinary offensive bidding resumes when this percentage of the locked combat baseline is reassembled.")]
		public readonly int ResumeOffenseAtOriginalForcePercent = 75;

		[Desc("Radius around the retreat point used to count physically regrouped Sea combat value.")]
		public readonly int RetreatAssemblyRadius = 8;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			if (string.IsNullOrWhiteSpace(BidderKey) || CommanderIndex < 0 || CommanderIndex > 9 ||
				ScanInterval < 25 || IdleBidInterval < ScanInterval || MaximumShipsPerMission <= 0 ||
				SecureFreeFleetCommitPercent <= 0 || SecureFreeFleetCommitPercent > 100 ||
				SecureAssemblyNoProgressTimeout < ScanInterval || SecureCohesionBypassTicks < ScanInterval ||
				FightTriggerRadius <= 0 || FightMicroRadius <= 0 ||
				ShoreBombardmentSupportRadius <= 0 || RememberedRaidMaximumAge <= 0 || RememberedRaidMinimumShips <= 0 || RememberedRaidFreeFleetCommitPercent <= 0 || RememberedRaidFreeFleetCommitPercent > 100 || MoveRefreshInterval <= 0 || CohesionMaximumLeadCells <= 0 ||
				CohesionChokepointLeadCells < CohesionMaximumLeadCells || CohesionFormationRadius <= 0 || FightRefreshInterval <= 0 || FightLostContactHoldTicks <= 0 ||
				LandFireBackoffCells <= 0 || LandFireQuietTicks < ScanInterval ||
				SecureThreatRadius <= 0 || SecureAssemblyRadius <= 0 || TransportBeachKeepClearRadius <= 0 || TransportBeachKeepClearRadius >= SecureAssemblyRadius ||
				SecureClearHoldTicks <= 0 || SecureCellCacheDuration <= 0 || SecureCellCacheMovementTolerance < 0 || RetreatAssemblyRadius <= 0 ||
				RetreatAtRemainingForcePercent <= 0 || RetreatAtRemainingForcePercent >= 100 ||
				ResumeOffenseAtOriginalForcePercent <= RetreatAtRemainingForcePercent || ResumeOffenseAtOriginalForcePercent > 100)
				throw new YamlException("Frans Sea Commander timing/radius/retreat values are invalid.");
		}

		public override object Create(ActorInitializer init) { return new FransSeaCommanderBotModule(init.Self, this); }
	}

	public class FransSeaCommanderBotModule : ConditionalTrait<FransSeaCommanderBotModuleInfo>, IBotTick, IBotEnabled, IBotRespondToAttack
	{
		string BidderKey => Info.BidderKey;

		readonly World world;
		readonly Player player;

		readonly HashSet<Actor> pendingStopOrders = [];
		readonly Dictionary<Actor, UnitStance> pendingStanceOrders = [];
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
			if (bot == null || pendingStopOrders.Count == 0 && pendingStanceOrders.Count == 0)
				return;

			foreach (var actor in pendingStopOrders.Concat(pendingStanceOrders.Keys).Distinct().OrderBy(a => a.ActorID).ToArray())
			{
				if (!IsValidOrderSubject(actor))
					continue;

				if (pendingStopOrders.Contains(actor))
					bot.QueueOrder(new Order("Stop", actor, false));

				if (pendingStanceOrders.TryGetValue(actor, out var stance) && actor.TraitOrDefault<AutoTarget>() != null)
					bot.QueueOrder(new Order("SetUnitStance", actor, false) { ExtraData = (uint)stance });
			}

			pendingStopOrders.Clear();
			pendingStanceOrders.Clear();
		}

		readonly HashSet<Actor> activeShips = [];
		readonly Dictionary<Actor, CPos> lastMoveDestination = [];
		readonly Dictionary<Actor, int> lastMoveWorldTick = [];
		readonly Dictionary<Actor, uint> lastFightTarget = [];
		readonly Dictionary<Actor, int> lastFightWorldTick = [];
		readonly Dictionary<Actor, CPos> raidRecoveryOrigins = [];
		readonly HashSet<Actor> raidAttackMoveRecoveryActors = [];
		readonly Dictionary<Actor, CPos> raidMissionOrigins = [];
		readonly HashSet<Actor> cohesionHeldShips = [];
		readonly Dictionary<Actor, CPos> cohesionFormationSlots = [];
		readonly record struct SeaSecureCellCacheKey(uint ShipActorId, CPos TargetCell, int MinimumDistance);
		sealed class SeaSecureCellCacheEntry
		{
			public CPos ShipCell;
			public CPos? Result;
			public int TerrainKnowledgeVersion;
			public int TestedTick;
		}
		readonly Dictionary<SeaSecureCellCacheKey, SeaSecureCellCacheEntry> seaSecureCellCache = [];
		readonly record struct SeaBidTopologyKey(CPos TargetCell, int Radius, int MinimumDistance);
		readonly record struct SeaBidTopologyCell(CPos Cell, int NavalRegionId, int OffshorePreference, int TargetDistanceSquared);
		sealed class SeaBidTopologyCacheEntry
		{
			public int TerrainKnowledgeVersion;
			public SeaBidTopologyCell[] Cells;
		}
		readonly Dictionary<SeaBidTopologyKey, SeaBidTopologyCacheEntry> seaBidTopologyCache = [];
		bool hasCohesionFormationObjective;
		CPos cohesionFormationObjective;
		int cohesionFormationMinimumDistance;

		IFransCombatIntelService combatIntelService;
		IFransRiskModelService riskModelService;
		IFransCommandBidService commandBidService;
		IFransCommanderCoreService commanderCoreService;
		IFransGeneralService generalService;
		IFransStrategicMapService strategicMapService;
		IFransExpansionStateService expansionStateService;
		PathFinder pathFinder;

		int scanTicks;
		int nextIdleBidTick;
		uint activeTargetActorId;
		uint combinedSecureHoldTargetActorId;
		int combinedSecureHoldUntilTick = -1;
		CPos activeObjective;
		CPos activeMoveDestination;
		FransCommanderOrder activeOrder = FransCommanderOrder.Move;
		FransMissionType activeMissionType = FransMissionType.Recon;
		int activeOrderStartedWorldTick;
		int lostContactSinceWorldTick = -1;
		readonly FransSearchSpiral reconSearchSpiral = new();
		readonly FransSearchSpiral raidSearchSpiral = new();
		readonly HashSet<uint> reconLoggedContactIds = [];
		Actor reconActor;
		CPos reconOrigin;
		CPos reconStart;
		CPos reconSearchWaypoint;
		bool hasReconSearchWaypoint;
		bool reconPioneerValidationActive;
		Actor reconRetreatActor;
		CPos reconRetreatOrigin;
		bool hasMoveRiskCheck;
		bool moveRiskAllowed;
		CPos moveRiskDestination;
		int nextMoveRiskCheckTick;
		bool raidStrikeIssued;
		int raidSearchStartedWorldTick = -1;
		CPos raidSearchWaypoint;
		bool hasRaidSearchWaypoint;
		int secureClearSinceWorldTick = -1;
		int secureAssemblyBestCount;
		int secureAssemblyLastProgressTick = -1;
		int secureCohesionBypassUntilTick;
		bool hasLastSafeMoveAnchor;
		CPos lastSafeMoveAnchor;
		bool hasMissionAnchorPoint;
		CPos missionAnchorPoint;
		bool retreatRecoveryActive;
		CPos retreatAnchorPoint;
		int retreatBaselineCombatValue;
		int retreatStartedWorldTick = -1;

		sealed class LandFireEvasionState
		{
			public CPos Destination;
			public int QuietUntilTick;
		}

		readonly Dictionary<Actor, LandFireEvasionState> landFireEvasion = [];
		readonly List<Actor> staleActorCacheKeys = [];

		public FransSeaCommanderBotModule(Actor self, FransSeaCommanderBotModuleInfo info)
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
				?? throw new InvalidOperationException("Sea Commander requires FransCombatIntelBotModule.");
			riskModelService = self.Owner.PlayerActor.TraitsImplementing<IFransRiskModelService>().FirstOrDefault()
				?? throw new InvalidOperationException("Sea Commander requires FransRiskModelBotModule.");
			commandBidService = self.Owner.PlayerActor.TraitsImplementing<IFransCommandBidService>().FirstOrDefault()
				?? throw new InvalidOperationException("Sea Commander requires FransCommandBidBotModule.");
			commanderCoreService = self.Owner.PlayerActor.TraitsImplementing<IFransCommanderCoreService>().FirstOrDefault()
				?? throw new InvalidOperationException("Sea Commander requires FransCommanderCoreBotModule.");
			generalService = self.Owner.PlayerActor.TraitsImplementing<IFransGeneralService>().FirstOrDefault()
				?? throw new InvalidOperationException("Sea Commander requires FransGeneralBotModule.");
			strategicMapService = self.Owner.PlayerActor.TraitsImplementing<IFransStrategicMapService>().FirstOrDefault()
				?? throw new InvalidOperationException("Sea Commander requires FransStrategicMapBotModule.");
			expansionStateService = self.Owner.PlayerActor.TraitsImplementing<IFransExpansionStateService>().FirstOrDefault();
			pathFinder = world.WorldActor.Trait<PathFinder>();
		}

		protected override void TraitEnabled(Actor self)
		{
			// spread the ten Sea capacities across the existing scan cycle so
			// expensive ship refresh/bid/path work no longer lands on one shared tick.
			var basePhase = (int)((self.ActorID + 8u) % (uint)Info.ScanInterval);
			var commanderPhase = Info.CommanderIndex * Info.ScanInterval / 10;
			scanTicks = (basePhase + commanderPhase) % Info.ScanInterval + 1;
			nextIdleBidTick = world.WorldTick + (Info.CommanderIndex * Math.Max(1, Info.IdleBidInterval / 10));
			hasLastSafeMoveAnchor = false;
			hasMissionAnchorPoint = false;
			missionAnchorPoint = default;
			retreatRecoveryActive = false;
			retreatAnchorPoint = default;
			retreatBaselineCombatValue = 0;
			retreatStartedWorldTick = -1;
			ResetMission();
			FransBotLog.BotDebug(world,
				"{0}: Sea Commander COMBINED SECURE + STRICT LAND-FIRE BACKOFF capacity {1} (index {2}) active. Normal SECURE requires max(5x observed enemy value, {9}% of the bounded free/reachable fleet value). Idle bidding remains topology-only with no native A* path proof in SubmitBids. Direct attackers remain first priority; an unexpected attackable naval defender becomes a local FIGHT without releasing the RAID, then SYRD/SPEN interdiction remains ahead of harvesters/ordinary buildings. Replay hardening makes land/shore fire unambiguous: every visible non-air attacker that is not a configured naval combat type goes to plain-Move BACKOFF, never RAID LOCAL FIGHT. The ship moves roughly {12} cells straight away, extends on each new hit, and resumes after {13} quiet WT. For COMBINED SECURE, Sea may delay launch toward the shared arrival time and releases locally when naval support is clear; Ground remains territorial authority. Fresh remembered stationary-building RAID snapshots remain eligible for {14} WT and use a bounded {15}% free-fleet package floor with at least {16} shore-capable ships when available; no hidden target state is read. No new strategic shore-risk planner is added. GroundTransfer remains decoupled; transport-beach SECURE keeps the {8}-cell landing exclusion ring. RECON uses {3}-waypoint plain-Move probing with {4}% retreat; normal/chokepoint cohesion leads remain {5}/{6} cells.",
				player, BidderKey, Info.CommanderIndex, commanderCoreService.ReconWaypointBatchSize, commanderCoreService.ReconRetreatHealthPercent,
				Info.CohesionMaximumLeadCells, Info.CohesionChokepointLeadCells, Info.ScanInterval, Info.TransportBeachKeepClearRadius,
				Info.SecureFreeFleetCommitPercent, Info.SecureAssemblyNoProgressTimeout, Info.SecureCohesionBypassTicks,
				Info.LandFireBackoffCells, Info.LandFireQuietTicks, Info.RememberedRaidMaximumAge,
				Info.RememberedRaidFreeFleetCommitPercent, Info.RememberedRaidMinimumShips);
		}

		protected override void TraitDisabled(Actor self)
		{
			pendingStopOrders.Clear();
			pendingStanceOrders.Clear();
			activeShips.Clear();
			lastMoveDestination.Clear();
			lastMoveWorldTick.Clear();
			lastFightTarget.Clear();
			lastFightWorldTick.Clear();
			raidRecoveryOrigins.Clear();
			raidAttackMoveRecoveryActors.Clear();
			raidMissionOrigins.Clear();
			cohesionHeldShips.Clear();
			cohesionFormationSlots.Clear();
			seaSecureCellCache.Clear();
			seaBidTopologyCache.Clear();
			landFireEvasion.Clear();
			staleActorCacheKeys.Clear();
			hasCohesionFormationObjective = false;
			cohesionFormationObjective = default;
			reconRetreatActor = null;
			reconRetreatOrigin = default;
			hasLastSafeMoveAnchor = false;
			hasMissionAnchorPoint = false;
			missionAnchorPoint = default;
			retreatRecoveryActive = false;
			retreatAnchorPoint = default;
			retreatBaselineCombatValue = 0;
			retreatStartedWorldTick = -1;
			commandBidService?.UpdateTransientActorReservations(FransCommanderKind.Sea, BidderKey, Array.Empty<uint>());
			ResetMission();
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
			PruneDeadActorKeys(lastFightWorldTick);
			PruneDeadActorKeys(raidRecoveryOrigins);
			PruneDeadActorKeys(raidMissionOrigins);
			PruneDeadActorKeys(cohesionFormationSlots);
			PruneDeadActorKeys(landFireEvasion);
			raidAttackMoveRecoveryActors.RemoveWhere(a => a == null || a.IsDead);
			cohesionHeldShips.RemoveWhere(a => a == null || a.IsDead);
			staleActorCacheKeys.Clear();
		}

		void IBotTick.BotTick(IBot bot)
		{
			FlushPendingSynchronizedActions(bot);
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransSeaCommander.BotTick");
			if (player.WinState != WinState.Undefined)
				return;

			if (--scanTicks > 0)
				return;
			scanTicks = Info.ScanInterval;

			combatIntelService.EnsureCurrentSnapshot();
			PruneDeadActorOrderState();
			var ships = combatIntelService.OwnedActors.Where(IsManagedShip).OrderBy(a => a.ActorID).ToArray();
			activeShips.RemoveWhere(a => !ships.Contains(a));
			MaintainReconRetreat(bot, ships);
			MaintainRaidRecovery(bot, ships);
			var landFireBackingOff = MaintainLandFireEvasion(bot, ships);
			PublishTransientReservations();
			if (ships.Length == 0)
			{
				if (commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.Sea, BidderKey,
					out _, out var emptyMission))
				{
					if (emptyMission.MissionType == FransMissionType.Recon)
					{
						commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey, "RECON ship died during persistent probing; no managed Sea unit remains");
						FransBotLog.BotDebug(world,
							"{0}: Sea RECON MineCluster {1} lost its final ship during persistent probing; General keeps the target open for rebid.",
							player, emptyMission.TargetActorId);
					}
					else if (emptyMission.MissionType == FransMissionType.Raid)
					{
						commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey, "RAID force was wiped out");
						generalService.ReportRaidRetreat(emptyMission.TargetActorId, "Sea RAID force was wiped out");
					}
					else if (emptyMission.MissionType == FransMissionType.Secure)
					{
						commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey, "SECURE force was wiped out");
						ReportSecureRetreatIfLast(emptyMission.TargetActorId, "Sea SECURE force was wiped out");
					}
				}

				retreatRecoveryActive = false;
				retreatStartedWorldTick = -1;
				retreatAnchorPoint = default;
				retreatBaselineCombatValue = 0;
				ResetMission();
				return;
			}

			// Local shore-fire survival temporarily owns this capacity's orders. Other committed
			// ships keep their already-issued native orders; the damaged ship simply opens range.
			if (landFireBackingOff)
				return;

			if (!retreatRecoveryActive && activeOrder == FransCommanderOrder.Fight &&
				ShouldRetreatFromFight(ships, out var collapsedFightValue))
			{
				BeginRetreat(bot, ships, collapsedFightValue);
				return;
			}

			if (retreatRecoveryActive)
			{
				// recovery is committed survival work; DEFEND may use IDLE or SECURE capacity only.
				ExecuteRetreatRecovery(bot, ships);
				return;
			}

			// an accepted capacity owns its exact committed actor snapshot.
			// Commanders do not re-bid while a MISSION is active and the broker does not preempt.
			if (commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.Sea, BidderKey,
				out var target, out var mission))
			{
				ExecuteMission(bot, ships, target, mission);
				return;
			}

			var urgentDefendBid = commandBidService.IsStrategicDefendPressureActive();
			if (!urgentDefendBid && world.WorldTick < nextIdleBidTick)
				return;
			if (!urgentDefendBid)
				nextIdleBidTick = world.WorldTick + Info.IdleBidInterval;

			SubmitBids(ships);
			if (commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.Sea, BidderKey,
				out target, out mission))
			{
				ExecuteMission(bot, ships, target, mission);
				return;
			}

			if (activeMissionType == FransMissionType.Raid && activeTargetActorId != 0)
				StartRaidAttackMoveReturn(bot, "RAID mission disappeared / target completed");
			ResetMission();
		}

		void PublishTransientReservations()
		{
			var ids = new HashSet<uint>();
			if (reconRetreatActor != null && reconRetreatActor.IsInWorld && !reconRetreatActor.IsDead)
				ids.Add(reconRetreatActor.ActorID);
			foreach (var actor in raidRecoveryOrigins.Keys)
				if (actor != null && actor.IsInWorld && !actor.IsDead)
					ids.Add(actor.ActorID);
			foreach (var actor in landFireEvasion.Keys)
				if (actor != null && actor.IsInWorld && !actor.IsDead)
					ids.Add(actor.ActorID);
			if (retreatRecoveryActive)
				foreach (var actor in activeShips)
					if (actor != null && actor.IsInWorld && !actor.IsDead)
						ids.Add(actor.ActorID);
			commandBidService.UpdateTransientActorReservations(FransCommanderKind.Sea, BidderKey, ids);
		}

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			if (self == null || !IsManagedShip(self) || e.Attacker == null ||
				(e.Attacker.Info.HasTraitInfo<HuskInfo>() || e.Attacker.Info.Name.EndsWith(".husk", StringComparison.OrdinalIgnoreCase)))
				return;

			var missionMember = activeShips.Contains(self);
			if (!missionMember && (Info.CommanderIndex != 0 ||
				!commanderCoreService.IsActorAvailableForBidder(FransCommanderKind.Sea, BidderKey, self)))
				return;

			if (missionMember && activeMissionType == FransMissionType.Recon &&
				(activeOrder == FransCommanderOrder.Move || activeOrder == FransCommanderOrder.Search) && IsEnemyActor(e.Attacker))
			{
				BeginReconRetreat(bot, self, "recon ship received hostile damage");
				return;
			}

			if (!IsVisibleEnemy(e.Attacker))
				return;

			// Keep shore reaction deliberately simple: do not invent a second strategic risk
			// planner. If visible land fire is actually hurting this ship, move straight away
			// from that attacker. A new hit extends the same local backoff farther offshore.
			if (IsLandBasedAttacker(e.Attacker))
			{
				BeginLandFireEvasion(bot, self, e.Attacker);
				return;
			}

			if (missionMember && activeMissionType == FransMissionType.Raid)
			{
				var expected = commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.Sea, BidderKey, out _, out var raidMission) &&
					commanderCoreService.IsExpectedRaidContact(raidMission, e.Attacker);
				if (!expected)
				{
					var canCounterattack = activeShips.Any(ship => ship != null && ship.IsInWorld && !ship.IsDead && CanAttackActor(ship, e.Attacker));
					if (!canCounterattack)
					{
						CloseRaid(bot, $"unexpected NEW defense {e.Attacker.Info.Name} {e.Attacker.ActorID} is attacking the RAID but no committed Sea ship can return fire", true);
						return;
					}

					BeginFight();
					if (CanAttackActor(self, e.Attacker))
						QueueAttack(bot, self, e.Attacker, true);
					FransBotLog.BotDebug(world,
						"{0}: Sea RAID LOCAL FIGHT: unexpected visible {1} {2} attacked {3}; the same RAID stays owned, direct combat threat becomes first target, and the original mission resumes after the attacker is neutralized.",
						player, e.Attacker.Info.Name, e.Attacker.ActorID, self);
				}
				// Expected SiteIntel resistance was already part of the accepted MISSION. Unexpected
				// attackable naval resistance becomes a short local FIGHT instead of an automatic abort.
				return;
			}

			if (missionMember && activeOrder == FransCommanderOrder.Move)
			{
				BeginFight();
				FransBotLog.BotDebug(world,
					"{0}: Sea Commander MOVE -> FIGHT because {1} was attacked by visible {2} {3}; RiskModel is ignored. Combat baseline {4}, fallback {5}.",
					player, self, e.Attacker.Info.Name, e.Attacker.ActorID, retreatBaselineCombatValue, retreatAnchorPoint);
			}
			if (CanAttackActor(self, e.Attacker))
				QueueAttack(bot, self, e.Attacker, true);
		}

		bool IsLandBasedAttacker(Actor attacker)
		{
			if (!IsVisibleEnemy(attacker) || attacker.Info.HasTraitInfo<AircraftInfo>())
				return false;

			// Simple ownership rule from replay validation: every visible non-air attacker
			// that is not one of the configured naval combat types is shore/land fire.
			// It therefore gets BACKOFF, never RAID LOCAL FIGHT. This avoids shoreline
			// region geometry accidentally classifying infantry/tanks as naval threats.
			return !Info.ManagedNavalCombatTypes.Contains(attacker.Info.Name);
		}

		bool TryFindLandFireBackoffCell(Actor ship, CPos threatCell, out CPos destination)
		{
			destination = default;
			var mobile = ship?.TraitOrDefault<Mobile>();
			if (mobile == null || !strategicMapService.TryGetNavalRegionId(ship.Location, out var shipRegion))
				return false;

			var awayX = ship.Location.X - threatCell.X;
			var awayY = ship.Location.Y - threatCell.Y;
			var stepX = Math.Sign(awayX);
			var stepY = Math.Sign(awayY);
			if (stepX == 0 && stepY == 0)
				return false;

			var ideal = new CPos(ship.Location.X + stepX * Info.LandFireBackoffCells,
				ship.Location.Y + stepY * Info.LandFireBackoffCells);
			var currentThreatDistance = (ship.Location - threatCell).LengthSquared;
			var searchRadius = Info.LandFireBackoffCells + 2;
			var candidate = world.Map.FindTilesInCircle(ship.Location, searchRadius)
				.Where(world.Map.Contains)
				.Where(c => (c - threatCell).LengthSquared > currentThreatDistance)
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.Where(c => strategicMapService.TryGetNavalRegionId(c, out var region) && region == shipRegion)
				.OrderBy(c => (c - ideal).LengthSquared)
				.ThenByDescending(c => (c - threatCell).LengthSquared)
				.ThenBy(c => c.X)
				.ThenBy(c => c.Y)
				.Select(c => (CPos?)c)
				.FirstOrDefault();
			if (!candidate.HasValue)
				return false;

			destination = candidate.Value;
			return true;
		}

		bool BeginLandFireEvasion(IBot bot, Actor ship, Actor attacker)
		{
			if (!TryFindLandFireBackoffCell(ship, attacker.Location, out var destination))
				return false;

			var first = !landFireEvasion.TryGetValue(ship, out var state);
			if (first)
			{
				state = new LandFireEvasionState();
				landFireEvasion.Add(ship, state);
			}

			state.Destination = destination;
			state.QuietUntilTick = world.WorldTick + Info.LandFireQuietTicks;
			QueueMove(bot, ship, destination, true);

			if (first)
				FransBotLog.BotDebug(world,
					"{0}: Sea LAND-FIRE BACKOFF {1} {2}: visible {3} {4} at {5} damaged the ship; plain Move goes away to {6}. Each new land hit silently extends the backoff; after {7} quiet WT Sea resumes the same mission from the new position.",
					player, ship.Info.Name, ship.ActorID, attacker.Info.Name, attacker.ActorID, attacker.Location, destination, Info.LandFireQuietTicks);
			return true;
		}

		bool MaintainLandFireEvasion(IBot bot, IReadOnlyCollection<Actor> ships)
		{
			var any = false;
			foreach (var ship in landFireEvasion.Keys.ToArray())
			{
				if (ship == null || !ship.IsInWorld || ship.IsDead || !ships.Contains(ship))
				{
					landFireEvasion.Remove(ship);
					continue;
				}

				var state = landFireEvasion[ship];
				if (world.WorldTick >= state.QuietUntilTick)
				{
					landFireEvasion.Remove(ship);
					FransBotLog.BotDebug(world,
						"{0}: Sea LAND-FIRE BACKOFF complete for {1} {2} at {3}: no new visible land hit for {4} WT. Sea resumes normal mission ownership from here.",
						player, ship.Info.Name, ship.ActorID, ship.Location, Info.LandFireQuietTicks);
					continue;
				}

				any = true;
				// The damage callback already issued the Move. Reassert only if native movement
				// unexpectedly went idle before reaching the chosen farther-water cell.
				if (ship.IsIdle && ship.Location != state.Destination)
					QueueMove(bot, ship, state.Destination, false);
			}

			return any;
		}

		// Cameo port: upstream ladder was RA ids (syrd/spen/agun/sam/tsla/gun/ftur/harv/fact/proc).
		// Trait ladder preserves the ordering: naval producers < AA defense < other defense
		// < harvester < conyard << refinery.
		int GetSeaTargetPriorityRank(string actorType)
		{
			if (actorType != null
				&& (world.Map.Rules.Actors.TryGetValue(actorType, out var info)
					|| world.Map.Rules.Actors.TryGetValue(actorType.ToLowerInvariant(), out info)))
			{
				if (FransActorClass.IsNavalProducer(info))
					return 0;
				if (FransActorClass.IsDefense(info) && FransActorClass.WeaponTargets(info, world.Map.Rules, "air"))
					return 2;
				if (FransActorClass.IsDefense(info))
					return 5;
				if (FransActorClass.IsHarvester(info))
					return 6;
				if (FransActorClass.IsConyard(info))
					return 7;
				if (FransActorClass.IsRefinery(info))
					return 50;
			}
			else if (string.Equals(actorType, "fact", StringComparison.OrdinalIgnoreCase))
				return 7; // SECURE-conyard mission token.

			return 20;
		}

		int ApplyRaidTargetPriorityToPrice(int basePrice, string actorType)
		{
			if (basePrice == int.MaxValue)
				return int.MaxValue;
			const int PriorityBandCost = 1000000;
			var ranked = (long)GetSeaTargetPriorityRank(actorType) * PriorityBandCost + Math.Max(1, basePrice);
			return (int)Math.Min(int.MaxValue - 1L, ranked);
		}

		static bool IsTransportBeachSecure(string actorType) => actorType == FransGeneralBotModule.SeaTransportBeachSecureTargetType;

		void SubmitBids(IReadOnlyCollection<Actor> ships)
		{
			using var bidPerf = FransBotLog.Profile(world, player, "Sea.SubmitBids");
			if (ships.Count == 0)
				return;

			generalService.EnsureCurrentMissions();
			foreach (var mission in generalService.CurrentMissions)
			{
				if (mission.Type == FransMissionType.Secure &&
					commandBidService.ShouldPreemptSecureForDefend(FransCommanderKind.Sea, BidderKey, mission.LastVisibleTargetCell))
					continue;
				var target = mission.Target;
				var targetCell = mission.LastVisibleTargetCell;

				if (mission.Type == FransMissionType.Secure &&
					generalService.TryGetDomainSecureClearWorldTick(mission.TargetActorId, FransCommanderKind.Sea, out var seaClearWorldTick) &&
					!HasNewSeaSecureIntelSince(mission, seaClearWorldTick, ships))
					continue;

				if (mission.Type == FransMissionType.Raid)
				{
					var visibleRaid = target != null && IsVisibleEnemy(target);
					var rememberedBuildingRaid = !visibleRaid && mission.IsRememberedIntel && mission.IsBuilding &&
						world.WorldTick - mission.PublishedWorldTick <= Info.RememberedRaidMaximumAge;
					if (!visibleRaid && !rememberedBuildingRaid)
						continue;
					var required = commanderCoreService.GetMissionRequiredContribution(FransCommanderKind.Sea, mission);
					if (required == int.MaxValue)
						continue;

					if (rememberedBuildingRaid)
					{
						// Sea may act on fresh remembered STATIONARY building intel. The exact target was
						// visible when General published the RAID; no hidden HP/position is read here.
						// Because exact armor-aware strike damage cannot be recomputed while hidden, size a
						// bounded shore-bombardment package from the currently free reachable fleet. Execution
						// moves to LastVisibleTargetCell and uses the existing bounded local RECON before strike.
						var rememberedRanked = ships
							.Where(ship => commanderCoreService.IsActorAvailableForMissionBid(FransCommanderKind.Sea, BidderKey, ship))
							.Where(ship => ship != reconRetreatActor && !raidRecoveryOrigins.ContainsKey(ship) && ship.TraitOrDefault<Cargo>() == null)
							.Where(ship => Info.SecureShoreBombardmentTypes.Contains(ship.Info.Name))
							.Select(ship =>
							{
								var destination = FindRememberedRaidBidFiringPosition(ship, targetCell);
								if (!destination.HasValue)
									return (Actor: ship, Destination: (CPos?)null, Eta: int.MaxValue, Price: int.MaxValue, Route: default(FransRouteRiskAssessment), Cost: 0);
								var eta = commanderCoreService.EstimateMoveEtaTicks(ship, destination.Value);
								var route = riskModelService.EvaluateDirectRoute(ship, ship.Location, destination.Value, FransRiskRole.NavalCombat, FransRiskTolerance.Balanced);
								var cost = GetCombatValue(ship);
								var price = commanderCoreService.PriceBid(FransCommanderKind.Sea, route.PeakScore, eta, cost);
								return (Actor: ship, Destination: destination, Eta: eta, Price: price, Route: route, Cost: cost);
							})
							.Where(x => x.Destination.HasValue && x.Eta != int.MaxValue && x.Price != int.MaxValue && !x.Route.IsCritical)
							.OrderBy(x => x.Price).ThenBy(x => x.Eta).ThenByDescending(x => x.Cost).ThenBy(x => x.Actor.ActorID)
							.Take(Info.MaximumShipsPerMission).ToArray();
						if (rememberedRanked.Length == 0)
							continue;

						var freeFleetValue = Math.Max(1, rememberedRanked.Sum(x => x.Cost));
						var packageFloor = Math.Max(1, freeFleetValue * Info.RememberedRaidFreeFleetCommitPercent / 100);
						var minimumShips = Math.Min(Info.RememberedRaidMinimumShips, rememberedRanked.Length);
						var chosen = new List<Actor>();
						var slowestEta = 0;
						var peakRisk = 0;
						var travel = 0;
						var totalCost = 0;
						foreach (var x in rememberedRanked)
						{
							chosen.Add(x.Actor);
							slowestEta = Math.Max(slowestEta, x.Eta);
							peakRisk = Math.Max(peakRisk, x.Route.PeakScore);
							travel = Math.Max(travel, Math.Abs(x.Destination.Value.X - x.Actor.Location.X) + Math.Abs(x.Destination.Value.Y - x.Actor.Location.Y));
							totalCost += x.Cost;
							if (chosen.Count >= minimumShips && totalCost >= packageFloor)
								break;
						}
						if (chosen.Count < minimumShips || totalCost < packageFloor)
							continue;
						var groupPrice = commanderCoreService.PriceBid(FransCommanderKind.Sea, peakRisk, slowestEta, totalCost);
						if (groupPrice == int.MaxValue)
							continue;
						groupPrice = ApplyRaidTargetPriorityToPrice(groupPrice, mission.TargetActorType);
						commandBidService.SubmitMissionBid(mission, new FransCommanderBidReport(
							FransCommanderKind.Sea, BidderKey, chosen[0].ActorID, chosen.Select(a => a.ActorID).ToArray(),
							groupPrice, peakRisk, travel, totalCost, slowestEta, required, required, false));
						FransBotLog.BotDebug(world,
							"{0}: Sea {1} bids fresh REMEMBERED BUILDING RAID {2} {3} at {4}: {5} shore-capable ships, package value {6}/{7} free-fleet floor, intel age {8}/{9} WT. No hidden target state is read; arrival uses bounded local RECON before any strike.",
							player, BidderKey, mission.TargetActorType, mission.TargetActorId, targetCell, chosen.Count, totalCost, packageFloor,
							world.WorldTick - mission.PublishedWorldTick, Info.RememberedRaidMaximumAge);
						continue;
					}

					var ranked = ships
						.Where(ship => commanderCoreService.IsActorAvailableForMissionBid(FransCommanderKind.Sea, BidderKey, ship))
						.Where(ship => ship != reconRetreatActor && !raidRecoveryOrigins.ContainsKey(ship) && ship.TraitOrDefault<Cargo>() == null && CanAttackActor(ship, target))
						.Select(ship =>
						{
							var destination = FindRaidBidFiringPosition(ship, target);
							if (!destination.HasValue)
								return (Actor: ship, Destination: (CPos?)null, Eta: int.MaxValue, Contribution: 0, Price: int.MaxValue, Route: default(FransRouteRiskAssessment), Cost: 0);
							var eta = commanderCoreService.EstimateMoveEtaTicks(ship, destination.Value);
							var contribution = commanderCoreService.EstimateRaidContribution(FransCommanderKind.Sea, ship, target);
							var route = riskModelService.EvaluateDirectRoute(ship, ship.Location, destination.Value, FransRiskRole.NavalCombat, FransRiskTolerance.Balanced);
							var price = commanderCoreService.PriceBid(FransCommanderKind.Sea, route.PeakScore, eta, GetCombatValue(ship));
							return (Actor: ship, Destination: destination, Eta: eta, Contribution: contribution, Price: price, Route: route, Cost: GetCombatValue(ship));
						})
						.Where(x => x.Destination.HasValue && x.Eta != int.MaxValue && x.Contribution > 0 && x.Price != int.MaxValue && !x.Route.IsCritical)
						.OrderBy(x => x.Price).ThenBy(x => x.Eta).ThenByDescending(x => x.Cost).ThenBy(x => x.Actor.ActorID)
						.Take(Info.MaximumShipsPerMission).ToArray();
					if (ranked.Length == 0)
						continue;

					var chosenVisible = new List<Actor>();
					var offered = 0;
					var slowestEtaVisible = 0;
					var peakRiskVisible = 0;
					var travelVisible = 0;
					var totalCostVisible = 0;
					foreach (var x in ranked)
					{
						chosenVisible.Add(x.Actor);
						offered = (int)Math.Min(int.MaxValue, (long)offered + x.Contribution);
						slowestEtaVisible = Math.Max(slowestEtaVisible, x.Eta);
						peakRiskVisible = Math.Max(peakRiskVisible, x.Route.PeakScore);
						travelVisible = Math.Max(travelVisible, Math.Abs(x.Destination.Value.X - x.Actor.Location.X) + Math.Abs(x.Destination.Value.Y - x.Actor.Location.Y));
						totalCostVisible += x.Cost;
						if (offered >= required)
							break;
					}
					var groupPriceVisible = commanderCoreService.PriceBid(FransCommanderKind.Sea, peakRiskVisible, slowestEtaVisible, totalCostVisible);
					if (groupPriceVisible == int.MaxValue)
						continue;
					groupPriceVisible = ApplyRaidTargetPriorityToPrice(groupPriceVisible, mission.TargetActorType);
					commandBidService.SubmitMissionBid(mission, new FransCommanderBidReport(
						FransCommanderKind.Sea, BidderKey, chosenVisible[0].ActorID, chosenVisible.Select(a => a.ActorID).ToArray(),
						groupPriceVisible, peakRiskVisible, travelVisible, totalCostVisible, slowestEtaVisible, offered, required, false));
					continue;
				}

				if (mission.Type == FransMissionType.Recon)
				{
					var best = ships
						.Where(ship => commanderCoreService.IsActorAvailableForMissionBid(FransCommanderKind.Sea, BidderKey, ship))
						.Where(commanderCoreService.IsReconCandidateOperational)
						.Where(ship => ship != reconRetreatActor && !raidRecoveryOrigins.ContainsKey(ship) && ship.TraitOrDefault<Cargo>() == null)
						.Where(ship => !ReconHealthBelowRetreatThreshold(ship, out _))
						.Select(ship =>
						{
							var destination = FindSeaReconCell(ship, targetCell);
							if (!destination.HasValue)
								return (Actor: ship, Destination: (CPos?)null, Eta: int.MaxValue, Price: int.MaxValue, Vision: 0);
							var eta = commanderCoreService.EstimateReconEtaTicks(ship, destination.Value);
							var price = commanderCoreService.PriceReconBid(FransCommanderKind.Sea, ship, eta);
							return (Actor: ship, Destination: destination, Eta: eta, Price: price, Vision: commanderCoreService.GetReconVisionCells(ship));
						})
						.Where(x => x.Destination.HasValue && x.Eta != int.MaxValue && x.Price != int.MaxValue && x.Vision > 0)
						.OrderBy(x => x.Price).ThenBy(x => x.Eta).ThenBy(x => x.Actor.ActorID).FirstOrDefault();
					if (best.Actor == null)
						continue;
					var travel = Math.Abs(best.Destination.Value.X - best.Actor.Location.X) + Math.Abs(best.Destination.Value.Y - best.Actor.Location.Y);
					commandBidService.SubmitMissionBid(mission, new FransCommanderBidReport(
						FransCommanderKind.Sea, BidderKey, best.Actor.ActorID, new[] { best.Actor.ActorID },
						best.Price, 0, travel, GetCombatValue(best.Actor), best.Eta, 1, 1, false));
					continue;
				}

				var secureKeepClear = mission.Type == FransMissionType.Secure && IsTransportBeachSecure(mission.TargetActorType)
					? Info.TransportBeachKeepClearRadius : 0;
				var eligibleCandidates = ships
					.Where(ship => commanderCoreService.IsActorAvailableForMissionBid(FransCommanderKind.Sea, BidderKey, ship))
					.Where(ship => ship != reconRetreatActor && !raidRecoveryOrigins.ContainsKey(ship))
					.Where(ship => mission.Type == FransMissionType.Defend || target == null || CanAttackActor(ship, target))
					.Select(ship => (Actor: ship, Destination: mission.Type == FransMissionType.Secure
						? FindSeaSecureBidCell(ship, targetCell, secureKeepClear)
						: mission.Type == FransMissionType.Defend
							? FindRememberedMoveDestination(ship, targetCell, mission.IsBuilding)
							: target != null ? FindMoveDestination(ship, target) : FindRememberedMoveDestination(ship, targetCell, mission.IsBuilding)))
					.Where(x => x.Destination.HasValue)
					.OrderBy(x => (x.Actor.Location - targetCell).LengthSquared).ThenBy(x => x.Actor.ActorID);
				var candidates = (mission.Type == FransMissionType.Defend
					? eligibleCandidates
					: eligibleCandidates.Take(Info.MaximumShipsPerMission)).ToArray();
				if (candidates.Length == 0)
					continue;

				var chosenNormal = new List<(Actor Actor, CPos? Destination)>();
				var offeredNormal = 0;
				int requiredNormal;
				if (mission.Type == FransMissionType.Defend)
				{
					var desiredUnitCount = commanderCoreService.GetDefendRequiredUnitCount(mission);
					var commitCount = Math.Min(desiredUnitCount, candidates.Length);
					chosenNormal.AddRange(candidates.Take(commitCount));
					offeredNormal = chosenNormal.Count;
					// Preserve the real 3x requirement so broker arbitration can compare
					// full/partial DEFEND strength before ETA.
					requiredNormal = desiredUnitCount;
				}
				else
				{
					var observedRequired = commanderCoreService.GetMissionRequiredContribution(FransCommanderKind.Sea, mission);
					if (mission.Type == FransMissionType.Secure)
					{
						var observedScaled = Math.Clamp((long)observedRequired * 5L, 1L, int.MaxValue);
						var freeFleetValue = candidates.Sum(x => (long)GetCombatValue(x.Actor));
						var proportionalCommit = Math.Max(1L, (long)freeFleetValue * Info.SecureFreeFleetCommitPercent / 100L);
						requiredNormal = (int)Math.Min(int.MaxValue, Math.Max(observedScaled, proportionalCommit));
					}
					else
						requiredNormal = observedRequired;
					foreach (var candidate in candidates)
					{
						chosenNormal.Add(candidate);
						offeredNormal = (int)Math.Min(int.MaxValue, (long)offeredNormal + GetCombatValue(candidate.Actor));
						if (offeredNormal >= requiredNormal)
							break;
					}
				}
				var subject = chosenNormal[0];
				var routeRisk = 0;
				var travelNormal = 0;
				var eta = 0;
				var routeBlocked = false;
				foreach (var selected in chosenNormal)
				{
					var route = riskModelService.EvaluateDirectRoute(selected.Actor, selected.Actor.Location, selected.Destination.Value,
						FransRiskRole.NavalCombat, FransRiskTolerance.Balanced);
					if (mission.Type != FransMissionType.Defend && route.IsCritical)
					{
						routeBlocked = true;
						break;
					}
					routeRisk = Math.Max(routeRisk, route.PeakScore);
					travelNormal = Math.Max(travelNormal,
						Math.Abs(selected.Destination.Value.X - selected.Actor.Location.X) + Math.Abs(selected.Destination.Value.Y - selected.Actor.Location.Y));
					eta = Math.Max(eta, commanderCoreService.EstimateMoveEtaTicks(selected.Actor, selected.Destination.Value));
				}
				if (routeBlocked || eta == int.MaxValue)
					continue;
				var force = chosenNormal.Sum(x => GetCombatValue(x.Actor));
				var price = commanderCoreService.PriceBid(FransCommanderKind.Sea, routeRisk, eta, force);
				var defendScore = mission.Type == FransMissionType.Defend
					? commanderCoreService.ScoreDefendResponse(mission, offeredNormal, requiredNormal, eta, force)
					: default;
				commandBidService.SubmitMissionBid(mission, new FransCommanderBidReport(
					FransCommanderKind.Sea, BidderKey, subject.Actor.ActorID, chosenNormal.Select(x => x.Actor.ActorID).ToArray(),
					price, routeRisk, travelNormal, force, eta, offeredNormal, requiredNormal, false,
					defendScore.Utility, defendScore.StrengthScore, defendScore.UrgencyScore, defendScore.AssetRiskScore,
					defendScore.ResponseTimeCost, defendScore.OpportunityCost));
			}
		}

		void ExecuteMission(IBot bot, IReadOnlyCollection<Actor> ships, Actor target, FransActiveMission mission)
		{
			RememberMissionAnchor(mission);
			if (mission.MissionType == FransMissionType.Secure)
			{
				ExecuteSecureMission(bot, ships, mission);
				return;
			}

			if (mission.MissionType == FransMissionType.Recon)
			{
				ExecuteReconMission(bot, ships, mission);
				return;
			}
			if (mission.MissionType == FransMissionType.Raid)
			{
				ExecuteRaidMission(bot, ships, target, mission);
				return;
			}

			activeMissionType = mission.MissionType;
			ResetReconState();
			var changed = activeTargetActorId != mission.TargetActorId;
			if (changed)
			{
				activeTargetActorId = mission.TargetActorId;
				activeObjective = mission.LastVisibleTargetCell;
				activeOrder = mission.InitialOrder;
				activeOrderStartedWorldTick = world.WorldTick;
				lostContactSinceWorldTick = -1;
				activeShips.Clear();
				var committed = (mission.CommittedActorIds ?? Array.Empty<uint>())
					.Select(id => ships.FirstOrDefault(s => s.ActorID == id && s != reconRetreatActor && !raidRecoveryOrigins.ContainsKey(s)))
					.Where(s => s != null).ToArray();
				if (committed.Length != mission.CommittedActorIds.Length || committed.Length == 0)
				{
					commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey, "exact committed Sea actor snapshot is no longer available");
					ResetMission();
					return;
				}
				foreach (var ship in committed)
					activeShips.Add(ship);
				if (activeShips.Count > 0)
				{
					var lead = activeShips.OrderBy(s => s.ActorID == mission.SubjectActorId ? 0 : 1).First();
					activeMoveDestination = target != null
						? FindMoveDestination(lead, target) ?? activeObjective
						: FindRememberedMoveDestination(lead, mission.LastVisibleTargetCell, mission.TargetIsBuilding) ?? activeObjective;
				}
				else
					activeMoveDestination = activeObjective;
				FransBotLog.BotDebug(world,
					"{0}: Sea Commander accepts MISSION {1} for target {2} at {3}; {4} ship(s), move destination {5}, cost {6}.",
					player, activeOrder, mission.TargetActorId, activeObjective, activeShips.Count, activeMoveDestination, mission.TotalCost);
			}
			activeShips.RemoveWhere(s => !ships.Contains(s));
			if (activeShips.Count == 0)
			{
				commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey, "no Sea Commander ships remain");
				ResetMission();
				return;
			}

			if (target != null && IsVisibleEnemy(target))
			{
				activeObjective = target.Location;
				activeMoveDestination = FindMoveDestination(activeShips.First(), target) ?? activeMoveDestination;
				lostContactSinceWorldTick = -1;
			}
			else if (lostContactSinceWorldTick < 0)
				lostContactSinceWorldTick = world.WorldTick;
			if (activeOrder == FransCommanderOrder.Defend && target == null)
				activeObjective = mission.LastVisibleTargetCell;

			if (activeOrder == FransCommanderOrder.Move)
			{
				if (target != null && !activeShips.Any(s => CanAttackActor(s, target)))
				{
					commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey, "remembered target became visible but current Sea force cannot attack it");
					ResetMission();
					return;
				}

				if (target != null && ShouldEnterFight())
				{
					BeginFight();
					FransBotLog.BotDebug(world,
						"{0}: Sea Commander MOVE -> FIGHT at {1} against visible {2} {3}; RiskModel is now ignored. Combat baseline {4}, fallback {5}.",
						player, activeMoveDestination, target.Info.Name, target.ActorID, retreatBaselineCombatValue, retreatAnchorPoint);
					ExecuteFight(bot, target);
					return;
				}

				hasLastSafeMoveAnchor = true;
				lastSafeMoveAnchor = GetGroupCenter(activeShips);

				if (!hasMoveRiskCheck || moveRiskDestination != activeMoveDestination || world.WorldTick >= nextMoveRiskCheckTick)
				{
					var lead = activeShips.OrderBy(s => (s.Location - activeMoveDestination).LengthSquared).ThenBy(s => s.ActorID).First();
					var route = riskModelService.EvaluateDirectRoute(lead, lead.Location, activeMoveDestination,
						FransRiskRole.NavalCombat, FransRiskTolerance.Balanced);
					hasMoveRiskCheck = true;
					moveRiskDestination = activeMoveDestination;
					moveRiskAllowed = !route.IsCritical;
					nextMoveRiskCheckTick = world.WorldTick + Info.MoveRefreshInterval;
				}

				if (moveRiskAllowed)
					foreach (var ship in activeShips.OrderBy(s => s.ActorID))
						QueueAttackMove(bot, ship, activeMoveDestination, false);
				return;
			}

			if (activeOrder == FransCommanderOrder.Defend)
			{
				if (target != null && IsVisibleEnemy(target))
				{
					if (ShouldEnterFight())
						ExecuteFight(bot, target);
					else
						foreach (var ship in activeShips.OrderBy(s => s.ActorID))
							QueueAttackMove(bot, ship, activeMoveDestination, true);
				}
				else if (lostContactSinceWorldTick >= 0 && world.WorldTick - lostContactSinceWorldTick <= Info.FightLostContactHoldTicks)
					foreach (var ship in activeShips.OrderBy(s => s.ActorID))
						QueueAttackMove(bot, ship, activeMoveDestination, false);
				else
					foreach (var ship in activeShips.OrderBy(s => s.ActorID))
						QueueAttackMove(bot, ship, activeMoveDestination, false);
				return;
			}

			if (activeOrder == FransCommanderOrder.Fight)
			{
				if (target != null && IsVisibleEnemy(target))
					ExecuteFight(bot, target);
				else if (lostContactSinceWorldTick >= 0 && world.WorldTick - lostContactSinceWorldTick <= Info.FightLostContactHoldTicks)
					foreach (var ship in activeShips.OrderBy(s => s.ActorID))
						QueueAttackMove(bot, ship, activeMoveDestination, false);
				else
				{
					commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey, "FIGHT contact cleared/lost");
					ResetMission();
				}
			}
		}


		bool HoldCombinedSecureUntilLaunch(IReadOnlyCollection<Actor> ships, FransActiveMission mission)
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
				var committedIds = (mission.CommittedActorIds ?? Array.Empty<uint>()).ToHashSet();
				foreach (var ship in ships.Where(s => s != null && s.IsInWorld && !s.IsDead && committedIds.Contains(s.ActorID)))
					QueueStopOrder(null, ship);
				FransBotLog.BotDebug(world,
					"{0}: Sea {1} holds COMBINED SECURE {2} until WT {3}; its ETA is {4} WT and {5} domains are timing departure toward the same area.",
					player, BidderKey, mission.TargetActorId, mission.ExecuteAfterWorldTick, mission.EstimatedEtaTicks, mission.CombinedSecureGroupSize);
			}
			return true;
		}

		void ReportSecureRetreatIfLast(uint targetActorId, string reason)
		{
			if (commandBidService.HasOtherActiveSecureMission(targetActorId, FransCommanderKind.Sea, BidderKey))
			{
				FransBotLog.BotDebug(world,
					"{0}: Sea {1} leaves COMBINED SECURE {2}: {3}. Another domain assignment remains active, so General does not reset the whole SECURE.",
					player, BidderKey, targetActorId, reason);
				return;
			}
			generalService.ReportSecureRetreat(targetActorId, reason);
		}

		void ExecuteSecureMission(IBot bot, IReadOnlyCollection<Actor> ships, FransActiveMission mission)
		{
			if (HoldCombinedSecureUntilLaunch(ships, mission))
				return;
			var transportBeachSupport = IsTransportBeachSecure(mission.TargetActorType);
			if (transportBeachSupport && !generalService.IsSeaTransportBeachSecureRequested(mission.TargetActorId))
			{
				commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey, "GroundTransfer transport-beach SECURE lease ended");
				ResetMission();
				return;
			}
			var secureKeepClear = transportBeachSupport ? Info.TransportBeachKeepClearRadius : 0;
			var changed = activeTargetActorId != mission.TargetActorId || activeMissionType != FransMissionType.Secure;
			activeMissionType = FransMissionType.Secure;
			ResetReconState();
			if (changed)
			{
				activeTargetActorId = mission.TargetActorId;
				activeObjective = mission.LastVisibleTargetCell;
				activeOrder = FransCommanderOrder.Move;
				activeOrderStartedWorldTick = world.WorldTick;
				lostContactSinceWorldTick = -1;
				secureClearSinceWorldTick = -1;
				secureAssemblyBestCount = 0;
				secureAssemblyLastProgressTick = world.WorldTick;
				secureCohesionBypassUntilTick = 0;
				activeShips.Clear();
				cohesionHeldShips.Clear();
				cohesionFormationSlots.Clear();
				hasCohesionFormationObjective = false;
				var committed = (mission.CommittedActorIds ?? Array.Empty<uint>())
					.Select(id => ships.FirstOrDefault(s => s.ActorID == id && s != reconRetreatActor && !raidRecoveryOrigins.ContainsKey(s) && FindSeaSecureCell(s, activeObjective, null, secureKeepClear).HasValue))
					.Where(s => s != null).ToArray();
				if (committed.Length != mission.CommittedActorIds.Length || committed.Length == 0)
				{
					commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey, "SECURE exact committed Sea actor snapshot is no longer available");
					ReportSecureRetreatIfLast(mission.TargetActorId, "Sea SECURE exact committed actor snapshot became unavailable");
					ResetMission();
					return;
				}
				foreach (var ship in committed)
					activeShips.Add(ship);
				var secureLabel = transportBeachSupport ? "transport beach" : mission.TargetActorType == "fact" ? "enemy FACT" : "MineCluster";
				FransBotLog.BotDebug(world,
					"{0}: Sea Commander accepts GENERAL SECURE {1} {2} at {3}; {4} ships, bid cost {5}. Sea owns naval-domain CLEAR only; transport-beach support keeps the configured landing-center exclusion ring and never reserves GroundTransfer LSTs or moves Ground ANCHOR.",
					player, secureLabel, mission.TargetActorId, activeObjective, activeShips.Count, mission.TotalCost);
			}

			activeShips.RemoveWhere(s => !ships.Contains(s) || !FindSeaSecureCell(s, mission.LastVisibleTargetCell, null, secureKeepClear).HasValue);
			if (activeShips.Count == 0)
			{
				commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey, "SECURE has no reachable Sea units");
				ReportSecureRetreatIfLast(mission.TargetActorId, "Sea SECURE has no reachable committed units");
				ResetMission();
				return;
			}

			activeObjective = mission.LastVisibleTargetCell;
			var threatRadiusSq = Info.SecureThreatRadius * Info.SecureThreatRadius;
			var threat = combatIntelService.VisibleEnemies
				.Where(IsVisibleEnemy)
				.Where(combatIntelService.IsTacticalCombatThreat)
				.Where(t => (t.Location - activeObjective).LengthSquared <= threatRadiusSq)
				.Where(t => activeShips.Any(s => CanAttackActor(s, t)))
				.OrderByDescending(GetCombatValue)
				.ThenBy(t => (t.Location - activeObjective).LengthSquared)
				.ThenBy(t => t.ActorID)
				.FirstOrDefault();

			if (threat != null)
			{
				secureClearSinceWorldTick = -1;
				secureAssemblyBestCount = 0;
				secureAssemblyLastProgressTick = world.WorldTick;
				if (activeOrder != FransCommanderOrder.Fight)
					BeginFight();
				ExecuteFight(bot, threat);
				return;
			}

			// Sea does not inherit Ground/Air's blanket remembered-building rule. A remembered
			// inland FACT/PROC/PBOX blocks naval CLEAR only when at least one committed shore-
			// bombardment ship can physically reach a water firing cell inside its native range.
			if (!transportBeachSupport && TrySelectSeaRelevantRememberedSecureBuilding(mission.LastVisibleTargetCell, out var rememberedBuilding, out var approachCells))
			{
				secureClearSinceWorldTick = -1;
				secureAssemblyBestCount = 0;
				secureAssemblyLastProgressTick = world.WorldTick;
				var visibleRemembered = rememberedBuilding.IsVisible ? world.GetActorById(rememberedBuilding.ActorId) : null;
				if (visibleRemembered != null && IsVisibleEnemy(visibleRemembered) && activeShips.Any(s => CanAttackActor(s, visibleRemembered)))
				{
					if (activeOrder != FransCommanderOrder.Fight)
						BeginFight();
					ExecuteFight(bot, visibleRemembered);
					return;
				}

				foreach (var pair in approachCells.OrderBy(kv => kv.Key.ActorID))
					QueueAttackMove(bot, pair.Key, pair.Value, false);
				return;
			}

			activeOrder = FransCommanderOrder.Move;
			var marchers = activeShips.OrderBy(s => s.ActorID).ToArray();
			if (!TryBuildSeaSecureFormationDestinations(marchers, activeObjective, secureKeepClear, out var destinations))
			{
				commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey, "SECURE coastal cohesion formation became unreachable");
				ReportSecureRetreatIfLast(mission.TargetActorId, "Sea SECURE coastal cohesion formation became unreachable");
				ResetMission();
				return;
			}

			var bypassCohesion = world.WorldTick < secureCohesionBypassUntilTick;
			IssueSeaCohesionMovement(bot, marchers, destinations, attackMove: true, bypassCohesion: bypassCohesion);

			// Assembly progress is measured against each ship's assigned reachable support cell,
			// not straight-line distance to the land objective. This remains O(n) and reuses the
			// cached formation; no per-tick path search is introduced.
			var assembledCount = activeShips.Count(s =>
				destinations.TryGetValue(s, out var destination) &&
				(s.Location - destination).LengthSquared <= 4);
			var requiredCount = Math.Max(1, (activeShips.Count * 3 + 3) / 4);
			secureAssemblyBestCount = Math.Min(secureAssemblyBestCount, activeShips.Count);
			if (assembledCount > secureAssemblyBestCount)
			{
				secureAssemblyBestCount = assembledCount;
				secureAssemblyLastProgressTick = world.WorldTick;
			}

			if (assembledCount < requiredCount)
			{
				secureClearSinceWorldTick = -1;
				if (secureAssemblyLastProgressTick < 0)
					secureAssemblyLastProgressTick = world.WorldTick;
				else if (world.WorldTick - secureAssemblyLastProgressTick >= Info.SecureAssemblyNoProgressTimeout)
				{
					// Replan only after a real bounded stall. The normal 50-WT execution path
					// remains cache-only/linear; expensive support-cell proofs are invalidated
					// only for the committed ships that actually stalled.
					var stalledShipIds = activeShips.Select(ship => ship.ActorID).ToHashSet();
					foreach (var key in seaSecureCellCache.Keys.Where(key => stalledShipIds.Contains(key.ShipActorId)).ToArray())
						seaSecureCellCache.Remove(key);
					cohesionFormationSlots.Clear();
					hasCohesionFormationObjective = false;
					cohesionHeldShips.Clear();
					secureCohesionBypassUntilTick = world.WorldTick + Info.SecureCohesionBypassTicks;
					secureAssemblyLastProgressTick = world.WorldTick;
					FransBotLog.BotDebug(world,
						"{0}: Sea SECURE {1} assembly watchdog replans after {2} WT without progress: {3}/{4} ships reached their assigned support cells. Cohesion is relaxed for {5} WT; support-cell path proofs are recomputed once, not every tick.",
						player, mission.TargetActorId, Info.SecureAssemblyNoProgressTimeout, assembledCount, activeShips.Count, Info.SecureCohesionBypassTicks);
				}
				return;
			}

			if (secureClearSinceWorldTick < 0)
			{
				secureClearSinceWorldTick = world.WorldTick;
				return;
			}
			if (world.WorldTick - secureClearSinceWorldTick < Info.SecureClearHoldTicks)
				return;

			var securePoint = mission.LastVisibleTargetCell;
			var transportLossSecure = mission.TargetActorType == FransGeneralBotModule.TransportLossSecureTargetType;
			if ((mission.CombinedSecureGroupSize <= 1 || transportLossSecure) &&
				!generalService.CompleteDomainSecureMission(mission.TargetActorId, FransCommanderKind.Sea, securePoint,
					$"Sea cleared reachable naval threats inside {Info.SecureThreatRadius} cells; remembered inland buildings that the committed fleet cannot influence from water are ignored") &&
				!(transportLossSecure && !generalService.IsTransportLossSecure(mission.TargetActorId)))
				return;

			if (mission.CombinedSecureGroupSize > 1 && !transportLossSecure)
				FransBotLog.BotDebug(world,
					"{0}: Sea COMBINED SECURE support {1} is locally CLEAR at {2}; Sea releases its assignment without closing General's target. Ground remains the territorial SECURE authority.",
					player, mission.TargetActorId, securePoint);

			hasLastSafeMoveAnchor = true;
			lastSafeMoveAnchor = securePoint;
			retreatBaselineCombatValue = 0;
			commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey,
				"Sea SECURE clear complete; naval domain mission closed without changing Ground ANCHOR");
			FransBotLog.BotDebug(world,
				"{0}: Sea Commander SECURE {1} is CLEAR at {2}: no visible attackable naval threat and no remembered building remains that this committed fleet can reach and influence from water. Naval domain mission closes without changing Ground ANCHOR; ships release in place.",
				player, mission.TargetActorId, securePoint);
			ResetMission();
		}

		bool HasNewSeaSecureIntelSince(FransMission mission, int clearWorldTick, IReadOnlyCollection<Actor> ships)
		{
			combatIntelService.EnsureCurrentSnapshot();
			var available = ships
				.Where(s => commanderCoreService.IsActorAvailableForMissionBid(FransCommanderKind.Sea, BidderKey, s))
				.Where(s => s != reconRetreatActor && !raidRecoveryOrigins.ContainsKey(s))
				.ToArray();
			if (available.Length == 0)
				return false;

			var radiusSq = Info.SecureThreatRadius * Info.SecureThreatRadius;
			foreach (var contact in combatIntelService.EnemyCombatContacts
				.Where(c => c.ActorId != 0 &&
					c.Owner != null &&
					PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(c.Owner)) &&
					c.LastSeenWorldTick > clearWorldTick &&
					(c.LastSeenCell - mission.LastVisibleTargetCell).LengthSquared <= radiusSq)
				.OrderBy(c => c.ActorId))
			{
				if (contact.IsVisible)
				{
					var visible = world.GetActorById(contact.ActorId);
					if (visible != null && IsVisibleEnemy(visible) && available.Any(s => CanAttackActor(s, visible)))
						return true;
				}

				// Hidden mobile contacts can move and are not enough to reopen a naval domain by
				// themselves. Persistent buildings reopen it only when the available fleet can
				// physically reach a legal firing/verification cell from water.
				if (!contact.IsBuilding)
					continue;

				foreach (var ship in available.OrderBy(s => s.ActorID))
					if (Info.SecureShoreBombardmentTypes.Contains(ship.Info.Name) &&
						CanBidReachRememberedBombardmentCell(ship, contact.LastSeenCell))
						return true;
			}

			return false;
		}

		bool TrySelectSeaRelevantRememberedSecureBuilding(CPos center, out FransCombatIntelContact building, out Dictionary<Actor, CPos> approachCells)
		{
			combatIntelService.EnsureCurrentSnapshot();
			approachCells = [];
			var radiusSq = Info.SecureThreatRadius * Info.SecureThreatRadius;
			var candidates = combatIntelService.EnemyCombatContacts
				.Where(c => c.ActorId != 0 && c.IsBuilding)
				.Where(c => c.Owner != null && PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(c.Owner)))
				.Where(c => (c.LastSeenCell - center).LengthSquared <= radiusSq)
				.OrderBy(c => GetSeaTargetPriorityRank(c.ActorType))
				.ThenByDescending(c => c.IsVisible)
				.ThenBy(c => (c.LastSeenCell - center).LengthSquared)
				.ThenBy(c => c.ActorId);

			foreach (var candidate in candidates)
			{
				var visible = candidate.IsVisible ? world.GetActorById(candidate.ActorId) : null;
				if (visible != null && IsVisibleEnemy(visible))
				{
					if (!activeShips.Any(s => CanAttackActor(s, visible)))
						continue;

					foreach (var ship in activeShips.OrderBy(s => s.ActorID))
					{
						if (!CanAttackActor(ship, visible))
							continue;
						var cell = FindReachableRaidFiringPosition(ship, visible);
						if (cell.HasValue)
							approachCells[ship] = cell.Value;
					}

					if (approachCells.Count == 0)
						continue;
					building = candidate;
					return true;
				}

				foreach (var ship in activeShips.OrderBy(s => s.ActorID))
				{
					if (!Info.SecureShoreBombardmentTypes.Contains(ship.Info.Name))
						continue;
					if (TryFindRememberedSeaBombardmentCell(ship, candidate.LastSeenCell, out var cell))
						approachCells[ship] = cell;
				}

				if (approachCells.Count == 0)
					continue;
				building = candidate;
				return true;
			}

			building = default;
			approachCells.Clear();
			return false;
		}

		int OffshorePreference(CPos cell)
		{
			var radius = Math.Min(6, Math.Max(1, Info.ShoreBombardmentSupportRadius));
			var distance = strategicMapService?.GetKnownBeachDistance(cell, radius) ?? -1;
			return distance < 0 ? 0 : distance;
		}

		IReadOnlyList<SeaBidTopologyCell> GetSeaBidTopologyCells(CPos targetCell, int radius, int minimumDistance = 0)
		{
			if (!world.Map.Contains(targetCell) || radius < 0)
				return Array.Empty<SeaBidTopologyCell>();

			var key = new SeaBidTopologyKey(targetCell, radius, minimumDistance);
			var terrainVersion = strategicMapService.TerrainKnowledgeVersion;
			if (seaBidTopologyCache.TryGetValue(key, out var cached) && cached.TerrainKnowledgeVersion == terrainVersion)
				return cached.Cells;

			// Cache topology-only inputs shared by repeated bid scans. Dynamic occupancy, ship
			// location, weapon range and Commander availability are deliberately evaluated
			// live by each caller, so this cannot make a stale gameplay decision.
			var minimumDistanceSq = minimumDistance * minimumDistance;
			var cells = world.Map.FindTilesInCircle(targetCell, radius)
				.Where(world.Map.Contains)
				.Where(c => minimumDistance <= 0 || (c - targetCell).LengthSquared >= minimumDistanceSq)
				.Select(c => strategicMapService.TryGetNavalRegionId(c, out var region)
					? new SeaBidTopologyCell(c, region, OffshorePreference(c), (c - targetCell).LengthSquared)
					: (SeaBidTopologyCell?)null)
				.Where(x => x.HasValue)
				.Select(x => x.Value)
				.ToArray();

			if (seaBidTopologyCache.Count >= 512)
				seaBidTopologyCache.Clear();
			seaBidTopologyCache[key] = new SeaBidTopologyCacheEntry
			{
				TerrainKnowledgeVersion = terrainVersion,
				Cells = cells
			};
			return cells;
		}

		CPos? FindSeaSecureBidCell(Actor ship, CPos targetCell, int minimumDistance = 0)
		{
			var mobile = ship?.TraitOrDefault<Mobile>();
			if (mobile == null || !world.Map.Contains(targetCell) ||
				!strategicMapService.TryGetNavalRegionId(ship.Location, out var shipRegion))
				return null;

			var formationRadiusSq = Info.CohesionFormationRadius * Info.CohesionFormationRadius;
			return GetSeaBidTopologyCells(targetCell, Info.SecureAssemblyRadius, minimumDistance)
				.Where(x => x.NavalRegionId == shipRegion)
				.Where(x => mobile.CanEnterCell(x.Cell, check: BlockedByActor.Immovable) && mobile.CanStayInCell(x.Cell))
				.OrderBy(x => x.TargetDistanceSquared > formationRadiusSq ? 1 : 0)
				.ThenByDescending(x => x.OffshorePreference)
				.ThenBy(x => x.TargetDistanceSquared)
				.ThenBy(x => (x.Cell - ship.Location).LengthSquared)
				.ThenBy(x => x.Cell.X).ThenBy(x => x.Cell.Y)
				.Select(x => (CPos?)x.Cell).FirstOrDefault();
		}

		CPos? FindRaidBidFiringPosition(Actor ship, Actor target)
		{
			if (!CanAttackActor(ship, target))
				return null;
			if (IsTargetWithinWeaponRange(ship, target))
				return ship.Location;
			var mobile = ship.TraitOrDefault<Mobile>();
			if (mobile == null || !strategicMapService.TryGetNavalRegionId(ship.Location, out var shipRegion))
				return null;

			return GetSeaBidTopologyCells(target.Location, Info.ShoreBombardmentSupportRadius)
				.Where(x => x.NavalRegionId == shipRegion)
				.Where(x => mobile.CanEnterCell(x.Cell, check: BlockedByActor.Immovable) && mobile.CanStayInCell(x.Cell))
				.Where(x => IsTargetWithinWeaponRangeFromCell(ship, target, x.Cell))
				.OrderByDescending(x => x.OffshorePreference)
				.ThenBy(x => (x.Cell - ship.Location).LengthSquared)
				.ThenBy(x => x.TargetDistanceSquared)
				.ThenBy(x => x.Cell.X).ThenBy(x => x.Cell.Y)
				.Select(x => (CPos?)x.Cell).FirstOrDefault();
		}

		CPos? FindRememberedRaidBidFiringPosition(Actor ship, CPos buildingCell)
		{
			if (ship == null || !Info.SecureShoreBombardmentTypes.Contains(ship.Info.Name))
				return null;
			var mobile = ship.TraitOrDefault<Mobile>();
			if (mobile == null || !world.Map.Contains(buildingCell) ||
				!strategicMapService.TryGetNavalRegionId(ship.Location, out var shipRegion))
				return null;

			var maximumRange = ship.TraitsImplementing<AttackBase>()
				.Where(a => !a.IsTraitDisabled && !a.IsTraitPaused)
				.SelectMany(a => a.Armaments)
				.Where(a => !a.IsTraitDisabled && !a.IsTraitPaused)
				.Select(a => a.MaxRange().Length).DefaultIfEmpty(0).Max();
			if (maximumRange <= 0)
				return null;

			var cellLength = Math.Max(1, WDist.FromCells(1).Length);
			var radius = Math.Min(Info.ShoreBombardmentSupportRadius, Math.Max(1, (maximumRange + cellLength - 1) / cellLength));
			return GetSeaBidTopologyCells(buildingCell, radius)
				.Where(x => x.NavalRegionId == shipRegion)
				.Where(x => mobile.CanEnterCell(x.Cell, check: BlockedByActor.Immovable) && mobile.CanStayInCell(x.Cell))
				.OrderByDescending(x => x.OffshorePreference)
				.ThenBy(x => (x.Cell - ship.Location).LengthSquared)
				.ThenBy(x => x.TargetDistanceSquared)
				.ThenBy(x => x.Cell.X).ThenBy(x => x.Cell.Y)
				.Select(x => (CPos?)x.Cell).FirstOrDefault();
		}

		bool CanBidReachRememberedBombardmentCell(Actor ship, CPos buildingCell)
		{
			var mobile = ship?.TraitOrDefault<Mobile>();
			if (mobile == null || !world.Map.Contains(buildingCell) ||
				!strategicMapService.TryGetNavalRegionId(ship.Location, out var shipRegion))
				return false;

			var maximumRange = ship.TraitsImplementing<AttackBase>()
				.Where(a => !a.IsTraitDisabled && !a.IsTraitPaused)
				.SelectMany(a => a.Armaments)
				.Where(a => !a.IsTraitDisabled && !a.IsTraitPaused)
				.Select(a => a.MaxRange().Length).DefaultIfEmpty(0).Max();
			if (maximumRange <= 0)
				return false;

			var cellLength = Math.Max(1, WDist.FromCells(1).Length);
			var radius = Math.Min(Info.ShoreBombardmentSupportRadius, Math.Max(1, (maximumRange + cellLength - 1) / cellLength));
			return world.Map.FindTilesInCircle(buildingCell, radius)
				.Where(world.Map.Contains)
				.Any(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c) &&
					strategicMapService.TryGetNavalRegionId(c, out var region) && region == shipRegion);
		}

		bool TryFindRememberedSeaBombardmentCell(Actor ship, CPos buildingCell, out CPos firingCell)
		{
			firingCell = default;
			var mobile = ship?.TraitOrDefault<Mobile>();
			if (mobile == null || pathFinder == null || !world.Map.Contains(buildingCell))
				return false;

			var maximumRange = ship.TraitsImplementing<AttackBase>()
				.Where(a => !a.IsTraitDisabled && !a.IsTraitPaused)
				.SelectMany(a => a.Armaments)
				.Where(a => !a.IsTraitDisabled && !a.IsTraitPaused)
				.Select(a => a.MaxRange().Length)
				.DefaultIfEmpty(0)
				.Max();
			if (maximumRange <= 0)
				return false;

			var cellLength = Math.Max(1, WDist.FromCells(1).Length);
			var maximumRangeCells = Math.Max(1, (maximumRange + cellLength - 1) / cellLength);
			var searchRadius = Math.Min(Info.ShoreBombardmentSupportRadius, maximumRangeCells);
			var candidates = world.Map.FindTilesInCircle(buildingCell, searchRadius)
				.Where(world.Map.Contains)
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.Where(c => pathFinder.PathMightExistForLocomotorBlockedByImmovable(mobile.Locomotor, ship.Location, c))
				.OrderByDescending(OffshorePreference)
				.ThenBy(c => (c - buildingCell).LengthSquared)
				.ThenBy(c => (c - ship.Location).LengthSquared)
				.ThenBy(c => c.X).ThenBy(c => c.Y)
				.Take(64)
				.ToArray();
			if (candidates.Length == 0)
				return false;

			var path = pathFinder.FindPathToTargetCells(ship, ship.Location, candidates, BlockedByActor.Immovable);
			if (path.Count == 0)
				return false;
			firingCell = path[0];
			return true;
		}

		void BeginFight()
		{
			activeOrder = FransCommanderOrder.Fight;
			activeOrderStartedWorldTick = world.WorldTick;
			lostContactSinceWorldTick = -1;
			var fightValue = Math.Max(1, activeShips.Sum(GetCombatValue));
			retreatBaselineCombatValue = Math.Max(retreatBaselineCombatValue, fightValue);
			retreatAnchorPoint = hasMissionAnchorPoint ? missionAnchorPoint : hasLastSafeMoveAnchor ? lastSafeMoveAnchor : GetGroupCenter(activeShips);
		}

		bool ShouldRetreatFromFight(IReadOnlyCollection<Actor> ships, out int currentCombatValue)
		{
			currentCombatValue = activeShips.Where(a => ships.Contains(a)).Sum(GetCombatValue);
			if (retreatBaselineCombatValue <= 0 || currentCombatValue <= 0)
				return false;
			var threshold = Math.Max(1, retreatBaselineCombatValue * Info.RetreatAtRemainingForcePercent / 100);
			return currentCombatValue <= threshold;
		}

		void BeginRetreat(IBot bot, IReadOnlyCollection<Actor> ships, int currentCombatValue)
		{
			// Keep only the exact mission survivors. must never let one Sea capacity
			// sweep the whole fleet into RETREAT merely because those ships exist.
			activeShips.RemoveWhere(s => s == null || !s.IsInWorld || s.IsDead || !ships.Contains(s));
			if (activeTargetActorId != 0)
			{
				if (activeMissionType == FransMissionType.Raid)
					generalService.ReportRaidRetreat(activeTargetActorId,
						$"Sea force collapse {currentCombatValue}/{retreatBaselineCombatValue}");
				else if (activeMissionType == FransMissionType.Secure)
					ReportSecureRetreatIfLast(activeTargetActorId,
						$"Sea force collapse {currentCombatValue}/{retreatBaselineCombatValue}");
			}
			commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey,
				$"FIGHT force collapse {currentCombatValue}/{retreatBaselineCombatValue}; RETREAT owns regroup");
			retreatRecoveryActive = true;
			retreatStartedWorldTick = world.WorldTick;
			activeTargetActorId = 0;
			activeOrder = FransCommanderOrder.Retreat;
			activeOrderStartedWorldTick = world.WorldTick;
			activeObjective = retreatAnchorPoint;
			lostContactSinceWorldTick = -1;
			PublishTransientReservations();
			FransBotLog.BotDebug(world,
				"{0}: Sea Commander FIGHT -> RETREAT: combat value {1}/{2}; ANCHOR POINT {3}. Exact mission survivors remain reserved; only genuinely free reinforcements may join recovery. Recovery requires {4}% of pre-fight combat value.",
				player, currentCombatValue, retreatBaselineCombatValue, retreatAnchorPoint, Info.ResumeOffenseAtOriginalForcePercent);
			foreach (var ship in activeShips.OrderBy(s => s.ActorID))
				RouteSeaRetreatUnit(bot, ship, true);
		}

		void ExecuteRetreatRecovery(IBot bot, IReadOnlyCollection<Actor> ships)
		{
			activeOrder = FransCommanderOrder.Retreat;
			activeObjective = retreatAnchorPoint;
			activeShips.RemoveWhere(s => s == null || !s.IsInWorld || s.IsDead || !ships.Contains(s));

			var requiredValue = Math.Max(1, retreatBaselineCombatValue * Info.ResumeOffenseAtOriginalForcePercent / 100);
			var reservedValue = activeShips.Sum(GetCombatValue);
			if (reservedValue < requiredValue)
			{
				foreach (var candidate in ships
					.Where(s => !activeShips.Contains(s) && s != reconRetreatActor && !raidRecoveryOrigins.ContainsKey(s))
					.Where(s => commanderCoreService.IsActorAvailableForBidder(FransCommanderKind.Sea, BidderKey, s))
					.OrderBy(s => (s.Location - retreatAnchorPoint).LengthSquared).ThenByDescending(GetCombatValue).ThenBy(s => s.ActorID))
				{
					activeShips.Add(candidate);
					reservedValue += GetCombatValue(candidate);
					if (reservedValue >= requiredValue)
						break;
				}
			}

			PublishTransientReservations();
			foreach (var ship in activeShips.OrderBy(s => s.ActorID))
				RouteSeaRetreatUnit(bot, ship, false);

			var radiusSq = Info.RetreatAssemblyRadius * Info.RetreatAssemblyRadius;
			var assembledValue = activeShips
				.Where(IsSeaRecoveryReady)
				.Where(s => (s.Location - retreatAnchorPoint).LengthSquared <= radiusSq)
				.Sum(GetCombatValue);
			if (assembledValue < requiredValue)
				return;

			FransBotLog.BotDebug(world,
				"{0}: Sea Commander RETREAT recovery complete at ANCHOR POINT {1}: assembled combat value {2}/{3}.",
				player, retreatAnchorPoint, assembledValue, requiredValue);
			retreatRecoveryActive = false;
			retreatStartedWorldTick = -1;
			retreatBaselineCombatValue = 0;
			hasLastSafeMoveAnchor = true;
			lastSafeMoveAnchor = retreatAnchorPoint;
			ResetMission();
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

		void IssueSeaCohesionMovement(IBot bot, IReadOnlyCollection<Actor> ships,
			IReadOnlyDictionary<Actor, CPos> destinations, bool attackMove, bool bypassCohesion = false)
		{
			var live = ships.Where(s => s != null && s.IsInWorld && !s.IsDead && destinations.ContainsKey(s))
				.OrderBy(s => s.ActorID).ToArray();
			if (live.Length == 0)
				return;

			cohesionHeldShips.RemoveWhere(s => !live.Contains(s) && !activeShips.Contains(s));

			if (live.Length == 1 || bypassCohesion)
			{
				foreach (var ship in live)
				{
					var force = cohesionHeldShips.Remove(ship);
					var destination = destinations[ship];
					if ((ship.Location - destination).LengthSquared <= 1)
						continue;
					if (attackMove)
						QueueAttackMove(bot, ship, destination, force);
					else
						QueueMove(bot, ship, destination, force);
				}
				return;
			}

			// Compare each ship with its own assigned reachable formation cell. Using the land
			// objective as a common geometric ruler mis-ordered ships around islands/coasts and
			// could make the genuinely shortest naval route look like the trailer.
			var trailer = live
				.OrderByDescending(s => CohesionCellDistance(s.Location, destinations[s]))
				.ThenBy(s => s.ActorID)
				.First();
			var trailerRemaining = CohesionCellDistance(trailer.Location, destinations[trailer]);
			var stalledTrailer = trailer.IsIdle && trailerRemaining > Info.CohesionMaximumLeadCells &&
				lastMoveWorldTick.TryGetValue(trailer, out var trailerLastMove) &&
				world.WorldTick - trailerLastMove >= Info.ScanInterval;
			var allowedLead = stalledTrailer ? Info.CohesionChokepointLeadCells : Info.CohesionMaximumLeadCells;

			foreach (var ship in live)
			{
				var destination = destinations[ship];
				var remaining = CohesionCellDistance(ship.Location, destination);
				var lead = trailerRemaining - remaining;
				if (lead > allowedLead)
				{
					if (cohesionHeldShips.Add(ship))
						bot.QueueOrder(new Order("Stop", ship, false));
					continue;
				}

				var force = cohesionHeldShips.Remove(ship);
				if ((ship.Location - destination).LengthSquared <= 1)
					continue;
				if (attackMove)
					QueueAttackMove(bot, ship, destination, force);
				else
					QueueMove(bot, ship, destination, force);
			}
		}

		bool TryBuildSeaSecureFormationDestinations(Actor[] ships, CPos center, int minimumDistance, out Dictionary<Actor, CPos> destinations)
		{
			destinations = [];
			if (hasCohesionFormationObjective && cohesionFormationObjective == center && cohesionFormationMinimumDistance == minimumDistance &&
				ships.All(ship => cohesionFormationSlots.ContainsKey(ship)))
			{
				foreach (var ship in ships)
					destinations[ship] = cohesionFormationSlots[ship];
				return true;
			}

			cohesionFormationSlots.Clear();
			hasCohesionFormationObjective = true;
			cohesionFormationObjective = center;
			cohesionFormationMinimumDistance = minimumDistance;
			var reserved = new HashSet<CPos>();
			foreach (var ship in ships.OrderBy(s => s.ActorID))
			{
				var destination = FindSeaSecureCell(ship, center, reserved, minimumDistance) ?? FindSeaSecureCell(ship, center, null, minimumDistance);
				if (!destination.HasValue)
					return false;
				destinations[ship] = destination.Value;
				cohesionFormationSlots[ship] = destination.Value;
				reserved.Add(destination.Value);
			}
			return true;
		}

		bool TryBuildSeaRaidFormationDestinations(Actor[] ships, Actor target, out Dictionary<Actor, CPos> destinations)
		{
			destinations = [];
			if (target == null)
				return false;

			if (hasCohesionFormationObjective && cohesionFormationObjective == target.Location &&
				ships.All(ship => cohesionFormationSlots.TryGetValue(ship, out var slot) &&
					IsTargetWithinWeaponRangeFromCell(ship, target, slot)))
			{
				foreach (var ship in ships)
					destinations[ship] = cohesionFormationSlots[ship];
				return true;
			}

			cohesionFormationSlots.Clear();
			hasCohesionFormationObjective = true;
			cohesionFormationObjective = target.Location;
			var reserved = new HashSet<CPos>();
			foreach (var ship in ships.OrderBy(s => s.ActorID))
			{
				var destination = FindReachableRaidFiringPosition(ship, target, reserved) ?? FindReachableRaidFiringPosition(ship, target);
				if (!destination.HasValue)
					return false;
				destinations[ship] = destination.Value;
				cohesionFormationSlots[ship] = destination.Value;
				reserved.Add(destination.Value);
			}
			return true;
		}

		Actor FindImmediateSeaCombatThreat()
		{
			var radiusSq = Info.FightMicroRadius * Info.FightMicroRadius;
			return combatIntelService.VisibleEnemies
				.Where(IsVisibleEnemy)
				.Where(combatIntelService.IsTacticalCombatThreat)
				.Where(enemy => activeShips.Any(ship =>
					(enemy.Location - ship.Location).LengthSquared <= radiusSq && CanAttackActor(ship, enemy)))
				.OrderByDescending(GetCombatValue)
				.ThenBy(enemy => activeShips.Min(ship => (enemy.Location - ship.Location).LengthSquared))
				.ThenBy(enemy => enemy.ActorID)
				.FirstOrDefault();
		}

		Actor FindVisibleNavalProducerInterdictionTarget(Actor currentTarget, CPos missionCenter)
		{
			var currentRank = currentTarget != null ? GetSeaTargetPriorityRank(currentTarget.Info.Name) : int.MaxValue;
			var radiusSq = Info.SecureThreatRadius * Info.SecureThreatRadius;
			return combatIntelService.VisibleEnemies
				.Where(IsVisibleEnemy)
				.Where(enemy => FransActorClass.IsNavalProducer(enemy.Info))
				.Where(enemy => GetSeaTargetPriorityRank(enemy.Info.Name) < currentRank)
				.Where(enemy => (enemy.Location - missionCenter).LengthSquared <= radiusSq)
				.Where(enemy => activeShips.Any(ship => CanAttackActor(ship, enemy)))
				.OrderBy(enemy => GetSeaTargetPriorityRank(enemy.Info.Name))
				.ThenBy(enemy => (enemy.Location - missionCenter).LengthSquared)
				.ThenBy(enemy => enemy.ActorID)
				.FirstOrDefault();
		}

		bool ExecuteSeaPriorityInterdiction(IBot bot, Actor target)
		{
			if (target == null)
				return false;

			var movers = activeShips.Where(ship => CanAttackActor(ship, target) && !IsTargetWithinWeaponRange(ship, target))
				.OrderBy(ship => ship.ActorID).ToArray();
			if (movers.Length > 0)
			{
				if (!TryBuildSeaRaidFormationDestinations(movers, target, out var destinations))
					return false;
				IssueSeaCohesionMovement(bot, movers, destinations, attackMove: false);
			}

			foreach (var ship in activeShips.Where(ship => CanAttackActor(ship, target) && IsTargetWithinWeaponRange(ship, target)).OrderBy(ship => ship.ActorID))
				QueueAttack(bot, ship, target, false);
			return true;
		}

		void ExecuteRaidMission(IBot bot, IReadOnlyCollection<Actor> ships, Actor target, FransActiveMission mission)
		{
			var visibleTarget = target != null && IsVisibleEnemy(target);
			var selected = mission.CommittedActorIds
				.Select(id => ships.FirstOrDefault(s => s.ActorID == id && !raidRecoveryOrigins.ContainsKey(s) &&
					(!visibleTarget || CanAttackActor(s, target))))
				.Where(s => s != null)
				.ToArray();
			if (selected.Length != mission.CommittedActorIds.Length || selected.Length == 0)
			{
				ReleaseRaidForRebid(bot, mission.TargetActorId, "exact committed Sea RAID actor list/readiness changed before strike");
				return;
			}

			var required = mission.RequiredContribution;
			var damage = mission.OfferedContribution;
			var changed = activeMissionType != FransMissionType.Raid || activeTargetActorId != mission.TargetActorId;
			if (changed)
			{
				activeMissionType = FransMissionType.Raid;
				activeTargetActorId = mission.TargetActorId;
				activeObjective = visibleTarget ? target.Location : mission.LastVisibleTargetCell;
				activeMoveDestination = activeObjective;
				activeOrder = FransCommanderOrder.Move;
				activeOrderStartedWorldTick = world.WorldTick;
				raidStrikeIssued = false;
				ResetRaidLostTargetSearch(false);
				activeShips.Clear();
				raidMissionOrigins.Clear();
				cohesionHeldShips.Clear();
				cohesionFormationSlots.Clear();
				hasCohesionFormationObjective = false;
				foreach (var ship in selected)
				{
					activeShips.Add(ship);
					raidMissionOrigins[ship] = ship.Location;
				}
				FransBotLog.BotDebug(world,
					visibleTarget
						? "{0}: Sea Commander accepts precision RAID {1} {2}: exact {3} ships [{4}], required strike {5}, estimated {6}. Synchronized cohesion Plain Move stages distinct reachable firing cells before the existing target-only coordinated strike."
						: "{0}: Sea Commander accepts precision RAID {1} {2}: exact {3} ships [{4}], strike snapshot {6}/{5}. Target is unseen; force moves to LastVisibleTargetCell and performs bounded local plain-Move RECON before ANCHOR return.",
					player, mission.TargetActorType, mission.TargetActorId, activeShips.Count,
					string.Join(",", activeShips.OrderBy(a => a.ActorID).Select(a => a.ActorID)), required, damage);
			}
			else
				activeShips.RemoveWhere(s => !selected.Contains(s));

			if (activeShips.Count == 0)
			{
				CloseRaid(bot, "all committed Sea RAID ships were lost", true);
				return;
			}

			// RAID never ignores local fire merely because its immutable strategic target is
			// temporarily unseen. Immediate attackers are handled first, then a visible naval
			// producer in the same mission area, and only then does bounded lost-target RECON run.
			var immediateThreat = FindImmediateSeaCombatThreat();
			if (immediateThreat != null)
			{
				if (activeOrder != FransCommanderOrder.Fight)
					BeginFight();
				ExecuteFight(bot, visibleTarget ? target : null);
				return;
			}

			if (activeOrder == FransCommanderOrder.Fight)
			{
				activeOrder = FransCommanderOrder.Move;
				activeOrderStartedWorldTick = world.WorldTick;
				lostContactSinceWorldTick = -1;
				FransBotLog.BotDebug(world,
					"{0}: Sea RAID LOCAL FIGHT clear; no immediate combat threat remains, so the same RAID resumes without rebid/recovery.",
					player);
			}

			var navalProducer = FindVisibleNavalProducerInterdictionTarget(visibleTarget ? target : null, mission.LastVisibleTargetCell);
			if (navalProducer != null && ExecuteSeaPriorityInterdiction(bot, navalProducer))
			{
				raidStrikeIssued = false;
				return;
			}

			if (!visibleTarget)
			{
				ExecuteLostRaidTargetRecon(bot, mission);
				return;
			}

			if (raidSearchStartedWorldTick >= 0)
			{
				foreach (var ship in activeShips.Where(s => s != null && s.IsInWorld && !s.IsDead))
					QueueStopOrder(bot, ship);
				ResetRaidLostTargetSearch(false);
				raidStrikeIssued = false;
				cohesionHeldShips.Clear();
				cohesionFormationSlots.Clear();
				hasCohesionFormationObjective = false;
				FransBotLog.BotDebug(world,
					"{0}: Sea RAID reacquires exact target {1}; local RECON ends and the same RAID resumes.",
					player, mission.TargetActorId);
			}

			activeObjective = target.Location;

			if (!raidStrikeIssued)
			{
				var movers = activeShips.Where(s => !IsTargetWithinWeaponRange(s, target)).OrderBy(s => s.ActorID).ToArray();
				if (movers.Length > 0)
				{
					if (!TryBuildSeaRaidFormationDestinations(movers, target, out var destinations))
					{
						CloseRaid(bot, "target no longer has a reachable Sea firing position", true);
						return;
					}

					foreach (var ship in activeShips.Where(s => IsTargetWithinWeaponRange(s, target)).OrderBy(s => s.ActorID))
						if (cohesionHeldShips.Add(ship))
							bot.QueueOrder(new Order("Stop", ship, false));

					IssueSeaCohesionMovement(bot, movers, destinations, attackMove: false);
					return;
				}

				cohesionHeldShips.Clear();
				foreach (var ship in activeShips.OrderBy(s => s.ActorID))
					QueueAttack(bot, ship, target, true);
				raidStrikeIssued = true;
				FransBotLog.BotDebug(world,
					"{0}: Sea RAID STRIKE NOW on {1} {2}: {3} cohesive ships attack the exact target in one Commander tick after synchronized march; estimated first strike {4}/{5}.",
					player, target.Info.Name, target.ActorID, activeShips.Count, damage, required);
			}
		}

		void ExecuteLostRaidTargetRecon(IBot bot, FransActiveMission mission)
		{
			activeObjective = mission.LastVisibleTargetCell;
			// Once local RECON has started, its deadline is absolute. Waypoints may move the
			// group outside the initial approach envelope; that must never bypass the 400-WT bound.
			if (raidSearchStartedWorldTick >= 0 &&
				world.WorldTick - raidSearchStartedWorldTick >= commanderCoreService.RaidLostTargetReconTicks)
			{
				CloseRaid(bot, "exact target not reacquired during bounded local RECON", false);
				return;
			}

			var center = GetGroupCenter(activeShips);
			// A lost/remembered land building is physically unreachable at its exact cell for ships.
			// Treat arrival inside the configured shore-support envelope as arrival at the search area;
			// otherwise a perfectly valid bombardment fleet can repeatedly move to an offshore cell
			// yet never enter the bounded local RECON because its center cannot get within 2 cells of land.
			var approachRadius = mission.TargetIsBuilding ? Info.ShoreBombardmentSupportRadius : 2;
			if ((center - activeObjective).LengthSquared > approachRadius * approachRadius)
			{
				activeOrder = FransCommanderOrder.Move;
				foreach (var ship in activeShips.OrderBy(s => s.ActorID))
				{
					var destination = FindRememberedMoveDestination(ship, activeObjective, mission.TargetIsBuilding);
					if (!destination.HasValue)
					{
						CloseRaid(bot, "committed Sea RAID ship cannot reach the last-visible target area", true);
						return;
					}
					QueueMove(bot, ship, destination.Value, false);
				}
				return;
			}

			if (raidSearchStartedWorldTick < 0)
			{
				var leader = activeShips.OrderBy(s => s.ActorID).FirstOrDefault();
				if (leader == null)
				{
					CloseRaid(bot, "lost target search has no live Sea unit", true);
					return;
				}
				raidSearchStartedWorldTick = world.WorldTick;
				raidSearchSpiral.Reset(activeObjective, commanderCoreService.GetReconVisionCells(leader));
				hasRaidSearchWaypoint = false;
				activeOrder = FransCommanderOrder.Search;
				foreach (var ship in activeShips)
					QueueStopOrder(bot, ship);
				FransBotLog.BotDebug(world,
					"{0}: Sea RAID target {1} is gone/unseen at LastVisibleTargetCell {2}; begins {3}-WT local plain-Move RECON before ANCHOR return.",
					player, mission.TargetActorId, activeObjective, commanderCoreService.RaidLostTargetReconTicks);
			}

			if (hasRaidSearchWaypoint && activeShips.Any(s => !s.IsIdle) && (center - raidSearchWaypoint).LengthSquared > 4)
				return;

			var lead = activeShips.OrderBy(s => s.ActorID).FirstOrDefault();
			if (lead == null)
				return;
			var waypoints = new List<CPos>(Math.Min(4, commanderCoreService.ReconWaypointBatchSize));
			var cursor = center;
			for (var i = 0; i < Math.Min(4, commanderCoreService.ReconWaypointBatchSize); i++)
			{
				if (!raidSearchSpiral.TryGetNextWaypoint(world, c => FindSeaReconCell(lead, c), cursor, out var waypoint))
					break;
				waypoints.Add(waypoint);
				cursor = waypoint;
			}
			if (waypoints.Count == 0)
				return;
			foreach (var ship in activeShips.OrderBy(s => s.ActorID))
				for (var i = 0; i < waypoints.Count; i++)
					bot.QueueOrder(new Order("Move", ship, Target.FromCell(world, waypoints[i]), i > 0));
			raidSearchWaypoint = waypoints[^1];
			hasRaidSearchWaypoint = true;
		}

		void ResetRaidLostTargetSearch(bool cancelActivities)
		{
			if (cancelActivities)
				foreach (var ship in activeShips.Where(s => s != null && s.IsInWorld && !s.IsDead))
					QueueStopOrder(null, ship);
			raidSearchStartedWorldTick = -1;
			raidSearchWaypoint = default;
			hasRaidSearchWaypoint = false;
		}

		void ReleaseRaidForRebid(IBot bot, uint targetId, string reason)
		{
			commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey, $"RAID RETREAT/re-bid: {reason}");
			if (targetId != 0)
				generalService.ReportRaidRetreat(targetId, $"Sea RAID: {reason}");
			if (activeMissionType == FransMissionType.Raid && activeTargetActorId == targetId)
				StartRaidRecovery(bot, $"RAID RETREAT/re-bid: {reason}");
			ResetMission();
		}

		void CloseRaid(IBot bot, string reason, bool reportRetreat)
		{
			var targetId = activeTargetActorId;
			if (targetId != 0)
				commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey, $"RAID ends: {reason}");
			if (reportRetreat && targetId != 0)
				generalService.ReportRaidRetreat(targetId, $"Sea RAID: {reason}");
			if (reportRetreat)
				StartRaidRecovery(bot, reason);
			else
				StartRaidAttackMoveReturn(bot, reason);
			ResetMission();
		}

		void StartRaidAttackMoveReturn(IBot bot, string reason)
		{
			var returning = activeShips.Where(s => s != null && s.IsInWorld && !s.IsDead).ToArray();
			foreach (var ship in returning)
			{
				var origin = raidMissionOrigins.TryGetValue(ship, out var saved) ? saved : ship.Location;
				raidRecoveryOrigins[ship] = origin;
				raidAttackMoveRecoveryActors.Add(ship);
				QueueAttackMove(bot, ship, origin, true);
			}
			if (returning.Length > 0)
			{
				PublishTransientReservations();
				FransBotLog.BotDebug(world,
					"{0}: Sea RAID normal completion sends {1} ship(s) by native AttackMove back to their individual RAID origin cells: {2}.",
					player, returning.Length, reason);
			}
			raidMissionOrigins.Clear();
		}

		void StartRaidRecovery(IBot bot, string reason)
		{
			var recovering = activeShips.Where(s => s != null && s.IsInWorld && !s.IsDead).ToArray();
			foreach (var ship in recovering)
			{
				raidAttackMoveRecoveryActors.Remove(ship);
				var origin = raidMissionOrigins.TryGetValue(ship, out var saved) ? saved : ship.Location;
				var anchor = hasMissionAnchorPoint ? missionAnchorPoint : origin;
				raidRecoveryOrigins[ship] = anchor;
				QueueMove(bot, ship, anchor, true);
			}
			if (recovering.Length > 0)
			{
				PublishTransientReservations();
				FransBotLog.BotDebug(world,
					"{0}: Sea RAID return sends {1} ship(s) to MISSION ANCHOR/recovery point(s): {2}.",
					player, recovering.Length, reason);
			}
			raidMissionOrigins.Clear();
		}

		void MaintainRaidRecovery(IBot bot, IReadOnlyCollection<Actor> ships)
		{
			foreach (var ship in raidRecoveryOrigins.Keys.ToArray())
			{
				if (ship == null || !ship.IsInWorld || ship.IsDead || !ships.Contains(ship))
				{
					raidRecoveryOrigins.Remove(ship);
					raidAttackMoveRecoveryActors.Remove(ship);
					continue;
				}
				var anchor = raidRecoveryOrigins[ship];
				if ((ship.Location - anchor).LengthSquared <= 4)
				{
					raidRecoveryOrigins.Remove(ship);
					raidAttackMoveRecoveryActors.Remove(ship);
					continue;
				}
				if (raidAttackMoveRecoveryActors.Contains(ship))
					QueueAttackMove(bot, ship, anchor, false);
				else
					QueueMove(bot, ship, anchor, false);
			}
		}

		bool IsTargetWithinWeaponRange(Actor attacker, Actor target) =>
			IsTargetWithinWeaponRangeAtPosition(attacker, target, attacker.CenterPosition);

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

		bool ShouldEnterFight()
		{
			var radiusSq = Info.FightTriggerRadius * Info.FightTriggerRadius;
			return activeShips.Any(s => (s.Location - activeMoveDestination).LengthSquared <= radiusSq);
		}

		void ExecuteFight(IBot bot, Actor missionTarget)
		{
			// No RiskModel calls in FIGHT/DEFEND micro. Active combat threats universally outrank passive structures.
			// SEA strategic structure priority (SYRD -> SPEN -> others) is handled by RAID/SECURE execution
			// only after immediate attackers have been neutralized.
			var visible = combatIntelService.VisibleEnemies.Where(IsVisibleEnemy).ToArray();
			var radiusSq = Info.FightMicroRadius * Info.FightMicroRadius;
			foreach (var ship in activeShips.OrderBy(s => s.ActorID))
			{
				var threat = visible
					.Where(combatIntelService.IsTacticalCombatThreat)
					.Where(enemy => (enemy.Location - ship.Location).LengthSquared <= radiusSq && CanAttackActor(ship, enemy))
					.OrderBy(enemy => (enemy.Location - ship.Location).LengthSquared)
					.ThenBy(enemy => enemy.ActorID)
					.FirstOrDefault();
				var chosen = threat ?? (missionTarget != null && CanAttackActor(ship, missionTarget) ? missionTarget : null);
				if (chosen != null)
					QueueAttack(bot, ship, chosen, false);
			}
		}

		CPos? FindSeaReconCell(Actor ship, CPos desired)
		{
			var mobile = ship?.TraitOrDefault<Mobile>();
			if (mobile == null || !strategicMapService.TryGetNavalRegionId(ship.Location, out var shipRegion))
				return null;

			if (world.Map.Contains(desired) &&
				mobile.CanEnterCell(desired, check: BlockedByActor.Immovable) && mobile.CanStayInCell(desired) &&
				strategicMapService.TryGetNavalRegionId(desired, out var desiredRegion) && desiredRegion == shipRegion)
				return desired;

			// A naval recon bidder is valid only if water is close enough for its own vision to
			// observe the requested ore-mine area. This naturally allows submarines on coastal sectors
			// but prevents a ship from "reconning" a deeply inland MineCluster.
			var radius = Math.Max(1, commanderCoreService.GetReconVisionCells(ship));
			return GetSeaBidTopologyCells(desired, radius)
				.Where(x => x.NavalRegionId == shipRegion)
				.Where(x => mobile.CanEnterCell(x.Cell, check: BlockedByActor.Immovable) && mobile.CanStayInCell(x.Cell))
				.OrderBy(x => x.TargetDistanceSquared)
				.ThenBy(x => (x.Cell - ship.Location).LengthSquared)
				.ThenBy(x => x.Cell.X)
				.ThenBy(x => x.Cell.Y)
				.Select(x => (CPos?)x.Cell)
				.FirstOrDefault();
		}

		void ExecuteReconMission(IBot bot, IReadOnlyCollection<Actor> ships, FransActiveMission mission)
		{
			var changed = activeTargetActorId != mission.TargetActorId || activeMissionType != FransMissionType.Recon;
			if (changed)
			{
				ResetReconState();
				if (mission.CommittedActorIds == null || mission.CommittedActorIds.Length != 1)
				{
					AbortReconMission("winning Sea RECON bid did not contain exactly one committed actor");
					return;
				}

				var selectedId = mission.CommittedActorIds[0];
				var selected = ships.FirstOrDefault(s => s.ActorID == selectedId &&
					s != reconRetreatActor && !raidRecoveryOrigins.ContainsKey(s) && s.TraitOrDefault<Cargo>() == null);
				if (selected == null)
				{
					AbortReconMission("selected Sea recon unit is no longer available");
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

				var start = FindSeaReconCell(selected, missionObjective);
				if (!start.HasValue)
				{
					AbortReconMission(reconPioneerValidationActive
						? "Sea cannot reach PIONEER exact-objective RECON; release for Ground/Air/other capability"
						: "selected Sea recon unit has no reachable water patrol start");
					return;
				}

				activeTargetActorId = mission.TargetActorId;
				activeMissionType = FransMissionType.Recon;
				activeObjective = missionObjective;
				activeMoveDestination = start.Value;
				activeOrder = FransCommanderOrder.Move;
				activeOrderStartedWorldTick = world.WorldTick;
				activeShips.Clear();
				activeShips.Add(selected);
				reconActor = selected;
				QueueSetUnitStanceOrder(bot, selected, UnitStance.HoldFire);
				reconOrigin = selected.Location;
				reconStart = start.Value;
				hasReconSearchWaypoint = false;
				reconLoggedContactIds.Clear();
				FransBotLog.BotDebug(world,
					"{0}: Sea Commander accepts persistent RECON MineCluster {1} with ONE {2} {3}; plain MOVE from {4} to water patrol start {5}. The mission has no coverage-completion threshold.",
					player, mission.TargetActorId, selected.Info.Name, selected.ActorID, reconOrigin, reconStart);
			}

			if (reconActor == null || !reconActor.IsInWorld || reconActor.IsDead ||
				!ships.Contains(reconActor) || raidRecoveryOrigins.ContainsKey(reconActor))
			{
				AbortReconMission("Sea recon unit died, entered recovery, or left Commander ownership");
				return;
			}

			if (expansionStateService != null && expansionStateService.TryGetPioneerReconObjectiveNear(activeObjective, out var exactPioneerObjective))
			{
				reconPioneerValidationActive = true;
				if (exactPioneerObjective != activeObjective)
				{
					var redirected = FindSeaReconCell(reconActor, exactPioneerObjective);
					if (!redirected.HasValue)
					{
						AbortReconMission("Sea cannot reach newly prioritized PIONEER exact objective; release for Ground/Air/other capability");
						return;
					}

					activeObjective = exactPioneerObjective;
					reconStart = redirected.Value;
					activeMoveDestination = redirected.Value;
					activeOrder = FransCommanderOrder.Move;
					activeOrderStartedWorldTick = world.WorldTick;
					hasReconSearchWaypoint = false;
					FransBotLog.BotDebug(world,
						"{0}: Sea RECON {1} redirects to PIONEER exact objective {2} via reachable water cell {3}; persistent probing is temporarily superseded until the exact ore cell is scout-cleared.",
						player, activeTargetActorId, activeObjective, reconStart);
				}
			}
			else if (reconPioneerValidationActive)
			{
				var completedMission = activeTargetActorId;
				var completedObjective = activeObjective;
				var completedUnit = reconActor.ActorID;
				commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey, "PIONEER exact-objective RECON completed");
				FransBotLog.BotDebug(world,
					"{0}: SEA PIONEER exact-objective RECON completed: mission={1} target={2} unit={3} reason=ExistingScoutClear action=ReleaseOneShotRecon.",
					player, completedMission, completedObjective, completedUnit);
				ResetMission();
				return;
			}

			if (ReconHealthBelowRetreatThreshold(reconActor, out var healthPercent))
			{
				BeginReconRetreat(bot, reconActor,
					$"health fell to {healthPercent}% (< {commanderCoreService.ReconRetreatHealthPercent}%)");
				return;
			}

			if (activeOrder == FransCommanderOrder.Move)
			{
				if ((reconActor.Location - reconStart).LengthSquared <= 1)
				{
					var vision = commanderCoreService.GetReconVisionCells(reconActor);
					if (vision <= 0)
					{
						AbortReconMission("Sea recon unit lost usable vision before patrol start");
						return;
					}

					reconSearchSpiral.Reset(reconStart, vision);
					activeOrder = FransCommanderOrder.Search;
					activeOrderStartedWorldTick = world.WorldTick;
					hasReconSearchWaypoint = false;
					FransBotLog.BotDebug(world,
						"{0}: Sea RECON {1} begins persistent probing at {2}: vision {3}, spiral spacing {4}, {5} queued plain-Move waypoints per packet. No coverage state is tracked.",
						player, activeTargetActorId, reconStart, vision, reconSearchSpiral.SpacingCells,
						commanderCoreService.ReconWaypointBatchSize);
				}
				else
					QueueMove(bot, reconActor, reconStart, false);
				return;
			}

			if (activeOrder != FransCommanderOrder.Search)
				return;

			if (TryGetReconContact(reconActor, out var contact) && reconLoggedContactIds.Add(contact.ActorID))
				FransBotLog.BotDebug(world,
					"{0}: Sea RECON MineCluster {1} sees incidental enemy {2} {3} at {4}; plain-Move probing continues and RECON never attacks the contact.",
					player, activeTargetActorId, contact.Info.Name, contact.ActorID, contact.Location);

			if (hasReconSearchWaypoint && !reconActor.IsIdle &&
				(reconActor.Location - reconSearchWaypoint).LengthSquared > 1)
				return;

			if (TryQueueReconWaypointPacket(bot, reconActor))
				return;

			var restartVision = commanderCoreService.GetReconVisionCells(reconActor);
			if (restartVision > 0)
			{
				reconSearchSpiral.Reset(reconStart, restartVision);
				hasReconSearchWaypoint = false;
				if (TryQueueReconWaypointPacket(bot, reconActor))
					return;
			}

			AbortReconMission("persistent Sea RECON has no reachable water spiral waypoint");
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
			var health = unit?.TraitOrDefault<Health>();
			if (health == null || health.MaxHP <= 0)
				return false;
			percent = Math.Clamp((int)((long)Math.Max(0, health.HP) * 100 / health.MaxHP), 0, 100);
			return (long)health.HP * 100 < (long)health.MaxHP * commanderCoreService.ReconRetreatHealthPercent;
		}

		bool TryQueueReconWaypointPacket(IBot bot, Actor ship)
		{
			var waypoints = new List<CPos>(commanderCoreService.ReconWaypointBatchSize);
			var cursor = ship.Location;
			for (var i = 0; i < commanderCoreService.ReconWaypointBatchSize; i++)
			{
				if (!reconSearchSpiral.TryGetNextWaypoint(world,
					c => FindSeaReconCell(ship, c), cursor, out var waypoint))
					break;
				waypoints.Add(waypoint);
				cursor = waypoint;
			}
			if (waypoints.Count == 0)
				return false;

			for (var i = 0; i < waypoints.Count; i++)
				bot.QueueOrder(new Order("Move", ship, Target.FromCell(world, waypoints[i]), i > 0));
			reconSearchWaypoint = waypoints[^1];
			hasReconSearchWaypoint = true;
			lastMoveDestination[ship] = reconSearchWaypoint;
			lastMoveWorldTick[ship] = world.WorldTick;
			return true;
		}

		void BeginReconRetreat(IBot bot, Actor unit, string reason)
		{
			var targetId = activeTargetActorId;
			var origin = reconOrigin;
			commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey, $"RECON -> RETREAT: {reason}");
			reconRetreatActor = unit;
			reconRetreatOrigin = origin;
			FransBotLog.BotDebug(world,
				"{0}: Sea persistent RECON {1} -> RETREAT; lone {2} {3} cancels its queued patrol and returns toward {4} with a non-queued plain Move: {5}. General keeps the RECON target open for a later bidder.",
				player, targetId, unit.Info.Name, unit.ActorID, origin, reason);
			ResetMission();
			reconRetreatActor = unit;
			reconRetreatOrigin = origin;
			PublishTransientReservations();
			QueueMove(bot, unit, origin, true);
		}

		void MaintainReconRetreat(IBot bot, IReadOnlyCollection<Actor> ships)
		{
			if (reconRetreatActor == null)
				return;
			if (!reconRetreatActor.IsInWorld || reconRetreatActor.IsDead || !ships.Contains(reconRetreatActor))
			{
				reconRetreatActor = null;
				return;
			}
			if ((reconRetreatActor.Location - reconRetreatOrigin).LengthSquared <= 4)
			{
				FransBotLog.BotDebug(world,
					"{0}: Sea RECON RETREAT complete for {1} at {2}. Ship returns to normal Commander ownership.",
					player, reconRetreatActor, reconRetreatActor.Location);
				reconRetreatActor = null;
				return;
			}
			QueueMove(bot, reconRetreatActor, reconRetreatOrigin, false);
		}

		void AbortReconMission(string reason)
		{
			commandBidService.ReleaseMission(FransCommanderKind.Sea, BidderKey, reason);
			FransBotLog.BotDebug(world,
				"{0}: Sea persistent RECON MineCluster {1} mission aborted without General completion: {2}. Target remains eligible for rebid.",
				player, activeTargetActorId, reason);
			ResetMission();
		}

		void QueueMove(IBot bot, Actor ship, CPos destination, bool force)
		{
			if (!force && lastMoveDestination.TryGetValue(ship, out var old) && old == destination)
			{
				if (!ship.IsIdle || (lastMoveWorldTick.TryGetValue(ship, out var last) && world.WorldTick - last < Info.MoveRefreshInterval))
					return;
			}
			bot.QueueOrder(new Order("Move", ship, Target.FromCell(world, destination), false));
			lastMoveDestination[ship] = destination;
			lastMoveWorldTick[ship] = world.WorldTick;
		}

		void ResetReconState()
		{
			// RECON temporarily suppresses native auto-targeting so its plain-Move doctrine cannot
			// turn into an incidental fight. Returning to normal ownership restores the global default.
			if (reconActor != null && reconActor.IsInWorld && !reconActor.IsDead)
			{
				QueueSetUnitStanceOrder(null, reconActor, UnitStance.AttackAnything);
				QueueStopOrder(null, reconActor);
			}
			reconActor = null;
			reconOrigin = default;
			reconStart = default;
			reconSearchWaypoint = default;
			hasReconSearchWaypoint = false;
			reconPioneerValidationActive = false;
			reconLoggedContactIds.Clear();
		}


		CPos? FindSeaSecureCell(Actor ship, CPos targetCell, ISet<CPos> reserved = null, int minimumDistance = 0)
		{
			var mobile = ship?.TraitOrDefault<Mobile>();
			if (mobile == null || pathFinder == null || !world.Map.Contains(targetCell))
				return null;

			var toleranceSq = Info.SecureCellCacheMovementTolerance * Info.SecureCellCacheMovementTolerance;
			var cacheKey = new SeaSecureCellCacheKey(ship.ActorID, targetCell, minimumDistance);
			if (seaSecureCellCache.TryGetValue(cacheKey, out var cached) &&
				cached.TerrainKnowledgeVersion == strategicMapService.TerrainKnowledgeVersion &&
				world.WorldTick - cached.TestedTick < Info.SecureCellCacheDuration &&
				(ship.Location - cached.ShipCell).LengthSquared <= toleranceSq)
			{
				if (!cached.Result.HasValue)
					return null;
				var cell = cached.Result.Value;
				if ((reserved == null || !reserved.Contains(cell)) &&
					mobile.CanEnterCell(cell, check: BlockedByActor.Immovable) && mobile.CanStayInCell(cell))
					return cell;
			}

			var minimumDistanceSq = minimumDistance * minimumDistance;
			var candidates = world.Map.FindTilesInCircle(targetCell, Info.SecureAssemblyRadius)
				.Where(world.Map.Contains)
				.Where(c => minimumDistance <= 0 || (c - targetCell).LengthSquared >= minimumDistanceSq)
				.Where(c => reserved == null || !reserved.Contains(c))
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.Where(c => pathFinder.PathMightExistForLocomotorBlockedByImmovable(mobile.Locomotor, ship.Location, c))
				.OrderBy(c => (c - targetCell).LengthSquared > Info.CohesionFormationRadius * Info.CohesionFormationRadius ? 1 : 0)
				.ThenByDescending(OffshorePreference)
				.ThenBy(c => (c - targetCell).LengthSquared)
				.ThenBy(c => (c - ship.Location).LengthSquared)
				.ThenBy(c => c.X).ThenBy(c => c.Y)
				.Take(24)
				.ToArray();
			if (candidates.Length == 0)
			{
				if (reserved == null)
					seaSecureCellCache[cacheKey] = new SeaSecureCellCacheEntry
					{
						ShipCell = ship.Location,
						Result = null,
						TerrainKnowledgeVersion = strategicMapService.TerrainKnowledgeVersion,
						TestedTick = world.WorldTick
					};
				return null;
			}

			var path = pathFinder.FindPathToTargetCells(ship, ship.Location, candidates, BlockedByActor.Immovable);
			var result = path.Count > 0 ? path[0] : (CPos?)null;
			if (reserved == null || result.HasValue)
				seaSecureCellCache[cacheKey] = new SeaSecureCellCacheEntry
				{
					ShipCell = ship.Location,
					Result = result,
					TerrainKnowledgeVersion = strategicMapService.TerrainKnowledgeVersion,
					TestedTick = world.WorldTick
				};
			return result;
		}


		CPos? FindRememberedMoveDestination(Actor ship, CPos targetCell, bool targetIsBuilding)
		{
			var mobile = ship?.TraitOrDefault<Mobile>();
			if (mobile == null || !strategicMapService.TryGetNavalRegionId(ship.Location, out var shipRegion))
				return null;
			if (world.Map.Contains(targetCell) && mobile.CanEnterCell(targetCell, check: BlockedByActor.Immovable) && mobile.CanStayInCell(targetCell) &&
				strategicMapService.TryGetNavalRegionId(targetCell, out var targetRegion) && targetRegion == shipRegion)
				return targetCell;
			return world.Map.FindTilesInCircle(targetCell, Info.ShoreBombardmentSupportRadius)
				.Where(world.Map.Contains)
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.Where(c => strategicMapService.TryGetNavalRegionId(c, out var region) && region == shipRegion)
				.OrderByDescending(OffshorePreference)
				.ThenBy(c => (c - targetCell).LengthSquared)
				.ThenBy(c => (c - ship.Location).LengthSquared)
				.ThenBy(c => c.X).ThenBy(c => c.Y).Select(c => (CPos?)c).FirstOrDefault();
		}

		CPos? FindReachableRaidFiringPosition(Actor ship, Actor target, ISet<CPos> reserved = null)
		{
			if (!CanAttackActor(ship, target))
				return null;
			if (IsTargetWithinWeaponRange(ship, target) && (reserved == null || !reserved.Contains(ship.Location)))
				return ship.Location;
			var mobile = ship.TraitOrDefault<Mobile>();
			if (mobile == null || pathFinder == null)
				return null;

			var candidates = world.Map.FindTilesInCircle(target.Location, Info.ShoreBombardmentSupportRadius)
				.Where(world.Map.Contains)
				.Where(c => reserved == null || !reserved.Contains(c))
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.Where(c => IsTargetWithinWeaponRangeFromCell(ship, target, c))
				.Where(c => pathFinder.PathMightExistForLocomotorBlockedByImmovable(mobile.Locomotor, ship.Location, c))
				.OrderBy(c => (c - target.Location).LengthSquared > Info.CohesionFormationRadius * Info.CohesionFormationRadius ? 1 : 0)
				.ThenByDescending(OffshorePreference)
				.ThenBy(c => (c - ship.Location).LengthSquared)
				.ThenBy(c => (c - target.Location).LengthSquared)
				.ThenBy(c => c.X).ThenBy(c => c.Y)
				.Take(64)
				.ToArray();
			if (candidates.Length == 0)
				return null;

			// Exact native path proof is execution-only in. Idle bidding uses cheap shared
			// StrategicMap naval-region topology, preventing ten Sea capacities from repeating A*.
			var path = pathFinder.FindPathToTargetCells(ship, ship.Location, candidates, BlockedByActor.Immovable);
			return path.Count > 0 ? path[0] : (CPos?)null;
		}

		CPos? FindMoveDestination(Actor ship, Actor target)
		{
			if (!CanAttackActor(ship, target))
				return null;
			if (IsTargetWithinWeaponRange(ship, target))
				return ship.Location;
			var mobile = ship.TraitOrDefault<Mobile>();
			if (mobile == null || !strategicMapService.TryGetNavalRegionId(ship.Location, out var shipRegion))
				return null;
			return world.Map.FindTilesInCircle(target.Location, Info.ShoreBombardmentSupportRadius)
				.Where(world.Map.Contains)
				.Where(c => mobile.CanEnterCell(c, check: BlockedByActor.Immovable) && mobile.CanStayInCell(c))
				.Where(c => IsTargetWithinWeaponRangeFromCell(ship, target, c))
				.Where(c => strategicMapService.TryGetNavalRegionId(c, out var region) && region == shipRegion)
				.OrderByDescending(OffshorePreference)
				.ThenBy(c => (c - ship.Location).LengthSquared)
				.ThenBy(c => (c - target.Location).LengthSquared)
				.ThenBy(c => c.X).ThenBy(c => c.Y).Select(c => (CPos?)c).FirstOrDefault();
		}

		void RememberMissionAnchor(FransActiveMission mission)
		{
			hasMissionAnchorPoint = mission.HasAnchorPoint;
			missionAnchorPoint = mission.HasAnchorPoint ? mission.AnchorPoint : default;
		}

		bool IsSeaRecoveryReady(Actor ship)
		{
			if (ship == null || !ship.IsInWorld || ship.IsDead)
				return false;
			var repairable = ship.TraitOrDefault<RepairableNear>();
			return repairable == null || ship.GetDamageState() <= DamageState.Undamaged;
		}

		void RouteSeaRetreatUnit(IBot bot, Actor ship, bool forceMove)
		{
			var repairable = ship.TraitOrDefault<RepairableNear>();
			if (repairable != null && ship.GetDamageState() > DamageState.Undamaged)
			{
				var harbour = repairable.FindRepairBuilding(ship);
				if (harbour != null)
				{
					if (ship.IsIdle)
						bot.QueueOrder(new Order("RepairNear", ship, Target.FromActor(harbour), false));
					return;
				}
			}

			QueueAttackMove(bot, ship, retreatAnchorPoint, forceMove);
		}

		void QueueAttackMove(IBot bot, Actor ship, CPos destination, bool force)
		{
			if (!force && lastMoveDestination.TryGetValue(ship, out var old) && old == destination)
			{
				// Native AttackMove owns physical execution. Do not reset the same path on
				// every strategic refresh; reassert only after the ship becomes idle/stalled.
				if (!ship.IsIdle || (lastMoveWorldTick.TryGetValue(ship, out var last) && world.WorldTick - last < Info.MoveRefreshInterval))
					return;
			}
			bot.QueueOrder(new Order("AttackMove", ship, Target.FromCell(world, destination), false));
			lastMoveDestination[ship] = destination;
			lastMoveWorldTick[ship] = world.WorldTick;
		}

		void QueueAttack(IBot bot, Actor ship, Actor target, bool force)
		{
			if (!force && lastFightTarget.TryGetValue(ship, out var old) && old == target.ActorID &&
				lastFightWorldTick.TryGetValue(ship, out var last) && world.WorldTick - last < Info.FightRefreshInterval)
				return;
			bot.QueueOrder(new Order("Attack", ship, Target.FromActor(target), false));
			lastFightTarget[ship] = target.ActorID;
			lastFightWorldTick[ship] = world.WorldTick;
		}

		bool IsManagedShip(Actor actor)
		{
			return actor != null && actor.IsInWorld && !actor.IsDead && actor.Owner == player &&
				Info.ManagedNavalCombatTypes.Contains(actor.Info.Name) && actor.TraitOrDefault<Mobile>() != null;
		}

		bool CanAttackActor(Actor ship, Actor target)
		{
			if (!IsVisibleEnemy(target))
				return false;
			var attackTarget = Target.FromActor(target);
			return ship.TraitsImplementing<AttackBase>()
				.Any(attack => !attack.IsTraitDisabled && !attack.IsTraitPaused && attack.HasAnyValidWeapons(attackTarget));
		}

		bool IsEnemyActor(Actor target) => target?.Owner != null &&
			PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(target.Owner));

		bool IsVisibleEnemy(Actor target)
		{
			return target != null && target.IsInWorld && !target.IsDead && target.OccupiesSpace != null &&
				target.CanBeViewedByPlayer(player) && PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(target.Owner));
		}

		int GetCombatValue(Actor actor) => commanderCoreService.GetActorValue(actor);

		void ResetMission()
		{
			activeShips.Clear();
			activeTargetActorId = 0;
			combinedSecureHoldTargetActorId = 0;
			combinedSecureHoldUntilTick = -1;
			activeObjective = default;
			activeMoveDestination = default;
			activeOrder = FransCommanderOrder.Move;
			activeMissionType = FransMissionType.Recon;
			activeOrderStartedWorldTick = world.WorldTick;
			lostContactSinceWorldTick = -1;
			secureClearSinceWorldTick = -1;
			secureAssemblyBestCount = 0;
			secureAssemblyLastProgressTick = -1;
			secureCohesionBypassUntilTick = 0;
			hasMissionAnchorPoint = false;
			missionAnchorPoint = default;
			ResetReconState();
			raidMissionOrigins.Clear();
			cohesionHeldShips.Clear();
			cohesionFormationSlots.Clear();
			hasCohesionFormationObjective = false;
			cohesionFormationObjective = default;
			raidStrikeIssued = false;
			ResetRaidLostTargetSearch(false);
			hasMoveRiskCheck = false;
			moveRiskAllowed = false;
			nextMoveRiskCheckTick = 0;
		}
	}
}
