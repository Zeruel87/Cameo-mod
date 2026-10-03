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

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>
	/// Phase 6e risk routing (docs/design/AI_FRANSBOT_RESEARCH.md): a coarse A*
	/// over RegionMemory, costed by remembered hostile value, emitting waypoints
	/// a squad can feed to its existing move/attack-move orders. Pure and
	/// unsynced — no engine queries, so it is directly unit-testable.
	/// </summary>
	public static class RegionRouter
	{
		/// <summary>
		/// Route from <paramref name="from"/> to <paramref name="to"/> across region
		/// centers, paying <paramref name="threatWeight"/>-normalised extra cost per
		/// remembered threat in each entered region. The start and goal regions are
		/// never charged (the risk gate, not the router, decides whether to go).
		/// </summary>
		/// <returns>Waypoints ending at <paramref name="to"/>, or null when start
		/// and goal share a region, when an endpoint resolves to no region (zone-backed
		/// indexOf can answer -1 for cells beyond every zone), or when no path exists —
		/// disjoint zones are real islands, unlike the always-connected grid.</returns>
		public static List<CPos> Route(
			RegionMemory regions,
			CPos from,
			CPos to,
			Func<int, int> threatAtRegion,
			int threatWeight,
			int maxWaypoints,
			Func<CPos, CPos, bool> waypointReachable = null)
		{
			var start = regions.IndexOf(from);
			var goal = regions.IndexOf(to);
			if (start == goal || start < 0 || goal < 0)
				return null;

			var weight = Math.Max(1, threatWeight);
			maxWaypoints = Math.Max(1, maxWaypoints);
			var path = FindPath(regions, start, goal, i => i == start || i == goal ? 0 : threatAtRegion(i) / (double)weight);
			if (path == null || path.Count < 2)
				return null;

			// Interior regions become waypoints at their centers; the goal region's
			// center is replaced by the exact target cell.
			var waypoints = new List<CPos>();
			for (var i = 1; i < path.Count - 1; i++)
				waypoints.Add(regions.CenterOf(path[i]));

			waypoints.Add(to);

			// Decimate long routes: keep evenly spaced waypoints and the target.
			if (waypoints.Count > maxWaypoints)
			{
				var thinned = new List<CPos>();
				for (var i = 0; i < maxWaypoints - 1; i++)
				{
					var index = (int)Math.Round(i * (waypoints.Count - 2) / (double)Math.Max(1, maxWaypoints - 1));
					thinned.Add(waypoints[index]);
				}

				thinned.Add(to);
				waypoints = thinned;
			}

			// Drop waypoints the locomotor cannot reach from the previous waypoint
			// (a region center may sit on water or a cliff).
			if (waypointReachable != null)
			{
				var filtered = new List<CPos>();
				var previous = from;
				foreach (var waypoint in waypoints)
				{
					if (waypoint == to || waypointReachable(previous, waypoint))
					{
						filtered.Add(waypoint);
						previous = waypoint;
					}
				}

				if (filtered.Count == 0 || filtered[filtered.Count - 1] != to)
					filtered.Add(to);

				waypoints = filtered;
			}

			return waypoints;
		}

		// A* over the region index space: 4-connected grid neighbours when grid-backed,
		// the zone graph's AdjacentRegionIds when zone-backed. Region counts are small
		// (a few hundred grid cells, tens of zones on typical maps) so a PriorityQueue
		// suffices.
		static List<int> FindPath(RegionMemory regions, int start, int goal, Func<int, double> enterCost)
		{
			var count = regions.CellCount;

			var g = new double[count];
			var parent = new int[count];
			Array.Fill(parent, -2);
			parent[start] = -1;
			g[start] = 0;

			var open = new PriorityQueue<int, double>();
			open.Enqueue(start, 0);

			if (regions.ZoneBacked)
			{
				// ZG-c: expansion is zone adjacency, and there is no grid metric left to aim
				// at — the heuristic is 0, so A* degrades to Dijkstra. Still cheapest-first
				// (the threat costs are what the route exists for), just not steered.
				while (open.Count > 0)
				{
					var current = open.Dequeue();
					if (current == goal)
						return Reconstruct(parent, goal);

					foreach (var neighbor in regions.NeighborsOf(current))
					{
						if (neighbor < 0 || neighbor >= count)
							continue;

						var tentative = g[current] + 1 + enterCost(neighbor);
						if (parent[neighbor] != -2 && tentative >= g[neighbor])
							continue;

						parent[neighbor] = current;
						g[neighbor] = tentative;
						open.Enqueue(neighbor, tentative);
					}
				}

				return null;
			}

			var columns = regions.Columns;
			var rows = regions.Rows;
			var goalRow = goal / columns;
			var goalCol = goal - goalRow * columns;

			while (open.Count > 0)
			{
				var current = open.Dequeue();
				if (current == goal)
					return Reconstruct(parent, goal);

				var row = current / columns;
				var col = current - row * columns;

				for (var d = 0; d < 4; d++)
				{
					var nCol = col + (d == 0 ? -1 : d == 1 ? 1 : 0);
					var nRow = row + (d == 2 ? -1 : d == 3 ? 1 : 0);
					if (nCol < 0 || nCol >= columns || nRow < 0 || nRow >= rows)
						continue;

					var neighbor = nRow * columns + nCol;
					var tentative = g[current] + 1 + enterCost(neighbor);
					if (parent[neighbor] != -2 && tentative >= g[neighbor])
						continue;

					parent[neighbor] = current;
					g[neighbor] = tentative;

					var nRowDelta = Math.Abs(nRow - goalRow);
					var nColDelta = Math.Abs(nCol - goalCol);
					open.Enqueue(neighbor, tentative + nRowDelta + nColDelta);
				}
			}

			return null;
		}

		static List<int> Reconstruct(int[] parent, int goal)
		{
			var path = new List<int>();
			for (var at = goal; at != -1; at = parent[at])
				path.Add(at);

			path.Reverse();
			return path;
		}
	}
}
