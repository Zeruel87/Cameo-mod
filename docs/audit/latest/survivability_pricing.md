# audit_survivability_pricing — E1: the baseline shield is priced at ZERO

| bucket | actors | priced today | belongs to |
|---|--:|---|---|
| spawns with a pool (**always-on**) | 56 | ✖ nothing | **E1 — this report** |
| empty capacity, needs `shieldgen` | 1164 | ✔ correctly nothing | — (it has no shield) |
| pool behind an upgrade | 210 | ✖ nothing | E5 (upgrade pricing) |

Shield row mean Versus **189.81**, so one shield point is **0.5269 HP** BEFORE any shield-gated `DamageMultiplier` — measured off the live ladder every run, never frozen. The Shield row takes **1.465%** of all roster raw damage at baseline.

⚠ **Every one of these 56 actors also carries `DamageMultiplier@shielded: 150`**, so it takes 150% damage WHILE the shield holds — the deliberate counterweight to having one. That divides the pool's worth: a shield point is really **0.3512 HP**, and the roster-wide gap is 38.6% rather than the 57.8% a shield-only reading gives. `shield_damage_multiplier` and `shield_hp_per_point` are published per actor.

## The gap

* Raw HP across these 56 actors: **12,812,500**
* Effective HP once the pool is counted: **20,046,224** (**+56.5%**)
* Implied price change if the formula read effective HP: median **×1.368**, max **×1.733**

⚠ **Retiring the 150% multiplier is a BUFF that must be paid for.** The numbers above already account for it, so they price the game AS IT IS. Delete `DamageMultiplier@shielded` and a shield point jumps from 0.351 to 0.527 HP — the same pool becomes 1.5x more valuable and the implied price rises again. Re-extract AFTER the deletion and price once, or these units get charged for durability they no longer have (or keep durability they were never charged for).

## Per actor

