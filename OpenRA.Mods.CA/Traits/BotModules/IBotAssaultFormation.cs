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
	/// The tunables of one assault fan-out: the arc geometry a Rush squad spreads
	/// onto around its target before committing, so the wave arrives from several
	/// bearings and fires together instead of walking single-file into the guns
	/// (the "line of death"). All fields are cells/ticks/percent — no floats, so
	/// every peer computes the identical plan.
	/// </summary>
	public readonly struct AssaultFormationSettings
	{
		/// <summary>Squads smaller than this skip the fan-out entirely — a token escort gains nothing from the ceremony.</summary>
		public readonly int MinSquadSize;

		/// <summary>Cells from the target cell to each slot on the arc.</summary>
		public readonly int FanoutRadiusCells;

		/// <summary>Total arc span in degrees, centered on the far side of the target from the squad's approach bearing.</summary>
		public readonly int ArcDegrees;

		/// <summary>Commits early once this percent of orderable members stand within <see cref="SlotReachCells"/> of their slot.</summary>
		public readonly int AssemblePercent;

		/// <summary>World-tick budget for the fan-out; at expiry the squad commits wherever its units stand.</summary>
		public readonly int StageDeadlineTicks;

		/// <summary>An advancing squad leader this close to the target (cells) enters the fan-out — larger than the radius so the fan forms before arrival.</summary>
		public readonly int FanoutTriggerCells;

		/// <summary>A member whose centre sits within this many cells of its slot's cell centre counts as assembled.</summary>
		public readonly int SlotReachCells;

		public AssaultFormationSettings(int minSquadSize, int fanoutRadiusCells, int arcDegrees,
			int assemblePercent, int stageDeadlineTicks, int fanoutTriggerCells, int slotReachCells)
		{
			MinSquadSize = minSquadSize;
			FanoutRadiusCells = fanoutRadiusCells;
			ArcDegrees = arcDegrees;
			AssemblePercent = assemblePercent;
			StageDeadlineTicks = stageDeadlineTicks;
			FanoutTriggerCells = fanoutTriggerCells;
			SlotReachCells = slotReachCells;
		}
	}

	/// <summary>
	/// Assault fan-out provider (the line-of-death fix): hands the
	/// <see cref="AssaultFormationSettings"/> a Rush squad's fan-out phase runs
	/// with. Implemented by a condition-gated module so every tunable lives on
	/// its Info; the squad state machine stays the single order authority and
	/// only consults this. An absent or disabled provider means the old
	/// single-point advance — identical to no provider at all.
	/// </summary>
	public interface IBotAssaultFormation
	{
		/// <summary>
		/// Whether a fan-out may arm for <paramref name="squad"/> against
		/// <paramref name="targetCell"/> right now, and the settings it would run
		/// with. Called from squad-state consults — must be cheap, side-effect
		/// free and sync-safe. Implementations may decline to re-arm the same
		/// target inside a cooldown so a committed squad is not looped back onto
		/// the arc forever.
		/// </summary>
		bool TryGetAssaultFormation(SquadCA squad, CPos targetCell, out AssaultFormationSettings settings);

		/// <summary>
		/// The fan-out state reports that it armed a plan for
		/// <paramref name="targetCell"/> — the provider records it for the
		/// cooldown check in <see cref="TryGetAssaultFormation"/>.
		/// </summary>
		void RecordFanout(SquadCA squad, CPos targetCell);
	}
}
