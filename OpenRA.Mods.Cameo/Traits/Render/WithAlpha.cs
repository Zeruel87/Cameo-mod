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
using OpenRA.Graphics;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	[Desc("Set to an alpha when a condition is active.")]
	public class WithAlphaInfo : ConditionalTraitInfo
	{
		[Desc("The alpha level to use when enabled.")]
		public readonly float Alpha = 0.55f;

		public override object Create(ActorInitializer init) { return new WithAlpha(this); }
	}

	public class WithAlpha : ConditionalTrait<WithAlphaInfo>, IRenderModifier
	{
		public WithAlpha(WithAlphaInfo info)
			: base(info) { }

		IEnumerable<IRenderable> IRenderModifier.ModifyRender(Actor self, WorldRenderer wr, IEnumerable<IRenderable> r)
		{
			if (IsTraitDisabled)
				return r;

			return ModifiedRender(r);
		}

		IEnumerable<IRenderable> ModifiedRender(IEnumerable<IRenderable> r)
		{
			foreach (var a in r)
			{
				if (!a.IsDecoration && a is IModifyableRenderable ma)
					yield return ma.WithAlpha(Info.Alpha);
			}
		}

		IEnumerable<Rectangle> IRenderModifier.ModifyScreenBounds(Actor self, WorldRenderer wr, IEnumerable<Rectangle> bounds)
		{
			return bounds;
		}
	}
}
