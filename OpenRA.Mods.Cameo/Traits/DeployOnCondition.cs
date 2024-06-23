#region Copyright & License Information
/*
 * Copyright 2015- OpenRA.Mods.AS Developers (see AUTHORS)
 * This file is a part of a third-party plugin for OpenRA, which is
 * free software. It is made available to you under the terms of the
 * GNU General Public License as published by the Free Software
 * Foundation. For more information, see COPYING.
 */
#endregion

using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	public class DeployOnConditionInfo : ConditionalTraitInfo
	{
		[ActorReference]
		public readonly string IntoActor = null;
		public readonly int ForceHealthPercentage = 0;
		public readonly bool SkipMakeAnims = true;

		public override object Create(ActorInitializer init) { return new DeployOnCondition(init, this); }
	}

	public class DeployOnCondition : ConditionalTrait<DeployOnConditionInfo>
	{
		public DeployOnCondition(ActorInitializer init, DeployOnConditionInfo info)
			: base(info) { }

		protected override void TraitEnabled(Actor self)
		{
			var trait = self.TraitOrDefault<GrantConditionOnDeploy>();
			if (trait != null && trait.DeployState == DeployState.Undeployed)
			{
				if (self.CurrentActivity == null)
					self.QueueActivity(new DeployForGrantedCondition(self, trait));
				else
					self.CurrentActivity.QueueChild(new DeployForGrantedCondition(self, trait));
				return;
			};
		}
	}
}
