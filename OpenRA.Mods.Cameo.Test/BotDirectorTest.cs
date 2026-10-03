#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public sealed class BotDirectorTest
	{
		const int SnapshotTicks = 150;

		static BotDirector Drive(int snapshots, ref int tick, BotDirector director,
			MasterAiBotModuleInfo info, int ownArmy = 5000, int attacksDelta = 0,
			int freshKills = 0, int freshLosses = 0)
		{
			for (var i = 0; i < snapshots; i++)
			{
				tick += SnapshotTicks;
				director.Observe(tick, ownArmy, attacksDelta, freshKills, freshLosses, info);
				Assert.That(director.Tension, Is.InRange(0, 100));
			}

			return director;
		}

		static BotDirector DriveToPressure(BotDirector director, MasterAiBotModuleInfo info, ref int tick)
		{
			for (var i = 0; i < 60 && director.Phase != DirectorPhase.Pressure; i++)
			{
				tick += SnapshotTicks;
				director.Observe(tick, 5000, 0, 0, 0, info);
			}

			Assert.That(director.Phase, Is.EqualTo(DirectorPhase.Pressure));
			Assert.That(director.Tension, Is.InRange(info.DirectorPressureThreshold, info.DirectorClimaxThreshold - 1));
			return director;
		}

		[Test]
		public void MassedIdleArmyBuildsTensionIntoPressure()
		{
			var info = new MasterAiBotModuleInfo();
			var director = new BotDirector();
			var tick = 0;
			var previous = -1;
			while (director.Phase == DirectorPhase.BuildUp)
			{
				Drive(1, ref tick, director, info);
				Assert.That(director.Tension, Is.GreaterThan(previous));
				previous = director.Tension;
				Assert.That(tick, Is.LessThan(20000), "tension should reach Pressure within a few game-minutes");
			}

			Assert.That(director.Phase, Is.EqualTo(DirectorPhase.Pressure));
			Assert.That(director.Tension, Is.GreaterThanOrEqualTo(info.DirectorPressureThreshold));
		}

		[Test]
		public void ThinArmyDecaysTensionAndNeverGoesNegative()
		{
			var info = new MasterAiBotModuleInfo();
			var director = new BotDirector();
			var tick = 0;
			Drive(10, ref tick, director, info, ownArmy: 5000);
			Assert.That(director.Tension, Is.GreaterThan(0));

			var previous = director.Tension;
			while (director.Tension > 0)
			{
				Drive(1, ref tick, director, info, ownArmy: 0);
				Assert.That(director.Tension, Is.LessThan(previous));
				previous = director.Tension;
			}

			// Already at the floor: another thin snapshot stays 0, never negative.
			Drive(3, ref tick, director, info, ownArmy: 0);
			Assert.That(director.Tension, Is.EqualTo(0));
		}

		[Test]
		public void AttackDuringBuildUpDoesNotPromoteToClimax()
		{
			// Spec literal: a launch crests the wave only out of Pressure — an early
			// attack during BuildUp just resets the impatience clock.
			var info = new MasterAiBotModuleInfo();
			var director = new BotDirector();
			var tick = 0;
			Drive(1, ref tick, director, info, ownArmy: 5000, attacksDelta: 1);
			Assert.That(director.Phase, Is.EqualTo(DirectorPhase.BuildUp));
		}

		[Test]
		public void AttackLaunchedFromPressurePromotesToClimax()
		{
			var info = new MasterAiBotModuleInfo();
			var director = new BotDirector();
			var tick = 0;
			DriveToPressure(director, info, ref tick);
			Drive(1, ref tick, director, info, attacksDelta: 1);
			Assert.That(director.Phase, Is.EqualTo(DirectorPhase.Climax));
		}

		[Test]
		public void TensionAtClimaxThresholdAlsoPromotes()
		{
			var info = new MasterAiBotModuleInfo();
			var director = new BotDirector();
			var tick = 0;
			while (director.Phase != DirectorPhase.Climax)
			{
				Drive(1, ref tick, director, info);
				Assert.That(director.Phase == DirectorPhase.Climax || director.Tension < info.DirectorClimaxThreshold,
					"no phase may sit at/above the climax threshold without being Climax");
				Assert.That(tick, Is.LessThan(60000));
			}

			Assert.That(director.Tension, Is.GreaterThanOrEqualTo(info.DirectorClimaxThreshold));
		}

		[Test]
		public void ClimaxRelaxesIntoReliefWhenTheKillWindowFlattens()
		{
			var info = new MasterAiBotModuleInfo();
			var director = new BotDirector();
			var tick = 0;
			DriveToPressure(director, info, ref tick);
			Drive(1, ref tick, director, info, attacksDelta: 1);
			Assert.That(director.Phase, Is.EqualTo(DirectorPhase.Climax));

			var quietSnapshots = info.DirectorReliefQuietTicks / SnapshotTicks;
			Drive(quietSnapshots - 1, ref tick, director, info, freshKills: 0);
			Assert.That(director.Phase, Is.EqualTo(DirectorPhase.Climax));
			Drive(1, ref tick, director, info);
			Assert.That(director.Phase, Is.EqualTo(DirectorPhase.Relief));
			Assert.That(director.Tension, Is.EqualTo(info.DirectorReliefTension));
		}

		[Test]
		public void FreshKillsKeepClimaxAlivePastTheQuietWindow()
		{
			var info = new MasterAiBotModuleInfo();
			var director = new BotDirector();
			var tick = 0;
			DriveToPressure(director, info, ref tick);
			Drive(1, ref tick, director, info, attacksDelta: 1);
			Assert.That(director.Phase, Is.EqualTo(DirectorPhase.Climax));

			// Past the quiet window, but every snapshot carries a fresh kill delta —
			// the attack is still paying out, so the wave has not broken.
			var quietSnapshots = info.DirectorReliefQuietTicks / SnapshotTicks;
			Drive(quietSnapshots + 2, ref tick, director, info, freshKills: 150);
			Assert.That(director.Phase, Is.EqualTo(DirectorPhase.Climax));
		}

		[Test]
		public void LossSpikeBreaksClimaxImmediately()
		{
			var info = new MasterAiBotModuleInfo();
			var director = new BotDirector();
			var tick = 0;
			DriveToPressure(director, info, ref tick);
			Drive(1, ref tick, director, info, attacksDelta: 1);
			Assert.That(director.Phase, Is.EqualTo(DirectorPhase.Climax));

			// One snapshot later the counter-attack lands: the wave broke on us.
			Drive(1, ref tick, director, info, freshLosses: info.DirectorLossSpikeValue);
			Assert.That(director.Phase, Is.EqualTo(DirectorPhase.Relief));
			Assert.That(director.Tension, Is.EqualTo(info.DirectorReliefTension));
		}

		[Test]
		public void LossSpikeBreaksPressureImmediately()
		{
			// A massed army shredded at home before delivering is the same broken wave.
			var info = new MasterAiBotModuleInfo();
			var director = new BotDirector();
			var tick = 0;
			DriveToPressure(director, info, ref tick);
			var before = director.Tension;
			Drive(1, ref tick, director, info, freshLosses: info.DirectorLossSpikeValue);
			Assert.That(director.Phase, Is.EqualTo(DirectorPhase.Relief));
			Assert.That(director.Tension, Is.LessThan(before));
			Assert.That(director.Tension, Is.EqualTo(info.DirectorReliefTension));
		}

		[Test]
		public void ReliefReArmsToBuildUpAboveTheExitThreshold()
		{
			var info = new MasterAiBotModuleInfo();
			var director = new BotDirector();
			var tick = 0;
			DriveToPressure(director, info, ref tick);
			Drive(1, ref tick, director, info, attacksDelta: 1);
			Drive(info.DirectorReliefQuietTicks / SnapshotTicks, ref tick, director, info);
			Assert.That(director.Phase, Is.EqualTo(DirectorPhase.Relief));
			Assert.That(director.Tension, Is.EqualTo(info.DirectorReliefTension));

			// Army still massed: tension re-accumulates; below the exit threshold the
			// phase holds Relief — the re-arm point sits above the reset, not on it.
			for (var i = 0; i < 40 && director.Phase == DirectorPhase.Relief; i++)
			{
				Drive(1, ref tick, director, info);
				if (director.Tension < info.DirectorReliefExitThreshold)
					Assert.That(director.Phase, Is.EqualTo(DirectorPhase.Relief));
			}

			Assert.That(director.Phase, Is.EqualTo(DirectorPhase.BuildUp));
			Assert.That(director.Tension, Is.GreaterThanOrEqualTo(info.DirectorReliefExitThreshold));
		}

		[Test]
		public void PressureThresholdHasHysteresisBothWays()
		{
			var info = new MasterAiBotModuleInfo();
			var director = new BotDirector();
			var tick = 0;
			DriveToPressure(director, info, ref tick);

			// Descend on a thin army (pure decay — impatience only feeds a massed
			// army): the phase must hold Pressure through the dead-band
			// [threshold - hysteresis, threshold) and only exit below it.
			var bandFloor = info.DirectorPressureThreshold - info.DirectorHysteresis;
			var descentSawBand = false;
			while (director.Phase == DirectorPhase.Pressure)
			{
				Drive(1, ref tick, director, info, ownArmy: 0);
				if (director.Tension >= bandFloor && director.Tension < info.DirectorPressureThreshold)
				{
					descentSawBand = true;
					Assert.That(director.Phase, Is.EqualTo(DirectorPhase.Pressure),
						"Pressure must hold inside the hysteresis band");
				}

				Assert.That(tick, Is.LessThan(100000));
			}

			Assert.That(director.Phase, Is.EqualTo(DirectorPhase.BuildUp));
			Assert.That(descentSawBand, Is.True, "the descent must pass through the dead-band");
			Assert.That(director.Tension, Is.LessThan(bandFloor));

			// Re-arm: inside the same dead-band the phase must now hold BuildUp — the
			// same tension readings hold a different phase depending on direction.
			var ascentSawBand = false;
			while (director.Phase == DirectorPhase.BuildUp && director.Tension < info.DirectorPressureThreshold)
			{
				Drive(1, ref tick, director, info, ownArmy: 5000);
				if (director.Tension >= bandFloor && director.Tension < info.DirectorPressureThreshold)
				{
					ascentSawBand = true;
					Assert.That(director.Phase, Is.EqualTo(DirectorPhase.BuildUp),
						"BuildUp must hold inside the hysteresis band on the way back up");
				}

				Assert.That(tick, Is.LessThan(200000));
			}

			Assert.That(ascentSawBand, Is.True, "the re-arm must pass through the dead-band");
			Assert.That(director.Phase, Is.EqualTo(DirectorPhase.Pressure));
		}

		[Test]
		public void ImpatienceIsCappedPerSnapshot()
		{
			var info = new MasterAiBotModuleInfo();
			var director = new BotDirector();

			// An absurdly idle massed army at its first snapshot: one step adds at
			// most rise + the impatience cap, never the raw idle quotient.
			director.Observe(10_000_000, 5000, 0, 0, 0, info);
			Assert.That(director.Tension, Is.EqualTo(
				info.DirectorTensionRisePerSnapshot + info.DirectorImpatienceMaxPerSnapshot));
		}

		[Test]
		public void SustainedClimaxCanPinTensionAtTheCap()
		{
			var info = new MasterAiBotModuleInfo();
			var director = new BotDirector();
			var tick = 0;
			DriveToPressure(director, info, ref tick);
			Drive(1, ref tick, director, info, attacksDelta: 1);
			var sawCap = false;
			for (var i = 0; i < 40 && !sawCap; i++)
			{
				Drive(1, ref tick, director, info, freshKills: 150);
				sawCap = director.Tension == 100;
				Assert.That(director.Phase, Is.EqualTo(DirectorPhase.Climax));
			}

			Assert.That(sawCap, Is.True, "a kept-alive climax must be able to sit on the 100 cap");
		}

		[Test]
		public void SituationLogEmitsDirectorFields()
		{
			var situation = new BotSituation
			{
				Tick = 1500,
				Enemies = new Dictionary<OpenRA.Player, EnemyProfile>(),
				Demand = new CounterDemand(),
				DirectorTension = 42,
				DirectorPhase = DirectorPhase.Pressure
			};
			var b = new StringBuilder();
			AiSituationLogWriter.AppendSituation(b, "game", "", "map", "Multi0", "td_gdi", "medium", "rush", situation);
			using var doc = JsonDocument.Parse(b.ToString());
			var own = doc.RootElement.GetProperty("own");
			Assert.That(own.GetProperty("director_tension").GetInt32(), Is.EqualTo(42));
			Assert.That(own.GetProperty("director_phase").GetString(), Is.EqualTo("pressure"));
		}
	}
}
