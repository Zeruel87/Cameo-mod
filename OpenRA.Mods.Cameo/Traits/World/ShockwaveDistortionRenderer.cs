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
	[Desc("Renders a screen-space shockwave-lens distortion: a refraction ring that expands outward",
		"from an impact over a fraction of a second (pressure-wave look). Add to the world actor.",
		"Deliberately separate from HeatDistortionRenderer: heat is vertical/ambient, this is radial/transient.")]
	public class ShockwaveDistortionRendererInfo : TraitInfo
	{
		[Desc("Screen pixels the ring expands out to over its lifetime.")]
		public readonly float MaxRadius = 300f;

		[Desc("Thickness in screen pixels of the displaced ring band.")]
		public readonly float RingThickness = 30f;

		[Desc("Peak radial pixel displacement at the ring band.")]
		public readonly float Strength = 20f;

		public override object Create(ActorInitializer init) { return new ShockwaveDistortionRenderer(this); }
	}

	public sealed class ShockwaveDistortionRenderer : IRenderPostProcessPass, INotifyActorDisposing
	{
		const int MaxDistortionsPerBatch = 16;

		// Hard upper bound on queued (pending + fading) shockwaves. Draw is the only place these lists are
		// drained, and it runs only on the render tick. If rendering stops (window minimized) or falls behind,
		// the simulation keeps registering shockwaves with nothing to drain them. Capping bounds the worst case
		// to a few extra shader batches in one frame instead of an unbounded flush that freezes the game.
		const int MaxActiveEffects = 64;

		// Ring expansion/fade follows logical game ticks, not render frames, so the shockwave plays over the same
		// wall-clock duration at any framerate and freezes while the game is paused.
		// fadeFrames/fadeInFrames are authored as render frames at ReferenceFps; convert to ticks to preserve the look.
		const float ReferenceFps = 60f;
		const float TicksPerSecond = 1000f / 40f; // normal game speed = 40ms timestep = 25 ticks/sec
		const float FramesToTicks = TicksPerSecond / ReferenceFps;

		static readonly string[] CentersKeys = Enumerable.Range(0, MaxDistortionsPerBatch).Select(i => $"ShockCenters[{i}]").ToArray();
		static readonly string[] RadiiKeys = Enumerable.Range(0, MaxDistortionsPerBatch).Select(i => $"RingRadii[{i}]").ToArray();
		static readonly string[] StrengthsKeys = Enumerable.Range(0, MaxDistortionsPerBatch).Select(i => $"Strengths[{i}]").ToArray();

		readonly ShockwaveDistortionRendererInfo info;
		readonly Renderer renderer;
		readonly IShader shader;
		readonly IVertexBuffer<RenderPostProcessPassVertex> buffer;

		readonly List<(WPos Center, float RadiusScale, float StrengthScale, bool Reverse, float ReverseEndRadiusFraction)> pendingDistortions = new();
		readonly List<(WPos Center, float RadiusScale, float StrengthScale, float TicksRemaining, float TotalTicks, float FadeInTicks, bool Reverse, float ReverseEndRadiusFraction)> fadingDistortions = new();

		// World tick at the previous Draw; used to advance the ring by elapsed ticks rather than render frames.
		int lastWorldTick = -1;

		readonly float[] centers = new float[MaxDistortionsPerBatch * 2];
		readonly float[] radii = new float[MaxDistortionsPerBatch];
		readonly float[] strengths = new float[MaxDistortionsPerBatch];

		public ShockwaveDistortionRenderer(ShockwaveDistortionRendererInfo info)
		{
			this.info = info;
			renderer = Game.Renderer;
			shader = renderer.CreateShader(new RenderPostProcessPassShaderBindings("shockwave"));
			buffer = renderer.CreateVertexBuffer(new RenderPostProcessPassVertex[]
			{
				new(-1, -1), new(1, -1), new(1, 1),
				new(1, 1), new(-1, 1), new(-1, -1)
			}, false);
		}

		public void RegisterShockwave(
			WPos center,
			float scale = 1f,
			int fadeFrames = 0,
			int fadeInFrames = 0)
		{
			RegisterShockwave(center, scale, scale, fadeFrames, fadeInFrames, false, 0f);
		}

		public void RegisterShockwave(
			WPos center,
			float radiusScale,
			float strengthScale,
			int fadeFrames,
			int fadeInFrames,
			bool reverse = false,
			float reverseEndRadiusFraction = 0f)
		{
			// Render-only cosmetic state that is drained exclusively by Draw (render tick). While the window
			// is minimized the render tick never runs, so nothing drains these lists, yet the simulation keeps
			// detonating warheads that call this. Dropping the registration while suspended keeps the lists from
			// growing without bound and flushing in one frame on restore. Sync is unaffected: the simulation
			// never reads this state.
			if (Game.Renderer.WindowIsSuspended)
				return;

			// If no shockwave is currently active, Draw has been idle (it only runs while effects exist) so
			// lastWorldTick is stale; reset it, otherwise the first Draw would advance the ring by the whole
			// idle gap and instantly expire this shockwave.
			if (pendingDistortions.Count == 0 && fadingDistortions.Count == 0)
				lastWorldTick = -1;

			if (fadeFrames > 0)
			{
				// Defensive bound for the render-starved (not suspended) case: drop the oldest, most-faded
				// shockwave rather than let the list grow without limit.
				if (fadingDistortions.Count >= MaxActiveEffects)
					fadingDistortions.RemoveAt(0);

				var totalTicks = fadeFrames * FramesToTicks;
				var fadeInTicks = fadeInFrames * FramesToTicks;
				fadingDistortions.Add((center, radiusScale, strengthScale, totalTicks, totalTicks, fadeInTicks, reverse, reverseEndRadiusFraction));
				return;
			}

			if (pendingDistortions.Count >= MaxActiveEffects)
				return;

			pendingDistortions.Add((center, radiusScale, strengthScale, reverse, reverseEndRadiusFraction));
		}

		PostProcessPassType IRenderPostProcessPass.Type => PostProcessPassType.AfterActors;

		bool IRenderPostProcessPass.Enabled => pendingDistortions.Count > 0 || fadingDistortions.Count > 0;

		void IRenderPostProcessPass.Draw(WorldRenderer wr)
		{
			// Advance the ring by the number of game ticks since the last Draw. At high framerates multiple
			// frames render per tick (elapsed == 0, ring holds steady); while paused WorldTick is frozen.
			var worldTick = wr.World.WorldTick;
			var ticksElapsed = lastWorldTick < 0 ? 0f : Math.Max(0, worldTick - lastWorldTick);
			lastWorldTick = worldTick;

			var downscale = renderer.WorldDownscaleFactor;
			var topLeft = wr.Viewport.TopLeft;

			Vector2 ToFb(WPos pos)
			{
				var screenPx = wr.ScreenPxPosition(pos);
				return new Vector2(
					(screenPx.X - topLeft.X) * downscale,
					(screenPx.Y - topLeft.Y) * downscale);
			}

			// Collect all shockwaves for this frame into one flat list (Center, Scale, Progress) so they can
			// be batched together. Progress 0->1 drives the ring's expanding radius and its fade.
			var batch = new List<(WPos Center, float RadiusScale, float StrengthScale, float Progress, bool Reverse, float ReverseEndRadiusFraction)>(pendingDistortions.Count + fadingDistortions.Count);
			foreach (var d in pendingDistortions)
				batch.Add((d.Center, d.RadiusScale, d.StrengthScale, 0f, d.Reverse, d.ReverseEndRadiusFraction));
			pendingDistortions.Clear();

			for (var i = fadingDistortions.Count - 1; i >= 0; i--)
			{
				var d = fadingDistortions[i];
				var ticksPassed = d.TotalTicks - d.TicksRemaining;

				// progress: how far the ring is through its lifetime (0 = just born, 1 = fully expanded/gone).
				var progress = Math.Clamp(ticksPassed / d.TotalTicks, 0f, 1f);

				// Optional ease-in on intensity (FadeInTicks). Most shockwaves use 0.
				var fadeIn = d.FadeInTicks > 0 && ticksPassed < d.FadeInTicks
					? ticksPassed / d.FadeInTicks
					: 1f;

				batch.Add((d.Center, d.RadiusScale, d.StrengthScale * fadeIn, progress, d.Reverse, d.ReverseEndRadiusFraction));

				var remaining = d.TicksRemaining - ticksElapsed;
				if (remaining <= 0f)
					fadingDistortions.RemoveAt(i);
				else
					fadingDistortions[i] = (d.Center, d.RadiusScale, d.StrengthScale, remaining, d.TotalTicks, d.FadeInTicks, d.Reverse, d.ReverseEndRadiusFraction);
			}

			// Draw shockwaves in fixed-size batches. Each batch takes one framebuffer snapshot and runs a
			// single shader pass that loops over all rings, accumulating radial displacement before sampling.
			for (var offset = 0; offset < batch.Count; offset += MaxDistortionsPerBatch)
			{
				var batchSize = Math.Min(MaxDistortionsPerBatch, batch.Count - offset);

				for (var i = 0; i < batchSize; i++)
				{
					var d = batch[offset + i];
					var p = ToFb(d.Center);

					centers[i * 2] = p.X;
					centers[i * 2 + 1] = p.Y;

					// Per-ring animated radius: expands from 0 to MaxRadius over the lifetime.
					var radiusProgress = d.Reverse
						? 1f - d.Progress * (1f - d.ReverseEndRadiusFraction)
						: d.Progress;
					radii[i] = info.MaxRadius * d.RadiusScale * radiusProgress;

					// Strength fades as the ring expands, so it vanishes as it reaches MaxRadius.
					strengths[i] = info.Strength * d.StrengthScale * (1f - d.Progress);
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
				shader.SetVec("RingThickness", info.RingThickness);
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
