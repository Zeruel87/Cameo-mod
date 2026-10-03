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
using System.Collections.Frozen;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Warheads;
using OpenRA.Primitives;
using OpenRA.Support;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	[TraitLocation(SystemActors.Player)]
	[Desc("The merged unit/target roles system (AI_ARCHITECTURE.md §12.4, CA-3, DESIGN §19.3):",
		"each actor's role set = its declared BotRoles entries + this player's BotRoleSets",
		"derivations + the statistical classifier below for whatever those leave unroled.",
		"Served to the CA bot modules through IBotUnitRoles; with no enabled provider every",
		"consumer stays inert, which is how `classic` keeps upstream behaviour verbatim.")]
	public class BotUnitRolesInfo : ConditionalTraitInfo
	{
		public override object Create(ActorInitializer init) { return new BotUnitRoles(this); }

		// role -> member actor names (resolved once per ruleset).
		public IReadOnlyDictionary<string, HashSet<string>> RoleMembers { get; private set; } =
			new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);

		// actor name -> roles.
		public IReadOnlyDictionary<string, HashSet<string>> ActorRoles { get; private set; } =
			new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);

		public override void RulesetLoaded(Ruleset rules, ActorInfo info)
		{
			base.RulesetLoaded(rules, info);

			var actorRoles = new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);
			void Add(string name, string role)
			{
				if (!actorRoles.TryGetValue(name, out var set))
					actorRoles[name] = set = new HashSet<string>(StringComparer.Ordinal);
				set.Add(role);
			}

			// Declared + derived roles first: the same ComputeMembers pass the Player's
			// BotRoleSets runs (the derivation predicates are written once, there).
			var sets = info.TraitInfos<BotRoleSetsInfo>().ToList();
			if (sets.Count > 0)
			{
				foreach (var roleSets in sets)
					foreach (var (role, names) in roleSets.ComputeMembers(rules, info))
						foreach (var name in names)
							Add(name, role);
			}
			else
			{
				// No BotRoleSets on this actor: declared BotRoles entries still count.
				foreach (var a in rules.Actors.Values.Where(a => !a.Name.StartsWith('^')))
					foreach (var role in a.TraitInfoOrDefault<BotRolesInfo>()?.Roles ?? FrozenSet<string>.Empty)
						Add(a.Name, role);
			}

			// Statistics fill gaps: the classifier only claims actors the yaml system left
			// unroled — a declared `firesupport`/`guerrilla` stays authoritative over a
			// statistical `frontline` (yaml first, statistics fill gaps).
			var statistics = BotUnitRoles.BuildRoleMap(rules);
			foreach (var kv in statistics)
			{
				if (kv.Value.Count == 0)
					continue;

				if (!actorRoles.TryGetValue(kv.Key, out var existing) || existing.Count == 0)
					actorRoles[kv.Key] = kv.Value;
			}

			var members = new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);
			foreach (var kv in actorRoles)
				foreach (var role in kv.Value)
				{
					if (!members.TryGetValue(role, out var set))
						members[role] = set = new HashSet<string>(StringComparer.Ordinal);
					set.Add(kv.Key);
				}

			ActorRoles = actorRoles;
			RoleMembers = members;

			Log.AddChannel("bot-roles", "bot-roles.log");
			foreach (var role in members.Keys.OrderBy(r => r, StringComparer.Ordinal))
				Log.Write("bot-roles",
					$"{info.Name} BotUnitRoles role `{role}`: {members[role].Count} members: {string.Join(", ", members[role].OrderBy(m => m, StringComparer.Ordinal))}");
		}
	}

	public class BotUnitRoles : ConditionalTrait<BotUnitRolesInfo>, IBotUnitRoles
	{
		// A weapon counts toward an anti-* role when it deals at least this much
		// (percent) against the armor class and more than against the other class.
		const int SpecializedVersus = 110;

		static readonly BitSet<TargetableType> AirTargets = new("Air");
		static readonly BitSet<TargetableType> GroundTargets = new("Ground");
		static readonly BitSet<TargetableType> HealRepairTargets = new("Heal", "Repair");
		static readonly BitSet<TargetableType> InfantryTargets = new("Infantry");
		static readonly BitSet<TargetableType> VehicleTargets = new("Vehicle", "Ship", "Structure");

		public BotUnitRoles(BotUnitRolesInfo info) : base(info) { }

		public IReadOnlyDictionary<string, HashSet<string>> RoleMembers => Info.RoleMembers;
		public IReadOnlyDictionary<string, HashSet<string>> ActorRoles => Info.ActorRoles;

		public string PrimaryRoleOf(string actorName) =>
			ActorRoles.TryGetValue(actorName, out var roles) ? PrimaryRole(roles) : null;

		// The single role a unit counts toward for composition accounting: first match in
		// PrimaryRoleOrder, so specialists claim before `frontline` keeps the tank mass.
		public static string PrimaryRole(IReadOnlySet<string> roles)
		{
			if (roles == null)
				return null;

			foreach (var role in BotUnitRole.PrimaryRoleOrder)
				if (roles.Contains(role))
					return role;

			return null;
		}

		// The per-actor facts the statistical classifier reads — public so the merged
		// map and the unit tests share one contract. Collect() fills it from the ruleset.
		public sealed class RoleFacts
		{
			public bool Mobile, Aircraft, Building, Attacks, Cargo, Reveals, Repairs;
			public int Health, Speed, Cost;
			public int MaxRange;
			public bool CanHitAir, CanHitGround, CanHeal;
			public int VersusInfantry, VersusVehicle;
			public bool VTOL;
			public int PowerAmount;
			public bool HitsInfantryType, CantHitInfantry, HitsVehicleType, CantHitVehicle;
			public bool GivesTech;
		}

		// The statistical classifier (CA-3): ruleset facts -> roles for one actor.
		// Pure — the unit tests drive it with synthetic RoleFacts.
		public static HashSet<string> ClassifyRoles(RoleFacts f, int hpCut, int speedCut, int costCut)
		{
			var set = new HashSet<string>(StringComparer.Ordinal);

			if (f.Building)
			{
				if (f.PowerAmount > 0)
					set.Add(BotUnitRole.Power);
				if (f.Attacks)
					set.Add(BotUnitRole.Defence);
				if (f.GivesTech)
					set.Add(BotUnitRole.Tech);
				return set;
			}

			if (!f.Mobile && !f.Aircraft)
				return set;

			if (f.Cargo)
				set.Add(f.Aircraft ? BotUnitRole.AirTransport : BotUnitRole.Transport);

			if (f.Repairs || f.CanHeal)
				set.Add(BotUnitRole.Support);

			if (!f.Attacks)
			{
				if (f.Mobile && f.Reveals && f.Speed >= speedCut && f.Cost <= costCut)
					set.Add(BotUnitRole.Scout);
				return set;
			}

			if (f.Aircraft)
			{
				if (f.VTOL && f.CanHitGround)
					set.Add(BotUnitRole.Gunship);
				if (f.CanHitAir)
					set.Add(BotUnitRole.Fighter);
				if (!f.VTOL && !f.CanHitAir && f.CanHitGround)
					set.Add(BotUnitRole.Bomber);
				return set;
			}

			// Mobile ground combat from here on.
			var ground = f.Mobile && !f.Aircraft;
			if (!ground)
				return set;

			if (f.MaxRange >= BotTargetTags.ArtilleryMinRange)
				set.Add(BotUnitRole.Artillery);
			if (f.CanHitAir)
				set.Add(BotUnitRole.AntiAir);
			if (f.Health >= hpCut && f.MaxRange < BotTargetTags.ArtilleryMinRange)
				set.Add(BotUnitRole.Frontline);
			else if (f.Speed >= speedCut)
				set.Add(BotUnitRole.Skirmisher);
			if (f.Reveals && f.Speed >= speedCut && f.Cost <= costCut)
				set.Add(BotUnitRole.Scout);

			// Anti-* specialisations, two complementary signals:
			// (a) the pooled Versus profile (fires where armour classes differ per unit class);
			// (b) explicit type targeting — a weapon that declares Infantry but not Vehicle is
			//     anti-infantry, and `InvalidTargets: Infantry` marks an anti-armour weapon.
			// Shared armour ladders can leave (a) empty without making (b) wrong.
			if (f.VersusInfantry >= SpecializedVersus && f.VersusInfantry > f.VersusVehicle
				|| f.HitsInfantryType && (f.CantHitVehicle || !f.HitsVehicleType))
				set.Add(BotUnitRole.AntiInfantry);
			if (f.VersusVehicle >= SpecializedVersus && f.VersusVehicle > f.VersusInfantry
				|| f.HitsVehicleType && (f.CantHitInfantry || !f.HitsInfantryType))
				set.Add(BotUnitRole.AntiArmour);

			return set;
		}

		public static IReadOnlyDictionary<string, HashSet<string>> BuildRoleMap(Ruleset rules)
		{
			var actors = rules.Actors.Values
				.Where(a => !a.Name.StartsWith('^'))
				.ToList();

			// Armour classes are pooled from the production-queue categories:
			// what "infantry" or "vehicle" means is read out of the ruleset, never typed.
			var infantryArmors = ArmorsOfQueue(actors, "Infantry");
			var vehicleArmors = ArmorsOfQueue(actors, "Vehicle");

			var facts = actors.ToDictionary(a => a.Name, a => Collect(a, rules, infantryArmors, vehicleArmors), StringComparer.Ordinal);

			// Faction-independent percentile bands over the mobile combat pool.
			var mobileCombat = facts.Values.Where(f => f.Mobile && f.Attacks && !f.Aircraft && !f.Building).ToList();
			var hpCut = Percentile(mobileCombat.Select(f => f.Health), 60);
			var speedCut = Percentile(mobileCombat.Select(f => f.Speed), 75);
			var costCut = Percentile(mobileCombat.Select(f => f.Cost), 50);

			var roles = new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);
			foreach (var a in actors)
				roles[a.Name] = ClassifyRoles(facts[a.Name], hpCut, speedCut, costCut);

			return roles;
		}

		// The three specialties of a static defence (AntiInfantry / AntiArmour / AntiAir) from the SAME classifier: a
		// building's own role set only says `defence`, so each attacking building is run through ClassifyRoles as a
		// mobile ground combatant (same RoleFacts, same Versus / target-type predicates; the percentile cuts only
		// feed frontline / skirmisher / scout, which are discarded here). Used by DefenseCoveragePlanner.
		public static IReadOnlyDictionary<string, HashSet<string>> BuildDefenceSpecialties(Ruleset rules)
		{
			var actors = rules.Actors.Values.Where(a => !a.Name.StartsWith('^')).ToList();
			var infantryArmors = ArmorsOfQueue(actors, "Infantry");
			var vehicleArmors = ArmorsOfQueue(actors, "Vehicle");

			var result = new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);
			foreach (var a in actors.Where(a => a.HasTraitInfo<BuildingInfo>() && a.HasTraitInfo<AttackBaseInfo>()))
			{
				var f = Collect(a, rules, infantryArmors, vehicleArmors);
				f.Building = false;
				f.Mobile = true;
				var roles = ClassifyRoles(f, int.MaxValue, int.MaxValue, 0);
				roles.IntersectWith(new[] { BotUnitRole.AntiInfantry, BotUnitRole.AntiArmour, BotUnitRole.AntiAir });
				result[a.Name] = roles;
			}

			return result;
		}

		static HashSet<string> ArmorsOfQueue(List<ActorInfo> actors, string queue)
		{
			var set = new HashSet<string>(StringComparer.Ordinal);
			foreach (var a in actors)
			{
				if (!a.TraitInfos<BuildableInfo>().Any(b => b.Queue != null &&
					b.Queue.Any(q => q.StartsWith(queue, StringComparison.OrdinalIgnoreCase))))
					continue;

				var armor = a.TraitInfos<ArmorInfo>().FirstOrDefault(x => x.InstanceName == null)?.Type;
				if (armor != null)
					set.Add(armor);
			}

			return set;
		}

		// A building earns the `tech` target tag when it provides a prerequisite whose
		// name carries the tech marker — faction-agnostic across every ContentPack.
		// An unset Prerequisite defaults to the actor's own name, like the trait does.
		static bool GivesTechPrerequisite(ActorInfo a)
		{
			return a.TraitInfos<ProvidesPrerequisiteInfo>().Any(p =>
				(p.Prerequisite ?? a.Name).IndexOf("tech", StringComparison.OrdinalIgnoreCase) >= 0);
		}

		static RoleFacts Collect(ActorInfo a, Ruleset rules, HashSet<string> infantryArmors, HashSet<string> vehicleArmors)
		{
			var f = new RoleFacts
			{
				Mobile = a.HasTraitInfo<MobileInfo>(),
				Aircraft = a.HasTraitInfo<AircraftInfo>(),
				Building = a.HasTraitInfo<BuildingInfo>(),
				Attacks = a.HasTraitInfo<AttackBaseInfo>(),
				Cargo = a.HasTraitInfo<CargoInfo>(),
				Reveals = a.HasTraitInfo<RevealsShroudInfo>(),
				Repairs = a.HasTraitInfo<RepairsUnitsInfo>(),
				VTOL = a.TraitInfos<AircraftInfo>().FirstOrDefault()?.VTOL ?? false,
				Health = a.TraitInfos<HealthInfo>().Select(h => h.HP).DefaultIfEmpty().Max(),
				Speed = a.TraitInfos<MobileInfo>().Select(m => m.Speed).DefaultIfEmpty().Max(),
				Cost = a.TraitInfos<ValuedInfo>().Select(v => v.Cost).DefaultIfEmpty().Min(),
				PowerAmount = a.TraitInfos<PowerInfo>().Sum(p => p.Amount),
				GivesTech = GivesTechPrerequisite(a)
			};

			// Same evaluation as BotRoleSets.WeaponTargets: EnabledByDefault is not
			// trustworthy at ruleset-load time, so conditions are evaluated directly.
			foreach (var armament in a.TraitInfos<ArmamentInfo>()
				.Where(x => x.RequiresCondition == null || x.RequiresCondition.Evaluate(VariableExpression.NoVariables)))
			{
				if (armament.Weapon == null || !rules.Weapons.TryGetValue(armament.Weapon.ToLowerInvariant(), out var weapon))
					continue;

				if (weapon.ValidTargets.Overlaps(AirTargets))
					f.CanHitAir = true;
				if (weapon.ValidTargets.Overlaps(GroundTargets))
					f.CanHitGround = true;
				if (weapon.ValidTargets.Overlaps(HealRepairTargets))
					f.CanHeal = true;
				if (weapon.ValidTargets.Overlaps(InfantryTargets))
					f.HitsInfantryType = true;
				if (weapon.ValidTargets.Overlaps(VehicleTargets))
					f.HitsVehicleType = true;
				if (weapon.InvalidTargets.Overlaps(InfantryTargets))
					f.CantHitInfantry = true;
				if (weapon.InvalidTargets.Overlaps(VehicleTargets))
					f.CantHitVehicle = true;
				if (weapon.Range.Length > f.MaxRange)
					f.MaxRange = weapon.Range.Length;

				// The scoring profile AdaptiveCounterProduction uses: the highest-damage
				// DamageWarhead's Versus, read against each pooled armour class.
				var main = weapon.Warheads.OfType<DamageWarhead>().Where(d => d.Damage > 0)
					.OrderByDescending(d => d.Damage).FirstOrDefault();
				if (main == null)
					continue;

				f.VersusInfantry = Math.Max(f.VersusInfantry, BestVersus(main, infantryArmors));
				f.VersusVehicle = Math.Max(f.VersusVehicle, BestVersus(main, vehicleArmors));
			}

			return f;
		}

		static int BestVersus(DamageWarhead warhead, HashSet<string> armors)
		{
			var best = 0;
			foreach (var armor in armors)
				best = Math.Max(best, warhead.Versus.GetValueOrDefault(armor, 100));
			return best;
		}

		internal static int Percentile(IEnumerable<int> values, int percentile)
		{
			var sorted = values.Where(v => v > 0).OrderBy(v => v).ToArray();
			return sorted.Length == 0 ? int.MaxValue : sorted[(sorted.Length - 1) * percentile / 100];
		}
	}
}
