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
using OpenRA.Support;

namespace OpenRA.Mods.Cameo.Graphics
{
	public static class LightningGeometry
	{
		// Fractal midpoint displacement shared by the main bolt and its forking branches. Start with the
		// straight src->tgt segment, then each generation split every segment at its midpoint and nudge it
		// perpendicular to that LOCAL segment (so sub-wiggles follow the orientation of their parent wiggle
		// = self-similar fractal detail). The displacement shrinks by 'roughness' each generation; the
		// endpoints are never moved, so the bolt stays pinned to the firing point and the target.
		// Passing a fresh MersenneTwister(seed) yields a deterministic (frozen, non-flickering) shape.
		public static List<Vector3> MidpointPath(in Vector3 src, in Vector3 tgt, float maxDev,
			int generations, float roughness, MersenneTwister rnd)
		{
			var points = new List<Vector3> { src, tgt };
			if (maxDev < 0.5f)
				return points;

			var offset = maxDev;
			var gens = Math.Clamp(generations, 1, 8);
			for (var g = 0; g < gens; g++)
			{
				var next = new List<Vector3>(points.Count * 2) { points[0] };
				for (var k = 0; k < points.Count - 1; k++)
				{
					var a = points[k];
					var b = points[k + 1];
					var mx = (a.X + b.X) * 0.5f;
					var my = (a.Y + b.Y) * 0.5f;
					var mz = (a.Z + b.Z) * 0.5f;

					var sx = b.X - a.X;
					var sy = b.Y - a.Y;
					var slen = (float)Math.Sqrt(sx * sx + sy * sy);
					if (slen > 0.001f)
					{
						var px = -sy / slen;
						var py = sx / slen;
						var disp = (rnd.NextFloat() * 2f - 1f) * offset;
						mx += px * disp;
						my += py * disp;
					}

					next.Add(new Vector3(mx, my, mz));
					next.Add(b);
				}

				points = next;
				offset *= roughness;
			}

			return points;
		}
	}
}
