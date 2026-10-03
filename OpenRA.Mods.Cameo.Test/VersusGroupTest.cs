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
using OpenRA.Mods.Cameo.Widgets.Logic;
using Group = OpenRA.Mods.Cameo.Widgets.Logic.VersusSummary.Group;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class VersusGroupTest
	{
		[Test]
		public void GroupPercentIsTheWeightedGeometricMean()
		{
			var versus = new Dictionary<string, int> { { "None", 200 }, { "Flak", 100 }, { "Plate", 50 } };

			// Unweighted: cube root of 200 * 100 * 50 = 100.
			Assert.That(VersusSummary.GroupPercent(versus, new Dictionary<string, int> { { "None", 1 }, { "Flak", 1 }, { "Plate", 1 } }),
				Is.EqualTo(100));

			// Weighted by who wears what: three None wearers to one Plate wearer, (200^3 * 50)^(1/4) = 141.
			Assert.That(VersusSummary.GroupPercent(versus, new Dictionary<string, int> { { "None", 3 }, { "Plate", 1 } }),
				Is.EqualTo(141));
		}

		[Test]
		public void AnArmourMissingFromTheTableCountsAsOneHundred()
		{
			var versus = new Dictionary<string, int> { { "Heavy", 25 } };
			Assert.That(VersusSummary.GroupPercent(versus, new Dictionary<string, int> { { "Heavy", 1 }, { "Superheavy", 1 } }),
				Is.EqualTo(50));
		}

		[Test]
		public void CannotAttackNamesTheDomainOrTheMissedClass()
		{
			Assert.That(ProductionTooltipCameoLogic.CannotReason(Group.Aircraft, true), Is.EqualTo("label-versus-cannot-air"));
			Assert.That(ProductionTooltipCameoLogic.CannotReason(Group.Ships, true), Is.EqualTo("label-versus-cannot-water"));
			Assert.That(ProductionTooltipCameoLogic.CannotReason(Group.Submarines, false), Is.EqualTo("label-versus-cannot-underwater"));

			// An anti-air-only unit hits nothing on land: "cannot attack ground".
			Assert.That(ProductionTooltipCameoLogic.CannotReason(Group.Tanks, false), Is.EqualTo("label-versus-cannot-ground"));

			// A sniper hits infantry but not vehicles or buildings: name the class it misses.
			Assert.That(ProductionTooltipCameoLogic.CannotReason(Group.Tanks, true), Is.EqualTo("label-versus-cannot-vehicles"));
			Assert.That(ProductionTooltipCameoLogic.CannotReason(Group.Defenses, true), Is.EqualTo("label-versus-cannot-buildings"));
			Assert.That(ProductionTooltipCameoLogic.CannotReason(Group.Heroes, true), Is.EqualTo("label-versus-cannot-infantry"));
		}

		[Test]
		public void BandsAreSymmetricOnTheGeometricScale()
		{
			// 125 above and 80 below are the same distance from 100: x1.25 and /1.25.
			Assert.That(100.0 * VersusSummary.StrongPercent / 100 * VersusSummary.WeakPercent / 100, Is.EqualTo(100.0));
		}
	}
}
