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

using System.Collections.Generic;
using System.Linq;
using OpenRA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;

namespace OpenRA.Mods.Cameo.Traits
{
	public class ProvidesTeamProxyActorInfo : ConditionalTraitInfo
	{
		[Desc("The prerequisite type that this provides. If left empty it defaults to the actor's name.")]
		public readonly string Actor = null;

		[Desc("Should it recheck everything when it is captured?")]
		public readonly bool ProvidePermanently = false;

		public override object Create(ActorInitializer init) { return new ProvidesTeamProxyActor(init, this); }
	}

	public class ProvidesTeamProxyActor : ConditionalTrait<ProvidesTeamProxyActorInfo>, INotifyOwnerChanged, INotifyCreated, INotifyAddedToWorld, INotifyActorDisposing
	{
		IEnumerable<OpenRA.Player> team;

		bool enabled;
		public List<Actor> proxies;

		public ProvidesTeamProxyActor(ActorInitializer init, ProvidesTeamProxyActorInfo info)
			: base(info) { }

		protected override void Created(Actor self)
		{
			team = new List<OpenRA.Player>();
			proxies = new List<Actor>();

			base.Created(self);
		}

		public void AddedToWorld(Actor self)
		{
			team = self.World.Players.Where(p => !p.NonCombatant && p.InternalName != "Everyone" && p.IsAlliedWith(self.Owner));

			Update(self);
		}

		public void OnOwnerChanged(Actor self, OpenRA.Player oldOwner, OpenRA.Player newOwner)
		{
			team = self.World.Players.Where(p => !p.NonCombatant && p.InternalName != "Everyone" && p.IsAlliedWith(newOwner));
			ClearActors();
			Update(self);
		}

		void Update(Actor self)
		{
			enabled = !IsTraitDisabled;
			if (IsTraitDisabled)
				ClearActors();
			else CreateActors(self);
		}

		void CreateActors(Actor self)
		{
			foreach (var player in team)
			{
				var proxy = self.World.CreateActor(Info.Actor, new TypeDictionary
				{
					new OwnerInit(player)
				});

				if (!Info.ProvidePermanently)
					proxies.Add(proxy);
			}
		}

		void ClearActors()
		{
			foreach (var proxy in proxies)
				proxy.Dispose();
		}

		public void Disposing(Actor self)
		{
			ClearActors();
		}

		protected override void TraitEnabled(Actor self)
		{
			Update(self);
		}

		protected override void TraitDisabled(Actor self)
		{
			Update(self);
		}
	}
}
