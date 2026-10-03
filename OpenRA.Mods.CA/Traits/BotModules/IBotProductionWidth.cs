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
	/// Settings seam (same shape as <see cref="IBotAssaultFormation"/>): how many idle queues of one
	/// production category a unit-builder call may fill in a pass. With no enabled provider the unit
	/// builder keeps the upstream behaviour — first free queue only. Providers live in
	/// OpenRA.Mods.Cameo and must not be referenced by name here.
	/// </summary>
	public interface IBotProductionWidth
	{
		/// <summary>Upper bound on idle queues filled per BuildUnit call; 1 = upstream single-queue fill.</summary>
		int MaxQueuesPerCategory { get; }
	}
}
