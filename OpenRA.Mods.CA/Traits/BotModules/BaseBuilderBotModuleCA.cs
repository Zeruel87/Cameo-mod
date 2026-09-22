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
using System.Collections.Frozen;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Linq;
using OpenRA.Mods.AS.Traits;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Manages AI base construction.")]
	public class BaseBuilderBotModuleCAInfo : ConditionalTraitInfo, NotBefore<ResourceMapBotModuleInfo>, NotBefore<IResourceLayerInfo>
	{
		[Desc("Tells the AI what building types are considered construction yards.")]
		public readonly FrozenSet<string> ConstructionYardTypes = FrozenSet<string>.Empty;

		[Desc("Tells the AI what building types are considered vehicle production facilities.")]
		public readonly FrozenSet<string> VehiclesFactoryTypes = FrozenSet<string>.Empty;

		[Desc("Tells the AI what building types are considered refineries.")]
		public readonly FrozenSet<string> RefineryTypes = FrozenSet<string>.Empty;

		[Desc("Tells the AI what building types are considered power plants.")]
		public readonly FrozenSet<string> PowerTypes = FrozenSet<string>.Empty;

		[Desc("Tells the AI what building types are considered infantry production facilities.")]
		public readonly FrozenSet<string> BarracksTypes = FrozenSet<string>.Empty;

		[Desc("Factions that may prioritize their first barracks before their first refinery when enabled by BotLimits.")]
		public readonly FrozenSet<string> BarracksBeforeRefineryFactions = FrozenSet<string>.Empty;

		[Desc("Tells the AI what building types are considered anti-air defenses.")]
		public readonly FrozenSet<string> AntiAirTypes = FrozenSet<string>.Empty;

		[Desc("Tells the AI what building types are considered defenses.")]
		public readonly FrozenSet<string> DefenseTypes = FrozenSet<string>.Empty;

		[Desc("Tells the AI what building types are considered production facilities.")]
		public readonly FrozenSet<string> ProductionTypes = FrozenSet<string>.Empty;

		[Desc("Tells the AI what building types are considered naval production facilities.")]
		public readonly FrozenSet<string> NavalProductionTypes = FrozenSet<string>.Empty;

		[Desc("Tells the AI what building types are considered silos (resource storage).")]
		public readonly FrozenSet<string> SiloTypes = FrozenSet<string>.Empty;

		[Desc("Tells the AI what building types are considered fragile.")]
		public readonly FrozenSet<string> FragileTypes = FrozenSet<string>.Empty;

		[Desc("Production queues AI uses for buildings.")]
		public readonly FrozenSet<string> BuildingQueues = new HashSet<string> { "Building" }.ToFrozenSet();

		[Desc("Production queues AI uses for defenses.")]
		public readonly FrozenSet<string> DefenseQueues = new HashSet<string> { "Defense" }.ToFrozenSet();

		[Desc("Minimum distance in cells from center of the base when checking for building placement.")]
		public readonly int MinBaseRadius = 2;

		[Desc("Radius in cells around the center of the base to expand.")]
		public readonly int MaxBaseRadius = 20;

		[Desc("Maximum number of extra refineries to build (in addition to RefineriesPerBase per construction yard).")]
		public readonly int MaxExtraRefineries = 1;

		[Desc("Number of refineries per construction yard.")]
		public readonly int RefineriesPerBase = 2;

		[Desc("Minimum excess power the AI should try to maintain.")]
		public readonly int MinimumExcessPower = 0;

		[Desc("The targeted excess power the AI tries to maintain cannot rise above this.")]
		public readonly int MaximumExcessPower = 0;

		[Desc("Increase maintained excess power by this amount for every ExcessPowerIncreaseThreshold of base buildings.")]
		public readonly int ExcessPowerIncrement = 0;

		[Desc("Increase maintained excess power by ExcessPowerIncrement for every N base buildings.")]
		public readonly int ExcessPowerIncreaseThreshold = 1;

		[Desc("Number of refineries to build before building any production building.")]
		public readonly int InititalMinimumRefineryCount = 1;

		[Desc("Number of refineries to build additionally after building any production building.")]
		public readonly int AdditionalMinimumRefineryCount = 1;

		[Desc("Additional delay (in ticks) between structure production checks when there is no active production.",
			"StructureProductionRandomBonusDelay is added to this.")]
		public readonly int StructureProductionInactiveDelay = 125;

		[Desc("Additional delay (in ticks) added between structure production checks when actively building things.",
			"Note: this should be at least as large as the typical order latency to avoid duplicated build choices.")]
		public readonly int StructureProductionActiveDelay = 25;

		[Desc("A random delay (in ticks) of up to this is added to active/inactive production delays.")]
		public readonly int StructureProductionRandomBonusDelay = 10;

		[Desc("Delay (in ticks) until retrying to build structure after the last 3 consecutive attempts failed.")]
		public readonly int StructureProductionResumeDelay = 1500;

		[Desc("After how many failed attempts to place a structure should AI give up and wait",
			"for StructureProductionResumeDelay before retrying.")]
		public readonly int MaximumFailedPlacementAttempts = 3;

		[Desc("How many randomly chosen cells with resources to check when deciding refinery placement.")]
		public readonly int MaxResourceCellsToCheck = 3;

		[Desc("Delay (in ticks) until rechecking for new BaseProviders.")]
		public readonly int CheckForNewBasesDelay = 1500;

		[Desc("Chance that the AI will place the defenses in the direction of the closest enemy building.")]
		public readonly int PlaceDefenseTowardsEnemyChance = 100;

		[Desc("Chance that the AI will place buildings to crawl toward resource patches.")]
		public readonly int BaseCrawlChance = 50;

		[Desc("Maximum range at which to basecrawl.")]
		public readonly int BaseCrawlRadius = 50;

		[Desc("Structures cheaper than this will be used to basecrawl.")]
		public readonly int BaseCrawlCostThreshold = 1000;

		[Desc("Minimum range at which to build defensive structures near a combat hotspot.")]
		public readonly int MinimumDefenseRadius = 5;

		[Desc("Maximum range at which to build defensive structures near a combat hotspot.")]
		public readonly int MaximumDefenseRadius = 20;

		[Desc("Try to build another production building if there is too much cash.")]
		public readonly int NewProductionCashThreshold = 10000;

		[Desc("Only queue construction of a new building when above this requirement.")]
		public readonly int BuildingProductionMinCashRequirement = 1750;

		[Desc("Only queue construction of a new defense when above this requirement.")]
		public readonly int DefenseProductionMinCashRequirement = 2250;

		[Desc("Radius in cells around a factory scanned for rally points by the AI.")]
		public readonly int RallyPointScanRadius = 8;

		[Desc("Radius in cells around each building with ProvideBuildableArea",
			"to check for a 3x3 area of water where naval structures can be built.",
			"Should match maximum adjacency of naval structures.")]
		public readonly int CheckForWaterRadius = 8;

		[Desc("Terrain types which are considered water for base building purposes.")]
		public readonly FrozenSet<string> WaterTerrainTypes = new HashSet<string> { "Water" }.ToFrozenSet();

		[Desc("What buildings to the AI should build.", "What integer percentage of the total base must be this type of building.")]
		public readonly FrozenDictionary<string, int> BuildingFractions = null;

		[Desc("What buildings should the AI have a maximum limit to build.")]
		public readonly FrozenDictionary<string, int> BuildingLimits = null;

		[Desc("When should the AI start building specific buildings.")]
		public readonly FrozenDictionary<string, int> BuildingDelays = null;

		[Desc("Minimum duration between building specific buildings.")]
		public readonly FrozenDictionary<string, int> BuildingIntervals = null;

		[Desc("Delay (in ticks) between reassigning rally points.")]
		public readonly int AssignRallyPointsInterval = 100;

		[Desc("Delay (in ticks) for finding a good resource to place a refinery next to.")]
		public readonly int CheckBestResourceLocationInterval = 151;

		[Desc("Interval (in ticks) between checking whether to sell a redundant refinery. Set to -1 to disable.")]
		public readonly int SellRefineryInterval = 5000;

		[Desc("Distance (in cells) for refineries finding redundant refineries.")]
		public readonly int SellRefineryTooCloseCellDistance = 6;

		[Desc("Maximum distance (in cells) from resources before refineries are eligible to be sold.")]
		public readonly int SellRefineryNoResourceDistance = 12;

		[Desc("Maximum refinery count per area. Area size is defined in " + nameof(ResourceMapBotModule) + ".")]
		public readonly int MaxRefineryPerIndice = 2;

		[Desc($"AI will move mcv when those numbers of refinery <= productions + tech - {nameof(ExpansionTolerate)}.")]
		public readonly ImmutableArray<int> ExpansionTolerate = [0, 1];

		[Desc($"AI will move the only mcv when those numbers of refinery <= productions + tech - {nameof(ForceExpansionTolerate)}.")]
		public readonly ImmutableArray<int> ForceExpansionTolerate = [2, 3];

		[Desc("Decrease the expansion tolerate by Cash / this. Used to prevent AI from expanding when it has enough cash.")]
		public readonly int PerExpansionTolerateOnCash = 12000;

		[Desc("Enemy building target types I can ignore construction distance from.")]
		public readonly BitSet<TargetableType> IgnoredEnemyBuildingTargetTypes = default(BitSet<TargetableType>);

		[Desc("Unit target types I should not count when scanning for sell condition .")]
		public readonly BitSet<TargetableType> IgnoredUnitTargetTypes = default(BitSet<TargetableType>);

		[Desc("Radius in cells around building being considered for sale to scan for units")]
		public readonly int SellScanRadius = 8;

		public override object Create(ActorInitializer init) { return new BaseBuilderBotModuleCA(init.Self, this); }
	}

	public class BaseBuilderBotModuleCA : ConditionalTrait<BaseBuilderBotModuleCAInfo>, IGameSaveTraitData,
		IBotTick, IBotPositionsUpdated, IBotRespondToAttack, IBotRequestPauseUnitProduction, IBotSuggestRefineryProduction, INotifyActorDisposing
	{
		public CPos GetRandomBaseCenter()
		{
			var randomConstructionYard = ConstructionYardBuildings.Actors.Where(a => !a.IsDead)
				.RandomOrDefault(world.LocalRandom);

			return randomConstructionYard?.Location ?? initialBaseCenter;
		}

		// Resolves the exact construction yard actor type that this building's Prerequisites
		// (after inheritance flattening) requires, or null if it doesn't require one specific
		// construction yard type (e.g. faction-agnostic shared buildings like ra1_powerplant
		// which use a generic "~rafact" token satisfied by any RA1 construction yard).
		public string GetRequiredConstructionYardType(ActorInfo actorInfo)
		{
			var bi = actorInfo.TraitInfoOrDefault<BuildableInfo>();
			if (bi == null)
				return null;

			foreach (var prereq in bi.Prerequisites)
			{
				var name = prereq.Replace("~", string.Empty).Replace("!", string.Empty);
				if (Info.ConstructionYardTypes.Contains(name))
					return name;
			}

			return null;
		}

		// Anchor placement/expansion checks on a construction yard belonging to the same
		// faction as the building being placed, rather than a random construction yard from
		// any faction. This matters when the player owns construction yards from multiple
		// factions at once (e.g. a stray enemy MCV of a different faction deployed into an
		// existing base) - otherwise a crowded main base can starve a smaller secondary base
		// of the same faction from ever finding room to build, since GetRandomBaseCenter()
		// might repeatedly anchor searches on the wrong (unrelated) faction's construction yard.
		public CPos GetBaseCenterForActor(ActorInfo actorInfo)
		{
			var conyardType = GetRequiredConstructionYardType(actorInfo);
			if (conyardType != null)
			{
				var matchingConstructionYard = ConstructionYardBuildings.Actors
					.Where(a => !a.IsDead && a.Info.Name == conyardType)
					.RandomOrDefault(world.LocalRandom);

				if (matchingConstructionYard != null)
					return matchingConstructionYard.Location;
			}

			return GetRandomBaseCenter();
		}

		public CPos GetDefenseBaseCenter()
		{
			var defenceConstructionYard = DefenseCenter != null ? ConstructionYardBuildings.Actors.OrderBy(a => (DefenseCenter.Value - a.Location).LengthSquared)
				.FirstOrDefault(a => !a.IsDead) : null;

			return defenceConstructionYard?.Location ?? GetRandomBaseCenter();
		}

		public CPos? DefenseCenter { get; private set; }

		/// <Summary> Actor, ActorCount </Summary>
		public Dictionary<string, int> BuildingsBeingProduced = [];
		public IBotBaseExpansion[] BaseExpansionModules;
		public ResourceMapBotModule ResourceMapModule;
		public Actor RelocationHoldConyard { get; set; }

		readonly World world;
		readonly Player player;
		PlayerResources playerResources;
		IResourceLayer resourceLayer;
		IPathFinder pathFinder;
		IBotPositionsUpdated[] positionsUpdatedModules;
		CPos initialBaseCenter;
		public CPos? ResourceConyardCenter;
		public Dictionary<Actor, (CPos ConyardLoc, CPos ResourceLoc)> RequestedRefineries = [];

		readonly Stack<TraitPair<RallyPoint>> rallyPoints = [];
		int assignRallyPointsTicks;
		int checkBestResourceLocationTicks;
		int sellRefineryTick;
		bool firstTick = true;
		bool openingBarracksPriorityCompleted;
		bool openingStartingCashCaptured;
		bool openingBarracksCostCommitted;
		bool openingRefineryCostCommitted;
		int openingStartingCash;
		int openingPowerCommittedCost;
		int openingBarracksCommittedCost;
		int openingRefineryCommittedCost;
		int openingDefenseCommittedCost;

		readonly BaseBuilderQueueManagerCA[] builders;
		int currentBuilderIndex = 0;

		public readonly ActorIndex.OwnerAndNamesAndTrait<RefineryInfo> RefineryBuildings;
		readonly ActorIndex.OwnerAndNamesAndTrait<BuildingInfo> powerBuildings;
		public readonly ActorIndex.OwnerAndNamesAndTrait<BuildingInfo> ConstructionYardBuildings;
		readonly ActorIndex.OwnerAndNamesAndTrait<BuildingInfo> barracksBuildings;
		readonly ActorIndex.OwnerAndNamesAndTrait<BuildingInfo> factoryBuildings;
		public readonly ActorIndex.OwnerAndNamesAndTrait<BuildingInfo> ProductionBuildings;

		BotLimits botLimits;
		int refineryLimit;

		public PowerManager PlayerPower { get; private set; }
		public int ExcessPower { get; private set; }

		public BaseBuilderBotModuleCA(Actor self, BaseBuilderBotModuleCAInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			builders = new BaseBuilderQueueManagerCA[info.BuildingQueues.Count + info.DefenseQueues.Count];
			RefineryBuildings = new ActorIndex.OwnerAndNamesAndTrait<RefineryInfo>(world, info.RefineryTypes, player);
			powerBuildings = new ActorIndex.OwnerAndNamesAndTrait<BuildingInfo>(world, info.PowerTypes, player);
			ConstructionYardBuildings = new ActorIndex.OwnerAndNamesAndTrait<BuildingInfo>(world, info.ConstructionYardTypes, player);
			barracksBuildings = new ActorIndex.OwnerAndNamesAndTrait<BuildingInfo>(world, info.BarracksTypes, player);
			factoryBuildings = new ActorIndex.OwnerAndNamesAndTrait<BuildingInfo>(world, info.VehiclesFactoryTypes, player);
			ProductionBuildings = new ActorIndex.OwnerAndNamesAndTrait<BuildingInfo>(world, info.ProductionTypes, player);
		}

		// Use for proactive targeting.
		public bool IsEnemyGroundUnit(Actor a)
		{
			if (a == null || a.IsDead || player.RelationshipWith(a.Owner) != PlayerRelationship.Enemy || a.Info.HasTraitInfo<HuskInfo>() || a.Info.HasTraitInfo<AircraftInfo>() || a.Info.HasTraitInfo<CarrierSlaveInfo>())
				return false;

			var targetTypes = a.GetEnabledTargetTypes();
			return !targetTypes.IsEmpty && !targetTypes.Overlaps(Info.IgnoredUnitTargetTypes);
		}

		public bool IsAllyGroundUnit(Actor a)
		{
			if (a == null || a.IsDead || player.RelationshipWith(a.Owner) != PlayerRelationship.Ally || a.Info.HasTraitInfo<HuskInfo>() || a.Info.HasTraitInfo<AircraftInfo>() || a.Info.HasTraitInfo<CarrierSlaveInfo>())
				return false;

			var targetTypes = a.GetEnabledTargetTypes();
			return !targetTypes.IsEmpty && !targetTypes.Overlaps(Info.IgnoredUnitTargetTypes);
		}

		protected override void Created(Actor self)
		{
			PlayerPower = self.Owner.PlayerActor.TraitOrDefault<PowerManager>();
			playerResources = self.Owner.PlayerActor.Trait<PlayerResources>();
			resourceLayer = self.World.WorldActor.TraitOrDefault<IResourceLayer>();
			pathFinder = self.World.WorldActor.TraitOrDefault<IPathFinder>();
			positionsUpdatedModules = self.Owner.PlayerActor.TraitsImplementing<IBotPositionsUpdated>().ToArray();
			BaseExpansionModules = self.Owner.PlayerActor.TraitsImplementing<IBotBaseExpansion>().ToArray();

			var i = 0;

			foreach (var building in Info.BuildingQueues)
				builders[i++] = new BaseBuilderQueueManagerCA(this, building, player, PlayerPower, playerResources, resourceLayer);

			foreach (var defense in Info.DefenseQueues)
				builders[i++] = new BaseBuilderQueueManagerCA(this, defense, player, PlayerPower, playerResources, resourceLayer);
		}

		protected override void TraitEnabled(Actor self)
		{
			RefreshBotLimits();

			// Avoid all AIs reevaluating assignments on the same tick, randomize their initial evaluation delay.
			assignRallyPointsTicks = world.LocalRandom.Next(0, Info.AssignRallyPointsInterval);
			checkBestResourceLocationTicks = world.LocalRandom.Next(0, Info.CheckBestResourceLocationInterval);
			sellRefineryTick = Info.SellRefineryInterval < 0 ? 0 : world.LocalRandom.Next(0, Info.SellRefineryInterval);
		}

		void IBotPositionsUpdated.UpdatedBaseCenter(CPos newLocation)
		{
			initialBaseCenter = newLocation;
		}

		void IBotPositionsUpdated.UpdatedDefenseCenter(CPos newLocation)
		{
			DefenseCenter = newLocation;
		}

		bool IBotRequestPauseUnitProduction.PauseUnitProduction => !IsTraitDisabled && !HasMinimalRefineryCount();

		void IBotTick.BotTick(IBot bot)
		{
			if (firstTick)
			{
				// Conditional traits are initialized after INotifyCreated, so resolve difficulty limits again here.
				RefreshBotLimits();
				if (!openingStartingCashCaptured)
				{
					openingStartingCash = playerResources.GetCashAndResources();
					openingStartingCashCaptured = true;
				}

				ResourceMapModule = bot.Player.PlayerActor.TraitsImplementing<ResourceMapBotModule>().FirstOrDefault(t => t.IsTraitEnabled());
				firstTick = false;
			}

			if (!openingBarracksPriorityCompleted && AIUtils.CountActorByCommonName(barracksBuildings) > 0)
				openingBarracksPriorityCompleted = true;

			if (RelocationHoldConyard != null &&
				(!RelocationHoldConyard.IsInWorld || RelocationHoldConyard.IsDead ||
				!BaseExpansionModules.Any(be => be.IsConyardRelocationPending(RelocationHoldConyard))))
				RelocationHoldConyard = null;

			if (--assignRallyPointsTicks <= 0)
			{
				assignRallyPointsTicks = Math.Max(2, Info.AssignRallyPointsInterval);
				foreach (var rp in world.ActorsWithTrait<RallyPoint>().Where(rp => rp.Actor.Owner == player))
					rallyPoints.Push(rp);
			}
			else
			{
				// PERF: Spread out rally point assignments updates across multiple ticks.
				var updateCount = Exts.IntegerDivisionRoundingAwayFromZero(rallyPoints.Count, assignRallyPointsTicks);
				for (var i = 0; i < updateCount; i++)
				{
					var rp = rallyPoints.Pop();
					if (rp.Actor.Owner == player && !rp.Actor.Disposed)
						SetRallyPoint(bot, rp);
				}
			}

			if (--checkBestResourceLocationTicks <= 0 && resourceLayer != null)
			{
				checkBestResourceLocationTicks = Info.CheckBestResourceLocationInterval;

				// Clear outdated refinery requests that add too many refinery to a map indice
				if (ResourceMapModule != null)
				{
					foreach (var mcv in RequestedRefineries.Keys.ToList())
					{
						if (ResourceMapModule.FindClosestIndiceFromCPos(
							RequestedRefineries[mcv].ResourceLoc).PlayerRefineryCount >= Info.MaxRefineryPerIndice)
							RequestedRefineries.Remove(mcv);
					}
				}

				Actor bestconyard = null;
				var best = int.MinValue;

				foreach (var conyard in ConstructionYardBuildings.Actors)
				{
					if (conyard.IsDead)
						continue;

					if (!world.Map.FindTilesInAnnulus(conyard.Location, Info.MinBaseRadius, Info.MaxBaseRadius)
						.Any(c => ResourceMapModule != null
						? ResourceMapModule.Info.ValuableResourceTypes.Contains(resourceLayer.GetResource(c).Type)
						: resourceLayer.GetResource(c).Type != null))
						continue;

					var refs = world.FindActorsInCircle(conyard.CenterPosition, WDist.FromCells(Info.MaxBaseRadius))
							.Count(a => a.Owner == player && Info.RefineryTypes.Contains(a.Info.Name));

					var suitable = -world.FindActorsInCircle(conyard.CenterPosition, WDist.FromCells(Info.MaxBaseRadius))
							.Count(a => a.Owner.RelationshipWith(player) == PlayerRelationship.Enemy) - refs;

					if (suitable > best)
					{
						best = suitable;
						bestconyard = conyard;
					}
				}

				ResourceConyardCenter = bestconyard?.Location;
			}

			BuildingsBeingProduced.Clear();

			// PERF: We tick only one type of valid queue at a time
			// if AI gets enough cash, it can fill all of its queues with enough ticks
			var findQueue = false;
			ExcessPower = PlayerPower != null ? PlayerPower.ExcessPower : 0;
			for (int i = 0, builderIndex = currentBuilderIndex; i < builders.Length; i++)
			{
				if (++builderIndex >= builders.Length)
					builderIndex = 0;

				--builders[builderIndex].WaitTicks;

				var queues = AIUtils.FindQueues(player, builders[builderIndex].Category).ToArray();
				if (queues.Length != 0)
				{
					if (!findQueue)
					{
						currentBuilderIndex = builderIndex;
						findQueue = true;
					}

					// Record buildings being produced only when AI can produce,
					// and record their power only when AI can produce
					if (playerResources.GetCashAndResources() >= Info.BuildingProductionMinCashRequirement)
					{
						foreach (var queue in queues)
						{
							// Record the number of the buildings.
							var producing = queue.AllQueued().FirstOrDefault();
							if (producing == null)
								continue;

							if (BuildingsBeingProduced.TryGetValue(producing.Item, out var value))
								BuildingsBeingProduced[producing.Item] = ++value;
							else
								BuildingsBeingProduced.Add(producing.Item, 1);

							// Record the power of the building.
							ExcessPower += producing.ActorInfo.TraitInfos<PowerInfo>().Where(p => p.EnabledByDefault).Sum(pi => pi.Amount);
						}
					}
				}
			}

			builders[currentBuilderIndex].Tick(bot);

			if (Info.SellRefineryInterval >= 0 && --sellRefineryTick <= 0)
			{
				SellUselessRefinery(bot);
				sellRefineryTick = Info.SellRefineryInterval;
			}
		}

		void RefreshBotLimits()
		{
			botLimits = player.PlayerActor.TraitsImplementing<BotLimits>().FirstEnabledTraitOrDefault();
			refineryLimit = botLimits?.Info.RefineryLimit ?? 0;

			foreach (var builder in builders)
				builder.SetBotLimits(botLimits);
		}

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			if (e.Attacker == null || e.Attacker.Disposed)
				return;

			if (e.Attacker.Owner.RelationshipWith(self.Owner) != PlayerRelationship.Enemy)
				return;

			if (!e.Attacker.Info.HasTraitInfo<ITargetableInfo>())
				return;

			if (!self.Info.HasTraitInfo<BuildingInfo>())
				return;

			if (ShouldSell(self, e))
			{
				bot.QueueOrder(new Order("Sell", self, Target.FromActor(self), false)
				{
					SuppressVisualFeedback = true
				});
				AIUtils.BotDebug("AI ({0}): Decided to sell {1}", player.ClientIndex, self);
				return;
			}

			// Protect buildings not suitable for selling
			foreach (var n in positionsUpdatedModules)
				n.UpdatedDefenseCenter(e.Attacker.Location);
		}

		bool ShouldSell(Actor self, AttackInfo e)
		{
			if (!self.Info.HasTraitInfo<SellableInfo>())
				return false;

			if (Info.DefenseTypes.Contains(self.Info.Name))
				return false;

			if (e.DamageState == DamageState.Dead || e.DamageState < DamageState.Medium || e.DamageState == e.PreviousDamageState)
				return false;

			var inMainBase = (self.CenterPosition - self.World.Map.CenterOfCell(initialBaseCenter)).Length < WDist.FromCells(28).Length;
			var chanceThreshold = inMainBase ? 95 : 70;

			if (self.World.LocalRandom.Next(100) < chanceThreshold)
				return false;

			if (Info.ConstructionYardTypes.Contains(self.Info.Name) && AIUtils.CountActorByCommonName(ConstructionYardBuildings) <= 1)
				return false;

			if (Info.BarracksTypes.Contains(self.Info.Name) && AIUtils.CountActorByCommonName(barracksBuildings) <= 1)
				return false;

			if (Info.VehiclesFactoryTypes.Contains(self.Info.Name) && AIUtils.CountActorByCommonName(factoryBuildings) <= 1)
				return false;

			var enemyUnits = self.World.FindActorsInCircle(self.CenterPosition, WDist.FromCells(Info.SellScanRadius)).Where(IsEnemyGroundUnit).ToList();

			if (enemyUnits.Count > 5)
			{
				var allyUnits = self.World.FindActorsInCircle(self.CenterPosition, WDist.FromCells(Info.SellScanRadius)).Where(IsAllyGroundUnit).ToList();

				if (enemyUnits.Count >= allyUnits.Count * 2)
					return true;
			}

			return false;
		}

		void SetRallyPoint(IBot bot, TraitPair<RallyPoint> rp)
		{
			var needsRallyPoint = rp.Trait.Path.Count == 0;

			if (!needsRallyPoint)
			{
				var locomotors = LocomotorsForProducibles(rp.Actor);
				needsRallyPoint = !IsRallyPointValid(rp.Actor.Location, rp.Trait.Path[0], locomotors, rp.Actor.Info.TraitInfoOrDefault<BuildingInfo>());
			}

			if (needsRallyPoint)
			{
				bot.QueueOrder(new Order("SetRallyPoint", rp.Actor, Target.FromCell(world, ChooseRallyLocationNear(rp.Actor)), false)
				{
					SuppressVisualFeedback = true
				});
			}
		}

		// Won't work for shipyards...
		CPos ChooseRallyLocationNear(Actor producer)
		{
			var locomotors = LocomotorsForProducibles(producer);
			var possibleRallyPoints = world.Map.FindTilesInCircle(producer.Location, Info.RallyPointScanRadius)
				.Where(c => IsRallyPointValid(producer.Location, c, locomotors, producer.Info.TraitInfoOrDefault<BuildingInfo>()))
				.ToList();

			if (possibleRallyPoints.Count == 0)
			{
				AIUtils.BotDebug("{0} has no possible rallypoint near {1}", producer.Owner, producer.Location);
				return producer.Location;
			}

			return possibleRallyPoints.Random(world.LocalRandom);
		}

		Locomotor[] LocomotorsForProducibles(Actor producer)
		{
			// Per-actor production
			var productions = producer.TraitsImplementing<Production>();

			// Player-wide production
			if (!productions.Any())
				productions = producer.World.ActorsWithTrait<Production>().Where(x => x.Actor.Owner != producer.Owner).Select(x => x.Trait);

			var produces = productions.SelectMany(p => p.Info.Produces).ToHashSet();
			var locomotors = Array.Empty<Locomotor>();
			if (produces.Count > 0)
			{
				// Per-actor production
				var productionQueues = producer.TraitsImplementing<ProductionQueue>();

				// Player-wide production
				if (!productionQueues.Any())
					productionQueues = producer.Owner.PlayerActor.TraitsImplementing<ProductionQueue>();

				productionQueues = productionQueues.Where(pq => produces.Contains(pq.Info.Type));

				var producibles = productionQueues.SelectMany(pq => pq.BuildableItems());
				var locomotorNames = producibles
					.Select(p => p.TraitInfoOrDefault<MobileInfo>())
					.Where(mi => mi != null)
					.Select(mi => mi.Locomotor)
					.ToHashSet();

				if (locomotorNames.Count != 0)
					locomotors = world.WorldActor.TraitsImplementing<Locomotor>()
						.Where(l => locomotorNames.Contains(l.Info.Name))
						.ToArray();
			}

			return locomotors;
		}

		bool IsRallyPointValid(CPos producerLocation, CPos rallyPointLocation, Locomotor[] locomotors, BuildingInfo buildingInfo)
		{
			return
				(pathFinder == null ||
					locomotors.All(l => pathFinder.PathMightExistForLocomotorBlockedByImmovable(l, producerLocation, rallyPointLocation)))
				&&
				(buildingInfo == null ||
					world.IsCellBuildable(rallyPointLocation, rallyPointLocation, null, buildingInfo));
		}

		// RefineryLimit (via BotLimits) is a single difficulty-scaled cap shared across every
		// construction yard the player owns, regardless of faction. Without the candidate
		// override below, a stray/secondary construction yard of a different faction than the
		// player's main base could never get its own first refinery once the main base alone
		// had already reached the global cap - starving that base's economy (and everything
		// that depends on it) indefinitely. Passing the specific refinery actor being
		// considered lets us always allow a faction's first refinery through.
		public bool HasMaxRefineries => HasMaxRefineriesFor(null);

		public bool HasMaxRefineriesFor(ActorInfo candidate)
		{
			if (candidate != null)
			{
				var conyardType = GetRequiredConstructionYardType(candidate);
				if (conyardType != null)
				{
					var factionHasRefinery = RefineryBuildings.Actors.Any(a => !a.IsDead
						&& GetRequiredConstructionYardType(a.Info) == conyardType);

					if (!factionHasRefinery)
						return false;
				}
			}

			var currentRefineryCount = AIUtils.CountActorByCommonName(RefineryBuildings);

			if (refineryLimit != 0 && currentRefineryCount >= refineryLimit)
				return true;

			foreach (var r in Info.RefineryTypes)
			{
				if (BuildingsBeingProduced != null && BuildingsBeingProduced.ContainsKey(r))
					currentRefineryCount += BuildingsBeingProduced[r];
			}

			return currentRefineryCount >= AIUtils.CountActorByCommonName(ConstructionYardBuildings) * Info.RefineriesPerBase + Info.MaxExtraRefineries;
		}

		// Require at least one refinery, unless we can't build it.
		public bool HasAdequateRefineryCount() =>
			Info.RefineryTypes.Count == 0 ||
			AIUtils.CountActorByCommonName(RefineryBuildings) >= OptimalRefineryCount() ||
			AIUtils.CountActorByCommonName(powerBuildings) == 0 ||
			AIUtils.CountActorByCommonName(ConstructionYardBuildings) == 0;

		int OptimalRefineryCount() =>
			AIUtils.CountActorByCommonName(ProductionBuildings) > 0
			? Info.InititalMinimumRefineryCount + Info.AdditionalMinimumRefineryCount + (AIUtils.CountActorByCommonName(ConstructionYardBuildings) - 1) * Info.RefineriesPerBase
			: Info.InititalMinimumRefineryCount;

		bool HasMinimalRefineryCount() =>
			AIUtils.CountActorByCommonName(RefineryBuildings) >= Info.InititalMinimumRefineryCount;

		public bool HasAdequateProductionCount() =>
			Info.ProductionTypes.Count == 0 ||
			AIUtils.CountActorByCommonName(ProductionBuildings) > 0;

		public bool HasCompletedPowerPlant() => AIUtils.CountActorByCommonName(powerBuildings) > 0;

		public bool OpeningBarracksPriorityCompleted => openingBarracksPriorityCompleted;

		public bool HasBuiltOrQueuedBarracks() =>
			AIUtils.CountActorByCommonName(barracksBuildings) > 0 || CountQueuedBuildings(Info.BarracksTypes) > 0;

		public bool HasQueuedBarracks() => CountQueuedBuildings(Info.BarracksTypes) > 0;

		public bool HasQueuedPowerPlant() => CountQueuedBuildings(Info.PowerTypes) > 0;

		public bool CanTrainOpeningDefense =>
			UsesBarracksFirstOpening && openingRefineryCostCommitted && !HasMinimalRefineryCount() && HasQueuedRefinery();

		bool UsesBarracksFirstOpening => botLimits != null && botLimits.Info.PrioritizeBarracksBeforeRefinery
			&& Info.BarracksBeforeRefineryFactions.Contains(player.Faction.InternalName);

		bool HasQueuedRefinery() => CountQueuedBuildings(Info.RefineryTypes) > 0;

		public void RecordOpeningStructureQueued(ProductionQueue queue, ActorInfo actorInfo)
		{
			if (!UsesBarracksFirstOpening || openingRefineryCostCommitted)
				return;

			var cost = queue.GetProductionCost(actorInfo);
			if (Info.PowerTypes.Contains(actorInfo.Name))
				openingPowerCommittedCost += cost;
			else if (Info.BarracksTypes.Contains(actorInfo.Name) && !openingBarracksCostCommitted)
			{
				openingBarracksCommittedCost = cost;
				openingBarracksCostCommitted = true;
			}
			else if (Info.RefineryTypes.Contains(actorInfo.Name) && openingBarracksPriorityCompleted)
			{
				// Custom maps may start with opening structures already present instead of producing them.
				if (openingPowerCommittedCost == 0)
					openingPowerCommittedCost = powerBuildings.Actors.Where(a => !a.IsDead)
						.Sum(a => queue.GetProductionCost(a.Info));

				if (!openingBarracksCostCommitted)
				{
					var barracks = barracksBuildings.Actors.FirstOrDefault(a => !a.IsDead);
					if (barracks != null)
					{
						openingBarracksCommittedCost = queue.GetProductionCost(barracks.Info);
						openingBarracksCostCommitted = true;
					}
				}

				openingRefineryCommittedCost = cost;
				openingRefineryCostCommitted = true;
				AIUtils.BotDebug("AI: {0} reserved {1} of {2} starting credits for the opening economy; {3} remain for early defense.",
					player, OpeningStructureCommittedCost, openingStartingCash, OpeningDefenseBudget);
			}
		}

		public bool TryCommitOpeningDefenseCost(int cost)
		{
			if (!CanTrainOpeningDefense || cost <= 0 || openingDefenseCommittedCost + cost > OpeningDefenseBudget)
				return false;

			openingDefenseCommittedCost += cost;
			return true;
		}

		int OpeningStructureCommittedCost =>
			openingPowerCommittedCost + openingBarracksCommittedCost + openingRefineryCommittedCost;

		int OpeningDefenseBudget => Math.Max(0, openingStartingCash - OpeningStructureCommittedCost);

		int CountQueuedBuildings(IReadOnlySet<string> buildingTypes) =>
			Info.BuildingQueues.Concat(Info.DefenseQueues)
				.Distinct()
				.SelectMany(category => AIUtils.FindQueues(player, category))
				.Distinct()
				.SelectMany(queue => queue.AllQueued())
				.Count(item => buildingTypes.Contains(item.Item));

		void SellUselessRefinery(IBot bot)
		{
			// Sell one refinery each time. Perserve at least one refinery
			var refineries = world.ActorsHavingTrait<Refinery>().Where(a => a.Owner == player).ToArray();

			if (refineries.Length <= Info.InititalMinimumRefineryCount + Info.AdditionalMinimumRefineryCount)
				return;

			for (var i = 0; i < refineries.Length; i++)
			{
				// StarCraft and Warcraft headquarters also accept resources. Keep them
				// in the refinery count, but never sell them as redundant drop-off sites.
				if (Info.ConstructionYardTypes.Contains(refineries[i].Info.Name))
				{
					AIUtils.BotDebug("AI ({0}): Preserving headquarters during refinery cleanup: {1}", player.ClientIndex, refineries[i]);
					continue;
				}

				for (var j = i + 1; j < refineries.Length; j++)
				{
					if ((refineries[i].Location - refineries[j].Location).LengthSquared <= Info.SellRefineryTooCloseCellDistance * Info.SellRefineryTooCloseCellDistance)
					{
						bot.QueueOrder(new Order("Sell", refineries[i], Target.FromActor(refineries[i]), false));
						return;
					}
				}

				if (ResourceMapModule != null &&
					!world.Map.FindTilesInAnnulus(refineries[i].Location, 0, Info.SellRefineryNoResourceDistance)
					.Any(c => ResourceMapModule.Info.ValuableResourceTypes.Contains(resourceLayer.GetResource(c).Type))
					&& !world.FindActorsInCircle(refineries[i].CenterPosition, WDist.FromCells(Info.SellRefineryNoResourceDistance))
					.Any(a => ResourceMapModule.Info.ResourceCreatorTypes.Contains(a.Info.Name)))
				{
					bot.QueueOrder(new Order("Sell", refineries[i], Target.FromActor(refineries[i]), false));
					return;
				}
			}
		}

		List<MiniYamlNode> IGameSaveTraitData.IssueTraitData(Actor self)
		{
			if (IsTraitDisabled)
				return null;

			return new List<MiniYamlNode>()
			{
				new("InitialBaseCenter", FieldSaver.FormatValue(initialBaseCenter)),
				new("DefenseCenter", FieldSaver.FormatValue(DefenseCenter)),
				new("OpeningBarracksPriorityCompleted", FieldSaver.FormatValue(openingBarracksPriorityCompleted)),
				new("OpeningStartingCashCaptured", FieldSaver.FormatValue(openingStartingCashCaptured)),
				new("OpeningStartingCash", FieldSaver.FormatValue(openingStartingCash)),
				new("OpeningPowerCommittedCost", FieldSaver.FormatValue(openingPowerCommittedCost)),
				new("OpeningBarracksCommittedCost", FieldSaver.FormatValue(openingBarracksCommittedCost)),
				new("OpeningBarracksCostCommitted", FieldSaver.FormatValue(openingBarracksCostCommitted)),
				new("OpeningRefineryCommittedCost", FieldSaver.FormatValue(openingRefineryCommittedCost)),
				new("OpeningRefineryCostCommitted", FieldSaver.FormatValue(openingRefineryCostCommitted)),
				new("OpeningDefenseCommittedCost", FieldSaver.FormatValue(openingDefenseCommittedCost))
			};
		}

		void IGameSaveTraitData.ResolveTraitData(Actor self, MiniYaml data)
		{
			if (self.World.IsReplay)
				return;

			var initialBaseCenterNode = data.NodeWithKeyOrDefault("InitialBaseCenter");
			if (initialBaseCenterNode != null)
				initialBaseCenter = FieldLoader.GetValue<CPos>("InitialBaseCenter", initialBaseCenterNode.Value.Value);

			var defenseCenterNode = data.NodeWithKeyOrDefault("DefenseCenter");
			if (defenseCenterNode != null)
				DefenseCenter = FieldLoader.GetValue<CPos>("DefenseCenter", defenseCenterNode.Value.Value);

			var openingBarracksPriorityCompletedNode = data.NodeWithKeyOrDefault("OpeningBarracksPriorityCompleted");
			if (openingBarracksPriorityCompletedNode != null)
				openingBarracksPriorityCompleted = FieldLoader.GetValue<bool>("OpeningBarracksPriorityCompleted",
					openingBarracksPriorityCompletedNode.Value.Value);

			var openingStartingCashCapturedNode = data.NodeWithKeyOrDefault("OpeningStartingCashCaptured");
			if (openingStartingCashCapturedNode != null)
				openingStartingCashCaptured = FieldLoader.GetValue<bool>("OpeningStartingCashCaptured",
					openingStartingCashCapturedNode.Value.Value);

			var openingStartingCashNode = data.NodeWithKeyOrDefault("OpeningStartingCash");
			if (openingStartingCashNode != null)
				openingStartingCash = FieldLoader.GetValue<int>("OpeningStartingCash", openingStartingCashNode.Value.Value);

			var openingPowerCommittedCostNode = data.NodeWithKeyOrDefault("OpeningPowerCommittedCost");
			if (openingPowerCommittedCostNode != null)
				openingPowerCommittedCost = FieldLoader.GetValue<int>("OpeningPowerCommittedCost", openingPowerCommittedCostNode.Value.Value);

			var openingBarracksCommittedCostNode = data.NodeWithKeyOrDefault("OpeningBarracksCommittedCost");
			if (openingBarracksCommittedCostNode != null)
				openingBarracksCommittedCost = FieldLoader.GetValue<int>("OpeningBarracksCommittedCost",
					openingBarracksCommittedCostNode.Value.Value);

			var openingBarracksCostCommittedNode = data.NodeWithKeyOrDefault("OpeningBarracksCostCommitted");
			if (openingBarracksCostCommittedNode != null)
				openingBarracksCostCommitted = FieldLoader.GetValue<bool>("OpeningBarracksCostCommitted",
					openingBarracksCostCommittedNode.Value.Value);

			var openingRefineryCommittedCostNode = data.NodeWithKeyOrDefault("OpeningRefineryCommittedCost");
			if (openingRefineryCommittedCostNode != null)
				openingRefineryCommittedCost = FieldLoader.GetValue<int>("OpeningRefineryCommittedCost",
					openingRefineryCommittedCostNode.Value.Value);

			var openingRefineryCostCommittedNode = data.NodeWithKeyOrDefault("OpeningRefineryCostCommitted");
			if (openingRefineryCostCommittedNode != null)
				openingRefineryCostCommitted = FieldLoader.GetValue<bool>("OpeningRefineryCostCommitted",
					openingRefineryCostCommittedNode.Value.Value);

			var openingDefenseCommittedCostNode = data.NodeWithKeyOrDefault("OpeningDefenseCommittedCost");
			if (openingDefenseCommittedCostNode != null)
				openingDefenseCommittedCost = FieldLoader.GetValue<int>("OpeningDefenseCommittedCost",
					openingDefenseCommittedCostNode.Value.Value);
		}

		void INotifyActorDisposing.Disposing(Actor self)
		{
			RefineryBuildings.Dispose();
			powerBuildings.Dispose();
			ConstructionYardBuildings.Dispose();
			barracksBuildings.Dispose();
		}

		void IBotSuggestRefineryProduction.RequestLocation(CPos refineryLocation, CPos conyardLocation, Actor expandActor)
		{
			if (ResourceMapModule == null || ResourceMapModule.FindClosestIndiceFromCPos(refineryLocation).PlayerRefineryCount < Info.MaxRefineryPerIndice)
				RequestedRefineries[expandActor] = (conyardLocation, refineryLocation);
		}
	}
}
