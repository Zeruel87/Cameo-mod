-------------------------------------------------------------------------------
-- DEPENDENCIES                                                              --
--                                                                           --
-- This project makes use of my own data structures utility library (MDSU).  --
-- This makes a lot of the code below much, much more compact and easier to  --
-- read (if you are somewhat familiar with functional-programming-based data --
-- structure interfaces & functions). Just make sure you have `mdsu.lua`     --
-- included in your own project before using this!                           --
-------------------------------------------------------------------------------

assert(MDSU, "MDSU has not been included, or the order of lua sources is incorrect")


local Dict = MDSU.Dict
local List = MDSU.List
local Set = MDSU.Set
local Tuple = MDSU.Tuple



-------------------------------------------------------------------------------
-- VARIABLES                                                                 --
--                                                                           --
-- The variables below are used for tracking the state of MTD. They should   --
-- not be set directly by map makers. If you find that you need to set one   --
-- directly to achieve desired behaviour, let me know and I'll look into     --
-- extending the external interface to satisfy your needs.                   --
-------------------------------------------------------------------------------

-- Tower Defence Core Module
MTD = {}


-- Mode State Variables
MTD.Mode = {}
MTD.Mode.NONE = 'none'
MTD.Mode.WAVE = 'wave'
MTD.Mode.BUILD = 'build'
MTD.Mode.mode = MTD.Mode.NONE
MTD.Mode.predicate = nil
MTD.Mode.OnEnterBuildMode = function() end
MTD.Mode.OnExitBuildMode = function() end
MTD.Mode.OnEnterWaveMode = function() end
MTD.Mode.OnExitWaveMode = function() end


-- Map State Variables
MTD.Map = {}
MTD.Map.path = nil
MTD.Map.border = nil
MTD.Map.spawns = nil
MTD.Map.targets = nil


-- Build State Variables
MTD.Build = {}
MTD.Build.producer = nil


-- Wave State Variables
MTD.Wave = {}
MTD.Wave.count = 1
MTD.Wave.initDelay = 5
MTD.Wave.spawnDelay = 20
MTD.Wave.spawnQueues = Dict.New()
MTD.Wave.next = List.New()
MTD.Wave.actors = List.New()

-- Default OnEnemySpawn callback randomizes spawns and targets
MTD.Wave.OnEnemySpawn = function(arg0, arg1, arg2)
  local spawnIdx = Utils.RandomInteger(0, MTD.Map.spawns.Size())
  local spawn = MTD.Map.spawns.Get(spawnIdx)
  local targetIdx = Utils.RandomInteger(0, MTD.Map.targets.Size())
  local target = MTD.Map.targets.Get(targetIdx)
  return spawn, target
end


-- Player State Variables
MTD.Player = {}
MTD.Player.player = nil
MTD.Player.objectiveID = nil
MTD.Player.lives = 10
MTD.Player.enemy = nil



-------------------------------------------------------------------------------
-- EXTERNAL INTERFACE                                                        --
--                                                                           --
-- If you are a map maker, the functions below are the only ones you should  --
-- be calling! If the interface provided isn't enough, let me know and I'll  --
-- look into extending it. If you are in a rush, do what you want but let me --
-- know what you would have liked to be here!                                --
-------------------------------------------------------------------------------

-- Used to set the user's player
MTD.SetPlayer = function(player)
  MTD.Player.player = player
end


-- Used to set the player used for enemy actors
MTD.SetEnemy = function(enemy)
  MTD.Player.enemy = enemy
end


-- Used to set the function called for the next wave
-- The function should take a single integer (the wave count)
MTD.SetWaveGen = function(gen)
  assert(gen ~= nil, "[MTD] Wave generation function must not be nil")
  MTD.Wave.generator = gen
end


-- Used to set the function called to select a spawn for a given actor
-- The function should take 3 parameters: the wave count, the order of the
-- actor, and the actor. The function should return 2 values: a spawn, and a
-- target
MTD.SetOnEnemySpawn = function(callback)
  assert(gen ~= nil, "[MTD] OnEnemySpawn callback may not be nil")
  MTD.Wave.OnEnemySpawn = callback
end


-- Used to set the function called just before entering build mode
-- The function should not take any parameters
MTD.SetOnEnterBuildMode = function(callback)
  assert(callback ~= nil, "[MTD] OnEnterBuildMode callback may not be nil")
  MTD.Mode.OnEnterBuildMode = callback
end


