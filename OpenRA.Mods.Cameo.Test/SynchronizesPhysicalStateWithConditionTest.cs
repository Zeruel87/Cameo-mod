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
	public sealed class SynchronizesPhysicalStateWithConditionTest
	{
		[TestCase(0, 0)]
		[TestCase(1, 10)]
		[TestCase(5, 50)]
		[TestCase(10, 100)]
		public void ConditionLevelMapsDirectlyToSpinState(int conditionLevel, int expectedState)
		{
			Assert.That(
				SynchronizesPhysicalStateWithCondition.ValueForConditionLevel(conditionLevel, 0, 10),
				Is.EqualTo(expectedState));
		}

		[Test]
		public void MissingOrNegativeConditionCannotCreateSpin()
		{
			Assert.That(SynchronizesPhysicalStateWithCondition.ValueForConditionLevel(-1, 0, 10), Is.Zero);
		}
	}
}
