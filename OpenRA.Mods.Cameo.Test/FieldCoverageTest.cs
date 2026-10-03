#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software.
 * It is made available under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System.Linq;
using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	// AI_ARCHITECTURE 12.24 FE-1: refineries per anchor, separation, spread. Pure helpers only.
	[TestFixture]
	public sealed class FieldCoverageTest
	{
		static CPos C(int x, int y) => new(x, y);

		[Test]
		public void AnchorsAreSpreadersPlusSpreaderlessFieldCenters()
		{
			var anchors = ExpansionPlannerBotModule.BuildAnchors(
				new[] { C(10, 10), C(10, 10), C(50, 50) },
				new[] { C(12, 12), C(80, 80), C(52, 49) }, 12);

			// duplicate spreader dropped; the two fields near a spreader are represented by it; (80,80) has none
			Assert.That(anchors, Is.EqualTo(new[] { C(10, 10), C(50, 50), C(80, 80) }));
		}

		[Test]
		public void OneRefineryServesAtMostOneAnchor()
		{
			var anchors = new[] { C(10, 10), C(14, 10) };
			var assigned = ExpansionPlannerBotModule.AssignRefineries(anchors, new[] { C(12, 10) }, 8);

			// equidistant: the lower anchor index takes it, the other stays unserved
			Assert.That(assigned, Is.EqualTo(new[] { 0, -1 }));
		}

		[Test]
		public void RefineryOutsideServeRadiusServesNothing()
		{
			var assigned = ExpansionPlannerBotModule.AssignRefineries(new[] { C(10, 10) }, new[] { C(30, 10) }, 8);
			Assert.That(assigned, Is.EqualTo(new[] { -1 }));
		}

		[Test]
		public void RefineryWantedWhileAnAnchorInReachIsUnserved()
		{
			var anchors = new[] { C(10, 10), C(100, 100) };
			var wanted = ExpansionPlannerBotModule.WantedAnchor(anchors, new CPos[0], new[] { C(14, 10) }, 8, 6, null, 0, out var unserved);

			// the far anchor is out of reach: only the first counts
			Assert.That(wanted, Is.EqualTo(0));
			Assert.That(unserved, Is.EqualTo(1));
		}

		[Test]
		public void NoRefineryWantedWhenEveryAnchorInReachIsServed()
		{
			var anchors = new[] { C(10, 10), C(100, 100) };
			var wanted = ExpansionPlannerBotModule.WantedAnchor(anchors, new[] { C(12, 10) }, new[] { C(14, 10) }, 8, 6, null, 0, out var unserved);
			Assert.That(wanted, Is.EqualTo(-1));
			Assert.That(unserved, Is.EqualTo(0));
		}

		[Test]
		public void NeverMoreRefineriesThanAnchors()
		{
			// two anchors, two refineries placed far from both (a home stack), a third anchor-less state: nothing wanted
			var anchors = new[] { C(10, 10), C(12, 12) };
			var homeStack = new[] { C(60, 60), C(62, 60) };
			var wanted = ExpansionPlannerBotModule.WantedAnchor(anchors, homeStack, new[] { C(10, 12) }, 8, 6, null, 0, out var unserved);
			Assert.That(wanted, Is.EqualTo(-1));
			Assert.That(unserved, Is.EqualTo(2));

			// queued refineries count too: one placed + one queued on two anchors leaves no room
			Assert.That(ExpansionPlannerBotModule.WantedAnchor(anchors, new[] { C(60, 60) }, new[] { C(10, 12) }, 8, 6, null, 1, out _), Is.EqualTo(-1));
		}

		[Test]
		public void ParkedAnchorIsSkippedButStillCountedUnserved()
		{
			var anchors = new[] { C(10, 10), C(18, 10) };
			var wanted = ExpansionPlannerBotModule.WantedAnchor(anchors, new CPos[0], new[] { C(12, 10) }, 8, 6, i => i == 0, 0, out var unserved);
			Assert.That(wanted, Is.EqualTo(1));
			Assert.That(unserved, Is.EqualTo(2));
		}

		[Test]
		public void SiteInTheCrawlDirectionIsPenalised()
		{
			var origin = C(50, 50);
			var crawl = new[] { C(70, 50) };

			// same bearing (east) -> min factor; a perpendicular site keeps 1
			Assert.That(ExpansionPlannerBotModule.SeparationFactor(C(90, 54), origin, crawl, 35, 0.25, 6), Is.EqualTo(0.25));
			Assert.That(ExpansionPlannerBotModule.SeparationFactor(C(50, 10), origin, crawl, 35, 0.25, 6), Is.EqualTo(1.0));
		}

		[Test]
		public void SeparationUsesYardsAndInflightSitesAndWrapsAround()
		{
			var origin = C(50, 50);

			// bearings straddling the 0/360 seam are still close
			Assert.That(ExpansionPlannerBotModule.SeparationFactor(C(90, 46), origin, new[] { C(90, 54) }, 35, 0.25, 6), Is.EqualTo(0.25));

			// a yard at the base itself has no bearing and never penalises
			Assert.That(ExpansionPlannerBotModule.SeparationFactor(C(90, 50), origin, new[] { C(52, 50) }, 35, 0.25, 6), Is.EqualTo(1.0));
		}

		[Test]
		public void BearingDeltaIsTheShorterArc()
		{
			Assert.That(ExpansionPlannerBotModule.BearingDelta(new WAngle(10), new WAngle(1014)), Is.EqualTo(20));
			Assert.That(ExpansionPlannerBotModule.BearingDelta(new WAngle(0), new WAngle(512)), Is.EqualTo(512));
		}

		[Test]
		public void SpreadFactorGrowsWithDistanceFromOwnBuildings()
		{
			Assert.That(ExpansionPlannerBotModule.SpreadFactor(0, 100, 1.0), Is.EqualTo(1.0));
			Assert.That(ExpansionPlannerBotModule.SpreadFactor(50, 100, 1.0), Is.EqualTo(1.5).Within(1e-9));
			Assert.That(ExpansionPlannerBotModule.SpreadFactor(50, 100, 0.0), Is.EqualTo(1.0));
		}

		[Test]
		public void McvSiteAvoidsTheCrawlDirectionWhenWeighted()
		{
			var origin = C(50, 50);
			var crawl = new[] { C(70, 50) };
			var east = new ExpansionPlannerBotModule.FieldScore(1, C(80, 50), 100, 5, 0, 0, 1);
			var north = new ExpansionPlannerBotModule.FieldScore(2, C(50, 0), 100, 5, 0, 0, 1);
			var fields = new[] { east, north };

			// east is nearer the MCV, so unweighted it wins; weighted by separation the north site wins
			Assert.That(ExpansionPlannerBotModule.McvSite(fields, origin, 3, 10)?.Index, Is.EqualTo(1));
			var weighted = ExpansionPlannerBotModule.McvSite(fields, origin, 3, 10, null,
				f => ExpansionPlannerBotModule.SeparationFactor(f.Center, origin, crawl, 35, 0.25, 6));
			Assert.That(weighted?.Index, Is.EqualTo(2));
		}

		[Test]
		public void FieldTakenByAnMcvSiteIsDetected()
		{
			Assert.That(ExpansionPlannerBotModule.TakenByMcvSite(C(100, 50), new[] { C(98, 50) }, 8), Is.True);
			Assert.That(ExpansionPlannerBotModule.TakenByMcvSite(C(100, 50), new[] { C(50, 5) }, 8), Is.False);
			Assert.That(ExpansionPlannerBotModule.TakenByMcvSite(C(100, 50), Enumerable.Empty<CPos>(), 8), Is.False);
		}
	}
}
