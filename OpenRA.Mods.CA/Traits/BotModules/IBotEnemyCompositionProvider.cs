#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System.Collections.Generic;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// The enemy army as this bot has SEEN it: remembered mobile combat value by actor type. Implemented by
	/// Cameo's master AI from its fog memory. Returns false when the bot is not observing through fog
	/// (no provider, provider disabled, or a map without shroud); the caller may then fall back to the
	/// legacy omniscient sample, which is what the `classic` bot type deliberately keeps.
	/// </summary>
	public interface IBotEnemyCompositionProvider
	{
		bool TryGetEnemyComposition(out IReadOnlyDictionary<string, int> valueByActorType);
	}
}
