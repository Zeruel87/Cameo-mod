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
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
	public sealed class FransMineCluster
	{
		public Actor Representative { get; }
		public IReadOnlyList<Actor> Mines { get; }
		public CPos Center => Representative.Location;
		public int MineCount => Mines.Count;

		public FransMineCluster(Actor representative, IReadOnlyList<Actor> mines)
		{
			Representative = representative;
			Mines = mines;
		}
	}

	public interface IFransMineClusterService
	{
		IReadOnlyList<FransMineCluster> VisibleClusters { get; }
	}

	[TraitLocation(SystemActors.Player)]
	[Desc("Groups nearby visible mine/gmine actors into stable Frans resource clusters.")]
	public class FransMineClusterBotModuleInfo : ConditionalTraitInfo
	{
		[ActorReference]
		[Desc("Renewable resource creator actors that form mine clusters.")]
		public readonly FrozenSet<string> ResourceCreatorTypes = FrozenSet<string>.Empty;

		[Desc("Two resource creators at or inside this distance in cells are connected to the same cluster. Connectivity is transitive.")]
		public readonly int ClusterLinkRadius = 10;

		[Desc("World ticks between cluster rebuilds.")]
		public readonly int ScanInterval = 25;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);

			// Cameo port: actor lists ship empty until per-faction ContentPack
			// wiring fills them; an empty set simply leaves clustering inactive.

			if (ClusterLinkRadius <= 0)
				throw new YamlException($"{nameof(ClusterLinkRadius)} must be greater than zero.");

			if (ScanInterval <= 0)
				throw new YamlException($"{nameof(ScanInterval)} must be greater than zero.");
		}

		public override object Create(ActorInitializer init) { return new FransMineClusterBotModule(init.Self, this); }
	}

	public class FransMineClusterBotModule : ConditionalTrait<FransMineClusterBotModuleInfo>,
		IBotTick, IFransMineClusterService
	{
		readonly World world;
		readonly Player player;

		FransMineCluster[] visibleClusters = [];
		IFransCombatIntelService combatIntelService;
		Actor[] lastVisibleMines = [];
		int scanTicks;

		public FransMineClusterBotModule(Actor self, FransMineClusterBotModuleInfo info)
			: base(info)
		{
			world = self.World;
			player = self.Owner;
		}

		public IReadOnlyList<FransMineCluster> VisibleClusters => visibleClusters;

		protected override void Created(Actor self)
		{
			combatIntelService = self.Owner.PlayerActor.TraitsImplementing<IFransCombatIntelService>().FirstOrDefault()
				?? throw new InvalidOperationException("FransMineClusterBotModule requires FransCombatIntelBotModule.");
		}

		protected override void TraitEnabled(Actor self)
		{
			// keep the 25-WT cadence but spread this scan away from the combat-command burst.
			// CombatIntel still supplies the fair visible mine snapshot; no strategy changes here.
			scanTicks = (int)((self.ActorID + 17u) % (uint)Info.ScanInterval) + 1;
		}

		protected override void TraitDisabled(Actor self)
		{
			visibleClusters = [];
			lastVisibleMines = [];
		}

		void IBotTick.BotTick(IBot bot)
		{
			using var fransPerfScope = FransBotLog.Profile(world, player, "FransMineCluster.BotTick");
			if (player.WinState != WinState.Undefined)
				return;

			if (--scanTicks > 0)
				return;

			scanTicks = Info.ScanInterval;
			RebuildClusters();
		}

		void RebuildClusters()
		{
			var mines = combatIntelService.VisibleActors
				.Where(a => a != null &&
					a.OccupiesSpace != null &&
					a.IsInWorld &&
					!a.IsDead &&
					Info.ResourceCreatorTypes.Contains(a.Info.Name) &&
					a.CanBeViewedByPlayer(player))
				.OrderBy(a => a.ActorID)
				.ToArray();

			// Mines do not move. Re-clustering the same visible actor set every 25 ticks
			// only creates garbage and repeats O(n²) work. Rebuild only when visibility
			// reveals/removes a mine actor.
			var sameMineSet = mines.Length == lastVisibleMines.Length;
			for (var i = 0; sameMineSet && i < mines.Length; i++)
				sameMineSet = mines[i] == lastVisibleMines[i];

			if (sameMineSet)
				return;

			lastVisibleMines = mines;
			if (mines.Length == 0)
			{
				visibleClusters = [];
				return;
			}

			var visited = new HashSet<Actor>();
			var clusters = new List<FransMineCluster>();
			var linkRadiusSquared = Info.ClusterLinkRadius * Info.ClusterLinkRadius;

			foreach (var seed in mines)
			{
				if (!visited.Add(seed))
					continue;

				var members = new List<Actor>();
				var pending = new Queue<Actor>();
				pending.Enqueue(seed);

				while (pending.Count > 0)
				{
					var current = pending.Dequeue();
					members.Add(current);

					// `mines` is already ActorID-sorted. Iterate it directly instead of
					// allocating/sorting a temporary neighbor array for every BFS node.
					foreach (var other in mines)
					{
						if (visited.Contains(other) ||
							(other.Location - current.Location).LengthSquared > linkRadiusSquared)
							continue;

						visited.Add(other);
						pending.Enqueue(other);
					}
				}

				var memberArray = members.OrderBy(a => a.ActorID).ToArray();
				var representative = memberArray
					.OrderBy(candidate => memberArray.Sum(other =>
						(long)(candidate.Location - other.Location).LengthSquared))
					.ThenBy(a => a.ActorID)
					.First();

				clusters.Add(new FransMineCluster(representative, memberArray));
			}

			visibleClusters = clusters
				.OrderBy(c => c.Representative.ActorID)
				.ToArray();
		}
	}
}
