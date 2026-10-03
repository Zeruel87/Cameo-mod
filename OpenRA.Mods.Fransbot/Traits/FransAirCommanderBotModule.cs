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
using OpenRA.Mods.Common.Activities;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	internal struct FransKnownAntiAirPreparedWork
	{
		public bool Enabled;
		public int SegmentChecks;
		public long SegmentZoneChecks;
		public long SegmentCellSamples;
		public long PreparedCellChecks;
		public int EscapeFallbackSegmentChecks;
	}

	/// <summary>
	/// Exact discrete-cell union of the current known-AA exclusion circles. Ordinary segments
	/// sample the same cells as the legacy per-zone loop, but test the prepared union once per
	/// sample. A segment starting inside the union retains the legacy per-zone escape rule.
	/// </summary>
	internal sealed class FransKnownAntiAirPreparedExclusion
	{
		readonly FransKnownAntiAirGeometryIdentity geometryIdentity;
		readonly CPos[] zoneCenters;
		readonly HashSet<long> excludedCoordinates = [];
		readonly long radiusSquared;

		public FransKnownAntiAirGeometryIdentity GeometryIdentity => geometryIdentity;
		public int Signature => geometryIdentity.Signature;
		public int SafetyRadius => geometryIdentity.SafetyRadius;
		public int ZoneCount => zoneCenters.Length;
		public int ExcludedCellCount => excludedCoordinates.Count;
		public CPos ZoneCenterAt(int index) => zoneCenters[index];

		public FransKnownAntiAirPreparedExclusion(FransKnownAntiAirGeometryIdentity geometryIdentity)
		{
			this.geometryIdentity = geometryIdentity ?? throw new ArgumentNullException(nameof(geometryIdentity));
			zoneCenters = Enumerable.Range(0, geometryIdentity.ZoneCount)
				.Select(i => geometryIdentity.ZoneAt(i).Center).ToArray();
			radiusSquared = (long)SafetyRadius * SafetyRadius;

			var extent = SafetyRadius - 1;
			foreach (var center in zoneCenters)
				for (var dx = -extent; dx <= extent; dx++)
					for (var dy = -extent; dy <= extent; dy++)
						if ((long)dx * dx + (long)dy * dy < radiusSquared)
							excludedCoordinates.Add(CoordinateKey(center.X + dx, center.Y + dy));
		}

		static long CoordinateKey(int x, int y) => ((long)x << 32) ^ (uint)y;

		static long CellDistanceSquared(CPos a, CPos b)
		{
			var dx = (long)a.X - b.X;
			var dy = (long)a.Y - b.Y;
			return dx * dx + dy * dy;
		}

		internal static int InterpolateCellCoordinate(int origin, int delta, int step, int steps)
		{
			var numerator = (long)delta * step;
			if (numerator >= 0)
				numerator += steps / 2;
			else
				numerator -= steps / 2;
			return origin + (int)(numerator / steps);
		}

		bool IsExcluded(CPos cell) => excludedCoordinates.Contains(CoordinateKey(cell.X, cell.Y));

		public bool IsCellOutside(CPos cell, ref FransKnownAntiAirPreparedWork work)
		{
			if (work.Enabled)
				work.PreparedCellChecks++;
			return !IsExcluded(cell);
		}

		public bool SegmentStaysOutside(CPos from, CPos to, ref FransKnownAntiAirPreparedWork work)
		{
			if (work.Enabled)
				work.SegmentChecks++;
			if (zoneCenters.Length == 0)
				return true;

			var dx = to.X - from.X;
			var dy = to.Y - from.Y;
			var steps = Math.Max(Math.Abs(dx), Math.Abs(dy));
			if (steps == 0)
				return IsCellOutside(from, ref work);

			if (IsCellOutside(from, ref work))
			{
				for (var i = 1; i <= steps; i++)
				{
					var cell = new CPos(
						InterpolateCellCoordinate(from.X, dx, i, steps),
						InterpolateCellCoordinate(from.Y, dy, i, steps));
					if (work.Enabled)
					{
						work.SegmentCellSamples++;
						work.PreparedCellChecks++;
					}
					if (IsExcluded(cell))
						return false;
				}

				return true;
			}

			// Preserve the legacy semantics exactly when the segment begins inside one or
			// more known-AA zones. Every zone is checked independently: an existing zone
			// may only be escaped without first moving closer, and no other zone may be entered.
			if (work.Enabled)
				work.EscapeFallbackSegmentChecks++;
			foreach (var center in zoneCenters)
			{
				if (work.Enabled)
					work.SegmentZoneChecks++;
				var previousDistance = CellDistanceSquared(from, center);
				var escapedExistingZone = previousDistance >= radiusSquared;
				for (var i = 1; i <= steps; i++)
				{
					var cell = new CPos(
						InterpolateCellCoordinate(from.X, dx, i, steps),
						InterpolateCellCoordinate(from.Y, dy, i, steps));
					var distance = CellDistanceSquared(cell, center);
					if (work.Enabled)
						work.SegmentCellSamples++;

					if (!escapedExistingZone)
					{
						if (distance < previousDistance)
							return false;
						if (distance >= radiusSquared)
							escapedExistingZone = true;
						previousDistance = distance;
						continue;
					}

					if (distance < radiusSquared)
						return false;
				}
			}

			return true;
		}
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Fransbot Air Commander. Uses the General auction/mission lifecycle for DEFEND/SECURE/RECON/RAID. Air SECURE owns domain-specific CLEAR validation with persistent remembered enemy buildings; domain CLEAR closes Air work without changing Ground territorial state. OpenRA-native aircraft orders execute movement, combat and return-to-base behavior.")]
	public class FransAirCommanderBotModuleInfo : ConditionalTraitInfo
	{
		[ActorReference]
		public readonly FrozenSet<string> ManagedAircraftTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Non-building mobile target types that Air is allowed to RAID. Buildings are always eligible. adds MCV and tank targets so aircraft doctrine can distinguish soft-strike YAK/HIND work from hard-strike MIG/HELI work.")]
		public readonly FrozenSet<string> RaidEligibleMobileTargetTypes =
			FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Known enemy static anti-air actor types that create a hard Air PathMove exclusion zone.")]
		public readonly FrozenSet<string> KnownAntiAirStructureTypes =
			FrozenSet<string>.Empty;

		[Desc("Hard minimum cell distance that Air Commander PathMove routes must keep from legitimately known SAM/AA positions. This is a routing exclusion, not merely a RiskModel price.")]
		public readonly int KnownAntiAirPathSafetyRadius = 8;

		[Desc("Unique CommandBid capacity key for this Air wing. Multiple FransAirCommander traits may coexist as independent wings as long as every key is unique.")]
		public readonly string BidderKey = "air1";

		[Desc("Zero-based Air wing index. Used only to deterministically stagger scans and select the single wing that writes aggregate Air-utilization diagnostics.")]
		public readonly int WingIndex = 0;

		[Desc("World ticks between aggregate Air-utilization diagnostics. Only WingIndex 0 writes this summary.")]
		public readonly int UtilizationLogInterval = 750;

		[Desc("World ticks between Air Commander execution/mission-state decisions. Active missions keep this responsive cadence.")]
		public readonly int ScanInterval = 25;

		[Desc("World ticks between full idle Air auction/bid scans. Active mission execution and attack callbacks remain on ScanInterval; this only throttles repeated expensive no-mission path/risk bidding.")]
		public readonly int IdleBidInterval = 75;

		[Desc("Maximum aircraft committed to the Air Commander's current bid mission.")]
		public readonly int MaximumAircraftPerMission = 4;

		[Desc("Distance in cells at which MOVE becomes FIGHT for the active MISSION target.")]
		public readonly int FightTriggerRadius = 10;

		[Desc("Local FIGHT/DEFEND target search radius.")]
		public readonly int FightMicroRadius = 16;

		[Desc("Minimum world ticks before refreshing an unchanged MOVE order.")]
		public readonly int MoveRefreshInterval = 75;

		[Desc("Minimum world ticks before refreshing an unchanged explicit attack order.")]
		public readonly int FightRefreshInterval = 50;

		[Desc("Minimum world ticks before repeating ReturnToBase while waiting for rearm/service.")]
		public readonly int ReturnToBaseRetryHoldTicks = 250;

		[Desc("Maximum world ticks before the first progressive STRIKE without any improvement in the committed wing's approach toward the exact visible RAID target before the stalled mission is ended into normal service recovery.")]
		public readonly int RaidPreStrikeProgressWatchdogTicks = 750;

		[Desc("After an Air RAID has been awarded, ordinary RiskModel changes below this peak score do not cancel the pre-strike approach. Hard known SAM/AA exclusion remains immediate and separate. This commitment hysteresis prevents GO/RETREAT oscillation from marginal shared-risk revisions.")]
		public readonly int RaidCommittedRiskAbortScore = 420;

		[Desc("World ticks a committed pre-strike Air RAID route must remain at or above RaidCommittedRiskAbortScore before the mission is released for re-bid. Hard known SAM/AA exclusion still aborts immediately.")]
		public readonly int RaidCommittedRiskAbortHoldTicks = 150;

		[Desc("Maximum world ticks after STRIKE NOW without ammo expenditure or continued approach progress from the remaining committed wing before a stalled native Attack is ended and routed to normal RAID recovery.")]
		public readonly int RaidStrikeAmmoProgressWatchdogTicks = 500;

		[Desc("World ticks without meaningful repair/rearm/regroup progress before RETREAT recovery force-refreshes the appropriate native service or Move order.")]
		public readonly int RecoveryProgressWatchdogTicks = 750;

		[Desc("Minimum world ticks between forced recovery-watchdog order refreshes for the same aircraft.")]
		public readonly int RecoveryWatchdogRetryHoldTicks = 250;

		[Desc("If true, an armed damaged aircraft may rejoin at the recovery ANCHOR POINT after the watchdog interval when no compatible repair building exists. This prevents permanent recovery deadlock after repair infrastructure is lost.")]
		public readonly bool RecoveryAllowUnrepairedWithoutRepairBuilding = true;

		[Desc("How long FIGHT may continue around the last visible target cell after contact is lost.")]
		public readonly int FightLostContactHoldTicks = 200;

		[Desc("Radius around a SECURE objective used to detect visible attackable enemy combat presence.")]
		public readonly int SecureThreatRadius = 14;

		[Desc("Radius around the SECURE objective used to confirm the Air group has physically reached the won area.")]
		public readonly int SecureAssemblyRadius = 8;

		[Desc("World ticks a SECURE area must remain clear while at least 75 percent of the committed Air mission group is present.")]
		public readonly int SecureClearHoldTicks = 250;

		[Desc("During FIGHT, retreat when surviving committed Air combat value falls to this percentage or less of the campaign high-water value.")]
		public readonly int RetreatAtRemainingForcePercent = 50;

		[Desc("After RETREAT, ordinary offensive bidding resumes when this percentage of the locked combat baseline is physically reassembled.")]
		public readonly int ResumeOffenseAtOriginalForcePercent = 75;

		[Desc("Radius around the retreat point used to count physically regrouped Air combat value.")]
		public readonly int RetreatAssemblyRadius = 8;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			if (string.IsNullOrWhiteSpace(BidderKey) || WingIndex < 0 || WingIndex > 9 || UtilizationLogInterval <= 0 || KnownAntiAirPathSafetyRadius <= 0 ||
				ScanInterval < 25 || IdleBidInterval < ScanInterval || MaximumAircraftPerMission <= 0 || FightTriggerRadius <= 0 || FightMicroRadius <= 0 ||
				MoveRefreshInterval <= 0 || FightRefreshInterval <= 0 || ReturnToBaseRetryHoldTicks < 0 ||
				RaidPreStrikeProgressWatchdogTicks <= 0 || RaidCommittedRiskAbortScore <= 0 || RaidCommittedRiskAbortHoldTicks < ScanInterval || RaidStrikeAmmoProgressWatchdogTicks <= 0 || RecoveryProgressWatchdogTicks <= 0 || RecoveryWatchdogRetryHoldTicks < 0 || FightLostContactHoldTicks <= 0 ||
				SecureThreatRadius <= 0 || SecureAssemblyRadius <= 0 || SecureClearHoldTicks <= 0 || RetreatAssemblyRadius <= 0 ||
				RetreatAtRemainingForcePercent <= 0 || RetreatAtRemainingForcePercent >= 100 ||
				ResumeOffenseAtOriginalForcePercent <= RetreatAtRemainingForcePercent || ResumeOffenseAtOriginalForcePercent > 100)
				throw new YamlException("Frans Air Commander bidder key, wing index, timing/radius/retreat values are invalid.");
		}

		public override object Create(ActorInitializer init) { return new FransAirCommanderBotModule(init.Self, this); }
	}

	public class FransAirCommanderBotModule : ConditionalTrait<FransAirCommanderBotModuleInfo>, IBotTick, IBotEnabled, IBotRespondToAttack
	{
		enum RaidLostTargetConfirmationState
		{
			Available,
			Active,
			Consumed
		}

		sealed class SecureProgressDiagnostic
		{
			public CPos Objective;
			public CPos LastCell;
			public long PreviousDistanceSquared;
			public long LastDistanceSquared;
			public long BestDistanceSquared;
			public int LastMovementWorldTick;
			public int LastProgressWorldTick;
			public bool ImprovedOnLastSample;
			public bool ImprovedSinceLastReport;
		}

		sealed class SecureMoveIntentDiagnostic
		{
			public CPos RequestedDestination;
			public CPos CurrentCell;
			public bool IsIdle;
			public bool CachedDestinationMatched;
			public bool KnownAaSignatureMatched;
			public int PreviousMoveWorldTick = -1;
			public int EventWorldTick;
			public int WaypointCount;
			public int QueuedCount;
			public int SuppressedNonIdleCount;
			public int SuppressedRefreshHoldCount;
			public int RejectedKnownAaCount;
			public string Outcome = "None";
			public string CurrentActivity = "NotCaptured";
			public bool? ActivityIsExpectedMove;
		}

		sealed class KnownAntiAirPathPerformanceDiagnostic
		{
			public bool GeometryCacheHit;
			public bool PhysicalGeometrySolve;
			public int ZoneCount;
			public int CandidatePointChecks;
			public int PreparedExcludedCellCount;
			public long PreparedCellChecks;
			public bool PreparedGeometryReused;
			public int EscapeFallbackSegmentChecks;
			public int SegmentChecks;
			public long SegmentZoneChecks;
			public long SegmentCellSamples;
			public int NodeCount;
			public int GraphPasses;
			public long GraphSelectionChecks;
			public long GraphNeighborChecks;
			public long PathElapsedTimestampTicks;
			public long NodeBuildElapsedTimestampTicks;
			public long GraphElapsedTimestampTicks;
			public long RiskElapsedTimestampTicks;
			public long EtaElapsedTimestampTicks;
			public int RiskCellCount;
			public string Outcome = "NotRun";
		}

		readonly record struct AirRaidRoutePerformanceDiagnostic(
			uint ActorId,
			CPos StartCell,
			CPos TargetCell,
			bool CacheHit,
			bool Feasible,
			bool IsCritical,
			KnownAntiAirPathPerformanceDiagnostic Path);

		sealed class AirRaidCandidatePerformanceDiagnostic
		{
			public readonly uint TargetActorId;
			public readonly string TargetActorType;
			public readonly CPos TargetCell;
			public readonly List<AirRaidRoutePerformanceDiagnostic> Routes = [];
			public int AvailableAttackers;
			public int AntiAirPathRejected;
			public int MetricRejected;
			public long ElapsedTimestampTicks;

			public AirRaidCandidatePerformanceDiagnostic(FransMission mission)
			{
				TargetActorId = mission.TargetActorId;
				TargetActorType = mission.TargetActorType;
				TargetCell = mission.LastVisibleTargetCell;
			}
		}

		sealed class AirRaidBidPassPerformanceDiagnostic
		{
			public int RaidMissionCount;
			public int RaidTemplateHits;
			public int RaidTemplateMisses;
			public int KnownAntiAirSignature = -1;
			public int RiskRevision = -1;
			public readonly List<AirRaidCandidatePerformanceDiagnostic> Candidates = [];
		}

		const double AirRaidBidPerformanceLogThresholdMilliseconds = 10.0;

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

		readonly HashSet<Actor> activeAircraft = [];
		readonly Dictionary<Actor, CPos> lastMoveDestination = [];
		readonly Dictionary<Actor, int> lastMoveWorldTick = [];
		readonly Dictionary<Actor, int> lastMoveKnownAntiAirSignature = [];
		readonly Dictionary<Actor, uint> lastFightTarget = [];
		readonly Dictionary<Actor, int> lastFightWorldTick = [];
		readonly Dictionary<Actor, int> lastReturnWorldTick = [];
		readonly Dictionary<Actor, int> lastRepairWorldTick = [];
		readonly Dictionary<Actor, int> raidRecoverySince = [];
		readonly Dictionary<Actor, CPos> raidRecoveryAnchors = [];
		readonly Dictionary<Actor, CPos> raidMissionOrigins = [];
		readonly HashSet<Actor> raidAttackMoveHomeActors = [];
		readonly Dictionary<Actor, int> recoveryLastObservedHp = [];
		readonly Dictionary<Actor, int> recoveryLastObservedAmmoCount = [];
		readonly Dictionary<Actor, long> recoveryLastObservedAnchorDistance = [];
		readonly Dictionary<Actor, long> recoveryLastObservedServiceDistance = [];
		readonly Dictionary<Actor, int> recoveryLastProgressWorldTick = [];
		readonly Dictionary<Actor, int> recoveryLastWatchdogReissueWorldTick = [];
		readonly List<Actor> staleActorCacheKeys = [];
		readonly HashSet<uint> lastRaidCapacityProtectedActorIds = [];
		uint lastRaidCapacityProtectedTargetActorId;
		readonly Dictionary<uint, int> factRaidDiagnosticNextTick = [];
		readonly Dictionary<uint, string> factRaidDiagnosticLastOutcome = [];
		readonly Dictionary<uint, SecureProgressDiagnostic> secureProgressDiagnostics = [];
		readonly Dictionary<uint, SecureMoveIntentDiagnostic> secureMoveIntentDiagnostics = [];

		IFransCombatIntelService combatIntelService;
		IFransRiskModelService riskModelService;
		IFransCommandBidService commandBidService;
		IFransCommanderCoreService commanderCoreService;
		IFransGeneralService generalService;
		IFransExpansionStateService expansionStateService;

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
		Actor reconActor;
		CPos reconOrigin;
		CPos reconStart;
		CPos reconSearchWaypoint;
		bool hasReconSearchWaypoint;
		bool reconPioneerValidationActive;
		const int PioneerReconNoProgressTimeoutTicks = 750;
		int reconPioneerBestDistanceSquared = int.MaxValue;
		int reconPioneerLastProgressWorldTick = -1;
		RaidLostTargetConfirmationState raidLostTargetConfirmationState;
		int raidStrikeLastObservedAmmo = -1;
		int raidStrikeLastAmmoProgressWorldTick = -1;
		int raidApproachBestOutOfRangeCount = int.MaxValue;
		int raidApproachBestMaxDistanceCells = int.MaxValue;
		int raidApproachLastProgressWorldTick = -1;
		readonly HashSet<uint> reconLoggedContactIds = [];
		Actor reconRetreatActor;
		CPos reconRetreatOrigin;
		bool hasMoveRiskCheck;
		bool moveRiskAllowed;
		CPos moveRiskObjective;
		bool raidStrikeIssued;
		readonly HashSet<uint> raidPreStrikeDroppedActorIds = [];
		readonly Dictionary<uint, int> raidCommittedContributionByActor = [];
		int raidLastRiskRevision = -1;
		CPos raidLastRiskObjective;
		int raidCommittedCriticalRiskSinceTick = -1;
		int nextMoveRiskCheckTick;
		int secureClearSinceWorldTick = -1;
		FransActiveMission? secureDiagnosticMission;
		string lastSecureDiagnosticSignature;
		string lastSecureDiagnosticBranch = "None";
		int nextSecureDiagnosticHeartbeatWorldTick;
		bool secureDiagnosticOwnershipActive;
		bool hasLastSafeMoveAnchor;
		CPos lastSafeMoveAnchor;
		bool hasMissionAnchorPoint;
		CPos missionAnchorPoint;
		bool retreatRecoveryActive;
		CPos retreatAnchorPoint;
		int retreatBaselineCombatValue;
		int retreatStartedWorldTick = -1;
		int nextUtilizationLogTick;
		int nextIdleBidTick;
		int cachedKnownAntiAirWorldTick = -1;
		KnownAntiAirZone[] cachedKnownAntiAirZones = Array.Empty<KnownAntiAirZone>();
		FransKnownAntiAirGeometryIdentity cachedKnownAntiAirGeometryIdentity;
		FransKnownAntiAirPreparedExclusion cachedKnownAntiAirPreparedExclusion;
		int lastAirRaidPerformanceRiskRevision = int.MinValue;
		bool airRaidGeometryCacheReuseProofLogged;

		public FransAirCommanderBotModule(Actor self, FransAirCommanderBotModuleInfo info)
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
				?? throw new InvalidOperationException("Air Commander requires FransCombatIntelBotModule.");
			riskModelService = self.Owner.PlayerActor.TraitsImplementing<IFransRiskModelService>().FirstOrDefault()
				?? throw new InvalidOperationException("Air Commander requires FransRiskModelBotModule.");
			commandBidService = self.Owner.PlayerActor.TraitsImplementing<IFransCommandBidService>().FirstOrDefault()
				?? throw new InvalidOperationException("Air Commander requires FransCommandBidBotModule.");
			commanderCoreService = self.Owner.PlayerActor.TraitsImplementing<IFransCommanderCoreService>().FirstOrDefault()
				?? throw new InvalidOperationException("Air Commander requires FransCommanderCoreBotModule.");
			generalService = self.Owner.PlayerActor.TraitsImplementing<IFransGeneralService>().FirstOrDefault()
				?? throw new InvalidOperationException("Air Commander requires FransGeneralBotModule.");
			expansionStateService = self.Owner.PlayerActor.TraitsImplementing<IFransExpansionStateService>().FirstOrDefault();
		}

		protected override void TraitEnabled(Actor self)
		{
			// every Air wing keeps the same cadence but receives a deterministic phase offset.
			// This avoids making ten Air capacities wake on the same tick and reduces artificial CPU/order spikes.
			scanTicks = (int)((self.ActorID + 11u + (uint)(Info.WingIndex * 4)) % (uint)Info.ScanInterval) + 1;
			nextUtilizationLogTick = world.WorldTick + Info.UtilizationLogInterval + Info.WingIndex;
			nextIdleBidTick = world.WorldTick + (Info.WingIndex * Math.Max(1, Info.IdleBidInterval / 10));
			cachedKnownAntiAirWorldTick = -1;
			cachedKnownAntiAirZones = Array.Empty<KnownAntiAirZone>();
			cachedKnownAntiAirGeometryIdentity = null;
			cachedKnownAntiAirPreparedExclusion = null;
			lastAirRaidPerformanceRiskRevision = int.MinValue;
			airRaidGeometryCacheReuseProofLogged = false;
			factRaidDiagnosticNextTick.Clear();
			factRaidDiagnosticLastOutcome.Clear();
			hasLastSafeMoveAnchor = false;
			hasMissionAnchorPoint = false;
			missionAnchorPoint = default;
			retreatRecoveryActive = false;
			retreatAnchorPoint = default;
			retreatBaselineCombatValue = 0;
			retreatStartedWorldTick = -1;
			ClearRecoveryProgressTracking();
			ResetMission();
			FransBotLog.BotDebug(world,
				"{0}: Air Commander COMBINED SECURE + RAID RECOVERY capacity {1} (index {2}) active for {3}. HARD known SAM/AA exclusion remains {6} cells. RAID doctrine is aircraft-specific: all Air wings prefer FACT/MCV when feasible, then HARV; purpose-matched soft/hard targets follow below those construction targets. PROC is deliberately low priority. Progressive immutable-target strike, {4}-WT pre-strike watchdog, one-pass confirmation, {5}-WT post-strike watchdog and 125% building sizing remain active. On normal RAID completion, aircraft with usable ammo native-AttackMove back to their individual RAID origin cells so remaining ammo can be spent en route; empty aircraft go directly to native service. Only strategic DEFEND pressure at/above the broker SECURE-preempt threshold interrupts/blocks Air SECURE; lower DEFEND may coexist with SECURE. For COMBINED SECURE, Air keeps its normal domain logic but may hold launch until the broker's shared arrival time and releases locally when its support domain is clear; Ground remains territorial authority.",
				player, BidderKey, Info.WingIndex, string.Join(",", Info.ManagedAircraftTypes.OrderBy(x => x)), Info.RaidPreStrikeProgressWatchdogTicks, Info.RaidStrikeAmmoProgressWatchdogTicks, Info.KnownAntiAirPathSafetyRadius);
		}

		protected override void TraitDisabled(Actor self)
		{
			pendingStopOrders.Clear();
			pendingStanceOrders.Clear();
			activeAircraft.Clear();
			lastMoveDestination.Clear();
			lastMoveWorldTick.Clear();
			lastMoveKnownAntiAirSignature.Clear();
			lastFightTarget.Clear();
			lastFightWorldTick.Clear();
			lastReturnWorldTick.Clear();
			lastRepairWorldTick.Clear();
			raidRecoverySince.Clear();
			raidRecoveryAnchors.Clear();
			raidMissionOrigins.Clear();
			raidAttackMoveHomeActors.Clear();
			staleActorCacheKeys.Clear();
			ClearRecoveryProgressTracking();
			reconRetreatActor = null;
			reconRetreatOrigin = default;
			hasLastSafeMoveAnchor = false;
			hasMissionAnchorPoint = false;
			missionAnchorPoint = default;
			retreatRecoveryActive = false;
			retreatAnchorPoint = default;
			retreatBaselineCombatValue = 0;
			retreatStartedWorldTick = -1;
			nextUtilizationLogTick = 0;
			lastRaidCapacityProtectedActorIds.Clear();
			lastRaidCapacityProtectedTargetActorId = 0;
			factRaidDiagnosticNextTick.Clear();
			factRaidDiagnosticLastOutcome.Clear();
			commandBidService?.UpdateTransientActorReservations(FransCommanderKind.Air, BidderKey, Array.Empty<uint>());
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
			PruneDeadActorKeys(lastMoveKnownAntiAirSignature);
			PruneDeadActorKeys(lastFightTarget);
			PruneDeadActorKeys(lastFightWorldTick);
			PruneDeadActorKeys(lastReturnWorldTick);
			PruneDeadActorKeys(lastRepairWorldTick);
			PruneDeadActorKeys(raidRecoverySince);
			PruneDeadActorKeys(raidRecoveryAnchors);
			PruneDeadActorKeys(raidMissionOrigins);
			PruneDeadActorKeys(recoveryLastObservedHp);
			PruneDeadActorKeys(recoveryLastObservedAmmoCount);
			PruneDeadActorKeys(recoveryLastObservedAnchorDistance);
			PruneDeadActorKeys(recoveryLastObservedServiceDistance);
			PruneDeadActorKeys(recoveryLastProgressWorldTick);
			PruneDeadActorKeys(recoveryLastWatchdogReissueWorldTick);
			raidAttackMoveHomeActors.RemoveWhere(a => a == null || a.IsDead);
			staleActorCacheKeys.Clear();
		}

		void IBotTick.BotTick(IBot bot)
		{
			FlushPendingSynchronizedActions(bot);
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransAirCommander.BotTick");
			if (player.WinState != WinState.Undefined)
				return;

			if (--scanTicks > 0)
				return;
			scanTicks = Info.ScanInterval;

			combatIntelService.EnsureCurrentSnapshot();
			PruneDeadActorOrderState();
			var allAircraft = combatIntelService.OwnedActors
				.Where(IsManagedAircraft)
				.OrderBy(a => a.ActorID)
				.ToArray();

			// Recovery ownership outlives the strategic mission. Publish those local reservations before
			// this wing computes its free pool so another wing can never steal an aircraft on the way home.
			RefreshTransientReservations();
			if (Info.WingIndex == 0 && world.WorldTick >= nextUtilizationLogTick)
			{
				WriteAirUtilization(allAircraft);
				nextUtilizationLogTick = world.WorldTick + Info.UtilizationLogInterval;
			}

			var aircraft = allAircraft
				.Where(a => commanderCoreService.IsActorAvailableForBidder(FransCommanderKind.Air, BidderKey, a))
				.ToArray();
			activeAircraft.RemoveWhere(a => !aircraft.Contains(a));
			MaintainReconRetreat(bot, aircraft);
			MaintainRaidRecovery(bot, aircraft);
			RefreshTransientReservations();

			if (!retreatRecoveryActive && commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.Air, BidderKey,
				out _, out var preemptableMission) && preemptableMission.MissionType == FransMissionType.Secure &&
				commandBidService.ShouldPreemptSecureForDefend(FransCommanderKind.Air, BidderKey, preemptableMission.LastVisibleTargetCell))
			{
				foreach (var id in preemptableMission.CommittedActorIds ?? Array.Empty<uint>())
				{
					var aircraftToRelease = aircraft.FirstOrDefault(a => a.ActorID == id && a.IsInWorld && !a.IsDead);
					if (aircraftToRelease == null)
						continue;
					QueueStopOrder(bot, aircraftToRelease);
					if (!HasAmmo(aircraftToRelease))
						QueueReturnToBase(bot, aircraftToRelease, true);
				}
				commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, "Air SECURE preempted by active DEFEND pressure");
				LogAirSecureReleased(preemptableMission, preemptableMission.LastVisibleTargetCell,
					"strategic DEFEND pressure invoked the existing SECURE preemption transition");
				FransBotLog.BotDebug(world,
					"{0}: Air Commander {1} releases SECURE {2} because strategic DEFEND pressure reached the SECURE-preempt threshold; aircraft are freed for defense/rearm.",
					player, BidderKey, preemptableMission.TargetActorId);
				ResetMission();
			}

			foreach (var a in aircraft)
				if (a != reconRetreatActor && !raidRecoverySince.ContainsKey(a) && !HasAmmo(a) &&
					(!retreatRecoveryActive || !NeedsNativeRepair(a)) &&
					(Info.WingIndex == 0 || activeAircraft.Contains(a)))
					QueueReturnToBase(bot, a);

			var ready = aircraft.Where(a => a != reconRetreatActor && !raidRecoverySince.ContainsKey(a) && HasAmmo(a)).ToArray();
			if (ready.Length == 0 && retreatRecoveryActive)
			{
				ExecuteRetreatRecovery(bot, aircraft);
				return;
			}

			if (ready.Length == 0 && commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.Air, BidderKey,
				out _, out var serviceMission) && serviceMission.MissionType == FransMissionType.Secure)
			{
				ExecuteSecureMission(bot, aircraft, serviceMission);
				return;
			}

			if (ready.Length == 0)
			{
				if (commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.Air, BidderKey,
					out _, out var emptyMission))
				{
					if (emptyMission.MissionType == FransMissionType.Recon)
					{
						commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, "RECON aircraft died or is unavailable during persistent probing");
						FransBotLog.BotDebug(world,
							"{0}: Air RECON MineCluster {1} lost its aircraft during persistent probing; General keeps the target open for rebid.",
							player, emptyMission.TargetActorId);
					}
					else if (emptyMission.MissionType == FransMissionType.Raid)
					{
						var completedSortie = activeMissionType == FransMissionType.Raid && raidStrikeIssued;
						commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, completedSortie
							? "RAID full sortie ammo exhausted"
							: "RAID force lost immediate readiness before STRIKE NOW; recovery owns surviving aircraft and General may rebid");
						if (activeMissionType == FransMissionType.Raid)
							StartRaidRecovery(bot, completedSortie
								? "full-sortie ammo exhausted after STRIKE NOW"
								: "RAID force lost immediate readiness before STRIKE NOW");
						if (completedSortie)
							FransBotLog.BotDebug(world,
								"{0}: Air RAID full sortie on target {1} is complete: no committed aircraft has usable ammo; recovery owns the surviving group.",
								player, emptyMission.TargetActorId);
					}
				}

				retreatRecoveryActive = false;
				retreatStartedWorldTick = -1;
				retreatAnchorPoint = default;
				retreatBaselineCombatValue = 0;
				ClearRecoveryProgressTracking();
				ResetMission();
				return;
			}

			if (!retreatRecoveryActive && activeOrder == FransCommanderOrder.Fight &&
				ShouldRetreatFromFight(aircraft, out var collapsedFightValue))
			{
				BeginRetreat(bot, aircraft, collapsedFightValue);
				return;
			}

			if (retreatRecoveryActive)
			{
				// recovery is committed survival work; DEFEND may use IDLE or SECURE capacity only.
				ExecuteRetreatRecovery(bot, aircraft);
				return;
			}

			if (commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.Air, BidderKey,
				out var target, out var mission))
			{
				ExecuteMission(bot, ready, target, mission);
				return;
			}

			// Idle bidding is the expensive part of Air Commander because every candidate mission may
			// require known-AA geometry plus RiskModel route pricing. Active mission execution remains
			// on the normal ScanInterval, but a free wing only recomputes the full auction periodically.
			if (activeMissionType == FransMissionType.Raid && activeTargetActorId != 0)
				StartRaidAttackMoveReturn(bot, "RAID mission disappeared / target completed");
			if (activeMissionType == FransMissionType.Secure && secureDiagnosticMission.HasValue && secureDiagnosticOwnershipActive)
				LogAirSecureReleased(secureDiagnosticMission.Value, activeObjective,
					"Broker no longer exposes the accepted SECURE assignment to this bidder");
			ResetMission();
			var urgentDefendBid = commandBidService.IsStrategicDefendPressureActive();
			if (!urgentDefendBid && world.WorldTick < nextIdleBidTick)
				return;
			if (!urgentDefendBid)
				nextIdleBidTick = world.WorldTick + Info.IdleBidInterval;

			SubmitBids(ready);
			if (commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.Air, BidderKey,
				out target, out mission))
			{
				ExecuteMission(bot, ready, target, mission);
				return;
			}

			if (activeMissionType == FransMissionType.Raid && activeTargetActorId != 0)
				StartRaidAttackMoveReturn(bot, "RAID mission disappeared / target completed");
			ResetMission();
		}

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			if (self == null || !IsManagedAircraft(self) || e.Attacker == null ||
				(e.Attacker.Info.HasTraitInfo<HuskInfo>() || e.Attacker.Info.Name.EndsWith(".husk", StringComparison.OrdinalIgnoreCase)))
				return;

			// Ten Air capacities receive the same engine attack callback. Exactly one owning capacity may react.
			// The broker mission identifies the owning wing before local mission state has necessarily caught up;
			// otherwise only wing 0 may service a truly free aircraft. Recovery actors never counterattack.
			var missionOwnedByThisWing = commandBidService.TryGetActorMission(FransCommanderKind.Air, self.ActorID, out _, out var missionWing) &&
				missionWing == BidderKey;
			var locallyOwned = missionOwnedByThisWing || activeAircraft.Contains(self) || self == reconRetreatActor || raidRecoverySince.ContainsKey(self);
			if (!locallyOwned && (Info.WingIndex != 0 || commandBidService.IsActorUnavailableForBidder(FransCommanderKind.Air, BidderKey, self.ActorID)))
				return;
			if (self == reconRetreatActor || raidRecoverySince.ContainsKey(self) || (retreatRecoveryActive && activeAircraft.Contains(self)))
				return;

			if (activeAircraft.Contains(self) && activeMissionType == FransMissionType.Recon &&
				(activeOrder == FransCommanderOrder.Move || activeOrder == FransCommanderOrder.Search) && IsEnemyActor(e.Attacker))
			{
				BeginReconRetreat(bot, self, "recon aircraft received hostile damage");
				return;
			}

			if (!HasAmmo(self) || !IsVisibleEnemy(e.Attacker))
				return;

			if (activeAircraft.Contains(self) && activeMissionType == FransMissionType.Raid)
			{
				var expected = commandBidService.TryGetActiveMissionForBidder(FransCommanderKind.Air, BidderKey, out _, out var raidMission) &&
					commanderCoreService.IsExpectedRaidContact(raidMission, e.Attacker);
				if (!expected)
				{
					var knownAaZones = GetKnownAntiAirZones();
					var safeCounterattack = activeAircraft.Any(a => a != null && a.IsInWorld && !a.IsDead && HasAmmo(a) &&
						CanAttackActor(a, e.Attacker) && IsAirAttackCorridorKnownAaSafe(a, e.Attacker, knownAaZones));
					if (!safeCounterattack)
					{
						CloseRaid(bot, $"unexpected NEW defense {e.Attacker.Info.Name} {e.Attacker.ActorID} cannot be counterattacked without violating the hard known-AA exclusion", true);
						return;
					}

					BeginFight();
					if (HasAmmo(self) && CanAttackActor(self, e.Attacker) && IsAirAttackCorridorKnownAaSafe(self, e.Attacker, knownAaZones))
						QueueAttack(bot, self, e.Attacker, true);
					FransBotLog.BotDebug(world,
						"{0}: Air RAID LOCAL FIGHT: unexpected visible {1} {2} attacked {3}; the committed wing keeps the same RAID, neutralizes the local attacker through normal FIGHT micro, then resumes the immutable mission target. Hard known-AA exclusion still overrides this behavior.",
						player, e.Attacker.Info.Name, e.Attacker.ActorID, self);
				}
				// Expected raw SiteIntel resistance was already priced into the accepted MISSION. Unexpected
				// attackable resistance becomes a short local FIGHT without releasing mission ownership.
				return;
			}

			if (activeAircraft.Contains(self) && activeOrder == FransCommanderOrder.Move)
			{
				BeginFight();
				FransBotLog.BotDebug(world,
					"{0}: Air Commander MOVE -> FIGHT because {1} was attacked by visible {2} {3}; RiskModel is now ignored. Combat baseline {4}, fallback {5}.",
					player, self, e.Attacker.Info.Name, e.Attacker.ActorID, retreatBaselineCombatValue, retreatAnchorPoint);
			}

			if (CanAttackActor(self, e.Attacker) && IsAirAttackCorridorKnownAaSafe(self, e.Attacker))
				QueueAttack(bot, self, e.Attacker, true);
		}

		bool IsAirRaidEligibleTarget(FransMission mission)
		{
			return mission.IsBuilding || Info.RaidEligibleMobileTargetTypes.Contains(mission.TargetActorType);
		}

		bool IsAirRaidEligibleTarget(FransActiveMission mission)
		{
			return mission.TargetIsBuilding || Info.RaidEligibleMobileTargetTypes.Contains(mission.TargetActorType);
		}

		readonly record struct KnownAntiAirZone(uint ActorId, string ActorType, CPos Center);

		KnownAntiAirZone[] GetKnownAntiAirZones()
		{
			if (cachedKnownAntiAirWorldTick == world.WorldTick)
				return cachedKnownAntiAirZones;

			combatIntelService.EnsureCurrentSnapshot();
			cachedKnownAntiAirZones = combatIntelService.EnemyCombatContacts
				.Where(c => Info.KnownAntiAirStructureTypes.Contains(c.ActorType))
				.OrderBy(c => c.ActorId)
				.Select(c => new KnownAntiAirZone(c.ActorId, c.ActorType, c.LastSeenCell))
				.ToArray();
			cachedKnownAntiAirWorldTick = world.WorldTick;
			cachedKnownAntiAirGeometryIdentity = BuildKnownAntiAirGeometryIdentity(cachedKnownAntiAirZones);
			GetPreparedKnownAntiAirExclusion(cachedKnownAntiAirZones, out _);
			return cachedKnownAntiAirZones;
		}

		FransKnownAntiAirGeometryIdentity BuildKnownAntiAirGeometryIdentity(IReadOnlyList<KnownAntiAirZone> zones)
		{
			return new FransKnownAntiAirGeometryIdentity(Info.KnownAntiAirPathSafetyRadius,
				zones.Select(z => new FransKnownAntiAirGeometryZone(z.ActorId, z.Center)).ToArray());
		}

		FransKnownAntiAirGeometryIdentity GetKnownAntiAirGeometryIdentity(IReadOnlyList<KnownAntiAirZone> zones)
		{
			if (ReferenceEquals(zones, cachedKnownAntiAirZones) && cachedKnownAntiAirGeometryIdentity != null)
				return cachedKnownAntiAirGeometryIdentity;
			return BuildKnownAntiAirGeometryIdentity(zones);
		}

		FransKnownAntiAirPreparedExclusion GetPreparedKnownAntiAirExclusion(
			IReadOnlyList<KnownAntiAirZone> zones, out bool reused)
		{
			var identity = GetKnownAntiAirGeometryIdentity(zones);
			if (cachedKnownAntiAirPreparedExclusion != null &&
				cachedKnownAntiAirPreparedExclusion.GeometryIdentity.Equals(identity))
			{
				reused = true;
				return cachedKnownAntiAirPreparedExclusion;
			}

			cachedKnownAntiAirPreparedExclusion = new FransKnownAntiAirPreparedExclusion(identity);
			reused = false;
			return cachedKnownAntiAirPreparedExclusion;
		}

		bool IsCellOutsideKnownAntiAir(CPos cell, IReadOnlyList<KnownAntiAirZone> zones)
		{
			var prepared = GetPreparedKnownAntiAirExclusion(zones, out _);
			var work = default(FransKnownAntiAirPreparedWork);
			return prepared.IsCellOutside(cell, ref work);
		}

		static int InterpolateCellCoordinate(int origin, int delta, int step, int steps)
			=> FransKnownAntiAirPreparedExclusion.InterpolateCellCoordinate(origin, delta, step, steps);

		bool SegmentStaysOutsideKnownAntiAir(CPos from, CPos to, IReadOnlyList<KnownAntiAirZone> zones)
		{
			var prepared = GetPreparedKnownAntiAirExclusion(zones, out _);
			var work = default(FransKnownAntiAirPreparedWork);
			return prepared.SegmentStaysOutside(from, to, ref work);
		}

		bool TryBuildKnownAntiAirSafePath(CPos from, CPos to, IReadOnlyList<KnownAntiAirZone> zones, out CPos[] waypoints)
		{
			return TryBuildKnownAntiAirSafePath(from, to, zones, out waypoints, null);
		}

		bool TryBuildKnownAntiAirSafePath(CPos from, CPos to, IReadOnlyList<KnownAntiAirZone> zones,
			out CPos[] waypoints, KnownAntiAirPathPerformanceDiagnostic diagnostic)
		{
			var prepared = GetPreparedKnownAntiAirExclusion(zones, out var preparedReused);
			var identity = prepared.GeometryIdentity;
			if (commanderCoreService.TryGetSharedAirKnownAntiAirGeometryRoute(from, to, identity, out var cached))
			{
				waypoints = cached.Waypoints ?? Array.Empty<CPos>();
				if (diagnostic != null)
				{
					diagnostic.GeometryCacheHit = true;
					diagnostic.ZoneCount = zones.Count;
					diagnostic.PreparedExcludedCellCount = prepared.ExcludedCellCount;
					diagnostic.PreparedGeometryReused = preparedReused;
					diagnostic.Outcome = cached.Outcome.ToString();
				}

				return cached.Feasible;
			}

			if (diagnostic != null)
				diagnostic.PhysicalGeometrySolve = true;
			var feasible = TryBuildKnownAntiAirSafePathPhysical(from, to, zones, prepared, preparedReused,
				out waypoints, out var outcome, diagnostic);
			commanderCoreService.StoreSharedAirKnownAntiAirGeometryRoute(from, to, identity,
				new FransAirKnownAntiAirGeometryRoute(feasible, outcome, waypoints));
			return feasible;
		}

		static void ApplyKnownAntiAirPreparedWork(KnownAntiAirPathPerformanceDiagnostic diagnostic,
			FransKnownAntiAirPreparedExclusion prepared, bool preparedReused, FransKnownAntiAirPreparedWork work)
		{
			if (diagnostic == null)
				return;
			diagnostic.PreparedExcludedCellCount = prepared.ExcludedCellCount;
			diagnostic.PreparedCellChecks = work.PreparedCellChecks;
			diagnostic.PreparedGeometryReused = preparedReused;
			diagnostic.EscapeFallbackSegmentChecks = work.EscapeFallbackSegmentChecks;
			diagnostic.SegmentChecks = work.SegmentChecks;
			diagnostic.SegmentZoneChecks = work.SegmentZoneChecks;
			diagnostic.SegmentCellSamples = work.SegmentCellSamples;
		}

		void CompleteKnownAntiAirPathDiagnostic(KnownAntiAirPathPerformanceDiagnostic diagnostic,
			FransAirKnownAntiAirGeometryOutcome outcome, long startedTimestamp, FransKnownAntiAirPreparedExclusion prepared,
			bool preparedReused, FransKnownAntiAirPreparedWork work)
		{
			if (diagnostic == null)
				return;
			ApplyKnownAntiAirPreparedWork(diagnostic, prepared, preparedReused, work);
			diagnostic.Outcome = outcome.ToString();
			diagnostic.PathElapsedTimestampTicks += Stopwatch.GetTimestamp() - startedTimestamp;
		}

		bool TryBuildKnownAntiAirSafePathPhysical(CPos from, CPos to, IReadOnlyList<KnownAntiAirZone> zones,
			FransKnownAntiAirPreparedExclusion prepared, bool preparedReused, out CPos[] waypoints,
			out FransAirKnownAntiAirGeometryOutcome outcome, KnownAntiAirPathPerformanceDiagnostic diagnostic)
		{
			var pathStarted = diagnostic == null ? 0 : Stopwatch.GetTimestamp();
			if (diagnostic != null)
				diagnostic.ZoneCount = zones.Count;
			var preparedWork = new FransKnownAntiAirPreparedWork { Enabled = diagnostic != null };
			waypoints = Array.Empty<CPos>();
			if (!world.Map.Contains(from) || !world.Map.Contains(to))
			{
				outcome = FransAirKnownAntiAirGeometryOutcome.OutsideMap;
				CompleteKnownAntiAirPathDiagnostic(diagnostic, outcome, pathStarted,
					prepared, preparedReused, preparedWork);
				return false;
			}
			if (!prepared.IsCellOutside(to, ref preparedWork))
			{
				outcome = FransAirKnownAntiAirGeometryOutcome.TargetInsideKnownAa;
				CompleteKnownAntiAirPathDiagnostic(diagnostic, outcome, pathStarted,
					prepared, preparedReused, preparedWork);
				return false;
			}

			if (prepared.SegmentStaysOutside(from, to, ref preparedWork))
			{
				waypoints = new[] { to };
				if (diagnostic != null)
					diagnostic.NodeCount = 2;
				outcome = FransAirKnownAntiAirGeometryOutcome.Direct;
				CompleteKnownAntiAirPathDiagnostic(diagnostic, outcome, pathStarted,
					prepared, preparedReused, preparedWork);
				return true;
			}

			// Aircraft ignore terrain, so the route graph only needs geometric visibility around
			// the hard known-AA circles. Eight ring nodes per known SAM/AA are enough to select
			// a deterministic left/right/top/bottom detour without running a full map A* per wing.
			var clearance = Info.KnownAntiAirPathSafetyRadius + 2;
			var nodes = new List<CPos> { from, to };
			var seen = new HashSet<CPos> { from, to };
			var offsets = new[]
			{
				(clearance, 0), (clearance, clearance), (0, clearance), (-clearance, clearance),
				(-clearance, 0), (-clearance, -clearance), (0, -clearance), (clearance, -clearance)
			};

			var nodeBuildStarted = diagnostic == null ? 0 : Stopwatch.GetTimestamp();
			foreach (var zone in zones)
				foreach (var (ox, oy) in offsets)
				{
					if (diagnostic != null)
						diagnostic.CandidatePointChecks++;
					var candidate = new CPos(zone.Center.X + ox, zone.Center.Y + oy);
					if (world.Map.Contains(candidate) && prepared.IsCellOutside(candidate, ref preparedWork) && seen.Add(candidate))
						nodes.Add(candidate);
				}
			if (diagnostic != null)
			{
				diagnostic.NodeCount = nodes.Count;
				diagnostic.NodeBuildElapsedTimestampTicks += Stopwatch.GetTimestamp() - nodeBuildStarted;
			}

			var count = nodes.Count;
			var distance = Enumerable.Repeat(long.MaxValue, count).ToArray();
			var previous = Enumerable.Repeat(-1, count).ToArray();
			var visited = new bool[count];
			distance[0] = 0;

			var graphStarted = diagnostic == null ? 0 : Stopwatch.GetTimestamp();
			for (var pass = 0; pass < count; pass++)
			{
				if (diagnostic != null)
					diagnostic.GraphPasses++;
				var u = -1;
				var best = long.MaxValue;
				for (var i = 0; i < count; i++)
				{
					if (diagnostic != null)
						diagnostic.GraphSelectionChecks++;
					if (!visited[i] && distance[i] < best)
					{
						best = distance[i];
						u = i;
					}
				}

				if (u < 0)
					break;
				if (u == 1)
					break;
				visited[u] = true;

				for (var v = 0; v < count; v++)
				{
					if (diagnostic != null)
						diagnostic.GraphNeighborChecks++;
					if (v == u || visited[v] || !prepared.SegmentStaysOutside(nodes[u], nodes[v], ref preparedWork))
						continue;

					var edgeCost = Math.Max(Math.Abs(nodes[u].X - nodes[v].X), Math.Abs(nodes[u].Y - nodes[v].Y));
					var candidateDistance = distance[u] + Math.Max(1, edgeCost);
					if (candidateDistance < distance[v])
					{
						distance[v] = candidateDistance;
						previous[v] = u;
					}
				}
			}
			if (diagnostic != null)
				diagnostic.GraphElapsedTimestampTicks += Stopwatch.GetTimestamp() - graphStarted;

			if (distance[1] == long.MaxValue)
			{
				outcome = FransAirKnownAntiAirGeometryOutcome.NoGraphRoute;
				CompleteKnownAntiAirPathDiagnostic(diagnostic, outcome, pathStarted,
					prepared, preparedReused, preparedWork);
				return false;
			}

			var reverse = new List<CPos>();
			for (var cursor = 1; cursor > 0; cursor = previous[cursor])
			{
				if (cursor < 0)
				{
					outcome = FransAirKnownAntiAirGeometryOutcome.BrokenPredecessor;
					CompleteKnownAntiAirPathDiagnostic(diagnostic, outcome, pathStarted,
						prepared, preparedReused, preparedWork);
					return false;
				}
				reverse.Add(nodes[cursor]);
			}
			reverse.Reverse();
			waypoints = reverse.ToArray();
			outcome = FransAirKnownAntiAirGeometryOutcome.GraphRoute;
			CompleteKnownAntiAirPathDiagnostic(diagnostic, outcome, pathStarted,
				prepared, preparedReused, preparedWork);
			return waypoints.Length > 0;
		}

		bool TryBuildKnownAntiAirSafePath(Actor aircraft, CPos destination, out CPos[] waypoints)
		{
			waypoints = Array.Empty<CPos>();
			if (aircraft == null || !aircraft.IsInWorld || aircraft.IsDead)
				return false;
			return TryBuildKnownAntiAirSafePath(aircraft.Location, destination, GetKnownAntiAirZones(), out waypoints);
		}

		void AppendLineCells(List<CPos> cells, CPos from, CPos to)
		{
			var dx = to.X - from.X;
			var dy = to.Y - from.Y;
			var steps = Math.Max(Math.Abs(dx), Math.Abs(dy));
			if (steps == 0)
			{
				if (world.Map.Contains(to) && (cells.Count == 0 || cells[^1] != to))
					cells.Add(to);
				return;
			}

			for (var i = 1; i <= steps; i++)
			{
				var cell = new CPos(
					InterpolateCellCoordinate(from.X, dx, i, steps),
					InterpolateCellCoordinate(from.Y, dy, i, steps));
				if (world.Map.Contains(cell) && (cells.Count == 0 || cells[^1] != cell))
					cells.Add(cell);
			}
		}

		FransRouteRiskAssessment EvaluateAirPathRisk(Actor aircraft, IReadOnlyList<CPos> path,
			KnownAntiAirPathPerformanceDiagnostic diagnostic = null)
		{
			var started = diagnostic == null ? 0 : Stopwatch.GetTimestamp();
			var cells = new List<CPos>();
			var cursor = aircraft.Location;
			foreach (var waypoint in path)
			{
				AppendLineCells(cells, cursor, waypoint);
				cursor = waypoint;
			}
			var result = riskModelService.EvaluateRoute(aircraft, cells, FransRiskRole.Aircraft, FransRiskTolerance.Balanced);
			if (diagnostic != null)
			{
				diagnostic.RiskCellCount += cells.Count;
				diagnostic.RiskElapsedTimestampTicks += Stopwatch.GetTimestamp() - started;
			}
			return result;
		}

		int EstimateAirPathEtaTicks(Actor aircraft, IReadOnlyList<CPos> path,
			KnownAntiAirPathPerformanceDiagnostic diagnostic = null)
		{
			var started = diagnostic == null ? 0 : Stopwatch.GetTimestamp();
			var movement = aircraft?.TraitOrDefault<Aircraft>();
			if (movement == null || movement.IsTraitDisabled || movement.IsTraitPaused || path == null || path.Count == 0)
			{
				if (diagnostic != null)
					diagnostic.EtaElapsedTimestampTicks += Stopwatch.GetTimestamp() - started;
				return int.MaxValue;
			}

			var from = aircraft.CenterPosition;
			long total = 0;
			foreach (var waypoint in path)
			{
				var to = world.Map.CenterOfCell(waypoint);
				var eta = movement.EstimatedMoveDuration(aircraft, from, to);
				if (eta <= 0)
					eta = 1;
				total += eta;
				if (total >= int.MaxValue)
				{
					if (diagnostic != null)
						diagnostic.EtaElapsedTimestampTicks += Stopwatch.GetTimestamp() - started;
					return int.MaxValue;
				}
				from = to;
			}
			if (diagnostic != null)
				diagnostic.EtaElapsedTimestampTicks += Stopwatch.GetTimestamp() - started;
			return (int)total;
		}

		static int GetAirPathTravelCells(CPos start, IReadOnlyList<CPos> path)
		{
			var cursor = start;
			long total = 0;
			foreach (var waypoint in path)
			{
				total += Math.Abs(waypoint.X - cursor.X) + Math.Abs(waypoint.Y - cursor.Y);
				cursor = waypoint;
			}
			return (int)Math.Min(int.MaxValue, total);
		}

		bool IsAirAttackCorridorKnownAaSafe(Actor aircraft, Actor target)
		{
			return IsAirAttackCorridorKnownAaSafe(aircraft, target, GetKnownAntiAirZones());
		}

		bool IsAirAttackCorridorKnownAaSafe(Actor aircraft, Actor target, IReadOnlyList<KnownAntiAirZone> zones)
		{
			return aircraft != null && target != null &&
				IsCellOutsideKnownAntiAir(target.Location, zones) &&
				SegmentStaysOutsideKnownAntiAir(aircraft.Location, target.Location, zones);
		}

		static int KnownAntiAirSignature(IReadOnlyList<KnownAntiAirZone> zones)
		{
			unchecked
			{
				var hash = 17;
				foreach (var zone in zones)
				{
					hash = hash * 31 + (int)zone.ActorId;
					hash = hash * 31 + zone.Center.X;
					hash = hash * 31 + zone.Center.Y;
				}
				return hash;
			}
		}

		bool TryGetSharedCombatBidRouteMetrics(Actor aircraft, CPos targetCell, IReadOnlyList<KnownAntiAirZone> knownAaZones,
			out FransAirBidRouteMetrics metrics)
		{
			return TryGetSharedCombatBidRouteMetrics(aircraft, targetCell, knownAaZones, null, out metrics);
		}

		bool TryGetSharedCombatBidRouteMetrics(Actor aircraft, CPos targetCell, IReadOnlyList<KnownAntiAirZone> knownAaZones,
			AirRaidCandidatePerformanceDiagnostic diagnostic, out FransAirBidRouteMetrics metrics)
		{
			metrics = default;
			if (aircraft == null || !aircraft.IsInWorld || aircraft.IsDead)
				return false;

			var startCell = aircraft.Location;
			var geometryIdentity = GetKnownAntiAirGeometryIdentity(knownAaZones);
			var riskRevision = riskModelService?.RiskRevision ?? -1;
			if (commanderCoreService.TryGetSharedAirBidRouteMetrics(aircraft.ActorID, startCell, targetCell,
				geometryIdentity, riskRevision, out metrics))
			{
				diagnostic?.Routes.Add(new AirRaidRoutePerformanceDiagnostic(
					aircraft.ActorID, startCell, targetCell, true, metrics.Feasible, metrics.IsCritical, null));
				return metrics.Feasible;
			}

			var pathDiagnostic = diagnostic == null ? null : new KnownAntiAirPathPerformanceDiagnostic();
			if (!TryBuildKnownAntiAirSafePath(startCell, targetCell, knownAaZones, out var safePath, pathDiagnostic))
			{
				metrics = new FransAirBidRouteMetrics(false, true, int.MaxValue, int.MaxValue, int.MaxValue);
				commanderCoreService.StoreSharedAirBidRouteMetrics(aircraft.ActorID, startCell, targetCell,
					geometryIdentity, riskRevision, metrics);
				diagnostic?.Routes.Add(new AirRaidRoutePerformanceDiagnostic(
					aircraft.ActorID, startCell, targetCell, false, false, true, pathDiagnostic));
				return false;
			}

			var route = EvaluateAirPathRisk(aircraft, safePath, pathDiagnostic);
			var eta = EstimateAirPathEtaTicks(aircraft, safePath, pathDiagnostic);
			var travel = GetAirPathTravelCells(startCell, safePath);
			metrics = new FransAirBidRouteMetrics(true, route.IsCritical, route.PeakScore, eta, travel);
			commanderCoreService.StoreSharedAirBidRouteMetrics(aircraft.ActorID, startCell, targetCell,
				geometryIdentity, riskRevision, metrics);
			diagnostic?.Routes.Add(new AirRaidRoutePerformanceDiagnostic(
				aircraft.ActorID, startCell, targetCell, false, true, route.IsCritical, pathDiagnostic));
			return true;
		}

		// Cameo port: upstream distinguished raid aircraft by RA ids (yak/hind vs mig/heli/mh60).
		// Trait split: VTOL gunships fly soft raids, fixed-wing strikers fly hard raids.
		static bool IsSoftRaidAircraft(Actor aircraft) =>
			aircraft?.Info is { } ai && FransActorClass.IsVtol(ai) && FransActorClass.IsArmed(ai);

		static bool IsHardRaidAircraft(Actor aircraft) =>
			aircraft?.Info is { } ai && FransActorClass.IsFixedWing(ai) && FransActorClass.IsArmed(ai);

		static bool IsRaidTankTargetType(ActorInfo info) =>
			info != null && FransActorClass.IsTank(info);

		static int GetRaidTargetPriorityRank(Actor aircraft, Ruleset rules, string actorType, bool isBuilding)
		{
			var type = actorType?.ToLowerInvariant() ?? string.Empty;
			ActorInfo info = null;
			if (type.Length > 0)
				rules.Actors.TryGetValue(type, out info);

			// Construction capability is the highest-value precision RAID objective.
			// A visible/feasible FACT or MCV therefore outranks economy vehicles for every
			// Air family. Refineries remain deliberately poor precision targets.
			if (info != null && FransActorClass.IsRefinery(info))
				return 50;
			// "fact" is the SECURE-conyard mission token, not an actor name.
			if (type == "fact" || (info != null && (FransActorClass.IsConyard(info) || FransActorClass.IsMcv(info))))
				return 0;

			if (IsSoftRaidAircraft(aircraft))
			{
				if (info != null && FransActorClass.IsHarvester(info))
					return 1;
				// Gunships then spend their cannon ammunition on exposed soft/high-value units.
				if (info != null && (FransActorClass.IsAAInfantry(info, rules) || FransActorClass.IsArtillery(info, rules)))
					return 2;
				if (IsRaidTankTargetType(info))
					return 4;
				return isBuilding ? 10 : 6;
			}

			if (IsHardRaidAircraft(aircraft))
			{
				if (info != null && FransActorClass.IsHarvester(info))
					return 1;
				if (info != null && FransActorClass.IsArtillery(info, rules))
					return 2;
				if (IsRaidTankTargetType(info))
					return 3;
				if (info != null && FransActorClass.IsAAInfantry(info, rules))
					return 5;
				return isBuilding ? 10 : 8;
			}

			// Other armed aircraft keep the same construction-first fallback doctrine.
			if (info != null && FransActorClass.IsHarvester(info))
				return 1;
			if (info != null && (FransActorClass.IsArtillery(info, rules) || FransActorClass.IsAAInfantry(info, rules)))
				return 2;
			if (IsRaidTankTargetType(info))
				return 4;
			return isBuilding ? 10 : 8;
		}

		static int GetRaidGroupTargetPriorityRank(IEnumerable<Actor> aircraft, Ruleset rules, string actorType, bool isBuilding)
		{
			var ranks = aircraft.Select(a => GetRaidTargetPriorityRank(a, rules, actorType, isBuilding)).ToArray();
			// The least-suitable committed member defines the group's doctrine band. This keeps
			// mixed wings from stealing a target that a purpose-matched wing can service cleanly.
			return ranks.Length == 0 ? 20 : ranks.Max();
		}

		static int ApplyRaidTargetPriorityToPrice(int basePrice, int priorityRank)
		{
			if (basePrice == int.MaxValue)
				return int.MaxValue;
			const int PriorityBandCost = 1000000;
			var ranked = (long)Math.Max(0, priorityRank) * PriorityBandCost + Math.Max(1, basePrice);
			return (int)Math.Min(int.MaxValue - 1L, ranked);
		}

		void LogFactRaidDiagnostic(FransMission mission, string outcome)
		{
			if (!string.Equals(mission.TargetActorType, "fact", StringComparison.OrdinalIgnoreCase))
				return;

			var targetId = mission.TargetActorId;
			var sameOutcome = factRaidDiagnosticLastOutcome.TryGetValue(targetId, out var previous) && previous == outcome;
			if (sameOutcome && factRaidDiagnosticNextTick.TryGetValue(targetId, out var nextTick) && world.WorldTick < nextTick)
				return;

			factRaidDiagnosticLastOutcome[targetId] = outcome;
			factRaidDiagnosticNextTick[targetId] = world.WorldTick + 500;
			FransBotLog.BotDebug(world,
				"{0}: Air capacity {1} FACT RAID diagnostic target {2} at {3}: {4}. Target doctrine remains FACT/MCV first; this diagnostic is read-only and does not alter bidding.",
				player, BidderKey, targetId, mission.LastVisibleTargetCell, outcome);
		}

		int BuildRaidCandidateSignature(IReadOnlyCollection<Actor> aircraft)
		{
			unchecked
			{
				var hash = 17;
				foreach (var a in aircraft.OrderBy(a => a.ActorID))
				{
					hash = hash * 31 + (int)a.ActorID;
					hash = hash * 31 + a.Location.X;
					hash = hash * 31 + a.Location.Y;
					hash = hash * 31 + (commanderCoreService.IsActorAvailableForMissionBid(FransCommanderKind.Air, BidderKey, a) ? 1 : 0);
					hash = hash * 31 + (a == reconRetreatActor ? 1 : 0);
					hash = hash * 31 + (raidRecoverySince.ContainsKey(a) ? 1 : 0);
					hash = hash * 31 + (a.TraitOrDefault<Cargo>() == null ? 1 : 0);
					hash = hash * 31 + (HasFullRaidAmmo(a) ? 1 : 0);
				}
				return hash;
			}
		}

		static FransCommanderBidReport MaterializeSharedRaidBid(FransAirRaidBidTemplate template, string bidderKey)
		{
			return new FransCommanderBidReport(
				FransCommanderKind.Air, bidderKey, template.SubjectActorId, template.CommittedActorIds ?? Array.Empty<uint>(),
				template.TotalCost, template.RouteRisk, template.TravelCost, template.ForceCost, template.EstimatedEtaTicks,
				template.OfferedContribution, template.RequiredContribution, false);
		}

		bool TryBuildRaidBid(FransMission mission, IReadOnlyCollection<Actor> aircraft, out FransCommanderBidReport report)
		{
			return TryBuildRaidBid(mission, aircraft, GetKnownAntiAirZones(), null, out report);
		}

		bool TryBuildRaidBid(FransMission mission, IReadOnlyCollection<Actor> aircraft, IReadOnlyList<KnownAntiAirZone> knownAaZones, out FransCommanderBidReport report)
		{
			return TryBuildRaidBid(mission, aircraft, knownAaZones, null, out report);
		}

		bool TryBuildRaidBid(FransMission mission, IReadOnlyCollection<Actor> aircraft, IReadOnlyList<KnownAntiAirZone> knownAaZones,
			AirRaidBidPassPerformanceDiagnostic passDiagnostic, out FransCommanderBidReport report)
		{
			using var raidPerf = FransBotLog.Profile(world, player, "Air.SubmitBids.RaidEvaluation");
			report = default;
			var target = mission.Target;
			if (mission.Type != FransMissionType.Raid)
				return false;
			if (!IsAirRaidEligibleTarget(mission))
			{
				LogFactRaidDiagnostic(mission, "rejected before capability analysis: target type is not Air RAID eligible");
				return false;
			}
			if (mission.IsRememberedIntel)
			{
				LogFactRaidDiagnostic(mission, "rejected: FACT is remembered/stale intel rather than a currently visible exact target");
				return false;
			}
			if (target == null || !IsVisibleEnemy(target))
			{
				LogFactRaidDiagnostic(mission, "rejected: exact FACT actor is not currently visible/alive");
				return false;
			}

			// A known SAM/AA exclusion is a hard feasibility rule. Air never bids an exact target
			// whose destination itself violates the configured YAML safety radius.
			if (!IsCellOutsideKnownAntiAir(target.Location, knownAaZones))
			{
				LogFactRaidDiagnostic(mission, "rejected: FACT destination lies inside known SAM/AA exclusion");
				return false;
			}

			var required = commanderCoreService.GetMissionRequiredContribution(FransCommanderKind.Air, mission);
			if (required == int.MaxValue)
			{
				LogFactRaidDiagnostic(mission, "rejected: required Air contribution could not be sized from the visible FACT");
				return false;
			}

			var geometryIdentity = GetKnownAntiAirGeometryIdentity(knownAaZones);
			var riskRevision = riskModelService?.RiskRevision ?? -1;
			var candidateSignature = BuildRaidCandidateSignature(aircraft);
			if (passDiagnostic != null)
			{
				passDiagnostic.KnownAntiAirSignature = geometryIdentity.Signature;
				passDiagnostic.RiskRevision = riskRevision;
			}
			if (commanderCoreService.TryGetSharedAirRaidBidTemplate(mission.TargetActorId, target.Location, required,
				geometryIdentity, riskRevision, candidateSignature, out var sharedTemplate))
			{
				if (passDiagnostic != null)
					passDiagnostic.RaidTemplateHits++;
				if (!sharedTemplate.Feasible)
					return false;
				report = MaterializeSharedRaidBid(sharedTemplate, BidderKey);
				return true;
			}
			if (passDiagnostic != null)
				passDiagnostic.RaidTemplateMisses++;

			var availableAttackers = 0;
			var antiAirPathRejected = 0;
			var metricRejected = 0;
			var ranked = new List<(Actor Actor, int Preference, int Eta, int Contribution, int Price, int PeakRisk, int Cost, int Travel)>();
			var candidateDiagnostic = passDiagnostic == null ? null : new AirRaidCandidatePerformanceDiagnostic(mission);
			var candidateStarted = candidateDiagnostic == null ? 0 : Stopwatch.GetTimestamp();
			var candidateElapsed = 0L;
			using (FransBotLog.Profile(world, player, "Air.SubmitBids.RaidCandidateEvaluation"))
			{
				foreach (var a in aircraft
					.Where(a => commanderCoreService.IsActorAvailableForMissionBid(FransCommanderKind.Air, BidderKey, a))
					.Where(a => a != reconRetreatActor && !raidRecoverySince.ContainsKey(a) && a.TraitOrDefault<Cargo>() == null && HasFullRaidAmmo(a) && CanAttackActor(a, target)))
				{
					availableAttackers++;
					if (!TryGetSharedCombatBidRouteMetrics(a, target.Location, knownAaZones, candidateDiagnostic, out var routeMetrics))
					{
						antiAirPathRejected++;
						continue;
					}
					var eta = routeMetrics.EstimatedEtaTicks;
					var contribution = commanderCoreService.EstimateRaidContribution(FransCommanderKind.Air, a, target);
					var price = commanderCoreService.PriceBid(FransCommanderKind.Air, routeMetrics.PeakRisk, eta, GetCombatValue(a));
					if (eta == int.MaxValue || contribution <= 0 || price == int.MaxValue || routeMetrics.IsCritical)
					{
						metricRejected++;
						continue;
					}
					var preference = GetRaidTargetPriorityRank(a, world.Map.Rules, mission.TargetActorType, mission.IsBuilding);
					ranked.Add((a, preference, eta, contribution, price, routeMetrics.PeakRisk, GetCombatValue(a), routeMetrics.TravelCells));
				}
				if (candidateDiagnostic != null)
					candidateElapsed = Stopwatch.GetTimestamp() - candidateStarted;
			}
			if (candidateDiagnostic != null)
			{
				candidateDiagnostic.AvailableAttackers = availableAttackers;
				candidateDiagnostic.AntiAirPathRejected = antiAirPathRejected;
				candidateDiagnostic.MetricRejected = metricRejected;
				candidateDiagnostic.ElapsedTimestampTicks = candidateElapsed;
				passDiagnostic.Candidates.Add(candidateDiagnostic);
			}

			var ordered = ranked
				.OrderBy(x => x.Preference).ThenBy(x => x.Price).ThenBy(x => x.Eta).ThenByDescending(x => x.Cost).ThenBy(x => x.Actor.ActorID)
				.Take(Info.MaximumAircraftPerMission).ToArray();
			if (ordered.Length == 0)
			{
				LogFactRaidDiagnostic(mission,
					$"rejected: no feasible full-ammo attacker; initial-capable {availableAttackers}, AA-path rejected {antiAirPathRejected}, ETA/risk/damage/price rejected {metricRejected}");
				commanderCoreService.StoreSharedAirRaidBidTemplate(mission.TargetActorId, target.Location, required,
					geometryIdentity, riskRevision, candidateSignature, new FransAirRaidBidTemplate(false, 0, Array.Empty<uint>(), 0, 0, 0, 0, 0, 0, required));
				return false;
			}

			var chosen = new List<Actor>();
			var offered = 0;
			var slowestEta = 0;
			var peakRisk = 0;
			var travel = 0;
			var totalCost = 0;
			foreach (var x in ordered)
			{
				chosen.Add(x.Actor);
				offered = (int)Math.Min(int.MaxValue, (long)offered + x.Contribution);
				slowestEta = Math.Max(slowestEta, x.Eta);
				peakRisk = Math.Max(peakRisk, x.PeakRisk);
				travel = Math.Max(travel, x.Travel);
				totalCost += x.Cost;
				if (offered >= required)
					break;
			}

			var groupPrice = commanderCoreService.PriceBid(FransCommanderKind.Air, peakRisk, slowestEta, totalCost);
			if (groupPrice == int.MaxValue)
			{
				LogFactRaidDiagnostic(mission, "rejected: assembled FACT strike group could not receive a finite bid price");
				commanderCoreService.StoreSharedAirRaidBidTemplate(mission.TargetActorId, target.Location, required,
					geometryIdentity, riskRevision, candidateSignature, new FransAirRaidBidTemplate(false, 0, Array.Empty<uint>(), 0, 0, 0, 0, 0, 0, required));
				return false;
			}
			groupPrice = ApplyRaidTargetPriorityToPrice(groupPrice, GetRaidGroupTargetPriorityRank(chosen, world.Map.Rules, mission.TargetActorType, mission.IsBuilding));
			LogFactRaidDiagnostic(mission,
				offered >= required
					? $"FEASIBLE full strike: {chosen.Count} aircraft, contribution {offered}/{required}, ETA {slowestEta}, risk {peakRisk}, final price {groupPrice}"
					: $"FEASIBLE PARTIAL only: {chosen.Count} aircraft, contribution {offered}/{required}, ETA {slowestEta}, risk {peakRisk}, final price {groupPrice}");
			var committedIds = chosen.Select(a => a.ActorID).ToArray();
			var template = new FransAirRaidBidTemplate(true, chosen[0].ActorID, committedIds, groupPrice, peakRisk, travel, totalCost, slowestEta, offered, required);
			commanderCoreService.StoreSharedAirRaidBidTemplate(mission.TargetActorId, target.Location, required,
				geometryIdentity, riskRevision, candidateSignature, template);
			report = MaterializeSharedRaidBid(template, BidderKey);
			return true;
		}

		bool TryGetOrBuildRaidBid(FransMission mission, IReadOnlyCollection<Actor> aircraft, IReadOnlyList<KnownAntiAirZone> knownAaZones,
			Dictionary<FransMission, FransCommanderBidReport> successfulRaidBids, HashSet<FransMission> failedRaidBids,
			AirRaidBidPassPerformanceDiagnostic passDiagnostic, out FransCommanderBidReport report)
		{
			if (successfulRaidBids.TryGetValue(mission, out report))
				return true;
			if (failedRaidBids.Contains(mission))
			{
				report = default;
				return false;
			}

			if (TryBuildRaidBid(mission, aircraft, knownAaZones, passDiagnostic, out report))
			{
				successfulRaidBids[mission] = report;
				return true;
			}

			failedRaidBids.Add(mission);
			return false;
		}

		HashSet<uint> GetRaidCapacityProtectedActorIds(IReadOnlyCollection<Actor> aircraft, IReadOnlyList<KnownAntiAirZone> knownAaZones,
			Dictionary<FransMission, FransCommanderBidReport> successfulRaidBids, HashSet<FransMission> failedRaidBids,
			AirRaidBidPassPerformanceDiagnostic passDiagnostic, out uint protectedTargetActorId)
		{
			protectedTargetActorId = 0;
			FransCommanderBidReport best = default;
			var found = false;
			foreach (var mission in generalService.CurrentMissions
				.Where(m => m.Type == FransMissionType.Raid)
				.OrderBy(m => m.TargetActorId))
			{
				if (passDiagnostic != null)
					passDiagnostic.RaidMissionCount++;
				if (!TryGetOrBuildRaidBid(mission, aircraft, knownAaZones, successfulRaidBids, failedRaidBids,
					passDiagnostic, out var candidate) ||
					candidate.OfferedContribution < candidate.RequiredContribution)
					continue;

				if (!found || candidate.TotalCost < best.TotalCost ||
					(candidate.TotalCost == best.TotalCost && candidate.EstimatedEtaTicks < best.EstimatedEtaTicks) ||
					(candidate.TotalCost == best.TotalCost && candidate.EstimatedEtaTicks == best.EstimatedEtaTicks && mission.TargetActorId < protectedTargetActorId))
				{
					found = true;
					best = candidate;
					protectedTargetActorId = mission.TargetActorId;
				}
			}

			if (!found)
				return [];
			return best.CommittedActorIds.ToHashSet();
		}

		static double AirRaidPerformanceMilliseconds(long timestampTicks) =>
			timestampTicks * 1000.0 / Stopwatch.Frequency;

		static string FormatAirRaidRoutePerformance(AirRaidRoutePerformanceDiagnostic route)
		{
			var path = route.Path;
			if (route.CacheHit)
				return $"actor={route.ActorId}@{route.StartCell}->{route.TargetCell},cache=Hit," +
					"geometryCache=NotChecked,physicalGeometrySolve=False," +
					$"outcome={(route.Feasible ? (route.IsCritical ? "FeasibleCritical" : "Feasible") : "NoSafeRoute")}";
			if (path == null)
				return $"actor={route.ActorId}@{route.StartCell}->{route.TargetCell},cache=Miss,outcome=NoDiagnostic";
			return $"actor={route.ActorId}@{route.StartCell}->{route.TargetCell},cache=Miss," +
				$"geometryCache={(path.GeometryCacheHit ? "Hit" : "Miss")},physicalGeometrySolve={path.PhysicalGeometrySolve}," +
				$"outcome={path.Outcome}," +
				$"feasible={route.Feasible},critical={route.IsCritical},zones={path.ZoneCount},nodes={path.NodeCount}," +
				$"ringCandidates={path.CandidatePointChecks},preparedExcludedCells={path.PreparedExcludedCellCount}," +
				$"preparedCellChecks={path.PreparedCellChecks},preparedReused={path.PreparedGeometryReused}," +
				$"escapeFallbackSegments={path.EscapeFallbackSegmentChecks}," +
				$"segmentChecks={path.SegmentChecks},segmentZoneChecks={path.SegmentZoneChecks}," +
				$"segmentCellSamples={path.SegmentCellSamples},graphPasses={path.GraphPasses}," +
				$"graphSelectionChecks={path.GraphSelectionChecks},graphNeighborChecks={path.GraphNeighborChecks}," +
				$"pathMs={AirRaidPerformanceMilliseconds(path.PathElapsedTimestampTicks):0.00}," +
				$"nodeBuildMs={AirRaidPerformanceMilliseconds(path.NodeBuildElapsedTimestampTicks):0.00}," +
				$"graphMs={AirRaidPerformanceMilliseconds(path.GraphElapsedTimestampTicks):0.00}," +
				$"riskCells={path.RiskCellCount},riskMs={AirRaidPerformanceMilliseconds(path.RiskElapsedTimestampTicks):0.00}," +
				$"etaMs={AirRaidPerformanceMilliseconds(path.EtaElapsedTimestampTicks):0.00}";
		}

		void LogAirRaidBidPassPerformance(AirRaidBidPassPerformanceDiagnostic diagnostic,
			IReadOnlyCollection<Actor> aircraft, IReadOnlyList<KnownAntiAirZone> knownAaZones, long elapsedTimestampTicks)
		{
			var elapsedMs = AirRaidPerformanceMilliseconds(elapsedTimestampTicks);
			var routeRequests = diagnostic.Candidates.Sum(c => c.Routes.Count);
			var routeCacheHits = diagnostic.Candidates.Sum(c => c.Routes.Count(r => r.CacheHit));
			var geometryCacheHits = diagnostic.Candidates.Sum(c => c.Routes.Count(r => !r.CacheHit && r.Path?.GeometryCacheHit == true));
			var pathSearches = diagnostic.Candidates.Sum(c => c.Routes.Count(r => r.Path?.PhysicalGeometrySolve == true));
			var previousRiskRevision = lastAirRaidPerformanceRiskRevision;
			var riskRevisionChanged = previousRiskRevision != int.MinValue && previousRiskRevision != diagnostic.RiskRevision;
			lastAirRaidPerformanceRiskRevision = diagnostic.RiskRevision;
			if (elapsedMs < AirRaidBidPerformanceLogThresholdMilliseconds)
			{
				if (airRaidGeometryCacheReuseProofLogged || geometryCacheHits == 0 || !riskRevisionChanged)
					return;
				airRaidGeometryCacheReuseProofLogged = true;
				OpenRA.Log.Write("debug",
					$"[AIR RAID BID PERF][WT {world.WorldTick}] player={player} bidder={BidderKey} " +
					$"cacheProof=FastGeometryReuse raidCapacityMs={elapsedMs:0.00} routeRequests={routeRequests} " +
					$"routeCacheHits={routeCacheHits} geometryCacheHits={geometryCacheHits} pathSearches={pathSearches} " +
					$"knownAaZones={knownAaZones.Count} knownAaSignature={diagnostic.KnownAntiAirSignature} " +
					$"previousRiskRevision={previousRiskRevision} riskRevision={diagnostic.RiskRevision} " +
					"diagnosticLogWriteExcluded=True");
				return;
			}
			if (geometryCacheHits > 0 && riskRevisionChanged)
				airRaidGeometryCacheReuseProofLogged = true;

			OpenRA.Log.Write("debug",
				$"[AIR RAID BID PERF][WT {world.WorldTick}] player={player} bidder={BidderKey} " +
				$"raidCapacityMs={elapsedMs:0.00} raidMissions={diagnostic.RaidMissionCount} " +
				$"templateHits={diagnostic.RaidTemplateHits} templateMisses={diagnostic.RaidTemplateMisses} " +
				$"candidateEvaluations={diagnostic.Candidates.Count} routeRequests={routeRequests} " +
				$"routeCacheHits={routeCacheHits} geometryCacheHits={geometryCacheHits} " +
				$"pathSearches={pathSearches} aircraft={aircraft.Count} " +
				$"knownAaZones={knownAaZones.Count} knownAaSignature={diagnostic.KnownAntiAirSignature} " +
				$"preparedExcludedCells={cachedKnownAntiAirPreparedExclusion?.ExcludedCellCount ?? 0} " +
				$"knownAaSnapshotWT={cachedKnownAntiAirWorldTick} combatSnapshotWT={combatIntelService.SnapshotWorldTick} " +
				$"previousRiskRevision={previousRiskRevision} riskRevision={diagnostic.RiskRevision} " +
				$"riskRevisionChanged={riskRevisionChanged} diagnosticLogWriteExcluded=True");

			foreach (var candidate in diagnostic.Candidates)
			{
				var candidatePathTicks = candidate.Routes.Sum(r => r.Path?.PathElapsedTimestampTicks ?? 0);
				var candidateRiskTicks = candidate.Routes.Sum(r => r.Path?.RiskElapsedTimestampTicks ?? 0);
				var candidateEtaTicks = candidate.Routes.Sum(r => r.Path?.EtaElapsedTimestampTicks ?? 0);
				var candidateAttributedTicks = candidatePathTicks + candidateRiskTicks + candidateEtaTicks;
				OpenRA.Log.Write("debug",
					$"[AIR RAID BID PERF][WT {world.WorldTick}] player={player} bidder={BidderKey} " +
					$"target={candidate.TargetActorId}/{candidate.TargetActorType}@{candidate.TargetCell} " +
					$"candidateMs={AirRaidPerformanceMilliseconds(candidate.ElapsedTimestampTicks):0.00} " +
					$"pathMs={AirRaidPerformanceMilliseconds(candidatePathTicks):0.00} " +
					$"riskMs={AirRaidPerformanceMilliseconds(candidateRiskTicks):0.00} " +
					$"etaMs={AirRaidPerformanceMilliseconds(candidateEtaTicks):0.00} " +
					$"otherMs={AirRaidPerformanceMilliseconds(Math.Max(0, candidate.ElapsedTimestampTicks - candidateAttributedTicks)):0.00} " +
					$"availableAttackers={candidate.AvailableAttackers} aaPathRejected={candidate.AntiAirPathRejected} " +
					$"metricRejected={candidate.MetricRejected} routes=[{string.Join(" | ", candidate.Routes.Select(FormatAirRaidRoutePerformance))}]");
			}
		}

		void LogRaidCapacityProtection(HashSet<uint> protectedActorIds, uint protectedTargetActorId)
		{
			if (lastRaidCapacityProtectedTargetActorId == protectedTargetActorId &&
				lastRaidCapacityProtectedActorIds.SetEquals(protectedActorIds))
				return;

			lastRaidCapacityProtectedActorIds.Clear();
			foreach (var actorId in protectedActorIds)
				lastRaidCapacityProtectedActorIds.Add(actorId);
			lastRaidCapacityProtectedTargetActorId = protectedTargetActorId;

			if (protectedActorIds.Count == 0)
			{
				FransBotLog.BotDebug(world,
					"{0}: Air capacity {1} has no currently feasible full-ammo RAID group to protect; RECON/SECURE may use otherwise-free aircraft.",
					player, BidderKey);
				return;
			}

			FransBotLog.BotDebug(world,
				"{0}: Air capacity {1} protects full-ammo RAID capability for target {2} with actor(s) [{3}]. These aircraft may still answer DEFEND but are withheld from Air RECON/SECURE bids.",
				player, BidderKey, protectedTargetActorId, string.Join(",", protectedActorIds.OrderBy(id => id)));
		}

		void SubmitBids(IReadOnlyCollection<Actor> aircraft)
		{
			using var bidPerf = FransBotLog.Profile(world, player, "Air.SubmitBids");
			KnownAntiAirZone[] knownAaZones;
			using (FransBotLog.Profile(world, player, "Air.SubmitBids.Prepare"))
			{
				generalService.EnsureCurrentMissions();
				knownAaZones = GetKnownAntiAirZones();
			}
			// Performance-only: capacity protection and actual RAID submission consume the exact
			// same bid object during this auction pass. The underlying AA path, ETA, risk, force
			// sizing, ranking and tie-break logic still runs once with the same inputs.
			var successfulRaidBids = new Dictionary<FransMission, FransCommanderBidReport>();
			var failedRaidBids = new HashSet<FransMission>();
			var raidPassDiagnostic = new AirRaidBidPassPerformanceDiagnostic();
			var raidCapacityStarted = Stopwatch.GetTimestamp();
			var raidCapacityElapsed = 0L;
			HashSet<uint> raidCapacityProtectedActorIds;
			using (FransBotLog.Profile(world, player, "Air.SubmitBids.RaidCapacity"))
			{
				raidCapacityProtectedActorIds = GetRaidCapacityProtectedActorIds(aircraft, knownAaZones,
					successfulRaidBids, failedRaidBids, raidPassDiagnostic, out var protectedRaidTargetActorId);
				LogRaidCapacityProtection(raidCapacityProtectedActorIds, protectedRaidTargetActorId);
				raidCapacityElapsed = Stopwatch.GetTimestamp() - raidCapacityStarted;
			}
			LogAirRaidBidPassPerformance(raidPassDiagnostic, aircraft, knownAaZones, raidCapacityElapsed);

			using var missionScanPerf = FransBotLog.Profile(world, player, "Air.SubmitBids.MissionScan");
			foreach (var mission in generalService.CurrentMissions)
			{
				if (mission.Type == FransMissionType.Secure && mission.TargetActorType == FransGeneralBotModule.SeaTransportBeachSecureTargetType)
					continue;
				if (mission.Type == FransMissionType.Secure &&
					commandBidService.ShouldPreemptSecureForDefend(FransCommanderKind.Air, BidderKey, mission.LastVisibleTargetCell))
					continue;

				var target = mission.Target;
				var targetCell = mission.LastVisibleTargetCell;

				if (mission.Type == FransMissionType.Secure &&
					generalService.TryGetDomainSecureClearWorldTick(mission.TargetActorId, FransCommanderKind.Air, out var airClearWorldTick) &&
					!HasNewAirSecureIntelSince(mission, airClearWorldTick, aircraft))
					continue;

				if (mission.Type == FransMissionType.Raid)
				{
					if (TryGetOrBuildRaidBid(mission, aircraft, knownAaZones, successfulRaidBids, failedRaidBids,
						null, out var raidBid))
						commandBidService.SubmitMissionBid(mission, raidBid);
					continue;
				}

				if (mission.Type == FransMissionType.Recon)
				{
					using var reconPerf = FransBotLog.Profile(world, player, "Air.SubmitBids.ReconEvaluation");
					var pioneerRecon = false;
					var reconTargetCell = targetCell;
					if (expansionStateService != null && expansionStateService.TryGetPioneerReconObjectiveNear(targetCell, out var pioneerReconObjective))
					{
						pioneerRecon = true;
						reconTargetCell = pioneerReconObjective;
					}
					var reconCandidates = new List<(Actor Actor, int Eta, int Price, int Vision, int Travel)>();
					foreach (var a in aircraft
						.Where(a => commanderCoreService.IsActorAvailableForMissionBid(FransCommanderKind.Air, BidderKey, a))
						.Where(a => pioneerRecon || !raidCapacityProtectedActorIds.Contains(a.ActorID))
						.Where(commanderCoreService.IsReconCandidateOperational)
						.Where(a => a != reconRetreatActor && a.TraitOrDefault<Cargo>() == null && !raidRecoverySince.ContainsKey(a))
						.Where(a => !ReconHealthBelowRetreatThreshold(a, out _)))
					{
						if (!TryBuildKnownAntiAirSafePath(a.Location, reconTargetCell, knownAaZones, out var safePath))
							continue;
						var eta = EstimateAirPathEtaTicks(a, safePath);
						var price = commanderCoreService.PriceReconBid(FransCommanderKind.Air, a, eta);
						var vision = commanderCoreService.GetReconVisionCells(a);
						if (eta != int.MaxValue && price != int.MaxValue && vision > 0)
							reconCandidates.Add((a, eta, price, vision, GetAirPathTravelCells(a.Location, safePath)));
					}
					var best = reconCandidates.OrderBy(x => x.Price).ThenBy(x => x.Eta).ThenBy(x => x.Actor.ActorID).FirstOrDefault();
					if (best.Actor == null)
						continue;
					commandBidService.SubmitMissionBid(mission, new FransCommanderBidReport(
						FransCommanderKind.Air, BidderKey, best.Actor.ActorID, new[] { best.Actor.ActorID },
						best.Price, 0, best.Travel, GetCombatValue(best.Actor), best.Eta, 1, 1, false));
					continue;
				}

				Actor[] candidates;
				using (FransBotLog.Profile(world, player, "Air.SubmitBids.AircraftCandidates"))
				{
					var eligibleCandidates = aircraft
						.Where(a => commanderCoreService.IsActorAvailableForMissionBid(FransCommanderKind.Air, BidderKey, a))
						.Where(a => mission.Type == FransMissionType.Defend || !raidCapacityProtectedActorIds.Contains(a.ActorID))
						.Where(a => a != reconRetreatActor && !raidRecoverySince.ContainsKey(a))
						.Where(a => mission.Type == FransMissionType.Defend || target == null || CanAttackActor(a, target))
						.OrderBy(a => (a.Location - targetCell).LengthSquared).ThenBy(a => a.ActorID);
					candidates = (mission.Type == FransMissionType.Defend
						? eligibleCandidates
						: eligibleCandidates.Take(Info.MaximumAircraftPerMission)).ToArray();
				}
				if (candidates.Length == 0)
					continue;
				var chosenNormal = new List<Actor>();
				var offeredNormal = 0;
				int requiredNormal;
				using (FransBotLog.Profile(world, player, "Air.SubmitBids.PackageEvaluation"))
				{
					if (mission.Type == FransMissionType.Defend)
					{
						var desiredUnitCount = commanderCoreService.GetDefendRequiredUnitCount(mission);
						var commitCount = Math.Min(desiredUnitCount, candidates.Length);
						chosenNormal.AddRange(candidates.Take(commitCount));
						offeredNormal = chosenNormal.Count;
						requiredNormal = desiredUnitCount;
					}
					else
					{
						var observedRequired = commanderCoreService.GetMissionRequiredContribution(FransCommanderKind.Air, mission);
						requiredNormal = mission.Type == FransMissionType.Secure
							? (int)Math.Clamp((long)observedRequired * 5L, 1L, int.MaxValue)
							: observedRequired;
						foreach (var actor in candidates)
						{
							chosenNormal.Add(actor);
							offeredNormal = (int)Math.Min(int.MaxValue, (long)offeredNormal + GetCombatValue(actor));
							if (offeredNormal >= requiredNormal)
								break;
						}
					}
				}

				if (chosenNormal.Count == 0)
					continue;
				var blockedByKnownAa = false;
				var peakRisk = 0;
				var slowestEta = 0;
				var travelNormal = 0;
				using (FransBotLog.Profile(world, player, "Air.SubmitBids.RouteEvaluation"))
				{
					foreach (var actor in chosenNormal)
					{
						if (!TryGetSharedCombatBidRouteMetrics(actor, targetCell, knownAaZones, out var routeMetrics))
						{
							blockedByKnownAa = true;
							break;
						}
						if (mission.Type != FransMissionType.Defend && routeMetrics.IsCritical)
						{
							blockedByKnownAa = true;
							break;
						}
						var eta = routeMetrics.EstimatedEtaTicks;
						if (eta == int.MaxValue)
						{
							blockedByKnownAa = true;
							break;
						}
						peakRisk = Math.Max(peakRisk, routeMetrics.PeakRisk);
						slowestEta = Math.Max(slowestEta, eta);
						travelNormal = Math.Max(travelNormal, routeMetrics.TravelCells);
					}
				}
				if (blockedByKnownAa)
					continue;

				using (FransBotLog.Profile(world, player, "Air.SubmitBids.Finalize"))
				{
					var subject = chosenNormal[0];
					var force = chosenNormal.Sum(GetCombatValue);
					var priceNormal = commanderCoreService.PriceBid(FransCommanderKind.Air, peakRisk, slowestEta, force);
					if (priceNormal == int.MaxValue)
						continue;
					var defendScore = mission.Type == FransMissionType.Defend
						? commanderCoreService.ScoreDefendResponse(mission, offeredNormal, requiredNormal, slowestEta, force)
						: default;
					commandBidService.SubmitMissionBid(mission, new FransCommanderBidReport(
						FransCommanderKind.Air, BidderKey, subject.ActorID, chosenNormal.Select(a => a.ActorID).ToArray(),
						priceNormal, peakRisk, travelNormal, force, slowestEta, offeredNormal, requiredNormal, false,
						defendScore.Utility, defendScore.StrengthScore, defendScore.UrgencyScore, defendScore.AssetRiskScore,
						defendScore.ResponseTimeCost, defendScore.OpportunityCost));
				}
			}
		}

		Actor[] ResolveCommittedAirActors(FransActiveMission mission) => (mission.CommittedActorIds ?? Array.Empty<uint>())
			.Where(id => !raidPreStrikeDroppedActorIds.Contains(id))
			.Select(id => combatIntelService.OwnedActors.FirstOrDefault(a => a.ActorID == id && IsManagedAircraft(a)))
			.Where(a => a != null && a.IsInWorld && !a.IsDead).ToArray();

		void ExecuteMission(IBot bot, IReadOnlyCollection<Actor> ready, Actor target, FransActiveMission mission)
		{
			RememberMissionAnchor(mission);
			if (mission.MissionType == FransMissionType.Secure)
			{
				ExecuteSecureMission(bot, ready, mission);
				return;
			}

			if (mission.MissionType == FransMissionType.Recon)
			{
				ExecuteReconMission(bot, ready, mission);
				return;
			}
			if (mission.MissionType == FransMissionType.Raid)
			{
				ExecuteRaidMission(bot, ready, target, mission);
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
				activeAircraft.Clear();
				var committed = ResolveCommittedAirActors(mission).Where(ready.Contains).ToArray();
				if (committed.Length != mission.CommittedActorIds.Length || committed.Length == 0)
				{
					commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, "exact committed Air actor snapshot is no longer ready");
					ResetMission();
					return;
				}
				foreach (var a in committed)
					activeAircraft.Add(a);

				FransBotLog.BotDebug(world,
					"{0}: Air Commander accepts MISSION {1} for target {2} at {3}; {4} aircraft, cost {5}. {6}",
					player, activeOrder, mission.TargetActorId, activeObjective, activeAircraft.Count, mission.TotalCost,
					activeOrder == FransCommanderOrder.Move ? "RiskModel remains active throughout MOVE; FIGHT will not start until engagement range." : "DEFEND accepts maximum combat risk immediately.");
			}

			activeAircraft.RemoveWhere(a => !ready.Contains(a));
			if (mission.CommittedActorIds != null && mission.CommittedActorIds.Length > 0)
				foreach (var id in mission.CommittedActorIds)
				{
					var returning = ready.FirstOrDefault(a => a.ActorID == id);
					if (returning != null)
						activeAircraft.Add(returning);
				}

			if (activeAircraft.Count == 0)
			{
				commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, "no armed Air Commander aircraft remain");
				ResetMission();
				return;
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

			if (activeOrder == FransCommanderOrder.Move)
			{
				if (target != null && !activeAircraft.Any(a => CanAttackActor(a, target)))
				{
					commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, "remembered target became visible but current Air force cannot attack it");
					ResetMission();
					return;
				}

				if (target != null && ShouldEnterFight(target))
				{
					BeginFight();
					FransBotLog.BotDebug(world,
						"{0}: Air Commander MOVE -> FIGHT near {1} against visible {2} {3}; first attack is now authorized and RiskModel is ignored. Combat baseline {4}, fallback {5}.",
						player, activeObjective, target.Info.Name, target.ActorID, retreatBaselineCombatValue, retreatAnchorPoint);
					ExecuteFightMicro(bot, target);
					return;
				}

				hasLastSafeMoveAnchor = true;
				lastSafeMoveAnchor = GetGroupCenter(activeAircraft);

				if (!hasMoveRiskCheck || moveRiskObjective != activeObjective || world.WorldTick >= nextMoveRiskCheckTick)
				{
					var lead = activeAircraft.OrderBy(a => (a.Location - activeObjective).LengthSquared).ThenBy(a => a.ActorID).First();
					if (!TryBuildKnownAntiAirSafePath(lead, activeObjective, out var safePath))
					{
						commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey,
							$"known SAM/AA exclusion blocks Air PathMove to {activeObjective}");
						ResetMission();
						return;
					}
					var route = EvaluateAirPathRisk(lead, safePath);
					hasMoveRiskCheck = true;
					moveRiskObjective = activeObjective;
					moveRiskAllowed = !route.IsCritical;
					nextMoveRiskCheckTick = world.WorldTick + Info.MoveRefreshInterval;
				}

				if (moveRiskAllowed)
					foreach (var a in activeAircraft.OrderBy(x => x.ActorID))
						if (!QueueMove(bot, a, activeObjective, false))
						{
							commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey,
								$"known SAM/AA exclusion blocks committed Air PathMove to {activeObjective}");
							ResetMission();
							return;
						}
				return;
			}

			if (activeOrder == FransCommanderOrder.Defend)
			{
				if (target != null && IsVisibleEnemy(target))
				{
					if (ShouldEnterFight(target))
						ExecuteFightMicro(bot, target);
					else
					{
						foreach (var a in activeAircraft.OrderBy(x => x.ActorID))
							if (!QueueMove(bot, a, activeObjective, true))
							{
								commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, "known SAM/AA exclusion blocks DEFEND PathMove");
								ResetMission();
								return;
							}
					}
				}
				else if (lostContactSinceWorldTick >= 0 && world.WorldTick - lostContactSinceWorldTick <= Info.FightLostContactHoldTicks)
				{
					foreach (var a in activeAircraft.OrderBy(x => x.ActorID))
						if (!QueueMove(bot, a, activeObjective, false))
						{
							commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, "known SAM/AA exclusion blocks lost-contact PathMove");
							ResetMission();
							return;
						}
				}
				else
					foreach (var a in activeAircraft.OrderBy(x => x.ActorID))
						if (!QueueMove(bot, a, activeObjective, false))
						{
							commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, "known SAM/AA exclusion blocks authoritative lost-contact DEFEND PathMove");
							ResetMission();
							return;
						}
				return;
			}

			if (activeOrder == FransCommanderOrder.Fight)
			{
				if (target != null && IsVisibleEnemy(target))
					ExecuteFightMicro(bot, target);
				else if (lostContactSinceWorldTick >= 0 && world.WorldTick - lostContactSinceWorldTick <= Info.FightLostContactHoldTicks)
				{
					foreach (var a in activeAircraft.OrderBy(x => x.ActorID))
						if (!QueueMove(bot, a, activeObjective, false))
						{
							commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, "known SAM/AA exclusion blocks lost-contact PathMove");
							ResetMission();
							return;
						}
				}
				else
				{
					commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, "FIGHT contact cleared/lost");
					ResetMission();
				}
			}
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
				foreach (var aircraft in ResolveCommittedAirActors(mission))
					QueueStopOrder(null, aircraft);
				FransBotLog.BotDebug(world,
					"{0}: Air {1} holds COMBINED SECURE {2} until WT {3}; its ETA is {4} WT and {5} domains are timing departure toward the same area.",
					player, BidderKey, mission.TargetActorId, mission.ExecuteAfterWorldTick, mission.EstimatedEtaTicks, mission.CombinedSecureGroupSize);
			}
			return true;
		}

		void ReportSecureRetreatIfLast(uint targetActorId, string reason)
		{
			if (commandBidService.HasOtherActiveSecureMission(targetActorId, FransCommanderKind.Air, BidderKey))
			{
				FransBotLog.BotDebug(world,
					"{0}: Air {1} leaves COMBINED SECURE {2}: {3}. Another domain assignment remains active, so General does not reset the whole SECURE.",
					player, BidderKey, targetActorId, reason);
				return;
			}
			generalService.ReportSecureRetreat(targetActorId, reason);
		}

		void ExecuteSecureMission(IBot bot, IReadOnlyCollection<Actor> ready, FransActiveMission mission)
		{
			if (HoldCombinedSecureUntilLaunch(mission))
			{
				LogAirSecureLiveness(mission, "CombinedHold", mission.LastVisibleTargetCell,
					$"executeAfterWT={mission.ExecuteAfterWorldTick}");
				return;
			}

			RememberMissionAnchor(mission);
			var changed = activeTargetActorId != mission.TargetActorId || activeMissionType != FransMissionType.Secure;
			activeMissionType = FransMissionType.Secure;
			ResetReconState();

			if (changed)
			{
				ResetAirSecureLivenessDiagnostics();
				activeTargetActorId = mission.TargetActorId;
				activeObjective = mission.LastVisibleTargetCell;
				activeOrder = FransCommanderOrder.Move;
				activeOrderStartedWorldTick = world.WorldTick;
				lostContactSinceWorldTick = -1;
				secureClearSinceWorldTick = -1;
				activeAircraft.Clear();
				var committed = ResolveCommittedAirActors(mission);
				if (committed.Length != mission.CommittedActorIds.Length || committed.Length == 0)
				{
					LogAirSecureLiveness(mission, "CommittedSnapshotUnavailable", activeObjective,
						$"resolved={committed.Length}/{mission.CommittedActorIds.Length}");
					ReportSecureRetreatIfLast(mission.TargetActorId, "Air SECURE exact committed actor snapshot became unavailable");
					commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, "SECURE exact committed Air actor snapshot is unavailable");
					LogAirSecureReleased(mission, activeObjective, "exact committed actor snapshot unavailable");
					ResetMission();
					return;
				}
				foreach (var aircraft in committed)
					activeAircraft.Add(aircraft);
				LogAirSecureLiveness(mission, "Accepted", activeObjective, "immutable committed snapshot resolved");
				FransBotLog.BotDebug(world,
					"{0}: Air Commander accepts GENERAL SECURE {1} {2} at {3}; {4} aircraft, bid cost {5}. Air owns domain-specific CLEAR, including persistent remembered buildings; Air CLEAR closes only the Air domain and never moves Ground ANCHOR.",
					player, mission.TargetActorType == "fact" ? "enemy FACT" : "MineCluster", mission.TargetActorId, activeObjective, activeAircraft.Count, mission.TotalCost);
			}

			activeAircraft.RemoveWhere(a => a == null || !a.IsInWorld || a.IsDead || a.Owner != player);
			if (activeAircraft.Count == 0)
			{
				// SECURE ownership survives a normal rearm/service cycle, but not the physical loss of
				// the entire immutable committed snapshot. Distinguish live-unarmed from dead/missing.
				var liveCommitted = ResolveCommittedAirActors(mission);
				if (liveCommitted.Length == 0)
				{
					LogAirSecureLiveness(mission, "CommittedSnapshotUnavailable", activeObjective,
						"every committed aircraft is physically missing/dead");
					ReportSecureRetreatIfLast(mission.TargetActorId, "Air SECURE committed snapshot physically lost");
					commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, "SECURE committed Air snapshot was physically lost; capacity released for rebid");
					LogAirSecureReleased(mission, activeObjective, "committed snapshot physically lost");
					FransBotLog.BotDebug(world,
						"{0}: Air SECURE MISSION {1} releases {2}: every committed aircraft is dead/missing; this is not a rearm wait.",
						player, mission.TargetActorId, BidderKey);
					ResetMission();
					return;
				}

				var committedIds = (mission.CommittedActorIds ?? Array.Empty<uint>()).ToHashSet();
				IEnumerable<Actor> returning = ready.Where(a => committedIds.Contains(a.ActorID) && HasAmmo(a));
				foreach (var aircraft in returning)
					activeAircraft.Add(aircraft);
				if (activeAircraft.Count == 0)
				{
					secureClearSinceWorldTick = -1;
					LogAirSecureLiveness(mission, "ServiceWait", activeObjective,
						"committed aircraft remain alive but none are currently ammo-ready");
					return;
				}
			}

			var armedSecureAircraft = activeAircraft.Where(HasAmmo).ToArray();
			if (armedSecureAircraft.Length == 0)
			{
				secureClearSinceWorldTick = -1;
				LogAirSecureLiveness(mission, "ServiceWait", activeObjective,
					"live immutable committed snapshot has no usable ammo");
				return;
			}

			var threatRadiusSq = Info.SecureThreatRadius * Info.SecureThreatRadius;
			var secureKnownAaZones = GetKnownAntiAirZones();
			var threat = combatIntelService.VisibleEnemies
				.Where(IsVisibleEnemy)
				.Where(t => (t.Location - mission.LastVisibleTargetCell).LengthSquared <= threatRadiusSq)
				.Where(t => armedSecureAircraft.Any(a => CanAttackActor(a, t) && IsAirAttackCorridorKnownAaSafe(a, t, secureKnownAaZones)))
				.OrderByDescending(GetCombatValue)
				.ThenBy(t => (t.Location - activeObjective).LengthSquared)
				.ThenBy(t => t.ActorID)
				.FirstOrDefault();

			if (threat != null)
			{
				secureClearSinceWorldTick = -1;
				if (activeOrder != FransCommanderOrder.Fight)
					BeginFight();
				ExecuteFightMicro(bot, threat);
				LogAirSecureLiveness(mission, "VisibleThreatFight", mission.LastVisibleTargetCell,
					$"target={threat.ActorID}/{threat.Info.Name}@{threat.Location}");
				return;
			}

			// Air CLEAR uses the same persistent shared building memory as Ground. A remembered
			// FACT/PROC/WEAP/defense inside the SECURE area must be directly disproved or destroyed
			// before Air may report CLEAR. If still hidden, fly to the last-seen cell to verify it.
			if (TrySelectRememberedSecureBuilding(mission.LastVisibleTargetCell, Info.SecureThreatRadius, out var rememberedBuilding))
			{
				secureClearSinceWorldTick = -1;
				var visibleRemembered = rememberedBuilding.IsVisible ? world.GetActorById(rememberedBuilding.ActorId) : null;
				if (visibleRemembered != null && IsVisibleEnemy(visibleRemembered))
				{
					var canEngage = armedSecureAircraft.Any(a => CanAttackActor(a, visibleRemembered) &&
						IsAirAttackCorridorKnownAaSafe(a, visibleRemembered, secureKnownAaZones));
					if (!canEngage)
					{
						LogAirSecureLiveness(mission, "VisibleRememberedCapabilityRejected", rememberedBuilding.LastSeenCell,
							"visible remembered building is not safely attackable by committed wing", rememberedBuilding);
						commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey,
							"Air SECURE visible remembered building is not safely attackable by the committed wing; release for rebid");
						LogAirSecureReleased(mission, rememberedBuilding.LastSeenCell,
							"visible remembered building is not safely attackable");
						ResetMission();
						return;
					}

					if (activeOrder != FransCommanderOrder.Fight)
						BeginFight();
					ExecuteFightMicro(bot, visibleRemembered);
					LogAirSecureLiveness(mission, "VisibleThreatFight", rememberedBuilding.LastSeenCell,
						$"rememberedTarget={rememberedBuilding.ActorId}/{rememberedBuilding.ActorType}", rememberedBuilding);
					return;
				}

				activeObjective = rememberedBuilding.LastSeenCell;
				foreach (var aircraft in armedSecureAircraft.OrderBy(a => a.ActorID))
					if (!QueueMove(bot, aircraft, activeObjective, false, allowSecureFlyIdleReacquire: true))
					{
						LogAirSecureLiveness(mission, "PathRejected", activeObjective,
							"known SAM/AA exclusion blocks remembered-building verification", rememberedBuilding);
						commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey,
							"known SAM/AA exclusion blocks remembered-building SECURE verification");
						LogAirSecureReleased(mission, activeObjective,
							"known SAM/AA exclusion blocks remembered-building verification");
						ResetMission();
						return;
					}
				LogAirSecureLiveness(mission, "RememberedBuildingVerification", activeObjective,
					"persistent remembered building keeps CLEAR open pending direct verification", rememberedBuilding);
				return;
			}

			activeObjective = mission.LastVisibleTargetCell;
			activeOrder = FransCommanderOrder.Move;
			hasLastSafeMoveAnchor = true;
			lastSafeMoveAnchor = GetGroupCenter(activeAircraft);
			foreach (var aircraft in armedSecureAircraft.OrderBy(a => a.ActorID))
				if (!QueueMove(bot, aircraft, activeObjective, false, allowSecureFlyIdleReacquire: true))
				{
					LogAirSecureLiveness(mission, "PathRejected", activeObjective,
						"known SAM/AA exclusion blocks objective move");
					ReportSecureRetreatIfLast(mission.TargetActorId, "known SAM/AA exclusion blocks Air SECURE PathMove");
					commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, "known SAM/AA exclusion blocks Air SECURE PathMove");
					LogAirSecureReleased(mission, activeObjective, "known SAM/AA exclusion blocks objective move");
					ResetMission();
					return;
				}

			var assemblyRadiusSq = Info.SecureAssemblyRadius * Info.SecureAssemblyRadius;
			var assembled = armedSecureAircraft.Where(a => (a.Location - activeObjective).LengthSquared <= assemblyRadiusSq).ToArray();
			var requiredCount = Math.Max(1, (activeAircraft.Count * 3 + 3) / 4);
			if (assembled.Length < requiredCount)
			{
				secureClearSinceWorldTick = -1;
				var branch = assembled.Length == 0 ? "ObjectiveMove" : "AssemblyWait";
				LogAirSecureLiveness(mission, branch, activeObjective,
					"committed armed aircraft have not met the unchanged assembly requirement",
					assembled: assembled.Length, required: requiredCount);
				return;
			}

			if (secureClearSinceWorldTick < 0)
			{
				secureClearSinceWorldTick = world.WorldTick;
				LogAirSecureLiveness(mission, "ClearHold", activeObjective,
					"assembly reached; unchanged clear hold begins", assembled: assembled.Length, required: requiredCount);
				return;
			}
			if (world.WorldTick - secureClearSinceWorldTick < Info.SecureClearHoldTicks)
			{
				LogAirSecureLiveness(mission, "ClearHold", activeObjective,
					"unchanged clear hold remains in progress", assembled: assembled.Length, required: requiredCount);
				return;
			}

			var securePoint = mission.LastVisibleTargetCell;
			var transportLossSecure = mission.TargetActorType == FransGeneralBotModule.TransportLossSecureTargetType;
			if ((mission.CombinedSecureGroupSize <= 1 || transportLossSecure) &&
				!generalService.CompleteDomainSecureMission(mission.TargetActorId, FransCommanderKind.Air, securePoint,
					$"Air cleared {Info.SecureThreatRadius}-cell area including persistent remembered enemy buildings and assembled {assembled.Length}/{activeAircraft.Count} committed aircraft") &&
				!(transportLossSecure && !generalService.IsTransportLossSecure(mission.TargetActorId)))
			{
				LogAirSecureLiveness(mission, "ClearHold", activeObjective,
					"General has not accepted domain completion; ownership remains unchanged",
					assembled: assembled.Length, required: requiredCount);
				return;
			}
			LogAirSecureLiveness(mission, "ClearComplete", securePoint,
				"General accepted the unchanged Commander CLEAR transition", assembled: assembled.Length, required: requiredCount);

			if (mission.CombinedSecureGroupSize > 1 && !transportLossSecure)
				FransBotLog.BotDebug(world,
					"{0}: Air COMBINED SECURE support {1} is locally CLEAR at {2}; Air releases its assignment without closing General's target. Ground remains the territorial SECURE authority.",
					player, mission.TargetActorId, securePoint);

			var releasedAircraft = ResolveCommittedAirActors(mission);
			commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey,
				"Air SECURE clear complete; domain mission closed without changing Ground ANCHOR");
			LogAirSecureReleased(mission, securePoint, "normal Air SECURE CLEAR released Broker ownership");
			foreach (var aircraft in releasedAircraft.OrderBy(a => a.ActorID))
			{
				if (!HasAmmo(aircraft) || NeedsNativeRepair(aircraft))
					QueueReturnToBase(bot, aircraft, true);
				else if (hasMissionAnchorPoint)
					QueueMove(bot, aircraft, missionAnchorPoint, true);
			}

			hasLastSafeMoveAnchor = true;
			lastSafeMoveAnchor = securePoint;
			retreatBaselineCombatValue = 0;
			FransBotLog.BotDebug(world,
				"{0}: Air Commander SECURE {1} is CLEAR at {2}: no persistent remembered enemy building remains inside {3} cells. Air domain mission closes without changing Ground ANCHOR and {4} releases immediately.",
				player, mission.TargetActorId, securePoint, Info.SecureThreatRadius, BidderKey);
			ResetMission();
		}

		bool HasNewAirSecureIntelSince(FransMission mission, int clearWorldTick, IReadOnlyCollection<Actor> aircraft)
		{
			combatIntelService.EnsureCurrentSnapshot();
			var available = aircraft
				.Where(a => commanderCoreService.IsActorAvailableForMissionBid(FransCommanderKind.Air, BidderKey, a))
				.Where(a => a != reconRetreatActor && !raidRecoverySince.ContainsKey(a))
				.ToArray();
			if (available.Length == 0)
				return false;

			var radiusSq = Info.SecureThreatRadius * Info.SecureThreatRadius;
			foreach (var contact in combatIntelService.EnemyCombatContacts.Where(c =>
				c.ActorId != 0 &&
				c.Owner != null &&
				PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(c.Owner)) &&
				c.LastSeenWorldTick > clearWorldTick &&
				(c.LastSeenCell - mission.LastVisibleTargetCell).LengthSquared <= radiusSq))
			{
				// Buildings are persistent strategic contacts: a newer sighting means Air must
				// verify/clear them again even if they have since left vision.
				if (contact.IsBuilding)
					return true;

				// Mobile memory can move. Re-open Air SECURE only for a currently visible mobile
				// contact that this available wing can actually attack.
				if (!contact.IsVisible)
					continue;
				var visible = world.GetActorById(contact.ActorId);
				if (visible != null && IsVisibleEnemy(visible) && available.Any(a => CanAttackActor(a, visible)))
					return true;
			}

			return false;
		}

		bool TrySelectRememberedSecureBuilding(CPos center, int radiusCells, out FransCombatIntelContact building)
		{
			combatIntelService.EnsureCurrentSnapshot();
			var radiusSq = radiusCells * radiusCells;
			var candidates = combatIntelService.EnemyCombatContacts
				.Where(c => c.ActorId != 0 && c.IsBuilding)
				.Where(c => c.Owner != null && PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(c.Owner)))
				.Where(c => (c.LastSeenCell - center).LengthSquared <= radiusSq)
				.OrderByDescending(c => c.IsVisible)
				.ThenBy(c => (c.LastSeenCell - center).LengthSquared)
				.ThenBy(c => c.ActorId)
				.ToArray();

			building = candidates.FirstOrDefault();
			return building.ActorId != 0;
		}

		void BeginFight()
		{
			activeOrder = FransCommanderOrder.Fight;
			activeOrderStartedWorldTick = world.WorldTick;
			lostContactSinceWorldTick = -1;
			var fightValue = Math.Max(1, activeAircraft.Sum(GetCombatValue));
			retreatBaselineCombatValue = Math.Max(retreatBaselineCombatValue, fightValue);
			retreatAnchorPoint = hasMissionAnchorPoint ? missionAnchorPoint : hasLastSafeMoveAnchor ? lastSafeMoveAnchor : GetGroupCenter(activeAircraft);
		}

		bool ShouldRetreatFromFight(IReadOnlyCollection<Actor> aircraft, out int currentCombatValue)
		{
			// Ammo expenditure is not a casualty. RETREAT measures surviving committed aircraft value,
			// while unarmed aircraft independently use native ReturnToBase/rearm behavior.
			currentCombatValue = activeAircraft.Where(a => aircraft.Contains(a)).Sum(GetCombatValue);
			if (retreatBaselineCombatValue <= 0 || currentCombatValue <= 0)
				return false;
			var threshold = Math.Max(1, retreatBaselineCombatValue * Info.RetreatAtRemainingForcePercent / 100);
			return currentCombatValue <= threshold;
		}

		void BeginRetreat(IBot bot, IReadOnlyCollection<Actor> aircraft, int currentCombatValue)
		{
			var retreatMissionType = activeMissionType;
			var retreatTargetId = activeTargetActorId;
			if (retreatMissionType == FransMissionType.Raid && retreatTargetId != 0)
				generalService.ReportRaidRetreat(retreatTargetId, $"Air force collapse {currentCombatValue}/{retreatBaselineCombatValue}");
			else if (retreatMissionType == FransMissionType.Secure && retreatTargetId != 0)
				ReportSecureRetreatIfLast(retreatTargetId, $"Air force collapse {currentCombatValue}/{retreatBaselineCombatValue}");
			commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey,
				$"FIGHT force collapse {currentCombatValue}/{retreatBaselineCombatValue}; RETREAT owns ANCHOR POINT recovery");
			if (retreatMissionType == FransMissionType.Secure && secureDiagnosticMission.HasValue)
				LogAirSecureReleased(secureDiagnosticMission.Value, activeObjective,
					$"existing FIGHT force-collapse RETREAT {currentCombatValue}/{retreatBaselineCombatValue}");
			retreatRecoveryActive = true;
			retreatStartedWorldTick = world.WorldTick;
			activeTargetActorId = 0;
			activeOrder = FransCommanderOrder.Retreat;
			activeOrderStartedWorldTick = world.WorldTick;
			activeObjective = retreatAnchorPoint;
			lostContactSinceWorldTick = -1;
			activeAircraft.RemoveWhere(a => a == null || !a.IsInWorld || a.IsDead || !aircraft.Contains(a));
			ClearRecoveryProgressTracking();
			foreach (var a in activeAircraft)
				ObserveRecoveryProgress(a, retreatAnchorPoint, requireFullAmmo: false, initialize: true);
			RecruitRecoveryAircraft(aircraft);
			RefreshTransientReservations();
			FransBotLog.BotDebug(world,
				"{0}: Air Commander FIGHT -> RETREAT: combat value {1}/{2}; ANCHOR POINT {3}. Survivors plus newly available/repaired/rearmed free aircraft reinforce this wing until {4}% of the pre-fight value is assembled at the same ANCHOR POINT.",
				player, currentCombatValue, retreatBaselineCombatValue, retreatAnchorPoint, Info.ResumeOffenseAtOriginalForcePercent);
			foreach (var a in activeAircraft.OrderBy(a => a.ActorID))
				RouteAirRetreatUnit(bot, a, true);
		}

		void ExecuteRetreatRecovery(IBot bot, IReadOnlyCollection<Actor> aircraft)
		{
			activeOrder = FransCommanderOrder.Retreat;
			activeObjective = retreatAnchorPoint;
			activeAircraft.RemoveWhere(a => !aircraft.Contains(a));
			RemoveStaleRecoveryProgressTracking();
			RecruitRecoveryAircraft(aircraft);
			RefreshTransientReservations();
			foreach (var a in activeAircraft.OrderBy(a => a.ActorID))
			{
				ObserveRecoveryProgress(a, retreatAnchorPoint, requireFullAmmo: false, initialize: false);
				RouteAirRetreatUnit(bot, a, false);
			}

			var radiusSq = Info.RetreatAssemblyRadius * Info.RetreatAssemblyRadius;
			var assembledValue = activeAircraft
				.Where(IsAirRecoveryReady)
				.Where(a => (a.Location - retreatAnchorPoint).LengthSquared <= radiusSq)
				.Sum(GetCombatValue);
			var requiredValue = Math.Max(1, retreatBaselineCombatValue * Info.ResumeOffenseAtOriginalForcePercent / 100);
			if (assembledValue < requiredValue)
				return;

			FransBotLog.BotDebug(world,
				"{0}: Air Commander RETREAT recovery complete at ANCHOR POINT {1}: assembled combat value {2}/{3}.",
				player, retreatAnchorPoint, assembledValue, requiredValue);
			retreatRecoveryActive = false;
			retreatStartedWorldTick = -1;
			retreatBaselineCombatValue = 0;
			ClearRecoveryProgressTracking();
			hasLastSafeMoveAnchor = true;
			lastSafeMoveAnchor = retreatAnchorPoint;
			ResetMission();
			RefreshTransientReservations();
		}

		void RecruitRecoveryAircraft(IReadOnlyCollection<Actor> aircraft)
		{
			if (!retreatRecoveryActive || retreatBaselineCombatValue <= 0)
				return;

			var requiredValue = Math.Max(1, retreatBaselineCombatValue * Info.ResumeOffenseAtOriginalForcePercent / 100);
			var readyRecoveryValue = activeAircraft.Where(IsAirRecoveryReady).Sum(GetCombatValue);
			if (readyRecoveryValue >= requiredValue)
				return;

			foreach (var candidate in aircraft
				.Where(a => !activeAircraft.Contains(a) && a != reconRetreatActor && !raidRecoverySince.ContainsKey(a))
				.Where(a => commanderCoreService.IsActorAvailableForBidder(FransCommanderKind.Air, BidderKey, a))
				.Where(IsAirRecoveryReady)
				.OrderBy(a => (a.Location - retreatAnchorPoint).LengthSquared)
				.ThenBy(a => a.ActorID))
			{
				activeAircraft.Add(candidate);
				ObserveRecoveryProgress(candidate, retreatAnchorPoint, requireFullAmmo: false, initialize: true);
				readyRecoveryValue += GetCombatValue(candidate);
				if (readyRecoveryValue >= requiredValue)
					break;
			}
		}

		void RefreshTransientReservations()
		{
			if (commandBidService == null)
				return;

			var ids = new HashSet<uint>();
			if (reconRetreatActor != null && reconRetreatActor.IsInWorld && !reconRetreatActor.IsDead)
				ids.Add(reconRetreatActor.ActorID);
			foreach (var a in raidRecoverySince.Keys)
				if (a != null && a.IsInWorld && !a.IsDead)
					ids.Add(a.ActorID);
			// Active RAID actors are already protected by their mission. Mirroring them into the existing
			// transient reservation layer bridges the short broker -> Commander handoff if General closes the mission;
			// another Air wing cannot steal them before this wing converts them to raidRecoverySince.
			if (activeMissionType == FransMissionType.Raid)
				foreach (var a in activeAircraft)
					if (a != null && a.IsInWorld && !a.IsDead)
						ids.Add(a.ActorID);
			if (retreatRecoveryActive)
				foreach (var a in activeAircraft)
					if (a != null && a.IsInWorld && !a.IsDead)
						ids.Add(a.ActorID);

			commandBidService.UpdateTransientActorReservations(FransCommanderKind.Air, BidderKey, ids.OrderBy(id => id).ToArray());
		}

		void WriteAirUtilization(IReadOnlyCollection<Actor> allAircraft)
		{
			var recon = 0;
			var raid = 0;
			var secure = 0;
			var defend = 0;
			var missionCommitted = 0;
			var recovery = 0;
			var rearm = 0;
			var repair = 0;
			var idleReady = 0;
			var activeWings = new HashSet<string>();

			foreach (var a in allAircraft)
			{
				var hasMission = commandBidService.TryGetActorMission(FransCommanderKind.Air, a.ActorID, out var kind, out var wing);
				if (hasMission)
				{
					missionCommitted++;
					if (!string.IsNullOrEmpty(wing))
						activeWings.Add(wing);
					switch (kind)
					{
						case FransMissionType.Recon: recon++; break;
						case FransMissionType.Raid: raid++; break;
						case FransMissionType.Secure: secure++; break;
						case FransMissionType.Defend: defend++; break;
					}
				}

				if (!HasAmmo(a))
					rearm++;
				if (NeedsNativeRepair(a))
					repair++;

				var occupied = commandBidService.IsActorUnavailableForBidder(FransCommanderKind.Air, "__air-utilization__", a.ActorID);
				if (!hasMission && occupied)
					recovery++;
				else if (!occupied && HasAmmo(a) && !NeedsNativeRepair(a))
					idleReady++;
			}

			FransBotLog.BotDebug(world,
				"{0}: AIR UTILIZATION total {1} | mission-committed {2} in {3} wing(s) | RECON {4} | RAID {5} | SECURE {6} | DEFEND {7} | recovery {8} | rearm {9} | repair {10} | idle-ready {11}.",
				player, allAircraft.Count, missionCommitted, activeWings.Count, recon, raid, secure, defend, recovery, rearm, repair, idleReady);
		}

		static CPos GetGroupCenter(IEnumerable<Actor> units)
		{
			var live = units.Where(a => a != null && a.IsInWorld && !a.IsDead).ToArray();
			if (live.Length == 0)
				return default;
			return new CPos(live.Sum(a => a.Location.X) / live.Length, live.Sum(a => a.Location.Y) / live.Length);
		}


		void ExecuteRaidMission(IBot bot, IReadOnlyCollection<Actor> ready, Actor target, FransActiveMission mission)
		{
			if (!IsAirRaidEligibleTarget(mission))
			{
				commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, "Air RAID target is outside buildings/HARV/ARTY/V2/e3 doctrine");
				ResetMission();
				return;
			}

			var visibleTarget = target != null && IsVisibleEnemy(target);
			var required = mission.RequiredContribution;
			var damage = mission.OfferedContribution;
			var changed = activeMissionType != FransMissionType.Raid || activeTargetActorId != mission.TargetActorId;
			if (changed)
			{
				raidPreStrikeDroppedActorIds.Clear();
				raidCommittedContributionByActor.Clear();
			}

			Actor[] selected;
			if (!raidStrikeIssued)
			{
				// The auction snapshot still defines the maximum strike group, but a single
				// aircraft that temporarily loses full-ammo/service readiness no longer forces
				// the whole RAID back through the broker. Drop unavailable members only when the
				// remaining fully ready aircraft still meet the original damage requirement.
				var expectedIds = (mission.CommittedActorIds ?? Array.Empty<uint>())
					.Where(id => !raidPreStrikeDroppedActorIds.Contains(id)).ToArray();
				selected = expectedIds
					.Select(id => ready.FirstOrDefault(a => a.ActorID == id && HasFullRaidAmmo(a) &&
						(!visibleTarget || CanAttackActor(a, target))))
					.Where(a => a != null)
					.ToArray();

				if (selected.Length == 0)
				{
					ReleaseRaidForRebid(bot, mission.TargetActorId, "no committed Air RAID aircraft remains fully ready before strike");
					return;
				}

				if (selected.Length != expectedIds.Length)
				{
					long remainingContribution = 0;
					var contributionKnown = true;
					foreach (var aircraft in selected)
					{
						var contribution = 0;
						if (visibleTarget)
						{
							contribution = commanderCoreService.EstimateRaidContribution(FransCommanderKind.Air, aircraft, target);
							if (contribution > 0)
								raidCommittedContributionByActor[aircraft.ActorID] = contribution;
						}
						else if (raidCommittedContributionByActor.TryGetValue(aircraft.ActorID, out var rememberedContribution))
							contribution = rememberedContribution;

						if (contribution <= 0)
						{
							contributionKnown = false;
							break;
						}
						remainingContribution += contribution;
					}

					if (!contributionKnown || remainingContribution < required)
					{
						ReleaseRaidForRebid(bot, mission.TargetActorId,
							contributionKnown
								? $"committed Air RAID readiness changed and remaining ready damage {remainingContribution}/{required} is insufficient"
								: "committed Air RAID readiness changed before strike and remaining damage cannot be verified against the unseen target");
						return;
					}

					var selectedIds = selected.Select(a => a.ActorID).ToHashSet();
					var dropped = expectedIds.Where(id => !selectedIds.Contains(id)).OrderBy(id => id).ToArray();
					foreach (var id in dropped)
					{
						raidPreStrikeDroppedActorIds.Add(id);
						var droppedAircraft = combatIntelService.OwnedActors.FirstOrDefault(a => a.ActorID == id && IsManagedAircraft(a) && a.IsInWorld && !a.IsDead);
						if (droppedAircraft == null || raidRecoverySince.ContainsKey(droppedAircraft))
							continue;
						QueueStopOrder(bot, droppedAircraft);
						if (!HasFullRaidAmmo(droppedAircraft))
							QueueReturnToBase(bot, droppedAircraft, true);
					}
					FransBotLog.BotDebug(world,
						"{0}: Air RAID {1} gracefully degrades pre-strike group after readiness change: drops [{2}], keeps {3} full-ready aircraft with verified sortie damage {4}/{5}. Mission ownership and target remain unchanged; the ready subset continues instead of forcing a full re-bid.",
						player, mission.TargetActorId, string.Join(",", dropped), selected.Length, remainingContribution, required);
				}
			}
			else
			{
				// After the first progressive STRIKE, decreasing ammo is sortie progress, not a
				// readiness failure. Preserve the surviving post-degradation committed subset
				// for casualty detection, but do not require HasFullRaidAmmo again.
				var committedLive = ResolveCommittedAirActors(mission);
				var expectedLiveCount = (mission.CommittedActorIds ?? Array.Empty<uint>())
					.Count(id => !raidPreStrikeDroppedActorIds.Contains(id));
				if (committedLive.Length != expectedLiveCount || committedLive.Length == 0)
				{
					CloseRaid(bot, "committed Air RAID aircraft was lost during the strike", true);
					return;
				}

				selected = committedLive.Where(a => !raidRecoverySince.ContainsKey(a)).ToArray();
			}

			// The winning bid still supplies the original required target damage. Air may
			// discard unavailable aircraft only after proving the surviving ready subset still
			// meets that same requirement; target HP itself is never live-repriced downward.
			if (changed)
			{
				activeMissionType = FransMissionType.Raid;
				activeTargetActorId = mission.TargetActorId;
				activeObjective = visibleTarget ? target.Location : mission.LastVisibleTargetCell;
				activeOrder = FransCommanderOrder.Move;
				activeOrderStartedWorldTick = world.WorldTick;
				raidStrikeIssued = false;
				ResetRaidLostTargetConfirmation(false);
				ResetRaidStrikeAmmoProgress();
				ResetRaidApproachProgress();
				raidLastRiskRevision = -1;
				raidLastRiskObjective = activeObjective;
				raidCommittedCriticalRiskSinceTick = -1;
				activeAircraft.Clear();
				raidMissionOrigins.Clear();
				foreach (var a in selected)
				{
					activeAircraft.Add(a);
					raidMissionOrigins[a] = a.Location;
					if (visibleTarget)
					{
						var contribution = commanderCoreService.EstimateRaidContribution(FransCommanderKind.Air, a, target);
						if (contribution > 0)
							raidCommittedContributionByActor[a.ActorID] = contribution;
					}
				}
				ResetRaidApproachProgress(visibleTarget ? target : null);
				RefreshTransientReservations();
				FransBotLog.BotDebug(world,
					visibleTarget
						? "{0}: Air Commander accepts precision RAID {1} {2}: exact {3} aircraft [{4}], current required HP {5}, estimated full-sortie ammo damage {6}. Native Move approaches the exact target; each committed aircraft begins the immutable-target strike as soon as that aircraft reaches valid weapon range."
						: "{0}: Air Commander accepts precision RAID {1} {2}: exact {3} aircraft [{4}], strike snapshot {6}/{5}. Target is currently unseen; aircraft make one confirmation pass to LastVisibleTargetCell and return to service + ANCHOR if the exact target is not reacquired.",
					player, mission.TargetActorType, mission.TargetActorId, activeAircraft.Count,
					string.Join(",", activeAircraft.OrderBy(a => a.ActorID).Select(a => a.ActorID)), required, damage);
			}
			else
				activeAircraft.RemoveWhere(a => !selected.Contains(a));

			if (!raidStrikeIssued)
			{
				if (activeAircraft.Count == 0 || activeAircraft.Any(a => !HasFullRaidAmmo(a)))
				{
					CloseRaid(bot, "RAID aircraft lost readiness before STRIKE NOW", true);
					return;
				}
			}
			else
			{
				// Each aircraft owns its sortie until its usable ammo is actually gone. Empty
				// aircraft peel off into the existing full-ammo recovery path while armed
				// wingmates continue the same immutable mission.
				foreach (var spent in activeAircraft.Where(a => !HasAmmo(a)).OrderBy(a => a.ActorID).ToArray())
					StartRaidAircraftRecovery(bot, spent, "full-sortie ammo exhausted after STRIKE NOW");

				if (activeAircraft.Count == 0)
				{
					commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, "RAID full sortie ammo exhausted");
					FransBotLog.BotDebug(world,
						"{0}: Air RAID full sortie on target {1} is complete: every surviving committed aircraft exhausted its usable ammo and is now in native ReturnToBase/rearm recovery.",
						player, mission.TargetActorId);
					ResetMission();
					return;
				}
			}

			if (activeOrder == FransCommanderOrder.Fight)
			{
				var localThreat = FindImmediateAirRaidCombatThreat();
				if (localThreat != null)
				{
					ExecuteFightMicro(bot, visibleTarget ? target : null);
					return;
				}

				activeOrder = FransCommanderOrder.Move;
				activeOrderStartedWorldTick = world.WorldTick;
				lostContactSinceWorldTick = -1;
				FransBotLog.BotDebug(world,
					"{0}: Air RAID LOCAL FIGHT clear; no immediate attackable combat threat remains, so the same RAID resumes its immutable target without rebid/recovery.",
					player);
			}

			activeObjective = visibleTarget ? target.Location : mission.LastVisibleTargetCell;
			if (!raidStrikeIssued && (raidCommittedCriticalRiskSinceTick >= 0 ||
				raidLastRiskRevision != riskModelService.RiskRevision || raidLastRiskObjective != activeObjective))
			{
				raidLastRiskRevision = riskModelService.RiskRevision;
				raidLastRiskObjective = activeObjective;
				var knownAaZones = GetKnownAntiAirZones();
				var committedHardRisk = false;
				var committedHardPeak = 0;
				var committedHardPeakCell = activeObjective;
				foreach (var a in activeAircraft.OrderBy(a => a.ActorID))
				{
					if (!TryBuildKnownAntiAirSafePath(a.Location, activeObjective, knownAaZones, out var safePath))
					{
						foreach (var aircraft in activeAircraft.Where(x => x != null && x.IsInWorld && !x.IsDead))
							QueueStopOrder(bot, aircraft);
						ReleaseRaidForRebid(bot, mission.TargetActorId,
							$"known SAM/AA exclusion blocks precision RAID PathMove to {activeObjective}");
						return;
					}

					var route = EvaluateAirPathRisk(a, safePath);
					if (!route.IsCritical || route.PeakScore < Info.RaidCommittedRiskAbortScore)
						continue;

					committedHardRisk = true;
					if (route.PeakScore > committedHardPeak)
					{
						committedHardPeak = route.PeakScore;
						committedHardPeakCell = route.PeakCell;
					}
				}

				if (!committedHardRisk)
					raidCommittedCriticalRiskSinceTick = -1;
				else
				{
					if (raidCommittedCriticalRiskSinceTick < 0)
					{
						raidCommittedCriticalRiskSinceTick = world.WorldTick;
						FransBotLog.BotDebug(world,
							"{0}: Air RAID keeps commitment through a new high-risk pre-strike route at peak {1} ({2}); abort requires {3} sustained WT at/above score {4}. Known SAM/AA exclusion remains immediate.",
							player, committedHardPeak, committedHardPeakCell, Info.RaidCommittedRiskAbortHoldTicks, Info.RaidCommittedRiskAbortScore);
					}

					var heldFor = world.WorldTick - raidCommittedCriticalRiskSinceTick;
					if (heldFor >= Info.RaidCommittedRiskAbortHoldTicks)
					{
						foreach (var aircraft in activeAircraft.Where(x => x != null && x.IsInWorld && !x.IsDead))
							QueueStopOrder(bot, aircraft);
						ReleaseRaidForRebid(bot, mission.TargetActorId,
							$"committed AA-safe route remained at/above risk {Info.RaidCommittedRiskAbortScore} for {heldFor} WT; peak {committedHardPeak} at {committedHardPeakCell}");
						return;
					}
				}
			}

			if (!visibleTarget)
			{
				ExecuteLostRaidTargetConfirmation(bot, mission);
				return;
			}

			if (raidLostTargetConfirmationState == RaidLostTargetConfirmationState.Active)
			{
				foreach (var a in activeAircraft.Where(a => a != null && a.IsInWorld && !a.IsDead))
					QueueStopOrder(bot, a);
				raidLostTargetConfirmationState = RaidLostTargetConfirmationState.Consumed;
				ResetRaidApproachProgress(target);
				if (raidStrikeIssued)
				{
					ResetRaidStrikeAmmoProgress(activeAircraft);
					FransBotLog.BotDebug(world,
						"{0}: Air RAID reacquires exact target {1} during the one-pass confirmation; progressive immutable-target strike resumes with surviving remaining ammo.",
						player, mission.TargetActorId);
				}
				else
					FransBotLog.BotDebug(world,
						"{0}: Air RAID reacquires exact target {1} during the one-pass confirmation; pre-strike approach resumes without resetting mission ownership.",
						player, mission.TargetActorId);
			}

			var knownAaZonesAtTarget = GetKnownAntiAirZones();
			if (!IsCellOutsideKnownAntiAir(target.Location, knownAaZonesAtTarget))
			{
				ReleaseRaidForRebid(bot, mission.TargetActorId,
					$"exact target {target.Info.Name} {target.ActorID} lies inside known SAM/AA exclusion radius {Info.KnownAntiAirPathSafetyRadius}");
				return;
			}

			var armedAttackable = activeAircraft
				.Where(a => HasAmmo(a) && CanAttackActor(a, target))
				.OrderBy(a => a.ActorID)
				.ToArray();
			if (armedAttackable.Length == 0)
			{
				CloseRaid(bot, "visible exact target is no longer attackable by the remaining committed Air strike", false);
				return;
			}

			// Native Attack is authorized only when the current attack corridor itself respects the
			// hard known-AA exclusion. Otherwise that aircraft keeps using safe plain-Move waypoints.
			var inRange = armedAttackable
				.Where(a => IsTargetWithinWeaponRange(a, target) && IsAirAttackCorridorKnownAaSafe(a, target, knownAaZonesAtTarget))
				.ToArray();
			var inRangeIds = inRange.Select(a => a.ActorID).ToHashSet();
			var approaching = armedAttackable.Where(a => !inRangeIds.Contains(a.ActorID)).ToArray();
			var approachProgress = ObserveRaidApproachProgress(target, approaching);

			if (!raidStrikeIssued)
			{
				if (inRange.Length == 0)
				{
					var stalledFor = raidApproachLastProgressWorldTick < 0 ? 0 : world.WorldTick - raidApproachLastProgressWorldTick;
					if (stalledFor >= Info.RaidPreStrikeProgressWatchdogTicks)
					{
						FransBotLog.BotDebug(world,
							"{0}: Air RAID pre-STRIKE watchdog on target {1}: {2} committed aircraft made no closer approach for {3} WT; mission ends into normal service recovery instead of remaining bound indefinitely.",
							player, mission.TargetActorId, approaching.Length, stalledFor);
						CloseRaid(bot, $"pre-STRIKE approach made no progress for {stalledFor} WT", false);
						return;
					}

					foreach (var a in approaching)
						if (!QueueMove(bot, a, activeObjective, false))
						{
							ReleaseRaidForRebid(bot, mission.TargetActorId, "known SAM/AA exclusion blocks remaining pre-STRIKE approach");
							return;
						}
					return;
				}

				foreach (var a in inRange)
					QueueAttack(bot, a, target, true);
				foreach (var a in approaching)
					if (!QueueMove(bot, a, activeObjective, false))
					{
						ReleaseRaidForRebid(bot, mission.TargetActorId, "known SAM/AA exclusion blocks progressive STRIKE approach");
						return;
					}
				raidStrikeIssued = true;
				ResetRaidStrikeAmmoProgress(activeAircraft);
				ResetRaidApproachProgress(target, approaching);
				FransBotLog.BotDebug(world,
					"{0}: Air RAID STRIKE NOW on {1} {2}: {3}/{4} committed aircraft are in valid weapon range and begin the progressive immutable-target strike; {5} continue native Move approach. Estimated full-sortie ammo damage {6}/{7}.",
					player, target.Info.Name, target.ActorID, inRange.Length, activeAircraft.Count, approaching.Length, damage, required);
				return;
			}

			if (!TrackRaidStrikeAmmoProgress(bot, mission.TargetActorId, approachProgress))
				return;

			foreach (var a in inRange)
				QueueAttack(bot, a, target, false);
			foreach (var a in approaching)
				if (!QueueMove(bot, a, activeObjective, false))
				{
					ReleaseRaidForRebid(bot, mission.TargetActorId, "known SAM/AA exclusion blocks post-STRIKE approach");
					return;
				}
		}

		void ExecuteLostRaidTargetConfirmation(IBot bot, FransActiveMission mission)
		{
			activeObjective = mission.LastVisibleTargetCell;
			if (raidLostTargetConfirmationState == RaidLostTargetConfirmationState.Consumed)
			{
				CloseRaid(bot, "exact target lost again after the accepted RAID consumed its one-pass confirmation", false);
				return;
			}

			var center = GetGroupCenter(activeAircraft);

			if (raidLostTargetConfirmationState == RaidLostTargetConfirmationState.Available)
			{
				raidLostTargetConfirmationState = RaidLostTargetConfirmationState.Active;
				ResetRaidApproachProgress();
				activeOrder = FransCommanderOrder.Move;
				activeOrderStartedWorldTick = world.WorldTick;
				// A lost exact target is not a scouting assignment. Cancel any stale native Attack
				// and make exactly one confirmation pass through the last legitimately observed cell.
				foreach (var a in activeAircraft.Where(a => a != null && a.IsInWorld && !a.IsDead).OrderBy(a => a.ActorID))
				{
					QueueStopOrder(bot, a);
					if (!QueueMove(bot, a, activeObjective, true))
					{
						ReleaseRaidForRebid(bot, mission.TargetActorId, "known SAM/AA exclusion blocks lost-target confirmation pass");
						return;
					}
				}
				FransBotLog.BotDebug(world,
					"{0}: Air RAID exact target {1} is gone/unseen; begins ONE-PASS confirmation to LastVisibleTargetCell {2}. No spiral/search waypoints are generated.",
					player, mission.TargetActorId, activeObjective);
				return;
			}

			// While the one native Move is still making physical progress, Commander stays silent.
			// If an aircraft idles early outside the confirmation radius, retry only the same
			// LastVisibleTargetCell; this can never become a search spiral.
			if ((center - activeObjective).LengthSquared > 16)
			{
				foreach (var a in activeAircraft.OrderBy(a => a.ActorID))
					if (!QueueMove(bot, a, activeObjective, false))
					{
						ReleaseRaidForRebid(bot, mission.TargetActorId, "known SAM/AA exclusion blocks lost-target confirmation retry");
						return;
					}
				return;
			}

			CloseRaid(bot, "exact target not reacquired during one-pass LastVisibleTargetCell confirmation", false);
		}

		void ResetRaidLostTargetConfirmation(bool cancelActivities)
		{
			if (cancelActivities)
				foreach (var a in activeAircraft.Where(a => a != null && a.IsInWorld && !a.IsDead))
					QueueStopOrder(null, a);
			raidLostTargetConfirmationState = RaidLostTargetConfirmationState.Available;
		}

		void ResetRaidApproachProgress(Actor target = null, IEnumerable<Actor> approaching = null)
		{
			if (target == null || !target.IsInWorld || target.IsDead)
			{
				raidApproachBestOutOfRangeCount = int.MaxValue;
				raidApproachBestMaxDistanceCells = int.MaxValue;
				raidApproachLastProgressWorldTick = -1;
				return;
			}

			var units = (approaching ?? activeAircraft.Where(a => HasAmmo(a) && CanAttackActor(a, target) && !IsTargetWithinWeaponRange(a, target)))
				.Where(a => a != null && a.IsInWorld && !a.IsDead)
				.ToArray();
			raidApproachBestOutOfRangeCount = units.Length;
			raidApproachBestMaxDistanceCells = units.Length == 0 ? 0 : units.Max(a => RaidCellDistance(a.Location, target.Location));
			raidApproachLastProgressWorldTick = world.WorldTick;
		}

		bool ObserveRaidApproachProgress(Actor target, IReadOnlyCollection<Actor> approaching)
		{
			if (target == null || !target.IsInWorld || target.IsDead)
				return false;

			var live = approaching.Where(a => a != null && a.IsInWorld && !a.IsDead).ToArray();
			var count = live.Length;
			var maxDistance = count == 0 ? 0 : live.Max(a => RaidCellDistance(a.Location, target.Location));
			if (raidApproachLastProgressWorldTick < 0 || raidApproachBestOutOfRangeCount == int.MaxValue)
			{
				raidApproachBestOutOfRangeCount = count;
				raidApproachBestMaxDistanceCells = maxDistance;
				raidApproachLastProgressWorldTick = world.WorldTick;
				return true;
			}

			var progressed = count < raidApproachBestOutOfRangeCount ||
				(count == raidApproachBestOutOfRangeCount && maxDistance < raidApproachBestMaxDistanceCells);
			if (!progressed)
				return false;

			raidApproachBestOutOfRangeCount = count;
			raidApproachBestMaxDistanceCells = maxDistance;
			raidApproachLastProgressWorldTick = world.WorldTick;
			return true;
		}

		static int RaidCellDistance(CPos from, CPos to)
		{
			return Math.Max(Math.Abs(from.X - to.X), Math.Abs(from.Y - to.Y));
		}

		int GetRaidAmmoCount(IEnumerable<Actor> aircraft)
		{
			long total = 0;
			var sawPool = false;
			foreach (var a in aircraft.Where(a => a != null && a.IsInWorld && !a.IsDead))
				foreach (var pool in a.TraitsImplementing<AmmoPool>())
				{
					sawPool = true;
					total += Math.Max(0, pool.CurrentAmmoCount);
				}
			return sawPool ? (int)Math.Clamp(total, 0L, int.MaxValue) : -1;
		}

		void ResetRaidStrikeAmmoProgress(IEnumerable<Actor> aircraft = null)
		{
			raidStrikeLastObservedAmmo = aircraft == null ? -1 : GetRaidAmmoCount(aircraft);
			raidStrikeLastAmmoProgressWorldTick = aircraft == null ? -1 : world.WorldTick;
		}

		bool TrackRaidStrikeAmmoProgress(IBot bot, uint targetId, bool approachProgress)
		{
			var ammo = GetRaidAmmoCount(activeAircraft);
			// Aircraft without AmmoPool are outside the current Red Alert managed-aircraft set.
			// Keep native ownership if such a future unit appears rather than inventing a false stall.
			if (ammo < 0)
				return true;

			if (approachProgress)
				raidStrikeLastAmmoProgressWorldTick = world.WorldTick;

			if (raidStrikeLastObservedAmmo < 0 || ammo != raidStrikeLastObservedAmmo)
			{
				if (raidStrikeLastObservedAmmo < 0 || ammo < raidStrikeLastObservedAmmo)
					raidStrikeLastAmmoProgressWorldTick = world.WorldTick;
				else
					// An increase is unexpected during an active strike, but it is still real progress/state
					// change and must not immediately trip the watchdog.
					raidStrikeLastAmmoProgressWorldTick = world.WorldTick;
				raidStrikeLastObservedAmmo = ammo;
			}

			if (raidStrikeLastAmmoProgressWorldTick < 0)
			{
				raidStrikeLastAmmoProgressWorldTick = world.WorldTick;
				raidStrikeLastObservedAmmo = ammo;
				return true;
			}

			var stalledFor = world.WorldTick - raidStrikeLastAmmoProgressWorldTick;
			if (stalledFor < Info.RaidStrikeAmmoProgressWatchdogTicks)
				return true;

			FransBotLog.BotDebug(world,
				"{0}: Air RAID post-STRIKE watchdog on target {1}: usable ammo stayed at {2} and no remaining aircraft improved its approach for {3} WT; strike is stalled, so the mission ends into normal service recovery instead of circling indefinitely.",
				player, targetId, ammo, stalledFor);
			CloseRaid(bot, $"post-STRIKE strike/approach made no progress for {stalledFor} WT", false);
			return false;
		}

		void ReleaseRaidForRebid(IBot bot, uint targetId, string reason)
		{
			commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, $"RAID RETREAT/re-bid: {reason}");
			if (targetId != 0)
				generalService.ReportRaidRetreat(targetId, $"Air RAID: {reason}");
			if (activeMissionType == FransMissionType.Raid && activeTargetActorId == targetId)
				StartRaidRecovery(bot, $"RAID RETREAT/re-bid: {reason}");
			ResetMission();
		}

		void CloseRaid(IBot bot, string reason, bool reportRetreat)
		{
			var targetId = activeTargetActorId;
			if (targetId != 0)
				commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, $"RAID ends: {reason}");
			if (reportRetreat && targetId != 0)
				generalService.ReportRaidRetreat(targetId, $"Air RAID: {reason}");
			if (reportRetreat)
				StartRaidRecovery(bot, reason);
			else
				StartRaidAttackMoveReturn(bot, reason);
			ResetMission();
		}

		void StartRaidAircraftRecovery(IBot bot, Actor aircraft, string reason)
		{
			if (aircraft == null || !aircraft.IsInWorld || aircraft.IsDead || raidRecoverySince.ContainsKey(aircraft))
				return;

			raidAttackMoveHomeActors.Remove(aircraft);
			raidRecoverySince[aircraft] = world.WorldTick;
			if (hasMissionAnchorPoint)
				raidRecoveryAnchors[aircraft] = missionAnchorPoint;
			var recoveryAnchor = raidRecoveryAnchors.TryGetValue(aircraft, out var savedAnchor) ? savedAnchor : aircraft.Location;
			ObserveRecoveryProgress(aircraft, recoveryAnchor, requireFullAmmo: true, initialize: true);
			QueueStopOrder(bot, aircraft);
			RouteAirServiceUnit(bot, aircraft, requireFullAmmo: true, watchdog: false);
			activeAircraft.Remove(aircraft);
			RefreshTransientReservations();
			FransBotLog.BotDebug(world,
				"{0}: Air RAID aircraft {1} leaves the active strike for normal native Repair/ReturnToBase service: {2}.",
				player, aircraft, reason);
		}

		void StartRaidAttackMoveReturn(IBot bot, string reason)
		{
			var returning = activeAircraft.Where(a => a != null && a.IsInWorld && !a.IsDead).OrderBy(a => a.ActorID).ToArray();
			if (returning.Length == 0)
				return;

			foreach (var a in returning)
			{
				var origin = raidMissionOrigins.TryGetValue(a, out var saved) ? saved : a.Location;
				raidRecoverySince[a] = world.WorldTick;
				raidRecoveryAnchors[a] = origin;
				ObserveRecoveryProgress(a, origin, requireFullAmmo: false, initialize: true);
				QueueStopOrder(bot, a);
				if (HasAmmo(a))
				{
					raidAttackMoveHomeActors.Add(a);
					QueueAttackMove(bot, a, origin, true);
				}
				else
				{
					raidAttackMoveHomeActors.Remove(a);
					RouteAirServiceUnit(bot, a, requireFullAmmo: true, watchdog: false);
				}
			}

			RefreshTransientReservations();
			FransBotLog.BotDebug(world,
				"{0}: Air RAID normal completion sends {1} surviving aircraft toward their individual RAID origin cells; aircraft with usable ammo use native AttackMove so remaining ammo may be spent en route, while empty aircraft go directly to native service: {2}.",
				player, returning.Length, reason);
			raidMissionOrigins.Clear();
		}

		void StartRaidRecovery(IBot bot, string reason)
		{
			var recovering = activeAircraft.Where(a => a != null && a.IsInWorld && !a.IsDead).OrderBy(a => a.ActorID).ToArray();
			if (recovering.Length == 0)
				return;

			foreach (var a in recovering)
			{
				raidAttackMoveHomeActors.Remove(a);
				raidRecoverySince[a] = world.WorldTick;
				if (hasMissionAnchorPoint)
					raidRecoveryAnchors[a] = missionAnchorPoint;
				var recoveryAnchor = raidRecoveryAnchors.TryGetValue(a, out var savedAnchor) ? savedAnchor : a.Location;
				ObserveRecoveryProgress(a, recoveryAnchor, requireFullAmmo: true, initialize: true);
				QueueStopOrder(bot, a);
				RouteAirServiceUnit(bot, a, requireFullAmmo: true, watchdog: false);
			}

			RefreshTransientReservations();
			FransBotLog.BotDebug(world,
				"{0}: Air RAID recovery routes {1} aircraft through normal native Repair/ReturnToBase service: {2}.",
				player, recovering.Length, reason);
			raidMissionOrigins.Clear();
		}

		void MaintainRaidRecovery(IBot bot, IReadOnlyCollection<Actor> aircraft)
		{
			foreach (var a in raidRecoverySince.Keys.OrderBy(a => a.ActorID).ToArray())
			{
				if (a == null || !a.IsInWorld || a.IsDead || !aircraft.Contains(a))
				{
					raidRecoverySince.Remove(a);
					raidRecoveryAnchors.Remove(a);
					raidAttackMoveHomeActors.Remove(a);
					RemoveRecoveryProgressTracking(a);
					continue;
				}

				if (raidAttackMoveHomeActors.Contains(a))
				{
					var origin = raidRecoveryAnchors.TryGetValue(a, out var saved) ? saved : a.Location;
					ObserveRecoveryProgress(a, origin, requireFullAmmo: false, initialize: false);
					var returnWatchdog = RecoveryWatchdogDue(a);
					if (HasAmmo(a) && (a.Location - origin).LengthSquared > 4)
					{
						if (returnWatchdog && !a.IsIdle)
							QueueStopOrder(bot, a);
						QueueAttackMove(bot, a, origin, returnWatchdog);
						if (returnWatchdog)
							MarkRecoveryWatchdogReissue(a, "RAID AttackMove return toward sortie origin");
						continue;
					}
					raidAttackMoveHomeActors.Remove(a);
					ObserveRecoveryProgress(a, origin, requireFullAmmo: true, initialize: true);
				}

				var recoveryAnchor = raidRecoveryAnchors.TryGetValue(a, out var savedAnchor) ? savedAnchor : a.Location;
				ObserveRecoveryProgress(a, recoveryAnchor, requireFullAmmo: true, initialize: false);
				var watchdog = RecoveryWatchdogDue(a);

				if (IsRaidServiceReady(a, raidRecoverySince[a]))
				{
					if ((a.Location - recoveryAnchor).LengthSquared > 4)
					{
						if (watchdog && !a.IsIdle)
							QueueStopOrder(bot, a);
						QueueMove(bot, a, recoveryAnchor, watchdog);
						if (watchdog)
							MarkRecoveryWatchdogReissue(a, "RAID recovery ANCHOR regroup Move");
						continue;
					}
					raidRecoverySince.Remove(a);
					raidRecoveryAnchors.Remove(a);
					raidAttackMoveHomeActors.Remove(a);
					RemoveRecoveryProgressTracking(a);
					continue;
				}

				RouteAirServiceUnit(bot, a, requireFullAmmo: true, watchdog: watchdog);
			}
			RefreshTransientReservations();
		}

		bool IsTargetWithinWeaponRange(Actor attacker, Actor target)
		{
			if (!CanAttackActor(attacker, target))
				return false;
			var attackTarget = Target.FromActor(target);
			var distance = (target.CenterPosition - attacker.CenterPosition).HorizontalLength;
			foreach (var attack in attacker.TraitsImplementing<AttackBase>())
			{
				if (attack.IsTraitDisabled || attack.IsTraitPaused)
					continue;
				foreach (var armament in attack.Armaments)
					if (!armament.IsTraitDisabled && !armament.IsTraitPaused && armament.Weapon.IsValidAgainst(attackTarget, world, attacker) &&
						distance <= armament.MaxRange().Length && (armament.Weapon.MinRange == WDist.Zero || distance > armament.Weapon.MinRange.Length))
						return true;
			}
			return false;
		}

		bool ShouldEnterFight(Actor target)
		{
			var radiusSq = Info.FightTriggerRadius * Info.FightTriggerRadius;
			var knownAaZones = GetKnownAntiAirZones();
			return activeAircraft.Any(a => CanAttackActor(a, target) &&
				(a.Location - target.Location).LengthSquared <= radiusSq &&
				IsAirAttackCorridorKnownAaSafe(a, target, knownAaZones));
		}

		Actor FindImmediateAirRaidCombatThreat()
		{
			var radiusSq = Info.FightMicroRadius * Info.FightMicroRadius;
			var knownAaZones = GetKnownAntiAirZones();
			return combatIntelService.VisibleEnemies
				.Where(IsVisibleEnemy)
				.Where(combatIntelService.IsTacticalCombatThreat)
				.Where(enemy => activeAircraft.Any(a => a != null && a.IsInWorld && !a.IsDead && HasAmmo(a) &&
					(enemy.Location - a.Location).LengthSquared <= radiusSq && CanAttackActor(a, enemy) &&
					IsAirAttackCorridorKnownAaSafe(a, enemy, knownAaZones)))
				.OrderByDescending(GetCombatValue)
				.ThenBy(enemy => activeAircraft.Min(a => (enemy.Location - a.Location).LengthSquared))
				.ThenBy(enemy => enemy.ActorID)
				.FirstOrDefault();
		}

		void ExecuteFightMicro(IBot bot, Actor missionTarget)
		{
			// FIGHT ignores ordinary RiskModel price, but the known SAM/AA path exclusion remains hard.
			var visible = combatIntelService.VisibleEnemies.Where(IsVisibleEnemy).ToArray();
			var knownAaZones = GetKnownAntiAirZones();
			var radiusSq = Info.FightMicroRadius * Info.FightMicroRadius;
			foreach (var aircraft in activeAircraft.OrderBy(a => a.ActorID))
			{
				if (!HasAmmo(aircraft))
				{
					QueueReturnToBase(bot, aircraft);
					continue;
				}

				var combatThreat = visible
					.Where(combatIntelService.IsTacticalCombatThreat)
					.Where(enemy => (enemy.Location - aircraft.Location).LengthSquared <= radiusSq && CanAttackActor(aircraft, enemy))
					.Where(enemy => IsAirAttackCorridorKnownAaSafe(aircraft, enemy, knownAaZones))
					.OrderBy(enemy => (enemy.Location - aircraft.Location).LengthSquared)
					.ThenBy(enemy => enemy.ActorID)
					.FirstOrDefault();
				var chosen = combatThreat ?? (missionTarget != null && IsVisibleEnemy(missionTarget) && CanAttackActor(aircraft, missionTarget) &&
					IsAirAttackCorridorKnownAaSafe(aircraft, missionTarget, knownAaZones)
					? missionTarget
					: visible.Where(enemy => CanAttackActor(aircraft, enemy) && (enemy.Location - aircraft.Location).LengthSquared <= radiusSq)
						.Where(enemy => IsAirAttackCorridorKnownAaSafe(aircraft, enemy, knownAaZones))
						.OrderBy(enemy => (enemy.Location - aircraft.Location).LengthSquared).ThenBy(enemy => enemy.ActorID).FirstOrDefault());
				if (chosen != null)
					QueueAttack(bot, aircraft, chosen, false);
			}
		}

		void ResetPioneerReconProgress(Actor actor, CPos objective)
		{
			reconPioneerBestDistanceSquared = actor == null ? int.MaxValue : (actor.Location - objective).LengthSquared;
			reconPioneerLastProgressWorldTick = world.WorldTick;
		}

		bool PioneerReconProgressTimedOut(Actor actor, CPos objective)
		{
			if (!reconPioneerValidationActive || actor == null || !actor.IsInWorld || actor.IsDead)
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

		void ExecuteReconMission(IBot bot, IReadOnlyCollection<Actor> ready, FransActiveMission mission)
		{
			var changed = activeTargetActorId != mission.TargetActorId || activeMissionType != FransMissionType.Recon;
			if (changed)
			{
				ResetReconState();
				if (mission.CommittedActorIds == null || mission.CommittedActorIds.Length != 1)
				{
					AbortReconMission("winning Air RECON bid did not contain exactly one committed actor");
					return;
				}

				var selectedId = mission.CommittedActorIds[0];
				var selected = ready.FirstOrDefault(a => a.ActorID == selectedId &&
					a != reconRetreatActor && a.TraitOrDefault<Cargo>() == null);
				if (selected == null)
				{
					AbortReconMission("selected Air recon unit is no longer available");
					return;
				}

				activeTargetActorId = mission.TargetActorId;
				activeMissionType = FransMissionType.Recon;
				activeObjective = mission.LastVisibleTargetCell;
				activeOrder = FransCommanderOrder.Move;
				activeOrderStartedWorldTick = world.WorldTick;
				activeAircraft.Clear();
				activeAircraft.Add(selected);
				reconActor = selected;
				QueueSetUnitStanceOrder(bot, selected, UnitStance.HoldFire);
				reconOrigin = selected.Location;
				reconStart = mission.LastVisibleTargetCell;
				reconPioneerValidationActive = false;
				if (expansionStateService != null &&
					expansionStateService.TryGetPioneerReconObjectiveNear(reconStart, out var pioneerObjective))
				{
					reconPioneerValidationActive = true;
					reconStart = pioneerObjective;
					activeObjective = pioneerObjective;
					ResetPioneerReconProgress(selected, activeObjective);
				}
				hasReconSearchWaypoint = false;
				reconLoggedContactIds.Clear();
				FransBotLog.BotDebug(world,
					"{0}: Air Commander accepts persistent RECON MineCluster {1} with ONE {2} {3}; plain MOVE from {4} to patrol start {5}. The mission has no coverage-completion threshold.",
					player, mission.TargetActorId, selected.Info.Name, selected.ActorID, reconOrigin, reconStart);
			}

			if (reconActor == null || !reconActor.IsInWorld || reconActor.IsDead || !IsManagedAircraft(reconActor))
			{
				AbortReconMission("Air recon unit died or left Commander ownership");
				return;
			}

			if (expansionStateService != null && expansionStateService.TryGetPioneerReconObjectiveNear(activeObjective, out var exactPioneerObjective))
			{
				var pioneerWasActive = reconPioneerValidationActive;
				reconPioneerValidationActive = true;
				if (exactPioneerObjective != activeObjective)
				{
					activeObjective = exactPioneerObjective;
					reconStart = exactPioneerObjective;
					ResetPioneerReconProgress(reconActor, activeObjective);
					activeOrder = FransCommanderOrder.Move;
					hasReconSearchWaypoint = false;
					QueueStopOrder(bot, reconActor);
					FransBotLog.BotDebug(world, "{0}: Air RECON {1} redirects to PIONEER exact objective {2}; persistent probing is temporarily superseded until the exact ore cell is scout-cleared.", player, activeTargetActorId, activeObjective);
				}
				else if (!pioneerWasActive)
					ResetPioneerReconProgress(reconActor, activeObjective);
			}
			else if (reconPioneerValidationActive)
			{
				commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, "PIONEER exact-objective RECON completed");
				FransBotLog.BotDebug(world, "{0}: Air PIONEER exact-objective RECON {1} completed at {2}; releases the one-shot validation mission and returns the aircraft to normal ownership.", player, activeTargetActorId, activeObjective);
				ResetMission();
				return;
			}

			if (PioneerReconProgressTimedOut(reconActor, activeObjective))
			{
				AbortReconMission($"PIONEER exact-objective RECON made no approach progress for {PioneerReconNoProgressTimeoutTicks} WT; release for another capability");
				return;
			}

			if (ReconHealthBelowRetreatThreshold(reconActor, out var healthPercent))
			{
				BeginReconRetreat(bot, reconActor,
					$"health fell to {healthPercent}% (< {commanderCoreService.ReconRetreatHealthPercent}%)");
				return;
			}

			if (!ready.Contains(reconActor))
			{
				AbortReconMission("Air recon unit became unavailable for persistent probing");
				return;
			}

			if (activeOrder == FransCommanderOrder.Move)
			{
				if ((reconActor.Location - reconStart).LengthSquared <= 1)
				{
					var vision = commanderCoreService.GetReconVisionCells(reconActor);
					if (vision <= 0)
					{
						AbortReconMission("Air recon unit lost usable vision before patrol start");
						return;
					}

					reconSearchSpiral.Reset(reconStart, vision);
					activeOrder = FransCommanderOrder.Search;
					activeOrderStartedWorldTick = world.WorldTick;
					hasReconSearchWaypoint = false;
					FransBotLog.BotDebug(world,
						"{0}: Air RECON {1} begins persistent probing at {2}: vision {3}, spiral spacing {4}, {5} queued plain-Move waypoints per packet. No coverage state is tracked.",
						player, activeTargetActorId, reconStart, vision, reconSearchSpiral.SpacingCells,
						commanderCoreService.ReconWaypointBatchSize);
				}
				else if (!QueueMove(bot, reconActor, reconStart, false))
				{
					AbortReconMission("known SAM/AA exclusion blocks patrol start PathMove");
					return;
				}
				return;
			}

			if (activeOrder != FransCommanderOrder.Search)
				return;

			if (TryGetReconContact(reconActor, out var contact) && reconLoggedContactIds.Add(contact.ActorID))
				FransBotLog.BotDebug(world,
					"{0}: Air RECON MineCluster {1} sees incidental enemy {2} {3} at {4}; plain-Move probing continues and RECON never attacks the contact.",
					player, activeTargetActorId, contact.Info.Name, contact.ActorID, contact.Location);

			// While the current native queue still has movement work, Commander deliberately stays silent.
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

			AbortReconMission("persistent Air RECON has no legal spiral waypoint");
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

		bool TryQueueReconWaypointPacket(IBot bot, Actor aircraft)
		{
			var knownAaZones = GetKnownAntiAirZones();
			var queuedPath = new List<CPos>();
			var cursor = aircraft.Location;
			var finalPatrolWaypoint = default(CPos);
			var haveFinal = false;
			for (var i = 0; i < commanderCoreService.ReconWaypointBatchSize; i++)
			{
				if (!reconSearchSpiral.TryGetNextWaypoint(world,
					c => world.Map.Contains(c) && IsCellOutsideKnownAntiAir(c, knownAaZones) ? c : (CPos?)null,
					cursor, out var waypoint))
					break;
				if (!TryBuildKnownAntiAirSafePath(cursor, waypoint, knownAaZones, out var safeSegment))
					continue;
				foreach (var safeWaypoint in safeSegment)
					if (queuedPath.Count == 0 || queuedPath[^1] != safeWaypoint)
						queuedPath.Add(safeWaypoint);
				cursor = waypoint;
				finalPatrolWaypoint = waypoint;
				haveFinal = true;
			}

			if (!haveFinal || queuedPath.Count == 0)
				return false;

			for (var i = 0; i < queuedPath.Count; i++)
				bot.QueueOrder(new Order("Move", aircraft, Target.FromCell(world, queuedPath[i]), i > 0));

			reconSearchWaypoint = finalPatrolWaypoint;
			hasReconSearchWaypoint = true;
			lastMoveDestination[aircraft] = reconSearchWaypoint;
			lastMoveWorldTick[aircraft] = world.WorldTick;
			lastMoveKnownAntiAirSignature[aircraft] = KnownAntiAirSignature(knownAaZones);
			return true;
		}

		void BeginReconRetreat(IBot bot, Actor unit, string reason)
		{
			var targetId = activeTargetActorId;
			var origin = reconOrigin;
			commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, $"RECON -> RETREAT: {reason}");
			reconRetreatActor = unit;
			reconRetreatOrigin = origin;
			FransBotLog.BotDebug(world,
				"{0}: Air persistent RECON {1} -> RETREAT; lone {2} {3} cancels its queued patrol and returns toward {4} with a non-queued plain Move: {5}. General keeps the RECON target open for a later bidder.",
				player, targetId, unit.Info.Name, unit.ActorID, origin, reason);
			ResetMission();
			reconRetreatActor = unit;
			reconRetreatOrigin = origin;
			RefreshTransientReservations();
			QueueMove(bot, unit, origin, true);
		}

		void MaintainReconRetreat(IBot bot, IReadOnlyCollection<Actor> aircraft)
		{
			if (reconRetreatActor == null)
				return;
			if (!reconRetreatActor.IsInWorld || reconRetreatActor.IsDead || !aircraft.Contains(reconRetreatActor))
			{
				reconRetreatActor = null;
				RefreshTransientReservations();
				return;
			}
			if ((reconRetreatActor.Location - reconRetreatOrigin).LengthSquared <= 4)
			{
				FransBotLog.BotDebug(world,
					"{0}: Air RECON RETREAT complete for {1} at {2}. Aircraft returns to normal Commander ownership.",
					player, reconRetreatActor, reconRetreatActor.Location);
				reconRetreatActor = null;
				RefreshTransientReservations();
				return;
			}
			QueueMove(bot, reconRetreatActor, reconRetreatOrigin, false);
			RefreshTransientReservations();
		}

		void AbortReconMission(string reason)
		{
			commandBidService.ReleaseMission(FransCommanderKind.Air, BidderKey, reason);
			FransBotLog.BotDebug(world,
				"{0}: Air persistent RECON MineCluster {1} mission aborted without General completion: {2}. Target remains eligible for rebid.",
				player, activeTargetActorId, reason);
			ResetMission();
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
			reconPioneerBestDistanceSquared = int.MaxValue;
			reconPioneerLastProgressWorldTick = -1;
			reconLoggedContactIds.Clear();
		}

		void ResetAirSecureLivenessDiagnostics()
		{
			secureDiagnosticMission = null;
			lastSecureDiagnosticSignature = null;
			lastSecureDiagnosticBranch = "None";
			nextSecureDiagnosticHeartbeatWorldTick = 0;
			secureDiagnosticOwnershipActive = false;
			secureProgressDiagnostics.Clear();
			secureMoveIntentDiagnostics.Clear();
		}

		void EnsureAirSecureDiagnosticMission(FransActiveMission mission)
		{
			var changed = !secureDiagnosticMission.HasValue ||
				secureDiagnosticMission.Value.TargetActorId != mission.TargetActorId ||
				secureDiagnosticMission.Value.StartedWorldTick != mission.StartedWorldTick ||
				!string.Equals(secureDiagnosticMission.Value.BidderKey, mission.BidderKey, StringComparison.Ordinal);
			if (!changed)
				return;

			ResetAirSecureLivenessDiagnostics();
			secureDiagnosticMission = mission;
			secureDiagnosticOwnershipActive = true;
			nextSecureDiagnosticHeartbeatWorldTick = world.WorldTick + Info.UtilizationLogInterval;
		}

		void ObserveAirSecureDiagnosticProgress(FransActiveMission mission, CPos objective)
		{
			EnsureAirSecureDiagnosticMission(mission);
			var liveById = combatIntelService.OwnedActors
				.Where(a => a != null && a.IsInWorld && !a.IsDead)
				.ToDictionary(a => a.ActorID);
			foreach (var actorId in mission.CommittedActorIds ?? Array.Empty<uint>())
			{
				if (!liveById.TryGetValue(actorId, out var aircraft))
					continue;

				var distanceSquared = (long)(aircraft.Location - objective).LengthSquared;
				if (!secureProgressDiagnostics.TryGetValue(actorId, out var progress) || progress.Objective != objective)
				{
					RebaseAirSecureDiagnosticProgress(aircraft, objective);
					continue;
				}

				progress.PreviousDistanceSquared = progress.LastDistanceSquared;
				progress.ImprovedOnLastSample = distanceSquared < progress.LastDistanceSquared;
				if (aircraft.Location != progress.LastCell)
					progress.LastMovementWorldTick = world.WorldTick;
				if (distanceSquared < progress.BestDistanceSquared)
				{
					progress.BestDistanceSquared = distanceSquared;
					progress.LastProgressWorldTick = world.WorldTick;
					progress.ImprovedSinceLastReport = true;
				}
				progress.LastCell = aircraft.Location;
				progress.LastDistanceSquared = distanceSquared;
			}
		}

		void RebaseAirSecureDiagnosticProgress(Actor aircraft, CPos objective)
		{
			if (!secureDiagnosticOwnershipActive || aircraft == null || !secureDiagnosticMission.HasValue ||
				!(secureDiagnosticMission.Value.CommittedActorIds ?? Array.Empty<uint>()).Contains(aircraft.ActorID))
				return;

			var distanceSquared = (long)(aircraft.Location - objective).LengthSquared;
			secureProgressDiagnostics[aircraft.ActorID] = new SecureProgressDiagnostic
			{
				Objective = objective,
				LastCell = aircraft.Location,
				PreviousDistanceSquared = distanceSquared,
				LastDistanceSquared = distanceSquared,
				BestDistanceSquared = distanceSquared,
				LastMovementWorldTick = world.WorldTick,
				LastProgressWorldTick = world.WorldTick,
				ImprovedOnLastSample = false
			};
		}

		string GetAirSecureServiceState(Actor aircraft)
		{
			if (aircraft == null || !aircraft.IsInWorld || aircraft.IsDead || aircraft.Owner != player)
				return "MissingOrDead";
			var armed = HasAmmo(aircraft);
			var repair = NeedsNativeRepair(aircraft);
			var damaged = aircraft.GetDamageState() > DamageState.Undamaged;
			if (!armed)
				return repair ? "AliveUnarmedRepairRequired" : "AliveUnarmedRearming";
			if (repair)
				return "AliveArmedRepairRequired";
			return damaged ? "AliveArmedDamaged" : "AliveArmedHealthy";
		}

		string FormatAirSecureActorDiagnostic(uint actorId, CPos objective)
		{
			var aircraft = combatIntelService.OwnedActors.FirstOrDefault(a => a != null && a.ActorID == actorId);
			if (aircraft == null || !aircraft.IsInWorld || aircraft.IsDead || aircraft.Owner != player)
				return $"{actorId}:state=MissingOrDead,immutableCommitted=True,activeTracked=False";

			var armed = HasAmmo(aircraft);
			var fullAmmo = HasFullRaidAmmo(aircraft);
			var repairRequired = NeedsNativeRepair(aircraft);
			var damageState = aircraft.GetDamageState();
			var health = aircraft.TraitOrDefault<Health>();
			var hp = health == null ? "n/a" : $"{health.HP}/{health.MaxHP}";
			var repairable = aircraft.TraitOrDefault<Repairable>();
			var repairBuilding = repairRequired ? repairable?.FindRepairBuilding(aircraft) : null;
			var repairSite = repairBuilding == null
				? "None"
				: $"{repairBuilding.ActorID}/{repairBuilding.Info.Name}@{repairBuilding.Location}";
			var distanceSquared = (long)(aircraft.Location - objective).LengthSquared;
			var previousDistance = distanceSquared;
			var bestDistance = distanceSquared;
			var lastMovement = world.WorldTick;
			var lastProgress = world.WorldTick;
			var improved = false;
			var improvedSinceReport = false;
			if (secureProgressDiagnostics.TryGetValue(actorId, out var progress) && progress.Objective == objective)
			{
				previousDistance = progress.PreviousDistanceSquared;
				bestDistance = progress.BestDistanceSquared;
				lastMovement = progress.LastMovementWorldTick;
				lastProgress = progress.LastProgressWorldTick;
				improved = progress.ImprovedOnLastSample;
				improvedSinceReport = progress.ImprovedSinceLastReport;
			}
			var returnTick = lastReturnWorldTick.TryGetValue(aircraft, out var lastReturn) ? lastReturn.ToString() : "None";
			var repairTick = lastRepairWorldTick.TryGetValue(aircraft, out var lastRepair) ? lastRepair.ToString() : "None";
			return $"{actorId}/{aircraft.Info.Name}:state={GetAirSecureServiceState(aircraft)},immutableCommitted=True," +
				$"activeTracked={activeAircraft.Contains(aircraft)}," +
				$"cell={aircraft.Location},objective={objective},distanceSq={distanceSquared},previousDistanceSq={previousDistance}," +
				$"bestDistanceSq={bestDistance},lastMovementWT={lastMovement},lastProgressWT={lastProgress},improvedLastSample={improved}," +
				$"improvedSinceLastReport={improvedSinceReport}," +
				$"ammo={armed},fullAmmo={fullAmmo},repairRequired={repairRequired},damage={damageState},hp={hp}," +
				$"repairBuilding={repairSite},idle={aircraft.IsIdle},currentActivity={aircraft.CurrentActivity?.GetType().Name ?? "None"}," +
				$"lastReturnToBaseWT={returnTick},lastRepairOrderWT={repairTick}";
		}

		string FormatAirSecureMoveDiagnostic(uint actorId)
		{
			if (!secureMoveIntentDiagnostics.TryGetValue(actorId, out var move))
				return $"{actorId}:outcome=None";
			return $"{actorId}:outcome={move.Outcome},requested={move.RequestedDestination},cell={move.CurrentCell}," +
				$"idle={move.IsIdle},cachedDestinationMatched={move.CachedDestinationMatched}," +
				$"knownAaSignatureMatched={move.KnownAaSignatureMatched},previousMoveWT={move.PreviousMoveWorldTick}," +
				$"currentActivity={move.CurrentActivity},activityIsExpectedMove=" +
				$"{(move.ActivityIsExpectedMove.HasValue ? move.ActivityIsExpectedMove.Value.ToString() : "n/a")}," +
				$"eventWT={move.EventWorldTick},waypoints={move.WaypointCount},counts=queued:{move.QueuedCount}/" +
				$"suppressedNonIdle:{move.SuppressedNonIdleCount}/suppressedRefreshHold:{move.SuppressedRefreshHoldCount}/" +
				$"rejectedKnownAa:{move.RejectedKnownAaCount}";
		}

		void RecordAirSecureMoveIntent(Actor aircraft, CPos destination, bool cachedDestinationMatched,
			bool knownAaSignatureMatched, int previousMoveWorldTick, string outcome, int waypointCount = 0,
			string currentActivity = "NotCaptured", bool? activityIsExpectedMove = null)
		{
			if (!secureDiagnosticOwnershipActive || aircraft == null || !secureDiagnosticMission.HasValue ||
				!(secureDiagnosticMission.Value.CommittedActorIds ?? Array.Empty<uint>()).Contains(aircraft.ActorID))
				return;

			if (!secureMoveIntentDiagnostics.TryGetValue(aircraft.ActorID, out var move))
			{
				move = new SecureMoveIntentDiagnostic();
				secureMoveIntentDiagnostics.Add(aircraft.ActorID, move);
			}
			move.RequestedDestination = destination;
			move.CurrentCell = aircraft.Location;
			move.IsIdle = aircraft.IsIdle;
			move.CachedDestinationMatched = cachedDestinationMatched;
			move.KnownAaSignatureMatched = knownAaSignatureMatched;
			move.PreviousMoveWorldTick = previousMoveWorldTick;
			move.EventWorldTick = world.WorldTick;
			move.WaypointCount = waypointCount;
			move.Outcome = outcome;
			move.CurrentActivity = currentActivity;
			move.ActivityIsExpectedMove = activityIsExpectedMove;
			switch (outcome)
			{
				case "QueuedNativeMove": move.QueuedCount++; break;
				case "SuppressedNonIdle": move.SuppressedNonIdleCount++; break;
				case "SuppressedRefreshHold": move.SuppressedRefreshHoldCount++; break;
				case "RejectedKnownAaPath": move.RejectedKnownAaCount++; break;
			}
		}

		void LogAirSecureLiveness(FransActiveMission mission, string branch, CPos objective, string detail,
			FransCombatIntelContact? rememberedBuilding = null, int assembled = -1, int required = -1, bool force = false)
		{
			ObserveAirSecureDiagnosticProgress(mission, objective);
			var committedIds = (mission.CommittedActorIds ?? Array.Empty<uint>()).OrderBy(id => id).ToArray();
			var remembered = rememberedBuilding.HasValue
				? $"{rememberedBuilding.Value.ActorId}/{rememberedBuilding.Value.ActorType}@{rememberedBuilding.Value.LastSeenCell}:" +
					$"visible={rememberedBuilding.Value.IsVisible},defensive={rememberedBuilding.Value.IsDefensiveBuilding}"
				: "None";
			var serviceSignature = string.Join(",", committedIds.Select(id =>
			{
				var aircraft = combatIntelService.OwnedActors.FirstOrDefault(a => a != null && a.ActorID == id);
				return aircraft == null || !aircraft.IsInWorld || aircraft.IsDead || aircraft.Owner != player
					? $"{id}:MissingOrDead"
					: $"{id}:{GetAirSecureServiceState(aircraft)}:{aircraft.GetDamageState()}:fullAmmo={HasFullRaidAmmo(aircraft)}";
			}));
			var moveSignature = string.Join(",", committedIds.Select(id =>
				secureMoveIntentDiagnostics.TryGetValue(id, out var move)
					? $"{id}:{move.Outcome}:{move.CurrentActivity}:{move.ActivityIsExpectedMove}"
					: $"{id}:None"));
			var signature = $"{mission.TargetActorId}|{mission.StartedWorldTick}|{branch}|{objective}|" +
				$"{rememberedBuilding?.ActorId ?? 0}|{rememberedBuilding?.IsVisible ?? false}|{assembled}|{required}|" +
				$"{serviceSignature}|{moveSignature}";
			var heartbeat = world.WorldTick >= nextSecureDiagnosticHeartbeatWorldTick;
			if (!force && !heartbeat && string.Equals(signature, lastSecureDiagnosticSignature, StringComparison.Ordinal))
				return;

			var previousBranch = lastSecureDiagnosticBranch;
			var eventKind = force || !string.Equals(signature, lastSecureDiagnosticSignature, StringComparison.Ordinal)
				? "StateChange"
				: "Heartbeat";
			var actorDetails = string.Join(" | ", committedIds.Select(id => FormatAirSecureActorDiagnostic(id, objective)));
			var moveDetails = string.Join(" | ", committedIds.Select(FormatAirSecureMoveDiagnostic));
			var clearHold = secureClearSinceWorldTick < 0 ? 0 : Math.Max(0, world.WorldTick - secureClearSinceWorldTick);
			FransBotLog.BotDebug(world,
				"{0}: [AIR SECURE LIVENESS] event={1} WT={2} mission={3} targetType={4} bidder={5} branch={6} previousBranch={7} " +
				"acceptedObjective={8} currentObjective={9} acceptedWT={10} ageWT={11} committed=[{12}] assembled={13}/{14} " +
				"clearHoldWT={15}/{16} remembered={17} actors=[{18}] moveIntent=[{19}] detail={20}.",
				player, eventKind, world.WorldTick, mission.TargetActorId, mission.TargetActorType, BidderKey, branch, previousBranch,
				mission.LastVisibleTargetCell, objective, mission.StartedWorldTick, Math.Max(0, world.WorldTick - mission.StartedWorldTick),
				string.Join(",", committedIds), assembled < 0 ? "n/a" : assembled.ToString(), required < 0 ? "n/a" : required.ToString(),
				clearHold, Info.SecureClearHoldTicks, remembered, actorDetails, moveDetails, detail ?? "None");
			lastSecureDiagnosticSignature = signature;
			lastSecureDiagnosticBranch = branch;
			nextSecureDiagnosticHeartbeatWorldTick = world.WorldTick + Info.UtilizationLogInterval;
			foreach (var progress in secureProgressDiagnostics.Values)
				progress.ImprovedSinceLastReport = false;
		}

		void LogAirSecureReleased(FransActiveMission mission, CPos objective, string reason)
		{
			LogAirSecureLiveness(mission, "Released", objective, reason, force: true);
			secureDiagnosticOwnershipActive = false;
		}

		void QueueAttack(IBot bot, Actor aircraft, Actor target, bool force)
		{
			if (!force && lastFightTarget.TryGetValue(aircraft, out var old) && old == target.ActorID &&
				lastFightWorldTick.TryGetValue(aircraft, out var last) && world.WorldTick - last < Info.FightRefreshInterval)
				return;
			bot.QueueOrder(new Order("Attack", aircraft, Target.FromActor(target), false));
			lastFightTarget[aircraft] = target.ActorID;
			lastFightWorldTick[aircraft] = world.WorldTick;
		}

		void QueueAttackMove(IBot bot, Actor aircraft, CPos destination, bool force)
		{
			if (!force && lastMoveDestination.TryGetValue(aircraft, out var old) && old == destination && !aircraft.IsIdle)
				return;
			bot.QueueOrder(new Order("AttackMove", aircraft, Target.FromCell(world, destination), false));
			lastMoveDestination[aircraft] = destination;
			lastMoveWorldTick[aircraft] = world.WorldTick;
		}

		bool QueueMove(IBot bot, Actor aircraft, CPos destination, bool force,
			bool allowSecureFlyIdleReacquire = false)
		{
			var knownAaZones = GetKnownAntiAirZones();
			var aaSignature = KnownAntiAirSignature(knownAaZones);
			var cachedDestinationMatched = lastMoveDestination.TryGetValue(aircraft, out var old) && old == destination;
			var knownAaSignatureMatched = lastMoveKnownAntiAirSignature.TryGetValue(aircraft, out var oldSignature) && oldSignature == aaSignature;
			var previousMoveWorldTick = lastMoveWorldTick.TryGetValue(aircraft, out var last) ? last : -1;
			string replacedActivity = null;
			bool? replacedActivityWasExpectedMove = null;
			if (!force && cachedDestinationMatched && knownAaSignatureMatched)
			{
				// Do not restart an in-progress native Move on a timer. A changed known-AA signature
				// deliberately bypasses this guard so a newly learned SAM/AA replans immediately.
				if (!aircraft.IsIdle)
				{
					var currentActivity = aircraft.CurrentActivity;
					var activityIsExpectedMove = currentActivity is Fly;
					var canReacquireSecureObjective = allowSecureFlyIdleReacquire && currentActivity is FlyIdle;
					if (activityIsExpectedMove || !canReacquireSecureObjective)
					{
						RecordAirSecureMoveIntent(aircraft, destination, cachedDestinationMatched,
							knownAaSignatureMatched, previousMoveWorldTick, "SuppressedNonIdle",
							currentActivity: currentActivity?.GetType().Name ?? "None",
							activityIsExpectedMove: activityIsExpectedMove);
						return true;
					}

					// FlyIdle is OpenRA's indefinite passive holding activity after ordinary aircraft work ends.
					// Only accepted SECURE objective execution may replace it here. Active combat, ReturnToBase,
					// repair, resupply, landing, and every non-SECURE QueueMove retain the existing suppression.
					replacedActivity = currentActivity.GetType().Name;
					replacedActivityWasExpectedMove = false;
				}
				if (previousMoveWorldTick >= 0 && world.WorldTick - previousMoveWorldTick < Info.MoveRefreshInterval)
				{
					RecordAirSecureMoveIntent(aircraft, destination, cachedDestinationMatched,
						knownAaSignatureMatched, previousMoveWorldTick, "SuppressedRefreshHold");
					return true;
				}
			}

			if (!TryBuildKnownAntiAirSafePath(aircraft.Location, destination, knownAaZones, out var safePath))
			{
				RecordAirSecureMoveIntent(aircraft, destination, cachedDestinationMatched,
					knownAaSignatureMatched, previousMoveWorldTick, "RejectedKnownAaPath",
					currentActivity: replacedActivity ?? "NotCaptured",
					activityIsExpectedMove: replacedActivityWasExpectedMove);
				return false;
			}

			// Normal Air mission transit still uses native plain Move. The Commander queues deterministic
			// safe waypoints so no planned segment enters the YAML-configured known SAM/AA radius.
			// uses native AttackMove only for normal post-RAID return-to-origin with ammo remaining.
			for (var i = 0; i < safePath.Length; i++)
				bot.QueueOrder(new Order("Move", aircraft, Target.FromCell(world, safePath[i]), i > 0));
			lastMoveDestination[aircraft] = destination;
			lastMoveWorldTick[aircraft] = world.WorldTick;
			lastMoveKnownAntiAirSignature[aircraft] = aaSignature;
			if (replacedActivity != null)
				RebaseAirSecureDiagnosticProgress(aircraft, destination);
			RecordAirSecureMoveIntent(aircraft, destination, cachedDestinationMatched,
				knownAaSignatureMatched, previousMoveWorldTick, "QueuedNativeMove", safePath.Length,
				currentActivity: replacedActivity ?? "NotCaptured",
				activityIsExpectedMove: replacedActivityWasExpectedMove);
			return true;
		}

		void QueueReturnToBase(IBot bot, Actor aircraft, bool force = false)
		{
			if (!force && Info.ReturnToBaseRetryHoldTicks > 0 && lastReturnWorldTick.TryGetValue(aircraft, out var last) &&
				world.WorldTick - last < Info.ReturnToBaseRetryHoldTicks)
				return;
			bot.QueueOrder(new Order("ReturnToBase", aircraft, false));
			lastReturnWorldTick[aircraft] = world.WorldTick;
		}

		bool IsManagedAircraft(Actor actor)
		{
			return actor != null && actor.IsInWorld && !actor.IsDead && actor.Owner == player &&
				Info.ManagedAircraftTypes.Contains(actor.Info.Name) && actor.TraitOrDefault<Aircraft>() != null;
		}

		void RememberMissionAnchor(FransActiveMission mission)
		{
			hasMissionAnchorPoint = mission.HasAnchorPoint;
			missionAnchorPoint = mission.HasAnchorPoint ? mission.AnchorPoint : default;
		}

		bool NeedsNativeRepair(Actor aircraft)
		{
			return aircraft != null && aircraft.IsInWorld && !aircraft.IsDead &&
				aircraft.GetDamageState() > DamageState.Undamaged && aircraft.TraitOrDefault<Repairable>() != null;
		}

		bool IsAirRecoveryReady(Actor aircraft)
		{
			return IsAirServiceReady(aircraft, retreatStartedWorldTick, requireFullAmmo: false);
		}

		bool IsRaidServiceReady(Actor aircraft, int recoveryStartedWorldTick)
		{
			return IsAirServiceReady(aircraft, recoveryStartedWorldTick, requireFullAmmo: true);
		}

		bool IsAirServiceReady(Actor aircraft, int recoveryStartedWorldTick, bool requireFullAmmo)
		{
			if (aircraft == null || !aircraft.IsInWorld || aircraft.IsDead ||
				(requireFullAmmo ? !HasFullRaidAmmo(aircraft) : !HasAmmo(aircraft)))
				return false;
			var repairable = aircraft.TraitOrDefault<Repairable>();
			if (repairable == null || aircraft.GetDamageState() <= DamageState.Undamaged)
				return true;

			// Reuse the existing Air recovery fallback: if physical repair infrastructure is gone,
			// an armed aircraft is released after the same configured recovery interval instead of
			// remaining reserved forever. The same shared recovery-progress watchdog is also used by normal RAID recovery; no parallel recovery state machine is introduced.
			return Info.RecoveryAllowUnrepairedWithoutRepairBuilding && recoveryStartedWorldTick >= 0 &&
				world.WorldTick - recoveryStartedWorldTick >= Info.RecoveryProgressWatchdogTicks &&
				repairable.FindRepairBuilding(aircraft) == null;
		}

		void ClearRecoveryProgressTracking()
		{
			recoveryLastObservedHp.Clear();
			recoveryLastObservedAmmoCount.Clear();
			recoveryLastObservedAnchorDistance.Clear();
			recoveryLastObservedServiceDistance.Clear();
			recoveryLastProgressWorldTick.Clear();
			recoveryLastWatchdogReissueWorldTick.Clear();
		}

		void RemoveRecoveryProgressTracking(Actor actor)
		{
			if (actor == null)
				return;
			recoveryLastObservedHp.Remove(actor);
			recoveryLastObservedAmmoCount.Remove(actor);
			recoveryLastObservedAnchorDistance.Remove(actor);
			recoveryLastObservedServiceDistance.Remove(actor);
			recoveryLastProgressWorldTick.Remove(actor);
			recoveryLastWatchdogReissueWorldTick.Remove(actor);
		}

		void RemoveStaleRecoveryProgressTracking()
		{
			var live = activeAircraft.Concat(raidRecoverySince.Keys).Where(a => a != null).ToHashSet();
			foreach (var actor in recoveryLastProgressWorldTick.Keys.Where(a => !live.Contains(a)).ToArray())
			{
				recoveryLastObservedHp.Remove(actor);
				recoveryLastObservedAmmoCount.Remove(actor);
				recoveryLastObservedAnchorDistance.Remove(actor);
				recoveryLastObservedServiceDistance.Remove(actor);
				recoveryLastProgressWorldTick.Remove(actor);
				recoveryLastWatchdogReissueWorldTick.Remove(actor);
			}
		}

		void ObserveRecoveryProgress(Actor aircraft, CPos anchor, bool requireFullAmmo, bool initialize)
		{
			if (aircraft == null || !aircraft.IsInWorld || aircraft.IsDead)
				return;

			var health = aircraft.TraitOrDefault<Health>();
			var hp = health?.HP ?? int.MaxValue;
			var ammoReady = requireFullAmmo ? HasFullRaidAmmo(aircraft) : HasAmmo(aircraft);
			var ammoCount = GetRaidAmmoCount(new[] { aircraft });
			var anchorDistance = (long)(aircraft.Location - anchor).LengthSquared;
			var repairable = aircraft.TraitOrDefault<Repairable>();
			var repairBuilding = aircraft.GetDamageState() > DamageState.Undamaged ? repairable?.FindRepairBuilding(aircraft) : null;
			var rearmBuilding = !ammoReady ? FindNearestRearmBuilding(aircraft) : null;
			var serviceBuilding = repairBuilding ?? rearmBuilding;
			var serviceDistance = serviceBuilding != null
				? (long)(aircraft.Location - serviceBuilding.Location).LengthSquared
				: long.MaxValue;
			if (initialize || !recoveryLastProgressWorldTick.ContainsKey(aircraft))
			{
				recoveryLastObservedHp[aircraft] = hp;
				recoveryLastObservedAmmoCount[aircraft] = ammoCount;
				recoveryLastObservedAnchorDistance[aircraft] = anchorDistance;
				recoveryLastObservedServiceDistance[aircraft] = serviceDistance;
				recoveryLastProgressWorldTick[aircraft] = world.WorldTick;
				return;
			}

			var damagedWithRepairBuilding = repairBuilding != null;
			var hadHp = recoveryLastObservedHp.TryGetValue(aircraft, out var oldHp);
			var hadAmmo = recoveryLastObservedAmmoCount.TryGetValue(aircraft, out var oldAmmoCount);
			var hadAnchorDistance = recoveryLastObservedAnchorDistance.TryGetValue(aircraft, out var oldAnchorDistance);
			var hadServiceDistance = recoveryLastObservedServiceDistance.TryGetValue(aircraft, out var oldServiceDistance);
			var approachedService = hadServiceDistance && serviceDistance < oldServiceDistance;
			var gainedAmmo = hadAmmo && ammoCount >= 0 && oldAmmoCount >= 0 && ammoCount > oldAmmoCount;
			var progressed = damagedWithRepairBuilding
				? (hadHp && hp > oldHp) || approachedService
				: !ammoReady
					? gainedAmmo || approachedService
					: hadAnchorDistance && anchorDistance < oldAnchorDistance;

			if (progressed)
				recoveryLastProgressWorldTick[aircraft] = world.WorldTick;
			recoveryLastObservedHp[aircraft] = hp;
			recoveryLastObservedAmmoCount[aircraft] = ammoCount;
			recoveryLastObservedAnchorDistance[aircraft] = anchorDistance;
			recoveryLastObservedServiceDistance[aircraft] = serviceDistance;
		}

		Actor FindNearestRearmBuilding(Actor aircraft)
		{
			var rearmable = aircraft?.Info.TraitInfoOrDefault<RearmableInfo>();
			if (rearmable == null || !rearmable.RearmActors.Any())
				return null;

			return combatIntelService.OwnedActors
				.Where(a => a != null && a.IsInWorld && !a.IsDead && rearmable.RearmActors.Contains(a.Info.Name))
				.OrderBy(a => (a.Location - aircraft.Location).LengthSquared)
				.ThenBy(a => a.ActorID)
				.FirstOrDefault();
		}

		bool RecoveryWatchdogDue(Actor aircraft)
		{
			if (!recoveryLastProgressWorldTick.TryGetValue(aircraft, out var lastProgress) ||
				world.WorldTick - lastProgress < Info.RecoveryProgressWatchdogTicks)
				return false;
			return !recoveryLastWatchdogReissueWorldTick.TryGetValue(aircraft, out var lastReissue) ||
				Info.RecoveryWatchdogRetryHoldTicks == 0 || world.WorldTick - lastReissue >= Info.RecoveryWatchdogRetryHoldTicks;
		}

		void MarkRecoveryWatchdogReissue(Actor aircraft, string action)
		{
			recoveryLastWatchdogReissueWorldTick[aircraft] = world.WorldTick;
			FransBotLog.BotDebug(world,
				"{0}: Air Commander {1} recovery watchdog refreshes {2} for {3} after {4} WT without repair/rearm/regroup progress.",
				player, BidderKey, action, aircraft, Info.RecoveryProgressWatchdogTicks);
		}

		void RouteAirRetreatUnit(IBot bot, Actor aircraft, bool forceMove)
		{
			var watchdog = RecoveryWatchdogDue(aircraft);
			if (RouteAirServiceUnit(bot, aircraft, requireFullAmmo: false, watchdog: watchdog))
				return;

			// No physical repair is currently possible, or service is complete. RETREAT keeps its
			// existing ANCHOR regroup behavior and 50/75 recovery semantics.
			if (NeedsNativeRepair(aircraft) && watchdog)
				MarkRecoveryWatchdogReissue(aircraft, "ANCHOR fallback because no repair building exists");
			if (watchdog && !aircraft.IsIdle)
				QueueStopOrder(bot, aircraft);
			QueueMove(bot, aircraft, retreatAnchorPoint, forceMove || watchdog);
			if (watchdog)
				MarkRecoveryWatchdogReissue(aircraft, "ANCHOR regroup Move");
		}

		bool RouteAirServiceUnit(IBot bot, Actor aircraft, bool requireFullAmmo, bool watchdog)
		{
			var repairable = aircraft.TraitOrDefault<Repairable>();
			if (repairable != null && aircraft.GetDamageState() > DamageState.Undamaged)
			{
				var repairBuilding = repairable.FindRepairBuilding(aircraft);
				if (repairBuilding != null)
				{
					if (aircraft.IsIdle || watchdog)
					{
						if (watchdog && !aircraft.IsIdle)
							QueueStopOrder(bot, aircraft);
						bot.QueueOrder(new Order("Repair", aircraft, Target.FromActor(repairBuilding), false));
						lastRepairWorldTick[aircraft] = world.WorldTick;
						if (watchdog)
							MarkRecoveryWatchdogReissue(aircraft, $"native Repair toward {repairBuilding}");
					}
					return true;
				}

				// Existing recovery policy handles the no-repair-building case. Continue into the
				// normal ammo check so an aircraft can still use native ReturnToBase/rearm.
			}

			var ammoReady = requireFullAmmo ? HasFullRaidAmmo(aircraft) : HasAmmo(aircraft);
			if (ammoReady)
				return false;

			if (watchdog && !aircraft.IsIdle)
				QueueStopOrder(bot, aircraft);
			QueueReturnToBase(bot, aircraft, watchdog);
			if (watchdog)
				MarkRecoveryWatchdogReissue(aircraft, "native ReturnToBase/rearm");
			return true;
		}

		bool HasAmmo(Actor aircraft)
		{
			var pools = aircraft.TraitsImplementing<AmmoPool>().ToArray();
			return pools.Length == 0 || pools.All(pool => pool.HasAmmo);
		}

		bool HasFullRaidAmmo(Actor aircraft)
		{
			var pools = aircraft.TraitsImplementing<AmmoPool>().ToArray();
			return pools.Length == 0 || pools.All(pool => pool.HasFullAmmo);
		}

		bool CanAttackActor(Actor aircraft, Actor target)
		{
			if (!IsVisibleEnemy(target))
				return false;
			var attackTarget = Target.FromActor(target);
			return aircraft.TraitsImplementing<AttackBase>()
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
			activeAircraft.Clear();
			activeTargetActorId = 0;
			combinedSecureHoldTargetActorId = 0;
			combinedSecureHoldUntilTick = -1;
			activeObjective = default;
			activeOrder = FransCommanderOrder.Move;
			activeMissionType = FransMissionType.Recon;
			activeOrderStartedWorldTick = world.WorldTick;
			lostContactSinceWorldTick = -1;
			secureClearSinceWorldTick = -1;
			ResetAirSecureLivenessDiagnostics();
			hasMissionAnchorPoint = false;
			missionAnchorPoint = default;
			ResetReconState();
			hasMoveRiskCheck = false;
			moveRiskAllowed = false;
			nextMoveRiskCheckTick = 0;
			raidStrikeIssued = false;
			raidPreStrikeDroppedActorIds.Clear();
			raidCommittedContributionByActor.Clear();
			ResetRaidLostTargetConfirmation(false);
			ResetRaidStrikeAmmoProgress();
			ResetRaidApproachProgress();
			raidLastRiskRevision = -1;
			raidLastRiskObjective = default;
			raidCommittedCriticalRiskSinceTick = -1;
			raidMissionOrigins.Clear();
		}
	}
}
