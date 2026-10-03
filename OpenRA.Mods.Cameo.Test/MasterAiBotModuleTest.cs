#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using NUnit.Framework;
using OpenRA;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public sealed class MasterAiBotModuleTest
	{
		sealed class EnemyProfiles : IReadOnlyDictionary<OpenRA.Player, EnemyProfile>
		{
			readonly EnemyProfile profile;

			public EnemyProfiles(EnemyProfile profile) { this.profile = profile; }
			public IEnumerable<OpenRA.Player> Keys { get { yield return null; } }
			public IEnumerable<EnemyProfile> Values { get { yield return profile; } }
			public int Count => 1;
			public EnemyProfile this[OpenRA.Player key] => profile;
			public bool ContainsKey(OpenRA.Player key) => true;
			public bool TryGetValue(OpenRA.Player key, out EnemyProfile value)
			{
				value = profile;
				return true;
			}

			public IEnumerator<KeyValuePair<OpenRA.Player, EnemyProfile>> GetEnumerator()
			{
				yield return new KeyValuePair<OpenRA.Player, EnemyProfile>(null, profile);
			}

			IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
		}

		static BotSituation Situation(BotUrgency urgency = BotUrgency.Normal, string personality = "",
			OpenRA.Player target = null, IReadOnlyDictionary<OpenRA.Player, EnemyProfile> enemies = null)
		{
			return new BotSituation
			{
				Tick = 1500,
				Urgency = urgency,
				Personality = personality,
				MainTarget = target,
				Enemies = enemies ?? new Dictionary<OpenRA.Player, EnemyProfile>(),
				Demand = new CounterDemand()
			};
		}

		[Test]
		public void SituationEmitterProducesParseableEmptyNullTargetRecord()
		{
			var b = new StringBuilder();
			AiSituationLogWriter.AppendSituation(b, "game", "", "map", "Multi0", "td_gdi", "medium", "rush",
				Situation());
			using var doc = JsonDocument.Parse(b.ToString());
			Assert.That(doc.RootElement.GetProperty("kind").GetString(), Is.EqualTo("situation"));
			Assert.That(doc.RootElement.GetProperty("main_target").GetString(), Is.Empty);
			Assert.That(doc.RootElement.GetProperty("enemies").GetArrayLength(), Is.Zero);
			Assert.That(doc.RootElement.EnumerateObject().Select(p => p.Name), Is.EqualTo(new[]
			{
				"schema", "kind", "record_id", "game_uid", "map_uid", "player", "faction", "bot_type",
				"tick", "urgency", "personality_current", "personality_candidate", "main_target",
				"main_target_score", "mission", "mission_assignment", "hints", "demand", "own", "enemies"
			}));
			Assert.That(doc.RootElement.GetProperty("schema").GetInt32(), Is.EqualTo(2));
			Assert.That(doc.RootElement.GetProperty("mission").ValueKind, Is.EqualTo(JsonValueKind.Null));
			Assert.That(doc.RootElement.GetProperty("own").GetProperty("losses_by_role").EnumerateObject().Count(), Is.Zero);
		}

		[Test]
		public void SituationEmitterProducesParseablePopulatedRecord()
		{
			var enemy = new EnemyProfile
			{
				Name = "Multi1",
				FactionName = "td_nod",
				Alive = true,
				ArmyValue = 8100,
				InfantryValue = 2000,
				VehicleValue = 5000,
				AirValue = 1100,
				DefenceCount = 7,
				DefenceValue = 3500,
				TechBuildings = 4,
				ProductionBuildings = 3,
				BuildingCount = 9,
				ExpansionClusters = 2,
				Harvesters = 5,
				Refineries = 2,
				PressureValue = 800,
				StealthShare = 10,
				NearestCells = 42,
				LastSeenTick = 1500,
				Score = 730
			};
			var b = new StringBuilder();
			var situation = Situation(BotUrgency.Pressured, "steamroller", null,
				new EnemyProfiles(enemy));
			situation.Mission = new BotMission { Type = BotMissionType.Raid, Priority = 65, RegionIndex = 18 };
			situation.Threats.Add((new BotThreatTracker.Group(40, 60, 3000, 5) { VelocityX = 0.05 },
				new BotThreatTracker.Prediction(new CPos(80, 60), 2500, 800)));
			situation.LossesByRole["rush"] = 5400;
			situation.LossesByRole["idle"] = 700;
			situation.AwayLossesByRole["rush"] = 4800;
			AiSituationLogWriter.AppendSituation(b, "game", "", "map", "Multi0", "td_gdi", "medium", "rush",
				situation);
			using var doc = JsonDocument.Parse(b.ToString());
			var own = doc.RootElement.GetProperty("own");
			Assert.That(own.GetProperty("losses_by_role").EnumerateObject().Select(p => p.Name), Is.EqualTo(new[] { "idle", "rush" }));
			Assert.That(own.GetProperty("losses_by_role").GetProperty("rush").GetInt32(), Is.EqualTo(5400));
			Assert.That(own.GetProperty("away_losses_by_role").GetProperty("rush").GetInt32(), Is.EqualTo(4800));
			Assert.That(own.GetProperty("combat_ratio_pct").GetInt32(), Is.Zero);
			var threat = own.GetProperty("threats")[0];
			Assert.That(threat.GetProperty("target").GetString(), Is.EqualTo("80,60"));
			Assert.That(threat.GetProperty("eta").GetInt32(), Is.EqualTo(800));
			Assert.That(threat.GetProperty("vx_per_kilotick").GetInt32(), Is.EqualTo(50));
			var enemyJson = doc.RootElement.GetProperty("enemies")[0];
			Assert.That(enemyJson.GetProperty("name").GetString(), Is.EqualTo("Multi1"));
			Assert.That(enemyJson.GetProperty("faction").GetString(), Is.EqualTo("td_nod"));
			Assert.That(enemyJson.GetProperty("army_value").GetInt32(), Is.EqualTo(8100));
			Assert.That(enemyJson.GetProperty("buildings").GetInt32(), Is.EqualTo(9));
			Assert.That(doc.RootElement.GetProperty("urgency").GetString(), Is.EqualTo("pressured"));
			Assert.That(doc.RootElement.GetProperty("personality_candidate").GetString(), Is.EqualTo("steamroller"));
			Assert.That(doc.RootElement.GetProperty("mission").GetProperty("type").GetString(), Is.EqualTo("raid"));
			Assert.That(doc.RootElement.GetProperty("mission").GetProperty("priority").GetInt32(), Is.EqualTo(65));
			Assert.That(doc.RootElement.GetProperty("mission").GetProperty("region_index").GetInt32(), Is.EqualTo(18));
			Assert.That(enemyJson.EnumerateObject().Select(p => p.Name), Is.EqualTo(new[]
			{
				"name", "faction", "alive", "army_value", "infantry_value", "vehicle_value", "air_value",
				"naval_value", "defence_count", "defence_value", "tech_buildings", "production_buildings",
				"buildings", "expansion_clusters", "harvesters", "harvester_count", "known_regions",
				"refineries", "pressure_value", "stealth_share", "nearest_cells", "last_seen_tick", "score",
				"army_value_delta" // §12.14 PL telemetry (#658)
			}));
		}

		[TestCase(false, false, true, true)]
		[TestCase(true, false, true, false)]
		[TestCase(false, true, true, false)]
		[TestCase(false, false, false, false)]
		public void SituationLogEligibilityExcludesReplaySaveAndNonHost(bool replay, bool save, bool host, bool expected)
		{
			Assert.That(AiSituationLogWriter.Eligible(WorldType.Regular, replay, save, host), Is.EqualTo(expected));
			Assert.That(AiSituationLogWriter.Eligible(WorldType.Shellmap, replay, save, host), Is.False);
			Assert.That(AiSituationLogWriter.Eligible(WorldType.Editor, replay, save, host), Is.False);
		}

		[Test]
		public void SaturationIsMonotonicBoundedAndHandlesZeroK()
		{
			Assert.That(MasterAiBotModule.Saturate(0, 0), Is.Zero);
			Assert.That(MasterAiBotModule.Saturate(10, 20), Is.LessThanOrEqualTo(MasterAiBotModule.Saturate(20, 20)));
			Assert.That(MasterAiBotModule.Saturate(int.MaxValue, 0), Is.EqualTo(100));
			Assert.That(MasterAiBotModule.Saturate(int.MaxValue, int.MaxValue), Is.InRange(0, 100));
		}

		[Test]
		public void DecisionCadenceStartsAtFirstRebuild()
		{
			var info = new MasterAiBotModuleInfo();
			var initialTick = -Math.Max(1, info.DecisionInterval);
			Assert.That(MasterAiBotModule.ShouldEvaluateDecision(initialTick, 0, info.DecisionInterval), Is.True);
			Assert.That(MasterAiBotModule.ShouldEvaluateDecision(0, 1, info.DecisionInterval), Is.False);
		}

		[TestCase(true, false, true)]
		[TestCase(true, true, false)]
		[TestCase(false, false, true)]
		public void TargetDecisionBypassesCadenceWhenNoTargetIsHeld(
			bool hasIncumbent, bool incumbentAvailable, bool expected)
		{
			var info = new MasterAiBotModuleInfo();
			Assert.That(MasterAiBotModule.ShouldEvaluateTargetDecision(
				hasIncumbent, incumbentAvailable, 0, 1, info.DecisionInterval), Is.EqualTo(expected));
		}

		[Test]
		public void CostCountersBaselineCumulativeStatsBeforeProducingDeltas()
		{
			var previousDeaths = 0;
			var previousKills = 0;
			var initialized = false;
			Assert.That(MasterAiBotModule.CostDeltas(5000, 2000,
				ref previousDeaths, ref previousKills, ref initialized), Is.EqualTo((0, 0)));
			Assert.That((previousDeaths, previousKills, initialized), Is.EqualTo((5000, 2000, true)));
			Assert.That(MasterAiBotModule.CostDeltas(5600, 2250,
				ref previousDeaths, ref previousKills, ref initialized), Is.EqualTo((600, 250)));
		}

		[Test]
		public void FreshGameCostCountersCountLossesBeforeTheFirstStaggeredCheck()
		{
			var previousDeaths = 0;
			var previousKills = 0;
			var initialized = true;
			Assert.That(MasterAiBotModule.CostDeltas(700, 100,
				ref previousDeaths, ref previousKills, ref initialized), Is.EqualTo((700, 100)));
		}

		[Test]
		public void MasterAiSaveStateRoundTripsEmergencyWindowsAndPersonalityHold()
		{
			var original = new MasterAiBotSavedState
			{
				CostCountersInitialized = true,
				PreviousDeathsCost = 5600,
				PreviousKillsCost = 2250,
				CurrentUrgency = BotUrgency.Emergency,
				LastPersonalitySwitchTick = 4321,
				PersonalityCandidateSince = 4100,
				PersonalityCandidate = "turtle",
				EmergencyPersonalityHandled = true,
				LossSamples = new[] { (4100, 250), (4250, 350) },
				KillSamples = new[] { (4200, 125), (4300, 125) },
				ProductionLossTicks = new[] { 4150, 4275 },
				ProductionBuildings = new uint[] { 17, 29 }
			};
			var nodes = new List<MiniYamlNode>
			{
				new("State", "", MasterAiBotModule.SerializeState(original))
			};
			var serialized = nodes.WriteToString();
			var restored = MasterAiBotModule.DeserializeState(
				MiniYaml.FromString(serialized, "test").Single().Value);

			Assert.That(restored.CostCountersInitialized, Is.True);
			Assert.That(restored.PreviousDeathsCost, Is.EqualTo(5600));
			Assert.That(restored.PreviousKillsCost, Is.EqualTo(2250));
			Assert.That(restored.CurrentUrgency, Is.EqualTo(BotUrgency.Emergency));
			Assert.That(restored.LastPersonalitySwitchTick, Is.EqualTo(4321));
			Assert.That(restored.PersonalityCandidateSince, Is.EqualTo(4100));
			Assert.That(restored.PersonalityCandidate, Is.EqualTo("turtle"));
			Assert.That(restored.EmergencyPersonalityHandled, Is.True);
			Assert.That(restored.LossSamples, Is.EqualTo(original.LossSamples));
			Assert.That(restored.KillSamples, Is.EqualTo(original.KillSamples));
			Assert.That(restored.ProductionLossTicks, Is.EqualTo(original.ProductionLossTicks));
			Assert.That(restored.ProductionBuildings, Is.EqualTo(original.ProductionBuildings));

			var previousDeaths = restored.PreviousDeathsCost;
			var previousKills = restored.PreviousKillsCost;
			var initialized = restored.CostCountersInitialized;
			Assert.That(MasterAiBotModule.CostDeltas(5600, 2250,
				ref previousDeaths, ref previousKills, ref initialized), Is.EqualTo((0, 0)));
		}

		[Test]
		public void TargetScoreStaysBoundedForExtremeProfiles()
		{
			var info = new MasterAiBotModuleInfo();
			foreach (var profile in new[]
			{
				new EnemyProfile { ArmyValue = 0, DefenceCount = 0, NearestCells = -1 },
				new EnemyProfile { ArmyValue = int.MaxValue, DefenceValue = int.MaxValue, DefenceCount = int.MaxValue, NearestCells = int.MaxValue }
			})
				Assert.That(MasterAiBotModule.TargetScore(profile, int.MaxValue, info), Is.InRange(0, 1000));
			Assert.That(MasterAiBotModule.Momentum(new EnemyProfile { Score = 1000 }, info.IncumbentMomentum),
				Is.EqualTo(1000));
		}

		[Test]
		public void TargetScoreDistinguishesCandidatesAndChoosesTheHigherScore()
		{
			var info = new MasterAiBotModuleInfo();
			var reachableWeak = new EnemyProfile { Name = "reachable-weak", ArmyValue = 100, NearestCells = 5 };
			var distantStrong = new EnemyProfile { Name = "distant-strong", ArmyValue = 10000, NearestCells = 50, BuildingCount = 8 };
			reachableWeak.Score = MasterAiBotModule.TargetScore(reachableWeak, 1000, info);
			distantStrong.Score = MasterAiBotModule.TargetScore(distantStrong, 1000, info);

			Assert.That(reachableWeak.Score, Is.GreaterThan(distantStrong.Score));
			Assert.That(MasterAiBotModule.ChooseTarget(new[] { distantStrong, reachableWeak }, null, 0, 0, info),
				Is.SameAs(reachableWeak));
		}

		[Test]
		public void TargetScoreHurtPenalisesTheEnemyBeatingUs()
		{
			var info = new MasterAiBotModuleInfo();
			var profile = new EnemyProfile { Name = "aggressor", ArmyValue = 100, NearestCells = 5 };
			var calm = MasterAiBotModule.TargetScore(profile, 1000, 0, 0, 0, info);
			var hurt = MasterAiBotModule.TargetScore(profile, 1000, 0, 0, 100, info);

			// §4.3: WeightHurt=150 is live now that the dealt-side producer landed —
			// a high taken-share of the exchange lowers the target score.
			Assert.That(hurt, Is.LessThan(calm));
			Assert.That(hurt, Is.GreaterThanOrEqualTo(0));
		}

		[Test]
		public void TargetScoreIntelAgePenalisesStaleIntel()
		{
			// CA-6 (§12.9): with WeightIntelAge armed, an enemy unseen for
			// IntelStaleTicks scores below an identical freshly-scouted one;
			// never-seen saturates at maximum staleness. Weight 0 is byte-identical.
			var info = FieldLoader.Load<MasterAiBotModuleInfo>(new MiniYaml("", new[]
			{
				new MiniYamlNode("WeightIntelAge", new MiniYaml("120")),
				new MiniYamlNode("IntelStaleTicks", new MiniYaml("4500"))
			}));
			var fresh = new EnemyProfile { Name = "fresh", ArmyValue = 100, NearestCells = 5, LastSeenTick = 9900 };
			var stale = new EnemyProfile { Name = "stale", ArmyValue = 100, NearestCells = 5, LastSeenTick = 1000 };
			var unseen = new EnemyProfile { Name = "unseen", ArmyValue = 100, NearestCells = 5, LastSeenTick = 0 };
			const int tick = 10000;

			Assert.That(MasterAiBotModule.TargetScore(fresh, 1000, 0, 0, 0, tick, info),
				Is.GreaterThan(MasterAiBotModule.TargetScore(stale, 1000, 0, 0, 0, tick, info)),
				"stale intel must score below fresh intel for identical profiles");
			Assert.That(MasterAiBotModule.TargetScore(stale, 1000, 0, 0, 0, tick, info),
				Is.GreaterThan(MasterAiBotModule.TargetScore(unseen, 1000, 0, 0, 0, tick, info)),
				"never-seen carries the strict maximum penalty (Saturate is asymptotic, age only approaches it)");

			var defaultInfo = new MasterAiBotModuleInfo();
			Assert.That(MasterAiBotModule.TargetScore(stale, 1000, 0, 0, 0, tick, defaultInfo),
				Is.EqualTo(MasterAiBotModule.TargetScore(fresh, 1000, 0, 0, 0, tick, defaultInfo)),
				"WeightIntelAge=0 must ignore intel age entirely");
		}

		[Test]
		public void HurtShareTracksTheExchangeBalance()
		{
			// The bounded form of §4.3's dealt/taken ratio: our share of the exchange
			// lost, 0-100. No exchange yet is neutral, not 100.
			Assert.That(MasterAiBotModule.HurtShare(0, 0), Is.EqualTo(0));
			Assert.That(MasterAiBotModule.HurtShare(50, 50), Is.EqualTo(50));
			Assert.That(MasterAiBotModule.HurtShare(100, 0), Is.EqualTo(100));
			Assert.That(MasterAiBotModule.HurtShare(0, 100), Is.EqualTo(0));
			Assert.That(MasterAiBotModule.HurtShare(25, 75), Is.EqualTo(25));
		}

		[Test]
		public void TargetChoiceHoldsIncumbentWithinMinimumHold()
		{
			var info = new MasterAiBotModuleInfo();
			var incumbent = new EnemyProfile { Name = "Multi0", Score = 100, NearestCells = 10 };
			var better = new EnemyProfile { Name = "Multi1", Score = 900, NearestCells = 10 };
			Assert.That(MasterAiBotModule.ChooseTarget(new[] { incumbent, better }, incumbent, 1000, 1000 + info.MinimumHoldTicks - 1, info),
				Is.SameAs(incumbent));
		}

		[Test]
		public void TargetChoiceSelectsBetterCandidateAfterHold()
		{
			var info = new MasterAiBotModuleInfo();
			var incumbent = new EnemyProfile { Name = "Multi0", Score = 100, NearestCells = 10 };
			var better = new EnemyProfile { Name = "Multi1", Score = 900, NearestCells = 10 };
			Assert.That(MasterAiBotModule.ChooseTarget(new[] { incumbent, better }, incumbent, 1000, 1000 + info.MinimumHoldTicks, info),
				Is.SameAs(better));
		}

		[Test]
		public void TargetChoiceSwitchesWhenIncumbentIsInvalid()
		{
			var info = new MasterAiBotModuleInfo();
			var incumbent = new EnemyProfile { Name = "Multi0", Score = 100, NearestCells = -1 };
			var better = new EnemyProfile { Name = "Multi1", Score = 900, NearestCells = 10 };
			Assert.That(MasterAiBotModule.ChooseTarget(new[] { better }, incumbent, 1000, 1000 + 1, info),
				Is.SameAs(better));
		}

		[Test]
		public void TargetChoiceDoesNotExtendHoldWhenChoiceIsUnchanged()
		{
			var info = new MasterAiBotModuleInfo();
			var incumbent = new EnemyProfile { Name = "Multi0", Score = 900, NearestCells = 10 };
			var better = new EnemyProfile { Name = "Multi1", Score = 100, NearestCells = 10 };
			var chosen = MasterAiBotModule.ChooseTarget(new[] { incumbent, better }, incumbent, 1000, 1000 + info.MinimumHoldTicks, info);
			Assert.That(chosen, Is.SameAs(incumbent));
			Assert.That(MasterAiBotModule.ChooseTarget(new[] { incumbent, better }, chosen, 1000,
				1000 + info.MinimumHoldTicks + 1, info), Is.SameAs(incumbent));
		}

		static MasterAiBotModuleInfo EmergencyInfo(int armyPct, bool keepsPersonality)
		{
			return FieldLoader.Load<MasterAiBotModuleInfo>(new MiniYaml("", new[]
			{
				new MiniYamlNode("EmergencyLossArmyPct", new MiniYaml(armyPct.ToString())),
				new MiniYamlNode("EmergencyKeepsPersonality", new MiniYaml(keepsPersonality ? "true" : "false"))
			}));
		}

		[Test]
		public void LossEmergencyLegacyModeKeepsAbsoluteRule()
		{
			var info = new MasterAiBotModuleInfo();
			Assert.That(MasterAiBotModule.IsLossEmergency(601, 5000, 100000, false, false, info), Is.True);
			Assert.That(MasterAiBotModule.IsLossEmergency(600, 0, 0, false, false, info), Is.False);
			Assert.That(MasterAiBotModule.IsLossEmergency(400, 0, 0, true, false, info), Is.True);
			Assert.That(MasterAiBotModule.IsLossEmergency(300, 0, 0, true, false, info), Is.False);
		}

		[Test]
		public void LossEmergencyNeedsRelativeLossAndNetLoss()
		{
			var info = EmergencyInfo(25, true);
			// Winning trade is never an emergency, however large the loss.
			Assert.That(MasterAiBotModule.IsLossEmergency(4500, 6000, 12400, false, false, info), Is.False);
			// Big army absorbing a loss: 700 / (50000 + 700) = 1%.
			Assert.That(MasterAiBotModule.IsLossEmergency(700, 0, 50000, false, false, info), Is.False);
			// Absolute floor: a wiped tiny army below the floor does not qualify.
			Assert.That(MasterAiBotModule.IsLossEmergency(600, 0, 0, false, false, info), Is.False);
			// Small army wiped (100%) and net losing.
			Assert.That(MasterAiBotModule.IsLossEmergency(900, 100, 0, false, false, info), Is.True);
			// 4500 / (12400 + 4500) = 26% > 25 and net loss.
			Assert.That(MasterAiBotModule.IsLossEmergency(4500, 3470, 12400, false, false, info), Is.True);
			// Unknown army (-1, just loaded) cannot pass the relative test.
			Assert.That(MasterAiBotModule.IsLossEmergency(4500, 0, -1, false, false, info), Is.False);
		}

		[Test]
		public void LossEmergencyHysteresisClearsAtHalfPercentage()
		{
			var info = EmergencyInfo(25, true);
			// 1000 / (6000 + 1000) = 14%: below the on-percentage, above the clear one (12%).
			Assert.That(MasterAiBotModule.IsLossEmergency(1000, 0, 6000, false, false, info), Is.False);
			Assert.That(MasterAiBotModule.IsLossEmergency(1000, 0, 6000, true, false, info), Is.True);
			// 1000 / (9000 + 1000) = 10% clears; so does a window that stopped being a net loss.
			Assert.That(MasterAiBotModule.IsLossEmergency(1000, 0, 9000, true, false, info), Is.False);
			Assert.That(MasterAiBotModule.IsLossEmergency(1000, 1500, 0, true, false, info), Is.False);
			// Absolute clear threshold still applies.
			Assert.That(MasterAiBotModule.IsLossEmergency(300, 0, 0, true, false, info), Is.False);
		}

		[Test]
		public void LossEmergencyProductionLossStillTriggers()
		{
			Assert.That(MasterAiBotModule.IsLossEmergency(0, 9000, 99999, false, true, EmergencyInfo(25, true)), Is.True);
			Assert.That(MasterAiBotModule.IsLossEmergency(0, 0, 0, false, true, new MasterAiBotModuleInfo()), Is.True);
		}

		[Test]
		public void EmergencyKeepsPersonalityDropsTheTurtleOverride()
		{
			var available = new[] { "rush", "turtle", "tech", "expansion", "steamroller" };
			var target = new EnemyProfile { Alive = true, NearestCells = 10, ArmyValue = 1000 };
			var legacy = new MasterAiBotModuleInfo();
			Assert.That(MasterAiBotModule.CandidatePersonality(BotUrgency.Emergency, target, 0, new[] { target }, "rush",
				available, legacy), Is.EqualTo("turtle"));
			var keeps = EmergencyInfo(25, true);
			// Same candidate as under Pressured (terminal turtle fallback), but reached through the normal chain.
			var weak = new EnemyProfile { Alive = true, NearestCells = 10, ArmyValue = 100 };
			Assert.That(MasterAiBotModule.CandidatePersonality(BotUrgency.Emergency, weak, 0, new[] { weak }, "",
				available, keeps), Is.EqualTo("rush"));
			Assert.That(MasterAiBotModule.CandidatePersonality(BotUrgency.Emergency, target, 0, new[] { target }, "",
				available, keeps), Is.EqualTo(MasterAiBotModule.CandidatePersonality(BotUrgency.Pressured, target, 0,
				new[] { target }, "", available, keeps)));
			Assert.That(MasterAiBotModule.UnfilteredCandidatePersonality(BotUrgency.Emergency, weak, 0, new[] { weak }, "", keeps),
				Is.EqualTo("rush"));
		}

		[Test]
		public void CandidatePersonalityRulesAreOrdered()
		{
			var info = new MasterAiBotModuleInfo();
			var available = new[] { "rush", "turtle", "tech", "expansion", "steamroller" };
			var availableWithGuerrilla = available.Append("guerrilla");
			var target = new EnemyProfile { Alive = true, NearestCells = 10, ArmyValue = 1000 };
			Assert.That(MasterAiBotModule.CandidatePersonality(BotUrgency.Emergency, target, 0, new[] { target }, "",
				available, info), Is.EqualTo("turtle"));
			target.DefenceCount = 6;
			Assert.That(MasterAiBotModule.CandidatePersonality(BotUrgency.Normal, target, 3000, new[] { target }, "",
				available, info), Is.EqualTo("steamroller"));
			target.DefenceCount = 0;
			target.ExpansionClusters = 3;
			target.TechBuildings = 4;
			Assert.That(MasterAiBotModule.CandidatePersonality(BotUrgency.Normal, target, 0, new[] { target }, "",
				available, info), Is.EqualTo("tech"));
			Assert.That(MasterAiBotModule.UnfilteredCandidatePersonality(BotUrgency.Normal, target, 0, new[] { target }, "", info),
				Is.EqualTo("guerrilla"));
			Assert.That(MasterAiBotModule.CandidatePersonality(BotUrgency.Normal, target, 0, new[] { target }, "",
				availableWithGuerrilla, info), Is.EqualTo("guerrilla"));
			target.TechBuildings = 0;
			target.ExpansionClusters = 0;
			target.ArmyValue = 1500;
			target.DefenceCount = 2;
			Assert.That(MasterAiBotModule.CandidatePersonality(BotUrgency.Normal, target, 0, new[] { target }, "",
				available, info), Is.EqualTo("rush"));
			target.ArmyValue = 5000;
			target.DefenceCount = 5;
			target.NearestCells = -1;
			Assert.That(MasterAiBotModule.CandidatePersonality(BotUrgency.Normal, target, 0, new[] { target }, "",
				available, info), Is.EqualTo("expansion"));
			target.NearestCells = 10;
			// Nothing matches a strong-but-unscouted enemy: the terminal fallback
			// picks a posture (calm -> expansion, pressured -> turtle) instead of
			// latching the incumbent forever.
			Assert.That(MasterAiBotModule.CandidatePersonality(BotUrgency.Normal, target, 0, new[] { target }, "turtle",
				available, info), Is.EqualTo("expansion"));
			Assert.That(MasterAiBotModule.CandidatePersonality(BotUrgency.Normal, target, 0, new[] { target }, "guerrilla",
				available, info), Is.EqualTo("expansion"));
			Assert.That(MasterAiBotModule.CandidatePersonality(BotUrgency.Pressured, target, 0, new[] { target }, "rush",
				available, info), Is.EqualTo("turtle"));
		}

		[Test]
		public void CounterDemandRequiresSustainedOnThreshold()
		{
			var info = new MasterAiBotModuleInfo();
			var candidateSince = new Dictionary<string, int>();
			var demand = new CounterDemand { AntiAir = info.AntiAirDemandOn };

			Assert.That(MasterAiBotModule.ResolveDemands(demand, Array.Empty<string>(), 0, 100, candidateSince, info),
				Is.Empty);
			Assert.That(MasterAiBotModule.ResolveDemands(demand, Array.Empty<string>(), 99, 100, candidateSince, info),
				Is.Empty);
			Assert.That(MasterAiBotModule.ResolveDemands(demand, Array.Empty<string>(), 100, 100, candidateSince, info),
				Is.EqualTo(new[] { "antiair" }));
		}

		[Test]
		public void CounterDemandCandidateResetsBelowOnThreshold()
		{
			var info = new MasterAiBotModuleInfo();
			var candidateSince = new Dictionary<string, int>();
			var demand = new CounterDemand { AntiAir = info.AntiAirDemandOn };

			MasterAiBotModule.ResolveDemands(demand, Array.Empty<string>(), 0, 100, candidateSince, info);
			demand.AntiAir = info.AntiAirDemandOn - 1;
			Assert.That(MasterAiBotModule.ResolveDemands(demand, Array.Empty<string>(), 50, 100, candidateSince, info),
				Is.Empty);
			demand.AntiAir = info.AntiAirDemandOn;
			MasterAiBotModule.ResolveDemands(demand, Array.Empty<string>(), 347, 100, candidateSince, info);
			Assert.That(MasterAiBotModule.ResolveDemands(demand, Array.Empty<string>(), 446, 100, candidateSince, info),
				Is.Empty);
			Assert.That(MasterAiBotModule.ResolveDemands(demand, Array.Empty<string>(), 447, 100, candidateSince, info),
				Is.EqualTo(new[] { "antiair" }));
		}

		[Test]
		public void CounterDemandUsesHysteresisForHeldDemand()
		{
			var info = new MasterAiBotModuleInfo();
			var candidateSince = new Dictionary<string, int>();
			var demand = new CounterDemand { AntiAir = info.AntiAirDemandOn - 1 };

			Assert.That(MasterAiBotModule.ResolveDemands(demand, new[] { "antiair" }, 0, 100, candidateSince, info),
				Is.EqualTo(new[] { "antiair" }));
			demand.AntiAir = info.AntiAirDemandOff - 1;
			Assert.That(MasterAiBotModule.ResolveDemands(demand, new[] { "antiair" }, 1, 100, candidateSince, info),
				Is.Empty);
		}

		[Test]
		public void NegativeReactionDelayDisablesCounterDemand()
		{
			var info = new MasterAiBotModuleInfo();
			var candidateSince = new Dictionary<string, int> { ["antiair"] = 10 };
			var demand = new CounterDemand
			{
				AntiAir = 100,
				AntiArmour = 100,
				AntiInfantry = 100,
				Detector = 100,
				Artillery = 100
			};

			Assert.That(MasterAiBotModule.ResolveDemands(demand, new[] { "antiair", "detector" }, 100, -1, candidateSince, info),
				Is.Empty);
			Assert.That(candidateSince, Is.Empty);
		}

		[Test]
		public void CounterDemandCanHoldMultipleDemands()
		{
			var info = new MasterAiBotModuleInfo();
			var demand = new CounterDemand
			{
				AntiAir = info.AntiAirDemandOn,
				AntiArmour = info.AntiArmourDemandOn,
				AntiInfantry = info.AntiInfantryDemandOn,
				Detector = info.DetectorDemandOn,
				Artillery = info.ArtilleryDemandOn
			};

			Assert.That(MasterAiBotModule.ResolveDemands(demand, Array.Empty<string>(), 0, 0,
				new Dictionary<string, int>(), info), Is.EqualTo(new[]
				{
					"antiair", "antiarmour", "antiinfantry", "detector", "artillery"
				}));
		}

		[Test]
		public void CounterDemandStateRoundTrips()
		{
			var original = new MasterAiBotSavedState
			{
				CounterDemandCandidateSince = new Dictionary<string, int>
				{
					["antiair"] = 120,
					["artillery"] = 240
				},
				LastIssuedCounterDemands = new[] { "antiair", "artillery" }
			};
			var nodes = new List<MiniYamlNode>
			{
				new("State", "", MasterAiBotModule.SerializeState(original))
			};

			var restored = MasterAiBotModule.DeserializeState(
				MiniYaml.FromString(nodes.WriteToString(), "test").Single().Value);

			Assert.That(restored.CounterDemandCandidateSince, Is.EqualTo(original.CounterDemandCandidateSince));
			Assert.That(restored.LastIssuedCounterDemands, Is.EqualTo(original.LastIssuedCounterDemands));
		}

		[Test]
		public void PreferOwnedReturnsNonEmptyFilteredSubset()
		{
			var candidates = new List<string> { "target", "other", "target" };
			Assert.That(SquadManagerBotModuleCA.PreferOwned(candidates, candidate => candidate == "target"),
				Is.EqualTo(new[] { "target", "target" }));
		}

		[Test]
		public void PreferOwnedFallsBackWhenFilteredSubsetIsEmpty()
		{
			var candidates = new List<string> { "target", "other" };
			Assert.That(SquadManagerBotModuleCA.PreferOwned(candidates, candidate => candidate == "missing"),
				Is.SameAs(candidates));
		}

		[Test]
		public void PreferOwnedLeavesCandidatesUnchangedWithoutMainTarget()
		{
			var candidates = new List<string> { "target", "other" };
			Assert.That(SquadManagerBotModuleCA.PreferOwned(candidates, null), Is.SameAs(candidates));
		}

		[Test]
		public void PreferOwnedLeavesEmptyCandidatesEmpty()
		{
			var candidates = new List<string>();
			Assert.That(SquadManagerBotModuleCA.PreferOwned(candidates, candidate => true), Is.SameAs(candidates));
		}

		[Test]
		public void PersonalityControllerMapsKnownConditionsAndIgnoresUnknownNames()
		{
			var info = new BotPersonalityControllerInfo();
			Assert.That(BotPersonalityController.PersonalityName("personality-rush", info.PersonalityPrefix), Is.EqualTo("rush"));
			Assert.That(info.Conditions.Any(c => BotPersonalityController.PersonalityName(c, info.PersonalityPrefix) == "steamroller"), Is.True);
			Assert.That(info.Conditions.Any(c => BotPersonalityController.PersonalityName(c, info.PersonalityPrefix) == "guerrilla"), Is.True);
			Assert.That(info.Conditions.Any(c => BotPersonalityController.PersonalityName(c, info.PersonalityPrefix) == "berserker"), Is.False);
		}

		[Test]
		public void PersonalityPinResolvesOnlyMappedBotTypes()
		{
			var pins = new System.Collections.Generic.Dictionary<string, string>
			{
				["exploit_rush"] = "rush",
				["exploit_turtle"] = "turtle",
			};
			Assert.That(BotPersonalityController.PinnedPersonality(pins, "exploit_rush"), Is.EqualTo("rush"));
			Assert.That(BotPersonalityController.PinnedPersonality(pins, "exploit_turtle"), Is.EqualTo("turtle"));
			Assert.That(BotPersonalityController.PinnedPersonality(pins, "hard"), Is.Null);
			Assert.That(BotPersonalityController.PinnedPersonality(pins, null), Is.Null);
		}

		[Test]
		public void PersonalityPinDefaultsToNullWithoutTable()
		{
			Assert.That(BotPersonalityController.PinnedPersonality(null, "exploit_rush"), Is.Null);
		}

		[TestCase("rush", "turtle", 1000, 1000 + 2999, false, 3000, 1000, false)]
		[TestCase("rush", "turtle", 1001, 1000 + 3000, false, 3000, 1000, false)]
		[TestCase("rush", "turtle", 1000, 1000 + 3000, false, 3000, 1000, true)]
		[TestCase("rush", "turtle", 1000, 1000 + 1, true, 7500, 1000, true)]
		[TestCase("rush", "turtle", 1000, 1000 + 3000, false, -1, 1000, false)]
		[TestCase("rush", "", 1000, 1000 + 3000, false, 3000, 1000, false)]
		[TestCase("rush", "rush", 1000, 1000 + 3000, false, 3000, 1000, false)]
		[TestCase("rush", "turtle", 1000, 1750, false, 750, 1000, true)]
		[TestCase("rush", "turtle", 1001, 1750, false, 750, 1000, false)]
		public void PersonalitySwitchPolicyRespectsReactionDelayAndHold(string current, string candidate, int lastSwitchTick,
			int tick, bool emergencyTransition, int reactionDelay, int candidateSince, bool expected)
		{
			Assert.That(MasterAiBotModule.ShouldSwitchPersonality(current, candidate, lastSwitchTick, tick,
				emergencyTransition, reactionDelay, candidateSince, new MasterAiBotModuleInfo()), Is.EqualTo(expected));
		}

		[Test]
		public void SustainedCandidateSinceTracksCandidateEpisodes()
		{
			Assert.That(MasterAiBotModule.SustainedCandidateSince("rush", "rush", 1000, 1500), Is.EqualTo(1000));
			Assert.That(MasterAiBotModule.SustainedCandidateSince("turtle", "rush", 1000, 1500), Is.EqualTo(1500));
			Assert.That(MasterAiBotModule.SustainedCandidateSince("", "rush", 1000, 1500), Is.EqualTo(1500));
		}

		[Test]
		public void EmergencyPersonalitySwitchLatchesPerEpisode()
		{
			var info = new MasterAiBotModuleInfo();
			var handled = false;
			var switches = 0;
			var lastSwitchTick = 1000;
			for (var i = 0; i < 3; i++)
			{
				var urgency = BotUrgency.Emergency;
				var tick = 1000 + i * 150;
				var emergencyTransition = urgency == BotUrgency.Emergency && !handled;
				if (MasterAiBotModule.ShouldSwitchPersonality("rush", "turtle", lastSwitchTick, tick,
					emergencyTransition, 7500, 1000, info))
				{
					switches++;
					lastSwitchTick = tick;
					handled = true;
				}
			}

			Assert.That(switches, Is.EqualTo(1));
			handled = false;
			var recoveryUrgency = BotUrgency.Emergency;
			var recoveryEmergencyTransition = recoveryUrgency == BotUrgency.Emergency && !handled;
			if (MasterAiBotModule.ShouldSwitchPersonality("rush", "turtle", lastSwitchTick, 1450,
				recoveryEmergencyTransition, 7500, 1000, info))
				switches++;

			Assert.That(switches, Is.EqualTo(2));
		}

		[Test]
		public void PersonalityReactionDelayUsesThirtySecondTierSteps()
		{
			var info = new MasterAiBotModuleInfo();
			foreach (var delay in Enumerable.Range(0, 10).Select(i => 7500 - i * 750))
			{
				Assert.That(MasterAiBotModule.ShouldSwitchPersonality("rush", "turtle", 0, delay - 1,
					false, delay, 0, info), Is.False);
				Assert.That(MasterAiBotModule.ShouldSwitchPersonality("rush", "turtle", 0, delay,
					false, delay, 0, info), Is.True);
			}
		}

		[Test]
		public void RelativeInitialAttackDelayPreservesStartAndRemovesElapsedDelay()
		{
			Assert.That(SquadManagerBotModuleCA.RemainingInitialAttackDelay(12000, 0), Is.EqualTo(12000));
			Assert.That(SquadManagerBotModuleCA.RemainingInitialAttackDelay(12000, 12001), Is.Zero);
		}

		[Test]
		public void RegionMemoryBucketsCellsAndClampsOutOfMapPositions()
		{
			var regions = new RegionMemory(new CPos(0, 0), new CPos(63, 63), 8);
			Assert.That(regions.Columns, Is.EqualTo(8));
			Assert.That(regions.Rows, Is.EqualTo(8));
			Assert.That(regions.CellCount, Is.EqualTo(64));
			Assert.That(regions.IndexOf(new CPos(0, 0)), Is.EqualTo(0));
			Assert.That(regions.IndexOf(new CPos(7, 7)), Is.EqualTo(0));
			Assert.That(regions.IndexOf(new CPos(8, 0)), Is.EqualTo(1));
			Assert.That(regions.IndexOf(new CPos(0, 8)), Is.EqualTo(8));
			Assert.That(regions.IndexOf(new CPos(63, 63)), Is.EqualTo(63));
			Assert.That(regions.IndexOf(new CPos(-5, 200)), Is.EqualTo(56));
			Assert.That(regions.CenterOf(0), Is.EqualTo(new CPos(4, 4)));
			Assert.That(regions.CenterOf(63), Is.EqualTo(new CPos(60, 60)));
		}

		[Test]
		public void RegionMemoryCountsOnlyEverSeenRegions()
		{
			var cells = new RegionMemory.Region[4];
			Assert.That(RegionMemory.CountKnown(cells), Is.Zero);
			cells[1] = new RegionMemory.Region { EverSeen = true };
			cells[2] = new RegionMemory.Region { ArmyValue = 500 };
			Assert.That(RegionMemory.CountKnown(cells), Is.EqualTo(1));
		}

		[Test]
		public void RegionMemoryHandlesNonAlignedMapBounds()
		{
			var regions = new RegionMemory(new CPos(-10, -10), new CPos(17, 9), 8);
			Assert.That(regions.Columns, Is.EqualTo(4));
			Assert.That(regions.Rows, Is.EqualTo(3));
			Assert.That(regions.IndexOf(new CPos(-10, -10)), Is.EqualTo(0));
			Assert.That(regions.IndexOf(new CPos(-3, -3)), Is.EqualTo(0));
			Assert.That(regions.IndexOf(new CPos(-2, -10)), Is.EqualTo(1));
		}

		[Test]
		public void ScoutPicksStalestRegionAndSkipsTaken()
		{
			var regions = new RegionMemory(new CPos(0, 0), new CPos(63, 63), 8);
			var staleness = new Dictionary<int, int> { { 3, 5000 }, { 9, 9000 }, { 20, 2000 } };
			var taken = new HashSet<int> { 9 };

			var picked = ScoutBotModule.PickScoutRegion(regions, new CPos(0, 0), taken,
				i => staleness.GetValueOrDefault(i), i => 0, i => 0);
			Assert.That(picked, Is.EqualTo(3));

			taken.Clear();
			picked = ScoutBotModule.PickScoutRegion(regions, new CPos(0, 0), taken,
				i => staleness.GetValueOrDefault(i), i => 0, i => 0);
			Assert.That(picked, Is.EqualTo(9));
		}

		[Test]
		public void ScoutPrefersInterestingAndSafeRegions()
		{
			var regions = new RegionMemory(new CPos(0, 0), new CPos(63, 63), 8);
			var staleness = new Dictionary<int, int> { { 3, 5000 }, { 9, 5000 } };

			var picked = ScoutBotModule.PickScoutRegion(regions, new CPos(0, 0), new HashSet<int>(),
				i => staleness.GetValueOrDefault(i), i => i == 9 ? 4000 : 0, i => 0);
			Assert.That(picked, Is.EqualTo(9));

			picked = ScoutBotModule.PickScoutRegion(regions, new CPos(0, 0), new HashSet<int>(),
				i => staleness.GetValueOrDefault(i), i => 0, i => i == 9 ? int.MaxValue : 0);
			Assert.That(picked, Is.EqualTo(3));
		}

		[Test]
		public void ScoutIgnoresFullyExploredRegions()
		{
			var regions = new RegionMemory(new CPos(0, 0), new CPos(63, 63), 8);
			var picked = ScoutBotModule.PickScoutRegion(regions, new CPos(0, 0), new HashSet<int>(),
				i => 0, i => 0, i => 0);
			Assert.That(picked, Is.EqualTo(-1));
		}

		[Test]
		public void RiskGateNeverBlocksUnknownRegions()
		{
			// threat 0 = nothing remembered there; even an empty squad may commit
			// (fog-honest: no information is not a reason to hold).
			Assert.That(SquadManagerBotModuleCA.PassesRiskGate(0, 0, 25), Is.True);
			Assert.That(SquadManagerBotModuleCA.PassesRiskGate(500, 0, 25), Is.True);
		}

		[Test]
		public void RiskGateBlocksOvermatchedSquads()
		{
			// margin 25: attacker must beat threat by 1.25x.
			Assert.That(SquadManagerBotModuleCA.PassesRiskGate(1000, 800, 25), Is.True);   // exactly 1.25x
			Assert.That(SquadManagerBotModuleCA.PassesRiskGate(1249, 1000, 25), Is.False); // 1.249x < 1.25x
			Assert.That(SquadManagerBotModuleCA.PassesRiskGate(1250, 1000, 25), Is.True);
			Assert.That(SquadManagerBotModuleCA.PassesRiskGate(400, 1000, 25), Is.False);
		}

		[Test]
		public void RiskGateNegativeMarginDisables()
		{
			Assert.That(SquadManagerBotModuleCA.PassesRiskGate(1, 999999, -1), Is.True);
		}

		sealed class StubFogProvider : IBotFoggedEnemyProvider
		{
			public bool FoggedObservation { get; set; }
		}

		[Test]
		public void FoggedScansNeedAnEnabledProvider()
		{
			// No provider / disabled trait / disabled provider all leave the
			// legacy omniscient scan in place (6d degradation rule).
			Assert.That(SquadManagerBotModuleCA.FoggedScansActive(false, null), Is.False);
			Assert.That(SquadManagerBotModuleCA.FoggedScansActive(true, new IBotFoggedEnemyProvider[] { new StubFogProvider { FoggedObservation = true } }), Is.False);
			Assert.That(SquadManagerBotModuleCA.FoggedScansActive(false, new IBotFoggedEnemyProvider[] { new StubFogProvider { FoggedObservation = false } }), Is.False);
		}

		[Test]
		public void FoggedScansOnWhenAnyProviderReportsFog()
		{
			var providers = new IBotFoggedEnemyProvider[]
			{
				new StubFogProvider { FoggedObservation = false },
				new StubFogProvider { FoggedObservation = true },
			};
			Assert.That(SquadManagerBotModuleCA.FoggedScansActive(false, providers), Is.True);
		}

		[Test]
		public void MasterAiImplementsFoggedEnemyProvider()
		{
			Assert.That(typeof(IBotFoggedEnemyProvider).IsAssignableFrom(typeof(MasterAiBotModule)), Is.True);
		}

		static (RegionMemory Regions, OpenRA.Player Enemy) MissionRegions(params (int Index, int Army, int Defence, int Economy)[] values)
		{
			var regions = new RegionMemory(new CPos(0, 0), new CPos(23, 23), 8);
			var cells = new RegionMemory.Region[regions.CellCount];
			foreach (var value in values)
				cells[value.Index] = new RegionMemory.Region
				{
					ArmyValue = value.Army,
					DefenceValue = value.Defence,
					EconomyValue = value.Economy,
					EverSeen = true
				};
			var enemy = (OpenRA.Player)RuntimeHelpers.GetUninitializedObject(typeof(OpenRA.Player));
			regions.SetRegions(enemy, cells);
			return (regions, enemy);
		}

		[Test]
		public void MissionsUseRaidPriorityAndRequiredValueArithmetic()
		{
			var setup = MissionRegions((0, 0, 0, 100), (1, 50, 50, 100));
			var missions = MasterAiBotModule.DeriveMissions(setup.Regions, new[] { setup.Enemy }, 8, 100,
				new MasterAiBotModuleInfo());

			Assert.That(missions.Select(m => m.RegionIndex), Is.EqualTo(new[] { 0, 1 }));
			Assert.That(missions[0].Priority, Is.EqualTo(99));
			Assert.That(missions[0].RequiredValue, Is.Zero);
			Assert.That(missions[1].Priority, Is.EqualTo(49));
			Assert.That(missions[1].RequiredValue, Is.EqualTo(120));
		}

		[Test]
		public void DefendMissionUsesNineRegionThreatAndThreshold()
		{
			var setup = MissionRegions((4, 100, 0, 0));
			var noDefend = MasterAiBotModule.DeriveMissions(setup.Regions, new[] { setup.Enemy }, 4, 100,
				new MasterAiBotModuleInfo());
			Assert.That(noDefend, Is.Empty);

			var defend = MasterAiBotModule.DeriveMissions(setup.Regions, new[] { setup.Enemy }, 4, 0,
				new MasterAiBotModuleInfo());
			Assert.That(defend, Has.Count.EqualTo(1));
			Assert.That(defend[0].Type, Is.EqualTo(BotMissionType.Defend));
			Assert.That(defend[0].Priority, Is.EqualTo(99));
			Assert.That(defend[0].RequiredValue, Is.Zero);
		}

		[Test]
		public void NeighbourDefenceDoesNotPublishDefend()
		{
			var setup = MissionRegions((3, 0, 100, 0));
			var missions = MasterAiBotModule.DeriveMissions(setup.Regions, new[] { setup.Enemy }, 4, 0,
				new MasterAiBotModuleInfo());

			Assert.That(missions, Is.Empty);
		}

		[Test]
		public void BaseRegionDefencePublishesDefend()
		{
			var setup = MissionRegions((4, 0, 100, 0));
			var missions = MasterAiBotModule.DeriveMissions(setup.Regions, new[] { setup.Enemy }, 4, 0,
				new MasterAiBotModuleInfo());

			Assert.That(missions, Has.Count.EqualTo(1));
			Assert.That(missions[0].Type, Is.EqualTo(BotMissionType.Defend));
		}

		[Test]
		public void EqualMissionPrioritiesOrderDefendThenRegion()
		{
			var setup = MissionRegions((0, 49, 0, 50), (4, 0, 0, 0), (8, 49, 0, 50));
			var missions = MasterAiBotModule.DeriveMissions(setup.Regions, new[] { setup.Enemy }, 4, 48,
				new MasterAiBotModuleInfo());

			Assert.That(missions.Select(m => (m.Type, m.RegionIndex)), Is.EqualTo(new[]
			{
				(BotMissionType.Defend, 4),
				(BotMissionType.Raid, 0),
				(BotMissionType.Raid, 8)
			}));
		}

		[Test]
		public void MissionReservationExpiresAfterConfiguredTicks()
		{
			Assert.That(MasterAiBotModule.ReservationActive(100, 100, 1500), Is.True);
			Assert.That(MasterAiBotModule.ReservationActive(100, 1600, 1500), Is.True);
			Assert.That(MasterAiBotModule.ReservationActive(100, 1601, 1500), Is.False);
		}

		sealed class StubMissionProvider : IBotMissionProvider
		{
			public IReadOnlyList<BotMission> Missions { get; set; } = Array.Empty<BotMission>();
			public void MissionTaken(BotMission mission) { }
		}

		[Test]
		public void BestAffordableMissionUsesProviderAndPublishedOrder()
		{
			var first = new BotMission { RequiredValue = 500, RegionIndex = 1 };
			var second = new BotMission { RequiredValue = 100, RegionIndex = 2 };
			var third = new BotMission { RequiredValue = 50, RegionIndex = 3 };
			var providers = new[]
			{
				new StubMissionProvider { Missions = new[] { first, second } },
				new StubMissionProvider { Missions = new[] { third } }
			};

			Assert.That(SquadManagerBotModuleCA.BestAffordableMission(providers, 100), Is.SameAs(second));
			Assert.That(SquadManagerBotModuleCA.BestAffordableMission(providers, 25), Is.Null);
		}

		[Test]
		public void BestAffordableMissionSkipsAllExhaustedDefends()
		{
			var firstDefend = new BotMission
			{
				Type = BotMissionType.Defend,
				RegionIndex = 4,
				Priority = 90
			};
			var secondDefend = new BotMission
			{
				Type = BotMissionType.Defend,
				RegionIndex = 5,
				Priority = 80
			};
			var raid = new BotMission
			{
				Type = BotMissionType.Raid,
				RegionIndex = 8,
				RequiredValue = 100,
				Priority = 60
			};
			var provider = new StubMissionProvider { Missions = new[] { firstDefend, secondDefend, raid } };

			Assert.That(
				SquadManagerBotModuleCA.BestAffordableMission(
					new[] { provider },
					100,
					m => m.Type == BotMissionType.Defend &&
						(firstDefend.RegionIndex == m.RegionIndex || secondDefend.RegionIndex == m.RegionIndex)),
				Is.SameAs(raid));
		}

		[Test]
		public void BestAffordableMissionSkipsExcludedMissions()
		{
			var defend = new BotMission { Type = BotMissionType.Defend, RequiredValue = 0, RegionIndex = 4 };
			var raid = new BotMission { Type = BotMissionType.Raid, RequiredValue = 0, RegionIndex = 8 };
			var providers = new[]
			{
				new StubMissionProvider { Missions = new[] { defend, raid } }
			};

			Assert.That(SquadManagerBotModuleCA.BestAffordableMission(providers, 0), Is.SameAs(defend));
			Assert.That(
				SquadManagerBotModuleCA.BestAffordableMission(providers, 0,
					m => m.Type == BotMissionType.Defend && m.RegionIndex == 4),
				Is.SameAs(raid));
			Assert.That(
				SquadManagerBotModuleCA.BestAffordableMission(providers, 0, m => m.Type == BotMissionType.Defend),
				Is.SameAs(raid));
			Assert.That(
				SquadManagerBotModuleCA.BestAffordableMission(providers, 0, m => true),
				Is.Null);
		}

		[Test]
		public void MissionIdentityKeyIsStableAcrossRederivedInstances()
		{
			// The same strategic mission re-published by a later DeriveMissions
			// pass must carry the same key, or attempt lineage fractures.
			var first = new BotMission { Type = BotMissionType.Raid, RegionIndex = 8 };
			var second = new BotMission { Type = BotMissionType.Raid, RegionIndex = 8, Priority = 99, RequiredValue = 4000 };
			Assert.That(second.IdentityKey, Is.EqualTo(first.IdentityKey));
			Assert.That(second.IdentityKey, Does.StartWith("raid:").And.EndsWith(":r8"));
		}

		[Test]
		public void MissionIdentityKeySeparatesDistinctMissions()
		{
			var raid8 = new BotMission { Type = BotMissionType.Raid, RegionIndex = 8 };
			var raid9 = new BotMission { Type = BotMissionType.Raid, RegionIndex = 9 };
			var defend8 = new BotMission { Type = BotMissionType.Defend, RegionIndex = 8 };
			Assert.That(raid9.IdentityKey, Is.Not.EqualTo(raid8.IdentityKey));
			Assert.That(defend8.IdentityKey, Is.Not.EqualTo(raid8.IdentityKey));
		}

		[Test]
		public void EffectiveMissionIdPrefersOwnerAllocation()
		{
			// Until the owner allocates (MC1), consumers key on IdentityKey; once
			// allocated, the owner id wins so cards and logs share one id space.
			var mission = new BotMission { Type = BotMissionType.Raid, RegionIndex = 8 };
			Assert.That(mission.EffectiveMissionId, Is.EqualTo(mission.IdentityKey));
			mission.MissionId = "owner:m42";
			Assert.That(mission.EffectiveMissionId, Is.EqualTo("owner:m42"));
		}

		[Test]
		public void AttemptVerdictBooksLossHandOffAndSuccessApart()
		{
			// died + empty = the only Failed; empty without a death = a hand-off (Released/reserved).
			Assert.That(SquadManagerBotModuleCA.AttemptVerdict(false, false, false, true, true),
				Is.EqualTo((BotMissionAttemptState.Failed, BotMissionReasons.LostUnits)));
			Assert.That(SquadManagerBotModuleCA.AttemptVerdict(false, false, false, true, false),
				Is.EqualTo((BotMissionAttemptState.Released, BotMissionReasons.Reserved)));
			Assert.That(SquadManagerBotModuleCA.AttemptVerdict(true, false, false, false, false),
				Is.EqualTo((BotMissionAttemptState.Success, BotMissionReasons.Done)));
			Assert.That(SquadManagerBotModuleCA.AttemptVerdict(false, true, false, false, false),
				Is.EqualTo((BotMissionAttemptState.Success, BotMissionReasons.Done)));
			Assert.That(SquadManagerBotModuleCA.AttemptVerdict(false, false, true, false, false),
				Is.EqualTo((BotMissionAttemptState.Released, BotMissionReasons.Superseded)));
			Assert.That(SquadManagerBotModuleCA.AttemptVerdict(false, false, false, false, false), Is.Null);
		}

		[Test]
		public void DormantShelfStreakGoesDormantAtThresholdAndZeroIsOff()
		{
			Assert.That(MasterAiBotModule.GoesDormant(5, 0), Is.False);
			Assert.That(MasterAiBotModule.GoesDormant(1, 2), Is.False);
			Assert.That(MasterAiBotModule.GoesDormant(2, 2), Is.True);
		}

		[Test]
		public void DormantShelfFailAddsSuccessClearsReleaseLeavesStreak()
		{
			var streak = MasterAiBotModule.NextFailStreak(0, BotMissionAttemptState.Failed);
			streak = MasterAiBotModule.NextFailStreak(streak, BotMissionAttemptState.Failed);
			Assert.That(streak, Is.EqualTo(2));
			Assert.That(MasterAiBotModule.NextFailStreak(streak, BotMissionAttemptState.Released), Is.EqualTo(2));
			Assert.That(MasterAiBotModule.NextFailStreak(streak, BotMissionAttemptState.Committed), Is.EqualTo(2));
			Assert.That(MasterAiBotModule.NextFailStreak(streak, BotMissionAttemptState.Success), Is.EqualTo(0));
		}

		[Test]
		public void DormantShelfFilterHidesOnlyUntilExpiry()
		{
			var mission = new BotMission { Type = BotMissionType.Raid, RegionIndex = 8 };
			var other = new BotMission { Type = BotMissionType.Raid, RegionIndex = 9 };
			var shelf = new Dictionary<string, int>(StringComparer.Ordinal) { [mission.EffectiveMissionId] = 5000 };
			Assert.That(MasterAiBotModule.IsDormant(shelf, mission.EffectiveMissionId, 4999), Is.True);
			Assert.That(MasterAiBotModule.IsDormant(shelf, mission.EffectiveMissionId, 5000), Is.False);
			Assert.That(MasterAiBotModule.IsDormant(shelf, other.EffectiveMissionId, 100), Is.False);
			Assert.That(MasterAiBotModule.IsDormant(new Dictionary<string, int>(), mission.EffectiveMissionId, 100), Is.False);
		}

		// TC-2d (AI_ARCHITECTURE.md 12.17): role split — allied bots spread the
		// TechRush<->Expansion rest by participant-key rank (InternalName: map-side
		// bots share the host ClientIndex, audit 4.4). Static per team, so the
		// precedence converges by construction and cannot oscillate.
		[Test]
		public void RoleRankCountsLowerParticipantKeys()
		{
			Assert.That(MasterAiBotModule.TeamRoleRank("Multi2", new[] { "Multi0", "Multi1", "Multi3" }), Is.EqualTo(2));
			Assert.That(MasterAiBotModule.TeamRoleRank("Multi0", new[] { "Multi1", "Multi2" }), Is.EqualTo(0),
				"the lowest key on the team is rank 0 — it takes the Expansion pole");
			Assert.That(MasterAiBotModule.TeamRoleRank("Multi3", System.Array.Empty<string>()), Is.EqualTo(0),
				"no allied bots — a 1v1 or a solo team — is rank 0 of a team of one");
			Assert.That(MasterAiBotModule.TeamRoleRank("Multi1", new[] { "Multi1" }), Is.EqualTo(0),
				"a same-key broadcast is never below the caller — strictly-lower holds");
		}

		[Test]
		public void RoleSplitBiasSpreadsTheTeamEndpoints()
		{
			Assert.That(MasterAiBotModule.RoleSplitBias(0, 1, 20), Is.EqualTo(0),
				"a lone bot splits nothing");
			Assert.That(MasterAiBotModule.RoleSplitBias(0, 2, 20), Is.EqualTo(20),
				"two-bot team: lowest index biases full Expansion");
			Assert.That(MasterAiBotModule.RoleSplitBias(1, 2, 20), Is.EqualTo(-20),
				"and its ally full TechRush");
			Assert.That(MasterAiBotModule.RoleSplitBias(1, 3, 20), Is.EqualTo(0),
				"three-bot team: the middle rank stays on its authored rest");
			Assert.That(MasterAiBotModule.RoleSplitBias(2, 3, 20), Is.EqualTo(-20));
		}
	}
}
