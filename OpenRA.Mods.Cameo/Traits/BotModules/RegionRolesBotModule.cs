#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System;
using System.Collections.Frozen;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>
	/// This bot's standing on one region: whether it holds it and what the ground is for.
	/// The region's shape is a shared terrain fact (<see cref="Zone"/>); everything here is one
	/// bot's own reading of it and is deliberately not shared. (Port of the donor's CNRegionState.)
	/// </summary>
	public sealed class RegionRoleState
	{
		public readonly int RegionId;

		/// <summary>Held: a construction yard of ours stands here, or enough of our buildings do.</summary>
		public bool Claimed;
		public int ClaimedSinceTick;

		public RegionRole Role;
		public int RoleSinceTick;

		// The three questions the region is scored on, each 0-100, plus the weighted total.
		public int ResourceScore;
		public int SpaceScore;
		public int SecurityScore;
		public int Value;

		public int BuildableCells;
		public int BuildingCapacity;

		/// <summary>Whether the region holds as many of our buildings as its ground is taken to hold.</summary>
		public bool IsFull => BuildingCapacity > 0 && OwnBuildings >= BuildingCapacity;

		/// <summary>Most buildings we have ever had here, and when that last went up.</summary>
		public int PeakBuildings;
		public int LastGrowthTick;

		public int Connections;
		public int SealableDoors;
		public int DoorWidthTotal;
		public int OwnBuildings;
		public int OwnConstructionYards;
		public bool BordersEnemy;

		public RegionRoleState(int regionId)
		{
			RegionId = regionId;
		}
	}

	// CN4 (AI_MASTER_PLAN §3, crystallized-nexus 30cf70a): port of CNRegionManagerBotModule. Tracks which
	// zone-graph regions this bot holds, scores each on resources / buildable space / security, and hands
	// out roles (Core / Economy / Military / Outpost) that steer defence fronts and production placement.
	// Publishes IBotRegionRoles; consumers advise, only this module decides roles.
	//
	// Cameo changes vs the donor:
	//  - Reads OUR topology, not CN's: TacticalMapBotModule implements IBotZoneTopology and carries the
	//    belief layer already (RegionOwner is tallied from own + REMEMBERED enemy buildings — the donor's
	//    tally was omniscient). Adjacency via Zone.AdjacentRegionIds, gate widths via
	//    GetRegionGateCorridor, invalidation via IBotZoneTopology.Generation.
	//  - Building claims come from ActorAdded/ActorRemoved bookkeeping (the DefenseCoveragePlanner
	//    pattern), not a world.Actors scan per refresh.
	//  - MP determinism (architecture §1.6): the donor's LocalRandom refresh offset desyncs the order
	//    stream; the offset here is self.ActorID % interval.
	//  - CNBotPerf/CNBotLog/cntopo overlay dropped: role changes log via Log.Write.
	[TraitLocation(SystemActors.Player)]
	[Desc("Tracks which regions of the map this bot holds and what each held region is for.",
		"Publishes IBotRegionRoles for the defence-front and expansion consumers.")]
	public class RegionRolesBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Actor types that claim a region outright by standing in it.")]
		public readonly FrozenSet<string> ConstructionYardTypes = FrozenSet<string>.Empty;

		[Desc("Buildings of ours in a region that claim it even with no construction yard there — a base whose",
			"yard packed up still holds its ground. 0 means only a construction yard ever claims.")]
		public readonly int ClaimMinimumBuildings = 3;

		[Desc("Ticks between re-reading claims and re-scoring regions.")]
		public readonly int RegionRefreshInterval = 250;

		[Desc("A region keeps a role for at least this many ticks before it can be reassigned. A role decides",
			"what gets defended there, so one that follows the evidence tick by flick leaves half-defended",
			"fronts in both directions.")]
		public readonly int RegionRoleMinimumHoldTicks = 1500;

		[Desc("Resource cells in a region that score a full 100 for resources; above this the score saturates.")]
		public readonly int ResourceCellsForFullScore = 400;

		[Desc("Buildable cells in a region that score a full 100 for space.")]
		public readonly int BuildableCellsForFullScore = 900;

		[Desc("Security lost per region this one connects to. Every neighbour is a way in.")]
		public readonly int ConnectionSecurityPenalty = 12;

		[Desc("Security lost per cell of total sealable-door width. A wide door is a worse door.")]
		public readonly int DoorWidthSecurityPenalty = 3;

		[Desc("Total penalty at which a region scores 50 for security; the score falls off by halves from",
			"there rather than subtracting outright (a straight subtraction floors every multi-door",
			"region at zero, which cannot rank them).")]
		public readonly int SecurityHalfScorePenalty = 60;

		[Desc("Weight of the resource score in a region's overall value.")]
		public readonly int ResourceValueWeight = 100;

		[Desc("Weight of the buildable-space score in a region's overall value.")]
		public readonly int SpaceValueWeight = 60;

		[Desc("Weight of the security score in a region's overall value.")]
		public readonly int SecurityValueWeight = 80;

		[Desc("Resource cells a held region needs before it can be the Economy region.")]
		public readonly int EconomyMinimumResourceCells = 60;

		[Desc("A held region at most this many cells across is an Outpost regardless of what else it scores.")]
		public readonly int OutpostMaximumRegionSize = 400;

		[Desc("Buildable cells a region needs per building it is considered able to hold — a full region",
			"is the signal to expand rather than keep cramming. 0 disables the capacity notion.")]
		public readonly int BuildableCellsPerBuilding = 0;

		public override object Create(ActorInitializer init) { return new RegionRolesBotModule(init.Self, this); }
	}

	public class RegionRolesBotModule : ConditionalTrait<RegionRolesBotModuleInfo>, IBotTick, IBotRegionRoles, INotifyActorDisposing
	{
		readonly World world;
		readonly OpenRA.Player player;

		// Own buildings, kept from the world's add/remove events — no world enumeration.
		readonly HashSet<Actor> buildings = new();

		TacticalMapBotModule tacticalMap;

		// Parallel to the topology's region list, rebuilt whenever Generation changes — region ids are
		// positions in that list and mean nothing across a re-cut (held roles included: a role is a
		// statement about a piece of ground, and after a re-cut nothing says id 4 is that ground).
		RegionRoleState[] states = [];
		int adoptedGeneration = -1;

		int nextRefreshTick;

		// Where this bot started, latched off the first construction yard it ever owns. The Core region is
		// pinned to this rather than to wherever the buildings currently average out, so losing ground does
		// not quietly relabel the main base as something else.
		CPos? homeOrigin;

		public RegionRolesBotModule(Actor self, RegionRolesBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			world.ActorAdded += ActorAdded;
			world.ActorRemoved += ActorRemoved;
		}

		void ActorAdded(Actor a)
		{
			if (a.Owner == player && a.Info.HasTraitInfo<BuildingInfo>())
				buildings.Add(a);
		}

		void ActorRemoved(Actor a) { buildings.Remove(a); }

		void INotifyActorDisposing.Disposing(Actor self)
		{
			world.ActorAdded -= ActorAdded;
			world.ActorRemoved -= ActorRemoved;
		}

		bool IBotRegionRoles.RolesReady => states.Length > 0;

		RegionRole IBotRegionRoles.RoleOf(int regionId) =>
			regionId >= 0 && regionId < states.Length ? states[regionId].Role : RegionRole.None;

		bool IBotRegionRoles.IsHeld(int regionId) =>
			regionId >= 0 && regionId < states.Length && states[regionId].Claimed;

		int IBotRegionRoles.ValueOf(int regionId) =>
			regionId >= 0 && regionId < states.Length ? states[regionId].Value : 0;

		/// <inheritdoc/>
		public RegionRole RoleAtCell(CPos cell)
		{
			if (states.Length == 0 || tacticalMap == null || !tacticalMap.TopologyReady)
				return RegionRole.None;

			var regionId = tacticalMap.NearestRegionId(cell);
			return regionId >= 0 && regionId < states.Length ? states[regionId].Role : RegionRole.None;
		}

		IReadOnlyList<int> IBotRegionRoles.RegionsWithRole(RegionRole role)
		{
			var found = new List<int>();
			foreach (var s in states)
				if (s.Claimed && s.Role == role)
					found.Add(s.RegionId);

			return found;
		}

		void IBotTick.BotTick(IBot bot)
		{
			tacticalMap ??= player.PlayerActor.TraitsImplementing<TacticalMapBotModule>()
				.FirstOrDefault(t => t.IsTraitEnabled());

			if (tacticalMap == null || !tacticalMap.TopologyReady)
				return;

			if (nextRefreshTick == 0)
			{
				// De-phase the refresh deterministically across bots (donor used LocalRandom — a desync
				// hazard for the order stream; ActorID is identical on all clients).
				nextRefreshTick = world.WorldTick + (int)(player.PlayerActor.ActorID % Math.Max(1, Info.RegionRefreshInterval));
				return;
			}

			if (world.WorldTick < nextRefreshTick)
				return;

			nextRefreshTick = world.WorldTick + Math.Max(1, Info.RegionRefreshInterval);
			Refresh();
		}

		void Refresh()
		{
			var regions = tacticalMap.Regions;
			if (regions == null || regions.Count == 0)
				return;

			if (adoptedGeneration != tacticalMap.Generation || states.Length != regions.Count)
			{
				adoptedGeneration = tacticalMap.Generation;
				states = Exts.MakeArray(regions.Count, i => new RegionRoleState(i));
			}

			ReadClaims(regions);
			ScoreRegions(regions);

			var homeRegion = homeOrigin != null ? tacticalMap.NearestRegionId(homeOrigin.Value) : -1;
			AssignRoles(states,
				regions.Select(r => r.Size).ToArray(),
				regions.Select(r => r.ResourceCellCount).ToArray(),
				homeRegion,
				world.WorldTick,
				Math.Max(0, Info.RegionRoleMinimumHoldTicks),
				Math.Max(1, Info.OutpostMaximumRegionSize),
				Info.EconomyMinimumResourceCells,
				out var changed);

			if (changed > 0)
				LogRoles(regions);
		}

		/// <summary>
		/// Counts our own buildings per region in one pass and settles which regions we hold.
		/// </summary>
		void ReadClaims(IReadOnlyList<Zone> regions)
		{
			foreach (var state in states)
			{
				state.OwnBuildings = 0;
				state.OwnConstructionYards = 0;
			}

			foreach (var actor in buildings)
			{
				if (actor.IsDead || !actor.IsInWorld || actor.Owner != player)
					continue;

				var regionId = tacticalMap.NearestRegionId(actor.Location);
				if (regionId < 0 || regionId >= states.Length)
					continue;

				states[regionId].OwnBuildings++;

				if (Info.ConstructionYardTypes.Contains(actor.Info.Name))
				{
					states[regionId].OwnConstructionYards++;
					homeOrigin ??= actor.Location;
				}
			}

			foreach (var state in states)
			{
				if (state.OwnBuildings > state.PeakBuildings)
				{
					state.PeakBuildings = state.OwnBuildings;
					state.LastGrowthTick = world.WorldTick;
				}
			}

			var claimMinimum = Info.ClaimMinimumBuildings;
			for (var i = 0; i < states.Length; i++)
			{
				var state = states[i];
				var claimed = state.OwnConstructionYards > 0
					|| (claimMinimum > 0 && state.OwnBuildings >= claimMinimum);

				if (claimed != state.Claimed)
				{
					state.Claimed = claimed;
					state.ClaimedSinceTick = world.WorldTick;
				}

				// A region we no longer hold steers nothing, so it cannot keep a role either — and it must
				// release the exclusive ones, or losing the Core region would leave the bot unable to name
				// a new one.
				if (!claimed && state.Role != RegionRole.None)
				{
					state.Role = RegionRole.None;
					state.RoleSinceTick = world.WorldTick;
				}

				// Belief, not truth: RegionOwner is tallied from own + remembered enemy buildings — an
				// enemy base never scouted claims nothing, so BordersEnemy stays fog-honest.
				state.BordersEnemy = false;
				foreach (var adjacentId in regions[i].AdjacentRegionIds)
				{
					var owner = tacticalMap.RegionOwner(adjacentId);
					if (owner != null && player.RelationshipWith(owner) == PlayerRelationship.Enemy)
					{
						state.BordersEnemy = true;
						break;
					}
				}
			}
		}

		/// <summary>
		/// Scores every region on the three questions that decide whether it is worth holding: what can be
		/// harvested there, what can be built there, and how many ways in it has. Terrain only — none of it
		/// depends on who owns what, so an unheld region can be scored before anything is committed to it.
		/// </summary>
		void ScoreRegions(IReadOnlyList<Zone> regions)
		{
			var resourceFull = Math.Max(1, Info.ResourceCellsForFullScore);
			var spaceFull = Math.Max(1, Info.BuildableCellsForFullScore);

			for (var i = 0; i < states.Length; i++)
			{
				var region = regions[i];
				var state = states[i];

				state.ResourceScore = Math.Min(100, region.ResourceCellCount * 100 / resourceFull);
				state.SpaceScore = Math.Min(100, region.BuildableCellCount * 100 / spaceFull);
				state.BuildableCells = region.BuildableCellCount;
				state.BuildingCapacity = Info.BuildableCellsPerBuilding > 0
					? region.BuildableCellCount / Info.BuildableCellsPerBuilding
					: 0;

				var widthTotal = 0;
				foreach (var corridorIndex in region.GateCorridorIndices)
				{
					var corridor = tacticalMap.GetRegionGateCorridor(corridorIndex);
					if (corridor != null)
						widthTotal += corridor.Width;
				}

				state.Connections = region.AdjacentRegionIds.Length;
				state.SealableDoors = region.GateCorridorIndices.Length;
				state.DoorWidthTotal = widthTotal;

				state.SecurityScore = SecurityScore(
					state.Connections, widthTotal,
					Info.ConnectionSecurityPenalty, Info.DoorWidthSecurityPenalty,
					Info.SecurityHalfScorePenalty);

				state.Value = ValueScore(
					state.ResourceScore, state.SpaceScore, state.SecurityScore,
					Info.ResourceValueWeight, Info.SpaceValueWeight, Info.SecurityValueWeight);
			}
		}

		// --- world-free helpers (tested) ---

		/// <summary>
		/// Halving, not subtracting: 100 falls off by halves per halfPenalty of total connection + door
		/// penalty, so a sealed pocket reads 100 and multi-door regions still rank instead of flooring
		/// at zero together. (Donor formula, verbatim.)
		/// </summary>
		public static int SecurityScore(int connections, int doorWidthTotal, int connectionPenalty, int doorWidthPenalty, int halfScorePenalty)
		{
			var penalty = connections * Math.Max(0, connectionPenalty)
				+ doorWidthTotal * Math.Max(0, doorWidthPenalty);
			var half = Math.Max(1, halfScorePenalty);
			return 100 * half / (half + penalty);
		}

		/// <summary>The weighted 0-100 region value from its three sub-scores.</summary>
		public static int ValueScore(int resourceScore, int spaceScore, int securityScore, int resourceWeight, int spaceWeight, int securityWeight)
		{
			var totalWeight = resourceWeight + spaceWeight + securityWeight;
			return totalWeight <= 0
				? 0
				: (resourceScore * resourceWeight + spaceScore * spaceWeight + securityScore * securityWeight) / totalWeight;
		}

		/// <summary>
		/// Hands out the roles among held regions. Core and Military are exclusive; Economy and Outpost
		/// are not. A region that has held its role for less than the hold time keeps it, and an
		/// exclusive role still held is not handed out again. Returns the new roles through
		/// <paramref name="states"/> and the change count through <paramref name="changed"/>.
		/// </summary>
		public static void AssignRoles(
			RegionRoleState[] states,
			int[] regionSizes,
			int[] regionResourceCells,
			int homeRegionId,
			int now,
			int holdTicks,
			int outpostMaxSize,
			int economyMinResourceCells,
			out int changed)
		{
			var locked = new bool[states.Length];
			var coreHeld = false;
			var militaryHeld = false;

			for (var i = 0; i < states.Length; i++)
			{
				var state = states[i];
				if (!state.Claimed || state.Role == RegionRole.None)
					continue;

				if (now - state.RoleSinceTick >= holdTicks)
					continue;

				locked[i] = true;
				coreHeld |= state.Role == RegionRole.Core;
				militaryHeld |= state.Role == RegionRole.Military;
			}

			var proposed = new RegionRole[states.Length];
			for (var i = 0; i < states.Length; i++)
				proposed[i] = locked[i] ? states[i].Role : RegionRole.None;

			// Core: where we started, if we still hold it. A bot driven off its starting ground falls back
			// to wherever most of its buildings now are, so there is always exactly one Core.
			if (!coreHeld)
			{
				var coreId = -1;
				if (homeRegionId >= 0 && homeRegionId < states.Length && states[homeRegionId].Claimed)
					coreId = homeRegionId;

				if (coreId < 0)
					coreId = BestUnassigned(proposed, locked, states, s => s.OwnBuildings > 0, s => s.OwnBuildings);

				if (coreId >= 0 && proposed[coreId] != RegionRole.Military)
				{
					// An exclusive role outranks a hold on a non-exclusive one — never at the cost of the
					// OTHER exclusive role, which is a place of its own and not a spare slot.
					proposed[coreId] = RegionRole.Core;
					locked[coreId] = false;
				}
			}

			// Military: held ground that touches an enemy's. Preferring the one that already has buildings
			// keeps the role on a place that can actually take the defence it steers there.
			if (!militaryHeld)
			{
				var militaryId = BestUnassigned(proposed, locked, states, s => s.BordersEnemy, s => s.OwnBuildings * 1000 + s.Value);

				// Same preemption as Core — Core is filled first above so it wins any contest.
				if (militaryId < 0)
					militaryId = BestUnassignedLocked(proposed, states, s => s.BordersEnemy && s.Role != RegionRole.Core,
						s => s.OwnBuildings * 1000 + s.Value);

				if (militaryId >= 0 && proposed[militaryId] != RegionRole.Core)
				{
					proposed[militaryId] = RegionRole.Military;
					locked[militaryId] = false;
				}
			}

			// Economy and Outpost are not exclusive. Outpost is decided first because it is about the
			// ground being too small to be anything else, which no amount of resources in it changes.
			for (var i = 0; i < states.Length; i++)
			{
				if (locked[i] || proposed[i] != RegionRole.None || !states[i].Claimed)
					continue;

				if (regionSizes[i] <= outpostMaxSize)
					proposed[i] = RegionRole.Outpost;
				else if (regionResourceCells[i] >= economyMinResourceCells)
					proposed[i] = RegionRole.Economy;
			}

			changed = 0;
			for (var i = 0; i < states.Length; i++)
			{
				if (states[i].Role == proposed[i])
					continue;

				states[i].Role = proposed[i];
				states[i].RoleSinceTick = now;
				changed++;
			}
		}

		/// <summary>The best claimed, unlocked, still-roleless region passing <paramref name="eligible"/>, ranked by <paramref name="rank"/>; -1 when none.</summary>
		static int BestUnassigned(RegionRole[] proposed, bool[] locked, RegionRoleState[] states,
			Func<RegionRoleState, bool> eligible, Func<RegionRoleState, int> rank)
		{
			var bestId = -1;
			var bestRank = int.MinValue;

			for (var i = 0; i < states.Length; i++)
			{
				if (locked[i] || proposed[i] != RegionRole.None || !states[i].Claimed || !eligible(states[i]))
					continue;

				var value = rank(states[i]);
				if (value <= bestRank)
					continue;

				bestRank = value;
				bestId = i;
			}

			return bestId;
		}

		/// <summary>
		/// The best claimed region for an exclusive role among those currently LOCKED under a
		/// non-exclusive one — reached only when no unlocked candidate exists at all.
		/// </summary>
		static int BestUnassignedLocked(RegionRole[] proposed, RegionRoleState[] states,
			Func<RegionRoleState, bool> eligible, Func<RegionRoleState, int> rank)
		{
			var bestId = -1;
			var bestRank = int.MinValue;

			for (var i = 0; i < states.Length; i++)
			{
				if (!states[i].Claimed || !eligible(states[i]))
					continue;

				if (proposed[i] == RegionRole.Core || proposed[i] == RegionRole.Military)
					continue;

				var value = rank(states[i]);
				if (value <= bestRank)
					continue;

				bestRank = value;
				bestId = i;
			}

			return bestId;
		}

		void LogRoles(IReadOnlyList<Zone> regions)
		{
			var held = states.Where(s => s.Claimed).ToList();
			if (held.Count == 0)
				return;

			var rows = held.Select(s =>
			{
				var cap = s.BuildingCapacity > 0
					? $"/cap{s.BuildingCapacity}" + (s.IsFull ? " FULL" : "")
					: "";
				return $"R{s.RegionId} {s.Role} v{s.Value} (res{s.ResourceScore} spc{s.SpaceScore} sec{s.SecurityScore}; "
					+ $"{s.Connections} conn, {s.SealableDoors} doors w{s.DoorWidthTotal}, {s.OwnBuildings}b{cap}"
					+ (s.BordersEnemy ? ", enemy adj" : "") + ")";
			});
			Log.Write("debug", $"AI ({player.ClientIndex}): REGION ROLES {held.Count} of {regions.Count} held | " + string.Join("  ", rows));
		}
	}
}
