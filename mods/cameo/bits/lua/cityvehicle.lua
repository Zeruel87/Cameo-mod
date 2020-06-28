
p1vehicle = function()
	if p1 and p1.IsBot then
		for v=1,#vehicleall do
			cityboteliteexpert = p1.GetActorsByType("cityboteliteexpert")
			for _,Transfer in pairs(cityboteliteexpert) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p1.IsAlliedWith(Spieler) then
						vehicleaction = Spieler.GetActorsByType(vehicleall[v])
						for _,vehicleaction in pairs(vehicleaction) do Transfer.DeliverExperience(vehicleaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p1vehicle()
	end)
end
p2vehicle = function()
	if p2 and p2.IsBot then
		for v=1,#vehicleall do
			cityboteliteexpert = p2.GetActorsByType("cityboteliteexpert")
			for _,Transfer in pairs(cityboteliteexpert) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p2.IsAlliedWith(Spieler) then
						vehicleaction = Spieler.GetActorsByType(vehicleall[v])
						for _,vehicleaction in pairs(vehicleaction) do Transfer.DeliverExperience(vehicleaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p2vehicle()
	end)
end
p3vehicle = function()
	if p3 and p3.IsBot then
		for v=1,#vehicleall do
			cityboteliteexpert = p3.GetActorsByType("cityboteliteexpert")
			for _,Transfer in pairs(cityboteliteexpert) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p3.IsAlliedWith(Spieler) then
						vehicleaction = Spieler.GetActorsByType(vehicleall[v])
						for _,vehicleaction in pairs(vehicleaction) do Transfer.DeliverExperience(vehicleaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p3vehicle()
	end)
end
p4vehicle = function()
	if p4 and p4.IsBot then
		for v=1,#vehicleall do
			cityboteliteexpert = p4.GetActorsByType("cityboteliteexpert")
			for _,Transfer in pairs(cityboteliteexpert) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p4.IsAlliedWith(Spieler) then
						vehicleaction = Spieler.GetActorsByType(vehicleall[v])
						for _,vehicleaction in pairs(vehicleaction) do Transfer.DeliverExperience(vehicleaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p4vehicle()
	end)
end
p5vehicle = function()
	if p5 and p5.IsBot then
		for v=1,#vehicleall do
			cityboteliteexpert = p5.GetActorsByType("cityboteliteexpert")
			for _,Transfer in pairs(cityboteliteexpert) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p5.IsAlliedWith(Spieler) then
						vehicleaction = Spieler.GetActorsByType(vehicleall[v])
						for _,vehicleaction in pairs(vehicleaction) do Transfer.DeliverExperience(vehicleaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p5vehicle()
	end)
end
p6vehicle = function()
	if p6 and p6.IsBot then
		for v=1,#vehicleall do
			cityboteliteexpert = p6.GetActorsByType("cityboteliteexpert")
			for _,Transfer in pairs(cityboteliteexpert) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p6.IsAlliedWith(Spieler) then
						vehicleaction = Spieler.GetActorsByType(vehicleall[v])
						for _,vehicleaction in pairs(vehicleaction) do Transfer.DeliverExperience(vehicleaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p6vehicle()
	end)
end
p7vehicle = function()
	if p7 and p7.IsBot then
		for v=1,#vehicleall do
			cityboteliteexpert = p7.GetActorsByType("cityboteliteexpert")
			for _,Transfer in pairs(cityboteliteexpert) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p7.IsAlliedWith(Spieler) then
						vehicleaction = Spieler.GetActorsByType(vehicleall[v])
						for _,vehicleaction in pairs(vehicleaction) do Transfer.DeliverExperience(vehicleaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p7vehicle()
	end)
end
p8vehicle = function()
	if p8 and p8.IsBot then
		for v=1,#vehicleall do
			cityboteliteexpert = p8.GetActorsByType("cityboteliteexpert")
			for _,Transfer in pairs(cityboteliteexpert) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p8.IsAlliedWith(Spieler) then
						vehicleaction = Spieler.GetActorsByType(vehicleall[v])
						for _,vehicleaction in pairs(vehicleaction) do Transfer.DeliverExperience(vehicleaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p8vehicle()
	end)
