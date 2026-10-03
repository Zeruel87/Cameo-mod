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
using OpenRA.Graphics;
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Support;

namespace OpenRA.Mods.Cameo.Graphics
{
	// Draws an instant electric bolt as a procedural fractal arc: the channel is built by recursive
	// midpoint displacement (each segment splits at its midpoint, nudged perpendicular, with the nudge
	// shrinking each generation) so every wiggle sprouts smaller self-similar sub-wiggles, like real
	// lightning. A white-hot additive core, an additive blue glow, fractal forking branches (each a jagged
	// mini-bolt that can sub-fork) and glowing plasma orbs (with radiating spark hairs) at both ends
	// complete it. The geometry is built in screen space
	// each frame (cosmetic, CosmeticRandom-driven, so it flickers and is not part of the simulation).
	public sealed class LightningRenderable : IRenderable, IFinalizedRenderable
	{
		readonly WVec length;
		readonly int generations;
		readonly float roughness;
		readonly WDist amplitude;
		readonly int branches;
		readonly WDist branchLength;
		readonly int branchGenerations;
		readonly float subBranchChance;
		readonly WDist nodeRadius;
		readonly int nodeHairs;
		readonly WDist nodeHairLength;
		readonly Color coreColor;
		readonly Color glowColor;
		readonly WDist coreWidth;
		readonly WDist glowWidth;
		readonly int glowAlpha;
		readonly float glowScale;
		readonly float glowIntensity;

		public LightningRenderable(WPos pos, int zOffset, in WVec length,
			int generations, float roughness, WDist amplitude,
			int branches, WDist branchLength, int branchGenerations, float subBranchChance,
			WDist nodeRadius, int nodeHairs, WDist nodeHairLength,
			Color coreColor, Color glowColor, WDist coreWidth,
			WDist glowWidth, int glowAlpha, float glowScale, float glowIntensity)
		{
			Pos = pos;
			ZOffset = zOffset;
			this.length = length;
			this.generations = generations;
			this.roughness = roughness;
			this.amplitude = amplitude;
			this.branches = branches;
			this.branchLength = branchLength;
			this.branchGenerations = branchGenerations;
			this.subBranchChance = subBranchChance;
			this.nodeRadius = nodeRadius;
			this.nodeHairs = nodeHairs;
			this.nodeHairLength = nodeHairLength;
			this.coreColor = coreColor;
			this.glowColor = glowColor;
			this.coreWidth = coreWidth;
			this.glowWidth = glowWidth;
			this.glowAlpha = glowAlpha;
			this.glowScale = glowScale;
			this.glowIntensity = glowIntensity;
		}

		public WPos Pos { get; }
		public int ZOffset { get; }
		public bool IsDecoration => true;

		LightningRenderable With(WPos pos, int zOffset) =>
			new(pos, zOffset, length, generations, roughness, amplitude,
				branches, branchLength, branchGenerations, subBranchChance, nodeRadius, nodeHairs, nodeHairLength,
				coreColor, glowColor, coreWidth, glowWidth, glowAlpha, glowScale, glowIntensity);

		public IRenderable WithZOffset(int newOffset) => With(Pos, newOffset);
		public IRenderable OffsetBy(in WVec vec) => With(Pos + vec, ZOffset);
		public IRenderable AsDecoration() => this;

		public IFinalizedRenderable PrepareRender(WorldRenderer wr) => this;
		public void RenderDebugGeometry(WorldRenderer wr) { }
		public Rectangle ScreenBounds(WorldRenderer wr) => Rectangle.Empty;

