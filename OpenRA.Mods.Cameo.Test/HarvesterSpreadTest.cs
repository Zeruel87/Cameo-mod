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
using System.Linq;
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	// Harvester field spread (flagged: HarvesterBotModuleCA.SpreadHarvestFields). Idle harvesters used
	// to pathfind to the nearest resource cell of ANY field, so N harvesters dog-piled the home field
	// while far fields sat empty. The filter is field-level: a cell counts only when its field — the
	// nearest indice centre, same rule as ResourceMapBotModule.FindClosestIndiceFromCPos — has fewer
	// own harvesters than its capacity (ResourceCells / cellsPerHarvester, minimum 1). All-saturated
	// falls back to the full set so the pathfind never starves.
	[TestFixture]
	public class HarvesterSpreadTest
	{
		static List<(CPos Center, int ResourceCells, int Harvesters)> Fields(
			params (CPos Center, int ResourceCells, int Harvesters)[] fields) => fields.ToList();

		[Test]
		public void UnsaturatedFieldIsPreferred()
		{
			var homeField = new[] { new CPos(10, 10), new CPos(11, 10), new CPos(12, 10) };
			var farField = new[] { new CPos(60, 40), new CPos(61, 40) };
			var fields = Fields(
				(new CPos(10, 10), 20, 5),   // capacity 20/4 = 5, fully crewed
				(new CPos(60, 40), 20, 1));  // capacity 5, one harvester -> can absorb more

			var picked = HarvesterBotModuleCA.FilterUnsaturatedFields(
				homeField.Concat(farField), fields, 4).ToList();

			Assert.That(picked, Is.EquivalentTo(farField),
				"cells of a field at capacity must not be offered to the idle harvester");
		}

		[Test]
		public void SaturatedBoundaryIsInclusive()
		{
			// 19 cells / 4 = capacity 4: the fourth harvester saturates the field.
			var cells = new[] { new CPos(10, 10), new CPos(60, 40) };
			var fields = Fields(
				(new CPos(10, 10), 19, 4),
				(new CPos(60, 40), 19, 3));

			var picked = HarvesterBotModuleCA.FilterUnsaturatedFields(cells, fields, 4).ToList();

			Assert.That(picked, Is.EquivalentTo(new[] { new CPos(60, 40) }),
				"Harvesters == capacity must count as saturated; capacity - 1 must not");
		}

		[Test]
		public void CapacityFloorIsOneHarvester()
		{
			// A field smaller than cellsPerHarvester still absorbs a single harvester.
			var tinyField = new[] { new CPos(10, 10) };
			var fields = Fields(
				(new CPos(10, 10), 2, 0),   // capacity max(1, 2/4) = 1, nobody there
				(new CPos(60, 40), 20, 0));

			var picked = HarvesterBotModuleCA.FilterUnsaturatedFields(tinyField, fields, 4).ToList();
			Assert.That(picked, Is.EquivalentTo(tinyField), "an empty tiny field takes one harvester");

			fields = Fields(
				(new CPos(10, 10), 2, 1),   // same field, now crewed to its floor capacity
				(new CPos(60, 40), 20, 0));

			picked = HarvesterBotModuleCA.FilterUnsaturatedFields(
				tinyField.Concat(new[] { new CPos(60, 40) }), fields, 4).ToList();
			Assert.That(picked, Is.EquivalentTo(new[] { new CPos(60, 40) }),
				"one harvester already saturates a sub-capacity field");
		}

		[Test]
		public void AllSaturatedFallsBackToFullSet()
		{
			var cells = new[] { new CPos(10, 10), new CPos(60, 40) };
			var fields = Fields(
				(new CPos(10, 10), 20, 9),
				(new CPos(60, 40), 20, 5));

			var picked = HarvesterBotModuleCA.FilterUnsaturatedFields(cells, fields, 4).ToList();

			Assert.That(picked, Is.EquivalentTo(cells),
				"every field at capacity: the caller must still see the full target set");
		}

		[Test]
		public void NoFieldsPassesEverythingThrough()
		{
			var cells = new[] { new CPos(10, 10), new CPos(60, 40) };

			var picked = HarvesterBotModuleCA.FilterUnsaturatedFields(
				cells, new List<(CPos Center, int ResourceCells, int Harvesters)>(), 4).ToList();

			Assert.That(picked, Is.EquivalentTo(cells), "no occupancy snapshot, no filtering");
		}

		[Test]
		public void NearestCentreWinsTiesDeterministically()
		{
			// A cell equidistant between two field centres belongs to the FIRST field in the list —
			// the strict < in FindClosestIndiceFromCPos keeps the earliest index on a tie. A second
			// cell clearly inside the unsaturated field keeps the output non-empty, so the tie's
			// resolution is observable rather than masked by the all-saturated fallback.
			var cells = new[] { new CPos(30, 10), new CPos(51, 10) };
			var saturatedFirst = Fields(
				(new CPos(10, 10), 20, 5),   // saturated — wins the tie when listed first
				(new CPos(50, 10), 20, 0));  // unsaturated
			var unsaturatedFirst = Fields(
				(new CPos(50, 10), 20, 0),
				(new CPos(10, 10), 20, 5));

			Assert.That(HarvesterBotModuleCA.FilterUnsaturatedFields(cells, saturatedFirst, 4),
				Is.EquivalentTo(new[] { new CPos(51, 10) }),
				"tie resolved to the saturated first field -> the border cell drops");
			Assert.That(HarvesterBotModuleCA.FilterUnsaturatedFields(cells, unsaturatedFirst, 4),
				Is.EquivalentTo(cells),
				"tie resolved to the unsaturated first field -> both cells stay");
		}

		[Test]
		public void OutputKeepsInputOrder()
		{
			// The pathfind only sees the surviving cells; their relative order must be stable so
			// equal-cost ties resolve the same way every tick.
			var cells = new[] { new CPos(62, 40), new CPos(60, 40), new CPos(61, 40) };
			var fields = Fields((new CPos(60, 40), 20, 0));

			var picked = HarvesterBotModuleCA.FilterUnsaturatedFields(cells, fields, 4).ToList();

			Assert.That(picked, Is.EqualTo(cells), "filtered output must preserve candidate order");
		}
	}
}
