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
using OpenRA.Mods.Common.Graphics;
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.Render
{
	[Desc("Renders a short-lived lens flare at the barrel that has just fired.")]
	public sealed class WithAttackLensFlareInfo : ConditionalTraitInfo
	{
		[Desc("Armament names that trigger a flare.")]
		public readonly HashSet<string> Armaments = ["primary"];

		[Desc("Color of the flare rays.")]
		public readonly Color RayColor = Color.Red;

		[Desc("Color of the flare core.")]
		public readonly Color CoreColor = Color.White;

		[Desc("Horizontal and vertical flare ray lengths in pixels.")]
		public readonly int2 Size = new(28, 22);

		[Desc("Flare ray width in pixels.")]
		public readonly float Width = 2f;

		[Desc("Flare core diameter in pixels.")]
		public readonly float CoreSize = 4f;

		[Desc("Number of ticks the flare remains after each shot.")]
		public readonly int Duration = 8;

		[Desc("Offset added to the flare render depth.")]
		public readonly int ZOffset = 1;

		public override object Create(ActorInitializer init) { return new WithAttackLensFlare(init.Self, this); }
	}

	public sealed class WithAttackLensFlare : ConditionalTrait<WithAttackLensFlareInfo>,
		INotifyAttack, IRender, ITick
	{
		sealed class FlareState
		{
			public readonly Armament Armament;
			public readonly Barrel Barrel;
			public readonly LensFlareRenderable Flare;
			public readonly IRenderable[] Renderable;
			public int Remaining;

			public FlareState(Armament armament, Barrel barrel, WithAttackLensFlareInfo info)
			{
				Armament = armament;
				Barrel = barrel;
				Flare = new LensFlareRenderable(WPos.Zero, info.ZOffset, info.RayColor, info.CoreColor,
					info.Size.X, info.Size.Y, info.Width, info.CoreSize);
				Renderable = [Flare];
			}
		}

		readonly Dictionary<Barrel, FlareState> flares = [];

		public WithAttackLensFlare(Actor self, WithAttackLensFlareInfo info)
			: base(info)
		{
		}

		protected override void Created(Actor self)
		{
			foreach (var armament in self.TraitsImplementing<Armament>())
			{
				if (!Info.Armaments.Contains(armament.Info.Name))
					continue;

				foreach (var barrel in armament.Barrels)
					flares.Add(barrel, new FlareState(armament, barrel, Info));
			}

			base.Created(self);
		}

		void INotifyAttack.Attacking(Actor self, in Target target, Armament armament, Barrel barrel)
		{
			if (!IsTraitDisabled && barrel != null && flares.TryGetValue(barrel, out var flare))
				flare.Remaining = Info.Duration;
		}

		void INotifyAttack.PreparingAttack(Actor self, in Target target, Armament armament, Barrel barrel) { }

		void ITick.Tick(Actor self)
		{
			foreach (var flare in flares.Values)
				if (flare.Remaining > 0)
					flare.Remaining--;
		}

		IEnumerable<IRenderable> IRender.Render(Actor self, WorldRenderer wr)
		{
			if (IsTraitDisabled || self.IsDead || !self.IsInWorld || self.World.FogObscures(self))
				yield break;

			foreach (var flare in flares.Values)
			{
				if (flare.Remaining <= 0 || flare.Armament.IsTraitDisabled)
					continue;

				var opacity = flare.Remaining / (float)Info.Duration;
				var ray = Color.FromArgb((int)(Info.RayColor.A * opacity), Info.RayColor);
				var core = Color.FromArgb((int)(Info.CoreColor.A * opacity), Info.CoreColor);
				var muzzle = self.CenterPosition + flare.Armament.MuzzleOffset(self, flare.Barrel);
				flare.Flare.Update(muzzle, Info.ZOffset, ray, core,
					Info.Size.X, Info.Size.Y, Info.Width, Info.CoreSize);

				foreach (var renderable in flare.Renderable)
					yield return renderable;
			}
		}

		IEnumerable<Rectangle> IRender.ScreenBounds(Actor self, WorldRenderer wr) { return []; }
	}
}
