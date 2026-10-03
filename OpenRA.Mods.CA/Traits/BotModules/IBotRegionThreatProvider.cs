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
	/// A fog-honest hostile-strength reading around a cell, from whatever memory
	/// the provider owns (region memory, scout danger marks). 0 means unknown —
	/// never penalised. Consumed by <c>SquadManagerBotModuleCA</c>'s pre-commit
	/// risk gate (AI_FRANSBOT_RESEARCH.md 6c); providers live in OpenRA.Mods.Cameo
	/// and must not be referenced by name from this assembly.
	/// </summary>
	public interface IBotRegionThreatProvider
	{
		int RememberedEnemyThreatAt(CPos cell);
	}
}
