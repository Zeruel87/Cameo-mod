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

using OpenRA.Mods.Common.Widgets;

namespace OpenRA.Mods.Cameo.Widgets
{
	public class ScaledImageWidget : ImageWidget
	{
		public ScaledImageWidget() { }

		protected ScaledImageWidget(ScaledImageWidget other)
			: base(other) { }

		public override ScaledImageWidget Clone() { return new ScaledImageWidget(this); }

		public override void Draw()
		{
			WidgetUtils.DrawSprite(GetSprite(), RenderOrigin.ToVector2(), RenderBounds.Size);
		}
	}
}
