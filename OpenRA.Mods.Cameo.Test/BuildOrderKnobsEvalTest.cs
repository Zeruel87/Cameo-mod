#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	// AI_ARCHITECTURE 12.25: the pure build-order knob math, the opening, the react rules and the learned file.
	[TestFixture]
	public class BuildOrderKnobsEvalTest
	{
		const int TicksPerMinute = 1500;

		static readonly BuildOrderReactThresholds Thresholds = new(600, 9000, 800, 1500, 40, 130, 6);

		static readonly Dictionary<string, Dictionary<string, int>> ReactTargets = new()
		{
			["air"] = new() { ["defence"] = 1300 },
			["rush"] = new() { ["defence"] = 1300, ["production"] = 1250, ["greed"] = 800 },
			["turtle"] = new() { ["tech"] = 1250, ["defence"] = 800 },
			["out_earned"] = new() { ["greed"] = 1300, ["expansion"] = 1300 }
		};

		[Test]
		public void EnemyEconomyIsTheMeanOverScoutedEnemiesNotTheSum()
		{
			Assert.That(BuildOrderKnobsEval.EnemyEconomyPerEnemy(new[] { 10 }), Is.EqualTo(10), "1v1 unchanged");
			Assert.That(BuildOrderKnobsEval.EnemyEconomyPerEnemy(new[] { 10, 10 }), Is.EqualTo(10), "two equal enemies == one");
			Assert.That(BuildOrderKnobsEval.EnemyEconomyPerEnemy(new[] { 10, 0, 10, 0 }), Is.EqualTo(10), "unscouted ignored");
			Assert.That(BuildOrderKnobsEval.EnemyEconomyPerEnemy(new[] { 0, 0 }), Is.EqualTo(0), "all unscouted");
			Assert.That(BuildOrderKnobsEval.EnemyEconomyPerEnemy(new int[0]), Is.EqualTo(0));
			Assert.That(BuildOrderKnobsEval.EnemyEconomyPerEnemy(new[] { 5, 6 }), Is.EqualTo(6), "5.5 rounds half up");
			Assert.That(BuildOrderKnobsEval.EnemyEconomyPerEnemy(new[] { 5, 5, 6 }), Is.EqualTo(5), "5.33 rounds down");
		}

		[Test]
		public void JitterSpansPlusMinusPercentAndIsNeutralAtTheMiddleDraw()
		{
			Assert.That(BuildOrderKnobsEval.JitterMilli(8, 1000), Is.EqualTo(1000));
			Assert.That(BuildOrderKnobsEval.JitterMilli(8, 0), Is.EqualTo(920));
			Assert.That(BuildOrderKnobsEval.JitterMilli(8, 2000), Is.EqualTo(1080));
			Assert.That(BuildOrderKnobsEval.JitterMilli(0, 0), Is.EqualTo(1000));
			Assert.That(BuildOrderKnobsEval.JitterMilli(8, 99999), Is.EqualTo(1080), "a stray draw is clamped, never extrapolated");
		}

		[Test]
		public void CombineMultipliesPresetLearnedJitterAndClamps()
		{
			Assert.That(BuildOrderKnobsEval.Combine(1000, 1000, 1000, 600, 1600), Is.EqualTo(1000));
			Assert.That(BuildOrderKnobsEval.Combine(1250, 1100, 1000, 600, 1600), Is.EqualTo(1375));
			Assert.That(BuildOrderKnobsEval.Combine(1250, 1000, 920, 600, 1600), Is.EqualTo(1150));
			Assert.That(BuildOrderKnobsEval.Combine(1500, 1500, 1080, 600, 1600), Is.EqualTo(1600), "clamped to KnobMax");
			Assert.That(BuildOrderKnobsEval.Combine(700, 700, 920, 600, 1600), Is.EqualTo(600), "clamped to KnobMin");
		}

		[Test]
		public void DecayMovesTowardNeutralFromBothSidesAndNeverPastIt()
		{
			// 150 thousandths per game minute: one minute takes 1300 to 1150, two minutes to 1000, ten minutes stay at 1000.
			Assert.That(BuildOrderKnobsEval.Decay(1300, 150, TicksPerMinute, TicksPerMinute), Is.EqualTo(1150));
			Assert.That(BuildOrderKnobsEval.Decay(1300, 150, TicksPerMinute * 2, TicksPerMinute), Is.EqualTo(1000));
			Assert.That(BuildOrderKnobsEval.Decay(1300, 150, TicksPerMinute * 10, TicksPerMinute), Is.EqualTo(1000));
			Assert.That(BuildOrderKnobsEval.Decay(800, 150, TicksPerMinute, TicksPerMinute), Is.EqualTo(950));
			Assert.That(BuildOrderKnobsEval.Decay(1000, 150, TicksPerMinute, TicksPerMinute), Is.EqualTo(1000));
			Assert.That(BuildOrderKnobsEval.Decay(1300, 150, 0, TicksPerMinute), Is.EqualTo(1300));
		}

		[Test]
		public void ReactStepApproachesTheTargetInBoundedStepsThenDecays()
		{
			var factor = 1000;
			for (var i = 0; i < 20; i++)
				factor = BuildOrderKnobsEval.ReactStep(factor, 1300, 100, 150, 125, TicksPerMinute, 700, 1500);
			Assert.That(factor, Is.EqualTo(1300), "reaches the target and stops there");

			factor = BuildOrderKnobsEval.ReactStep(1000, 1300, 100, 150, 125, TicksPerMinute, 700, 1500);
			Assert.That(factor, Is.EqualTo(1100), "one step is at most ReactStep");

			// A target beyond the bound is cut at the bound.
			for (var i = 0; i < 20; i++)
				factor = BuildOrderKnobsEval.ReactStep(factor, 3000, 100, 150, 125, TicksPerMinute, 700, 1500);
			Assert.That(factor, Is.EqualTo(1500));

			// No reaction (target 1000): decays at 150 per minute, 125 ticks at a time.
			for (var i = 0; i < 45; i++)
				factor = BuildOrderKnobsEval.ReactStep(factor, 1000, 100, 150, 125, TicksPerMinute, 700, 1500);
			Assert.That(factor, Is.EqualTo(1000), "decays all the way back to the base");
		}

		[Test]
		public void CombinedTargetMultipliesTheActiveReactionsOnOneKnob()
		{
			Assert.That(BuildOrderKnobsEval.CombinedTarget("defence", BuildOrderReaction.None, ReactTargets), Is.EqualTo(1000));
			Assert.That(BuildOrderKnobsEval.CombinedTarget("defence", BuildOrderReaction.Air, ReactTargets), Is.EqualTo(1300));
			Assert.That(BuildOrderKnobsEval.CombinedTarget("defence", BuildOrderReaction.Air | BuildOrderReaction.Rush, ReactTargets), Is.EqualTo(1690));
			Assert.That(BuildOrderKnobsEval.CombinedTarget("defence", BuildOrderReaction.Air | BuildOrderReaction.Turtle, ReactTargets), Is.EqualTo(1040));
			Assert.That(BuildOrderKnobsEval.CombinedTarget("support", BuildOrderReaction.Air | BuildOrderReaction.Rush, ReactTargets), Is.EqualTo(1000));
		}

		[Test]
		public void EnemyAirSeenTriggersAirOnly()
		{
			var calm = new BuildOrderReactInputs(3000, 0, 0, 0, 2000, 4, 4);
			Assert.That(BuildOrderKnobsEval.Evaluate(calm, Thresholds), Is.EqualTo(BuildOrderReaction.None));

			var air = new BuildOrderReactInputs(3000, 600, 0, 0, 2000, 4, 4);
			Assert.That(BuildOrderKnobsEval.Evaluate(air, Thresholds), Is.EqualTo(BuildOrderReaction.Air));
		}

		[Test]
		public void EarlyArmyNearTheBaseIsARushOnlyInsideTheWindow()
		{
			var early = new BuildOrderReactInputs(4000, 0, 800, 0, 2000, 4, 4);
			Assert.That(BuildOrderKnobsEval.Evaluate(early, Thresholds), Is.EqualTo(BuildOrderReaction.Rush));

			var late = new BuildOrderReactInputs(12000, 0, 5000, 0, 2000, 4, 4);
			Assert.That(BuildOrderKnobsEval.Evaluate(late, Thresholds), Is.EqualTo(BuildOrderReaction.None), "a late attack is not an opening rush");

			var small = new BuildOrderReactInputs(4000, 0, 799, 0, 2000, 4, 4);
			Assert.That(BuildOrderKnobsEval.Evaluate(small, Thresholds), Is.EqualTo(BuildOrderReaction.None));
		}

		[Test]
		public void DefenceHeavyEnemyNeedsBothTheValueAndTheShare()
		{
			Assert.That(BuildOrderKnobsEval.Evaluate(new BuildOrderReactInputs(5000, 0, 0, 2000, 2000, 4, 4), Thresholds), Is.EqualTo(BuildOrderReaction.Turtle));
			Assert.That(BuildOrderKnobsEval.Evaluate(new BuildOrderReactInputs(5000, 0, 0, 1000, 100, 4, 4), Thresholds), Is.EqualTo(BuildOrderReaction.None), "below the value floor");
			Assert.That(BuildOrderKnobsEval.Evaluate(new BuildOrderReactInputs(5000, 0, 0, 1600, 9000, 4, 4), Thresholds), Is.EqualTo(BuildOrderReaction.None), "a small share of a big army is not a turtle");
		}

		[Test]
		public void OutEarnedNeedsTheMarginAndTheMinimum()
		{
			Assert.That(BuildOrderKnobsEval.Evaluate(new BuildOrderReactInputs(5000, 0, 0, 0, 0, 14, 10), Thresholds), Is.EqualTo(BuildOrderReaction.OutEarned));
			Assert.That(BuildOrderKnobsEval.Evaluate(new BuildOrderReactInputs(5000, 0, 0, 0, 0, 13, 10), Thresholds), Is.EqualTo(BuildOrderReaction.None), "exactly 130% is not more");
			Assert.That(BuildOrderKnobsEval.Evaluate(new BuildOrderReactInputs(5000, 0, 0, 0, 0, 5, 1), Thresholds), Is.EqualTo(BuildOrderReaction.None), "below the minimum proxy");
		}

		[Test]
		public void SeveralReactionsCanHoldAtOnce()
		{
			var all = new BuildOrderReactInputs(4000, 900, 900, 2000, 2000, 20, 4);
			Assert.That(BuildOrderKnobsEval.Evaluate(all, Thresholds),
				Is.EqualTo(BuildOrderReaction.Air | BuildOrderReaction.Rush | BuildOrderReaction.Turtle | BuildOrderReaction.OutEarned));
		}

		[Test]
		public void OpeningAdvancesOnTheWantedCategoryOnly()
		{
			var opening = new BuildOrderOpening("eco", new[] { "power", "refinery", "production" }, 7500, 1500);
			Assert.That(opening.Wanted, Is.EqualTo("power"));

			opening.NotifyQueued("refinery", 10);
			Assert.That(opening.Wanted, Is.EqualTo("power"), "an out-of-order building does not advance it");

			opening.NotifyQueued("power", 20);
			Assert.That(opening.Wanted, Is.EqualTo("refinery"));

			opening.NotifyQueued("refinery", 30);
			Assert.That(opening.Wanted, Is.EqualTo("production"));

			opening.NotifyQueued("barracks", 40);
			Assert.That(opening.Active, Is.False, "the generic production step takes a barracks");
			Assert.That(opening.EndReason, Is.EqualTo("completed"));
			Assert.That(opening.Wanted, Is.Null);
		}

		[Test]
		public void ExactStepsDoNotAcceptASiblingCategory()
		{
			var opening = new BuildOrderOpening("b", new[] { "barracks" }, 7500, 1500);
			opening.NotifyQueued("factory", 5);
			Assert.That(opening.Wanted, Is.EqualTo("barracks"));
		}

		[Test]
		public void AStuckStepIsSkippedAndTheOpeningTimesOut()
		{
			var opening = new BuildOrderOpening("t", new[] { "tech", "tech", "production" }, 7500, 1500);
			opening.Update(1499);
			Assert.That(opening.StepIndex, Is.EqualTo(0));

			opening.Update(1500);
			Assert.That(opening.StepIndex, Is.EqualTo(1), "a step not met in 1500 ticks is skipped");

			opening.Update(3000);
			Assert.That(opening.StepIndex, Is.EqualTo(2));
			opening.Update(4500);
			Assert.That(opening.EndReason, Is.EqualTo("completed"), "the last step timed out too");

			var late = new BuildOrderOpening("t", new[] { "tech", "tech", "tech", "tech", "tech", "tech" }, 7500, 1500);
			late.Update(7500);
			Assert.That(late.EndReason, Is.EqualTo("timeout"));
		}

		[Test]
		public void TheReactLayerCanInvalidateAnOpeningAndANoteAfterwardsIsIgnored()
		{
			var opening = new BuildOrderOpening("eco", new[] { "power", "refinery" }, 7500, 1500);
			opening.Invalidate("react_rush");
			Assert.That(opening.Active, Is.False);
			Assert.That(opening.EndReason, Is.EqualTo("react_rush"));
			opening.NotifyQueued("power", 1);
			Assert.That(opening.EndReason, Is.EqualTo("react_rush"));
			Assert.That(opening.Wanted, Is.Null);
		}

		[Test]
		public void AnEmptyOpeningIsNeverActive()
		{
			Assert.That(new BuildOrderOpening("x", Array.Empty<string>(), 7500, 1500).Active, Is.False);
		}

		[Test]
		public void CategorySatisfactionAndKnobMapping()
		{
			Assert.That(BuildOrderCategory.Satisfies("production", "barracks"), Is.True);
			Assert.That(BuildOrderCategory.Satisfies("production", "factory"), Is.True);
			Assert.That(BuildOrderCategory.Satisfies("barracks", "production"), Is.False);
			Assert.That(BuildOrderCategory.Satisfies("tech", "tech"), Is.True);
			Assert.That(BuildOrderCategory.Satisfies(null, "tech"), Is.False);

			Assert.That(BuildOrderCategory.KnobFor("barracks"), Is.EqualTo("production"));
			Assert.That(BuildOrderCategory.KnobFor("superweapon"), Is.EqualTo("tech"));
			Assert.That(BuildOrderCategory.KnobFor("defence"), Is.EqualTo("defence"));
			Assert.That(BuildOrderCategory.KnobFor("support"), Is.EqualTo("support"));
			Assert.That(BuildOrderCategory.KnobFor("refinery"), Is.EqualTo("greed"));
			Assert.That(BuildOrderCategory.KnobFor("power"), Is.Null);
			Assert.That(BuildOrderCategory.KnobFor("other"), Is.Null);
		}

		[Test]
		public void ScaleIsIdentityAtNeutralAndRoundsDown()
		{
			Assert.That(BotBuildOrderKnobs.Scale(150, 1000), Is.EqualTo(150));
			Assert.That(BotBuildOrderKnobs.Scale(150, 1150), Is.EqualTo(172));
			Assert.That(BotBuildOrderKnobs.Scale(int.MaxValue, 1600), Is.EqualTo(int.MaxValue), "saturates instead of overflowing");
		}

		[Test]
		public void FamilyIsTheFactionPrefix()
		{
			Assert.That(BuildOrderKnobsEval.FamilyOf("ra1_allies"), Is.EqualTo("ra1"));
			Assert.That(BuildOrderKnobsEval.FamilyOf("td_gdi"), Is.EqualTo("td"));
			Assert.That(BuildOrderKnobsEval.FamilyOf("solo"), Is.EqualTo("solo"));
			Assert.That(BuildOrderKnobsEval.FamilyOf(null), Is.EqualTo(""));
		}

		static Func<double> Sequence(params double[] values)
		{
			var i = 0;
			return () => values[i++ % values.Length];
		}

		[Test]
		public void BetaSampleIsInsideTheUnitIntervalAndReproducible()
		{
			var a = BuildOrderKnobsEval.SampleBeta(5, 3, Sequence(0.1, 0.9, 0.5, 0.3, 0.7, 0.2, 0.6, 0.4));
			var b = BuildOrderKnobsEval.SampleBeta(5, 3, Sequence(0.1, 0.9, 0.5, 0.3, 0.7, 0.2, 0.6, 0.4));
			Assert.That(a, Is.EqualTo(b));
			Assert.That(a, Is.InRange(0.0, 1.0));
		}

		[Test]
		public void BetaSampleMeanFollowsAlphaOverAlphaPlusBeta()
		{
			var random = new Random(12345);
			double sum = 0;
			const int N = 4000;
			for (var i = 0; i < N; i++)
				sum += BuildOrderKnobsEval.SampleBeta(8, 2, random.NextDouble);

			Assert.That(sum / N, Is.EqualTo(0.8).Within(0.02));
		}

		[Test]
		public void OpeningChoiceIsDeterministicSkipsZeroWeightAndFollowsEvidence()
		{
			var weights = new Dictionary<string, int> { ["eco"] = 2, ["barracks_first"] = 5, ["defence_first"] = 0 };

			string Pick(int seed, Func<string, (int, int)> posterior) =>
				BuildOrderKnobsEval.ChooseOpening(weights, posterior, new Random(seed).NextDouble);

			Assert.That(Pick(7, _ => (1, 1)), Is.EqualTo(Pick(7, _ => (1, 1))), "same draws, same opening");

			for (var seed = 0; seed < 200; seed++)
				Assert.That(Pick(seed, _ => (1, 1)), Is.Not.EqualTo("defence_first"), "zero weight is never chosen");

			// Strong evidence that eco wins and barracks_first loses outweighs the preset tilt.
			var eco = 0;
			for (var seed = 0; seed < 200; seed++)
				if (Pick(seed, n => n == "eco" ? (40, 2) : (2, 40)) == "eco")
					eco++;
			Assert.That(eco, Is.GreaterThan(190));

			// With no evidence the heavier weight is picked more often.
			var barracks = 0;
			for (var seed = 0; seed < 400; seed++)
				if (Pick(seed, _ => (1, 1)) == "barracks_first")
					barracks++;
			Assert.That(barracks, Is.GreaterThan(200));
		}

		const string Learned =
			"BotBuildOrderKnobs:\n" +
			"\tKnobs@any__any:\n\t\ttempo: 1010\n\t\tgreed: 1020\n" +
			"\tKnobs@rush__any:\n\t\ttempo: 1100\n" +
			"\tKnobs@rush__family_ra1:\n\t\ttempo: 1200\n\t\tdefence: 900\n" +
			"\tKnobs@rush__ra1_allies:\n\t\ttempo: 1300\n" +
			"\tOpenings@rush__ra1_allies__vs__ra1_soviets:\n\t\teco: 7 3\n\t\tbarracks_first: 2 9\n";

		static BuildOrderLearned Load(string yaml) => BuildOrderLearned.Parse(MiniYaml.FromString(yaml, "learned"));

		[Test]
		public void LearnedFallsBackFactionThenFamilyThenAnyThenGlobalThenNeutral()
		{
			var learned = Load(Learned);
			Assert.That(learned.ScopeCount, Is.EqualTo(4));
			Assert.That(learned.Multiplier("rush", "ra1_allies", "tempo"), Is.EqualTo(1300));
			Assert.That(learned.Multiplier("rush", "ra1_soviets", "tempo"), Is.EqualTo(1200), "family");
			Assert.That(learned.Multiplier("rush", "ra1_soviets", "defence"), Is.EqualTo(900), "family, other knob");
			Assert.That(learned.Multiplier("rush", "td_gdi", "tempo"), Is.EqualTo(1100), "personality any");
			Assert.That(learned.Multiplier("turtle", "td_gdi", "tempo"), Is.EqualTo(1010), "global");
			Assert.That(learned.Multiplier("rush", "td_gdi", "greed"), Is.EqualTo(1020), "global for a knob only the global scope has");
			Assert.That(learned.Multiplier("turtle", "td_gdi", "support"), Is.EqualTo(1000), "missing = neutral");
		}

		[Test]
		public void LearnedPosteriorsAreKeyedByMatchupAndDefaultToOneOne()
		{
			var learned = Load(Learned);
			Assert.That(learned.OpeningScopeCount, Is.EqualTo(1));
			Assert.That(learned.Posterior("rush", "ra1_allies", "ra1_soviets", "eco"), Is.EqualTo((7, 3)));
			Assert.That(learned.Posterior("rush", "ra1_allies", "ra1_soviets", "barracks_first"), Is.EqualTo((2, 9)));
			Assert.That(learned.Posterior("rush", "ra1_allies", "td_nod", "eco"), Is.EqualTo((1, 1)));
			Assert.That(learned.Posterior("rush", "ra1_allies", "ra1_soviets", "fast_tech"), Is.EqualTo((1, 1)));
		}

		[Test]
		public void AnEmptyOrForeignLearnedFileIsNeutral()
		{
			var empty = Load("BotBuildOrderKnobs:\n");
			Assert.That(empty.ScopeCount, Is.EqualTo(0));
			Assert.That(empty.Multiplier("rush", "td_gdi", "tempo"), Is.EqualTo(1000));
			Assert.That(Load("Other:\n\tA: 1\n").ScopeCount, Is.EqualTo(0));
		}
	}
}
