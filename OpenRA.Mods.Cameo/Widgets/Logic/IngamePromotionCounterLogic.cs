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

using System.Globalization;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Primitives;
using OpenRA.Widgets;

namespace OpenRA.Mods.Cameo.Widgets.Logic
{
	public class IngamePromotionCounterLogic : ChromeLogic
	{
		[ObjectCreator.UseCtor]
		public IngamePromotionCounterLogic(Widget widget, ModData modData, World world)
		{
			var playerPromotions = world.LocalPlayer.PlayerActor.Trait<PlayerPromotions>();
			var promotion = widget.Get("PROMOTIONS");
			var promotionRank = widget.Get<LabelWithTooltipWidget>("PROMOTION_RANK");
			var promotionPoints = widget.Get<LabelWithTooltipWidget>("PROMOTION_POINTS");
			var promotionProgress = widget.Get<LabelWithTooltipWidget>("PROMOTION_PROGRESS");

			promotionRank.GetColor = () => playerPromotions.Points > 0 ? Color.Gold : Color.White;
			promotionRank.GetText = () => "Current Rank: " + playerPromotions.currentRank;

			promotionPoints.GetColor = () => playerPromotions.Points > 0 ? Color.Gold : Color.White;
			promotionPoints.GetText = () => "Promotion Points: " + playerPromotions.Points;

			promotionProgress.GetColor = () => playerPromotions.Points > 0 ? Color.Gold : Color.White;
			promotionProgress.GetText = () => playerPromotions.IsMaxLevel ? null : "Progress: " + playerPromotions.Experience + (playerPromotions.IsMaxLevel ? null : "/" + playerPromotions.nextLevelXpRequired);
		}
	}
}
