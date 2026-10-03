#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 *
 * Written for the CN4 region-roles port (crystallized-nexus
 * CNRegionManagerBotModule, GPLv3, Copyright (c) The Crystallized Nexus
 * Developers).
 */
#endregion

using System.Collections.Generic;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>
	/// What a held region is for, once <see cref="RegionRolesBotModule"/> has classified it.
	/// Port of the donor's CNRegionRole: the region's shape is a shared terrain fact
	/// (<see cref="Zone"/>); the role is one bot's own reading of it and is deliberately not shared.
	/// </summary>
	public enum RegionRole
	{
		/// <summary>Unheld, unready, or a region the bot holds but steers nothing toward.</summary>
		None,

		/// <summary>The starting region (or its fallback). Exclusive: exactly one at a time.</summary>
		Core,

		/// <summary>Held ground carrying the resources. Non-exclusive.</summary>
		Economy,

		/// <summary>Held ground bordering an enemy-believed region. Exclusive: steers the front.</summary>
		Military,

		/// <summary>Held ground too small to be anything else; mostly a door onto something that matters.</summary>
		Outpost,
	}

	/// <summary>
	/// Per-region claim + role answers published by <see cref="RegionRolesBotModule"/> (the CN4 port).
	/// Read with the region ids <see cref="IBotZoneTopology"/> hands out — both are invalidated by the
	/// same <see cref="IBotZoneTopology.Generation"/> bump (a bridge re-cut reshuffles them).
	/// <para>
	/// Advisors consume this; only the provider decides the roles (one owner per decision).
	/// Consumers must tolerate <see cref="RegionRole.None"/> — it means unheld, unbuilt or not yet
	/// classified, and it is the normal answer while the topology is still being adopted.
	/// </para>
	/// </summary>
	public interface IBotRegionRoles
	{
		/// <summary>True once regions have been classified at least once.</summary>
		bool RolesReady { get; }

		/// <summary>The role of a held region, or <see cref="RegionRole.None"/> for unheld/unknown ids.</summary>
		RegionRole RoleOf(int regionId);

		/// <summary>
		/// The role of the region a cell sits in — the provider does the
		/// <see cref="IBotZoneTopology.NearestRegionId"/> hop for cells on a gate corridor or barrier.
		/// </summary>
		RegionRole RoleAtCell(CPos cell);

		/// <summary>Whether this bot holds the region (a construction yard or enough buildings stand there).</summary>
		bool IsHeld(int regionId);

		/// <summary>The region's weighted value (0-100): resources + buildable space + security. Terrain-only.</summary>
		int ValueOf(int regionId);

		/// <summary>Region ids currently carrying <paramref name="role"/> (empty when none).</summary>
		IReadOnlyList<int> RegionsWithRole(RegionRole role);
	}
}
