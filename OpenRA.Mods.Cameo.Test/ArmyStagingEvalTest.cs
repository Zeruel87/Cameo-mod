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

using System.Linq;
using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	// DESIGN 19.12 / AI_ARCHITECTURE 12.28: the pure arithmetic of the army staging planner.
	[TestFixture]
	public sealed class ArmyStagingEvalTest
	{
		const long Unit = 1000;

		static long[] Rim(params (int Sector, long Value)[] weights)
		{
			var rim = new long[ArmyStagingEval.Sectors];
			foreach (var (sector, value) in weights)
				rim[sector] = value * Unit;
			return rim;
		}

		static StagingAllocation Allocate(long[] rim, long inside = 0) =>
			ArmyStagingEval.Allocate(rim, inside * Unit, 20, 3, 35, 60);

		[TestCase(10, 0, 0)]
		[TestCase(10, 10, 1)]
		[TestCase(0, 10, 2)]
		[TestCase(-10, 10, 3)]
		[TestCase(-10, 0, 4)]
		[TestCase(-10, -10, 5)]
		[TestCase(0, -10, 6)]
		[TestCase(10, -10, 7)]
		[TestCase(10, 4, 0)]
		[TestCase(10, 5, 1)]
		public void SectorOfIsAnOctantAroundTheCentre(int dx, int dy, int expected)
		{
			Assert.That(ArmyStagingEval.SectorOf(dx, dy), Is.EqualTo(expected));
		}

		[Test]
		public void SectorOfTheCentreIsNone()
		{
			Assert.That(ArmyStagingEval.SectorOf(0, 0), Is.EqualTo(-1));
		}

		[Test]
		public void StagingPointSitsInsideTheMedianArmedRadiusNeverBeyondIt()
		{
			var ring = ArmyStagingEval.RingRadius(new[] { 10, 12, 20 }, new[] { 10, 12, 20, 25 }, null, null);
			Assert.That(ring, Is.EqualTo(12));
			Assert.That(ArmyStagingEval.StagingRadius(ring, 3), Is.EqualTo(9));
			Assert.That(ArmyStagingEval.StagingRadius(2, 3), Is.EqualTo(0));
		}

		[Test]
		public void WithoutDefencesTheOutermostBuildingMakesTheRing()
		{
			var ring = ArmyStagingEval.RingRadius(new int[0], new[] { 8, 14, 11 }, new[] { 30 }, new[] { 30, 40 });
			Assert.That(ring, Is.EqualTo(14));
			Assert.That(ArmyStagingEval.RingRadius(new int[0], new int[0], new[] { 6, 10, 20 }, new[] { 30 }), Is.EqualTo(10));
			Assert.That(ArmyStagingEval.RingRadius(new int[0], new int[0], new int[0], new[] { 30, 40 }), Is.EqualTo(40));
		}

		[Test]
		public void OffsetFollowsTheSectorCentreLine()
		{
			Assert.That(ArmyStagingEval.Offset(0, 10), Is.EqualTo((10, 0)));
			Assert.That(ArmyStagingEval.Offset(6, 10), Is.EqualTo((0, -10)));
			var (x, y) = ArmyStagingEval.Offset(3, 10);
			Assert.That(x, Is.EqualTo(-7));
			Assert.That(y, Is.EqualTo(7));
		}

		[Test]
		public void AttacksFromOneSideMakeOneRimGroup()
		{
			var plan = Allocate(Rim((2, 3000)));
			Assert.That(plan.CentreMode, Is.False);
			Assert.That(plan.Groups.Select(g => g.Sector), Is.EqualTo(new[] { 2 }));
			Assert.That(plan.Groups[0].SharePct, Is.EqualTo(100));
			Assert.That(plan.ReservePct, Is.EqualTo(0));
		}

		[Test]
		public void AttacksFromTwoOppositeSidesMakeTwoGroupsBySize()
		{
			var plan = Allocate(Rim((0, 3000), (4, 1000)));
			Assert.That(plan.Groups.Select(g => g.Sector), Is.EqualTo(new[] { 0, 4 }));
			Assert.That(plan.Groups[0].SharePct, Is.EqualTo(75));
			Assert.That(plan.Groups[1].SharePct, Is.EqualTo(25));
			Assert.That(plan.Groups.Sum(g => g.SharePct) + plan.ReservePct, Is.EqualTo(100));
		}

		[Test]
		public void ASectorBelowTheActiveShareGetsNoGroup()
		{
			var plan = Allocate(Rim((0, 9000), (4, 1000)));
			Assert.That(plan.Groups.Select(g => g.Sector), Is.EqualTo(new[] { 0 }));
		}

		[Test]
		public void NoMoreThanMaxGroupsHeaviestFirst()
		{
			var plan = Allocate(Rim((0, 2500), (2, 2400), (4, 2300), (6, 2200)));
			Assert.That(plan.Groups.Count, Is.EqualTo(3));
			Assert.That(plan.Groups.Select(g => g.Sector), Is.EqualTo(new[] { 0, 2, 4 }));
			Assert.That(plan.Groups.Sum(g => g.SharePct), Is.EqualTo(100));
		}

		[Test]
		public void ATinyShareMergesIntoTheNearestGroup()
		{
			var plan = ArmyStagingEval.Allocate(Rim((0, 3000), (1, 1000), (4, 3000)), 0, 10, 3, 35, 60);
			ArmyStagingEval.MergeSmallGroups(plan.Groups, 4000, 1500);

			// The sector-1 group would hold 14% of 4000 = 570 < 1500: it joins sector 0, its neighbour.
			Assert.That(plan.Groups.Select(g => g.Sector).OrderBy(s => s), Is.EqualTo(new[] { 0, 4 }));
			Assert.That(plan.Groups.Sum(g => g.SharePct), Is.EqualTo(100));
			Assert.That(plan.Groups.Single(g => g.Sector == 0).SharePct, Is.GreaterThan(plan.Groups.Single(g => g.Sector == 4).SharePct));
		}

		[Test]
		public void AGroupOfEnoughValueIsKept()
		{
			var plan = Allocate(Rim((0, 3000), (4, 3000)));
			ArmyStagingEval.MergeSmallGroups(plan.Groups, 20000, 1500);
			Assert.That(plan.Groups.Count, Is.EqualTo(2));
		}

		[Test]
		public void ASmallArmyCollapsesToOneGroup()
		{
			var plan = Allocate(Rim((0, 3000), (4, 3000)));
			ArmyStagingEval.MergeSmallGroups(plan.Groups, 1000, 1500);
			Assert.That(plan.Groups.Count, Is.EqualTo(1));
			Assert.That(plan.Groups[0].SharePct, Is.EqualTo(100));
		}

		[Test]
		public void InsideAttacksTakeASmallReserveCappedByReserveMax()
		{
			var plan = Allocate(Rim((0, 3000)), 1500);

			// Inside share = 1500 / 4500 = 33%: under the 35% cap, over nothing else.
			Assert.That(plan.CentreMode, Is.False);
			Assert.That(plan.ReservePct, Is.EqualTo(33));
			Assert.That(plan.Groups.Sum(g => g.SharePct) + plan.ReservePct, Is.EqualTo(100));

			var heavier = Allocate(Rim((0, 3000)), 3000);
			Assert.That(heavier.ReservePct, Is.EqualTo(35));
		}

		[Test]
		public void InsideHeavyAttacksSendTheWholeArmyToTheCentre()
		{
			var plan = Allocate(Rim((0, 1000)), 6000);
			Assert.That(plan.CentreMode, Is.True);
			Assert.That(plan.Groups, Is.Empty);
			Assert.That(plan.ReservePct, Is.EqualTo(100));
		}

		[Test]
		public void NoWeightAtAllPlansNothing()
		{
			var plan = Allocate(Rim());
			Assert.That(plan.Groups, Is.Empty);
			Assert.That(plan.ReservePct, Is.EqualTo(0));
			Assert.That(plan.CentreMode, Is.False);
		}

		[Test]
		public void NoEventsStageTowardThePriorDirection()
		{
			// One spawn candidate to the north-east, nothing learned yet.
			var prior = ArmyStagingEval.PriorMilli(new[] { 0, 0, 0, 0, 0, 0, 0, 1 }, 2000 * Unit);
			var plan = ArmyStagingEval.Allocate(prior, 0, 20, 3, 35, 60);
			Assert.That(plan.Groups.Select(g => g.Sector), Is.EqualTo(new[] { 7 }));
		}

		[Test]
		public void RealEventsOutweighThePriorAndThenFadeBackToIt()
		{
			var prior = ArmyStagingEval.PriorMilli(new[] { 0, 0, 0, 0, 0, 0, 0, 1 }, 2000 * Unit);
			var learned = new long[ArmyStagingEval.Sectors];
			learned[2] = 8000 * Unit;

			long[] Sum() => Enumerable.Range(0, ArmyStagingEval.Sectors).Select(i => learned[i] + prior[i]).ToArray();
			Assert.That(ArmyStagingEval.Allocate(Sum(), 0, 30, 3, 35, 60).Groups.Select(g => g.Sector), Is.EqualTo(new[] { 2 }));

			// Many half-lives later the learned weight is gone and the prior direction leads again.
			for (var i = 0; i < 400; i++)
				learned[2] = ArmyStagingEval.Decay(learned[2], 25, 3000);

			Assert.That(ArmyStagingEval.Allocate(Sum(), 0, 20, 3, 35, 60).Groups[0].Sector, Is.EqualTo(7));
		}

		[Test]
		public void DecayHalvesAboutEveryHalfLife()
		{
			var w = 1000L * Unit;
			for (var i = 0; i < 120; i++)
				w = ArmyStagingEval.Decay(w, 25, 3000);

			// 3000 ticks: close to a half (linear steps give a little under).
			Assert.That(w, Is.InRange(450L * Unit, 550L * Unit));
		}

		[Test]
		public void ASmallWeightStillDecaysToZero()
		{
			var w = 5L;
			for (var i = 0; i < 10; i++)
				w = ArmyStagingEval.Decay(w, 25, 3000);
			Assert.That(w, Is.EqualTo(0));
		}

		[Test]
		public void AlliedSpawnsAreNotEnemyCandidates()
		{
			var spawns = new[] { new CPos(10, 10), new CPos(90, 10), new CPos(10, 90), new CPos(90, 90) };
			var homes = new[] { new CPos(11, 10), new CPos(10, 89) };
			var candidates = ArmyStagingEval.EnemySpawnCandidates(spawns, homes, 8);
			Assert.That(candidates, Is.EqualTo(new[] { new CPos(90, 10), new CPos(90, 90) }));
		}

		[Test]
		public void LiveAttackOnOneSideSendsEveryGroupAndTheReserveThere()
		{
			var live = new long[ArmyStagingEval.Sectors];
			live[4] = 1200;
			var targets = ArmyStagingEval.LiveTargets(new[] { 0, 4, 2 }, live, 0);
			Assert.That(targets.Live, Is.True);
			Assert.That(targets.GroupTargets, Is.EqualTo(new[] { 4, 4, 4 }));
			Assert.That(targets.ReserveTarget, Is.EqualTo(4));
		}

		[Test]
		public void LiveAttacksOnTwoSidesSplitTheGroupsAndTheReserveTakesTheHeaviest()
		{
			var live = new long[ArmyStagingEval.Sectors];
			live[0] = 500;
			live[4] = 1500;
			var targets = ArmyStagingEval.LiveTargets(new[] { 0, 4 }, live, 0);
			Assert.That(targets.GroupTargets, Is.EqualTo(new[] { 0, 4 }));
			Assert.That(targets.ReserveTarget, Is.EqualTo(4));
		}

		[Test]
		public void NoLiveAttackKeepsTheStagingPlan()
		{
			var targets = ArmyStagingEval.LiveTargets(new[] { 0, 4 }, new long[ArmyStagingEval.Sectors], 0);
			Assert.That(targets.Live, Is.False);
			Assert.That(targets.GroupTargets, Is.EqualTo(new[] { 0, 4 }));
			Assert.That(targets.ReserveTarget, Is.EqualTo(-1));
		}

		[Test]
		public void AnInsideLiveAttackSendsOnlyTheReserveToTheCentre()
		{
			var targets = ArmyStagingEval.LiveTargets(new[] { 0, 4 }, new long[ArmyStagingEval.Sectors], 900);
			Assert.That(targets.Live, Is.True);
			Assert.That(targets.GroupTargets, Is.EqualTo(new[] { 0, 4 }));
			Assert.That(targets.ReserveTarget, Is.EqualTo(-1));
		}

		[Test]
		public void GroupsReturnOnlyAfterTheQuietWindow()
		{
			Assert.That(ArmyStagingEval.ShouldReturn(374, 375), Is.False);
			Assert.That(ArmyStagingEval.ShouldReturn(375, 375), Is.True);
		}

		[Test]
		public void UnitsAreSplitByValueAcrossTheShares()
		{
			var parts = ArmyStagingEval.AssignByValue(new long[] { 500, 500, 500, 500 }, new[] { 50, 50 });
			Assert.That(parts, Is.EqualTo(new[] { 0, 0, 1, 1 }));

			var reserve = ArmyStagingEval.AssignByValue(new long[] { 500, 500, 500, 500 }, new[] { 100 });
			Assert.That(reserve, Is.EqualTo(new[] { 0, 0, 0, 0 }));
		}
	}
}
