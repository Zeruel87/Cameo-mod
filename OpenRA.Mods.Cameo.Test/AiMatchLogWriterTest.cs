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
using OpenRA.Mods.Cameo.Traits.BotModules;

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
		static string BuildPlayerLine(IReadOnlyList<AiMatchLogPersonalityTransition> timeline,
			IReadOnlyList<AiMatchLogCompositionTransition> compositions = null,
			IReadOnlyList<AiMatchLogEpisodeTransition> episodes = null)
		{
			var b = new StringBuilder();
			AiMatchLogWriter.AppendObjectStart(b);
			AiMatchLogWriter.AppendNumber(b, "schema", 2, true);
			AiMatchLogWriter.AppendString(b, "record_id", "game|Multi0");
			AiMatchLogWriter.AppendNumber(b, "duration_ticks", 2400);

			AiMatchLogWriter.AppendObjectPropertyStart(b, "player");
			AiMatchLogWriter.AppendString(b, "name", "Multi0", true);
			AiMatchLogWriter.AppendString(b, "personality", "rush");
			AiMatchLogWriter.AppendNumber(b, "personality_switches", 2);
			AiMatchLogWriter.AppendTimeline(b, timeline);
			AiMatchLogWriter.AppendString(b, "composition", "opener");
			AiMatchLogWriter.AppendNumber(b, "composition_switches", 1);
			AiMatchLogWriter.AppendCompositionTimeline(b, compositions);
			AiMatchLogWriter.AppendEpisodeTimeline(b, episodes);
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
		public void CompositionAndEpisodeTimelinesRoundTrip()
		{
			var compositions = new List<AiMatchLogCompositionTransition>
			{
				new(9000, "tdgdi_armorpush")
			};
			var episodes = new List<AiMatchLogEpisodeTransition>
			{
				new(0, "rush", "", 0, 0),
				new(9000, "rush", "tdgdi_armorpush", 1500, 800)
			};

			using var doc = JsonDocument.Parse(BuildPlayerLine(null, compositions, episodes));
			var player = doc.RootElement.GetProperty("player");
			Assert.That(player.GetProperty("composition").GetString(), Is.EqualTo("opener"));
			Assert.That(player.GetProperty("composition_switches").GetInt32(), Is.EqualTo(1));

			var ct = player.GetProperty("composition_timeline");
			Assert.That(ct.GetArrayLength(), Is.EqualTo(1));
			Assert.That(ct[0].GetProperty("composition").GetString(), Is.EqualTo("tdgdi_armorpush"));

			var ep = player.GetProperty("episode_timeline");
			Assert.That(ep.GetArrayLength(), Is.EqualTo(2));
			Assert.That(ep[1].GetProperty("composition").GetString(), Is.EqualTo("tdgdi_armorpush"));
			Assert.That(ep[1].GetProperty("kills_cost").GetInt32(), Is.EqualTo(1500));
			Assert.That(ep[1].GetProperty("deaths_cost").GetInt32(), Is.EqualTo(800));
		}

		[Test]
		public void EmptySchema2FieldsStillProduceParseableJson()
		{
			using var doc = JsonDocument.Parse(BuildPlayerLine(null));
			var player = doc.RootElement.GetProperty("player");
			Assert.That(player.GetProperty("composition_timeline").GetArrayLength(), Is.EqualTo(0));
			Assert.That(player.GetProperty("episode_timeline").GetArrayLength(), Is.EqualTo(0));
			Assert.That(doc.RootElement.GetProperty("schema").GetInt32(), Is.EqualTo(2));
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

		// stats_timeline follows kills_cost inside "stats", so a missing separator would break every
		// line the same way the personality timeline once did.
		[TestCase(false)]
		[TestCase(true)]
		public void StatsTimelineRoundTrips(bool empty)
		{
			var b = new StringBuilder();
			AiMatchLogWriter.AppendObjectStart(b);
			AiMatchLogWriter.AppendObjectPropertyStart(b, "stats", true);
			AiMatchLogWriter.AppendNumber(b, "kills_cost", 100, true);
			AiMatchLogWriter.AppendStatsTimeline(b, empty ? null : new List<int[]> { new[] { 750, 1200, 1000, 800, 5000, 0, 0, 200, 1 }, new[] { 1500, 2600, 2500, 1900, 7000, 300, 110, 100, 0 } });
			b.Append("}}");

			using var doc = JsonDocument.Parse(b.ToString());
			var stats = doc.RootElement.GetProperty("stats");
			Assert.That(stats.GetProperty("stats_timeline_fields").GetString(), Is.EqualTo(AiMatchLogWriter.StatsTimelineFields));
			var timeline = stats.GetProperty("stats_timeline");
			Assert.That(timeline.GetArrayLength(), Is.EqualTo(empty ? 0 : 2));
			if (!empty)
			{
				Assert.That(timeline[1].GetArrayLength(), Is.EqualTo(AiMatchLogWriter.StatsTimelineFields.Split(',').Length));
				Assert.That(timeline[1][3].GetInt32(), Is.EqualTo(1900));
			}
		}

		[Test]
		public void OwnershipCountsAreOneObjectWithEveryKindAndTheWorstTypesFirst()
		{
			var counts = new Dictionary<BotOwnershipViolation, int> { [BotOwnershipViolation.DoubleOwner] = 3, [BotOwnershipViolation.Orphan] = 1 };
			var byType = new Dictionary<(BotOwnershipViolation, string), int>
			{
				[(BotOwnershipViolation.DoubleOwner, "td_gdi_humveemkii")] = 2,
				[(BotOwnershipViolation.DoubleOwner, "td_gdi_shotgunner")] = 1,
				[(BotOwnershipViolation.Orphan, "td_gdi_apc")] = 1,
			};

			var b = new StringBuilder("{");
			AiMatchLogWriter.AppendNumber(b, "schema", 2, true);
			AiMatchLogWriter.AppendOwnership(b, 240, counts, byType);
			b.Append('}');

			using var doc = JsonDocument.Parse(b.ToString());
			var o = doc.RootElement.GetProperty("ownership");
			Assert.That(o.GetProperty("checks").GetInt32(), Is.EqualTo(240));
			Assert.That(o.GetProperty("double_owner").GetInt32(), Is.EqualTo(3));
			Assert.That(o.GetProperty("two_squads").GetInt32(), Is.EqualTo(0), "every kind is present, zero included");
			Assert.That(o.GetProperty("held_by_disabled").GetInt32(), Is.EqualTo(0));
			Assert.That(o.GetProperty("dead_held").GetInt32(), Is.EqualTo(0));
			Assert.That(o.GetProperty("orphan").GetInt32(), Is.EqualTo(1));
			var first = o.GetProperty("by_type")[0];
			Assert.That(first.GetProperty("kind").GetString(), Is.EqualTo("double_owner"));
			Assert.That(first.GetProperty("type").GetString(), Is.EqualTo("td_gdi_humveemkii"));
			Assert.That(first.GetProperty("units").GetInt32(), Is.EqualTo(2));
			Assert.That(o.GetProperty("by_type").GetArrayLength(), Is.EqualTo(3));
		}
	}
}
