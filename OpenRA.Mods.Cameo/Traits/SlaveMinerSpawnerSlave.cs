#region Copyright & License Information
/*
 * Copyright 2015- OpenRA.Mods.AS Developers (see AUTHORS)
 * This file is a part of a third-party plugin for OpenRA, which is
 * free software. It is made available to you under the terms of the
 * GNU General Public License as published by the Free Software
 * Foundation. For more information, see COPYING.
 */
#endregion

using System;
using System.Linq;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.AS.Traits;
using OpenRA.Traits;
using System.Collections.Generic;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Can be slaved to a drone spawner.")]
	public class SlaveMinerSpawnerSlaveInfo : BaseSpawnerSlaveInfo
	{
		[Desc("Aircraft slaves outside of this range from master while moving will be call back")]
		public readonly int MovingCallBackCellDistance = 2;

		[Desc("Slaves will follow master instead of attack while target outside of this range")]
		public readonly WDist AttackCallBackDistance = WDist.FromCells(10);

		[GrantedConditionReference]
		[Desc("The condition to grant to slaves when freed.")]
		public readonly string FreedCondition = null;

		[Desc("Player relationships the attacking player needs to free the slave.")]
		public readonly PlayerRelationship FreeingRelationships = PlayerRelationship.Neutral | PlayerRelationship.Enemy;

		[Desc("Sound to play when the slave is freed.")]
		public readonly string FreedSound = null;

		public override object Create(ActorInitializer init) { return new SlaveMinerSpawnerSlave(this); }
	}

	public class SlaveMinerSpawnerSlave : BaseSpawnerSlave, INotifyHarvestAction, INotifyDockClientMoving, INotifyAddedToWorld
	{
		public IMove[] Moves { get; private set; }
		public IPositionable Positionable { get; private set; }
		public bool IsAircraft;
		public readonly SlaveMinerSpawnerSlaveInfo Info;
		Actor currentActor;
		Actor masterActor;
		public readonly Predicate<Actor> InvalidActor;
		CPos harvestedField;
		IDockHost masterDock;
		DockClientManager dockClient;

		public bool IsMoving(CPos gatherlocation)
		{
			if (IsAircraft)
			{
				if (!InvalidActor(currentActor) && !InvalidActor(masterActor) &&
					(currentActor.Location - gatherlocation).LengthSquared > Info.MovingCallBackCellDistance * Info.MovingCallBackCellDistance)
					return false;

				return true;
			}

			var groundmove = Array.Exists(Moves, m => m.IsTraitEnabled() && (m.CurrentMovementTypes.HasFlag(MovementType.Horizontal) || m.CurrentMovementTypes.HasFlag(MovementType.Vertical)));
			return groundmove;
		}

		public SlaveMinerSpawnerSlave(SlaveMinerSpawnerSlaveInfo info)
			: base(info)
		{
			InvalidActor = a => a == null || a.IsDead || !a.IsInWorld;
			Info = info;
		}

		protected override void Created(Actor self)
		{
			base.Created(self);

			currentActor = self;

			Moves = self.TraitsImplementing<IMove>().ToArray();

			var positionables = self.TraitsImplementing<IPositionable>();
			if (positionables.Count() != 1)
				throw new InvalidOperationException($"Actor {self} has multiple (or no) traits implementing IPositionable.");

			Positionable = positionables.First();

			IsAircraft = self.Info.HasTraitInfo<AircraftInfo>();

			dockClient = self.Trait<DockClientManager>();
		}

		public override void LinkMaster(Actor self, Actor master, BaseSpawnerMaster spawnerMaster)
		{
			base.LinkMaster(self, master, spawnerMaster);
			masterActor = master;
		}
		void INotifyAddedToWorld.AddedToWorld(Actor self)
		{
			UpdateMasterDock(self);
		}

		void UpdateMasterDock(Actor self)
		{
			if (masterActor == null)
			{
				masterDock = null;
				return;
			}
			var dock = dockClient.AvailableDockHosts(masterActor, default, true).ClosestDock(self, dockClient);
			if (dock.HasValue)
			{
				masterDock = dock.Value.Trait;
				dockClient.ReserveHost(masterActor, masterDock);
			}
		}

		public void UpdateOnTransform(Actor self)
		{
			UpdateMasterDock(self);
			self.QueueActivity(false, new FindAndDeliverResources(self));
		}

		public void Move(Actor self, CPos location)
		{
			// And tell attack bases to stop attacking.
			if (Moves.Length == 0)
				return;

			foreach (var mv in Moves)
				if (mv.IsTraitEnabled())
				{
					if (IsAircraft)
						self.QueueActivity(mv.MoveTo(location, 0));
					else
						self.QueueActivity(mv.MoveTo(location, 2));
					break;
				}
		}

		void INotifyDockClientMoving.MovingToDock(Actor self, Actor hostActor, IDockHost host, bool forceEnter)
		{
			if (DeliverToMaster(self))
				return;
			else if (hostActor == null)
			{
				harvestedField = self.World.Map.CellContaining(self.CenterPosition);
				self.QueueActivity(new FindAndDeliverResources(self, harvestedField));
			}
			else
				self.QueueActivity(new MoveToDock(self, hostActor, host, true));
		}

		void INotifyDockClientMoving.MovementCancelled(Actor self) { Reset(self); }

		void INotifyHarvestAction.MovingToResources(Actor self, CPos targetCell) { Reset(self); }

		void INotifyHarvestAction.MovementCancelled(Actor self) { Reset(self); }

		void INotifyHarvestAction.Harvested(Actor self, string resourceType) { }

		void Reset(Actor self)
		{
			DeliverToMaster(self);
		}

		bool DeliverToMaster(Actor self)
		{
			if (masterActor != null && masterDock != null)
			{
				self.QueueActivity(new MoveToDock(self, masterActor, masterDock, true));
				self.QueueActivity(new FindAndDeliverResources(self));
				return true;
			}
			return false;
		}

		public override void OnMasterKilled(Actor self, Actor attacker, SpawnerSlaveDisposal disposal)
		{
			// Grant MasterDead condition.
			if (!string.IsNullOrEmpty(Info.MasterDeadCondition))
				self.GrantCondition(Info.MasterDeadCondition);

			var killer = attacker ?? self;

			switch (disposal)
			{
				case SpawnerSlaveDisposal.KillSlaves:
					self.Kill(killer, Info.DamageTypes);
					break;
				case SpawnerSlaveDisposal.GiveSlavesToAttacker:
					masterActor = null;
					self.CancelActivity();
					self.ChangeOwner(killer.Owner);
					if (!string.IsNullOrEmpty(Info.FreedCondition) && Info.FreeingRelationships.HasRelationship(killer.Owner.RelationshipWith(self.Owner)))
					{
						self.GrantCondition(Info.FreedCondition);
						Game.Sound.Play(SoundType.World, Info.FreedSound, self.CenterPosition);
					}
					break;
				case SpawnerSlaveDisposal.DoNothing:
					masterActor = null;
					break;
				default:
					break;
			}
		}

		public override void OnMasterOwnerChanged(Actor self, OpenRA.Player oldOwner, OpenRA.Player newOwner, SpawnerSlaveDisposal disposal)
		{
			switch (disposal)
			{
				case SpawnerSlaveDisposal.KillSlaves:
					self.Kill(self, Info.DamageTypes);
					break;
				case SpawnerSlaveDisposal.GiveSlavesToAttacker:
					self.ChangeOwner(newOwner);
					UpdateOnTransform(self);
					break;
				case SpawnerSlaveDisposal.DoNothing:
					masterActor = null;
					break;
				default:
					break;
			}
		}

		public override void OnOwnerChanged(Actor self, OpenRA.Player oldOwner, OpenRA.Player newOwner)
		{
			if (Master == null || !Master.IsDead)
			{
				masterActor = null;
				return;
			}

			// This function got triggered because the master got mind controlled and
			// thus triggered slave.ChangeOwner().
			// In this case, do nothing.
			if (Master.Owner == newOwner)
				return;

			if (Info.AllowOwnerChange)
			{
				masterActor = null;
				return;
			}

			self.Kill(self, Info.DamageTypes);
		}
	}
}
