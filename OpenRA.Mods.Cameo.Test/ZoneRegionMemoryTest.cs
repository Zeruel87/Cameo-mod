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

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class ZoneRegionMemoryTest
	{
		// Engine-free stand-in for TacticalMapBotModule: a fixed cell->zone map plus an
		// explicit adjacency list, and the same nearest-region ring contract the module
		// implements (own id first, then a small expanding scan, then -1).
		sealed class FakeZoneTopology : IBotZoneTopology
		{
			readonly Dictionary<CPos, int> idByCell = new();

			public readonly List<Zone> ZoneList = new();
			public int Generation { get; set; }

			public IReadOnlyList<Zone> Regions => ZoneList;
			public IReadOnlyList<ZoneChokepoint> Chokepoints => Array.Empty<ZoneChokepoint>();
			public IReadOnlyList<ZoneTerritoryDoor> TerritoryDoors => Array.Empty<ZoneTerritoryDoor>();
			public IReadOnlyCollection<CPos> Territory => Array.Empty<CPos>();

			public int RegionIdAt(CPos cell) => idByCell.GetValueOrDefault(cell, -1);

			public int NearestRegionId(CPos cell)
			{
				var id = RegionIdAt(cell);
				if (id >= 0)
					return id;

				for (var radius = 1; radius <= 3; radius++)
				{
					for (var dx = -radius; dx <= radius; dx++)
					{
						for (var dy = -radius; dy <= radius; dy++)
						{
							if (Math.Max(Math.Abs(dx), Math.Abs(dy)) != radius)
								continue;

							id = RegionIdAt(cell + new CVec(dx, dy));
							if (id >= 0)
								return id;
						}
					}
				}

				return -1;
			}

			public bool IsPassableCell(CPos cell) => idByCell.ContainsKey(cell);
			public OpenRA.Player RegionOwner(int regionId) => null;
			public bool IsInTerritory(CPos cell) => false;

			public void AddZone(IEnumerable<CPos> cells, params int[] adjacent)
			{
				var id = ZoneList.Count;
				var cellArray = cells.ToArray();
				ZoneList.Add(new Zone(id, cellArray, [], adjacent, 0, cellArray.Length, []));
				foreach (var cell in cellArray)
					idByCell[cell] = id;
			}

			// A re-cut: the shared Regions list is refilled in place and every zone id
			// re-derived, exactly like the module's bridge-change rebuild.
			public void Recut()
			{
				ZoneList.Clear();
				idByCell.Clear();
			}
		}

		static RegionMemory Zoned(FakeZoneTopology topology) =>
			new(new CPos(0, 0), new CPos(63, 63), 8, topology);

		// A square grid block of cells, as one zone.
		static IEnumerable<CPos> Block(int x, int y, int size = 8)
		{
			for (var dy = 0; dy < size; dy++)
				for (var dx = 0; dx < size; dx++)
					yield return new CPos(x + dx, y + dy);
		}

		static FakeZoneTopology ChainTopology(int zones)
		{
			var topology = new FakeZoneTopology();
			for (var i = 0; i < zones; i++)
			{
				var adjacent = new List<int>();
				if (i > 0)
					adjacent.Add(i - 1);
				if (i < zones - 1)
					adjacent.Add(i + 1);

				topology.AddZone(Block(i * 8, 0), adjacent.ToArray());
			}

			return topology;
		}

		[Test]
		public void ZoneBackedIndexOfAnswersZoneIds()
		{
			var topology = ChainTopology(4);
			var regions = Zoned(topology);

			Assert.That(regions.ZoneBacked, Is.True);
			Assert.That(regions.CellCount, Is.EqualTo(4), "index space is the zone list, not grid cells");
			Assert.That(regions.IndexOf(new CPos(2, 2)), Is.EqualTo(0));
			Assert.That(regions.IndexOf(new CPos(17, 5)), Is.EqualTo(2));
		}

		[Test]
		public void ZoneCenterIsAMemberCell()
		{
			var topology = new FakeZoneTopology();
			topology.AddZone(new[] { new CPos(10, 10), new CPos(11, 10), new CPos(12, 10) }, []);
			var regions = Zoned(topology);

			var center = regions.CenterOf(0);
			Assert.That(topology.Regions[0].Cells, Does.Contain(center),
				"the zone representative is real ground of the zone, not a bounding-box middle");
		}

		[Test]
		public void GateCellFoldsIntoNearestZone()
		{
			// The -1 policy: a barrier cell (a bridge, a ramp) belongs to no region, so the
			// nearest zone a few cells out stands in - threat on a chokepoint lands somewhere.
			var topology = ChainTopology(2);
			var regions = Zoned(topology);

			Assert.That(regions.IndexOf(new CPos(8, 0)), Is.EqualTo(1), "a member cell answers its own id");
			Assert.That(regions.IndexOf(new CPos(14, 9)), Is.EqualTo(1),
				"an unzoned cell two rows off zone 1 folds into it (and only zone 1 is in reach)");
		}

		[Test]
		public void CellBeyondEveryZoneAnswersMinusOne()
		{
			var topology = ChainTopology(2);
			var regions = Zoned(topology);

			Assert.That(regions.IndexOf(new CPos(63, 63)), Is.EqualTo(-1),
				"deep unzoned ground has no region to fold into");
		}

		[Test]
		public void ZoneRouterWalksTheAdjacencyList()
		{
			var topology = ChainTopology(4);
			var regions = Zoned(topology);

			var route = RegionRouter.Route(regions, new CPos(2, 2), new CPos(30, 2), i => 0, 1000, 8);
			Assert.That(route, Is.Not.Null);
			Assert.That(route[route.Count - 1], Is.EqualTo(new CPos(30, 2)));

			var indices = route.Select(regions.IndexOf).ToArray();
			Assert.That(indices, Is.EqualTo(new[] { 1, 2, 3 }),
				"interior waypoints are the intermediate zones' centers, in adjacency order");
		}

		[Test]
		public void ZoneRouterDetoursThroughTheCheaperZone()
		{
			// Diamond: 0 -> {1, 2} -> 3. Threat on zone 1 must push the route through zone 2.
			var topology = new FakeZoneTopology();
			topology.AddZone(Block(0, 0), 1, 2);
			topology.AddZone(Block(16, 0), 0, 3);
			topology.AddZone(Block(16, 16), 0, 3);
			topology.AddZone(Block(32, 8), 1, 2);
			var regions = Zoned(topology);

			var route = RegionRouter.Route(regions, new CPos(2, 2), new CPos(36, 10),
				i => i == 1 ? 100000 : 0, 1000, 8);

			Assert.That(route, Is.Not.Null);
			var indices = route.Select(regions.IndexOf).ToArray();
			Assert.That(indices, Is.EqualTo(new[] { 2, 3 }), "the hot zone is skirted via the other branch");
		}

		[Test]
		public void DisjointZonesYieldNoRoute()
		{
			// Two islands with no adjacency at all - impossible on the always-connected grid,
			// real under zones: the router answers null instead of tunneling.
			var topology = new FakeZoneTopology();
			topology.AddZone(Block(0, 0));
			topology.AddZone(Block(40, 40));
			var regions = Zoned(topology);

			Assert.That(RegionRouter.Route(regions, new CPos(2, 2), new CPos(44, 44), i => 0, 1000, 8), Is.Null);
		}

		[Test]
		public void UnzonedEndpointYieldsNoRoute()
		{
			var topology = ChainTopology(2);
			var regions = Zoned(topology);

			// (63,63) resolves to -1: no region to route from, so no route.
			Assert.That(RegionRouter.Route(regions, new CPos(63, 63), new CPos(2, 2), i => 0, 1000, 8), Is.Null);
			Assert.That(RegionRouter.Route(regions, new CPos(2, 2), new CPos(63, 63), i => 0, 1000, 8), Is.Null);
		}

		[Test]
		public void ZoneRouterMatchesGridOnAnIsomorphicGraph()
		{
			// A 4x4 region grid where only an L corridor is affordable: the unique cheapest
			// path is forced, so grid A* and zone Dijkstra must pick the same region sequence.
			var grid = new RegionMemory(new CPos(0, 0), new CPos(31, 31), 8);
			var corridor = new HashSet<int> { 0, 1, 2, 3, 7, 11, 15 };

			var topology = new FakeZoneTopology();
			for (var row = 0; row < 4; row++)
			{
				for (var col = 0; col < 4; col++)
				{
					var adjacent = new List<int>();
					if (col > 0)
						adjacent.Add(row * 4 + col - 1);
					if (col < 3)
						adjacent.Add(row * 4 + col + 1);
					if (row > 0)
						adjacent.Add((row - 1) * 4 + col);
					if (row < 3)
						adjacent.Add((row + 1) * 4 + col);

					topology.AddZone(Block(col * 8, row * 8), adjacent.ToArray());
				}
			}

			var zoned = Zoned(topology);
			Func<int, int> wall = i => corridor.Contains(i) ? 0 : 100000;

			var gridRoute = RegionRouter.Route(grid, new CPos(2, 2), new CPos(30, 30), wall, 1000, 16);
			var zoneRoute = RegionRouter.Route(zoned, new CPos(2, 2), new CPos(30, 30), wall, 1000, 16);

			Assert.That(gridRoute, Is.Not.Null);
			Assert.That(zoneRoute, Is.Not.Null);

			var gridPath = gridRoute.Select(grid.IndexOf).ToArray();
			var zonePath = zoneRoute.Select(zoned.IndexOf).ToArray();
			Assert.That(zonePath, Is.EqualTo(gridPath), "same graph + same costs = same region sequence");
			Assert.That(zonePath, Is.EqualTo(new[] { 1, 2, 3, 7, 11, 15 }), "the forced corridor");
		}

		[Test]
		public void GridNeighborsOfIsTheOld4ConnectedExpansion()
		{
			var regions = new RegionMemory(new CPos(0, 0), new CPos(63, 63), 8);

			Assert.That(regions.NeighborsOf(0), Is.EqualTo(new[] { 1, 8 }), "a corner has two neighbours");
			Assert.That(regions.NeighborsOf(9), Is.EqualTo(new[] { 8, 10, 1, 17 }),
				"interior keeps the router's old left/right/up/down expansion order");
		}

		[Test]
		public void GenerationBumpDropsStaleRegionArrays()
		{
			var topology = ChainTopology(4);
			var regions = Zoned(topology);
			var enemy = (OpenRA.Player)RuntimeHelpers.GetUninitializedObject(typeof(OpenRA.Player));

			var cells = new RegionMemory.Region[regions.CellCount];
			cells[1] = new RegionMemory.Region { EverSeen = true, ArmyValue = 500 };
			regions.SetRegions(enemy, cells);
			Assert.That(regions.KnownRegionCount(enemy), Is.EqualTo(1));

			// A bridge re-cut reshuffles every zone id: beliefs indexed by the old ids must not
			// alias onto the new cut - the arrays drop wholesale and re-derive next snapshot.
			topology.Generation++;
			Assert.That(regions.Generation, Is.EqualTo(topology.Generation));
			Assert.That(regions.ByEnemy, Is.Empty);
			Assert.That(regions.KnownRegionCount(enemy), Is.Zero);
		}

		[Test]
		public void GenerationBumpRekeysCentersToTheNewCut()
		{
			var topology = ChainTopology(2);
			var regions = Zoned(topology);
			var oldCenter = regions.CenterOf(1);

			// The re-cut's zones occupy different ground: cached centres die with the old ids.
			topology.Recut();
			topology.AddZone(Block(0, 24), 1);
			topology.AddZone(Block(40, 24));
			topology.Generation++;

			var newCenter = regions.CenterOf(1);
			Assert.That(newCenter, Is.Not.EqualTo(oldCenter));
			Assert.That(regions.IndexOf(newCenter), Is.EqualTo(1), "the new centre belongs to the new zone 1");
		}

		[Test]
		public void ZoneBackedNeighborsOfReadsAdjacency()
		{
			var topology = ChainTopology(4);
			var regions = Zoned(topology);

			Assert.That(regions.NeighborsOf(1), Is.EquivalentTo(new[] { 0, 2 }));
			Assert.That(regions.NeighborsOf(3), Is.EquivalentTo(new[] { 2 }), "chain end has one neighbour");
			Assert.That(regions.NeighborsOf(-1), Is.Empty, "an out-of-space index expands to nothing");
			Assert.That(regions.NeighborsOf(99), Is.Empty);
		}
	}
}
