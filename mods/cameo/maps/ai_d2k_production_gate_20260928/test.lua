WorldLoaded = function()
	local player = Player.GetPlayer("Player")
	local bot = Player.GetPlayer("HardBot")
	local objective = player.AddPrimaryObjective("Hold until the gate completes.")

	-- The bot starts with only a construction yard and DefaultCash. Every
	-- actor it gains is produced by the bot pipeline, so the owned-actor count
	-- growing proves production works for a content-pack faction (regression:
	-- atreides ids missing from the central *Types lists left the bot inert).
	Actor.Create("atreides_constructionyard", true, { Owner = bot, Location = CPos.New(72, 72) })

	-- A harkonnen anchor for the human player keeps the faction-pair honest
	-- without producing anything itself.
	Actor.Create("harkonnen_constructionyard", true, { Owner = player, Location = CPos.New(24, 24) })
	print("AI_D2K_PRODUCTION_GATE_STARTED bot=HardBot type=hard")

	-- Tick + actor-count heartbeat so a stalled or inert world is visible in
	-- the output tail even when the gate itself times out.
	for i = 250, 2750, 250 do
		Trigger.AfterDelay(i, function()
			print("AI_D2K_GATE_TICK " .. DateTime.GameTime .. " bot_actors=" .. #bot.GetActors())
		end)
	end

	Trigger.AfterDelay(3000, function()
		print("AI_D2K_GATE_ACTORS=" .. #bot.GetActors())
		print("AI_D2K_PRODUCTION_GATE_COMPLETED bot=HardBot tick=" .. DateTime.GameTime)
		player.MarkFailedObjective(objective)
	end)
end
