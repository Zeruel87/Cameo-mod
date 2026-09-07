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

	public class AiMatchLogRecorder : IObservesVariables
	{
		readonly AiMatchLogRecorderInfo info;
		readonly List<AiMatchLogPersonalityTransition> timeline = [];
		readonly List<string> activePersonalities = [];

		int personalitySwitches;

		public IReadOnlyList<AiMatchLogPersonalityTransition> PersonalityTimeline => timeline;
		public int PersonalitySwitches => personalitySwitches;
		public string CurrentPersonality => activePersonalities.Count > 0 ? activePersonalities[^1] : "";

		public AiMatchLogRecorder(AiMatchLogRecorderInfo info)
		{
			this.info = info;
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
				}
				else if (!enabled && active)
					activePersonalities.Remove(personality);
			}
		}
	}
}
