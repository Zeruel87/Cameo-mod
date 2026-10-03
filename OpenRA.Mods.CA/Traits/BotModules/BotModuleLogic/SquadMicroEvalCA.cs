#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System.Collections.Generic;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// MI groundwork (AI_MASTER_PLAN): the pure evaluation half of budgeted
	/// micro — focus-fire target choice, damaged pull-back, and kite standoff.
	/// Stateless and World-free so tests drive it directly; the order-issuing
	/// half wires into the squad states after CA-4 lands and spends
	/// <see cref="IBotActionBudget"/> actions per micro order (a human cannot
	/// micro forty units at once, so neither may the bot).
	/// </summary>
	public static class SquadMicroEvalCA
	{
		/// <summary>
		/// Index of the target the squad should concentrate on: the one it kills
		/// fastest (lowest aggregate time-to-kill), tiebreak on the threat the
		/// target poses to the squad, then on cost — equal races kill the
		/// dangerous unit, equal threats kill the expensive one. Targets no
		/// squad weapon can hurt are unkillable and never picked. Returns -1
		/// when nothing is killable.
		/// </summary>
		public static int PickFocusTarget(IReadOnlyList<BotUnitProfile> squad, IReadOnlyList<BotUnitProfile> targets)
		{
			var best = -1;
			double bestTtk = 0;
			double bestThreat = 0;
			var bestCost = 0;

			for (var i = 0; i < targets.Count; i++)
			{
				var target = targets[i];
				var squadDps = 0.0;
				foreach (var own in squad)
					squadDps += own.DamagePerTickAgainst(target);

				if (squadDps <= 0 || target.Hp <= 0)
					continue;

				var ttk = target.Hp / squadDps;
				var threat = 0.0;
				foreach (var own in squad)
					threat += target.DamagePerTickAgainst(own);

				if (best < 0
					|| ttk < bestTtk
					|| (ttk == bestTtk && (threat > bestThreat || (threat == bestThreat && target.Cost > bestCost))))
				{
					best = i;
					bestTtk = ttk;
					bestThreat = threat;
					bestCost = target.Cost;
				}
			}

			return best;
		}

		/// <summary>
		/// A unit pulls back when its remaining HP fraction drops to or below
		/// <paramref name="retreatPct"/>. Integer math — no float drift at the
		/// boundary (exactly at the threshold means pull back).
		/// </summary>
		public static bool ShouldPullBack(long hp, long maxHp, int retreatPct)
		{
			return maxHp > 0 && hp * 100 <= maxHp * retreatPct;
		}

		/// <summary>
		/// The standoff distance a unit should keep from <paramref name="target"/>
		/// when it outranges it: the target's own max range plus
		/// <paramref name="margin"/>, so the unit fires from beyond the reply.
		/// Null when the unit holds no range advantage — there is nothing to kite
		/// with and the caller uses normal engage behavior.
		/// </summary>
		public static WDist? KiteStandoff(BotUnitProfile own, BotUnitProfile target, WDist margin)
		{
			if (own.MaxRange <= target.MaxRange)
				return null;

			return target.MaxRange + margin;
		}

		/// <summary>
		/// The waypoint a pulled-back (or kiting) unit runs to:
		/// <paramref name="fromPos"/> continued past itself, directly away from
		/// <paramref name="threatPos"/>, by <paramref name="distance"/>. Passing
		/// the formation centroid yields a rally behind the formation anchor;
		/// passing a unit's own position yields a personal retreat. Returns
		/// <paramref name="fromPos"/> when the two positions coincide.
		/// </summary>
		public static WPos PullBackPoint(WPos fromPos, WPos threatPos, WDist distance)
		{
			var away = fromPos - threatPos;
			var len = away.HorizontalLength;
			if (len <= 0)
				return fromPos;

			return fromPos + new WVec(
				(int)(away.X * (long)distance.Length / len),
				(int)(away.Y * (long)distance.Length / len),
				0);
		}
	}
}
