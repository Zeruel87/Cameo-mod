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

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	// EL-0 (AI_ARCHITECTURE §12.30, DESIGN §19.13): the PURE half of the engagement log. Nothing here touches the world, a
	// player or an actor, so every rule is unit-tested (EngagementMathTest) and the scoring is mirrored line for line in
	// tools/ai/ai_log_common.py (engagement_score) over the same test vectors. Integer math throughout; the one double is the
	// approach angle, rounded to whole degrees.
	public static class EngagementConstants
	{
		/// <summary>An event joins an open engagement whose centroid is within this many cells.</summary>
		public const int RadiusCells = 10;

		/// <summary>An engagement with no event for this long closes (150 ticks = 6 s at 40 ms).</summary>
		public const int QuietTicks = 150;

		/// <summary>A quiet engagement older than this is checked for "one side has nothing left in radius".</summary>
		public const int SideGoneQuietTicks = 50;

		/// <summary>Below this much value traded (killed + lost), or fewer than two deaths, the engagement is a skirmish.</summary>
		public const int MinValueTraded = 300;
		public const int MinDeaths = 2;

		/// <summary>Own base: an engagement centred this close to an own construction yard is a defend.</summary>
		public const int OwnBaseRadiusCells = 20;

		/// <summary>Seen enemy base: an engagement centred this close to a seen enemy construction yard is an attack.</summary>
		public const int EnemyBaseRadiusCells = 20;

		/// <summary>Own-unit snapshot and ring-buffer sample period (ticks).</summary>
		public const int SampleIntervalTicks = 50;

		/// <summary>Ring depth: 5 samples at 50 ticks reach back 200 ticks, past the 150-tick approach window.</summary>
		public const int RingSamples = 5;
		public const int ApproachWindowTicks = 150;

		public const int PostureIntervalTicks = 250;
		public const int PostureSeenRadiusCells = 40;
		public const int UnderAttackWindowTicks = 500;
		public const int EnemyBaseRefreshTicks = 500;
	}

	/// <summary>The one engagement scoring function (zero-sum trade, play quality against the prediction, objective), in thousandths.</summary>
	public static class EngagementScore
	{
		public const int TradeWeight = 500;
		public const int VsPredictionWeight = 250;
		public const int ObjectiveWeight = 250;

		// C# integer division truncates toward zero; the Python mirror does the same explicitly.
		public static int Trade(long killed, long lost) => (int)(1000L * (killed - lost) / Math.Max(1, killed + lost));

		/// <summary>The trade the Lanchester prediction implies: the value each side was predicted to lose, scored like a real one.</summary>
		public static int PredictedTrade(long ownValue, long enemyValue, int ownSurvivingPermille, int enemySurvivingPermille)
		{
			var predictedLost = ownValue * (1000 - Clamp(ownSurvivingPermille, 0, 1000)) / 1000;
			var predictedKilled = enemyValue * (1000 - Clamp(enemySurvivingPermille, 0, 1000)) / 1000;
			return Trade(predictedKilled, predictedLost);
		}

		public static int VsPrediction(int trade, int predictedTrade) => trade - predictedTrade;

		/// <summary>HP fraction lost, in thousandths of max HP, clamped to 0..1000.</summary>
		public static int HpLost(int hpStart, int hpEnd, int maxHp) =>
			Clamp((int)(1000L * (hpStart - hpEnd) / Math.Max(1, maxHp)), 0, 1000);

		/// <summary>One building: two thirds by the HP fraction lost, one third on death (OpenAI Five's building reward shape).</summary>
		public static int BuildingLoss(int hpLostMilli, bool dead) => (2 * hpLostMilli + (dead ? 1000 : 0)) / 3;

		/// <summary>The value-weighted building loss over every building at stake, in thousandths.</summary>
		public static int BuildingsLoss(IReadOnlyList<(int Value, int HpLostMilli, bool Dead)> buildings)
		{
			long weighted = 0, total = 0;
			foreach (var (value, hpLost, dead) in buildings)
			{
				var weight = Math.Max(1, value);
				weighted += weight * BuildingLoss(hpLost, dead);
				total += weight;
			}

			return (int)(weighted / Math.Max(1, total));
		}

		/// <summary>
		/// defend: own buildings saved (1000 - 2 x own loss); attack: enemy buildings destroyed (2 x enemy loss - 1000); field or
		/// nothing at stake: 0. All in -1000..1000.
		/// </summary>
		public static int Objective(string kind, int ownLossMilli, int enemyLossMilli, bool ownStake, bool enemyStake)
		{
			if (kind == "defend" && ownStake)
				return 1000 - 2 * ownLossMilli;
			if (kind == "attack" && enemyStake)
				return 2 * enemyLossMilli - 1000;
			return 0;
		}

		public static int Total(int trade, int vsPrediction, int objective) =>
			Clamp((TradeWeight * trade + VsPredictionWeight * vsPrediction + ObjectiveWeight * objective) / 1000, -1000, 1000);

		static int Clamp(int value, int min, int max) => value < min ? min : value > max ? max : value;
	}

	public static class EngagementGeometry
	{
		public static long Dist2(int x1, int y1, int x2, int y2)
		{
			long dx = x1 - x2, dy = y1 - y2;
			return dx * dx + dy * dy;
		}

		/// <summary>Whole cells, rounded down (integer square root).</summary>
		public static int DistCells(int x1, int y1, int x2, int y2) => (int)Math.Sqrt(Dist2(x1, y1, x2, y2));

		/// <summary>The angle between two vectors in whole degrees (0 = same direction, 180 = opposite); -1 when either has no length.</summary>
		public static int AngleDegrees(long ax, long ay, long bx, long by)
		{
			if ((ax == 0 && ay == 0) || (bx == 0 && by == 0))
				return -1;

			var dot = (double)ax * bx + (double)ay * by;
			var cross = (double)ax * by - (double)ay * bx;
			return (int)Math.Round(Math.Atan2(Math.Abs(cross), dot) * 180.0 / Math.PI);
		}
	}

	/// <summary>The last few cells of one unit, one per sample, to read where it was ~150 ticks ago.</summary>
	public sealed class PositionRing
	{
		readonly int[] ticks = new int[EngagementConstants.RingSamples];
		readonly int[] xs = new int[EngagementConstants.RingSamples];
		readonly int[] ys = new int[EngagementConstants.RingSamples];
		int count;
		int head;

		public void Add(int tick, int x, int y)
		{
			ticks[head] = tick;
			xs[head] = x;
			ys[head] = y;
			head = (head + 1) % ticks.Length;
			if (count < ticks.Length)
				count++;
		}

		/// <summary>The newest sample at least `minAge` ticks old, else the oldest sample held; false when empty or only the current sample exists.</summary>
		public bool TryOlder(int nowTick, int minAge, out int x, out int y)
		{
			x = y = 0;
			if (count < 2)
				return false;

			var found = false;
			var bestTick = int.MinValue;
			for (var i = 0; i < count; i++)
			{
				if (nowTick - ticks[i] >= minAge && ticks[i] > bestTick)
				{
					bestTick = ticks[i];
					x = xs[i];
					y = ys[i];
					found = true;
				}
			}

			if (found)
				return true;

			var oldest = int.MaxValue;
			for (var i = 0; i < count; i++)
			{
				if (ticks[i] < oldest && ticks[i] < nowTick)
				{
					oldest = ticks[i];
					x = xs[i];
					y = ys[i];
					found = true;
				}
			}

			return found;
		}
	}

	public sealed class EngagementBuilding
	{
		public bool Own;
		public int Value;
		public int MaxHp;
		public int HpStart;
		public int HpEnd;
		public bool Dead;
	}

	/// <summary>A seen enemy static defence: where it stands and how far it shoots (whole cells), for the tactics block.</summary>
	public readonly record struct EngagementDefence(uint Id, int X, int Y, int RangeCells, int Value);

	/// <summary>What the bot knew about the fight at one moment: only seen state, plus the predictor read of it.</summary>
	public sealed class EngagementSeen
	{
		public int Tick;
		public int OwnCommittedValue, OwnCommittedUnits, OwnDefenceValue, OwnArtilleryValue;
		public int EnemyUnitValue, EnemyUnits, EnemyDefenceValue, EnemyDefenceCount, EnemyArtilleryValue;
		public int PredictedRatioMilli, PredictedOwnSurvivingPermille, PredictedEnemySurvivingPermille;
		public int ArmyDistCells = -1;
	}

	/// <summary>The real unfogged state, offline scoring only (DESIGN §19.13, "truth block, logging only"). Nothing reads it back.</summary>
	public sealed class EngagementTruth
	{
		public int Tick;
		public int EnemyUnitValue, EnemyUnits, EnemyDefenceValue, EnemyDefenceCount;
		public int EnemyLossValue;
	}

	/// <summary>One open engagement: the running cluster plus every accumulator the record needs.</summary>
	public sealed class EngagementState
	{
		public int Id;
		public int StartTick;
		public int LastEventTick;
		public int NextSideCheckTick;
		public long SumX, SumY;
		public int EventCount;

		public int OwnHurtEvents, OwnDealtEvents;
		public int FirstOwnHurtTick = -1;
		public int FirstOwnMobileDealtTick = -1;

		public int OwnLostUnitValue, OwnLostUnits, OwnBuildingsLost;
		public int EnemyKilledUnitValue, EnemyKilledUnits;
		public int EnemyKilledDefenceValue, EnemyKilledDefences;
		public int EnemyKilledBuildingValue, EnemyBuildingsKilled;
		public int EnemyKilledHarvesterValue, EnemyHarvestersKilled;

		public readonly SortedDictionary<string, int> LostByRole = new(StringComparer.Ordinal);
		public readonly Dictionary<uint, EngagementBuilding> Buildings = new();
		public readonly List<EngagementDefence> Defences = new();

		public int IntoDefencesValue;
		public int DefenceKilledBeforeDirectEntry = -1;
		public long ApproachDx, ApproachDy;
		public int ApproachUnits;
		public int ArmyDistAtStartCells = -1;

		public EngagementSeen SeenStart, SeenEnd;
		public EngagementTruth TruthStart, TruthEnd;

		public int CentroidX => (int)(SumX / Math.Max(1, EventCount));
		public int CentroidY => (int)(SumY / Math.Max(1, EventCount));
		public int Deaths => OwnLostUnits + OwnBuildingsLost + EnemyKilledUnits + EnemyKilledDefences + EnemyBuildingsKilled + EnemyHarvestersKilled;
		public int EnemyKilledValue => EnemyKilledUnitValue + EnemyKilledDefenceValue + EnemyKilledBuildingValue + EnemyKilledHarvesterValue;
	}

	/// <summary>Spatial-temporal clustering of combat events into engagements (STARDATA-style battle segmentation).</summary>
	public sealed class EngagementTracker
	{
		readonly int radius2;
		readonly int quietTicks;
		readonly List<EngagementState> open = new();
		int nextId = 1;

		public EngagementTracker(int radiusCells, int quietTicks)
		{
			radius2 = radiusCells * radiusCells;
			this.quietTicks = quietTicks;
		}

		public IReadOnlyList<EngagementState> Open => open;

		/// <summary>The engagement an event at (x, y) belongs to: the nearest open one within the radius of its centroid, else a new one.</summary>
		public EngagementState Locate(int tick, int x, int y, out bool created)
		{
			EngagementState best = null;
			var bestDist = long.MaxValue;
			foreach (var e in open)
			{
				var d = EngagementGeometry.Dist2(x, y, e.CentroidX, e.CentroidY);
				if (d <= radius2 && d < bestDist)
				{
					best = e;
					bestDist = d;
				}
			}

			created = best == null;
			if (created)
			{
				best = new EngagementState { Id = nextId++, StartTick = tick, NextSideCheckTick = tick + EngagementConstants.SideGoneQuietTicks };
				open.Add(best);
			}

			best.SumX += x;
			best.SumY += y;
			best.EventCount++;
			best.LastEventTick = tick;
			return best;
		}

		/// <summary>Removes and returns every engagement quiet for QuietTicks.</summary>
		public List<EngagementState> CollectQuiet(int tick)
		{
			List<EngagementState> closed = null;
			for (var i = open.Count - 1; i >= 0; i--)
			{
				if (tick - open[i].LastEventTick < quietTicks)
					continue;

				closed ??= new List<EngagementState>();
				closed.Add(open[i]);
				open.RemoveAt(i);
			}

			closed?.Reverse();
			return closed ?? new List<EngagementState>();
		}

		public void Close(EngagementState state) => open.Remove(state);

		public List<EngagementState> CloseAll()
		{
			var all = new List<EngagementState>(open);
			open.Clear();
			return all;
		}
	}
}
