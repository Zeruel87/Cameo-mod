-- elseif Map.LobbyOption("difficulty") == "normal" then
-- 	Mutants = { "furry1" }
-- 	Mutantsx2 = { "furry1", "furry1" }
-- 	Arachnotron = { "furry1" }
-- 	Arachnotronx2 = { "furry1", "furry1" }
-- 	furry3 = { "furry1" }
-- 	furry3x2 = { "furry1", "furry1" }
-- 	furry3 = { "furry1" }
-- 	furry3x2 = { "furry1", "furry1" }
-- 	Demon = { "furry1" }
-- 	Demonx2 = { "furry1", "furry1" }
-- 	furryinfubus = { "furry1" }
-- 	furryinfubusx2 = { "furry1", "furry1" }

-- new
EggMonsterEntryPoints = { MonsterWaypoint }
EggSpawnPoints = { Waypoint, Waypoint1, Waypoint2, Waypoint3, Waypoint4, Waypoint5, Waypoint6, Waypoint7 }

if Map.LobbyOption("difficulty") == "hard" then
	Mutants = { "furry1", "furry2" }
	Mutantsx2 = { "furry1", "furry2", "furry3"  }
	Arachnotron = { "furry1", "furry2", }
	Arachnotronx2 = { "furry1", "furry2", "furry3" }
	furry3 = { "furry1", "furry2", "furryinf2" }
	furry3x2 = { "furry1", "furry2", "furry3" }
	furry3 = { "furry1", "furry2" }
	furry3x2 = { "furry1", "furry2", "furry3" }
	Demon = { "furryi", "furryi" }
	Demonx2 = { "furryi", "furryi", "furryi" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf", "furryinf2", "furryinf2" }
elseif Map.LobbyOption("difficulty") == "normal" then
	Mutants = { "furry1", "furry2" }
	Mutantsx2 = { "furry1", "furry2", "furry3"  }
	Arachnotron = { "furry1", "furry2", }
	Arachnotronx2 = { "furry1", "furry2", "furry3" }
	furry3 = { "furry1", "furry2" }
	furry3x2 = { "furry1", "furry2", "furry3" }
	furry3 = { "furry1", "furry2" }
	furry3x2 = { "furry1", "furry2", "furry3" }
	Demon = { "furry1", "furry2" }
	Demonx2 = { "furryinf2", "furryinf2", "furryinf2" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf", "furryinf2", "furryinf2" }
elseif Map.LobbyOption("difficulty") == "easy" then
	Mutants = { "furry1", "furry2" }
	Mutantsx2 = { "furry1", "furry2", "furry3"  }
	Arachnotron = { "furry1", "furry2", }
	Arachnotronx2 = { "furry1", "furry2", "furry3" }
	furry3 = { "furry1", "furry2" }
	furry3x2 = { "furry1", "furry2", "furry3" }
	furry3 = { "furry1", "furry2" }
	furry3x2 = { "furry1", "furry2", "furry3" }
	Demon = { "furry1", "furry2" }
	Demonx2 = { "furryinf2", "furryinf2", "furryinf2" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf", "furryinf2" }
end
--Adjust the amount--Mutants
EggWave = 0
EggWaves =
{
	{ delay = 1, units = { } },--00
	{ delay = 1, units = { Mutants } },--45
	{ delay = 1, units = { Mutants, Mutants, Mutantsx2, Arachnotron, Arachnotronx2 } },--2:00
	{ delay = 1, units = { Mutants, Mutants, Mutantsx2, Mutantsx2, Arachnotron, Arachnotron } },--240
	{ delay = 1, units = { Mutants, Arachnotron, Mutantsx2, Mutantsx2, Mutantsx2, Arachnotronx2, Arachnotron, Arachnotron } },--320
	{ delay = 1, units = { Mutantsx2, Mutantsx2, furry3, Arachnotron, furry3, Arachnotron, Mutants, Mutants, } },--440
	{ delay = 1, units = { Mutantsx2, Arachnotron, furry3, Mutantsx2, Arachnotronx2, Arachnotronx2, Arachnotron, Mutants } },--420
	{ delay = 1, units = { } },
	{ delay = 1, units = { Mutantsx2, Mutants, Mutantsx2, Arachnotron, Arachnotron, Arachnotronx2, furry3x2, furry3, furry3, Mutantsx2 } },--500
	{ delay = 1, units = { Arachnotronx2, Mutantsx2, furry3x2, furry3, furry3, Mutants, Mutants } },--540
	{ delay = 1, units = { furry3x2, furry3x2, furry3, furry3, Arachnotronx2, Arachnotronx2, Mutantsx2, Mutantsx2, Mutantsx2 } },--620
	{ delay = 1, units = { } },
	{ delay = 1, units = { furry3, furry3, furry3, furry3, furry3, Mutantsx2, Mutantsx2, furry3x2 } },--700
	{ delay = 1, units = { furry3x2, furry3x2, furry3x2, Mutantsx2, Mutantsx2, Mutantsx2, furry3x2 } },--740
	{ delay = 1, units = { furry3x2, furry3x2, Arachnotronx2,Mutantsx2 } },--820
	{ delay = 1, units = { Demon, Demon, Demon, Demon, furry3, furry3, furryinfubus } },--920
	{ delay = 1, units = { } },--1000
	{ delay = 1, units = { Demonx2, Demon, Demon, furry3x2, furry3x2 } },--10:40
	{ delay = 1, units = { Demon, Demon, Mutantsx2 } },--11:20
	{ delay = 1, units = { Mutants, Mutants, furryinfubus, Mutantsx2, furry3, furry3, furry3, furry3 } },--240
	{ delay = 1, units = { } },
	{ delay = 1, units = { furryinfubus, furryinfubus, furry3 } }
}

SendUnits = function(entryCell, unitTypes, targetCell)
	Reinforcements.Reinforce(Monsters, unitTypes, { entryCell }, 40, function(a)
		if not a.HasProperty("AttackMove") then
			Trigger.OnIdle(a, function(a)
				a.Move(targetCell)
			end)
			return
		end

		a.AttackMove(targetCell)
		Trigger.OnIdle(a, function(a)
			a.Hunt()
		end)
	end)
end

EggIncreaseDifficulty = function()
	local additions = { Mutants, Arachnotron, furry3, furry3, Demon, furryinfubus }
	Utils.Do(EggWaves, function(wave)
		wave.units[#wave.units + 1] = Utils.Random(additions)
	end)
end

EggSendWave = function()
	if Egg.IsDead then
		return
	end
	
		
	EggWave = EggWave + 1
	local wave = EggWaves[EggWave]
	Trigger.AfterDelay(wave.delay, function()
		Utils.Do(wave.units, function(units)
			local entry = Utils.Random(EggMonsterEntryPoints).Location
			local target = Utils.Random(EggSpawnPoints).Location
			SendUnits(entry, units, target)
		end)
		if (EggWave < #EggWaves) then
			delayFirstTeam = 55
			local delay = delayFirstTeam
			Trigger.AfterDelay(DateTime.Seconds(delay), function()
				EggSendWave()
				Trigger.AfterDelay(DateTime.Minutes(14), EggIncreaseDifficulty)
			end)
		end
	end)
end

if (EggWave == null) then
	EggSendWave()
end

-----------Egg1
Egg1MonsterEntryPoints = { MonsterWaypoint1 }
Egg1SpawnPoints = { Waypoint1, Waypoint3, Waypoint1, Waypoint }

if Map.LobbyOption("difficulty") == "hard" then
	Mutants = { "furry1", "furry1" }
	Mutantsx2 = { "furry1", "furry1", "furry1", "furry1", "furry1"  }
	Arachnotron = { "furry2", "furry2", "furry1", "furry1" }
	Arachnotronx2 = { "furry2", "furry2", "furry2", "furry1", "furry1", "furry1", "furry1" }
	furry3 = { "furry3", "furry3", "furry1", "furry1", "furry1", "furry1" }
	furry3x2 = { "furry3", "furry3", "furry3", "furry1", "furry1" }
	furry3 = { "furry3", "furry3" }
	furry3x2 = { "furry3", "furry3", "furry3" }
	Demon = { "furryi", "furryi" }
	Demonx2 = { "furryi", "furryi", "furryi", "furryinf2" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf", "furryinf2" }
elseif Map.LobbyOption("difficulty") == "normal" then
	Mutants = { "furry1", "furry1" }
	Mutantsx2 = { "furry1", "furry1", "furry1" }
	Arachnotron = { "furry2", "furry2" }
	Arachnotronx2 = { "furry2", "furry1", "furry1" }
	furry3 = { "furry3", "furry3", "furry2" }
	furry3x2 = { "furry3", "furry1", "furry1", "furry2" }
	furry3 = { "furry3", "furry3", "furry2", "furry1" }
	furry3x2 = { "furry3", "furry1", "furry1", "furry3" }
	Demon = { "furryi", "furryinf" }
	Demonx2 = { "furryi", "furry1", "furry1", "furry3" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furry1", "furry1", "furryi" }
elseif Map.LobbyOption("difficulty") == "easy" then
	Mutants = { "furry1" }
	Mutantsx2 = {  }
	Arachnotron = { "furry2" }
	Arachnotronx2 = { "furry1" }
	furry3 = { "furry3" }
	furry3x2 = { "furry1" }
	furry3 = { "furry3" }
	furry3x2 = { "furry1"  }
	Demon = { "furryi" }
	Demonx2 = { "furry1"  }
	furryinfubus = { "furryinf" }
	furryinfubusx2 = { "furry1" }
end
--Arachnotron
Egg1Wave = 0
Egg1Waves =
{
	{ delay = 1, units = { } },--00
	{ delay = 1, units = { Mutants } },--1:00
	{ delay = 1, units = { Mutants, Mutants, Arachnotron, Mutants } },--2
	{ delay = 1, units = { Arachnotron, Arachnotron, furry3, Mutantsx2, Mutantsx2, Mutantsx2, Mutantsx2 } },--3
	{ delay = 1, units = { Arachnotronx2, Arachnotronx2, furry3, furry3, Mutantsx2, Mutantsx2, Mutantsx2 } },--4
	{ delay = 1, units = { Arachnotronx2, Arachnotronx2, furry3, furry3, furry3, Mutantsx2, Mutantsx2 } },--5
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, furry3x2, furry3x2, furry3, furry3, furry3x2, Arachnotronx2, } },--6
	{ delay = 1, units = { furry3x2, Mutantsx2, furry3, furry3x2, Demon, furry3, Arachnotronx2, Arachnotronx2, furry3 } },--7
	{ delay = 1, units = { } },--8
	{ delay = 1, units = { furry3x2, Mutantsx2, furryinfubus, Arachnotronx2, Demon, Mutantsx2, furry3x2 } },--9
	{ delay = 1, units = { Mutantsx2, Demonx2, Arachnotronx2, Demon, Mutantsx2, furry3x2 } },--10
	{ delay = 1, units = { furryinfubus, Mutantsx2, Arachnotronx2, Mutantsx2 } },--11
	{ delay = 1, units = { } },--12
	{ delay = 1, units = { furryinfubus, furry3x2 } },--13
	{ delay = 1, units = { furryinfubus, furry3x2, Demon, Demon } }--14
}

Egg1IncreaseDifficulty = function()
	local additions = { Mutants, Arachnotron, furry3, furry3, Demon, furryinfubus }
	Utils.Do(Egg1Waves, function(wave)
		wave.units[#wave.units + 1] = Utils.Random(additions)
	end)
end

Egg1SendWave = function()
	if Egg1.IsDead then
		return
	end
	Egg1Wave = Egg1Wave + 1
	local wave = Egg1Waves[Egg1Wave]
	Trigger.AfterDelay(wave.delay, function()
		Utils.Do(wave.units, function(units)
			local entry = Utils.Random(Egg1MonsterEntryPoints).Location
			local target = Utils.Random(Egg1SpawnPoints).Location
			SendUnits(entry, units, target)
		end)
		if (Egg1Wave < #Egg1Waves) then
			delayFirstTeam = 60
			local delay = delayFirstTeam
			Trigger.AfterDelay(DateTime.Seconds(delay), function()
				Egg1SendWave()
				Trigger.AfterDelay(DateTime.Minutes(15), Egg1IncreaseDifficulty)
			end)
		end
	end)
end

-----------Egg2
Egg2MonsterEntryPoints = { MonsterWaypoint2 }
Egg2SpawnPoints = { Waypoint2, Waypoint3, Waypoint, Waypoint1 }

if Map.LobbyOption("difficulty") == "hard" then
	Mutants = { "furry1", "furry1" }
	Mutantsx2 = { "furry1", "furry1", "furry1", "furry1", "furry1"  }
	Arachnotron = { "furry2", "furry2", }
	Arachnotronx2 = { "furry2", "furry2", "furry2", "furry1", "furry1" }
	furry3 = { "furry3", "furry3" }
	furry3x2 = { "furry3", "furry3", "furry3" }
	furry3 = { "furry3", "furry3" }
	furry3x2 = { "furry3", "furry3", "furry3" }
	Demon = { "furryi", "furryi" }
	Demonx2 = { "furryi", "furryi", "furryi" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf", "furryinf2" }
elseif Map.LobbyOption("difficulty") == "normal" then
	Mutants = { "furry1", "furry1" }
	Mutantsx2 = { "furry1", "furry1", "furry1" }
	Arachnotron = { "furry2", "furry2" }
	Arachnotronx2 = { "furry2", "furry1", "furry1" }
	furry3 = { "furry3", "furry3", "furry2" }
	furry3x2 = { "furry3", "furry1", "furry1", "furry2" }
	furry3 = { "furry3", "furry3", "furry2", "furry1" }
	furry3x2 = { "furry3", "furry1", "furry1", "furry3" }
	Demon = { "furryi", "furryi" }
	Demonx2 = { "furryi", "furry1", "furry1", "furry3" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furry1", "furry1", "furryi" }
elseif Map.LobbyOption("difficulty") == "easy" then
	Mutants = { "furry1" }
	Mutantsx2 = { "furry1" }
	Arachnotron = { "furry2" }
	Arachnotronx2 = { "furry1" }
	furry3 = { "furry3" }
	furry3x2 = { "furry1" }
	furry3 = { "furry3" }
	furry3x2 = { "furry1"  }
	Demon = { "furryi" }
	Demonx2 = { "furry1"  }
	furryinfubus = { "furryinf" }
	furryinfubusx2 = { "furry1" }
end
--furry3
Egg2Wave = 0
Egg2Waves =
{
	{ delay = 1, units = { } },--0
	{ delay = 1, units = { Mutants } },--110
	{ delay = 1, units = { Arachnotron, Mutantsx2, Arachnotron } },--220
	{ delay = 1, units = { Arachnotron, Arachnotronx2, Mutantsx2, furry3, Mutantsx2 } },--330
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Arachnotronx2, furry3, Mutantsx2 } },--440
	{ delay = 1, units = { Mutants, Mutants, Mutants, Mutants, Mutants, furry3 } },--550
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, furry3, furry3, Arachnotronx2, furry3x2, furry3 } },--700
	{ delay = 1, units = { Mutantsx2, Mutantsx2, furry3x2, Arachnotronx2, furry3x2, furry3, furry3 } },--810
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, furryinfubus, furry3x2, furry3, furry3, Arachnotronx2, Arachnotronx2, furry3 } },--920
	{ delay = 1, units = { furry3x2, furry3, furry3, furryinfubus, Arachnotronx2, Arachnotronx2, Demon, furry3, Mutantsx2 } },--1030
	{ delay = 1, units = { furry3, furry3, Mutantsx2, Mutantsx2, Mutantsx2, Mutants, Mutants, furryinfubus } },--1140
	{ delay = 1, units = { Demon, Demon, Demon, furry3, furry3, furryinfubus, Mutantsx2, Mutantsx2, Arachnotronx2, Mutantsx2, furry3 } },--1250
	{ delay = 1, units = { Demonx2, Demonx2, furry3x2, furry3x2, Mutantsx2, furry3x2 } },--1400
	{ delay = 1, units = { furryinfubus, Demonx2 } },--1510
	{ delay = 1, units = { Mutants, Mutants, Mutants, Mutants, Mutants } },--1620
	{ delay = 1, units = { furryinfubusx2, furryinfubus } },--
}

Egg2IncreaseDifficulty = function()
	local additions = { Mutants, Arachnotron, furry3, furry3, Demon, furryinfubus }
	Utils.Do(Egg2Waves, function(wave)
		wave.units[#wave.units + 1] = Utils.Random(additions)
	end)
end

Egg2SendWave = function()
	if Egg2.IsDead then
		return
	end
	Egg2Wave = Egg2Wave + 1
	local wave = Egg2Waves[Egg2Wave]
	Trigger.AfterDelay(wave.delay, function()
		Utils.Do(wave.units, function(units)
			local entry = Utils.Random(Egg2MonsterEntryPoints).Location
			local target = Utils.Random(Egg2SpawnPoints).Location
			SendUnits(entry, units, target)
		end)
		if (Egg2Wave < #Egg2Waves) then
			delayFirstTeam = 70
			local delay = delayFirstTeam
			Trigger.AfterDelay(DateTime.Seconds(delay), function()
				Egg2SendWave()
				Trigger.AfterDelay(DateTime.Minutes(13), Egg2IncreaseDifficulty)
			end)
		end
	end)
end

-----------Egg3
Egg3MonsterEntryPoints = { MonsterWaypoint3 }
Egg3SpawnPoints = { Waypoint2, Waypoint1, Waypoint3, Waypoint0 }

if Map.LobbyOption("difficulty") == "hard" then
	Mutants = { "furry1", "furry1" }
	Mutantsx2 = { "furry1", "furry1", "furry1"  }
	Arachnotron = { "furry2", "furry2", }
	Arachnotronx2 = { "furry2", "furry2", "furry2" }
	furry3 = { "furry3", "furry3" }
	furry3x2 = { "furry3", "furry3", "furry3", "furry1", "furry1" }
	furry3 = { "furry3", "furry3" }
	furry3x2 = { "furry3", "furry3", "furry3" }
	Demon = { "furryi", "furryi" }
	Demonx2 = { "furryi", "furryi", "furryi" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf", "furryinf2" }
elseif Map.LobbyOption("difficulty") == "normal" then
	Mutants = { "furry1", "furry1" }
	Mutantsx2 = { "furry1", "furry1", "furry1" }
	Arachnotron = { "furry2", "furry2" }
	Arachnotronx2 = { "furry2", "furry1", "furry1" }
	furry3 = { "furry3", "furry3", "furry2" }
	furry3x2 = { "furry3", "furry1", "furry1", "furry2" }
	furry3 = { "furry3", "furry3", "furry2", "furry1" }
	furry3x2 = { "furry3", "furry1", "furry1", "furry3" }
	Demon = { "furryi", "furryi" }
	Demonx2 = { "furryi", "furry1", "furry1", "furry3" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furry1", "furry1", "furryi" }
elseif Map.LobbyOption("difficulty") == "easy" then
	Mutants = { "furry1" }
	Mutantsx2 = {  }
	Arachnotron = { "furry2" }
	Arachnotronx2 = { "furry1" }
	furry3 = { "furry3" }
	furry3x2 = { "furry1" }
	furry3 = { "furry3" }
	furry3x2 = { "furry1"  }
	Demon = { "furryi" }
	Demonx2 = { "furry1"  }
	furryinfubus = { "furryinf" }
	furryinfubusx2 = { "furry1" }
end

Egg3Wave = 0
Egg3Waves =
{
	{ delay = 1, units = { } },--00
	{ delay = 1, units = { Mutants } },--55
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Arachnotron, Arachnotron } },--150
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Arachnotronx2, Arachnotron, Arachnotron } },--245
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Mutantsx2, Mutantsx2, Arachnotron } },--340
	{ delay = 1, units = { Arachnotronx2, Arachnotronx2, Arachnotron, Arachnotron, furry3, Mutantsx2, Mutantsx2 } },--435
	{ delay = 1, units = { Mutantsx2, Mutantsx2, furry3, Arachnotronx2, Arachnotronx2, furry3 } },--530
	{ delay = 1, units = { furry3, furry3, Mutantsx2, Mutantsx2, Demon, Arachnotronx2, Arachnotronx2, furry3x2, furry3 } },--625
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Mutantsx2, furry3, furry3,furry3 } },--720
	{ delay = 1, units = { furry3x2, furry3, furryinfubus, Demon, furry3, Arachnotronx2, Arachnotron, Arachnotron, Mutantsx2, Mutantsx2 } },--815
	{ delay = 1, units = { Demon, Demonx2, Demon, furry3, furry3x2, furry3x2, Mutantsx2, Mutantsx2 } },--910
	{ delay = 1, units = { furry3, furry3, furryinfubus, Demon, Demon, Mutantsx2, Arachnotronx2, Arachnotronx2 } },--1005
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Mutantsx2 } },--1100
	{ delay = 1, units = { furryinfubus, furryinfubus, furryinfubus, furry3x2, furry3, furry3 } },--1155
	{ delay = 1, units = { furryinfubus, furryinfubusx2, furry3x2, furry3 } },--1250
	{ delay = 1, units = { furryinfubusx2, furryinfubusx2, furryinfubus, furry3x2 } }--1345
}

