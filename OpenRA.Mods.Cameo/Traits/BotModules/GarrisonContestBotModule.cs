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
using OpenRA.Mods.AS.Traits;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;
using CAAIUtils = OpenRA.Mods.CA.AIUtils;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	// GC-1 (AI_ARCHITECTURE §12.19): the garrison contest. The A/B finding was that genericbot never fought for
	// neutral garrisonables - LoadGarrisonerBotModuleCA only drafts units that are IsIdle *and* unsquad-owned,
	// and on the new stack squads absorb every infantryman first, so the civilian bunkers went to the classic
	// bot by default and then shot the assaults apart. This module is the genericbot answer, in two passes:
	//
	//  - Contest: lease a small infantry contingent (BotLeasePurpose.Garrison, the §19.6 contract, so squads
	//    cannot re-draft the walkers mid-trip) and send it into the best reachable neutral garrisonable in the
	//    explored frontier - capacity-weighted nearest-first, early enough to beat the enemy to it. Targets are
	//    gated on Shroud.IsExplored, so the bot only claims what it has actually scouted.
	//  - Clear: enemy-occupied garrisonables (enemy-owned via ChangeOwnerOnGarrisoner, or remembered as
	//    garrisonable defences through IBotRememberedDefenceProvider - both fog-honest) are published as Raid
	//    missions on the IBotMissionProvider seam. Squads stay the execution authority: the assault goes through
	//    SiegeEvaluator's stand-off / artillery-first verdicts, so a garrison is bombarded down before infantry
	//    are committed instead of fed in one by one. Mission Id `raid:garrison_<cell>:r<zone>` keeps the
	//    attempt lineage per building.
	//
	// Denial is emergent: an enemy engineer/infantry column walking at a garrison we want produces the same
	// contest claim; once the building flips enemy it becomes a published Raid target, so it does not stay
	// enemy property for free.
	//
	// Owns its slice alone per the one-owner rule: when this module is armed, `LoadGarrisonerBotModuleCA@Infantry`
	// is disarmed for genericbot in ai.yaml (the classic stack keeps it untouched), exactly like
	// EngineerBotModule yields RepairBridge to BridgeRepairBotModule under cn3_bridge_repair.
	[TraitLocation(SystemActors.Player)]
	[Desc("Contests neutral garrisonable buildings with leased infantry and publishes Raid missions against enemy-occupied garrisons.")]
	public class GarrisonContestBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Ticks between contest/clear scans.")]
		public readonly int ScanInterval = 100;

		[Desc("How far (cells) from the frontier anchor a neutral garrisonable may be before it is ignored.")]
		public readonly int ContestRadiusCells = 80;

		[Desc("Idle infantry beyond this floor are contest-eligible - squad formation is never starved to man bunkers.")]
		public readonly int MinimumSpareInfantry = 2;

		[Desc("Occupied weight to aim for per claimed garrison (<= the building's own MaxWeight).")]
		public readonly int DesiredOccupancyWeight = 4;

		[Desc("Cap on distinct garrisons with walkers en route at once.")]
		public readonly int MaxConcurrentClaims = 4;

		[Desc("Cap on total infantry leased for contest claims at once.")]
		public readonly int MaxLeasedWalkers = 12;

		[Desc("Publish Raid missions against enemy-occupied garrisonables on the IBotMissionProvider seam.")]
		public readonly bool PublishClearRaids = true;

		[Desc("Mission Priority for garrison-clear raids (MasterAi raids derive 0-100 from economy share).")]
		public readonly int ClearRaidPriority = 55;

		[Desc("RequiredValue = remembered garrison value times this percent / 100 (rule-4 commit ratio convention).")]
		public readonly int ClearRaidForcePercent = 150;

		[Desc("Ticks a taken clear raid stays reserved before it may be republished.")]
		public readonly int MissionReservationTicks = 2500;

		[Desc("Value priced per remembered garrison seat when the fog memory carries none (dormant-arm default).")]
		public readonly int GarrisonSeatValue = 120;

		[Desc("TC-2e (AI_ARCHITECTURE §12.17): yield a contest target an outranking allied bot already claims",
			"(published on the team blackboard - lower ClientIndex wins), and stand an in-flight claim down",
			"when an outranking ally's claim lands on its cell. Inert in 1v1 - no allied broadcasts exist.")]
		public readonly bool UseTeamCaptureClaims = false;

		[Desc("BF-2 (AI_ARCHITECTURE §12.26): prefer contest targets in the caller's deterministic",
			"shard (hash of the target cell mod team size) - two allies picking the same garrison",
			"inside one snapshot interval can't be arbitrated by an unpublished claim. Orders, never",
			"filters: out-of-shard targets stay eligible once the own tier is exhausted.")]
		public readonly bool PreferShardCaptureTargets = false;

		[Desc("Ticks a contest claim may run with no walker inside before it stands down (DORMANT stuck).",
			"A wedged but living walker renews its lease forever - the claim would otherwise never close.")]
		public readonly int ClaimTimeoutTicks = 7500;

		[Desc("Base tick backoff per consecutive lost_units/x_contest_lost close on the same building;",
			"the wait scales with the failure streak and clears when a claim lands. Feeding walkers into",
			"a defended approach is the suicide this module exists to avoid.")]
		public readonly int ContestRetryCooldownTicks = 2500;

		public override object Create(ActorInitializer init) { return new GarrisonContestBotModule(init.Self, this); }
	}

	public class GarrisonContestBotModule : ConditionalTrait<GarrisonContestBotModuleInfo>, IBotTick, IBotMissionProvider,
		IBotCaptureClaimSource
	{
		const string LeaseOwner = nameof(GarrisonContestBotModule);

		readonly World world;
		readonly OpenRA.Player player;

		// Building ActorID -> walkers en route. Released on arrival, death, or the building leaving neutral hands.
		readonly Dictionary<uint, List<Actor>> claimWalkers = new();

		// TC-2e: the claimed garrison's cell per ActorID - buildings do not move, so it is written once at claim
		// time and dropped with the claim. This is what CaptureClaimPositions publishes to the blackboard.
		readonly Dictionary<uint, CPos> claimCells = new();

		// Tick each claim was issued - a claim whose walkers never arrive (wedged but alive renews the lease
		// forever) must still terminalize, or its card hangs open for the rest of the match.
		readonly Dictionary<uint, int> claimStartTicks = new();

		// Consecutive bleeding closes per building and the resulting re-contest block - escalating backoff on
		// lost_units/x_contest_lost, cleared when a claim lands.
		readonly Dictionary<uint, int> contestFailures = new();
		readonly Dictionary<uint, int> contestBlockedUntil = new();
		readonly Dictionary<string, int> raidReservations = new();
		List<BotMission> missions = [];
		IBotZoneTopology zoneTopology;
		IBotRememberedDefenceProvider[] defenceProviders;
		bool providersSearched;
		int scanTicks;

		public GarrisonContestBotModule(Actor self, GarrisonContestBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			scanTicks = world.LocalRandom.Next(Info.ScanInterval);
		}

		protected override void TraitDisabled(Actor self)
		{
			var leases = BotUnitLeases.Of(player);
			foreach (var walkers in claimWalkers.Values)
				foreach (var walker in walkers)
					leases?.Release(walker, LeaseOwner);

			claimWalkers.Clear();
			claimCells.Clear();
			claimStartTicks.Clear();
			contestFailures.Clear();
			contestBlockedUntil.Clear();
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (--scanTicks > 0)
				return;

			scanTicks = Info.ScanInterval;

			if (!providersSearched)
			{
				providersSearched = true;
				zoneTopology = player.PlayerActor.TraitsImplementing<IBotZoneTopology>().FirstEnabledTraitOrDefault();
				defenceProviders = player.PlayerActor.TraitsImplementing<IBotRememberedDefenceProvider>().ToArray();
			}

			var leases = BotUnitLeases.Of(player);
			TickContests(bot, leases);
			if (Info.PublishClearRaids)
				TickClearMissions();
		}

		static bool IsInside(Actor a) =>
			a.TraitOrDefault<Garrisoner>()?.Transport != null || a.TraitOrDefault<Passenger>()?.Transport != null;

		static bool CanFightFromGarrison(Actor actor)
		{
			return actor.Info.TraitInfoOrDefault<GarrisonerInfo>() != null &&
				actor.Info.TraitInfos<ArmamentInfo>()
					.Any(a => string.Equals(a.Name, "garrisoned", StringComparison.OrdinalIgnoreCase));
		}

		// The contested-buildings frontier anchor: centroid of our own buildings; null until the yard deploys.
		CPos? FrontierAnchor()
		{
			var buildings = world.Actors
				.Where(a => a.Owner == player && a.IsInWorld && !a.IsDead && a.Info.HasTraitInfo<BuildingInfo>())
				.ToArray();
			if (buildings.Length == 0)
				return null;

			return new CPos(
				(int)buildings.Average(b => (long)b.Location.X),
				(int)buildings.Average(b => (long)b.Location.Y));
		}

		void TickContests(IBot bot, IBotUnitLeases leases)
		{
			// TC-2e (§12.17): the cells outranking allied bots already claim, off the team blackboard —
			// one read per pass. Flag off or 1v1 leaves null and every gate below is the no-op it is today.
			HashSet<WPos> claimsAhead = null;
			if (Info.UseTeamCaptureClaims)
				claimsAhead = TeamBlackboard.ClaimsAheadOf(TeamBlackboard.CollectBroadcasts(player), player.InternalName);

			// BF-2 (§12.26): the deterministic shard tier — in-shard targets sort first,
			// out-of-shard stays eligible after them. Size 1 makes every tier 0, the no-op.
			var shardSize = 1;
			var shardRank = 0;
			if (Info.PreferShardCaptureTargets)
				(shardRank, shardSize) = TeamBlackboard.ClaimRank(player);

			int ShardTier(Actor garrison) =>
				shardSize <= 1 ? 0 : (TeamBlackboard.CaptureShard(garrison.Location, shardSize) == shardRank ? 0 : 1);

			// Housekeeping first: drop walkers that arrived, died, lost their lease, or whose target stopped being neutral.
			var prune = new List<(uint Building, bool AnyInside, bool Superseded, bool TimedOut)>();
			foreach (var (building, walkers) in claimWalkers)
			{
				var anyInside = false;
				var superseded = false;
				var timedOut = false;

				// Standing down a claim is the same shape whoever asks: leases released, the walkers that are
				// still outside get a Stop or a queued EnterGarrison would capture the building anyway.
				void StandDownWalkers()
				{
					// Order before release: a Stop issued while the lease is still held reads as the claim's
					// own last act at the order gate; releasing first would leave the Stop unattributed and
					// the next module's order inside the window counts as crossed, not a hand-off.
					foreach (var w in walkers)
					{
						if (!w.IsDead && w.IsInWorld && w.Owner == player && !IsInside(w))
							bot.QueueOrder(new Order("Stop", w, false));
						leases?.Release(w, LeaseOwner);
					}

					walkers.Clear();
				}

				// TC-2e: the claim lost arbitration to a lower-index ally. The walkers stand down through the
				// stale-claim path — released, the entry pruned.
				if (claimsAhead != null && claimCells.TryGetValue(building, out var claimedCell)
					&& claimsAhead.Contains(world.Map.CenterOfCell(claimedCell)))
				{
					superseded = true;
					// IsInside calls TraitOrDefault on destroyed actors, so the guards run inside the predicate.
					anyInside = walkers.Any(w => !w.IsDead && w.IsInWorld && w.Owner == player && IsInside(w));
					StandDownWalkers();
				}
				else if (claimStartTicks.TryGetValue(building, out var started)
					&& world.WorldTick - started > Info.ClaimTimeoutTicks)
				{
					// The walkers never arrived and never died - wedged on a dead-end path but still alive, so
					// the lease heartbeat renews forever. Stand them down and close the card honestly.
					timedOut = true;
					StandDownWalkers();
				}
				else
				{
					walkers.RemoveAll(w =>
					{
						// IsInside calls TraitOrDefault - destroyed actors throw, so the guards must run first.
						var inside = !w.IsDead && w.IsInWorld && w.Owner == player && IsInside(w);
						var done = inside || w.IsDead || !w.IsInWorld || w.Owner != player
							|| leases == null || !leases.TryClaim(w, LeaseOwner, BotLeasePurpose.Garrison, LeaseHeartbeatTicks());
						if (done)
						{
							anyInside |= inside;
							leases?.Release(w, LeaseOwner);
						}

						return done;
					});
				}


				if (walkers.Count == 0)
					prune.Add((building, anyInside, superseded, timedOut));
			}

			foreach (var (id, anyInside, superseded, timedOut) in prune)
			{
				claimWalkers.Remove(id);
				claimCells.Remove(id);
				claimStartTicks.Remove(id);
				WriteClaimClosed(id, anyInside, superseded, timedOut);
			}

			if (claimWalkers.Count >= Info.MaxConcurrentClaims)
				return;

			var anchor = FrontierAnchor();
			if (anchor == null)
				return;

			var radiusSq = (long)Info.ContestRadiusCells * Info.ContestRadiusCells;
			var shroud = player.Shroud;

			// Neutral-owned only: ChangeOwnerOnGarrisoner flips occupied buildings to the garrisoner's owner,
			// so a neutral-owner garrisonable is enterable; an enemy one is a clear-mission target instead.
			// IsExplored keeps it fog-honest - the contest can only claim what scouting has already mapped.
			var candidates = world.ActorsHavingTrait<Garrisonable>()
				.Where(a => a.IsInWorld && !a.IsDead
					&& a.Owner.RelationshipWith(player) == PlayerRelationship.Neutral
					&& a.Trait<Garrisonable>().HasSpace(1)
					&& !claimWalkers.ContainsKey(a.ActorID)
					&& !(contestBlockedUntil.TryGetValue(a.ActorID, out var blockedUntil) && world.WorldTick < blockedUntil)
					&& (claimsAhead == null || !claimsAhead.Contains(world.Map.CenterOfCell(a.Location)))
					&& shroud.IsExplored(a.Location)
					&& (a.Location - anchor.Value).LengthSquared <= radiusSq)
				.OrderBy(ShardTier).ThenBy(a => ((a.Location - anchor.Value).LengthSquared)
					/ Math.Max(1, a.Trait<Garrisonable>().Info.MaxWeight))
				.ToList();
			if (candidates.Count == 0)
				return;

			// The spare-infantry buffer: only what exceeds the floor may walk, and only walkers that can
			// actually fight from a garrison - a rifleman that cannot shoot through a port is wasted weight.
			var pool = world.Actors
				.Where(a => a.Owner == player && a.IsInWorld && !a.IsDead && a.IsIdle
					&& CanFightFromGarrison(a)
					&& !BotUnitLeases.IsClaimedByOther(leases, a, LeaseOwner))
				.OrderBy(a => a.ActorID)
				.Skip(Info.MinimumSpareInfantry)
				.ToList();
			if (pool.Count == 0)
				return;

			var leased = claimWalkers.Values.Sum(w => w.Count);
			foreach (var garrison in candidates)
			{
				if (claimWalkers.Count >= Info.MaxConcurrentClaims || leased >= Info.MaxLeasedWalkers || pool.Count == 0)
					break;

				var garrisonable = garrison.Trait<Garrisonable>();
				var desired = Math.Min(garrisonable.Info.MaxWeight, Math.Max(1, Info.DesiredOccupancyWeight));
				var walkers = new List<Actor>();
				for (var weight = 0; weight < desired && pool.Count > 0 && leased < Info.MaxLeasedWalkers
					&& garrisonable.HasSpace(garrisonable.TotalWeight + weight + 1);)
				{
					var pick = pool
						.OrderBy(p => (p.CenterPosition - garrison.CenterPosition).HorizontalLengthSquared)
						.First();
					var w = pick.Info.TraitInfoOrDefault<GarrisonerInfo>().Weight;
					if (!garrisonable.HasSpace(garrisonable.TotalWeight + weight + w))
						break;

					pool.Remove(pick);
					weight += w;
					leased++;
					walkers.Add(pick);
				}

				if (walkers.Count == 0)
					continue;

				// The claimed set is leased before the orders go out, so a squad pass in the same tick
				// cannot draft a walker mid-decision. AttackMove carries them through incidental contact;
				// the queued EnterGarrison finishes the job - same shape as LoadGarrisonerBotModuleCA.
				var claimed = new List<Actor>();
				foreach (var walker in walkers)
					if (leases == null || leases.TryClaim(walker, LeaseOwner, BotLeasePurpose.Garrison, LeaseHeartbeatTicks()))
						claimed.Add(walker);

				if (claimed.Count == 0)
					continue;

				claimWalkers[garrison.ActorID] = claimed;
				claimCells[garrison.ActorID] = garrison.Location;
				claimStartTicks[garrison.ActorID] = world.WorldTick;
				bot.QueueOrder(new Order("AttackMove", null, Target.FromCell(world, garrison.Location), false, groupedActors: claimed.ToArray()));
				bot.QueueOrder(new Order("EnterGarrison", null, Target.FromActor(garrison), true, groupedActors: claimed.ToArray()));

				var line = $"AI ({player.ClientIndex}): GC-1 contest claim on {garrison.Info.Name} {garrison.ActorID} at {garrison.Location} - {claimed.Count} walkers leased, at tick {world.WorldTick}";
				Log.Write("debug", line);
				CAAIUtils.BotDebug(line);
				BotMissionLog.Write(new BotMissionRecord
				{
					Player = player,
					MissionId = $"garrison_contest:a{garrison.ActorID}",
					Event = BotMissionEvent.Published,
					Executor = nameof(GarrisonContestBotModule),
					MissionType = "garrison_contest",
					TargetCell = garrison.Location,
					Units = claimed.Count,
					Tick = world.WorldTick
				});
			}
		}

		// Every resolved contest claim writes a terminal card line - occupied, lost to the enemy, target
		// destroyed, or the walkers died in transit. Without it the archive holds open claims forever.
		void WriteClaimClosed(uint building, bool anyInside, bool superseded = false, bool timedOut = false)
		{
			var actor = world.GetActorById(building);
			string reason;
			if (superseded)
				reason = BotMissionReasons.Superseded;   // TC-2e: outranked ally holds the claim — nothing was lost
			else if (timedOut)
				reason = BotMissionReasons.Stuck;        // walkers wedged en route - never arrived, never died
			else if (anyInside || (actor != null && !actor.IsDead && actor.Owner == player))
				reason = BotMissionReasons.Done;
			else if (actor == null || actor.IsDead)
				reason = BotMissionReasons.TargetGone;
			else if (actor.Owner.RelationshipWith(player) == PlayerRelationship.Enemy)
				reason = "x_contest_lost";
			else
				reason = BotMissionReasons.LostUnits;

			// Bleeding memory: a consecutive lost_units/x_contest_lost/stuck streak backs off re-contests on
			// the same building; a landed claim clears it. Stuck counts - a wedged path is topological, so a
			// re-claim sends the next walkers into the same dead end. Superseded is neutral - nothing bled.
			if (reason == BotMissionReasons.Done)
			{
				contestFailures.Remove(building);
				contestBlockedUntil.Remove(building);
			}
			else if (reason == BotMissionReasons.LostUnits || reason == BotMissionReasons.Stuck || reason == "x_contest_lost")
			{
				var streak = contestFailures.TryGetValue(building, out var f) ? f + 1 : 1;
				contestFailures[building] = streak;
				contestBlockedUntil[building] = world.WorldTick + Info.ContestRetryCooldownTicks * streak;
			}

			BotMissionLog.Write(new BotMissionRecord
			{
				Player = player,
				MissionId = $"garrison_contest:a{building}",
				Event = BotMissionEvent.Dormant,
				Reason = reason,
				Executor = nameof(GarrisonContestBotModule),
				MissionType = "garrison_contest",
				TargetCell = actor?.Location,
				Tick = world.WorldTick
			});
		}

		void TickClearMissions()
		{
			raidReservations.Keys
				.Where(k => raidReservations[k] <= world.WorldTick)
				.ToList()
				.ForEach(k => raidReservations.Remove(k));

			var seen = new HashSet<long>();
			var next = new List<BotMission>();

			void Publish(CPos cell, OpenRA.Player enemy, int rememberedValue)
			{
				var key = ((long)cell.X << 20) | (uint)cell.Y;
				if (!seen.Add(key))
					return;

				var region = zoneTopology?.NearestRegionId(cell) ?? 0;
				var missionId = $"raid:garrison_{cell.X}_{cell.Y}:r{region}";
				if (raidReservations.ContainsKey(missionId))
					return;

				var value = rememberedValue > 0 ? rememberedValue : Info.GarrisonSeatValue * 6;
				next.Add(new BotMission
				{
					Type = BotMissionType.Raid,
					Location = cell,
					TargetPlayer = enemy,
					RegionIndex = region,
					RequiredValue = (int)Math.Clamp((long)value * Info.ClearRaidForcePercent / 100, 0, int.MaxValue),
					Priority = Info.ClearRaidPriority,
					MissionId = missionId
				});
			}

			// Live, verifiable occupation: a building whose owner flipped to an enemy is garrisoned
			// (ChangeOwnerOnGarrisoner). CanBeViewedByPlayer is the same fog check the rest of the stack uses.
			foreach (var actor in world.ActorsHavingTrait<Garrisonable>())
			{
				if (!actor.IsInWorld || actor.IsDead || !actor.CanBeViewedByPlayer(player)
					|| actor.Owner.RelationshipWith(player) != PlayerRelationship.Enemy)
					continue;

				Publish(actor.Location, actor.Owner, 0);
			}

			// Fogged occupation: the remembered-defence feed already prices garrisonable buildings by
			// capacity (§12.12), so a remembered GarrisonableInfo defence IS a known enemy garrison.
			foreach (var provider in defenceProviders ?? Array.Empty<IBotRememberedDefenceProvider>())
				foreach (var defence in provider.RememberedDefences())
					if (defence.Observed.TraitInfoOrDefault<GarrisonableInfo>() != null)
						Publish(defence.Cell, defence.Enemy, defence.Value);

			next.Sort((a, b) => b.Priority.CompareTo(a.Priority));
			var previous = new HashSet<string>(missions.Select(m => m.MissionId));
			foreach (var mission in next)
			{
				if (previous.Contains(mission.MissionId))
					continue;

				BotMissionLog.Write(new BotMissionRecord
				{
					Player = player,
					MissionId = mission.MissionId,
					Event = BotMissionEvent.Published,
					Executor = nameof(GarrisonContestBotModule),
					MissionType = "raid",
					RegionIndex = mission.RegionIndex,
					TargetCell = mission.Location,
					Value = mission.RequiredValue,
					Tick = world.WorldTick
				});
			}

			// A card that vanished from the scan while not reserved resolved itself - the garrison was
			// destroyed or captured - so shelf it; reserved cards are live attempts owned by the executor.
			foreach (var retired in previous.Except(next.Select(m => m.MissionId)).Where(id => !raidReservations.ContainsKey(id)))
				BotMissionLog.Write(new BotMissionRecord
				{
					Player = player,
					MissionId = retired,
					Event = BotMissionEvent.Dormant,
					Reason = BotMissionReasons.TargetGone,
					Executor = nameof(GarrisonContestBotModule),
					MissionType = "raid",
					Tick = world.WorldTick
				});

			missions = next;
		}

		public IReadOnlyList<BotMission> Missions => IsTraitDisabled ? Array.Empty<BotMission>() : missions;

		// TC-2e (AI_ARCHITECTURE §12.17): the live contest claims' cell centres, for the team blackboard.
		public IReadOnlyList<WPos> CaptureClaimPositions =>
			claimCells.Count == 0
				? Array.Empty<WPos>()
				: claimCells.Values.Select(c => world.Map.CenterOfCell(c)).ToList();

		public void MissionTaken(BotMission mission)
		{
			if (mission?.MissionId != null)
				raidReservations[mission.MissionId] = world.WorldTick + Info.MissionReservationTicks;
		}

		int LeaseHeartbeatTicks() => Math.Max(200, Info.ScanInterval * 4);
	}
}
