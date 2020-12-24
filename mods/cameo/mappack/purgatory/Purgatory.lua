-- elseif Map.LobbyOption("difficulty") == "normal" then
-- 	Mutants = { "pvice" }
-- 	Mutantsx2 = { "pvice", "pvice" }
-- 	Arachnotron = { "bspi" }
-- 	Arachnotronx2 = { "bspi", "bspi" }
-- 	Reve = { "reve" }
-- 	Revex2 = { "reve", "reve" }
-- 	Imp = { "imp" }
-- 	Impx2 = { "imp", "imp" }
-- 	Demon = { "pinky" }
-- 	Demonx2 = { "pinky", "pinky" }
-- 	Mancubus = { "manc" }
-- 	Mancubusx2 = { "manc", "manc" }

-- new
EggMonsterEntryPoints = { MonsterWaypoint }
EggSpawnPoints = { Waypoint, Waypoint1, Waypoint2, Waypoint3, Waypoint4, Waypoint5, Waypoint6, Waypoint7 }

if Map.LobbyOption("difficulty") == "hard" then
	Mutants = { "pvice", "pvice" }
	Mutantsx2 = { "pvice", "pvice", "pvice"  }
	Arachnotron = { "bspi", "bspi", }
	Arachnotronx2 = { "bspi", "bspi", "bspi" }
	Reve = { "reve", "reve" }
	Revex2 = { "reve", "reve", "reve" }
	Imp = { "imp", "imp" }
	Impx2 = { "imp", "imp", "imp" }
	Demon = { "pinky", "pinky" }
	Demonx2 = { "pinky", "pinky", "pinky" }
	Mancubus = { "manc", "manc" }
	Mancubusx2 = { "manc", "manc" }
elseif Map.LobbyOption("difficulty") == "normal" then
	Mutants = { "pvice", "pvice" }
	Mutantsx2 = { "pvice", "pvice", "pvice" }
	Arachnotron = { "bspi", "bspi" }
	Arachnotronx2 = { "bspi", "pvice", "pvice" }
	Reve = { "reve", "reve", "bspi" }
	Revex2 = { "reve", "pvice", "pvice", "bspi" }
	Imp = { "imp", "imp", "bspi", "pvice" }
	Impx2 = { "imp", "pvice", "pvice", "reve" }
	Demon = { "pinky", "pinky" }
	Demonx2 = { "pinky", "pvice", "pvice", "imp" }
	Mancubus = { "manc", "manc" }
	Mancubusx2 = { "manc", "pvice", "pvice", "pinky" }
elseif Map.LobbyOption("difficulty") == "easy" then
	Mutants = { "pvice" }
	Mutantsx2 = { "pvice" }
	Arachnotron = { "bspi" }
	Arachnotronx2 = { "bspi" }
	Reve = { "reve" }
	Revex2 = { "reve" }
	Imp = { "imp" }
	Impx2 = { "imp" }
	Demon = { "pinky" }
	Demonx2 = { "pinky" }
	Mancubus = { "manc" }
	Mancubusx2 = { "manc" }
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
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Reve, Arachnotron, Reve, Arachnotron, Mutants, Mutants, } },--440
	{ delay = 1, units = { Mutantsx2, Arachnotron, Reve, Mutantsx2, Arachnotronx2, Arachnotronx2, Arachnotron, Mutants } },--420
	{ delay = 1, units = { } },
	{ delay = 1, units = { Mutantsx2, Mutants, Mutantsx2, Arachnotron, Arachnotron, Arachnotronx2, Revex2, Reve, Reve, Mutantsx2 } },--500
	{ delay = 1, units = { Arachnotronx2, Mutantsx2, Revex2, Reve, Imp, Mutants, Mutants } },--540
	{ delay = 1, units = { Revex2, Revex2, Imp, Imp, Arachnotronx2, Arachnotronx2, Mutantsx2, Mutantsx2, Mutantsx2 } },--620
	{ delay = 1, units = { } },
	{ delay = 1, units = { Imp, Imp, Imp, Imp, Imp, Mutantsx2, Mutantsx2, Revex2 } },--700
	{ delay = 1, units = { Impx2, Impx2, Impx2, Mutantsx2, Mutantsx2, Mutantsx2, Revex2 } },--740
	{ delay = 1, units = { Impx2, Revex2, Arachnotronx2,Mutantsx2 } },--820
	{ delay = 1, units = { Demon, Demon, Demon, Demon, Reve, Reve, Mancubus } },--920
	{ delay = 1, units = { } },--1000
	{ delay = 1, units = { Demonx2, Demon, Demon, Impx2, Revex2 } },--10:40
	{ delay = 1, units = { Demon, Demon, Mutantsx2 } },--11:20
	{ delay = 1, units = { Mutants, Mutants, Mancubus, Mutantsx2, Reve, Reve, Reve, Reve } },--240
	{ delay = 1, units = { } },
	{ delay = 1, units = { Mancubus, Mancubus, Reve } }
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
	local additions = { Mutants, Arachnotron, Reve, Imp, Demon, Mancubus }
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
	Mutants = { "pvice", "pvice" }
	Mutantsx2 = { "pvice", "pvice", "pvice"  }
	Arachnotron = { "bspi", "bspi", }
	Arachnotronx2 = { "bspi", "bspi", "bspi" }
	Reve = { "reve", "reve" }
	Revex2 = { "reve", "reve", "reve" }
	Imp = { "imp", "imp" }
	Impx2 = { "imp", "imp", "imp" }
	Demon = { "pinky", "pinky" }
	Demonx2 = { "pinky", "pinky", "pinky" }
	Mancubus = { "manc", "manc" }
	Mancubusx2 = { "manc", "manc" }
