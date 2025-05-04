
SankalpaArrival = false

Difficulty = Map.LobbyOptionOrDefault("difficulty", "normal")

SetTimer = function()
	if Difficulty == "easy" then
		DateTime.TimeLimit = DateTime.Minutes(7) + DateTime.Seconds(10)
	elseif Difficulty == "normal" then
		DateTime.TimeLimit = DateTime.Minutes(10) + DateTime.Seconds(20)
	elseif Difficulty == "hard" then
		DateTime.TimeLimit = DateTime.Minutes(15) + DateTime.Seconds(40)
	end
end

Notification = function (text)
	Media.DisplayMessage(text, "Notification", HSLColor.SkyBlue)
end

Tip = function (text)
	Media.DisplayMessage(text, "Tip", HSLColor.DarkCyan)
end

Warning = function (text)
	Media.DisplayMessage(text, "Warning", HSLColor.Red)
end

InitObjectives = function(player)
	Trigger.OnObjectiveAdded(player, function(p, id)
		if p.IsLocalPlayer then
			Trigger.AfterDelay(1, function()
				local colour = HSLColor.Yellow
				if p.GetObjectiveType(id) ~= "Primary" then
					colour = HSLColor.Gray
				end
				Media.DisplayMessage(p.GetObjectiveDescription(id), "New " .. string.lower(p.GetObjectiveType(id)) .. " objective", colour)
			end)
		end
	end)

	Trigger.OnObjectiveCompleted(player, function(p, id)
		if p.IsLocalPlayer then
			Media.PlaySoundNotification(player, "AlertBleep")
			Media.DisplayMessage(p.GetObjectiveDescription(id), "Objective completed", HSLColor.LimeGreen)
		end
	end)

	Trigger.OnObjectiveFailed(player, function(p, id)
		if p.IsLocalPlayer then
			Media.DisplayMessage(p.GetObjectiveDescription(id), "Objective failed", HSLColor.Red)
		end
	end)

	Trigger.OnPlayerLost(player, function()
		if player.IsLocalPlayer then
			Trigger.AfterDelay(DateTime.Seconds(1), function()
				Media.PlaySpeechNotification(player, "MissionFailed")
			end)
		end
	end)

	Trigger.OnPlayerWon(player, function()
		if player.IsLocalPlayer then
			Trigger.AfterDelay(DateTime.Seconds(1), function()
				Media.PlaySpeechNotification(player, "MissionAccomplished")
			end)
		end
	end)
end

UnitHunt = function (a)
	Trigger.OnIdle(a, function (a)
		a.Hunt()
	end)
end

SankalpaHeli = { "modhip" }
SankalpaAirForce = { "heli", "heli", "heli" }
SankalpaDefenseForce = { "nodftnk2", "nodftnk2", "chemssm", "chemssm" }

WorldLoaded = function ()
	NewHopeOne = Player.GetPlayer("NewHopeOne")
	NewHopeTwo = Player.GetPlayer("NewHopeTwo")
	Sankalpa = Player.GetPlayer("Sankalpa")
	Nitro = Player.GetPlayer("Nitro")
	NitroJP = Player.GetPlayer("NitroJP")
	NitroRed = Player.GetPlayer("NitroRed")
	Neutral = Player.GetPlayer("Neutral")
	-- WorldLoadedGeneralsPromotions()

	InitObjectives(NewHopeOne)
	InitObjectives(NewHopeTwo)
	NewHopeObjectives = {
		NewHopeOne.AddPrimaryObjective("Defend the harbour until support arrives."),
		NewHopeTwo.AddPrimaryObjective("Defend the harbour until support arrives.")
	}
	SetTimer()

	Trigger.AfterDelay(DateTime.Seconds(3), function ()
		Tip("BOTH Construction Yards must survive. They cannot be rebuilt.")
	end)

	Trigger.OnRemovedFromWorld(PlayerOneMCV, function ()
		NewHopeOne.MarkFailedObjective(NewHopeObjectives[1])
		NewHopeTwo.MarkFailedObjective(NewHopeObjectives[2])
	end)

	Trigger.OnRemovedFromWorld(PlayerTwoMCV, function ()
		NewHopeOne.MarkFailedObjective(NewHopeObjectives[1])
		NewHopeTwo.MarkFailedObjective(NewHopeObjectives[2])
	end)

	Trigger.OnTimerExpired(function ()
		Notification("The Sankalpa have arrived!")
		SankalpaArrival = true
		Reinforcements.Reinforce(Sankalpa, SankalpaHeli, {SpawnOne.Location}, 0, function(heli)
			Trigger.OnIdle(heli, function (heli)
				heli.Move(HeliEntranceOne.Location)
				heli.Wait(DateTime.Seconds(3))
				heli.UnloadPassengers()
				heli.Destroy()
			end)
		end)
		Reinforcements.Reinforce(Sankalpa, SankalpaAirForce, {SpawnTwo.Location, HeliEntranceOne.Location}, 0, UnitHunt)
		Reinforcements.ReinforceWithTransport(Sankalpa, "lst", SankalpaDefenseForce, {SpawnThree.Location}, nil, function (transport)
			Trigger.OnIdle(transport, function (transport)
				transport.Move(TransportTwo.Location)
				transport.Wait(DateTime.Seconds(3))
				transport.UnloadPassengers()
			end)
		end, function (la)
			la.Wait(DateTime.Seconds(3))
			la.Move(SpawnThree.Location)
			la.Destroy()
		end)
		Reinforcements.Reinforce(Sankalpa, SankalpaAirForce, {SpawnFour.Location, HeliEntranceOne.Location}, 0, UnitHunt)
		Reinforcements.ReinforceWithTransport(Sankalpa, "lst", SankalpaDefenseForce, {SpawnFive.Location}, nil, function (transport)
			Trigger.OnIdle(transport, function (transport)
				transport.Move(TransportThree.Location)
				transport.Wait(DateTime.Seconds(3))
				transport.UnloadPassengers()
			end)
		end, function (la)
			la.Wait(DateTime.Seconds(3))
			la.Move(SpawnFive.Location)
			la.Destroy()
		end)
		Reinforcements.Reinforce(Sankalpa, SankalpaAirForce, {SpawnSix.Location, HeliEntranceTwo.Location}, 0, UnitHunt)
		Reinforcements.Reinforce(Sankalpa, SankalpaHeli, {SpawnSeven.Location, HeliEntranceTwo.Location}, 0, function(heli)
			Trigger.OnIdle(heli, function (heli)
				heli.Move(HeliEntranceTwo.Location)
				heli.Wait(DateTime.Seconds(3))
				heli.UnloadPassengers()
				heli.Destroy()
			end)
		end)

		Trigger.AfterDelay(DateTime.Seconds(30), function ()
			NewHopeOne.MarkCompletedObjective(NewHopeObjectives[1])
			NewHopeTwo.MarkCompletedObjective(NewHopeObjectives[2])
		end)

	end)

end

Tick = function ()
	-- TickPromotions()
end
