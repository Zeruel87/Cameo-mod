-- One shot per lane; no upgrades, AI, movement or damage modifiers.
-- Shield lanes test the armor coefficient, not a regenerating shield pool.
local lanes = { "legacy_light", "legacy_medium", "legacy_heavy", "h0", "h1000", "h2000", "shield_h0", "shield_h1000", "shield_h2000", "tankkiller", "warriortank", "warriorturret" }
local weapons = { "legacy_light", "legacy_medium", "legacy_heavy", "h0", "h1000", "h2000", "h0", "h1000", "h2000", "tankkiller", "warriortank", "warriorturret" }
local expected = { 3860, 4560, 4660, 2720, 3960, 5520, 2880, 6480, 11520, 40800, 54400, 65280 }
local targets = {}
local shooters = {}
local hits = {}
local freedom = {}
WorldLoaded = function()
	Camera.Position = Map.CenterOfCell(CPos.New(24, 42))
	local a = Player.GetPlayer("SideA")
	local b = Player.GetPlayer("SideB")
	for i, spec in ipairs({ {0, false, 108000}, {16, false, 81000}, {32, false, 54000},
		{33, false, 0}, {16, true, 40500}, {17, true, 0} }) do
		local pair = { expected = spec[3], distance = spec[1], ally = spec[2] }
		for j, kind in ipairs({ "old", "new" }) do
			local x, y = 8 + (i - 1) * 14, 80 + j * 6
			local target = Actor.Create("probe_distance_" .. spec[1], true,
				{ Owner = spec[2] and a or b, Location = CPos.New(x, y) })
			local shooter = Actor.Create("probe_freedom_" .. kind, true,
				{ Owner = a, Location = CPos.New(x - 3, y) })
			local events = {}
			local aim = Actor.Create("probe_aim", true, { Owner = b, Location = CPos.New(x, y) })
			pair[kind] = { target = target, aim = aim, shooter = shooter, events = events }
			Trigger.OnDamaged(target, function(self, attacker, damage)
				table.insert(events, damage)
			end)
		end
		table.insert(freedom, pair)
	end
	for i, label in ipairs(lanes) do
		local forgotten = i > 9
		local shield = i > 6 and not forgotten
		local y = 12 + (forgotten and i - 9 or shield and i - 6 or i) * 11
		local x = forgotten and 80 or shield and 52 or 24
		local target = Actor.Create(shield and "probe_target_shield" or "probe_target", true, { Owner = b, Location = CPos.New(x, y) })
		local shooter = Actor.Create("probe_" .. weapons[i], true, { Owner = a, Location = CPos.New(x - 3, y) })
		targets[i] = target
		shooters[i] = shooter
		hits[i] = 0
		Trigger.OnDamaged(target, function(self, attacker, damage)
			hits[i] = hits[i] + 1
			print("HEAVINESS_HIT lane=" .. label .. " damage=" .. damage)
		end)
	end
	print("HEAVINESS_PROBE_STARTED lanes=12 boundary_pairs=6 armor=Medium_and_Shield hp=1000000 mode=SharedVersus")
	Trigger.AfterDelay(25, function()
		for i, shooter in ipairs(shooters) do
			shooter.Attack(targets[i], false, true)
		end
		for _, pair in ipairs(freedom) do
			for _, kind in ipairs({ "old", "new" }) do
				pair[kind].shooter.Attack(pair[kind].aim, false, true)
			end
		end
	end)
	Trigger.AfterDelay(100, function()
		local passed = true
		local exact = true
		for i, target in ipairs(targets) do
			local lost = target.MaxHealth - target.Health
			print("HEAVINESS_RESULT lane=" .. lanes[i] .. " lost=" .. lost .. " expected=" .. expected[i] .. " events=" .. hits[i])
			if lost <= 0 or hits[i] == 0 then passed = false end
			if lost ~= expected[i] then exact = false end
			shooters[i].Destroy()
		end
		for _, pair in ipairs(freedom) do
			local old = pair.old.events[2] or 0
			local new = pair.new.target.MaxHealth - pair.new.target.Health
			print("FREEDOM_BOUNDARY distance=" .. pair.distance .. " ally=" .. tostring(pair.ally) ..
				" old=" .. old .. " new=" .. new .. " expected=" .. pair.expected)
			if old ~= pair.expected or new ~= pair.expected then exact = false end
			pair.old.shooter.Destroy()
			pair.new.shooter.Destroy()
		end
		print("HEAVINESS_PROBE_COMPLETED all_lanes_hit=" .. tostring(passed) .. " all_expected=" .. tostring(exact))
		Media.DisplayMessage("Heaviness probe complete; measurements are in lua.log.", "Probe")
	end)
end
