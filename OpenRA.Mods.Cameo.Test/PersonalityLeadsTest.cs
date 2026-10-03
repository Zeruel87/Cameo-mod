#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System.Collections.Generic;
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public sealed class PersonalityLeadsTest
	{
		// §12.14 PL-1: the 1500 ticks/min of a 40ms game (60000 / Timestep).
		const long TicksPerGameMin = 1500;

		sealed class FakeLeadProvider : IBotPersonalityLeadProvider
		{
			public double Value = 1.0;
			public double PersonalityLeadLean(string personality) => Value;
		}

		static BotSituation Situation(string ownPersonality = "steamroller")
		{
			return new BotSituation
			{
				OwnPersonality = ownPersonality,
				Enemies = new Dictionary<OpenRA.Player, EnemyProfile>(),
				Demand = new CounterDemand()
			};
		}

		[Test]
		public void EnemyProductionEstimateIsZeroWithoutAWindow()
		{
			// First snapshot has no delta window: nothing is estimated, even with
			// remembered production buildings — a guess would lean on day one.
			var enemies = new[] { new EnemyProfile { ArmyValueDelta = 300, ProductionBuildings = 2 } };
			Assert.That(MasterAiBotModule.EnemyProductionPerGameMin(enemies, 0, TicksPerGameMin, 200), Is.Zero);
			Assert.That(MasterAiBotModule.EnemyProductionPerGameMin(enemies, -5, TicksPerGameMin, 200), Is.Zero);
		}

		[Test]
		public void EnemyProductionEstimateCountsSeenArmyGrowthOnly()
		{
			var enemies = new[] { new EnemyProfile { ArmyValueDelta = 300, ProductionBuildings = 0 } };
			Assert.That(MasterAiBotModule.EnemyProductionPerGameMin(enemies, 150, TicksPerGameMin, 200),
				Is.EqualTo(3000));

			// Shrinking remembered armies are not negative production.
			var shrinking = new[] { new EnemyProfile { ArmyValueDelta = -900, ProductionBuildings = 0 } };
			Assert.That(MasterAiBotModule.EnemyProductionPerGameMin(shrinking, 150, TicksPerGameMin, 200), Is.Zero);
		}

		[Test]
		public void EnemyProductionEstimateCountsBuildingsOnly()
		{
			var enemies = new[] { new EnemyProfile { ArmyValueDelta = 0, ProductionBuildings = 2 } };
			Assert.That(MasterAiBotModule.EnemyProductionPerGameMin(enemies, 150, TicksPerGameMin, 200),
				Is.EqualTo(400));
		}

		[Test]
		public void EnemyProductionEstimateAggregatesEverySeenEnemy()
		{
			var enemies = new[]
			{
				new EnemyProfile { ArmyValueDelta = 150, ProductionBuildings = 1 },
				new EnemyProfile { ArmyValueDelta = 150, ProductionBuildings = 1 }
			};
			Assert.That(MasterAiBotModule.EnemyProductionPerGameMin(enemies, 150, TicksPerGameMin, 200),
				Is.EqualTo(3000 + 400));
			Assert.That(MasterAiBotModule.EnemyProductionPerGameMin(null, 150, TicksPerGameMin, 200), Is.Zero);
		}

		[Test]
		public void SteamrollerLeadReadsAtTargetWhenNoEnemyOutputIsRemembered()
		{
			// An unseen enemy is not a lead to chase: denominator ~0 reads as
			// at-target (1), never infinite and never a deficit — documented §12.14 choice.
			Assert.That(MasterAiBotModule.SteamrollerLead(0, 0), Is.EqualTo(1.0));
			Assert.That(MasterAiBotModule.SteamrollerLead(5000, 0), Is.EqualTo(1.0));
		}

		[Test]
		public void SteamrollerLeadIsTheOwnOverEnemyRatio()
		{
			Assert.That(MasterAiBotModule.SteamrollerLead(2000, 1000), Is.EqualTo(2.0));
			Assert.That(MasterAiBotModule.SteamrollerLead(500, 1000), Is.EqualTo(0.5));
			Assert.That(MasterAiBotModule.SteamrollerLead(0, 400), Is.EqualTo(0.0));
		}

		[Test]
		public void RushLeadIsZeroUntilTheFirstAttackLaunches()
		{
			// FirstAttackTick <= 0 (the -1 sentinel or tick 0) zeroes the timing score.
			Assert.That(MasterAiBotModule.RushLead(10, 2, -1, 4500, 0), Is.Zero);
			Assert.That(MasterAiBotModule.RushLead(10, 2, 0, 4500, 9999), Is.Zero);
		}

		[Test]
		public void RushLeadIsTheWeakerOfRateAndTiming()
		{
			// On-time first attack, half the target rate -> rate limits.
			Assert.That(MasterAiBotModule.RushLead(1, 2, 2250, 4500, 0), Is.EqualTo(0.5));

			// Target rate met but the first attack came at twice the target tick -> timing limits.
			Assert.That(MasterAiBotModule.RushLead(2, 2, 9000, 4500, 0), Is.EqualTo(0.5));

			// Both met -> at target.
			Assert.That(MasterAiBotModule.RushLead(2, 2, 4500, 4500, 0), Is.EqualTo(1.0));
		}

		[Test]
		public void RushLeadCreditsRememberedEconDamageLightly()
		{
			// A flat quarter point on the attack score: 1.5 launches/min plus any econ
			// kill reads at-target, but econ damage alone (timing 0) still trails.
			Assert.That(MasterAiBotModule.RushLead(1, 2, 2250, 4500, 500), Is.EqualTo(0.75));
			Assert.That(MasterAiBotModule.RushLead(2, 2, 9000, 4500, 500), Is.EqualTo(0.5));
			Assert.That(MasterAiBotModule.RushLead(0, 2, -1, 4500, 5000), Is.Zero);
		}

		[Test]
		public void LeadLeanMultiplierIsLinearInTheDeficitAndCapped()
		{
			Assert.That(MasterAiBotModule.LeadLeanMultiplier(0, 50), Is.EqualTo(0.5));
			Assert.That(MasterAiBotModule.LeadLeanMultiplier(0.5, 50), Is.EqualTo(0.75));
			Assert.That(MasterAiBotModule.LeadLeanMultiplier(1.0, 50), Is.EqualTo(1.0));
			Assert.That(MasterAiBotModule.LeadLeanMultiplier(2.0, 50), Is.EqualTo(1.0));

			// The cap is the cap: a fully-trailing lead at 100% leans to zero, at 0% not at all.
			Assert.That(MasterAiBotModule.LeadLeanMultiplier(0, 100), Is.EqualTo(0.0));
			Assert.That(MasterAiBotModule.LeadLeanMultiplier(0, 0), Is.EqualTo(1.0));
		}

		[Test]
		public void LeadGateReturnsNoLeanWhenOffMismatchedOrUnknown()
		{
			var situation = Situation("rush");
			situation.RushLead = 0;

			// Flag off -> 1: consumers keep their base knobs bit-identically.
			Assert.That(MasterAiBotModule.PersonalityLeadLean(false, false, situation, "rush", 50), Is.EqualTo(1.0));

			// Disabled trait, no snapshot, a different running personality, an unknown
			// lead name — all read as no-lean.
			Assert.That(MasterAiBotModule.PersonalityLeadLean(true, true, situation, "rush", 50), Is.EqualTo(1.0));
			Assert.That(MasterAiBotModule.PersonalityLeadLean(false, true, null, "rush", 50), Is.EqualTo(1.0));
			Assert.That(MasterAiBotModule.PersonalityLeadLean(false, true, situation, "steamroller", 50), Is.EqualTo(1.0));
			Assert.That(MasterAiBotModule.PersonalityLeadLean(false, true, situation, "turtle", 50), Is.EqualTo(1.0));
			Assert.That(MasterAiBotModule.PersonalityLeadLean(false, true, situation, null, 50), Is.EqualTo(1.0));
		}

		[Test]
		public void LeadGateLeansTheMatchingTrailingPersonality()
		{
			var steamroller = Situation("steamroller");
			steamroller.SteamrollerLead = 0.4;
			Assert.That(MasterAiBotModule.PersonalityLeadLean(false, true, steamroller, "steamroller", 50),
				Is.EqualTo(0.7).Within(1e-9));

			var rush = Situation("rush");
			rush.RushLead = 0;
			Assert.That(MasterAiBotModule.PersonalityLeadLean(false, true, rush, "rush", 50), Is.EqualTo(0.5));
		}

		[Test]
		public void ConsumerHelpersKeepUnleanedKnobsUntouched()
		{
			Assert.That(BotPersonalityLeads.Lean(null, "rush"), Is.EqualTo(1.0));
			Assert.That(BotPersonalityLeads.Scaled(2000, 1.0), Is.EqualTo(2000));
			Assert.That(BotPersonalityLeads.Scaled(0, 0.5), Is.EqualTo(0));
			Assert.That(BotPersonalityLeads.Scaled(2000, 0.75), Is.EqualTo(1500));

			var neutral = new FakeLeadProvider();
			Assert.That(BotPersonalityLeads.Lean(new[] { neutral }, "rush"), Is.EqualTo(1.0));

			var leaning = new FakeLeadProvider { Value = 0.6 };
			Assert.That(BotPersonalityLeads.Lean(new[] { neutral, leaning }, "rush"), Is.EqualTo(0.6));
			Assert.That(BotPersonalityLeads.Scaled(1000, BotPersonalityLeads.Lean(new[] { leaning }, "rush")),
				Is.EqualTo(600));
		}

		[Test]
		public void InfoDefaultsKeepTheSwitchOffAndTheKnobsDocumented()
		{
			var info = new MasterAiBotModuleInfo();
			Assert.That(info.UsePersonalityLeads, Is.False);
			Assert.That(info.PersonalityLeadEnemyProductionPerBuildingPerMin, Is.EqualTo(200));
			Assert.That(info.PersonalityLeadRushAttacksPerGameMinTarget, Is.EqualTo(2));
			Assert.That(info.PersonalityLeadRushFirstAttackTargetTick, Is.EqualTo(4500));
			Assert.That(info.PersonalityLeadMaxLeanPercent, Is.EqualTo(50));
		}
	}
}
