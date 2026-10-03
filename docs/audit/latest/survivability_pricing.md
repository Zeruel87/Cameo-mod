# audit_survivability_pricing — E1: the baseline shield is priced at ZERO

| bucket | actors | priced today | belongs to |
|---|--:|---|---|
| spawns with a pool (**always-on**) | 56 | ✖ nothing | **E1 — this report** |
| empty capacity, needs `shieldgen` | 1335 | ✔ correctly nothing | — (it has no shield) |
| pool behind an upgrade | 215 | ✖ nothing | E5 (upgrade pricing) |

Shield row mean Versus **184.71**, so one shield point is **0.5414 HP** BEFORE any shield-gated `DamageMultiplier` — measured off the live ladder every run, never frozen. The Shield row takes **1.603%** of all roster raw damage at baseline.

⚠ **Every one of these 56 actors also carries `DamageMultiplier@shielded: 150`**, so it takes 150% damage WHILE the shield holds — the deliberate counterweight to having one. That divides the pool's worth: a shield point is really **0.3609 HP**, and the roster-wide gap is 38.6% rather than the 57.8% a shield-only reading gives. `shield_damage_multiplier` and `shield_hp_per_point` are published per actor.

## The gap

* Raw HP across these 56 actors: **12,812,500**
* Effective HP once the pool is counted: **20,245,767** (**+58.0%**)
* Implied price change if the formula read effective HP: median **×1.377**, max **×1.752**

⚠ **Retiring the 150% multiplier is a BUFF that must be paid for.** The numbers above already account for it, so they price the game AS IT IS. Delete `DamageMultiplier@shielded` and a shield point jumps from 0.361 to 0.541 HP — the same pool becomes 1.5x more valuable and the implied price rises again. Re-extract AFTER the deletion and price once, or these units get charged for durability they no longer have (or keep durability they were never charged for).

## Per actor

