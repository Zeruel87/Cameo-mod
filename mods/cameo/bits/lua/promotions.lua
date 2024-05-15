--[[
   Copyright 2007-2020 The OpenRA Developers (see AUTHORS)
   This file is part of OpenRA, which is free software. It is made
   available to you under the terms of the GNU General Public License
   as published by the Free Software Foundation, either version 3 of
   the License, or (at your option) any later version. For more
   information, see COPYING.
]]

PromotionsText = ""

PromotionNotificationText = {
	"You have been promoted. Review the Promotions tab for access to new technologies.",
	"Congratulations on your field promotion! Purchase a Promotional upgrade to bolster your forces.",
	"Your successes have granted you access to an exclusive field technology or ability of your choice.",
	"You've been authorized to purchase a Promotional upgrade. Fight on to earn more points and expand your arsenal.",
	"A Promotional upgrade is now available to you. Unlock new units and powers or augment your existing ones."
}

Seconds = 0

PointsPerRank = { 0, 1, 1, 1, 1, 1, 1, 2}

PointActorExists = { }
Points = { }
HasPointsActors = { }
Levels = { }
TextColors = { }

Ranks = { "Level 1", "Level 2", "Level 3", "Level 4", "Level 5" , "Level 6", "Level 7", "Level 8" }
RankXPs = { 0, 5000, 15000, 30000, 50000, 75000, 115000, 140000 }

NotifyPromotion = function(player)
	Media.DisplayMessageToPlayer(player, Utils.Random(PromotionNotificationText), "General Staff", player.Color)
end

ReducePoints = function(player)
	Trigger.OnProduction(player.GetActorsByType("player")[1], function()
		if Points[player.InternalName] > 0 then
			Points[player.InternalName] = Points[player.InternalName] - 1
		end
	end)
end

TickPromotions = function()
	localPlayerIsNull = true;
	for _,player in pairs(players) do
		if player.IsLocalPlayer then
			localPlayerIsNull = false;
			if Levels[player.InternalName] < 7 then
				PromotionsText = "Current Rank: " .. Ranks[Levels[player.InternalName] + 1] .. "\nPromotion Points: " .. Points[player.InternalName] .. "\nProgress to Next Rank: " .. player.Experience - RankXPs[Levels[player.InternalName] + 1] .. "/" .. RankXPs[Levels[player.InternalName] + 2] - RankXPs[Levels[player.InternalName] + 1] .. "\n\n"
			else
				PromotionsText = "Current Rank: " .. Ranks[Levels[player.InternalName] + 1] .. "\nPromotion Points: " .. Points[player.InternalName] .. "\n\n"
			end
			UserInterface.SetMissionText(PromotionsText, TextColors[player.InternalName])
		end

		if Points[player.InternalName] > 0 and not PointActorExists[player.InternalName] then
			HasPointsActors[player.InternalName] = Actor.Create("hack.has_points", true, { Owner = player })

			PointActorExists[player.InternalName] = true
		end

		if not (Points[player.InternalName] > 0) and PointActorExists[player.InternalName] and HasPointsActors[player.InternalName] ~= nil then
			HasPointsActors[player.InternalName].Destroy()

			PointActorExists[player.InternalName] = false
		end

		if player.Experience >= RankXPs[2] and not (Levels[player.InternalName] > 0) then
			Levels[player.InternalName] = Levels[player.InternalName] + 1
			Points[player.InternalName] = Points[player.InternalName] + PointsPerRank[2]

			NotifyPromotion(player)
		end

		if player.Experience >= RankXPs[3] and not (Levels[player.InternalName] > 1) then
			Levels[player.InternalName] = Levels[player.InternalName] + 1
			Points[player.InternalName] = Points[player.InternalName] + PointsPerRank[3]

			NotifyPromotion(player)
			Actor.Create("hack.rank_3", true, { Owner = player })
		end

		if player.Experience >= RankXPs[4] and not (Levels[player.InternalName] > 2) then
			Levels[player.InternalName] = Levels[player.InternalName] + 1
			Points[player.InternalName] = Points[player.InternalName] + PointsPerRank[4]

			NotifyPromotion(player)
		end

		if player.Experience >= RankXPs[5] and not (Levels[player.InternalName] > 3) then
			Levels[player.InternalName] = Levels[player.InternalName] + 1
			Points[player.InternalName] = Points[player.InternalName] + PointsPerRank[5]

			NotifyPromotion(player)
			Actor.Create("hack.rank_5", true, { Owner = player })
		end

		if player.Experience >= RankXPs[6] and not (Levels[player.InternalName] > 4) then
			Levels[player.InternalName] = Levels[player.InternalName] + 1
			Points[player.InternalName] = Points[player.InternalName] + PointsPerRank[6]

			NotifyPromotion(player)
		end

		if player.Experience >= RankXPs[7] and not (Levels[player.InternalName] > 5) then
			Levels[player.InternalName] = Levels[player.InternalName] + 1
			Points[player.InternalName] = Points[player.InternalName] + PointsPerRank[7]

			NotifyPromotion(player)
		end

		if player.Experience >= RankXPs[8] and not (Levels[player.InternalName] > 6) then
			Levels[player.InternalName] = Levels[player.InternalName] + 1
			Points[player.InternalName] = Points[player.InternalName] + PointsPerRank[8]

			NotifyPromotion(player)
		end
	end
end

Second = function()
	Trigger.AfterDelay(DateTime.Seconds(1), function()
		Seconds = Seconds + 1

		for _,player in pairs(players) do
			if Points[player.InternalName] > 0 and Seconds % 6 == 0 then
				TextColors[player.InternalName] = player.Color
			elseif Points[player.InternalName] > 0 and Seconds % 6 == 1 then
				TextColors[player.InternalName] = HSLColor.Yellow
			elseif Points[player.InternalName] > 0 and Seconds % 6 == 2 then
				TextColors[player.InternalName] = HSLColor.Orange
			elseif Points[player.InternalName] > 0 and Seconds % 6 == 3 then
				TextColors[player.InternalName] = HSLColor.Red
			elseif Points[player.InternalName] > 0 and Seconds % 6 == 4 then
				TextColors[player.InternalName] = HSLColor.Magenta
			elseif Points[player.InternalName] > 0 and Seconds % 6 == 5 then
				TextColors[player.InternalName] = HSLColor.Blue
			else
				TextColors[player.InternalName] = HSLColor.White
			end
		end

		Second()
	end)
end

SetUpDefaults = function()
	for _,player in pairs(players) do
		PointActorExists[player.InternalName] = false
		Points[player.InternalName] = PointsPerRank[1]
		HasPointsActors[player.InternalName] = nil
		Levels[player.InternalName] = 0
		TextColors[player.InternalName] = HSLColor.White
	end
end

WorldLoadedGeneralsPromotions = function()
	players = Player.GetPlayers(function(p) return not p.IsNonCombatant end)
	SetUpDefaults()
	Second()

	for _,player in pairs(players) do
		ReducePoints(player)
	end
end
