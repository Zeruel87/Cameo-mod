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

using OpenRA.Mods.Cameo.FileSystem;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Mods.Common.Widgets.Logic;
using OpenRA.Widgets;

namespace OpenRA.Mods.Cameo.Widgets.Logic
{
	// Binds the "C&C Remastered HD Art" checkbox in the Display settings panel to RemasterSettings.
	// Added as a second Logic on the panel so it works without modifying the engine's DisplaySettingsLogic.
	// The checkbox is disabled when the Remastered Collection isn't installed, so it can only be turned
	// on when the HD assets are actually available.
	public class CameoRemasterDisplaySettingsLogic : ChromeLogic
	{
		[ObjectCreator.UseCtor]
		public CameoRemasterDisplaySettingsLogic(Widget widget)
		{
			var checkbox = widget.GetOrNull<CheckboxWidget>("REMASTER_ART_CHECKBOX");
			if (checkbox == null)
				return;

			var settings = Game.Settings.GetOrCreate<RemasterSettings>(null);
			SettingsUtils.BindCheckboxPref(widget, "REMASTER_ART_CHECKBOX", settings, nameof(RemasterSettings.UseRemasteredArt));

			// Only allow opting in when the Collection is actually installed; the bound value is still
			// persisted on Save like every other settings checkbox.
			var installed = RemasterContent.TryFindDataDir(out _);
			checkbox.IsDisabled = () => !installed;
		}
	}
}
