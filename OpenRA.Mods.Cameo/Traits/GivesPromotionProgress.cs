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

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("This actor gives experience to a GainsExperience actor when they are killed.")]
	sealed class GivesPromotionProgressInfo : TraitInfo
	{
		[Desc("If -1, use the value of the unit cost.")]
		public readonly int Experience = -1;

		[Desc("Player relationships the attacking player needs to receive the experience.")]
		public readonly PlayerRelationship ValidRelationships = PlayerRelationship.Neutral | PlayerRelationship.Enemy;

		[Desc("Percentage of the `Experience` value that is being granted to the player owning the killing actor.")]
		public readonly int KillerExperienceModifier = 0;

		[Desc("Percentage of the `Experience` value that is being granted to the player owning the killed actor.")]
		public readonly int OwnerExperienceModifier = 0;

		public override object Create(ActorInitializer init) { return new GivesPromotionProgress(this); }
	}

	sealed class GivesPromotionProgress : INotifyKilled, INotifyCreated
	{
		readonly GivesPromotionProgressInfo info;

		int exp;
		IEnumerable<int> experienceModifiers;

		public GivesPromotionProgress(GivesPromotionProgressInfo info)
		{
			this.info = info;
		}

		void INotifyCreated.Created(Actor self)
		{
			var valued = self.Info.TraitInfoOrDefault<ValuedInfo>();
			exp = info.Experience >= 0 ? info.Experience
				: valued != null ? valued.Cost : 0;

			experienceModifiers = self.TraitsImplementing<IGivesExperienceModifier>().ToArray().Select(m => m.GetGivesExperienceModifier());
		}

		void INotifyKilled.Killed(Actor self, AttackInfo e)
		{
			if (exp == 0 || e.Attacker == null || e.Attacker.Disposed)
				return;

			if (!info.ValidRelationships.HasRelationship(e.Attacker.Owner.RelationshipWith(self.Owner)))
				return;

			exp = Common.Util.ApplyPercentageModifiers(exp, experienceModifiers);

			e.Attacker.Owner.PlayerActor.TraitOrDefault<PlayerPromotions>()
				?.GiveExperience(Common.Util.ApplyPercentageModifiers(exp, new[] { info.KillerExperienceModifier }));

			self.Owner.PlayerActor.TraitOrDefault<PlayerPromotions>()
				?.GiveExperience(Common.Util.ApplyPercentageModifiers(exp, new[] { info.OwnerExperienceModifier }));
		}
	}
}
