#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	[Desc("Turns actor randomly when idle.",
		"CA version applies to any actor with a facing trait.")]
	class TurnOnIdleCAInfo : ConditionalTraitInfo, Requires<IFacingInfo>
	{
		[Desc("Minimum amount of ticks the actor will wait before the turn.")]
		public readonly int MinDelay = 400;

		[Desc("Maximum amount of ticks the actor will wait before the turn.")]
		public readonly int MaxDelay = 800;

		public override object Create(ActorInitializer init) { return new TurnOnIdleCA(init, this); }
	}

	class TurnOnIdleCA : ConditionalTrait<TurnOnIdleCAInfo>, ITick
	{
		int currentDelay;
		WAngle targetFacing;
		readonly IFacing facing;

		public TurnOnIdleCA(ActorInitializer init, TurnOnIdleCAInfo info)
			: base(info)
		{
			currentDelay = init.World.SharedRandom.Next(Info.MinDelay, Info.MaxDelay);
			facing = init.Self.Trait<IFacing>();
			targetFacing = facing.Facing;
		}

		void ITick.Tick(Actor self)
		{
			if (IsTraitDisabled)
				return;

			if (!self.IsIdle)
				return;

			if (--currentDelay > 0)
				return;

			if (targetFacing == facing.Facing)
			{
				targetFacing = new WAngle(self.World.SharedRandom.Next(1024));
				currentDelay = self.World.SharedRandom.Next(Info.MinDelay, Info.MaxDelay);
			}

			facing.Facing = Util.TickFacing(facing.Facing, targetFacing, facing.TurnSpeed);
		}
	}
}
