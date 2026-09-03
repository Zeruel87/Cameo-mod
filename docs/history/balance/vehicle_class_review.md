# Vehicle 13-class classification — REVIEW (maintainer sign-off)

> ⛔ **ARCHIVED 2026-08-23 — not current.** Moved out of the live documentation set: it is either machine-generated (regenerate it rather than reading this copy) or the programme it belonged to is finished or dormant. Kept for provenance. Start at [`docs/HANDOFF.md`](../../HANDOFF.md).

_Auto-generated from CURRENT yaml (in-memory extract). 266 buildable combat vehicles already assigned to the 13 templates via `Inherits@Template`. This is a VERIFY + flag pass, not a from-scratch reclassification: the templates exist and membership is ~90% set. Columns: cost/hp/spd/rng/dps/armor + air(hits air)/T(turret)/K(KeepsDistance)/BL(BuildLimit)._

**subtype→anchor-key map:** `ScoutVehicle`→`scout_vehicle`, `LightTank`→`light_tank`, `Artillery`→`artillery`, `TankDestroyer`→`tank_destroyer`, `ArtilleryTank`→`artillery_tank`, `MainBattleTank`→`mbt`, `AntiAirVehicle`→`anti_air_vehicle`, `MissileVehicle`→`missile_vehicle`, `FireSupport`→`fire_support`, `LineBreaker`→`line_breaker`, `HighTechTank`→`high_tech_tank`, `Dreadnought`→`dreadnought`, `EpicVehicle`→`epic_vehicle`



---

## ⚠ FLAGGED FOR REVIEW (summary)


**hits AIR** (36):
- `artillery` / `cabal_artilleryspider` (Artillery Spider) — hits AIR (§9 ground-only)
- `artillery` / `naxis_donnerschlag` (Donnerschlag) — hits AIR (§9 ground-only)
- `artillery_tank` / `schwarzermond_mars` (MARS) — hits AIR (§9 ground-only)
- `dreadnought` / `asianalliance_pulverizermecha` (Pulverizer Mecha) — hits AIR (§9 ground-only)
- `dreadnought` / `ixian_neocymek` (Neo Cymek) — hits AIR (§9 ground-only)
- `dreadnought` / `terran_warhound` (Warhound) — hits AIR (§9 ground-only)
- `fire_support` / `futuretech_beehivedronecarrier` (Beehive Drone Carrier) — hits AIR (§9 ground-only)
- `fire_support` / `futuretech_gunstrider` (Gun Strider) — hits AIR (§9 ground-only)
- `fire_support` / `ixian_stormraider` (Storm Raider) — hits AIR (§9 ground-only)
- `fire_support` / `japan_waveforcetank` (Waveforce Tank) — hits AIR (§9 ground-only)
- `fire_support` / `naxis_nokana` (Nokana) — hits AIR (§9 ground-only)
- `fire_support` / `ordos_dustdrone` (Dust Drone) — hits AIR (§9 ground-only)
- `fire_support` / `schwarzermond_korruptesbiest` (Korruptes Biest) — hits AIR (§9 ground-only)
- `fire_support` / `td_nod_stealthtank` (Stealth Tank) — hits AIR (§9 ground-only)
- `fire_support` / `tkm_stryker` (TKM Stryker) — hits AIR (§9 ground-only)
- `fire_support` / `ts_gdi_wolverine` (Wolverine) — hits AIR (§9 ground-only)
- `fire_support` / `ts_gdi_wolverinemkii` (Wolverine MK II) — hits AIR (§9 ground-only)
- `fire_support` / `yuri_magnetron` (Magnetron) — hits AIR (§9 ground-only)
- `fire_support` / `zerg_lurker` (Lurker) — hits AIR (§9 ground-only)
- `fire_support` / `zerg_sporemaw` (Sporemaw) — hits AIR (§9 ground-only)
- `line_breaker` / `latinsyndicate_tortugatank` (Tortuga Tank) — hits AIR (§9 ground-only)
- `line_breaker` / `ordos_heavyautoguntank` (Heavy Autogun Tank) — hits AIR (§9 ground-only)
- `line_breaker` / `protoss_archon` (Archon) — hits AIR (§9 ground-only)
- `line_breaker` / `td_gdi_assaultapc` (Assault APC) — hits AIR (§9 ground-only)
- `line_breaker` / `ts_gdi_disruptor` (Disruptor) — hits AIR (§9 ground-only)
- `mbt` / `ixian_mongoose` (Mongoose) — hits AIR (§9 ground-only)
- `mbt` / `latinsyndicate_smokertank` (Smoker Tank) — hits AIR (§9 ground-only)
- `mbt` / `ordos_combatautoguntank` (Combat Autogun Tank) — hits AIR (§9 ground-only)
- `mbt` / `ordos_heavycombattank` (Ordos Heavy Combat Tank) — hits AIR (§9 ground-only)
- `mbt` / `protoss_dragoon` (Dragoon) — hits AIR (§9 ground-only)
- `mbt` / `td_gdi_battletank` (GDI Battle Tank) — hits AIR (§9 ground-only)
- `mbt` / `td_gdi_predatortank` (Predator Tank) — hits AIR (§9 ground-only)
- `mbt` / `terran_matador` (Matador) — hits AIR (§9 ground-only)
- `mbt` / `tkm_t72m` (T-72M) — hits AIR (§9 ground-only)
- `mbt` / `tkm_technicaltank` (Technical Tank) — hits AIR (§9 ground-only)
- `mbt` / `ts_nod_ticktank` (Tick Tank) — hits AIR (§9 ground-only)

**armor=Medium** (18):
- `high_tech_tank` / `cabal_avatar` (Avatar) — armor=Medium (HT=superheavy)
- `high_tech_tank` / `japan_hovercraftflametank` (Hovercraft Flametank) — armor=Medium (HT=superheavy)
- `high_tech_tank` / `ordos_deviatortank` (Deviator Tank) — armor=Medium (HT=superheavy)
- `high_tech_tank` / `ordos_lasertank` (Laser Tank) — armor=Medium (HT=superheavy)
- `high_tech_tank` / `protoss_atreus` (Atreus) — armor=Medium (HT=superheavy)
- `high_tech_tank` / `ra1_soviets_heavyteslatank` (Heavy Tesla Tank) — armor=Medium (HT=superheavy)
- `high_tech_tank` / `ra2_allies_miragetank` (Mirage Tank) — armor=Medium (HT=superheavy)
- `high_tech_tank` / `td_nod_chemicalstealthtank` (Chemical Stealth Tank) — armor=Medium (HT=superheavy)
- `high_tech_tank` / `terran_goliath` (Goliath) — armor=Medium (HT=superheavy)
- `high_tech_tank` / `terran_goliathmk2` (Goliath Mk2) — armor=Medium (HT=superheavy)
- `high_tech_tank` / `zerg_goremaw` (Goremaw) — armor=Medium (HT=superheavy)
- `line_breaker` / `asianalliance_asianflametank` (Asian Flame Tank) — armor=Medium (LB=super/heavy)
- `line_breaker` / `asianalliance_warturtle` (War Turtle) — armor=Medium (LB=super/heavy)
- `line_breaker` / `naxis_oldtank` (Old Tank) — armor=Medium (LB=super/heavy)
- `line_breaker` / `protoss_archon` (Archon) — armor=Medium (LB=super/heavy)
- `line_breaker` / `tkm_battlebus` (Battle Bus) — armor=Medium (LB=super/heavy)
- `line_breaker` / `wc2_humans_paladin` (Paladin) — armor=Medium (LB=super/heavy)
- `line_breaker` / `wc2_humans_warcraft3knight` (Warcraft 3 Knight) — armor=Medium (LB=super/heavy)

