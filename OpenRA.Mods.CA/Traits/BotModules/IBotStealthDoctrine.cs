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
	/// One detector the bot has actually seen (live or through the engine's
	/// frozen-actor layer): where it was, the detection radius its observed
	/// type carries, and when it was last observed. RangeCells is derived
	/// from public ruleset data for the observed type — never from hidden
	/// state — so the value is fog-honest. The stealth squad states
	/// (AI_MASTER_PLAN §3, CN3) read this to route around and abort on
	/// remembered detection coverage.
	/// </summary>
	public readonly struct BotKnownDetector
	{
		public readonly CPos Cell;
		public readonly int RangeCells;
		public readonly int LastSeenTick;
		public readonly OpenRA.Player Enemy;

		public BotKnownDetector(CPos cell, int rangeCells, int lastSeenTick, OpenRA.Player enemy)
		{
			Cell = cell;
			RangeCells = rangeCells;
			LastSeenTick = lastSeenTick;
			Enemy = enemy;
		}
	}

	/// <summary>
	/// Fog-honest remembered DetectCloaked carriers, from whatever memory the
	/// provider owns. Implemented by master-AI modules that keep the fog
	/// table; an empty sequence means nothing observed, never "no detectors
	/// exist".
	/// </summary>
	public interface IBotStealthDoctrine
	{
		IEnumerable<BotKnownDetector> RememberedDetectors();
	}
}
