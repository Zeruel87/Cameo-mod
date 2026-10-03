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

using System.Linq;
using System.Reflection;
using NUnit.Framework;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class PlaceBeaconShadowTest
	{
		[Test]
		public void ShadowCarriesEveryUpstreamField()
		{
			// The engine DROPS unknown yaml fields silently (CLAUDE.md rule 8b): if the
			// shadow lacks a field upstream declares, any yaml using it would vanish.
			var upstream = typeof(OpenRA.Mods.Common.Traits.PlaceBeaconInfo)
				.GetFields(BindingFlags.Public | BindingFlags.Instance)
				.Select(f => f.Name)
				.ToHashSet();
			var shadow = typeof(Traits.PlaceBeaconInfo)
				.GetFields(BindingFlags.Public | BindingFlags.Instance)
				.Select(f => f.Name)
				.ToHashSet();

			Assert.That(shadow.IsSupersetOf(upstream), Is.True,
				"shadow is missing upstream fields: " + string.Join(", ", upstream.Except(shadow)));
		}

		[Test]
		public void ShadowHasCameoOnlyMarker()
		{
			// Rule-7 proof field: exists only on the Cameo type.
			Assert.That(typeof(Traits.PlaceBeaconInfo).GetField("TrackForBots"), Is.Not.Null);
			Assert.That(typeof(OpenRA.Mods.Common.Traits.PlaceBeaconInfo).GetField("TrackForBots"), Is.Null);
		}

		[Test]
		public void BeaconTrackerRecordsEntries()
		{
			var tracker = new Traits.BeaconTracker(null, new Traits.BeaconTrackerInfo());
			tracker.Record(null, new WPos(1024, 2048, 0), 42);

			Assert.That(tracker.Entries.Count, Is.EqualTo(1));
			Assert.That(tracker.Entries[0].Tick, Is.EqualTo(42));
			Assert.That(tracker.Entries[0].Position, Is.EqualTo(new WPos(1024, 2048, 0)));
		}
	}
}
