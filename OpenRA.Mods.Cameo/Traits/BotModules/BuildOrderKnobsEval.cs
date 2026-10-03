#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using OpenRA.Mods.CA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>What the bot SAW this snapshot (fog memory only), reduced to the numbers the react rules read.</summary>
	public readonly struct BuildOrderReactInputs
	{
		public readonly int Tick;
		public readonly int EnemyAirValue, EnemyPressureValue, EnemyDefenceValue, EnemyArmyValue;
		public readonly int EnemyEconomy, OwnEconomy;

		public BuildOrderReactInputs(int tick, int enemyAirValue, int enemyPressureValue, int enemyDefenceValue, int enemyArmyValue,
			int enemyEconomy, int ownEconomy)
		{
			Tick = tick;
			EnemyAirValue = enemyAirValue;
			EnemyPressureValue = enemyPressureValue;
			EnemyDefenceValue = enemyDefenceValue;
			EnemyArmyValue = enemyArmyValue;
			EnemyEconomy = enemyEconomy;
			OwnEconomy = ownEconomy;
		}
	}

	/// <summary>The thresholds of the react rules (module Info numbers).</summary>
	public readonly struct BuildOrderReactThresholds
	{
		public readonly int AirValue, RushWindowTicks, RushPressureValue, TurtleDefenceValue, TurtleDefenceSharePct, OutEarnPct, OutEarnMinEconomy;

		public BuildOrderReactThresholds(int airValue, int rushWindowTicks, int rushPressureValue, int turtleDefenceValue,
			int turtleDefenceSharePct, int outEarnPct, int outEarnMinEconomy)
		{
			AirValue = airValue;
			RushWindowTicks = rushWindowTicks;
			RushPressureValue = rushPressureValue;
			TurtleDefenceValue = turtleDefenceValue;
			TurtleDefenceSharePct = turtleDefenceSharePct;
			OutEarnPct = outEarnPct;
			OutEarnMinEconomy = outEarnMinEconomy;
		}
	}

	[Flags]
	public enum BuildOrderReaction
	{
		None = 0,
		Air = 1,
		Rush = 2,
		Turtle = 4,
		OutEarned = 8
	}

	/// <summary>
	/// The opening: an ordered list of the first N building categories. It is "active" until it completes, runs past
	/// MaxTicks, or is invalidated by the react layer. A step stuck for StepTimeoutTicks (not buildable yet, or already
	/// satisfied by a pre-placed building) is skipped, so an opening can never stall the base. Pure: no world access.
	/// </summary>
	public sealed class BuildOrderOpening
	{
		public readonly string Name;
		readonly string[] steps;
		readonly int maxTicks, stepTimeoutTicks;
		int index, stepStartTick;

		public string EndReason { get; private set; } = "";
		public int StepIndex => index;
		public int StepCount => steps.Length;
		public bool Active => EndReason.Length == 0;

		public BuildOrderOpening(string name, string[] steps, int maxTicks, int stepTimeoutTicks, int startTick = 0)
		{
			Name = name;
			this.steps = steps ?? Array.Empty<string>();
			this.maxTicks = maxTicks;
			this.stepTimeoutTicks = stepTimeoutTicks;
			stepStartTick = startTick;
			if (this.steps.Length == 0)
				EndReason = "empty";
		}

		/// <summary>The category the opening wants next, or null once it has ended.</summary>
		public string Wanted => Active && index < steps.Length ? steps[index] : null;

		public void Update(int tick)
		{
			if (!Active)
				return;

			if (tick >= maxTicks)
			{
				EndReason = "timeout";
				return;
			}

			while (Active && tick - stepStartTick >= stepTimeoutTicks)
				Advance(tick);
		}

		/// <summary>The base builder queued a building of the category; the current step advances when it satisfies it.</summary>
		public void NotifyQueued(string category, int tick)
		{
			if (Active && BuildOrderCategory.Satisfies(steps[index], category))
				Advance(tick);
		}

		public void Invalidate(string reason)
		{
			if (Active)
				EndReason = reason;
		}

		void Advance(int tick)
		{
			index++;
			stepStartTick = tick;
			if (index >= steps.Length)
				EndReason = "completed";
		}
	}

	/// <summary>
	/// Pure build-order knob math (DESIGN 19.2, AI_ARCHITECTURE 12.25). Fixed point in thousandths, integer only except the
	/// bandit's Beta sample (host-only, drawn from the host's random). A knob = preset x learned x jitter, clamped; the react
	/// layer then multiplies it by a bounded factor that decays back to 1000.
	/// </summary>
	public static class BuildOrderKnobsEval
	{
		public const int One = BuildOrderKnob.Neutral;

		/// <summary>Mean observed economy per enemy, rounded half up, over enemies whose observed economy is above 0 (an
		/// unscouted enemy reads 0 under fog; counting it would understate the enemy). None observed: 0.</summary>
		public static int EnemyEconomyPerEnemy(IEnumerable<int> observedEconomies)
		{
			long sum = 0;
			var count = 0;
			foreach (var e in observedEconomies)
			{
				if (e <= 0)
					continue;
				sum += e;
				count++;
			}

			return count == 0 ? 0 : (int)((sum * 2 + count) / (count * 2));
		}

		public static int Clamp(int value, int min, int max) => Math.Max(min, Math.Min(max, value));

		/// <summary>
		/// The per-match jitter factor in thousandths, from one uniform draw in [0, 2000]:
		/// 1000 + (draw - 1000) x jitterPct / 100, so JitterPct 8 spans 920..1080.
		/// </summary>
		public static int JitterMilli(int jitterPct, int draw)
		{
			var d = Clamp(draw, 0, 2000);
			return One + (d - 1000) * Math.Max(0, jitterPct) / 100;
		}

		/// <summary>Value = preset x learned x jitter (all thousandths), clamped to [min, max].</summary>
		public static int Combine(int presetMilli, int learnedMilli, int jitterMilli, int min, int max)
		{
			var value = presetMilli * (long)learnedMilli / One * jitterMilli / One;
			return Clamp((int)Math.Max(int.MinValue, Math.Min(int.MaxValue, value)), min, max);
		}

		/// <summary>Move current toward target by at most maxStep.</summary>
		public static int Approach(int current, int target, int maxStep)
		{
			var step = Math.Max(0, maxStep);
			if (current < target)
				return Math.Min(target, current + step);
			return Math.Max(target, current - step);
		}

		/// <summary>
		/// A react factor (1000 = none) after elapsedTicks with no reaction pushing it: it decays toward 1000 by
		/// decayPerMinute thousandths per game minute.
		/// </summary>
		public static int Decay(int reactMilli, int decayPerMinute, int elapsedTicks, int ticksPerMinute)
		{
			var step = (int)(Math.Max(0, decayPerMinute) * (long)Math.Max(0, elapsedTicks) / Math.Max(1, ticksPerMinute));
			return Approach(reactMilli, One, step);
		}

		/// <summary>
		/// One react step for a knob: while a reaction pushes it (target != 1000) the factor approaches the target by
		/// approachStep; with no reaction it decays toward 1000. Always inside [reactMin, reactMax].
		/// </summary>
		public static int ReactStep(int reactMilli, int targetMilli, int approachStep, int decayPerMinute, int elapsedTicks,
			int ticksPerMinute, int reactMin, int reactMax)
		{
			var next = targetMilli == One
				? Decay(reactMilli, decayPerMinute, elapsedTicks, ticksPerMinute)
				: Approach(reactMilli, Clamp(targetMilli, reactMin, reactMax), approachStep);
			return Clamp(next, reactMin, reactMax);
		}

		/// <summary>The react rules over what was SEEN (AI_ARCHITECTURE 12.25).</summary>
		public static BuildOrderReaction Evaluate(in BuildOrderReactInputs i, in BuildOrderReactThresholds t)
		{
			var result = BuildOrderReaction.None;

			// Enemy air seen -> defence (the AA share).
			if (i.EnemyAirValue >= t.AirValue)
				result |= BuildOrderReaction.Air;

			// An early enemy army near our base -> rush.
			if (i.Tick <= t.RushWindowTicks && i.EnemyPressureValue >= t.RushPressureValue)
				result |= BuildOrderReaction.Rush;

			// Enemy defence-heavy: a lot of defence, and a large share of everything they showed.
			var shown = (long)i.EnemyDefenceValue + i.EnemyArmyValue;
			if (i.EnemyDefenceValue >= t.TurtleDefenceValue && i.EnemyDefenceValue * 100L >= shown * t.TurtleDefenceSharePct)
				result |= BuildOrderReaction.Turtle;

			// The enemy out-earns us: their seen economy proxy beats ours by OutEarnPct.
			if (i.EnemyEconomy >= t.OutEarnMinEconomy && i.EnemyEconomy * 100L > (long)i.OwnEconomy * t.OutEarnPct)
				result |= BuildOrderReaction.OutEarned;

			return result;
		}

		public static string ReactionName(BuildOrderReaction reaction)
		{
			switch (reaction)
			{
				case BuildOrderReaction.Air: return "air";
				case BuildOrderReaction.Rush: return "rush";
				case BuildOrderReaction.Turtle: return "turtle";
				case BuildOrderReaction.OutEarned: return "out_earned";
				default: return "none";
			}
		}

		static readonly BuildOrderReaction[] ReactionOrder =
		{
			BuildOrderReaction.Air, BuildOrderReaction.Rush, BuildOrderReaction.Turtle, BuildOrderReaction.OutEarned
		};

		/// <summary>
		/// The combined react target of one knob over the active reactions: the product (in thousandths) of every active
		/// reaction's entry for that knob. 1000 when none touches it.
		/// </summary>
		public static int CombinedTarget(string knob, BuildOrderReaction active, IReadOnlyDictionary<string, Dictionary<string, int>> reactTargets)
		{
			long product = One;
			foreach (var reaction in ReactionOrder)
			{
				if ((active & reaction) == 0)
					continue;

				if (reactTargets.TryGetValue(ReactionName(reaction), out var perKnob) && perKnob.TryGetValue(knob, out var milli))
					product = product * milli / One;
			}

			return (int)product;
		}

		/// <summary>
		/// Thompson sampling: draw Beta(alpha, beta) with integer shapes as x / (x + y), x and y sums of alpha and beta
		/// unit exponentials. Shapes above maxShape are scaled down together (same mean, a little more spread than the
		/// data deserves, which is harmless for a bounded bandit). uniform returns a double in [0, 1).
		/// </summary>
		public static double SampleBeta(int alpha, int beta, Func<double> uniform, int maxShape = 64)
		{
			alpha = Math.Max(1, alpha);
			beta = Math.Max(1, beta);
			var biggest = Math.Max(alpha, beta);
			if (biggest > maxShape)
			{
				alpha = Math.Max(1, alpha * maxShape / biggest);
				beta = Math.Max(1, beta * maxShape / biggest);
			}

			double x = 0, y = 0;
			for (var k = 0; k < alpha; k++)
				x += -Math.Log(Math.Max(1e-12, 1.0 - uniform()));
			for (var k = 0; k < beta; k++)
				y += -Math.Log(Math.Max(1e-12, 1.0 - uniform()));

			return x / (x + y);
		}

		/// <summary>
		/// Choose an opening: every candidate scores preset weight x a Thompson sample of its learned (alpha, beta); the
		/// best score wins. No posterior = Beta(1, 1), so the choice is a weight-tilted random draw. A zero weight is never
		/// chosen. Candidates are visited in name order so the result is deterministic for a given sequence of draws.
		/// </summary>
		public static string ChooseOpening(IReadOnlyDictionary<string, int> weights, Func<string, (int Alpha, int Beta)> posterior, Func<double> uniform)
		{
			string best = null;
			var bestScore = -1.0;
			foreach (var name in weights.Keys.OrderBy(k => k, StringComparer.Ordinal))
			{
				var weight = weights[name];
				if (weight <= 0)
					continue;

				var (alpha, beta) = posterior(name);
				var score = weight * SampleBeta(alpha, beta, uniform);
				if (score > bestScore)
				{
					bestScore = score;
					best = name;
				}
			}

			return best;
		}

		/// <summary>The game family of a faction: the part of its internal name before the first underscore (ra1_allies gives ra1). No id list.</summary>
		public static string FamilyOf(string faction)
		{
			if (string.IsNullOrEmpty(faction))
				return "";

			var cut = faction.IndexOf('_');
			return cut > 0 ? faction[..cut] : faction;
		}
	}

	/// <summary>
	/// The offline-fitted build-order knobs (tools/ai/tune_build_order.py), free of world state so tests can drive it with
	/// an inline MiniYaml string. Layout: a BotBuildOrderKnobs root with `Knobs@personality__scope` nodes (scope = a faction
	/// id, family_FAMILY, or any; children are knob: thousandths) and `Openings@personality__ownfaction__vs__enemyfaction`
	/// nodes (children are opening: alpha beta). Lookup for a knob: (personality, faction), then (personality, family),
	/// then (personality, any), then (any, any); missing = 1000.
	/// </summary>
	public sealed class BuildOrderLearned
	{
		const string VersusSeparator = "__vs__";

		readonly Dictionary<(string Personality, string Scope), Dictionary<string, int>> knobs = new();
		readonly Dictionary<(string Personality, string Own, string Enemy), Dictionary<string, (int Alpha, int Beta)>> openings = new();

		public int ScopeCount => knobs.Count;
		public int OpeningScopeCount => openings.Count;

		public static BuildOrderLearned Parse(IEnumerable<MiniYamlNode> nodes)
		{
			var learned = new BuildOrderLearned();
			var root = nodes.FirstOrDefault(n => n.Key == "BotBuildOrderKnobs");
			if (root == null)
				return learned;

			foreach (var node in root.Value.Nodes)
			{
				if (node.Key.StartsWith("Knobs@", StringComparison.Ordinal))
				{
					var key = node.Key["Knobs@".Length..];
					var split = key.IndexOf("__", StringComparison.Ordinal);
					if (split <= 0)
						continue;

					var values = new Dictionary<string, int>(StringComparer.Ordinal);
					foreach (var child in node.Value.Nodes)
						if (Array.IndexOf(BuildOrderKnob.All, child.Key) >= 0
							&& int.TryParse(child.Value.Value, NumberStyles.Integer, CultureInfo.InvariantCulture, out var milli))
							values[child.Key] = milli;

					learned.knobs[(key[..split], key[(split + 2)..])] = values;
				}
				else if (node.Key.StartsWith("Openings@", StringComparison.Ordinal))
				{
					var key = node.Key["Openings@".Length..];
					var vs = key.IndexOf(VersusSeparator, StringComparison.Ordinal);
					if (vs <= 0)
						continue;

					var left = key[..vs];
					var enemy = key[(vs + VersusSeparator.Length)..];
					var split = left.IndexOf("__", StringComparison.Ordinal);
					if (split <= 0)
						continue;

					var posteriors = new Dictionary<string, (int, int)>(StringComparer.Ordinal);
					foreach (var child in node.Value.Nodes)
					{
						var parts = child.Value.Value?.Split(' ', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
						if (parts is { Length: 2 }
							&& int.TryParse(parts[0], NumberStyles.Integer, CultureInfo.InvariantCulture, out var alpha)
							&& int.TryParse(parts[1], NumberStyles.Integer, CultureInfo.InvariantCulture, out var beta))
							posteriors[child.Key] = (Math.Max(1, alpha), Math.Max(1, beta));
					}

					learned.openings[(left[..split], left[(split + 2)..], enemy)] = posteriors;
				}
			}

			return learned;
		}

		/// <summary>The learned multiplier of a knob in thousandths; 1000 when no scope in the chain has it.</summary>
		public int Multiplier(string personality, string faction, string knob)
		{
			var family = "family_" + BuildOrderKnobsEval.FamilyOf(faction);
			foreach (var key in new[] { (personality, faction), (personality, family), (personality, "any"), ("any", "any") })
				if (key.Item2 != null && knobs.TryGetValue(key, out var values) && values.TryGetValue(knob, out var milli))
					return milli;

			return BuildOrderKnob.Neutral;
		}

		/// <summary>The (alpha, beta) posterior of an opening for a matchup; (1, 1) when none was fitted.</summary>
		public (int Alpha, int Beta) Posterior(string personality, string ownFaction, string enemyFaction, string opening)
		{
			return openings.TryGetValue((personality, ownFaction, enemyFaction), out var per) && per.TryGetValue(opening, out var p)
				? p : (1, 1);
		}
	}
}
