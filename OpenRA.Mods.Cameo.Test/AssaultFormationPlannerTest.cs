#region Copyright & License Information
/*
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
	// AF-1 (the line-of-death fix): the fan-out arc planner. Slots must cover the
	// ring's far side (not cluster on the approach corridor), the same inputs must
	// plan identically on every peer (integer LUT math, no RNG), and members must
	// keep their own side of the target — a unit east of the objective belongs on
	// the arc's east end, not walked across to the west.
	[TestFixture]
	public class AssaultFormationPlannerTest
	{
		static readonly CPos Target = new(50, 50);

		static List<(CPos Cell, uint ActorId)> Column(int x, int y0, int n)
		{
			// A tight column south of the target — the "line of death" shape:
			// every member in nearly the same cell column, one bearing in.
			var units = new List<(CPos Cell, uint ActorId)>();
			for (var i = 0; i < n; i++)
				units.Add((new CPos(x + (i % 2), y0 + i / 2), (uint)(100 + i)));
			return units;
		}

		static int BearingOf(CPos from, CPos to) =>
			WAngle.ArcTan(to.Y - from.Y, to.X - from.X).Angle;

		[Test]
		public void SlotsSpreadAcrossTheFarSideNotACluster()
		{
			// A symmetric spread due south of the target: the approach bearing is
			// exactly north, so the arc spans the whole far half.
			var units = new List<(CPos Cell, uint ActorId)>
			{
				(new CPos(48, 60), 1), (new CPos(52, 60), 2),
				(new CPos(50, 61), 3), (new CPos(49, 62), 4),
				(new CPos(51, 62), 5), (new CPos(50, 63), 6),
				(new CPos(48, 64), 7), (new CPos(52, 64), 8),
			};
			var plan = AssaultFormationPlanner.PlanSlots(units, Target, 8, 180, _ => true, out var arc);

			Assert.That(plan, Has.Length.EqualTo(8));
			Assert.That(arc, Has.Length.EqualTo(8),
				"eight slots on a radius-8 half-ring must not collapse into a cluster");

			// Far side of a southern approach is the north half: every slot at or
			// above the target row, and the arc must reach both flanks.
			Assert.That(arc.All(c => c.Y <= Target.Y), Is.True,
				"the arc wraps the far side — no slot may sit back on the approach side");
			Assert.That(arc.Min(c => c.X), Is.LessThanOrEqualTo(Target.X - 6), "west flank must be covered");
			Assert.That(arc.Max(c => c.X), Is.GreaterThanOrEqualTo(Target.X + 6), "east flank must be covered");
			Assert.That(plan.Distinct().Count(), Is.EqualTo(arc.Length),
				"with enough ring cells every member gets its own slot");
		}

		[Test]
		public void SameInputPlansIdentically()
		{
			var units = Column(49, 60, 8);
			var first = AssaultFormationPlanner.PlanSlots(units, Target, 8, 180, _ => true, out var arcA);
			var second = AssaultFormationPlanner.PlanSlots(units, Target, 8, 180, _ => true, out var arcB);

			Assert.That(second, Is.EqualTo(first), "sync code: identical inputs must plan identically");
			Assert.That(arcB, Is.EqualTo(arcA));
		}

		[Test]
		public void MembersKeepTheirOwnSideOfTheTarget()
		{
			// Two members flanking the approach: the eastern member must take the
			// arc's eastern end, the western the western — a swapped pair would
			// send each across the other's lane.
			var west = (Cell: new CPos(44, 60), ActorId: (uint)1);
			var east = (Cell: new CPos(56, 60), ActorId: (uint)2);
			var units = new List<(CPos Cell, uint ActorId)> { west, east };

			var plan = AssaultFormationPlanner.PlanSlots(units, Target, 8, 180, _ => true, out _);

			var westSlot = plan[0];
			var eastSlot = plan[1];
			Assert.That(westSlot.X, Is.LessThan(Target.X), "the member west of the target fans west");
			Assert.That(eastSlot.X, Is.GreaterThan(Target.X), "the member east of the target fans east");

			// And measured in ring angle, each slot is the nearer end for its member:
			// circular distance to the taken slot must beat the distance to the other.
			var westBearing = BearingOf(Target, west.Cell);
			var eastBearing = BearingOf(Target, east.Cell);
			var westSlotAngle = BearingOf(Target, westSlot);
			var eastSlotAngle = BearingOf(Target, eastSlot);
			int Circ(int a, int b) => Math.Min(Math.Abs(a - b), 1024 - Math.Abs(a - b));
			Assert.That(Circ(westBearing, westSlotAngle), Is.LessThanOrEqualTo(Circ(westBearing, eastSlotAngle)));
			Assert.That(Circ(eastBearing, eastSlotAngle), Is.LessThanOrEqualTo(Circ(eastBearing, westSlotAngle)));
		}

		[Test]
		public void DegenerateInputsAreSafe()
		{
			// Nothing to place.
			var empty = AssaultFormationPlanner.PlanSlots(
				new List<(CPos Cell, uint ActorId)>(), Target, 8, 180, _ => true, out var emptyArc);
			Assert.That(empty, Is.Empty);
			Assert.That(emptyArc, Is.Empty);

			// A single member fans to the far-side point alone.
			var one = AssaultFormationPlanner.PlanSlots(
				new List<(CPos Cell, uint ActorId)> { (new CPos(50, 60), 7) },
				Target, 8, 180, _ => true, out var oneArc);
			Assert.That(one, Has.Length.EqualTo(1));
			Assert.That(oneArc, Has.Length.EqualTo(1));
			Assert.That(one[0].Y, Is.LessThan(Target.Y), "the lone slot still sits on the far side");

			// A zero radius collapses onto the objective — the pre-AF-1 behaviour.
			var zero = AssaultFormationPlanner.PlanSlots(
				Column(49, 60, 4), Target, 0, 180, _ => true, out _);
			Assert.That(zero.All(c => c == Target), Is.True);

			// No usable ring cell (e.g. target ring entirely off-map): everyone
			// folds onto the target cell, the honest fallback.
			var walled = AssaultFormationPlanner.PlanSlots(
				Column(49, 60, 4), Target, 8, 180, _ => false, out var walledArc);
			Assert.That(walledArc, Is.Empty);
			Assert.That(walled.All(c => c == Target), Is.True);
		}

		[Test]
		public void MoreMembersThanUsableSlotsFoldOntoTheObjective()
		{
			// A sliver of an arc at short radius holds few distinct cells; the
			// overflow must degrade to the target cell, not drop the members.
			var units = Column(49, 60, 12);
			var plan = AssaultFormationPlanner.PlanSlots(units, Target, 2, 1, _ => true, out var arc);

			Assert.That(plan, Has.Length.EqualTo(12));
			Assert.That(arc.Length, Is.LessThan(12), "a sliver arc cannot hold twelve distinct cells");
			Assert.That(plan.Count(c => c == Target), Is.GreaterThan(0),
				"members without a ring slot get the objective — never no order at all");
			Assert.That(plan.All(c => c == Target || arc.Contains(c)), Is.True,
				"every assignment is a real slot or the target cell");
		}

		[Test]
		public void NearestSlotIndexPicksTheClosestCell()
		{
			var slots = new List<CPos> { new(40, 50), new(50, 42), new(60, 50) };
			Assert.That(AssaultFormationPlanner.NearestSlotIndex(new CPos(59, 50), slots), Is.EqualTo(2));
			Assert.That(AssaultFormationPlanner.NearestSlotIndex(new CPos(41, 51), slots), Is.EqualTo(0));
			Assert.That(AssaultFormationPlanner.NearestSlotIndex(new CPos(5, 5), Array.Empty<CPos>()), Is.EqualTo(-1));
		}
	}
}
