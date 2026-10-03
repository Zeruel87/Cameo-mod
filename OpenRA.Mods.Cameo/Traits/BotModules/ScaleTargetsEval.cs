#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>One category's line in the growth law: every fraction in thousandths (1000 = 1.0).</summary>
	public readonly struct ScaleLine
	{
		public readonly int Min, Max, RatioMin, RatioMax, Margin, Growth, Floor;

		public ScaleLine(int min, int max, int ratioMin, int ratioMax, int margin, int growth, int floor)
		{
			Min = min;
			Max = max;
			RatioMin = ratioMin;
			RatioMax = ratioMax;
			Margin = margin;
			Growth = growth;
			Floor = floor;
		}
	}

	/// <summary>
	/// Scale targets (DESIGN 19.10, AI_ARCHITECTURE 12.22): the pure growth law. World-free and float-free:
	/// bots run in lockstep, so every fraction is an integer in thousandths and the only rounding is ONE floor at
	/// the end.
	///
	///   f        = tier / (tierCount - 1)
	///   own      = lerp(Min, Max, f) x (1 + Growth x game minutes / 60)
	///   enemy    = lerp(RatioMin, RatioMax, f) x seen x (1 + Margin x unscouted) / team size
	///   target   = floor(P x max(own, enemy)), clamped to [Floor, cap]
	/// </summary>
	public static class ScaleTargetsEval
	{
		/// <summary>The fixed-point scale: 1000 = 1.0.</summary>
		public const int One = 1000;

		/// <summary>lerp(min, max) at tier / (tierCount - 1), in thousandths. A one-tier ladder reads min.</summary>
		public static long Lerp(int minMilli, int maxMilli, int tier, int tierCount)
		{
			var steps = tierCount - 1;
			if (steps <= 0)
				return minMilli;

			var t = Math.Clamp(tier, 0, steps);
			return minMilli + ((long)(maxMilli - minMilli) * t) / steps;
		}

		/// <summary>1 + growth x minutes / 60, in thousandths; growth is per HOUR and uncapped (long games grow without limit).</summary>
		public static long GrowthFactor(int growthPerHourMilli, long gameTicks, int ticksPerMinute)
		{
			if (ticksPerMinute <= 0 || gameTicks <= 0)
				return One;

			return One + (long)growthPerHourMilli * gameTicks / (60L * ticksPerMinute);
		}

		/// <summary>
		/// One axis' lean factor in thousandths: <paramref name="leanPercent"/> (signed, at the pole) scaled by how far
		/// the axis (0..100, 50 neutral) sits from the middle. Neutral or zero lean is exactly 1000.
		/// </summary>
		public static int AxisLeanFactor(int axis, int leanPercent)
		{
			if (leanPercent == 0)
				return One;

			var a = Math.Clamp(axis, 0, 100);
			return Math.Max(0, One + leanPercent * (a - 50) * 10 / 50);
		}

		/// <summary>P_k: the personality multiplier times each axis lean, in thousandths.</summary>
		public static int Personality(int personalityMilli, int turtleRushFactor, int techExpansionFactor)
		{
			var p = (long)personalityMilli * turtleRushFactor / One * techExpansionFactor / One;
			return (int)Math.Clamp(p, 0, int.MaxValue);
		}

		/// <summary>
		/// The own-side term in thousandths of a unit: lerp x growth, times <paramref name="ownScale"/> (1 for counts,
		/// the personality SquadValue for the army).
		/// </summary>
		public static long Own(in ScaleLine line, int tier, int tierCount, long gameTicks, int ticksPerMinute, long ownScale)
		{
			return ownScale * Lerp(line.Min, line.Max, tier, tierCount)
				* GrowthFactor(line.Growth, gameTicks, ticksPerMinute) / One;
		}

		/// <summary>The enemy term in thousandths of a unit: seen x ratio line x (1 + margin x unscouted share) over the team.</summary>
		public static long Enemy(in ScaleLine line, int tier, int tierCount, long seen, int unscoutedMilli, int teamSize)
		{
			if (seen <= 0)
				return 0;

			var ratio = Lerp(line.RatioMin, line.RatioMax, tier, tierCount);
			var margin = One + (long)line.Margin * Math.Clamp(unscoutedMilli, 0, One) / One;
			return ratio * seen * margin / One / Math.Max(1, teamSize);
		}

		/// <summary>
		/// The target. <paramref name="cap"/> is the physical cap (negative: none); it wins over the floor.
		/// </summary>
		public static int Target(in ScaleLine line, int tier, int tierCount, long gameTicks, int ticksPerMinute,
			long seen, int unscoutedMilli, int teamSize, int personalityMilli, long ownScale, int cap)
		{
			var own = Own(line, tier, tierCount, gameTicks, ticksPerMinute, ownScale);
			var enemy = Enemy(line, tier, tierCount, seen, unscoutedMilli, teamSize);
			var best = Math.Max(own, enemy);

			// milli x milli -> divide by One twice; the second division IS the single floor.
			var scaled = best * personalityMilli / One / One;
			var target = (int)Math.Clamp(scaled, line.Floor, int.MaxValue);
			return cap >= 0 ? Math.Min(target, cap) : target;
		}
	}
}
