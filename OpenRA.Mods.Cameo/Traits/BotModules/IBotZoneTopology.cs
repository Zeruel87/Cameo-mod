#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 *
 * Written for the ZG zone-graph port (crystallized-nexus CNTacticalMapBotModule,
 * GPLv3, Copyright (c) The Crystallized Nexus Developers).
 */
#endregion

using System.Collections.Generic;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>
	/// What kind of terrain feature a <see cref="ZoneChokepoint"/> marks. First letter is the
	/// overlay label (P/R/B), matching the donor's convention.
	/// </summary>
	public enum ZoneChokepointType { Passage, Ramp, Bridge }

	/// <summary>
	/// One detected access point in the static topology: the representative cell, the
	/// pathfinder abstract domain it sits in, its kind and a base defensive weight.
	/// (Port of the donor's CNChokepoint.)
	/// </summary>
	public sealed class ZoneChokepoint
	{
		public readonly CPos Cell;
		public readonly uint Domain;
		public readonly ZoneChokepointType Type;
		public readonly int BaseWeight;

		public ZoneChokepoint(CPos cell, uint domain, ZoneChokepointType type, int baseWeight)
		{
			Cell = cell;
			Domain = domain;
			Type = type;
			BaseWeight = baseWeight;
		}
	}

	/// <summary>
	/// A resolved wall-to-wall corridor through a chokepoint: the full passable width the
	/// region cut is made along. <see cref="Zone.GateCorridorIndices"/> indexes into the
	/// module's corridor list. (Port of the donor's CNSealableCorridor; renamed because the
	/// "sealable" use — can it be plugged by one wall line — is ZG-b territory logic, while
	/// the corridor itself is a terrain fact.)
	/// </summary>
	public sealed class ZoneGateCorridor
	{
		public readonly CPos Center;

		/// <summary>True when the wall line sealing this corridor runs along the X axis (cells vary in X).</summary>
		public readonly bool WallRunsHorizontal;

		public readonly CPos[] Cells;

		public int Width => Cells.Length;

		public ZoneGateCorridor(CPos center, bool wallRunsHorizontal, CPos[] cells)
		{
			Center = center;
			WallRunsHorizontal = wallRunsHorizontal;
			Cells = cells;
		}
	}

	/// <summary>
	/// A contiguous run of passable cells on the edge of a player's believed territory: a way in.
	/// <para>
	/// The rest of that edge is cliff, water or map edge - wall the terrain provides for free. Only the
	/// doors have to be held, which is what lets defence be planned as a line rather than as a scatter
	/// of independent points. (Port of the donor's CNTerritoryDoor.)
	/// </para>
	/// </summary>
	public sealed class ZoneTerritoryDoor
	{
		public readonly CPos Center;
		public readonly CPos[] Cells;

		/// <summary>Direction leading out of the territory, averaged over the run.</summary>
		public readonly CVec Outward;

		/// <summary>Reachable ground behind the door, capped. What passing through it actually opens up.</summary>
		public readonly int GroundBeyond;

		public int Width => Cells.Length;

		public ZoneTerritoryDoor(CPos center, CPos[] cells, CVec outward, int groundBeyond)
		{
			Center = center;
			Cells = cells;
			Outward = outward;
			GroundBeyond = groundBeyond;
		}
	}

	/// <summary>
	/// A passable cliff-edge cell that overlooks reachable lower ground (height advantage,
	/// natural wall). (Port of the donor's CNHighGroundEdge.)
	/// </summary>
	public readonly struct ZoneHighGroundEdge
	{
		public readonly CPos Cell;
		public readonly CVec Outward;
		public readonly int HeightLevels;

		public ZoneHighGroundEdge(CPos cell, CVec outward, int heightLevels)
		{
			Cell = cell;
			Outward = outward;
			HeightLevels = heightLevels;
		}
	}

	/// <summary>
	/// A weighted position a defence should cover. (Port of the donor's
	/// CNBaseBuilderBotModule.DefensePlacementThreat - freestanding here because the Cameo base
	/// builder is not part of the ZG-b port's dependency set.)
	/// </summary>
	public readonly struct ZoneDefenseThreat
	{
		public readonly CPos Location;
		public readonly int Weight;

		public ZoneDefenseThreat(CPos location, int weight)
		{
			Location = location;
			Weight = weight;
		}
	}

	/// <summary>
	/// One cell of the map's shape: a connected pocket of ground bounded by chokepoint
	/// corridors and cliff ramps, independent of who (if anyone) holds it. Computed once,
	/// shared between bots via the static registry in TacticalMapBotModule.
	/// (Port of the donor's CNRegion.)
	/// </summary>
	public sealed class Zone
	{
		/// <summary>Position of this zone in <see cref="IBotZoneTopology.Regions"/>.</summary>
		public readonly int Id;

		public readonly CPos[] Cells;

		/// <summary>Indices into the module's gate-corridor list for the gates bounding this zone.</summary>
		public readonly int[] GateCorridorIndices;

		/// <summary>Ids of zones sharing a barrier cell with this one.</summary>
		public readonly int[] AdjacentRegionIds;

		/// <summary>Cells carrying a resource type - a rough size of what this zone's ground is worth.</summary>
		public readonly int ResourceCellCount;

		/// <summary>Passable, non-ramp cells - a rough size of how much of this zone can be built on.</summary>
		public readonly int BuildableCellCount;

		/// <summary>Cells with a non-zone neighbour (a gate, a wall, the map edge) - the outline, for drawing.</summary>
		public readonly CPos[] BoundaryCells;

		public int Size => Cells.Length;

		public Zone(int id, CPos[] cells, int[] gateCorridorIndices, int[] adjacentRegionIds,
			int resourceCellCount, int buildableCellCount, CPos[] boundaryCells)
		{
			Id = id;
			Cells = cells;
			GateCorridorIndices = gateCorridorIndices;
			AdjacentRegionIds = adjacentRegionIds;
			ResourceCellCount = resourceCellCount;
			BuildableCellCount = buildableCellCount;
			BoundaryCells = boundaryCells;
		}
	}

	/// <summary>
	/// The static terrain topology every bot reads: the map's passable ground cut into
	/// <see cref="Zone"/> regions by the chokepoint corridors (plus cliff ramps) that gate it.
	/// <para>
	/// Terrain-only and fog-honest by construction: derived from the map's tiles, heights and the
	/// hierarchical pathfinder's connectivity domains, never from enumerating actors. Implemented
	/// by <c>TacticalMapBotModule</c>, built once per (world, locomotor) and shared between bots.
	/// </para>
	/// <para>
	/// Consumers are the ZG-c stack (<c>BotFogMemory</c>, <c>RegionRouter</c>, <c>BotSituation</c>):
	/// they locate the module via <c>player.PlayerActor.Trait&lt;TacticalMapBotModule&gt;()</c>.
	/// On a non-host client (or a replay) the topology is never built and every answer is empty.
	/// </para>
	/// </summary>
	public interface IBotZoneTopology
	{
		/// <summary>
		/// The map's regions — connected pockets of passable ground bounded by chokepoint corridors
		/// and cliff ramps. Unowned terrain facts; ids are positions in this list and are invalidated
		/// whenever <see cref="Generation"/> changes (a bridge re-cut reshuffles them).
		/// </summary>
		IReadOnlyList<Zone> Regions { get; }

		/// <summary>The detected chokepoints (passages, cliff ramps, bridges) that gate the regions.</summary>
		IReadOnlyList<ZoneChokepoint> Chokepoints { get; }

		/// <summary>Region id at a cell, or -1 if it is a gate/barrier cell or outside any region.</summary>
		int RegionIdAt(CPos cell);

		/// <summary>
		/// The region at a cell, or the nearest one a few cells out when the cell itself sits on a
		/// gate corridor or barrier and belongs to no region. This is how a caller lands SOMETHING:
		/// threat remembered on a bridge or ramp counts in an adjacent zone rather than dropping
		/// out of the index space entirely. -1 when nothing region-like is in reach (deep water,
		/// off-map) — callers must treat that as "no region", never index with it.
		/// </summary>
		int NearestRegionId(CPos cell);

		/// <summary>
		/// The generation this bot has ADOPTED, bumped whenever the shared topology is re-cut
		/// (a destroyed or repaired bridge). Anything cached per region id must be dropped when this
		/// changes — after a re-cut nothing says id 4 is the same ground it was. -1 while unbuilt.
		/// </summary>
		int Generation { get; }

		/// <summary>
		/// Whether ground units can cross a cell, by the same locomotor the chokepoints and regions
		/// were scanned with — so a caller walks the map the way these answers were derived.
		/// </summary>
		bool IsPassableCell(CPos cell);

		// ---- ZG-b: per-bot BELIEF over the shared terrain ----
		// Unlike the members above, these answers come from what this one bot has seen and
		// remembered (own buildings + BotFogMemory sightings). They are not shared, they can be
		// stale, and "unknown" is a normal answer — never read them as the truth on the ground.

		/// <summary>
		/// The player this bot believes dominates a region, or null when unclaimed/contested/unknown.
		/// Fog-honest: tallied from the bot's own buildings plus its REMEMBERED enemy buildings —
		/// an enemy base never scouted claims nothing here even if it stands. May be stale (refreshed
		/// on an interval). Region ids are positions in <see cref="Regions"/> and are invalidated
		/// whenever <see cref="Generation"/> changes.
		/// </summary>
		OpenRA.Player RegionOwner(int regionId);

		/// <summary>
		/// The ways into this bot's believed territory — a contiguous run of passable edge cells each.
		/// Belief (fog memory decides where the claim raced to), possibly stale; empty until the
		/// territory refresh has run or while the bot holds nothing.
		/// </summary>
		IReadOnlyList<ZoneTerritoryDoor> TerritoryDoors { get; }

		/// <summary>
		/// The ground this bot believes it holds: cells its claim won in the own-vs-remembered-enemy
		/// building race around the gate corridors. Belief, possibly stale.
		/// </summary>
		IReadOnlyCollection<CPos> Territory { get; }

		/// <summary>Whether a cell is inside this bot's believed territory claim.</summary>
		bool IsInTerritory(CPos cell);
	}
}
