
p1building = function()
	if p1 and p1.IsBot then
		for p=1,#powerall do
			citybotelitearchitect = p1.GetActorsByType("citybotelitearchitect")
			for _,Transfer in pairs(citybotelitearchitect) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p1.IsAlliedWith(Spieler) then
						poweraction = Spieler.GetActorsByType(powerall[p])
						for _,poweraction in pairs(poweraction) do Transfer.DeliverExperience(poweraction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p1building()
	end)
end
p2building = function()
	if p2 and p2.IsBot then
		for p=1,#powerall do
			citybotelitearchitect = p2.GetActorsByType("citybotelitearchitect")
			for _,Transfer in pairs(citybotelitearchitect) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p2.IsAlliedWith(Spieler) then
						poweraction = Spieler.GetActorsByType(powerall[p])
						for _,poweraction in pairs(poweraction) do Transfer.DeliverExperience(poweraction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p2building()
	end)
end
p3building = function()
	if p3 and p3.IsBot then
		for p=1,#powerall do
			citybotelitearchitect = p3.GetActorsByType("citybotelitearchitect")
			for _,Transfer in pairs(citybotelitearchitect) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p3.IsAlliedWith(Spieler) then
						poweraction = Spieler.GetActorsByType(powerall[p])
						for _,poweraction in pairs(poweraction) do Transfer.DeliverExperience(poweraction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p3building()
	end)
end
p4building = function()
	if p4 and p4.IsBot then
		for p=1,#powerall do
			citybotelitearchitect = p4.GetActorsByType("citybotelitearchitect")
			for _,Transfer in pairs(citybotelitearchitect) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p4.IsAlliedWith(Spieler) then
						poweraction = Spieler.GetActorsByType(powerall[p])
						for _,poweraction in pairs(poweraction) do Transfer.DeliverExperience(poweraction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p4building()
	end)
end
p5building = function()
	if p5 and p5.IsBot then
		for p=1,#powerall do
			citybotelitearchitect = p5.GetActorsByType("citybotelitearchitect")
			for _,Transfer in pairs(citybotelitearchitect) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p5.IsAlliedWith(Spieler) then
						poweraction = Spieler.GetActorsByType(powerall[p])
						for _,poweraction in pairs(poweraction) do Transfer.DeliverExperience(poweraction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p5building()
	end)
end
p6building = function()
	if p6 and p6.IsBot then
		for p=1,#powerall do
			citybotelitearchitect = p6.GetActorsByType("citybotelitearchitect")
			for _,Transfer in pairs(citybotelitearchitect) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p6.IsAlliedWith(Spieler) then
						poweraction = Spieler.GetActorsByType(powerall[p])
						for _,poweraction in pairs(poweraction) do Transfer.DeliverExperience(poweraction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p6building()
	end)
end
p7building = function()
	if p7 and p7.IsBot then
		for p=1,#powerall do
			citybotelitearchitect = p7.GetActorsByType("citybotelitearchitect")
			for _,Transfer in pairs(citybotelitearchitect) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p7.IsAlliedWith(Spieler) then
						poweraction = Spieler.GetActorsByType(powerall[p])
						for _,poweraction in pairs(poweraction) do Transfer.DeliverExperience(poweraction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p7building()
	end)
end
p8building = function()
	if p8 and p8.IsBot then
		for p=1,#powerall do
			citybotelitearchitect = p8.GetActorsByType("citybotelitearchitect")
			for _,Transfer in pairs(citybotelitearchitect) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p8.IsAlliedWith(Spieler) then
						poweraction = Spieler.GetActorsByType(powerall[p])
						for _,poweraction in pairs(poweraction) do Transfer.DeliverExperience(poweraction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p8building()
	end)
end
p9building = function()
	if p9 and p9.IsBot then
		for p=1,#powerall do
			citybotelitearchitect = p9.GetActorsByType("citybotelitearchitect")
			for _,Transfer in pairs(citybotelitearchitect) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p9.IsAlliedWith(Spieler) then
						poweraction = Spieler.GetActorsByType(powerall[p])
						for _,poweraction in pairs(poweraction) do Transfer.DeliverExperience(poweraction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p9building()
	end)
end
p10building = function()
	if p10 and p10.IsBot then
		for p=1,#powerall do
			citybotelitearchitect = p10.GetActorsByType("citybotelitearchitect")
			for _,Transfer in pairs(citybotelitearchitect) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p10.IsAlliedWith(Spieler) then
						poweraction = Spieler.GetActorsByType(powerall[p])
						for _,poweraction in pairs(poweraction) do Transfer.DeliverExperience(poweraction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p10building()
	end)
end
p11building = function()
	if p11 and p11.IsBot then
		for p=1,#powerall do
			citybotelitearchitect = p11.GetActorsByType("citybotelitearchitect")
			for _,Transfer in pairs(citybotelitearchitect) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p11.IsAlliedWith(Spieler) then
						poweraction = Spieler.GetActorsByType(powerall[p])
						for _,poweraction in pairs(poweraction) do Transfer.DeliverExperience(poweraction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p11building()
	end)
end
p12building = function()
	if p12 and p12.IsBot then
		for p=1,#powerall do
			citybotelitearchitect = p12.GetActorsByType("citybotelitearchitect")
			for _,Transfer in pairs(citybotelitearchitect) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p12.IsAlliedWith(Spieler) then
						poweraction = Spieler.GetActorsByType(powerall[p])
						for _,poweraction in pairs(poweraction) do Transfer.DeliverExperience(poweraction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p12building()
	end)
end
p13building = function()
	if p13 and p13.IsBot then
		for p=1,#powerall do
			citybotelitearchitect = p13.GetActorsByType("citybotelitearchitect")
			for _,Transfer in pairs(citybotelitearchitect) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p13.IsAlliedWith(Spieler) then
						poweraction = Spieler.GetActorsByType(powerall[p])
						for _,poweraction in pairs(poweraction) do Transfer.DeliverExperience(poweraction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p13building()
	end)
end
p14building = function()
	if p14 and p14.IsBot then
		for p=1,#powerall do
			citybotelitearchitect = p14.GetActorsByType("citybotelitearchitect")
			for _,Transfer in pairs(citybotelitearchitect) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p14.IsAlliedWith(Spieler) then
						poweraction = Spieler.GetActorsByType(powerall[p])
						for _,poweraction in pairs(poweraction) do Transfer.DeliverExperience(poweraction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p14building()
	end)
end
p15building = function()
	if p15 and p15.IsBot then
		for p=1,#powerall do
			citybotelitearchitect = p15.GetActorsByType("citybotelitearchitect")
			for _,Transfer in pairs(citybotelitearchitect) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p15.IsAlliedWith(Spieler) then
						poweraction = Spieler.GetActorsByType(powerall[p])
						for _,poweraction in pairs(poweraction) do Transfer.DeliverExperience(poweraction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p15building()
	end)
end
p16building = function()
	if p16 and p16.IsBot then
		for p=1,#powerall do
			citybotelitearchitect = p16.GetActorsByType("citybotelitearchitect")
			for _,Transfer in pairs(citybotelitearchitect) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p16.IsAlliedWith(Spieler) then
						poweraction = Spieler.GetActorsByType(powerall[p])
						for _,poweraction in pairs(poweraction) do Transfer.DeliverExperience(poweraction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p16building()
	end)
end
