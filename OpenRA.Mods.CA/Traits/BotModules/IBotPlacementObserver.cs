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
	/// Record-only observer of the base builder's placement orders (AI_ARCHITECTURE 12.24 FE-0 / 12.25 BO-0). Implemented by a world
	/// trait in OpenRA.Mods.Cameo (the placement log); this assembly must not reference it by name. The observer must never feed a
	/// decision: the base builder ignores everything about it, so an absent observer leaves behaviour bit-identical.
	/// </summary>
	public interface IBotPlacementObserver
	{
		/// <summary>
		/// A bot issued the placement order for <paramref name="actor"/> at <paramref name="cell"/>.
		/// <paramref name="reason"/> is one of crawl, refinery_claim, base, defence, other; <paramref name="queuedTick"/> is the tick the
		/// item entered production (the placed tick when that was not seen).
		/// </summary>
		void BuildingPlaced(Player owner, int tick, string actor, CPos cell, string reason, int queuedTick);
	}
}
