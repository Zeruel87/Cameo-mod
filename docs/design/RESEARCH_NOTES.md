# Research notes

Source-game and mod research that informs design but binds nothing. Five separate files until
2026-08-23; each is small, none is a queue, and none had a reason to be alone.

**Nothing here is authoritative.** Binding rules are in [`../DESIGN.md`](../DESIGN.md); the work
queue is [`ROADMAP.md`](ROADMAP.md). Findings get promoted OUT of this file when they become
rules — if a section here contradicts DESIGN.md, DESIGN.md wins.

---

## Tiberian Sun authenticity — Shattered Paradise

_Merged 2026-08-23 from `docs/design/shattered_paradise_research.md`, unedited below this line._

_Research 2026-07-11 against the local SDK checkout
(Shattered-Paradise-SDK-bleed, bleed).
SP is the reference-quality OpenRA TS total conversion. License: code
GPLv3 (traits are portable into our GPL assemblies with attribution).
**ASSET LAW (design 2026-07-11): take NO art or sound from SP** — no
icons, no sprites, no audio that doesn't exist in base Tiberian Sun.
Use only TS assets Cameo already has, or create new ones. Effects are
to be REBUILT to look almost the same (contrail colors, palettes,
beam settings are yaml parameters, not assets — freely reusable as
recipes; the sprite images they reference are not). Goal: heavy SP
inspiration for ALL TS factions — CABAL first, then GDI, Nod,
Forgotten, and eventually the upcoming Scrin. tjk-ws has already
started mining the code side: `TakeOffOnMake.cs` in OpenRA.Mods.Cameo
is SP's trait verbatim._

### 1. Layout differences vs Cameo

SP is a single-mod build: one `mods/sp` with per-faction WEAPON files
(`cabweapons.yaml`, `gdiweapons.yaml`, `nodweapons.yaml`,
`mutweapons.yaml`, `scrweapons.yaml`) but SHARED rules files
(infantry/vehicles/structures for all factions together), faction
ownership expressed through prerequisites (`~cabclaw`, `~cabweap`) and
`GrantConditionOnFaction@CAB`. Five factions: GDI, Nod, CABAL (`cab`),
Mutants (`mut`), Scrin (`scr`). Tech depth: `techlevel.1–6` lobby
options + per-faction tech tokens (`hasTech.cabT2/cabT3`) — a
double-gate similar to our tier system. Our ContentPack split is
strictly better for the dynamic-loading goal; SP's per-faction weapon
files confirm that direction.

### 2. SP CABAL — full roster (for our CABAL rebuild)

Buildings: Power → **Claw** (barracks) → War Factory (TL2) → Radar
(TL4) → Tech (TL5); defenses: **Drone Pit** (launches mini bomber
drones at targets, TL1), **Blaster Turret** (arcing green-plasma
artillery defense, Burst 5, MinRange), **Railgun Turret** (AA, cyan
railgun), **Eye of C.A.B.A.L.** (detection), **Nanomachine Core**
(support superweapon), **Iron Savior** (Scrin-tech energy cannon SW),
**C.A.B.A.L. Defender** (ultimate multi-weapon fortress: 2 lasers +
plasma cannon burst 8 + range-18 plasma artillery with FireRadius
shrapnel ring).

Units: Swarmling (T1 support inf), Gladiator (resilient cyborg,
4-burst 120mm), Abductor (ambusher drone), Cyborg Commando (plasma
cannon), Centurion (chaingun walker), **Cyborg Reaper** (missiles +
web launcher), Mobile Repair Vehicle, Hover Transport, **Drone Host**
(range-18 artillery whose shells spawn linked sentry drones at the
impact — `FireFragment` + `FireShrapnel` + `SpawnActor` warhead chain),
Minotaur (twin-laser walker), Wasp (railgun drone — same name as ours),
Basilisk (firestorm-rocket frigate), Devourer (siege frigate with a
melee **grinder** that applies `Slowdown50pp` on hit).

Faction economy mechanic — **nanomachine reanimation**: every organic
carries `SpawnCorpseOnDeath` (a reusable "corpse" token); the
Nanomachine Core power drops a field whose `SpawnActorsOnCorpseInRadius`
consumes corpses in 7c0 and reanimates them as `nanos` swarm actors for
CABAL. Strong candidate for our CABAL pillbox "assimilation" option or
a T4 support power.

Upgrade suite (all radar/tech-gated, cost 500–2500): Cybernetic Leg
Enhancements, Improved Reaper Nets, Limpet AA Targeting, Reclaim &
Recycle, Regenerative Materials, Gatling Cannons. Upgraded weapons are
`<Weapon>Upg` twins that differ ONLY in `DamageTypes` (`CabalDeath` →
`CabalDeathUpg`) — the upgrade effects hang off death types, keeping
weapon stats identical. Elegant pattern for our upgrade twins.

### 3. Exact effect recipes our design orders asked for

**Green plasma ball** (ordered for Commando/Mk2/new CABAL turret) —
SP's Cyborg Commando `CyCannon`:
```
Projectile: MissileTA            # we HAVE MissileTA (Mods.AS)
	Palette: jascgreen
	Image: greenplasma2          # SP asset — do NOT copy; recreate ours
	ContrailLength: 32
	ContrailStartColor: 0CD95740 (alpha 64) → ContrailEndColor: 0CD95710 (alpha 16)
	ContrailStartWidth: 0c172
Report: scrin5b.aud
Inherits@2: ^GreenPlasmaExplosion:
	CreateEffect: Explosions: plasmaballexplosion, ImpactSounds: expnew12.aud,
	ExplosionPalette: gensmkexploFgreen + LeaveSmudge Scorch
```
Turret-scale variant `BlasterProton`/`BlackCDefCannon`: same look on
`BulletAS` with `LaunchAngle: 42–120` (arcing volley) — exactly the
new green plasma turret. Artillery scale: `hugegreenplasma` image.

**Classic TS rocket trail** (ordered for all TS rockets): on the
missile projectile —
```
Projectile: MissileTA
	TrailImage: small_smoke_trail
	TrailSequences: idle2
```
That single pair IS the classic white TS smoke trail (CyborgRocket,
ReaperScythe, every SP rocket). Our TS rockets should adopt the
recipe; if we lack an equivalent trail sprite, create our own (SP's
asset itself is off-limits per the asset law). **Our equivalent
trails already exist**: `smokey` (generic white TS smoke, 71 uses),
`blue_smokey` (blue — used for CABAL's blue identity, e.g.
`^CabalMissile`), `black_smokey`/`red_smokey`. Config: `TrailImage:
blue_smokey` + `TrailPalette: effect75alpha` + `TrailInterval: 1`
(the Ixian pattern; the sprite's default `idle` sequence is used, no
`TrailSequences` needed). Use these in place of SP's `small_smoke_
trail`.

**CABAL laser identity** (we ruled dark blue/purple): SP agrees —
Minotaur `PalaLazor`: LaserZap `Color: 1122FF88` + `SecondaryBeam`
white-cyan core `55fffff0`, Width 250/30, `HitAnimSequence: lazerflare`
palette `apblue`; Core Defender variant `0011FF88`. Railguns cyan
`22BBFF`/helix `44FFFF`. Recipe: main beam saturated deep blue at ~50%
alpha + thin near-white secondary core.

**Tracer performance trick**: `InstantHitWithFakeBullets` projectile
(Centurion vulcan) renders fake tracer bullets on an instant hit —
cheap high-ROF guns. NOT in our engine (port candidate).

**Web/stun on hit**: `SpreadDamageWithCondition` warhead (damage +
grants a condition like `WebDisable`/`Slowdown50pp` with duration on
victims). NOT in our engine — port candidate; useful for Reaper webs,
Devourer-style slows, and our corrosion mechanics.

### 4. Port candidates for the Cameo engine (OpenRA.Mods.Cameo)

Already present here: MissileTA, Railgun, FireFragment/FireShrapnel,
SpawnActorWarhead (AS), WarheadTrailProjectile (CA), LeaveSmudge
(Common), TakeOffOnMake (ported by tjk-ws).

High value, small ports:
- **ArmamentsChargeBar** — a charge-up UI bar for weapons; exactly what
  the Hacker / Ixian Projector charge mechanic needs.
- **SpreadDamageWithCondition** — see above.
- **InstantHitWithFakeBullets** — perf-friendly tracers for chainguns.
- **GuardsSelection** — support units ordered with a combat group
  auto-guard it (QoL for repair/medic units, incl. our new CABAL
  engineer).
- **SpawnCorpseOnDeath + SpawnActorsOnCorpseInRadius** — the
  nanomachine reanimation pair (CABAL flavor).
- **FirestromSP** — ring-shaped firestorm damage field.
- **WeaponWeather / CloudSpawner** — map-wide weapon weather (ion
  storms) and drifting cloud shadows; TS atmosphere.
- **SpawnSparks** — cheap ambient spark/effect emitter (CABAL bases).
- **WithMakeExplodeWeapon / WithSupportPowerActivationExplodeWeapon** —
  fire an effect weapon on build/power activation (visual polish).
- **ExplodesAlsoTransported** — passengers explode properly in
  transports (bug-class fix we may share).
- **AttackGarrisonedSP** — one fire port per passenger.
- AI: **UnpackBaseBotModule** (bot expands with spare MCVs),
  McvManagerSP; HarvesterBotModuleSP.

### 5. Differences worth noting vs our TS factions

- SP prices sit ~2–3× ours (Centurion 900, Minotaur 2000, Obelisk-class
  2500) — do NOT copy stats, only looks/mechanics; our balance comes
  from the Armor System workbook.
- SP's CABAL has no walls-of-cyborgs identity like 333ggg's concept —
  ours goes wider (Crab/Widow/Avatar, obelisk variants). Their roster
  overlaps ours on: Cyborg Reaper (web!), Cyborg Commando (plasma),
  Wasp, repair vehicle (we replaced with the repair-beam engineer),
  artillery spider (theirs deploys drones — a candidate twist for our
  Artillery Walker neutron upgrade instead of plain AoE?).
- Death feedback: per-death-type corpses/blood (`CabalDeath` etc.) and
  `SpawnHuskEffectOnDeath` (husk flies off as a projectile) — TS-feel
  polish we lack.
- Their garrison rule: `AttackGarrisonedSP` fire ports per passenger —
  compare with our §11 garrison law.

### 6. Follow-ups queued in ROADMAP

- TS authenticity pass now has its local reference (this doc, §3).
- CABAL weapon quality pass: use §3 recipes; Drone Host chain for
  ideas; keep our workbook stats.
- Engine port shortlist (§4) — needs design's priority pick.
- Reaper web upgrade (design 2026-07-11): SP's Improved Reaper Nets
  equivalent, implemented Cameo-style — a warhead that applies the
  existing `snared` condition (`^Snareable`, the Zerg Corruptor
  pattern) as a CABAL upgrade research improving TSReaperTrap.
- NO SP assets ever (asset law in the header) — recreate effects and
  sounds; only base-TS material or newly created work.

---

## Mission win/lose conditions (campaign design)

_Merged 2026-08-23 from `docs/design/mission_win_lose_research.md`, unedited below this line._

_Research 2026-07-29_
_Cross-comparing Combined Arms (CA), Shattered Paradise (SP), base OpenRA (Cnc/RA/D2k), and the Cameo survival map._

### Purpose

Identify how each codebase ensures missions **reach a definitive end** (win or lose) rather than continuing indefinitely. Extract best practices applicable to the Cameo survival map.

---

### 1. Base OpenRA (Cnc, RA, D2k) — The Foundation

#### 1.1 Shared Pattern: `InitObjectives(player)`

Every OpenRA mod (Cnc, RA, D2k) defines `InitObjectives` in their `campaign.lua`. This is the **mandatory setup function** called once per human player in `WorldLoaded`:

**Cnc** (`OpenRA-bleed/mods/cnc/scripts/campaign.lua:14-32`):
```lua
InitObjectives = function(player)
    Trigger.OnObjectiveCompleted(player, function(p, id)
        Media.DisplayMessage(p.GetObjectiveDescription(id), UserInterface.GetFluentMessage("objective-completed"))
    end)
    Trigger.OnObjectiveFailed(player, function(p, id)
        Media.DisplayMessage(p.GetObjectiveDescription(id), UserInterface.GetFluentMessage("objective-failed"))
    end)
    Trigger.OnPlayerLost(player, function()
        Trigger.AfterDelay(DateTime.Seconds(1), function()
            Media.PlaySpeechNotification(player, "Lose")
        end)
    end)
    Trigger.OnPlayerWon(player, function()
        Trigger.AfterDelay(DateTime.Seconds(1), function()
            Media.PlaySpeechNotification(player, "Win")
        end)
    end)
