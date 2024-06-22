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
using System.Collections.Generic;
using OpenRA.Mods.Common.Orders;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Cameo.Activities;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	public class InfectorOldInfo : ConditionalTraitInfo
	{
		public readonly string Name = "primary";

		[Desc("Name of the armaments that trigger infection.")]
		public readonly HashSet<string> ArmamentNames = new() { "primary" };

		[FieldLoader.Require]
		[Desc("How much damage to deal.")]
		public readonly int Damage;

		[FieldLoader.Require]
		[Desc("How often to deal the damage.")]
		public readonly int DamageInterval;

		[Desc("Sounds to play when damage is dealt.")]
		public readonly string[] DamageSounds = Array.Empty<string>();

		[Desc("Do the sounds play under shroud or fog.")]
		public readonly bool AudibleThroughFog = false;

		[Desc("Volume the sounds played at.")]
		public readonly float Volume = 1f;

		[Desc("If more than this outside damage is dealt to infected unit while this actor is in, it is killed when infected unit dies.",
			"Use -1 to never kill the actor.")]
		public readonly int SuppressionDamageThreshold = -1;

		[Desc("If more than this many times outside damage with enough is dealt SuppressionDamageThreshold to infected unit while this actor is in, it is killed when infected unit dies.",
			"Use -1 to never kill the actor.")]
		public readonly int SuppressionAmountThreshold = 1;

		[Desc("If the infected actor enters this damage state, kill the actor.")]
		public readonly DamageState[] KillState = Array.Empty<DamageState>();

		[Desc("Damage types for the infection damage.")]
		public readonly BitSet<DamageType> DamageTypes = default;

		[SequenceReference]
		[Desc("Sequence to use upon infection beginning.")]
		public readonly string StartSequence = null;

		[SequenceReference]
		[Desc("Sequence name to play during infection.")]
		public readonly string Sequence = null;

		[PaletteReference(nameof(IsPlayerPalette))]
		[Desc("Custom palette name")]
		public readonly string Palette = null;

		[Desc("Custom palette is a player palette BaseName")]
		public readonly bool IsPlayerPalette = false;

		[GrantedConditionReference]
		[Desc("The condition to grant to self while infecting any actor.")]
		public readonly string InfectingCondition = null;

		public override object Create(ActorInitializer init) { return new InfectorOld(this); }
	}

	public class InfectorOld : ConditionalTrait<InfectorOldInfo>, INotifyAttack
	{
		int token = Actor.InvalidConditionToken;

		public InfectorOld(InfectorOldInfo info)
			: base(info) { }

		public void GrantCondition(Actor self)
		{
			if (token == Actor.InvalidConditionToken && !string.IsNullOrEmpty(Info.InfectingCondition))
				token = self.GrantCondition(Info.InfectingCondition);
		}

		public void RevokeCondition(Actor self)
		{
			if (token != Actor.InvalidConditionToken)
				token = self.RevokeCondition(token);
		}

		void INotifyAttack.Attacking(Actor self, in Target target, Armament a, Barrel barrel)
		{
			if (!Info.ArmamentNames.Contains(a.Info.Name))
				return;

			if (IsTraitDisabled)
				return;

			self.CancelActivity();

			self.QueueActivity(new InfectOld(self, target, this));
			self.ShowTargetLines();
		}

		void INotifyAttack.PreparingAttack(Actor self, in Target target, Armament a, Barrel barrel) { }
	}
}
