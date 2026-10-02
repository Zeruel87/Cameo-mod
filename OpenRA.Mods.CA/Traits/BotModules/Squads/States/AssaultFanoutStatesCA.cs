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
using System.Linq;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits.BotModules.Squads
{
	// AF-1 (the "line of death" fix): between the rally/advance and the commit,
	// a Rush squad spreads onto an arc of slots around the target — centered on
	// the far side from its approach bearing — then commits together, so the
	// wave arrives from several bearings and every member fires at once instead
	// of feeding one corridor. Geometry comes from AssaultFormationPlanner,
	// tunables from the IBotAssaultFormation provider (a Cameo module; the squad
	// states remain the only order authority). No provider, a small squad, or an
	// invalid target falls straight back to the plain attack-move — the old
	// behaviour verbatim.
	class GroundUnitsAssaultFanoutStateCA : GroundStateBaseCA, IState
	{
		readonly Dictionary<uint, CPos> slots = new();
		CPos[] arc = [];
		AssaultFormationSettings settings;
		int deadlineTick;
		bool armed;

		// The consult shared by the transition sites in GroundStatesCA.cs: resolves
		// the armed provider for this squad+target (the provider's own cooldown may
		// decline a re-fan on the same ground). Cheap and side-effect free.
		internal static bool TryGetSettings(SquadCA owner, CPos targetCell, out AssaultFormationSettings settings)
		{
			settings = default;
			var provider = owner.Bot.Player.PlayerActor.TraitsImplementing<IBotAssaultFormation>()
				.FirstEnabledTraitOrDefault();
			return provider != null && provider.TryGetAssaultFormation(owner, targetCell, out settings);
		}

		public void Activate(SquadCA owner)
		{
			if (!owner.IsValid || !owner.IsTargetValid)
			{
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackMoveStateCA(), false);
				return;
			}

			var targetCell = owner.World.Map.CellContaining(owner.Target.CenterPosition);
			var provider = owner.Bot.Player.PlayerActor.TraitsImplementing<IBotAssaultFormation>()
				.FirstEnabledTraitOrDefault();
			if (provider == null || !provider.TryGetAssaultFormation(owner, targetCell, out settings)
				|| owner.Units.Count < settings.MinSquadSize)
			{
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackMoveStateCA(), false);
				return;
			}

			armed = true;
			deadlineTick = owner.World.WorldTick + settings.StageDeadlineTicks;
			provider.RecordFanout(owner, targetCell);

			// ActorID order is the planner's documented tiebreak — and the same
			// ordering on every peer.
			var ordered = owner.Units
				.Where(u => u.Actor != null && !owner.SquadManager.unitCannotBeOrdered(u.Actor))
				.OrderBy(u => u.Actor.ActorID)
				.ToList();
			var inputs = ordered.ConvertAll(u => (Cell: u.Actor.Location, ActorId: u.Actor.ActorID));
			var plan = AssaultFormationPlanner.PlanSlots(inputs, targetCell,
				settings.FanoutRadiusCells, settings.ArcDegrees,
				c => owner.World.Map.Contains(c), out arc);

			for (var i = 0; i < ordered.Count; i++)
				slots[ordered[i].Actor.ActorID] = plan[i];

			// The phase's primary orders go out once; Tick re-issues only to
			// members that are unslotted AND idle (a lost/cancelled order).
			foreach (var u in ordered)
				IssueSlotOrder(owner, u.Actor);
		}

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			if (!armed || !owner.IsTargetValid)
			{
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackMoveStateCA(), false);
				return;
			}

			// Contact during the fan commits the whole spread at once — that is
			// the point of the phase: nobody walks in alone. Same convergence as
			// the stage state.
			var enemyActor = owner.SquadManager.FindClosestEnemy(owner.Units[0].Actor,
				WDist.FromCells(owner.SquadManager.Info.AttackScanRadius), owner);
			if (enemyActor != null)
			{
				owner.TargetActor = enemyActor;
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackState(), false);
				return;
			}

			var reachSquared = (long)WDist.FromCells(settings.SlotReachCells).LengthSquared;
			var targetCenter = owner.Target.CenterPosition;
			var eligible = 0;
			var assembled = 0;
			foreach (var u in owner.Units)
			{
				var a = u.Actor;
				if (a == null || owner.SquadManager.unitCannotBeOrdered(a))
					continue;

				eligible++;

				if (!slots.TryGetValue(a.ActorID, out var cell))
				{
					// Late joiner: the nearest surviving point on the arc keeps
					// the spread honest; an empty arc folds it onto the target.
					var nearest = AssaultFormationPlanner.NearestSlotIndex(a.Location, arc);
					cell = nearest >= 0 ? arc[nearest]
						: owner.World.Map.CellContaining(targetCenter);
					slots[a.ActorID] = cell;
				}

				var slotCenter = owner.World.Map.CenterOfCell(cell);
				if ((a.CenterPosition - slotCenter).LengthSquared <= reachSquared
					|| (a.CenterPosition - targetCenter).LengthSquared <= reachSquared)
				{
					// At the slot — or already on the objective itself (a member
					// whose slot order was budget-denied kept its old attack-move
					// and arrived early; walking it back out would be a farce).
					assembled++;
				}
				else if (a.IsIdle)
				{
					IssueSlotOrder(owner, a);
				}
			}

			if (eligible == 0)
			{
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackMoveStateCA(), false);
				return;
			}

			// Commit together: engage the observed target directly; with nothing
			// live, the normal attack-move path carries the spread inward and
			// retargets itself — AttackState would only stall on an empty order.
			if (assembled * 100 >= eligible * settings.AssemblePercent ||
				owner.World.WorldTick >= deadlineTick)
			{
				if (owner.TargetActor != null)
					owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackState(), false);
				else
					owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackMoveStateCA(), false);
			}
		}

		// Per-member slot order, bounded by the micro-action budget (the
		// IssueFormationOrders precedent): a denied member keeps its previous
		// order and retries from Tick once it goes idle.
		void IssueSlotOrder(SquadCA owner, Actor unit)
		{
			if (!slots.TryGetValue(unit.ActorID, out var cell))
				return;

			if (!owner.SquadManager.TryConsumeMicroActions())
				return;

			owner.Bot.QueueOrder(new Order("AttackMove", unit, Target.FromCell(owner.World, cell), false));
		}

		public void Deactivate(SquadCA owner) { }
	}
}
