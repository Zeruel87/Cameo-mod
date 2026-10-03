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

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	// TC-1 (AI_ARCHITECTURE.md §12.17, AI_DEEP_RESEARCH.md §11): the publish-only
	// team blackboard. Aggregate is the pure half — the tests pin its arithmetic;
	// Collect is the World-reading half and stays integration-side.
	[TestFixture]
	public sealed class TeamBlackboardTest
	{
		// A shared MainTarget means allies committed to the same enemy Player; the
		// tests only need distinct references, so uninitialised Players stand in
		// (the same fixture trick ZoneRegionMemoryTest uses).
		static OpenRA.Player FakePlayer() =>
			(OpenRA.Player)RuntimeHelpers.GetUninitializedObject(typeof(OpenRA.Player));

		static TeamBroadcast Broadcast(int ownArmyValue = 0, int urgencyLevel = 0, int directorTension = 0,
			DirectorPhase directorPhase = DirectorPhase.BuildUp, OpenRA.Player mainTarget = null,
			bool requestsDefence = false, WPos defendPosition = default, int snapshotTick = 1500) =>
			new(snapshotTick, ownArmyValue, urgencyLevel, directorTension,
				directorPhase, mainTarget, requestsDefence, defendPosition);

		[Test]
		public void NullOrEmptyInputYieldsZeroSummary()
		{
			foreach (var summary in new[]
			{
				TeamBlackboard.Aggregate(null),
				TeamBlackboard.Aggregate(new List<TeamBroadcast>())
			})
			{
				Assert.That(summary.AlliedBots, Is.EqualTo(0));
				Assert.That(summary.TotalArmyValue, Is.EqualTo(0));
				Assert.That(summary.MaxTension, Is.EqualTo(0));
				Assert.That(summary.AnyClimax, Is.False);
				Assert.That(summary.DefendRequests, Is.EqualTo(0));
				Assert.That(summary.SharedTargetCount, Is.EqualTo(0));
			}
		}

		[Test]
		public void EmptyBroadcastPublishesAbsence()
		{
			// What an absent, disabled or never-snapshotted provider reports — a
			// zeroed broadcast, never a behaviour change.
			var empty = TeamBroadcast.Empty;
			Assert.That(empty.SnapshotTick, Is.EqualTo(0));
			Assert.That(empty.OwnArmyValue, Is.EqualTo(0));
			Assert.That(empty.UrgencyLevel, Is.EqualTo(0));
			Assert.That(empty.DirectorTension, Is.EqualTo(0));
			Assert.That(empty.DirectorPhase, Is.EqualTo(DirectorPhase.BuildUp));
			Assert.That(empty.MainTarget, Is.Null);
			Assert.That(empty.RequestsDefence, Is.False);
			Assert.That(empty.DefendPosition, Is.EqualTo(WPos.Zero));

			// The ally is still on the team — an empty broadcast counts as a member
			// while contributing nothing to any signal.
			var summary = TeamBlackboard.Aggregate(new[] { empty });
			Assert.That(summary.AlliedBots, Is.EqualTo(1));
			Assert.That(summary.TotalArmyValue, Is.EqualTo(0));
			Assert.That(summary.SharedTargetCount, Is.EqualTo(0));
		}

		[Test]
		public void ConstructorCarriesEveryField()
		{
			var target = FakePlayer();
			var broadcast = new TeamBroadcast(1234, 5678, 2, 91, DirectorPhase.Pressure,
				target, true, new WPos(100, 200, 0));
			Assert.That(broadcast.SnapshotTick, Is.EqualTo(1234));
			Assert.That(broadcast.OwnArmyValue, Is.EqualTo(5678));
			Assert.That(broadcast.UrgencyLevel, Is.EqualTo(2));
			Assert.That(broadcast.DirectorTension, Is.EqualTo(91));
			Assert.That(broadcast.DirectorPhase, Is.EqualTo(DirectorPhase.Pressure));
			Assert.That(broadcast.MainTarget, Is.SameAs(target));
			Assert.That(broadcast.RequestsDefence, Is.True);
			Assert.That(broadcast.DefendPosition, Is.EqualTo(new WPos(100, 200, 0)));
		}

		[Test]
		public void SingleBroadcastCountsOneAlly()
		{
			var summary = TeamBlackboard.Aggregate(new[]
			{
				Broadcast(ownArmyValue: 4000, urgencyLevel: 1, directorTension: 65,
					directorPhase: DirectorPhase.Pressure, requestsDefence: true)
			});
			Assert.That(summary.AlliedBots, Is.EqualTo(1));
			Assert.That(summary.TotalArmyValue, Is.EqualTo(4000));
			Assert.That(summary.MaxTension, Is.EqualTo(65));
			Assert.That(summary.DefendRequests, Is.EqualTo(1));
		}

		[Test]
		public void ArmyValuesSumAcrossAllies()
		{
			var summary = TeamBlackboard.Aggregate(new[]
			{
				Broadcast(ownArmyValue: 3000),
				Broadcast(ownArmyValue: 1500),
				Broadcast(ownArmyValue: 500)
			});
			Assert.That(summary.AlliedBots, Is.EqualTo(3));
			Assert.That(summary.TotalArmyValue, Is.EqualTo(5000));
		}

		[Test]
		public void MaxTensionTakesTheHighest()
		{
			var summary = TeamBlackboard.Aggregate(new[]
			{
				Broadcast(directorTension: 20),
				Broadcast(directorTension: 90),
				Broadcast(directorTension: 45)
			});
			Assert.That(summary.MaxTension, Is.EqualTo(90));
		}

		[Test]
		public void AnyClimaxFlagsAPeakingAlly()
		{
			var summary = TeamBlackboard.Aggregate(new[]
			{
				Broadcast(directorPhase: DirectorPhase.BuildUp),
				Broadcast(directorPhase: DirectorPhase.Climax)
			});
			Assert.That(summary.AnyClimax, Is.True);
		}

		[Test]
		public void AnyClimaxStaysFalseWithoutOne()
		{
			var summary = TeamBlackboard.Aggregate(new[]
			{
				Broadcast(directorPhase: DirectorPhase.Pressure),
				Broadcast(directorPhase: DirectorPhase.Relief)
			});
			Assert.That(summary.AnyClimax, Is.False);
		}

		[Test]
		public void DefendRequestsCountsOnlyThoseAsking()
		{
			var summary = TeamBlackboard.Aggregate(new[]
			{
				Broadcast(requestsDefence: true),
				Broadcast(requestsDefence: false),
				Broadcast(requestsDefence: true)
			});
			Assert.That(summary.DefendRequests, Is.EqualTo(2));
		}

		[Test]
		public void SharedTargetCountsTheLargestCommittedGroup()
		{
			var alpha = FakePlayer();
			var beta = FakePlayer();
			var summary = TeamBlackboard.Aggregate(new[]
			{
				Broadcast(mainTarget: alpha),
				Broadcast(mainTarget: beta),
				Broadcast(mainTarget: alpha)
			});
			Assert.That(summary.SharedTargetCount, Is.EqualTo(2),
				"two allies committed to the same enemy are the largest shared-target group");
		}

		[Test]
		public void DistinctTargetsNeverGroup()
		{
			var summary = TeamBlackboard.Aggregate(new[]
			{
				Broadcast(mainTarget: FakePlayer()),
				Broadcast(mainTarget: FakePlayer())
			});
			Assert.That(summary.SharedTargetCount, Is.EqualTo(1),
				"allies on different enemies share nothing — each commitment is a group of one");
		}

		[Test]
		public void NullMainTargetsAreNotCounted()
		{
			var summary = TeamBlackboard.Aggregate(new[]
			{
				Broadcast(),
				Broadcast()
			});
			Assert.That(summary.SharedTargetCount, Is.EqualTo(0),
				"a bot without a target committed to nothing — null is not a shared enemy");
		}

		[Test]
		public void SituationLogEmitsTeamFields()
		{
			var situation = new BotSituation
			{
				Tick = 1500,
				Enemies = new Dictionary<OpenRA.Player, EnemyProfile>(),
				Demand = new CounterDemand(),
				TeamAlliedBots = 2,
				TeamArmyValue = 7000,
				TeamMaxTension = 80,
				TeamDefendRequests = 1,
				TeamSharedTarget = 2
			};
			var b = new StringBuilder();
			AiSituationLogWriter.AppendSituation(b, "game", "", "map", "Multi0", "td_gdi", "medium", "rush", situation);
			using var doc = JsonDocument.Parse(b.ToString());
			var own = doc.RootElement.GetProperty("own");
			Assert.That(own.GetProperty("team_allied_bots").GetInt32(), Is.EqualTo(2));
			Assert.That(own.GetProperty("team_army_value").GetInt32(), Is.EqualTo(7000));
			Assert.That(own.GetProperty("team_max_tension").GetInt32(), Is.EqualTo(80));
			Assert.That(own.GetProperty("team_defend_requests").GetInt32(), Is.EqualTo(1));
			Assert.That(own.GetProperty("team_shared_target").GetInt32(), Is.EqualTo(2));
		}

		// Review 4.2: the central liveness contract — CollectBroadcasts only carries
		// entries that pass it, so no consumer can be fed a defeated or stale ally.
		[Test]
		public void ValidBroadcastRequiresAlivePublishedAndFresh()
		{
			var p = FakePlayer(); // uninitialised Player reads WinState.Undefined (0) = still in the game
			var fresh = Broadcast(snapshotTick: 1400);

			Assert.That(TeamBlackboard.IsLive(fresh, p, 1500), Is.True);
			Assert.That(TeamBlackboard.IsLive(fresh, p, 1400 + TeamBlackboard.BroadcastMaxAgeTicks),
				Is.True, "the window boundary itself is still valid");
			Assert.That(TeamBlackboard.IsLive(fresh, p, 1401 + TeamBlackboard.BroadcastMaxAgeTicks),
				Is.False, "one tick past the window is stale");

			Assert.That(TeamBlackboard.IsLive(TeamBroadcast.Empty, p, 1500), Is.False,
				"SnapshotTick 0 = never published");
			Assert.That(TeamBlackboard.IsLive(null, p, 1500), Is.False);

			p.WinState = WinState.Lost;
			Assert.That(TeamBlackboard.IsLive(fresh, p, 1500), Is.False,
				"a defeated ally's last broadcast cannot hold a claim open");
		}

		// BF-2 (§12.26): the shard is a pure function of the cell — same input, same shard,
		// every result inside [0, size), negative coordinates safe, size 0 guarded.
		[Test]
		public void CaptureShardIsDeterministicAndBounded()
		{
			var seen = new HashSet<int>();
			for (var size = 1; size <= 6; size++)
			{
				seen.Clear();
				for (var x = -40; x <= 40; x += 13)
					for (var y = -40; y <= 40; y += 17)
					{
						var shard = TeamBlackboard.CaptureShard(new CPos(x, y), size);
						Assert.That(shard, Is.InRange(0, size - 1));
						Assert.That(TeamBlackboard.CaptureShard(new CPos(x, y), size), Is.EqualTo(shard),
							"the shard is deterministic — both allies must compute the same owner");
						seen.Add(shard);
					}

				Assert.That(seen.Count, Is.EqualTo(size),
					$"size {size}: the partition actually splits the map, not collapses to one tier");
			}

			Assert.That(TeamBlackboard.CaptureShard(new CPos(7, 3), 0), Is.EqualTo(0),
				"size 0 cannot divide-by-zero");
		}

		// BF-2 (§12.26): rank is the caller's position in the ordinal-sorted union of own +
		// allied participant keys; the marked-ClientIndex fallback sorts with real ids.
		[Test]
		public void ClaimRankSortsOrdinalAndDeduplicates()
		{
			Assert.That(TeamBlackboard.ClaimRank("b", new[] { "a", "c" }), Is.EqualTo((1, 3)));
			Assert.That(TeamBlackboard.ClaimRank("a", new[] { "b", "c" }), Is.EqualTo((0, 3)));
			Assert.That(TeamBlackboard.ClaimRank("c", new[] { "a", "b" }), Is.EqualTo((2, 3)));

			Assert.That(TeamBlackboard.ClaimRank("solo", null), Is.EqualTo((0, 1)),
				"1v1 / no allies: everything in-shard");
			Assert.That(TeamBlackboard.ClaimRank("solo", new List<string>()), Is.EqualTo((0, 1)));

			Assert.That(TeamBlackboard.ClaimRank("a", new[] { "a", "b" }), Is.EqualTo((0, 2)),
				"the own key must not double-count when a broadcast echoes it");

			Assert.That(TeamBlackboard.ClaimRank("#3", new[] { "#1", "#7" }), Is.EqualTo((1, 3)),
				"publishers without a ParticipantId still partition deterministically");
		}
	}
}
