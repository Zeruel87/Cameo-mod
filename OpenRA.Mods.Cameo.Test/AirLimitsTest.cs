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
	// CA F2p2 (71754fc06): air limit arithmetic and the fog-honest enemy air threat estimate.
	[TestFixture]
	public class AirLimitsTest
	{
		static int Cost(string type) => type == "mig" ? 1000 : type == "free" ? 0 : 500;

		[Test]
		public void ThreatCountIsDerivedFromObservedValueAndCost()
		{
			var seen = new Dictionary<string, int> { ["mig"] = 2500, ["tank"] = 9000, ["yak"] = 500 };
			var n = AirLimits.EstimateObservedThreatCount(seen, new[] { "mig", "yak", "hind" }, Cost);
			Assert.That(n, Is.EqualTo(3 + 1)); // ceil(2500/1000) + ceil(500/500); hind unseen; tank is not a threat type
		}

		[Test]
		public void UnknownCostCountsTypeOnceAndNothingSeenIsZero()
		{
			Assert.That(AirLimits.EstimateObservedThreatCount(new Dictionary<string, int> { ["free"] = 4000 }, new[] { "free" }, Cost), Is.EqualTo(1));
			Assert.That(AirLimits.EstimateObservedThreatCount(new Dictionary<string, int>(), new[] { "mig" }, Cost), Is.EqualTo(0));
			Assert.That(AirLimits.EstimateObservedThreatCount(null, new[] { "mig" }, Cost), Is.EqualTo(0));
		}

		[Test]
		public void SuperiorityLimitLegacyAndQueuedForms()
		{
			// Legacy: friendly air-to-air lowers the limit, floor is the base limit.
			Assert.That(AirLimits.AirSuperiorityLimit(4, 10, 3, false, 0), Is.EqualTo(8));
			Assert.That(AirLimits.AirSuperiorityLimit(4, 2, 3, false, 0), Is.EqualTo(4));
			// F2p2: friendly are part of the current count, so the limit is enemy + 1.
			Assert.That(AirLimits.AirSuperiorityLimit(4, 10, 3, true, 0), Is.EqualTo(11));
			// MaxAirSuperiority caps either form.
			Assert.That(AirLimits.AirSuperiorityLimit(4, 10, 3, true, 6), Is.EqualTo(6));
		}
	}
}
