Carryall = { "scdropship" }
NumCaptured = 0


WorldLoaded = function()
    player = Player.GetPlayer("Player")
    bluemoon = Player.GetPlayer("BM")
    greenearth = Player.GetPlayer("GE")
    yellowcomet = Player.GetPlayer("YC")
    lila = Player.GetPlayer("Lila")
    Camera.Position = SAMI.CenterPosition
    bluemoon.Cash = 5000
    greenearth.Cash = 5000
    yellowcomet.Cash = 5000

    Trigger.OnObjectiveAdded(player, function(p, id)
		Media.DisplayMessage(p.GetObjectiveDescription(id), "New " .. string.lower(p.GetObjectiveType(id)) .. " objective")
	end)
	Trigger.OnObjectiveCompleted(player, function(p, id)
		Media.DisplayMessage(p.GetObjectiveDescription(id), "Objective completed")
	end)
	Trigger.OnObjectiveFailed(player, function(p, id)
		Media.DisplayMessage(p.GetObjectiveDescription(id), "Objective failed")
	end)

    SecureObjective = player.AddPrimaryObjective("Capture four enemy factories.")
    DefendObjective = player.AddPrimaryObjective("Defend the four factories until extraction is complete.")
    KeepAliveObjective = player.AddSecondaryObjective("Do not lose Sami.")

    Trigger.OnKilled(SAMI, function()
        Media.DisplayMessage("Sami has fallen. We'll try to recover her from the battlefield.")
        player.MarkFailedObjective(KeepAliveObjective)
    end)

    Trigger.OnCapture(FactoryBM1, function()
        Trigger.AfterDelay(DateTime.Seconds(5), function()
            Media.DisplayMessage("A Carryall is arriving to extract the technology. Do not let it be destroyed!")
            local carryall = Reinforcements.Reinforce(lila, Carryall, { CarryallSpawner.Location, BMFactW1.Location }, 0, function(ship)
                Trigger.AfterDelay(DateTime.Seconds(40), function()
                    Media.DisplayMessage("Extraction complete.")
                    ship.Move(CarryallSpawner.Location)
                    NumCaptured = NumCaptured + 1
                end)
                Trigger.OnKilled(ship, function()
                    player.MarkFailedObjective(SecureObjective)
                    player.MarkFailedObjective(DefendObjective)
                end)
            end)
        end)
    end)

    Trigger.OnCapture(FactoryBM2, function()
        Trigger.AfterDelay(DateTime.Seconds(5), function()
            Media.DisplayMessage("A Carryall is arriving to extract the technology. Do not let it be destroyed!")
            local carryall = Reinforcements.Reinforce(lila, Carryall, { CarryallSpawner.Location, BMFactW2.Location }, 0, function(ship)
                Trigger.AfterDelay(DateTime.Seconds(40), function()
                    Media.DisplayMessage("Extraction complete.")
                    ship.Move(CarryallSpawner.Location)
                    NumCaptured = NumCaptured + 1
                end)
                Trigger.OnKilled(ship, function()
                    player.MarkFailedObjective(SecureObjective)
                    player.MarkFailedObjective(DefendObjective)
                end)
            end)
        end)
    end)

    Trigger.OnCapture(FactoryGE1, function()
        Trigger.AfterDelay(DateTime.Seconds(5), function()
            Media.DisplayMessage("A Carryall is arriving to extract the technology. Do not let it be destroyed!")
            local carryall = Reinforcements.Reinforce(lila, Carryall, { CarryallSpawner.Location, GEFactW1.Location }, 0, function(ship)
                Trigger.AfterDelay(DateTime.Seconds(40), function()
                    Media.DisplayMessage("Extraction complete.")
                    ship.Move(CarryallSpawner.Location)
                    NumCaptured = NumCaptured + 1
                end)
                Trigger.OnKilled(ship, function()
                    player.MarkFailedObjective(SecureObjective)
                    player.MarkFailedObjective(DefendObjective)
                end)
            end)
        end)
    end)

    Trigger.OnCapture(FactoryGE2, function()
        Trigger.AfterDelay(DateTime.Seconds(5), function()
            Media.DisplayMessage("A Carryall is arriving to extract the technology. Do not let it be destroyed!")
            local carryall = Reinforcements.Reinforce(lila, Carryall, { CarryallSpawner.Location, GEFactW2.Location }, 0, function(ship)
                Trigger.AfterDelay(DateTime.Seconds(40), function()
                    Media.DisplayMessage("Extraction complete.")
                    ship.Move(CarryallSpawner.Location)
                    NumCaptured = NumCaptured + 1
                end)
                Trigger.OnKilled(ship, function()
                    player.MarkFailedObjective(SecureObjective)
                    player.MarkFailedObjective(DefendObjective)
                end)
            end)
        end)
    end)

    Trigger.OnCapture(FactoryYC1, function()
        Trigger.AfterDelay(DateTime.Seconds(5), function()
            Media.DisplayMessage("A Carryall is arriving to extract the technology. Do not let it be destroyed!")
            local carryall = Reinforcements.Reinforce(lila, Carryall, { CarryallSpawner.Location, YCFactW1.Location }, 0, function(ship)
                Trigger.AfterDelay(DateTime.Seconds(40), function()
                    Media.DisplayMessage("Extraction complete.")
                    ship.Move(CarryallSpawner.Location)
                    NumCaptured = NumCaptured + 1
                end)
                Trigger.OnKilled(ship, function()
                    player.MarkFailedObjective(SecureObjective)
                    player.MarkFailedObjective(DefendObjective)
                end)
            end)
        end)
    end)

    Trigger.OnCapture(FactoryYC2, function()
        Trigger.AfterDelay(DateTime.Seconds(5), function()
            Media.DisplayMessage("A Carryall is arriving to extract the technology. Do not let it be destroyed!")
            local carryall = Reinforcements.Reinforce(lila, Carryall, { CarryallSpawner.Location, YCFactW2.Location }, 0, function(ship)
                Trigger.AfterDelay(DateTime.Seconds(40), function()
                    Media.DisplayMessage("Extraction complete.")
                    ship.Move(CarryallSpawner.Location)
                    NumCaptured = NumCaptured + 1
                end)
                Trigger.OnKilled(ship, function()
                    player.MarkFailedObjective(SecureObjective)
                    player.MarkFailedObjective(DefendObjective)
                end)
            end)
        end)
    end)
end

Tick = function()
    if NumCaptured >= 4 then
        player.MarkCompletedObjective(SecureObjective)
        player.MarkCompletedObjective(DefendObjective)
        if not SAMI.IsDead then
            player.MarkCompletedObjective(KeepAliveObjective)
        end
    end
end