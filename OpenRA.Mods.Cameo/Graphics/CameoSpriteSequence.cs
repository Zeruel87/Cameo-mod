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
using OpenRA.Mods.Common.Graphics;
using OpenRA.Mods.D2k.SpriteLoaders;
using OpenRA.Primitives;

namespace OpenRA.Mods.Cameo.Graphics
{
	public class CameoSpriteSequenceLoader : DefaultSpriteSequenceLoader
	{
		public CameoSpriteSequenceLoader(ModData modData)
			: base(modData) { }

		public override ISpriteSequence CreateSequence(ModData modData, string tileSet, SpriteCache cache, string image, string sequence, MiniYaml data, MiniYaml defaults)
		{
			return new CameoSpriteSequence(cache, this, image, sequence, data, defaults);
		}
	}

	[Desc("A sprite sequence that can have tileset-specific variants.")]
	public class CameoSpriteSequence : DefaultSpriteSequence
	{
		[Desc("Sets the player remap reference colour.")]
		static readonly SpriteSequenceField<Color> Remap = new(nameof(Remap), default);

		[Desc("Remap embedded palette index 1 to shadow.")]
		static readonly SpriteSequenceField<bool> UseShadow = new(nameof(UseShadow), true);

		[Desc("Indicates that this is a fog sprite definition.")]
		static readonly SpriteSequenceField<bool> ConvertShroudToFog = new(nameof(ConvertShroudToFog), false);

		[Desc("Dictionary of <tileset name>: filename to override the Filename key.")]
		static readonly SpriteSequenceField<Dictionary<string, string>> TilesetFilenames = new(nameof(TilesetFilenames), null);

		[Desc("Dictionary of <tileset name>: <filename pattern> to override the FilenamePattern key.")]
		static readonly SpriteSequenceField<Dictionary<string, string>> TilesetFilenamesPattern = new(nameof(TilesetFilenamesPattern), null);

		readonly Color remapColor;
		readonly bool useShadow;
		readonly bool convertShroudToFog;

		public CameoSpriteSequence(SpriteCache cache, ISpriteSequenceLoader loader, string image, string sequence, MiniYaml data, MiniYaml defaults)
			: base(cache, loader, image, sequence, data, defaults)
		{
			remapColor = LoadField(Remap, data, defaults);
			useShadow = LoadField(UseShadow, data, defaults);
			convertShroudToFog = LoadField(ConvertShroudToFog, data, defaults);
		}

		public override void ReserveSprites(ModData modData, string tileset, SpriteCache cache, MiniYaml data, MiniYaml defaults)
		{
			var frames = LoadField(Frames, data, defaults);
			var flipX = LoadField(FlipX, data, defaults);
			var flipY = LoadField(FlipY, data, defaults);
			var zRamp = LoadField(ZRamp, data, defaults);
			var offset = LoadField(Offset, data, defaults);
			var blendMode = LoadField(BlendMode, data, defaults);

			AdjustFrame adjustFrame = null;
			if (remapColor != default || convertShroudToFog)
				adjustFrame = RemapFrame;

			ISpriteFrame RemapFrame (ISpriteFrame f, int index, int total) =>
				(f is R8Loader.RemappableFrame rf) ? rf.WithSequenceFlags(useShadow, convertShroudToFog, remapColor) : f;

			var combineNode = data.NodeWithKeyOrDefault(Combine.Key);
			if (combineNode != null)
			{
				for (var i = 0; i < combineNode.Value.Nodes.Length; i++)
				{
					var subData = combineNode.Value.Nodes[i].Value;
					var subOffset = LoadField(Offset, subData, NoData);
					var subFlipX = LoadField(FlipX, subData, NoData);
					var subFlipY = LoadField(FlipY, subData, NoData);
					var subFrames = LoadField(Frames, subData);

					foreach (var f in ParseCombineFilenames(modData, tileset, subFrames, subData))
					{
						var token = cache.ReserveSprites(f.Filename, f.LoadFrames, f.Location, adjustFrame);

						spritesToLoad.Add(new SpriteReservation
						{
							Token = token,
							Offset = subOffset + offset,
							FlipX = subFlipX ^ flipX,
							FlipY = subFlipY ^ flipY,
							BlendMode = blendMode,
							ZRamp = zRamp,
							Frames = f.Frames
						});
					}
				}
			}
			else
			{
				foreach (var f in ParseFilenames(modData, tileset, frames, data, defaults))
				{
					var token = cache.ReserveSprites(f.Filename, f.LoadFrames, f.Location, adjustFrame);

					spritesToLoad.Add(new SpriteReservation
					{
						Token = token,
						Offset = offset,
						FlipX = flipX,
						FlipY = flipY,
						BlendMode = blendMode,
						ZRamp = zRamp,
						Frames = f.Frames,
					});
				}
			}
		}

