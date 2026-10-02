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
using OpenRA.Graphics;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.AS.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Put this on the Player actor. Manages bot harvesters to ensure they always continue harvesting as long as there are resources on the map.")]
	public class HarvesterBotModuleCAInfo : ConditionalTraitInfo, NotBefore<IResourceLayerInfo>, NotBefore<ResourceMapBotModuleInfo>
	{
		[Desc("Actor types that are considered harvesters. If harvester count drops below RefineryTypes count, a new harvester is built.",
			"Leave empty to disable harvester replacement. Currently only needed by harvester replacement system.")]
		public readonly HashSet<string> HarvesterTypes = new HashSet<string>();

		[Desc("Number of harvesters per refinery to maintain.")]
		public readonly int HarvestersPerRefinery = 2;

		[Desc("Maximum number of harvesters to build.")]
		public readonly int MaxHarvesters = 8;

		[Desc("Actor types that are counted as refineries. Currently only needed by harvester replacement system.")]
		public readonly HashSet<string> RefineryTypes = new HashSet<string>();

		[Desc("Interval (in ticks) between giving out orders to idle harvesters.")]
		public readonly int ScanForIdleHarvestersInterval = 50;

		[Desc("Interval (in ticks) between giving out orders to idle harvesters.")]
		public readonly int ScanForLowEffectHarvestersInterval = 433;

		[Desc("When an idle harvester cannot find resources, increase the wait to this many scan intervals.")]
		public readonly int ScanIntervalMultiplerWhenNoResources = 5;

		[Desc("Interval (in ticks) between checking whether to produce new harvesters.")]
		public readonly int ProduceHarvestersInterval = 375;

		[Desc("Additional harvesters to build.")]
		public readonly int AdditionalHarvesters = 0;

		[Desc("Avoid enemy actors nearby when searching for a new resource patch. Should be somewhere near the max weapon range.")]
		public readonly WDist HarvesterEnemyAvoidanceRadius = WDist.FromCells(8);

		[Desc("For each enemy within the threat radius, apply the following cost multiplier for every cell that needs to be moved through.")]
		public readonly int HarvesterEnemyAvoidanceCostMultipler = 20;

		[Desc("How many resource cells should a harvester response for.")]
		public readonly int ResourceCellsPerHarvester = 4;

		[Desc("How many harvester should player owned at least.")]
		public readonly int InitialHarvesters = 4;

		[Desc("Prefer resource cells on fields that can still absorb a harvester (own harvesters below",
			"ResourceCellsCount / ResourceCellsPerHarvester, minimum 1) when an idle harvester picks a new patch.",
			"Needs ResourceMapBotModule; default off keeps the nearest-cell search untouched.")]
		public readonly bool SpreadHarvestFields = false;

		[Desc("Maximum harvesters the low-effect scan relocates per scan. Values above 1 also pick the source field",
			"by real surplus (own harvesters - ResourceCellsCount / ResourceCellsPerHarvester) instead of the first",
			"overstaffed field. 1 preserves the original single-relocation scan; 0 disables relocation orders.")]
		public readonly int RebalanceMaxPerScan = 1;

		public override object Create(ActorInitializer init) { return new HarvesterBotModuleCA(init.Self, this); }
	}

	public class HarvesterBotModuleCA : ConditionalTrait<HarvesterBotModuleCAInfo>, IBotTick, INotifyActorDisposing, IWorldLoaded, IBotRespondToAttack
	{
		class HarvesterTraitWrapper
		{
			public readonly Actor Actor;
			public readonly Harvester Harvester;
			public readonly DockClientManager DockClientManager;
			public readonly Parachutable Parachutable;
			public readonly Mobile Mobile;
			public int NoResourcesCooldown { get; set; }

			public HarvesterTraitWrapper(Actor actor)
			{
				Actor = actor;
				Harvester = actor.Trait<Harvester>();
				DockClientManager = actor.Trait<DockClientManager>();
				Parachutable = actor.TraitOrDefault<Parachutable>();
				Mobile = actor.Trait<Mobile>();
			}
		}

		readonly World world;
		readonly Player player;
		readonly Func<Actor, bool> unitCannotBeOrdered;
		readonly Dictionary<Actor, HarvesterTraitWrapper> harvesters = [];
		readonly Stack<HarvesterTraitWrapper> harvestersNeedingOrders = [];
		readonly ActorIndex.OwnerAndNamesAndTrait<BuildingInfo> refineries;
		readonly ActorIndex.OwnerAndNamesAndTrait<HarvesterInfo> harvestersIndex;
		readonly Dictionary<CPos, string> resourceTypesByCell = [];

		IResourceLayer resourceLayer;
		ResourceClaimLayer claimLayer;
		IBotRequestUnitProduction[] requestUnitProduction;
		ResourceMapBotModule resourceMapModule;

		int scanForLowEffectHarvestersTicks;
		int scanForEnoughHarvestersTicks;
		int scanForIdleHarvestersTicks;
		int respondToAttackCooldown = 40; // prevent too many responses to the same wave of attacks
		bool firstTick = true;
		bool limitsRechecked;

		BotLimits botLimits;
		int harvesterLimit;

		// Cameo: the shared @generic instance also serves classicbot — armed spread/rebalance behaviour
		// applies to genericbot only so the A/B keeps classic untouched. Resolved lazily from the bot's
		// ModularBot info (IBot.Info.Type); null-safe before the bot trait answers.
		bool? isClassicBot;
		bool IsClassicBot => isClassicBot ??= player.PlayerActor.TraitsImplementing<IBot>()
			.FirstOrDefault()?.Info.Type == "classic";

		public HarvesterBotModuleCA(Actor self, HarvesterBotModuleCAInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			unitCannotBeOrdered = a => a.Owner != self.Owner || a.IsDead || !a.IsInWorld || a.Info.HasTraitInfo<BaseSpawnerSlaveInfo>();
			refineries = new ActorIndex.OwnerAndNamesAndTrait<BuildingInfo>(world, info.RefineryTypes, player);
			harvestersIndex = new ActorIndex.OwnerAndNamesAndTrait<HarvesterInfo>(world, info.HarvesterTypes, player);
		}

		protected override void Created(Actor self)
		{
			requestUnitProduction = self.Owner.PlayerActor.TraitsImplementing<IBotRequestUnitProduction>().ToArray();
		}

		protected override void TraitEnabled(Actor self)
		{
			resourceLayer = world.WorldActor.TraitOrDefault<IResourceLayer>();
			claimLayer = world.WorldActor.TraitOrDefault<ResourceClaimLayer>();

			botLimits = self.TraitsImplementing<BotLimits>().FirstEnabledTraitOrDefault();
			if (botLimits != null)
				harvesterLimit = botLimits.Info.HarvesterLimit;

			limitsRechecked = false;

			// Avoid all AIs scanning for idle harvesters on the same tick, randomize their initial scan delay.
			scanForIdleHarvestersTicks = world.LocalRandom.Next(Info.ScanForIdleHarvestersInterval, Info.ScanForIdleHarvestersInterval * 2);

			scanForLowEffectHarvestersTicks = world.LocalRandom.Next(Info.ScanForLowEffectHarvestersInterval);

			scanForEnoughHarvestersTicks = Info.ProduceHarvestersInterval;
		}

		public void WorldLoaded(World w, WorldRenderer wr)
		{
			if (resourceLayer != null)
			{
				foreach (var cell in w.Map.AllCells)
				{
					var resource = resourceLayer.GetResource(cell);
					if (resource.Type != null)
						resourceTypesByCell.Add(cell, resource.Type);
				}

				resourceLayer.CellChanged += ResourceCellChanged;
			}
		}

		void ResourceCellChanged(CPos cell, string resourceType)
		{
			if (resourceType == null)
				resourceTypesByCell.Remove(cell);
			else
				resourceTypesByCell[cell] = resourceType;
		}

		void IBotTick.BotTick(IBot bot)
		{
			respondToAttackCooldown--;

			// LC4: the BotLimits cached in TraitEnabled can predate the tier condition (BotLimitsResolver).
			if (!limitsRechecked)
			{
				botLimits = BotLimitsResolver.Recheck(player, botLimits, nameof(HarvesterBotModuleCA));
				harvesterLimit = botLimits?.Info.HarvesterLimit ?? 0;
				limitsRechecked = true;
			}

			if (resourceLayer == null || resourceLayer.IsEmpty)
				return;

			if (firstTick)
			{
				resourceMapModule = bot.Player.PlayerActor.TraitsImplementing<ResourceMapBotModule>().FirstOrDefault(t => t.IsTraitEnabled());
				firstTick = false;
			}

			// Find idle harvesters and give them orders:
			// PERF: FindNextResource is expensive, so only perform one search per tick.
			var searchedForResources = false;
			while (harvestersNeedingOrders.TryPop(out var hno) && !searchedForResources)
				searchedForResources = HarvestIfAble(bot, hno);

			if (--scanForIdleHarvestersTicks <= 0)
			{
				FindIdleHarvester();
				scanForIdleHarvestersTicks = Info.ScanForIdleHarvestersInterval;
			}

			if (--scanForLowEffectHarvestersTicks <= 0)
			{
				scanForLowEffectHarvestersTicks = Info.ScanForLowEffectHarvestersInterval;
				if (resourceMapModule != null)
					FindAndOrderLowEffectHarvesterOnResourceMap(bot);
			}

			if (--scanForEnoughHarvestersTicks <= 0)
			{
				ProduceHarvesters(bot);
				scanForEnoughHarvestersTicks = Info.ProduceHarvestersInterval;
			}
		}

		void FindIdleHarvester()
		{
			var toRemove = harvesters.Keys.Where(unitCannotBeOrdered).ToList();
			foreach (var a in toRemove)
				harvesters.Remove(a);

			// Find new harvesters
			// TODO: Look for a more performance-friendly way to update this list
			var newHarvesters = world.ActorsHavingTrait<Harvester>().Where(a => !unitCannotBeOrdered(a) && !harvesters.ContainsKey(a));
			foreach (var a in newHarvesters)
				harvesters[a] = new HarvesterTraitWrapper(a);

			harvestersNeedingOrders.Clear();
			foreach (var h in harvesters)
				harvestersNeedingOrders.Push(h.Value);
		}

		protected void ProduceHarvesters(IBot bot)
		{
			// Less harvesters than refineries - build a new harvester
			var unitBuilder = requestUnitProduction.FirstEnabledTraitOrDefault();
			if (unitBuilder != null && Info.HarvesterTypes.Count > 0)
			{
				var numHarvesters = AIUtils.CountActorByCommonName(harvestersIndex);

				if ((harvesterLimit > 0 && numHarvesters >= harvesterLimit) || numHarvesters >= Info.MaxHarvesters)
					return;

				var harvCountTooLow = numHarvesters < AIUtils.CountActorByCommonName(refineries) * Info.HarvestersPerRefinery + Info.AdditionalHarvesters;
				if (harvCountTooLow)
				{
					var harvInfo = AIUtils.GetBuildableInfoByCommonName(Info.HarvesterTypes, player);
					if (harvInfo != null && unitBuilder.RequestedProductionCount(bot, harvInfo.Name) == 0)
						unitBuilder.RequestUnitProduction(bot, harvInfo.Name);
				}
			}
		}

		void FindAndOrderLowEffectHarvesterOnResourceMap(IBot bot)
		{
			CPos? worstEffectIndice = null;
			var worstEffectHarvesterCount = int.MaxValue;

			// Cameo (harvester spread): RebalanceMaxPerScan > 1 switches the source-field pick from the
			// binary lackHarvs < 0 test — which flattens every overstaffed field to -1, so at most one
			// harvester moves per scan — to the field with the biggest real surplus, and lets a scan
			// relocate up to that many harvesters. The default 1 keeps the original behaviour verbatim.
			var multiRelocate = Info.RebalanceMaxPerScan > 1 && !IsClassicBot;
			var maxSurplus = 0;
			var worstEffectIndex = -1;

			var lackHarvesterIndices = new List<(int Attraction, int LackHarvs, CPos ResoueceCenter, int Index)>();

			/*
			 * indiceSideLengthSquare (which is equal to indiceSideLength * indiceSideLength) is used as the basic unit to calculate the attraction of a candidate,
			 * we compare the attraction on the same scale on different factors, such as ally refinery within range or threats nearby.
			 * Note: this function requires an enabled resourceMapModule.
			 */

			var indiceSideLengthSquare = resourceMapModule.GetIndiceSideLength() * resourceMapModule.GetIndiceSideLength();

			for (var i = 0; i < resourceMapModule.GetIndicesLength(); i++)
			{
				var baseIndice = resourceMapModule.GetIndice(i);

				// Initial attraction is indiceSideLengthSquare >> 5
				var attraction = indiceSideLengthSquare >> 5;

				attraction += baseIndice.ResourceCellsCount - baseIndice.PlayerHarvetserCount * Info.ResourceCellsPerHarvester;

				var lackHarvs = attraction > 0 ? attraction / Info.ResourceCellsPerHarvester : (attraction == 0 && baseIndice.ResourceCellsCount > 0 ? 1 : -1);

				// Reduce the attraction of resource cells count
				attraction >>= 1;

				if (baseIndice.PlayerRefineryCount <= 0 && lackHarvs > 0)
					lackHarvs = 1;

				// If there is enemy in indice, reduce attraction by indiceSideLengthSquare << 4
				// If there is enemy in the nearby indices. reduce attraction by indiceSideLengthSquare >> 5 (equals to initial attraction)
				if (baseIndice.EnemyBaseCount > 0 || baseIndice.EnemyUnitCount > 0)
					attraction -= indiceSideLengthSquare << 4;
				else
				{
					var (indiceCount, nearbyEnemy, nearbyEnemyBase) = resourceMapModule.GetNearbyIndicesThreat(i);
					if (nearbyEnemyBase + nearbyEnemy > 0)
						attraction -= indiceSideLengthSquare >> 5;
				}

				if (baseIndice.PlayerRefineryCount > 0)
					attraction += indiceSideLengthSquare;

				if (baseIndice.ResourceCellsCount > 0 && attraction > 0 && lackHarvs > 0)
					lackHarvesterIndices.Add((attraction, lackHarvs, baseIndice.ResourceCellsCenter, i));

				if (multiRelocate)
				{
					// Real surplus: own harvesters beyond the field's capacity — a magnitude, not a flag.
					var surplus = baseIndice.PlayerHarvetserCount - baseIndice.ResourceCellsCount / Info.ResourceCellsPerHarvester;
					if (surplus > maxSurplus)
					{
						maxSurplus = surplus;
						worstEffectIndex = i;
						worstEffectIndice = baseIndice.IndiceCenter;
					}
				}
				else if (lackHarvs < worstEffectHarvesterCount && lackHarvs < 0)
				{
					worstEffectHarvesterCount = lackHarvs;
					worstEffectIndice = baseIndice.IndiceCenter;
				}
			}

			if (worstEffectIndice == null)
				return;

			// Armed: bounded by the source field's real surplus and the configured per-scan cap.
			// Flag-off: -worstEffectHarvesterCount is always 1 and RebalanceMaxPerScan defaults to 1,
			// so this reproduces the original value exactly; 0 disables relocation orders.
			var harvestersCanAssign = Math.Min(
				multiRelocate ? maxSurplus : -worstEffectHarvesterCount, Info.RebalanceMaxPerScan);

			// Try to find a new resource patch for the worst effect harvester
			var searchRadius = resourceMapModule.GetIndiceScanRadius();

			var harvesters = world.FindActorsInCircle(world.Map.CenterOfCell(worstEffectIndice.Value), WDist.FromCells(searchRadius))
				.Where(a => a.Owner == player && !a.IsDead && a.IsInWorld && resourceMapModule.Info.HarvesterTypes.Contains(a.Info.Name)).ToList();

			// Armed only: the lease registry (harvesters are normally unleased, but a claimed one is
			// mid-job elsewhere — e.g. a mission or transport run). Resolved per use, never cached.
			var leases = multiRelocate ? BotUnitLeases.Of(player) : null;

			var pathDistanceSquareFactor = resourceMapModule.GetIndiceRowCount() * resourceMapModule.GetIndiceRowCount()
					+ resourceMapModule.GetIndiceColumnCount() * resourceMapModule.GetIndiceColumnCount();

			harvestersCanAssign = Math.Min(harvestersCanAssign, harvesters.Count - 1);
			if (harvestersCanAssign > 0)
			{
				foreach (var (_, lackHarvs, resourceCenter, index) in
					lackHarvesterIndices.OrderByDescending(d => d.Attraction - (harvesters[0].Location - d.ResoueceCenter).LengthSquared / pathDistanceSquareFactor))
				{
					if (harvestersCanAssign <= 0)
						break;

					// Armed: never "relocate" a harvester onto the field it is leaving — under the
					// real-surplus metric a field can be both the most overstaffed source and still
					// attractive enough to enter the destination list, which the binary flag-off
					// test could never produce (lackHarvs < 0 fields never enter this list).
					if (multiRelocate && index == worstEffectIndex)
						continue;

					var needHarvs = lackHarvs;
					var nearbyResources = world.Map.FindTilesInAnnulus(resourceCenter, 0, resourceMapModule.GetIndiceScanRadius())
					.Where(c => resourceMapModule.Info.ValuableResourceTypes.Contains(resourceLayer.GetResource(c).Type)
					&& (harvesters[0].Location - resourceCenter).LengthSquared >= (c - harvesters[0].Location).LengthSquared).ToArray();

					if (nearbyResources.Length <= 0 || needHarvs <= 0)
						continue;

					var usedHarvs = new HashSet<Actor>();
					foreach (var harv in harvesters)
					{
						if (needHarvs <= 0 || harvestersCanAssign <= 0)
							break;

						// Armed: only idle-equivalent harvesters are fair game — idle or running the
						// normal harvest loop (FindAndDeliverResources covers travel/harvest/dock),
						// and never a unit another module holds a lease on. Flag-off keeps the
						// original unconditional orders.
						if (multiRelocate &&
							((!harv.IsIdle && harv.CurrentActivity is not FindAndDeliverResources)
								|| BotUnitLeases.IsClaimedByOther(leases, harv, nameof(HarvesterBotModuleCA))))
							continue;

						var parach = harv.TraitOrDefault<Parachutable>();
						if (parach != null && parach.IsInAir)
						{
							harvestersCanAssign--;
							usedHarvs.Add(harv);
							continue;
						}

						var mobile = harv.TraitOrDefault<Mobile>();
						if (mobile != null)
						{
							var tcell = nearbyResources.Random(world.LocalRandom);
							if (mobile.PathFinder.PathMightExistForLocomotorBlockedByImmovable(mobile.Locomotor, harv.Location, tcell))
							{
								bot.QueueOrder(new Order("Harvest", harv, Target.FromCell(world, tcell), false));
								needHarvs--;
								harvestersCanAssign--;
								usedHarvs.Add(harv);
							}
							else
							{
								if (needHarvs > 1)
									needHarvs = 1;
								else
									break;
							}
						}
						else
						{
							bot.QueueOrder(new Order("Harvest", harv, Target.FromCell(world, nearbyResources.Random(world.LocalRandom)), false));
							needHarvs--;
							harvestersCanAssign--;
							usedHarvs.Add(harv);
						}
					}

					harvesters.RemoveAll(usedHarvs.Contains);
				}
			}
		}

		// Returns true if FindNextResource was called.
		bool HarvestIfAble(IBot bot, HarvesterTraitWrapper h)
		{
			if (h.Actor.IsDead || !h.Actor.IsInWorld || h.Mobile == null)
				return false;

			if (!h.Actor.IsIdle)
			{
				// Ignore this actor if FindAndDeliverResources is working fine or it is performing a different activity
				if (h.Actor.CurrentActivity is not FindAndDeliverResources act || !act.LastSearchFailed)
					return false;
			}

			if (h.NoResourcesCooldown > 0)
			{
				h.NoResourcesCooldown--;
				return false;
			}

			if (h.Parachutable != null && h.Parachutable.IsInAir)
				return false;

			// Tell the idle harvester to quit slacking:
			var newSafeResourcePatch = FindNextResource(h.Actor, h);
			AIUtils.BotDebug($"AI: Harvester {h.Actor} is idle. Ordering to {newSafeResourcePatch} in search for new resources.");
			if (newSafeResourcePatch.Type != TargetType.Invalid)
				bot.QueueOrder(new Order("Harvest", h.Actor, newSafeResourcePatch, false));
			else
				h.NoResourcesCooldown = Info.ScanIntervalMultiplerWhenNoResources;

			return true;
		}

		Target FindNextResource(Actor actor, HarvesterTraitWrapper harv)
		{
			// Prefer resource nearby to the nearest drop off point, otherwise scan from the current location.
			var scanFromActor = harv.DockClientManager.ClosestDock(null, ignoreOccupancy: true)?.Actor ?? actor;

			var targets = resourceTypesByCell
				.Where(kvp =>
					harv.Harvester.Info.Resources.Contains(kvp.Value) &&
					claimLayer.CanClaimCell(actor, kvp.Key))
				.Select(kvp => kvp.Key);

			// Cameo (harvester spread): drop cells of fields already at capacity so idle harvesters
			// scatter to fields that can still absorb one. Snapshot per-field occupancy ONCE per
			// call — ResourceMapBotModule.FindClosestIndiceFromCPos is O(indices) and must not run
			// per cell. Default off: targets untouched.
			if (Info.SpreadHarvestFields && !IsClassicBot && resourceMapModule != null)
			{
				var fieldCount = resourceMapModule.GetIndicesLength();
				if (fieldCount > 0)
				{
					var fields = new List<(CPos Center, int ResourceCells, int Harvesters)>(fieldCount);
					for (var i = 0; i < fieldCount; i++)
					{
						var indice = resourceMapModule.GetIndice(i);
						if (indice != null)
							fields.Add((indice.IndiceCenter, indice.ResourceCellsCount, indice.PlayerHarvetserCount));
					}

					targets = FilterUnsaturatedFields(targets, fields, Info.ResourceCellsPerHarvester);
				}
			}

			var avoidanceCostForBin = new Dictionary<int2, int>();
			var cellRadius = Info.HarvesterEnemyAvoidanceRadius.Length / 1024;
			var minCellCost = harv.Mobile.Locomotor.Info.TerrainSpeeds.Values.Min(ti => ti.Cost);
			var cellCostMultiplier = Info.HarvesterEnemyAvoidanceCostMultipler;

			static int2 CellToBin(CPos cell, int cellRadius)
			{
				return new int2(
					cell.X / cellRadius,
					cell.Y / cellRadius);
			}

			static int CalculateAvoidanceCostForBin(World world, int2 bin, int cellRadius, Actor actor, int minCellCost, int cellCostMultipler)
			{
				// Bins are overlapping, this allows actors to apply threat in both directions when they're at the edge.
				// If the bins didn't overlap, actors along the edge of a bin only affect that bin, and not the bin next to it,
				// despite the fact the are an equal risk to both.
				var r = WDist.FromCells(cellRadius);
				var vec = new WVec(r, r, WDist.Zero);
				var originCell = new CPos(bin.X * cellRadius + cellRadius / 2, bin.Y * cellRadius + cellRadius / 2);
				var origin = world.Map.CenterOfCell(originCell);
				var threatActors = world.ActorMap.ActorsInBox(origin - vec, origin + vec)
					.Where(u => !u.IsDead && actor.Owner.RelationshipWith(u.Owner) == PlayerRelationship.Enemy);

				// For each actor in the threat radius, every cell we want to move is an extra cost than a threat-free area.
				return threatActors.Count() * minCellCost * cellCostMultipler;
			}

			var path = harv.Mobile.PathFinder.FindPathToTargetCells(
				actor, scanFromActor.Location, targets, BlockedByActor.Stationary,
				loc =>
				{
					// Avoid areas with enemies.
					var bin = CellToBin(loc, cellRadius);
					if (avoidanceCostForBin.TryGetValue(bin, out var avoidanceCost))
						return avoidanceCost;

					// PERF: Calculate a "bin" for a threat area.
					// This allows future custom cost checks to reuse the result for that area,
					// rather than calculating it fresh for every cell explored for the path.
					avoidanceCost = CalculateAvoidanceCostForBin(world, bin, cellRadius, actor, minCellCost, cellCostMultiplier);
					avoidanceCostForBin.Add(bin, avoidanceCost);
					return avoidanceCost;
				});

			if (path.Count == 0)
				return Target.Invalid;

			return Target.FromCell(world, path[0]);
		}

		/// <summary>
		/// Keeps only the candidate cells whose nearest resource field can still absorb a harvester —
		/// a field is saturated once its own-harvester count reaches ResourceCells / cellsPerHarvester
		/// (clamped to a minimum capacity of 1). Each cell belongs to the field whose centre is nearest
		/// (strictly smaller distance wins; the first field takes ties — the same rule
		/// ResourceMapBotModule.FindClosestIndiceFromCPos uses). Falls back to the full candidate list
		/// when every field is saturated or <paramref name="fields"/> is empty, so the caller's
		/// pathfind always sees a usable target set.
		/// </summary>
		public static IEnumerable<CPos> FilterUnsaturatedFields(IEnumerable<CPos> candidates,
			IReadOnlyList<(CPos Center, int ResourceCells, int Harvesters)> fields, int cellsPerHarvester)
		{
			var list = candidates as IReadOnlyList<CPos> ?? candidates.ToList();
			if (list.Count == 0 || fields.Count == 0)
				return list;

			var perHarvester = Math.Max(1, cellsPerHarvester);
			var unsaturated = new List<CPos>(list.Count);
			foreach (var cell in list)
			{
				var bestDist = int.MaxValue;
				var bestField = 0;
				for (var i = 0; i < fields.Count; i++)
				{
					var dist = (fields[i].Center - cell).LengthSquared;
					if (dist < bestDist)
					{
						bestDist = dist;
						bestField = i;
					}
				}

				var field = fields[bestField];
				if (field.Harvesters < Math.Max(1, field.ResourceCells / perHarvester))
					unsaturated.Add(cell);
			}

			return unsaturated.Count > 0 ? unsaturated : list;
		}

		void INotifyActorDisposing.Disposing(Actor self)
		{
			refineries.Dispose();
			harvestersIndex.Dispose();

			if (resourceLayer != null)
				resourceLayer.CellChanged -= ResourceCellChanged;
		}

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			if (respondToAttackCooldown > 0 || !Info.HarvesterTypes.Contains(self.Info.Name)
				|| e.Attacker == null || e.Attacker.IsDead || !e.Attacker.AppearsHostileTo(self))
				return;

			var parach = self.TraitOrDefault<Parachutable>();
			if (parach != null && parach.IsInAir)
				return;

			var dockClientManager = self.Trait<DockClientManager>();
			if (dockClientManager.ReservedHostActor != null)
				return;

			respondToAttackCooldown = 30;
			var dock = dockClientManager.ClosestDock(null, forceEnter: true, ignoreOccupancy: true);
			if (dock == null)
				return;

			var harvester = self.Trait<Harvester>();
			if (!harvester.IsEmpty)
			{
				bot.QueueOrder(new Order("ForceDock", self, Target.FromActor(dock.Value.Actor), false));
				return;
			}

			// Empty harvesters have nothing to unload. Retreat clear of the refinery entrance,
			// then resume harvesting instead of attempting a dock that will be rejected.
			var mobile = self.Trait<Mobile>();
			var deliveryLoc = world.Map.CellContaining(dock.Value.Trait.DockPosition);
			var preferredRetreatLoc = deliveryLoc + harvester.Info.UnblockCell;
			bool IsValidRetreatLoc(CPos loc)
			{
				return loc != deliveryLoc &&
					mobile.CanEnterCell(loc, check: BlockedByActor.Immovable) &&
					mobile.CanStayInCell(loc) &&
					mobile.PathFinder.PathMightExistForLocomotorBlockedByImmovable(
						mobile.Locomotor, self.Location, loc);
			}

			var retreatLoc = mobile.NearestCell(preferredRetreatLoc, IsValidRetreatLoc, 1, 5);
			var hasRetreat = IsValidRetreatLoc(retreatLoc);
			if (hasRetreat)
				bot.QueueOrder(new Order("Move", self, Target.FromCell(world, retreatLoc), false));

			var wrapper = harvesters.TryGetValue(self, out var existingWrapper)
				? existingWrapper
				: new HarvesterTraitWrapper(self);
			var resourceTarget = FindNextResource(self, wrapper);
			if (resourceTarget.Type != TargetType.Invalid)
				bot.QueueOrder(new Order("Harvest", self, resourceTarget, hasRetreat));
		}
	}
}