elseif Map.LobbyOption("difficulty") == "normal" then
	Mutants = { "pvice", "pvice" }
	Mutantsx2 = { "pvice", "pvice", "pvice" }
	Arachnotron = { "bspi", "bspi" }
	Arachnotronx2 = { "bspi", "pvice", "pvice" }
	Reve = { "reve", "reve", "bspi" }
	Revex2 = { "reve", "pvice", "pvice", "bspi" }
	Imp = { "imp", "imp", "bspi", "pvice" }
	Impx2 = { "imp", "pvice", "pvice", "reve" }
	Demon = { "pinky", "pinky" }
	Demonx2 = { "pinky", "pvice", "pvice", "imp" }
	Mancubus = { "manc", "manc" }
	Mancubusx2 = { "manc", "pvice", "pvice", "pinky" }
elseif Map.LobbyOption("difficulty") == "easy" then
	Mutants = { "pvice" }
	Mutantsx2 = {  }
	Arachnotron = { "bspi" }
	Arachnotronx2 = { "pvice" }
	Reve = { "reve" }
	Revex2 = { "pvice" }
	Imp = { "imp" }
	Impx2 = { "pvice"  }
	Demon = { "pinky" }
	Demonx2 = { "pvice"  }
	Mancubus = { "manc" }
	Mancubusx2 = { "pvice" }
end
--Arachnotron
Egg1Wave = 0
Egg1Waves =
{
	{ delay = 1, units = { } },--00
	{ delay = 1, units = { Mutants } },--1:00
	{ delay = 1, units = { Mutants, Mutants, Arachnotron, Mutants } },--2
	{ delay = 1, units = { Arachnotron, Arachnotron, Reve, Mutantsx2, Mutantsx2, Mutantsx2, Mutantsx2 } },--3
	{ delay = 1, units = { Arachnotronx2, Arachnotronx2, Reve, Reve, Mutantsx2, Mutantsx2, Mutantsx2 } },--4
	{ delay = 1, units = { Arachnotronx2, Arachnotronx2, Reve, Reve, Imp, Mutantsx2, Mutantsx2 } },--5
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Revex2, Revex2, Imp, Imp, Impx2, Arachnotronx2, } },--6
	{ delay = 1, units = { Impx2, Mutantsx2, Imp, Revex2, Demon, Imp, Arachnotronx2, Arachnotronx2, Reve } },--7
	{ delay = 1, units = { } },--8
	{ delay = 1, units = { Impx2, Mutantsx2, Mancubus, Arachnotronx2, Demon, Mutantsx2, Revex2 } },--9
	{ delay = 1, units = { Mutantsx2, Demonx2, Arachnotronx2, Demon, Mutantsx2, Revex2 } },--10
	{ delay = 1, units = { Mancubus, Mutantsx2, Arachnotronx2, Mutantsx2 } },--11
	{ delay = 1, units = { } },--12
	{ delay = 1, units = { Mancubus, Revex2 } },--13
	{ delay = 1, units = { Mancubus, Revex2, Demon, Demon } }--14
}