| pack | actor | HP | shield pool | effective HP | ×HP | cost | implied ×price |
|---|---|--:|--:|--:|--:|--:|--:|
| redalert2mod_consortium | `steelconsortium_defenderbot` | 210,000 | 420,000 | 437,383 | ×2.083 | 3,200 | ×1.752 |
| redalert2mod_consortium | `steelconsortium_skyhammer` | 120,000 | 240,000 | 249,933 | ×2.083 | 4,500 | ×1.745 |
| redalert2mod_consortium | `steelconsortium_katytank` | 275,000 | 550,000 | 572,764 | ×2.083 | 3,800 | ×1.711 |
| redalert2mod_consortium | `steelconsortium_stalker` | 140,000 | 280,000 | 291,589 | ×2.083 | 4,000 | ×1.693 |
| redalert2mod_consortium | `steelconsortium_whiterabbit` | 150,000 | 300,000 | 312,417 | ×2.083 | 4,500 | ×1.570 |
| starcraft_protoss | `protoss_arbitertribunal` | 250,000 | 250,000 | 385,347 | ×1.541 | 2,500 | ×1.541 |
| starcraft_protoss | `protoss_observatory` | 250,000 | 250,000 | 385,347 | ×1.541 | 2,500 | ×1.541 |
| starcraft_protoss | `protoss_pylon` | 250,000 | 250,000 | 385,347 | ×1.541 | 1,000 | ×1.541 |
| starcraft_protoss | `protoss_templararchives` | 250,000 | 250,000 | 385,347 | ×1.541 | 2,500 | ×1.541 |
| starcraft_protoss | `protoss_roboticsfacility` | 400,000 | 400,000 | 616,556 | ×1.541 | 2,000 | ×1.541 |
| starcraft_protoss | `protoss_fleetbeacon` | 1,000,000 | 1,000,000 | 1,541,389 | ×1.541 | 10,000 | ×1.541 |
| starcraft_protoss | `protoss_nexus` | 1,000,000 | 1,000,000 | 1,541,389 | ×1.541 | 5,000 | ×1.541 |
| starcraft_protoss | `protoss_assimilator` | 300,000 | 300,000 | 462,417 | ×1.541 | 3,000 | ×1.541 |
| starcraft_protoss | `protoss_cyberneticscore` | 150,000 | 150,000 | 231,208 | ×1.541 | 1,500 | ×1.541 |
| starcraft_protoss | `protoss_forge` | 150,000 | 150,000 | 231,208 | ×1.541 | 1,500 | ×1.541 |
| starcraft_protoss | `protoss_stargate` | 300,000 | 300,000 | 462,417 | ×1.541 | 1,500 | ×1.541 |
| starcraft_protoss | `protoss_citadelofadun` | 200,000 | 200,000 | 308,278 | ×1.541 | 2,000 | ×1.541 |
| starcraft_protoss | `protoss_gateway` | 200,000 | 200,000 | 308,278 | ×1.541 | 1,000 | ×1.541 |
| starcraft_protoss | `protoss_roboticssupportbay` | 200,000 | 200,000 | 308,278 | ×1.541 | 2,000 | ×1.541 |
| starcraft_protoss | `protoss_mobilenexus` | 300,000 | 300,000 | 462,417 | ×1.541 | 5,000 | ×1.492 |
| redalert2mod_consortium | `steel_cruiser_f` | 37,500 | 75,000 | 78,104 | ×2.083 | 125 | ×1.453 |
| starcraft_protoss | `protoss_starshipsovereign` | 750,000 | 750,000 | 1,156,042 | ×1.541 | 10,000 | ×1.447 |
| redalert2mod_consortium | `steelconsortium_supportshieldgenerator` | 100,000 | 200,000 | 208,278 | ×2.083 | 3,000 | ×1.433 |
| redalert2mod_consortium | `steelconsortium_empressstation` | 1,500,000 | 1,500,000 | 2,312,083 | ×1.541 | 5,000 | ×1.428 |
| starcraft_protoss | `protoss_archon` | 350,000 | 350,000 | 539,486 | ×1.541 | 5,600 | ×1.408 |
| starcraft_protoss | `protoss_epigraph` | 200,000 | 200,000 | 308,278 | ×1.541 | 2,600 | ×1.395 |
| starcraft_protoss | `protoss_shuttle` | 100,000 | 100,000 | 154,139 | ×1.541 | 6,000 | ×1.394 |
| starcraft_protoss | `protoss_carrier` | 300,000 | 300,000 | 462,417 | ×1.541 | 3,000 | ×1.379 |
| starcraft_protoss | `protoss_idol` | 350,000 | 350,000 | 539,486 | ×1.541 | 2,800 | ×1.375 |
| starcraft_protoss | `protoss_arbiter` | 225,000 | 225,000 | 346,812 | ×1.541 | 4,800 | ×1.371 |
| starcraft_protoss | `protoss_atreus` | 250,000 | 250,000 | 385,347 | ×1.541 | 2,400 | ×1.365 |
| starcraft_protoss | `protoss_zeratul` | 250,000 | 250,000 | 385,347 | ×1.541 | 4,000 | ×1.364 |
| starcraft_protoss | `protoss_corsair` | 125,000 | 125,000 | 192,674 | ×1.541 | 2,100 | ×1.359 |
| redalert2mod_consortium | `steelconsortium_cloudbreaker` | 250,000 | 250,000 | 385,347 | ×1.541 | 5,000 | ×1.356 |
| starcraft_protoss | `protoss_reaver` | 275,000 | 275,000 | 423,882 | ×1.541 | 2,700 | ×1.344 |
| redalert2mod_consortium | `steel_cougar` | 25,000 | 50,000 | 52,069 | ×2.083 | 1,200 | ×1.316 |
| starcraft_protoss | `protoss_voidray` | 70,000 | 70,000 | 107,897 | ×1.541 | 1,400 | ×1.315 |
| starcraft_protoss | `protoss_scout` | 75,000 | 75,000 | 115,604 | ×1.541 | 1,500 | ×1.314 |
| redalert2mod_consortium | `steel_hummer` | 45,000 | 67,500 | 81,544 | ×1.812 | 2,000 | ×1.313 |
| redalert2mod_consortium | `steel_oldqtnk` | 112,500 | 112,500 | 173,406 | ×1.541 | 2,400 | ×1.309 |
| starcraft_protoss | `protoss_shieldbattery` | 100,000 | 100,000 | 154,139 | ×1.541 | 1,000 | ×1.271 |
| starcraft_protoss | `protoss_positron` | 60,000 | 60,000 | 92,483 | ×1.541 | 1,200 | ×1.262 |
| starcraft_protoss | `protoss_dragoon` | 75,000 | 75,000 | 115,604 | ×1.541 | 1,200 | ×1.243 |
| starcraft_protoss | `protoss_gladius` | 100,000 | 100,000 | 154,139 | ×1.541 | 1,800 | ×1.241 |
| starcraft_protoss | `protoss_patriarch` | 75,000 | 75,000 | 115,604 | ×1.541 | 4,000 | ×1.237 |
| redalert2mod_consortium | `steel_cobra` | 325,000 | 162,500 | 412,976 | ×1.271 | 3,600 | ×1.200 |
| starcraft_protoss | `protoss_probe` | 45,000 | 45,000 | 69,362 | ×1.541 | 500 | ×1.189 |
| starcraft_protoss | `protoss_analogue` | 60,000 | 60,000 | 92,483 | ×1.541 | 1,200 | ×1.188 |
| starcraft_protoss | `protoss_amaranth` | 70,000 | 70,000 | 107,897 | ×1.541 | 1,200 | ×1.180 |
| starcraft_protoss | `protoss_observer` | 12,500 | 12,500 | 19,267 | ×1.541 | 500 | ×1.170 |
| starcraft_protoss | `protoss_darktemplar` | 50,000 | 50,000 | 77,069 | ×1.541 | 600 | ×1.161 |
| starcraft_protoss | `protoss_zealot` | 40,000 | 40,000 | 61,656 | ×1.541 | 300 | ×1.146 |
| starcraft_protoss | `protoss_legionnaire` | 60,000 | 60,000 | 92,483 | ×1.541 | 700 | ×1.142 |
| starcraft_protoss | `protoss_adept` | 30,000 | 30,000 | 46,242 | ×1.541 | 650 | ×1.130 |
| starcraft_protoss | `protoss_manifold` | 25,000 | 25,000 | 38,535 | ×1.541 | 600 | ×1.119 |
| starcraft_protoss | `protoss_photoncannon` | 200,000 | 200,000 | 308,278 | ×1.541 | 2,000 | ×1.014 |
