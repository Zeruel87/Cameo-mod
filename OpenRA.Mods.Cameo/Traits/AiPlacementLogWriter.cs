#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available under the terms of the GNU General Public License
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
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Cameo.Traits.BotModules;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.World)]
	[Desc("Appends the record-only AI placement / build-order log (AI_ARCHITECTURE 12.24 FE-0, 12.25 BO-0): one line per building a bot places.")]
	public class AiPlacementLogWriterInfo : TraitInfo
	{
		public readonly string FileName = "cameo-ai-placements.jsonl";

		public override object Create(ActorInitializer init) { return new AiPlacementLogWriter(this); }
	}

	// Observer only: it never feeds a decision. The base builder calls BuildingPlaced when it issues the placement order; the line
	// is built at once (the personality and the anchors are those of that moment) and appended at game over, like the situation log.
	public class AiPlacementLogWriter : IWorldLoaded, IGameOver, ITick, IBotPlacementObserver
	{
		readonly AiPlacementLogWriterInfo info;
		readonly StringBuilder lines = new();
		IReadOnlyDictionary<string, HashSet<string>> tagMap;
		string fallbackGameUid;
		AiLogFileAppender appender;
		bool written;
		bool eligibleAtWorldLoad;
		bool flushing;
		int nextAttemptTick;
		World world;

		public AiPlacementLogWriter(AiPlacementLogWriterInfo info) { this.info = info; }

		void IWorldLoaded.WorldLoaded(World world, WorldRenderer worldRenderer)
		{
			this.world = world;
			eligibleAtWorldLoad = AiMatchLogWriter.Eligible(world.Type, world.IsReplay, world.IsLoadingGameSave, Game.IsHost);
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
			if (written || !flushing || self.World.WorldTick < nextAttemptTick)
				return;

			TryAppend(self.World.WorldTick);
		}

		void IGameOver.GameOver(World world)
		{
			if (written || !eligibleAtWorldLoad)
				return;

			flushing = true;
			TryAppend(world.WorldTick);
		}

		void TryAppend(int worldTick)
		{
			if (lines.Length == 0)
			{
				written = true;
				return;
			}

			var result = appender.TryAppend(lines.ToString(), worldTick, out nextAttemptTick);
			if (result != AiLogAppendResult.RetryableFailure || appender.IsTerminal)
				written = true;
		}

		void IBotPlacementObserver.BuildingPlaced(OpenRA.Player owner, int tick, string actor, CPos cell, string reason, int queuedTick)
		{
			if (written || !eligibleAtWorldLoad || !AiMatchLogWriter.IsLoggableBot(owner))
				return;

			var gameUid = world.LobbyInfo.GlobalSettings.GameUid;
			if (string.IsNullOrEmpty(gameUid))
				gameUid = fallbackGameUid;

			tagMap ??= BotTargetTags.BuildTagMap(world.Map.Rules);
			tagMap.TryGetValue(actor, out var tags);
			var roles = owner.PlayerActor.TraitsImplementing<IBotUnitRoles>().FirstEnabledTraitOrDefault()?.ActorRoles;
			HashSet<string> actorRoles = null;
			roles?.TryGetValue(actor, out actorRoles);
			var category = ExpansionMath.Category(tags, actorRoles);

			var personality = owner.PlayerActor.TraitOrDefault<BotPersonalityController>()?.CurrentPersonality
				?? owner.PlayerActor.TraitOrDefault<AiMatchLogRecorder>()?.CurrentPersonality ?? "";

			var builder = lines;
			AiMatchLogWriter.AppendObjectStart(builder);
			AiMatchLogWriter.AppendNumber(builder, "schema", 1, true);
			AiMatchLogWriter.AppendString(builder, "kind", "placement");
			AiMatchLogWriter.AppendString(builder, "game_uid", world.LobbyInfo.GlobalSettings.GameUid ?? "");
			AiMatchLogWriter.AppendString(builder, "record_id", gameUid + "|" + owner.InternalName + "|" + tick + "|" + actor + "|" + cell.X + "," + cell.Y);
			AiMatchLogWriter.AppendString(builder, "map_uid", world.Map.Uid);
			AiMatchLogWriter.AppendNumber(builder, "seed", world.LobbyInfo.GlobalSettings.RandomSeed);
			AiMatchLogWriter.AppendString(builder, "player", owner.InternalName);
			AiMatchLogWriter.AppendString(builder, "faction", owner.Faction.InternalName);
			AiMatchLogWriter.AppendString(builder, "bot_type", owner.BotType ?? "");
			AiMatchLogWriter.AppendString(builder, "personality", personality);
			AiMatchLogWriter.AppendNumber(builder, "tick", tick);
			AiMatchLogWriter.AppendNumber(builder, "queued_tick", queuedTick);
			AiMatchLogWriter.AppendNumber(builder, "placed_tick", tick);
			AiMatchLogWriter.AppendString(builder, "actor", actor);
			AiMatchLogWriter.AppendString(builder, "cell", cell.X.ToString(CultureInfo.InvariantCulture) + "," + cell.Y.ToString(CultureInfo.InvariantCulture));
			AiMatchLogWriter.AppendString(builder, "category", category);
			AiMatchLogWriter.AppendString(builder, "reason", reason);

			// Refineries: the nearest anchor (a spreader, else the centre of a spreaderless field) and the distance in cells.
			if (category == "refinery")
			{
				var telemetry = owner.PlayerActor.TraitsImplementing<MasterAiBotModule>().FirstOrDefault()?.ExpansionTelemetry;
				if (telemetry != null)
				{
					var (index, anchor, spreader, distance) = telemetry.NearestAnchor(owner, cell);
					if (index >= 0)
					{
						AiMatchLogWriter.AppendString(builder, "anchor_kind", spreader ? "spreader" : "field");
						AiMatchLogWriter.AppendString(builder, "anchor_cell", anchor.X + "," + anchor.Y);
						AiMatchLogWriter.AppendNumber(builder, "anchor_dist", Math.Round(distance, 1));
					}
				}
			}

			builder.Append("}\n");
		}
	}
}
