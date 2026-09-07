# TurnSpeed derivation (DESIGN.md — Vehicle turning)

## T1 — turreted ground: hull != round(Speed/5): **37** (ratchet 37) ok
   CNCSS                                speed=80    hull=32    want=16
   EDEN_TIGER_ACIDCLOUD                 speed=45    hull=10    want=9
   PLYMOUTH_TIGER_EMP                   speed=45    hull=10    want=9
   PLYMOUTH_TIGER_ESG                   speed=45    hull=10    want=9
   PLYMOUTH_TIGER_MICROWAVE             speed=45    hull=10    want=9
   PLYMOUTH_TIGER_RPG                   speed=45    hull=10    want=9
   PLYMOUTH_TIGER_STARFLARE             speed=45    hull=10    want=9
   PLYMOUTH_TIGER_STICKYFOAM            speed=45    hull=10    want=9
   PLYMOUTH_TIGER_SUPERNOVA             speed=45    hull=10    want=9
   atreides_apc                         speed=65    hull=16    want=13
   atreides_mongoose                    speed=64    hull=20    want=13
   atreides_siegetank                   speed=43    hull=48    want=9
   … and 25 more

## T2 — turretless ground: hull != round(2*Speed/5): **142** (ratchet 142) ok
   CNCRSS                               speed=150   hull=40    want=60
   EDEN_CARGOTRUCK_EMPTY                speed=85    hull=17    want=34
   EDEN_CONVEC_STRUCTURE_FACTORY        speed=75    hull=15    want=30
   LST                                  speed=125   hull=40    want=50
   PLYMOUTH_CARGOTRUCK_EMPTY            speed=80    hull=16    want=32
   PLYMOUTH_CONVEC_STRUCTURE_FACTORY    speed=75    hull=15    want=30
   PLYMOUTH_SCORPION                    speed=140   hull=40    want=56
   PLYMOUTH_SPIDER                      speed=140   hull=40    want=56
   SCSPIDERMINE                         speed=200   hull=200   want=80
   ^CivilianDriveByVehicle              speed=100   hull=20    want=40
   ^MCV                                 speed=75    hull=15    want=30
   ^Monster                             speed=50    hull=32    want=20
   … and 130 more

## T3 — turret turn speed != hull turn speed: **27** (ratchet 27) ok
   CNCSS                                hull=32     turret=16
   ^IFVBase                             hull=30     turret=60
   atreides_apc                         hull=16     turret=48
   atreides_mongoose                    hull=20     turret=48
   cabal_lazerboat                      hull=16     turret=24
   cabal_tarantula_backup               hull=0      turret=14
   harkonnen_adp                        hull=20     turret=48
   japan_exorcistoitank                 hull=10     turret=24
   japan_japanesespeedboat              hull=28     turret=56
   japan_oitank                         hull=10     turret=24
   ksub.asian                           hull=50     turret=20
   lsub.asian                           hull=24     turret=12
   … and 15 more

## T4 — turreted actor with NO hull speed (immobile — own rule pending): **137** (ratchet 137) ok
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
   … and 125 more

exit=0
