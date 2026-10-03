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
using System.Text;
using System.Text.Json;
using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class BotArsenalLedgerTest
	{
		static BotArsenalLedger Sample()
		{
			var ledger = new BotArsenalLedger();
			ledger.RecordCreated("tank");
			ledger.RecordCreated("tank");
			ledger.RecordCreated("rifle");
			ledger.RecordLost("tank", 800);
			ledger.RecordKill("tank", "rifle", 100);
			ledger.RecordKill("tank", "rifle", 100);
			ledger.RecordKill("tank", "apc", 600);
			ledger.RecordKill("rifle", "rifle", 100);
			return ledger;
		}

		[Test]
		public void BooksCreationLossAndKillsByVictim()
		{
			var tank = Sample().ByType["tank"];
			Assert.That(tank.Created, Is.EqualTo(2));
			Assert.That(tank.Lost, Is.EqualTo(1));
			Assert.That(tank.LostValue, Is.EqualTo(800));
			Assert.That(tank.KilledValue, Is.EqualTo(800));
			Assert.That(tank.KilledValueByVictim["rifle"], Is.EqualTo(200));
			Assert.That(tank.KilledValueByVictim["apc"], Is.EqualTo(600));
		}

		[Test]
		public void OrderedPutsTheBiggestKillerFirst()
		{
			Assert.That(Sample().Ordered().Select(kv => kv.Key), Is.EqualTo(new[] { "tank", "rifle" }));
		}

		[TestCase(true)]
		[TestCase(false)]
		public void ArsenalRoundTripsAsJson(bool empty)
		{
			var b = new StringBuilder("{");
			AiMatchLogWriter.AppendArsenal(b, empty ? new BotArsenalLedger() : Sample(), true);
			b.Append('}');

			using var doc = JsonDocument.Parse(b.ToString());
			var arsenal = doc.RootElement.GetProperty("arsenal");
			Assert.That(arsenal.GetArrayLength(), Is.EqualTo(empty ? 0 : 2));
			if (!empty)
			{
				Assert.That(arsenal[0].GetProperty("type").GetString(), Is.EqualTo("tank"));
				Assert.That(arsenal[0].GetProperty("killed_by_victim").GetProperty("apc").GetInt32(), Is.EqualTo(600));
				Assert.That(arsenal[1].GetProperty("lost").GetInt32(), Is.Zero);
			}
		}
	}
}
