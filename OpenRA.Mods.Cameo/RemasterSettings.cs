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

namespace OpenRA.Mods.Cameo
{
	[SettingsModule.YamlNode("Remaster")]
	public class RemasterSettings : SettingsModule
	{
		[Desc("Render Tiberian Dawn (and Red Alert) units with C&C Remastered Collection HD artwork.",
			"Requires the C&C Remastered Collection to be installed. Takes effect after restart.")]
		public bool UseRemasteredArt = false;
	}
}
