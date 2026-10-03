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
using OpenRA.Mods.AS.Traits;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	// CN2 (AI_MASTER_PLAN §3, crystallized-nexus 30cf70a): port of CNGarrisonBotModule. Sends spare idle infantry
	// into own buildings listed in GarrisonableBuildingTypes, preferring the specialist the local threat calls
	// for (anti-armour vs anti-air), and unloads a mismatched garrison once the threat flips and a free
	// specialist exists.
	//
	// Cameo changes vs the donor:
	//  - Cameo has no BotCapabilities trait (the same finding as CombatAnalysisBotModule): capability tags become
	//    yaml type sets (GarrisonableBuildingTypes / AntiArmorInfantryTypes / AntiAirInfantryTypes /
	//    EnemyArmorTypes) and AircraftInfo for air, per the explicit-list convention.
	//  - Targets the AS garrison pair (Garrisonable buildings + EnterGarrison orders + Garrisoner infantry),
	//    which is what Cameo packs deploy - the donor's Cargo/EnterTransport buildings exist here only as the
	//    owned-conditional tech-building variant.
	//  - `squadManager.IsUnitAssignedToSquad` and the public TryReserveInfantry callback are replaced by the
	//    §19.6 lease contract: the module claims each infantryman for the walk (BotLeasePurpose.Garrison) so
	//    squads and other owners skip it, renews every scan and releases on arrival, death or loss. Without a
	//    registry (classic) nothing is claimed - donor behaviour.
	//  - Threat assessment keeps the donor's fog check: only `CanBeViewedByPlayer` enemies count.
	//  - Candidates iterate in ActorID order; CNBotPerf/CNBotLog instrumentation dropped.
	[TraitLocation(SystemActors.Player)]
	[Desc("Sends spare idle infantry to garrison own buildings tagged in GarrisonableBuildingTypes, preferring the infantry specialization the local threat calls for.")]
	public class GarrisonDefenseBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Ticks between scans for garrison buildings with open capacity and available infantry.")]
		public readonly int ScanInterval = 150;

		[Desc("Ticks between re-evaluating whether the current garrison mix still covers the local threat.")]
		public readonly int SwapInterval = 450;

		[Desc("Radius (in cells) around a garrison building scanned for enemy presence to determine which infantry specialization it needs.")]
		public readonly WDist ThreatScanRadius = WDist.FromCells(12);

		[Desc("Restricts the garrisoned positions the bot keeps manned to these building actor types. Empty = every building the bot owns that can garrison infantry - captured civilian/tech garrisons included.")]
		public readonly FrozenSet<string> GarrisonableBuildingTypes = FrozenSet<string>.Empty;

		[Desc("Infantry types counted as anti-armour specialists when picking garrison passengers.")]
		public readonly FrozenSet<string> AntiArmorInfantryTypes = FrozenSet<string>.Empty;

		[Desc("Infantry types counted as anti-air specialists when picking garrison passengers.")]
		public readonly FrozenSet<string> AntiAirInfantryTypes = FrozenSet<string>.Empty;

		[Desc("Armor trait types on enemy units that count as an armour threat.")]
		public readonly FrozenSet<string> EnemyArmorTypes = new[] { "Light", "Heavy", "Superheavy" }.ToFrozenSet();

		[Desc("Idle infantry are only sent to garrison once this many remain unclaimed, so squad formation is never starved just to fill a bunker.")]
		public readonly int MinimumSpareInfantry = 2;

		[Desc("Desired occupied cargo weight per garrison. Kept below full capacity so several positions can be manned without consuming the bot's whole infantry production.")]
		public readonly int DesiredOccupancyWeight = 4;

		public override object Create(ActorInitializer init) { return new GarrisonDefenseBotModule(init.Self, this); }
	}

	public class GarrisonDefenseBotModule : ConditionalTrait<GarrisonDefenseBotModuleInfo>, IBotTick
	{
		const string LeaseOwner = nameof(GarrisonDefenseBotModule);

		enum GarrisonNeed { None, AntiArmor, AntiAir }

		readonly World world;
		readonly HashSet<Actor> heldUnits = [];
		int scanTicks;
		int swapTicks;

		public GarrisonDefenseBotModule(Actor self, GarrisonDefenseBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			scanTicks = world.LocalRandom.Next(Info.ScanInterval);
			swapTicks = world.LocalRandom.Next(Info.SwapInterval);
		}

		protected override void TraitDisabled(Actor self)
		{
			var leases = BotUnitLeases.Of(self.Owner);
			foreach (var a in heldUnits)
				leases?.Release(a, LeaseOwner);

			heldUnits.Clear();
		}

		void IBotTick.BotTick(IBot bot)
		{
			var doFill = --scanTicks <= 0;
			var doSwap = --swapTicks <= 0;
			if (doFill)
				scanTicks = Info.ScanInterval;
			if (doSwap)
				swapTicks = Info.SwapInterval;
			if (!doFill && !doSwap)
				return;

			var player = bot.Player;
			var leases = BotUnitLeases.Of(player);

			// Release arrivals and the gone; renew claims on everyone still en route so the lease (not the
			// idle flag) is what keeps squads away for the duration of the trip.
			var prune = new List<Actor>();
			foreach (var a in heldUnits)
			{
				if (a.IsDead || !a.IsInWorld || a.Owner != player || IsInside(a) ||
					leases == null || !leases.TryClaim(a, LeaseOwner, BotLeasePurpose.Garrison, LeaseHeartbeatTicks()))
					prune.Add(a);
			}

			foreach (var a in prune)
			{
				heldUnits.Remove(a);
				leases?.Release(a, LeaseOwner);
			}

			var garrisons = world.ActorsHavingTrait<Garrisonable>()
				.Where(a => a.Owner == player && a.IsInWorld && !a.IsDead
					&& (Info.GarrisonableBuildingTypes.Count == 0 || Info.GarrisonableBuildingTypes.Contains(a.Info.Name)))
				.OrderBy(a => a.ActorID)
				.ToList();

			if (garrisons.Count == 0)
				return;

			if (doSwap)
				TickSwap(bot, player, leases, garrisons);

			if (doFill)
				TickFill(bot, player, leases, garrisons);
		}

		static bool IsInside(Actor a) => a.TraitOrDefault<Passenger>()?.Transport != null
			|| a.TraitOrDefault<Garrisoner>()?.Transport != null;

		// Determines what the garrison building's immediate surroundings call for, based on visible enemy
		// presence near it. `CanBeViewedByPlayer` is what keeps this honest: without it the garrison answered
		// threats the bot has no business knowing about yet - cloaked or shrouded aircraft approaching out of
		// sight had it swapping pre-emptively to anti-air (donor comment).
		GarrisonNeed AssessNeed(Actor garrison, OpenRA.Player player)
		{
			var armorCount = 0;
			var airCount = 0;

			foreach (var enemy in world.FindActorsInCircle(garrison.CenterPosition, Info.ThreatScanRadius))
			{
				if (enemy.Owner.RelationshipWith(player) != PlayerRelationship.Enemy)
					continue;

				if (!enemy.CanBeViewedByPlayer(player))
					continue;

				if (enemy.Info.TraitInfoOrDefault<AircraftInfo>() != null)
					airCount++;
				else if (enemy.Info.TraitInfos<ArmorInfo>().Any(a => Info.EnemyArmorTypes.Contains(a.Type)))
					armorCount++;
			}

			if (airCount == 0 && armorCount == 0)
				return GarrisonNeed.None;

			return airCount > armorCount ? GarrisonNeed.AntiAir : GarrisonNeed.AntiArmor;
		}

		FrozenSet<string> WantedTypes(GarrisonNeed need)
		{
			return need == GarrisonNeed.AntiAir ? Info.AntiAirInfantryTypes : Info.AntiArmorInfantryTypes;
		}

		bool CanFightFromGarrison(Actor actor)
		{
			return actor.Info.TraitInfoOrDefault<GarrisonerInfo>() != null &&
				actor.Info.TraitInfos<ArmamentInfo>()
					.Any(a => string.Equals(a.Name, "garrisoned", StringComparison.OrdinalIgnoreCase));
		}

		/// <summary>
		/// A spare unit of <paramref name="wanted"/> that is free to be garrisoned, or null. Same
		/// eligibility the fill pass uses - idle, unclaimed, and outside the spare-infantry buffer -
		/// because a swap that empties a position on the strength of a replacement the fill pass would
		/// then refuse to hand over is worse than no swap at all.
		/// </summary>
		Actor FindFreeSpecialist(OpenRA.Player player, IBotUnitLeases leases, FrozenSet<string> wanted)
		{
			var spare = -Info.MinimumSpareInfantry;
			foreach (var a in world.ActorsHavingTrait<Mobile>())
			{
				if (a.Owner != player || !a.IsInWorld || a.IsDead || !a.IsIdle
					|| !CanFightFromGarrison(a)
					|| BotUnitLeases.IsClaimedByOther(leases, a, LeaseOwner))
					continue;

				// Counted the same way the fill pass counts: the buffer comes off the top, and only what is
				// left over may be committed.
				if (++spare > 0 && wanted.Contains(a.Info.Name))
					return a;
			}

			return null;
		}

		void TickFill(IBot bot, OpenRA.Player player, IBotUnitLeases leases, List<Actor> garrisons)
		{
			// Leased units are off limits. "Idle" is not the same as "unassigned": a squad parked waiting for
			// the next attack wave sits still and reports IsIdle, and a fill pass pulling exactly those units
			// out of the staging wave is the donor's fixed bug - the lease check is what makes it stay fixed
			// here (squad members carry a Squad claim).
			var pool = world.ActorsHavingTrait<Mobile>()
				.Where(a => a.Owner == player && a.IsInWorld && !a.IsDead && a.IsIdle
					&& CanFightFromGarrison(a)
					&& !BotUnitLeases.IsClaimedByOther(leases, a, LeaseOwner))
				.OrderBy(a => a.ActorID)
				.Skip(Info.MinimumSpareInfantry)
				.ToList();

			if (pool.Count == 0)
				return;

			foreach (var garrison in garrisons)
			{
				if (pool.Count == 0)
					break;

				var garrisonable = garrison.Trait<Garrisonable>();
				var desired = Math.Min(garrisonable.Info.MaxWeight, Math.Max(1, Info.DesiredOccupancyWeight));
				var occupied = garrisonable.TotalWeight;
				if (occupied >= desired || !garrisonable.HasSpace(1))
					continue;

				var need = AssessNeed(garrison, player);

				// HasSpace() reflects committed state only; QueueOrder doesn't apply until the order resolves
				// later, so track how much we've already earmarked this pass ourselves.
				for (var pendingWeight = 0; pool.Count > 0 && occupied + pendingWeight < desired
					&& garrisonable.HasSpace(pendingWeight + 1); pendingWeight++)
				{
					var pick = PickBestForNeed(pool, need);
					pool.Remove(pick);
					bot.QueueOrder(new Order("EnterGarrison", pick, Target.FromActor(garrison), false));
					if (leases != null && leases.TryClaim(pick, LeaseOwner, BotLeasePurpose.Garrison, LeaseHeartbeatTicks()))
						heldUnits.Add(pick);
				}
			}
		}

		Actor PickBestForNeed(List<Actor> pool, GarrisonNeed need)
		{
			if (need != GarrisonNeed.None)
			{
				var wanted = WantedTypes(need);
				var match = pool.FirstOrDefault(a => wanted.Contains(a.Info.Name));
				if (match != null)
					return match;
			}

			return pool[0];
		}

		void TickSwap(IBot bot, OpenRA.Player player, IBotUnitLeases leases, List<Actor> garrisons)
		{
			foreach (var garrison in garrisons)
			{
				var garrisonable = garrison.Trait<Garrisonable>();
				if (garrisonable.IsEmpty())
					continue;

				var need = AssessNeed(garrison, player);
				if (need == GarrisonNeed.None)
					continue;

				var wanted = WantedTypes(need);
				if (garrisonable.Garrisoners.Any(p => wanted.Contains(p.Info.Name)))
					continue;

				// Nobody currently inside covers the local threat. If there's a free slot the fill pass will
				// bring the right specialist in on its own; if the garrison is full, make room for it now -
				// but only once the replacement actually exists.
				//
				// Unload empties the whole position, and this used to fire whether or not anything could
				// take the vacated seats. A full anti-armour bunker that spotted aircraft with no free
				// anti-air infantry anywhere would empty itself and stand there vacant, then refill with
				// the same unsuitable squad on the next pass and empty again on the one after. Worse, the
				// fill pass running in the same bot tick still sees the old cargo, because orders resolve
				// later - so it cannot be relied on to catch the position on the way down.
				if (!garrisonable.HasSpace(1) && FindFreeSpecialist(player, leases, wanted) != null)
					bot.QueueOrder(new Order("Unload", garrison, false));
			}
		}

		int LeaseHeartbeatTicks() => Math.Max(200, Info.ScanInterval * 4);
	}
}
