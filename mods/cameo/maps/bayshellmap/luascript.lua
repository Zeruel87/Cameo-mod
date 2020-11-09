ProtossSquad = { "sczealot", "sczealot", "scdarktemplar", "scdragoon" }
ProtossHeavy = { "scarchon", "scdragoon", "scdragoon", "scdragoon", "scdragoon", "schightemplar" }
CabalSquad = { "tscyborg", "tscyborg", "tscyborg", "tscyborg", "tscyborg", "tscyc2", "tsreaper", "tscyc2", "tsreaper" }
AlliedSquad = { "2tnk", "2tnk", "1tnk", "1tnk", "rajeep", "raarty" }
AlliedInf = { "rae1", "rae1", "rae1", "rae1", "rae1", "rae1", "rae3", "rae3" }
SovietSquad = { "ra2e2", "ra2e2", "ra2e2", "ra2e2", "ra2e2", "ra2e2", "ra2flakt", "ra2flakt", "ra2shk" }
SovietHeavy = { "3tnk", "3tnk", "ftnk", "ltnk", "ltnk", "4tnk" }
AlphaSquad = { "2100mvw", "2100mvw", "2100rvw", "2100rvw", "2100rvw", "2100mch" }
AlphaSquadHeavy = { "2100tch", "2100apt", "2100hpt", "2100tch" }
CitySquad = { "cityfiretruck", "citypolicecar", "tsdoggie", "tsdoggie", "tsdoggie", "tse3", "tse3", "cityambulance" }
CitySWAT = { "citypolicecar", "cityswat", "cityswat" }
JojoChopper = { "scwraith", "scwraith" }
Kirov = { "scbattlecruiser" }
Kilgore = { "raheli", "mh60", "mh60" }
Dred = { "ramsub" }
Carrier = { "sccarrier" }
Reavers = { "screaver", "screaver" }
ShockArmy = { "ra2shk", "ra2shk", "ra2shk", "ra2shk", "ttnk" }

BindActorTriggers = function(a)
	if a.HasProperty("Hunt") then
		Trigger.OnIdle(a, function(a)
			if a.IsInWorld then
				a.Hunt()
			end
		end)
	end
	if a.HasProperty("HasPassengers") then
		Trigger.OnDamaged(a, function()
			if a.HasPassengers then
				a.Stop()
				a.UnloadPassengers()
			end
		end)
	end
end

SendCabalUnits = function(entryCell, unitTypes, interval)
	local units = Reinforcements.Reinforce(cabal, unitTypes, { entryCell }, interval)
	Utils.Do(units, function(unit)
		BindActorTriggers(unit)
	end)
	Trigger.OnAllKilled(units, function() SendCabalUnits(entryCell, unitTypes, interval) end)
end

SendAlliedUnits = function(entryCell, unitTypes, interval)
	local units = Reinforcements.Reinforce(allies, unitTypes, { entryCell }, interval)
	Utils.Do(units, function(unit)
		BindActorTriggers(unit)
	end)
	Trigger.OnAllKilled(units, function() SendAlliedUnits(entryCell, unitTypes, interval) end)
end

SendProtossUnits = function(entryCell, unitTypes, interval)
	local units = Reinforcements.Reinforce(protoss, unitTypes, { entryCell }, interval)
	Utils.Do(units, function(unit)
		BindActorTriggers(unit)
	end)
	Trigger.OnAllKilled(units, function() SendProtossUnits(entryCell, unitTypes, interval) end)
end

SendSovietUnits = function(entryCell, unitTypes, interval)
	local units = Reinforcements.Reinforce(ussr, unitTypes, { entryCell }, interval)
	Utils.Do(units, function(unit)
		BindActorTriggers(unit)
	end)
	Trigger.OnAllKilled(units, function() SendSovietUnits(entryCell, unitTypes, interval) end)
end

Send2100Units = function(entryCell, unitTypes, interval)
	local units = Reinforcements.Reinforce(alpha, unitTypes, { entryCell }, interval)
	Utils.Do(units, function(unit)
		BindActorTriggers(unit)
	end)
	Trigger.OnAllKilled(units, function() Send2100Units(entryCell, unitTypes, interval) end)
