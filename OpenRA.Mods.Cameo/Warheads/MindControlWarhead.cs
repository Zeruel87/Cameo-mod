#region Copyright & License Information
/*
 * Copyright 2015- OpenRA.Mods.AS Developers (see AUTHORS)
 * This file is a part of a third-party plugin for OpenRA, which is
 * free software. It is made available to you under the terms of the
 * GNU General Public License as published by the Free Software
 * Foundation. For more information, see COPYING.
 */
#endregion

using System;
using System.Linq;
using OpenRA.GameRules;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.CA.Warheads;
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Warheads
{
	[Desc("Enslaves affected targets to the firer.")]
	public class MindControlWarhead : WarheadAS
	{
		[Desc("The condition to apply. Must be included in the target actor's ExternalConditions list.")]
		public readonly string Condition = null;

		public readonly WDist Range = WDist.FromCells(1);

		[Desc("What types of targets are affected.")]
		public readonly BitSet<TargetableType> ChangeOwnerValidTargets = new("Ground", "Water");

		[Desc("What types of targets are unaffected.", "Overrules ChangeOwnerValidTargets.")]
		public readonly BitSet<TargetableType> ChangeOwnerInvalidTargets;

		[Desc("What diplomatic stances are affected.")]
		public readonly PlayerRelationship ChangeOwnerValidRelationships = PlayerRelationship.Neutral | PlayerRelationship.Enemy;

		public override void DoImpact(in Target target, WarheadArgs args)
		{
			var firedBy = args.SourceActor;
			if (!target.IsValidFor(firedBy))
				return;

			//if (!IsValidImpact(target.CenterPosition, firedBy))
			//	return;

			var mc = firedBy.Trait<MindController>();
			if (mc == null || mc.IsTraitDisabled || mc.IsTraitPaused) return;

            var actors = firedBy.World.FindActorsInCircle(target.CenterPosition, Range);

			foreach (var a in actors)
			{
				if (!IsValidForOwnerChange(a, firedBy))
					continue;

				var capturable = a.TraitsImplementing<MindControllable>()
					.FirstOrDefault(c => !c.IsTraitDisabled);

				if (a.IsDead || capturable == null)
					continue;

				mc.AddSlave(firedBy, a);

				// Stop shooting, you have new enemies
				a.CancelActivity();
			}
		}

		bool IsValidForOwnerChange(Actor victim, Actor firedBy)
		{
			var relationship = firedBy.Owner.RelationshipWith(victim.Owner);
			if (!ChangeOwnerValidRelationships.HasRelationship(relationship))
				return false;

			// A target type is valid if it is in the valid targets list, and not in the invalid targets list.
			if (!IsValidTargetForOwnerChange(victim.GetEnabledTargetTypes()))
				return false;

			return true;
		}

		bool IsValidTargetForOwnerChange(BitSet<TargetableType> targetTypes)
		{
			return ChangeOwnerValidTargets.Overlaps(targetTypes) && !ChangeOwnerInvalidTargets.Overlaps(targetTypes);
		}
	}
}
