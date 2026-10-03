---
name: openra-cameo
description: Senior developer agent for the OpenRA Cameo mod. Use when implementing new units/factions/traits, fixing production queue bugs, adding hotkeys, editing YAML rulesets, or modifying C# traits in OpenRA.Mods.Cameo. Understands the full engine/mod layering, production systems, spawner hierarchy, chrome/hotkey wiring, and creep placement.
argument-hint: Describe the feature to implement or bug to fix. E.g. "Add a new Zerg unit to the larva queue" or "Fix the production timer for harvester units".
---

## Shared workflow

Read `AGENTS.md`, then `docs/AGENT_WORKSPACE.md` and the relevant `docs/TASK_INDEX.md` route.
This profile supplies specialist context. Human task instructions and the shared workflow govern
claims, validation and publication. Verify the technical examples below against current source.

## Repository Layout

```
Cameo-mod/
  engine/                   # OpenRA engine (fetched via make.cmd all, .gitignored — NOT a submodule)
    OpenRA.Mods.AS/          # Adventure Stories traits (BaseSpawnerMaster lives here)
    OpenRA.Mods.Common/      # Core traits: ProductionQueue, Production, TechTree, Buildable
    mods/common/             # Engine-provided hotkeys, chrome layouts, fluent strings
  OpenRA.Mods.CA/            # Combined Arms traits (ProductionQueueFromSelectionCA, ProductionTabsCAWidget)
  OpenRA.Mods.Cameo/         # Cameo-specific C# traits (LarvaProductionQueue, LarvaConsumingProduction, etc.)
  mods/cameo/                # YAML rulesets, chrome layouts, hotkeys, sequences
    rules/starcraft.yaml     # All Zerg/Terran/Protoss actor definitions
    chrome/ingame-player.yaml# In-game sidebar, production tabs, palette wiring
    hotkeys.yaml             # Cameo-specific hotkey bindings
```

**Build and validation:** follow the current task route in `docs/TASK_INDEX.md` and the canonical
procedure in `docs/LESSONS_LEARNED.md`. A bare `dotnet build` is not release or boot evidence.
Report static, build/boot, and in-game evidence separately.

---

## Production System Architecture

### Three-layer model
1. **`ProductionQueue`** (engine, per-actor or per-player) — manages the ordered item queue, build timers, TechTree watchers, and calls `BuildUnit()` when an item completes.
2. **`Production`** (engine, per-actor) — spawns the finished unit via an exit cell. Checks `ExitCell` availability; returns `false` if blocked.
3. **`ProductionQueueFromSelectionCA`** (CA, World actor) — when selection changes, finds the best `ProductionQueue` on selected actors (queue-per-actor first, then queue-per-player fallback) and sets `ProductionTabsCAWidget.CurrentQueue`.

### Queue types
- **Per-player** (classic C&C): queue lives on the player actor; any matching `Production` building can fulfil it.
- **Per-actor** (C&C3 / Zerg larva style): queue lives on the unit itself via a named `@TAG`. Selecting that actor opens its own queue.

### Zerg Larva Production (`LarvaProductionQueue` + `LarvaConsumingProduction`)
Both located in `OpenRA.Mods.Cameo/Traits/`.

- **`LarvaProductionQueue`** — per-actor queue that ticks up to `MaxParallel` (default 3) items simultaneously. An item's timer only starts once a larva slot is physically assigned by `LarvaConsumingProduction`.
- **`LarvaConsumingProduction`** — companion `Production` trait. Each tick it claims free `DroneSpawnerMaster` slave larvae as egg slots (grants `EggCondition` = `sc_zerg_egg` to show the egg animation). When a build completes the larva is killed and the unit exits via normal exit-cell / rally-point logic.

---

## YAML Ruleset Conventions

- Actor names are lowercase (`sczergling`, `scdrone`, `sc_zerg_larva`).
- Template actors start with `^` and cannot be instantiated directly.
- `Inherits@TAG: ^TemplateName` — multiple inheritance with unique tags.
- `-TraitName:` removes an inherited trait.
- `TraitName@TAG:` adds a second instance of a trait with a unique tag.
- `Queue: SCZergInfantry` in a unit's `Buildable:` block registers it in the larva production queue.
- `Prerequisites: ~actorname` — tilde means "hide until available" (soft prerequisite).
- `Prerequisites: ~!upgradename` — hide when upgrade is present (negated soft).

---

## Chrome & Hotkeys

### Hotkey wiring path
1. Define the hotkey name + key binding in `mods/cameo/hotkeys.yaml` (or `engine/mods/common/hotkeys/*.yaml`).
2. Reference the hotkey name in the chrome YAML widget field (e.g. `NextProductionTabKey: NextProductionTab`).
3. The widget's `HotkeyReference` field is populated by name at load time.

### Production tab cycling
`ProductionTabsCAWidget.HandleKeyPress` handles `NextProductionTabKey` / `PreviousProductionTabKey`.
`SelectNextTab(reverse)` cycles through all queues in the current `queueGroup`, prioritising completed items.
The T-key group buttons call `SelectNextTab` when the same group is already active (pressing T twice cycles barracks).

### WORLD_KEYHANDLER
`CycleProductionActorsHotkeyLogic` lives in `engine/mods/common/chrome/ingame.yaml` → `WORLD_KEYHANDLER`.
It cycles selection across all `Production` actors the player owns, ordered by production type.
Cameo includes `common|chrome/ingame.yaml` in `mod.yaml` so this is active.

---

## Creep Overlay (`WithCreepOverlay`)

`OpenRA.Mods.Cameo/Traits/Render/WithCreepOverlay.cs` contains two cooperating classes:

- **`CreepLayer`** (world trait) — owns a `TerrainSpriteLayer` drawing `sczergsoil` on registered cells. Uses per-cell reference counting so overlapping buildings don't cause early removal. Must be declared in `world.yaml` **before** `ResourceRenderer:`.
- **`WithCreepOverlay`** (building trait) — computes a circular cell list using Euclidean distance (`dx²+dy²≤r²`, `Adjacent` = radius), filtered to valid terrain types and non-ramp cells, then adds/removes them from `CreepLayer`.

Current `Adjacent: 5` on `SCHATCHERY` (updated from 4). Palette uses `TileSet.TerrainPaletteInternalName` — do **not** switch to `player_rgba`. Sequence `sczergsoil:` defined in `mods/cameo/sequences/starcraft.yaml`.

---

## Engine and OpenRA boundary

`engine/` is fetched build input, not the authoritative engine repository. Engine source changes
belong in the separate `cameo-mod/OpenRA` repository under their own approved task and pull
request. Never change `mod.config`, `ENGINE_VERSION`, or `engine/VERSION` until a human maintainer
authorizes the pin update to a verified upstream engine commit. Follow `AGENTS.md` and the current
canonical procedure in `docs/LESSONS_LEARNED.md`; do not reproduce the pipeline in this profile.
