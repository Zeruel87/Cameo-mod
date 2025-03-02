#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System.Collections.Generic;
using OpenRA.Activities;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Orders;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	[Desc("Actor becomes a specified actor type when this trait is triggered.")]
	public class InstantTransformsInfo : PausableConditionalTraitInfo
	{
		[ActorReference]
		[FieldLoader.Require]
		[Desc("Actor to transform into.")]
		public readonly string IntoActor = null;

		[Desc("Offset to spawn the transformed actor relative to the current cell.")]
		public readonly CVec Offset = CVec.Zero;

		[Desc("Facing that the actor must face before transforming.")]
		public readonly WAngle Facing = new WAngle(384);

		[Desc("Sounds to play when transforming.")]
		public readonly string[] TransformSounds = System.Array.Empty<string>();

		[Desc("Sounds to play when the transformation is blocked.")]
		public readonly string[] NoTransformSounds = System.Array.Empty<string>();

		[NotificationReference("Speech")]
		[Desc("Notification to play when transforming.")]
		public readonly string TransformNotification = null;

		[NotificationReference("Speech")]
		[Desc("Notification to play when the transformation is blocked.")]
		public readonly string NoTransformNotification = null;

		[Desc("Cursor to display when able to (un)deploy the actor.")]
		public readonly string DeployCursor = "deploy";

		[Desc("Cursor to display when unable to (un)deploy the actor.")]
		public readonly string DeployBlockedCursor = "deploy-blocked";

		[VoiceReference]
		public readonly string Voice = "Action";

		public override object Create(ActorInitializer init) { return new InstantTransforms(init, this); }
	}

	public class InstantTransforms : PausableConditionalTrait<InstantTransformsInfo>, IIssueOrder, IResolveOrder, IOrderVoice, IIssueDeployOrder
	{
		readonly Actor self;
		readonly ActorInfo actorInfo;
		readonly BuildingInfo buildingInfo;
		readonly string faction;

		public InstantTransforms(ActorInitializer init, InstantTransformsInfo info)
			: base(info)
		{
			self = init.Self;
			actorInfo = self.World.Map.Rules.Actors[info.IntoActor];
			buildingInfo = actorInfo.TraitInfoOrDefault<BuildingInfo>();
			faction = init.GetValue<FactionInit, string>(self.Owner.Faction.InternalName);
		}

		public string VoicePhraseForOrder(Actor self, Order order)
		{
			return order.OrderString == "DeployTransform" ? Info.Voice : null;
		}

		public bool CanDeploy()
		{
			if (IsTraitPaused || IsTraitDisabled)
				return false;

			return buildingInfo == null || self.World.CanPlaceBuilding(self.Location + Info.Offset, actorInfo, buildingInfo, self);
		}

		public Activity GetTransformActivity(Actor self)
		{
			return new Transform(Info.IntoActor)
			{
				Offset = Info.Offset,
				Facing = Info.Facing,
				Sounds = Info.TransformSounds,
				Notification = Info.TransformNotification,
				Faction = faction
			};
		}

		public IEnumerable<IOrderTargeter> Orders
		{
			get
			{
				if (!IsTraitDisabled)
					yield return new DeployOrderTargeter("DeployTransform", 5,
						() => CanDeploy() ? Info.DeployCursor : Info.DeployBlockedCursor);
			}
		}

		public Order IssueOrder(Actor self, IOrderTargeter order, in Target target, bool queued)
		{
			if (order.OrderID == "DeployTransform")
				return new Order(order.OrderID, self, queued);

			return null;
		}

		Order IIssueDeployOrder.IssueDeployOrder(Actor self, bool queued)
		{
			return new Order("DeployTransform", self, queued);
		}

		bool IIssueDeployOrder.CanIssueDeployOrder(Actor self, bool queued) { return !IsTraitPaused && !IsTraitDisabled; }

		public void DeployTransform(bool queued)
		{
			if (!queued && !CanDeploy())
			{
				// Only play the "Cannot deploy here" audio
				// for non-queued orders
				foreach (var s in Info.NoTransformSounds)
					Game.Sound.PlayToPlayer(SoundType.World, self.Owner, s);

				Game.Sound.PlayNotification(self.World.Map.Rules, self.Owner, "Speech", Info.NoTransformNotification, self.Owner.Faction.InternalName);

				return;
			}

			self.QueueActivity(queued, GetTransformActivity(self));
		}

		public void ResolveOrder(Actor self, Order order)
		{
			if (order.OrderString == "DeployTransform" && !IsTraitPaused && !IsTraitDisabled)
				DeployTransform(order.Queued);
		}
	}
}
