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
using System.Linq;
using System.Numerics;
using OpenRA.Graphics;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.World | SystemActors.EditorWorld)]
	[Desc("Renders a screen-space heat-haze distortion effect that displaces the framebuffer.",
		"Vertical-biased (heat rises), not radial. Add to the world actor.",
		"Deliberately separate from GlowRenderer: glow blends light, this displaces pixels.")]
	public class HeatDistortionRendererInfo : TraitInfo
	{
		[Desc("Gaussian falloff radius of each distortion in screen pixels.")]
		public readonly float DistortionRadius = 80f;

		[Desc("Peak pixel displacement at the centre of a distortion.")]
		public readonly float DistortionStrength = 12f;

		public override object Create(ActorInitializer init) { return new HeatDistortionRenderer(this); }
	}

	public sealed class HeatDistortionRenderer : IRenderPostProcessPass, INotifyActorDisposing
	{
		const int MaxDistortionsPerBatch = 16;

		// Hard upper bound on queued (pending + fading) distortions. Draw is the only place these lists are
		// drained, and it runs only on the render tick. If rendering stops (window minimized) or falls behind,
		// the simulation keeps registering distortions with nothing to drain them. Capping bounds the worst
		// case to a few extra shader batches in one frame instead of an unbounded flush that freezes the game.
		const int MaxActiveEffects = 64;

		// Fade timing and the shimmer animation follow logical game ticks, not render frames, so the effect
		// lasts the same wall-clock duration at any framerate and freezes while the game is paused.
		// fadeFrames/fadeInFrames are authored as render frames at ReferenceFps; convert to ticks to preserve the look.
		const float ReferenceFps = 60f;
		const float TicksPerSecond = 1000f / 40f; // normal game speed = 40ms timestep = 25 ticks/sec
		const float FramesToTicks = TicksPerSecond / ReferenceFps;

		static readonly string[] CentersKeys = Enumerable.Range(0, MaxDistortionsPerBatch).Select(i => $"DistortionCenters[{i}]").ToArray();
		static readonly string[] RadiiKeys = Enumerable.Range(0, MaxDistortionsPerBatch).Select(i => $"DistortionRadii[{i}]").ToArray();
		static readonly string[] StrengthsKeys = Enumerable.Range(0, MaxDistortionsPerBatch).Select(i => $"DistortionStrengths[{i}]").ToArray();

		readonly HeatDistortionRendererInfo info;
		readonly Renderer renderer;
		readonly IShader shader;
		readonly IVertexBuffer<RenderPostProcessPassVertex> buffer;

		readonly List<(WPos Center, float RadiusScale, float StrengthScale)> pendingDistortions = new();
		readonly List<(WPos Center, float RadiusScale, float StrengthScale, float TicksRemaining, float TotalTicks, float FadeInTicks, float HoldTicks)> fadingDistortions = new();

		readonly float[] centers = new float[MaxDistortionsPerBatch * 2];
		readonly float[] radii = new float[MaxDistortionsPerBatch];
		readonly float[] strengths = new float[MaxDistortionsPerBatch];

		// Game-time (seconds) counter driving the shimmer animation, advanced by elapsed ticks so its speed is
		// framerate-independent and pauses with the game. Render-only, so its value is irrelevant to sync.
		float time;

		// World tick at the previous Draw; used to advance fades/shimmer by elapsed ticks rather than render frames.
		int lastWorldTick = -1;

		public HeatDistortionRenderer(HeatDistortionRendererInfo info)
		{
			this.info = info;
			renderer = Game.Renderer;
			shader = renderer.CreateShader(new RenderPostProcessPassShaderBindings("heat_distortion"));
			buffer = renderer.CreateVertexBuffer(new RenderPostProcessPassVertex[]
			{
				new(-1, -1), new(1, -1), new(1, 1),
				new(1, 1), new(-1, 1), new(-1, -1)
			}, false);
		}

		public void RegisterDistortion(
			WPos center,
			float scale = 1f,
			int fadeFrames = 0,
			int fadeInFrames = 0)
		{
			RegisterDistortion(center, scale, scale, fadeFrames, fadeInFrames, 0);
		}

		public void RegisterDistortion(
			WPos center,
			float radiusScale,
			float strengthScale,
			int fadeFrames,
			int fadeInFrames)
		{
			RegisterDistortion(center, radiusScale, strengthScale, fadeFrames, fadeInFrames, 0);
		}

		public void RegisterDistortion(
			WPos center,
			float radiusScale,
			float strengthScale,
			int fadeFrames,
			int fadeInFrames,
			int holdFrames)
		{
			// Render-only cosmetic state that is drained exclusively by Draw (render tick). While the window
			// is minimized the render tick never runs, so nothing drains these lists, yet the simulation keeps
			// detonating warheads that call this. Dropping the registration while suspended keeps the lists from
			// growing without bound and flushing in one frame on restore. Sync is unaffected: the simulation
			// never reads this state.
			if (Game.Renderer.WindowIsSuspended)
				return;

			// If no distortion is currently active, Draw has been idle (it only runs while effects exist) so
			// lastWorldTick is stale; reset it, otherwise the first Draw would advance the fade by the whole
			// idle gap and instantly expire this distortion.
			if (pendingDistortions.Count == 0 && fadingDistortions.Count == 0)
				lastWorldTick = -1;

			if (fadeFrames > 0 || holdFrames > 0)
			{
				// Defensive bound for the render-starved (not suspended) case: drop the oldest, most-faded
				// distortion rather than let the list grow without limit.
				if (fadingDistortions.Count >= MaxActiveEffects)
					fadingDistortions.RemoveAt(0);

				// Convert before adding so malformed extreme YAML values cannot overflow
				// the integer addition and create a negative lifetime.
				var totalTicks = fadeFrames * FramesToTicks + holdFrames * FramesToTicks;
				var fadeInTicks = fadeInFrames * FramesToTicks;
				var holdTicks = holdFrames * FramesToTicks;
				fadingDistortions.Add((center, radiusScale, strengthScale, totalTicks, totalTicks, fadeInTicks, holdTicks));
				return;
			}

			if (pendingDistortions.Count >= MaxActiveEffects)
				return;

			pendingDistortions.Add((center, radiusScale, strengthScale));
		}

		PostProcessPassType IRenderPostProcessPass.Type => PostProcessPassType.AfterActors;
		bool IRenderPostProcessPass.Enabled => pendingDistortions.Count > 0 || fadingDistortions.Count > 0;

		void IRenderPostProcessPass.Draw(WorldRenderer wr)
		{
			// Advance fades and shimmer by the number of game ticks since the last Draw. At high framerates
			// multiple frames render per tick (elapsed == 0, effect holds steady); while paused WorldTick is frozen.
			var worldTick = wr.World.WorldTick;
			var ticksElapsed = lastWorldTick < 0 ? 0f : Math.Max(0, worldTick - lastWorldTick);
			lastWorldTick = worldTick;

			time += ticksElapsed / TicksPerSecond;

			var downscale = renderer.WorldDownscaleFactor;
			var topLeft = wr.Viewport.TopLeft;

			Vector2 ToFb(WPos pos)
			{
				var screenPx = wr.ScreenPxPosition(pos);
				return new Vector2(
					(screenPx.X - topLeft.X) * downscale,
					(screenPx.Y - topLeft.Y) * downscale);
			}

			// Collect all distortions for this frame into one flat list so they can be batched together.
			var batch = new List<(WPos Center, float RadiusScale, float StrengthScale)>(pendingDistortions.Count + fadingDistortions.Count);
			foreach (var d in pendingDistortions)
				batch.Add(d);
			pendingDistortions.Clear();

			for (var i = fadingDistortions.Count - 1; i >= 0; i--)
			{
				var d = fadingDistortions[i];
				var ticksPassed = d.TotalTicks - d.TicksRemaining;
				float fadeScale;
				if (d.FadeInTicks > 0 && ticksPassed < d.FadeInTicks)
					fadeScale = ticksPassed / d.FadeInTicks;
				else if (ticksPassed < d.FadeInTicks + d.HoldTicks)
					fadeScale = 1f;
				else
				{
					var fadeOutTotal = d.TotalTicks - d.FadeInTicks - d.HoldTicks;
					fadeScale = fadeOutTotal > 0 ? d.TicksRemaining / fadeOutTotal : 1f;
				}

				fadeScale = Math.Clamp(fadeScale, 0f, 1f);
				batch.Add((d.Center, d.RadiusScale, d.StrengthScale * fadeScale));

				var remaining = d.TicksRemaining - ticksElapsed;
				if (remaining <= 0f)
					fadingDistortions.RemoveAt(i);
				else
					fadingDistortions[i] = (d.Center, d.RadiusScale, d.StrengthScale, remaining, d.TotalTicks, d.FadeInTicks, d.HoldTicks);
			}

			// Draw distortions in fixed-size batches. Each batch takes one framebuffer snapshot and runs
			// a single shader pass that loops over all sources, accumulating displacement before sampling.
			for (var offset = 0; offset < batch.Count; offset += MaxDistortionsPerBatch)
			{
				var batchSize = Math.Min(MaxDistortionsPerBatch, batch.Count - offset);

				for (var i = 0; i < batchSize; i++)
				{
					var d = batch[offset + i];
					var p = ToFb(d.Center);

					centers[i * 2] = p.X;
					centers[i * 2 + 1] = p.Y;
					radii[i] = info.DistortionRadius * d.RadiusScale;
					strengths[i] = info.DistortionStrength * d.StrengthScale;
				}

				shader.SetTexture("WorldTexture", Game.Renderer.GetRenderBufferSnapshot());

				// ANGLE/ES rejects glUniformXfv with count > 1 on array uniforms, so set each element individually.
				for (var i = 0; i < batchSize; i++)
				{
					shader.SetVec(CentersKeys[i], centers[i * 2], centers[i * 2 + 1]);
					shader.SetVec(RadiiKeys[i], radii[i]);
					shader.SetVec(StrengthsKeys[i], strengths[i]);
				}

				shader.SetVec("DistortionCount", (float)batchSize);
				shader.SetVec("Time", time);
				shader.PrepareRender();
				renderer.DrawBatch(buffer, shader, 0, 6, PrimitiveType.TriangleList);
			}
		}

		void INotifyActorDisposing.Disposing(Actor self)
		{
			buffer.Dispose();
		}
	}
}
