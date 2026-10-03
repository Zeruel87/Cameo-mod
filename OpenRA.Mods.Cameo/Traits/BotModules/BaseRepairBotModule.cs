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

using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	// Merged from OpenRA BuildingRepairBotModule (engine d5d8b2a685) and CA BuildingRepairBotModuleCA
	// (CAmod f31049d2d) under DESIGN §19.3 (one module per decision). AI_MASTER_PLAN RV1.
	//   from CA:     repair on the hit that leaves a building Light or worse (the engine waited for Medium);
	//                a null attacker is ignored instead of crashing.
	//   from OpenRA: the periodic sweep that repairs every damaged building nobody is repairing (it now runs
	//                on the bot tick, so it also reaches buildings that are not under fire, e.g. captured ones).
	//   new:         never a second RepairBuilding for the same building (it is a toggle, see below).
	[TraitLocation(SystemActors.Player)]
	[Desc("The ONE owner of the bot's building-repair decision (DESIGN §19.3): replaces BuildingRepairBotModule +",
		"BuildingRepairBotModuleCA, which classic still runs side by side. RepairBuilding is a TOGGLE, so the module",
		"never orders a building the bot already repairs or has an order in flight for: it reads",
		"RepairableBuilding.Repairers, not RepairActive, which stays false until a queued order resolves and while",
		"the bot cannot pay.")]
	public class BaseRepairBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Repair a building once it is at this damage state or worse.")]
		public readonly DamageState MinimumDamageState = DamageState.Light;

		[Desc("Ticks between sweeps that repair every damaged own building nobody is repairing. -1 disables the sweep.")]
		public readonly int RepairAllInterval = 107;

		[Desc("Ticks a queued repair order counts as in flight. Covers the order latency; after it the order is",
			"assumed dropped (e.g. the repairer limit was full) and the building may be ordered again. Err long:",
			"expiring before the order resolves re-creates the toggle-off this module exists to prevent.")]
		public readonly int PendingOrderTicks = 100;

		public override object Create(ActorInitializer init) { return new BaseRepairBotModule(init.Self, this); }
	}

	public enum BaseRepairDecision { Ignore, Order, AlreadyRepairing, OrderInFlight, RepairerLimit }

	public class BaseRepairBotModule : ConditionalTrait<BaseRepairBotModuleInfo>, IBotTick, IBotRespondToAttack
	{
		readonly World world;
		readonly OpenRA.Player player;
		readonly Dictionary<Actor, int> pendingSince = [];
		int sweepTicks;

		// Telemetry (situation log `own.repair_*`, cumulative). TogglesAvoided counts the hits where master's
		// CA module (damage state rose, `!RepairActive`) would have sent a second order and switched the repair OFF.
		public int RepairOrders { get; private set; }
		public int SweepOrders { get; private set; }
		public int TogglesAvoided { get; private set; }

		public BaseRepairBotModule(Actor self, BaseRepairBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		protected override void TraitEnabled(Actor self)
		{
			sweepTicks = Info.RepairAllInterval;
		}

		/// <summary>The whole policy, free of world state so it can be tested.</summary>
		public static BaseRepairDecision Decide(DamageState state, DamageState minimum, bool isHeal,
			bool alreadyRepairer, bool orderInFlight, int repairers, int maxRepairers)
		{
			if (isHeal || state < minimum || state == DamageState.Dead)
				return BaseRepairDecision.Ignore;

			// A second order would REMOVE the bot from Repairers.
			if (alreadyRepairer)
				return BaseRepairDecision.AlreadyRepairing;

			if (orderInFlight)
				return BaseRepairDecision.OrderInFlight;

			// RepairableBuilding drops the order silently when allies already fill every slot.
			if (repairers >= maxRepairers)
				return BaseRepairDecision.RepairerLimit;

			return BaseRepairDecision.Order;
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (Info.RepairAllInterval < 0 || --sweepTicks > 0)
				return;

			sweepTicks = Info.RepairAllInterval;
			var tick = world.WorldTick;

			// Own buildings only: the bot's knowledge of its own base, no fog involved.
			foreach (var tp in world.ActorsWithTrait<RepairableBuilding>())
			{
				var a = tp.Actor;
				if (a.Owner != player || a.IsDead || !a.IsInWorld || tp.Trait.IsTraitDisabled)
					continue;

				var health = a.TraitOrDefault<IHealth>();
				if (health == null)
					continue;

				if (Consider(bot, a, tp.Trait, health.DamageState, false, tick, "sweep") == BaseRepairDecision.Order)
					SweepOrders++;
			}
		}

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			if (self.IsDead || self.Owner != player)
				return;

			// D2k: buildings placed off concrete take neutral terrain damage; repairing it is waste
			// (the hack both parents carry). No attacker: nothing to attribute, as in Cameo's CA copy.
			if (e.Attacker == null || player.RelationshipWith(e.Attacker.Owner) == PlayerRelationship.Neutral)
				return;

			var rb = self.TraitOrDefault<RepairableBuilding>();
			if (rb == null || rb.IsTraitDisabled)
				return;

			var decision = Consider(bot, self, rb, e.DamageState, e.Damage.Value <= 0, world.WorldTick, "hit");
			if (decision == BaseRepairDecision.Order)
			{
				RepairOrders++;
				AIUtils.BotDebug($"{player} noticed damage {self} {e.PreviousDamageState}->{e.DamageState}, repairing.");
			}
			else if ((decision == BaseRepairDecision.AlreadyRepairing || decision == BaseRepairDecision.OrderInFlight)
				&& !rb.RepairActive && e.PreviousDamageState < e.DamageState)
				TogglesAvoided++;
		}

		BaseRepairDecision Consider(IBot bot, Actor building, RepairableBuilding rb, DamageState state, bool isHeal, int tick, string source)
		{
			var inFlight = pendingSince.TryGetValue(building, out var since) && tick - since < Info.PendingOrderTicks;
			var decision = Decide(state, Info.MinimumDamageState, isHeal, rb.Repairers.Contains(player), inFlight,
				rb.Repairers.Count, rb.Info.RepairBonuses.Length - 1);

			if (decision == BaseRepairDecision.Order)
			{
				PruneExpired(tick);
				pendingSince[building] = tick;
				bot.QueueOrder(new Order("RepairBuilding", player.PlayerActor, Target.FromActor(building), false));

				// Plan step 4 telemetry: a batch shows every repair decision (BotDebug alone only reaches chat).
				Log.Write("debug", $"AI ({player.ClientIndex}): RV1 repair {building.Info.Name} {building.ActorID} at {state} ({source}) tick {tick}");
			}

			return decision;
		}

		void PruneExpired(int tick)
		{
			if (pendingSince.Count == 0)
				return;

			foreach (var a in pendingSince.Where(kv => kv.Key.IsDead || tick - kv.Value >= Info.PendingOrderTicks)
				.Select(kv => kv.Key).ToList())
				pendingSince.Remove(a);
		}
	}
}
