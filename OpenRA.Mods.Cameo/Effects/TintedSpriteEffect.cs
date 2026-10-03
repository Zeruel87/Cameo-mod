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
using System.Numerics;
using OpenRA.Effects;
using OpenRA.Graphics;
using OpenRA.Primitives;

namespace OpenRA.Mods.Cameo.Effects
{
	// A short-lived sprite effect that recolors the rendered sprite to a fixed tint.
	// Modeled on OpenRA.Mods.Common.Effects.SpriteEffect, with a ReplaceColor tint applied.
	public class TintedSpriteEffect : IEffect, ISpatiallyPartitionable
	{
		readonly World world;
		readonly string palette;
		readonly Animation anim;
		readonly WPos pos;
		readonly bool visibleThroughFog;
		readonly string sequence;
		readonly Vector3 tint;
		bool initialized;

		public TintedSpriteEffect(WPos pos, World world, string image, string sequence, string palette,
			Color tintColor, bool visibleThroughFog = false)
		{
			this.world = world;
			this.pos = pos;
			this.palette = palette;
			this.sequence = sequence;
			this.visibleThroughFog = visibleThroughFog;
			tint = new Vector3(tintColor.R, tintColor.G, tintColor.B) / 255f;
			anim = new Animation(world, image);
		}

		public void Tick(World world)
		{
			if (!initialized)
			{
				anim.PlayThen(sequence, () => world.AddFrameEndTask(w => { w.Remove(this); w.ScreenMap.Remove(this); }));
				world.ScreenMap.Add(this, pos, anim.Image);
				initialized = true;
			}
			else
			{
				anim.Tick();
				world.ScreenMap.Update(this, pos, anim.Image);
			}
		}

		public IEnumerable<IRenderable> Render(WorldRenderer wr)
		{
			if (!initialized || (!visibleThroughFog && world.FogObscures(pos)))
				return SpriteRenderable.None;

			// Multiplicative tint (not ReplaceColor): because the sparkle sprite is white,
			// multiplying by the tint yields that color while preserving the sprite's
			// per-pixel alpha — which is where the fade in/out lives. ReplaceColor would
			// discard that texture alpha and render every frame fully opaque.
			return anim.Render(pos, wr.Palette(palette))
				.Where(r => r is IModifyableRenderable)
				.Select(r =>
				{
					var mr = (IModifyableRenderable)r;
					return mr.WithTint(tint, mr.TintModifiers);
				});
		}
	}
}