-- Used to set the function called just after exiting build mode
-- The function should not take any parameters
MTD.SetOnExitBuildMode = function(callback)
  assert(callbak ~= nil, "[MTD] OnExitBuildMode callback may not be nil")
  MTD.Mode.OnExitBuildMode = callback
end


-- Used to set the function called just before entering wave mode
-- The function should take a single integer (the wave count)
MTD.SetOnEnterWaveMode = function(callback)
  assert(callback ~= nil, "[MTD] OnEnterWaveMode callback may not be nil")
  MTD.Mode.OnEnterWaveMode = callback
end


-- Used to set the function called just after exiting wave mode
-- The function should take a single integer (the wave count)
MTD.SetOnExitWaveMode = function(callback)
  assert(callback ~= nil, "[MTD] OnExitWaveMode callback may not be nil")
  MTD.Mode.OnExitWaveMode = callback
end


-- Used to set the cash of the player
MTD.SetCash = function(cash)
  assert(cash >= 0, "[MTD] Set cash must be non-negative")
  assert(MTD.Player.player ~= nil, "[MTD] Player must be set using MTD.SetPlayer")
  MTD.Player.player.Cash = cash
end


-- Used to add cash to the player
MTD.GiveCash = function(cash)
  assert(cash >= 0, "[MTD] Given cash must be non-negative")
  assert(MTD.Player.player ~= nil, "[MTD] Player must be set using MTD.SetPlayer")
  MTD.Player.player.Cash = MTD.Player.player.Cash + cash
end


-- Used to take cash from the player
MTD.TakeCash = function(cash)
  assert(cash >= 0, "[MTD] Taken cash must be non-negative")
  assert(MTD.Player.player ~= nil, "[MTD] Player must be set using MTD.SetPlayer")
  MTD.Player.player.Cash = MTD.Player.player.Cash - cash
end


-- Used to set the lives of the player
MTD.SetLives = function(lives)
  assert(lives >= 0, "[MTD] Set lives must be non-negative")
  MTD.Player.lives = lives
  if MTD.initFlag then
    MTD.UpdateBanner()
    if lives <= 0 then
      MTD.Lose()
    end
  end
end


-- Used to give lives to the player
MTD.GiveLives = function(lives)
  assert(lives >= 0, "[MTD] Given lives must be non-negative")
  MTD.Player.lives = MTD.Player.lives + lives
  if MTD.initFlag then
    MTD.UpdateBanner()
  end
end


-- Used to take lives from the player
MTD.GiveLives = function(lives)
  assert(lives >= 0, "[MTD] Taken lives must be non-negative")
  MTD.Player.lives = MTD.Player.lives - lives
  if MTD.initFlag then
    MTD.UpdateBanner()
    if lives <= 0 then
      MTD.Lose()
    end
  end
end


-- Used to set the delay before the first unit of a wave is spawned
MTD.SetInitialSpawnDelay = function(delay)
  assert(delay >= 0, "[MTD] Initial spawn delay must be non-negative")
  MTD.Wave.initDelay = delay
end


-- Used to set the delay between spawning units of a wave
MTD.SetInitialSpawnDelay = function(delay)
  assert(delay >= 0, "[MTD] Spawn delay must be non-negative")
  MTD.Wave.spawnDelay = delay
end


-- Begin function, call to begin an MTD game
MTD.Begin = function()

  -- Do not initialised if already initialised
  if MTD.beginFlag then
    assert(false, "[MTD] Begin called twice")
  end

  -- Ensure required settings are set
  assert(MTD.Player.player ~= nil, "[MTD] Player must be set using MTD.SetPlayer")
  assert(MTD.Player.enemy ~= nil, "[MTD] Enemy must be set using MTD.SetEnemy")
  assert(MTD.Wave.generator ~= nil, "[MTD] Wave generation function must be set using MTD.SetWaveGen")

  -- Set player objective
  MTD.Player.objectiveID = MTD.Player.player.AddObjective("Survive")

  -- Get all path tiles
  MTD.Map.path = Set.New(MDSU.GetActors(function(a)
    return a.Type == "path"
  end))

  -- Get all border tiles
  MTD.Map.border = Set.New(MDSU.GetActors(function(a)
    return a.Type == "border"
  end))

  -- Get all spawns
  MTD.Map.spawns = List.New(MDSU.GetActors(function(a)
    return a.Type == "spawn"
  end))

  -- Get all targets
  MTD.Map.targets = List.New(MDSU.GetActors(function(a)
    return a.Type == "target"
  end))

  -- Set up triggers for targets
  MTD.Map.targets.ForEach(function(a)
    Trigger.OnPassengerEntered(a, function(_, a)
      MTD.Wave.actors = MTD.Wave.actors.FilterNot(function(v) return v == a end)
      MTD.LoseLives(1)
      a.Destroy()
      MTD.UpdateBanner()
    end)
  end)

  -- Set flag as initialised
  MTD.beginFlag = true

  -- Enter build mode
  MTD.EnterBuildMode()
