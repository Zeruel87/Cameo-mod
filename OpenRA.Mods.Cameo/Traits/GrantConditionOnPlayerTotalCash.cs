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

using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Grants a condition to this actor when the player has total stored resources plus cash.")]
	public class GrantConditionOnPlayerTotalCashInfo : TraitInfo
	{
		[FieldLoader.Require]
		[GrantedConditionReference]
		[Desc("Condition to grant.")]
		public readonly string Condition = null;

		[Desc("Enable condition when the amount of total cash is greater than this.")]
		public readonly int Threshold = 0;

		public override object Create(ActorInitializer init) { return new GrantConditionOnPlayerTotalCash(this); }
	}

	public class GrantConditionOnPlayerTotalCash : INotifyCreated, INotifyOwnerChanged, ITick
	{
		readonly GrantConditionOnPlayerTotalCashInfo info;
		PlayerResources playerResources;

		int conditionToken = Actor.InvalidConditionToken;

		public GrantConditionOnPlayerTotalCash(GrantConditionOnPlayerTotalCashInfo info)
		{
			this.info = info;
		}

		void INotifyCreated.Created(Actor self)
		{
			playerResources = self.Owner.PlayerActor.Trait<PlayerResources>();
		}

		void INotifyOwnerChanged.OnOwnerChanged(Actor self, OpenRA.Player oldOwner, OpenRA.Player newOwner)
		{
			playerResources = newOwner.PlayerActor.Trait<PlayerResources>();
		}

		void ITick.Tick(Actor self)
		{
			if (string.IsNullOrEmpty(info.Condition))
				return;

			var enabled = playerResources.GetCashAndResources() > info.Threshold;
			if (enabled && conditionToken == Actor.InvalidConditionToken)
				conditionToken = self.GrantCondition(info.Condition);
			else if (!enabled && conditionToken != Actor.InvalidConditionToken)
				conditionToken = self.RevokeCondition(conditionToken);
		}
	}
}
