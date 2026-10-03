#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	// LC2 (AI_REVIEW_FRANSOTTO P1b): a crate reservation is released instead of lasting forever.
	[TestFixture]
	public sealed class CratePickupBotModuleTest
	{
		static bool Stale(bool crateGone = false, bool collectorGone = false, bool idle = false, int age = 10,
			int grace = 100, int timeout = 1500)
		{
			return CratePickupBotModule.ReservationStale(crateGone, collectorGone, idle, age, grace, timeout);
		}

		[Test]
		public void ALiveBusyCollectorKeepsItsCrate() => Assert.That(Stale(age: 1000), Is.False);

		[Test]
		public void AGoneCrateOrCollectorReleases()
		{
			Assert.That(Stale(crateGone: true), Is.True);
			Assert.That(Stale(collectorGone: true), Is.True);
		}

		[Test]
		public void ACollectorIdlePastTheGraceReleases()
		{
			// Order latency: the collector is still idle right after the order, so the grace protects it.
			Assert.That(Stale(idle: true, age: 50), Is.False);
			Assert.That(Stale(idle: true, age: 101), Is.True);
		}

		[Test]
		public void TheTimeoutReleasesAndMinusOneKeepsTheOldBehaviour()
		{
			Assert.That(Stale(age: 1501), Is.True);
			Assert.That(Stale(age: 100000, timeout: -1), Is.False);
		}
	}
}
