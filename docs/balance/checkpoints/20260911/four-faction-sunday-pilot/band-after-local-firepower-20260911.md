# Baseband validator (BALANCE_PIPELINE §8.1)

band: floor 75% - sweet 100%–250% - ceil 350%

Unresolved cargo passenger-sum checks (3): td_gdi_landingcraft (filled weight 0/10), td_nod_chinooktransport (filled weight 11/8), td_nod_transportsubmarine (filled weight 0/5)
These carriers need named full-load valuations; combat class prices are not used for them.

## Authored mixed cargo loads

Static passenger-sum check; tier suitability and runtime loading remain separate.

| Actor | Current cost | Passenger sum | Combat stat budget (K 1.25) |
|---|---:|---:|---:|
| ra1_allies_alliedchinooktransport | 3600.0 | 3914 | None |
| ra1_allies_phasetransport | 1800.0 | 1957 | 1565.6 |
| ra1_soviets_hiptransport | 2500.0 | 2500 | None |
| ra1_soviets_btr80 | 1600.0 | 1622 | 1297.6 |
| ra1_soviets_flaktruck | 800.0 | 800 | 640.0 |
| ra1_allies_alliedapc | 1300.0 | 1300 | 1040.0 |
| td_gdi_chinooktransport | 3000.0 | 3932 | None |
| td_gdi_apc | 1200.0 | 1400 | 1120.0 |
| td_gdi_assaultapc | 4500.0 | 3932 | 3145.6 |
| td_gdi_humveemkii | 600.0 | 700 | 560.0 |
| td_nod_buggymkii | 500.0 | 600 | 480.0 |

8 cargo price mismatches; no price writeback.

## `anti_air_vehicle` — 2 members - sweet-spot 0/2 (0%) - signed_off=False
  !! below 75% floor (too weak/price): ra1_soviets_gatlingtank, ra1_allies_alliedheavyaatank

## `artillery` — 7 members - sweet-spot 3/7 (43%) - signed_off=False
  !! below 75% floor (too weak/price): td_nod_artillery, td_nod_specterartillery, ra1_allies_alliedartillery

## `artillery_tank` — 2 members - sweet-spot 0/2 (0%) - signed_off=False
  !! below 75% floor (too weak/price): td_gdi_archerartillery

## `closecombat` — 1 members - sweet-spot 1/1 (100%) - signed_off=False

## `commando` — 6 members - sweet-spot 3/6 (50%) - signed_off=False

## `epic_vehicle` — 2 members - sweet-spot 0/2 (0%) - signed_off=False

## `fire_support` — 4 members - sweet-spot 0/4 (0%) - signed_off=False
  !! below 75% floor (too weak/price): td_gdi_exosuit, ra1_soviets_teslatank, td_nod_ssmlauncher, ra1_soviets_heatraytank

## `grenadier` — 4 members - sweet-spot 2/4 (50%) - signed_off=False
  !! above 350% ceil (needs tech-tier gate): td_gdi_empgrenadier

## `heavy_infantry` — 5 members - sweet-spot 3/5 (60%) - signed_off=False
  !! below 75% floor (too weak/price): ra1_soviets_flamethrower

## `heavy_sniper` — 2 members - sweet-spot 2/2 (100%) - signed_off=False

## `high_tech_tank` — 6 members - sweet-spot 1/6 (17%) - signed_off=False
  !! below 75% floor (too weak/price): td_gdi_mammothtankmkiii, ra1_soviets_mammothtank, td_gdi_mammothtank

## `light_tank` — 4 members - sweet-spot 0/4 (0%) - signed_off=False
  !! below 75% floor (too weak/price): ra1_allies_alliedlighttank, ra1_allies_sheridanassaulttank, td_nod_lighttank

## `line_breaker` — 3 members - sweet-spot 0/3 (0%) - signed_off=False
  !! below 75% floor (too weak/price): ra1_soviets_gorynychtank, td_nod_flametankmkii, td_nod_flametank

## `mbt` — 7 members - sweet-spot 0/7 (0%) - signed_off=False
  !! below 75% floor (too weak/price): ra1_allies_alliedmediumtank, ra1_soviets_heavytank, td_gdi_battletank, ra1_allies_alliedtigerheavytank, td_gdi_predatortank, ra1_soviets_hammertank, ra1_soviets_kotinnucleartank

## `melee` — 2 members - sweet-spot 0/2 (0%) - signed_off=False

## `missile_vehicle` — 4 members - sweet-spot 0/4 (0%) - signed_off=False
  !! below 75% floor (too weak/price): td_nod_stealthtank, td_gdi_mlrs, td_nod_reconbike, td_nod_chemicalattackbike

## `mortar` — 1 members - sweet-spot 0/1 (0%) - signed_off=False
  !! below 75% floor (too weak/price): ra1_soviets_mortarsoldier

## `pure_sniper` — 2 members - sweet-spot 1/2 (50%) - signed_off=False
  !! above 350% ceil (needs tech-tier gate): ra1_soviets_commissar

## `rocket_trooper` — 6 members - sweet-spot 4/6 (67%) - signed_off=False

## `scout` — 5 members - sweet-spot 4/5 (80%) - signed_off=False

## `scout_vehicle` — 3 members - sweet-spot 2/3 (67%) - signed_off=False

## `special_forces` — 4 members - sweet-spot 0/4 (0%) - signed_off=False
  !! above 350% ceil (needs tech-tier gate): td_nod_stealthsoldier, ra1_allies_machinegunner, td_gdi_officer

## `tank_destroyer` — 1 members - sweet-spot 0/1 (0%) - signed_off=False

