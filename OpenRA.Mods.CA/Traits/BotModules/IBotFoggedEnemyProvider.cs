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

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// Reports whether bot squads should observe fog of war when scanning for
	/// targets. Implemented by master-AI modules that maintain a fogged
	/// observation snapshot; when the provider is absent or reports false,
	/// squad scans fall back to the legacy omniscient enumeration.
	/// </summary>
	public interface IBotFoggedEnemyProvider
	{
		/// <summary>Whether squad target scans should only consider what the bot can see or remember.</summary>
		bool FoggedObservation { get; }
	}
}
