# Unit stat uniqueness (DESIGN.md — the uniqueness law)

## U1 — identical on every priced stat, ACROSS factions: **31** actors in 11 groups (ratchet 36)

   5x  hp=   50000 sp=   64 cost=   750  atreides_missiletank, atreides_mongoose, corrino_missiletank, harkonnen_rockettank …
   4x  hp=   32000 sp=   56 cost=   150  atreides_lightinfantry, corrino_lightinfantry, harkonnen_lightinfantry, ixian_lightinfantry
   3x  hp=   40000 sp=   42 cost=   200  atreides_rockettrooper, corrino_trooper, harkonnen_rockettrooper
   3x  hp=   12000 sp=   48 cost=   300  ixian_rockettrooper, ordos_rockettrooper, trooper
   3x  hp=    5000 sp=  100 cost=   200  ra1_soviets_dog, ra2_allies_dog, ra2_soviets_dog
   3x  hp=   10000 sp=   55 cost=   600  forgotten_engineer, ts_gdi_engineer, ts_nod_engineer
   2x  hp=   50000 sp=  192 cost=  1200  corrino_gunship, harkonnen_gunship
   2x  hp=   50000 sp=  150 cost=  1000  futuretech_twister, steelconsortium_twister
   2x  hp=   27500 sp=  150 cost=   400  tkm_as42, ts_gdi_pitbull
   2x  hp=   12000 sp=   50 cost=   300  forgotten_rocketinfantry, ts_nod_rocketinfantry
   2x  hp=   16000 sp=   60 cost=   120  ts_gdi_lightinfantry, ts_nod_lightinfantry

## U2 — identical within ONE faction: **38** actors in 16 groups (ratchet 33)

   6x  ra2_allies_ifv, ra2_allies_ifv_chrono, ra2_allies_ifv_hmg, ra2_allies_ifv_mg …
   3x  corrino_sardaukar_berserker, corrino_sardaukar_javelin, corrino_sardaukar_sword
   3x  ra2_allies_battlefortress, ra2_allies_battlefortress_chrono, ra2_allies_battlefortress_empty
   2x  harkonnen_assaulttank, harkonnen_combat_tank
   2x  ra1_allies_rifleinfantry, ra1_allies_rifleinfantry
   2x  ra1_allies_rocketsoldier, ra1_allies_rocketsoldier
   2x  protoss_probe, zerg_drone
   2x  wc2_humans_archmage, wc2_humans_mage
   2x  wc2_humans_elvenarcher, wc2_humans_elvenranger
   2x  wc2_humans_highelfpriest, wc2_humans_highelfsorceress

## U3 — per-stat collisions (ratchets hp 779 · speed 716 · cost 809)

   hp          927 values   140 distinct   787 collisions ( 85%)  most-shared: 50000 x68
   speed       818 values    89 distinct   729 collisions ( 89%)  most-shared: 75 x81
   w_range     750 values   436 distinct   314 collisions ( 42%)  most-shared: 5000 x29
   w_dps       748 values   432 distinct   316 collisions ( 42%)  most-shared: 500 x22
   cost        926 values   127 distinct   799 collisions ( 86%)  most-shared: 500 x75

exit=1
