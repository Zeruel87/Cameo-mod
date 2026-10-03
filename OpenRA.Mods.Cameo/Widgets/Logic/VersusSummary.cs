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
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Warheads;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Widgets.Logic
{
	/// <summary>
	/// What a unit's weapons do to each armour class, read from the RESOLVED rules at runtime, so the
	/// production tooltip can never disagree with the warheads (maintainer ruling 2026-09-23, ROADMAP
	/// "three ideas from Combined Arms' damage model").
	///
	/// The armour ladders are DESIGN §12.0d's, each ordered lightest -> heaviest. `Heroic` is left out:
	/// it is a DERIVED cell (§12.0b), not a rung. Protection layers (Shield, HAZMAT, ...) are not
	/// ladders either.
	/// </summary>
	public sealed class VersusSummary
	{
		public enum LadderKind { Infantry, Vehicles, Buildings, Aircraft }

		public static readonly (LadderKind Kind, string[] Rungs, string[] TargetTypes)[] Ladders =
		[
			(LadderKind.Infantry, ["None", "Flak", "Plate"], ["Ground", "Infantry"]),
			(LadderKind.Vehicles, ["Scout", "Light", "Medium", "Heavy", "Superheavy"], ["Ground", "Water", "Vehicle"]),
			(LadderKind.Buildings, ["Wood", "Steel", "Concrete"], ["Ground", "Structure"]),
			(LadderKind.Aircraft, ["Fighter", "Helicopter", "Bomber", "Spaceship"], ["Air"]),
		];

		/// <summary>A profile whose strongest rung beats its weakest by less than this is FLAT (§12.0d "Super").</summary>
		const int FlatRatioPercent = 115;

		public readonly struct Ladder
		{
			public readonly LadderKind Kind;

			/// <summary>Null when no weapon of the unit can target this ladder.</summary>
			public readonly (string Armor, int Percent)[] Rungs;

			public Ladder(LadderKind kind, (string, int)[] rungs)
			{
				Kind = kind;
				Rungs = rungs;
			}

			public bool CanAttack => Rungs != null;
		}

		public readonly Ladder[] Rows;

		/// <summary>
		/// The vehicle ladder peaks on its HEAVIEST rungs (`Heavy`/`Superheavy`, §12.0d's heavy end) and is
		/// not flat. Maintainer 2026-09-23: show "Armor Piercing" for anti-heavy, and no tag otherwise.
		/// </summary>
		public readonly bool ArmorPiercing;

		/// <summary>Target DOMAINS any of the unit's weapons can hit, in <see cref="Domains"/> order.</summary>
		public readonly string[] Targets;

		/// <summary>The target types shown on the tooltip's "Targets" line, in display order.</summary>
		public static readonly string[] Domains = ["Ground", "Water", "Underwater", "Air"];

		/// <summary>Ground target classes, listed only when a unit cannot hit `Ground` as a whole.</summary>
		public static readonly string[] GroundClasses = ["Infantry", "Vehicle", "Structure"];

		public bool HasWeapons => Rows.Any(r => r.CanAttack);

		VersusSummary(Ladder[] rows, bool armorPiercing, string[] targets)
		{
			Rows = rows;
			ArmorPiercing = armorPiercing;
			Targets = targets;
		}

		/// <summary>
		/// The unit GROUPS the tooltip's Strong / Medium / Weak lines speak about (maintainer 2026-09-28). A group's
		/// percentage is the geometric mean of the weapon's Versus over the armour its members WEAR, each armour
		/// weighted by how many buildable members of the group wear it, so the number describes the units a
		/// player actually meets and follows DESIGN §12.0l's re-armouring without a code change.
		/// </summary>
		public enum Group { Infantry, Heroes, Vehicles, Tanks, Ships, Submarines, Buildings, Defenses, Aircraft }

		/// <summary>What a member of each group is targetable as; a weapon must overlap it and not be invalid for it.</summary>
		public static readonly (Group Group, BitSet<TargetableType> TargetTypes, bool Naval)[] Groups =
		[
			(Group.Infantry, new BitSet<TargetableType>("Ground", "Infantry"), false),
			(Group.Heroes, new BitSet<TargetableType>("Ground", "Infantry"), false),
			(Group.Vehicles, new BitSet<TargetableType>("Ground", "Vehicle"), false),
			(Group.Tanks, new BitSet<TargetableType>("Ground", "Vehicle"), false),
			(Group.Ships, new BitSet<TargetableType>("Water", "Ship"), true),
			(Group.Submarines, new BitSet<TargetableType>("Underwater"), true),
			(Group.Buildings, new BitSet<TargetableType>("Ground", "Structure"), false),
			(Group.Defenses, new BitSet<TargetableType>("Ground", "Structure", "Defense"), false),
			(Group.Aircraft, new BitSet<TargetableType>("Air"), false),
		];

		/// <summary>Bands, symmetric around 100 on the geometric scale (x1.25 and /1.25). Maintainer 2026-09-28.</summary>
		public const int StrongPercent = 125;
		public const int WeakPercent = 80;

		/// <summary>The six tank class templates each leave a `TooltipExtras@&lt;Class&gt;` on the actor.</summary>
		static readonly string[] TankClasses = ["MainBattleTank", "HighTechTank", "Dreadnought", "TankDestroyer", "ArtilleryTank", "LightTank"];

		static readonly ConditionalWeakTable<Ruleset, Dictionary<Group, Dictionary<string, int>>> WeightCache = new();

		/// <summary>One group's value for this unit: null when none of its weapons can hit the group.</summary>
		public readonly struct GroupValue
		{
			public readonly Group Group;
			public readonly int? Percent;

			public GroupValue(Group group, int? percent)
			{
				Group = group;
				Percent = percent;
			}
		}

		/// <summary>Every group present in the rules (and allowed by the lobby), in <see cref="Group"/> order.</summary>
		public GroupValue[] GroupValues { get; private set; } = [];

		/// <summary>The group a buildable unit belongs to, or null (upgrades, doctrines, anything not a unit).</summary>
		internal static Group? GroupOf(ActorInfo actor)
		{
			if (actor.HasTraitInfo<AircraftInfo>())
				return Group.Aircraft;

			if (actor.HasTraitInfo<BuildingInfo>())
				return actor.HasTraitInfo<ArmamentInfo>() ? Group.Defenses : Group.Buildings;

			var targetables = actor.TraitInfos<TargetableInfo>().ToList();
			if (targetables.Any(t => t.TargetTypes.Contains("Underwater")))
				return Group.Submarines;

			var mobile = actor.TraitInfos<MobileInfo>().FirstOrDefault();
			var locomotor = mobile?.Locomotor?.ToLowerInvariant() ?? "";
			if (locomotor.Contains("naval") || locomotor.Contains("water") || locomotor.Contains("ship") || locomotor.Contains("sub"))
				return Group.Ships;

			if (targetables.Any(t => t.TargetTypes.Contains("Infantry")))
				return MainArmor(actor) == "Heroic" ? Group.Heroes : Group.Infantry;

			if (actor.TraitInfos<TooltipExtrasInfo>().Any(t => TankClasses.Contains(t.InstanceName)))
				return Group.Tanks;

			if (mobile != null || targetables.Any(t => t.TargetTypes.Contains("Vehicle")))
				return Group.Vehicles;

			return null;
		}

		/// <summary>The unnamed, unconditional `Armor` trait: the class armour (Shield and HAZMAT are layers).</summary>
		static string MainArmor(ActorInfo actor)
		{
			return actor.TraitInfos<ArmorInfo>().FirstOrDefault(a => a.InstanceName == null && a.EnabledByDefault)?.Type;
		}

		/// <summary>Per group, how many buildable members wear each armour. Built once per ruleset.</summary>
		internal static Dictionary<Group, Dictionary<string, int>> ArmorWeights(Ruleset rules)
		{
			return WeightCache.GetValue(rules, r =>
			{
				var weights = new Dictionary<Group, Dictionary<string, int>>();
				foreach (var actor in r.Actors.Values)
				{
					if (actor.Name.StartsWith('^') || !actor.TraitInfos<BuildableInfo>().Any(b => b.Queue.Count > 0))
						continue;

					var group = GroupOf(actor);
					var armor = MainArmor(actor);
					if (group == null || armor == null)
						continue;

					if (!weights.TryGetValue(group.Value, out var counts))
						weights[group.Value] = counts = new Dictionary<string, int>();

					counts[armor] = counts.GetValueOrDefault(armor) + 1;
				}

				return weights;
			});
		}

		/// <summary>Weighted geometric mean of a Versus table over one group's worn armour.</summary>
		internal static int GroupPercent(IReadOnlyDictionary<string, int> versus, Dictionary<string, int> weights)
		{
			double logSum = 0, total = 0;
			foreach (var (armor, count) in weights)
			{
				logSum += count * Math.Log(Math.Max(1, versus.GetValueOrDefault(armor, 100)));
				total += count;
			}

			return total > 0 ? (int)Math.Round(Math.Exp(logSum / total)) : 100;
		}

		/// <summary>
		/// Sorts group values into the three tooltip lines. Within a line the strongest group comes first; groups the
		/// unit cannot hit close the Weak line, in <see cref="Group"/> order.
		/// </summary>
		public static (List<GroupValue> Strong, List<GroupValue> Medium, List<GroupValue> Weak) Bands(IEnumerable<GroupValue> values)
		{
			var all = values.ToList();
			var hit = all.Where(v => v.Percent != null).OrderByDescending(v => v.Percent.Value).ToList();
			return (
				hit.Where(v => v.Percent >= StrongPercent).ToList(),
				hit.Where(v => v.Percent >= WeakPercent && v.Percent < StrongPercent).ToList(),
				hit.Where(v => v.Percent < WeakPercent).Concat(all.Where(v => v.Percent == null)).ToList());
		}

		static bool CanHit(WeaponInfo weapon, BitSet<TargetableType> targetTypes)
		{
			return weapon.ValidTargets.Overlaps(targetTypes) && !weapon.InvalidTargets.Overlaps(targetTypes);
		}

		/// <summary>The ladder summary plus the per-group values; `naval` is the lobby's Naval Units option.</summary>
		public static VersusSummary For(ActorInfo actor, Ruleset rules, bool naval)
		{
			var summary = For(actor, rules);
			var weapons = Weapons(actor, rules);
			var weights = ArmorWeights(rules);
			var values = new List<GroupValue>();
			foreach (var (group, targetTypes, isNaval) in Groups)
			{
				if ((isNaval && !naval) || !weights.TryGetValue(group, out var worn))
					continue;

				// As for the ladders: the strongest weapon that can hit the group speaks for it.
				var best = weapons.Where(w => CanHit(w.Weapon, targetTypes)).OrderByDescending(w => w.Potency).FirstOrDefault();
				values.Add(new GroupValue(group, best.Weapon == null ? null : GroupPercent(best.Warhead.Versus, worn)));
			}

			summary.GroupValues = values.ToArray();
			return summary;
		}

		public static VersusSummary For(ActorInfo actor, Ruleset rules)
		{
			var weapons = Weapons(actor, rules);
			var rows = new Ladder[Ladders.Length];
			var armorPiercing = false;

			for (var i = 0; i < Ladders.Length; i++)
			{
				var (kind, rungs, targetTypes) = Ladders[i];

				// The strongest weapon that can hit this ladder speaks for it: a sidearm's profile must not
				// mask the main gun's.
				var best = weapons
					.Where(w => CanTarget(w.Weapon, targetTypes))
					.OrderByDescending(w => w.Potency)
					.FirstOrDefault();

				if (best.Weapon == null)
				{
					rows[i] = new Ladder(kind, null);
					continue;
				}

				var values = rungs.Select(r => (r, best.Warhead.Versus.GetValueOrDefault(r, 100))).ToArray();
				rows[i] = new Ladder(kind, values);

				if (kind == LadderKind.Vehicles)
				{
					var max = values.Max(v => v.Item2);
					var min = values.Min(v => v.Item2);
					var peak = System.Array.FindLastIndex(values, v => v.Item2 == max);
					armorPiercing = max * 100 > min * FlatRatioPercent && peak >= rungs.Length - 2;
				}
			}

			// Domains first; a weapon that cannot hit `Ground` as a whole (a sniper rifle targets `Infantry`)
			// names the ground classes it CAN hit instead, so the line is never empty for an armed unit.
			var targets = Domains.Where(d => weapons.Any(w => CanTarget(w.Weapon, [d]))).ToList();
			if (!targets.Contains("Ground"))
				targets.InsertRange(0, GroundClasses.Where(c => weapons.Any(w => CanTarget(w.Weapon, [c]))));
			return new VersusSummary(rows, armorPiercing, targets.ToArray());
		}

		static List<(WeaponInfo Weapon, DamageWarhead Warhead, long Potency)> Weapons(ActorInfo actor, Ruleset rules)
		{
			var armaments = actor.TraitInfos<ArmamentInfo>().ToList();
			var innate = armaments.Where(a => a.EnabledByDefault).ToList();

			// A unit whose every armament is condition-gated (deploy modes, garrisons) still has weapons.
			var chosen = innate.Count > 0 ? innate : armaments;
			var result = new List<(WeaponInfo, DamageWarhead, long)>();
			foreach (var a in chosen)
			{
				if (a.Weapon == null || !rules.Weapons.TryGetValue(a.Weapon.ToLowerInvariant(), out var weapon))
					continue;

				// W24: one MAIN damage warhead per weapon. Where a weapon still stacks several, the largest
				// is its main one; twins and effect warheads are smaller or deal no damage.
				var main = weapon.Warheads.OfType<DamageWarhead>().Where(d => d.Damage > 0)
					.OrderByDescending(d => d.Damage).FirstOrDefault();
				if (main == null)
					continue;

				var potency = (long)main.Damage * weapon.Burst * 1000 / System.Math.Max(1, weapon.ReloadDelay);
				result.Add((weapon, main, potency));
			}

			return result;
		}

		static bool CanTarget(WeaponInfo weapon, string[] targetTypes)
		{
			return targetTypes.Any(t => weapon.ValidTargets.Contains(t) && !weapon.InvalidTargets.Contains(t));
		}

		/// <summary>Colour band for one percentage. MEAN-100 profiles centre on 100 (§12.0h).</summary>
		public static Color ColorFor(int percent)
		{
			if (percent >= 150)
				return Color.FromArgb(0x33, 0xEE, 0x55);
			if (percent >= 115)
				return Color.FromArgb(0x99, 0xDD, 0x66);
			if (percent >= 85)
				return Color.FromArgb(0xDD, 0xDD, 0xDD);
			if (percent >= 50)
				return Color.FromArgb(0xFF, 0xAA, 0x33);
			return Color.FromArgb(0xEE, 0x55, 0x55);
		}

		/// <summary>Rungs this unit is strong against (>= StrongPercent), in ladder order.</summary>
		public IEnumerable<string> Strong(int strongPercent = 130)
		{
			return Rows.Where(r => r.CanAttack).SelectMany(r => r.Rungs).Where(v => v.Percent >= strongPercent).Select(v => v.Armor);
		}

		/// <summary>Rungs this unit is weak against (&lt;= WeakPercent), in ladder order.</summary>
		public IEnumerable<string> Weak(int weakPercent = 50)
		{
			return Rows.Where(r => r.CanAttack).SelectMany(r => r.Rungs).Where(v => v.Percent <= weakPercent).Select(v => v.Armor);
		}

		public IEnumerable<LadderKind> CannotAttack()
		{
			return Rows.Where(r => !r.CanAttack).Select(r => r.Kind);
		}
	}
}
