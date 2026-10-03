# audit_drain_status — live vs dead defs per global file


## R1 — file summary (nodes / live / dead / referrer packs)

| file | nodes | live | dead | live referrers |
|---|---|---|---|---|
| weapons/advacewars.yaml | 109 | 0 | 109 |  |
| weapons/advancewars.yaml | 109 | 0 | 109 |  |
| weapons/ballistics.yaml | 18 | 4 | 14 | GLOBAL:tech, RedAlert/Japan, RedAlert2/Allies, RedAlert2Mod/FutureTech, RedAlert2Mod/Naxis, TiberianDawn/GDI… |
| weapons/classicdoom.yaml | 25 | 0 | 25 |  |
| weapons/d2k.yaml | 90 | 1 | 89 | GLOBAL:d2k |
| weapons/darkreign.yaml | 94 | 0 | 94 |  |
| weapons/dune2.yaml | 16 | 0 | 16 |  |
| weapons/effects_d2k.yaml | 112 | 0 | 112 |  |
| weapons/effects_op2.yaml | 13 | 0 | 13 |  |
| weapons/effects_td.yaml | 45 | 0 | 45 |  |
| weapons/effects_ts.yaml | 99 | 0 | 99 |  |
| weapons/elementals.yaml | 4 | 0 | 4 |  |
| weapons/ep315.yaml | 4 | 0 | 4 |  |
| weapons/explosions.yaml | 18 | 11 | 7 | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos, D2k/Shared… |
| weapons/generals.yaml | 208 | 0 | 208 |  |
| weapons/halloween.yaml | 16 | 0 | 16 |  |
| weapons/heroes.yaml | 76 | 0 | 76 |  |
| weapons/infected.yaml | 18 | 0 | 18 |  |
| weapons/iok.yaml | 1 | 0 | 1 |  |
| weapons/keeper.yaml | 3 | 0 | 3 |  |
| weapons/lostunits.yaml | 37 | 0 | 37 |  |
| weapons/mindustry.yaml | 11 | 0 | 11 |  |
| weapons/missiles.yaml | 29 | 2 | 27 | GLOBAL:tech, TiberianDawn/GDI |
| weapons/monsters.yaml | 37 | 2 | 35 | GLOBAL:tiberiansun |
| weapons/other.yaml | 70 | 15 | 55 | D2k/Ordos, GLOBAL:civilian, GLOBAL:tiberiansun, GLOBAL:weapons, RedAlert/Allies, RedAlert/Japan… |
| weapons/outpost2.yaml | 37 | 32 | 5 | GLOBAL:outpost2 |
| weapons/redalert2.yaml | 180 | 128 | 52 | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos, D2k/Shared… |
| weapons/redalert2mod.yaml | 80 | 45 | 35 | GLOBAL:redalert2mod, RedAlert2/Shared, RedAlert2/Soviets, RedAlert2Mod/AsianAlliance, RedAlert2Mod/Consortium, RedAlert2Mod/FutureTech… |
| weapons/sc2k.yaml | 12 | 0 | 12 |  |
| weapons/shockwave.yaml | 214 | 0 | 214 |  |
| weapons/simcity.yaml | 20 | 0 | 20 |  |
| weapons/sow.yaml | 58 | 0 | 58 |  |
| weapons/starcraft.yaml | 21 | 13 | 8 | GLOBAL:starcraft, RedAlert/Japan, RedAlert2/Allies, RedAlert2Mod/FutureTech, RedAlert2Mod/TKM, StarCraft/Protoss… |
| weapons/starcraft2.yaml | 1 | 0 | 1 |  |
| weapons/starwars.yaml | 92 | 1 | 91 | RedAlert2Mod/Consortium |
| weapons/targeting.yaml | 6 | 3 | 3 | GLOBAL:outpost2, RedAlert/Soviets, RedAlert2/Allies, RedAlert2/Shared, RedAlert2/Soviets, RedAlert2Mod/AsianAlliance… |
| weapons/tiberiaalliances.yaml | 12 | 0 | 12 |  |
| weapons/tiberiandawn.yaml | 15 | 10 | 5 | GLOBAL:civilian, GLOBAL:tiberiansun, RedAlert/Japan, RedAlert/Soviets, RedAlert2/Allies, RedAlert2/Shared… |
| weapons/tiberiansun.yaml | 112 | 60 | 52 | GLOBAL:misc, GLOBAL:outpost2, GLOBAL:tiberiansun, TiberianSun/CABAL, TiberianSun/Forgotten, TiberianSun/GDI… |
| weapons/tomorrow.yaml | 12 | 0 | 12 |  |
| weapons/valentine.yaml | 21 | 0 | 21 |  |
| weapons/warcraft1.yaml | 27 | 0 | 27 |  |
| weapons/warcraft2.yaml | 26 | 24 | 2 | GLOBAL:warcraft2, RedAlert2Mod/Naxis, Warcraft2/Humans, Warcraft2/Orcs |
| weapons/weapons.yaml | 525 | 61 | 464 | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos, D2k/Shared… |
| weapons/wh40k.yaml | 95 | 0 | 95 |  |
| weapons/win98.yaml | 7 | 0 | 7 |  |
| weapons/worms.yaml | 23 | 1 | 22 | GLOBAL:outpost2, RedAlert/Soviets, RedAlert2/Allies, RedAlert2/Shared, RedAlert2Mod/AsianAlliance, RedAlert2Mod/FutureTech… |
| weapons/wz2100.yaml | 92 | 0 | 92 |  |
| weapons/xcom.yaml | 10 | 0 | 10 |  |
| weapons/xmas.yaml | 15 | 0 | 15 |  |
| weapons/z.yaml | 29 | 0 | 29 |  |
| sequences/actiblizz.yaml | 8 | 0 | 8 |  |
| sequences/advancewars.yaml | 319 | 1 | 318 | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/campaign.yaml | 2 | 1 | 1 | TiberianDawn/GDI |
| sequences/casino.yaml | 15 | 0 | 15 |  |
| sequences/challenge.yaml | 15 | 0 | 15 |  |
| sequences/civilian.yaml | 17 | 0 | 17 |  |
| sequences/classicdoom.yaml | 46 | 0 | 46 |  |
| sequences/d2k.yaml | 150 | 27 | 123 | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos, D2k/Shared |
| sequences/darkreign.yaml | 245 | 1 | 244 | GLOBAL:weapons |
| sequences/decorations.yaml | 431 | 22 | 409 | GLOBAL:misc, GLOBAL:trees |
| sequences/dune2.yaml | 40 | 1 | 39 | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/funpark.yaml | 4 | 0 | 4 |  |
| sequences/generals.yaml | 229 | 1 | 228 | GLOBAL:weapons |
| sequences/halloween.yaml | 43 | 2 | 41 | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos, D2k/Shared… |
| sequences/heroes.yaml | 74 | 1 | 73 | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/hexshields.yaml | 4 | 4 | 0 | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos, D2k/Shared… |
| sequences/infected.yaml | 8 | 0 | 8 |  |
| sequences/iok.yaml | 14 | 0 | 14 |  |
| sequences/keeper.yaml | 5 | 0 | 5 |  |
| sequences/lostunits.yaml | 118 | 4 | 114 | GLOBAL:weapons, RedAlert/Soviets, RedAlert2/Soviets, RedAlert2/Yuri, TiberianDawn/GDI, TiberianDawn/Nod |
| sequences/mindustry.yaml | 21 | 0 | 21 |  |
| sequences/misc.yaml | 200 | 78 | 122 | Core/yaml, D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos… |
| sequences/n64.yaml | 54 | 0 | 54 |  |
| sequences/outpost2.yaml | 95 | 6 | 89 | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos, D2k/Shared… |
| sequences/pokemon.yaml | 2 | 0 | 2 |  |
| sequences/redalert2.yaml | 333 | 84 | 249 | GLOBAL:misc, GLOBAL:tech, RedAlert2/Shared, RedAlert2/Soviets, RedAlert2Mod/FutureTech, RedAlert2Mod/Syndicate |
| sequences/redalert2mod.yaml | 24 | 9 | 15 | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos, D2k/Shared… |
| sequences/sc2k.yaml | 62 | 1 | 61 | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/shared_effects.yaml | 26 | 21 | 5 | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos, D2k/Shared… |
| sequences/shockwave.yaml | 246 | 2 | 244 | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos, D2k/Shared… |
| sequences/simcity.yaml | 43 | 1 | 42 | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/sow.yaml | 112 | 1 | 111 | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/starcraft.yaml | 35 | 10 | 25 | GLOBAL:d2k, GLOBAL:starcraft, GLOBAL:weapons, StarCraft/Protoss, StarCraft/Terran, StarCraft/Zerg |
| sequences/starcraft2.yaml | 4 | 0 | 4 |  |
| sequences/starwars.yaml | 175 | 3 | 172 | GLOBAL:weapons |
| sequences/structures.yaml | 53 | 2 | 51 | TiberianDawn/GDI, TiberianDawn/Nod |
| sequences/test.yaml | 22 | 2 | 20 | GLOBAL:weapons, RedAlert2/Shared |
| sequences/tiberiaalliances.yaml | 107 | 0 | 107 |  |
| sequences/tiberiandawn.yaml | 81 | 10 | 71 | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos, D2k/Shared… |
| sequences/tiberiansun.yaml | 83 | 66 | 17 | GLOBAL:effects_ts, GLOBAL:tiberiansun, TiberianSun/CABAL, TiberianSun/Forgotten, TiberianSun/GDI, TiberianSun/Nod… |
| sequences/tomorrow.yaml | 43 | 1 | 42 | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/valentine.yaml | 45 | 2 | 43 | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos, D2k/Shared… |
| sequences/voxels.yaml | 96 | 38 | 58 | GLOBAL:tiberiansun, RedAlert2/Allies, RedAlert2/Shared, RedAlert2/Soviets, RedAlert2Mod/AsianAlliance, RedAlert2Mod/FutureTech… |
| sequences/warcraft1.yaml | 74 | 1 | 73 | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/warcraft2.yaml | 79 | 27 | 52 | GLOBAL:warcraft2, RedAlert2/Allies, RedAlert2Mod/AsianAlliance, Warcraft2/Humans, Warcraft2/Orcs |
| sequences/wh40k.yaml | 272 | 2 | 270 | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos, D2k/Shared… |
| sequences/win98.yaml | 43 | 1 | 42 | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/worms.yaml | 52 | 2 | 50 | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos, D2k/Shared… |
| sequences/wz2100.yaml | 290 | 0 | 290 |  |
| sequences/xcom.yaml | 2 | 0 | 2 |  |
| sequences/xmas.yaml | 23 | 2 | 21 | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos, D2k/Shared… |
| sequences/z.yaml | 33 | 0 | 33 |  |


