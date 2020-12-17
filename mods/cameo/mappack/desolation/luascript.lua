ProducedUnitTypes = {
	{ factory = SovietBarracks, types = { "ra2e2", "ra2flakt", "ra2ivan", "ra2shk" } },
	{ factory = TerranBarracks, types = { "scmarine", "scfirebat" } },
	{ factory = TerranBarracks2, types = { "scmarine", "scfirebat" } },
	{ factory = NodBarracks, types = { "e1", "e3", "e4", "e5" } },
	{ factory = ChinaBarracks, types = { "che1", "che2", "che3" } },
	{ factory = ChinaBarracks2, types = { "che1", "che2", "che3" } },
	{ factory = TerranFactory, types = { "scgoliath", "scvulture" } },
	{ factory = ChinaFactory, types = { "chbattle", "choverlord", "chgtnk" } },
	{ factory = NodFactory, types = { "ltnk", "arty", "bggy", "ftnk", "bike" } }
}

GLAUnitTypes = { "gle1", "gle1", "gle3", "gle3", "glpickup", "glpickup", "glquad", "glquad", "glbggy" }

AlliesUnitTypes = { "rae1", "rae1", "rae1", "rae1", "rae3", "rae3", "rae3", "rajeep", "2tnk", "2tnk", "raarty" }

AlliesUnitTypes2 = { "ctnk", "ctnk", "ctnk" }

USAUnitTypes = { "usacrusader", "usacrusader2", "usapala", "usacomanche" }

ChineseUnitTypes = { "che1", "che1", "che1", "che3", "che3", "che3", "chbattle", "chbattle", "chgtnk", "chgtnk" }

ZergUnitTypes = { "sczergling", "sczergling", "sczergling", "sczergling", "sczergling", "sczergling", "schydralisk", "schydralisk", "schydralisk" }

CABALUnitTypes = { "tscyborg", "tscyborg", "tscyborg", "tscyborg", "tscyc2", "tsreaper" }

SovietUnitTypes = { "ra2deso", "ra2shk", "ra2shk", "ra2e2", "ra2e2", "ra2flakt", "ra2flakt", "ra2e2", "ra2e2", "ra2e2", "yrboris" }

SovietUnitTypes2 = { "3tnk", "3tnk", "3tnk", "ttnk", "4tnk", "v2rl" }

GDIUnitTypes = { "tse1", "tse1", "tse2", "tse2", "tssmech", "tssmech", "tsmmch" }

TerranAirTypes = { "scwraith", "scwraith", "scwraith" }

NodAirTypes = { "heli", "heli" }

AlliesNavalTypes = { "raca" }

Reavers = { "screaver", "scdarktemplar", "scdarktemplar" }

TerranDrop = { "scmarine", "scmarine", "scmarine", "scmarine", "scghost", "scfirebat", "scfirebat", "scmedic" }

BomberWaypoints = { Bomber1, Bomber2, Bomber3, Bomber4 }

BindActorTriggers = function(a)
	if a.HasProperty("Hunt") then
		Trigger.OnIdle(a, function(a)
			if a.IsInWorld then
				a.Hunt()
			end
		end)
	end
	if a.HasProperty("HasPassengers") then
		Trigger.OnPassengerExited(a, function(t, p)
			BindActorTriggers(p)
		end)
		
		Trigger.OnDamaged(a, function()
			if a.HasPassengers then
				a.Stop()
				a.UnloadPassengers()
			end
		end)
	end
end

SendBlueUnits = function(entryCell, unitTypes, interval)
	local units = Reinforcements.Reinforce(blue, unitTypes, { entryCell }, interval)
	Utils.Do(units, function(unit)
		BindActorTriggers(unit)
	end)
	Trigger.OnAllKilled(units, function() SendBlueUnits(entryCell, unitTypes, interval) end)
end

SendRedUnits = function(entryCell, unitTypes, interval)
	local units = Reinforcements.Reinforce(red, unitTypes, { entryCell }, interval)
	Utils.Do(units, function(unit)
		BindActorTriggers(unit)
	end)
	Trigger.OnAllKilled(units, function() SendRedUnits(entryCell, unitTypes, interval) end)
end

ShuttleDrop = function(entry, hpad)
	local units = Reinforcements.ReinforceWithTransport(blue, "scshuttle",
		Reavers, { entry.Location, hpad.Location + CVec.New(1, 2) }, { entry.Location })[2]

	Utils.Do(units, function(unit)
		BindActorTriggers(unit)
	end)

	Trigger.AfterDelay(DateTime.Seconds(60), function() ShuttleDrop(entry, hpad) end)
