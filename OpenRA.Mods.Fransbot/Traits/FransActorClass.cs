#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public
 * License as published by the Free Software Foundation, either
 * version 3 of the License, or (at your option) any later version.
 * For more information, see COPYING.
 */
#endregion

using System;
using System.Collections.Frozen;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.Common.Traits.Radar;
using OpenRA.Mods.Common.Traits.Render;

namespace OpenRA.Mods.Common.Traits
{
	/// <summary>
	/// Trait-derived actor classification for the Fransbot port.
	/// Upstream logic hard-coded Red Alert actor ids ("harv", "proc", "fact",
	/// "mcv", "e3", "arty", ...) that never resolve in Cameo's multi-faction
	/// ContentPack ruleset. These helpers classify by traits instead, so every
	/// faction participates without per-name lists. Mission-kind tokens such as
	/// "fact"/"minecluster" on mission records are NOT actor names and stay
	/// strings — only real actor classification goes through here.
	/// </summary>
	public static class FransActorClass
	{
		static readonly string[] NavalLocomotors = { "naval", "lcraft" };
		static readonly string[] LandLocomotors =
			{ "foot", "tracked", "wheeled", "heavytracked", "heavywheeled", "lighttracked", "subterranean" };

		public static bool IsBuilding(ActorInfo a) => a.HasTraitInfo<BuildingInfo>();
		public static bool IsHarvester(ActorInfo a) => a.HasTraitInfo<HarvesterInfo>();
		public static bool IsTransport(ActorInfo a) => a.HasTraitInfo<CargoInfo>();
		public static bool IsCapturer(ActorInfo a) => a.HasTraitInfo<CapturesInfo>();
		public static bool IsBridgeEngineer(ActorInfo a) => a.HasTraitInfo<RepairsBridgesInfo>();
		public static bool IsMinelayer(ActorInfo a) => a.HasTraitInfo<MinelayerInfo>();
		public static bool IsAircraft(ActorInfo a) => a.HasTraitInfo<AircraftInfo>();
		public static bool IsRefinery(ActorInfo a) => IsBuilding(a) && a.HasTraitInfo<RefineryInfo>();
		public static bool IsRadar(ActorInfo a) => IsBuilding(a) && a.HasTraitInfo<ProvidesRadarInfo>();
		public static bool IsRepairDepot(ActorInfo a) => IsBuilding(a) && a.HasTraitInfo<RepairsUnitsInfo>();
		public static bool IsSilo(ActorInfo a) => IsBuilding(a) && a.HasTraitInfo<StoresPlayerResourcesInfo>();
		public static bool IsPowerPlant(ActorInfo a) => IsBuilding(a) && a.TraitInfoOrDefault<PowerInfo>() is { } p && p.Amount > 0;
		public static bool IsSuperweapon(ActorInfo a) => IsBuilding(a) && a.TraitInfos<SupportPowerInfo>().Any();

		/// <summary>Tech-center class: building granting a *tech*/tek/hq/lab prerequisite (atek/stek analogues).</summary>
		public static bool IsTechCenter(ActorInfo a) =>
			IsBuilding(a) && a.TraitInfos<ProvidesPrerequisiteInfo>().Any(p =>
				!string.IsNullOrEmpty(p.Prerequisite) && p.Prerequisite.Split(',').Any(v =>
				{
					var t = v.Trim().ToLowerInvariant();
					return t.Contains("tech") || t.Contains("tek") || t.Contains("hq") || t.Contains("lab");
				}));

		public static bool IsProducer(ActorInfo a) => IsBuilding(a) && a.TraitInfos<ProductionInfo>().Any();

		/// <summary>True when the actor is a producer whose Produces list matches any keyword (case-insensitive substring).</summary>
		public static bool ProducesAny(ActorInfo a, params string[] keywords) =>
			a.TraitInfos<ProductionInfo>().Any(p => p.Produces.Any(q =>
				keywords.Any(k => q.Contains(k, StringComparison.OrdinalIgnoreCase))));

		public static bool IsNavalProducer(ActorInfo a) =>
			IsProducer(a) && ProducesAny(a, "naval", "ship", "submarine", "lcraft");

		public static bool IsAirProducer(ActorInfo a) =>
			IsProducer(a) && ProducesAny(a, "aircraft", "plane", "helicopter");

		public static bool IsConyard(ActorInfo a) => IsBuilding(a) && a.HasTraitInfo<BaseBuildingInfo>() && IsProducer(a);

		public static bool IsMcv(ActorInfo a) => a.HasTraitInfo<TransformsInfo>() && !IsBuilding(a);

		public static bool IsInfantry(ActorInfo a) =>
			a.HasTraitInfo<WithInfantryBodyInfo>() || a.HasTraitInfo<TakeCoverInfo>()
			|| (a.TraitInfoOrDefault<MobileInfo>() is { } m && m.Locomotor == "foot");

		public static bool IsNaval(ActorInfo a) =>
			a.TraitInfoOrDefault<MobileInfo>() is { } m && NavalLocomotors.Contains(m.Locomotor?.ToLowerInvariant());

		public static bool IsGround(ActorInfo a) =>
			a.TraitInfoOrDefault<MobileInfo>() is { } m && LandLocomotors.Contains(m.Locomotor?.ToLowerInvariant());

		public static bool IsArmed(ActorInfo a) =>
			a.TraitInfos<AttackBaseInfo>().Any() || a.TraitInfos<ArmamentInfo>().Any();

