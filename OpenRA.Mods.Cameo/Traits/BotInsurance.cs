#region Copyright & License Information

/*
 * Copyright 2007-2020 The OpenRA Developers (see AUTHORS)
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */

#endregion

using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Grants a condition to this actor when the player has stored resources.")]
	public class BotInsuranceInfo : TraitInfo
	{
		[FieldLoader.Require]
		[GrantedConditionReference]
		[Desc("Condition to grant.")]
		public readonly string Condition = null;

		[Desc("Enable condition when the amount of Cash is greater than this.")]
		public readonly int Threshold = 1000;

		[Desc("Minimum Duration of Bot Player under Threshold until Insurance is active.")]
		public readonly int ThresholdDuration = 250;

		public override object Create(ActorInitializer init)
		{
			return new BotInsurance(this);
		}
	}

	public class BotInsurance : INotifyCreated, INotifyOwnerChanged, ITick
	{
		readonly BotInsuranceInfo info;
		PlayerResources playerResources;

		int conditionToken = Actor.InvalidConditionToken;

		[Sync]
		int ticks;

		public BotInsurance(BotInsuranceInfo info)
		{
			this.info = info;

			ticks = info.ThresholdDuration;
		}

		void INotifyCreated.Created(Actor self)
		{
			// Special case handling is required for the Player actor.
			// Created is called before Player.PlayerActor is assigned,
			// so we must query other player traits from self, knowing that
			// it refers to the same actor as self.Owner.PlayerActor
			var playerActor = self.Info.Name == "player" ? self : self.Owner.PlayerActor;
			playerResources = playerActor.Trait<PlayerResources>();
		}

		void INotifyOwnerChanged.OnOwnerChanged(Actor self, OpenRA.Player oldOwner, OpenRA.Player newOwner)
		{
			playerResources = newOwner.PlayerActor.Trait<PlayerResources>();
		}

		void ITick.Tick(Actor self)
		{
			if (playerResources.Cash >= info.Threshold)
			{
				ticks = info.ThresholdDuration;
			}
			else
			{
				--ticks;
			}

			if (string.IsNullOrEmpty(info.Condition))
				return;

			var enabled = (playerResources.GetCashAndResources() < info.Threshold && ticks < 0);
			if (enabled && conditionToken == Actor.InvalidConditionToken)
				conditionToken = self.GrantCondition(info.Condition);
			else if (!enabled && conditionToken != Actor.InvalidConditionToken)
				conditionToken = self.RevokeCondition(conditionToken);
		}
	}
}
