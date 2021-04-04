#region Copyright & License Information
/*
 * Copyright 2007-2020 The OpenRA Developers (see AUTHORS)
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
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
[Desc("Adds new Actors into Cargo space of this Actor")]
public class AddCargoInfo : ConditionalTraitInfo, Requires<IOccupySpaceInfo>
	{
		[Desc("A list of actor types that are spawned into this actor.")]
		public readonly string[] Actors = { };
		
	    [Desc("Should newly created actors replace current cargo?")]
		public readonly bool Replace = false;
		
		public object Create(ActorInitializer init) { return new AddCargo(init, this); }		
	}

class AddCargo : ConditionalTrait<AddCargoInfo>, INotifyCreated, IPips
{		
	    public readonly AddCargoInfo Info;
		readonly Actor self;
		readonly List<Actor> addCargo = new List<Actor>();		
		ConditionManager conditionManager;
		
		public AddCargo(ActorInitializer init, AddCargoInfo info)
		{
			Self = init.Self;
			Info = info;
			foreach (var u in info.AddCargo)
				{
					var unit = self.World.CreateActor(false, u.ToLowerInvariant(),
						new TypeDictionary { new OwnerInit(self.Owner) });

					AddCargo.Add(unit);
				}
		}		
		void INotifyCreated.Created(Actor self)
		{
			aircraft = self.TraitOrDefault<Aircraft>();
			conditionManager = self.TraitOrDefault<ConditionManager>();

			if (conditionManager != null && cargo.Any())
			{
				foreach (var c in cargo)
				{
					string passengerCondition;
					if (Info.PassengerConditions.TryGetValue(c.Info.Name, out passengerCondition))
						passengerTokens.GetOrAdd(c.Info.Name).Push(conditionManager.GrantCondition(self, passengerCondition));
				}

				if (!string.IsNullOrEmpty(Info.LoadedCondition))
					loadedTokens.Push(conditionManager.GrantCondition(self, Info.LoadedCondition));
			}		
	}
	}
}