end
```

**RA** (`OpenRA-bleed/mods/ra/scripts/campaign.lua:14-33`): Identical pattern, uses `"MissionFailed"` / `"MissionAccomplished"` speech notifications.

**D2k** (`OpenRA-bleed/mods/d2k/scripts/campaign.lua:42-60`): Identical pattern, uses `"Lose"` / `"Win"`.

#### 1.2 How Win/Lose Actually Triggers

The engine **automatically** fires `Trigger.OnPlayerWon` when all primary objectives are completed, and `Trigger.OnPlayerLost` when any primary objective is failed. The mission script's job is to:

1. Call `InitObjectives(player)` to register the callbacks
2. Create objectives with `AddPrimaryObjective` / `AddSecondaryObjective`
3. In `Tick()` or event triggers, call `MarkCompletedObjective` / `MarkFailedObjective`
4. The engine handles the rest — speech, game-over screen, etc.

#### 1.3 Example: Simple Mission (gdi01.lua)

`OpenRA-bleed/mods/cnc/maps/gdi01/gdi01.lua:29-60`:
```lua
WorldLoaded = function()
    GDI = Player.GetPlayer("GDI")
    Nod = Player.GetPlayer("Nod")
    InitObjectives(GDI)  -- Register win/lose callbacks
    SecureAreaObjective = AddPrimaryObjective(GDI, "eliminate-nod")
    BeachheadObjective = AddSecondaryObjective(GDI, "establish-beachhead")
end

Tick = function()
    if Nod.HasNoRequiredUnits() then
        GDI.MarkCompletedObjective(SecureAreaObjective)  -- Win
    end
    if DateTime.GameTime > DateTime.Seconds(5) and GDI.HasNoRequiredUnits() then
        GDI.MarkFailedObjective(BeachheadObjective)  -- Lose
        GDI.MarkFailedObjective(SecureAreaObjective)
    end
    -- Secondary objective check
    if DateTime.GameTime % DateTime.Seconds(1) == 0 and not GDI.IsObjectiveCompleted(BeachheadObjective)
       and CheckForBase(GDI, GDIBaseBuildings) then
        GDI.MarkCompletedObjective(BeachheadObjective)
    end
end
```

**Key pattern**: Win/lose checks run in `Tick()`. The engine fires the win/lose speech automatically once objectives are marked.

#### 1.4 Example: Complex Mission (gdi04a.lua)

`OpenRA-bleed/mods/cnc/maps/gdi04a/gdi04a.lua:89-95`:
```lua
Tick = function()
    Nod.Cash = 1000  -- Perpetual AI cash
    if (GDIReinforcementsLeft == 0 or not GDI.IsObjectiveCompleted(ReinforcementsObjective))
       and GDI.HasNoRequiredUnits() then
        GDI.MarkFailedObjective(GDIObjective)  -- Lose
    end
end
```

Win is triggered by `Trigger.OnRemovedFromWorld(crate, function() GDI.MarkCompletedObjective(GDIObjective) end)` — an event-based win condition, not a poll.

#### 1.5 Key OpenRA Best Practices

- **Always** call `InitObjectives(player)` in `WorldLoaded` for each human player
- Win/lose checks in `Tick()` use `HasNoRequiredUnits()` — simple and reliable
- Event-based triggers (`OnKilled`, `OnCapture`, `OnRemovedFromWorld`, `OnEnteredFootprint`) can mark objectives without polling
- `AddPrimaryObjective` / `AddSecondaryObjective` are global helpers defined in `common/scripts/utils.lua` that auto-announce to the player
- AI cash injection in `Tick()` is fine but should be guarded by game state

---

### 2. Shattered Paradise (SP) — TS Total Conversion

#### 2.1 SP's `mission_utils.lua`

`Shattered-Paradise-SDK-bleed/mods/sp/scripts/mission_utils.lua:14-48`:
```lua
AddPrimaryObjective = function(player, description)
    local translation = UserInterface.GetFluentMessage(description)
    return player.AddObjective(translation, UserInterface.GetFluentMessage("primary-objective"), true)
end
AddSecondaryObjective = function(player, description)
    local translation = UserInterface.GetFluentMessage(description)
    return player.AddObjective(translation, UserInterface.GetFluentMessage("secondary-objective"), false)
end
TranslatedNotification = function(who, text, color)
    Media.DisplayMessage(UserInterface.GetFluentMessage(text), UserInterface.GetFluentMessage(who), HSLColor.FromHex(color))
end
```

**Notable**: SP does NOT define its own `InitObjectives` — it relies on the base OpenRA pattern. Individual missions handle win/lose directly.

#### 2.2 SP Mission Pattern: `CheckObjectivesOnMissionEnd(success)`

SP's cabal-01 mission (`mods/sp/maps/cabal-01/mission.lua:60-104`) uses a **centralized end-game function**:

```lua
CheckObjectivesOnMissionEnd = function(success)
    -- Check all secondary objectives first
    if not LocalPlayer.IsObjectiveCompleted(SecondaryObjectiveHackAllArray) then
        LocalPlayer.MarkFailedObjective(SecondaryObjectiveHackAllArray)
    end
    if not LocalPlayer.IsObjectiveCompleted(SecondaryObjectiveCaptureMCV) then
        -- Try to check if player has MCV/conyard
        for key,unit in ipairs(LocalPlayer.GetActorsByType("cabmcv")) do
            LocalPlayer.MarkCompletedObjective(SecondaryObjectiveCaptureMCV)
            break
        end
        -- ... similar for cabyard
        if not LocalPlayer.IsObjectiveCompleted(SecondaryObjectiveCaptureMCV) then
            LocalPlayer.MarkFailedObjective(SecondaryObjectiveCaptureMCV)
        end
    end
    -- Mark primary objectives
    if success then
        LocalPlayer.MarkCompletedObjective(ObjectiveCaptureAlien)
    else
        LocalPlayer.MarkFailedObjective(ObjectiveCaptureAlien)
    end
    -- ... fail any incomplete primaries
end
```

This function is called from **event triggers**:
```lua
Trigger.OnCapture(ScrinRep, function()
    MissionCompleteMessage()
    CheckObjectivesOnMissionEnd(true)  -- Win
end)
Trigger.OnKilled(ScrinRep, function(self, killer)
    CheckObjectivesOnMissionEnd(false)  -- Lose
end)
Trigger.OnKilled(CabHacker, function(self, killer)
    CheckObjectivesOnMissionEnd(false)  -- Lose
end)
```

**Key SP pattern**: Win/lose is **event-driven** (OnCapture, OnKilled), not polled in Tick. The centralized function ensures ALL objectives are resolved (completed or failed) at mission end.

#### 2.3 SP Minigame — Survival with Timer

`Shattered-Paradise-SDK-bleed/mods/sp/maps/minigame-01/mission.lua` is the closest analog to our survival map:

- **Survival objective**: `AddPrimaryObjective(LocalPlayer, "objective-survive")`
- **Secondary objective**: `AddSecondaryObjective(LocalPlayer, "objective-mcv")` (protect MCVs)
- **Timer-based win**: `RemainingTime` counts down in `Tick()`. When it hits 0, `CheckObjectivesOnMissionEnd(true)` fires — the player survived.
- **Event-based lose**: `Trigger.OnKilled(IonTur, function() CheckObjectivesOnMissionEnd(false) end)` — if the key structure dies, instant loss.
- **Wave system**: `SendWaveLoop()` sends reinforcements on a timer, decrements `Waves`, stops when `Waves <= 0`.
- **Difficulty setup**: Random hard modes selected at start, each with unique mechanics.
- **No `InitObjectives` call**: SP minigame does NOT call `InitObjectives` — it relies on the engine's default behavior. This means no speech notifications on win/lose (a gap).

#### 2.4 SP Domination/KotH — Multiplayer Win/Lose

`Shattered-Paradise-SDK-bleed/mods/sp/scripts/domination.lua:86-104`:
```lua
-- If only 1 player left alive, they win
if players_still_in <= 1 then
    for i,player in pairs(players) do
        if player.alive then
            player.object.MarkCompletedObjective(player.objective)
        end
    end
end
-- Or if someone reaches target_points
if winner ~= nil then
    for i,player in pairs(players) do
        if i == winner then
            player.object.MarkCompletedObjective(player.objective)
        else
            player.object.MarkFailedObjective(player.objective)
        end
    end
    in_play = false  -- STOP the game loop
