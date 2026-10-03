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

using System.Text.Json;
using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	// EL-0 (AI_ARCHITECTURE 12.30): the pure engagement math. The score vectors are mirrored number for number in
	// tools/tests/test_engagement_report.py so EngagementScore and ai_log_common.engagement_score cannot diverge.
	[TestFixture]
	public sealed class EngagementMathTest
	{
		[TestCase(600, 200, 500)]
		[TestCase(0, 0, 0)]
		[TestCase(100, 300, -500)]
		[TestCase(100, 200, -333)]
		[TestCase(500, 0, 1000)]
		public void TradeIsZeroSum(int killed, int lost, int expected)
		{
			Assert.That(EngagementScore.Trade(killed, lost), Is.EqualTo(expected));
			Assert.That(EngagementScore.Trade(lost, killed), Is.EqualTo(-expected));
		}

		[Test]
		public void PredictedTradeScoresThePredictedLosses()
		{
			Assert.That(EngagementScore.PredictedTrade(1000, 1000, 600, 0), Is.EqualTo(428));
			Assert.That(EngagementScore.PredictedTrade(1000, 800, 600, 0), Is.EqualTo(333));
			Assert.That(EngagementScore.PredictedTrade(0, 0, 0, 0), Is.EqualTo(0));
		}

		[Test]
		public void BuildingRewardIsTwoThirdsHpOneThirdDeath()
		{
			Assert.That(EngagementScore.HpLost(1000, 500, 1000), Is.EqualTo(500));
			Assert.That(EngagementScore.BuildingLoss(500, false), Is.EqualTo(333));
			Assert.That(EngagementScore.BuildingLoss(1000, true), Is.EqualTo(1000));
			Assert.That(EngagementScore.BuildingsLoss(new[] { (1000, 500, false), (3000, 1000, true) }), Is.EqualTo(833));
			Assert.That(EngagementScore.BuildingsLoss(new (int, int, bool)[0]), Is.EqualTo(0));
		}

		[Test]
		public void ObjectiveAndTotal()
		{
			Assert.That(EngagementScore.Objective("defend", 333, 0, true, false), Is.EqualTo(334));
			Assert.That(EngagementScore.Objective("defend", 333, 0, false, false), Is.EqualTo(0));
			Assert.That(EngagementScore.Objective("attack", 0, 1000, false, true), Is.EqualTo(1000));
			Assert.That(EngagementScore.Objective("attack", 0, 0, false, true), Is.EqualTo(-1000));
			Assert.That(EngagementScore.Objective("field", 500, 500, true, true), Is.EqualTo(0));
			Assert.That(EngagementScore.Total(500, 250, 334), Is.EqualTo(396));
			Assert.That(EngagementScore.Total(1000, 2000, 1000), Is.EqualTo(1000));
			Assert.That(EngagementScore.Total(-1000, -2000, -1000), Is.EqualTo(-1000));
		}

		[Test]
		public void EventsClusterInSpaceAndTime()
		{
			var t = new EngagementTracker(10, 150);
			var a = t.Locate(100, 50, 50, out var created);
			Assert.That(created, Is.True);
			Assert.That(t.Locate(110, 55, 55, out created), Is.SameAs(a));
			Assert.That(created, Is.False);

			var far = t.Locate(120, 80, 80, out created);
			Assert.That(created, Is.True);
			Assert.That(far, Is.Not.SameAs(a));
			Assert.That(t.Open.Count, Is.EqualTo(2));

			// a (last event 110) goes quiet at 260; far (120) at 270.
			Assert.That(t.CollectQuiet(259), Is.Empty);
			var closed = t.CollectQuiet(260);
			Assert.That(closed, Is.EqualTo(new[] { a }));
			Assert.That(t.Open.Count, Is.EqualTo(1));
			Assert.That(t.CloseAll(), Is.EqualTo(new[] { far }));
		}

		[Test]
		public void PositionRingReadsBackAboutOneWindow()
		{
			var r = new PositionRing();
			Assert.That(r.TryOlder(0, 150, out _, out _), Is.False);
			for (var i = 0; i < 7; i++)
				r.Add(i * 50, i * 10, 0);

			// samples at ticks 100..300 held; now = 300: newest at least 150 old is tick 150.
			Assert.That(r.TryOlder(300, 150, out var x, out _), Is.True);
			Assert.That(x, Is.EqualTo(30));

			// only recent samples: falls back to the oldest one before now.
			var s = new PositionRing();
			s.Add(250, 5, 0);
			s.Add(300, 9, 0);
			Assert.That(s.TryOlder(300, 150, out x, out _), Is.True);
			Assert.That(x, Is.EqualTo(5));
		}

		[Test]
		public void AngleIsZeroAlongAndOppositeAgainst()
		{
			Assert.That(EngagementGeometry.AngleDegrees(10, 0, 5, 0), Is.EqualTo(0));
			Assert.That(EngagementGeometry.AngleDegrees(10, 0, -5, 0), Is.EqualTo(180));
			Assert.That(EngagementGeometry.AngleDegrees(0, 3, 4, 0), Is.EqualTo(90));
			Assert.That(EngagementGeometry.AngleDegrees(0, 0, 4, 0), Is.EqualTo(-1));
		}

		[Test]
		public void KindFollowsTheBaseRadii()
		{
			Assert.That(EngagementRecord.KindOf(5, 90), Is.EqualTo("defend"));
			Assert.That(EngagementRecord.KindOf(60, 12), Is.EqualTo("attack"));
			Assert.That(EngagementRecord.KindOf(60, -1), Is.EqualTo("field"));
			Assert.That(EngagementRecord.KindOf(-1, -1), Is.EqualTo("field"));
		}

		[Test]
		public void LinesAreValidJson()
		{
			var s = new EngagementState { Id = 3, StartTick = 100, EventCount = 1, SumX = 40, SumY = 41, OwnLostUnitValue = 400, OwnLostUnits = 2,
				EnemyKilledUnitValue = 900, EnemyKilledUnits = 3, FirstOwnHurtTick = 100, FirstOwnMobileDealtTick = 160 };
			s.LostByRole["frontline"] = 400;
			s.Buildings[1] = new EngagementBuilding { Own = true, Value = 500, MaxHp = 1000, HpStart = 1000, HpEnd = 500 };
			s.Defences.Add(new EngagementDefence(9, 45, 45, 7, 600));
			s.SeenStart = new EngagementSeen { Tick = 100 };
			s.SeenEnd = new EngagementSeen { Tick = 300 };
			var h = new EngagementHeader { GameUid = "g", MapUid = "m", Player = "Multi0", BotType = "genericbot", Faction = "td_gdi", Personality = "rush",
				CloseReason = "quiet", EndTick = 300, Kind = "defend", OwnBaseX = 30, OwnBaseY = 30 };

			using var doc = JsonDocument.Parse(EngagementRecord.BuildEngagement(h, s));
			var root = doc.RootElement;
			Assert.That(root.GetProperty("schema").GetString(), Is.EqualTo("engagement/1"));
			Assert.That(root.GetProperty("response").GetProperty("response_ticks").GetInt32(), Is.EqualTo(60));
			Assert.That(root.GetProperty("score").GetProperty("trade_milli").GetInt32(), Is.EqualTo(EngagementScore.Trade(900, 400)));
			Assert.That(root.GetProperty("outcome").GetProperty("own_lost_by_role").GetProperty("frontline").GetInt32(), Is.EqualTo(400));
			Assert.That(root.TryGetProperty("truth", out _), Is.True);
			Assert.That(root.GetProperty("skirmish").GetBoolean(), Is.False);

			h.Kind = "field";
			using var field = JsonDocument.Parse(EngagementRecord.BuildEngagement(h, s));
			Assert.That(field.RootElement.TryGetProperty("response", out _), Is.False);

			using var posture = JsonDocument.Parse(EngagementRecord.BuildPosture(h, 0, 10, 11, 5, 3000, 20, -1, 4, 30, 250, "40,41", 7));
			Assert.That(posture.RootElement.GetProperty("record").GetString(), Is.EqualTo("posture"));
			Assert.That(posture.RootElement.GetProperty("staging_cell").GetString(), Is.EqualTo("40,41"));
			Assert.That(posture.RootElement.GetProperty("army_to_staging_cells").GetInt32(), Is.EqualTo(7));
			using var noStaging = JsonDocument.Parse(EngagementRecord.BuildPosture(h, 1, 10, 11, 5, 3000, 20, -1, 4, 30, 250, null, -1));
			Assert.That(noStaging.RootElement.GetProperty("staging_cell").ValueKind, Is.EqualTo(JsonValueKind.Null));
		}
	}
}