end



-------------------------------------------------------------------------------
-- INTERNAL INTERFACE                                                        --
--                                                                           --
-- If you are a map maker you shouldn't need to touch this. If you do, let   --
-- me know and I'll look into extending the external interface to allow for  --
-- whatever you needed to do.                                                --
-------------------------------------------------------------------------------

-- Toggles the current mode of MTD and calls the appropriate callbacks
MTD.ToggleMode = function()
  if MTD.Mode.mode == MTD.Mode.BUILD then
    MTD.ExitBuildMode()
    MTD.EnterWaveMode()
  elseif MTD.Mode.mode == MTD.Mode.WAVE then
    MTD.ExitWaveMode()
    MTD.EnterBuildMode()
  elseif MTD.Mode.mode == MTD.Mode.NONE then
    error("[MTD] Cannot toggle from none mode")
  else
    error("[MTD] Cannot toggle from invalid mode")
  end
end


-- Enters build mode, calling the appropriate callback
MTD.EnterBuildMode = function()

  -- Set mode to build mode
  MTD.Mode.mode = MTD.Mode.BUILD

  -- Bring all border actors out of the world
  MTD.Map.border.ForEach(function(a) if a.IsInWorld then a.IsInWorld = false end end)
  
  -- Bring all path actors into the world
  MTD.Map.path.ForEach(function(a) if not a.IsInWorld then a.IsInWorld = true end end)

  -- Create a `producer` actor, allowing the player to produce defences
  MTD.Build.producer = Actor.Create("producer", true, {Owner = MTD.Player.player, Location = CPos.New(1, 1)})

  -- When a `mode.wave` actor is produced, then we destroy the `producer`
  -- actor, the `mode.wave` actor, and toggle to wave mode
  Trigger.OnProduction(MTD.Build.producer, function(_0, produced)
    if produced.Type == "mode.wave" then
      MTD.Build.producer.Destroy()
      MTD.Build.producer = nil
      produced.Destroy()
      MTD.ToggleMode()
    end
  end)

  -- Get list of next wave actors
  MTD.Wave.next = List.New(MTD.Wave.generator(MTD.Wave.count))

  -- If there are no next actors, then end the game with a win
  if MTD.Wave.next.IsEmpty() then
    MTD.Win()
    return
  end

  -- Update the banner
  MTD.UpdateBanner()

  -- Call callback
  MTD.Mode.OnEnterBuildMode()
end


-- Exits build mode, calling the appropriate callback
MTD.ExitBuildMode = function()

  -- Destroy the build mode `producer` actor, if we haven't already
  if MTD.Build.producer ~= nil then
    MTD.Build.producer.Destroy()
    MTD.Build.producer = nil
  end

  -- Switch the mode to the none mode
  MTD.Mode.mode = MTD.Mode.NONE

  -- Call callback
  MTD.Mode.OnExitBuildMode()
end


