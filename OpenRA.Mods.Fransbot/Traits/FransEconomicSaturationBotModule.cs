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
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Linq;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	public enum FransEconomicState
	{
		Struggling,
		Growing,
		Prosperous,
		Surplus
	}

	public interface IFransEconomicSaturationService
	{
		FransEconomicState State { get; }
		bool IsStruggling { get; }
		bool IsProsperousOrBetter { get; }
		bool IsSurplus { get; }
		bool RequestsSupplyCash { get; }
		int AvailableQueueCount { get; }
		int BusyQueueCount { get; }
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Shared Fransbot economic-state detector. Economic state is defined only by real production throughput and cash sustainability, not by how many ore mines, gem fields, refineries or Oil Derricks are owned. " +
		"Struggling cannot sustain two queues near MinimumCash; Growing can operate about three queues; Prosperous can sustain three/four queues without losing its bank; Surplus can keep every existing relevant queue working without cash collapse, so producer throughput becomes the bottleneck.")]
	public class FransEconomicSaturationBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Military production queue categories included in the economic throughput model. Building is measured separately so the state counts queue categories, not individual producer structures.")]
		public readonly ImmutableArray<string> ProductionQueueCategories =
			["Infantry", "Vehicle", "Aircraft", "Plane", "Ship"];

		[Desc("Shared building-production queue category included in the same throughput model.")]
		public readonly string BuildingQueueCategory = "Building";

		[Desc("The shared MinimumCash floor. Repeatedly operating two or more queues at/below this value means Struggling.")]
		public readonly int MinimumCash = 500;

		[Desc("Cash margin above MinimumCash that must be held briefly before Struggling is considered stabilized enough to return to Growing.")]
		public readonly int StrugglingRecoveryMargin = 1000;

		[Desc("Minimum simultaneous busy queue categories used to prove Struggling pressure.")]
		public readonly int StrugglingBusyQueues = 2;

		[Desc("World ticks of repeated two-queue MinimumCash pressure before Struggling activates.")]
		public readonly int StrugglingSustainTicks = 400;

		[Desc("World ticks the recovered bank must remain above MinimumCash + recovery margin before Struggling returns to Growing.")]
		public readonly int StrugglingRecoveryTicks = 250;

		[Desc("Minimum busy queue categories used by the Growing/Prosperous throughput model.")]
		public readonly int GrowingBusyQueues = 3;

		[Desc("Minimum busy queue categories for a normal Prosperous proof. Three is valid when the bank is stable; four is stronger evidence.")]
		public readonly int ProsperousBusyQueues = 3;

		[Desc("Preferred strong Prosperous evidence: this many queues may be observed busy during the proof window.")]
		public readonly int ProsperousPreferredBusyQueues = 4;

		[Desc("World ticks of sustained three/four-queue operation with a stable bank before Growing becomes Prosperous.")]
		public readonly int ProsperousSustainTicks = 500;

		[Desc("Minimum number of existing relevant queue categories required before Surplus can be proven. Prevents an early three-queue economy from declaring Surplus before mature production exists.")]
		public readonly int SurplusMinimumAvailableQueues = 4;

		[Desc("World ticks that all existing relevant queues must remain substantially occupied without cash collapse before Prosperous becomes Surplus.")]
		public readonly int SurplusSustainTicks = 300;

		[Desc("World ticks of renewed MinimumCash pressure before true Surplus is released.")]
		public readonly int SurplusReleaseSustainTicks = 500;

		[Desc("Maximum tolerated net bank drawdown during a Prosperous/Surplus proof window. This absorbs normal purchase timing without treating a steadily shrinking economy as sustainable.")]
		public readonly int StableCashDrawdownTolerance = 500;

		[Desc("Percentage of samples in a proof window that must meet the relevant busy-queue condition.")]
		public readonly int BusySamplePercent = 70;

		[Desc("Percentage of Surplus proof samples in which every currently available relevant queue category must be busy.")]
		public readonly int SurplusAllBusySamplePercent = 60;

		[Desc("World ticks between economic-state evaluations.")]
		public readonly int ScanInterval = 50;

		[Desc("Conditions granted to the player for YAML/rules integration and diagnostics.")]
		public readonly string StrugglingCondition = "frans-economic-struggling";
		public readonly string GrowingCondition = "frans-economic-growing";
		public readonly string ProsperousCondition = "frans-economic-prosperous";
		public readonly string SurplusCondition = "frans-economic-surplus";

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			if (MinimumCash < 0 || StrugglingRecoveryMargin < 0 || StrugglingBusyQueues < 2 || StrugglingSustainTicks <= 0 || StrugglingRecoveryTicks <= 0)
				throw new YamlException("Economic Struggling throughput settings are invalid.");
			if (GrowingBusyQueues < StrugglingBusyQueues || ProsperousBusyQueues < GrowingBusyQueues ||
				ProsperousPreferredBusyQueues < ProsperousBusyQueues || ProsperousSustainTicks <= 0)
				throw new YamlException("Economic Growing/Prosperous throughput settings are invalid.");
			if (SurplusMinimumAvailableQueues < ProsperousBusyQueues || SurplusSustainTicks <= 0 || SurplusReleaseSustainTicks <= 0 || StableCashDrawdownTolerance < 0)
				throw new YamlException("Economic Surplus throughput settings are invalid.");
			if (BusySamplePercent <= 0 || BusySamplePercent > 100 || SurplusAllBusySamplePercent <= 0 || SurplusAllBusySamplePercent > 100 ||
				ScanInterval <= 0 || string.IsNullOrWhiteSpace(BuildingQueueCategory) ||
				string.IsNullOrWhiteSpace(StrugglingCondition) || string.IsNullOrWhiteSpace(GrowingCondition) ||
				string.IsNullOrWhiteSpace(ProsperousCondition) || string.IsNullOrWhiteSpace(SurplusCondition))
				throw new YamlException("Economic state scan/condition settings are invalid.");
		}

		public override object Create(ActorInitializer init) { return new FransEconomicSaturationBotModule(init.Self, this); }
	}

	public class FransEconomicSaturationBotModule : ConditionalTrait<FransEconomicSaturationBotModuleInfo>,
		IBotTick, IFransEconomicSaturationService
	{
		readonly record struct EconomySample(int WorldTick, int Cash, int AvailableQueues, int BusyQueues);

		readonly World world;
		readonly Player player;
		readonly Actor playerActor;
		readonly List<EconomySample> samples = [];
		PlayerResources playerResources;
		FransEconomicState state = FransEconomicState.Growing;
		int scanTicks;
		int stateConditionToken = Actor.InvalidConditionToken;
		int nextProbeLogTick;

		public FransEconomicSaturationBotModule(Actor self, FransEconomicSaturationBotModuleInfo info) : base(info)
		{
			world = self.World;
			player = self.Owner;
			playerActor = self;
		}

		public FransEconomicState State => state;
		public bool IsStruggling => state == FransEconomicState.Struggling;
		public bool IsProsperousOrBetter => (int)state >= (int)FransEconomicState.Prosperous;
		public bool IsSurplus => state == FransEconomicState.Surplus;
		public bool RequestsSupplyCash => IsStruggling;
		public int AvailableQueueCount { get; private set; }
		public int BusyQueueCount { get; private set; }

		protected override void Created(Actor self)
		{
			playerResources = self.Trait<PlayerResources>();
		}

		protected override void TraitEnabled(Actor self)
		{
			var phase = Info.ScanInterval > 1 ? (int)self.ActorID % Info.ScanInterval : 0;
			scanTicks = phase + 1;
			samples.Clear();
			nextProbeLogTick = 0;
			SetState(FransEconomicState.Growing, force: true, "initial/default development state");
			FransBotLog.BotDebug(world,
				"{0}: FransEconomicState QUEUE CAPACITY active: state depends on sustainable production throughput only, never mine/refinery/Oil Derrick counts or fixed high-cash thresholds. Struggling=two-queue MinimumCash pressure; Growing=about three queues; Prosperous=three/four stable queues; Surplus=all existing mature queues sustained.", player);
		}

		protected override void TraitDisabled(Actor self)
		{
			RevokeStateCondition();
			samples.Clear();
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransEconomicSaturation.BotTick");
			if (player.WinState != WinState.Undefined)
				return;

			if (--scanTicks > 0)
				return;
			scanTicks = Info.ScanInterval;
			UpdateEconomicState();
		}

		void UpdateEconomicState()
		{
			var cash = playerResources.GetCashAndResources();
			(AvailableQueueCount, BusyQueueCount) = GetQueueCategoryCounts();
			RecordSample(new EconomySample(world.WorldTick, cash, AvailableQueueCount, BusyQueueCount));


			if (IsStrugglingPressure())
			{
				SetState(FransEconomicState.Struggling, false,
					$"cannot sustain {Info.StrugglingBusyQueues} queues: repeated MinimumCash pressure at {cash} with {BusyQueueCount}/{AvailableQueueCount} queue categories busy");
				return;
			}

			if (state == FransEconomicState.Struggling)
			{
				if (HasRecoveredFromStruggling())
					SetState(FransEconomicState.Growing, false,
						$"bank stabilized above MinimumCash while economy recovery runs ({cash} cash, {BusyQueueCount}/{AvailableQueueCount} queues busy)");
				return;
			}

			if (state == FransEconomicState.Surplus)
			{
				if (HasSustainedMinimumCashPressure(Info.SurplusReleaseSustainTicks))
				{
					SetState(FransEconomicState.Prosperous, false,
						$"expanded producer throughput now drives the economy back to MinimumCash pressure ({cash} cash)");
					return;
				}

				// Surplus intentionally persists while the expanded producer set can still be funded.
				return;
			}

			if (state == FransEconomicState.Prosperous)
			{
				if (CanProveSurplus(out var surplusReason))
				{
					SetState(FransEconomicState.Surplus, false, surplusReason);
					return;
				}

				if (world.WorldTick >= nextProbeLogTick)
				{
					nextProbeLogTick = world.WorldTick + 500;
					FransBotLog.BotDebug(world,
						"{0}: Prosperous state: cash {1}, queue categories busy {2}/{3}; explicit Prosperous producer targets are active while Surplus remains a separate proven throughput state.",
						player, cash, BusyQueueCount, AvailableQueueCount);
				}
				return;
			}

			if (CanProveProsperous(out var prosperousReason))
			{
				SetState(FransEconomicState.Prosperous, false, prosperousReason);
				return;
			}

			// Growing is the normal development state. It remains active until either repeated
			// two-queue MinimumCash pressure proves Struggling or sustainable throughput proves Prosperous.
		}

		(int Available, int Busy) GetQueueCategoryCounts()
		{
			var queuesByCategory = AIUtils.FindQueuesByCategory(player);
			var available = 0;
			var busy = 0;

			var buildingQueues = queuesByCategory[Info.BuildingQueueCategory]
				.Where(IsUsableQueue).ToArray();
			if (buildingQueues.Length > 0)
			{
				available++;
				if (buildingQueues.Any(q => q.AllQueued().Any()))
					busy++;
			}

			foreach (var category in Info.ProductionQueueCategories.Distinct())
			{
				var queues = queuesByCategory[category]
					.Where(IsUsableQueue)
					.Where(q => q.BuildableItems().Any())
					.ToArray();
				if (queues.Length == 0)
					continue;
				available++;
				if (queues.Any(q => q.AllQueued().Any()))
					busy++;
			}

			return (available, busy);
		}

		static bool IsUsableQueue(ProductionQueue q) => q != null && q.Enabled && q.Actor.IsInWorld && !q.Actor.IsDead;

		void RecordSample(EconomySample sample)
		{
			samples.Add(sample);
			var keepTicks = Math.Max(Math.Max(Info.StrugglingSustainTicks, Info.ProsperousSustainTicks),
				Math.Max(Info.SurplusSustainTicks, Info.SurplusReleaseSustainTicks)) + Info.ScanInterval * 3;
			var oldest = world.WorldTick - keepTicks;
			samples.RemoveAll(s => s.WorldTick < oldest);
		}

		EconomySample[] GetWindow(int ticks)
		{
			var from = world.WorldTick - ticks;
			return samples.Where(s => s.WorldTick >= from).OrderBy(s => s.WorldTick).ToArray();
		}

		bool HasFullWindow(EconomySample[] window, int ticks)
		{
			return window.Length >= 2 && window[0].WorldTick <= world.WorldTick - ticks + Info.ScanInterval;
		}

		bool IsStrugglingPressure()
		{
			var window = GetWindow(Info.StrugglingSustainTicks);
			if (!HasFullWindow(window, Info.StrugglingSustainTicks))
				return false;

			var loaded = window.Where(s => s.BusyQueues >= Info.StrugglingBusyQueues).ToArray();
			if (loaded.Length == 0 || loaded.Length * 100 < window.Length * Info.BusySamplePercent)
				return false;
			var atMinimum = loaded.Count(s => s.Cash <= Info.MinimumCash);
			return atMinimum * 100 >= loaded.Length * Info.BusySamplePercent;
		}

		bool HasRecoveredFromStruggling()
		{
			var window = GetWindow(Info.StrugglingRecoveryTicks);
			if (!HasFullWindow(window, Info.StrugglingRecoveryTicks))
				return false;
			var recoveryFloor = Info.MinimumCash + Info.StrugglingRecoveryMargin;
			return window.Count(s => s.Cash > recoveryFloor) * 100 >= window.Length * Info.BusySamplePercent;
		}

		bool CanProveProsperous(out string reason)
		{
			reason = null;
			var window = GetWindow(Info.ProsperousSustainTicks);
			if (!HasFullWindow(window, Info.ProsperousSustainTicks))
				return false;

			var loaded = window.Count(s => s.BusyQueues >= Info.ProsperousBusyQueues);
			if (loaded * 100 < window.Length * Info.BusySamplePercent)
				return false;
			if (window.Any(s => s.Cash <= Info.MinimumCash))
				return false;

			var cashDelta = window[^1].Cash - window[0].Cash;
			if (cashDelta < -Info.StableCashDrawdownTolerance)
				return false;

			var preferredSamples = window.Count(s => s.BusyQueues >= Info.ProsperousPreferredBusyQueues);
			reason = $"sustained {Info.ProsperousBusyQueues}+ queues for {Info.ProsperousSustainTicks} WT without MinimumCash pressure (peak {window.Max(s => s.BusyQueues)} queues, cash delta {cashDelta})";
			if (preferredSamples > 0)
				reason += $"; {Info.ProsperousPreferredBusyQueues}-queue operation observed";
			return true;
		}

		bool CanProveSurplus(out string reason)
		{
			reason = null;
			var window = GetWindow(Info.SurplusSustainTicks);
			if (!HasFullWindow(window, Info.SurplusSustainTicks))
				return false;
			if (window.Count(s => s.AvailableQueues >= Info.SurplusMinimumAvailableQueues) * 100 < window.Length * Info.BusySamplePercent)
				return false;
			if (window.Any(s => s.Cash <= Info.MinimumCash))
				return false;

			var allBusySamples = window.Count(s => s.AvailableQueues >= Info.SurplusMinimumAvailableQueues && s.BusyQueues >= s.AvailableQueues);
			if (allBusySamples * 100 < window.Length * Info.SurplusAllBusySamplePercent)
				return false;

			var cashDelta = window[^1].Cash - window[0].Cash;
			if (cashDelta < -Info.StableCashDrawdownTolerance)
				return false;

			reason = $"all existing mature queue categories remained funded for {Info.SurplusSustainTicks} WT ({allBusySamples}/{window.Length} all-busy samples, cash delta {cashDelta}); producer throughput is now the bottleneck";
			return true;
		}

		bool HasSustainedMinimumCashPressure(int ticks)
		{
			var window = GetWindow(ticks);
			if (!HasFullWindow(window, ticks))
				return false;
			var loaded = window.Where(s => s.BusyQueues >= Info.GrowingBusyQueues).ToArray();
			if (loaded.Length == 0)
				return false;
			return loaded.Count(s => s.Cash <= Info.MinimumCash) * 100 >= loaded.Length * Info.BusySamplePercent;
		}

		void SetState(FransEconomicState next, bool force, string reason)
		{
			if (!force && state == next)
				return;
			var previous = state;
			state = next;
			RevokeStateCondition();
			var condition = state switch
			{
				FransEconomicState.Struggling => Info.StrugglingCondition,
				FransEconomicState.Growing => Info.GrowingCondition,
				FransEconomicState.Prosperous => Info.ProsperousCondition,
				_ => Info.SurplusCondition
			};
			stateConditionToken = playerActor.GrantCondition(condition);
			FransBotLog.BotDebug(world,
				"{0}: ECONOMY STATE {1} -> {2}: {3}. Current cash {4}; queue categories busy {5}/{6}.",
				player, previous, state, reason, playerResources?.GetCashAndResources() ?? 0, BusyQueueCount, AvailableQueueCount);
		}

		void RevokeStateCondition()
		{
			if (stateConditionToken != Actor.InvalidConditionToken)
				stateConditionToken = playerActor.RevokeCondition(stateConditionToken);
		}
	}
}
