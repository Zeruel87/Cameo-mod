#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software.
 * It is made available under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public sealed class ExpansionPlannerBotModuleTest
	{
		// AI_ARCHITECTURE §12.13: score = V x S / (T + tau), S = 1 / (1 + threat / max(guard, 1)).
		static double Score(int value, int threat = 0, int guard = 0, int cost = 2000, int income = 10, int hops = 0)
		{
			return ExpansionPlannerBotModule.Score(value, threat, guard, cost, income, hops, 300, 900, 750, out _);
		}

		[Test]
		public void MoreValueRanksHigher()
		{
			Assert.That(Score(80), Is.GreaterThan(Score(40)));
		}

		[Test]
		public void ShorterDistanceRanksHigher()
		{
			Assert.That(Score(60, hops: 0), Is.GreaterThan(Score(60, hops: 3)));
		}

		[Test]
		public void FewerRememberedEnemiesRankSafer()
		{
			Assert.That(Score(60, threat: 0), Is.GreaterThan(Score(60, threat: 3000)));

			// Our own guard at the field offsets the threat.
			Assert.That(Score(60, threat: 3000, guard: 6000), Is.GreaterThan(Score(60, threat: 3000, guard: 0)));
		}

		[Test]
		public void PaybackTurnsCostIntoTicksAtTheCurrentIncome()
		{
			ExpansionPlannerBotModule.Score(60, 0, 0, 2000, 10, 2, 300, 900, 750, out var payback);

			// 2000 / 10 per tick + 2 links x 300 + the refinery's 900.
			Assert.That(payback, Is.EqualTo(200 + 600 + 900));
		}

		[Test]
		public void NoIncomeMakesEveryFieldSlowButStillRanksThem()
		{
			Assert.That(Score(80, income: 0), Is.GreaterThan(Score(40, income: 0)));
		}

		[Test]
		public void HopsCountTheBuildingsNeededToReachAField()
		{
			Assert.That(ExpansionPlannerBotModule.Hops(10, 12, 4), Is.EqualTo(0));
			Assert.That(ExpansionPlannerBotModule.Hops(13, 12, 4), Is.EqualTo(1));
			Assert.That(ExpansionPlannerBotModule.Hops(20, 12, 4), Is.EqualTo(2));
			Assert.That(ExpansionPlannerBotModule.Hops(21, 12, 4), Is.EqualTo(3));
		}

		[Test]
		public void ARefineryWithinTheClaimRadiusClaimsTheField()
		{
			var field = new CPos(16, 36);
			Assert.That(ExpansionPlannerBotModule.Claimed(field, new[] { new CPos(20, 40) }, 8), Is.True);
			Assert.That(ExpansionPlannerBotModule.Claimed(field, new[] { new CPos(30, 36) }, 8), Is.False);
			Assert.That(ExpansionPlannerBotModule.Claimed(field, new CPos[0], 8), Is.False);
		}

		[Test]
		public void RefineriesBuiltWithoutClaimingTheFieldParkItAfterTheLimit()
		{
			// Start wanting field 6 with 1 refinery owned.
			var (state, attempts, park) = ExpansionPlannerBotModule.TrackClaim((-1, 0), 6, 1, 0, 2);
			Assert.That(state, Is.EqualTo((6, 1)));
			Assert.That(park, Is.False);

			// A refinery appears elsewhere, the field is still unclaimed: one missed attempt.
			(state, attempts, park) = ExpansionPlannerBotModule.TrackClaim(state, 6, 2, attempts, 2);
			Assert.That(attempts, Is.EqualTo(1));
			Assert.That(park, Is.False);

			// A second miss reaches the limit: park the field instead of building refineries forever.
			(_, attempts, park) = ExpansionPlannerBotModule.TrackClaim(state, 6, 3, attempts, 2);
			Assert.That(attempts, Is.EqualTo(2));
			Assert.That(park, Is.True);
		}

		[Test]
		public void ANewTargetStartsItsOwnCount()
		{
			var (state, attempts, park) = ExpansionPlannerBotModule.TrackClaim((6, 3), 7, 5, 0, 2);
			Assert.That(state, Is.EqualTo((7, 5)));
			Assert.That(attempts, Is.EqualTo(0));
			Assert.That(park, Is.False);
		}

		static ExpansionPlannerBotModule.FieldScore Field(int index, int x, int y, int value, int hops, double safety = 1)
		{
			return new ExpansionPlannerBotModule.FieldScore(index, new CPos(x, y), value, hops, 0, 0, 0, safety);
		}

		[Test]
		public void TheMcvGoesToAFarFieldNeverOneTheBuildingLineReaches()
		{
			var fields = new[] { Field(1, 12, 12, 200, 1), Field(2, 40, 10, 60, 5) };
			var site = ExpansionPlannerBotModule.McvSite(fields, new CPos(10, 10), 3, 10);
			Assert.That(site?.Index, Is.EqualTo(2));
			Assert.That(ExpansionPlannerBotModule.McvSite(new[] { Field(1, 12, 12, 200, 1) }, new CPos(10, 10), 3, 10), Is.Null);
		}

		[Test]
		public void TheMcvWeighsValueSafetyAndDistance()
		{
			var mcv = new CPos(10, 10);

			// Same distance: the richer field wins.
			Assert.That(ExpansionPlannerBotModule.McvSite(new[] { Field(1, 40, 10, 60, 4), Field(2, 10, 40, 90, 4) }, mcv, 3, 10)?.Index, Is.EqualTo(2));

			// Same value: the safer field wins.
			Assert.That(ExpansionPlannerBotModule.McvSite(new[] { Field(1, 40, 10, 60, 4, 0.25), Field(2, 10, 40, 60, 4, 1) }, mcv, 3, 10)?.Index, Is.EqualTo(2));

			// Same value and safety: the nearer field wins.
			Assert.That(ExpansionPlannerBotModule.McvSite(new[] { Field(1, 60, 10, 60, 4), Field(2, 30, 10, 60, 4) }, mcv, 3, 10)?.Index, Is.EqualTo(2));
		}

		[Test]
		public void AnIneligibleFieldFallsOutAndTheNextBestIsOffered()
		{
			// LC3: an unreachable or parked field is skipped, never handed to the MCV again.
			var fields = new[] { Field(1, 40, 10, 90, 4), Field(2, 10, 40, 60, 4) };
			var mcv = new CPos(10, 10);
			Assert.That(ExpansionPlannerBotModule.McvSite(fields, mcv, 3, 10)?.Index, Is.EqualTo(1));
			Assert.That(ExpansionPlannerBotModule.McvSite(fields, mcv, 3, 10, f => f.Index != 1)?.Index, Is.EqualTo(2));
			Assert.That(ExpansionPlannerBotModule.McvSite(fields, mcv, 3, 10, f => false), Is.Null);
		}

		[Test]
		public void AFieldHandedOutTooOftenInARowIsParked()
		{
			// LC3: the MCV module only asks again for an idle MCV, so a repeat means the last attempt failed.
			var streak = (Field: -1, Count: 0);
			for (var i = 1; i <= 3; i++)
			{
				(streak, var park) = ExpansionPlannerBotModule.TrackMcvHandout(streak, 7, 3);
				Assert.That(park, Is.False);
				Assert.That(streak.Count, Is.EqualTo(i));
			}

			(streak, var parked) = ExpansionPlannerBotModule.TrackMcvHandout(streak, 7, 3);
			Assert.That(parked, Is.True);
			Assert.That(streak, Is.EqualTo((-1, 0)));

			// A different field restarts the streak; 0 disables parking.
			Assert.That(ExpansionPlannerBotModule.TrackMcvHandout((7, 3), 8, 3), Is.EqualTo(((8, 1), false)));
			Assert.That(ExpansionPlannerBotModule.TrackMcvHandout((7, 50), 7, 0).Park, Is.False);
		}

		[Test]
		public void BevSendsOnlyBaseBuildingVehiclesHome()
		{
			// Construction MCVs found bases at fields (EX-3); Yuri's slave miner and Japan's core refinery deploy into
			// refineries and go to fields too; Japan's other cores are base buildings and deploy at home.
			Assert.That(ExpansionPlannerBotModule.ClassifyMcv(constructionMcv: true, deploysIntoRefinery: false), Is.EqualTo(McvRole.Expansion));
			Assert.That(ExpansionPlannerBotModule.ClassifyMcv(constructionMcv: true, deploysIntoRefinery: true), Is.EqualTo(McvRole.Expansion),
				"a StarCraft command centre is a construction MCV that also accepts resources: still an expansion");
			Assert.That(ExpansionPlannerBotModule.ClassifyMcv(constructionMcv: false, deploysIntoRefinery: true), Is.EqualTo(McvRole.FieldRefinery));
			Assert.That(ExpansionPlannerBotModule.ClassifyMcv(constructionMcv: false, deploysIntoRefinery: false), Is.EqualTo(McvRole.BaseBuilding));
		}
	}
}
