#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System.Linq;
using OpenRA.Mods.CA.Activities;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;
using OpenRA.Mods.AS.Traits;

namespace OpenRA.Mods.CA.Traits
{
	[Desc("Can be slaved to a spawner.")]
	public class AirstrikeSlaveCAInfo : BaseSpawnerSlaveInfo
	{
		[Desc("Move this close to the spawner, before entering it.")]
		public readonly WDist LandingDistance = new WDist(5 * 1024);

		[Desc("We consider this is close enought to the spawner and enter it, instead of trying to reach 0 distance." +
			"This allows the spawned unit to enter the spawner while the spawner is moving.")]
		public readonly WDist CloseEnoughDistance = new WDist(128);

		public override object Create(ActorInitializer init) { return new AirstrikeSlaveCA(init, this); }
	}

	public class AirstrikeSlaveCA : BaseSpawnerSlave, INotifyIdle, INotifyKilled
	{
		public readonly AirstrikeSlaveCAInfo Info;

		WPos finishEdge;
		WVec spawnOffset;

		AirstrikeMasterCA spawnerMaster;
		bool isBusy;

		public AirstrikeSlaveCA(ActorInitializer init, AirstrikeSlaveCAInfo info)
			: base(info)
		{
			Info = info;
			isBusy = false;
		}

		public void SetSpawnInfo(WPos finishEdge, WVec spawnOffset)
		{
			this.finishEdge = finishEdge;
			this.spawnOffset = spawnOffset;
		}

		public void LeaveMap(Actor self)
		{
			// Hopefully, self will be disposed shortly afterwards by SpawnerSlaveDisposal policy.
			if (Master == null || Master.IsDead)
				return;

			if (isBusy)
			{
				isBusy = false;
				spawnerMaster.MarkSlaveAvailable(Master);
			}

			// Proceed with enter, if already at it.
			if (self.CurrentActivity is ReturnAirstrikeMaster)
				return;

			// Cancel whatever else self was doing and return.
			self.QueueActivity(false, new ReturnAirstrikeMaster(Master, spawnerMaster, finishEdge + spawnOffset));
		}

		public override void LinkMaster(Actor self, Actor master, BaseSpawnerMaster spawnerMaster)
		{
			base.LinkMaster(self, master, spawnerMaster);
			this.spawnerMaster = spawnerMaster as AirstrikeMasterCA;
		}

		public override void Attack(Actor self, Target target)
		{
			base.Attack(self, target);
			if (!isBusy)
			{
				isBusy = true;
				spawnerMaster.MarkSlaveUnavailable(Master);
			}
		}

		void INotifyIdle.TickIdle(Actor self)
		{
			if (!spawnerMaster.SlaveEntries.Select(se => se.Actor).Contains(self))
			{
				if (!isBusy)
					spawnerMaster.MarkSlaveUnavailable(Master);
				self.Dispose();
				return;
			}

			LeaveMap(self);
		}

		void INotifyKilled.Killed(Actor self, AttackInfo e)
		{
			if (Master == null || Master.IsDead)
				return;

			spawnerMaster.OnSlaveKilled(Master, self);

			if (!isBusy)
				spawnerMaster.MarkSlaveUnavailable(Master);
		}
	}
}
