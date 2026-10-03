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
using System.Collections.Immutable;
using System.Linq;
using System.Reflection;
using OpenRA.Mods.Common.Traits;
using OpenRA.Support;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	[Desc("What this actor is FOR, as far as the bots are concerned (AI_ARCHITECTURE.md §2.8).",
		"Declared on the actor in its own ContentPack, so that no central ai.yaml list has to name it.",
		"BotRoleSets turns roles into the bot modules' actor lists.")]
	public class BotRolesInfo : TraitInfo<BotRoles>
	{
		[FieldLoader.Require]
		[Desc("Role names, e.g. harvester, guerrilla, highvaluetarget.")]
		public readonly FrozenSet<string> Roles = FrozenSet<string>.Empty;
	}

	public class BotRoles { }

	[TraitLocation(SystemActors.Player)]
	[Desc("Fills bot-module actor lists from ROLES instead of central id lists, so a faction's AI is",
		"plug and play: an unloaded ContentPack contributes no actors and therefore no ids (AI_ARCHITECTURE.md §2.8,",
		"ruled 2026-09-27). A role's members are the actors with a matching BotRoles entry plus, if a derivation",
		"is configured, the actors whose traits match it. Runs once at rules load, identically on every client.",
		"A role is only APPLIED when listed in Apply; otherwise it writes what it would add to bot-roles.log.")]
	public class BotRoleSetsInfo : TraitInfo<BotRoleSets>, IRulesetLoaded
	{
		[Desc("Role -> trait types an actor must ALL have to get the role by derivation.",
			"Type names without the Info suffix; base classes count (a subclass of Harvester is a Harvester).")]
		public readonly Dictionary<string, string[]> DeriveHas = [];

		[Desc("Role -> trait types that block the derived role.")]
		public readonly Dictionary<string, string[]> DeriveNot = [];

		[Desc("Role -> field predicates an actor must ALL satisfy to get the role by derivation:",
			"`Trait.Field any v1|v2` (the field holds at least one of the values) or",
			"`Trait.Field only v1|v2` (the field holds values and every one of them is listed).",
			"The virtual `Weapons.ValidTargets` is the union of what the actor's enabled armaments' weapons may target",
			"(e.g. `Weapons.ValidTargets any Air` = can shoot aircraft).",
			"Trait is the type name without Info (base classes count); values compare case-insensitively.",
			"No commas inside a predicate: MiniYaml splits the list on them.")]
		public readonly Dictionary<string, string[]> DeriveHasField = [];

		[Desc("Role -> field predicates that block the derived role (same syntax as DeriveHasField).",
			"E.g. `refinery: Building.TerrainTypes only Water` keeps water-only refineries out of a land base's pick.")]
		public readonly Dictionary<string, string[]> DeriveNotField = [];

		[Desc("Role -> actors that never get the role by DERIVATION. An explicit BotRoles entry still applies.")]
		public readonly Dictionary<string, string[]> Exclude = [];

		[Desc("Only actors a queue can produce (Buildable with a Queue) get a derived role. Spawned slaves such as",
			"YRSLAV carry Buildable for its tooltip but no Queue: their master drives them, not the bot.")]
		public readonly bool DeriveOnlyBuildable = true;

		[Desc("Role -> the module list fields it fills, as TraitType.Field (every instance of that trait on this actor)",
			"or TraitType@instance.Field (that instance only, e.g. to leave the A/B reference bot's list as written).")]
		public readonly Dictionary<string, string[]> Targets = [];

		[Desc("Roles whose members are ADDED to their Targets. Any other role only reports to bot-roles.log.")]
		public readonly FrozenSet<string> Apply = FrozenSet<string>.Empty;

		// role -> member actor names: every actor's declared BotRoles entries plus this
		// instance's derivation config, resolved over the ruleset. Pure recompute — the
		// merged IBotUnitRoles provider (BotUnitRoles, same assembly) calls this to compose
		// its map, so the derivation predicates are written once, here (DESIGN §19.3).
		public Dictionary<string, HashSet<string>> ComputeMembers(Ruleset rules, ActorInfo owner)
		{
			var hasField = ParsePredicates(DeriveHasField);
			var notField = ParsePredicates(DeriveNotField);
			var fieldKeys = hasField.Values.Concat(notField.Values).SelectMany(p => p)
				.Select(p => (p.Trait, p.Field)).Distinct().ToList();
			var fieldSeen = new HashSet<(string, string)>();

			var actors = rules.Actors.Values
				.Where(a => !a.Name.StartsWith('^'))
				.Select(a => new RoleCandidate(
					a.Name,
					TraitTypeNames(a),
					a.TraitInfoOrDefault<BotRolesInfo>()?.Roles ?? FrozenSet<string>.Empty,
					a.TraitInfoOrDefault<BuildableInfo>()?.Queue.Count > 0,
					fieldKeys.Count == 0 ? null : fieldKeys.ToDictionary(k => k.Trait + "." + k.Field,
						k => k.Trait == WeaponsTrait
							? WeaponField(rules, a, k.Field, fieldSeen)
							: ReadField(a, k.Trait, k.Field, fieldSeen))))
				.ToList();

			// A predicate no trait can ever satisfy is a typo, not a filter: fail at rules load.
			foreach (var (trait, field) in fieldKeys)
				if (!fieldSeen.Contains((trait, field)))
					throw new YamlException($"BotRoleSets on {owner.Name}: no actor has a `{trait}` trait with a public field `{field}`");

			return ResolveMembers(actors, DeriveHas, DeriveNot, Exclude, DeriveOnlyBuildable, hasField, notField);
		}

		void IRulesetLoaded<ActorInfo>.RulesetLoaded(Ruleset rules, ActorInfo info)
		{
			var members = ComputeMembers(rules, info);

			Log.AddChannel("bot-roles", "bot-roles.log");
			foreach (var (role, targets) in Targets)
			{
				var roleMembers = members.GetValueOrDefault(role) ?? [];
				foreach (var target in targets)
				{
					var dot = target.LastIndexOf('.');
					if (dot <= 0)
						throw new YamlException($"BotRoleSets on {info.Name}: target `{target}` must be TraitType.Field or TraitType@instance.Field");

					var traitType = target[..dot];
					var fieldName = target[(dot + 1)..];
					var at = traitType.IndexOf('@');
					var instance = at < 0 ? null : traitType[(at + 1)..];
					if (at >= 0)
						traitType = traitType[..at];

					var traitInfos = info.TraitInfos<TraitInfo>()
						.Where(t => t.GetType().Name == traitType + "Info" && (instance == null || t.InstanceName == instance)).ToList();
					if (traitInfos.Count == 0)
						throw new YamlException($"BotRoleSets on {info.Name}: role `{role}` targets `{target[..dot]}`, which this actor does not have");

					foreach (var ti in traitInfos)
					{
						var field = ti.GetType().GetField(fieldName, BindingFlags.Public | BindingFlags.Instance)
							?? throw new YamlException($"BotRoleSets: `{traitType}` has no public field `{fieldName}`");
						var current = (field.GetValue(ti) as IEnumerable<string>)?.ToHashSet()
							?? throw new YamlException($"BotRoleSets: `{target}` is not a set of actor names");

						var added = roleMembers.Where(m => !current.Contains(m)).OrderBy(m => m, StringComparer.Ordinal).ToList();
						var writtenOnly = current.Where(c => !roleMembers.Contains(c)).OrderBy(c => c, StringComparer.Ordinal).ToList();
						var applied = Apply.Contains(role);
						Log.Write("bot-roles",
							$"{info.Name} {target} role `{role}`: {roleMembers.Count} members, {current.Count} written; " +
							$"{(applied ? "ADDED" : "would add")} {added.Count}: {string.Join(", ", added)}; " +
							$"written but not in role {writtenOnly.Count}: {string.Join(", ", writtenOnly)}");

						if (applied && added.Count > 0)
							field.SetValue(ti, Union(field.FieldType, current, added));
					}
				}
			}

			// AI_ARCHITECTURE.md §2.9 P0: every bot-module field as the engine now holds it (opt-in).
			BotModuleFieldDump.WriteIfRequested(info);
		}

		const string WeaponsTrait = "Weapons";
		const string ValidTargetsField = "ValidTargets";
		const string AirArmamentField = "AirArmament";

		static readonly IReadOnlySet<string> AirClasses = new[] { "Air", "Aircraft" }.ToFrozenSet(StringComparer.OrdinalIgnoreCase);

		static IReadOnlySet<string> WeaponField(Ruleset rules, ActorInfo a, string field, HashSet<(string, string)> seen)
		{
			if (field == ValidTargetsField)
				return WeaponTargets(rules, a, seen);

			if (field == AirArmamentField)
				return AirArmamentClasses(rules, a, seen);

			// Unknown Weapons.* virtual: never `seen`, so the typo guard rejects it.
			return FrozenSet<string>.Empty;
		}

		// The virtual `Weapons.AirArmament` (CA-5): the actor's air capability class.
		// `dedicated` = at least one enabled armament whose weapon may ONLY hit air
		// (a purpose-built interceptor like firehawk's missiles); `auxiliary` =
		// air-capable but every air armament also hits other things (a defensive gun
		// like the japanese bomber's chaingun). Empty = cannot hit air at all.
		static IReadOnlySet<string> AirArmamentClasses(Ruleset rules, ActorInfo a, HashSet<(string, string)> seen)
		{
			var airCapable = false;
			var dedicated = false;
			foreach (var armament in a.TraitInfos<ArmamentInfo>()
				.Where(x => x.RequiresCondition == null || x.RequiresCondition.Evaluate(VariableExpression.NoVariables)))
			{
				seen.Add((WeaponsTrait, AirArmamentField));
				if (armament.Weapon == null || !rules.Weapons.TryGetValue(armament.Weapon.ToLowerInvariant(), out var weapon))
					continue;

				var vt = weapon.ValidTargets.Select(t => t.ToString()).ToHashSet(StringComparer.OrdinalIgnoreCase);
				if (!vt.Overlaps(AirClasses))
					continue;

				airCapable = true;
				if (vt.All(AirClasses.Contains))
					dedicated = true;
			}

			if (dedicated)
				return new[] { "dedicated" }.ToFrozenSet();

			if (airCapable)
				return new[] { "auxiliary" }.ToFrozenSet();

			return FrozenSet<string>.Empty;
		}

		// The virtual `Weapons.ValidTargets`: what the actor's enabled armaments may hit, per their weapons.
		// ⚠ Not ArmamentInfo.EnabledByDefault: that is set in each actor's OWN RulesetLoaded, which may run after
		// this one (Player), so it would still read false. Evaluate the condition the same way instead.
		static IReadOnlySet<string> WeaponTargets(Ruleset rules, ActorInfo a, HashSet<(string, string)> seen)
		{
			var values = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
			foreach (var armament in a.TraitInfos<ArmamentInfo>()
				.Where(x => x.RequiresCondition == null || x.RequiresCondition.Evaluate(VariableExpression.NoVariables)))
			{
				seen.Add((WeaponsTrait, ValidTargetsField));
				if (armament.Weapon == null || !rules.Weapons.TryGetValue(armament.Weapon.ToLowerInvariant(), out var weapon))
					continue;

				foreach (var t in weapon.ValidTargets)
					values.Add(t);
			}

			return values;
		}

		// Trait type names of every trait on the actor, including base classes, without the Info suffix.
		static HashSet<string> TraitTypeNames(ActorInfo a)
		{
			var names = new HashSet<string>();
			foreach (var ti in a.TraitInfos<TraitInfo>())
				for (var t = ti.GetType(); t != null && t != typeof(TraitInfo) && t != typeof(object); t = t.BaseType)
					names.Add(t.Name.EndsWith("Info", StringComparison.Ordinal) ? t.Name[..^4] : t.Name);

			return names;
		}

		// Every value of Trait.Field over the actor's traits of that type (or a subclass), as strings.
		static IReadOnlySet<string> ReadField(ActorInfo a, string trait, string field, HashSet<(string, string)> seen)
		{
			var values = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
			foreach (var ti in a.TraitInfos<TraitInfo>())
			{
				if (!IsOrDerives(ti.GetType(), trait))
					continue;

				var f = ti.GetType().GetField(field, BindingFlags.Public | BindingFlags.Instance);
				if (f == null)
					continue;

				seen.Add((trait, field));
				foreach (var token in Tokens(f.GetValue(ti)))
					values.Add(token);
			}

			return values;
		}

		static bool IsOrDerives(Type t, string trait)
		{
			for (; t != null && t != typeof(TraitInfo) && t != typeof(object); t = t.BaseType)
				if (t.Name == trait + "Info")
					return true;

			return false;
		}

		static IEnumerable<string> Tokens(object value)
		{
			switch (value)
			{
				case null:
					yield break;
				case string s:
					yield return s;
					break;
				case Enum e:
					foreach (var part in e.ToString().Split(", "))
						yield return part;
					break;
				case System.Collections.IEnumerable items:
					foreach (var item in items)
						if (item != null)
							yield return item.ToString();
					break;
				default:
					yield return value.ToString();
					break;
			}
		}

		static Dictionary<string, FieldPredicate[]> ParsePredicates(Dictionary<string, string[]> byRole) =>
			byRole.ToDictionary(kv => kv.Key, kv => kv.Value.Select(FieldPredicate.Parse).ToArray());

		public sealed record FieldPredicate(string Trait, string Field, bool Only, FrozenSet<string> Values)
		{
			public string Key => Trait + "." + Field;

			public static FieldPredicate Parse(string text)
			{
				var parts = text.Split(' ', StringSplitOptions.RemoveEmptyEntries);
				var dot = parts.Length == 3 ? parts[0].LastIndexOf('.') : -1;
				if (dot <= 0 || dot == parts[0].Length - 1 || (parts[1] != "any" && parts[1] != "only"))
					throw new YamlException($"BotRoleSets: field predicate `{text}` must be `Trait.Field any|only v1|v2`");

				var values = parts[2].Split('|', StringSplitOptions.RemoveEmptyEntries).ToFrozenSet(StringComparer.OrdinalIgnoreCase);
				return new FieldPredicate(parts[0][..dot], parts[0][(dot + 1)..], parts[1] == "only", values);
			}

			// `any`: some field value is listed. `only`: the field has values and all of them are listed.
			public bool Matches(IReadOnlySet<string> fieldValues) =>
				fieldValues != null && fieldValues.Count > 0 &&
				(Only ? fieldValues.All(Values.Contains) : fieldValues.Any(Values.Contains));
		}

		public readonly record struct RoleCandidate(string Name, ISet<string> TraitTypes, IReadOnlySet<string> ExplicitRoles, bool Buildable,
			IReadOnlyDictionary<string, IReadOnlySet<string>> Fields = null)
		{
			public IReadOnlySet<string> FieldValues(string key) =>
				Fields != null && Fields.TryGetValue(key, out var v) ? v : FrozenSet<string>.Empty;
		}

		// Pure: role -> member actor names. Explicit BotRoles always count; derivations need every DeriveHas type,
		// none of the DeriveNot types, every DeriveHasField predicate, no DeriveNotField predicate, and
		// (optionally) Buildable, and are blocked by Exclude. A role may be derived from field predicates alone.
		public static Dictionary<string, HashSet<string>> ResolveMembers(
			IEnumerable<RoleCandidate> actors,
			IReadOnlyDictionary<string, string[]> deriveHas,
			IReadOnlyDictionary<string, string[]> deriveNot,
			IReadOnlyDictionary<string, string[]> exclude,
			bool deriveOnlyBuildable,
			IReadOnlyDictionary<string, FieldPredicate[]> deriveHasField = null,
			IReadOnlyDictionary<string, FieldPredicate[]> deriveNotField = null)
		{
			var derivedRoles = deriveHas.Keys.Concat(deriveHasField?.Keys ?? []).Distinct().ToArray();
			var members = new Dictionary<string, HashSet<string>>();
			HashSet<string> Of(string role)
			{
				if (!members.TryGetValue(role, out var set))
					members[role] = set = [];
				return set;
			}

			foreach (var a in actors)
			{
				foreach (var role in a.ExplicitRoles)
					Of(role).Add(a.Name);

				if (deriveOnlyBuildable && !a.Buildable)
					continue;

				foreach (var role in derivedRoles)
				{
					if (deriveHas.TryGetValue(role, out var has) && !has.All(a.TraitTypes.Contains))
						continue;
					if (deriveNot.TryGetValue(role, out var not) && not.Any(a.TraitTypes.Contains))
						continue;
					if (deriveHasField != null && deriveHasField.TryGetValue(role, out var hasField) &&
						!hasField.All(p => p.Matches(a.FieldValues(p.Key))))
						continue;
					if (deriveNotField != null && deriveNotField.TryGetValue(role, out var notField) &&
						notField.Any(p => p.Matches(a.FieldValues(p.Key))))
						continue;
					if (exclude.TryGetValue(role, out var ex) && ex.Contains(a.Name))
						continue;
					Of(role).Add(a.Name);
				}
			}

			return members;
		}

		// A new set of the field's own type: the lists are HashSet in some modules and FrozenSet in others,
		// and a FrozenSet cannot be added to in place.
		public static object Union(Type fieldType, IEnumerable<string> current, IEnumerable<string> added)
		{
			var all = current.Concat(added);
			if (fieldType == typeof(FrozenSet<string>))
				return all.ToFrozenSet();
			if (fieldType == typeof(HashSet<string>))
				return all.ToHashSet();
			if (fieldType == typeof(ImmutableHashSet<string>))
				return all.ToImmutableHashSet();
			throw new YamlException($"BotRoleSets: cannot fill a field of type {fieldType.Name}");
		}
	}

	public class BotRoleSets { }
}
