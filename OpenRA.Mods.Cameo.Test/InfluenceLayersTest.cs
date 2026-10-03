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
	public class InfluenceLayersTest
	{
		// Engine-free stand-in for TacticalMapBotModule (same fake as ZoneRegionMemoryTest,
		// with a settable resource-cell count per zone for the Interest layer).
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
			public int NearestRegionId(CPos cell) => RegionIdAt(cell);
			public bool IsPassableCell(CPos cell) => idByCell.ContainsKey(cell);
			public OpenRA.Player RegionOwner(int regionId) => null;
			public bool IsInTerritory(CPos cell) => false;

			public void AddZone(IEnumerable<CPos> cells, int resourceCells = 0, params int[] adjacent)
			{
				var id = ZoneList.Count;
				var cellArray = cells.ToArray();
				ZoneList.Add(new Zone(id, cellArray, [], adjacent, resourceCells, cellArray.Length, []));
				foreach (var cell in cellArray)
					idByCell[cell] = id;
			}
		}

		static RegionMemory Grid() => new(new CPos(0, 0), new CPos(63, 63), 8);

		static RegionMemory Zoned(FakeZoneTopology topology) =>
			new(new CPos(0, 0), new CPos(63, 63), 8, topology);

		static IEnumerable<CPos> Block(int x, int y, int size = 8)
		{
			for (var dy = 0; dy < size; dy++)
				for (var dx = 0; dx < size; dx++)
					yield return new CPos(x + dx, y + dy);
		}

		static OpenRA.Player FakePlayer() =>
			(OpenRA.Player)RuntimeHelpers.GetUninitializedObject(typeof(OpenRA.Player));

		static BotInfluenceLayers Layers() => new(new MasterAiBotModuleInfo());

		[Test]
		public void EmaMovesTowardCurrentByAlpha()
		{
			Assert.That(BotInfluenceLayers.EmaToward(1000f, 0f, 0.2f), Is.EqualTo(200f).Within(0.001f),
				"hist = a*current + (1-a)*hist");
			Assert.That(BotInfluenceLayers.EmaToward(500f, 500f, 0.2f), Is.EqualTo(500f).Within(0.001f),
				"a steady signal is its own average");
			Assert.That(BotInfluenceLayers.EmaToward(1000f, 300f, 0f), Is.EqualTo(300f),
				"alpha 0 freezes the history");
		}

		[Test]
		public void BlendKeepsTheCurrentSightingWhileFresh()
		{
			Assert.That(BotInfluenceLayers.BlendWithHistory(1000, 200f, 0, 7500), Is.EqualTo(1000));
			Assert.That(BotInfluenceLayers.BlendWithHistory(1000, 200f, -5, 7500), Is.EqualTo(1000),
				"a negative staleness clamps to fresh");
		}

		[Test]
		public void BlendIsTheHistoryOnceFullyStale()
		{
			Assert.That(BotInfluenceLayers.BlendWithHistory(1000, 200f, 7500, 7500), Is.EqualTo(200));
			Assert.That(BotInfluenceLayers.BlendWithHistory(1000, 200f, 90000, 7500), Is.EqualTo(200),
				"staleness past the horizon still clamps at the history");
			Assert.That(BotInfluenceLayers.BlendWithHistory(1000, 200f, 10, 0), Is.EqualTo(200),
				"a zero horizon means fully stale at once");
		}

		[Test]
		public void BlendIsLinearBetweenFreshAndStale()
		{
			Assert.That(BotInfluenceLayers.BlendWithHistory(1000, 200f, 3750, 7500), Is.EqualTo(600));
			Assert.That(BotInfluenceLayers.BlendWithHistory(0, 500f, 1875, 7500), Is.EqualTo(125));
		}

		[Test]
		public void LayersSizeToTheGridCellCount()
		{
			var regions = Grid();
			var layers = Layers();
			layers.Refresh(regions, Array.Empty<OpenRA.Actor>(), null, null, 100);

			Assert.That(layers.Count, Is.EqualTo(regions.CellCount));
			Assert.That(layers.ThreatGround.Count, Is.EqualTo(regions.CellCount));
			Assert.That(layers.ThreatAir.Count, Is.EqualTo(regions.CellCount));
			Assert.That(layers.Interest.Count, Is.EqualTo(regions.CellCount));
			Assert.That(layers.OwnStrength.Count, Is.EqualTo(regions.CellCount));
			Assert.That(layers.Staleness.Count, Is.EqualTo(regions.CellCount));
		}

		[Test]
		public void LayersSizeToTheZoneCount()
		{
			var topology = new FakeZoneTopology();
			topology.AddZone(Block(0, 0));
			topology.AddZone(Block(8, 0));
			topology.AddZone(Block(16, 0));
			var regions = Zoned(topology);
			var layers = Layers();
			layers.Refresh(regions, Array.Empty<OpenRA.Actor>(), topology, null, 100);

			Assert.That(layers.Count, Is.EqualTo(3));
			Assert.That(layers.ZoneBacked, Is.True);
			Assert.That(layers.Generation, Is.EqualTo(topology.Generation));
		}

		[Test]
		public void RememberedValuesPublishIntoTheLayers()
		{
			var regions = Grid();
			var enemy = FakePlayer();
			var cells = new RegionMemory.Region[regions.CellCount];
			cells[3] = new RegionMemory.Region
			{
				ArmyValue = 300, DefenceValue = 200, AntiAirValue = 50,
				EconomyValue = 400, ProductionTechValue = 250,
				EverSeen = true, LastSeenTick = 100
			};
			regions.SetRegions(enemy, cells);

			var layers = Layers();
			layers.Refresh(regions, Array.Empty<OpenRA.Actor>(), null, null, 100);

			// A same-tick sighting has staleness 0: published threat is the current value.
			Assert.That(layers.Staleness[3], Is.EqualTo(0));
			Assert.That(layers.ThreatGround[3], Is.EqualTo(500), "ground threat = army + defence");
			Assert.That(layers.ThreatAir[3], Is.EqualTo(50), "air threat = the AA-capable value");
			Assert.That(layers.Interest[3], Is.EqualTo(650), "interest = remembered economy + production/tech");
		}

		[Test]
		public void NeverSeenRegionsReportTheNeverSeenStaleness()
		{
			var regions = Grid();
			var layers = Layers();
			var info = new MasterAiBotModuleInfo();
			layers.Refresh(regions, Array.Empty<OpenRA.Actor>(), null, null, 100);

			Assert.That(layers.Staleness[0], Is.EqualTo(100 + info.InfluenceStaleAfterTicks),
				"no enemy memory at all reads as never-seen (mirrors ScoutBotModule.Staleness)");

			var enemy = FakePlayer();
			regions.SetRegions(enemy, new RegionMemory.Region[regions.CellCount]);
			layers.Refresh(regions, Array.Empty<OpenRA.Actor>(), null, null, 100);
			Assert.That(layers.Staleness[0], Is.EqualTo(100 + info.InfluenceStaleAfterTicks),
				"an enemy table with a null region entry is never-seen too");
		}

		[Test]
		public void SeenRegionStalenessIsTheAgeOfTheSighting()
		{
			var regions = Grid();
			var enemy = FakePlayer();
			var cells = new RegionMemory.Region[regions.CellCount];
			cells[7] = new RegionMemory.Region { EverSeen = true, LastSeenTick = 40 };
			regions.SetRegions(enemy, cells);

			var layers = Layers();
			layers.Refresh(regions, Array.Empty<OpenRA.Actor>(), null, null, 100);

			Assert.That(layers.Staleness[7], Is.EqualTo(60));
			Assert.That(layers.Staleness[6], Is.EqualTo(100 + 2500),
				"the neighbouring never-seen index keeps the never-seen value");
		}

		[Test]
		public void ThreatSumsAcrossEveryEnemyTable()
		{
			var regions = Grid();
			var enemyA = FakePlayer();
			var enemyB = FakePlayer();
			var cellsA = new RegionMemory.Region[regions.CellCount];
			cellsA[2] = new RegionMemory.Region { ArmyValue = 300, EverSeen = true, LastSeenTick = 100 };
			var cellsB = new RegionMemory.Region[regions.CellCount];
			cellsB[2] = new RegionMemory.Region { ArmyValue = 100, DefenceValue = 100, EverSeen = true, LastSeenTick = 100 };
			regions.SetRegions(enemyA, cellsA);
			regions.SetRegions(enemyB, cellsB);

			var layers = Layers();
			layers.Refresh(regions, Array.Empty<OpenRA.Actor>(), null, null, 100);

			Assert.That(layers.ThreatGround[2], Is.EqualTo(500));
		}

		[Test]
		public void StaleThreatBlendsTowardTheZoneHistory()
		{
			var regions = Grid();
			var enemy = FakePlayer();
			var cells = new RegionMemory.Region[regions.CellCount];
			cells[5] = new RegionMemory.Region { ArmyValue = 1000, EverSeen = true, LastSeenTick = 6250 };
			regions.SetRegions(enemy, cells);

			var layers = Layers();
			layers.Refresh(regions, Array.Empty<OpenRA.Actor>(), null, null, 10000);

			// Staleness 3750 = half the 7500 decay horizon; the EMA just learned 0.2*1000 = 200.
			Assert.That(layers.ThreatGroundHistory[5], Is.EqualTo(200f).Within(0.001f));
			Assert.That(layers.ThreatGround[5], Is.EqualTo(600), "half-way stale publishes half-way to the average");
		}

		[Test]
		public void GenerationBumpDropsTheHistoryWithTheIds()
		{
			var topology = new FakeZoneTopology();
			topology.AddZone(Block(0, 0));
			topology.AddZone(Block(8, 0));
			var regions = Zoned(topology);
			var enemy = FakePlayer();

			var cells = new RegionMemory.Region[regions.CellCount];
			cells[1] = new RegionMemory.Region { ArmyValue = 1000, EverSeen = true, LastSeenTick = 10 };
			regions.SetRegions(enemy, cells);

			var layers = Layers();
			layers.Refresh(regions, Array.Empty<OpenRA.Actor>(), topology, null, 10);
			Assert.That(layers.ThreatGroundHistory[1], Is.EqualTo(200f).Within(0.001f),
				"the EMA learned the sighting");

			// A bridge re-cut reshuffles every zone id: the published index space and its
			// averages die together rather than describe different ground under the same id.
			topology.Generation++;
			layers.Refresh(regions, Array.Empty<OpenRA.Actor>(), topology, null, 20);

			Assert.That(layers.Generation, Is.EqualTo(topology.Generation));
			Assert.That(layers.ThreatGroundHistory[1], Is.EqualTo(0f),
				"a retained history would read 160 (0.8*200), not 0");
			Assert.That(layers.ThreatGround[1], Is.EqualTo(0));
		}

		[Test]
		public void ZoneResourceCellsFeedInterest()
		{
			var topology = new FakeZoneTopology();
			topology.AddZone(Block(0, 0));
			topology.AddZone(Block(8, 0), resourceCells: 40);
			var regions = Zoned(topology);

			var layers = Layers();
			layers.Refresh(regions, Array.Empty<OpenRA.Actor>(), topology, null, 100);

			Assert.That(layers.Interest[1], Is.EqualTo(40), "a zone's static resource cells are interest");
			Assert.That(layers.Interest[0], Is.EqualTo(0));
		}

		[Test]
		public void ThreatSpreadsIntoNeighbourRegions()
		{
			var regions = Grid();
			var enemy = FakePlayer();
			var cells = new RegionMemory.Region[regions.CellCount];
			cells[3] = new RegionMemory.Region { ArmyValue = 1000, EverSeen = true, LastSeenTick = 100 };
			regions.SetRegions(enemy, cells);

			var layers = Layers();
			layers.Refresh(regions, Array.Empty<OpenRA.Actor>(), null, null, 100);

			// Fresh sighting: the seat keeps its full 1000; each grid neighbour (index 3's
			// left 2, right 4, down 11) publishes half of it — the remembered unit's reach
			// covers the ground past the boundary it holds.
			Assert.That(layers.ThreatGround[3], Is.EqualTo(1000));
			Assert.That(layers.ThreatGround[4], Is.EqualTo(500), "neighbour bleeds in SpreadPercent of the sighting");
			Assert.That(layers.ThreatGround[11], Is.EqualTo(500));
			Assert.That(layers.ThreatGround[0], Is.EqualTo(0), "a non-neighbour stays clear — one hop only");
		}

		[Test]
		public void SpreadFollowsZoneAdjacency()
		{
			var topology = new FakeZoneTopology();
			topology.AddZone(Block(0, 0), 0, 1);      // zone 0 neighbours zone 1
			topology.AddZone(Block(8, 0), 0, 0);      // zone 1 neighbours zone 0 only
			topology.AddZone(Block(16, 0), 0);        // zone 2 has no declared neighbours
			var regions = Zoned(topology);
			var enemy = FakePlayer();

			var cells = new RegionMemory.Region[regions.CellCount];
			cells[0] = new RegionMemory.Region { ArmyValue = 800, EverSeen = true, LastSeenTick = 100 };
			regions.SetRegions(enemy, cells);

			var layers = Layers();
			layers.Refresh(regions, Array.Empty<OpenRA.Actor>(), topology, null, 100);

			Assert.That(layers.ThreatGround[0], Is.EqualTo(800));
			Assert.That(layers.ThreatGround[1], Is.EqualTo(400), "spread crosses the declared zone adjacency");
			Assert.That(layers.ThreatGround[2], Is.EqualTo(0), "no adjacency, no bleed");
		}

		[Test]
		public void MatchesIndexSpaceTracksTheTriple()
		{
			var topology = new FakeZoneTopology();
			topology.AddZone(Block(0, 0));
			var regions = Zoned(topology);
			var layers = Layers();
			layers.Refresh(regions, Array.Empty<OpenRA.Actor>(), topology, null, 100);

			Assert.That(layers.MatchesIndexSpace(regions), Is.True);
			Assert.That(layers.MatchesIndexSpace(Grid()), Is.False, "grid-backed space is a different index space");
			Assert.That(layers.MatchesIndexSpace(null), Is.False);

			topology.Generation++;
			layers.Refresh(regions, Array.Empty<OpenRA.Actor>(), topology, null, 200);
			Assert.That(layers.MatchesIndexSpace(regions), Is.True, "both re-derived under the new generation");
		}
	}
}
