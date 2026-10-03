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
using System.Collections.Frozen;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Graphics;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Primitives;
using OpenRA.Traits;
using OpenRA.Widgets;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.World)]
	[Desc("Cameo's colour picker manager. Identical to the Common trait of the same name,",
		"except that a faction's preview actor is DERIVED from rules data when it is not",
		"listed in FactionPreviewActors: the faction's StartingUnits BaseActor (its MCV) is",
		"followed through Transforms.IntoActor to the construction yard. Combined with the",
		"RenderSprites shadow (which recolours ColorPicker previews live), every faction",
		"previews its own real conyard in the picked colour — no clone actors, no",
		"hand-maintained faction table. Yaml FactionPreviewActors entries still win, and",
		"PreviewActor remains the fallback for Random/unknown factions.",
		"",
		"⚠ THIS SHADOWS `OpenRA.Mods.Common.Traits.ColorPickerManagerInfo` ON PURPOSE.",
		"ObjectCreator.FindType returns the FIRST assembly in mod.yaml's Assemblies list",
		"that has a type of the requested name, and the order there is",
		"AS, CA, Cameo, Cnc, D2k, Common — so Cameo wins. Cameo already does this for",
		"ColorPickerColorShift, PlayerColorShift, SelectionDecorations and RenderSprites.",
		"",
		"⚠ The event is re-declared (`new`) on purpose: the base class's explicit interface",
		"implementations are not virtual, so this class re-declares IColorPickerManagerInfo",
		"to give ShowColorDropDown the derived-actor lookup — and once the interface is",
		"re-declared, its event member must resolve to an event this class can raise, which",
		"only the local one is. Subscribers (ColorPickerPalette) attach through",
		"IColorPickerManagerInfo, so they land on this event.")]
	public class ColorPickerManagerInfo : Common.Traits.ColorPickerManagerInfo, IColorPickerManagerInfo
	{
		[Desc("Derive each selectable faction's colour-picker preview actor from its",
			"StartingUnits BaseActor -> Transforms.IntoActor chain instead of requiring a",
			"yaml FactionPreviewActors row. Set false to get Common's original behaviour",
			"(yaml table only). This field also PROVES the shadowing works: Common's trait",
			"has no such field, so yaml naming it loads without an 'unknown field' error",
			"only if the type resolved is this one.")]
		public readonly bool DeriveFactionPreviewActors = true;

		public new event Action<Color> OnColorPickerColorUpdate;

		World derivedPreviewsWorld;
		FrozenDictionary<string, string> derivedPreviews;

		FrozenDictionary<string, string> DerivedPreviewActors(global::OpenRA.World world)
		{
			if (derivedPreviews != null && ReferenceEquals(derivedPreviewsWorld, world))
				return derivedPreviews;

			var worldInfo = world.WorldActor.Info;
			var rules = world.Map.Rules;

			// faction internal name -> the faction's StartingUnits BaseActor (its MCV)
			var mcvByFaction = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
			foreach (var su in worldInfo.TraitInfos<StartingUnitsInfo>())
			{
				if (su.BaseActor == null)
					continue;

				foreach (var faction in su.Factions)
					mcvByFaction[faction] = su.BaseActor;
			}

			var map = new Dictionary<string, string>();
			foreach (var faction in worldInfo.TraitInfos<FactionInfo>())
			{
				if (!faction.Selectable || faction.InternalName == null)
					continue;

				if (!mcvByFaction.TryGetValue(faction.InternalName, out var baseActor))
					continue;

				if (!rules.Actors.TryGetValue(baseActor.ToLowerInvariant(), out var baseActorInfo))
					continue;

				// The MCV deploys into the construction yard. If it cannot transform
				// (unusual), preview the MCV itself — still faction-correct art.
				var previewName = baseActorInfo.TraitInfoOrDefault<TransformsInfo>()?.IntoActor ?? baseActor;
				if (rules.Actors.ContainsKey(previewName.ToLowerInvariant()))
					map[faction.InternalName] = previewName;
			}

			derivedPreviewsWorld = world;
			derivedPreviews = map.ToFrozenDictionary();
			return derivedPreviews;
		}

		string PreviewActorType(global::OpenRA.World world, string faction)
		{
			if (faction != null && FactionPreviewActors.TryGetValue(faction, out var actorType))
				return actorType;

			if (DeriveFactionPreviewActors && faction != null &&
				DerivedPreviewActors(world).TryGetValue(faction, out actorType))
				return actorType;

			return PreviewActor;
		}

		void IColorPickerManagerInfo.ShowColorDropDown(
			DropDownButtonWidget dropdownButton,
			Color initialColor,
			string initialFaction,
			WorldRenderer worldRenderer,
			Action<Color> onExit)
		{
			dropdownButton.RemovePanel();

			// We do not want to force other ColorPickerManager implementations to have an Actor preview.
			// We achieve this by fully encapsulating its initialisation.
			void AddActorPreview(Widget parent)
			{
				var preview = parent.GetOrNull<ActorPreviewWidget>("PREVIEW");
				if (preview == null)
					return;

				var actorType = PreviewActorType(worldRenderer.World, initialFaction);
				if (actorType == null)
					throw new YamlException(
						$"{nameof(ColorPickerManagerInfo)} does not define a preview actor" +
						(initialFaction == null ? "." : $" for faction {initialFaction}."));

				var actor = worldRenderer.World.Map.Rules.Actors[actorType.ToLowerInvariant()];

				var td = new TypeDictionary
				{
					new OwnerInit(worldRenderer.World.WorldActor.Owner),
					new FactionInit(worldRenderer.World.WorldActor.Owner.PlayerReference.Faction)
				};

				foreach (var api in actor.TraitInfos<IActorPreviewInitInfo>())
					foreach (var o in api.ActorPreviewInits(actor, ActorPreviewType.ColorPicker))
						td.Add(o);

				preview.SetPreview(actor, td);
			}

			var finalColor = initialColor;
			var colorChooser = Game.LoadWidget(worldRenderer.World, "COLOR_CHOOSER", null, new WidgetArgs()
			{
				{ "onChange", (Action<Color>)(c => { finalColor = c; OnColorPickerColorUpdate?.Invoke(c); }) },
				{ "initialColor", initialColor },
				{ "extraLogic", (Action<Widget>)AddActorPreview },
			});

			dropdownButton.AttachPanel(colorChooser, () => onExit(finalColor));
		}
	}
}
