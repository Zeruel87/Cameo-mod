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
using System.Numerics;
using OpenRA.Graphics;
using OpenRA.Mods.AS.Traits;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Graphics
{
	/// <summary>
	/// Draws an actor's selection bars in W21 LAYER ORDER, outermost first:
	/// shield, then integrity, then armor plating, then health, then everything else.
	/// </summary>
	/// <remarks>
	/// Common's SelectionBarsAnnotationRenderable always draws HEALTH FIRST and pushes
	/// every extra bar BELOW it (each one offset a further 4px down). That reads exactly
	/// backwards for a layered unit: damage arrives at the shield, passes to the armor and
	/// only then reaches health, so the bar a player watches first should be on top.
	///
	/// Only the three LAYER bars are reordered. Ammo, cargo, charge and every other
	/// ISelectionBar keeps its existing position underneath health, so this changes the
	/// three bars the maintainer asked about and nothing else.
	/// </remarks>
	public class LayeredSelectionBarsRenderable : IRenderable, IFinalizedRenderable
	{
		const float BarSpacing = 4;

		readonly Actor actor;
		readonly Rectangle decorationBounds;

		public LayeredSelectionBarsRenderable(Actor actor, Rectangle decorationBounds, bool displayHealth, bool displayExtra)
			: this(actor.CenterPosition, actor, decorationBounds)
		{
			DisplayHealth = displayHealth;
			DisplayExtra = displayExtra;
		}

		public LayeredSelectionBarsRenderable(WPos pos, Actor actor, Rectangle decorationBounds)
		{
			Pos = pos;
			this.actor = actor;
			this.decorationBounds = decorationBounds;
		}

		public WPos Pos { get; }
		public bool DisplayHealth { get; }
		public bool DisplayExtra { get; }

		public int ZOffset => 0;
		public bool IsDecoration => true;

		public IRenderable WithZOffset(int newOffset) { return this; }
		public IRenderable OffsetBy(in WVec vec) { return new LayeredSelectionBarsRenderable(Pos + vec, actor, decorationBounds); }
		public IRenderable AsDecoration() { return this; }

		/// <summary>
		/// Where a bar sits in the damage stack. Lower is further out, so lower draws
		/// higher up. Anything that is not a layer returns -1 and keeps its old place
		/// below health.
		/// </summary>
		static int LayerRank(ISelectionBar bar)
		{
			return bar switch
			{
				Shielded => 0,
				Integrity => 1,
				ArmorPlating => 2,
				_ => -1,
			};
		}

		static void DrawBar(Vector2 start, Vector2 end, float value, Color barColor)
		{
			var c = Color.FromArgb(128, 30, 30, 30);
			var c2 = Color.FromArgb(128, 10, 10, 10);
			var p = new Vector2(0, -4);
			var q = new Vector2(0, -3);
			var r = new Vector2(0, -2);

			var barColor2 = Color.FromArgb(255, barColor.R / 2, barColor.G / 2, barColor.B / 2);

			var z = Vector2.Lerp(start, end, value);
			var cr = Game.Renderer.RgbaColorRenderer;
			cr.DrawLine(start + p, end + p, 1, c);
			cr.DrawLine(start + q, end + q, 1, c2);
			cr.DrawLine(start + r, end + r, 1, c);

			cr.DrawLine(start + p, z + p, 1, barColor2);
			cr.DrawLine(start + q, z + q, 1, barColor);
			cr.DrawLine(start + r, z + r, 1, barColor2);
		}

		static Color GetHealthColor(IHealth health)
		{
			return health.DamageState == DamageState.Critical ? Color.Red :
				health.DamageState == DamageState.Heavy ? Color.Yellow : Color.LimeGreen;
		}

		static void DrawHealthBar(IHealth health, Vector2 start, Vector2 end)
		{
			var c = Color.FromArgb(128, 30, 30, 30);
			var c2 = Color.FromArgb(128, 10, 10, 10);
			var p = new Vector2(0, -4);
			var q = new Vector2(0, -3);
			var r = new Vector2(0, -2);

			var healthColor = GetHealthColor(health);
			var healthColor2 = Color.FromArgb(255, healthColor.R / 2, healthColor.G / 2, healthColor.B / 2);

			var z = Vector2.Lerp(start, end, (float)health.HP / health.MaxHP);

			var cr = Game.Renderer.RgbaColorRenderer;
			cr.DrawLine(start + p, end + p, 1, c);
			cr.DrawLine(start + q, end + q, 1, c2);
			cr.DrawLine(start + r, end + r, 1, c);

			cr.DrawLine(start + p, z + p, 1, healthColor2);
			cr.DrawLine(start + q, z + q, 1, healthColor);
			cr.DrawLine(start + r, z + r, 1, healthColor2);

			// The orange "damage just taken" trail, unchanged from Common.
			if (health.DisplayHP != health.HP)
			{
				var deltaColor = Color.OrangeRed;
				var deltaColor2 = Color.FromArgb(255, deltaColor.R / 2, deltaColor.G / 2, deltaColor.B / 2);
				var zz = Vector2.Lerp(start, end, (float)health.DisplayHP / health.MaxHP);

				cr.DrawLine(z + p, zz + p, 1, deltaColor2);
				cr.DrawLine(z + q, zz + q, 1, deltaColor);
				cr.DrawLine(z + r, zz + r, 1, deltaColor2);
			}
		}

		public IFinalizedRenderable PrepareRender(WorldRenderer wr) { return this; }

		public void Render(WorldRenderer wr)
		{
			if (!actor.IsInWorld || actor.IsDead)
				return;

			var health = actor.TraitOrDefault<IHealth>();
			var start = wr.Viewport.WorldToViewPx(new Vector3(decorationBounds.Left + 1, decorationBounds.Top, 0)).ToVector2();
			var end = wr.Viewport.WorldToViewPx(new Vector3(decorationBounds.Right - 1, decorationBounds.Top, 0)).ToVector2();

			// Split the extras before drawing anything: the health bar's row depends on how
			// many LAYER bars are going to sit above it.
			var layers = new List<(int Rank, ISelectionBar Bar)>();
			var others = new List<ISelectionBar>();
			if (DisplayExtra)
			{
				foreach (var bar in actor.TraitsImplementing<ISelectionBar>())
				{
					// Same visibility test Common uses — a bar reporting 0 that does not ask
					// to be shown when empty takes up no row at all.
					if (bar.GetValue() == 0 && !bar.DisplayWhenEmpty)
						continue;

					var rank = LayerRank(bar);
					if (rank >= 0)
						layers.Add((rank, bar));
					else
						others.Add(bar);
				}

				// Sort by stack position, not by trait declaration order. Declaration order
				// happens to be right today, but it is an accident of which template was
				// inherited first and would silently flip the shield and armor bars the
				// moment somebody reordered an Inherits line.
				layers.Sort((a, b) => a.Rank.CompareTo(b.Rank));
			}

			var row = 0;
			foreach (var (_, bar) in layers)
			{
				var offset = new Vector2(0, row * BarSpacing);
				DrawBar(start + offset, end + offset, bar.GetValue(), bar.GetColor());
				row++;
			}

			if (DisplayHealth && health != null && !health.IsDead)
			{
				var offset = new Vector2(0, row * BarSpacing);
				DrawHealthBar(health, start + offset, end + offset);
			}

			// Health always occupies a row for the purposes of what sits below it, even when
			// it is not being drawn, so toggling the health bar cannot make the ammo bar jump.
			row++;

			foreach (var bar in others)
			{
				var offset = new Vector2(0, row * BarSpacing);
				DrawBar(start + offset, end + offset, bar.GetValue(), bar.GetColor());
				row++;
			}
		}

		public void RenderDebugGeometry(WorldRenderer wr) { }
		public Rectangle ScreenBounds(WorldRenderer wr) { return Rectangle.Empty; }
	}
}
