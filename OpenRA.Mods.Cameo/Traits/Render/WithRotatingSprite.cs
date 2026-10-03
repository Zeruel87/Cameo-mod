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
using System.Numerics;
using OpenRA.Graphics;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.Render
{
	[Desc("Renders a sprite that rotates continuously around the actor centre.")]
	public sealed class WithRotatingSpriteInfo : TraitInfo
	{
		[FieldLoader.Require]
		[Desc("Image containing the sprite.")]
		public readonly string Image = null;

		[SequenceReference(nameof(Image))]
		[Desc("Sequence to render.")]
		public readonly string Sequence = "idle";

		[PaletteReference]
		[Desc("Palette used to render the sprite.")]
		public readonly string Palette = "effect";

		[Desc("Position relative to the actor centre.")]
		public readonly WVec Offset = WVec.Zero;

		[Desc("Opacity of the rotating sprite.")]
		public readonly float Alpha = 1f;

		[Desc("Ticks required for one complete rotation.")]
		public readonly int RevolutionTicks = 500;

		[Desc("Rotate clockwise instead of counter-clockwise.")]
		public readonly bool Clockwise = true;

		public override object Create(ActorInitializer init) { return new WithRotatingSprite(init.Self, this); }
	}

	public sealed class WithRotatingSprite : IRender, ITick
	{
		readonly WithRotatingSpriteInfo info;
		readonly Animation animation;
		readonly int revolutionTicks;
		int ticks;

		public WithRotatingSprite(Actor self, WithRotatingSpriteInfo info)
		{
			this.info = info;
			revolutionTicks = System.Math.Max(1, info.RevolutionTicks);
			animation = new Animation(self.World, info.Image);
			animation.PlayRepeating(info.Sequence);
		}

		void ITick.Tick(Actor self)
		{
			animation.Tick();
			ticks = (ticks + 1) % revolutionTicks;
		}

		SpriteRenderable Renderable(Actor self, WorldRenderer wr)
		{
			var sequence = animation.CurrentSequence;
			var frame = animation.CurrentFrame;
			var (sprite, sourceRotation) = sequence.GetSpriteWithRotation(frame, WAngle.Zero);
			var direction = info.Clockwise ? -1 : 1;
			var rotationValue = (int)(direction * (long)ticks * 1024 / revolutionTicks);
			var rotation = sourceRotation + new WAngle(rotationValue);
			var tintModifiers = sequence.IgnoreWorldTint ? TintModifiers.IgnoreWorldTint : TintModifiers.None;

			return new SpriteRenderable(
				sprite,
				self.CenterPosition,
				info.Offset,
				sequence.ZOffset,
				wr.Palette(info.Palette),
				sequence.Scale,
				info.Alpha * sequence.GetAlpha(frame),
				Vector3.One,
				tintModifiers,
				true,
				rotation);
		}

		IEnumerable<IRenderable> IRender.Render(Actor self, WorldRenderer wr)
		{
			yield return Renderable(self, wr);
		}

		IEnumerable<Rectangle> IRender.ScreenBounds(Actor self, WorldRenderer wr)
		{
			yield return Renderable(self, wr).ScreenBounds(wr);
		}
	}
}
