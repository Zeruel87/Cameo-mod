ObjectiveTimer = {
	Easy = DateTime.Minutes(3) + DateTime.Seconds(20),
	Normal = DateTime.Minutes(2) + DateTime.Seconds(30),
	Hard = DateTime.Minutes(1) + DateTime.Seconds(40)
}

Diff = Map.LobbyOptionOrDefault("difficulty", "normal")

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

ConstructionVehicle = {"ramcv.allies"}
TaskForceOne = {"ra2fv", "ra2fv", "ra2mtnk", "ra2mtnk"}
TaskForceTwo = {"rae1", "rae1", "rae1", "rae3", "rae3", "rae3", "raarty", "raarty"}
Boats = {"dd", "dd"}
BeachheadOne = {Actor1, Actor6, Actor7, Actor11, Actor12, Actor79}
BeachheadTwo = {Actor4, Actor5, Actor8, Actor9, Actor10, Actor80}

MCVone = false
MCVtwo = false
PhaseTwo = false

WorldLoaded = function ()
	Penta = Player.GetPlayer("Penta")
	ShadeIdle = Player.GetPlayer("ShadeIdle")
	ShadeActive = Player.GetPlayer("ShadeActive")
	NitroIdle = Player.GetPlayer("NitroIdle")
	NitroActive = Player.GetPlayer("NitroActive")

	InitObjectives(Penta)
	Notification("We've started our assault on the beachhead in North Carolina. More naval and land forces are coming.")
	
	PlayerOneObjective = Penta.AddPrimaryObjective("Clear the enemy forces at the beachhead and prepare for a landing.")
	Trigger.AfterDelay(DateTime.Seconds(1), function ()
		Notification("We'll need to get set up quickly before the Nitro's communications network comes back online.")
		Media.PlaySpeechNotification(Penta, "MissionTimerInitialised")
		if Diff == "easy" then
			DateTime.TimeLimit = ObjectiveTimer.Easy
		elseif Diff == "normal" then
			DateTime.TimeLimit = ObjectiveTimer.Normal
		else
			DateTime.TimeLimit = ObjectiveTimer.Hard
		end

		Trigger.OnTimerExpired(function ()
			Notification("The Nitro communications grid is back online. They're going to attack soon!")
			ActivateNitro()
		end)
	end)

	Trigger.AfterDelay(DateTime.Seconds(3), function ()
		Media.PlaySpeechNotification(Penta, "ReinforcementsArrived")
		Notification("Reinforcements have arrived.")
		Reinforcements.Reinforce(Penta, Boats, {PentaSpawnOne.Location, PentaNavalPointOne.Location})
		Reinforcements.Reinforce(Penta, Boats, {PentaSpawnTwo.Location, PentaNavalPointTwo.Location})
		Reinforcements.Reinforce(Penta, Boats, {PentaSpawnThree.Location, PentaNavalPointThree.Location})
		Reinforcements.Reinforce(ShadeActive, Boats, {ShadeSpawnOne.Location, ShadeNavalPointOne.Location})
		Reinforcements.Reinforce(ShadeActive, Boats, {ShadeSpawnTwo.Location, ShadeNavalPointTwo.Location})
		Reinforcements.Reinforce(ShadeActive, Boats, {ShadeSpawnThree.Location, ShadeNavalPointThree.Location})
	end)

	Trigger.OnAllRemovedFromWorld(BeachheadOne, function ()
		Media.PlaySpeechNotification(Penta, "ReinforcementsArrived")
		Notification("Reinforcements have arrived.")
		Reinforcements.ReinforceWithTransport(Penta, "ra2lcrf", TaskForceOne, {PentaSpawnOne.Location, PentaDestOne.Location}, {PentaSpawnOne.Location})
		Reinforcements.ReinforceWithTransport(Penta, "ra2lcrf", TaskForceOne, {PentaSpawnThree.Location, PentaDestThree.Location}, {PentaSpawnThree.Location})
		Reinforcements.ReinforceWithTransport(Penta, "ra2lcrf", ConstructionVehicle, {PentaSpawnTwo.Location, PentaDestTwo.Location}, {PentaSpawnTwo.Location})
		Trigger.AfterDelay(DateTime.Seconds(5), function ()
			PlayerOneClear = Penta.AddPrimaryObjective("Eliminate all Nitro forces.")
			Penta.MarkCompletedObjective(PlayerOneObjective)
		end)
	end)

	Trigger.OnAllRemovedFromWorld(BeachheadTwo, function ()
		Reinforcements.ReinforceWithTransport(ShadeIdle, "ra2lcrf", TaskForceOne, {ShadeSpawnOne.Location, ShadeDestOne.Location}, nil, function(la, a)
			la.UnloadPassengers()
			Utils.Do(a, function (ta)
				ta.Owner = ShadeActive
			end)
		end, function (la)
			la.Wait(DateTime.Seconds(3))
			la.Move(ShadeSpawnOne.Location)
			la.Destroy()
		end)
		Reinforcements.ReinforceWithTransport(ShadeIdle, "ra2lcrf", TaskForceOne, {ShadeSpawnThree.Location, ShadeDestThree.Location}, nil, function (la, a)
			la.UnloadPassengers()
			Utils.Do(a, function (ta)
				ta.Owner = ShadeActive
			end)
		end, function (la)
			la.Wait(DateTime.Seconds(3))
			la.Move(ShadeSpawnThree.Location)
			la.Destroy()
		end)
		Reinforcements.ReinforceWithTransport(ShadeIdle, "ra2lcrf", ConstructionVehicle, {ShadeSpawnTwo.Location, ShadeDestTwo.Location}, nil, function (la, cv)
			la.UnloadPassengers()
			Utils.Do(cv, function (mcv)
				Trigger.OnAddedToWorld(mcv, function ()
					mcv.Move(Actor202.Location)
					mcv.Deploy()
					mcv.Owner = ShadeActive
					Trigger.Clear(mcv, "OnAddedToWorld")
				end)
			end)
		end, function (la)
			la.Wait(DateTime.Seconds(3))
			la.Move(ShadeSpawnTwo.Location)
			la.Destroy()
		end)
	end)
