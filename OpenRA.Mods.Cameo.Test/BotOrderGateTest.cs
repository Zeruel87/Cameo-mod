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
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class BotOrderGateTest
	{
		static readonly HashSet<string> Emergency = ["SquadManagerBotModuleCA"];

		[Test]
		public void UnclaimedUnitsAndTheHoldersOwnOrdersPass()
		{
			Assert.That(BotOrderGate<int>.Decide("SquadManagerBotModuleCA", null, true, false, Emergency), Is.EqualTo(BotOrderVerdict.Allow));
			Assert.That(BotOrderGate<int>.Decide("CratePickupBotModule", "CratePickupBotModule", true, false, Emergency), Is.EqualTo(BotOrderVerdict.Allow));
			Assert.That(BotOrderGate<int>.Decide(null, "CratePickupBotModule", true, false, Emergency), Is.EqualTo(BotOrderVerdict.Allow),
				"an order queued outside a module call is never refused");
		}

		[Test]
		public void WatchModeCountsEnforceModeRefuses()
		{
			Assert.That(BotOrderGate<int>.Decide("SquadManagerBotModuleCA", "CratePickupBotModule", false, false, Emergency), Is.EqualTo(BotOrderVerdict.Conflict));
			Assert.That(BotOrderGate<int>.Decide("SquadManagerBotModuleCA", "CratePickupBotModule", true, false, Emergency), Is.EqualTo(BotOrderVerdict.Refuse));
		}

		[Test]
		public void OnlyAListedModuleInAnEmergencyTakesTheUnitOver()
		{
			Assert.That(BotOrderGate<int>.Decide("SquadManagerBotModuleCA", "CratePickupBotModule", true, true, Emergency), Is.EqualTo(BotOrderVerdict.Preempt));
			Assert.That(BotOrderGate<int>.Decide("ScoutBotModule", "CratePickupBotModule", true, true, Emergency), Is.EqualTo(BotOrderVerdict.Refuse),
				"not on the emergency list");
			Assert.That(BotOrderGate<int>.Decide("SquadManagerBotModuleCA", "CratePickupBotModule", false, true, Emergency), Is.EqualTo(BotOrderVerdict.Conflict),
				"watch mode never preempts");
		}

		[Test]
		public void JudgeCountsAndFlagsTheFirstOfEachPair()
		{
			var gate = new BotOrderGate<int>();
			Assert.That(gate.Judge("SquadManagerBotModuleCA", "CratePickupBotModule", true, false, Emergency), Is.EqualTo((BotOrderVerdict.Refuse, true)));
			Assert.That(gate.Judge("SquadManagerBotModuleCA", "CratePickupBotModule", true, false, Emergency), Is.EqualTo((BotOrderVerdict.Refuse, false)));
			Assert.That(gate.Judge("SquadManagerBotModuleCA", null, true, false, Emergency).Verdict, Is.EqualTo(BotOrderVerdict.Allow));
			gate.Judge(null, null, true, false, Emergency);
			Assert.That(gate.Refused, Is.EqualTo(2));
			Assert.That(gate.Unattributed, Is.EqualTo(1));
			Assert.That(gate.Pairs[("SquadManagerBotModuleCA", "CratePickupBotModule", BotOrderVerdict.Refuse)], Is.EqualTo(2));
		}

		[Test]
		public void TwoModulesOrderingOneUnitInsideTheWindowIsACrossedOrder()
		{
			var gate = new BotOrderGate<int>();
			Assert.That(gate.NoteIssued(7, "SquadManagerBotModuleCA", 100, 100, null), Is.Null);
			Assert.That(gate.NoteIssued(7, "SquadManagerBotModuleCA", 150, 100, null), Is.Null, "same module again is not crossed");
			Assert.That(gate.NoteIssued(7, "CratePickupBotModule", 200, 100, null), Is.EqualTo("SquadManagerBotModuleCA"));
			Assert.That(gate.NoteIssued(7, "SquadManagerBotModuleCA", 400, 100, null), Is.Null, "outside the window");
			Assert.That(gate.Crossed, Is.EqualTo(1));
			Assert.That(gate.CrossedPairs[("SquadManagerBotModuleCA", "CratePickupBotModule")], Is.EqualTo(1));
		}

		[Test]
		public void AReleasedClaimReadsAsAHandOffNotACross()
		{
			// EMBER's round-trip finding: a unit returning to the idle pool after squad
			// dissolution read as SquadManager->ScoutBotModule crossed — the earlier
			// issuer's lease had already ended, so the later order is the new owner.
			var gate = new BotOrderGate<int>();
			Assert.That(gate.NoteIssued(7, "SquadManagerBotModuleCA", 100, 100, "SquadManagerBotModuleCA"), Is.Null);
			Assert.That(gate.NoteIssued(7, "ScoutBotModule", 150, 100, null), Is.Null, "the squad released the unit — a clean hand-off");
			Assert.That(gate.Crossed, Is.EqualTo(0));

			var gate2 = new BotOrderGate<int>();
			Assert.That(gate2.NoteIssued(7, "SquadManagerBotModuleCA", 100, 100, "SquadManagerBotModuleCA"), Is.Null);
			Assert.That(gate2.NoteIssued(7, "ScoutBotModule", 150, 100, "ScoutBotModule"), Is.Null, "the new holder claimed it");
			Assert.That(gate2.Crossed, Is.EqualTo(0));
		}

		[Test]
		public void OrderingAUnitTheEarlierIssuerStillHoldsIsACross()
		{
			var gate = new BotOrderGate<int>();
			Assert.That(gate.NoteIssued(7, "SquadManagerBotModuleCA", 100, 100, "SquadManagerBotModuleCA"), Is.Null);
			Assert.That(gate.NoteIssued(7, "ScoutBotModule", 150, 100, "SquadManagerBotModuleCA"), Is.EqualTo("SquadManagerBotModuleCA"),
				"the squad still holds the lease — two owners in fact");
			Assert.That(gate.Crossed, Is.EqualTo(1));
		}

		[Test]
		public void APreemptTakesTheLeaseAndNamesThePreviousHolder()
		{
			var table = new BotLeaseTable<int>();
			Assert.That(table.TryClaim(1, "CratePickupBotModule", BotLeasePurpose.Crate, 0, 1000), Is.True);
			Assert.That(table.Preempt(1, "SquadManagerBotModuleCA", BotLeasePurpose.Emergency, 10, 500), Is.EqualTo("CratePickupBotModule"));
			Assert.That(table.LeaseOf(1, 20)?.Owner, Is.EqualTo("SquadManagerBotModuleCA"));
			Assert.That(table.TryClaim(1, "CratePickupBotModule", BotLeasePurpose.Crate, 30, 1000), Is.False, "the old holder's heartbeat is denied");
			Assert.That(table.LeaseOf(1, 600), Is.Null, "the emergency lease expires");
			Assert.That(table.Preempt(2, "SquadManagerBotModuleCA", BotLeasePurpose.Emergency, 0, 500), Is.Null, "nobody held it");
		}
	}
}
