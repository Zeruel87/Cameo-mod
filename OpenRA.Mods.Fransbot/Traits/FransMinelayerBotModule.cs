#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software under the GNU General Public License,
 * version 3 or later. See COPYING in the OpenRA source tree.
 */
#endregion

using System;
using System.Collections.Frozen;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Fransbots fair-information minelayer manager. Conflict/fallback intelligence is converted into minefield candidates, while the shared FransRiskModel owns destination and route safety.")]
	public class FransMinelayerBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Enemy target types to ignore when recording combat locations or choosing a visible fallback direction.")]
		public readonly BitSet<TargetableType> IgnoredEnemyTargetTypes = default;

		[Desc("Victim target types that prefer the attacker's location when the attacker is currently visible; otherwise the victim location is used.")]
		public readonly BitSet<TargetableType> UseEnemyLocationTargetTypes = default;

		[ActorReference(typeof(MinelayerInfo))]
		[Desc("Actors with Minelayer trait.")]
		public readonly FrozenSet<string> MinelayingActorTypes = default;

		[Desc("Maximum suitable minelayers assigned to one minefield order.")]
		public readonly int MaxPerAssign = 1;

		[Desc("World ticks between assignment scans.")]
		public readonly int ScanTick = 320;

		[Desc("Radius per mine laying order.")]
		public readonly int MineFieldRadius = 1;

		[Desc("Minefield is cancelled if allied actors with these target types are nearby.")]
		public readonly BitSet<TargetableType> AwayFromAlliedTargetTypes = default;


		[Desc("Radius for nearby allied-unit safety checks around a proposed minefield.")]
		public readonly int AwayFromCellDistance = 9;

		[ActorReference]
		[Desc("Owned or allied base-infrastructure actor types that define a no-mine exclusion zone. Front-line static defenses are deliberately omitted so minefields may still support defensive lines.")]
		public readonly FrozenSet<string> FriendlyBaseStructureTypes = FrozenSet<string>.Empty;

		[Desc("Minimum cells between the center of a proposed minefield and owned or allied base infrastructure. MineFieldRadius is added automatically so the whole field stays outside the exclusion zone.")]
		public readonly int FriendlyBaseExclusionRadius = 8;

		[Desc("Unified RiskModel tolerance for minelayer destinations and routes.")]
		public readonly FransRiskTolerance MinelayerRiskTolerance = FransRiskTolerance.Cautious;

		[Desc("Merge conflict positions into an existing favorite minefield within this many cells.")]
		public readonly int FavoritePositionDistance = 6;

		[Desc("Allow currently visible enemy mobile units from FransCombatIntel to provide a fair fallback direction when no combat location has been recorded.")]
		public readonly bool UseVisibleEnemyFallback = true;

		[Desc("Allow remembered StrategicMap enemy structures/frontline sectors to provide a coarse fair fallback direction after they have actually been observed.")]
		public readonly bool UseStrategicMemoryFallback = true;

		[Desc("Minimum confidence of a remembered enemy structure used as a fallback direction.")]
		public readonly int MinimumStrategicMemoryConfidencePercent = 35;

		[Desc("When true, FransMinelayer starts no new minefield cycle while any owned damaged aircraft has a usable FIX repair building. An already-running native mine refill is not interrupted.")]
		public readonly bool YieldFixToAircraftRepair = true;

		[ActorReference]
		[Desc("Repair-depot actor types whose service capacity is reserved for damaged aircraft ahead of new Minelayer refill cycles.")]
		public readonly FrozenSet<string> AircraftPriorityRepairActorTypes = FrozenSet<string>.Empty;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			// Cameo port: actor lists ship empty until per-faction ContentPack
			// wiring fills them; an empty set leaves the feature inactive.
			if (MaxPerAssign <= 0 || ScanTick <= 0 || MineFieldRadius < 0 || AwayFromCellDistance < 0 || FriendlyBaseExclusionRadius < 0 || FavoritePositionDistance < 0)
				throw new YamlException("FransMinelayer timing/radius settings are invalid.");
			if (MinimumStrategicMemoryConfidencePercent < 0 || MinimumStrategicMemoryConfidencePercent > 100)
				throw new YamlException($"{nameof(MinimumStrategicMemoryConfidencePercent)} must be between 0 and 100.");
		}

		public override object Create(ActorInitializer init) => new FransMinelayerBotModule(init.Self, this);
	}

	public class FransMinelayerBotModule : ConditionalTrait<FransMinelayerBotModuleInfo>, IBotTick, IBotRespondToAttack
	{
		const int MaxPositionCacheLength = 5;
		const int RepeatedAlertTicks = 40;

		readonly World world;
		readonly Player player;
		readonly Predicate<Actor> unitCannotBeOrdered;
		readonly Predicate<Actor> unitCannotBeOrderedOrIsBusy;
		readonly CPos?[] conflictPositionQueue = new CPos?[MaxPositionCacheLength];
		readonly CPos?[] favoritePositions = new CPos?[MaxPositionCacheLength];

		IFransCombatIntelService combatIntelService;
		IFransStrategicMapService strategicMapService;
		IFransRiskModelService riskModelService;
		PathFinder pathFinder;
		int minAssignRoleDelayTicks;
		int conflictPositionLength;
		int favoritePositionsLength;
		int currentFavoritePositionIndex;
		int alertedTicks;
		int nextAircraftRepairYieldLogTick;

		public FransMinelayerBotModule(Actor self, FransMinelayerBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			unitCannotBeOrdered = a => a == null || a.IsDead || !a.IsInWorld || a.Owner != player;
			unitCannotBeOrderedOrIsBusy = a => unitCannotBeOrdered(a) || !a.IsIdle;
		}

		protected override void Created(Actor self)
		{
			combatIntelService = self.Owner.PlayerActor.TraitsImplementing<IFransCombatIntelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransMinelayerBotModule requires FransCombatIntelBotModule.");
			strategicMapService = self.Owner.PlayerActor.TraitsImplementing<IFransStrategicMapService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransMinelayerBotModule requires FransStrategicMapBotModule.");
			riskModelService = self.Owner.PlayerActor.TraitsImplementing<IFransRiskModelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransMinelayerBotModule requires FransRiskModelBotModule.");
		}

		protected override void TraitEnabled(Actor self)
		{
			minAssignRoleDelayTicks = world.LocalRandom.Next(0, Info.ScanTick);
			alertedTicks = 0;
			conflictPositionLength = 0;
			favoritePositionsLength = 0;
			currentFavoritePositionIndex = 0;
			nextAircraftRepairYieldLogTick = 0;
			pathFinder = self.World.WorldActor.Trait<PathFinder>();
			FransBotLog.BotDebug(world,
				"{0}: FransMinelayer AIRCRAFT-FIX PRIORITY active: existing friendly-base mine exclusion remains, and no NEW minefield cycle starts while damaged aircraft has usable FIX service. Native refill already in progress is never interrupted.",
				player);
		}

		bool HasOwnedAircraftRepairDemand(out int count)
		{
			count = 0;
			if (!Info.YieldFixToAircraftRepair)
				return false;
			foreach (var actor in combatIntelService.OwnedActors)
			{
				if (actor == null || !actor.IsInWorld || actor.IsDead || actor.TraitOrDefault<Aircraft>() == null ||
					actor.GetDamageState() <= DamageState.Undamaged)
					continue;
				var repairable = actor.TraitOrDefault<Repairable>();
				var repairBuilding = repairable?.FindRepairBuilding(actor);
				if (repairBuilding == null || !repairBuilding.IsInWorld || repairBuilding.IsDead ||
					!Info.AircraftPriorityRepairActorTypes.Contains(repairBuilding.Info.Name.ToLowerInvariant()))
					continue;
				count++;
			}
			return count > 0;
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransMinelayer.BotTick");
			if (player.WinState != WinState.Undefined)
				return;

			if (alertedTicks > 0)
				alertedTicks--;

			if (--minAssignRoleDelayTicks > 0)
				return;

			minAssignRoleDelayTicks = Info.ScanTick;
			if (HasOwnedAircraftRepairDemand(out var waitingAircraft))
			{
				if (world.WorldTick >= nextAircraftRepairYieldLogTick)
				{
					nextAircraftRepairYieldLogTick = world.WorldTick + Math.Max(250, Info.ScanTick);
					FransBotLog.BotDebug(world,
						"{0}: FransMinelayer yields FIX service: {1} damaged aircraft currently has usable repair-depot service, so no new minefield/refill cycle is started this pass.",
						player, waitingAircraft);
				}
				return;
			}
			var minelayingPosition = CPos.Zero;
			var useFavoritePosition = false;
			var layMineOnHalfway = false;

			while (conflictPositionLength > 0)
			{
				minelayingPosition = conflictPositionQueue[0].Value;
				var hasInvalidActors = HasInvalidAlliedActorInCircle(
					world.Map.CenterOfCell(minelayingPosition), WDist.FromCells(Info.AwayFromCellDistance));
				if (hasInvalidActors || IsInsideFriendlyBaseExclusion(minelayingPosition))
					DequeueFirstConflictPosition();
				else
				{
					layMineOnHalfway = !riskModelService.EvaluateStrategicCell(
						minelayingPosition, FransRiskRole.Minelayer, Info.MinelayerRiskTolerance).IsPreferred;
					break;
				}
			}

			TraitPair<Minelayer>[] minelayers = null;
			if (conflictPositionLength == 0)
			{
				if (favoritePositionsLength == 0)
				{
					minelayers = world.ActorsWithTrait<Minelayer>()
						.Where(at => Info.MinelayingActorTypes.Contains(at.Actor.Info.Name))
						.Where(at => !unitCannotBeOrderedOrIsBusy(at.Actor))
						.ToArray();
					if (minelayers.Length == 0 || !TryGetFairFallbackTarget(out var fairTarget, out var source))
						return;

					foreach (var minelayer in minelayers)
					{
						var cells = pathFinder.FindPathToTargetCell(
							minelayer.Actor, [minelayer.Actor.Location], fairTarget, BlockedByActor.Immovable,
							customCost: cell => riskModelService.GetPathCost(minelayer.Actor, cell, FransRiskRole.Minelayer, Info.MinelayerRiskTolerance),
							laneBias: false);
						if (cells == null || cells.Count == 0)
							continue;

						if (!TryFindBaseSafePathCell(cells, cells.Count / 2, out var midpoint))
							continue;

						FransBotLog.BotDebug(world,
							"{0}: FransMinelayer uses fair {1} toward {2}; adding base-safe route midpoint {3} as a minefield candidate.",
							player, source, fairTarget, midpoint);
						EnqueueConflictPosition(midpoint);
						return;
					}

					return;
				}

				while (favoritePositionsLength > 0)
				{
					minelayingPosition = favoritePositions[currentFavoritePositionIndex].Value;
					var hasInvalidActors = HasInvalidAlliedActorInCircle(
						world.Map.CenterOfCell(minelayingPosition), WDist.FromCells(Info.AwayFromCellDistance));
					if (hasInvalidActors || IsInsideFriendlyBaseExclusion(minelayingPosition))
					{
						DeleteCurrentFavoritePosition();
						if (favoritePositionsLength == 0)
							return;
					}
					else
					{
						layMineOnHalfway = !riskModelService.EvaluateStrategicCell(
							minelayingPosition, FransRiskRole.Minelayer, Info.MinelayerRiskTolerance).IsPreferred;
						useFavoritePosition = true;
						break;
					}
				}
			}

			minelayers ??= world.ActorsWithTrait<Minelayer>()
				.Where(at => Info.MinelayingActorTypes.Contains(at.Actor.Info.Name))
				.Where(at => !unitCannotBeOrderedOrIsBusy(at.Actor))
				.ToArray();
			if (minelayers.Length == 0)
				return;

			var orderedActors = new List<Actor>();
			var returnCells = new Dictionary<Actor, CPos>();
			foreach (var minelayer in minelayers)
			{
				var targetRisk = riskModelService.EvaluateCell(minelayer.Actor, minelayingPosition,
					FransRiskRole.Minelayer, Info.MinelayerRiskTolerance);
				if (targetRisk.IsCritical)
					continue;

				var cells = pathFinder.FindPathToTargetCell(
					minelayer.Actor, [minelayer.Actor.Location], minelayingPosition, BlockedByActor.Immovable,
					customCost: cell => riskModelService.GetPathCost(minelayer.Actor, cell, FransRiskRole.Minelayer, Info.MinelayerRiskTolerance),
					laneBias: false);
				if (cells == null || cells.Count == 0)
					continue;

				var actualMinefieldPosition = minelayingPosition;
				if (layMineOnHalfway)
				{
					if (!TryFindBaseSafePathCell(cells, cells.Count / 4, out actualMinefieldPosition))
						continue;
				}

				if (IsInsideFriendlyBaseExclusion(actualMinefieldPosition))
					continue;

				orderedActors.Add(minelayer.Actor);
				returnCells[minelayer.Actor] = minelayer.Actor.Location;
				if (layMineOnHalfway)
				{
					minelayingPosition = actualMinefieldPosition;
					layMineOnHalfway = false;
				}

				if (orderedActors.Count >= Info.MaxPerAssign)
					break;
			}

			if (orderedActors.Count == 0)
			{
				if (useFavoritePosition)
					DeleteCurrentFavoritePosition();
				else
					DequeueFirstConflictPosition();
				return;
			}

			if (IsInsideFriendlyBaseExclusion(minelayingPosition))
			{
				FransBotLog.BotDebug(world,
					"{0}: FransMinelayer rejects final minefield center {1}: it overlaps the friendly-base infrastructure exclusion zone.",
					player, minelayingPosition);
				if (useFavoritePosition)
					DeleteCurrentFavoritePosition();
				else
					DequeueFirstConflictPosition();
				return;
			}

			if (useFavoritePosition)
				NextFavoritePositionIndex();
			else
			{
				DequeueFirstConflictPosition();
				AddPositionToFavoritePositions(minelayingPosition);
			}

			var vec = new CVec(Info.MineFieldRadius, Info.MineFieldRadius);
			bot.QueueOrder(new Order(
				"PlaceMinefield", null, Target.FromCell(world, minelayingPosition + vec), false,
				groupedActors: orderedActors.ToArray())
			{ ExtraLocation = minelayingPosition - vec });

			foreach (var actor in orderedActors)
			{
				if (!returnCells.TryGetValue(actor, out var returnCell) || actor.TraitOrDefault<Mobile>() == null ||
					riskModelService.EvaluateCell(actor, returnCell, FransRiskRole.Minelayer, Info.MinelayerRiskTolerance).IsCritical)
					continue;

				int CustomCost(CPos cell) => riskModelService.GetPathCost(actor, cell, FransRiskRole.Minelayer, Info.MinelayerRiskTolerance);
				var returnPath = pathFinder.FindPathToTargetCell(actor, [minelayingPosition], returnCell,
					BlockedByActor.Immovable, CustomCost, laneBias: false);
				if (returnPath == null || returnPath.Count == 0 ||
					riskModelService.EvaluateRoute(actor, returnPath, FransRiskRole.Minelayer, Info.MinelayerRiskTolerance).IsCritical)
					continue;

				// This queued Move is a continuation of PlaceMinefield, but both destination and route
				// have already been approved by the shared RiskModel.
				bot.QueueOrder(new Order("Move", actor, Target.FromCell(world, returnCell), true));
			}
		}

		bool TryGetFairFallbackTarget(out CPos target, out string source)
		{
			target = CPos.Zero;
			source = null;

			if (Info.UseVisibleEnemyFallback)
			{
				var visibleEnemies = combatIntelService.VisibleEnemies
					.Where(IsPreferredEnemyUnit)
					.ToArray();
				if (visibleEnemies.Length > 0)
				{
					var enemy = visibleEnemies.Random(world.LocalRandom);
					target = enemy.Location;
					source = $"visible enemy {enemy.Info.Name}";
					return true;
				}
			}

			if (!Info.UseStrategicMemoryFallback)
				return false;

			var rememberedStructures = strategicMapService.KnownEnemyStructures
				.Where(s => s.ConfidencePercent >= Info.MinimumStrategicMemoryConfidencePercent)
				.OrderByDescending(s => s.LastSeenWorldTick)
				.ThenByDescending(s => s.ConfidencePercent)
				.ToArray();
			if (rememberedStructures.Length > 0)
			{
				target = rememberedStructures[0].LastKnownLocation;
				source = $"remembered enemy structure {rememberedStructures[0].ActorType} ({rememberedStructures[0].ConfidencePercent}% confidence)";
				return true;
			}

			var priorities = strategicMapService.GetStrategicPrioritySectors(6)
				.Where(p => p.IsFrontlineSector || p.EnemyControlScore > 0 || p.EnemyStrategicObjectiveCount > 0)
				.OrderByDescending(p => p.TotalScore)
				.ToArray();
			if (priorities.Length == 0)
				return false;

			target = priorities[0].SuggestedStagingPoint ?? priorities[0].Target;
			source = "remembered/frontline StrategicMap sector";
			return true;
		}

		void DequeueFirstConflictPosition()
		{
			if (conflictPositionLength <= 0)
				return;
			for (var i = 1; i < conflictPositionLength; i++)
				conflictPositionQueue[i - 1] = conflictPositionQueue[i];
			conflictPositionQueue[conflictPositionLength - 1] = null;
			conflictPositionLength--;
		}

		void DeleteCurrentFavoritePosition()
		{
			for (var i = currentFavoritePositionIndex; i < favoritePositionsLength - 1; i++)
				favoritePositions[i] = favoritePositions[i + 1];
			favoritePositions[favoritePositionsLength - 1] = null;
			if (--favoritePositionsLength > 0)
				currentFavoritePositionIndex %= favoritePositionsLength;
		}

		void AddPositionToFavoritePositions(CPos cpos)
		{
			var favoriteDistSquare = Info.FavoritePositionDistance * Info.FavoritePositionDistance;
			var closestIndex = 0;
			var closestDistSquare = int.MaxValue;
			for (var i = 0; i < favoritePositionsLength; i++)
			{
				var lengthSquare = (favoritePositions[i].Value - cpos).LengthSquared;
				if (lengthSquare < closestDistSquare)
				{
					closestIndex = i;
					closestDistSquare = lengthSquare;
				}
			}

			if (closestDistSquare > favoriteDistSquare && favoritePositionsLength < favoritePositions.Length)
				favoritePositions[favoritePositionsLength++] = cpos;
			else if (favoritePositionsLength > 0)
			{
				var pos = favoritePositions[closestIndex].Value;
				favoritePositions[closestIndex] = (pos - cpos) / 2 + cpos;
			}
			else
				favoritePositions[favoritePositionsLength++] = cpos;
		}

		void NextFavoritePositionIndex()
		{
			currentFavoritePositionIndex = (currentFavoritePositionIndex + 1) % favoritePositionsLength;
		}

		bool IsPreferredEnemyUnit(Actor actor)
		{
			if (actor == null || actor.IsDead || !actor.IsInWorld ||
				player.RelationshipWith(actor.Owner) != PlayerRelationship.Enemy || actor.Info.HasTraitInfo<HuskInfo>())
				return false;

			var targetTypes = actor.GetEnabledTargetTypes();
			return !targetTypes.IsEmpty && !targetTypes.Overlaps(Info.IgnoredEnemyTargetTypes);
		}

		bool IsInsideFriendlyBaseExclusion(CPos cell)
		{
			if (Info.FriendlyBaseExclusionRadius <= 0 || Info.FriendlyBaseStructureTypes.Count == 0)
				return false;

			var radius = Info.FriendlyBaseExclusionRadius + Info.MineFieldRadius;
			var radiusSquared = radius * radius;
			return world.ActorsHavingTrait<Building>().Any(actor =>
				actor != null && actor.IsInWorld && !actor.IsDead &&
				(actor.Owner == player || PlayerRelationship.Ally.HasRelationship(player.RelationshipWith(actor.Owner))) &&
				Info.FriendlyBaseStructureTypes.Contains(actor.Info.Name) &&
				(actor.Location - cell).LengthSquared <= radiusSquared);
		}

		bool TryFindBaseSafePathCell(IReadOnlyList<CPos> cells, int preferredIndex, out CPos cell)
		{
			cell = default;
			if (cells == null || cells.Count == 0)
				return false;

			preferredIndex = preferredIndex.Clamp(0, cells.Count - 1);
			for (var offset = 0; offset < cells.Count; offset++)
			{
				var forward = preferredIndex + offset;
				if (forward < cells.Count && !IsInsideFriendlyBaseExclusion(cells[forward]))
				{
					cell = cells[forward];
					return true;
				}

				var backward = preferredIndex - offset;
				if (backward >= 0 && backward != forward && !IsInsideFriendlyBaseExclusion(cells[backward]))
				{
					cell = cells[backward];
					return true;
				}
			}

			return false;
		}

		bool HasInvalidAlliedActorInCircle(WPos pos, WDist dist)
		{
			return world.FindActorsInCircle(pos, dist).Any(actor =>
			{
				if (actor.Owner.RelationshipWith(player) != PlayerRelationship.Ally)
					return false;

				var targetTypes = actor.GetEnabledTargetTypes();
				return !targetTypes.IsEmpty && targetTypes.Overlaps(Info.AwayFromAlliedTargetTypes);
			});
		}

		void EnqueueConflictPosition(CPos cell)
		{
			if (conflictPositionLength < MaxPositionCacheLength)
				conflictPositionQueue[conflictPositionLength++] = cell;
			else
				conflictPositionQueue[MaxPositionCacheLength - 1] = cell;
		}

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			if (alertedTicks > 0 || e.Attacker == null)
				return;

			// An attack on our actor is legitimate information, but a hidden attacker must
			// not leak its live type or position into Fransbot. Only inspect/filter the
			// attacker when it is currently viewable; otherwise remember the victim cell.
			var attackerVisible = e.Attacker.CanBeViewedByPlayer(player);
			if (attackerVisible && !IsPreferredEnemyUnit(e.Attacker))
				return;

			alertedTicks = RepeatedAlertTicks;
			if (HasInvalidAlliedActorInCircle(self.CenterPosition, WDist.FromCells(Info.AwayFromCellDistance)))
				return;

			var targetTypes = self.GetEnabledTargetTypes();
			var useAttackerLocation = attackerVisible && !targetTypes.IsEmpty && targetTypes.Overlaps(Info.UseEnemyLocationTargetTypes);
			var pos = useAttackerLocation ? e.Attacker.Location : self.Location;
			if (IsInsideFriendlyBaseExclusion(pos))
				return;
			EnqueueConflictPosition(pos);
		}
	}
}
