
p1cash = function()
	if p1 and p1.IsBot then
		for m=1,#moneyall do
			citybottruck = p1.GetActorsByType("citybottruck")
			for _,Transfer in pairs(citybottruck) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p1.IsAlliedWith(Spieler) then
						moneyaction = Spieler.GetActorsByType(moneyall[m])
						for _,moneyaction in pairs(moneyaction) do Transfer.DeliverCash(moneyaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p1cash()
	end)
end
p2cash = function()
	if p2 and p2.IsBot then
		for m=1,#moneyall do
			citybottruck = p2.GetActorsByType("citybottruck")
			for _,Transfer in pairs(citybottruck) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p2.IsAlliedWith(Spieler) then
						moneyaction = Spieler.GetActorsByType(moneyall[m])
						for _,moneyaction in pairs(moneyaction) do Transfer.DeliverCash(moneyaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p2cash()
	end)
end
p3cash = function()
	if p3 and p3.IsBot then
		for m=1,#moneyall do
			citybottruck = p3.GetActorsByType("citybottruck")
			for _,Transfer in pairs(citybottruck) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p3.IsAlliedWith(Spieler) then
						moneyaction = Spieler.GetActorsByType(moneyall[m])
						for _,moneyaction in pairs(moneyaction) do Transfer.DeliverCash(moneyaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p3cash()
	end)
end
p4cash = function()
	if p4 and p4.IsBot then
		for m=1,#moneyall do
			citybottruck = p4.GetActorsByType("citybottruck")
			for _,Transfer in pairs(citybottruck) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p4.IsAlliedWith(Spieler) then
						moneyaction = Spieler.GetActorsByType(moneyall[m])
						for _,moneyaction in pairs(moneyaction) do Transfer.DeliverCash(moneyaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p4cash()
	end)
end
p5cash = function()
	if p5 and p5.IsBot then
		for m=1,#moneyall do
			citybottruck = p5.GetActorsByType("citybottruck")
			for _,Transfer in pairs(citybottruck) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p5.IsAlliedWith(Spieler) then
						moneyaction = Spieler.GetActorsByType(moneyall[m])
						for _,moneyaction in pairs(moneyaction) do Transfer.DeliverCash(moneyaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p5cash()
	end)
end
p6cash = function()
	if p6 and p6.IsBot then
		for m=1,#moneyall do
			citybottruck = p6.GetActorsByType("citybottruck")
			for _,Transfer in pairs(citybottruck) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p6.IsAlliedWith(Spieler) then
						moneyaction = Spieler.GetActorsByType(moneyall[m])
						for _,moneyaction in pairs(moneyaction) do Transfer.DeliverCash(moneyaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p6cash()
	end)
end
p7cash = function()
	if p7 and p7.IsBot then
		for m=1,#moneyall do
			citybottruck = p7.GetActorsByType("citybottruck")
			for _,Transfer in pairs(citybottruck) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p7.IsAlliedWith(Spieler) then
						moneyaction = Spieler.GetActorsByType(moneyall[m])
						for _,moneyaction in pairs(moneyaction) do Transfer.DeliverCash(moneyaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p7cash()
	end)
end
p8cash = function()
	if p8 and p8.IsBot then
		for m=1,#moneyall do
			citybottruck = p8.GetActorsByType("citybottruck")
			for _,Transfer in pairs(citybottruck) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p8.IsAlliedWith(Spieler) then
						moneyaction = Spieler.GetActorsByType(moneyall[m])
						for _,moneyaction in pairs(moneyaction) do Transfer.DeliverCash(moneyaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p8cash()
	end)
end
p9cash = function()
	if p9 and p9.IsBot then
		for m=1,#moneyall do
			citybottruck = p9.GetActorsByType("citybottruck")
			for _,Transfer in pairs(citybottruck) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p9.IsAlliedWith(Spieler) then
						moneyaction = Spieler.GetActorsByType(moneyall[m])
						for _,moneyaction in pairs(moneyaction) do Transfer.DeliverCash(moneyaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p9cash()
	end)
end
p10cash = function()
	if p10 and p10.IsBot then
		for m=1,#moneyall do
			citybottruck = p10.GetActorsByType("citybottruck")
			for _,Transfer in pairs(citybottruck) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p10.IsAlliedWith(Spieler) then
						moneyaction = Spieler.GetActorsByType(moneyall[m])
						for _,moneyaction in pairs(moneyaction) do Transfer.DeliverCash(moneyaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p10cash()
	end)
end
p11cash = function()
	if p11 and p11.IsBot then
		for m=1,#moneyall do
			citybottruck = p11.GetActorsByType("citybottruck")
			for _,Transfer in pairs(citybottruck) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p11.IsAlliedWith(Spieler) then
						moneyaction = Spieler.GetActorsByType(moneyall[m])
						for _,moneyaction in pairs(moneyaction) do Transfer.DeliverCash(moneyaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p11cash()
	end)
end
p12cash = function()
	if p12 and p12.IsBot then
		for m=1,#moneyall do
			citybottruck = p12.GetActorsByType("citybottruck")
			for _,Transfer in pairs(citybottruck) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p12.IsAlliedWith(Spieler) then
						moneyaction = Spieler.GetActorsByType(moneyall[m])
						for _,moneyaction in pairs(moneyaction) do Transfer.DeliverCash(moneyaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p12cash()
	end)
end
p13cash = function()
	if p13 and p13.IsBot then
		for m=1,#moneyall do
			citybottruck = p13.GetActorsByType("citybottruck")
			for _,Transfer in pairs(citybottruck) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p13.IsAlliedWith(Spieler) then
						moneyaction = Spieler.GetActorsByType(moneyall[m])
						for _,moneyaction in pairs(moneyaction) do Transfer.DeliverCash(moneyaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p13cash()
	end)
end
p14cash = function()
	if p14 and p14.IsBot then
		for m=1,#moneyall do
			citybottruck = p14.GetActorsByType("citybottruck")
			for _,Transfer in pairs(citybottruck) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p14.IsAlliedWith(Spieler) then
						moneyaction = Spieler.GetActorsByType(moneyall[m])
						for _,moneyaction in pairs(moneyaction) do Transfer.DeliverCash(moneyaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p14cash()
	end)
end
p15cash = function()
	if p15 and p15.IsBot then
		for m=1,#moneyall do
			citybottruck = p15.GetActorsByType("citybottruck")
			for _,Transfer in pairs(citybottruck) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p15.IsAlliedWith(Spieler) then
						moneyaction = Spieler.GetActorsByType(moneyall[m])
						for _,moneyaction in pairs(moneyaction) do Transfer.DeliverCash(moneyaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p15cash()
	end)
end
p16cash = function()
	if p16 and p16.IsBot then
		for m=1,#moneyall do
			citybottruck = p16.GetActorsByType("citybottruck")
			for _,Transfer in pairs(citybottruck) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p16.IsAlliedWith(Spieler) then
						moneyaction = Spieler.GetActorsByType(moneyall[m])
						for _,moneyaction in pairs(moneyaction) do Transfer.DeliverCash(moneyaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p16cash()
	end)
end
