# audit_survivability_pricing — E1: the baseline shield is priced at ZERO

| bucket | actors | priced today | belongs to |
|---|--:|---|---|
| spawns with a pool (**always-on**) | 56 | ✖ nothing | **E1 — this report** |
| empty capacity, needs `shieldgen` | 1227 | ✔ correctly nothing | — (it has no shield) |
| pool behind an upgrade | 231 | ✖ nothing | E5 (upgrade pricing) |

Shield row mean Versus **176.60**, so one shield point is **0.5663 HP** BEFORE any shield-gated `DamageMultiplier` — measured off the live ladder every run, never frozen. The Shield row takes **1.515%** of all roster raw damage at baseline.

⚠ **Every one of these 56 actors also carries `DamageMultiplier@shielded: 150`**, so it takes 150% damage WHILE the shield holds — the deliberate counterweight to having one. That divides the pool's worth: a shield point is really **0.3775 HP**, and the roster-wide gap is 38.6% rather than the 57.8% a shield-only reading gives. `shield_damage_multiplier` and `shield_hp_per_point` are published per actor.

## The gap

* Raw HP across these 56 actors: **12,812,500**
* Effective HP once the pool is counted: **20,587,228** (**+60.7%**)
* Implied price change if the formula read effective HP: median **×1.394**, max **×1.787**

⚠ **Retiring the 150% multiplier is a BUFF that must be paid for.** The numbers above already account for it, so they price the game AS IT IS. Delete `DamageMultiplier@shielded` and a shield point jumps from 0.378 to 0.566 HP — the same pool becomes 1.5x more valuable and the implied price rises again. Re-extract AFTER the deletion and price once, or these units get charged for durability they no longer have (or keep durability they were never charged for).

## Per actor

