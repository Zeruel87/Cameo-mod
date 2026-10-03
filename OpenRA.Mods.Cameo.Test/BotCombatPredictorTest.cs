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
	public class BotCombatPredictorTest
	{
		static readonly BitSet<TargetableType> Ground = new("Ground");
		static readonly BitSet<TargetableType> Air = new("Air");
		static readonly BitSet<TargetableType> None = default;

		static BotUnitProfile Unit(string name, int hp, string armor, double dpt, Dictionary<string, int> versus = null,
			BitSet<TargetableType>? targets = null, BitSet<TargetableType>? hits = null)
		{
			var weapons = dpt > 0 ? new[] { new BotWeaponProfile(dpt, WDist.FromCells(5), hits ?? Ground, None, versus) } : [];
			return new BotUnitProfile(name, 100, hp, armor, 50, false, false, targets ?? Ground, weapons);
		}

		[Test]
		public void EqualForcesAreEven()
		{
			var p = BotCombatPredictor.Predict(10, 1000, 10, 1000);
			Assert.That(p.Ratio, Is.EqualTo(1).Within(1e-9));
		}

		[Test]
		public void SquareLawRewardsConcentration()
		{
			// Twice the units: twice the damage AND twice the HP -> four times the fighting strength.
			var tank = Unit("tank", 400, "Heavy", 2);
			var p = BotCombatPredictor.Predict(new[] { (tank, 10) }, new[] { (tank, 5) });
			Assert.That(p.Ratio, Is.EqualTo(4).Within(1e-9));
			Assert.That(p.OwnWins, Is.True);
			Assert.That(p.OwnSurvivingFraction, Is.EqualTo(System.Math.Sqrt(0.75)).Within(1e-9));
			Assert.That(p.EnemySurvivingFraction, Is.Zero);
		}

		[Test]
		public void VersusDecidesWhoWins()
		{
			// The rocket team costs the same and has less HP, but deals 300% to Heavy while the tank deals 25% to Light.
			var tank = Unit("tank", 600, "Heavy", 2, new Dictionary<string, int> { { "Light", 25 } });
			var rockets = Unit("rockets", 200, "Light", 2, new Dictionary<string, int> { { "Heavy", 300 } });
			var p = BotCombatPredictor.Predict(new[] { (rockets, 5) }, new[] { (tank, 5) });
			Assert.That(p.OwnWins, Is.True, $"ratio {p.Ratio}");
		}

		[Test]
		public void AGroundArmyCannotHurtAircraft()
		{
			var tank = Unit("tank", 600, "Heavy", 2);
			var jet = Unit("jet", 300, "Light", 2, targets: Air, hits: Ground);
			var p = BotCombatPredictor.Predict(new[] { (tank, 20) }, new[] { (jet, 1) });
			Assert.That(p.Ratio, Is.Zero);
			Assert.That(p.OwnWins, Is.False);
		}

		[Test]
		public void AnUnarmedEnemyIsCappedNotInfinite()
		{
			var tank = Unit("tank", 600, "Heavy", 2);
			var truck = Unit("truck", 500, "Light", 0);
			var p = BotCombatPredictor.Predict(new[] { (tank, 1) }, new[] { (truck, 3) });
			Assert.That(p.Ratio, Is.EqualTo(BotCombatPredictor.MaxRatio));
			Assert.That(p.OwnSurvivingFraction, Is.EqualTo(1));
		}

		[TestCase(40, 1, new[] { 5 }, 40)]
		[TestCase(40, 3, new[] { 5 }, 50)]
		[TestCase(40, 3, new[] { 2, 8 }, 50)]
		[TestCase(0, 1, new int[0], 1)]
		public void CycleIsBurstGapsPlusReload(int reload, int burst, int[] delays, int expected)
		{
			Assert.That(BotWeaponProfile.CycleTicks(reload, burst, delays), Is.EqualTo(expected));
		}
	}
}
