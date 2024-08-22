GoundAttackArrayTop = {Top1,Top2,Top3,Top4}
GoundAttackArrayRight= {Right1,Right2,Right3,Right4}
GoundAttackArraySouth = {South1,South2,South3,South4}
GoundAttackArrayLeft = {Left1,Left2,Left3,Left4}

GoundAttackArrayCorner1 = {TopLeft1,TopLeft2,TopLeft3,TopLeft4}
GoundAttackArrayCorner2= {TopRight1,TopRight2,TopRight3,TopRight4}
GoundAttackArrayCorner3 = {BottomRight1,BottomRight2,BottomRight3,BottomRight4}
GoundAttackArrayCorner4 = {BottomLeft1,BottomLeft2,BottomLeft3,BottomLeft4}

Foes = {}
Spielerzahl = 0
ActivePlayer = {}
Difficulty = 0
remainingTime = 0
Text = ""
Delay = 2 -- Delay between waves 2 min
SecondsDelay = 30 -- 30 sec


XTime = Delay --Start Delay
XSeconds = SecondsDelay --Start Delay
	
	
GetherData = function()	
	for i=1,4 do
		local Spieler = Player.GetPlayer("Multi" .. tostring(i-1))
		if Spieler ~= nil then
			table.insert(ActivePlayer, Spieler)
			Media.DisplayMessage("Multi" .. tostring(i-1) .. " is Playing!" ,"")
		end
		Spielerzahl = #ActivePlayer
	end
	Media.DisplayMessage(tostring(Spielerzahl) .. " player ... setting difficulty up ..." ,"")
	table.insert(Foes, Player.GetPlayer("True Nemesis"))
	table.insert(Foes, Player.GetPlayer("True Enemy"))
	table.insert(Foes, Player.GetPlayer("True Opponent"))
	table.insert(Foes, Player.GetPlayer("True Villian"))
	
end

Announce = function()
		if Spielerzahl == 1 then
			Difficulty = 1
			DisplayDifficulty = "Easy"
		elseif Spielerzahl == 2 then
			Difficulty = 3
			DisplayDifficulty = "Medium"
		elseif Spielerzahl == 3 then
			Difficulty = 6
			DisplayDifficulty = "Hard"
		elseif Spielerzahl == 4 then
			Difficulty = 10
			DisplayDifficulty = "Very Hard"
		end
		Media.DisplayMessage("Difficulty set to .... " .. DisplayDifficulty,"")
end



AttackGround = function(Type, Howmany, T2, T3, T4, T5, T6, T7)
	local stringerony = {}
	for i = 1, (Howmany+Difficulty) do
		table.insert(stringerony,Type)
		if T2 ~= nil then
			table.insert(stringerony,T2)
		end
		if T3 ~= nil then
			table.insert(stringerony,T3)
		end
		if T4 ~= nil then
			table.insert(stringerony,T4)
		end
		if T5 ~= nil then
			table.insert(stringerony,T5)
		end
		if T6 ~= nil then
			table.insert(stringerony,T6)
		end
		if T7 ~= nil then
			table.insert(stringerony,T7)
		end
	end
	for p = 1, 4 do
		Reinforcements.Reinforce(Foes[p],stringerony, { GoundAttackArrayTop[p].Location, GoundAttackArrayTop[p].Location + CVec.New(0,5) }, 8,
		function(Units)
			Units.AttackMove(CPos.New(50,50))
			IdleHunt(Units)
		end)
		Reinforcements.Reinforce(Foes[p],stringerony, { GoundAttackArrayRight[p].Location, GoundAttackArrayRight[p].Location + CVec.New(-5,0) }, 8, 
		function(Units)
			Units.AttackMove(CPos.New(50,50))
			IdleHunt(Units)
		end)
		Reinforcements.Reinforce(Foes[p],stringerony, { GoundAttackArraySouth[p].Location, GoundAttackArraySouth[p].Location + CVec.New(0,-5) }, 8,
		function(Units)
			Units.AttackMove(CPos.New(50,50))
			IdleHunt(Units)
		end)
		Reinforcements.Reinforce(Foes[p],stringerony, { GoundAttackArrayLeft[p].Location, GoundAttackArrayLeft[p].Location + CVec.New(5,0) }, 8,
		function(Units)
			Units.AttackMove(CPos.New(50,50))
			IdleHunt(Units)
		end)
	end

end

AttackAir = function(Type, Howmany, T2, T3, T4)
	local stringerony = {}
	for i = 1, (Howmany+Difficulty) do
		table.insert(stringerony,Type)
		if T2 ~= nil then
			table.insert(stringerony,T2)
		end
		if T3 ~= nil then
			table.insert(stringerony,T3)
		end
		if T4 ~= nil then
			table.insert(stringerony,T4)
		end
	end
	for p = 1, 4 do
		Reinforcements.Reinforce(Foes[p],stringerony, { GoundAttackArrayCorner1[p].Location, GoundAttackArrayCorner1[p].Location + CVec.New(5,5) }, 8,
		function(Units)
			Units.AttackMove(CPos.New(50,50))
			IdleHunt(Units)
		end)
		Reinforcements.Reinforce(Foes[p],stringerony, { GoundAttackArrayCorner2[p].Location, GoundAttackArrayCorner2[p].Location + CVec.New(-5,5) }, 8, 
		function(Units)
			Units.AttackMove(CPos.New(50,50))
			IdleHunt(Units)
		end)
		Reinforcements.Reinforce(Foes[p],stringerony, { GoundAttackArrayCorner3[p].Location, GoundAttackArrayCorner3[p].Location + CVec.New(-5,-5) }, 8,
		function(Units)
			Units.AttackMove(CPos.New(50,50))
			IdleHunt(Units)
		end)
		Reinforcements.Reinforce(Foes[p],stringerony, { GoundAttackArrayCorner4[p].Location, GoundAttackArrayCorner4[p].Location + CVec.New(5,-5) }, 8,
		function(Units)
			Units.AttackMove(CPos.New(50,50))
			IdleHunt(Units)
		end)
	end
