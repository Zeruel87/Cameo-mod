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
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	/// <summary>
	/// Cheap shared per-player snapshot plus fair enemy combat/structure memory. Mobile
	/// contacts decay by age because they can move. Observed enemy buildings are static
	/// knowledge and persist at full confidence until their exact last-seen cell is directly
	/// observed again and the building is no longer present/enemy-owned. Hidden actors are
	/// never queried directly.
	/// </summary>

	public readonly record struct FransCombatIntelContact(
		uint ActorId,
		string ActorType,
		Player Owner,
		CPos LastSeenCell,
		int FullValue,
		int EstimatedValue,
		int LastSeenWorldTick,
		bool IsVisible,
		bool IsBuilding,
		bool IsDefensiveBuilding);

	public interface IFransCombatIntelService
	{
		IReadOnlyList<Actor> VisibleActors { get; }
		IReadOnlyList<Actor> VisibleEnemies { get; }
		IReadOnlyList<FransCombatIntelContact> EnemyCombatContacts { get; }
		bool TryGetEnemyCombatContact(uint actorId, out FransCombatIntelContact contact);
		bool IsCombatThreat(Actor actor);
		bool IsTacticalCombatThreat(Actor actor);
		IReadOnlyList<Actor> OwnedActors { get; }
		int VisibleEnemyCombatUnitCount { get; }
		int RememberedEnemyCombatUnitCount { get; }
		int VisibleEnemyCombatValue { get; }
		int EstimatedEnemyCombatValue { get; }
		int EstimateEnemyCombatValueNear(CPos center, int radiusCells, Player preferredEnemy, out int visibleValue, out int rememberedUnits);
		void EnsureCurrentSnapshot();
		int SnapshotWorldTick { get; }
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Shared Fransbot actor-intel snapshot plus fair last-seen enemy force estimation.")]
	public class FransCombatIntelBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("World ticks between shared actor-intel refreshes.")]
		public readonly int ScanInterval = 25;

		[Desc("World ticks before a last-seen MOBILE enemy combat contact contributes zero estimated force value. Buildings persist until direct observation disproves them.")]
		public readonly int EnemyForceMemoryDuration = 6000;

		[Desc("World ticks between concise force-estimate debug summaries.")]
		public readonly int ForceSummaryInterval = 1500;

		[ActorReference]
		[Desc("Explicit enemy defensive structures. also treats any armed enemy building as defensive for Intel value, so anti-air defenses are no longer passive scenery.")]
		public readonly FrozenSet<string> StaticGroundDefenseTypes =
			FrozenSet<string>.Empty;

		[Desc("Intel combat-value multiplier applied to defensive/armed enemy buildings. 100 means purchase cost at full value.")]
		public readonly int StaticGroundDefenseValuePercent = 100;

		[Desc("Intel combat-value multiplier applied to passive/unarmed enemy buildings. 1 means one percent of purchase cost: enough to keep a remembered attack objective alive without making passive structures look like real battlefield firepower.")]
		public readonly int PassiveBuildingValuePercent = 1;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);
			if (ScanInterval <= 0)
				throw new YamlException($"{nameof(ScanInterval)} must be greater than zero.");
			if (EnemyForceMemoryDuration <= 0)
				throw new YamlException($"{nameof(EnemyForceMemoryDuration)} must be greater than zero.");
			if (ForceSummaryInterval <= 0)
				throw new YamlException($"{nameof(ForceSummaryInterval)} must be greater than zero.");
			if (StaticGroundDefenseValuePercent <= 0)
				throw new YamlException($"{nameof(StaticGroundDefenseValuePercent)} must be greater than zero.");
			if (PassiveBuildingValuePercent <= 0)
				throw new YamlException($"{nameof(PassiveBuildingValuePercent)} must be greater than zero.");
		}

		public override object Create(ActorInitializer init) { return new FransCombatIntelBotModule(init.Self, this); }
	}

	public class FransCombatIntelBotModule : ConditionalTrait<FransCombatIntelBotModuleInfo>,
		IBotTick, IFransCombatIntelService
	{
		sealed class EnemyCombatMemory
		{
			public string ActorType;
			public Player Owner;
			public CPos LastSeenCell;
			public int FullValue;
			public int LastSeenWorldTick;
			public bool CanRemainHiddenWhileObserved;
			public bool IsBuilding;
			public bool IsDefensiveBuilding;
		}

		readonly World world;
		readonly Player player;
		readonly Dictionary<uint, EnemyCombatMemory> enemyCombatMemory = [];
		Shroud shroud;

		uint[] visibleActorIds = [];
		uint[] visibleEnemyActorIds = [];
		FransCombatIntelContact[] enemyCombatContacts = [];
		uint[] ownedActorIds = [];
		Actor[] resolvedVisibleActors = [];
		Actor[] resolvedVisibleEnemies = [];
		Actor[] resolvedOwnedActors = [];
		int resolvedActorsWorldTick = -1;
		int scanTicks;
		int nextForceSummaryTick;
		int nextReconcileSummaryTick;
		int pendingReconciledContacts;

		public FransCombatIntelBotModule(Actor self, FransCombatIntelBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		public IReadOnlyList<Actor> VisibleActors
		{
			get
			{
				EnsureResolvedActors();
				return resolvedVisibleActors;
			}
		}

		public IReadOnlyList<Actor> VisibleEnemies
		{
			get
			{
				EnsureResolvedActors();
				return resolvedVisibleEnemies;
			}
		}

		public IReadOnlyList<FransCombatIntelContact> EnemyCombatContacts => enemyCombatContacts;

		public IReadOnlyList<Actor> OwnedActors
		{
			get
			{
				EnsureResolvedActors();
				return resolvedOwnedActors;
			}
		}
		public int VisibleEnemyCombatUnitCount { get; private set; }
		public int RememberedEnemyCombatUnitCount { get; private set; }
		public int VisibleEnemyCombatValue { get; private set; }
		public int EstimatedEnemyCombatValue { get; private set; }
		public int SnapshotWorldTick { get; private set; } = -1;

		protected override void Created(Actor self)
		{
			if (world.Type == WorldType.Editor)
				return;

			shroud = self.Trait<Shroud>();
		}

		protected override void TraitEnabled(Actor self)
		{
			scanTicks = (int)self.ActorID % Info.ScanInterval + 1;
			nextForceSummaryTick = world.WorldTick + Info.ForceSummaryInterval + (int)self.ActorID % Info.ScanInterval;
			nextReconcileSummaryTick = world.WorldTick + Math.Max(250, Info.ScanInterval * 4);
			pendingReconciledContacts = 0;
			FransBotLog.BotDebug(world,
				"{0}: FransCombatIntel PERSISTENT STRUCTURE MEMORY + LIVE-ID SNAPSHOT active: mobile contacts still decay, but observed enemy buildings remain at their last-seen cells with full remembered value until direct observation proves them gone/changed. Only ActorIDs are retained for live snapshots. Armed/defensive buildings use {1}% purchase cost, passive buildings use {2}%.",
				player, Info.StaticGroundDefenseValuePercent, Info.PassiveBuildingValuePercent);
		}

		protected override void TraitDisabled(Actor self)
		{
			visibleActorIds = [];
			visibleEnemyActorIds = [];
			enemyCombatContacts = [];
			ownedActorIds = [];
			resolvedVisibleActors = [];
			resolvedVisibleEnemies = [];
			resolvedOwnedActors = [];
			resolvedActorsWorldTick = -1;
			enemyCombatMemory.Clear();
			VisibleEnemyCombatUnitCount = 0;
			RememberedEnemyCombatUnitCount = 0;
			VisibleEnemyCombatValue = 0;
			EstimatedEnemyCombatValue = 0;
			SnapshotWorldTick = -1;
			pendingReconciledContacts = 0;
			nextReconcileSummaryTick = 0;
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransCombatIntel.BotTick");
			if (player.WinState != WinState.Undefined)
				return;

			if (--scanTicks > 0)
				return;

			scanTicks = Info.ScanInterval;
			EnsureCurrentSnapshot();
		}

		public void EnsureCurrentSnapshot()
		{
			// this is a shared SENSOR snapshot, not a per-consumer "current tick" query.
			// General, RiskModel and the three Commanders are intentionally phase-spread; requiring
			// SnapshotWorldTick == world.WorldTick made each of them rebuild the same full actor list
			// on different ticks. Keep one coherent snapshot for the configured sensor interval.
			if (SnapshotWorldTick >= 0 && world.WorldTick - SnapshotWorldTick < Info.ScanInterval)
				return;

			Refresh();
			// A consumer-triggered refresh satisfies the normal periodic sensor cadence too.
			scanTicks = Info.ScanInterval;
		}

		void Refresh()
		{
			var visible = new List<Actor>();
			var enemies = new List<Actor>();
			var owned = new List<Actor>();
			var seenEnemyCombatIds = new HashSet<uint>();
			var visibleCombatUnits = 0;
			var visibleCombatValue = 0;

			foreach (var actor in world.Actors)
			{
				if (actor == null || !actor.IsInWorld || actor.IsDead)
					continue;

				if (actor.Owner == player)
				{
					owned.Add(actor);
					visible.Add(actor);
					continue;
				}

				if (!actor.CanBeViewedByPlayer(player))
					continue;

				visible.Add(actor);
				if (actor.Owner == null ||
					!PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(actor.Owner)))
					continue;

				// crash/death husks remain visible world actors but are not enemy contacts.
				// This prevents them from entering any Commander fallback target list.
				if (IsNonCombatHusk(actor))
					continue;

				enemies.Add(actor);
				if (!IsCombatThreat(actor))
					continue;

				var value = GetCombatValue(actor);
				visibleCombatUnits++;
				visibleCombatValue += value;
				seenEnemyCombatIds.Add(actor.ActorID);
				var isBuilding = actor.Info.HasTraitInfo<BuildingInfo>();
				var isDefensiveBuilding = isBuilding && IsDefensiveBuilding(actor);
				enemyCombatMemory[actor.ActorID] = new EnemyCombatMemory
				{
					ActorType = actor.Info.Name,
					Owner = actor.Owner,
					LastSeenCell = actor.Location,
					FullValue = value,
					LastSeenWorldTick = world.WorldTick,
					CanRemainHiddenWhileObserved = actor.Info.HasTraitInfo<CloakInfo>(),
					IsBuilding = isBuilding,
					IsDefensiveBuilding = isDefensiveBuilding
				};
			}

			var staleIds = new List<uint>();
			var estimatedValue = 0;
			var rememberedOnlyCount = 0;
			var reconciledMissingCount = 0;
			foreach (var pair in enemyCombatMemory)
			{
				var memory = pair.Value;
				var age = Math.Max(0, world.WorldTick - memory.LastSeenWorldTick);
				if (!memory.IsBuilding && age >= Info.EnemyForceMemoryDuration)
				{
					staleIds.Add(pair.Key);
					continue;
				}

				// Fair-intel reconciliation: if the exact last-seen cell is currently observed and
				// the remembered actor is not visible there (or anywhere else) anymore, a human
				// would know that this contact is no longer at the remembered location. Remove the
				// local-force memory immediately instead of carrying a dead/moved phantom for 6000 WT.
				// Cloaked actors are exempt because an observed terrain cell does not prove they left.
				if (!seenEnemyCombatIds.Contains(pair.Key) && !memory.CanRemainHiddenWhileObserved &&
					IsCellCurrentlyObserved(memory.LastSeenCell))
				{
					staleIds.Add(pair.Key);
					reconciledMissingCount++;
					continue;
				}

				var remaining = Math.Max(0, Info.EnemyForceMemoryDuration - age);
				estimatedValue += memory.IsBuilding
					? memory.FullValue
					: memory.FullValue * remaining / Info.EnemyForceMemoryDuration;
				if (!seenEnemyCombatIds.Contains(pair.Key))
					rememberedOnlyCount++;
			}

			foreach (var id in staleIds)
				enemyCombatMemory.Remove(id);

			var contacts = new List<FransCombatIntelContact>(enemyCombatMemory.Count);
			foreach (var pair in enemyCombatMemory.OrderBy(p => p.Key))
			{
				var memory = pair.Value;
				var age = Math.Max(0, world.WorldTick - memory.LastSeenWorldTick);
				var remaining = Math.Max(0, Info.EnemyForceMemoryDuration - age);
				var estimated = memory.IsBuilding
					? memory.FullValue
					: memory.FullValue * remaining / Info.EnemyForceMemoryDuration;
				contacts.Add(new FransCombatIntelContact(
					pair.Key, memory.ActorType, memory.Owner, memory.LastSeenCell, memory.FullValue, estimated,
					memory.LastSeenWorldTick, seenEnemyCombatIds.Contains(pair.Key), memory.IsBuilding, memory.IsDefensiveBuilding));
			}

			visibleActorIds = visible.Select(a => a.ActorID).ToArray();
			visibleEnemyActorIds = enemies.Select(a => a.ActorID).ToArray();
			ownedActorIds = owned.Select(a => a.ActorID).ToArray();
			resolvedActorsWorldTick = -1;
			VisibleEnemyCombatUnitCount = visibleCombatUnits;
			RememberedEnemyCombatUnitCount = rememberedOnlyCount;
			VisibleEnemyCombatValue = visibleCombatValue;
			EstimatedEnemyCombatValue = estimatedValue;
			enemyCombatContacts = contacts.ToArray();
			SnapshotWorldTick = world.WorldTick;

			if (reconciledMissingCount > 0)
				pendingReconciledContacts += reconciledMissingCount;

			// Reconciliation can happen for many destroyed/moving units during a large battle.
			// Aggregate the diagnostics so fair-intel cleanup does not become new per-scan log spam.
			if (pendingReconciledContacts > 0 && world.WorldTick >= nextReconcileSummaryTick)
			{
				FransBotLog.BotDebug(world,
					"{0}: combat intel reconciled {1} stale mobile/structure contact(s) since the last summary because their last-seen cells were directly visible and the actors were no longer there/enemy-owned; remembered knowledge was removed immediately.",
					player, pendingReconciledContacts);
				pendingReconciledContacts = 0;
				nextReconcileSummaryTick = world.WorldTick + Math.Max(250, Info.ScanInterval * 4);
			}

			if (world.WorldTick >= nextForceSummaryTick)
			{
				nextForceSummaryTick = world.WorldTick + Info.ForceSummaryInterval;
				FransBotLog.BotDebug(world,
					"{0}: combat intel sees {1} enemy combat threat(s) value {2}; remembers {3}; believed combat value {4}.",
					player, VisibleEnemyCombatUnitCount, VisibleEnemyCombatValue, RememberedEnemyCombatUnitCount, EstimatedEnemyCombatValue);
			}
		}


		void EnsureResolvedActors()
		{
			// Never retain live Actor references across world ticks. Actors may be removed from World
			// when killed, transformed, captured into cargo, sold, or otherwise disposed. Holding the
			// old Actor object for the full 25-WT sensor interval can make a later consumer dereference
			// an Actor whose Positionable/traits have already been disposed.
			//
			// The expensive operation remains the one full world scan in Refresh(). Between scans we
			// only resolve the small cached ID sets through World.GetActorById, at most once per WT.
			if (resolvedActorsWorldTick == world.WorldTick)
				return;

			resolvedOwnedActors = ResolveLiveActors(ownedActorIds,
				a => a.Owner == player);
			resolvedVisibleActors = ResolveLiveActors(visibleActorIds,
				a => a.Owner == player || a.CanBeViewedByPlayer(player));
			resolvedVisibleEnemies = ResolveLiveActors(visibleEnemyActorIds,
				a => a.Owner != null &&
					PlayerRelationship.Enemy.HasRelationship(player.RelationshipWith(a.Owner)) &&
					a.CanBeViewedByPlayer(player));
			resolvedActorsWorldTick = world.WorldTick;
		}

		Actor[] ResolveLiveActors(IEnumerable<uint> actorIds, Func<Actor, bool> predicate)
		{
			var resolved = new List<Actor>();
			foreach (var id in actorIds)
			{
				var actor = world.GetActorById(id);
				// Fransbot live snapshots represent physical map actors. System/player actors can be
				// in World.Actors with no IOccupySpace, which makes Actor.Location invalid.
				if (actor == null || !actor.IsInWorld || actor.IsDead || actor.OccupiesSpace == null || !predicate(actor))
					continue;

				resolved.Add(actor);
			}

			return resolved.ToArray();
		}


		public bool TryGetEnemyCombatContact(uint actorId, out FransCombatIntelContact contact)
		{
			EnsureCurrentSnapshot();
			foreach (var candidate in enemyCombatContacts)
				if (candidate.ActorId == actorId)
				{
					contact = candidate;
					return true;
				}

			contact = default;
			return false;
		}

		public int EstimateEnemyCombatValueNear(CPos center, int radiusCells, Player preferredEnemy, out int visibleValue, out int rememberedUnits)
		{
			EnsureCurrentSnapshot();
			visibleValue = 0;
			rememberedUnits = 0;
			if (radiusCells <= 0)
				return 0;

			var radiusSquared = radiusCells * radiusCells;
			foreach (var actor in VisibleEnemies)
			{
				if (actor == null || !actor.IsInWorld || actor.IsDead || !IsCombatThreat(actor) ||
					(preferredEnemy != null && actor.Owner != preferredEnemy) ||
					(actor.Location - center).LengthSquared > radiusSquared)
					continue;

				visibleValue += GetCombatValue(actor);
			}

			var estimatedValue = 0;
			foreach (var pair in enemyCombatMemory)
			{
				var memory = pair.Value;
				if ((preferredEnemy != null && memory.Owner != preferredEnemy) ||
					(memory.LastSeenCell - center).LengthSquared > radiusSquared)
					continue;

				var age = Math.Max(0, world.WorldTick - memory.LastSeenWorldTick);
				if (!memory.IsBuilding && age >= Info.EnemyForceMemoryDuration)
					continue;

				var remaining = Math.Max(0, Info.EnemyForceMemoryDuration - age);
				estimatedValue += memory.IsBuilding
					? memory.FullValue
					: memory.FullValue * remaining / Info.EnemyForceMemoryDuration;
				if (memory.LastSeenWorldTick < SnapshotWorldTick)
					rememberedUnits++;
			}

			return estimatedValue;
		}

		bool IsCellCurrentlyObserved(CPos cell)
		{
			return world.Map.Contains(cell) && (shroud == null || shroud.Disabled || shroud.IsVisible(cell));
		}

		static bool IsNonCombatHusk(Actor actor) => actor?.Info != null &&
			(actor.Info.HasTraitInfo<HuskInfo>() || actor.Info.Name.EndsWith(".husk", StringComparison.OrdinalIgnoreCase));

		public bool IsCombatThreat(Actor actor)
		{
			if (actor == null || !actor.IsInWorld || actor.IsDead || IsNonCombatHusk(actor))
				return false;

			// every observed enemy building becomes persistent fair Intel. Armed/defensive
			// buildings carry full purchase cost; passive buildings carry only one percent by default.
			// Mobile contacts still require an actual attack trait to count as combat Intel.
			if (actor.Info.HasTraitInfo<BuildingInfo>())
				return true;

			return actor.Info.HasTraitInfo<AttackBaseInfo>();
		}

		bool IsDefensiveBuilding(Actor actor)
		{
			return actor != null && actor.Info.HasTraitInfo<BuildingInfo>() &&
				(Info.StaticGroundDefenseTypes.Contains(actor.Info.Name) || actor.Info.HasTraitInfo<AttackBaseInfo>());
		}

		public bool IsTacticalCombatThreat(Actor actor)
		{
			if (actor == null || !actor.IsInWorld || actor.IsDead || IsNonCombatHusk(actor))
				return false;
			if (actor.Info.HasTraitInfo<BuildingInfo>())
				return IsDefensiveBuilding(actor);
			return actor.Info.HasTraitInfo<AttackBaseInfo>();
		}

		int GetCombatValue(Actor actor)
		{
			var value = Math.Max(1, actor.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 1);
			if (!actor.Info.HasTraitInfo<BuildingInfo>())
				return value;

			var percent = IsDefensiveBuilding(actor) ? Info.StaticGroundDefenseValuePercent : Info.PassiveBuildingValuePercent;
			return Math.Max(1, value * percent / 100);
		}
	}
}
