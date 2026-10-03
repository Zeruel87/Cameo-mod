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
	/// Scale targets (DESIGN 19.10, AI_ARCHITECTURE 12.22): HOW BIG the base and army should be, one number per
	/// size category, grown from the difficulty line, the enemy the bot has SEEN, the unscouted map, the
	/// personality and game time. Providers live in OpenRA.Mods.Cameo and must not be referenced by name from
	/// this assembly. A consumer reads this ONLY when an enabled provider answers true; no provider (classic, or
	/// the switch off) or a false answer means the consumer's own limit runs unchanged, bit-identical.
	/// Categories: army, harvester, refinery, production, conyard, tech, superweapon, defence, aircraft.
	/// </summary>
	public interface IBotScaleTargets
	{
		/// <summary>The target count of <paramref name="category"/> (army/defence are values, the rest counts). False when disabled or unknown.</summary>
		bool TryGetTarget(string category, out int target);

		/// <summary>
		/// The attack-force value target. <paramref name="baselineValue"/> is the caller's personality
		/// SquadValue: the own-side term is baseline x the difficulty/time line, the enemy term is what was seen.
		/// </summary>
		bool TryGetArmyValueTarget(int baselineValue, out int value);

		/// <summary>
		/// The per-building limit for a building the provider's rules-derived tags put in the `tech` or
		/// `superweapon` category. False for every other building: its own BuildingLimits entry stands.
		/// </summary>
		bool TryGetBuildingTarget(string actorName, out int target);
	}

	/// <summary>Consumer helpers: ask the first enabled provider that answers.</summary>
	public static class BotScaleTargets
	{
		public static bool TryTarget(this IBotScaleTargets[] providers, string category, out int target)
		{
			if (providers != null)
				foreach (var provider in providers)
					if (provider.TryGetTarget(category, out target))
						return true;

			target = 0;
			return false;
		}

		public static bool TryArmyValue(this IBotScaleTargets[] providers, int baselineValue, out int value)
		{
			if (providers != null)
				foreach (var provider in providers)
					if (provider.TryGetArmyValueTarget(baselineValue, out value))
						return true;

			value = 0;
			return false;
		}

		public static bool TryBuilding(this IBotScaleTargets[] providers, string actorName, out int target)
		{
			if (providers != null)
				foreach (var provider in providers)
					if (provider.TryGetBuildingTarget(actorName, out target))
						return true;

			target = 0;
			return false;
		}
	}
}
