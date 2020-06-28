
p1infantry = function()
	if p1 and p1.IsBot then
		for s=1,#infantryall do
			cityboteliteinstructor = p1.GetActorsByType("cityboteliteinstructor")
			for _,Transfer in pairs(cityboteliteinstructor) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p1.IsAlliedWith(Spieler) then
						infantryaction = Spieler.GetActorsByType(infantryall[s])
						for _,infantryaction in pairs(infantryaction) do Transfer.DeliverExperience(infantryaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p1infantry()
	end)
end
p2infantry = function()
	if p2 and p2.IsBot then
		for s=1,#infantryall do
			cityboteliteinstructor = p2.GetActorsByType("cityboteliteinstructor")
			for _,Transfer in pairs(cityboteliteinstructor) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p2.IsAlliedWith(Spieler) then
						infantryaction = Spieler.GetActorsByType(infantryall[s])
						for _,infantryaction in pairs(infantryaction) do Transfer.DeliverExperience(infantryaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p2infantry()
	end)
end
p3infantry = function()
	if p3 and p3.IsBot then
		for s=1,#infantryall do
			cityboteliteinstructor = p3.GetActorsByType("cityboteliteinstructor")
			for _,Transfer in pairs(cityboteliteinstructor) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p3.IsAlliedWith(Spieler) then
						infantryaction = Spieler.GetActorsByType(infantryall[s])
						for _,infantryaction in pairs(infantryaction) do Transfer.DeliverExperience(infantryaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p3infantry()
	end)
end
p4infantry = function()
	if p4 and p4.IsBot then
		for s=1,#infantryall do
			cityboteliteinstructor = p4.GetActorsByType("cityboteliteinstructor")
			for _,Transfer in pairs(cityboteliteinstructor) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p4.IsAlliedWith(Spieler) then
						infantryaction = Spieler.GetActorsByType(infantryall[s])
						for _,infantryaction in pairs(infantryaction) do Transfer.DeliverExperience(infantryaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p4infantry()
	end)
end
p5infantry = function()
	if p5 and p5.IsBot then
		for s=1,#infantryall do
			cityboteliteinstructor = p5.GetActorsByType("cityboteliteinstructor")
			for _,Transfer in pairs(cityboteliteinstructor) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p5.IsAlliedWith(Spieler) then
						infantryaction = Spieler.GetActorsByType(infantryall[s])
						for _,infantryaction in pairs(infantryaction) do Transfer.DeliverExperience(infantryaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p5infantry()
	end)
end
p6infantry = function()
	if p6 and p6.IsBot then
		for s=1,#infantryall do
			cityboteliteinstructor = p6.GetActorsByType("cityboteliteinstructor")
			for _,Transfer in pairs(cityboteliteinstructor) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p6.IsAlliedWith(Spieler) then
						infantryaction = Spieler.GetActorsByType(infantryall[s])
						for _,infantryaction in pairs(infantryaction) do Transfer.DeliverExperience(infantryaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p6infantry()
	end)
end
p7infantry = function()
	if p7 and p7.IsBot then
		for s=1,#infantryall do
			cityboteliteinstructor = p7.GetActorsByType("cityboteliteinstructor")
			for _,Transfer in pairs(cityboteliteinstructor) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p7.IsAlliedWith(Spieler) then
						infantryaction = Spieler.GetActorsByType(infantryall[s])
						for _,infantryaction in pairs(infantryaction) do Transfer.DeliverExperience(infantryaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p7infantry()
	end)
end
p8infantry = function()
	if p8 and p8.IsBot then
		for s=1,#infantryall do
			cityboteliteinstructor = p8.GetActorsByType("cityboteliteinstructor")
			for _,Transfer in pairs(cityboteliteinstructor) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p8.IsAlliedWith(Spieler) then
						infantryaction = Spieler.GetActorsByType(infantryall[s])
						for _,infantryaction in pairs(infantryaction) do Transfer.DeliverExperience(infantryaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p8infantry()
	end)
