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

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>
	/// Phase DF step 1 (AI_DEEP_RESEARCH.md §14): where is the enemy going? Pure geometry, unit-tested:
	/// cluster the enemy combat units SEEN this snapshot into groups, match each group to the nearest group of
	/// the previous snapshot to get its velocity, and extrapolate a moving group to the own asset it heads for
	/// (best value ÷ distance inside a cone around its heading) with an ETA. Record-only for now.
	/// </summary>
	public static class BotThreatTracker
	{
		public readonly record struct Unit(CPos Cell, int Value);

		public sealed record Group(double X, double Y, int Value, int Count)
		{
			public double VelocityX { get; init; }
			public double VelocityY { get; init; }
			public int SeenTick { get; init; }
			public double Speed => Math.Sqrt(VelocityX * VelocityX + VelocityY * VelocityY);
		}

		public readonly record struct Prediction(CPos Target, int TargetValue, int EtaTicks);

		/// <summary>Greedy clustering: a unit joins the first group whose centroid lies within `radiusCells`.</summary>
		public static List<Group> Cluster(IEnumerable<Unit> units, int radiusCells, int tick)
		{
			var groups = new List<(double X, double Y, int Value, int Count)>();
			var r2 = (double)radiusCells * radiusCells;
			foreach (var u in units.OrderByDescending(u => u.Value))
			{
				var i = groups.FindIndex(g => Dist2(g.X, g.Y, u.Cell.X, u.Cell.Y) <= r2);
				if (i < 0)
				{
					groups.Add((u.Cell.X, u.Cell.Y, u.Value, 1));
					continue;
				}

				var g = groups[i];
				var n = g.Count + 1;
				groups[i] = (g.X + (u.Cell.X - g.X) / n, g.Y + (u.Cell.Y - g.Y) / n, g.Value + u.Value, n);
			}

			return groups.Select(g => new Group(g.X, g.Y, g.Value, g.Count) { SeenTick = tick }).ToList();
		}

		/// <summary>Each current group takes the velocity from the nearest previous group within `matchRadiusCells`.</summary>
		public static List<Group> Track(IReadOnlyList<Group> previous, IReadOnlyList<Group> current, int matchRadiusCells)
		{
			var r2 = (double)matchRadiusCells * matchRadiusCells;
			var result = new List<Group>(current.Count);
			foreach (var g in current)
			{
				var prev = previous?
					.Where(p => p.SeenTick < g.SeenTick && Dist2(p.X, p.Y, g.X, g.Y) <= r2)
					.OrderBy(p => Dist2(p.X, p.Y, g.X, g.Y)).FirstOrDefault();
				if (prev == null)
				{
					result.Add(g);
					continue;
				}

				var dt = g.SeenTick - prev.SeenTick;
				result.Add(g with { VelocityX = (g.X - prev.X) / dt, VelocityY = (g.Y - prev.Y) / dt });
			}

			return result;
		}

		/// <summary>
		/// The own asset a moving group heads for: inside a cone of `coneCos` around its heading, the highest value ÷
		/// (1 + distance); null when the group is not moving faster than `minSpeed` cells per tick or nothing is ahead.
		/// </summary>
		public static Prediction? Predict(Group group, IEnumerable<(CPos Cell, int Value)> assets, double coneCos, double minSpeed)
		{
			var speed = group.Speed;
			if (speed < minSpeed)
				return null;

			var hx = group.VelocityX / speed;
			var hy = group.VelocityY / speed;
			Prediction? best = null;
			var bestScore = 0.0;
			foreach (var (cell, value) in assets)
			{
				var dx = cell.X - group.X;
				var dy = cell.Y - group.Y;
				var dist = Math.Sqrt(dx * dx + dy * dy);
				if (dist < 1e-6 || (dx * hx + dy * hy) / dist < coneCos)
					continue;

				var score = value / (1 + dist);
				if (score > bestScore)
				{
					bestScore = score;
					best = new Prediction(cell, value, (int)Math.Round(dist / speed));
				}
			}

			return best;
		}

		static double Dist2(double ax, double ay, double bx, double by) => (ax - bx) * (ax - bx) + (ay - by) * (ay - by);
	}
}
