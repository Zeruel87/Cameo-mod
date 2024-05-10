Notification = function (text)
	Media.DisplayMessage(text, "Notification", HSLColor.SkyBlue)
end

Tip = function (text)
	Media.DisplayMessage(text, "Tip", HSLColor.DarkCyan)
end

Warning = function (text)
	Media.DisplayMessage(text, "Warning", HSLColor.Red)
end

InitObjectives = function(player)
	Trigger.OnObjectiveAdded(player, function(p, id)
		if p.IsLocalPlayer then
			Trigger.AfterDelay(1, function()
				local colour = HSLColor.Yellow
				if p.GetObjectiveType(id) ~= "Primary" then
					colour = HSLColor.Gray
				end
				Media.DisplayMessage(p.GetObjectiveDescription(id), "New " .. string.lower(p.GetObjectiveType(id)) .. " objective", colour)
			end)
		end
	end)

	Trigger.OnObjectiveCompleted(player, function(p, id)
		if p.IsLocalPlayer then
			Media.PlaySoundNotification(player, "AlertBleep")
			Media.DisplayMessage(p.GetObjectiveDescription(id), "Objective completed", HSLColor.LimeGreen)
		end
	end)

	Trigger.OnObjectiveFailed(player, function(p, id)
		if p.IsLocalPlayer then
			Media.DisplayMessage(p.GetObjectiveDescription(id), "Objective failed", HSLColor.Red)
		end
	end)

	Trigger.OnPlayerLost(player, function()
		if player.IsLocalPlayer then
			Trigger.AfterDelay(DateTime.Seconds(1), function()
				Media.PlaySpeechNotification(player, "MissionFailed")
			end)
		end
	end)

	Trigger.OnPlayerWon(player, function()
		if player.IsLocalPlayer then
			Trigger.AfterDelay(DateTime.Seconds(1), function()
				Media.PlaySpeechNotification(player, "MissionAccomplished")
			end)
		end
	end)
end

UnitHunt = function (a)
	Trigger.OnIdle(a, function (a)
		a.Hunt()
	end)
end

JPPoints = {JPSpawn.Location, JPDeploy.Location}
SecondMCVSpawn = {EnemySpawnThree.Location, SecondBaseDeploy.Location}

NitroTaskForceSmall = {"ftrk", "ftrk", "3tnk"}
NitroTaskForceMedium = {"ftrk", "ftrk", "ftrk", "3tnk", "3tnk", "v2rl"}
NitroTaskForceLarge = {"3tnk", "3tnk", "3tnk", "3tnk", "3tnk", "v2rl", "v2rl", "4tnk"}

NavySmall = {"ss"}
NavyLarge = {"ss", "msub"}

WorldLoaded = function ()
	NewHopeOne = Player.GetPlayer("NewHopeOne")
	NewHopeTwo = Player.GetPlayer("NewHopeTwo")
	Sankalpa = Player.GetPlayer("Sankalpa")
	Nitro = Player.GetPlayer("Nitro")
	NitroJP = Player.GetPlayer("NitroJP")
	Neutral = Player.GetPlayer("Neutral")

	InitObjectives(NewHopeOne)
	InitObjectives(NewHopeTwo)
	NewHopeObjectives = {
		NewHopeOne.AddPrimaryObjective("Defend the harbour until support arrives."),
		NewHopeTwo.AddPrimaryObjective("Defend the harbour until support arrives.")
	}
	
	DateTime.TimeLimit = DateTime.Minutes(20) + DateTime.Seconds(10)
	Trigger.AfterDelay(DateTime.Seconds(3), function ()
		Tip("BOTH Construction Yards must survive. They cannot be rebuilt.")
	end)
	
	Trigger.AfterDelay(DateTime.Seconds(10), RegularAttackWaves)

	Trigger.AfterDelay(DateTime.Minutes(3), function()
		Reinforcements.Reinforce(NitroJP, {"ramcv.japan"}, JPPoints, 0, function (mcv)
			Trigger.OnIdle(mcv, function (mcv)
				mcv.Deploy()
			end)
		end)
	end)

	Trigger.AfterDelay(DateTime.Minutes(10), function()
		Reinforcements.Reinforce(Nitro, {"ramcv.soviet"}, SecondMCVSpawn, 0, function (mcv)
			Trigger.OnIdle(mcv, function (mcv)
				mcv.Deploy()
			end)
		end)
	end)

	Trigger.OnKilled(PlayerOneMCV, function ()
		NewHopeOne.MarkFailedObjective(NewHopeObjectives[1])
		NewHopeTwo.MarkFailedObjective(NewHopeObjectives[2])
	end)

	Trigger.OnKilled(PlayerTwoMCV, function ()
		NewHopeOne.MarkFailedObjective(NewHopeObjectives[1])
		NewHopeTwo.MarkFailedObjective(NewHopeObjectives[2])
	end)

	Trigger.OnTimerExpired(function ()
		NewHopeOne.MarkCompletedObjective(NewHopeObjectives[1])
		NewHopeTwo.MarkCompletedObjective(NewHopeObjectives[2])
	end)

