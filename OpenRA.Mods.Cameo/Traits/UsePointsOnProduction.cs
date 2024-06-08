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

using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Uses a promotion point when this actor produces a specific actor.")]
	public class UsePointsOnProductionInfo : TraitInfo
	{
		[ActorReference]
		[Desc("The actors to use points for. If empty condition will be used for all actors.")]
		public readonly HashSet<string> Actors = new();

		public override object Create(ActorInitializer init) { return new UsePointsOnProduction(this); }
	}

	public class UsePointsOnProduction : INotifyProduction, INotifyCreated
	{
		readonly UsePointsOnProductionInfo info;
		PlayerPromotions playerPromotions;

		public UsePointsOnProduction(UsePointsOnProductionInfo info)
		{
			this.info = info;
		}

		void INotifyCreated.Created(Actor self)
		{
			playerPromotions = self.Info.HasTraitInfo<PlayerPromotionsInfo>() ? self.Trait<PlayerPromotions>() : self.Owner.PlayerActor.Trait<PlayerPromotions>();
		}

		void INotifyProduction.UnitProduced(Actor self, Actor other, CPos exit)
		{
			if (info.Actors.Count > 0 && !info.Actors.Select(a => a.ToLowerInvariant()).Contains(other.Info.Name))
				return;

			playerPromotions.TakePoint(1);
		}
	}
}
