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
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class AdaptiveCounterProductionTest
	{
		[Test]
		public void WeightZeroNeverPicksACounter()
		{
			Assert.That(AdaptiveCounterProduction.CounterPickAllowed(0, 100, 0), Is.False);
		}

		[Test]
		public void CountersWaitForTwoOrdinaryPicks()
		{
			Assert.That(AdaptiveCounterProduction.CounterPickAllowed(0, 1, 40), Is.False);
			Assert.That(AdaptiveCounterProduction.CounterPickAllowed(0, 2, 40), Is.True);
		}

		[Test]
		public void CounterShareStaysAtOrBelowTheWeight()
		{
			// Simulate 1000 picks where a counter is taken whenever allowed: the share converges on the weight.
			foreach (var weight in new[] { 4, 18, 40 })
			{
				int adaptive = 0, total = 0;
				for (var i = 0; i < 1000; i++)
				{
					if (AdaptiveCounterProduction.CounterPickAllowed(adaptive, total, weight))
						adaptive++;
					total++;
				}

				Assert.That(adaptive * 100, Is.LessThanOrEqualTo(total * weight + 100), $"weight {weight}");
				Assert.That(adaptive * 100, Is.GreaterThanOrEqualTo(total * weight - 200), $"weight {weight}");
			}
		}

		[Test]
		public void SmoothingMovesAQuarterAndForgetsZeroes()
		{
			var memory = new Dictionary<string, int> { { "tank", 4000 }, { "rifle", 1 } };
			AdaptiveCounterProduction.Smooth(memory, new Dictionary<string, int> { { "tank", 0 }, { "plane", 800 } });

			Assert.That(memory["tank"], Is.EqualTo(3000));
			Assert.That(memory["plane"], Is.EqualTo(200));
			Assert.That(memory.ContainsKey("rifle"), Is.False, "(1 * 3 + 0) / 4 = 0 drops out");
		}
	}
}
