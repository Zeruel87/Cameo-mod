WorldLoaded = function()
	local frans = Player.GetPlayer("FransBot")
	local hard = Player.GetPlayer("HardBot")

	Actor.Create("ra1_allies_constructionyard", true, { Owner = frans, Location = CPos.New(72, 72) })
	Actor.Create("ra1_soviets_constructionyard", true, { Owner = hard, Location = CPos.New(24, 24) })
	print("AI_VERSUS_STARTED frans=fransbot hard=hard")

	-- 25000-tick safety cap; a knockout normally ends the match well before.
	Trigger.AfterDelay(25000, function()
		print("AI_VERSUS_TIMECAP tick=" .. DateTime.GameTime)
	end)
end