		public void Render(WorldRenderer wr)
		{
			if (length.Length == 0)
				return;

			if (wr.World.FogObscures(Pos) && wr.World.FogObscures(Pos + length))
				return;

			var cr = Game.Renderer.WorldRgbaColorRenderer;
			var src = wr.Screen3DPosition(Pos);
			var tgt = wr.Screen3DPosition(Pos + length);

			// All widths/sizes come from fixed world distances projected to screen, so they stay
			// constant regardless of the bolt's reach (matching the existing core/glow widths).
			var coreScreen = wr.ScreenVector(new WVec(coreWidth, WDist.Zero, WDist.Zero))[0];
			var glowScreen = wr.ScreenVector(new WVec(glowWidth, WDist.Zero, WDist.Zero))[0];
			var ampScreen = Math.Abs(wr.ScreenVector(new WVec(amplitude, WDist.Zero, WDist.Zero))[0]);
			var branchScreen = Math.Abs(wr.ScreenVector(new WVec(branchLength, WDist.Zero, WDist.Zero))[0]);

			var dx = tgt.X - src.X;
			var dy = tgt.Y - src.Y;
			var screenLen = (float)Math.Sqrt(dx * dx + dy * dy);

			// The largest (first-generation) displacement; capped so a near-point-blank bolt doesn't
			// swing wider than it is long.
			var maxDev = Math.Min(ampScreen, 0.45f * screenLen);

			var rnd = Game.CosmeticRandom;
			var main = LightningGeometry.MidpointPath(src, tgt, maxDev, generations, roughness, rnd);

			// Soft gaussian bloom that FOLLOWS the bolt: the GlowRenderer only glows straight segments,
			// so we approximate the jagged path with a few short beams chained along it (instead of one
			// straight muzzle-to-target capsule). Gated by the "Weapon Glow Effects" setting; the segment
			// count is capped per bolt so the post-process batch count stays bounded no matter how many
			// bolts fire at once. Screen points are projected back to ground positions because the
			// GlowRenderer batches in world space.
			if (Game.Settings.Graphics.LaserGlow && glowScale > 0f && main.Count > 1)
			{
				var glow = wr.World.WorldActor.TraitOrDefault<GlowRenderer>();
				if (glow != null)
				{
					const int MaxGlowSegments = 8;
					var stepN = Math.Max(1, (main.Count - 1) / MaxGlowSegments);
					var prev = wr.ProjectedPosition(int2.FromVector(main[0]));
					for (var i = stepN; i < main.Count; i += stepN)
					{
						var cur = wr.ProjectedPosition(int2.FromVector(main[i]));
						glow.RegisterGlow(prev, cur, glowColor, glowScale, intensity: glowIntensity);
						prev = cur;
					}

					var end = wr.ProjectedPosition(int2.FromVector(main[^1]));
					if (end != prev)
						glow.RegisterGlow(prev, end, glowColor, glowScale, intensity: glowIntensity);
				}
			}

			// Thin additive bolt drawn FROM the path: a tight inner glow and a hot near-white core. This
			// is the always-on baseline (kept thin so it doesn't fatten the bolt); the soft wide halo is
			// the gaussian GlowRenderer bloom above, which only kicks in with the Weapon Glow setting.
			// NOTE: segments are drawn DISCONNECTED (no miter joins). RgbaColorRenderer's connected-line
			// path mitres corners via a line intersection that "behaves badly" for near-parallel segments;
			// the sharp fractal kinks would blow that mitre vertex out to near-infinity and streak a giant
			// quad across the screen. Independent butt-capped segments avoid that, and the joints are
			// invisible on a thin additive bolt.
			var glowOuter = Color.FromArgb(glowAlpha, glowColor);
			var glowInner = Color.FromArgb(Math.Min(255, glowAlpha + 50), glowColor);
			cr.DrawLine(main, glowScreen, glowOuter, false, BlendMode.Additive);
			cr.DrawLine(main, glowScreen * 0.5f, glowInner, false, BlendMode.Additive);
			cr.DrawLine(main, coreScreen, coreColor, false, BlendMode.Additive);

			for (var b = 0; b < branches; b++)
			{
				// Root each branch on an ACTUAL vertex of the jagged path, not the straight muzzle->target
				// chord. The visible bolt has wandered up to maxDev off that chord, so a chord-rooted branch
				// starts in empty space beside the bolt (detached) or stabs across it (crossed). Sprouting
				// from a real path vertex keeps every fork attached, and forking relative to the LOCAL bolt
				// direction there looks more natural than relative to the overall chord.
				var idx = Math.Clamp((int)((0.2f + 0.6f * rnd.NextFloat()) * (main.Count - 1)), 0, main.Count - 2);
				var root = main[idx];
				var nb = main[idx + 1];
				var localAng = (float)Math.Atan2(nb.Y - root.Y, nb.X - root.X);
				var ang = localAng + (rnd.NextFloat() < 0.5f ? -1f : 1f) * (0.4f + 0.7f * rnd.NextFloat());
				var blen = branchScreen * (0.7f + 0.6f * rnd.NextFloat());
				DrawFractalBranch(cr, root, ang, blen, 0, coreScreen, glowScreen, rnd);
			}

			// Glowing plasma "balls" with radiating spark hairs where the bolt grounds: one at the
			// firing point, one at the impact point.
			if (nodeRadius.Length > 0 && nodeHairs > 0)
			{
				var nodeScreen = Math.Abs(wr.ScreenVector(new WVec(nodeRadius, WDist.Zero, WDist.Zero))[0]);
				var hairLenScreen = Math.Abs(wr.ScreenVector(new WVec(nodeHairLength, WDist.Zero, WDist.Zero))[0]);
				var hairDev = nodeScreen * 0.35f;
				DrawNode(cr, src, nodeScreen, hairLenScreen, hairDev, coreScreen, glowScreen, rnd);
				DrawNode(cr, tgt, nodeScreen, hairLenScreen, hairDev, coreScreen, glowScreen, rnd);
			}
		}

