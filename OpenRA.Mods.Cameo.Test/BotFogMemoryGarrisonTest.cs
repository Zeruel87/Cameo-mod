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
	public sealed class BotFogMemoryGarrisonTest
	{
		[Test]
		public void AnEnemyHeldHouseIsPricedByItsGarrison()
		{
			// A civilian house (no Valued cost, armed through its fire ports, MaxWeight 6) was worth 0 to the
			// risk gate, so infantry walked into it one by one (AI_ARCHITECTURE §12.11-12.12).
			Assert.That(BotFogMemory.ObservedValue(0, true, 6, 200), Is.EqualTo(1200));
		}

		[Test]
		public void EverythingElseKeepsItsOwnCost()
		{
			// Off by default.
			Assert.That(BotFogMemory.ObservedValue(0, true, 6, 0), Is.EqualTo(0));

			// A priced building (a bunker with a Valued cost) keeps its cost.
			Assert.That(BotFogMemory.ObservedValue(500, true, 6, 200), Is.EqualTo(500));

			// Unarmed, or not garrisonable: unchanged.
			Assert.That(BotFogMemory.ObservedValue(0, false, 6, 200), Is.EqualTo(0));
			Assert.That(BotFogMemory.ObservedValue(0, true, 0, 200), Is.EqualTo(0));
		}
	}
}
