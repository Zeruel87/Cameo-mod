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
using OpenRA.Traits;
using OpenRA.Mods.Common.Traits;

namespace OpenRA.Mods.CA.Traits.BotModules.Squads
{
	class UnitsForProtectionIdleState : GroundStateBaseCA, IState
	{
		public void Activate(SquadCA owner) { }
		public void Tick(SquadCA owner) { owner.FuzzyStateMachine.ChangeState(owner, new UnitsForProtectionAttackState(), true); }
		public void Deactivate(SquadCA owner) { }
	}

	class UnitsForProtectionAttackState : GroundStateBaseCA, IState
	{
		public const int BackoffTicks = 4;
		int tryAttackTick;

		internal int Backoff = BackoffTicks;
		int tryAttack = 0;

		public void Activate(SquadCA owner)
		{
			tryAttackTick = owner.SquadManager.Info.ProtectionScanRadius;
		}

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			var leader = owner.Units[0].Actor;

			// rescan target to prevent being ambushed and die without fight
			// return to AttackMove state for formation
			var protectionScanRadius = WDist.FromCells(owner.SquadManager.Info.ProtectionScanRadius);
			var closestEnemy = owner.SquadManager.FindClosestEnemy(leader, protectionScanRadius);

			if (closestEnemy == null && !owner.IsTargetValid)
			{
				owner.FuzzyStateMachine.ChangeState(owner, new UnitsForProtectionFleeState(), false);
				return;
			}
			else if (closestEnemy != null && owner.TargetActor != closestEnemy)
			{
				// Refresh tryAttack when target switched
				tryAttack = 0;
				owner.TargetActor = closestEnemy;
			}

			var cannotRetaliate = false;
			var resupplyingUnits = new List<Actor>();
			var followingUnits = new List<Actor>();
			var attackingUnits = new List<Actor>();

			if (!owner.IsTargetVisible)
			{
				if (Backoff < 0)
				{
					owner.FuzzyStateMachine.ChangeState(owner, new UnitsForProtectionFleeState(), false);
					Backoff = BackoffTicks;
					return;
				}

				Backoff--;
			}
			else
			{
				cannotRetaliate = true;

				for (var i = 0; i < owner.Units.Count; i++)
				{
					var u = owner.Units[i];

					// Air units control:
					var ammoPools = u.Actor.TraitsImplementing<AmmoPool>().ToArray();
					if (u.Actor.Info.HasTraitInfo<AircraftInfo>() && ammoPools.Length > 0)
					{
						if (IsAttackingAndTryAttack(u.Actor).TryAttacking)
						{
							cannotRetaliate = false;
							continue;
						}

						if (!ReloadsAutomatically(ammoPools, u.Actor.TraitOrDefault<Rearmable>()))
						{
							if (IsRearming(u.Actor))
								continue;

							if (!HasAmmo(ammoPools))
							{
								resupplyingUnits.Add(u.Actor);
								continue;
							}
						}

						if (CanAttackTarget(u.Actor, owner.TargetActor))
						{
							attackingUnits.Add(u.Actor);
							cannotRetaliate = false;
						}
						else
							followingUnits.Add(u.Actor);
					}

					// Ground/naval units control:
					// Becuase MoveWithinRange can cause huge lag when stuck
					// we only allow free attack behaivour within TryAttackTick
					// then the squad will gather to a certain leader
					else
					{
						var (isFiring, tryAttacking) = IsAttackingAndTryAttack(u.Actor);

						if ((tryAttacking || isFiring) &&
							(u.Actor.CenterPosition - owner.TargetActor.CenterPosition).HorizontalLengthSquared <
							(leader.CenterPosition - owner.TargetActor.CenterPosition).HorizontalLengthSquared)
							leader = u.Actor;

						if (isFiring && tryAttack != 0)
							cannotRetaliate = false;
						else if (CanAttackTarget(u.Actor, owner.TargetActor))
						{
							if (tryAttack > tryAttackTick && tryAttacking)
							{
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
			}

			if (cannotRetaliate)
			{
				owner.FuzzyStateMachine.ChangeState(owner, new UnitsForProtectionFleeState(), false);
				return;
			}

			tryAttack++;

			owner.Bot.QueueOrder(new Order("ReturnToBase", null, false, groupedActors: resupplyingUnits.ToArray()));
			owner.Bot.QueueOrder(new Order("AttackMove", null, Target.FromCell(owner.World, leader.Location), false, groupedActors: followingUnits.ToArray()));
			owner.Bot.QueueOrder(new Order("AttackMove", null, Target.FromActor(owner.TargetActor), false, groupedActors: attackingUnits.ToArray()));
		}

		public void Deactivate(SquadCA owner) { }
	}

	class UnitsForProtectionFleeState : GroundStateBaseCA, IState
	{
		public void Activate(SquadCA owner) { }

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			GoToRandomOwnBuilding(owner);
			owner.FuzzyStateMachine.ChangeState(owner, new UnitsForProtectionIdleState(), true);
		}

		public void Deactivate(SquadCA owner) { }
	}
}
