WorldLoaded = function()
	Trigger.AfterDelay(DateTime.Seconds(3), function()
		Utils.Do(Map.ActorsInWorld, function(actor)
			if actor.HasProperty("GrantCondition") then
				actor.GrantCondition("speedboost", DateTime.Seconds(30))
			end
		end)
	end)
end
