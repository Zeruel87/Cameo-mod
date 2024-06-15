#region Copyright & License Information
/*
 * Copyright 2007-2022 The OpenRA Developers (see AUTHORS)
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using OpenRA.Graphics;
using OpenRA.Mods.Common.Orders;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Network;
using OpenRA.Widgets;

namespace OpenRA.Mods.CA.Widgets
{
	public class ProductionPaletteCAWidget : ProductionPaletteWidget
	{
		public string Cursor = ChromeMetrics.Get<string>("ButtonCursor");

		readonly WorldRenderer worldRenderer;

		[ObjectCreator.UseCtor]
		public ProductionPaletteCAWidget(ModData modData, OrderManager orderManager, World world, WorldRenderer worldRenderer)
			: base(modData, orderManager, world, worldRenderer) {
			this.worldRenderer = worldRenderer;
		}

		public override string GetCursor(int2 pos)
		{
			return Cursor;
		}

		public new void PickUpCompletedBuilding()
		{
			var item = CurrentQueue.CurrentItem();
			if (item == null) return; 
			PickUpCompletedBuildingIcon(item);
		}

		protected bool PickUpCompletedBuildingIcon(ProductionItem item)
		{
			var actor = World.Map.Rules.Actors[item.Item];

			if (item != null && item.Done && actor.HasTraitInfo<BuildingInfo>())
			{
				World.OrderGenerator = new PlaceBuildingOrderGenerator(CurrentQueue, item.Item, worldRenderer);
				return true;
			}
			return false;
		}
	}
}
