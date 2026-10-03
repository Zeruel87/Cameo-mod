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

using NUnit.Framework;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Cameo.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	// AI_ARCHITECTURE 12.20: the three merged mechanisms' pure rules (building gap, per-field harvester cap, army-first gate).
	[TestFixture]
	public class SpreadRulesTest
	{
		[Test]
		public void GapBufferCoversChebyshevRadiusAroundFootprint()
		{
			var buffer = BuildingGapRule.BufferCells(new[] { new CPos(10, 10) }, 2);
			Assert.That(buffer.Count, Is.EqualTo(25));
			Assert.That(buffer.Contains(new CPos(12, 8)), Is.True);
			Assert.That(buffer.Contains(new CPos(13, 10)), Is.False);
		}

		[Test]
		public void ZeroGapIsEmptyBuffer() => Assert.That(BuildingGapRule.BufferCells(new[] { new CPos(1, 1) }, 0), Is.Empty);

		[Test]
		public void NoAdvisorMeansNoGap() => Assert.That(BuildingGapRule.Resolve(null, false), Is.EqualTo(0));

		[Test]
		public void FieldCapZeroIsUnlimited()
		{
			Assert.That(HarvesterFieldCap.Saturated(99, 0), Is.False);
			Assert.That(HarvesterFieldCap.Surplus(99, 0), Is.EqualTo(0));
			Assert.That(HarvesterFieldCap.Need(3, 99, 0), Is.EqualTo(3));
		}

		[Test]
		public void FieldCapSaturatesAtCapAndLimitsReceivers()
		{
			Assert.That(HarvesterFieldCap.Saturated(3, 4), Is.False);
			Assert.That(HarvesterFieldCap.Saturated(4, 4), Is.True);
			Assert.That(HarvesterFieldCap.Surplus(6, 4), Is.EqualTo(2));
			Assert.That(HarvesterFieldCap.Need(3, 3, 4), Is.EqualTo(1));
			Assert.That(HarvesterFieldCap.Need(1, 1, 4), Is.EqualTo(1));
		}

		[Test]
		public void CashPoorVoteHasHysteresisAndReleasesWithoutProducer()
		{
			Assert.That(ArmyFirstEval.NextPaused(false, true, 2000, 2500, 4000), Is.True);
			Assert.That(ArmyFirstEval.NextPaused(true, true, 3000, 2500, 4000), Is.True);
			Assert.That(ArmyFirstEval.NextPaused(true, true, 4000, 2500, 4000), Is.False);
			Assert.That(ArmyFirstEval.NextPaused(true, false, 0, 2500, 4000), Is.False);
		}

		[Test]
		public void ArmyCountGateNeedsMinCashAndProducer()
		{
			Assert.That(ArmyFirstEval.ArmyCountHolds(true, 2000, 5, 14, 1500), Is.True);
			Assert.That(ArmyFirstEval.ArmyCountHolds(true, 1500, 5, 14, 1500), Is.False);
			Assert.That(ArmyFirstEval.ArmyCountHolds(true, 2000, 14, 14, 1500), Is.False);
			Assert.That(ArmyFirstEval.ArmyCountHolds(false, 2000, 5, 14, 1500), Is.False);
			Assert.That(ArmyFirstEval.ArmyCountHolds(true, 9000, 0, 0, 1500), Is.False);
		}

		[Test]
		public void EssentialsAlwaysPass()
		{
			Assert.That(ArmyFirstEval.Holds(true, true, true), Is.False);
			Assert.That(ArmyFirstEval.Holds(false, true, false), Is.True);
			Assert.That(ArmyFirstEval.Holds(false, false, true), Is.True);
			Assert.That(ArmyFirstEval.Holds(false, false, false), Is.False);
		}
	}
}
