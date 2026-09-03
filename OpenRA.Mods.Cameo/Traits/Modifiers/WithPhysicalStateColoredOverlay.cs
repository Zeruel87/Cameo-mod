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
using OpenRA.Graphics;
using OpenRA.Primitives;
using OpenRA.Traits;
using OpenRA.Mods.Common.Traits;
using System.Linq;
using System;

namespace OpenRA.Mods.Cameo.Traits
{
	public enum PhysicalStateOverlayBlendMode
	{
		Additive,
		Multiply
	}

	[Desc("Display a colored overlay based on PhysicalState, changing along a gradient between two values for upper and lower bounds.")]
	public class WithPhysicalStateColoredOverlayInfo : ConditionalTraitInfo, Requires<PhysicalStateInfo>
	{
		[FieldLoader.Require]
		[Desc("Name of the PhysicalState to track.")]
		public readonly string PhysicalStateName = null;

		[Desc("Color to overlay at LowerValue.")]
		public readonly Color MinColor = Color.FromArgb(0, 0, 0, 0);

		[Desc("Color to overlay at UpperValue.")]
		public readonly Color MaxColor = Color.FromArgb(128, 128, 0, 0);

		[Desc("Lower bound for MinColor.")]
		public readonly int LowerValue = 0;

		[Desc("Upper bound for MaxColor.")]
		public readonly int UpperValue = 100;

		[Desc("How the physical-state tint blends with the renderable. Additive can brighten; Multiply only darkens or preserves channels.")]
		public readonly PhysicalStateOverlayBlendMode BlendMode = PhysicalStateOverlayBlendMode.Additive;

		public override object Create(ActorInitializer init) { return new WithPhysicalStateColoredOverlay(init.Self, this); }
	}

	public class WithPhysicalStateColoredOverlay : ConditionalTrait<WithPhysicalStateColoredOverlayInfo>, IRenderModifier, INotifyPhysicalStateChanged
	{
		readonly Actor self;
		readonly float3 maxTint;
		readonly float3 minTint;
		readonly float3 tintRange;

		readonly float alphaRange;
		readonly float minAlpha;
		readonly float maxAlpha;

		readonly int valueRange;
		readonly PhysicalState physicalState;

		float3 currentTint;
		float currentAlpha;
		float proportion;

		public WithPhysicalStateColoredOverlay(Actor self, WithPhysicalStateColoredOverlayInfo info)
			: base(info)
		{
			this.self = self;
			valueRange = Info.UpperValue - Info.LowerValue;
			maxTint = new float3(info.MaxColor.R, info.MaxColor.G, info.MaxColor.B) / 255f;
			minTint = new float3(info.MinColor.R, info.MinColor.G, info.MinColor.B) / 255f;
			tintRange = maxTint - minTint;
			
			minAlpha = info.MinColor.A / 255f;
			maxAlpha = info.MaxColor.A / 255f;
			alphaRange = maxAlpha - minAlpha;

			physicalState = self.TraitsImplementing<PhysicalState>()
				.FirstOrDefault(ps => ps.Name == info.PhysicalStateName);
		}

		void UpdateColor()
		{
			proportion = (float)(physicalState.Value - Info.LowerValue) / valueRange;

			if (proportion < 1)
			{
				currentTint = minTint + proportion * tintRange;
				currentAlpha = minAlpha + proportion * alphaRange;
			}
			else
			{
				currentTint = maxTint;
				currentAlpha = maxAlpha;
			}
		}

		IEnumerable<IRenderable> IRenderModifier.ModifyRender(Actor self, WorldRenderer wr, IEnumerable<IRenderable> r)
		{
			if (IsTraitDisabled)
				return r;

			if (physicalState.Value > Info.UpperValue || physicalState.Value < Info.LowerValue)
				return r;

			return ModifiedRender(r);
		}

		IEnumerable<IRenderable> ModifiedRender(IEnumerable<IRenderable> r)
		{
			foreach (var a in r)
			{
				if (!a.IsDecoration && a is IModifyableRenderable ma)
				{
					if (Info.BlendMode == PhysicalStateOverlayBlendMode.Multiply)
					{
						// Interpolate from neutral white toward the state colour, then multiply the
						// renderable's existing tint. Every channel remains <= its original value, so
						// sprite/model detail is preserved and the effect can never brighten pixels.
						var multiply = float3.Ones + currentAlpha * (currentTint - float3.Ones);
						yield return ma.WithTint(ma.Tint * multiply, ma.TintModifiers);
					}
					else
					{
						// Additive "glow": add the tint colour on top of the sprite/model, scaled by the
						// current alpha. The shader treats alpha=2 as the additive-overlay sentinel
						// (vTint.a > 1.0), adding vTint.rgb * (alpha - 1).
						var scaledTint = currentAlpha * currentTint;
						yield return ma.WithTint(scaledTint, TintModifiers.OverlayTint).WithAlpha(2f);
					}
				}
				else
				{
					yield return a;
				}
			}
		}

		IEnumerable<Rectangle> IRenderModifier.ModifyScreenBounds(Actor self, WorldRenderer wr, IEnumerable<Rectangle> bounds)
		{
			return bounds;
		}

		void INotifyPhysicalStateChanged.PhysicalStateChanged(Actor self, PhysicalState physicalState, int oldValue, int newValue)
		{
			if (physicalState == this.physicalState)
				UpdateColor();
		}
	}
}
