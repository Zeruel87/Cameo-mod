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
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>
	/// IM-1 (docs/design/AI_DEEP_RESEARCH.md §3.3): the read side of the per-region influence
	/// layers. Every list is indexed by the owning <see cref="RegionMemory"/>'s region index —
	/// grid cells, or zone ids when zone-backed — and has <see cref="Count"/> entries.
	/// <see cref="ZoneBacked"/>/<see cref="Generation"/> identify the index space the values were
	/// published in; a consumer holding id-keyed state of its own must never read across a change.
	/// Published read-only on each BotSituation; consumers must not mutate.
	/// </summary>
	public interface IBotInfluenceMap
	{
		/// <summary>Entries per layer — the owning <see cref="RegionMemory"/>'s CellCount at publish.</summary>
		int Count { get; }

		/// <summary>Whether the indices are a zone topology's region ids (vs the square grid).</summary>
		bool ZoneBacked { get; }

		/// <summary>The index-space generation the layers were published under.</summary>
		int Generation { get; }

		/// <summary>Remembered enemy ground threat per region (army + defence value), blended toward the zone's running average as the sighting goes stale.</summary>
		IReadOnlyList<int> ThreatGround { get; }

		/// <summary>Remembered enemy anti-air-capable value per region — the layer air routing pays.</summary>
		IReadOnlyList<int> ThreatAir { get; }

		/// <summary>What a region is worth: its static resource cells plus remembered economy and production/tech building value.</summary>
		IReadOnlyList<int> Interest { get; }

		/// <summary>The bot's own live ground/naval combat value per region — real knowledge, not fogged.</summary>
		IReadOnlyList<int> OwnStrength { get; }

		/// <summary>Ticks since the region's newest sighting across all enemy memories; never-seen regions report tick + the never-seen constant.</summary>
		IReadOnlyList<int> Staleness { get; }

		/// <summary>
		/// Whether these layers answer in <paramref name="regions"/>' index space — same
		/// <see cref="Count"/>, <see cref="ZoneBacked"/> and <see cref="Generation"/>. A consumer
		/// must never read ids across a zone re-cut or a backing switch; always check first.
		/// </summary>
		bool MatchesIndexSpace(RegionMemory regions);
	}

	/// <summary>
	/// IM-1 (docs/design/AI_DEEP_RESEARCH.md §3.3): per-region influence layers, refreshed once
	/// per situation snapshot by the master module — the one publisher (§10.3).
	/// <para>
	/// Fog-honest by construction: every enemy input comes out of <see cref="RegionMemory"/>'s
	/// per-enemy tables, which only ever hold what this bot actually saw (BotFogMemory already
	/// gates visibility); the own-strength layer is real data because the bot's own actors are
	/// its own knowledge. Nothing here ever enumerates enemy actors live.
	/// </para>
	/// <para>
	/// The published threat blends the newest remembered value toward a per-zone EMA
	/// (<c>hist = α·current + (1-α)·hist</c>, α = <see cref="MasterAiBotModuleInfo.InfluenceHistoryAlphaPercent"/>)
	/// as the region goes stale — <c>pub = current·(1-t) + hist·t</c> with
	/// <c>t = min(1, staleness/InfluenceDecayTicks)</c> — so an old sighting reads as "where they
	/// usually are" (§12.3) instead of a frozen snapshot. Unsynced; read and written only from
	/// IBotTick. Live handle: a new snapshot republishes in place.
	/// </para>
	/// </summary>
	internal sealed class BotInfluenceLayers : IBotInfluenceMap
	{
		readonly MasterAiBotModuleInfo info;

		// The (ZoneBacked, Generation, Count) triple this instance last published under — the
		// index space's identity. Any part moving means region ids may name different ground,
		// so every per-index array, EMA history included, is rebuilt rather than aliased.
		int count;
		bool zoneBacked;
		int generation = -1;

		int[] threatGround = [];
		int[] threatAir = [];

		// The published arrays: the blended values after the neighbour-spread pass.
		int[] threatGroundSpread = [];
		int[] threatAirSpread = [];
		int[] interest = [];
		int[] ownStrength = [];
		int[] staleness = [];
		float[] histGround = [];
		float[] histAir = [];

		public BotInfluenceLayers(MasterAiBotModuleInfo info)
		{
			this.info = info;
		}

		public int Count => count;
		public bool ZoneBacked => zoneBacked;
		public int Generation => generation;

		// The published threats are post-spread: each region's blended value plus a share of
		// every neighbour's — a remembered unit's reach crosses the boundary it guards.
		public IReadOnlyList<int> ThreatGround => threatGroundSpread;
		public IReadOnlyList<int> ThreatAir => threatAirSpread;
		public IReadOnlyList<int> Interest => interest;
		public IReadOnlyList<int> OwnStrength => ownStrength;
		public IReadOnlyList<int> Staleness => staleness;

		public bool MatchesIndexSpace(RegionMemory regions)
		{
			return regions != null && count == regions.CellCount &&
				zoneBacked == regions.ZoneBacked && generation == regions.Generation;
		}

		// Internal for tests: the EMA the published threats decay toward.
		internal IReadOnlyList<float> ThreatGroundHistory => histGround;
		internal IReadOnlyList<float> ThreatAirHistory => histAir;

		/// <summary>The EMA step: hist = α·current + (1-α)·hist, written as the stable one-line form.</summary>
		internal static float EmaToward(float current, float history, float alpha)
		{
			return history + alpha * (current - history);
		}

		/// <summary>
		/// The published threat: <paramref name="current"/> while the sighting is fresh,
		/// <paramref name="history"/> once staleness reaches <paramref name="decayTicks"/>,
		/// linear between. A non-positive horizon means fully stale at once.
		/// </summary>
		internal static int BlendWithHistory(int current, float history, int stalenessTicks, int decayTicks)
		{
			var t = decayTicks <= 0 ? 1f : Math.Clamp(stalenessTicks / (float)decayTicks, 0f, 1f);
			return (int)Math.Round(current * (1f - t) + history * t);
		}

		/// <summary>
		/// Republish every layer for this snapshot tick. <paramref name="ownActors"/> is the
		/// master's already-filtered live own-actor list; <paramref name="zones"/> feeds the
		/// static resource cells when <paramref name="regions"/> is zone-backed,
		/// <paramref name="resourceMap"/> is the grid fallback's resource sites (null = remembered
		/// economy only).
		/// </summary>
		internal void Refresh(RegionMemory regions, IEnumerable<Actor> ownActors,
			IBotZoneTopology zones, ResourceMapBotModule resourceMap, int tick)
		{
			EnsureSpace(regions);
			Array.Clear(threatGround, 0, count);
			Array.Clear(threatAir, 0, count);
			Array.Clear(interest, 0, count);
			Array.Clear(ownStrength, 0, count);
			Array.Clear(staleness, 0, count);

			// Static ground value: a zone knows its resource cells directly; the grid falls
			// back to the resource map's field sites, folded onto the region index space.
			if (regions.ZoneBacked)
			{
				if (zones != null)
				{
					var zoneList = zones.Regions;
					for (var i = 0; i < count && i < zoneList.Count; i++)
						interest[i] += zoneList[i].ResourceCellCount;
				}
			}
			else if (resourceMap != null)
			{
				var indexCount = resourceMap.GetIndicesLength();
				for (var i = 0; i < indexCount; i++)
				{
					var indice = resourceMap.GetIndice(i);
					if (indice == null || indice.ResourceCellsCount <= 0)
						continue;

					var index = regions.IndexOf(indice.IndiceCenter);
					if (index >= 0 && index < count)
						interest[index] += indice.ResourceCellsCount;
				}
			}

			// Remembered enemy values and the staleness read — the same per-index max over
			// every enemy's table ScoutBotModule derives inline (never-seen = tick + the
			// never-seen constant; no enemy memory at all reads the same).
			var byEnemy = regions.ByEnemy;
			var neverSeen = tick + Math.Max(0, info.InfluenceStaleAfterTicks);
			for (var i = 0; i < count; i++)
			{
				var stalest = byEnemy.Count == 0 ? neverSeen : 0;
				foreach (var enemyRegions in byEnemy.Values)
				{
					var region = i < enemyRegions.Length ? enemyRegions[i] : null;
					if (region == null)
					{
						stalest = Math.Max(stalest, neverSeen);
						continue;
					}

					threatGround[i] += region.ArmyValue + region.DefenceValue;
					threatAir[i] += region.AntiAirValue;
					interest[i] += region.EconomyValue + region.ProductionTechValue;
					stalest = Math.Max(stalest, region.EverSeen ? tick - region.LastSeenTick : neverSeen);
				}

				staleness[i] = stalest;
			}

			// Own strength is real knowledge, not belief: the bot's live ground/naval combat
			// units (the same classification fog memory's Combat flag uses, minus aircraft —
			// they are the ThreatAir concern, not the ground-holding strength layer).
			if (ownActors != null)
				foreach (var actor in ownActors)
				{
					if (actor == null || actor.IsDead || !actor.IsInWorld)
						continue;

					if (!MasterAiBotModule.IsCombatUnit(actor) || actor.Info.HasTraitInfo<AircraftInfo>())
						continue;

					var index = regions.IndexOf(actor.Location);
					if (index >= 0 && index < count)
						ownStrength[index] += MasterAiBotModule.Value(actor);
				}

			// Decay toward the per-zone average: fold this snapshot's remembered values into
			// the EMA first, then publish the staleness-weighted blend of the two.
			var alpha = Math.Clamp(info.InfluenceHistoryAlphaPercent, 0, 100) / 100f;
			var decayTicks = info.InfluenceDecayTicks;
			for (var i = 0; i < count; i++)
			{
				histGround[i] = EmaToward(threatGround[i], histGround[i], alpha);
				histAir[i] = EmaToward(threatAir[i], histAir[i], alpha);
				threatGround[i] = BlendWithHistory(threatGround[i], histGround[i], staleness[i], decayTicks);
				threatAir[i] = BlendWithHistory(threatAir[i], histAir[i], staleness[i], decayTicks);
			}

			// Spread over the boundary: a remembered unit's weapon reach crosses into the
			// neighbouring regions, so each region publishes its own believed threat plus
			// InfluenceSpreadPercent of every neighbour's (Mark's "spread over the weapon's
			// range" approximated at region granularity — one adjacency hop, not a flood).
			var spreadPercent = Math.Clamp(info.InfluenceSpreadPercent, 0, 100);
			for (var i = 0; i < count; i++)
			{
				var g = threatGround[i];
				var a = threatAir[i];
				if (spreadPercent > 0)
					foreach (var neighbor in regions.NeighborsOf(i))
						if (neighbor >= 0 && neighbor < count)
						{
							g += threatGround[neighbor] * spreadPercent / 100;
							a += threatAir[neighbor] * spreadPercent / 100;
						}

				threatGroundSpread[i] = g;
				threatAirSpread[i] = a;
			}
		}

		// Rebuild every per-index array when the index space moves. History drops with the
		// rest: a generation bump means a zone re-cut reshuffled every id, so an old average
		// describes different ground than the new id names.
		void EnsureSpace(RegionMemory regions)
		{
			var size = regions.CellCount;
			var backed = regions.ZoneBacked;
			var gen = regions.Generation;
			if (size == count && backed == zoneBacked && gen == generation)
				return;

			count = size;
			zoneBacked = backed;
			generation = gen;
			threatGround = new int[size];
			threatAir = new int[size];
			threatGroundSpread = new int[size];
			threatAirSpread = new int[size];
			interest = new int[size];
			ownStrength = new int[size];
			staleness = new int[size];
			histGround = new float[size];
			histAir = new float[size];
		}
	}
}
