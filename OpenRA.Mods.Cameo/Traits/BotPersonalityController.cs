#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors.
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.GameRules;
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.Player)]
	public class BotPersonalityControllerInfo : ConditionalTraitInfo
	{
		public readonly string[] Conditions =
		{
			"personality-rush",
			"personality-turtle",
			"personality-tech",
			"personality-expansion",
			"personality-steamroller",
			"personality-guerrilla"
		};

		public readonly string PersonalityPrefix = "personality-";

		[Desc("Bot type -> personality pins for league-harness exploiters (AI_DEEP_RESEARCH §6.2). " +
			"A pinned bot always draws its pole at enable time and ignores SetBotPersonality orders " +
			"for any other personality, so the A/B harness can expose candidate flaws deterministically.")]
		public readonly Dictionary<string, string> PinnedPersonalities = null;

		// Declares the runtime-granted `personality-*` conditions to the yaml linter (see
		// BotCounterDemandController), so their consumers stop reading as "not granted".
		[GrantedConditionReference]
		public IEnumerable<string> LinterConditions => Conditions;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);

			if (Conditions.Length == 0)
				throw new YamlException("Conditions must contain at least one personality.");

			if (Conditions.Any(c => !c.StartsWith(PersonalityPrefix, StringComparison.Ordinal)))
				throw new YamlException($"Every personality condition must start with '{PersonalityPrefix}'.");

			if (PinnedPersonalities != null)
				foreach (var kv in PinnedPersonalities)
					if (!Conditions.Any(c => BotPersonalityController.PersonalityName(c, PersonalityPrefix) == kv.Value))
						throw new YamlException($"PinnedPersonalities[{kv.Key}] names '{kv.Value}', which has no matching personality-* condition.");
		}

		public override object Create(ActorInitializer init) { return new BotPersonalityController(init.Self, this); }
	}

	public class BotPersonalityController : ConditionalTrait<BotPersonalityControllerInfo>, IResolveOrder
	{
		int personalityToken = Actor.InvalidConditionToken;
		string pinnedTo;

		public string CurrentPersonality { get; private set; } = "";

		public BotPersonalityController(Actor self, BotPersonalityControllerInfo info)
			: base(info) { }

		internal static string PinnedPersonality(Dictionary<string, string> pins, string botType)
		{
			if (botType == null || pins == null)
				return null;

			return pins.TryGetValue(botType, out var pinned) ? pinned : null;
		}

		string PinnedPersonality(Actor self)
		{
			if (pinnedTo == null)
			{
				var botType = self.Owner.IsBot ? self.Owner.BotType : null;
				pinnedTo = PinnedPersonality(Info.PinnedPersonalities, botType) ?? "";
			}

			return pinnedTo.Length > 0 ? pinnedTo : null;
		}

		protected override void TraitEnabled(Actor self)
		{
			var pinned = PinnedPersonality(self);
			var condition = pinned != null
				? Info.Conditions.First(c => PersonalityName(c, Info.PersonalityPrefix) == pinned)
				: Info.Conditions.Random(self.World.SharedRandom);
			personalityToken = self.GrantCondition(condition);
			CurrentPersonality = PersonalityName(condition, Info.PersonalityPrefix);
		}

		protected override void TraitDisabled(Actor self)
		{
			if (personalityToken != Actor.InvalidConditionToken)
				personalityToken = self.RevokeCondition(personalityToken);

			CurrentPersonality = "";
			pinnedTo = null;
		}

		void IResolveOrder.ResolveOrder(Actor self, Order order)
		{
			if (IsTraitDisabled || order.OrderString != "SetBotPersonality" || string.IsNullOrEmpty(order.TargetString))
				return;

			if (PinnedPersonality(self) != null)
				return;

			var condition = Info.Conditions.FirstOrDefault(c => PersonalityName(c, Info.PersonalityPrefix) == order.TargetString);
			if (condition == null || PersonalityName(condition, Info.PersonalityPrefix) == CurrentPersonality)
				return;

			self.World.AddFrameEndTask(_ =>
			{
				if (IsTraitDisabled || PersonalityName(condition, Info.PersonalityPrefix) == CurrentPersonality)
					return;

				if (personalityToken != Actor.InvalidConditionToken)
					personalityToken = self.RevokeCondition(personalityToken);

				personalityToken = self.GrantCondition(condition);
				CurrentPersonality = PersonalityName(condition, Info.PersonalityPrefix);
			});
		}

		internal static string PersonalityName(string condition, string prefix)
		{
			return condition.StartsWith(prefix, StringComparison.Ordinal) ? condition[prefix.Length..] : "";
		}
	}
}
