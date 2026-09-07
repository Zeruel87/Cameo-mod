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
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
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

		public override object Create(ActorInitializer init) { return new AiMatchLogWriter(this); }
	}

	public class AiMatchLogWriter : IWorldLoaded, IGameOver, ITick
	{
		enum AppendResult { Appended, RetryableFailure, Failed }

		readonly AiMatchLogWriterInfo info;

		string fallbackGameUid;
		string pendingText;
		string filePath;
		string mutexName;
		bool written;
		bool eligibleAtWorldLoad;
		int attempts;
		int nextAttemptTick;

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
			filePath = Path.Combine(Platform.SupportDir, "Logs", info.FileName);
			var canonicalPath = Path.GetFullPath(filePath);
			if (OperatingSystem.IsWindows())
				canonicalPath = canonicalPath.ToUpperInvariant();

			mutexName = "OpenRA-CameoAiMatchLog-" + Convert.ToHexString(
				SHA256.HashData(Encoding.UTF8.GetBytes(canonicalPath)));
		}

		void ITick.Tick(Actor self)
		{
			var world = self.World;
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
			attempts++;
			var result = Append(pendingText);
			if (result != AppendResult.RetryableFailure || attempts >= 8)
			{
				written = true;
				return;
			}

			nextAttemptTick = worldTick + Math.Min(1 << Math.Min(attempts - 1, 5), 30);
		}

		AppendResult Append(string text)
		{
			Mutex mutex = null;
			try
			{
				mutex = new Mutex(false, mutexName);
				try
				{
					if (!mutex.WaitOne(TimeSpan.FromMilliseconds(100)))
						return AppendResult.RetryableFailure;
				}
				catch (AbandonedMutexException)
				{
				}

				try
				{
					Directory.CreateDirectory(Path.GetDirectoryName(filePath));
					File.AppendAllText(filePath, text, new UTF8Encoding(false));
					return AppendResult.Appended;
				}
				catch
				{
					return AppendResult.Failed;
				}
				finally
				{
					try { mutex.ReleaseMutex(); }
					catch { }
				}
			}
			catch
			{
				return AppendResult.Failed;
			}
			finally
			{
				mutex?.Dispose();
			}
		}

		static bool AllBotsResolved(World world)
		{
			return world.Players
				.Where(IsEligiblePlayer)
				.Where(p => p.IsBot)
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
			foreach (var player in world.Players.Where(p => p.IsBot && IsEligiblePlayer(p)))
			{
				var recorder = player.PlayerActor.TraitOrDefault<AiMatchLogRecorder>();
				var stats = player.PlayerActor.TraitOrDefault<PlayerStatistics>();
				var resources = player.PlayerActor.TraitOrDefault<PlayerResources>();
				var team = world.LobbyInfo.ClientWithIndex(player.ClientIndex)?.Team ?? 0;

				AppendObjectStart(lines);
				AppendNumber(lines, "schema", 1, true);
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
				AppendString(lines, "outcome", Outcome(player.WinState));
				AppendString(lines, "personality", recorder?.CurrentPersonality ?? "");
				AppendNumber(lines, "personality_switches", recorder?.PersonalitySwitches ?? 0);
				AppendTimeline(lines, recorder?.PersonalityTimeline);
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
				lines.Append('}');

				AppendRelationships(lines, world, player, "opponents", false);
				AppendRelationships(lines, world, player, "allies", true);
				lines.Append("}\n");
			}

			return lines.ToString();
		}

		static void AppendRelationships(StringBuilder builder, World world, OpenRA.Player subject, string property, bool allies, bool first = false)
		{
			if (!first)
				builder.Append(',');
			builder.Append('"').Append(property).Append("\":[");
			var relationships = world.Players
				.Where(IsEligiblePlayer)
				.Where(p => p != subject && p.IsAlliedWith(subject) == allies)
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
			if (!first)
				builder.Append(',');
			builder.Append("\"personality_timeline\":[");
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

		static bool IsEligiblePlayer(OpenRA.Player player)
		{
			return !player.NonCombatant && player.Playable;
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
