local thresholdCases = {}
local reloadCases = {}
local thresholdDone = false
local reloadDone = false
local carrierDone = false
local gateStarted = false
local gateFinished = false
local gatePass = true
local startTick = 0
local pauseToken = nil
local carrier = nil
local carrierTarget = nil
local carrierSlave = nil
local carrierPhase = "waiting"
local carrierDepleted = false
local carrierReturnedTick = nil

local Fail = function(message)
	gatePass = false
	print("R8_RUNTIME_FAIL tick=" .. DateTime.GameTime .. " message=" .. message)
end

local SetAmmo = function(actor, amount)
	actor.Reload("primary", -actor.MaximumAmmoCount("primary"))
	if amount > 0 then actor.Reload("primary", amount) end
end

local Spawn = function(kind, owner, x, y)
	return Actor.Create(kind, true, { Owner = owner, Location = CPos.New(x, y) })
end

local AddThresholdCase = function(label, kind, target, blockedAmmo, fundedAmmo, expectedProbe, x, y)
	local actor = Spawn(kind, Player.GetPlayer("SideA"), x, y)
	table.insert(thresholdCases, {
		label = label,
		actor = actor,
		target = target,
		blockedAmmo = blockedAmmo,
		fundedAmmo = fundedAmmo,
		expectedProbe = expectedProbe,
		probeStart = actor.AmmoCount("probe")
	})
end

local AddReloadCase = function(label, kind, delay, count, capacity, x, y)
	local actor = Spawn(kind, Player.GetPlayer("SideA"), x, y)
	table.insert(reloadCases, {
		label = label,
		actor = actor,
		delay = delay,
		count = count,
		capacity = capacity,
		last = capacity,
		events = {},
		enabledStart = nil,
		secondStart = nil
	})
end

