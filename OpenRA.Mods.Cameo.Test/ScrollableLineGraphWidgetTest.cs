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
using OpenRA.Mods.Cameo.Widgets;
using OpenRA.Primitives;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public sealed class ScrollableLineGraphWidgetTest
	{
		static (float Min, float Max) ScaledRange(params float[][] points)
		{
			var series = new List<ScrollableLineGraphSeries>();
			foreach (var values in points)
				series.Add(new ScrollableLineGraphSeries("test", Color.White, values));

			return ScrollableLineGraphWidget.GetScaledRange(series);
		}

		[Test]
		public void EmptySeriesUsesHistoricalRange()
		{
			Assert.That(ScaledRange(), Is.EqualTo((0f, 5000f)));
			Assert.That(ScaledRange(System.Array.Empty<float>()), Is.EqualTo((0f, 5000f)));
		}

		[Test]
		public void MultipleSeriesIncludeBothExtremes()
		{
			Assert.That(ScaledRange(new[] { -6200f, 0f }, new[] { 3500f }),
				Is.EqualTo((-7000f, 4000f)));
		}

		[Test]
		public void AllPositiveValuesPreserveHistoricalRange()
		{
			var range = ScaledRange(new[] { 6250f });

			Assert.That(range.Min, Is.EqualTo(0f));
			Assert.That(range.Max, Is.EqualTo(7000f));
		}

		[Test]
		public void MixedSignValuesSpanBothSidesOfZero()
		{
			var range = ScaledRange(new[] { -1200f, 2500f });

			Assert.That(range.Min, Is.LessThan(0f));
			Assert.That(range.Max, Is.GreaterThan(0f));
			Assert.That(range.Min, Is.LessThanOrEqualTo(-1200f));
			Assert.That(range.Max, Is.GreaterThanOrEqualTo(2500f));
		}

		[Test]
		public void AllNegativeValuesKeepZeroAsMaximum()
		{
			var range = ScaledRange(new[] { -1250f });

			Assert.That(range.Max, Is.EqualTo(0f));
			Assert.That(range.Min, Is.LessThan(0f));
		}

		[TestCase(new[] { 0f })]
		[TestCase(new[] { 100f })]
		[TestCase(new[] { -100f })]
		[TestCase(new[] { -100f, 100f })]
		public void ScaledRangeHasMinimumSpan(float[] points)
		{
			var range = ScaledRange(points);

			Assert.That(range.Max - range.Min, Is.GreaterThanOrEqualTo(5000f));
		}
	}
}
