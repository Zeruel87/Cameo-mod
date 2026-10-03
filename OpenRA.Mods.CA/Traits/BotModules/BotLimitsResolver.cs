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

using OpenRA.Mods.Common.Traits;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// LC4 (AI_MASTER_PLAN §3, the conditional-trait cache class). Actor.Initialize grants every bot condition during
	/// INotifyCreated, then notifies the condition observers in HashSet order: a module enabled by `genericbot` /
	/// `classicbot` can therefore run TraitEnabled BEFORE `BotLimits@<tier>` is enabled, and a BotLimits cached there
	/// is null (or another tier's) for the whole match. BaseBuilderBotModuleCA and UnitBuilderBotModuleCA already
	/// re-resolve on their first bot tick; this is that fix, shared, with a debug.log line whenever it corrects a value.
	/// </summary>
	public static class BotLimitsResolver
	{
		public static BotLimits Current(Player player) =>
			player.PlayerActor.TraitsImplementing<BotLimits>().FirstEnabledTraitOrDefault();

		public static string Describe(BotLimits limits) =>
			limits == null ? "none" : limits.Info.RequiresCondition?.Expression ?? "unconditional";

		/// <summary>Resolve again on the module's first bot tick. One debug.log line per module either way: "kept" proves
		/// the re-check ran and names the tier; "corrected" is the bug caught (and the only case that changes behaviour).</summary>
		public static BotLimits Recheck(Player player, BotLimits cached, string module)
		{
			var current = Current(player);
			var verdict = current == cached ? "kept" : $"CORRECTED from {Describe(cached)}";
			Log.Write("debug", $"AI ({player.ClientIndex}): LC4 {module} BotLimits on its first tick: {Describe(current)}, {verdict} (tick {player.World.WorldTick})");
			return current;
		}
	}
}
