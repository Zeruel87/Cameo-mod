#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or (at your
 * option) any later version. For more information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Numerics;
using System.Linq;
using OpenRA.Graphics;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Traits.Render;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	public class MaterializingProductionInit(bool value) : ValueActorInit<bool>(value), ISingleInstanceInit { }

	[Desc("Produces actors with the marker used by WithActorMaterialization.")]
	public class MaterializingProductionInfo : ProductionInfo
	{
		public override object Create(ActorInitializer init) { return new MaterializingProduction(init, this); }
	}

	public class MaterializingProduction : Production
	{
		public MaterializingProduction(ActorInitializer init, MaterializingProductionInfo info)
			: base(init, info) { }

		public override void DoProduction(Actor self, ActorInfo producee, ExitInfo exitinfo,
			string productionType, TypeDictionary inits)
		{
			var markedInits = new TypeDictionary(inits);
			if (!markedInits.Contains<MaterializingProductionInit>())
				markedInits.Add(new MaterializingProductionInit(true));

			base.DoProduction(self, producee, exitinfo, productionType, markedInits);
		}
	}

	[Desc("Materializes a newly factory-produced actor as a white silhouette, then reveals it bottom-to-top.")]
	public class WithActorMaterializationInfo : MaterializationInfo
	{
		[Desc("Only play for actors created by a MaterializingProduction exit.")]
		public readonly bool OnlyProducedActors = true;

		[Desc("White-hot saber core color and opacity.")]
		public readonly Color SaberCoreColor = Color.White;

		[Desc("Inner saber bloom color and opacity.")]
		public readonly Color SaberInnerGlowColor = Color.FromArgb(190, 55, 255, 155);

		[Desc("Outer saber bloom color and opacity.")]
		public readonly Color SaberOuterGlowColor = Color.FromArgb(90, 125, 55, 255);

		[Desc("Trailing afterglow color and opacity.")]
		public readonly Color SaberAfterglowColor = Color.FromArgb(70, 110, 255, 180);

		[Desc("Screen-pixel height of the white-hot core.")]
		public readonly int SaberCoreHeight = 2;

		[Desc("Keep the factory exit facing locked until the actor materialization completes.")]
		public readonly bool LockFacing = true;

		public override object Create(ActorInitializer init) { return new WithActorMaterialization(init, this); }
	}

	public class WithActorMaterialization : INotifyCreated, ITick, IRenderModifier
	{
		readonly WithActorMaterializationInfo info;
		readonly bool skipForward;
		readonly Vector3 silhouetteTint;
		readonly Vector3 saberCoreTint;
		readonly Vector3 saberInnerGlowTint;
		readonly Vector3 saberOuterGlowTint;
		readonly Vector3 saberAfterglowTint;
		readonly float silhouetteAlpha;
		readonly float saberCoreAlpha;
		readonly float saberInnerGlowAlpha;
		readonly float saberOuterGlowAlpha;
		readonly float saberAfterglowAlpha;

		static readonly int2[] InnerGlowOffsets =
		[
			new(-1, -1), new(0, -1), new(1, -1),
			new(-1, 0), new(1, 0),
			new(-1, 1), new(0, 1), new(1, 1)
		];

		static readonly int2[] OuterGlowOffsets =
		[
			new(-1, -2), new(0, -2), new(1, -2),
			new(-2, -1), new(2, -1),
			new(-2, 0), new(2, 0),
			new(-2, 1), new(2, 1),
			new(-1, 2), new(0, 2), new(1, 2)
		];

		int age;
		int conditionToken = Actor.InvalidConditionToken;
		long lastLogicTickTime;
		int observedTimestep = 40;
		IFacing facing;
		WAngle initialFacing;

		public WithActorMaterialization(ActorInitializer init, WithActorMaterializationInfo info)
		{
			this.info = info;
			skipForward = (info.RespectSkipMakeAnims && init.Contains<SkipMakeAnimsInit>(info))
				|| (info.OnlyProducedActors && !init.GetValue<MaterializingProductionInit, bool>(false));
			silhouetteTint = new Vector3(info.SilhouetteColor.R, info.SilhouetteColor.G, info.SilhouetteColor.B) / 255f;
			saberCoreTint = new Vector3(info.SaberCoreColor.R, info.SaberCoreColor.G, info.SaberCoreColor.B) / 255f;
			saberInnerGlowTint = new Vector3(info.SaberInnerGlowColor.R, info.SaberInnerGlowColor.G, info.SaberInnerGlowColor.B) / 255f;
			saberOuterGlowTint = new Vector3(info.SaberOuterGlowColor.R, info.SaberOuterGlowColor.G, info.SaberOuterGlowColor.B) / 255f;
			saberAfterglowTint = new Vector3(info.SaberAfterglowColor.R, info.SaberAfterglowColor.G, info.SaberAfterglowColor.B) / 255f;
			silhouetteAlpha = info.SilhouetteColor.A / 255f;
			saberCoreAlpha = info.SaberCoreColor.A / 255f;
			saberInnerGlowAlpha = info.SaberInnerGlowColor.A / 255f;
			saberOuterGlowAlpha = info.SaberOuterGlowColor.A / 255f;
			saberAfterglowAlpha = info.SaberAfterglowColor.A / 255f;
		}

		int Duration => Math.Max(0, info.FadeTicks) + Math.Max(0, info.RevealTicks);
		bool Active => !skipForward && age < Duration;

		void INotifyCreated.Created(Actor self)
		{
			lastLogicTickTime = Game.RunTime;
			facing = self.TraitOrDefault<IFacing>();
			if (facing != null)
				initialFacing = facing.Facing;

			if (!Active)
			{
				age = Duration;
				return;
			}

			conditionToken = self.GrantCondition(info.Condition);
		}

		void ITick.Tick(Actor self)
		{
			var now = Game.RunTime;
			if (lastLogicTickTime > 0)
				observedTimestep = (int)Math.Clamp(now - lastLogicTickTime, 1, Game.TimestepJankThreshold);
			lastLogicTickTime = now;

			if (!Active)
				return;

			// Production activities tick before traits and may turn a newly created
			// mobile actor while the materialization is still running. Keep the exact
			// factory exit facing used by the initial white silhouette until the reveal
			// completes, then let the queued activity turn and move normally.
			if (info.LockFacing && facing != null)
				facing.Facing = initialFacing;

			if (++age < Duration)
				return;

			if (conditionToken != Actor.InvalidConditionToken)
				conditionToken = self.RevokeCondition(conditionToken);
		}

		IEnumerable<IRenderable> IRenderModifier.ModifyRender(Actor self, WorldRenderer wr, IEnumerable<IRenderable> renderables)
		{
			if (!Active)
				return renderables;

			// Modify the actor's real renderables instead of drawing a private duplicate
			// animation. This preserves the exact facing, sequence, offsets, layers, and
			// pivot selected by the actor's body traits.
			return MaterializedRender(self, wr, renderables, RenderAge(self));
		}

		float RenderAge(Actor self)
		{
			if (self.World.Paused || observedTimestep <= 0)
				return age;

			var fraction = Math.Clamp((Game.RunTime - lastLogicTickTime) / (float)observedTimestep, 0f, 1f);
			return Math.Clamp(age + fraction, 0f, Math.Max(0, Duration - 1));
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
				var fade = fadeTicks == 0 ? 1f : renderAge / fadeTicks;
				foreach (var renderable in bodyRenderables)
				{
					if (renderable.IsDecoration || renderable is not IModifyableRenderable modifier)
						continue;

					yield return new MaterializationClipRenderable(
						modifier.WithTint(silhouetteTint,
							modifier.TintModifiers | TintModifiers.ReplaceColorPreserveAlpha | TintModifiers.IgnoreWorldTint)
							.WithAlpha(modifier.Alpha * silhouetteAlpha * fade),
						sharedBounds, MaterializationClipMode.Full, 0f, self.ActorID, 0, info);
				}

				yield break;
			}

			var revealAge = renderAge - fadeTicks;
			var progress = revealTicks <= 1 ? 1f : revealAge / (revealTicks - 1);
			var jitterPhase = (int)revealAge / Math.Max(1, info.ElectricJitterTicks);
			var revealTop = Math.Clamp(sharedBounds.Top + Math.Max(0, info.RevealTopInset),
				sharedBounds.Top, sharedBounds.Bottom);
			var revealBottom = Math.Clamp(sharedBounds.Bottom - Math.Max(0, info.RevealBottomInset),
				revealTop, sharedBounds.Bottom);
			var boundary = revealBottom - progress * (revealBottom - revealTop);
			foreach (var renderable in bodyRenderables)
			{
				if (renderable is not IModifyableRenderable modifier)
					continue;

				if (renderable.IsDecoration)
				{
					yield return modifier.WithAlpha(modifier.Alpha * progress);
					continue;
				}

				// Compose ordinary sprite bodies in one shader pass. This guarantees that
				// each source pixel is exactly one of silhouette, saber, or native color;
				// duplicated scissor-clipped copies can produce hard half-white component
				// seams on large diagonal actors such as the Scrin Tripods.
				if (modifier is SpriteRenderable sprite)
				{
					yield return sprite.WithMaterialization(new SpriteMaterialization(
						boundary, info.SaberCoreHeight,
						silhouetteTint, silhouetteAlpha,
						saberCoreTint, saberCoreAlpha,
						saberInnerGlowTint, saberInnerGlowAlpha,
						saberOuterGlowTint, saberOuterGlowAlpha,
						saberAfterglowTint, saberAfterglowAlpha));
					continue;
				}

				// Retain the generic clipped fallback for non-sprite renderables.
				yield return new MaterializationClipRenderable(
					modifier.WithTint(silhouetteTint,
						modifier.TintModifiers | TintModifiers.ReplaceColorPreserveAlpha | TintModifiers.IgnoreWorldTint)
						.WithAlpha(modifier.Alpha * silhouetteAlpha),
					sharedBounds, MaterializationClipMode.Above, progress, self.ActorID, jitterPhase, info);

				yield return new MaterializationClipRenderable(modifier, sharedBounds,
					MaterializationClipMode.Below, progress, self.ActorID, jitterPhase, info);

				yield return SaberLayer(modifier, sharedBounds, progress, self.ActorID, jitterPhase,
					saberAfterglowTint, saberAfterglowAlpha, Math.Max(1, info.SaberCoreHeight), info.SaberCoreHeight);
				foreach (var offset in OuterGlowOffsets)
					yield return SaberOffsetLayer(wr, modifier, sharedBounds, progress, self.ActorID, jitterPhase,
						saberOuterGlowTint, saberOuterGlowAlpha * 0.32f, info.SaberCoreHeight, offset);
				foreach (var offset in InnerGlowOffsets)
					yield return SaberOffsetLayer(wr, modifier, sharedBounds, progress, self.ActorID, jitterPhase,
						saberInnerGlowTint, saberInnerGlowAlpha * 0.45f, info.SaberCoreHeight, offset);
				yield return SaberLayer(modifier, sharedBounds, progress, self.ActorID, jitterPhase,
					saberCoreTint, saberCoreAlpha, Math.Max(1, info.SaberCoreHeight), 0);
			}
		}

		IRenderable SaberOffsetLayer(WorldRenderer wr, IModifyableRenderable modifier, Rectangle sharedBounds,
			float progress, uint actorId, int jitterPhase, Vector3 tint, float alpha, int height, int2 screenOffset)
		{
			var origin = wr.ProjectedPosition(int2.Zero);
			var target = wr.ProjectedPosition(screenOffset);
			var offset = target - origin;
			var layer = SaberLayer(modifier, sharedBounds, progress, actorId, jitterPhase,
				tint, alpha, Math.Max(1, height), 0).OffsetBy(offset);
			return layer.WithZOffset(layer.ZOffset - offset.Y - offset.Z);
		}

		MaterializationClipRenderable SaberLayer(IModifyableRenderable modifier, Rectangle sharedBounds,
			float progress, uint actorId, int jitterPhase, Vector3 tint, float alpha, int height, int offset)
		{
			return new MaterializationClipRenderable(
				modifier.WithTint(tint,
					modifier.TintModifiers | TintModifiers.ReplaceColorPreserveAlpha | TintModifiers.IgnoreWorldTint)
					.WithAlpha(modifier.Alpha * alpha),
				sharedBounds, MaterializationClipMode.Band, progress, actorId, jitterPhase, info, height, offset);
		}

		IEnumerable<Rectangle> IRenderModifier.ModifyScreenBounds(Actor self, WorldRenderer wr,
			IEnumerable<Rectangle> bounds)
		{
			return bounds;
		}
	}
}
