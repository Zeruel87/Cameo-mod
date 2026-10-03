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
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	// CN3 (AI_MASTER_PLAN §3, crystallized-nexus 30cf70a): port of CN DeployBotModule. Unified deploy/undeploy
	// driving for units carrying GrantConditionOnDeploy - artillery sets up in range and packs away when the
	// enemy closes inside its dead zone, stat-deployers entrench when idle and threatened, support deploys near
	// enough allies, ability deploys fire once and pack back up.
	//
	// Cameo changes vs the donor:
	//  - §19.6: units another module holds (a Squad claim, an engineer job) are left alone entirely - a deploy
	//    order from this module would be refused by the order gate anyway, and claiming is wrong here because
	//    the unit's job belongs to its squad; deploy is a state toggle on top of it. Deploy decisions on
	//    squad-held artillery are the open contract question - tracked for the INC-n spec, not hacked around.
	//  - The donor's Support-mode threat scan had no visibility gate; enemy reads here all go through
	//    shroud.IsVisible (own units and allies need none).
	//  - Candidates iterate in ActorID order; CNBotPerf instrumentation dropped.
	//  - Namespace and config shape follow this assembly, not the donor's.
	public enum DeployBotMode
	{
		// Must deploy to attack. Moves into range, deploys, undeploys when enemy too close.
		Artillery,

		// Deploys for better stats when idle and enemy in range. Undeploys to flee.
		Stats,

		// Deploys near friendly forces. Undeploys when alone or threatened.
		Support,

		// Deploys to fire a one-shot ability. Undeploys after ability duration.
		Ability
	}

	public class DeployBotGroup
	{
		[Desc("Actor type names this group applies to.")]
		public readonly HashSet<string> ActorTypes = [];

		[Desc("Deploy behavior mode.")]
		public readonly DeployBotMode Mode = DeployBotMode.Artillery;

		[Desc("Cell radius to scan for enemies.")]
		public readonly int ScanRadius = 20;

		[Desc("Artillery/Stats/Ability: deploy when enemy within this range.")]
		public readonly int DeployRange = 15;

		[Desc("Artillery/Stats/Ability: undeploy when enemy within this range.")]
		public readonly int SafeRange = 5;

		[Desc("Support: cell radius to count friendly units.")]
		public readonly int AllyScanRadius = 8;

		[Desc("Support: minimum allies nearby before deploying.")]
		public readonly int MinAlliesNearby = 3;

		[Desc("Support: undeploy if an enemy gets within this range.")]
		public readonly int ThreatRange = 6;

		[Desc("Ability: how many ticks after deploying before undeploying.")]
		public readonly int AbilityDuration = 100;

		[Desc("Ticks to wait after deploying or undeploying before doing it again. Prevents oscillation.")]
		public readonly int DeployCooldown = 150;
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Unified bot module for all deployable unit types. Configure groups with different deploy modes per actor type.")]
	public class DeployBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("How often (in ticks) the bot re-evaluates all groups.")]
		public readonly int ScanInterval = 25;

		[FieldLoader.LoadUsing(nameof(LoadGroups))]
		[Desc("Deploy behavior groups, keyed by an arbitrary group name.")]
		public readonly Dictionary<string, DeployBotGroup> Groups = [];

		static object LoadGroups(MiniYaml yaml)
		{
			var groups = new Dictionary<string, DeployBotGroup>();
			var groupsNode = yaml.NodeWithKeyOrDefault("Groups");
			if (groupsNode == null)
				return groups;

			foreach (var node in groupsNode.Value.Nodes)
			{
				var group = new DeployBotGroup();
				FieldLoader.Load(group, node.Value);
				groups[node.Key] = group;
			}

			return groups;
		}

		public override object Create(ActorInitializer init) { return new DeployBotModule(init.Self, this); }
	}

	public class DeployBotModule : ConditionalTrait<DeployBotModuleInfo>, IBotTick
	{
		const string LeaseOwner = nameof(DeployBotModule);

		readonly World world;
		readonly OpenRA.Player player;
		int scanTicks;

		// Tracks when Ability-mode units deployed, for undeploy timing
		readonly Dictionary<Actor, int> abilityDeployedAt = [];

		// Cooldown after deploy/undeploy to prevent oscillation
		readonly Dictionary<Actor, int> deployCooldown = [];

		public DeployBotModule(Actor self, DeployBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
			scanTicks = world.LocalRandom.Next(ScanInterval);
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (--scanTicks > 0)
				return;

			scanTicks = ScanInterval;

			// Clean up dead actors from ability tracking
			foreach (var dead in abilityDeployedAt.Keys
				.Where(a => a.IsDead || !a.IsInWorld).ToList())
				abilityDeployedAt.Remove(dead);
			foreach (var dead in deployCooldown.Keys
				.Where(a => a.IsDead || !a.IsInWorld).ToList())
				deployCooldown.Remove(dead);

			var leases = BotUnitLeases.Of(player);

			// Single scan per tick - shared across all groups. Leased units are skipped wholesale: a squad
			// member's squad owns its orders for this tick (§19.6), and unclaimable double-ordering is the
			// exact class the gate exists to stop.
			var playerDeployables = world.ActorsHavingTrait<GrantConditionOnDeploy>()
				.Where(a => !a.IsDead && a.IsInWorld && a.Owner == player
					&& !BotUnitLeases.IsClaimedByOther(leases, a, LeaseOwner))
				.OrderBy(a => a.ActorID)
				.ToList();

			foreach (var group in Info.Groups.Values)
			{
				var units = group.ActorTypes.Count == 0
					? playerDeployables
					: playerDeployables.Where(a => group.ActorTypes.Contains(a.Info.Name));

				foreach (var unit in units)
				{
					switch (group.Mode)
					{
						case DeployBotMode.Artillery:
							TickArtillery(bot, unit, group);
							break;
						case DeployBotMode.Stats:
							TickStats(bot, unit, group);
							break;
						case DeployBotMode.Support:
							TickSupport(bot, unit, group);
							break;
						case DeployBotMode.Ability:
							TickAbility(bot, unit, group);
							break;
					}
				}
			}
		}

		int ScanInterval => Info.ScanInterval > 0 ? Info.ScanInterval : 1;

		// Artillery: Move into range -> deploy -> undeploy if enemy within SafeRange
		void TickArtillery(IBot bot, Actor unit, DeployBotGroup group)
		{
			var isDeployed = GetDeployState(unit) == DeployState.Deployed;
			var nearestEnemy = FindNearestEnemy(unit, group.ScanRadius);
			if (nearestEnemy == null)
			{
				if (isDeployed)
					TryUndeploy(bot, unit, group);
				return;
			}

			var distSq = DistSq(unit, nearestEnemy);
			if (isDeployed)
			{
				if (distSq <= RangeSq(group.SafeRange))
				{
					TryUndeploy(bot, unit, group);
					BackAwayFrom(bot, unit, nearestEnemy, group);
				}
			}
			else
			{
				// Packing up alone left the piece standing exactly where it was, with the enemy still
				// inside SafeRange. The next scan saw an undeployed gun with a target in DeployRange and
				// set it up again, the one after that packed it up again, and so on at the cooldown's
				// pace. Retreating is what actually resolves it: SafeRange is the weapon's minimum range,
				// so a battery that stays put cannot shoot the thing standing on top of it either.
				if (distSq <= RangeSq(group.SafeRange))
					BackAwayFrom(bot, unit, nearestEnemy, group);
				else if (distSq <= RangeSq(group.DeployRange))
					TryDeploy(bot, unit, group);
				else if (distSq <= RangeSq(group.ScanRadius))
					MoveIntoRange(bot, unit, nearestEnemy, group.DeployRange);
			}
		}

		// Stats: Deploy when idle + enemy in range -> undeploy to flee if too close
		void TickStats(IBot bot, Actor unit, DeployBotGroup group)
		{
			var deployState = GetDeployState(unit);

			// Don't interrupt ongoing deploy/undeploy animation
			if (deployState == DeployState.Deploying || deployState == DeployState.Undeploying)
				return;

			var isDeployed = deployState == DeployState.Deployed;
			var nearestEnemy = FindNearestEnemy(unit, group.DeployRange);
			if (nearestEnemy == null)
			{
				if (isDeployed)
					TryUndeploy(bot, unit, group);
				return;
			}

			var distSq = DistSq(unit, nearestEnemy);
			if (isDeployed)
			{
				if (distSq <= RangeSq(group.SafeRange))
					TryUndeploy(bot, unit, group);
			}
			else
			{
				if (distSq <= RangeSq(group.DeployRange))
					TryDeploy(bot, unit, group);
			}
		}

		// Support: Deploy near enough allies -> undeploy when alone or threatened
		void TickSupport(IBot bot, Actor unit, DeployBotGroup group)
		{
			var deployState = GetDeployState(unit);
			if (deployState == DeployState.Deploying || deployState == DeployState.Undeploying)
				return;

			var isDeployed = deployState == DeployState.Deployed;

			// Same hostility filter FindNearestEnemy uses. Without the NonCombatant/world-owner checks
			// any neutral or civilian building counted as a threat, so a support unit standing next to
			// a civvie hut was permanently "threatened" and never deployed at all. The donor's scan had
			// no visibility gate; here enemies must also be visible (shroud.IsVisible), matching §19.5.
			var shroud = player.Shroud;
			var threatened = world.FindActorsInCircle(unit.CenterPosition, WDist.FromCells(group.ThreatRange))
				.Any(a =>
					!a.IsDead && a.IsInWorld && a != unit
					&& !player.IsAlliedWith(a.Owner)
					&& !a.Owner.NonCombatant
					&& a.Owner != world.WorldActor.Owner
					&& a.Info.HasTraitInfo<ITargetableInfo>()
					&& shroud.IsVisible(a.Location));

			var nearbyAllies = world.FindActorsInCircle(unit.CenterPosition, WDist.FromCells(group.AllyScanRadius))
				.Count(a =>
					!a.IsDead && a.IsInWorld && a != unit
					&& player.IsAlliedWith(a.Owner)
					&& a.Info.HasTraitInfo<IMoveInfo>());

			if (isDeployed)
			{
				if (nearbyAllies < group.MinAlliesNearby || threatened)
					TryUndeploy(bot, unit, group);
			}
			else
			{
				if (nearbyAllies >= group.MinAlliesNearby && !threatened && unit.IsIdle)
					TryDeploy(bot, unit, group);
			}
		}

		// Ability: Move into range -> deploy -> undeploy after AbilityDuration ticks
		void TickAbility(IBot bot, Actor unit, DeployBotGroup group)
		{
			var deployState = GetDeployState(unit);
			if (deployState == DeployState.Deploying || deployState == DeployState.Undeploying)
				return;

			var isDeployed = deployState == DeployState.Deployed;
			if (isDeployed)
			{
				if (abilityDeployedAt.TryGetValue(unit, out var deployTick)
					&& world.WorldTick - deployTick >= group.AbilityDuration)
				{
					TryUndeploy(bot, unit, group);
					abilityDeployedAt.Remove(unit);
				}

				return;
			}

			var target = FindNearestEnemy(unit, group.ScanRadius);
			if (target == null)
				return;

			var distSq = DistSq(unit, target);
			if (distSq <= RangeSq(group.DeployRange))
			{
				TryDeploy(bot, unit, group);
				abilityDeployedAt[unit] = world.WorldTick;
			}
			else if (distSq <= RangeSq(group.ScanRadius))
			{
				MoveIntoRange(bot, unit, target, group.DeployRange);
			}
		}

		// --- Deploy/Undeploy via IIssueDeployOrder ---
		void TryDeploy(IBot bot, Actor unit, DeployBotGroup group)
		{
			if (deployCooldown.TryGetValue(unit, out var lastAction)
				&& world.WorldTick - lastAction < group.DeployCooldown)
				return;

			var deploy = unit.TraitsImplementing<GrantConditionOnDeploy>()
				.FirstOrDefault(d => !d.IsTraitDisabled && !d.IsTraitPaused);
			if (deploy == null)
				return;

			if (!deploy.IsValidTerrain(unit.Location))
			{
				var validCell = FindNearestValidDeployCell(unit, deploy);
				if (validCell.HasValue)
					bot.QueueOrder(new Order("Move", unit, Target.FromCell(world, validCell.Value), false));
				return;
			}

			var deployTraits = unit.TraitsImplementing<IIssueDeployOrder>()
				.Where(d => d.CanIssueDeployOrder(unit, false));
			foreach (var d in deployTraits)
				bot.QueueOrder(d.IssueDeployOrder(unit, false));

			deployCooldown[unit] = world.WorldTick;
		}

		void TryUndeploy(IBot bot, Actor unit, DeployBotGroup group)
		{
			if (deployCooldown.TryGetValue(unit, out var lastAction)
				&& world.WorldTick - lastAction < group.DeployCooldown)
				return;

			var deployTraits = unit.TraitsImplementing<IIssueDeployOrder>()
				.Where(d => d.CanIssueDeployOrder(unit, false));
			foreach (var d in deployTraits)
				bot.QueueOrder(d.IssueDeployOrder(unit, false));

			deployCooldown[unit] = world.WorldTick;
		}

		CPos? FindNearestValidDeployCell(Actor unit, GrantConditionOnDeploy deploy)
		{
			var mobile = unit.TraitOrDefault<Mobile>();
			if (mobile == null)
				return null;

			// Search in expanding rings around the unit
			for (var radius = 1; radius <= 6; radius++)
			{
				var best = world.Map.FindTilesInAnnulus(unit.Location, radius, radius)
					.Where(c =>
						world.Map.Contains(c)
						&& deploy.IsValidTerrain(c)
						&& mobile.CanEnterCell(c))
					.MinByOrDefault(c => (c - unit.Location).LengthSquared);
				if (best != default)
					return best;
			}

			return null;
		}

		// --- Helpers ---
		static DeployState GetDeployState(Actor unit)
		{
			var deploy = unit.TraitsImplementing<GrantConditionOnDeploy>()
				.FirstOrDefault(d => !d.IsTraitDisabled);
			return deploy?.DeployState ?? DeployState.Undeployed;
		}

		/// <summary>
		/// Opens the distance to something that has come inside SafeRange. Aims for the middle of the
		/// band the piece can actually shoot from - past the minimum range that SafeRange stands for,
		/// and still well short of the maximum - so it neither creeps back into trouble nor gives up
		/// the target entirely.
		/// </summary>
		void BackAwayFrom(IBot bot, Actor unit, Actor threat, DeployBotGroup group)
		{
			var wanted = (group.SafeRange + group.DeployRange) / 2;
			if (wanted <= group.SafeRange)
				wanted = group.SafeRange + 1;

			var away = unit.Location - threat.Location;
			var dist = away.Length;
			if (dist >= wanted)
				return;

			// Directly on top of it: any direction will do, and standing still is the one thing that
			// cannot work.
			var cell = dist == 0
				? unit.Location + new CVec(wanted, 0)
				: new CPos(
					threat.Location.X + away.X * wanted / dist,
					threat.Location.Y + away.Y * wanted / dist);
			if (cell == unit.Location)
				return;

			var mobile = unit.TraitOrDefault<Mobile>();
			if (mobile != null && (!world.Map.Contains(cell) || !mobile.CanEnterCell(cell)))
			{
				var validCell = FindNearestValidMoveCell(mobile, cell);
				if (!validCell.HasValue || validCell.Value == unit.Location)
					return;
				cell = validCell.Value;
			}

			bot.QueueOrder(new Order("Move", unit, Target.FromCell(world, cell), false));
		}

		void MoveIntoRange(IBot bot, Actor unit, Actor target, int range)
		{
			var toTarget = target.Location - unit.Location;
			var dist = toTarget.Length;
			if (dist == 0)
				return;

			var ratio = (float)(dist - range + 2) / dist;
			if (ratio < 0) ratio = 0;
			if (ratio > 1) ratio = 1;
			var cell = new CPos(
				unit.Location.X + (int)(toTarget.X * ratio),
				unit.Location.Y + (int)(toTarget.Y * ratio));
			if (cell == unit.Location)
				return;

			var mobile = unit.TraitOrDefault<Mobile>();
			if (mobile != null && (!world.Map.Contains(cell) || !mobile.CanEnterCell(cell)))
			{
				var validCell = FindNearestValidMoveCell(mobile, cell);
				if (!validCell.HasValue || validCell.Value == unit.Location)
					return;
				cell = validCell.Value;
			}

			bot.QueueOrder(new Order("Move", unit, Target.FromCell(world, cell), false));
		}

		CPos? FindNearestValidMoveCell(Mobile mobile, CPos around)
		{
			for (var radius = 1; radius <= 4; radius++)
			{
				var best = world.Map.FindTilesInAnnulus(around, radius, radius)
					.Where(c => world.Map.Contains(c) && mobile.CanEnterCell(c))
					.MinByOrDefault(c => (c - around).LengthSquared);
				if (best != default)
					return best;
			}

			return null;
		}

		Actor FindNearestEnemy(Actor unit, int radius)
		{
			var shroud = player.Shroud;
			return world.FindActorsInCircle(unit.CenterPosition, WDist.FromCells(radius))
				.Where(a =>
					!a.IsDead && a.IsInWorld && a != unit
					&& !player.IsAlliedWith(a.Owner)
					&& !a.Owner.NonCombatant
					&& a.Owner != world.WorldActor.Owner
					&& a.Info.HasTraitInfo<ITargetableInfo>()
					&& !a.Info.HasTraitInfo<LineBuildInfo>()
					&& shroud.IsVisible(a.Location))
				.MinByOrDefault(a => (a.CenterPosition - unit.CenterPosition).HorizontalLengthSquared);
		}

		// Horizontal world-space distance, matching the metric FindActorsInCircle scans with.
		// This used to be (a.Location - b.Location).LengthSquared, i.e. CELL space, while the enemy
		// scan itself ran on a WDist.FromCells world circle. On the RectangularIsometric grid the two
		// metrics differ per axis, so DeployRange and SafeRange effectively changed with the bearing
		// to the target. Z is dropped so an aircraft's cruise altitude doesn't inflate the distance.
		static long DistSq(Actor a, Actor b)
		{
			return (a.CenterPosition - b.CenterPosition).HorizontalLengthSquared;
		}

		static long RangeSq(int cells)
		{
			var range = WDist.FromCells(Math.Max(0, cells)).Length;
			return (long)range * range;
		}
	}
}