Egg1IncreaseDifficulty = function()
	local additions = { Mutants, Arachnotron, Reve, Imp, Demon, Mancubus }
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
	Mutants = { "pvice", "pvice" }
	Mutantsx2 = { "pvice", "pvice", "pvice"  }
	Arachnotron = { "bspi", "bspi", }
	Arachnotronx2 = { "bspi", "bspi", "bspi" }
	Reve = { "reve", "reve" }
	Revex2 = { "reve", "reve", "reve" }
	Imp = { "imp", "imp" }
	Impx2 = { "imp", "imp", "imp" }
	Demon = { "pinky", "pinky" }
	Demonx2 = { "pinky", "pinky", "pinky" }
	Mancubus = { "manc", "manc" }
	Mancubusx2 = { "manc", "manc" }
elseif Map.LobbyOption("difficulty") == "normal" then
	Mutants = { "pvice", "pvice" }
	Mutantsx2 = { "pvice", "pvice", "pvice" }
	Arachnotron = { "bspi", "bspi" }
	Arachnotronx2 = { "bspi", "pvice", "pvice" }
	Reve = { "reve", "reve", "bspi" }
	Revex2 = { "reve", "pvice", "pvice", "bspi" }
	Imp = { "imp", "imp", "bspi", "pvice" }
	Impx2 = { "imp", "pvice", "pvice", "reve" }
	Demon = { "pinky", "pinky" }
	Demonx2 = { "pinky", "pvice", "pvice", "imp" }
	Mancubus = { "manc", "manc" }
	Mancubusx2 = { "manc", "pvice", "pvice", "pinky" }
elseif Map.LobbyOption("difficulty") == "easy" then
	Mutants = { "pvice" }
	Mutantsx2 = { "pvice" }
	Arachnotron = { "bspi" }
	Arachnotronx2 = { "pvice" }
	Reve = { "reve" }
	Revex2 = { "pvice" }
	Imp = { "imp" }
	Impx2 = { "pvice"  }
	Demon = { "pinky" }
	Demonx2 = { "pvice"  }
	Mancubus = { "manc" }
	Mancubusx2 = { "pvice" }
end
--Reve
Egg2Wave = 0
Egg2Waves =
{
	{ delay = 1, units = { } },--0
	{ delay = 1, units = { Mutants } },--110
	{ delay = 1, units = { Arachnotron, Mutantsx2, Arachnotron } },--220
	{ delay = 1, units = { Arachnotron, Arachnotronx2, Mutantsx2, Reve, Mutantsx2 } },--330
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Arachnotronx2, Reve, Mutantsx2 } },--440
	{ delay = 1, units = { Mutants, Mutants, Mutants, Mutants, Mutants, Imp } },--550
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Imp, Imp, Arachnotronx2, Revex2, Reve } },--700
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Revex2, Arachnotronx2, Impx2, Imp, Imp } },--810
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Mancubus, Impx2, Imp, Imp, Arachnotronx2, Arachnotronx2, Reve } },--920
	{ delay = 1, units = { Impx2, Imp, Imp, Mancubus, Arachnotronx2, Arachnotronx2, Demon, Reve, Mutantsx2 } },--1030
	{ delay = 1, units = { Imp, Imp, Mutantsx2, Mutantsx2, Mutantsx2, Mutants, Mutants, Mancubus } },--1140
	{ delay = 1, units = { Demon, Demon, Demon, Imp, Imp, Mancubus, Mutantsx2, Mutantsx2, Arachnotronx2, Mutantsx2, Reve } },--1250
	{ delay = 1, units = { Demonx2, Demonx2, Impx2, Impx2, Mutantsx2, Revex2 } },--1400
	{ delay = 1, units = { Mancubus, Demonx2 } },--1510
	{ delay = 1, units = { Mutants, Mutants, Mutants, Mutants, Mutants } },--1620
	{ delay = 1, units = { Mancubusx2, Mancubus } },--
}

Egg2IncreaseDifficulty = function()
	local additions = { Mutants, Arachnotron, Reve, Imp, Demon, Mancubus }
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
	Mutants = { "pvice", "pvice" }
	Mutantsx2 = { "pvice", "pvice", "pvice"  }
	Arachnotron = { "bspi", "bspi", }
	Arachnotronx2 = { "bspi", "bspi", "bspi" }
	Reve = { "reve", "reve" }
	Revex2 = { "reve", "reve", "reve" }
	Imp = { "imp", "imp" }
	Impx2 = { "imp", "imp", "imp" }
	Demon = { "pinky", "pinky" }
	Demonx2 = { "pinky", "pinky", "pinky" }
	Mancubus = { "manc", "manc" }
	Mancubusx2 = { "manc", "manc" }