-- Enters wave mode, calling the appropriate callback
MTD.EnterWaveMode = function()

  local count = MTD.Wave.count

  -- Set mode to wave mode
  MTD.Mode.mode = MTD.Mode.WAVE

  -- Bring all border actors into world
  MTD.Map.border.ForEach(function(a) if not a.IsInWorld then a.IsInWorld = true end end)

  -- Bring all path actors out of the world
  MTD.Map.path.ForEach(function(a) if a.IsInWorld then a.IsInWorld = false end end)

  -- Fill spawn queues
  local delta = MTD.Wave.initDelay
  for i, v in MTD.Wave.next.Iterator() do
    
    -- Get spawn-target pair
    local spawn, target = MTD.Wave.OnEnemySpawn(MTD.Wave.count, i, v)

    -- Create entry for spawn queue
    local entry = Tuple.New(v, target)
    
    -- Get spawn queue
    local queue = MTD.Wave.spawnQueues.GetOrElse(spawn, List.New()).Appended(entry)

    -- Update spawn queue
    MTD.Wave.spawnQueues = MTD.Wave.spawnQueues.Updated(spawn, queue)
  end

  local spawnTick
  spawnTick = function()
    if count ~= MTD.Wave.count then
      return
    end
    for spawn, queue in MTD.Wave.spawnQueues.Iterator() do
      if queue.NonEmpty() then
        
        -- Pop first element
        local str, target = queue.Head().Unpack()
        MTD.Wave.spawnQueues = MTD.Wave.spawnQueues.Updated(spawn, queue.Drop(1))
        
        -- Create actor with corresponding internal id
        local actor = Actor.Create(str, true, {Owner = MTD.Player.enemy, Location = spawn.Location})

        -- Add to enemy actors list
        MTD.Wave.actors = MTD.Wave.actors.Appended(actor)

        -- When idle, the actor moves towards it's target transport
        Trigger.OnIdle(actor, function(_0)
          actor.EnterTransport(target)
        end)

        -- When killed, update the list of actors, and the banner
        Trigger.OnKilled(actor, function(_0, _1)
          MTD.Wave.actors = MTD.Wave.actors.FilterNot(function(a) return a == actor end)
          MTD.UpdateBanner()
          if MTD.Wave.actors.IsEmpty() and MTD.Wave.spawnQueues.ForAll(function(k, v) return v.IsEmpty() and MTD.Mode.mode == MTD.Mode.WAVE end) then
            MTD.ToggleMode()
          end
        end)

        -- Update the banner
        MTD.UpdateBanner()
      end
    end
    Trigger.AfterDelay(MTD.Wave.spawnDelay, spawnTick)
  end
  
  Trigger.AfterDelay(MTD.Wave.initDelay, spawnTick)
  
  -- Empty list of next enemy actors
  MTD.Wave.next = List.New()

  -- Update banner
  MTD.UpdateBanner()

  -- Call callback
  MTD.Mode.OnEnterWaveMode(MTD.Wave.count)
end


-- Exits wave mode, calling the appropriate callback
MTD.ExitWaveMode = function()

  -- Destroy remaining enemy actors
  MTD.Wave.actors.ForEach(function(a)
    a.Destroy()
  end)
  MTD.Wave.actors = List.New()

  -- Empty spawn queues and cancel triggers
  MTD.Wave.spawnQueues = Dict.New()

  -- Update banner
  MTD.UpdateBanner()

  -- Update internal mode value
  MTD.Mode.mode = MTD.Mode.NONE

  -- Call callback
  MTD.Mode.OnExitWaveMode(MTD.Wave.count)
  
  -- Increment wave count
  MTD.Wave.count = MTD.Wave.count + 1
end


-- Removes the given number of lives from the player
MTD.LoseLives = function(n)

  -- Subtract lives
  MTD.Player.lives = MTD.Player.lives - n

  -- If no lives remain, lose
  if MTD.Player.lives <= 0 then
    MTD.Lose()

  -- Otherwise, if no enemies remain, then toggle the mode
  elseif MTD.Wave.actors.IsEmpty() and MTD.Wave.spawnQueues.ForAll(function(k, v) return v.IsEmpty() end) and MTD.Mode.mode == MTD.Mode.WAVE then
    MTD.ToggleMode()
  end
end


-- Updates the banner to display relevant information about the current state
-- of the game
MTD.UpdateBanner = function()

  -- Display appropriate information for build mode
  if MTD.Mode.mode == MTD.Mode.BUILD then
    UserInterface.SetMissionText(MTD.Player.player.Name .. " | Build Mode | Lives: " .. MTD.Player.lives .. " | Next Wave: " .. (MTD.Wave.next.Size()) .. " Units")
  
  -- Display appropriate information for wave mode
  elseif MTD.Mode.mode == MTD.Mode.WAVE then
    local remaining = MTD.Wave.actors.Size() + List.New(MTD.Wave.spawnQueues.Values()).Map(function(l) return l.Size() end).Sum()
    UserInterface.SetMissionText(MTD.Player.player.Name .. " | Wave Mode | Lives: " .. MTD.Player.lives .. " | Remaining: " .. remaining .. " Units")

  -- Error out if the NONE mode is set
  elseif MTD.Mode.mode == MTD.Mode.NONE then
    error("[MTD] Mode set to NONE when banner updated")
  
  -- Error out if the mode is set to anything else
  else
    error("[MTD] No mode set when banner updated")
  end
end


-- Causes the player to win the game, called when no waves remain
MTD.Win = function()
  MTD.Player.player.MarkCompletedObjective(MTD.Player.objectiveID)
end


-- Causes the player to lose the game, called when no lives remain
MTD.Lose = function()
  MTD.Player.player.MarkFailedObjective(MTD.Player.objectiveID)
end
