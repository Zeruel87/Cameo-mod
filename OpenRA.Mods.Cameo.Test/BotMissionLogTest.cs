#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	// MC1 (docs/design/AI_MISSION_CARDS.md): one vocabulary and one line format for every bot stack's mission cards.
	[TestFixture]
	public sealed class BotMissionLogTest
	{
		[Test]
		public void TheGeneralsLogLineIsGreppableByMissionAndAttempt()
		{
			var line = BotMissionLog.FormatLine("Multi0", "capture:Multi1:td_gdi_constructionyard:412", 2,
				BotMissionAttemptState.Failed, BotMissionReasons.LostUnits, "Engineers", 5210);
			Assert.That(line, Is.EqualTo(
				"AI Multi0: MISSION capture:Multi1:td_gdi_constructionyard:412 ATTEMPT 2 FAILED reason=lost_units by=Engineers tick=5210"));
		}

		[Test]
		public void AnAttemptExistsOnlyFromCommit()
		{
			// fransotto, 2026-09-30: DENIED is mission/bid feedback — a mission can be denied by every commander without
			// any execution attempt existing — so it is a mission event, not an attempt state.
			Assert.That(Enum.GetNames<BotMissionAttemptState>(), Is.EqualTo(new[]
				{ "Committed", "Progressing", "Stalled", "Recover", "Success", "Failed", "Released" }));
			Assert.That(Enum.GetNames<BotMissionEvent>(), Is.EqualTo(new[] { "Published", "Denied", "Dormant", "Reopened" }));
			Assert.That(BotMissionLog.IsTerminal(BotMissionAttemptState.Success), Is.True);
			Assert.That(BotMissionLog.IsTerminal(BotMissionAttemptState.Released), Is.True);
			Assert.That(BotMissionLog.IsTerminal(BotMissionAttemptState.Stalled), Is.False);
			Assert.That(BotMissionLog.IsTerminal(BotMissionAttemptState.Recover), Is.False);
		}

		[Test]
		public void ReasonsAreTheSharedSetOrAPrivateXPrefix()
		{
			Assert.That(BotMissionReasons.IsValid(null), Is.True);
			Assert.That(BotMissionReasons.IsValid("lost_units"), Is.True);
			Assert.That(BotMissionReasons.IsValid("x_frans_board_closed"), Is.True);
			Assert.That(BotMissionReasons.IsValid("mission-board-closed"), Is.False, "a dialect must be caught, not archived");
			Assert.That(BotMissionReasons.IsValid("x_Board"), Is.False);
			Assert.That(BotMissionReasons.IsValid("x_"), Is.False);
		}

		[Test]
		public void AMissionEventIsItsOwnRecordKindWithNoAttempt()
		{
			var record = new BotMissionRecord
			{
				MissionId = "capture:oilb:611", Event = BotMissionEvent.Dormant, Reason = BotMissionReasons.Outmatched,
				Executor = "Engineers", Tick = 6919
			};

			var line = AiMissionLogWriter.BuildLine(record, "g", "m", "A Nuclear Winter", new DateTime(2026, 9, 30, 0, 0, 0, DateTimeKind.Utc));
			using var doc = JsonDocument.Parse(line);
			var root = doc.RootElement;
			Assert.That(root.GetProperty("record_kind").GetString(), Is.EqualTo("mission"));
			Assert.That(root.GetProperty("event").GetString(), Is.EqualTo("DORMANT"));
			Assert.That(root.TryGetProperty("attempt", out _), Is.False);
			Assert.That(root.TryGetProperty("attempt_id", out _), Is.False);
			Assert.That(BotMissionLog.FormatEventLine("Multi0", "capture:oilb:611", BotMissionEvent.Dormant, "outmatched", "Engineers", 6919),
				Is.EqualTo("AI Multi0: MISSION capture:oilb:611 DORMANT reason=outmatched by=Engineers tick=6919"));
		}

		[Test]
		public void ADenialNobodyBidOnHasNoExecutorRatherThanAnEmptyOne()
		{
			// DAWN's #679 smoke: broker DENIED rows serialized `by: ""`.
			var record = new BotMissionRecord { MissionId = "frans:77", Event = BotMissionEvent.Denied, Executor = "", Tick = 500 };
			var line = AiMissionLogWriter.BuildLine(record, "g", "m", "A Nuclear Winter", new DateTime(2026, 9, 30, 0, 0, 0, DateTimeKind.Utc));
			using var doc = JsonDocument.Parse(line);
			Assert.That(doc.RootElement.TryGetProperty("by", out _), Is.False);
			Assert.That(BotMissionLog.FormatEventLine("Multi0", "frans:77", BotMissionEvent.Denied, null, "", 500),
				Is.EqualTo("AI Multi0: MISSION frans:77 DENIED by=? tick=500"));
		}

		[Test]
		public void TheArchiveLineIsOneJsonObjectWithTheSchemaAndIds()
		{
			var record = new BotMissionRecord
			{
				MissionId = "capture:Multi1:oilb:526", Attempt = 1, State = BotMissionAttemptState.Success,
				Reason = BotMissionReasons.Done, Executor = "Engineers", MissionType = "capture",
				TargetCell = new CPos(61, 33), Units = 1, Tick = 2561
			};

			var line = AiMissionLogWriter.BuildLine(record, "g-uid", "m-uid", "A Nuclear Winter", new DateTime(2026, 9, 30, 12, 0, 0, DateTimeKind.Utc));
			using var doc = JsonDocument.Parse(line);
			var root = doc.RootElement;
			Assert.That(root.GetProperty("schema").GetString(), Is.EqualTo("mission-card/1"));
			Assert.That(root.GetProperty("record_kind").GetString(), Is.EqualTo("attempt"));
			Assert.That(root.GetProperty("mission_id").GetString(), Is.EqualTo("capture:Multi1:oilb:526"));
			Assert.That(root.GetProperty("attempt_id").GetString(), Is.EqualTo("capture:Multi1:oilb:526|A1"));
			Assert.That(root.GetProperty("state").GetString(), Is.EqualTo("SUCCESS"));
			Assert.That(root.GetProperty("terminal").GetBoolean(), Is.True);
			Assert.That(root.GetProperty("target_cell").GetString(), Is.EqualTo("61,33"));
			Assert.That(root.GetProperty("tick").GetInt32(), Is.EqualTo(2561));
			Assert.That(root.TryGetProperty("region", out _), Is.False, "absent context stays absent");
		}

		[Test]
		public void ACaptureThatTurnedTheBuildingOursIsASuccessEvenThoughTheEngineerIsGone()
		{
			// The engineer is consumed by the capture, and Actor.IsDead includes Disposed.
			Assert.That(EngineerBotModule.CaptureVerdict(targetOurs: true, stuck: false, engineerDead: true, targetGone: false),
				Is.EqualTo((BotMissionAttemptState.Success, BotMissionReasons.Done)));
		}

		[Test]
		public void CaptureVerdictsForTheOtherEndings()
		{
			Assert.That(EngineerBotModule.CaptureVerdict(false, true, false, false),
				Is.EqualTo((BotMissionAttemptState.Released, BotMissionReasons.Stuck)));
			Assert.That(EngineerBotModule.CaptureVerdict(false, false, true, false),
				Is.EqualTo((BotMissionAttemptState.Failed, BotMissionReasons.LostUnits)));
			Assert.That(EngineerBotModule.CaptureVerdict(false, false, false, true),
				Is.EqualTo((BotMissionAttemptState.Released, BotMissionReasons.TargetGone)));
			Assert.That(EngineerBotModule.CaptureVerdict(false, false, false, false),
				Is.EqualTo((BotMissionAttemptState.Released, BotMissionReasons.Dropped)));
		}

		[Test]
		public void TwoLostEngineersInARowRestTheMission()
		{
			Assert.That(EngineerBotModule.GoesDormant(1, 2), Is.False);
			Assert.That(EngineerBotModule.GoesDormant(2, 2), Is.True);
			Assert.That(EngineerBotModule.GoesDormant(9, 0), Is.False, "0 disables the shelf");
		}

		[Test]
		public void OnlyTechBuildingsGetAnEscortTheEnemyBaseIsTakenByStealth()
		{
			Assert.That(EngineerBotModule.EscortEligible(enemyOwned: false, priorityType: true), Is.True, "neutral derrick");
			Assert.That(EngineerBotModule.EscortEligible(enemyOwned: true, priorityType: true), Is.True, "a tech building the enemy holds");
			Assert.That(EngineerBotModule.EscortEligible(enemyOwned: true, priorityType: false), Is.False, "their yard: sneak, never escort");
		}

		[Test]
		public void OnlyAStealthInfiltrationRollsForATransport()
		{
			Assert.That(EngineerBotModule.WantsTransport(stealthTarget: true, roll: 24, chancePct: 25), Is.True);
			Assert.That(EngineerBotModule.WantsTransport(stealthTarget: true, roll: 25, chancePct: 25), Is.False);
			Assert.That(EngineerBotModule.WantsTransport(stealthTarget: false, roll: 0, chancePct: 25), Is.False, "tech buildings: escort rules");
			Assert.That(EngineerBotModule.WantsTransport(stealthTarget: true, roll: 0, chancePct: 0), Is.False);
		}

		[Test]
		public void ARunVisitsTheNearestNextBuildingAndStopsAtItsSize()
		{
			// Stops: 0 the chosen yard, then buildings at increasing distances in a scattered order.
			var stops = new[] { new CPos(10, 10), new CPos(40, 40), new CPos(12, 10), new CPos(20, 10), new CPos(11, 14) };
			Assert.That(EngineerBotModule.GreedyRoute(stops, 0, 5), Is.EqualTo(new[] { 0, 2, 4, 3, 1 }));
			Assert.That(EngineerBotModule.GreedyRoute(stops, 0, 2), Is.EqualTo(new[] { 0, 2 }), "one engineer per stop");
			Assert.That(EngineerBotModule.GreedyRoute(stops, 0, 1), Is.EqualTo(new[] { 0 }));
		}

		[Test]
		public void AnEscortRequestAlwaysClearsTheSquadManagersBar()
		{
			// The first flag-on match published 440, 500, 700 and 1000 against a 1500 bar: no escort ever came.
			Assert.That(EngineerBotModule.EscortRequestValue(440, 1500), Is.EqualTo(1500));
			Assert.That(EngineerBotModule.EscortRequestValue(2600, 1500), Is.EqualTo(2600));
			Assert.That(EngineerBotModule.EscortRequestValue(0, 0), Is.EqualTo(1));
		}

		[Test]
		public void AnEscortedCaptureWaitsForSuperiority()
		{
			Assert.That(EngineerBotModule.EscortReady(0, 0, 100), Is.True, "undefended: no escort needed");
			Assert.That(EngineerBotModule.EscortReady(1500, 1600, 100), Is.False);
			Assert.That(EngineerBotModule.EscortReady(1600, 1600, 100), Is.True);
			Assert.That(EngineerBotModule.EscortReady(2400, 1600, 150), Is.True);
			Assert.That(EngineerBotModule.EscortReady(int.MaxValue / 50, int.MaxValue / 60, 100), Is.True, "no int overflow");

			// Thinning: 150% superiority alone is not enough while the defenders are still at full strength.
			Assert.That(EngineerBotModule.EscortReady(2400, 1600, 1600, 150, 50), Is.False, "escort arrived, fight not won");
			Assert.That(EngineerBotModule.EscortReady(2400, 800, 1600, 150, 50), Is.True, "defenders halved");
			Assert.That(EngineerBotModule.EscortReady(1000, 800, 1600, 150, 50), Is.False, "halved but escort too weak");
			Assert.That(EngineerBotModule.EscortReady(2400, 1600, 1600, 150, 100), Is.True, "100 = no thinning required");
			Assert.That(EngineerBotModule.EscortReady(0, 0, 1600, 150, 50), Is.True, "defenders gone");
			Assert.That(EngineerBotModule.EscortReady(5000, 2000, 1600, 150, 50), Is.False, "reinforced past the publish value");
		}

		[Test]
		public void OneMissionOneLiveAttemptByDefault()
		{
			Assert.That(EngineerBotModule.TargetFull(0, 1), Is.False);
			Assert.That(EngineerBotModule.TargetFull(1, 1), Is.True);
			Assert.That(EngineerBotModule.TargetFull(5, 0), Is.False, "0 keeps the parents' unlimited behaviour");
		}

		[Test]
		public void TheCaptureMissionIsTheBuildingNotTheEngineer()
		{
			// No owner in the id: a derrick that changes hands is still the same mission (a smoke match split one in two).
			Assert.That(EngineerBotModule.CaptureMissionId("oilb", 526), Is.EqualTo("capture:oilb:526"));
		}

		[Test]
		public void ExposureCountsRouteCellsUnderFireButNotTheFinalApproach()
		{
			var target = new CPos(50, 10);
			var route = new List<(CPos, int)>
			{
				(new CPos(10, 10), 0), (new CPos(20, 10), 900), (new CPos(30, 10), 1200), (new CPos(40, 10), 0),
				(new CPos(46, 10), 700), (new CPos(49, 10), 5000),
			};

			// (46,10) is 4 cells out and (49,10) 1 cell out: both inside a 6-cell approach, so only 2 cells count.
			Assert.That(EngineerBotModule.ExposedCells(route, target, 6), Is.EqualTo(2));
			Assert.That(EngineerBotModule.ExposedCells(route, target, 0), Is.EqualTo(4), "no approach excluded");
		}

		[Test]
		public void RemainingExposureCountsOnlyCellsAheadOutsideTheApproach()
		{
			var route = Enumerable.Range(0, 21).Select(x => new CPos(x, 5)).ToList();
			var target = new CPos(21, 5);
			Func<CPos, int> hot = c => c.X is 2 or 8 or 12 or 19 ? 1 : 0;

			// From the start: 2, 8, 12 count; 19 is 2 cells from the target (inside a 6-cell approach).
			Assert.That(EngineerBotModule.RemainingExposure(route, new CPos(0, 5), target, 6, hot), Is.EqualTo(3));
			Assert.That(EngineerBotModule.RemainingExposure(route, new CPos(8, 5), target, 6, hot), Is.EqualTo(1), "behind the engineer is walked already");
			Assert.That(EngineerBotModule.RemainingExposure(route, new CPos(13, 6), target, 6, hot), Is.EqualTo(0));
			Assert.That(EngineerBotModule.RemainingExposure(null, new CPos(0, 5), target, 6, hot), Is.EqualTo(0));
		}

		[Test]
		public void StealthGateIsOffAtMinusOneAndTripsAboveTheThreshold()
		{
			Assert.That(EngineerBotModule.StealthGuarded(50, -1), Is.False, "-1 = off");
			Assert.That(EngineerBotModule.StealthGuarded(0, 0), Is.False);
			Assert.That(EngineerBotModule.StealthGuarded(1, 0), Is.True);
			Assert.That(EngineerBotModule.StealthGuarded(2, 2), Is.False, "at the threshold is allowed");
			Assert.That(EngineerBotModule.StealthGuarded(3, 2), Is.True);
		}

		[Test]
		public void RankScorePrefersValueAndPunishesExposure()
		{
			// Same distance and value: the less exposed target wins.
			Assert.That(EngineerBotModule.RankScore(1000, 20, 0, 10), Is.GreaterThan(EngineerBotModule.RankScore(1000, 20, 5, 10)));

			// A far valuable safe target beats a near cheap one; an exposed valuable one does not.
			var nearCheap = EngineerBotModule.RankScore(300, 10, 0, 10);
			Assert.That(EngineerBotModule.RankScore(3000, 40, 0, 10), Is.GreaterThan(nearCheap));
			Assert.That(EngineerBotModule.RankScore(3000, 40, 30, 10), Is.LessThan(EngineerBotModule.RankScore(3000, 40, 0, 10)));

			// Weight 0 ignores exposure; with no exposure the order is value per distance.
			Assert.That(EngineerBotModule.RankScore(1000, 20, 9, 0), Is.EqualTo(EngineerBotModule.RankScore(1000, 20, 0, 10)));
			Assert.That(EngineerBotModule.RankScore(0, 5, 0, 10), Is.EqualTo(0));
		}

		[Test]
		public void WaypointsFollowTheRouteAndStopBeforeTheApproach()
		{
			var route = Enumerable.Range(0, 21).Select(x => new CPos(x, 5)).ToList();
			var target = new CPos(21, 5);
			Assert.That(EngineerBotModule.Waypoints(route, 5, 6, target),
				Is.EqualTo(new[] { new CPos(5, 5), new CPos(10, 5) }), "(15,5) is 6 cells out: inside the approach");
			Assert.That(EngineerBotModule.Waypoints(route.Take(4).ToList(), 5, 6, target), Is.Empty, "short route: capture order alone");
		}

		[Test]
		public void AFailedAttemptRecordsWhereTheEngineerFell()
		{
			var record = new BotMissionRecord
			{
				MissionId = "capture:oilb:1067", Attempt = 3, State = BotMissionAttemptState.Failed, Reason = BotMissionReasons.LostUnits,
				Executor = "Engineers", TargetCell = new CPos(60, 8), UnitCell = new CPos(41, 22), Tick = 14720
			};

			var line = AiMissionLogWriter.BuildLine(record, "g", "m", "A Nuclear Winter", new DateTime(2026, 9, 30, 0, 0, 0, DateTimeKind.Utc));
			using var doc = JsonDocument.Parse(line);
			Assert.That(doc.RootElement.GetProperty("target_cell").GetString(), Is.EqualTo("60,8"));
			Assert.That(doc.RootElement.GetProperty("unit_cell").GetString(), Is.EqualTo("41,22"));
		}
	}
}
