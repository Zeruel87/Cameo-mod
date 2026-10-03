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

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// Lets a planner choose where the base builder puts a defence. With no ACTIVE advisor the base builder keeps its
	/// own placement (the roll toward the enemy, else a random base cell), draw for draw. Advisors live in
	/// OpenRA.Mods.Cameo and must not be referenced by name here.
	/// </summary>
	public interface IBotDefensePlacementAdvisor
	{
		/// <summary>Whether this advisor is enabled; an inactive advisor is never asked.</summary>
		bool IsActive { get; }

		/// <summary>
		/// The cell for <paramref name="defense"/> (an anti-air defence when <paramref name="antiAir"/>), or null to
		/// leave the choice to the base builder. <paramref name="canPlace"/> applies the base builder's own placement checks.
		/// </summary>
		CPos? ChooseDefenseCell(ActorInfo defense, bool antiAir, CPos baseCenter, Func<CPos, bool> canPlace);
	}
}
