#region Copyright & License Information
/*
 * Copyright 2015- OpenRA.Mods.AS Developers (see AUTHORS)
 * This file is a part of a third-party plugin for OpenRA, which is
 * free software. It is made available to you under the terms of the
 * GNU General Public License as published by the Free Software
 * Foundation. For more information, see COPYING.
 */
#endregion

using System.Linq;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Grant an external condition to the killer.")]
	public class GrantExternalConditionToTransportInfo : TraitInfo
	{
		[FieldLoader.Require]
		[Desc("The condition to apply. Must be included among the target actor's ExternalCondition traits.")]
		public readonly string Condition = null;

		public override object Create(ActorInitializer init) { return new GrantExternalConditionToTransport(this); }
	}

	public class GrantExternalConditionToTransport : INotifyEnteredCargo, INotifyExitedCargo, INotifyKilled
	{
		public readonly GrantExternalConditionToTransportInfo Info;
		int conditionToken = Actor.InvalidConditionToken;
		Actor Transport;
		ExternalCondition cargoConditionTrait;

		public GrantExternalConditionToTransport(GrantExternalConditionToTransportInfo info)
		{
			Info = info;
		}

		void INotifyEnteredCargo.OnEnteredCargo(Actor self, Actor cargo)
		{
			Transport = cargo;
			cargoConditionTrait = cargo.TraitsImplementing<ExternalCondition>()
				.FirstOrDefault(t => t.Info.Condition == Info.Condition && t.CanGrantCondition(self));

			if (cargoConditionTrait != null)
				conditionToken = cargoConditionTrait.GrantCondition(cargo, self);
		}

		void INotifyExitedCargo.OnExitedCargo(Actor self, Actor cargo)
		{
			if (conditionToken != Actor.InvalidConditionToken
				&& cargoConditionTrait.TryRevokeCondition(Transport, self, conditionToken))
			{
				conditionToken = Actor.InvalidConditionToken;
				Transport = null;
			}
		}

		void INotifyKilled.Killed(Actor self, AttackInfo e)
		{
			if (conditionToken != Actor.InvalidConditionToken
				&& cargoConditionTrait.TryRevokeCondition(Transport, self, conditionToken))
				conditionToken = Actor.InvalidConditionToken;
		}

	}
}
