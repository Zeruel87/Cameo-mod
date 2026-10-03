#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System.Collections.Generic;
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	// ENG / DESIGN §19.3: the merged engineer owner keeps an engineer until it is done, gone or stuck, and one owner
	// at a time holds it (AI_REVIEW_FRANSOTTO P0b, "IsIdle is not ownership").
	[TestFixture]
	public sealed class EngineerBotModuleTest
	{
		const int Grace = 50;
		const int Sample = 120;

		static EngineerCheck Check(bool gone = false, bool idle = false, bool moving = false, bool moved = true,
			int sinceOrder = 500, int sinceSample = 500)
		{
			return EngineerBotModule.Check(gone, idle, moving, moved, sinceOrder, sinceSample, Grace, Sample);
		}

		[Test]
		public void AGoneEngineerIsDroppedWhateverElseHolds()
		{
			Assert.That(Check(gone: true, idle: true, moving: true, moved: false), Is.EqualTo(EngineerCheck.Gone));
		}

		[Test]
		public void AnIdleEngineerInsideTheGraceIsStillOnItsWay()
		{
			// The order was queued, not issued: ModularBot hands out ceil(n / MinOrderQuotientPerTick) orders a tick.
			Assert.That(Check(idle: true, sinceOrder: Grace - 1), Is.EqualTo(EngineerCheck.Working));
			Assert.That(Check(idle: true, sinceOrder: Grace), Is.EqualTo(EngineerCheck.Done));
		}

		[Test]
		public void MovingWithoutMovingForASampleIsStuck()
		{
			Assert.That(Check(moving: true, moved: false), Is.EqualTo(EngineerCheck.Stuck));
			Assert.That(Check(moving: true, moved: true), Is.EqualTo(EngineerCheck.Working));
		}

		[Test]
		public void NotStuckBeforeAWholeSampleOrInsideTheGrace()
		{
			Assert.That(Check(moving: true, moved: false, sinceSample: Sample - 1), Is.EqualTo(EngineerCheck.Working));
			Assert.That(Check(moving: true, moved: false, sinceOrder: Grace - 1), Is.EqualTo(EngineerCheck.Working));
		}

		[Test]
		public void StandingStillWhileNotMovingIsWorkNotStuck()
		{
			// e.g. repairing, or inside the capture's enter step: only a stalled MOVE counts.
			Assert.That(Check(moving: false, moved: false), Is.EqualTo(EngineerCheck.Working));
		}

		[Test]
		public void AnEngineerTheSquadsHoldIsRefusedToTheEngineerOwner()
		{
			var table = new BotLeaseTable<int>();
			Assert.That(table.TryClaim(7, "SquadManagerBotModuleCA", BotLeasePurpose.Squad, 0, 3000), Is.True);
			Assert.That(table.IsClaimedByOther(7, nameof(EngineerBotModule), 10), Is.True);
			Assert.That(table.TryClaim(7, nameof(EngineerBotModule), BotLeasePurpose.Capture, 10, 3000), Is.False);

			table.Release(7, "SquadManagerBotModuleCA");
			Assert.That(table.TryClaim(7, nameof(EngineerBotModule), BotLeasePurpose.Capture, 20, 3000), Is.True);
			Assert.That(table.LeaseOf(7, 20)?.Purpose, Is.EqualTo(BotLeasePurpose.Capture));
		}

		// ENG-T: the transport roll is the seam's own gate — stealth target only, chance > 0,
		// roll strictly below the percentage.
		[Test]
		public void TransportRollsOnlyForStealthTargetsWithAChance()
		{
			Assert.That(EngineerBotModule.WantsTransport(stealthTarget: false, 0, 25), Is.False);
			Assert.That(EngineerBotModule.WantsTransport(stealthTarget: true, 0, 0), Is.False);
			Assert.That(EngineerBotModule.WantsTransport(stealthTarget: true, 24, 25), Is.True);
			Assert.That(EngineerBotModule.WantsTransport(stealthTarget: true, 25, 25), Is.False);
			Assert.That(EngineerBotModule.WantsTransport(stealthTarget: true, 99, 100), Is.True);
		}

		[Test]
		public void GreedyRouteStartsAtStartAndAlwaysPicksTheNearestUnvisited()
		{
			// A row of cells: 0 ---- 5 ---- 20 ---- 21; from cell 5 the nearest-next walk is 0 -> 20 -> 21.
			var stops = new List<CPos> { new(0, 0), new(5, 0), new(20, 0), new(21, 0) };
			Assert.That(EngineerBotModule.GreedyRoute(stops, 1, 5), Is.EqualTo(new[] { 1, 0, 2, 3 }));

			// max caps the run length: the farthest two stops are cut off first.
			Assert.That(EngineerBotModule.GreedyRoute(stops, 1, 2), Is.EqualTo(new[] { 1, 0 }));

			// A single stop is a run of one.
			Assert.That(EngineerBotModule.GreedyRoute(new List<CPos> { new(9, 9) }, 0, 5), Is.EqualTo(new[] { 0 }));
		}

		// FB2 (switch T): safe capturable targets justify a specialist even with none alive;
		// the cap is a ceiling, not a target — zero safe targets always means zero demand.
		[Test]
		public void DemandScalesWithSafeTargetsAndCapsAtTheMaximum()
		{
			Assert.That(EngineerBotModule.DemandCapturersDesired(0, 3, 2), Is.EqualTo(0));
			Assert.That(EngineerBotModule.DemandCapturersDesired(1, 3, 2), Is.EqualTo(0));
			Assert.That(EngineerBotModule.DemandCapturersDesired(2, 3, 2), Is.EqualTo(1));
			Assert.That(EngineerBotModule.DemandCapturersDesired(5, 3, 2), Is.EqualTo(2));
			Assert.That(EngineerBotModule.DemandCapturersDesired(100, 3, 2), Is.EqualTo(3));
		}

		[Test]
		public void DemandIsDefensiveAgainstBadConfigAndNegativeCounts()
		{
			Assert.That(EngineerBotModule.DemandCapturersDesired(9, -2, 0), Is.EqualTo(0));
		}

		// The dormant shelf's threshold — shared by the death streak (CaptureFailuresBeforeDormant)
		// and the retreat streak (CaptureRetreatsBeforeDormant, the outmatched-only storm class the
		// 2v2 smoke exposed: consecutive voluntary retreats never reached the death shelf). 0 disables.
		[Test]
		public void DormantThresholdCountsStreaksAndZeroDisables()
		{
			Assert.That(EngineerBotModule.GoesDormant(0, 2), Is.False);
			Assert.That(EngineerBotModule.GoesDormant(1, 2), Is.False);
			Assert.That(EngineerBotModule.GoesDormant(2, 2), Is.True);
			Assert.That(EngineerBotModule.GoesDormant(5, 2), Is.True);
			Assert.That(EngineerBotModule.GoesDormant(10, 0), Is.False,
				"a zero threshold is the off switch — a retreat/death run never rests");
		}
	}
}
