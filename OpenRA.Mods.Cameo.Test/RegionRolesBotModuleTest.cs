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

using System.Linq;
using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public sealed class RegionRolesBotModuleTest
	{
		static RegionRoleState Claimed(int id, RegionRole role = RegionRole.None, int roleSince = -100000, int buildings = 0, int value = 0, bool bordersEnemy = false)
		{
			return new RegionRoleState(id)
			{
				Claimed = true,
				Role = role,
				RoleSinceTick = roleSince,
				OwnBuildings = buildings,
				Value = value,
				BordersEnemy = bordersEnemy,
			};
		}

		[Test]
		public void SecurityScoreHalvesInsteadOfFlooring()
		{
			// A sealed pocket reads 100; heavier exposure approaches but never reaches 0 —
			// a moderately open region and a hopeless one still rank differently.
			var sealedPocket = RegionRolesBotModule.SecurityScore(0, 0, 12, 3, 60);
			var oneDoor = RegionRolesBotModule.SecurityScore(1, 8, 12, 3, 60);
			var manyDoors = RegionRolesBotModule.SecurityScore(4, 40, 12, 3, 60);
			var hopeless = RegionRolesBotModule.SecurityScore(10, 200, 12, 3, 60);

			Assert.That(sealedPocket, Is.EqualTo(100));
			Assert.That(oneDoor, Is.GreaterThan(manyDoors));
			Assert.That(manyDoors, Is.GreaterThan(hopeless));
			Assert.That(hopeless, Is.GreaterThan(0));
		}

		[Test]
		public void ValueScoreIsTheWeightedMean()
		{
			Assert.That(RegionRolesBotModule.ValueScore(100, 100, 100, 100, 60, 80), Is.EqualTo(100));
			Assert.That(RegionRolesBotModule.ValueScore(0, 0, 0, 100, 60, 80), Is.EqualTo(0));
			Assert.That(RegionRolesBotModule.ValueScore(50, 0, 0, 100, 60, 80), Is.EqualTo(50 * 100 / 240));
			Assert.That(RegionRolesBotModule.ValueScore(80, 80, 80, 0, 0, 0), Is.EqualTo(0));
		}

		[Test]
		public void CoreIsPinnedToHomeWhenHeld()
		{
			var states = new[] { Claimed(0, buildings: 5), Claimed(1, buildings: 9), Claimed(2, buildings: 1) };
			var sizes = new[] { 1000, 1000, 1000 };
			var res = new[] { 0, 0, 0 };

			RegionRolesBotModule.AssignRoles(states, sizes, res, homeRegionId: 0, now: 100, holdTicks: 0,
				outpostMaxSize: 400, economyMinResourceCells: 60, out var changed);

			Assert.That(states[0].Role, Is.EqualTo(RegionRole.Core));
			Assert.That(changed, Is.EqualTo(1));
		}

		[Test]
		public void CoreFallsBackToMostBuiltRegionWhenHomeIsLost()
		{
			var states = new[] { Claimed(0, buildings: 5), Claimed(1, buildings: 9), Claimed(2, buildings: 1) };
			var sizes = new[] { 1000, 1000, 1000 };
			var res = new[] { 0, 0, 0 };

			RegionRolesBotModule.AssignRoles(states, sizes, res, homeRegionId: -1, now: 100, holdTicks: 0,
				outpostMaxSize: 400, economyMinResourceCells: 60, out _);

			Assert.That(states[1].Role, Is.EqualTo(RegionRole.Core));
			Assert.That(states.Count(s => s.Role == RegionRole.Core), Is.EqualTo(1));
		}

		[Test]
		public void MilitaryGoesToTheBuiltEnemyBorderRegion()
		{
			var states = new[]
			{
				Claimed(0, buildings: 9, bordersEnemy: false),
				Claimed(1, buildings: 2, bordersEnemy: true, value: 30),
				Claimed(2, buildings: 6, bordersEnemy: true, value: 50),
			};
			var sizes = new[] { 1000, 1000, 1000 };
			var res = new[] { 0, 0, 0 };

			RegionRolesBotModule.AssignRoles(states, sizes, res, homeRegionId: 0, now: 100, holdTicks: 0,
				outpostMaxSize: 400, economyMinResourceCells: 60, out _);

			Assert.That(states[0].Role, Is.EqualTo(RegionRole.Core));
			Assert.That(states[2].Role, Is.EqualTo(RegionRole.Military));
			Assert.That(states.Count(s => s.Role == RegionRole.Military), Is.EqualTo(1));
		}

		[Test]
		public void SmallClaimedRegionIsOutpostBeforeEconomy()
		{
			var states = new[] { Claimed(0, buildings: 9), Claimed(1, buildings: 3) };
			var sizes = new[] { 1000, 200 };      // region 1 is too small to be anything but Outpost
			var res = new[] { 0, 500 };           // …even though it carries plenty of resources

			RegionRolesBotModule.AssignRoles(states, sizes, res, homeRegionId: 0, now: 100, holdTicks: 0,
				outpostMaxSize: 400, economyMinResourceCells: 60, out _);

			Assert.That(states[1].Role, Is.EqualTo(RegionRole.Outpost));
		}

		[Test]
		public void BigResourcefulRegionIsEconomy()
		{
			var states = new[] { Claimed(0, buildings: 9), Claimed(1, buildings: 3) };
			var sizes = new[] { 1000, 2000 };
			var res = new[] { 0, 500 };

			RegionRolesBotModule.AssignRoles(states, sizes, res, homeRegionId: 0, now: 100, holdTicks: 0,
				outpostMaxSize: 400, economyMinResourceCells: 60, out _);

			Assert.That(states[1].Role, Is.EqualTo(RegionRole.Economy));
		}

		[Test]
		public void ALockedRoleSurvivesInsideItsHoldWindow()
		{
			// Region 1 took Economy at tick 0; at tick 100 (< holdTicks) the role holds — it does not
			// border the enemy, so the exclusive-role preemption has no reason to reach for it.
			var states = new[]
			{
				Claimed(0, buildings: 9),
				Claimed(1, RegionRole.Economy, roleSince: 0, buildings: 4, bordersEnemy: false, value: 60),
			};
			var sizes = new[] { 1000, 1000 };
			var res = new[] { 0, 0 };

			RegionRolesBotModule.AssignRoles(states, sizes, res, homeRegionId: 0, now: 100, holdTicks: 1500,
				outpostMaxSize: 400, economyMinResourceCells: 60, out _);

			Assert.That(states[1].Role, Is.EqualTo(RegionRole.Economy));
		}

		[Test]
		public void ExclusivePreemptionStillGrabsMilitaryWhenAllCandidatesLocked()
		{
			// The only enemy-bordering region is locked under Economy — the exclusive role preempts the
			// hold, because a hold was never meant to leave the bot without a Military at all.
			var states = new[]
			{
				Claimed(0, buildings: 9),
				Claimed(1, RegionRole.Economy, roleSince: 0, buildings: 4, bordersEnemy: true, value: 60),
				Claimed(2, RegionRole.Outpost, roleSince: 0, buildings: 2),
			};
			var sizes = new[] { 1000, 1000, 100 };
			var res = new[] { 0, 0, 0 };

			RegionRolesBotModule.AssignRoles(states, sizes, res, homeRegionId: 0, now: 100, holdTicks: 1500,
				outpostMaxSize: 400, economyMinResourceCells: 60, out _);

			Assert.That(states[1].Role, Is.EqualTo(RegionRole.Military));
			Assert.That(states[0].Role, Is.EqualTo(RegionRole.Core));
			Assert.That(states[2].Role, Is.EqualTo(RegionRole.Outpost));
		}

		[Test]
		public void UnheldRegionsGetNoRole()
		{
			var held = Claimed(0, buildings: 9);
			var unheld = new RegionRoleState(1); // Claimed = false
			var states = new[] { held, unheld };
			var sizes = new[] { 1000, 1000 };
			var res = new[] { 0, 500 };

			RegionRolesBotModule.AssignRoles(states, sizes, res, homeRegionId: 0, now: 100, holdTicks: 0,
				outpostMaxSize: 400, economyMinResourceCells: 60, out _);

			Assert.That(states[1].Role, Is.EqualTo(RegionRole.None));
		}
	}
}
