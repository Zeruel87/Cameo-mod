#region Copyright & License Information
/*
 * Copyright (c) OpenRA Developers and Contributors
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
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Army staging planner (DESIGN 19.12, AI_ARCHITECTURE 12.29): WHERE the idle army waits. One staging point per threatened side, on the",
		"rim a few cells inside the own armed buildings; several defence groups only when the base is hit from several sides; a small centre",
		"reserve for attacks that come from inside the ring. The prior is the direction of the enemy spawn candidates and of seen enemy defences;",
		"the picture then follows the bot's own attack events (decaying weight per 45-degree sector).",
		"A PURE PLANNER: it publishes IBotArmyStaging and issues NO orders. The squad manager stays the only owner of the idle pool and the base",
		"builder points factory rally points at the primary staging cell. With no enabled provider every consumer keeps today's behaviour.",
		"",
		"FIXED POINT: weights are integers (an attacker's cost, kept in thousandths internally); shares are whole percents.")]
	public class ArmyStagingBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("A staging point sits this many cells inside the median radius of the own armed buildings of its sector (never beyond it, so never beyond tower range).")]
		public readonly int StagingInsetCells = 3;

		[Desc("A sector needs at least this percent of the decayed rim weight to get a defence group.")]
		public readonly int ActiveSectorSharePct = 20;

		[Desc("At most this many defence groups (the heaviest sectors win).")]
		public readonly int MaxDefenceGroups = 3;

		[Desc("A group whose share of the idle army value is below this merges into the nearest other group. About two light units: a smaller squad loses its fight alone.")]
		public readonly int MinGroupValue = 1500;

		[Desc("The centre reserve takes the inside share of the attack weight, at most this percent of the idle army value.")]
		public readonly int ReserveMaxPct = 35;

		[Desc("The whole army waits in the centre only when the inside share of the attack weight reaches this percent (sneak attacks that bypass the defences).")]
		public readonly int CentreSwitchPct = 60;

		[Desc("An attack event younger than this many ticks is live in its sector (150 = 6 s at the normal game speed).")]
		public readonly int LiveAttackTicks = 150;

		[Desc("No live attack for this many ticks: the groups return to their staging points (375 = 15 s). Until then they hold the last live assignment.")]
		public readonly int ReturnAfterTicks = 375;

		[Desc("A pool unit is ordered to its point at most every this many ticks (also the squad manager's cadence).")]
		public readonly int StagingInterval = 50;

		[Desc("A pool unit within this many cells of its point is left alone.")]
		public readonly int StagingRadiusCells = 5;

		[Desc("Half-life of the attack weight in ticks (3000 = 2 minutes): the picture follows the game, an old side fades back to the prior.")]
		public readonly int WeightHalfLifeTicks = 3000;

		[Desc("Ticks between recomputes of the plan.")]
		public readonly int PlanIntervalTicks = 25;

		[Desc("The prior counts as this much attacker value in total, shared over the spawn-candidate and seen-defence directions. Real events outweigh it after about two units' worth.")]
		public readonly int PriorWeightValue = 2000;

		[Desc("One attacker adds weight at most once per this many ticks, so a single tank firing for a minute is not a whole army (its live flag still follows every hit).")]
		public readonly int EventDedupeTicks = 150;

		[Desc("An own actor within this many cells of the base centre counts as 'in the base' for attack events; DF-2 threats aimed inside it are answered by the staging.")]
		public readonly int BaseRadiusCells = 30;

		[Desc("A map spawn point within this many cells of an own or allied start is that team's own, not an enemy candidate.")]
		public readonly int SpawnMatchCells = 8;

		[Desc("Read the DF-2 threat prediction (IBotThreatPredictionProvider) as an extra live-attack input.")]
		public readonly bool UsePrediction = true;

		public override object Create(ActorInitializer init) { return new ArmyStagingBotModule(init.Self, this); }
	}

	public class ArmyStagingBotModule : ConditionalTrait<ArmyStagingBotModuleInfo>, IBotTick, IBotRespondToAttack, IBotArmyStaging
	{
		sealed class AttackEvent
		{
			public int Tick, WeightTick, Sector, Value;
			public bool Inside;
		}

		readonly World world;
		readonly OpenRA.Player player;

		// Learned weight in thousandths of a value unit.
		readonly long[] learnedMilli = new long[ArmyStagingEval.Sectors];
		long insideMilli;
		readonly Dictionary<uint, AttackEvent> events = new();

		List<CPos> enemySpawns;
		IBotRememberedDefenceProvider[] defenceProviders;
		IBotThreatPredictionProvider[] predictionProviders;

		int nextPlanTick, lastPlanTick;
		int lastLiveTick = int.MinValue / 2;
		long lastIdleValue;

		// The last live assignment, kept until ReturnAfterTicks passes without a live attack: group sector -> sector it converged on.
		Dictionary<int, int> heldGroupTargets = new();
		int heldReserveTarget = -1;

		public ArmyStagingPlan Plan { get; private set; }

		int IBotArmyStaging.StagingIntervalTicks => Math.Max(1, Info.StagingInterval);
		int IBotArmyStaging.StagingRadiusCells => Math.Max(0, Info.StagingRadiusCells);

		public ArmyStagingBotModule(Actor self, ArmyStagingBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (IsTraitDisabled)
				return;

			var tick = world.WorldTick;
			if (tick < nextPlanTick)
				return;

			nextPlanTick = tick + Math.Max(1, Info.PlanIntervalTicks);
			Recompute(tick);
		}

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			var plan = Plan;
			var attacker = e.Attacker;
			if (IsTraitDisabled || plan == null || attacker == null || attacker.IsDead || !attacker.IsInWorld)
				return;

			// Own attack events only: an enemy ground unit that just hurt one of our actors near the base. Air raids are the anti-air
			// defences' job and neither move the army nor weigh a sector.
			// An attacker is revealed when it fires (RevealOnFire), so its position and type are fair information (maintainer 2026-10-03).
			if (player.RelationshipWith(attacker.Owner) != PlayerRelationship.Enemy || attacker.Info.HasTraitInfo<AircraftInfo>())
				return;

			var radius = (long)Info.BaseRadiusCells * Info.BaseRadiusCells;
			if ((self.Location - plan.Centre).LengthSquared > radius)
				return;

			var d = attacker.Location - plan.Centre;
			var sector = ArmyStagingEval.SectorOf(d.X, d.Y);
			var inside = sector < 0 || Exts.ISqrt((int)Math.Min(int.MaxValue, d.LengthSquared)) <= plan.RingRadius[sector];
			if (sector < 0)
				sector = 0;

			var tick = world.WorldTick;
			var value = Math.Max(1, attacker.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? Math.Max(1, e.Damage?.Value ?? 1));

			if (!events.TryGetValue(attacker.ActorID, out var known))
			{
				known = new AttackEvent { WeightTick = int.MinValue / 2 };
				events[attacker.ActorID] = known;
			}

			known.Tick = tick;
			known.Sector = sector;
			known.Inside = inside;
			known.Value = value;

			if (tick - known.WeightTick >= Math.Max(1, Info.EventDedupeTicks))
			{
				known.WeightTick = tick;
				if (inside)
					insideMilli += value * 1000L;
				else
					learnedMilli[sector] += value * 1000L;
			}
		}

		void Recompute(int tick)
		{
			var centre = default(CPos);
			var count = 0;
			long sumX = 0, sumY = 0;
			var buildings = new List<(CPos Cell, bool Armed)>();
			foreach (var a in world.ActorsHavingTrait<Building>())
			{
				if (a.Owner != player || a.IsDead || !a.IsInWorld)
					continue;

				buildings.Add((a.Location, a.Info.HasTraitInfo<AttackBaseInfo>()));
				sumX += a.Location.X;
				sumY += a.Location.Y;
				count++;
			}

			if (count == 0)
				return;

			centre = new CPos((int)(sumX / count), (int)(sumY / count));

			// Decay what was learned since the last plan, then drop events that can no longer matter.
			var elapsed = Math.Max(0, tick - lastPlanTick);
			lastPlanTick = tick;
			for (var s = 0; s < learnedMilli.Length; s++)
				learnedMilli[s] = ArmyStagingEval.Decay(learnedMilli[s], elapsed, Info.WeightHalfLifeTicks);

			insideMilli = ArmyStagingEval.Decay(insideMilli, elapsed, Info.WeightHalfLifeTicks);
			var keep = Math.Max(Info.LiveAttackTicks, Info.EventDedupeTicks);
			foreach (var id in events.Where(kv => tick - kv.Value.Tick > keep).Select(kv => kv.Key).ToList())
				events.Remove(id);

			// Defence ring per sector, from the own buildings.
			var sectorArmed = new List<int>[ArmyStagingEval.Sectors];
			var sectorAll = new List<int>[ArmyStagingEval.Sectors];
			for (var s = 0; s < ArmyStagingEval.Sectors; s++)
			{
				sectorArmed[s] = [];
				sectorAll[s] = [];
			}

			var baseArmed = new List<int>();
			var baseAll = new List<int>();
			foreach (var (cell, armed) in buildings)
			{
				var d = cell - centre;
				var sector = ArmyStagingEval.SectorOf(d.X, d.Y);
				var r = Exts.ISqrt((int)Math.Min(int.MaxValue, d.LengthSquared));
				baseAll.Add(r);
				if (armed)
					baseArmed.Add(r);

				if (sector < 0)
					continue;

				sectorAll[sector].Add(r);
				if (armed)
					sectorArmed[sector].Add(r);
			}

			var plan = new ArmyStagingPlan { Tick = tick, Centre = centre, InsideValue = (int)Math.Min(int.MaxValue, insideMilli / 1000) };
			for (var s = 0; s < ArmyStagingEval.Sectors; s++)
			{
				plan.RingRadius[s] = ArmyStagingEval.RingRadius(sectorArmed[s], sectorAll[s], baseArmed, baseAll);
				plan.StagingCell[s] = StagingCellOf(centre, s, ArmyStagingEval.StagingRadius(plan.RingRadius[s], Info.StagingInsetCells));
			}

			// Rim weight = learned + prior.
			var prior = ArmyStagingEval.PriorMilli(PriorCounts(centre), Info.PriorWeightValue * 1000L);
			var rim = new long[ArmyStagingEval.Sectors];
			for (var s = 0; s < rim.Length; s++)
			{
				rim[s] = learnedMilli[s] + prior[s];
				plan.RimValue[s] = (int)Math.Min(int.MaxValue, rim[s] / 1000);
				plan.PriorValue[s] = (int)Math.Min(int.MaxValue, prior[s] / 1000);
			}

			// Live: own events within LiveAttackTicks plus the DF-2 prediction as one more input.
			var live = new long[ArmyStagingEval.Sectors];
			long liveInside = 0;
			foreach (var ev in events.Values)
			{
				if (tick - ev.Tick > Info.LiveAttackTicks)
					continue;

				if (ev.Inside)
					liveInside += ev.Value;
				else
					live[ev.Sector] += ev.Value;
			}

			if (Info.UsePrediction)
			{
				predictionProviders ??= player.PlayerActor.TraitsImplementing<IBotThreatPredictionProvider>().ToArray();
				foreach (var p in predictionProviders)
					foreach (var threat in p.PredictedThreats)
					{
						if (threat.EtaTicks > Info.LiveAttackTicks)
							continue;

						var d = threat.Target - centre;
						var sector = ArmyStagingEval.SectorOf(d.X, d.Y);
						if (sector >= 0)
							live[sector] += threat.Value;
					}
			}

			for (var s = 0; s < live.Length; s++)
				plan.LiveValue[s] = (int)Math.Min(int.MaxValue, live[s]);

			plan.LiveInsideValue = (int)Math.Min(int.MaxValue, liveInside);

			// Groups, then the live reaction (held until ReturnAfterTicks without a live attack).
			var allocation = ArmyStagingEval.Allocate(rim, insideMilli, Info.ActiveSectorSharePct, Info.MaxDefenceGroups, Info.ReserveMaxPct, Info.CentreSwitchPct);
			ArmyStagingEval.MergeSmallGroups(allocation.Groups, lastIdleValue, Info.MinGroupValue);
			var targets = ArmyStagingEval.LiveTargets(allocation.Groups.Select(g => g.Sector).ToArray(), live, liveInside);
			if (targets.Live)
			{
				lastLiveTick = tick;
				heldGroupTargets = new Dictionary<int, int>();
				for (var g = 0; g < allocation.Groups.Count; g++)
					heldGroupTargets[allocation.Groups[g].Sector] = targets.GroupTargets[g];

				heldReserveTarget = targets.ReserveTarget;
			}
			else if (!ArmyStagingEval.ShouldReturn(tick - lastLiveTick, Info.ReturnAfterTicks))
			{
				for (var g = 0; g < allocation.Groups.Count; g++)
					if (heldGroupTargets.TryGetValue(allocation.Groups[g].Sector, out var held))
						targets.GroupTargets[g] = held;

				targets.ReserveTarget = heldReserveTarget;
				targets.Live = true;
			}

			plan.CentreMode = allocation.CentreMode;
			plan.ReservePct = allocation.ReservePct;
			plan.Live = targets.Live;
			plan.ReserveTargetSector = allocation.ReservePct > 0 ? targets.ReserveTarget : -1;
			plan.ReserveCell = plan.ReserveTargetSector >= 0 ? plan.StagingCell[plan.ReserveTargetSector] : centre;
			plan.Groups = new ArmyStagingGroup[allocation.Groups.Count];
			for (var g = 0; g < plan.Groups.Length; g++)
			{
				var target = targets.GroupTargets[g];
				plan.Groups[g] = new ArmyStagingGroup
				{
					Sector = allocation.Groups[g].Sector,
					SharePct = allocation.Groups[g].SharePct,
					TargetSector = target,
					Cell = plan.StagingCell[target]
				};
			}

			Plan = plan;
		}

		// The cell `radius` cells from the centre along a sector, pulled back toward the centre until it is on the map.
		CPos StagingCellOf(CPos centre, int sector, int radius)
		{
			for (var r = radius; r > 0; r--)
			{
				var (x, y) = ArmyStagingEval.Offset(sector, r);
				var cell = new CPos(centre.X + x, centre.Y + y);
				if (world.Map.Contains(cell))
					return cell;
			}

			return centre;
		}

		// Direction counts of the prior: every enemy spawn candidate and every seen enemy defence adds one to its sector; with
		// neither known, the map centre stands in so the bot still faces the middle of the map rather than nowhere.
		int[] PriorCounts(CPos centre)
		{
			var counts = new int[ArmyStagingEval.Sectors];
			var total = 0;

			enemySpawns ??= ResolveEnemySpawns();
			foreach (var spawn in enemySpawns)
				total += CountDirection(counts, spawn - centre);

			defenceProviders ??= player.PlayerActor.TraitsImplementing<IBotRememberedDefenceProvider>().ToArray();
			foreach (var provider in defenceProviders)
				foreach (var defence in provider.RememberedDefences())
					total += CountDirection(counts, defence.Cell - centre);

			if (total == 0)
			{
				var bounds = world.Map.Bounds;
				var mapCentre = new CPos(bounds.X + bounds.Width / 2, bounds.Y + bounds.Height / 2);
				CountDirection(counts, mapCentre - centre);
			}

			return counts;
		}

		static int CountDirection(int[] counts, CVec offset)
		{
			var sector = ArmyStagingEval.SectorOf(offset.X, offset.Y);
			if (sector < 0)
				return 0;

			counts[sector]++;
			return 1;
		}

		// Public map data (the same read the scout makes): the mpspawn actors, minus every start within SpawnMatchCells of an own or
		// allied player's home. In a team game that leaves the enemy team's starts, not the geometric rim.
		List<CPos> ResolveEnemySpawns()
		{
			var spawns = world.Map.ActorDefinitions
				.Where(d => d.Value.Value == "mpspawn")
				.Select(d => new ActorReference(d.Value.Value, d.Value).Get<LocationInit>().Value);
			var homes = world.Players.Where(p => p == player || player.IsAlliedWith(p)).Select(p => p.HomeLocation);
			return ArmyStagingEval.EnemySpawnCandidates(spawns, homes, Info.SpawnMatchCells);
		}

		CPos? IBotArmyStaging.PrimaryStagingCell
		{
			get
			{
				var plan = Plan;
				if (plan == null)
					return null;

				if (plan.Groups.Length > 0)
					return plan.Groups[0].Cell;

				return plan.ReservePct > 0 ? plan.ReserveCell : null;
			}
		}

		CPos? IBotArmyStaging.StagingCellNear(CPos from)
		{
			var plan = Plan;
			if (plan == null)
				return null;

			CPos? best = null;
			long bestDistance = long.MaxValue;
			foreach (var cell in AssignedCells(plan))
			{
				var distance = (cell - from).LengthSquared;
				if (distance < bestDistance)
				{
					bestDistance = distance;
					best = cell;
				}
			}

			return best;
		}

		bool IBotArmyStaging.Covers(CPos cell)
		{
			var plan = Plan;
			return plan != null && (cell - plan.Centre).LengthSquared <= (long)Info.BaseRadiusCells * Info.BaseRadiusCells;
		}

		static IEnumerable<CPos> AssignedCells(ArmyStagingPlan plan)
		{
			foreach (var g in plan.Groups)
				yield return g.Cell;

			if (plan.ReservePct > 0)
				yield return plan.ReserveCell;
		}

		void IBotArmyStaging.AssignIdlePool(IReadOnlyList<ArmyStagingUnit> pool, List<ArmyStagingOrder> result)
		{
			lastIdleValue = pool.Sum(u => (long)u.Value);

			var plan = Plan;
			if (plan == null || pool.Count == 0)
				return;

			var cells = AssignedCells(plan).ToArray();
			var shares = plan.Groups.Select(g => g.SharePct).ToList();
			if (plan.ReservePct > 0)
				shares.Add(plan.ReservePct);

			if (cells.Length == 0)
				return;

			var ordered = pool.OrderBy(u => u.Actor.ActorID).ToArray();
			var parts = ArmyStagingEval.AssignByValue(ordered.Select(u => (long)u.Value).ToArray(), shares);
			for (var i = 0; i < ordered.Length; i++)
				result.Add(new ArmyStagingOrder(ordered[i].Actor, cells[Math.Min(parts[i], cells.Length - 1)]));
		}
	}
}
