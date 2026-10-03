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
using System.Collections.Generic;
using System.Numerics;
using System.Collections.Immutable;
using System.Linq;
using OpenRA.Activities;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Traits.Render;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	public abstract class MaterializationInfo : TraitInfo, Requires<RenderSpritesInfo>
	{
		[Desc("Ticks used to fade the initial white silhouette from transparent to opaque.")]
		public readonly int FadeTicks = 10;

		[Desc("Ticks used by the bottom-to-top sprite reveal.")]
		public readonly int RevealTicks = 30;

		[Desc("Sprite body names affected by the materialization effect.")]
		public readonly ImmutableArray<string> BodyNames = ["body"];

		[GrantedConditionReference]
		[Desc("Condition granted while materializing. Other traits may require its inverse to pause during the effect.")]
		public readonly string Condition = "materializing";

		[Desc("White silhouette color and opacity.")]
		public readonly Color SilhouetteColor = Color.FromArgb(230, 255, 255, 255);

		[Desc("Electric boundary color and opacity.")]
		public readonly Color ElectricColor = Color.FromArgb(255, 152, 255, 226);

		[Desc("Height of the electric boundary in screen pixels.")]
		public readonly int ElectricBandHeight = 4;

		[Desc("Width of each independently jittered electric boundary segment in screen pixels.")]
		public readonly int ElectricStripWidth = 8;

		[Desc("Maximum vertical jitter of the electric boundary in screen pixels.")]
		public readonly int ElectricJitter = 5;

		[Desc("Transparent padding to skip above the visible body, in world-render pixels.")]
		public readonly int RevealTopInset = 0;

		[Desc("Transparent padding to skip below the visible body, in world-render pixels.")]
		public readonly int RevealBottomInset = 0;

		[Desc("Ticks between deterministic electric-boundary jitter changes.")]
		public readonly int ElectricJitterTicks = 2;

		[Desc("Honor SkipMakeAnimsInit, suppressing the effect for map actors and other skipped make animations.")]
		public readonly bool RespectSkipMakeAnims = true;

		[Desc("Pilot-only delay before repeating the effect. Zero keeps normal one-shot behavior.")]
		public readonly int PreviewLoopDelayTicks = 0;
	}

	[Desc("Materializes selected sprite bodies without requiring dedicated make sequences.",
		"The bodies fade in as white silhouettes, then a configurable electric boundary",
		"travels from bottom to top and reveals their normal sprites.")]
	public class WithBuildingMaterializationInfo : MaterializationInfo, Requires<WithSpriteBodyInfo>
	{

		public override object Create(ActorInitializer init) { return new WithBuildingMaterialization(init, this); }
	}

	public class WithBuildingMaterialization : INotifyCreated, ITick, IRender, IBuildingMakeAnimation
	{
		readonly MaterializationInfo info;
		readonly WithSpriteBody[] bodies;
		readonly RenderSprites renderSprites;
		readonly bool skipForward;
		readonly Vector3 silhouetteTint;
		readonly Vector3 electricTint;
		readonly float silhouetteAlpha;
		readonly float electricAlpha;

		int age;
		int loopDelay;
		int conditionToken = Actor.InvalidConditionToken;
		bool reversing;
		Activity reverseActivity;
		bool reverseQueued;
		long lastLogicTickTime;
		int observedTimestep = 40;

		public WithBuildingMaterialization(ActorInitializer init, WithBuildingMaterializationInfo info)
		{
			this.info = info;
			var self = init.Self;
			bodies = self.TraitsImplementing<WithSpriteBody>().Where(w => info.BodyNames.Contains(w.Info.Name)).ToArray();
			renderSprites = self.Trait<RenderSprites>();
			skipForward = info.RespectSkipMakeAnims && init.Contains<SkipMakeAnimsInit>(info);
			silhouetteTint = new Vector3(info.SilhouetteColor.R, info.SilhouetteColor.G, info.SilhouetteColor.B) / 255f;
			electricTint = new Vector3(info.ElectricColor.R, info.ElectricColor.G, info.ElectricColor.B) / 255f;
			silhouetteAlpha = info.SilhouetteColor.A / 255f;
			electricAlpha = info.ElectricColor.A / 255f;
		}

		int Duration => Math.Max(0, info.FadeTicks) + Math.Max(0, info.RevealTicks);

		bool Active => (reversing || !skipForward) && age < Duration;

		void INotifyCreated.Created(Actor self)
		{
			lastLogicTickTime = Game.RunTime;
			if (skipForward || Duration == 0 || bodies.Length == 0)
			{
				age = Duration;
				return;
			}

			EnsureBodyAnimations(self);
			conditionToken = self.GrantCondition(info.Condition);
		}

		void ITick.Tick(Actor self)
		{
			var now = Game.RunTime;
			if (lastLogicTickTime > 0)
				observedTimestep = (int)Math.Clamp(now - lastLogicTickTime, 1, Game.TimestepJankThreshold);
			lastLogicTickTime = now;

			if (Duration == 0 || bodies.Length == 0)
				return;

			if (reversing)
			{
				if (age > 0)
				{
					age--;
					return;
				}

				reversing = false;
				age = Duration;
				var activity = reverseActivity;
				reverseActivity = null;
				// Match WithMakeAnimation's sell handoff: keep the normal body disabled
				// during the one tick before the disposing follow-up activity runs.
				if (activity != null)
					self.QueueActivity(reverseQueued, activity);

				return;
			}

			if (skipForward)
				return;

			if (age < Duration)
			{
				if (++age < Duration)
					return;

				if (conditionToken != Actor.InvalidConditionToken)
					conditionToken = self.RevokeCondition(conditionToken);

				loopDelay = 0;
				return;
			}

			if (info.PreviewLoopDelayTicks <= 0 || ++loopDelay < info.PreviewLoopDelayTicks)
				return;

			age = 0;
			loopDelay = 0;
			conditionToken = self.GrantCondition(info.Condition);
		}

		void EnsureBodyAnimations(Actor self)
		{
			// The materializing condition disables the normal body. Ensure its animation has
			// selected a sequence before granting that condition so render bounds remain valid.
			foreach (var body in bodies)
				if (body.DefaultAnimation.CurrentSequence == null)
					body.DefaultAnimation.PlayRepeating(body.NormalizeSequence(self, body.Info.Sequence));
		}

		public void Reverse(Actor self, Activity activity, bool queued = true)
		{
			if (Duration == 0 || bodies.Length == 0)
			{
				self.QueueActivity(queued, activity);
				return;
			}

			EnsureBodyAnimations(self);
			reversing = true;
			reverseActivity = activity;
			reverseQueued = queued;
			loopDelay = 0;
			age = Math.Max(0, Duration - 1);
			if (conditionToken == Actor.InvalidConditionToken)
				conditionToken = self.GrantCondition(info.Condition);
		}

		PaletteReference PaletteFor(Actor self, WorldRenderer wr, WithSpriteBody body)
		{
			var owner = self.EffectiveOwner != null && self.EffectiveOwner.Disguised ? self.EffectiveOwner.Owner : self.Owner;
			if (body.Info.Palette != null)
				return wr.Palette(body.Info.IsPlayerPalette ? body.Info.Palette + owner.InternalName : body.Info.Palette);

			return renderSprites.Info.Palette != null ?
				wr.Palette(renderSprites.Info.Palette) :
				wr.Palette(renderSprites.Info.PlayerPalette + owner.InternalName);
		}

		IEnumerable<IRenderable> BodyRenderables(Actor self, WorldRenderer wr)
		{
			foreach (var body in bodies)
			{
				if (body.DefaultAnimation.CurrentSequence == null)
					continue;

				var offset = body.Info.ForceToGround ?
					new WVec(0, 0, -self.World.Map.DistanceAboveTerrain(self.CenterPosition).Length) :
					WVec.Zero;

				foreach (var renderable in body.DefaultAnimation.Render(self.CenterPosition, offset, 0, PaletteFor(self, wr, body)))
					yield return renderable;
			}
		}

		IEnumerable<IRenderable> IRender.Render(Actor self, WorldRenderer wr)
		{
			if (!Active)
				return SpriteRenderable.None;

			return MaterializedRender(self, wr, BodyRenderables(self, wr), RenderAge(self));
		}

		float RenderAge(Actor self)
		{
			if (self.World.Paused)
				return age;

			if (observedTimestep <= 0)
				return age;

			var fraction = Math.Clamp((Game.RunTime - lastLogicTickTime) / (float)observedTimestep, 0f, 1f);
			var interpolated = age + (reversing ? -fraction : fraction);
			return Math.Clamp(interpolated, 0f, Math.Max(0, Duration - 1));
		}

		IEnumerable<IRenderable> MaterializedRender(Actor self, WorldRenderer wr,
			IEnumerable<IRenderable> renderables, float renderAge)
		{
			var bodyRenderables = renderables.ToArray();
			var sharedBounds = bodyRenderables
				.Where(renderable => !renderable.IsDecoration)
				.Select(renderable => renderable.PrepareRender(wr).ScreenBounds(wr))
				.Where(bounds => !bounds.IsEmpty)
				.Union();
			var fadeTicks = Math.Max(0, info.FadeTicks);
			var revealTicks = Math.Max(0, info.RevealTicks);
			if (renderAge < fadeTicks)
			{
				// Reach full white exactly at the phase boundary. Using fadeTicks - 1
				// would hold a completed silhouette for one logic tick before reveal.
				var fade = fadeTicks == 0 ? 1f : renderAge / fadeTicks;
				foreach (var renderable in bodyRenderables)
				{
					if (renderable.IsDecoration || renderable is not IModifyableRenderable modifier)
						continue;

					yield return new MaterializationClipRenderable(
						modifier.WithTint(silhouetteTint, modifier.TintModifiers | TintModifiers.ReplaceColor | TintModifiers.IgnoreWorldTint)
							.WithAlpha(modifier.Alpha * silhouetteAlpha * fade),
						sharedBounds, MaterializationClipMode.Full, 0f, self.ActorID, 0, info);
				}

				yield break;
			}

			var revealAge = renderAge - fadeTicks;
			var progress = revealTicks <= 1 ? 1f : revealAge / (revealTicks - 1);
			var jitterPhase = (int)revealAge / Math.Max(1, info.ElectricJitterTicks);
			foreach (var renderable in bodyRenderables)
			{
				if (renderable is not IModifyableRenderable modifier)
					continue;

				// Shadows remain absent during the white fade, then emerge smoothly with
				// the materialized mass. They are never sliced or recolored.
				if (renderable.IsDecoration)
				{
					yield return modifier.WithAlpha(modifier.Alpha * progress);
					continue;
				}

				yield return new MaterializationClipRenderable(
					modifier.WithTint(silhouetteTint, modifier.TintModifiers | TintModifiers.ReplaceColor | TintModifiers.IgnoreWorldTint)
						.WithAlpha(modifier.Alpha * silhouetteAlpha),
					sharedBounds, MaterializationClipMode.Above, progress, self.ActorID, jitterPhase, info);

				yield return new MaterializationClipRenderable(modifier, sharedBounds,
					MaterializationClipMode.Below, progress, self.ActorID, jitterPhase, info);

				yield return new MaterializationClipRenderable(
					modifier.WithTint(electricTint, modifier.TintModifiers | TintModifiers.ReplaceColor | TintModifiers.IgnoreWorldTint)
						.WithAlpha(modifier.Alpha * electricAlpha),
					sharedBounds, MaterializationClipMode.Band, progress, self.ActorID, jitterPhase, info);
			}
		}

		IEnumerable<Rectangle> IRender.ScreenBounds(Actor self, WorldRenderer wr)
		{
			if (!Active)
				return [];

			return bodies
				.Where(body => body.DefaultAnimation.CurrentSequence != null)
				.Select(body => body.DefaultAnimation.ScreenBounds(wr, self.CenterPosition, WVec.Zero));
		}
	}

	enum MaterializationClipMode
	{
		Full,
		Above,
		Below,
		Band
	}

	sealed class MaterializationClipRenderable : IPalettedRenderable, IModifyableRenderable
	{
		readonly IModifyableRenderable inner;
		readonly Rectangle sharedBounds;
		readonly WVec boundsOffset;
		readonly MaterializationClipMode mode;
		readonly float progress;
		readonly uint actorId;
		readonly int jitterPhase;
		readonly MaterializationInfo info;
		readonly int bandHeight;
		readonly int boundaryOffset;

		public MaterializationClipRenderable(IModifyableRenderable inner, Rectangle sharedBounds,
			MaterializationClipMode mode, float progress, uint actorId, int jitterPhase,
			MaterializationInfo info, int bandHeight = 0, int boundaryOffset = 0)
			: this(inner, sharedBounds, WVec.Zero, mode, progress, actorId, jitterPhase,
				info, bandHeight, boundaryOffset) { }

		MaterializationClipRenderable(IModifyableRenderable inner, Rectangle sharedBounds, WVec boundsOffset,
			MaterializationClipMode mode, float progress, uint actorId, int jitterPhase,
			MaterializationInfo info, int bandHeight, int boundaryOffset)
		{
			this.inner = inner;
			this.sharedBounds = sharedBounds;
			this.boundsOffset = boundsOffset;
			this.mode = mode;
			this.progress = Math.Clamp(progress, 0f, 1f);
			this.actorId = actorId;
			this.jitterPhase = jitterPhase;
			this.info = info;
			this.bandHeight = bandHeight;
			this.boundaryOffset = boundaryOffset;
		}

		public WPos Pos => inner.Pos;
		public int ZOffset => inner.ZOffset;
		public bool IsDecoration => inner.IsDecoration;
		public PaletteReference Palette => ((IPalettedRenderable)inner).Palette;
		public float Alpha => inner.Alpha;
		public Vector3 Tint => inner.Tint;
		public TintModifiers TintModifiers => inner.TintModifiers;

		public IRenderable WithZOffset(int newOffset)
		{
			return Wrap((IModifyableRenderable)inner.WithZOffset(newOffset));
		}

		public IRenderable OffsetBy(in WVec offset)
		{
			return new MaterializationClipRenderable((IModifyableRenderable)inner.OffsetBy(offset),
				sharedBounds, boundsOffset + offset, mode, progress, actorId, jitterPhase,
				info, bandHeight, boundaryOffset);
		}

		public IRenderable AsDecoration()
		{
			var decoration = (IModifyableRenderable)inner.AsDecoration();
			return mode == MaterializationClipMode.Below ?
				decoration.WithAlpha(decoration.Alpha * progress) :
				decoration.WithAlpha(0f);
		}

		public IPalettedRenderable WithPalette(PaletteReference newPalette)
		{
			return Wrap((IModifyableRenderable)((IPalettedRenderable)inner).WithPalette(newPalette));
		}

		public IModifyableRenderable WithAlpha(float newAlpha)
		{
			return Wrap(inner.WithAlpha(newAlpha));
		}

		public IModifyableRenderable WithTint(in Vector3 newTint, TintModifiers newTintModifiers)
		{
			return Wrap(inner.WithTint(newTint, newTintModifiers));
		}

		MaterializationClipRenderable Wrap(IModifyableRenderable renderable)
		{
			return new MaterializationClipRenderable(renderable, sharedBounds, boundsOffset,
				mode, progress, actorId, jitterPhase, info, bandHeight, boundaryOffset);
		}

		public IFinalizedRenderable PrepareRender(WorldRenderer wr)
		{
			return new FinalizedMaterializationClipRenderable(inner.PrepareRender(wr), sharedBounds, boundsOffset,
				mode, progress, actorId, jitterPhase, info, bandHeight, boundaryOffset);
		}
	}

	sealed class FinalizedMaterializationClipRenderable : IFinalizedRenderable
	{
		readonly IFinalizedRenderable inner;
		readonly Rectangle sharedBounds;
		readonly WVec boundsOffset;
		readonly MaterializationClipMode mode;
		readonly float progress;
		readonly uint actorId;
		readonly int jitterPhase;
		readonly MaterializationInfo info;
		readonly int bandHeight;
		readonly int boundaryOffset;

		public FinalizedMaterializationClipRenderable(IFinalizedRenderable inner, Rectangle sharedBounds, WVec boundsOffset,
			MaterializationClipMode mode, float progress, uint actorId, int jitterPhase,
			MaterializationInfo info, int bandHeight, int boundaryOffset)
		{
			this.inner = inner;
			this.sharedBounds = sharedBounds;
			this.boundsOffset = boundsOffset;
			this.mode = mode;
			this.progress = progress;
			this.actorId = actorId;
			this.jitterPhase = jitterPhase;
			this.info = info;
			this.bandHeight = bandHeight;
			this.boundaryOffset = boundaryOffset;
		}

		Rectangle ViewBounds(WorldRenderer wr)
		{
			var world = sharedBounds;
			if (world.IsEmpty)
				return Rectangle.Empty;

			var offset = wr.ScreenPxOffset(boundsOffset);
			world = new Rectangle(world.X + offset.X, world.Y + offset.Y, world.Width, world.Height);

			// World renderables are drawn into the unscaled world buffer. Its scissor
			// coordinates match world-pixel positions relative to the viewport top-left,
			// not the zoomed/UI-space coordinates returned by WorldToViewPx.
			var topLeft = world.TopLeft - wr.Viewport.TopLeft;
			var bottomRight = world.BottomRight - wr.Viewport.TopLeft;
			return Rectangle.FromLTRB(
				Math.Min(topLeft.X, bottomRight.X), Math.Min(topLeft.Y, bottomRight.Y),
				Math.Max(topLeft.X, bottomRight.X), Math.Max(topLeft.Y, bottomRight.Y));
		}

		public void Render(WorldRenderer wr)
		{
			if (mode == MaterializationClipMode.Full)
			{
				inner.Render(wr);
				return;
			}

			var bounds = ViewBounds(wr);
			if (bounds.IsEmpty || bounds.Width <= 0 || bounds.Height <= 0)
				return;

			var revealTop = Math.Clamp(bounds.Top + Math.Max(0, info.RevealTopInset), bounds.Top, bounds.Bottom);
			var revealBottom = Math.Clamp(bounds.Bottom - Math.Max(0, info.RevealBottomInset), revealTop, bounds.Bottom);
			var boundary = revealBottom - (int)Math.Round(progress * (revealBottom - revealTop)) + boundaryOffset;
			if (mode != MaterializationClipMode.Band)
			{
				var clip = mode == MaterializationClipMode.Above ?
					Rectangle.FromLTRB(bounds.Left, bounds.Top, bounds.Right, Math.Clamp(boundary, bounds.Top, bounds.Bottom)) :
					Rectangle.FromLTRB(bounds.Left, Math.Clamp(boundary, bounds.Top, bounds.Bottom), bounds.Right, bounds.Bottom);

				RenderClipped(wr, clip);
				return;
			}

			var stripWidth = Math.Max(1, info.ElectricStripWidth);
			var renderedBandHeight = Math.Max(1, bandHeight > 0 ? bandHeight : info.ElectricBandHeight);
			if (info.ElectricJitter <= 0)
			{
				var top = Math.Clamp(boundary - renderedBandHeight / 2, bounds.Top, bounds.Bottom);
				var bottom = Math.Clamp(top + renderedBandHeight, bounds.Top, bounds.Bottom);
				RenderClipped(wr, Rectangle.FromLTRB(bounds.Left, top, bounds.Right, bottom));
				return;
			}

			for (int left = bounds.Left, strip = 0; left < bounds.Right; left += stripWidth, strip++)
			{
				var right = Math.Min(bounds.Right, left + stripWidth);
				var jitter = Jitter(actorId, strip, jitterPhase, Math.Max(0, info.ElectricJitter));
				var center = boundary + jitter;
				var top = Math.Clamp(center - renderedBandHeight / 2, bounds.Top, bounds.Bottom);
				var bottom = Math.Clamp(top + renderedBandHeight, bounds.Top, bounds.Bottom);
				RenderClipped(wr, Rectangle.FromLTRB(left, top, right, bottom));
			}
		}

		void RenderClipped(WorldRenderer wr, Rectangle clip)
		{
			if (clip.Width <= 0 || clip.Height <= 0)
				return;

			Game.Renderer.EnableScissor(clip);
			try
			{
				inner.Render(wr);
			}
			finally
			{
				Game.Renderer.DisableScissor();
			}
		}

		static int Jitter(uint actorId, int strip, int phase, int range)
		{
			if (range == 0)
				return 0;

			unchecked
			{
				var value = actorId ^ (uint)(strip * 0x45d9f3b) ^ (uint)(phase * 0x27d4eb2d);
				value ^= value >> 16;
				value *= 0x7feb352d;
				value ^= value >> 15;
				return (int)(value % (uint)(2 * range + 1)) - range;
			}
		}

		public void RenderDebugGeometry(WorldRenderer wr) { inner.RenderDebugGeometry(wr); }
		public Rectangle ScreenBounds(WorldRenderer wr) { return inner.ScreenBounds(wr); }
	}
}