Egg3IncreaseDifficulty = function()
	local additions = { Mutants, Arachnotron, furry3, furry3, Demon, furryinfubus }
	Utils.Do(Egg3Waves, function(wave)
		wave.units[#wave.units + 1] = Utils.Random(additions)
	end)
end

Egg3SendWave = function()
	if Egg3.IsDead then
		return
	end
	Egg3Wave = Egg3Wave + 1
	local wave = Egg3Waves[Egg3Wave]
	Trigger.AfterDelay(wave.delay, function()
		Utils.Do(wave.units, function(units)
			local entry = Utils.Random(Egg3MonsterEntryPoints).Location
			local target = Utils.Random(Egg3SpawnPoints).Location
			SendUnits(entry, units, target)
		end)
		if (Egg3Wave < #Egg3Waves) then
			delayFirstTeam = 55
			local delay = delayFirstTeam
			Trigger.AfterDelay(DateTime.Seconds(delay), function()
				Egg3SendWave()
				Trigger.AfterDelay(DateTime.Minutes(14), Egg3IncreaseDifficulty)
			end)
		end
	end)
end

-----------Egg4
Egg4MonsterEntryPoints = { MonsterWaypoint4 }
Egg4SpawnPoints = { Waypoint3, Waypoint2, Waypoint1, Waypoint }

if Map.LobbyOption("difficulty") == "hard" then
	Mutants = { "furry1", "furry1" }
	Mutantsx2 = { "furry1", "furry1", "furry1"  }
	Arachnotron = { "furry2", "furry2", }
	Arachnotronx2 = { "furry2", "furry2", "furry2" }
	furry3 = { "furry3", "furry3", "furry1", "furry1" }
	furry3x2 = { "furry3", "furry3", "furry3" }
	furry3 = { "furry3", "furry3" }
	furry3x2 = { "furry3", "furry3", "furry3" }
	Demon = { "furryi", "furryi" }
	Demonx2 = { "furryi", "furryi", "furryi" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf", "furryinf2" }
elseif Map.LobbyOption("difficulty") == "normal" then
	Mutants = { "furry1", "furry1" }
	Mutantsx2 = { "furry1", "furry1", "furry1" }
	Arachnotron = { "furry2" }
	Arachnotronx2 = { "furry2", "furry1", "furry1" }
	furry3 = { "furry3", "furry3", "furry2" }
	furry3x2 = { "furry3", "furry1", "furry1", "furry2" }
	furry3 = { "furry3", "furry3", "furry2", "furry1" }
	furry3x2 = { "furry3", "furry1", "furry1", "furry3" }
	Demon = { "furryi", "furryi" }
	Demonx2 = { "furryi", "furry1", "furry1", "furry3" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furry1", "furry1", "furryi" }
elseif Map.LobbyOption("difficulty") == "easy" then
	Mutants = { "furry1" }
	Mutantsx2 = {  }
	Arachnotron = { "furry2" }
	Arachnotronx2 = { "furry1" }
	furry3 = { "furry3" }
	furry3x2 = { "furry1" }
	furry3 = { "furry3" }
	furry3x2 = { "furry1"  }
	Demon = { "furryi" }
	Demonx2 = { "furry1"  }
	furryinfubus = { "furryinf" }
	furryinfubusx2 = { "furry1" }
end

Egg4Wave = 0
Egg4Waves =
{
	{ delay = 1, units = { } },--00
	{ delay = 1, units = { Mutants, Mutantsx2 } },--45
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Arachnotron, Arachnotron } },--130
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Arachnotronx2, Arachnotron, Mutantsx2 } },--215
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, furry3 } },--300
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Arachnotron, Arachnotronx2, furry3, furry3 } },--345
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Mutants, furry3, furry3, Arachnotronx2, Arachnotron } },--430
	{ delay = 1, units = { furry3, Mutantsx2, Mutantsx2, Mutantsx2, Arachnotron, Arachnotron, Arachnotron, furry3 } },--515
	{ delay = 1, units = { Mutantsx2, furry3, furry3, Mutantsx2 } },--600
	{ delay = 1, units = { Mutantsx2, Mutantsx2, furry3, furry3, furry3x2, furry3x2, Demon, Demon } },--745
	{ delay = 1, units = { Demon, furryinfubus, Arachnotron, Demon } },--830
	{ delay = 1, units = { Demonx2, furry3, furry3, furry3x2, furryinfubusx2, furry3x2, Mutantsx2, Mutantsx2 } },--915
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Mutantsx2 } },--1000
	{ delay = 1, units = { furryinfubus, furryinfubusx2, Demonx2, Demonx2 } },--1145
	{ delay = 1, units = { furryinfubus, Mutantsx2, furryinfubus } }--1230
}

