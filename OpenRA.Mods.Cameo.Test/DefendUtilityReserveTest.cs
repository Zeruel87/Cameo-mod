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
	// UT-3 (AI_DEEP_RESEARCH.md §5.1 'defence share'): the TurtleRush axis scales the
	// CA-2 defend reserve — turtles dig in deeper, rushers strip the pool for the wave.
	// The lean only modulates a reserve that CA-2 already keeps; UseDefendPreservation
	// off, emergency, or a too-small pool all bypass it exactly as before.
	[TestFixture]
	public class DefendUtilityReserveTest
	{
		sealed class StubAxes : IBotUtilityAxes
		{
			readonly int turtleRush;
			public StubAxes(int turtleRush) { this.turtleRush = turtleRush; }
			public int UtilityTurtleRush => turtleRush;
			public int UtilityTechRushExpansion => IBotUtilityAxes.Neutral;
			public int UtilitySteamrollerGuerrilla => IBotUtilityAxes.Neutral;
		}

		static SquadManagerBotModuleCAInfo Armed() => FieldLoader.Load<SquadManagerBotModuleCAInfo>(
			new MiniYaml("", new[]
			{
				new MiniYamlNode("UseDefendPreservation", new MiniYaml("true")),
				new MiniYamlNode("UseUtilityDefendReserve", new MiniYaml("true"))
			}));

		[Test]
		public void AxisMapHitsThePolesAndNeutral()
		{
			Assert.That(SquadManagerBotModuleCA.DefendReserveAxisPercent(0, 200, 50), Is.EqualTo(200));
			Assert.That(SquadManagerBotModuleCA.DefendReserveAxisPercent(50, 200, 50), Is.EqualTo(100));
			Assert.That(SquadManagerBotModuleCA.DefendReserveAxisPercent(100, 200, 50), Is.EqualTo(50));
			Assert.That(SquadManagerBotModuleCA.DefendReserveAxisPercent(25, 200, 50), Is.EqualTo(150));
			Assert.That(SquadManagerBotModuleCA.DefendReserveAxisPercent(75, 200, 50), Is.EqualTo(75));
		}

		[Test]
		public void FlagOffIgnoresTheProvider()
		{
			var info = FieldLoader.Load<SquadManagerBotModuleCAInfo>(
				new MiniYaml("", new[] { new MiniYamlNode("UseDefendPreservation", new MiniYaml("true")) }));
			var providers = new IBotUtilityAxes[] { new StubAxes(0) };

			// 40 draftable, plain 25% reserve = keep 10, draft 30 — the turtle pole cannot deepen it.
			Assert.That(SquadManagerBotModuleCA.DefendDraftLimit(40, false, info, providers), Is.EqualTo(30));
		}

		[Test]
		public void NeutralAxisIsThePlainReserve()
		{
			var info = Armed();
			var providers = new IBotUtilityAxes[] { new StubAxes(IBotUtilityAxes.Neutral) };
			Assert.That(SquadManagerBotModuleCA.DefendDraftLimit(40, false, info, providers), Is.EqualTo(30),
				"neutral must be bit-identical to the CA-2 reserve");
		}

		[Test]
		public void TurtlePoleDoublesTheReserve()
		{
			var info = Armed();
			var providers = new IBotUtilityAxes[] { new StubAxes(0) };

			// 40 draftable: 25% x 200% = 50% reserve = keep 20, draft 20.
			Assert.That(SquadManagerBotModuleCA.DefendDraftLimit(40, false, info, providers), Is.EqualTo(20));
		}

		[Test]
		public void RushPoleHalvesTheReserve()
		{
			var info = Armed();
			var providers = new IBotUtilityAxes[] { new StubAxes(100) };

			// 40 draftable: 25% x 50% = 12% reserve = keep max(4, 4.8->4) = 4, draft 36.
			Assert.That(SquadManagerBotModuleCA.DefendDraftLimit(40, false, info, providers), Is.EqualTo(36));
		}

		[Test]
		public void EmergencyAndSmallPoolBypassTheAxis()
		{
			var info = Armed();
			var providers = new IBotUtilityAxes[] { new StubAxes(0) };
			Assert.That(SquadManagerBotModuleCA.DefendDraftLimit(40, true, info, providers), Is.EqualTo(40),
				"attacker inside the base commits everything — the axis never overrides an emergency");
			Assert.That(SquadManagerBotModuleCA.DefendDraftLimit(5, false, info, providers), Is.EqualTo(5));
		}

		[Test]
		public void MissingProviderReadsNeutral()
		{
			var info = Armed();
			Assert.That(SquadManagerBotModuleCA.DefendDraftLimit(40, false, info, null), Is.EqualTo(30));
			Assert.That(SquadManagerBotModuleCA.DefendDraftLimit(40, false, info, new IBotUtilityAxes[0]), Is.EqualTo(30));
		}
	}
}
