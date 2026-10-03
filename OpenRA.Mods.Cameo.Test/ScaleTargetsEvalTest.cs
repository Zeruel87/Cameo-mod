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
	// DESIGN 19.10 / AI_ARCHITECTURE 12.22: the pure growth law. Lines are the ai.yaml defaults, in thousandths.
	[TestFixture]
	public class ScaleTargetsEvalTest
	{
		const int Tiers = 10;
		const int TicksPerMinute = 1500;
		const int Neutral = 1000;

		static readonly ScaleLine Tech = new(1000, 3250, 600, 1400, 500, 500, 1);
		static readonly ScaleLine Refinery = new(1000, 10000, 600, 1400, 500, 500, 1);
		static readonly ScaleLine Harvester = new(3000, 30000, 600, 1400, 500, 500, 1);
		static readonly ScaleLine Production = new(1500, 7500, 600, 1400, 500, 500, 1);
		static readonly ScaleLine Conyard = new(1500, 7500, 600, 1400, 500, 500, 1);

		static int[] Line(ScaleLine line, long gameTicks = 0, long seen = 0, int unscouted = 0, int team = 1, int p = Neutral, int cap = -1) =>
			Enumerable.Range(0, Tiers)
				.Select(t => ScaleTargetsEval.Target(line, t, Tiers, gameTicks, TicksPerMinute, seen, unscouted, team, p, 1, cap))
				.ToArray();

		[Test]
		public void TechLineFloorsToOneOneOneOneTwoTwoTwoTwoThreeThree()
		{
			Assert.That(Line(Tech), Is.EqualTo(new[] { 1, 1, 1, 1, 2, 2, 2, 2, 3, 3 }));
		}

		[Test]
		public void MinuteZeroNothingSeenReproducesTheDifficultyTable()
		{
			Assert.That(Line(Refinery), Is.EqualTo(new[] { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 }));
			Assert.That(Line(Harvester), Is.EqualTo(new[] { 3, 6, 9, 12, 15, 18, 21, 24, 27, 30 }));
			Assert.That(Line(Production), Is.EqualTo(new[] { 1, 2, 2, 3, 4, 4, 5, 6, 6, 7 }));
			Assert.That(Line(Conyard), Is.EqualTo(new[] { 1, 2, 2, 3, 4, 4, 5, 6, 6, 7 }));
		}

		[Test]
		public void ABiggerSeenEnemyRaisesTheTarget()
		{
			var none = ScaleTargetsEval.Target(Refinery, 4, Tiers, 0, TicksPerMinute, 0, 0, 1, Neutral, 1, -1);
			var some = ScaleTargetsEval.Target(Refinery, 4, Tiers, 0, TicksPerMinute, 8, 0, 1, Neutral, 1, -1);
			var more = ScaleTargetsEval.Target(Refinery, 4, Tiers, 0, TicksPerMinute, 16, 0, 1, Neutral, 1, -1);
			Assert.That(none, Is.EqualTo(5));
			Assert.That(some, Is.GreaterThan(none));
			Assert.That(more, Is.GreaterThan(some));

			// Hard (tier 4) ratio is 0.955 on the 0.6 -> 1.4 line: eight seen refineries ask for floor(7.64) = 7.
			Assert.That(some, Is.EqualTo(7));
		}

		[Test]
		public void MoreUnscoutedAreaRaisesTheEnemyTerm()
		{
			var lit = ScaleTargetsEval.Target(Refinery, 4, Tiers, 0, TicksPerMinute, 10, 0, 1, Neutral, 1, -1);
			var half = ScaleTargetsEval.Target(Refinery, 4, Tiers, 0, TicksPerMinute, 10, 500, 1, Neutral, 1, -1);
			var dark = ScaleTargetsEval.Target(Refinery, 4, Tiers, 0, TicksPerMinute, 10, 1000, 1, Neutral, 1, -1);
			Assert.That(lit, Is.EqualTo(9));
			Assert.That(half, Is.GreaterThan(lit));
			Assert.That(dark, Is.GreaterThan(half));

			// Margin 0.5 on a fully dark map: 9.55 x 1.5 = 14.3.
			Assert.That(dark, Is.EqualTo(14));
		}

		[Test]
		public void TeamSizeDividesTheEnemyTerm()
		{
			var solo = ScaleTargetsEval.Target(Refinery, 4, Tiers, 0, TicksPerMinute, 20, 0, 1, Neutral, 1, -1);
			var duo = ScaleTargetsEval.Target(Refinery, 4, Tiers, 0, TicksPerMinute, 20, 0, 2, Neutral, 1, -1);
			var squad = ScaleTargetsEval.Target(Refinery, 4, Tiers, 0, TicksPerMinute, 20, 0, 4, Neutral, 1, -1);
			Assert.That(solo, Is.EqualTo(19));
			Assert.That(duo, Is.EqualTo(9));

			// 4.775 over four players sinks under the own line (5): the own line is the floor of the ambition.
			Assert.That(squad, Is.EqualTo(5));
		}

		[Test]
		public void TimeGrowthRaisesTheOwnLineLinearlyWithNoCap()
		{
			// Growth 500 per hour: +50% of the own line per 60 game minutes.
			var hourTicks = 60L * TicksPerMinute;
			var start = ScaleTargetsEval.Target(Harvester, 4, Tiers, 0, TicksPerMinute, 0, 0, 1, Neutral, 1, -1);
			var hour = ScaleTargetsEval.Target(Harvester, 4, Tiers, hourTicks, TicksPerMinute, 0, 0, 1, Neutral, 1, -1);
			var two = ScaleTargetsEval.Target(Harvester, 4, Tiers, 2 * hourTicks, TicksPerMinute, 0, 0, 1, Neutral, 1, -1);
			var ten = ScaleTargetsEval.Target(Harvester, 4, Tiers, 10 * hourTicks, TicksPerMinute, 0, 0, 1, Neutral, 1, -1);
			Assert.That(start, Is.EqualTo(15));
			Assert.That(hour, Is.EqualTo(22));
			Assert.That(two, Is.EqualTo(30));
			Assert.That(ten, Is.EqualTo(90));
		}

		[Test]
		public void PersonalityMultiplierScalesTheWholeTarget()
		{
			var plain = ScaleTargetsEval.Target(Tech, 8, Tiers, 0, TicksPerMinute, 0, 0, 1, Neutral, 1, -1);
			var techy = ScaleTargetsEval.Target(Tech, 8, Tiers, 0, TicksPerMinute, 0, 0, 1, 1500, 1, -1);
			Assert.That(plain, Is.EqualTo(3));
			Assert.That(techy, Is.EqualTo(4));
		}

		[Test]
		public void AxisLeanIsNeutralAtTheMiddleAndSignedAtThePoles()
		{
			Assert.That(ScaleTargetsEval.AxisLeanFactor(50, 25), Is.EqualTo(1000));
			Assert.That(ScaleTargetsEval.AxisLeanFactor(100, 25), Is.EqualTo(1250));
			Assert.That(ScaleTargetsEval.AxisLeanFactor(0, 25), Is.EqualTo(750));
			Assert.That(ScaleTargetsEval.AxisLeanFactor(100, -25), Is.EqualTo(750));
			Assert.That(ScaleTargetsEval.AxisLeanFactor(100, 0), Is.EqualTo(1000));
			Assert.That(ScaleTargetsEval.Personality(1250, 1250, 1000), Is.EqualTo(1562));
		}

		[Test]
		public void ThePhysicalCapClampsAndBeatsTheFloor()
		{
			var line = new ScaleLine(25000, 25000, 600, 1400, 500, 500, 5);
			Assert.That(ScaleTargetsEval.Target(line, 5, Tiers, 0, TicksPerMinute, 0, 0, 1, Neutral, 1, 12), Is.EqualTo(12));
			Assert.That(ScaleTargetsEval.Target(line, 5, Tiers, 0, TicksPerMinute, 0, 0, 1, Neutral, 1, 2), Is.EqualTo(2));
			Assert.That(ScaleTargetsEval.Target(line, 5, Tiers, 0, TicksPerMinute, 0, 0, 1, Neutral, 1, -1), Is.EqualTo(25));
		}

		[Test]
		public void TheFloorHoldsWhenEverythingIsZero()
		{
			var line = new ScaleLine(0, 0, 600, 1400, 500, 500, 1);
			Assert.That(ScaleTargetsEval.Target(line, 3, Tiers, 0, TicksPerMinute, 0, 0, 1, Neutral, 1, -1), Is.EqualTo(1));
		}

		[Test]
		public void TheArmyOwnTermScalesTheBaselineAndTheEnemyTermIsInValue()
		{
			var army = new ScaleLine(1000, 1000, 600, 1400, 1000, 1000, 0);

			// Nothing seen: the personality's SquadValue, unchanged at minute 0.
			Assert.That(ScaleTargetsEval.Target(army, 4, Tiers, 0, TicksPerMinute, 0, 0, 1, Neutral, 12000, -1), Is.EqualTo(12000));

			// A 30000 army seen by Hard on a half-dark map: 0.955 x 30000 x 1.5 = 42975 beats the 12000 baseline.
			Assert.That(ScaleTargetsEval.Target(army, 4, Tiers, 0, TicksPerMinute, 30000, 500, 1, Neutral, 12000, -1), Is.EqualTo(42975));
		}

		[Test]
		public void TheLerpHitsBothEndsAndIsMonotonic()
		{
			Assert.That(ScaleTargetsEval.Lerp(1000, 3250, 0, Tiers), Is.EqualTo(1000));
			Assert.That(ScaleTargetsEval.Lerp(1000, 3250, 9, Tiers), Is.EqualTo(3250));
			var previous = -1L;
			for (var t = 0; t < Tiers; t++)
			{
				var v = ScaleTargetsEval.Lerp(1500, 7500, t, Tiers);
				Assert.That(v, Is.GreaterThanOrEqualTo(previous));
				previous = v;
			}
		}

		[Test]
		public void TheLawIsDeterministic()
		{
			var a = Line(Production, 12345, 7, 333, 2, 1250);
			var b = Line(Production, 12345, 7, 333, 2, 1250);
			Assert.That(a, Is.EqualTo(b));
		}
	}
}
