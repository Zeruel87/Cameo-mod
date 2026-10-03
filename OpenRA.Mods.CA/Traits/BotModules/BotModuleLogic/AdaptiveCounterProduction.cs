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
using OpenRA.GameRules;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Warheads;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// Adaptive counter-production, ported from #245 (Blackrobe) onto the difficulty scale (DESIGN §19.1).
	/// <list type="bullet">
	/// <item>How MUCH a bot counters is `BotLimits.AdaptiveCounterWeight`, one number per tier on the line,
	/// instead of #245's "Hard and above" switch.</item>
	/// <item>What it counters is the enemy army it has SEEN (IBotEnemyCompositionProvider, the master AI's fog
	/// memory). Only when no provider observes through fog does it fall back to #245's omniscient sample,
	/// which the `classic` bot keeps on purpose.</item>
	/// <item>A candidate's score comes from its weapons' real Versus against each observed enemy's armour,
	/// weighted by that enemy's value: no cost thresholds and no per-actor override lists.</item>
	/// </list>
	/// </summary>
	public sealed class AdaptiveCounterProduction
	{
		readonly World world;
		readonly Player player;
		readonly Dictionary<string, int> observedEnemyValue = new();
		readonly Dictionary<string, WeaponProfile[]> profiles = new();
		int nextObservation;

		public int AdaptiveSelections;
		public int TotalSelections;
		public bool LastChoiceAdaptive;

		public IReadOnlyDictionary<string, int> ObservedEnemyValue => observedEnemyValue;

		readonly struct WeaponProfile
		{
			public readonly BitSet<TargetableType> Valid;
			public readonly BitSet<TargetableType> Invalid;
			public readonly IReadOnlyDictionary<string, int> Versus;

			public WeaponProfile(WeaponInfo weapon, DamageWarhead main)
			{
				Valid = weapon.ValidTargets;
				Invalid = weapon.InvalidTargets;
				Versus = main.Versus;
			}
		}

		public AdaptiveCounterProduction(World world, Player player)
		{
			this.world = world;
			this.player = player;
		}

		/// <summary>#245's selection cap: counters stay at or below `weightPercent` of mobile combat picks.</summary>
		public static bool CounterPickAllowed(int adaptiveSelections, int totalSelections, int weightPercent)
		{
			return weightPercent > 0 && totalSelections >= 2 &&
				(adaptiveSelections + 1) * 100 <= (totalSelections + 1) * Math.Clamp(weightPercent, 0, 100);
		}

		/// <summary>#245's smoothing: each sample moves the memory a quarter of the way; zeroes drop out.</summary>
		public static void Smooth(Dictionary<string, int> memory, IReadOnlyDictionary<string, int> sample)
		{
			foreach (var name in memory.Keys.Union(sample.Keys).ToArray())
			{
				sample.TryGetValue(name, out var value);
				memory.TryGetValue(name, out var old);
				var smoothed = (old * 3 + value) / 4;
				if (smoothed > 0)
					memory[name] = smoothed;
				else
					memory.Remove(name);
			}
		}

		public void Observe(int interval, IBotEnemyCompositionProvider provider)
		{
			if (world.WorldTick < nextObservation)
				return;

			nextObservation = world.WorldTick + Math.Max(1, interval);
			IReadOnlyDictionary<string, int> sample = null;
			if (provider == null || !provider.TryGetEnemyComposition(out sample))
				sample = OmniscientSample();

			Smooth(observedEnemyValue, sample);
		}

		Dictionary<string, int> OmniscientSample()
		{
			var sample = new Dictionary<string, int>();
			foreach (var a in world.ActorsHavingTrait<IPositionable>())
			{
				if (a.IsDead || !a.IsInWorld || a.Owner == player || player.RelationshipWith(a.Owner) != PlayerRelationship.Enemy)
					continue;

				if (!IsArmy(a.Info))
					continue;

				sample[a.Info.Name] = sample.GetValueOrDefault(a.Info.Name) + (a.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 1);
			}

			return sample;
		}

		static bool IsArmy(ActorInfo actor) =>
			(actor.HasTraitInfo<AttackBaseInfo>() || actor.HasTraitInfo<CargoInfo>() || actor.HasTraitInfo<CloakInfo>()) &&
			!actor.HasTraitInfo<HarvesterInfo>();

		public static bool IsMobileCombat(ActorInfo actor) => actor.HasTraitInfo<IPositionableInfo>() &&
			actor.HasTraitInfo<AttackBaseInfo>() && !actor.HasTraitInfo<HarvesterInfo>();

		/// <summary>The best counter among `candidates`, or null. `owned` counts what the bot already has of a type.</summary>
		public ActorInfo Choose(IEnumerable<ActorInfo> candidates, Func<string, int> owned)
		{
			if (observedEnemyValue.Count == 0)
				return null;

			ActorInfo best = null;
			var bestScore = 0L;
			foreach (var candidate in candidates.OrderBy(c => c.Name, StringComparer.Ordinal))
			{
				var score = Score(candidate) / (1 + owned(candidate.Name));
				if (score > bestScore)
				{
					bestScore = score;
					best = candidate;
				}
			}

			return best;
		}

		public void Record(ActorInfo chosen)
		{
			if (!IsMobileCombat(chosen))
				return;

			TotalSelections++;
			if (LastChoiceAdaptive)
				AdaptiveSelections++;
		}

		long Score(ActorInfo candidate)
		{
			var weapons = Profile(candidate);
			if (weapons.Length == 0)
				return 0;

			var detects = candidate.HasTraitInfo<DetectCloakedInfo>();
			var score = 0L;
			foreach (var (type, value) in observedEnemyValue)
			{
				if (!world.Map.Rules.Actors.TryGetValue(type, out var enemy))
					continue;

				var targets = enemy.GetAllTargetTypes();
				var armor = enemy.TraitInfos<ArmorInfo>().FirstOrDefault(a => a.InstanceName == null && a.EnabledByDefault)?.Type;
				var effect = 0;
				foreach (var w in weapons)
					if (w.Valid.Overlaps(targets) && !w.Invalid.Overlaps(targets))
						effect = Math.Max(effect, armor == null ? 100 : w.Versus.GetValueOrDefault(armor, 100));

				if (effect == 0)
					continue;

				if (detects && enemy.HasTraitInfo<CloakInfo>())
					effect *= 2;

				score += (long)value * effect / 100;
			}

			return score;
		}

		WeaponProfile[] Profile(ActorInfo candidate)
		{
			if (profiles.TryGetValue(candidate.Name, out var cached))
				return cached;

			var list = new List<WeaponProfile>();
			foreach (var armament in candidate.TraitInfos<ArmamentInfo>().Where(a => a.EnabledByDefault))
			{
				if (armament.Weapon == null || !world.Map.Rules.Weapons.TryGetValue(armament.Weapon.ToLowerInvariant(), out var weapon))
					continue;

				// The largest positive damage warhead is the weapon's main one (W24), as the production tooltip reads it.
				var main = weapon.Warheads.OfType<DamageWarhead>().Where(d => d.Damage > 0).OrderByDescending(d => d.Damage).FirstOrDefault();
				if (main != null)
					list.Add(new WeaponProfile(weapon, main));
			}

			return profiles[candidate.Name] = list.ToArray();
		}

		public IEnumerable<MiniYamlNode> SaveNodes()
		{
			yield return new MiniYamlNode("AdaptiveSelections", FieldSaver.FormatValue(AdaptiveSelections));
			yield return new MiniYamlNode("TotalWeightedSelections", FieldSaver.FormatValue(TotalSelections));
			yield return new MiniYamlNode("ObservedEnemyTypes", FieldSaver.FormatValue(observedEnemyValue.Keys.ToArray()));
			yield return new MiniYamlNode("ObservedEnemyValues", FieldSaver.FormatValue(observedEnemyValue.Values.ToArray()));
		}

		public void Load(MiniYaml data)
		{
			var selections = data.NodeWithKeyOrDefault("AdaptiveSelections");
			if (selections != null)
				AdaptiveSelections = FieldLoader.GetValue<int>("AdaptiveSelections", selections.Value.Value);

			var total = data.NodeWithKeyOrDefault("TotalWeightedSelections");
			if (total != null)
				TotalSelections = FieldLoader.GetValue<int>("TotalWeightedSelections", total.Value.Value);

			var types = data.NodeWithKeyOrDefault("ObservedEnemyTypes");
			var values = data.NodeWithKeyOrDefault("ObservedEnemyValues");
			if (types != null && values != null)
			{
				var t = FieldLoader.GetValue<string[]>("ObservedEnemyTypes", types.Value.Value);
				var v = FieldLoader.GetValue<int[]>("ObservedEnemyValues", values.Value.Value);
				observedEnemyValue.Clear();
				for (var i = 0; i < Math.Min(t.Length, v.Length); i++)
					observedEnemyValue[t[i]] = v[i];
			}
		}
	}
}