| pack | actor | HP | shield pool | effective HP | ×HP | cost | implied ×price |
|---|---|--:|--:|--:|--:|--:|--:|
| redalert2mod_consortium | `steelconsortium_defenderbot` | 210,000 | 420,000 | 431,279 | ×2.054 | 3,200 | ×1.733 |
| redalert2mod_consortium | `steelconsortium_skyhammer` | 120,000 | 240,000 | 246,445 | ×2.054 | 4,500 | ×1.726 |
| redalert2mod_consortium | `steelconsortium_katytank` | 275,000 | 550,000 | 564,770 | ×2.054 | 3,800 | ×1.691 |
| redalert2mod_consortium | `steelconsortium_stalker` | 140,000 | 280,000 | 287,520 | ×2.054 | 4,000 | ×1.674 |
| redalert2mod_consortium | `steelconsortium_whiterabbit` | 150,000 | 300,000 | 308,057 | ×2.054 | 4,500 | ×1.555 |
| starcraft_protoss | `protoss_citadelofadun` | 200,000 | 200,000 | 305,371 | ×1.527 | 2,000 | ×1.527 |
| starcraft_protoss | `protoss_gateway` | 200,000 | 200,000 | 305,371 | ×1.527 | 1,000 | ×1.527 |
| starcraft_protoss | `protoss_roboticsfacility` | 400,000 | 400,000 | 610,742 | ×1.527 | 2,000 | ×1.527 |
| starcraft_protoss | `protoss_roboticssupportbay` | 200,000 | 200,000 | 305,371 | ×1.527 | 2,000 | ×1.527 |
| starcraft_protoss | `protoss_fleetbeacon` | 1,000,000 | 1,000,000 | 1,526,855 | ×1.527 | 10,000 | ×1.527 |
| starcraft_protoss | `protoss_nexus` | 1,000,000 | 1,000,000 | 1,526,855 | ×1.527 | 5,000 | ×1.527 |
| starcraft_protoss | `protoss_assimilator` | 300,000 | 300,000 | 458,057 | ×1.527 | 3,000 | ×1.527 |
| starcraft_protoss | `protoss_cyberneticscore` | 150,000 | 150,000 | 229,028 | ×1.527 | 1,500 | ×1.527 |
| starcraft_protoss | `protoss_forge` | 150,000 | 150,000 | 229,028 | ×1.527 | 1,500 | ×1.527 |
| starcraft_protoss | `protoss_stargate` | 300,000 | 300,000 | 458,057 | ×1.527 | 1,500 | ×1.527 |
| starcraft_protoss | `protoss_arbitertribunal` | 250,000 | 250,000 | 381,714 | ×1.527 | 2,500 | ×1.527 |
| starcraft_protoss | `protoss_observatory` | 250,000 | 250,000 | 381,714 | ×1.527 | 2,500 | ×1.527 |
| starcraft_protoss | `protoss_pylon` | 250,000 | 250,000 | 381,714 | ×1.527 | 1,000 | ×1.527 |
| starcraft_protoss | `protoss_templararchives` | 250,000 | 250,000 | 381,714 | ×1.527 | 2,500 | ×1.527 |
| redalert2mod_consortium | `cruiser_f.steel` | 37,500 | 75,000 | 77,014 | ×2.054 | 125 | ×1.522 |
| starcraft_protoss | `protoss_mobilenexus` | 300,000 | 300,000 | 458,057 | ×1.527 | 5,000 | ×1.479 |
| starcraft_protoss | `protoss_starshipsovereign` | 750,000 | 750,000 | 1,145,142 | ×1.527 | 10,000 | ×1.436 |
| redalert2mod_consortium | `steelconsortium_supportshieldgenerator` | 100,000 | 200,000 | 205,371 | ×2.054 | 3,000 | ×1.421 |
| redalert2mod_consortium | `steelconsortium_empressstation` | 1,500,000 | 1,500,000 | 2,290,283 | ×1.527 | 5,000 | ×1.417 |
| starcraft_protoss | `protoss_archon` | 350,000 | 350,000 | 534,399 | ×1.527 | 5,600 | ×1.397 |
| starcraft_protoss | `protoss_epigraph` | 200,000 | 200,000 | 305,371 | ×1.527 | 2,600 | ×1.385 |
| starcraft_protoss | `protoss_shuttle` | 100,000 | 100,000 | 152,686 | ×1.527 | 6,000 | ×1.383 |
| starcraft_protoss | `protoss_carrier` | 300,000 | 300,000 | 458,057 | ×1.527 | 3,000 | ×1.368 |
| starcraft_protoss | `protoss_arbiter` | 225,000 | 225,000 | 343,542 | ×1.527 | 4,800 | ×1.367 |
| starcraft_protoss | `protoss_idol` | 350,000 | 350,000 | 534,399 | ×1.527 | 2,800 | ×1.365 |
| starcraft_protoss | `protoss_atreus` | 250,000 | 250,000 | 381,714 | ×1.527 | 2,400 | ×1.360 |
| starcraft_protoss | `protoss_zeratul` | 250,000 | 250,000 | 381,714 | ×1.527 | 4,000 | ×1.356 |
| starcraft_protoss | `protoss_corsair` | 125,000 | 125,000 | 190,857 | ×1.527 | 2,100 | ×1.350 |
| redalert2mod_consortium | `steelconsortium_cloudbreaker` | 250,000 | 250,000 | 381,714 | ×1.527 | 5,000 | ×1.346 |
| starcraft_protoss | `protoss_reaver` | 275,000 | 275,000 | 419,885 | ×1.527 | 2,700 | ×1.332 |
| redalert2mod_consortium | `hummer.steel` | 45,000 | 67,500 | 80,563 | ×1.790 | 2,000 | ×1.313 |
| starcraft_protoss | `protoss_scout` | 75,000 | 75,000 | 114,514 | ×1.527 | 1,500 | ×1.307 |
| starcraft_protoss | `protoss_voidray` | 70,000 | 70,000 | 106,880 | ×1.527 | 1,400 | ×1.305 |
| redalert2mod_consortium | `oldqtnk.steel` | 112,500 | 112,500 | 171,771 | ×1.527 | 2,400 | ×1.300 |
| redalert2mod_consortium | `cougar.steel` | 25,000 | 50,000 | 51,343 | ×2.054 | 1,200 | ×1.278 |
| starcraft_protoss | `protoss_shieldbattery` | 100,000 | 100,000 | 152,686 | ×1.527 | 1,000 | ×1.263 |
| starcraft_protoss | `protoss_positron` | 60,000 | 60,000 | 91,611 | ×1.527 | 1,200 | ×1.257 |
| starcraft_protoss | `protoss_dragoon` | 75,000 | 75,000 | 114,514 | ×1.527 | 1,200 | ×1.242 |
| starcraft_protoss | `protoss_patriarch` | 75,000 | 75,000 | 114,514 | ×1.527 | 4,000 | ×1.236 |
| starcraft_protoss | `protoss_gladius` | 100,000 | 100,000 | 152,686 | ×1.527 | 1,800 | ×1.234 |
| redalert2mod_consortium | `cobra.steel` | 325,000 | 162,500 | 410,614 | ×1.263 | 3,600 | ×1.194 |
| starcraft_protoss | `protoss_probe` | 45,000 | 45,000 | 68,708 | ×1.527 | 500 | ×1.185 |
| starcraft_protoss | `protoss_analogue` | 60,000 | 60,000 | 91,611 | ×1.527 | 1,200 | ×1.184 |
| starcraft_protoss | `protoss_amaranth` | 70,000 | 70,000 | 106,880 | ×1.527 | 1,200 | ×1.179 |
| starcraft_protoss | `protoss_observer` | 12,500 | 12,500 | 19,086 | ×1.527 | 500 | ×1.166 |
| starcraft_protoss | `protoss_darktemplar` | 50,000 | 50,000 | 76,343 | ×1.527 | 600 | ×1.158 |
| starcraft_protoss | `protoss_zealot` | 40,000 | 40,000 | 61,074 | ×1.527 | 300 | ×1.148 |
| starcraft_protoss | `protoss_legionnaire` | 60,000 | 60,000 | 91,611 | ×1.527 | 700 | ×1.143 |
| starcraft_protoss | `protoss_adept` | 30,000 | 30,000 | 45,806 | ×1.527 | 650 | ×1.123 |
| starcraft_protoss | `protoss_manifold` | 25,000 | 25,000 | 38,171 | ×1.527 | 600 | ×1.115 |
| starcraft_protoss | `protoss_photoncannon` | 200,000 | 200,000 | 305,371 | ×1.527 | 2,000 | ×1.045 |
