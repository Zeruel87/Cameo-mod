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
using OpenRA.Mods.AS.Traits;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	[Desc("Handle infection by infector units.")]
	public class InfectableCAInfo : ConditionalTraitInfo, Requires<HealthInfo>
	{
		[Desc("Damage types that removes the infector.")]
		public readonly BitSet<DamageType> RemoveInfectorDamageTypes = default;

		[Desc("Damage types that kills the infector.")]
		public readonly BitSet<DamageType> KillInfectorDamageTypes = default;

		[Desc("Teleport types that removes the infector.")]
		public readonly HashSet<string> RemoveInfectorTeleportTypes = default;

		[GrantedConditionReference]
		[Desc("The condition to grant to self while infected by any actor.")]
		public readonly string InfectedCondition = null;

		[GrantedConditionReference]
		[Desc("Condition granted when being infected by another actor.")]
		public readonly string BeingInfectedCondition = null;

		[Desc("Conditions to grant when infected by specified actors.",
			"A dictionary of [actor id]: [condition].")]
		public readonly Dictionary<string, string> InfectedByConditions = new();

		[Desc("Up to how many infectors may infect this actor. Use 0 for unlimited")]
		public readonly int InfectorLimit = 0;

		[Desc("How many infectors should be affected by infector remove damage each time.")]
		public readonly int RemoveInfectorsCount = -1;

		[Desc("How many infectors should be affected by infector kill damage each time.")]
		public readonly int KillInfectorsCount = -1;

		[GrantedConditionReference]
		public IEnumerable<string> LinterConditions { get { return InfectedByConditions.Values; } }

		public override object Create(ActorInitializer init) { return new InfectableCA(init.Self, this); }
	}

	public class InfectorCA
	{
		public Actor actor;
		public AttackInfectCA infection;
		public AttackInfectCAInfo info;

		public int[] FirepowerMultipliers = Array.Empty<int>();

		public int dealtDamage = 0;
		public int suppressionCount = 0;

		public bool killInfectorOnDeath = false;

		[Sync]
		public int Ticks;

		public InfectorCA(Actor actor, AttackInfectCA infection, AttackInfectCAInfo info)
		{
			this.actor = actor;
			this.infection = infection;
			this.info = info;

			Ticks = info.DamageInterval;

			FirepowerMultipliers = actor.TraitsImplementing<IFirepowerModifier>()
					.Select(a => a.GetFirepowerModifier(null)).ToArray();
		}
	}

	public class InfectableCA : ConditionalTrait<InfectableCAInfo>, ISync, ITick, INotifyDamage, INotifyKilled, IRemoveInfector, IOnSuccessfulTeleportRA2
	{
		readonly Health health;
		readonly Actor self;

		public List<InfectorCA> Infectors = new();

		int beingInfectedToken = Actor.InvalidConditionToken;

		Stack<int> infectedTokens = new();
		Dictionary<string, Stack<int>> infectedByTokens = new();

		public InfectableCA(Actor self, InfectableCAInfo info)
			: base(info)
		{
			this.self = self;
			health = self.Trait<Health>();
		}

		public bool TryStartInfecting(Actor self, Actor infector)
		{
			if (infector != null)
			{
				if (beingInfectedToken == Actor.InvalidConditionToken && !string.IsNullOrEmpty(Info.BeingInfectedCondition))
					beingInfectedToken = self.GrantCondition(Info.BeingInfectedCondition);

				return true;
			}

			return false;
		}

		public void GrantCondition(Actor self, Actor Infector)
		{
			if (!string.IsNullOrEmpty(Info.InfectedCondition))
				infectedTokens.Push(self.GrantCondition(Info.InfectedCondition));

			if (Info.InfectedByConditions.TryGetValue(Infector.Info.Name, out var infectedByCondition))
				infectedByTokens.GetOrAdd(Infector.Info.Name).Push(self.GrantCondition(infectedByCondition));
		}

		public void RevokeInfectingCondition(Actor self, Actor infector)
		{
			if (self.IsDead)
				return;

			if (beingInfectedToken != Actor.InvalidConditionToken)
				beingInfectedToken = self.RevokeCondition(beingInfectedToken);
		}
		
		public void RevokeInfectedCondition(Actor self, Actor infector) {
			if (infectedTokens.Count > 0)
				self.RevokeCondition(infectedTokens.Pop());

			if (infectedByTokens.TryGetValue(infector.Info.Name, out var infectedByToken) && infectedByToken.Count > 0)
				self.RevokeCondition(infectedByToken.Pop());
		}

		void RemoveInfector(Actor self, InfectorCA Infector, bool kill, AttackInfo e)
		{
			if (Infector == null || Infector.actor.IsDead || Infector.actor.IsInWorld)
				return;

			Infector.actor.TraitOrDefault<IPositionable>().SetPosition(Infector.actor, self.CenterPosition);
			self.World.AddFrameEndTask(w =>
			{
				if (!Infector.actor.IsInWorld)
					w.Add(Infector.actor);

				if (kill)
				{
					if (e != null)
						Infector.actor.Kill(e.Attacker, e.Damage.DamageTypes);
					else
						Infector.actor.Kill(self);
				}
				else
				{
					Infector.actor.QueueActivity(false, new Nudge(Infector.actor));
				}

				RevokeInfectedCondition(self, Infector.actor);
				Infectors.Remove(Infector);
			});
		}

		void INotifyDamage.Damaged(Actor self, AttackInfo e)
		{
			if (Infectors.Count > 0)
			{
				var infectorsKilled = 0;
				var infectorsRemoved = 0;
				foreach (var Infector in Infectors) {
					if (e.Damage.DamageTypes.Overlaps(Info.KillInfectorDamageTypes) && (Info.KillInfectorsCount <= 0 || infectorsKilled < Info.KillInfectorsCount)) {
						RemoveInfector(self, Infector, true, e);
						++infectorsKilled;
					}
					else if (e.Damage.DamageTypes.Overlaps(Info.RemoveInfectorDamageTypes) && (Info.RemoveInfectorsCount <= 0 || infectorsRemoved < Info.RemoveInfectorsCount)) {
						RemoveInfector(self, Infector, false, e);
						++infectorsRemoved;
					}
					else if (e.Attacker != Infector.actor && e.Damage.DamageTypes.Overlaps(Infector.info.SuppressionDamageType))
					{
						Infector.killInfectorOnDeath |= Infector.info.SuppressionDamageThreshold > 0 && e.Damage.Value > Infector.info.SuppressionDamageThreshold;

						Infector.dealtDamage += e.Damage.Value;
						Infector.killInfectorOnDeath |= Infector.info.SuppressionSumThreshold > 0 && Infector.dealtDamage > Infector.info.SuppressionSumThreshold;

						Infector.suppressionCount++;
						Infector.killInfectorOnDeath |= Infector.info.SuppressionCountThreshold > 0 && Infector.suppressionCount > Infector.info.SuppressionCountThreshold;
					}
				}
			}
		}

		void INotifyKilled.Killed(Actor self, AttackInfo e)
		{
			if (Infectors.Count > 0)
			{
				foreach (var Infector in Infectors){
					var shdt = Infector.info.SurviveHostDamageTypes;
					var kill = Infector.killInfectorOnDeath || (shdt.Any() && !shdt.Overlaps(e.Damage.DamageTypes));
					RemoveInfector(self, Infector, kill, e);
				}
			}
		}

		void ITick.Tick(Actor self)
		{
			if (!IsTraitDisabled && Infectors.Count > 0)
			{
				foreach (var Infector in Infectors){
					if (--Infector.Ticks < 0)
					{
						var damage = Util.ApplyPercentageModifiers(Infector.info.Damage, Infector.FirepowerMultipliers);
						health.InflictDamage(self, Infector.actor, new Damage(damage, Infector.info.DamageTypes), false);

						Infector.Ticks = Infector.info.DamageInterval;
					}
				}
			}
		}

		void IRemoveInfector.RemoveInfector(Actor self, bool kill, AttackInfo e)
		{
			foreach (var Infector in Infectors)
				RemoveInfector(self, Infector, kill, e);
		}

		void IOnSuccessfulTeleportRA2.OnSuccessfulTeleport(string type, WPos oldPos, WPos newPos)
		{
			if (Info.RemoveInfectorTeleportTypes.Contains(type))
				foreach (var Infector in Infectors)
					RemoveInfector(self, Infector, false, null);
		}
	}
}