		public override void ResolveSprites(SpriteCache cache)
		{
			if (bounds != null)
				return;

			Sprite depthSprite = null;
			if (depthSpriteReservation != null)
				depthSprite = cache.ResolveSprites(depthSpriteReservation.Value).First(s => s != null);

			var allSprites = spritesToLoad.SelectMany(r =>
			{
				var resolved = cache.ResolveSprites(r.Token);

				if (r.Frames != null)
					resolved = r.Frames.Select(f => resolved[f]).ToArray();

				return resolved.Select(s =>
				{
					if (s == null)
						return null;

					var dx = r.Offset.X + (r.FlipX ? -s.Offset.X : s.Offset.X);
					var dy = r.Offset.Y + (r.FlipY ? -s.Offset.Y : s.Offset.Y);
					var dz = r.Offset.Z + s.Offset.Z + r.ZRamp * dy;
					var sprite = new Sprite(s.Sheet, FlipRectangle(s.Bounds, r.FlipX, r.FlipY), r.ZRamp, new float3(dx, dy, dz), s.Channel, r.BlendMode);
					if (depthSprite == null)
						return sprite;

					var cw = (depthSprite.Bounds.Left + depthSprite.Bounds.Right) / 2 + (int)(s.Offset.X + depthSpriteOffset.X);
					var ch = (depthSprite.Bounds.Top + depthSprite.Bounds.Bottom) / 2 + (int)(s.Offset.Y + depthSpriteOffset.Y);
					var w = s.Bounds.Width / 2;
					var h = s.Bounds.Height / 2;

					return new SpriteWithSecondaryData(sprite, depthSprite.Sheet, Rectangle.FromLTRB(cw - w, ch - h, cw + w, ch + h), depthSprite.Channel);
				});
			}).ToArray();

			length ??= allSprites.Length - start;

			if (alpha != null)
			{
				if (alpha.Length == 1)
					alpha = Exts.MakeArray(length.Value, _ => alpha[0]);
				else if (alpha.Length != length.Value)
					throw new YamlException($"Sequence {image}.{Name} must define either 1 or {length.Value} Alpha values.");
			}
			else if (alphaFade)
				alpha = Exts.MakeArray(length.Value, i => float2.Lerp(1f, 0f, i / (length.Value - 1f)));

			// Reindex sprites to order facings anti-clockwise and remove unused frames
			var index = CalculateFrameIndices(start, length.Value, stride ?? length.Value, facings, null, transpose, reverseFacings, -1);
			if (reverses)
			{
				index.AddRange(index.Skip(1).Take(length.Value - 2).Reverse());
				length = 2 * length - 2;
			}

			if (index.Count == 0)
				throw new YamlException($"Sequence {image}.{Name} does not define any frames.");

			var minIndex = index.Min();
			var maxIndex = index.Max();
			if (minIndex < 0 || maxIndex >= allSprites.Length)
				throw new YamlException($"Sequence {image}.{Name} uses frames between {minIndex}..{maxIndex}, but only 0..{allSprites.Length - 1} exist.");

			sprites = index.Select(f => allSprites[f]).ToArray();
			if (shadowStart >= 0)
				shadowSprites = index.Select(f => allSprites[f - start + shadowStart]).ToArray();

			bounds = sprites.Concat(shadowSprites ?? Enumerable.Empty<Sprite>()).Select(OffsetSpriteBounds).Union();
		}

		protected override IEnumerable<ReservationInfo> ParseFilenames(ModData modData, string tileset, int[] frames, MiniYaml data, MiniYaml defaults)
		{
			var tilesetFilenamesPatternNode = data.NodeWithKeyOrDefault(TilesetFilenamesPattern.Key) ?? defaults.NodeWithKeyOrDefault(TilesetFilenamesPattern.Key);
			if (tilesetFilenamesPatternNode != null)
			{
				var tilesetNode = tilesetFilenamesPatternNode.Value.NodeWithKeyOrDefault(tileset);
				if (tilesetNode != null)
				{
					var patternStart = LoadField("Start", 0, tilesetNode.Value);
					var patternCount = LoadField("Count", 1, tilesetNode.Value);

					return Enumerable.Range(patternStart, patternCount).Select(i =>
						new ReservationInfo(tilesetNode.Value.Value.FormatInvariant(i), FirstFrame, FirstFrame, tilesetNode.Location));
				}
			}

			var node = data.NodeWithKeyOrDefault(TilesetFilenames.Key) ?? defaults.NodeWithKeyOrDefault(TilesetFilenames.Key);
			if (node != null)
			{
				var tilesetNode = node.Value.NodeWithKeyOrDefault(tileset);
				if (tilesetNode != null)
				{
					var loadFrames = CalculateFrameIndices(start, length, stride ?? length ?? 0, facings, frames, transpose, reverseFacings, shadowStart);
					return new[] { new ReservationInfo(tilesetNode.Value.Value, loadFrames, frames, tilesetNode.Location) };
				}
			}

			return base.ParseFilenames(modData, tileset, frames, data, defaults);
		}

		protected override IEnumerable<ReservationInfo> ParseCombineFilenames(ModData modData, string tileset, int[] frames, MiniYaml data)
		{
			var node = data.NodeWithKeyOrDefault(TilesetFilenames.Key);
			if (node != null)
			{
				var tilesetNode = node.Value.NodeWithKeyOrDefault(tileset);
				if (tilesetNode != null)
				{
					if (frames == null && LoadField<string>("Length", null, data) != "*")
					{
						var subStart = LoadField("Start", 0, data);
						var subLength = LoadField("Length", 1, data);
						frames = Exts.MakeArray(subLength, i => subStart + i);
					}

					return new[] { new ReservationInfo(tilesetNode.Value.Value, frames, frames, tilesetNode.Location) };
				}
			}

			return base.ParseCombineFilenames(modData, tileset, frames, data);
		}
	}
}