**armor=Heavy** (10):
- `dreadnought` / `ixian_neocymek` (Neo Cymek) — armor=Heavy (Dread=superheavy)
- `dreadnought` / `terran_warhound` (Warhound) — armor=Heavy (Dread=superheavy)
- `high_tech_tank` / `duelist_tank.ixian` (Ix Duelist Tank) — armor=Heavy (HT=superheavy)
- `high_tech_tank` / `forgotten_scoopertank` (actor_forgotten_scoopertank.name) — armor=Heavy (HT=superheavy)
- `high_tech_tank` / `futuretech_oriontank` (Orion Tank) — armor=Heavy (HT=superheavy)
- `high_tech_tank` / `naxis_shoekarn` (Shoe Karn) — armor=Heavy (HT=superheavy)
- `high_tech_tank` / `ra2_allies_heavymiragetank` (Heavy Mirage Tank) — armor=Heavy (HT=superheavy)
- `high_tech_tank` / `td_gdi_mammothtank` (GDI Mammoth Tank) — armor=Heavy (HT=superheavy)
- `high_tech_tank` / `ts_nod_stealthtank` (Stealth Tank) — armor=Heavy (HT=superheavy)
- `high_tech_tank` / `yuri_mastermind` (Master Mind) — armor=Heavy (HT=superheavy)

**scout w/o AA** (3):
- `scout_vehicle` / `japan_grenadebuggy` (Grenade Buggy) — scout w/o AA (§9: scouts have AA)
- `scout_vehicle` / `protoss_positron` (Positron) — scout w/o AA (§9: scouts have AA)
- `scout_vehicle` / `ra2_soviets_terrordrone` (Terror Drone) — scout w/o AA (§9: scouts have AA)

**long rng=5000** (3):
- `line_breaker` / `ra2_allies_battlefortress` (Battle Fortress) — long rng=5000 (LB≈2500 brawler)
- `line_breaker` / `ra2_allies_battlefortress_chrono` (Battle Fortress) — long rng=5000 (LB≈2500 brawler)
- `line_breaker` / `ra2_allies_battlefortress_empty` (Battle Fortress) — long rng=5000 (LB≈2500 brawler)

**pricey cost=1200** (2):
- `scout_vehicle` / `ordos_raider` (Ordos Raider) — pricey cost=1200
- `scout_vehicle` / `protoss_positron` (Positron) — pricey cost=1200

**no turret** (2):
- `artillery_tank` / `naxis_sturmtiger` (Sturm Tiger) — no turret (arty_tank is turreted)
- `artillery_tank` / `ts_gdi_juggernautmkii` (Juggernaut MK II) — no turret (arty_tank is turreted)

**BuildLimit1** (2):
- `fire_support` / `naxis_nokana` (Nokana) — BuildLimit1→epic? (§18.1)
- `line_breaker` / `cabal_berserker` (Berserker) — BuildLimit1→epic? (§18.1)

**long rng=512000** (2):
- `line_breaker` / `wc2_humans_paladin` (Paladin) — long rng=512000 (LB≈2500 brawler)
- `line_breaker` / `wc2_humans_warcraft3knight` (Warcraft 3 Knight) — long rng=512000 (LB≈2500 brawler)

**pricey cost=850** (1):
- `scout_vehicle` / `forgotten_bowler` (actor_forgotten_bowler.name) — pricey cost=850

**pricey cost=900** (1):
- `scout_vehicle` / `japan_grenadebuggy` (Grenade Buggy) — pricey cost=900

**pricey cost=950** (1):
- `scout_vehicle` / `futuretech_salamanderifv` (Salamander IFV) — pricey cost=950

**pricey cost=1300** (1):
- `scout_vehicle` / `ordos_stealthraider` (Stealth Raider) — pricey cost=1300

**NO air** (1):
- `anti_air_vehicle` / `tkm_flakbus` (Flak Bus) — NO air (should hit air!)

**short rng=6305** (1):
- `fire_support` / `ts_gdi_wolverine` (Wolverine) — short rng=6305 (FS≈10000)

**short rng=6520** (1):
- `fire_support` / `ts_gdi_wolverinemkii` (Wolverine MK II) — short rng=6520 (FS≈10000)

**short rng=6147** (1):
- `fire_support` / `cabal_laserspider` (Laser Spider) — short rng=6147 (FS≈10000)

**short rng=6806** (1):
- `fire_support` / `td_gdi_exosuit` (Exosuit) — short rng=6806 (FS≈10000)

**short rng=6666** (1):
- `fire_support` / `zerg_lurker` (Lurker) — short rng=6666 (FS≈10000)

**short rng=6500** (1):
- `fire_support` / `ordos_dustdrone` (Dust Drone) — short rng=6500 (FS≈10000)

