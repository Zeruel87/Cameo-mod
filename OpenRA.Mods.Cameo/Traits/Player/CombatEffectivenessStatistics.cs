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
using OpenRA.Graphics;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Attach this to the player actor to record a low-resolution history of the combat value trade:",
		"enemy asset value destroyed minus own asset value lost.")]
	public class CombatEffectivenessStatisticsInfo : TraitInfo
	{
		public override object Create(ActorInitializer init) { return new CombatEffectivenessStatistics(); }
	}

	public class CombatEffectivenessStatistics : ITick, INotifyCreated, IWorldLoaded
	{
		// Matches the 30 second cadence of PlayerStatistics' army and income samples.
		const int SampleIntervalMs = 30000;

		public readonly List<int> Samples = new(100);

		PlayerStatistics stats;
		int ticks;

		void INotifyCreated.Created(Actor self) { stats = self.TraitOrDefault<PlayerStatistics>(); }

		void IWorldLoaded.WorldLoaded(World w, WorldRenderer wr) { Sample(); }

		void ITick.Tick(Actor self)
		{
			ticks++;
			if (ticks * self.World.Timestep < SampleIntervalMs)
				return;

			ticks = 0;
			Sample();
		}

		void Sample()
		{
			// Zero is a legitimate value here, so sampling must never disable itself.
			if (stats != null)
				Samples.Add(stats.KillsCost - stats.DeathsCost);
		}
	}
}
