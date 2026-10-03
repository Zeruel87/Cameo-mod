#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System.Collections.Generic;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>One idle-pool unit offered to the staging planner: the actor and its value (the squad manager's UnitValue).</summary>
	public readonly record struct ArmyStagingUnit(Actor Actor, int Value);

	/// <summary>Where one pool unit should wait. The planner returns these; only the squad manager turns them into orders.</summary>
	public readonly record struct ArmyStagingOrder(Actor Actor, CPos Cell);

	/// <summary>One defence group of the plan: the sector it guards, its share of the idle army value, the cell it waits at NOW.</summary>
	public sealed class ArmyStagingGroup
	{
		public int Sector;
		public int SharePct;

		/// <summary>The cell the group is assigned to now: its own staging point, or the live sector's point while it answers an attack.</summary>
		public CPos Cell;

		/// <summary>The sector whose point <see cref="Cell"/> is (equals <see cref="Sector"/> unless the group converged on an attack elsewhere).</summary>
		public int TargetSector;
	}

	/// <summary>
	/// DESIGN 19.12 / AI_ARCHITECTURE 12.28: the planner's last result, an immutable-by-convention value for the units that
	/// consume it and for the situation log. Weights are in value units (an attacker's cost), already decayed.
	/// </summary>
	public sealed class ArmyStagingPlan
	{
		public int Tick;
		public CPos Centre;

		/// <summary>The decayed rim weight per 45-degree sector (index 0 = east, clockwise), prior included.</summary>
		public int[] RimValue = new int[8];

		/// <summary>The prior part of <see cref="RimValue"/> (spawn candidates and seen enemy defences).</summary>
		public int[] PriorValue = new int[8];

		/// <summary>The decayed weight of attacks that came from inside the defence ring.</summary>
		public int InsideValue;

		/// <summary>Per sector: the defence ring radius in cells and the staging cell on it (a few cells inside).</summary>
		public int[] RingRadius = new int[8];
		public CPos[] StagingCell = new CPos[8];

		/// <summary>Attacker value seen within LiveAttackTicks per sector (own events plus the DF-2 prediction), and from inside.</summary>
		public int[] LiveValue = new int[8];
		public int LiveInsideValue;

		public ArmyStagingGroup[] Groups = System.Array.Empty<ArmyStagingGroup>();
		public int ReservePct;

		/// <summary>The cell the reserve waits at now: the base centre, or a sector's staging point while it answers an attack.</summary>
		public CPos ReserveCell;

		/// <summary>The sector the reserve answers, -1 = the centre.</summary>
		public int ReserveTargetSector = -1;

		/// <summary>The inside share was at or over CentreSwitchPct: the whole army waits in the centre.</summary>
		public bool CentreMode;

		/// <summary>An attack is live now (own events within LiveAttackTicks) or the plan still holds the last live assignment.</summary>
		public bool Live;
	}

	/// <summary>
	/// DESIGN 19.12: the army waits at the front with the defences. A pure PLANNER — it computes where each part of the idle
	/// army should wait and never orders anything; the squad manager stays the only owner of the idle pool and of squads, and
	/// the base builder points factory rally points at <see cref="PrimaryStagingCell"/>. Nothing here reads an enemy actor the
	/// bot cannot see (spawn candidates are public map data; the rest is own attack events and fog memory). A consumer treats
	/// "no enabled provider" as today's behaviour, bit for bit.
	/// </summary>
	public interface IBotArmyStaging
	{
		/// <summary>The last plan, null before the first one (consumers then keep their own behaviour).</summary>
		ArmyStagingPlan Plan { get; }

		/// <summary>Ticks between staging orders per unit (the squad manager's cadence).</summary>
		int StagingIntervalTicks { get; }

		/// <summary>A pool unit within this many cells of its assigned point is left alone.</summary>
		int StagingRadiusCells { get; }

		/// <summary>The cell of the biggest group (or the centre in centre mode); null while there is no plan.</summary>
		CPos? PrimaryStagingCell { get; }

		/// <summary>The assigned cell (group or reserve) closest to <paramref name="from"/>; null while there is no plan.</summary>
		CPos? StagingCellNear(CPos from);

		/// <summary>True when <paramref name="cell"/> lies inside the defence ring the plan stages in (the staging answers it, not DF-2).</summary>
		bool Covers(CPos cell);

		/// <summary>
		/// Splits the pool across the groups and the reserve by value, in deterministic ActorID order, and appends one entry
		/// per unit to <paramref name="result"/>. Also tells the planner the idle army value (it sizes the merge of small groups).
		/// </summary>
		void AssignIdlePool(IReadOnlyList<ArmyStagingUnit> pool, List<ArmyStagingOrder> result);
	}
}
