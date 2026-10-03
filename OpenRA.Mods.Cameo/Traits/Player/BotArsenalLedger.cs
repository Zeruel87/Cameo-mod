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
using System.Linq;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("The arsenal ledger (AI_ARCHITECTURE.md §12.3, phase CA-1): per actor type, how many this player created and",
		"lost, the value lost, and the value of what that type destroyed, broken down by victim type. Filled by Cameo's",
		"UpdatesPlayerStatistics shadow; read only by bot code and the match log. Never synced, never read by the simulation.")]
	public class BotArsenalLedgerInfo : TraitInfo<BotArsenalLedger> { }

	public class BotArsenalLedger
	{
		public sealed class Entry
		{
			public int Created;
			public int Lost;
			public int LostValue;
			public int KilledValue;

			// Victim type -> value this attacker type destroyed of it: the data a per-type combat factor is fitted from.
			public readonly Dictionary<string, int> KilledValueByVictim = new(StringComparer.Ordinal);
		}

		readonly Dictionary<string, Entry> byType = new(StringComparer.Ordinal);

		public IReadOnlyDictionary<string, Entry> ByType => byType;

		Entry Of(string type)
		{
			if (!byType.TryGetValue(type, out var entry))
				byType[type] = entry = new Entry();

			return entry;
		}

		public void RecordCreated(string type) => Of(type).Created++;

		public void RecordLost(string type, int value)
		{
			var entry = Of(type);
			entry.Lost++;
			entry.LostValue += value;
		}

		public void RecordKill(string attackerType, string victimType, int value)
		{
			var entry = Of(attackerType);
			entry.KilledValue += value;
			entry.KilledValueByVictim[victimType] = entry.KilledValueByVictim.GetValueOrDefault(victimType) + value;
		}

		/// <summary>Types ordered by what they destroyed, then lost: the ledger as the match log prints it.</summary>
		public IEnumerable<KeyValuePair<string, Entry>> Ordered() =>
			byType.OrderByDescending(kv => kv.Value.KilledValue).ThenByDescending(kv => kv.Value.LostValue).ThenBy(kv => kv.Key, StringComparer.Ordinal);
	}
}
