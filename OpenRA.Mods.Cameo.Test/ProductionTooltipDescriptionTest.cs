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
using OpenRA.Mods.Cameo.Widgets.Logic;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class ProductionTooltipDescriptionTest
	{
		static string Shown(string yaml) =>
			ProductionTooltipCameoLogic.StripHandWrittenVersus(ProductionTooltipCameoLogic.UnescapeNewlines(yaml));

		[Test]
		public void EscapedNewlinesBecomeLineBreaks()
		{
			Assert.That(ProductionTooltipCameoLogic.UnescapeNewlines(@"Provides double the power of\n a standard Power Plant."),
				Is.EqualTo("Provides double the power of\n a standard Power Plant."));
		}

		[Test]
		public void HandWrittenVersusLinesAreRemovedOnceUnescaped()
		{
			// The GDI Rocket Soldier's description, as the yaml spells it.
			Assert.That(Shown(@"Anti-tank infantry.\n  Strong vs Vehicles, Aircraft\n  Weak vs Infantry"),
				Is.EqualTo("Anti-tank infantry."));
		}

		[Test]
		public void InlineVersusSentencesAreRemoved()
		{
			Assert.That(Shown("Scout vehicle.  Strong vs Vehicles, Aircraft.  Weak vs Infantry"), Is.EqualTo("Scout vehicle."));
			Assert.That(Shown("Powerful Anti Material Sniper. Strong vs Tanks and Aircraft"), Is.EqualTo("Powerful Anti Material Sniper."));
			Assert.That(Shown("Slow heavy walker. Strong vs Everything. May crush tanks."),
				Is.EqualTo("Slow heavy walker. May crush tanks."));
		}

		[Test]
		public void OtherLinesAndSentencesAreKept()
		{
			Assert.That(Shown(@"Deploys into a Construction Yard.\nUnarmed"), Is.EqualTo("Deploys into a Construction Yard.\nUnarmed"));
			Assert.That(Shown("Strongly armoured. Weakened by EMP."), Is.EqualTo("Strongly armoured. Weakened by EMP."));
		}
	}
}
