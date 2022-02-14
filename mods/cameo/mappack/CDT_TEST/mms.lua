GivePlayerMoney = function()
	Trigger.AfterDelay(1, function()
		moneyMakers = Map.ActorsInBox(Map.TopLeft, Map.BottomRight, function(actor) return actor.Type == "tower.money" end)
		for i, v in ipairs(moneyMakers) do
			Config.player.Cash = Config.player.Cash + 60
			Media.FloatingText("$60", WPos.New(v.CenterPosition.X, v.CenterPosition.Y, v.CenterPosition.Z), 30, HSLColor.Green)
		end
	end)
end
