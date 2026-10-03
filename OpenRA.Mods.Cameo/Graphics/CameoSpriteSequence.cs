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
using OpenRA.Mods.Cameo.FileSystem;
using OpenRA.Mods.Cnc.Graphics;
using OpenRA.Mods.Common.Graphics;
using OpenRA.Mods.D2k.SpriteLoaders;
using OpenRA.Primitives;

namespace OpenRA.Mods.Cameo.Graphics
{
	// Applies an indexed mask to a remastered HD frame: only mask texels with a non-zero
	// index keep the inner sprite's data (used for player-colour / shadow regions).
	sealed class MaskedFrame : ISpriteFrame
	{
		readonly ISpriteFrame inner;
		readonly ISpriteFrame mask;
		byte[] data;

		public MaskedFrame(ISpriteFrame inner, ISpriteFrame mask)
		{
			this.inner = inner;
			this.mask = mask;
		}

		public SpriteFrameType Type => inner.Type;
		public Size Size => inner.Size;
		public Size FrameSize => inner.FrameSize;
		public Vector2 Offset => inner.Offset;
		public bool DisableExportPadding => inner.DisableExportPadding;

		public byte[] Data
		{
			get
			{
				if (data == null)
				{
					data = new byte[inner.Data.Length];

					var channels = inner.Data.Length / mask.Data.Length;
					for (var j = 0; j < mask.Data.Length; j++)
						if (mask.Data[j] != 0)
							for (var k = 0; k < channels; k++)
								data[j * channels + k] = inner.Data[j * channels + k];
				}

				return data;
			}
		}
	}

	public class CameoSpriteSequenceLoader : DefaultSpriteSequenceLoader
	{
		// Whether C&C Remastered HD art should be used. True only when the player opted in AND owns the
		// Collection (see RemasterContent.IsEnabled) - so a missing install leaves the game looking
		// exactly like classic. Read once at mod load.
		public readonly bool RemasterEnabled = RemasterContent.IsEnabled();

		public override ISpriteSequence CreateSequence(ModData modData, string tileSet, SpriteCache cache, string image, string sequence, MiniYaml data, MiniYaml defaults)
		{
			return new CameoSpriteSequence(cache, this, image, sequence, data, defaults, RemasterEnabled);
		}
	}

	[Desc("A sprite sequence that can have tileset-specific variants and optional C&C Remastered HD art.")]
	public class CameoSpriteSequence : ClassicSpriteSequence
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

		[Desc("File name of the remastered HD sprite to use for this sequence (loaded from the C&C Remastered Collection).")]
		static readonly SpriteSequenceField<string> RemasteredFilename = new(nameof(RemasteredFilename), null);

		[Desc("File name pattern to build the remastered HD sprite to use for this sequence.")]
		static readonly SpriteSequenceField<string> RemasteredFilenamePattern = new(nameof(RemasteredFilenamePattern), null);

		[Desc("File name of the sprite to mask the remastered HD sprite.")]
		static readonly SpriteSequenceField<string> RemasteredMaskFilename = new(nameof(RemasteredMaskFilename), null);

		[Desc("Change the position in-game on X, Y, Z for the remastered HD sprite.")]
		static readonly SpriteSequenceField<Vector3> RemasteredOffset = new(nameof(RemasteredOffset), Vector3.Zero);

		[Desc("Frame index to start from for the remastered HD sprite.")]
		static readonly SpriteSequenceField<int?> RemasteredStart = new(nameof(RemasteredStart), null);

		[Desc("Number of frames to use for the remastered HD sprite.")]
		static readonly SpriteSequenceField<int?> RemasteredLength = new(nameof(RemasteredLength), null);

		[Desc("Time (in milliseconds at default game speed) between frames for the remastered HD sprite.")]
		static readonly SpriteSequenceField<int?> RemasteredTick = new(nameof(RemasteredTick), null);

		[Desc("Adjusts the rendered size of the remastered HD sprite.")]
		static readonly SpriteSequenceField<float?> RemasteredScale = new(nameof(RemasteredScale), null);

		[Desc("Remastered HD sprite data is already pre-multiplied by alpha channel.")]
		static readonly SpriteSequenceField<bool> RemasteredPremultiplied = new(nameof(RemasteredPremultiplied), true);

		[Desc("Sets transparency for the remastered HD sprite - one value for all frames or one per frame.")]
		static readonly SpriteSequenceField<ImmutableArray<float>> RemasteredAlpha = new(nameof(RemasteredAlpha), default);

		readonly Color remapColor;
		readonly bool useShadow;
		readonly bool convertShroudToFog;

		readonly bool remasterEnabled;
		bool hasRemasteredSprite = true;

