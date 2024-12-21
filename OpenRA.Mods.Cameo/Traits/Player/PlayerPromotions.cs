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
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[TraitLocation(SystemActors.Player)]
	[Desc("Tracks player experience and grants points based on levels.")]
	public class PlayerPromotionsInfo : TraitInfo, ILobbyOptions
	{
		[FieldLoader.Require]
		[Desc("Condition to grant at each level.",
			"Key is the XP requirements for each level as a percentage of our own value.",
			"Value is the condition to grant.")]
		public readonly Dictionary<int, string> Conditions = null;

		[GrantedConditionReference]
		[Desc("Condition to grant when has points.")]
		public readonly string HasPointsCondition = null;

		[GrantedConditionReference]
		public IEnumerable<string> LinterConditions => Conditions.Values;

		[Desc("Image for the level up sprite.")]
		public readonly string LevelUpImage = null;

		[NotificationReference("Sounds")]
		public readonly string NotificationType = "Sounds";

		[NotificationReference("Sounds")]
		public readonly string LevelUpNotification = null;

		[FluentReference(optional: true)]
		public readonly string LevelUpTextNotification = null;

		[Desc("A dictionary of ranks for each faction.")]
		public readonly Dictionary<string, List<string>> Ranks = null;

		[FieldLoader.Require]
		[Desc("Default rank set key.")]
		public readonly string RanksDefault = "default";

		[FieldLoader.Require]
		[Desc("Points per rank options that are available in the lobby options.")]
		public readonly Dictionary<string, List<int>> PointsPerRank = null;

		[FieldLoader.Require]
		[Desc("Internal id for this option.")]
		public readonly string ID = "promotions";

		[FieldLoader.Require]
		[FluentReference]
		[Desc("Descriptive label for this option.")]
		public readonly string Label = null;

		[FluentReference]
		[Desc("Tooltip description for this option.")]
		public readonly string Description = null;

		[FieldLoader.Require]
		[Desc("Default option key in the `Values` list.")]
		public readonly string PointsPerRankDefault = null;

		[FluentReference]
		public readonly string[] FlavorTextNotifications = null;

		[FluentReference]
		public readonly string FlavorTextPrefix = null;

		[Desc("Prevent the option from being changed from its default value.")]
		public readonly bool Locked = false;

		[Desc("Whether to display the option in the lobby.")]
		public readonly bool Visible = true;

		[Desc("Display order for the option in the lobby.")]
		public readonly int DisplayOrder = 0;

		IEnumerable<LobbyOption> ILobbyOptions.LobbyOptions(MapPreview map)
		{
			var startingPoints = PointsPerRank.ToDictionary(p => p.Key, p => string.Join(", ", p.Value));

			yield return new LobbyOption(map, ID, Label, Description, Visible, DisplayOrder,
				startingPoints, PointsPerRankDefault, Locked);
		}

		public override object Create(ActorInitializer init) { return new PlayerPromotions(init, this); }
	}

	public class PlayerPromotions : INotifyCreated, ISync, INotifyPlayerExperience
	{
		readonly Actor self;
		readonly PlayerPromotionsInfo Info;

		[Sync]
		public int Experience { get; private set; }

		[Sync]
		public int Points;

		List<int> PointsPerRank;
		List<string> Ranks;
		public string currentRank;

		readonly List<(int RequiredExperience, string Condition)> nextLevel = new();

		readonly int MaxLevel;
		public int currentLevel;
		public bool IsMaxLevel;
		public int nextLevelXpRequired;

		int hasPointsToken = Actor.InvalidConditionToken;

		public PlayerPromotions(ActorInitializer init, PlayerPromotionsInfo Info)
		{
			self = init.Self;
			this.Info = Info;
			Experience = 0;
			MaxLevel = Info.Conditions.Count;

			foreach (var kv in Info.Conditions)
				nextLevel.Add((kv.Key, kv.Value ?? null));
		}

		void INotifyCreated.Created(Actor self)
		{
			var pointsOption = self.World.LobbyInfo.GlobalSettings.OptionOrDefault(Info.ID, Info.PointsPerRankDefault);
			PointsPerRank = Info.PointsPerRank[pointsOption];

			var faction = self.Owner.Faction.InternalName;
			if (Info.Ranks.ContainsKey(faction))
				Ranks = Info.Ranks[faction];
			else
				Ranks = Info.Ranks[Info.RanksDefault];

			for (int i = 0; i < Ranks.Count; ++i)
				Ranks[i] = FluentProvider.GetMessage(Ranks[i]);

			LevelUp();
		}

		void INotifyPlayerExperience.OnGainsExperience(OpenRA.Actor player, int exp)
		{
			Experience += exp;
			while (currentLevel < MaxLevel && Experience >= nextLevel[currentLevel].RequiredExperience)
			{
				LevelUp();
			}
		}

		void LevelUp()
		{
			currentLevel++;

			PromoteToRank(currentLevel);

			Game.Sound.PlayNotification(self.World.Map.Rules, self.Owner, Info.NotificationType, Info.LevelUpNotification, self.Owner.Faction.InternalName);
			TextNotificationsManager.AddTransientLine(self.Owner, string.Format(Info.LevelUpTextNotification, currentLevel));
		}

		void PromoteToRank(int level)
		{
			currentRank = Ranks[currentLevel - 1];
			self.GrantCondition(nextLevel[currentLevel - 1].Condition);
			GivePoint(PointsPerRank[currentLevel - 1]);
			if (currentLevel < MaxLevel)
			{
				nextLevelXpRequired = nextLevel[currentLevel].RequiredExperience;
			}
			else
				IsMaxLevel = true;

			if (Info.FlavorTextNotifications != null && currentLevel > 1) TextNotify();
		}

		void GivePoint(int pointsToGive)
		{
			Points += pointsToGive;
			if (hasPointsToken == Actor.InvalidConditionToken && Points > 0)
				hasPointsToken = self.GrantCondition(Info.HasPointsCondition);
		}

		public void TakePoint(int pointsToTake)
		{
			if (Points > 0)
				Points -= pointsToTake;

			if (Points <= 0 && hasPointsToken != Actor.InvalidConditionToken)
				hasPointsToken = self.RevokeCondition(hasPointsToken);
		}

		void TextNotify()
		{
			if (self.Owner != self.Owner.World.LocalPlayer) return;

			var notification = FluentProvider.GetMessage(Info.FlavorTextNotifications.Random(self.World.LocalRandom));
			TextNotificationsManager.AddMissionLine(FluentProvider.GetMessage(Info.FlavorTextPrefix), notification, self.Owner.Color);
		}
	}
}
