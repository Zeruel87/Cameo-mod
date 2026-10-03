#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>One squad member as the concave planner sees it. Plain values only.</summary>
	public readonly struct ConcaveMember
	{
		public readonly uint Id;
		public readonly WPos Pos;
		public readonly int MaxRange;
		public readonly int Speed;
		public readonly bool IsInfantry;

		public ConcaveMember(uint id, WPos pos, int maxRange, int speed, bool isInfantry)
		{
			Id = id;
			Pos = pos;
			MaxRange = maxRange;
			Speed = speed;
			IsInfantry = isInfantry;
		}
	}

	/// <summary>Tuning for <see cref="ConcaveEvalCA.Plan"/>; every length is in WDist units.</summary>
	public readonly struct ConcaveParams
	{
		public readonly int Margin;
		public readonly int RankBand;
		public readonly int Spacing;
		public readonly int MinSpacing;
		public readonly int MaxArcDegrees;
		public readonly int RankGap;

		public ConcaveParams(int margin, int rankBand, int spacing, int minSpacing, int maxArcDegrees, int rankGap)
		{
			Margin = margin;
			RankBand = rankBand;
			Spacing = spacing;
			MinSpacing = minSpacing;
			MaxArcDegrees = maxArcDegrees;
			RankGap = rankGap;
		}
	}

	/// <summary>The planned slot of the member at <see cref="Member"/> (index into the input list).</summary>
	public readonly struct ConcaveSlot
	{
		public readonly int Member;
		public readonly WPos Pos;

		/// <summary>0 = innermost arc; each rank band and each overflow arc adds one.</summary>
		public readonly int Rank;

		public ConcaveSlot(int member, WPos pos, int rank)
		{
			Member = member;
			Pos = pos;
			Rank = rank;
		}
	}

	/// <summary>
	/// CV (AI_ARCHITECTURE 12.7a): the pure geometry half of the concave
	/// engagement. Stateless, World-free, integer/long math only, no RNG, so
	/// tests drive it directly. GroundConcaveStateCA does the terrain snap and
	/// issues the orders.
	/// </summary>
	public static class ConcaveEvalCA
	{
		// 1024 WAngle units per turn; one radian = 1024 / (2 pi) units, kept as a ratio
		// (1024 * 10000 / 62832) so arc-length / radius converts with long math.
		const long RadNum = 1024L * 10000;
		const long RadDen = 62832;

		/// <summary>
		/// One slot per member, in input order. Members stand F + MaxRange + Margin from
		/// <paramref name="anchor"/> on arcs centred on the approach axis (anchor to
		/// <paramref name="frontline"/>); a band of members within RankBand of each other
		/// shares an arc at the band's minimum radius. Arc width follows the member count;
		/// past MaxArcDegrees spacing compresses to MinSpacing, then the rest overflow to an
		/// arc RankGap further out. Slots are paired with members by bearing so straight
		/// paths do not cross.
		/// </summary>
		public static ConcaveSlot[] Plan(WPos anchor, WPos frontline, int frontDepth,
			IReadOnlyList<ConcaveMember> members, ConcaveParams p)
		{
			var result = new ConcaveSlot[members.Count];
			if (members.Count == 0)
				return result;

			var axis = frontline - anchor;
			var axisLen = (long)axis.HorizontalLength;
			if (axisLen <= 0)
			{
				axis = new WVec(1024, 0, 0);
				axisLen = 1024;
			}

			// Members ordered by own radius then id: bands are consecutive runs.
			var order = new int[members.Count];
			var radius = new long[members.Count];
			for (var i = 0; i < members.Count; i++)
			{
				order[i] = i;
				radius[i] = (long)Math.Max(0, frontDepth) + members[i].MaxRange + p.Margin;
			}

			Array.Sort(order, (a, b) =>
			{
				var c = radius[a].CompareTo(radius[b]);
				return c != 0 ? c : members[a].Id.CompareTo(members[b].Id);
			});

			var maxArc = (long)p.MaxArcDegrees * 1024 / 360;
			var rank = 0;
			var pos = 0;
			while (pos < order.Length)
			{
				var bandRadius = radius[order[pos]];
				var end = pos;
				while (end < order.Length && radius[order[end]] - bandRadius <= p.RankBand)
					end++;

				// Fill arcs of this band until every member of the band has a slot.
				var arcRadius = bandRadius;
				var remaining = pos;
				while (remaining < end)
				{
					var count = ArcCapacity(members, order, remaining, end, arcRadius, p, maxArc);
					PlaceArc(anchor, axis, axisLen, members, order, remaining, count, arcRadius, p, maxArc, rank, result);
					remaining += count;
					rank++;
					arcRadius += p.RankGap;
				}

				pos = end;
			}

			return result;
		}

		/// <summary>
		/// Objective shape (12.7a, DAWN's assault fan merged in): how many approach prongs a squad
		/// of <paramref name="memberCount"/> splits into, half its size clamped to [min, max]
		/// (never fewer than one).
		/// </summary>
		public static int ProngCount(int memberCount, int minProngs, int maxProngs)
		{
			return Math.Max(1, Math.Min(maxProngs, Math.Max(minProngs, memberCount / 2)));
		}

		/// <summary>
		/// Objective shape: <paramref name="prongCount"/> prong positions on a ring of
		/// <paramref name="radius"/> around <paramref name="objective"/>, fanned over
		/// <paramref name="frontDegrees"/> centred on the bearing objective to
		/// <paramref name="approachFrom"/>, outermost prongs first and last. Wings mirror exactly.
		/// A single prong sits on the approach axis.
		/// </summary>
		public static WPos[] ObjectiveProngs(WPos objective, WPos approachFrom, int radius, int frontDegrees, int prongCount)
		{
			var count = Math.Max(1, prongCount);
			var axis = approachFrom - objective;
			var axisLen = (long)axis.HorizontalLength;
			if (axisLen <= 0)
			{
				axis = new WVec(1024, 0, 0);
				axisLen = 1024;
			}

			var result = new WPos[count];
			for (var i = 0; i < count; i++)
			{
				var offset = count == 1 ? 0 : frontDegrees * i / (count - 1) - frontDegrees / 2;

				// Rotate by |offset| and conjugate for the negative wing so mirrored prongs stay exactly mirrored.
				var rot = WRot.FromYaw(WAngle.FromDegrees(Math.Abs(offset)));
				if (offset < 0)
					rot = -rot;

				var dir = axis.Rotate(rot);
				result[i] = objective + new WVec(
					(int)(dir.X * (long)radius / axisLen),
					(int)(dir.Y * (long)radius / axisLen),
					0);
			}

			return result;
		}

		/// <summary>
		/// Objective shape: one prong slot per member, in input order. A member takes prong
		/// <c>Id % prongs</c> (stable across runs and peers); <see cref="ConcaveSlot.Rank"/> is the
		/// prong index, <see cref="ConcaveSlot.Pos"/> its position (terrain snap is the caller's).
		/// </summary>
		public static ConcaveSlot[] PlanObjective(WPos objective, WPos approachFrom, int radius, int frontDegrees,
			IReadOnlyList<uint> memberIds, int minProngs, int maxProngs)
		{
			var result = new ConcaveSlot[memberIds.Count];
			if (memberIds.Count == 0)
				return result;

			var prongs = ObjectiveProngs(objective, approachFrom, radius, frontDegrees,
				ProngCount(memberIds.Count, minProngs, maxProngs));
			for (var i = 0; i < memberIds.Count; i++)
			{
				var prong = (int)(memberIds[i] % (uint)prongs.Length);
				result[i] = new ConcaveSlot(i, prongs[prong], prong);
			}

			return result;
		}

		static long Width(ConcaveMember m, int spacing)
		{
			return m.IsInfantry ? spacing / 2 : spacing;
		}

		// Angle in WAngle units subtended by an arc length at a radius.
		static long ArcAngle(long length, long radius)
		{
			return radius <= 0 ? 0 : length * RadNum / (RadDen * radius);
		}

		// How many of the members order[from..end) one arc at this radius holds: all of
		// them when they fit at MinSpacing, else the longest prefix that does (at least 1).
		static int ArcCapacity(IReadOnlyList<ConcaveMember> members, int[] order, int from, int end,
			long radius, ConcaveParams p, long maxArc)
		{
			long length = 0;
			var count = 0;
			for (var i = from; i < end; i++)
			{
				length += Width(members[order[i]], p.MinSpacing);
				if (count > 0 && ArcAngle(length, radius) > maxArc)
					break;
				count++;
			}

			return count;
		}

		static void PlaceArc(WPos anchor, WVec axis, long axisLen, IReadOnlyList<ConcaveMember> members, int[] order,
			int from, int count, long radius, ConcaveParams p, long maxArc, int rank, ConcaveSlot[] result)
		{
			// Total arc length at full spacing; compress (down to MinSpacing) only as far as the cap needs.
			long full = 0;
			long min = 0;
			for (var i = from; i < from + count; i++)
			{
				full += Width(members[order[i]], p.Spacing);
				min += Width(members[order[i]], p.MinSpacing);
			}

			long scaleNum = 1, scaleDen = 1;
			if (ArcAngle(full, radius) > maxArc)
			{
				// Target length: the cap at this radius, never below the minimum-spacing length.
				scaleNum = Math.Max(min, maxArc * RadDen * radius / RadNum);
				scaleDen = Math.Max(1, full);
			}

			var ringVec = new WVec(
				(int)(axis.X * radius / axisLen),
				(int)(axis.Y * radius / axisLen),
				0);

			var slotPos = new WPos[count];
			var slotKey = new long[count];
			long cum = 0;
			for (var j = 0; j < count; j++)
			{
				var w = Width(members[order[from + j]], p.Spacing);

				// Twice the slot's signed offset from the arc centre; uniform widths give slot j
				// and slot count-1-j exactly opposite values, so the wings mirror exactly.
				var signed = (2 * cum + w - full) * scaleNum / scaleDen;
				cum += w;

				var angle = (int)ArcAngle(Math.Abs(signed), 2 * radius);

				// Rotate by |angle| and conjugate for the negative wing: a wrapped WAngle halves
				// asymmetrically inside WRot (odd offsets lose half a unit), while -rot is the
				// exact inverse rotation, so mirrored slots stay exactly mirrored.
				var rot = WRot.FromYaw(new WAngle(angle));
				if (signed < 0)
					rot = -rot;

				slotPos[j] = anchor + ringVec.Rotate(rot);
				slotKey[j] = Bearing(slotPos[j] - anchor, axis);
			}

			// Pair by bearing around the anchor: sorted members to sorted slots.
			var slotOrder = new int[count];
			var memberOrder = new int[count];
			var memberKey = new long[count];
			for (var j = 0; j < count; j++)
			{
				slotOrder[j] = j;
				memberOrder[j] = j;
				memberKey[j] = Bearing(members[order[from + j]].Pos - anchor, axis);
			}

			Array.Sort(slotOrder, (a, b) =>
			{
				var c = slotKey[a].CompareTo(slotKey[b]);
				return c != 0 ? c : a.CompareTo(b);
			});

			Array.Sort(memberOrder, (a, b) =>
			{
				var c = memberKey[a].CompareTo(memberKey[b]);
				return c != 0 ? c : members[order[from + a]].Id.CompareTo(members[order[from + b]].Id);
			});

			for (var j = 0; j < count; j++)
			{
				var memberIndex = order[from + memberOrder[j]];
				result[memberIndex] = new ConcaveSlot(memberIndex, slotPos[slotOrder[j]], rank);
			}
		}

		/// <summary>
		/// Monotone integer stand-in for the signed angle of <paramref name="v"/> about the
		/// axis (a diamond pseudo-angle, no trig): sorting by it sorts by bearing.
		/// </summary>
		public static long Bearing(WVec v, WVec axis)
		{
			if (axis.HorizontalLengthSquared == 0)
				return 0;

			// u along the axis, w across it (both scaled by the axis length, which cancels below).
			var u = (long)v.X * axis.X + (long)v.Y * axis.Y;
			var w = (long)v.X * axis.Y - (long)v.Y * axis.X;
			var den = Math.Abs(u) + Math.Abs(w);
			if (den == 0)
				return 0;

			var q = w * 1000000 / den;
			if (u >= 0)
				return q;

			return w >= 0 ? 2000000 - q : -2000000 - q;
		}

		/// <summary>
		/// Distance a member still has to walk before its own weapon reaches the enemy line:
		/// its distance to the anchor, less the enemy front depth and its own range (never negative).
		/// </summary>
		public static long DistanceToRange(WPos pos, WPos anchor, int frontDepth, int maxRange)
		{
			var d = (long)(pos - anchor).HorizontalLength;
			return Math.Max(0, d - Math.Max(0, frontDepth) - maxRange);
		}

		/// <summary>
		/// Staggered commit: delay (ticks after the commit tick) for each member so that
		/// delay + time-to-range is equal for all - the slowest to range starts at once and
		/// everyone arrives in range together. A member that cannot move (speed 0) gets
		/// delay 0 and does not set the pace. Under fire every delay is 0:
		/// holding units idle while they are shot is wrong.
		/// </summary>
		public static int[] CommitDelays(IReadOnlyList<long> distanceToRange, IReadOnlyList<int> speed, bool underFire = false)
		{
			var n = distanceToRange.Count;
			if (underFire)
				return new int[n];

			var time = new long[n];
			long slowest = 0;
			for (var i = 0; i < n; i++)
			{
				if (speed[i] <= 0)
					continue;

				time[i] = (distanceToRange[i] + speed[i] - 1) / speed[i];
				slowest = Math.Max(slowest, time[i]);
			}

			var delays = new int[n];
			for (var i = 0; i < n; i++)
				delays[i] = speed[i] <= 0 ? 0 : (int)(slowest - time[i]);

			return delays;
		}
	}
}
