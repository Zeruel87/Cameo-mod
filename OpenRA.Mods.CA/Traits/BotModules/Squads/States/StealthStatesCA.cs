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
	// CN3 (AI_MASTER_PLAN §3, crystallized-nexus port): dedicated squads for
	// cloak-capable armed ground units. The squad picks a seen-or-remembered
	// target outside known detector coverage, approaches without auto-attacking
	// (cloaked), aborts and flees when it takes damage before any unit aims or
	// when remembered detector coverage newly overlaps its position or target,
	// commits to one volley window once revealed and aiming, then flees to
	// re-cloak when the fight turns.
	//
	// Cameo changes vs the donor:
	//  - Detector coverage comes through IBotStealthDoctrine: remembered
	//    observations plus the observed type's public DetectCloaked range, not
	//    the donor's cell->type table and live world scan. Per-detector
	//    DetectionTypes do not survive the DTO - any remembered detector counts
	//    against every cloak type, which is the conservative direction.
	//  - ShouldFlee/CannotAttackEvenTogether are the shared
	//    GroundStateBaseCA dispatch (combat predictor when enabled, fuzzy
	//    otherwise) over the same visibility-gated threat enumeration.
	//  - BuildStealthApproachRoute's pinned-route machinery and
	//    FindAmbushChokepoint are deferred: both need the CN tactical map. A
	//    squad with no target simply holds position, and the approach goes
	//    straight at the target rather than around known coverage.
	public static class StealthHelpersCA
	{
		// CN parity: IsCoveredByKnownDetector added a margin to the printed
		// range so an approach skirting the bubble's edge does not clip it.
		internal const int DetectorSafetyCells = 2;

		public static bool IsCloakedOrUncloakable(Actor actor)
		{
			foreach (var cloak in actor.TraitsImplementing<Cloak>())
			{
				if (cloak.IsTraitDisabled)
					continue;

				if (!cloak.Cloaked)
					return false;
			}

			return true;
		}

		// A position is covered when it sits inside a remembered detector's
		// bubble - the observed type's DetectCloaked range plus the safety
		// margin. `cellCenter` is the map lookup, injected so tests can drive
		// the check without a World.
		public static bool CoveredByKnownDetector(IEnumerable<BotKnownDetector> detectors, Func<CPos, WPos> cellCenter, WPos position)
		{
			var safety = WDist.FromCells(DetectorSafetyCells).Length;
			foreach (var detector in detectors)
			{
				var reach = (long)WDist.FromCells(detector.RangeCells).Length + safety;
				if ((position - cellCenter(detector.Cell)).LengthSquared <= reach * reach)
					return true;
			}

			return false;
		}

		// CN FindRetreatCell's per-candidate score, pure for tests: distance to
		// the closest seen threat dominates (none in reach scores a flat
		// million), then a nudge away from that threat's cell, then a pull
		// toward the anchor (the squad's target while one stands, home
		// otherwise). Higher wins.
		public static int ScoreRetreatCell(CPos candidate, CPos anchor, WPos candidatePos,
			IReadOnlyList<(WPos Pos, CPos Cell)> threats, long threatRangeSq)
		{
			var closestEnemyDistance = int.MaxValue;
			var closestThreatCell = CPos.Zero;
			var foundThreat = false;

			foreach (var (pos, cell) in threats)
			{
				var distance = (pos - candidatePos).LengthSquared;
				if (distance > threatRangeSq)
					continue;

				if (distance < closestEnemyDistance)
				{
					closestEnemyDistance = (int)distance;
					closestThreatCell = cell;
					foundThreat = true;
				}
			}

			var score = closestEnemyDistance == int.MaxValue ? 1000000 : closestEnemyDistance;
			if (foundThreat)
				score += (candidate - closestThreatCell).LengthSquared * 20;
			score -= (candidate - anchor).LengthSquared * 2;

			return score;
		}
	}

	sealed class StealthUnitsIdleStateCA : GroundStateBaseCA, IState
	{
		// Game ticks, not update cycles: how long a target picked here is kept before the squad
		// looks for a better one.
		const int RethinkInterval = 225;
		int rethinkDeadlineTick;

		public void Activate(SquadCA owner) { rethinkDeadlineTick = owner.World.WorldTick; }

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			if (owner.World.WorldTick < rethinkDeadlineTick && owner.IsTargetValid)
			{
				owner.FuzzyStateMachine.ChangeState(owner, new StealthApproachStateCA(), true);
				return;
			}

			rethinkDeadlineTick = owner.World.WorldTick + RethinkInterval;
			var center = owner.Units[0].Actor;

			// Killing a soft target often returns here before the first-volley commitment expires. Do
			// not start a fresh commitment window for every building in the base: a revealed squad that
			// is now losing the local fight should disengage and cloak before choosing the next victim.
			if (owner.Units.Any(u => !StealthHelpersCA.IsCloakedOrUncloakable(u.Actor)) && ShouldFlee(owner))
			{
				owner.FuzzyStateMachine.ChangeState(owner, new StealthFleeStateCA(), true);
				return;
			}

			// A pick inside remembered detector coverage is a trap, not an ambush -
			// the squad decloaks into a gun it was warned about. Both pickers
			// return the single best candidate only, so a covered one is dropped
			// for this rethink rather than exchanged for the next candidate
			// (a candidate-exclusion API is the deferred half of the port).
			bool OutsideKnownDetection(WPos pos)
				=> !StealthHelpersCA.CoveredByKnownDetector(owner.SquadManager.RememberedDetectors(),
					c => owner.World.Map.CenterOfCell(c), pos);

			var attackerValue = owner.SquadManager.SquadValueOf(owner);
			var target = owner.SquadManager.FindClosestEnemy(center, attackerValue, owner);
			if (target != null && OutsideKnownDetection(target.CenterPosition))
			{
				owner.TargetActor = target;
				owner.FuzzyStateMachine.ChangeState(owner, new StealthApproachStateCA(), true);
				return;
			}

			// Nothing visible: commit to an enemy building the FrozenActorLayer
			// remembers - the record self-invalidates when the cell is
			// re-observed empty, so a stale memory cannot trap the squad.
			if (owner.SquadManager.FoggedScans)
			{
				var frozen = owner.SquadManager.FindFrozenEnemyTarget(center.CenterPosition, attackerValue, owner);
				if (frozen != null && OutsideKnownDetection(frozen.CenterPosition))
				{
					owner.Target = Target.FromFrozenActor(frozen);
					owner.FuzzyStateMachine.ChangeState(owner, new StealthApproachStateCA(), true);
				}
			}

			// Donor kept no target -> ambush-chokepoint reposition
			// (FindAmbushChokepoint, CN tactical map) is deferred; the squad
			// holds position until the next rethink.
		}

		public void Deactivate(SquadCA owner) { }
	}

	sealed class StealthApproachStateCA : GroundStateBaseCA, IState
	{
		// A stealth strike that reevaluates the fight on the same tick as its first volley often turns
		// around before the missiles land. Give the ambush enough time to kill its focus target, then
		// restore the normal threat/health decision instead of making the squad permanently fearless.
		const int MinimumCommitTicks = 150;
		const int MaxStuckTicks = 225;
		const int StrikeCommitDistanceCells = 8;

		bool ordersIssued;
		int firstRevealTick;
		int lastActivityTick;
		int lastTotalHealth;
		CPos lastCenterPos;

		public void Activate(SquadCA owner)
		{
			ordersIssued = false;
			firstRevealTick = 0;
			lastActivityTick = owner.World.WorldTick;
			lastTotalHealth = TotalHealth(owner);
			lastCenterPos = owner.Units[0].Actor.Location;
		}

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			if (!owner.IsTargetValid)
			{
				owner.FuzzyStateMachine.ChangeState(owner, new StealthUnitsIdleStateCA(), true);
				return;
			}

			if (!ordersIssued && !IssueApproachOrders(owner))
				return;

			var allCloaked = owner.Units.All(u => StealthHelpersCA.IsCloakedOrUncloakable(u.Actor));
			var totalHealth = TotalHealth(owner);
			var tookDamage = totalHealth < lastTotalHealth;
			lastTotalHealth = totalHealth;
			var anyAiming = IsAnyUnitAiming(owner);
			var center = owner.Units[0].Actor;
			var strikeDistance = WDist.FromCells(StrikeCommitDistanceCells).Length;
			var closeToStrike = (center.CenterPosition - owner.Target.CenterPosition).HorizontalLengthSquared <=
				(long)strikeDistance * strikeDistance;
			var knownDetectionAhead = CoveredByKnownDetector(owner, center.CenterPosition) ||
				CoveredByKnownDetector(owner, owner.Target.CenterPosition);
			if (allCloaked && knownDetectionAhead && !closeToStrike)
			{
				AIUtils.BotDebug("AI ({0}): stealth squad aborted {1}: detector coverage changed during approach",
					owner.Bot.Player.ClientIndex, owner.Target);
				owner.Target = Target.Invalid;
				owner.FuzzyStateMachine.ChangeState(owner, new StealthFleeStateCA(), true);
				return;
			}

			// Detection does not clear Cloak.Cloaked: it only makes the unit visible to the detector's
			// owner. Damage is therefore the first legal signal when an unseen detector catches a squad.
			// A hit on the run-in is not an ambush volley and must not buy the old six-second commitment.
			if (tookDamage && !anyAiming && !closeToStrike)
			{
				owner.FuzzyStateMachine.ChangeState(owner, new StealthFleeStateCA(), true);
				return;
			}

			if ((!allCloaked || tookDamage) && firstRevealTick == 0)
				firstRevealTick = owner.World.WorldTick;

			var committed = firstRevealTick > 0 &&
				(anyAiming || closeToStrike) && owner.World.WorldTick - firstRevealTick < MinimumCommitTicks;

			// A still-cloaked squad has not joined the local fight yet. Letting nearby enemies feed the
			// fuzzy flee check here made covert routes peel away merely because they passed a defended
			// area. Once revealed, the squad commits to one volley window and then judges the real fight.
			if ((!allCloaked || tookDamage) && !committed && ShouldFlee(owner))
			{
				owner.FuzzyStateMachine.ChangeState(owner, new StealthFleeStateCA(), true);
				return;
			}

			var currentPos = center.Location;

			if (currentPos != lastCenterPos || anyAiming)
			{
				lastActivityTick = owner.World.WorldTick;
				lastCenterPos = currentPos;
			}

			if (owner.World.WorldTick > lastActivityTick + MaxStuckTicks)
			{
				owner.FuzzyStateMachine.ChangeState(owner, new StealthUnitsIdleStateCA(), true);
				return;
			}

			foreach (var u in owner.Units)
				if (u.Actor.IsIdle)
					owner.Bot.QueueOrder(new Order("Attack", u.Actor, owner.Target, false));
		}

		public void Deactivate(SquadCA owner) { }

		static bool CoveredByKnownDetector(SquadCA owner, WPos position)
		{
			return StealthHelpersCA.CoveredByKnownDetector(owner.SquadManager.RememberedDetectors(),
				c => owner.World.Map.CenterOfCell(c), position);
		}

		bool IssueApproachOrders(SquadCA owner)
		{
			// The donor routed a building approach along a pinned infiltration
			// path (BuildStealthApproachRoute) that skirted remembered detector
			// bubbles - deferred, it needs the CN tactical map. A direct Attack
			// order still walks to the target and engages only it: unlike
			// AttackMove it does not auto-engage contacts on the way in, which
			// is what keeps the run-in covert.
			var units = owner.Units.OrderBy(u => u.Actor.ActorID).Select(u => u.Actor).ToArray();
			if (units.Length == 0)
				return false;

			foreach (var unit in units)
				owner.Bot.QueueOrder(new Order("Attack", unit, owner.Target, false));

			ordersIssued = true;
			return true;
		}

		static int TotalHealth(SquadCA owner)
		{
			var total = 0;
			foreach (var u in owner.Units)
				total += u.Actor.TraitOrDefault<IHealth>()?.HP ?? 0;

			return total;
		}

		static bool IsAnyUnitAiming(SquadCA owner)
		{
			foreach (var u in owner.Units)
			{
				foreach (var attack in u.Actor.TraitsImplementing<AttackBase>())
					if (!attack.IsTraitDisabled && attack.IsAiming)
						return true;
			}

			return false;
		}
	}

	sealed class StealthFleeStateCA : GroundStateBaseCA, IState
	{
		const int RecloakWaitTicks = 150;
		const int MinRetreatCells = 6;
		const int MaxRetreatCells = 14;
		const int ReengageThreatDistanceCells = 10;
		int fleeDeadlineTick;

		public void Activate(SquadCA owner)
		{
			fleeDeadlineTick = owner.World.WorldTick + RecloakWaitTicks;

			var retreatCell = FindRetreatCell(owner);
			if (retreatCell.HasValue)
			{
				var target = Target.FromCell(owner.World, retreatCell.Value);
				foreach (var u in owner.Units)
					owner.Bot.QueueOrder(new Order("Move", u.Actor, target, false));
			}
			else
				GoToRandomOwnBuilding(owner);
		}

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			var center = owner.Units[0].Actor;
			var allCloaked = owner.Units.All(u => StealthHelpersCA.IsCloakedOrUncloakable(u.Actor));

			// The donor's FindClosestThreat over the DangerScanRadius circle: the
			// same visibility-gated enumeration the other flee paths use - only
			// what the bot can currently see counts as a threat.
			var enemy = owner.SquadManager.VisibleEnemiesNear(center.CenterPosition,
					WDist.FromCells(owner.SquadManager.Info.DangerScanRadius))
				.Where(a => a.Info.HasTraitInfo<AttackBaseInfo>())
				.MinByOrDefault(a => (a.CenterPosition - center.CenterPosition).HorizontalLengthSquared);

			if (enemy == null ||
				(allCloaked && HasOpenedKiteDistance(center, enemy)) ||
				owner.World.WorldTick >= fleeDeadlineTick)
				owner.FuzzyStateMachine.ChangeState(owner, new StealthUnitsIdleStateCA(), true);
		}

		public void Deactivate(SquadCA owner) { }

		static bool HasOpenedKiteDistance(Actor center, Actor enemy)
		{
			var minDistance = WDist.FromCells(ReengageThreatDistanceCells).Length;
			return (center.CenterPosition - enemy.CenterPosition).HorizontalLengthSquared >= (long)minDistance * minDistance;
		}

		// CN FindRetreatCell: the best cell in a ring around the squad leader to
		// fall back to - far from seen threats, close to the target or home. One
		// scan covers every candidate's detection radius instead of a circle per
		// candidate. Returns null when the leader cannot move (no Mobile), which
		// is when the caller sends everyone to a random own building instead.
		static CPos? FindRetreatCell(SquadCA owner)
		{
			var leader = owner.Units[0].Actor;
			var mobile = leader.TraitOrDefault<Mobile>();
			if (mobile == null)
				return null;

			var map = owner.World.Map;
			var origin = leader.Location;
			var baseCell = owner.SquadManager.GetRandomBaseCenter();
			var dangerRadiusCells = Math.Max(0, owner.SquadManager.Info.DangerScanRadius) + 4;

			var scanRadius = WDist.FromCells(MaxRetreatCells + dangerRadiusCells);
			var threats = owner.World.FindActorsInCircle(leader.CenterPosition, scanRadius)
				.Where(a => owner.SquadManager.IsPreferredObservedEnemyUnit(a) && a.Info.HasTraitInfo<AttackBaseInfo>())
				.Select(a => (Pos: a.CenterPosition, Cell: a.Location))
				.ToList();

			var threatRangeSq = (long)WDist.FromCells(dangerRadiusCells).Length * WDist.FromCells(dangerRadiusCells).Length;
			var anchor = owner.IsTargetValid
				? map.CellContaining(owner.Target.CenterPosition)
				: baseCell;

			CPos? bestCell = null;
			var bestScore = int.MinValue;

			for (var dy = -MaxRetreatCells; dy <= MaxRetreatCells; dy++)
			{
				for (var dx = -MaxRetreatCells; dx <= MaxRetreatCells; dx++)
				{
					var distanceSquared = dx * dx + dy * dy;
					if (distanceSquared < MinRetreatCells * MinRetreatCells ||
						distanceSquared > MaxRetreatCells * MaxRetreatCells)
						continue;

					var candidate = origin + new CVec(dx, dy);
					if (!map.Contains(candidate) || !mobile.CanEnterCell(candidate))
						continue;

					var score = StealthHelpersCA.ScoreRetreatCell(candidate, anchor,
						map.CenterOfCell(candidate), threats, threatRangeSq);
					if (score <= bestScore)
						continue;

					bestScore = score;
					bestCell = candidate;
				}
			}

			return bestCell;
		}
	}
}
