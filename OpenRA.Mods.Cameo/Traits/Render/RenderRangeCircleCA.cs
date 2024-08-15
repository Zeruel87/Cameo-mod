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

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Graphics;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.Render
{
	public enum RangeCircleMode { Maximum, Minimum }

	[Desc("Draw a circle indicating my weapon's range.")]
	sealed class RenderRangeCircleCAInfo : TraitInfo, IPlaceBuildingDecorationInfo, IRulesetLoaded, Requires<ArmamentInfo>
	{
		public readonly string RangeCircleType = null;

		[Desc("Armament names")]
		public readonly string[] Armaments = { "primary", "secondary" };

		[Desc("Range to draw if no armaments are available.")]
		public readonly WDist FallbackRange = WDist.Zero;

		[Desc("Which circle to show. Valid values are `Maximum`, and `Minimum`.")]
		public readonly RangeCircleMode RangeCircleMode = RangeCircleMode.Maximum;

		[Desc("Color of the circle.")]
		public readonly Color Color = Color.FromArgb(128, Color.Yellow);

		[Desc("Range circle line width.")]
		public readonly float Width = 1;

		[Desc("Color of the border.")]
		public readonly Color BorderColor = Color.FromArgb(96, Color.Black);

		[Desc("Range circle border width.")]
		public readonly float BorderWidth = 3;

		// Computed range
		Lazy<WDist> range;

		public IEnumerable<IRenderable> RenderAnnotations(WorldRenderer wr, World w, ActorInfo ai, WPos centerPosition)
		{
			if (range == null || range.Value == WDist.Zero)
				return SpriteRenderable.None;

			var localRange = new RangeCircleAnnotationRenderable(
				centerPosition,
				range.Value,
				0,
				Color,
				Width,
				BorderColor,
				BorderWidth);

			var otherRanges = w.ActorsWithTrait<RenderRangeCircleCA>()
				.Where(a => a.Trait.Info.RangeCircleType == RangeCircleType)
				.SelectMany(a => a.Trait.RangeCircleRenderables());

			return otherRanges.Append(localRange);
		}

		public override object Create(ActorInitializer init) { return new RenderRangeCircleCA(init.Self, this); }

		public void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			// ArmamentInfo.ModifiedRange is set by RulesetLoaded, and may not have been initialized yet.
			// Defer this lookup until we really need it to ensure we get the correct value.
			range = Exts.Lazy(() =>
			{
				var armaments = ai.TraitInfos<ArmamentInfo>().Where(a => a.EnabledByDefault);
				if (!armaments.Any())
					return FallbackRange;

				return armaments.Max(a => a.ModifiedRange);
			});
		}
	}

	sealed class RenderRangeCircleCA : IRenderAnnotationsWhenSelected
	{
		public readonly RenderRangeCircleCAInfo Info;
		readonly Actor self;
		public IEnumerable<Armament> armaments;

		public RenderRangeCircleCA(Actor self, RenderRangeCircleCAInfo info)
		{
			Info = info;
			this.self = self;
			armaments = self.TraitsImplementing<Armament>()
				.Where(a => Info.Armaments.Contains(a.Info.Name)).ToArray();
		}

		public WDist GetMinimumRange()
		{
			// PERF: Avoid LINQ.
			var min = WDist.MaxValue;
			foreach (var armament in armaments)
			{
				if (armament.IsTraitDisabled)
					continue;

				if (armament.IsTraitPaused)
					continue;

				var range = armament.Weapon.MinRange;
				if (min > range)
					min = range;
			}

			return min != WDist.MaxValue ? min : WDist.Zero;
		}

		public WDist GetMaximumRange()
		{
			// PERF: Avoid LINQ.
			var max = WDist.Zero;
			foreach (var armament in armaments)
			{
				if (armament.IsTraitDisabled)
					continue;

				if (armament.IsTraitPaused)
					continue;

				var range = armament.MaxRange();
				if (max < range)
					max = range;
			}

			return max;
		}

		public IEnumerable<IRenderable> RangeCircleRenderables()
		{
			if (!self.Owner.IsAlliedWith(self.World.RenderPlayer))
				yield break;

			var range = Info.RangeCircleMode == RangeCircleMode.Minimum ? GetMinimumRange() : GetMaximumRange();
			if (range == WDist.Zero)
				yield break;

			yield return new RangeCircleAnnotationRenderable(
				self.CenterPosition,
				range,
				0,
				Info.Color,
				Info.Width,
				Info.BorderColor,
				Info.BorderWidth);
		}

		IEnumerable<IRenderable> IRenderAnnotationsWhenSelected.RenderAnnotations(Actor self, WorldRenderer wr)
		{
			return RangeCircleRenderables();
		}

		bool IRenderAnnotationsWhenSelected.SpatiallyPartitionable => false;
	}
}