| pack | actor | HP | shield pool | effective HP | ×HP | cost | implied ×price |
|---|---|--:|--:|--:|--:|--:|--:|
| redalert2mod_consortium | `steelconsortium_defenderbot` | 210,000 | 420,000 | 447,828 | ×2.132 | 3,200 | ×1.787 |
| redalert2mod_consortium | `steelconsortium_skyhammer` | 120,000 | 240,000 | 255,902 | ×2.132 | 4,500 | ×1.780 |
| redalert2mod_consortium | `steelconsortium_katytank` | 275,000 | 550,000 | 586,442 | ×2.132 | 3,800 | ×1.743 |
| redalert2mod_consortium | `steelconsortium_stalker` | 140,000 | 280,000 | 298,552 | ×2.132 | 4,000 | ×1.725 |
| redalert2mod_consortium | `steelconsortium_whiterabbit` | 150,000 | 300,000 | 319,878 | ×2.132 | 4,500 | ×1.597 |
| starcraft_protoss | `protoss_cyberneticscore` | 150,000 | 150,000 | 234,939 | ×1.566 | 1,500 | ×1.566 |
| starcraft_protoss | `protoss_forge` | 150,000 | 150,000 | 234,939 | ×1.566 | 1,500 | ×1.566 |
| starcraft_protoss | `protoss_citadelofadun` | 200,000 | 200,000 | 313,252 | ×1.566 | 2,000 | ×1.566 |
| starcraft_protoss | `protoss_gateway` | 200,000 | 200,000 | 313,252 | ×1.566 | 1,000 | ×1.566 |
| starcraft_protoss | `protoss_roboticsfacility` | 400,000 | 400,000 | 626,503 | ×1.566 | 2,000 | ×1.566 |
| starcraft_protoss | `protoss_roboticssupportbay` | 200,000 | 200,000 | 313,252 | ×1.566 | 2,000 | ×1.566 |
| starcraft_protoss | `protoss_arbitertribunal` | 250,000 | 250,000 | 391,565 | ×1.566 | 2,500 | ×1.566 |
| starcraft_protoss | `protoss_fleetbeacon` | 1,000,000 | 1,000,000 | 1,566,258 | ×1.566 | 10,000 | ×1.566 |
| starcraft_protoss | `protoss_nexus` | 1,000,000 | 1,000,000 | 1,566,258 | ×1.566 | 5,000 | ×1.566 |
| starcraft_protoss | `protoss_observatory` | 250,000 | 250,000 | 391,565 | ×1.566 | 2,500 | ×1.566 |
| starcraft_protoss | `protoss_pylon` | 250,000 | 250,000 | 391,565 | ×1.566 | 1,000 | ×1.566 |
| starcraft_protoss | `protoss_templararchives` | 250,000 | 250,000 | 391,565 | ×1.566 | 2,500 | ×1.566 |
| starcraft_protoss | `protoss_assimilator` | 300,000 | 300,000 | 469,878 | ×1.566 | 3,000 | ×1.566 |
| starcraft_protoss | `protoss_stargate` | 300,000 | 300,000 | 469,878 | ×1.566 | 1,500 | ×1.566 |
| starcraft_protoss | `protoss_mobilenexus` | 300,000 | 300,000 | 469,878 | ×1.566 | 5,000 | ×1.515 |
| redalert2mod_consortium | `cruiser_f.steel` | 37,500 | 75,000 | 79,969 | ×2.132 | 125 | ×1.480 |
| starcraft_protoss | `protoss_starshipsovereign` | 750,000 | 750,000 | 1,174,694 | ×1.566 | 10,000 | ×1.467 |
| redalert2mod_consortium | `steelconsortium_supportshieldgenerator` | 100,000 | 200,000 | 213,252 | ×2.132 | 3,000 | ×1.453 |
| redalert2mod_consortium | `steelconsortium_empressstation` | 1,500,000 | 1,500,000 | 2,349,388 | ×1.566 | 5,000 | ×1.448 |
| starcraft_protoss | `protoss_archon` | 350,000 | 350,000 | 548,190 | ×1.566 | 5,600 | ×1.426 |
| starcraft_protoss | `protoss_epigraph` | 200,000 | 200,000 | 313,252 | ×1.566 | 2,600 | ×1.416 |
| starcraft_protoss | `protoss_shuttle` | 100,000 | 100,000 | 156,626 | ×1.566 | 6,000 | ×1.412 |
| starcraft_protoss | `protoss_carrier` | 300,000 | 300,000 | 469,878 | ×1.566 | 3,000 | ×1.396 |
| starcraft_protoss | `protoss_idol` | 350,000 | 350,000 | 548,190 | ×1.566 | 2,800 | ×1.393 |
| starcraft_protoss | `protoss_atreus` | 250,000 | 250,000 | 391,565 | ×1.566 | 2,400 | ×1.391 |
| starcraft_protoss | `protoss_arbiter` | 225,000 | 225,000 | 352,408 | ×1.566 | 4,800 | ×1.388 |
| starcraft_protoss | `protoss_zeratul` | 250,000 | 250,000 | 391,565 | ×1.566 | 4,000 | ×1.381 |
| starcraft_protoss | `protoss_corsair` | 125,000 | 125,000 | 195,782 | ×1.566 | 2,100 | ×1.376 |
| redalert2mod_consortium | `steelconsortium_cloudbreaker` | 250,000 | 250,000 | 391,565 | ×1.566 | 5,000 | ×1.372 |
| starcraft_protoss | `protoss_reaver` | 275,000 | 275,000 | 430,721 | ×1.566 | 2,700 | ×1.360 |
| redalert2mod_consortium | `cougar.steel` | 25,000 | 50,000 | 53,313 | ×2.132 | 1,200 | ×1.330 |
| starcraft_protoss | `protoss_voidray` | 70,000 | 70,000 | 109,638 | ×1.566 | 1,400 | ×1.330 |
| starcraft_protoss | `protoss_scout` | 75,000 | 75,000 | 117,469 | ×1.566 | 1,500 | ×1.329 |
| redalert2mod_consortium | `hummer.steel` | 45,000 | 67,500 | 83,222 | ×1.849 | 2,000 | ×1.327 |
| redalert2mod_consortium | `oldqtnk.steel` | 112,500 | 112,500 | 176,204 | ×1.566 | 2,400 | ×1.323 |
| starcraft_protoss | `protoss_shieldbattery` | 100,000 | 100,000 | 156,626 | ×1.566 | 1,000 | ×1.283 |
| starcraft_protoss | `protoss_positron` | 60,000 | 60,000 | 93,976 | ×1.566 | 1,200 | ×1.274 |
| starcraft_protoss | `protoss_dragoon` | 75,000 | 75,000 | 117,469 | ×1.566 | 1,200 | ×1.254 |
| starcraft_protoss | `protoss_gladius` | 100,000 | 100,000 | 156,626 | ×1.566 | 1,800 | ×1.252 |
| starcraft_protoss | `protoss_patriarch` | 75,000 | 75,000 | 117,469 | ×1.566 | 4,000 | ×1.249 |
| redalert2mod_consortium | `cobra.steel` | 325,000 | 162,500 | 417,017 | ×1.283 | 3,600 | ×1.209 |
| starcraft_protoss | `protoss_probe` | 45,000 | 45,000 | 70,482 | ×1.566 | 500 | ×1.199 |
| starcraft_protoss | `protoss_analogue` | 60,000 | 60,000 | 93,976 | ×1.566 | 1,200 | ×1.198 |
| starcraft_protoss | `protoss_amaranth` | 70,000 | 70,000 | 109,638 | ×1.566 | 1,200 | ×1.189 |
| starcraft_protoss | `protoss_observer` | 12,500 | 12,500 | 19,578 | ×1.566 | 500 | ×1.178 |
| starcraft_protoss | `protoss_darktemplar` | 50,000 | 50,000 | 78,313 | ×1.566 | 600 | ×1.170 |
| starcraft_protoss | `protoss_zealot` | 40,000 | 40,000 | 62,650 | ×1.566 | 300 | ×1.154 |
| starcraft_protoss | `protoss_legionnaire` | 60,000 | 60,000 | 93,976 | ×1.566 | 700 | ×1.150 |
| starcraft_protoss | `protoss_adept` | 30,000 | 30,000 | 46,988 | ×1.566 | 650 | ×1.136 |
| starcraft_protoss | `protoss_manifold` | 25,000 | 25,000 | 39,156 | ×1.566 | 600 | ×1.124 |
| starcraft_protoss | `protoss_photoncannon` | 200,000 | 200,000 | 313,252 | ×1.566 | 2,000 | ×1.015 |
