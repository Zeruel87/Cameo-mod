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
using System.Linq;
using System.Runtime.CompilerServices;
using OpenRA.GameRules;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Warheads;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// What one unit TYPE brings to a fight, read once per ruleset from its rules (AI_DEEP_RESEARCH.md §2.3,
	/// AI_ARCHITECTURE.md §12.3–12.4): cost, hit points, armour, speed, and per weapon the damage per tick, the
	/// Versus row of its main warhead, its range and what it may target. Bot-side, unsynced, read-only.
	/// </summary>
	public sealed class BotUnitProfile
	{
		public readonly string Name;
		public readonly int Cost;
		public readonly int Hp;
		public readonly string Armor;
		public readonly int Speed;
		public readonly bool IsAircraft;
		public readonly bool IsBuilding;
		public readonly BitSet<TargetableType> TargetTypes;
		public readonly BotWeaponProfile[] Weapons;

		public BotUnitProfile(string name, int cost, int hp, string armor, int speed, bool isAircraft, bool isBuilding,
			BitSet<TargetableType> targetTypes, BotWeaponProfile[] weapons)
		{
			Name = name;
			Cost = cost;
			Hp = hp;
			Armor = armor;
			Speed = speed;
			IsAircraft = isAircraft;
			IsBuilding = isBuilding;
			TargetTypes = targetTypes;
			Weapons = weapons;
		}

		public WDist MaxRange => Weapons.Length == 0 ? WDist.Zero : Weapons.Max(w => w.Range);

		/// <summary>Damage per tick this unit deals to one `target`: every weapon that may hit it, scaled by Versus.</summary>
		public double DamagePerTickAgainst(BotUnitProfile target)
		{
			var total = 0.0;
			foreach (var w in Weapons)
				if (w.CanTarget(target.TargetTypes))
					total += w.DamagePerTick * (target.Armor == null ? 100 : w.Versus.GetValueOrDefault(target.Armor, 100)) / 100.0;

			return total;
		}
	}

	public readonly struct BotWeaponProfile
	{
		public readonly double DamagePerTick;
		public readonly WDist Range;
		public readonly BitSet<TargetableType> Valid;
		public readonly BitSet<TargetableType> Invalid;
		public readonly IReadOnlyDictionary<string, int> Versus;

		public BotWeaponProfile(double damagePerTick, WDist range, BitSet<TargetableType> valid, BitSet<TargetableType> invalid,
			IReadOnlyDictionary<string, int> versus)
		{
			DamagePerTick = damagePerTick;
			Range = range;
			Valid = valid;
			Invalid = invalid;
			Versus = versus ?? new Dictionary<string, int>();
		}

		public bool CanTarget(BitSet<TargetableType> targetTypes) => Valid.Overlaps(targetTypes) && !Invalid.Overlaps(targetTypes);

		/// <summary>Ticks per full cycle: the burst's gaps, then the reload (the charge-cycle law's first two terms).</summary>
		public static int CycleTicks(int reloadDelay, int burst, IReadOnlyList<int> burstDelays)
		{
			var cycle = Math.Max(1, reloadDelay);
			for (var shot = 0; shot < burst - 1; shot++)
				cycle += burstDelays == null || burstDelays.Count == 0 ? 0
					: burstDelays.Count == 1 ? burstDelays[0] : burstDelays[Math.Min(shot, burstDelays.Count - 1)];

			return cycle;
		}
	}

	public static class BotUnitProfiles
	{
		static readonly ConditionalWeakTable<Ruleset, Dictionary<string, BotUnitProfile>> Cache = new();

		public static BotUnitProfile Get(Ruleset rules, ActorInfo actor)
		{
			var byName = Cache.GetOrCreateValue(rules);
			lock (byName)
			{
				if (!byName.TryGetValue(actor.Name, out var profile))
					byName[actor.Name] = profile = Build(rules, actor);

				return profile;
			}
		}

		static BotUnitProfile Build(Ruleset rules, ActorInfo actor)
		{
			var weapons = new List<BotWeaponProfile>();
			foreach (var armament in actor.TraitInfos<ArmamentInfo>().Where(a => a.EnabledByDefault))
			{
				if (armament.Weapon == null || !rules.Weapons.TryGetValue(armament.Weapon.ToLowerInvariant(), out var weapon))
					continue;

				// The largest positive damage warhead is the weapon's main one (W24), as the counter picker reads it.
				var main = weapon.Warheads.OfType<DamageWarhead>().Where(d => d.Damage > 0).OrderByDescending(d => d.Damage).FirstOrDefault();
				if (main == null)
					continue;

				var cycle = BotWeaponProfile.CycleTicks(weapon.ReloadDelay, weapon.Burst, weapon.BurstDelays);
				weapons.Add(new BotWeaponProfile((double)main.Damage * Math.Max(1, weapon.Burst) / cycle, weapon.Range,
					weapon.ValidTargets, weapon.InvalidTargets, main.Versus));
			}

			var speed = actor.TraitInfoOrDefault<MobileInfo>()?.Speed ?? actor.TraitInfoOrDefault<AircraftInfo>()?.Speed ?? 0;
			return new BotUnitProfile(actor.Name,
				actor.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0,
				actor.TraitInfoOrDefault<IHealthInfo>()?.MaxHP ?? 0,
				actor.TraitInfos<ArmorInfo>().FirstOrDefault(a => a.EnabledByDefault)?.Type,
				speed,
				actor.HasTraitInfo<AircraftInfo>(),
				actor.HasTraitInfo<BuildingInfo>(),
				actor.GetAllTargetTypes(),
				weapons.ToArray());
		}
	}

	/// <summary>
	/// Lanchester square-law prediction of a fight between two forces (AI_DEEP_RESEARCH.md §2: Stanescu et al.,
	/// AIIDE 2013/2015). With x, y the surviving HP fractions, dx/dt = -b·y and dy/dt = -a·x, where a is side A's
	/// damage per tick over side B's total HP and b the reverse; a·x² − b·y² is invariant, so A wins when
	/// DPS_A·HP_A > DPS_B·HP_B and keeps √(1 − b/a) of its HP. Each unit's damage is spread over the enemy by
	/// HP share (no focus fire, no range or terrain advantage — deliberately simple; learned per-type factors
	/// correct it later, CA-1b).
	/// </summary>
	public static class BotCombatPredictor
	{
		public readonly record struct Prediction(double Ratio, double OwnSurvivingFraction, double EnemySurvivingFraction)
		{
			/// <summary>`Ratio` > 1: the own side wins. Capped so an undefended enemy does not print infinity.</summary>
			public bool OwnWins => Ratio > 1;
		}

		public const double MaxRatio = 100;

		/// <summary>The pure square law on aggregates: damage per tick against the other side, and total HP.</summary>
		public static Prediction Predict(double ownDamagePerTick, double ownHp, double enemyDamagePerTick, double enemyHp)
		{
			var own = ownDamagePerTick * ownHp;
			var enemy = enemyDamagePerTick * enemyHp;
			if (own <= 0 && enemy <= 0)
				return new Prediction(1, ownHp > 0 ? 1 : 0, enemyHp > 0 ? 1 : 0);
			if (enemy <= 0)
				return new Prediction(MaxRatio, 1, 0);
			if (own <= 0)
				return new Prediction(0, 0, 1);

			var ratio = Math.Min(MaxRatio, own / enemy);
			return ratio >= 1
				? new Prediction(ratio, Math.Sqrt(1 - 1 / ratio), 0)
				: new Prediction(ratio, 0, Math.Sqrt(1 - ratio));
		}

		/// <summary>Two forces given as (profile, count); damage is spread over the other side by HP share.</summary>
		public static Prediction Predict(IReadOnlyList<(BotUnitProfile Unit, int Count)> own, IReadOnlyList<(BotUnitProfile Unit, int Count)> enemy)
		{
			var ownHp = own.Sum(u => (double)u.Unit.Hp * u.Count);
			var enemyHp = enemy.Sum(u => (double)u.Unit.Hp * u.Count);
			return Predict(DamagePerTick(own, enemy, enemyHp), ownHp, DamagePerTick(enemy, own, ownHp), enemyHp);
		}

		static double DamagePerTick(IReadOnlyList<(BotUnitProfile Unit, int Count)> attackers,
			IReadOnlyList<(BotUnitProfile Unit, int Count)> targets, double targetHp)
		{
			if (targetHp <= 0)
				return 0;

			var total = 0.0;
			foreach (var (attacker, count) in attackers)
				foreach (var (target, targetCount) in targets)
					total += count * attacker.DamagePerTickAgainst(target) * target.Hp * targetCount / targetHp;

			return total;
		}
	}
}
