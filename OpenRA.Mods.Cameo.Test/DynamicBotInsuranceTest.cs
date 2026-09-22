#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public sealed class DynamicBotInsuranceTest
	{
		static int HistoryHash(params int[] values)
		{
			var hash = 0;
			for (var i = 0; i < values.Length; i++)
				hash ^= DynamicBotInsurance.MixedHistorySlotHash(i, values[i]);

			return hash;
		}

		[Test]
		public void HistoryHashDistinguishesPermutedSamples()
		{
			Assert.That(HistoryHash(1, 2), Is.Not.EqualTo(HistoryHash(2, 1)));
			Assert.That(HistoryHash(1000, 7000, 3000), Is.Not.EqualTo(HistoryHash(3000, 7000, 1000)));
		}

		[Test]
		public void EmptyHistorySlotsAreNeutral()
		{
			Assert.That(DynamicBotInsurance.MixedHistorySlotHash(0, 0), Is.Zero);
			Assert.That(DynamicBotInsurance.MixedHistorySlotHash(1499, 0), Is.Zero);
		}

		[Test]
		public void DifficultyInterpolationKeepsExactEndpoints()
		{
			Assert.That(DynamicBotInsurance.InterpolateByRank(1, 10, 0, 10), Is.EqualTo(1));
			Assert.That(DynamicBotInsurance.InterpolateByRank(1, 10, 9, 10), Is.EqualTo(10));
			Assert.That(DynamicBotInsurance.InterpolateByRank(10, 100, 4, 10), Is.EqualTo(50));
		}

		[Test]
		public void TriggerCancellationAndRecoveryKeepTheirStrictBoundaries()
		{
			Assert.That(DynamicBotInsurance.ShouldStartDelay(999, 1000), Is.True);
			Assert.That(DynamicBotInsurance.ShouldStartDelay(1000, 1000), Is.False);
			Assert.That(DynamicBotInsurance.ShouldCancelDelay(1001, 1000), Is.True);
			Assert.That(DynamicBotInsurance.ShouldCancelDelay(1000, 1000), Is.False);
			Assert.That(DynamicBotInsurance.ShouldStopPaying(9999, 10000), Is.False);
			Assert.That(DynamicBotInsurance.ShouldStopPaying(10000, 10000), Is.True);
		}

		[Test]
		public void DelayCalculationClampsAndProtectsZeroDivisor()
		{
			Assert.That(DynamicBotInsurance.DelayTicks(1500, 10, 25, 1500), Is.EqualTo(150));
			Assert.That(DynamicBotInsurance.DelayTicks(0, 100, 25, 1500), Is.EqualTo(25));
			Assert.That(DynamicBotInsurance.DelayTicks(int.MaxValue, 0, 25, 1500), Is.EqualTo(1500));
		}

		[Test]
		public void CashPayoutCarriesFractionsAndCannotCrossTheCap()
		{
			var first = DynamicBotInsurance.CashPayout(0, 1, 500, 5000, 10000);
			Assert.That(first, Is.EqualTo((0, 500)));
			var second = DynamicBotInsurance.CashPayout(first.Accumulator, 1, 500, 5000, 10000);
			Assert.That(second, Is.EqualTo((1, 0)));

			var nearCap = DynamicBotInsurance.CashPayout(999, 10, 1000, 9999, 10000);
			Assert.That(nearCap.Grant, Is.EqualTo(1));
			Assert.That(nearCap.Accumulator, Is.EqualTo(999));
		}

		[Test]
		public void PurifierPayoutUsesDepthAndCannotCrossTheCap()
		{
			Assert.That(DynamicBotInsurance.PurifierPayout(1000, 50, 1000, 0, 0, 10000),
				Is.EqualTo(500));
			Assert.That(DynamicBotInsurance.PurifierPayout(100000, 50, 1000, 9900, 25, 10000),
				Is.EqualTo(75));
		}

		[Test]
		public void ParWorthRemainsBoundedAtTheLongMatchLimit()
		{
			var info = new DynamicBotInsuranceInfo();
			for (var rank = 0; rank < info.Difficulties.Length; rank++)
			{
				var asymptote = info.ParBaseWorth + info.ParAsymptotePerRank * (rank + 1);
				Assert.That(DynamicBotInsurance.ParWorthAt(info, rank, int.MaxValue), Is.EqualTo(asymptote));
			}
		}
	}
}
