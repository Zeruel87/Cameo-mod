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
	/// <summary>An enemy group predicted to hit an own asset (AI_DEEP_RESEARCH.md §14, phase DF).</summary>
	public readonly record struct BotPredictedThreat(CPos Target, int EtaTicks, int Value, int PredictedAtTick);

	/// <summary>Published by the master module from its fog-honest group tracking; read by the squad manager.</summary>
	public interface IBotThreatPredictionProvider
	{
		IReadOnlyList<BotPredictedThreat> PredictedThreats { get; }

		/// <summary>The base is under PERCEIVED threat now: enemy pressure at home, or the master is Pressured/Emergency.</summary>
		bool PerceivedBaseThreat { get; }
	}
}
