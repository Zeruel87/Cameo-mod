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
using System.Text;
using System.Text.Json;
using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public sealed class AiMatchLogWriterTest
	{
		[TestCase(false, false, true, true)]
		[TestCase(true, false, true, false)]
		[TestCase(false, true, true, false)]
		[TestCase(false, false, false, false)]
		public void EligibilityExcludesReplaySaveAndNonHost(bool replay, bool save, bool host, bool expected)
		{
			Assert.That(AiMatchLogWriter.Eligible(WorldType.Regular, replay, save, host), Is.EqualTo(expected));
			Assert.That(AiMatchLogWriter.Eligible(WorldType.Shellmap, replay, save, host), Is.False);
			Assert.That(AiMatchLogWriter.Eligible(WorldType.Editor, replay, save, host), Is.False);
		}

		// The match log is JSON Lines assembled by hand with a StringBuilder, so a single missing
		// separator makes every line unparseable — and the aggregator can only report it as a skip.
		// The shipped emitter had exactly that: AppendTimeline wrote no leading comma, so each line
		// came out as ..."personality_switches":0"personality_timeline":[]... The Python tests build
		// their fixtures with json.dumps and cannot see it. This mirrors BuildLog's call sequence.
		static string BuildPlayerLine(IReadOnlyList<AiMatchLogPersonalityTransition> timeline)
		{
			var b = new StringBuilder();
			AiMatchLogWriter.AppendObjectStart(b);
			AiMatchLogWriter.AppendNumber(b, "schema", 1, true);
			AiMatchLogWriter.AppendString(b, "record_id", "game|Multi0");
			AiMatchLogWriter.AppendNumber(b, "duration_ticks", 2400);

			AiMatchLogWriter.AppendObjectPropertyStart(b, "player");
			AiMatchLogWriter.AppendString(b, "name", "Multi0", true);
			AiMatchLogWriter.AppendString(b, "personality", "rush");
			AiMatchLogWriter.AppendNumber(b, "personality_switches", 2);
			AiMatchLogWriter.AppendTimeline(b, timeline);
			b.Append('}');

			AiMatchLogWriter.AppendObjectPropertyStart(b, "stats");
			AiMatchLogWriter.AppendNumber(b, "kills_cost", 100, true);
			b.Append('}');
			b.Append('}');
			return b.ToString();
		}

		[Test]
		public void EmptyTimelineStillProducesParseableJson()
		{
			var json = BuildPlayerLine(null);
			using var doc = JsonDocument.Parse(json);
			var player = doc.RootElement.GetProperty("player");
			Assert.That(player.GetProperty("personality_switches").GetInt32(), Is.EqualTo(2));
			Assert.That(player.GetProperty("personality_timeline").GetArrayLength(), Is.EqualTo(0));
		}

		[Test]
		public void PopulatedTimelineRoundTrips()
		{
			var timeline = new List<AiMatchLogPersonalityTransition>
			{
				new(0, "rush"),
				new(1500, "tech")
			};

			using var doc = JsonDocument.Parse(BuildPlayerLine(timeline));
			var entries = doc.RootElement.GetProperty("player").GetProperty("personality_timeline");
			Assert.That(entries.GetArrayLength(), Is.EqualTo(2));
			Assert.That(entries[1].GetProperty("tick").GetInt32(), Is.EqualTo(1500));
			Assert.That(entries[1].GetProperty("personality").GetString(), Is.EqualTo("tech"));
		}

		[Test]
		public void ControlCharactersAndQuotesAreEscaped()
		{
			var b = new StringBuilder();
			AiMatchLogWriter.AppendObjectStart(b);
			AiMatchLogWriter.AppendString(b, "map_title", "a \"quoted\"	map\name", true);
			b.Append('}');

			using var doc = JsonDocument.Parse(b.ToString());
			Assert.That(doc.RootElement.GetProperty("map_title").GetString(),
				Is.EqualTo("a \"quoted\"	map\name"));
		}
	}
}
