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
using OpenRA.Mods.CA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	// UF-1 "army first" (UnitBuilderBotModuleCAInfo.UnitsFirstFillAllQueues): an armed pass fills
	// every idle factory of each queue category in turn while cash holds above the (lead-scaled)
	// ProductionMinCashRequirement floor — MaximiseProductionCash no longer throttles the fill.
	// These cover the pure seams: the continue-decision and the per-pass issue cap. The queue-side
	// predicate (IssuableThisPass) needs a live ProductionQueue and stays untested here; what must
	// hold is that a marked/empty queue reads as not issuable so the fill never re-issues to the
	// same factory inside one BotTick (orders resolve only after BotTick — see ModularBot.Tick).
	[TestFixture]
	public class UnitsFirstProductionTest
	{
		[Test]
		public void SwitchDefaultsOffSoClassicStaysUntouched()
		{
			Assert.That(new UnitBuilderBotModuleCAInfo().UnitsFirstFillAllQueues, Is.False,
				"the flag is an increment switch: classic keeps the one-factory-per-category cadence");
		}

		[Test]
		public void FillContinuesWhileBudgetFloorAndQueueAllHold()
		{
			Assert.That(UnitBuilderBotModuleCA.UnitsFirstContinueFill(3, 5000, 2000, true), Is.True);
		}

		[Test]
		public void MinCashFloorIsInclusive()
		{
			// Same floor semantics as the pass-entry gate: only BELOW the requirement stops work —
			// at exactly the floor the army still soaks the cash.
			Assert.That(UnitBuilderBotModuleCA.UnitsFirstContinueFill(3, 2000, 2000, true), Is.True);
			Assert.That(UnitBuilderBotModuleCA.UnitsFirstContinueFill(3, 1999, 2000, true), Is.False,
				"one below the min-cash floor the fill stops — the reserve is a hard boundary");
		}

		[Test]
		public void ExhaustedBudgetStopsTheFillEvenWithCashAndQueues()
		{
			Assert.That(UnitBuilderBotModuleCA.UnitsFirstContinueFill(0, 999999, 2000, true), Is.False,
				"the per-pass cap is a hard bound — a stuck queue must not spin the tick");
		}

		[Test]
		public void NoIssuableQueueStopsTheFill()
		{
			Assert.That(UnitBuilderBotModuleCA.UnitsFirstContinueFill(3, 999999, 2000, false), Is.False,
				"every factory of the category busy or already issued this pass -> move on");
		}

		[Test]
		public void IssueCapIsFourPerConfiguredQueue()
		{
			Assert.That(UnitBuilderBotModuleCA.UnitsFirstFillIssueCap(8), Is.EqualTo(32),
				"default UnitQueues has 8 categories -> at most 32 issues per pass");
			Assert.That(UnitBuilderBotModuleCA.UnitsFirstFillIssueCap(1), Is.EqualTo(4));
			Assert.That(UnitBuilderBotModuleCA.UnitsFirstFillIssueCap(0), Is.EqualTo(0),
				"a bot with no unit queues never fills");
		}
	}
}
