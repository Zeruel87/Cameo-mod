#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System.Collections.Generic;
using System.Linq;
using OpenRA.Effects;
using OpenRA.Graphics;
using OpenRA.Mods.CA.Traits;
using OpenRA.Primitives;

namespace OpenRA.Mods.CA.Graphics
{
	public class TintedCell : IRenderable, IFinalizedRenderable, IEffect
	{
		public int Ticks = 0;
		readonly TintedCellsLayer layer;
		readonly CPos cpos;
		readonly WPos wpos;

		public int Level { get; private set; }
		public int ZOffset { get { return layer.Info.ZOffset; } }

		public TintedCell(TintedCellsLayer layer, CPos cpos, WPos wpos)
		{
			this.layer = layer;
			this.cpos = cpos;
			this.wpos = wpos;
		}

		public TintedCell(TintedCell src)
		{
			Ticks = src.Ticks;
			Level = src.Level;
			layer = src.layer;
			cpos = src.cpos;
			wpos = src.wpos;
		}

		public IRenderable WithPalette(PaletteReference newPalette) { return this; }
		public IRenderable WithZOffset(int newOffset) { return this; }
		public IRenderable OffsetBy(in WVec vec) { return this; }
		public IRenderable AsDecoration() { return this; }

		public PaletteReference Palette { get { return null; } }
		public bool IsDecoration { get { return false; } }

		WPos IRenderable.Pos { get { return wpos; } }

		IFinalizedRenderable IRenderable.PrepareRender(WorldRenderer wr) { return this; }

		bool firstTime = true;
		float3[] screen;
		int alpha;

		int tintedLeft = 0;
		int tintedRight = 0;
		int tintedBottom = 0;
		int tintedTop = 0;

		public void Render(WorldRenderer wr)
		{
			if (firstTime)
			{
				var map = wr.World.Map;
				var terrainInfo = wr.World.Map.Rules.TerrainInfo;
				var uv = cpos.ToMPos(map);

				if (!map.Height.Contains(uv))
					return;

				var tile = map.Tiles[uv];
				var ti = terrainInfo.GetTerrainInfo(tile);
				var ramp = ti != null ? ti.RampType : 0;

				var corners = map.Grid.Ramps[ramp].Corners;
				screen = corners.Select(c => wr.Screen3DPxPosition(wpos + c - new WVec(0, 0, map.Grid.Ramps[ramp].CenterHeightOffset) + new WVec(0, 0, ZOffset))).ToArray();

				CPos neighborL = new CPos(cpos.X - 1, cpos.Y);
				CPos neighborR = new CPos(cpos.X + 1, cpos.Y);
				CPos neighborT = new CPos(cpos.X, cpos.Y - 1);
				CPos neighborB = new CPos(cpos.X, cpos.Y + 1);

				tintedLeft = 0;
				tintedTop = 0;
				tintedRight = 0;
				tintedBottom = 0;

				if (layer.GetTiles().ContainsKey(neighborL))
					tintedLeft = layer.GetTiles()[neighborL].Level;
				if (layer.GetTiles().ContainsKey(neighborR))
					tintedRight = layer.GetTiles()[neighborR].Level;
				if (layer.GetTiles().ContainsKey(neighborT))
					tintedTop = layer.GetTiles()[neighborT].Level;
				if (layer.GetTiles().ContainsKey(neighborB))
					tintedBottom = layer.GetTiles()[neighborB].Level;

				SetLevel(Level);

				firstTime = false;
			}

			if (Level == 0)
				return;

			var countTintedNeighbors = 0;
			if (tintedTop != 0)
				countTintedNeighbors++;
			if (tintedRight != 0)
				countTintedNeighbors++;
			if (tintedLeft != 0)
				countTintedNeighbors++;
			if (tintedBottom != 0)
				countTintedNeighbors++;

			var center = new float3((screen[0].X + screen[1].X) / 2, (screen[1].Y + screen[2].Y) / 2, screen[1].Z);
			var selfLevel = 0;
			if (layer.GetTiles().ContainsKey(cpos))
				selfLevel = layer.GetTiles()[cpos].Level;

			if (countTintedNeighbors >= 3) {
				SetLevel((selfLevel + tintedTop) / 2);
				Game.Renderer.WorldRgbaColorRenderer.FillTriangle(center, screen[0], screen[1], Color.FromArgb(alpha, layer.Info.Color));
				SetLevel((selfLevel + tintedRight) / 2);
				Game.Renderer.WorldRgbaColorRenderer.FillTriangle(center, screen[1], screen[2], Color.FromArgb(alpha, layer.Info.Color));
				SetLevel((selfLevel + tintedLeft) / 2);
				Game.Renderer.WorldRgbaColorRenderer.FillTriangle(center, screen[0], screen[3], Color.FromArgb(alpha, layer.Info.Color));
				SetLevel((selfLevel + tintedBottom) / 2);
				Game.Renderer.WorldRgbaColorRenderer.FillTriangle(center, screen[2], screen[3], Color.FromArgb(alpha, layer.Info.Color));
			}
			else {
				if (tintedTop != 0)
				{
					SetLevel((selfLevel + tintedTop) / 2);
					Game.Renderer.WorldRgbaColorRenderer.FillTriangle(center, screen[0], screen[1], Color.FromArgb(alpha, layer.Info.Color));
				}
				if (tintedRight != 0)
				{
					SetLevel((selfLevel + tintedRight) / 2);
					Game.Renderer.WorldRgbaColorRenderer.FillTriangle(center, screen[1], screen[2], Color.FromArgb(alpha, layer.Info.Color));
				}
				if (tintedLeft != 0)
				{
					SetLevel((selfLevel + tintedLeft) / 2);
					Game.Renderer.WorldRgbaColorRenderer.FillTriangle(center, screen[0], screen[3], Color.FromArgb(alpha, layer.Info.Color));
				}
				if (tintedBottom != 0)
				{
					SetLevel((selfLevel + tintedBottom) / 2);
					Game.Renderer.WorldRgbaColorRenderer.FillTriangle(center, screen[2], screen[3], Color.FromArgb(alpha, layer.Info.Color));
				}
			}
		}

		public void SetLevel(int value)
		{
			Level = value;

			if (layer == null)
				return;

			// Saturate the visualization to MaxLevel
			int level = Level.Clamp(0, layer.Info.MaxLevel);

			// Linear interpolation
			alpha = layer.Info.Darkest + (layer.TintLevel * level) / 255;
		}

		public void RenderDebugGeometry(WorldRenderer wr) { }
		public Rectangle ScreenBounds(WorldRenderer wr) { return Rectangle.Empty; }
		public void Tick(World world) { }
		IEnumerable<IRenderable> IEffect.Render(WorldRenderer r) { yield return this; }
	}
}