Egg4IncreaseDifficulty = function()
	local additions = { Mutants, Arachnotron, furry3, furry3, Demon, furryinfubus }
	Utils.Do(Egg4Waves, function(wave)
		wave.units[#wave.units + 1] = Utils.Random(additions)
	end)
end

Egg4SendWave = function()
	if Egg4.IsDead then
		return
	end
	Egg4Wave = Egg4Wave + 1
	local wave = Egg4Waves[Egg4Wave]
	Trigger.AfterDelay(wave.delay, function()
		Utils.Do(wave.units, function(units)
			local entry = Utils.Random(Egg4MonsterEntryPoints).Location
			local target = Utils.Random(Egg4SpawnPoints).Location
			SendUnits(entry, units, target)
		end)
		if (Egg4Wave < #Egg4Waves) then
			delayFirstTeam = 45
			local delay = delayFirstTeam
			Trigger.AfterDelay(DateTime.Seconds(delay), function()
				Egg4SendWave()
				Trigger.AfterDelay(DateTime.Minutes(13), Egg4IncreaseDifficulty)
			end)
		end
	end)
end

-----------Egg5
Egg5MonsterEntryPoints = { MonsterWaypoint5 }
Egg5SpawnPoints = { Waypoint3, Waypoint2, Waypoint1, Waypoint }

if Map.LobbyOption("difficulty") == "hard" then
	Mutants = { "furry1", "furry1" }
	Mutantsx2 = { "furry1", "furry1", "furry1"  }
	Arachnotron = { "furry2", "furry2", }
	Arachnotronx2 = { "furry2", "furry2", "furry2", "furry1", "furry1" }
	furry3 = { "furry3", "furry3" }
	furry3x2 = { "furry3", "furry3", "furry3" }
	furry3 = { "furry3", "furry3" }
	furry3x2 = { "furry3", "furry3", "furry3" }
	Demon = { "furryi", "furryi" }
	Demonx2 = { "furryi", "furryi", "furryi" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf", "furryinf2" }
elseif Map.LobbyOption("difficulty") == "normal" then
	Mutants = { "furry1", "furry1" }
	Mutantsx2 = { "furry1", "furry1", "furry1" }
	Arachnotron = { "furry2", "furry2" }
	Arachnotronx2 = { "furry2", "furry1", "furry1" }
	furry3 = { "furry3", "furry3", "furry2" }
	furry3x2 = { "furry3", "furry1", "furry1", "furry2" }
	furry3 = { "furry3", "furry3", "furry2" }
	furry3x2 = { "furry3", "furry1", "furry1", "furry3" }
	Demon = { "furryi", "furryi" }
	Demonx2 = { "furryi", "furry1", "furry1", "furry3" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furry1", "furry1", "furryi" }
elseif Map.LobbyOption("difficulty") == "easy" then
	Mutants = { "furry1" }
	Mutantsx2 = { "furry1" }
	Arachnotron = { "furry2" }
	Arachnotronx2 = { "furry1" }
	furry3 = { "furry3" }
	furry3x2 = { "furry1" }
	furry3 = { "furry3" }
	furry3x2 = { "furry1"  }
	Demon = { "furryi" }
	Demonx2 = { "furry1"  }
	furryinfubus = { "furryinf" }
	furryinfubusx2 = { "furry1" }
end

Egg5Wave = 0
Egg5Waves =
{
	{ delay = 1, units = { } },--00
	{ delay = 1, units = { Mutants } },--100
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Arachnotron, Arachnotronx2 } },--200
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Arachnotron, Arachnotronx2, Mutantsx2 } },--300
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Arachnotron, Mutantsx2, furry3x2, Arachnotronx2 } },--400
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, furry3, furry3 } },--500
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Arachnotron, Arachnotron, furry3, furry3, furry3 } },--600
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, furry3, Arachnotronx2, furry3, Demon } },--700
	{ delay = 1, units = { furry3, furry3, furry3x2, Demon, Demon, Mutantsx2, Arachnotronx2, Arachnotronx2, furry3, furry3x2 } },--800
	{ delay = 1, units = { furry3x2, Demon, Demon, furryinfubus, Arachnotron, Arachnotronx2, furry3, furry3x2 } },--900
	{ delay = 1, units = { Demonx2, furry3, furryinfubus, Arachnotron, Arachnotron, Arachnotronx2, furry3x2 } },--1000
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2 } },--1100
	{ delay = 1, units = { furryinfubus, furryinfubus, Mutantsx2, furry3, Mutantsx2, furry3x2 } },--1200
	{ delay = 1, units = { furry3, furryinfubus, Arachnotron, furry3 } },--1300
	{ delay = 1, units = { furryinfubus, furryinfubusx2, furry3x2 } }--1400
}

