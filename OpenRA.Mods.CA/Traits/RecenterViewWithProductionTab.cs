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

using OpenRA.Traits;
using OpenRA.Mods.Common.Traits;

namespace OpenRA.Mods.CA.Traits
{
	[Desc("Tag trait for instantly placed buildings.")]
	public class RecenterViewWithProductionTabInfo : TraitInfo<RecenterViewWithProductionTab>, Requires<IOccupySpaceInfo> { }
	public class RecenterViewWithProductionTab { }
}
