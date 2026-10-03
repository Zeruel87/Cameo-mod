# audit_family_uniqueness — 211 family templates (159 legacy level templates + 52 active level-less base(s))

Shape checks use authored implicit-range geometry, not heaviness-scaled runtime geometry.

  Heavy     51 distinct shapes   OK
  Light     52 distinct shapes   OK
  Medium    51 distinct shapes   OK
  Super      4 distinct shapes   OK
  Trace      1 distinct shapes   OK

  level-less bases (continuous heaviness):

      Arrow          radius     88  100,0                              Shield 77
      BlastCryo      radius    630  100,72,50,32,19,9,0                Shield 119
      BlastSonic     radius   1674  100,73,51,33,20,10,0               Shield 131
      Bullet         radius    100  100,0                              Shield 100
      BulletChem     radius    332  100,82,61,38,0                     Shield 120
      BulletCryo     radius     92  100,48,0                           Shield 121
      BulletFire     radius    344  100,82,64,42,0                     Shield 128
      BulletHE       radius    372  100,60,34,16,0                     Shield 102
      BulletSonic    radius    400  100,75,50,25,0                     Shield 145
      BulletTesla    radius    118  100,52,0                           Shield 172
      BulletThermobaric radius    390  100,80,62,46,32,17,0               Shield 116
      CannonAP       radius    120  100,0                              Shield 96
      CannonChem     radius    360  100,82,61,38,0                     Shield 149
      CannonCryo     radius    165  100,61,28,0                        Shield 122
      CannonFire     radius   1036  100,76,56,38,0                     Shield 154
      CannonHE       radius    900  100,50,20,0                        Shield 98
      CannonNuke     radius   3000  100,88,75,62,52,42,33,24,16,8,0    Shield 136
      CannonSonic    radius   1200  100,68,42,20,0                     Shield 143
      CannonTesla    radius    130  100,52,0                           Shield 170
      Chemical       radius   1100  100,88,72,50,0                     Shield 146
      Concussion     radius   2100  100,72,50,32,18,8,0                Shield 110
      Cryo           radius     84  100,45,0                           Shield 182
      Demolition     radius   1400  100,45,18,6,0                      Shield 103
      Flak           radius    550  100,58,32,16,6,0                   Shield 114
      FlakCryo       radius    215  100,68,44,26,12,0                  Shield 123
      Flame          radius   1200  100,90,78,60,0                     Shield 150
      Inferno        radius    424  100,80,59,40,0                     Shield 160
      Laser          radius     48  100,0                              Shield 181
      Magic          radius     96  100,0                              Shield 162
      Melee          radius      1  100,0                              Shield 72
      MissileAA      radius    900  100,70,30,0                        Shield 101
      MissileAP      radius     64  100,0                              Shield 97
      MissileChem    radius    264  100,82,61,38,0                     Shield 151
      MissileCryo    radius    120  100,60,27,0                        Shield 124
      MissileFire    radius    732  100,74,54,36,0                     Shield 155
      MissileHE      radius    450  100,45,15,0                        Shield 99
      MissileNuke    radius    800  100,90,80,70,60,50,40,30,20,10,0   Shield 133
      MissileQuantum radius     70  100,51,0                           Shield 161
      MissileSonic   radius    320  100,75,50,25,0                     Shield 141
      MissileTesla   radius     94  100,52,0                           Shield 171
      MissileThermobaric radius    828  100,74,51,36,23,13,0               Shield 117
      PhotonCannon   radius    284  100,75,49,24,0                     Shield 125
      Plasma         radius   1148  100,89,75,55,0                     Shield 174
      Prism          radius    150  100,40,0                           Shield 183
      Quantum        radius     78  100,52,0                           Shield 194
      Railgun        radius     72  100,0                              Shield 152
      Sonic          radius   1600  100,75,50,25,0                     Shield 165
      Storm          radius   1600  100,70,45,25,10,0                  Shield 216
      Tesla          radius    140  100,55,0                           Shield 225
      Thermobaric    radius   1518  100,76,57,43,31,17,0               Shield 134
      Toxic          radius   5500  100,90,75,55,30,0                  Shield 142
      Waveforce      radius    228  100,81,61,38,0                     Shield 175

  RAW Shield duplicate groups — 31 (base/Medium compatibility is approved and stays visible):

      Shield    100  ->  Bullet (^Warhead_Bullet), Melee (^Warhead_Melee_Light)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    110  ->  Concussion (^Warhead_Concussion), Sniper (^Warhead_Sniper_Light)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    116  ->  Arrow (^Warhead_Arrow_Medium), BulletThermobaric (^Warhead_BulletThermobaric)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    133  ->  CannonAP (^Warhead_CannonAP_Light), MissileNuke (^Warhead_MissileNuke)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    134  ->  MissileAP (^Warhead_MissileAP_Light), Thermobaric (^Warhead_Thermobaric)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    136  ->  CannonHE (^Warhead_CannonHE_Light), CannonNuke (^Warhead_CannonNuke)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    142  ->  BulletHE (^Warhead_BulletHE_Light), Toxic (^Warhead_Toxic)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    143  ->  CannonSonic (^Warhead_CannonSonic), Demolition (^Warhead_Demolition_Light)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    145  ->  BulletSonic (^Warhead_BulletSonic), MissileAP (^Warhead_MissileAP_Medium)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    146  ->  Chemical (^Warhead_Chemical), Concussion (^Warhead_Concussion_Light)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    150  ->  Bullet (^Warhead_Bullet_Medium), Flame (^Warhead_Flame)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    151  ->  MissileAA (^Warhead_MissileAA_Medium), MissileChem (^Warhead_MissileChem)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    152  ->  Flak (^Warhead_Flak_Light), Railgun (^Warhead_Railgun)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    154  ->  CannonFire (^Warhead_CannonFire), Demolition (^Warhead_Demolition_Medium)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    155  ->  BulletThermobaric (^Warhead_BulletThermobaric_Light), MissileFire (^Warhead_MissileFire), Nuclear (^Warhead_Nuclear_Super)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    160  ->  BulletChem (^Warhead_BulletChem_Light), Inferno (^Warhead_Inferno)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    161  ->  BulletCryo (^Warhead_BulletCryo_Light), MissileQuantum (^Warhead_MissileQuantum)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    162  ->  CannonCryo (^Warhead_CannonCryo_Light), Magic (^Warhead_Magic)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    165  ->  PhotonCannon (^Warhead_PhotonCannon_Light), Sonic (^Warhead_Sonic)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    170  ->  BulletFire (^Warhead_BulletFire_Light), CannonTesla (^Warhead_CannonTesla)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    171  ->  Flak (^Warhead_Flak_Medium), MissileTesla (^Warhead_MissileTesla)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    172  ->  Bullet (^Warhead_Bullet_Heavy), BulletTesla (^Warhead_BulletTesla)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    174  ->  BlastSonic (^Warhead_BlastSonic_Light), Plasma (^Warhead_Plasma)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    175  ->  BulletThermobaric (^Warhead_BulletThermobaric_Medium), Waveforce (^Warhead_Waveforce)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    181  ->  BlastCryo (^Warhead_BlastCryo_Medium), Laser (^Warhead_Laser)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    182  ->  BulletChem (^Warhead_BulletChem_Medium), Cryo (^Warhead_Cryo)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    183  ->  BulletCryo (^Warhead_BulletCryo_Medium), Prism (^Warhead_Prism)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    194  ->  BulletSonic (^Warhead_BulletSonic_Light), Quantum (^Warhead_Quantum)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    205  ->  CannonNuke (^Warhead_CannonNuke_Medium), IncendiaryYakComposition (^Warhead_IncendiaryYakComposition)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    216  ->  CannonFire (^Warhead_CannonFire_Light), Storm (^Warhead_Storm)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.
      Shield    225  ->  Flame (^Warhead_Flame_Medium), Tesla (^Warhead_Tesla)
          ⚠ DISTINCT legacy families share a Shield value — fewer than two NEW bases are involved; reported, not failed.

OK — no two families share both a radius and a curve at any level (bases incl.), and no distinct NEW family bases share a Shield value. Raw compatibility and legacy duplicates remain listed above.
