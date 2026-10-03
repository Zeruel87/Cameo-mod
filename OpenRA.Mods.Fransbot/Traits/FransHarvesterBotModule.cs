#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * Fransbot adaptations copyright (c) Fransbots contributors.
 * This file is part of OpenRA-compatible GPL code and is made available
 * under the GNU General Public License, version 3 or later.
 */
#endregion

using System;
using System.Collections.Frozen;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Activities;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	public interface IFransOreEconomyService
	{
		int VisibleMineCount { get; }
		int ResourceControlRadius { get; }
		IReadOnlyList<CPos> UnpairedMineLocations { get; }
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Fransbot ore-economy/harvester controller. After the deterministic opening it owns one-mine/one-PROC/one-HARV matching, surplus-HARV redistribution, HARV demand, and harvester movement through the shared RiskModel.")]
	public class FransHarvesterBotModuleInfo : ConditionalTraitInfo, NotBefore<IResourceLayerInfo>
	{
		[ActorReference]
		[Desc("Actor types managed as harvesters. Post-opening replacement/expansion demand is requested by this module; UnitBuilder only executes the production request.")]
		public readonly FrozenSet<string> HarvesterTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Owned refinery structures used as economic anchors and emergency retreat/dock destinations.")]
		public readonly FrozenSet<string> RefineryTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Renewable resource creator actors that receive one persistent harvester claim when serviced by a refinery.")]
		public readonly FrozenSet<string> ResourceCreatorTypes = FrozenSet<string>.Empty;

		[Desc("Maximum mine-to-PROC distance. Matching is one-to-one: one physical PROC can service at most one visible ore-mine and one ore-mine can use at most one PROC.")]
		public readonly int ResourceControlRadius = 18;

		[Desc("Harvesters demanded per serviced economic node. 1 preserves the strict node model; higher values let a serviced ore field keep a second harvester like classic RTS openings.")]
		public readonly int HarvestersPerServicedMine = 1;

		[Desc("Resource cells within this many cells of an assigned mine are preferred by that mine's harvester.")]
		public readonly int AssignedMineResourceRadius = 10;

		[Desc("World ticks between rebuilding the one-mine/one-PROC/one-HARV table and checking redistribution/production demand.")]
		public readonly int AssignmentInterval = 50;

		[Desc("World ticks between collecting idle/failed harvesters that need new Harvest orders.")]
		public readonly int ScanForIdleHarvestersInterval = 50;

		[Desc("When no reachable resources exist, wait this many idle-scan cycles before searching again.")]
		public readonly int ScanIntervalMultiplierWhenNoResources = 5;

		[Desc("Unified RiskModel tolerance for resource-field selection, resource paths and emergency refinery choice.")]
		public readonly FransRiskTolerance HarvesterRiskTolerance = FransRiskTolerance.Cautious;

		[Desc("World ticks before this harvester manager may issue another emergency retreat response after an attacked harvester event.")]
		public readonly int RespondToAttackCooldownTicks = 30;

		[Desc("If true, resource targets must be on explored terrain and enemy avoidance only uses enemies the player can currently view.")]
		public readonly bool RespectShroud = true;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			if (ResourceControlRadius <= 0 || AssignedMineResourceRadius <= 0 || AssignmentInterval <= 0 ||
				ScanForIdleHarvestersInterval <= 0 || ScanIntervalMultiplierWhenNoResources <= 0 || RespondToAttackCooldownTicks < 0 ||
				HarvestersPerServicedMine <= 0)
				throw new YamlException("FransHarvester timing/radius settings are invalid.");
		}

		public override object Create(ActorInitializer init) { return new FransHarvesterBotModule(init.Self, this); }
	}

	public class FransHarvesterBotModule : ConditionalTrait<FransHarvesterBotModuleInfo>,
		IBotTick, IBotRespondToAttack, INotifyActorDisposing, IWorldLoaded, IFransOreEconomyService
	{
		sealed class EconomicNode
		{
			public readonly Actor Mine;
			public readonly Actor Refinery;

			public EconomicNode(Actor mine, Actor refinery)
			{
				Mine = mine;
				Refinery = refinery;
			}
		}

		readonly record struct EconomicTopologyStamp(uint ActorId, CPos Cell);

		sealed class HarvesterState
		{
			public readonly Actor Actor;
			public readonly Harvester Harvester;
			public readonly DockClientManager DockClientManager;
			public readonly Parachutable Parachutable;
			public readonly Mobile Mobile;
			public int NoResourcesCooldown;

			public HarvesterState(Actor actor)
			{
				Actor = actor;
				Harvester = actor.Trait<Harvester>();
				DockClientManager = actor.Trait<DockClientManager>();
				Parachutable = actor.TraitOrDefault<Parachutable>();
				Mobile = actor.TraitOrDefault<Mobile>();
			}
		}

		readonly World world;
		readonly Player player;
		readonly ActorIndex.OwnerAndNames ownedHarvesters;
		readonly ActorIndex.OwnerAndNames refineries;
		readonly Dictionary<Actor, HarvesterState> harvesters = [];
		readonly Dictionary<Actor, Actor> mineClaims = [];
		readonly Dictionary<Actor, Actor> economicNodePairings = [];
		readonly Stack<HarvesterState> harvestersNeedingOrders = [];
		readonly Dictionary<CPos, string> resourceTypesByCell = [];
		CPos[] unpairedMineLocations = [];
		EconomicTopologyStamp[] cachedMineTopology = Array.Empty<EconomicTopologyStamp>();
		EconomicTopologyStamp[] cachedRefineryTopology = Array.Empty<EconomicTopologyStamp>();
		EconomicNode[] cachedEconomicNodes = Array.Empty<EconomicNode>();
		int visibleMineCount;

		IResourceLayer resourceLayer;
		ResourceClaimLayer claimLayer;
		IFransMineClusterService mineClusterService;
		IFransRiskModelService riskModelService;
		IFransBaseBuilderService baseBuilderService;
		IBotRequestUnitProduction[] requestUnitProduction;
		Shroud shroud;

		int scanForIdleHarvestersTicks;
		int assignmentTicks;
		int respondToAttackCooldown;

		public int VisibleMineCount => visibleMineCount;
		public int ResourceControlRadius => Info.ResourceControlRadius;
		public IReadOnlyList<CPos> UnpairedMineLocations => unpairedMineLocations;

		public FransHarvesterBotModule(Actor self, FransHarvesterBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			ownedHarvesters = new ActorIndex.OwnerAndNames(world, info.HarvesterTypes, player);
			refineries = new ActorIndex.OwnerAndNames(world, info.RefineryTypes, player);
		}

		protected override void Created(Actor self)
		{
			resourceLayer = world.WorldActor.TraitOrDefault<IResourceLayer>();
			claimLayer = world.WorldActor.TraitOrDefault<ResourceClaimLayer>();
			mineClusterService = self.Owner.PlayerActor.TraitsImplementing<IFransMineClusterService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransHarvesterBotModule requires FransMineClusterBotModule.");
			riskModelService = self.Owner.PlayerActor.TraitsImplementing<IFransRiskModelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransHarvesterBotModule requires FransRiskModelBotModule.");
			baseBuilderService = self.Owner.PlayerActor.TraitsImplementing<IFransBaseBuilderService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransHarvesterBotModule requires FransBaseBuilderBotModule.");
			requestUnitProduction = self.Owner.PlayerActor.TraitsImplementing<IBotRequestUnitProduction>().ToArray();
			shroud = self.TraitOrDefault<Shroud>();
		}

		public void WorldLoaded(World w, WorldRenderer wr)
		{
			if (resourceLayer == null)
				return;

			foreach (var cell in w.Map.AllCells)
			{
				var resource = resourceLayer.GetResource(cell);
				if (resource.Type != null)
					resourceTypesByCell[cell] = resource.Type;
			}

			resourceLayer.CellChanged += ResourceCellChanged;
		}

		void ResourceCellChanged(CPos cell, string resourceType)
		{
			if (resourceType == null)
				resourceTypesByCell.Remove(cell);
			else
				resourceTypesByCell[cell] = resourceType;
		}

		protected override void TraitEnabled(Actor self)
		{
			// Deterministic fixed offsets: no random startup jitter.
			scanForIdleHarvestersTicks = Math.Max(1, Info.ScanForIdleHarvestersInterval / 2);
			assignmentTicks = Math.Max(1, Info.AssignmentInterval / 2);
			respondToAttackCooldown = Info.RespondToAttackCooldownTicks;
			cachedMineTopology = Array.Empty<EconomicTopologyStamp>();
			cachedRefineryTopology = Array.Empty<EconomicTopologyStamp>();
			cachedEconomicNodes = Array.Empty<EconomicNode>();
			RefreshHarvesterSet();
			FransBotLog.BotDebug(world,
				"{0}: FransHarvester ORE NODE OWNER active: after the standard opening, economy matching is strict one visible ore-mine <-> one physical PROC <-> one HARV. Surplus HARVs are redistributed before new HARV production is requested.",
				player);
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransHarvester.BotTick");
			if (player.WinState != WinState.Undefined)
				return;

			if (respondToAttackCooldown > 0)
				respondToAttackCooldown--;

			if (resourceLayer == null || resourceLayer.IsEmpty)
				return;

			// PERF: path search is expensive. At most one idle harvester performs a full
			// resource-path search per world tick, matching the useful stock behavior.
			var searchedForResources = false;
			while (harvestersNeedingOrders.TryPop(out var state) && !searchedForResources)
				searchedForResources = HarvestIfAble(bot, state);

			if (--assignmentTicks <= 0)
			{
				assignmentTicks = Math.Max(1, Info.AssignmentInterval);
				RefreshHarvesterSet();
				RefreshMineClaims(bot);
			}

			if (--scanForIdleHarvestersTicks <= 0)
			{
				scanForIdleHarvestersTicks = Math.Max(1, Info.ScanForIdleHarvestersInterval);
				RefreshHarvesterSet();
				harvestersNeedingOrders.Clear();
				foreach (var state in harvesters.Values.OrderByDescending(h => h.Actor.ActorID))
					harvestersNeedingOrders.Push(state);
			}
		}

		void RefreshHarvesterSet()
		{
			foreach (var actor in harvesters.Keys
				.Where(a => a == null || a.IsDead || !a.IsInWorld || a.Owner != player)
				.ToArray())
			{
				harvesters.Remove(actor);
				mineClaims.Remove(actor);
			}

			foreach (var actor in ownedHarvesters.Actors
				.Where(a => a != null && a.IsInWorld && !a.IsDead)
				.OrderBy(a => a.ActorID))
			{
				if (!harvesters.ContainsKey(actor))
					harvesters[actor] = new HarvesterState(actor);
			}
		}

		EconomicNode[] BuildEconomicNodes()
		{
			var anchors = refineries.Actors
				.Where(a => a != null && a.OccupiesSpace != null && a.IsInWorld && !a.IsDead)
				.OrderBy(a => a.ActorID)
				.ToArray();

			var mines = mineClusterService.VisibleClusters
				.SelectMany(c => c.Mines)
				.Where(m => m != null && m.IsInWorld && !m.IsDead &&
					Info.ResourceCreatorTypes.Contains(m.Info.Name) &&
					m.CanBeViewedByPlayer(player))
				.Distinct()
				.OrderBy(m => m.ActorID)
				.ToArray();

			visibleMineCount = mines.Length;
			var mineTopology = mines.Select(a => new EconomicTopologyStamp(a.ActorID, a.Location)).ToArray();
			var refineryTopology = anchors.Select(a => new EconomicTopologyStamp(a.ActorID, a.Location)).ToArray();
			if (mineTopology.SequenceEqual(cachedMineTopology) && refineryTopology.SequenceEqual(cachedRefineryTopology))
				return cachedEconomicNodes;

			if (anchors.Length == 0 || mines.Length == 0 || Info.ResourceControlRadius <= 0)
			{
				economicNodePairings.Clear();
				unpairedMineLocations = mines.Select(m => m.Location).ToArray();
				cachedMineTopology = mineTopology;
				cachedRefineryTopology = refineryTopology;
				cachedEconomicNodes = Array.Empty<EconomicNode>();
				return cachedEconomicNodes;
			}

			var radiusSquared = Info.ResourceControlRadius * Info.ResourceControlRadius;
			var liveMines = mines.ToHashSet();
			var liveRefineries = anchors.ToHashSet();
			foreach (var mine in economicNodePairings
				.Where(kv => !liveMines.Contains(kv.Key) || !liveRefineries.Contains(kv.Value) ||
					(kv.Key.Location - kv.Value.Location).LengthSquared > radiusSquared)
				.Select(kv => kv.Key)
				.ToArray())
				economicNodePairings.Remove(mine);

			// Maximum-cardinality one-to-one matching with deterministic preference for a
			// still-valid previous pair. This prevents an unchanged PROC from hopping between
			// nearby mines while still allowing augmenting-path reassignment when that is
			// required to keep the maximum possible number of ore nodes serviced.
			var adjacency = mines.ToDictionary(
				mine => mine,
				mine => anchors
					.Where(r => (mine.Location - r.Location).LengthSquared <= radiusSquared)
					.OrderBy(r => economicNodePairings.TryGetValue(mine, out var previous) && previous == r ? 0 : 1)
					.ThenBy(r => (mine.Location - r.Location).LengthSquared)
					.ThenBy(r => r.ActorID)
					.ToArray());

			// Seed the matcher with every still-valid old pair. If the graph is unchanged,
			// no pair can move at all. Only a genuinely unmatched mine is allowed to start
			// an augmenting path that may reassign an old pair when doing so increases the
			// total number of serviced ore nodes.
			var mineByRefinery = economicNodePairings.ToDictionary(kv => kv.Value, kv => kv.Key);
			var alreadyMatchedMines = economicNodePairings.Keys.ToHashSet();
			bool TryAssign(Actor mine, HashSet<Actor> visitedRefineries)
			{
				foreach (var refinery in adjacency[mine])
				{
					if (!visitedRefineries.Add(refinery))
						continue;

					if (!mineByRefinery.TryGetValue(refinery, out var incumbent) || TryAssign(incumbent, visitedRefineries))
					{
						mineByRefinery[refinery] = mine;
						return true;
					}
				}

				return false;
			}

			foreach (var mine in mines.Where(m => !alreadyMatchedMines.Contains(m)))
				TryAssign(mine, new HashSet<Actor>());

			economicNodePairings.Clear();
			foreach (var pair in mineByRefinery.OrderBy(kv => kv.Value.ActorID).ThenBy(kv => kv.Key.ActorID))
				economicNodePairings[pair.Value] = pair.Key;

			var usedMines = economicNodePairings.Keys.ToHashSet();
			unpairedMineLocations = mines
				.Where(m => !usedMines.Contains(m))
				.Select(m => m.Location)
				.ToArray();
			cachedMineTopology = mineTopology;
			cachedRefineryTopology = refineryTopology;
			cachedEconomicNodes = economicNodePairings
				.OrderBy(kv => kv.Key.ActorID)
				.Select(kv => new EconomicNode(kv.Key, kv.Value))
				.ToArray();
			return cachedEconomicNodes;
		}

		void RefreshMineClaims(IBot bot)
		{
			var nodes = BuildEconomicNodes();
			var mines = nodes.Select(n => n.Mine).ToArray();
			var hs = harvesters.Keys
				.Where(a => a.IsInWorld && !a.IsDead)
				.OrderBy(a => a.ActorID)
				.ToArray();

			var validHarvesters = hs.ToHashSet();
			var validMines = mines.ToHashSet();
			foreach (var h in mineClaims
				.Where(kv => !validHarvesters.Contains(kv.Key) || !validMines.Contains(kv.Value))
				.Select(kv => kv.Key)
				.ToArray())
				mineClaims.Remove(h);

			if (mines.Length == 0)
			{
				mineClaims.Clear();
				return;
			}

			var claimedMines = mineClaims.Values.ToHashSet();
			var freeHarvesters = hs.Where(h => !mineClaims.ContainsKey(h)).ToList();

			foreach (var mine in mines.Where(m => !claimedMines.Contains(m)))
			{
				if (freeHarvesters.Count == 0)
					break;

				var harvester = freeHarvesters
					.Select(h => (Actor: h, Risk: riskModelService.EvaluateCell(h, mine.Location, FransRiskRole.Harvester, Info.HarvesterRiskTolerance)))
					.Where(x => !x.Risk.IsCritical)
					.OrderBy(x => x.Risk.Score)
					.ThenBy(x => (x.Actor.Location - mine.Location).LengthSquared)
					.ThenBy(x => x.Actor.ActorID)
					.Select(x => x.Actor)
					.FirstOrDefault();
				if (harvester == null)
					continue;

				freeHarvesters.Remove(harvester);
				mineClaims[harvester] = mine;
				claimedMines.Add(mine);

				// Stock HarvesterBotModule redistributes a low-effect surplus HARV before
				// requesting a replacement. Our stricter node model does the same, but the
				// destination is the specific unstaffed ore-mine that already has its own PROC.
				var state = harvesters[harvester];
				var redirected = TryRedirectToMine(bot, state, mine);
				FransBotLog.BotDebug(world,
					"{0}: ore-node assignment {1} -> {2} {3} at {4}; redistribution order={5}.",
					player, harvester, mine.Info.Name, mine.ActorID, mine.Location, redirected);
			}

			RequestMissingHarvester(bot, mines.Length * Math.Max(1, Info.HarvestersPerServicedMine), hs.Length);
		}

		bool TryRedirectToMine(IBot bot, HarvesterState state, Actor mine)
		{
			if (state.Actor.IsDead || !state.Actor.IsInWorld || state.Mobile == null ||
				(state.Parachutable != null && state.Parachutable.IsInAir))
				return false;

			// Do not break an active refinery docking transaction. Once it finishes, the
			// normal idle/failed-search scan will use the new persistent mine claim.
			if (state.DockClientManager.ReservedHostActor != null)
				return false;

			var target = FindResourceNearMine(state.Actor, state, mine);
			if (target.Type == TargetType.Invalid)
				return false;

			bot.QueueOrder(new Order("Harvest", state.Actor, target, false));
			return true;
		}

		void RequestMissingHarvester(IBot bot, int targetHarvesters, int ownedHarvesterCount)
		{
			if (!baseBuilderService.AllowAutomaticHarvesterDemand || targetHarvesters <= 0 ||
				Info.HarvesterTypes.Count == 0 || ownedHarvesterCount >= targetHarvesters)
				return;

			var unitBuilder = requestUnitProduction.FirstEnabledTraitOrDefault();
			if (unitBuilder == null)
				return;

			var harvesterType = Info.HarvesterTypes
				.OrderBy(x => x)
				.FirstOrDefault(t => world.Map.Rules.Actors.ContainsKey(t) &&
					FransActorClass.AnyOwnedQueueCanBuild(player, t));
			if (harvesterType == null)
				return;

			var requested = unitBuilder.RequestedProductionCount(bot, harvesterType);
			var queued = world.ActorsHavingTrait<ProductionQueue>()
				.Where(a => a.Owner == player && a.IsInWorld && !a.IsDead)
				.SelectMany(a => a.TraitsImplementing<ProductionQueue>())
				.Where(q => q.Enabled)
				.Sum(q => q.AllQueued().Count(item => Info.HarvesterTypes.Contains(item.Item)));

			if (ownedHarvesterCount + requested + queued >= targetHarvesters || requested > 0 || queued > 0)
				return;

			unitBuilder.RequestUnitProduction(bot, harvesterType);
			FransBotLog.BotDebug(world,
				"{0}: ore-node economy has {1} paired mine/PROC nodes but {2} HARV; no surplus can cover the deficit, requesting {3} x1 before re-evaluating.",
				player, targetHarvesters, ownedHarvesterCount, harvesterType);
		}

		Target FindResourceNearMine(Actor actor, HarvesterState state, Actor mine)
		{
			var radiusSquared = Info.AssignedMineResourceRadius * Info.AssignedMineResourceRadius;
			var local = resourceTypesByCell
				.Where(kv => state.Harvester.Info.Resources.Contains(kv.Value) &&
					(claimLayer == null || claimLayer.CanClaimCell(actor, kv.Key)) &&
					IsTerrainKnown(kv.Key) &&
					(kv.Key - mine.Location).LengthSquared <= radiusSquared)
				.Select(kv => kv.Key)
				.OrderBy(c => (c - mine.Location).LengthSquared)
				.ThenBy(c => c.X)
				.ThenBy(c => c.Y)
				.ToArray();

			return local.Length == 0
				? Target.Invalid
				: FindSafePathTarget(actor, state, actor.Location, local);
		}

		bool HarvestIfAble(IBot bot, HarvesterState state)
		{
			var actor = state.Actor;
			if (actor.IsDead || !actor.IsInWorld || state.Mobile == null)
				return false;

			if (!actor.IsIdle)
			{
				if (actor.CurrentActivity is not FindAndDeliverResources activity || !activity.LastSearchFailed)
					return false;
			}

			if (state.NoResourcesCooldown > 1)
			{
				state.NoResourcesCooldown--;
				return false;
			}

			if (state.Parachutable != null && state.Parachutable.IsInAir)
				return false;

			var target = FindNextResource(actor, state);
			if (target.Type != TargetType.Invalid)
				bot.QueueOrder(new Order("Harvest", actor, target, false));
			else
				state.NoResourcesCooldown = Math.Max(1, Info.ScanIntervalMultiplierWhenNoResources);

			return true;
		}

		Target FindNextResource(Actor actor, HarvesterState state)
		{
			IEnumerable<CPos> candidates = resourceTypesByCell
				.Where(kv => state.Harvester.Info.Resources.Contains(kv.Value) &&
					(claimLayer == null || claimLayer.CanClaimCell(actor, kv.Key)) &&
					IsTerrainKnown(kv.Key))
				.Select(kv => kv.Key);

			// A claimed harvester first searches the resource halo around its mine. This is
			// the movement-side half of the one-HARV-per-mine economy rule.
			if (mineClaims.TryGetValue(actor, out var mine) && mine != null && mine.IsInWorld && !mine.IsDead)
			{
				var localTarget = FindResourceNearMine(actor, state, mine);
				if (localTarget.Type != TargetType.Invalid)
					return localTarget;
			}

			var scanFrom = state.DockClientManager.ClosestDock(null, ignoreOccupancy: true)?.Actor ?? actor;
			var global = candidates
				.OrderBy(c => (c - scanFrom.Location).LengthSquared)
				.ThenBy(c => c.X)
				.ThenBy(c => c.Y)
				.ToArray();

			return global.Length == 0
				? Target.Invalid
				: FindSafePathTarget(actor, state, scanFrom.Location, global);
		}

		Target FindSafePathTarget(Actor actor, HarvesterState state, CPos from, IEnumerable<CPos> targets)
		{
			var preferredTargets = targets
				.Where(cell => riskModelService.EvaluateCell(actor, cell, FransRiskRole.Harvester, Info.HarvesterRiskTolerance).IsPreferred)
				.ToArray();
			if (preferredTargets.Length == 0)
				return Target.Invalid;

			int RiskCost(CPos cell) => cell == from ? 0 :
				riskModelService.GetPathCost(actor, cell, FransRiskRole.Harvester, Info.HarvesterRiskTolerance);
			var path = state.Mobile.PathFinder.FindPathToTargetCells(
				actor, from, preferredTargets, BlockedByActor.Stationary, RiskCost);
			return path.Count == 0 ? Target.Invalid : Target.FromCell(world, path[0]);
		}


		bool IsTerrainKnown(CPos cell)
		{
			if (!Info.RespectShroud || shroud == null || shroud.Disabled || shroud.ExploreMapEnabled)
				return true;

			return shroud.IsExplored(cell);
		}

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			if (respondToAttackCooldown > 0 || !Info.HarvesterTypes.Contains(self.Info.Name) ||
				e.Attacker == null || e.Attacker.IsDead || !e.Attacker.AppearsHostileTo(self))
				return;

			var parachutable = self.TraitOrDefault<Parachutable>();
			if (parachutable != null && parachutable.IsInAir)
				return;

			var dock = self.Trait<DockClientManager>();
			if (dock.ReservedHostActor != null)
				return;

			respondToAttackCooldown = Info.RespondToAttackCooldownTicks;
			var candidateDocks = refineries.Actors
				.Where(a => a != null && a.IsInWorld && !a.IsDead)
				.Select(a => (Actor: a, Risk: riskModelService.EvaluateCell(self, a.Location, FransRiskRole.Harvester, Info.HarvesterRiskTolerance)))
				.Where(x => !x.Risk.IsCritical)
				.OrderBy(x => x.Risk.Score)
				.ThenBy(x => (x.Actor.Location - self.Location).LengthSquared)
				.Select(x => x.Actor)
				.ToArray();
			var safeDock = candidateDocks.ClosestToWithPathFrom(self);
			if (safeDock == null)
				return;

			AIUtils.BotDebug("{0}: attacked harvester {1} retreats to RiskModel-selected refinery {2}.", player, self, safeDock);
			bot.QueueOrder(new Order("Dock", self, Target.FromActor(safeDock), false));
		}

		void INotifyActorDisposing.Disposing(Actor self)
		{
			ownedHarvesters.Dispose();
			refineries.Dispose();
			if (resourceLayer != null)
				resourceLayer.CellChanged -= ResourceCellChanged;
		}
	}
}
