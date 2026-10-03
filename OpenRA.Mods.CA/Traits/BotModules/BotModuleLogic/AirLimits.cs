#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>Pure arithmetic of the AI aircraft limits (CA F2p2, 71754fc06), split out so it is unit-testable.</summary>
	public static class AirLimits
	{
		/// <summary>
		/// Enemy air threats as the bot has SEEN them: for each AirThreatUnits type present in the observed composition,
		/// remembered value / unit cost (rounded up, at least 1). Approximation: the provider reports value-by-type, not a
		/// head count, so the count is derived from the cost; an unknown cost (0) counts the type once.
		/// </summary>
		public static int EstimateObservedThreatCount(IReadOnlyDictionary<string, int> valueByActorType, IEnumerable<string> threatTypes, Func<string, int> costOf)
		{
			if (valueByActorType == null)
				return 0;

			var count = 0;
			foreach (var type in threatTypes)
			{
				if (!valueByActorType.TryGetValue(type, out var value) || value <= 0)
					continue;

				var cost = costOf(type);
				count += cost > 0 ? Math.Max(1, (value + cost - 1) / cost) : 1;
			}

			return count;
		}

		/// <summary>Air-superiority limit: match the enemy threat count (+1), never below the base limit, capped by MaxAirSuperiority.</summary>
		public static int AirSuperiorityLimit(int baseLimit, int enemyThreatCount, int friendlyAirToAirCount, bool queuedCountsAsFriendly, int maxAirSuperiority)
		{
			// Legacy: the friendly A2A units reduce the limit. CA F2p2: they are part of the current count instead.
			var limit = queuedCountsAsFriendly
				? Math.Max(enemyThreatCount + 1, baseLimit)
				: Math.Max(enemyThreatCount - friendlyAirToAirCount + 1, baseLimit);

			if (maxAirSuperiority > 0)
				limit = Math.Min(maxAirSuperiority, limit);

			return limit;
		}
	}
}
