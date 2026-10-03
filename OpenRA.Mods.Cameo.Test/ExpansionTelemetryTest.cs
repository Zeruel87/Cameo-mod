#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System.Collections.Generic;
using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	// AI_ARCHITECTURE 12.24 FE-0 / 12.25 BO-0: the pure helpers of the field-economy telemetry and the placement log.
	[TestFixture]
	public class ExpansionTelemetryTest
	{
		static readonly CPos[] Anchors = { new(10, 10), new(60, 10) };

		[Test]
		public void BearingsRunClockwiseFromNorth()
		{
			var o = new CPos(50, 50);
			Assert.That(ExpansionMath.BearingDegrees(o, new CPos(50, 40)), Is.EqualTo(0));
			Assert.That(ExpansionMath.BearingDegrees(o, new CPos(60, 50)), Is.EqualTo(90));
			Assert.That(ExpansionMath.BearingDegrees(o, new CPos(50, 60)), Is.EqualTo(180));
			Assert.That(ExpansionMath.BearingDegrees(o, new CPos(40, 50)), Is.EqualTo(270));
		}

		[Test]
		public void AngleIsTheSmallerArc()
		{
			Assert.That(ExpansionMath.AngleBetween(350, 10), Is.EqualTo(20));
			Assert.That(ExpansionMath.AngleBetween(0, 180), Is.EqualTo(180));
			Assert.That(ExpansionMath.AngleBetween(90, 90), Is.EqualTo(0));
		}

		[Test]
		public void TwoRefineriesAtOneAnchorAreOneExcess()
		{
			var r = ExpansionMath.AssignRefineries(new CPos[] { new(12, 10), new(14, 12), new(60, 12) }, Anchors, 12);
			Assert.That(r.Excess, Is.EqualTo(1));
			Assert.That(r.Unassigned, Is.EqualTo(0));
			Assert.That(r.MaxDistance, Is.EqualTo(System.Math.Sqrt(20)).Within(1e-9));
		}

		[Test]
		public void ARefineryBeyondTheServeRadiusIsUnassignedAndExcess()
		{
			var r = ExpansionMath.AssignRefineries(new CPos[] { new(10, 40) }, Anchors, 12);
			Assert.That(r.Unassigned, Is.EqualTo(1));
			Assert.That(r.Excess, Is.EqualTo(1));
			Assert.That(r.MeanDistance, Is.EqualTo(30).Within(1e-9));
		}

		[Test]
		public void NoRefineriesNoExcess()
		{
			Assert.That(ExpansionMath.AssignRefineries(new CPos[0], Anchors, 12).Excess, Is.EqualTo(0));
		}

		[Test]
		public void AFieldNearASpreaderIsNotAnAnchorOfItsOwn()
		{
			var fields = new CPos[] { new(15, 10), new(100, 100) };
			var own = ExpansionMath.SpreaderlessFields(fields, new CPos[] { new(10, 10) }, 12);
			Assert.That(own, Is.EqualTo(new[] { new CPos(100, 100) }));
		}

		[Test]
		public void CategoryFollowsTheTagOrder()
		{
			Assert.That(ExpansionMath.Category(new HashSet<string> { "refinery", "production" }, null), Is.EqualTo("refinery"));
			Assert.That(ExpansionMath.Category(new HashSet<string> { "power" }, null), Is.EqualTo("power"));
			Assert.That(ExpansionMath.Category(new HashSet<string> { "defence" }, null), Is.EqualTo("defence"));
			Assert.That(ExpansionMath.Category(null, new HashSet<string> { "tech" }), Is.EqualTo("tech"));
			Assert.That(ExpansionMath.Category(null, new HashSet<string> { "support" }), Is.EqualTo("support"));
			Assert.That(ExpansionMath.Category(null, null), Is.EqualTo("other"));
		}
	}
}
