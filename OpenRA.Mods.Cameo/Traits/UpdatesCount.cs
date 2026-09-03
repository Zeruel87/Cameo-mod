#region Copyright & License Information
/*
 * Ported to Cameo from OpenRA Combined Arms (github.com/Inq8/CAmod), which is
 * free software under the GNU General Public License. See COPYING.
 *
 * Cameo changes: namespace OpenRA.Mods.CA.* -> OpenRA.Mods.Cameo.*.
 */
#endregion

using System;
using System.Collections.Generic;
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Flags]
	public enum UpdateOnType
	{
		Owned = 1,
		Killed = 2,
		SoldAfterDamage = 4,
		Captured = 8,
		Infiltrated = 16
	}

	[Desc("Updates a counter when the actor is created/disposed or changes owner.")]
	public class UpdatesCountInfo : ConditionalTraitInfo
	{
		[FieldLoader.Require]
		[Desc("Name of the counter to update.")]
		public readonly string Type = null;

		[Desc("Name of the owner counter to increment for the victim player when the actor is killed (requires UpdateOnType to include Killed).")]
		public readonly string LossType = null;

		[Desc("What triggers an update.")]
		public readonly UpdateOnType UpdateOn = UpdateOnType.Owned;

		[Desc("Ticks after being damaged during which selling the actor will update the counter for the damaging player(s).")]
		public readonly int SoldAfterDamageCooldown = 75;

		[Desc("Relationships that a killing/capturing/damaging/infiltrating player must have to update the count. No effect on Owned.")]
		public readonly PlayerRelationship ValidRelationships = PlayerRelationship.Enemy;

		public override object Create(ActorInitializer init) { return new UpdatesCount(this); }
	}

	public class UpdatesCount : ConditionalTrait<UpdatesCountInfo>, INotifyCreated, INotifyActorDisposing, INotifyOwnerChanged,
		INotifyKilled, INotifySold, INotifyDamage, INotifyCapture, INotifyInfiltrated
	{
		public readonly UpdatesCountInfo info;
		CountManager countManager;
		public readonly Dictionary<OpenRA.Player, int> lastDamagedTicks = new();
		HashSet<OpenRA.Player> playersInfiltratedBy = new();

		public UpdatesCount(UpdatesCountInfo info)
			: base(info)
		{
			this.info = info;
		}

		void UpdateCounter(OpenRA.Player owner)
		{
			countManager = owner.PlayerActor.Trait<CountManager>();
		}

		void INotifyCreated.Created(Actor self)
		{
			UpdateCounter(self.Owner);

			if (!info.UpdateOn.HasFlag(UpdateOnType.Owned))
				return;

			if (IsTraitDisabled)
				return;

			countManager.Increment(info.Type);
		}

		protected override void TraitEnabled(Actor self)
		{
			if (info.UpdateOn.HasFlag(UpdateOnType.Owned))
				countManager.Increment(info.Type);
		}

		protected override void TraitDisabled(Actor self)
		{
			if (info.UpdateOn.HasFlag(UpdateOnType.Owned))
				countManager.Decrement(info.Type);
		}

		void INotifyOwnerChanged.OnOwnerChanged(Actor self, OpenRA.Player oldOwner, OpenRA.Player newOwner)
		{
			UpdateCounter(newOwner);

			if (info.UpdateOn.HasFlag(UpdateOnType.Owned))
			{
				oldOwner.PlayerActor.Trait<CountManager>().Decrement(info.Type);

				if (!info.UpdateOn.HasFlag(UpdateOnType.Captured))
					countManager.Increment(info.Type);
			}
		}

		void INotifyActorDisposing.Disposing(Actor self)
		{
			if (info.UpdateOn.HasFlag(UpdateOnType.Owned))
				countManager.Decrement(info.Type);
		}

		void INotifyKilled.Killed(Actor self, AttackInfo e)
		{
			if (!info.UpdateOn.HasFlag(UpdateOnType.Killed))
				return;

			if (self.Owner.WinState != WinState.Undefined)
				return;

			var attackingPlayer = e.Attacker.Owner;

			if (!Info.ValidRelationships.HasRelationship(attackingPlayer.RelationshipWith(self.Owner)))
				return;

			var attackerCounter = attackingPlayer.PlayerActor.Trait<CountManager>();
			attackerCounter.Increment(info.Type);

			if (info.LossType != null)
				self.Owner.PlayerActor.Trait<CountManager>().Increment(info.LossType);
		}

		void INotifySold.Selling(Actor self) { }

		void INotifySold.Sold(Actor self)
		{
			if (!info.UpdateOn.HasFlag(UpdateOnType.SoldAfterDamage))
				return;

			var currentTick = self.World.WorldTick;
			foreach (var kvp in lastDamagedTicks)
			{
				var player = kvp.Key;
				var damagedTick = kvp.Value;
				if (currentTick - damagedTick <= info.SoldAfterDamageCooldown)
				{
					var attackerCounter = player.PlayerActor.Trait<CountManager>();
					attackerCounter.Increment(info.Type);
				}
			}
		}

		void INotifyDamage.Damaged(Actor self, AttackInfo e)
		{
			if (!Info.ValidRelationships.HasRelationship(e.Attacker.Owner.RelationshipWith(self.Owner)))
				return;

			if (info.UpdateOn.HasFlag(UpdateOnType.SoldAfterDamage))
				lastDamagedTicks[e.Attacker.Owner] = self.World.WorldTick;
		}

		void INotifyCapture.OnCapture(Actor self, Actor captor, OpenRA.Player oldOwner, OpenRA.Player newOwner, BitSet<CaptureType> captureTypes)
		{
			if (!info.UpdateOn.HasFlag(UpdateOnType.Captured))
				return;

			if (!Info.ValidRelationships.HasRelationship(newOwner.RelationshipWith(oldOwner)))
				return;

			newOwner.PlayerActor.Trait<CountManager>().Increment(info.Type);
		}

		void INotifyInfiltrated.Infiltrated(Actor self, Actor infiltrator, BitSet<TargetableType> types)
		{
			if (!info.UpdateOn.HasFlag(UpdateOnType.Infiltrated))
				return;

			if (playersInfiltratedBy.Contains(infiltrator.Owner))
				return;

			if (!Info.ValidRelationships.HasRelationship(infiltrator.Owner.RelationshipWith(self.Owner)))
				return;

			infiltrator.Owner.PlayerActor.Trait<CountManager>().Increment(info.Type);
			playersInfiltratedBy.Add(infiltrator.Owner);
		}
	}
}
