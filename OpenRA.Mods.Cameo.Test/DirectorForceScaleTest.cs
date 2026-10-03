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

using NUnit.Framework;
using OpenRA;
using OpenRA.Mods.CA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	// DI-2 (AI_ARCHITECTURE.md 12.16): the pacing Director's wave phase scales the
	// assault launch bar — Climax discharges tension by releasing on a smaller
	// pool, Relief holds the rebuild longer after a wave breaks. The flag-off
	// path never calls the helpers, so these tests pin the armed behaviour.
	[TestFixture]
	public class DirectorForceScaleTest
	{
		static SquadManagerBotModuleCAInfo Info() => new();

		[Test]
		public void PhaseMapsToItsScale()
		{
			var info = Info();
			Assert.That(SquadManagerBotModuleCA.DirectorForceScalePercent(DirectorPhase.BuildUp, info),
				Is.EqualTo(info.DirectorBuildUpForceScalePercent));
			Assert.That(SquadManagerBotModuleCA.DirectorForceScalePercent(DirectorPhase.Pressure, info),
				Is.EqualTo(info.DirectorPressureForceScalePercent));
			Assert.That(SquadManagerBotModuleCA.DirectorForceScalePercent(DirectorPhase.Climax, info),
				Is.EqualTo(info.DirectorClimaxForceScalePercent));
			Assert.That(SquadManagerBotModuleCA.DirectorForceScalePercent(DirectorPhase.Relief, info),
				Is.EqualTo(info.DirectorReliefForceScalePercent));
		}

		[Test]
		public void BuildUpDefaultIsNeutral()
		{
			// A disabled or absent Director provider reads BuildUp — the default
			// must be the baseline bar so an un-pacing bot is never shifted.
			Assert.That(Info().DirectorBuildUpForceScalePercent, Is.EqualTo(100));
		}

		[Test]
		public void ClimaxReleasesSmallerThanBaseline()
		{
			// The wave's release valve: the launch bar drops below baseline when
			// the Director reaches Climax.
			Assert.That(Info().DirectorClimaxForceScalePercent, Is.LessThan(100));
			Assert.That(SquadManagerBotModuleCA.ApplyForceScale(2000, Info().DirectorClimaxForceScalePercent),
				Is.LessThan(2000));
		}

		[Test]
		public void ReliefHoldsAboveBaseline()
		{
			// After a wave breaks the bot rebuilds past the baseline bar instead of
			// immediately re-committing what survived.
			Assert.That(Info().DirectorReliefForceScalePercent, Is.GreaterThan(100));
			Assert.That(SquadManagerBotModuleCA.ApplyForceScale(2000, Info().DirectorReliefForceScalePercent),
				Is.GreaterThan(2000));
		}

		[Test]
		public void ZeroBarStaysZero()
		{
			// SquadValue 0 makes the value bar trivially passing — scaling must not
			// invent a minimum that blocks dispatch for those configs.
			Assert.That(SquadManagerBotModuleCA.ApplyForceScale(0, 55), Is.EqualTo(0));
			Assert.That(SquadManagerBotModuleCA.ApplyForceScale(0, 150), Is.EqualTo(0));
		}

		[Test]
		public void PositiveBarNeverRoundsToZero()
		{
			Assert.That(SquadManagerBotModuleCA.ApplyForceScale(1, 1), Is.EqualTo(1));
			Assert.That(SquadManagerBotModuleCA.ApplyForceScale(7, 55), Is.EqualTo(3));
			Assert.That(SquadManagerBotModuleCA.ApplyForceScale(10, 150), Is.EqualTo(15));
		}

		[Test]
		public void YamlOverridesLoad()
		{
			var info = FieldLoader.Load<SquadManagerBotModuleCAInfo>(
				new MiniYaml("", new[] { new MiniYamlNode("DirectorClimaxForceScalePercent", new MiniYaml("70")) }));
			Assert.That(SquadManagerBotModuleCA.DirectorForceScalePercent(DirectorPhase.Climax, info), Is.EqualTo(70));
			Assert.That(info.DirectorReliefForceScalePercent, Is.EqualTo(150), "unmentioned knobs keep defaults");
		}
	}
}
