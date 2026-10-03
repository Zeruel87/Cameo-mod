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

using System.Collections.Generic;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// Computes coarse, threat-aware waypoints for a squad's move/attack-move —
	/// phase 6e risk routing (docs/design/AI_FRANSBOT_RESEARCH.md). Implemented
	/// by master-AI modules that keep a region memory; squads call it only as a
	/// suggestion and fall back to their normal routing when it returns null.
	/// </summary>
	public interface IBotRouteThreatRouter
	{
		/// <summary>
		/// Waypoints (ending at <paramref name="to"/>) that avoid remembered enemy
		/// threat, or null when the router is disabled or has no useful detour.
		/// <paramref name="leader"/> identifies the squad so the router can match
		/// waypoints to its locomotor.
		/// </summary>
		List<CPos> RouteAroundThreat(Actor leader, CPos to, int maxWaypoints);
	}
}
