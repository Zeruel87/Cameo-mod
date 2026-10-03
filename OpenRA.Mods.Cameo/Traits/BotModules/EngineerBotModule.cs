#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * Copyright 2015- OpenRA.Mods.AS Developers (see AUTHORS)
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
using OpenRA.Activities;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	// Merged from CA CaptureManagerBotModuleCA (Cameo's copy of CAmod's, itself from OpenRA.Mods.AS) and AS
	// CncEngineerManagerBotModule (engine d5d8b2a685) under DESIGN §19.3 (one module per decision). AI_MASTER_PLAN ENG.
	//   from CA: capture — a priority target by chance (nearest to the base first), otherwise the most valuable
	//            capturable of a random enemy/neutral player, nearest per engineer; SafePath was meant to route the
	//            engineer around enemy fire but never did (its goal predicate matched the start cell and the path was
	//            discarded) — SafeRoute below does it for real when MaxExposedRouteCells >= 0.
	//   from AS: bridge-hut repair and instant building repair (nearest path-reachable target, one engineer per
	//            evaluation, the repair jobs taking turns); the stuck check (moving, not moved since the last sample).
	//            DESIGN §19.5 lets the whole module see through fog (maintainer 2026-09-30); both visibility switches
	//            remain, so a fog-honest engineer owner is one yaml line each.
	//   new:     the ONE owner of every engineer (review P0b, "IsIdle is not ownership"): an LC1 claim before every
	//            order, renewed while the engineer works and released when it is idle again; its own in-flight set,
	//            so the capture and repair passes never order one engineer twice in a tick (the lease lets the same
	//            owner re-claim, so it cannot catch that); a stuck engineer is stopped, released and retried after
	//            StuckRetryTicks (the AS module benched it for the rest of the match); an optional visibility check
	//            for bridge huts (the AS module had none).
	[TraitLocation(SystemActors.Player)]
	[Desc("The ONE owner of the bot's engineers (DESIGN §19.3): replaces CaptureManagerBotModuleCA + CncEngineerBotModule,",
		"which ordered the same idle engineers side by side. classic keeps running the CA copy alone.")]
	public class EngineerBotModuleInfo : ConditionalTraitInfo
	{
		// The three id lists below: empty = read from CaptureManagerBotModuleCA on the same Player actor (classic's copy,
		// defined whatever its condition), so the ids live in ai.yaml once (audit_central_ids is lower-only).
		[Desc("Actor types that capture (via `Captures`). Empty: CaptureManagerBotModuleCA's list on this actor.")]
		public readonly HashSet<string> CapturingActorTypes = [];

		[Desc("Percentage chance of trying a priority capture.")]
		public readonly int PriorityCaptureChance = 75;

		[Desc("Actor types captured first, nearest to the base first. Empty: CaptureManagerBotModuleCA's list.")]
		public readonly HashSet<string> PriorityCapturableActorTypes = [];

		[Desc("Actor types that may be captured; empty on both modules includes all actors. Empty: CaptureManagerBotModuleCA's list.")]
		public readonly HashSet<string> CapturableActorTypes = [];

		[Desc("Avoid enemy actors this close to the path when routing a capturer. Near the maximum weapon range.")]
		public readonly WDist EnemyAvoidanceRadius = WDist.FromCells(8);

		[Desc("Route engineers for real (maintainer 2026-09-30: if three engineers die at one target, the path was not",
			"safe enough). The parents' SafePath never scored a route: its goal predicate matched the engineer's own cell,",
			"and the order ignored the result, so engineers walked the default shortest path. With this >= 0 the module",
			"searches the least-exposed path (cost: nearness of ARMED enemies within EnemyAvoidanceRadius), skips a target",
			"whose safest path still has more than this many exposed cells outside the final approach, and walks the",
			"engineer along it through waypoints. -1 = the parents' behaviour, the default until its A/B.")]
		public readonly int MaxExposedRouteCells = -1;

		[Desc("Re-check a routed capture while the engineer walks (v2): every this many ticks the REMAINING route cells (ahead",
			"of the engineer, outside ApproachCells) are scored; if more than MaxExposedRouteCells are exposed a fresh safe route",
			"from the engineer's cell is issued, and if none passes the engineer is pulled back to the base and the attempt is",
			"released (outmatched). Needs MaxExposedRouteCells >= 0; runs on its own countdown in BotTick (independent of",
			"MinimumCaptureDelay). 0 = off, the default.")]
		public readonly int RouteRecheckTicks = 0;

		[Desc("Stealth means unguarded (v2): a target that is not escort-eligible (an enemy-base building) is skipped when",
			"more than this many armed enemy actors stand within EnemyAvoidanceRadius of it. -1 = off, the default.")]
		public readonly int StealthMaxDefenders = -1;

		[Desc("Rank capture candidates by safety and value (v2) instead of pure distance: score = target value / (1 + distance",
			"in cells + ExposureWeight x exposed route cells); only the nearest CaptureTargetTries x 2 are scored. false = off.")]
		public readonly bool RankTargetsBySafety = false;

		[Desc("Cost of one exposed route cell, in cells of distance, for RankTargetsBySafety.")]
		public readonly int ExposureWeight = 10;

		[Desc("Cells around the target excluded from the exposure count: the final approach to a defended target is the",
			"escort's question (EscortDefendedCaptures), not the route's.")]
		public readonly int ApproachCells = 6;

		[Desc("Cells between the waypoints of a safe route (MaxExposedRouteCells >= 0).")]
		public readonly int RouteWaypointSpacing = 5;

		[Desc("Targets tried per engineer, nearest first, before it waits for the next evaluation. A target that is full",
			"(MaxEngineersPerTarget), dormant or unsafe is passed over so the engineer goes to a DIFFERENT target. 1 = the",
			"parents' single nearest target, the default until its A/B.")]
		public readonly int CaptureTargetTries = 1;

		[Desc("Ticks between capture evaluations.")]
		public readonly int MinimumCaptureDelay = 375;

		[Desc("Most capture targets considered per evaluation (at least 1).")]
		public readonly int MaximumCaptureTargetOptions = 10;

		[Desc("Consider visibility (shroud, fog, cloak) when choosing capture targets. DESIGN §19.5 allows false for this module.")]
		public readonly bool CheckCaptureTargetsForVisibility = true;

		[Desc("Player relationships whose actors capturers target.")]
		public readonly PlayerRelationship CapturableRelationships = PlayerRelationship.Enemy | PlayerRelationship.Neutral;

		[Desc("FB2 (Frans SpecOps demand-capturers): with zero live capturers the capture pipeline never",
			"even enumerates targets, so the first specialist only ever appears by unit-mix luck. On each",
			"capture evaluation, count the safe capturable targets (not full, not dormant, not escort-blocked);",
			"while live capturers < min(MaximumDemandCapturers, safe/DemandTargetsPerCapturer), request one",
			"more capturer type from the unit builders. The route/escort checks still gate the dispatch itself.")]
		public readonly bool UseDemandCapturers = false;

		[Desc("FB2 demand-capturers: never keep more live capturers than this.")]
		public readonly int MaximumDemandCapturers = 1;

		[Desc("FB2 demand-capturers: how many safe targets justify one specialist (Frans DemandTargetsPerCapturer).")]
		public readonly int DemandTargetsPerCapturer = 1;

		[Desc("Actor types that repair: bridge huts (via `RepairsBridges`) and buildings (via `InstantlyRepairs`).")]
		public readonly HashSet<string> RepairingActorTypes = [];

		[Desc("Allied building types an engineer repairs instantly (via `InstantlyRepairable`). Empty disables it.")]
		public readonly HashSet<string> RepairableActorTypes = [];

		[Desc("Repair an allied building at this damage state or worse.")]
		public readonly DamageState RepairableDamageState = DamageState.Heavy;

		[Desc("Bridge hut types an engineer repairs once their bridge is down. Empty disables it.")]
		public readonly HashSet<string> RepairableHutActorTypes = [];

		[Desc("Ticks between repair evaluations; also the stuck-check sample interval.")]
		public readonly int AssignRoleDelay = 120;

		[Desc("Only repair bridge huts the player can see. DESIGN §19.5 allows false for this module.")]
		public readonly bool CheckRepairTargetsForVisibility = true;

		[Desc("LC1 lease length in ticks, renewed at every evaluation while the engineer works.")]
		public readonly int LeaseTicks = 3000;

		[Desc("Ticks after an order before an idle engineer counts as done (orders reach the unit a few ticks late).")]
		public readonly int OrderGraceTicks = 50;

		[Desc("Ticks a stuck engineer is left alone before it may be ordered again.")]
		public readonly int StuckRetryTicks = 1500;

		[Desc("Most engineers sent at one capture target at a time (one mission, one live attempt). 0 = no limit,",
			"the parents' behaviour and the default until its A/B: a smoke match sent three engineers at one oil derrick",
			"within 400 ticks; the candidate sets 1 (AI_MASTER_PLAN §1.2 step 6).")]
		public readonly int MaxEngineersPerTarget = 0;

		[Desc("A capture mission whose attempts fail this many times in a row (the engineer died) goes dormant: its target",
			"is skipped for CaptureDormantTicks (fransotto's dormant shelf; AI_MISSION_CARDS §2.2). 0 disables. A smoke match",
			"lost five engineers one after another at one defended derrick. Off until its A/B; the candidate sets 2.")]
		public readonly int CaptureFailuresBeforeDormant = 0;

		[Desc("Ticks a dormant capture mission rests before its target may be tried again.")]
		public readonly int CaptureDormantTicks = 3000;

		[Desc("Consecutive released/outmatched retreats on the same capture mission that shelve it for",
			"CaptureDormantTicks. The death streak (CaptureFailuresBeforeDormant) is unchanged — a voluntary",
			"retreat is still not a failure — but a target whose route stays hot through every recheck produces",
			"commit-retreat churn the shelf otherwise never sees (armed 2v2 smoke: one defended airstrip committed",
			"4x by the same bot across ~28k ticks). Higher than the death threshold on purpose. 0 disables.")]
		public readonly int CaptureRetreatsBeforeDormant = 0;

		[Desc("Escort as ONE mission (maintainer 2026-09-30): a TECH building (neutral, or a PriorityCapturableActorTypes",
			"entry) defended by enemy armed units (within EnemyAvoidanceRadius) is not attempted solo; a building in the",
			"enemy base is never escorted — the engineer sneaks in alone (SafePath), an escort would give it away. The mission is PUBLISHED and a protection request is raised at the",
			"target (IBotProtectionRequestProvider, the squad manager's escort seam — it needs UseProtectionRequests); the",
			"engineer goes once our armed value there reaches EscortSuperiority percent of the defenders'. Off until its A/B.")]
		public readonly bool EscortDefendedCaptures = false;

		[Desc("Percent of the defenders' value our armed units near the target must reach before the engineer goes.")]
		public readonly int EscortSuperiority = 100;

		[Desc("The engineer also waits until the defenders' value near the target has fallen to this percent of their value",
			"when the mission was published: the escort must have thinned them out, not merely arrived (#693's first A/B",
			"smoke: the escort arrived, the engineer went into the firefight and died twice). 100 = no thinning required.")]
		public readonly int EscortThinnedPercent = 100;

		[Desc("Ticks an escorted capture waits for its escort before the mission is DENIED (no_units) and goes dormant.")]
		public readonly int EscortWaitTicks = 3000;

		[Desc("Ticks a published protection request stays valid; it is re-published while the mission lives.")]
		public readonly int EscortRequestTicks = 250;

		[Desc("ENG-T (maintainer 2026-09-30): percent of stealth infiltrations (a building in the enemy base) that ask an",
			"IBotCaptureTransportProvider to carry the engineer in (APC, transport helicopter) along a route around the enemy;",
			"the rest go on foot. 0 = never (and no random number is drawn). The A/B candidate sets 25.")]
		public readonly int TransportChance = 0;

		[Desc("ENG-T: most engineers (and buildings) in one infiltration run — one per stop.")]
		public readonly int TransportRunMax = 5;

		[Desc("TC-2e (AI_ARCHITECTURE §12.17): yield a capture target an outranking allied bot already claims",
			"(published on the team blackboard — lower ClientIndex wins), and stand an in-flight capture down",
			"when an outranking ally's claim lands on its cell. Inert in 1v1 — no allied broadcasts exist.")]
		public readonly bool UseTeamCaptureClaims = false;

		[Desc("BF-2 (AI_ARCHITECTURE §12.26): prefer capture targets in the caller's deterministic",
			"shard (hash of the target cell mod team size) — two allies picking the same building",
			"inside one snapshot interval can't be arbitrated by an unpublished claim. Orders, never",
			"filters: out-of-shard targets stay eligible once the own tier is exhausted.")]
		public readonly bool PreferShardCaptureTargets = false;

		public override object Create(ActorInitializer init) { return new EngineerBotModule(init.Self, this); }
	}

	public enum EngineerJob { Capture, RepairBridge, RepairBuilding }

	public enum EngineerCheck { Working, Done, Stuck, Gone }

	public class EngineerBotModule : ConditionalTrait<EngineerBotModuleInfo>, IBotTick, IBotPositionsUpdated, IGameSaveTraitData,
		IBotProtectionRequestProvider, IBotCaptureClaimSource
	{
		const string LeaseOwner = nameof(EngineerBotModule);

		sealed class Assignment
		{
			public EngineerJob Job;
			public int OrderedTick;
			public int SampleTick;
			public WPos SamplePos;
			public Actor Target;
			public string MissionId;
			public int Attempt;
			public bool ViaTransport;
			public List<CPos> Route;
		}

		readonly World world;
		readonly OpenRA.Player player;
		readonly int maximumCaptureTargetOptions;
		readonly EngineerJob[] repairJobs;
		readonly HashSet<string> capturingTypes;
		readonly HashSet<string> priorityCapturableTypes;
		readonly HashSet<string> capturableTypes;
		readonly Dictionary<Actor, Assignment> assigned = [];
		readonly Dictionary<Actor, int> stuckUntil = [];
		readonly IBotRequestUnitProduction[] unitBuilders;
		readonly Dictionary<string, int> missionAttempts = [];
		readonly Dictionary<string, int> missionFailStreak = [];
		readonly Dictionary<string, int> missionRetreatStreak = [];
		readonly Dictionary<string, int> dormantUntil = [];

		// The one escorted capture in progress: the mission waits (no attempt) until the escort holds the target area.
		sealed class EscortPlan
		{
			public Actor Target;
			public string MissionId;
			public int SinceTick;
			public int DefenceValue;
			public int InitialDefenceValue;
			public bool Committed;
		}

		EscortPlan escort;

		// The squad manager serves a protection request only at or above its PrepositionMinThreatValue: a request valued at
		// a few riflemen (the first flag-on match published 440-1000) is dropped in silence. Read the bar from the squad
		// managers on this player (Info-level, fixed for the match) instead of copying the number.
		int escortRequestFloor = -1;

		int EscortRequestFloor() =>
			escortRequestFloor >= 0 ? escortRequestFloor
				: escortRequestFloor = player.PlayerActor.Info.TraitInfos<SquadManagerBotModuleCAInfo>()
					.Select(i => i.PrepositionMinThreatValue).DefaultIfEmpty(0).Max();

		/// <summary>The request value, free of world state so it can be tested: the defenders' value, never below the bar
		/// the squad manager serves requests at.</summary>
		public static int EscortRequestValue(int defenceValue, int floor) => Math.Max(Math.Max(1, defenceValue), floor);

		int captureTicks;
		int routeRecheckCountdown;
		int repairTicks;
		int nextRepairJob;
		int housekeptTick = -1;
		CPos initialBaseCenter;

		// Telemetry (debug.log). SkippedClaimed counts evaluations that left an idle engineer alone because another
		// module holds it — each is a chance for the order pair that used to collide.
		public int CaptureOrders { get; private set; }
		public int BridgeOrders { get; private set; }
		public int BuildingRepairOrders { get; private set; }
		public int StuckStops { get; private set; }
		public int SkippedClaimed { get; private set; }

		/// <summary>Capture targets passed over because even the safest route was too exposed.</summary>
		public int UnsafeRoutes { get; private set; }

		/// <summary>Routed captures whose remaining route turned exposed and were given a fresh safe route.</summary>
		public int Reroutes { get; private set; }

		/// <summary>Routed captures pulled back to the base because no safe route remained.</summary>
		public int Pullbacks { get; private set; }

		/// <summary>Stealth targets passed over because more than StealthMaxDefenders armed enemies guard them.</summary>
		public int GuardedSkips { get; private set; }

		/// <summary>Capture attempts stood down to an outranking ally's published claim, plus denied escort plans (TC-2e).</summary>
		public int SupersededCaptures { get; private set; }

		// TC-2e (AI_ARCHITECTURE §12.17): the live capture missions' target cell centres — repair and
		// bridge jobs are not claims. A waiting escort plan counts: it already holds its target.
		public IReadOnlyList<WPos> CaptureClaimPositions
		{
			get
			{
				var positions = new List<WPos>();
				foreach (var job in assigned.Values)
					if (job.Job == EngineerJob.Capture && job.Target != null)
						positions.Add(world.Map.CenterOfCell(job.Target.Location));

				if (escort?.Target != null)
					positions.Add(world.Map.CenterOfCell(escort.Target.Location));

				return positions;
			}
		}

		public EngineerBotModule(Actor self, EngineerBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			maximumCaptureTargetOptions = Math.Max(1, info.MaximumCaptureTargetOptions);

			var shared = self.Info.TraitInfos<CaptureManagerBotModuleCAInfo>().FirstOrDefault();
			capturingTypes = info.CapturingActorTypes.Count > 0 || shared == null ? info.CapturingActorTypes : shared.CapturingActorTypes;
			priorityCapturableTypes = info.PriorityCapturableActorTypes.Count > 0 || shared == null ? info.PriorityCapturableActorTypes : shared.PriorityCapturableActorTypes;
			capturableTypes = info.CapturableActorTypes.Count > 0 || shared == null ? info.CapturableActorTypes : shared.CapturableActorTypes;

			var jobs = new List<EngineerJob>();

			// One owner per decision (architecture audit): when the dedicated CN bridge module is
			// enabled on this actor (cn3_bridge_repair), it owns hut repair — Engineer keeps the job
			// only as its fallback. TraitsImplementing is safe here; unitBuilders below does the same.
			if (info.RepairableHutActorTypes.Count > 0
				&& !self.TraitsImplementing<BridgeRepairBotModule>().Any(t => !t.IsTraitDisabled))
				jobs.Add(EngineerJob.RepairBridge);
			if (info.RepairableActorTypes.Count > 0)
				jobs.Add(EngineerJob.RepairBuilding);
			repairJobs = jobs.ToArray();

			unitBuilders = self.TraitsImplementing<IBotRequestUnitProduction>().ToArray();
		}

		protected override void TraitEnabled(Actor self)
		{
			// Avoid all AIs reevaluating on the same tick (both parents do this).
			captureTicks = world.LocalRandom.Next(Info.MinimumCaptureDelay);
			repairTicks = world.LocalRandom.Next(Info.AssignRoleDelay);
		}

		void IBotPositionsUpdated.UpdatedBaseCenter(CPos newLocation) { initialBaseCenter = newLocation; }

		void IBotPositionsUpdated.UpdatedDefenseCenter(CPos newLocation) { }

		/// <summary>What happened to an engineer this module ordered. Free of world state so it can be tested.</summary>
		public static EngineerCheck Check(bool gone, bool idle, bool moving, bool movedSinceSample,
			int ticksSinceOrder, int ticksSinceSample, int graceTicks, int sampleTicks)
		{
			if (gone)
				return EngineerCheck.Gone;

			// A queued order reaches the unit a few ticks late: an engineer idle inside the grace is still on its way.
			if (idle)
				return ticksSinceOrder >= graceTicks ? EngineerCheck.Done : EngineerCheck.Working;

			// The AS stuck rule: moving, yet at the same spot a whole sample interval later.
			if (moving && !movedSinceSample && ticksSinceSample >= sampleTicks && ticksSinceOrder >= graceTicks)
				return EngineerCheck.Stuck;

			return EngineerCheck.Working;
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (player.WinState != WinState.Undefined)
				return;

			if (--repairTicks <= 0)
			{
				repairTicks = Info.AssignRoleDelay;
				if (repairJobs.Length > 0)
				{
					Housekeep(bot);
					var job = repairJobs[nextRepairJob];
					nextRepairJob = (nextRepairJob + 1) % repairJobs.Length;
					if (job == EngineerJob.RepairBridge)
						QueueRepairBridgeOrder(bot);
					else
						QueueRepairBuildingOrder(bot);
				}
			}

			if (Info.RouteRecheckTicks > 0 && Info.MaxExposedRouteCells >= 0 && --routeRecheckCountdown <= 0)
			{
				routeRecheckCountdown = Info.RouteRecheckTicks;
				var tick = world.WorldTick;
				var leases = BotUnitLeases.Of(player);
				foreach (var (a, job) in assigned.ToList())
					if (job.Route != null && !job.ViaTransport && job.Job == EngineerJob.Capture && !IsGone(a))
						Recheck(bot, leases, a, job, tick);
			}

			if (--captureTicks <= 0)
			{
				captureTicks = Info.MinimumCaptureDelay;
				Housekeep(bot);
				QueueCaptureOrders(bot);
			}
		}

		bool IsGone(Actor a) => a.IsDead || !a.IsInWorld || a.Owner != player;

		/// <summary>Renew the leases of working engineers, release finished ones, stop stuck ones. Once per tick.</summary>
		void Housekeep(IBot bot)
		{
			var tick = world.WorldTick;
			if (housekeptTick == tick)
				return;

			housekeptTick = tick;
			HousekeepEscort(tick);
			var leases = BotUnitLeases.Of(player);
			foreach (var (a, job) in assigned.ToList())
			{
				// ENG-T: a passenger is out of the world while it rides, so the normal checks would read it as gone.
				if (job.ViaTransport)
				{
					var provider = TransportProvider();
					if (provider != null && provider.TryConsumeDelivered(a, out var delivered))
					{
						job.ViaTransport = false;
						job.OrderedTick = job.SampleTick = tick;
						job.SamplePos = a.CenterPosition;
						var t = delivered ?? job.Target;
						bot.QueueOrder(new Order("CaptureActor", a, Target.FromActor(t), true));
						BotMissionLog.Write(new BotMissionRecord
						{
							Player = player, MissionId = job.MissionId, Attempt = job.Attempt, State = BotMissionAttemptState.Progressing,
							Executor = "Engineers", MissionType = "capture", TargetCell = t.Location, Units = 1
						});
						BotUnitLeases.TryClaim(leases, a, LeaseOwner, BotLeasePurpose.Capture, Info.LeaseTicks);
						continue;
					}

					if (provider != null && provider.IsHandlingPassenger(a))
					{
						// §19.6: the run hands each passenger's lease to the provider for the ride —
						// renew ours only once it is back or free, so housekeeping isn't a refused
						// claim against the transport module on every pass.
						if (!BotUnitLeases.IsClaimedByOther(leases, a, LeaseOwner))
							BotUnitLeases.TryClaim(leases, a, LeaseOwner, BotLeasePurpose.Capture, Info.LeaseTicks);
						continue;
					}

					// Dropped by the provider (or no provider any more): from here the normal checks decide.
					job.ViaTransport = false;
					job.OrderedTick = tick;
				}

				var moving = !IsGone(a) && a.CurrentActivity?.ChildActivity?.ActivityType == ActivityType.Move;
				var check = Check(IsGone(a), !IsGone(a) && a.IsIdle, moving, IsGone(a) || a.CenterPosition != job.SamplePos,
					tick - job.OrderedTick, tick - job.SampleTick, Info.OrderGraceTicks, Info.AssignRoleDelay);

				switch (check)
				{
					case EngineerCheck.Gone:
						assigned.Remove(a);
						EndMission(a, job, check);
						break;
					case EngineerCheck.Done:
						assigned.Remove(a);
						leases?.Release(a, LeaseOwner);
						EndMission(a, job, check);
						break;
					case EngineerCheck.Stuck:
						assigned.Remove(a);
						EndMission(a, job, check);
						stuckUntil[a] = tick + Info.StuckRetryTicks;
						StuckStops++;

						// Order before release: a Stop issued while the lease is still held reads as the
						// claim's own last act at the order gate; releasing first would leave the Stop
						// unattributed and the next module's order counted crossed (GC-1 StandDownWalkers).
						bot.QueueOrder(new Order("Stop", a, false));
						leases?.Release(a, LeaseOwner);
						Log.Write("debug", $"AI ({player.ClientIndex}): ENG stuck {a.Info.Name} {a.ActorID} on {job.Job}, stopped and released (tick {tick})");
						break;
					default:
						BotUnitLeases.TryClaim(leases, a, LeaseOwner, PurposeOf(job.Job), Info.LeaseTicks);
						if (tick - job.SampleTick >= Info.AssignRoleDelay)
						{
							job.SampleTick = tick;
							job.SamplePos = a.CenterPosition;
						}

						break;
				}
			}

			foreach (var a in stuckUntil.Where(kv => kv.Value <= tick || IsGone(kv.Key)).Select(kv => kv.Key).ToList())
				stuckUntil.Remove(a);
		}

		/// <summary>Re-scores the remaining route of a walking engineer. Returns true when the attempt ended (pull back).</summary>
		bool Recheck(IBot bot, IBotUnitLeases leases, Actor a, Assignment job, int tick)
		{
			var target = job.Target;
			if (target == null || target.IsDead || !target.IsInWorld || job.Job != EngineerJob.Capture)
				return false;

			var remaining = RemainingExposure(job.Route, a.Location, target.Location, Info.ApproachCells, c => Danger(a, c));
			if (remaining <= Info.MaxExposedRouteCells)
				return false;

			var fresh = SafeRoute(a, target);
			if (fresh != null && ExposedCells(fresh.Select(c => (c, Danger(a, c))), target.Location, Info.ApproachCells) <= Info.MaxExposedRouteCells)
			{
				var waypoints = Waypoints(fresh, Info.RouteWaypointSpacing, Info.ApproachCells, target.Location);
				for (var i = 0; i < waypoints.Count; i++)
					bot.QueueOrder(new Order("Move", a, Target.FromCell(world, waypoints[i]), i > 0));

				bot.QueueOrder(new Order("CaptureActor", a, Target.FromActor(target), waypoints.Count > 0));
				job.Route = fresh;
				job.OrderedTick = job.SampleTick = tick;
				job.SamplePos = a.CenterPosition;
				Reroutes++;
				BotUnitLeases.TryClaim(leases, a, LeaseOwner, BotLeasePurpose.Capture, Info.LeaseTicks);
				Log.Write("debug", $"AI ({player.ClientIndex}): ENG reroute {a.Info.Name} {a.ActorID} -> {target.Info.Name} {target.ActorID}: {remaining} exposed cells ahead > {Info.MaxExposedRouteCells} (tick {tick}; reroutes {Reroutes}, pullbacks {Pullbacks})");
				return false;
			}

			assigned.Remove(a);
			bot.QueueOrder(new Order("Move", a, Target.FromCell(world, initialBaseCenter), false));
			leases?.Release(a, LeaseOwner);
			EndMission(a, job, EngineerCheck.Working, true);
			Pullbacks++;
			Log.Write("debug", $"AI ({player.ClientIndex}): ENG pullback {a.Info.Name} {a.ActorID} from {target.Info.Name} {target.ActorID}: {remaining} exposed cells ahead, no safe route (tick {tick}; reroutes {Reroutes}, pullbacks {Pullbacks})");
			return true;
		}

		/// <summary>Exposed cells still AHEAD of the engineer: the route cells after the one nearest its cell, outside the
		/// approach of the target. Free of world state so it can be tested.</summary>
		public static int RemainingExposure(IReadOnlyList<CPos> route, CPos engineerCell, CPos target, int approachCells, Func<CPos, int> danger)
		{
			if (route == null || route.Count == 0)
				return 0;

			var at = 0;
			for (var i = 1; i < route.Count; i++)
				if ((route[i] - engineerCell).LengthSquared < (route[at] - engineerCell).LengthSquared)
					at = i;

			var count = 0;
			for (var i = at + 1; i < route.Count; i++)
				if ((route[i] - target).LengthSquared > approachCells * approachCells && danger(route[i]) > 0)
					count++;

			return count;
		}

		/// <summary>The stealth gate, free of world state so it can be tested: guarded when more than `max` defenders (-1 = off).</summary>
		public static bool StealthGuarded(int defenders, int max) => max >= 0 && defenders > max;

		/// <summary>RankTargetsBySafety's score (higher is better), free of world state so it can be tested: value per cell
		/// of effective cost, each exposed cell costing `exposureWeight` cells of walking.</summary>
		public static double RankScore(int value, int distanceCells, int exposedCells, int exposureWeight) =>
			(double)Math.Max(0, value) / (1 + Math.Max(0, distanceCells) + (long)Math.Max(0, exposureWeight) * Math.Max(0, exposedCells));

		int GuardingEnemies(Actor capturer, Actor target) =>
			world.FindActorsInCircle(target.CenterPosition, Info.EnemyAvoidanceRadius)
				.Count(u => !u.IsDead && u.IsInWorld && player.RelationshipWith(u.Owner) == PlayerRelationship.Enemy
					&& u.Info.HasTraitInfo<AttackBaseInfo>() && capturer.IsTargetableBy(u));

		/// <summary>Orders the try-candidates by RankScore over the nearest CaptureTargetTries x 2 (the rest are dropped).</summary>
		List<Actor> RankBySafety(Actor capturer, IEnumerable<Actor> candidates)
		{
			var tries = Math.Max(1, Info.CaptureTargetTries);
			return candidates.OrderBy(t => (t.CenterPosition - capturer.CenterPosition).LengthSquared)
				.Take(tries * 2)
				.Select(t =>
				{
					var route = SafeRoute(capturer, t);
					var exposed = route == null ? int.MaxValue / 2 : ExposedCells(route.Select(c => (c, Danger(capturer, c))), t.Location, Info.ApproachCells);
					return (Target: t, Score: RankScore(t.GetSellValue(), (t.Location - capturer.Location).Length, exposed, Info.ExposureWeight));
				})
				.OrderByDescending(x => x.Score)
				.Take(tries)
				.Select(x => x.Target)
				.ToList();
		}

		/// <summary>FB2: how many capturers the safe-target count justifies (Frans
		/// DemandTargetsPerCapturer / MaximumDemandCapturers). Static for tests.</summary>
		public static int DemandCapturersDesired(int safeTargets, int maximum, int targetsPerCapturer) =>
			Math.Min(Math.Max(0, maximum), Math.Max(0, safeTargets) / Math.Max(1, targetsPerCapturer));

		// FB2 (Frans SpecOps, DESIGN §19.5 omniscient-owner exemption applies to the same scans the
		// assign path already runs): count the safe capturable targets across EVERY capturable owner —
		// the assign path picks one random owner because one attempt needs one target, but demand is a
		// production question and must see the whole opportunity set deterministically. "Safe" reuses
		// the assign path's own gates (full / dormant / escort-blocked); route and guard checks still
		// apply when a real engineer is dispatched.
		void DemandCapturers(IBot bot, int liveCapturers)
		{
			if (liveCapturers >= Math.Max(0, Info.MaximumDemandCapturers))
				return;

			var targets = world.Actors.Where(a => !a.IsDead && a.IsInWorld
				&& Info.CapturableRelationships.HasRelationship(player.RelationshipWith(a.Owner))
				&& a.TraitOrDefault<CaptureManager>() != null);
			if (Info.CheckCaptureTargetsForVisibility)
				targets = targets.Where(a => a.CanBeViewedByPlayer(player));
			if (capturableTypes.Count > 0)
				targets = targets.Where(t => capturableTypes.Contains(t.Info.Name.ToLowerInvariant()));

			var safeTargets = targets.Count(t => !TargetFull(t) && !Dormant(t) && !BlockedByEscort(t));
			if (liveCapturers < DemandCapturersDesired(safeTargets, Info.MaximumDemandCapturers, Info.DemandTargetsPerCapturer))
				RequestCapturer(bot);
		}

		// ScoutBotModule.RequestScout's contract verbatim: ordinal-sorted names, skip anything a builder
		// already queued or no queue of this faction can build, request the first buildable capturer type.
		void RequestCapturer(IBot bot)
		{
			foreach (var name in capturingTypes.OrderBy(n => n, StringComparer.Ordinal))
			{
				var builder = unitBuilders.FirstOrDefault(b => b.RequestedProductionCount(bot, name) == 0);
				if (builder == null)
					continue;

				// Unloaded ContentPacks leave their actor names out of Rules.Actors; TryGetValue is load-bearing.
				if (!world.Map.Rules.Actors.TryGetValue(name, out var actorInfo))
					continue;
				if (actorInfo?.TraitInfoOrDefault<BuildableInfo>() is not { } buildable)
					continue;
				if (!buildable.Queue.Any(q => OpenRA.Mods.CA.AIUtils.FindQueues(player, q).Any(pq => pq.BuildableItems().Any(b => b.Name == name))))
					continue;

				builder.RequestUnitProduction(bot, name);
				return;
			}
		}

		static BotLeasePurpose PurposeOf(EngineerJob job) => job == EngineerJob.Capture ? BotLeasePurpose.Capture : BotLeasePurpose.Engineer;

		/// <summary>An engineer this module may order now: ours, idle, not already on a job, not benched, not held by another module.</summary>
		bool Available(Actor a, IBotUnitLeases leases, bool allowFlyIdle)
		{
			if (IsGone(a) || assigned.ContainsKey(a) || stuckUntil.ContainsKey(a))
				return false;

			if (!(a.IsIdle || (allowFlyIdle && a.CurrentActivity is FlyIdle)))
				return false;

			if (BotUnitLeases.IsClaimedByOther(leases, a, LeaseOwner))
			{
				SkippedClaimed++;
				return false;
			}

			return true;
		}

		bool Assign(IBot bot, IBotUnitLeases leases, Actor engineer, EngineerJob job, Order order, Actor target,
			IReadOnlyList<CPos> waypoints = null, List<CPos> route = null)
		{
			if (!BotUnitLeases.TryClaim(leases, engineer, LeaseOwner, PurposeOf(job), Info.LeaseTicks))
				return false;

			var tick = world.WorldTick;
			var assignment = new Assignment { Job = job, OrderedTick = tick, SampleTick = tick, SamplePos = engineer.CenterPosition, Target = target, Route = route };
			assigned[engineer] = assignment;
			if (waypoints != null && waypoints.Count > 0)
			{
				// Walk the safe route: the first leg replaces whatever the engineer was doing, the rest queue behind it,
				// and the capture order (queued) follows the last waypoint.
				for (var i = 0; i < waypoints.Count; i++)
					bot.QueueOrder(new Order("Move", engineer, Target.FromCell(world, waypoints[i]), i > 0));
			}

			bot.QueueOrder(order);
			if (job == EngineerJob.Capture)
			{
				StartMission(assignment, engineer);
				if (escort != null && escort.Target == target)
					escort.Committed = true;
			}

			switch (job)
			{
				case EngineerJob.Capture: CaptureOrders++; break;
				case EngineerJob.RepairBridge: BridgeOrders++; break;
				default: BuildingRepairOrders++; break;
			}

			Log.Write("debug", $"AI ({player.ClientIndex}): ENG {job} {engineer.Info.Name} {engineer.ActorID} -> {target.Info.Name} {target.ActorID} (tick {tick}; captures {CaptureOrders}, bridges {BridgeOrders}, repairs {BuildingRepairOrders}, stuck {StuckStops}, skipped-claimed {SkippedClaimed})");
			return true;
		}

		void QueueCaptureOrders(IBot bot)
		{
			if (capturingTypes.Count == 0)
				return;

			var leases = BotUnitLeases.Of(player);

			// TC-2e (AI_ARCHITECTURE §12.17): the cells outranking allied bots already claim, off the team
			// blackboard — one read per evaluation. Flag off or 1v1 leaves null and every gate below is the
			// no-op it is today.
			HashSet<WPos> claimsAhead = null;
			if (Info.UseTeamCaptureClaims)
				claimsAhead = TeamBlackboard.ClaimsAheadOf(TeamBlackboard.CollectBroadcasts(player), player.InternalName);

			bool ClaimedByOutrankingAlly(Actor target) =>
				claimsAhead != null && claimsAhead.Contains(world.Map.CenterOfCell(target.Location));

			// BF-2 (AI_ARCHITECTURE §12.26): the deterministic shard tier — in-shard targets sort
			// first, out-of-shard stays eligible after them. Size 1 makes every tier 0, the no-op.
			var shardSize = 1;
			var shardRank = 0;
			if (Info.PreferShardCaptureTargets)
				(shardRank, shardSize) = TeamBlackboard.ClaimRank(player);

			int ShardTier(Actor target) =>
				shardSize <= 1 ? 0 : (TeamBlackboard.CaptureShard(target.Location, shardSize) == shardRank ? 0 : 1);

			if (claimsAhead != null && claimsAhead.Count > 0)
			{
				// Stand down an in-flight capture whose target an outranking ally now claims — the same
				// release path as a finished job (unassigned, mission ended, lease out) plus a Stop.
				foreach (var (a, job) in assigned.ToList())
				{
					if (job.Job != EngineerJob.Capture || job.Target == null || !ClaimedByOutrankingAlly(job.Target))
						continue;

					assigned.Remove(a);
					EndMission(a, job, EngineerCheck.Working, superseded: true);
					SupersededCaptures++;

					// Order before release (same shape as the Stuck path above).
					bot.QueueOrder(new Order("Stop", a, false));
					leases?.Release(a, LeaseOwner);
					Log.Write("debug", $"AI ({player.ClientIndex}): ENG capture superseded {a.Info.Name} {a.ActorID} -> {job.Target.Info.Name} {job.Target.ActorID} (tick {world.WorldTick}; superseded {SupersededCaptures})");
				}

				// The waiting escort plan is the same claim without a walking engineer — deny it too.
				// (A committed plan is ended by the stand-down above through its MissionId.)
				if (escort != null && escort.Target != null && ClaimedByOutrankingAlly(escort.Target))
				{
					BotMissionLog.Write(new BotMissionRecord
					{
						Player = player, MissionId = escort.MissionId, Event = BotMissionEvent.Denied, Reason = BotMissionReasons.Superseded,
						Executor = "Engineers", MissionType = "capture", TargetCell = escort.Target.Location, Value = escort.DefenceValue
					});
					SupersededCaptures++;
					escort = null;
				}
			}

			var capturers = world.ActorsHavingTrait<Captures>()
				.Where(a => a.Owner == player && capturingTypes.Contains(a.Info.Name.ToLowerInvariant()))
				.Select(a => new TraitPair<CaptureManager>(a, a.TraitOrDefault<CaptureManager>()))
				.Where(tp => tp.Trait != null)
				.ToList();
			var liveCapturers = capturers.Count;
			capturers = capturers.Where(tp => Available(tp.Actor, leases, false)).ToList();

			// FB2: safe targets justify building a specialist even when none is available — without
			// this, the first capturer only ever appears by unit-mix luck (the enumeration above is
			// the module's own-units scan; the demand count includes assigned and riding engineers).
			if (Info.UseDemandCapturers)
				DemandCapturers(bot, liveCapturers);

			if (capturers.Count == 0)
				return;

			var next = 0;
			var baseCenter = world.Map.CenterOfCell(initialBaseCenter);

			if (world.LocalRandom.Next(100) < Info.PriorityCaptureChance)
			{
				var priorityTargets = world.Actors.Where(a =>
					!a.IsDead && a.IsInWorld && Info.CapturableRelationships.HasRelationship(player.RelationshipWith(a.Owner))
					&& priorityCapturableTypes.Contains(a.Info.Name.ToLowerInvariant()));

				// DESIGN §19.5: the engineer owner's fog exception.
				if (Info.CheckCaptureTargetsForVisibility)
					priorityTargets = priorityTargets.Where(a => a.CanBeViewedByPlayer(player));

				var candidates = priorityTargets.Where(t => !TargetFull(t) && !Dormant(t) && !ClaimedByOutrankingAlly(t)).OrderBy(ShardTier).ThenBy(a => (a.CenterPosition - baseCenter).LengthSquared).ToList();
				ConsiderEscort(candidates);
				var ordered = candidates.Where(t => !BlockedByEscort(t)).ToList();

				// As the CA parent: each attempt uses up a target; a capturer is used up only when it is sent.
				var attempts = Math.Min(capturers.Count, ordered.Count);
				for (var i = 0; i < attempts && next < capturers.Count; i++)
				{
					var capturer = capturers[next];
					var target = ordered[i];
					var captureManager = target.TraitOrDefault<CaptureManager>();
					if (captureManager != null && capturer.Trait.CanTarget(captureManager) && TryRoute(capturer.Actor, target, out var waypoints, out var fullRoute)
						&& Assign(bot, leases, capturer.Actor, EngineerJob.Capture, new Order("CaptureActor", capturer.Actor, Target.FromActor(target), true), target, waypoints, fullRoute))
						next++;
				}

				if (next >= capturers.Count)
					return;
			}

			var randPlayers = world.Players.Where(p => !p.Spectating
				&& Info.CapturableRelationships.HasRelationship(player.RelationshipWith(p))).ToList();
			if (randPlayers.Count == 0)
				return;

			var randPlayer = randPlayers.Random(world.LocalRandom);
			var remaining = capturers.Skip(next).ToList();

			var options = world.Actors.Where(a => a.Owner == randPlayer && !a.IsDead && a.IsInWorld);
			if (Info.CheckCaptureTargetsForVisibility)
				options = options.Where(a => a.CanBeViewedByPlayer(player));

			var capturable = options
				.Where(target =>
				{
					var captureManager = target.TraitOrDefault<CaptureManager>();
					return captureManager != null && remaining.Any(tp => tp.Trait.CanTarget(captureManager));
				})
				.OrderBy(ShardTier).ThenByDescending(target => target.GetSellValue())
				.Take(maximumCaptureTargetOptions);

			if (capturableTypes.Count > 0)
				capturable = capturable.Where(target => capturableTypes.Contains(target.Info.Name.ToLowerInvariant()));

			var targets = capturable.Where(t => !ClaimedByOutrankingAlly(t)).ToList();
			if (targets.Count == 0)
				return;

			for (var ci = 0; ci < remaining.Count; ci++)
			{
				var capturer = remaining[ci];
				ConsiderEscort(targets.Where(t => !TargetFull(t) && !Dormant(t)).OrderBy(ShardTier).ThenByDescending(t => t.GetSellValue()));

				// Nearest first. A full, dormant, escort-blocked or unsafe target passes the engineer on to the next one, so
				// with MaxEngineersPerTarget 1 engineers spread over DIFFERENT targets (TargetFull is re-read per engineer:
				// the previous engineer's Assign already counts). CaptureTargetTries 1 = the parents' single nearest target.
			var open = targets.Where(t => !TargetFull(t) && !Dormant(t) && !BlockedByEscort(t));
				var tries = Info.RankTargetsBySafety
					? RankBySafety(capturer.Actor, open)
					: open.OrderBy(ShardTier).ThenBy(t => (t.CenterPosition - capturer.Actor.CenterPosition).LengthSquared)
						.Take(Math.Max(1, Info.CaptureTargetTries))
						.ToList();
				foreach (var target in tries)
				{
					if (StealthTargetGuarded(capturer.Actor, target))
						continue;

					// ENG-T: sometimes a stealth infiltration rides in. Transport answers a hot or missing ground route,
					// so the roll precedes the route check; the provider plans its own way in, and a refused run falls
					// through to the foot path. The roll is drawn only when it can matter, so a chance of 0 leaves
					// LocalRandom's sequence — and every later random choice — exactly as before.
					if (Info.TransportChance > 0 && !EscortEligible(target)
						&& WantsTransport(true, world.LocalRandom.Next(100), Info.TransportChance)
						&& TransportProvider() is IBotCaptureTransportProvider provider)
					{
						var used = TryTransportRun(bot, leases, remaining.Skip(ci).Select(tp => tp.Actor).ToList(), target, targets, provider);
						if (used > 0)
						{
							ci += used - 1;
							break;
						}
					}

					if (!TryRoute(capturer.Actor, target, out var waypoints, out var fullRoute))
						continue;

					Assign(bot, leases, capturer.Actor, EngineerJob.Capture, new Order("CaptureActor", capturer.Actor, Target.FromActor(target), true), target, waypoints, fullRoute);
					break;
				}
			}
		}

		/// <summary>ENG-T's gate, free of world state so it can be tested.</summary>
		public static bool WantsTransport(bool stealthTarget, int roll, int chancePct) => stealthTarget && chancePct > 0 && roll < chancePct;

		/// <summary>The enabled transport provider, resolved at use (never cached: LC4's bug class).</summary>
		IBotCaptureTransportProvider TransportProvider() =>
			player.PlayerActor.TraitsImplementing<IBotCaptureTransportProvider>().FirstOrDefault(p => p is not IDisabledTrait d || !d.IsTraitDisabled);

		/// <summary>The visiting order of a run, free of world state so it can be tested: start at `start`, then always the
		/// nearest unvisited stop (squared cell distance), at most `max` stops.</summary>
		public static List<int> GreedyRoute(IReadOnlyList<CPos> stops, int start, int max)
		{
			var route = new List<int> { start };
			var left = Enumerable.Range(0, stops.Count).Where(i => i != start).ToList();
			while (route.Count < max && left.Count > 0)
			{
				var from = stops[route[^1]];
				var next = left.MinBy(i => (stops[i] - from).LengthSquared);
				route.Add(next);
				left.Remove(next);
			}

			return route;
		}

		/// <summary>ENG-T: one run of up to TransportRunMax engineers, one per stealth building; returns the engineers used.</summary>
		int TryTransportRun(IBot bot, IBotUnitLeases leases, List<Actor> candidates, Actor first, List<Actor> pool, IBotCaptureTransportProvider provider)
		{
			// The stops: the chosen building, then other stealth buildings that are free for an attempt.
			var stops = new List<Actor> { first };
			stops.AddRange(pool.Where(t => t != first && !TargetFull(t) && !Dormant(t) && !EscortEligible(t)));
			var order = GreedyRoute(stops.Select(t => t.Location).ToList(), 0, Math.Min(Info.TransportRunMax, candidates.Count));

			var passengers = new List<Actor>();
			var targets = new List<Actor>();
			foreach (var engineer in candidates)
			{
				if (passengers.Count == order.Count)
					break;

				if (!BotUnitLeases.TryClaim(leases, engineer, LeaseOwner, BotLeasePurpose.Capture, Info.LeaseTicks))
					continue;

				passengers.Add(engineer);
				targets.Add(stops[order[passengers.Count - 1]]);
			}

			if (passengers.Count == 0 || !provider.TryRequestCaptureRun(bot, passengers, targets))
			{
				foreach (var p in passengers)
					leases?.Release(p, LeaseOwner);

				return 0;
			}

			var tick = world.WorldTick;
			for (var k = 0; k < passengers.Count; k++)
			{
				var job = new Assignment
				{
					Job = EngineerJob.Capture, OrderedTick = tick, SampleTick = tick, SamplePos = passengers[k].CenterPosition,
					Target = targets[k], ViaTransport = true
				};
				assigned[passengers[k]] = job;
				CaptureOrders++;
				StartMission(job, passengers[k], "Transport");
			}

			Log.Write("debug", $"AI ({player.ClientIndex}): ENG transport run: {passengers.Count} engineer(s) -> {string.Join(", ", targets.Select(t => $"{t.Info.Name} {t.ActorID}"))} (tick {tick})");

			// The remaining candidates list may skip engineers whose claim failed; the caller advances by the scanned count.
			return candidates.IndexOf(passengers[^1]) + 1;
		}


		/// <summary>
		/// The route gate for one capture. MaxExposedRouteCells &lt; 0: the parents' check (a path exists; no waypoints).
		/// Otherwise the least-exposed path, rejected when too exposed; its waypoints are returned for the order.
		/// </summary>
		/// <summary>The stealth-guard veto, shared by the foot and transport paths: a stealth target ringed by more
		/// than StealthMaxDefenders armed guards is skipped entirely — escorted targets never gate on it.</summary>
		bool StealthTargetGuarded(Actor capturer, Actor target)
		{
			if (Info.StealthMaxDefenders < 0 || EscortEligible(target))
				return false;

			var defenders = GuardingEnemies(capturer, target);
			if (!StealthGuarded(defenders, Info.StealthMaxDefenders))
				return false;

			GuardedSkips++;
			Log.Write("debug", $"AI ({player.ClientIndex}): ENG stealth target {target.Info.Name} {target.ActorID} guarded by {defenders} > {Info.StealthMaxDefenders} (tick {world.WorldTick}; guarded {GuardedSkips})");
			return true;
		}

		bool TryRoute(Actor capturer, Actor target, out IReadOnlyList<CPos> waypoints, out List<CPos> fullRoute)
		{
			waypoints = null;
			fullRoute = null;
			if (Info.MaxExposedRouteCells < 0)
				return SafePath(capturer, target).Type != TargetType.Invalid;

			var route = SafeRoute(capturer, target);
			if (route == null)
				return false;

			var exposed = ExposedCells(route.Select(c => (c, Danger(capturer, c))), target.Location, Info.ApproachCells);
			if (exposed > Info.MaxExposedRouteCells)
			{
				UnsafeRoutes++;
				Log.Write("debug", $"AI ({player.ClientIndex}): ENG route to {target.Info.Name} {target.ActorID} too exposed: {exposed} cells under fire > {Info.MaxExposedRouteCells} (tick {world.WorldTick}; unsafe {UnsafeRoutes})");
				return false;
			}

			waypoints = Waypoints(route, Info.RouteWaypointSpacing, Info.ApproachCells, target.Location);
			fullRoute = route;
			return true;
		}

		/// <summary>Cells of the route within reach of armed enemies, the final approach (within `approachCells` of the
		/// target) excluded. Free of world state so it can be tested.</summary>
		public static int ExposedCells(IEnumerable<(CPos Cell, int Danger)> route, CPos target, int approachCells) =>
			route.Count(c => c.Danger > 0 && (c.Cell - target).LengthSquared > approachCells * approachCells);

		/// <summary>Every `spacing`-th cell of a source-first route, stopping before the final approach (the capture
		/// order walks that part). Free of world state so it can be tested.</summary>
		public static List<CPos> Waypoints(IReadOnlyList<CPos> route, int spacing, int approachCells, CPos target)
		{
			var result = new List<CPos>();
			spacing = Math.Max(1, spacing);
			for (var i = spacing; i < route.Count; i += spacing)
			{
				if ((route[i] - target).LengthSquared <= approachCells * approachCells)
					break;

				result.Add(route[i]);
			}

			return result;
		}

		readonly Dictionary<CPos, int> dangerCache = [];
		int dangerCacheTick = -1;

		// DESIGN §19.5: the engineer owner is omniscient as a whole, so this scan sees through fog. Only ARMED enemies
		// count (the parent counted every actor that could target an engineer's type, harvesters and MCVs included).
		// Cached per tick: one evaluation routes several engineers over the same cells.
		int Danger(Actor capturer, CPos loc)
		{
			if (dangerCacheTick != world.WorldTick)
			{
				dangerCache.Clear();
				dangerCacheTick = world.WorldTick;
			}

			if (dangerCache.TryGetValue(loc, out var d))
				return d;

			var center = world.Map.CenterOfCell(loc);
			var sum = 0L;
			foreach (var u in world.FindActorsInCircle(center, Info.EnemyAvoidanceRadius))
				if (!u.IsDead && capturer.Owner.RelationshipWith(u.Owner) == PlayerRelationship.Enemy
					&& u.Info.HasTraitInfo<AttackBaseInfo>() && capturer.IsTargetableBy(u))
					sum += Math.Max(0, Info.EnemyAvoidanceRadius.Length - (center - u.CenterPosition).Length);

			// Bounded so a long route through a crowded base cannot overflow the path cost.
			return dangerCache[loc] = (int)Math.Min(sum, 1 << 20);
		}

		/// <summary>The least-exposed path from the engineer to a cell next to the target, source first; null when none.</summary>
		List<CPos> SafeRoute(Actor capturer, Actor target)
		{
			var mobile = capturer.TraitOrDefault<Mobile>();
			if (mobile == null || !mobile.PathFinder.PathExistsForLocomotor(mobile.Locomotor, capturer.Location, target.Location))
				return null;

			var footprint = target.OccupiesSpace?.OccupiedCells().Select(c => c.Cell).ToHashSet() ?? [target.Location];
			var ring = new HashSet<CPos>();
			foreach (var c in footprint)
				for (var dx = -1; dx <= 1; dx++)
					for (var dy = -1; dy <= 1; dy++)
					{
						var n = new CPos(c.X + dx, c.Y + dy);
						if (!footprint.Contains(n) && world.Map.Contains(n))
							ring.Add(n);
					}

			var path = mobile.PathFinder.FindPathToTargetCellByPredicate(
				capturer, [capturer.Location], ring.Contains, BlockedByActor.Stationary, loc => Danger(capturer, loc));
			if (path.Count == 0)
				return null;

			// The engine returns paths goal-first.
			if ((path[0] - capturer.Location).LengthSquared > (path[^1] - capturer.Location).LengthSquared)
				path.Reverse();

			return path;
		}

		// CA parent verbatim, kept for MaxExposedRouteCells < 0 (the default until its A/B). It is only a reachability
		// check: the goal predicate `loc => true` matches the start cell, so the danger cost is never scored along any
		// route, and the caller discards the path anyway (maintainer's question, 2026-09-30). SafeRoute is the real one.
		Target SafePath(Actor capturer, Actor target)
		{
			var mobile = capturer.TraitOrDefault<Mobile>();
			if (mobile == null)
				return Target.Invalid;

			var locomotor = mobile.Locomotor;
			if (!mobile.PathFinder.PathExistsForLocomotor(locomotor, capturer.Location, target.Location))
				return Target.Invalid;

			var path = mobile.PathFinder.FindPathToTargetCellByPredicate(
				capturer, new[] { capturer.Location }, loc => true, BlockedByActor.Stationary,
				loc => world.FindActorsInCircle(world.Map.CenterOfCell(loc), Info.EnemyAvoidanceRadius)
					.Where(u => !u.IsDead && capturer.Owner.RelationshipWith(u.Owner) == PlayerRelationship.Enemy && capturer.IsTargetableBy(u))
					.Sum(u => Math.Max(WDist.Zero.Length, Info.EnemyAvoidanceRadius.Length - (world.Map.CenterOfCell(loc) - u.CenterPosition).Length)));

			return path.Count == 0 ? Target.Invalid : Target.FromActor(target);
		}

		void QueueRepairBridgeOrder(IBot bot)
		{
			if (Info.RepairingActorTypes.Count == 0)
				return;

			var leases = BotUnitLeases.Of(player);
			var repairers = world.ActorsHavingTrait<RepairsBridges>()
				.Where(a => a.Owner == player && Info.RepairingActorTypes.Contains(a.Info.Name) && Available(a, leases, true))
				.ToList();

			if (repairers.Count == 0)
				return;

			// Few bridge huts per map, so a list is fine (AS parent).
			var huts = world.ActorsWithTrait<BridgeHut>()
				.Where(at => Info.RepairableHutActorTypes.Contains(at.Actor.Info.Name) && at.Trait.BridgeDamageState >= DamageState.Dead)
				.Select(at => at.Actor).ToList();
			huts.AddRange(world.ActorsWithTrait<LegacyBridgeHut>()
				.Where(at => Info.RepairableHutActorTypes.Contains(at.Actor.Info.Name) && at.Trait.BridgeDamageState >= DamageState.Dead)
				.Select(at => at.Actor));

			if (Info.CheckRepairTargetsForVisibility)
				huts.RemoveAll(h => !h.CanBeViewedByPlayer(player));

			SendOneRepairer(bot, leases, repairers, huts, EngineerJob.RepairBridge, "RepairBridge");
		}

		void QueueRepairBuildingOrder(IBot bot)
		{
			if (Info.RepairingActorTypes.Count == 0)
				return;

			var leases = BotUnitLeases.Of(player);
			var repairers = world.ActorsHavingTrait<InstantlyRepairs>()
				.Where(a => a.Owner == player && Info.RepairingActorTypes.Contains(a.Info.Name) && Available(a, leases, true))
				.ToList();

			if (repairers.Count == 0)
				return;

			// Allied buildings only: the bot knows its own and its allies' base, no fog involved.
			var targets = world.ActorsHavingTrait<InstantlyRepairable>().Where(t =>
			{
				if (!Info.RepairableActorTypes.Contains(t.Info.Name) || t.Owner.RelationshipWith(player) != PlayerRelationship.Ally)
					return false;

				var health = t.TraitOrDefault<IHealth>();
				return health != null && health.DamageState >= Info.RepairableDamageState;
			}).ToList();

			SendOneRepairer(bot, leases, repairers, targets, EngineerJob.RepairBuilding, "InstantRepair");
		}

		/// <summary>AS parent: the first repairer that reaches its nearest target goes; one per evaluation.</summary>
		void SendOneRepairer(IBot bot, IBotUnitLeases leases, List<Actor> repairers, List<Actor> targets, EngineerJob job, string orderString)
		{
			if (targets.Count == 0)
				return;

			foreach (var r in repairers)
			{
				foreach (var target in targets.OrderBy(a => (r.Location - a.Location).LengthSquared))
				{
					if (!AIUtils.PathExist(r, target.Location, target))
						continue;

					if (Assign(bot, leases, r, job, new Order(orderString, r, Target.FromActor(target), true), target))
						return;

					break;
				}
			}
		}

		/// <summary>The escort rule, free of world state so it can be tested: an undefended target needs no escort;
		/// otherwise our armed value near it must reach `superiorityPct` percent of the defenders'.</summary>
		public static bool EscortReady(int ownValue, int defenceValue, int superiorityPct) =>
			defenceValue <= 0 || (long)ownValue * 100 >= (long)defenceValue * superiorityPct;

		/// <summary>Superiority AND thinning: the defenders must also have fallen to `thinnedPct` percent of their value
		/// at publish. Free of world state so it can be tested.</summary>
		public static bool EscortReady(int ownValue, int defenceValue, int initialDefenceValue, int superiorityPct, int thinnedPct) =>
			defenceValue <= 0 || (EscortReady(ownValue, defenceValue, superiorityPct)
				&& (long)defenceValue * 100 <= (long)Math.Max(defenceValue, initialDefenceValue) * thinnedPct);

		static int CostOf(Actor a) => a.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0;

		// DESIGN §19.5: the engineer owner is omniscient as a whole (maintainer 2026-09-30) — these scans see through fog.
		int DefenceValue(Actor target) =>
			world.FindActorsInCircle(target.CenterPosition, Info.EnemyAvoidanceRadius)
				.Where(u => !u.IsDead && u.IsInWorld && player.RelationshipWith(u.Owner) == PlayerRelationship.Enemy
					&& u.Info.HasTraitInfo<AttackBaseInfo>())
				.Sum(CostOf);

		int OwnArmedValueNear(Actor target) =>
			world.FindActorsInCircle(target.CenterPosition, Info.EnemyAvoidanceRadius)
				.Where(u => !u.IsDead && u.IsInWorld && u.Owner == player && u.Info.HasTraitInfo<AttackBaseInfo>()
					&& !u.Info.HasTraitInfo<BuildingInfo>())
				.Sum(CostOf);

		/// <summary>
		/// Maintainer 2026-09-30: escorts are ONLY for tech buildings (neutral, or a PriorityCapturableActorTypes
		/// entry) in an unsafe area. A building in the enemy's base is taken by stealth — an escort would give the
		/// engineer away — so it is never escorted: the engineer sneaks in alone along SafePath.
		/// </summary>
		public static bool EscortEligible(bool enemyOwned, bool priorityType) => priorityType || !enemyOwned;

		bool EscortEligible(Actor target) =>
			EscortEligible(player.RelationshipWith(target.Owner) == PlayerRelationship.Enemy,
				priorityCapturableTypes.Contains(target.Info.Name.ToLowerInvariant()));

		/// <summary>True when a defended tech target may not be attempted yet: escorts on, defenders present, and no
		/// ready escort plan for exactly this target. Enemy-base buildings are never blocked (stealth).</summary>
		bool BlockedByEscort(Actor target)
		{
			if (!Info.EscortDefendedCaptures || !EscortEligible(target))
				return false;

			var defence = DefenceValue(target);
			if (defence <= 0)
				return false;

			if (escort == null || escort.Target != target)
				return true;

			escort.DefenceValue = defence;
			return !EscortReady(OwnArmedValueNear(target), defence, escort.InitialDefenceValue, Info.EscortSuperiority, Info.EscortThinnedPercent);
		}

		/// <summary>Opens the one escort plan for the first defended candidate (the candidates arrive best first).</summary>
		void ConsiderEscort(IEnumerable<Actor> candidates)
		{
			if (!Info.EscortDefendedCaptures || escort != null)
				return;

			foreach (var t in candidates)
			{
				if (!EscortEligible(t))
					continue;

				var defence = DefenceValue(t);
				if (defence <= 0)
					continue;

				escort = new EscortPlan
				{
					Target = t, MissionId = CaptureMissionId(t.Info.Name, t.ActorID), SinceTick = world.WorldTick, DefenceValue = defence,
					InitialDefenceValue = defence
				};

				BotMissionLog.Write(new BotMissionRecord
				{
					Player = player, MissionId = escort.MissionId, Event = BotMissionEvent.Published,
					Executor = "Engineers", MissionType = "capture", TargetCell = t.Location, Value = defence
				});
				return;
			}
		}

		/// <summary>Ends a plan whose target is gone or ours, and denies one whose escort never came.</summary>
		void HousekeepEscort(int tick)
		{
			if (escort == null || escort.Committed)
				return;

			var t = escort.Target;
			if (t.IsDead || !t.IsInWorld || t.Owner == player)
			{
				BotMissionLog.Write(new BotMissionRecord
				{
					Player = player, MissionId = escort.MissionId, Event = BotMissionEvent.Denied, Reason = BotMissionReasons.TargetGone,
					Executor = "Engineers", MissionType = "capture"
				});
				escort = null;
				return;
			}

			if (tick - escort.SinceTick < Info.EscortWaitTicks)
				return;

			// No escort in time: no execution attempt ever existed — mission feedback, then the shelf.
			BotMissionLog.Write(new BotMissionRecord
			{
				Player = player, MissionId = escort.MissionId, Event = BotMissionEvent.Denied, Reason = BotMissionReasons.NoUnits,
				Executor = "Engineers", MissionType = "capture", TargetCell = t.Location, Value = escort.DefenceValue
			});
			dormantUntil[escort.MissionId] = tick + Info.CaptureDormantTicks;
			BotMissionLog.Write(new BotMissionRecord
			{
				Player = player, MissionId = escort.MissionId, Event = BotMissionEvent.Dormant, Reason = BotMissionReasons.NoUnits,
				Executor = "Engineers", MissionType = "capture", TargetCell = t.Location
			});
			escort = null;
		}

		/// <summary>The escort seam: one standing guard request at the escorted target while its mission lives.</summary>
		IReadOnlyList<BotProtectionRequest> IBotProtectionRequestProvider.ProtectionRequests =>
			escort == null || escort.Target.IsDead || !escort.Target.IsInWorld
				? []
				: [new BotProtectionRequest(escort.Target.Location, EscortRequestValue(escort.DefenceValue, EscortRequestFloor()), world.WorldTick + Info.EscortRequestTicks)];

		/// <summary>A target already carrying `max` live capture attempts takes no more (max ≤ 0: no limit).</summary>
		public static bool TargetFull(int liveAttempts, int max) => max > 0 && liveAttempts >= max;

		bool TargetFull(Actor target) =>
			TargetFull(assigned.Values.Count(j => j.Job == EngineerJob.Capture && j.Target == target), Info.MaxEngineersPerTarget);

		// MC1 (docs/design/AI_MISSION_CARDS.md): every capture is a mission card. The mission is the building (its
		// strategic reason survives a lost engineer, and a change of owner); each engineer sent at it is one attempt.
		public static string CaptureMissionId(string actorType, uint actorId) => $"capture:{actorType}:{actorId}";

		/// <summary>The dormant shelf's trigger, free of world state so it can be tested.</summary>
		public static bool GoesDormant(int failStreak, int threshold) => threshold > 0 && failStreak >= threshold;

		bool Dormant(Actor target) =>
			dormantUntil.TryGetValue(CaptureMissionId(target.Info.Name, target.ActorID), out var until) && world.WorldTick < until;

		/// <summary>How a capture attempt ended, free of world state so it can be tested. Order matters: an engineer
		/// consumed by a successful capture is also "dead" (Actor.IsDead includes Disposed).</summary>
		public static (BotMissionAttemptState State, string Reason) CaptureVerdict(bool targetOurs, bool stuck, bool engineerDead, bool targetGone)
		{
			if (targetOurs)
				return (BotMissionAttemptState.Success, BotMissionReasons.Done);

			if (stuck)
				return (BotMissionAttemptState.Released, BotMissionReasons.Stuck);

			if (engineerDead)
				return (BotMissionAttemptState.Failed, BotMissionReasons.LostUnits);

			if (targetGone)
				return (BotMissionAttemptState.Released, BotMissionReasons.TargetGone);

			return (BotMissionAttemptState.Released, BotMissionReasons.Dropped);
		}

		void StartMission(Assignment job, Actor engineer, string executor = "Engineers")
		{
			var target = job.Target;
			job.MissionId = CaptureMissionId(target.Info.Name, target.ActorID);

			// A card leaving the shelf is its own event, before the attempt that follows it.
			if (dormantUntil.Remove(job.MissionId))
				BotMissionLog.Write(new BotMissionRecord
				{
					Player = player, MissionId = job.MissionId, Event = BotMissionEvent.Reopened, Reason = BotMissionReasons.Timeout,
					Executor = "Engineers", MissionType = "capture", TargetCell = target.Location
				});

			job.Attempt = missionAttempts.GetValueOrDefault(job.MissionId) + 1;
			missionAttempts[job.MissionId] = job.Attempt;
			BotMissionLog.Write(new BotMissionRecord
			{
				Player = player, MissionId = job.MissionId, Attempt = job.Attempt, State = BotMissionAttemptState.Committed,
				Executor = "Engineers", MissionType = "capture", TargetCell = target.Location, Units = 1
			});
		}

		void EndMission(Actor engineer, Assignment job, EngineerCheck check, bool pulledBack = false, bool superseded = false)
		{
			if (job.MissionId == null)
				return;

			// The escorted attempt is over either way: the escort's job ends with it.
			if (escort != null && escort.MissionId == job.MissionId)
				escort = null;

			var target = job.Target;
			var targetGone = target == null || target.IsDead || !target.IsInWorld;
			var (state, reason) = CaptureVerdict(!targetGone && target.Owner == player, check == EngineerCheck.Stuck,
				engineer.IsDead, targetGone);

							// A voluntary retreat (RouteRecheckTicks): released, outmatched; it does not feed the dormant shelf.
							if (pulledBack && state == BotMissionAttemptState.Released && reason == BotMissionReasons.Dropped)
								reason = BotMissionReasons.Outmatched;

							// TC-2e: a stand-down to an outranking ally's published claim — released, superseded;
							// like the voluntary retreat, it does not feed the dormant shelf.
							if (superseded && state == BotMissionAttemptState.Released && reason == BotMissionReasons.Dropped)
								reason = BotMissionReasons.Superseded;
							BotMissionLog.Write(new BotMissionRecord
			{
				Player = player, MissionId = job.MissionId, Attempt = job.Attempt, State = state, Reason = reason,
				Executor = "Engineers", MissionType = "capture", TargetCell = target?.Location, Units = 1,

				// Where the attempt ended: for a lost engineer, where it fell (on the route or at the target).
				UnitCell = world.Map.CellContaining(engineer.CenterPosition)
			});

			// The dormant shelf: a success clears both streaks; consecutive losses rest the mission.
			// A consecutive `Released/outmatched` run feeds the retreat shelf instead — a voluntary
			// retreat is not a failure, but sustained commit-retreat churn still rests the target.
			if (state == BotMissionAttemptState.Success)
			{
				missionFailStreak.Remove(job.MissionId);
				missionRetreatStreak.Remove(job.MissionId);
			}
			else if (state == BotMissionAttemptState.Failed)
			{
				missionRetreatStreak.Remove(job.MissionId);
				var streak = missionFailStreak.GetValueOrDefault(job.MissionId) + 1;
				missionFailStreak[job.MissionId] = streak;
				if (GoesDormant(streak, Info.CaptureFailuresBeforeDormant))
				{
					missionFailStreak.Remove(job.MissionId);
					dormantUntil[job.MissionId] = world.WorldTick + Info.CaptureDormantTicks;
					BotMissionLog.Write(new BotMissionRecord
					{
						Player = player, MissionId = job.MissionId, Event = BotMissionEvent.Dormant, Reason = BotMissionReasons.Outmatched,
						Executor = "Engineers", MissionType = "capture", TargetCell = target?.Location
					});
				}
			}
			else if (state == BotMissionAttemptState.Released && reason == BotMissionReasons.Outmatched)
			{
				var retreats = missionRetreatStreak.GetValueOrDefault(job.MissionId) + 1;
				missionRetreatStreak[job.MissionId] = retreats;
				if (GoesDormant(retreats, Info.CaptureRetreatsBeforeDormant))
				{
					missionRetreatStreak.Remove(job.MissionId);
					dormantUntil[job.MissionId] = world.WorldTick + Info.CaptureDormantTicks;
					BotMissionLog.Write(new BotMissionRecord
					{
						Player = player, MissionId = job.MissionId, Event = BotMissionEvent.Dormant, Reason = BotMissionReasons.Outmatched,
						Executor = "Engineers", MissionType = "capture", TargetCell = target?.Location
					});
				}
			}
		}

		List<MiniYamlNode> IGameSaveTraitData.IssueTraitData(Actor self)
		{
			if (IsTraitDisabled)
				return null;

			return [new("InitialBaseCenter", FieldSaver.FormatValue(initialBaseCenter))];
		}

		void IGameSaveTraitData.ResolveTraitData(Actor self, MiniYaml data)
		{
			if (self.World.IsReplay)
				return;

			var nodes = data.ToDictionary();
			if (nodes.TryGetValue("InitialBaseCenter", out var node))
				initialBaseCenter = FieldLoader.GetValue<CPos>("InitialBaseCenter", node.Value);
		}
	}
}
