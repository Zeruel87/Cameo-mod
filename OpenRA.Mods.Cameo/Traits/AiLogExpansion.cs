#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Cameo.Traits.BotModules;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	/// <summary>
	/// The `expansion` object of a situation snapshot (AI_ARCHITECTURE 12.24 FE-0). Record-only: nothing in the bot reads it.
	/// Distances are in cells. Angles are degrees, -1 when not defined.
	/// </summary>
	internal sealed class ExpansionSnapshot
	{
		public int FieldsKnown, FieldsInReach, FieldsServed, FieldsHarvested;
		public int AnchorsSpreader, AnchorsField;
		public int Refineries, ExcessRefineries, UnassignedRefineries;
		public double AnchorDistMean, AnchorDistMax;
		public int Conyards, Outposts;
		public string CrawlTarget = "", McvSite = "";
		public int CrawlMcvAngle = -1;
		public int CoverageMilli;
	}

	internal readonly struct RefineryAssignment
	{
		public readonly int Excess;
		public readonly int Unassigned;
		public readonly double MeanDistance;
		public readonly double MaxDistance;

		public RefineryAssignment(int excess, int unassigned, double mean, double max)
		{
			Excess = excess;
			Unassigned = unassigned;
			MeanDistance = mean;
			MaxDistance = max;
		}
	}

	/// <summary>Pure helpers of the field-economy telemetry, free of world state so they can be tested.</summary>
	internal static class ExpansionMath
	{
		/// <summary>A field within this many cells of a spreader belongs to that spreader; a refinery within it of an anchor serves it.</summary>
		public const int AnchorRadiusCells = 12;

		/// <summary>Bearing in degrees, clockwise from north (map up = -y), 0..359.</summary>
		public static int BearingDegrees(CPos from, CPos to)
		{
			var dx = to.X - from.X;
			var dy = to.Y - from.Y;
			if (dx == 0 && dy == 0)
				return 0;

			var degrees = Math.Atan2(dx, -dy) * 180.0 / Math.PI;
			return ((int)Math.Round(degrees) % 360 + 360) % 360;
		}

		/// <summary>The smaller angle between two bearings, 0..180.</summary>
		public static int AngleBetween(int bearingA, int bearingB)
		{
			var d = Math.Abs(bearingA - bearingB) % 360;
			return d > 180 ? 360 - d : d;
		}

		public static double Distance(CPos a, CPos b)
		{
			return Math.Sqrt((a - b).LengthSquared);
		}

		/// <summary>The fields (centres) with no spreader within <paramref name="radius"/> cells: each is an anchor of its own.</summary>
		public static List<CPos> SpreaderlessFields(IEnumerable<CPos> fields, IReadOnlyList<CPos> spreaders, int radius)
		{
			var result = new List<CPos>();
			foreach (var f in fields)
			{
				var covered = false;
				foreach (var s in spreaders)
					if (Distance(f, s) <= radius)
					{
						covered = true;
						break;
					}

				if (!covered)
					result.Add(f);
			}

			return result;
		}

		/// <summary>Index and distance of the anchor nearest to <paramref name="cell"/>; (-1, 0) with no anchors.</summary>
		public static (int Index, double Distance) Nearest(CPos cell, IReadOnlyList<CPos> anchors)
		{
			var best = -1;
			var bestDistance = double.MaxValue;
			for (var i = 0; i < anchors.Count; i++)
			{
				var d = Distance(cell, anchors[i]);
				if (d < bestDistance)
				{
					bestDistance = d;
					best = i;
				}
			}

			return best < 0 ? (-1, 0) : (best, bestDistance);
		}

		/// <summary>
		/// Assign each refinery to its nearest anchor; it serves that anchor when within <paramref name="serveRadius"/>, else it is
		/// unassigned. Excess = for each anchor the refineries beyond the first, plus every unassigned refinery. The distance stats
		/// run over all refineries to their nearest anchor (assigned or not).
		/// </summary>
		public static RefineryAssignment AssignRefineries(IReadOnlyList<CPos> refineries, IReadOnlyList<CPos> anchors, int serveRadius)
		{
			if (refineries.Count == 0)
				return new RefineryAssignment(0, 0, 0, 0);

			var perAnchor = new Dictionary<int, int>();
			var unassigned = 0;
			double sum = 0, max = 0;
			var measured = 0;
			foreach (var r in refineries)
			{
				var (index, distance) = Nearest(r, anchors);
				if (index < 0)
				{
					unassigned++;
					continue;
				}

				sum += distance;
				max = Math.Max(max, distance);
				measured++;
				if (distance <= serveRadius)
					perAnchor[index] = perAnchor.TryGetValue(index, out var n) ? n + 1 : 1;
				else
					unassigned++;
			}

			var excess = unassigned + perAnchor.Values.Sum(n => n - 1);
			return new RefineryAssignment(excess, unassigned, measured == 0 ? 0 : sum / measured, max);
		}

		/// <summary>Rules-derived building category of the placement log; the first match in this order wins.</summary>
		public static string Category(IReadOnlySet<string> tags, IReadOnlySet<string> roles)
		{
			bool Has(string t) => tags != null && tags.Contains(t);
			if (Has(BotTargetTags.Conyard))
				return "conyard";
			if (Has(BotTargetTags.Refinery))
				return "refinery";
			if (Has(BotTargetTags.Superweapon))
				return "superweapon";
			if (Has(BotTargetTags.Power))
				return "power";
			if (Has(BotTargetTags.Defence))
				return "defence";
			if (Has(BotTargetTags.Production))
				return "production";
			if (roles != null && roles.Contains(BotUnitRole.Tech))
				return "tech";
			if (roles != null && roles.Contains(BotUnitRole.Support))
				return "support";
			return "other";
		}
	}

	/// <summary>
	/// Per-player collector of the field-economy telemetry (12.24 FE-0). Observer only: it reads the resource map the bot already keeps
	/// (no second field model; this only remembers each field's first-seen centre like the planner does), the planner's published
	/// target and MCV site, and the map's spreaders (public map data). It never writes to any module.
	/// </summary>
	internal sealed class ExpansionTelemetry
	{
		const int MainBaseRadiusCells = 20;
		const int SpreaderRescanTicks = 1500;

		readonly Dictionary<int, CPos> fieldCenters = new();
		readonly List<CPos> spreaders = new();
		readonly List<CPos> anchors = new();
		int spreaderCount;
		int nextSpreaderScan;
		CPos? mainConyard;

		/// <summary>Anchors: the spreaders first, then the spreaderless fields' centres.</summary>
		public IReadOnlyList<CPos> Anchors => anchors;

		void Refresh(OpenRA.Player player, int tick)
		{
			var map = player.PlayerActor.TraitsImplementing<ResourceMapBotModule>().FirstOrDefault(t => t.IsTraitEnabled());
			if (map != null)
				for (var i = 0; i < map.GetIndicesLength(); i++)
				{
					var field = map.GetIndice(i);
					if (field != null && field.ResourceCellsCount > 0 && !fieldCenters.ContainsKey(i))
						fieldCenters[i] = field.ResourceCellsCenter;
				}

			if (tick >= nextSpreaderScan)
			{
				nextSpreaderScan = tick + SpreaderRescanTicks;
				spreaders.Clear();
				foreach (var a in player.World.ActorsWithTrait<ISeedableResource>())
					if (!a.Actor.IsDead && a.Actor.IsInWorld)
						spreaders.Add(a.Actor.Location);
			}

			anchors.Clear();
			anchors.AddRange(spreaders);
			spreaderCount = spreaders.Count;
			anchors.AddRange(ExpansionMath.SpreaderlessFields(fieldCenters.Values, spreaders, ExpansionMath.AnchorRadiusCells));
		}

		/// <summary>The anchor nearest to a placed building, for the placement log. Index -1 when the map knows none.</summary>
		public (int Index, CPos Anchor, bool Spreader, double Distance) NearestAnchor(OpenRA.Player player, CPos cell)
		{
			Refresh(player, player.World.WorldTick);
			var (index, distance) = ExpansionMath.Nearest(cell, anchors);
			return index < 0 ? (-1, CPos.Zero, false, 0) : (index, anchors[index], index < spreaderCount, distance);
		}

		public ExpansionSnapshot Capture(OpenRA.Player player, IReadOnlyCollection<Actor> ownBuildings)
		{
			var world = player.World;
			Refresh(player, world.WorldTick);

			var map = player.PlayerActor.TraitsImplementing<ResourceMapBotModule>().FirstOrDefault(t => t.IsTraitEnabled());
			var planner = player.PlayerActor.TraitsImplementing<ExpansionPlannerBotModule>().FirstEnabledTraitOrDefault();
			var reach = planner?.Info.ReachCells ?? 6;
			var claimRadius = planner?.Info.ClaimRadiusCells ?? 8;

			var buildableArea = new List<CPos>();
			var refineries = new List<CPos>();
			var conyards = new List<CPos>();
			foreach (var b in ownBuildings)
			{
				if (b.Info.HasTraitInfo<GivesBuildableAreaInfo>())
					buildableArea.Add(b.Location);
				if (b.Info.HasTraitInfo<RefineryInfo>())
					refineries.Add(b.Location);
				if (b.Info.HasTraitInfo<BaseBuildingInfo>())
					conyards.Add(b.Location);
			}

			var snapshot = new ExpansionSnapshot
			{
				FieldsKnown = fieldCenters.Count,
				AnchorsSpreader = spreaderCount,
				AnchorsField = anchors.Count - spreaderCount,
				Refineries = refineries.Count,
				Conyards = conyards.Count
			};

			var covered = 0;
			foreach (var kv in fieldCenters)
			{
				var center = kv.Value;
				var inReach = buildableArea.Any(c => ExpansionMath.Distance(c, center) <= reach);
				var served = refineries.Any(r => ExpansionMath.Distance(r, center) <= claimRadius);
				if (inReach)
					snapshot.FieldsInReach++;
				if (served)
					snapshot.FieldsServed++;
				if (inReach || served)
					covered++;
				if (map != null && map.GetIndice(kv.Key)?.PlayerHarvetserCount > 0)
					snapshot.FieldsHarvested++;
			}

			snapshot.CoverageMilli = fieldCenters.Count == 0 ? 0 : covered * 1000 / fieldCenters.Count;

			var assignment = ExpansionMath.AssignRefineries(refineries, anchors, ExpansionMath.AnchorRadiusCells);
			snapshot.ExcessRefineries = assignment.Excess;
			snapshot.UnassignedRefineries = assignment.Unassigned;
			snapshot.AnchorDistMean = Math.Round(assignment.MeanDistance, 1);
			snapshot.AnchorDistMax = Math.Round(assignment.MaxDistance, 1);

			// The main base: the first construction yard seen (kept for the match); outposts are the yards beyond MainBaseRadiusCells of it.
			if (mainConyard == null && conyards.Count > 0)
				mainConyard = conyards[0];
			CPos? main = mainConyard ?? (ownBuildings.Count > 0 ? ownBuildings.First().Location : null);
			if (main.HasValue)
			{
				snapshot.Outposts = conyards.Count(c => ExpansionMath.Distance(c, main.Value) > MainBaseRadiusCells);
				var near = ownBuildings.Where(b => ExpansionMath.Distance(b.Location, main.Value) <= MainBaseRadiusCells)
					.Select(b => b.Location).ToList();
				var centroid = near.Count == 0 ? main.Value
					: new CPos((int)near.Average(c => c.X), (int)near.Average(c => c.Y));
				var crawl = planner?.Target?.Center;
				var mcv = planner?.LastMcvSite;
				snapshot.CrawlTarget = crawl.HasValue ? $"{crawl.Value.X},{crawl.Value.Y}" : "";
				snapshot.McvSite = mcv.HasValue ? $"{mcv.Value.X},{mcv.Value.Y}" : "";
				if (crawl.HasValue && mcv.HasValue)
					snapshot.CrawlMcvAngle = ExpansionMath.AngleBetween(
						ExpansionMath.BearingDegrees(centroid, crawl.Value), ExpansionMath.BearingDegrees(centroid, mcv.Value));
			}

			return snapshot;
		}
	}
}
