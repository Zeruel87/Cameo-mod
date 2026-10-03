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
		"Recorded asset value destroyed minus recorded asset value lost (PlayerStatistics accounting).")]
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

		void IWorldLoaded.WorldLoaded(World w, WorldRenderer wr)
		{
			if (stats != null)
				Sample(stats.KillsCost, stats.DeathsCost);
		}

		void ITick.Tick(Actor self)
		{
			if (stats != null)
				TickSamples(self.World.Timestep, stats.KillsCost, stats.DeathsCost);
		}

		internal void TickSamples(int timestep, int killsCost, int deathsCost)
		{
			ticks++;
			if (ticks * timestep < SampleIntervalMs)
				return;

			ticks = 0;
			Sample(killsCost, deathsCost);
		}

		internal void Sample(int killsCost, int deathsCost)
		{
			// Zero is a legitimate value here, so sampling must never disable itself.
			Samples.Add(killsCost - deathsCost);
		}
	}
}
