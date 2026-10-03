#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// The strategist's bipolar posture axes (UT-1, AI_DEEP_RESEARCH.md §5.1): each value is
	/// in [0,100] with 100 the SECOND-named pole and <see cref="Neutral"/> the midpoint.
	/// Published by the master bot module from its per-snapshot utility computation over
	/// fog-honest inputs; consumers must treat a missing or disabled provider as neutral —
	/// never penalised, never a behaviour change. Providers live in OpenRA.Mods.Cameo and
	/// must not be referenced by name from this assembly.
	/// </summary>
	public interface IBotUtilityAxes
	{
		const int Neutral = 50;

		/// <summary>0 = Turtle (hold, fortify, bleed the attacker), 100 = Rush (attack early and often).</summary>
		int UtilityTurtleRush { get; }

		/// <summary>0 = TechRush (tech up behind a held home front), 100 = Expansion (take the map).</summary>
		int UtilityTechRushExpansion { get; }

		/// <summary>0 = Steamroller (one massed frontal force), 100 = Guerrilla (raids and harassment).</summary>
		int UtilitySteamrollerGuerrilla { get; }
	}
}
