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

namespace OpenRA.Mods.Cameo.Test
{
	// MinimumStructureSpacingCells (BaseBuilderBotModuleCA@generic): the base builder's findPos keeps the
	// first legal cell leaving an N-cell empty gap to every own building, else the legal cell with the
	// widest gap — so genericbot stops packing structures adjacently. The gap itself is pure rectangle
	// math — the larger of the horizontal and vertical empty-cell counts between two footprints, 0 when
	// they touch — exposed as the static BaseBuilderBotModuleCA.FootprintGap so it is testable without a
	// World. The pieces that are NOT pure (the min-over-buildings aggregation in
	// BaseBuilderQueueManagerCA.StructureClearance, and the soft-preference scan inside findPos) need live
	// actors and are not covered here; every legal fallback cell is already CanPlaceBuilding-approved, so
	// the worst case stays a valid placement.
	[TestFixture]
	public class BaseSpacingTest
	{
		static int Gap(int cx, int cy, int cw, int ch, int ex, int ey, int ew, int eh) =>
			BaseBuilderBotModuleCA.FootprintGap(new CPos(cx, cy), new CVec(cw, ch), new CPos(ex, ey), new CVec(ew, eh));

		// Candidate footprint: 2x2 at (10,10), covering cells (10,10)-(11,11).

		[Test]
		public void TouchingFootprintsHaveZeroGap()
		{
			Assert.That(Gap(10, 10, 2, 2, 12, 10, 1, 1), Is.EqualTo(0),
				"a building on the cell directly east of the footprint touches it — zero empty cells");
			Assert.That(Gap(10, 10, 2, 2, 9, 10, 1, 1), Is.EqualTo(0),
				"same on the west side");
		}

		[Test]
		public void CornerTouchIsZeroGapToo()
		{
			Assert.That(Gap(10, 10, 2, 2, 12, 12, 1, 1), Is.EqualTo(0),
				"diagonal adjacency counts as touching on both axes — no empty cell between");
		}

		[Test]
		public void EmptyCellColumnsCountAsTheGap()
		{
			Assert.That(Gap(10, 10, 2, 2, 13, 10, 1, 1), Is.EqualTo(1),
				"cell column 12 stands empty between the footprints");
			Assert.That(Gap(10, 10, 2, 2, 14, 10, 1, 1), Is.EqualTo(2),
				"columns 12 and 13 stand empty");
		}

		[Test]
		public void GapIsSymmetric()
		{
			Assert.That(Gap(10, 10, 2, 2, 7, 10, 2, 2), Is.EqualTo(1),
				"an existing 2x2 ending at column 8 leaves column 9 empty");
			Assert.That(Gap(7, 10, 2, 2, 10, 10, 2, 2), Is.EqualTo(1),
				"the same pair measured the other way round must agree");
		}

		[Test]
		public void VerticalGapUsesTheSameRule()
		{
			Assert.That(Gap(10, 10, 2, 2, 10, 14, 2, 1), Is.EqualTo(2),
				"rows 12 and 13 empty below the footprint; the X axes overlap so only Y separates");
		}

		[Test]
		public void DiagonalGapIsTheLargerAxisNotTheSum()
		{
			Assert.That(Gap(10, 10, 2, 2, 14, 15, 1, 1), Is.EqualTo(3),
				"2 empty columns and 3 empty rows — the Chebyshev-style gap is max, not sum or euclidean");
		}

		[Test]
		public void OverlapOnOneAxisLeavesTheOther()
		{
			Assert.That(Gap(10, 10, 2, 2, 11, 14, 1, 1), Is.EqualTo(2),
				"the existing footprint shares column 11 with the candidate — X contributes 0, Y gives 2");
		}

		[Test]
		public void LargerFootprintsShrinkTheGap()
		{
			Assert.That(Gap(10, 10, 3, 3, 14, 10, 1, 1), Is.EqualTo(1),
				"a 3x3 candidate reaches column 12, so only column 13 is empty");
			Assert.That(Gap(10, 10, 2, 2, 13, 10, 3, 3), Is.EqualTo(1),
				"existing footprint size is irrelevant to the gap — only its edges count");
		}

		[Test]
		public void DistantBuildingsReportTheFullGap()
		{
			Assert.That(Gap(10, 10, 2, 2, 30, 10, 1, 1), Is.EqualTo(18),
				"columns 12-29 stand empty — spacing is satisfied far beyond any sane threshold");
		}
	}
}
