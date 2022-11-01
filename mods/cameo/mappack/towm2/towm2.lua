if Map.LobbyOption("difficulty") == "easy" then
    DateTime.TimeLimit = DateTime.Minutes(16) + DateTime.Seconds(10)
elseif Map.LobbyOption("difficulty") == "normal" then
    DateTime.TimeLimit = DateTime.Minutes(20) + DateTime.Seconds(25)
else
    DateTime.TimeLimit = DateTime.Minutes(24) + DateTime.Seconds(40)
end

OWConvoy = { "awapc", "awapc" }

PlayerEscort = function()
    Media.DisplayMessage("The Orange Star leaders are leaving. Ensure their safe dpearture!")
    local owapcs = Reinforcements.Reinforce(orangestar, OWConvoy, { Actor87.Location, Actor88.Location }, DateTime.Seconds(1), function(apc)
        Trigger.OnIdle(apc, function()
            apc.Move(Actor89.Location)
        end)
    end)

    local cells = Utils.ExpandFootprint({ Actor89.Location }, true)
    Trigger.OnEnteredFootprint(cells, function()
        player.MarkCompletedObjective(EscortObjective)
    end)

    Trigger.OnAnyKilled(owapcs, function()
        player.MarkFailedObjective(EscortObjective)
    end)

end

WorldLoaded = function()
    player = Player.GetPlayer("Player")
    bluemoon = Player.GetPlayer("BM")
    orangestar = Player.GetPlayer("OW")

    Trigger.OnObjectiveAdded(player, function(p, id)
		Media.DisplayMessage(p.GetObjectiveDescription(id), "New " .. string.lower(p.GetObjectiveType(id)) .. " objective")
	end)
	Trigger.OnObjectiveCompleted(player, function(p, id)
		Media.DisplayMessage(p.GetObjectiveDescription(id), "Objective completed")
	end)
	Trigger.OnObjectiveFailed(player, function(p, id)
		Media.DisplayMessage(p.GetObjectiveDescription(id), "Objective failed")
	end)

    DefendObjective = player.AddPrimaryObjective("Defend the Command Center until negotiations are complete.")
    EscortObjective = player.AddPrimaryObjective("Escort the Orange Star leaders to safety.")

    Trigger.OnKilled(Actor0, function()
        player.MarkFailedObjective(DefendObjective)
        player.MarkFailedObjective(EscortObjective)
    end)

    Trigger.OnTimerExpired(function()
        player.MarkCompletedObjective(DefendObjective)
        Trigger.AfterDelay(DateTime.Seconds(3), PlayerEscort)
    end)


end

Tick = function()

end
