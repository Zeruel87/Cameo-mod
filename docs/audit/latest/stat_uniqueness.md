# Unit stat uniqueness (DESIGN.md — the uniqueness law)

## U1 — identical on every priced stat, ACROSS factions: **36** actors in 14 groups (ratchet 36)

   4x  hp=   32000 sp=   56 cost=   150  atreides_lightinfantry, corrino_lightinfantry, harkonnen_lightinfantry, ixian_lightinfantry
   4x  hp=   50000 sp=   64 cost=   750  atreides_missiletank, atreides_mongoose, corrino_missiletank, missile_tank
   3x  hp=   40000 sp=   42 cost=   200  atreides_rockettrooper, corrino_trooper, harkonnen_rockettrooper
   3x  hp=   12000 sp=   48 cost=   300  ixian_rockettrooper, ordos_rockettrooper, trooper
   3x  hp=    5000 sp=  100 cost=   200  ra1_soviets_actordogname, ra2_allies_attackdog, ra2_soviets_attackdog
   3x  hp=   10000 sp=   55 cost=   600  forgotten_engineer, ts_gdi_engineer, ts_nod_engineer
   2x  hp=   50000 sp=  192 cost=  1200  corrino_gunship, harkonnen_gunship
   2x  hp=   50000 sp=  150 cost=  1000  futuretech_twister, steelconsortium_twister
   2x  hp=   27500 sp=  150 cost=   400  tkm_as42, ts_gdi_pitbull
   2x  hp=   10000 sp=   55 cost=   300  ra1_allies_alliedrocketsoldier, ra1_soviets_sovietrocketsoldier
   2x  hp=    9000 sp=   50 cost=   300  td_gdi_rocketsoldier, td_nod_rocketsoldier
   2x  hp=   12000 sp=   50 cost=   300  forgotten_rocketinfantry, ts_nod_rocketinfantry
   2x  hp=   16000 sp=   60 cost=   120  ts_gdi_lightinfantry, ts_nod_lightinfantry
   2x  hp=  350000 sp=   40 cost=  4000  ts_gdi_cruiser, ts_nod_cruiser

## U2 — identical within ONE faction: **33** actors in 12 groups (ratchet 33)

   6x  ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg …
   4x  wc2_humans_archmage, wc2_humans_highelfpriest, wc2_humans_highelfsorceress, wc2_humans_mage
   3x  corrino_sardaukar_berserker, corrino_sardaukar_javelin, corrino_sardaukar_sword
   3x  ra2_allies_battlefortress, ra2_allies_battlefortress_chrono, ra2_allies_battlefortress_empty
   3x  protoss_probe, terran_scv, zerg_drone
   2x  wc2_humans_elvenarcher, wc2_humans_elvenranger
   2x  wc2_humans_knight, wc2_humans_paladin
   2x  wc2_humans_demolitionsquad, wc2_orcs_goblinsappers
   2x  wc2_humans_peasant, wc2_orcs_peon
   2x  wc2_humans_siegeengine, wc2_orcs_siegeengine

## U3 — per-stat collisions (ratchets hp 750 · speed 716 · cost 771)

   hp          869 values   119 distinct   750 collisions ( 86%)  most-shared: 50000 x67
   speed       792 values    76 distinct   716 collisions ( 90%)  most-shared: 75 x86
   w_range     707 values   418 distinct   289 collisions ( 41%)  most-shared: 5000 x31
   w_dps       687 values   375 distinct   312 collisions ( 45%)  most-shared: 400 x29
   cost        868 values    97 distinct   771 collisions ( 89%)  most-shared: 500 x75

exit=0
