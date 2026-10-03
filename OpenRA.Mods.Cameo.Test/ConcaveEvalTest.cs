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
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class ConcaveEvalTest
	{
		static readonly WPos Anchor = new(100000, 100000, 0);

		// Approach axis along +X: the army stands east of the anchor.
		static readonly WPos Frontline = new(100000 + 25 * 1024, 100000, 0);

		static readonly ConcaveParams Defaults = new(2048, 2048, 1536, 1024, 150, 2048);

		static ConcaveMember Tank(uint id, WPos pos, int rangeCells = 6, int speed = 71, bool infantry = false)
		{
			return new ConcaveMember(id, pos, rangeCells * 1024, speed, infantry);
		}

		// n tanks on a ring 25 cells out, spread over +-40 degrees, in id order from north to south.
		static List<ConcaveMember> Ring(int n, int rangeCells = 6, bool infantry = false)
		{
			var list = new List<ConcaveMember>();
			for (var i = 0; i < n; i++)
			{
				var deg = n == 1 ? 0 : -40 + 80.0 * i / (n - 1);
				var rad = deg * Math.PI / 180;
				list.Add(Tank((uint)(i + 1), Anchor + new WVec(
					(int)(25 * 1024 * Math.Cos(rad)), (int)(25 * 1024 * Math.Sin(rad)), 0), rangeCells, 71, infantry));
			}

			return list;
		}

		static double Dist(WPos a, WPos b)
		{
			var d = a - b;
			return Math.Sqrt((double)d.X * d.X + (double)d.Y * d.Y);
		}

		// WRot quantises odd WAngle units away (about 100 WDist at 8 cells), so spacing checks allow 20%.
		// Angle of a slot about the anchor relative to the +X axis, in degrees.
		static double Deg(WPos p)
		{
			var d = p - Anchor;
			return Math.Atan2(d.Y, d.X) * 180 / Math.PI;
		}

		static double Span(ConcaveSlot[] slots)
		{
			var angles = slots.Select(s => Deg(s.Pos)).ToList();
			return angles.Max() - angles.Min();
		}

		[Test]
		public void ArcWidthGrowsWithMemberCountAndSpacingHolds()
		{
			var four = ConcaveEvalCA.Plan(Anchor, Frontline, 0, Ring(4), Defaults);
			var eight = ConcaveEvalCA.Plan(Anchor, Frontline, 0, Ring(8), Defaults);
			Assert.That(Span(eight), Is.GreaterThan(Span(four) + 5));

			var sorted = eight.Select(s => s.Pos).OrderBy(Deg).ToList();
			for (var i = 1; i < sorted.Count; i++)
				Assert.That(Dist(sorted[i], sorted[i - 1]), Is.EqualTo(1536).Within(1536 * 0.2), "neighbour spacing " + i);
		}

		[Test]
		public void InfantryStandHalfAsFarApart()
		{
			var slots = ConcaveEvalCA.Plan(Anchor, Frontline, 0, Ring(6, infantry: true), Defaults);
			var sorted = slots.Select(s => s.Pos).OrderBy(Deg).ToList();
			Assert.That(Dist(sorted[1], sorted[0]), Is.EqualTo(768).Within(80));
		}

		[Test]
		public void EverySlotStandsOutsideOwnRangeByTheMargin()
		{
			const int Depth = 3 * 1024;
			var members = Ring(6, 7);
			var slots = ConcaveEvalCA.Plan(Anchor, Frontline, Depth, members, Defaults);
			foreach (var s in slots)
			{
				var d = Dist(s.Pos, Anchor);
				var wanted = Depth + members[s.Member].MaxRange + 2048;
				Assert.That(d, Is.GreaterThanOrEqualTo(Depth + members[s.Member].MaxRange), "never inside own range");
				Assert.That(d, Is.EqualTo(wanted).Within(1024));
			}
		}

		[Test]
		public void MixedRangesFormRanksLongerOutside()
		{
			var members = new List<ConcaveMember>();
			var ring = Ring(8);
			for (var i = 0; i < 8; i++)
				members.Add(Tank(ring[i].Id, ring[i].Pos, i < 4 ? 4 : 13));

			var slots = ConcaveEvalCA.Plan(Anchor, Frontline, 0, members, Defaults);
			Assert.That(slots.Select(s => s.Rank).Distinct().Count(), Is.GreaterThanOrEqualTo(2));

			var shortRanks = slots.Where(s => members[s.Member].MaxRange == 4096).ToList();
			var longRanks = slots.Where(s => members[s.Member].MaxRange == 13 * 1024).ToList();
			Assert.That(longRanks.Min(s => s.Rank), Is.GreaterThan(shortRanks.Max(s => s.Rank)));
			Assert.That(longRanks.Min(s => Dist(s.Pos, Anchor)), Is.GreaterThan(shortRanks.Max(s => Dist(s.Pos, Anchor))));
		}

		[Test]
		public void ArcCapCompressesSpacingThenOverflowsToSecondArc()
		{
			// 8 cell radius: a 150 degree arc is ~21400 long - 13 tanks at 1536, 20 at 1024.
			var compressed = ConcaveEvalCA.Plan(Anchor, Frontline, 0, Ring(20), Defaults);
			Assert.That(compressed.Select(s => s.Rank).Distinct().Count(), Is.EqualTo(1));
			Assert.That(Span(compressed), Is.LessThanOrEqualTo(150 + 1));
			var sorted = compressed.Select(s => s.Pos).OrderBy(Deg).ToList();
			var gap = Dist(sorted[1], sorted[0]);
			Assert.That(gap, Is.LessThan(1536 - 50));
			Assert.That(gap, Is.GreaterThanOrEqualTo(1024 - 60));

			var overflow = ConcaveEvalCA.Plan(Anchor, Frontline, 0, Ring(40), Defaults);
			Assert.That(overflow.Max(s => s.Rank), Is.EqualTo(1));
			var inner = overflow.Where(s => s.Rank == 0).Select(s => Dist(s.Pos, Anchor)).Average();
			var outer = overflow.Where(s => s.Rank == 1).Select(s => Dist(s.Pos, Anchor)).Average();
			Assert.That(outer - inner, Is.EqualTo(2048).Within(30));
			foreach (var s in overflow)
				Assert.That(Span(overflow), Is.LessThanOrEqualTo(150 + 1));
		}

		static bool Cross(WPos a, WPos b, WPos c, WPos d)
		{
			static long Orient(WPos p, WPos q, WPos r) =>
				Math.Sign(((long)q.X - p.X) * ((long)r.Y - p.Y) - ((long)q.Y - p.Y) * ((long)r.X - p.X));

			return Orient(a, b, c) * Orient(a, b, d) < 0 && Orient(c, d, a) * Orient(c, d, b) < 0;
		}

		[Test]
		public void AssignmentByBearingNeverCrossesPaths()
		{
			// Scrambled ids so assignment cannot be by id.
			var members = Ring(9);
			var scrambled = members.Select((m, i) => Tank((uint)(((i * 5) % 9) + 1), m.Pos)).ToList();
			var slots = ConcaveEvalCA.Plan(Anchor, Frontline, 0, scrambled, Defaults);

			for (var i = 0; i < slots.Length; i++)
				for (var j = i + 1; j < slots.Length; j++)
					Assert.That(Cross(scrambled[i].Pos, slots[i].Pos, scrambled[j].Pos, slots[j].Pos), Is.False, $"paths {i}/{j} cross");

			var leftMost = Enumerable.Range(0, 9).OrderBy(i => Deg(scrambled[i].Pos)).First();
			var leftSlot = slots.OrderBy(s => Deg(s.Pos)).First();
			Assert.That(slots[leftMost].Pos, Is.EqualTo(leftSlot.Pos));
		}

		[Test]
		public void SymmetricSlotsMirrorExactlyAboutTheAxis()
		{
			foreach (var n in new[] { 4, 5, 8, 20 })
			{
				var slots = ConcaveEvalCA.Plan(Anchor, Frontline, 2048, Ring(n), Defaults);
				var set = new HashSet<WPos>(slots.Select(s => s.Pos));
				foreach (var s in slots)
				{
					var mirror = new WPos(s.Pos.X, 2 * Anchor.Y - s.Pos.Y, 0);
					Assert.That(set.Contains(mirror), Is.True, $"n={n}: {s.Pos} has no mirror");
				}
			}
		}

		[Test]
		public void StaggerEqualisesArrivalAndSlowestStartsFirst()
		{
			var dist = new long[] { 8000, 6000, 3000, 0, 5000 };
			var speed = new[] { 40, 71, 56, 71, 0 };
			var delays = ConcaveEvalCA.CommitDelays(dist, speed);

			var arrival = new List<long>();
			for (var i = 0; i < dist.Length; i++)
			{
				if (speed[i] == 0)
				{
					Assert.That(delays[i], Is.EqualTo(0), "immobile member never waits");
					continue;
				}

				arrival.Add(delays[i] + (dist[i] + speed[i] - 1) / speed[i]);
			}

			Assert.That(arrival.Max() - arrival.Min(), Is.LessThanOrEqualTo(1));
			Assert.That(delays[0], Is.EqualTo(0), "slowest to range starts at once");
			Assert.That(delays.All(d => d >= 0), Is.True);
		}

		[Test]
		public void UnderFireCommitsEveryoneWithoutDelay()
		{
			var delays = ConcaveEvalCA.CommitDelays(new long[] { 8000, 3000, 0 }, new[] { 40, 71, 71 }, true);
			Assert.That(delays, Is.EqualTo(new[] { 0, 0, 0 }));
		}

		[Test]
		public void SameInputGivesIdenticalOutput()
		{
			var a = ConcaveEvalCA.Plan(Anchor, Frontline, 1024, Ring(13), Defaults);
			var b = ConcaveEvalCA.Plan(Anchor, Frontline, 1024, Ring(13), Defaults);
			Assert.That(a.Select(s => (s.Member, s.Pos, s.Rank)), Is.EqualTo(b.Select(s => (s.Member, s.Pos, s.Rank))));
		}

		[Test]
		public void DegenerateInputsAreSafe()
		{
			Assert.That(ConcaveEvalCA.Plan(Anchor, Frontline, 0, new List<ConcaveMember>(), Defaults), Is.Empty);

			var single = ConcaveEvalCA.Plan(Anchor, Frontline, 0, Ring(1), Defaults);
			Assert.That(single, Has.Length.EqualTo(1));
			Assert.That(Dist(single[0].Pos, Anchor), Is.EqualTo(8192).Within(1024));

			// Coincident anchor and frontline: no axis, a default one is used and the plan still holds.
			var coincident = ConcaveEvalCA.Plan(Anchor, Anchor, 0, Ring(5), Defaults);
			Assert.That(coincident, Has.Length.EqualTo(5));
			Assert.That(coincident.Select(s => s.Pos).Distinct().Count(), Is.EqualTo(5));

			// A zero-range member and a negative front depth do not break the geometry.
			var odd = ConcaveEvalCA.Plan(Anchor, Frontline, -5000, new List<ConcaveMember> { Tank(1, Frontline, 0) }, Defaults);
			Assert.That(Dist(odd[0].Pos, Anchor), Is.EqualTo(2048).Within(2));

			Assert.That(ConcaveEvalCA.CommitDelays(new long[] { 100 }, new[] { 0 }), Is.EqualTo(new[] { 0 }));
		}

		// ---- Objective shape (DAWN's assault fan merged in) ----

		static List<uint> Ids(int n)
		{
			return Enumerable.Range(1, n).Select(i => (uint)i).ToList();
		}

		[Test]
		public void ObjectiveProngCountIsHalfTheSquadClampedToMinAndMax()
		{
			Assert.That(ConcaveEvalCA.ProngCount(1, 3, 8), Is.EqualTo(3));
			Assert.That(ConcaveEvalCA.ProngCount(6, 3, 8), Is.EqualTo(3));
			Assert.That(ConcaveEvalCA.ProngCount(10, 3, 8), Is.EqualTo(5));
			Assert.That(ConcaveEvalCA.ProngCount(40, 3, 8), Is.EqualTo(8));
			Assert.That(ConcaveEvalCA.ProngCount(0, 0, 0), Is.EqualTo(1), "never below one prong");
		}

		[Test]
		public void ObjectiveProngsSpreadOverTheFrontAndMirror()
		{
			// Objective at Anchor, the squad east of it: the approach axis is +X.
			var prongs = ConcaveEvalCA.ObjectiveProngs(Anchor, Frontline, 10 * 1024, 200, 5);
			Assert.That(prongs, Has.Length.EqualTo(5));

			var degrees = prongs.Select(Deg).ToList();
			Assert.That(degrees.Max() - degrees.Min(), Is.EqualTo(200).Within(2), "front width");
			Assert.That(degrees[2], Is.EqualTo(0).Within(1), "middle prong on the approach axis");
			foreach (var pr in prongs)
				Assert.That(Dist(pr, Anchor), Is.EqualTo(10 * 1024).Within(40));

			// Symmetric headings: prong i and prong n-1-i mirror across the axis exactly.
			for (var i = 0; i < prongs.Length / 2; i++)
			{
				var a = prongs[i] - Anchor;
				var b = prongs[prongs.Length - 1 - i] - Anchor;
				Assert.That(a.X, Is.EqualTo(b.X).Within(1), "mirror X " + i);
				Assert.That(a.Y, Is.EqualTo(-b.Y).Within(1), "mirror Y " + i);
			}

			Assert.That(ConcaveEvalCA.ObjectiveProngs(Anchor, Frontline, 10 * 1024, 200, 1)[0].X,
				Is.EqualTo(Anchor.X + 10 * 1024).Within(1), "a single prong takes the axis");
		}

		[Test]
		public void ObjectivePlanGivesEveryMemberAHeadingDeterministically()
		{
			var ids = Ids(13);
			var a = ConcaveEvalCA.PlanObjective(Anchor, Frontline, 10 * 1024, 200, ids, 3, 8);
			var b = ConcaveEvalCA.PlanObjective(Anchor, Frontline, 10 * 1024, 200, ids, 3, 8);

			Assert.That(a, Has.Length.EqualTo(13));
			Assert.That(a.Select(s => s.Member), Is.EqualTo(Enumerable.Range(0, 13)), "one slot per member, input order");
			Assert.That(a.Select(s => (s.Pos, s.Rank)), Is.EqualTo(b.Select(s => (s.Pos, s.Rank))));
			Assert.That(a.Select(s => s.Rank).Max(), Is.EqualTo(5), "13 members -> 6 prongs");
			Assert.That(a.Select(s => s.Rank).Distinct().Count(), Is.EqualTo(6));

			// Same id, same prong whatever the squad order or size of the others.
			Assert.That(a[6].Rank, Is.EqualTo((int)(7 % 6u)));

			Assert.That(ConcaveEvalCA.PlanObjective(Anchor, Frontline, 10 * 1024, 200, new List<uint>(), 3, 8), Is.Empty);
			Assert.That(ConcaveEvalCA.PlanObjective(Anchor, Anchor, 10 * 1024, 200, Ids(4), 3, 8), Has.Length.EqualTo(4),
				"coincident anchor and approach: default axis");
		}
	}
}
