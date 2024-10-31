#region Copyright & License Information
/*
 * Copyright 2007-2018 The OpenRA Developers (see AUTHORS)
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System.Collections.Generic;
using System.Linq;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Shares cash across each team. Attach this to the world actor.")]
	public class CashTransferToAlliesInfo : TraitInfo, ILobbyOptions
	{
		[Desc("Duration between cash transfers.")]
		public readonly int ChargeDuration = 1;

		[Desc("Percentage value of the resource difference to send as cash when above the threshold.")]
		public readonly int ModifierAboveThreshold = 1;

		[Desc("Permillage value of the resource difference to send as cash when below the threshold.")]
		public readonly int ModifierBelowThreshold = 1;

		[Desc("Money Threshold for sending cash.")]
		public readonly int Threshold = 1000;

		[FluentReference]
		[Desc("Descriptive label for the creeps checkbox in the lobby.")]
		public readonly string CheckboxLabel = "Team Cash Sharing";

		[FluentReference]
		[Desc("Tooltip description for the creeps checkbox in the lobby.")]
		public readonly string CheckboxDescription = "Automatically share cash among teammates";

		[Desc("Default value of the creeps checkbox in the lobby.")]
		public readonly bool CheckboxEnabled = true;

		[Desc("Prevent the creeps state from being changed in the lobby.")]
		public readonly bool CheckboxLocked = false;

		[Desc("Whether to display the creeps checkbox in the lobby.")]
		public readonly bool CheckboxVisible = true;

		[Desc("Display order for the creeps checkbox in the lobby.")]
		public readonly int CheckboxDisplayOrder = 0;

		IEnumerable<LobbyOption> ILobbyOptions.LobbyOptions(MapPreview map)
		{
			yield return new LobbyBooleanOption(map, "cashtransfer", CheckboxLabel, CheckboxDescription, CheckboxVisible, CheckboxDisplayOrder, CheckboxEnabled, CheckboxLocked);
		}

		public override object Create(ActorInitializer init) { return new CashTransferToAllies(init.Self, this); }
	}

	class CashTransferToAllies : ITick, IWorldLoaded, INotifyCreated
	{
		readonly int[] modifierAboveThreshold;
		readonly int[] modifierBelowThreshold;
		readonly CashTransferToAlliesInfo info;
		int ticktime = 7500;
		int addedticks;
		public bool Enabled { get; private set; }

		[Sync]
		int ticks;

		Dictionary<int, List<PlayerResources>> teams;

		public CashTransferToAllies(Actor self, CashTransferToAlliesInfo info)
		{
			this.info = info;
			ticks = info.ChargeDuration;
			modifierAboveThreshold = new int[] { info.ModifierAboveThreshold };
			modifierBelowThreshold = new int[] { info.ModifierBelowThreshold };
		}

		void INotifyCreated.Created(Actor self)
		{
			Enabled = self.World.LobbyInfo.GlobalSettings
				.OptionOrDefault("cashtransfer", info.CheckboxEnabled);
		}

		void IWorldLoaded.WorldLoaded(World world, WorldRenderer wr)
		{
			if (!Enabled) return;

			teams = new Dictionary<int, List<PlayerResources>>();
			var playersToTeam = world.Players.Where(p => !p.NonCombatant && p.InternalName != "Everyone").ToList();

			// Console.WriteLine("Finding teams for " + playersToTeam.Count());

			int teamId = 0;
			while (playersToTeam.Count() > 0)
			{
				var currentTeam = new List<OpenRA.Player>();
				var firstTeam = playersToTeam[0];
				currentTeam.Add(firstTeam);
				playersToTeam.RemoveAt(0);

				for (int i = playersToTeam.Count - 1; i >= 0; i--)
				{
					bool isAllied = true;
					foreach (var player in currentTeam)
					{
						if (!player.IsAlliedWith(playersToTeam[i]))
						{
							isAllied = false;
							break;
						}
					}

					if (isAllied)
					{
						currentTeam.Add(playersToTeam[i]);
						playersToTeam.RemoveAt(i);
					}
				}

				if (currentTeam.Count() <= 1)
					continue;

				var currentTeamResources = new List<PlayerResources>();
				foreach (var player in currentTeam)
					currentTeamResources.Add(player.PlayerActor.Trait<PlayerResources>());

				// Console.WriteLine("Team assigned with " + currentTeam.Count() + "members");

				teams[teamId++] = currentTeamResources;
			}
		}

		void ITick.Tick(Actor self)
		{
			if (!Enabled)
			{
				return;
			}

			--ticktime;

			if (ticktime > 0)
			{
				addedticks = ticktime / 75;
			}
			else
			{
				addedticks = 0;
			}

			if (--ticks < 0)
			{
				ticks = info.ChargeDuration + addedticks;

				foreach (var team in teams.Values)
				{
					var teamTotal = 0;
					var playerMoney = 0;

					if (team.Count <= 1)
						continue;

					foreach (var playerResources in team)
					{
						playerMoney = playerResources.GetCashAndResources();

						if (playerMoney <= info.Threshold)
							playerMoney = Common.Util.ApplyPercentageModifiers(10 * playerMoney, modifierBelowThreshold);

						teamTotal += playerMoney;
					}

					var cashMean = teamTotal / team.Count;

					foreach (var playerResources in team)
					{
						playerMoney = playerResources.GetCashAndResources();

						if (playerMoney <= info.Threshold)
							playerMoney = Common.Util.ApplyPercentageModifiers(10 * playerMoney, modifierBelowThreshold);

						playerResources.ChangeCash(Common.Util.ApplyPercentageModifiers((cashMean - (playerMoney)), modifierAboveThreshold));
					}

				}
			}
		}
	}
}
