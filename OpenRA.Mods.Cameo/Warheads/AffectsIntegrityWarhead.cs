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

using System.Linq;
using OpenRA.GameRules;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Warheads;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Warheads
{
	[Desc("Grant an external condition to hit actors.")]
	public class AffectsIntegrityWarhead : Warhead
	{
		[Desc("How much (raw) damage to deal.")]
		public readonly int Damage = 0;

		public readonly WDist Range = WDist.FromCells(1);

		public override void DoImpact(in Target target, WarheadArgs args)
		{
			if (target.Type == TargetType.Invalid)
				return;

			var firedBy = args.SourceActor;

			if (target.Type == TargetType.Invalid)
				return;

			var actors = target.Type == TargetType.Actor ? new[] { target.Actor } :
				firedBy.World.FindActorsInCircle(target.CenterPosition, Range);

			foreach (var a in actors)
			{
				if (!IsValidAgainst(a, firedBy))
					continue;

				a.TraitsImplementing<Integrity>()
					.FirstOrDefault(t => !t.IsTraitPaused && !t.IsTraitDisabled)
					?.Regenerate(a, -Damage);
			}
		}
	}
}