elseif Map.LobbyOption("difficulty") == "normal" then
	Mutants = { "pvice", "pvice" }
	Mutantsx2 = { "pvice", "pvice", "pvice" }
	Arachnotron = { "bspi", "bspi" }
	Arachnotronx2 = { "bspi", "pvice", "pvice" }
	Reve = { "reve", "reve", "bspi" }
	Revex2 = { "reve", "pvice", "pvice", "bspi" }
	Imp = { "imp", "imp", "bspi", "pvice" }
	Impx2 = { "imp", "pvice", "pvice", "reve" }
	Demon = { "pinky", "pinky" }
	Demonx2 = { "pinky", "pvice", "pvice", "imp" }
	Mancubus = { "manc", "manc" }
	Mancubusx2 = { "manc", "pvice", "pvice", "pinky" }
elseif Map.LobbyOption("difficulty") == "easy" then
	Mutants = { "pvice" }
	Mutantsx2 = {  }
	Arachnotron = { "bspi" }
	Arachnotronx2 = { "pvice" }
	Reve = { "reve" }
	Revex2 = { "pvice" }
	Imp = { "imp" }
	Impx2 = { "pvice"  }
	Demon = { "pinky" }
	Demonx2 = { "pvice"  }
	Mancubus = { "manc" }
	Mancubusx2 = { "pvice" }
end

Egg3Wave = 0
Egg3Waves =
{
	{ delay = 1, units = { } },--00
	{ delay = 1, units = { Mutants } },--55
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Arachnotron, Arachnotron } },--150
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Arachnotronx2, Arachnotron, Arachnotron } },--245
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Mutantsx2, Mutantsx2, Arachnotron } },--340
	{ delay = 1, units = { Arachnotronx2, Arachnotronx2, Arachnotron, Arachnotron, Reve, Mutantsx2, Mutantsx2 } },--435
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Imp, Arachnotronx2, Arachnotronx2, Reve } },--530
	{ delay = 1, units = { Imp, Imp, Mutantsx2, Mutantsx2, Demon, Arachnotronx2, Arachnotronx2, Revex2, Reve } },--625
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Mutantsx2, Imp, Imp,Imp } },--720
	{ delay = 1, units = { Impx2, Imp, Mancubus, Demon, Reve, Arachnotronx2, Arachnotron, Arachnotron, Mutantsx2, Mutantsx2 } },--815
	{ delay = 1, units = { Demon, Demonx2, Demon, Imp, Impx2, Revex2, Mutantsx2, Mutantsx2 } },--910
	{ delay = 1, units = { Imp, Imp, Mancubus, Demon, Demon, Mutantsx2, Arachnotronx2, Arachnotronx2 } },--1005
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Mutantsx2 } },--1100
	{ delay = 1, units = { Mancubus, Mancubus, Mancubus, Impx2, Reve, Reve } },--1155
	{ delay = 1, units = { Mancubus, Mancubusx2, Revex2, Reve } },--1250
	{ delay = 1, units = { Mancubusx2, Mancubusx2, Mancubus, Revex2 } }--1345
}

Egg3IncreaseDifficulty = function()
	local additions = { Mutants, Arachnotron, Reve, Imp, Demon, Mancubus }
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
	Mutants = { "pvice", "pvice" }
	Mutantsx2 = { "pvice", "pvice", "pvice"  }
	Arachnotron = { "bspi", "bspi", }
	Arachnotronx2 = { "bspi", "bspi", "bspi" }
	Reve = { "reve", "reve" }
	Revex2 = { "reve", "reve", "reve" }
	Imp = { "imp", "imp" }
	Impx2 = { "imp", "imp", "imp" }
	Demon = { "pinky", "pinky" }
	Demonx2 = { "pinky", "pinky", "pinky" }
	Mancubus = { "manc", "manc" }
	Mancubusx2 = { "manc", "manc" }
