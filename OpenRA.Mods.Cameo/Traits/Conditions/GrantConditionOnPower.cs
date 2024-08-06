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

using OpenRA.Traits;
using OpenRA.Mods.Common.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Grants condition as long as a valid power level is maintained.")]
	public class GrantConditionOnPowerInfo : ConditionalTraitInfo
	{
		[FieldLoader.Require]
		[GrantedConditionReference]
		[Desc("Condition to grant.")]
		public readonly string Condition = null;

		[Desc("Amount of excess power to grant condition for.")]
		public readonly int Power = 0;

		public override object Create(ActorInitializer init) { return new GrantConditionOnPower(this); }
	}

	public class GrantConditionOnPower : ConditionalTrait<GrantConditionOnPowerInfo>, INotifyOwnerChanged, INotifyPowerAmountChanged
	{
		PowerManager playerPower;
		int conditionToken = Actor.InvalidConditionToken;

		bool validPowerState;

		public GrantConditionOnPower(GrantConditionOnPowerInfo info)
			: base(info) { }

		protected override void Created(Actor self)
		{
			playerPower = self.Owner.PlayerActor.Trait<PowerManager>();

			base.Created(self);

			Update(self);
		}

		protected override void TraitEnabled(Actor self)
		{
			Update(self);
		}

		protected override void TraitDisabled(Actor self)
		{
			Update(self);
		}

		void Update(Actor self)
		{
			validPowerState = !IsTraitDisabled && playerPower.ExcessPower >= Info.Power;

			if (validPowerState && conditionToken == Actor.InvalidConditionToken)
				conditionToken = self.GrantCondition(Info.Condition);
			else if (!validPowerState && conditionToken != Actor.InvalidConditionToken)
				conditionToken = self.RevokeCondition(conditionToken);
		}

		void INotifyPowerAmountChanged.PowerLevelChanged(Actor self)
		{
			Update(self);
		}

		void INotifyOwnerChanged.OnOwnerChanged(Actor self, OpenRA.Player oldOwner, OpenRA.Player newOwner)
		{
			playerPower = newOwner.PlayerActor.Trait<PowerManager>();
			Update(self);
		}
	}
}
