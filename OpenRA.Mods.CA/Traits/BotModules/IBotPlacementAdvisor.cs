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

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// Lets a planner re-rank the candidate cells <c>findPos</c> already validated for a building, so an
	/// advisor can prefer spread-out placement over the first legal cell in scan order. With no ACTIVE advisor
	/// the base builder keeps its draw-for-draw placement (first valid cell wins, no building gap). The advisor is
	/// also the single owner of the building-gap rule (hard reject of cells near own footprints). Advisors live in
	/// OpenRA.Mods.Cameo and must not be referenced by name here.
	/// </summary>
	public interface IBotPlacementAdvisor
	{
		/// <summary>Whether this advisor is mounted; an inactive advisor owns nothing (no gap, no re-rank).</summary>
		bool IsActive { get; }

		/// <summary>Whether <see cref="ChooseCell"/> should be asked at all (the re-ranking switch).</summary>
		bool RanksCandidates { get; }

		/// <summary>Cells of empty space a new building keeps to every own building footprint (0 = none).</summary>
		int MinBuildingGapCells { get; }

		/// <summary>The same gap for defence placements, so walls/turrets can still form tighter lines.</summary>
		int MinBuildingGapDefensesCells { get; }

		/// <summary>
		/// Pick one cell from <paramref name="candidates"/> for <paramref name="building"/>, or null to keep the
		/// caller's own first-valid choice. <paramref name="candidates"/> contains ONLY cells that already passed
		/// the caller's placement checks (CanPlaceBuilding, IsCloseEnoughToBase, distanceRequirement) — the
		/// advisor must not introduce cells the caller would have rejected.
		/// </summary>
		CPos? ChooseCell(ActorInfo building, IReadOnlyList<CPos> candidates, Func<CPos, bool> stillPlaceable);
	}
}
