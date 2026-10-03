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
using System.Collections.Generic;
using System.Linq;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>One defence group before it becomes a cell: the sector it guards and its share (percent of the whole idle army).</summary>
	public sealed class StagingGroupPlan
	{
		public int Sector;
		public int SharePct;
	}

	/// <summary>What <see cref="ArmyStagingEval.Allocate"/> decides: groups, the reserve share and whether the army sits in the centre.</summary>
	public sealed class StagingAllocation
	{
		public List<StagingGroupPlan> Groups = [];
		public int ReservePct;
		public bool CentreMode;
	}

	/// <summary>Where each group and the reserve go while an attack is live. Sector -1 = the base centre.</summary>
	public sealed class StagingLiveTargets
	{
		public int[] GroupTargets = Array.Empty<int>();
		public int ReserveTarget = -1;
		public bool Live;
	}

	/// <summary>
	/// DESIGN 19.12 / AI_ARCHITECTURE 12.29: the pure arithmetic of the army staging planner. Integer math only (the bots run in
	/// lockstep): sectors are the eight 45-degree octants around the base centre, index 0 = east, clockwise on screen (y grows
	/// downward). No world access, so every rule is unit-testable.
	/// </summary>
	public static class ArmyStagingEval
	{
		public const int Sectors = 8;

		// tan(22.5 degrees) in thousandths: the octant boundary.
		const int TanHalfOctantMilli = 414;

		// Unit vectors of the sector centres, scaled by 1024 (724 = 1024 / sqrt 2).
		static readonly (int X, int Y)[] Vectors =
		{
			(1024, 0), (724, 724), (0, 1024), (-724, 724), (-1024, 0), (-724, -724), (0, -1024), (724, -724)
		};

		/// <summary>The sector of an offset from the base centre; -1 for the centre itself.</summary>
		public static int SectorOf(int dx, int dy)
		{
			var ax = Math.Abs(dx);
			var ay = Math.Abs(dy);
			if (ax == 0 && ay == 0)
				return -1;

			if (ay * 1000L <= ax * (long)TanHalfOctantMilli)
				return dx > 0 ? 0 : 4;

			if (ax * 1000L <= ay * (long)TanHalfOctantMilli)
				return dy > 0 ? 2 : 6;

			if (dx > 0)
				return dy > 0 ? 1 : 7;

			return dy > 0 ? 3 : 5;
		}

		/// <summary>The cell offset of <paramref name="radius"/> cells from the centre along a sector's centre line.</summary>
		public static (int X, int Y) Offset(int sector, int radius)
		{
			var v = Vectors[((sector % Sectors) + Sectors) % Sectors];
			return ((int)((long)v.X * radius / 1024), (int)((long)v.Y * radius / 1024));
		}

		/// <summary>The distance between two sectors on the circle of eight, 0..4.</summary>
		public static int SectorDistance(int a, int b)
		{
			var d = Math.Abs(a - b) % Sectors;
			return Math.Min(d, Sectors - d);
		}

		public static int Median(IReadOnlyList<int> values)
		{
			if (values == null || values.Count == 0)
				return 0;

			var sorted = values.OrderBy(v => v).ToArray();
			return sorted[sorted.Length / 2];
		}

		/// <summary>
		/// The defence ring radius of a sector in cells: the median radius of the own ARMED buildings there; with none, the
		/// outermost own building of the sector; with none, the same two rules over the whole base. 0 when the base is empty.
		/// </summary>
		public static int RingRadius(IReadOnlyList<int> sectorArmed, IReadOnlyList<int> sectorAll, IReadOnlyList<int> baseArmed, IReadOnlyList<int> baseAll)
		{
			if (sectorArmed != null && sectorArmed.Count > 0)
				return Median(sectorArmed);

			if (sectorAll != null && sectorAll.Count > 0)
				return sectorAll.Max();

			if (baseArmed != null && baseArmed.Count > 0)
				return Median(baseArmed);

			if (baseAll != null && baseAll.Count > 0)
				return baseAll.Max();

			return 0;
		}

		/// <summary>The staging radius: a few cells inside the ring, never beyond it (so never beyond tower range) and never negative.</summary>
		public static int StagingRadius(int ring, int insetCells)
		{
			return Math.Max(0, ring - Math.Max(0, insetCells));
		}

		/// <summary>
		/// Linear decay of a weight: half after <paramref name="halfLifeTicks"/> to a first-order approximation (ln 2 = 0.693),
		/// integer only. Weights are kept in milli-units so a small weight still decays.
		/// </summary>
		public static long Decay(long weightMilli, int elapsedTicks, int halfLifeTicks)
		{
			if (weightMilli <= 0 || elapsedTicks <= 0)
				return Math.Max(0, weightMilli);

			var drop = weightMilli * elapsedTicks * 693L / (Math.Max(1, halfLifeTicks) * 1000L);
			return Math.Max(0, weightMilli - Math.Max(1, drop));
		}

		/// <summary>The prior: <paramref name="totalMilli"/> shared out over the sectors in proportion to <paramref name="counts"/>.</summary>
		public static long[] PriorMilli(IReadOnlyList<int> counts, long totalMilli)
		{
			var result = new long[Sectors];
			long sum = 0;
			for (var i = 0; i < Sectors && i < counts.Count; i++)
				sum += counts[i];

			if (sum <= 0)
				return result;

			for (var i = 0; i < Sectors && i < counts.Count; i++)
				result[i] = totalMilli * counts[i] / sum;

			return result;
		}

		/// <summary>The spawn candidates left after dropping every one within <paramref name="radiusCells"/> of an own or allied home.</summary>
		public static List<CPos> EnemySpawnCandidates(IEnumerable<CPos> spawns, IEnumerable<CPos> ownAndAlliedHomes, int radiusCells)
		{
			var homes = ownAndAlliedHomes.ToArray();
			var limit = (long)radiusCells * radiusCells;
			var result = new List<CPos>();
			foreach (var s in spawns)
			{
				var taken = false;
				foreach (var h in homes)
				{
					var dx = s.X - h.X;
					var dy = s.Y - h.Y;
					if ((long)dx * dx + (long)dy * dy <= limit)
					{
						taken = true;
						break;
					}
				}

				if (!taken)
					result.Add(s);
			}

			return result;
		}

		/// <summary>
		/// Groups, reserve and centre decision from the rim weights (learned + prior) and the inside weight. Active sectors hold at
		/// least <paramref name="activePct"/> of the rim weight (at most <paramref name="maxGroups"/>, heaviest first; the heaviest
		/// one at least). The reserve takes min(reserveMaxPct, inside share); the whole army goes to the centre when the inside share
		/// reaches <paramref name="centreSwitchPct"/>. Shares sum to 100 whenever there is anything to stage.
		/// </summary>
		public static StagingAllocation Allocate(IReadOnlyList<long> rim, long insideMilli, int activePct, int maxGroups, int reserveMaxPct, int centreSwitchPct)
		{
			var result = new StagingAllocation();
			long rimTotal = 0;
			for (var i = 0; i < Sectors; i++)
				rimTotal += Math.Max(0, rim[i]);

			insideMilli = Math.Max(0, insideMilli);
			if (rimTotal + insideMilli <= 0)
				return result;

			var insideShare = (int)(100L * insideMilli / (rimTotal + insideMilli));
			if (insideShare >= centreSwitchPct)
			{
				result.CentreMode = true;
				result.ReservePct = 100;
				return result;
			}

			if (rimTotal <= 0)
			{
				result.ReservePct = 100;
				return result;
			}

			var ranked = Enumerable.Range(0, Sectors).Where(i => rim[i] > 0).OrderByDescending(i => rim[i]).ThenBy(i => i).ToList();
			var active = ranked.Where(i => rim[i] * 100 >= (long)activePct * rimTotal).Take(Math.Max(1, maxGroups)).ToList();
			if (active.Count == 0)
				active.Add(ranked[0]);

			result.ReservePct = Math.Min(Math.Max(0, reserveMaxPct), insideShare);
			var pool = 100 - result.ReservePct;
			var activeTotal = active.Sum(i => rim[i]);
			var assigned = 0;
			foreach (var i in active)
			{
				var pct = (int)(pool * rim[i] / activeTotal);
				result.Groups.Add(new StagingGroupPlan { Sector = i, SharePct = pct });
				assigned += pct;
			}

			// The rounding remainder goes to the heaviest group so the shares sum to exactly 100.
			result.Groups[0].SharePct += pool - assigned;
			return result;
		}

		/// <summary>
		/// A group whose share of the idle army value is below <paramref name="minGroupValue"/> merges into the nearest other
		/// group (the bigger one on a tie), smallest first, until none is left or one group remains. The reserve is never merged.
		/// </summary>
		public static void MergeSmallGroups(List<StagingGroupPlan> groups, long idleValue, int minGroupValue)
		{
			while (groups.Count > 1)
			{
				var small = groups.Where(g => g.SharePct * Math.Max(0, idleValue) / 100 < minGroupValue)
					.OrderBy(g => g.SharePct).ThenByDescending(g => g.Sector).FirstOrDefault();
				if (small == null)
					break;

				var target = groups.Where(g => g != small)
					.OrderBy(g => SectorDistance(g.Sector, small.Sector)).ThenByDescending(g => g.SharePct).ThenBy(g => g.Sector).First();
				target.SharePct += small.SharePct;
				groups.Remove(small);
			}

			// Heaviest first, as Allocate returns them: the primary point is index 0.
			groups.Sort((a, b) => b.SharePct != a.SharePct ? b.SharePct.CompareTo(a.SharePct) : a.Sector.CompareTo(b.Sector));
		}

		/// <summary>
		/// The live reaction. One live sector: every group and the reserve converge on it. Several: each group answers its own
		/// sector and the reserve goes to the sector with the largest live value. Attacks from inside answer with the reserve
		/// alone (centre) unless a rim attack is heavier. Nothing live: groups hold their sectors and the reserve the centre.
		/// </summary>
		public static StagingLiveTargets LiveTargets(IReadOnlyList<int> groupSectors, IReadOnlyList<long> liveValue, long liveInside)
		{
			var result = new StagingLiveTargets { GroupTargets = groupSectors.ToArray() };
			var liveSectors = Enumerable.Range(0, Sectors).Where(i => liveValue[i] > 0).ToList();
			if (liveSectors.Count == 0 && liveInside <= 0)
				return result;

			result.Live = true;
			if (liveSectors.Count == 0)
				return result;

			var heaviest = liveSectors.OrderByDescending(i => liveValue[i]).ThenBy(i => i).First();
			result.ReserveTarget = liveInside > 0 && liveInside >= liveValue[heaviest] ? -1 : heaviest;
			if (liveSectors.Count == 1)
				for (var g = 0; g < result.GroupTargets.Length; g++)
					result.GroupTargets[g] = heaviest;

			return result;
		}

		/// <summary>True once no attack has been live for <paramref name="returnAfterTicks"/>: the groups go back to their staging points.</summary>
		public static bool ShouldReturn(int ticksSinceLive, int returnAfterTicks)
		{
			return ticksSinceLive >= returnAfterTicks;
		}

		/// <summary>
		/// Which part each unit joins: groups 0..n-1 by their share, then the reserve (index n). Units must already be in a
		/// deterministic order; each is placed by the midpoint of its value along the cumulative line.
		/// </summary>
		public static int[] AssignByValue(IReadOnlyList<long> unitValues, IReadOnlyList<int> sharePct)
		{
			var result = new int[unitValues.Count];
			if (sharePct.Count == 0)
				return result;

			var total = unitValues.Sum(v => Math.Max(1, v));
			long cumulative = 0;
			for (var u = 0; u < unitValues.Count; u++)
			{
				var value = Math.Max(1, unitValues[u]);
				var mid = cumulative + value / 2;
				cumulative += value;

				long boundary = 0;
				var part = sharePct.Count - 1;
				for (var g = 0; g < sharePct.Count; g++)
				{
					boundary += sharePct[g];
					if (mid * 100 < boundary * total)
					{
						part = g;
						break;
					}
				}

				result[u] = part;
			}

			return result;
		}
	}
}
