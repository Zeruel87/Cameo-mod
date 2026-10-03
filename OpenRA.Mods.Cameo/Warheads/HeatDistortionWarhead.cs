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

using OpenRA.GameRules;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Mods.Common.Warheads;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Warheads
{
	[Desc("Registers a screen-space heat-haze distortion at the impact position. Purely visual, no damage.")]
	public class HeatDistortionWarhead : Warhead
	{
		[Desc("Scale multiplier on the renderer's DistortionRadius and DistortionStrength.")]
		public readonly float Scale = 1f;

		[Desc("Additional scale multiplier on the renderer's DistortionRadius only.")]
		public readonly float RadiusScale = 1f;

		[Desc("Additional scale multiplier on the renderer's DistortionStrength only.")]
		public readonly float StrengthScale = 1f;

		[Desc("Combined render-frame budget for fade-in and fade-out. The fade-out uses the frames remaining after FadeInFrames. 0 = single-frame flash when HoldFrames is also 0.")]
		public readonly int FadeFrames = 90;

		[Desc("Number of render frames to fade in over. 0 = instant on.")]
		public readonly int FadeInFrames = 0;

		[Desc("Number of render frames to hold at full strength between fade-in and fade-out.")]
		public readonly int HoldFrames = 0;

		public override bool IsValidAgainst(Actor victim, Actor firedBy) => true;

		public override void DoImpact(in Target target, WarheadArgs args)
		{
			if (!Game.Settings.Graphics.HeatDistortion)
				return;

			// Use target.CenterPosition, not args.ImpactPosition: the latter is only populated by real
			// projectiles. Superweapons detonate via the projectile-less WeaponInfo.Impact(target, firedBy)
			// overload, which leaves ImpactPosition at (0,0,0). CreateEffectWarhead uses CenterPosition too.
			args.SourceActor.World.WorldActor.TraitOrDefault<HeatDistortionRenderer>()
				?.RegisterDistortion(
					target.CenterPosition,
					Scale * RadiusScale,
					Scale * StrengthScale,
					FadeFrames,
					FadeInFrames,
					HoldFrames);
		}
	}
}
