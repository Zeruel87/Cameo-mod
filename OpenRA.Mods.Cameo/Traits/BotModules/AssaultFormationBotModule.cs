#region Copyright & License Information
/*
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System.Collections.Generic;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.CA.Traits.BotModules.Squads;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	// AF-1 (the "line of death" fix): the IBotAssaultFormation provider for
	// genericbot's Rush assault squads. Before this, every member of a committed
	// squad attack-moved to one shared target point and arrived single-file —
	// the first unit into the guns died alone, then the next. With the provider
	// armed, GroundUnitsAssaultFanoutStateCA inserts a fan-out phase between the
	// rally and the commit: AssaultFormationPlanner lays one slot per member on
	// an arc around the target (centered on the far side from the approach
	// bearing, so the wave wraps and fires together), the squad walks the ring,
	// and the commit lands once AssemblePercent are in place or the deadline
	// burns down. Contact mid-fan commits immediately — nobody fights alone.
	//
	// Settings-only, like the siege advisor seam: this module issues no orders —
	// the squad state machine is the single order authority. The per-squad
	// refanout cooldown (recorded on each armed plan) stops a committed squad
	// from being looped back onto the same arc forever when nothing visible
	// answers the advance; a different target fans freely.
	[TraitLocation(SystemActors.Player)]
	[Desc("Arms the pre-commit assault fan-out for Rush squads (the line-of-death fix): settings for the target-centered arc the squad spreads onto before engaging together.")]
	public class AssaultFormationBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Squads smaller than this skip the fan-out and advance as before.")]
		public readonly int MinSquadSize = 4;

		[Desc("Cells from the target cell to each slot on the arc.")]
		public readonly int FanoutRadiusCells = 8;

		[Desc("Total arc span in degrees, centered on the far side of the target from the squad's approach bearing.")]
		public readonly int ArcDegrees = 180;

		[Desc("Commit once this percent of orderable members are at their slots; the rest pile in behind.")]
		public readonly int AssemblePercent = 60;

		[Desc("World ticks before the squad commits wherever its units stand.")]
		public readonly int StageDeadlineTicks = 500;

		[Desc("A squad leader this close to the target (cells) enters the fan-out — beyond FanoutRadiusCells so the fan forms before arrival.")]
		public readonly int FanoutTriggerCells = 12;

		[Desc("A member this close to its slot (cells) counts as assembled.")]
		public readonly int SlotReachCells = 2;

		[Desc("World ticks before the same target may be fanned again by the same squad.")]
		public readonly int RefanoutCooldownTicks = 750;

		public override object Create(ActorInitializer init) { return new AssaultFormationBotModule(init.Self, this); }
	}

	public class AssaultFormationBotModule : ConditionalTrait<AssaultFormationBotModuleInfo>, IBotAssaultFormation
	{
		readonly World world;

		// Squad -> (fanned target cell, fan-out start tick). Read on every consult
		// to refuse a prompt re-fan of the same ground; pruned on record.
		readonly Dictionary<SquadCA, (CPos Cell, int Tick)> recentFanouts = new();

		public AssaultFormationBotModule(Actor self, AssaultFormationBotModuleInfo info)
			: base(info)
		{
			world = self.World;
		}

		public bool TryGetAssaultFormation(SquadCA squad, CPos targetCell, out AssaultFormationSettings settings)
		{
			settings = new AssaultFormationSettings(
				Info.MinSquadSize, Info.FanoutRadiusCells, Info.ArcDegrees, Info.AssemblePercent,
				Info.StageDeadlineTicks, Info.FanoutTriggerCells, Info.SlotReachCells);

			if (IsTraitDisabled)
				return false;

			// The same-target cooldown: a squad that already fanned onto this
			// ground commits inward instead of re-orbiting the ring. Read-only —
			// the entry is overwritten by RecordFanout on the next arm and
			// pruned there once stale.
			if (recentFanouts.TryGetValue(squad, out var rec))
			{
				var radiusSq = Info.FanoutRadiusCells * Info.FanoutRadiusCells;
				var sameGround = (rec.Cell - targetCell).LengthSquared <= radiusSq;
				if (sameGround && world.WorldTick - rec.Tick < Info.RefanoutCooldownTicks)
					return false;
			}

			return true;
		}

		public void RecordFanout(SquadCA squad, CPos targetCell)
		{
			recentFanouts[squad] = (targetCell, world.WorldTick);

			// Prune entries whose cooldown has fully expired — dissolved squads
			// never record again, so the record site does the housekeeping.
			if (recentFanouts.Count > 32)
			{
				var stale = new List<SquadCA>();
				foreach (var kv in recentFanouts)
					if (world.WorldTick - kv.Value.Tick > Info.RefanoutCooldownTicks)
						stale.Add(kv.Key);

				foreach (var s in stale)
					recentFanouts.Remove(s);
			}
		}
	}
}