end
```

**Key pattern**: `in_play = false` flag stops the game loop. This is the equivalent of our `GameWon`/`GameLost` flags.

---

### 3. Combined Arms (CA) — The Gold Standard

#### 3.1 CA's `InitObjectives(player)`

`CAmod-master/mods/ca/scripts/campaign.lua:226-267`:
```lua
InitObjectives = function(player)
    Trigger.OnObjectiveAdded(player, function(p, id)
        if p.IsLocalPlayer then
            Trigger.AfterDelay(1, function()
                local colour = HSLColor.Yellow
                if p.GetObjectiveType(id) ~= "Primary" then colour = HSLColor.Gray end
                Media.DisplayMessage(p.GetObjectiveDescription(id), "New " .. string.lower(p.GetObjectiveType(id)) .. " objective", colour)
            end)
        end
    end)
    Trigger.OnObjectiveCompleted(player, function(p, id)
        if p.IsLocalPlayer then
            Media.PlaySoundNotification(player, "AlertBleep")
            Media.DisplayMessage(p.GetObjectiveDescription(id), "Objective completed", HSLColor.LimeGreen)
        end
    end)
    Trigger.OnObjectiveFailed(player, function(p, id)
        if p.IsLocalPlayer then
            Media.DisplayMessage(p.GetObjectiveDescription(id), "Objective failed", HSLColor.Red)
        end
    end)
    Trigger.OnPlayerLost(player, function()
        if player.IsLocalPlayer then
            Trigger.AfterDelay(DateTime.Seconds(1), function()
                Media.PlaySpeechNotification(player, "MissionFailed")
            end)
        end
    end)
    Trigger.OnPlayerWon(player, function()
        if player.IsLocalPlayer then
            Trigger.AfterDelay(DateTime.Seconds(1), function()
                Media.PlaySpeechNotification(player, "MissionAccomplished")
            end)
        end
    end)
end
```

**CA enhancements over base OpenRA**:
- `OnObjectiveAdded` handler — announces new objectives with color-coded messages
- `PlaySoundNotification("AlertBleep")` on objective completion
- `IsLocalPlayer` check — only show messages to the local player (multiplayer-safe)
- Both speech and text notifications

#### 3.2 CA Coop Win/Lose Sync

`CAmod-master/mods/ca/scripts/coop.lua:316-350`:
```lua
ForEachPlayer(function(player)
    Trigger.OnPlayerWon(player, function()
        Trigger.AfterDelay(DateTime.Seconds(1), function()
            Media.PlaySpeechNotification(player, "Win")
        end)
    end)
    Trigger.OnPlayerLost(player, function(p)
        PlayerDefeatedOrDisconnected(p)  -- Redistribute units to survivors
    end)
    TriggerCA.OnPlayerDisconnected(player, function(p)
        PlayerDefeatedOrDisconnected(p)
    end)
end)

