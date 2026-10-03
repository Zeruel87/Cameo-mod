#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.AS.Traits;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>
	/// Coarse spatial value memory over the map: one bucket per region per enemy player.
	/// Values persist while the region is dark and are overwritten when it is observed again
	/// (Fransbot-style "threat map", see docs/design/AI_FRANSBOT_RESEARCH.md §2).
	/// Published read-only on each BotSituation; consumers must not mutate.
	/// <para>
	/// ZG-c: the index space is either the fixed square grid (default, unchanged) or — when
	/// constructed with an <see cref="IBotZoneTopology"/> — that topology's zone ids, so a
	/// "region" becomes one chokepoint-bounded pocket of ground instead of an 8x8 cell block.
	/// <see cref="IndexOf"/> then answers <see cref="IBotZoneTopology.NearestRegionId"/>
	/// (gate/barrier cells fold into the nearest zone; unreachable answers are -1, never
	/// a valid index), <see cref="CenterOf"/> answers the zone's centroid cell, and
	/// adjacency comes from <see cref="NeighborsOf"/> rather than grid coordinates.
	/// </para>
	/// </summary>
	public sealed class RegionMemory
	{
		public sealed class Region
		{
			public int ArmyValue;
			public int DefenceValue;
			public int AntiAirValue;
			public int EconomyValue;

			// IM-1 (§3.3): remembered value of production/tech buildings — the non-economy
			// half of the influence layers' Interest read. Counted once even when a building
			// is both production and tech.
			public int ProductionTechValue;
			public int LastSeenTick;
			public bool EverSeen;

			// CA-2c (§12.6 rule 5): sieges that failed against this region.
			// Stamped per publish from MasterAiBotModule's durable store; the
			// snapshot is rebuilt every pass so the count itself lives there.
			public int FailedSiegeCount;
			public int LastFailedSiegeTick;
		}

		public readonly int CellSize;
		public readonly int Columns;
		public readonly int Rows;
		public readonly CPos Origin;
		readonly Dictionary<OpenRA.Player, Region[]> byEnemy = new();

		// ZG-c zone backing: when set, region indices are the topology's zone ids (positions
		// in IBotZoneTopology.Regions), not grid cells. The grid fields are still computed —
		// consumers must check ZoneBacked before reading geometry off Columns/Rows.
		readonly IBotZoneTopology zones;
		int zoneGeneration;
		CPos[] zoneCenters;

		public RegionMemory(Map map, int cellSize)
			: this(map.AllCells.TopLeft, map.AllCells.BottomRight, cellSize) { }

		/// <summary>Zone-backed memory: region indices are <paramref name="zoneTopology"/>'s region ids.</summary>
		public RegionMemory(Map map, int cellSize, IBotZoneTopology zoneTopology)
			: this(map.AllCells.TopLeft, map.AllCells.BottomRight, cellSize, zoneTopology) { }

		internal RegionMemory(CPos topLeft, CPos bottomRight, int cellSize)
		{
			CellSize = Math.Max(1, cellSize);
			Origin = topLeft;
			Columns = Math.Max(1, (bottomRight.X - Origin.X) / CellSize + 1);
			Rows = Math.Max(1, (bottomRight.Y - Origin.Y) / CellSize + 1);
		}

		internal RegionMemory(CPos topLeft, CPos bottomRight, int cellSize, IBotZoneTopology zoneTopology)
			: this(topLeft, bottomRight, cellSize)
		{
			zones = zoneTopology;
			zoneGeneration = zoneTopology?.Generation ?? -1;
		}

		/// <summary>
		/// True when region indices are a zone topology's region ids rather than grid cells.
		/// Anything else keyed by region id (the per-enemy arrays here, a caller's own caches)
		/// belongs to one (<see cref="ZoneBacked"/>, <see cref="Generation"/>) pair and must be
		/// dropped when that pair moves.
		/// </summary>
		public bool ZoneBacked => zones != null;

		/// <summary>
		/// The generation of the index space this memory currently answers in: the zone
		/// topology's adopted generation, constant 0 on the grid. A bridge re-cut bumps it —
		/// nothing says zone id 4 is the same ground it was.
		/// </summary>
		public int Generation
		{
			get
			{
				if (zones == null)
					return 0;

				SyncZoneGeneration();
				return zoneGeneration;
			}
		}

		public int CellCount
		{
			get
			{
				if (zones == null)
					return Columns * Rows;

				SyncZoneGeneration();
				return zones.Regions.Count;
			}
		}

		public IReadOnlyDictionary<OpenRA.Player, Region[]> ByEnemy
		{
			get
			{
				SyncZoneGeneration();
				return byEnemy;
			}
		}

		public int IndexOf(CPos cell)
		{
			if (zones != null)
			{
				SyncZoneGeneration();

				// Zone ids only exist on passable ground: a cell on a gate corridor, a ramp
				// barrier or a wall folds into the nearest region a few cells out, so threat
				// sitting on a chokepoint still lands in a region's memory instead of dropping
				// out of the index space. -1 means nothing was in reach at all (deep water,
				// off-map) — callers must treat it as "no region", not index with it.
				return zones.NearestRegionId(cell);
			}

			var col = Math.Clamp((cell.X - Origin.X) / CellSize, 0, Columns - 1);
			var row = Math.Clamp((cell.Y - Origin.Y) / CellSize, 0, Rows - 1);
			return row * Columns + col;
		}

		public CPos CenterOf(int index)
		{
			if (zones != null)
			{
				SyncZoneGeneration();
				var centers = zoneCenters ??= ZoneCenters();
				return index >= 0 && index < centers.Length ? centers[index] : Origin;
			}

			var row = index / Columns;
			var col = index - row * Columns;
			return new CPos(Origin.X + col * CellSize + CellSize / 2, Origin.Y + row * CellSize + CellSize / 2);
		}

		/// <summary>
		/// Region indices a path may step to from <paramref name="index"/>: the zone's
		/// <see cref="Zone.AdjacentRegionIds"/> when zone-backed, the 4-connected grid
		/// neighbours otherwise (in the same left/right/up/down order the router's old
		/// inline loop used). This is the adjacency-as-data seam: consumers walking
		/// region-to-region read it instead of re-deriving neighbours from grid coordinates.
		/// </summary>
		public IReadOnlyList<int> NeighborsOf(int index)
		{
			if (zones != null)
			{
				SyncZoneGeneration();
				var list = zones.Regions;
				return index >= 0 && index < list.Count ? list[index].AdjacentRegionIds : Array.Empty<int>();
			}

			var row = index / Columns;
			var col = index - row * Columns;
			var neighbors = new List<int>(4);
			if (col > 0)
				neighbors.Add(index - 1);
			if (col < Columns - 1)
				neighbors.Add(index + 1);
			if (row > 0)
				neighbors.Add(index - Columns);
			if (row < Rows - 1)
				neighbors.Add(index + Columns);
			return neighbors;
		}

		internal void SetRegions(OpenRA.Player enemy, Region[] regions)
		{
			SyncZoneGeneration();
			byEnemy[enemy] = regions;
		}

		public int KnownRegionCount(OpenRA.Player enemy)
		{
			SyncZoneGeneration();
			return byEnemy.TryGetValue(enemy, out var regions) ? CountKnown(regions) : 0;
		}

		internal static int CountKnown(Region[] regions)
		{
			var count = 0;
			foreach (var region in regions)
				if (region != null && region.EverSeen)
					count++;
			return count;
		}

		// A bridge re-cut re-shuffles every zone id, so per-zone memory built against the old
		// cut must not alias onto the new ground: the per-enemy arrays and cached centres are
		// dropped wholesale, and SetRegions re-derives them from remembered actors on the next
		// snapshot anyway. (A zone that no longer exists simply loses its remembered values —
		// honest fog semantics, not a salvage job.) Grid-backed memories never reach here.
		void SyncZoneGeneration()
		{
			if (zones == null || zones.Generation == zoneGeneration)
				return;

			zoneGeneration = zones.Generation;
			zoneCenters = null;
			byEnemy.Clear();
		}

		// The representative cell of every zone — the member nearest its geometric centre —
		// so a waypoint or visibility probe lands on real ground of that zone rather than a
		// bounding-box middle that can sit on water or a cliff.
		CPos[] ZoneCenters()
		{
			var list = zones.Regions;
			var centers = new CPos[list.Count];
			for (var i = 0; i < list.Count; i++)
				centers[i] = list[i].Cells.Length > 0 ? TacticalMapBotModule.Centroid(list[i].Cells) : Origin;
			return centers;
		}
	}

	/// <summary>
	/// One remembered enemy actor: position, value and the classification the profile needs,
	/// captured at the last sighting. Stored per ActorID so a unit seen somewhere new moves
	/// its value instead of counting twice.
	/// </summary>
	internal sealed class ObservedActor
	{
		// The type, for consumers that reason per unit type (adaptive counter-production).
		public ActorInfo Info;
		public uint ActorID;
		public CPos Location;
		public int LastSeenTick;
		public int Value;
		public bool Building;
		public bool BaseBuilding;
		public bool Combat;
		public bool Defence;
		public bool Tech;
		public bool Production;
		public bool Refinery;
		public bool Harvester;
		public bool Cloaked;
		public bool Aircraft;
		public bool AntiAir;
		public bool Infantry;
		public bool Vehicle;
		public bool Naval;

		// CN3: the actor carries an enabled-by-default DetectCloaked — the
		// stealth doctrine's remembered detector coverage. DetectorRangeCells is
		// the observed type's longest such range in cells (public ruleset data
		// for a seen type — fog-honest).
		public bool Detector;
		public int DetectorRangeCells;
	}

	/// <summary>
	/// The bot player's fogged picture of the enemy: a per-enemy last-seen table fed only by
	/// what the player can actually see (live actors passing CanBeViewedByPlayer, plus the
	/// engine's FrozenActorLayer which already remembers fogged buildings).
	/// Unsynced; read and written only from IBotTick.
	/// </summary>
	internal sealed class BotFogMemory
	{
		static readonly BitSet<TargetableType> AirTargetTypes = new("Air");

		readonly OpenRA.Player viewer;
		readonly MasterAiBotModuleInfo info;
		readonly Dictionary<OpenRA.Player, Dictionary<uint, ObservedActor>> tables = new();

		public BotFogMemory(OpenRA.Player viewer, MasterAiBotModuleInfo info)
		{
			this.viewer = viewer;
			this.info = info;
		}

		/// <summary>
		/// Refresh the enemy's table from the actors of theirs visible this tick and the
		/// frozen-actor layer, then forget anything contradicted by current visibility
		/// (a remembered cell now visible without the actor) or the unit timeout.
		/// Returns the number of enemy harvesters visible right now.
		/// </summary>
		public int Observe(OpenRA.Player enemy, IEnumerable<Actor> enemyActors, int tick)
		{
			var table = Table(enemy);
			var visibleIds = new HashSet<uint>();
			var visibleHarvesters = 0;
			foreach (var actor in enemyActors)
			{
				if (!actor.Info.HasTraitInfo<IOccupySpaceInfo>() || !actor.CanBeViewedByPlayer(viewer))
					continue;

				visibleIds.Add(actor.ActorID);
				var record = Classify(actor.Info, actor.ActorID, actor.Location, actor.GetEnabledTargetTypes(), tick, info);
				record.Cloaked = actor.Info.HasTraitInfo<CloakInfo>();
				table[actor.ActorID] = record;
				if (record.Harvester)
					visibleHarvesters++;
			}

			var frozen = viewer.FrozenActorLayer;
			if (frozen != null)
			{
				foreach (var fa in frozen.FrozenActorsInRegion(viewer.World.Map.AllCells))
				{
					if (!fa.IsValid || fa.Owner != enemy || table.ContainsKey(fa.ID))
						continue;

					var record = Classify(fa.Info, fa.ID, viewer.World.Map.CellContaining(fa.CenterPosition), fa.TargetTypes, tick, info);
					record.Cloaked = fa.Info.HasTraitInfo<CloakInfo>();
					table[fa.ID] = record;
				}
			}

			var shroud = viewer.Shroud;
			List<uint> forgotten = null;
			foreach (var pair in table)
			{
				if (visibleIds.Contains(pair.Key))
					continue;

				var record = pair.Value;
				if (shroud.IsVisible(record.Location) ||
					(!record.Building && tick - record.LastSeenTick > info.ObservationTimeoutTicks))
				{
					forgotten ??= new List<uint>();
					forgotten.Add(pair.Key);
				}
			}

			if (forgotten != null)
				foreach (var id in forgotten)
					table.Remove(id);

			return visibleHarvesters;
		}

		public IReadOnlyCollection<ObservedActor> Remembered(OpenRA.Player enemy)
		{
			return Table(enemy).Values;
		}

		// CN3: the remembered DetectCloaked carriers across every enemy table,
		// aged by their last sighting — the detector coverage the stealth squads
		// route around. `Enemy` is the table's owner. Sightings older than
		// maxAgeTicks are treated as gone; empty means none observed, never
		// "no detectors exist".
		internal IEnumerable<BotKnownDetector> KnownDetectors(int maxAgeTicks)
		{
			var tick = viewer.World.WorldTick;
			foreach (var (enemy, table) in tables)
				foreach (var seen in table.Values)
					if (seen.Detector && seen.DetectorRangeCells > 0 && tick - seen.LastSeenTick <= maxAgeTicks)
						yield return new BotKnownDetector(seen.Location, seen.DetectorRangeCells, seen.LastSeenTick, enemy);
		}

		Dictionary<uint, ObservedActor> Table(OpenRA.Player enemy)
		{
			if (!tables.TryGetValue(enemy, out var table))
				tables[enemy] = table = new Dictionary<uint, ObservedActor>();
			return table;
		}

		internal static ObservedActor Classify(ActorInfo actorInfo, uint actorID, CPos location,
			BitSet<TargetableType> targetTypes, int tick, MasterAiBotModuleInfo info)
		{
			var building = actorInfo.HasTraitInfo<BuildingInfo>();
			var hasAttack = actorInfo.HasTraitInfo<AttackBaseInfo>();

			// Only traits enabled by default count: a condition-gated detector
			// (RequiresCondition unmet at rules load) may never come online, and
			// the memory cannot observe condition state through fog anyway.
			var detectorRanges = actorInfo.TraitInfos<DetectCloakedInfo>()
				.Where(t => t.EnabledByDefault)
				.Select(t => (t.Range.Length + 1023) / 1024)
				.ToList();
			return new ObservedActor
			{
				Info = actorInfo,
				ActorID = actorID,
				Location = location,
				LastSeenTick = tick,
				Value = ObservedValue(actorInfo.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0, building && hasAttack,
					actorInfo.TraitInfoOrDefault<GarrisonableInfo>()?.MaxWeight ?? 0, info.GarrisonOccupantValue),
				Building = building,
				BaseBuilding = building && actorInfo.HasTraitInfo<BaseBuildingInfo>(),
				Combat = hasAttack && !building && !actorInfo.HasTraitInfo<HarvesterInfo>(),
				Defence = building && (hasAttack || targetTypes.Overlaps(info.DefenceTargetTypes)),
				Tech = building && actorInfo.HasTraitInfo<ProvidesPrerequisiteInfo>(),
				Production = building && actorInfo.HasTraitInfo<ProductionInfo>(),
				Refinery = building && actorInfo.HasTraitInfo<RefineryInfo>(),
				Harvester = actorInfo.HasTraitInfo<HarvesterInfo>(),
				Aircraft = actorInfo.HasTraitInfo<AircraftInfo>(),
				AntiAir = HasAntiAirWeapon(actorInfo),
				Infantry = targetTypes.Overlaps(info.InfantryTargetTypes),
				Vehicle = targetTypes.Overlaps(info.VehicleTargetTypes),
				Naval = targetTypes.Overlaps(info.NavalTargetTypes),
				Detector = detectorRanges.Count > 0,
				DetectorRangeCells = detectorRanges.Count > 0 ? detectorRanges.Max() : 0
			};
		}

		// AI_ARCHITECTURE §12.12: an enemy-held garrisonable building is occupied (ChangeOwnerOnGarrisoner), and the
		// civilian houses carry no Valued cost, so pricing them by their own cost made a garrison worth 0 to the risk
		// gate and infantry were fed into it one by one. Price the garrison instead: the building's capacity times a
		// rules constant, never the real passenger list, which the observer cannot see.
		internal static int ObservedValue(int valuedCost, bool armedBuilding, int garrisonMaxWeight, int occupantValue)
		{
			if (valuedCost > 0 || !armedBuilding || garrisonMaxWeight <= 0 || occupantValue <= 0)
				return valuedCost;

			return garrisonMaxWeight * occupantValue;
		}

		static bool HasAntiAirWeapon(ActorInfo actorInfo)
		{
			foreach (var armament in actorInfo.TraitInfos<ArmamentInfo>())
				if (armament.WeaponInfo != null && armament.WeaponInfo.IsValidTarget(AirTargetTypes))
					return true;
			return false;
		}
	}
}