end

RegularAttackWaves = function ()
	if DateTime.GameTime < DateTime.Minutes(6) then
		SendSmallWaves()
	elseif DateTime.GameTime < DateTime.Minutes(12) then
		SendMediumWaves()
	else
		SendLargeWaves()
	end
	Trigger.AfterDelay(DateTime.Seconds(60), RegularAttackWaves)
end

SeaAttackWaves = function ()
	if DateTime.GameTime < DateTime.Minutes(12) then
		Reinforcements.Reinforce(Nitro, NavySmall, {EnemyNavySpawnOne.Location}, 0, UnitHunt)
		Reinforcements.Reinforce(Nitro, NavySmall, {EnemyNavySpawnTwo.Location}, 0, UnitHunt)
		Reinforcements.Reinforce(Nitro, NavySmall, {EnemyNavySpawnThree.Location}, 0, UnitHunt)
	else
		Reinforcements.Reinforce(Nitro, NavyLarge, {EnemyNavySpawnOne.Location}, 0, UnitHunt)
		Reinforcements.Reinforce(Nitro, NavyLarge, {EnemyNavySpawnTwo.Location}, 0, UnitHunt)
		Reinforcements.Reinforce(Nitro, NavyLarge, {EnemyNavySpawnThree.Location}, 0, UnitHunt)
	end
end

SendSmallWaves = function ()
	Reinforcements.Reinforce(Nitro, NitroTaskForceSmall, {EnemySpawnOne.Location}, 0, UnitHunt)
	Reinforcements.Reinforce(Nitro, NitroTaskForceSmall, {EnemySpawnTwo.Location}, 0, UnitHunt)
	Reinforcements.Reinforce(Nitro, NitroTaskForceSmall, {EnemySpawnThree.Location}, 0, UnitHunt)
end

SendMediumWaves = function ()
	Reinforcements.Reinforce(Nitro, NitroTaskForceMedium, {EnemySpawnOne.Location}, 0, UnitHunt)
	Reinforcements.Reinforce(Nitro, NitroTaskForceMedium, {EnemySpawnTwo.Location}, 0, UnitHunt)
	Reinforcements.Reinforce(Nitro, NitroTaskForceMedium, {EnemySpawnThree.Location}, 0, UnitHunt)
end

SendLargeWaves = function ()
	Reinforcements.Reinforce(Nitro, NitroTaskForceLarge, {EnemySpawnOne.Location}, 0, UnitHunt)
	Reinforcements.Reinforce(Nitro, NitroTaskForceLarge, {EnemySpawnTwo.Location}, 0, UnitHunt)
	Reinforcements.Reinforce(Nitro, NitroTaskForceLarge, {EnemySpawnThree.Location}, 0, UnitHunt)
end

Tick = function ()
	
end