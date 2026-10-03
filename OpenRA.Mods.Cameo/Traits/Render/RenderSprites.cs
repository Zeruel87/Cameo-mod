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
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Graphics;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.Render
{
	[Desc("Marker injected into previews built for the lobby colour picker.",
		"Consumed by Cameo's RenderSpritesInfo shadow to select the live picker palette.")]
	public class ColorPickerPreviewInit : RuntimeFlagInit, ISingleInstanceInit { }

	[Desc("Cameo's sprite renderer fundament. Identical to the Common trait of the same name,",
		"except that previews created for ActorPreviewType.ColorPicker render through the LIVE",
		"colour-picker palette (the palette that follows the slider) instead of the owner-locked",
		"PlayerPalette. This makes any actor its own colour-picker preview: the manager can point",
		"at a faction's real construction yard and the preview recolours live, with no",
		".colorpicker clone actor and no Palette: override.",
		"",
		"⚠ THIS SHADOWS `OpenRA.Mods.Common.Traits.Render.RenderSpritesInfo` ON PURPOSE.",
		"ObjectCreator.FindType returns the FIRST assembly in mod.yaml's Assemblies list",
		"that has a type of the requested name, and the order there is",
		"AS, CA, Cameo, Cnc, D2k, Common — so Cameo wins and every `RenderSprites:` node",
		"gets this version with no yaml change at all. Cameo already does this for",
		"ColorPickerColorShift, PlayerColorShift and SelectionDecorations.")]
	public class RenderSpritesInfo : Common.Traits.Render.RenderSpritesInfo,
		IActorPreviewInitInfo, IRenderActorPreviewInfo
	{
		[Desc("Use the live colour-picker palette for ActorPreviewType.ColorPicker previews.",
			"Set false to get Common's original behaviour back (previews render through the",
			"world owner's fixed palette). This field also PROVES the shadowing works:",
			"Common's trait has no such field, so yaml naming it loads without an",
			"'unknown field' error only if the type resolved is this one.")]
		public readonly bool LiveColorPickerPreview = true;

		IEnumerable<ActorInit> IActorPreviewInitInfo.ActorPreviewInits(ActorInfo ai, ActorPreviewType type)
		{
			if (LiveColorPickerPreview && type == ActorPreviewType.ColorPicker)
				yield return new ColorPickerPreviewInit();
		}

		public new IEnumerable<IActorPreview> RenderPreview(ActorPreviewInitializer init)
		{
			var sequences = init.World.Map.Sequences;
			var faction = init.GetValue<FactionInit, string>(this);
			var ownerName = init.Get<OwnerInit>().InternalName;
			var image = GetImage(init.Actor, faction);
			var palette = init.WorldRenderer.Palette(PreviewPaletteName(init, ownerName));

			var facings = 0;
			var body = init.Actor.TraitInfoOrDefault<BodyOrientationInfo>();
			if (body != null)
			{
				facings = body.QuantizedFacings;

				if (facings == -1)
				{
					var qbo = init.Actor.TraitInfoOrDefault<IQuantizeBodyOrientationInfo>();
					facings = qbo?.QuantizedBodyFacings(init.Actor, sequences, faction) ?? 1;
				}
			}

			foreach (var spi in init.Actor.TraitInfos<Common.Traits.Render.IRenderActorPreviewSpritesInfo>())
				foreach (var preview in spi.RenderPreviewSprites(init, image, facings, palette))
					yield return preview;
		}

		string PreviewPaletteName(ActorPreviewInitializer init, string ownerName)
		{
			var normalPalette = Palette ?? PlayerPalette + ownerName;
			if (!init.Contains<ColorPickerPreviewInit>())
				return normalPalette;

			// The picker palette for the art family this actor renders through.
			// PlayerPalette is a PlayerColorPalette BaseName; its BasePalette names the raw
			// art palette (terrain, ra, ra2unit, ...). A ColorPickerPalette with the same
			// BasePalette is that family's live picker palette.
			var basePalette = Palette;
			if (basePalette == null)
				foreach (var p in init.World.WorldActor.Info.TraitInfos<PlayerColorPaletteInfo>())
					if (p.BaseName == PlayerPalette)
					{
						basePalette = p.BasePalette;
						break;
					}

			if (basePalette != null && TryGetPickerPalette(init, basePalette, out var pickerPalette))
				return pickerPalette;

			// No picker palette covers this art family — keep the normal palette rather
			// than failing the preview.
			return normalPalette;
		}

		static bool TryGetPickerPalette(ActorPreviewInitializer init, string basePalette, out string paletteName)
		{
			// ColorPickerPaletteInfo is internal to OpenRA.Mods.Common, so it is matched by
			// name and read via its public fields.
			foreach (var info in init.World.WorldActor.Info.TraitInfos<TraitInfo>())
			{
				var type = info.GetType();
				if (type.Name != "ColorPickerPaletteInfo")
					continue;

				var infoBase = type.GetField("BasePalette")?.GetValue(info) as string;
				if (infoBase == basePalette)
				{
					paletteName = type.GetField("Name")?.GetValue(info) as string;
					if (paletteName != null)
						return true;
				}
			}

			paletteName = null;
			return false;
		}
	}
}
