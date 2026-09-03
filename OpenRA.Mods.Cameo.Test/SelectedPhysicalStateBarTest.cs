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
using OpenRA.Mods.Cameo.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public sealed class SelectedPhysicalStateBarTest
	{
		[TestCase(0, 0, 100, 0, true, 0f)]
		[TestCase(10, 0, 100, 0, true, 0.1f)]
		[TestCase(100, 0, 100, 0, true, 1f)]
		[TestCase(-10000, -20000, 20000, 0, false, 0.5f)]
		[TestCase(10000, -20000, 20000, 0, false, 0.5f)]
		[TestCase(int.MinValue, int.MinValue, int.MaxValue, 0, true, 0f)]
		[TestCase(int.MaxValue, int.MinValue, int.MaxValue, 0, true, 1f)]
		[TestCase(int.MinValue, int.MinValue, int.MaxValue, 0, false, 1f)]
		public void PhysicalStateMapsToExpectedBarValue(
			int value, int minValue, int maxValue, int relaxedValue, bool showAbsoluteValues, float expected)
		{
			Assert.That(
				SelectedPhysicalStateBar.BarValue(value, minValue, maxValue, relaxedValue, showAbsoluteValues),
				Is.EqualTo(expected));
		}
	}
}
