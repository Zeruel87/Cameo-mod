#region Copyright & License Information
/*
 * Copyright 2007-2020 The OpenRA Developers (see AUTHORS)
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Primitives;

namespace OpenRA.Mods.Common.LoadScreens
{
	public sealed class FitImageLoadScreen : SheetLoadScreen
	{
		//Rectangle stripeRect;
		float2 scale;
		float2 logoPos;
		Sprite logo;

		Sheet lastSheet;
		int lastDensity;
		Size lastResolution;

		string[] messages = { "Loading..." };

		public override void Init(ModData modData, Dictionary<string, string> info)
		{
			base.Init(modData, info);

			if (info.ContainsKey("Text"))
				messages = info["Text"].Split(',');
		}

		public override void DisplayInner(Renderer r, Sheet s, int density)
		{
			if (s != lastSheet || density != lastDensity)
			{
				lastSheet = s;
				Rectangle rect = new Rectangle(0, 0, s.Size.Width, s.Size.Height);

				lastDensity = density;

				scale = new float2((float) r.Resolution.Width / (float) s.Size.Width, (float) r.Resolution.Height / (float) s.Size.Height );

				if (scale.X > scale.Y) {
					logo = new Sprite(s, rect, TextureChannel.RGBA, scale.Y * 1f);
				}
				else {
					logo = new Sprite(s, rect, TextureChannel.RGBA, scale.X * 1f);
				}
			}

			if (r.Resolution != lastResolution)
			{
				lastResolution = r.Resolution;

				if (scale.X > scale.Y) {
					logoPos = new float2((r.Resolution.Width - s.Size.Width*scale.Y) / 2, 0);
				}
				else {
					logoPos = new float2(0, (-s.Size.Height*scale.X + r.Resolution.Height) / 2);
				}
			}

			if (logo != null)
				r.RgbaSpriteRenderer.DrawSprite(logo, logoPos);

			if (r.Fonts != null)
			{
				var text = messages.Random(Game.CosmeticRandom);
				var textSize = r.Fonts["Bold"].Measure(text);
				r.Fonts["Bold"].DrawText(text, new float2(r.Resolution.Width - textSize.X - 20, r.Resolution.Height - textSize.Y - 20), Color.White);
			}
		}
	}
}
