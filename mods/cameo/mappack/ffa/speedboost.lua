WorldLoaded = function()
	WorldLoadedGeneralsPromotions()

	powerall = {
		"citybotcoal","citybotnuke","nuk2","nuke","apwr","powr","ra2gapowr","ra2nanrct","ra2napowr","yryapowr",
		"2100power","2100scavpowr","scsupplydepot","scpylon","cityboti","cityi","cityc","citybotr","citybotr2","cityr","citymayor",
	}

	moneyall = {
		"fact.gdi","pyle","weap","hpad.gdi",
		"fact.nod","hand","afld","hpad.nod",
		"rafact.allies","tent","raweapa","rahpad",
		"rafact.soviet","barr","raweap","raafld",
		"ra2gacnst","ra2gapile","ra2gaweap","ra2gaairc",
		"ra2nacnst","ra2nahand","ra2naweap",
		"yrnacnst","yryabrck","yrygweap",
		"2100hq.alpha","2100fy1","2100fy2",
		"2100hq.scavenger","2100chopshop","2100chopshopadv","2100scavhangar",
		"sccommandcenter","scbarracks","scfactory","scstarport",
		"scnexus","scgateway","scroboticsfacility","scstargate",
		"schatchery","tsgtcnstgdi","tsgtcnstnod","tsgtcnstcabal","tsgtcnstmutant"
	}

	infantryall = {
		"rmbo","e3","e2","e4","e5","e1",
		"e7","shok","rae4","rae3","rae2","rae1","dog",
		"ra2tany","ra2seal","ra2e1","ra2cleg","yrggi","ra2snipe",
		"yrboris","ra2e2","ra2flakt","ra2deso","ra2ivan","ra2shk",
		"yryurix","yrvirus","yrjulia","ra2yuri","yryuri","yrbrute","yrinit",
		"2100scav",
		"scghost","scfirebat","scmarine",
		"sczealot","scdragoon","schightemplar","scdarktemplar",
		"schydralisk","sczergling",
		"cityfirefighter","citypoliceofficer",
	}

	vehicleall = {
		"citypolicecar","cityfiretruck",
		"htnk","msam","mtnk","apc","jeep",
		"stnk","arty","ltnk","ftnk","mlrs","bike","bggy",
		"ctnk","2tnk","raarty","1tnk","rajeep",
		"4tnk","v2rl","3tnk","ttnk","ftrk","raapc",
		"ra2mtnk","yrrobo","ra2tnkd","ra2fv","ra2fvbotmg","ra2fvbotms","ra2fvbotrep","ra2sref","ra2mgtk","yrbfrt","yrbfrt.bot",
		"ra2apoc","ra2htnk","ra2htk","ra2v3","ra2ttnk",
		"yrytnk","yrltnk","yrtele","yrcaos","yrmind",
		"2100hpt","2100apt","2100mch","2100tch","2100rvw","2100mvw","2100rvw2","2100mvw2",
		"2100icecream","2100scavtruck","2100ftruk","2100tractor","2100jeepmsl","2100jeep","2100trike",
		"scgoliath","scvulture","scsiegetank",
		"scarchon","screaver",
		"scultralisk",
	}

	p1 = Player.GetPlayer("Multi0")
	p2 = Player.GetPlayer("Multi1")
	p3 = Player.GetPlayer("Multi2")
	p4 = Player.GetPlayer("Multi3")
	p5 = Player.GetPlayer("Multi4")
	p6 = Player.GetPlayer("Multi5")
	p7 = Player.GetPlayer("Multi6")
	p8 = Player.GetPlayer("Multi7")
	p9 = Player.GetPlayer("Multi8")
	p10 = Player.GetPlayer("Multi9")
	p11 = Player.GetPlayer("Multi10")
	p12 = Player.GetPlayer("Multi11")
	p13 = Player.GetPlayer("Multi12")
	p14 = Player.GetPlayer("Multi13")
	p15 = Player.GetPlayer("Multi14")
	p16 = Player.GetPlayer("Multi15")

	p1cash()
	p2cash()
	p3cash()
	p4cash()
	p5cash()
	p6cash()
	p7cash()
	p8cash()
	p9cash()
	p10cash()
	p11cash()
	p12cash()
	p13cash()
	p14cash()
	p15cash()
	p16cash()

	p1scavengercash()
	p2scavengercash()
	p3scavengercash()
	p4scavengercash()
	p5scavengercash()
	p6scavengercash()
	p7scavengercash()
	p8scavengercash()
	p9scavengercash()
	p10scavengercash()
	p11scavengercash()
	p12scavengercash()
	p13scavengercash()
	p14scavengercash()
	p15scavengercash()
	p16scavengercash()

	Trigger.AfterDelay(DateTime.Seconds(3), function()
		Utils.Do(Map.ActorsInWorld, function(actor)
			if actor.HasProperty("GrantCondition") then
				actor.GrantCondition("speedboost", DateTime.Seconds(30))
			end
		end)
	end)
end
