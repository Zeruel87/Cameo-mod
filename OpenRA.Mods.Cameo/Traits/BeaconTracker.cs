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
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	// World-level record of beacon placements, written by the PlaceBeacon shadow in
	// synced code and read by bot modules (read-only for bots — never write back).
	[TraitLocation(SystemActors.World)]
	[Desc("Records beacon placements (owner, position, tick) for bot beacon response.")]
	public class BeaconTrackerInfo : TraitInfo
	{
		[Desc("Ticks a beacon record stays queryable. Should cover the beacon Duration.")]
		public readonly int MemoryTicks = 1500;

		public override object Create(ActorInitializer init) { return new BeaconTracker(init.Self, this); }
	}

	public sealed class BeaconTracker : ITick
	{
		public readonly struct Entry
		{
			public readonly OpenRA.Player Owner;
			public readonly WPos Position;
			public readonly int Tick;

			public Entry(OpenRA.Player owner, WPos position, int tick)
			{
				Owner = owner;
				Position = position;
				Tick = tick;
			}
		}

		readonly BeaconTrackerInfo info;
		readonly List<Entry> entries = new();

		public BeaconTracker(Actor self, BeaconTrackerInfo info)
		{
			this.info = info;
		}

		public void Record(OpenRA.Player owner, WPos position, int tick)
		{
			entries.Add(new Entry(owner, position, tick));
		}

		public IReadOnlyList<Entry> Entries => entries;

		void ITick.Tick(Actor self)
		{
			var cutoff = self.World.WorldTick - info.MemoryTicks;
			entries.RemoveAll(e => e.Tick < cutoff);
		}
	}
}
