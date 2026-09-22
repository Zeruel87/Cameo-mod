#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License as
 * published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using NUnit.Framework;
using OpenRA.Mods.Cameo.Warheads;

namespace OpenRA.Mods.Cameo.Test
{
	/// <summary>
	/// Differential tests for the §12.0i continuous-heaviness CORE: the REAL C#
	/// rounding, band interpolation and bell must reproduce the exact vectors the
	/// Python mirror (tools/balance/effective_heaviness.py) produced on the
	/// committed TS90mm CannonAP_Medium table (no knife-edge values — verified).
	/// Validation of Heaviness / anchor configuration needs a full Ruleset and is
	/// mirrored (and covered) in Python; see the session report's gaps note.
	/// </summary>
	[TestFixture]
	public sealed class AreaDamageWarheadHeavinessTest
	{
		static readonly Dictionary<string, int> Ts90MediumPctVersus = new()
		{
			["Bomber"] = 6, ["Concrete"] = 15, ["Fighter"] = 5, ["Flak"] = 10,
			["Heavy"] = 19, ["Helicopter"] = 7, ["Heroic"] = 12, ["Light"] = 17,
			["Medium"] = 18, ["None"] = 9, ["Plate"] = 11, ["Scout"] = 16,
			["Shield"] = 25, ["Spaceship"] = 8, ["Steel"] = 14, ["Superheavy"] = 20,
			["Wood"] = 13,
		};

		static readonly Dictionary<string, int> Light = new()
		{ ["None"] = 10, ["Flak"] = 30, ["Plate"] = 50, ["Medium"] = 40 };
		static readonly Dictionary<string, int> Medium = new()
		{ ["None"] = 20, ["Flak"] = 35, ["Plate"] = 40, ["Medium"] = 38 };
		static readonly Dictionary<string, int> Heavy = new()
		{ ["None"] = 30, ["Flak"] = 28, ["Plate"] = 60, ["Medium"] = 36 };

		[TestCase(5, 2, 2)]
		[TestCase(7, 2, 4)]
		[TestCase(3, 2, 2)]
		[TestCase(1, 2, 0)]
		[TestCase(2501, 1000, 3)]
		[TestCase(1500, 1000, 2)]
		[TestCase(-1500, 1000, -2)]
		public void RoundHalfEvenMatchesThePythonMirror(int numerator, int denominator, int expected)
		{
			Assert.That(AreaDamageWarhead.RoundHalfEven(numerator, denominator), Is.EqualTo(expected));
		}

		[TestCase(0, new[] { 10, 30, 50, 40 })]
		[TestCase(500, new[] { 15, 32, 45, 39 })]
		[TestCase(1000, new[] { 20, 35, 40, 38 })]
		[TestCase(1500, new[] { 25, 32, 50, 37 })]
		[TestCase(2000, new[] { 30, 28, 60, 36 })]
		public void PercentageBandsInterpolatePiecewiseTiesEven(int heaviness, int[] expectedOrderNoneFlakPlateMedium)
		{
			var outTable = (Dictionary<string, int>)AreaDamageWarhead.InterpolatePercentageBands(
				Light, Medium, Heavy, heaviness);
			Assert.That(outTable["None"], Is.EqualTo(expectedOrderNoneFlakPlateMedium[0]));
			Assert.That(outTable["Flak"], Is.EqualTo(expectedOrderNoneFlakPlateMedium[1]));
			Assert.That(outTable["Plate"], Is.EqualTo(expectedOrderNoneFlakPlateMedium[2]));
			Assert.That(outTable["Medium"], Is.EqualTo(expectedOrderNoneFlakPlateMedium[3]));
		}

		[TestCase(0.0, new[] { 7, 15, 6, 10, 19, 7, 9, 17, 17, 9, 11, 16, 25, 7, 15, 19, 14 })]
		[TestCase(0.5, new[] { 7, 15, 5, 10, 18, 7, 8, 17, 18, 9, 11, 15, 25, 7, 15, 19, 14 })]
		[TestCase(1.0, new[] { 6, 16, 5, 10, 19, 8, 8, 17, 18, 8, 11, 14, 25, 8, 15, 20, 14 })]
		[TestCase(1.5, new[] { 6, 16, 4, 11, 19, 8, 7, 16, 19, 8, 11, 13, 25, 8, 15, 20, 13 })]
		[TestCase(2.0, new[] { 6, 17, 4, 10, 21, 8, 7, 15, 19, 7, 12, 13, 25, 9, 14, 21, 12 })]
		public void BellMatchesThePythonMirrorOnTheTs90MediumTable(
			double h, int[] expected)
		{
			var outTable = HeavinessBell.Transform(Ts90MediumPctVersus, h);
			var armors = new[]
			{
				"Bomber", "Concrete", "Fighter", "Flak", "Heavy", "Helicopter", "Heroic",
				"Light", "Medium", "None", "Plate", "Scout", "Shield", "Spaceship",
				"Steel", "Superheavy", "Wood",
			};
			for (var i = 0; i < armors.Length; i++)
				Assert.That(outTable[armors[i]], Is.EqualTo(expected[i]),
					$"armor {armors[i]} at h={h}");
		}

