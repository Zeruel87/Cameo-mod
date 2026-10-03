#region Copyright & License Information
/*
 * Cameo mod
 */
#endregion

using System.Collections.Generic;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Place on the Player actor. Dynamically caps bot unit production by sharing a single global",
		"combat-unit budget across all living bots: each bot's cap = budget / (living bots). As opponents",
		"are eliminated the survivors are allowed larger armies, so the TOTAL unit count across the AI stays",
		"roughly bounded - which keeps the single-threaded simulation tick (and late-game FPS) under control.",
		"Implemented via IBotRequestPauseUnitProduction, so it only pauses the unit builders;",
		"base/structure construction is unaffected. Harmless on non-bot players (never queried).")]
	public class BotGlobalUnitBudgetInfo : ConditionalTraitInfo
	{
		[Desc("Total combat-unit budget shared across all living bots. 0 or less disables the cap.")]
		public readonly int GlobalUnitBudget = 0;

		[Desc("Upper clamp on a single bot's share of the budget (0 = no clamp).",
			"Stops a 1-or-2-bots-left endgame from letting one bot consume the whole budget and tank FPS.")]
		public readonly int MaxUnitsPerBot = 0;

		[Desc("Lower clamp on a single bot's share of the budget (0 = no floor).")]
		public readonly int MinUnitsPerBot = 0;

		[Desc("How often (in ticks) to recompute the cap. Larger = cheaper, slightly less responsive.")]
		public readonly int RecalculationInterval = 25;

		[Desc("Exclude resource collectors (any actor with the Harvester trait) from the per-bot count,",
			"so lowering the budget never starves the bot economy. Faction-agnostic across all rulesets.")]
		public readonly bool IgnoreHarvesters = true;

		[Desc("Log per-bot budget state (living bots, cap, current unit count, paused) to the",
			"debug log on each recompute. For tuning/verification only; leave off in normal play.")]
		public readonly bool Debug = false;

		[ActorReference]
		[Desc("Additional actor types excluded from the per-bot unit count by name (e.g. MCVs).",
			"Harvesters are already covered by IgnoreHarvesters.")]
		public readonly HashSet<string> IgnoredActorTypes = new();

		public override object Create(ActorInitializer init) => new BotGlobalUnitBudget(init.Self, this);
	}

	public class BotGlobalUnitBudget : ConditionalTrait<BotGlobalUnitBudgetInfo>, IBotRequestPauseUnitProduction
	{
		readonly World world;
		readonly OpenRA.Player player;

		int lastTick = -1;
		bool paused;

		public BotGlobalUnitBudget(Actor self, BotGlobalUnitBudgetInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		bool IBotRequestPauseUnitProduction.PauseUnitProduction
		{
			get
			{
				if (IsTraitDisabled || Info.GlobalUnitBudget <= 0)
					return false;

				// Throttle the recompute. Only ever queried on the host (bots run host-side), and the
				// inputs are synced state, so the decision is deterministic for the orders it gates.
				var tick = world.WorldTick;
				if (lastTick < 0 || tick - lastTick >= Info.RecalculationInterval)
				{
					lastTick = tick;
					paused = ComputePaused();
				}

				return paused;
			}
		}

		/// <summary>
		/// This bot's share of the combat-unit budget right now (budget / living bots, clamped), or -1 when the budget
		/// is off. A physical cap for the scale targets (DESIGN 19.10): an army or aircraft target never exceeds it.
		/// </summary>
		public int CurrentShare()
		{
			if (IsTraitDisabled || Info.GlobalUnitBudget <= 0)
				return -1;

			var livingBots = 0;
			foreach (var p in world.Players)
				if (p.IsBot && p.WinState == WinState.Undefined)
					livingBots++;

			if (livingBots < 1)
				livingBots = 1;

			var cap = Info.GlobalUnitBudget / livingBots;
			if (Info.MaxUnitsPerBot > 0 && cap > Info.MaxUnitsPerBot)
				cap = Info.MaxUnitsPerBot;
			if (cap < Info.MinUnitsPerBot)
				cap = Info.MinUnitsPerBot;

			return cap;
		}

		bool ComputePaused()
		{
			var livingBots = 0;
			foreach (var p in world.Players)
				if (p.IsBot && p.WinState == WinState.Undefined)
					livingBots++;

			if (livingBots < 1)
				livingBots = 1;

			var cap = CurrentShare();

			// Count this bot's live mobile units (IPositionable excludes buildings) - same notion of
			// "army" the unit builders use. Stop as soon as we reach the cap; no need to count further.
			var count = 0;
			var ignoreNames = Info.IgnoredActorTypes.Count > 0;
			foreach (var a in world.ActorsHavingTrait<IPositionable>())
			{
				if (a.Owner != player || a.IsDead)
					continue;

				// Resource collectors don't count against the combat budget, so a lower budget
				// never starves the economy.
				if (Info.IgnoreHarvesters && a.Info.HasTraitInfo<HarvesterInfo>())
					continue;

				if (ignoreNames && Info.IgnoredActorTypes.Contains(a.Info.Name))
					continue;

				// When not logging, stop as soon as we reach the cap - no need to count further.
				// With Debug on we count every unit so the log shows the true army size vs the cap.
				count++;
				if (!Info.Debug && count >= cap)
					return true;
			}

			if (Info.Debug)
				Log.Write("debug", $"BotBudget {player.InternalName}: livingBots={livingBots} " +
					$"cap={cap} units={count} paused={count >= cap}");

			return count >= cap;
		}
	}
}
