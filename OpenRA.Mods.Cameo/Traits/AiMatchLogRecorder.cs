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
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Records the player's bot personality timeline for the AI match log.")]
	public class AiMatchLogRecorderInfo : TraitInfo
	{
		[Desc("Conditions to observe as the bot's personality; the prefix is stripped in the log.")]
		public readonly string[] PersonalityConditions =
		{
			"personality-rush",
			"personality-turtle",
			"personality-tech",
			"personality-expansion",
			"personality-steamroller"
		};

		public readonly string PersonalityPrefix = "personality-";

		public override object Create(ActorInitializer init) { return new AiMatchLogRecorder(this); }
	}

	public readonly record struct AiMatchLogPersonalityTransition(int Tick, string Personality);
	public readonly record struct AiMatchLogCompositionTransition(int Tick, string Composition);

	// A boundary between two episodes: emitted whenever the personality OR the active
	// unit composition changes, carrying a cumulative kills/deaths cost snapshot so
	// the offline aggregator can attribute value destroyed vs lost per episode (the
	// §6.1 `outcome` unit of learning) instead of only per match.
	public readonly record struct AiMatchLogEpisodeTransition(int Tick, string Personality, string Composition, int KillsCost, int DeathsCost);

	public class AiMatchLogRecorder : IObservesVariables, INotifyCreated
	{
		readonly AiMatchLogRecorderInfo info;
		readonly List<AiMatchLogPersonalityTransition> timeline = [];
		readonly List<AiMatchLogCompositionTransition> compositionTimeline = [];
		readonly List<AiMatchLogEpisodeTransition> episodeTimeline = [];
		readonly List<string> activePersonalities = [];

		PlayerStatistics playerStats;
		string currentComposition = "";
		int personalitySwitches;
		int compositionSwitches;

		public IReadOnlyList<AiMatchLogPersonalityTransition> PersonalityTimeline => timeline;
		public IReadOnlyList<AiMatchLogCompositionTransition> CompositionTimeline => compositionTimeline;
		public IReadOnlyList<AiMatchLogEpisodeTransition> EpisodeTimeline => episodeTimeline;
		public int PersonalitySwitches => personalitySwitches;
		public int CompositionSwitches => compositionSwitches;
		public string CurrentPersonality => activePersonalities.Count > 0 ? activePersonalities[^1] : "";
		public string CurrentComposition => currentComposition;

		public AiMatchLogRecorder(AiMatchLogRecorderInfo info)
		{
			this.info = info;
		}

		void INotifyCreated.Created(Actor self)
		{
			playerStats = self.TraitOrDefault<PlayerStatistics>();
			var unitBuilder = self.TraitOrDefault<UnitBuilderBotModuleCA>();
			if (unitBuilder != null)
				unitBuilder.ActiveCompositionChanged += OnCompositionChanged;
		}

		void OnCompositionChanged(int tick, string composition)
		{
			if (composition == currentComposition)
				return;

			if (compositionTimeline.Count > 0)
				compositionSwitches++;

			currentComposition = composition;
			compositionTimeline.Add(new AiMatchLogCompositionTransition(tick, composition));
			if (compositionTimeline.Count > 64)
				compositionTimeline.RemoveRange(32, compositionTimeline.Count - 64);

			RecordEpisodeBoundary(tick);
		}

		void RecordEpisodeBoundary(int tick)
		{
			episodeTimeline.Add(new AiMatchLogEpisodeTransition(
				tick, CurrentPersonality, currentComposition,
				playerStats?.KillsCost ?? 0, playerStats?.DeathsCost ?? 0));
			if (episodeTimeline.Count > 128)
				episodeTimeline.RemoveRange(64, episodeTimeline.Count - 128);
		}

		IEnumerable<VariableObserver> IObservesVariables.GetVariableObservers()
		{
			yield return new VariableObserver(PersonalityConditionsChanged, info.PersonalityConditions);
		}

		void PersonalityConditionsChanged(Actor self, IReadOnlyDictionary<string, int> conditions)
		{
			foreach (var condition in info.PersonalityConditions)
			{
				var enabled = conditions.TryGetValue(condition, out var tokens) && tokens > 0;
				var personality = condition.StartsWith(info.PersonalityPrefix, System.StringComparison.Ordinal)
					? condition[info.PersonalityPrefix.Length..]
					: condition;
				var active = activePersonalities.Contains(personality);

				if (enabled && !active)
				{
					if (timeline.Count > 0)
						personalitySwitches++;

					timeline.Add(new AiMatchLogPersonalityTransition(self.World.WorldTick, personality));
					if (timeline.Count > 64)
						timeline.RemoveRange(32, timeline.Count - 64);

					activePersonalities.Add(personality);
					RecordEpisodeBoundary(self.World.WorldTick);
				}
				else if (!enabled && active)
					activePersonalities.Remove(personality);
			}
		}
	}
}
