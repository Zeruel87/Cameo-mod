# audit_heaviness_bell — would the continuous-heaviness bell invert any family?

Idealized floating-point simulation of authored profiles. This does not verify runtime integer rounding, derived armor reconstruction, splash geometry, or roster-weighted pricing. Arithmetic-mean preservation is not price invariance.

DESIGN §12.0i: `LO` 0.667 (swing 1.50x), `sigma` 0.75, mu = (h + centre_of_mass) / 2, x-axis = one global 13-slot scale 0..2. Simulated at h = 0.0, 0.5, 1.0, 1.5, 2.0.

| | |
|---|--:|
| families measured | 54 |
| measured from the ACTUAL level-less base | 52 |
| legacy-first-level DIAGNOSTIC only | 2 |
| with NO gradient the bell could preserve | 2 |
| ladder ORDERINGS changed by the bell | 0 |
| mean drift (arithmetic) beyond 1e-6 | 0 |

## Profile sources

  Arrow  <- ^Warhead_Arrow  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  BlastCryo  <- ^Warhead_BlastCryo  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  BlastSonic  <- ^Warhead_BlastSonic  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Bullet  <- ^Warhead_Bullet  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  BulletChem  <- ^Warhead_BulletChem  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  BulletCryo  <- ^Warhead_BulletCryo  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  BulletFire  <- ^Warhead_BulletFire  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  BulletHE  <- ^Warhead_BulletHE  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  BulletSonic  <- ^Warhead_BulletSonic  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  BulletTesla  <- ^Warhead_BulletTesla  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  BulletThermobaric  <- ^Warhead_BulletThermobaric  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  CannonAP  <- ^Warhead_CannonAP  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  CannonChem  <- ^Warhead_CannonChem  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  CannonCryo  <- ^Warhead_CannonCryo  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  CannonFire  <- ^Warhead_CannonFire  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  CannonHE  <- ^Warhead_CannonHE  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  CannonNuke  <- ^Warhead_CannonNuke  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  CannonSonic  <- ^Warhead_CannonSonic  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  CannonTesla  <- ^Warhead_CannonTesla  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Chemical  <- ^Warhead_Chemical  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Concussion  <- ^Warhead_Concussion  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Cryo  <- ^Warhead_Cryo  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Demolition  <- ^Warhead_Demolition  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Flak  <- ^Warhead_Flak  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  FlakCryo  <- ^Warhead_FlakCryo  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Flame  <- ^Warhead_Flame  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Inferno  <- ^Warhead_Inferno  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Laser  <- ^Warhead_Laser  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Magic  <- ^Warhead_Magic  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Melee  <- ^Warhead_Melee  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  MissileAA  <- ^Warhead_MissileAA  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  MissileAP  <- ^Warhead_MissileAP  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  MissileChem  <- ^Warhead_MissileChem  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  MissileCryo  <- ^Warhead_MissileCryo  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  MissileFire  <- ^Warhead_MissileFire  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  MissileHE  <- ^Warhead_MissileHE  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  MissileNuke  <- ^Warhead_MissileNuke  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  MissileQuantum  <- ^Warhead_MissileQuantum  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  MissileSonic  <- ^Warhead_MissileSonic  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  MissileTesla  <- ^Warhead_MissileTesla  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  MissileThermobaric  <- ^Warhead_MissileThermobaric  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  PhotonCannon  <- ^Warhead_PhotonCannon  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Plasma  <- ^Warhead_Plasma  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Prism  <- ^Warhead_Prism  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Quantum  <- ^Warhead_Quantum  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Railgun  <- ^Warhead_Railgun  (Heaviness 2000 = h 2.0, authored continuous-base input; not the final runtime table)
  Sonic  <- ^Warhead_Sonic  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Storm  <- ^Warhead_Storm  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Tesla  <- ^Warhead_Tesla  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Thermobaric  <- ^Warhead_Thermobaric  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Toxic  <- ^Warhead_Toxic  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Waveforce  <- ^Warhead_Waveforce  (Heaviness 1000 = h 1.0, authored continuous-base input; not the final runtime table)
  Nuclear  <- ^Warhead_Nuclear_Super  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)
  Sniper  <- ^Warhead_Sniper_Light  (LEGACY-FIRST-LEVEL DIAGNOSTIC: no active level-less base exists for this family, so the bell verdict is simulated from the legacy level template)

## Flat families — no gradient to preserve

§9.2 predicted SIX of these; four (Cryo, Railgun, Waveforce, Storm) have since been given real gradients, so the prediction is stale and only these remain. The bell cannot help a family with no gradient — they need real profiles authored (§9.4). Lower `INVERT_BASELINE` as that happens, never by widening the bell.

  Magic
  Sonic

WARN 2 flat families (ratchet 2) · 0 inversions (must be 0) · 0 mean drifts (must be 0)
Lower `INVERT_BASELINE` as flat families get real profiles; never raise it.
