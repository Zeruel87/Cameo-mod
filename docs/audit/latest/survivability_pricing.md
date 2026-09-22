# audit_survivability_pricing — E1: the baseline shield is priced at ZERO

| bucket | actors | priced today | belongs to |
|---|--:|---|---|
| spawns with a pool (**always-on**) | 56 | ✖ nothing | **E1 — this report** |
| empty capacity, needs `shieldgen` | 1227 | ✔ correctly nothing | — (it has no shield) |
| pool behind an upgrade | 231 | ✖ nothing | E5 (upgrade pricing) |

Shield row mean Versus **177.11**, so one shield point is **0.5646 HP** BEFORE any shield-gated `DamageMultiplier` — measured off the live ladder every run, never frozen. The Shield row takes **1.486%** of all roster raw damage at baseline.

⚠ **Every one of these 56 actors also carries `DamageMultiplier@shielded: 150`**, so it takes 150% damage WHILE the shield holds — the deliberate counterweight to having one. That divides the pool's worth: a shield point is really **0.3764 HP**, and the roster-wide gap is 38.6% rather than the 57.8% a shield-only reading gives. `shield_damage_multiplier` and `shield_hp_per_point` are published per actor.

## The gap

* Raw HP across these 56 actors: **12,812,500**
* Effective HP once the pool is counted: **20,564,875** (**+60.5%**)
* Implied price change if the formula read effective HP: median **×1.393**, max **×1.785**

⚠ **Retiring the 150% multiplier is a BUFF that must be paid for.** The numbers above already account for it, so they price the game AS IT IS. Delete `DamageMultiplier@shielded` and a shield point jumps from 0.376 to 0.565 HP — the same pool becomes 1.5x more valuable and the implied price rises again. Re-extract AFTER the deletion and price once, or these units get charged for durability they no longer have (or keep durability they were never charged for).

## Per actor

