#region Copyright & License Information
/*
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
	/// One static defence the bot has actually seen (live or through the
	/// engine's frozen-actor layer): where it was, what it was worth, and the
	/// longest weapon range its observed type carries. MaxRangeCells is
	/// derived from public ruleset data for the observed type — never from
	/// hidden state — so the value is fog-honest. CA-2 siege planning
	/// (AI_ARCHITECTURE §12.6) reads this to place its stand-off line.
	/// </summary>
	public readonly struct BotRememberedDefence
	{
		public readonly CPos Cell;
		public readonly int Value;
		public readonly int MaxRangeCells;
		public readonly int LastSeenTick;
		public readonly OpenRA.Player Enemy;

		// The observed actor type — public ruleset data for something the bot
		// actually saw; BotUnitProfiles resolves it for the combat predictor.
		public readonly ActorInfo Observed;

		public BotRememberedDefence(CPos cell, int value, int maxRangeCells, int lastSeenTick, OpenRA.Player enemy, ActorInfo observed)
		{
			Cell = cell;
			Value = value;
			MaxRangeCells = maxRangeCells;
			LastSeenTick = lastSeenTick;
			Enemy = enemy;
			Observed = observed;
		}
	}

	/// <summary>
	/// Fog-honest remembered static defences, from whatever memory the provider
	/// owns. Implemented by master-AI modules that keep the fog table; an empty
	/// sequence means nothing observed, never "no defences exist".
	/// </summary>
	public interface IBotRememberedDefenceProvider
	{
		IEnumerable<BotRememberedDefence> RememberedDefences();
	}
}
