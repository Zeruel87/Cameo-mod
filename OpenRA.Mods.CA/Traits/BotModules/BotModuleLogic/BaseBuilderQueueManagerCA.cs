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

		Actor[] playerBuildings = [];
		int failCount;

		// Cameo: effective spacing request for this tick. The shared @generic instance also serves
		// classicbot, and the A/B keeps classic as the untouched reference — spacing only applies to
		// genericbot bots. Resolved in Tick; 0 disables the findPos clearance check.
		int spacingGate;
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

		// BotLimits carries the per-difficulty value on the DESIGN §19.1 line; negative there means the module's own.
		int NewProductionCashThreshold => botLimits != null && botLimits.Info.NewProductionCashThreshold >= 0
			? botLimits.Info.NewProductionCashThreshold : baseBuilder.Info.NewProductionCashThreshold;

		public void Tick(IBot bot)
		{
			spacingGate = bot.Info.Type == "classic" ? 0 : baseBuilder.Info.MinimumStructureSpacingCells;

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

				baseBuilder.RecordOpeningStructureQueued(queue, item);
				bot.QueueOrder(Order.StartProduction(queue.Actor, item.Name, 1));
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
				if (baseBuilder.Info.BuildingLimits.ContainsKey(currentBuilding.Item))
				{
					if ((AIUtils.CountBuildingByCommonName(new HashSet<string> { currentBuilding.Item }, player) >= baseBuilder.Info.BuildingLimits[currentBuilding.Item]))
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

		ActorInfo GetProducibleBuilding(IReadOnlySet<string> actors, IEnumerable<ActorInfo> buildables, Func<ActorInfo, int> orderBy = null)
		{
			var available = buildables.Where(actor =>
			{
				// Are we able to build this?
				if (!actors.Contains(actor.Name))
					return false;

				if (!baseBuilder.Info.BuildingLimits.TryGetValue(actor.Name, out var limit))
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
				.Sum(p => p.Amount) + playerPower.ExcessPower) >= baseBuilder.Info.MinimumExcessPower;
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

			// Make sure that we can spend as fast as we are earning
			if (NewProductionCashThreshold > 0 && playerResources.GetCashAndResources() > NewProductionCashThreshold)
			{
				var production = GetProducibleBuilding(baseBuilder.Info.ProductionTypes, buildableThings);

				if (production != null && (productionTypeLimit <= 0 || playerBuildings.Count(a => a.Info.Name == production.Name) < productionTypeLimit))
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
					delay * buildingDelayModifier / 100 > world.WorldTick)
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
				if (count * 100 > frac.Value * playerBuildings.Length)
					continue;

				if (botLimits != null && baseBuilder.Info.ProductionTypes.Contains(name) && count >= botLimits.Info.ProductionTypeLimit)
				{
					AIUtils.BotDebug("{0} decided to build {1} but limit of {2} already reached)", queue.Actor.Owner, name, botLimits.Info.ProductionTypeLimit);
					continue;
				}

				if (baseBuilder.Info.BuildingLimits.TryGetValue(name, out var limit) && limit <= count)
				{
					AIUtils.BotDebug("{0} decided to build {1} but limit of {2} already reached)", queue.Actor.Owner, name, baseBuilder.Info.BuildingLimits[name]);
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

		// Smallest rectangular gap, in empty cells, between the candidate footprint at `cell` and every
		// standing own building (playerBuildings, refreshed each Tick) — 0 means touching. Ported from
		// Fransbot's StructureClearance; a candidate on an empty base counts as meeting the request.
		int StructureClearance(CPos cell, BuildingInfo candidateInfo, int minSpacing)
		{
			var minimum = int.MaxValue;
			foreach (var existing in playerBuildings)
			{
				if (existing == null || existing.IsDead || !existing.IsInWorld)
					continue;

				var info = existing.Info.TraitInfoOrDefault<BuildingInfo>();
				if (info == null)
					continue;

				minimum = Math.Min(minimum,
					BaseBuilderBotModuleCA.FootprintGap(cell, candidateInfo.Dimensions, existing.Location, info.Dimensions));
				if (minimum == 0)
					break;
			}

			return minimum == int.MaxValue ? minSpacing : minimum;
		}

		// Find the buildable cell that is closest to pos and centered around center
		(CPos? Location, CPos Center, int Variant) findPos(string actorType, bool distanceToBaseIsImportant, Actor producer, CPos center, CPos target, int minRange, int maxRange, int distanceRequirement = 0, bool sortMax = false, int minSpacing = 0)
		{
			var actorInfo = world.Map.Rules.Actors[actorType];
			var actorVariant = 0;
			var buildingVariantInfo = actorInfo.TraitInfoOrDefault<PlaceBuildingVariantsInfo>();
			var bi = actorInfo.TraitInfoOrDefault<BuildingInfo>();
			if (bi == null)
				return (null, center, 0);

			var cells = world.Map.FindTilesInAnnulus(center, minRange, maxRange);

			// Sort by distance to target if we have one
			if (center != target)
			{
				cells = sortMax ? cells.OrderByDescending(c => (c - target).LengthSquared) : cells.OrderBy(c => (c - target).LengthSquared);

				// Rotate building if we have a Facings in buildingVariantInfo.
				// If we don't have Facings in buildingVariantInfo, use a random variant
				if (buildingVariantInfo?.Actors != null)
				{
					if (buildingVariantInfo.Facings != null)
					{
						var vector = world.Map.CenterOfCell(target) - world.Map.CenterOfCell(center);

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

			// Cameo (MinimumStructureSpacingCells): the gap is an ideal, not a hard rule. Keep the first
			// legal cell meeting it; otherwise remember the legal cell with the widest gap and return it
			// after the scan — a soft preference, never a placement failure. Ties keep the first cell in
			// enumeration order (the existing distance/shuffle ordering), so no new randomness.
			CPos? widestFallback = null;
			var widestClearance = -1;

			foreach (var cell in cells)
			{
				if (!world.CanPlaceBuilding(cell, actorInfo, bi, null))
					continue;

				if (distanceToBaseIsImportant && !bi.IsCloseEnoughToBase(world, player, actorInfo, producer, cell))
					continue;

				if (distanceRequirement > 0 && (cell - target).LengthSquared > distanceRequirement * distanceRequirement)
					continue;

				if (minSpacing > 0)
				{
					var clearance = StructureClearance(cell, bi, minSpacing);
					if (clearance >= minSpacing)
						return (cell, center, actorVariant);

					if (clearance > widestClearance)
					{
						widestClearance = clearance;
						widestFallback = cell;
					}

					continue;
				}

				return (cell, center, actorVariant);
			}

			if (widestFallback != null)
				return (widestFallback, center, actorVariant);

			return (null, center, 0);
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
			return advisor.ChooseDefenseCell(actorInfo, baseBuilder.Info.AntiAirTypes.Contains(actorInfo.Name), baseCenter,
				cell => world.CanPlaceBuilding(cell, actorInfo, bi, null)
					&& (!distanceToBaseIsImportant || bi.IsCloseEnoughToBase(world, player, actorInfo, producer, cell)));
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
					return findPos(actorType, distanceToBaseIsImportant, producer, defenseCenter, targetCell, baseBuilder.Info.MinimumDefenseRadius, baseBuilder.Info.MaximumDefenseRadius);

				case BuildingType.Fragile:
					// Build away from where enemy last attacked
					var fragileDefenseCenter = baseBuilder.DefenseCenter ?? baseCenter;
					return findPos(actorType, distanceToBaseIsImportant, producer, baseCenter, fragileDefenseCenter, baseBuilder.Info.MinBaseRadius,
						distanceToBaseIsImportant ? baseBuilder.Info.MaxBaseRadius : world.Map.Grid.MaximumTileSearchRange, sortMax: true,
						minSpacing: spacingGate);

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
						var claim = findPos(actorType, distanceToBaseIsImportant, producer, field, baseCenter,
							0, claimer.ExpansionTargetClaimRadius);
						if (claim.Location != null)
						{
							Log.Write("debug", $"AI ({player.ClientIndex}): EX-2 refinery {actorType} at {claim.Location.Value} claims field {field} at tick {world.WorldTick}");
							return claim;
						}
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
							baseBuilder.Info.MinBaseRadius, baseBuilder.Info.BaseCrawlRadius,
							minSpacing: spacingGate);
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
							var found = findPos(actorType, distanceToBaseIsImportant, producer, baseCenter, r, baseBuilder.Info.MinBaseRadius, baseBuilder.Info.MaxBaseRadius,
								minSpacing: spacingGate);
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
					return findPos(actorType, distanceToBaseIsImportant, producer, crawlDefenseCenter, targetCell, baseBuilder.Info.MinimumDefenseRadius, baseBuilder.Info.MaximumDefenseRadius,
						minSpacing: spacingGate);

				case BuildingType.Building:
					return findPos(actorType, distanceToBaseIsImportant, producer, baseCenter, baseCenter, baseBuilder.Info.MinBaseRadius,
						distanceToBaseIsImportant ? baseBuilder.Info.MaxBaseRadius : world.Map.Grid.MaximumTileSearchRange,
						minSpacing: spacingGate);
			}

			// Can't find a build location
			return (null, null, 0);
		}

		void SetBuildingInterval(string name)
		{
			if (baseBuilder.Info.BuildingIntervals == null || !baseBuilder.Info.BuildingIntervals.ContainsKey(name))
				return;

			activeBuildingIntervals[name] = baseBuilder.Info.BuildingIntervals[name] * buildingIntervalModifier / 100;
		}
	}
}