Egg5IncreaseDifficulty = function()
	local additions = { Mutants, Arachnotron, furry3, furry3, Demon, furryinfubus }
	Utils.Do(Egg5Waves, function(wave)
		wave.units[#wave.units + 1] = Utils.Random(additions)
	end)
end

Egg5SendWave = function()
	if Egg5.IsDead then
		return
	end
	Egg5Wave = Egg5Wave + 1
	local wave = Egg5Waves[Egg5Wave]
	Trigger.AfterDelay(wave.delay, function()
		Utils.Do(wave.units, function(units)
			local entry = Utils.Random(Egg5MonsterEntryPoints).Location
			local target = Utils.Random(Egg5SpawnPoints).Location
			SendUnits(entry, units, target)
		end)
		if (Egg5Wave < #Egg5Waves) then
			delayFirstTeam = 60
			local delay = delayFirstTeam
			Trigger.AfterDelay(DateTime.Seconds(delay), function()
				Egg5SendWave()
				Trigger.AfterDelay(DateTime.Minutes(14), Egg5IncreaseDifficulty)
			end)
		end
	end)
end

-----------Egg6
Egg6MonsterEntryPoints = { MonsterWaypoint6 }
Egg6SpawnPoints = { Waypoint, Waypoint3, Waypoint2, Waypoint1 }

if Map.LobbyOption("difficulty") == "hard" then
	Mutants = { "furry1", "furry1" }
	Mutantsx2 = { "furry1", "furry1", "furry1"  }
	Arachnotron = { "furry2", "furry2", }
	Arachnotronx2 = { "furry2", "furry2", "furry2" }
	furry3 = { "furry3", "furry3" }
	furry3x2 = { "furry3", "furry3", "furry3" }
	furry3 = { "furry3", "furry3" }
	furry3x2 = { "furry3", "furry3", "furry3" }
	Demon = { "furryi", "furryi" }
	Demonx2 = { "furryi", "furryi", "furryi" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf", "furryinf2" }
elseif Map.LobbyOption("difficulty") == "normal" then
	Mutants = { "furry1", "furry1" }
	Mutantsx2 = { "furry1", "furry1", "furry1" }
	Arachnotron = { "furry2" }
	Arachnotronx2 = { "furry2", "furry1", "furry1" }
	furry3 = { "furry3", "furry3", "furry2" }
	furry3x2 = { "furry3", "furry1", "furry1", "furry2" }
	furry3 = { "furry3", "furry3", "furry2", "furry1" }
	furry3x2 = { "furry3", "furry1", "furry1", "furry3" }
	Demon = { "furryi", "furryi" }
	Demonx2 = { "furryi", "furry1", "furry1", "furry3" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furry1", "furry1", "furryi" }
elseif Map.LobbyOption("difficulty") == "easy" then
	Mutants = { "furry1" }
	Mutantsx2 = { "furry1" }
	Arachnotron = { "furry2" }
	Arachnotronx2 = { "furry1" }
	furry3 = { "furry3" }
	furry3x2 = { "furry1" }
	furry3 = { "furry3" }
	furry3x2 = { "furry1"  }
	Demon = { "furryi" }
	Demonx2 = { "furry1"  }
	furryinfubus = { "furryinf" }
	furryinfubusx2 = { "furry1" }
end

Egg6Wave = 0
Egg6Waves =
{
	{ delay = 1, units = { } },--00
	{ delay = 1, units = { Mutants } },--105
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Arachnotron, Arachnotron } },--210
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, furry3, Arachnotron, Arachnotron } },--315
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, furry3, Arachnotronx2, furry3, Arachnotron } },--420
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, furry3, furry3 } },--525
	{ delay = 1, units = { Arachnotronx2, furry3, furry3, Mutantsx2, furry3, Arachnotron } },--630
	{ delay = 1, units = { Arachnotronx2, Arachnotron, Arachnotron, Demon, furry3, furry3, furry3, Mutantsx2, Mutantsx2 } },--735
	{ delay = 1, units = { furry3x2, furry3, furry3x2, furry3, Arachnotronx2, Mutantsx2, Mutantsx2 } },--840
	{ delay = 1, units = { Demon, furryinfubus, furry3, furry3x2, Mutantsx2, Mutantsx2, furry3, furry3, furry3 } },--945
	{ delay = 1, units = { furry3, furry3, furry3x2, furryinfubus, Mutantsx2, Mutantsx2, Demon, Demon } },--1050
	{ delay = 1, units = { furry3x2, Demonx2, furryinfubus, furry3, Mutantsx2, furry3x2 } },--1155
	{ delay = 1, units = { furry3, Mutantsx2, furryinfubus, Mutantsx2, furry3x2 } },--1300
	{ delay = 1, units = { furryinfubusx2, furryinfubusx2, furry3x2 } }--1405
}

