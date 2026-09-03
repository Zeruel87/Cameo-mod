#region Copyright & License Information
/*
 * Ported to Cameo from OpenRA Combined Arms (github.com/Inq8/CAmod), which is
 * free software under the GNU General Public License. See COPYING.
 *
 * Cameo changes: namespace OpenRA.Mods.CA.* -> OpenRA.Mods.Cameo.*.
 */
#endregion

using System;
using System.Collections.Generic;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Allows arbitrary counts.")]
	public class CountManagerInfo : TraitInfo
	{
		[Desc("Maximum count for specific count types.")]
		public readonly Dictionary<string, int> MaxCounts = new();

		public override object Create(ActorInitializer init) { return new CountManager(this); }
	}

	public class CountManager
	{
		public Dictionary<string, int> Counts { get; }
		public CountManagerInfo Info { get; }
		public event Action<string, int> Incremented;
		public event Action<string, int> Decremented;

		public CountManager(CountManagerInfo info)
		{
			Counts = new Dictionary<string, int>();
			Info = info;
		}

		public void Increment(string type)
		{
			if (!Counts.ContainsKey(type))
				Counts[type] = 0;

			if (Info.MaxCounts.TryGetValue(type, out var maxCount) && Counts[type] >= maxCount)
				return;

			Counts[type]++;
			Incremented?.Invoke(type, Counts[type]);
		}

		public void Decrement(string type)
		{
			if (!Counts.TryGetValue(type, out var value))
				return;

			if (value <= 0)
				return;

			Counts[type] = --value;
			Decremented?.Invoke(type, value);
		}
	}
}
