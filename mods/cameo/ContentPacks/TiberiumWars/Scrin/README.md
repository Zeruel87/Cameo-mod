# Scrin content pack

This content pack now provides an initial playable Scrin faction foundation,
covering its approved structures, defenses, Eradicator Hexapod, and initial
infantry, vehicle, and aircraft rosters. The faction is selectable in the lobby,
starts from a Drone Ship, and follows the production graph documented below.
The Drone Ship lands and
transforms into the Drone Platform, which plays its genuine deployment cycle.

The pack contains 51 approved map/editor-ready actors. All sheets pair their
body art with separate, model-derived ground shadows. The structures use
Cameo's dynamic `player_rgba` palette. Reactor and Signal Transmitter remain
static; Extractor, Growth Accelerator, and Storm Column have 16-frame idle
cycles. Photon Cannon and Plasma Missile Battery use 32 embedded turret
facings. Drone Platform uses a
45-frame, 1.8-second make sequence whose final frame is also its exact idle
frame. Combined with the Drone Ship's tuned landing rate, deployment takes
approximately three seconds.

Portal, Warp Gate, and Warp Chasm cores use RGBA animation sheets so their
authored soft transparency survives the runtime sprite loader. Alternate linked
portal colors remain deferred until the gameplay mode is implemented.

The Reaper-17 Growth Stimulator uses its distinct Growth Accelerator-derived
body with four Tiberium extraction pods. The Global Conquest Lifeform Recycling
Plant and Terraforming Nexus are included as map/editor actors; their strategic
operations remain outside the current faction foundation.

## Current gameplay pilot

Reactor is available from Drone Platform as the first production test. It uses
the authentic 56-frame CNC3 `ObjectsAlienBuildup` expanding-hole dissolve with
its structure-shaped aurora on a separately synchronized overlay. Stock
building sale behavior plays both layers in exact reverse. The independent
fade-white/bottom-to-top materialization prototype remains available as a
faction-neutral effect for future structures, but Reactor no longer uses it.

All Scrin structures inherit the standard base-building placement, repair,
capture, and sale lifecycle. Their shared placement sound is the authentic
Tiberium Wars `ALI_Building_Placed` asset (`ABBuild_placea`). The complete
initial structure roster now uses this lifecycle. Production, combat, economy,
and upgrade values are a playable baseline; final balance remains deferred until
the combined in-game review.

The earlier Tiberium-creep visual pilot was rejected and is deliberately not
part of this checkpoint. A replacement ground-field concept remains deferred
until it has a stronger visual direction.

## Production graph

- Drone Platform initially constructs Reactor and Extractor.
- Reactor unlocks Portal.
- Reactor plus Extractor unlock Warp Gate, Nerve Center, and Gravity Stabilizer.
- Nerve Center unlocks Technology Assembler and Foundry.
- Portal plus Nerve Center unlock Stasis Chamber.
- Technology Assembler unlocks Warp Chasm, Signal Transmitter, Control Node,
  and Phase Generator.
- Portal trains all Scrin infantry.
- Warp Gate produces all Scrin vehicles except Eradicator Hexapod.
- Warp Chasm produces all Scrin vehicles including Eradicator Hexapod, plus
  Devastator Warship, Planetary Assault Carrier, Mothership, and the remaining
  Scrin aircraft roster.
- Gravity Stabilizer produces Stormriders and Drone Ships.

The Extractor deploys a free Harvester, all standard producers have explicit
unit exits and rally points, and the Foundry provides an additional construction
queue. Nerve Center researches Fusion Reactor: existing Reactors immediately
transform while newly constructed power plants use the Fusion Reactor actor.

The Eradicator Hexapod uses the approved AIDA frame 65 static pose and the
corrected WLKA cycle sampled to 12 frames across 32 facings. Its indexed source
frames are stored at half resolution and displayed at 2x scale, preserving the
approved physical size with a more native OpenRA pixel density. Its embedded
palette reserves indices 249-255 for `scrin_hexapod_player` remapping.

The initial infantry roster contains the Disintegrator, Assimilator, Shock
Trooper, Blink Pack Shock Trooper, Ravager, Mastermind, and Prodigy. Each uses
the approved held idle pose and 12-frame walk cycle across 8 facings. Their
indexed idle and movement sheets share a per-unit embedded palette, with indices
249-255 reserved for player-color remapping. Cultist is deliberately excluded;
Buzzer remains deferred to a later simplified FX-style representation.

The initial vehicle roster contains the Explorer, Harvester, Seeker, Devourer
Tank, Repair Drone, Gun Walker, Shard Walker, Corrupter, Annihilator Tripod, and
Reaper Tripod. Hover vehicles remain static except for the Repair Drone. The
walkers use approved native movement cycles across 32 facings; Gun Walker has
softened leg-joint skinning to preserve its silhouette at OpenRA resolution.
Each indexed sheet reserves indices 249-255 for player-color remapping. Every
mobile-unit facing is locked to an authored body/rig pivot, with the same
per-facing correction applied to its complete body and native shadow group.
This prevents asymmetric hulls, barrels, tentacles, and lifted legs from making
the model orbit its cell while turning without suppressing real walk motion.

The initial aircraft roster contains the Drone Ship, Stormrider, Devastator
Warship, Planetary Assault Carrier, Invader Fighter, and Mothership. Their
approved 32-facing spacecraft renders use fixed authored pivots, native ground
shadows, and bright player-color ramps. The PAC idle visual carries its full
complement of eight docked Invader Fighters. The initial gameplay layer spawns,
launches, repairs, replenishes, and recovers the same eight Invader Fighter
actors through the shared carrier system.

The actors now expose initial production roles, costs, health, weapons, power,
prerequisites, construction and reverse-sale behavior, economy flow, engineer
capture/repair, Repair Drone support, carrier fighters, and the Fusion Reactor
upgrade. Canonical special abilities, destruction art, AI tuning, and competitive
balance remain later work. The reviewed footprints and visual pivots remain
unchanged by this gameplay pass.

The sprites were independently extracted and rendered from the official
*Command & Conquer 3: Tiberium Wars* and *Kane's Wrath* assets. The source
models and textures are copyright Electronic Arts and remain the property of
their respective owner.

The small Scrin projectile, impact, and matching weapon-audio assets are
adapted from the GPLv3 [Combined Arms project](https://github.com/Inq8/CAmod).
They are kept namespaced inside this content pack; no Combined Arms unit or
building art is included.
