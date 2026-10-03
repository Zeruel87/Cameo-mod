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
using OpenRA.Mods.CA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class BotTargetTagsTest
	{
		static List<(string Name, HashSet<string> Tags)> Candidates() =>
		[
			("rifle", ["infantry"]),
			("arty", ["artillery"]),
			("tank", ["vehicle"]),
			("harv", ["harvester"]),
		];

		static HashSet<string> TagsOf((string Name, HashSet<string> Tags) c) => c.Tags;

		[Test]
		public void TaggedCandidatesMoveToTheFront()
		{
			var picked = BotTargetTags.PreferTagged(Candidates(), new HashSet<string> { "artillery" }, TagsOf);
			Assert.That(picked[0].Name, Is.EqualTo("arty"));
			Assert.That(picked.Select(c => c.Name), Is.EquivalentTo(Candidates().Select(c => c.Name)));
		}

		[Test]
		public void MultipleMatchesKeepOriginalOrderAmongThemselves()
		{
			var picked = BotTargetTags.PreferTagged(Candidates(), new HashSet<string> { "artillery", "harvester" }, TagsOf);
			Assert.That(picked[0].Name, Is.EqualTo("arty"));
			Assert.That(picked[1].Name, Is.EqualTo("harv"));
		}

		[Test]
		public void NoMatchReturnsInputOrder()
		{
			var input = Candidates();
			var picked = BotTargetTags.PreferTagged(input, new HashSet<string> { "superweapon" }, TagsOf);
			Assert.That(picked.Select(c => c.Name), Is.EqualTo(input.Select(c => c.Name)));
		}

		[Test]
		public void EmptyPriorityTagsReturnsInput()
		{
			var input = Candidates();
			var picked = BotTargetTags.PreferTagged(input, new HashSet<string>(), TagsOf);
			Assert.That(picked, Is.SameAs(input));
		}

		[Test]
		public void NullTagsOnCandidatesNeverMatch()
		{
			var input = new List<(string, HashSet<string>)> { ("a", null), ("b", ["artillery"]) };
			var picked = BotTargetTags.PreferTagged(input, new HashSet<string> { "artillery" }, TagsOf);
			Assert.That(picked[0].Item1, Is.EqualTo("b"));
		}
	}
}
