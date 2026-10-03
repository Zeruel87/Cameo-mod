#region Copyright & License Information
/*
 * Copyright 2015- OpenRA.Mods.AS Developers (see AUTHORS)
 * This file is a part of a third-party plugin for OpenRA, which is
 * free software. It is made available to you under the terms of the
 * GNU General Public License as published by the Free Software
 * Foundation. For more information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Allows the AI to spawn plugs on pluggable buildings.",
		"Each entry maps one plug actor to the host actor names it may be spawned on.",
		"One module covers every plug kind — the upstream AS module needed one variant per plug.")]
	public class PlugSpawnerBotModuleCAInfo : ConditionalTraitInfo
	{
		[Desc("Plug actor name -> comma-separated host actor names the AI may spawn it on.")]
		public readonly Dictionary<string, string> Plugs = new();

		[Desc("Plug spawning interval per plug type.")]
		public readonly int Interval = 50;

		[Desc("Should costs of the plug be ignored?")]
		public readonly bool IgnoreCost = false;

		public override object Create(ActorInitializer init) { return new PlugSpawnerBotModuleCA(init.Self, this); }
	}

	public class PlugSpawnerBotModuleCA : ConditionalTrait<PlugSpawnerBotModuleCAInfo>, IBotTick, IResolveOrder, INotifyCreated
	{
		readonly World world;
		PlayerResources playerResources;
		TechTree techTree;

		// plugActor -> (plug type, host name set, prerequisites)
		readonly Dictionary<string, (string Type, HashSet<string> Hosts, string[] Prerequisites)> plugs = new();
		int ticks;

		public PlugSpawnerBotModuleCA(Actor self, PlugSpawnerBotModuleCAInfo info)
			: base(info)
		{
			world = self.World;
			ticks = Info.Interval;
		}

		protected override void Created(Actor self)
		{
			playerResources = self.Owner.PlayerActor.Trait<PlayerResources>();
			techTree = self.Owner.PlayerActor.TraitOrDefault<TechTree>();

			foreach (var kv in Info.Plugs)
			{
				if (!world.Map.Rules.Actors.TryGetValue(kv.Key, out var actorInfo))
					continue;

				var plugInfo = actorInfo.TraitInfoOrDefault<PlugInfo>();
				if (plugInfo == null)
					continue;

				var hosts = kv.Value.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
					.ToHashSet();
				var prereqs = actorInfo.TraitInfos<BuildableInfo>()
					.SelectMany(b => b.Prerequisites)
					.Distinct()
					.ToArray();

				plugs[kv.Key] = (plugInfo.Type, hosts, prereqs);
			}

			base.Created(self);
		}

		bool PrerequisitesMet(string[] prereqs)
		{
			return prereqs.Length == 0 || techTree == null || techTree.HasPrerequisites(prereqs);
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (--ticks > 0)
				return;

			var player = bot.Player;

			foreach (var (plugActor, plug) in plugs)
			{
				// Never queue a plug the tech tree still gates off — plugs that bypass
				// Buildable prerequisites would skip the faction's tech path entirely.
				if (!PrerequisitesMet(plug.Prerequisites))
					continue;

				var targetActors = world.Actors.Where(x => x.IsInWorld && !x.IsDead && x.Owner == player && plug.Hosts.Contains(x.Info.Name));
				if (!targetActors.Any())
					continue;

				var target = targetActors
					.Select(x => (x, x.TraitsImplementing<Pluggable>().FirstOrDefault(p => p.AcceptsPlug(plug.Type))))
					.FirstOrDefault(x => x.Item2 != null);

				if (target.x != null)
				{
					var order = new Order("PlacePlugAI", player.PlayerActor, Target.FromActor(target.x), false)
					{
						TargetString = plugActor,
						ExtraData = player.PlayerActor.ActorID,
						SuppressVisualFeedback = true
					};

					bot.QueueOrder(order);
				}
			}

			ticks = Info.Interval;
		}

		void IResolveOrder.ResolveOrder(Actor self, Order order)
		{
			if (IsTraitDisabled)
				return;

			var os = order.OrderString;
			if (os != "PlacePlugAI")
				return;

			var ts = order.TargetString;
			if (!plugs.TryGetValue(ts, out var plug))
				return;

			self.World.AddFrameEndTask(w =>
			{
				var playerActor = w.GetActorById(order.ExtraData);
				var targetActor = order.Target.Actor;

				if (playerActor == null || playerActor.IsDead || targetActor == null || targetActor.IsDead)
					return;

				var actorInfo = self.World.Map.Rules.Actors[ts];

				var faction = self.Owner.Faction.InternalName;
				var buildingInfo = actorInfo.TraitInfo<BuildingInfo>();

				var buildableInfo = actorInfo.TraitInfos<BuildableInfo>().FirstOrDefault();
				if (buildableInfo != null && buildableInfo.ForceFaction != null)
					faction = buildableInfo.ForceFaction;

				var plugInfo = actorInfo.TraitInfoOrDefault<PlugInfo>();
				if (plugInfo == null)
					return;

				var location = targetActor.Location;
				var pluggable = targetActor.TraitsImplementing<Pluggable>()
					.FirstOrDefault(p => p.AcceptsPlug(plugInfo.Type));

				if (pluggable == null)
					return;

				// Re-check at resolve time: the tech state or slot may have changed
				// while the order sat in the queue.
				if (!PrerequisitesMet(plug.Prerequisites))
					return;

				var valued = actorInfo.TraitInfoOrDefault<ValuedInfo>();
				if (!Info.IgnoreCost && valued != null)
				{
					if (valued.Cost > playerResources.GetCashAndResources())
						return;
					else
						playerResources.TakeCash(valued.Cost);
				}

				pluggable.EnablePlug(targetActor, plugInfo.Type);
				foreach (var s in buildingInfo.BuildSounds)
					Game.Sound.PlayToPlayer(SoundType.World, order.Player, s, targetActor.CenterPosition);
			});
		}

		protected override void TraitEnabled(Actor self)
		{
			ticks = Info.Interval;
		}
	}
}
