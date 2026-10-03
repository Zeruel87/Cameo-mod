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
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits.BotModules.Squads
{
	/// <summary>Which deployment <see cref="GroundUnitsConcaveStateCA"/> runs, chosen by its anchor.</summary>
	enum DeployShape { None, Army, Objective }

	// CV (AI_ARCHITECTURE 12.7a, unified with ATK-1 and DAWN's assault fan 2026-10-02): before the
	// first shot a Rush squad deploys, then commits and hands over to GroundUnitsAttackState.
	// ONE planner (ConcaveEvalCA), two shapes chosen by the anchor:
	//  * Army: observed armed enemies in contact - a range-matched concave arc, staggered commit
	//    so every member reaches its own firing range on the same tick. Gated by the
	//    IBotAssaultFormation provider (AssaultFormationBotModule): no enabled provider, no army shape.
	//  * Objective: no armed enemy in contact, the squad target within AssaultEngageRadiusCells -
	//    the fan's 3-8 prongs on a ~200 degree front around it, hold up to AssaultSyncHoldTicks,
	//    then everyone pushes together (zero-delay commit). Gated by FormationMovement (no provider);
	//    its cooldown lives on the squad.
	// Orders only; every order spends one micro action.
	class GroundUnitsConcaveStateCA : GroundStateBaseCA, IState
	{
		const int ReplanMinTicks = 25;
		const int ReplanAnchorCells = 3;
		const int FormedRadius = 1536;
		const int MaxFormOrders = 3;
		const int CommitRetryTicks = 60;

		// Objective shape (the assault fan's constants): terrain-snap reach, the distance a prong
		// still counts as inbound, the front the prongs spread over, and the same-ground cooldown
		// (the provider's RefanoutCooldownTicks default) kept on the squad.
		const int ObjectiveReachCells = 2;
		const int ObjectiveStraggleCells = 6;
		const int ObjectiveFrontDegrees = 200;
		const int ObjectiveCooldownTicks = 750;
		static readonly List<Actor> NoEnemies = [];
		static readonly BitSet<TargetableType> InfantryTargetTypes = new("Infantry");

		enum CommitReason { None, Formed, UnderFire }

		sealed class Placed
		{
			public Actor Actor;
			public int Range;
			public int Speed;
			public WPos Slot;
			public int Orders;
			public int LastHp;
		}

		sealed class Pending
		{
			public Actor Actor;
			public int DueTick;
		}

		List<Placed> placed;
		readonly HashSet<uint> plannedIds = [];
		readonly List<Pending> pending = [];
		readonly DeployShape shape;
		AssaultFormationSettings settings;
		IBotAssaultFormation provider;
		CPos cooldownCell;
		WPos planAnchor;
		WPos anchor;
		int frontDepth;
		int lastPlanTick = int.MinValue / 2;
		int formStartTick;
		bool committed;

		public GroundUnitsConcaveStateCA(DeployShape shape)
		{
			this.shape = shape;
		}

		public void Activate(SquadCA owner)
		{
			formStartTick = owner.World.WorldTick;

			// Entry already consulted the provider (army shape), so it resolves here; if it vanished
			// since (condition flipped), fall back to the plain advance. The objective shape has no provider.
			var members = Eligible(owner);
			if (members.Count == 0 || shape == DeployShape.None
				|| (shape == DeployShape.Army && !TryGetSettings(owner, CooldownCell(owner, members), out settings, out provider)))
			{
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackMoveStateCA(), false);
				return;
			}

			// A re-entry is not allowed until the cooldown has run; record now so an abort or a
			// commit both restart it (RecordCooldown again) from their own moment.
			cooldownCell = CooldownCell(owner, members);
			RecordCooldown(owner);
		}

		// Army: the provider's per-squad same-ground cooldown. Objective: the squad's own record.
		void RecordCooldown(SquadCA owner)
		{
			if (shape == DeployShape.Army)
				provider?.RecordFanout(owner, cooldownCell);
			else
			{
				owner.DeployCooldownCell = cooldownCell;
				owner.DeployCooldownTick = owner.World.WorldTick;
			}
		}

		static bool ObjectiveCooling(SquadCA owner, CPos targetCell)
		{
			var radius = owner.SquadManager.Info.AssaultEngageRadiusCells;
			return owner.World.WorldTick - owner.DeployCooldownTick < ObjectiveCooldownTicks
				&& (owner.DeployCooldownCell - targetCell).LengthSquared <= radius * radius;
		}

		public void Deactivate(SquadCA owner) { }

		// The provider consult shared by the entry hook and Activate: the enabled
		// IBotAssaultFormation for this squad's bot and the settings it would run with. The
		// provider's own per-squad same-ground cooldown may decline. Cheap and side-effect free.
		internal static bool TryGetSettings(SquadCA owner, CPos cell, out AssaultFormationSettings settings, out IBotAssaultFormation provider)
		{
			settings = default;
			provider = owner.Bot.Player.PlayerActor.TraitsImplementing<IBotAssaultFormation>().FirstEnabledTraitOrDefault();
			return provider != null && provider.TryGetAssaultFormation(owner, cell, out settings);
		}

		// The ground the cooldown is keyed on: the squad target, else the frontline centroid.
		static CPos CooldownCell(SquadCA owner, List<Actor> members)
		{
			if (owner.IsTargetValid)
				return owner.World.Map.CellContaining(owner.Target.CenterPosition);

			return owner.World.Map.CellContaining(Centroid(members));
		}

		// The trigger, read from the attack-move state before its own scan; the shape is the anchor's.
		//  * Army: a Rush squad with an enabled provider, enough weaponed ground members, off the
		//    provider's cooldown, and an observed ARMED enemy within FanoutTriggerCells of the
		//    frontline centroid.
		//  * Objective (DAWN's fan): FormationMovement on, no armed enemy in contact (none in the
		//    attack scan either), the squad target within AssaultEngageRadiusCells of the centroid,
		//    siege advisors say advance, off the squad's own same-ground cooldown.
		// Neither runs once the fight is on for any member: the contact-first all-in handles that.
		public static bool ShouldEnter(SquadCA owner, out DeployShape shape)
		{
			shape = DeployShape.None;

			// Cheapest gates first: classic has neither a provider nor FormationMovement and pays nothing more.
			if (owner.Type != SquadCAType.Rush)
				return false;

			var info = owner.SquadManager.Info;
			var armed = owner.Bot.Player.PlayerActor.TraitsImplementing<IBotAssaultFormation>().FirstEnabledTraitOrDefault() != null;
			if (!armed && !info.FormationMovement)
				return false;

			var members = Eligible(owner);
			if (members.Count == 0)
				return false;

			var scan = WDist.FromCells(info.AttackScanRadius);
			var centroid = Centroid(members);
			var engagedChecked = false;
			if (armed && TryGetSettings(owner, CooldownCell(owner, members), out var settings, out _) && members.Count >= settings.MinSquadSize)
			{
				// Formation is for the approach, not the fight: once the fight is on for any
				// member, the attack-move state's contact-first all-in handles it.
				if (GroundUnitsAttackMoveStateCA.NearestEngagedEnemy(owner, scan) != null)
					return false;

				engagedChecked = true;
				if (GatherEnemies(owner, centroid, WDist.FromCells(settings.FanoutTriggerCells)).Count > 0)
				{
					shape = DeployShape.Army;
					return true;
				}
			}

			if (!info.FormationMovement || !owner.IsTargetValid)
				return false;

			var engage = WDist.FromCells(info.AssaultEngageRadiusCells);
			if ((owner.Target.CenterPosition - centroid).HorizontalLengthSquared > (long)engage.Length * engage.Length
				|| ObjectiveCooling(owner, CooldownCell(owner, members)))
				return false;

			if (!engagedChecked && GroundUnitsAttackMoveStateCA.NearestEngagedEnemy(owner, scan) != null)
				return false;

			if (owner.SquadManager.EvaluateSiege(owner, out _) != SiegeVerdict.Advance
				|| owner.SquadManager.FindClosestEnemy(members[0], scan, owner) != null)
				return false;

			shape = DeployShape.Objective;
			return true;
		}

		public void Tick(SquadCA owner)
		{
			if (!owner.IsValid)
				return;

			var tick = owner.World.WorldTick;
			if (committed)
			{
				TickCommit(owner, tick);
				return;
			}

			var members = Eligible(owner);
			if (members.Count == 0)
			{
				Abort(owner);
				return;
			}

			var centroid = Centroid(members);
			List<Actor> enemies;
			WPos newAnchor;
			int newDepth;
			if (shape == DeployShape.Objective)
			{
				// The objective is the anchor and no enemy is in contact (an engaged one commits
				// under fire below). A target that moved away beyond the engage radius, or died, ends it.
				var engage = WDist.FromCells(owner.SquadManager.Info.AssaultEngageRadiusCells);
				if (!owner.IsTargetValid
					|| (owner.Target.CenterPosition - centroid).HorizontalLengthSquared > (long)engage.Length * engage.Length)
				{
					Abort(owner);
					return;
				}

				enemies = NoEnemies;
				newAnchor = owner.Target.CenterPosition;
				newDepth = 0;
			}
			else
			{
				enemies = GatherEnemies(owner, centroid, WDist.FromCells(settings.FanoutTriggerCells));
				if (!TryAnchor(owner, enemies, centroid, out newAnchor, out newDepth))
				{
					Abort(owner);
					return;
				}
			}

			anchor = newAnchor;
			frontDepth = newDepth;

			var replanRange = WDist.FromCells(ReplanAnchorCells);

			// Re-plan when the anchor moved, or when an eligible member joined while forming (a
			// late joiner gets a slot); both are rate-limited by ReplanMinTicks.
			if (placed == null
				|| (tick - lastPlanTick >= ReplanMinTicks
					&& ((anchor - planAnchor).HorizontalLengthSquared > (long)replanRange.Length * replanRange.Length
						|| members.Any(m => !plannedIds.Contains(m.ActorID)))))
			{
				if (!Plan(owner, members, centroid))
				{
					Abort(owner);
					return;
				}

				lastPlanTick = tick;
				planAnchor = anchor;
			}

			var reason = ShouldCommit(owner, tick, enemies, members);
			if (reason != CommitReason.None)
			{
				Commit(owner, members, enemies, tick, reason == CommitReason.UnderFire);
				TickCommit(owner, tick);
				return;
			}

			foreach (var p in placed)
			{
				if (owner.SquadManager.unitCannotBeOrdered(p.Actor))
					continue;

				// The first form order goes out even to a member still on the march AttackMove;
				// re-issues only for members that are idle, off their slot and under the retry cap.
				if (p.Orders > 0 && (!p.Actor.IsIdle || p.Orders >= MaxFormOrders))
					continue;

				if ((p.Actor.CenterPosition - p.Slot).HorizontalLengthSquared <= (long)FormedRadius * FormedRadius)
					continue;

				if (!owner.SquadManager.TryConsumeMicroActions())
					continue;

				// The objective prongs attack-move (the fan did): a prong that meets something shoots it.
				p.Orders++;
				owner.Bot.QueueOrder(new Order(shape == DeployShape.Objective ? "AttackMove" : "Move", p.Actor, Target.FromCell(owner.World, owner.World.Map.CellContaining(p.Slot)), false));
			}
		}

		bool Plan(SquadCA owner, List<Actor> members, WPos centroid)
		{
			var rules = owner.World.Map.Rules;
			var inputs = new List<ConcaveMember>(members.Count);
			var profiles = new List<BotUnitProfile>(members.Count);
			foreach (var m in members)
			{
				var profile = BotUnitProfiles.Get(rules, m.Info);
				profiles.Add(profile);
				inputs.Add(new ConcaveMember(m.ActorID, m.CenterPosition, profile.MaxRange.Length, profile.Speed,
					profile.TargetTypes.Overlaps(InfantryTargetTypes)));
			}

			ConcaveSlot[] slots;
			int reachCells;
			var map = owner.World.Map;
			if (shape == DeployShape.Objective)
			{
				var info = owner.SquadManager.Info;
				slots = ConcaveEvalCA.PlanObjective(anchor, centroid, WDist.FromCells(info.AssaultFanRadiusCells).Length,
					ObjectiveFrontDegrees, members.ConvertAll(m => m.ActorID), info.AssaultFanMinSlots, info.AssaultFanMaxSlots);
				reachCells = ObjectiveReachCells;
			}
			else
			{
				var p = new ConcaveParams(
					WDist.FromCells(settings.StageMarginCells).Length,
					WDist.FromCells(settings.RankBandCells).Length,
					settings.Spacing,
					settings.MinSpacing,
					settings.ArcDegrees,
					settings.RankGap);

				slots = ConcaveEvalCA.Plan(anchor, centroid, frontDepth, inputs, p);
				reachCells = settings.SlotReachCells;
			}

			var result = new List<Placed>(members.Count);
			var old = placed?.ToDictionary(o => o.Actor);
			plannedIds.Clear();
			foreach (var m in members)
				plannedIds.Add(m.ActorID);

			var valid = 0;
			for (var i = 0; i < members.Count; i++)
			{
				var slotPos = slots[i].Pos;

				// A prong off the map projects onto the ring around the objective, keeping roughly its bearing.
				if (shape == DeployShape.Objective && !map.Contains(map.CellContaining(slotPos)))
					slotPos = map.CenterOfCell(NearestAnnulusCell(map, map.CellContaining(anchor),
						owner.SquadManager.Info.AssaultFanRadiusCells, map.CellContaining(slotPos)));

				if (!TrySnap(owner.World, members[i], slotPos, reachCells, out var cell))
					continue;

				valid++;
				var slot = owner.World.Map.CenterOfCell(cell);
				if (old != null && old.TryGetValue(members[i], out var prev))
				{
					// Slot moved at most a cell: keep the record (and its order count); else a fresh order.
					if ((prev.Slot - slot).HorizontalLengthSquared > 1024L * 1024)
					{
						prev.Slot = slot;
						prev.Orders = 0;
					}

					result.Add(prev);
					continue;
				}

				result.Add(new Placed
				{
					Actor = members[i],
					Range = profiles[i].MaxRange.Length,
					Speed = profiles[i].Speed,
					Slot = slot,
					LastHp = HpOf(members[i]),
				});
			}

			// A choke or a cliff edge: too few usable slots, engage as today. The objective shape never
			// aborts here (the fan did not): members without a slot just join at the commit.
			if (shape == DeployShape.Army && valid * 100 < members.Count * settings.MinValidSlotPct)
				return false;

			placed = result;
			return true;
		}

		// The nearest cell within reachCells of the slot the member's locomotor can enter, stay in
		// and path to. Mirrors HarvesterBotModuleCA's retreat-cell check.
		static bool TrySnap(World world, Actor actor, WPos slot, int reachCells, out CPos cell)
		{
			cell = default;
			var mobile = actor.TraitOrDefault<Mobile>();
			var target = world.Map.CellContaining(slot);
			if (mobile == null || !world.Map.Contains(target))
				return false;

			bool Valid(CPos c) => world.Map.Contains(c)
				&& mobile.CanEnterCell(c, check: BlockedByActor.Immovable)
				&& mobile.CanStayInCell(c)
				&& mobile.PathFinder.PathMightExistForLocomotorBlockedByImmovable(mobile.Locomotor, actor.Location, c);

			cell = mobile.NearestCell(target, Valid, 0, reachCells);
			return Valid(cell);
		}

		CommitReason ShouldCommit(SquadCA owner, int tick, List<Actor> enemies, List<Actor> members)
		{
			// Evaluate every member first (LastHp must update for all), then decide.
			var near = 0;
			var damaged = false;
			var enemyInRange = false;
			var straggler = false;
			var straggleSq = (long)WDist.FromCells(ObjectiveStraggleCells).LengthSquared;
			foreach (var p in placed)
			{
				var slotDistSq = (p.Actor.CenterPosition - p.Slot).HorizontalLengthSquared;
				if (slotDistSq <= (long)FormedRadius * FormedRadius)
					near++;

				if (slotDistSq > straggleSq)
					straggler = true;

				var hp = HpOf(p.Actor);
				if (hp < p.LastHp)
					damaged = true;
				p.LastHp = hp;

			}

			// The fight is on for ANY member (placed or not, either side's weapon range): never keep
			// forming under fire — the zero-delay commit sends everyone on the same tick (§12.7b).
			enemyInRange = GroundUnitsAttackMoveStateCA.NearestEngagedEnemy(owner, WDist.FromCells(owner.SquadManager.Info.AttackScanRadius)) != null;

			if (damaged || enemyInRange)
				return CommitReason.UnderFire;

			// Objective: the synchronized push - every prong within ObjectiveStraggleCells of its slot, or
			// the hold (AssaultSyncHoldTicks) expired. Army: assembled, or the stage deadline.
			if (shape == DeployShape.Objective)
			{
				if (!straggler || tick - formStartTick >= owner.SquadManager.Info.AssaultSyncHoldTicks)
					return CommitReason.Formed;

				return CommitReason.None;
			}

			if (tick - formStartTick >= settings.StageDeadlineTicks || near * 100 >= placed.Count * settings.AssemblePercent)
				return CommitReason.Formed;

			return CommitReason.None;
		}

		// Staggered arrival: member i attack-moves max(t) - t_i ticks after the commit, where
		// t_i is the time from where it stands to its own firing range.
		void Commit(SquadCA owner, List<Actor> members, List<Actor> enemies, int tick, bool underFire)
		{
			committed = true;
			RecordCooldown(owner);

			// The attack state fights owner.TargetActor: the observed enemy nearest the anchor.
			Actor nearest = null;
			var best = long.MaxValue;
			foreach (var e in enemies)
			{
				var d = (e.CenterPosition - anchor).HorizontalLengthSquared;
				if (d < best)
				{
					best = d;
					nearest = e;
				}
			}

			if (nearest != null)
				owner.TargetActor = nearest;

			var distances = placed.ConvertAll(p => ConcaveEvalCA.DistanceToRange(p.Actor.CenterPosition, anchor, frontDepth, p.Range));
			var speeds = placed.ConvertAll(p => p.Speed);

			// The objective shape pushes together (the fan did): no stagger.
			var delays = ConcaveEvalCA.CommitDelays(distances, speeds, underFire || shape == DeployShape.Objective);
			for (var i = 0; i < placed.Count; i++)
				pending.Add(new Pending { Actor = placed[i].Actor, DueTick = tick + delays[i] });

			// Weaponed members without a usable slot join at once.
			var placedActors = placed.Select(p => p.Actor).ToHashSet();
			foreach (var m in members)
				if (!placedActors.Contains(m))
					pending.Add(new Pending { Actor = m, DueTick = tick });
		}

		void TickCommit(SquadCA owner, int tick)
		{
			for (var i = pending.Count - 1; i >= 0; i--)
			{
				var p = pending[i];
				if (owner.SquadManager.unitCannotBeOrdered(p.Actor) || tick > p.DueTick + CommitRetryTicks)
				{
					pending.RemoveAt(i);
					continue;
				}

				if (tick < p.DueTick)
					continue;

				// Denied by the action budget: the member keeps its last order and retries next tick.
				if (!owner.SquadManager.TryConsumeMicroActions())
					continue;

				owner.Bot.QueueOrder(new Order("AttackMove", p.Actor, Target.FromPos(anchor), false));
				pending.RemoveAt(i);
			}

			if (pending.Count == 0)
				owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackState(), false);
		}

		void Abort(SquadCA owner)
		{
			RecordCooldown(owner);
			owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsAttackMoveStateCA(), false);
		}

		// Project an out-of-bounds prong slot onto the ring around the objective - FindTilesInAnnulus only
		// yields contained cells, so the nearest one keeps roughly the desired bearing and radius. Falls
		// back to the objective cell itself when the ring is empty.
		static CPos NearestAnnulusCell(Map map, CPos center, int radiusCells, CPos desired)
		{
			var maxRange = Math.Min(radiusCells + 2, map.Grid.MaximumTileSearchRange - 1);
			var minRange = Math.Max(0, Math.Min(radiusCells - 2, maxRange));
			var best = center;
			var bestSq = int.MaxValue;
			foreach (var c in map.FindTilesInAnnulus(center, minRange, maxRange))
			{
				var distSq = (c - desired).LengthSquared;
				if (distSq < bestSq)
				{
					bestSq = distSq;
					best = c;
				}
			}

			return best;
		}

		// Anchor: centroid of the observed enemies in contact, else the squad target. Front depth:
		// how far the enemy line already sits toward us along anchor -> frontline centroid.
		static bool TryAnchor(SquadCA owner, List<Actor> enemies, WPos centroid, out WPos anchorPos, out int depth)
		{
			depth = 0;
			anchorPos = default;
			if (enemies.Count == 0)
			{
				if (!owner.IsTargetValid)
					return false;

				anchorPos = owner.Target.CenterPosition;
				return true;
			}

			long x = 0, y = 0;
			foreach (var e in enemies)
			{
				x += e.CenterPosition.X;
				y += e.CenterPosition.Y;
			}

			anchorPos = new WPos((int)(x / enemies.Count), (int)(y / enemies.Count), 0);
			var axis = centroid - anchorPos;
			var axisLen = (long)axis.HorizontalLength;
			if (axisLen > 0)
			{
				long front = 0;
				foreach (var e in enemies)
				{
					var d = e.CenterPosition - anchorPos;
					front = Math.Max(front, ((long)d.X * axis.X + (long)d.Y * axis.Y) / axisLen);
				}

				depth = (int)front;
			}

			return true;
		}

		// Observed ARMED enemy units around the frontline centroid (a lone harvester is no reason to deploy). IsPreferredObservedEnemyUnit is the
		// only enemy filter: a unit the bot cannot currently see or legitimately remember is not here.
		static List<Actor> GatherEnemies(SquadCA owner, WPos centroid, WDist radius)
		{
			return owner.World.FindActorsInCircle(centroid, radius)
				.Where(owner.SquadManager.IsPreferredObservedEnemyUnit)
				.Where(e => BotUnitProfiles.Get(owner.World.Map.Rules, e.Info).MaxRange.Length > 0).ToList();
		}

		// Orderable, mobile ground members that have a weapon and are not scouts.
		static List<Actor> Eligible(SquadCA owner)
		{
			var roleMap = owner.SquadManager.ActorRoles;
			var rules = owner.World.Map.Rules;
			var result = new List<Actor>();
			foreach (var u in owner.Units)
			{
				var a = u.Actor;
				if (owner.SquadManager.unitCannotBeOrdered(a) || a.TraitOrDefault<Mobile>() == null)
					continue;

				if (roleMap != null && roleMap.TryGetValue(a.Info.Name, out var roles) && roles.Contains(BotUnitRole.Scout))
					continue;

				if (BotUnitProfiles.Get(rules, a.Info).MaxRange.Length <= 0)
					continue;

				result.Add(a);
			}

			return result;
		}

		static WPos Centroid(List<Actor> members)
		{
			long x = 0, y = 0;
			foreach (var m in members)
			{
				x += m.CenterPosition.X;
				y += m.CenterPosition.Y;
			}

			return new WPos((int)(x / members.Count), (int)(y / members.Count), 0);
		}

		static int HpOf(Actor a)
		{
			return a.TraitOrDefault<IHealth>()?.HP ?? 0;
		}
	}
}
