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
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	[Desc("Places defences so the whole base is covered: each one goes where its weapon range covers the most base cells",
		"no defence of the same role (anti-air or ground) covers yet, preferring the outer edge and the side of the enemy.",
		"Advises the shared base builder through IBotDefensePlacementAdvisor; switched off, the base builder is untouched.")]
	public class DefenseCoveragePlannerInfo : ConditionalTraitInfo
	{
		[Desc("Advise the base builder. False = inert (the base builder places defences as it always did).")]
		public readonly bool Enabled = false;

		[Desc("Candidate cells scored per placement, sampled by a fixed stride (no random draw).")]
		public readonly int MaxCandidates = 300;

		[Desc("Score per percent of how far out (0-100) from the base centre the cell lies.")]
		public readonly int EdgeWeight = 30;

		[Desc("Score per percent (-100..100) of how well the cell lies toward the enemy.")]
		public readonly int ThreatWeight = 40;

		[Desc("Share (percent) of our defences that should stand on the perimeter; the rest guard the inside against intruders.")]
		public readonly int PerimeterSharePercent = 75;

		[Desc("A cell is on the perimeter when its edgeness (percent of the maximum defence radius) is at least this.")]
		public readonly int PerimeterEdgePercent = 70;

		[Desc("Cover remote expansion fronts too: cluster own buildings, advise the defence where the most cells are uncovered instead of only around the randomly-picked yard.")]
		public readonly bool CoverRemoteOutposts = false;

		[Desc("CN4 consumer: when region roles are published, an UNCOVERED front in a Military or Outpost",
			"region outranks every non-frontier front — defence walks to the frontier first. Needs CoverRemoteOutposts.")]
		public readonly bool UseRegionRoles = false;

		[Desc("Two building cells belong to one front when they are at most this many cells apart (Chebyshev).")]
		public readonly int FrontLinkRadius = 14;

		[Desc("Search annulus (cells) when no base builder is found.")]
		public readonly int MinimumRadius = 5;

		[Desc("Search annulus (cells) when no base builder is found.")]
		public readonly int MaximumRadius = 20;

		public override object Create(ActorInitializer init) { return new DefenseCoveragePlanner(init.Self, this); }
	}

	public class DefenseCoveragePlanner : ConditionalTrait<DefenseCoveragePlannerInfo>, IBotDefensePlacementAdvisor, INotifyActorDisposing
	{
		// Coverage dominates (maintainer: "the whole base should always be covered"): one newly covered base cell (1000)
		// outweighs the full edge + enemy-side bonus (EdgeWeight 30 + ThreatWeight 40, x100 = 7000) only from 8 cells on,
		// so the bonus decides between spots of nearly equal coverage and pulls them outward and toward the enemy.
		const int CoverageScore = 1000;

		readonly World world;
		readonly OpenRA.Player player;

		// Own buildings, kept from the world's add/remove events: no enumeration of the world's actors.
		readonly HashSet<Actor> buildings = new();
		BaseBuilderBotModuleCA[] baseBuilders;
		IBotRegionRoles regionRoles;
		IReadOnlyDictionary<string, HashSet<string>> specialties;

		public DefenseCoveragePlanner(Actor self, DefenseCoveragePlannerInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			world.ActorAdded += Added;
			world.ActorRemoved += Removed;
		}

		void Added(Actor a)
		{
			if (a.Owner == player && a.Info.HasTraitInfo<BuildingInfo>())
				buildings.Add(a);
		}

		void Removed(Actor a) { buildings.Remove(a); }

		void INotifyActorDisposing.Disposing(Actor self)
		{
			world.ActorAdded -= Added;
			world.ActorRemoved -= Removed;
		}

		bool IBotDefensePlacementAdvisor.IsActive => !IsTraitDisabled && Info.Enabled;

		// --- world-free helpers (tested) ---

		/// <summary>The longest weapon range, in whole cells (rounded up), of a defence's armaments; 0 with no weapon.</summary>
		public static int MaxRangeCells(ActorInfo info)
		{
			var max = 0;
			foreach (var armament in info.TraitInfos<ArmamentInfo>())
				if (armament.WeaponInfo != null && armament.WeaponInfo.Range.Length > max)
					max = armament.WeaponInfo.Range.Length;

			return (max + 1023) / 1024;
		}

		/// <summary>True when the cell lies within the range of any of the defences (centre, range in cells).</summary>
		public static bool Covered(CPos cell, IEnumerable<(CPos Center, int Range)> defences)
		{
			foreach (var d in defences)
				if ((cell - d.Center).LengthSquared <= d.Range * d.Range)
					return true;

			return false;
		}

		/// <summary>How many of the still-uncovered base cells a defence at <paramref name="at"/> would newly cover.</summary>
		public static int NewlyCovered(CPos at, int range, IReadOnlyCollection<CPos> uncovered)
		{
			var n = 0;
			foreach (var c in uncovered)
				if ((c - at).LengthSquared <= range * range)
					n++;

			return n;
		}

		/// <summary>How far out the cell lies, 0 (at the centre) to 100 (at the maximum radius or beyond), in percent.</summary>
		public static int Edgeness(CPos cell, CPos center, int maxRadius)
		{
			if (maxRadius <= 0)
				return 0;

			var d = Math.Sqrt((cell - center).LengthSquared);
			return (int)Math.Min(100, d * 100 / maxRadius);
		}

		/// <summary>Cosine, in percent (-100..100), between (cell - center) and (threat - center); 0 when either is degenerate.</summary>
		public static int ThreatAlignment(CPos cell, CPos center, CPos threat)
		{
			var a = cell - center;
			var b = threat - center;
			var la = Math.Sqrt(a.LengthSquared);
			var lb = Math.Sqrt(b.LengthSquared);
			if (la < 1e-6 || lb < 1e-6)
				return 0;

			return (int)Math.Round((a.X * b.X + a.Y * b.Y) * 100 / (la * lb));
		}

		public static int Score(int newlyCovered, int edgeness, int threatAlignment, int edgeWeight, int threatWeight)
		{
			return newlyCovered * CoverageScore + edgeWeight * edgeness + threatWeight * threatAlignment;
		}

		/// <summary>
		/// The perimeter quota: true when the next defence belongs on the perimeter (its share is below the target),
		/// false when it belongs inside. With no defences yet the first goes to the perimeter.
		/// </summary>
		public static bool PlacePerimeter(int perimeterCount, int interiorCount, int sharePercent)
		{
			var total = perimeterCount + interiorCount;
			return total == 0 || perimeterCount * 100 < sharePercent * total;
		}

		/// <summary>
		/// DEF-3: cluster building cells into fronts — greedy single-linkage, two cells join when
		/// within `linkRadius` (Chebyshev). Returns each cluster's cells; order is the discovery
		/// order of the sorted input, so the result is deterministic for the tests.
		/// </summary>
		public static List<List<CPos>> ClusterFronts(IReadOnlyCollection<CPos> cells, int linkRadius)
		{
			var remaining = new List<CPos>(cells.OrderBy(c => c.X).ThenBy(c => c.Y));
			var fronts = new List<List<CPos>>();
			while (remaining.Count > 0)
			{
				var front = new List<CPos> { remaining[0] };
				remaining.RemoveAt(0);
				for (var i = 0; i < front.Count; i++)
					for (var j = remaining.Count - 1; j >= 0; j--)
						if (Math.Abs(front[i].X - remaining[j].X) <= linkRadius
							&& Math.Abs(front[i].Y - remaining[j].Y) <= linkRadius)
						{
							front.Add(remaining[j]);
							remaining.RemoveAt(j);
						}
				fronts.Add(front);
			}

			return fronts;
		}

		/// <summary>
		/// DEF-3: the centroid of the front whose cells still lack the most coverage — the next
		/// defence defends what is actually naked, which is how remote outposts earn a tower
		/// instead of queueing behind the (already covered) main base. Ties go to the front with
		/// more cells total, then to the lowest centroid coordinates — deterministic both ways.
		/// Returns the picked cluster's centroid; null when every front is fully covered.
		/// </summary>
		public static CPos? PickFrontCenter(IReadOnlyCollection<CPos> baseCells,
			IEnumerable<(CPos Center, int Range)> defences, int linkRadius)
		{
			var fronts = ClusterFronts(baseCells, linkRadius);
			List<CPos> bestFront = null;
			var bestUncovered = 0;
			foreach (var front in fronts)
			{
				var uncovered = front.Count(c => !Covered(c, defences));
				if (uncovered > bestUncovered ||
					(uncovered == bestUncovered && uncovered > 0 && bestFront != null &&
						(front.Count > bestFront.Count ||
							(front.Count == bestFront.Count && CompareCell(Centroid(front), Centroid(bestFront)) < 0))))
				{
					bestUncovered = uncovered;
					bestFront = front;
				}
			}

			return bestFront == null ? (CPos?)null : Centroid(bestFront);
		}

		/// <summary>CN4: a region role that marks a frontier — the ground that faces (or gates) the enemy.</summary>
		public static bool IsFrontierRole(RegionRole role) => role is RegionRole.Military or RegionRole.Outpost;

		/// <summary>
		/// CN4/DEF-3: like <see cref="PickFrontCenter"/>, but only fronts whose centroid lands in a
		/// frontier region (Military or Outpost) compete — the frontier is defended before the interior,
		/// whatever the uncovered count elsewhere. Null when no frontier front has uncovered cells;
		/// the caller then falls back to the plain pick (a naked core base is never left undefended
		/// behind a covered frontier).
		/// </summary>
		public static CPos? PickFrontierCenter(IReadOnlyCollection<CPos> baseCells,
			IEnumerable<(CPos Center, int Range)> defences, int linkRadius, Func<CPos, RegionRole> roleOf)
		{
			var fronts = ClusterFronts(baseCells, linkRadius);
			List<CPos> bestFront = null;
			var bestUncovered = 0;
			foreach (var front in fronts)
			{
				if (!IsFrontierRole(roleOf(Centroid(front))))
					continue;

				var uncovered = front.Count(c => !Covered(c, defences));
				if (uncovered > bestUncovered ||
					(uncovered == bestUncovered && uncovered > 0 && bestFront != null &&
						(front.Count > bestFront.Count ||
							(front.Count == bestFront.Count && CompareCell(Centroid(front), Centroid(bestFront)) < 0))))
				{
					bestUncovered = uncovered;
					bestFront = front;
				}
			}

			return bestFront == null ? (CPos?)null : Centroid(bestFront);
		}

		static int CompareCell(CPos a, CPos b)
		{
			return a.X != b.X ? a.X.CompareTo(b.X) : a.Y.CompareTo(b.Y);
		}

		static CPos Centroid(List<CPos> cells)
		{
			return new CPos(cells.Sum(c => c.X) / cells.Count, cells.Sum(c => c.Y) / cells.Count);
		}

		/// <summary>The specialties a defence holds; one with none falls back to anti-air (AntiAirTypes) else anti-armour.</summary>
		public static IReadOnlyCollection<string> RolesOf(IReadOnlyDictionary<string, HashSet<string>> specialties, string name, bool antiAirType)
		{
			if (specialties != null && specialties.TryGetValue(name, out var set) && set.Count > 0)
				return set;

			return new[] { antiAirType ? BotUnitRole.AntiAir : BotUnitRole.AntiArmour };
		}

		// --- placement ---

		CPos? IBotDefensePlacementAdvisor.ChooseDefenseCell(ActorInfo defense, bool antiAir, CPos baseCenter, Func<CPos, bool> canPlace)
		{
			var range = MaxRangeCells(defense);
			if (range <= 0)
				return null;

			baseBuilders ??= player.PlayerActor.TraitsImplementing<BaseBuilderBotModuleCA>().ToArray();
			var builder = baseBuilders.FirstOrDefault(b => b.IsTraitEnabled());
			var antiAirTypes = builder?.Info.AntiAirTypes;
			var minRadius = builder?.Info.MinimumDefenseRadius ?? Info.MinimumRadius;
			var maxRadius = builder?.Info.MaximumDefenseRadius ?? Info.MaximumRadius;

			specialties ??= BotUnitRoles.BuildDefenceSpecialties(world.Map.Rules);
			IReadOnlyCollection<string> RolesFor(ActorInfo i) =>
				RolesOf(specialties, i.Name, antiAirTypes != null && antiAirTypes.Contains(i.Name));
			var roles = RolesFor(defense);

			// Our own buildings and, of those, the defences per role (buildings under construction are in the world already).
			var baseCells = new HashSet<CPos>();
			var byRole = new Dictionary<string, List<(CPos Center, int Range)>>();
			var perimeter = 0;
			var interior = 0;
			foreach (var b in buildings)
			{
				if (b.IsDead || !b.IsInWorld || b.Owner != player) // captured since it was added
					continue;

				var bi = b.Info.TraitInfoOrDefault<BuildingInfo>();
				foreach (var c in bi.Tiles(b.Location))
					baseCells.Add(c);

				if (b.Info.HasTraitInfo<AttackBaseInfo>())
				{
					var r = MaxRangeCells(b.Info);
					if (r <= 0)
						continue;

					foreach (var role in RolesFor(b.Info))
					{
						if (!byRole.TryGetValue(role, out var list))
							byRole[role] = list = new List<(CPos Center, int Range)>();
						list.Add((b.Location, r));
					}
				}
			}

			// A base cell is protected only when every role covers it; a candidate scores per role it holds.
			var uncovered = new Dictionary<string, CPos[]>();
			foreach (var role in roles)
			{
				var list = byRole.TryGetValue(role, out var l) ? l : new List<(CPos Center, int Range)>();
				uncovered[role] = baseCells.Where(c => !Covered(c, list)).ToArray();
			}

			// DEF-3: with remote-outpost cover the annulus centres on the FRONT needing coverage
			// most — an expansion's naked cells outscore the main base's covered ones, so towers
			// walk out to the crawled-to fields instead of stacking at home. Any buildable-area
			// provider still legalises the cell (IsCloseEnoughToBase is per-provider), so the
			// remote yard's own buildable ring supplies the placement.
			var roleDefences = byRole.Values.SelectMany(l => l).ToArray();
			if (Info.CoverRemoteOutposts)
			{
				// CN4 consumer: a still-uncovered front inside a frontier region (Military/Outpost)
				// outranks every interior front — the seam advises, the defence still belongs to the
				// module whose cells are naked. Falls back to the plain uncovered-max pick.
				CPos? frontCenter = null;
				if (Info.UseRegionRoles)
				{
					regionRoles ??= player.PlayerActor.TraitsImplementing<IBotRegionRoles>()
						.FirstOrDefault(p => p.RolesReady);
					if (regionRoles != null && regionRoles.RolesReady)
						frontCenter = PickFrontierCenter(baseCells, roleDefences, Info.FrontLinkRadius, regionRoles.RoleAtCell);
				}

				if (frontCenter == null)
					frontCenter = PickFrontCenter(baseCells, roleDefences, Info.FrontLinkRadius);
				if (frontCenter is CPos picked)
					baseCenter = picked;
			}

			// Perimeter quota is measured around the EFFECTIVE centre (the front, when DEF-3
			// retargeted it) — an outpost's own ring splits interior/perimeter locally.
			foreach (var d in roleDefences)
			{
				if (Edgeness(d.Center, baseCenter, maxRadius) >= Info.PerimeterEdgePercent)
					perimeter++;
				else
					interior++;
			}

			var cells = world.Map.FindTilesInAnnulus(baseCenter, minRadius, maxRadius).ToArray();
			var stride = Math.Max(1, (cells.Length + Info.MaxCandidates - 1) / Math.Max(1, Info.MaxCandidates));

			// The quota picks the ring; an empty ring falls back to the other rather than to nothing.
			var wantPerimeter = PlacePerimeter(perimeter, interior, Info.PerimeterSharePercent);
			var threat = ThreatCell();
			CPos? best = null;
			var bestScore = int.MinValue;
			int bestNew = 0, bestEdge = 0, bestThreat = 0;
			var bestOnWanted = false;
			for (var i = 0; i < cells.Length; i += stride)
			{
				var cell = cells[i];
				if (!canPlace(cell))
					continue;

				var edge = Edgeness(cell, baseCenter, maxRadius);
				var onWanted = (edge >= Info.PerimeterEdgePercent) == wantPerimeter;
				if (best != null && bestOnWanted && !onWanted)
					continue;

				var n = 0;
				foreach (var role in roles)
					n += NewlyCovered(cell, range, uncovered[role]);

				// Inside, only the coverage of the base counts; on the perimeter the edge and threat bias stay.
				var t = wantPerimeter ? ThreatAlignment(cell, baseCenter, threat) : 0;
				var score = Score(n, wantPerimeter ? edge : 0, t, Info.EdgeWeight, Info.ThreatWeight);
				if ((onWanted && !bestOnWanted) || score > bestScore)
				{
					bestScore = score;
					best = cell;
					bestNew = n;
					bestEdge = edge;
					bestThreat = t;
					bestOnWanted = onWanted;
				}
			}

			if (best == null)
				return null;

			Log.Write("debug", $"AI ({player.ClientIndex}): DEFENSE PLACE {defense.Name} at {best.Value}: covers {bestNew} new base cells " +
				$"(roles {string.Join("+", roles)}), {(wantPerimeter ? "perimeter" : "interior")} ({perimeter} out / {interior} in), edge {bestEdge}, threat {bestThreat}" +
				(bestNew == 0 ? " [no new coverage: redundant edge/threat cell]" : "") + $" at tick {world.WorldTick}");
			return best;
		}

		// Fog-honest direction of the enemy: the centroid of the defences we REMEMBER of the main target (else of any
		// enemy), else the map centre. Nothing here enumerates the world's actors.
		CPos ThreatCell()
		{
			var main = player.PlayerActor.TraitsImplementing<IBotMainTargetProvider>().Select(p => p.MainTarget).FirstOrDefault(t => t != null);
			var remembered = player.PlayerActor.TraitsImplementing<IBotRememberedDefenceProvider>()
				.SelectMany(p => p.RememberedDefences()).ToArray();
			var pool = main != null ? remembered.Where(d => d.Enemy == main).ToArray() : remembered;
			if (pool.Length == 0)
				pool = remembered;

			if (pool.Length > 0)
				return new CPos((int)pool.Average(d => d.Cell.X), (int)pool.Average(d => d.Cell.Y));

			var size = world.Map.MapSize;
			return new CPos(size.Width / 2, size.Height / 2);
		}
	}
}
