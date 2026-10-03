#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software.
 * It is made available under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System.Collections.Generic;
using System.Linq;
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public sealed class DefenseCoveragePlannerTest
	{
		static readonly CPos Center = new(50, 50);

		// A 21 x 21 block of base cells around the centre.
		static CPos[] BaseCells() =>
			Enumerable.Range(40, 21).SelectMany(x => Enumerable.Range(40, 21).Select(y => new CPos(x, y))).ToArray();

		static CPos[] Uncovered(params (CPos Center, int Range)[] defences) =>
			BaseCells().Where(c => !DefenseCoveragePlanner.Covered(c, defences)).ToArray();

		[Test]
		public void OverlapWithAnExistingSameRoleDefenceIsNotCounted()
		{
			var none = Uncovered();
			var one = Uncovered((new CPos(45, 50), 6));

			var at = new CPos(47, 50);
			Assert.That(DefenseCoveragePlanner.NewlyCovered(at, 6, one), Is.LessThan(DefenseCoveragePlanner.NewlyCovered(at, 6, none)));

			// Far from the first one, nothing is lost.
			var far = new CPos(58, 50);
			Assert.That(DefenseCoveragePlanner.NewlyCovered(far, 3, one), Is.EqualTo(DefenseCoveragePlanner.NewlyCovered(far, 3, none) - OverlapOf(far, 3, new CPos(45, 50), 6)));
		}

		static int OverlapOf(CPos a, int ra, CPos b, int rb) =>
			BaseCells().Count(c => (c - a).LengthSquared <= ra * ra && (c - b).LengthSquared <= rb * rb);

		[Test]
		public void RolesAreIndependent()
		{
			// An AA tower covers for AA only: the ground role has no defence at all, so nothing is covered for it.
			var aa = new List<(CPos Center, int Range)> { (Center, 10) };
			var ground = new List<(CPos Center, int Range)>();
			Assert.That(DefenseCoveragePlanner.Covered(Center, aa), Is.True);
			Assert.That(DefenseCoveragePlanner.Covered(Center, ground), Is.False);
			Assert.That(DefenseCoveragePlanner.NewlyCovered(Center, 10, Uncovered()), Is.GreaterThan(0));
		}

		[Test]
		public void TheScorePrefersTheUncoveredSide()
		{
			var uncovered = Uncovered((new CPos(42, 50), 7));
			var west = new CPos(44, 50);
			var east = new CPos(56, 50);
			var sw = DefenseCoveragePlanner.Score(DefenseCoveragePlanner.NewlyCovered(west, 7, uncovered), 0, 0, 30, 40);
			var se = DefenseCoveragePlanner.Score(DefenseCoveragePlanner.NewlyCovered(east, 7, uncovered), 0, 0, 30, 40);
			Assert.That(se, Is.GreaterThan(sw));
		}

		[Test]
		public void ThreatAlignmentBreaksATie()
		{
			var threat = new CPos(90, 50);
			var toward = DefenseCoveragePlanner.ThreatAlignment(new CPos(60, 50), Center, threat);
			var away = DefenseCoveragePlanner.ThreatAlignment(new CPos(40, 50), Center, threat);
			Assert.That(toward, Is.EqualTo(100));
			Assert.That(away, Is.EqualTo(-100));
			Assert.That(DefenseCoveragePlanner.Score(10, 50, toward, 30, 40), Is.GreaterThan(DefenseCoveragePlanner.Score(10, 50, away, 30, 40)));
		}

		[Test]
		public void TheOuterEdgeIsPreferredAtEqualCoverage()
		{
			var inner = DefenseCoveragePlanner.Edgeness(new CPos(55, 50), Center, 20);
			var outer = DefenseCoveragePlanner.Edgeness(new CPos(68, 50), Center, 20);
			Assert.That(outer, Is.GreaterThan(inner));
			Assert.That(DefenseCoveragePlanner.Edgeness(new CPos(90, 50), Center, 20), Is.EqualTo(100));
			Assert.That(DefenseCoveragePlanner.Score(10, outer, 0, 30, 40), Is.GreaterThan(DefenseCoveragePlanner.Score(10, inner, 0, 30, 40)));
		}

		[Test]
		public void CoverageOutweighsEdgeAndThreat()
		{
			// One new cell is worth 100; the full edge + threat bonus is 30 * 100 + 40 * 100 = 7000, so
			// a cell covering 80 more base cells wins over a perfectly placed one covering nothing new.
			Assert.That(DefenseCoveragePlanner.Score(80, 0, 0, 30, 40), Is.GreaterThan(DefenseCoveragePlanner.Score(0, 100, 100, 30, 40)));
			Assert.That(DefenseCoveragePlanner.Score(8, 0, 0, 30, 40), Is.GreaterThan(DefenseCoveragePlanner.Score(0, 100, 100, 30, 40)),
				"eight newly covered base cells beat the full edge + enemy-side bonus: coverage dominates");
		}

		static readonly IReadOnlyDictionary<string, HashSet<string>> Specialties = new Dictionary<string, HashSet<string>>
		{
			["guard"] = new() { BotUnitRole.AntiInfantry },
			["advanced"] = new() { BotUnitRole.AntiArmour },
			["sky"] = new() { BotUnitRole.AntiAir },
			["multi"] = new() { BotUnitRole.AntiInfantry, BotUnitRole.AntiArmour },
			["none"] = new(),
		};

		[Test]
		public void AnInfantryTowerDoesNotCoverForAntiAir()
		{
			var guardRoles = DefenseCoveragePlanner.RolesOf(Specialties, "guard", false);
			Assert.That(guardRoles, Does.Contain(BotUnitRole.AntiInfantry));
			Assert.That(guardRoles, Does.Not.Contain(BotUnitRole.AntiAir));

			// Coverage is kept per role: the tower is in the anti-infantry list only, so the anti-air list leaves the cell uncovered.
			var byRole = new Dictionary<string, List<(CPos Center, int Range)>>
			{
				[BotUnitRole.AntiInfantry] = new() { (Center, 12) },
				[BotUnitRole.AntiAir] = new(),
			};
			Assert.That(DefenseCoveragePlanner.Covered(Center, byRole[BotUnitRole.AntiInfantry]), Is.True);
			Assert.That(DefenseCoveragePlanner.Covered(Center, byRole[BotUnitRole.AntiAir]), Is.False);
		}

		[Test]
		public void AMultiRoleDefenceSumsItsRoles()
		{
			var roles = DefenseCoveragePlanner.RolesOf(Specialties, "multi", false);
			Assert.That(roles, Has.Count.EqualTo(2));

			// Anti-infantry already covers the centre; anti-armour covers nothing: the sum counts both roles' uncovered cells.
			var all = Uncovered();
			var covered = new List<(CPos Center, int Range)> { (Center, 4) };
			var perRole = new Dictionary<string, CPos[]>
			{
				[BotUnitRole.AntiInfantry] = all.Where(c => !DefenseCoveragePlanner.Covered(c, covered)).ToArray(),
				[BotUnitRole.AntiArmour] = all,
			};
			var sum = roles.Sum(r => DefenseCoveragePlanner.NewlyCovered(Center, 4, perRole[r]));
			Assert.That(sum, Is.EqualTo(DefenseCoveragePlanner.NewlyCovered(Center, 4, all)));
			Assert.That(sum, Is.GreaterThan(0));
			Assert.That(sum, Is.LessThan(2 * DefenseCoveragePlanner.NewlyCovered(Center, 4, all)));
		}

		[Test]
		public void ARolelessDefenceFallsBackToAntiAirOrAntiArmour()
		{
			Assert.That(DefenseCoveragePlanner.RolesOf(Specialties, "none", true), Is.EquivalentTo(new[] { BotUnitRole.AntiAir }));
			Assert.That(DefenseCoveragePlanner.RolesOf(Specialties, "missing", false), Is.EquivalentTo(new[] { BotUnitRole.AntiArmour }));
		}

		[Test]
		public void TheQuotaSwitchesBetweenRingAndInterior()
		{
			Assert.That(DefenseCoveragePlanner.PlacePerimeter(0, 0, 75), Is.True);
			Assert.That(DefenseCoveragePlanner.PlacePerimeter(2, 2, 75), Is.True);
			Assert.That(DefenseCoveragePlanner.PlacePerimeter(3, 1, 75), Is.False);
			Assert.That(DefenseCoveragePlanner.PlacePerimeter(6, 3, 75), Is.True);

			// Placing in the wanted ring in turn converges on the share.
			int ring = 0, inside = 0;
			for (var i = 0; i < 20; i++)
			{
				if (DefenseCoveragePlanner.PlacePerimeter(ring, inside, 75))
					ring++;
				else
					inside++;
			}

			Assert.That(ring, Is.EqualTo(15));
		}

		// DEF-3: building cells within FrontLinkRadius of each other form one front; a gap
		// beyond it splits the map into separate fronts (the outpost is its own front).
		[Test]
		public void ClusterFrontsSplitsOnTheLinkRadius()
		{
			var cells = new[]
			{
				new CPos(10, 10), new CPos(12, 10), new CPos(10, 13),   // main base blob
				new CPos(40, 40), new CPos(41, 40),                     // remote outpost
			};
			var fronts = DefenseCoveragePlanner.ClusterFronts(cells, 14);
			Assert.That(fronts.Count, Is.EqualTo(2));
			Assert.That(fronts[0].Count, Is.EqualTo(3));
			Assert.That(fronts[1].Count, Is.EqualTo(2));

			// A chain bridging the gap joins them back into one front (single linkage is
			// transitive: (24,24) touches the blob, (33,30) chains onward to the outpost).
			var bridged = cells.Concat(new[] { new CPos(24, 24), new CPos(33, 30) }).ToArray();
			Assert.That(DefenseCoveragePlanner.ClusterFronts(bridged, 14).Count, Is.EqualTo(1));
		}

		// DEF-3: the next defence goes to the front with the most uncovered cells — the naked
		// outpost beats the covered main base even though the base has far more cells.
		[Test]
		public void TheNakedOutpostFrontWinsTheNextDefence()
		{
			var cells = new[]
			{
				new CPos(10, 10), new CPos(12, 10), new CPos(10, 13), new CPos(11, 11),
				new CPos(40, 40), new CPos(41, 40),
			};
			var coveringTheBase = new[] { (new CPos(11, 11), 6) };
			var pick = DefenseCoveragePlanner.PickFrontCenter(cells, coveringTheBase, 14);
			Assert.That(pick, Is.Not.Null, "the outpost's cells are uncovered — it wins");
			Assert.That(pick.Value.X, Is.EqualTo(40), "outpost centroid x");
			Assert.That(pick.Value.Y, Is.EqualTo(40), "outpost centroid y");

			// Cover the outpost too and nothing remains naked: no retarget.
			var coveringAll = new[] { (new CPos(11, 11), 6), (new CPos(40, 40), 5) };
			Assert.That(DefenseCoveragePlanner.PickFrontCenter(cells, coveringAll, 14), Is.Null);

			// With no defences at all the bigger front (the base) wins by the tie-break.
			var naked = DefenseCoveragePlanner.PickFrontCenter(cells, new (CPos, int)[0], 14);
			Assert.That(naked, Is.Not.Null);
			Assert.That(naked.Value.X, Is.LessThan(20), "all naked: the larger base front wins");
		}

		// CN4: frontier roles (Military/Outpost) outrank the interior — a naked front in a
		// frontier region wins the next defence even when an interior front is barer still.
		[Test]
		public void TheFrontierFrontWinsOverTheInterior()
		{
			var cells = new[]
			{
				new CPos(10, 10), new CPos(12, 10), new CPos(10, 13),   // interior front (Core role)
				new CPos(40, 40), new CPos(41, 40),                    // frontier front (Military role)
			};
			var roleOf = (CPos c) => c.X > 30 ? RegionRole.Military : RegionRole.Core;

			var pick = DefenseCoveragePlanner.PickFrontierCenter(
				cells, new (CPos, int)[0], 14, roleOf);
			Assert.That(pick, Is.Not.Null);
			Assert.That(pick.Value.X, Is.EqualTo(40), "the frontier front wins although the interior has more cells");

			// A covered frontier lets the fallback see the naked interior: frontier pick returns null.
			var coveringFrontier = new[] { (new CPos(40, 40), 6), (new CPos(41, 40), 6) };
			Assert.That(DefenseCoveragePlanner.PickFrontierCenter(cells, coveringFrontier, 14, roleOf), Is.Null);

			// No frontier roles at all → no answer (caller falls back to the plain pick).
			var pickNoFrontier = DefenseCoveragePlanner.PickFrontierCenter(
				cells, new (CPos, int)[0], 14, _ => RegionRole.Economy);
			Assert.That(pickNoFrontier, Is.Null);
		}
	}
}