end

ActivateNitro = function ()
	local NitroActors = NitroIdle.GetActors()
	for i=1, #NitroActors do
		NitroActors[i].Owner = NitroActive
	end
end

Tick = function ()
	if Penta.HasNoRequiredUnits() then
		Penta.MarkFailedObjective(PlayerOneObjective)
	end

	if NitroIdle.HasNoRequiredUnits() and NitroActive.HasNoRequiredUnits() then
		Penta.MarkCompletedObjective(PlayerOneClear)
	end

	if MCVone == false and #Penta.GetActorsByType("rafact.allies") > 0 then
		MCVone = true
		Notification("Reinforcements have arrived.")
		Media.PlaySpeechNotification(Penta, "ReinforcementsArrived")
		Reinforcements.ReinforceWithTransport(Penta, "ra2lcrf", TaskForceTwo, {PentaSpawnOne.Location, PentaDestOne.Location}, {PentaSpawnOne.Location})
		Reinforcements.ReinforceWithTransport(Penta, "ra2lcrf", TaskForceTwo, {PentaSpawnThree.Location, PentaDestThree.Location}, {PentaSpawnThree.Location})
	end

	if MCVtwo == false and #ShadeActive.GetActorsByType("rafact.allies") > 0 then
		MCVtwo = true
		Reinforcements.ReinforceWithTransport(ShadeIdle, "ra2lcrf", TaskForceTwo, {ShadeSpawnOne.Location, ShadeDestOne.Location}, nil, function(la, a)
			la.UnloadPassengers()
			Utils.Do(a, function (ta)
				ta.Owner = ShadeActive
			end)
		end, function (la)
			la.Wait(DateTime.Seconds(3))
			la.Move(ShadeSpawnOne.Location)
			la.Destroy()
		end)
		Reinforcements.ReinforceWithTransport(ShadeIdle, "ra2lcrf", TaskForceTwo, {ShadeSpawnThree.Location, ShadeDestThree.Location}, nil, function (la, a)
			la.UnloadPassengers()
			Utils.Do(a, function (ta)
				ta.Owner = ShadeActive
			end)
		end, function (la)
			la.Wait(DateTime.Seconds(3))
			la.Move(ShadeSpawnThree.Location)
			la.Destroy()
		end)
	end
end