## R2 — zero-live files (51) — dead inventory

weapons/advacewars.yaml, weapons/advancewars.yaml, weapons/classicdoom.yaml, weapons/darkreign.yaml, weapons/dune2.yaml, weapons/effects_d2k.yaml, weapons/effects_op2.yaml, weapons/effects_td.yaml, weapons/effects_ts.yaml, weapons/elementals.yaml, weapons/ep315.yaml, weapons/generals.yaml, weapons/halloween.yaml, weapons/heroes.yaml, weapons/infected.yaml, weapons/iok.yaml, weapons/keeper.yaml, weapons/lostunits.yaml, weapons/mindustry.yaml, weapons/sc2k.yaml, weapons/shockwave.yaml, weapons/simcity.yaml, weapons/sow.yaml, weapons/starcraft2.yaml, weapons/tiberiaalliances.yaml, weapons/tomorrow.yaml, weapons/valentine.yaml, weapons/warcraft1.yaml, weapons/wh40k.yaml, weapons/win98.yaml, weapons/wz2100.yaml, weapons/xcom.yaml, weapons/xmas.yaml, weapons/z.yaml, sequences/actiblizz.yaml, sequences/casino.yaml, sequences/challenge.yaml, sequences/civilian.yaml, sequences/classicdoom.yaml, sequences/funpark.yaml, sequences/infected.yaml, sequences/iok.yaml, sequences/keeper.yaml, sequences/mindustry.yaml, sequences/n64.yaml, sequences/pokemon.yaml, sequences/starcraft2.yaml, sequences/tiberiaalliances.yaml, sequences/wz2100.yaml, sequences/xcom.yaml, sequences/z.yaml

