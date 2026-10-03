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

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.World)]
	[Desc("Appends record-only AI match logs for bot players.")]
	public class AiMatchLogWriterInfo : TraitInfo
	{
		[Desc("Name of the append-only AI match log file.")]
		public readonly string FileName = "cameo-ai-matches.jsonl";

		[Desc("World ticks between two stats_timeline samples (earned, spent, army, assets, kills/deaths cost). 0 disables it.")]
		public readonly int SampleIntervalTicks = 750;

		public override object Create(ActorInitializer init) { return new AiMatchLogWriter(this); }
	}

	public class AiMatchLogWriter : IWorldLoaded, IGameOver, ITick
	{
		readonly AiMatchLogWriterInfo info;

		string fallbackGameUid;
		string pendingText;
		AiLogFileAppender appender;
		bool written;
		bool eligibleAtWorldLoad;
		int nextAttemptTick;
		readonly Dictionary<OpenRA.Player, List<int[]>> samples = new();

		public AiMatchLogWriter(AiMatchLogWriterInfo info)
		{
			this.info = info;
		}

		void IWorldLoaded.WorldLoaded(World world, WorldRenderer worldRenderer)
		{
			// Save replay-in eventually clears IsLoadingGameSave. Keep the exclusion
			// for this world's entire lifetime, including its eventual GameOver.
			eligibleAtWorldLoad = Eligible(world.Type, world.IsReplay, world.IsLoadingGameSave, Game.IsHost);
			if (!eligibleAtWorldLoad)
			{
				written = true;
				return;
			}

			fallbackGameUid = Guid.NewGuid().ToString("N");
			appender = new AiLogFileAppender(info.FileName);
		}

		void ITick.Tick(Actor self)
		{
			var world = self.World;
			if (!written && info.SampleIntervalTicks > 0 && world.WorldTick % info.SampleIntervalTicks == 0)
				Sample(world);

			if (written || world.WorldTick < nextAttemptTick)
				return;

			if (pendingText != null)
			{
				TryAppend(world.WorldTick);
				return;
			}

			if (AllBotsResolved(world))
				CaptureAndAppend(world);
		}

		void IGameOver.GameOver(World world)
		{
			// World.EndGame pauses before dispatching IGameOver, and paused worlds do not advance ticks.
			// A retry scheduled here may therefore never run; retries matter for live all-bots-resolved capture.
			CaptureAndAppend(world);
		}

		void CaptureAndAppend(World world)
		{
			if (written)
				return;

			if (!eligibleAtWorldLoad || world.Type != WorldType.Regular || world.IsReplay || !Game.IsHost)
			{
				written = true;
				return;
			}

			pendingText ??= BuildLog(world);
			if (string.IsNullOrEmpty(pendingText))
			{
				written = true;
				return;
			}

			TryAppend(world.WorldTick);
		}

		void TryAppend(int worldTick)
		{
			var result = appender.TryAppend(pendingText, worldTick, out nextAttemptTick);
			if (result != AiLogAppendResult.RetryableFailure || appender.IsTerminal)
			{
				written = true;
				return;
			}
		}

		// Fixed tick cadence, unlike PlayerStatistics' own graph samples, which follow wall-clock
		// game time (every 3000 ticks at the harness's maximum speed, 750 at normal speed).
		void Sample(World world)
		{
			foreach (var player in world.Players.Where(IsLoggableBot))
			{
				var stats = player.PlayerActor.TraitOrDefault<PlayerStatistics>();
				var resources = player.PlayerActor.TraitOrDefault<PlayerResources>();
				if (!samples.TryGetValue(player, out var list))
					samples[player] = list = new List<int[]>();

				list.Add(new[]
				{
					world.WorldTick, resources?.Earned ?? 0, resources?.Spent ?? 0, stats?.ArmyValue ?? 0,
					stats?.AssetsValue ?? 0, stats?.KillsCost ?? 0, stats?.DeathsCost ?? 0,
					(resources?.Cash ?? 0) + (resources?.Resources ?? 0), IdleQueues(player)
				});
			}
		}

		// The arsenal ledger (AI_ARCHITECTURE.md §12.3): per own actor type, created / lost / value lost / value
		// destroyed, and what it destroyed by victim type — the input of the offline fitter (CA-1b) and the
		// per-enemy-faction profiles (DESIGN.md §19.2).
		/// <summary>
		/// LC5: the ownership watchdog's distinct violations for this bot, by kind and by actor type. Absent when the
		/// watchdog did not run (a match with a human, or a bot without it), so "no field" never reads as "no violations".
		/// </summary>
		internal static void AppendOwnership(StringBuilder builder, BotModules.BotOwnershipWatchdog watchdog)
		{
			if (watchdog != null)
				AppendOwnership(builder, watchdog.Passes, watchdog.Counts, watchdog.CountsByType);
		}

		internal static void AppendOwnership(StringBuilder builder, int checks,
			IReadOnlyDictionary<BotModules.BotOwnershipViolation, int> counts,
			IReadOnlyDictionary<(BotModules.BotOwnershipViolation Kind, string Type), int> byType)
		{
			AppendObjectPropertyStart(builder, "ownership");
			AppendNumber(builder, "checks", checks, true);
			foreach (var kind in Enum.GetValues<BotModules.BotOwnershipViolation>())
				AppendNumber(builder, SnakeCase(kind.ToString()), counts.GetValueOrDefault(kind));

			AppendArrayPropertyStart(builder, "by_type");
			var i = 0;
			foreach (var ((kind, type), count) in byType.OrderByDescending(kv => kv.Value)
				.ThenBy(kv => kv.Key.Kind).ThenBy(kv => kv.Key.Type, StringComparer.Ordinal))
			{
				if (i++ > 0)
					builder.Append(',');

				AppendObjectStart(builder);
				AppendString(builder, "kind", SnakeCase(kind.ToString()), true);
				AppendString(builder, "type", type);
				AppendNumber(builder, "units", count);
				builder.Append('}');
			}

			builder.Append("]}");
		}

		/// <summary>
		/// DESIGN §19.6: what the order gate did for this bot — orders refused (another module held the unit), preempted
		/// (an emergency took it), conflicts (watch mode: would have been refused), crossed orders (two modules ordered one
		/// unit inside the window), plus the module pairs. Written only for bots with a lease registry (genericbot).
		/// </summary>
		internal static void AppendOrderGate(StringBuilder builder, ModularBot bot)
		{
			if (bot == null)
				return;

			var g = bot.OrderGate;
			AppendObjectPropertyStart(builder, "order_gate");
			AppendNumber(builder, "refused", g.Refused, true);
			AppendNumber(builder, "preempted", g.Preempted);
			AppendNumber(builder, "conflicts", g.Conflicts);
			AppendNumber(builder, "crossed", g.Crossed);
			AppendNumber(builder, "unattributed", g.Unattributed);
			AppendNumber(builder, "dropped_full_queue", bot.DroppedOrders);
			AppendArrayPropertyStart(builder, "pairs");
			var i = 0;
			foreach (var ((issuer, holder, verdict), n) in g.Pairs.OrderByDescending(kv => kv.Value).ThenBy(kv => kv.Key.Issuer, StringComparer.Ordinal))
			{
				if (i++ > 0)
					builder.Append(',');

				AppendObjectStart(builder);
				AppendString(builder, "issuer", issuer ?? "", true);
				AppendString(builder, "holder", holder ?? "");
				AppendString(builder, "verdict", SnakeCase(verdict.ToString()));
				AppendNumber(builder, "orders", n);
				builder.Append('}');
			}

			builder.Append(']');
			AppendArrayPropertyStart(builder, "crossed_pairs");
			i = 0;
			foreach (var ((first, second), n) in g.CrossedPairs.OrderByDescending(kv => kv.Value).ThenBy(kv => kv.Key.First, StringComparer.Ordinal))
			{
				if (i++ > 0)
					builder.Append(',');

				AppendObjectStart(builder);
				AppendString(builder, "first", first, true);
				AppendString(builder, "then", second);
				AppendNumber(builder, "orders", n);
				builder.Append('}');
			}

			builder.Append("]}");
		}

		static string SnakeCase(string pascal) =>
			string.Concat(pascal.Select((c, i) => i > 0 && char.IsUpper(c) ? "_" + char.ToLowerInvariant(c) : char.ToLowerInvariant(c).ToString()));

		internal static void AppendArsenal(StringBuilder builder, BotArsenalLedger ledger, bool first = false)
		{
			AppendArrayPropertyStart(builder, "arsenal", first);
			if (ledger != null)
			{
				var i = 0;
				foreach (var (type, e) in ledger.Ordered())
				{
					if (i++ > 0)
						builder.Append(',');
					AppendObjectStart(builder);
					AppendString(builder, "type", type, true);
					AppendNumber(builder, "created", e.Created);
					AppendNumber(builder, "lost", e.Lost);
					AppendNumber(builder, "lost_value", e.LostValue);
					AppendNumber(builder, "killed_value", e.KilledValue);
					AppendObjectPropertyStart(builder, "killed_by_victim");
					var j = 0;
					foreach (var (victim, value) in e.KilledValueByVictim.OrderByDescending(kv => kv.Value).ThenBy(kv => kv.Key, StringComparer.Ordinal))
						AppendNumber(builder, victim, value, j++ == 0);
					builder.Append("}}");
				}
			}

			builder.Append(']');
		}

		internal const string StatsTimelineFields = "tick,earned,spent,army_value,assets_value,kills_cost,deaths_cost,banked,idle_queues";

		// Discipline telemetry (AI_DEEP_RESEARCH.md §13 item 1): player-level production queues that could build
		// something but have nothing queued. Humans leave factories idle; a strong bot should not. Building-level
		// queues (per-factory production) are not counted.
		static int IdleQueues(OpenRA.Player player)
		{
			var idle = 0;
			foreach (var q in player.PlayerActor.TraitsImplementing<ProductionQueue>())
				if (q.Enabled && !q.AllQueued().Any() && q.BuildableItems().Any())
					idle++;

			return idle;
		}

		internal static void AppendStatsTimeline(StringBuilder builder, IReadOnlyList<int[]> timeline, bool first = false)
		{
			AppendString(builder, "stats_timeline_fields", StatsTimelineFields, first);
			AppendArrayPropertyStart(builder, "stats_timeline");
			if (timeline != null)
				for (var i = 0; i < timeline.Count; i++)
				{
					if (i > 0)
						builder.Append(',');
					builder.Append('[').Append(string.Join(",", timeline[i].Select(v => v.ToString(CultureInfo.InvariantCulture)))).Append(']');
				}

			builder.Append(']');
		}

		static bool AllBotsResolved(World world)
		{
			return world.Players
				.Where(IsLoggableBot)
				.All(p => p.WinState != WinState.Undefined);
		}

		internal static bool Eligible(WorldType type, bool replay, bool loadingSave, bool host)
		{
			return type == WorldType.Regular && !replay && !loadingSave && host;
		}

		string BuildLog(World world)
		{
			var gameUid = world.LobbyInfo.GlobalSettings.GameUid;
			if (string.IsNullOrEmpty(gameUid))
				gameUid = fallbackGameUid;

			var lines = new StringBuilder();
			foreach (var player in world.Players.Where(IsLoggableBot))
			{
				var recorder = player.PlayerActor.TraitOrDefault<AiMatchLogRecorder>();
				var stats = player.PlayerActor.TraitOrDefault<PlayerStatistics>();
				var resources = player.PlayerActor.TraitOrDefault<PlayerResources>();
				var team = world.LobbyInfo.ClientWithIndex(player.ClientIndex)?.Team ?? 0;

				AppendObjectStart(lines);
				AppendNumber(lines, "schema", 2, true);
				AppendString(lines, "record_id", gameUid + "|" + player.InternalName);
				AppendString(lines, "recorded_utc", DateTime.UtcNow.ToString("o", CultureInfo.InvariantCulture));
				AppendString(lines, "mod_version", Game.ModData.Manifest.Metadata.Version);
				AppendString(lines, "game_uid", world.LobbyInfo.GlobalSettings.GameUid ?? "");
				AppendString(lines, "map_uid", world.Map.Uid);
				AppendString(lines, "map_title", world.Map.Title);
				AppendNumber(lines, "duration_ticks", world.WorldTick);
				AppendNumber(lines, "timestep", world.Timestep);

				AppendObjectPropertyStart(lines, "player");
				AppendString(lines, "name", player.InternalName, true);
				AppendString(lines, "bot_type", player.BotType);
				AppendString(lines, "faction", player.Faction.InternalName);
				AppendNumber(lines, "team", team);
				AppendNumber(lines, "handicap", player.Handicap);
				AppendNumber(lines, "spawn", player.SpawnPoint);

				// SpawnPoint is the lobby's choice and stays 0 for map-side players (the A/B harness),
				// so the home cell is what tells the two sides of a duel apart.
				AppendString(lines, "home", $"{player.HomeLocation.X},{player.HomeLocation.Y}");
				AppendString(lines, "outcome", Outcome(player.WinState));
				AppendString(lines, "personality", recorder?.CurrentPersonality ?? "");
				AppendNumber(lines, "personality_switches", recorder?.PersonalitySwitches ?? 0);
				AppendTimeline(lines, recorder?.PersonalityTimeline);
				AppendString(lines, "composition", recorder?.CurrentComposition ?? "");
				AppendNumber(lines, "composition_switches", recorder?.CompositionSwitches ?? 0);
				AppendCompositionTimeline(lines, recorder?.CompositionTimeline);
				AppendEpisodeTimeline(lines, recorder?.EpisodeTimeline);
				lines.Append('}');

				AppendObjectPropertyStart(lines, "stats");
				AppendNumber(lines, "units_killed", stats?.UnitsKilled ?? 0, true);
				AppendNumber(lines, "units_lost", stats?.UnitsDead ?? 0);
				AppendNumber(lines, "buildings_killed", stats?.BuildingsKilled ?? 0);
				AppendNumber(lines, "buildings_lost", stats?.BuildingsDead ?? 0);
				AppendNumber(lines, "kills_cost", stats?.KillsCost ?? 0);
				AppendNumber(lines, "deaths_cost", stats?.DeathsCost ?? 0);
				AppendNumber(lines, "army_value", stats?.ArmyValue ?? 0);
				AppendNumber(lines, "assets_value", stats?.AssetsValue ?? 0);
				AppendNumber(lines, "resources_earned", resources?.Earned ?? 0);
				AppendNumber(lines, "resources_spent", resources?.Spent ?? 0);
				samples.TryGetValue(player, out var timeline);
				AppendStatsTimeline(lines, timeline);
				lines.Append('}');

				AppendArsenal(lines, player.PlayerActor.TraitOrDefault<BotArsenalLedger>());
				AppendOwnership(lines, player.PlayerActor.TraitsImplementing<BotModules.BotOwnershipWatchdog>().FirstOrDefault(w => w.Passes > 0));
				if (OpenRA.Mods.CA.Traits.BotUnitLeases.Of(player) != null)
					AppendOrderGate(lines, player.PlayerActor.TraitsImplementing<ModularBot>().FirstOrDefault(b => b.IsEnabled));

				AppendRelationships(lines, world, player, "opponents", false);
				AppendRelationships(lines, world, player, "allies", true);
				lines.Append("}\n");
			}

			return lines.ToString();
		}

		static void AppendRelationships(StringBuilder builder, World world, OpenRA.Player subject, string property, bool allies, bool first = false)
		{
			AppendArrayPropertyStart(builder, property, first);
			// Evaluate stances from the masks assigned at world creation rather than
			// Player.IsAlliedWith: once the match resolves, decided players report
			// Spectating (WinState != Undefined) and IsAlliedWith short-circuits to
			// ally on non-mission maps, which would record every loser as an ally.
			var relationships = world.Players
				.Where(IsEligiblePlayer)
				.Where(p => p != subject && p.AlliedPlayersMask.Overlaps(subject.PlayerMask) == allies)
				.OrderBy(p => p.InternalName, StringComparer.Ordinal)
				.ToArray();

			for (var i = 0; i < relationships.Length; i++)
			{
				if (i > 0)
					builder.Append(',');

				var player = relationships[i];
				var team = world.LobbyInfo.ClientWithIndex(player.ClientIndex)?.Team ?? 0;
				AppendObjectStart(builder);
				AppendString(builder, "name", player.InternalName, true);
				AppendBoolean(builder, "is_bot", player.IsBot);
				AppendString(builder, "bot_type", player.BotType ?? "");
				AppendString(builder, "faction", player.Faction.InternalName);
				AppendNumber(builder, "team", team);
				AppendNumber(builder, "handicap", player.Handicap);
				AppendString(builder, "outcome", Outcome(player.WinState));
				builder.Append('}');
			}

			builder.Append(']');
		}

		internal static void AppendTimeline(StringBuilder builder, IReadOnlyList<AiMatchLogPersonalityTransition> timeline, bool first = false)
		{
			AppendArrayPropertyStart(builder, "personality_timeline", first);
			if (timeline != null)
				for (var i = 0; i < timeline.Count; i++)
				{
					if (i > 0)
						builder.Append(',');
					AppendObjectStart(builder);
					AppendNumber(builder, "tick", timeline[i].Tick, true);
					AppendString(builder, "personality", timeline[i].Personality);
					builder.Append('}');
				}

			builder.Append(']');
		}

		internal static void AppendCompositionTimeline(StringBuilder builder, IReadOnlyList<AiMatchLogCompositionTransition> timeline, bool first = false)
		{
			AppendArrayPropertyStart(builder, "composition_timeline", first);
			if (timeline != null)
				for (var i = 0; i < timeline.Count; i++)
				{
					if (i > 0)
						builder.Append(',');
					AppendObjectStart(builder);
					AppendNumber(builder, "tick", timeline[i].Tick, true);
					AppendString(builder, "composition", timeline[i].Composition);
					builder.Append('}');
				}

			builder.Append(']');
		}

		internal static void AppendEpisodeTimeline(StringBuilder builder, IReadOnlyList<AiMatchLogEpisodeTransition> timeline, bool first = false)
		{
			AppendArrayPropertyStart(builder, "episode_timeline", first);
			if (timeline != null)
				for (var i = 0; i < timeline.Count; i++)
				{
					if (i > 0)
						builder.Append(',');
					AppendObjectStart(builder);
					AppendNumber(builder, "tick", timeline[i].Tick, true);
					AppendString(builder, "personality", timeline[i].Personality);
					AppendString(builder, "composition", timeline[i].Composition);
					AppendNumber(builder, "kills_cost", timeline[i].KillsCost);
					AppendNumber(builder, "deaths_cost", timeline[i].DeathsCost);
					builder.Append('}');
				}

			builder.Append(']');
		}

		static bool IsEligiblePlayer(OpenRA.Player player)
		{
			// Player.NonCombatant only applies to map-side players: the lobby-client
			// branch of the Player ctor ignores it, so a map-declared inert slot
			// (e.g. the ai_duel referee) occupied by a real client keeps its intent
			// only in PlayerReference. Honor the declared flag here so such slots
			// never leak into opponents/allies and break the 1v1 contract.
			// Map-declared bots are never Playable (only lobby clients are), but a
			// headless bot-vs-bot match still fights real opponents, so IsBot
			// admits them where Playable cannot.
			return !player.NonCombatant && !player.PlayerReference.NonCombatant && (player.Playable || player.IsBot);
		}

		// Map-declared bots are real bot players even when they are not playable lobby slots.
		// Same declared-intent rule as IsEligiblePlayer: a lobby-occupied slot ignores
		// Player.NonCombatant, so PlayerReference.NonCombatant is what keeps an inert
		// bot slot (or a hypothetical declared-noncombatant bot) out of the log.
		internal static bool IsLoggableBot(OpenRA.Player player)
		{
			return player.IsBot && !player.NonCombatant && !player.PlayerReference.NonCombatant;
		}

		static string Outcome(WinState state)
		{
			return state switch
			{
				WinState.Won => "won",
				WinState.Lost => "lost",
				_ => "undecided"
			};
		}

		internal static void AppendObjectStart(StringBuilder builder) { builder.Append('{'); }

		internal static void AppendObjectPropertyStart(StringBuilder builder, string name, bool first = false)
		{
			if (!first)
				builder.Append(',');
			builder.Append('"').Append(name).Append("\":{");
		}

		internal static void AppendArrayPropertyStart(StringBuilder builder, string name, bool first = false)
		{
			if (!first)
				builder.Append(',');
			builder.Append('"').Append(name).Append("\":[");
		}

		internal static void AppendString(StringBuilder builder, string name, string value, bool first = false)
		{
			if (!first)
				builder.Append(',');
			builder.Append('"').Append(name).Append("\":\"");
			AppendEscaped(builder, value ?? "");
			builder.Append('"');
		}

		internal static void AppendNumber(StringBuilder builder, string name, int value, bool first = false)
		{
			if (!first)
				builder.Append(',');
			builder.Append('"').Append(name).Append("\":")
				.Append(value.ToString(CultureInfo.InvariantCulture));
		}

		internal static void AppendNumber(StringBuilder builder, string name, long value, bool first = false)
		{
			if (!first)
				builder.Append(',');
			builder.Append('"').Append(name).Append("\":")
				.Append(value.ToString(CultureInfo.InvariantCulture));
		}

		internal static void AppendNumber(StringBuilder builder, string name, double value, bool first = false)
		{
			if (!first)
				builder.Append(',');
			builder.Append('"').Append(name).Append("\":")
				.Append(value.ToString(CultureInfo.InvariantCulture));
		}

		internal static void AppendBoolean(StringBuilder builder, string name, bool value, bool first = false)
		{
			if (!first)
				builder.Append(',');
			builder.Append('"').Append(name).Append("\":")
				.Append(value ? "true" : "false");
		}

		static void AppendEscaped(StringBuilder builder, string value)
		{
			foreach (var c in value)
			{
				switch (c)
				{
					case '\\': builder.Append("\\\\"); break;
					case '"': builder.Append("\\\""); break;
					case '\b': builder.Append("\\b"); break;
					case '\f': builder.Append("\\f"); break;
					case '\n': builder.Append("\\n"); break;
					case '\r': builder.Append("\\r"); break;
					case '\t': builder.Append("\\t"); break;
					default:
						if (char.IsControl(c))
							builder.Append("\\u").Append(((int)c).ToString("x4", CultureInfo.InvariantCulture));
						else
							builder.Append(c);
						break;
				}
			}
		}
	}
}
