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
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.CA.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Activities
{
	class InfectCA : Enter
	{
		readonly AttackInfectCA infector;
		readonly AttackInfectCAInfo info;
		readonly Target target;

		bool jousting;

		public InfectCA(Actor self, Target target, AttackInfectCA infector, AttackInfectCAInfo info, Color? targetLineColor)
			: base(self, target, targetLineColor)
		{
			this.target = target;
			this.infector = infector;
			this.info = info;
			IsInterruptible = false;
		}

		protected override void OnFirstRun(Actor self)
		{
			infector.IsAiming = true;
		}

		protected override void OnLastRun(Actor self)
		{
			infector.IsAiming = false;
		}

		protected override void OnEnterComplete(Actor self, Actor targetActor)
		{
			self.World.AddFrameEndTask(w =>
			{
				if (infector.IsTraitDisabled)
					return;

				if (jousting)
				{
					jousting = false;
					infector.RevokeJoustCondition(self);
				}

				infector.DoAttack(self, target);

				var infectable = targetActor.TraitOrDefault<InfectableCA>();
				if (infectable == null || infectable.IsTraitDisabled || (infectable.Info.InfectorLimit > 0 && infectable.Infectors.Count >= infectable.Info.InfectorLimit))
					return;

				w.Remove(self);

				infectable.Infectors.Add(new InfectorCA(self, infector, info));
				infectable.RevokeInfectingCondition(targetActor, self);
				infectable.GrantCondition(targetActor, self);
			});
		}

		void CancelInfection(Actor self)
		{
			if (jousting)
			{
				jousting = false;
				infector.RevokeJoustCondition(self);
			}
			
			if (target.Type != TargetType.Actor)
				return;

			if (target.Actor.IsDead)
				return;

			var infectable = target.Actor.TraitOrDefault<InfectableCA>();
			if (infectable == null || infectable.IsTraitDisabled)
				return;

			infectable.RevokeInfectingCondition(target.Actor, self);
		}

		bool IsValidInfection(Actor self, Actor targetActor)
		{
			if (infector.IsTraitDisabled)
				return false;

			if (targetActor.IsDead)
				return false;

			if (!target.IsValidFor(self) || !infector.HasAnyValidWeapons(target))
				return false;

			var infectable = targetActor.TraitOrDefault<InfectableCA>();
			if (infectable == null || infectable.IsTraitDisabled || (infectable.Infectors.Count > 0))
				return false;

			return true;
		}

		bool CanStartInfect(Actor self, Actor targetActor)
		{
			if (!IsValidInfection(self, targetActor))
				return false;

			// IsValidInfection validated the lookup, no need to check here.
			var infectable = targetActor.Trait<InfectableCA>();
			return infectable.TryStartInfecting(targetActor, self);
		}

		protected override bool TryStartEnter(Actor self, Actor targetActor)
		{
			if (jousting)
			{
				infector.RevokeJoustCondition(self);
				jousting = false;
			}

			var canStartInfect = CanStartInfect(self, targetActor);
			if (canStartInfect == false)
			{
				CancelInfection(self);
				Cancel(self, true);
			}

			// Can't leap yet
			if (infector.Armaments.All(a => a.IsReloading))
				return false;

			return true;
		}

		protected override void TickInner(Actor self, in Target target, bool targetIsDeadOrHiddenActor)
		{
			if (target.Type != TargetType.Actor || !IsValidInfection(self, target.Actor))
			{
				CancelInfection(self);
				Cancel(self, true);
				return;
			}

			if (!jousting && !IsCanceling && (self.CenterPosition - target.CenterPosition).Length < info.JoustRange.Length)
			{
				jousting = true;
				infector.GrantJoustCondition(self);
			}
		}
	}
}
