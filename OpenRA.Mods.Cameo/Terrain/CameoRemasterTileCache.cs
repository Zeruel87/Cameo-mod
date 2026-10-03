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
using System.Collections.Immutable;
using System.IO;
using System.Linq;
using System.Numerics;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Terrain;
using OpenRA.Primitives;
using OpenRA.Support;

namespace OpenRA.Mods.Cameo.Terrain
{
	// A fork of DefaultTileCache. The classic sprite-building path is preserved verbatim (variants,
	// Frames, depth, IgnoreTileSpriteOffsets) so non-HD terrain is byte-identical. When the HD toggle
	// is on and a template defines RemasteredFilenames, the HD DDS tiles are loaded instead and the
	// per-template render scale is derived so the HD sprite fits the classic cell size.
	public sealed class CameoRemasterTileCache : IDisposable
	{
		readonly Cache<SheetType, SheetBuilder> sheetBuilders;
		readonly Dictionary<ushort, TheaterTemplate> templates = [];
		readonly Dictionary<ushort, float> scale = [];
		readonly MersenneTwister random;

		public Sprite MissingTile { get; }

		public CameoRemasterTileCache(CameoRemasterTerrain terrainInfo, Action<uint, string> onMissingImage = null)
		{
			sheetBuilders = new Cache<SheetType, SheetBuilder>(t =>
				new SheetBuilder(t, t == SheetType.BGRA ? terrainInfo.BgraSheetSize : terrainInfo.SheetSize));

			random = new MersenneTwister();

			var frameCache = new FrameCache(Game.ModData.DefaultFileSystem, Game.ModData.SpriteLoaders);
			foreach (var t in terrainInfo.Templates)
			{
				var templateInfo = (CameoRemasterTerrainTemplateInfo)t.Value;

				// HD path: explicit RemasteredFilenames, or auto-derived from RemasteredFolder + Images.
				// Returns null when this template has no usable HD art, so we fall through to classic.
				if (terrainInfo.UseRemasteredTerrain)
				{
					var tileCount = t.Value.TilesCount;
					var hdPaths = ResolveRemasterPaths(terrainInfo, templateInfo, tileCount);
					if (hdPaths != null)
					{
						var hdSprites = new Sprite[tileCount];
						var nativeWidth = 0;

						for (var i = 0; i < tileCount; i++)
						{
							var path = hdPaths[i];
							if (path == null)
								continue;

							ISpriteFrame[] frames;
							if (onMissingImage != null)
							{
								try { frames = frameCache[path]; }
								catch (FileNotFoundException) { onMissingImage(t.Key, path); continue; }
							}
							else
								frames = frameCache[path];

							var f = frames[0];
							var type = SheetBuilder.FrameTypeToSheetType(f.Type);
							var s = sheetBuilders[type].Allocate(f.Size, 1f, new Vector3(f.Offset, 0));
							OpenRA.Graphics.Util.FastCopyIntoChannel(s, f.Data, f.Type);
							hdSprites[i] = s;
							if (nativeWidth == 0)
								nativeWidth = f.Size.Width;
						}

						if (nativeWidth > 0)
						{
							templates.Add(t.Value.Id, new TheaterTemplate(hdSprites, tileCount, 1));
							scale[t.Value.Id] = (float)terrainInfo.TileSize.Width / nativeWidth;
							continue;
						}
					}
				}

				// Classic path - identical to DefaultTileCache.
				var variants = new List<Sprite[]>();

				for (var ii = 0; ii < templateInfo.Images.Length; ii++)
				{
					var i = templateInfo.Images[ii];

					ISpriteFrame[] allFrames;
					ISpriteFrame[] depthFrames = null;

					if (onMissingImage != null)
					{
						try
						{
							allFrames = frameCache[i];
						}
						catch (FileNotFoundException)
						{
							onMissingImage(t.Key, i);
							continue;
						}
					}
					else
						allFrames = frameCache[i];

					if (terrainInfo.EnableDepth && templateInfo.DepthImages != null && templateInfo.DepthImages.Length == templateInfo.Images.Length)
					{
						var di = templateInfo.DepthImages[ii];
						if (onMissingImage != null)
						{
							try
							{
								depthFrames = frameCache[di];
							}
							catch (FileNotFoundException)
							{
								onMissingImage(t.Key, di);
								continue;
							}
						}
						else
							depthFrames = frameCache[di];
					}

					var frameCount = terrainInfo.EnableDepth && depthFrames == null ? allFrames.Length / 2 : allFrames.Length;
					var indices = templateInfo.Frames != null ? templateInfo.Frames : Exts.MakeArray(t.Value.TilesCount, j => j).ToImmutableArray();

					var start = indices.Min();
					var end = indices.Max();
					if (start < 0 || end >= frameCount)
						throw new YamlException($"Template `{t.Key}` uses frames [{start}..{end}] of {i}, but only [0..{frameCount - 1}] actually exist");

					variants.Add(indices.Select(j =>
					{
						var f = allFrames[j];
						var tile = t.Value.Contains(j) ? (DefaultTerrainTileInfo)t.Value[j] : null;

						// The internal z axis is inverted from expectation (negative is closer)
						var zOffset = tile != null ? -tile.ZOffset : 0;
						var zRamp = tile != null ? tile.ZRamp : 1f;
						var offset = new Vector3(f.Offset, zOffset);
						var type = SheetBuilder.FrameTypeToSheetType(f.Type);

						var s = sheetBuilders[type].Allocate(f.Size, zRamp, offset);
						OpenRA.Graphics.Util.FastCopyIntoChannel(s, f.Data, f.Type);

						if (terrainInfo.EnableDepth)
						{
							var depthFrame = depthFrames != null ? depthFrames[j] : allFrames[j + frameCount];
							var depthType = SheetBuilder.FrameTypeToSheetType(depthFrame.Type);
							var ss = sheetBuilders[depthType].Allocate(depthFrame.Size, zRamp, offset);
							OpenRA.Graphics.Util.FastCopyIntoChannel(ss, depthFrame.Data, depthFrame.Type);
							s = new SpriteWithSecondaryData(s, ss.Sheet, ss.Bounds, ss.Channel);
						}

						return s;
					}).ToArray());
				}

				var allSprites = variants.SelectMany(s => s);

				// Ignore the offsets baked into R8 sprites
				if (terrainInfo.IgnoreTileSpriteOffsets)
					allSprites = allSprites.Select(s => new Sprite(s.Sheet, s.Bounds, s.ZRamp, new Vector3(Vector2.Zero, s.Offset.Z), s.Channel, s.BlendMode));

				if (onMissingImage != null && variants.Count == 0)
					continue;

				templates.Add(t.Value.Id, new TheaterTemplate(allSprites.ToArray(), variants[0].Length, templateInfo.Images.Length));
				scale[t.Value.Id] = 1f;
			}

			// 1x1px transparent tile
			var missingDataLength = 1;
			var missingFrameType = SpriteFrameType.Indexed8;
			var missingSheetType = SheetType.Indexed;

			// Avoid creating an indexed sheet if all tiles are BGRA
			var missing = sheetBuilders.FirstOrDefault();
			if (missing.Value != null && missing.Key == SheetType.BGRA)
			{
				missingDataLength = 4;
				missingFrameType = SpriteFrameType.Bgra32;
				missingSheetType = SheetType.BGRA;
			}

			MissingTile = sheetBuilders[missingSheetType].Add(new byte[missingDataLength], missingFrameType, new Size(1, 1));
			foreach (var sb in sheetBuilders.Values)
				sb.Current?.ReleaseBuffer();
		}

