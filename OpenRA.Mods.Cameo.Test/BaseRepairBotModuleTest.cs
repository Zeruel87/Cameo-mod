#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Mods.Cameo.Traits.BotModules;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	// RV1 / DESIGN §19.3: the merged repair owner never sends the second RepairBuilding that toggles a repair off.
	[TestFixture]
	public sealed class BaseRepairBotModuleTest
	{
		const int MaxRepairers = 8;

		static BaseRepairDecision Decide(DamageState state, bool heal = false, bool repairer = false,
			bool inFlight = false, int repairers = 0)
		{
			return BaseRepairBotModule.Decide(state, DamageState.Light, heal, repairer, inFlight, repairers, MaxRepairers);
		}

		[Test]
		public void OrdersOnceTheBuildingIsLightOrWorse()
		{
			Assert.That(Decide(DamageState.Undamaged), Is.EqualTo(BaseRepairDecision.Ignore));
			Assert.That(Decide(DamageState.Light), Is.EqualTo(BaseRepairDecision.Order));
			Assert.That(Decide(DamageState.Critical), Is.EqualTo(BaseRepairDecision.Order));
			Assert.That(Decide(DamageState.Dead), Is.EqualTo(BaseRepairDecision.Ignore));
		}

		[Test]
		public void RepairHealingIsNotAnAttack()
		{
			// RepairableBuilding heals through InflictDamage(self, negative), which reaches RespondToAttack.
			Assert.That(Decide(DamageState.Medium, heal: true), Is.EqualTo(BaseRepairDecision.Ignore));
		}

		[Test]
		public void NeverTogglesOffARepairTheBotAlreadyRuns()
		{
			// The double-owner case (OpenRA + CA answering one hit), and the broke case: the bot stays in
			// Repairers while RepairActive is false, which the old `!RepairActive` test read as "not repairing".
			Assert.That(Decide(DamageState.Medium, repairer: true), Is.EqualTo(BaseRepairDecision.AlreadyRepairing));
		}

		[Test]
		public void NeverSendsASecondOrderWhileTheFirstIsInFlight()
		{
			// Undamaged->Light queues an order; Light->Medium arrives before it resolves.
			Assert.That(Decide(DamageState.Medium, inFlight: true), Is.EqualTo(BaseRepairDecision.OrderInFlight));
		}

		[Test]
		public void SkipsWhenAlliesFillEveryRepairSlot()
		{
			Assert.That(Decide(DamageState.Heavy, repairers: MaxRepairers), Is.EqualTo(BaseRepairDecision.RepairerLimit));
			Assert.That(Decide(DamageState.Heavy, repairers: MaxRepairers - 1), Is.EqualTo(BaseRepairDecision.Order));
		}

		[Test]
		public void SituationLogCarriesTheRepairCounters()
		{
			var situation = new BotSituation
			{
				Tick = 1500,
				Personality = "",
				Enemies = new Dictionary<OpenRA.Player, EnemyProfile>(),
				Demand = new CounterDemand(),
				RepairOrders = 7,
				RepairSweepOrders = 3,
				RepairTogglesAvoided = 2
			};

			var b = new StringBuilder();
			AiSituationLogWriter.AppendSituation(b, "game", "", "map", "Multi0", "td_gdi", "medium", "rush", situation);
			using var doc = JsonDocument.Parse(b.ToString());
			var own = doc.RootElement.GetProperty("own");
			Assert.That(own.GetProperty("repair_orders").GetInt32(), Is.EqualTo(7));
			Assert.That(own.GetProperty("repair_sweep_orders").GetInt32(), Is.EqualTo(3));
			Assert.That(own.GetProperty("repair_toggles_avoided").GetInt32(), Is.EqualTo(2));
		}
	}
}
