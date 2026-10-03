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
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.CA.Traits.BotModules.Squads;

namespace OpenRA.Mods.Cameo.Test
{
	// CN3 (AI_MASTER_PLAN §3, crystallized-nexus port): the stealth draftable
	// predicate, the remembered-detector coverage check, and the flee score are
	// the pure seams of StealthStatesCA - the world-touching halves (target
	// picking, order issue) are exercised by the increment A/B, not unit tests.
	[TestFixture]
	public class StealthSquadTest
	{
		static WPos CellCenter(CPos cell) => new(cell.X * 1024 + 512, cell.Y * 1024 + 512, 0);

		[Test]
		public void DraftableRequiresCloakAndArmedGround()
		{
			Assert.That(SquadManagerBotModuleCA.IsStealthDraftable(true, true, false, false), Is.True);

			// A cloak-capable unit with no attack is a scout, not an ambusher.
			Assert.That(SquadManagerBotModuleCA.IsStealthDraftable(true, false, false, false), Is.False);

			// An armed unit that cannot cloak infiltrates nothing.
			Assert.That(SquadManagerBotModuleCA.IsStealthDraftable(false, true, false, false), Is.False);
		}

		[Test]
		public void DraftableRejectsNavalAndAir()
		{
			Assert.That(SquadManagerBotModuleCA.IsStealthDraftable(true, true, true, false), Is.False);
			Assert.That(SquadManagerBotModuleCA.IsStealthDraftable(true, true, false, true), Is.False);
		}

		[Test]
		public void CoverageUsesObservedRangePlusMargin()
		{
			var detectors = new[]
			{
				new BotKnownDetector(new CPos(10, 10), rangeCells: 5, lastSeenTick: 100, enemy: null)
			};

			// Dead centre of the detector cell is covered.
			Assert.That(StealthHelpersCA.CoveredByKnownDetector(detectors, CellCenter,
				new WPos(10 * 1024 + 512, 10 * 1024 + 512, 0)), Is.True);

			// Range 5 + 2-cell margin = 7 cells reach: a point 6 cells east is inside.
			Assert.That(StealthHelpersCA.CoveredByKnownDetector(detectors, CellCenter,
				new WPos(16 * 1024 + 512, 10 * 1024 + 512, 0)), Is.True);

			// 8 cells east is outside the bubble.
			Assert.That(StealthHelpersCA.CoveredByKnownDetector(detectors, CellCenter,
				new WPos(18 * 1024 + 512, 10 * 1024 + 512, 0)), Is.False);
		}

		[Test]
		public void NoDetectorsMeansNoCoverage()
		{
			Assert.That(StealthHelpersCA.CoveredByKnownDetector(new BotKnownDetector[0], CellCenter,
				new WPos(1024, 1024, 0)), Is.False);
		}

		[Test]
		public void RetreatScorePrefersFarFromThreats()
		{
			var anchor = new CPos(0, 0);
			var candidate = new CPos(5, 5);
			var candidatePos = CellCenter(candidate);
			var reachSq = (long)WDist.FromCells(10).Length * WDist.FromCells(10).Length;

			// No threat in reach scores the flat million; a threat on the
			// candidate drops the score below it.
			var openScore = StealthHelpersCA.ScoreRetreatCell(candidate, anchor, candidatePos,
				new List<(WPos, CPos)>(), reachSq);
			var nearThreat = new List<(WPos, CPos)> { (candidatePos, candidate) };
			var threatenedScore = StealthHelpersCA.ScoreRetreatCell(candidate, anchor, candidatePos,
				nearThreat, reachSq);
			Assert.That(openScore, Is.GreaterThan(threatenedScore));
		}

		[Test]
		public void RetreatScoreIsDeterministic()
		{
			var anchor = new CPos(20, 20);
			var candidate = new CPos(12, 20);
			var candidatePos = CellCenter(candidate);
			var reachSq = (long)WDist.FromCells(10).Length * WDist.FromCells(10).Length;
			var threats = new List<(WPos, CPos)>
			{
				(CellCenter(new CPos(10, 10)), new CPos(10, 10)),
				(CellCenter(new CPos(14, 25)), new CPos(14, 25))
			};

			var first = StealthHelpersCA.ScoreRetreatCell(candidate, anchor, candidatePos, threats, reachSq);
			var second = StealthHelpersCA.ScoreRetreatCell(candidate, anchor, candidatePos, threats, reachSq);
			Assert.That(first, Is.EqualTo(second));

			// A candidate farther from the nearest threat scores higher, anchor
			// distance held equal.
			var safer = new CPos(18, 20);
			var saferScore = StealthHelpersCA.ScoreRetreatCell(safer, anchor, CellCenter(safer), threats, reachSq);
			Assert.That(saferScore, Is.GreaterThan(first));
		}
	}
}
