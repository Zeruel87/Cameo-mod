--[[ Copyright 2021 by SteamsDev
    made for map purposes ONLY
]]

ChronoReinforcementsOne = { "rajeep", "rajeep", "2tnk", "2tnk", "arty" }
ChronoReinforcementsTwo = { "ra2mtnk", "ra2mtnk", "ra2fv", "ra2fv", "ra2sref" }
ChronoReinforcementsThree = { "scvulture", "scvulture", "scgoliath", "scgoliath", "scsiegetank" }
ChronoLocationOne = { ChronoLocation1.Location }
ChronoLocationTwo = { ChronoLocation2.Location }
ChronoLocationThree = { ChronoLocation3.Location }
Index = 1

SpawnChronoOnePast = function()
	if not ChronoOne.IsDead then
		local cells = Utils.ExpandFootprint(ChronoLocationOne, false)
		local units = { }

		for i = 1, #ChronoReinforcementsOne do
			local unit = Actor.Create(ChronoReinforcementsOne[i], true, { Owner = AlliesOne, Location = ChronoSpawn.Location })
			if unit.IsInWorld then
				unit.Hunt()
			end
			units[unit] = cells[i]
		end

		ChronoOne.Chronoshift(units)
		Trigger.AfterDelay(DateTime.Seconds(120), SpawnChronoOnePresent)
	end
end

SpawnChronoOnePresent = function()
	if not ChronoOne.IsDead then
		local cells = Utils.ExpandFootprint(ChronoLocationOne, false)
		local units = { }

		for i = 1, #ChronoReinforcementsTwo do
			local unit = Actor.Create(ChronoReinforcementsTwo[i], true, { Owner = AlliesOne, Location = ChronoSpawn.Location })
			if unit.IsInWorld then
				unit.Hunt()
			end
			units[unit] = cells[i]
		end

		ChronoOne.Chronoshift(units)
		Trigger.AfterDelay(DateTime.Seconds(120), SpawnChronoOneFuture)
	end
end

SpawnChronoOneFuture = function()
	if not ChronoOne.IsDead then
		local cells = Utils.ExpandFootprint(ChronoLocationOne, false)
		local units = { }

		for i = 1, #ChronoReinforcementsThree do
			local unit = Actor.Create(ChronoReinforcementsThree[i], true, { Owner = AlliesOne, Location = ChronoSpawn.Location })
			if unit.IsInWorld then
				unit.Hunt()
			end
			units[unit] = cells[i]
		end

		ChronoOne.Chronoshift(units)
		Trigger.AfterDelay(DateTime.Seconds(120), SpawnChronoOnePast)
	end
end

SpawnChronoTwoPast = function()
	if not ChronoTwo.IsDead then
		local cells = Utils.ExpandFootprint(ChronoLocationTwo, false)
		local units = { }

		for i = 1, #ChronoReinforcementsOne do
			local unit = Actor.Create(ChronoReinforcementsOne[i], true, { Owner = AlliesTwo, Location = ChronoSpawn.Location })
			if unit.IsInWorld then
				unit.Hunt()
			end
			units[unit] = cells[i]
		end

		ChronoTwo.Chronoshift(units)
		Trigger.AfterDelay(DateTime.Seconds(120), SpawnChronoTwoPresent)
	end
end

SpawnChronoTwoPresent = function()
	if not ChronoTwo.IsDead then
		local cells = Utils.ExpandFootprint(ChronoLocationTwo, false)
		local units = { }

		for i = 1, #ChronoReinforcementsTwo do
			local unit = Actor.Create(ChronoReinforcementsTwo[i], true, { Owner = AlliesTwo, Location = ChronoSpawn.Location })
			if unit.IsInWorld then
				unit.Hunt()
			end
			units[unit] = cells[i]
		end

		ChronoTwo.Chronoshift(units)
		Trigger.AfterDelay(DateTime.Seconds(120), SpawnChronoTwoFuture)
	end
end

SpawnChronoTwoFuture = function()
	if not ChronoTwo.IsDead then
		local cells = Utils.ExpandFootprint(ChronoLocationTwo, false)
		local units = { }

		for i = 1, #ChronoReinforcementsThree do
			local unit = Actor.Create(ChronoReinforcementsThree[i], true, { Owner = AlliesTwo, Location = ChronoSpawn.Location })
			if unit.IsInWorld then
				unit.Hunt()
			end
			units[unit] = cells[i]
		end

		ChronoTwo.Chronoshift(units)
		Trigger.AfterDelay(DateTime.Seconds(120), SpawnChronoTwoPast)
	end
end

SpawnChronoThreePast = function()
	if not ChronoThree.IsDead then
		local cells = Utils.ExpandFootprint(ChronoLocationThree, false)
		local units = { }

		for i = 1, #ChronoReinforcementsOne do
			local unit = Actor.Create(ChronoReinforcementsOne[i], true, { Owner = AlliesThree, Location = ChronoSpawn.Location })
			if unit.IsInWorld then
				unit.Hunt()
			end
			units[unit] = cells[i]
		end

		ChronoThree.Chronoshift(units)
		Trigger.AfterDelay(DateTime.Seconds(120), SpawnChronoThreePresent)
	end
end

SpawnChronoThreePresent = function()
	if not ChronoThree.IsDead then
		local cells = Utils.ExpandFootprint(ChronoLocationThree, false)
		local units = { }

		for i = 1, #ChronoReinforcementsTwo do
			local unit = Actor.Create(ChronoReinforcementsTwo[i], true, { Owner = AlliesThree, Location = ChronoSpawn.Location })
			if unit.IsInWorld then
				unit.Hunt()
			end
			units[unit] = cells[i]
		end

		ChronoThree.Chronoshift(units)
		Trigger.AfterDelay(DateTime.Seconds(120), SpawnChronoThreeFuture)
	end
end

SpawnChronoThreeFuture = function()
	if not ChronoThree.IsDead then
		local cells = Utils.ExpandFootprint(ChronoLocationThree, false)
		local units = { }

		for i = 1, #ChronoReinforcementsThree do
			local unit = Actor.Create(ChronoReinforcementsThree[i], true, { Owner = AlliesThree, Location = ChronoSpawn.Location })
			if unit.IsInWorld then
				unit.Hunt()
			end
			units[unit] = cells[i]
		end

		ChronoThree.Chronoshift(units)
		Trigger.AfterDelay(DateTime.Seconds(120), SpawnChronoThreePast)
	end
end

WorldLoaded = function()

	AlliesOne = Player.GetPlayer("Multi2")
	AlliesTwo = Player.GetPlayer("Multi3")
	AlliesThree = Player.GetPlayer("Multi4")

	Trigger.AfterDelay(DateTime.Seconds(120), function()
		SpawnChronoOnePast()
		SpawnChronoTwoPast()
		SpawnChronoThreePast()
	end)

end