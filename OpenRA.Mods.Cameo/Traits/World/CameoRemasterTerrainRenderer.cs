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
using System.IO;
using System.Numerics;
using OpenRA.Graphics;
using OpenRA.Mods.Cameo.Terrain;
using OpenRA.Mods.Common.Terrain;
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	// A fork of TerrainRenderer that drives CameoRemasterTileCache and applies the per-template HD
	// scale. With HD off, the tile cache returns classic sprites at scale 1f, so this renders exactly
	// like the stock TerrainRenderer.
	[TraitLocation(SystemActors.World | SystemActors.EditorWorld)]
	public class CameoRemasterTerrainRendererInfo : TraitInfo, ITiledTerrainRendererInfo
	{
		bool ITiledTerrainRendererInfo.ValidateTileSprites(ITemplatedTerrainInfo terrainInfo, Action<string> onError)
		{
			var failed = false;
			void OnMissingImage(uint id, string f)
			{
				onError($"\tTemplate `{id}` references sprite `{f}` that does not exist.");
				failed = true;
			}

			var tileCache = new CameoRemasterTileCache((CameoRemasterTerrain)terrainInfo, OnMissingImage);
			tileCache.Dispose();
			return failed;
		}

		public override object Create(ActorInitializer init) { return new CameoRemasterTerrainRenderer(init.World); }
	}

	public sealed class CameoRemasterTerrainRenderer : IRenderTerrain, IWorldLoaded, INotifyActorDisposing, ITiledTerrainRenderer
	{
		readonly Map map;
		TerrainSpriteLayer spriteLayer;
		readonly CameoRemasterTerrain terrainInfo;
		readonly CameoRemasterTileCache tileCache;
		WorldRenderer worldRenderer;
		bool disposed;

		public CameoRemasterTerrainRenderer(World world)
		{
			map = world.Map;
			terrainInfo = map.Rules.TerrainInfo as CameoRemasterTerrain;
			if (terrainInfo == null)
				throw new InvalidDataException($"{nameof(CameoRemasterTerrainRenderer)} can only be used with the {nameof(CameoRemasterTerrain)} parser");

			tileCache = new CameoRemasterTileCache(terrainInfo);
		}

		void IWorldLoaded.WorldLoaded(World world, WorldRenderer wr)
		{
			worldRenderer = wr;
			spriteLayer = new TerrainSpriteLayer(world, wr, tileCache.MissingTile, BlendMode.Alpha, world.Type != WorldType.Editor);
			foreach (var cell in map.AllCells)
				UpdateCell(cell);

			map.Tiles.CellEntryChanged += UpdateCell;
			map.Height.CellEntryChanged += UpdateCell;
		}

		public void UpdateCell(CPos cell)
		{
			var tile = map.Tiles[cell];
			var palette = terrainInfo.Palette;
			if (terrainInfo.Templates.TryGetValue(tile.Type, out var template))
				palette = ((CameoRemasterTerrainTemplateInfo)template).Palette ?? palette;

			var sprite = tileCache.TileSprite(tile);
			var paletteReference = worldRenderer.Palette(palette);
			spriteLayer.Update(cell, sprite, paletteReference, tileCache.TileScale(tile));
		}

		void IRenderTerrain.RenderTerrain(WorldRenderer wr, Viewport viewport)
		{
			spriteLayer.Draw(wr.Viewport);

			foreach (var r in wr.World.WorldActor.TraitsImplementing<IRenderOverlay>())
				r.Render(wr);
		}

		void INotifyActorDisposing.Disposing(Actor self)
		{
			if (disposed)
				return;

			map.Tiles.CellEntryChanged -= UpdateCell;
			map.Height.CellEntryChanged -= UpdateCell;

			spriteLayer.Dispose();

			tileCache.Dispose();
			disposed = true;
		}

		Sprite ITiledTerrainRenderer.MissingTile => tileCache.MissingTile;

		Sprite ITiledTerrainRenderer.TileSprite(TerrainTile r, int? variant)
		{
			return tileCache.TileSprite(r, variant);
		}

		Rectangle ITiledTerrainRenderer.TemplateBounds(TerrainTemplateInfo template)
		{
			Rectangle? templateRect = null;
			var tileSize = map.Rules.TerrainInfo.TileSize;

			var i = 0;
			for (var y = 0; y < template.Size.Y; y++)
			{
				for (var x = 0; x < template.Size.X; x++)
				{
					var tile = new TerrainTile(template.Id, (byte)i++);
					if (!terrainInfo.TryGetTileInfo(tile, out var tileInfo))
						continue;

					var sprite = tileCache.TileSprite(tile);
					var s = tileCache.TileScale(tile);
					var u = map.Grid.Type == MapGridType.Rectangular ? x : (x - y) / 2f;
					var v = map.Grid.Type == MapGridType.Rectangular ? y : (x + y) / 2f;

					var tl = new Vector2(u * tileSize.Width, (v - 0.5f * tileInfo.Height) * tileSize.Height) - 0.5f * s * sprite.Size.AsVector2();
					var rect = new Rectangle(
						(int)(tl.X + s * sprite.Offset.X),
						(int)(tl.Y + s * sprite.Offset.Y),
						(int)(s * sprite.Size.X),
						(int)(s * sprite.Size.Y));
					templateRect = templateRect.HasValue ? Rectangle.Union(templateRect.Value, rect) : rect;
				}
			}

			return templateRect ?? Rectangle.Empty;
		}

		IEnumerable<IRenderable> ITiledTerrainRenderer.RenderUIPreview(WorldRenderer wr, TerrainTemplateInfo t, int2 origin, float scale)
		{
			if (t is not CameoRemasterTerrainTemplateInfo template)
				yield break;

			var ts = map.Rules.TerrainInfo.TileSize;
			var gridType = map.Grid.Type;

			var i = 0;
			for (var y = 0; y < template.Size.Y; y++)
			{
				for (var x = 0; x < template.Size.X; x++)
				{
					var tile = new TerrainTile(template.Id, (byte)i++);
					if (!terrainInfo.TryGetTileInfo(tile, out var tileInfo))
						continue;

					var sprite = tileCache.TileSprite(tile, 0);
					var tileScale = tileCache.TileScale(tile);
					var u = gridType == MapGridType.Rectangular ? x : (x - y) / 2f;
					var v = gridType == MapGridType.Rectangular ? y : (x + y) / 2f;
					var offset = scale * (new Vector2(u * ts.Width, (v - 0.5f * tileInfo.Height) * ts.Height) - 0.5f * tileScale * sprite.Size.AsVector2());
					var palette = template.Palette ?? terrainInfo.Palette;

					yield return new UISpriteRenderable(sprite, WPos.Zero, origin.ToVector2() + offset, 0, wr.Palette(palette), scale * tileScale);
				}
			}
		}

		IEnumerable<IRenderable> ITiledTerrainRenderer.RenderPreview(WorldRenderer wr, TerrainTemplateInfo t, WPos origin)
		{
			if (t is not CameoRemasterTerrainTemplateInfo template)
				yield break;

			var i = 0;
			for (var y = 0; y < template.Size.Y; y++)
			{
				for (var x = 0; x < template.Size.X; x++)
				{
					var tile = new TerrainTile(template.Id, (byte)i++);
					if (!terrainInfo.TryGetTileInfo(tile, out var tileInfo))
						continue;

					var sprite = tileCache.TileSprite(tile, 0);
					var offset = map.Offset(new CVec(x, y), tileInfo.Height);
					var palette = wr.Palette(template.Palette ?? terrainInfo.Palette);

					yield return new SpriteRenderable(sprite, origin, offset, 0, palette, tileCache.TileScale(tile), 1f, Vector3.One, TintModifiers.None, false);
				}
			}
		}

		IEnumerable<IRenderable> ITiledTerrainRenderer.RenderPreview(WorldRenderer wr, TerrainTile tile, WPos origin)
		{
			if (!terrainInfo.Templates.TryGetValue(tile.Type, out var template) || !template.Contains(tile.Index))
				yield break;

			var sprite = tileCache.TileSprite(tile, 0);
			var palette = wr.Palette(((CameoRemasterTerrainTemplateInfo)template)?.Palette ?? terrainInfo.Palette);

			yield return new SpriteRenderable(sprite, origin, WVec.Zero, 0, palette, tileCache.TileScale(tile), 1f, Vector3.One, TintModifiers.None, false);
		}
	}
}
