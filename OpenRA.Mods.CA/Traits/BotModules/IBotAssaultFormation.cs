#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using OpenRA.Mods.CA.Traits.BotModules.Squads;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// The tunables of one concave deployment (AI_ARCHITECTURE 12.7a): how a Rush squad
	/// that meets the enemy deploys into a range-matched arc before committing, so the
	/// wave fires together instead of walking single-file into the guns (the "line of
	/// death"). Cells, ticks, percent and WDist units only - no floats, so every peer
	/// computes the identical plan.
	/// </summary>
	public readonly struct AssaultFormationSettings
	{
		/// <summary>Squads with fewer weaponed ground members skip the deployment entirely.</summary>
		public readonly int MinSquadSize;

		/// <summary>Cells from the frontline centroid within which an observed enemy (or the squad target) triggers the deployment.</summary>
		public readonly int FanoutTriggerCells;

		/// <summary>Cells each member stages outside its own weapon range (and the enemy front depth).</summary>
		public readonly int StageMarginCells;

		/// <summary>Members whose staging radii lie within this many cells share one arc.</summary>
		public readonly int RankBandCells;

		/// <summary>Arc length per member in WDist units (1024 = 1 cell); infantry take half.</summary>
		public readonly int Spacing;

		/// <summary>Spacing in WDist units the arc may compress to before members overflow to a second arc.</summary>
		public readonly int MinSpacing;

		/// <summary>Widest arc in degrees; a bigger army compresses spacing, then overflows to a second arc.</summary>
		public readonly int ArcDegrees;

		/// <summary>WDist units between an arc and its overflow arc (2048 = 2 cells).</summary>
		public readonly int RankGap;

		/// <summary>Percent of slots that must be reachable terrain, else the deployment aborts and the squad engages as before.</summary>
		public readonly int MinValidSlotPct;

		/// <summary>Cells around a slot searched for a cell the member can enter, stay in and path to (terrain snap).</summary>
		public readonly int SlotReachCells;

		/// <summary>Commits once this percent of placed members stand within 1.5 cells of their slot.</summary>
		public readonly int AssemblePercent;

		/// <summary>World-tick budget for forming; at expiry the squad commits wherever its units stand.</summary>
		public readonly int StageDeadlineTicks;

		public AssaultFormationSettings(int minSquadSize, int fanoutTriggerCells, int stageMarginCells, int rankBandCells,
			int spacing, int minSpacing, int arcDegrees, int rankGap, int minValidSlotPct,
			int slotReachCells, int assemblePercent, int stageDeadlineTicks)
		{
			MinSquadSize = minSquadSize;
			FanoutTriggerCells = fanoutTriggerCells;
			StageMarginCells = stageMarginCells;
			RankBandCells = rankBandCells;
			Spacing = spacing;
			MinSpacing = minSpacing;
			ArcDegrees = arcDegrees;
			RankGap = rankGap;
			MinValidSlotPct = minValidSlotPct;
			SlotReachCells = slotReachCells;
			AssemblePercent = assemblePercent;
			StageDeadlineTicks = stageDeadlineTicks;
		}
	}

	/// <summary>
	/// Assault formation provider (the line-of-death fix): hands the
	/// <see cref="AssaultFormationSettings"/> a Rush squad's concave deployment runs
	/// with. Implemented by a condition-gated module so every tunable lives on
	/// its Info and its presence is the only switch; the squad state machine stays
	/// the single order authority and only consults this. An absent or disabled
	/// provider means the old single-point advance - identical to no provider at all.
	/// </summary>
	public interface IBotAssaultFormation
	{
		/// <summary>
		/// Whether a deployment may arm for <paramref name="squad"/> against
		/// <paramref name="targetCell"/> right now, and the settings it would run
		/// with. Called from squad-state consults — must be cheap, side-effect
		/// free and sync-safe. Implementations may decline to re-arm the same
		/// target inside a cooldown so a committed squad is not looped back onto
		/// the arc forever.
		/// </summary>
		bool TryGetAssaultFormation(SquadCA squad, CPos targetCell, out AssaultFormationSettings settings);

		/// <summary>
		/// The concave state reports that it armed (or committed/aborted) a deployment for
		/// <paramref name="targetCell"/> - the provider (re)starts the cooldown
		/// clock for the cooldown check in <see cref="TryGetAssaultFormation"/>.
		/// </summary>
		void RecordFanout(SquadCA squad, CPos targetCell);
	}
}
