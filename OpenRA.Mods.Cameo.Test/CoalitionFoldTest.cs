#region Copyright & License Information
/*
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	// TC-3 (AI_ARCHITECTURE.md §12.18): the coalition fold. Every member computes
	// the identical directive from the same broadcast set, so the tests pin the
	// arithmetic: target votes, phase precedence, rescue election determinism,
	// and the Voronoi sector score.
	[TestFixture]
	public sealed class CoalitionFoldTest
	{
		// Uninitialised Players stand in for real ones — only reference identity
		// matters to the vote (same fixture trick as TeamBlackboardTest).
		static OpenRA.Player FakePlayer() =>
			(OpenRA.Player)RuntimeHelpers.GetUninitializedObject(typeof(OpenRA.Player));

		static TeamBroadcast Broadcast(int clientIndex, int ownArmyValue = 0, int urgencyLevel = 0,
			int directorTension = 0, DirectorPhase directorPhase = DirectorPhase.BuildUp,
			OpenRA.Player mainTarget = null, bool requestsDefence = false, WPos defendPosition = default,
			WPos armyCentroid = default, WPos spawnPoint = default, string participantId = null,
			WPos expansionAssist = default) =>
			new(1500, ownArmyValue, urgencyLevel, directorTension, directorPhase, mainTarget,
				requestsDefence, defendPosition, clientIndex, default, armyCentroid, expansionAssist, spawnPoint,
				null, participantId);

		[Test]
		public void EmptyInputYieldsEmptyDirective()
		{
			var d = CoalitionFold.Compute(null, null);
			Assert.That(d.MainTarget, Is.Null);
			Assert.That(d.Phase, Is.EqualTo(CoalitionPhase.BuildUp));
			Assert.That(d.RescueAssignments, Is.Empty);
			Assert.That(d.SectorAnchors, Is.Empty);
		}

		[Test]
		public void SoloBroadcastDegradesToOwn()
		{
			var t = FakePlayer();
			var own = Broadcast(3, ownArmyValue: 5000, mainTarget: t);
			var d = CoalitionFold.Compute(own, new List<TeamBroadcast>());
			Assert.That(d.MainTarget, Is.SameAs(t));
			Assert.That(d.RescueAssignments, Is.Empty);
		}

		[Test]
		public void MainTargetVotePicksTheMostSharedTarget()
		{
			var a = FakePlayer();
			var b = FakePlayer();
			var own = Broadcast(0, mainTarget: a);
			var allies = new List<TeamBroadcast>
			{
				Broadcast(1, mainTarget: b),
				Broadcast(2, mainTarget: b, directorTension: 90),
			};

			Assert.That(CoalitionFold.Compute(own, allies).MainTarget, Is.SameAs(b));
		}

		[Test]
		public void MainTargetTieBreaksToHigherTensionThenLowerIndex()
		{
			var a = FakePlayer();
			var b = FakePlayer();
			var allies = new List<TeamBroadcast>
			{
				Broadcast(5, mainTarget: a, directorTension: 10),
				Broadcast(4, mainTarget: b, directorTension: 80),
			};

			Assert.That(CoalitionFold.Compute(null, allies).MainTarget, Is.SameAs(b));

			// Equal tension: lowest ClientIndex publisher wins.
			var lowIndex = new List<TeamBroadcast>
			{
				Broadcast(5, mainTarget: a, directorTension: 10),
				Broadcast(4, mainTarget: b, directorTension: 10),
			};
			Assert.That(CoalitionFold.Compute(null, lowIndex).MainTarget, Is.SameAs(b));
		}

		[Test]
		public void PushNeedsTargetAndClimax_DefendOverrides()
		{
			var t = FakePlayer();
			var quiet = new List<TeamBroadcast> { Broadcast(1, mainTarget: t) };
			Assert.That(CoalitionFold.Compute(null, quiet).Phase, Is.EqualTo(CoalitionPhase.BuildUp));

			var wave = new List<TeamBroadcast>
			{
				Broadcast(1, mainTarget: t),
				Broadcast(2, directorPhase: DirectorPhase.Climax),
			};
			Assert.That(CoalitionFold.Compute(null, wave).Phase, Is.EqualTo(CoalitionPhase.Push));

			var emergency = new List<TeamBroadcast>(wave)
			{
				Broadcast(3, urgencyLevel: 2, requestsDefence: true, defendPosition: new WPos(1000, 1000, 0)),
			};
			Assert.That(CoalitionFold.Compute(null, emergency).Phase, Is.EqualTo(CoalitionPhase.Defend));
		}

		[Test]
		public void RescueElectionPicksNearestFreeAlly()
		{
			var defendAt = new WPos(1000, 1000, 0);
			var requester = Broadcast(0, urgencyLevel: 2, requestsDefence: true, defendPosition: defendAt);
			var near = Broadcast(1, armyCentroid: new WPos(1100, 1000, 0));
			var far = Broadcast(2, armyCentroid: new WPos(9000, 9000, 0));

			var d = CoalitionFold.Compute(requester, new List<TeamBroadcast> { near, far });
			Assert.That(d.RescueAssignments.Count, Is.EqualTo(1));
			Assert.That(d.RescueAssignments[0].ResponderClientIndex, Is.EqualTo(1));
			Assert.That(d.RescueAssignments[0].RequesterClientIndex, Is.EqualTo(0));

			// Every member computes the same election — swap own/allies roles.
			var d2 = CoalitionFold.Compute(near, new List<TeamBroadcast> { requester, far });
			Assert.That(d2.RescueAssignments[0].ResponderClientIndex, Is.EqualTo(1));
		}

		[Test]
		public void RequesterNeverRescuesAndZeroCentroidIsNeverElected()
		{
			var defendAt = new WPos(1000, 1000, 0);
			var allies = new List<TeamBroadcast>
			{
				Broadcast(1, urgencyLevel: 2, requestsDefence: true, defendPosition: defendAt,
					armyCentroid: new WPos(1001, 1001, 0)),
				Broadcast(2), // zero centroid — no army
				Broadcast(3, armyCentroid: new WPos(5000, 5000, 0)),
			};

			var d = CoalitionFold.Compute(null, allies);
			Assert.That(d.RescueAssignments.Count, Is.EqualTo(1));
			Assert.That(d.RescueAssignments[0].ResponderClientIndex, Is.EqualTo(3));
		}

		[Test]
		public void RescueElectionConsumesThePool()
		{
			// Post-merge audit 4.3: two simultaneous requests elect DISTINCT responders —
			// an elected responder leaves the free pool instead of answering twice.
			var allies = new List<TeamBroadcast>
			{
				Broadcast(0, urgencyLevel: 2, requestsDefence: true, defendPosition: new WPos(1000, 1000, 0)),
				Broadcast(1, urgencyLevel: 2, requestsDefence: true, defendPosition: new WPos(1200, 1000, 0)),
				Broadcast(2, armyCentroid: new WPos(1100, 1000, 0)),
				Broadcast(3, armyCentroid: new WPos(5000, 5000, 0)),
			};

			var d = CoalitionFold.Compute(null, allies);
			Assert.That(d.RescueAssignments.Count, Is.EqualTo(2));
			Assert.That(d.RescueAssignments[0].ResponderClientIndex,
				Is.Not.EqualTo(d.RescueAssignments[1].ResponderClientIndex));

			// More requests than responders: the pool runs dry, nobody double-books.
			var d2 = CoalitionFold.Compute(null, new List<TeamBroadcast>(allies) { allies[0] });
			Assert.That(d2.RescueAssignments.Select(a => a.ResponderClientIndex).Distinct().Count(),
				Is.EqualTo(d2.RescueAssignments.Count));
		}

		[Test]
		public void SameClientIndexMapBotsStayDistinct()
		{
			// Post-merge audit 4.4: map-side bots can inherit the host's ClientIndex —
			// participant id keeps them distinct in elections and sectors.
			var allies = new List<TeamBroadcast>
			{
				Broadcast(0, spawnPoint: new WPos(512, 512, 0), participantId: "MapBotA"),
				Broadcast(0, spawnPoint: new WPos(8000, 512, 0), participantId: "MapBotB"),
			};
			var d = CoalitionFold.Compute(null, allies);
			Assert.That(d.SectorAnchors.Count, Is.EqualTo(2));
			Assert.That(d.SectorAnchors["MapBotA"], Is.EqualTo(new WPos(512, 512, 0)));
			Assert.That(d.SectorAnchors["MapBotB"], Is.EqualTo(new WPos(8000, 512, 0)));
		}

		[Test]
		public void SectorAnchorsFoldDeterministically()
		{
			var allies = new List<TeamBroadcast>
			{
				Broadcast(7, spawnPoint: new WPos(512, 512, 0)),
				Broadcast(2, spawnPoint: new WPos(8000, 512, 0)),
			};
			var d = CoalitionFold.Compute(Broadcast(9, spawnPoint: new WPos(512, 8000, 0)), allies);
			Assert.That(d.SectorAnchors.Count, Is.EqualTo(3));
			Assert.That(d.SectorAnchors["#7"], Is.EqualTo(new WPos(512, 512, 0)));
			Assert.That(d.SectorAnchors["#2"], Is.EqualTo(new WPos(8000, 512, 0)));
			Assert.That(d.SectorAnchors["#9"], Is.EqualTo(new WPos(512, 8000, 0)));
		}

		[Test]
		public void SectorScorePercentOwnsNearestAnchor()
		{
			var anchors = new Dictionary<string, WPos>
			{
				["a"] = new WPos(0, 0, 0),
				["b"] = new WPos(10000, 0, 0),
			};

			Assert.That(OpenRA.Mods.Cameo.Traits.BotModules.ExpansionPlannerBotModule.SectorScorePercent(
				new WPos(100, 0, 0), anchors, "a", 35), Is.EqualTo(100));
			Assert.That(OpenRA.Mods.Cameo.Traits.BotModules.ExpansionPlannerBotModule.SectorScorePercent(
				new WPos(100, 0, 0), anchors, "b", 35), Is.EqualTo(35));

			// No anchors: everything scores full.
			Assert.That(OpenRA.Mods.Cameo.Traits.BotModules.ExpansionPlannerBotModule.SectorScorePercent(
				new WPos(100, 0, 0), new Dictionary<string, WPos>(), "a", 35), Is.EqualTo(100));
		}

		[Test]
		public void AssistElectionPicksNearestFreeAlly()
		{
			// §12.28: the second election pass routes an escort to a contested claim —
			// nearest ArmyCentroid to the published ExpansionAssist, ParticipantKey
			// tie-break, same arithmetic as the rescue pass.
			var assistAt = new WPos(4000, 4000, 0);
			var requester = Broadcast(0, expansionAssist: assistAt);
			var near = Broadcast(1, armyCentroid: new WPos(4200, 4000, 0));
			var far = Broadcast(2, armyCentroid: new WPos(9000, 9000, 0));

			var d = CoalitionFold.Compute(requester, new List<TeamBroadcast> { near, far });
			Assert.That(d.AssistAssignments.Count, Is.EqualTo(1));
			Assert.That(d.AssistAssignments[0].RequesterClientIndex, Is.EqualTo(0));
			Assert.That(d.AssistAssignments[0].ResponderClientIndex, Is.EqualTo(1));
			Assert.That(d.AssistAssignments[0].AssistPosition, Is.EqualTo(assistAt));
			Assert.That(d.AssistAssignments[0].RequesterId, Is.EqualTo("#0"));
			Assert.That(d.AssistAssignments[0].ResponderId, Is.EqualTo("#1"));

			// Every member computes the same election — swap own/allies roles.
			var d2 = CoalitionFold.Compute(near, new List<TeamBroadcast> { requester, far });
			Assert.That(d2.AssistAssignments[0].ResponderClientIndex, Is.EqualTo(1));
		}

		[Test]
		public void AssistRequesterNeverElectsItself()
		{
			// Assist requesters were never excluded from the free pool (only defend
			// requesters are) — without the self-skip an army at its own claim would
			// escort itself, the nearest possible responder.
			var allies = new List<TeamBroadcast>
			{
				Broadcast(1, expansionAssist: new WPos(4000, 4000, 0),
					armyCentroid: new WPos(4100, 4000, 0)),
				Broadcast(2, armyCentroid: new WPos(9000, 9000, 0)),
			};

			var d = CoalitionFold.Compute(null, allies);
			Assert.That(d.AssistAssignments.Count, Is.EqualTo(1));
			Assert.That(d.AssistAssignments[0].ResponderClientIndex, Is.EqualTo(2));

			// The requester alone in the pool: no responder exists at all.
			var solo = CoalitionFold.Compute(null, new List<TeamBroadcast> { allies[0] });
			Assert.That(solo.AssistAssignments, Is.Empty);
		}

		[Test]
		public void AssistElectsOnlyWhatRescueLeaves()
		{
			// Shared capacity, survival first: the rescue pass drains the pool before
			// assist elects, so the one free army answers the defend request and the
			// contested claim stands down until the next fold.
			var allies = new List<TeamBroadcast>
			{
				Broadcast(0, urgencyLevel: 2, requestsDefence: true, defendPosition: new WPos(1000, 1000, 0)),
				Broadcast(1, expansionAssist: new WPos(4000, 4000, 0)),
				Broadcast(2, armyCentroid: new WPos(3000, 3000, 0)),
			};

			var d = CoalitionFold.Compute(null, allies);
			Assert.That(d.RescueAssignments.Count, Is.EqualTo(1));
			Assert.That(d.RescueAssignments[0].ResponderClientIndex, Is.EqualTo(2));
			Assert.That(d.AssistAssignments, Is.Empty);

			// A second free army frees one answer for the assist — and still nobody
			// answers two requests in one fold.
			var d2 = CoalitionFold.Compute(null, new List<TeamBroadcast>(allies)
			{
				Broadcast(3, armyCentroid: new WPos(4500, 3000, 0)),
			});
			Assert.That(d2.RescueAssignments.Count, Is.EqualTo(1));
			Assert.That(d2.AssistAssignments.Count, Is.EqualTo(1));
			Assert.That(d2.AssistAssignments[0].ResponderClientIndex, Is.EqualTo(3));
			Assert.That(d2.AssistAssignments[0].ResponderClientIndex,
				Is.Not.EqualTo(d2.RescueAssignments[0].ResponderClientIndex));
		}

		[Test]
		public void AssistElectionConsumesTheSharedPool()
		{
			// Two simultaneous assist requests elect DISTINCT responders from what
			// the rescue pass left — the elected escort leaves the pool, so requests
			// beyond the pool's depth go unanswered this fold.
			var allies = new List<TeamBroadcast>
			{
				Broadcast(0, expansionAssist: new WPos(4000, 4000, 0)),
				Broadcast(1, expansionAssist: new WPos(6000, 6000, 0)),
				Broadcast(2, armyCentroid: new WPos(4100, 4000, 0)),
				Broadcast(3, armyCentroid: new WPos(6100, 6000, 0)),
			};

			var d = CoalitionFold.Compute(null, allies);
			Assert.That(d.AssistAssignments.Count, Is.EqualTo(2));
			Assert.That(d.AssistAssignments.Select(a => a.ResponderClientIndex).Distinct().Count(),
				Is.EqualTo(2));
		}

		[Test]
		public void NoAssistRequestYieldsEmptyAssistList()
		{
			// Staleness is not the fold's concern — CollectBroadcasts filters dead or
			// expired publishers before Compute ever sees them, so the fold only needs
			// the Zero-field contract: no published assist, no assignments.
			var allies = new List<TeamBroadcast>
			{
				Broadcast(0, armyCentroid: new WPos(1000, 1000, 0)),
				Broadcast(1, armyCentroid: new WPos(2000, 2000, 0)),
			};

			Assert.That(CoalitionFold.Compute(null, allies).AssistAssignments, Is.Empty);
			Assert.That(CoalitionFold.Compute(null, null).AssistAssignments, Is.Empty);
			Assert.That(CoalitionDirective.Empty.AssistAssignments, Is.Empty);
		}
	}
}
