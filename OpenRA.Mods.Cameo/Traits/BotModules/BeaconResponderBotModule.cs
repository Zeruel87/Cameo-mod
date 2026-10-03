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
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common.Traits;
using CAAIUtils = OpenRA.Mods.CA.AIUtils;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Phase 8: answers allied beacons. A beacon near remembered/visible enemies",
		"draws idle combat units through the risk gate; a beacon on an allied building",
		"draws a repair unit if the faction has one. Claims only from the squad",
		"manager's idle pool, never from squads. AI_FRANSBOT_RESEARCH.md phase 8.")]
	public class BeaconResponderBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Ticks between beacon scans.")]
		public readonly int ScanInterval = 25;

		[Desc("Maximum idle combat units sent to answer one hostile beacon.")]
		public readonly int MaxResponseUnits = 6;

		[Desc("Hostiles remembered/visible within this many cells of a beacon count as its target.")]
		public readonly int EnemySearchRadiusCells = 8;

		[Desc("An allied building within this many cells of a beacon triggers the support response.")]
		public readonly int SupportSearchRadiusCells = 4;

		[Desc("Minimum ticks a responder stays owned before an idle unit is released back to the pool.",
			"Covers the order-dispatch latency so a just-tasked unit is not reclaimed mid-handoff.")]
		public readonly int ReleaseAfterTicks = 50;

		public override object Create(ActorInitializer init) { return new BeaconResponderBotModule(init.Self, this); }
	}

	public class BeaconResponderBotModule : ConditionalTrait<BeaconResponderBotModuleInfo>,
		IBotTick, IBotEnabled, IBotNotifyIdleBaseUnits
	{
		readonly World world;
		readonly OpenRA.Player player;
		readonly Predicate<Actor> unitCannotBeOrdered;

		readonly List<UnitWposWrapper> responders = new();
		readonly Dictionary<Actor, int> responderAssignedTick = new();

		IBotRegionThreatProvider[] threatProviders;
		List<UnitWposWrapper> idlePool = new();
		int scanTicks;
		int lastProcessedTick = -1;

		public BeaconResponderBotModule(Actor self, BeaconResponderBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			unitCannotBeOrdered = a => a == null || a.IsDead || !a.IsInWorld || a.Owner != player;
		}

		protected override void TraitEnabled(Actor self)
		{
			threatProviders = self.TraitsImplementing<IBotRegionThreatProvider>().ToArray();
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

			var tracker = world.WorldActor.TraitOrDefault<BeaconTracker>();
			if (tracker == null)
				return;

			var tick = world.WorldTick;
			var maxSeen = lastProcessedTick;
			foreach (var entry in tracker.Entries)
			{
				if (entry.Tick <= lastProcessedTick)
					continue;

				maxSeen = System.Math.Max(maxSeen, entry.Tick);

				// Only allied beacons, and not our own.
				if (entry.Owner == player || !entry.Owner.IsAlliedWith(player))
					continue;

				Respond(bot, entry);
			}

			lastProcessedTick = maxSeen;

			// LC1 heartbeat: renew every responder each scan; one dropped by the release below stops being renewed.
			var leases = BotUnitLeases.Of(player);
			if (leases != null)
				foreach (var r in responders)
					leases.TryClaim(r.Actor, LeaseOwner, BotLeasePurpose.Beacon, ResponderLeaseTicks);

			// Release responders that are done (same ownership-release discipline as scouts).
			if (responders.Count != 0)
			{
				var squadOwned = player.PlayerActor.TraitsImplementing<SquadManagerBotModuleCA>()
					.Where(m => !m.IsTraitDisabled)
					.SelectMany(m => m.Squads)
					.SelectMany(s => s.Units)
					.Select(u => u.Actor)
					.ToHashSet();

				foreach (var r in responders.Where(u =>
					unitCannotBeOrdered(u.Actor) || squadOwned.Contains(u.Actor) ||
					u.Actor.IsIdle && tick - responderAssignedTick.GetValueOrDefault(u.Actor) >= Info.ReleaseAfterTicks).ToArray())
				{
					responderAssignedTick.Remove(r.Actor);
					responders.Remove(r);

					// Alive and not squad-owned -> hand back to the idle pool; a unit
					// removed from the pool but only held in activeUnits is stranded
					// (FindNewUnits skips activeUnits), so squads would never see it.
					if (!unitCannotBeOrdered(r.Actor) && !squadOwned.Contains(r.Actor)
						&& idlePool != null && idlePool.All(u => u.Actor != r.Actor))
						idlePool.Add(r);
				}
			}
		}

		void Respond(IBot bot, BeaconTracker.Entry entry)
		{
			var cell = world.Map.CellContaining(entry.Position);
			var threat = threatProviders == null ? 0 : threatProviders.Max(p => p.RememberedEnemyThreatAt(cell));

			// Visible enemies near the beacon count too — gated by CanBeViewedByPlayer so
			// actors hidden under fog/shroud do not leak into the response decision.
			var visibleEnemies = world.FindActorsInCircle(entry.Position, WDist.FromCells(Info.EnemySearchRadiusCells))
				.Where(a => !a.IsDead && a.IsInWorld && player.RelationshipWith(a.Owner) == PlayerRelationship.Enemy
					&& a.CanBeViewedByPlayer(player))
				.ToList();

			if (threat > 0 || visibleEnemies.Count > 0)
			{
				CombatResponse(bot, cell, threat + visibleEnemies.Sum(a => a.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0));
				return;
			}

			// Support response: allied building near the beacon pulls a repair unit.
			var alliedBuilding = world.FindActorsInCircle(entry.Position, WDist.FromCells(Info.SupportSearchRadiusCells))
				.FirstOrDefault(a => !a.IsDead && a.IsInWorld && a.Info.HasTraitInfo<BuildingInfo>() &&
					a.Owner.IsAlliedWith(player));

			if (alliedBuilding != null)
				SupportResponse(bot, cell);
		}

		const string LeaseOwner = nameof(BeaconResponderBotModule);

		// LC1: three scans — survives the order latency, frees a dropped responder within seconds.
		int ResponderLeaseTicks => 3 * System.Math.Max(1, Info.ScanInterval);

		void CombatResponse(IBot bot, CPos cell, int threat)
		{
			if (idlePool == null)
				return;

			var leases = BotUnitLeases.Of(player);
			var candidates = idlePool
				.Where(u => !unitCannotBeOrdered(u.Actor) && u.Actor.Info.HasTraitInfo<ArmamentInfo>()
					&& responders.All(r => r.Actor != u.Actor)
					&& !BotUnitLeases.IsClaimedByOther(leases, u.Actor, LeaseOwner))
				.OrderBy(u => (u.Actor.CenterPosition - world.Map.CenterOfCell(cell)).Length)
				.Take(Info.MaxResponseUnits)
				.ToList();

			if (candidates.Count == 0)
				return;

			var value = candidates.Sum(u => u.Actor.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0);
			var manager = player.PlayerActor.TraitsImplementing<SquadManagerBotModuleCA>()
				.FirstOrDefault(m => !m.IsTraitDisabled);
			var margin = manager?.Info.AttackRiskMargin ?? 25;

			// The risk gate applies: do not feed a beacon the enemy out-values us on.
			if (!SquadManagerBotModuleCA.PassesRiskGate(value, threat, margin))
				return;

			foreach (var u in candidates)
			{
				idlePool.Remove(u);
				responders.Add(u);
				responderAssignedTick[u.Actor] = world.WorldTick;
				BotUnitLeases.TryClaim(leases, u.Actor, LeaseOwner, BotLeasePurpose.Beacon, ResponderLeaseTicks);
			}

			bot.QueueOrder(new Order("AttackMove", null, Target.FromCell(world, cell), false,
				groupedActors: candidates.Select(u => u.Actor).ToArray()));
			CAAIUtils.BotDebug("AI ({0}): beacon response — {1} units to {2}", player.ClientIndex, candidates.Count, cell);
		}

		void SupportResponse(IBot bot, CPos cell)
		{
			if (idlePool == null)
				return;

			var support = idlePool
				.Where(u => !unitCannotBeOrdered(u.Actor) && responders.All(r => r.Actor != u.Actor)
					&& (u.Actor.Info.HasTraitInfo<RepairsUnitsInfo>() || u.Actor.Info.HasTraitInfo<InstantlyRepairsInfo>()
						|| u.Actor.Info.HasTraitInfo<RepairsBridgesInfo>()))
				.OrderBy(u => (u.Actor.CenterPosition - world.Map.CenterOfCell(cell)).Length)
				.FirstOrDefault();

			if (support == null)
				return;

			idlePool.Remove(support);
			responders.Add(support);
			responderAssignedTick[support.Actor] = world.WorldTick;
			bot.QueueOrder(new Order("Move", support.Actor, Target.FromCell(world, cell), false));
			CAAIUtils.BotDebug("AI ({0}): beacon support response — {1} to {2}", player.ClientIndex, support.Actor, cell);
		}
	}
}
