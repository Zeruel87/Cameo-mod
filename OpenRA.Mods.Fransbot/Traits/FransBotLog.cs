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

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;

[assembly: AssemblyMetadata("FransbotBuildId", OpenRA.Mods.Common.Traits.FransBotLog.BuildId)]

namespace OpenRA.Mods.Common.Traits
{
	/// <summary>
	/// Fransbot logging bridge, replay build fingerprint and low-overhead diagnostic profiler.
	/// PERF diagnostics never inspect hidden information, never issue orders and only write to debug.log.
	/// </summary>
	public static class FransBotLog
	{
		public const string PackageVersion = "V1.29.48";
		public const string BasePackageVersion = "V1.29.47";
		public const string BuildId = "FB-1.29.48-211D3D16F2BF";
		public const string SourceFingerprint = "FransAirCommanderBotModule.cs=2B55FE560E9B;FransBaseBuilderBotModule.cs=31046C08645E;FransCombatIntelBotModule.cs=AFC796BC0D6E;FransCommandBidBotModule.cs=4FC9147C7437;FransCommanderCoreBotModule.cs=AAA9E2E3361D;FransDefenseCommanderBotModule.cs=3CE547EAABE0;FransEconomicSaturationBotModule.cs=D691F1E25785;FransGeneralBotModule.cs=1B6D83DC4575;FransGroundCommanderBotModule.cs=753AC9699729;FransGroundDefendForcePreservationGuard.cs=682FA494F825;FransGroundTransferBotModule.cs=DED97319453A;FransHarvesterBotModule.cs=FEA42B2A7A87;FransMcvExpansionManagerBotModule.cs=DA260CE420B1;FransMineClusterBotModule.cs=205CE05C1136;FransMinelayerBotModule.cs=E6829A2DC18B;FransRiskModelBotModule.cs=E58583E4E7E3;FransSeaCommanderBotModule.cs=F4DAA52DA3D3;FransSpecOpsCommanderBotModule.cs=D370BB8324F3;FransStrategicMapBotModule.cs=8F3428541228;FransSupplyTruckBotModule.cs=AB42C945CCDF;FransSupportCoordinatorBotModule.cs=DAB05F2ADA8D;FransSupportPowerBotModule.cs=6F310B0C773C;FransTransportCommanderBotModule.cs=348CEE906AEE;FransUnitBuilderBotModule.cs=435C109BE053;RoutineLandNegativeUnionPolicy.cs=CC0A31B7EA8E;fransbot-personalities.yaml=1512B5A93C36";

		const double ImmediateSpikeMilliseconds = 10.0;
		const double WorldTickGapMilliseconds = 60.0;
		const double CountAsSlowMilliseconds = 2.0;
		const int PerfSummaryIntervalWorldTicks = 250;
		const int PerfSummaryTopEntries = 12;

		sealed class PerfAggregate
		{
			public long Calls;
			public long TotalTimestampTicks;
			public long MaxTimestampTicks;
			public long SlowCalls;
		}

		sealed class WorldPerfState
		{
			public bool BuildLogged;
			public int LastHeartbeatWorldTick = -1;
			public long LastHeartbeatTimestamp;
			public int LastSummaryWorldTick = -1;
			public readonly Dictionary<string, PerfAggregate> Aggregates = [];
			public readonly Dictionary<string, string> Context = [];
		}

		public readonly struct PerfScope : IDisposable
		{
			readonly World world;
			readonly Player player;
			readonly string label;
			readonly long startTimestamp;

			internal PerfScope(World world, Player player, string label)
			{
				this.world = world;
				this.player = player;
				this.label = label;
				startTimestamp = Stopwatch.GetTimestamp();
			}

			public void Dispose()
			{
				if (world == null || label == null)
					return;

				RecordPerf(world, player, label, Stopwatch.GetTimestamp() - startTimestamp);
			}
		}

		// Match-scoped diagnostics must not keep completed World instances alive between games.
		static readonly ConditionalWeakTable<World, WorldPerfState> PerfStates = new();

		static WorldPerfState GetPerfState(World world) =>
			PerfStates.GetValue(world, _ => new WorldPerfState());

		static double TimestampTicksToMilliseconds(long ticks) =>
			ticks * 1000.0 / Stopwatch.Frequency;

		static string MatchInfoValue(string value) =>
			string.IsNullOrEmpty(value)
				? "unavailable"
				: value.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\r", "\\r").Replace("\n", "\\n");

		static void LogMatchInfo(World world)
		{
			try
			{
				var map = world.Map;
				OpenRA.Log.Write("debug",
					$"[MATCH INFO] Map=\"{MatchInfoValue(map.Title)}\" MapUID={MatchInfoValue(map.Uid)} " +
					$"Tileset={MatchInfoValue(map.Tileset)} Size={map.MapSize.Width}x{map.MapSize.Height} " +
					$"Package=\"{MatchInfoValue(map.Package?.Name)}\" BuildId={BuildId} Version={PackageVersion}");
			}
			catch
			{
				// Match metadata is diagnostic only and must not suppress existing build diagnostics.
			}
		}

