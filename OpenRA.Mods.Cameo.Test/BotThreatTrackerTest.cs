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
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class BotThreatTrackerTest
	{
		static BotThreatTracker.Unit U(int x, int y, int value = 500) => new(new CPos(x, y), value);

		[Test]
		public void NearbyUnitsFormOneGroupFarOnesAnother()
		{
			var groups = BotThreatTracker.Cluster(new[] { U(10, 10), U(12, 11), U(60, 60) }, 8, 100);
			Assert.That(groups, Has.Count.EqualTo(2));
			Assert.That(groups[0].Count + groups[1].Count, Is.EqualTo(3));
			Assert.That(groups[0].Value + groups[1].Value, Is.EqualTo(1500));
		}

		[Test]
		public void TrackingGivesVelocityFromThePreviousSnapshot()
		{
			var before = BotThreatTracker.Cluster(new[] { U(10, 10) }, 8, 100);
			var now = BotThreatTracker.Cluster(new[] { U(20, 10) }, 8, 200);
			var tracked = BotThreatTracker.Track(before, now, 20);
			Assert.That(tracked[0].VelocityX, Is.EqualTo(0.1).Within(1e-9));
			Assert.That(tracked[0].VelocityY, Is.Zero);
		}

		[Test]
		public void AGroupHeadsForTheValuableAssetAheadNotTheOneBehind()
		{
			var group = new BotThreatTracker.Group(50, 50, 3000, 5) { VelocityX = 0.1, VelocityY = 0, SeenTick = 1 };
			var assets = new[] { (new CPos(90, 52), 2000), (new CPos(10, 50), 9000), (new CPos(80, 90), 5000) };
			var p = BotThreatTracker.Predict(group, assets, 0.7, 0.01);
			Assert.That(p.HasValue, Is.True);
			Assert.That(p.Value.Target, Is.EqualTo(new CPos(90, 52)));
			Assert.That(p.Value.EtaTicks, Is.InRange(398, 402));
		}

		[Test]
		public void AStandingGroupPredictsNothing()
		{
			var group = new BotThreatTracker.Group(50, 50, 3000, 5) { SeenTick = 1 };
			Assert.That(BotThreatTracker.Predict(group, new[] { (new CPos(60, 50), 1000) }, 0.7, 0.01), Is.Null);
		}
	}
}
