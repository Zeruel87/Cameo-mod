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
using System.Collections.Generic;
using System.Linq;
using System.Text;
using OpenRA.Graphics;
using OpenRA.Mods.Cameo.Traits.BotModules;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.World)]
	[Desc("Appends record-only AI situation snapshots for bot players.")]
	public class AiSituationLogWriterInfo : TraitInfo
	{
		public readonly string FileName = "cameo-ai-situations.jsonl";

		public override object Create(ActorInitializer init) { return new AiSituationLogWriter(this); }
	}

	public class AiSituationLogWriter : IWorldLoaded, IGameOver, ITick
	{
		readonly AiSituationLogWriterInfo info;
		string fallbackGameUid;
		string pendingText;
		AiLogFileAppender appender;
		bool written;
		bool eligibleAtWorldLoad;
		int nextAttemptTick;

		public AiSituationLogWriter(AiSituationLogWriterInfo info) { this.info = info; }

		void IWorldLoaded.WorldLoaded(World world, WorldRenderer worldRenderer)
		{
			eligibleAtWorldLoad = Eligible(world.Type, world.IsReplay, world.IsLoadingGameSave, Game.IsHost);
			if (!eligibleAtWorldLoad)
			{
				written = true;
				return;
			}

			fallbackGameUid = Guid.NewGuid().ToString("N");
			appender = new AiLogFileAppender(info.FileName);
		}

		void ITick.Tick(Actor self)
		{
			var world = self.World;
			if (written || world.WorldTick < nextAttemptTick)
				return;
			if (pendingText != null)
			{
				TryAppend(world.WorldTick);
				return;
			}
			if (AllBotsResolved(world))
				CaptureAndAppend(world);
		}

		void IGameOver.GameOver(World world)
		{
			// World.EndGame pauses before dispatching IGameOver, and paused worlds do not advance ticks.
			// A retry scheduled here may therefore never run; retries matter for live all-bots-resolved capture.
			CaptureAndAppend(world);
		}

		void CaptureAndAppend(World world)
		{
			if (written)
				return;
			if (!eligibleAtWorldLoad || world.Type != WorldType.Regular || world.IsReplay || !Game.IsHost)
			{
				written = true;
				return;
			}

			pendingText ??= BuildLog(world);
			if (string.IsNullOrEmpty(pendingText))
			{
				written = true;
				return;
			}
			TryAppend(world.WorldTick);
		}

		internal static bool Eligible(WorldType type, bool replay, bool loadingSave, bool host)
		{
			return AiMatchLogWriter.Eligible(type, replay, loadingSave, host);
		}

		void TryAppend(int worldTick)
		{
			var result = appender.TryAppend(pendingText, worldTick, out nextAttemptTick);
			if (result != AiLogAppendResult.RetryableFailure || appender.IsTerminal)
			{
				written = true;
				return;
			}
		}

		static bool AllBotsResolved(World world)
		{
			return world.Players.Where(AiMatchLogWriter.IsLoggableBot)
				.All(p => p.WinState != WinState.Undefined);
		}

		string BuildLog(World world)
		{
			var gameUid = world.LobbyInfo.GlobalSettings.GameUid;
			if (string.IsNullOrEmpty(gameUid))
				gameUid = fallbackGameUid;
			var lines = new StringBuilder();
			foreach (var player in world.Players.Where(AiMatchLogWriter.IsLoggableBot)
				.OrderBy(p => p.InternalName, StringComparer.Ordinal))
			{
				var module = player.PlayerActor.TraitsImplementing<MasterAiBotModule>().FirstOrDefault();
				if (module == null)
					continue;
				foreach (var situation in module.PendingSituations)
					AppendSituation(lines, gameUid, world.LobbyInfo.GlobalSettings.GameUid ?? "", world.Map.Uid,
						player.InternalName, player.Faction.InternalName, player.BotType ?? "",
						situation.OwnPersonality, situation);
			}
			return lines.ToString();
		}

		// DF step 1: per tracked enemy group its centre, value, velocity (cells per 1000 ticks) and, if moving, the
		// own asset it heads for with the ETA in ticks. `target` is empty for a standing group.
		internal static void AppendThreats(StringBuilder builder,
			IReadOnlyList<(BotThreatTracker.Group Group, BotThreatTracker.Prediction? Prediction)> threats)
		{
			AiMatchLogWriter.AppendArrayPropertyStart(builder, "threats");
			for (var i = 0; threats != null && i < threats.Count; i++)
			{
				if (i > 0)
					builder.Append(',');
				var (g, p) = threats[i];
				AiMatchLogWriter.AppendObjectStart(builder);
				AiMatchLogWriter.AppendNumber(builder, "value", g.Value, true);
				AiMatchLogWriter.AppendNumber(builder, "count", g.Count);
				AiMatchLogWriter.AppendNumber(builder, "x", (int)Math.Round(g.X));
				AiMatchLogWriter.AppendNumber(builder, "y", (int)Math.Round(g.Y));
				AiMatchLogWriter.AppendNumber(builder, "vx_per_kilotick", (int)Math.Round(g.VelocityX * 1000));
				AiMatchLogWriter.AppendNumber(builder, "vy_per_kilotick", (int)Math.Round(g.VelocityY * 1000));
				AiMatchLogWriter.AppendString(builder, "target", p.HasValue ? $"{p.Value.Target.X},{p.Value.Target.Y}" : "");
				AiMatchLogWriter.AppendNumber(builder, "target_value", p?.TargetValue ?? 0);
				AiMatchLogWriter.AppendNumber(builder, "eta", p?.EtaTicks ?? 0);
				builder.Append('}');
			}

			builder.Append(']');
		}

		// ST (DESIGN 19.10): the growth law's inputs and per-category seen/target pairs; omitted while no provider runs.
		internal static void AppendScaleTargets(StringBuilder builder, ScaleTargetsSnapshot snapshot)
		{
			if (snapshot == null)
				return;

			AiMatchLogWriter.AppendObjectPropertyStart(builder, "scale_targets");
			AiMatchLogWriter.AppendNumber(builder, "tick", snapshot.Tick, true);
			AiMatchLogWriter.AppendNumber(builder, "tier", snapshot.Tier);
			AiMatchLogWriter.AppendString(builder, "personality", snapshot.Personality ?? "");
			AiMatchLogWriter.AppendNumber(builder, "team_size", snapshot.TeamSize);
			AiMatchLogWriter.AppendNumber(builder, "unscouted_milli", snapshot.UnscoutedMilli);
			AiMatchLogWriter.AppendNumber(builder, "game_minutes_milli", snapshot.GameMinutesMilli);
			AiMatchLogWriter.AppendNumber(builder, "army_baseline", snapshot.ArmyBaseline);
			for (var i = 0; i < snapshot.Categories.Length; i++)
			{
				AiMatchLogWriter.AppendNumber(builder, "seen_" + snapshot.Categories[i], snapshot.Seen[i]);
				AiMatchLogWriter.AppendNumber(builder, "target_" + snapshot.Categories[i], snapshot.Targets[i]);
			}

			builder.Append('}');
		}

		// BO-1 (AI_ARCHITECTURE 12.25): the build-order knob vector (base = preset x learned x jitter, now = after react), the opening and the
		// react events, so the report and tuner can group matches by them; omitted while no provider runs.
		internal static void AppendBuildOrder(StringBuilder builder, BuildOrderSnapshot snapshot)
		{
			if (snapshot == null)
				return;

			AiMatchLogWriter.AppendObjectPropertyStart(builder, "build_order");
			AiMatchLogWriter.AppendNumber(builder, "tick", snapshot.Tick, true);
			AiMatchLogWriter.AppendString(builder, "personality", snapshot.Personality ?? "");
			AiMatchLogWriter.AppendString(builder, "faction", snapshot.Faction ?? "");
			AiMatchLogWriter.AppendString(builder, "enemy_faction", snapshot.EnemyFaction ?? "");
			AiMatchLogWriter.AppendString(builder, "opening", snapshot.Opening ?? "");
			AiMatchLogWriter.AppendString(builder, "opening_end", snapshot.OpeningEnd ?? "");
			AiMatchLogWriter.AppendNumber(builder, "opening_step", snapshot.OpeningStep);
			AiMatchLogWriter.AppendNumber(builder, "opening_steps", snapshot.OpeningSteps);
			AiMatchLogWriter.AppendNumber(builder, "reactions", snapshot.Reactions);
			AiMatchLogWriter.AppendString(builder, "events", snapshot.Events ?? "");
			for (var i = 0; i < snapshot.KnobNames.Length; i++)
			{
				AiMatchLogWriter.AppendNumber(builder, "base_" + snapshot.KnobNames[i], snapshot.Base[i]);
				AiMatchLogWriter.AppendNumber(builder, "now_" + snapshot.KnobNames[i], snapshot.Now[i]);
			}
			builder.Append('}');
		}

		// FE-0 (12.24): the field-economy picture of one snapshot; omitted when none was captured.
		internal static void AppendExpansion(StringBuilder builder, ExpansionSnapshot e)
		{
			if (e == null)
				return;

			AiMatchLogWriter.AppendObjectPropertyStart(builder, "expansion");
			AiMatchLogWriter.AppendNumber(builder, "fields_known", e.FieldsKnown, true);
			AiMatchLogWriter.AppendNumber(builder, "fields_in_reach", e.FieldsInReach);
			AiMatchLogWriter.AppendNumber(builder, "fields_served", e.FieldsServed);
			AiMatchLogWriter.AppendNumber(builder, "fields_harvested", e.FieldsHarvested);
			AiMatchLogWriter.AppendNumber(builder, "anchors_spreader", e.AnchorsSpreader);
			AiMatchLogWriter.AppendNumber(builder, "anchors_field", e.AnchorsField);
			AiMatchLogWriter.AppendNumber(builder, "refineries", e.Refineries);
			AiMatchLogWriter.AppendNumber(builder, "excess_refineries", e.ExcessRefineries);
			AiMatchLogWriter.AppendNumber(builder, "unassigned_refineries", e.UnassignedRefineries);
			AiMatchLogWriter.AppendNumber(builder, "anchor_dist_mean", e.AnchorDistMean);
			AiMatchLogWriter.AppendNumber(builder, "anchor_dist_max", e.AnchorDistMax);
			AiMatchLogWriter.AppendNumber(builder, "conyards", e.Conyards);
			AiMatchLogWriter.AppendNumber(builder, "outposts", e.Outposts);
			AiMatchLogWriter.AppendString(builder, "crawl_target", e.CrawlTarget);
			AiMatchLogWriter.AppendString(builder, "mcv_site", e.McvSite);
			AiMatchLogWriter.AppendNumber(builder, "crawl_mcv_angle", e.CrawlMcvAngle);
			AiMatchLogWriter.AppendNumber(builder, "coverage_milli", e.CoverageMilli);
			builder.Append('}');
		}

		internal static void AppendRoleCosts(StringBuilder builder, string name, IReadOnlyDictionary<string, int> costs)
		{
			AiMatchLogWriter.AppendObjectPropertyStart(builder, name);
			var first = true;
			if (costs != null)
				foreach (var (role, cost) in costs.OrderBy(c => c.Key, StringComparer.Ordinal))
				{
					AiMatchLogWriter.AppendNumber(builder, role, cost, first);
					first = false;
				}

			builder.Append('}');
		}

		internal static void AppendSituation(StringBuilder builder, string gameUid, string worldGameUid,
			string mapUid, string playerName, string faction, string botType, string currentPersonality,
			BotSituation situation)
		{
			AiMatchLogWriter.AppendObjectStart(builder);
			AiMatchLogWriter.AppendNumber(builder, "schema", 2, true);
			AiMatchLogWriter.AppendString(builder, "kind", "situation");
			AiMatchLogWriter.AppendString(builder, "record_id", gameUid + "|" + playerName + "|" + situation.Tick);
			AiMatchLogWriter.AppendString(builder, "game_uid", worldGameUid);
			AiMatchLogWriter.AppendString(builder, "map_uid", mapUid);
			AiMatchLogWriter.AppendString(builder, "player", playerName);
			AiMatchLogWriter.AppendString(builder, "faction", faction);
			AiMatchLogWriter.AppendString(builder, "bot_type", botType);
			AiMatchLogWriter.AppendNumber(builder, "tick", situation.Tick);
			AiMatchLogWriter.AppendString(builder, "urgency", situation.Urgency.ToString().ToLowerInvariant());
			AiMatchLogWriter.AppendString(builder, "personality_current", currentPersonality);
			AiMatchLogWriter.AppendString(builder, "personality_candidate", situation.Personality ?? "");
			AiMatchLogWriter.AppendString(builder, "main_target", situation.MainTarget?.InternalName ?? "");
			AiMatchLogWriter.AppendNumber(builder, "main_target_score",
				situation.MainTarget != null && situation.Enemies.TryGetValue(situation.MainTarget, out var target) ? target.Score : 0);
			if (situation.Mission == null)
				builder.Append(",\"mission\":null");
			else
			{
				builder.Append(",\"mission\":{\"type\":\"")
					.Append(situation.Mission.Type.ToString().ToLowerInvariant())
					.Append("\",\"priority\":")
					.Append(situation.Mission.Priority)
					.Append(",\"region_index\":")
					.Append(situation.Mission.RegionIndex)
					.Append('}');
			}
			if (situation.MissionAssignment == null)
				builder.Append(",\"mission_assignment\":null");
			else
			{
				builder.Append(",\"mission_assignment\":{\"type\":\"")
					.Append(situation.MissionAssignment.Type.ToString().ToLowerInvariant())
					.Append("\",\"region_index\":")
					.Append(situation.MissionAssignment.RegionIndex)
					.Append(",\"frozen\":")
					.Append(situation.MissionAssignment.Frozen ? "true" : "false")
					.Append('}');
			}

			AiMatchLogWriter.AppendObjectPropertyStart(builder, "hints");
			AiMatchLogWriter.AppendNumber(builder, "defence_fraction", situation.DefenceFractionHint, true);
			AiMatchLogWriter.AppendNumber(builder, "expansion_appetite", situation.ExpansionAppetiteHint);
			builder.Append('}');
			AiMatchLogWriter.AppendObjectPropertyStart(builder, "demand");
			AiMatchLogWriter.AppendNumber(builder, "anti_air", situation.Demand.AntiAir, true);
			AiMatchLogWriter.AppendNumber(builder, "anti_armour", situation.Demand.AntiArmour);
			AiMatchLogWriter.AppendNumber(builder, "anti_infantry", situation.Demand.AntiInfantry);
			AiMatchLogWriter.AppendNumber(builder, "detector", situation.Demand.Detector);
			AiMatchLogWriter.AppendNumber(builder, "artillery", situation.Demand.Artillery);
			builder.Append('}');

			AiMatchLogWriter.AppendObjectPropertyStart(builder, "own");
			AiMatchLogWriter.AppendNumber(builder, "army_value", situation.OwnArmyValue, true);
			AiMatchLogWriter.AppendNumber(builder, "defence_value", situation.OwnDefenceValue);
			AiMatchLogWriter.AppendNumber(builder, "buildings", situation.OwnBuildings);
			AiMatchLogWriter.AppendNumber(builder, "harvesters", situation.OwnHarvesters);
			AiMatchLogWriter.AppendNumber(builder, "kills_cost_window", situation.OwnKillsCostWindow);
			AiMatchLogWriter.AppendNumber(builder, "deaths_cost_window", situation.OwnDeathsCostWindow);
			AiMatchLogWriter.AppendNumber(builder, "squad_count", situation.SquadCount);
			AiMatchLogWriter.AppendNumber(builder, "squad_units", situation.SquadUnitCount);
			AppendRoleCosts(builder, "losses_by_role", situation.LossesByRole);
			AppendRoleCosts(builder, "away_losses_by_role", situation.AwayLossesByRole);
			AiMatchLogWriter.AppendNumber(builder, "combat_ratio_pct", situation.CombatRatioPct);
			AiMatchLogWriter.AppendNumber(builder, "combat_ratio_defended_pct", situation.CombatRatioDefendedPct);

			// §12.14 PL telemetry (record-only).
			AiMatchLogWriter.AppendNumber(builder, "production_window", situation.ProductionValueWindow);
			AiMatchLogWriter.AppendNumber(builder, "production_per_game_min", situation.ProductionPerGameMin);
			AiMatchLogWriter.AppendNumber(builder, "econ_destroyed_window", situation.EnemyEconValueDestroyedWindow);
			AiMatchLogWriter.AppendNumber(builder, "econ_destroyed", situation.EnemyEconValueDestroyedTotal);
			AiMatchLogWriter.AppendNumber(builder, "attacks_launched", situation.AttacksLaunched);
			AiMatchLogWriter.AppendNumber(builder, "first_attack_tick", situation.FirstAttackTick);
			AiMatchLogWriter.AppendNumber(builder, "attacks_per_game_min", situation.AttacksPerGameMin);
			AiMatchLogWriter.AppendNumber(builder, "regions_fresh", situation.RegionsFresh);
			AiMatchLogWriter.AppendNumber(builder, "regions_total", situation.RegionsTotal);
			AiMatchLogWriter.AppendNumber(builder, "regions_enemy_presence", situation.RegionsEnemyPresence);
			AiMatchLogWriter.AppendNumber(builder, "guerrilla_lead", situation.GuerrillaLead);

			// §12.14 PL-1 leads (record-only; UsePersonalityLeads gates only the consumers).
			AiMatchLogWriter.AppendNumber(builder, "enemy_production_per_game_min", situation.EnemyProductionPerGameMin);
			AiMatchLogWriter.AppendNumber(builder, "steamroller_lead", situation.SteamrollerLead);
			AiMatchLogWriter.AppendNumber(builder, "rush_lead", situation.RushLead);

			// §13.1 discipline telemetry (record-only): the "never do" counters — banked
			// cash at snapshot, brownout ticks, per-queue idle production ticks.
			AiMatchLogWriter.AppendNumber(builder, "banked_cash", situation.BankedCash);
			AiMatchLogWriter.AppendNumber(builder, "brownout_ticks", situation.BrownoutTicks);
			AiMatchLogWriter.AppendNumber(builder, "idle_production_ticks", situation.IdleProductionTicks);
			AiMatchLogWriter.AppendNumber(builder, "production_queues", situation.ProductionQueues);

			// RV1 repair-owner telemetry (cumulative).
			AiMatchLogWriter.AppendNumber(builder, "repair_orders", situation.RepairOrders);
			AiMatchLogWriter.AppendNumber(builder, "repair_sweep_orders", situation.RepairSweepOrders);
			AiMatchLogWriter.AppendNumber(builder, "repair_toggles_avoided", situation.RepairTogglesAvoided);

			// UT-1 (AI_DEEP_RESEARCH.md §5.1): the bipolar posture axes, each [0,100]
			// with 100 the second pole — record-only, explainable against the inputs above.
			AiMatchLogWriter.AppendNumber(builder, "utility_turtlerush", situation.UtilityTurtleRush);
			AiMatchLogWriter.AppendNumber(builder, "utility_techrushexpansion", situation.UtilityTechRushExpansion);
			AiMatchLogWriter.AppendNumber(builder, "utility_steamrollerguerrilla", situation.UtilitySteamrollerGuerrilla);
			// DI-1 (AI_ARCHITECTURE §12.16): the pacing Director's wave — record-only,
			// pacing/aggression telemetry; no consumer yet (DI-2).
			AiMatchLogWriter.AppendNumber(builder, "director_tension", situation.DirectorTension);
			AiMatchLogWriter.AppendString(builder, "director_phase", situation.DirectorPhase.ToString().ToLowerInvariant());

			// TC-1 (AI_ARCHITECTURE §12.17): the team blackboard summary — allied bots
			// only (the own broadcast is never folded in), publish-always; a 1v1 or a
			// team without an allied bot provider reads all zeros.
			AiMatchLogWriter.AppendNumber(builder, "team_allied_bots", situation.TeamAlliedBots);
			AiMatchLogWriter.AppendNumber(builder, "team_army_value", situation.TeamArmyValue);
			AiMatchLogWriter.AppendNumber(builder, "team_max_tension", situation.TeamMaxTension);
			AiMatchLogWriter.AppendNumber(builder, "team_defend_requests", situation.TeamDefendRequests);
			AiMatchLogWriter.AppendNumber(builder, "team_shared_target", situation.TeamSharedTarget);
			AiMatchLogWriter.AppendNumber(builder, "team_any_climax", situation.TeamAnyClimax);
			AiMatchLogWriter.AppendNumber(builder, "coalition_phase", situation.CoalitionPhase);
			AiMatchLogWriter.AppendString(builder, "coalition_main_target", situation.CoalitionMainTarget);
			AppendThreats(builder, situation.Threats);
			AppendScaleTargets(builder, situation.ScaleTargets);
			AppendBuildOrder(builder, situation.BuildOrder);
			builder.Append('}');
			AppendExpansion(builder, situation.Expansion);

			AiMatchLogWriter.AppendArrayPropertyStart(builder, "enemies");
			var enemies = situation.Enemies.Values.OrderBy(e => e.Name ?? "", StringComparer.Ordinal).ToArray();
			for (var i = 0; i < enemies.Length; i++)
			{
				if (i > 0)
					builder.Append(',');
				var enemy = enemies[i];
				AiMatchLogWriter.AppendObjectStart(builder);
				AiMatchLogWriter.AppendString(builder, "name", enemy.Name ?? "", true);
				AiMatchLogWriter.AppendString(builder, "faction", enemy.FactionName ?? "");
				AiMatchLogWriter.AppendBoolean(builder, "alive", enemy.Alive);
				AiMatchLogWriter.AppendNumber(builder, "army_value", enemy.ArmyValue);
				AiMatchLogWriter.AppendNumber(builder, "infantry_value", enemy.InfantryValue);
				AiMatchLogWriter.AppendNumber(builder, "vehicle_value", enemy.VehicleValue);
				AiMatchLogWriter.AppendNumber(builder, "air_value", enemy.AirValue);
				AiMatchLogWriter.AppendNumber(builder, "naval_value", enemy.NavalValue);
				AiMatchLogWriter.AppendNumber(builder, "defence_count", enemy.DefenceCount);
				AiMatchLogWriter.AppendNumber(builder, "defence_value", enemy.DefenceValue);
				AiMatchLogWriter.AppendNumber(builder, "tech_buildings", enemy.TechBuildings);
				AiMatchLogWriter.AppendNumber(builder, "production_buildings", enemy.ProductionBuildings);
				AiMatchLogWriter.AppendNumber(builder, "buildings", enemy.BuildingCount);
				AiMatchLogWriter.AppendNumber(builder, "expansion_clusters", enemy.ExpansionClusters);
				AiMatchLogWriter.AppendNumber(builder, "harvesters", enemy.Harvesters);
				AiMatchLogWriter.AppendNumber(builder, "harvester_count", enemy.HarvesterCount);
				AiMatchLogWriter.AppendNumber(builder, "known_regions", enemy.KnownRegions);
				AiMatchLogWriter.AppendNumber(builder, "refineries", enemy.Refineries);
				AiMatchLogWriter.AppendNumber(builder, "pressure_value", enemy.PressureValue);
				AiMatchLogWriter.AppendNumber(builder, "stealth_share", enemy.StealthShare);
				AiMatchLogWriter.AppendNumber(builder, "nearest_cells", enemy.NearestCells);
				AiMatchLogWriter.AppendNumber(builder, "last_seen_tick", enemy.LastSeenTick);
				AiMatchLogWriter.AppendNumber(builder, "score", enemy.Score);
				AiMatchLogWriter.AppendNumber(builder, "army_value_delta", enemy.ArmyValueDelta);
				builder.Append('}');
			}
			builder.Append("]}\n");
		}
	}
}