Egg6IncreaseDifficulty = function()
	local additions = { Mutants, Arachnotron, furry3, furry3, Demon, furryinfubus }
	Utils.Do(Egg6Waves, function(wave)
		wave.units[#wave.units + 1] = Utils.Random(additions)
	end)
end

Egg6SendWave = function()
	if Egg6.IsDead then
		return
	end
	Egg6Wave = Egg6Wave + 1
	local wave = Egg6Waves[Egg6Wave]
	Trigger.AfterDelay(wave.delay, function()
		Utils.Do(wave.units, function(units)
			local entry = Utils.Random(Egg6MonsterEntryPoints).Location
			local target = Utils.Random(Egg6SpawnPoints).Location
			SendUnits(entry, units, target)
		end)
		if (Egg6Wave < #Egg6Waves) then
			delayFirstTeam = 65
			local delay = delayFirstTeam
			Trigger.AfterDelay(DateTime.Seconds(delay), function()
				Egg6SendWave()
				Trigger.AfterDelay(DateTime.Minutes(13), Egg6IncreaseDifficulty)
			end)
		end
	end)
end

-----------Egg7
Egg7MonsterEntryPoints = { MonsterWaypoint7 }
Egg7SpawnPoints = { Waypoint1, Waypoint2, Waypoint, Waypoint3 }

if Map.LobbyOption("difficulty") == "hard" then
	Mutants = { "furry1", "furry1" }
	Mutantsx2 = { "furry1", "furry1", "furry1"  }
	Arachnotron = { "furry2", "furry2", }
	Arachnotronx2 = { "furry2", "furry2", "furry2" }
	furry3 = { "furry3", "furry3" }
	furry3x2 = { "furry3", "furry3", "furry3" }
	furry3 = { "furry3", "furry3" }
	furry3x2 = { "furry3", "furry3", "furry3" }
	Demon = { "furryi", "furryi" }
	Demonx2 = { "furryi", "furryi", "furryi" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf", "furryinf2" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
elseif Map.LobbyOption("difficulty") == "normal" then
	Mutants = { "furry1", "furry1" }
	Mutantsx2 = { "furry1", "furry1", "furry1" }
	Arachnotron = { "furry2", "furry2" }
	Arachnotronx2 = { "furry2", "furry1", "furry1" }
	furry3 = { "furry3", "furry3" }
	furry3x2 = { "furry3", "furry1", "furry1", "furry2" }
	furry3 = { "furry3", "furry3", "furry2", "furry1" }
	furry3x2 = { "furry3", "furry1", "furry1", "furry3" }
	Demon = { "furryi", "furryi" }
	Demonx2 = { "furryi", "furry1", "furry1", "furry3" }
	furryinfubus = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furryinf" }
	furryinfubusx2 = { "furryinf", "furryinf", "furryinf2", "furryinf2", "furryinf2", "furry1", "furry1", "furryi" }
elseif Map.LobbyOption("difficulty") == "easy" then
	Mutants = { "furry1" }
	Mutantsx2 = { "furry1" }
	Arachnotron = { "furry2" }
	Arachnotronx2 = { "furry1" }
	furry3 = { "furry3" }
	furry3x2 = { "furry1" }
	furry3 = { "furry3" }
	furry3x2 = { "furry1"  }
	Demon = { "furryi" }
	Demonx2 = { "furry1"  }
	furryinfubus = { "furryinf" }
	furryinfubusx2 = { "furry1" }
end

Egg7Wave = 0
Egg7Waves =
{
	{ delay = 1, units = { } },--00
	{ delay = 1, units = { Mutants } },--40
	{ delay = 1, units = { Mutantsx2, Arachnotron, Mutantsx2 } },--120
	{ delay = 1, units = { Arachnotron, Arachnotron, Arachnotronx2, Mutantsx2, Mutantsx2, Mutantsx2 } },--200
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Arachnotronx2, Mutantsx2, Mutantsx2 } },--240
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Arachnotronx2, Arachnotronx2, Mutantsx2 } },--320
	{ delay = 1, units = { Mutantsx2, furry3, Arachnotronx2, Mutantsx2, Mutantsx2, furry3 } },--400
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Arachnotronx2, Arachnotron, furry3x2 } },--440
	{ delay = 1, units = { Arachnotron, Arachnotron, Mutantsx2, Mutantsx2, furry3, furry3 } },--520
	{ delay = 1, units = { furry3, furry3, Arachnotronx2, Arachnotron, furry3, furry3x2 } },--600
	{ delay = 1, units = { furry3x2, furry3, furry3, Mutantsx2, Demon, Arachnotron, Arachnotronx2, Mutantsx2 } },--640
	{ delay = 1, units = { Demon, furry3, furry3x2, Mutantsx2, Mutantsx2, Arachnotron } },--720
	{ delay = 1, units = { furryinfubus, Arachnotron, Arachnotron, } },--800
	{ delay = 1, units = { furryinfubus, furry3 } },--840
	{ delay = 1, units = { furryinfubus, furryinfubusx2, Arachnotronx2, Mutantsx2, furry3 } },--920
	{ delay = 1, units = { furryinfubus, Arachnotron, Arachnotron, Demon, furry3, furry3x2, Mutantsx2, Mutantsx2, } }
}

