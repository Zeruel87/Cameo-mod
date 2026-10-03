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
using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class ZoneTopologyTest
	{
		[Test]
		public void ConnectedComponentCollectsOnlyTheLinkedCells()
		{
			// A 3-cell row plus one disjoint cell: the component from (0,0) takes the row only.
			// The helper's contract is that the seed is already in `visited` (see its remark).
			var cells = new HashSet<CPos> { new(0, 0), new(1, 0), new(2, 0), new(5, 5) };
			var visited = new HashSet<CPos> { new(0, 0) };

			var comp = TacticalMapBotModule.ConnectedComponent(new CPos(0, 0), cells, visited);

			Assert.That(comp, Is.EquivalentTo(new[] { new CPos(0, 0), new CPos(1, 0), new CPos(2, 0) }));
			Assert.That(comp, Does.Not.Contain(new CPos(5, 5)), "a disjoint cell belongs to another component");
			Assert.That(visited.Count, Is.EqualTo(3), "visited marks exactly the collected cells");
		}

		[Test]
		public void ConnectedComponentReachesDiagonallyAdjacentCells()
		{
			// CVec.Directions is 8-connected; a diagonal chain is one component.
			var cells = new HashSet<CPos> { new(0, 0), new(1, 1), new(2, 2) };
			var comp = TacticalMapBotModule.ConnectedComponent(new CPos(0, 0), cells, new HashSet<CPos> { new(0, 0) });

			Assert.That(comp.Count, Is.EqualTo(3));
		}

		[Test]
		public void CentroidPicksTheMemberNearestTheGeometricCentre()
		{
			// Geometric centre (6,0) is not itself a member; (10,0) at distance 16 wins over (10,1) at 17.
			var cells = new List<CPos> { new(0, 0), new(10, 0), new(10, 1) };

			var rep = TacticalMapBotModule.Centroid(cells);

			Assert.That(rep, Is.EqualTo(new CPos(10, 0)));
			Assert.That(cells, Does.Contain(rep), "the representative is always a real member, not the mean point");
		}

		[Test]
		public void CentroidKeepsFirstOnATie()
		{
			// Centre (1,1): (0,0) and (0,2) tie at distance 2; the scan keeps the first-seen best.
			var cells = new List<CPos> { new(0, 0), new(0, 2), new(4, 1) };

			Assert.That(TacticalMapBotModule.Centroid(cells), Is.EqualTo(new CPos(0, 0)));
		}

		// ---- ZG-b: ported pure helpers ----

		[Test]
		public void TallyOwnersMajorityWinsAndTieIsContested()
		{
			// Region 0: A outnumbers B. Region 1: A and B tie -> contested (null), the donor's fix.
			// Region 2: untouched by the tally -> null. Region 3: single owner.
			var tally = new Dictionary<int, Dictionary<string, int>>
			{
				[0] = new() { ["a"] = 3, ["b"] = 1 },
				[1] = new() { ["a"] = 2, ["b"] = 2 },
				[3] = new() { ["b"] = 4 },
			};

			var owners = TacticalMapBotModule.TallyOwners(4, tally);

			Assert.That(owners[0], Is.EqualTo("a"));
			Assert.That(owners[1], Is.Null, "a tied region is contested, not handed to whoever enumerated first");
			Assert.That(owners[2], Is.Null, "a region with no tally is unclaimed");
			Assert.That(owners[3], Is.EqualTo("b"));
		}

		[Test]
		public void TallyOwnersIgnoresStrayRegionIds()
		{
			// A tally entry outside the region range must not write out of bounds (re-cut mid-refresh).
			var tally = new Dictionary<int, Dictionary<string, int>>
			{
				[9] = new() { ["a"] = 5 },
				[-1] = new() { ["b"] = 5 },
			};

			var owners = TacticalMapBotModule.TallyOwners(2, tally);

			Assert.That(owners, Is.All.Null);
		}

		[Test]
		public void DoorApproachAxisPicksTheDominantAxis()
		{
			var door = new ZoneTerritoryDoor(new CPos(4, 4), [new CPos(4, 4)], new CVec(1, 5), 100);

			Assert.That(TacticalMapBotModule.DoorApproachAxis(door), Is.EqualTo(new CVec(0, 1)),
				"|Y| > |X| -> the approach runs along Y");
		}

		[Test]
		public void DoorApproachAxisFallsToXOnATie()
		{
			// |X| == |Y| is not strictly less, so the X axis answers.
			var door = new ZoneTerritoryDoor(new CPos(4, 4), [new CPos(4, 4)], new CVec(-3, 3), 100);

			Assert.That(TacticalMapBotModule.DoorApproachAxis(door), Is.EqualTo(new CVec(-1, 0)));
		}

		[Test]
		public void DoorWeightScalesBetweenFloorAndCeiling()
		{
			// floor 120, ceiling 200, qualifying range 96..1200.
			Assert.That(TacticalMapBotModule.DoorWeight(96, 96, 1200, 120, 200), Is.EqualTo(120), "at the floor");
			Assert.That(TacticalMapBotModule.DoorWeight(1200, 96, 1200, 120, 200), Is.EqualTo(200), "at the cap");
			Assert.That(TacticalMapBotModule.DoorWeight(648, 96, 1200, 120, 200), Is.EqualTo(160), "midpoint");
			Assert.That(TacticalMapBotModule.DoorWeight(5000, 96, 1200, 120, 200), Is.EqualTo(200), "beyond the cap clamps");
		}

		[Test]
		public void DoorWeightCollapsesToCeilingWhenFloorMeetsCap()
		{
			// minBeyond >= cap: the scale has no width, so every qualifying door weighs the ceiling.
			Assert.That(TacticalMapBotModule.DoorWeight(0, 100, 100, 120, 200), Is.EqualTo(200));
		}

		[Test]
		public void CoverageScaledDoorWeightDropsAsCoverageFills()
		{
			// Width 8 with 4 cells-per-defence needs 1 + 8/4 = 3 structures; 2 covered -> a third remains.
			Assert.That(TacticalMapBotModule.CoverageScaledDoorWeight(180, 8, 2, 4), Is.EqualTo(60));
			Assert.That(TacticalMapBotModule.CoverageScaledDoorWeight(180, 8, 3, 4), Is.EqualTo(0), "fully covered drops out");
			Assert.That(TacticalMapBotModule.CoverageScaledDoorWeight(180, 8, 99, 4), Is.EqualTo(0), "over-covered clamps");
			Assert.That(TacticalMapBotModule.CoverageScaledDoorWeight(180, 8, 0, 4), Is.EqualTo(180), "uncovered keeps full weight");
		}
	}
}
