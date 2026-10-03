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

using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Mods.Cameo.Widgets.Logic;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public sealed class CombatEffectivenessStatisticsTest
	{
		[Test]
		public void InitialSampleRecordsExistingAccountingDifference()
		{
			var stats = new CombatEffectivenessStatistics();
			stats.Sample(100, 400);
			Assert.That(stats.Samples, Is.EqualTo(new[] { -300 }));
		}

		[TestCase(40, 750)]
		[TestCase(20, 1500)]
		[TestCase(35, 858)]
		public void SamplesAtFirstTickReachingThirtySeconds(int timestep, int interval)
		{
			var stats = new CombatEffectivenessStatistics();
			stats.Sample(0, 0);
			for (var i = 1; i < interval; i++)
				stats.TickSamples(timestep, 1000, 1500);

			Assert.That(stats.Samples, Is.EqualTo(new[] { 0 }));
			stats.TickSamples(timestep, 1000, 1500);
			Assert.That(stats.Samples, Is.EqualTo(new[] { 0, -500 }));
			for (var i = 0; i < interval; i++)
				stats.TickSamples(timestep, 3000, 1500);

			Assert.That(stats.Samples, Is.EqualTo(new[] { 0, -500, 1500 }));
		}

		[Test]
		public void FlatAndZeroLedgersNeverStopSampling()
		{
			// Defeated players' underlying ledger can stop changing. The history must
			// keep sampling it, including a zero result after an even exchange.
			var stats = new CombatEffectivenessStatistics();
			stats.Sample(0, 0);
			for (var i = 0; i < 1500; i++)
				stats.TickSamples(40, 500, 500);
			for (var i = 0; i < 1500; i++)
				stats.TickSamples(40, 500, 1000);

			Assert.That(stats.Samples, Is.EqualTo(new[] { 0, 0, 0, -500, -500 }));
		}

		[Test]
		public void GraphPanelIndicesMatchObserverDropdownOrder()
		{
			// The observer's hotkey dispatcher and dropdown share these indices.
			Assert.That((int)CameoObserverStatsPanel.ArmyGraph, Is.EqualTo(14));
			Assert.That((int)CameoObserverStatsPanel.CombatEffectivenessGraph, Is.EqualTo(15));
			Assert.That((int)CameoObserverStatsPanel.TeamArmyGraph, Is.EqualTo(16));
			Assert.That((int)CameoObserverStatsPanel.TeamEarningsGraph, Is.EqualTo(17));
		}
	}
}