elseif Map.LobbyOption("difficulty") == "normal" then
	Mutants = { "pvice", "pvice" }
	Mutantsx2 = { "pvice", "pvice", "pvice" }
	Arachnotron = { "bspi" }
	Arachnotronx2 = { "bspi", "pvice", "pvice" }
	Reve = { "reve", "reve", "bspi" }
	Revex2 = { "reve", "pvice", "pvice", "bspi" }
	Imp = { "imp", "imp", "bspi", "pvice" }
	Impx2 = { "imp", "pvice", "pvice", "reve" }
	Demon = { "pinky", "pinky" }
	Demonx2 = { "pinky", "pvice", "pvice", "imp" }
	Mancubus = { "manc", "manc" }
	Mancubusx2 = { "manc", "pvice", "pvice", "pinky" }
elseif Map.LobbyOption("difficulty") == "easy" then
	Mutants = { "pvice" }
	Mutantsx2 = {  }
	Arachnotron = { "bspi" }
	Arachnotronx2 = { "pvice" }
	Reve = { "reve" }
	Revex2 = { "pvice" }
	Imp = { "imp" }
	Impx2 = { "pvice"  }
	Demon = { "pinky" }
	Demonx2 = { "pvice"  }
	Mancubus = { "manc" }
	Mancubusx2 = { "pvice" }
end

Egg4Wave = 0
Egg4Waves =
{
	{ delay = 1, units = { } },--00
	{ delay = 1, units = { Mutants, Mutantsx2 } },--45
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Arachnotron, Arachnotron } },--130
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Arachnotronx2, Arachnotron, Mutantsx2 } },--215
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Reve } },--300
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Arachnotron, Arachnotronx2, Reve, Reve } },--345
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Mutants, Reve, Reve, Arachnotronx2, Arachnotron } },--430
	{ delay = 1, units = { Imp, Mutantsx2, Mutantsx2, Mutantsx2, Arachnotron, Arachnotron, Arachnotron, Reve } },--515
	{ delay = 1, units = { Mutantsx2, Imp, Imp, Mutantsx2 } },--600
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Imp, Imp, Impx2, Revex2, Demon, Demon } },--745
	{ delay = 1, units = { Demon, Mancubus, Arachnotron, Demon } },--830
	{ delay = 1, units = { Demonx2, Imp, Imp, Impx2, Mancubusx2, Revex2, Mutantsx2, Mutantsx2 } },--915
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Mutantsx2 } },--1000
	{ delay = 1, units = { Mancubus, Mancubusx2, Demonx2, Demonx2 } },--1145
	{ delay = 1, units = { Mancubus, Mutantsx2, Mancubus } }--1230
}

Egg4IncreaseDifficulty = function()
	local additions = { Mutants, Arachnotron, Reve, Imp, Demon, Mancubus }
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
	Mutants = { "pvice", "pvice" }
	Mutantsx2 = { "pvice", "pvice", "pvice"  }
	Arachnotron = { "bspi", "bspi", }
	Arachnotronx2 = { "bspi", "bspi", "bspi" }
	Reve = { "reve", "reve" }
	Revex2 = { "reve", "reve", "reve" }
	Imp = { "imp", "imp" }
	Impx2 = { "imp", "imp", "imp" }
	Demon = { "pinky", "pinky" }
	Demonx2 = { "pinky", "pinky", "pinky" }
	Mancubus = { "manc", "manc" }
	Mancubusx2 = { "manc", "manc" }
elseif Map.LobbyOption("difficulty") == "normal" then
	Mutants = { "pvice", "pvice" }
	Mutantsx2 = { "pvice", "pvice", "pvice" }
	Arachnotron = { "bspi", "bspi" }
	Arachnotronx2 = { "bspi", "pvice", "pvice" }
	Reve = { "reve", "reve", "bspi" }
	Revex2 = { "reve", "pvice", "pvice", "bspi" }
	Imp = { "imp", "imp", "bspi" }
	Impx2 = { "imp", "pvice", "pvice", "reve" }
	Demon = { "pinky", "pinky" }
	Demonx2 = { "pinky", "pvice", "pvice", "imp" }
	Mancubus = { "manc", "manc" }
	Mancubusx2 = { "manc", "pvice", "pvice", "pinky" }
elseif Map.LobbyOption("difficulty") == "easy" then
	Mutants = { "pvice" }
	Mutantsx2 = { "pvice" }
	Arachnotron = { "bspi" }
	Arachnotronx2 = { "pvice" }
	Reve = { "reve" }
	Revex2 = { "pvice" }
	Imp = { "imp" }
	Impx2 = { "pvice"  }
	Demon = { "pinky" }
	Demonx2 = { "pvice"  }
	Mancubus = { "manc" }
	Mancubusx2 = { "pvice" }
