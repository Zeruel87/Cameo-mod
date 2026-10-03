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
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	// The return leg of the learning loop (DESIGN §19.2): the fitted priors file parses, and every unknown is neutral.
	[TestFixture]
	public class ArsenalPriorsTest
	{
		const string Yaml = "# GENERATED\nBotArsenalPriors:\n\tVisibilityPercentByPhase: 60, 55, 70\n\tTradePercent@td_gdi__vs__td_nod:\n\t\ttd_gdi_mediumtank: 135\n\t\ttd_gdi_rifle: 80\n";

		static ArsenalPriors Load(string yaml) => ArsenalPriors.Parse(MiniYaml.FromString(yaml, "priors"));

		[Test]
		public void ParsesPairsTypesAndVisibility()
		{
			var priors = Load(Yaml);
			Assert.That(priors.PairCount, Is.EqualTo(1));
			Assert.That(priors.TypeCount, Is.EqualTo(2));
			Assert.That(priors.VisibilityPercentByPhase, Is.EqualTo(new[] { 60, 55, 70 }));
			Assert.That(priors.TradePercent("td_gdi", "td_nod", "td_gdi_mediumtank"), Is.EqualTo(135));
			Assert.That(priors.TradePercent("td_gdi", "td_nod", "td_gdi_rifle"), Is.EqualTo(80));
		}

		[Test]
		public void UnknownIsNeutral()
		{
			var priors = Load(Yaml);
			Assert.That(priors.TradePercent("td_gdi", "td_nod", "nothing"), Is.EqualTo(100));
			Assert.That(priors.TradePercent("td_nod", "td_gdi", "td_gdi_mediumtank"), Is.EqualTo(100));
			Assert.That(priors.TradePercent(null, "td_nod", "td_gdi_rifle"), Is.EqualTo(100));
			Assert.That(Load("Other:\n\tA: 1\n").PairCount, Is.EqualTo(0));
		}
	}
}
