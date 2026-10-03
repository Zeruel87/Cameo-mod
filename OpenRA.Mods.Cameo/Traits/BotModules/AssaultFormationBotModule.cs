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
	// The "line of death" fix, unified (2026-10-02, AI_ARCHITECTURE 12.7a): the
	// IBotAssaultFormation provider for genericbot's Rush squads. The geometry and
	// state machine are CV's - ConcaveEvalCA plans a range-matched concave arc and
	// GroundUnitsConcaveStateCA deploys, commits with staggered AttackMove orders and
	// hands over to the attack state. This module is the ONLY place the tunables live
	// and its presence (RequiresCondition genericbot && assault_fanout) is the ONLY
	// switch: classic has no provider, so the old single-point advance stays
	// bit-identical.
	//
	// Settings-only, like the siege advisor seam: this module issues no orders - the
	// squad state machine is the single order authority. The per-squad same-target
	// cooldown (restarted on arm, commit and abort) stops a squad from being looped
	// back into the formation forever; a different target deploys freely.
	[TraitLocation(SystemActors.Player)]
	[Desc("Arms the pre-commit concave deployment for Rush squads (the line-of-death fix): the settings a squad deploys with before engaging together.")]
	public class AssaultFormationBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Squads with fewer weaponed ground members skip the deployment and advance as before.")]
		public readonly int MinSquadSize = 4;

		[Desc("Cells from the frontline centroid within which an observed enemy (or the squad target) triggers the deployment.")]
		public readonly int FanoutTriggerCells = 16;

		[Desc("Cells each member stages outside its own weapon range (and the enemy front depth).")]
		public readonly int StageMarginCells = 2;

		[Desc("Members whose staging radii lie within this many cells share one arc.")]
		public readonly int RankBandCells = 2;

		[Desc("Arc length per member in WDist units (1024 = 1 cell); infantry take half. Bigger armies are wider.")]
		public readonly int Spacing = 1536;

		[Desc("Spacing in WDist units the arc may compress to before members overflow to a second arc.")]
		public readonly int MinSpacing = 1024;

		[Desc("Widest arc in degrees; a bigger army compresses spacing, then overflows to a second arc.")]
		public readonly int ArcDegrees = 150;

		[Desc("WDist units between an arc and its overflow arc (2048 = 2 cells).")]
		public readonly int RankGap = 2048;

		[Desc("Percent of slots that must be reachable terrain, else the deployment aborts and the squad engages as before.")]
		public readonly int MinValidSlotPct = 50;

		[Desc("Cells around a slot searched for a cell the member can enter, stay in and path to.")]
		public readonly int SlotReachCells = 2;

		[Desc("Commit once this percent of placed members stand within 1.5 cells of their slot.")]
		public readonly int AssemblePercent = 80;

		[Desc("World ticks before the squad commits wherever its units stand.")]
		public readonly int StageDeadlineTicks = 150;

		[Desc("World ticks after an arm, commit or abort before the same squad may deploy again against the same ground.")]
		public readonly int RefanoutCooldownTicks = 750;

		public override object Create(ActorInitializer init) { return new AssaultFormationBotModule(init.Self, this); }
	}

	public class AssaultFormationBotModule : ConditionalTrait<AssaultFormationBotModuleInfo>, IBotAssaultFormation
	{
		readonly World world;

		// Squad -> (deployed target cell, last arm/commit/abort tick). Read on every consult
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
				Info.MinSquadSize, Info.FanoutTriggerCells, Info.StageMarginCells, Info.RankBandCells,
				Info.Spacing, Info.MinSpacing, Info.ArcDegrees, Info.RankGap, Info.MinValidSlotPct,
				Info.SlotReachCells, Info.AssemblePercent, Info.StageDeadlineTicks);

			if (IsTraitDisabled)
				return false;

			// The same-target cooldown: a squad that already deployed against this
			// ground engages as before instead of re-forming. Read-only - the
			// entry is overwritten by RecordFanout and pruned there once stale.
			if (recentFanouts.TryGetValue(squad, out var rec))
			{
				var radiusSq = Info.FanoutTriggerCells * Info.FanoutTriggerCells;
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
