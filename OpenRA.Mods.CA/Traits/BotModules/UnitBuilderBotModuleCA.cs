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
using OpenRA.Support;
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

		[Desc("Only queue construction of a new unit when above this requirement.",
			"BotLimits.MaximiseProductionCashRequirement overrides this per difficulty (DESIGN §19.1).")]
		public readonly int MaximiseProductionCashRequirement = 10000;

		[Desc("Ticks between samples of the enemy army for adaptive counter-production (BotLimits.AdaptiveCounterWeight).")]
		public readonly int AdaptiveObservationInterval = 250;

		[Desc("Maximum number of aircraft AI can build.",
			"If MaintainAirSuperiority is true this only applies to units not listed in AirToAirUnits.")]
		public readonly int MaxAircraft = 4;

		[Desc("If true, will always attempt to match the number of enemy air threats.")]
		public readonly bool MaintainAirSuperiority = false;

		[ConsumedConditionReference]
		[Desc("Increment switches on this shared instance (CountQueuedAircraft, ObservedAirThreats) take effect only while this condition is true",
			"(e.g. genericbot), so a shared module can be A/B-switched without changing the classic reference. Null = switches apply to every owner.")]
		public readonly BooleanExpression SwitchCondition = null;

		[Desc("CA F2p2 (71754fc06): aircraft already queued for production count towards the aircraft limits,",
			"and allied air-to-air aircraft count as part of the current air-to-air count instead of lowering the limit.",
			"Default false keeps the previous behaviour.")]
		public readonly bool CountQueuedAircraft = false;

		[Desc("CA F2p2 / DESIGN 19.5: count enemy air threats (for MaintainAirSuperiority) from the observed enemy composition instead of",
			"scanning every actor in the world. Bots without a fog-observing composition provider (classic) keep the world count.",
			"Default false keeps the previous behaviour.")]
		public readonly bool ObservedAirThreats = false;

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

		[Desc("AI_ARCHITECTURE.md §2.8b item 3 (UW-1): derive the UnitsToBuild weights from the enabled",
			"personality's RoleMix and each candidate's Versus-weighted strength instead of using the",
			"yaml shares. The yaml rows stay the membership gate; rows for units with no combat role",
			"pass through as overrides, and an active composition still wins. Off until the next",
			"increment A/B (switch group I_derived_unit_weights). Inert on classic: it carries no",
			"RoleMix and no IBotUnitRoles provider.")]
		public readonly bool UseDerivedUnitWeights = false;

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

		// SwitchCondition result; true when no condition is configured.
		bool switchesActive;
		bool CountQueued => Info.CountQueuedAircraft && switchesActive;
		bool ObservedThreats => Info.ObservedAirThreats && switchesActive;

		UnitComposition activeComposition;
		int activeCompositionProducedValue;
		int activeCompositionSelectedTick;
		int nextCompositionSelectTick;

		// Record-only observability for the AI match log (schema 2): the id of the
		// currently selected composition, and a transition notification keyed by tick.
		public string ActiveCompositionId => activeComposition?.Id ?? string.Empty;
		public event Action<int, string> ActiveCompositionChanged;
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

		readonly AdaptiveCounterProduction counters;
		IBotEnemyCompositionProvider compositionProvider;
		IBotPersonalityLeadProvider[] leadProviders;
		IBotUnitRoles unitRoles;

		// Cameo (§12.23, PP-1): lazy — resolved on first BuildUnit; null keeps the upstream one-queue fill.
		IBotProductionWidth productionWidth;
		IBotScaleTargets[] scaleTargets;
		readonly DerivedUnitWeights derivedUnitWeights = new DerivedUnitWeights();

		int CounterWeight => botLimits?.Info.AdaptiveCounterWeight ?? 0;

		int MaximiseProductionCash => botLimits != null && botLimits.Info.MaximiseProductionCashRequirement >= 0
			? botLimits.Info.MaximiseProductionCashRequirement : Info.MaximiseProductionCashRequirement;

		public UnitBuilderBotModuleCA(Actor self, UnitBuilderBotModuleCAInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			counters = new AdaptiveCounterProduction(world, player);
			switchesActive = info.SwitchCondition == null;
		}

		public override IEnumerable<VariableObserver> GetVariableObservers()
		{
			foreach (var observer in base.GetVariableObservers())
				yield return observer;

			if (Info.SwitchCondition != null)
				yield return new VariableObserver(SwitchConditionChanged, Info.SwitchCondition.Variables);
		}

		void SwitchConditionChanged(Actor self, IReadOnlyDictionary<string, int> conditions)
		{
			switchesActive = Info.SwitchCondition.Evaluate(conditions);
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
			compositionProvider = self.TraitsImplementing<IBotEnemyCompositionProvider>().FirstOrDefault();
			leadProviders = self.TraitsImplementing<IBotPersonalityLeadProvider>().ToArray();
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

			if (CounterWeight > 0)
				counters.Observe(Info.AdaptiveObservationInterval, compositionProvider);

			// Decrement any active unit intervals, removing any that reach zero
			foreach (KeyValuePair<string, int> i in activeUnitIntervals.ToList())
			{
				activeUnitIntervals[i.Key]--;
				if (activeUnitIntervals[i.Key] <= 0)
					activeUnitIntervals.Remove(i.Key);
			}

			var baseBuilderPause = requestPause.FirstOrDefault(rp => ReferenceEquals(rp, baseBuilder));
			if (requestPause.Any(rp => !ReferenceEquals(rp, baseBuilderPause) && rp.IsTraitEnabled() && rp.PauseUnitProduction))
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

				// §12.14 PL-1: a trailing Steamroller lead relaxes both cash floors
				// toward spending sooner — at target (or leads off) the multiplier
				// is 1 and the floors are unchanged.
				var cashLean = BotPersonalityLeads.Lean(leadProviders, "steamroller");

				// Don't produce if we don't have enough cash
				if (playerResources.Cash + playerResources.Resources < BotPersonalityLeads.Scaled(Info.ProductionMinCashRequirement, cashLean))
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

						if (playerResources.Cash + playerResources.Resources < BotPersonalityLeads.Scaled(MaximiseProductionCash, cashLean))
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
			// Cameo (§12.21, PP-1): an enabled IBotProductionWidth provider lifts the one-queue-per-call
			// cap — three war factories produce in parallel instead of feeding one and idling the rest.
			// No provider = first free queue only, byte-identical to upstream; classic mounts none.
			productionWidth ??= player.PlayerActor.TraitsImplementing<IBotProductionWidth>().FirstEnabledTraitOrDefault();
			var maxQueues = productionWidth?.MaxQueuesPerCategory ?? 1;
			var queues = AIUtils.FindQueues(player, category)
				.Where(q =>
				{
					if (q is IHasParallelQueueSlots p)
						return p.AvailableSlots > 0;
					return !q.AllQueued().Any();
				})
				.Take(Math.Max(1, maxQueues));

			foreach (var queue in queues)
			{
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

						break;
					}

					var name = unit.Name;

					if (!ShouldBuild(name, false, queue.Info.Type))
					{
						if (!excludeLimited)
						{
							BuildUnit(bot, category, buildRandom, true);
							return;
						}

						break;
					}

					SetUnitInterval(name);
					bot.QueueOrder(Order.StartProduction(queue.Actor, name, 1));
					counters.Record(unit);
					if (activeComposition != null && CompositionAppliesToCategory(activeComposition, queue.Info.Type))
						AddToActiveCompositionProducedValue(unit);
				}
			}
		}

		// In cases where we want to build a specific unit but don't know the queue name (because there's more than one possibility)
		void BuildUnit(IBot bot, string name)
		{
			// Actors[] throws KeyNotFoundException for names absent from the ruleset —
			// reachable when a queued request survives a save whose version renamed the actor.
			if (!world.Map.Rules.Actors.TryGetValue(name, out var actorInfo))
				return;

			// Upstream iterates every Buildable trait — an actor with several (alternate
			// queue sets) would otherwise have requests routed only through the first.
			foreach (var buildableInfo in actorInfo.TraitInfos<BuildableInfo>())
			{
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
					return;
				}
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

			var counter = ChooseCounter(buildableThings);
			if (counter != null)
				return counter;

			var deficit = ChooseRoleDeficit(buildableThings, unitsToBuildShares, excludeLimited);
			if (deficit != null)
				return deficit;

			var weights = ActiveProductionWeights();
			var unit = weights.Count > 0 ? ChooseWeighted(buildableThings.ToList(), weights) : buildableThings.Random(world.LocalRandom);
			return CanBuildMoreOfAircraft(unit) ? unit : null;
		}

		// The ACTIVE IBotProductionWeight providers (Cameo's learned priors, genericbot only, off by default). Resolved
		// from the player actor on each use: their conditions settle after Created, so an empty set is never cached.
		// None active = the unit builder's original path, random draws included.
		List<IBotProductionWeight> ActiveProductionWeights() =>
			player.PlayerActor.TraitsImplementing<IBotProductionWeight>().Where(p => p.IsActive).ToList();

		// Product of the providers' factors, in percent (100 = neutral).
		int LearnedWeightPercent(ActorInfo unit, List<IBotProductionWeight> providers)
		{
			var weight = 100L;
			foreach (var provider in providers)
				weight = weight * provider.WeightPercent(player, unit) / 100;

			return (int)Math.Max(weight, 0);
		}

		ActorInfo ChooseWeighted(List<ActorInfo> candidates, List<IBotProductionWeight> providers)
		{
			var weights = candidates.Select(c => LearnedWeightPercent(c, providers)).ToList();
			var total = weights.Sum();
			if (total <= 0)
				return candidates.Random(world.LocalRandom);

			var roll = world.LocalRandom.Next(total);
			for (var i = 0; i < candidates.Count; i++)
			{
				roll -= weights[i];
				if (roll < 0)
					return candidates[i];
			}

			return candidates[^1];
		}

		ActorInfo ChooseUnitToBuild(ProductionQueue queue, bool excludeLimited)
		{
			var buildableThings = queue.BuildableItems();
			if (!buildableThings.Any())
				return null;

			var unitsToBuildShares = GetUnitsToBuildForCategory(queue.Info.Type);
			if (unitsToBuildShares == null || unitsToBuildShares.Count == 0)
				return null;

			var counter = ChooseCounter(buildableThings.Where(b => unitsToBuildShares.ContainsKey(b.Name) &&
				(!excludeLimited || Info.UnitLimits == null || !Info.UnitLimits.ContainsKey(b.Name))));
			if (counter != null)
				return counter;

			var deficit = ChooseRoleDeficit(buildableThings, unitsToBuildShares, excludeLimited);
			if (deficit != null)
				return deficit;

			var myUnits = player.World
				.ActorsHavingTrait<IPositionable>()
				.Where(a => a.Owner == player)
				.Select(a => a.Info.Name).ToList();

			foreach (var unit in unitsToBuildShares.Shuffle(world.LocalRandom))
				if (buildableThings.Any(b => b.Name == unit.Key))
					if (!excludeLimited || Info.UnitLimits == null || !Info.UnitLimits.ContainsKey(unit.Key))
						if (myUnits.Count(a => a == unit.Key) * 100 < ShareFor(unit.Key, unit.Value) * myUnits.Count)
							if (CanBuildMoreOfAircraft(world.Map.Rules.Actors[unit.Key]))
								return world.Map.Rules.Actors[unit.Key];

			return null;
		}

		int ShareFor(string name, int share)
		{
			var providers = ActiveProductionWeights();
			return providers.Count > 0 ? share * LearnedWeightPercent(world.Map.Rules.Actors[name], providers) / 100 : share;
		}

		// CA-3 (AI_ARCHITECTURE.md 12.5): the enabled personality's RoleMix is a target
		// army composition by role, in percent of own mobile combat units. Each pick
		// fills the largest deficit — counter production still gets first refusal, and
		// a fully satisfied mix falls through to the proportional pick. Roles the mix
		// does not name get RoleMixRoleFloorPct whenever this queue can serve them.
		// The provider resolves lazily: BotUnitRoles is a genericbot-gated
		// ConditionalTrait whose condition settles after Created.
		ActorInfo ChooseRoleDeficit(IEnumerable<ActorInfo> buildableThings, Dictionary<string, int> unitsToBuildShares, bool excludeLimited)
		{
			var manager = player.PlayerActor.TraitsImplementing<SquadManagerBotModuleCA>().FirstEnabledTraitOrDefault();
			var mix = manager?.Info.UseRoleMix == true ? manager.Info.RoleMix : null;
			if (mix == null || mix.Count == 0)
				return null;

			var roles = unitRoles ??= player.PlayerActor.TraitsImplementing<IBotUnitRoles>().FirstEnabledTraitOrDefault();
			if (roles == null)
				return null;

			var counts = new Dictionary<string, int>(StringComparer.Ordinal);
			var total = 0;
			foreach (var a in world.ActorsHavingTrait<IPositionable>())
			{
				if (a.IsDead || a.Owner != player)
					continue;

				var primary = roles.PrimaryRoleOf(a.Info.Name);
				if (primary == null)
					continue;

				counts[primary] = counts.GetValueOrDefault(primary) + 1;
				total++;
			}

			// The deficit domain is the combat taxonomy: list/doctrine roles (guerrilla,
			// firesupport, navalunit, ...) and the building target tags never become
			// mix dimensions — a unit counts toward exactly one primary role.
			foreach (var role in mix.Keys
				.Concat(roles.RoleMembers.Keys)
				.Where(r => BotUnitRole.CombatRoles.Contains(r))
				.Distinct(StringComparer.Ordinal)
				.Select(r => (Role: r, Target: mix.TryGetValue(r, out var t) ? t : manager.Info.RoleMixRoleFloorPct))
				.Where(rt => rt.Target > 0)
				.OrderByDescending(rt => rt.Target - 100.0 * counts.GetValueOrDefault(rt.Role) / Math.Max(1, total)))
			{
				var members = roles.RoleMembers.GetValueOrDefault(role.Role);
				if (members == null || members.Count == 0)
					continue;

				var options = buildableThings.Where(b => members.Contains(b.Name) &&
					unitsToBuildShares.ContainsKey(b.Name) &&
					(!excludeLimited || Info.UnitLimits == null || !Info.UnitLimits.ContainsKey(b.Name)) &&
					ShouldBuild(b.Name, false) && CanBuildMoreOfAircraft(b)).ToList();

				if (options.Count == 0)
					continue;

				// A multi-role unit counts toward its primary role only, so prefer
				// members that actually relieve this deficit (e.g. a dual-role Orca
				// fields as fighter, not the gunship share it also belongs to).
				var relieving = options.Where(b => roles.PrimaryRoleOf(b.Name) == role.Role).ToList();
				return (relieving.Count > 0 ? relieving : options).Random(world.LocalRandom);
			}

			return null;
		}

		// Adaptive counters (DESIGN §19.1): below this tier's share of counter picks, the best counter to the
		// observed enemy army among the units this composition allows; otherwise the normal choice.
		ActorInfo ChooseCounter(IEnumerable<ActorInfo> allowed)
		{
			counters.LastChoiceAdaptive = false;
			if (!AdaptiveCounterProduction.CounterPickAllowed(counters.AdaptiveSelections, counters.TotalSelections, CounterWeight))
				return null;

			var owned = player.World.ActorsHavingTrait<IPositionable>().Where(a => a.Owner == player)
				.GroupBy(a => a.Info.Name).ToDictionary(g => g.Key, g => g.Count());
			var choice = counters.Choose(allowed.Where(a => AdaptiveCounterProduction.IsMobileCombat(a) &&
				ShouldBuild(a.Name, false) && CanBuildMoreOfAircraft(a)), n => owned.GetValueOrDefault(n));
			counters.LastChoiceAdaptive = choice != null;
			return choice;
		}

		Dictionary<string, int> GetUnitsToBuildForCategory(string queueCategory)
		{
			var compositionWeights = compositionsModule != null && compositionsModule.UnitCompositions.Count != 0 &&
				activeComposition != null && CompositionAppliesToCategory(activeComposition, queueCategory)
					? activeComposition.UnitsToBuild : null;

			// UW-1 (AI_ARCHITECTURE.md §2.8b item 3): the inputs are resolved only when the flag
			// is on and no composition claims the category — an enabled squad manager carrying a
			// RoleMix plus an enabled IBotUnitRoles provider (genericbot-gated). Flag off skips
			// every lookup and returns the pre-change table byte-identical.
			SquadManagerBotModuleCA manager = null;
			IReadOnlyDictionary<string, int> mix = null;
			IBotUnitRoles roles = null;
			if (compositionWeights == null && Info.UseDerivedUnitWeights &&
				(manager = player.PlayerActor.TraitsImplementing<SquadManagerBotModuleCA>().FirstEnabledTraitOrDefault()) != null &&
				(mix = manager.Info.RoleMix) != null && mix.Count != 0)
				roles = unitRoles ??= player.PlayerActor.TraitsImplementing<IBotUnitRoles>().FirstEnabledTraitOrDefault();

			return derivedUnitWeights.Select(Info.UseDerivedUnitWeights, compositionWeights, Info.UnitsToBuild,
				mix, manager?.Info.RoleMixRoleFloorPct ?? 0, roles, DerivedUnitStrength);
		}

		// A candidate's strength is read off its own type profile — no enemy is ever
		// enumerated (fog-honest, DESIGN §19.5).
		double DerivedUnitStrength(string name)
		{
			return world.Map.Rules.Actors.TryGetValue(name, out var actorInfo)
				? DerivedUnitWeights.Strength(BotUnitProfiles.Get(world.Map.Rules, actorInfo))
				: 1.0;
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
					SetActiveComposition(newActiveComposition);
					activeCompositionProducedValue = 0;
					activeCompositionSelectedTick = world.WorldTick;
					if (!string.IsNullOrEmpty(activeComposition.Id))
						compositionLastUsedTickById[activeComposition.Id] = world.WorldTick;
				}
			}
		}

		void RevertToBaselineComposition()
		{
			SetActiveComposition(null);
			activeCompositionProducedValue = 0;
			nextCompositionSelectTick = GetNextCompositionSelectTick();
		}

		void SetActiveComposition(UnitComposition next)
		{
			var nextId = next?.Id ?? string.Empty;
			if (nextId == ActiveCompositionId)
				return;

			activeComposition = next;
			ActiveCompositionChanged?.Invoke(world.WorldTick, nextId);
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

			// Scale targets (DESIGN 19.10): an enabled provider's aircraft target replaces MaxAircraft, and scales
			// MaxAirSuperiority in the same proportion; without one both are the yaml numbers.
			var limit = Info.MaxAircraft;
			var maxAirSuperiority = Info.MaxAirSuperiority;
			scaleTargets ??= player.PlayerActor.TraitsImplementing<IBotScaleTargets>().ToArray();
			if (scaleTargets.TryTarget("aircraft", out var scaledAircraft))
			{
				if (maxAirSuperiority > 0 && Info.MaxAircraft > 0)
					maxAirSuperiority = Math.Max(1, (int)((long)maxAirSuperiority * scaledAircraft / Info.MaxAircraft));

				limit = scaledAircraft;
			}

			var currentCount = 0;
			var isAirToAir = Info.AirToAirUnits.Contains(actorInfo.Name);

			// One enumeration of our own and allied aircraft (own/allied actors are always visible: not a fog read).
			var alliedAircraft = AIUtils.GetActorsWithTrait<Aircraft>(player.World)
				.Where(a => a.Owner.RelationshipWith(player) == PlayerRelationship.Ally || a.Owner == player).ToList();
			var ownAllAircraft = alliedAircraft.Where(a => a.Owner == player).ToList();
			var ownAircraft = ownAllAircraft.Where(a => a.Info.HasTraitInfo<BuildableInfo>()).ToList();

			// CA F2p2 (71754fc06): aircraft already in a production queue count towards the limit.
			var queued = CountQueued ? QueuedAircraft(!Info.MaintainAirSuperiority || !isAirToAir) : null;

			if (Info.MaintainAirSuperiority)
			{
				var numAirToAirUnits = ownAllAircraft.Count(a => Info.AirToAirUnits.Contains(a.Info.Name));

				if (isAirToAir)
				{
					currentCount = numAirToAirUnits;
					var numFriendlyAirToAirUnits = alliedAircraft.Count(a => a.Owner.RelationshipWith(player) == PlayerRelationship.Ally && Info.AirToAirUnits.Contains(a.Info.Name));
					var numEnemyAirThreatUnits = EnemyAirThreatCount();

					if (CountQueued)
					{
						// Upstream: friendly (allied) A2A plus everything queued by the team is the current count.
						currentCount = numFriendlyAirToAirUnits + queued.Count(n => Info.AirToAirUnits.Contains(n));
					}

					limit = AirLimits.AirSuperiorityLimit(limit, numEnemyAirThreatUnits, numFriendlyAirToAirUnits, CountQueued, maxAirSuperiority);
				}
				else
				{
					currentCount = ownAircraft.Count - numAirToAirUnits;
					if (CountQueued)
						currentCount += queued.Count(n => !Info.AirToAirUnits.Contains(n));
				}
			}
			else
			{
				currentCount = ownAircraft.Count;
				if (CountQueued)
					currentCount += queued.Count;
			}

			return currentCount < limit;
		}

		// Names of aircraft sitting in production queues: our own queues, plus allied queues unless `ownOnly`
		// (the air-to-air pool is shared with allies, upstream counts their queues too).
		List<string> QueuedAircraft(bool ownOnly)
		{
			var result = new List<string>();
			foreach (var p in world.Players)
			{
				if (p != player && (ownOnly || !p.IsAlliedWith(player)))
					continue;

				foreach (var group in OpenRA.Mods.Common.AIUtils.FindQueuesByCategory(p))
					foreach (var q in group)
						foreach (var item in q.AllQueued())
							if (world.Map.Rules.Actors.TryGetValue(item.Item, out var ai) && ai.HasTraitInfo<AircraftInfo>())
								result.Add(item.Item);
			}

			return result;
		}

		// CA F2p2 / DESIGN 19.5: with ObservedAirThreats the enemy air threats come from the OBSERVED enemy composition
		// (fog memory). Without a provider that observes through fog (the classic bot) - or with the switch off - the
		// legacy omniscient world count stays, so the classic A/B reference is unchanged.
		int EnemyAirThreatCount()
		{
			if (ObservedThreats && compositionProvider != null && compositionProvider.TryGetEnemyComposition(out var valueByType))
				return AirLimits.EstimateObservedThreatCount(valueByType, Info.AirThreatUnits,
					type => world.Map.Rules.Actors.TryGetValue(type, out var ai) ? ai.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0 : 0);

			return player.World.Actors.Count(a => a.Owner.RelationshipWith(player) == PlayerRelationship.Enemy && Info.AirThreatUnits.Contains(a.Info.Name));
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
			}.Concat(counters.SaveNodes()).ToList();
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

			counters.Load(data);
		}

		void INotifyActorDisposing.Disposing(Actor self)
		{
			unitsToBuild?.Dispose();
		}
	}
}
