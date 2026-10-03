
-- AI harvester gate (AI_ARCHITECTURE.md §2.8). HarvesterBotModuleCA counts and builds
-- harvesters BY NAME from HarvesterTypes and counts refineries by name from RefineryTypes,
-- aiming for HarvestersPerRefinery x refineries + AdditionalHarvesters (hard: 3 x n + 1).
--   TkmBot:      refinery listed, harvester was NOT -> the harvester role fixes it.
--   AtreidesBot: neither listed -> needs the refinery role as well.
-- A refinery's FreeActor gives harvesters away (TKM 1, Atreides 2: FreeActor + carryall delivery),
-- and the base builder builds more refineries, so the raw count proves nothing. The gate reports
-- extra = harvesters - free x refineries: harvesters that were actually BUILT. Rich bots (10000)
-- because UnitBuilderBotModuleCA serves no request while the base builder pauses it to save cash.
SampleTicks = { 1500, 3000, 4500, 6000 }

Bases = {
	{ bot = "TkmBot", harvester = "tkm_templateharvesterraname", refinery = "tkm_orerefinery", free = 1, origin = CPos.New(72, 72),
		buildings = { { "tkm_constructionyard", 0, 0 }, { "tkm_powerplant", 5, 0 }, { "tkm_powerplant", 8, 0 },
			{ "tkm_orerefinery", 0, 5 }, { "tkm_warfactory", 5, 5 } } },
	{ bot = "AtreidesBot", harvester = "atreides_spiceharvester", refinery = "atreides_refinery", free = 2, origin = CPos.New(20, 72),
		buildings = { { "atreides_constructionyard", 0, 0 }, { "atreides_windtrap", 5, 0 }, { "atreides_windtrap", 8, 0 },
			{ "atreides_refinery", 0, 5 }, { "atreides_heavyfactory", 6, 5 } } },
}

Report = function(tag)
	for _, base in ipairs(Bases) do
		local bot = Player.GetPlayer(base.bot)
		local h = #bot.GetActorsByType(base.harvester)
		local r = #bot.GetActorsByType(base.refinery)
		local far = 0
		for _, hv in ipairs(bot.GetActorsByType(base.harvester)) do
			local d = hv.Location - base.origin
			if d.X * d.X + d.Y * d.Y > 25 * 25 then far = far + 1 end
		end
		local owned = 0
		for _, a in ipairs(bot.GetActors()) do if a.Type ~= "player" then owned = owned + 1 end end
		print(tag .. " bot=" .. base.bot .. " tick=" .. DateTime.GameTime .. " harvesters=" .. h .. " refineries=" .. r
			.. " extra=" .. (h - base.free * r) .. " actors=" .. owned .. " far=" .. far .. " cash=" .. bot.Cash)
	end
end

WorldLoaded = function()
	local player = Player.GetPlayer("Player")
	local objective = player.AddPrimaryObjective("Hold until the gate completes.")

	Actor.Create("td_gdi_constructionyard", true, { Owner = player, Location = CPos.New(24, 24) })
	Actor.Create("td_gdi_guardtower", true, { Owner = player, Location = CPos.New(28, 24) })
	Actor.Create("td_gdi_guardtower", true, { Owner = player, Location = CPos.New(24, 28) })

	for _, base in ipairs(Bases) do
		local bot = Player.GetPlayer(base.bot)
		for _, b in ipairs(base.buildings) do
			Actor.Create(b[1], true, { Owner = bot, Location = base.origin + CVec.New(b[2], b[3]) })
		end
		bot.Cash = 10000
	end
	print("AI_HARVESTER_GATE_STARTED")
	Report("AI_HARVESTER_GATE_SAMPLE")

	for _, t in ipairs(SampleTicks) do
		Trigger.AfterDelay(t, function() Report("AI_HARVESTER_GATE_SAMPLE") end)
	end

	Trigger.AfterDelay(SampleTicks[#SampleTicks] + 1, function()
		print("AI_HARVESTER_GATE_COMPLETED tick=" .. DateTime.GameTime)
		player.MarkFailedObjective(objective)
	end)
end
