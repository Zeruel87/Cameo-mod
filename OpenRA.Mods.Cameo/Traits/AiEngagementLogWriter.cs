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
using System.Text;
using OpenRA.Graphics;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.World)]
	[Desc("Appends the record-only AI engagement log (AI_ARCHITECTURE 12.30 EL-0, DESIGN 19.13): one line per closed fight and one",
		"per army posture sample.")]
	public class AiEngagementLogWriterInfo : TraitInfo
	{
		public readonly string FileName = "cameo-ai-engagements.jsonl";

		public override object Create(ActorInitializer init) { return new AiEngagementLogWriter(this); }
	}

	// Observer only: it never feeds a decision. The engagement module hands over finished lines; the file is appended at game over,
	// like the placement and situation logs, after every registered module has closed its open engagements (reason match_end).
	public class AiEngagementLogWriter : IWorldLoaded, IGameOver, ITick
	{
		readonly AiEngagementLogWriterInfo info;
		readonly StringBuilder lines = new();
		readonly List<Action<int>> flushers = new();
		AiLogFileAppender appender;
		bool written;
		bool flushing;
		int nextAttemptTick;

		/// <summary>False for replays, saved-game loads, non-hosts and non-regular worlds: the module then records nothing.</summary>
		public bool Active { get; private set; }

		public string FallbackGameUid { get; private set; }

		public AiEngagementLogWriter(AiEngagementLogWriterInfo info) { this.info = info; }

		public void RegisterFlush(Action<int> flush) => flushers.Add(flush);

		public void Append(string line)
		{
			if (Active && !written)
				lines.Append(line);
		}

		void IWorldLoaded.WorldLoaded(World world, WorldRenderer worldRenderer)
		{
			Active = AiMatchLogWriter.Eligible(world.Type, world.IsReplay, world.IsLoadingGameSave, Game.IsHost);
			if (!Active)
			{
				written = true;
				return;
			}

			FallbackGameUid = Guid.NewGuid().ToString("N");
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
			if (written || !Active || flushing)
				return;

			foreach (var flush in flushers)
				flush(world.WorldTick);

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
	}
}