		[Test]
		public void FlatFamiliesStayExactlyFlat()
		{
			var flat = new Dictionary<string, int>
			{
				["Scout"] = 45, ["None"] = 45, ["Fighter"] = 45, ["Light"] = 45,
				["Wood"] = 45, ["Bomber"] = 45, ["Medium"] = 45, ["Flak"] = 45,
				["Steel"] = 45, ["Helicopter"] = 45, ["Concrete"] = 45, ["Heavy"] = 45,
				["Spaceship"] = 45, ["Plate"] = 45, ["Superheavy"] = 45, ["Shield"] = 45,
			};
			foreach (var h in new[] { 0.0, 1.0, 2.0 })
				Assert.That(HeavinessBell.Transform(flat, h),
					Is.EqualTo(flat), $"flat family at h={h}");
		}

		[Test]
		public void DerivedOnlyTable_IsHandledSafelyNotThrown()
		{
			// The empty-peak guard: a table with ONLY derived armors must return the
			// table unchanged (no InvalidOperationException, no bogus re-derivation).
			var derivedOnly = new Dictionary<string, int>
			{ ["Heroic"] = 10, ["Airborne"] = 5 };
			Assert.DoesNotThrow(() => HeavinessBell.Transform(derivedOnly, 1.0));
			Assert.That(HeavinessBell.Transform(derivedOnly, 1.0),
				Is.EqualTo(derivedOnly));
		}

		[Test]
		public void FoldedPercentageUnitsRegressionStillHolds()
		{
			Assert.That(AreaDamageWarhead.FoldedPercentageUnits(2010, 10000), Is.EqualTo(101));
			Assert.That(AreaDamageWarhead.FoldedPercentageUnits(240000, 10000), Is.EqualTo(12000));
		}

		// ------------------------------------------------------------------
		// THE SHARED-PROFILE percentage conversion (HeavinessMode SharedVersus):
		// ONE rounded combined fraction Damage x PercentageScale x h / (200000x2000),
		// HALF-UP over the nonnegative input. The legacy helper above is untouched.
		// ------------------------------------------------------------------

		[Test]
		public void SharedFoldedPercentageUnits_ZeroHeavinessIsZeroPercentage()
		{
			// h = 0 keeps the flat profile but the percentage half reads ZERO.
			Assert.That(AreaDamageWarhead.SharedFoldedPercentageUnits(2000, 2000, 0), Is.Zero);
		}

		[TestCase(100, 2000, 2000, 1)]     // 100 x 2000 x 2 / 4e8 = 1.0 exactly (100 -> 0.01%)
		[TestCase(100, 2000, 1000, 1)]     // 0.5 -> HALF-UP to 1
		[TestCase(100, 2000, 500, 0)]      // 0.25 -> 0
		[TestCase(2000, 2000, 2000, 20)]   // Damage 2000 Scale 2000 h=2 -> 20 bp (0.20%)
		[TestCase(6000, 10000, 2000, 300)] // legacy Scale 10000 at h=2 -> Damage/2000 x 2
		[TestCase(6000, 2500, 1000, 38)]   // 6000 x 2500 x 1000 / 4e8 = 37.5 -> HALF-UP to 38
		[TestCase(80000, 2000, 1000, 400)] // RA2sabot pilot magnitude
		public void SharedFoldedPercentageUnits_SmallDamageBoundaries(
			int damage, int scale, int heaviness, int expected)
		{
			Assert.That(
				AreaDamageWarhead.SharedFoldedPercentageUnits(damage, scale, heaviness),
				Is.EqualTo(expected));
		}

		[TestCase(160000, 8000, 2000, 6_400)]        // 160000 x 8000 x 2 / 4e8 — fits
		[TestCase(2_000_000_000, 1000, 2000, 10_000_000)] // large-but-fitting product
		public void SharedFoldedPercentageUnits_LargeValuesStayInt32(
			int damage, int scale, int heaviness, int expected)
		{
			Assert.That(
				AreaDamageWarhead.SharedFoldedPercentageUnits(damage, scale, heaviness),
				Is.EqualTo(expected));
		}

		[Test]
		public void SharedFoldedPercentageUnits_Int32BoundOverflowFailsClear()
		{
			// damage x scale x h ~ 9.2e18 x 2000 — far beyond Int64, and the rounded
			// result exceeds Int32, so the checked cast must throw, not wrap.
			Assert.Throws<OverflowException>(() =>
				AreaDamageWarhead.SharedFoldedPercentageUnits(int.MaxValue, int.MaxValue, 2000));
		}

		// ------------------------------------------------------------------
		// THE SHARED-PROFILE Shield coefficient: ONE half-up scaling by
		// (2000 + h) / 2000, every other row verbatim.
		// ------------------------------------------------------------------

		[TestCase(0, 25)]
		[TestCase(500, 31)]   // 25 x 1.25 = 31.25 -> HALF-UP 31
		[TestCase(1000, 38)]  // 25 x 1.5 = 37.5 -> HALF-UP 38
		[TestCase(1500, 44)]  // 25 x 1.75 = 43.75 -> HALF-UP 44
		[TestCase(2000, 50)]  // 25 x 2 = 50 exactly
		public void SharedShieldCoefficient_ScalesOnceHalfUp(int heaviness, int expected)
		{
			var table = new Dictionary<string, int>
			{
				["Heavy"] = 21, ["Shield"] = 25, ["None"] = 7, ["Concrete"] = 17,
			};
			var scaled = AreaDamageWarhead.ScaleShieldCoefficient(table, heaviness);
			Assert.That(scaled["Shield"], Is.EqualTo(expected));
			Assert.That(scaled["Heavy"], Is.EqualTo(21), "non-Shield rows verbatim");
			Assert.That(scaled["None"], Is.EqualTo(7));
			Assert.That(scaled["Concrete"], Is.EqualTo(17));
		}
	}
}