Trigger.OnObjectiveCompleted(MainPlayer, function(_, obid)
    ForEachPlayer(function(player)
        player.MarkCompletedObjective(obid)  -- Mirror to all coop players
    end)
end)
Trigger.OnObjectiveFailed(MainPlayer, function(_, obid)
    ForEachPlayer(function(player)
        player.MarkFailedObjective(obid)  -- Mirror to all coop players
    end)
end)
```

**Key CA coop patterns**:
- Objectives are **mirrored** across all coop players — when MainPlayer completes/fails, all players get the same
- `PlayerDefeatedOrDisconnected` redistributes units and cash to survivors
- `OnPlayerDisconnected` handled separately from `OnPlayerLost`
- Win speech played per-player via `ForEachPlayer`

#### 3.3 CA Mission End Conditions

CA missions (e.g., `crossrip.lua`) use:
- `MissionPlayersHaveNoRequiredUnits()` — checks if ALL human players have no units (defeat)
- Event triggers for specific objectives (OnCapture, OnKilled, OnEnteredFootprint)
- `Trigger.OnAllKilled` for squad-based objectives
- Difficulty-scaled AI attacks via `InitAttackSquad` system
- `AfterWorldLoaded` / `AfterTick` hooks for mission-specific logic

---

### 4. Cameo Survival Map — Current State & Gaps

#### 4.1 What Works

- **Wave system**: `SendWave()` with `FinalWaveSent` flag, `TotalWaves` count
- **Defeat check**: `CheckDefeat()` polls every 100 ticks, checks `HasNoRequiredUnits()` on all active players
- **Victory check**: `CheckVictory()` polls every 100 ticks, checks if all `LiveFoes` are dead after `FinalWaveSent`, or if all Foe players have no units
- **Objective creation**: Creates "Survive all enemy waves" and "Destroy all enemy bases" objectives on all human players
- **Game state flags**: `GameWon`, `GameLost`, `FinalWaveSent` control flow

#### 4.2 What's Broken / Missing

| Issue | Impact | Reference | Status |
|-------|--------|-----------|--------|
| **No `InitObjectives` call** | No `Trigger.OnPlayerWon`/`OnPlayerLost` handlers → no speech notifications ("MissionAccomplished"/"MissionFailed"), no clean game-over feedback | All three reference codebases register these | **FIXED** — Added `InitObjectives` with all handlers |
| **No `Trigger.OnObjectiveCompleted/Failed` handlers** | Players get no notification when objectives are marked complete/failed | CA and OpenRA both register these | **FIXED** — Added in `InitObjectives` |
| **`GameLost` not checked in perpetual systems** | `RandomReinforcementDrop`, `RandomEventScheduler`, `CheckDifficulty`, AI cash injection all continue after player loses | SP minigame's `in_play = false` stops all loops; CA checks game state in all schedulers | **FIXED** — All systems now check `GameLost` |
| **No `GameLost` guard in `SendWave`** | If player loses between waves, next wave still fires | Should check `GameLost or GameWon` at top of `SendWave` | **FIXED** — Guard added |
| **No `GameLost` guard in AI cash injection** | AI keeps getting cash after game is over | `Tick()` line 2717 should check game state | **FIXED** — Guard added |
| **No centralized end-game function** | Win/lose logic scattered across `CheckDefeat`/`CheckVictory`, no single function to resolve all objectives | SP's `CheckObjectivesOnMissionEnd(success)` is the model | **FIXED** — Added `ResolveMission` |
| **No objective announcement** | Players don't see "New primary objective" when objectives are created | CA's `OnObjectiveAdded` handler announces | **FIXED** — Added `OnObjectiveAdded` handler |
| **`LiveFoes` tracking edge cases** | Delayed spawns via `Trigger.AfterDelay` may not be in `LiveFoes` when victory check runs | Could cause premature victory trigger | **FIXED** — Added `PendingSpawns` counter |

---

### 5. Comparative Summary

| Feature | OpenRA | SP | CA | Cameo Survival |
|---------|--------|-----|-----|----------------|
| `InitObjectives` with win/lose speech | Yes | No (relies on engine) | Yes (enhanced) | **YES** (implemented) |
| `OnObjectiveCompleted/Failed` messages | Yes | No | Yes (with sound) | **YES** (implemented) |
| `OnObjectiveAdded` announcement | No | No | Yes | **YES** (implemented) |
| Centralized end-game function | No | Yes (`CheckObjectivesOnMissionEnd`) | No | **YES** (`ResolveMission`) |
| Event-driven win/lose | Partial | Yes (OnCapture/OnKilled) | Partial | No (poll-based) |
| `HasNoRequiredUnits()` defeat check | Yes | Yes | Yes (`MissionPlayersHaveNoRequiredUnits`) | Yes |
| Game state flags to stop loops | N/A | `in_play` | Various | `GameWon`/`GameLost` (complete) |
| Coop objective sync | N/A | N/A | Yes (mirror to all) | **YES** (elimination handling) |
| Perpetual system guards | N/A | `in_play` check | Game state checks | **All guarded** (verified) |
| Timer-based win | N/A | Yes (minigame) | No | No (wave-based) |
| Wave system | N/A | Yes (minigame) | Yes (attack squads) | Yes |

---

### 6. Fixes Applied to Cameo Survival Map (2026-07-29)

All 5 recommended fixes have been implemented in `mods/cameo/maps/survival/script.lua`.

#### Fix 1: `InitObjectives` (Implemented)

Added CA-style `InitObjectives(player)` function (~line 2564) and called it for each human player in `WorldLoaded`:
- `Trigger.OnObjectiveAdded` → displays "New primary/secondary objective" message with color coding (with `IsLocalPlayer` check)
- `Trigger.OnObjectiveCompleted` → plays "AlertBleep" + displays green message (with `IsLocalPlayer` check)
- `Trigger.OnObjectiveFailed` → displays red message (with `IsLocalPlayer` check)
- `Trigger.OnPlayerLost` → plays "MissionFailed" speech (1s delay, `IsLocalPlayer` check)
- `Trigger.OnPlayerWon` → plays "MissionAccomplished" speech (1s delay, `IsLocalPlayer` check)

#### Fix 2: All Perpetual Systems Guarded with `GameLost` (Implemented)

Every `if GameWon` check in the file updated to `if GameWon or GameLost`. Verified with grep — zero remaining unguarded instances:
- `RandomReinforcementDrop` — entry guard
- `RandomEventScheduler` — entry guard + event fire guard + reschedule guard
- `CheckDifficulty` — entry guard
- `SendWave` — entry guard
- `RandomTauntBurst` — entry guard + inner delayed callback guard
- `MemelordDuel` — entry guard + all 8 delayed callback guards
- `DualFactionAttack` — entry guard
- `PlayCrossTaunt` — all delayed callback guards
- AI cash injection in `Tick()` — condition guard
- RANDOM SILENCE trap — delayed spawn guard

#### Fix 3: Centralized `ResolveMission` (Implemented)

Added `ResolveMission(success, reasonText, messageText)` function (~line 2588):
- Sets `GameWon` or `GameLost` flag
- Marks ALL survive + destroy objectives on ALL players as completed or failed
- Displays final mission text and message
- `CheckDefeat` and `CheckVictory` both refactored to call it (no more duplicated logic)

#### Fix 4: Coop Player Elimination (Implemented)

`CheckDefeat` now handles individual player elimination in multiplayer:
- Detects players with `HasNoRequiredUnits()`, announces their elimination
- Removes eliminated players from `ActivePlayer` list
- Mission loss only triggers when NO survivors remain
- `EliminatedPlayers` table prevents duplicate elimination announcements

#### Fix 5: `LiveFoes` Tracking Edge Case (Implemented)

Added `PendingSpawns` counter to prevent premature victory:
- `SpawnUnitListAt` increments `PendingSpawns` by the number of units scheduled via `Reinforcements.Reinforce`
- The arrival callback decrements `PendingSpawns` when each unit arrives and is added to `LiveFoes`
- `CheckVictory` now requires `PendingSpawns == 0` before checking if all `LiveFoes` are dead
- This prevents a victory trigger when reinforcements are in transit but not yet counted in `LiveFoes`

---

### 7. Source Files Referenced

- `OpenRA-bleed/mods/cnc/scripts/campaign.lua` — Cnc campaign framework
- `OpenRA-bleed/mods/ra/scripts/campaign.lua` — RA campaign framework
- `OpenRA-bleed/mods/d2k/scripts/campaign.lua` — D2k campaign framework (most sophisticated AI)
- `OpenRA-bleed/mods/common/scripts/utils.lua` — Shared `AddPrimaryObjective`/`AddSecondaryObjective`/`IdleHunt`
- `OpenRA-bleed/mods/cnc/maps/gdi01/gdi01.lua` — Simple mission example
- `OpenRA-bleed/mods/cnc/maps/gdi04a/gdi04a.lua` — Complex mission with reinforcements
- `Shattered-Paradise-SDK-bleed/mods/sp/scripts/mission_utils.lua` — SP objective helpers
- `Shattered-Paradise-SDK-bleed/mods/sp/maps/cabal-01/mission.lua` — Complex SP mission with `CheckObjectivesOnMissionEnd`
- `Shattered-Paradise-SDK-bleed/mods/sp/maps/minigame-01/mission.lua` — SP survival minigame (closest analog to Cameo survival)
- `Shattered-Paradise-SDK-bleed/mods/sp/scripts/domination.lua` — SP multiplayer win/lose with `in_play` flag
- `CAmod-master/mods/ca/scripts/campaign.lua` — CA campaign framework with enhanced `InitObjectives`
- `CAmod-master/mods/ca/scripts/coop.lua` — CA coop system with objective mirroring and player defeat handling
- `CAmod-master/mods/ca/missions/main-campaign/ca01-crossrip/crossrip.lua` — CA mission example
- `CAmod-master/mods/ca/missions/coop-campaign/ca01-crossrip-coop/crossrip-coop.lua` — CA coop mission
- `Cameo-mod/mods/cameo/maps/survival/script.lua` — Current survival map script (2770 lines, fixes applied)
- `Cameo-mod/mods/cameo/maps/survival/rules.yaml` — Survival map rules

---

## CABAL faction rebuild — concept to actor mapping

_Merged 2026-08-23 from `docs/design/cabal_rebuild_plan.md`, unedited below this line._

_Working plan for executing the CABAL concept workbook. Sheet stats are
formula-validated (same system as `cameo_armor_system.xlsx`); the sheet
wins on mismatch. Status: mapping done 2026-07-11; execution follows
the design picks at the bottom._

### Concept → existing actor mapping

| concept (sheet stats) | existing actor (game stats) | action |
|---|---|---|
| Cyborg 500 · 45k HP · 50spd · 20000@60 | cabal_cyborginfantry (300 · 35k · 56) | rebalance to sheet |
| cnc4 Cyborg 750 · 60k · 24000@48 | — | NEW research (Cyborg→cnc4, Forgotten-chem pattern) |
| Rocket Cyborg 650 · 45k · 24000@60 | closest: cabal_devout? | map or NEW (pick) |
| cnc4 Rocket 900 · 60k · 24000@50 | — | NEW research |
| Dissolver 725 · 50k · 50spd · K=1.5 | cabal_dissolver (750 · 28k · 70) | rebalance; K question: vampire ✓ implemented, cloak NOT — add cloak or K=1.25 |
| Hacker 1250 · 30k · 80spd | cabal_hackercyborg (1200 · 60k · 56) | rebalance |
| T800 1250 · 85k · 32000@32 | cabal_eliminator800 (inf, 1000 · 16k) | rebalance + naming decision |
| T1000 1500 · 100k · 32000@30 | cabal_eliminator1000 (a 250k VEHICLE!) | design pick: concept T1000 is an infantry research of T800; existing eliminator1000 is a different vehicle |
| Cyborg Commando 5000 · 250k | cabal_cyborgcommando (4000 · 200k) | rebalance |
| Commando V2 10000 · 400k (research) | cabal_cyborgcommandov2 (8000 · 400k) | rebalance + wire as research |
| Tarantula 1000 · 110k · 70spd · 16000@48 | cabal_tarantula (1500 · 250k · 75) | rebalance (large) |
| Crab 675 · 50k · 100spd · 16000@25 · rng 1.6 | — | NEW (short-range fast brawler) |
| cnc4 Avatar 2250 · 175k · 32000@40 | cabal_heavyspider? (1200 · 80k) | design pick: rebuild heavyspider as Avatar or NEW |
| Widow 2400 · 100k · 40000@50 (Avatar research) | — | NEW research unit |
| Mantis 500 · 35k · 120spd | cabal_mantis (600 · 40k · 160) | rebalance |
| Spider — TWO variants in sheet: adv-scout 900 OR fire-support 1200 | cabal_laserspider / cabal_spidertankdrone | design pick: which role, which actor |
| Cyborg Reaper 1100 · 70k · AA support | cabal_cyborgreaper (1000 · 75k) | rebalance |
| Heavy Reaper 1400 · 100k (research) | — | NEW research |
| Artillery Walker 1250 · 50k · 70spd · 48000@64 · rng 11.58 | cabal_artilleryspider (1600 · 200k · 60) | rebalance (large) |
| Core 12500 · 1.5M · 160000@70 | cabal_coredefender (10000 · 1M) | rebalance |
| Hunter Killer mk1 1500 · 35k · 160spd | cabal_hunterkillermk1 (1000 · 22.5k · 145) | rebalance |
| Hunter Killer mk2 3000 · 300k · 50spd (SPACESHIP class!) | cabal_hunterkillermk2 (2400 · 60k · 145) | rebalance — mk2 becomes a slow heavy spaceship |
| Cyborg Pillbox 800 · 85k · 12000@18 | cabal_pillbox (600 · 110k) | rebalance |
| Obelisk of Darkness 1200 · 120k · rng 12.66 — **as the AA defense** | cabal_obeliskofdarkness (1350 · 242.5k) | rebalance + role move to AA (sheet section) |
| "Obelisk of Balls" 2400 · 220k · 140000@90 · K=0.75 advanced defense | cabal_heavycabalobelisk (2600 · 300k)? | design pick: same unit? display name needed (proposals below); K=0.75 = negative special? |
| "Nuke or smth" | cabal_missilesilo | exists, keep |
| Scarab APC (tree, no stats row) | cabal_scarabapc (2600) | keep or add sheet row |
| Carryall (tree, no stats row) | cabal_overkillcarryall | keep |
| Engineer / Harvester / T4 stealth gen | exist | keep |

### Execution rules (from DESIGN.md §12)

Sheet wins; every changed weapon = own weapon inheriting the sealed
class templates; even spread; FF twins 50/50; Percentage = 1 per 2000;
nice-number law (prices 25s, damage 2000s, HP 2500/1000 steps, speed
5s); promotion/research units inherit ^PromotionUnitBuff (not modeled
in sheet); descriptions per §7 as part of the pass.

### Design picks needed before execution

1. **Spider role**: advanced scout (900) or fire support (1200)? And is
   it cabal_laserspider or cabal_spidertankdrone (the other one is then
   freed or cut)?
2. **T800/T1000 vs eliminator800/eliminator1000**: concept has T1000 as
   an infantry research of the T800; the live eliminator1000 is an
   unrelated 250k-HP vehicle. Rename/rebuild how?
3. **"Obelisk of Balls"**: map to cabal_heavycabalobelisk? Display-name
   proposals: "Obelisk of Annihilation", "Twin Obelisk", "Obelisk
   Prime" (or keep the meme?). Also: its K=0.75 is below 1 — intended
   as a NEGATIVE special (drawback), or a typo for 1.75?
4. **Avatar**: rebuild cabal_heavyspider into the cnc4 Avatar, or new
   actor and keep the heavyspider separately?
5. **Rocket Cyborg**: is cabal_devout the intended base, or a new unit?
6. **Dissolver K=1.5**: add the missing innate cloak (vampire is
   already implemented), or drop the sheet to K=1.25?


### Batch 2b work order (design 2026-07-11)

- **Engineer**: gets the repair beam + ammo system per the Naxis
  engineering truck / Schwarzer Mond repair bot / Terran SCV pattern.
- **Rocket Cyborg**: cabal_platedarmorcyborg RENAMES to
  cabal_rocketcyborg (sheet row 650/45k/24000@60); **cabal_devout is
  its promotion upgrade** (cnc4 Rocket row 900/60k/24000@50).
- **Hacker**: weak Ixian-projector-style disabling weapon (charge-up
  first), ~10 range, low attack speed, formula-priced. Sound: the GDI
  Predator laser targeting sound, NOT tesla. Additional hacking
  mechanic: open brainstorm (vehicle mind-control too Yuri-like).
- **Ixian Projector rework** (D2k Ixian): predator-laser sound; DOUBLE
  damage on weapon and EMP; holograms become carrier-master/slave
  drones (aircraft-carrier logic on a ground unit — experiment):
  projector damages + EMP-disables + marks the target, holograms
  attack it. Replaces deploy + mob-spawner.
- **New units**: Crab/Widow/Avatar/Heavy Reaper launch with placeholder
  art from base units (no art yet).
- **Pillbox**: it is a BUNKER (building + infantry inside; the
  garrison's weapon is the defense; cost = initial load). References:
  RA2 Soviet Battle Bunker, Terran bunker, RA1/RA2 pillboxes. Options
  for a unique CABAL version to be proposed.
- **New early turret**: Nod Laser Turret art, fires the CLASSIC GREEN
  PLASMA BALL. The same green plasma projectile goes on Cyborg
  Commando and Commando Mk2 (asset exists somewhere in the files).
- **TS authenticity pass**: find the classic TS rocket trail(s), apply
  to all TS rocket units; reference the Shattered Paradise mod for
  correct TS projectile/explosion/sound effects across all TS units.

### Appendix: 333ggg's cell annotations (extracted 2026-07-11)

cabal.xlsx carries 26 cell comments — the design intent per unit.
Key ones (Лист1 tree unless noted):
- Cyborg (B2): "basic heavy infantry, probably manual vision range
  needed"; its pillbox neighbor (E2): "tankier but less dps ts laser
  turret" → pillbox = laser-turret style.
- Rocket Cyborg (B3): "basic anti-air anti-tank heavy infantry" ✓.
- Mantis (C3): "scout without turret, slightly better stats than
  average scout" ✓ (ranged frontal gun, NOT melee — confirmed by
  design 2026-07-11 after a brief melee detour).
- Crab (C4): "fast melee vehicle" ✓ (regular unit, zergling↔ultralisk).
- Dissolver (B5): "heavy anti-tank infantry, TD warhead and lifesteal".
- Tarantula (C5): "heavy main battle tank with heavy but slow gun".
- Scarab APC (C6): "apc. I leave its balance to you".
- Hacker (B7): "heavy infantry with emp weapon".
- Artillery Spider (C7): "heavy artillery. Maybe tier 3?" — ❓ open.
- HK mk1 (D7): "another MG helicopter"; Obelisk of Darkness (E7):
  "fast hitscan flak aa defense with laser projectile".
- Heavy Reaper (C8): "sturdy anti-air cyborg with root mechanic" ✓
  (root = TSReaperTrap web).
- cnc4 Spider (C9): "longer range fire support laser unit. Can enter
  widow to boost its laser. Potentially web laser mechanic".
- T1000 (B10): "heavy infantry with plasma (tesla+chemical maybe?)";
  Avatar (C10): "heavy walker with plasma(?) weaponry"; HK mk2 (D10):
  "medium spaceship with beam cannons, plasma upgrade"; Obelisk Prime
  (E10): "heavy defense with td+laser warhead".
- Commando V2 (B11): plasma tesla+chem; Widow (C11): "heavy fire
  support vehicle. Laser can be boosted by up to 4 spiders inside";
  superweapon (E11): "dune emp nuke would fit".
- Tier IV (C12): "Superheavy walker"; stealth generator (E12):
  "should give some kind of buff rather than stealth around self".
- Лист2 B26/B33: both Spider variants "similar to cnc4" / "beam cannon".

Plasma class ruling from the annotations: plasma ≈ Tesla + Chemical
warhead mix (B10/B11) — use for T1000, Commando plasma, Avatar.

### Appendix 2: design screenshots 2026-07-11 — promotion trees + upgrades

Promotion tree (right column = empty placeholders like TS GDI):

| left (infantry) | middle (vehicles) | right |
|---|---|---|
| Devout (1) | Spider CNC4 (2) | - |
| Ascended (4) | Heavy Reaper -> Manticore (5) | - |
| T1000 (7) | Widow (8) | - |
| CybCom v2 (10) | Core Defender (11) | - |

Upgrade suite "Networked Cabal Protocol":
- Radar tier: Backup Systems (reclaim vehicles from husks),
  Reclamation Protocol (gives HP and regen), Neutron Nuclear Catalyst
  (KEEP the existing neutron-shell twins unchanged — design praise —
  optionally extend to more units).
- Lab tier: Mobility Matrix (speed+HP of walkers), Advanced Beam
  Cannons (upgrade: defenses, HK mk2, spider, mantis, widow; new to:
  MG cyborgs, tarantula, spider tank drone, HK mk1), Proton
  Dissolution (upgrade: cyborg commando, T800/1000, avatar; gives
  weapon to: HK mk2, artillery, rocket cyborgs, reapers), Overcharged
  Servos (attack speed: reapers, avatar, HK mk2, tarantula, artillery,
  rocket cyborgs, T800/100, cyborg commando).

Sequencing ruling: prerequisites + stats FIRST (faction fully in
game), effects and art AFTER (SP-behaviour recipes, own art only).

---

## Schwarzer Mond icon/artwork status

_Merged 2026-08-23 from `docs/design/schwarzer_mond_artwork_status.md`, unedited below this line._

### Copy-pasted / borrowed icons (need replacement)

These Schwarzer Mond actors previously used icons from the Naxis faction or reused
another Schwarzer Mond actor's icon. They now have temporary unique placeholder
icons pending final artwork.

| Priority | Actor | Current icon | Notes |
|---|---|---|---|
| High | `schwarzer_mond_mars` | `schwarzer_mond_mars_icon.png` | MARS hover artillery; placeholder generated. |
| High | `schwarzer_mond_m200bjagerline` | `schwarzer_mond_m200bjagerline_icon.png` | Heavy tank destroyer/artillery; placeholder generated. |
| Medium | `schwarzer_mond_gravitycoretank` | `schwarzer_mond_gravitycoretank_icon.png` | Superheavy advanced tank; placeholder generated. |
| Low | `schwarzer_mond_blackbomb` | `schwarzer_mond_blackbomb_icon.png` | Kamikaze bomb; placeholder generated. |

### Missing icon files

All icon files referenced by `sequences.yaml` exist in `mods/cameo/bits/ra2/` or
`mods/cameo/bits/ra2/mod/`. No missing PNGs were found.

### Other potential artwork gaps

This audit only checked icon filenames. A full asset audit (sprites, voxel
sequences, SHP files, cameo artwork) has not been run. The user should decide if
we should expand the search to:

- Placeholder/default SHP sprite sheets for buildings and vehicles.
- Voxel files (`.vxl`/`.hva`) for voxel-based units.
- Construction / death / weapon-fire animation sequences.
- Faction-specific UI artwork (loading screens, faction icon, etc.).

### Suggested replacement order

1. **MARS + M200 B. Jägerline** — both use the same borrowed Naxis icon and are
   player-facing combat units. Fixing them removes the most obvious copy-paste.
2. **Gravity Core Tank** — uses a Naxis Jagdpanzer icon; a superheavy tank needs
   a distinctive cameo.
3. **Black Bomb** — optional, internal reuse is less urgent.
4. **Full asset sweep** — if time permits, run a sequence-by-sequence audit for
   missing or placeholder sprites/voxels.

---

## Tier-chain validation

_Merged 2026-08-23 from `docs/design/tier_chain_validation.md`, unedited below this line._

### What changed

The original `tier_gates.py` used `name.split('_')[0]` as the faction key and allowed a unit to pick the cheapest building from **any** faction for a generic token. That produced impossible build orders such as a TD Nod unit buying a GDI Construction Yard. This validator restricts each unit to buildings from its own ContentPack faction plus the same game's Shared pack.

### Corrected tier bucket medians

| tier | units | median $ | mean $ | min | max |
|---|---|---:|---:|---:|---:|
| T0 no chain | 109 | 0 | 0 | 0 | 0 |
| T1 production | 628 | 9,500 | 9,334 | 800 | 19,700 |
| T2 radar | 239 | 11,600 | 11,767 | 5,600 | 24,000 |
| T3 tech center | 1 | 15,000 | 15,000 | 15,000 | 15,000 |
| T4 tech+extra | 354 | 17,750 | 18,014 | 10,800 | 30,100 |

### Functional forms (recalibrated)

- B (T1 median) = $9,500
- S = (T4 median - B) = $8,250
- alpha (power law) = 1.1089

| tier | median $ | rational x | power x |
|---|---:|---:|---:|
| T0 no chain | 0 | 1.000 | 1.000 |
| T1 production | 9,500 | 1.000 | 1.000 |
| T2 radar | 11,600 | 0.797 | 0.801 |
| T3 tech center | 15,000 | 0.600 | 0.603 |
| T4 tech+extra | 17,750 | 0.500 | 0.500 |

Extrapolation:

- tortuga $21,500: rational x0.407, power x0.404
- deepest $30,100: rational x0.286, power x0.278
- hypothetical $50,000: rational x0.169, power x0.159

### Top 10 most expensive corrected chains

- `ra2_soviets_upgrade_kirovatomicbombs`: `$30,100` — ra2_soviets_battlelab, ra2_soviets_constructionyard, ra2_soviets_industrialplant, ra2_soviets_nuclearmissilesilo, ra2_soviets_orerefinery, ra2_soviets_radar, ra2_soviets_teslareactor
- `futuretech_harbingergunship`: `$29,800` — futuretech_battlelab, futuretech_constructionyard, futuretech_hypercore, futuretech_launchpad, futuretech_refinery, futuretech_robotcontrolcenter, futuretech_thermalpowerplant, futuretech_transmissioncenter, futuretech_warpgate
- `futuretech_cryolegionnaire`: `$29,300` — futuretech_battlelab, futuretech_constructionyard, futuretech_hypercore, futuretech_refinery, futuretech_robotcontrolcenter, futuretech_thermalpowerplant, futuretech_transmissioncenter, futuretech_troopgate, futuretech_warpgate
- `latinsyndicate_tortugatank`: `$28,500` — latinsyndicate_defensebureau, latinsyndicate_latinempradar, latinsyndicate_powerstation, latinsyndicate_recyclingcenter, latinsyndicate_recyclingrefinery, latinsyndicate_spycenter, latinsyndicate_syndicateconstructionyard, latinsyndicate_syndicatefactory
- `futuretech_beehivedronecarrier`: `$28,300` — futuretech_battlelab, futuretech_constructionyard, futuretech_hypercore, futuretech_refinery, futuretech_robotcontrolcenter, futuretech_thermalpowerplant, futuretech_transmissioncenter, futuretech_warpgate
- `futuretech_doctrine_equalizerx3`: `$28,300` — futuretech_battlelab, futuretech_constructionyard, futuretech_hypercore, futuretech_refinery, futuretech_robotcontrolcenter, futuretech_thermalpowerplant, futuretech_transmissioncenter, futuretech_warpgate
- `futuretech_energizer`: `$28,300` — futuretech_battlelab, futuretech_constructionyard, futuretech_hypercore, futuretech_refinery, futuretech_robotcontrolcenter, futuretech_thermalpowerplant, futuretech_transmissioncenter, futuretech_warpgate
- `futuretech_futuretank`: `$28,300` — futuretech_battlelab, futuretech_constructionyard, futuretech_hypercore, futuretech_refinery, futuretech_robotcontrolcenter, futuretech_thermalpowerplant, futuretech_transmissioncenter, futuretech_warpgate
- `futuretech_plasmastrider`: `$28,300` — futuretech_battlelab, futuretech_constructionyard, futuretech_hypercore, futuretech_refinery, futuretech_robotcontrolcenter, futuretech_thermalpowerplant, futuretech_transmissioncenter, futuretech_warpgate
- `ordos_deviatorartillery`: `$28,000` — ordos_constructionyard, ordos_heavyfactory, ordos_ixresearchcenter, ordos_outpost, ordos_palace, ordos_refineryordos, ordos_windtrap

### Hand-validated cases

#### td_nod_lasertrooper
- `td_nod_lasertrooper`: `$27,000`
  - file: `mods/cameo/ContentPacks/TiberianDawn/Nod/yaml/infantry.yaml`
  - prerequisites: td_nod_handofnod, td_nod_templeprime, td_nod_promotion_lasertrooper
  - `td_nod_lasertrooper` needs `td_nod_handofnod` ($1,000) for token `td_nod_handofnod`
  - `td_nod_handofnod` needs `td_nod_constructionyard` ($5,000) for token `td_nod_constructionyard`
  - `td_nod_handofnod` needs `NUKE` ($500) for token `nuke`
  - `NUKE` needs `td_nod_constructionyard` ($5,000) for token `fact`
  - `td_nod_lasertrooper` needs `td_nod_templeprime` ($5,000) for token `td_nod_templeprime`
  - `td_nod_templeprime` needs `td_nod_constructionyard` ($5,000) for token `td_nod_constructionyard`
  - `td_nod_templeprime` needs `td_nod_templeofnod` ($10,000) for token `td_nod_templeofnod`
  - `td_nod_templeofnod` needs `td_nod_constructionyard` ($5,000) for token `td_nod_constructionyard`
  - `td_nod_templeofnod` needs `td_nod_communicationscenter` ($2,500) for token `td_nod_communicationscenter`
  - `td_nod_communicationscenter` needs `td_nod_constructionyard` ($5,000) for token `td_nod_constructionyard`
  - `td_nod_communicationscenter` needs `td_nod_tiberiumrefinery` ($3,000) for token `td_nod_tiberiumrefinery`
  - `td_nod_tiberiumrefinery` needs `td_nod_constructionyard` ($5,000) for token `td_nod_constructionyard`
  - `td_nod_tiberiumrefinery` needs `NUKE` ($500) for token `nuke`
  - `NUKE` needs `td_nod_constructionyard` ($5,000) for token `fact`
  - buildings: NUKE, td_nod_communicationscenter, td_nod_constructionyard, td_nod_handofnod, td_nod_templeofnod, td_nod_templeprime, td_nod_tiberiumrefinery

#### ra2_soviets_upgrade_kirovatomicbombs
- `ra2_soviets_upgrade_kirovatomicbombs`: `$30,100`
  - file: `mods/cameo/ContentPacks/RedAlert2/Soviets/yaml/upgrades.yaml`
  - prerequisites: ra2_soviets_battlelab, ra2_soviets_industrialplant, ra2_soviets_nuclearmissilesilo
  - `ra2_soviets_upgrade_kirovatomicbombs` needs `ra2_soviets_battlelab` ($5,000) for token `ra2_soviets_battlelab`
  - `ra2_soviets_battlelab` needs `ra2_soviets_constructionyard` ($5,000) for token `ra2_soviets_constructionyard`
  - `ra2_soviets_battlelab` needs `ra2_soviets_radar` ($2,500) for token `ra2_soviets_radar`
  - `ra2_soviets_radar` needs `ra2_soviets_constructionyard` ($5,000) for token `ra2_soviets_constructionyard`
  - `ra2_soviets_radar` needs `ra2_soviets_orerefinery` ($2,000) for token `ra2_soviets_orerefinery`
  - `ra2_soviets_orerefinery` needs `ra2_soviets_constructionyard` ($5,000) for token `ra2_soviets_constructionyard`
  - `ra2_soviets_orerefinery` needs `ra2_soviets_teslareactor` ($600) for token `ra2_soviets_teslareactor`
  - `ra2_soviets_teslareactor` needs `ra2_soviets_constructionyard` ($5,000) for token `ra2_soviets_constructionyard`
  - `ra2_soviets_upgrade_kirovatomicbombs` needs `ra2_soviets_industrialplant` ($5,000) for token `ra2_soviets_industrialplant`
  - `ra2_soviets_industrialplant` needs `ra2_soviets_constructionyard` ($5,000) for token `ra2_soviets_constructionyard`
  - `ra2_soviets_industrialplant` needs `ra2_soviets_battlelab` ($5,000) for token `ra2_soviets_battlelab`
  - `ra2_soviets_battlelab` needs `ra2_soviets_constructionyard` ($5,000) for token `ra2_soviets_constructionyard`
  - `ra2_soviets_battlelab` needs `ra2_soviets_radar` ($2,500) for token `ra2_soviets_radar`
  - `ra2_soviets_radar` needs `ra2_soviets_constructionyard` ($5,000) for token `ra2_soviets_constructionyard`
  - `ra2_soviets_radar` needs `ra2_soviets_orerefinery` ($2,000) for token `ra2_soviets_orerefinery`
  - `ra2_soviets_orerefinery` needs `ra2_soviets_constructionyard` ($5,000) for token `ra2_soviets_constructionyard`
  - `ra2_soviets_orerefinery` needs `ra2_soviets_teslareactor` ($600) for token `ra2_soviets_teslareactor`
  - `ra2_soviets_teslareactor` needs `ra2_soviets_constructionyard` ($5,000) for token `ra2_soviets_constructionyard`
  - `ra2_soviets_upgrade_kirovatomicbombs` needs `ra2_soviets_nuclearmissilesilo` ($10,000) for token `ra2_soviets_nuclearmissilesilo`
  - `ra2_soviets_nuclearmissilesilo` needs `ra2_soviets_constructionyard` ($5,000) for token `ra2_soviets_constructionyard`
  - `ra2_soviets_nuclearmissilesilo` needs `ra2_soviets_battlelab` ($5,000) for token `ra2_soviets_battlelab`
  - `ra2_soviets_battlelab` needs `ra2_soviets_constructionyard` ($5,000) for token `ra2_soviets_constructionyard`
  - `ra2_soviets_battlelab` needs `ra2_soviets_radar` ($2,500) for token `ra2_soviets_radar`
  - `ra2_soviets_radar` needs `ra2_soviets_constructionyard` ($5,000) for token `ra2_soviets_constructionyard`
  - `ra2_soviets_radar` needs `ra2_soviets_orerefinery` ($2,000) for token `ra2_soviets_orerefinery`
  - `ra2_soviets_orerefinery` needs `ra2_soviets_constructionyard` ($5,000) for token `ra2_soviets_constructionyard`
  - `ra2_soviets_orerefinery` needs `ra2_soviets_teslareactor` ($600) for token `ra2_soviets_teslareactor`
  - `ra2_soviets_teslareactor` needs `ra2_soviets_constructionyard` ($5,000) for token `ra2_soviets_constructionyard`
  - buildings: ra2_soviets_battlelab, ra2_soviets_constructionyard, ra2_soviets_industrialplant, ra2_soviets_nuclearmissilesilo, ra2_soviets_orerefinery, ra2_soviets_radar, ra2_soviets_teslareactor

#### futuretech_harbingergunship
- `futuretech_harbingergunship`: `$29,800`
  - file: `mods/cameo/ContentPacks/RedAlert2Mod/FutureTech/yaml/aircraft.yaml`
  - prerequisites: futuretech_launchpad, futuretech_hypercore, futuretech_promotion_harbingergunship
  - `futuretech_harbingergunship` needs `futuretech_launchpad` ($1,500) for token `futuretech_launchpad`
  - `futuretech_launchpad` needs `futuretech_constructionyard` ($5,000) for token `futuretech_constructionyard`
  - `futuretech_launchpad` needs `futuretech_transmissioncenter` ($2,500) for token `futuretech_transmissioncenter`
  - `futuretech_transmissioncenter` needs `futuretech_constructionyard` ($5,000) for token `futuretech_constructionyard`
  - `futuretech_transmissioncenter` needs `futuretech_robotcontrolcenter` ($2,500) for token `futuretech_robotcontrolcenter`
  - `futuretech_robotcontrolcenter` needs `futuretech_constructionyard` ($5,000) for token `futuretech_constructionyard`
  - `futuretech_robotcontrolcenter` needs `futuretech_warpgate` ($2,000) for token `futuretech_warpgate`
  - `futuretech_warpgate` needs `futuretech_constructionyard` ($5,000) for token `futuretech_constructionyard`
  - `futuretech_warpgate` needs `futuretech_refinery` ($3,000) for token `futuretech_refinery`
  - `futuretech_refinery` needs `futuretech_constructionyard` ($5,000) for token `futuretech_constructionyard`
  - `futuretech_refinery` needs `futuretech_thermalpowerplant` ($800) for token `futuretech_thermalpowerplant`
  - `futuretech_thermalpowerplant` needs `futuretech_constructionyard` ($5,000) for token `futuretech_constructionyard`
  - `futuretech_harbingergunship` needs `futuretech_hypercore` ($7,500) for token `futuretech_hypercore`
  - `futuretech_hypercore` needs `futuretech_constructionyard` ($5,000) for token `futuretech_constructionyard`
  - `futuretech_hypercore` needs `futuretech_battlelab` ($5,000) for token `futuretech_battlelab`
  - `futuretech_battlelab` needs `futuretech_constructionyard` ($5,000) for token `futuretech_constructionyard`
  - `futuretech_battlelab` needs `futuretech_transmissioncenter` ($2,500) for token `futuretech_transmissioncenter`
  - `futuretech_transmissioncenter` needs `futuretech_constructionyard` ($5,000) for token `futuretech_constructionyard`
  - `futuretech_transmissioncenter` needs `futuretech_robotcontrolcenter` ($2,500) for token `futuretech_robotcontrolcenter`
  - `futuretech_robotcontrolcenter` needs `futuretech_constructionyard` ($5,000) for token `futuretech_constructionyard`
  - `futuretech_robotcontrolcenter` needs `futuretech_warpgate` ($2,000) for token `futuretech_warpgate`
  - `futuretech_warpgate` needs `futuretech_constructionyard` ($5,000) for token `futuretech_constructionyard`
  - `futuretech_warpgate` needs `futuretech_refinery` ($3,000) for token `futuretech_refinery`
  - `futuretech_refinery` needs `futuretech_constructionyard` ($5,000) for token `futuretech_constructionyard`
  - `futuretech_refinery` needs `futuretech_thermalpowerplant` ($800) for token `futuretech_thermalpowerplant`
  - `futuretech_thermalpowerplant` needs `futuretech_constructionyard` ($5,000) for token `futuretech_constructionyard`
  - buildings: futuretech_battlelab, futuretech_constructionyard, futuretech_hypercore, futuretech_launchpad, futuretech_refinery, futuretech_robotcontrolcenter, futuretech_thermalpowerplant, futuretech_transmissioncenter, futuretech_warpgate

#### latinsyndicate_tortugatank
- `latinsyndicate_tortugatank`: `$28,500`
  - file: `mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/vehicles.yaml`
  - prerequisites: latinsyndicate_syndicatefactory, latinsyndicate_recyclingcenter
  - `latinsyndicate_tortugatank` needs `latinsyndicate_syndicatefactory` ($2,000) for token `latinsyndicate_syndicatefactory`
  - `latinsyndicate_syndicatefactory` needs `latinsyndicate_syndicateconstructionyard` ($5,000) for token `latinsyndicate_syndicateconstructionyard`
  - `latinsyndicate_syndicatefactory` needs `latinsyndicate_recyclingrefinery` ($3,000) for token `latinsyndicate_recyclingrefinery`
  - `latinsyndicate_recyclingrefinery` needs `latinsyndicate_syndicateconstructionyard` ($5,000) for token `latinsyndicate_syndicateconstructionyard`
  - `latinsyndicate_recyclingrefinery` needs `latinsyndicate_powerstation` ($1,000) for token `latinsyndicate_powerstation`
  - `latinsyndicate_powerstation` needs `latinsyndicate_syndicateconstructionyard` ($5,000) for token `latinsyndicate_syndicateconstructionyard`
  - `latinsyndicate_tortugatank` needs `latinsyndicate_recyclingcenter` ($5,000) for token `latinsyndicate_recyclingcenter`
  - `latinsyndicate_recyclingcenter` needs `latinsyndicate_syndicateconstructionyard` ($5,000) for token `latinsyndicate_syndicateconstructionyard`
  - `latinsyndicate_recyclingcenter` needs `latinsyndicate_defensebureau` ($5,000) for token `latinsyndicate_defensebureau`
  - `latinsyndicate_defensebureau` needs `latinsyndicate_syndicateconstructionyard` ($5,000) for token `latinsyndicate_syndicateconstructionyard`
  - `latinsyndicate_defensebureau` needs `latinsyndicate_spycenter` ($5,000) for token `latinsyndicate_spycenter`
  - `latinsyndicate_spycenter` needs `latinsyndicate_syndicateconstructionyard` ($5,000) for token `latinsyndicate_syndicateconstructionyard`
  - `latinsyndicate_spycenter` needs `latinsyndicate_latinempradar` ($2,500) for token `latinsyndicate_latinempradar`
  - `latinsyndicate_latinempradar` needs `latinsyndicate_syndicateconstructionyard` ($5,000) for token `latinsyndicate_syndicateconstructionyard`
  - `latinsyndicate_latinempradar` needs `latinsyndicate_recyclingrefinery` ($3,000) for token `latinsyndicate_recyclingrefinery`
  - `latinsyndicate_recyclingrefinery` needs `latinsyndicate_syndicateconstructionyard` ($5,000) for token `latinsyndicate_syndicateconstructionyard`
  - `latinsyndicate_recyclingrefinery` needs `latinsyndicate_powerstation` ($1,000) for token `latinsyndicate_powerstation`
  - `latinsyndicate_powerstation` needs `latinsyndicate_syndicateconstructionyard` ($5,000) for token `latinsyndicate_syndicateconstructionyard`
  - buildings: latinsyndicate_defensebureau, latinsyndicate_latinempradar, latinsyndicate_powerstation, latinsyndicate_recyclingcenter, latinsyndicate_recyclingrefinery, latinsyndicate_spycenter, latinsyndicate_syndicateconstructionyard, latinsyndicate_syndicatefactory

#### ordos_deviatorartillery
- `ordos_deviatorartillery`: `$28,000`
  - file: `mods/cameo/ContentPacks/D2k/Ordos/yaml/vehicles.yaml`
  - prerequisites: ordos_heavy_vehicle_production, ordos_palace
  - `ordos_deviatorartillery` needs `ordos_heavyfactory` ($2,000) for token `ordos_heavy_vehicle_production`
  - `ordos_heavyfactory` needs `ordos_constructionyard` ($5,000) for token `ordos_constructionyard`
  - `ordos_heavyfactory` needs `ordos_refineryordos` ($3,000) for token `ordos_refineryordos`
  - `ordos_refineryordos` needs `ordos_constructionyard` ($5,000) for token `ordos_constructionyard`
  - `ordos_refineryordos` needs `ordos_windtrap` ($500) for token `ordos_windtrap`
  - `ordos_windtrap` needs `ordos_constructionyard` ($5,000) for token `ordos_constructionyard`
  - `ordos_deviatorartillery` needs `ordos_palace` ($10,000) for token `ordos_palace`
  - `ordos_palace` needs `ordos_constructionyard` ($5,000) for token `ordos_constructionyard`
  - `ordos_palace` needs `ordos_ixresearchcenter` ($5,000) for token `ordos_ixresearchcenter`
  - `ordos_ixresearchcenter` needs `ordos_constructionyard` ($5,000) for token `ordos_constructionyard`
  - `ordos_ixresearchcenter` needs `ordos_outpost` ($2,500) for token `ordos_outpost`
  - `ordos_outpost` needs `ordos_constructionyard` ($5,000) for token `ordos_constructionyard`
  - `ordos_outpost` needs `ordos_refineryordos` ($3,000) for token `ordos_refineryordos`
  - `ordos_refineryordos` needs `ordos_constructionyard` ($5,000) for token `ordos_constructionyard`
  - `ordos_refineryordos` needs `ordos_windtrap` ($500) for token `ordos_windtrap`
  - `ordos_windtrap` needs `ordos_constructionyard` ($5,000) for token `ordos_constructionyard`
  - buildings: ordos_constructionyard, ordos_heavyfactory, ordos_ixresearchcenter, ordos_outpost, ordos_palace, ordos_refineryordos, ordos_windtrap

#### yuri_biotrooper
- `yuri_biotrooper`: `$26,600`
  - file: `mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/infantry.yaml`
  - prerequisites: yuri_barracks, yuri_cloningvats
  - `yuri_biotrooper` needs `yuri_barracks` ($1,000) for token `yuri_barracks`
  - `yuri_barracks` needs `yuri_constructionyard` ($5,000) for token `yuri_constructionyard`
  - `yuri_barracks` needs `yuri_bioreactor` ($600) for token `yuri_bioreactor`
  - `yuri_bioreactor` needs `yuri_constructionyard` ($5,000) for token `yuri_constructionyard`
  - `yuri_biotrooper` needs `yuri_cloningvats` ($5,000) for token `yuri_cloningvats`
  - `yuri_cloningvats` needs `yuri_constructionyard` ($5,000) for token `yuri_constructionyard`
  - `yuri_cloningvats` needs `yuri_battlelab` ($5,000) for token `yuri_battlelab`
  - `yuri_battlelab` needs `yuri_constructionyard` ($5,000) for token `yuri_constructionyard`
  - `yuri_battlelab` needs `yuri_psychicsensor` ($2,500) for token `yuri_psychicsensor`
  - `yuri_psychicsensor` needs `yuri_constructionyard` ($5,000) for token `yuri_constructionyard`
  - `yuri_psychicsensor` needs `yuri_slaveminer_deployed` ($2,500) for token `yuri_slaveminer_deployed`
  - `yuri_slaveminer_deployed` needs `yuri_constructionyard` ($5,000) for token `yuri_constructionyard`
  - `yuri_slaveminer_deployed` needs `yuri_bioreactor` ($600) for token `yuri_bioreactor`
  - `yuri_bioreactor` needs `yuri_constructionyard` ($5,000) for token `yuri_constructionyard`
  - `yuri_cloningvats` needs `yuri_lunarcommandcenter` ($5,000) for token `yuri_lunarcommandcenter`
  - `yuri_lunarcommandcenter` needs `yuri_constructionyard` ($5,000) for token `yuri_constructionyard`
  - `yuri_lunarcommandcenter` needs `yuri_battlelab` ($5,000) for token `yuri_battlelab`
  - `yuri_battlelab` needs `yuri_constructionyard` ($5,000) for token `yuri_constructionyard`
  - `yuri_battlelab` needs `yuri_psychicsensor` ($2,500) for token `yuri_psychicsensor`
  - `yuri_psychicsensor` needs `yuri_constructionyard` ($5,000) for token `yuri_constructionyard`
  - `yuri_psychicsensor` needs `yuri_slaveminer_deployed` ($2,500) for token `yuri_slaveminer_deployed`
  - `yuri_slaveminer_deployed` needs `yuri_constructionyard` ($5,000) for token `yuri_constructionyard`
  - `yuri_slaveminer_deployed` needs `yuri_bioreactor` ($600) for token `yuri_bioreactor`
  - `yuri_bioreactor` needs `yuri_constructionyard` ($5,000) for token `yuri_constructionyard`
  - buildings: yuri_barracks, yuri_battlelab, yuri_bioreactor, yuri_cloningvats, yuri_constructionyard, yuri_lunarcommandcenter, yuri_psychicsensor, yuri_slaveminer_deployed

#### wc2_orcs_deathknight
- `wc2_orcs_deathknight`: `$15,000`
  - file: `mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/infantry.yaml`
  - prerequisites: wc2_orcs_templeofthedamned
  - `wc2_orcs_deathknight` needs `wc2_orcs_templeofthedamned` ($10,000) for token `wc2_orcs_templeofthedamned`
  - `wc2_orcs_templeofthedamned` needs `wc2_orcs_greathall` ($5,000) for token `wc2_orcs_greathall`
  - `wc2_orcs_templeofthedamned` needs `wc2_orcs_greathall` ($5,000) for token `wc2_orcs_fortress`
  - buildings: wc2_orcs_greathall, wc2_orcs_templeofthedamned

#### devastator
- `devastator`: `$18,000`
  - file: `mods/cameo/ContentPacks/D2k/Harkonnen/yaml/vehicles.yaml`
  - prerequisites: harkonnen_vehicle_production, heavy.harkonnen, research_centre
  - `devastator` needs `harkonnen_heavyfactory` ($2,000) for token `harkonnen_vehicle_production`
  - `harkonnen_heavyfactory` needs `harkonnen_constructionyard` ($5,000) for token `harkonnen_constructionyard`
  - `harkonnen_heavyfactory` needs `harkonnen_refinery` ($3,000) for token `harkonnen_refinery`
  - `harkonnen_refinery` needs `harkonnen_constructionyard` ($5,000) for token `harkonnen_constructionyard`
  - `harkonnen_refinery` needs `harkonnen_windtrap` ($500) for token `harkonnen_windtrap`
  - `harkonnen_windtrap` needs `harkonnen_constructionyard` ($5,000) for token `harkonnen_constructionyard`
  - `devastator` needs `harkonnen_heavyfactory` ($2,000) for token `heavy.harkonnen`
  - `harkonnen_heavyfactory` needs `harkonnen_constructionyard` ($5,000) for token `harkonnen_constructionyard`
  - `harkonnen_heavyfactory` needs `harkonnen_refinery` ($3,000) for token `harkonnen_refinery`
  - `harkonnen_refinery` needs `harkonnen_constructionyard` ($5,000) for token `harkonnen_constructionyard`
  - `harkonnen_refinery` needs `harkonnen_windtrap` ($500) for token `harkonnen_windtrap`
  - `harkonnen_windtrap` needs `harkonnen_constructionyard` ($5,000) for token `harkonnen_constructionyard`
  - `devastator` needs `harkonnen_ixresearchcenter` ($5,000) for token `research_centre`
  - `harkonnen_ixresearchcenter` needs `harkonnen_constructionyard` ($5,000) for token `harkonnen_constructionyard`
  - `harkonnen_ixresearchcenter` needs `harkonnen_outpost` ($2,500) for token `harkonnen_outpost`
  - `harkonnen_outpost` needs `harkonnen_constructionyard` ($5,000) for token `harkonnen_constructionyard`
  - `harkonnen_outpost` needs `harkonnen_refinery` ($3,000) for token `harkonnen_refinery`
  - `harkonnen_refinery` needs `harkonnen_constructionyard` ($5,000) for token `harkonnen_constructionyard`
  - `harkonnen_refinery` needs `harkonnen_windtrap` ($500) for token `harkonnen_windtrap`
  - `harkonnen_windtrap` needs `harkonnen_constructionyard` ($5,000) for token `harkonnen_constructionyard`
  - buildings: harkonnen_constructionyard, harkonnen_heavyfactory, harkonnen_ixresearchcenter, harkonnen_outpost, harkonnen_refinery, harkonnen_windtrap


### Per-faction maxima

| faction | buildable units | median chain | max chain | max unit(s) |
|---|---|---:|---:|---|
| D2k/Atreides | 2 | 10,500 | 10,500 | `atreides_mobileconstructionvehicle`, `combat_tank.atreides` |
| D2k/Harkonnen | 4 | 18,000 | 18,000 | `devastator`, `missile_tank` |
| D2k/Ixian | 35 | 13,000 | 18,000 | `duelist_tank.ixian`, `ixian_ixmissiletank`, `ixian_ixprojector` |
| D2k/Ordos | 44 | 12,500 | 28,000 | `ordos_deviatorartillery`, `ordos_deviatortank` |
| D2k/Shared | 17 | 0 | 0 | `carryall`, `carryall.paradrop`, `carryall.reinforce` |
| RedAlert/Allies | 34 | 12,500 | 18,000 | `ra1_allies_chronotank`, `ra1_allies_mobilegapgenerator`, `ra1_allies_mobileradarjammer` |
| RedAlert/Japan | 43 | 14,250 | 18,250 | `japan_ballista`, `japan_exorcistoitank`, `japan_oitank` |
| RedAlert/Shared | 16 | 800 | 3,000 | `japan_japanesecarrier`, `japan_japanesespeedboat`, `japan_yamatobattleship` |
| RedAlert/Soviets | 79 | 12,500 | 18,000 | `ra1_soviets_grad`, `ra1_soviets_madtank`, `ra1_soviets_mammothtank` |
| RedAlert2/Allies | 48 | 15,800 | 20,800 | `ra2_allies_upgrade_chronoengine` |
| RedAlert2/Shared | 42 | 0 | 3,000 | `ra2carrier`, `ra2dest`, `ra2dlph` |
| RedAlert2/Soviets | 38 | 10,600 | 30,100 | `ra2_soviets_upgrade_kirovatomicbombs` |
| RedAlert2/Yuri | 48 | 15,600 | 26,600 | `yuri_biotrooper` |
| RedAlert2Mod/AsianAlliance | 53 | 12,750 | 24,250 | `tsun.asian`, `up_tsunami.asian` |
| RedAlert2Mod/Consortium | 41 | 13,500 | 25,500 | `steelconsortium_cloudbreaker` |
| RedAlert2Mod/FutureTech | 33 | 16,800 | 29,800 | `futuretech_harbingergunship` |
| RedAlert2Mod/Naxis | 57 | 13,300 | 20,300 | `muboat.nax`, `nax_bitsmark` |
| RedAlert2Mod/SchwarzerMond | 35 | 14,300 | 19,300 | `schwarzermond_blackbomb`, `schwarzermond_corruptorpiercer`, `schwarzermond_dieglocke` |
| RedAlert2Mod/Syndicate | 42 | 13,000 | 28,500 | `latinsyndicate_tortugatank` |
| RedAlert2Mod/TKM | 51 | 12,900 | 19,900 | `tkm_viper` |
| StarCraft/Protoss | 43 | 9,000 | 19,000 | `protoss_carrier`, `protoss_starshipsovereign`, `protoss_upgrade_airarmorlevel2` |
| StarCraft/Terran | 49 | 10,500 | 14,500 | `terran_battlecruiser`, `terran_ghost`, `terran_jimraynor` |
| StarCraft/Zerg | 41 | 6,500 | 12,000 | `zerg_infestedterranbomber` |
| TiberianDawn/GDI | 45 | 11,500 | 24,000 | `gdicarrier` |
| TiberianDawn/Nod | 43 | 12,500 | 27,500 | `td_nod_chemicalssmlauncher`, `td_nod_venom` |
| TiberianDawn/Shared | 1 | 0 | 0 | `E6` |
| TiberianSun/CABAL | 62 | 6,800 | 22,800 | `cabal_coredefender`, `cabal_widow` |
| TiberianSun/Forgotten | 56 | 7,400 | 12,600 | `forgotten_chemicalmammothtank`, `forgotten_experimentalmammothtank`, `forgotten_flametank` |
| TiberianSun/GDI | 39 | 8,000 | 23,000 | `ts_gdi_kodiakcommandship` |
| TiberianSun/Nod | 30 | 8,900 | 16,600 | `ts_nod_mobilestealthgenerator` |
| Warcraft2/Humans | 48 | 9,700 | 19,700 | `wc2_humans_upgrade_blizzard`, `wc2_humans_upgrade_polymorph`, `wc2_humans_upgrade_slow` |
| Warcraft2/Orcs | 40 | 9,500 | 19,500 | `wc2_orcs_upgrade_deathanddecay`, `wc2_orcs_upgrade_haste`, `wc2_orcs_upgrade_raisedead` |
| other | 72 | 10,750 | 18,200 | `wc2_human_battleship` |

### Observations

- The TD Nod Laser Trooper chain is **$27,000**, not $32,000. The $5,000 inflation was a cross-faction GDI Construction Yard that the corrected resolver removes.
- The RA2 Soviets `kirovatomicbombs` promotion upgrade has the highest corrected chain at **$30,100**, driven by the Industrial Plant, Nuclear Missile Silo, Battle Lab, and Radar.
- FutureTech top units cluster around **$28,300–$29,800** and depend on the Warp Gate, Transmission Center, Battle Lab, and Robot Control Center.
- The T3 tech-center bucket contains exactly one unit, `wc2_orcs_deathknight`, with a real $15,000 chain (Great Hall $5,000 + Temple of the Damned $10,000).
- T2 radar now lands at ~0.80, not the old fixed-ladder 1.0, confirming radar is a real tier.
- The rational form and the power law still agree within ~0.02 at every measured tier; the rational form is simpler to explain and calibrate.

### Implementation

The resolver now lives in `tools/balance/tier_chain.py`:

- `TierChain(model)` builds a provider index over resolved `Building` actors that have `Valued.Cost`.
- Building-plug addons (`Plug:` trait) are not counted as separate actor-name providers; their tokens are provided by the host building, so chain costs do not double-count upgrades such as the Warcraft 2 Fortress plug.
- Provider search is restricted to the actor's own ContentPack leaf plus the same game's `Shared` pack, preventing the Nod/GDI cross-factor bug.
- Recursive prerequisite closure deduplicates buildings and breaks cycles.
- `TierChain.chain_cost(actor)` returns `C`, the total cost of the unique building chain.
- `tier_chain.tier_multiplier(C)` implements `f(C) = 1 / (1 + (C - B) / S)` with `B = 9500`, `S = 8250`, clamped to `[0, 1]` and returning `1.0` for `C <= B`.
- `tier_chain.effective_tier(design, derived, default=1.0)` preserves manually authored `design.tech_tier` values as overrides; the computed `tier_multiplier` from the derived sidecar is the fallback.

`tools/balance/extract_stats.py` now computes `tier_chain_cost` and `tier_multiplier` for every buildable actor and stores them in the derived sidecar (`docs/balance/derived/*.json`). The raw ledger's `design.tech_tier` is never overwritten, so maintainer overrides remain intact.

Consumers updated to the new semantics:

- `fit_class.py` — reads `design.tech_tier` first, then the derived `tier_multiplier`, for absolute tier in `estimators()`.
- `propose_class_rebalance.py` — class-baseline prices now use the relative multiplier `f(C)/f(C_anchor)`. Manual anchor `design.tech_tier` is used as the denominator when present, otherwise the computed anchor multiplier is used.
- `build_workbook.py` — the `TechTier` workbook column shows the absolute multiplier; the class-baseline `Price` and `RangeSolve` formulas divide by the anchor's absolute tier.
- `check_band.py` — band validator uses the relative tier for `class_baseline_price` and absolute tier for `class_anchor_price`.
- `formula.py` — documents the difference between absolute (`estimators`/`class_anchor_price`) and relative (`class_baseline_price`) usage and exposes `formula.tier_multiplier` with the canonical `B` and `S` constants.

Verified: `td_nod_lasertrooper` resolves to `C = $27,000` and `f(C) = 0.3204` with no GDI buildings in its closure. `wc2_orcs_deathknight` resolves to `C = $15,000` (Great Hall + Temple of the Damned) and `devastator` to `C = $18,000`.

### Recommendation

Adopt the rational form `f(C) = 1 / (1 + (C - B) / S)` with B = T1 median chain and S = (T4 median chain - B). Use the corrected medians above for the next `tier` term calibration.