local ValidateInitialReload = function(case)
	local expectedEvents = case.capacity / case.count
	if #case.events ~= expectedEvents then
		Fail(case.label .. " refill event count " .. #case.events .. " expected " .. expectedEvents)
		return
	end
	if case.actor.AmmoCount("primary") ~= case.capacity then
		Fail(case.label .. " did not refill to capacity")
	end
	if case.events[1].tick - case.enabledStart ~= case.delay + 1 then
		Fail(case.label .. " first refill delay was " .. (case.events[1].tick - case.enabledStart))
	end
	for i = 2, #case.events do
		if case.events[i].tick - case.events[i - 1].tick ~= case.delay then
			Fail(case.label .. " refill interval changed at event " .. i)
		end
		if case.events[i].ammo - case.events[i - 1].ammo ~= case.count then
			Fail(case.label .. " refill count changed at event " .. i)
		end
	end
	print("R8_RELOAD_INITIAL lane=" .. case.label .. " events=" .. #case.events ..
		" first_delay=" .. (case.events[1].tick - case.enabledStart) .. " full_tick=" .. case.events[#case.events].tick)
end

local BeginGate = function()
	startTick = DateTime.GameTime
	gateStarted = true
	print("R8_RUNTIME_GATE_STARTED tick=" .. startTick .. " head=f60681e74")

	for _, case in ipairs(thresholdCases) do
		SetAmmo(case.actor, case.blockedAmmo)
		case.probeStart = case.actor.AmmoCount("probe")
		case.actor.Attack(case.target, false, true)
	end

	for _, case in ipairs(reloadCases) do
		SetAmmo(case.actor, 0)
		case.last = 0
		case.enabledStart = startTick
	end

	pauseToken = reloadCases[1].actor.GrantCondition("probe_pause")
	reloadCases[1].enabledStart = nil
	carrier.Attack(carrierTarget, false, true)

	Trigger.AfterDelay(25, function()
		if reloadCases[1].actor.AmmoCount("primary") ~= 0 then
			Fail("A10 reload advanced while probe_pause was active")
		end
		reloadCases[1].actor.RevokeCondition(pauseToken)
		reloadCases[1].enabledStart = DateTime.GameTime
		print("R8_RELOAD_UNPAUSED lane=a10 tick=" .. DateTime.GameTime)
	end)

	Trigger.AfterDelay(50, function()
		for _, case in ipairs(thresholdCases) do
			local spent = case.probeStart - case.actor.AmmoCount("probe")
			print("R8_BLOCKED lane=" .. case.label .. " ammo=" .. case.blockedAmmo .. " probe_spent=" .. spent)
			if spent ~= 0 then Fail(case.label .. " fired while below AmmoUsage") end
			case.actor.Stop()
			SetAmmo(case.actor, case.fundedAmmo)
			case.probeFundedStart = case.actor.AmmoCount("probe")
			case.actor.Attack(case.target, false, true)
		end
	end)

	Trigger.AfterDelay(110, function()
		for _, case in ipairs(thresholdCases) do
			local spent = case.probeFundedStart - case.actor.AmmoCount("probe")
			print("R8_FUNDED lane=" .. case.label .. " ammo=" .. case.fundedAmmo .. " probe_spent=" .. spent)
			if spent ~= case.expectedProbe then
				Fail(case.label .. " funded control spent " .. spent .. " expected " .. case.expectedProbe)
			end
			if case.actor.AmmoCount("primary") ~= 0 then
				Fail(case.label .. " funded control did not stop at empty")
			end
		end
		thresholdDone = true
	end)

	Trigger.AfterDelay(145, function()
		for _, case in ipairs(reloadCases) do ValidateInitialReload(case) end
	end)

	Trigger.AfterDelay(160, function()
		for _, case in ipairs(reloadCases) do
			case.secondEventIndex = #case.events
			case.actor.Reload("primary", -case.count)
			case.last = case.actor.AmmoCount("primary")
			case.secondStart = DateTime.GameTime
		end
	end)

	Trigger.AfterDelay(161, function()
		for _, case in ipairs(reloadCases) do
			if case.actor.AmmoCount("primary") == case.capacity then
				Fail(case.label .. " reused elapsed full-pool time")
			end
		end
	end)

	Trigger.AfterDelay(190, function()
		for _, case in ipairs(reloadCases) do
			local event = case.events[case.secondEventIndex + 1]
			if event == nil then
				Fail(case.label .. " did not refill after second drain")
			elseif event.tick - case.secondStart ~= case.delay + 1 then
				Fail(case.label .. " second refill delay was " .. (event.tick - case.secondStart))
			end
			if case.actor.AmmoCount("primary") ~= case.capacity then
				Fail(case.label .. " second refill did not stop at capacity")
			end
		end
		reloadDone = true
	end)

	Trigger.AfterDelay(1200, function()
		if not gateFinished then
			Fail("timeout threshold=" .. tostring(thresholdDone) .. " reload=" .. tostring(reloadDone) ..
				" carrier=" .. tostring(carrierDone) .. " carrier_phase=" .. carrierPhase)
			print("R8_RUNTIME_GATE_COMPLETED pass=false")
			gateFinished = true
		end
	end)
end

WorldLoaded = function()
	Camera.Position = Map.CenterOfCell(CPos.New(48, 45))
	local sideA = Player.GetPlayer("SideA")
	local sideB = Player.GetPlayer("SideB")
	local gunTarget = Spawn("probe_target_ground", sideB, 70, 10)
	local bombTarget = Spawn("probe_target_ground", sideB, 70, 20)
	local interceptorTarget = Spawn("probe_target_ground", sideB, 70, 30)
	local japanTarget = Spawn("probe_target_ground", sideB, 70, 40)
	local air = Spawn("probe_target_air", sideB, 70, 70)
	carrierTarget = Spawn("probe_target_ground", sideB, 30, 80)

	AddThresholdCase("a10_gun_empty", "probe_a10_gun", gunTarget, 0, 1, 1, 64, 10)
	AddThresholdCase("a10_bomb", "probe_a10_bomb", bombTarget, 9, 10, 10, 68, 20)
	AddThresholdCase("a10_aa", "probe_a10_aa", air, 4, 5, 5, 66, 70)
	AddThresholdCase("interceptor", "probe_interceptor", interceptorTarget, 0, 1, 1, 64, 30)
	AddThresholdCase("usage12_contract", "probe_usage12_contract", japanTarget, 11, 12, 12, 68, 40)

	AddReloadCase("a10", "probe_a10_reload", 5, 1, 20, 10, 10)
	AddReloadCase("interceptor", "probe_interceptor_reload", 25, 1, 4, 10, 20)
	AddReloadCase("japan", "probe_japan_reload", 25, 9, 36, 10, 30)

	carrier = Spawn("probe_supercarrier", sideA, 24, 80)
	Trigger.AfterDelay(20, BeginGate)
end

Tick = function()
	if not gateStarted or gateFinished then return end

	for _, case in ipairs(reloadCases) do
		local ammo = case.actor.AmmoCount("primary")
		if ammo ~= case.last then
			table.insert(case.events, { tick = DateTime.GameTime, ammo = ammo })
			print("R8_RELOAD_EVENT lane=" .. case.label .. " tick=" .. DateTime.GameTime .. " ammo=" .. ammo)
			case.last = ammo
		end
	end

	if carrierSlave == nil then
		for _, actor in ipairs(Map.ActorsInWorld) do
			if actor.Type == "probe_real_a10" then
				carrierSlave = actor
				carrierPhase = "deployed"
				print("R8_CARRIER_LAUNCHED tick=" .. DateTime.GameTime .. " ammo=" .. actor.AmmoCount("primary"))
				actor.Reload("reentry_probe", -actor.MaximumAmmoCount("reentry_probe"))
				break
			end
		end
	elseif carrierPhase == "deployed" then
		if carrierSlave.IsInWorld then
			local ammo = carrierSlave.AmmoCount("primary")
			if ammo < carrierSlave.MaximumAmmoCount("primary") then carrierDepleted = true end
		else
			if not carrierDepleted then Fail("carrier slave returned without spending ammo") end
			carrierPhase = "returned"
			carrierReturnedTick = DateTime.GameTime
			print("R8_CARRIER_RETURNED tick=" .. DateTime.GameTime)
		end
	elseif carrierPhase == "returned" then
		if DateTime.GameTime % 25 == 0 then carrier.Attack(carrierTarget, false, true) end
		if carrierSlave.IsInWorld then
			local primaryAmmo = carrierSlave.AmmoCount("primary")
			local probeAmmo = carrierSlave.AmmoCount("reentry_probe")
			print("R8_CARRIER_RELAUNCHED tick=" .. DateTime.GameTime .. " primary_ammo=" .. primaryAmmo .. " probe=" .. probeAmmo)
			if primaryAmmo ~= carrierSlave.MaximumAmmoCount("primary") then
				Fail("carrier re-entry did not refill the primary pool")
			end
			if probeAmmo ~= carrierSlave.MaximumAmmoCount("reentry_probe") then
				Fail("carrier re-entry did not refill the observer pool")
			end
			if DateTime.GameTime - carrierReturnedTick < 125 then
				Fail("carrier relaunched before the authored 125-tick rearm interval")
			end
			carrierDone = true
			carrierPhase = "complete"
		end
	end

	if thresholdDone and reloadDone and carrierDone and not gateFinished then
		print("R8_RUNTIME_GATE_COMPLETED pass=" .. tostring(gatePass))
		Media.DisplayMessage("R8 carrier-ammo runtime gate complete: " .. tostring(gatePass), "Gate")
		gateFinished = true
	end
end
