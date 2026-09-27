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
using System.Collections.Generic;
using System.Linq;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	public enum FransCommanderKind
	{
		Ground,
		Air,
		Sea,
		Transport,
		SpecOps
	}

	/// <summary>
	/// Commander execution states. MOVE is ordinary strategic transit; SEARCH is the plain-Move
	/// expanding RECON spiral. FIGHT/DEFEND/RETREAT remain combat/survival states.
	/// </summary>
	public enum FransCommanderOrder
	{
		Move,
		Search,
		Fight,
		Defend,
		Retreat
	}


	/// <summary>
	/// Pure waypoint geometry for persistent RECON probing. The square spiral advances in coarse
	/// cardinal steps sized to about 75% of the unit's current vision radius. Commanders decide
	/// lifecycle, movement batching and retreat; this helper only generates deterministic reachable
	/// points and never tracks coverage or mission completion.
	/// </summary>
	public sealed class FransSearchSpiral
	{
		readonly HashSet<CPos> issuedWaypoints = [];
		CPos conceptualCell;
		int direction;
		int legLengthSteps;
		int stepsRemaining;
		int legsAtCurrentLength;
		int spacingCells;

		public int SpacingCells => spacingCells;

		public void Reset(CPos center, int visionCells)
		{
			conceptualCell = center;
			direction = 0;
			legLengthSteps = 1;
			stepsRemaining = 1;
			legsAtCurrentLength = 0;
			// Standard square-spiral geometry can separate neighboring parallel legs by two
			// step lengths. 0.75R therefore yields <= 1.5R between sweeps (except R=1
			// where the cell grid forces a one-cell step), leaving sight overlap.
			spacingCells = Math.Max(1, visionCells * 3 / 4);
			issuedWaypoints.Clear();
			issuedWaypoints.Add(center);
		}

		public bool TryGetNextWaypoint(World world, Func<CPos, CPos?> resolveWaypoint, CPos currentCell, out CPos waypoint)
		{
			waypoint = default;
			if (world == null || resolveWaypoint == null || spacingCells <= 0)
				return false;

			var bounds = world.Map.Bounds;
			var width = Math.Max(1, bounds.Right - bounds.Left);
			var height = Math.Max(1, bounds.Bottom - bounds.Top);
			var maxAttempts = Math.Max(128, ((width + height) * 8 / Math.Max(1, spacingCells)) + 128);

			for (var attempt = 0; attempt < maxAttempts; attempt++)
			{
				var delta = direction switch
				{
					0 => new CPos(spacingCells, 0),
					1 => new CPos(0, spacingCells),
					2 => new CPos(-spacingCells, 0),
					_ => new CPos(0, -spacingCells)
				};
				conceptualCell = new CPos(conceptualCell.X + delta.X, conceptualCell.Y + delta.Y);
				stepsRemaining--;
				if (stepsRemaining <= 0)
				{
					direction = (direction + 1) & 3;
					legsAtCurrentLength++;
					if (legsAtCurrentLength >= 2)
					{
						legLengthSteps++;
						legsAtCurrentLength = 0;
					}
					stepsRemaining = legLengthSteps;
				}

				var clamped = new CPos(
					Math.Clamp(conceptualCell.X, bounds.Left, bounds.Right - 1),
					Math.Clamp(conceptualCell.Y, bounds.Top, bounds.Bottom - 1));
				var resolved = resolveWaypoint(clamped);
				if (!resolved.HasValue || !world.Map.Contains(resolved.Value) ||
					resolved.Value == currentCell || !issuedWaypoints.Add(resolved.Value))
					continue;

				waypoint = resolved.Value;
				return true;
			}

			return false;
		}
	}

	public readonly record struct FransCommanderBidReport(
		FransCommanderKind Commander,
		string BidderKey,
		uint SubjectActorId,
		uint[] CommittedActorIds,
		int TotalCost,
		int RouteRisk,
		int TravelCost,
		int ForceCost,
		int EstimatedEtaTicks,
		int OfferedContribution,
		int RequiredContribution,
		bool IsSpecialistCapability,
		int DefendUtility = 0,
		int DefendStrengthScore = 0,
		int DefendUrgencyScore = 0,
		int DefendAssetRiskScore = 0,
		int DefendResponseTimeCost = 0,
		int DefendOpportunityCost = 0);

	public readonly record struct FransActiveMission(
		uint TargetActorId,
		string TargetActorType,
		bool TargetIsBuilding,
		CPos LastVisibleTargetCell,
		FransSiteIntel SiteIntel,
		FransCommanderKind Commander,
		string BidderKey,
		uint SubjectActorId,
		FransMissionType MissionType,
		FransCommanderOrder InitialOrder,
		int TotalCost,
		int RouteRisk,
		int TravelCost,
		int ForceCost,
		int StrategicPriority,
		int EstimatedEtaTicks,
		uint[] CommittedActorIds,
		int OfferedContribution,
		int RequiredContribution,
		bool IsSpecialistCapability,
		bool HasAnchorPoint,
		CPos AnchorPoint,
		int StartedWorldTick,
		int ExecuteAfterWorldTick,
		int CombinedSecureGroupSize,
		uint MissionId = 0);

	/// <summary>
	/// Generic deterministic broker between General and all combat Commander capacities.
	/// General publishes strategic missions; Commanders independently evaluate AVAILABLE -> CAPABILITY -> ETA ->
	/// RISK -> FORCE SIZING -> BID and submit a complete snapshot. The broker never re-prices or rebuilds an
	/// accepted actor snapshot. DEFEND is the explicit strategic exception to ordinary ownership: while DEFEND
	/// pressure is active, Commanders may release SECURE so the same actors can rebid for defense. SECURE remains
	/// single-domain because Ground territorial sufficiency cannot be established by summing contributions from
	/// domains with different threat-removal semantics. DEFEND arbitration compares force fulfillment
	/// first, then ETA, so the strongest available response can launch when no capacity can reach the full 3x
	/// requirement. Transport remains a service Commander.
	/// </summary>
	public interface IFransCommandBidService
	{
		void SubmitMissionBid(FransMission mission, FransCommanderBidReport report);
		bool TryGetActiveMissionForBidder(FransCommanderKind commander, string bidderKey,
			out Actor target, out FransActiveMission mission);
		bool TryGetActiveMissionForTarget(uint targetActorId, out FransActiveMission mission);
		bool TryGetActorActiveMission(uint actorId, out FransActiveMission mission);
		bool IsDefenseTarget(Actor target);
		bool HasActiveReconMission(uint targetActorId);
		int GetActiveReconMissionCount();
		int GetActiveOrFreshPendingMissionCount(FransCommanderKind commander, FransMissionType missionType);
		bool IsDefendPressureActive();
		bool IsStrategicDefendPressureActive();
		bool ShouldPreemptSecureForDefend(FransCommanderKind commander, string bidderKey, CPos secureCell);
		bool HasOtherActiveSecureMission(uint targetActorId, FransCommanderKind commander, string bidderKey);
		bool HasReconBid(uint targetActorId);
		bool HasFreshPendingMissionBid(FransCommanderKind commander, FransMissionType missionType, uint targetActorId, string excludingBidderKey);
		void ClearPendingMissionBids(FransCommanderKind commander, string bidderKey, FransMissionType missionType);
		bool IsActorUnavailableForBidder(FransCommanderKind commander, string bidderKey, uint actorId);
		bool IsCapacityUnavailableForMissionBid(FransCommanderKind commander, string bidderKey);
		int MissionBidAvailabilityRevision { get; }
		bool IsActorUnavailableForMissionBid(FransCommanderKind commander, string bidderKey, uint actorId);
		bool TryGetActorMission(FransCommanderKind commander, uint actorId, out FransMissionType missionType, out string bidderKey);
		void UpdateTransientActorReservations(FransCommanderKind commander, string bidderKey, IReadOnlyCollection<uint> actorIds);
		void ReleaseMission(FransCommanderKind commander, string bidderKey, string reason);
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Generic Fransbot command broker. Commander evaluation lives in FransCommanderCore; this module only stores bids, arbitrates capacities and owns mission/reservation state.")]
	public class FransCommandBidBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("World ticks between auction maintenance scans.")]
		public readonly int ScanInterval = 25;

		[Desc("How long a newly published MISSION waits for Commander bids before arbitration.")]
		public readonly int BidWindowTicks = 50;

		[Desc("Forget a pending bid if its Commander has not refreshed it within this many world ticks.")]
		public readonly int BidFreshnessTicks = 100;

		[Desc("Minimum DEFEND strategic priority that may globally block/preempt SECURE. Lower-priority DEFEND remains active but does not stop SECURE.")]
		public readonly int SecurePreemptDefendPriorityMinimum = 750;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			if (ScanInterval < 25 || BidWindowTicks <= 0 || BidFreshnessTicks <= 0 || SecurePreemptDefendPriorityMinimum < 0)
				throw new YamlException("FransCommandBid timing values must be positive, ScanInterval must be at least 25 world ticks, and SecurePreemptDefendPriorityMinimum must be non-negative.");
		}

		public override object Create(ActorInitializer init) { return new FransCommandBidBotModule(init.Self, this); }
	}

	public class FransCommandBidBotModule : ConditionalTrait<FransCommandBidBotModuleInfo>, IBotTick, IFransCommandBidService
	{
		sealed class Bid
		{
			public FransCommanderKind Commander;
			public string BidderKey;
			public uint SubjectActorId;
			public uint[] CommittedActorIds = Array.Empty<uint>();
			public int TotalCost;
			public int RouteRisk;
			public int TravelCost;
			public int ForceCost;
			public int StrategicPriority;
			public int EstimatedEtaTicks;
			public int OfferedContribution;
			public int RequiredContribution;
			public bool IsSpecialistCapability;
			public int DefendUtility;
			public int DefendStrengthScore;
			public int DefendUrgencyScore;
			public int DefendAssetRiskScore;
			public int DefendResponseTimeCost;
			public int DefendOpportunityCost;
			public int WorldTick;
		}

		sealed class Auction
		{
			public uint MissionId;
			public uint TargetActorId;
			public string TargetActorType;
			public bool TargetIsBuilding;
			public Actor Target;
			public CPos LastVisibleCell;
			public bool IsRememberedIntel;
			public FransSiteIntel SiteIntel;
			public FransMissionType MissionType;
			public bool Initialized;
			public int StrategicPriority;
			public int OpenedWorldTick;
			public readonly Dictionary<string, Bid> Bids = [];
			public readonly Dictionary<string, FransActiveMission> ActiveMissions = [];

			public FransActiveMission? Mission => ActiveMissions.Count == 0
				? null
				: ActiveMissions.Values
					.OrderBy(m => m.StartedWorldTick)
					.ThenBy(m => m.Commander)
					.ThenBy(m => m.BidderKey, StringComparer.Ordinal)
					.First();
		}

		sealed class TransientReservation
		{
			public FransCommanderKind Commander;
			public string BidderKey;
			public uint[] ActorIds = Array.Empty<uint>();
			public int WorldTick;
		}

		readonly World world;
		readonly Player player;
		readonly Dictionary<uint, Auction> auctions = [];
		readonly Dictionary<string, TransientReservation> transientReservations = [];

		// PERFORMANCE-ONLY mission-availability index. The previous hot path repeatedly walked
		// every auction, active mission and transient reservation once per candidate actor.
		// These sets preserve the exact ownership semantics but turn those lookups into O(1).
		readonly HashSet<string> missionBidActiveCapacityKeys = new(StringComparer.Ordinal);
		readonly HashSet<string> missionBidTransientCapacityKeys = new(StringComparer.Ordinal);
		readonly Dictionary<uint, string> bidderActiveActorOwners = [];
		readonly Dictionary<uint, string> bidderTransientActorOwners = [];
		int missionBidAvailabilityRevision;
		int missionBidIndexBuiltRevision = -1;
		int missionBidIndexWorldTick = int.MinValue;

		IFransGeneralService generalService;
		IFransCaptureTransportService transportService;
		int scanTicks;
		int lastMaintenanceWorldTick = int.MinValue;

		public FransCommandBidBotModule(Actor self, FransCommandBidBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		public int MissionBidAvailabilityRevision => missionBidAvailabilityRevision;

		void InvalidateMissionBidAvailabilityIndex()
		{
			unchecked { missionBidAvailabilityRevision++; }
		}

		static void AddActorOwner(Dictionary<uint, string> owners, uint actorId, string capacityKey)
		{
			if (actorId == 0 || string.IsNullOrEmpty(capacityKey))
				return;
			if (!owners.TryGetValue(actorId, out var existing))
			{
				owners.Add(actorId, capacityKey);
				return;
			}

			// Empty string is an internal MULTIPLE-OWNERS sentinel. Normal broker invariants
			// prevent this, but preserving it makes owner-aware availability exact even if an
			// actor is ever observed in more than one committed ownership record.
			if (!string.Equals(existing, capacityKey, StringComparison.Ordinal))
				owners[actorId] = string.Empty;
		}

		void EnsureMissionBidAvailabilityIndex()
		{
			if (missionBidIndexWorldTick == world.WorldTick && missionBidIndexBuiltRevision == missionBidAvailabilityRevision)
				return;

			using var perf = FransBotLog.Profile(world, player, "CommandBid.AvailabilityIndexBuild");
			missionBidActiveCapacityKeys.Clear();
			missionBidTransientCapacityKeys.Clear();
			bidderActiveActorOwners.Clear();
			bidderTransientActorOwners.Clear();

			foreach (var auction in auctions.Values)
				foreach (var mission in auction.ActiveMissions.Values)
				{
					var key = CapacityKey(mission.Commander, mission.BidderKey);
					missionBidActiveCapacityKeys.Add(key);
					foreach (var actorId in MissionActorIds(mission))
					{
						if (actorId == 0)
							continue;
						AddActorOwner(bidderActiveActorOwners, actorId, key);
					}
				}

			var freshness = Math.Max(Info.BidFreshnessTicks, 100);
			foreach (var reservation in transientReservations.Values)
			{
				if (reservation.ActorIds.Length == 0 || world.WorldTick - reservation.WorldTick > freshness)
					continue;
				var key = CapacityKey(reservation.Commander, reservation.BidderKey);
				missionBidTransientCapacityKeys.Add(key);
				foreach (var actorId in reservation.ActorIds)
				{
					if (actorId == 0)
						continue;
					AddActorOwner(bidderTransientActorOwners, actorId, key);
				}
			}

			missionBidIndexWorldTick = world.WorldTick;
			missionBidIndexBuiltRevision = missionBidAvailabilityRevision;
		}

		protected override void Created(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;
			generalService = self.Owner.PlayerActor.TraitsImplementing<IFransGeneralService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransCommandBid requires FransGeneralBotModule.");
			transportService = self.Owner.PlayerActor.TraitsImplementing<IFransCaptureTransportService>().FirstOrDefault();
		}

		protected override void TraitEnabled(Actor self)
		{
			scanTicks = (int)((self.ActorID + 20u) % (uint)Info.ScanInterval) + 1;
			lastMaintenanceWorldTick = int.MinValue;
			auctions.Clear();
			transientReservations.Clear();
			InvalidateMissionBidAvailabilityIndex();
			FransBotLog.BotDebug(world,
				"{0}: FransCommandBid current broker active: DEFEND auctions use stable General MissionId even when the visible representative changes; partial DEFEND ranks strength before ETA. SECURE assignments are single-domain; Ground territorial sufficiency is never inferred from cross-domain contribution arithmetic. Strategic DEFEND >= {1} preempts SECURE under the existing coverage rule.", player, Info.SecurePreemptDefendPriorityMinimum);
		}

		protected override void TraitDisabled(Actor self)
		{
			auctions.Clear();
			transientReservations.Clear();
			InvalidateMissionBidAvailabilityIndex();
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransCommandBid.BotTick");
			if (player.WinState != WinState.Undefined)
				return;
			if (--scanTicks > 0)
				return;
			scanTicks = Info.ScanInterval;
			MaintainAuctions();
		}

		static uint MissionAuctionId(FransMission mission) => mission.MissionId != 0 ? mission.MissionId : mission.TargetActorId;

		public void SubmitMissionBid(FransMission mission, FransCommanderBidReport report)
		{
			if (report.Commander == FransCommanderKind.Transport || mission.TargetActorId == 0 ||
				string.IsNullOrEmpty(report.BidderKey) || report.SubjectActorId == 0 || report.TotalCost < 0 ||
				report.EstimatedEtaTicks < 0 || report.RequiredContribution <= 0 || report.OfferedContribution < 0)
				return;

			var ids = (report.CommittedActorIds ?? Array.Empty<uint>()).Where(id => id != 0).Distinct().OrderBy(id => id).ToArray();
			if (ids.Length == 0)
				ids = new[] { report.SubjectActorId };
			if (!ids.Contains(report.SubjectActorId))
				return;

			MaintainAuctions();
			if (mission.Type == FransMissionType.Secure && IsStrategicDefendPressureActive())
				return;
			foreach (var id in ids)
			{
				var actor = world.GetActorById(id);
				if (actor == null || !actor.IsInWorld || actor.IsDead || actor.Owner != player ||
					IsActorUnavailableForMissionBid(report.Commander, report.BidderKey, id))
					return;
			}

			var auctionId = MissionAuctionId(mission);
			if (!auctions.TryGetValue(auctionId, out var auction))
			{
				auction = new Auction { OpenedWorldTick = world.WorldTick };
				UpdateAuctionFromMission(auction, mission);
				auctions[auctionId] = auction;
			}
			else
			{
				if (auction.Mission.HasValue)
					return;

				// MaintainAuctions() above already reconciled this target to General's current
				// MissionType. Never let a Commander submit an older mission snapshot and
				// silently reclassify the pending auction back to its stale type.
				if (!auction.Initialized || auction.MissionType != mission.Type)
					return;
			}

			var key = CapacityKey(report.Commander, report.BidderKey);
			auction.Bids[key] = new Bid
			{
				Commander = report.Commander,
				BidderKey = report.BidderKey,
				SubjectActorId = report.SubjectActorId,
				CommittedActorIds = ids,
				TotalCost = report.TotalCost,
				RouteRisk = report.RouteRisk,
				TravelCost = report.TravelCost,
				ForceCost = report.ForceCost,
				StrategicPriority = mission.StrategicPriority,
				EstimatedEtaTicks = report.EstimatedEtaTicks,
				OfferedContribution = report.OfferedContribution,
				RequiredContribution = report.RequiredContribution,
				IsSpecialistCapability = report.IsSpecialistCapability,
				DefendUtility = report.DefendUtility,
				DefendStrengthScore = report.DefendStrengthScore,
				DefendUrgencyScore = report.DefendUrgencyScore,
				DefendAssetRiskScore = report.DefendAssetRiskScore,
				DefendResponseTimeCost = report.DefendResponseTimeCost,
				DefendOpportunityCost = report.DefendOpportunityCost,
				WorldTick = world.WorldTick
			};
		}

		public bool TryGetActiveMissionForBidder(FransCommanderKind commander, string bidderKey,
			out Actor target, out FransActiveMission mission)
		{
			MaintainAuctions();
			var match = auctions.Values
				.SelectMany(a => a.ActiveMissions.Values.Select(m => (Auction: a, Mission: m)))
				.Where(x => x.Mission.Commander == commander && x.Mission.BidderKey == bidderKey)
				.OrderBy(x => x.Mission.StartedWorldTick)
				.ThenBy(x => x.Mission.TargetActorId)
				.FirstOrDefault();

			if (match.Auction == null)
			{
				target = null;
				mission = default;
				return false;
			}

			target = IsValidVisibleEnemy(match.Auction.Target) ? match.Auction.Target : null;
			mission = match.Mission;
			return true;
		}

		public bool TryGetActiveMissionForTarget(uint targetActorId, out FransActiveMission mission)
		{
			if (targetActorId != 0)
			{
				var auction = auctions.Values.FirstOrDefault(a => a.TargetActorId == targetActorId && a.Mission.HasValue);
				if (auction != null)
				{
					mission = auction.Mission.Value;
					return true;
				}
			}
			mission = default;
			return false;
		}

		public bool TryGetActorActiveMission(uint actorId, out FransActiveMission mission)
		{
			if (actorId != 0)
				foreach (var auction in auctions.Values.OrderBy(a => a.TargetActorId))
					foreach (var active in auction.ActiveMissions.Values
						.OrderBy(m => m.Commander).ThenBy(m => m.BidderKey, StringComparer.Ordinal))
					{
						if (!MissionActorIds(active).Contains(actorId))
							continue;
						mission = active;
						return true;
					}

			mission = default;
			return false;
		}

		public bool IsDefenseTarget(Actor target) => generalService != null && generalService.IsDefenseTarget(target);

		public bool HasActiveReconMission(uint targetActorId) => targetActorId != 0 && auctions.TryGetValue(targetActorId, out var auction) &&
			auction.MissionType == FransMissionType.Recon && auction.Mission.HasValue && auction.Mission.Value.MissionType == FransMissionType.Recon;

		public int GetActiveReconMissionCount()
		{
			MaintainAuctions();
			return auctions.Values.Count(a => a.Mission.HasValue && a.Mission.Value.MissionType == FransMissionType.Recon);
		}

		public int GetActiveOrFreshPendingMissionCount(FransCommanderKind commander, FransMissionType missionType)
		{
			MaintainAuctions();
			return auctions.Values.Count(a =>
				a.ActiveMissions.Values.Any(m => m.Commander == commander && m.MissionType == missionType) ||
				(!a.Mission.HasValue && a.MissionType == missionType && a.Bids.Values.Any(b =>
					b.Commander == commander && world.WorldTick - b.WorldTick <= Info.BidFreshnessTicks &&
					(missionType == FransMissionType.Defend || missionType == FransMissionType.Secure || b.OfferedContribution >= b.RequiredContribution))));
		}

		public bool IsDefendPressureActive()
		{
			generalService?.EnsureCurrentMissions();
			MaintainAuctions();
			return (generalService != null && generalService.CurrentMissions.Any(m => m.Type == FransMissionType.Defend)) ||
				auctions.Values.Any(a => a.Mission.HasValue && a.Mission.Value.MissionType == FransMissionType.Defend);
		}

		public bool IsStrategicDefendPressureActive()
		{
			generalService?.EnsureCurrentMissions();
			MaintainAuctions();
			return (generalService != null && generalService.CurrentMissions.Any(m =>
				m.Type == FransMissionType.Defend && m.StrategicPriority >= Info.SecurePreemptDefendPriorityMinimum)) ||
				auctions.Values.Any(a => a.Mission.HasValue && a.Mission.Value.MissionType == FransMissionType.Defend &&
					a.Mission.Value.StrategicPriority >= Info.SecurePreemptDefendPriorityMinimum);
		}


		public bool ShouldPreemptSecureForDefend(FransCommanderKind commander, string bidderKey, CPos secureCell)
		{
			generalService?.EnsureCurrentMissions();
			MaintainAuctions();
			if (generalService == null)
				return false;
			_ = secureCell;

			foreach (var defend in generalService.CurrentMissions
				.Where(m => m.Type == FransMissionType.Defend && m.StrategicPriority >= Info.SecurePreemptDefendPriorityMinimum)
				.OrderByDescending(m => m.StrategicPriority).ThenBy(m => m.TargetActorId))
			{
				if (!auctions.TryGetValue(MissionAuctionId(defend), out var auction))
					return true;

				var coveredByOtherCapacity = auction.ActiveMissions.Values.Any(m =>
					m.MissionType == FransMissionType.Defend &&
					(m.Commander != commander || !string.Equals(m.BidderKey, bidderKey, StringComparison.Ordinal)));
				if (!coveredByOtherCapacity)
					coveredByOtherCapacity = auction.Bids.Values.Any(b =>
						(b.Commander != commander || !string.Equals(b.BidderKey, bidderKey, StringComparison.Ordinal)) &&
						world.WorldTick - b.WorldTick <= Info.BidFreshnessTicks && b.OfferedContribution > 0);

				if (!coveredByOtherCapacity)
					return true;
			}

			return false;
		}

		public bool HasOtherActiveSecureMission(uint targetActorId, FransCommanderKind commander, string bidderKey)
		{
			if (targetActorId == 0 || !auctions.TryGetValue(targetActorId, out var auction))
				return false;

			return auction.ActiveMissions.Values.Any(m => m.MissionType == FransMissionType.Secure &&
				(m.Commander != commander || !string.Equals(m.BidderKey, bidderKey, StringComparison.Ordinal)));
		}

		public bool HasReconBid(uint targetActorId) => targetActorId != 0 && auctions.TryGetValue(targetActorId, out var auction) &&
			auction.MissionType == FransMissionType.Recon && auction.Bids.Count > 0;

		public bool HasFreshPendingMissionBid(FransCommanderKind commander, FransMissionType missionType, uint targetActorId, string excludingBidderKey)
		{
			if (targetActorId == 0 || !auctions.TryGetValue(targetActorId, out var auction) || auction.Mission.HasValue ||
				auction.MissionType != missionType)
				return false;

			return auction.Bids.Values.Any(b => b.Commander == commander &&
				!string.Equals(b.BidderKey, excludingBidderKey, StringComparison.Ordinal) &&
				world.WorldTick - b.WorldTick <= Info.BidFreshnessTicks &&
				(missionType == FransMissionType.Defend || b.OfferedContribution >= b.RequiredContribution));
		}

		public void ClearPendingMissionBids(FransCommanderKind commander, string bidderKey, FransMissionType missionType)
		{
			MaintainAuctions();
			if (string.IsNullOrEmpty(bidderKey))
				return;
			var key = CapacityKey(commander, bidderKey);
			foreach (var auction in auctions.Values)
				if (!auction.Mission.HasValue && auction.MissionType == missionType)
					auction.Bids.Remove(key);
		}

		static IEnumerable<uint> MissionActorIds(FransActiveMission mission)
		{
			if (mission.CommittedActorIds != null && mission.CommittedActorIds.Length > 0)
				return mission.CommittedActorIds;
			return mission.SubjectActorId != 0 ? new[] { mission.SubjectActorId } : Array.Empty<uint>();
		}

		static IEnumerable<uint> BidActorIds(Bid bid)
		{
			if (bid.CommittedActorIds != null && bid.CommittedActorIds.Length > 0)
				return bid.CommittedActorIds;
			return bid.SubjectActorId != 0 ? new[] { bid.SubjectActorId } : Array.Empty<uint>();
		}

		static string CapacityKey(FransCommanderKind commander, string bidderKey) => $"{(int)commander}:{bidderKey}";

		public bool IsActorUnavailableForBidder(FransCommanderKind commander, string bidderKey, uint actorId)
		{
			if (actorId == 0 || string.IsNullOrEmpty(bidderKey))
				return false;

			if (transportService?.IsHandlingPassenger(actorId) == true)
				return true;

			EnsureMissionBidAvailabilityIndex();
			var key = CapacityKey(commander, bidderKey);
			if (bidderActiveActorOwners.TryGetValue(actorId, out var activeOwner) &&
				(string.IsNullOrEmpty(activeOwner) || !string.Equals(activeOwner, key, StringComparison.Ordinal)))
				return true;

			// Service ownership is intentionally owner-aware: a capacity must still be able to
			// route/repair/rearm its own RETREAT/recovery actors while every other capacity sees them busy.
			return bidderTransientActorOwners.TryGetValue(actorId, out var transientOwner) &&
				(string.IsNullOrEmpty(transientOwner) || !string.Equals(transientOwner, key, StringComparison.Ordinal));
		}

		public bool IsCapacityUnavailableForMissionBid(FransCommanderKind commander, string bidderKey)
		{
			if (string.IsNullOrEmpty(bidderKey))
				return false;
			EnsureMissionBidAvailabilityIndex();
			var key = CapacityKey(commander, bidderKey);
			return missionBidActiveCapacityKeys.Contains(key) || missionBidTransientCapacityKeys.Contains(key);
		}

		public bool IsActorUnavailableForMissionBid(FransCommanderKind commander, string bidderKey, uint actorId)
		{
			if (actorId == 0 || string.IsNullOrEmpty(bidderKey))
				return false;

			// Transport ownership is real actor ownership even before native Cargo removes the passenger
			// from World.GetActorById(). Revalidate this here as well as at BID submission so an older
			// SpecOps offer cannot win during the short Waiting/Pickup/boarding window after Transport
			// has already accepted the same E6/Tanya ActorID.
			if (transportService?.IsHandlingPassenger(actorId) == true)
				return true;

			EnsureMissionBidAvailabilityIndex();
			var key = CapacityKey(commander, bidderKey);

			// One capacity may own only one unit of committed work at a time. RETREAT/recovery is
			// committed survival work, so even a different free actor cannot be used for a new MISSION BID
			// until that capacity clears its transient reservation.
			if (missionBidActiveCapacityKeys.Contains(key) || missionBidTransientCapacityKeys.Contains(key))
				return true;

			return bidderActiveActorOwners.ContainsKey(actorId) || bidderTransientActorOwners.ContainsKey(actorId);
		}

		public bool TryGetActorMission(FransCommanderKind commander, uint actorId, out FransMissionType missionType, out string bidderKey)
		{
			foreach (var auction in auctions.Values.OrderBy(a => a.TargetActorId))
				foreach (var mission in auction.ActiveMissions.Values
					.OrderBy(m => m.Commander).ThenBy(m => m.BidderKey, StringComparer.Ordinal))
				{
					if (mission.Commander != commander || !MissionActorIds(mission).Contains(actorId))
						continue;
					missionType = mission.MissionType;
					bidderKey = mission.BidderKey;
					return true;
				}
			missionType = default;
			bidderKey = null;
			return false;
		}

		public void UpdateTransientActorReservations(FransCommanderKind commander, string bidderKey, IReadOnlyCollection<uint> actorIds)
		{
			if (string.IsNullOrEmpty(bidderKey))
				return;
			var key = CapacityKey(commander, bidderKey);
			var ids = actorIds?.Where(id => id != 0).Distinct().OrderBy(id => id).ToArray() ?? Array.Empty<uint>();
			if (ids.Length == 0)
			{
				if (transientReservations.Remove(key))
					InvalidateMissionBidAvailabilityIndex();
				return;
			}
			transientReservations[key] = new TransientReservation
			{
				Commander = commander, BidderKey = bidderKey, ActorIds = ids, WorldTick = world.WorldTick
			};
			InvalidateMissionBidAvailabilityIndex();
		}

		void WithdrawPendingBidsForCapacity(FransCommanderKind commander, string bidderKey)
		{
			if (string.IsNullOrEmpty(bidderKey))
				return;
			var key = CapacityKey(commander, bidderKey);
			foreach (var auction in auctions.Values)
				auction.Bids.Remove(key);
		}

		public void ReleaseMission(FransCommanderKind commander, string bidderKey, string reason)
		{
			foreach (var auction in auctions.Values.Where(a => a.Mission.HasValue).ToArray())
			{
				var key = CapacityKey(commander, bidderKey);
				if (!auction.ActiveMissions.TryGetValue(key, out var mission))
					continue;
				auction.ActiveMissions.Remove(key);
				InvalidateMissionBidAvailabilityIndex();
				if (auction.ActiveMissions.Count == 0)
				{
					auction.OpenedWorldTick = world.WorldTick;
					auction.Bids.Clear();
				}
				FransBotLog.BotDebug(world, "{0}: {1} Commander releases MISSION for target {2}: {3}.",
					player, commander, mission.TargetActorId, reason);
			}
		}

		static int MissionTypeTieBreakRank(FransMissionType kind) => kind switch
		{
			FransMissionType.Defend => 4,
			FransMissionType.Secure => 3,
			FransMissionType.Raid => 2,
			FransMissionType.Recon => 1,
			_ => 0
		};

		static bool PreferCurrentMission(FransMission candidate, FransMission existing)
		{
			if (candidate.StrategicPriority != existing.StrategicPriority)
				return candidate.StrategicPriority > existing.StrategicPriority;
			var candidateRank = MissionTypeTieBreakRank(candidate.Type);
			var existingRank = MissionTypeTieBreakRank(existing.Type);
			if (candidateRank != existingRank)
				return candidateRank > existingRank;
			return candidate.PublishedWorldTick > existing.PublishedWorldTick;
		}

		Dictionary<uint, FransMission> BuildCurrentMissionIndex()
		{
			var index = new Dictionary<uint, FransMission>();
			if (generalService == null)
				return index;
			foreach (var mission in generalService.CurrentMissions)
			{
				if (mission.TargetActorId == 0)
					continue;
				var missionId = MissionAuctionId(mission);
				if (!index.TryGetValue(missionId, out var existing) || PreferCurrentMission(mission, existing))
					index[missionId] = mission;
			}
			return index;
		}

		void MaintainAuctions()
		{
			if (lastMaintenanceWorldTick == world.WorldTick)
				return;
			lastMaintenanceWorldTick = world.WorldTick;

			var removedTransientReservation = false;
			foreach (var stale in transientReservations
				.Where(p => world.WorldTick - p.Value.WorldTick > Math.Max(Info.BidFreshnessTicks, 100))
				.Select(p => p.Key).ToArray())
				removedTransientReservation |= transientReservations.Remove(stale);
			if (removedTransientReservation)
				InvalidateMissionBidAvailabilityIndex();

			var currentMissions = BuildCurrentMissionIndex();
			foreach (var pair in auctions.ToArray())
			{
				var auction = pair.Value;
				// Ordinary accepted assignments remain immutable snapshots. DEFEND is the intentional
				// exception: its stable General MissionId is the lifetime identity, while the visible
				// representative is tactical evidence that may change during the same hostile incident.
				if (auction.Mission.HasValue)
				{
					if (auction.MissionType != FransMissionType.Defend)
						continue;

					if (!currentMissions.TryGetValue(pair.Key, out var authoritativeDefend) &&
						!generalService.TryGetDefendIncident(auction.MissionId, out authoritativeDefend))
					{
						foreach (var active in auction.ActiveMissions.Values.OrderBy(m => m.Commander).ThenBy(m => m.BidderKey, StringComparer.Ordinal))
							FransBotLog.BotDebug(world,
								"{0}: [DEFEND RELEASE] mission={1} representative={2} authoritativeIncident=Inactive reason=General incident lease ended; Broker releases {3}/{4}.",
								player, auction.MissionId, auction.TargetActorId, active.Commander, active.BidderKey);
						auctions.Remove(pair.Key);
						InvalidateMissionBidAvailabilityIndex();
						continue;
					}

					var oldRepresentative = auction.TargetActorId;
					UpdateAuctionFromMission(auction, authoritativeDefend);
					foreach (var key in auction.ActiveMissions.Keys.ToArray())
					{
						var active = auction.ActiveMissions[key];
						auction.ActiveMissions[key] = active with
						{
							MissionId = auction.MissionId,
							TargetActorId = auction.TargetActorId,
							TargetActorType = auction.TargetActorType,
							TargetIsBuilding = auction.TargetIsBuilding,
							LastVisibleTargetCell = auction.LastVisibleCell,
							SiteIntel = auction.SiteIntel,
							StrategicPriority = auction.StrategicPriority
						};
					}

					if (oldRepresentative != auction.TargetActorId)
						FransBotLog.BotDebug(world,
							"{0}: [DEFEND INCIDENT] mission={1} oldRepresentative={2} newRepresentative={3} action=RepresentativeUpdated cell={4}.",
							player, auction.MissionId, oldRepresentative, auction.TargetActorId, auction.LastVisibleCell);
					continue;
				}

				if (!currentMissions.TryGetValue(pair.Key, out var mission))
				{
					auctions.Remove(pair.Key);
					continue;
				}
				UpdateAuctionFromMission(auction, mission);
				foreach (var bid in auction.Bids.Values)
					bid.StrategicPriority = auction.StrategicPriority;
				foreach (var staleBid in auction.Bids
					.Where(b => world.WorldTick - b.Value.WorldTick > Info.BidFreshnessTicks)
					.Select(b => b.Key).ToArray())
					auction.Bids.Remove(staleBid);
			}

			var dueTargets = auctions
				.Where(p => !p.Value.Mission.HasValue && world.WorldTick - p.Value.OpenedWorldTick >= Info.BidWindowTicks && p.Value.Bids.Count > 0)
				.Select(p => p.Key).ToHashSet();
			if (dueTargets.Count == 0)
				return;

			// A complete single-Commander bid wins normally. DEFEND retains its intentional
			// partial-bid exception; every other mission requires its own authoritative contribution.
			var candidates = auctions
				.Where(p => dueTargets.Contains(p.Key))
				.SelectMany(p => p.Value.Bids.Values.Select(b => (TargetId: p.Key, Auction: p.Value, Bid: b)))
				.Where(x => x.Auction.MissionType == FransMissionType.Defend || x.Bid.OfferedContribution >= x.Bid.RequiredContribution)
				.Where(x => !IsCommanderCapacityCommitted(x.Bid))
				.OrderByDescending(x => x.Bid.StrategicPriority)
				.ThenByDescending(x => x.Auction.MissionType == FransMissionType.Defend)
				.ThenByDescending(x => x.Auction.MissionType == FransMissionType.Defend ? x.Bid.DefendUtility : 0)
				.ThenByDescending(x => x.Auction.MissionType == FransMissionType.Defend && x.Bid.OfferedContribution >= x.Bid.RequiredContribution)
				.ThenByDescending(x => x.Auction.MissionType == FransMissionType.Defend ? x.Bid.OfferedContribution : 0)
				.ThenBy(x => x.Auction.MissionType == FransMissionType.Defend ? x.Bid.EstimatedEtaTicks : x.Bid.TotalCost)
				.ThenBy(x => x.Bid.RouteRisk)
				.ThenBy(x => x.Bid.TravelCost)
				.ThenBy(x => x.Bid.ForceCost)
				.ThenBy(x => x.Bid.Commander)
				.ThenBy(x => x.Bid.BidderKey, StringComparer.Ordinal)
				.ThenBy(x => x.Bid.SubjectActorId)
				.ThenBy(x => x.TargetId)
				.ToArray();

			var usedCapacity = new HashSet<string>();
			foreach (var candidate in candidates)
			{
				if (candidate.Auction.Mission.HasValue)
					continue;
				var key = CapacityKey(candidate.Bid.Commander, candidate.Bid.BidderKey);
				if (usedCapacity.Contains(key) || IsCommanderCapacityCommitted(candidate.Bid))
					continue;
				if (AssignAuction(candidate.Auction, candidate.Bid))
					usedCapacity.Add(key);
			}
		}

		void UpdateAuctionFromMission(Auction auction, FransMission mission)
		{
			if (auction.Initialized && !auction.Mission.HasValue && auction.MissionType != mission.Type)
			{
				var previousType = auction.MissionType;
				var staleBidCount = auction.Bids.Count;
				auction.Bids.Clear();
				auction.OpenedWorldTick = world.WorldTick;
				FransBotLog.BotDebug(world,
					"{0}: MISSION BROKER target {1} changes pending MissionType {2} -> {3}; clears {4} stale bids and restarts the bid window. No bid may cross MissionType identity.",
					player, mission.TargetActorId, previousType, mission.Type, staleBidCount);
			}

			auction.MissionId = MissionAuctionId(mission);
			auction.TargetActorId = mission.TargetActorId;
			auction.TargetActorType = mission.TargetActorType;
			auction.TargetIsBuilding = mission.IsBuilding;
			auction.Target = mission.Target;
			auction.LastVisibleCell = mission.LastVisibleTargetCell;
			auction.IsRememberedIntel = mission.IsRememberedIntel;
			auction.SiteIntel = mission.SiteIntel;
			auction.MissionType = mission.Type;
			auction.StrategicPriority = mission.StrategicPriority;
			auction.Initialized = true;
		}

		bool IsCommanderCapacityCommitted(Bid bid)
		{
			if (IsCapacityUnavailableForMissionBid(bid.Commander, bid.BidderKey))
				return true;
			return BidActorIds(bid).Any(id => IsActorUnavailableForMissionBid(bid.Commander, bid.BidderKey, id));
		}

		bool AssignAuction(Auction auction, Bid winner)
		{
			if (auction.Mission.HasValue ||
				(auction.MissionType != FransMissionType.Defend && winner.OfferedContribution < winner.RequiredContribution))
				return false;
			if (IsCommanderCapacityCommitted(winner))
				return false;

			var committed = BidActorIds(winner).Distinct().OrderBy(id => id).ToArray();
			if (committed.Length == 0 || !committed.Contains(winner.SubjectActorId))
				return false;
			foreach (var id in committed)
			{
				var actor = world.GetActorById(id);
				if (actor == null || !actor.IsInWorld || actor.IsDead || actor.Owner != player ||
					IsActorUnavailableForMissionBid(winner.Commander, winner.BidderKey, id))
					return false;
			}

			var initialOrder = auction.MissionType == FransMissionType.Defend ? FransCommanderOrder.Defend : FransCommanderOrder.Move;
			var subject = world.GetActorById(winner.SubjectActorId);
			var anchor = default(CPos);
			var hasAnchor = auction.MissionType != FransMissionType.Recon &&
				generalService.TrySelectAnchorPoint(winner.Commander, auction.MissionType, committed, subject, auction.LastVisibleCell, out anchor);

			var next = new FransActiveMission(
				auction.TargetActorId, auction.TargetActorType, auction.TargetIsBuilding, auction.LastVisibleCell, auction.SiteIntel,
				winner.Commander, winner.BidderKey, winner.SubjectActorId, auction.MissionType, initialOrder,
				winner.TotalCost, winner.RouteRisk, winner.TravelCost, winner.ForceCost, winner.StrategicPriority,
				winner.EstimatedEtaTicks, committed, winner.OfferedContribution, winner.RequiredContribution,
				winner.IsSpecialistCapability, hasAnchor, anchor, world.WorldTick, world.WorldTick, 1, auction.MissionId);
			auction.ActiveMissions[CapacityKey(winner.Commander, winner.BidderKey)] = next;
			InvalidateMissionBidAvailabilityIndex();
			auction.Bids.Clear();
			// A winning capacity has committed its availability snapshot. Every other pending offer
			// from that same capacity is now stale and is removed immediately instead of surviving
			// into mission end/recovery where it could win without a fresh evaluation.
			WithdrawPendingBidsForCapacity(winner.Commander, winner.BidderKey);

			if (auction.MissionType == FransMissionType.Raid)
				FransBotLog.BotDebug(world,
					"{0}: MISSION BROKER starts MISSION RAID {1} {2} at {3} to {4}/{5}: exact committed actor snapshot [{6}], contribution {7}/{8}, ETA {9} WT, price {10}, route peak {11}. No broker re-pricing or preemption.",
					player, auction.TargetActorType, auction.TargetActorId, auction.LastVisibleCell, next.Commander, next.BidderKey,
					string.Join(",", next.CommittedActorIds), next.OfferedContribution, next.RequiredContribution,
					next.EstimatedEtaTicks, next.TotalCost, next.RouteRisk);
			else if (auction.MissionType == FransMissionType.Defend)
				FransBotLog.BotDebug(world,
					"{0}: MISSION BROKER starts MISSION DEFEND MissionId {1}, representative {2} at {3} to {4}/{5}: strength {6}/{7} units (full={8}), ETA {9} WT, exact actors [{10}], route peak {11}, utility {12} (strength {13}, urgency {14}, asset-risk {15}, response cost {16}, opportunity cost {17}).",
					player, auction.MissionId, auction.TargetActorId, auction.LastVisibleCell, next.Commander, next.BidderKey,
					next.OfferedContribution, next.RequiredContribution, next.OfferedContribution >= next.RequiredContribution,
					next.EstimatedEtaTicks, string.Join(",", next.CommittedActorIds), next.RouteRisk,
					winner.DefendUtility, winner.DefendStrengthScore, winner.DefendUrgencyScore, winner.DefendAssetRiskScore,
					winner.DefendResponseTimeCost, winner.DefendOpportunityCost);
			else
				FransBotLog.BotDebug(world,
					"{0}: MISSION BROKER starts MISSION {1} {2} at {3} to {4}/{5}: order {6}, priority {7}, exact actors [{8}], price {9}, ETA {10} WT, route peak {11}; capacity owns mission until Commander release/RETREAT.",
					player, auction.MissionType.ToString().ToUpperInvariant(), auction.TargetActorId, auction.LastVisibleCell,
					next.Commander, next.BidderKey, next.InitialOrder, next.StrategicPriority,
					string.Join(",", next.CommittedActorIds), next.TotalCost, next.EstimatedEtaTicks, next.RouteRisk);
			return true;
		}

		bool IsValidVisibleEnemy(Actor target)
		{
			if (target == null || !target.IsInWorld || target.IsDead || target.OccupiesSpace == null ||
				!target.CanBeViewedByPlayer(player) || !PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(target.Owner)))
				return false;
			var type = target.Info.Name;
			return !target.Info.HasTraitInfo<HuskInfo>() &&
				!type.EndsWith(".husk", StringComparison.OrdinalIgnoreCase) &&
				!type.EndsWith("husk", StringComparison.OrdinalIgnoreCase);
		}
	}
}
