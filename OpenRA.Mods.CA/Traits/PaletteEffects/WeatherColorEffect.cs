#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using OpenRA.Graphics;
using OpenRA.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;

namespace OpenRA.Mods.CA.Traits
{
	using Util = OpenRA.Graphics.Util;

	[Desc("Global color tint effect.")]
	public class WeatherPostProcessEffectInfo : TraitInfo
	{
		[Desc("Measured in ticks.")]
		public readonly int Length = 40;

		[Desc("Time (in ticks) to ramp effect")]
		public readonly int RampLength = 10;

		[Desc("Color to overlay.")]
		public readonly Color Color = Color.FromArgb(128, 128, 0, 0);

		[Desc("Set this when using multiple independent flash effects.")]
		public readonly string Type = null;

		public override object Create(ActorInitializer init) { return new WeatherPostProcessEffect(this); }
	}

	public class WeatherPostProcessEffect : RenderPostProcessPassBase, ITick
	{
		public readonly WeatherPostProcessEffectInfo Info;

		int remainingFrames;
		int startRamp;
		int endRamp;

		float alpha;
		float RatioPerRamp;

		public WeatherPostProcessEffect(WeatherPostProcessEffectInfo info)
			: base("flash", PostProcessPassType.AfterWorld)
		{
			Info = info;
		}

		public void Enable(int ticks)
		{
			if (ticks == -1)
				remainingFrames = Info.Length;
			else
				remainingFrames = ticks;

			startRamp = remainingFrames - Info.RampLength;
			endRamp = Info.RampLength;
			RatioPerRamp = Info.Color.A / 255f / Info.RampLength;
		}

		void ITick.Tick(Actor self)
		{
			if (remainingFrames > 0)
				remainingFrames--;
			else alpha = 0;

			if (remainingFrames > startRamp)
				alpha += RatioPerRamp;
			else if (remainingFrames < endRamp)
				alpha -= RatioPerRamp;
		}

		protected override bool Enabled => remainingFrames > 0;
		protected override void PrepareRender(WorldRenderer wr, IShader shader)
		{
			shader.SetVec("Blend", alpha);
			shader.SetVec("Color", (float)Info.Color.R / 255, (float)Info.Color.G / 255, (float)Info.Color.B / 255);
		}
	}
}