end

SendCityUnits = function(entryCell, unitTypes, interval)
	local units = Reinforcements.Reinforce(city, unitTypes, { entryCell }, interval)
	Utils.Do(units, function(unit)
		BindActorTriggers(unit)
	end)
	Trigger.OnAllKilled(units, function() SendCityUnits(entryCell, unitTypes, interval) end)
end

ShuttleDrop = function(entry, hpad)
	local units = Reinforcements.ReinforceWithTransport(protoss, "scshuttle",
		Reavers, { entry.Location, hpad.Location + CVec.New(1, 2) }, { entry.Location })[2]

	Utils.Do(units, function(unit)
		BindActorTriggers(unit)
	end)

	Trigger.AfterDelay(DateTime.Seconds(60), function() ShuttleDrop(entry, hpad) end)
end

ChronoshiftRedUnits = function()
	local cells = Utils.ExpandFootprint({ SovietChrono.Location }, false)
	local units = { }
	for i = 1, #cells do
		local unit = Actor.Create("2100tch", true, { Owner = alpha, Facing = 0 })
		BindActorTriggers(unit)
		units[unit] = cells[i]
	end
	RedChrono.Chronoshift(units)
	Trigger.AfterDelay(DateTime.Seconds(60), ChronoshiftRedUnits)
end

ticks = 1250
speed = 7

Tick = function()
	ticks = ticks + 1
	local t = (ticks + 45) % (360 * speed) * (math.pi / 180) / speed;
	Camera.Position = viewportOrigin + WVec.New(3500 * math.sin(t), 3000 * math.cos(t), 0)
end

WorldLoaded = function()
	cabal = Player.GetPlayer("CABAL")
	allies = Player.GetPlayer("Allies")
	protoss = Player.GetPlayer("Protoss")
	ussr = Player.GetPlayer("Soviets")
	alpha = Player.GetPlayer("Project")
	city = Player.GetPlayer("SimCity")
	viewportOrigin = Camera.Position

	Trigger.AfterDelay(DateTime.Seconds(2), ChronoshiftRedUnits)
	
	SendProtossUnits(entry1.Location, ProtossSquad, 20)
	SendProtossUnits(entry6.Location, ProtossSquad, 20)
	SendProtossUnits(entry2.Location, ProtossHeavy, 20)
	SendCabalUnits(entry1.Location, CabalSquad, 5)
	SendCabalUnits(entry6.Location, CabalSquad, 5)
	SendAlliedUnits(entry2.Location, AlliedSquad, 15)
	SendAlliedUnits(entry1.Location, AlliedInf, 15)
	Send2100Units(entry5.Location, AlphaSquad, 20)
	Send2100Units(entry4.Location, AlphaSquadHeavy, 20)
	SendSovietUnits(entry3.Location, SovietSquad, 15)
	SendSovietUnits(entry4.Location, SovietSquad, 15)
	SendSovietUnits(entry5.Location, SovietHeavy, 20)
	SendSovietUnits(entry4.Location, ShockArmy, 30)
	SendCityUnits(entry3.Location, CitySquad, 10)
	SendCityUnits(entry5.Location, CitySWAT, 10)
	Send2100Units(ChopperEntry.Location, JojoChopper, 30)

	ShuttleDrop(ShuttleEntry, ReaverDrop)
	ShuttleDrop(CarrierEntry, ReaverDrop2)
	Trigger.AfterDelay(DateTime.Seconds(20), function()
		Send2100Units(entry5.Location, Kirov, 50) 
	end)
	Trigger.AfterDelay(DateTime.Seconds(20), function()
		SendProtossUnits(CarrierEntry.Location, Carrier, 50) 
	end)
	Trigger.AfterDelay(DateTime.Seconds(30), function()
		SendSovietUnits(DredEntry.Location, Dred, 60) 
	end)
	SendAlliedUnits(HeliEntry.Location, Kilgore, 30)
end