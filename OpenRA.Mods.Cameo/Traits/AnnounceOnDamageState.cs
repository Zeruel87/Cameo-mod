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
using OpenRA.Traits;
using OpenRA.Mods.Common.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Applies a condition to the actor at specified damage states.")]
	public class AnnounceOnDamageStateInfo : TraitInfo
	{
		[VoiceReference]
		[Desc("Voice to use when killing something.")]
		public readonly string Voice = "Feedback";

		[Desc("Chance of voice line to play.")]
		public readonly int Chance = 25;

		[Desc("Levels of damage at which to grant the condition.")]
		public readonly DamageState ValidDamageStates = DamageState.Heavy | DamageState.Critical;

		public override object Create(ActorInitializer init) { return new AnnounceOnDamageState(init.Self, this); }
	}

	public class AnnounceOnDamageState : INotifyDamageStateChanged
	{
		readonly AnnounceOnDamageStateInfo info;

		public AnnounceOnDamageState(Actor self, AnnounceOnDamageStateInfo info)
		{
			this.info = info;
		}

		void INotifyDamageStateChanged.DamageStateChanged(Actor self, AttackInfo e)
		{
			if (info.ValidDamageStates.HasFlag(e.DamageState)
				&& !info.ValidDamageStates.HasFlag(e.PreviousDamageState)
				&& self.World.LocalRandom.Next(0, 100) < info.Chance)
				self.PlayVoice(info.Voice);
		}
	}
}
