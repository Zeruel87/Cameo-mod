#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 *
 * Ported from the Crystallized Nexus CNTacticalMapBotModule (crystallized-nexus
 * commit 30cf70a, GPLv3, Copyright (c) The Crystallized Nexus Developers).
 *
 * ZG-a scope: STATIC TOPOLOGY — passability snapshot, chokepoints
 * (passages / cliff ramps / bridges), the region cut gated by them, the
 * cell -> region-id lookup, and the shared Generation counter bumped on
 * bridge re-cuts.
 *
 * ZG-b scope: the per-bot BELIEF on top — the incremental 'useful'
 * chokepoint / sealable-corridor / high-ground refresh cadences, the
 * territory claiming race, door detection, and the region-ownership tally.
 * The donor ran all of this OMNISCIENT (live world.Actors scans); here every
 * enemy input comes from BotFogMemory via the master AI's situation
 * (Situation.Remembered), so a never-scouted enemy contributes nothing.
 * Because each bot sees differently, ownership/territory/doors are PER-BOT
 * state on this module — the donor parked RegionOwners on the shared
 * topology, which only works when every bot computes the identical answer.
 *
 * ZG-c scope: NearestRegionId (a gate/barrier cell's nearest region) moved onto
 * IBotZoneTopology so RegionMemory's zone backing can fold unzoned cells into a
 * region's memory instead of dropping them.
 *
 * Adaptations: CNChokepoint/CNRegion/CNSealableCorridor -> ZoneChokepoint/Zone/
 * ZoneGateCorridor (see IBotZoneTopology.cs); MaxDoorWidth -> MaxGateWidth
 * (its only ZG-a use is bounding the corridor the region cut resolves to);
 * CNBotLog -> CAAIUtils.BotDebug; the CNDestroyableCliff bridge-watch is
 * dropped — Cameo has no destroyable-cliff trait, so only bridge cells are
 * watched for passability changes. No CN engine patches required: the Cameo
 * engine already exposes PathFinder.GetOverlayDataForLocomotor returning the
 * same (abstract graph, abstract domains) pair the donor consumes.
 */
#endregion

using System;
using System.Collections.Frozen;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;
using CAAIUtils = OpenRA.Mods.CA.AIUtils;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	// The terrain-only topology (chokepoints + connectivity), shared by all bots on the same map+locomotor so the
	// expensive scan runs once. Base-relative and belief results (useful set, high-ground, corridors, territory,
	// doors, region owners) stay per bot on the module - under fog they differ between bots.
	public sealed class SharedZoneTopology
	{
		public readonly List<ZoneChokepoint> Chokepoints = [];
		public readonly List<CPos> BridgeWatchCells = [];
		public CellLayer<bool> Passability;
		public IReadOnlyDictionary<CPos, uint> AbstractDomains;
		public CPos[] NodeCells = [];

		// A fold over the watched bridge cells, not a yes/no - see CurrentBridgeSignature.
		public int LastBridgeSignature;
		public int Generation;

		// The map's shape, cut once by the same chokepoints that gate the territory walk - not anyone's
		// claim, a terrain fact every bot can read regardless of who (if anyone) owns it.
		public readonly List<Zone> Regions = [];
		public CellLayer<int> RegionIdByCell;

		// The corridors Zone.GateCorridorIndices index into. Kept because the indices are otherwise
		// unreadable: the list was local to BuildRegions and thrown away, so a region could say it had
		// three doors and nothing could ask how wide any of them was.
		public readonly List<ZoneGateCorridor> RegionGateCorridors = [];

		// What the cut actually ran along: resolved chokepoint corridors plus cliff ramps. Kept because
		// "the regions are wrong here" always turns out to mean "the barrier has a hole here", and a hole
		// is not visible from the region outlines alone - they simply run past it.
		public HashSet<CPos> RegionBarrier = [];

		// ZG-b divergence: the donor parked the periodically-refreshed region-ownership tally here
		// (RegionOwners / NextOwnershipRefreshTick on CNSharedTopology). That only works because the
		// donor is omniscient - every bot's tally is identical. Under fog each bot believes
		// differently, so ownership (like territory and doors) is per-bot state on the module.
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Cartographs the map once at game start (and on bridge changes) to find chokepoints (bridges, cliff ramps,",
		"narrow land passages) and cut the map into regions (IBotZoneTopology).",
		"Reads the hierarchical pathfinder's abstract graph for connectivity domains.")]
	public class TacticalMapBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Locomotor name(s) used to analyse ground access. The first one present is used.",
			"Should be the bot's main ground combat locomotor (e.g. tracked). Empty = first available ground locomotor.")]
		public readonly FrozenSet<string> TopologyLocomotors = FrozenSet<string>.Empty;

		[Desc("Maximum number of chokepoints returned per defensive placement query.")]
		public readonly int MaxTopologyHotspots = 6;

		[Desc("Only chokepoints within this many cells of the query reference are considered.")]
		public readonly int TopologyMaxDistance = 28;

		[Desc("Base weight of a chokepoint that is a bridge (the strongest natural funnel).")]
		public readonly int BridgeWeight = 220;

		[Desc("Base weight of a chokepoint that is a cliff ramp / height transition.")]
		public readonly int RampWeight = 170;

		[Desc("Base weight of a chokepoint that is a narrow land passage.")]
		public readonly int PassageWeight = 120;

		[Desc("Ticks between re-checks of bridge-chokepoint passability. A change triggers a rebuild.")]
		public readonly int TopologyRecheckInterval = 50;

		[Desc("Minimum ticks between recomputing the 'useful' chokepoint set (reachable + leads somewhere). Higher =",
			"cheaper; this is queried very often by the base builder so it is throttled rather than computed per query.")]
		public readonly int UsefulRefreshInterval = 125;

		[Desc("How many chokepoints to evaluate per tick when refreshing the 'useful' set or sealable corridors. The",
			"flood per chokepoint is expensive, so this is spread over several ticks. Lower = smoother but slower to",
			"update.")]
		public readonly int UsefulChunkSize = 3;

		[Desc("How many candidate cells to evaluate per tick when refreshing high-ground edges. A single cell check",
			"is cheap (a couple of height/passability lookups), so this can be much larger than UsefulChunkSize",
			"without a per-tick cost - keeps a full-radius scan from taking hundreds of ticks to complete.")]
		public readonly int HighGroundChunkSize = 80;

		[Desc("Optional long fallback recompute interval in ticks. 0 disables it (rely on bridge-change detection).")]
		public readonly int RecomputeInterval = 0;

		[Desc("Skip a base-relative refresh cycle (high-ground/useful-chokepoints/sealable-corridors) if the base",
			"reference has moved less than this many cells since the last completed scan - the base-building",
			"centroid drifts a little with every building added or lost, but a real relocation (new main base,",
			"lost conyard) moves it much further than that.")]
		public readonly int BaseMoveThreshold = 8;

		[Desc("Same idea as BaseMoveThreshold, but for the enemy building count: skip the refresh cycle unless it",
			"has changed by more than this many buildings since the last completed scan. During active combat the",
			"count churns constantly from individual losses/builds that don't meaningfully change reachability.",
			"ZG-b: counts REMEMBERED enemy buildings (fog memory), not live ones.")]
		public readonly int EnemyBuildingCountTolerance = 2;

		[Desc("Radius (cells) around the base reference scanned for high-ground cliff edges.")]
		public readonly int HighGroundScanRadius = 18;

		[Desc("Terrain height at which no height advantage is granted (matches the donor's",
			"HeightAdvantageBonus.BaseHeight convention).")]
		public readonly int HighGroundBaseHeight = 2;

		[Desc("A chokepoint is only considered sealable with a wall if its passable corridor is at most this wide (cells).")]
		public readonly int ChokepointSealMaxWidth = 5;

		[Desc("Ignore chokepoints in regions (domains) with fewer abstract graph nodes than this — tiny isolated",
			"areas like an unreachable mesa top are not tactically meaningful.")]
		public readonly int MinDomainNodes = 4;

		[Desc("Maximum width (cells) of a passable corridor still considered a Passage chokepoint. Wider gaps are open",
			"terrain, not bottlenecks.")]
		public readonly int MaxPassageWidth = 8;

		[Desc("Both sides of a Passage must flood to at least this many cells, else it is a dead end / non-separating",
			"gap and is discarded.")]
		public readonly int MinPassageSideCells = 24;

		[Desc("Merge chokepoints that end up within this many cells of each other (cuts duplicate markers/clutter).")]
		public readonly int ChokepointMergeRadius = 5;

		[Desc("How far (cells) a ramp seal may grow away from the cliff it is anchored at. A ramp is a cut",
			"through a cliff and is at most about this wide; without a bound the run of slope tiles it grows",
			"along is connected across half a rolling map and the seal swallows the map with it. Both edges",
			"of a wide ramp seed the growth, so a ramp up to roughly twice this wide still closes.")]
		public readonly int RampSealMaxSpread = 8;

		[Desc("Regions smaller than this (cells) are merged into their larger neighbour by dropping the",
			"barrier between them, repeated until no undersized region has anywhere left to merge into.",
			"A chokepoint can be a perfectly genuine bottleneck and still be far too minor a wrinkle to",
			"deserve a region of its own - a coastline pinched every few cells came out as a chain of",
			"15/35/47-cell regions, which is not how anybody reads that ground. 0 disables merging.")]
		public readonly int MinRegionSize = 60;

		[Desc("The coarse chokepoint cell is snapped to the genuinely narrowest crossing within this radius (cells).")]
		public readonly int ChokepointSnapRadius = 3;

		[Desc("Widest a gap may be and still resolve to a gate corridor between two regions. Past this the terrain",
			"is not pinching anything. (Donor's MaxDoorWidth — renamed: doors are ZG-b, the width bound itself is",
			"needed here because it is what the region cut resolves along.)")]
		public readonly int MaxGateWidth = 14;

		[Desc("Fallback minimum number of passable cells beyond a chokepoint before treating it as a real access.",
			"Used only when no enemy buildings are remembered; otherwise the far side must contain one.")]
		public readonly int MinimumChokepointBeyondCells = 96;

		[Desc("Hard cap on cells visited by the per-chokepoint 'leads somewhere' flood-fill, regardless of whether",
			"enemy buildings are known. Without this, a chokepoint whose reachable region contains no remembered",
			"enemy building floods the ENTIRE region before giving up - unbounded on an open map. Treated as",
			"'not confirmed' if hit.")]
		public readonly int FloodFillCellCap = 1500;

		[Desc("Hard cap on cells visited while working out which ground belongs to whom. A safety net, not",
			"a tuning knob: it counts every claim in the same walk, so at 5000 two territories of 2900 and",
			"2200 cells hit it between them and the walk stopped with most of the map - and nearly every",
			"chokepoint on it - never reached. Sized to cover a whole map instead.")]
		public readonly int TerritoryCellCap = 40000;

		[Desc("How far from its own buildings a player's territory reaches while no enemy building is known.",
			"Once one is remembered, the split is decided by which side reaches a cell in fewer steps instead.")]
		public readonly int TerritoryUnopposedRadius = 40;

		[Desc("Ticks between territory rebuilds. Also gated on the base having moved or the remembered enemy",
			"building count having changed, so a settled game recomputes almost never.")]
		public readonly int TerritoryRefreshInterval = 250;

		[Desc("Ticks between region-ownership rescans. ZG-b: ownership is PER-BOT belief (fog memory), not the",
			"donor's shared tally - each bot tallies own buildings plus remembered enemy ones on its own clock.")]
		public readonly int RegionOwnershipRefreshInterval = 250;

		[Desc("Cells counted behind a door before the measurement stops. A door opening onto more ground than",
			"this is simply 'wide open' - the exact figure stops mattering well before the cap.")]
		public readonly int DoorBeyondCellCap = 1200;

		[Desc("Doors narrower than this are ignored: a one-cell gap in a cliff that units barely thread",
			"through is not what a defence line is planned around.")]
		public readonly int MinDoorWidth = 1;

		[Desc("Cells the flood behind a door must reach before it counts as a real way in. A pinch that",
			"opens onto almost nothing is a dead end, not something worth anchoring a defence at. Same",
			"figure as MinimumChokepointBeyondCells - both are the same question, 'is what's behind this",
			"real', just asked for a different feature.")]
		public readonly int MinDoorGroundBeyond = 96;

		[Desc("Doors within this many cells of a wider door are folded into it instead of standing on",
			"their own. A single gap scanned at a couple of slightly different points, or two real gaps",
			"a few cells apart, is one way in to a human - not several lined up in a row.")]
		public readonly int DoorMergeRadius = 8;

		[Desc("Weight given to a fully open territory door (GroundBeyond at DoorBeyondCellCap), scaled down",
			"for narrower ones but never below PassageWeight - MinDoorGroundBeyond already means 'this is a",
			"real way in', so the weakest qualifying door still has to compete like one. Same scale as",
			"BridgeWeight so a door-sourced and a chokepoint-sourced threat compose identically wherever",
			"both feed the same score.")]
		public readonly int DoorDefenseWeight = 200;

		[Desc("Cells of door width that one defence structure is taken to cover. A door counts as held once",
			"1 + Width/this many stand near it, so a wide gap asks for more than a narrow one instead of",
			"both being answered by the single turret the old boolean check was satisfied with. Its weight",
			"falls off as that count is filled, which is what moves the budget on to the next door.")]
		public readonly int DoorCellsPerDefense = 4;

		[Desc("How far behind a door (cells, opposite Outward) the kill-zone wall band sits. Bigger than the",
			"3-cell GetDoorDefenseAnchors offset on purpose, so the already-anchored defence ends up INSIDE",
			"the walled zone, not sitting on its edge.")]
		public readonly int DoorKillZoneRadius = 7;

		public override object Create(ActorInitializer init) { return new TacticalMapBotModule(init.Self, this); }
	}

	public class TacticalMapBotModule : ConditionalTrait<TacticalMapBotModuleInfo>, IBotTick, IWorldLoaded, IBotZoneTopology
	{
		readonly World world;
		readonly OpenRA.Player player;

		PathFinder pathFinder;
		Locomotor locomotor;

		readonly List<ZoneChokepoint> chokepoints = [];
		IReadOnlyDictionary<CPos, uint> abstractDomains;
		CPos[] nodeCells = [];

		// Region shape (Cells/GateCorridorIndices/AdjacentRegionIds/counts) is small and copied per-instance
		// like chokepoints; RegionIdByCell is heavy like Passability, so it is only ever referenced, never copied.
		readonly List<Zone> regions = [];
		readonly List<ZoneGateCorridor> regionGateCorridors = [];
		CellLayer<int> regionIdByCell;
		HashSet<CPos> regionBarrier = [];
		IResourceLayer resourceLayer;

		// The terrain-only topology is built once per (world, locomotor) and shared across all bots. The first bot to
		// build publishes here; the rest adopt it. Generation bumps on a (shared) bridge-change rebuild.
		static readonly ConditionalWeakTable<World, Dictionary<string, SharedZoneTopology>> Registries = [];
		SharedZoneTopology shared;
		int sharedGeneration = -1;

		// True once the topology has been built. Exposed so a consumer can read without triggering a build.
		public bool TopologyReady { get; private set; }

		// Passability signature of bridge chokepoints, used to detect destroyed/repaired bridges cheaply.
		readonly List<CPos> bridgeWatchCells = [];
		int lastBridgeSignature;
		int recheckTick;
		int recomputeTick;

		// --- ZG-b: per-bot, base-relative belief state (refreshed incrementally on the sim thread) ---
		// High-ground edges and sealable corridors are base-relative; computed a slice per tick
		// (throttled / spread) and read as snapshots, so the per-query path never pays the cost.
		readonly List<ZoneHighGroundEdge> highGroundEdges = [];
		readonly List<ZoneHighGroundEdge> highGroundBuilding = [];
		readonly List<CPos> highGroundSource = [];
		int highGroundCursor = -1;
		int highGroundRefreshTick;
		CPos highGroundBaseRef;
		int highGroundBaseHeight;
		CPos? highGroundLastBaseRef;

		// Sealable corridors are refreshed INCREMENTALLY (a few chokepoints per tick) to avoid a periodic burst.
		readonly List<ZoneGateCorridor> sealableCorridors = [];
		readonly List<ZoneGateCorridor> corridorBuilding = [];
		readonly List<ZoneChokepoint> corridorSource = [];
		int corridorCursor = -1;
		int corridorNextRefreshTick;
		CPos corridorBaseRef;
		HashSet<CPos> corridorEnemy;
		HashSet<CPos> corridorSeen;
		CPos? corridorLastBaseRef;
		int corridorLastEnemyCount = -1;

		// "Useful" chokepoints (reachable from own base, leading somewhere). The per-chokepoint flood is expensive,
		// so it is computed INCREMENTALLY on the sim thread (a few per tick) into usefulBuilding, then swapped into
		// usefulChokepoints. Queries (base builder, overlay) just read the last completed snapshot.
		readonly List<ZoneChokepoint> usefulChokepoints = [];
		readonly List<ZoneChokepoint> usefulBuilding = [];
		int usefulCursor = -1;
		int usefulNextRefreshTick;

		// Per-tick memo for RememberedEnemyBuildingCells - see there.
		HashSet<CPos> enemyBuildingCells = [];
		int enemyBuildingCellsTick = -1;
		uint usefulDomain;
		CPos usefulReference;
		HashSet<CPos> usefulEnemyBuildings;
		CPos? usefulLastBaseRef;
		int usefulLastEnemyCount = -1;

		// Terrain passability cached once per rebuild (avoids repeated Locomotor.MovementCostForCell in scans/floods).
		CellLayer<bool> passability;

		public TacticalMapBotModule(Actor self, TacticalMapBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		protected override void Created(Actor self)
		{
			pathFinder = world.WorldActor.TraitOrDefault<PathFinder>();
			resourceLayer = world.WorldActor.TraitOrDefault<IResourceLayer>();

			if (Info.TopologyLocomotors.Count > 0)
				locomotor = world.WorldActor.TraitsImplementing<Locomotor>()
					.FirstOrDefault(l => Info.TopologyLocomotors.Contains(l.Info.Name));

			// Fallback: first locomotor that actually allows ground movement.
			locomotor ??= world.WorldActor.TraitsImplementing<Locomotor>()
				.FirstOrDefault(l => l.Info.TerrainSpeeds.Values.Any(t => t.Cost < short.MaxValue));

			base.Created(self);
		}

		void IWorldLoaded.WorldLoaded(World w, WorldRenderer wr)
		{
			// Build the (terrain-only) topology up front so bots never pay the one-time scan as a mid-game hitch.
			// Deferred to a frame-end task so it runs AFTER PathFinder.WorldLoaded has created its abstract graph
			// (trait WorldLoaded order is not guaranteed), and gated to enabled bot players — a disabled
			// (non-genericbot) module never builds, which is the ZG-a activation gate.
			if (player.IsBot)
				w.AddFrameEndTask(_ =>
				{
					if (!IsTraitDisabled)
						EnsureBuilt();
				});
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (!TopologyReady)
				return;

			// Another bot rebuilt the shared topology (e.g. after a bridge change) -> adopt the newer version.
			// FIRST, before anything below reads a region id: the shared Regions list is already the new cut
			// while this bot's regionIdByCell is still the old one. Running the refreshes in the other order
			// would mix the two: TickRegionOwnershipRefresh would tally into an array sized for the new cut
			// using ids from the old one.
			if (shared != null && shared.Generation != sharedGeneration)
			{
				Adopt(shared);
				return;
			}

			// Five incremental refreshes, each doing a slice of work every tick so no single tick pays a
			// full flood. (Donor wrapped each in a CNBotPerf scope; Cameo drops those - no sampler exists.)
			TickUsefulRefresh();
			TickCorridorRefresh();
			TickHighGroundRefresh();
			TickTerritoryRefresh();
			TickRegionOwnershipRefresh();

			if (Info.RecomputeInterval > 0 && --recomputeTick <= 0)
			{
				recomputeTick = Info.RecomputeInterval;
				RebuildSharedOnBridgeChange();
				return;
			}

			if (--recheckTick > 0)
				return;

			recheckTick = Math.Max(1, Info.TopologyRecheckInterval);

			// A bridge being destroyed/repaired flips the passability of its cells -> rebuild the shared topology once.
			if (shared != null && CurrentBridgeSignature() != lastBridgeSignature)
				RebuildSharedOnBridgeChange();
		}

		int CurrentBridgeSignature()
		{
			// A fold over each watched cell, not "are they all passable". As a boolean this could only ever
			// report the FIRST change: once one bridge was down it read false and stayed false, so a second
			// bridge falling, or the first being repaired while the second stayed down, changed nothing and
			// the graph went stale for the rest of the match.
			// Checked LIVE rather than through the frozen passability snapshot, so a bridge actually
			// destroyed or repaired is seen. Only a handful of cells, and bridgeWatchCells is filled in
			// scan order, so the same map state always folds to the same number everywhere.
			var signature = 17;
			foreach (var cell in bridgeWatchCells)
			{
				var passable = locomotor != null && world.Map.Contains(cell)
					&& locomotor.MovementCostForCell(cell) != short.MaxValue;

				signature = signature * 31 + (passable ? 1 : 0);
			}

			return signature;
		}

		void EnsureBuilt()
		{
			if (!TopologyReady)
				Rebuild();
		}

		void Rebuild()
		{
			// TopologyReady is set only on success, at the end. It used to be set here, before the
			// guards below — so a build that bailed out (no abstract graph yet, no locomotor) left the
			// module permanently "ready" with zero chokepoints, and EnsureBuilt, which only rebuilds
			// while !TopologyReady, never tried again. The tactical map stayed silently dead for the
			// whole match. BuildOwnTopology returning false is exactly the "graph not created yet"
			// case the WorldLoaded frame-end task is meant to avoid, so it must stay retryable.
			ResetPerBaseCaches();
			recheckTick = Math.Max(1, Info.TopologyRecheckInterval);
			recomputeTick = Math.Max(1, Info.RecomputeInterval);
			chokepoints.Clear();
			bridgeWatchCells.Clear();
			abstractDomains = null;
			nodeCells = [];
			passability = null;
			regions.Clear();
			regionGateCorridors.Clear();
			regionIdByCell = null;
			shared = null;
			sharedGeneration = -1;

			if (pathFinder == null || locomotor == null)
				return;

			// Reuse another bot's build for the same locomotor if present; otherwise build it once and publish.
			var registry = Registries.GetValue(world, _ => []);
			var key = locomotor.Info.Name;
			if (registry.TryGetValue(key, out var existing) && existing != null)
			{
				Adopt(existing);
				TopologyReady = true;
				return;
			}

			if (!BuildOwnTopology())
				return;

			shared = Publish();
			registry[key] = shared;
			sharedGeneration = shared.Generation;
			TopologyReady = true;
		}

		// Per-bot refresh state: unlike the shared topology graph, this is this bot's own base-relative
		// and fog-belief work, so several Cameo bots in one game would otherwise all start their cycles at
		// tick 0 and stay locked in step forever at the same interval - bursting together instead of
		// spreading out. A one-time random phase offset per cycle (kept apart from each other) avoids that
		// without needing any coordination (the donor's world.LocalRandom approach, kept).
		void ResetPerBaseCaches()
		{
			var interval = Math.Max(1, Info.UsefulRefreshInterval);

			highGroundEdges.Clear();
			highGroundBuilding.Clear();
			highGroundSource.Clear();
			highGroundCursor = -1;
			highGroundRefreshTick = world.WorldTick + world.LocalRandom.Next(interval);
			highGroundLastBaseRef = null;
			usefulChokepoints.Clear();
			usefulBuilding.Clear();
			usefulCursor = -1;
			usefulNextRefreshTick = world.WorldTick + world.LocalRandom.Next(interval);
			usefulLastBaseRef = null;
			usefulLastEnemyCount = -1;
			sealableCorridors.Clear();
			corridorBuilding.Clear();
			corridorSource.Clear();
			corridorCursor = -1;
			corridorLastBaseRef = null;
			corridorLastEnemyCount = -1;
			corridorNextRefreshTick = world.WorldTick + world.LocalRandom.Next(interval);

			// ZG-b belief caches: territory, doors and region owners were derived against the old cut's
			// corridors and region ids (and the old fog-memory picture), so they are dropped and rebuilt
			// on their next refresh. Resetting lastBaseRef/lastEnemyCount forces the recompute even when
			// neither the base nor the remembered count moved.
			territory.Clear();
			doors.Clear();
			territoryWall.Clear();
			territoryFront.Clear();
			horizon.Clear();
			territoryLastBaseRef = null;
			territoryLastEnemyCount = -1;
			territoryNextRefreshTick = world.WorldTick + world.LocalRandom.Next(interval);
			regionOwners = [];
			regionOwnershipNextRefreshTick = world.WorldTick + world.LocalRandom.Next(interval);
		}

		// Adopt a shared topology built by another bot: reference the heavy data, copy the small lists.
		void Adopt(SharedZoneTopology sh)
		{
			shared = sh;
			sharedGeneration = sh.Generation;
			passability = sh.Passability;
			abstractDomains = sh.AbstractDomains;
			nodeCells = sh.NodeCells;
			lastBridgeSignature = sh.LastBridgeSignature;
			chokepoints.Clear();
			chokepoints.AddRange(sh.Chokepoints);
			bridgeWatchCells.Clear();
			bridgeWatchCells.AddRange(sh.BridgeWatchCells);
			regions.Clear();
			regions.AddRange(sh.Regions);
			regionGateCorridors.Clear();
			regionGateCorridors.AddRange(sh.RegionGateCorridors);
			regionIdByCell = sh.RegionIdByCell;
			regionBarrier = sh.RegionBarrier;

			// The per-bot belief caches were computed against the OLD cut's corridors and region ids;
			// drop them so the next refresh recomputes on the adopted one.
			ResetPerBaseCaches();
		}

		SharedZoneTopology Publish()
		{
			var sh = new SharedZoneTopology
			{
				Passability = passability,
				AbstractDomains = abstractDomains,
				NodeCells = nodeCells,
				LastBridgeSignature = lastBridgeSignature,
				RegionIdByCell = regionIdByCell,
				RegionBarrier = regionBarrier,
			};
			sh.Chokepoints.AddRange(chokepoints);
			sh.BridgeWatchCells.AddRange(bridgeWatchCells);
			sh.Regions.AddRange(regions);
			sh.RegionGateCorridors.AddRange(regionGateCorridors);
			return sh;
		}

		// Rebuild the shared topology after a bridge change and bump the generation so other bots re-adopt it.
		void RebuildSharedOnBridgeChange()
		{
			if (shared == null || !BuildOwnTopology())
				return;

			shared.Passability = passability;
			shared.AbstractDomains = abstractDomains;
			shared.NodeCells = nodeCells;
			shared.LastBridgeSignature = lastBridgeSignature;
			shared.Chokepoints.Clear();
			shared.Chokepoints.AddRange(chokepoints);
			shared.BridgeWatchCells.Clear();
			shared.BridgeWatchCells.AddRange(bridgeWatchCells);

			// A bridge changing can split or merge regions (it changes which corridors resolve), so the
			// shape has to be rebuilt alongside the chokepoints that gate it.
			shared.Regions.Clear();
			shared.Regions.AddRange(regions);
			shared.RegionGateCorridors.Clear();
			shared.RegionGateCorridors.AddRange(regionGateCorridors);
			shared.RegionIdByCell = regionIdByCell;
			shared.RegionBarrier = regionBarrier;

			shared.Generation++;
			sharedGeneration = shared.Generation;

			// This bot's own belief caches are stale on the new cut too (territory/doors/owners index
			// the old region ids) - same drop-on-adopt as every other bot gets.
			ResetPerBaseCaches();
		}

		// The heavy terrain scan (shared by all bots via Publish): fills passability, abstractDomains, nodeCells,
		// chokepoints, bridgeWatchCells and lastBridgeSignature. Returns false if the locomotor has no abstract graph.
		bool BuildOwnTopology()
		{
			chokepoints.Clear();
			bridgeWatchCells.Clear();

			// Terrain-only connectivity (BlockedByActor.None): topology should reflect permanent terrain (cliffs,
			// water, bridges, ramps), NOT trees/buildings/units, which would create fake chokepoints around obstacles.
			// Queried BEFORE the passability fill so a not-yet-created abstract graph costs nothing: this method is
			// retryable (see Rebuild), and the fill is a full-map pass we don't want to repeat on every failed attempt.
			var (graph, domains) = pathFinder.GetOverlayDataForLocomotor(locomotor, BlockedByActor.None);
			if (graph == null || domains == null || graph.Count == 0)
				return false;

			// Cache terrain passability once so the scans/floods below don't call Locomotor.MovementCostForCell repeatedly.
			passability = new CellLayer<bool>(world.Map);
			foreach (var c in world.Map.AllCells)
				passability[c] = locomotor.MovementCostForCell(c) != short.MaxValue;

			abstractDomains = domains;
			nodeCells = graph.Keys.ToArray();

			// Count abstract nodes per domain so we can ignore tiny, isolated regions (mesa tops, unreachable
			// islands). Those are their own domain with only a handful of nodes and produce meaningless chokepoints.
			var domainNodeCount = new Dictionary<uint, int>();
			foreach (var node in nodeCells)
				if (abstractDomains.TryGetValue(node, out var dom))
					domainNodeCount[dom] = (domainNodeCount.TryGetValue(dom, out var dc) ? dc : 0) + 1;

			// De-duplicate chokepoints that map to the same representative cell.
			var byCell = new Dictionary<CPos, ZoneChokepoint>();

			void AddTyped(CPos cell, uint domain, ZoneChokepointType type)
			{
				if (byCell.ContainsKey(cell))
					return;

				// Merge near-duplicate passages to cut clutter. Discrete points (ramps, bridges) are kept as-is.
				var mergeSq = Math.Max(0, Info.ChokepointMergeRadius) * Math.Max(0, Info.ChokepointMergeRadius);
				if (type == ZoneChokepointType.Passage && mergeSq > 0)
					foreach (var existing in byCell.Keys)
						if ((existing - cell).LengthSquared <= mergeSq)
							return;

				var weight = type switch
				{
					ZoneChokepointType.Bridge => Info.BridgeWeight,
					ZoneChokepointType.Ramp => Info.RampWeight,
					_ => Info.PassageWeight,
				};

				byCell[cell] = new ZoneChokepoint(cell, domain, type, weight);
				if (type == ZoneChokepointType.Bridge)
					bridgeWatchCells.Add(cell);
			}

			void Add(CPos cell, ZoneChokepointType type)
			{
				// Ignore chokepoints inside tiny, isolated regions (e.g. an unreachable mesa top): not tactically real.
				var domain = DomainOf(cell);
				if (domainNodeCount.TryGetValue(domain, out var nodes) && nodes < Math.Max(1, Info.MinDomainNodes))
					return;

				AddTyped(cell, domain, type);
			}

			// Chokepoints are found directly from the terrain (not from the coarse abstract graph, which over-produces
			// noise): narrow separating passages, cliff ramps (marked below + above), and bridges.
			// Order matters: the near-duplicate merge in AddTyped only drops a Passage that lands close
			// to an ALREADY REGISTERED chokepoint. Scanning passages first meant bridges and ramps did
			// not exist yet, so nothing could be merged away — and bridges/ramps are never merge-checked
			// themselves. A single bridge therefore produced three markers (B in the middle, P at each
			// approach), which then crowded out other approaches in the donor's top-N hotspot query.
			// Discrete features first, passages last, so ChokepointMergeRadius actually does its job.
			foreach (var center in ScanBridgeCenters())
				Add(center, ZoneChokepointType.Bridge);

			foreach (var endpoint in ScanRampEndpoints())
				Add(endpoint, ZoneChokepointType.Ramp);

			foreach (var center in ScanPassageCenters())
				Add(center, ZoneChokepointType.Passage);

			chokepoints.AddRange(byCell.Values);

			// Donor also watched CNDestroyableCliff footprints here: a cliff shot open re-cuts the map exactly
			// the way a bridge falling does. Cameo has no destroyable-cliff trait, so only bridge cells are
			// watched — if one is ever added, extend the watch here rather than adding a second mechanism.
			lastBridgeSignature = CurrentBridgeSignature();

			BuildRegions(domainNodeCount);
			return true;
		}

		// The map's shape, cut by the same chokepoint corridors that gate the territory walk PLUS every
		// cliff ramp's full footprint - computed once here (unseeded by any claim) so every bot reads the
		// same regions regardless of who, if anyone, owns them. A ramp only sealable-corridor-resolves to
		// a narrow gate cell when it happens to be the tightest crossing nearby; a wide or gentle one
		// otherwise let the flood walk straight through it, so a visible cliff with a walkable slope ended
		// up inside one region instead of splitting high ground from low. The full ramp footprint (not
		// just its two chokepoint marker endpoints) is barrier here regardless of whether it resolved to a
		// gate corridor, because height is a real separation even where nothing is narrow enough to
		// wall. One flood-fill component per gap between barrier cells is one region; adjacency between
		// regions falls out of which ones share a barrier cell, whether or not that cell also happens to
		// carry a resolved door corridor.
		//
		// Not every barrier deserves to stand, though: a coastline pinched every few cells came out as a
		// chain of 15/35/47-cell regions, which is not how anybody reads that ground. So the fill runs
		// more than once - undersized regions merge by dropping the barrier piece between them and
		// filling again (see MinRegionSize), which recomputes every outline, count and adjacency instead
		// of patching finished records up by hand.
		void BuildRegions(Dictionary<uint, int> domainNodeCount)
		{
			var gate = new HashSet<CPos>();
			var corridors = ResolveChokepointCorridors(gate);

			// Kept for the whole run, not just for cellToCorridorIndex below: GateCorridorIndices on every
			// finished region points in here, and the merge only ever drops barrier pieces - it never
			// renumbers this list - so the indices stay valid however many rounds the fill takes.
			regionGateCorridors.Clear();
			regionGateCorridors.AddRange(corridors);

			var cellToCorridorIndex = new Dictionary<CPos, int>();
			for (var i = 0; i < corridors.Count; i++)
				foreach (var cell in corridors[i].Cells)
					cellToCorridorIndex[cell] = i;

			// IsCliffRamp only flags a cell with a cliff immediately beside it, so on a ramp wider than a
			// couple of cells only its outermost columns qualify: the middle of the slope touches nothing
			// impassable and was never barrier at all, which leaves a hole straight through the middle of
			// the very thing being sealed - and the one-ring dilation below only ever covered a hole two
			// cells across. A ramp is one connected run of walkable slope, bounded by the cliff it cuts
			// through, so the flagged cells are grown across that run: the seal ends up the ramp's true
			// width, however wide it is, while open bumpy ground stays untouched because no cliff seeds it
			// in the first place.
			// Map.Ramp was tried as part of this run and taken back out: on this tileset a great many
			// ordinary ground tiles carry a nonzero ramp index, so the run was connected across most of the
			// map and the seal carpeted open ground - see the terrain census logged below, which is what
			// any further attempt here should be decided on rather than on what a ramp "ought" to look
			// like.
			var slopeCells = new HashSet<CPos>();
			var rampCells = new HashSet<CPos>();
			foreach (var c in world.Map.AllCells)
			{
				if (!IsPassable(c) || !IsHeightTransition(c))
					continue;

				slopeCells.Add(c);

				// Seeded from the cliff, so a hillside nowhere near one is never barrier however much it
				// slopes.
				if (HasCliffAbove(c))
					rampCells.Add(c);
			}

			// What the map is actually made of, because three attempts at sealing ramps were each argued
			// from a different guess about that and each was wrong in a different direction. Once per map,
			// alongside the region census below.
			var passableCells = 0;
			var slopeTileCells = 0;
			var transitionCells = 0;
			var cliffAdjacentCells = 0;
			var heightCensus = new Dictionary<byte, int>();
			foreach (var c in world.Map.AllCells)
			{
				if (!IsPassable(c))
					continue;

				passableCells++;
				var h = world.Map.Height[c];
				heightCensus[h] = heightCensus.GetValueOrDefault(h) + 1;

				if (world.Map.Ramp[c] != 0)
					slopeTileCells++;

				if (IsHeightTransition(c))
					transitionCells++;

				if (HasCliffAbove(c))
					cliffAdjacentCells++;
			}

			CAAIUtils.BotDebug("terrain: {0} passable, {1} slope tiles, {2} height transitions, {3} cliff-adjacent | heights {4}",
				passableCells, slopeTileCells, transitionCells, cliffAdjacentCells,
				string.Join(" ", heightCensus.OrderBy(kv => kv.Key).Select(kv => $"{kv.Key}:{kv.Value}")));

			// Bounded, because slope tiles are not rare on rolling terrain: their connected run reaches
			// across half a map, and an unbounded growth swallowed it whole - the barrier covered open
			// ground everywhere and left regions of one and two cells behind. A ramp is a cut through a
			// cliff and is only so wide, and both of its edges seed, so the bound closes a ramp up to
			// roughly twice RampSealMaxSpread across while leaving open hillside alone.
			var maxSpread = Math.Max(1, Info.RampSealMaxSpread);
			var rampQueue = new Queue<(CPos Cell, int Depth)>();
			foreach (var seed in rampCells)
				rampQueue.Enqueue((seed, 0));

			while (rampQueue.Count > 0)
			{
				var (cell, depth) = rampQueue.Dequeue();
				if (depth >= maxSpread)
					continue;

				foreach (var dir in CVec.Directions)
				{
					var next = cell + dir;
					if (slopeCells.Contains(next) && rampCells.Add(next))
						rampQueue.Enqueue((next, depth + 1));
				}
			}

			// The barrier is kept as individually droppable pieces - one per resolved corridor, one per
			// chokepoint that never resolved to one, one per physical ramp - because merging undersized
			// regions below works by dropping the piece that separates them and running the whole fill
			// again, rather than by editing finished Zone records. Recomputing boundaries, adjacency
			// and the resource/buildable counts by hand per merge is exactly the bespoke bookkeeping that
			// re-deriving door geometry by hand already cost this feature five attempts.
			// Droppable says whether the merge below may give a piece up. Corridors and chokepoint cells
			// may: a bottleneck can be too minor a wrinkle to deserve a region. A ramp may not - dropping
			// it merges high ground into low ground, which is the one separation the whole ramp barrier
			// exists for, and a small plateau is still a place in its own right rather than part of the
			// ground below it.
			var pieces = new List<(HashSet<CPos> Cells, bool Droppable)>();
			foreach (var corridor in corridors)
				pieces.Add(([.. corridor.Cells], true));

			foreach (var cell in gate)
				if (!cellToCorridorIndex.ContainsKey(cell))
					pieces.Add(([cell], true));

			// A one-cell-thin barrier line has two known ways to leak with 8-directional movement: the
			// flood corner-cuts diagonally between two ramp cells that only touch corner-to-corner, and
			// the flat lead-in/lead-out cells at a ramp's very top and bottom are not height transitions
			// at all, so nothing above flags them - exactly where a region flowed straight through in the
			// first overlay pass. Dilating by one ring closes both: thick enough that no diagonal gap fits,
			// and wide enough to cover the ramp's open ends too. Per ramp rather than over one combined
			// blob - same cells, but each physical ramp can then be dropped on its own.
			var rampVisited = new HashSet<CPos>();
			var rampPieces = 0;
			foreach (var start in rampCells)
			{
				if (!rampVisited.Add(start))
					continue;

				var component = ConnectedComponent(start, rampCells, rampVisited);
				var piece = new HashSet<CPos>(component);
				foreach (var cell in component)
					foreach (var dir in CVec.Directions)
					{
						var n = cell + dir;
						if (world.Map.Contains(n) && IsPassable(n))
							piece.Add(n);
					}

				pieces.Add((piece, false));
				rampPieces++;
			}

			var active = new bool[pieces.Count];
			for (var i = 0; i < active.Length; i++)
				active[i] = true;

			var minRegionSize = Math.Max(0, Info.MinRegionSize);
			var piecesDropped = 0;
			var round = 0;

			// Cheap insurance, not a tuning knob: dropping is monotone, so this terminates on its own -
			// and it all happens once inside BuildOwnTopology, never per tick. One piece goes per round
			// now, so the ceiling has to be the number of droppable pieces rather than a flat ten, which
			// would have stopped the merge a tenth of the way through. Each extra round is one more
			// full-map fill, paid once at map load.
			var maxMergeRounds = pieces.Count + 1;

			for (; ; round++)
			{
				var barrier = new HashSet<CPos>();
				for (var i = 0; i < pieces.Count; i++)
					if (active[i])
						barrier.UnionWith(pieces[i].Cells);

				FloodRegions(barrier, cellToCorridorIndex, domainNodeCount);
				regionBarrier = barrier;

				if (minRegionSize == 0 || round >= maxMergeRounds - 1)
					break;

				// Every INDEPENDENT drop of the round at once. Dropping every qualifying piece together was
				// wrong because they were all measured against a fill still cut by pieces about to be
				// dropped themselves: a side reads undersized only because its neighbours have not been
				// merged into it yet, the piece goes on that reading, and dropping is monotone so it never
				// comes back. A played map lost 67 of 120 pieces that way and left passages separating
				// nothing.
				//
				// But only pieces touching the SAME region can spoil each other's measurement. Two whose
				// neighbouring regions are disjoint can go in one round with no artifact at all, and nearly
				// every sliver is of that kind. Taking strictly one per round was the safe reading and cost
				// 129 full-map fills at load on a 367-piece map - 1901 ms inside a single bot tick, which
				// is a visible hitch and was waved through in its own commit message as "paid once at map
				// load" without anyone measuring it.
				// An undersized pocket with nothing to merge into keeps its pieces and stays small, the
				// same way MinDomainNodes leaves unreachable pockets alone.
				var eligible = new List<(int Index, int Separated, HashSet<int> Touching)>();
				for (var i = 0; i < pieces.Count; i++)
				{
					if (!active[i] || !pieces[i].Droppable)
						continue;

					var touching = TouchedRegions(pieces[i].Cells);
					if (touching.Count < 2)
						continue;

					var separated = int.MaxValue;
					foreach (var id in touching)
						separated = Math.Min(separated, regions[id].Size);

					if (separated < minRegionSize)
						eligible.Add((i, separated, touching));
				}

				if (eligible.Count == 0)
					break;

				// Worst first, so where two genuinely do conflict the more urgent one goes this round and
				// the other is re-measured in the next.
				eligible.Sort((a, b) => a.Separated.CompareTo(b.Separated));

				var claimed = new HashSet<int>();
				foreach (var (index, _, touching) in eligible)
				{
					if (touching.Overlaps(claimed))
						continue;

					claimed.UnionWith(touching);
					active[index] = false;
					piecesDropped++;
				}
			}

			CAAIUtils.BotDebug(
				"regions: {0} barrier pieces ({1} ramps, {2} ramp cells, kept whatever happens), {3} dropped "
				+ "over {4} rounds -> {5} regions (min size {6})",
				pieces.Count, rampPieces, rampCells.Count, piecesDropped, round + 1, regions.Count, minRegionSize);
		}

		/// <summary>
		/// The regions this barrier piece holds apart. Read off the finished fill rather than tracked
		/// during it: a piece is small, and what it separates is simply whatever <see cref="regionIdByCell"/>
		/// says on either side of it.
		/// <para>
		/// The whole set rather than only the smallest size, because the merge needs to know which drops
		/// may share a round: two pieces with no neighbouring region in common cannot spoil each other's
		/// measurement, and batching those is the difference between a handful of full-map fills and one
		/// per dropped piece. Fewer than two regions means nothing on the far side to merge into - a piece
		/// against the map edge, or buried inside a wider barrier.
		/// </para>
		/// </summary>
		HashSet<int> TouchedRegions(HashSet<CPos> piece)
		{
			var touching = new HashSet<int>();
			foreach (var cell in piece)
				foreach (var dir in CVec.Directions)
				{
					var id = RegionIdAt(cell + dir);
					if (id >= 0)
						touching.Add(id);
				}

			return touching;
		}

		/// <summary>
		/// One flood-fill pass over the map with the given barrier: every gap between barrier cells
		/// becomes one region, with its outline, adjacency and counts derived fresh. Called repeatedly by
		/// <see cref="BuildRegions"/> with a shrinking barrier, so everything a merge would otherwise have
		/// to patch up by hand is simply recomputed instead.
		/// </summary>
		void FloodRegions(HashSet<CPos> barrier, Dictionary<CPos, int> cellToCorridorIndex, Dictionary<uint, int> domainNodeCount)
		{
			regions.Clear();
			regionIdByCell = new CellLayer<int>(world.Map);
			foreach (var c in world.Map.AllCells)
				regionIdByCell[c] = -1;

			var minDomainNodes = Math.Max(1, Info.MinDomainNodes);
			var visited = new HashSet<CPos>(barrier);
			var regionsTouchingBarrierCell = new Dictionary<CPos, List<int>>();

			foreach (var start in world.Map.AllCells)
			{
				if (!IsPassable(start) || !visited.Add(start))
					continue;

				// Tiny isolated pockets (a mesa top, an unreachable sliver) are not a tactically real
				// region, same reasoning MinDomainNodes already applies to chokepoints in one.
				if (domainNodeCount.TryGetValue(DomainOf(start), out var nodes) && nodes < minDomainNodes)
					continue;

				var id = regions.Count;
				var cells = new List<CPos>();
				var gateIndices = new HashSet<int>();
				var touchedBarrierCells = new List<CPos>();
				var resourceCells = 0;
				var buildableCells = 0;
				var queue = new Queue<CPos>();
				queue.Enqueue(start);
				cells.Add(start);

				while (queue.Count > 0)
				{
					var cell = queue.Dequeue();
					regionIdByCell[cell] = id;

					if (resourceLayer != null && resourceLayer.GetResource(cell).Type != null)
						resourceCells++;

					if (world.Map.Ramp[cell] == 0)
						buildableCells++;

					foreach (var dir in CVec.Directions)
					{
						var next = cell + dir;
						if (!world.Map.Contains(next))
							continue;

						if (barrier.Contains(next))
						{
							if (cellToCorridorIndex.TryGetValue(next, out var corridorIndex))
								gateIndices.Add(corridorIndex);

							touchedBarrierCells.Add(next);
							continue;
						}

						if (!IsPassable(next) || !visited.Add(next))
							continue;

						cells.Add(next);
						queue.Enqueue(next);
					}
				}

				foreach (var barrierCell in touchedBarrierCells)
				{
					if (!regionsTouchingBarrierCell.TryGetValue(barrierCell, out var touching))
						regionsTouchingBarrierCell[barrierCell] = touching = [];

					if (!touching.Contains(id))
						touching.Add(id);
				}

				// A cell with any neighbour outside this region's own cell set is on the outline - a
				// separate pass over the finished set rather than tracked during the flood, since a
				// neighbour failing visited.Add there could mean either "already ours" or "someone else's
				// region", and only this region's own finished cell set can tell the two apart.
				var cellSet = new HashSet<CPos>(cells);
				var boundary = new List<CPos>();
				foreach (var cell in cells)
				{
					var isBoundary = false;
					foreach (var dir in CVec.Directions)
					{
						if (world.Map.Contains(cell + dir) && cellSet.Contains(cell + dir))
							continue;

						isBoundary = true;
						break;
					}

					if (isBoundary)
						boundary.Add(cell);
				}

				regions.Add(new Zone(id, cells.ToArray(), gateIndices.ToArray(), [], resourceCells,
					buildableCells, boundary.ToArray()));
			}

			// Adjacency falls out of which regions share a barrier cell - a resolved gate corridor or an
			// unresolved cliff ramp both count. One pass over the (small) barrier-cell map rather than one
			// per region: most barrier cells touch exactly two regions, so this stays close to linear.
			var adjacency = new Dictionary<int, HashSet<int>>();
			foreach (var touching in regionsTouchingBarrierCell.Values)
			{
				if (touching.Count < 2)
					continue;

				foreach (var a in touching)
				{
					if (!adjacency.TryGetValue(a, out var set))
						adjacency[a] = set = [];

					foreach (var b in touching)
						if (b != a)
							set.Add(b);
				}
			}

			for (var id = 0; id < regions.Count; id++)
			{
				var region = regions[id];
				var adjacent = adjacency.TryGetValue(id, out var set) ? set.ToArray() : [];
				regions[id] = new Zone(id, region.Cells, region.GateCorridorIndices, adjacent,
					region.ResourceCellCount, region.BuildableCellCount, region.BoundaryCells);
			}
		}

		// Directly scans the terrain for narrow separating passages: the narrowest cell of each bounded, thick-
		// shouldered through-corridor whose two sides are both substantial (not a dead end). One cell per local
		// minimum; near-duplicates are merged by the caller.
		IEnumerable<CPos> ScanPassageCenters()
		{
			var maxWidth = Math.Max(1, Info.MaxPassageWidth);
			var widthH = new Dictionary<CPos, int>();
			var widthV = new Dictionary<CPos, int>();

			foreach (var c in world.Map.AllCells)
			{
				if (!IsPassable(c))
					continue;

				var wh = CorridorWidth(c, new CVec(1, 0), maxWidth);
				if (wh <= maxWidth)
					widthH[c] = wh;

				var wv = CorridorWidth(c, new CVec(0, 1), maxWidth);
				if (wv <= maxWidth)
					widthV[c] = wv;
			}

			var centers = new List<CPos>();

			// Horizontal corridors (narrow in X): keep the narrowest along the corridor length (Y).
			foreach (var (c, w) in widthH)
			{
				var up = widthH.GetValueOrDefault(c + new CVec(0, 1), int.MaxValue);
				var dn = widthH.GetValueOrDefault(c + new CVec(0, -1), int.MaxValue);
				if (w <= up && w <= dn && IsRealSeparator(c, new CVec(1, 0)))
					centers.Add(c);
			}

			// Vertical corridors (narrow in Y): keep the narrowest along the corridor length (X).
			foreach (var (c, w) in widthV)
			{
				var l = widthV.GetValueOrDefault(c + new CVec(-1, 0), int.MaxValue);
				var r = widthV.GetValueOrDefault(c + new CVec(1, 0), int.MaxValue);
				if (w <= l && w <= r && IsRealSeparator(c, new CVec(0, 1)))
					centers.Add(c);
			}

			return centers;
		}

		// Width of the passable run through c along step, if it is a through-corridor (open along the perpendicular
		// length axis) bounded by thick (>=2 cell) impassable shoulders within maxWidth. Otherwise int.MaxValue.
		int CorridorWidth(CPos c, CVec step, int maxWidth)
		{
			var perp = new CVec(step.Y, step.X);
			if (!IsPassable(c + perp) || !IsPassable(c - perp))
				return int.MaxValue;

			var pos = WalkSide(c, step, maxWidth);
			if (pos < 0)
				return int.MaxValue;

			var neg = WalkSide(c, new CVec(-step.X, -step.Y), maxWidth);
			if (neg < 0)
				return int.MaxValue;

			return pos + neg + 1;
		}

		// Passable cells from c along step until a thick shoulder; returns that count, or -1 if no thick shoulder.
		int WalkSide(CPos c, CVec step, int maxWidth)
		{
			for (var i = 1; i <= maxWidth; i++)
			{
				var cell = c + step * i;
				if (!IsPassable(cell))
				{
					var beyond = c + step * (i + 1);
					return !world.Map.Contains(beyond) || !IsPassable(beyond) ? i - 1 : -1;
				}
			}

			return -1;
		}

		// True if blocking the narrow corridor through c (along step) separates two substantial regions — both
		// perpendicular sides flood to at least MinPassageSideCells. Drops dead ends and non-separating gaps.
		bool IsRealSeparator(CPos c, CVec step)
		{
			var perp = new CVec(step.Y, step.X);
			var barrier = new HashSet<CPos> { c };
			for (var i = 1; i <= Info.MaxPassageWidth; i++)
			{
				var p = c + step * i;
				if (!IsPassable(p))
					break;
				barrier.Add(p);
			}

			for (var i = 1; i <= Info.MaxPassageWidth; i++)
			{
				var nn = c + new CVec(-step.X, -step.Y) * i;
				if (!IsPassable(nn))
					break;
				barrier.Add(nn);
			}

			var min = Math.Max(1, Info.MinPassageSideCells);
			return FloodAtLeast(c + perp, barrier, min) && FloodAtLeast(c - perp, barrier, min);
		}

		bool FloodAtLeast(CPos seed, HashSet<CPos> barrier, int min)
		{
			if (!world.Map.Contains(seed) || !IsPassable(seed) || barrier.Contains(seed))
				return false;

			var visited = new HashSet<CPos>(barrier) { seed };
			var queue = new Queue<CPos>();
			queue.Enqueue(seed);
			var count = 0;
			while (queue.Count > 0)
			{
				var cell = queue.Dequeue();
				if (++count >= min)
					return true;

				foreach (var d in CVec.Directions)
				{
					var nx = cell + d;
					if (!world.Map.Contains(nx) || !IsPassable(nx) || !visited.Add(nx))
						continue;

					queue.Enqueue(nx);
				}
			}

			return false;
		}

		// Finds cliff ramps directly and yields a point below and above each (clustered: one ramp = two points).
		IEnumerable<CPos> ScanRampEndpoints()
		{
			var rampCells = new HashSet<CPos>();
			foreach (var c in world.Map.AllCells)
				if (IsPassable(c) && IsCliffRamp(c))
					rampCells.Add(c);

			var endpoints = new List<CPos>();
			var visited = new HashSet<CPos>();
			foreach (var start in rampCells)
			{
				if (!visited.Add(start))
					continue;

				var (bottom, top) = RampEndpoints(Centroid(ConnectedComponent(start, rampCells, visited)));
				if (bottom != null)
					endpoints.Add(bottom.Value);
				if (top != null)
					endpoints.Add(top.Value);
			}

			return endpoints;
		}

		// Finds bridges directly (terrain type "Bridge", bridge actor footprints, and MapEditorData-tagged
		// bridge actors) and yields one cell per bridge.
		IEnumerable<CPos> ScanBridgeCenters()
		{
			var bridgeCells = new HashSet<CPos>();
			foreach (var c in world.Map.AllCells)
				if (world.Map.GetTerrainInfo(c).Type == "Bridge")
					bridgeCells.Add(c);

			foreach (var b in world.ActorsWithTrait<Bridge>())
			{
				var bi = b.Actor.Info.TraitInfoOrDefault<BuildingInfo>();
				if (bi == null)
					continue;

				foreach (var cell in bi.Tiles(b.Actor.Location))
					bridgeCells.Add(cell);
			}

			// High/elevated bridges (the donor's BRIDGE1/BRIDGE2/RAILBRDG1/RAILBRDG2) are pure decoration there -
			// Immobile, OccupiesSpace: false, no Bridge trait, and nothing patches the terrain layer to type
			// "Bridge" under them since they are not destructible - so neither check above ever saw them,
			// and they fell through to being scanned as a plain Passage instead. Every bridge actor in the
			// donor's rules, low or high, was tagged MapEditorData Categories: Bridge, which is the one
			// thing both families shared. Kept in the port: harmless when nothing is tagged, and it covers
			// the same decoration-only case if a Cameo content pack ever ships it.
			foreach (var a in world.Actors)
			{
				if (a.IsDead || !a.IsInWorld)
					continue;

				var med = a.Info.TraitInfoOrDefault<MapEditorDataInfo>();
				if (med == null || !med.Categories.Contains("Bridge"))
					continue;

				var bi = a.Info.TraitInfoOrDefault<BuildingInfo>();
				if (bi == null)
					continue;

				foreach (var cell in bi.Tiles(a.Location))
					bridgeCells.Add(cell);
			}

			var centers = new List<CPos>();
			var visited = new HashSet<CPos>();
			foreach (var start in bridgeCells)
			{
				if (!visited.Add(start))
					continue;

				centers.Add(Centroid(ConnectedComponent(start, bridgeCells, visited)));
			}

			return centers;
		}

		// One 8-connected component of `cells`, grown from `start`. The caller must already have
		// added `start` to `visited` — the donors all do `if (!visited.Add(start)) continue;` —
		// otherwise the walk re-enters through a neighbour and `start` is collected twice.
		internal static List<CPos> ConnectedComponent(CPos start, HashSet<CPos> cells, HashSet<CPos> visited)
		{
			var comp = new List<CPos> { start };
			var queue = new Queue<CPos>();
			queue.Enqueue(start);
			while (queue.Count > 0)
			{
				var c = queue.Dequeue();
				foreach (var d in CVec.Directions)
				{
					var n = c + d;
					if (cells.Contains(n) && visited.Add(n))
					{
						comp.Add(n);
						queue.Enqueue(n);
					}
				}
			}

			return comp;
		}

		internal static CPos Centroid(IReadOnlyList<CPos> cells)
		{
			long sx = 0;
			long sy = 0;
			foreach (var c in cells)
			{
				sx += c.X;
				sy += c.Y;
			}

			var centre = new CPos((int)(sx / cells.Count), (int)(sy / cells.Count));
			var rep = cells[0];
			var best = (rep - centre).LengthSquared;
			foreach (var c in cells)
			{
				var s = (c - centre).LengthSquared;
				if (s < best)
				{
					best = s;
					rep = c;
				}
			}

			return rep;
		}

		// A ramp: a walkable height transition AND flanked by a cliff (a higher, impassable neighbour = the cliff wall
		// the ramp cuts through). This excludes gentle hills / bumpy open ground that merely vary in height.
		bool IsCliffRamp(CPos cell)
		{
			return IsHeightTransition(cell) && HasCliffAbove(cell);
		}

		// The cliff-wall half of IsCliffRamp on its own: a higher, impassable neighbour. Split out because
		// the region barrier seeds from slope tiles as well, not only from cells that read as a walkable
		// height transition.
		bool HasCliffAbove(CPos cell)
		{
			var h = world.Map.Height[cell];
			foreach (var d in CVec.Directions)
			{
				var n = cell + d;
				if (world.Map.Contains(n) && !IsPassable(n) && world.Map.Height[n] > h)
					return true;
			}

			return false;
		}

		// Representative cells just below and just above a cliff ramp, instead of on the slope.
		(CPos? Bottom, CPos? Top) RampEndpoints(CPos cell)
		{
			CPos? transition = IsHeightTransition(cell) ? cell : null;
			if (transition == null)
				foreach (var d in CVec.Directions)
					if (IsHeightTransition(cell + d))
					{
						transition = cell + d;
						break;
					}

			if (transition == null)
				return (null, null);

			var t = transition.Value;
			var h = world.Map.Height[t];
			CVec downhill = default;
			CVec uphill = default;
			var haveDown = false;
			var haveUp = false;
			foreach (var d in CVec.Directions)
			{
				var n = t + d;
				if (!world.Map.Contains(n) || !IsPassable(n))
					continue;

				var nh = world.Map.Height[n];
				if (Math.Abs(nh - h) > 1)
					continue;

				if (nh < h && !haveDown)
				{
					downhill = d;
					haveDown = true;
				}
				else if (nh > h && !haveUp)
				{
					uphill = d;
					haveUp = true;
				}
			}

			var bottom = haveDown ? (CPos?)ProjectPassable(t, downhill, 2) : null;
			var top = haveUp ? (CPos?)ProjectPassable(t, uphill, 2) : null;
			return (bottom, top);
		}

		// Steps up to 'steps' cells along dir while passable, returning the furthest reachable cell.
		CPos ProjectPassable(CPos start, CVec dir, int steps)
		{
			var c = start;
			for (var i = 0; i < steps; i++)
			{
				var n = c + dir;
				if (!world.Map.Contains(n) || !IsPassable(n))
					break;

				c = n;
			}

			return c;
		}

		bool IsHeightTransition(CPos cell)
		{
			if (!world.Map.Contains(cell))
				return false;

			var h = world.Map.Height[cell];
			var lower = false;
			var higher = false;
			foreach (var d in CVec.Directions)
			{
				var n = cell + d;
				if (!world.Map.Contains(n) || !IsPassable(n))
					continue;

				var nh = world.Map.Height[n];

				// Skip cliff jumps (height diff > 1 is not walkable); we only want actual walkable transitions.
				if (Math.Abs(nh - h) > 1)
					continue;

				if (nh < h)
					lower = true;
				else if (nh > h)
					higher = true;
			}

			return lower && higher;
		}

		bool IsPassable(CPos cell)
		{
			if (!world.Map.Contains(cell))
				return false;

			if (passability != null)
				return passability[cell];

			return locomotor != null && locomotor.MovementCostForCell(cell) != short.MaxValue;
		}

		uint DomainOf(CPos reference)
		{
			if (nodeCells.Length == 0)
				return 0;

			var best = nodeCells[0];
			var bestDist = (best - reference).LengthSquared;
			foreach (var node in nodeCells)
			{
				var dist = (node - reference).LengthSquared;
				if (dist < bestDist)
				{
					bestDist = dist;
					best = node;
				}
			}

			return abstractDomains.TryGetValue(best, out var d) ? d : 0;
		}

		// ---------------------------------------------------------------------
		// ZG-b: base-relative refreshes, territory claim, doors, region ownership.
		// Everything below this line is PER-BOT BELIEF: it runs off this bot's own
		// buildings plus what BotFogMemory remembers of the enemy - never the live
		// enemy actor list the donor enumerated.
		// ---------------------------------------------------------------------

		// Throttled: recomputing this per query (a flood + enemy-building scan per chokepoint) caused frame
		// spikes, because the base builder queries topology very frequently. Usefulness is base-relative and
		// changes slowly. Pure read of the last completed snapshot; the refresh runs incrementally below.
		public IReadOnlyList<ZoneChokepoint> GetUsefulChokepoints() => usefulChokepoints;

		// Advances the incremental 'useful' refresh by one chunk. Called from BotTick (sim thread) so the cost of the
		// per-chokepoint flood is spread over several ticks instead of bursting every UsefulRefreshInterval ticks.
		void TickUsefulRefresh()
		{
			if (chokepoints.Count == 0)
				return;

			if (usefulCursor < 0)
			{
				// Idle: start a new pass once the interval has elapsed.
				if (world.WorldTick < usefulNextRefreshTick)
					return;

				var reference = GetOwnBaseReference();
				if (reference == null)
				{
					usefulNextRefreshTick = world.WorldTick + Math.Max(1, Info.UsefulRefreshInterval);
					return;
				}

				// One remembered-buildings pass, not two: the count pre-check and the position set are the
				// same filter. (Donor: one world.Actors pass, live. Here the fog memory tables do the
				// walking - this stays a small dictionary read.)
				var enemyCells = RememberedEnemyBuildingCells();

				// Skip if neither our base nor the remembered enemy building count changed since the last
				// completed scan.
				if (!BaseMoved(reference.Value, usefulLastBaseRef) && !EnemyBuildingCountChanged(enemyCells.Count, usefulLastEnemyCount))
				{
					usefulNextRefreshTick = world.WorldTick + Math.Max(1, Info.UsefulRefreshInterval);
					return;
				}

				usefulLastBaseRef = reference.Value;
				usefulLastEnemyCount = enemyCells.Count;
				usefulReference = reference.Value;
				usefulDomain = DomainOf(usefulReference);
				usefulEnemyBuildings = enemyCells;
				usefulBuilding.Clear();
				usefulCursor = 0;
			}

			var end = Math.Min(chokepoints.Count, usefulCursor + Math.Max(1, Info.UsefulChunkSize));
			for (; usefulCursor < end; usefulCursor++)
			{
				var cp = chokepoints[usefulCursor];
				if (cp.Domain != usefulDomain)
					continue;

				if (HasRealAccessBeyond(usefulReference, cp, usefulEnemyBuildings))
					usefulBuilding.Add(cp);
			}

			if (usefulCursor >= chokepoints.Count)
			{
				usefulChokepoints.Clear();
				usefulChokepoints.AddRange(usefulBuilding);
				usefulCursor = -1;
				usefulNextRefreshTick = world.WorldTick + Math.Max(1, Info.UsefulRefreshInterval);
			}
		}

		bool HasRealAccessBeyond(CPos reference, ZoneChokepoint cp, HashSet<CPos> enemyBuildings)
		{
			var hasEnemyBuildings = enemyBuildings.Count > 0;
			var beyondLimit = Math.Max(1, Info.MinimumChokepointBeyondCells);
			var forward = cp.Cell - reference;
			if (forward.LengthSquared == 0)
				return true;

			// Block the local pinch line (perpendicular to the approach, extended until impassable) so the flood cannot
			// wrap around the chokepoint back to the base side. Otherwise a coastal nook / dead end always looks "open".
			var perp = Math.Abs(forward.X) < Math.Abs(forward.Y) ? new CVec(1, 0) : new CVec(0, 1);
			const int MaxPinch = 16;
			var barrier = new HashSet<CPos> { cp.Cell };
			foreach (var sign in new[] { 1, -1 })
			{
				for (var k = 1; k <= MaxPinch; k++)
				{
					var c = cp.Cell + perp * (sign * k);
					if (!world.Map.Contains(c) || !IsPassable(c))
						break;

					barrier.Add(c);
				}
			}

			var seeds = new List<CPos>();
			if (forward.X != 0)
				seeds.Add(cp.Cell + new CVec(Math.Sign(forward.X), 0));
			if (forward.Y != 0)
				seeds.Add(cp.Cell + new CVec(0, Math.Sign(forward.Y)));
			if (forward.X != 0 && forward.Y != 0)
				seeds.Add(cp.Cell + new CVec(Math.Sign(forward.X), Math.Sign(forward.Y)));

			var queue = new Queue<CPos>();
			var visited = new HashSet<CPos>(barrier);
			foreach (var seed in seeds)
			{
				if (!world.Map.Contains(seed) || !IsPassable(seed) || !visited.Add(seed))
					continue;

				queue.Enqueue(seed);
			}

			var farCount = 0;
			var cellCap = Math.Max(beyondLimit, Info.FloodFillCellCap);
			while (queue.Count > 0)
			{
				var cell = queue.Dequeue();
				if (hasEnemyBuildings && enemyBuildings.Contains(cell))
					return true;

				farCount++;
				if (!hasEnemyBuildings && farCount >= beyondLimit)
					return true;

				// Hard safety cap: with remembered enemy buildings present, there is otherwise no bound - a
				// chokepoint whose reachable region doesn't happen to contain one would flood the entire
				// region before giving up.
				if (farCount >= cellCap)
					return false;

				foreach (var dir in CVec.Directions)
				{
					var next = cell + dir;
					if (!world.Map.Contains(next) || !IsPassable(next) || !visited.Add(next))
						continue;

					queue.Enqueue(next);
				}
			}

			return false;
		}

		/// <summary>Chokepoints reachable from the reference, as defensive placement threats (proactive, static).</summary>
		public IEnumerable<ZoneDefenseThreat> GetTopologyHotspots(CPos reference)
		{
			EnsureBuilt();
			if (chokepoints.Count == 0)
				return [];

			var maxDistSq = Math.Max(1, Info.TopologyMaxDistance) * Math.Max(1, Info.TopologyMaxDistance);

			return GetUsefulChokepoints()
				.Select(c => (Chokepoint: c, DistSq: (c.Cell - reference).LengthSquared))
				.Where(c => c.DistSq <= maxDistSq)
				.OrderByDescending(c => c.Chokepoint.BaseWeight - c.DistSq / 16)
				.Take(Math.Max(1, Info.MaxTopologyHotspots))
				.Select(c => new ZoneDefenseThreat(c.Chokepoint.Cell, c.Chokepoint.BaseWeight))
				.ToArray();
		}

		/// <summary>
		/// Territory doors as defensive placement threats, weighted by ground behind rather than by type.
		/// Deliberately territory-wide, not per-base like <see cref="GetTopologyHotspots"/> - a door does not
		/// belong to whichever base happens to be nearest it, and re-ranking the same small door list by
		/// distance to each base in turn is exactly the per-base scatter this was built to stop.
		/// </summary>
		/// <param name="coverage">
		/// How many of the bot's own defence structures already cover a door, or null to weight purely by
		/// what lies behind it. Supplied by the caller rather than read here, because which actor types
		/// count as defence is the base builder's business and this module has no notion of it.
		/// </param>
		public IReadOnlyList<ZoneDefenseThreat> GetDoorHotspots(
			Func<ZoneTerritoryDoor, int> coverage = null)
		{
			var territoryDoors = TerritoryDoors;
			if (territoryDoors.Count == 0)
				return [];

			var cap = Math.Max(1, Info.DoorBeyondCellCap);
			var minBeyond = Math.Min(cap, Math.Max(0, Info.MinDoorGroundBeyond));
			var floor = Info.PassageWeight;
			var ceiling = Math.Max(floor, Info.DoorDefenseWeight);

			return territoryDoors
				.Select(d =>
				{
					var weight = DoorWeight(d.GroundBeyond, minBeyond, cap, floor, ceiling);

					// Ground behind the door says how much it is worth holding; it says nothing about
					// whether it is already held. Without this the weight never moves, so the widest door
					// keeps winning the budget after it is covered and the second one never gets a turret -
					// the defence piles up in one place instead of closing the line, which is the same
					// failure this whole feature was built to end, one level in.
					// Need scales with width, because a fifteen-cell gap is not held by what holds a four-
					// cell one. A fully covered door falls to zero and drops out of the ranking until
					// something is lost there.
					if (coverage != null)
						weight = CoverageScaledDoorWeight(weight, d.Width, coverage(d), Info.DoorCellsPerDefense);

					return new ZoneDefenseThreat(d.Center, weight);
				})
				.ToArray();
		}

		// The door's defence weight from what lies behind it: PassageWeight at the qualifying floor
		// (MinDoorGroundBeyond) up to DoorDefenseWeight at "wide open" (DoorBeyondCellCap). Extracted pure
		// for the tests; minBeyond >= cap collapses the scale to the ceiling.
		internal static int DoorWeight(int groundBeyond, int minBeyond, int cap, int floor, int ceiling)
		{
			var beyond = Math.Min(groundBeyond, cap);
			return minBeyond >= cap
				? ceiling
				: floor + (ceiling - floor) * (beyond - minBeyond) / (cap - minBeyond);
		}

		// Need scales with width: 1 + Width/DoorCellsPerDefense structures hold a door, and a fully covered
		// one drops out of the ranking (weight -> 0) until something is lost there.
		internal static int CoverageScaledDoorWeight(int weight, int width, int covered, int cellsPerDefense)
		{
			var required = 1 + width / Math.Max(1, cellsPerDefense);
			return weight * (required - Math.Clamp(covered, 0, required)) / required;
		}

		/// <summary>
		/// Positions behind a territory door, facing the approach - same shape as
		/// <see cref="GetChokepointDefenseAnchors"/>, but the axis and side are already known from the door
		/// itself instead of having to be resigned against a reference each call.
		/// </summary>
		public IReadOnlyList<CPos> GetDoorDefenseAnchors()
		{
			var anchors = new List<CPos>();
			foreach (var door in TerritoryDoors)
			{
				if (door.Outward == CVec.Zero)
					continue;

				var approach = DoorApproachAxis(door);
				var lateral = new CVec(-approach.Y, approach.X);
				var behind = door.Center - approach * 3; // same offset GetChokepointDefenseAnchors uses

				foreach (var offset in new[] { 0, -2, 2, -4, 4 })
					anchors.Add(behind + lateral * offset);
			}

			return anchors;
		}

		// Doors are axis-aligned corridors (see ResolveChokepointCorridors), so Outward - summed over every
		// cell in the run in MakeDoor - stays dominated by one axis even though it is not unit length itself.
		public static CVec DoorApproachAxis(ZoneTerritoryDoor door) =>
			Math.Abs(door.Outward.X) < Math.Abs(door.Outward.Y)
				? new CVec(0, Math.Sign(door.Outward.Y))
				: new CVec(Math.Sign(door.Outward.X), 0);

		/// <summary>
		/// A band of cells behind a territory door - candidate wall cells for a set-back "kill zone", as
		/// opposed to sealing the door itself. Half of an annulus centered on the door, kept only on the
		/// territory side (opposite Outward) so the door stays passable and the zone's open side faces it.
		/// No radius parameter - always Info.DoorKillZoneRadius, so wall placement and the debug overlay can
		/// never disagree on which radius is in play.
		/// </summary>
		public IReadOnlyList<CPos> GetDoorKillZoneCells(ZoneTerritoryDoor door)
		{
			var radius = Math.Max(1, Info.DoorKillZoneRadius);
			if (door.Outward == CVec.Zero)
				return [];

			var approach = DoorApproachAxis(door);
			var band = Math.Min(radius - 1, 2);
			var cells = new List<CPos>();
			foreach (var cell in world.Map.FindTilesInAnnulus(door.Center, radius - band, radius))
			{
				var delta = cell - door.Center;
				var behind = approach.X != 0
					? Math.Sign(delta.X) != Math.Sign(approach.X)
					: Math.Sign(delta.Y) != Math.Sign(approach.Y);
				if (behind)
					cells.Add(cell);
			}

			return cells;
		}

		/// <summary>Bearings (from reference) toward each reachable access point, for the sealed-flank penalty.</summary>
		public IReadOnlyList<CVec> GetAccessBearings(CPos reference)
		{
			EnsureBuilt();
			if (chokepoints.Count == 0)
				return [];

			return GetUsefulChokepoints()
				.Select(c => c.Cell - reference)
				.Where(v => v.LengthSquared > 0)
				.ToList();
		}

		// Pure reads for the debug overlay (render thread): never build or recompute - just read what the sim produced.
		public IReadOnlyList<ZoneChokepoint> ChokepointsForOverlay() => chokepoints;
		public IReadOnlyList<ZoneChokepoint> UsefulForOverlay() => usefulChokepoints;

		// The chokepoints this bot actually acts on (reachable from its base and leading to a real region, not a
		// dead end). Used by the debug overlay to distinguish "detected" from "acted-on".
		public IReadOnlyList<ZoneChokepoint> GetUsefulChokepointsForOwnBase()
		{
			EnsureBuilt();
			return GetUsefulChokepoints();
		}

		CPos? GetOwnBaseReference()
		{
			// Own buildings only: the bot always knows its own (fog hides the enemy, not us), so this
			// enumeration stays live and is identical to the donor's.
			var sumX = 0L;
			var sumY = 0L;
			var n = 0;
			foreach (var a in world.Actors)
			{
				if (a.IsDead || !a.IsInWorld || a.Owner != player || !a.Info.HasTraitInfo<BuildingInfo>())
					continue;

				sumX += a.Location.X;
				sumY += a.Location.Y;
				n++;
			}

			return n == 0 ? null : new CPos((int)(sumX / n), (int)(sumY / n));
		}

		// True if the base centroid has drifted far enough from the last completed scan to be a genuine
		// relocation (new main base, lost conyard) rather than the normal jitter from adding/losing a building.
		bool BaseMoved(CPos current, CPos? last)
		{
			if (last == null)
				return true;

			var threshold = Math.Max(0, Info.BaseMoveThreshold);
			return (current - last.Value).LengthSquared > threshold * threshold;
		}

		// Same idea as BaseMoved: ignore the normal churn of individual buildings gained/lost during combat -
		// here: sightings gained/forgotten - and only treat it as a real change once it drifts far enough to
		// plausibly affect reachability. ZG-b reads the REMEMBERED count, not the live one.
		bool EnemyBuildingCountChanged(int current, int last)
		{
			if (last < 0)
				return true;

			return Math.Abs(current - last) > Math.Max(0, Info.EnemyBuildingCountTolerance);
		}

		/// <summary>
		/// Passable cliff-edge cells within range of the reference that overlook reachable lower ground.
		/// Turrets here gain the height advantage bonus and use the cliff as a natural wall.
		/// </summary>
		public IReadOnlyList<ZoneHighGroundEdge> GetHighGroundEdges(CPos reference) => highGroundEdges;

		// Incremental refresh on the sim thread: scan a few candidate cells per tick instead of the whole
		// circle (~1000 cells at the default radius) in one go. With one TacticalMapBotModule per bot and
		// no sharing of this base-relative state (unlike the topology graph, which is shared per locomotor),
		// an unchunked scan could land on the same tick for several bots at once in a multi-bot game.
		void TickHighGroundRefresh()
		{
			if (highGroundCursor < 0)
			{
				if (world.WorldTick < highGroundRefreshTick)
					return;

				var reference = GetOwnBaseReference();
				if (reference == null || locomotor == null)
				{
					highGroundRefreshTick = world.WorldTick + Math.Max(1, Info.UsefulRefreshInterval);
					highGroundEdges.Clear();
					return;
				}

				// Base hasn't meaningfully moved since the last completed scan - the result would be identical,
				// so skip re-scanning and just check back next interval.
				if (!BaseMoved(reference.Value, highGroundLastBaseRef))
				{
					highGroundRefreshTick = world.WorldTick + Math.Max(1, Info.UsefulRefreshInterval);
					return;
				}

				highGroundBaseRef = reference.Value;
				highGroundLastBaseRef = reference.Value;
				highGroundBaseHeight = world.Map.Height[highGroundBaseRef];
				highGroundBuilding.Clear();
				highGroundSource.Clear();

				if (highGroundBaseHeight <= Info.HighGroundBaseHeight)
				{
					// Base is not elevated; no height advantage to exploit. Nothing to scan this cycle.
					highGroundEdges.Clear();
					highGroundRefreshTick = world.WorldTick + Math.Max(1, Info.UsefulRefreshInterval);
					return;
				}

				var radius = Math.Max(1, Info.HighGroundScanRadius);
				highGroundSource.AddRange(world.Map.FindTilesInCircle(highGroundBaseRef, radius));
				highGroundCursor = 0;
			}

			var end = Math.Min(highGroundSource.Count, highGroundCursor + Math.Max(1, Info.HighGroundChunkSize));
			for (; highGroundCursor < end; highGroundCursor++)
			{
				var cell = highGroundSource[highGroundCursor];
				if (world.Map.Height[cell] != highGroundBaseHeight || !IsPassable(cell))
					continue;

				// An edge cell borders a strictly lower, enemy-reachable cell: it overlooks the approach.
				CVec outward = default;
				var isEdge = false;
				foreach (var d in CVec.Directions)
				{
					var lower = cell + d;
					if (!world.Map.Contains(lower))
						continue;

					if (world.Map.Height[lower] < highGroundBaseHeight && IsPassable(lower))
					{
						outward = d;
						isEdge = true;
						break;
					}
				}

				if (isEdge)
					highGroundBuilding.Add(new ZoneHighGroundEdge(cell, outward,
						Math.Clamp(highGroundBaseHeight - Info.HighGroundBaseHeight, 0, 4)));
			}

			if (highGroundCursor >= highGroundSource.Count)
			{
				highGroundEdges.Clear();
				highGroundEdges.AddRange(highGroundBuilding);
				highGroundCursor = -1;
				highGroundRefreshTick = world.WorldTick + Math.Max(1, Info.UsefulRefreshInterval);
			}
		}

		/// <summary>
		/// Reachable chokepoints whose passable corridor is narrow enough to plug with a single axis-aligned wall line.
		/// The wall runs perpendicular to the approach; a matching gate goes at the corridor center.
		/// </summary>
		public IReadOnlyList<ZoneGateCorridor> GetSealableCorridors(CPos reference) => sealableCorridors;

		// Incremental refresh on the sim thread: process a few useful chokepoints per tick (the snap search + dead-end
		// flood per chokepoint is the cost), build into corridorBuilding, then swap. Spreads what was a periodic burst.
		void TickCorridorRefresh()
		{
			if (corridorCursor < 0)
			{
				if (world.WorldTick < corridorNextRefreshTick)
					return;

				var reference = GetOwnBaseReference();
				if (reference == null || usefulChokepoints.Count == 0)
				{
					corridorNextRefreshTick = world.WorldTick + Math.Max(1, Info.UsefulRefreshInterval);
					if (usefulChokepoints.Count == 0)
						sealableCorridors.Clear();
					return;
				}

				// Single remembered-buildings pass, as in TickUsefulRefresh.
				var enemyCells = RememberedEnemyBuildingCells();

				if (!BaseMoved(reference.Value, corridorLastBaseRef) && !EnemyBuildingCountChanged(enemyCells.Count, corridorLastEnemyCount))
				{
					corridorNextRefreshTick = world.WorldTick + Math.Max(1, Info.UsefulRefreshInterval);
					return;
				}

				corridorLastBaseRef = reference.Value;
				corridorLastEnemyCount = enemyCells.Count;
				corridorBaseRef = reference.Value;
				corridorEnemy = enemyCells;
				corridorSeen = [];
				corridorBuilding.Clear();
				corridorSource.Clear();
				corridorSource.AddRange(usefulChokepoints); // snapshot, in case the useful set is swapped mid-pass
				corridorCursor = 0;
			}

			var maxWidth = Math.Max(1, Info.ChokepointSealMaxWidth);
			var maxDistSq = Math.Max(1, Info.TopologyMaxDistance) * Math.Max(1, Info.TopologyMaxDistance);
			var snapRadius = Math.Max(0, Info.ChokepointSnapRadius);
			var end = Math.Min(corridorSource.Count, corridorCursor + Math.Max(1, Info.UsefulChunkSize));
			for (; corridorCursor < end; corridorCursor++)
			{
				var cp = corridorSource[corridorCursor];
				if ((cp.Cell - corridorBaseRef).LengthSquared > maxDistSq)
					continue;

				var corridor = FindNarrowestCrossing(cp.Cell, snapRadius, maxWidth);
				if (corridor != null && corridorSeen.Add(corridor.Center)
					&& SealingLeadsSomewhere(corridorBaseRef, corridor, corridorEnemy))
					corridorBuilding.Add(corridor);
			}

			if (corridorCursor >= corridorSource.Count)
			{
				corridorBuilding.Sort((a, b) =>
					(a.Center - corridorBaseRef).LengthSquared.CompareTo((b.Center - corridorBaseRef).LengthSquared));
				sealableCorridors.Clear();
				sealableCorridors.AddRange(corridorBuilding);
				corridorCursor = -1;
				corridorNextRefreshTick = world.WorldTick + Math.Max(1, Info.UsefulRefreshInterval);
			}
		}

		/// <summary>
		/// Candidate defense cells on the base side of sealable chokepoints.
		/// These sit just behind the wall/gate line so turrets cover the forced path instead of blocking it.
		/// </summary>
		public IReadOnlyList<CPos> GetChokepointDefenseAnchors(CPos reference)
		{
			var anchors = new List<CPos>();
			foreach (var corridor in GetSealableCorridors(reference))
			{
				var approachAxis = corridor.WallRunsHorizontal ? new CVec(0, 1) : new CVec(1, 0);
				var lateralAxis = corridor.WallRunsHorizontal ? new CVec(1, 0) : new CVec(0, 1);
				var baseSide = (reference - corridor.Center).LengthSquared > 0
					? Math.Sign(corridor.WallRunsHorizontal ? reference.Y - corridor.Center.Y : reference.X - corridor.Center.X)
					: 0;

				if (baseSide == 0)
					continue;

				var behind = corridor.Center + approachAxis * (baseSide * 3);
				foreach (var offset in new[] { 0, -2, 2, -4, 4 })
				{
					var cell = behind + lateralAxis * offset;
					if (world.Map.Contains(cell) && IsPassable(cell))
						anchors.Add(cell);
				}
			}

			return anchors;
		}

		// True if the far side of the wall line is a genuine region (reaches a remembered enemy building, or is
		// large), rather than a dead-end pocket. The whole wall line is used as a barrier so the flood cannot
		// wrap back to the base side - this is what actually distinguishes "a chokepoint into enemy territory"
		// from "a wall against nothing".
		bool SealingLeadsSomewhere(CPos reference, ZoneGateCorridor corridor, HashSet<CPos> enemyBuildings)
		{
			var approach = corridor.WallRunsHorizontal ? new CVec(0, 1) : new CVec(1, 0);
			var baseSign = Math.Sign(corridor.WallRunsHorizontal
				? reference.Y - corridor.Center.Y
				: reference.X - corridor.Center.X);

			// Base exactly level with the corridor on the approach axis: there is no identifiable far
			// side, so which side the wall would seal is undefined. Reject instead of accepting - this
			// used to return true while GetChokepointDefenseAnchors skipped the very same corridor on
			// the same condition, producing corridors marked sealable that never got a turret behind them.
			if (baseSign == 0)
				return false;

			var farSeed = corridor.Center - approach * baseSign;
			var barrier = new HashSet<CPos>(corridor.Cells);
			if (!world.Map.Contains(farSeed) || !IsPassable(farSeed) || barrier.Contains(farSeed))
				return false;

			var hasEnemy = enemyBuildings.Count > 0;
			var limit = Math.Max(1, Info.MinimumChokepointBeyondCells);

			var visited = new HashSet<CPos>(barrier) { farSeed };
			var queue = new Queue<CPos>();
			queue.Enqueue(farSeed);
			var count = 0;
			while (queue.Count > 0)
			{
				var cell = queue.Dequeue();
				if (hasEnemy && enemyBuildings.Contains(cell))
					return true;

				if (++count >= limit)
					return true;

				foreach (var dir in CVec.Directions)
				{
					var next = cell + dir;
					if (!world.Map.Contains(next) || !IsPassable(next) || !visited.Add(next))
						continue;

					queue.Enqueue(next);
				}
			}

			return false;
		}

		/// <summary>
		/// Resolves every scanned chokepoint to its genuine wall-to-wall corridor via
		/// <see cref="FindNarrowestCrossing"/> and folds each into <paramref name="gate"/> at full width.
		/// A chokepoint that fails to resolve to a real corridor (no thick shoulder in reach) still blocks
		/// its own coarse cell, so the region cut cannot pass straight through a marker that turned out to
		/// be unresolvable.
		/// </summary>
		List<ZoneGateCorridor> ResolveChokepointCorridors(HashSet<CPos> gate)
		{
			var corridors = new List<ZoneGateCorridor>();
			var seenCenters = new HashSet<CPos>();
			var snapRadius = Math.Max(0, Info.ChokepointSnapRadius);
			var maxWidth = Math.Max(1, Info.MaxGateWidth) + 1;

			foreach (var cp in chokepoints)
			{
				var corridor = FindNarrowestCrossing(cp.Cell, snapRadius, maxWidth);
				if (corridor == null)
				{
					gate.Add(cp.Cell);
					continue;
				}

				gate.UnionWith(corridor.Cells);
				if (seenCenters.Add(corridor.Center))
					corridors.Add(corridor);
			}

			return corridors;
		}

		// Searches near the coarse chokepoint cell for the narrowest passable crossing that is a genuine bottleneck:
		// bounded by thick (>=2 cell) impassable shoulders on both sides AND open along the approach axis.
		// This stops a single rock in open ground (or a wide field) from being mistaken for a sealable chokepoint.
		// Public: ZG-b also uses it to search for a narrower fallback pinch behind a door that is a poor line to hold.
		public ZoneGateCorridor FindNarrowestCrossing(CPos near, int snapRadius, int maxWidth)
		{
			ZoneGateCorridor best = null;
			var bestWidth = int.MaxValue;

			foreach (var center in world.Map.FindTilesInCircle(near, snapRadius))
			{
				if (!IsPassable(center))
					continue;

				for (var axis = 0; axis < 2; axis++)
				{
					var wallRunsHorizontal = axis == 0;
					var step = wallRunsHorizontal ? new CVec(1, 0) : new CVec(0, 1);

					// A real passage is open along the approach (perpendicular) axis on both sides of the line.
					var approach = wallRunsHorizontal ? new CVec(0, 1) : new CVec(1, 0);
					if (!IsPassable(center + approach) || !IsPassable(center - approach))
						continue;

					var cells = new List<CPos> { center };
					if (!WalkToShoulder(center, step, maxWidth, cells) || !WalkToShoulder(center, -step, maxWidth, cells))
						continue;

					if (cells.Count <= maxWidth && cells.Count < bestWidth)
					{
						bestWidth = cells.Count;
						best = new ZoneGateCorridor(center, wallRunsHorizontal, cells.ToArray());
					}
				}
			}

			return best;
		}

		// Walks passable cells from origin along step. Succeeds only at a *thick* shoulder (>=2 impassable cells or the
		// map edge), so a single isolated obstacle in open ground is not mistaken for a wall of a chokepoint.
		bool WalkToShoulder(CPos origin, CVec step, int maxWidth, List<CPos> into)
		{
			for (var i = 1; i <= maxWidth; i++)
			{
				var cell = origin + step * i;
				if (!IsPassable(cell))
				{
					var beyond = origin + step * (i + 1);
					return !world.Map.Contains(beyond) || !IsPassable(beyond);
				}

				into.Add(cell);
			}

			return false;
		}

		#region Territory and doors

		readonly HashSet<CPos> territory = [];
		readonly List<ZoneTerritoryDoor> doors = [];
		readonly List<CPos> territoryWall = [];
		readonly List<CPos> territoryFront = [];
		readonly HashSet<CPos> horizon = [];
		int territoryNextRefreshTick;
		CPos? territoryLastBaseRef;
		int territoryLastEnemyCount = -1;

		// Which measurement answered "how much ground does this door open onto" - counted per rebuild and
		// reported in the funnel log, for the same reason every other stage of that funnel is: a door
		// inside our own ground cannot be measured the normal way, and which fallback answered for it is
		// not something to work out from a single number on the overlay.
		int doorsMeasuredByRegion;
		int doorsMeasuredByPinch;
		int doorsUnmeasured;

		// ZG-b divergence: the donor's ownership tally lived on the SHARED topology (CNSharedTopology.
		// RegionOwners) because every omniscient bot computed the identical answer. Under fog each bot
		// believes differently, so this is per-bot: parallel to `regions`, null = unclaimed/contested/
		// never-seen, refreshed by TickRegionOwnershipRefresh on this bot's own (de-phased) clock.
		OpenRA.Player[] regionOwners = [];
		int regionOwnershipNextRefreshTick;

		/// <summary>
		/// Ground this bot BELIEVES it holds: closer to its own buildings than to any remembered enemy
		/// one. (Donor raced against live enemy buildings; see RebuildTerritory.)
		/// </summary>
		public IReadOnlyCollection<CPos> Territory { get { EnsureBuilt(); return territory; } }

		/// <summary>
		/// Whether a cell is inside this bot's believed claim. Separate from <see cref="Territory"/> because
		/// the collection it hands back is read as an interface, and a caller testing thousands of
		/// candidate cells against it would walk the whole claim per cell instead of hashing once.
		/// </summary>
		public bool IsInTerritory(CPos cell) { EnsureBuilt(); return territory.Contains(cell); }

		/// <summary>The believed ways into that ground. Everything else along its edge is terrain doing the work.</summary>
		public IReadOnlyList<ZoneTerritoryDoor> TerritoryDoors { get { EnsureBuilt(); return doors; } }

		/// <summary>
		/// The ways into the region containing a cell. Unlike <see cref="TerritoryDoors"/> this is not
		/// about anyone's claim, so it answers the question for ground the caller does not hold - which is
		/// what an attacker needs, and what makes it work against a human opponent who has no bot module to
		/// ask. (Donor's GetRegionDoorsAt; renamed to match the gate-corridor vocabulary.)
		/// </summary>
		public IReadOnlyList<ZoneGateCorridor> GetRegionGatesAt(CPos cell)
		{
			EnsureBuilt();

			var regionId = RegionIdAt(cell);
			if (regionId < 0 || regionId >= regions.Count)
				return [];

			var gates = new List<ZoneGateCorridor>();
			foreach (var index in regions[regionId].GateCorridorIndices)
			{
				var corridor = GetRegionGateCorridor(index);
				if (corridor != null)
					gates.Add(corridor);
			}

			return gates;
		}

		/// <summary>Edge cells backed by cliff, water or map edge - free wall, nothing to build there.</summary>
		public IReadOnlyList<CPos> GetTerritoryWall() { EnsureBuilt(); return territoryWall; }

		/// <summary>Edge cells open to the (remembered) enemy, or too wide to plug. Held with an army, not with turrets.</summary>
		public IReadOnlyList<CPos> GetTerritoryFront() { EnsureBuilt(); return territoryFront; }

		// Read-only views for the render thread. Deliberately without EnsureBuilt: the overlay must never
		// trigger a topology build from render-prepare, which is what used to cause periodic spikes.
		public IReadOnlyCollection<CPos> TerritoryForOverlay() => territory;
		public IReadOnlyList<ZoneTerritoryDoor> DoorsForOverlay() => doors;
		public IReadOnlyList<CPos> TerritoryWallForOverlay() => territoryWall;
		public IReadOnlyList<CPos> TerritoryFrontForOverlay() => territoryFront;

		void TickTerritoryRefresh()
		{
			if (world.WorldTick < territoryNextRefreshTick)
				return;

			territoryNextRefreshTick = world.WorldTick + Math.Max(1, Info.TerritoryRefreshInterval);

			var reference = GetOwnBaseReference();
			if (reference == null)
				return;

			var enemyCells = RememberedEnemyBuildingCells();

			// Same guard the chokepoint refresh uses: individual sightings coming and going during a fight
			// do not move an edge, and rebuilding on every one of them would be the expensive way to
			// compute the same answer.
			if (!BaseMoved(reference.Value, territoryLastBaseRef) && !EnemyBuildingCountChanged(enemyCells.Count, territoryLastEnemyCount))
				return;

			territoryLastBaseRef = reference.Value;
			territoryLastEnemyCount = enemyCells.Count;

			RebuildTerritory(enemyCells);
		}

		/// <summary>
		/// Region ownership as a cheap, periodically-refreshed tally over the (rarely-changing) region
		/// shape. ZG-b divergence: the donor tallied EVERY player's buildings off one live
		/// <c>world.Actors</c> scan into the shared topology - omniscient, identical for every bot.
		/// Under fog that is cheating, so this tallies what this bot can honestly claim to know: its own
		/// buildings (always known) plus REMEMBERED enemy buildings (BotFogMemory via the situation).
		/// An enemy never scouted claims nothing; its regions stay null rather than being quietly stolen.
		/// Allied and neutral buildings are not remembered either, so they tally nothing here - the
		/// donor counted them, this cannot see them.
		/// </summary>
		void TickRegionOwnershipRefresh()
		{
			if (regions.Count == 0 || world.WorldTick < regionOwnershipNextRefreshTick)
				return;

			regionOwnershipNextRefreshTick = world.WorldTick + Math.Max(1, Info.RegionOwnershipRefreshInterval);

			var tally = new Dictionary<int, Dictionary<OpenRA.Player, int>>();

			void Count(CPos cell, OpenRA.Player owner)
			{
				var regionId = RegionIdAt(cell);
				if (regionId < 0)
					return;

				if (!tally.TryGetValue(regionId, out var byPlayer))
					tally[regionId] = byPlayer = [];

				byPlayer[owner] = byPlayer.GetValueOrDefault(owner) + 1;
			}

			// Own buildings: the bot always knows its own (fog hides the enemy, not us).
			foreach (var a in world.Actors)
			{
				if (a.IsDead || !a.IsInWorld || a.Owner != player || !a.Info.HasTraitInfo<BuildingInfo>())
					continue;

				Count(a.Location, player);
			}

			// Enemy buildings: BELIEF - what this bot has seen and still remembers, not what stands there.
			var situation = player.PlayerActor.TraitOrDefault<MasterAiBotModule>()?.Situation;
			if (situation?.Enemies != null)
				foreach (var enemy in situation.Enemies.Keys)
					foreach (var seen in situation.Remembered(enemy))
						if (seen.Building)
							Count(seen.Location, enemy);

			regionOwners = TallyOwners(regions.Count, tally);
		}

		// A clear majority, or nobody. OrderByDescending().First() handed the region to whoever the
		// dictionary happened to enumerate first when two players had the same number of buildings -
		// so a frontier region with one building each was declared held, which reads downstream as
		// "this neighbour belongs to an enemy" and steers Military roles, attack choice and expansion
		// off a coin toss. RegionOwner documents null as contested; this makes that true.
		// One pass instead of a sort, which also drops the per-region allocation. Generic over the
		// owner key so the tests can drive it without a World.
		internal static T[] TallyOwners<T>(int regionCount, IReadOnlyDictionary<int, Dictionary<T, int>> tally) where T : class
		{
			var owners = new T[regionCount];
			foreach (var (regionId, byOwner) in tally)
			{
				// The tally was built against this cut's ids, but a cell on a gate/barrier can still
				// produce a stray id when the regions were re-cut mid-refresh - guard, don't trust.
				if (regionId < 0 || regionId >= regionCount)
					continue;

				T leader = null;
				var best = 0;
				var tied = false;

				foreach (var (owner, count) in byOwner)
				{
					if (count > best)
					{
						best = count;
						leader = owner;
						tied = false;
					}
					else if (count == best)
						tied = true;
				}

				owners[regionId] = tied ? null : leader;
			}

			return owners;
		}

		/// <summary>
		/// Claims ground for this player, then reads its edge.
		/// <para>
		/// Ownership is settled by a race rather than by distance: own buildings and REMEMBERED enemy
		/// buildings (the donor seeded live ones) are all seeded into one breadth-first walk, and
		/// whichever side reaches a cell first keeps it. That follows the ground - a cell ten cells
		/// away across a cliff belongs to whoever can actually get there - which is the whole point
		/// of doing this on the map instead of on a circle.
		/// </para>
		/// </summary>
		void RebuildTerritory(HashSet<CPos> enemyCells)
		{
			territory.Clear();
			doors.Clear();
			territoryWall.Clear();
			territoryFront.Clear();

			var ownCells = OwnBuildingCells();
			if (ownCells.Count == 0)
				return;

			// Chokepoints hold the walk like walls. That is what makes a territory a place rather than a
			// blob: ground is enclosed by cliffs and by the handful of gaps in them, and a claim that runs
			// straight through those gaps describes nothing anybody would defend.
			//
			// It also puts the doors on the boundary by construction. Three earlier attempts tried to cut
			// them back out of a claim that had already flowed past them, and each failed differently.
			//
			// The gate has to be the chokepoint's full width, not just its coarse marker cell - blocking
			// only the one cell let the walk leak around anything wider than a single file, which is what
			// fragmented one real gap into a chain of several ragged "doors" a cell or two apart. The width
			// is exactly what ZoneGateCorridor already resolves, so it is looked up once here and reused
			// for both the gate and, in BuildDoors, the door itself.
			var gate = new HashSet<CPos>();
			var chokepointCorridors = ResolveChokepointCorridors(gate);

			var mine = new HashSet<CPos>();
			var theirs = new HashSet<CPos>();
			var claimed = new HashSet<CPos>();
			var queue = new Queue<(CPos Cell, bool Mine, int Dist)>();

			foreach (var cell in ownCells)
				if (world.Map.Contains(cell) && claimed.Add(cell))
				{
					mine.Add(cell);
					queue.Enqueue((cell, true, 0));
				}

			foreach (var cell in enemyCells)
				if (world.Map.Contains(cell) && claimed.Add(cell))
				{
					theirs.Add(cell);
					queue.Enqueue((cell, false, 0));
				}

			// Without a remembered enemy there is no race to lose, so the claim has to be bounded by
			// something else or it swallows the map.
			var unopposedLimit = enemyCells.Count == 0 ? Math.Max(1, Info.TerritoryUnopposedRadius) : int.MaxValue;
			var cap = Math.Max(1, Info.TerritoryCellCap);

			// Where the walk ran out of budget rather than out of ground. This edge is an artefact of the
			// bound, not a feature of the map, and reading it as one produced a "door" sixty cells wide
			// with the rest of the map behind it - the outside of a circle is open in every direction.
			horizon.Clear();

			while (queue.Count > 0)
			{
				var (cell, isMine, dist) = queue.Dequeue();
				if (dist >= unopposedLimit || claimed.Count >= cap)
				{
					if (isMine)
						horizon.Add(cell);

					continue;
				}

				foreach (var dir in CVec.Directions)
				{
					var next = cell + dir;
					if (!world.Map.Contains(next) || !IsPassable(next) || gate.Contains(next) || !claimed.Add(next))
						continue;

					if (isMine)
						mine.Add(next);
					else
						theirs.Add(next);

					queue.Enqueue((next, isMine, dist + 1));
				}
			}

			territory.UnionWith(mine);
			BuildDoors(theirs, chokepointCorridors);
		}

		/// <summary>
		/// Walks the edge of the claimed ground and splits it into what has to be held and what does not.
		/// An edge cell whose outside neighbour is driveable is a way in; one backed by cliff, water or the
		/// map edge is wall we did not have to build.
		/// </summary>
		void BuildDoors(HashSet<CPos> theirs, List<ZoneGateCorridor> chokepointCorridors)
		{
			var doorCells = new HashSet<CPos>();
			doorsMeasuredByRegion = 0;
			doorsMeasuredByPinch = 0;
			doorsUnmeasured = 0;

			foreach (var cell in territory)
			{
				// The bound stopped the walk here, so what lies past this cell was never examined. Reading
				// it as an edge describes the budget, not the map.
				if (horizon.Contains(cell))
					continue;

				var isEdge = false;
				var isDoor = false;
				var isFront = false;

				foreach (var dir in CVec.Directions)
				{
					var next = cell + dir;
					if (territory.Contains(next))
						continue;

					isEdge = true;

					if (!world.Map.Contains(next) || !IsPassable(next))
						continue;

					// Ground the (remembered) enemy claim got to first is a front, not a way in. Nothing
					// about the terrain funnels anything here; it is simply where the two claims met,
					// and it is held with an army rather than with turrets.
					if (theirs.Contains(next))
						isFront = true;
					else
						isDoor = true;
				}

				if (!isEdge)
					continue;

				if (isDoor)
					doorCells.Add(cell);
				else if (isFront)
					territoryFront.Add(cell);
				else
					territoryWall.Add(cell);
			}

			// Chokepoint corridors standing on our own ground are doors in the line we would draw, whether
			// or not they sit on the edge of the claim. A ramp through a cliff in the middle of held
			// territory is exactly what a defence is anchored at, and it never shows up as a boundary cell
			// because both of its sides belong to us. The corridor already covers the chokepoint at full
			// width - it is what gated the walk in RebuildTerritory - so touching it is adjacency against
			// the whole gap, not just its coarse marker cell.
			var chokepointGateCells = new HashSet<CPos>();
			var candidates = new List<ZoneGateCorridor>();
			foreach (var corridor in chokepointCorridors)
			{
				chokepointGateCells.UnionWith(corridor.Cells);

				var touches = false;
				foreach (var cell in corridor.Cells)
				{
					foreach (var dir in CVec.Directions)
					{
						if (!territory.Contains(cell + dir))
							continue;

						touches = true;
						break;
					}

					if (touches)
						break;
				}

				if (touches)
					candidates.Add(corridor);
			}

			var adjacentOnly = candidates.Count;

			// Anything left in doorCells that is not part of a scanned chokepoint is an open edge nothing
			// was recorded for - rare, since the two claims otherwise tile the whole reachable map between
			// them, but resolved through the same lookup rather than left unclassified.
			var runsNoCorridor = 0;
			var snapRadius = Math.Max(0, Info.ChokepointSnapRadius);
			var maxWidth = Math.Max(1, Info.MaxGateWidth) + 1; // MaxGateWidth is the donor's MaxDoorWidth.
			var seenCenters = new HashSet<CPos>(candidates.Select(c => c.Center));
			foreach (var start in doorCells)
			{
				if (chokepointGateCells.Contains(start))
					continue;

				var corridor = FindNarrowestCrossing(start, snapRadius, maxWidth);
				if (corridor == null)
				{
					// No thick shoulder within reach on either axis - nothing here actually funnels anything,
					// so it is front rather than a gate that simply failed to resolve.
					runsNoCorridor++;
					territoryFront.Add(start);
					continue;
				}

				if (seenCenters.Add(corridor.Center))
					candidates.Add(corridor);
			}

			// Doors that sit close together read as one way in to a human, not several lined up in a row -
			// a gap scanned at a couple of slightly different snap points, or two real gaps a few cells
			// apart. Widest first, so the one that actually leads somewhere is what survives the merge
			// rather than whichever happened to be found first.
			candidates.Sort((a, b) => b.Cells.Length.CompareTo(a.Cells.Length));
			var accepted = new List<ZoneGateCorridor>();
			var mergeRadiusSq = Math.Max(0, Info.DoorMergeRadius) * Math.Max(0, Info.DoorMergeRadius);
			var runsMerged = 0;
			foreach (var corridor in candidates)
			{
				var mergedAway = false;
				foreach (var kept in accepted)
				{
					if ((corridor.Center - kept.Center).LengthSquared <= mergeRadiusSq)
					{
						mergedAway = true;
						break;
					}
				}

				if (mergedAway)
					runsMerged++;
				else
					accepted.Add(corridor);
			}

			var runsTooWide = 0;
			var runsTooNarrow = 0;
			var runsTooShallow = 0;
			foreach (var corridor in accepted)
			{
				if (corridor.Cells.Length < Math.Max(1, Info.MinDoorWidth))
				{
					runsTooNarrow++;
					continue;
				}

				// Too wide to be a door (MaxGateWidth = donor's MaxDoorWidth). Terrain is not funnelling
				// anything through a gap this size, and no arrangement of turrets closes it - treat it
				// as front and let an army hold it.
				if (corridor.Cells.Length > Math.Max(1, Info.MaxGateWidth))
				{
					runsTooWide++;
					territoryFront.AddRange(corridor.Cells);
					continue;
				}

				var door = MakeDoor(corridor.Cells.ToList());

				// A pinch that opens onto almost nothing is a dead end, not a way in - the ground behind it
				// has to be worth defending before it counts as one.
				if (door.GroundBeyond < Math.Max(0, Info.MinDoorGroundBeyond))
				{
					runsTooShallow++;
					continue;
				}

				doors.Add(door);
			}

			// Widest first: the door that lets the most through is the one a defence is built at.
			doors.Sort((a, b) => b.GroundBeyond.CompareTo(a.GroundBeyond));

			// Every step of the funnel, because three attempts at this produced no doors and each time the
			// screen could only report the total. Which stage empties the list is not something to keep
			// guessing at.
			CAAIUtils.BotDebug(
				"{0} territory: {1} cells, {2} wall, {3} front, {4} horizon | {5} chokepoints, {6} corridors "
				+ "touching this territory | {7} extra edge cells ({8} no corridor) -> {9} candidates -> "
				+ "{10} merged away -> {11} doors ({12} too wide, {13} too narrow, {14} too shallow) | "
				+ "beyond: {15} raised by region, {16} by pinch, {17} nothing answered",
				player, territory.Count, territoryWall.Count, territoryFront.Count, horizon.Count,
				chokepoints.Count, adjacentOnly,
				doorCells.Count, runsNoCorridor, candidates.Count, runsMerged, doors.Count,
				runsTooWide, runsTooNarrow, runsTooShallow,
				doorsMeasuredByRegion, doorsMeasuredByPinch, doorsUnmeasured);
		}

		ZoneTerritoryDoor MakeDoor(List<CPos> run)
		{
			var sumX = 0;
			var sumY = 0;
			var outward = CVec.Zero;
			var outside = new List<CPos>();

			foreach (var cell in run)
			{
				sumX += cell.X;
				sumY += cell.Y;

				foreach (var dir in CVec.Directions)
				{
					var next = cell + dir;
					if (territory.Contains(next) || !world.Map.Contains(next) || !IsPassable(next))
						continue;

					outward += dir;
					outside.Add(next);
				}
			}

			var mid = new CPos(sumX / run.Count, sumY / run.Count);

			// The centroid of a curved run can fall outside the run itself; the nearest actual cell is what
			// anything downstream wants to aim at.
			var center = run[0];
			var bestSq = int.MaxValue;
			foreach (var cell in run)
			{
				var d = (cell - mid).LengthSquared;
				if (d < bestSq)
				{
					bestSq = d;
					center = cell;
				}
			}

			// Measured from the ground just outside where there is any. That can come to nothing - every
			// candidate already inside the span or the claim, which is what produced "beyond 0" - and a
			// door standing inside our own ground is exactly that case. The regions know what such a door
			// separates without any flooding, so they are asked before falling back to sealing a guessed
			// axis by hand.
			// Gated on "would this answer keep the door" rather than on "is this answer exactly zero".
			// Zero never occurred in practice: a door standing inside our own claim has almost all of its
			// far side already ours, so the flood comes back small - twenty, forty - which is not zero, so
			// neither fallback ran, and the door then died at MinDoorGroundBeyond as too shallow. A played
			// match measured "0 by region" for every bot on the map while ten of one bot's doors were
			// dropped that way, which is the whole case GroundBeyondRegions was written for going unasked.
			// The best answer wins, so a door can only gain ground here, never lose it: anything the flood
			// already measured above the bar keeps exactly the number that was validated by eye.
			var minBeyond = Math.Max(0, Info.MinDoorGroundBeyond);
			var beyond = outside.Count > 0 ? GroundBeyondDoor(run, outside) : 0;

			if (beyond < minBeyond)
			{
				var byRegion = GroundBeyondRegions(run);
				if (byRegion > beyond)
				{
					beyond = byRegion;
					doorsMeasuredByRegion++;
				}
			}

			if (beyond < minBeyond)
			{
				var byPinch = GroundBeyondPinch(center, run);
				if (byPinch > beyond)
				{
					beyond = byPinch;
					doorsMeasuredByPinch++;
				}
				else if (beyond == 0)
					doorsUnmeasured++;
			}

			return new ZoneTerritoryDoor(center, run.ToArray(), outward, beyond);
		}

		/// <summary>
		/// How much ground the door opens onto, measured with the door itself sealed so the flood cannot
		/// simply walk back in through it. Capped: past a point the answer is just "wide open".
		/// </summary>
		int GroundBeyondDoor(List<CPos> run, List<CPos> outside)
		{
			var cap = Math.Max(1, Info.DoorBeyondCellCap);
			var visited = new HashSet<CPos>(run);
			visited.UnionWith(territory);

			var queue = new Queue<CPos>();
			foreach (var cell in outside)
				if (visited.Add(cell))
					queue.Enqueue(cell);

			var count = 0;
			while (queue.Count > 0 && count < cap)
			{
				var cell = queue.Dequeue();
				count++;

				foreach (var dir in CVec.Directions)
				{
					var next = cell + dir;
					if (!world.Map.Contains(next) || !IsPassable(next) || !visited.Add(next))
						continue;

					queue.Enqueue(next);
				}
			}

			return count;
		}

		/// <summary>
		/// Ground behind a door read off the shared region graph rather than flooded for. A door's cells
		/// are a region barrier by construction - <see cref="BuildRegions"/> cuts the map on exactly the
		/// resolved chokepoint corridors doors are made of - so the regions standing against its far side
		/// already know their own size, and nothing has to be walked or sealed by hand. Returns 0 when the
		/// graph cannot answer (the door separates nothing, or our own side of it cannot be identified),
		/// leaving the caller its old fallback.
		/// </summary>
		int GroundBeyondRegions(List<CPos> run)
		{
			if (regionIdByCell == null || regions.Count == 0)
				return 0;

			var nearId = NearestRegionId(territoryLastBaseRef ?? run[0]);
			if (nearId < 0)
				return 0;

			// Two cells out, not one: a ramp's barrier is dilated by a ring in BuildRegions, so the cells
			// immediately beside a ramp door belong to no region at all.
			var beyondIds = new HashSet<int>();
			foreach (var cell in run)
			{
				foreach (var neighbour in world.Map.FindTilesInCircle(cell, 2))
				{
					var id = RegionIdAt(neighbour);
					if (id >= 0 && id != nearId)
						beyondIds.Add(id);
				}
			}

			if (beyondIds.Count == 0)
				return 0;

			// Everything the far side leads on to in turn, with our own region held shut: a door onto a
			// small plateau that itself opens onto the rest of the map is a way in, not a pocket. Capped
			// like the floods are - past a point the answer is simply "wide open".
			var cap = Math.Max(1, Info.DoorBeyondCellCap);
			var visited = new HashSet<int>(beyondIds) { nearId };
			var queue = new Queue<int>(beyondIds);
			var count = 0;
			while (queue.Count > 0 && count < cap)
			{
				var region = regions[queue.Dequeue()];
				count += region.Size;

				foreach (var adjacent in region.AdjacentRegionIds)
					if (visited.Add(adjacent))
						queue.Enqueue(adjacent);
			}

			return Math.Min(count, cap);
		}

		/// <summary>
		/// Ground behind a gap that sits inside our own territory, where "behind" has to be worked out
		/// rather than read off the claim. The pinch is sealed across its narrow axis - the same barrier
		/// the chokepoint scan builds - and the flood starts on the side away from the base. Last resort,
		/// for a door the region graph cannot place: it guesses the axis from the base direction, so a
		/// wide feature can end up sealed the wrong way round.
		/// </summary>
		int GroundBeyondPinch(CPos center, List<CPos> run)
		{
			var reference = territoryLastBaseRef ?? center;
			var forward = center - reference;
			if (forward.LengthSquared == 0)
				return 0;

			// Same sideways reach the chokepoint scan uses, for the same reason: far enough to close a
			// narrow gap, short enough not to wall off open ground.
			const int PinchBarrierReach = 16;

			var perp = Math.Abs(forward.X) < Math.Abs(forward.Y) ? new CVec(1, 0) : new CVec(0, 1);
			var barrier = new HashSet<CPos>(run);
			foreach (var cell in run)
			{
				foreach (var sign in new[] { 1, -1 })
				{
					for (var k = 1; k <= PinchBarrierReach; k++)
					{
						var c = cell + perp * (sign * k);
						if (!world.Map.Contains(c) || !IsPassable(c))
							break;

						barrier.Add(c);
					}
				}
			}

			var seeds = new List<CPos>();
			if (forward.X != 0)
				seeds.Add(center + new CVec(Math.Sign(forward.X), 0));
			if (forward.Y != 0)
				seeds.Add(center + new CVec(0, Math.Sign(forward.Y)));

			var cap = Math.Max(1, Info.DoorBeyondCellCap);
			var visited = new HashSet<CPos>(barrier);
			var queue = new Queue<CPos>();
			foreach (var seed in seeds)
				if (world.Map.Contains(seed) && IsPassable(seed) && visited.Add(seed))
					queue.Enqueue(seed);

			var count = 0;
			while (queue.Count > 0 && count < cap)
			{
				var cell = queue.Dequeue();
				count++;

				foreach (var dir in CVec.Directions)
				{
					var next = cell + dir;
					if (!world.Map.Contains(next) || !IsPassable(next) || !visited.Add(next))
						continue;

					queue.Enqueue(next);
				}
			}

			return count;
		}

		HashSet<CPos> OwnBuildingCells()
		{
			// Own buildings only: fog hides the enemy, never us, so this enumeration stays live and is
			// identical to the donor's.
			var cells = new HashSet<CPos>();
			foreach (var a in world.Actors)
				if (!a.IsDead && a.IsInWorld && a.Owner == player && a.Info.HasTraitInfo<BuildingInfo>())
					cells.Add(a.Location);

			return cells;
		}

		#endregion

		/// <summary>
		/// The enemy building cells this bot can honestly claim to know: remembered sightings only
		/// (<see cref="BotFogMemory"/> merges live sightings with the FrozenActorLayer and forgets
		/// contradicted/timed-out records). Memoised per tick like the donor's EnemyBuildingCells,
		/// because the useful and corridor refreshes can both ask on the same tick.
		/// <para>
		/// FOG DIVERGENCE (donor line ~2964): the donor enumerated
		/// <c>world.ActorsHavingTrait&lt;Building&gt;</c> LIVE - every enemy building whether the bot had
		/// ever seen it or not. Here an enemy base never scouted contributes nothing, so every consumer
		/// degrades to its "no known enemy" branch (unopposed territory claim, beyond-cells fallback)
		/// until the first sighting - that is the intended fog-honest semantics, not an error.
		/// </para>
		/// </summary>
		HashSet<CPos> RememberedEnemyBuildingCells()
		{
			if (enemyBuildingCellsTick == world.WorldTick)
				return enemyBuildingCells;

			enemyBuildingCellsTick = world.WorldTick;
			enemyBuildingCells = [];

			var situation = player.PlayerActor.TraitOrDefault<MasterAiBotModule>()?.Situation;
			if (situation?.Enemies != null)
				foreach (var enemy in situation.Enemies.Keys)
					foreach (var seen in situation.Remembered(enemy))
						if (seen.Building)
							enemyBuildingCells.Add(seen.Location);

			return enemyBuildingCells;
		}

		#region IBotZoneTopology

		/// <inheritdoc/>
		public IReadOnlyList<Zone> Regions
		{
			get
			{
				EnsureBuilt();
				return regions;
			}
		}

		/// <inheritdoc/>
		public IReadOnlyList<ZoneChokepoint> Chokepoints
		{
			get
			{
				EnsureBuilt();
				return chokepoints;
			}
		}

		/// <inheritdoc/>
		public int RegionIdAt(CPos cell) => regionIdByCell != null && world.Map.Contains(cell) ? regionIdByCell[cell] : -1;

		/// <inheritdoc/>
		public int NearestRegionId(CPos cell)
		{
			// A base reference (or a remembered actor) can sit on a gate or ramp cell, which
			// belongs to no region at all - look a couple of cells out before giving up.
			var id = RegionIdAt(cell);
			if (id >= 0)
				return id;

			foreach (var near in world.Map.FindTilesInCircle(cell, 3))
			{
				id = RegionIdAt(near);
				if (id >= 0)
					return id;
			}

			return -1;
		}

		/// <summary>
		/// The generation this bot has ADOPTED, not the one currently published. The two differ for a tick
		/// after a bridge falls: the rebuilding bot publishes at once, while every other bot still answers
		/// <see cref="Regions"/> from the old cut until its own Adopt runs. Reporting the published
		/// number there would tell a caller its cached per-region state was current when it was not - and
		/// since the number then matches for good, the state would never be rebuilt at all.
		/// </summary>
		public int Generation => TopologyReady ? sharedGeneration : -1;

		/// <inheritdoc/>
		public bool IsPassableCell(CPos cell)
		{
			EnsureBuilt();
			return IsPassable(cell);
		}

		/// <inheritdoc/>
		public OpenRA.Player RegionOwner(int regionId) =>
			regionId >= 0 && regionId < regionOwners.Length ? regionOwners[regionId] : null;

		#endregion

		/// <summary>
		/// The corridor a region's <see cref="Zone.GateCorridorIndices"/> entry names, or null when the
		/// index does not resolve. This is how a region's gates get a width: the region itself only
		/// carries the indices.
		/// </summary>
		public ZoneGateCorridor GetRegionGateCorridor(int corridorIndex)
		{
			EnsureBuilt();
			return corridorIndex >= 0 && corridorIndex < regionGateCorridors.Count ? regionGateCorridors[corridorIndex] : null;
		}

		/// <summary>The resolved gate corridors bounding regions, indexed by <see cref="Zone.GateCorridorIndices"/>.</summary>
		public IReadOnlyList<ZoneGateCorridor> RegionGateCorridors
		{
			get
			{
				EnsureBuilt();
				return regionGateCorridors;
			}
		}

		/// <summary>
		/// The cells the region cut ran along: resolved gate corridors plus dilated cliff-ramp pieces.
		/// Read-only view for debugging/overlays: never builds or recomputes, just reads what the sim produced.
		/// </summary>
		public IReadOnlyCollection<CPos> RegionBarrierForOverlay() => regionBarrier;
	}
}
