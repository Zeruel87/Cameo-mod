# audit_heaviness_bell — would the continuous-heaviness bell invert any family?

Idealized floating-point simulation of authored profiles. This does not verify runtime integer rounding, derived armor reconstruction, splash geometry, or roster-weighted pricing. Arithmetic-mean preservation is not price invariance.

DESIGN §12.0i: `LO` 0.667 (swing 1.50x), `sigma` 0.75, mu = (h + centre_of_mass) / 2, x-axis = one global 13-slot scale 0..2. Simulated at h = 0.0, 0.5, 1.0, 1.5, 2.0.

| | |
|---|--:|
| families measured | 50 |
| measured from the ACTUAL level-less base | 1 |
| legacy-first-level DIAGNOSTIC only | 49 |
| with NO gradient the bell could preserve | 2 |
| ladder ORDERINGS changed by the bell | 0 |
| mean drift (arithmetic) beyond 1e-6 | 0 |

## Profile sources

  CannonAP  <- ^Warhead_CannonAP  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Arrow  <- ^Warhead_Arrow_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Bullet  <- ^Warhead_Bullet_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  BulletChem  <- ^Warhead_BulletChem_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  BulletCryo  <- ^Warhead_BulletCryo_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  BulletFire  <- ^Warhead_BulletFire_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  BulletHE  <- ^Warhead_BulletHE_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  BulletTesla  <- ^Warhead_BulletTesla_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  BulletThermobaric  <- ^Warhead_BulletThermobaric_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  CannonChem  <- ^Warhead_CannonChem_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  CannonCryo  <- ^Warhead_CannonCryo_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  CannonFire  <- ^Warhead_CannonFire_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  CannonHE  <- ^Warhead_CannonHE_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  CannonNuke  <- ^Warhead_CannonNuke_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  CannonTesla  <- ^Warhead_CannonTesla_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Chemical  <- ^Warhead_Chemical_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Concussion  <- ^Warhead_Concussion_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Cryo  <- ^Warhead_Cryo_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  CryoBlast  <- ^Warhead_CryoBlast_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Demolition  <- ^Warhead_Demolition_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Flak  <- ^Warhead_Flak_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  FlakCryo  <- ^Warhead_FlakCryo_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Flame  <- ^Warhead_Flame_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Inferno  <- ^Warhead_Inferno_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Laser  <- ^Warhead_Laser_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Magic  <- ^Warhead_Magic_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Melee  <- ^Warhead_Melee_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  MissileAA  <- ^Warhead_MissileAA_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  MissileAP  <- ^Warhead_MissileAP_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  MissileChem  <- ^Warhead_MissileChem_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  MissileCryo  <- ^Warhead_MissileCryo_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  MissileFire  <- ^Warhead_MissileFire_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  MissileHE  <- ^Warhead_MissileHE_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  MissileNuke  <- ^Warhead_MissileNuke_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  MissileQuantum  <- ^Warhead_MissileQuantum_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  MissileTesla  <- ^Warhead_MissileTesla_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  MissileThermobaric  <- ^Warhead_MissileThermobaric_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Nuclear  <- ^Warhead_Nuclear_Super  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  PhotonCannon  <- ^Warhead_PhotonCannon_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Plasma  <- ^Warhead_Plasma_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Prism  <- ^Warhead_Prism_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Quantum  <- ^Warhead_Quantum_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Railgun  <- ^Warhead_Railgun_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Sniper  <- ^Warhead_Sniper_Light  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Sonic  <- ^Warhead_Sonic_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Storm  <- ^Warhead_Storm_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Tesla  <- ^Warhead_Tesla_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Thermobaric  <- ^Warhead_Thermobaric_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Toxic  <- ^Warhead_Toxic_Light  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Waveforce  <- ^Warhead_Waveforce_Heavy  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)

## Flat families — no gradient to preserve

§9.2 predicted SIX of these; four (Cryo, Railgun, Waveforce, Storm) have since been given real gradients, so the prediction is stale and only these remain. The bell cannot help a family with no gradient — they need real profiles authored (§9.4). Lower `INVERT_BASELINE` as that happens, never by widening the bell.

  Magic
  Sonic

WARN 2 flat families (ratchet 2) · 0 inversions (must be 0) · 0 mean drifts (must be 0)
Lower `INVERT_BASELINE` as flat families get real profiles; never raise it.