end

DropshipDrop = function(entry, hpad)
	local units = Reinforcements.ReinforceWithTransport(red, "scdropship",
		TerranDrop, { entry.Location, hpad.Location + CVec.New(1, 2) }, { entry.Location })[2]

	Utils.Do(units, function(unit)
		BindActorTriggers(unit)
	end)

	Trigger.AfterDelay(DateTime.Seconds(60), function() DropshipDrop(entry, hpad) end)
end

ChronoshiftRedUnits = function()
	local cells = Utils.ExpandFootprint({ SovietChrono.Location }, false)
	local units = { }
	for i = 1, #cells do
		local unit = Actor.Create("scgoliath", true, { Owner = red, Facing = 0 })
		BindActorTriggers(unit)
		units[unit] = cells[i]
	end
	RedChrono.Chronoshift(units)
	Trigger.AfterDelay(DateTime.Seconds(90), ChronoshiftRedUnits)
end

SendBombers = function(waypoints)
	local bomberEntryPath = { waypoints[1].Location, waypoints[2].Location }
	local bombers = Reinforcements.Reinforce(blue, { "usaraptor" }, bomberEntryPath, 4)
	Utils.Do(bombers, function(bomber)
		bomber.Move(waypoints[3].Location)
		bomber.Move(waypoints[4].Location)
		bomber.Destroy()
	end)

	Trigger.AfterDelay(DateTime.Seconds(40), function() SendBombers(waypoints) end)
end

SetupUnits = function()
	Utils.Do(Map.NamedActors, function(a)
		if a.HasProperty("AcceptsCondition") and a.AcceptsCondition("unkillable") then
			a.GrantCondition("unkillable")
			a.Stance = "Defend"
		end
	end)
end

SetupFactories = function()
	Utils.Do(ProducedUnitTypes, function(production)
		Trigger.OnProduction(production.factory, function(_, a) BindActorTriggers(a) end)
	end)
end

ProduceUnits = function(t)
	local factory = t.factory
	if not factory.IsDead then
		local unitType = t.types[Utils.RandomInteger(1, #t.types + 1)]
		factory.Wait(Actor.BuildTime(unitType))
		factory.Produce(unitType)
		factory.CallFunc(function() ProduceUnits(t) end)
	end
end

ticks = 1250
speed = 7

Tick = function()
	ticks = ticks + 1
	local t = (ticks + 45) % (360 * speed) * (math.pi / 180) / speed;
	Camera.Position = viewportOrigin + WVec.New(13000 * math.sin(t), 27000 * math.cos(t), 0)
end

WorldLoaded = function()
	blue = Player.GetPlayer("Blues")
	red = Player.GetPlayer("Reds")
	viewportOrigin = Camera.Position

	SetupUnits()
	SetupFactories()
	Utils.Do(ProducedUnitTypes, ProduceUnits)

	Trigger.AfterDelay(DateTime.Seconds(30), ChronoshiftRedUnits)

	ShuttleDrop(Bomber4, ReaverDrop)
	ShuttleDrop(CarrierEntry, ReaverDrop2)
	DropshipDrop(ShuttleEntry, TerranDropPoint)

	SendRedUnits(SovietEntry1.Location, GLAUnitTypes, 30)
	SendRedUnits(SovietEntry1.Location, SovietUnitTypes, 50)
	
	Trigger.AfterDelay(DateTime.Seconds(30), function()
		SendBombers(BomberWaypoints) 
		SendRedUnits(TerranEntry2.Location, GDIUnitTypes, 50)
		SendRedUnits(TerranEntry.Location, SovietUnitTypes2, 20)
	end)

	SendRedUnits(TerranEntry2.Location, TerranAirTypes, 50)

	SendBlueUnits(AlliesEntry.Location, AlliesUnitTypes, 20)
	SendBlueUnits(AlliesEntry.Location, CABALUnitTypes, 20)

	SendBlueUnits(ChineseEntry1.Location, ChineseUnitTypes, 50)
	Trigger.AfterDelay(DateTime.Seconds(60), function()
		SendBlueUnits(ChineseEntry2.Location, ChineseUnitTypes, 40)
		SendBlueUnits(ChineseEntry2.Location, NodAirTypes, 100)
		SendBlueUnits(AlliesEntry2.Location, USAUnitTypes, 40)
	end)
end