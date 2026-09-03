#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3
 * of the License, or (at your option) any later version.
 * For more information, see COPYING.
 */
#endregion

using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Displays a one-time notification when a condition enables this trait.")]
	public class ObserverConditionNotificationInfo : ConditionalTraitInfo
	{
		[FieldLoader.Require]
		[FluentReference]
		[Desc("Fluent message to display.")]
		public readonly string Notification = null;

		[Desc("Number of ticks to wait after the trait becomes enabled.")]
		public readonly int Delay = 25;

		[Desc("Only display the notification to observers and replay viewers.")]
		public readonly bool ObserversOnly = true;

		public override object Create(ActorInitializer init) { return new ObserverConditionNotification(this); }
	}

	public class ObserverConditionNotification : ConditionalTrait<ObserverConditionNotificationInfo>, ITick
	{
		int ticksRemaining;
		bool announced;

		public ObserverConditionNotification(ObserverConditionNotificationInfo info)
			: base(info) { }

		protected override void TraitEnabled(Actor self)
		{
			if (announced)
				return;

			if (Info.ObserversOnly && self.World.LocalPlayer != null && !self.World.IsReplay)
			{
				announced = true;
				return;
			}

			ticksRemaining = Info.Delay;
			if (ticksRemaining <= 0)
				Announce(self);
		}

		void ITick.Tick(Actor self)
		{
			if (announced || IsTraitDisabled)
				return;

			if (Info.ObserversOnly && self.World.LocalPlayer != null && !self.World.IsReplay)
			{
				announced = true;
				return;
			}

			if (ticksRemaining > 0)
			{
				ticksRemaining--;
				if (ticksRemaining > 0)
					return;
			}

			Announce(self);
		}

		void Announce(Actor self)
		{
			announced = true;
			TextNotificationsManager.AddSystemLine(Info.Notification, "bot", self.Owner.PlayerName);
		}
	}
}
