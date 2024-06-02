
InfantryAllies = {"rae1", "rae1", "rae1", "rae1", "rae1", "rae3", "rae3"}
InfantrySoviets = {"rare1", "rare1", "rare1", "rare1", "rare1", "rare3", "rare3"}
InfantryJapan = {"raje1", "raje1", "raje1", "raje1", "raje1", "raje3", "raje3"}
AlliesVehicles = {"1tnk", "1tnk", "1tnk", "2tnk", "2tnk", "raarty"}
SovietVehicles = {"3tnk", "3tnk", "3tnk", "4tnk", "v2rl"}
JapanVehicles = {"modkubel", "modkubel", "modkubel", "modtypej", "modtypej", "modnano"}

GDIConvoy = {"mtnk", "mtnk", "mtnk", "htnk", "mlrs"}
NodConvoy = {"bike", "bike", "bike", "ltnk", "ltnk", "mssm"}

Ticks = 0
Speed = 5

UnitHunt = function (units)
	Utils.Do(units, function (u)
		Trigger.OnIdle(u, u.Hunt)
	end)
end

WorldLoaded = function ()
	Allies = Player.GetPlayer("Allies")
	Allies.Cash = 99999
	Soviets = Player.GetPlayer("Soviets")
	Soviets.Cash = 99999
	Japan = Player.GetPlayer("Japan")
	Japan.Cash = 99999
	GDI = Player.GetPlayer("GDI")
	Nod = Player.GetPlayer("Nod")
	ViewportOrigin = Camera.Position

	ShellMapCommands()
end

Tick = function ()
	Ticks = Ticks + 1

	local t = (Ticks + 45) % (360 * Speed) * (math.pi / 180) / Speed;
	Camera.Position = ViewportOrigin + WVec.New(19200 * math.sin(t), 20480 * math.cos(t), 0)
end

ShellMapCommands = function ()

	AlliesProduction()
	SovietsProduction()
	JapanProduction()

	Trigger.AfterDelay(DateTime.Seconds(20), GDIConvoyMove)
	Trigger.AfterDelay(DateTime.Seconds(40), NodConvoyMove)

end

GDIConvoyMove = function ()
	local convoy = Reinforcements.Reinforce(GDI, GDIConvoy, {GDIPoint.Location}, 1, function (a)
		a.Move(Center.Location, 1)
		Trigger.OnIdle(a, function (a)
			a.Hunt()
		end)
	end)

	Trigger.OnAllKilled(convoy, function ()
		Trigger.AfterDelay(DateTime.Seconds(30), GDIConvoyMove)
	end)
end

NodConvoyMove = function ()
	local convoy = Reinforcements.Reinforce(Nod, NodConvoy, {NodPoint.Location}, 1, function (a)
		a.Move(Center.Location, 1)
		Trigger.OnIdle(a, function (a)
			a.Hunt()
		end)
	end)

	Trigger.OnAllKilled(convoy, function ()
		Trigger.AfterDelay(DateTime.Seconds(30), NodConvoyMove)
	end)
end

AlliesProduction = function ()
	if not AlliesFact.IsProducing("1tnk") then
		AlliesFact.Build(AlliesVehicles, UnitHunt)
	end

	if not AlliesBar.IsProducing("rae1") then
		AlliesBar.Build(InfantryAllies, UnitHunt)
	end

	Utils.Do(Utils.Where(Allies.GetActors(), function (a)
		return a.HasProperty("StartBuildingRepairs") and a.Health < a.MaxHealth * 0.75
	end), function (a)
		a.StartBuildingRepairs(Allies)
	end)

	Trigger.AfterDelay(DateTime.Seconds(10), AlliesProduction)
end

SovietsProduction = function ()
	if not SovietsFact.IsProducing("3tnk") then
		SovietsFact.Build(SovietVehicles, UnitHunt)
	end

	if not SovietsBar.IsProducing("rare1") then
		SovietsBar.Build(InfantrySoviets, UnitHunt)
	end

	Utils.Do(Utils.Where(Soviets.GetActors(), function (a)
		return a.HasProperty("StartBuildingRepairs") and a.Health < a.MaxHealth * 0.75
	end), function (a)
		a.StartBuildingRepairs(Soviets)
	end)

	Trigger.AfterDelay(DateTime.Seconds(10), SovietsProduction)
end

JapanProduction = function ()
	if not JapanFact.IsProducing("modkubel") then
		JapanFact.Build(JapanVehicles, UnitHunt)
	end

	if not JapanBar.IsProducing("rare1") then
		JapanBar.Build(InfantryJapan, UnitHunt)
	end

	Utils.Do(Utils.Where(Japan.GetActors(), function (a)
		return a.HasProperty("StartBuildingRepairs") and a.Health < a.MaxHealth * 0.75
	end), function (a)
		a.StartBuildingRepairs(Japan)
	end)

	Trigger.AfterDelay(DateTime.Seconds(10), JapanProduction)
end

