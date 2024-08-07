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
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Graphics;
using System.Collections.Generic;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Grants a shield with its own health pool. Main health pool is unaffected by damage until the shield is broken.")]
	public class ShieldedCAInfo : PausableConditionalTraitInfo
	{
		[Desc("The strength of the shield (amount of damage it will absorb).")]
		public readonly int MaxStrength = 1000;

		[Desc("The strength of the shield (amount of damage it will absorb) in percentage of health.")]
		public readonly int MaxPercentageStrength = 0;

		[Desc("Strength of the shield when the trait is enabled.")]
		public readonly int InitialStrength = 1000;

		[Desc("The strength of the shield (amount of damage it will absorb).")]
		public readonly int InitialPercentageStrength = 0;

		[Desc("Delay in ticks before shield regenerate for the first time after trait is enabled.")]
		public readonly int InitialRegenDelay = 0;

		[Desc("Delay in ticks after absorbing damage before the shield will regenerate.")]
		public readonly int DamageRegenDelay = 0;

		[Desc("Amount to recharge at each interval.")]
		public readonly int RegenAmount = 0;

		[Desc("Number of ticks between recharging.")]
		public readonly int RegenInterval = 25;

		[Desc("Block the remaining damage after shield breaks.")]
		public readonly bool BlockExcessDamage = false;

		[Desc("Damage types that ignore this shield.")]
		public readonly BitSet<DamageType> IgnoreShieldDamageTypes = default;

		[GrantedConditionReference]
		[Desc("Condition to grant when shields are active.")]
		public readonly string ShieldsUpCondition = null;

		[Desc("Hides selection bar when shield is at max strength.")]
		public readonly bool HideBarWhenFull = false;

		public readonly bool ShowSelectionBar = true;
		public readonly Color SelectionBarColor = Color.FromArgb(128, 200, 255);

		public override object Create(ActorInitializer init) { return new ShieldedCA(init, this); }
	}

	public class ShieldedCA : PausableConditionalTrait<ShieldedCAInfo>, ITick, ISync, ISelectionBar, IDamageModifier, INotifyDamage
	{
		int conditionToken = Actor.InvalidConditionToken;
		readonly Actor self;
		readonly SpriteFont font;

		[Sync]
		public int Strength;
		public int maxStrength;
		int ticks;

		IHealth health;

		public ShieldedCA(ActorInitializer init, ShieldedCAInfo info)
			: base(info)
		{
			self = init.Self;
			font = Game.Renderer.Fonts["TinyBold"];
		}

		protected override void Created(Actor self)
		{
			base.Created(self);
			health = self.TraitOrDefault<IHealth>();
			maxStrength = Info.MaxStrength + Info.MaxPercentageStrength * health.MaxHP / 100;
			Strength = Info.InitialStrength + Info.InitialPercentageStrength * health.MaxHP / 100;
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

			if (Strength == maxStrength)
				return;

			if (--ticks > 0)
				return;

			Strength += Info.RegenAmount;

			if (Strength > maxStrength)
				Strength = maxStrength;

			if (Strength > 0 && conditionToken == Actor.InvalidConditionToken)
				conditionToken = self.GrantCondition(Info.ShieldsUpCondition);

			ticks = Info.RegenInterval;
		}

		public void Regenerate(Actor self, int amount)
		{
			if (IsTraitDisabled || IsTraitPaused)
				return;

			Strength += amount;

			if (Strength > 0 && conditionToken == Actor.InvalidConditionToken)
				conditionToken = self.GrantCondition(Info.ShieldsUpCondition);

			if (Strength <= 0 && conditionToken != Actor.InvalidConditionToken)
			{
				Strength = 0;
				conditionToken = self.RevokeCondition(conditionToken);
			}
		}

		void INotifyDamage.Damaged(Actor self, AttackInfo e)
		{
			if (IsTraitDisabled)
				return;

			if (Strength == 0 || e.Damage.Value == 0 || e.Attacker == self)
				return;

			if (e.Damage.Value < 0 || (!Info.IgnoreShieldDamageTypes.IsEmpty && e.Damage.DamageTypes.Overlaps(Info.IgnoreShieldDamageTypes)))
				return;

			if (ticks < Info.DamageRegenDelay)
				ticks = Info.DamageRegenDelay;

			var damageAmt = Convert.ToInt32(e.Damage.Value / 0.01);
			var damageTypes = e.Damage.DamageTypes;
			var excessDamage = damageAmt - Strength;
			Strength = Math.Max(Strength - damageAmt, 0);

			if (health != null)
			{
				var absorbedDamage = new Damage(-e.Damage.Value, damageTypes);
				health.InflictDamage(self, self, absorbedDamage, true);
			}

			if (Strength == 0 && conditionToken != Actor.InvalidConditionToken)
				conditionToken = self.RevokeCondition(conditionToken);

			if (excessDamage > 0 && !Info.BlockExcessDamage)
			{
				var hullDamage = new Damage(excessDamage, damageTypes);

				health?.InflictDamage(self, e.Attacker, hullDamage, true);
			}
		}

		float ISelectionBar.GetValue()
		{
			if (IsTraitDisabled || !Info.ShowSelectionBar || Strength == 0 || (Strength == maxStrength && Info.HideBarWhenFull))
				return 0;

			var selected = self.World.Selection.Contains(self);
			var rollover = self.World.Selection.RolloverContains(self);
			var regularWorld = self.World.Type == WorldType.Regular;
			var statusBars = Game.Settings.Game.StatusBars;

			var displayHealth = selected || rollover || (regularWorld && statusBars == StatusBarsType.AlwaysShow)
				|| (regularWorld && statusBars == StatusBarsType.DamageShow && Strength < maxStrength);

			if (!displayHealth)
				return 0;

			return (float)Strength / maxStrength;
		}

		bool ISelectionBar.DisplayWhenEmpty { get { return false; } }

		Color ISelectionBar.GetColor() { return Info.SelectionBarColor; }

		int IDamageModifier.GetDamageModifier(Actor attacker, Damage damage)
		{
			return IsTraitDisabled || Strength == 0 || (!Info.IgnoreShieldDamageTypes.IsEmpty && damage.DamageTypes.Overlaps(Info.IgnoreShieldDamageTypes)) ? 100 : 1;
		}

		protected override void TraitEnabled(Actor self)
		{
			ticks = Info.InitialRegenDelay;
			Strength = Info.InitialStrength;

			if (conditionToken == Actor.InvalidConditionToken && Strength > 0)
				conditionToken = self.GrantCondition(Info.ShieldsUpCondition);
		}

		protected override void TraitDisabled(Actor self)
		{
			if (conditionToken == Actor.InvalidConditionToken)
				return;

			conditionToken = self.RevokeCondition(conditionToken);
		}
	}
}
