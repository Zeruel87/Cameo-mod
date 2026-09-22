# Content-pack loading: dependency audit and implementation approach

Moving files into faction folders does not yet let Cameo load only selected factions. The current engine constructs globally cached default rules from the manifest, and match rules reuse those defaults. Selective loading needs both a dependency boundary and a match-specific rules context.

## Source evidence

- `engine/OpenRA.Game/ModData.cs`: the lazy default rules call `Ruleset.LoadDefaults`; `GetRulesYaml` reads manifest rules. `PrepareMap` initializes loaders and loads sequence sprites.
- `engine/OpenRA.Game/GameRules/Ruleset.cs`: `LoadDefaults` consumes the manifest, while `LoadDefaultsForTileSet` and `Load` reuse `modData.DefaultRules`.
- `engine/OpenRA.Game/Map/Map.cs`: `PostInit` loads map rules and then constructs the sequence set. Failed map-rule loading can fall back to default rules.
- Manifest includes expand before rules are constructed. A folder move alone does not change any of these selection points.

The read-only `tools/audit/content_pack_dependencies.py` inventories active explicit inheritance and recognized weapon references. The September 10 candidate has 319 rules files, 40 weapon files, 47 sequence files, 4133 actor definitions and 2969 weapon definitions. It finds 10907 cross-owner actor inheritance edges, 926 actor-to-weapon references, 4605 weapon inheritance edges and 63 weapon-to-weapon references.

The coarse closure starting with `TiberianDawn/GDI` and `global/shared` reaches 29 owners. This is deliberately conservative: ownership of a shared template does not mean that its entire faction must load. For example, shared TD engineer definitions inherit GDI sensors and Nod upgrade templates; GDI skyshield depends on a building-experience template owned by Japan. Whole-folder dependency closure therefore retains much of the unwanted content.

## Proposed first implementation slice

1. Keep a small always-loaded lobby catalog for faction names, icons, map metadata and selection. Identify its rules and asset dependencies explicitly.
2. Extract cross-faction templates into stable shared modules, starting with the TD pilot's sensors, engineer upgrades and building experience. Preserve current include order and resolved values during this structural change.
3. Define a selected-match content context from chosen factions, map requirements and their shared dependencies. Random factions, bots, neutral actors and scripted reinforcements must participate before the match begins.
4. Construct rules, weapons and sequences from that context before sprite loading. Cache by an ordered content identity; include that identity in multiplayer compatibility checks and saved-game/replay reconstruction.
5. Keep the existing full-content route as the initial fallback. Compare resolved selected-faction rules against it, then measure memory and load time with the same map and participants.

This is a design proposal, not a live loader change. A broad engine rewrite is premature until the pilot identifies the required shared modules and lobby assets. Faction-local AI data can follow the same packaging boundary, but AI ownership alone does not close dynamic actor dependencies.

## Inventory limits

The tool is not a runtime dependency certificate. It does not yet resolve actor creation from arbitrary trait fields, Lua scripts, map-local definitions, conditional asset names, sound packages or dynamically selected build/production paths. The 29-owner result diagnoses coarse coupling; it is not a minimal loading plan or a memory-savings estimate.

Reproduce the conservative pilot inventory with:

```powershell
python tools/audit/content_pack_dependencies.py --seed TiberianDawn/GDI --seed global/shared --output content-pack-dependency-inventory.json
```
