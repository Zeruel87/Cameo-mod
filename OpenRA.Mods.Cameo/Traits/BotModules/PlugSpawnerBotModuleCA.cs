#region Copyright & License Information
/*
 * Copyright 2015- OpenRA.Mods.AS Developers (see AUTHORS)
 * This file is a part of a third-party plugin for OpenRA, which is
 * free software. It is made available to you under the terms of the
 * GNU General Public License as published by the Free Software
 * Foundation. For more information, see COPYING.
 */
#endregion

using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Allows the AI to have a single plug type.", "Plugs are all spawned.", "Use multiple variants of this trait to support more kind.")]
	public class PlugSpawnerBotModuleCAInfo : ConditionalTraitInfo
	{
		[ActorReference(typeof(PlugInfo))]
		[FieldLoader.Require]
		[Desc("What plug the AI can spawn.")]
		public readonly string Plug = null;

		[ActorReference(typeof(PluggableInfo))]
		[FieldLoader.Require]
		[Desc("What actors the AI can spawn this plug on.")]
		public readonly HashSet<string> Pluggables = new() { };

		[Desc("Plug spawning interval.")]
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

		string plugType;
		int ticks;

		public PlugSpawnerBotModuleCA(Actor self, PlugSpawnerBotModuleCAInfo info)
			: base(info)
		{
			world = self.World;
			ticks = Info.Interval;
		}

		protected override void Created(Actor self)
		{
			plugType = world.Map.Rules.Actors[Info.Plug].TraitInfo<PlugInfo>().Type;
			playerResources = self.Owner.PlayerActor.Trait<PlayerResources>();
			techTree = self.Owner.PlayerActor.Trait<TechTree>();

			base.Created(self);
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (--ticks > 0)
				return;

			var player = bot.Player;

			var targetActors = world.Actors.Where(x => x.IsInWorld && !x.IsDead && x.Owner == player && Info.Pluggables.Contains(x.Info.Name));

			if (!targetActors.Any())
				return;

			var target = targetActors
				.Select(x => (x, x.TraitsImplementing<Pluggable>().FirstOrDefault(p => p.AcceptsPlug(plugType))))
				.FirstOrDefault(x => x.Item2 != null);

			if (target.x != null)
			{
				var order = new Order("PlacePlugAI", player.PlayerActor, Target.FromActor(target.x), false)
				{
					TargetString = Info.Plug,
					ExtraData = player.PlayerActor.ActorID,
					SuppressVisualFeedback = true
				};

				world.IssueOrder(order);
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
			if (ts != Info.Plug)
				return;

			self.World.AddFrameEndTask(w =>
			{
				var playerActor = w.GetActorById(order.ExtraData);
				var targetActor = order.Target.Actor;

				if (playerActor == null || playerActor.IsDead || targetActor == null || targetActor.IsDead)
					return;

				var actorInfo = self.World.Map.Rules.Actors[order.TargetString];

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
