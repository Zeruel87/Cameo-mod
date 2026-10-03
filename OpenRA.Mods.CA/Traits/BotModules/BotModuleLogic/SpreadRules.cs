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

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>Pure building-gap rule (AI_ARCHITECTURE 12.20: the spacing advisor owns the numbers, findPos applies them).</summary>
	public static class BuildingGapRule
	{
		/// <summary>Every cell within <paramref name="gap"/> cells (Chebyshev) of any footprint cell; a candidate footprint touching this set is rejected.</summary>
		public static HashSet<CPos> BufferCells(IEnumerable<CPos> ownFootprintCells, int gap)
		{
			var cells = new HashSet<CPos>();
			if (gap <= 0)
				return cells;

			foreach (var tile in ownFootprintCells)
				for (var dx = -gap; dx <= gap; dx++)
					for (var dy = -gap; dy <= gap; dy++)
						cells.Add(new CPos(tile.X + dx, tile.Y + dy));

			return cells;
		}

		/// <summary>Gap to apply: no advisor (null) = none; defence placements use their own, tighter value.</summary>
		public static int Resolve(IBotPlacementAdvisor advisor, bool defense) =>
			advisor == null || !advisor.IsActive ? 0 : Math.Max(0, defense ? advisor.MinBuildingGapDefensesCells : advisor.MinBuildingGapCells);
	}

	/// <summary>Pure per-field harvester cap (HarvesterBotModuleCA.MaxHarvestersPerResourceIndice; 0 or negative = unlimited).</summary>
	public static class HarvesterFieldCap
	{
		public static bool Saturated(int harvesters, int cap) => cap > 0 && harvesters >= cap;

		/// <summary>Harvesters beyond the cap that should be pushed to lacking fields (0 when unlimited).</summary>
		public static int Surplus(int harvesters, int cap) => Saturated(harvesters, cap) ? harvesters - cap : 0;

		/// <summary>How many of <paramref name="lack"/> a receiving field may take: its own cap headroom only.</summary>
		public static int Need(int lack, int harvesters, int cap) => cap > 0 ? Math.Min(lack, cap - harvesters) : lack;
	}
}
