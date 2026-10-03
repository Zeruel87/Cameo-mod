WorldLoaded = function()
	local player = Player.GetPlayer("Player")
	local bot = Player.GetPlayer("FransBot")
	local objective = player.AddPrimaryObjective("Hold until the gate completes.")

	Actor.Create("td_gdi_constructionyard", true, { Owner = player, Location = CPos.New(24, 24) })
	Actor.Create("ra1_soviets_constructionyard", true, { Owner = bot, Location = CPos.New(72, 72) })
	print("AI_FRANSBOT_SMOKE_STARTED bot=FransBot type=fransbot")

	-- Nine hundred ticks exercises repeated situation snapshots.
	Trigger.AfterDelay(4500, function()
		print("AI_FRANSBOT_SMOKE_COMPLETED bot=FransBot tick=" .. DateTime.GameTime)
		player.MarkFailedObjective(objective)
	end)
end
