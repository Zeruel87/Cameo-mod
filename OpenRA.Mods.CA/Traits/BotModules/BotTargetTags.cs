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
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	// 6g (CN A3): rules-derived target tags for per-squad priority lists.
	// Tags come from traits and weapon metadata — no actor ids are hand-typed.
	public static class BotTargetTags
	{
		public const string Artillery = "artillery";
		public const string Harvester = "harvester";
		public const string Production = "production";
		public const string Superweapon = "superweapon";
		public const string Power = "power";
		public const string Refinery = "refinery";
		public const string Conyard = "conyard";
		public const string Defence = "defence";

		// A mobile actor counts as artillery when its longest-ranged armament
		// reaches at least this far (the siege threshold, 12 cells). Public: the
		// merged roles provider (Cameo BotUnitRoles) reuses the same line (§12.4).
		public static readonly int ArtilleryMinRange = new WDist(12 * 1024).Length;

		public static IReadOnlyDictionary<string, HashSet<string>> BuildTagMap(Ruleset rules)
		{
			var superweaponSources = new HashSet<string>(StringComparer.Ordinal);
			if (rules.Actors.TryGetValue(SystemActors.Player.ToString().ToLowerInvariant(), out var playerInfo))
				foreach (var power in playerInfo.TraitInfos<SupportPowerInfo>())
					foreach (var names in power.Prerequisites.Values)
						superweaponSources.UnionWith(names);

			var tags = new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);
			foreach (var kv in rules.Actors)
			{
				var set = TagsFor(kv.Value, rules, superweaponSources);
				if (set.Count > 0)
					tags[kv.Key] = set;
			}

			return tags;
		}

		internal static HashSet<string> TagsFor(
			ActorInfo info, Ruleset rules, IReadOnlySet<string> superweaponSources)
		{
			var tags = new HashSet<string>(StringComparer.Ordinal);

			if (info.HasTraitInfo<HarvesterInfo>())
				tags.Add(Harvester);

			if (info.HasTraitInfo<ProductionInfo>())
				tags.Add(Production);

			if (superweaponSources.Contains(info.Name))
				tags.Add(Superweapon);

			// Generators only - consumers carry the same trait with Amount <= 0.
			if (info.TraitInfos<PowerInfo>().Any(p => p.Amount > 0))
				tags.Add(Power);

			if (info.HasTraitInfo<RefineryInfo>())
				tags.Add(Refinery);

			// Same shape as the `conyard` role (DeriveHas: BaseBuilding, Building).
			if (info.HasTraitInfo<BaseBuildingInfo>() && info.HasTraitInfo<BuildingInfo>())
				tags.Add(Conyard);

			// Armed buildings - the `staticaa` role's shape without the air restriction.
			if (info.HasTraitInfo<BuildingInfo>() && info.HasTraitInfo<AttackBaseInfo>())
				tags.Add(Defence);

			if (info.HasTraitInfo<MobileInfo>())
				foreach (var armament in info.TraitInfos<ArmamentInfo>())
				{
					var name = armament.Weapon;
					if (string.IsNullOrEmpty(name))
						continue;

					if (rules.Weapons.TryGetValue(name.ToLowerInvariant(), out var weapon)
						&& weapon.Range.Length >= ArtilleryMinRange)
					{
						tags.Add(Artillery);
						break;
					}
				}

			return tags;
		}

		// Stable tag preference for candidate lists: matches first, original order
		// otherwise preserved. Returns the input untouched when nothing can match.
		public static List<T> PreferTagged<T>(List<T> candidates, IReadOnlySet<string> priorityTags, Func<T, HashSet<string>> tagsOf)
		{
			if (priorityTags == null || priorityTags.Count == 0 || candidates.Count < 2)
				return candidates;

			List<T> preferred = null;
			for (var i = 0; i < candidates.Count; i++)
			{
				var tags = tagsOf(candidates[i]);
				if (tags != null && tags.Overlaps(priorityTags))
					(preferred ??= []).Add(candidates[i]);
			}

			if (preferred == null || preferred.Count == 0)
				return candidates;

			var rest = new List<T>(candidates.Count - preferred.Count);
			foreach (var c in candidates)
			{
				var tags = tagsOf(c);
				if (tags == null || !tags.Overlaps(priorityTags))
					rest.Add(c);
			}

			preferred.AddRange(rest);
			return preferred;
		}
	}
}
