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
using System.Linq;
using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class BotOwnershipLedgerTest
	{
		static readonly HashSet<string> NoneGone = new();

		static List<BotOwnershipViolation> Kinds(IEnumerable<(BotOwnershipViolation Kind, string Key, string Detail)> found) =>
			found.Select(f => f.Kind).ToList();

		[Test]
		public void ConsistentHoldingsReportNothing()
		{
			var l = new BotOwnershipLedger<string>();
			l.Begin();
			l.Squad("tank", "rush/Assault#0", true);
			l.Lease("tank", l.SquadLeaseOwner);
			l.Lease("eng", "EngineerBotModule");
			l.Pool("rifle");
			var found = l.Evaluate(100, NoneGone.Contains, new[] { "tank", "eng", "rifle" }, 400, 750);
			Assert.That(found, Is.Empty);
		}

		[Test]
		public void SquadMemberLeasedByAnotherModuleIsDoubleOwner()
		{
			var l = new BotOwnershipLedger<string>();
			l.Begin();
			l.Squad("tank", "rush/Assault#0", true);
			l.Lease("tank", "ScoutBotModule");
			var found = l.Evaluate(100, NoneGone.Contains, new[] { "tank" }, 400, 750);
			Assert.That(Kinds(found), Is.EqualTo(new[] { BotOwnershipViolation.DoubleOwner }));
			Assert.That(found[0].Detail, Does.Contain("ScoutBotModule"));
		}

		[Test]
		public void TwoSquadsAndDisabledHoldersAreReported()
		{
			var l = new BotOwnershipLedger<string>();
			l.Begin();
			l.Squad("tank", "rush/Assault#0", true);
			l.Squad("tank", "rush/Protection#1", true);
			l.Squad("apc", "turtle/Assault#0", false);
			var found = l.Evaluate(100, NoneGone.Contains, new[] { "tank", "apc" }, 400, 750);
			Assert.That(Kinds(found), Is.EquivalentTo(new[] { BotOwnershipViolation.TwoSquads, BotOwnershipViolation.HeldByDisabled }));
		}

		[Test]
		public void DeadHeldWaitsForTheGraceWindow()
		{
			var l = new BotOwnershipLedger<string>();
			var gone = new HashSet<string> { "wreck" };
			for (var tick = 0; tick <= 400; tick += 100)
			{
				l.Begin();
				l.Lease("wreck", "CratePickupBotModule");
				Assert.That(l.Evaluate(tick, gone.Contains, new string[0], 400, 750), Is.Empty, $"tick {tick}");
			}

			l.Begin();
			l.Lease("wreck", "CratePickupBotModule");
			var found = l.Evaluate(500, gone.Contains, new string[0], 400, 750);
			Assert.That(Kinds(found), Is.EqualTo(new[] { BotOwnershipViolation.DeadHeld }));
		}

		[Test]
		public void AReleasedUnitThatNeverReachesThePoolBecomesAnOrphanOnce()
		{
			var l = new BotOwnershipLedger<string>();
			l.Begin();
			l.Lease("tank", "BeaconResponderBotModule");
			Assert.That(l.Evaluate(0, NoneGone.Contains, new[] { "tank" }, 400, 750), Is.Empty);

			// Released at tick 100 and never re-adopted.
			var found = new List<(BotOwnershipViolation, string, string)>();
			for (var tick = 100; tick <= 1000; tick += 100)
			{
				l.Begin();
				found.AddRange(l.Evaluate(tick, NoneGone.Contains, new[] { "tank" }, 400, 750));
			}

			Assert.That(found.Select(f => f.Item1), Is.EqualTo(new[] { BotOwnershipViolation.Orphan }), "reported once, not every pass");
			Assert.That(l.Counts[BotOwnershipViolation.Orphan], Is.EqualTo(1));
		}

		[Test]
		public void ReachingThePoolInsideTheGraceWindowResetsTheOrphanClock()
		{
			var l = new BotOwnershipLedger<string>();
			for (var tick = 0; tick <= 2000; tick += 100)
			{
				l.Begin();

				// In the pool on every fourth pass: never unowned for longer than 300 ticks.
				if (tick % 400 == 0)
					l.Pool("tank");

				Assert.That(l.Evaluate(tick, NoneGone.Contains, new[] { "tank" }, 400, 750), Is.Empty, $"tick {tick}");
			}
		}
	}
}
