/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// A bounded multiplier on one candidate's share in the unit builder, in percent (100 = neutral).
	/// The unit builder consults it only while at least one provider is ACTIVE; with none (classic has no provider,
	/// genericbot has it switched off by default) unit choice and its random draws are exactly as before.
	/// Implemented by Cameo's BotLearnedPriors.
	/// </summary>
	public interface IBotProductionWeight
	{
		bool IsActive { get; }

		int WeightPercent(Player self, ActorInfo unit);
	}
}
