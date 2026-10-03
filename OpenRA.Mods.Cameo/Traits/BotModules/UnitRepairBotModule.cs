#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System;
using System.Collections.Frozen;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	// CN2 (AI_MASTER_PLAN §3, crystallized-nexus 30cf70a): port of CNRepairManagerBotModule. Sends damaged idle
	// base units to allied repair facilities - a depot (Repairable), a repair-near building (RepairableNear), or
	// within aura range of a mobile repairer (MobileRepairActorTypes). Building repair is owned by
	// BaseRepairBotModule (§19.3); this module only ever orders units.
	//
	// Cameo changes vs the donor:
	//  - Unit ownership is the §19.6 lease contract, not the CN squad manager: a unit ordered to a facility is
	//    claimed for the trip (BotLeasePurpose.Repair) so nothing re-drafts it mid-walk; claims renew every scan
	//    and release when the unit is healed, dead or gone. Without a registry (classic) nothing is claimed and
	//    every unit behaves as the donor's did.
	//  - The RepairableInBarracks path is dropped: that trait is CN-only and no Cameo pack declares it. If a pack
	//    wants barracks healing, vendor the trait and restore the path.
	//  - Candidates iterate in ActorID order (the donor's HashSet order is not a contract).
	//  - CNBotPerf instrumentation dropped.
	[TraitLocation(SystemActors.Player)]
	[Desc("Sends damaged idle base units to allied repair facilities.")]
	public class UnitRepairBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Delay in ticks between repair scans.")]
		public readonly int RepairScanInterval = 75;

		[Desc("Minimum damage state required before a unit is sent to repair.")]
		public readonly DamageState MinimumDamageState = DamageState.Light;

		[Desc("Maximum number of repair orders to issue on each scan.")]
		public readonly int MaxAssignmentsPerScan = 3;

		[Desc("Mobile repair actor types that should repair damaged idle units inside the base area.")]
		public readonly FrozenSet<string> MobileRepairActorTypes = FrozenSet<string>.Empty;

		[Desc("Only use mobile repairers when the damaged unit is within this many cells of one.")]
		public readonly int MobileRepairSearchRadius = 10;

		public override object Create(ActorInitializer init) { return new UnitRepairBotModule(init.Self, this); }
	}

	public class UnitRepairBotModule : ConditionalTrait<UnitRepairBotModuleInfo>, IBotTick, IBotNotifyIdleBaseUnits
	{
		const string LeaseOwner = nameof(UnitRepairBotModule);

		readonly List<UnitWposWrapper> idleBaseUnits = [];
		readonly HashSet<Actor> heldUnits = [];
		int repairScanTicks;
		readonly World world;

		public UnitRepairBotModule(Actor self, UnitRepairBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			repairScanTicks = world.LocalRandom.Next(RepairScanInterval);
		}

		void IBotNotifyIdleBaseUnits.UpdatedIdleBaseUnits(List<UnitWposWrapper> idleUnits)
		{
			idleBaseUnits.Clear();
			idleBaseUnits.AddRange(idleUnits);
		}

		protected override void TraitDisabled(Actor self)
		{
			var leases = BotUnitLeases.Of(self.Owner);
			foreach (var a in heldUnits)
				leases?.Release(a, LeaseOwner);

			heldUnits.Clear();
			idleBaseUnits.Clear();
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (--repairScanTicks > 0)
				return;

			repairScanTicks = RepairScanInterval;
			var leases = BotUnitLeases.Of(bot.Player);

			// Reconcile held units first: release the healed and the gone, renew the rest so the lease
			// (not the unit's idle flag) is what keeps squads away while the trip is in progress.
			var prune = new List<Actor>();
			foreach (var a in heldUnits)
			{
				// A held unit can be destroyed between scans; TraitOrDefault on it throws, so the
				// alive/in-world check must come before any trait access.
				if (a.IsDead || !a.IsInWorld || a.Owner != bot.Player)
				{
					prune.Add(a);
					continue;
				}

				var health = a.TraitOrDefault<IHealth>();
				if (health == null || health.DamageState < Info.MinimumDamageState || health.DamageState >= DamageState.Dead ||
					leases == null || !leases.TryClaim(a, LeaseOwner, BotLeasePurpose.Repair, LeaseHeartbeatTicks()))
					prune.Add(a);
			}

			foreach (var a in prune)
			{
				heldUnits.Remove(a);
				leases?.Release(a, LeaseOwner);
			}

			var assignments = 0;
			var repairCandidates = new HashSet<Actor>(idleBaseUnits.Select(u => u.Actor).Where(a => a != null));
			foreach (var actor in world.ActorsHavingTrait<Repairable>())
				if (actor.Owner == bot.Player && !actor.IsDead && actor.IsInWorld && actor.IsIdle)
					repairCandidates.Add(actor);

			foreach (var actor in repairCandidates.OrderBy(a => a.ActorID))
			{
				if (assignments >= Info.MaxAssignmentsPerScan)
					break;

				if (actor.Owner != bot.Player || actor.IsDead || !actor.IsInWorld || !actor.IsIdle)
					continue;

				if (BotUnitLeases.IsClaimedByOther(leases, actor, LeaseOwner))
					continue;

				var health = actor.TraitOrDefault<IHealth>();
				if (health == null || health.DamageState < Info.MinimumDamageState || health.DamageState >= DamageState.Dead)
					continue;

				var mobileRepair = TryAssignMobileRepair(bot, actor);
				if (mobileRepair == MobileRepairResult.Ordered)
				{
					assignments++;
					Claim(bot, leases, actor);
					continue;
				}

				// Already standing at its repairer and being healed: nothing to order, and nothing to send
				// it away for either. Falling through here is what had a unit drive off to a service depot
				// while the aura beside it was already repairing it - and it does not spend an assignment
				// slot, since no order was issued.
				if (mobileRepair == MobileRepairResult.AlreadyServiced)
					continue;

				var repairableNear = actor.TraitOrDefault<RepairableNear>();
				if (repairableNear != null)
				{
					var repairBuilding = repairableNear.FindRepairBuilding(actor);
					if (repairBuilding != null)
					{
						bot.QueueOrder(new Order("RepairNear", actor, Target.FromActor(repairBuilding), false));
						assignments++;
						Claim(bot, leases, actor);
						continue;
					}
				}

				var repairable = actor.TraitOrDefault<Repairable>();
				if (repairable != null)
				{
					var repairBuilding = repairable.FindRepairBuilding(actor);
					if (repairBuilding != null)
					{
						bot.QueueOrder(new Order("Repair", actor, Target.FromActor(repairBuilding), false));
						assignments++;
						Claim(bot, leases, actor);
					}
				}
			}
		}

		void Claim(IBot bot, IBotUnitLeases leases, Actor actor)
		{
			if (leases != null && leases.TryClaim(actor, LeaseOwner, BotLeasePurpose.Repair, LeaseHeartbeatTicks()))
				heldUnits.Add(actor);
		}

		/// <summary>
		/// What became of a mobile-repair attempt. Three outcomes, because two of them used to share the
		/// same "false" and the caller could not tell them apart: a unit already parked at its repairer,
		/// being healed by its aura, was read as "mobile repair not possible" and sent off to a distant
		/// service depot on the very next scan.
		/// </summary>
		enum MobileRepairResult { NotApplicable, AlreadyServiced, Ordered }

		MobileRepairResult TryAssignMobileRepair(IBot bot, Actor actor)
		{
			if (Info.MobileRepairActorTypes.Count == 0 || actor.Info.TraitInfoOrDefault<AircraftInfo>() != null)
				return MobileRepairResult.NotApplicable;

			var bestRepairer = idleBaseUnits
				.Where(u => u.Actor != null)
				.Select(u => u.Actor)
				.Where(a =>
					a != actor &&
					a.Owner == actor.Owner &&
					!a.IsDead &&
					a.IsInWorld &&
					a.IsIdle &&
					Info.MobileRepairActorTypes.Contains(a.Info.Name))

				// Ranked in world space, not in cells. CPos distance on a RectangularIsometric map is not
				// the distance on the ground: the same raw cell delta is a different real separation along
				// one axis than along the other, so the nearest repairer by this measure was not always the
				// nearest one, and the radius below let one damaged unit in and kept an equally close one
				// out depending on which way it happened to lie.
				.OrderBy(a => (a.CenterPosition - actor.CenterPosition).HorizontalLengthSquared)
				.FirstOrDefault();

			if (bestRepairer == null)
				return MobileRepairResult.NotApplicable;

			var maxRange = WDist.FromCells(Info.MobileRepairSearchRadius);
			var distanceSq = (bestRepairer.CenterPosition - actor.CenterPosition).HorizontalLengthSquared;
			if (distanceSq > (long)maxRange.Length * maxRange.Length)
				return MobileRepairResult.NotApplicable;

			// Already standing at the repairer: the unit is being serviced (or the repairer can't help
			// it), so there is nothing to order. Returning true here would burn one of the scan's
			// MaxAssignmentsPerScan slots on a no-op every single scan, starving units that do need
			// a repair order.
			// In cells, like the radius above. This read "<= 2" while distanceSq was a raw cell delta -
			// about one and a half cells - and measuring in world units now makes 2 a couple of pixels,
			// which no unit is ever inside. The check would have been dead.
			var atRepairer = WDist.FromCells(2);
			if (distanceSq <= (long)atRepairer.Length * atRepairer.Length)
				return MobileRepairResult.AlreadyServiced;

			bot.QueueOrder(new Order("Move", actor, Target.FromCell(actor.World, bestRepairer.Location), false));
			return MobileRepairResult.Ordered;
		}

		int RepairScanInterval => Info.RepairScanInterval > 0 ? Info.RepairScanInterval : 1;
		int LeaseHeartbeatTicks() => Math.Max(200, RepairScanInterval * 4);
	}
}
