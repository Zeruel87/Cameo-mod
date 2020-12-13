--[[
   Copyright 2007-2020 The OpenRA Developers (see AUTHORS)
   This file is part of OpenRA, which is free software. It is made
   available to you under the terms of the GNU General Public License
   as published by the Free Software Foundation, either version 3 of
   the License, or (at your option) any later version. For more
   information, see COPYING.
]]

PromotionsText = ""

Seconds = 0

PointsPerRank = { 1, 1, 1, 1, 3 }

PointActorExists = { }
Points = { }
HasPointsActors =  { }
Levels = { }
TextColors ={ }

Ranks = { "OF-1", "OF-2", "OF-3", "OF-4", "OF-5" }
RankXPs = { 0, 12500, 25000, 50000, 100000 }

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
			if Levels[player.InternalName] < 4 then
				PromotionsText = "Current Rank: " .. Ranks[Levels[player.InternalName] + 1] .. "\nPromotion Points: " .. Points[player.InternalName] .. "\nProgress to Next Rank: " .. player.Experience - RankXPs[Levels[player.InternalName] + 1] .. "/" .. RankXPs[Levels[player.InternalName] + 2] - RankXPs[Levels[player.InternalName] + 1] .. "\n\n"
			else
				PromotionsText = "Current Rank: " .. Ranks[Levels[player.InternalName] + 1] .. "\nPromotion Points: " .. Points[player.InternalName] .. "\n\n"
			end
			UserInterface.SetMissionText(PromotionsText, TextColors[player.InternalName])
		end

		if localPlayerIsNull then
			PromotionsText = ""
			UserInterface.SetMissionText(PromotionsText)
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

			
		end

		if player.Experience >= RankXPs[3] and not (Levels[player.InternalName] > 1) then
			Levels[player.InternalName] = Levels[player.InternalName] + 1
			Points[player.InternalName] = Points[player.InternalName] + PointsPerRank[3]

			
			Actor.Create("hack.rank_3", true, { Owner = player })
		end

		if player.Experience >= RankXPs[4] and not (Levels[player.InternalName] > 2) then
			Levels[player.InternalName] = Levels[player.InternalName] + 1
			Points[player.InternalName] = Points[player.InternalName] + PointsPerRank[4]

			
		end

		if player.Experience >= RankXPs[5] and not (Levels[player.InternalName] > 3) then
			Levels[player.InternalName] = Levels[player.InternalName] + 1
			Points[player.InternalName] = Points[player.InternalName] + PointsPerRank[5]

			
			Actor.Create("hack.rank_5", true, { Owner = player })
		end
	end
end

Second = function()
	Trigger.AfterDelay(DateTime.Seconds(1), function()
		Seconds = Seconds + 1

		for _,player in pairs(players) do
			if Points[player.InternalName] > 0 and Seconds % 2 == 0 then
				TextColors[player.InternalName] = HSLColor.White
			else
				TextColors[player.InternalName] = player.Color
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

	for _,player in pairs(players) do
		ReducePoints(player)
	end
end
