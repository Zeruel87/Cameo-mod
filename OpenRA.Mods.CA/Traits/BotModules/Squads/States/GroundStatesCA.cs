#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Traits;
using OpenRA.Mods.Common.Traits;

namespace OpenRA.Mods.CA.Traits.BotModules.Squads
{
	abstract class GroundStateBaseCA : StateBaseCA
	{
		protected virtual bool ShouldFlee(SquadCA owner)
		{
			// Never suicide (maintainer 2026-09-28): with CP, turn back once the visible fight is predicted lost.
			if (owner.SquadManager.Info.UseCombatPredictor)
				return ShouldFlee(owner, enemies => owner.SquadManager.PredictsLoss(owner, enemies));

			return ShouldFlee(owner, enemies => !AttackOrFleeFuzzyCA.Default.CanAttack(owner.Units.ConvertAll(u => u.Actor), enemies));
		}

		protected Actor FindClosestEnemy(SquadCA owner)
		{
			return owner.SquadManager.FindClosestEnemy(owner.Units.First().Actor, owner);
		}

		// 6c: pre-commit checks route through the risk-gated overloads — the squad's
		// unit value is compared to the remembered threat at each candidate's region.
		protected Actor FindClosestEnemy(SquadCA owner, bool riskCheck)
		{
			return riskCheck
				? owner.SquadManager.FindClosestEnemy(owner.Units.First().Actor, owner.SquadManager.SquadValueOf(owner), owner)
				: owner.SquadManager.FindClosestEnemy(owner.Units.First().Actor, owner);
		}

		protected Actor FindHighValueTarget(SquadCA owner)
		{
			return owner.SquadManager.FindHighValueTarget(owner.Units.First().Actor.CenterPosition);
		}

		protected Actor FindHighValueTarget(SquadCA owner, bool riskCheck)
		{
			return riskCheck
				? owner.SquadManager.FindHighValueTarget(owner.Units.First().Actor.CenterPosition, owner.SquadManager.SquadValueOf(owner))
				: owner.SquadManager.FindHighValueTarget(owner.Units.First().Actor.CenterPosition);
		}

		protected bool FindNewTarget(SquadCA owner, bool highValueCheck = false, bool riskCheck = false)
		{
			if (highValueCheck)
			{
				var highValueTargetRoll = owner.World.LocalRandom.Next(0, 100);

				if (owner.SquadManager.Info.HighValueTargetPriority > highValueTargetRoll)
				{
					var highValueTarget = FindHighValueTarget(owner, riskCheck);
					if (highValueTarget != null)
					{
						owner.TargetActor = highValueTarget;
						return true;
					}
				}
			}

			var closestEnemy = FindClosestEnemy(owner, riskCheck);
			if (closestEnemy != null)
			{
				owner.TargetActor = closestEnemy;
				return true;
			}

			// 6d fogged fallback: nothing visible — commit to an enemy building the
			// FrozenActorLayer remembers. The record self-invalidates when the
			// cell is re-observed empty, so a stale memory can't trap the squad.
			if (owner.SquadManager.FoggedScans)
			{
				var frozen = owner.SquadManager.FindFrozenEnemyTarget(
					owner.Units.First().Actor.CenterPosition,
					riskCheck ? owner.SquadManager.SquadValueOf(owner) : -1);

				if (frozen != null)
				{
					owner.Target = Target.FromFrozenActor(frozen);
					return true;
				}
			}

			return false;
		}
	}

	class GroundUnitsIdleStateCA : GroundStateBaseCA, IState
	{
		Actor leader;

		public void Activate(SquadCA owner) { }

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			// The idle squad is committing to a proactive attack — gate it on the
			// remembered threat at the target's region (6c). Mid-fight retargets in
			// GroundUnitsAttackState stay ungated.
			if (!owner.IsTargetValid && !FindNewTarget(owner, true, riskCheck: true))
				return;

			if (owner.SquadManager.unitCannotBeOrdered(leader))
				leader = GetPathfindLeader(owner, owner.SquadManager.Info.SuggestedGroundLeaderLocomotor).Actor;

			var enemyUnits = owner.World.FindActorsInCircle(owner.Target.CenterPosition, WDist.FromCells(owner.SquadManager.Info.IdleScanRadius))
				.Where(owner.SquadManager.IsPreferredObservedEnemyUnit).ToList();

			if (enemyUnits.Count == 0)
			{
				// A FrozenActor target is itself the point of the attack — nothing
				// visible nearby doesn't mean nothing is there.
				if (owner.Target.Type == TargetType.FrozenActor)
					owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackMoveStateCA(), false);
				else
					Retreat(owner, flee: false, rearm: true, repair: true);

				return;
			}

