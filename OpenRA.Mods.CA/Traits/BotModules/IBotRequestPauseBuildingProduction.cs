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
	/// Voting seam, the building-side mirror of <see cref="IBotRequestPauseUnitProduction"/> (which is an
	/// OR-of-vetoes, DESIGN §19.4 R4): any provider returning true makes the base-builder queues hold off
	/// queueing new non-refinery buildings for the tick. With no providers nothing pauses — upstream behaviour
	/// is byte-identical. Providers live in OpenRA.Mods.Cameo and must not be referenced by name here.
	/// </summary>
	public interface IBotRequestPauseBuildingProduction
	{
		/// <summary>
		/// Whether the base builder should hold <paramref name="building"/> this tick. <paramref name="essential"/>
		/// is the base builder's own classification (construction yard, refinery, power, first production
		/// building) - providers normally let essentials through so the economy and tech chain never stall.
		/// </summary>
		bool PausesBuilding(ActorInfo building, bool essential);
	}
}
