#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System.Text;
using System.Text.Json;
using NUnit.Framework;
using OpenRA;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Mods.Cameo.Traits.BotModules;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public sealed class BotUtilityAxesTest
	{
		sealed class StubUtilityAxes : IBotUtilityAxes
		{
			readonly int turtleRush;
			readonly int steamrollerGuerrilla;
			public StubUtilityAxes(int turtleRush, int steamrollerGuerrilla = IBotUtilityAxes.Neutral)
			{
				this.turtleRush = turtleRush;
				this.steamrollerGuerrilla = steamrollerGuerrilla;
			}

			public int UtilityTurtleRush => turtleRush;
			public int UtilityTechRushExpansion => IBotUtilityAxes.Neutral;
			public int UtilitySteamrollerGuerrilla => steamrollerGuerrilla;
		}

		sealed class DisabledStubUtilityAxes : IBotUtilityAxes, IDisabledTrait
		{
			public int UtilityTurtleRush => 100;
			public int UtilityTechRushExpansion => 100;
			public int UtilitySteamrollerGuerrilla => 100;
			public bool IsTraitDisabled => true;
		}

		static UtilityAxisSample Quiet() => new();

		static UtilityAxisSample Winning() => new()
		{
			EnemyArmyValue = 5000,
			CombatRatioDefendedPct = 400
		};

		static UtilityAxisSample Pressured() => new()
		{
			EnemyArmyValue = 5000,
			EnemyPressureValue = 4500,
			OwnDeathsCostWindow = 600,
			EnemyDefenceValue = 4000
		};

		static BotUtilityAxes ObservedAxes(MasterAiBotModuleInfo info, string personality,
			UtilityAxisSample sample, int snapshots)
		{
			var axes = new BotUtilityAxes();
			for (var i = 0; i < snapshots; i++)
				axes.Observe(sample, personality, info);
			return axes;
		}

		[Test]
		public void MissingPersonalityRestsAtNeutral()
		{
			// No rest configured for the personality (or none at all) — every axis
			// parks at the 50 neutral point and stays there while inputs are quiet.
			var info = new MasterAiBotModuleInfo();
			var axes = ObservedAxes(info, "nosuch", Quiet(), 50);
			Assert.That(axes.TurtleRush, Is.EqualTo(50));
			Assert.That(axes.TechRushExpansion, Is.EqualTo(50));
			Assert.That(axes.SteamrollerGuerrilla, Is.EqualTo(50));
			Assert.That(ObservedAxes(info, "", Quiet(), 50).TurtleRush, Is.EqualTo(50));
			Assert.That(BotUtilityAxes.Rest(info.UtilityTurtleRushRest, "nosuch"), Is.EqualTo(50));
			Assert.That(BotUtilityAxes.Rest(info.UtilityTurtleRushRest, ""), Is.EqualTo(50));
			Assert.That(BotUtilityAxes.Rest(null, "rush"), Is.EqualTo(50));
		}

		[Test]
		public void FirstObservationParksAxesOnThePersonalityRest()
		{
			// §5.1: a personality is a starting point on the axes — the first
			// snapshot reads its rest before inputs move anything.
			var info = new MasterAiBotModuleInfo();
			info.UtilityTurtleRushRest["rush"] = 80;
			info.UtilitySteamrollerGuerrillaRest["rush"] = 45;
			var axes = ObservedAxes(info, "rush", Quiet(), 1);
			Assert.That(axes.TurtleRush, Is.EqualTo(80));
			Assert.That(axes.TechRushExpansion, Is.EqualTo(50));
			Assert.That(axes.SteamrollerGuerrilla, Is.EqualTo(45));
		}

		[Test]
		public void AxisMovesOffRestUnderInputs()
		{
			var info = new MasterAiBotModuleInfo();
			var axes = ObservedAxes(info, "rush", Winning(), 1);
			Assert.That(axes.TurtleRush, Is.GreaterThan(50));

			// Predicted-win 400: target = 50 + 25*Saturate(300,300)/100 = 62 —
			// the EMA converges on it and never overshoots.
			Assert.That(ObservedAxes(info, "rush", Winning(), 50).TurtleRush, Is.EqualTo(62));
		}

		[Test]
		public void PressureLossesAndEnemyDefencesPullTowardTurtle()
		{
			var info = new MasterAiBotModuleInfo();
			var axes = ObservedAxes(info, "turtle", Pressured(), 200);
			Assert.That(axes.TurtleRush, Is.LessThan(50));

			// And the same pressure pulls TechRushExpansion toward the TechRush pole.
			Assert.That(axes.TechRushExpansion, Is.LessThan(50));
		}

		[Test]
		public void AxisDecaysBackTowardRestWhenInputsGoQuiet()
		{
			var info = new MasterAiBotModuleInfo();
			var axes = new BotUtilityAxes();
			for (var i = 0; i < 50; i++)
				axes.Observe(Pressured(), "rush", info);
			var pressured = axes.TurtleRush;
			Assert.That(pressured, Is.LessThan(50));

			var previous = pressured;
			var steps = 0;
			while (axes.TurtleRush != 50 && steps < 2000)
			{
				axes.Observe(Quiet(), "rush", info);
				Assert.That(axes.TurtleRush, Is.GreaterThanOrEqualTo(previous));
				previous = axes.TurtleRush;
				steps++;
			}

			Assert.That(axes.TurtleRush, Is.EqualTo(50));
			Assert.That(steps, Is.GreaterThan(0));
		}

		[Test]
		public void AxesStayBoundedUnderExtremeInputs()
		{
			var info = new MasterAiBotModuleInfo();
			var extreme = new UtilityAxisSample
			{
				CombatRatioDefendedPct = int.MaxValue,
				EnemyArmyValue = int.MaxValue,
				EnemyPressureValue = int.MaxValue,
				EnemyDefenceValue = int.MaxValue,
				EnemyExpansionClusters = int.MaxValue,
				EnemyStealthShare = 100,
				OwnEconomy = 0,
				OwnExpansionClusters = 0,
				OwnDeathsCostWindow = int.MaxValue,
				OwnKillsCostWindow = 0
			};
			var axes = ObservedAxes(info, "rush", extreme, 500);
			Assert.That(axes.TurtleRush, Is.InRange(0, 100));
			Assert.That(axes.TechRushExpansion, Is.InRange(0, 100));
			Assert.That(axes.SteamrollerGuerrilla, Is.InRange(0, 100));
		}

		[Test]
		public void LosingTheExchangePushesGuerrillaWinningPushesSteamroller()
		{
			var info = new MasterAiBotModuleInfo();
			var losing = ObservedAxes(info, "guerrilla",
				new UtilityAxisSample { OwnDeathsCostWindow = 900, OwnKillsCostWindow = 100 }, 200);
			Assert.That(losing.SteamrollerGuerrilla, Is.GreaterThan(50));

			var winning = ObservedAxes(info, "steamroller",
				new UtilityAxisSample { OwnDeathsCostWindow = 100, OwnKillsCostWindow = 900 }, 200);
			Assert.That(winning.SteamrollerGuerrilla, Is.LessThan(50));
		}

		[Test]
		public void EnemySprawlPushesExpansionAndGuerrilla()
		{
			var info = new MasterAiBotModuleInfo();
			var axes = ObservedAxes(info, "expansion",
				new UtilityAxisSample { EnemyExpansionClusters = 5 }, 200);
			Assert.That(axes.TechRushExpansion, Is.GreaterThan(50));
			Assert.That(axes.SteamrollerGuerrilla, Is.GreaterThan(50));
		}

		[Test]
		public void PersonalitySwitchMovesTheRestNotTheAxis()
		{
			var info = new MasterAiBotModuleInfo();
			info.UtilityTurtleRushRest["rush"] = 80;
			info.UtilityTurtleRushRest["turtle"] = 20;
			var axes = ObservedAxes(info, "rush", Quiet(), 10);
			Assert.That(axes.TurtleRush, Is.EqualTo(80));

			// Quiet inputs under the new rest: the axis glides toward it.
			var first = axes.TurtleRush;
			axes.Observe(Quiet(), "turtle", info);
			Assert.That(axes.TurtleRush, Is.LessThan(first));
		}

		[Test]
		public void YamlKnobsLoadAndZeroWeightPinsAxesAtRest()
		{
			// CLAUDE.md 8b: the engine drops unknown fields silently — load the real
			// knobs through FieldLoader so the yaml names are proven, not assumed.
			var info = FieldLoader.Load<MasterAiBotModuleInfo>(new MiniYaml("",
				MiniYaml.FromString(
					"UtilityTurtleRushRest:\n" +
					"\trush: 80\n" +
					"UtilityInputWeightPercent: 0\n" +
					"UtilityAxisDecayPercent: 100\n",
					"test")));
			Assert.That(info.UtilityTurtleRushRest["rush"], Is.EqualTo(80));
			Assert.That(info.UtilityInputWeightPercent, Is.EqualTo(0));
			Assert.That(info.UtilityAxisDecayPercent, Is.EqualTo(100));

			// Weight 0 = pure personality: maximal inputs cannot move the axis.
			Assert.That(ObservedAxes(info, "rush", Pressured(), 10).TurtleRush, Is.EqualTo(80));

			// Decay 100 tracks the target instantly.
			var snap = FieldLoader.Load<MasterAiBotModuleInfo>(new MiniYaml("",
				MiniYaml.FromString("UtilityAxisDecayPercent: 100\n", "test")));
			Assert.That(ObservedAxes(snap, "rush", Winning(), 1).TurtleRush, Is.EqualTo(62));
		}

		[Test]
		public void RestOutsideRangeFailsValidation()
		{
			var info = new MasterAiBotModuleInfo();
			info.UtilityTurtleRushRest["rush"] = 150;
			Assert.Throws<YamlException>(() => info.RulesetLoaded(null, null));
		}

		[Test]
		public void UtilityAttackDelayPercentIsPiecewiseLinearAndClamped()
		{
			Assert.That(SquadManagerBotModuleCA.UtilityAttackDelayPercent(0), Is.EqualTo(150));
			Assert.That(SquadManagerBotModuleCA.UtilityAttackDelayPercent(50), Is.EqualTo(100));
			Assert.That(SquadManagerBotModuleCA.UtilityAttackDelayPercent(100), Is.EqualTo(60));
			Assert.That(SquadManagerBotModuleCA.UtilityAttackDelayPercent(25), Is.EqualTo(125));
			Assert.That(SquadManagerBotModuleCA.UtilityAttackDelayPercent(75), Is.EqualTo(80));
			Assert.That(SquadManagerBotModuleCA.UtilityAttackDelayPercent(-20), Is.EqualTo(150));
			Assert.That(SquadManagerBotModuleCA.UtilityAttackDelayPercent(200), Is.EqualTo(60));
		}

		[Test]
		public void ConsumerFlagOffIsByteIdentical()
		{
			// Default flag (UseUtilityAxes = false): the reset is the yaml value
			// verbatim — even when an enabled provider advertises a hard Rush pole.
			var info = FieldLoader.Load<SquadManagerBotModuleCAInfo>(new MiniYaml("",
				MiniYaml.FromString("MinimumAttackForceDelay: 400\n", "test")));
			Assert.That(info.UseUtilityAxes, Is.False);
			var providers = new IBotUtilityAxes[] { new StubUtilityAxes(100) };
			Assert.That(SquadManagerBotModuleCA.MinAttackDelayResetTicks(info, providers),
				Is.EqualTo(info.MinimumAttackForceDelay));
			Assert.That(SquadManagerBotModuleCA.MinAttackDelayResetTicks(info, providers), Is.EqualTo(400));
		}

		[Test]
		public void ProviderlessConsumerReadsNeutral()
		{
			var armed = FieldLoader.Load<SquadManagerBotModuleCAInfo>(new MiniYaml("",
				MiniYaml.FromString("UseUtilityAxes: true\nMinimumAttackForceDelay: 400\n", "test")));
			Assert.That(armed.UseUtilityAxes, Is.True);

			// No provider at all, and a disabled-only provider, both read neutral -> x1.0.
			Assert.That(SquadManagerBotModuleCA.MinAttackDelayResetTicks(armed, null), Is.EqualTo(400));
			Assert.That(SquadManagerBotModuleCA.MinAttackDelayResetTicks(armed,
				new IBotUtilityAxes[] { new DisabledStubUtilityAxes() }), Is.EqualTo(400));
		}

		[Test]
		public void ArmedConsumerScalesByTurtleRush()
		{
			var armed = FieldLoader.Load<SquadManagerBotModuleCAInfo>(new MiniYaml("",
				MiniYaml.FromString("UseUtilityAxes: true\nMinimumAttackForceDelay: 400\n", "test")));

			Assert.That(SquadManagerBotModuleCA.MinAttackDelayResetTicks(armed,
				new IBotUtilityAxes[] { new StubUtilityAxes(100) }), Is.EqualTo(240));
			Assert.That(SquadManagerBotModuleCA.MinAttackDelayResetTicks(armed,
				new IBotUtilityAxes[] { new StubUtilityAxes(0) }), Is.EqualTo(600));
			Assert.That(SquadManagerBotModuleCA.MinAttackDelayResetTicks(armed,
				new IBotUtilityAxes[] { new StubUtilityAxes(50) }), Is.EqualTo(400));
		}

		[Test]
		public void GuerrillaCapScalesBySteamrollerGuerrilla()
		{
			var yaml = "MaxGuerrillaSquads: 2\n";
			var off = FieldLoader.Load<SquadManagerBotModuleCAInfo>(new MiniYaml("", MiniYaml.FromString(yaml, "test")));
			var armed = FieldLoader.Load<SquadManagerBotModuleCAInfo>(new MiniYaml("",
				MiniYaml.FromString("UseUtilityAxes: true\n" + yaml, "test")));
			var providers = new IBotUtilityAxes[] { new StubUtilityAxes(50, 100) };

			Assert.That(SquadManagerBotModuleCA.GuerrillaSquadCap(off, 0, providers), Is.EqualTo(2));
			Assert.That(SquadManagerBotModuleCA.GuerrillaSquadCap(armed, 0, null), Is.EqualTo(2));
			Assert.That(SquadManagerBotModuleCA.GuerrillaSquadCap(armed, 0, providers), Is.EqualTo(3));
			Assert.That(SquadManagerBotModuleCA.GuerrillaSquadCap(armed, 0,
				new IBotUtilityAxes[] { new StubUtilityAxes(50, 0) }), Is.EqualTo(1));
			Assert.That(SquadManagerBotModuleCA.GuerrillaSquadCap(armed, 0,
				new IBotUtilityAxes[] { new StubUtilityAxes(50, 50) }), Is.EqualTo(2));
		}

		[Test]
		public void SituationLogRecordsTheAxes()
		{
			var situation = new BotSituation
			{
				Tick = 1500,
				Enemies = new System.Collections.Generic.Dictionary<OpenRA.Player, EnemyProfile>(),
				Demand = new CounterDemand(),
				UtilityTurtleRush = 72,
				UtilityTechRushExpansion = 31,
				UtilitySteamrollerGuerrilla = 58
			};
			var b = new StringBuilder();
			AiSituationLogWriter.AppendSituation(b, "game", "", "map", "Multi0", "td_gdi", "medium", "rush", situation);
			using var doc = JsonDocument.Parse(b.ToString());
			var own = doc.RootElement.GetProperty("own");
			Assert.That(own.GetProperty("utility_turtlerush").GetInt32(), Is.EqualTo(72));
			Assert.That(own.GetProperty("utility_techrushexpansion").GetInt32(), Is.EqualTo(31));
			Assert.That(own.GetProperty("utility_steamrollerguerrilla").GetInt32(), Is.EqualTo(58));
		}
	}
}
