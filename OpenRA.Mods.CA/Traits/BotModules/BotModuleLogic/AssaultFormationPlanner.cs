#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// Assault fan-out geometry (the line-of-death fix): places one slot per squad
	/// member on an arc around the target, centered on the far side from the
	/// squad's approach bearing, so the wave wraps the target and every member
	/// fires from its own angle at the commit instead of feeding a single
	/// corridor one by one. Pure integer math on the <see cref="WAngle"/> cosine
	/// LUT and CPos cell space — deterministic across peers, no RNG, no floats,
	/// no World access (callers inject the cell-usability predicate).
	/// </summary>
	public static class AssaultFormationPlanner
	{
		/// <summary>
		/// Per-unit slot cells, in the same order as <paramref name="units"/>.
		/// The arc spans <paramref name="arcDegrees"/> around
		/// <paramref name="targetCell"/> at <paramref name="radiusCells"/>, centred
		/// on the bearing from the squad centroid to the target (the far side —
		/// units wrap around the objective, facing inward).
		/// Slots are deduplicated and filtered through
		/// <paramref name="isUsableCell"/> (the map-bounds check is the caller's);
		/// members beyond the usable count fold onto the target cell itself, as
		/// does every member when nothing on the ring is usable — the honest
		/// collapse back to the old single-point attack.
		/// <paramref name="arc"/> receives the distinct usable slots in ascending
		/// angular order, for callers that must place late joiners.
		/// </summary>
		public static CPos[] PlanSlots(
			IReadOnlyList<(CPos Cell, uint ActorId)> units,
			CPos targetCell,
			int radiusCells,
			int arcDegrees,
			Func<CPos, bool> isUsableCell,
			out CPos[] arc)
		{
			arc = [];
			var count = units?.Count ?? 0;
			if (count == 0)
				return [];

			radiusCells = Math.Max(0, radiusCells);
			var arcSpan = Math.Clamp(arcDegrees, 1, 360) * 1024 / 360; // WAngle units, 1024 = 360 degrees

			// Squad centroid in cell space gives the approach bearing: centroid -> target.
			long cx = 0, cy = 0;
			foreach (var u in units)
			{
				cx += u.Cell.X;
				cy += u.Cell.Y;
			}

			var centroid = new CPos((int)(cx / count), (int)(cy / count));
			var approach = WAngle.ArcTan(targetCell.Y - centroid.Y, targetCell.X - centroid.X).Angle;

			// The usable ring slots, deduplicated, in ascending angular order.
			var usable = new List<(int Angle, CPos Cell)>(count);
			var seen = new HashSet<CPos>();
			for (var i = 0; i < count; i++)
			{
				var angle = new WAngle(count == 1
					? approach
					: approach - arcSpan / 2 + (int)((long)arcSpan * i / (count - 1)));

				var cell = new CPos(
					targetCell.X + radiusCells * angle.Cos() / 1024,
					targetCell.Y + radiusCells * angle.Sin() / 1024);

				if (!seen.Add(cell) || (isUsableCell != null && !isUsableCell(cell)))
					continue;

				usable.Add((angle.Angle, cell));
			}

			usable.Sort(static (a, b) => a.Angle.CompareTo(b.Angle));
			arc = usable.Select(u => u.Cell).ToArray();

			// Assignment: members are processed in angular order — sorted by their
			// bearing FROM the target, ties on ActorId (the documented tiebreak) —
			// and each takes the still-free slot nearest its own bearing by
			// circular distance. Each member keeps its own side: no two approach
			// chains cross more than the arc itself forces. Members beyond the
			// usable count collapse onto the target cell — the old single-point
			// attack, honestly degraded.
			var order = new int[count];
			var bearings = new int[count];
			for (var i = 0; i < count; i++)
			{
				order[i] = i;
				bearings[i] = WAngle.ArcTan(units[i].Cell.Y - targetCell.Y, units[i].Cell.X - targetCell.X).Angle;
			}

			Array.Sort(order, (a, b) =>
			{
				var c = bearings[a].CompareTo(bearings[b]);
				return c != 0 ? c : units[a].ActorId.CompareTo(units[b].ActorId);
			});

			var result = new CPos[count];
			if (usable.Count == 0)
			{
				foreach (var j in order)
					result[j] = targetCell;

				return result;
			}

			var taken = new bool[usable.Count];
			foreach (var j in order)
			{
				var best = -1;
				var bestDistance = int.MaxValue;
				for (var k = 0; k < usable.Count; k++)
				{
					if (taken[k])
						continue;

					var diff = Math.Abs(bearings[j] - usable[k].Angle);
					var distance = Math.Min(diff, 1024 - diff);
					if (distance < bestDistance)
					{
						bestDistance = distance;
						best = k;
					}
				}

				// No free slot left — the member folds onto the objective itself,
				// the old single-point attack for that one unit.
				result[j] = best < 0 ? targetCell : usable[best].Cell;
				if (best >= 0)
					taken[best] = true;
			}

			return result;
		}

		/// <summary>
		/// Index of the slot closest to <paramref name="cell"/> — where a member
		/// that joined after the plan was laid goes. -1 on an empty list.
		/// </summary>
		public static int NearestSlotIndex(CPos cell, IReadOnlyList<CPos> slots)
		{
			var best = -1;
			var bestSquared = long.MaxValue;
			for (var i = 0; i < slots.Count; i++)
			{
				var distance = (long)(slots[i] - cell).LengthSquared;
				if (distance < bestSquared)
				{
					bestSquared = distance;
					best = i;
				}
			}

			return best;
		}
	}
}
