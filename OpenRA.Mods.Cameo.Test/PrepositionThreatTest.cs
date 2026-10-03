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
using OpenRA.Mods.CA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class PrepositionThreatTest
	{
		static BotPredictedThreat T(int eta, int value) => new(new CPos(eta, value), eta, value, 0);

		[Test]
		public void TheBiggestThreatInTimeAndLargeEnoughIsMet()
		{
			var pick = SquadManagerBotModuleCA.SelectPrepositionThreat(new[] { T(900, 3000), T(400, 8000), T(3000, 20000), T(200, 500) }, 1500, 1500);
			Assert.That(pick?.Value, Is.EqualTo(8000));
		}

		[TestCase(40, 0.1, 500, true)]
		[TestCase(40, 0.1, 300, false)]
		[TestCase(40, 0, 100000, false)]
		public void AFastSquadJoinsOnlyIfItArrivesFirst(double cells, double speed, int eta, bool expected)
		{
			Assert.That(SquadManagerBotModuleCA.ArrivesInTime(cells, speed, eta), Is.EqualTo(expected));
		}

		[Test]
		public void NothingSmallOrFarIsMet()
		{
			Assert.That(SquadManagerBotModuleCA.SelectPrepositionThreat(new[] { T(3000, 20000), T(200, 500) }, 1500, 1500), Is.Null);
		}

		static BotProtectionRequest R(int x, int value, int expires) => new(new CPos(x, 0), value, expires);

		[Test]
		public void ExpiredAndSmallRequestsAreSkipped()
		{
			var pick = SquadManagerBotModuleCA.SelectProtectionRequest(
				new[] { R(1, 5000, 90), R(2, 400, 900), R(3, 8000, 900) }, 100, 1500);
			Assert.That(pick?.Location, Is.EqualTo(new CPos(3, 0)));
		}

		[Test]
		public void TheMostValuableLiveRequestWins()
		{
			var pick = SquadManagerBotModuleCA.SelectProtectionRequest(
				new[] { R(1, 3000, 800), R(2, 9000, 900), R(3, 6000, 700) }, 100, 1500);
			Assert.That(pick?.Location, Is.EqualTo(new CPos(2, 0)));
		}

		[Test]
		public void NoLiveRequestReturnsNull()
		{
			Assert.That(SquadManagerBotModuleCA.SelectProtectionRequest(
				new[] { R(1, 5000, 99) }, 100, 1500), Is.Null);
			Assert.That(SquadManagerBotModuleCA.SelectProtectionRequest(
				new BotProtectionRequest[0], 100, 1500), Is.Null);
		}
	}
}
