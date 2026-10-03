WorldLoaded = function()
	local player = Player.GetPlayer("Player")
	local bot = Player.GetPlayer("HardBot")
	local objective = player.AddPrimaryObjective("Hold until the gate completes.")

	Actor.Create("td_gdi_constructionyard", true, { Owner = player, Location = CPos.New(24, 24) })
	Actor.Create("td_gdi_guardtower", true, { Owner = player, Location = CPos.New(28, 24) })
	Actor.Create("td_gdi_guardtower", true, { Owner = player, Location = CPos.New(24, 28) })
	Actor.Create("td_gdi_battletank", true, { Owner = player, Location = CPos.New(28, 28) })
	Actor.Create("td_gdi_battletank", true, { Owner = player, Location = CPos.New(30, 28) })
	Actor.Create("ts_gdi_tiberiumrefinery", true, { Owner = player, Location = CPos.New(36, 36) })
	Actor.Create("ts_gdi_tiberiumharvester", true, { Owner = player, Location = CPos.New(38, 36) })
	Actor.Create("ts_gdi_tiberiumharvester", true, { Owner = player, Location = CPos.New(38, 38) })
	Actor.Create("td_nod_constructionyard", true, { Owner = bot, Location = CPos.New(90, 90) })
	Actor.Create("td_nod_mobileconstructionvehicle", true, { Owner = bot, Location = CPos.New(44, 44) })
	-- An army that must form at least one attack squad. The mix includes
	-- ts_nod_attackbuggy on purpose: it carries AttackFrontal + AttackFollow,
	-- the exact multi-AttackBase unit that crashed #554 (fixed in #555).
	local army = { "ts_nod_attackbuggy", "td_nod_buggy", "td_nod_buggy", "td_nod_lighttank",
		"td_nod_lighttank", "td_nod_lighttank", "td_nod_artillery", "td_nod_flametank" }
	for i, unit in ipairs(army) do
		Actor.Create(unit, true, { Owner = bot, Location = CPos.New(86 + (i % 4), 86 + math.floor(i / 4)) })
	end

	-- A scout next to the enemy refinery keeps a visible Raid target alive so
	-- the gate does not depend on the fogged-scan fallback having fired.
	Actor.Create("td_nod_buggy", true, { Owner = bot, Location = CPos.New(36, 40) })

	print("AI_RAID_GATE_STARTED bot=HardBot type=hard")

	-- mission_assignment is only recorded when a Rush squad is created against
	-- an already-published Raid mission. The starting army can exhaust the
	-- squad queue before the strategist publishes, so a second wave lands
	-- mid-window: sized above every personality's MaxIdleUnits to force the
	-- attack-force trigger regardless of its random tick.
	local wave2 = {}
	for i = 1, 16 do
		wave2[i] = "td_nod_lighttank"
	end
	Trigger.AfterDelay(450, function()
		for i, unit in ipairs(wave2) do
			Actor.Create(unit, true, { Owner = bot, Location = CPos.New(86 + (i % 4), 88 + math.floor(i / 4)) })
		end
	end)

	-- A third wave gives a second post-publication formation chance if the
	-- first still raced the strategist's scan cadence.
	Trigger.AfterDelay(700, function()
		for i, unit in ipairs(wave2) do
			Actor.Create(unit, true, { Owner = bot, Location = CPos.New(80 + (i % 4), 88 + math.floor(i / 4)) })
		end
	end)

	-- Squads must have formed well before this fires (force interval 50t,
	-- 1400 ticks leaves margin for two formation waves plus scouting.
	Trigger.AfterDelay(1400, function()
		print("AI_RAID_GATE_COMPLETED bot=HardBot tick=" .. DateTime.GameTime)
		player.MarkFailedObjective(objective)
	end)
end