		static void EnsureBuildFingerprintLogged(World world)
		{
			if (world == null)
				return;

			var state = GetPerfState(world);
			lock (state)
			{
				if (state.BuildLogged)
					return;
				state.BuildLogged = true;
			}

			LogMatchInfo(world);

			try
			{
				OpenRA.Log.Write("debug", $"[FRANS-BUILD][WT {world.WorldTick}] PACKAGE={PackageVersion} BASE={BasePackageVersion} ID={BuildId}");
				OpenRA.Log.Write("debug", $"[FRANS-BUILD-FILES][WT {world.WorldTick}] {SourceFingerprint};FransBotLog.cs=SELF-{PackageVersion}");
				OpenRA.Log.Write("debug",
					$"[FRANS-PERF-CONFIG][WT {world.WorldTick}] module spike >= {ImmediateSpikeMilliseconds:0.0} ms; world-tick wall gap >= {WorldTickGapMilliseconds:0.0} ms; aggregate window {PerfSummaryIntervalWorldTicks} WT. " +
					"Diagnostic wall-clock measurements only; no gameplay/order side effects.");
			}
			catch
			{
				// Diagnostics must never affect gameplay.
			}
		}

		public static PerfScope Profile(World world, Player player, string label)
		{
			return new PerfScope(world, player, label);
		}

		static void RecordPerf(World world, Player player, string label, long elapsedTimestampTicks)
		{
			try
			{
				var state = GetPerfState(world);
				if (!state.Aggregates.TryGetValue(label, out var aggregate))
				{
					aggregate = new PerfAggregate();
					state.Aggregates.Add(label, aggregate);
				}

				aggregate.Calls++;
				aggregate.TotalTimestampTicks += elapsedTimestampTicks;
				if (elapsedTimestampTicks > aggregate.MaxTimestampTicks)
					aggregate.MaxTimestampTicks = elapsedTimestampTicks;

				var elapsedMs = TimestampTicksToMilliseconds(elapsedTimestampTicks);
				if (elapsedMs >= CountAsSlowMilliseconds)
					aggregate.SlowCalls++;

				if (elapsedMs >= ImmediateSpikeMilliseconds)
					OpenRA.Log.Write("debug",
						$"[FRANS-PERF-SPIKE][WT {world.WorldTick}] {player} {label} = {elapsedMs:0.00} ms");
			}
			catch
			{
				// Profiling must never affect gameplay.
			}
		}

		public static void SetPerfContext(World world, string key, string value)
		{
			if (world == null || string.IsNullOrEmpty(key))
				return;

			try
			{
				GetPerfState(world).Context[key] = value ?? string.Empty;
			}
			catch
			{
				// Context is diagnostic only.
			}
		}

		public static void PerfWorldHeartbeat(World world)
		{
			if (world == null)
				return;

			try
			{
				var state = GetPerfState(world);
				var worldTick = world.WorldTick;
				if (state.LastHeartbeatWorldTick < 0)
					EnsureBuildFingerprintLogged(world);
				if (state.LastHeartbeatWorldTick == worldTick)
					return;

				var now = Stopwatch.GetTimestamp();
				if (state.LastHeartbeatTimestamp != 0)
				{
					var worldTickDelta = worldTick - state.LastHeartbeatWorldTick;
					var gapMs = TimestampTicksToMilliseconds(now - state.LastHeartbeatTimestamp);
					if (worldTickDelta == 1 && gapMs >= WorldTickGapMilliseconds)
					{
						var context = state.Context.Count == 0
							? "no ferry context"
							: string.Join(" | ", state.Context.OrderBy(kv => kv.Key).Select(kv => $"{kv.Key}={kv.Value}"));

						OpenRA.Log.Write("debug",
							$"[FRANS-PERF-WORLD][WT {worldTick}] previous world-tick wall interval = {gapMs:0.00} ms; {context}");
					}
				}

				state.LastHeartbeatWorldTick = worldTick;
				state.LastHeartbeatTimestamp = now;

				if (state.LastSummaryWorldTick < 0)
					state.LastSummaryWorldTick = worldTick;

				if (worldTick - state.LastSummaryWorldTick < PerfSummaryIntervalWorldTicks)
					return;

				var entries = state.Aggregates
					.Where(kv => kv.Value.Calls > 0)
					.OrderByDescending(kv => kv.Value.TotalTimestampTicks)
					.ThenByDescending(kv => kv.Value.MaxTimestampTicks)
					.Take(PerfSummaryTopEntries)
					.ToArray();

				if (entries.Length > 0)
				{
					OpenRA.Log.Write("debug",
						$"[FRANS-PERF-SUMMARY][WT {worldTick}] top {entries.Length} Frans profiles over last ~{worldTick - state.LastSummaryWorldTick} WT:");

					foreach (var entry in entries)
					{
						var a = entry.Value;
						OpenRA.Log.Write("debug",
							$"[FRANS-PERF-SUMMARY][WT {worldTick}] {entry.Key}: calls={a.Calls}, total={TimestampTicksToMilliseconds(a.TotalTimestampTicks):0.00} ms, max={TimestampTicksToMilliseconds(a.MaxTimestampTicks):0.00} ms, >=2ms={a.SlowCalls}");
					}
				}

				state.Aggregates.Clear();
				state.LastSummaryWorldTick = worldTick;
			}
			catch (Exception e)
			{
				OpenRA.Log.Write("debug", $"[FRANS-PERF-ERROR][WT {world.WorldTick}] {e.Message}");
			}
		}

		public static void BotDebug(World world, string format, params object[] args)
		{
			EnsureBuildFingerprintLogged(world);

			AIUtils.BotDebug(format, args);

			try
			{
				var message = string.Format(format, args);
				var worldTick = world?.WorldTick ?? -1;
				OpenRA.Log.Write("debug", $"[FRANS][WT {worldTick}] {message}");
			}
			catch (Exception e)
			{
				OpenRA.Log.Write("debug", $"[FRANS][LOGGER-ERROR] {e.Message}");
			}
		}
	}
}
