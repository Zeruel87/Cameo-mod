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
			"personality-steamroller"
		};

		public readonly string PersonalityPrefix = "personality-";

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);

			if (Conditions.Length == 0)
				throw new YamlException("Conditions must contain at least one personality.");

			if (Conditions.Any(c => !c.StartsWith(PersonalityPrefix, StringComparison.Ordinal)))
				throw new YamlException($"Every personality condition must start with '{PersonalityPrefix}'.");
		}

		public override object Create(ActorInitializer init) { return new BotPersonalityController(init.Self, this); }
	}

	public class BotPersonalityController : ConditionalTrait<BotPersonalityControllerInfo>, IResolveOrder
	{
		int personalityToken = Actor.InvalidConditionToken;

		public string CurrentPersonality { get; private set; } = "";

		public BotPersonalityController(Actor self, BotPersonalityControllerInfo info)
			: base(info) { }

		protected override void TraitEnabled(Actor self)
		{
			var condition = Info.Conditions.Random(self.World.SharedRandom);
			personalityToken = self.GrantCondition(condition);
			CurrentPersonality = PersonalityName(condition, Info.PersonalityPrefix);
		}

		protected override void TraitDisabled(Actor self)
		{
			if (personalityToken != Actor.InvalidConditionToken)
				personalityToken = self.RevokeCondition(personalityToken);

			CurrentPersonality = "";
		}

		void IResolveOrder.ResolveOrder(Actor self, Order order)
		{
			if (IsTraitDisabled || order.OrderString != "SetBotPersonality" || string.IsNullOrEmpty(order.TargetString))
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
