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

using System;
using System.Collections.Generic;
using OpenRA.Mods.Common.Traits;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// DESIGN §19.1 / §22 ("one implementation per mechanic"): THE bot difficulty ladder.
	/// Resolve a <see cref="Player.BotType"/> to a rank (aliases applied), then interpolate any
	/// Min/Max pair on one equal-step line between the easiest and the hardest tier. Shared by
	/// DynamicBotInsurance (OpenRA.Mods.Cameo) and the Frans modules' Min*/Max* knobs (F1).
	/// </summary>
	public static class BotDifficultyLadder
	{
		/// <summary>
		/// Canonical ladder in bot-type space, easiest to hardest — what <see cref="Player.BotType"/>
		/// returns. The BotLimits tier namespace differs at the top only: `BotLimits@god` vs bot type
		/// `cameogod`. Consumers carrying their own yaml-overridable list (DynamicBotInsurance.Difficulties)
		/// pass it explicitly; Frans modules use this one.
		/// </summary>
		public static readonly string[] Difficulties =
		{
			"easiest", "veryeasy", "easy", "medium", "hard",
			"veryhard", "brutal", "challenger", "unbeatable", "cameogod"
		};

		/// <summary>
		/// Bot types that play AS a ladder tier: `classic` is the A/B reference (old hard plus full map
		/// vision), `fransbot` the hidden donor stack, the exploit_* league bots run at hard.
		/// </summary>
		public static readonly IReadOnlyDictionary<string, string> DefaultAliases = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
		{
			["classic"] = "hard",
			["fransbot"] = "hard",
			["exploit_rush"] = "hard",
			["exploit_turtle"] = "hard",
			["exploit_guerrilla"] = "hard",
		};

		/// <summary>Bot-type rank on the ladder, aliases applied. -1 = not a listed bot.</summary>
		public static int RankOf(Player owner, string[] difficulties = null, IReadOnlyDictionary<string, string> aliases = null)
		{
			if (owner == null || !owner.IsBot || string.IsNullOrEmpty(owner.BotType))
				return -1;

			var botType = owner.BotType;
			if (aliases != null && aliases.TryGetValue(botType, out var alias))
				botType = alias;

			return Array.FindIndex(difficulties ?? Difficulties,
				d => string.Equals(d, botType, StringComparison.OrdinalIgnoreCase));
		}

		/// <summary>Linear interpolation across the difficulty list by rank index (rank 0 → min, last → max).</summary>
		public static int InterpolateByRank(int min, int max, int rank, int difficultyCount)
		{
			var steps = difficultyCount - 1;
			if (steps <= 0)
				return min;

			return min + ((max - min) * rank) / steps;
		}

		/// <summary>Resolve + interpolate in one step on the canonical ladder. Unranked owners get <paramref name="unranked"/>.</summary>
		public static int Scale(int min, int max, Player owner, int unranked = 0)
		{
			var rank = RankOf(owner);
			return rank < 0 ? unranked : InterpolateByRank(min, max, rank, Difficulties.Length);
		}
	}
}
