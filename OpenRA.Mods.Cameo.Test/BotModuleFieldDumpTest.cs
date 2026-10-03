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

using System.Collections.Frozen;
using System.Collections.Generic;
using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class BotModuleFieldDumpTest
	{
		[Test]
		public void SetsAreSortedSoTwoBootsOfTheSameRulesDumpTheSameText()
		{
			// Insertion order differs; .NET's per-process string hashing makes iteration order differ too.
			Assert.That(BotModuleFieldDump.Format(new HashSet<string> { "zerg_zergling", "atreides_trike", "e1" }),
				Is.EqualTo("[atreides_trike, e1, zerg_zergling]"));
			Assert.That(BotModuleFieldDump.Format(new[] { "b", "a" }.ToFrozenSet()), Is.EqualTo("[a, b]"));
		}

		[Test]
		public void ListsKeepTheirOrder()
		{
			Assert.That(BotModuleFieldDump.Format(new[] { "b", "a" }), Is.EqualTo("(b, a)"));
			Assert.That(BotModuleFieldDump.Format(new List<int> { 3, 1, 2 }), Is.EqualTo("(3, 1, 2)"));
		}

		[Test]
		public void DictionariesAreSortedByEntryAndFormatTheirValues()
		{
			var rows = new Dictionary<string, int> { ["refinery"] = 15, ["barracks"] = 10 };
			Assert.That(BotModuleFieldDump.Format(rows), Is.EqualTo("{barracks: 10; refinery: 15}"));
			Assert.That(BotModuleFieldDump.Format(rows.ToFrozenDictionary()), Is.EqualTo("{barracks: 10; refinery: 15}"));

			var targets = new Dictionary<string, string[]> { ["guerrilla"] = ["Squad@rush.GuerrillaTypes", "Squad@tech.GuerrillaTypes"] };
			Assert.That(BotModuleFieldDump.Format(targets), Is.EqualTo("{guerrilla: (Squad@rush.GuerrillaTypes, Squad@tech.GuerrillaTypes)}"));
		}

		[Test]
		public void NullAndScalarsFormatPlainly()
		{
			Assert.That(BotModuleFieldDump.Format(null), Is.EqualTo(""));
			Assert.That(BotModuleFieldDump.Format("hard"), Is.EqualTo("hard"));
			Assert.That(BotModuleFieldDump.Format(250), Is.EqualTo("250"));
			Assert.That(BotModuleFieldDump.Format(true), Is.EqualTo("True"));
		}
	}
}
