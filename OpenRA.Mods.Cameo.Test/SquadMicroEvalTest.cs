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

using System.Collections.Generic;
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class SquadMicroEvalTest
	{
		static readonly BitSet<TargetableType> Ground = new("Ground");
		static readonly BitSet<TargetableType> Air = new("Air");
		static readonly BitSet<TargetableType> None = default;

		static BotUnitProfile Unit(string name, int hp, int cost, double dpt, WDist range,
			BitSet<TargetableType>? targets = null, BitSet<TargetableType>? hits = null)
		{
			var weapons = dpt > 0 ? new[] { new BotWeaponProfile(dpt, range, hits ?? Ground, None, null) } : [];
			return new BotUnitProfile(name, cost, hp, null, 50, false, false, targets ?? Ground, weapons);
		}

		[Test]
		public void FocusPicksFastestKill()
		{
			var squad = new[] { Unit("tank", 100, 100, 10, WDist.FromCells(5)) };
			var targets = new[]
			{
				Unit("wall", 2000, 10, 0, WDist.Zero),   // 200 ticks to kill
				Unit("harvester", 100, 800, 0, WDist.Zero), // 10 ticks to kill
			};
			Assert.That(SquadMicroEvalCA.PickFocusTarget(squad, targets), Is.EqualTo(1));
		}

		[Test]
		public void FocusSkipsUnkillableTargets()
		{
			var squad = new[] { Unit("tank", 100, 100, 10, WDist.FromCells(5)) }; // ground-only guns
			var targets = new[]
			{
				Unit("plane", 50, 500, 5, WDist.FromCells(6), targets: Air), // unreachable: air target vs ground-only weapon
				Unit("tank", 500, 500, 5, WDist.FromCells(5)),
			};
			Assert.That(SquadMicroEvalCA.PickFocusTarget(squad, targets), Is.EqualTo(1));
		}

		[Test]
		public void FocusReturnsMinusOneWhenNothingKillable()
		{
			var squad = new[] { Unit("tank", 100, 100, 10, WDist.FromCells(5)) };
			var targets = new[] { Unit("plane", 50, 500, 5, WDist.FromCells(6), targets: Air) };
			Assert.That(SquadMicroEvalCA.PickFocusTarget(squad, targets), Is.EqualTo(-1));
		}

		[Test]
		public void FocusTiebreakPrefersThreateningTarget()
		{
			var squad = new[] { Unit("tank", 100, 100, 10, WDist.FromCells(5)) };
			var targets = new[]
			{
				Unit("harvester", 100, 800, 0, WDist.Zero),    // same TTK, no threat
				Unit("tank", 100, 800, 9, WDist.FromCells(5)), // same TTK, shoots back
			};
			Assert.That(SquadMicroEvalCA.PickFocusTarget(squad, targets), Is.EqualTo(1));
		}

		[Test]
		public void PullBackAtThreshold()
		{
			Assert.That(SquadMicroEvalCA.ShouldPullBack(30, 100, 30), Is.True);  // exactly at the line
			Assert.That(SquadMicroEvalCA.ShouldPullBack(29, 100, 30), Is.True);
			Assert.That(SquadMicroEvalCA.ShouldPullBack(31, 100, 30), Is.False);
			Assert.That(SquadMicroEvalCA.ShouldPullBack(0, 0, 30), Is.False);    // dead/unknown never pulls
		}

		[Test]
		public void KiteStandoffOnlyWithRangeAdvantage()
		{
			var artillery = Unit("arty", 100, 900, 8, WDist.FromCells(12));
			var tank = Unit("tank", 300, 800, 10, WDist.FromCells(5));
			Assert.That(SquadMicroEvalCA.KiteStandoff(artillery, tank, WDist.FromCells(1)),
				Is.EqualTo(WDist.FromCells(6)));
			Assert.That(SquadMicroEvalCA.KiteStandoff(tank, artillery, WDist.FromCells(1)), Is.Null);
			Assert.That(SquadMicroEvalCA.KiteStandoff(tank, tank, WDist.FromCells(1)), Is.Null); // equal range: no kite
		}

		[Test]
		public void PullBackPointRetreatsDirectlyAwayFromThreat()
		{
			var squadPos = new WPos(5000, 0, 0);
			var threatPos = new WPos(2000, 0, 0);
			var point = SquadMicroEvalCA.PullBackPoint(squadPos, threatPos, WDist.FromCells(3));

			Assert.That(point.X, Is.EqualTo(5000 + WDist.FromCells(3).Length));
			Assert.That(point.Y, Is.EqualTo(0));
		}

		[Test]
		public void PullBackPointDiagonalKeepsDirection()
		{
			// away = (-3000, -4000), |away| = 5000: the point lands at
			// (-3000/5000*1024, -4000/5000*1024) = (-614, -819) after truncation.
			var point = SquadMicroEvalCA.PullBackPoint(new WPos(0, 0, 0), new WPos(3000, 4000, 0), WDist.FromCells(1));
			Assert.That(point.X, Is.EqualTo(-614));
			Assert.That(point.Y, Is.EqualTo(-819));
		}

		[Test]
		public void PullBackPointCoincidentPositionsStayPut()
		{
			var pos = new WPos(1234, 567, 0);
			Assert.That(SquadMicroEvalCA.PullBackPoint(pos, pos, WDist.FromCells(4)), Is.EqualTo(pos));
		}
	}
}
