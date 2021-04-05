#region Copyright & License Information
/*
 * Copyright 2015- OpenRA.Mods.AS Developers (see AUTHORS)
 * This file is a part of a third-party plugin for OpenRA, which is
 * free software. It is made available to you under the terms of the
 * GNU General Public License as published by the Free Software
 * Foundation. For more information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	[Flags]
	public enum DeployTriggers
	{
		None = 0,
		Attack = 1,
		Damage = 2,
		Heal = 4,
		Periodically = 8
	}

	[Desc("If this unit is owned by an AI, issue a deploy order automatically.")]
	public class AIDeployNotifierInfo : ConditionalTraitInfo
	{
		[Desc("Events leading to the actor getting uncloaked. Possible values are: None, Attack, Damage, Heal, Periodically.")]
		public readonly DeployTriggers DeployTrigger = DeployTriggers.Attack | DeployTriggers.Damage;

		[Desc("Chance of deploying when the trigger activates.")]
		public readonly int DeployChance = 50;

		[Desc("Delay between two successful deploy orders.")]
		public readonly int DeployTicks = 2500;

		[Desc("Delay to wait for the actor to undeploy (if capable to) after a successful deploy.")]
		public readonly int UndeployTicks = 450;

		public override object Create(ActorInitializer init) { return new AIDeployNotifier(this); }
	}

	// TO-DO: Pester OpenRA to allow INotifyDeployTrigger to be used for other traits besides WithMakeAnimation. Like this one.
	public class AIDeployNotifier : ConditionalTrait<AIDeployNotifierInfo>, INotifyAttack, ITick, INotifyDamage, INotifyCreated, ISync, INotifyOwnerChanged, INotifyDeployComplete
	{
		public const string PrimaryBuildingOrderID = "PrimaryProducer";

		[Sync]
		int undeployTicks = -1, deployTicks;

		bool deployed;
		public bool PrimaryBuilding;
		public IIssueDeployOrder[] DeployTraits;
		DeployBotModule deployBotModule;

		public AIDeployNotifier(AIDeployNotifierInfo info)
			: base(info) { }

		protected override void Created(Actor self)
		{
			DeployTraits = self.TraitsImplementing<IIssueDeployOrder>().ToArray();
			PrimaryBuilding = self.Info.HasTraitInfo<PrimaryBuildingInfo>();
			deployBotModule = self.Owner.PlayerActor.Trait<DeployBotModule>();
		}

		void TryDeploy(Actor self)
		{
			if (deployTicks > 0 || deployBotModule.IsTraitDisabled)
				return;

			deployBotModule.AddEntry(new TraitPair<AIDeployNotifier>(self, this));

			deployTicks = Info.DeployTicks;
			undeployTicks = Info.UndeployTicks;
		}

		void Undeploy(Actor self)
		{
			if (deployBotModule.IsTraitDisabled)
				return;

			deployBotModule.AddUndeployOrders(new Order("GrantConditionOnDeploy", self, false));
		}

		void INotifyAttack.Attacking(Actor self, Target target, Armament a, Barrel barrel)
		{
			if (IsTraitDisabled || !self.Owner.IsBot)
				return;

			if (Info.DeployTrigger.HasFlag(DeployTriggers.Attack))
				TryDeploy(self);
		}

		void INotifyAttack.PreparingAttack(Actor self, Target target, Armament a, Barrel barrel) { }

		void ITick.Tick(Actor self)
		{
			if (IsTraitDisabled || !self.Owner.IsBot)
				return;

			if (deployed)
			{
				if (--undeployTicks < 0)
				{
					Undeploy(self);
					deployed = false;
				}

				return;
			}

			if (--deployTicks < 0 && Info.DeployTrigger.HasFlag(DeployTriggers.Periodically))
				TryDeploy(self);
		}

		void INotifyDamage.Damaged(Actor self, AttackInfo e)
		{
			if (IsTraitDisabled || !self.Owner.IsBot)
				return;

			if (e.Damage.Value > 0 && Info.DeployTrigger.HasFlag(DeployTriggers.Damage))
				TryDeploy(self);

			if (e.Damage.Value < 0 && Info.DeployTrigger.HasFlag(DeployTriggers.Heal))
				TryDeploy(self);
		}

		void INotifyOwnerChanged.OnOwnerChanged(Actor self, Player oldOwner, Player newOwner)
		{
			deployBotModule = newOwner.PlayerActor.Trait<DeployBotModule>();
		}

		void INotifyDeployComplete.FinishedDeploy(Actor self)
		{
			deployed = true;
		}

		void INotifyDeployComplete.FinishedUndeploy(Actor self)
		{
			deployed = false;
		}
	}
}
