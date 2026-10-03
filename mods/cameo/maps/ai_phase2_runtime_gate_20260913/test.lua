WorldLoaded = function()
	local player = Player.GetPlayer("Player")
	local bot = Player.GetPlayer("HardBot")
	local objective = player.AddPrimaryObjective("Hold until the gate completes.")

	Actor.Create("td_gdi_constructionyard", true, { Owner = player, Location = CPos.New(24, 24) })
	Actor.Create("td_nod_constructionyard", true, { Owner = bot, Location = CPos.New(72, 72) })
	print("AI_PHASE2_GATE_STARTED bot=HardBot type=hard")

	-- Nine hundred ticks exercises repeated situation snapshots.
	Trigger.AfterDelay(900, function()
		print("AI_PHASE2_GATE_COMPLETED bot=HardBot tick=" .. DateTime.GameTime)
		player.MarkFailedObjective(objective)
	end)
end
