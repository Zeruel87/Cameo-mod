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

MCVOne = false
MCVTwo = false
PhaseTwo = false

WorldLoaded = function ()
	Penta = Player.GetPlayer("Penta")
	Shade = Player.GetPlayer("Shade")
	NitroIdle = Player.GetPlayer("NitroIdle")
	NitroActive = Player.GetPlayer("NitroActive")

	InitObjectives(Penta)
	InitObjectives(Shade)
	Notification("We've started our assault on the beachhead in North Carolina. More navl and land forces are coming.")
	
	PlayerOneObjective = Penta.AddPrimaryObjective("Clear the enemy forces at the beachhead and prepare for a landing.")
	PlayerTwoObjective = Shade.AddPrimaryObjective("Clear the enemy forces at the beachhead and prepare for a landing.")

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
		Media.PlaySpeechNotification(Shade, "ReinforcementsArrived")
		Media.DisplayMessage("Reinforcements have arrived.", "Player 1", HSLColor.SkyBlue)
		Reinforcements.Reinforce(Penta, Boats, {PentaSpawnOne.Location, PentaNavalPointOne.Location})
		Reinforcements.Reinforce(Penta, Boats, {PentaSpawnTwo.Location, PentaNavalPointTwo.Location})
		Reinforcements.Reinforce(Penta, Boats, {PentaSpawnThree.Location, PentaNavalPointThree.Location})
		Media.DisplayMessage("Reinforcements have arrived.", "Player 2", HSLColor.SkyBlue)
		Reinforcements.Reinforce(Shade, Boats, {ShadeSpawnOne.Location, ShadeNavalPointOne.Location})
		Reinforcements.Reinforce(Shade, Boats, {ShadeSpawnTwo.Location, ShadeNavalPointTwo.Location})
		Reinforcements.Reinforce(Shade, Boats, {ShadeSpawnThree.Location, ShadeNavalPointThree.Location})
	end)

	Trigger.OnAllRemovedFromWorld(BeachheadOne, function ()
		Media.PlaySpeechNotification(Penta, "ReinforcementsArrived")
		Media.DisplayMessage("Reinforcements have arrived.", "Player 1", HSLColor.SkyBlue)
		Reinforcements.ReinforceWithTransport(Penta, "ra2lcrf", TaskForceOne, {PentaSpawnOne.Location, PentaDestOne.Location}, {PentaSpawnOne.Location})
		Reinforcements.ReinforceWithTransport(Penta, "ra2lcrf", TaskForceOne, {PentaSpawnThree.Location, PentaDestThree.Location}, {PentaSpawnThree.Location})
		Reinforcements.ReinforceWithTransport(Penta, "ra2lcrf", ConstructionVehicle, {PentaSpawnTwo.Location, PentaDestTwo.Location}, {PentaSpawnTwo.Location})
		Trigger.AfterDelay(DateTime.Seconds(5), function ()
			PlayerOneClear = Penta.AddPrimaryObjective("Eliminate all Nitro forces.")
			Penta.MarkCompletedObjective(PlayerOneObjective)
		end)
	end)

	Trigger.OnAllRemovedFromWorld(BeachheadTwo, function ()
		Media.PlaySpeechNotification(Shade, "ReinforcementsArrived")
		Media.DisplayMessage("Reinforcements have arrived.", "Player 2", HSLColor.SkyBlue)
		Reinforcements.ReinforceWithTransport(Shade, "ra2lcrf", TaskForceOne, {ShadeSpawnOne.Location, ShadeDestOne.Location}, {ShadeSpawnOne.Location})
		Reinforcements.ReinforceWithTransport(Shade, "ra2lcrf", TaskForceOne, {ShadeSpawnThree.Location, ShadeDestThree.Location}, {ShadeSpawnThree.Location})
		Reinforcements.ReinforceWithTransport(Shade, "ra2lcrf", ConstructionVehicle, {ShadeSpawnTwo.Location, ShadeDestTwo.Location}, {ShadeSpawnTwo.Location})
		Trigger.AfterDelay(DateTime.Seconds(5), function ()
			PlayerTwoClear = Shade.AddPrimaryObjective("Eliminate all Nitro forces.")
			Shade.MarkCompletedObjective(PlayerTwoObjective)
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
		Penta.MarkFailedObjective(PlayerOneClear)
	end

	if Shade.HasNoRequiredUnits() then
		Shade.MarkFailedObjective(PlayerTwoObjective)
		Shade.MarkFailedObjective(PlayerTwoClear)
	end

	if NitroIdle.HasNoRequiredUnits() and NitroActive.HasNoRequiredUnits() then
		Penta.MarkCompletedObjective(PlayerOneClear)
		Shade.MarkCompletedObjective(PlayerTwoClear)
	end
end