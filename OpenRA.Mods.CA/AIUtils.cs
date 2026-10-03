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
using System.Linq;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Pathfinder;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.CA
{
	public enum BuildingType { Building, Defense, Refinery, Fragile, BaseCrawl }

	public enum WaterCheck { NotChecked, EnoughWater, NotEnoughWater, DontCheck }

	public static class AIUtils
	{
		public static bool IsAreaAvailable<T>(World world, Player player, Map map, int radius, FrozenSet<string> terrainTypes)
		{
			var cells = world.ActorsHavingTrait<T>().Where(a => a.Owner == player);

			// TODO: Properly check building foundation rather than 3x3 area.
			return cells.Select(a => map.FindTilesInCircle(a.Location, radius)
				.Count(c => map.Contains(c) && terrainTypes.Contains(map.GetTerrainInfo(c).Type) &&
					Util.AdjacentCells(world, Target.FromCell(world, c))
						.All(ac => map.Contains(ac) && terrainTypes.Contains(map.GetTerrainInfo(ac).Type))))
							.Any(availableCells => availableCells > 0);
		}

		// PERF: FindQueues was doing a whole-world player.World.ActorsWithTrait<ProductionQueue>()
		// scan (every player's queues) on every call — ~tens of times per tick across all bots, each
		// allocating a LINQ chain. Cache the global production-queue list once per WorldTick (the
		// actor set is stable within a tick, and identical on every client, so this is deterministic
		// and behaviour-preserving) and just filter the cached array per call.
		static int findQueuesCacheTick = -1;
		static TraitPair<ProductionQueue>[] findQueuesCache;

		public static IEnumerable<ProductionQueue> FindQueues(Player player, string category)
		{
			var world = player.World;
			if (findQueuesCacheTick != world.WorldTick || findQueuesCache == null)
			{
				findQueuesCache = world.ActorsWithTrait<ProductionQueue>().ToArray();
				findQueuesCacheTick = world.WorldTick;
			}

			foreach (var a in findQueuesCache)
				if (a.Actor.Owner == player && a.Trait.Info.Type == category && a.Trait.Enabled)
					yield return a.Trait;
		}

		public static IEnumerable<Actor> GetActorsWithTrait<T>(World world)
		{
			return world.ActorsHavingTrait<T>();
		}

		public static int CountActorsWithNameAndTrait<T>(string actorName, Player owner)
		{
			return owner.World.ActorsHavingTrait<T>().Count(a => a.Owner == owner && a.Info.Name == actorName);
		}

		public static int CountActorByCommonName<TTraitInfo>(ActorIndex.OwnerAndNamesAndTrait<TTraitInfo> actorIndex) where TTraitInfo : ITraitInfoInterface
		{
			return actorIndex.Actors.Count(a => !a.IsDead);
		}

		public static int CountBuildingByCommonName(HashSet<string> buildings, Player owner)
		{
			return GetActorsWithTrait<Building>(owner.World)
				.Count(a => a.Owner == owner && buildings.Contains(a.Info.Name));
		}

		public static List<Actor> FindEnemiesByCommonName(HashSet<string> commonNames, Player player)
		{
			return player.World.Actors.Where(a => !a.IsDead && player.RelationshipWith(a.Owner) == PlayerRelationship.Enemy &&
				commonNames.Contains(a.Info.Name)).ToList();
		}

		public static ActorInfo GetInfoByCommonName(HashSet<string> names, Player owner)
		{
			var matches = owner.World.Map.Rules.Actors.Where(k => names.Contains(k.Key)).ToList();
			return matches.Count > 0 ? matches.Random(owner.World.LocalRandom).Value : null;
		}

		// Common-name sets (e.g. HarvesterTypes) are shared across every faction in the mod, so a
		// plain random pick from `names` is overwhelmingly likely to select a type the owner can't
		// currently produce (wrong faction), silently failing the production request. Restrict the
		// pick to types that are actually buildable by one of the owner's current production queues.
		public static ActorInfo GetBuildableInfoByCommonName(HashSet<string> names, Player owner)
		{
			var buildable = owner.World.ActorsWithTrait<ProductionQueue>()
				.Where(a => a.Actor.Owner == owner && a.Trait.Enabled)
				.SelectMany(a => a.Trait.BuildableItems())
				.Where(a => names.Contains(a.Name))
				.Distinct()
				.ToList();

			if (buildable.Count > 0)
				return buildable.Random(owner.World.LocalRandom);

			return GetInfoByCommonName(names, owner);
		}

		public static void BotDebug(string s, params object[] args)
		{
			if (Game.Settings.Debug.BotDebug)
				TextNotificationsManager.Debug(s, args);
		}

		public static bool PathExist(Actor unit, CPos destination, Actor ignoreActor, BlockedByActor blockedByActor = BlockedByActor.Immovable)
		{
			var mobile = unit.TraitOrDefault<Mobile>();
			if (mobile == null)
			{
				// We consider other IMove ignore all blockers
				if (unit.TraitsImplementing<IMove>().Any())
					return true;
				else
					return false;
			}

			if (mobile.PathFinder.FindPathToTargetCell(unit, new List<CPos> { unit.Location }, destination, blockedByActor, ignoreActor: ignoreActor, laneBias: false).Count > 0)
				return true;
			else
				return false;
		}

		// Finds multiple distinct routes between source and target for a given locomotor.
		public static List<List<CPos>> FindDistinctRoutes(
			World world,
			Locomotor locomotor,
			CPos source,
			CPos target,
			int maxRoutes = 3,
			BlockedByActor check = BlockedByActor.None)
		{
			var routes = new List<List<CPos>>();

			var pathFinder = world.WorldActor.TraitOrDefault<PathFinder>();
			if (pathFinder == null)
				return routes;

			var (abstractGraph, abstractDomains) = pathFinder.GetOverlayDataForLocomotor(locomotor, check);
			if (abstractGraph == null || abstractDomains == null)
				return routes;

			var sourceAbstract = FindAbstractNodeForCell(source, abstractGraph, abstractDomains);
			var targetAbstract = FindAbstractNodeForCell(target, abstractGraph, abstractDomains);

			if (sourceAbstract == null || targetAbstract == null)
				return routes;

			if (!abstractDomains.TryGetValue(sourceAbstract.Value, out var sourceDomain) ||
				!abstractDomains.TryGetValue(targetAbstract.Value, out var targetDomain) ||
				sourceDomain != targetDomain)
				return routes;

			var excludedNodes = new HashSet<CPos>();

			for (var i = 0; i < maxRoutes; i++)
			{
				var route = FindAbstractPath(sourceAbstract.Value, targetAbstract.Value, abstractGraph, excludedNodes);
				if (route == null || route.Count == 0)
					break;

				routes.Add(route);

				foreach (var node in route)
				{
					if (node != sourceAbstract.Value
						&& node != targetAbstract.Value
						&& node != route.ElementAtOrDefault(1)
						&& node != route.ElementAtOrDefault(2)
						&& node != route.ElementAtOrDefault(route.Count - 2))
						excludedNodes.Add(node);
				}
			}

			return routes;
		}

		static CPos? FindAbstractNodeForCell(
			CPos cell,
			IReadOnlyDictionary<CPos, List<GraphConnection>> abstractGraph,
			IReadOnlyDictionary<CPos, uint> abstractDomains)
		{
			if (abstractDomains.ContainsKey(cell))
				return cell;

			CPos? nearestNode = null;
			var minDistSq = int.MaxValue;

			foreach (var abstractNode in abstractDomains.Keys)
			{
				var distSq = (abstractNode - cell).LengthSquared;
				if (distSq < minDistSq)
				{
					minDistSq = distSq;
					nearestNode = abstractNode;
				}
			}

			return nearestNode;
		}

		static List<CPos> FindAbstractPath(
			CPos source,
			CPos target,
			IReadOnlyDictionary<CPos, List<GraphConnection>> abstractGraph,
			HashSet<CPos> excludedNodes)
		{
			var openSet = new Dictionary<CPos, PathNode>();
			var closedSet = new HashSet<CPos>();

			var startNode = new PathNode
			{
				Position = source,
				CostFromStart = 0,
				EstimatedTotalCost = Heuristic(source, target),
				Parent = null
			};

			openSet[source] = startNode;

			while (openSet.Count > 0)
			{
				var current = openSet.Values.MinBy(n => n.EstimatedTotalCost);
				if (current == null)
					break;

				if (current.Position == target)
					return ReconstructPath(current);

				openSet.Remove(current.Position);
				closedSet.Add(current.Position);

				if (!abstractGraph.TryGetValue(current.Position, out var connections))
					continue;

				foreach (var connection in connections)
				{
					var neighbor = connection.Destination;

					if (closedSet.Contains(neighbor) || (excludedNodes.Contains(neighbor) && neighbor != target))
						continue;

					var newCost = current.CostFromStart + connection.Cost;

					if (!openSet.TryGetValue(neighbor, out var neighborNode))
					{
						neighborNode = new PathNode
						{
							Position = neighbor,
							CostFromStart = newCost,
							EstimatedTotalCost = newCost + Heuristic(neighbor, target),
							Parent = current
						};
						openSet[neighbor] = neighborNode;
					}
					else if (newCost < neighborNode.CostFromStart)
					{
						neighborNode.CostFromStart = newCost;
						neighborNode.EstimatedTotalCost = newCost + Heuristic(neighbor, target);
						neighborNode.Parent = current;
					}
				}
			}

			return null;
		}

		static List<CPos> ReconstructPath(PathNode targetNode)
		{
			var path = new List<CPos>();
			var current = targetNode;

			while (current != null)
			{
				path.Add(current.Position);
				current = current.Parent;
			}

			path.Reverse();
			return path;
		}

		static int Heuristic(CPos from, CPos to)
		{
			var delta = from - to;
			return Math.Abs(delta.X) + Math.Abs(delta.Y);
		}

		class PathNode
		{
			public CPos Position;
			public int CostFromStart;
			public int EstimatedTotalCost;
			public PathNode Parent;
		}
	}
}
