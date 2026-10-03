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
using System.Collections.Immutable;
using System.Linq;
using System.Xml.Linq;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	class BaseBuilderQueueManagerCA
	{
		public readonly string Category;
		public int WaitTicks;

		readonly BaseBuilderBotModuleCA baseBuilder;
		readonly World world;
		readonly Player player;
		readonly PowerManager playerPower;
		readonly PlayerResources playerResources;
		readonly IResourceLayer resourceLayer;

		Actor[] playerBuildings;
		int failCount;
		int failRetryTicks;
		string lastFailedBuilding;
		int checkForBasesTicks;
		int cachedBases;
		int cachedBuildings;
		int minimumExcessPower;
		int minCashRequirement;
		CPos? baseCenterKeepsFailing = null;

		bool itemQueuedThisTick = false;

		// An empty tolerance list in yaml would make ImmutableArray.Random throw.
		int RandomTolerance(ImmutableArray<int> values)
		{
			return values.IsDefaultOrEmpty ? 0 : values.Random(world.LocalRandom);
		}
		bool limitBuildRadius = false;

		WaterCheck waterState = WaterCheck.NotChecked;
		readonly Dictionary<string, int> activeBuildingIntervals = new Dictionary<string, int>();

		BotLimits botLimits;
		int productionTypeLimit = 0;
		int buildingDelayModifier = 100;
		int buildingIntervalModifier = 100;

		// Cameo (§12.20): lazy — resolved on first TickQueue, an OR-of-vetoes pause on new building
		// production. Empty = nothing pauses, upstream-identical.
		IBotRequestPauseBuildingProduction[] pauseBuilding;

		public BaseBuilderQueueManagerCA(BaseBuilderBotModuleCA baseBuilder, string category, Player p, PowerManager pm,
			PlayerResources pr, IResourceLayer rl)
		{
			this.baseBuilder = baseBuilder;
			world = p.World;
			player = p;
			playerPower = pm;
			playerResources = pr;
			resourceLayer = rl;
			Category = category;
			failRetryTicks = baseBuilder.Info.StructureProductionResumeDelay;
			minimumExcessPower = baseBuilder.Info.MinimumExcessPower;
			minCashRequirement = baseBuilder.Info.DefenseQueues.Contains(Category) ? baseBuilder.Info.DefenseProductionMinCashRequirement : baseBuilder.Info.BuildingProductionMinCashRequirement;
			if (baseBuilder.Info.NavalProductionTypes.Count == 0)
				waterState = WaterCheck.DontCheck;
			limitBuildRadius = world.WorldActor.TraitOrDefault<MapBuildRadius>().BuildRadiusEnabled;
		}

		public void SetBotLimits(BotLimits limits)
		{
			botLimits = limits;
			if (botLimits == null)
			{
				productionTypeLimit = 0;
				buildingDelayModifier = 100;
				buildingIntervalModifier = 100;
				return;
			}

			productionTypeLimit = botLimits.Info.ProductionTypeLimit;
			buildingDelayModifier = botLimits.Info.BuildingDelayModifier;
			buildingIntervalModifier = botLimits.Info.BuildingIntervalModifier;
		}

		// Scale targets (DESIGN 19.10): an enabled provider's production target replaces BotLimits.ProductionTypeLimit
		// (0 stays "no limit" when there are no BotLimits at all).
		int ProductionTypeLimit => productionTypeLimit > 0 && baseBuilder.TryGetScaleTarget("production", out var scaled)
			? scaled : productionTypeLimit;

		// BotLimits carries the per-difficulty value on the DESIGN §19.1 line; negative there means the module's own.
		// Build-order knobs (12.25): greed raises the cash the production priority override waits for (economy first), production lowers it.
		int NewProductionCashThreshold
		{
			get
			{
				var threshold = botLimits != null && botLimits.Info.NewProductionCashThreshold >= 0
					? botLimits.Info.NewProductionCashThreshold : baseBuilder.Info.NewProductionCashThreshold;
				var knobs = baseBuilder.BuildOrderKnobs;
				if (knobs == null || threshold <= 0)
					return threshold;

				return DivideByKnob(BotBuildOrderKnobs.Scale(threshold, knobs.KnobMilli(BuildOrderKnob.Greed)), knobs.KnobMilli(BuildOrderKnob.Production));
			}
		}

		public void Tick(IBot bot)
		{
			foreach (KeyValuePair<string, int> i in activeBuildingIntervals.ToList())
			{
				activeBuildingIntervals[i.Key]--;
				if (activeBuildingIntervals[i.Key] <= 0)
					activeBuildingIntervals.Remove(i.Key);
			}

			// If we can't place any structures, give a nudge to BaseExpansionModules and hope it gets fixed.
			if (failCount >= baseBuilder.Info.MaximumFailedPlacementAttempts)
			{
				if (baseBuilder.BaseExpansionModules != null && baseCenterKeepsFailing != null &&
					baseBuilder.RelocationHoldConyard == null)
				{
					// we should not give a nudge for defence
					if (!baseBuilder.Info.DefenseTypes.Contains(lastFailedBuilding))
					{
						var stuckConyard = baseBuilder.ConstructionYardBuildings.Actors
							.Where(a => (a.Location - baseCenterKeepsFailing.Value).LengthSquared <= baseBuilder.Info.MaxBaseRadius * baseBuilder.Info.MaxBaseRadius)
							.MinByOrDefault(a => (a.Location - baseCenterKeepsFailing.Value).LengthSquared);

						if (stuckConyard != null)
						{
							baseBuilder.RelocationHoldConyard = stuckConyard;
							foreach (var queue in stuckConyard.TraitsImplementing<ProductionQueue>())
							{
								foreach (var item in queue.AllQueued().ToArray())
									bot.QueueOrder(Order.CancelProduction(queue.Actor, item.Item, 1));
							}

							foreach (var be in baseBuilder.BaseExpansionModules)
								be.UpdateExpansionParams(bot, false, true, stuckConyard);

							failCount = 0;
							return;
						}
					}

					failCount = 0;
				}

				// No BaseExpansionModules exist. Only bother resetting failCount when either
				// a) the number of buildings has decreased since last failure M ticks ago,
				// or b) number of BaseProviders (construction yard or similar) has increased since then.
				// Otherwise reset failRetryTicks instead to wait again.
				// (BaseExpansionModules is a .ToArray() — never null; Length==0 was the intent.)
				else if (baseBuilder.BaseExpansionModules.Length == 0 && --failRetryTicks <= 0)
				{
					var currentBuildings = world.ActorsHavingTrait<Building>().Count(a => a.Owner == player);
					var baseProviders = world.ActorsHavingTrait<BaseProvider>().Count(a => a.Owner == player);

					if (currentBuildings < cachedBuildings || baseProviders > cachedBases)
						failCount = 0;
					else
						failRetryTicks = baseBuilder.Info.StructureProductionResumeDelay;
				}

				if (failCount >= baseBuilder.Info.MaximumFailedPlacementAttempts)
					return;
			}

			if (waterState == WaterCheck.NotChecked)
			{
				if (AIUtils.IsAreaAvailable<BaseProvider>(world, player, world.Map, baseBuilder.Info.MaxBaseRadius, baseBuilder.Info.WaterTerrainTypes))
					waterState = WaterCheck.EnoughWater;
				else
				{
					waterState = WaterCheck.NotEnoughWater;
					checkForBasesTicks = baseBuilder.Info.CheckForNewBasesDelay;
				}
			}

			if (waterState == WaterCheck.NotEnoughWater && --checkForBasesTicks <= 0)
			{
				var currentBases = world.ActorsHavingTrait<BaseProvider>().Count(a => a.Owner == player);

				if (currentBases > cachedBases)
				{
					cachedBases = currentBases;
					waterState = WaterCheck.NotChecked;
				}
				else
					checkForBasesTicks = baseBuilder.Info.CheckForNewBasesDelay;
			}

			// Only update once per second or so
			if (WaitTicks > 0)
				return;

			playerBuildings = world.ActorsHavingTrait<Building>().Where(a => a.Owner == player).ToArray();
			var excessPowerBonus = baseBuilder.Info.ExcessPowerIncrement * (playerBuildings.Count() / baseBuilder.Info.ExcessPowerIncreaseThreshold.Clamp(1, int.MaxValue));
			minimumExcessPower = (baseBuilder.Info.MinimumExcessPower + excessPowerBonus).Clamp(baseBuilder.Info.MinimumExcessPower, baseBuilder.Info.MaximumExcessPower);

			// Build-order knobs (12.25): power_margin scales the surplus target (no provider = unchanged).
			var knobs = baseBuilder.BuildOrderKnobs;
			if (knobs != null)
				minimumExcessPower = BotBuildOrderKnobs.Scale(minimumExcessPower, knobs.KnobMilli(BuildOrderKnob.PowerMargin));

			// PERF: Queue only one actor at a time per category
			itemQueuedThisTick = false;
			var active = false;
			foreach (var queue in AIUtils.FindQueues(player, Category))
			{
				if (TickQueue(bot, queue))
					active = true;
			}

			// Add a random factor so not every AI produces at the same tick early in the game.
			// Minimum should not be negative as delays in HackyAI could be zero.
			var randomFactor = world.LocalRandom.Next(0, baseBuilder.Info.StructureProductionRandomBonusDelay);

			WaitTicks = active ? baseBuilder.Info.StructureProductionActiveDelay + randomFactor
				: baseBuilder.Info.StructureProductionInactiveDelay + randomFactor;

			// Build-order knobs (12.25): tempo shortens (above 1000) or lengthens the general build interval.
			if (knobs != null)
				WaitTicks = DivideByKnob(WaitTicks, knobs.KnobMilli(BuildOrderKnob.Tempo));
		}

		bool TickQueue(IBot bot, ProductionQueue queue)
		{
			if (queue.Actor == baseBuilder.RelocationHoldConyard)
				return false;

			var currentBuilding = queue.AllQueued().FirstOrDefault();

			// Waiting to build something
			if (currentBuilding == null && failCount < baseBuilder.Info.MaximumFailedPlacementAttempts)
			{
				var item = ChooseBuildingToBuild(queue);
				if (item == null)
					return false;

				// We shouldn't be queueing new buildings (other than refineries) when we're low on cash
				if ((playerResources.GetCashAndResources() < minCashRequirement && !baseBuilder.Info.RefineryTypes.Contains(item.Name)) || itemQueuedThisTick)
					return false;

				// Cameo (§12.20): the army-first vote - a provider (ArmyFirstBotModule, the one owner) can hold new
				// non-essential buildings so cash flows to unit production while it needs to. Construction yards,
				// refineries, power and the first production building are essential and always pass.
				pauseBuilding ??= player.PlayerActor.TraitsImplementing<IBotRequestPauseBuildingProduction>().ToArray();
				if (pauseBuilding.Length > 0)
				{
					var essential = IsArmyFirstEssential(item);
					if (pauseBuilding.Any(p => p.PausesBuilding(item, essential)))
						return false;
				}

				baseBuilder.RecordOpeningStructureQueued(queue, item);
				baseBuilder.BuildOrderKnobs?.NotifyQueued(item.Name);
				bot.QueueOrder(Order.StartProduction(queue.Actor, item.Name, 1));
				queuedAt[queue.Actor.ActorID] = (item.Name, world.WorldTick);
				itemQueuedThisTick = true;
				SetBuildingInterval(item.Name);
			}
			else if (currentBuilding != null && currentBuilding.Done)
			{
				// Production is complete
				// Choose the placement logic
				// HACK: HACK HACK HACK
				// TODO: Derive this from BuildingCommonNames instead
				var type = BuildingType.Building;
				var placeDefenseTowardsEnemyChance = baseBuilder.Info.PlaceDefenseTowardsEnemyChance;

				CPos? location = null;
				var actorVariant = 0;
				string orderString = "PlaceBuilding";

				// Check if we've hit the limit for this building already, if so cancel it
				if (baseBuilder.TryGetBuildingLimit(currentBuilding.Item, out var currentLimit))
				{
					if ((AIUtils.CountBuildingByCommonName(new HashSet<string> { currentBuilding.Item }, player) >= currentLimit))
					{
						AIUtils.BotDebug($"{player} has already has enough {currentBuilding.Item}; cancelling production");
						bot.QueueOrder(Order.CancelProduction(queue.Actor, currentBuilding.Item, 1));
					}
				}

				// Check if Building is a plug for other Building
				var actorInfo = world.Map.Rules.Actors[currentBuilding.Item];
				var plugInfo = actorInfo.TraitInfoOrDefault<PlugInfo>();
				var valueInfo = actorInfo.TraitInfoOrDefault<ValuedInfo>();
				var distanceToBaseIsImportant = true;
				CPos? advisedDefense = null;
				refineryClaimed = false;
				if (plugInfo != null)
				{
					var possibleBuilding = world.ActorsWithTrait<Pluggable>().FirstOrDefault(a =>
						a.Actor.Owner == player && a.Trait.AcceptsPlug(plugInfo.Type));

					if (possibleBuilding.Actor != null)
					{
						orderString = "PlacePlug";
						location = possibleBuilding.Actor.Location + possibleBuilding.Trait.Info.Offset;
					}
				}
				else
				{
					// Check if Building is a defense and if we should place it towards the enemy or not.
					if (baseBuilder.Info.RefineryTypes.Contains(actorInfo.Name))
					{
						type = BuildingType.Refinery;
					}
					else if (baseBuilder.Info.FragileTypes.Contains(actorInfo.Name))
					{
						type = BuildingType.Fragile;
						// distanceToBaseIsImportant = false;
					}
					else if (actorInfo.HasTraitInfo<AttackBaseInfo>())
					{
						// Cameo: an active advisor picks the cell itself, skipping the roll (no random draw is consumed);
						// without one, or when it has no answer, the code below is unchanged.
						advisedDefense = AdvisedDefenseCell(actorInfo, distanceToBaseIsImportant, queue.Actor);
						if (advisedDefense == null)
						{
							if (baseBuilder.Info.AntiAirTypes.Contains(actorInfo.Name))
								placeDefenseTowardsEnemyChance = (int)Math.Ceiling(placeDefenseTowardsEnemyChance / 1.5);

							if (world.LocalRandom.Next(100) < placeDefenseTowardsEnemyChance)
								type = BuildingType.Defense;
						}
					}
					else if (!limitBuildRadius && valueInfo != null && valueInfo.Cost < baseBuilder.Info.BaseCrawlCostThreshold && world.LocalRandom.Next(100) < baseBuilder.Info.BaseCrawlChance)
						type = BuildingType.BaseCrawl;

					if (advisedDefense != null)
						location = advisedDefense;
					else
						(location, baseCenterKeepsFailing, actorVariant) = ChooseBuildLocation(currentBuilding.Item, distanceToBaseIsImportant, queue.Actor, type);
				}

				if (location == null)
				{
					// If we just reached the maximum fail count, cache the number of current structures
					if (++failCount >= baseBuilder.Info.MaximumFailedPlacementAttempts)
					{
						AIUtils.BotDebug($"{player} has nowhere to place {currentBuilding.Item}");
						bot.QueueOrder(Order.CancelProduction(queue.Actor, currentBuilding.Item, 1));
						lastFailedBuilding = currentBuilding.Item;
						if (baseBuilder.BaseExpansionModules == null)
						{
							cachedBuildings = world.ActorsHavingTrait<Building>().Count(a => a.Owner == player);
							cachedBases = world.ActorsHavingTrait<BaseProvider>().Count(a => a.Owner == player);
						}
					}
				}
				else
				{
					failCount = 0;
					NotifyPlacement(currentBuilding.Item, location.Value, queue.Actor.ActorID, orderString, type, advisedDefense != null);

					bot.QueueOrder(new Order(orderString, player.PlayerActor, Target.FromCell(world, location.Value), false)
					{
						// Building to place
						TargetString = currentBuilding.Item,

						// Actor variant will always be small enough to safely pack in a CPos
						ExtraLocation = new CPos(actorVariant, 0),

						// Actor ID to associate the placement with
						ExtraData = queue.Actor.ActorID,
						SuppressVisualFeedback = true
					});

					// After succesfuly placing a building, nudge BaseExpansionModules to expand.
					// We want to avoid expanding too often, so we make a judgement by counting buildings.
					if (baseBuilder.Info.ProductionTypes.Contains(currentBuilding.Item)
						|| baseBuilder.Info.FragileTypes.Contains(currentBuilding.Item) || baseBuilder.Info.RefineryTypes.Contains(currentBuilding.Item))
					{
						var numRef = baseBuilder.RefineryBuildings.Actors.Count(a => !a.IsDead) + (baseBuilder.Info.RefineryTypes.Contains(currentBuilding.Item) ? 1 : 0);

						var numProd = baseBuilder.ProductionBuildings.Actors.Count(a => !a.IsDead) + (baseBuilder.Info.ProductionTypes.Contains(currentBuilding.Item) ? 1 : 0);

						var numTech = playerBuildings.Count(a => baseBuilder.Info.FragileTypes.Contains(a.Info.Name))
							+ (baseBuilder.Info.FragileTypes.Contains(currentBuilding.Item) ? 1 : 0);

						var tolerateOnCash = playerResources.GetCashAndResources() / Math.Max(baseBuilder.Info.PerExpansionTolerateOnCash, 1);

						if (numRef >= baseBuilder.Info.InititalMinimumRefineryCount + baseBuilder.Info.AdditionalMinimumRefineryCount
							&& numProd > 0 && numProd + numTech - RandomTolerance(baseBuilder.Info.ExpansionTolerate) - tolerateOnCash >= numRef)
						{
							var undeployEvenNoBase = numProd + numTech - RandomTolerance(baseBuilder.Info.ForceExpansionTolerate) - tolerateOnCash >= numRef;

							foreach (var be in baseBuilder.BaseExpansionModules)
								be.UpdateExpansionParams(bot, true, undeployEvenNoBase, null);
						}
					}
					return true;
				}
			}

			return true;
		}

		// Cameo (12.24 FE-0 / 12.25 BO-0): record-only telemetry. The queue tick per producer and the refinery-claim flag are read by
		// NotifyPlacement only; nothing here feeds a decision.
		readonly Dictionary<uint, (string Item, int Tick)> queuedAt = new();
		bool refineryClaimed;
		IBotPlacementObserver[] placementObservers;

		void NotifyPlacement(string item, CPos cell, uint producerId, string orderString, BuildingType type, bool advisedDefence)
		{
			placementObservers ??= world.WorldActor.TraitsImplementing<IBotPlacementObserver>().ToArray();
			if (placementObservers.Length == 0)
				return;

			var reason = orderString != "PlaceBuilding" ? "other"
				: advisedDefence || type == BuildingType.Defense ? "defence"
				: type == BuildingType.BaseCrawl ? "crawl"
				: type == BuildingType.Refinery && refineryClaimed ? "refinery_claim"
				: "base";
			var queued = queuedAt.TryGetValue(producerId, out var q) && q.Item == item ? q.Tick : world.WorldTick;
			foreach (var observer in placementObservers)
				observer.BuildingPlaced(player, world.WorldTick, item, cell, reason, queued);
		}

		ActorInfo GetProducibleBuilding(IReadOnlySet<string> actors, IEnumerable<ActorInfo> buildables, Func<ActorInfo, int> orderBy = null)
		{
			var available = buildables.Where(actor =>
			{
				// Are we able to build this?
				if (!actors.Contains(actor.Name))
					return false;

				if (!baseBuilder.TryGetBuildingLimit(actor.Name, out var limit))
					return true;

				return playerBuildings.Count(a => a.Info.Name == actor.Name) +
					(baseBuilder.BuildingsBeingProduced.TryGetValue(actor.Name, out var beingProduced) ? beingProduced : 0) < limit;
			});

			if (orderBy != null)
				return available.MaxByOrDefault(orderBy);

			return available.RandomOrDefault(world.LocalRandom);
		}

		bool HasSufficientPowerForActor(ActorInfo actorInfo)
		{
			return playerPower == null || (actorInfo.TraitInfos<PowerInfo>().Where(i => i.EnabledByDefault)
				.Sum(p => p.Amount) + playerPower.ExcessPower) >= ScaledBaseMinimumExcessPower();
		}

		// Build-order knobs (12.25): power_margin scales the configured surplus floor too.
		int ScaledBaseMinimumExcessPower()
		{
			var knobs = baseBuilder.BuildOrderKnobs;
			return knobs == null ? baseBuilder.Info.MinimumExcessPower
				: BotBuildOrderKnobs.Scale(baseBuilder.Info.MinimumExcessPower, knobs.KnobMilli(BuildOrderKnob.PowerMargin));
		}

		// Build-order knobs (12.25): the milli multiplier of a building's fraction by its rules-derived category (1000 = none).
		int FractionMilli(string actorName)
		{
			var knobs = baseBuilder.BuildOrderKnobs;
			if (knobs == null)
				return BuildOrderKnob.Neutral;

			var knob = BuildOrderCategory.KnobFor(knobs.CategoryOf(actorName));
			return knob == null ? BuildOrderKnob.Neutral : knobs.KnobMilli(knob);
		}

		// Build-order knobs (12.25): the opening's next wanted building, preferred over the fraction table. It runs AFTER the
		// low-power and refinery priority overrides, so an opening never blocks a power or refinery emergency, and it respects
		// the same limits and the power check as every other choice. Null = no opening, nothing wanted here, or nothing buildable
		// in this queue (another queue's manager may take the step).
		ActorInfo ChooseOpeningBuilding(IBotBuildOrderKnobs knobs, IEnumerable<ActorInfo> buildableThings, ActorInfo power)
		{
			var wanted = knobs.OpeningWanted;
			if (wanted == null)
				return null;

			ActorInfo best = null;
			var bestFraction = -1;
			foreach (var candidate in buildableThings)
			{
				var name = candidate.Name;
				if (!BuildOrderCategory.Satisfies(wanted, knobs.CategoryOf(name)))
					continue;

				if (baseBuilder.Info.NavalProductionTypes.Contains(name) || baseBuilder.Info.RefineryTypes.Contains(name) && baseBuilder.HasMaxRefineriesFor(candidate))
					continue;

				var count = playerBuildings.Count(a => a.Info.Name == name) +
					(baseBuilder.BuildingsBeingProduced.TryGetValue(name, out var num) ? num : 0);

				if (botLimits != null && baseBuilder.Info.ProductionTypes.Contains(name) && count >= ProductionTypeLimit)
					continue;

				if (baseBuilder.TryGetBuildingLimit(name, out var limit) && limit <= count)
					continue;

				var fraction = baseBuilder.Info.BuildingFractions != null && baseBuilder.Info.BuildingFractions.TryGetValue(name, out var f) ? f : 0;
				if (best == null || fraction > bestFraction || fraction == bestFraction && string.CompareOrdinal(name, best.Name) < 0)
				{
					best = candidate;
					bestFraction = fraction;
				}
			}

			if (best == null)
				return null;

			if (!HasSufficientPowerForActor(best))
				return power != null && power.TraitInfos<PowerInfo>().Where(i => i.EnabledByDefault).Sum(pi => pi.Amount) > 0 ? power : null;

			AIUtils.BotDebug("{0} decided to build {1}: opening step {2}", player, best.Name, wanted);
			return best;
		}

		static int DivideByKnob(int ticks, int milli) => milli == BuildOrderKnob.Neutral ? ticks : (int)(ticks * 1000L / Math.Max(1, milli));

		// Build-order knobs (12.25): a delay or interval in ticks for one building. tempo divides every one (above 1000 = faster);
		// a tech/superweapon building's also divides by the tech knob, a refinery's by greed. No provider = unchanged.
		int KnobTicks(int ticks, string actorName)
		{
			var knobs = baseBuilder.BuildOrderKnobs;
			if (knobs == null)
				return ticks;

			ticks = DivideByKnob(ticks, knobs.KnobMilli(BuildOrderKnob.Tempo));
			var knob = BuildOrderCategory.KnobFor(knobs.CategoryOf(actorName));
			if (knob == BuildOrderKnob.Tech || knob == BuildOrderKnob.Greed)
				ticks = DivideByKnob(ticks, knobs.KnobMilli(knob));

			return ticks;
		}

		// Cameo (army-first): buildings that stay allowed while the army-first vote holds
		// the rest. Construction yards, refineries and power are always essential; the first
		// production building must pass too — no factory means no army, so blocking it deadlocks.
		bool IsArmyFirstEssential(ActorInfo actorInfo)
		{
			var name = actorInfo.Name;
			if (baseBuilder.Info.ConstructionYardTypes.Contains(name)
				|| baseBuilder.Info.RefineryTypes.Contains(name)
				|| baseBuilder.Info.PowerTypes.Contains(name))
				return true;

			// One queued-but-unplaced factory is enough to break the deadlock — don't let the
			// gate admit a second one while the first is still producing.
			if (baseBuilder.Info.ProductionTypes.Contains(name)
				&& !baseBuilder.HasAdequateProductionCount()
				&& !baseBuilder.BuildingsBeingProduced.Keys.Any(baseBuilder.Info.ProductionTypes.Contains))
				return true;

			return false;
		}

		ActorInfo ChooseBuildingToBuild(ProductionQueue queue)
		{
			var buildableThings = queue.BuildableItems();
			var availableCash = playerResources.GetCashAndResources();

			// This gets used quite a bit, so let's cache it here
			var power = GetProducibleBuilding(baseBuilder.Info.PowerTypes, buildableThings,
				a => a.TraitInfos<PowerInfo>().Where(i => i.EnabledByDefault).Sum(p => p.Amount));
			var openingBarracksPolicyActive = botLimits != null && botLimits.Info.PrioritizeBarracksBeforeRefinery
				&& baseBuilder.Info.BarracksBeforeRefineryFactions.Contains(player.Faction.InternalName)
				&& !baseBuilder.OpeningBarracksPriorityCompleted;

			// Wait for the queued opening structure to be placed before allowing another construction queue to proceed.
			if (openingBarracksPolicyActive && (baseBuilder.HasQueuedPowerPlant() || baseBuilder.HasQueuedBarracks()))
				return null;

			// First priority is to get out of a low power situation
			if (playerPower != null && playerPower.ExcessPower < minimumExcessPower && power != null && power.TraitInfos<PowerInfo>().Where(i => i.EnabledByDefault).Sum(p => p.Amount) > 0)
			{
					AIUtils.BotDebug("{0} decided to build {1}: Priority override (low power)", queue.Actor.Owner, power.Name);
					return power;
			}

			if (openingBarracksPolicyActive && !baseBuilder.HasBuiltOrQueuedBarracks())
			{
				// Finish the opening power plant before starting the barracks.
				if (!baseBuilder.HasCompletedPowerPlant())
				{
					if (!baseBuilder.HasQueuedPowerPlant() && power != null && queue.GetProductionCost(power) <= availableCash)
					{
						AIUtils.BotDebug("{0} decided to build {1}: Priority override (opening power)", queue.Actor.Owner, power.Name);
						return power;
					}
				}
				else
				{
					var barracks = GetProducibleBuilding(baseBuilder.Info.BarracksTypes, buildableThings);

					if (barracks != null && queue.GetProductionCost(barracks) <= availableCash)
					{
						if (HasSufficientPowerForActor(barracks))
						{
							AIUtils.BotDebug("{0} decided to build {1}: Priority override (opening barracks)", queue.Actor.Owner, barracks.Name);
							return barracks;
						}

						if (power != null && queue.GetProductionCost(power) <= availableCash)
						{
							AIUtils.BotDebug("{0} decided to build {1}: Priority override (opening barracks would cause low power)", queue.Actor.Owner, power.Name);
							return power;
						}
					}
				}
			}

			// Next is to build up a strong economy
			if (!baseBuilder.HasAdequateRefineryCount())
			{
				var refinery = GetProducibleBuilding(baseBuilder.Info.RefineryTypes, buildableThings);

				// RefineryLimit is shared across every faction the player owns, so always allow
				// a faction's own first refinery through even if that global cap has already
				// been reached by a different faction's construction yard.
				if (refinery != null && !baseBuilder.HasMaxRefineriesFor(refinery))
				{
					if (HasSufficientPowerForActor(refinery))
					{
						AIUtils.BotDebug("{0} decided to build {1}: Priority override (refinery)", queue.Actor.Owner, refinery.Name);
						return refinery;
					}

					if (power != null && !HasSufficientPowerForActor(refinery))
					{
						AIUtils.BotDebug("{0} decided to build {1}: Priority override (would be low power)", queue.Actor.Owner, power.Name);
						return power;
					}
				}
			}

			// Build-order knobs (12.25): the active opening's next wanted building.
			var buildOrderKnobs = baseBuilder.BuildOrderKnobs;
			if (buildOrderKnobs != null)
			{
				var opening = ChooseOpeningBuilding(buildOrderKnobs, buildableThings, power);
				if (opening != null)
					return opening;
			}

			// Make sure that we can spend as fast as we are earning
			if (NewProductionCashThreshold > 0 && playerResources.GetCashAndResources() > NewProductionCashThreshold)
			{
				var production = GetProducibleBuilding(baseBuilder.Info.ProductionTypes, buildableThings);

				if (production != null && (ProductionTypeLimit <= 0 || playerBuildings.Count(a => a.Info.Name == production.Name) < ProductionTypeLimit))
				{
					if (HasSufficientPowerForActor(production))
					{
						AIUtils.BotDebug("{0} decided to build {1}: Priority override (production)", queue.Actor.Owner, production.Name);
						return production;
					}

					if (power != null && !HasSufficientPowerForActor(production))
					{
						AIUtils.BotDebug("{0} decided to build {1}: Priority override (would be low power)", queue.Actor.Owner, power.Name);
						return power;
					}
				}
			}

			// Only consider building this if there is enough water inside the base perimeter and there are close enough adjacent buildings
			if (waterState == WaterCheck.EnoughWater && NewProductionCashThreshold > 0
				&& playerResources.Resources > NewProductionCashThreshold
				&& AIUtils.IsAreaAvailable<GivesBuildableArea>(world, player, world.Map, baseBuilder.Info.CheckForWaterRadius, baseBuilder.Info.WaterTerrainTypes))
			{
				var navalproduction = GetProducibleBuilding(baseBuilder.Info.NavalProductionTypes, buildableThings);
				if (navalproduction != null && HasSufficientPowerForActor(navalproduction))
				{
					AIUtils.BotDebug("{0} decided to build {1}: Priority override (navalproduction)", queue.Actor.Owner, navalproduction.Name);
					return navalproduction;
				}

				if (power != null && navalproduction != null && !HasSufficientPowerForActor(navalproduction))
				{
					AIUtils.BotDebug("{0} decided to build {1}: Priority override (would be low power)", queue.Actor.Owner, power.Name);
					return power;
				}
			}

			// Create some head room for resource storage if we really need it
			if (playerResources.Resources > 0.8 * playerResources.ResourceCapacity)
			{
				var silo = GetProducibleBuilding(baseBuilder.Info.SiloTypes, buildableThings);
				if (silo != null && HasSufficientPowerForActor(silo))
				{
					AIUtils.BotDebug("{0} decided to build {1}: Priority override (silo)", queue.Actor.Owner, silo.Name);
					return silo;
				}

				if (power != null && silo != null && !HasSufficientPowerForActor(silo))
				{
					AIUtils.BotDebug("{0} decided to build {1}: Priority override (would be low power)", queue.Actor.Owner, power.Name);
					return power;
				}
			}

			// Build everything else
			foreach (var frac in baseBuilder.Info.BuildingFractions.Shuffle(world.LocalRandom))
			{
				var name = frac.Key;

				// Does this building have initial delay, if so have we passed it?
				if (baseBuilder.Info.BuildingDelays != null &&
					baseBuilder.Info.BuildingDelays.TryGetValue(name, out var delay) &&
					KnobTicks(delay * buildingDelayModifier / 100, name) > world.WorldTick)
					continue;

				// Does this building have an interval which hasn't elapsed yet?
				if (baseBuilder.Info.BuildingIntervals != null &&
					baseBuilder.Info.BuildingIntervals.ContainsKey(name) &&
					activeBuildingIntervals.ContainsKey(name))
					continue;

				// Can we build this structure?
				if (!buildableThings.Any(b => b.Name == name))
					continue;

				// Check the number of this structure and its variants
				var actorInfo = world.Map.Rules.Actors[name];
				var buildingVariantInfo = actorInfo.TraitInfoOrDefault<PlaceBuildingVariantsInfo>();
				var variants = buildingVariantInfo?.Actors ?? [];

				var count = playerBuildings.Count(a =>
					a.Info.Name == name || variants.Contains(a.Info.Name)) +
					(baseBuilder.BuildingsBeingProduced.TryGetValue(name, out var num) ? num : 0);

				// Do we want to build this structure?
				// Build-order knobs (12.25): production/tech/defence/support/greed scale the fraction of their categories (milli = 1000 without a provider).
				if (count * 100L * 1000 > (long)frac.Value * FractionMilli(name) * playerBuildings.Length)
					continue;

				if (botLimits != null && baseBuilder.Info.ProductionTypes.Contains(name) && count >= ProductionTypeLimit)
				{
					AIUtils.BotDebug("{0} decided to build {1} but limit of {2} already reached)", queue.Actor.Owner, name, ProductionTypeLimit);
					continue;
				}

				if (baseBuilder.TryGetBuildingLimit(name, out var limit) && limit <= count)
				{
					AIUtils.BotDebug("{0} decided to build {1} but limit of {2} already reached)", queue.Actor.Owner, name, limit);
					continue;
				}

				if (baseBuilder.Info.RefineryTypes.Contains(name) && baseBuilder.HasMaxRefineriesFor(actorInfo))
					continue;

				// If we're considering to build a naval structure, check whether there is enough water inside the base perimeter
				// and any structure providing buildable area close enough to that water.
				// TODO: Extend this check to cover any naval structure, not just production.
				if (baseBuilder.Info.NavalProductionTypes.Contains(name)
					&& (waterState == WaterCheck.NotEnoughWater
						|| !AIUtils.IsAreaAvailable<GivesBuildableArea>(world, player, world.Map, baseBuilder.Info.CheckForWaterRadius, baseBuilder.Info.WaterTerrainTypes)))
					continue;

				// Will this put us into low power?
				var actor = world.Map.Rules.Actors[name];
				if (playerPower != null && (playerPower.ExcessPower < minimumExcessPower || !HasSufficientPowerForActor(actor)))
				{
					// Try building a power plant instead
					if (power != null && power.TraitInfos<PowerInfo>().Where(i => i.EnabledByDefault).Sum(pi => pi.Amount) > 0)
					{
						if (playerPower.PowerOutageRemainingTicks > 0)
							AIUtils.BotDebug("{0} decided to build {1}: Priority override (is low power)", queue.Actor.Owner, power.Name);
						else
							AIUtils.BotDebug("{0} decided to build {1}: Priority override (would be low power)", queue.Actor.Owner, power.Name);

						return power;
					}
				}

				// Lets build this
				AIUtils.BotDebug("{0} decided to build {1}: Desired is {2} ({3} / {4}); current is {5} / {4}",
					queue.Actor.Owner, name, frac.Value, frac.Value * playerBuildings.Length, playerBuildings.Length, count);
				return actor;
			}

			// Too spammy to keep enabled all the time, but very useful when debugging specific issues.
			// AIUtils.BotDebug("{0} couldn't decide what to build for queue {1}.", queue.Actor.Owner, queue.Info.Group);
			return null;
		}

		// Find the buildable cell that is closest to pos and centered around center.
		// The building gap belongs to the placement advisor (BuildingGapRule.Resolve; no advisor = no gap);
		// defense-style callers pass defenseGap so walls/turrets can still form tighter lines.
		(CPos? Location, CPos Center, int Variant) findPos(string actorType, bool distanceToBaseIsImportant, Actor producer, CPos center, CPos target, int minRange, int maxRange, int distanceRequirement = 0, bool sortMax = false, bool defenseGap = false, CPos? anchorTieBreak = null, bool anchorOrder = false)
		{
			var actorInfo = world.Map.Rules.Actors[actorType];
			var actorVariant = 0;
			var buildingVariantInfo = actorInfo.TraitInfoOrDefault<PlaceBuildingVariantsInfo>();
			var bi = actorInfo.TraitInfoOrDefault<BuildingInfo>();
			if (bi == null)
				return (null, center, 0);

			var cells = world.Map.FindTilesInAnnulus(center, minRange, maxRange);

			// Sort by distance to target if we have one
			if (center != target || anchorOrder)
			{
				cells = sortMax ? cells.OrderByDescending(c => (c - target).LengthSquared) : cells.OrderBy(c => (c - target).LengthSquared);

				// FE-1 (§12.24): the refinery claim takes the placeable cell nearest its anchor; ties go to the cell
				// closest to the field's resource cells. OrderBy is stable, so every other caller is unchanged.
				if (anchorOrder && anchorTieBreak.HasValue)
				{
					var tie = anchorTieBreak.Value;
					cells = ((IOrderedEnumerable<CPos>)cells).ThenBy(c => (c - tie).LengthSquared);
				}

				// Rotate building if we have a Facings in buildingVariantInfo.
				// If we don't have Facings in buildingVariantInfo, use a random variant
				if (buildingVariantInfo?.Actors != null)
				{
					if (buildingVariantInfo.Facings != null)
					{
						var vector = world.Map.CenterOfCell(target) - world.Map.CenterOfCell(center);

						// FE-1: centre == target (anchor placement) has no direction; keep variant 0 instead of dividing by zero.
						if (vector.Length == 0)
							vector = new WVec(0, 1, 0);

						// The rotation Y point to upside vertically, so -Y = Y(rotation)
						var desireFacing = new WAngle(WAngle.ArcSin((int)((long)Math.Abs(vector.X) * 1024 / vector.Length)).Angle);
						if (vector.X > 0 && vector.Y >= 0)
							desireFacing = new WAngle(512) - desireFacing;
						else if (vector.X < 0 && vector.Y >= 0)
							desireFacing = new WAngle(512) + desireFacing;
						else if (vector.X < 0 && vector.Y < 0)
							desireFacing = -desireFacing;

						for (int i = 0, e = 1024; i < buildingVariantInfo.Facings.Length; i++)
						{
							var minDelta = Math.Min((desireFacing - buildingVariantInfo.Facings[i]).Angle, (buildingVariantInfo.Facings[i] - desireFacing).Angle);
							if (e > minDelta)
							{
								e = minDelta;
								actorVariant = i;
							}
						}
					}
					else
						actorVariant = world.LocalRandom.Next(buildingVariantInfo.Actors.Length + 1);
				}
			}
			else
			{
				cells = cells.Shuffle(world.LocalRandom);

				if (buildingVariantInfo?.Actors != null)
					actorVariant = world.LocalRandom.Next(buildingVariantInfo.Actors.Length + 1);
			}

			if (actorVariant != 0)
			{
				actorInfo = world.Map.Rules.Actors[buildingVariantInfo.Actors[actorVariant - 1]];
				bi = actorInfo.TraitInfoOrDefault<BuildingInfo>();
			}

			// Cameo (building spacing): cells within `gap` of an own building's footprint are
			// off-limits so a new building keeps that much empty space to existing structures.
			// The buffer is built once per search from the per-tick playerBuildings cache —
			// never relaxed inside this call; an exhausted annulus returns null and the
			// caller retries later. AllowInvalidPlacement actors bypass CanPlaceBuilding
			// entirely, so they keep bypassing the spacing rule too — same opt-out semantic.
			var advisor = player.PlayerActor.TraitsImplementing<IBotPlacementAdvisor>().FirstOrDefault(a => a.IsActive);

			// Refineries are owned by field proximity (EX-2 claims, SP-1 fix 1ba1db9b8): spacing never touches them,
			// the hard gap included — a gap-pushed refinery reads its field as unserved and the builder stacks another.
			var isRefinery = world.Map.Rules.Actors.TryGetValue(actorType, out var placedInfo) && placedInfo.HasTraitInfo<RefineryInfo>();
			var gap = isRefinery ? 0 : BuildingGapRule.Resolve(advisor, defenseGap);
			var ownBuildingBuffer = gap > 0 ? OwnBuildingBufferCells(gap) : null;

			// Cameo (§12.20): an advisor that ranks re-ranks a bounded prefix of placeable, gap-valid cells
			// (spread-out bases instead of first-valid packing). No ranking advisor = first valid cell wins,
			// exactly as upstream.
			if (advisor != null && advisor.RanksCandidates && !anchorOrder)
			{
				var candidates = new List<CPos>();
				foreach (var cell in cells)
				{
					if (!world.CanPlaceBuilding(cell, actorInfo, bi, null))
						continue;

					if (distanceToBaseIsImportant && !bi.IsCloseEnoughToBase(world, player, actorInfo, producer, cell))
						continue;

					if (distanceRequirement > 0 && (cell - target).LengthSquared > distanceRequirement * distanceRequirement)
						continue;

					if (ownBuildingBuffer != null && !bi.AllowInvalidPlacement && bi.Tiles(cell).Any(ownBuildingBuffer.Contains))
						continue;

					candidates.Add(cell);
					if (candidates.Count >= baseBuilder.Info.PlacementAdvisorCandidates)
						break;
				}

				if (candidates.Count > 0)
				{
					var chosen = advisor.ChooseCell(actorInfo, candidates,
						c => world.CanPlaceBuilding(c, actorInfo, bi, null));
					if (chosen.HasValue && candidates.Contains(chosen.Value))
						return (chosen.Value, center, actorVariant);

					return (candidates[0], center, actorVariant);
				}
			}
			else
			{
				foreach (var cell in cells)
				{
					if (!world.CanPlaceBuilding(cell, actorInfo, bi, null))
						continue;

					if (distanceToBaseIsImportant && !bi.IsCloseEnoughToBase(world, player, actorInfo, producer, cell))
						continue;

					if (distanceRequirement > 0 && (cell - target).LengthSquared > distanceRequirement * distanceRequirement)
						continue;

					if (ownBuildingBuffer != null && !bi.AllowInvalidPlacement && bi.Tiles(cell).Any(ownBuildingBuffer.Contains))
						continue;

					return (cell, center, actorVariant);
				}
			}

			return (null, center, 0);
		}

		// Cameo (building spacing): every cell within `gap` cells of an own building's footprint —
		// the buffer zone a new footprint must not overlap. Symmetric check: a candidate is rejected
		// when one of its footprint cells lands in this set.
		HashSet<CPos> OwnBuildingBufferCells(int gap)
		{
			if (playerBuildings == null)
				return new HashSet<CPos>();

			return BuildingGapRule.BufferCells(
				playerBuildings.SelectMany(b => b.Info.TraitInfoOrDefault<BuildingInfo>()?.Tiles(b.Location) ?? Enumerable.Empty<CPos>()), gap);
		}

		// Cameo: ask the first ACTIVE defence-placement advisor (resolved on each use, so a late-enabled one is seen)
		// for a cell. canPlace is the check findPos applies.
		CPos? AdvisedDefenseCell(ActorInfo actorInfo, bool distanceToBaseIsImportant, Actor producer)
		{
			var advisor = player.PlayerActor.TraitsImplementing<IBotDefensePlacementAdvisor>().FirstOrDefault(a => a.IsActive);
			var bi = actorInfo.TraitInfoOrDefault<BuildingInfo>();
			if (advisor == null || bi == null)
				return null;

			var baseCenter = baseBuilder.GetBaseCenterForActor(actorInfo);

			// The advisor's candidate cells get the same spacing rule as findPos defenses.
			var gap = BuildingGapRule.Resolve(player.PlayerActor.TraitsImplementing<IBotPlacementAdvisor>().FirstOrDefault(a => a.IsActive), true);
			var ownBuildingBuffer = gap > 0 ? OwnBuildingBufferCells(gap) : null;

			return advisor.ChooseDefenseCell(actorInfo, baseBuilder.Info.AntiAirTypes.Contains(actorInfo.Name), baseCenter,
				cell => world.CanPlaceBuilding(cell, actorInfo, bi, null)
					&& (!distanceToBaseIsImportant || bi.IsCloseEnoughToBase(world, player, actorInfo, producer, cell))
					&& (ownBuildingBuffer == null || bi.AllowInvalidPlacement || !bi.Tiles(cell).Any(ownBuildingBuffer.Contains)));
		}

		(CPos? Location, CPos? BaseCenter, int Variant) ChooseBuildLocation(string actorType, bool distanceToBaseIsImportant, Actor producer, BuildingType type)
		{
			var baseCenter = baseBuilder.GetBaseCenterForActor(world.Map.Rules.Actors[actorType]);

			switch (type)
			{
				case BuildingType.Defense:

					// Build near the closest enemy structure
					var defenseCenter = baseBuilder.DefenseCenter ?? baseCenter;
					var closestEnemy = world.ActorsHavingTrait<Building>()
						.Where(a => !a.Disposed && player.RelationshipWith(a.Owner) == PlayerRelationship.Enemy)
						.ClosestToIgnoringPath(world.Map.CenterOfCell(defenseCenter));

					var targetCell = closestEnemy != null ? closestEnemy.Location : baseCenter;
					return findPos(actorType, distanceToBaseIsImportant, producer, defenseCenter, targetCell, baseBuilder.Info.MinimumDefenseRadius, baseBuilder.Info.MaximumDefenseRadius,
						defenseGap: true);

				case BuildingType.Fragile:
					// Build away from where enemy last attacked
					var fragileDefenseCenter = baseBuilder.DefenseCenter ?? baseCenter;
					return findPos(actorType, distanceToBaseIsImportant, producer, baseCenter, fragileDefenseCenter, baseBuilder.Info.MinBaseRadius,
						distanceToBaseIsImportant ? baseBuilder.Info.MaxBaseRadius : world.Map.Grid.MaximumTileSearchRange, sortMax: true);

				case BuildingType.Refinery:

					var requestRef = baseBuilder.RequestedRefineries.Count > 0 ? baseBuilder.RequestedRefineries.Keys.First() : null;

					// Cameo (AI_ARCHITECTURE §12.13, EX-2): the planner's field is in reach and unclaimed, so the refinery goes
					// there, close enough to count as claiming it. A refinery the MCV module requested keeps priority.
					var claimer = requestRef == null ? baseBuilder.ExpansionWantsRefinery() : null;
					if (claimer != null)
					{
						// EX-2c: the claim field may differ from the crawl aim — any free field already in
						// reach qualifies, so an outpost yard claims its local field without waiting to
						// become the crawl target. Null falls back to the expansion target (EX-2).
						var field = claimer.RefineryClaimTarget ?? claimer.ExpansionTarget.Value;

						// The annulus must be around the FIELD, not baseCenter: a crawled-to field sits beyond
						// baseCenter + MaxBaseRadius + claimRadius, so centering on the base yields zero candidate
						// cells, the claim silently fails, and the fallback drops the refinery back home.
						// FE-1 (§12.24): under the refinery law the field is an ANCHOR and the cell nearest it wins
						// (then the cell nearest the field's resource cells); the home-base fallback below is skipped,
						// because a refinery stacked at home is exactly what the law forbids (a failed attempt retries).
						var law = claimer.RefineryLawActive;
						var claim = law
							? findPos(actorType, distanceToBaseIsImportant, producer, field, field,
								0, claimer.ExpansionTargetClaimRadius, anchorTieBreak: claimer.RefineryClaimFieldCenter, anchorOrder: true)
							: findPos(actorType, distanceToBaseIsImportant, producer, field, baseCenter,
								0, claimer.ExpansionTargetClaimRadius);
						if (claim.Location != null)
						{
							Log.Write("debug", $"AI ({player.ClientIndex}): EX-2 refinery {actorType} at {claim.Location.Value} claims field {field} at tick {world.WorldTick}");
							refineryClaimed = true;
							return claim;
						}

						if (law)
							return (null, null, 0);
					}

					// Try and place the refinery near a resource field
					if (resourceLayer != null)
					{
						// If we have failed to place to the requested refinery point, try and place it near the base center
						var resourceBaseCenter = failCount > 0 ? baseCenter :
							(requestRef != null ? baseBuilder.RequestedRefineries[requestRef].ConyardLoc : (baseBuilder.ResourceConyardCenter ?? baseCenter));

						// If we have a ResourceMapModule, only consider the resource types it considers valuable
						// Otherwise consider any resource type
						var nearbyResources = world.Map
							.FindTilesInAnnulus(resourceBaseCenter, baseBuilder.Info.MinBaseRadius, baseBuilder.Info.MaxBaseRadius)
							.Where(c => baseBuilder.ResourceMapModule != null ?
							baseBuilder.ResourceMapModule.Info.ValuableResourceTypes.Contains(resourceLayer.GetResource(c).Type)
							: resourceLayer.GetResource(c).Type != null);

						// Find the closest refinery we have if we have any when not failing to place for the first time
						var closestRefinery = failCount <= 0
							? baseBuilder.RefineryBuildings.Actors.Where(a => !a.IsDead)?.ClosestToIgnoringPath(world.Map.CenterOfCell(resourceBaseCenter))
							: null;

						IEnumerable<CPos> resourcesShouldCheck = null;

						if (closestRefinery == null)
							resourcesShouldCheck = nearbyResources.Shuffle(world.LocalRandom).Take(baseBuilder.Info.MaxResourceCellsToCheck);
						else if (requestRef != null)
						{
							resourcesShouldCheck = nearbyResources.OrderBy(c => (c - baseBuilder.RequestedRefineries[requestRef].ResourceLoc).LengthSquared)
								.Take(baseBuilder.Info.MaxResourceCellsToCheck);
						}
						else
						{
							// Cameo (§12.13, EX-2): an expansion planner wants every field served — sample only cells
							// of fields no own refinery covers yet, so refineries spread to new fields instead of
							// stacking on the far edge of the home field. No provider or no resource map (classic):
							// today's ordering, unchanged.
							var candidates = nearbyResources;
							if (baseBuilder.HasExpansionGuidance && baseBuilder.ResourceMapModule != null)
							{
								var ownRefineryCells = baseBuilder.RefineryBuildings.Actors
									.Where(a => !a.IsDead)
									.Select(a => a.Location)
									.ToList();
								candidates = BaseBuilderBotModuleCA.PreferUnservedResourceCells(
									nearbyResources,
									c => baseBuilder.ResourceMapModule.FindClosestIndiceFromCPos(c).ResourceCellsCenter,
									ownRefineryCells, baseBuilder.Info.RefineryUnservedRadiusCells);
							}

							resourcesShouldCheck = candidates.OrderByDescending(c => (c - closestRefinery.Location).LengthSquared)
								.Take(baseBuilder.Info.MaxResourceCellsToCheck);
						}

						foreach (var r in resourcesShouldCheck)
						{
							var found = findPos(actorType, distanceToBaseIsImportant, producer, resourceBaseCenter, r, baseBuilder.Info.MinBaseRadius, baseBuilder.Info.MaxBaseRadius);
							if (found.Location != null)
							{
								if (baseBuilder.RequestedRefineries.Count > 0)
									baseBuilder.RequestedRefineries.Remove(requestRef);
								return found;
							}
						}
					}

					if (baseBuilder.RequestedRefineries.Count > 0)
						baseBuilder.RequestedRefineries.Remove(requestRef);

					// Try and find a free spot somewhere else in the base
					return findPos(actorType, distanceToBaseIsImportant, producer, baseCenter, baseCenter, baseBuilder.Info.MinBaseRadius, baseBuilder.Info.MaxBaseRadius);

				case BuildingType.BaseCrawl:

					// Cameo (AI_ARCHITECTURE §12.13, EX-1): walk toward the planner's target field, one building at a
					// time (findPos takes the placeable cell nearest the target), instead of a random resource cell or
					// the enemy building found by scanning every building on the map.
					var expansionTarget = baseBuilder.ExpansionTarget();
					if (expansionTarget != null)
					{
						var toward = findPos(actorType, distanceToBaseIsImportant, producer, baseCenter, expansionTarget.Value,
							baseBuilder.Info.MinBaseRadius, baseBuilder.Info.BaseCrawlRadius);
						if (toward.Location != null)
						{
							Log.Write("debug", $"AI ({player.ClientIndex}): EX-1 BaseCrawl {actorType} at {toward.Location.Value} toward field {expansionTarget.Value} at tick {world.WorldTick}");
							return toward;
						}
					}

					// Try and place the refinery near a resource field
					if (resourceLayer != null)
					{
						var nearbyResources = world.Map.FindTilesInAnnulus(baseCenter, baseBuilder.Info.MinBaseRadius, baseBuilder.Info.BaseCrawlRadius)
							.Where(a => resourceLayer.GetResource(a).Type != null)
							.Shuffle(world.LocalRandom).Take(baseBuilder.Info.MaxResourceCellsToCheck);

						foreach (var r in nearbyResources)
						{
							var found = findPos(actorType, distanceToBaseIsImportant, producer, baseCenter, r, baseBuilder.Info.MinBaseRadius, baseBuilder.Info.MaxBaseRadius);
							if (found.Location != null)
								return found;
						}
					}

					// Try and find a free spot somewhere else in the base
					var crawlDefenseCenter = baseBuilder.DefenseCenter ?? baseCenter;
					closestEnemy = world.ActorsHavingTrait<Building>()
						.Where(a => !a.Disposed && player.RelationshipWith(a.Owner) == PlayerRelationship.Enemy)
						.ClosestToIgnoringPath(world.Map.CenterOfCell(crawlDefenseCenter));

					targetCell = closestEnemy != null ? closestEnemy.Location : baseCenter;

					// Defense-style placement (defense center, defense radii, toward the enemy):
					// gets the tighter defense gap like BuildingType.Defense.
					return findPos(actorType, distanceToBaseIsImportant, producer, crawlDefenseCenter, targetCell, baseBuilder.Info.MinimumDefenseRadius, baseBuilder.Info.MaximumDefenseRadius,
						defenseGap: true);

				case BuildingType.Building:
					return findPos(actorType, distanceToBaseIsImportant, producer, baseCenter, baseCenter, baseBuilder.Info.MinBaseRadius,
						distanceToBaseIsImportant ? baseBuilder.Info.MaxBaseRadius : world.Map.Grid.MaximumTileSearchRange);
			}

			// Can't find a build location
			return (null, null, 0);
		}

		void SetBuildingInterval(string name)
		{
			if (baseBuilder.Info.BuildingIntervals == null || !baseBuilder.Info.BuildingIntervals.ContainsKey(name))
				return;

			activeBuildingIntervals[name] = KnobTicks(baseBuilder.Info.BuildingIntervals[name] * buildingIntervalModifier / 100, name);
		}
	}
}