end
p9vehicle = function()
	if p9 and p9.IsBot then
		for v=1,#vehicleall do
			cityboteliteexpert = p9.GetActorsByType("cityboteliteexpert")
			for _,Transfer in pairs(cityboteliteexpert) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p9.IsAlliedWith(Spieler) then
						vehicleaction = Spieler.GetActorsByType(vehicleall[v])
						for _,vehicleaction in pairs(vehicleaction) do Transfer.DeliverExperience(vehicleaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p9vehicle()
	end)
end
p10vehicle = function()
	if p10 and p10.IsBot then
		for v=1,#vehicleall do
			cityboteliteexpert = p10.GetActorsByType("cityboteliteexpert")
			for _,Transfer in pairs(cityboteliteexpert) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p10.IsAlliedWith(Spieler) then
						vehicleaction = Spieler.GetActorsByType(vehicleall[v])
						for _,vehicleaction in pairs(vehicleaction) do Transfer.DeliverExperience(vehicleaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p10vehicle()
	end)
end
p11vehicle = function()
	if p11 and p11.IsBot then
		for v=1,#vehicleall do
			cityboteliteexpert = p11.GetActorsByType("cityboteliteexpert")
			for _,Transfer in pairs(cityboteliteexpert) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p11.IsAlliedWith(Spieler) then
						vehicleaction = Spieler.GetActorsByType(vehicleall[v])
						for _,vehicleaction in pairs(vehicleaction) do Transfer.DeliverExperience(vehicleaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p11vehicle()
	end)
end
p12vehicle = function()
	if p12 and p12.IsBot then
		for v=1,#vehicleall do
			cityboteliteexpert = p12.GetActorsByType("cityboteliteexpert")
			for _,Transfer in pairs(cityboteliteexpert) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p12.IsAlliedWith(Spieler) then
						vehicleaction = Spieler.GetActorsByType(vehicleall[v])
						for _,vehicleaction in pairs(vehicleaction) do Transfer.DeliverExperience(vehicleaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p12vehicle()
	end)
end
p13vehicle = function()
	if p13 and p13.IsBot then
		for v=1,#vehicleall do
			cityboteliteexpert = p13.GetActorsByType("cityboteliteexpert")
			for _,Transfer in pairs(cityboteliteexpert) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p13.IsAlliedWith(Spieler) then
						vehicleaction = Spieler.GetActorsByType(vehicleall[v])
						for _,vehicleaction in pairs(vehicleaction) do Transfer.DeliverExperience(vehicleaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p13vehicle()
	end)
end
p14vehicle = function()
	if p14 and p14.IsBot then
		for v=1,#vehicleall do
			cityboteliteexpert = p14.GetActorsByType("cityboteliteexpert")
			for _,Transfer in pairs(cityboteliteexpert) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p14.IsAlliedWith(Spieler) then
						vehicleaction = Spieler.GetActorsByType(vehicleall[v])
						for _,vehicleaction in pairs(vehicleaction) do Transfer.DeliverExperience(vehicleaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p14vehicle()
	end)
end
p15vehicle = function()
	if p15 and p15.IsBot then
		for v=1,#vehicleall do
			cityboteliteexpert = p15.GetActorsByType("cityboteliteexpert")
			for _,Transfer in pairs(cityboteliteexpert) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p15.IsAlliedWith(Spieler) then
						vehicleaction = Spieler.GetActorsByType(vehicleall[v])
						for _,vehicleaction in pairs(vehicleaction) do Transfer.DeliverExperience(vehicleaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p15vehicle()
	end)
end
p16vehicle = function()
	if p16 and p16.IsBot then
		for v=1,#vehicleall do
			cityboteliteexpert = p16.GetActorsByType("cityboteliteexpert")
			for _,Transfer in pairs(cityboteliteexpert) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p16.IsAlliedWith(Spieler) then
						vehicleaction = Spieler.GetActorsByType(vehicleall[v])
						for _,vehicleaction in pairs(vehicleaction) do Transfer.DeliverExperience(vehicleaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p16vehicle()
	end)
end
