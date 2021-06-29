WorldLoaded = function()
    LLL = Player.GetPlayer("Creeps")
end
arr = LLL.GetActors()
for _, act in ipairs(arr) do
        if not act.IsDead then
            act.Destroy()
        end
    end