		static List<Vector3> BuildBranch(in Vector3 root, float ang, float length, float devScreen, MersenneTwister rnd)
		{
			var dirX = (float)Math.Cos(ang);
			var dirY = (float)Math.Sin(ang);
			var perpX = -dirY;
			var perpY = dirX;
			const int n = 4;

			var pts = new List<Vector3>();
			for (var i = 0; i <= n; i++)
			{
				var t = i / (float)n;
				var dev = (i == 0 || i == n ? 0f : 1f) * (rnd.NextFloat() * 2f - 1f) * devScreen * (1f - t);
				pts.Add(new Vector3(
					root.X + dirX * length * t + perpX * dev,
					root.Y + dirY * length * t + perpY * dev,
					root.Z));
			}

			return pts;
		}

		// A branch as a jagged mini-bolt: the same fractal midpoint-displacement channel as the main bolt
		// (so it looks like real forked lightning, not a smooth whisker), drawn from `root` along `ang`.
		// It may recursively spawn a shorter, thinner sub-fork from a point on its first half, depth-capped
		// and probability-gated so the per-frame segment count stays bounded.
		void DrawFractalBranch(RgbaColorRenderer cr, in Vector3 root, float ang, float length,
			int depth, float coreScreen, float glowScreen, MersenneTwister rnd)
		{
			const int MaxDepth = 2;
			const float MinSubLengthScreen = 6f;

			var tip = new Vector3(
				root.X + (float)Math.Cos(ang) * length,
				root.Y + (float)Math.Sin(ang) * length,
				root.Z);

			// Wiggle scales with the branch's own length so short forks don't thrash; reuse the main
			// bolt's roughness for matching self-similar character.
			var dev = length * 0.18f;
			var gens = Math.Clamp(branchGenerations, 1, 8);
			var pts = LightningGeometry.MidpointPath(root, tip, dev, gens, roughness, rnd);
			DrawBranch(cr, pts, coreScreen, glowScreen);

			if (depth < MaxDepth && length > MinSubLengthScreen
				&& subBranchChance > 0f && rnd.NextFloat() < subBranchChance)
			{
				// Sub-fork off a point in the first half of this branch.
				var j = Math.Clamp(pts.Count / 4 + (int)(rnd.NextFloat() * pts.Count / 4f), 1, pts.Count - 1);
				var subAng = ang + (rnd.NextFloat() < 0.5f ? -1f : 1f) * (0.4f + 0.5f * rnd.NextFloat());
				DrawFractalBranch(cr, pts[j], subAng, length * (0.4f + 0.2f * rnd.NextFloat()),
					depth + 1, coreScreen, glowScreen, rnd);
			}
		}

		void DrawBranch(RgbaColorRenderer cr, List<Vector3> pts, float coreScreen, float glowScreen)
		{
			var count = pts.Count - 1;
			for (var i = 0; i < count; i++)
			{
				var fade = 1f - i / (float)count;                    // taper brightness toward the tip
				var ga = (int)(glowAlpha * 0.7f * fade);
				var ca = (int)(255 * fade);
				if (ga > 0)
					cr.DrawLine(pts[i], pts[i + 1], glowScreen * 0.5f, Color.FromArgb(ga, glowColor), BlendMode.Additive);
				if (ca > 0)
					cr.DrawLine(pts[i], pts[i + 1], coreScreen * 0.7f, Color.FromArgb(ca, coreColor), BlendMode.Additive);
			}
		}

		void DrawNode(RgbaColorRenderer cr, in Vector3 c, float radius, float hairLen, float hairDev,
			float coreScreen, float glowScreen, MersenneTwister rnd)
		{
			// Soft additive orb: a faint wide halo, a brighter mid, then a hot near-white centre.
			DrawDisc(cr, c, radius, Color.FromArgb(45, glowColor));
			DrawDisc(cr, c, radius * 0.6f, Color.FromArgb(95, glowColor));
			DrawDisc(cr, c, radius * 0.32f, Color.FromArgb(230, coreColor));

			// Short jagged filaments radiating evenly around the orb (each slot jittered so it flickers).
			for (var i = 0; i < nodeHairs; i++)
			{
				var ang = (i + (rnd.NextFloat() - 0.5f)) / nodeHairs * 2f * (float)Math.PI;
				var len = hairLen * (0.6f + 0.7f * rnd.NextFloat());
				DrawBranch(cr, BuildBranch(c, ang, len, hairDev, rnd), coreScreen, glowScreen);
			}
		}

		static void DrawDisc(RgbaColorRenderer cr, in Vector3 c, float radius, Color color)
		{
			if (radius < 0.5f)
				return;

			cr.FillEllipse(
				new Vector3(c.X - radius, c.Y - radius, c.Z),
				new Vector3(c.X + radius, c.Y + radius, c.Z),
				color, BlendMode.Additive);
		}
	}
}
