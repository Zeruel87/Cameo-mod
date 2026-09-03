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
using System.Linq;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	[Desc("Controls AI unit production.")]
	public class UnitBuilderBotModuleCAInfo : ConditionalTraitInfo
	{
		// TODO: Investigate whether this might the (or at least one) reason why bots occasionally get into a state of doing nothing.
		// Reason: If this is less than SquadSize, the bot might get stuck between not producing more units due to this,
		// but also not creating squads since there aren't enough idle units.
		[Desc("Only produce units as long as there are less than this amount of units idling inside the base.")]
		public readonly int IdleBaseUnitsMaximum = 12;

		[Desc("Production queues AI uses for producing units.")]
		public readonly string[] UnitQueues = { "VehicleSQ", "InfantrySQ", "AircraftSQ", "ShipSQ", "VehicleMQ", "InfantryMQ", "AircraftMQ", "ShipMQ" };

		[Desc("Basic combat units that may be produced from the starting-cash surplus while the opening refinery is unfinished.")]
		public readonly HashSet<string> OpeningDefenseUnitTypes = new HashSet<string>();

		[Desc("What units to the AI should build.", "What relative share of the total army must be this type of unit.")]
		public readonly Dictionary<string, int> UnitsToBuild = null;

		[Desc("What units should the AI have a maximum limit to train.")]
		public readonly Dictionary<string, int> UnitLimits = null;

		[Desc("When should the AI start train specific units.")]
		public readonly Dictionary<string, int> UnitDelays = null;

		[Desc("Minimum duration between building a specific unit.")]
		public readonly Dictionary<string, int> UnitIntervals = null;

		[Desc("How often should the unit builder check to build more units")]
		public readonly int UnitBuilderInterval = 0;

		[Desc("Only queue construction of a new unit when above this requirement.")]
		public readonly int ProductionMinCashRequirement = 2000;

		[Desc("Only queue construction of a new unit when above this requirement.")]
		public readonly int MaximiseProductionCashRequirement = 10000;

		[Desc("Maximum number of aircraft AI can build.",
			"If MaintainAirSuperiority is true this only applies to units not listed in AirToAirUnits.")]
		public readonly int MaxAircraft = 4;

		[Desc("If true, will always attempt to match the number of enemy air threats.")]
		public readonly bool MaintainAirSuperiority = false;

		[Desc("If MaintainAirSuperiority is true and this is non-zero,",
			"sets an upper limit for the number of air superiority aircraft.")]
		public readonly int MaxAirSuperiority = 0;

		[Desc("List of actor types to be used for air superiority.")]
		public readonly HashSet<string> AirToAirUnits = new HashSet<string>();

		[Desc("List of actor types to measure against for air superiority.")]
		public readonly HashSet<string> AirThreatUnits = new HashSet<string>();

		[Desc("If true, the bot will use compositions defined in the UnitCompositionsBotModule to determine what units to build.",
			"If false, the bot will ignore compositions and just use UnitsToBuild.")]
		public readonly bool UseCompositions = false;

		[Desc("Minimum ticks before selecting a new composition.")]
		public readonly int MinCompositionSelectInterval = 750;

		[Desc("Maximum ticks before selecting a new composition.")]
		public readonly int MaxCompositionSelectInterval = 7500;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);

			if (MinCompositionSelectInterval < 0)
				throw new YamlException("MinCompositionSelectInterval must not be negative.");

			if (MaxCompositionSelectInterval < 0)
				throw new YamlException("MaxCompositionSelectInterval must not be negative.");

			if (MinCompositionSelectInterval != 0 && MaxCompositionSelectInterval != 0 &&
				MaxCompositionSelectInterval < MinCompositionSelectInterval)
				throw new YamlException("MaxCompositionSelectInterval cannot be less than MinCompositionSelectInterval.");
		}

		public override object Create(ActorInitializer init) { return new UnitBuilderBotModuleCA(init.Self, this); }
	}

	public class UnitBuilderBotModuleCA : ConditionalTrait<UnitBuilderBotModuleCAInfo>, IBotTick, IBotNotifyIdleBaseUnits, IBotRequestUnitProduction, IGameSaveTraitData, IBotAircraftBuilder, INotifyActorDisposing
	{
		public const int FeedbackTime = 30; // ticks; = a bit over 1s. must be >= netlag.

		readonly World world;
		readonly Player player;

		UnitComposition activeComposition;
		int activeCompositionProducedValue;
		int activeCompositionSelectedTick;
		int nextCompositionSelectTick;
		readonly Dictionary<string, int> compositionLastUsedTickById = new Dictionary<string, int>();

		readonly List<string> queuedBuildRequests = new List<string>();
		ActorIndex.OwnerAndNames unitsToBuild;
		readonly Dictionary<string, int> activeUnitIntervals = new Dictionary<string, int>();

		UnitCompositionsBotModule compositionsModule;
		List<UnitComposition> possibleActiveCompositions;
		TechTree techTree;

		IBotRequestPauseUnitProduction[] requestPause;
		int idleUnitCount;
		int currentQueueIndex = 0;
		PlayerResources playerResources;
		BotLimits botLimits;
		BaseBuilderBotModuleCA baseBuilder;

		int ticks;
		int openingDefenseTicks;
		int unitDelayModifier = 100;
		int unitIntervalModifier = 100;
		bool firstTick = true;

		public UnitBuilderBotModuleCA(Actor self, UnitBuilderBotModuleCAInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		protected override void Created(Actor self)
		{
			// Special case handling is required for the Player actor.
			// Created is called before Player.PlayerActor is assigned,
			// so we must query player traits from self, which refers
			// for bot modules always to the Player actor.
			requestPause = self.TraitsImplementing<IBotRequestPauseUnitProduction>().ToArray();
			playerResources = self.Owner.PlayerActor.Trait<PlayerResources>();
			techTree = self.Owner.PlayerActor.TraitOrDefault<TechTree>();
			compositionsModule = Info.UseCompositions ? self.World.WorldActor.TraitOrDefault<UnitCompositionsBotModule>() : null;

			var referencedUnitTypes = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
			if (Info.UnitsToBuild != null)
				referencedUnitTypes.UnionWith(Info.UnitsToBuild.Keys);

			if (compositionsModule != null && compositionsModule.UnitCompositions.Count != 0)
			{
				foreach (var composition in compositionsModule.UnitCompositions)
					if (composition?.UnitsToBuild != null)
						referencedUnitTypes.UnionWith(composition.UnitsToBuild.Keys);

				possibleActiveCompositions = compositionsModule.UnitCompositions
					.Where(c => c != null && !c.IsBaseline &&
						(c.EnabledChance == 100 || self.World.LocalRandom.Next(100) < c.EnabledChance))
					.ToList();

				nextCompositionSelectTick = GetNextCompositionSelectTick();
			}

			unitsToBuild = new ActorIndex.OwnerAndNames(world, referencedUnitTypes, player);
		}

		protected override void TraitEnabled(Actor self)
		{
			RefreshDifficultyTraits();
		}

		void RefreshDifficultyTraits()
		{
			botLimits = player.PlayerActor.TraitsImplementing<BotLimits>().FirstEnabledTraitOrDefault();
			baseBuilder = player.PlayerActor.TraitsImplementing<BaseBuilderBotModuleCA>().FirstEnabledTraitOrDefault();
			unitDelayModifier = botLimits?.Info.UnitDelayModifier ?? 100;
			unitIntervalModifier = botLimits?.Info.UnitIntervalModifier ?? 100;
		}

		void IBotNotifyIdleBaseUnits.UpdatedIdleBaseUnits(List<UnitWposWrapper> idleUnits)
		{
			idleUnitCount = idleUnits.Count;
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (firstTick)
			{
				RefreshDifficultyTraits();
				firstTick = false;
			}

			// Decrement any active unit intervals, removing any that reach zero
			foreach (KeyValuePair<string, int> i in activeUnitIntervals.ToList())
			{
				activeUnitIntervals[i.Key]--;
				if (activeUnitIntervals[i.Key] <= 0)
					activeUnitIntervals.Remove(i.Key);
			}

			var baseBuilderPause = requestPause.FirstOrDefault(rp => ReferenceEquals(rp, baseBuilder));
			if (requestPause.Any(rp => !ReferenceEquals(rp, baseBuilderPause) && rp.PauseUnitProduction))
				return;

			if (baseBuilderPause != null && baseBuilderPause.PauseUnitProduction)
			{
				if (++openingDefenseTicks % (FeedbackTime + Info.UnitBuilderInterval) == 0)
					TryBuildOpeningDefense(bot);

				return;
			}

			openingDefenseTicks = 0;

			ticks++;

			if (ticks % (FeedbackTime + Info.UnitBuilderInterval) == 0)
			{
				UpdateComposition();

				var buildRequest = queuedBuildRequests.FirstOrDefault();
				if (buildRequest != null)
				{
					BuildUnit(bot, buildRequest);
					queuedBuildRequests.Remove(buildRequest);
				}

				// Don't produce if we don't have enough cash
				if (playerResources.Cash + playerResources.Resources < Info.ProductionMinCashRequirement)
					return;

				for (var i = 0; i < Info.UnitQueues.Length; i++)
				{
					if (++currentQueueIndex >= Info.UnitQueues.Length)
						currentQueueIndex = 0;

					if (AIUtils.FindQueues(player, Info.UnitQueues[currentQueueIndex]).Any())
					{
						// PERF: We tick only one type of valid queue at a time
						// if AI gets enough cash, it can fill all of its queues with enough ticks
						BuildUnit(bot, Info.UnitQueues[currentQueueIndex], idleUnitCount < Info.IdleBaseUnitsMaximum, false);

						if (playerResources.Cash + playerResources.Resources < Info.MaximiseProductionCashRequirement)
							break;
					}
				}
			}
		}

		void TryBuildOpeningDefense(IBot bot)
		{
			if (baseBuilder == null || !baseBuilder.CanTrainOpeningDefense || Info.OpeningDefenseUnitTypes.Count == 0)
				return;

			foreach (var queue in Info.UnitQueues.SelectMany(category => AIUtils.FindQueues(player, category)).Distinct())
			{
				if (queue.AllQueued().Any())
					continue;

				var unit = queue.BuildableItems()
					.FirstOrDefault(a => Info.OpeningDefenseUnitTypes.Contains(a.Name) && ShouldBuild(a.Name, false, queue.Info.Type));
				if (unit == null)
					continue;

				var cost = queue.GetProductionCost(unit);
				if (playerResources.GetCashAndResources() < cost || !baseBuilder.TryCommitOpeningDefenseCost(cost))
					return;

				SetUnitInterval(unit.Name);
				bot.QueueOrder(Order.StartProduction(queue.Actor, unit.Name, 1));
				AIUtils.BotDebug("AI: {0} decided to build {1} from the opening defense budget.", player, unit.Name);
				return;
			}
		}

		void IBotRequestUnitProduction.RequestUnitProduction(IBot bot, string requestedActor)
		{
			queuedBuildRequests.Add(requestedActor);
		}

		int IBotRequestUnitProduction.RequestedProductionCount(IBot bot, string requestedActor)
		{
			return queuedBuildRequests.Count(r => r == requestedActor);
		}

		void BuildUnit(IBot bot, string category, bool buildRandom, bool excludeLimited)
		{
			// For queues that support parallel production (e.g. Zerg hatchery), find one with a free slot.
			// For standard queues, require the queue to be completely empty.
			var queue = AIUtils.FindQueues(player, category).FirstOrDefault(q =>
			{
				if (q is IHasParallelQueueSlots p)
					return p.AvailableSlots > 0;
				return !q.AllQueued().Any();
			});

			if (queue == null)
				return;

			// Fill all available parallel slots in one pass so that every larva stays occupied.
			var slotsToFill = (queue is IHasParallelQueueSlots parallelQueue)
				? parallelQueue.AvailableSlots
				: 1;

			for (var slot = 0; slot < slotsToFill; slot++)
			{
				var unit = buildRandom ?
					ChooseRandomUnitToBuild(queue, excludeLimited) :
					ChooseUnitToBuild(queue, excludeLimited);

				if (unit == null)
				{
					if (activeComposition != null && CompositionAppliesToCategory(activeComposition, queue.Info.Type))
						RevertToBaselineComposition();

					return;
				}

				var name = unit.Name;

				if (!ShouldBuild(name, false, queue.Info.Type))
				{
					if (!excludeLimited)
						BuildUnit(bot, category, buildRandom, true);

					return;
				}

				SetUnitInterval(name);
				bot.QueueOrder(Order.StartProduction(queue.Actor, name, 1));
				if (activeComposition != null && CompositionAppliesToCategory(activeComposition, queue.Info.Type))
					AddToActiveCompositionProducedValue(unit);
			}
		}

		// In cases where we want to build a specific unit but don't know the queue name (because there's more than one possibility)
		void BuildUnit(IBot bot, string name)
		{
			var actorInfo = world.Map.Rules.Actors[name];
			if (actorInfo == null)
				return;

			var buildableInfo = actorInfo.TraitInfoOrDefault<BuildableInfo>();
			if (buildableInfo == null)
				return;

			if (!ShouldBuild(name, true))
				return;

			ProductionQueue queue = null;
			foreach (var pq in buildableInfo.Queue)
			{
				queue = AIUtils.FindQueues(player, pq).FirstOrDefault(q => !q.AllQueued().Any());
				if (queue != null)
					break;
			}

			if (queue != null && queue.BuildableItems().Any(b => b.Name == name))
			{
				SetUnitInterval(name);
				bot.QueueOrder(Order.StartProduction(queue.Actor, name, 1));
				AIUtils.BotDebug("AI: {0} decided to build {1} (external request)", queue.Actor.Owner, name);
			}
		}

		void SetUnitInterval(string name)
		{
			if (Info.UnitIntervals == null || !Info.UnitIntervals.ContainsKey(name))
				return;

			activeUnitIntervals[name] = Info.UnitIntervals[name] * unitIntervalModifier / 100;
		}

		bool ShouldBuild(string name, bool ignoreUnitsToBuild, string queueCategory = null)
		{
			var unitsToBuildShares = GetUnitsToBuildForCategory(queueCategory);
			if (!ignoreUnitsToBuild && unitsToBuildShares != null && !unitsToBuildShares.ContainsKey(name))
				return false;

			if (Info.UnitDelays != null &&
				Info.UnitDelays.ContainsKey(name) &&
				Info.UnitDelays[name] * unitDelayModifier / 100 > world.WorldTick)
				return false;

			if (Info.UnitIntervals != null &&
				Info.UnitIntervals.ContainsKey(name) &&
				activeUnitIntervals.ContainsKey(name))
				return false;

			if (Info.UnitLimits != null &&
				Info.UnitLimits.ContainsKey(name) &&
				world.Actors.Count(a => !a.IsDead && a.Owner == player && a.Info.Name == name) >= Info.UnitLimits[name])
				return false;

			return true;
		}

		ActorInfo ChooseRandomUnitToBuild(ProductionQueue queue, bool excludeLimited)
		{
			var unitsToBuildShares = GetUnitsToBuildForCategory(queue.Info.Type);
			if (unitsToBuildShares == null || unitsToBuildShares.Count == 0)
				return null;

			var buildableThings = queue.BuildableItems().Where(a => unitsToBuildShares.ContainsKey(a.Name) &&
				(!excludeLimited || Info.UnitLimits == null || !Info.UnitLimits.ContainsKey(a.Name)));
			if (!buildableThings.Any())
				return null;

			var unit = buildableThings.Random(world.LocalRandom);
			return CanBuildMoreOfAircraft(unit) ? unit : null;
		}

		ActorInfo ChooseUnitToBuild(ProductionQueue queue, bool excludeLimited)
		{
			var buildableThings = queue.BuildableItems();
			if (!buildableThings.Any())
				return null;

			var unitsToBuildShares = GetUnitsToBuildForCategory(queue.Info.Type);
			if (unitsToBuildShares == null || unitsToBuildShares.Count == 0)
				return null;

			var myUnits = player.World
				.ActorsHavingTrait<IPositionable>()
				.Where(a => a.Owner == player)
				.Select(a => a.Info.Name).ToList();

			foreach (var unit in unitsToBuildShares.Shuffle(world.LocalRandom))
				if (buildableThings.Any(b => b.Name == unit.Key))
					if (!excludeLimited || Info.UnitLimits == null || !Info.UnitLimits.ContainsKey(unit.Key))
						if (myUnits.Count(a => a == unit.Key) * 100 < unit.Value * myUnits.Count)
							if (CanBuildMoreOfAircraft(world.Map.Rules.Actors[unit.Key]))
								return world.Map.Rules.Actors[unit.Key];

			return null;
		}

		Dictionary<string, int> GetUnitsToBuildForCategory(string queueCategory)
		{
			if (compositionsModule == null || compositionsModule.UnitCompositions.Count == 0 ||
				activeComposition == null || !CompositionAppliesToCategory(activeComposition, queueCategory))
				return Info.UnitsToBuild;

			return activeComposition.UnitsToBuild;
		}

		void UpdateComposition()
		{
			if (compositionsModule == null || compositionsModule.UnitCompositions.Count == 0)
				return;

			if (activeComposition != null)
			{
				var exceededDuration = activeComposition.MaxDuration > 0 &&
					world.WorldTick - activeCompositionSelectedTick >= activeComposition.MaxDuration;
				var exceededValue = activeComposition.MaxProducedValue > 0 &&
					activeCompositionProducedValue >= activeComposition.MaxProducedValue;

				if (exceededDuration || exceededValue)
					RevertToBaselineComposition();
			}
			else if (world.WorldTick >= nextCompositionSelectTick)
			{
				var newActiveComposition = ChooseActiveComposition();
				if (newActiveComposition != null)
				{
					activeComposition = newActiveComposition;
					activeCompositionProducedValue = 0;
					activeCompositionSelectedTick = world.WorldTick;
					if (!string.IsNullOrEmpty(activeComposition.Id))
						compositionLastUsedTickById[activeComposition.Id] = world.WorldTick;
				}
			}
		}

		void RevertToBaselineComposition()
		{
			activeComposition = null;
			activeCompositionProducedValue = 0;
			nextCompositionSelectTick = GetNextCompositionSelectTick();
		}

		UnitComposition ChooseActiveComposition()
		{
			if (possibleActiveCompositions == null || possibleActiveCompositions.Count == 0)
				return null;

			nextCompositionSelectTick = GetNextCompositionSelectTick();

			var playerQueues = OpenRA.Mods.Common.AIUtils.FindQueuesByCategory(player);
			var candidates = possibleActiveCompositions
				.Where(c => IsCompositionTimeValid(c)
					&& IsCompositionIntervalValid(c)
					&& AreCompositionPrerequisitesMet(c)
					&& CanProduceAnyUnitInCompositionForEachQueueCategory(c, playerQueues))
				.ToArray();

			return candidates.Length != 0 ? candidates.Random(world.LocalRandom) : null;
		}

		bool IsCompositionIntervalValid(UnitComposition composition)
		{
			if (composition.MinInterval <= 0 || string.IsNullOrEmpty(composition.Id))
				return true;

			if (!compositionLastUsedTickById.TryGetValue(composition.Id, out var lastTick))
				return true;

			return world.WorldTick - lastTick >= composition.MinInterval;
		}

		bool IsCompositionTimeValid(UnitComposition composition)
		{
			var tick = world.WorldTick;
			if (composition.MinTime > 0 && tick < composition.MinTime)
				return false;
			if (composition.MaxTime > 0 && tick > composition.MaxTime)
				return false;

			return true;
		}

		bool CanProduceAnyUnitInCompositionForQueueCategory(UnitComposition composition, string queueCategory)
		{
			if (string.IsNullOrEmpty(queueCategory))
				return false;

			if (techTree == null)
				return true;

			var byQueue = composition.UnitPrerequisitesByQueue;
			if (byQueue == null || !byQueue.TryGetValue(queueCategory, out var unitPrereqs) ||
				unitPrereqs == null || unitPrereqs.Count == 0)
				return false;

			foreach (var prereqs in unitPrereqs.Values)
				if (prereqs == null || prereqs.Length == 0 || techTree.HasPrerequisites(prereqs))
					return true;

			return false;
		}

		bool CanProduceAnyUnitInCompositionForEachQueueCategory(UnitComposition composition, ILookup<string, ProductionQueue> playerQueues)
		{
			var byQueue = composition.UnitPrerequisitesByQueue;
			if (byQueue == null || byQueue.Count == 0)
				return false;

			foreach (var queueCategory in byQueue.Keys)
			{
				if (!playerQueues.Contains(queueCategory))
					continue;

				if (!CanProduceAnyUnitInCompositionForQueueCategory(composition, queueCategory))
					return false;
			}

			return true;
		}

		bool CompositionAppliesToCategory(UnitComposition composition, string queueCategory)
		{
			if (composition.UnitQueues == null || composition.UnitQueues.Length == 0)
				return true;

			return composition.UnitQueues.Any(q => q != null && q.Equals(queueCategory, StringComparison.OrdinalIgnoreCase));
		}

		bool AreCompositionPrerequisitesMet(UnitComposition composition)
		{
			if (composition.Prerequisites == null || composition.Prerequisites.Length == 0)
				return true;

			return techTree == null || techTree.HasPrerequisites(composition.Prerequisites);
		}

		int GetNextCompositionSelectTick()
		{
			var min = Math.Max(0, Info.MinCompositionSelectInterval);
			var max = Math.Max(0, Info.MaxCompositionSelectInterval);

			if (min == 0 && max == 0)
				return int.MaxValue / 4;

			if (max < min)
				max = min;

			var interval = min == max ? min : world.LocalRandom.Next(min, max + 1);
			return world.WorldTick + interval;
		}

		void AddToActiveCompositionProducedValue(ActorInfo builtUnit)
		{
			if (activeComposition == null || compositionsModule == null || builtUnit == null)
				return;

			compositionsModule.UnitCosts.TryGetValue(builtUnit.Name, out var unitCost);
			if (unitCost <= 0)
				return;

			activeCompositionProducedValue += unitCost;
		}

		bool IBotAircraftBuilder.CanBuildMoreOfAircraft(ActorInfo actorInfo)
		{
			return CanBuildMoreOfAircraft(actorInfo);
		}

		bool CanBuildMoreOfAircraft(ActorInfo actorInfo)
		{
			var attackAircraftInfo = actorInfo.TraitInfoOrDefault<AircraftInfo>();
			if (attackAircraftInfo == null)
				return true;

			var limit = Info.MaxAircraft;
			var currentCount = 0;

			if (Info.MaintainAirSuperiority)
			{
				var numAirToAirUnits = AIUtils.GetActorsWithTrait<Aircraft>(player.World).Count(a => a.Owner == player && Info.AirToAirUnits.Contains(a.Info.Name));

				if (Info.AirToAirUnits.Contains(actorInfo.Name))
				{
					currentCount = numAirToAirUnits;
					var numFriendlyAirToAirUnits = player.World.Actors.Count(a => a.Owner.RelationshipWith(player) == PlayerRelationship.Ally && Info.AirToAirUnits.Contains(a.Info.Name));
					var numEnemyAirThreatUnits = player.World.Actors.Count(a => a.Owner.RelationshipWith(player) == PlayerRelationship.Enemy && Info.AirThreatUnits.Contains(a.Info.Name));
					limit = Math.Max(numEnemyAirThreatUnits - numFriendlyAirToAirUnits + 1, limit);

					if (Info.MaxAirSuperiority > 0)
						limit = Math.Min(Info.MaxAirSuperiority, limit);
				}
				else
					currentCount = AIUtils.GetActorsWithTrait<Aircraft>(player.World).Count(a => a.Owner == player && a.Info.HasTraitInfo<BuildableInfo>()) - numAirToAirUnits;
			}
			else
				currentCount = AIUtils.GetActorsWithTrait<Aircraft>(player.World).Count(a => a.Owner == player && a.Info.HasTraitInfo<BuildableInfo>());

			return currentCount < limit;
		}

		List<MiniYamlNode> IGameSaveTraitData.IssueTraitData(Actor self)
		{
			if (IsTraitDisabled)
				return null;

			return new List<MiniYamlNode>()
			{
				new("QueuedBuildRequests", FieldSaver.FormatValue(queuedBuildRequests.ToArray())),
				new("IdleUnitCount", FieldSaver.FormatValue(idleUnitCount)),
				new("CompositionLastUsed", "", compositionLastUsedTickById
					.Select(kvp => new MiniYamlNode(kvp.Key, FieldSaver.FormatValue(kvp.Value)))
					.ToList())
			};
		}

		void IGameSaveTraitData.ResolveTraitData(Actor self, MiniYaml data)
		{
			if (self.World.IsReplay)
				return;

			var queuedBuildRequestsNode = data.NodeWithKeyOrDefault("QueuedBuildRequests");
			if (queuedBuildRequestsNode != null)
			{
				queuedBuildRequests.Clear();
				queuedBuildRequests.AddRange(FieldLoader.GetValue<string[]>("QueuedBuildRequests", queuedBuildRequestsNode.Value.Value));
			}

			var idleUnitCountNode = data.NodeWithKeyOrDefault("IdleUnitCount");
			if (idleUnitCountNode != null)
				idleUnitCount = FieldLoader.GetValue<int>("IdleUnitCount", idleUnitCountNode.Value.Value);

			var compositionLastUsedNode = data.NodeWithKeyOrDefault("CompositionLastUsed");
			if (compositionLastUsedNode != null)
			{
				compositionLastUsedTickById.Clear();
				foreach (var n in compositionLastUsedNode.Value.Nodes)
					compositionLastUsedTickById[n.Key] = FieldLoader.GetValue<int>("CompositionLastUsed", n.Value.Value);
			}
		}

		void INotifyActorDisposing.Disposing(Actor self)
		{
			unitsToBuild?.Dispose();
		}
	}
}