end

Egg5Wave = 0
Egg5Waves =
{
	{ delay = 1, units = { } },--00
	{ delay = 1, units = { Mutants } },--100
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Arachnotron, Arachnotronx2 } },--200
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Arachnotron, Arachnotronx2, Mutantsx2 } },--300
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Arachnotron, Mutantsx2, Revex2, Arachnotronx2 } },--400
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Reve, Reve } },--500
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Arachnotron, Arachnotron, Reve, Imp, Imp } },--600
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Imp, Arachnotronx2, Reve, Demon } },--700
	{ delay = 1, units = { Imp, Imp, Impx2, Demon, Demon, Mutantsx2, Arachnotronx2, Arachnotronx2, Reve, Revex2 } },--800
	{ delay = 1, units = { Impx2, Demon, Demon, Mancubus, Arachnotron, Arachnotronx2, Reve, Revex2 } },--900
	{ delay = 1, units = { Demonx2, Imp, Mancubus, Arachnotron, Arachnotron, Arachnotronx2, Revex2 } },--1000
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2 } },--1100
	{ delay = 1, units = { Mancubus, Mancubus, Mutantsx2, Imp, Mutantsx2, Revex2 } },--1200
	{ delay = 1, units = { Imp, Mancubus, Arachnotron, Reve } },--1300
	{ delay = 1, units = { Mancubus, Mancubusx2, Impx2 } }--1400
}

Egg5IncreaseDifficulty = function()
	local additions = { Mutants, Arachnotron, Reve, Imp, Demon, Mancubus }
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
	Mutants = { "pvice", "pvice" }
	Mutantsx2 = { "pvice", "pvice", "pvice"  }
	Arachnotron = { "bspi", "bspi", }
	Arachnotronx2 = { "bspi", "bspi", "bspi" }
	Reve = { "reve", "reve" }
	Revex2 = { "reve", "reve", "reve" }
	Imp = { "imp", "imp" }
	Impx2 = { "imp", "imp", "imp" }
	Demon = { "pinky", "pinky" }
	Demonx2 = { "pinky", "pinky", "pinky" }
	Mancubus = { "manc", "manc" }
	Mancubusx2 = { "manc", "manc" }
elseif Map.LobbyOption("difficulty") == "normal" then
	Mutants = { "pvice", "pvice" }
	Mutantsx2 = { "pvice", "pvice", "pvice" }
	Arachnotron = { "bspi" }
	Arachnotronx2 = { "bspi", "pvice", "pvice" }
	Reve = { "reve", "reve", "bspi" }
	Revex2 = { "reve", "pvice", "pvice", "bspi" }
	Imp = { "imp", "imp", "bspi", "pvice" }
	Impx2 = { "imp", "pvice", "pvice", "reve" }
	Demon = { "pinky", "pinky" }
	Demonx2 = { "pinky", "pvice", "pvice", "imp" }
	Mancubus = { "manc", "manc" }
	Mancubusx2 = { "manc", "pvice", "pvice", "pinky" }
elseif Map.LobbyOption("difficulty") == "easy" then
	Mutants = { "pvice" }
	Mutantsx2 = { "pvice" }
	Arachnotron = { "bspi" }
	Arachnotronx2 = { "pvice" }
	Reve = { "reve" }
	Revex2 = { "pvice" }
	Imp = { "imp" }
	Impx2 = { "pvice"  }
	Demon = { "pinky" }
	Demonx2 = { "pvice"  }
	Mancubus = { "manc" }
	Mancubusx2 = { "pvice" }
end

