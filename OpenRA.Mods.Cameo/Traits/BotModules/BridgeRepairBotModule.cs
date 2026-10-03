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
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	// CN3 (AI_MASTER_PLAN §3, crystallized-nexus 30cf70a): port of CNBridgeRepairBotModule. Scans the map's
	// bridge huts every RepairScanInterval ticks and orders owned idle `RepairsBridges` units into damaged
	// ones (worst damage first, one repairer per hut); when no repairer exists at all it requests one from
	// the unit builders, capped at MaximumRepairers. When this module is enabled it owns hut repair:
	// EngineerBotModule skips its own RepairBridge job (one owner per decision), so arming
	// `cn3_bridge_repair` is a clean incumbent-vs-donor swap for the increment A/B, not an additive layer.
	//
	// Cameo changes vs the donor:
	//  - MP determinism (architecture §1.6): the donor's `world.LocalRandom.Next(RepairScanInterval)` scan
	//    offset is a desync hazard — LocalRandom differs per client while order streams must not. The first
	//    scan is offset by `self.ActorID % RepairScanInterval` (ActorID is identical on all clients), and
	//    both scans iterate deterministically (repairers by ActorID; huts worst-damaged first with an
	//    ActorID tiebreak).
	//  - §19.6 unit leases: a repairer is claimed (BotLeasePurpose.Repair) before its order is queued, a
	//    unit another module holds is skipped, the claim is renewed every scan and released when the
	//    assignment is pruned or the trait is disabled; an emergency preempt drops the assignment through
	//    IBotUnitLeaseLost. Without a registry (classic) nothing is claimed — donor behaviour.
	//  - Production demand gates: a RepairerActorTypes entry is requested only when its resolved ActorInfo
	//    carries RepairsBridgesInfo and BuildableInfo — a roster name that cannot repair bridges or is not
	//    buildable is skipped — and the count is capped by the damaged-target count, not just
	//    MaximumRepairers (the donor could queue two types for one hut).
	//  - Hut scan covers both trait kinds: the donor was TS-based so it scanned `BridgeHut` only —
	//    Cameo maps carry `LegacyBridgeHut` (RA/TD flat bridges) which the order targets too.
	//  - CNBotPerf/CNBotLog instrumentation dropped: decisions log via Log.Write + AIUtils.BotDebug.
	[TraitLocation(SystemActors.Player)]
	[Desc("Orders engineers to enter damaged bridge huts and requests replacements when needed.")]
	public class BridgeRepairBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Actor types that can repair bridges via RepairsBridges.")]
		public readonly FrozenSet<string> RepairerActorTypes = FrozenSet<string>.Empty;

		[Desc("Bridge hut actor types to consider. Leave empty to include all BridgeHut actors.")]
		public readonly FrozenSet<string> BridgeHutActorTypes = FrozenSet<string>.Empty;

		[Desc("Delay in ticks between bridge repair scans.")]
		public readonly int RepairScanInterval = 125;

		[Desc("Minimum bridge damage state required before a repairer is assigned.")]
		public readonly DamageState MinimumDamageState = DamageState.Light;

		[Desc("Maximum number of bridge hut options to consider on each scan.")]
		public readonly int MaximumRepairTargetOptions = 25;

		[Desc("Maximum owned or requested repairers for bridge repair support.")]
		public readonly int MaximumRepairers = 2;

		[Desc("Should visibility be considered when searching for repair targets?")]
		public readonly bool CheckRepairTargetsForVisibility = true;

		public override object Create(ActorInitializer init) { return new BridgeRepairBotModule(init.Self, this); }
	}

	public class BridgeRepairBotModule : ConditionalTrait<BridgeRepairBotModuleInfo>, IBotTick, IBotUnitLeaseLost
	{
		const string LeaseOwner = nameof(BridgeRepairBotModule);

		readonly World world;
		readonly OpenRA.Player player;
		readonly Dictionary<Actor, Actor> activeAssignments = [];
		IBotRequestUnitProduction[] requestUnitProduction = [];
		int repairScanTicks;

		public BridgeRepairBotModule(Actor self, BridgeRepairBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;

			// ActorID is identical on all clients — unlike LocalRandom, which would offset the first scan
			// differently per client and make the order stream diverge (§1.6).
			repairScanTicks = (int)(self.ActorID % (uint)RepairScanInterval);
		}

		protected override void Created(Actor self)
		{
			requestUnitProduction = self.Owner.PlayerActor.TraitsImplementing<IBotRequestUnitProduction>().ToArray();
			base.Created(self);
		}

		protected override void TraitDisabled(Actor self)
		{
			var leases = BotUnitLeases.Of(self.Owner);
			foreach (var a in activeAssignments.Keys)
				leases?.Release(a, LeaseOwner);

			activeAssignments.Clear();
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (--repairScanTicks > 0)
				return;

			repairScanTicks = RepairScanInterval;
			QueueRepairOrders(bot);
		}

		/// <summary>An emergency took the unit (§19.6): it is no longer ours to track.</summary>
		void IBotUnitLeaseLost.LeaseLost(Actor actor, string newOwner, BotLeasePurpose purpose)
		{
			activeAssignments.Remove(actor);
		}

		// A hut target as the module sees it: the actor plus the two fields both hut traits expose.
		// Cameo maps place LegacyBridgeHut (RA/TD flat bridges); the donor scanned only BridgeHut
		// (TS elevated bridges, CN's huts) — both are supported so either map style repairs.
		readonly record struct HutTarget(Actor Actor, DamageState State, bool Repairing);

		static HutTarget? ToHutTarget(Actor a)
		{
			var hut = a.TraitOrDefault<BridgeHut>();
			if (hut != null)
				return new HutTarget(a, hut.BridgeDamageState, hut.Repairing);

			var legacy = a.TraitOrDefault<LegacyBridgeHut>();
			if (legacy != null)
				return new HutTarget(a, legacy.BridgeDamageState, legacy.Repairing);

			return null;
		}

		static IEnumerable<HutTarget> HutTargets(World world)
		{
			foreach (var a in world.ActorsHavingTrait<BridgeHut>())
				if (ToHutTarget(a) is HutTarget t)
					yield return t;

			foreach (var a in world.ActorsHavingTrait<LegacyBridgeHut>())
				if (ToHutTarget(a) is HutTarget t)
					yield return t;
		}

		void QueueRepairOrders(IBot bot)
		{
			if (player.WinState != WinState.Undefined)
				return;

			var leases = BotUnitLeases.Of(player);
			PruneAssignments(leases);

			var targets = HutTargets(world)
				.Where(IsRepairTarget)
				.OrderByDescending(t => t.State)
				.ThenBy(t => t.Actor.ActorID)
				.Take(Math.Max(1, Info.MaximumRepairTargetOptions))
				.Select(t => t.Actor)
				.ToList();

			if (targets.Count == 0)
				return;

			var repairers = world.ActorsHavingTrait<RepairsBridges>()
				.Where(a => IsAvailableRepairer(a, leases))
				.OrderBy(a => a.ActorID)
				.ToList();

			if (repairers.Count == 0)
			{
				RequestRepairerProduction(bot, targets.Count);
				return;
			}

			var assignedTargets = activeAssignments.Values.ToHashSet();
			foreach (var repairer in repairers)
			{
				var target = targets
					.Where(t => !assignedTargets.Contains(t))
					.ClosestToWithPathFrom(repairer);

				if (target == null)
					continue;

				// LC1: the claim precedes the order — the order gate refuses a unit we do not hold.
				if (!BotUnitLeases.TryClaim(leases, repairer, LeaseOwner, BotLeasePurpose.Repair, LeaseHeartbeatTicks()))
					continue;

				bot.QueueOrder(new Order("RepairBridge", repairer, Target.FromActor(target), false));
				activeAssignments[repairer] = target;
				assignedTargets.Add(target);

				var line = $"AI ({player.ClientIndex}): Ordered {repairer} to repair bridge hut {target}";
				Log.Write("debug", line);
				AIUtils.BotDebug(line);
			}
		}

		void PruneAssignments(IBotUnitLeases leases)
		{
			var stale = activeAssignments
				.Where(kv => !IsActiveAssignment(kv.Key, kv.Value)
					|| !BotUnitLeases.TryClaim(leases, kv.Key, LeaseOwner, BotLeasePurpose.Repair, LeaseHeartbeatTicks()))
				.Select(kv => kv.Key)
				.ToArray();

			foreach (var repairer in stale)
			{
				activeAssignments.Remove(repairer);
				leases?.Release(repairer, LeaseOwner);
			}
		}

		bool IsActiveAssignment(Actor repairer, Actor target)
		{
			return IsLiveOwnedRepairer(repairer) && !repairer.IsIdle &&
				ToHutTarget(target) is HutTarget t && IsRepairTarget(t);
		}

		bool IsAvailableRepairer(Actor repairer, IBotUnitLeases leases)
		{
			return IsLiveOwnedRepairer(repairer) &&
				repairer.IsIdle &&
				!activeAssignments.ContainsKey(repairer) &&
				!BotUnitLeases.IsClaimedByOther(leases, repairer, LeaseOwner) &&
				repairer.Info.HasTraitInfo<IPositionableInfo>();
		}

		bool IsLiveOwnedRepairer(Actor repairer)
		{
			if (repairer.Owner != player || repairer.IsDead || !repairer.IsInWorld)
				return false;

			if (Info.RepairerActorTypes.Count > 0 && !Info.RepairerActorTypes.Contains(repairer.Info.Name.ToLowerInvariant()))
				return false;

			return repairer.TraitOrDefault<RepairsBridges>() != null;
		}

		bool IsRepairTarget(HutTarget target)
		{
			var actor = target.Actor;
			if (actor == null || actor.IsDead || !actor.IsInWorld)
				return false;

			if (Info.BridgeHutActorTypes.Count > 0 && !Info.BridgeHutActorTypes.Contains(actor.Info.Name.ToLowerInvariant()))
				return false;

			return IsEligibleHut(target.State, target.Repairing,
				!Info.CheckRepairTargetsForVisibility || actor.CanBeViewedByPlayer(player),
				Info.CheckRepairTargetsForVisibility, Info.MinimumDamageState);
		}

		/// <summary>The hut gate, free of world state so it can be tested: damaged at least `minimum`, not
		/// already under repair, and (when `checkVisibility`) visible to the bot.</summary>
		public static bool IsEligibleHut(DamageState state, bool repairing, bool visible, bool checkVisibility, DamageState minimum)
		{
			if (repairing || state < minimum)
				return false;

			return !checkVisibility || visible;
		}

		void RequestRepairerProduction(IBot bot, int damagedTargets)
		{
			if (Info.MaximumRepairers <= 0 || Info.RepairerActorTypes.Count == 0)
				return;

			var unitBuilder = requestUnitProduction.FirstEnabledTraitOrDefault();
			if (unitBuilder == null)
				return;

			var repairerCount = CountOwnedRepairers() + Info.RepairerActorTypes.Sum(type => unitBuilder.RequestedProductionCount(bot, type));
			var remaining = DesiredRepairerCount(damagedTargets, repairerCount, Info.MaximumRepairers);

			foreach (var repairerType in Info.RepairerActorTypes.OrderBy(n => n, StringComparer.Ordinal))
			{
				if (remaining <= 0)
					break;

				if (unitBuilder.RequestedProductionCount(bot, repairerType) > 0)
					continue;

				// Unloaded ContentPacks leave their actor names out of Rules.Actors; TryGetValue is
				// load-bearing. A listed type that cannot repair bridges, or is not buildable at all,
				// is skipped rather than requested (the roster is shared with the capture list).
				if (!world.Map.Rules.Actors.TryGetValue(repairerType, out var actorInfo))
					continue;
				if (!actorInfo.HasTraitInfo<RepairsBridgesInfo>() || !actorInfo.HasTraitInfo<BuildableInfo>())
					continue;

				unitBuilder.RequestUnitProduction(bot, repairerType);
				remaining--;
			}
		}

		/// <summary>How many more repairers the damaged targets justify, free of world state so it can be
		/// tested: one per damaged hut up to `maximum`, minus the owned-or-queued count.</summary>
		public static int DesiredRepairerCount(int safeTargets, int ownedPlusQueued, int maximum)
		{
			if (safeTargets <= 0 || maximum <= 0)
				return 0;

			return Math.Max(0, Math.Min(maximum, safeTargets) - Math.Max(0, ownedPlusQueued));
		}

		int CountOwnedRepairers()
		{
			return world.ActorsHavingTrait<RepairsBridges>().Count(IsLiveOwnedRepairer);
		}

		int RepairScanInterval => Info.RepairScanInterval > 0 ? Info.RepairScanInterval : 1;
		int LeaseHeartbeatTicks() => Math.Max(200, Info.RepairScanInterval * 4);

		// NOTE: there is deliberately no INotifyActorDisposing here. This trait lives on the player
		// actor, so Disposing would only ever fire for the player actor itself — never for a repairer
		// or a bridge hut. A handler that matched `self` against the assignment dictionary could
		// therefore never remove anything. PruneAssignments already drops dead repairers and repaired
		// or destroyed huts at the start of every scan, which is where that cleanup belongs.
	}
}