		public static bool IsVtol(ActorInfo a) =>
			a.TraitInfoOrDefault<AircraftInfo>() is { } ai && (ai.VTOL || ai.CanHover);

		public static bool IsFixedWing(ActorInfo a) => IsAircraft(a) && !IsVtol(a);

		public static bool IsDefense(ActorInfo a) => IsBuilding(a) && IsArmed(a);
		public static bool IsTank(ActorInfo a) => IsGround(a) && IsArmed(a) && !IsHarvester(a) && !IsTransport(a);

		/// <summary>True when any armament's resolved weapon accepts <paramref name="target"/>.</summary>
		/// <summary>
		/// True when an owned, enabled production queue can currently produce the type.
		/// Uses the prerequisite-resolved BuildableItems set — Producible is queue-type
		/// matched only and contains cross-faction entries that can never be built.
		/// </summary>
		public static bool AnyOwnedQueueCanBuild(Player player, string type)
		{
			return player.World.ActorsHavingTrait<ProductionQueue>()
				.Where(a => a.Owner == player && a.IsInWorld && !a.IsDead)
				.SelectMany(a => a.TraitsImplementing<ProductionQueue>())
				.Any(q => q.Enabled && q.BuildableItems().Any(i => i.Name == type));
		}

		public static bool WeaponTargets(ActorInfo a, Ruleset rules, string target)
		{
			foreach (var arm in a.TraitInfos<ArmamentInfo>())
			{
				var name = arm.Weapon;
				if (string.IsNullOrEmpty(name) || !rules.Weapons.TryGetValue(name.ToLowerInvariant(), out var w))
					continue;
				var valid = w.ValidTargets;
				var invalid = w.InvalidTargets;
				if (valid.Contains(target) && !invalid.Contains(target))
					return true;
			}

			return false;
		}

		/// <summary>Maximum armament weapon range in WDist length units (0 when unarmed).</summary>
		public static int MaxWeaponRange(ActorInfo a, Ruleset rules)
		{
			var best = 0;
			foreach (var arm in a.TraitInfos<ArmamentInfo>())
			{
				var name = arm.Weapon;
				if (string.IsNullOrEmpty(name) || !rules.Weapons.TryGetValue(name.ToLowerInvariant(), out var w))
					continue;
				if (w.Range.Length > best)
					best = w.Range.Length;
			}

			return best;
		}

		/// <summary>Rocket-soldier class: infantry whose weapon targets air.</summary>
		public static bool IsAAInfantry(ActorInfo a, Ruleset rules) => IsInfantry(a) && WeaponTargets(a, rules, "air");

		/// <summary>Artillery class: armed mobile unit with weapon range >= ~10 cells.</summary>
		public static bool IsArtillery(ActorInfo a, Ruleset rules) =>
			!IsBuilding(a) && IsArmed(a) && !IsAircraft(a) && MaxWeaponRange(a, rules) >= 10 * 1024;
	}

	/// <summary>
	/// Queue-name to production-domain mapping, derived per ruleset from which mobile
	/// unit classes declare each Buildable.Queue name. Upstream logic compared queue
	/// names to literals ("Infantry"/"Vehicle"/"Aircraft"/"Ship"), which silently match
	/// nothing under Cameo's hybrid mode where live queue types are RAInfantry /
	/// RAVehicle / RAAircraft / RANaval (and pack-specific names like SCZergInfantry or
	/// Vehicle.HunterSeeker). Every domain set contains every alias a domain unit
	/// declares, so lookups resolve in classic and hybrid queue modes alike.
	/// </summary>
	public sealed class FransQueueDomains
	{
		static readonly Dictionary<Ruleset, FransQueueDomains> Cache = new();

		public readonly FrozenSet<string> Infantry;
		public readonly FrozenSet<string> Vehicle;
		public readonly FrozenSet<string> Air;
		public readonly FrozenSet<string> Naval;

		FransQueueDomains(FrozenSet<string> infantry, FrozenSet<string> vehicle,
			FrozenSet<string> air, FrozenSet<string> naval)
		{
			Infantry = infantry;
			Vehicle = vehicle;
			Air = air;
			Naval = naval;
		}

		public static FransQueueDomains For(Ruleset rules)
		{
			lock (Cache)
			{
				if (Cache.TryGetValue(rules, out var domains))
					return domains;

				var infantry = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
				var vehicle = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
				var air = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
				var naval = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

				foreach (var actor in rules.Actors.Values)
				{
					if (FransActorClass.IsBuilding(actor))
						continue;
					var buildable = actor.TraitInfoOrDefault<BuildableInfo>();
					if (buildable == null)
						continue;

					if (FransActorClass.IsInfantry(actor))
						infantry.UnionWith(buildable.Queue);
					else if (FransActorClass.IsAircraft(actor))
						air.UnionWith(buildable.Queue);
					else if (FransActorClass.IsNaval(actor))
						naval.UnionWith(buildable.Queue);
					else if (FransActorClass.IsGround(actor))
						vehicle.UnionWith(buildable.Queue);
				}

				domains = new FransQueueDomains(
					infantry.ToFrozenSet(StringComparer.OrdinalIgnoreCase),
					vehicle.ToFrozenSet(StringComparer.OrdinalIgnoreCase),
					air.ToFrozenSet(StringComparer.OrdinalIgnoreCase),
					naval.ToFrozenSet(StringComparer.OrdinalIgnoreCase));
				Cache[rules] = domains;
				return domains;
			}
		}
	}
}
