#region Copyright & License Information
/*
 * Copyright 2007-2018 The OpenRA Developers (see AUTHORS)
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.GameRules;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

using OpenRA.Mods.Common.Effects;

using OpenRA.Graphics;
using OpenRA.Mods.Common.Traits.Render;

namespace OpenRA.Mods.CA.Traits
{
	[Desc("Explodes a weapon at the actor's position when enabled."
		+ "Reload/BurstDelays are used as explosion intervals.")]
	public class CashTransferToAlliesInfo : PausableConditionalTraitInfo
	{
		[Desc("Duration between cash transfers.")]
		public readonly int ChargeDuration = 5;

		[Desc("Whether to show the cash tick indicators rising from the actor.")]
		public readonly bool ShowTicks = true;

		public override object Create(ActorInitializer init) { return new CashTransferToAllies(init.Self, this); }
	}

	class CashTransferToAllies : PausableConditionalTrait<PausableConditionalTraitInfo>, ITick
	{
		readonly CashTransferToAlliesInfo info;

		[Sync]
		int ticks;

		public CashTransferToAllies(Actor self, CashTransferToAlliesInfo info)
			: base(info)
		{
			this.info = info;

			ticks = info.ChargeDuration;
		}

		void ITick.Tick(Actor self)
		{
			if (IsTraitDisabled || IsTraitPaused)
				return;

			if (--ticks < 0)
			{
				ticks = info.ChargeDuration;

				var ownResources = self.Owner.PlayerActor.Trait<PlayerResources>();
				var allies = self.Owner.World.Players.Where(p => p.IsAlliedWith(self.Owner) && p != self.Owner && p.InternalName != "Everyone");

				if (allies.Count() == 0)
					return;

				foreach (var player in allies)
				{
					var allyResources = player.PlayerActor.Trait<PlayerResources>();
					var toTakeFromAlly = allyResources.Cash / (99 * allies.Count());
					allyResources.TakeCash(toTakeFromAlly);
					ownResources.GiveCash(toTakeFromAlly);
				}

				var toTake = ownResources.Cash / 100;
				var toGive = toTake / allies.Count();

				foreach (var player in allies)
				{
					var allyResources = player.PlayerActor.Trait<PlayerResources>();
					allyResources.GiveCash(toGive);
				}

				ownResources.TakeCash(toGive*allies.Count());
			
			}
		}
	}
}
