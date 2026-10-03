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

using System.Collections.Frozen;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Builds and sends supply trucks to allied cash receivers. Recipient need is preserved, while the shared FransRiskModel selects safe destinations and rejects dangerous delivery corridors.")]
	public class FransSupplyTruckBotModuleInfo : ConditionalTraitInfo, Requires<PlayerResourcesInfo>
	{
		[ActorReference]
		[Desc("Actor types that can deliver cash and should be managed as supply trucks.")]
		public readonly FrozenSet<string> SupplyTruckTypes = FrozenSet<string>.Empty;

		[ActorReference]
		[Desc("Allied actor types that may receive deliveries. Leave empty to allow every actor with AcceptsDeliveredCash.")]
		public readonly FrozenSet<string> DeliveryTargetTypes = FrozenSet<string>.Empty;

		[Desc("Only request a new supply truck when the bot has at least this much cash and resources.")]
		public readonly int MinimumCashForProduction = 5000;

		[Desc("Delay in ticks between scans for production and delivery opportunities.")]
		public readonly int ScanInterval = 125;

		[Desc("Minimum delay in ticks after requesting a supply truck before another may be requested.")]
		public readonly int ProductionRequestCooldown = 1500;

		[Desc("Maximum total number of owned, queued, or externally requested supply trucks.")]
		public readonly int MaximumSupplyTrucks = 1;

		[Desc("Only deliver to allied actors that are currently visible to the bot.")]
		public readonly bool CheckTargetVisibility = true;

		[Desc("Unified RiskModel tolerance for supply-truck destination and corridor safety.")]
		public readonly FransRiskTolerance DeliveryRiskTolerance = FransRiskTolerance.Cautious;

		[Desc("Prefer allied players explicitly reporting Struggling through FransEconomicState, then break ties by lowest combined cash/resources.")]
		public readonly bool PrioritizeLowestFunds = true;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);

			if (MinimumCashForProduction < 0)
				throw new YamlException($"{nameof(MinimumCashForProduction)} cannot be negative.");

			if (ScanInterval <= 0)
				throw new YamlException($"{nameof(ScanInterval)} must be greater than zero.");

			if (ProductionRequestCooldown < 0)
				throw new YamlException($"{nameof(ProductionRequestCooldown)} cannot be negative.");

			if (MaximumSupplyTrucks <= 0)
				throw new YamlException($"{nameof(MaximumSupplyTrucks)} must be greater than zero.");
		}

		public override object Create(ActorInitializer init) { return new FransSupplyTruckBotModule(init.Self, this); }
	}

	public class FransSupplyTruckBotModule : ConditionalTrait<FransSupplyTruckBotModuleInfo>,
		IBotTick, IGameSaveTraitData, INotifyActorDisposing
	{
		readonly World world;
		readonly Player player;
		readonly ActorIndex.OwnerAndNames supplyTrucks;

		IBotRequestUnitProduction[] requestUnitProduction;
		PlayerResources playerResources;
		IFransRiskModelService riskModelService;
		IFransCombatIntelService combatIntelService;
		int scanTicks;
		int productionRequestCooldownTicks;
		bool awaitingProductionConfirmation;

		public FransSupplyTruckBotModule(Actor self, FransSupplyTruckBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;

			if (world.Type == WorldType.Editor)
				return;

			supplyTrucks = new ActorIndex.OwnerAndNames(world, Info.SupplyTruckTypes, player);
		}

		protected override void Created(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;

			requestUnitProduction = self.TraitsImplementing<IBotRequestUnitProduction>().ToArray();
			playerResources = self.Trait<PlayerResources>();
			riskModelService = self.TraitsImplementing<IFransRiskModelService>().FirstOrDefault()
				?? throw new System.InvalidOperationException("FransSupplyTruckBotModule requires FransRiskModelBotModule.");
			combatIntelService = self.TraitsImplementing<IFransCombatIntelService>().FirstOrDefault()
				?? throw new System.InvalidOperationException("FransSupplyTruckBotModule requires FransCombatIntelBotModule.");
		}

		protected override void TraitEnabled(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;

			// Stagger evaluations so that several bots do not all scan on the same tick.
			scanTicks = world.LocalRandom.Next(0, Info.ScanInterval);
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransSupplyTruck.BotTick");
			if (player.WinState != WinState.Undefined)
				return;

			if (productionRequestCooldownTicks > 0)
				productionRequestCooldownTicks--;

			if (--scanTicks > 0)
				return;

			scanTicks = Info.ScanInterval;

			if (Info.SupplyTruckTypes.Count == 0)
				return;

			QueueDeliveryOrders(bot);
			RequestSupplyTruckProduction(bot);
		}

		void QueueDeliveryOrders(IBot bot)
		{
			var idleSupplyTrucks = supplyTrucks.Actors
				.Where(a => a.IsInWorld && !a.IsDead && a.IsIdle)
				.ToArray();

			foreach (var truck in idleSupplyTrucks)
			{
				var target = SelectDeliveryTarget(truck);
				if (target == null)
					continue;

				var recipientResources = target.Owner.PlayerActor.TraitOrDefault<PlayerResources>();
				var recipientFunds = recipientResources?.GetCashAndResources() ?? -1;
				var recipientEconomy = target.Owner.PlayerActor.TraitsImplementing<IFransEconomicSaturationService>().FirstOrDefault();
				AIUtils.BotDebug("{0} is sending {1} to deliver supplies to {2} owned by {3} with {4} total funds; explicit Struggling request {5}.",
					player, truck, target, target.Owner, recipientFunds, recipientEconomy?.RequestsSupplyCash ?? false);
				bot.QueueOrder(new Order("DeliverCash", truck, Target.FromActor(target), false));
			}
		}

		void RequestSupplyTruckProduction(IBot bot)
		{
			if (playerResources.GetCashAndResources() < Info.MinimumCashForProduction)
				return;

			var unitBuilder = requestUnitProduction.FirstEnabledTraitOrDefault();
			if (unitBuilder == null)
				return;

			var ownedCount = supplyTrucks.Actors.Count(a => a.IsInWorld && !a.IsDead);
			var queuedCount = CountQueuedSupplyTrucks();
			var requestedCount = Info.SupplyTruckTypes.Sum(type => unitBuilder.RequestedProductionCount(bot, type));
			if (ownedCount + queuedCount > 0)
				awaitingProductionConfirmation = false;

			// UnitBuilderBotModule consumes an external request even when its production queue is busy.
			// Retry an unconfirmed request instead of waiting for the normal delivery cooldown.
			var retryUnconfirmedRequest = awaitingProductionConfirmation && requestedCount == 0 &&
				ownedCount + queuedCount == 0;
			if (ownedCount + queuedCount + requestedCount >= Info.MaximumSupplyTrucks)
				return;

			if (productionRequestCooldownTicks > 0 && !retryUnconfirmedRequest)
				return;

			var validTypes = Info.SupplyTruckTypes
				.Where(type => world.Map.Rules.Actors.ContainsKey(type) &&
					FransActorClass.AnyOwnedQueueCanBuild(player, type) && GetValidDeliveryTargets().Any())
				.ToArray();

			if (validTypes.Length == 0)
				return;

			var supplyTruckType = validTypes.Random(world.LocalRandom);
			unitBuilder.RequestUnitProduction(bot, supplyTruckType);
			awaitingProductionConfirmation = true;
			if (!retryUnconfirmedRequest)
				productionRequestCooldownTicks = Info.ProductionRequestCooldown;

			AIUtils.BotDebug("{0} requested {1} for an allied supply delivery.", player, supplyTruckType);
		}

		int CountQueuedSupplyTrucks()
		{
			combatIntelService.EnsureCurrentSnapshot();
			return combatIntelService.OwnedActors
				.Where(a => a.IsInWorld && !a.IsDead)
				.SelectMany(a => a.TraitsImplementing<ProductionQueue>())
				.Where(q => q.Enabled)
				.Sum(q => q.AllQueued().Count(item => Info.SupplyTruckTypes.Contains(item.Item)));
		}

		Actor SelectDeliveryTarget(Actor truck)
		{
			var validTargets = GetValidDeliveryTargets()
				.Where(target => CanDeliverCashTo(truck, target))
				.Select(target => new
				{
					Target = target,
					DestinationRisk = riskModelService.EvaluateCell(truck, target.Location, FransRiskRole.SupportVehicle, Info.DeliveryRiskTolerance),
					RouteRisk = riskModelService.EvaluateDirectRoute(truck, truck.Location, target.Location, FransRiskRole.SupportVehicle, Info.DeliveryRiskTolerance)
				})
				.Where(x => !x.DestinationRisk.IsCritical && !x.RouteRisk.IsCritical)
				.ToArray();
			if (validTargets.Length == 0)
				return null;

			if (!Info.PrioritizeLowestFunds)
			{
				var preferred = validTargets
					.OrderBy(x => x.RouteRisk.PeakScore)
					.ThenBy(x => x.DestinationRisk.Score)
					.ThenBy(x => (x.Target.Location - truck.Location).LengthSquared)
					.Select(x => x.Target)
					.ToArray();
				return preferred.ClosestToWithPathFrom(truck);
			}

			var recipients = validTargets
				.GroupBy(x => x.Target.Owner)
				.Select(group => new
				{
					Owner = group.Key,
					Resources = group.Key.PlayerActor.TraitOrDefault<PlayerResources>(),
					RequestsSupplyCash = group.Key.PlayerActor.TraitsImplementing<IFransEconomicSaturationService>().FirstOrDefault()?.RequestsSupplyCash ?? false,
					Targets = group
						.OrderBy(x => x.RouteRisk.PeakScore)
						.ThenBy(x => x.DestinationRisk.Score)
						.ThenBy(x => (x.Target.Location - truck.Location).LengthSquared)
						.Select(x => x.Target)
						.ToArray()
				})
				.OrderByDescending(group => group.RequestsSupplyCash)
				.ThenBy(group => group.Resources?.GetCashAndResources() ?? int.MaxValue)
				.ThenBy(group => group.Owner.PlayerActor.ActorID);

			foreach (var recipient in recipients)
			{
				var target = recipient.Targets.ClosestToWithPathFrom(truck);
				if (target != null)
					return target;
			}

			return null;
		}

		static bool CanDeliverCashTo(Actor truck, Actor target)
		{
			var orderTarget = Target.FromActor(target);
			foreach (var issueOrder in truck.TraitsImplementing<IIssueOrder>())
			{
				foreach (var orderTargeter in issueOrder.Orders)
				{
					if (orderTargeter.OrderID != "DeliverCash")
						continue;

					var modifiers = TargetModifiers.None;
					string cursor = null;
					if (orderTargeter.CanTarget(truck, orderTarget, ref modifiers, ref cursor))
						return true;
				}
			}

			return false;
		}

		IEnumerable<Actor> GetValidDeliveryTargets()
		{
			foreach (var targetAndTrait in world.ActorsWithTrait<AcceptsDeliveredCash>())
			{
				var target = targetAndTrait.Actor;
				if (!target.IsInWorld || target.IsDead || target.Owner == player ||
					!PlayerRelationship.Ally.HasRelationship(player.RelationshipWith(target.Owner)))
					continue;

				if (Info.CheckTargetVisibility && !target.CanBeViewedByPlayer(player))
					continue;

				if (Info.DeliveryTargetTypes.Count > 0 && !Info.DeliveryTargetTypes.Contains(target.Info.Name))
					continue;

				var acceptsCashInfo = target.Info.TraitInfoOrDefault<AcceptsDeliveredCashInfo>();
				if (acceptsCashInfo == null ||
					!acceptsCashInfo.ValidRelationships.HasRelationship(target.Owner.RelationshipWith(player)))
					continue;

				yield return target;
			}
		}

		List<MiniYamlNode> IGameSaveTraitData.IssueTraitData(Actor self)
		{
			if (IsTraitDisabled)
				return null;

			return
			[
				new("ScanTicks", FieldSaver.FormatValue(scanTicks)),
				new("ProductionRequestCooldownTicks", FieldSaver.FormatValue(productionRequestCooldownTicks)),
				new("AwaitingProductionConfirmation", FieldSaver.FormatValue(awaitingProductionConfirmation))
			];
		}

		void IGameSaveTraitData.ResolveTraitData(Actor self, MiniYaml data)
		{
			if (self.World.IsReplay)
				return;

			var scanTicksNode = data.NodeWithKeyOrDefault("ScanTicks");
			if (scanTicksNode != null)
				scanTicks = FieldLoader.GetValue<int>("ScanTicks", scanTicksNode.Value.Value);

			var cooldownNode = data.NodeWithKeyOrDefault("ProductionRequestCooldownTicks");
			if (cooldownNode != null)
				productionRequestCooldownTicks = FieldLoader.GetValue<int>(
					"ProductionRequestCooldownTicks", cooldownNode.Value.Value);

			var awaitingProductionNode = data.NodeWithKeyOrDefault("AwaitingProductionConfirmation");
			if (awaitingProductionNode != null)
				awaitingProductionConfirmation = FieldLoader.GetValue<bool>(
					"AwaitingProductionConfirmation", awaitingProductionNode.Value.Value);
		}

		void INotifyActorDisposing.Disposing(Actor self)
		{
			supplyTrucks?.Dispose();
		}
	}
}