		public CameoSpriteSequence(SpriteCache cache, ISpriteSequenceLoader loader, string image, string sequence, MiniYaml data, MiniYaml defaults, bool remasterEnabled)
			: base(cache, loader, image, sequence, data, defaults)
		{
			remapColor = LoadField(Remap, data, defaults);
			useShadow = LoadField(UseShadow, data, defaults);
			convertShroudToFog = LoadField(ConvertShroudToFog, data, defaults);
			this.remasterEnabled = remasterEnabled;

			// When HD art is enabled, the remastered sheet may use a different frame layout,
			// timing, scale and transparency than the classic art - override the parsed values.
			if (remasterEnabled)
			{
				start = LoadField(RemasteredStart, data, defaults) ?? start;
				tick = LoadField(RemasteredTick, data, defaults) ?? tick;
				scale = LoadField(RemasteredScale, data, defaults) ?? scale;

				var remasteredAlpha = LoadField(RemasteredAlpha, data, defaults);
				if (remasteredAlpha != default)
					alpha = remasteredAlpha;

				if (LoadField<string>(RemasteredLength.Key, null, data, defaults) != "*")
					length = LoadField(RemasteredLength, data, defaults) ?? length;
				else
					length = null;
			}
		}

		public override void ReserveSprites(ModData modData, string tileset, SpriteCache cache, MiniYaml data, MiniYaml defaults)
		{
			var frames = LoadField(Frames, data, defaults);
			var flipX = LoadField(FlipX, data, defaults);
			var flipY = LoadField(FlipY, data, defaults);
			var zRamp = LoadField(ZRamp, data, defaults);
			var offset = LoadField(Offset, data, defaults);
			var blendMode = LoadField(BlendMode, data, defaults);

			// Classic player-colour remap / shroud-to-fog frame adjustment (R8 indexed frames).
			AdjustFrame remapAdjust = null;
			object remapCacheKey = null;
			if (remapColor != default || convertShroudToFog)
			{
				remapAdjust = RemapFrame;

				// Stable value-typed key so SpriteCachePool can recognise equivalent reservations across
				// map loads as cache hits. The delegate itself has a fresh Target every parse (captures useShadow,
				// convertShroudToFog, remapColor) and would never compare equal across sessions.
				remapCacheKey = (useShadow, convertShroudToFog, remapColor);
			}

			ISpriteFrame RemapFrame(ISpriteFrame f, int index, int total) =>
				(f is R8Loader.RemappableFrame rf) ? rf.WithSequenceFlags(useShadow, convertShroudToFog, remapColor) : f;

			// Remastered HD mask adjustment. Only consulted when the HD toggle is enabled and a mask is defined.
			var remasteredOffset = LoadField(RemasteredOffset, data, defaults);
			var premultiplied = LoadField(RemasteredPremultiplied, data, defaults);
			var remasteredMaskFilename = LoadField(RemasteredMaskFilename, data, defaults, out var remasteredMaskFilenameLocation);

			ISpriteFrame[] maskFrames = null;
			AdjustFrame maskAdjust = null;
			if (remasterEnabled && !string.IsNullOrEmpty(remasteredMaskFilename))
				maskAdjust = MaskFrame;

			ISpriteFrame MaskFrame(ISpriteFrame f, int index, int total)
			{
				if (maskFrames == null)
				{
					maskFrames = cache.LoadFramesUncached(remasteredMaskFilename);
					if (maskFrames == null)
						throw new FileNotFoundException($"{remasteredMaskFilenameLocation}: {remasteredMaskFilename} not found", remasteredMaskFilename);

					if (maskFrames.Length != total)
						throw new YamlException($"Sequence {image}.{Name} with {total} frames cannot use mask with {maskFrames.Length} frames.");
				}

				var m = maskFrames[index];
				if (f.Size != m.Size)
					throw new YamlException($"Sequence {image}.{Name} frame {index} with size {f.Size} cannot use mask with size {m.Size}.");

				if (m.Type != SpriteFrameType.Indexed8)
					throw new YamlException($"Sequence {image}.{Name} mask frame {index} must be an indexed image.");

				return new MaskedFrame(f, m);
			}

			var combineNode = data.NodeWithKeyOrDefault(Combine.Key);
			if (combineNode != null)
			{
				for (var i = 0; i < combineNode.Value.Nodes.Length; i++)
				{
					var subData = combineNode.Value.Nodes[i].Value;
					var subOffset = LoadField(Offset, subData, NoData);
					var remasteredSubOffset = LoadField(RemasteredOffset, subData, NoData);
					var subFlipX = LoadField(FlipX, subData, NoData);
					var subFlipY = LoadField(FlipY, subData, NoData);
					var subFrames = LoadField(Frames, subData);

					var reservations = remasterEnabled
						? ParseRemasterCombineFilenames(modData, tileset, subFrames, subData)
						: ParseCombineFilenames(modData, tileset, subFrames, subData);

					foreach (var f in reservations)
					{
						var useHd = remasterEnabled && hasRemasteredSprite;
						var token = cache.ReserveSprites(f.Filename, f.LoadFrames, f.Location,
							useHd ? maskAdjust : remapAdjust,
							useHd && premultiplied,
							useHd ? (object)remasteredMaskFilename : remapCacheKey);

						spritesToLoad.Add(new SpriteReservation
						{
							Token = token,
							Offset = useHd ? remasteredSubOffset + remasteredOffset : subOffset + offset,
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
				var reservations = remasterEnabled
					? ParseRemasterFilenames(modData, tileset, frames, data, defaults)
					: ParseFilenames(modData, tileset, frames, data, defaults);

				foreach (var f in reservations)
				{
					var useHd = remasterEnabled && hasRemasteredSprite;
					var token = cache.ReserveSprites(f.Filename, f.LoadFrames, f.Location,
						useHd ? maskAdjust : remapAdjust,
						useHd && premultiplied,
						useHd ? (object)remasteredMaskFilename : remapCacheKey);

					spritesToLoad.Add(new SpriteReservation
					{
						Token = token,
						Offset = useHd ? remasteredOffset : offset,
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
					var sprite = new Sprite(s.Sheet, FlipRectangle(s.Bounds, r.FlipX, r.FlipY), r.ZRamp, new Vector3(dx, dy, dz), s.Channel, r.BlendMode);
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
					alpha = Exts.MakeArray(length.Value, _ => alpha[0]).ToImmutableArray();
				else if (alpha.Length != length.Value)
					throw new YamlException($"Sequence {image}.{Name} must define either 1 or {length.Value} Alpha values.");
			}
			else if (alphaFade)
				alpha = Exts.MakeArray(length.Value, i => float.Lerp(1f, 0f, i / (length.Value - 1f))).ToImmutableArray();

			// Reindex sprites to order facings anti-clockwise and remove unused frames
			var index = CalculateFrameIndices(start, length.Value, stride ?? length.Value, facings, default, transpose, reverseFacings, -1);
			if (reverses)
			{
				index = index.AddRange(index.Skip(1).Take(length.Value - 2).Reverse());
				if (alpha != null)
					alpha = alpha.AddRange(alpha.Skip(1).Take(length.Value - 2).Reverse());

				length = 2 * length - 2;
			}

			if (index.Length == 0)
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

		protected override IEnumerable<ReservationInfo> ParseFilenames(ModData modData, string tileset, ImmutableArray<int> frames, MiniYaml data, MiniYaml defaults)
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
					return [new ReservationInfo(tilesetNode.Value.Value, loadFrames, frames, tilesetNode.Location)];
				}
			}

			return base.ParseFilenames(modData, tileset, frames, data, defaults);
		}

		protected override IEnumerable<ReservationInfo> ParseCombineFilenames(ModData modData, string tileset, ImmutableArray<int> frames, MiniYaml data)
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
						frames = Exts.MakeArray(subLength, i => subStart + i).ToImmutableArray();
					}

					return [new ReservationInfo(tilesetNode.Value.Value, frames, frames, tilesetNode.Location)];
				}
			}

			return base.ParseCombineFilenames(modData, tileset, frames, data);
		}

		// Picks the remastered HD sprite for this sequence; falls back to the classic art (and clears
		// hasRemasteredSprite) when no RemasteredFilename/Pattern is defined.
		IEnumerable<ReservationInfo> ParseRemasterFilenames(ModData modData, string tileset, ImmutableArray<int> frames, MiniYaml data, MiniYaml defaults)
		{
			var remasteredFilenamePatternNode = data.NodeWithKeyOrDefault(RemasteredFilenamePattern.Key)
				?? defaults.NodeWithKeyOrDefault(RemasteredFilenamePattern.Key);

			if (!string.IsNullOrEmpty(remasteredFilenamePatternNode?.Value.Value))
			{
				var patternStart = LoadField("Start", 0, remasteredFilenamePatternNode.Value);
				var patternCount = LoadField("Count", 1, remasteredFilenamePatternNode.Value);

				return Enumerable.Range(patternStart, patternCount).Select(i =>
					new ReservationInfo(remasteredFilenamePatternNode.Value.Value.FormatInvariant(i),
						FirstFrame, FirstFrame, remasteredFilenamePatternNode.Location));
			}

			var filename = LoadField(RemasteredFilename, data, defaults, out var location);
			if (filename != null)
			{
				// Only request the subset of frames that we actually need.
				var loadFrames = CalculateFrameIndices(start, length, stride ?? length ?? 0, facings, frames, transpose, reverseFacings, shadowStart);
				return [new ReservationInfo(filename, loadFrames, frames, location)];
			}

			hasRemasteredSprite = false;
			return ParseFilenames(modData, tileset, frames, data, defaults);
		}

		IEnumerable<ReservationInfo> ParseRemasterCombineFilenames(ModData modData, string tileset, ImmutableArray<int> frames, MiniYaml data)
		{
			var filename = LoadField(RemasteredFilename, data, null, out var location);
			if (frames == null && LoadField<string>("Length", null, data) != "*")
			{
				var subStart = LoadField("Start", 0, data);
				var subLength = LoadField("Length", 1, data);
				frames = Exts.MakeArray(subLength, i => subStart + i).ToImmutableArray();
			}

			if (filename != null)
				return [new ReservationInfo(filename, frames, frames, location)];

			hasRemasteredSprite = false;
			return ParseCombineFilenames(modData, tileset, frames, data);
		}
	}
}