**long rng=4250** (1):
- `line_breaker` / `ts_nod_devilstongue` (Devil's Tongue) — long rng=4250 (LB≈2500 brawler)

**long rng=4831** (1):
- `line_breaker` / `tkm_battlebus` (Battle Bus) — long rng=4831 (LB≈2500 brawler)

**long rng=4700** (1):
- `line_breaker` / `asianalliance_asianflametank` (Asian Flame Tank) — long rng=4700 (LB≈2500 brawler)

**long rng=5120** (1):
- `line_breaker` / `wc2_orcs_ogremage` (Ogre-Mage) — long rng=5120 (LB≈2500 brawler)

**long rng=7361** (1):
- `line_breaker` / `naxis_oldtank` (Old Tank) — long rng=7361 (LB≈2500 brawler)

**long rng=4050** (1):
- `line_breaker` / `ts_gdi_disruptor` (Disruptor) — long rng=4050 (LB≈2500 brawler)

**long rng=8000** (1):
- `line_breaker` / `futuretech_plasmastrider` (Plasma Strider) — long rng=8000 (LB≈2500 brawler)

**long rng=7480** (1):
- `line_breaker` / `ordos_heavyautoguntank` (Heavy Autogun Tank) — long rng=7480 (LB≈2500 brawler)

**long rng=7000** (1):
- `line_breaker` / `latinsyndicate_tortugatank` (Tortuga Tank) — long rng=7000 (LB≈2500 brawler)

**long rng=6333** (1):
- `line_breaker` / `steelconsortium_poseidontank` (Poseidon Tank) — long rng=6333 (LB≈2500 brawler)

**long rng=8397** (1):
- `line_breaker` / `td_gdi_assaultapc` (Assault APC) — long rng=8397 (LB≈2500 brawler)

**long rng=4567** (1):
- `line_breaker` / `asianalliance_warturtle` (War Turtle) — long rng=4567 (LB≈2500 brawler)

**long rng=7850** (1):
- `line_breaker` / `forgotten_thumperbus` (actor_forgotten_thumperbus.name) — long rng=7850 (LB≈2500 brawler)

**long rng=6800** (1):
- `line_breaker` / `latinsyndicate_carteltruck` (Cartel Truck) — long rng=6800 (LB≈2500 brawler)

## scout_vehicle  (25)  — target: cost 300, hp 30000, spd 200, rng 4500, dps 450

| actor | name | cost | hp | spd | rng | dps | armor | air | T | K | BL | flags |
|---|---|--:|--:|--:|--:|--:|---|:-:|:-:|:-:|:-:|---|
| forgotten_raidercar | actor_forgotten_raidercar.name | 300 | 22500 | 180 | 4475 | 462 | Scout | 1 | 1 | 0 | - |  |
| japan_scoutcar | Scout Car | 300 | 25000 | 160 | 5004 | 857 | Scout | 1 | 1 | 0 | - |  |
| ra1_allies_ranger | Ranger | 300 | 22500 | 175 | 4359 | 480 | Scout | 1 | 1 | 0 | - |  |
| td_nod_buggy | Nod Buggy | 300 | 20000 | 200 | 4540 | 675 | Scout | 1 | 1 | 0 | - | **ANCHOR** |
| td_gdi_humvee | GDI Humvee | 400 | 27500 | 150 | 4792 | 1500 | Scout | 1 | 1 | 0 | - |  |
| tkm_as42 | TKM AS42 | 400 | 27500 | 150 | 7214 | 1391 | Scout | 1 | 0 | 0 | - |  |
| tkm_technical | TKM Technical | 400 | 27500 | 175 | 4792 | 1667 | Scout | 1 | 1 | 0 | - |  |
| ts_gdi_pitbull | Pitbull | 400 | 27500 | 150 | 6379 | 500 | Scout | 1 | 1 | 0 | - |  |
| ts_nod_attackbuggy | Attack Buggy | 450 | 30000 | 160 | 4964 | 2697 | Scout | 1 | 0 | 0 | - |  |
| forgotten_ruiner | actor_forgotten_ruiner.name | 500 | 35000 | 150 | 5919 | 1732 | Scout | 1 | 1 | 0 | - |  |
| ra2_allies_ifv | actor_fv.name | 500 | 25000 | 150 | 10255 | 31700 | Scout | 1 | 1 | 1 | - |  |
| ra2_allies_ifv_chrono | actor_fv.name | 500 | 25000 | 150 | 10255 | 31700 | Scout | 1 | 1 | 1 | - |  |
| ra2_allies_ifv_hmg | actor_fv.name | 500 | 25000 | 150 | 10255 | 31700 | Scout | 1 | 1 | 1 | - |  |
| ra2_allies_ifv_mg | actor_fv.name | 500 | 25000 | 150 | 10255 | 31700 | Scout | 1 | 1 | 1 | - |  |
| ra2_allies_ifv_missile | actor_fv.name | 500 | 25000 | 150 | 10255 | 31700 | Scout | 1 | 1 | 1 | - |  |
| ra2_allies_ifv_repair | actor_fv.name | 500 | 25000 | 150 | 10255 | 31700 | Scout | 1 | 1 | 1 | - |  |
| td_nod_buggymkii | Nod Buggy Mk. II | 500 | 25000 | 120 | 7911 | 1279 | Scout | 1 | 1 | 0 | - |  |
| ra2_soviets_terrordrone | Terror Drone | 600 | 10000 | 200 | 4000 | 0 | Scout | 0 | 0 | 0 | - | scout w/o AA (§9: scouts have AA) |
| td_gdi_humveemkii | Humvee Mk. II | 600 | 37500 | 115 | 8397 | 1714 | Scout | 1 | 1 | 0 | - |  |
| forgotten_bowler | actor_forgotten_bowler.name | 850 | 40000 | 120 | 6603 | 700 | Scout | 1 | 1 | 0 | - | pricey cost=850 |
| japan_grenadebuggy | Grenade Buggy | 900 | 60000 | 120 | 5184 | 2083 | Scout | 0 | 1 | 0 | - | scout w/o AA (§9: scouts have AA); pricey cost=900 |
| futuretech_salamanderifv | Salamander IFV | 950 | 50000 | 150 | 10255 | 31700 | Scout | 1 | 1 | 1 | - | pricey cost=950 |
| ordos_raider | Ordos Raider | 1200 | 60000 | 180 | 6000 | 3188 | Scout | 1 | 0 | 0 | - | pricey cost=1200 |
| protoss_positron | Positron | 1200 | 60000 | 120 | 5044 | 1250 | Light | 0 | 0 | 0 | - | scout w/o AA (§9: scouts have AA); pricey cost=1200 |
| ordos_stealthraider | Stealth Raider | 1300 | 60000 | 180 | 4857 | 923 | Scout | 1 | 0 | 0 | - | pricey cost=1300 |

## light_tank  (15)  — target: cost 400, hp 100000, spd 125, rng 5000, dps 200

| actor | name | cost | hp | spd | rng | dps | armor | air | T | K | BL | flags |
|---|---|--:|--:|--:|--:|--:|---|:-:|:-:|:-:|:-:|---|
| ra1_allies_alliedlighttank | Allied Light Tank | 500 | 50000 | 120 | 4720 | 308 | Medium | 0 | 1 | 0 | - | **ANCHOR** |
| ra1_allies_sheridanassaulttank | Sheridan Assault Tank | 600 | 85000 | 85 | 5023 | 906 | Medium | 1 | 1 | 0 | - |  |
| td_nod_lighttank | Nod Light Tank | 600 | 80000 | 110 | 4993 | 267 | Medium | 1 | 1 | 0 | - |  |
| yuri_lashertank | Lasher Tank | 600 | 70000 | 105 | 10000 | 1628 | Medium | 0 | 1 | 0 | - |  |
| latinsyndicate_rushertank | Rusher Tank | 650 | 75000 | 115 | 6031 | 982 | Medium | 1 | 1 | 0 | - |  |
| ordos_combattank | Ordos Combat Tank | 650 | 85000 | 85 | 5230 | 182 | Medium | 0 | 1 | 0 | - |  |
| schwarzermond_lunarpanzer | Lunar Panzer | 650 | 90000 | 90 | 6121 | 1386 | Medium | 0 | 1 | 0 | - |  |
| td_nod_lighttankmkii | Light Tank Mk. II | 800 | 80000 | 100 | 4903 | 400 | Medium | 1 | 1 | 0 | - | **VERIFIER** |
| steelconsortium_manta | Manta | 850 | 55000 | 115 | 9999 | 2800 | Medium | 1 | 0 | 0 | - |  |
| asianalliance_quasar | Quasar | 900 | 55000 | 125 | 9000 | 970 | Medium | 1 | 0 | 0 | - |  |
| terran_vulture | Vulture | 900 | 75000 | 125 | 4800 | 750 | Light | 0 | 0 | 0 | - | **VERIFIER** |
| ixian_shockraider | Shock Raider | 1300 | 40000 | 120 | 7756 | 450 | Medium | 0 | 1 | 0 | - |  |
| cabal_ravager | Ravager | 1500 | 70000 | 130 | 3000 | 2133 | Plate | 0 | 0 | 0 | - |  |
| futuretech_robottank | Robot Tank | 1600 | 50000 | 130 | 6780 | 1083 | Medium | 0 | 1 | 0 | - |  |
| japan_shrineminitank | Shrine Minitank | 1600 | 60000 | 120 | 6370 | 504 | Medium | 0 | 1 | 0 | - |  |

## artillery  (26)  — target: cost 500, hp 50000, spd 75, rng 15000, dps 500

| actor | name | cost | hp | spd | rng | dps | armor | air | T | K | BL | flags |
|---|---|--:|--:|--:|--:|--:|---|:-:|:-:|:-:|:-:|---|
| td_nod_artillery | Nod Artillery | 400 | 17500 | 55 | 12345 | 676 | Light | 0 | 0 | 1 | - |  |
| ra1_allies_alliedartillery | Allied Artillery | 600 | 20000 | 60 | 13350 | 812 | Light | 0 | 0 | 1 | - | **ANCHOR** |
| asianalliance_viper | Viper | 700 | 25000 | 125 | 10000 | 1210 | Light | 0 | 0 | 1 | - |  |
| naxis_grille | Grille | 800 | 40000 | 80 | 13333 | 1381 | Light | 0 | 0 | 1 | - |  |
| wc2_orcs_catapult | Catapult | 800 | 40000 | 40 | 13400 | 531 | Light | 0 | 0 | 1 | - |  |
| ra1_soviets_v1rockettruck | V1 Rocket Truck | 850 | 25000 | 100 | 9595 | 1538 | Light | 0 | 1 | 1 | - |  |
| ra2_soviets_v3rocketlauncher | V3 Rocket Launcher | 900 | 37500 | 75 | 20000 | 0 | Light | 0 | 0 | 1 | - |  |
| td_nod_specterartillery | Specter Artillery | 900 | 22500 | 100 | 12640 | 850 | Light | 0 | 0 | 1 | - |  |
| wc2_humans_ballista | Ballista | 900 | 45000 | 45 | 14450 | 542 | Light | 0 | 0 | 1 | - |  |
| steelconsortium_hammerheadartillerytank | Hammerhead Artillery Tank | 1000 | 52500 | 100 | 11111 | 762 | Medium | 0 | 0 | 1 | - |  |
| naxis_brummbar | Brummbär | 1100 | 90000 | 60 | 15000 | 1331 | Light | 0 | 0 | 1 | - | **VERIFIER** |
| japan_ballista | Ballista | 1150 | 65000 | 65 | 13515 | 1833 | Medium | 0 | 0 | 1 | - |  |
| td_nod_chemicalssmlauncher | Chemical SSM Launcher | 1200 | 32500 | 75 | 12345 | 1056 | Medium | 0 | 0 | 1 | - |  |
| tkm_tornadoglauncher | Tornado-G Launcher | 1200 | 35000 | 80 | 14000 | 4177 | Medium | 0 | 0 | 1 | - |  |
| cabal_artilleryspider | Artillery Spider | 1250 | 50000 | 70 | 11580 | 8414 | Light | 1 | 0 | 1 | - | hits AIR (§9 ground-only) |
| ordos_deviatorartillery | Deviator Artillery | 1250 | 55000 | 55 | 10025 | 990 | Medium | 0 | 0 | 1 | - |  |
| steelconsortium_dagger | Dagger | 1300 | 25000 | 100 | 25000 | 2040 | Light | 0 | 0 | 1 | - |  |
| ra1_soviets_v2rocketlauncher | V2 Rocket Launcher | 1600 | 30000 | 85 | 14110 | 3375 | Medium | 0 | 0 | 1 | - |  |
| tkm_dronepodtruck | Drone Pod Truck | 1600 | 60000 | 60 | 23589 | 0 | Light | 0 | 0 | 1 | - |  |
| latinsyndicate_burrito | Burrito | 1800 | 35000 | 80 | 12000 | 2347 | Medium | 0 | 0 | 1 | - |  |
| wc2_humans_siegeengine | Siege Engine | 1800 | 70000 | 70 | 11200 | 1858 | Medium | 0 | 0 | 1 | - |  |
| wc2_orcs_siegeengine | Siege Engine | 1800 | 70000 | 70 | 11200 | 1858 | Medium | 0 | 0 | 1 | - |  |
| ixian_ixsiegetank | Ix Siege Tank | 2050 | 60000 | 60 | 12000 | 1062 | Medium | 0 | 0 | 1 | - |  |
| futuretech_athenacannon | Athena Cannon | 2200 | 62500 | 60 | 16000 | 176000 | Medium | 0 | 0 | 1 | - |  |
| naxis_donnerschlag | Donnerschlag | 2300 | 80000 | 40 | 20130 | 0 | Medium | 1 | 0 | 1 | - | hits AIR (§9 ground-only) |
| ra1_soviets_nuclearv2launcher | Nuclear V2 Launcher | 2300 | 40000 | 80 | 12550 | 4950 | Medium | 0 | 0 | 1 | - |  |

## tank_destroyer  (5)  — target: cost 600, hp 150000, spd 70, rng 7500, dps 900

| actor | name | cost | hp | spd | rng | dps | armor | air | T | K | BL | flags |
|---|---|--:|--:|--:|--:|--:|---|:-:|:-:|:-:|:-:|---|
| ra1_allies_alliedtankdestroyer | Allied Tank Destroyer | 1200 | 120000 | 60 | 6819 | 400 | Medium | 0 | 0 | 1 | - |  |
| naxis_hetzer | Hetzer | 1300 | 75000 | 75 | 7132 | 1464 | Medium | 0 | 0 | 1 | - | **ANCHOR** |
| ra2_allies_tankdestroyer | Tank Destroyer | 1500 | 145000 | 65 | 8040 | 1875 | Heavy | 0 | 0 | 1 | - | **VERIFIER** |
| naxis_jagdpanzer | Jagdpanzer | 2000 | 125000 | 50 | 8396 | 2202 | Heavy | 0 | 0 | 1 | - |  |
| ordos_tankdestroyer | Tank Destroyer | 2200 | 80000 | 90 | 8500 | 681 | Medium | 0 | 0 | 1 | - |  |

## artillery_tank  (16)  — target: cost 700, hp 140000, spd 85, rng 12000, dps 525

| actor | name | cost | hp | spd | rng | dps | armor | air | T | K | BL | flags |
|---|---|--:|--:|--:|--:|--:|---|:-:|:-:|:-:|:-:|---|
| schwarzermond_lunargrille | Lunar Grille | 600 | 62500 | 90 | 13333 | 3186 | Medium | 0 | 1 | 1 | - | **VERIFIER** |
| td_gdi_archerartillery | Archer Artillery | 750 | 35000 | 70 | 14000 | 550 | Medium | 0 | 1 | 1 | - |  |
| forgotten_missilevan | actor_forgotten_missilevan.name | 1200 | 35000 | 75 | 10460 | 3000 | Light | 0 | 1 | 1 | - |  |
| ixian_ixcombatsiege | Ix Combat Siege | 1200 | 80000 | 80 | 8686 | 325 | Medium | 0 | 1 | 1 | - | **ANCHOR** |
| ts_nod_artillery | Artillery | 1300 | 30000 | 60 | 13083 | 1000 | Light | 0 | 1 | 1 | - |  |
| ra1_soviets_grad | Grad | 1400 | 50000 | 75 | 13820 | 1920 | Medium | 0 | 1 | 1 | - |  |
| ts_gdi_juggernaut | Juggernaut | 1400 | 35000 | 71 | 12834 | 1200 | Medium | 0 | 1 | 1 | - |  |
| ordos_cobratank | Cobra Tank | 1500 | 45000 | 45 | 7640 | 3000 | Heavy | 0 | 1 | 1 | - |  |
| asianalliance_howitzer | Howitzer | 1600 | 40000 | 60 | 20000 | 562 | Heavy | 0 | 1 | 1 | - |  |
| schwarzermond_mars | MARS | 2000 | 35000 | 70 | 17350 | 0 | Medium | 1 | 1 | 1 | - | hits AIR (§9 ground-only) |
| ts_gdi_juggernautmkii | Juggernaut MK II | 2200 | 50000 | 70 | 12860 | 1714 | Medium | 0 | 0 | 1 | - | no turret (arty_tank is turreted) |
| japan_waveforceartillery | Waveforce Artillery | 2500 | 50000 | 55 | 11111 | 0 | Light | 0 | 1 | 1 | - |  |
| naxis_sturmtiger | Sturm Tiger | 2500 | 250000 | 30 | 14000 | 619 | Heavy | 0 | 0 | 1 | - | no turret (arty_tank is turreted) |
| ordos_pythontank | Python Tank | 2500 | 70000 | 40 | 9380 | 3902 | Heavy | 0 | 1 | 1 | - |  |
| forgotten_mlrs | actor_forgotten_mlrs.name | 2750 | 40000 | 80 | 11913 | 6000 | Medium | 0 | 1 | 1 | - |  |
| terran_siegetank | Siege Tank | 2800 | 150000 | 75 | 11775 | 2167 | Heavy | 0 | 1 | 1 | - |  |

## mbt  (39)  — target: cost 800, hp 240000, spd 95, rng 5500, dps 600

| actor | name | cost | hp | spd | rng | dps | armor | air | T | K | BL | flags |
|---|---|--:|--:|--:|--:|--:|---|:-:|:-:|:-:|:-:|---|
| combat_tank.atreides | Combat Tank | 600 | 100000 | 75 | 5120 | 320 | Medium | 0 | 1 | 0 | - |  |
| combat_tank.harkonnen | Harkonnen Combat Tank | 600 | 70000 | 65 | 5120 | 145 | Medium | 0 | 1 | 0 | - |  |
| forgotten_rattytank | actor_forgotten_rattytank.name | 600 | 70000 | 90 | 5566 | 385 | Medium | 0 | 1 | 0 | - |  |
| ra1_allies_alliedmediumtank | Allied Medium Tank | 700 | 90000 | 100 | 5159 | 170 | Medium | 0 | 1 | 0 | - |  |
| tkm_technicaltank | Technical Tank | 700 | 70000 | 110 | 5316 | 612 | Medium | 1 | 1 | 0 | - | hits AIR (§9 ground-only) |
| ra2_allies_grizzlytank | Grizzly Tank | 750 | 100000 | 95 | 6289 | 511 | Medium | 0 | 1 | 0 | - |  |
| ixian_kodatank | Koda Tank | 800 | 65000 | 65 | 5555 | 429 | Medium | 0 | 1 | 0 | - |  |
| japan_igomediumtank | I-Go Medium Tank | 800 | 110000 | 90 | 5243 | 474 | Medium | 0 | 1 | 0 | - |  |
| tiger.nax | Tiger Heavy Tank | 800 | 100000 | 100 | 6000 | 577 | Heavy | 0 | 1 | 0 | - | **ANCHOR** |
| ts_nod_ticktank | Tick Tank | 800 | 100000 | 90 | 6754 | 2090 | Heavy | 1 | 1 | 0 | - | hits AIR (§9 ground-only) |
| asianalliance_lynxtank | Lynx Tank | 850 | 120000 | 90 | 6357 | 1136 | Medium | 0 | 1 | 0 | - |  |
| futuretech_guardiantank | Guardian Tank | 850 | 115000 | 85 | 8820 | 414 | Medium | 0 | 1 | 0 | - |  |
| ra2_soviets_rhinoheavytank | Rhino Heavy Tank | 850 | 130000 | 85 | 6374 | 2251 | Heavy | 0 | 1 | 0 | - |  |
| steelconsortium_mako | Mako | 900 | 95000 | 85 | 7050 | 2284 | Medium | 0 | 0 | 0 | - |  |
| td_gdi_battletank | GDI Battle Tank | 900 | 125000 | 80 | 5438 | 673 | Medium | 1 | 1 | 0 | - | hits AIR (§9 ground-only) |
| tkm_t72m | T-72M | 900 | 100000 | 80 | 6196 | 438 | Medium | 1 | 1 | 0 | - | hits AIR (§9 ground-only) |
| ordos_heavycombattank | Ordos Heavy Combat Tank | 950 | 115000 | 75 | 6000 | 484 | Heavy | 1 | 1 | 0 | - | hits AIR (§9 ground-only) |
| schwarzermond_lunartiger | Lunar Tiger | 950 | 160000 | 80 | 6105 | 1317 | Heavy | 0 | 1 | 0 | - |  |
| ts_gdi_titan | Titan | 950 | 100000 | 75 | 6201 | 682 | Heavy | 0 | 1 | 0 | - |  |
| cabal_tarantula | Tarantula | 1000 | 110000 | 70 | 6201 | 879 | Heavy | 0 | 1 | 0 | - |  |
| ra1_soviets_heavytank | Soviet Heavy Tank | 1000 | 150000 | 70 | 5469 | 543 | Heavy | 0 | 1 | 0 | - |  |
| tkm_abrams | Abrams | 1000 | 120000 | 80 | 5672 | 261 | Medium | 0 | 1 | 0 | - |  |
| ixian_heavykodatank | Heavy Koda Tank | 1100 | 95000 | 58 | 6000 | 562 | Heavy | 0 | 1 | 0 | - |  |
| japan_chihaheavytank | Chi-Ha Heavy Tank | 1200 | 130000 | 85 | 5692 | 491 | Heavy | 0 | 1 | 0 | - |  |
| protoss_dragoon | Dragoon | 1200 | 75000 | 80 | 5000 | 1083 | Medium | 1 | 0 | 0 | - | hits AIR (§9 ground-only) |
| td_gdi_predatortank | Predator Tank | 1250 | 170000 | 70 | 5880 | 686 | Heavy | 1 | 1 | 0 | - | hits AIR (§9 ground-only) |
| ixian_mongoose | Mongoose | 1300 | 75000 | 75 | 6183 | 521 | Medium | 1 | 1 | 0 | - | hits AIR (§9 ground-only) |
| ra1_allies_alliedtigerheavytank | Allied Tiger Heavy Tank | 1300 | 160000 | 75 | 5915 | 300 | Heavy | 0 | 1 | 0 | - |  |
| ordos_combatautoguntank | Combat Autogun Tank | 1500 | 95000 | 80 | 6220 | 1760 | Medium | 1 | 1 | 0 | - | hits AIR (§9 ground-only) |
| ra1_soviets_hammertank | Hammer Tank | 1500 | 210000 | 60 | 6825 | 764 | Heavy | 0 | 1 | 0 | - |  |
| steelconsortium_quantumtank | Quantum Tank | 1600 | 100000 | 100 | 7000 | 1415 | Heavy | 0 | 1 | 0 | - |  |
| ts_gdi_titanmkii | Titan MK II | 1600 | 120000 | 75 | 6201 | 1290 | Heavy | 0 | 1 | 0 | - |  |
| terran_matador | Matador | 1700 | 100000 | 100 | 6590 | 2678 | Medium | 1 | 1 | 0 | - | hits AIR (§9 ground-only) |
| latinsyndicate_smokertank | Smoker Tank | 1800 | 260000 | 95 | 7550 | 1869 | Heavy | 1 | 1 | 0 | - | hits AIR (§9 ground-only) |
| ra1_soviets_kotinnucleartank | Kotin Nuclear Tank | 1800 | 240000 | 65 | 6427 | 630 | Heavy | 0 | 1 | 0 | - |  |
| naxis_kingtigerheavytank | King Tiger Heavy Tank | 2000 | 200000 | 100 | 6000 | 1155 | Heavy | 0 | 1 | 0 | - | **VERIFIER** |
| ptnk.asian | Plasma Tank | 2400 | 130000 | 50 | 8888 | 2667 | Heavy | 0 | 1 | 0 | - |  |
| tkm_trenchtank | Trench Tank | 2500 | 200000 | 65 | 9237 | 600 | Heavy | 0 | 1 | 0 | - |  |
| cabal_widow | Widow | 3500 | 120000 | 60 | 6813 | 2625 | Medium | 0 | 0 | 0 | - |  |

## anti_air_vehicle  (13)  — target: cost 1000, hp 125000, spd 110, rng 6000, dps 1250

| actor | name | cost | hp | spd | rng | dps | armor | air | T | K | BL | flags |
|---|---|--:|--:|--:|--:|--:|---|:-:|:-:|:-:|:-:|---|
| japan_armoredcar | Armored Car | 700 | 42500 | 130 | 7518 | 8583 | Medium | 1 | 1 | 0 | - |  |
| ra1_soviets_flaktruck | Flak Truck | 800 | 30000 | 120 | 8118 | 3200 | Medium | 1 | 1 | 0 | - |  |
| naxis_kubelwagen | Kübelwagen | 850 | 50000 | 115 | 5757 | 210 | Light | 1 | 1 | 0 | - |  |
| ra2_soviets_flaktrack | Flak Track | 900 | 45000 | 95 | 9292 | 1862 | Medium | 1 | 1 | 0 | - |  |
| forgotten_m113adats | actor_forgotten_m113adats.name | 950 | 50000 | 70 | 8409 | 1867 | Light | 1 | 1 | 0 | - |  |
| ra1_soviets_gatlingtank | Gatling Tank | 1100 | 75000 | 75 | 7500 | 1900 | Medium | 1 | 1 | 0 | - |  |
| steelconsortium_barracuda | Barracuda | 1100 | 40000 | 80 | 12000 | 4000 | Medium | 1 | 1 | 0 | - | **VERIFIER** |
| yuri_gatlingtank | Yuri Gatling Tank | 1100 | 45000 | 90 | 8250 | 9625 | Light | 1 | 1 | 0 | - |  |
| latinsyndicate_diablo | Diablo | 1200 | 45000 | 125 | 10450 | 2461 | Light | 1 | 1 | 0 | - | **ANCHOR** |
| ra1_allies_alliedheavyaatank | Allied Heavy AA Tank | 1250 | 125000 | 75 | 7119 | 1400 | Heavy | 1 | 1 | 1 | - |  |
| asianalliance_pulverizer | Pulverizer | 1400 | 85000 | 65 | 5517 | 1000 | Medium | 1 | 1 | 0 | - |  |
| tkm_flakbus | Flak Bus | 1800 | 120000 | 60 | 0 | 0 | Heavy | 0 | 0 | 0 | - | NO air (should hit air!) |
| wirbelwind.nax | Wirbelwind | 1800 | 87500 | 85 | 9052 | 3082 | Medium | 1 | 1 | 0 | - |  |

## missile_vehicle  (10)  — target: cost 1200, hp 120000, spd 100, rng 8000, dps 1200

| actor | name | cost | hp | spd | rng | dps | armor | air | T | K | BL | flags |
|---|---|--:|--:|--:|--:|--:|---|:-:|:-:|:-:|:-:|---|
| td_nod_reconbike | Recon Bike | 500 | 17500 | 200 | 6000 | 451 | Light | 1 | 1 | 1 | - |  |
| ts_nod_attackcycle | Attack Cycle | 550 | 20000 | 170 | 6554 | 1089 | Light | 1 | 0 | 1 | - |  |
| missile_tank | Missile Tank | 750 | 50000 | 64 | 10240 | 356 | Medium | 1 | 0 | 1 | - |  |
| td_nod_chemicalattackbike | Chemical Attack Bike | 750 | 22500 | 175 | 6000 | 733 | Light | 1 | 1 | 1 | - |  |
| ts_gdi_hovermlrs | Hover MLRS | 900 | 30000 | 80 | 8159 | 353 | Medium | 1 | 1 | 1 | - | **ANCHOR** |
| td_gdi_mlrs | GDI MLRS | 1000 | 25000 | 80 | 9920 | 750 | Light | 1 | 1 | 1 | - |  |
| asianalliance_type89mlrs | Type 89 MLRS | 1200 | 40000 | 80 | 8500 | 531 | Medium | 1 | 1 | 1 | - |  |
| latinsyndicate_lars | LARS | 1300 | 47500 | 70 | 10130 | 1143 | Medium | 1 | 0 | 1 | - |  |
| ixian_ixmissiletank | Ix Missile Tank | 2250 | 50000 | 50 | 10052 | 4800 | Light | 1 | 0 | 1 | - |  |
| terran_cyclone | Cyclone | 2300 | 90000 | 115 | 10000 | 933 | Light | 1 | 1 | 1 | - | **VERIFIER** |

## fire_support  (34)  — target: cost 1400, hp 105000, spd 90, rng 10000, dps 2100

| actor | name | cost | hp | spd | rng | dps | armor | air | T | K | BL | flags |
|---|---|--:|--:|--:|--:|--:|---|:-:|:-:|:-:|:-:|---|
| cabal_mantis | Mantis | 500 | 35000 | 120 | 7082 | 262 | Scout | 0 | 0 | 1 | - |  |
| ts_gdi_wolverine | Wolverine | 550 | 30000 | 80 | 6305 | 569 | Light | 1 | 0 | 1 | - | hits AIR (§9 ground-only); short rng=6305 (FS≈10000) |
| td_nod_ssmlauncher | SSM Launcher | 800 | 20000 | 100 | 8940 | 420 | Light | 0 | 1 | 1 | - |  |
| forgotten_tankkiller | actor_forgotten_tankkiller.name | 900 | 85000 | 65 | 7701 | 792 | Medium | 0 | 0 | 1 | - |  |
| td_nod_stealthtank | Stealth Tank | 900 | 25000 | 150 | 7432 | 727 | Light | 1 | 0 | 1 | - | hits AIR (§9 ground-only) |
| naxis_imperialturbotank | Imperial Turbo Tank | 950 | 82500 | 110 | 7396 | 1752 | Medium | 0 | 0 | 1 | - |  |
| ts_gdi_wolverinemkii | Wolverine MK II | 950 | 50000 | 80 | 6520 | 1062 | Medium | 1 | 0 | 1 | - | hits AIR (§9 ground-only); short rng=6520 (FS≈10000) |
| futuretech_energizer | Energizer | 1000 | 50000 | 50 | 7500 | 400 | Light | 0 | 1 | 1 | - |  |
| latinsyndicate_missiletruck | Missile Truck | 1000 | 30000 | 75 | 7777 | 930 | Light | 0 | 0 | 1 | - | **ANCHOR** |
| zerg_sporemaw | Sporemaw | 1000 | 25000 | 80 | 7740 | 478 | Light | 1 | 0 | 1 | - | hits AIR (§9 ground-only) |
| cabal_laserspider | Laser Spider | 1200 | 40000 | 70 | 6147 | 489 | Light | 0 | 0 | 1 | - | short rng=6147 (FS≈10000) |
| japan_nanodronebuggy | Nanodrone Buggy | 1200 | 37500 | 77 | 7777 | 328 | Light | 0 | 1 | 1 | - |  |
| td_gdi_exosuit | Exosuit | 1200 | 50000 | 100 | 6806 | 625 | Medium | 0 | 0 | 1 | - | short rng=6806 (FS≈10000) |
| yuri_magnetron | Magnetron | 1300 | 65000 | 65 | 8032 | 2676 | Light | 1 | 1 | 1 | - | hits AIR (§9 ground-only) |
| zerg_lurker | Lurker | 1300 | 125000 | 90 | 6666 | 0 | Heavy | 1 | 1 | 1 | - | hits AIR (§9 ground-only); short rng=6666 (FS≈10000) |
| naxis_nop03sarubia | Nop-03 Sarubia | 1400 | 62500 | 65 | 7800 | 0 | Medium | 0 | 0 | 1 | - |  |
| ordos_dustdrone | Dust Drone | 1400 | 32500 | 145 | 6500 | 500 | Light | 1 | 0 | 1 | - | hits AIR (§9 ground-only); short rng=6500 (FS≈10000) |
| asianalliance_railguntank | Railgun Tank | 1500 | 160000 | 65 | 10000 | 1100 | Medium | 0 | 0 | 1 | - |  |
| cabal_spidercnc4 | Spider CNC4 | 1500 | 40000 | 70 | 7000 | 550 | Light | 0 | 0 | 1 | - |  |
| tkm_stryker | TKM Stryker | 1600 | 80000 | 105 | 7880 | 1300 | Light | 1 | 1 | 1 | - | hits AIR (§9 ground-only) |
| ra1_soviets_teslatank | Tesla Tank | 1700 | 40000 | 80 | 7300 | 1500 | Light | 0 | 1 | 1 | - |  |
| schwarzermond_crystaltank | Crystal Tank | 1700 | 400000 | 60 | 8420 | 1111 | Medium | 0 | 1 | 1 | - |  |
| japan_waveforcetank | Waveforce Tank | 1800 | 60000 | 60 | 9343 | 1021 | Medium | 1 | 1 | 1 | - | hits AIR (§9 ground-only) |
| ra2_soviets_teslatank | Tesla Tank | 1800 | 75000 | 75 | 8500 | 1200 | Medium | 0 | 1 | 1 | - |  |
| ra1_soviets_heatraytank | Heatray Tank | 1900 | 60000 | 60 | 8212 | 2750 | Medium | 0 | 1 | 1 | - |  |
| forgotten_warriortank | actor_forgotten_warriortank.name | 2000 | 100000 | 75 | 8207 | 1727 | Medium | 0 | 1 | 1 | - |  |
| ra2_allies_prismtank | Prism Tank | 2000 | 60000 | 60 | 12345 | 960 | Light | 0 | 1 | 1 | - |  |
| futuretech_beehivedronecarrier | Beehive Drone Carrier | 2100 | 125000 | 45 | 17500 | 0 | Heavy | 1 | 1 | 1 | - | hits AIR (§9 ground-only) |
| asianalliance_heavyrailguntank | Heavy Railgun Tank | 2200 | 250000 | 50 | 11111 | 1267 | Heavy | 0 | 0 | 1 | - |  |
| ixian_stormraider | Storm Raider | 2200 | 60000 | 95 | 7343 | 1250 | Medium | 1 | 1 | 1 | - | hits AIR (§9 ground-only) |
| futuretech_gunstrider | Gun Strider | 2500 | 320000 | 35 | 8300 | 611 | Heavy | 1 | 0 | 1 | - | hits AIR (§9 ground-only) |
| protoss_reaver | Reaver | 2700 | 275000 | 40 | 7777 | 2500 | Heavy | 0 | 0 | 1 | - |  |
| naxis_nokana | Nokana | 3000 | 450000 | 60 | 7000 | 2358 | Heavy | 1 | 0 | 1 | 1 | BuildLimit1→epic? (§18.1); hits AIR (§9 ground-only) |
| schwarzermond_korruptesbiest | Korruptes Biest | 3500 | 240000 | 40 | 8984 | 2708 | Heavy | 1 | 0 | 1 | - | hits AIR (§9 ground-only) |

## line_breaker  (30)  — target: cost 1600, hp 800000, spd 80, rng 2500, dps 1600

| actor | name | cost | hp | spd | rng | dps | armor | air | T | K | BL | flags |
|---|---|--:|--:|--:|--:|--:|---|:-:|:-:|:-:|:-:|---|
| td_nod_flametank | Nod Flame Tank | 800 | 100000 | 80 | 2390 | 467 | Heavy | 0 | 0 | 0 | - | **ANCHOR** |
| wc2_humans_demolitionsquad | Demolition Squad | 800 | 40000 | 80 | 1536 | 600 | Heavy | 0 | 0 | 0 | - |  |
| wc2_orcs_goblinsappers | Goblin Sappers | 800 | 40000 | 80 | 1536 | 600 | Heavy | 0 | 0 | 0 | - |  |
| forgotten_closhtank | actor_forgotten_closhtank.name | 1000 | 120000 | 80 | 2386 | 1400 | Heavy | 0 | 0 | 0 | - |  |
| ts_nod_devilstongue | Devil's Tongue | 1150 | 100000 | 70 | 4250 | 667 | Heavy | 0 | 0 | 0 | - | long rng=4250 (LB≈2500 brawler) |
| tkm_battlebus | Battle Bus | 1250 | 50000 | 100 | 4831 | -900 | Medium | 0 | 0 | 0 | - | long rng=4831 (LB≈2500 brawler); armor=Medium (LB=super/heavy) |
| asianalliance_asianflametank | Asian Flame Tank | 1300 | 85000 | 85 | 4700 | 1071 | Medium | 0 | 0 | 0 | - | long rng=4700 (LB≈2500 brawler); armor=Medium (LB=super/heavy) |
| forgotten_flametank | actor_forgotten_flametank.name | 1300 | 200000 | 80 | 2425 | 1731 | Heavy | 0 | 0 | 0 | - |  |
| td_nod_flametankmkii | Flame Tank Mk. II | 1300 | 200000 | 75 | 2534 | 781 | Superheavy | 0 | 1 | 0 | - | **VERIFIER** |
| ts_gdi_mobileemp | Mobile EMP | 1400 | 150000 | 100 | 1512 | 320 | Heavy | 0 | 1 | 0 | - |  |
| wc2_humans_paladin | Paladin | 1600 | 167500 | 115 | 512000 | 1000 | Medium | 0 | 0 | 0 | - | long rng=512000 (LB≈2500 brawler); armor=Medium (LB=super/heavy) |
| wc2_orcs_ogremage | Ogre-Mage | 1800 | 200000 | 85 | 5120 | 1125 | Heavy | 0 | 0 | 0 | - | long rng=5120 (LB≈2500 brawler) |
| naxis_oldtank | Old Tank | 2000 | 110000 | 50 | 7361 | 373 | Medium | 0 | 0 | 0 | - | long rng=7361 (LB≈2500 brawler); armor=Medium (LB=super/heavy) |
| wc2_humans_warcraft3knight | Warcraft 3 Knight | 2200 | 180000 | 120 | 512000 | 1000 | Medium | 0 | 0 | 0 | - | long rng=512000 (LB≈2500 brawler); armor=Medium (LB=super/heavy) |
| ts_gdi_disruptor | Disruptor | 2400 | 250000 | 50 | 4050 | 200 | Heavy | 1 | 1 | 0 | - | hits AIR (§9 ground-only); long rng=4050 (LB≈2500 brawler) |
| cabal_beholder | Beholder | 2500 | 125000 | 125 | 2500 | 1636 | Heavy | 0 | 0 | 0 | - |  |
| futuretech_plasmastrider | Plasma Strider | 2600 | 240000 | 40 | 8000 | 3083 | Heavy | 0 | 0 | 0 | - | long rng=8000 (LB≈2500 brawler) |
| ordos_heavyautoguntank | Heavy Autogun Tank | 2800 | 160000 | 75 | 7480 | 1760 | Heavy | 1 | 1 | 0 | - | hits AIR (§9 ground-only); long rng=7480 (LB≈2500 brawler) |
| latinsyndicate_tortugatank | Tortuga Tank | 3000 | 875000 | 45 | 7000 | 3099 | Heavy | 1 | 1 | 0 | - | hits AIR (§9 ground-only); long rng=7000 (LB≈2500 brawler) |
| ra2_allies_battlefortress | Battle Fortress | 4000 | 320000 | 60 | 5000 | 467 | Heavy | 0 | 0 | 0 | - | long rng=5000 (LB≈2500 brawler) |
| ra2_allies_battlefortress_chrono | Battle Fortress | 4000 | 320000 | 60 | 5000 | 467 | Heavy | 0 | 0 | 0 | - | long rng=5000 (LB≈2500 brawler) |
| ra2_allies_battlefortress_empty | Battle Fortress | 4000 | 320000 | 60 | 5000 | 467 | Heavy | 0 | 0 | 0 | - | long rng=5000 (LB≈2500 brawler) |
| steelconsortium_poseidontank | Poseidon Tank | 4000 | 125000 | 50 | 6333 | 683 | Heavy | 0 | 0 | 0 | - | long rng=6333 (LB≈2500 brawler) |
| td_gdi_assaultapc | Assault APC | 4500 | 250000 | 100 | 8397 | 667 | Heavy | 1 | 1 | 0 | - | hits AIR (§9 ground-only); long rng=8397 (LB≈2500 brawler) |
| steelconsortium_megalodon | Megalodon | 4600 | 450000 | 65 | 2400 | 16719 | Superheavy | 0 | 0 | 0 | - |  |
| asianalliance_warturtle | War Turtle | 5000 | 250000 | 75 | 4567 | 87 | Medium | 0 | 0 | 0 | - | long rng=4567 (LB≈2500 brawler); armor=Medium (LB=super/heavy) |
| forgotten_thumperbus | actor_forgotten_thumperbus.name | 5200 | 200000 | 90 | 7850 | 1800 | Heavy | 0 | 0 | 0 | - | long rng=7850 (LB≈2500 brawler) |
| protoss_archon | Archon | 5600 | 350000 | 75 | 3152 | 1500 | Medium | 1 | 0 | 0 | - | hits AIR (§9 ground-only); armor=Medium (LB=super/heavy) |
| latinsyndicate_carteltruck | Cartel Truck | 6000 | 167500 | 70 | 6800 | 2191 | Heavy | 0 | 1 | 0 | - | long rng=6800 (LB≈2500 brawler) |
| cabal_berserker | Berserker | 10000 | 800000 | 60 | 2048 | 4162 | Heavy | 0 | 0 | 0 | 1 | BuildLimit1→epic? (§18.1) |

## high_tech_tank  (26)  — target: cost 2000, hp 700000, spd 65, rng 6500, dps 2000

| actor | name | cost | hp | spd | rng | dps | armor | air | T | K | BL | flags |
|---|---|--:|--:|--:|--:|--:|---|:-:|:-:|:-:|:-:|---|
| yuri_mastermind | Master Mind | 1500 | 100000 | 120 | 7000 | 0 | Heavy | 0 | 1 | 0 | - | armor=Heavy (HT=superheavy) |
| zerg_goremaw | Goremaw | 1500 | 150000 | 150 | 1250 | 750 | Medium | 0 | 0 | 0 | - | armor=Medium (HT=superheavy) |
| ordos_deviatortank | Deviator Tank | 1600 | 85000 | 115 | 7070 | 442 | Medium | 1 | 1 | 0 | - | armor=Medium (HT=superheavy) |
| ra2_allies_miragetank | Mirage Tank | 1600 | 120000 | 90 | 7031 | 1978 | Medium | 0 | 1 | 0 | - | armor=Medium (HT=superheavy) |
| td_gdi_mammothtank | GDI Mammoth Tank | 1600 | 225000 | 60 | 6141 | 1250 | Heavy | 1 | 1 | 0 | - | **ANCHOR** armor=Heavy (HT=superheavy) |
| terran_goliath | Goliath | 1600 | 125000 | 90 | 6000 | 3655 | Medium | 1 | 1 | 0 | - | armor=Medium (HT=superheavy) |
| japan_hovercraftflametank | Hovercraft Flametank | 1700 | 120000 | 90 | 6000 | 2360 | Medium | 0 | 1 | 0 | - | armor=Medium (HT=superheavy) |
| ra2_soviets_apocalypsetank | Apocalypse Tank | 1750 | 350000 | 55 | 7992 | 5924 | Superheavy | 1 | 1 | 0 | - |  |
| ts_nod_stealthtank | Stealth Tank | 1750 | 80000 | 100 | 6385 | 1613 | Heavy | 1 | 0 | 0 | - | armor=Heavy (HT=superheavy) |
| duelist_tank.ixian | Ix Duelist Tank | 1800 | 240000 | 45 | 7000 | 2358 | Heavy | 1 | 1 | 0 | - | armor=Heavy (HT=superheavy) |
| td_nod_chemicalstealthtank | Chemical Stealth Tank | 1800 | 90000 | 120 | 6962 | 500 | Medium | 1 | 1 | 0 | - | armor=Medium (HT=superheavy) |
| ra1_soviets_mammothtank | Soviet Mammoth Tank | 2000 | 375000 | 50 | 6412 | 5689 | Superheavy | 1 | 1 | 0 | - |  |
| ra2_allies_heavymiragetank | Heavy Mirage Tank | 2000 | 240000 | 60 | 7112 | 1964 | Heavy | 0 | 1 | 0 | - | armor=Heavy (HT=superheavy) |
| forgotten_scoopertank | actor_forgotten_scoopertank.name | 2250 | 250000 | 65 | 6224 | 1613 | Heavy | 0 | 1 | 0 | - | armor=Heavy (HT=superheavy) |
| futuretech_oriontank | Orion Tank | 2400 | 180000 | 60 | 9000 | 3750 | Heavy | 0 | 1 | 0 | - | armor=Heavy (HT=superheavy) |
| ordos_lasertank | Laser Tank | 2400 | 105000 | 105 | 7275 | 773 | Medium | 1 | 1 | 0 | - | armor=Medium (HT=superheavy) |
| protoss_atreus | Atreus | 2400 | 250000 | 60 | 4500 | 1050 | Medium | 1 | 0 | 0 | - | armor=Medium (HT=superheavy) |
| terran_goliathmk2 | Goliath Mk2 | 2400 | 175000 | 75 | 6479 | 3200 | Medium | 1 | 1 | 0 | - | armor=Medium (HT=superheavy) |
| naxis_shoekarn | Shoe Karn | 2500 | 150000 | 75 | 12345 | 1109 | Heavy | 0 | 1 | 0 | - | armor=Heavy (HT=superheavy) |
| td_gdi_mammothtankmkiii | Mammoth Tank Mk. III | 3000 | 500000 | 55 | 6340 | 1364 | Superheavy | 1 | 1 | 0 | - |  |
| ra1_soviets_heavyteslatank | Heavy Tesla Tank | 3500 | 150000 | 60 | 6650 | 2000 | Medium | 1 | 1 | 0 | - | armor=Medium (HT=superheavy) |
| steelconsortium_katytank | Katy Tank | 3800 | 275000 | 45 | 8250 | 7590 | Superheavy | 0 | 1 | 0 | - |  |
| ra1_soviets_siegemammothtank | Siege Mammoth Tank | 4000 | 625000 | 45 | 6666 | 6957 | Superheavy | 1 | 1 | 0 | - | **VERIFIER** |
| naxis_maus | Maus | 4200 | 600000 | 60 | 7777 | 1872 | Superheavy | 0 | 1 | 0 | - |  |
| japan_oitank | O-I Tank | 7000 | 650000 | 50 | 5394 | 5766 | Superheavy | 0 | 0 | 0 | - |  |
| cabal_avatar | Avatar | 7500 | 1000000 | 25 | 6332 | 2286 | Medium | 0 | 0 | 0 | - | armor=Medium (HT=superheavy) |

## dreadnought  (4)  — target: cost 3000, hp 1200000, spd 50, rng 7000, dps 3750

| actor | name | cost | hp | spd | rng | dps | armor | air | T | K | BL | flags |
|---|---|--:|--:|--:|--:|--:|---|:-:|:-:|:-:|:-:|---|
| asianalliance_pulverizermecha | Pulverizer Mecha | 3000 | 285000 | 55 | 7020 | 1333 | Superheavy | 1 | 0 | 1 | - | hits AIR (§9 ground-only) |
| ixian_neocymek | Neo Cymek | 4500 | 300000 | 45 | 6787 | 2636 | Heavy | 1 | 1 | 1 | - | **VERIFIER** hits AIR (§9 ground-only); armor=Heavy (Dread=superheavy) |
| schwarzermond_neojagdpanzer | Neo Jagdpanzer | 4500 | 450000 | 45 | 8379 | 7543 | Superheavy | 0 | 1 | 1 | - |  |
| terran_warhound | Warhound | 4500 | 300000 | 45 | 7156 | 1483 | Heavy | 1 | 0 | 1 | - | **ANCHOR** hits AIR (§9 ground-only); armor=Heavy (Dread=superheavy) |

## epic_vehicle  (23)  — target: cost 10000, hp 5000000, spd 60, rng 8500, dps 10000

| actor | name | cost | hp | spd | rng | dps | armor | air | T | K | BL | flags |
|---|---|--:|--:|--:|--:|--:|---|:-:|:-:|:-:|:-:|---|
| ra1_allies_chronotank | Chrono Tank | 2000 | 75000 | 100 | 6102 | 5333 | Medium | 1 | 0 | 0 | 1 |  |
| protoss_idol | Idol | 2800 | 350000 | 40 | 9343 | 604 | Medium | 1 | 0 | 0 | 1 |  |
| latinsyndicate_nuketruck | Nuke Truck | 3000 | 60000 | 100 | 2000 | 0 | Light | 0 | 0 | 0 | 1 |  |
| ra1_soviets_madtank | MAD Tank | 3000 | 300000 | 60 | 2500 | 0 | Heavy | 0 | 0 | 0 | 1 |  |
| ts_gdi_mammothprototype | Mammoth Prototype | 4000 | 800000 | 50 | 9332 | 3565 | Superheavy | 1 | 0 | 0 | 1 |  |
| forgotten_chemicalmammothtank | actor_forgotten_chemicalmammothtank.name | 5000 | 400000 | 60 | 6172 | 6155 | Superheavy | 1 | 1 | 0 | 1 |  |
| ixian_ixprojector | Ix Projector | 5000 | 100000 | 100 | 20000 | 0 | Medium | 0 | 0 | 0 | 1 |  |
| td_gdi_defenserig | GDI Defense Rig | 5000 | 400000 | 60 | 9350 | 10129 | Superheavy | 1 | 0 | 0 | 1 |  |
| tkm_bigshiee | Big Shiee | 5000 | 500000 | 50 | 7238 | 37839 | Superheavy | 1 | 0 | 0 | 1 |  |
| tkm_sandmarine | Sand Marine | 5000 | 800000 | 30 | 6464 | 37653 | Superheavy | 1 | 0 | 0 | 1 |  |
| tkm_t30 | T-30 | 5000 | 400000 | 50 | 22000 | 1250 | Superheavy | 0 | 1 | 0 | 1 |  |
| forgotten_experimentalmammothtank | actor_forgotten_experimentalmammothtank.name | 6000 | 1000000 | 50 | 5677 | 7757 | Superheavy | 1 | 1 | 0 | 1 |  |
| latinsyndicate_topolm | Topol-M | 6000 | 100000 | 75 | 32000 | 400 | Medium | 0 | 0 | 0 | 1 |  |
| zerg_hermit | Hermit | 6000 | 375000 | 50 | 7120 | 2083 | Superheavy | 1 | 0 | 0 | 1 |  |
| forgotten_nomadbarracks | actor_forgotten_nomadbarracks.name | 6500 | 650000 | 65 | 8301 | 1333 | Superheavy | 0 | 1 | 0 | 1 |  |
| naxis_ratte | Ratte | 8000 | 2000000 | 35 | 9052 | 7582 | Superheavy | 1 | 1 | 0 | 1 |  |
| ts_gdi_mammothmkii | Mammoth MK. II | 8000 | 1200000 | 50 | 9388 | 7667 | Superheavy | 1 | 0 | 0 | 1 |  |
| schwarzermond_dalek | Dalek | 9000 | 325000 | 65 | 9060 | 12829 | Superheavy | 0 | 0 | 0 | 1 |  |
| futuretech_futuretank | Future Tank | 10000 | 650000 | 45 | 8500 | 48300 | Heavy | 0 | 1 | 0 | 1 |  |
| japan_exorcistoitank | Exorcist O-I Tank | 10000 | 750000 | 50 | 5394 | 8311 | Superheavy | 1 | 0 | 0 | 1 |  |
| japan_shogunexecutioner | Shogun Executioner | 10000 | 3000000 | 65 | 3000 | 1500 | Superheavy | 1 | 0 | 0 | 1 |  |
| ra1_soviets_monstertank | Monster Tank | 10000 | 1000000 | 45 | 7833 | 16098 | Superheavy | 1 | 1 | 0 | 1 | **ANCHOR** |
| cabal_coredefender | Core Defender | 15000 | 2000000 | 50 | 6332 | 4571 | Superheavy | 0 | 0 | 0 | 1 |  |
