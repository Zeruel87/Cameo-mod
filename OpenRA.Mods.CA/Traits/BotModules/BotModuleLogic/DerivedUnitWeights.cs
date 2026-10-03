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

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// AI_ARCHITECTURE.md §2.8b item 3 (UW-1): the derived `UnitsToBuild` table. The
	/// personality's RoleMix (§12.5) sets a target share per combat role; a candidate's
	/// weight is that share scaled by its Versus-weighted strength relative to the other
	/// candidates that share its primary role:
	///
	///   share[r]    = mix[r] when the mix names r, else the manager's RoleMixRoleFloorPct
	///   strength[u] = max over weapons of (DamagePerTick × mean(Versus values) / 100),
	///                 floored at 1 so a weaponless unit still counts toward the role mean
	///   w[u]        = max(1, round(share[primaryRole(u)] × strength[u] / mean strength
	///                 over the candidates whose primary role is primaryRole(u)))
	///
	/// The candidate set is exactly the yaml `UnitsToBuild` keys: the rows stay the
	/// membership gate, and a unit with no primary combat role keeps its yaml weight
	/// verbatim — the deliberate hand rows of §2.8b survive as overrides. A unit counts
	/// toward exactly one role, its PRIMARY (IBotUnitRoles.PrimaryRoleOf), mirroring
	/// ChooseRoleDeficit's composition accounting. The mix's own domain is
	/// BotUnitRole.CombatRoles; anything else a mix names can never be served and is
	/// ignored. Pure own-side stats — no enemy is enumerated (DESIGN §19.5).
	/// </summary>
	public sealed class DerivedUnitWeights
	{
		// The derived table is a pure function of (yamlWeights, mix, floorPct, roles,
		// ruleset); every input but the enabled squad manager is fixed at rules load,
		// and a personality switch swaps the manager — hence the mix dictionary — so
		// (mix, floorPct) is the whole cache key. One table serves every queue
		// category: UnitsToBuild is not split per category.
		IReadOnlyDictionary<string, int> cachedMix;
		int cachedFloorPct = -1;
		Dictionary<string, int> cachedTable;

		/// <summary>
		/// The UnitsToBuild table for one queue pick. An applicable composition wins over
		/// everything (§1.4 compositions stay the personality flavour); flag off, no
		/// RoleMix, or no roles provider each return the yaml table unchanged — the
		/// pre-derivation path, byte-identical.
		/// </summary>
		public Dictionary<string, int> Select(
			bool useDerived,
			Dictionary<string, int> compositionWeights,
			Dictionary<string, int> yamlWeights,
			IReadOnlyDictionary<string, int> mix,
			int roleFloorPct,
			IBotUnitRoles roles,
			Func<string, double> strengthOf)
		{
			if (compositionWeights != null)
				return compositionWeights;

			if (!useDerived || yamlWeights == null || mix == null || mix.Count == 0 ||
				roles == null || strengthOf == null)
				return yamlWeights;

			if (cachedTable == null || !ReferenceEquals(cachedMix, mix) || cachedFloorPct != roleFloorPct)
			{
				cachedTable = Derive(yamlWeights, mix, roleFloorPct, roles, strengthOf);
				cachedMix = mix;
				cachedFloorPct = roleFloorPct;
			}

			return cachedTable;
		}

		/// <summary>
		/// The derivation itself: the result carries exactly `yamlWeights`' keys — roled
		/// rows rewritten by the share × relative-strength formula, every other row verbatim.
		/// </summary>
		public static Dictionary<string, int> Derive(
			IReadOnlyDictionary<string, int> yamlWeights,
			IReadOnlyDictionary<string, int> mix,
			int roleFloorPct,
			IBotUnitRoles roles,
			Func<string, double> strengthOf)
		{
			var result = new Dictionary<string, int>(yamlWeights.Count, StringComparer.Ordinal);
			foreach (var kv in yamlWeights)
				result[kv.Key] = kv.Value;

			// Bucket the candidates by the one role they count toward. Roles with no
			// candidate member (a mix key the roster cannot serve) are simply absent.
			var byRole = new Dictionary<string, List<string>>(StringComparer.Ordinal);
			foreach (var name in yamlWeights.Keys)
			{
				var role = roles.PrimaryRoleOf(name);
				if (role == null || !BotUnitRole.CombatRoles.Contains(role))
					continue;

				if (!byRole.TryGetValue(role, out var members))
					byRole[role] = members = new List<string>();
				members.Add(name);
			}

			foreach (var (role, members) in byRole)
			{
				var share = mix.TryGetValue(role, out var named) ? named : roleFloorPct;
				var strength = members.ToDictionary(m => m, strengthOf, StringComparer.Ordinal);

				// strength is floored at 1, so the mean is never 0.
				var mean = strength.Values.Average();
				foreach (var m in members)
					result[m] = Math.Max(1, (int)Math.Round(share * strength[m] / mean, MidpointRounding.AwayFromZero));
			}

			return result;
		}

		/// <summary>
		/// The strength proxy: the best weapon's damage per tick scaled by the mean of its
		/// Versus entries — a weapon with no Versus overrides reads 100, the DamageWarhead
		/// default. A weaponless profile floors at 1 so it still counts toward the role mean.
		/// </summary>
		public static double Strength(BotUnitProfile profile)
		{
			var best = 0.0;
			if (profile != null)
				foreach (var w in profile.Weapons)
				{
					var versus = w.Versus.Count == 0 ? 100.0 : w.Versus.Values.Average();
					best = Math.Max(best, w.DamagePerTick * versus / 100.0);
				}

			return Math.Max(1.0, best);
		}
	}
}
