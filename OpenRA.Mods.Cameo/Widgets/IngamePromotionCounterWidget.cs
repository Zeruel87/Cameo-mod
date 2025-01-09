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

using OpenRA.Graphics;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Primitives;
using OpenRA.Widgets;

namespace OpenRA.Mods.Cameo.Widgets
{
	public class IngamePromotionCounterWidget : Widget
	{
		[FluentReference]
		const string RankText = "promotion-counter.rank";

		[FluentReference]
		const string PointsText = "promotion-counter.points";

		[FluentReference]
		const string ProgressText = "promotion-counter.progress";

		public readonly string Font = "Bold";
		public readonly TextAlign Align = TextAlign.Right;

		readonly SpriteFont font;
		readonly Color bgDark, bgLight;

		string[] Texts;
		Color textColor;

		readonly Color playerColor;
		readonly PlayerPromotions playerPromotions;

		[ObjectCreator.UseCtor]
		public IngamePromotionCounterWidget(World world)
		{
			playerPromotions = world.LocalPlayer.PlayerActor.Trait<PlayerPromotions>();
			playerColor = world.LocalPlayer.Color;

			bgDark = ChromeMetrics.Get<Color>("TextContrastColorDark");
			bgLight = ChromeMetrics.Get<Color>("TextContrastColorLight");
			font = Game.Renderer.Fonts[Font];
		}

		public override void Tick()
		{
			var rankText = FluentProvider.GetMessage(RankText) + " " + playerPromotions.currentRank;
			var pointsText = FluentProvider.GetMessage(PointsText) + " " + playerPromotions.Points;
			var progressText = playerPromotions.IsMaxLevel ? "" : FluentProvider.GetMessage(ProgressText) + " " + playerPromotions.Experience + (playerPromotions.IsMaxLevel ? null : "/" + playerPromotions.nextLevelXpRequired);

			Texts = new string[] { rankText, pointsText, progressText };

			textColor = playerPromotions.Points > 0 && Game.LocalTick % 50 < 25 ? playerColor : Color.White;
		}

		public override void Draw()
		{
			if (!IsVisible() || Texts == null)
				return;
			
			var y = 0;
			foreach (var t in Texts)
			{
				var textSize = font.Measure(t);
				var location = new float2(Bounds.X, Bounds.Y + y);

				if (Align == TextAlign.Center)
					location += new int2((Bounds.Width - textSize.X) / 2, 0);

				if (Align == TextAlign.Right)
					location += new int2(Bounds.Width - textSize.X, 0);

				font.DrawTextWithShadow(t, location, textColor, bgDark, bgLight, 1);
				y += (font.Measure(t).Y + 3);
			}
		}
	}
}
