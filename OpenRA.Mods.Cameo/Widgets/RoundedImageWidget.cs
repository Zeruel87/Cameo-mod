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
using OpenRA.Graphics;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Primitives;

namespace OpenRA.Mods.Cameo.Widgets
{
	// Scaled image with optional rounded corners. Rounding is done by clipping the
	// scaled sprite to a stack of horizontal scissor strips that follow a quarter-circle,
	// so the rounded-off corners simply aren't drawn (the background shows through) -
	// no alpha mask, baked art or shader required.
	public class RoundedImageWidget : ScaledImageWidget
	{
		public int CornerRadius = 0;
		public bool RoundTopLeft = false;
		public bool RoundTopRight = false;
		public bool RoundBottomLeft = false;
		public bool RoundBottomRight = false;

		public RoundedImageWidget() { }

		protected RoundedImageWidget(RoundedImageWidget other)
			: base(other)
		{
			CornerRadius = other.CornerRadius;
			RoundTopLeft = other.RoundTopLeft;
			RoundTopRight = other.RoundTopRight;
			RoundBottomLeft = other.RoundBottomLeft;
			RoundBottomRight = other.RoundBottomRight;
		}

		public override RoundedImageWidget Clone() { return new RoundedImageWidget(this); }

		public override void Draw()
		{
			var sprite = GetSprite();
			if (sprite == null)
				return;

			var origin = RenderOrigin;
			var size = RenderBounds.Size;
			var w = size.Width;
			var h = size.Height;
			var r = Math.Min(CornerRadius, Math.Min(w, h) / 2);

			if (r <= 0)
			{
				WidgetUtils.DrawSprite(sprite, origin.ToVector2(), size);
				return;
			}

			// Full-width band between the two rounded corner zones.
			DrawClipped(sprite, origin, size, new Rectangle(origin.X, origin.Y + r, w, h - 2 * r));

			// Corner rows: inset the relevant edge along a quarter-circle profile.
			for (var i = 0; i < r; i++)
			{
				var j = r - i;
				var inset = (int)Math.Round(r - Math.Sqrt(Math.Max(0, (r * r) - (j * j))));

				var topLeft = RoundTopLeft ? inset : 0;
				var topRight = RoundTopRight ? inset : 0;
				var botLeft = RoundBottomLeft ? inset : 0;
				var botRight = RoundBottomRight ? inset : 0;

				DrawClipped(sprite, origin, size, new Rectangle(origin.X + topLeft, origin.Y + i, w - topLeft - topRight, 1));
				DrawClipped(sprite, origin, size, new Rectangle(origin.X + botLeft, origin.Y + h - 1 - i, w - botLeft - botRight, 1));
			}
		}

		static void DrawClipped(Sprite sprite, int2 origin, Size size, Rectangle clip)
		{
			if (clip.Width <= 0 || clip.Height <= 0)
				return;

			Game.Renderer.EnableScissor(clip);
			WidgetUtils.DrawSprite(sprite, origin.ToVector2(), size);
			Game.Renderer.DisableScissor();
		}
	}
}
