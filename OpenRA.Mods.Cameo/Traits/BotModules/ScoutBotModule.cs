#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Traits;
using CAAIUtils = OpenRA.Mods.CA.AIUtils;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	[Desc("Keeps cheap scout units cycling through stale map regions so the fogged " +
		"observation layer (phase 6a) has fresh sightings. Claims units out of the squad " +
		"manager's idle pool, never from squads. See docs/design/AI_FRANSBOT_RESEARCH.md 6b.")]
	public class ScoutBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Actor types usable as scouts (cheap, fast units; empty disables claiming).")]
		public readonly HashSet<string> ScoutUnitTypes = new();

		[Desc("Maximum scouts held at once.")]
		public readonly int MaxScouts = 2;

		[Desc("Minimum ticks between two scout production requests (AI_ARCHITECTURE §12.12). A request is built ahead of",
			"the unit builder's queue rotation and cash check, so unrationed replacements for scouts that die or get",
			"drafted into squads took over the vehicle factory. 0 = request on every scan, as before.")]
		public readonly int ScoutRebuildCooldownTicks = 0;

		[Desc("Ticks between claim/retarget evaluations.")]
		public readonly int ScanInterval = 50;

		[Desc("Ticks a scout keeps its assigned region before being re-evaluated.")]
		public readonly int RetargetTicks = 750;

		[Desc("Ticks until an unexplored region reaches full staleness interest.")]
		public readonly int StaleAfterTicks = 2500;

		[Desc("Ticks a recorded attacker value keeps counting against a region.")]
		public readonly int DangerDecayTicks = 7500;

		[Desc("Bonus interest added to regions containing a resource cluster.")]
		public readonly int ResourceSiteBonus = 3000;

		[Desc("Bonus interest per unit of remembered enemy value in a region.")]
		public readonly int RememberedValueWeight = 1;

		[Desc("Bonus interest for regions holding a multiplayer spawn other than this bot's own (public map data, as",
			"every human sees in the lobby): scouts keep checking where the enemy base probably is. The bot saw only",
			"1-18% of the enemy army without it (AI_DEEP_RESEARCH.md §2.3). 0 disables it.")]
		public readonly int EnemySpawnBonus = 0;

		[Desc("CA-6: keep fresh eyes on the current main target's remembered footprint. Regions where the target",
			"enemy was last seen gain this much interest, so scouting refreshes the intel that target choice and",
			"raid bidding consume (AI_ARCHITECTURE §12.9) instead of wandering stale regions uniformly.")]
		public readonly bool UseTargetIntelBias = false;

		[Desc("Interest added to a region remembered as occupied by the current main target.")]
		public readonly int TargetIntelBonus = 2000;

		[Desc("PL-2 (§12.14): extra scout cap added while the guerrilla lead trails, scaled by the",
			"deficit — behind on map control means leaning on scouts, the lead's driver. Inert unless",
			"UsePersonalityLeads is armed and the running personality is guerrilla.")]
		public readonly int GuerrillaLeadExtraScouts = 2;

		public override object Create(ActorInitializer init) { return new ScoutBotModule(init.Self, this); }
	}

	public class ScoutBotModule : ConditionalTrait<ScoutBotModuleInfo>, IBotTick, IBotEnabled,
		IBotNotifyIdleBaseUnits, IBotRespondToAttack, IBotRegionThreatProvider
	{
		readonly World world;
		readonly OpenRA.Player player;
		readonly Predicate<Actor> unitCannotBeOrdered;

		readonly List<UnitWposWrapper> scouts = new();
		readonly Dictionary<Actor, (int Region, int AssignedTick)> scoutTargets = new();

		// Killer-attributed hostile value per region, fed by attacks on our scouts.
		// Exposed read-only for the 6c risk gate; keys are RegionMemory region indices.
		readonly Dictionary<int, (int Value, int Tick)> dangerByRegion = new();

		// ZG-c: scoutTargets, dangerByRegion and enemySpawnRegions all key Situation.Regions'
		// index space — grid cells, or zone ids when zone-backed. A zone re-cut or a backing
		// switch re-shuffles every id, so those caches drop on the (ZoneBacked, Generation)
		// change rather than alias onto different ground.
		bool lastRegionsZoned;
		int lastRegionsGeneration = -1;

		ResourceMapBotModule resourceMap;
		IBotMainTargetProvider mainTargetProvider;
		IBotRequestUnitProduction[] unitBuilders;
		IBotPersonalityLeadProvider[] leadProviders;
		int lastScoutRequestTick = -1;
		// Null until the squad manager supplies its shared idle-unit pool.
		List<UnitWposWrapper> idlePool;
		int scanTicks;

		public ScoutBotModule(Actor self, ScoutBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			unitCannotBeOrdered = a => a == null || a.IsDead || !a.IsInWorld || a.Owner != player;
		}

		public IReadOnlyDictionary<int, (int Value, int Tick)> DangerByRegion => dangerByRegion;

		protected override void TraitEnabled(Actor self)
		{
			resourceMap = self.TraitsImplementing<ResourceMapBotModule>().FirstOrDefault(t => t.IsTraitEnabled());
			mainTargetProvider = self.TraitsImplementing<IBotMainTargetProvider>().FirstOrDefault();
			unitBuilders = self.TraitsImplementing<IBotRequestUnitProduction>().ToArray();
			leadProviders = self.Owner.PlayerActor.TraitsImplementing<IBotPersonalityLeadProvider>().ToArray();
			scanTicks = world.LocalRandom.Next(0, Info.ScanInterval);
		}

		void IBotEnabled.BotEnabled(IBot bot) { }

		void IBotNotifyIdleBaseUnits.UpdatedIdleBaseUnits(List<UnitWposWrapper> unitsHangingAroundTheBase)
		{
			idlePool = unitsHangingAroundTheBase;
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (--scanTicks > 0)
				return;

			scanTicks = Info.ScanInterval;

			scouts.RemoveAll(u => unitCannotBeOrdered(u.Actor));
			foreach (var dead in scoutTargets.Keys.Where(a => unitCannotBeOrdered(a)).ToArray())
				scoutTargets.Remove(dead);

			// A scout that went idle between scans re-enters the squad manager's
			// idle pool and can be claimed by a squad while we still hold it —
			// yielding duelling orders (DAWN's edge). Release ownership instead.
			if (scouts.Count != 0)
			{
				var squadOwned = player.PlayerActor.TraitsImplementing<SquadManagerBotModuleCA>()
					.Where(m => !m.IsTraitDisabled)
					.SelectMany(m => m.Squads)
					.SelectMany(s => s.Units)
					.Select(u => u.Actor)
					.ToHashSet();

				foreach (var scout in scouts.Where(u => squadOwned.Contains(u.Actor)).ToArray())
				{
					scoutTargets.Remove(scout.Actor);
					scouts.Remove(scout);
				}
			}

			// LC1 heartbeat: renew every held scout each scan; a scout dropped by any path above or below simply stops
			// being renewed and its lease expires, so no release call can be forgotten. A scout another module holds
			// goes back to the pool (it was claimed out from under us between scans).
			var leases = BotUnitLeases.Of(player);
			if (leases != null)
				foreach (var scout in scouts.ToArray())
					if (!leases.TryClaim(scout.Actor, LeaseOwner, BotLeasePurpose.Scout, ScoutLeaseTicks))
						ReturnScoutToIdlePool(scout, scouts, scoutTargets, idlePool);

			var regions = player.PlayerActor.TraitOrDefault<MasterAiBotModule>()?.Situation?.Regions;
			if (regions == null)
				return;

			var tick = world.WorldTick;
			if (RegionSpaceChanged(regions))
				DropRegionCaches();

			var hasStaleRegion = AnyStaleRegion(regions, tick);
			if (ReleaseScoutsIfNoStaleRegions(hasStaleRegion, scouts, scoutTargets, idlePool))
				return;

			var taken = new HashSet<int>(scoutTargets.Values.Select(t => t.Region));
			ClaimScouts(bot);

			foreach (var scout in scouts.ToArray())
			{
				var actor = scout.Actor;
				if (scoutTargets.TryGetValue(actor, out var target) && tick - target.AssignedTick < Info.RetargetTicks && !actor.IsIdle)
					continue;

				var region = ChooseScoutTarget(regions, actor.Location, tick, taken);
				if (region < 0)
				{
					// No unassigned stale region: return ownership to the shared pool.
					ReturnScoutToIdlePool(scout, scouts, scoutTargets, idlePool);
					continue;
				}

				taken.Add(region);
				scoutTargets[actor] = (region, tick);
				bot.QueueOrder(new Order("Move", actor, Target.FromCell(world, regions.CenterOf(region)), false));
			}
		}

		internal static bool ReleaseScoutsIfNoStaleRegions(bool hasStaleRegion,
			List<UnitWposWrapper> scouts, Dictionary<Actor, (int Region, int AssignedTick)> scoutTargets,
			List<UnitWposWrapper> idlePool)
		{
			if (hasStaleRegion)
				return false;

			if (idlePool != null)
				while (scouts.Count > 0)
					ReturnScoutToIdlePool(scouts[0], scouts, scoutTargets, idlePool);

			return true;
		}

		static void ReturnScoutToIdlePool(UnitWposWrapper scout, List<UnitWposWrapper> scouts,
			Dictionary<Actor, (int Region, int AssignedTick)> scoutTargets, List<UnitWposWrapper> idlePool)
		{
			if (idlePool == null)
				return;

			scoutTargets.Remove(scout.Actor);
			scouts.Remove(scout);
			if (!IdlePoolContainsActor(idlePool, scout.Actor))
				idlePool.Add(scout);
		}

		static bool IdlePoolContainsActor(List<UnitWposWrapper> idlePool, Actor actor)
		{
			foreach (var unit in idlePool)
				if (unit.Actor == actor)
					return true;

			return false;
		}

		const string LeaseOwner = nameof(ScoutBotModule);

		// LC1: three scans — survives the order latency, frees a dropped scout within seconds.
		int ScoutLeaseTicks => 3 * System.Math.Max(1, Info.ScanInterval);

		// PL-2 (§12.14): behind on the guerrilla lead grows the cap toward base + extra,
		// linear in the deficit. lean >= 1 keeps the configured cap bit-identical.
		internal static int EffectiveMaxScouts(int baseMax, double lean, int extra) =>
			baseMax + (lean >= 1 ? 0 : (int)Math.Round((1 - Math.Max(0, lean)) * extra));

		void ClaimScouts(IBot bot)
		{
			var maxScouts = EffectiveMaxScouts(Info.MaxScouts,
				BotPersonalityLeads.Lean(leadProviders, "guerrilla"), Info.GuerrillaLeadExtraScouts);
			if (Info.ScoutUnitTypes.Count == 0 || scouts.Count >= maxScouts)
				return;

			var claimedAny = false;
			if (idlePool != null)
			{
				foreach (var candidate in idlePool.ToArray())
				{
					if (scouts.Count >= maxScouts)
						break;

					var actor = candidate.Actor;
					if (unitCannotBeOrdered(actor) || !Info.ScoutUnitTypes.Contains(actor.Info.Name))
						continue;

					if (scouts.Any(u => u.Actor == actor))
						continue;

					// LC1: never claim a unit another module holds (a crate run, a capture, a beacon response).
					if (!BotUnitLeases.TryClaim(BotUnitLeases.Of(player), actor, LeaseOwner, BotLeasePurpose.Scout, ScoutLeaseTicks))
						continue;

					scouts.Add(candidate);
					idlePool.Remove(candidate);
					claimedAny = true;
					AIUtils.BotDebug("AI ({0}): claimed scout {1}", player.ClientIndex, actor);
				}
			}

			if (!claimedAny && scouts.Count < maxScouts && MayRequest(world.WorldTick, lastScoutRequestTick, Info.ScoutRebuildCooldownTicks)
					&& RequestScout(bot))
				lastScoutRequestTick = world.WorldTick;
		}

		internal static bool MayRequest(int tick, int lastRequestTick, int cooldownTicks)
		{
			return cooldownTicks <= 0 || lastRequestTick < 0 || tick - lastRequestTick >= cooldownTicks;
		}

		bool RequestScout(IBot bot)
		{
			if (unitBuilders == null || unitBuilders.Length == 0)
				return false;

			foreach (var name in Info.ScoutUnitTypes.OrderBy(n => n, StringComparer.Ordinal))
			{
				var builder = unitBuilders.FirstOrDefault(b => b.RequestedProductionCount(bot, name) == 0);
				if (builder == null)
					continue;

				// Unloaded ContentPacks leave their actor names out of Rules.Actors;
				// indexing a missing key throws, so TryGetValue is load-bearing.
				if (!world.Map.Rules.Actors.TryGetValue(name, out var actorInfo))
					continue;

				var buildable = actorInfo?.TraitInfoOrDefault<BuildableInfo>();
				if (buildable == null)
					continue;

				if (!buildable.Queue.Any(q => CAAIUtils.FindQueues(player, q).Any(pq => pq.BuildableItems().Any(b => b.Name == name))))
					continue;

				builder.RequestUnitProduction(bot, name);
				return true;
			}

			return false;
		}

		int ChooseScoutTarget(RegionMemory regions, CPos from, int tick, HashSet<int> taken)
		{
			// IM-1 (AI_DEEP_RESEARCH §3.3): when the master snapshot publishes the influence
			// layers, they are the interest/danger/staleness source — threat_ground answers
			// the danger callback — instead of re-deriving per-index values from ByEnemy.
			// The score formula and the ByEnemy derivation below stay the fallback.
			var influence = player.PlayerActor.TraitOrDefault<MasterAiBotModule>()?.Situation?.Influence;
			if (LayersMatch(regions, influence))
				return PickScoutRegion(regions, from, taken,
					i => influence.Staleness[i], i => influence.Interest[i], i => influence.ThreatGround[i]);

			return PickScoutRegion(regions, from, taken,
				i => Staleness(regions, i, tick), i => Interest(regions, i), DangerAt);
		}

		// IM-1: the published layers answer in the same index space as this Regions only when
		// the (ZoneBacked, Generation, CellCount) triples agree — they are built in the same
		// snapshot, but a consumer must never read ids across a zone re-cut or backing switch.
		static bool LayersMatch(RegionMemory regions, IBotInfluenceMap influence)
		{
			return influence != null && influence.MatchesIndexSpace(regions);
		}

		internal static int PickScoutRegion(RegionMemory regions, CPos from, IReadOnlySet<int> taken,
			Func<int, int> staleness, Func<int, int> interest, Func<int, int> danger)
		{
			var best = -1;
			var bestScore = long.MinValue;
			var cellCount = regions.CellCount;

			for (var i = 0; i < cellCount; i++)
			{
				if (taken.Contains(i))
					continue;

				var stale = staleness(i);
				if (stale <= 0)
					continue;

				var score = (long)stale * (1000 + interest(i)) - danger(i) - DistancePenalty(regions, from, i);
				if (score > bestScore || (score == bestScore && best >= 0 && i < best))
				{
					best = i;
					bestScore = score;
				}
			}

			return best;
		}

		bool AnyStaleRegion(RegionMemory regions, int tick)
		{
			var influence = player.PlayerActor.TraitOrDefault<MasterAiBotModule>()?.Situation?.Influence;
			var layered = LayersMatch(regions, influence);
			for (var i = 0; i < regions.CellCount; i++)
			{
				if ((layered ? influence.Staleness[i] : Staleness(regions, i, tick)) > 0)
					return true;
			}

			return false;
		}

		// True when the memory's region index space moved (backing switch or zone re-cut)
		// since the last check — every id-keyed cache this module holds goes stale at once.
		bool RegionSpaceChanged(RegionMemory regions)
		{
			var zoned = regions.ZoneBacked;
			var generation = regions.Generation;
			if (zoned == lastRegionsZoned && generation == lastRegionsGeneration)
				return false;

			lastRegionsZoned = zoned;
			lastRegionsGeneration = generation;
			return true;
		}

		void DropRegionCaches()
		{
			dangerByRegion.Clear();
			enemySpawnRegions = null;
			scoutTargets.Clear();
		}

		int Staleness(RegionMemory regions, int index, int tick)
		{
			var stalest = 0;
			foreach (var enemyRegions in regions.ByEnemy.Values)
			{
				var region = index < enemyRegions.Length ? enemyRegions[index] : null;
				var seenTick = region?.LastSeenTick ?? 0;
				var everSeen = region?.EverSeen ?? false;
				stalest = Math.Max(stalest, everSeen ? tick - seenTick : tick + Info.StaleAfterTicks);
			}

			if (regions.ByEnemy.Count == 0)
				stalest = tick + Info.StaleAfterTicks;

			return stalest;
		}

		HashSet<int> enemySpawnRegions;

		// Region indices of the map's mpspawn cells, minus the one this bot starts on. Read from the map's actor
		// definitions (as CheckPlayers does) — public, identical for every player, no world scan.
		// Recomputed whenever the index space moves (DropRegionCaches nulls the cache).
		HashSet<int> EnemySpawnRegions(RegionMemory regions)
		{
			if (enemySpawnRegions != null)
				return enemySpawnRegions;

			var own = regions.IndexOf(player.HomeLocation);
			enemySpawnRegions = world.Map.ActorDefinitions
				.Where(d => d.Value.Value == "mpspawn")
				.Select(d => new ActorReference(d.Value.Value, d.Value).Get<LocationInit>().Value)
				.Select(regions.IndexOf)
				.Where(i => i >= 0 && i != own)
				.ToHashSet();
			return enemySpawnRegions;
		}

		int Interest(RegionMemory regions, int index)
		{
			var interest = 0;
			if (Info.EnemySpawnBonus > 0 && EnemySpawnRegions(regions).Contains(index))
				interest += Info.EnemySpawnBonus;

			if (Info.UseTargetIntelBias && mainTargetProvider != null)
			{
				var target = mainTargetProvider.MainTarget;
				if (target != null
					&& regions.ByEnemy.TryGetValue(target, out var targetRegions)
					&& index < targetRegions.Length && targetRegions[index] != null)
					interest += Info.TargetIntelBonus;
			}

			foreach (var enemyRegions in regions.ByEnemy.Values)
			{
				var region = index < enemyRegions.Length ? enemyRegions[index] : null;
				if (region != null)
					interest += (region.ArmyValue + region.DefenceValue + region.EconomyValue) * Info.RememberedValueWeight;
			}

			if (resourceMap != null && IsResourceSite(regions, index))
				interest += Info.ResourceSiteBonus;

			return interest;
		}

		bool IsResourceSite(RegionMemory regions, int index)
		{
			var count = resourceMap.GetIndicesLength();
			for (var i = 0; i < count; i++)
			{
				var indice = resourceMap.GetIndice(i);
				if (indice.ResourceCellsCount > 0 && regions.IndexOf(indice.IndiceCenter) == index)
					return true;
			}

			return false;
		}

		int DangerAt(int index)
		{
			if (!dangerByRegion.TryGetValue(index, out var mark))
				return 0;

			var age = world.WorldTick - mark.Tick;
			if (age > Info.DangerDecayTicks)
				return 0;

			return mark.Value;
		}

		static int DistancePenalty(RegionMemory regions, CPos from, int index)
		{
			return (regions.CenterOf(index) - from).Length / 64;
		}

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			if (e.Attacker == null || !e.Attacker.Info.HasTraitInfo<IOccupySpaceInfo>() || !scouts.Any(u => u.Actor == self))
				return;

			var regions = player.PlayerActor.TraitOrDefault<MasterAiBotModule>()?.Situation?.Regions;
			if (regions == null)
				return;

			// Same index-space guard as the scan loop: a mark written under the new ids must
			// not sit beside stale ones keyed under the old.
			if (RegionSpaceChanged(regions))
				DropRegionCaches();

			var value = e.Attacker.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0;
			var index = regions.IndexOf(e.Attacker.Location);
			dangerByRegion.TryGetValue(index, out var existing);
			dangerByRegion[index] = (existing.Value + Math.Max(1, value), world.WorldTick);
		}

		// The 6c risk gate reads scout-loss marks through this CA-side interface;
		// a region that killed a scout counts its attacker's cost as threat.
		int IBotRegionThreatProvider.RememberedEnemyThreatAt(CPos cell)
		{
			var regions = player.PlayerActor.TraitOrDefault<MasterAiBotModule>()?.Situation?.Regions;
			return IsTraitDisabled || regions == null ? 0 : DangerAt(regions.IndexOf(cell));
		}
	}
}
