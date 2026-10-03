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
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// The execution lifecycle of ONE attempt (docs/design/AI_MISSION_CARDS.md §2.2, schema `mission-card/1`). An attempt
	/// exists only from COMMIT — fransotto, 2026-09-30: a mission can be published and denied by every commander without
	/// any execution ever existing. Terminal: SUCCESS, FAILED (the units were lost), RELEASED (handed back, no verdict).
	/// </summary>
	public enum BotMissionAttemptState { Committed, Progressing, Stalled, Recover, Success, Failed, Released }

	/// <summary>
	/// Mission-level events: the card's own story, observable apart from any attempt. DENIED is bid/mission feedback (no
	/// executor took it); DORMANT puts the card on the shelf; REOPENED takes it off again (new recon, a changed Best Read,
	/// a rest that ended). The card is the strategic memory; attempts are evidence written back to it.
	/// </summary>
	public enum BotMissionEvent { Published, Denied, Dormant, Reopened }

	/// <summary>The closed reason set. Project-private reasons carry an `x_` prefix (e.g. `x_frans_board_closed`).</summary>
	public static class BotMissionReasons
	{
		public const string NoUnits = "no_units";
		public const string Unreachable = "unreachable";
		public const string Undeployable = "undeployable";
		public const string Reserved = "reserved";
		public const string Outmatched = "outmatched";
		public const string TargetGone = "target_gone";
		public const string Timeout = "timeout";
		public const string Stuck = "stuck";
		public const string Superseded = "superseded";
		public const string LostUnits = "lost_units";
		public const string Done = "done";

		/// <summary>The executor's order ended (the unit went idle) without a result either way.</summary>
		public const string Dropped = "dropped";

		/// <summary>The match tore down while the attempt was still open. Written by
		/// <see cref="BotMissionAttemptTracker"/>, never by an executor.</summary>
		public const string MatchEnd = "match_end";

		public static readonly IReadOnlyCollection<string> Shared = new[]
		{
			NoUnits, Unreachable, Undeployable, Reserved, Outmatched, TargetGone, Timeout, Stuck, Superseded, LostUnits, Done, Dropped, MatchEnd
		};

		/// <summary>Null (no reason), one of the shared reasons, or an `x_` private reason of lowercase words.</summary>
		public static bool IsValid(string reason) =>
			reason == null || Shared.Contains(reason)
				|| (reason.Length > 2 && reason.StartsWith("x_", System.StringComparison.Ordinal)
					&& reason.All(c => c == '_' || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')));
	}

	/// <summary>
	/// One record: a mission-level event when <see cref="Event"/> is set (no attempt), otherwise an attempt transition.
	/// Identity is the composite (game_uid, mission_id, attempt) — unique within one match, never across matches.
	/// Everything except the ids and the state/event is optional context.
	/// </summary>
	public sealed class BotMissionRecord
	{
		public Player Player;
		public string MissionId;
		public BotMissionEvent? Event;
		public int Attempt;
		public BotMissionAttemptState State;
		public string Reason;
		public string Executor;
		public string MissionType;
		public int? RegionIndex;
		public CPos? TargetCell;

		/// <summary>Where the executing unit was when the record was written (a lost unit: where it fell).</summary>
		public CPos? UnitCell;
		public int? Units;
		public int? Value;
		public int Tick;
	}

	/// <summary>
	/// Receives every mission record, e.g. Cameo's AiMissionLogWriter (World actor), which appends
	/// `cameo-ai-missions.jsonl` record-only (DESIGN §21.1). Implemented on the World actor.
	/// </summary>
	public interface IBotMissionRecordSink
	{
		void MissionRecorded(BotMissionRecord record);
	}

	/// <summary>
	/// MC1 (AI_MASTER_PLAN §3): the ONE writer of mission-card transitions for every bot stack — the genericbot squad
	/// layer, the master AI, the MCV and engineer owners, and the vendored Fransbot broker all emit through here, so
	/// both logs share one line format and one archive format. It never changes a decision: one plain-text debug.log
	/// line ("the General's log") plus a record handed to the World's sinks.
	/// </summary>
	public static class BotMissionLog
	{
		public static string StateName(BotMissionAttemptState state) => state.ToString().ToUpperInvariant();

		public static string EventName(BotMissionEvent e) => e.ToString().ToUpperInvariant();

		public static bool IsTerminal(BotMissionAttemptState state) =>
			state is BotMissionAttemptState.Success or BotMissionAttemptState.Failed or BotMissionAttemptState.Released;

		/// <summary>The debug.log line of a mission-level event. Grep key: `MISSION &lt;id&gt;`.</summary>
		public static string FormatEventLine(string playerName, string missionId, BotMissionEvent e, string reason, string by, int tick)
		{
			var line = $"AI {playerName}: MISSION {missionId} {EventName(e)}";
			if (reason != null)
				line += $" reason={reason}";

			return line + $" by={(string.IsNullOrEmpty(by) ? "?" : by)} tick={tick}";
		}

		/// <summary>The debug.log line, free of world state so it can be tested. Grep key: `MISSION &lt;id&gt; ATTEMPT &lt;n&gt;`.</summary>
		public static string FormatLine(string playerName, string missionId, int attempt, BotMissionAttemptState state,
			string reason, string executor, int tick)
		{
			var line = $"AI {playerName}: MISSION {missionId} ATTEMPT {attempt} {StateName(state)}";
			if (reason != null)
				line += $" reason={reason}";

			return line + $" by={(string.IsNullOrEmpty(executor) ? "?" : executor)} tick={tick}";
		}

		public static void Write(BotMissionRecord record)
		{
			if (record?.Player == null || string.IsNullOrEmpty(record.MissionId))
				return;

			// LC8: keep the player's open-attempt ledger in step so match-end teardown can
			// release whatever never reached a terminal state. Note() is a no-op when the
			// trait is absent (classic without the tracker, humans) — callers change nothing.
			record.Player.PlayerActor?.TraitOrDefault<BotMissionAttemptTracker>()?.Note(record);

			// A reason outside the shared set is a contract bug in the emitter: write it, but mark it so the story tool
			// and tests catch it instead of the archive silently growing a dialect.
			if (!BotMissionReasons.IsValid(record.Reason))
				record.Reason = "x_invalid_" + new string(record.Reason.ToLowerInvariant().Where(c => char.IsLetterOrDigit(c) || c == '_').ToArray());

			var world = record.Player.World;
			record.Tick = world.WorldTick;
			Log.Write("debug", record.Event is BotMissionEvent e
				? FormatEventLine(record.Player.InternalName, record.MissionId, e, record.Reason, record.Executor, record.Tick)
				: FormatLine(record.Player.InternalName, record.MissionId, record.Attempt, record.State, record.Reason, record.Executor, record.Tick));

			foreach (var sink in world.WorldActor.TraitsImplementing<IBotMissionRecordSink>())
				sink.MissionRecorded(record);
		}
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("LC8 (mission outcomes): keeps the set of open mission attempts and writes a terminal",
		"Released(match_end) record for anything still open when the player's actor tears down,",
		"so no attempt stays dangling past GameOver. Bookkeeping only — never orders.")]
	public sealed class BotMissionAttemptTrackerInfo : TraitInfo
	{
		public override object Create(ActorInitializer init) { return new BotMissionAttemptTracker(init.Self, this); }
	}

	public sealed class BotMissionAttemptTracker : INotifyActorDisposing
	{
		readonly Player player;

		// (missionId, attempt) -> executor name, for every attempt whose last record was non-terminal.
		readonly Dictionary<(string, int), string> openAttempts = new();

		// Answer ids released by a pivot, keyed per-player so the cooldown survives the
		// personality-conditioned SquadManagerBotModuleCA instance rotating out — a fresh
		// instance's own map is empty and would re-draft the same standing request.
		readonly Dictionary<string, int> answerCooldownUntil = new();

		// Highest attempt number seen per mission id — attempt numbering lives here so a
		// personality rotation can't re-issue attempt 1 and collide the (mission, attempt)
		// identity the jsonl schema keys on.
		readonly Dictionary<string, int> lastAttempt = new();

		public BotMissionAttemptTracker(Actor self, BotMissionAttemptTrackerInfo info)
		{
			player = self.Owner;
		}

		public int NextAttemptNumber(string missionId)
		{
			return lastAttempt.GetValueOrDefault(missionId) + 1;
		}

		public int CurrentAttemptNumber(string missionId)
		{
			return lastAttempt.GetValueOrDefault(missionId);
		}

		public void CoolAnswer(string missionId, int untilTick)
		{
			answerCooldownUntil[missionId] = untilTick;
		}

		public bool AnswerCooling(string missionId, int tick)
		{
			return answerCooldownUntil.TryGetValue(missionId, out var until) && tick < until;
		}

		public void Note(BotMissionRecord record)
		{
			if (record.Event != null)
				return;

			var key = (record.MissionId, record.Attempt);
			lastAttempt[record.MissionId] = System.Math.Max(lastAttempt.GetValueOrDefault(record.MissionId), record.Attempt);
			if (BotMissionLog.IsTerminal(record.State))
				openAttempts.Remove(key);
			else
				openAttempts[key] = record.Executor;
		}

		void INotifyActorDisposing.Disposing(Actor self)
		{
			// Copy before flushing: each Write re-enters Note() on the terminal record.
			foreach (var kv in openAttempts.ToList())
			{
				openAttempts.Remove(kv.Key);
				BotMissionLog.Write(new BotMissionRecord
				{
					Player = player,
					MissionId = kv.Key.Item1,
					Attempt = kv.Key.Item2,
					State = BotMissionAttemptState.Released,
					Reason = BotMissionReasons.MatchEnd,
					Executor = kv.Value
				});
			}
		}
	}
}