		// Resolves the HD DDS path for each tile index of a template, or null if the template has no
		// usable HD art (so the caller falls back to the classic sprites). Explicit RemasteredFilenames
		// win; otherwise paths are derived by convention from RemasteredFolder + the template's Images,
		// and the whole template stays classic unless every derived tile exists in the mounted packages.
		static string[] ResolveRemasterPaths(CameoRemasterTerrain terrainInfo, CameoRemasterTerrainTemplateInfo templateInfo, int tileCount)
		{
			var paths = new string[tileCount];

			if (templateInfo.RemasteredFilenames != null)
			{
				var any = false;
				foreach (var kv in templateInfo.RemasteredFilenames)
				{
					if (kv.Key < 0 || kv.Key >= tileCount || kv.Value.Length == 0)
						continue;

					// Animated tiles list multiple frames; we render the first (static) frame.
					paths[kv.Key] = kv.Value[0];
					any = true;
				}

				return any ? paths : null;
			}

			if (string.IsNullOrEmpty(terrainInfo.RemasteredFolder) || templateInfo.Images.Length == 0)
				return null;

			// The HD file prefix is always the full classic filename, e.g. "clear1.win" -> "CLEAR1.WIN".
			var image = templateInfo.Images[0];
			var prefix = Path.GetFileName(image).ToUpperInvariant();
			var folderWithExt = prefix;
			var folderNoExt = Path.GetFileNameWithoutExtension(image).ToUpperInvariant();
			var fileSystem = Game.ModData.DefaultFileSystem;

			// Only the tile indices the template actually defines have HD art in the meg. Cells implied
			// by Size but absent from Tiles (common in irregular cliff/shore templates, e.g. desert s14
			// is 2x2 but only defines tiles 0-2) are never exported, so requiring them would wrongly drop
			// the whole template to classic - the visible cause of HD cliffs not blending with neighbours.
			var firstDefined = -1;
			for (var i = 0; i < tileCount; i++)
			{
				if (templateInfo.Contains(i))
				{
					firstDefined = i;
					break;
				}
			}

			if (firstDefined < 0)
				return null;

			// The containing folder name is INCONSISTENT across tilesets in the Remastered meg: TEMPERATE
			// strips the extension (CLEAR1\CLEAR1.TEM-0000.DDS) while DESERT/WINTER/RA keep it
			// (CLEAR1.WIN\CLEAR1.WIN-0000.DDS). Probe both forms using the first defined tile.
			string folder = null;
			foreach (var candidate in new[] { folderWithExt, folderNoExt })
			{
				if (fileSystem.Exists($"{terrainInfo.RemasteredFolder}\\{candidate}\\{prefix}-{firstDefined:0000}.DDS"))
				{
					folder = candidate;
					break;
				}
			}

			if (folder == null)
				return null;

			for (var i = 0; i < tileCount; i++)
			{
				// Skip cells the template doesn't use - they have no HD frame and are never placed
				// (TileSprite returns MissingTile for the null slot).
				if (!templateInfo.Contains(i))
					continue;

				var path = $"{terrainInfo.RemasteredFolder}\\{folder}\\{prefix}-{i:0000}.DDS";

				// A defined tile missing its HD art -> keep the whole template classic, avoiding
				// mismatched tiles within one template (e.g. animated water or partial custom SHPs).
				if (!fileSystem.Exists(path))
					return null;

				paths[i] = path;
			}

			return paths;
		}

		public bool HasTileSprite(TerrainTile r, int? variant = null)
		{
			return TileSprite(r, variant) != MissingTile;
		}

		public Sprite TileSprite(TerrainTile r, int? variant = null)
		{
			if (!templates.TryGetValue(r.Type, out var template))
				return MissingTile;

			if (r.Index >= template.Stride)
				return MissingTile;

			var start = template.Variants > 1 ? variant ?? random.Next(template.Variants) : 0;
			return template.Sprites[start * template.Stride + r.Index] ?? MissingTile;
		}

		public float TileScale(TerrainTile r)
		{
			return scale.TryGetValue(r.Type, out var s) ? s : 1f;
		}

		public SheetBuilder GetSheetBuilder(SheetType sheetType)
		{
			return sheetBuilders[sheetType];
		}

		public void Dispose()
		{
			foreach (var sb in sheetBuilders.Values)
				sb.Dispose();
		}
	}
}
