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
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Network;
using OpenRA.Traits;
using OpenRA.Widgets;

namespace OpenRA.Mods.Cameo.Widgets.Logic
{
	/// <summary>
	/// Bot types a player may pick in the lobby. A `ModularBot` with `HiddenInLobby: true` still exists (map-side
	/// bots, the A/B harness and scripts use it by type) but is not offered: the `fransbot` donor and the A/B
	/// reference bot `classic` (maintainer 2026-09-28). The engine's slot dropdown lists every IBotInfo and is a
	/// static method, so Cameo's lobby replaces only that dropdown with this filtered copy of
	/// LobbyUtils.ShowSlotDropDown.
	/// </summary>
	public static class CameoLobbyBots
	{
		[FluentReference]
		const string Open = "options-lobby-slot.open";

		[FluentReference]
		const string Closed = "options-lobby-slot.closed";

		[FluentReference]
		const string Bots = "options-lobby-slot.bots";

		[FluentReference]
		const string BotsDisabled = "options-lobby-slot.bots-disabled";

		[FluentReference]
		const string Slot = "options-lobby-slot.slot";

		public static bool ShownInLobby(IBotInfo bot) => bot is not ModularBotInfo modular || !modular.HiddenInLobby;

		public static IEnumerable<IBotInfo> Selectable(MapPreview map) => map.PlayerActorInfo.TraitInfos<IBotInfo>().Where(ShownInLobby);

		/// <summary>Call after LobbyUtils.SetupEditableSlotWidget: swaps its dropdown for the filtered one.</summary>
		public static void UseFilteredSlotDropDown(Widget parent, Session.Slot slot, Session.Client client, OrderManager orderManager, MapPreview map)
		{
			var dropdown = parent.GetOrNull<DropDownButtonWidget>("SLOT_OPTIONS");
			if (dropdown != null)
				dropdown.OnMouseDown = _ => ShowSlotDropDown(dropdown, slot, client, orderManager, map);
		}

		sealed record SlotDropDownOption(string Title, string Order, Func<bool> Selected);

		static void ShowSlotDropDown(DropDownButtonWidget dropdown, Session.Slot slot, Session.Client client, OrderManager orderManager, MapPreview map)
		{
			var options = new Dictionary<string, IEnumerable<SlotDropDownOption>>
			{
				{
					FluentProvider.GetMessage(Slot), new List<SlotDropDownOption>
					{
						new(FluentProvider.GetMessage(Open), "slot_open " + slot.PlayerReference, () => !slot.Closed && client == null),
						new(FluentProvider.GetMessage(Closed), "slot_close " + slot.PlayerReference, () => slot.Closed)
					}
				}
			};

			var bots = new List<SlotDropDownOption>();
			if (slot.AllowBots)
			{
				var botController = orderManager.LobbyInfo.Clients.FirstOrDefault(c => c.IsAdmin);
				foreach (var b in Selectable(map))
				{
					var bot = b;
					bots.Add(new SlotDropDownOption(map.GetMessage(bot.Name),
						$"slot_bot {slot.PlayerReference} {botController.Index} {bot.Type}",
						() => client != null && client.Bot == bot.Type));
				}
			}

			options.Add(bots.Count > 0 ? FluentProvider.GetMessage(Bots) : FluentProvider.GetMessage(BotsDisabled), bots);

			ScrollItemWidget SetupItem(SlotDropDownOption o, ScrollItemWidget itemTemplate)
			{
				var item = ScrollItemWidget.Setup(itemTemplate, o.Selected, () => orderManager.IssueOrder(Order.Command(o.Order)));
				item.Get<LabelWidget>("LABEL").GetText = () => o.Title;
				return item;
			}

			dropdown.ShowDropDown("LABEL_DROPDOWN_TEMPLATE", 180, options, SetupItem);
		}
	}
}
