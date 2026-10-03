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

using System.Numerics;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Conditionally applies a global colour tint to the world by driving the terrain lighting, ",
		"so it tints terrain and units but is skipped by sprites that set IgnoreWorldTint (and by ",
		"non-sprite visuals such as beams and zaps). Use this instead of a fullscreen tint ",
		"post-process when weapon/flame visuals must stay untinted.")]
	[TraitLocation(SystemActors.World | SystemActors.EditorWorld)]
	public class ConditionalWorldTintInfo : ConditionalTraitInfo, Requires<TerrainLightingInfo>
	{
		public readonly float Red = 1f;
		public readonly float Green = 1f;
		public readonly float Blue = 1f;

		[Desc("Overall brightness multiplier applied on top of the colour.")]
		public readonly float Ambient = 1f;

		public override object Create(ActorInitializer init) { return new ConditionalWorldTint(this); }
	}

	public class ConditionalWorldTint : ConditionalTrait<ConditionalWorldTintInfo>
	{
		public ConditionalWorldTint(ConditionalWorldTintInfo info)
			: base(info) { }

		protected override void TraitEnabled(Actor self)
		{
			self.Trait<TerrainLighting>().SetAmbientTint(
				new Vector3(Info.Ambient * Info.Red, Info.Ambient * Info.Green, Info.Ambient * Info.Blue));
		}

		protected override void TraitDisabled(Actor self)
		{
			self.Trait<TerrainLighting>().SetAmbientTint(Vector3.One);
		}
	}
}
