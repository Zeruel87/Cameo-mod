// Copyright (c) Fransbot contributors.
// Licensed under the GNU General Public License version 3 or later.

using OpenRA;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace Fransbot.OpenRA.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("External Fransbot controller and integration boundary.")]
	public sealed class FransbotControllerBotModuleInfo : ConditionalTraitInfo
	{
		[Desc("Number of bot ticks between strategic decisions.")]
		public readonly int DecisionInterval = 25;

		public override object Create(ActorInitializer init)
		{
			return new FransbotControllerBotModule(this);
		}
	}

	/// <summary>
	/// Minimal external BotModule used to validate assembly loading and lifecycle.
	/// Gameplay decisions will be added behind this boundary in later phases.
	/// </summary>
	public sealed class FransbotControllerBotModule : ConditionalTrait<FransbotControllerBotModuleInfo>, IBotEnabled, IBotTick
	{
		int ticksUntilDecision;

		public FransbotControllerBotModule(FransbotControllerBotModuleInfo info)
			: base(info)
		{
			ticksUntilDecision = info.DecisionInterval;
		}

		void IBotEnabled.BotEnabled(IBot bot)
		{
			ticksUntilDecision = Info.DecisionInterval;
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (--ticksUntilDecision > 0)
				return;

			ticksUntilDecision = Info.DecisionInterval;

			// Bot code must not mutate the synchronized world directly.
			// Future decisions enter the simulation through bot.QueueOrder(...).
		}
	}
}