Egg6Wave = 0
Egg6Waves =
{
	{ delay = 1, units = { } },--00
	{ delay = 1, units = { Mutants } },--105
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Arachnotron, Arachnotron } },--210
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Reve, Arachnotron, Arachnotron } },--315
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Imp, Arachnotronx2, Reve, Arachnotron } },--420
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Reve, Reve } },--525
	{ delay = 1, units = { Arachnotronx2, Reve, Reve, Mutantsx2, Imp, Arachnotron } },--630
	{ delay = 1, units = { Arachnotronx2, Arachnotron, Arachnotron, Demon, Reve, Imp, Imp, Mutantsx2, Mutantsx2 } },--735
	{ delay = 1, units = { Revex2, Imp, Impx2, Imp, Arachnotronx2, Mutantsx2, Mutantsx2 } },--840
	{ delay = 1, units = { Demon, Mancubus, Imp, Impx2, Mutantsx2, Mutantsx2, Imp, Imp, Imp } },--945
	{ delay = 1, units = { Imp, Imp, Impx2, Mancubus, Mutantsx2, Mutantsx2, Demon, Demon } },--1050
	{ delay = 1, units = { Impx2, Demonx2, Mancubus, Imp, Mutantsx2, Revex2 } },--1155
	{ delay = 1, units = { Imp, Mutantsx2, Mancubus, Mutantsx2, Revex2 } },--1300
	{ delay = 1, units = { Mancubusx2, Mancubusx2, Revex2 } }--1405
}

Egg6IncreaseDifficulty = function()
	local additions = { Mutants, Arachnotron, Reve, Imp, Demon, Mancubus }
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
	Mutants = { "pvice", "pvice" }
	Mutantsx2 = { "pvice", "pvice", "pvice"  }
	Arachnotron = { "bspi", "bspi", }
	Arachnotronx2 = { "bspi", "bspi", "bspi" }
	Reve = { "reve", "reve" }
	Revex2 = { "reve", "reve", "reve" }
	Imp = { "imp", "imp" }
	Impx2 = { "imp", "imp", "imp" }
	Demon = { "pinky", "pinky" }
	Demonx2 = { "pinky", "pinky", "pinky" }
	Mancubus = { "manc", "manc" }
	Mancubusx2 = { "manc", "manc" }
elseif Map.LobbyOption("difficulty") == "normal" then
	Mutants = { "pvice", "pvice" }
	Mutantsx2 = { "pvice", "pvice", "pvice" }
	Arachnotron = { "bspi", "bspi" }
	Arachnotronx2 = { "bspi", "pvice", "pvice" }
	Reve = { "reve", "reve" }
	Revex2 = { "reve", "pvice", "pvice", "bspi" }
	Imp = { "imp", "imp", "bspi", "pvice" }
	Impx2 = { "imp", "pvice", "pvice", "reve" }
	Demon = { "pinky", "pinky" }
	Demonx2 = { "pinky", "pvice", "pvice", "imp" }
	Mancubus = { "manc", "manc" }
	Mancubusx2 = { "manc", "pvice", "pvice", "pinky" }
elseif Map.LobbyOption("difficulty") == "easy" then
	Mutants = { "pvice" }
	Mutantsx2 = { "pvice" }
	Arachnotron = { "bspi" }
	Arachnotronx2 = { "pvice" }
	Reve = { "reve" }
	Revex2 = { "pvice" }
	Imp = { "imp" }
	Impx2 = { "pvice"  }
	Demon = { "pinky" }
	Demonx2 = { "pvice"  }
	Mancubus = { "manc" }
	Mancubusx2 = { "pvice" }
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
	{ delay = 1, units = { Mutantsx2, Reve, Arachnotronx2, Mutantsx2, Mutantsx2, Reve } },--400
	{ delay = 1, units = { Mutantsx2, Mutantsx2, Mutantsx2, Arachnotronx2, Arachnotron, Revex2 } },--440
	{ delay = 1, units = { Arachnotron, Arachnotron, Mutantsx2, Mutantsx2, Reve, Imp } },--520
	{ delay = 1, units = { Imp, Imp, Arachnotronx2, Arachnotron, Imp, Revex2 } },--600
	{ delay = 1, units = { Impx2, Imp, Imp, Mutantsx2, Demon, Arachnotron, Arachnotronx2, Mutantsx2 } },--640
	{ delay = 1, units = { Demon, Imp, Impx2, Mutantsx2, Mutantsx2, Arachnotron } },--720
	{ delay = 1, units = { Mancubus, Arachnotron, Arachnotron, } },--800
	{ delay = 1, units = { Mancubus, Imp } },--840
	{ delay = 1, units = { Mancubus, Mancubusx2, Arachnotronx2, Mutantsx2, Reve } },--920
	{ delay = 1, units = { Mancubus, Arachnotron, Arachnotron, Demon, Imp, Impx2, Mutantsx2, Mutantsx2, } }
}

Egg7IncreaseDifficulty = function()
	local additions = { Mutants, Arachnotron, Reve, Imp, Demon, Mancubus }
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

