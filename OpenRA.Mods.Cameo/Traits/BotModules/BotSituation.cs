#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	public enum BotUrgency { Normal, Pressured, Emergency }

	public sealed class EnemyProfile
	{
		public OpenRA.Player Player;
		public string Name;
		public string FactionName;
		public bool Alive;
		public int ArmyValue;
		public int InfantryValue, VehicleValue, AirValue, NavalValue;
		public int DefenceCount, DefenceValue;
		public int TechBuildings;
		public int ProductionBuildings;
		public int BuildingCount;
		public int ExpansionClusters;
		public int Harvesters, Refineries;
		public int PressureValue;
		public int StealthShare;
		public int NearestCells;
		public int LastSeenTick;
		public int Score;
	}

	public sealed class CounterDemand
	{
		public int AntiAir, AntiArmour, AntiInfantry, Detector, Artillery;
	}

	public sealed class BotSituation
	{
		public int Tick;
		public OpenRA.Player MainTarget;
		public string Personality = "";
		public BotUrgency Urgency;
		public IReadOnlyDictionary<OpenRA.Player, EnemyProfile> Enemies;
		public CounterDemand Demand;
		public int DefenceFractionHint, ExpansionAppetiteHint;
		internal int OwnArmyValue, OwnDefenceValue, OwnBuildings, OwnHarvesters;
		internal int OwnKillsCostWindow, OwnDeathsCostWindow;
		internal string OwnPersonality = "";
	}

	internal sealed class MasterAiBotSavedState
	{
		public bool CostCountersInitialized;
		public int PreviousDeathsCost;
		public int PreviousKillsCost;
		public BotUrgency CurrentUrgency;
		public int LastPersonalitySwitchTick;
		public bool EmergencyPersonalityHandled;
		public (int Tick, int Delta)[] LossSamples = Array.Empty<(int, int)>();
		public (int Tick, int Delta)[] KillSamples = Array.Empty<(int, int)>();
		public int[] ProductionLossTicks = Array.Empty<int>();
		public uint[] ProductionBuildings = Array.Empty<uint>();
	}

	public class MasterAiBotModuleInfo : ConditionalTraitInfo
	{
		public readonly BitSet<TargetableType> InfantryTargetTypes = new("Infantry");
		public readonly BitSet<TargetableType> VehicleTargetTypes = new("Vehicle");
		public readonly BitSet<TargetableType> NavalTargetTypes = new("Water", "Ship");
		public readonly BitSet<TargetableType> DefenceTargetTypes = new("Defense");

		public readonly int ClusterRadius = 12;
		public readonly int PressureRadius = 15;
		public readonly int LossWindowTicks = 750;
		public readonly int EmergencyLossThreshold = 600;
		public readonly int PressuredArmyRatio = 60;
		public readonly int EmergencyCheckInterval = 25;
		public readonly int SnapshotInterval = 150;
		public readonly int DecisionInterval = 1500;
		public readonly int WeightReach = 250;
		public readonly int WeightWeak = 200;
		public readonly int WeightEcon = 150;
		public readonly int WeightKill = 100;
		public readonly int WeightDefence = 150;
		public readonly int WeightAlly = 100;
		public readonly int IncumbentMomentum = 75;
		public readonly int MinimumHoldTicks = 3000;
		public readonly int FortifiedDefenceCount = 6;
		public readonly int SteamrollerMinArmyValue = 3000;
		public readonly int GuerrillaMinClusters = 3;
		public readonly int TechEnemyTechBuildings = 4;
		public readonly int RushMaxEnemyArmyValue = 1500;
		public readonly int RushMaxEnemyDefenceCount = 2;
		public readonly int EliminationBuildingSaturation = 8;
		public readonly int PersonalityHoldTicks = 3000;

		public override object Create(ActorInitializer init) { return new MasterAiBotModule(init.Self, this); }
	}

	public class MasterAiBotModule : ConditionalTrait<MasterAiBotModuleInfo>, IBotTick, IGameSaveTraitData
	{
		static readonly string[] DefaultPersonalities = { "rush", "turtle", "tech", "expansion", "steamroller" };
		readonly OpenRA.Player player;
		readonly List<BotSituation> pendingSituations = [];
		readonly Queue<(int Tick, int Delta)> lossSamples = new();
		readonly Queue<(int Tick, int Delta)> killSamples = new();
		readonly Queue<int> productionLossTicks = new();
		readonly HashSet<uint> productionBuildings = [];
		int nextSnapshotTick;
		int nextEmergencyTick;
		int lastDecisionTick;
		OpenRA.Player incumbentTarget;
		string incumbentPersonality = "";
		int incumbentSince;
		int previousDeathsCost;
		int previousKillsCost;
		bool costCountersInitialized;
		BotUrgency currentUrgency;
		int lastPersonalitySwitchTick;
		bool emergencyPersonalityHandled;

		public BotSituation Situation { get; private set; }
		internal int DeathsCostWindow { get; private set; }
		internal int KillsCostWindow { get; private set; }
		internal IReadOnlyList<BotSituation> PendingSituations => pendingSituations;

		public MasterAiBotModule(Actor self, MasterAiBotModuleInfo info)
			: base(info)
		{
			player = self.Owner;
			costCountersInitialized = !player.World.IsLoadingGameSave;
			lastDecisionTick = -Math.Max(1, info.DecisionInterval);
			lastPersonalitySwitchTick = -Math.Max(1, info.PersonalityHoldTicks);
			nextSnapshotTick = Math.Abs(player.ClientIndex * 37) % Math.Max(1, info.SnapshotInterval);
			nextEmergencyTick = nextSnapshotTick;
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (IsTraitDisabled || bot.Player != player)
				return;

			var tick = player.World.WorldTick;
			if (tick >= nextEmergencyTick)
			{
				nextEmergencyTick = tick + Math.Max(1, Info.EmergencyCheckInterval);
				CheckEmergency(tick);
			}
			if (tick < nextSnapshotTick)
				return;

			nextSnapshotTick = tick + Math.Max(1, Info.SnapshotInterval);
			Rebuild(tick, bot);
		}

		void Rebuild(int tick, IBot bot)
		{
			var actors = player.World.Actors.Where(a => a.IsInWorld && !a.IsDead).ToArray();
			var actorsByOwner = actors.GroupBy(a => a.Owner).ToDictionary(g => g.Key, g => g.ToArray());
			var ownActors = actorsByOwner.TryGetValue(player, out var ownedActors) ? ownedActors : Array.Empty<Actor>();
			var ownBuildings = ownActors.Where(IsBuilding).ToArray();
			var ownArmy = ownActors.Where(IsCombatUnit).Sum(Value);
			var ownDefence = ownBuildings.Where(IsDefence).Sum(Value);
			var ownHarvesters = ownActors.Count(a => a.Info.HasTraitInfo<HarvesterInfo>());
			var profiles = new Dictionary<OpenRA.Player, EnemyProfile>();
			foreach (var enemy in player.World.Players.Where(IsEligible).Where(p => p != player && player.RelationshipWith(p) == PlayerRelationship.Enemy))
			{
				var enemyActors = actorsByOwner.TryGetValue(enemy, out var ownedEnemyActors) ? ownedEnemyActors : Array.Empty<Actor>();
				var profile = BuildProfile(enemy, enemyActors, ownBuildings, tick);
				profiles.Add(enemy, profile);
			}

			var enemyArmy = profiles.Values.Sum(p => p.ArmyValue);
			var urgency = currentUrgency == BotUrgency.Emergency
				? BotUrgency.Emergency
				: profiles.Values.Any(p => p.PressureValue > 0) ||
					(enemyArmy > 0 && (long)ownArmy * 100 < (long)enemyArmy * Info.PressuredArmyRatio)
					? BotUrgency.Pressured : BotUrgency.Normal;
			currentUrgency = urgency;
			if (urgency != BotUrgency.Emergency)
				emergencyPersonalityHandled = false;

			var econTotal = profiles.Values.Where(p => p.Alive).Sum(EconProxy);
			foreach (var profile in profiles.Values.Where(p => p.Alive))
				profile.Score = TargetScore(profile, ownArmy, AlliedCommitments(profile.Player), econTotal, Info);

			var targetProfile = profiles.Values.FirstOrDefault(p => p.Player == incumbentTarget);
			var decision = ShouldEvaluateTargetDecision(
				incumbentTarget != null, targetProfile != null,
				lastDecisionTick, tick, Info.DecisionInterval);
			OpenRA.Player target = incumbentTarget;
			if (decision)
			{
				var candidates = profiles.Values.Where(p => p.Alive && p.NearestCells >= 0).ToArray();
				var chosen = ChooseTarget(candidates, targetProfile, incumbentSince, tick, Info);
				target = chosen?.Player;
				targetProfile = chosen;
				if (target != incumbentTarget)
					incumbentSince = tick;
				incumbentTarget = target;
			}

			var currentPersonality = CurrentPersonality();
			var personalityCandidate = UnfilteredCandidatePersonality(urgency, targetProfile, ownArmy,
				profiles.Values, currentPersonality, Info);
			var personalityDecision = ShouldEvaluatePersonality(decision, urgency, emergencyPersonalityHandled);
			if (personalityDecision)
			{
				var availablePersonalities = AvailablePersonalities();
				var candidatePersonality = CandidatePersonality(urgency, targetProfile, ownArmy,
					profiles.Values, currentPersonality, availablePersonalities, Info);
				incumbentPersonality = candidatePersonality;

				var botLimits = player.PlayerActor.TraitsImplementing<BotLimits>().FirstEnabledTraitOrDefault();
				if (ShouldSwitchPersonality(currentPersonality, candidatePersonality, lastPersonalitySwitchTick, tick,
					urgency == BotUrgency.Emergency && !emergencyPersonalityHandled,
					botLimits?.Info.AllowPersonalitySwitching ?? false, Info))
				{
					bot.QueueOrder(new Order("SetBotPersonality", player.PlayerActor, false)
					{
						TargetString = candidatePersonality,
						SuppressVisualFeedback = true
					});
					lastPersonalitySwitchTick = tick;
				}

				if (urgency == BotUrgency.Emergency)
					emergencyPersonalityHandled = true;
			}

			if (decision)
				lastDecisionTick = tick;

			var demand = BuildDemand(profiles.Values, targetProfile, enemyArmy);
			var situation = new BotSituation
			{
				Tick = tick,
				MainTarget = target,
				Personality = personalityCandidate,
				Urgency = urgency,
				Enemies = profiles,
				Demand = demand,
				DefenceFractionHint = Clamp(urgency == BotUrgency.Emergency ? 80 : urgency == BotUrgency.Pressured ? 55 : 30),
				ExpansionAppetiteHint = Clamp(urgency == BotUrgency.Normal && ownArmy > 0 ? 60 : 20),
				OwnArmyValue = ownArmy,
				OwnDefenceValue = ownDefence,
				OwnBuildings = ownBuildings.Length,
				OwnHarvesters = ownHarvesters,
				OwnKillsCostWindow = KillsCostWindow,
				OwnDeathsCostWindow = DeathsCostWindow,
				OwnPersonality = CurrentPersonality()
			};
			Situation = situation;
			pendingSituations.Add(situation);
			if (pendingSituations.Count > 2000)
				pendingSituations.RemoveRange(1000, pendingSituations.Count - 2000);
		}

		string CurrentPersonality()
		{
			return player.PlayerActor.TraitOrDefault<BotPersonalityController>()?.CurrentPersonality
				?? player.PlayerActor.TraitOrDefault<AiMatchLogRecorder>()?.CurrentPersonality
				?? "";
		}

		IEnumerable<string> AvailablePersonalities()
		{
			var controller = player.PlayerActor.TraitOrDefault<BotPersonalityController>();
			return controller == null
				? DefaultPersonalities
				: controller.Info.Conditions.Select(c => BotPersonalityController.PersonalityName(c, controller.Info.PersonalityPrefix));
		}

		void CheckEmergency(int tick)
		{
			var stats = player.PlayerActor.TraitOrDefault<PlayerStatistics>();
			var deaths = stats?.DeathsCost ?? 0;
			var kills = stats?.KillsCost ?? 0;
			var (delta, killDelta) = CostDeltas(deaths, kills,
				ref previousDeathsCost, ref previousKillsCost, ref costCountersInitialized);
			if (delta > 0)
				lossSamples.Enqueue((tick, delta));
			if (killDelta > 0)
				killSamples.Enqueue((tick, killDelta));

			while (lossSamples.Count > 0 && tick - lossSamples.Peek().Tick > Info.LossWindowTicks)
				lossSamples.Dequeue();
			while (killSamples.Count > 0 && tick - killSamples.Peek().Tick > Info.LossWindowTicks)
				killSamples.Dequeue();

			var liveProduction = player.World.ActorsHavingTrait<Production>()
				.Where(a => a.IsInWorld && !a.IsDead && a.Owner == player && a.Info.HasTraitInfo<ProductionInfo>())
				.Select(a => a.ActorID)
				.ToHashSet();
			if (productionBuildings.Count > 0 && productionBuildings.Any(id => !liveProduction.Contains(id)))
				productionLossTicks.Enqueue(tick);
			productionBuildings.Clear();
			foreach (var id in liveProduction)
				productionBuildings.Add(id);
			while (productionLossTicks.Count > 0 && tick - productionLossTicks.Peek() > Info.LossWindowTicks)
				productionLossTicks.Dequeue();

			DeathsCostWindow = lossSamples.Sum(s => s.Delta);
			KillsCostWindow = killSamples.Sum(s => s.Delta);
			currentUrgency = DeathsCostWindow > Info.EmergencyLossThreshold || productionLossTicks.Count > 0
				? BotUrgency.Emergency
				: BotUrgency.Normal;
		}

		EnemyProfile BuildProfile(OpenRA.Player enemy, Actor[] enemyActors, Actor[] ownBuildings, int tick)
		{
			var profile = new EnemyProfile
			{
				Player = enemy,
				Name = enemy.InternalName,
				FactionName = enemy.Faction?.InternalName ?? "",
				Alive = enemy.WinState == WinState.Undefined && enemyActors.Length > 0,
				NearestCells = -1,
				LastSeenTick = tick,
				BuildingCount = enemyActors.Count(IsBuilding)
			};
			var enemyBuildings = enemyActors.Where(IsBuilding).ToArray();
			var combat = enemyActors.Where(IsCombatUnit).ToArray();
			profile.Harvesters = enemyActors.Count(a => a.Info.HasTraitInfo<HarvesterInfo>());
			foreach (var actor in combat)
			{
				var value = Value(actor);
				profile.ArmyValue += value;
				if (actor.Info.HasTraitInfo<AircraftInfo>())
					profile.AirValue += value;
				else
				{
					var types = actor.GetEnabledTargetTypes();
					if (types.Overlaps(Info.InfantryTargetTypes))
						profile.InfantryValue += value;
					if (types.Overlaps(Info.VehicleTargetTypes))
						profile.VehicleValue += value;
					if (types.Overlaps(Info.NavalTargetTypes))
						profile.NavalValue += value;
				}
				if (actor.Info.HasTraitInfo<CloakInfo>())
					profile.StealthShare += value;
				if (ownBuildings.Any(b => (actor.Location - b.Location).Length <= Info.PressureRadius))
					profile.PressureValue += value;
			}

			foreach (var building in enemyBuildings)
			{
				var value = Value(building);
				if (IsDefence(building))
				{
					profile.DefenceCount++;
					profile.DefenceValue += value;
				}
				if (building.Info.HasTraitInfo<ProvidesPrerequisiteInfo>())
					profile.TechBuildings++;
				if (building.Info.HasTraitInfo<ProductionInfo>())
					profile.ProductionBuildings++;
				if (building.Info.HasTraitInfo<RefineryInfo>())
					profile.Refineries++;
			}

			profile.StealthShare = profile.ArmyValue == 0 ? 0 : Clamp(profile.StealthShare * 100 / profile.ArmyValue);
			profile.ExpansionClusters = ClusterCount(enemyBuildings);
			if (enemyBuildings.Length > 0)
			{
				var ownBase = ownBuildings.Where(a => a.Info.HasTraitInfo<BaseBuildingInfo>()).ToArray();
				var baseActors = ownBase.Length > 0 ? ownBase : ownBuildings.Take(1).ToArray();
				if (baseActors.Length > 0)
				{
					var ownCenter = new CPos(baseActors.Sum(a => a.Location.X) / baseActors.Length,
						baseActors.Sum(a => a.Location.Y) / baseActors.Length);
					profile.NearestCells = enemyBuildings.Min(a => (a.Location - ownCenter).Length);
				}
			}
			return profile;
		}

		int ClusterCount(Actor[] buildings)
		{
			var seeds = new List<CPos>();
			foreach (var building in buildings.Where(a => a.Info.HasTraitInfo<BaseBuildingInfo>() || a.Info.HasTraitInfo<RefineryInfo>()))
				if (!seeds.Any(seed => (building.Location - seed).Length <= Info.ClusterRadius))
					seeds.Add(building.Location);
			return seeds.Count;
		}

		internal static EnemyProfile ChooseTarget(IEnumerable<EnemyProfile> candidates, EnemyProfile incumbent,
			int incumbentSince, int tick, MasterAiBotModuleInfo info)
		{
			var list = candidates.ToList();
			if (incumbent != null && tick - incumbentSince < info.MinimumHoldTicks)
			{
				if (list.Contains(incumbent))
					return incumbent;
			}
			return list.OrderByDescending(p => Momentum(p, p == incumbent ? info.IncumbentMomentum : 0))
				.ThenBy(p => p.Name ?? p.Player?.InternalName ?? "", StringComparer.Ordinal).FirstOrDefault();
		}

		internal static int Momentum(EnemyProfile profile, int bonus)
		{
			return ClampScore(profile.Score + profile.Score * bonus / 1000);
		}

		internal static bool ShouldSwitchPersonality(string current, string candidate, int lastSwitchTick, int tick,
			bool emergencyTransition, bool allowSwitching, MasterAiBotModuleInfo info)
		{
			if (!allowSwitching || string.IsNullOrEmpty(candidate) || candidate == current)
				return false;

			return emergencyTransition || tick - lastSwitchTick >= info.PersonalityHoldTicks;
		}

		internal static bool ShouldEvaluatePersonality(bool decision, BotUrgency urgency, bool handled)
		{
			return decision || urgency == BotUrgency.Emergency && !handled;
		}

		internal static int Saturate(int x, int k)
		{
			if (x <= 0)
				return 0;
			if (k < 0)
				k = 0;
			return ClampSignal((long)100 * x / (x + (long)k));
		}

		internal static int TargetScore(EnemyProfile profile, int ownArmy, MasterAiBotModuleInfo info)
			=> TargetScore(profile, ownArmy, 0, 0, info);

		static int TargetScore(EnemyProfile profile, int ownArmy, int ally, long econTotal,
			MasterAiBotModuleInfo info)
		{
			var reach = profile.NearestCells < 0 ? 0 : 100 - Saturate(profile.NearestCells, 25);
			var weak = Saturate(ownArmy, profile.ArmyValue);
			var econProxy = profile.Harvesters + profile.Refineries * 2;
			var econ = econTotal <= 0 ? 0 : ClampSignal((long)econProxy * 100 / econTotal);
			var kill = 100 - Saturate(profile.BuildingCount, info.EliminationBuildingSaturation);
			var fort = Saturate(profile.DefenceValue, 1500);
			var total = Math.Max(1, info.WeightReach + info.WeightWeak + info.WeightEcon + info.WeightKill + info.WeightDefence + info.WeightAlly);
			var score = (long)info.WeightReach * reach + (long)info.WeightWeak * weak + (long)info.WeightEcon * econ +
				(long)info.WeightKill * kill - (long)info.WeightDefence * fort - (long)info.WeightAlly * ally;
			return ClampScore(score * 10 / total);
		}

		internal static bool ShouldEvaluateDecision(int lastDecisionTick, int tick, int decisionInterval)
		{
			return tick - lastDecisionTick >= Math.Max(1, decisionInterval);
		}

		internal static bool ShouldEvaluateTargetDecision(bool hasIncumbent, bool incumbentAvailable,
			int lastDecisionTick, int tick, int decisionInterval)
		{
			return hasIncumbent && !incumbentAvailable ||
				ShouldEvaluateDecision(lastDecisionTick, tick, decisionInterval);
		}

		internal static (int Deaths, int Kills) CostDeltas(int deaths, int kills,
			ref int previousDeaths, ref int previousKills, ref bool initialized)
		{
			if (!initialized)
			{
				previousDeaths = deaths;
				previousKills = kills;
				initialized = true;
				return (0, 0);
			}

			var result = (Math.Max(0, deaths - previousDeaths), Math.Max(0, kills - previousKills));
			previousDeaths = deaths;
			previousKills = kills;
			return result;
		}

		int AlliedCommitments(OpenRA.Player enemy)
		{
			return player.World.Players
				.Where(p => p != player && p.IsBot && IsEligible(p) && player.IsAlliedWith(p))
				.Select(p => p.PlayerActor.TraitOrDefault<MasterAiBotModule>()?.Situation)
				.Count(s => s?.MainTarget == enemy);
		}

		internal static string CandidatePersonality(BotUrgency urgency, EnemyProfile target, int ownArmy,
			IEnumerable<EnemyProfile> enemies, string incumbent, IEnumerable<string> availablePersonalities,
			MasterAiBotModuleInfo info)
		{
			var available = availablePersonalities.ToHashSet(StringComparer.Ordinal);
			foreach (var candidate in PersonalityCandidates(urgency, target, ownArmy, enemies, info))
				if (available.Contains(candidate))
					return candidate;

			return incumbent != null && available.Contains(incumbent) ? incumbent : "";
		}

		internal static string UnfilteredCandidatePersonality(BotUrgency urgency, EnemyProfile target, int ownArmy,
			IEnumerable<EnemyProfile> enemies, string incumbent, MasterAiBotModuleInfo info)
		{
			return PersonalityCandidates(urgency, target, ownArmy, enemies, info).FirstOrDefault() ?? incumbent ?? "";
		}

		static IEnumerable<string> PersonalityCandidates(BotUrgency urgency, EnemyProfile target, int ownArmy,
			IEnumerable<EnemyProfile> enemies, MasterAiBotModuleInfo info)
		{
			if (urgency == BotUrgency.Emergency)
				yield return "turtle";
			if (target != null && target.DefenceCount >= info.FortifiedDefenceCount && ownArmy >= info.SteamrollerMinArmyValue)
				yield return "steamroller";
			if (target != null && target.ExpansionClusters >= info.GuerrillaMinClusters)
				yield return "guerrilla";
			if (target != null && target.TechBuildings >= info.TechEnemyTechBuildings &&
				target.ArmyValue < info.RushMaxEnemyArmyValue * 2)
				yield return "tech";
			if (target != null && target.ArmyValue <= info.RushMaxEnemyArmyValue &&
				target.DefenceCount <= info.RushMaxEnemyDefenceCount)
				yield return "rush";
			if (!enemies.Any(e => e.Alive && e.NearestCells >= 0))
				yield return "expansion";
		}

		static CounterDemand BuildDemand(IEnumerable<EnemyProfile> enemies, EnemyProfile target, int totalArmy)
		{
			var values = enemies.ToArray();
			var air = values.Sum(e => e.AirValue);
			var armour = values.Sum(e => e.VehicleValue);
			var infantry = values.Sum(e => e.InfantryValue);
			var stealth = values.Sum(e => e.StealthShare);
			return new CounterDemand
			{
				AntiAir = totalArmy == 0 ? 0 : ClampSignal((long)air * 100 / totalArmy),
				AntiArmour = totalArmy == 0 ? 0 : ClampSignal((long)armour * 100 / totalArmy),
				AntiInfantry = totalArmy == 0 ? 0 : ClampSignal((long)infantry * 100 / totalArmy),
				Detector = totalArmy == 0 ? 0 : ClampSignal(values.Sum(e => (long)e.ArmyValue * e.StealthShare / 100) * 100 / totalArmy),
				Artillery = Saturate(target?.DefenceValue ?? values.Select(e => e.DefenceValue).DefaultIfEmpty().Max(), 1500)
			};
		}

		List<MiniYamlNode> IGameSaveTraitData.IssueTraitData(Actor self)
		{
			if (IsTraitDisabled)
				return null;

			return SerializeState(new MasterAiBotSavedState
			{
				CostCountersInitialized = costCountersInitialized,
				PreviousDeathsCost = previousDeathsCost,
				PreviousKillsCost = previousKillsCost,
				CurrentUrgency = currentUrgency,
				LastPersonalitySwitchTick = lastPersonalitySwitchTick,
				EmergencyPersonalityHandled = emergencyPersonalityHandled,
				LossSamples = lossSamples.ToArray(),
				KillSamples = killSamples.ToArray(),
				ProductionLossTicks = productionLossTicks.ToArray(),
				ProductionBuildings = productionBuildings.OrderBy(id => id).ToArray()
			});
		}

		void IGameSaveTraitData.ResolveTraitData(Actor self, MiniYaml data)
		{
			if (self.World.IsReplay)
				return;

			var state = DeserializeState(data);
			costCountersInitialized = state.CostCountersInitialized;
			previousDeathsCost = state.PreviousDeathsCost;
			previousKillsCost = state.PreviousKillsCost;
			currentUrgency = state.CurrentUrgency;
			lastPersonalitySwitchTick = state.LastPersonalitySwitchTick;
			emergencyPersonalityHandled = state.EmergencyPersonalityHandled;

			lossSamples.Clear();
			foreach (var sample in state.LossSamples)
				lossSamples.Enqueue(sample);
			killSamples.Clear();
			foreach (var sample in state.KillSamples)
				killSamples.Enqueue(sample);
			DeathsCostWindow = lossSamples.Sum(s => s.Delta);
			KillsCostWindow = killSamples.Sum(s => s.Delta);

			productionLossTicks.Clear();
			foreach (var tick in state.ProductionLossTicks)
				productionLossTicks.Enqueue(tick);

			productionBuildings.Clear();
			foreach (var id in state.ProductionBuildings)
				productionBuildings.Add(id);
		}

		internal static List<MiniYamlNode> SerializeState(MasterAiBotSavedState state)
		{
			return new List<MiniYamlNode>
			{
				new("CostCountersInitialized", FieldSaver.FormatValue(state.CostCountersInitialized)),
				new("PreviousDeathsCost", FieldSaver.FormatValue(state.PreviousDeathsCost)),
				new("PreviousKillsCost", FieldSaver.FormatValue(state.PreviousKillsCost)),
				new("CurrentUrgency", FieldSaver.FormatValue(state.CurrentUrgency)),
				new("LastPersonalitySwitchTick", FieldSaver.FormatValue(state.LastPersonalitySwitchTick)),
				new("EmergencyPersonalityHandled", FieldSaver.FormatValue(state.EmergencyPersonalityHandled)),
				new("LossSamples", "", state.LossSamples.Select(SampleNode).ToList()),
				new("KillSamples", "", state.KillSamples.Select(SampleNode).ToList()),
				new("ProductionLossTicks", FieldSaver.FormatValue(state.ProductionLossTicks)),
				new("ProductionBuildings", FieldSaver.FormatValue(state.ProductionBuildings))
			};
		}

		internal static MasterAiBotSavedState DeserializeState(MiniYaml data)
		{
			var state = new MasterAiBotSavedState();
			var nodes = data.ToDictionary();
			if (nodes.TryGetValue("CostCountersInitialized", out var initializedNode))
				state.CostCountersInitialized = FieldLoader.GetValue<bool>("CostCountersInitialized", initializedNode.Value);
			if (nodes.TryGetValue("PreviousDeathsCost", out var deathsNode))
				state.PreviousDeathsCost = FieldLoader.GetValue<int>("PreviousDeathsCost", deathsNode.Value);
			if (nodes.TryGetValue("PreviousKillsCost", out var killsNode))
				state.PreviousKillsCost = FieldLoader.GetValue<int>("PreviousKillsCost", killsNode.Value);
			if (nodes.TryGetValue("CurrentUrgency", out var urgencyNode))
				state.CurrentUrgency = FieldLoader.GetValue<BotUrgency>("CurrentUrgency", urgencyNode.Value);
			if (nodes.TryGetValue("LastPersonalitySwitchTick", out var switchNode))
				state.LastPersonalitySwitchTick = FieldLoader.GetValue<int>("LastPersonalitySwitchTick", switchNode.Value);
			if (nodes.TryGetValue("EmergencyPersonalityHandled", out var handledNode))
				state.EmergencyPersonalityHandled = FieldLoader.GetValue<bool>("EmergencyPersonalityHandled", handledNode.Value);

			state.LossSamples = ReadSamples(nodes, "LossSamples");
			state.KillSamples = ReadSamples(nodes, "KillSamples");
			if (nodes.TryGetValue("ProductionLossTicks", out var productionLossNode))
				state.ProductionLossTicks = FieldLoader.GetValue<int[]>("ProductionLossTicks", productionLossNode.Value);
			if (nodes.TryGetValue("ProductionBuildings", out var productionBuildingsNode))
				state.ProductionBuildings = FieldLoader.GetValue<uint[]>("ProductionBuildings", productionBuildingsNode.Value);
			return state;
		}

		static MiniYamlNode SampleNode((int Tick, int Delta) sample)
		{
			return new MiniYamlNode("Sample", FieldSaver.FormatValue(new[] { sample.Tick, sample.Delta }));
		}

		static (int Tick, int Delta)[] ReadSamples(Dictionary<string, MiniYaml> nodes, string key)
		{
			if (!nodes.TryGetValue(key, out var node))
				return Array.Empty<(int, int)>();

			var samples = new List<(int Tick, int Delta)>();
			foreach (var sampleNode in node.Nodes)
			{
				var values = FieldLoader.GetValue<int[]>("Sample", sampleNode.Value.Value);
				if (values.Length == 2)
					samples.Add((values[0], values[1]));
			}

			return samples.ToArray();
		}

		static bool IsEligible(OpenRA.Player p) => !p.NonCombatant && p.Playable;
		static int EconProxy(EnemyProfile profile) => profile.Harvesters + profile.Refineries * 2;
		static bool IsBuilding(Actor a) => a.Info.HasTraitInfo<BuildingInfo>();
		bool IsDefence(Actor a) => IsBuilding(a) && (a.Info.HasTraitInfo<AttackBaseInfo>() ||
			a.GetEnabledTargetTypes().Overlaps(Info.DefenceTargetTypes));
		static bool IsCombatUnit(Actor a) => a.Info.HasTraitInfo<AttackBaseInfo>() && !IsBuilding(a) && !a.Info.HasTraitInfo<HarvesterInfo>();
		static int Value(Actor a) => a.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0;
		static int Clamp(long value) => (int)Math.Max(0, Math.Min(100, value));
		static int ClampSignal(long value) => (int)Math.Max(0, Math.Min(100, value));
		static int ClampScore(long value) => (int)Math.Max(0, Math.Min(1000, value));
	}
}