			var engage = owner.SquadManager.Info.UseCombatPredictor
				? owner.SquadManager.PredictsWin(owner, enemyUnits)
				: AttackOrFleeFuzzyCA.Default.CanAttack(owner.Units.ConvertAll(u => u.Actor), enemyUnits);
			if (engage)
			{
				// 6f: assault waves stage before committing so slow units catch
				// up and the attack arrives as one wave, not a trickle.
				if (owner.Type == SquadCAType.Rush && owner.SquadManager.Info.StageBeforeAssault)
					owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsStageStateCA(), false);
				else
					owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackMoveStateCA(), false);
			}
			else
				Retreat(owner, flee: true, rearm: true, repair: true);
		}

		public void Deactivate(SquadCA owner) { }
	}

	class GroundUnitsStageStateCA : GroundStateBaseCA, IState
	{
		CPos stagingCell;
		int stageDeadlineTick;
		bool staged;

		public void Activate(SquadCA owner)
		{
			// WorldTick deadline — squad Update() runs on AttackForceInterval,
			// not per tick, so a decrementing counter would wait 50-100x too long.
			stageDeadlineTick = owner.World.WorldTick + owner.SquadManager.Info.StageTimeoutTicks;

			// Rally at the own building nearest the target; without one there is
			// nowhere to stage, so commit directly. A building farther from the
			// target than the squad already is would stage it backwards — commit
			// immediately in that case too.
			var buildings = owner.World.ActorsHavingTrait<Building>()
				.Where(a => a.Owner == owner.Bot.Player).ToList();

			if (buildings.Count == 0 || !owner.IsTargetValid)
			{
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackMoveStateCA(), false);
				return;
			}

			var targetPos = owner.Target.CenterPosition;
			var targetCell = owner.World.Map.CellContaining(targetPos);
			var nearest = buildings.MinBy(b => (b.Location - targetCell).LengthSquared);

			var squadPos = owner.CenterPosition;
			var buildingDist = (nearest.CenterPosition - targetPos).LengthSquared;
			var squadDist = (squadPos - targetPos).LengthSquared;
			if (buildingDist >= squadDist)
			{
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackMoveStateCA(), false);
				return;
			}

			stagingCell = nearest.Location;
			staged = true;

			foreach (var u in owner.Units)
				owner.Bot.QueueOrder(new Order("Move", u.Actor, Target.FromCell(owner.World, stagingCell), false));
		}

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			if (!staged || !owner.IsTargetValid)
			{
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsIdleStateCA(), true);
				return;
			}

			// Contact during staging: commit to the fight at the rally point.
			var enemyActor = owner.SquadManager.FindClosestEnemy(owner.Units[0].Actor,
				WDist.FromCells(owner.SquadManager.Info.AttackScanRadius), owner);
			if (enemyActor != null)
			{
				owner.TargetActor = enemyActor;
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackState(), false);
				return;
			}

			var radiusSquared = (long)WDist.FromCells(owner.SquadManager.Info.StageRadiusCells).LengthSquared;
			var rally = owner.World.Map.CenterOfCell(stagingCell);
			var assembled = owner.Units.Count(u =>
				(u.Actor.CenterPosition - rally).LengthSquared <= radiusSquared);

			// AF-1: a staged Rush squad commits through the fan-out — the state
			// falls back to the plain attack-move itself when no
			// IBotAssaultFormation provider is armed.
			if (assembled * 100 >= owner.Units.Count * owner.SquadManager.Info.StageAssemblePercent ||
				owner.World.WorldTick >= stageDeadlineTick)
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAssaultFanoutStateCA(), false);
		}

		public void Deactivate(SquadCA owner) { }
	}

	class SupportUnitsIdleStateCA : GroundStateBaseCA, IState
	{
		const int HoldTicks = 250;
		int holdTicks;

		public void Activate(SquadCA owner) { }

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			var parent = owner.Parent;
			if (parent == null || !parent.IsValid)
			{
				parent = owner.SquadManager.FindAttachableAssault(owner);
				owner.Parent = parent;
			}

			if (parent == null)
			{
				// No assault to support: hold near home so medics stop charging
				// into the attack force like they did as generic ground units.
				if (--holdTicks <= 0)
				{
					GoToRandomOwnBuilding(owner);
					holdTicks = HoldTicks;
				}

				return;
			}

			// Trail the assault: units beyond SupportFollowRangeCells get a move
			// order toward it. Their own AutoTarget heals/repairs in reach.
			var followRangeSquared = (long)WDist.FromCells(owner.SquadManager.Info.SupportFollowRangeCells).LengthSquared;
			var parentPos = parent.CenterPosition;
			foreach (var u in owner.Units)
			{
				if ((u.Actor.CenterPosition - parentPos).LengthSquared <= followRangeSquared)
					continue;

				owner.Bot.QueueOrder(new Order("Move", u.Actor, Target.FromPos(parentPos), false));
			}
		}

		public void Deactivate(SquadCA owner) { }
	}

	class GroundUnitsAttackMoveStateCA : GroundStateBaseCA, IState
	{
		const int MaxMakeWayPossibility = 4;
		const int MaxSquadStuckPossibility = 6;
		const int MakeWayTicks = 3;
		const int KickStuckTicks = 4;

		// Give tolerance for AI grouping team at start
		int shouldMakeWayPossibility = -(MaxMakeWayPossibility * 6);
		int shouldKickStuckPossibility = -(MaxSquadStuckPossibility * 6);
		int makeWay = 0;
		int kickStuck = 0;

		UnitWposWrapper leader = new(null);

		// 12.7 formation: rear-frontline stall tracking (fransbot chokepoint rule)
		WPos formationRearPos;
		int formationRearStallTicks;
		int formationRearHp = -1;

		// Indirect/harass routing state
		List<CPos> currentRoute;
		int currentWaypointIndex;
		int lastWaypointUpdateTick;
		Target lastRoutingTarget;

		public void Activate(SquadCA owner) { }

		public void Tick(SquadCA owner)
		{
			// Basic check
			if (!owner.IsValid)
				return;

			// Initialize leader. Optimize pathfinding by using a leader with specific locomotor.
			if (owner.SquadManager.unitCannotBeOrdered(leader.Actor))
				leader = GetPathfindLeader(owner, owner.SquadManager.Info.SuggestedGroundLeaderLocomotor);

			if (!owner.IsTargetValid || !CheckReachability(leader.Actor, owner.World.Map.CellContaining(owner.Target.CenterPosition)))
			{
				// Harassers retarget high-value first when the target is gone (HV
				// roll + risk gate + frozen fallback live inside FindNewTarget); a
				// valid-but-unreachable target keeps the plain closest-enemy pick
				// so the squad cannot HV-reroll itself into a thrash loop.
				if (owner.Type == SquadCAType.Harass && !owner.IsTargetValid && !FindNewTarget(owner, highValueCheck: true, riskCheck: true))
				{
					owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsFleeStateCA(), false);
					return;
				}
				else if (owner.Type != SquadCAType.Harass || owner.IsTargetValid)
				{
					var targetActor = owner.SquadManager.FindClosestEnemy(leader.Actor, owner);
					if (targetActor != null)
						owner.TargetActor = targetActor;
					else
					{
						owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsFleeStateCA(), false);
						return;
					}
				}
			}

			// Switch to "GroundUnitsAttackState" if we encounter enemy units.
			var attackScanRadius = WDist.FromCells(owner.SquadManager.Info.AttackScanRadius);

			var enemyActor = owner.SquadManager.FindClosestEnemy(leader.Actor, attackScanRadius, owner);
			if (enemyActor != null)
			{
				owner.TargetActor = enemyActor;
				if (owner.Type == SquadCAType.Guerrilla)
					owner.FuzzyStateMachine.ChangeState(owner, new GuerrillaUnitsHitState(), false);
				else
					owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackState(), false);
				return;
			}

			// CA-2 siege consult (§12.6): with no live enemy in reach, an advisor
			// may hold the squad at the remembered-defence stand-off line or pull
			// it out before a losing trade. Advance (or no advisor) changes nothing.
			if (owner.Type == SquadCAType.Rush || owner.Type == SquadCAType.Guerrilla || owner.Type == SquadCAType.Harass)
			{
				var siegeVerdict = owner.SquadManager.EvaluateSiege(owner, out var standOffCell);
				if (siegeVerdict == SiegeVerdict.Retreat)
				{
					owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsFleeStateCA(), false);
					return;
				}

				if (siegeVerdict == SiegeVerdict.StandOff && leader.Actor != null && owner.World.Map.Contains(standOffCell))
				{
					// Re-order only when the leader drifts off the hold line.
					if ((owner.World.Map.CellContaining(leader.Actor.CenterPosition) - standOffCell).LengthSquared > 4)
						foreach (var u in owner.Units)
							owner.Bot.QueueOrder(new Order("Move", u.Actor, Target.FromCell(owner.World, standOffCell), false));
					return;
				}
			}

			// AF-1 (line-of-death fix): a Rush squad whose leader has entered the
			// fan-out band — inside the trigger radius but still outside the arc —
			// spreads onto the assault ring before the commit. Runs only when the
			// enemy scan above found nothing (the fan must form pre-contact) and
			// after the siege consult so a stand-off hold still wins. The band's
			// inner edge plus the provider's same-target cooldown keep a squad
			// already on the ring from re-fanning forever.
			if (owner.Type == SquadCAType.Rush && owner.IsTargetValid && leader.Actor != null
				&& GroundUnitsAssaultFanoutStateCA.TryGetSettings(owner,
					owner.World.Map.CellContaining(owner.Target.CenterPosition), out var fanout)
				&& owner.Units.Count >= fanout.MinSquadSize)
			{
				var leaderDistSquared = (leader.Actor.CenterPosition - owner.Target.CenterPosition).HorizontalLengthSquared;
				var triggerSquared = (long)WDist.FromCells(fanout.FanoutTriggerCells).LengthSquared;
				var ringSquared = (long)WDist.FromCells(fanout.FanoutRadiusCells).LengthSquared;
				if (leaderDistSquared <= triggerSquared && leaderDistSquared > ringSquared)
				{
					owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAssaultFanoutStateCA(), false);
					return;
				}
			}

			// Since units have different movement speeds, they get separated while approaching the target.
			// Let them regroup into tighter formation towards "leader".
			//
			// "occupiedArea" means the space the squad units will occupy (if 1 per Cell).
			// leader only stop when scope of "lookAround" is not covered all units;
			// units in "unitsHurryUp"  will catch up, which keep the team tight while not stuck.
			//
			// Imagining "occupiedArea" takes up a a place shape like square,
			// we need to draw a circle to cover the the enitire circle.
			var occupiedArea = (long)WDist.FromCells(owner.Units.Count).Length * 1024;

			// Kick stuck units: Kick stuck units that is blocked
			if (kickStuck > 0)
			{
				var stopUnits = new List<Actor>();
				var otherUnits = new List<Actor>();

				// Check if it is the leader stuck
				if (leader.Actor.CenterPosition == leader.WPos && !IsAttackingAndTryAttack(leader.Actor).IsFiring)
				{
					stopUnits.Add(leader.Actor);

					// GetPathfindLeader may return a fresh wrapper rather than the
					// instance stored in Units — remove by actor identity.
					owner.Units.RemoveAll(u => u.Actor == leader.Actor);
					owner.SquadManager.ReturnToIdlePool(leader.Actor);
					AIUtils.BotDebug("AI ({0}): Kick leader from squad.", owner.Bot.Player.ClientIndex);
				}

				// Check if it is the units stuck
				else
				{
					for (var i = 0; i < owner.Units.Count; i++)
					{
						var u = owner.Units[i];

						if (u.Actor == leader.Actor)
							continue;

						// If unit that is not in valid distance from leader nor firing at enemy,
						// we will check if it can reach the leader, or stuck due to unknow reason
						if ((u.Actor.CenterPosition - leader.Actor.CenterPosition).HorizontalLengthSquared >= 5 * occupiedArea
							&& (u.Actor.CenterPosition == u.WPos
							|| !AIUtils.PathExist(u.Actor, leader.Actor.Location, leader.Actor)))
						{
							stopUnits.Add(u.Actor);
							owner.Units.RemoveAt(i);
							owner.SquadManager.ReturnToIdlePool(u.Actor);
							i--;
						}
						else
						{
							u.WPos = u.Actor.CenterPosition;
							otherUnits.Add(u.Actor);
						}
					}

					if (stopUnits.Count > 0)
						AIUtils.BotDebug("AI ({0}): Kick ({1}) from squad.", owner.Bot.Player.ClientIndex, stopUnits.Count);
				}

				if (owner.Units.Count == 0)
					return;

				if (kickStuck > 1)
				{
					leader = GetPathfindLeader(owner, owner.SquadManager.Info.SuggestedGroundLeaderLocomotor);
					leader.WPos = leader.Actor.CenterPosition;
					owner.Bot.QueueOrder(new Order("AttackMove", leader.Actor, Target.FromPos(owner.Target.CenterPosition), false));
					owner.Bot.QueueOrder(new Order("Stop", null, false, groupedActors: stopUnits.ToArray()));
					owner.Bot.QueueOrder(new Order("AttackMove", null, Target.FromCell(owner.World, leader.Actor.Location), false, groupedActors: otherUnits.ToArray()));
					kickStuck--;
				}
				else if (kickStuck == 1)
				{
					shouldMakeWayPossibility = 0;
					shouldKickStuckPossibility = 0;
					leader = GetPathfindLeader(owner, owner.SquadManager.Info.SuggestedGroundLeaderLocomotor);

					// The end of "kickStuck": stop the leader for position record next tick
					owner.Bot.QueueOrder(new Order("Stop", leader.Actor, false));
					kickStuck = 0;
				}

				return;
			}

			// Make way for leader: Make sure the guide unit has not been blocked by the rest of the squad.
			if (makeWay > 0)
			{
				if (makeWay > 1)
				{
					var others = owner.Units.Where(u => u.Actor != leader.Actor).Select(u => u.Actor);
					owner.Bot.QueueOrder(new Order("Scatter", null, false, groupedActors: others.ToArray()));
					owner.Bot.QueueOrder(new Order("AttackMove", leader.Actor, Target.FromPos(owner.Target.CenterPosition), false));
					makeWay--;
				}
				else if (makeWay == 1)
				{
					shouldMakeWayPossibility = 0;
					shouldKickStuckPossibility = MaxSquadStuckPossibility / 2;

					// The end of "makeWay": stop the leader for position record next tick
					// set "makeWay" to -1 to inform that squad just make way for leader
					owner.Bot.QueueOrder(new Order("Stop", leader.Actor, false));
					makeWay = -1;
				}

				return;
			}

			// "leaderStopCheck" to see if leader move.
			// "leaderWaitCheck" to see if leader should wait squad members that left behind.
			var leaderStopCheck = leader.Actor.CenterPosition == leader.WPos;
			var leaderWaitCheck = owner.Units.Any(u => (u.Actor.CenterPosition - leader.Actor.CenterPosition).HorizontalLengthSquared > occupiedArea * 5);

			// To find out the stuck problem of the squad and deal with it.
			// 1. If leader cannot move and leader should wait, there may be squad members stuck.
			// 2. If leader cannot move but leader should go, leader is stuck.
			// -- Try make way for leader
			// -- If make way cannot solve this problem, we kick stuck unit
			// 3. If leader can move and leader should go, we consider this squad has no problem on stuck.
			if (leaderStopCheck && leaderWaitCheck)
				shouldKickStuckPossibility++;
			else if (leaderStopCheck && !leaderWaitCheck)
			{
				if (makeWay != -1)
					shouldMakeWayPossibility++;
				else
					shouldKickStuckPossibility++;
			}
			else if (!leaderStopCheck && !leaderWaitCheck)
			{
				shouldMakeWayPossibility = 0;
				shouldKickStuckPossibility = 0;
			}

			// Check if we need to make way for leader or kick stuck units
			if (shouldMakeWayPossibility >= MaxMakeWayPossibility)
			{
				AIUtils.BotDebug("AI ({0}): Make way for squad leader.", owner.Bot.Player.ClientIndex);
				makeWay = MakeWayTicks;
			}
			else if (shouldKickStuckPossibility >= MaxSquadStuckPossibility)
			{
				AIUtils.BotDebug("AI ({0}): Kick stuck units from squad.", owner.Bot.Player.ClientIndex);
				kickStuck = KickStuckTicks;
			}

			// Compute indirect/harass route when target changes
			if (!owner.Target.Equals(lastRoutingTarget))
			{
				lastRoutingTarget = owner.Target;
				currentRoute = null;
				currentWaypointIndex = 0;
				lastWaypointUpdateTick = owner.World.WorldTick;

				var targetCell = owner.World.Map.CellContaining(owner.Target.CenterPosition);

				// 6e risk routing: coarse waypoints that skirt remembered threat,
				// when a router answers. Guerrillas and harassers keep their harass
				// routes — unpredictability is the point there.
				if (owner.Type != SquadCAType.Guerrilla && owner.Type != SquadCAType.Harass)
					currentRoute = owner.SquadManager.RouteAroundThreat(leader.Actor, targetCell);

				var locomotor = leader.Actor.TraitOrDefault<Mobile>()?.Locomotor;
				if (currentRoute == null && locomotor != null)
				{
					var maxRoutes = 2;
					var useIndirectRoutes = false;

					if (owner.Type == SquadCAType.Harass)
						maxRoutes = owner.SquadManager.Info.HarassRouteCount;
					else if (owner.Type == SquadCAType.Guerrilla)
						maxRoutes = 3;
					else if (owner.SquadManager.Info.IndirectRouteChance > 0 && owner.World.LocalRandom.Next(100) < owner.SquadManager.Info.IndirectRouteChance)
					{
						useIndirectRoutes = true;
						maxRoutes = 7;
					}

					if (maxRoutes > 2 || useIndirectRoutes)
					{
						var routes = AIUtils.FindDistinctRoutes(owner.World, locomotor, leader.Actor.Location, owner.World.Map.CellContaining(owner.Target.CenterPosition), maxRoutes);

						if (owner.Type == SquadCAType.Guerrilla || owner.Type == SquadCAType.Harass)
							routes = routes.Skip(Math.Max(0, routes.Count - 2)).Take(2).ToList();
						else if (useIndirectRoutes)
							routes = routes.Skip(1).ToList();

						if (routes.Count > 0)
						{
							var chosen = routes.Random(owner.World.LocalRandom);
							currentRoute = chosen.Skip(1).ToList();
							currentWaypointIndex = 0;
							lastWaypointUpdateTick = owner.World.WorldTick;
						}
					}
				}
			}

			// Advance through route waypoints
			if (currentRoute != null && currentWaypointIndex < currentRoute.Count - 1)
			{
				if ((leader.Actor.Location - currentRoute[currentWaypointIndex]).LengthSquared < 16
					|| owner.World.WorldTick > lastWaypointUpdateTick + 625)
				{
					currentWaypointIndex++;
					lastWaypointUpdateTick = owner.World.WorldTick;
				}
			}

			// Determine move target (waypoint or direct)
			var routeTarget = currentRoute != null && currentRoute.Count > 1 && currentWaypointIndex < currentRoute.Count
				? Target.FromCell(owner.World, currentRoute[currentWaypointIndex])
				: Target.FromPos(owner.Target.CenterPosition);

			// Record current position of the squad leader
			leader.WPos = leader.Actor.CenterPosition;

			// Leader will wait squad members that left behind, unless
			// next tick is kick stuck unit (we need leader move in advance).
			if (leaderWaitCheck && kickStuck <= 0)
				owner.Bot.QueueOrder(new Order("Stop", leader.Actor, false));
			else
				owner.Bot.QueueOrder(new Order("AttackMove", leader.Actor, routeTarget, false));

			// 12.7: assault squads keep formation steps - frontline leads, anti-air
			// inside, the rest trails the frontline centroid. Other squad types keep
			// the plain straggler catch-up (guerrilla/harass mobility is doctrinal).
			if (owner.SquadManager.Info.FormationMovement && owner.Type == SquadCAType.Rush
				&& IssueFormationOrders(owner, leader, routeTarget))
				return;

			var unitsHurryUp = owner.Units.Where(u => (u.Actor.CenterPosition - leader.Actor.CenterPosition).HorizontalLengthSquared >= occupiedArea * 2).Select(u => u.Actor).ToArray();
			owner.Bot.QueueOrder(new Order("AttackMove", null, Target.FromCell(owner.World, leader.Actor.Location), false, groupedActors: unitsHurryUp));
		}

		// 12.7 formation step, once per squad tick (orders only, no activities):
		// frontline leads toward the route target at the pace of its slowest
		// member - anyone FormationMaxLeadCells ahead of the rear frontline
		// projection holds; anti-air sits on the frontline centroid; every other
		// ground unit aims FormationTrailCells behind the centroid. Scouts are
		// never constrained - they run ahead on their own. Returns false when no
		// usable role/frontline data exists so the caller keeps the old path.
		bool IssueFormationOrders(SquadCA owner, UnitWposWrapper leader, Target routeTarget)
		{
			var roleMap = owner.SquadManager.ActorRoles;
			if (roleMap == null || roleMap.Count == 0)
				return false;

			var frontline = new List<UnitWposWrapper>();
			var antiAir = new List<UnitWposWrapper>();
			var scouts = new List<UnitWposWrapper>();
			var trailing = new List<UnitWposWrapper>();

			foreach (var u in owner.Units)
			{
				if (u.Actor == leader.Actor)
					continue;

				if (!roleMap.TryGetValue(u.Actor.Info.Name, out var roles))
				{
					trailing.Add(u);
					continue;
				}

				if (roles.Contains(BotUnitRole.Frontline))
					frontline.Add(u);
				else if (roles.Contains(BotUnitRole.Scout))
					scouts.Add(u);
				else if (roles.Contains(BotUnitRole.AntiAir))
					antiAir.Add(u);
				else
					trailing.Add(u);
			}

			if (frontline.Count == 0)
				return false;

			// Axis of advance: frontline centroid -> route target.
			var routePos = routeTarget.CenterPosition;
			long cx = leader.Actor.CenterPosition.X, cy = leader.Actor.CenterPosition.Y;
			foreach (var u in frontline)
			{
				cx += u.Actor.CenterPosition.X;
				cy += u.Actor.CenterPosition.Y;
			}

			var centroid = new WPos((int)(cx / (frontline.Count + 1)), (int)(cy / (frontline.Count + 1)), 0);
			var axis = routePos - centroid;
			if (axis.HorizontalLengthSquared < (long)WDist.FromCells(2).Length * WDist.FromCells(2).Length)
				return false;

			var axisLen = axis.HorizontalLength;
			var maxLead = (long)WDist.FromCells(owner.SquadManager.Info.FormationMaxLeadCells).Length;

			// Distance-to-go along the axis for every frontline member; the slowest
			// (largest remaining) gates how far ahead the others may run. The
			// projection is computed in long: WVec.Dot returns int and overflows
			// beyond ~45 cells of span, which is most real routes.
			var slowestRemaining = long.MinValue;
			UnitWposWrapper rear = null;
			foreach (var u in frontline)
			{
				var delta = routePos - u.Actor.CenterPosition;
				var rem = ((long)delta.X * axis.X + (long)delta.Y * axis.Y + (long)delta.Z * axis.Z) / axisLen;
				if (rem > slowestRemaining)
				{
					slowestRemaining = rem;
					rear = u;
				}
			}

			// Fransbot donor rule: a rear member stalled in a chokepoint grants the
			// leaders the wider FormationMaxStalledLeadCells allowance; the normal
			// lead resumes the tick it moves again. MI watches the stall's HP:
			// a stalled rear that is losing HP is under fire and becomes the
			// pull-back trigger below.
			var lead = maxLead;
			var stalledRearUnderFire = false;
			if (rear != null)
			{
				if (rear.Actor.CenterPosition == formationRearPos)
				{
					formationRearStallTicks++;
					var rearHealth = rear.Actor.TraitOrDefault<IHealth>();
					if (rearHealth != null)
					{
						if (formationRearHp >= 0 && rearHealth.HP < formationRearHp)
							stalledRearUnderFire = true;

						formationRearHp = rearHealth.HP;
					}
				}
				else
				{
					formationRearStallTicks = 0;
					formationRearPos = rear.Actor.CenterPosition;
					formationRearHp = -1;
				}

				if (formationRearStallTicks >= 25)
					lead = WDist.FromCells(owner.SquadManager.Info.FormationMaxStalledLeadCells).Length;
			}

			var holdFront = new List<Actor>();
			var pushFront = new List<Actor>();
			foreach (var u in frontline)
			{
				var delta = routePos - u.Actor.CenterPosition;
				var rem = ((long)delta.X * axis.X + (long)delta.Y * axis.Y + (long)delta.Z * axis.Z) / axisLen;
				if (slowestRemaining - rem > lead)
					holdFront.Add(u.Actor);
				else
					pushFront.Add(u.Actor);
			}

			// The trail line doubles as the pull-back rally behind the
			// formation anchor for MI below.
			var trailPos = SquadMicroEvalCA.PullBackPoint(centroid, routePos,
				WDist.FromCells(owner.SquadManager.Info.FormationTrailCells));

			if (pushFront.Count > 0)
				owner.Bot.QueueOrder(new Order("AttackMove", null, routeTarget, false, groupedActors: pushFront.ToArray()));
			if (holdFront.Count > 0)
				owner.Bot.QueueOrder(new Order("Stop", null, false, groupedActors: holdFront.ToArray()));

			var centroidCell = owner.World.Map.CellContaining(centroid);
			if (antiAir.Count > 0)
				owner.Bot.QueueOrder(new Order("AttackMove", null, Target.FromCell(owner.World, centroidCell), false, groupedActors: antiAir.Select(u => u.Actor).ToArray()));

			if (scouts.Count > 0)
				owner.Bot.QueueOrder(new Order("AttackMove", null, routeTarget, false, groupedActors: scouts.Select(u => u.Actor).ToArray()));

			if (trailing.Count > 0)
				owner.Bot.QueueOrder(new Order("AttackMove", null, Target.FromPos(trailPos), false, groupedActors: trailing.Select(u => u.Actor).ToArray()));

			// MI pull-back (budgeted per order): members at/below
			// SquadMicroRetreatPct fall back to the trail line — behind the
			// formation anchor, still with the squad. A stalled rear that is
			// taking fire pulls back past itself to break contact in the
			// chokepoint. Queued after the formation orders so the micro order
			// wins for that member this tick; a denied member keeps its
			// formation order.
			if (owner.SquadManager.Info.SquadMicroEnabled)
			{
				var retreatPct = owner.SquadManager.Info.SquadMicroRetreatPct;
				foreach (var u in frontline)
				{
					var hp = u.Actor.TraitOrDefault<IHealth>();
					if (hp == null || !SquadMicroEvalCA.ShouldPullBack(hp.HP, hp.MaxHP, retreatPct))
						continue;

					if (!owner.SquadManager.TryConsumeMicroActions())
						break;

					owner.Bot.QueueOrder(new Order("Move", u.Actor, Target.FromPos(trailPos), false));
				}

				foreach (var u in trailing)
				{
					var hp = u.Actor.TraitOrDefault<IHealth>();
					if (hp == null || !SquadMicroEvalCA.ShouldPullBack(hp.HP, hp.MaxHP, retreatPct))
						continue;

					if (!owner.SquadManager.TryConsumeMicroActions())
						break;

					owner.Bot.QueueOrder(new Order("Move", u.Actor, Target.FromPos(trailPos), false));
				}

				if (stalledRearUnderFire && rear != null && owner.SquadManager.TryConsumeMicroActions())
					owner.Bot.QueueOrder(new Order("Move", rear.Actor,
						Target.FromPos(SquadMicroEvalCA.PullBackPoint(rear.Actor.CenterPosition, routePos,
							WDist.FromCells(owner.SquadManager.Info.FormationTrailCells))), false));
			}

			return true;
		}

		public void Deactivate(SquadCA owner) { }
	}

	class GroundUnitsAttackState : GroundStateBaseCA, IState
	{
		int lastUpdatedTick;
		CPos? lastLeaderLocation;
		Actor lastTarget;

		public void Activate(SquadCA owner) { }

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			if (!owner.IsTargetValid && !FindNewTarget(owner))
			{
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsFleeStateCA(), true);
				return;
			}

			var leader = owner.Units[0].Actor;
			if (leader.Location != lastLeaderLocation)
			{
				lastLeaderLocation = leader.Location;
				lastUpdatedTick = owner.World.WorldTick;
			}

			if (owner.TargetActor != lastTarget)
			{
				lastTarget = owner.TargetActor;
				lastUpdatedTick = owner.World.WorldTick;
			}

			// HACK: Drop back to the idle state if we haven't moved in 2.5 seconds
			// This works around the squad being stuck trying to attack-move to a location
			// that they cannot path to, generating expensive pathfinding calls each tick.
			if (owner.World.WorldTick > lastUpdatedTick + 63)
			{
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsIdleStateCA(), true);
				return;
			}

			// MI order half (SquadMicroEnabled, Rush only — its own A/B cell):
			// one focus target per squad tick, members that can reach it
			// concentrate fire, damaged members pull back behind the squad,
			// outranging members kite. Candidates come through
			// IsPreferredObservedEnemyUnit — only what the bot can currently see
			// or legitimately remember. Budget denial or no pick degrades to the
			// plain AttackMove below.
			var micro = owner.SquadManager.Info.SquadMicroEnabled && owner.Type == SquadCAType.Rush
				&& owner.TargetActor != null;
			Actor focus = null;
			BotUnitProfile focusProfile = null;
			if (micro)
			{
				var targets = owner.World.FindActorsInCircle(owner.TargetActor.CenterPosition,
						WDist.FromCells(owner.SquadManager.Info.AttackScanRadius))
					.Where(owner.SquadManager.IsPreferredObservedEnemyUnit).ToList();

				if (targets.Count > 0)
				{
					var squadProfiles = owner.Units.ConvertAll(u => BotUnitProfiles.Get(owner.World.Map.Rules, u.Actor.Info));
					var pick = SquadMicroEvalCA.PickFocusTarget(squadProfiles,
						targets.ConvertAll(t => LiveHpProfile(owner.World, t)));

					if (pick >= 0)
					{
						focus = targets[pick];
						focusProfile = LiveHpProfile(owner.World, focus);
					}
				}
			}

			foreach (var a in owner.Units)
			{
				if (BusyAttack(a.Actor))
					continue;

				if (micro && TryIssueMicroOrder(owner, a.Actor, focus, focusProfile))
					continue;

				owner.Bot.QueueOrder(new Order("AttackMove", a.Actor, Target.FromActor(owner.TargetActor), false));
			}

			if (ShouldFlee(owner))
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsFleeStateCA(), true);
		}

		// One member's micro order (the order half of SquadMicroEvalCA),
		// priority pull-back > kite standoff > focus-fire. Spends one
		// IBotActionBudget action per issued order; false means the member
		// keeps the default AttackMove.
		static bool TryIssueMicroOrder(SquadCA owner, Actor unit, Actor focus, BotUnitProfile focusProfile)
		{
			var assignedTarget = focus ?? owner.TargetActor;

			var health = unit.TraitOrDefault<IHealth>();
			if (health != null && SquadMicroEvalCA.ShouldPullBack(health.HP, health.MaxHP, owner.SquadManager.Info.SquadMicroRetreatPct))
			{
				if (!owner.SquadManager.TryConsumeMicroActions())
					return false;

				// Retreat behind the squad centre — regroup with the squad, not a rout home.
				var waypoint = SquadMicroEvalCA.PullBackPoint(owner.CenterPosition, assignedTarget.CenterPosition,
					WDist.FromCells(owner.SquadManager.Info.FormationTrailCells));
				owner.Bot.QueueOrder(new Order("Move", unit, Target.FromPos(waypoint), false));
				return true;
			}

			var ownProfile = BotUnitProfiles.Get(owner.World.Map.Rules, unit.Info);
			var targetProfile = BotUnitProfiles.Get(owner.World.Map.Rules, assignedTarget.Info);
			var standoff = SquadMicroEvalCA.KiteStandoff(ownProfile, targetProfile,
				WDist.FromCells(owner.SquadManager.Info.SquadMicroKiteMarginCells));
			if (standoff is WDist standoffDist)
			{
				// Kite only when inside the target's reply range — beyond it
				// AttackMove already holds the unit at its own weapon range.
				var dist = (unit.CenterPosition - assignedTarget.CenterPosition).HorizontalLength;
				if (dist < targetProfile.MaxRange.Length)
				{
					if (!owner.SquadManager.TryConsumeMicroActions())
						return false;

					var waypoint = SquadMicroEvalCA.PullBackPoint(unit.CenterPosition, assignedTarget.CenterPosition,
						new WDist((int)Math.Max(0, standoffDist.Length - dist)));
					owner.Bot.QueueOrder(new Order("Move", unit, Target.FromPos(waypoint), false));
					return true;
				}
			}

			if (focus != null && focusProfile != null
				&& ownProfile.DamagePerTickAgainst(focusProfile) > 0
				&& (focus.CenterPosition - unit.CenterPosition).HorizontalLengthSquared
					<= (long)ownProfile.MaxRange.Length * ownProfile.MaxRange.Length)
			{
				if (!owner.SquadManager.TryConsumeMicroActions())
					return false;

				owner.Bot.QueueOrder(new Order("Attack", unit, Target.FromActor(focus), false));
				return true;
			}

			return false;
		}

		// A rules profile with the actor's CURRENT hit points — PickFocusTarget's
		// time-to-kill must see a near-dead target as near-dead, not at the
		// pristine MaxHP the cache stores.
		static BotUnitProfile LiveHpProfile(World world, Actor actor)
		{
			var profile = BotUnitProfiles.Get(world.Map.Rules, actor.Info);
			var health = actor.TraitOrDefault<IHealth>();
			if (health == null || health.HP == profile.Hp)
				return profile;

			return new BotUnitProfile(profile.Name, profile.Cost, health.HP, profile.Armor, profile.Speed,
				profile.IsAircraft, profile.IsBuilding, profile.TargetTypes, profile.Weapons);
		}

		public void Deactivate(SquadCA owner) { }
	}

	class GroundUnitsFleeStateCA : GroundStateBaseCA, IState
	{
		public void Activate(SquadCA owner) { }

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			GoToRandomOwnBuilding(owner);
			owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsIdleStateCA(), true);
		}

		public void Deactivate(SquadCA owner) { owner.SquadManager.DismissSquad(owner); }
	}

	class HarasserUnitsIdleStateCA : GroundStateBaseCA, IState
	{
		public void Activate(SquadCA owner) { }

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			// The harasser launch quorum (upstream CA): a trickle of one or two
			// raiders is a waste — wait for a squad that can hurt a harvester line.
			if (!ShouldHarass(owner.Units.Count, owner.SquadManager.Info.HarassMinLaunchSize, owner.World.LocalRandom.Next(100)))
				return;

			// High-value targets first (harvester lines, expansions), through the
			// 6c risk gate — a harasser raid still should not suicide.
			if (!owner.IsTargetValid && !FindNewTarget(owner, highValueCheck: true, riskCheck: true))
				return;

			owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackMoveStateCA(), true);
		}

		internal static bool ShouldHarass(int count, int minSize, int roll)
		{
			if (count < minSize)
				return false;

			// Just past the quorum the launch is a roll; a full wing always goes.
			if (count == minSize)
				return roll < 5;

			if (count == minSize + 1)
				return roll < 10;

			return true;
		}

		public void Deactivate(SquadCA owner) { }
	}

	class GuerrillaUnitsHitState : GroundStateBaseCA, IState
	{
		// Use it to find if entire squad cannot reach the attack position
		int tryAttackTick;

		Actor leader;
		int tryAttack = 0;
		bool isFirstTick = true; // Only record HP and do not retreat at first tick
		int squadsize = 0;

		public void Activate(SquadCA owner)
		{
			tryAttackTick = owner.SquadManager.Info.AttackScanRadius;
		}

		public void Tick(SquadCA owner)
		{
			// Basic check
			if (!owner.IsValid)
				return;

			if (owner.SquadManager.unitCannotBeOrdered(leader))
				leader = owner.Units[0].Actor;

			owner.SquadManager.SetAirStrikeTarget(owner.TargetActor);
			var isDefaultLeader = true;

			// Rescan target to prevent being ambushed and die without fight
			// If there is no threat around, return to AttackMove state for formation
			var attackScanRadius = WDist.FromCells(owner.SquadManager.Info.AttackScanRadius);
			var closestEnemy = owner.SquadManager.FindClosestEnemy(leader, attackScanRadius, owner);

			var healthChange = false;
			var cannotRetaliate = true;
			var followingUnits = new List<Actor>();
			var attackingUnits = new List<Actor>();

			if (closestEnemy == null)
			{
				owner.TargetActor = owner.SquadManager.FindClosestEnemy(leader, owner);
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackMoveStateCA(), false);
				return;
			}
			else
			{
				if (owner.TargetActor != closestEnemy)
				{
					// Refresh tryAttack when target switched
					tryAttack = 0;
					owner.TargetActor = closestEnemy;
				}

				for (var i = 0; i < owner.Units.Count; i++)
				{
					var u = owner.Units[i];
					var (isFiring, tryAttacking) = IsAttackingAndTryAttack(u.Actor);

					var health = u.Actor.TraitOrDefault<IHealth>();

					if (health != null)
					{
						var healthWPos = new WPos(0, 0, (int)health.DamageState); // HACK: use WPos.Z storage HP
						if (u.WPos.Z != healthWPos.Z)
						{
							if (u.WPos.Z < healthWPos.Z)
								healthChange = true;
							u.WPos = healthWPos;
						}
					}

					if (owner.TargetActor != null && (tryAttacking || isFiring) &&
						(u.Actor.CenterPosition - owner.TargetActor.CenterPosition).HorizontalLengthSquared <
						(leader.CenterPosition - owner.TargetActor.CenterPosition).HorizontalLengthSquared)
					{
						isDefaultLeader = false;
						leader = u.Actor;
					}

					if (isFiring && tryAttack != 0)
					{
						// Make there is at least one follow and attack target, AFTER first trying on attack
						if (isDefaultLeader)
						{
							leader = u.Actor;
							isDefaultLeader = false;
						}

						cannotRetaliate = false;
					}
					else if (CanAttackTarget(u.Actor, owner.TargetActor))
					{
						if (tryAttack > tryAttackTick && tryAttacking)
						{
							// Make there is at least one follow and attack target even when approach max tryAttackTick
							if (isDefaultLeader)
							{
								leader = u.Actor;
								isDefaultLeader = false;
								attackingUnits.Add(u.Actor);
								continue;
							}

							followingUnits.Add(u.Actor);
							continue;
						}

						attackingUnits.Add(u.Actor);
						cannotRetaliate = false;
					}
					else
						followingUnits.Add(u.Actor);
				}
			}

			// Because ShouldFlee(owner) cannot retreat units while they cannot even fight
			// a unit that they cannot target. Therefore, use `cannotRetaliate` here to solve this bug.
			if (cannotRetaliate)
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsFleeStateCA(), true);

			tryAttack++;

			var unitlost = squadsize > owner.Units.Count;
			squadsize = owner.Units.Count;

			if (owner.TargetActor != null && (healthChange || unitlost) && !isFirstTick)
			{
				var friendlyUnits = owner.World.FindActorsInCircle(owner.TargetActor.CenterPosition, WDist.FromCells(owner.SquadManager.Info.AttackScanRadius)).Where(owner.SquadManager.IsValidAllyUnit);
				if (friendlyUnits.Count() < squadsize + owner.SquadManager.Info.SquadSize)
					owner.FuzzyStateMachine.ChangeState(owner, new GuerrillaUnitsRunState(), true);
			}

			owner.Bot.QueueOrder(new Order("AttackMove", null, Target.FromCell(owner.World, leader.Location), false, groupedActors: followingUnits.ToArray()));
			owner.Bot.QueueOrder(new Order("AttackMove", null, Target.FromActor(owner.TargetActor), false, groupedActors: attackingUnits.ToArray()));

			isFirstTick = false;
		}

		public void Deactivate(SquadCA owner) { }
	}

	class GuerrillaUnitsRunState : GroundStateBaseCA, IState
	{
		public const int HitTicks = 2;
		internal int Hit = HitTicks;
		bool ordered;

		public void Activate(SquadCA owner) { ordered = false; }

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			if (Hit-- <= 0)
			{
				Hit = HitTicks;
				owner.FuzzyStateMachine.ChangeState(owner, new GuerrillaUnitsHitState(), true);
				return;
			}

			if (!ordered)
			{
				owner.Bot.QueueOrder(new Order("Move", null, Target.FromCell(owner.World, RandomBuildingLocation(owner)), false, groupedActors: owner.Units.Select(u => u.Actor).ToArray()));
				ordered = true;
			}
		}

		public void Deactivate(SquadCA owner) { }
	}
	// 6f (CN A2/A6): an artillery squad trails an assault squad and bombards only
	// what the assault can see — its parent's target is fog-honest by
	// construction (observed actor or remembered frozen building).
	class ArtilleryUnitsIdleStateCA : GroundStateBaseCA, IState
	{
		public void Activate(SquadCA owner) { }

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			var parent = owner.Parent;
			if (parent == null || !parent.IsValid)
			{
				parent = owner.SquadManager.FindAttachableAssault(owner);
				owner.Parent = parent;
			}

			// No assault to escort: stop babysitting and act as one.
			if (parent == null)
			{
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsIdleStateCA(), false);
				return;
			}

			if (!parent.IsTargetValid)
			{
				// Parent is still forming up — trail it.
				owner.Target = Target.Invalid;
				owner.Bot.QueueOrder(new Order("AttackMove", null, Target.FromPos(parent.CenterPosition), false,
					groupedActors: owner.Units.Select(u => u.Actor).ToArray()));
				return;
			}

			owner.Target = parent.Target;
			var targetPos = owner.Target.CenterPosition;
			var anchor = SquadManagerBotModuleCA.HangBackAnchor(parent.CenterPosition, targetPos,
				WDist.FromCells(owner.SquadManager.Info.ArtilleryHangBackCells).Length);

			foreach (var u in owner.Units)
			{
				// Longest range over the enabled attack traits; TraitOrDefault<AttackBase>
				// throws on the many actors that carry more than one.
				var range = WDist.Zero;
				foreach (var attack in u.Actor.TraitsImplementing<AttackBase>())
				{
					if (attack.IsTraitDisabled)
						continue;

					var r = attack.GetMaximumRangeVersusTarget(owner.Target);
					if (r > range)
						range = r;
				}

				// In range: bombard the shared target. Out of range: move to the
				// hang-back anchor, NOT toward the target — the assault squad does
				// the closing so artillery keeps its range advantage.
				if (range > WDist.Zero && owner.Target.IsInRange(u.Actor.CenterPosition, range))
					owner.Bot.QueueOrder(new Order("Attack", u.Actor, owner.Target, false));
				else
					owner.Bot.QueueOrder(new Order("AttackMove", u.Actor, Target.FromPos(anchor), false));
			}
		}

		public void Deactivate(SquadCA owner) { }
	}

	// §12.4a: fire-support squads screen the artillery (or assault) squad they are
	// parented to. Members hold at the protected squad's position and AttackMove
	// back into screen range — escorts fight whatever threatens the parent instead
	// of drifting to the front or idling at home.
	class FireSupportUnitsIdleStateCA : GroundStateBaseCA, IState
	{
		const int HoldTicks = 250;
		const int OrderCooldownTicks = 25;
		int holdTicks;
		int orderCooldown;

		public void Activate(SquadCA owner) { }

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			var parent = owner.Parent;
			if (parent == null || !parent.IsValid)
			{
				// Re-attach to the biggest artillery squad first, else an assault.
				parent = owner.SquadManager.Squads
					.Where(s => s.Type == SquadCAType.Artillery && s.IsValid && s != owner)
					.MaxByOrDefault(s => s.Units.Count)
					?? owner.SquadManager.FindAttachableAssault(owner);
				owner.Parent = parent;
			}

			if (parent == null)
			{
				// Nothing to screen: hold near home like the support state rather
				// than trickling into the enemy alone.
				if (--holdTicks <= 0)
				{
					GoToRandomOwnBuilding(owner);
					holdTicks = HoldTicks;
				}

				return;
			}

			// Re-check follow range on a cooldown - issuing AttackMove every tick
			// resets the unit's current activity before it can close the distance.
			if (--orderCooldown > 0)
				return;

			orderCooldown = OrderCooldownTicks;
			var followRangeSquared = (long)WDist.FromCells(owner.SquadManager.Info.SupportFollowRangeCells).LengthSquared;
			var parentPos = parent.CenterPosition;
			foreach (var u in owner.Units)
			{
				if ((u.Actor.CenterPosition - parentPos).LengthSquared <= followRangeSquared)
					continue;

				owner.Bot.QueueOrder(new Order("AttackMove", u.Actor, Target.FromPos(parentPos), false));
			}
		}

		public void Deactivate(SquadCA owner) { }
	}

}
