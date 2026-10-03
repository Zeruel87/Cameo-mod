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
using System.Globalization;
using System.Linq;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Support;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>
	/// The offline-fitted arsenal priors (tools/ai/fit_arsenal_priors.py), free of world state so tests can drive it
	/// with an inline MiniYaml string. Unknown pairs and types are neutral (100).
	/// </summary>
	public sealed class ArsenalPriors
	{
		const string PairSeparator = "__vs__";

		readonly Dictionary<(string Mine, string Theirs), Dictionary<string, int>> trades = new();

		public int[] VisibilityPercentByPhase { get; private set; } = Array.Empty<int>();
		public int PairCount => trades.Count;
		public int TypeCount => trades.Values.Sum(t => t.Count);

		public static ArsenalPriors Parse(IEnumerable<MiniYamlNode> nodes)
		{
			var priors = new ArsenalPriors();
			var root = nodes.FirstOrDefault(n => n.Key == "BotArsenalPriors");
			if (root == null)
				return priors;

			foreach (var node in root.Value.Nodes)
			{
				if (node.Key == "VisibilityPercentByPhase")
				{
					priors.VisibilityPercentByPhase = node.Value.Value.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
						.Select(s => int.Parse(s, CultureInfo.InvariantCulture)).ToArray();
				}
				else if (node.Key.StartsWith("TradePercent@", StringComparison.Ordinal))
				{
					var pair = node.Key["TradePercent@".Length..];
					var split = pair.IndexOf(PairSeparator, StringComparison.Ordinal);
					if (split <= 0)
						continue;

					var key = (pair[..split], pair[(split + PairSeparator.Length)..]);
					var types = new Dictionary<string, int>(StringComparer.Ordinal);
					foreach (var t in node.Value.Nodes)
						if (int.TryParse(t.Value.Value, NumberStyles.Integer, CultureInfo.InvariantCulture, out var pct))
							types[t.Key] = pct;

					priors.trades[key] = types;
				}
			}

			return priors;
		}

		/// <summary>Value destroyed per value lost (percent) by <paramref name="unitType"/> of faction <paramref name="mine"/> against <paramref name="theirs"/>; 100 when unknown.</summary>
		public int TradePercent(string mine, string theirs, string unitType)
		{
			return mine != null && theirs != null && unitType != null
				&& trades.TryGetValue((mine, theirs), out var types) && types.TryGetValue(unitType, out var pct) ? pct : 100;
		}
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Reads the committed, offline-fitted arsenal priors (DESIGN §19.2: frozen in release, trained on dev) and serves them",
		"to the unit builder as a bounded per-candidate weight (IBotProductionWeight). Host-only (bot ticks run only there);",
		"the values are never written into rules. Inert unless UseLearnedPriors is on (genericbot only: classic has no provider).")]
	public class BotLearnedPriorsInfo : ConditionalTraitInfo
	{
		[Desc("Weight the unit builder's choices by the priors. False (default) = the provider is inactive and the unit",
			"builder takes its original path, random draws included.")]
		public readonly bool UseLearnedPriors = false;

		[Desc("Mod-relative path of the priors file written by tools/ai/fit_arsenal_priors.py --write.")]
		public readonly string PriorsFile = "ai/learned/arsenal_priors.yaml";

		[Desc("Lowest weight (percent) the priors may give a candidate.")]
		public readonly int MinWeightPercent = 50;

		[Desc("Highest weight (percent) the priors may give a candidate.")]
		public readonly int MaxWeightPercent = 150;

		public override object Create(ActorInitializer init) { return new BotLearnedPriors(init.Self, this); }
	}

	public class BotLearnedPriors : ConditionalTrait<BotLearnedPriorsInfo>, IBotTick, IBotProductionWeight
	{
		readonly World world;
		readonly OpenRA.Player player;
		ArsenalPriors priors = new();
		bool loaded;

		public BotLearnedPriors(Actor self, BotLearnedPriorsInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (loaded)
				return;

			loaded = true;
			var fs = Game.ModData.DefaultFileSystem;
			if (!fs.Exists(Info.PriorsFile))
			{
				Log.Write("debug", $"AI {player.InternalName}: LEARNED priors: no priors ({Info.PriorsFile} missing), everything neutral");
				return;
			}

			using (var stream = fs.Open(Info.PriorsFile))
				priors = ArsenalPriors.Parse(MiniYaml.FromStream(stream, Info.PriorsFile));

			Log.Write("debug", $"AI {player.InternalName}: LEARNED priors: {priors.PairCount} pairs, {priors.TypeCount} types");
		}

		// The enemy faction: the main target's if a provider names one, else the most common faction among enemy
		// PLAYERS (never actors - nothing here enumerates the world's units).
		string EnemyFaction()
		{
			var main = player.PlayerActor.TraitsImplementing<IBotMainTargetProvider>()
				.Select(p => p.MainTarget).FirstOrDefault(t => t != null);
			if (main != null)
				return main.Faction?.InternalName;

			return world.Players
				.Where(p => p != player && !p.NonCombatant && !p.Spectating && player.RelationshipWith(p) == PlayerRelationship.Enemy)
				.GroupBy(p => p.Faction?.InternalName).Where(g => g.Key != null)
				.OrderByDescending(g => g.Count()).ThenBy(g => g.Key, StringComparer.Ordinal)
				.Select(g => g.Key).FirstOrDefault();
		}

		bool IBotProductionWeight.IsActive => !IsTraitDisabled && Info.UseLearnedPriors;

		int IBotProductionWeight.WeightPercent(OpenRA.Player self, ActorInfo unit)
		{
			if (IsTraitDisabled || !loaded)
				return 100;

			// A kill/loss trade ratio only measures combat units: transports, harvesters and other unarmed units never kill,
			// so the first fitted file scored the Chinook 0.01 and harvesters 0.05 — they stay neutral here.
			if (!unit.HasTraitInfo<AttackBaseInfo>())
				return 100;

			var pct = priors.TradePercent(self.Faction?.InternalName, EnemyFaction(), unit.Name);
			return Math.Clamp(pct, Info.MinWeightPercent, Info.MaxWeightPercent);
		}
	}
}
