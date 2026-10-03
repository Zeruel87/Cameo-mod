WorldLoaded = function()
	local player = Player.GetPlayer("Player")
	local bot = Player.GetPlayer("HardBot")
	local objective = player.AddPrimaryObjective("Hold until the gate completes.")

	Actor.Create("td_gdi_constructionyard", true, { Owner = player, Location = CPos.New(24, 24) })
	Actor.Create("td_gdi_guardtower", true, { Owner = player, Location = CPos.New(28, 24) })
	Actor.Create("td_gdi_guardtower", true, { Owner = player, Location = CPos.New(24, 28) })
	Actor.Create("td_gdi_battletank", true, { Owner = player, Location = CPos.New(28, 28) })
	Actor.Create("td_gdi_battletank", true, { Owner = player, Location = CPos.New(30, 28) })

	Actor.Create("td_nod_constructionyard", true, { Owner = bot, Location = CPos.New(72, 72) })
	-- An army that must form at least one attack squad. The mix includes
	-- ts_nod_attackbuggy on purpose: it carries AttackFrontal + AttackFollow,
	-- the exact multi-AttackBase unit that crashed #554 (fixed in #555).
	local army = { "ts_nod_attackbuggy", "td_nod_buggy", "td_nod_buggy", "td_nod_lighttank",
		"td_nod_lighttank", "td_nod_lighttank", "td_nod_artillery", "td_nod_flametank" }
	for i, unit in ipairs(army) do
		Actor.Create(unit, true, { Owner = bot, Location = CPos.New(68 + (i % 4), 68 + math.floor(i / 4)) })
	end
	print("AI_SQUAD_GATE_STARTED bot=HardBot type=hard")

	-- Hard's MAIN army waits BotLimits@hard InitialAttackDelay = 3750 ticks (DESIGN §19.1, 2026-09-28);
	-- guerrilla squads may form earlier but at random. 5000 = that delay + the force interval and
	-- snapshot cadence, so the attack squad this gate exists for has certainly had its chance.
	Trigger.AfterDelay(5000, function()
		print("AI_SQUAD_GATE_COMPLETED bot=HardBot tick=" .. DateTime.GameTime)
		player.MarkFailedObjective(objective)
	end)
end
