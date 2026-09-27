#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * Fransbot adaptation based on OpenRA's SupportPowerBotModule.
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System;
using System.Collections.Frozen;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Linq;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{

	public interface IFransSupportPowerService
	{
		bool IsPowerReady(string orderName);
		bool TryFindFairIntelNukeTarget(out CPos target, out int score);
		bool TryFindFairIntelNukeTarget(CPos missionCenter, int missionRadius, out CPos target, out int score);
		bool TryFindSafeMissionDeliveryCell(string orderName, CPos missionCenter, int searchRadius, out CPos target);
		bool TryFirePower(IBot bot, string orderName, CPos target);
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Fransbot support-power manager. Uses deterministic stock-style support-power targeting, shared FransRiskModel tie-breaking, and fair FransCombatIntel targeting for nuclear strikes.")]
	public class FransSupportPowerBotModuleInfo : ConditionalTraitInfo, Requires<SupportPowerManagerInfo>
	{
		[Desc("Tells Fransbot how to use its support powers. Uses the stock SupportPowerDecision format so existing RA decision YAML remains compatible.")]
		[FieldLoader.LoadUsing(nameof(LoadDecisions))]
		public readonly ImmutableArray<SupportPowerDecision> Decisions = [];

		[Desc("Orders that place friendly troops and must reject critical ground-risk cells.")]
		public readonly FrozenSet<string> RiskAvoidingPowerOrders = new[] { "SovietParatroopers" }.ToFrozenSet();

		[Desc("Offensive strike orders that prefer higher unified-risk cells when attractiveness ties, concentrating fire on defended/contested locations.")]
		public readonly FrozenSet<string> RiskSeekingPowerOrders = new[] { "UkraineParabombs", "NukePowerInfoOrder" }.ToFrozenSet();

		[Desc("Reconnaissance power orders that prefer higher-information-risk cells when attractiveness ties.")]
		public readonly FrozenSet<string> RiskReconPowerOrders = new[] { "SovietSpyPlane" }.ToFrozenSet();

		[Desc("Support-power orders owned by FransSupportCoordinator. The low-level support module exposes readiness/targeting/firing services for these but never launches them autonomously.")]
		public readonly FrozenSet<string> CoordinatorOwnedPowerOrders = new[] { "NukePowerInfoOrder", "SovietParatroopers" }.ToFrozenSet();

		[Desc("Terrain types rejected for mission-aware troop-delivery support powers.")]
		public readonly FrozenSet<string> DeliveryRejectedTerrainTypes = new[] { "Water" }.ToFrozenSet();

		[Desc("Risk tolerance for troop-delivery support powers.")]
		public readonly FransRiskTolerance DeliveryRiskTolerance = FransRiskTolerance.Aggressive;

		[Desc("Support-power order that must use fair persistent FransCombatIntel instead of scanning hidden world actors.")]
		public readonly string FairIntelNukeOrder = "NukePowerInfoOrder";

		[Desc("Cells around each known enemy structure tested as possible nuke centers. This is a bounded local search, never a full-map actor scan.")]
		public readonly int NukeIntelCandidateSpreadRadius = 2;

		[Desc("Radius in cells for the normal known-enemy-structure nuke value term.")]
		public readonly int NukeIntelStructureRadius = 1;

		[Desc("Normal known enemy structure value percentage used by fair-intel nuke targeting. Matches the existing YAML nuke consideration of 50.")]
		public readonly int NukeIntelStructureValuePercent = 50;

		[ActorReference]
		[Desc("Known enemy structures receiving the existing extra nuke priority term.")]
		public readonly FrozenSet<string> NukeIntelPriorityStructureTypes = FrozenSet<string>.Empty;

		[Desc("Radius in cells for the extra strategic-structure nuke priority term.")]
		public readonly int NukeIntelPriorityRadius = 2;

		[Desc("Extra known strategic-structure value percentage. Matches the existing YAML MSLO nuke consideration of 100.")]
		public readonly int NukeIntelPriorityValuePercent = 100;

		[Desc("Radius in cells in which visible own/allied mobile value penalizes a nuke target.")]
		public readonly int NukeIntelFriendlyPenaltyRadius = 7;

		[Desc("Visible own/allied mobile value penalty percentage. Matches the existing YAML ally nuke consideration magnitude of 10.")]
		public readonly int NukeIntelFriendlyValuePercent = 10;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			if (string.IsNullOrWhiteSpace(FairIntelNukeOrder) ||
				NukeIntelCandidateSpreadRadius < 0 || NukeIntelStructureRadius < 0 || NukeIntelStructureValuePercent < 0 ||
				NukeIntelPriorityRadius < 0 || NukeIntelPriorityValuePercent < 0 ||
				NukeIntelFriendlyPenaltyRadius < 0 || NukeIntelFriendlyValuePercent < 0)
				throw new YamlException("FransSupportPower fair-intel nuke settings are invalid.");
		}

		static object LoadDecisions(MiniYaml yaml)
		{
			var ret = new List<SupportPowerDecision>();
			var decisions = yaml.NodeWithKeyOrDefault("Decisions");
			if (decisions != null)
				foreach (var d in decisions.Value.Nodes)
					ret.Add(new SupportPowerDecision(d.Value));

			return ret.ToImmutableArray();
		}

		public override object Create(ActorInitializer init) { return new FransSupportPowerBotModule(init.Self, this); }
	}

	public class FransSupportPowerBotModule : ConditionalTrait<FransSupportPowerBotModuleInfo>, IBotTick, IGameSaveTraitData, IFransSupportPowerService
	{
		readonly World world;
		readonly Player player;
		readonly Dictionary<SupportPowerInstance, int> waitingPowers = [];
		readonly Dictionary<string, SupportPowerDecision> powerDecisions = [];
		readonly List<SupportPowerInstance> stalePowers = [];
		SupportPowerManager supportPowerManager;
		IFransRiskModelService riskModelService;
		IFransCombatIntelService combatIntelService;

		public FransSupportPowerBotModule(Actor self, FransSupportPowerBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		protected override void Created(Actor self)
		{
			supportPowerManager = self.Owner.PlayerActor.Trait<SupportPowerManager>();
			riskModelService = self.Owner.PlayerActor.TraitsImplementing<IFransRiskModelService>().FirstOrDefault()
				?? throw new System.InvalidOperationException("FransSupportPowerBotModule requires FransRiskModelBotModule.");
			combatIntelService = self.Owner.PlayerActor.TraitsImplementing<IFransCombatIntelService>().FirstOrDefault()
				?? throw new System.InvalidOperationException("FransSupportPowerBotModule requires FransCombatIntelBotModule.");
		}

		protected override void TraitEnabled(Actor self)
		{
			powerDecisions.Clear();
			foreach (var decision in Info.Decisions)
				powerDecisions[decision.OrderName] = decision;

			FransBotLog.BotDebug(world, "{0}: FransSupportPower FAIR-INTEL NUKE FALLBACK enabled with {1} decision(s); coordinator-owned powers are exposed as readiness/targeting/fire services and are never launched autonomously. FAIR-INTEL NUKE still uses only visible/persistently remembered enemy structures.", player.ResolvedPlayerName, powerDecisions.Count);
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransSupportPower.BotTick");
			if (player.WinState != WinState.Undefined)
				return;

			foreach (var sp in supportPowerManager.Powers.Values)
			{
				if (sp.Disabled)
					continue;

				waitingPowers.TryAdd(sp, 0);
				if (waitingPowers[sp] > 0)
					waitingPowers[sp]--;

				if (Info.CoordinatorOwnedPowerOrders.Contains(sp.Info.OrderName))
					continue;

				var isDelayed = waitingPowers[sp] > 0;
				if (!sp.Ready || isDelayed || !powerDecisions.TryGetValue(sp.Info.OrderName, out var powerDecision))
					continue;

				if (powerDecision == null)
				{
					FransBotLog.BotDebug(world, "{0}: FransSupportPower cannot find decision for {1}.", player.ResolvedPlayerName, sp.Info.OrderName);
					continue;
				}

				CPos? attackLocation;
				if (sp.Info.OrderName == Info.FairIntelNukeOrder)
				{
					attackLocation = FindFairIntelNukeAttackLocation(powerDecision, out var nukeScore, out var knownStructures, out var rememberedStructures);
					if (attackLocation == null)
					{
						FransBotLog.BotDebug(world, "{0}: FransSupportPower FAIR-INTEL NUKE found no known enemy-structure cluster above attractiveness {1}; {2} known structure contact(s), {3} remembered-only. Delaying rescan.",
							player.ResolvedPlayerName, powerDecision.MinimumAttractiveness, knownStructures, rememberedStructures);
						waitingPowers[sp] += powerDecision.GetNextScanTime(world);
						continue;
					}

					FransBotLog.BotDebug(world, "{0}: FransSupportPower FAIR-INTEL NUKE selected {1}, score {2}, from {3} known enemy structure contact(s) ({4} remembered-only).",
						player.ResolvedPlayerName, attackLocation.Value, nukeScore, knownStructures, rememberedStructures);
				}
				else
				{
					attackLocation = FindDeterministicCoarseAttackLocation(sp);
					if (attackLocation == null)
					{
						FransBotLog.BotDebug(world, "{0}: FransSupportPower found no coarse target for {1}; delaying rescan.", player.ResolvedPlayerName, sp.Info.OrderName);
						waitingPowers[sp] += powerDecision.GetNextScanTime(world);
						continue;
					}

					attackLocation = FindFineAttackLocation(sp, attackLocation.Value);
					if (attackLocation == null)
					{
						FransBotLog.BotDebug(world, "{0}: FransSupportPower found no final target for {1}; delaying rescan.", player.ResolvedPlayerName, sp.Info.OrderName);
						waitingPowers[sp] += powerDecision.GetNextScanTime(world);
						continue;
					}

					FransBotLog.BotDebug(world, "{0}: FransSupportPower selected deterministic target {1} for {2}.", player.ResolvedPlayerName, attackLocation.Value, sp.Info.OrderName);
				}
				waitingPowers[sp] += 10;
				bot.QueueOrder(
					new Order(sp.Key, supportPowerManager.Self, Target.FromCell(world, attackLocation.Value), false)
					{ SuppressVisualFeedback = true, ExtraData = uint.MaxValue });
			}

			stalePowers.AddRange(waitingPowers.Keys.Where(wp => !supportPowerManager.Powers.ContainsKey(wp.Key)));
			foreach (var p in stalePowers)
				waitingPowers.Remove(p);

			stalePowers.Clear();
		}


		bool IFransSupportPowerService.IsPowerReady(string orderName)
		{
			if (string.IsNullOrWhiteSpace(orderName))
				return false;

			return supportPowerManager.Powers.Values.Any(sp => !sp.Disabled && sp.Ready &&
				sp.Info.OrderName == orderName && (!waitingPowers.TryGetValue(sp, out var wait) || wait <= 0));
		}

		bool IFransSupportPowerService.TryFindFairIntelNukeTarget(out CPos target, out int score)
		{
			target = default;
			score = int.MinValue;
			if (!powerDecisions.TryGetValue(Info.FairIntelNukeOrder, out var decision) || decision == null)
				return false;

			var found = FindFairIntelNukeAttackLocation(decision, out score, out _, out _);
			if (!found.HasValue)
				return false;

			target = found.Value;
			return true;
		}

		bool IFransSupportPowerService.TryFindFairIntelNukeTarget(CPos missionCenter, int missionRadius, out CPos target, out int score)
		{
			target = default;
			score = int.MinValue;
			if (!powerDecisions.TryGetValue(Info.FairIntelNukeOrder, out var decision) || decision == null ||
				missionRadius <= 0 || !world.Map.Contains(missionCenter))
				return false;

			var found = FindFairIntelNukeAttackLocation(decision, out score, out _, out _, missionCenter, missionRadius);
			if (!found.HasValue)
				return false;

			target = found.Value;
			return true;
		}

		bool IFransSupportPowerService.TryFindSafeMissionDeliveryCell(string orderName, CPos missionCenter, int searchRadius, out CPos target)
		{
			target = default;
			if (string.IsNullOrWhiteSpace(orderName) || searchRadius < 0 || !world.Map.Contains(missionCenter))
				return false;

			CPos? best = null;
			var bestRisk = int.MaxValue;
			var bestDistance = int.MaxValue;
			for (var dy = -searchRadius; dy <= searchRadius; dy++)
				for (var dx = -searchRadius; dx <= searchRadius; dx++)
				{
					var candidate = new CPos(missionCenter.X + dx, missionCenter.Y + dy);
					if (!world.Map.Contains(candidate) || Info.DeliveryRejectedTerrainTypes.Contains(world.Map.GetTerrainInfo(candidate).Type))
						continue;

					var risk = riskModelService.EvaluateStrategicCell(candidate, FransRiskRole.GroundCombat, Info.DeliveryRiskTolerance);
					if (risk.IsCritical)
						continue;

					var distance = Math.Abs(dx) + Math.Abs(dy);
					if (best == null || risk.Score < bestRisk ||
						(risk.Score == bestRisk && (distance < bestDistance ||
							(distance == bestDistance && IsEarlier(candidate, best.Value)))))
					{
						best = candidate;
						bestRisk = risk.Score;
						bestDistance = distance;
					}
				}

			if (!best.HasValue)
				return false;

			target = best.Value;
			return true;
		}

		bool IFransSupportPowerService.TryFirePower(IBot bot, string orderName, CPos target)
		{
			if (bot == null || string.IsNullOrWhiteSpace(orderName) || !world.Map.Contains(target))
				return false;

			var power = supportPowerManager.Powers.Values
				.Where(sp => !sp.Disabled && sp.Ready && sp.Info.OrderName == orderName)
				.FirstOrDefault(sp => !waitingPowers.TryGetValue(sp, out var wait) || wait <= 0);
			if (power == null)
				return false;

			waitingPowers.TryAdd(power, 0);
			waitingPowers[power] = 10;
			bot.QueueOrder(new Order(power.Key, supportPowerManager.Self, Target.FromCell(world, target), false)
			{ SuppressVisualFeedback = true, ExtraData = uint.MaxValue });
			return true;
		}


		/// <summary>
		/// Nuclear targeting is deliberately sensor-owned: candidates come only from visible or
		/// legitimately remembered enemy STRUCTURES in FransCombatIntel. Persistent structure
		/// memory may therefore launch at an old last-seen base if the bot has not re-scouted it;
		/// this is intentional fair-information behavior. No hidden live Actor is queried.
		/// </summary>
		CPos? FindFairIntelNukeAttackLocation(SupportPowerDecision powerDecision, out int bestScore,
			out int knownStructures, out int rememberedStructures, CPos? missionCenter = null, int missionRadius = 0)
		{
			bestScore = int.MinValue;
			knownStructures = 0;
			rememberedStructures = 0;
			combatIntelService.EnsureCurrentSnapshot();

			var contacts = combatIntelService.EnemyCombatContacts
				.Where(c => c.IsBuilding && c.EstimatedValue > 0 && c.Owner != null &&
					PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(c.Owner)))
				.OrderBy(c => c.ActorId)
				.ToArray();
			knownStructures = contacts.Length;
			rememberedStructures = contacts.Count(c => !c.IsVisible);
			if (contacts.Length == 0)
				return null;

			// Only scan a small deterministic neighborhood around real intel contacts. This is both
			// fairer and much cheaper than the stock full-map ActorMap support-power scan.
			var candidates = new HashSet<CPos>();
			foreach (var contact in contacts)
				for (var dx = -Info.NukeIntelCandidateSpreadRadius; dx <= Info.NukeIntelCandidateSpreadRadius; dx++)
					for (var dy = -Info.NukeIntelCandidateSpreadRadius; dy <= Info.NukeIntelCandidateSpreadRadius; dy++)
					{
						var candidate = new CPos(contact.LastSeenCell.X + dx, contact.LastSeenCell.Y + dy);
						if (world.Map.Contains(candidate))
							candidates.Add(candidate);
					}

			CPos? bestLocation = null;
			var bestRiskScore = int.MinValue;
			var missionRadiusSquared = missionCenter.HasValue && missionRadius > 0 ? missionRadius * missionRadius : int.MaxValue;
			foreach (var candidate in candidates.OrderBy(c => c.Y).ThenBy(c => c.X))
			{
				if (missionCenter.HasValue && (candidate - missionCenter.Value).LengthSquared > missionRadiusSquared)
					continue;

				var score = ScoreFairIntelNukeCell(candidate, contacts);
				if (score < powerDecision.MinimumAttractiveness || (bestLocation.HasValue && score < bestScore))
					continue;

				// Risk is only a tie-breaker. Avoid paying for a RiskModel query on candidates
				// whose fair-intel value already cannot beat the current best.
				var risk = riskModelService.EvaluateStrategicCell(candidate,
					FransRiskRole.AuxiliaryCombat, FransRiskTolerance.Assault);
				if (bestLocation == null || score > bestScore ||
					(score == bestScore && (risk.Score > bestRiskScore ||
						(risk.Score == bestRiskScore && IsEarlier(candidate, bestLocation.Value)))))
				{
					bestScore = score;
					bestRiskScore = risk.Score;
					bestLocation = candidate;
				}
			}

			return bestLocation;
		}

		int ScoreFairIntelNukeCell(CPos candidate, IReadOnlyList<FransCombatIntelContact> contacts)
		{
			var score = 0;
			var normalRadiusSquared = Info.NukeIntelStructureRadius * Info.NukeIntelStructureRadius;
			var priorityRadiusSquared = Info.NukeIntelPriorityRadius * Info.NukeIntelPriorityRadius;
			foreach (var contact in contacts)
			{
				var distanceSquared = (contact.LastSeenCell - candidate).LengthSquared;
				var value = KnownActorPurchaseValue(contact.ActorType, contact.FullValue);
				if (distanceSquared <= normalRadiusSquared)
					score += value * Info.NukeIntelStructureValuePercent / 100;
				if (Info.NukeIntelPriorityStructureTypes.Contains(contact.ActorType) && distanceSquared <= priorityRadiusSquared)
					score += value * Info.NukeIntelPriorityValuePercent / 100;
			}

			// Friendly-fire penalty uses only owned or currently visible allied mobile actors.
			// Hidden enemy or allied world state is never consulted.
			var friendlyRadiusSquared = Info.NukeIntelFriendlyPenaltyRadius * Info.NukeIntelFriendlyPenaltyRadius;
			foreach (var actor in combatIntelService.VisibleActors)
			{
				// VisibleActors also contains non-spatial system/player actors. Actor.Location dereferences
				// OccupiesSpace, so only score physical map actors here. This also protects against
				// transient actors whose spatial trait is unavailable during a live snapshot.
				if (actor == null || actor.IsDead || !actor.IsInWorld || actor.OccupiesSpace == null ||
					actor.Info.HasTraitInfo<BuildingInfo>() || actor.Owner == null)
					continue;
				if (actor.Owner != player && !PlayerRelationship.Ally.HasRelationship(player.RelationshipWith(actor.Owner)))
					continue;
				if ((actor.Location - candidate).LengthSquared > friendlyRadiusSquared)
					continue;

				var value = Math.Max(1, actor.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 1);
				score -= value * Info.NukeIntelFriendlyValuePercent / 100;
			}

			return score;
		}

		int KnownActorPurchaseValue(string actorType, int fallback)
		{
			if (!string.IsNullOrWhiteSpace(actorType) && world.Map.Rules.Actors.TryGetValue(actorType, out var actorInfo))
				return Math.Max(1, actorInfo.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? fallback);
			return Math.Max(1, fallback);
		}

		/// <summary>
		/// Stock SupportPowerBotModule chooses a random above-average coarse region.
		/// Fransbot instead chooses the region with the highest measured attractiveness.
		/// Ties are resolved by map coordinates, making identical game states produce identical choices.
		/// </summary>
		CPos? FindDeterministicCoarseAttackLocation(SupportPowerInstance readyPower)
		{
			var powerDecision = powerDecisions[readyPower.Info.OrderName];
			if (powerDecision == null)
				return null;

			var map = world.Map;
			var checkRadius = powerDecision.CoarseScanRadius;
			MPos? bestLocation = null;
			var bestAttractiveness = int.MinValue;

			for (var i = 0; i < map.MapSize.Width; i += checkRadius)
			{
				for (var j = 0; j < map.MapSize.Height; j += checkRadius)
				{
					var tl = new MPos(i, j);
					var br = new MPos(i + checkRadius, j + checkRadius);
					var region = new CellRegion(map.Grid.Type, tl, br);
					var wtl = world.Map.CenterOfCell(tl.ToCPos(map));
					var wbr = world.Map.CenterOfCell(br.ToCPos(map));
					var targets = world.ActorMap.ActorsInBox(wtl, wbr);
					var frozenTargets = player.FrozenActorLayer != null ? player.FrozenActorLayer.FrozenActorsInRegion(region) : [];
					var attractiveness = powerDecision.GetAttractiveness(targets, player) + powerDecision.GetAttractiveness(frozenTargets, player);

					if (attractiveness < powerDecision.MinimumAttractiveness)
						continue;

					if (bestLocation == null || attractiveness > bestAttractiveness ||
						(attractiveness == bestAttractiveness && IsEarlier(tl, bestLocation.Value)))
					{
						bestAttractiveness = attractiveness;
						bestLocation = tl;
					}
				}
			}

			return bestLocation?.ToCPos(map);
		}

		static bool IsEarlier(MPos candidate, MPos current)
		{
			return candidate.V < current.V || (candidate.V == current.V && candidate.U < current.U);
		}

		/// <summary>Detail scans the selected coarse region and deterministically picks its strongest cell.</summary>
		CPos? FindFineAttackLocation(SupportPowerInstance readyPower, CPos checkPos, int extendedRange = 1)
		{
			CPos? bestLocation = null;
			var bestAttractiveness = int.MinValue;
			var bestRiskScore = 0;
			var powerDecision = powerDecisions[readyPower.Info.OrderName];
			if (powerDecision == null)
				return null;

			var orderName = readyPower.Info.OrderName;
			var avoidRisk = Info.RiskAvoidingPowerOrders.Contains(orderName);
			var seekRisk = Info.RiskSeekingPowerOrders.Contains(orderName) || Info.RiskReconPowerOrders.Contains(orderName);
			var checkRadius = powerDecision.CoarseScanRadius;
			var fineCheck = powerDecision.FineScanRadius;
			for (var i = -extendedRange; i <= checkRadius + extendedRange; i += fineCheck)
			{
				var x = checkPos.X + i;
				for (var j = -extendedRange; j <= checkRadius + extendedRange; j += fineCheck)
				{
					var y = checkPos.Y + j;
					var candidate = new CPos(x, y);
					if (!world.Map.Contains(candidate))
						continue;

					var pos = world.Map.CenterOfCell(candidate);
					var attractiveness = powerDecision.GetAttractiveness(pos, player);
					if (attractiveness < powerDecision.MinimumAttractiveness)
						continue;

					var risk = riskModelService.EvaluateStrategicCell(candidate,
						avoidRisk ? FransRiskRole.GroundCombat : FransRiskRole.AuxiliaryCombat,
						avoidRisk ? Info.DeliveryRiskTolerance : FransRiskTolerance.Assault);
					if (avoidRisk && risk.IsCritical)
						continue;

					var betterTie = bestLocation.HasValue && (avoidRisk
						? risk.Score < bestRiskScore ||
							(risk.Score == bestRiskScore && IsEarlier(candidate, bestLocation.Value))
						: seekRisk
							? risk.Score > bestRiskScore ||
								(risk.Score == bestRiskScore && IsEarlier(candidate, bestLocation.Value))
							: IsEarlier(candidate, bestLocation.Value));
					if (bestLocation == null || attractiveness > bestAttractiveness ||
						(attractiveness == bestAttractiveness && betterTie))
					{
						bestAttractiveness = attractiveness;
						bestRiskScore = risk.Score;
						bestLocation = candidate;
					}
				}
			}

			return bestLocation;
		}

		static bool IsEarlier(CPos candidate, CPos current)
		{
			return candidate.Y < current.Y || (candidate.Y == current.Y && candidate.X < current.X);
		}

		List<MiniYamlNode> IGameSaveTraitData.IssueTraitData(Actor self)
		{
			if (IsTraitDisabled)
				return null;

			var waitingPowersNodes = waitingPowers
				.Select(kv => new MiniYamlNode(kv.Key.Key, FieldSaver.FormatValue(kv.Value)))
				.ToList();

			return
			[
				new("WaitingPowers", "", waitingPowersNodes)
			];
		}

		void IGameSaveTraitData.ResolveTraitData(Actor self, MiniYaml data)
		{
			if (self.World.IsReplay)
				return;

			var waitingPowersNode = data.NodeWithKeyOrDefault("WaitingPowers");
			if (waitingPowersNode == null)
				return;

			foreach (var n in waitingPowersNode.Value.Nodes)
				if (supportPowerManager.Powers.TryGetValue(n.Key, out var instance))
					waitingPowers[instance] = FieldLoader.GetValue<int>("WaitingPowers", n.Value.Value);
		}
	}
}