## R3 — cross-theme referrers (40)

| file | foreign packs |
|---|---|
| weapons/ballistics.yaml | RedAlert/Japan, RedAlert2/Allies, RedAlert2Mod/FutureTech, RedAlert2Mod/Naxis, TiberianDawn/GDI |
| weapons/explosions.yaml | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos |
| weapons/missiles.yaml | TiberianDawn/GDI |
| weapons/other.yaml | D2k/Ordos, RedAlert/Allies, RedAlert/Japan, RedAlert2/Allies, RedAlert2/Shared |
| weapons/redalert2.yaml | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos |
| weapons/redalert2mod.yaml | RedAlert2/Shared, RedAlert2/Soviets, StarCraft/Protoss, StarCraft/Terran |
| weapons/starcraft.yaml | RedAlert/Japan, RedAlert2/Allies, RedAlert2Mod/FutureTech, RedAlert2Mod/TKM, Warcraft2/Humans |
| weapons/starwars.yaml | RedAlert2Mod/Consortium |
| weapons/targeting.yaml | RedAlert/Soviets, RedAlert2/Allies, RedAlert2/Shared, RedAlert2/Soviets, RedAlert2Mod/AsianAlliance |
| weapons/tiberiandawn.yaml | RedAlert/Japan, RedAlert/Soviets, RedAlert2/Allies, RedAlert2/Shared, RedAlert2Mod/FutureTech |
| weapons/warcraft2.yaml | RedAlert2Mod/Naxis |
| weapons/weapons.yaml | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos |
| weapons/worms.yaml | RedAlert/Soviets, RedAlert2/Allies, RedAlert2/Shared, RedAlert2Mod/AsianAlliance, RedAlert2Mod/FutureTech |
| sequences/advancewars.yaml | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/campaign.yaml | TiberianDawn/GDI |
| sequences/dune2.yaml | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/halloween.yaml | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos |
| sequences/heroes.yaml | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/hexshields.yaml | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos |
| sequences/lostunits.yaml | RedAlert/Soviets, RedAlert2/Soviets, RedAlert2/Yuri, TiberianDawn/GDI, TiberianDawn/Nod |
| sequences/misc.yaml | Core/yaml, D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian |
| sequences/outpost2.yaml | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos |
| sequences/redalert2mod.yaml | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos |
| sequences/sc2k.yaml | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/shared_effects.yaml | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos |
| sequences/shockwave.yaml | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos |
| sequences/simcity.yaml | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/sow.yaml | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/structures.yaml | TiberianDawn/GDI, TiberianDawn/Nod |
| sequences/test.yaml | RedAlert2/Shared |
| sequences/tiberiandawn.yaml | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos |
| sequences/tomorrow.yaml | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/valentine.yaml | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos |
| sequences/voxels.yaml | RedAlert2/Allies, RedAlert2/Shared, RedAlert2/Soviets, RedAlert2Mod/AsianAlliance, RedAlert2Mod/FutureTech |
| sequences/warcraft1.yaml | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/warcraft2.yaml | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/wh40k.yaml | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos |
| sequences/win98.yaml | RedAlert2/Allies, RedAlert2Mod/AsianAlliance |
| sequences/worms.yaml | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos |
| sequences/xmas.yaml | D2k/Atreides, D2k/Corrino, D2k/Harkonnen, D2k/Ixian, D2k/Ordos |

