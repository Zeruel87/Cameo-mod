WorldLoaded = function()
    player = Player.GetPlayer("Player")
    yellowcomet1 = Player.GetPlayer("YC1")
    yellowcomet2 = Player.GetPlayer("YC2")

    Trigger.OnObjectiveAdded(player, function(p, id)
		Media.DisplayMessage(p.GetObjectiveDescription(id), "New " .. string.lower(p.GetObjectiveType(id)) .. " objective")
	end)
	Trigger.OnObjectiveCompleted(player, function(p, id)
		Media.DisplayMessage(p.GetObjectiveDescription(id), "Objective completed")
	end)
	Trigger.OnObjectiveFailed(player, function(p, id)
		Media.DisplayMessage(p.GetObjectiveDescription(id), "Objective failed")
	end)

    SecureObjective = player.AddPrimaryObjective("Defend the Stabilizer device.")
    DestroyObjective = player.AddPrimaryObjective("Destroy the invading enemy forces.")

    Trigger.OnKilled(Stable, function()
        player.MarkFailedObjective(SecureObjective)
        player.MarkFailedObjective(DestroyObjective)
    end)

    
end

Tick = function()
    if #yellowcomet1.GetActors() == 0 and #yellowcomet2.GetActors() == 0 then
        player.MarkCompletedObjective(SecureObjective)
        player.MarkCompletedObjective(DestroyObjective)
    end
end