| pack | actor | HP | shield pool | effective HP | ×HP | cost | implied ×price |
|---|---|--:|--:|--:|--:|--:|--:|
| redalert2mod_consortium | `steelconsortium_defenderbot` | 210,000 | 420,000 | 447,145 | ×2.129 | 3,200 | ×1.785 |
| redalert2mod_consortium | `steelconsortium_skyhammer` | 120,000 | 240,000 | 255,511 | ×2.129 | 4,500 | ×1.777 |
| redalert2mod_consortium | `steelconsortium_katytank` | 275,000 | 550,000 | 585,547 | ×2.129 | 3,800 | ×1.741 |
| redalert2mod_consortium | `steelconsortium_stalker` | 140,000 | 280,000 | 298,096 | ×2.129 | 4,000 | ×1.723 |
| redalert2mod_consortium | `steelconsortium_whiterabbit` | 150,000 | 300,000 | 319,389 | ×2.129 | 4,500 | ×1.596 |
| starcraft_protoss | `protoss_cyberneticscore` | 150,000 | 150,000 | 234,695 | ×1.565 | 1,500 | ×1.565 |
| starcraft_protoss | `protoss_forge` | 150,000 | 150,000 | 234,695 | ×1.565 | 1,500 | ×1.565 |
| starcraft_protoss | `protoss_citadelofadun` | 200,000 | 200,000 | 312,926 | ×1.565 | 2,000 | ×1.565 |
| starcraft_protoss | `protoss_gateway` | 200,000 | 200,000 | 312,926 | ×1.565 | 1,000 | ×1.565 |
| starcraft_protoss | `protoss_roboticsfacility` | 400,000 | 400,000 | 625,852 | ×1.565 | 2,000 | ×1.565 |
| starcraft_protoss | `protoss_roboticssupportbay` | 200,000 | 200,000 | 312,926 | ×1.565 | 2,000 | ×1.565 |
| starcraft_protoss | `protoss_arbitertribunal` | 250,000 | 250,000 | 391,158 | ×1.565 | 2,500 | ×1.565 |
| starcraft_protoss | `protoss_fleetbeacon` | 1,000,000 | 1,000,000 | 1,564,630 | ×1.565 | 10,000 | ×1.565 |
| starcraft_protoss | `protoss_nexus` | 1,000,000 | 1,000,000 | 1,564,630 | ×1.565 | 5,000 | ×1.565 |
| starcraft_protoss | `protoss_observatory` | 250,000 | 250,000 | 391,158 | ×1.565 | 2,500 | ×1.565 |
| starcraft_protoss | `protoss_pylon` | 250,000 | 250,000 | 391,158 | ×1.565 | 1,000 | ×1.565 |
| starcraft_protoss | `protoss_templararchives` | 250,000 | 250,000 | 391,158 | ×1.565 | 2,500 | ×1.565 |
| starcraft_protoss | `protoss_assimilator` | 300,000 | 300,000 | 469,389 | ×1.565 | 3,000 | ×1.565 |
| starcraft_protoss | `protoss_stargate` | 300,000 | 300,000 | 469,389 | ×1.565 | 1,500 | ×1.565 |
| starcraft_protoss | `protoss_mobilenexus` | 300,000 | 300,000 | 469,389 | ×1.565 | 5,000 | ×1.513 |
| redalert2mod_consortium | `cruiser_f.steel` | 37,500 | 75,000 | 79,847 | ×2.129 | 125 | ×1.479 |
| starcraft_protoss | `protoss_starshipsovereign` | 750,000 | 750,000 | 1,173,473 | ×1.565 | 10,000 | ×1.466 |
| redalert2mod_consortium | `steelconsortium_supportshieldgenerator` | 100,000 | 200,000 | 212,926 | ×2.129 | 3,000 | ×1.452 |
| redalert2mod_consortium | `steelconsortium_empressstation` | 1,500,000 | 1,500,000 | 2,346,946 | ×1.565 | 5,000 | ×1.447 |
| starcraft_protoss | `protoss_archon` | 350,000 | 350,000 | 547,621 | ×1.565 | 5,600 | ×1.425 |
| starcraft_protoss | `protoss_epigraph` | 200,000 | 200,000 | 312,926 | ×1.565 | 2,600 | ×1.412 |
| starcraft_protoss | `protoss_shuttle` | 100,000 | 100,000 | 156,463 | ×1.565 | 6,000 | ×1.411 |
| starcraft_protoss | `protoss_carrier` | 300,000 | 300,000 | 469,389 | ×1.565 | 3,000 | ×1.395 |
| starcraft_protoss | `protoss_idol` | 350,000 | 350,000 | 547,621 | ×1.565 | 2,800 | ×1.391 |
| starcraft_protoss | `protoss_arbiter` | 225,000 | 225,000 | 352,042 | ×1.565 | 4,800 | ×1.387 |
| starcraft_protoss | `protoss_atreus` | 250,000 | 250,000 | 391,158 | ×1.565 | 2,400 | ×1.381 |
| starcraft_protoss | `protoss_zeratul` | 250,000 | 250,000 | 391,158 | ×1.565 | 4,000 | ×1.380 |
| starcraft_protoss | `protoss_corsair` | 125,000 | 125,000 | 195,579 | ×1.565 | 2,100 | ×1.375 |
| redalert2mod_consortium | `steelconsortium_cloudbreaker` | 250,000 | 250,000 | 391,158 | ×1.565 | 5,000 | ×1.371 |
| starcraft_protoss | `protoss_reaver` | 275,000 | 275,000 | 430,273 | ×1.565 | 2,700 | ×1.359 |
| redalert2mod_consortium | `cougar.steel` | 25,000 | 50,000 | 53,232 | ×2.129 | 1,200 | ×1.329 |
| starcraft_protoss | `protoss_voidray` | 70,000 | 70,000 | 109,524 | ×1.565 | 1,400 | ×1.329 |
| starcraft_protoss | `protoss_scout` | 75,000 | 75,000 | 117,347 | ×1.565 | 1,500 | ×1.328 |
| redalert2mod_consortium | `hummer.steel` | 45,000 | 67,500 | 83,113 | ×1.847 | 2,000 | ×1.326 |
| redalert2mod_consortium | `oldqtnk.steel` | 112,500 | 112,500 | 176,021 | ×1.565 | 2,400 | ×1.322 |
| starcraft_protoss | `protoss_shieldbattery` | 100,000 | 100,000 | 156,463 | ×1.565 | 1,000 | ×1.282 |
| starcraft_protoss | `protoss_positron` | 60,000 | 60,000 | 93,878 | ×1.565 | 1,200 | ×1.274 |
| starcraft_protoss | `protoss_dragoon` | 75,000 | 75,000 | 117,347 | ×1.565 | 1,200 | ×1.254 |
| starcraft_protoss | `protoss_gladius` | 100,000 | 100,000 | 156,463 | ×1.565 | 1,800 | ×1.251 |
| starcraft_protoss | `protoss_patriarch` | 75,000 | 75,000 | 117,347 | ×1.565 | 4,000 | ×1.248 |
| redalert2mod_consortium | `cobra.steel` | 325,000 | 162,500 | 416,752 | ×1.282 | 3,600 | ×1.208 |
| starcraft_protoss | `protoss_probe` | 45,000 | 45,000 | 70,408 | ×1.565 | 500 | ×1.198 |
| starcraft_protoss | `protoss_analogue` | 60,000 | 60,000 | 93,878 | ×1.565 | 1,200 | ×1.198 |
| starcraft_protoss | `protoss_amaranth` | 70,000 | 70,000 | 109,524 | ×1.565 | 1,200 | ×1.189 |
| starcraft_protoss | `protoss_observer` | 12,500 | 12,500 | 19,558 | ×1.565 | 500 | ×1.177 |
| starcraft_protoss | `protoss_darktemplar` | 50,000 | 50,000 | 78,232 | ×1.565 | 600 | ×1.169 |
| starcraft_protoss | `protoss_zealot` | 40,000 | 40,000 | 62,585 | ×1.565 | 300 | ×1.154 |
| starcraft_protoss | `protoss_legionnaire` | 60,000 | 60,000 | 93,878 | ×1.565 | 700 | ×1.149 |
| starcraft_protoss | `protoss_adept` | 30,000 | 30,000 | 46,939 | ×1.565 | 650 | ×1.136 |
| starcraft_protoss | `protoss_manifold` | 25,000 | 25,000 | 39,116 | ×1.565 | 600 | ×1.124 |
| starcraft_protoss | `protoss_photoncannon` | 200,000 | 200,000 | 312,926 | ×1.565 | 2,000 | ×1.015 |
