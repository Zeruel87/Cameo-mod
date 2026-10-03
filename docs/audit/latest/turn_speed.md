# TurnSpeed derivation (DESIGN.md — Vehicle turning)

## T1 — turreted ground: hull != round(Speed/5): **49** (ratchet 37) ⛔ RAISED
   EDEN_TIGER_ACIDCLOUD                 speed=45    hull=10    want=9
   PLYMOUTH_TIGER_EMP                   speed=45    hull=10    want=9
   PLYMOUTH_TIGER_ESG                   speed=45    hull=10    want=9
   PLYMOUTH_TIGER_MICROWAVE             speed=45    hull=10    want=9
   PLYMOUTH_TIGER_RPG                   speed=45    hull=10    want=9
   PLYMOUTH_TIGER_STARFLARE             speed=45    hull=10    want=9
   PLYMOUTH_TIGER_STICKYFOAM            speed=45    hull=10    want=9
   PLYMOUTH_TIGER_SUPERNOVA             speed=45    hull=10    want=9
   asianalliance_ksub                   speed=125   hull=50    want=25
   asianalliance_lsub                   speed=60    hull=24    want=12
   atreides_apc                         speed=65    hull=16    want=13
   atreides_mongoose                    speed=64    hull=20    want=13
   … and 37 more

## T2 — turretless ground: hull != round(2*Speed/5): **167** (ratchet 142) ⛔ RAISED
   EDEN_CARGOTRUCK_EMPTY                speed=85    hull=17    want=34
   EDEN_CONVEC_STRUCTURE_FACTORY        speed=75    hull=15    want=30
   PLYMOUTH_CARGOTRUCK_EMPTY            speed=80    hull=16    want=32
   PLYMOUTH_CONVEC_STRUCTURE_FACTORY    speed=75    hull=15    want=30
   PLYMOUTH_SCORPION                    speed=140   hull=40    want=56
   PLYMOUTH_SPIDER                      speed=140   hull=40    want=56
   SCSPIDERMINE                         speed=200   hull=200   want=80
   ^CivilianDriveByVehicle              speed=100   hull=20    want=40
   ^MCV                                 speed=75    hull=15    want=30
   ^Monster                             speed=50    hull=32    want=20
   ^RAHARV                              speed=90    hull=18    want=36
   ^RAMCV                               speed=75    hull=15    want=30
   … and 155 more

## T3 — turret turn speed != hull turn speed: **27** (ratchet 27) ok
   ^IFVBase                             hull=30     turret=60
   asianalliance_ksub                   hull=50     turret=20
   asianalliance_lsub                   hull=24     turret=12
   atreides_apc                         hull=16     turret=48
   atreides_mongoose                    hull=20     turret=48
   cabal_lazerboat                      hull=16     turret=24
   cabal_tarantula_backup               hull=0      turret=14
   harkonnen_adp                        hull=20     turret=48
   japan_exorcistoitank                 hull=10     turret=24
   japan_japanesespeedboat              hull=28     turret=56
   japan_oitank                         hull=10     turret=24
   latin_sub                            hull=22     turret=11
   … and 15 more

## T4 — turreted actor with NO hull speed (immobile — own rule pending): **139** (ratchet 137) ⛔ RAISED
   C2KFIREDEPARTMENT                    turret=None
   EDEN_GP_EMP                          turret=12
   EDEN_GP_LASER                        turret=12
   EDEN_GP_RAILGUN                      turret=12
   MAMMOTHBUNKER                        turret=8
   PLYMOUTH_GP_MICROWAVE                turret=12
   PLYMOUTH_GP_RPG                      turret=12
   PLYMOUTH_GP_STICKYFOAM               turret=12
   TECHBCANNON                          turret=28
   TECHBCANNON2                         turret=32
   ^DefenseTurretedEMP                  turret=None
   ^HunterSeekersPower                  turret=None
   … and 127 more

exit=1
