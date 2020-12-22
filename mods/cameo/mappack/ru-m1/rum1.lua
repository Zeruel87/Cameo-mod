StartingEngineers = { Engineer1, Engineer2, Engineer3 }

WorldLoaded = function()
	player = Player.GetPlayer("Multi0")
	allies = Player.GetPlayer("Allies")

	Trigger.OnObjectiveAdded(player, function(p, id)
		Media.DisplayMessage(p.GetObjectiveDescription(id), "New " .. string.lower(p.GetObjectiveType(id)) .. " objective")
	end)
	Trigger.OnObjectiveCompleted(player, function(p, id)
		Media.DisplayMessage(p.GetObjectiveDescription(id), "Objective completed")
	end)
	Trigger.OnObjectiveFailed(player, function(p, id)
		Media.DisplayMessage(p.GetObjectiveDescription(id), "Objective failed")
	end)
	Trigger.OnPlayerLost(player, function()
		Media.PlaySpeechNotification(player, "MissionFailed")
	end)
	Trigger.OnPlayerWon(player, function()
		Media.PlaySpeechNotification(player, "MissionAccomplished")
	end)
	
	ConquestObjective = player.AddPrimaryObjective("Eliminate the entire Allied presence in this area.")
	alliedObjective = allies.AddPrimaryObjective("Destroy all opposition!")

end

Tick = function()
	if allies.HasNoRequiredUnits() then
		player.MarkCompletedObjective(ConquestObjective)
	end

	if player.HasNoRequiredUnits() then
		allies.MarkCompletedObjective(alliedObjective)
	end
end