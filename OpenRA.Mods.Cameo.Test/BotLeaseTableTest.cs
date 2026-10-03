#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System.Linq;
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	// LC1 (AI_REVIEW_FRANSOTTO P0): one unexpired lease per unit; IsIdle is not ownership.
	[TestFixture]
	public sealed class BotLeaseTableTest
	{
		[Test]
		public void ASecondOwnerIsRefusedWhileTheLeaseLives()
		{
			var t = new BotLeaseTable<int>();
			Assert.That(t.TryClaim(1, "capture", BotLeasePurpose.Capture, 100, 50), Is.True);
			Assert.That(t.TryClaim(1, "engineer", BotLeasePurpose.Engineer, 120, 50), Is.False);
			Assert.That(t.IsClaimedByOther(1, "engineer", 120), Is.True);
			Assert.That(t.IsClaimedByOther(1, "capture", 120), Is.False);
		}

		[Test]
		public void TheHolderRenewsAndKeepsItsAcquiredTick()
		{
			var t = new BotLeaseTable<int>();
			t.TryClaim(1, "scout", BotLeasePurpose.Scout, 100, 150);
			Assert.That(t.TryClaim(1, "scout", BotLeasePurpose.Scout, 200, 150), Is.True);
			var lease = t.LeaseOf(1, 200);
			Assert.That(lease?.AcquiredTick, Is.EqualTo(100));
			Assert.That(lease?.ExpiresTick, Is.EqualTo(350));
		}

		[Test]
		public void AnExpiredLeaseFreesTheUnit()
		{
			// The heartbeat model: a holder that stops renewing loses the unit without a release call.
			var t = new BotLeaseTable<int>();
			t.TryClaim(1, "scout", BotLeasePurpose.Scout, 100, 150);
			Assert.That(t.IsClaimedByOther(1, "crate", 249), Is.True);
			Assert.That(t.IsClaimedByOther(1, "crate", 250), Is.False);
			Assert.That(t.TryClaim(1, "crate", BotLeasePurpose.Crate, 250, 1500), Is.True);
			Assert.That(t.LeaseOf(1, 250)?.AcquiredTick, Is.EqualTo(250));
		}

		[Test]
		public void OnlyTheHolderCanRelease()
		{
			var t = new BotLeaseTable<int>();
			t.TryClaim(1, "capture", BotLeasePurpose.Capture, 0, 0);
			t.Release(1, "crate");
			Assert.That(t.IsClaimedByOther(1, "crate", 10_000_000), Is.True, "a zero duration lasts until released");
			t.Release(1, "capture");
			Assert.That(t.LeaseOf(1, 0), Is.Null);
		}

		[Test]
		public void TransferMovesTheLeaseToTheNewOwner()
		{
			// ENG-T: the run hands each passenger's lease to the transport provider for the ride,
			// so §19.6's order gate counts the rider orders as owned; the old owner is not told
			// (a negotiation, not an emergency) and simply finds the lease gone on its next renew.
			var t = new BotLeaseTable<int>();
			t.TryClaim(1, "engineer", BotLeasePurpose.Capture, 100, 50);
			t.Transfer(1, "transport", BotLeasePurpose.Mission, 120, 250);
			var lease = t.LeaseOf(1, 120);
			Assert.That(lease?.Owner, Is.EqualTo("transport"));
			Assert.That(lease?.Purpose, Is.EqualTo(BotLeasePurpose.Mission));
			Assert.That(lease?.AcquiredTick, Is.EqualTo(120));
			Assert.That(lease?.ExpiresTick, Is.EqualTo(370));
			Assert.That(t.TryClaim(1, "engineer", BotLeasePurpose.Capture, 130, 50), Is.False,
				"the old owner's renew is refused while the ride lease lives");
			Assert.That(t.TryClaim(1, "transport", BotLeasePurpose.Mission, 130, 250), Is.True,
				"the new owner heartbeats it");
		}

		[Test]
		public void TransferClaimsAnUnheldUnit()
		{
			var t = new BotLeaseTable<int>();
			t.Transfer(1, "transport", BotLeasePurpose.Mission, 100, 100);
			Assert.That(t.LeaseOf(1, 100)?.Owner, Is.EqualTo("transport"));
		}

		[Test]
		public void PruneDropsExpiredAndGoneUnitsSeparately()
		{
			var t = new BotLeaseTable<int>();
			t.TryClaim(1, "a", BotLeasePurpose.Scout, 0, 10);
			t.TryClaim(2, "a", BotLeasePurpose.Scout, 0, 1000);
			t.TryClaim(3, "a", BotLeasePurpose.Scout, 0, 1000);
			var (expired, gone) = t.Prune(100, key => key == 3);
			Assert.That((expired, gone), Is.EqualTo((1, 1)));
			Assert.That(t.ActiveLeases(100).Select(l => l.Key), Is.EqualTo(new[] { 2 }));
		}
	}
}
