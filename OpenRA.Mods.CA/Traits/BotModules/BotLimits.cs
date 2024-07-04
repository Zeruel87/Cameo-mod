#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	public class BotLimitsInfo : ConditionalTraitInfo
	{
		public readonly int ProductionTypeLimit = 1;
		public readonly int RefineryLimit = 4;
		public readonly int ConstructionYardLimit = 1;

		public readonly int BuildingDelayModifier = 100;
		public readonly int BuildingIntervalModifier = 100;

		public readonly int HarvesterLimit = 8;

		public readonly int UnitDelayModifier = 100;
		public readonly int UnitIntervalModifier = 100;

		public readonly int InitialAttackDelay = 0;

		public override object Create(ActorInitializer init) { return new BotLimits(init.Self, this); }
	}

	public class BotLimits : ConditionalTrait<BotLimitsInfo>
	{
		public BotLimits(Actor self, BotLimitsInfo info) : base(info)
		{
		}
	}
}
