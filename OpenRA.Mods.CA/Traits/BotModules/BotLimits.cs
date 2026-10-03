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

		[Desc("Prioritize the first barracks before the first refinery for configured factions.")]
		public readonly bool PrioritizeBarracksBeforeRefinery = false;

		[Desc("Ticks the same personality candidate must persist before this difficulty switches to it. Negative disables switching.")]
		public readonly int PersonalityReactionDelay = 7500;

		[Desc("Cash above which the base builder adds more production structures to spend what it earns.",
			"Overrides BaseBuilderBotModuleCA.NewProductionCashThreshold. Negative: use the module's value.")]
		public readonly int NewProductionCashThreshold = -1;

		[Desc("Cash above which the unit builder fills every unit queue in one pass.",
			"Overrides UnitBuilderBotModuleCA.MaximiseProductionCashRequirement. Negative: use the module's value.")]
		public readonly int MaximiseProductionCashRequirement = -1;

		[Desc("Percent (0-100) of mobile combat picks the unit builder may spend on COUNTERS to the enemy army it",
			"has observed (through fog when the master AI observes through fog). 0 disables adaptive counters.")]
		public readonly int AdaptiveCounterWeight = 0;

		[Desc("Self-preservation (AI_DEEP_RESEARCH.md §7, Zero-K's lesson): a ground squad using the combat predictor",
			"retreats when its predicted strength ratio against the enemies it sees falls below this percent. Higher",
			"tiers value their units more. Maintainer 2026-09-28: never suicide units.")]
		public readonly int RetreatRatioPct = 50;

		public override object Create(ActorInitializer init) { return new BotLimits(init.Self, this); }
	}

	public class BotLimits : ConditionalTrait<BotLimitsInfo>
	{
		public BotLimits(Actor self, BotLimitsInfo info) : base(info)
		{
		}
	}
}
