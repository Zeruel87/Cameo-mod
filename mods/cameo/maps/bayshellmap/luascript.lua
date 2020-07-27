ProducedUnitTypes =
{
	{ factory = NodRax, types = { "e1", "e3", "e5", "e4" } },
	{ factory = NodAirstrip, types = { "bggy", "bike", "ltnk", "ftnk", "arty" } },
	{ factory = NodHelipad, types = { "heli" } },
	{ factory = CityPD, types = { "citypoliceofficer", "citypolicecar" } },
	{ factory = CityFD, types = { "cityfirefighter", "cityambulance", "cityfiretruck" } },
	{ factory = CityFD2, types = { "cityfirefighter", "cityambulance", "cityfiretruck" } },
	{ factory = ZergHive1, types = { "sczergling", "schydralisk" } },
	{ factory = ZergHive2, types = { "sczergling", "schydralisk", "scultralisk", "scmutalisk", "scguardian", "scinfestedterran" } },
	{ factory = ZergHive3, types = { "sczergling", "schydralisk", "scmutalisk" } },
	{ factory = ZergHive4, types = { "sczergling" } },
	{ factory = ZergHive5, types = { "sczergling" } },
	{ factory = SovietWF, types = { "ra2htnk", "ra2apoc", "ra2v3", "ra2htk", "ra2ttnk", "yrschp", "ra2zep", "ra2dron" } },
	{ factory = SovietRax, types = { "ra2e2", "ra2flakt", "ra2dog", "ra2shk", "ra2deso" } },
	{ factory = SovietShipyard, types = { "ra2dred", "ra2hyd"} },
	{ factory = GDIWF, types = { "tsmmch", "tssmech", "tsapc", "tsjugg", "tssonic", "tshvr" } },
	{ factory = GDIRax, types = { "tse1", "tse2", "tsjumpjet2", "tssonic" } },
	{ factory = GDIHelipad, types = { "tsorcab", "tsorca" } },
	{ factory = ChopShop1, types = { "2100scav", "2100trike", "2100jeep", "2100jeepmsl" } },
	{ factory = ChopShop2, types = { "2100scav", "2100trike", "2100jeep", "2100jeepmsl", "2100camper", "2100tractor" } },
	{ factory = ChopShop3, types = { "2100bus", "2100ftruk", "2100scavtruck", "2100icecream" } }
}

ProduceUnits = function(t)
	local factory = t.factory
	if not factory.IsDead then
		local unitType = t.types[Utils.RandomInteger(1, #t.types + 1)]
		factory.Wait(Actor.BuildTime(unitType))
		factory.Produce(unitType)
		factory.CallFunc(function() ProduceUnits(t) end)
	end
end

SetupFactories = function()
	Utils.Do(ProducedUnitTypes, function(production)
		Trigger.OnProduction(production.factory, function(_, a) BindActorTriggers(a) end)
	end)
end

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

SetCash = function()
	city.Cash = 100000
	nod.Cash = 100000
	ussr.Cash = 100000
	zerg.Cash = 100000
	scav.Cash = 100000
	gdi.Cash = 100000
	city.Resources = 10000000
	nod.Resources = 10000000
	ussr.Resources = 10000000
	zerg.Resources = 10000000
	scav.Resources = 10000000
	gdi.Resources = 10000000
end

SetWaypoints = function()
	ZergHive1.RallyPoint = ZergRally.Location
	ZergHive2.RallyPoint = ZergRally.Location
	ZergHive3.RallyPoint = ZergRally.Location
	ZergHive4.RallyPoint = ZergRally.Location
	CityPD.RallyPoint = CityRally.Location
	CityFD.RallyPoint = CityRally.Location
	CityFD2.RallyPoint = CityRally.Location
	NodAirstrip.RallyPoint = NodWFRally.Location
	NodRax.RallyPoint = NodRaxRally.Location
	NodHelipad.RallyPoint = NodHeliRally.Location
	SovietRax.RallyPoint = SovietRaxRally.Location
	SovietWF.RallyPoint = SovietWFRally.Location
	SovietShipyard.RallyPoint = SovietShipRally.Location
	GDIRax.RallyPoint = GDIRaxRally.Location
	GDIWF.RallyPoint = GDIWFRally.Location
	GDIHelipad.RallyPoint = GDIHeliRally.Location
	ChopShop1.RallyPoint = ScavRally.Location
	ChopShop2.RallyPoint = ScavRally.Location
	ChopShop3.RallyPoint = ScavRally.Location
end

ticks = 1250
speed = 7

Tick = function()
	ticks = ticks + 1
	local t = (ticks + 45) % (360 * speed) * (math.pi / 180) / speed;
	Camera.Position = viewportOrigin + WVec.New(19200 * math.sin(t), 46080 * math.cos(t), 0)
end

WorldLoaded = function()
	city = Player.GetPlayer("SimCity")
	nod = Player.GetPlayer("Nod")
	ussr = Player.GetPlayer("Soviets")
	zerg = Player.GetPlayer("Zerg")
	scav = Player.GetPlayer("Scavengers")
	gdi = Player.GetPlayer("GDI")
	viewportOrigin = Camera.Position
	
	SetCash()
	SetWaypoints()
	SetupFactories()
	Utils.Do(ProducedUnitTypes, ProduceUnits)
end