Egg7IncreaseDifficulty = function()
	local additions = { Mutants, Arachnotron, furry3, furry3, Demon, furryinfubus }
	Utils.Do(Egg7Waves, function(wave)
		wave.units[#wave.units + 1] = Utils.Random(additions)
	end)
end

Egg7SendWave = function()
	if Egg7.IsDead then
		return
	end
	Egg7Wave = Egg7Wave + 1
	local wave = Egg7Waves[Egg7Wave]
	Trigger.AfterDelay(wave.delay, function()
		Utils.Do(wave.units, function(units)
			local entry = Utils.Random(Egg7MonsterEntryPoints).Location
			local target = Utils.Random(Egg7SpawnPoints).Location
			SendUnits(entry, units, target)
		end)
		if (Egg7Wave < #Egg7Waves) then
			delayFirstTeam = 40
			local delay = delayFirstTeam
			Trigger.AfterDelay(DateTime.Seconds(delay), function()
				Egg7SendWave()
				Trigger.AfterDelay(DateTime.Minutes(10), Egg7IncreaseDifficulty)
			end)
		end
	end)
end


--hard difficulty check
MothershipChrono = function()
	if Map.LobbyOption("difficulty") == "easy" then
		EggsDestroyed()
		MothershipDestroyed()
	elseif Map.LobbyOption("difficulty") == "normal" or Map.LobbyOption("difficulty") == "hard" then
		EggsDestroyed()
		Media.DisplayMessage("Incomming mothership detected...")
		Trigger.AfterDelay(DateTime.Seconds(7), function()
			Media.PlaySound("mothershipdeployed.aud")
			Trigger.AfterDelay(DateTime.Seconds(3), function()
				Media.PlaySound("Chrono.aud")
				Trigger.AfterDelay(DateTime.Seconds(4), function()
					Lightning()
					local delay = Utils.RandomInteger(20, 10)
					Lighting.Flash("LightningStrike", delay)
					Lighting.Flash("LightningStrike", delay)
					ChronoShift = Actor.Create(Mothership, true, { Owner = Aliens, Location = MotherShipWaypoint.Location })
					Trigger.AfterDelay(DateTime.Seconds(0.5), function()
						ChronoShift.Kill()
						AlienMothership = Actor.Create(Mothership, true, { Owner = Aliens, Location = MotherShipWaypoint.Location })
						--Smoke1 = Actor.Create(Smoke, true, { Owner = Neutral, Location = MotherShipWaypoint.Location })
						--Smoke2 = Actor.Create(Smoke, true, { Owner = Neutral, Location = WaypointMiddle.Location })
						Trigger.AfterDelay(DateTime.Seconds(5), function()
							AlienSendWave()
							Trigger.OnKilled(AlienMothership, MothershipDestroyed) 
						end)
					end)
				end)
			end)
		end)
	end
end

-----------AlienSpawns
AlienMonsterEntryPoints = { MotherShipWaypoint }
AlienSpawnPoints = { Waypoint2, Waypoint, Waypoint2, Waypoint3 }

if Map.LobbyOption("difficulty") == "normal" then
	Mechwarrior = { "mechwarrior", "mechwarrior", "mechwarrior", "mechwarrior" }
	Exciter = { "exciter", "exciter", "exciter", "exciter" }
	Tripod = { "tripod", "tripod", "tripod" }
end

AlienWave = 0
AlienWaves =
{
	{ delay = 1, units = { Tripod } },
	{ delay = 1, units = { Mechwarrior } },
	{ delay = 1, units = { Exciter, Exciter } },
	{ delay = 1, units = { Mechwarrior, Mechwarrior } },
	{ delay = 1, units = { Exciter, Exciter, Exciter, Exciter } },
	{ delay = 1, units = { Tripod, Tripod } },
	{ delay = 1, units = { Tripod } },
	{ delay = 1, units = { Mechwarrior } },
	{ delay = 1, units = { Exciter, Exciter } },
	{ delay = 1, units = { Mechwarrior, Mechwarrior } },
	{ delay = 1, units = { Exciter, Exciter, Exciter, Exciter } },
	{ delay = 1, units = { Tripod, Tripod } }
}

SendAlienUnits = function(entryCell, unitTypes, targetCell)
	Reinforcements.Reinforce(Aliens, unitTypes, { entryCell }, 40, function(a)
		if not a.HasProperty("AttackMove") then
			Trigger.OnIdle(a, function(a)
				a.Move(targetCell)
			end)
			return
		end

		a.AttackMove(targetCell)
		Trigger.OnIdle(a, function(a)
			a.Hunt()
		end)
	end)
end

AlienIncreaseDifficulty = function()
	local additions = { ExoMech, Exciter, ExoMech, Exciter, Tripod, Tripod }
	Utils.Do(AlienWaves, function(wave)
		wave.units[#wave.units + 1] = Utils.Random(additions)
	end)
end

AlienSendWave = function()
	if AlienMothership.IsDead then
		return
	end
	AlienWave = AlienWave + 1
	local wave = AlienWaves[AlienWave]
	Trigger.AfterDelay(wave.delay, function()
		Utils.Do(wave.units, function(units)
			local entry = Utils.Random(AlienMonsterEntryPoints).Location
			local target = Utils.Random(AlienSpawnPoints).Location
			SendAlienUnits(entry, units, target)
		end)
		if (AlienWave < #AlienWaves) then
			delayFirstTeam = 40
			local delay = delayFirstTeam
			Trigger.AfterDelay(DateTime.Seconds(delay), function()
				AlienSendWave()
				Trigger.AfterDelay(DateTime.Minutes(7), AlienIncreaseDifficulty)
			end)
		end
	end)
end

AlienMonsterEntryPoints = { MotherShipWaypoint }
AlienSpawnPoints = { Waypoint2, Waypoint, Waypoint2, Waypoint3 }

if Map.LobbyOption("difficulty") == "hard" then
	Mechwarrior = { "mechwarrior", "mechwarrior", "mechwarrior", "mechwarrior" }
	Exciter = { "exciter", "exciter", "exciter" }
	Tripod = { "tripod", "tripod", "tripod", "tripod" }
end

AlienWave = 0
AlienWaves =
{
	{ delay = 1, units = { Tripod } },
	{ delay = 1, units = { Mechwarrior } },
	{ delay = 1, units = { Exciter, Exciter } },
	{ delay = 1, units = { Mechwarrior, Mechwarrior } },
	{ delay = 1, units = { Exciter, Exciter, Exciter, Exciter } },
	{ delay = 1, units = { Tripod, Tripod } },
	{ delay = 1, units = { Tripod } },
	{ delay = 1, units = { Mechwarrior } },
	{ delay = 1, units = { Exciter, Exciter } },
	{ delay = 1, units = { Mechwarrior, Mechwarrior } },
	{ delay = 1, units = { Exciter, Exciter, Exciter, Exciter } },
	{ delay = 1, units = { Tripod, Tripod } }
}

SendAlienUnits = function(entryCell, unitTypes, targetCell)
	Reinforcements.Reinforce(Aliens, unitTypes, { entryCell }, 40, function(a)
		if not a.HasProperty("AttackMove") then
			Trigger.OnIdle(a, function(a)
				a.Move(targetCell)
			end)
			return
		end

		a.AttackMove(targetCell)
		Trigger.OnIdle(a, function(a)
			a.Hunt()
		end)
	end)
end

AlienIncreaseDifficulty = function()
	local additions = { ExoMech, Exciter, ExoMech, Exciter, Tripod, Tripod }
	Utils.Do(AlienWaves, function(wave)
		wave.units[#wave.units + 1] = Utils.Random(additions)
	end)
end

AlienSendWave = function()
	if AlienMothership.IsDead then
		return
	end
	AlienWave = AlienWave + 1
	local wave = AlienWaves[AlienWave]
	Trigger.AfterDelay(wave.delay, function()
		Utils.Do(wave.units, function(units)
			local entry = Utils.Random(AlienMonsterEntryPoints).Location
			local target = Utils.Random(AlienSpawnPoints).Location
			SendAlienUnits(entry, units, target)
		end)
		if (AlienWave < #AlienWaves) then
			delayFirstTeam = 40
			local delay = delayFirstTeam
			Trigger.AfterDelay(DateTime.Seconds(delay), function()
				AlienSendWave()
				Trigger.AfterDelay(DateTime.Minutes(7), AlienIncreaseDifficulty)
			end)
		end
	end)
end

--Game Over check
MissionOverCheckMonster = { MonsterMissionAccomplished }
MissionOverCheckAlien = { AlienMissionAccomplished }

EggsDestroyed = function()
	Utils.Do(MissionOverCheckMonster, function(a)
		if not a.IsDead and a.Owner == Monsters then
			a.Destroy()
		end
	end)
end

MothershipDestroyed = function()
	if Map.LobbyOption("difficulty") == "hard" then
		Actor.Create(Weapons, true, { Owner = Aliens, Location = WaypointMiddle.Location })
	end
	Utils.Do(MissionOverCheckAlien, function(a)
		if not a.IsDead and a.Owner == Aliens then
			a.Destroy()
		end
	end)
end

--AI Behavior
SendUnits = function(entryCell, unitTypes, targetCell)
	Reinforcements.Reinforce(Monsters, unitTypes, { entryCell }, 40, function(a)
		if not a.HasProperty("AttackMove") then
			Trigger.OnIdle(a, function(a)
				a.Move(targetCell)
			end)
			return
		end

		a.AttackMove(targetCell)
		Trigger.OnIdle(a, function(a)
			a.Hunt()
		end)
	end)
end

GameOver = function()
	Utils.Do(MissionOverCheckMonster, function(a)
		if not a.IsDead and a.Owner == Monsters then
			a.Destroy()
		end
	end)
end
--eggs
Eggs = { Egg, Egg1, Egg2, Egg3, Egg4, Egg5, Egg6, Egg7 }
Fire = "boxes01"
Mothership = "mothership"
Smoke = "flare"
TechCrate = "techcrate"
Weapons = "weaponscrate"
WorldLoaded = function()
	WorldLoadedGeneralsPromotions()
--factions
	Neutral = Player.GetPlayer("Neutral")
	Monsters = Player.GetPlayer("Monsters")
	Aliens = Player.GetPlayer("Aliens")
	Media.DisplayMessage("Destroy the Egg spawns")
	Trigger.OnAllRemovedFromWorld(Eggs, function()
		GameOver()
		MothershipChrono()
	end)
--egg spawn commands
	EggSendWave()
	Egg1SendWave()
	Egg3SendWave()
	Egg5SendWave()
	Egg7SendWave()

--endless spawn trigger
	Trigger.AfterDelay(DateTime.Minutes(14), function()
		EggIncreaseDifficulty()
		Egg1IncreaseDifficulty()
		Egg3IncreaseDifficulty()
		Egg5IncreaseDifficulty()
		Egg7IncreaseDifficulty()
	end)

--weather and effects
	local delay = Utils.RandomInteger(20, 10)
	Lighting.Flash("LightningStrike", delay)
	Lighting.Flash("LightningStrike", delay)
	Media.PlaySound("thunder3.aud")
end
Lightning = function() 
	local delay = Utils.RandomInteger(20, 10)
	Lighting.Flash("LightningStrike", delay)
	Lighting.Flash("LightningStrike", delay)
	Tick = function()
		TickPromotions()
		if (Utils.RandomInteger(1, 200) == 10) then
			local delay = Utils.RandomInteger(1, 10)
			Lighting.Flash("LightningStrike", delay)
			Trigger.AfterDelay(delay, function()
				Media.PlaySound("thunder" .. Utils.RandomInteger(1,6) .. ".aud")
			end)
		end
		if (Utils.RandomInteger(1, 200) == 10) then
			Media.PlaySound("thunder-ambient.aud")
		end
	end
end

