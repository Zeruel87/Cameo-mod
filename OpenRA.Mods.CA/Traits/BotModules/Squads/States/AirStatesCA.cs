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
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits.BotModules.Squads
{
	abstract class AirStateBaseCA : StateBaseCA
	{
		static readonly BitSet<TargetableType> AirTargetTypes = new BitSet<TargetableType>("Air");

		protected const int StaticAntiAirMultiplier = 3;

		protected static int CountAntiAirUnits(IEnumerable<Actor> units, SquadCA owner)
		{
			if (!units.Any())
				return 0;

			var missileUnitsCount = 0;
			foreach (var unit in units)
			{
				if (unit == null || unit.IsDead)
					continue;

				if (owner.SquadManager.Info.StaticAntiAirTypes.Contains(unit.Info.Name))
				{
					missileUnitsCount += StaticAntiAirMultiplier;
					continue;
				}

				foreach (var ab in unit.TraitsImplementing<AttackBase>())
				{
					if (ab.IsTraitDisabled || ab.IsTraitPaused)
						continue;

					foreach (var a in ab.Armaments)
					{
						if (a.Weapon.IsValidTarget(AirTargetTypes))
						{
							missileUnitsCount++;
							break;
						}
					}
				}
			}

			return missileUnitsCount / StaticAntiAirMultiplier;
		}

		// CA-5: the farthest this unit's air-valid weapons reach. Zero = not AA.
		protected static WDist AntiAirRange(Actor unit)
		{
			var range = WDist.Zero;
			foreach (var ab in unit.TraitsImplementing<AttackBase>())
			{
				if (ab.IsTraitDisabled || ab.IsTraitPaused)
					continue;

				foreach (var a in ab.Armaments)
					if (a.Weapon.IsValidTarget(AirTargetTypes) && a.Weapon.Range > range)
						range = a.Weapon.Range;
			}

			return range;
		}

		// CA-5: same weighting as CountAntiAirUnits, but an enemy only counts when
		// its air weapons actually reach `loc` - a SAM site beyond its range is
		// scenery, and a long-range one outside DangerScanRadius still threatens.
		protected static int CountAntiAirUnitsInRange(IEnumerable<Actor> units, WPos loc, SquadCA owner)
		{
			if (!units.Any())
				return 0;

			var missileUnitsCount = 0;
			foreach (var unit in units)
			{
				if (unit == null || unit.IsDead)
					continue;

				var range = AntiAirRange(unit);
				if (range == WDist.Zero || (unit.CenterPosition - loc).HorizontalLength > range.Length)
					continue;

				// LC6: a unit counted toward the gate IS consumed by the decision -
				// an unseen AA must never move this count.
				owner.SquadManager.CanaryObserved(unit, "aa-gate");

				missileUnitsCount += owner.SquadManager.Info.StaticAntiAirTypes.Contains(unit.Info.Name)
					? StaticAntiAirMultiplier
					: 1;
			}

			return missileUnitsCount / StaticAntiAirMultiplier;
		}

		// CA-5: NearToPosSafely with per-unit AA ranges for the doctrine states.
		// One wider sweep covers long-range AA; targets are still judged inside
		// DangerScanRadius so target selection matches the generic air wing.
		protected static bool NearToPosSafelyAircraft(SquadCA owner, WPos loc)
		{
			return NearToPosSafelyAircraft(owner, loc, out _);
		}

		protected static bool NearToPosSafelyAircraft(SquadCA owner, WPos loc, out Actor detectedEnemyTarget)
		{
			detectedEnemyTarget = null;
			var dangerRadius = owner.SquadManager.Info.DangerScanRadius;

			var nearby = owner.World.FindActorsInCircle(loc, WDist.FromCells(dangerRadius * 2))
				.Where(a => owner.SquadManager.IsPreferredObservedEnemyUnit(a))
				.ToList();

			if (nearby.Count == 0)
				return true;

			if (CountAntiAirUnitsInRange(nearby, loc, owner) >= owner.Units.Count)
				return false;

			var dangerRadiusLength = WDist.FromCells(dangerRadius).Length;
			var possibleTargets = nearby
				.Where(a => (a.CenterPosition - loc).HorizontalLength <= dangerRadiusLength
					&& owner.SquadManager.IsAirSquadTargetType(a, owner))
				.ToList();

			if (possibleTargets.Count > 0)
			{
				possibleTargets = owner.SquadManager.PreferSquadTargets(possibleTargets, owner, owner.SquadManager.TagsOf);
				detectedEnemyTarget = possibleTargets.Random(owner.Random);
			}

			return true;
		}

		protected static bool IsPathSafe(SquadCA owner, WPos start, WPos end)
		{
			var map = owner.World.Map;
			var stepSize = owner.SquadManager.Info.DangerScanRadius;
			var direction = new WVec((end - start).X, (end - start).Y, 0);
			var distance = direction.Length;

			if (distance == 0)
				return NearToPosSafely(owner, start);

			var normalizedDirection = new WVec(
				direction.X * 1024 / distance,
				direction.Y * 1024 / distance,
				direction.Z * 1024 / distance
			);
			// Evaluate each grid cell along the path
			for (var d = 0; d <= distance; d += stepSize * 2048) // cpos to wpos
			{
				var currentPos = start + normalizedDirection * d / 1024;
				var cell = map.CellContaining(currentPos);

				// Check if the current grid cell is safe
				if (!NearToPosSafely(owner, map.CenterOfCell(cell)))
					return false;
			}

			return true;
		}

		protected static Actor FindAirTarget(SquadCA owner)
		{
			Actor target = null;
			var groundTargetPriority = owner.World.LocalRandom.Next(0, 100);

			if (groundTargetPriority > owner.SquadManager.Info.AirToAirPriority)
				return target;

			var leader = owner.Units.FirstOrDefault().Actor;
			if (leader == null)
				return target;

			var canAttackAir = false;
			foreach (var ab in leader.TraitsImplementing<AttackBase>())
			{
				foreach (var a in ab.Armaments)
				{
					if (a.Weapon.IsValidTarget(AirTargetTypes))
					{
						canAttackAir = true;
						break;
					}
				}
			}

			if (canAttackAir)
			{
				var pos = leader.CenterPosition;

				if (owner.SquadManager.Info.BigAirThreats.Count > 0)
				{
					var regularTargetPriority = owner.World.LocalRandom.Next(0, 100);

					if (owner.SquadManager.Info.AirToAirPriority > regularTargetPriority)
					{
						target = owner.World.Actors.Where(a => owner.SquadManager.IsPreferredEnemyAircraft(a) &&
							owner.SquadManager.IsNotHiddenUnit(a) &&
							a.IsTargetableBy(leader) &&
							owner.SquadManager.Info.BigAirThreats.Contains(a.Info.Name))
							.ClosestToIgnoringPath(pos);
					}
				}

				if (target != null)
					return target;

				target = owner.World.Actors.Where(a => owner.SquadManager.IsPreferredEnemyAircraft(a) &&
					owner.SquadManager.IsNotHiddenUnit(a) &&
					a.IsTargetableBy(leader))
					.ClosestToIgnoringPath(pos);
			}

			return target;
		}

		protected static Actor FindDefenselessTarget(SquadCA owner)
		{
			var target = FindAirTarget(owner);
			if (target != null)
			{
				owner.SquadManager.CanaryObserved(target, "air-target");
				return target;
			}

			FindSafePlace(owner, out target, true);
			if (target != null)
				owner.SquadManager.CanaryObserved(target, "air-safescan");

			return target;
		}

		protected static CPos? FindSafePlace(SquadCA owner, out Actor detectedEnemyTarget, bool needTarget)
		{
			var leader = owner.Units.FirstOrDefault().Actor;
			var map = owner.World.Map;
			detectedEnemyTarget = null;

			foreach (var pos in owner.SquadManager.airStrikeGrid.Shuffle(owner.World.LocalRandom).ToArray()) //.OrderBy(a => (a - leader.Location).LengthSquared))
			{
				if (NearToPosSafely(owner, map.CenterOfCell(pos), out detectedEnemyTarget))
				{
					if (needTarget && detectedEnemyTarget == null)
						continue;

					if (!IsPathSafe(owner, leader.CenterPosition, map.CenterOfCell(pos)))
						continue;

					return pos;
				}
			}

			return null;
		}

		protected static bool NearToPosSafely(SquadCA owner, WPos loc)
		{
			return NearToPosSafely(owner, loc, out _);
		}

		protected static bool NearToPosSafely(SquadCA owner, WPos loc, out Actor detectedEnemyTarget)
		{
			detectedEnemyTarget = null;
			var dangerRadius = owner.SquadManager.Info.DangerScanRadius;
			var unitsAroundPos = owner.World.FindActorsInCircle(loc, WDist.FromCells(dangerRadius))
				.Where(a => owner.SquadManager.IsPreferredObservedEnemyUnit(a));

			if (!unitsAroundPos.Any())
				return true;

			var possibleTargets = unitsAroundPos.Where(a => owner.SquadManager.IsAirSquadTargetType(a, owner)).ToList();
			var possibleAntiAir = unitsAroundPos.ToList();

			if (CountAntiAirUnits(possibleAntiAir, owner) < owner.Units.Count)
			{
				if (possibleTargets.Count > 0)
				{
					possibleTargets = owner.SquadManager.PreferSquadTargets(possibleTargets, owner, owner.SquadManager.TagsOf);
					detectedEnemyTarget = possibleTargets.Random(owner.Random);
				}

				return true;
			}

			return false;
		}

		// Checks the number of anti air enemies around units
		protected virtual bool ShouldFlee(SquadCA owner)
		{
			return ShouldFlee(owner, enemies => CountAntiAirUnits(enemies, owner) > owner.Units.Count);
		}

		// CA-5 (12.8): the idle state an air-family squad returns to after fleeing.
		// Doctrine squads keep their role behaviour; generic Air squads keep theirs.
		protected static IState IdleStateFor(SquadCA owner) => owner.Type switch
		{
			SquadCAType.Fighter => new FighterIdleStateCA(),
			SquadCAType.Gunship => new GunshipCASStateCA(),
			SquadCAType.Bomber => new BomberIdleStateCA(),
			_ => new AirIdleStateCA(),
		};
	}

	class AirIdleStateCA : AirStateBaseCA, IState
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

			var e = FindDefenselessTarget(owner);
			if (e == null)
				return;

			owner.TargetActor = e;
			owner.FuzzyStateMachine.ChangeState(owner, new AirAttackStateCA(), true);
		}

		public void Deactivate(SquadCA owner) { }
	}

	class AirAttackStateCA : AirStateBaseCA, IState
	{
		// Set after the strike route is attempted for the current target —
		// the state may be entered with a valid target (AirIdle already
		// picked one), where newTarget never fires but routing still applies.
		bool routedCurrentTarget;

		public void Activate(SquadCA owner) { }

		public void Tick(SquadCA owner)
		{
			var newTarget = false;

			if (!owner.IsValid)
				return;

			// target is no longer valid, find a new target
			if (!owner.IsTargetValid)
			{
				var closestEnemy = FindAirTarget(owner);
				if (closestEnemy == null)
				{
					var a = owner.Units.Random(owner.Random).Actor;

					// copied from FindClosestEnemy() so that non-air squads don't check IsAirSquadTargetType unnecessarily
					var units = owner.SquadManager.PreferSquadTargets(
						a.World.Actors.Where(t => owner.SquadManager.IsPreferredObservedEnemyUnit(t) && owner.SquadManager.IsAirSquadTargetType(t, owner)).ToList(),
						owner, owner.SquadManager.TagsOf);
					closestEnemy = units.Where(owner.SquadManager.IsNotHiddenUnit).ClosestToIgnoringPath(a.CenterPosition) ?? units.ClosestToIgnoringPath(a.CenterPosition);
				}

				if (closestEnemy != null)
				{
					owner.TargetActor = closestEnemy;
					newTarget = true;
				}
				else
				{
					owner.FuzzyStateMachine.ChangeState(owner, new AirFleeStateCA(), true);
					return;
				}
			}

			if (!NearToPosSafely(owner, owner.TargetActor.CenterPosition))
			{
				owner.FuzzyStateMachine.ChangeState(owner, new AirFleeStateCA(), true);
				return;
			}

			var leader = owner.Units.FirstOrDefault().Actor;
			var buildableInfo = leader.Info.TraitInfoOrDefault<BuildableInfo>();
			var limitOne = buildableInfo != null && buildableInfo.BuildLimit == 1;

			// CA-5 (AI_ARCHITECTURE §12.8): on a fresh target, transit through
			// waypoints that skirt remembered anti-air coverage instead of
			// beelining. The router picks the threat read by leader domain —
			// aircraft pay remembered AntiAir, ground pays Army+Defence.
			var needRoute = newTarget || !routedCurrentTarget;
			var strikeRoute = needRoute && leader != null
				? owner.SquadManager.RouteAroundThreat(leader, owner.World.Map.CellContaining(owner.TargetActor.CenterPosition))
				: null;

			if (needRoute)
				routedCurrentTarget = true;

			// CA F2p2 (71754fc06): evaluated lazily - the limit check is only needed when the squad would otherwise keep waiting.
			System.Func<bool> canBuildMoreOfAircraft = () => leader != null && !limitOne && owner.SquadManager.CanBuildMoreOfAircraft(leader.Info);
			var waitingCount = owner.WaitingUnits.Count();

			var waitingPatience = 99;
			if (waitingCount > 7)
				waitingPatience = 65;
			else if (waitingCount > 3)
				waitingPatience = 85;
			else if (waitingCount > 1)
				waitingPatience = 95;

			var impatience = owner.World.LocalRandom.Next(100);
			var noPatience = impatience > waitingPatience;

			foreach (var a in owner.Units)
			{
				var currentActivity = a.Actor.CurrentActivity;
				if (currentActivity == null) continue;
				var activityType = currentActivity.GetType();
				var nextActivity = currentActivity.NextActivity;

				var ammoPools = a.Actor.TraitsImplementing<AmmoPool>().ToArray();
				if (!ReloadsAutomatically(ammoPools, a.Actor.TraitOrDefault<Rearmable>()))
				{
					if (!HasAmmo(ammoPools) && !owner.RearmingUnits.Contains(a.Actor))
					{
						owner.RearmingUnits.Add(a.Actor);
						owner.WaitingUnits.Remove(a.Actor);
						owner.NewUnits.Remove(a.Actor);
						owner.Bot.QueueOrder(new Order("ReturnToBase", a.Actor, false));
						continue;
					}

					if (owner.NewUnits.Contains(a.Actor))
					{
						owner.WaitingUnits.Add(a.Actor);
						owner.NewUnits.Remove(a.Actor);
						owner.Bot.QueueOrder(new Order("Move", a.Actor, Target.FromCell(owner.World, RandomBuildingLocation(owner)), false));
					}

					if (owner.WaitingUnits.Contains(a.Actor))
						continue;

					if (owner.RearmingUnits.Contains(a.Actor))
					{
						if (FullAmmo(ammoPools))
						{
							owner.RearmingUnits.Remove(a.Actor);
							owner.WaitingUnits.Add(a.Actor);
							owner.Bot.QueueOrder(new Order("Move", a.Actor, Target.FromCell(owner.World, RandomBuildingLocation(owner)), false));
						}
						else
							owner.Bot.QueueOrder(new Order("ReturnToBase", a.Actor, false));

						continue;
					}

					// target switched or not attacking, attack the target. A unit
					// mid-Fly is transiting the strike route's waypoints — its
					// queued Attack takes over on arrival, so leave it alone.
					if ((newTarget || (activityType != typeof(FlyAttack) && activityType != typeof(Fly))) && CanAttackTarget(a.Actor, owner.TargetActor))
					{
						if (strikeRoute != null && strikeRoute.Count > 0)
						{
							for (var i = 0; i < strikeRoute.Count; i++)
								owner.Bot.QueueOrder(new Order("Move", a.Actor, Target.FromCell(owner.World, strikeRoute[i]), i != 0));

							owner.Bot.QueueOrder(new Order("Attack", a.Actor, Target.FromActor(owner.TargetActor), true));
						}
						else
							owner.Bot.QueueOrder(new Order("Attack", a.Actor, Target.FromActor(owner.TargetActor), false));

						continue;
					}
					else if (activityType == typeof(FlyIdle))
					{
						owner.RearmingUnits.Add(a.Actor);
						owner.Bot.QueueOrder(new Order("ReturnToBase", a.Actor, false));
					}
				}
				else
					owner.WaitingUnits.Add(a.Actor);
			}

			if (owner.WaitingUnits.Count > 0 && owner.WaitingUnits.Count >= owner.RearmingUnits.Count && (noPatience || !canBuildMoreOfAircraft()))
			{
				foreach (var a in owner.WaitingUnits)
					if (CanAttackTarget(a, owner.TargetActor))
						owner.Bot.QueueOrder(new Order("Attack", a, Target.FromActor(owner.TargetActor), false));

				owner.WaitingUnits.Clear();
			}
		}

		public void Deactivate(SquadCA owner) { }
	}

	class AirFleeStateCA : AirStateBaseCA, IState
	{
		public void Activate(SquadCA owner) { }

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			Retreat(owner, flee: false, rearm: true, repair: true);

			owner.FuzzyStateMachine.ChangeState(owner, IdleStateFor(owner), true);
		}

		public void Deactivate(SquadCA owner) { }
	}
}
