WorldLoaded = function()
	local player = Player.GetPlayer("Player")
	local bot = Player.GetPlayer("HardBot")

	Actor.Create("td_gdi_constructionyard", true, { Owner = player, Location = CPos.New(24, 24) })
	Actor.Create("td_nod_constructionyard", true, { Owner = bot, Location = CPos.New(72, 72) })
	print("AI_PHASE2_GATE_STARTED bot=HardBot type=hard")

	-- Four hundred ticks exercises construction and world advancement with the
	-- same fixed hard-bot form used by Cameo campaign maps.
	Trigger.AfterDelay(400, function()
		print("AI_PHASE2_GATE_COMPLETED bot=HardBot tick=" .. DateTime.GameTime)
	end)
end