end
p9infantry = function()
	if p9 and p9.IsBot then
		for s=1,#infantryall do
			cityboteliteinstructor = p9.GetActorsByType("cityboteliteinstructor")
			for _,Transfer in pairs(cityboteliteinstructor) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p9.IsAlliedWith(Spieler) then
						infantryaction = Spieler.GetActorsByType(infantryall[s])
						for _,infantryaction in pairs(infantryaction) do Transfer.DeliverExperience(infantryaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p9infantry()
	end)
end
p10infantry = function()
	if p10 and p10.IsBot then
		for s=1,#infantryall do
			cityboteliteinstructor = p10.GetActorsByType("cityboteliteinstructor")
			for _,Transfer in pairs(cityboteliteinstructor) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p10.IsAlliedWith(Spieler) then
						infantryaction = Spieler.GetActorsByType(infantryall[s])
						for _,infantryaction in pairs(infantryaction) do Transfer.DeliverExperience(infantryaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p10infantry()
	end)
end
p11infantry = function()
	if p11 and p11.IsBot then
		for s=1,#infantryall do
			cityboteliteinstructor = p11.GetActorsByType("cityboteliteinstructor")
			for _,Transfer in pairs(cityboteliteinstructor) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p11.IsAlliedWith(Spieler) then
						infantryaction = Spieler.GetActorsByType(infantryall[s])
						for _,infantryaction in pairs(infantryaction) do Transfer.DeliverExperience(infantryaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p11infantry()
	end)
end
p12infantry = function()
	if p12 and p12.IsBot then
		for s=1,#infantryall do
			cityboteliteinstructor = p12.GetActorsByType("cityboteliteinstructor")
			for _,Transfer in pairs(cityboteliteinstructor) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p12.IsAlliedWith(Spieler) then
						infantryaction = Spieler.GetActorsByType(infantryall[s])
						for _,infantryaction in pairs(infantryaction) do Transfer.DeliverExperience(infantryaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p12infantry()
	end)
end
p13infantry = function()
	if p13 and p13.IsBot then
		for s=1,#infantryall do
			cityboteliteinstructor = p13.GetActorsByType("cityboteliteinstructor")
			for _,Transfer in pairs(cityboteliteinstructor) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p13.IsAlliedWith(Spieler) then
						infantryaction = Spieler.GetActorsByType(infantryall[s])
						for _,infantryaction in pairs(infantryaction) do Transfer.DeliverExperience(infantryaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p13infantry()
	end)
end
p14infantry = function()
	if p14 and p14.IsBot then
		for s=1,#infantryall do
			cityboteliteinstructor = p14.GetActorsByType("cityboteliteinstructor")
			for _,Transfer in pairs(cityboteliteinstructor) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p14.IsAlliedWith(Spieler) then
						infantryaction = Spieler.GetActorsByType(infantryall[s])
						for _,infantryaction in pairs(infantryaction) do Transfer.DeliverExperience(infantryaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p14infantry()
	end)
end
p15infantry = function()
	if p15 and p15.IsBot then
		for s=1,#infantryall do
			cityboteliteinstructor = p15.GetActorsByType("cityboteliteinstructor")
			for _,Transfer in pairs(cityboteliteinstructor) do
				for i=0,15 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p15.IsAlliedWith(Spieler) then
						infantryaction = Spieler.GetActorsByType(infantryall[s])
						for _,infantryaction in pairs(infantryaction) do Transfer.DeliverExperience(infantryaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p15infantry()
	end)
end
p16infantry = function()
	if p16 and p16.IsBot then
		for s=1,#infantryall do
			cityboteliteinstructor = p16.GetActorsByType("cityboteliteinstructor")
			for _,Transfer in pairs(cityboteliteinstructor) do
				for i=15,0,-1 do
					local Spieler = Player.GetPlayer("Multi" .. tostring(i))
					if Spieler and p16.IsAlliedWith(Spieler) then
						infantryaction = Spieler.GetActorsByType(infantryall[s])
						for _,infantryaction in pairs(infantryaction) do Transfer.DeliverExperience(infantryaction) end
					end
				end
			end
		end
	end
	Trigger.AfterDelay(DateTime.Seconds(Utils.RandomInteger(1, 10)), function()
		p16infantry()
	end)
end
