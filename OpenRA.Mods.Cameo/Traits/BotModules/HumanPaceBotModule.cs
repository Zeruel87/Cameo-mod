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
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Human-likeness H1: a shared action + attention budget so a bot cannot spend",
		"superhuman bursts and decision points take turns. Consumers: ModularBot's",
		"order drain (TryConsumeActions) and SquadManagerBotModuleCA's squad updates",
		"(TryConsumeAttention).")]
	public class HumanPaceBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Orders admitted per sliding window (the sustained APM cap). 0 = unlimited.",
			"The default 6 per 25 ticks is 360 orders per game minute. Cameo's bots run UNCAPPED (0) by",
			"maintainer ruling 2026-09-28 (DESIGN.md §19.1): the cap only made the bot weaker.")]
		public readonly int ActionsPerWindow = 6;

		[Desc("Window length in ticks for the sustained action budget (25 ticks = 1s at default timestep).")]
		public readonly int WindowTicks = 25;

		[Desc("Orders admitted in a single tick regardless of window headroom (the burst cap). 0 = unlimited.")]
		public readonly int MaxActionsPerTick = 3;

		[Desc("Distinct decision points (squads, managers) that may act in one tick. 0 = unlimited.",
			"Callers past the cap must defer — the deferral is the stagger that keeps group",
			"orders landing one after another instead of simultaneously.")]
		public readonly int AttentionSlotsPerTick = 2;

		public override object Create(ActorInitializer init) { return new HumanPaceBotModule(init.Self, this); }
	}

	public class HumanPaceBotModule : ConditionalTrait<HumanPaceBotModuleInfo>, IBotActionBudget
	{
		readonly World world;

		// Sliding window as a per-tick ledger; expired entries are dropped lazily on the
		// next query, so the module needs no IBotTick and works at any point in the
		// tick order — the reset cannot be missed by ticking too early or too late.
		readonly Queue<KeyValuePair<int, int>> window = new();
		int windowTotal;
		int actionsThisTick;
		int burstTick = -1;
		readonly HashSet<object> attention = [];
		int attentionTick = -1;

		public HumanPaceBotModule(Actor self, HumanPaceBotModuleInfo info)
			: base(info)
		{
			world = self.World;
		}

		public int ActionsInWindow => windowTotal;
		public int ActionsThisTick => burstTick == world.WorldTick ? actionsThisTick : 0;
		public int AttentionInUse => attentionTick == world.WorldTick ? attention.Count : 0;

		public bool TryConsumeActions(int count = 1)
		{
			if (IsTraitDisabled)
				return true;
			if (count <= 0)
				return true;

			var tick = world.WorldTick;
			ExpireWindow(tick);

			if (Info.MaxActionsPerTick > 0)
			{
				if (burstTick != tick)
				{
					burstTick = tick;
					actionsThisTick = 0;
				}

				if (actionsThisTick + count > Info.MaxActionsPerTick)
					return false;
			}

			if (Info.ActionsPerWindow > 0 && windowTotal + count > Info.ActionsPerWindow)
				return false;

			actionsThisTick += count;
			windowTotal += count;
			window.Enqueue(new KeyValuePair<int, int>(tick, count));
			return true;
		}

		public bool TryConsumeAttention(object decisionPoint)
		{
			if (IsTraitDisabled)
				return true;
			if (decisionPoint == null)
				return true;

			var tick = world.WorldTick;
			if (attentionTick != tick)
			{
				attentionTick = tick;
				attention.Clear();
			}

			if (attention.Contains(decisionPoint))
				return true;

			if (Info.AttentionSlotsPerTick <= 0 || attention.Count < Info.AttentionSlotsPerTick)
			{
				attention.Add(decisionPoint);
				return true;
			}

			return false;
		}

		void ExpireWindow(int tick)
		{
			if (Info.ActionsPerWindow <= 0)
			{
				if (window.Count > 0)
				{
					window.Clear();
					windowTotal = 0;
				}

				return;
			}

			var cutoff = tick - Math.Max(1, Info.WindowTicks);
			while (window.Count > 0 && window.Peek().Key <= cutoff)
				windowTotal -= window.Dequeue().Value;
		}
	}
}