end

IdleHunt = function(unit)
	if not unit.IsDead and unit.HasProperty("AttackMove") then
		Trigger.OnIdle(unit, unit.Hunt)
	end
end



WorldLoaded = function()
	Trigger.AfterDelay(DateTime.Seconds(3),GetherData)
	Trigger.AfterDelay(DateTime.Seconds(6),Announce)
	
	
	
	
	
	
	Trigger.AfterDelay(DateTime.Seconds(15),
	function()
	
		Media.DisplayMessage("Setting Up Timer!" ,"")
	
	
		timerStarted = true 
		Text = "Attacking Units: Rifle Gunner."
	
		remainingTime = DateTime.Minutes(3) + DateTime.Seconds(50)  -- 3:50
	end)

		
		Trigger.AfterDelay(DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay),
		function() 
			AttackGround("e1",4) 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Buggys." 
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("bggy",1) 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Basic Soldier Invasion."
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("e1",4,"rare1","ra2e1","ra2e2","yrinit") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Civilian Revolt."
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("c1",16,"c2","c3","c4","c5","c6") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Clone Wars."
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("steel_fedinf",12,"steel_qinf") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Flaky."
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("ra2htk",5,"ftrk","ra2flakt") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Schnitzel !!!! ."
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("yrgtrp",5,"yrgtrp","yrgtrp","ra2tnkd","yrgtrp") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Mutant Time!."
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("yrbrute",5,"vice") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking AIR Units: M60s."
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackAir("mh60",2) 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Weeb invasion."
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("aa_samurai",24) 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "BOSS ROUND Attacking Units: Schnitzel X2."
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("yrgtrp",5,"yrgtrp","yrgtrp","ra2tnkd","yrgtrp","modtiger") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Civilian The Vengeance"
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("c1",24,"c2","c3","c4","c5","c6","ra2harv","ra2harv","ra2harv") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Flames, Flames, Flames."
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("e4",3,"aa_flam","e3flamer","ftnk","aa_ftnk") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: My Chemical Romance"
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("e5",2,"e5","cheme3","chembike","yrvirus","yrbiot","chemssm") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Air Units: Migs"
		end)
		XSeconds = XSeconds + SecondsDelay
		XTime = XTime +Delay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackAir("mig",3) 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: UFO Invasion"
		end)
		XSeconds = XSeconds + SecondsDelay
		XTime = XTime +Delay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackAir("yrdisk",3,"yrlunr","yrlunr") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "BOSS ROUND  Attacking Units: Mig Family"
		end)
		XSeconds = XSeconds + SecondsDelay
		XTime = XTime +Delay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackAir("mig",3,"yrbpln1","aa_phoenix") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "BOSS ROUND  Attacking Units: Thicc"
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("ra2apoc",1, "steel_katy", "4tnk", "htnk") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "BOSS ROUND  Attacking Units: Commando Squad"
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("rmbo",1,"e7","volkov","gdihavoc","nodlasercommando") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Medium Tanks huh?"
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("mtnk",12,"2tnk","3tnk") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "BOSS ROUND  Attacking Units: Thicc 2"
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("5tnk",2, "4tnk", "htnk", "steel_katy", "ra2apoc") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Advanced Tanks"
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("nodltnk2",4, "gdipredator") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Air Units: Venom."
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackAir("nodvenom",4) 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Mechas"
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("aa_mecha",2,"steel_mega","steel_defender") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Battle Tanks!."
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("ra2mtnk",4,"ra2htnk","yrltnk","steel_qtank","aa_lynx") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: The Soviet Union."
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("ra2e2",12,"ra2flakt","ra2htnk","ra2htk","yrinit","ra2v3","ra2apoc","4tnk","3tnk") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Kirov Madness."
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackAir("ra2zep",8) 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Admin Closing"
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("monstertank",4,"ra2zep") 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Air Units: Venom."
		end)

		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
		Trigger.AfterDelay(DateTime.Minutes(XTime) + DateTime.Seconds(XSeconds),
		function() 
			AttackGround("e1",20) 
			timerStarted = true 
			remainingTime = DateTime.Minutes(Delay) + DateTime.Seconds(SecondsDelay)
			Text = "Attacking Units: Empty"
		end)
		XTime = XTime +Delay
		XSeconds = XSeconds + SecondsDelay
end


Tick = function()

	if remainingTime > 0 and timerStarted then
			UserInterface.SetMissionText(Text .. " Time until Attack: " .. Utils.FormatTime(remainingTime), Player.GetPlayer("Neutral").Color)
			remainingTime = remainingTime - 1
	end

end



