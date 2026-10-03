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
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits.BotModules.Squads
{
	// CA-5 (AI_ARCHITECTURE.md 12.8): role-specific idle states for the doctrine
	// squads. They pick targets per role; AirAttackStateCA still flies the strike
	// (threat routing, rearm cycle) and AirFleeStateCA returns here via
	// IdleStateFor.
	//
	// Survival rule for all three: a target is only accepted inside AA cover the
	// squad can take - per-unit weapon range decides, not a fixed circle
	// (NearToPosSafelyAircraft). Route legs are plotted around remembered AA by
	// the 6e router in AirAttackStateCA / RouteAroundThreat.

	class FighterIdleStateCA : AirStateBaseCA, IState
	{
		public void Activate(SquadCA owner) { }

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			if (ShouldFlee(owner))
			{
				owner.FuzzyStateMachine.ChangeState(owner, new AirFleeStateCA(), true);
				return;
			}

			var e = FindFighterTarget(owner);
			if (e == null)
				return;

			owner.TargetActor = e;
			owner.FuzzyStateMachine.ChangeState(owner, new AirAttackStateCA(), true);
		}

		// Air superiority first: hunt visible enemy aircraft, preferring the
		// configured big threats; otherwise pick off an enemy unit isolated from
		// its army - few armed allies nearby and no AA reaching it that the squad
		// cannot take.
		static Actor FindFighterTarget(SquadCA owner)
		{
			var squadManager = owner.SquadManager;
			var leader = owner.Units[0].Actor;
			var pos = leader.CenterPosition;

			var aircraft = owner.World.Actors
				.Where(a => squadManager.IsPreferredEnemyAircraft(a) && squadManager.IsNotHiddenUnit(a) && a.IsTargetableBy(leader))
				.ToList();

			// Big threats first, then nearest; skip targets sitting under AA the
			// squad cannot outgun - diving covered airspace is suicide.
			var ordered = aircraft
				.OrderByDescending(a => squadManager.Info.BigAirThreats.Contains(a.Info.Name))
				.ThenBy(a => (a.CenterPosition - pos).LengthSquared);
			foreach (var c in ordered)
				if (NearToPosSafelyAircraft(owner, c.CenterPosition))
				{
					owner.SquadManager.CanaryObserved(c, "fighter-air-target");
					return c;
				}

			var candidates = owner.World.Actors
				.Where(a => squadManager.IsPreferredObservedEnemyUnit(a) && squadManager.IsNotHiddenUnit(a)
					&& squadManager.IsAirSquadTargetType(a, owner) && a.IsTargetableBy(leader))
				.ToList();

			foreach (var c in squadManager.PreferSquadTargets(candidates, owner, squadManager.TagsOf)
				.OrderBy(c => (c.CenterPosition - pos).LengthSquared))
			{
				if (IsIsolated(owner, c) && NearToPosSafelyAircraft(owner, c.CenterPosition))
				{
					owner.SquadManager.CanaryObserved(c, "fighter-pickoff");
					return c;
				}
			}

			return null;
		}

		static bool IsIsolated(SquadCA owner, Actor target)
		{
			var squadManager = owner.SquadManager;
			var near = owner.World.FindActorsInCircle(target.CenterPosition, WDist.FromCells(squadManager.Info.DangerScanRadius))
				.Where(a => squadManager.IsPreferredObservedEnemyUnit(a))
				.ToList();

			// LC6: each counted escort is consumed by the isolation decision -
			// an unseen escort must never change it.
			var escorts = near.Where(a => a.Info.HasTraitInfo<AttackBaseInfo>()).ToList();
			foreach (var e in escorts)
				squadManager.CanaryObserved(e, "fighter-isolation");

			return escorts.Count <= squadManager.Info.FighterPickoffMaxEscorts;
		}

		public void Deactivate(SquadCA owner) { }
	}

	class GunshipCASStateCA : AirStateBaseCA, IState
	{
		public void Activate(SquadCA owner) { }

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			if (ShouldFlee(owner))
			{
				owner.FuzzyStateMachine.ChangeState(owner, new AirFleeStateCA(), true);
				return;
			}

			// 12.8 CAS: attach to the main assault and engage what the frontline
			// engages. The largest ground-combat squad (artillery included, so the
			// wing rides shotgun over the siege line) stands in for the frontline.
			var anchor = owner.SquadManager.Squads
				.Where(s => s.IsValid && s != owner &&
					(s.Type == SquadCAType.Rush || s.Type == SquadCAType.Protection ||
					 s.Type == SquadCAType.FireSupport || s.Type == SquadCAType.Guerrilla ||
					 s.Type == SquadCAType.Artillery))
				.MaxByOrDefault(s => s.Units.Count);

			var leader = owner.Units[0].Actor;

			if (anchor == null)
			{
				// No frontline yet: hunt like the generic air wing.
				var fallback = FindDefenselessTarget(owner);
				if (fallback == null)
					return;

				owner.TargetActor = fallback;
				owner.FuzzyStateMachine.ChangeState(owner, new AirAttackStateCA(), true);
				return;
			}

			var anchorPos = anchor.CenterPosition;
			var anchorTarget = anchor.TargetActor;
			var target = anchor.IsTargetValid && anchorTarget != null && NearToPosSafelyAircraft(owner, anchorTarget.CenterPosition)
				? anchorTarget
				: FindCasTarget(owner, anchorPos);

			if (target != null)
				owner.SquadManager.CanaryObserved(target, "gunship-cas-target");

			if (target != null)
			{
				owner.TargetActor = target;
				owner.FuzzyStateMachine.ChangeState(owner, new AirAttackStateCA(), true);
				return;
			}

			// Nothing to engage: hover over the frontline - but never cross AA
			// cover to get there. Remembered-threat routing first, the direct
			// line only if it is clean; otherwise hold position.
			var casRadius = WDist.FromCells(owner.SquadManager.Info.GunshipCASRadiusCells).Length;
			if ((leader.CenterPosition - anchorPos).HorizontalLength <= casRadius)
				return;

			var anchorCell = owner.World.Map.CellContaining(anchorPos);
			var route = owner.SquadManager.RouteAroundThreat(leader, anchorCell);
			List<CPos> waypoints;
			if (route != null && route.Count > 0)
				waypoints = route;
			else if (IsPathSafe(owner, leader.CenterPosition, anchorPos))
				waypoints = [anchorCell];
			else
				return;

			foreach (var u in owner.Units)
			{
				var current = u.Actor.CurrentActivity;
				if (current == null || current is FlyIdle)
				{
					for (var i = 0; i < waypoints.Count; i++)
						owner.Bot.QueueOrder(new Order("Move", u.Actor, Target.FromCell(owner.World, waypoints[i]), i != 0));
				}
			}
		}

		static Actor FindCasTarget(SquadCA owner, WPos anchorPos)
		{
			var squadManager = owner.SquadManager;
			var leader = owner.Units[0].Actor;
			var radius = WDist.FromCells(squadManager.Info.GunshipCASRadiusCells);

			var candidates = owner.World.FindActorsInCircle(anchorPos, radius)
				.Where(a => squadManager.IsPreferredObservedEnemyUnit(a) && squadManager.IsNotHiddenUnit(a)
					&& squadManager.IsAirSquadTargetType(a, owner) && a.IsTargetableBy(leader))
				.ToList();

			if (candidates.Count == 0)
				return null;

			return squadManager.PreferSquadTargets(candidates, owner, squadManager.TagsOf)
				.Where(a => NearToPosSafelyAircraft(owner, a.CenterPosition))
				.ClosestToIgnoringPath(anchorPos);
		}

		public void Deactivate(SquadCA owner) { }
	}

	class BomberIdleStateCA : AirStateBaseCA, IState
	{
		public void Activate(SquadCA owner) { }

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			if (ShouldFlee(owner))
			{
				owner.FuzzyStateMachine.ChangeState(owner, new AirFleeStateCA(), true);
				return;
			}

			// 12.8: strike teams gather before flying - a short-staffed team holds.
			if (owner.Units.Count < owner.SquadManager.Info.BomberSquadMinSize)
				return;

			var target = FindBomberTarget(owner);

			// A full team does not wait on a tagged target - take an opportunity
			// target like the generic air wing would.
			if (target == null && owner.Units.Count >= owner.SquadManager.Info.BomberSquadMaxSize)
				target = FindDefenselessTarget(owner);

			if (target == null)
				return;

			owner.TargetActor = target;
			owner.FuzzyStateMachine.ChangeState(owner, new AirAttackStateCA(), true);
		}

		// Tag-priority targets (12.8's strike list: superweapon, conyard,
		// production, refinery, power, harvester, artillery) the team can hit and
		// whose position is not covered by AA it cannot take. The strike itself
		// routes over the remembered air-threat layer in AirAttackStateCA.
		static Actor FindBomberTarget(SquadCA owner)
		{
			var squadManager = owner.SquadManager;
			var leader = owner.Units[0].Actor;
			var pos = leader.CenterPosition;

			var candidates = owner.World.Actors
				.Where(a => squadManager.IsPreferredObservedEnemyUnit(a) && squadManager.IsNotHiddenUnit(a)
					&& squadManager.IsAirSquadTargetType(a, owner) && a.IsTargetableBy(leader)
					&& squadManager.TagsOf(a) is { } tags && tags.Overlaps(owner.PriorityTags))
				.OrderBy(a => (a.CenterPosition - pos).LengthSquared);

			foreach (var c in candidates)
				if (NearToPosSafelyAircraft(owner, c.CenterPosition))
				{
					owner.SquadManager.CanaryObserved(c, "bomber-target");
					return c;
				}

			return null;
		}

		public void Deactivate(SquadCA owner) { }
	}
}
