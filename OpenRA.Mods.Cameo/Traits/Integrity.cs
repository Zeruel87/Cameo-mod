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

using System;
using OpenRA.Mods.AS.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Grants a shield with its own health pool. Main health pool is unaffected by damage until the shield is broken.")]
	public class IntegrityInfo : PausableConditionalTraitInfo
	{
		[Desc("The strength of the shield (amount of damage it will absorb).")]
		public readonly int MaxStrength = 0;

		[Desc("The strength of the shield (amount of damage it will absorb) in percentage of health.")]
		public readonly int MaxPercentageStrength = 100;

		[Desc("Strength of the shield when the trait is enabled.")]
		public readonly int InitialStrength = 0;

		[Desc("The strength of the shield (amount of damage it will absorb).")]
		public readonly int InitialPercentageStrength = 100;

		[Desc("Delay in ticks before shield regenerate for the first time after trait is enabled.")]
		public readonly int InitialRegenDelay = 0;

		[Desc("Delay in ticks after absorbing damage before the shield will regenerate.")]
		public readonly int DamageRegenDelay = 0;

		[Desc("Amount to recharge at each interval.")]
		public readonly int RegenAmount = 0;

		[Desc("Amount to recharge at each interval.")]
		public readonly int PercentageRegenAmount = 1;

		[Desc("Number of ticks between recharging.")]
		public readonly int RegenInterval = 25;

		[Desc("Damage types that affect this shield.")]
		public readonly BitSet<DamageType> AffectedByDamageTypes = default;

		[GrantedConditionReference]
		[Desc("Condition to grant when shields are active.")]
		public readonly string ActiveCondition = null;

		[Desc("Hides selection bar when shield is at max strength.")]
		public readonly bool HideBarWhenFull = true;

		public readonly bool ShowSelectionBar = true;
		public readonly Color SelectionBarColor = Color.FromArgb(0, 148, 128);
		public readonly Color DisabledSelectionBarColor = Color.FromArgb(173, 216, 230);

		public override object Create(ActorInitializer init) { return new Integrity(init, this); }
	}

	public class Integrity : PausableConditionalTrait<IntegrityInfo>, ITick, ISync, ISelectionBar, INotifyDamage
	{
		int conditionToken = Actor.InvalidConditionToken;
		readonly Actor self;

		[Sync]
		public int Strength;
		public int MaxStrength;
		int ticks;

		IHealth health;

		public Integrity(ActorInitializer init, IntegrityInfo info)
			: base(info)
		{
			self = init.Self;
		}

		protected override void Created(Actor self)
		{
			base.Created(self);
			health = self.TraitOrDefault<IHealth>();
			MaxStrength = Info.MaxStrength + Info.MaxPercentageStrength * health.MaxHP / 100;
			Strength = Info.InitialStrength + Info.InitialPercentageStrength * health.MaxHP / 100;
			if (Strength > 0 && conditionToken == Actor.InvalidConditionToken)
				conditionToken = self.GrantCondition(Info.ActiveCondition);
			ticks = Info.InitialRegenDelay;
		}

		void ITick.Tick(Actor self)
		{
			Regenerate(self);
		}

		protected void Regenerate(Actor self)
		{
			if (IsTraitDisabled || IsTraitPaused)
				return;

			if (Strength == MaxStrength)
				return;

			if (--ticks > 0)
				return;

			Strength += Info.RegenAmount + (Info.PercentageRegenAmount * MaxStrength / 100);

			if (Strength > MaxStrength)
				Strength = MaxStrength;

			if (Strength <= -MaxStrength)
				Strength = -MaxStrength;

			if (Strength > 0 && conditionToken == Actor.InvalidConditionToken)
				conditionToken = self.GrantCondition(Info.ActiveCondition);

			ticks = Info.RegenInterval;
		}

		public void Regenerate(Actor self, int amount)
		{
			if (IsTraitDisabled || IsTraitPaused)
				return;

			if (amount < 0 && ticks < Info.DamageRegenDelay)
				ticks = Info.DamageRegenDelay;

			Strength += amount;

			if (Strength > 0 && conditionToken == Actor.InvalidConditionToken)
				conditionToken = self.GrantCondition(Info.ActiveCondition);

			if (Strength <= 0 && conditionToken != Actor.InvalidConditionToken)
				conditionToken = self.RevokeCondition(conditionToken);

			if (Strength <= -MaxStrength)
				Strength = -MaxStrength;
		}

		void INotifyDamage.Damaged(Actor self, AttackInfo e)
		{
			if (IsTraitDisabled)
				return;

			if (e.Damage.Value == 0 || e.Attacker == self)
				return;

			if (e.Damage.Value < 0 || (!Info.AffectedByDamageTypes.IsEmpty && !e.Damage.DamageTypes.Overlaps(Info.AffectedByDamageTypes)))
				return;

			if (ticks < Info.DamageRegenDelay)
				ticks = Info.DamageRegenDelay;

			var damageAmt = Convert.ToInt32(e.Damage.Value);
			Strength -= damageAmt;

			if (Strength <= 0 && conditionToken != Actor.InvalidConditionToken)
				conditionToken = self.RevokeCondition(conditionToken);

			if (Strength <= -MaxStrength)
				Strength = -MaxStrength;
		}

		float ISelectionBar.GetValue()
		{
			if (IsTraitDisabled || !Info.ShowSelectionBar || Strength == 0 || (Strength == MaxStrength && Info.HideBarWhenFull))
				return 0;

			var selected = self.World.Selection.Contains(self);
			var rollover = self.World.Selection.RolloverContains(self);
			var regularWorld = self.World.Type == WorldType.Regular;
			var statusBars = Game.Settings.Game.StatusBars;

			var displayHealth = selected || rollover || (regularWorld && statusBars == StatusBarsType.AlwaysShow)
				|| (regularWorld && statusBars == StatusBarsType.DamageShow && Strength < MaxStrength);

			if (!displayHealth)
				return 0;

			return Math.Abs((float)Strength / MaxStrength);
		}

		bool ISelectionBar.DisplayWhenEmpty { get { return false; } }

		Color ISelectionBar.GetColor() { return Strength > 0 ? Info.SelectionBarColor : Info.DisabledSelectionBarColor; }

		protected override void TraitEnabled(Actor self)
		{
			ticks = Info.InitialRegenDelay;
			Strength = Info.InitialStrength;

			if (conditionToken == Actor.InvalidConditionToken && Strength > 0)
				conditionToken = self.GrantCondition(Info.ActiveCondition);
		}

		protected override void TraitDisabled(Actor self)
		{
			if (conditionToken == Actor.InvalidConditionToken)
				return;

			conditionToken = self.RevokeCondition(conditionToken);
		}
	}
}
