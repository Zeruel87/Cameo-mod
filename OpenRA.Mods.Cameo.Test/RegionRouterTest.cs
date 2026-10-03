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

using System.Collections.Generic;
using System.Linq;
using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class RegionRouterTest
	{
		// 64x64 cells -> 8x8 regions at CellSize 8.
		static RegionMemory Grid(int cells = 8) => new(new CPos(0, 0), new CPos(cells * 8 - 1, cells * 8 - 1), 8);

		[Test]
		public void SameRegionReturnsNull()
		{
			var regions = Grid();
			Assert.That(RegionRouter.Route(regions, new CPos(4, 4), new CPos(6, 6), i => 0, 1000, 4), Is.Null);
		}

		[Test]
		public void DirectRouteRunsStraightWhenNoThreat()
		{
			var regions = Grid();
			var route = RegionRouter.Route(regions, new CPos(4, 4), new CPos(60, 4), i => 0, 1000, 4);
			Assert.That(route, Is.Not.Null);
			Assert.That(route[route.Count - 1], Is.EqualTo(new CPos(60, 4)));
			foreach (var waypoint in route)
				Assert.That(waypoint.Y, Is.LessThanOrEqualTo(12), "direct route should stay in the first row of regions");
		}

		[Test]
		public void ThreatWallForcesADetour()
		{
			var regions = Grid();

			// Wall of threat down column 3 (cells X 24-31), rows 0-5. Region 3,6/3,7 stay free.
			var wall = new HashSet<int>();
			for (var row = 0; row <= 5; row++)
				wall.Add(row * 8 + 3);

			var route = RegionRouter.Route(regions, new CPos(4, 4), new CPos(52, 4), i => wall.Contains(i) ? 100000 : 0, 1000, 4);
			Assert.That(route, Is.Not.Null);
			Assert.That(route[route.Count - 1], Is.EqualTo(new CPos(52, 4)));

			foreach (var waypoint in route)
			{
				var index = regions.IndexOf(waypoint);
				Assert.That(wall.Contains(index), Is.False, $"waypoint {waypoint} sits in the threat wall");
			}
		}

		[Test]
		public void GoalRegionThreatIsNotCharged()
		{
			var regions = Grid();

			// Massive threat in the goal region must not deter the route — the
			// risk gate, not the router, decides whether to go at all.
			var goalIndex = regions.IndexOf(new CPos(52, 52));
			var route = RegionRouter.Route(regions, new CPos(4, 4), new CPos(52, 52), i => i == goalIndex ? int.MaxValue : 0, 1000, 4);
			Assert.That(route, Is.Not.Null);
			Assert.That(route[route.Count - 1], Is.EqualTo(new CPos(52, 52)));
		}

		[Test]
		public void MaxWaypointsIsRespected()
		{
			var regions = Grid(16);
			var route = RegionRouter.Route(regions, new CPos(4, 4), new CPos(124, 124), i => 0, 1000, 4);
			Assert.That(route, Is.Not.Null);
			Assert.That(route.Count, Is.LessThanOrEqualTo(4));
			Assert.That(route[route.Count - 1], Is.EqualTo(new CPos(124, 124)));
		}

		[Test]
		public void UnreachableWaypointsAreDropped()
		{
			var regions = Grid();

			// Every second region center pretends to be water for this locomotor.
			var blockedX = new HashSet<int> { 20, 36 };
			var route = RegionRouter.Route(regions, new CPos(4, 4), new CPos(60, 4), i => 0, 1000, 8,
				(a, b) => !blockedX.Contains(b.X));

			Assert.That(route, Is.Not.Null);
			foreach (var waypoint in route)
				Assert.That(blockedX.Contains(waypoint.X), Is.False, $"unreachable waypoint {waypoint} was kept");
		}

		[Test]
		public void AirborneLeadersPayAntiAirNotGroundThreat()
		{
			// CA-5 (§12.8): the same region read splits by leader domain —
			// ground pays Army+Defence, air pays AntiAir, holes pay nothing.
			var region = new RegionMemory.Region { ArmyValue = 1000, DefenceValue = 500, AntiAirValue = 200 };
			Assert.That(MasterAiBotModule.RememberedThreatAtRegion(region, false), Is.EqualTo(1500));
			Assert.That(MasterAiBotModule.RememberedThreatAtRegion(region, true), Is.EqualTo(200));
			Assert.That(MasterAiBotModule.RememberedThreatAtRegion(null, true), Is.Zero);
			Assert.That(MasterAiBotModule.RememberedThreatAtRegion(null, false), Is.Zero);
		}

		[Test]
		public void HangBackAnchorOffsetsAwayFromTarget()
		{
			// Parent at X=10000, target due east at X=20000: anchor sits 1024
			// world units BEHIND the parent, away from the target.
			var anchor = OpenRA.Mods.CA.Traits.SquadManagerBotModuleCA.HangBackAnchor(
				new WPos(10000, 0, 0), new WPos(20000, 0, 0), 1024);
			Assert.That(anchor.X, Is.EqualTo(8976));
			Assert.That(anchor.Y, Is.EqualTo(0));
		}

		[Test]
		public void HangBackAnchorColocatedReturnsParent()
		{
			var pos = new WPos(5000, 5000, 0);
			Assert.That(OpenRA.Mods.CA.Traits.SquadManagerBotModuleCA.HangBackAnchor(pos, pos, 1024), Is.EqualTo(pos));
		}
	}
}
