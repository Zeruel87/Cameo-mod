# audit_duplicate_keys — duplicate keys in one node (ambiguous merges)

Files scanned: **699** — D1 ambiguous inheritance labels: **0**, D2 merged duplicates: **170**


## D1 — duplicate inheritance labels with different parent values

_none found_


## D2 — duplicate keys by key name (top 40)

| key | occurrences |
|---|---|
| Projectile | 19 |
| Range | 17 |
| ReloadDelay | 14 |
| Warhead@Effect | 7 |
| Warhead@Bullet_Medium_Flat | 7 |
| ValidTargets | 7 |
| Warhead@ShieldHit | 6 |
| Report | 6 |
| Burst | 6 |
| Warhead@Concrete | 5 |
| Warhead@EffectAir | 4 |
| Warhead@ShieldHitEffect | 4 |
| BurstDelays | 3 |
| Warhead@EffectWater | 3 |
| Warhead@Smudge | 3 |
| Warhead@DuneRock | 3 |
| Warhead@DuneSand | 3 |
| Warhead@CannonHE_Medium | 3 |
| Warhead@Shrapnel | 2 |
| Warhead@Demolition_Light | 2 |
| Warhead@GrenadePercentage | 2 |
| Warhead@ChaingunPercentage | 2 |
| Warhead@Glow | 2 |
| Warhead@RA2Crater | 2 |
| Defaults | 2 |
| Voiced | 2 |
| AutoTarget | 2 |
| RenderSprites | 2 |
| Warhead@1Dam | 1 |
| Warhead@Bullet_Medium | 1 |
| Warhead@OwnerChange | 1 |
| Warhead@TankDestroyerCannonPercentage | 1 |
| Warhead@LightChemicalWeaponPercentage | 1 |
| Warhead@FlakWeaponPercentage | 1 |
| Warhead@MediumMissilePercentage | 1 |
| Warhead@HeavyBombPercentage | 1 |
| Warhead@Heal | 1 |
| Warhead@MediumChemicalWeaponPercentage | 1 |
| Warhead@MissileAP_Light | 1 |
| Warhead@Demolition_Heavy_Flat | 1 |


## D2 — full list

| file | lines | node | key |
|---|---|---|---|
| mods/cameo/ContentPacks/D2k/Atreides/yaml/weapons.yaml | 203, 212 | PhoenixRocket | Warhead@1Dam |
| mods/cameo/ContentPacks/D2k/Atreides/yaml/weapons.yaml | 204, 228 | PhoenixRocket | Warhead@Shrapnel |
| mods/cameo/ContentPacks/D2k/Harkonnen/yaml/weapons.yaml | 181, 192 | ExplosiveDebris | Projectile |
| mods/cameo/ContentPacks/D2k/Harkonnen/yaml/weapons.yaml | 184, 199 | ExplosiveDebris | Warhead@Demolition_Light |
| mods/cameo/ContentPacks/D2k/Ixian/yaml/weapons.yaml | 1733, 1741 | HMG_Duelist_upgrade | Warhead@ShieldHit |
| mods/cameo/ContentPacks/D2k/Ixian/yaml/weapons.yaml | 2363, 2375 | d2k_air_drone_guns | Warhead@Bullet_Medium |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml | 2398, 2415 | DeviatorMissile | Warhead@OwnerChange |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml | 3917, 3948 | ordos_airmine | Warhead@TankDestroyerCannonPercentage |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml | 3918, 3988 | ordos_airmine | Warhead@LightChemicalWeaponPercentage |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml | 3919, 4031 | ordos_airmine | Warhead@FlakWeaponPercentage |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml | 3920, 4071 | ordos_airmine | Warhead@MediumMissilePercentage |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml | 3921, 4111 | ordos_airmine | Warhead@HeavyBombPercentage |
| mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml | 3922, 4152 | ordos_airmine | Warhead@Shrapnel |
| mods/cameo/ContentPacks/RedAlert/Japan/yaml/weapons.yaml | 6261, 6263 | NanoReturnHeal | Warhead@Heal |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml | 11643, 11754 | ra1_soviets_volkov_volkovmagneticweaponincendiarytesla | ReloadDelay |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml | 11644, 11755 | ra1_soviets_volkov_volkovmagneticweaponincendiarytesla | Range |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml | 11646, 11756 | ra1_soviets_volkov_volkovmagneticweaponincendiarytesla | BurstDelays |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml | 11648, 11757 | ra1_soviets_volkov_volkovmagneticweaponincendiarytesla | Projectile |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml | 11658, 11762 | ra1_soviets_volkov_volkovmagneticweaponincendiarytesla | Warhead@MediumChemicalWeaponPercentage |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml | 11700, 11810 | ra1_soviets_volkov_volkovmagneticweaponincendiarytesla | Warhead@GrenadePercentage |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml | 11740, 11930 | ra1_soviets_volkov_volkovmagneticweaponincendiarytesla | Warhead@Concrete |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml | 11742, 11932 | ra1_soviets_volkov_volkovmagneticweaponincendiarytesla | Warhead@Effect |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml | 11747, 11946 | ra1_soviets_volkov_volkovmagneticweaponincendiarytesla | Warhead@EffectWater |
| mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml | 11749, 11876 | ra1_soviets_volkov_volkovmagneticweaponincendiarytesla | Warhead@ShieldHit |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml | 1923, 2026 | RA2MultiHoverMissile_elite | Range |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml | 1927, 2027 | RA2MultiHoverMissile_elite | Projectile |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml | 1940, 2033 | RA2MultiHoverMissile_elite | Warhead@MissileAP_Light |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml | 2561, 2581 | RA2DepthCharge | Report |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml | 2562, 2582 | RA2DepthCharge | ReloadDelay |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml | 2563, 2583 | RA2DepthCharge | Range |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml | 2565, 2586 | RA2DepthCharge | Projectile |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml | 6400, 6610 | DredMissile | Projectile |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml | 6412, 6614 | DredMissile | Warhead@Demolition_Light |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml | 6498, 6612 | DredMissile | Warhead@Effect |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml | 9489, 9582 | TanyaBomb | Report |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml | 9490, 9583 | TanyaBomb | Warhead@Effect |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml | 9496, 9847 | TanyaBomb | Warhead@Demolition_Heavy_Flat |
| mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml | 10552, 10560 | RA2LargeDebris | Projectile |
| mods/cameo/ContentPacks/RedAlert2/Soviets/yaml/weapons.yaml | 945, 950 | RA160mmE_elite | Warhead@Concussion_Medium_Flat |
| mods/cameo/ContentPacks/RedAlert2/Soviets/yaml/weapons.yaml | 1693, 1709 | RA2120xmm_fire_elite | Range |
| mods/cameo/ContentPacks/RedAlert2/Soviets/yaml/weapons.yaml | 1695, 1710 | RA2120xmm_fire_elite | Burst |
| mods/cameo/ContentPacks/RedAlert2/Soviets/yaml/weapons.yaml | 1696, 1711 | RA2120xmm_fire_elite | BurstDelays |
| mods/cameo/ContentPacks/RedAlert2/Soviets/yaml/weapons.yaml | 1754, 1770 | RA2120xmm_tesla_elite | Range |
| mods/cameo/ContentPacks/RedAlert2/Soviets/yaml/weapons.yaml | 1756, 1771 | RA2120xmm_tesla_elite | Burst |
| mods/cameo/ContentPacks/RedAlert2/Soviets/yaml/weapons.yaml | 1757, 1772 | RA2120xmm_tesla_elite | BurstDelays |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml | 3062, 3067 | YuriGatlingTankMG1 | Warhead@Bullet_Medium_Flat |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml | 3090, 3095 | YuriGatlingTankMG1_AA | Warhead@Bullet_Medium_Flat |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml | 3118, 3123 | YuriGatlingTankMG2 | Warhead@Bullet_Medium_Flat |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml | 3146, 3151 | YuriGatlingTankMG2_AA | Warhead@Bullet_Medium_Flat |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml | 3174, 3179 | YuriGatlingTankMG3 | Warhead@Bullet_Medium_Flat |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml | 3202, 3207 | YuriGatlingTankMG3_AA | Warhead@Bullet_Medium_Flat |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml | 3313, 3322 | RA2Virusgun | ValidTargets |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml | 3314, 3361 | RA2Virusgun | Warhead@Toxic_Light |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml | 3373, 3382 | RA2Virusgun2 | ValidTargets |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml | 3429, 3486 | RA2Virusgun3 | Warhead@Toxic_Medium |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml | 3443, 3499 | RA2Virusgun3 | Warhead@Effect |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml | 3444, 3506 | RA2Virusgun3 | Warhead@EffectAir |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml | 3445, 3511 | RA2Virusgun3 | Warhead@ShieldHit |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml | 3446, 3513 | RA2Virusgun3 | Warhead@Concrete |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml | 3447, 3515 | RA2Virusgun3 | Warhead@ShieldHitEffect |
| mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml | 3453, 3492 | RA2Virusgun3 | Warhead@Cloud |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 6199, 6661 | AsianTurretPlasma | Range |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 6200, 6663 | AsianTurretPlasma | ReloadDelay |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 6201, 6666 | AsianTurretPlasma | Report |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 6202, 6667 | AsianTurretPlasma | Projectile |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 6208, 6673 | AsianTurretPlasma | Warhead@FireShrapnel |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 6256, 6675 | AsianTurretPlasma | Warhead@Plasma_Heavy_Flat |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 6601, 6671 | AsianTurretPlasma | Warhead@Effect |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 6609, 6772 | AsianTurretPlasma | Warhead@Smudge |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 6613, 6761 | AsianTurretPlasma | Warhead@DuneRock |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 6616, 6764 | AsianTurretPlasma | Warhead@DuneSand |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 6619, 6767 | AsianTurretPlasma | Warhead@EffectAir |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 7621, 7641 | AsianChaosMine | Report |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 8172, 8322 | AAGunBoatFlak | ValidTargets |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 8175, 8319 | AAGunBoatFlak | Range |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 8176, 8324 | AAGunBoatFlak | Warhead@Flak_Medium |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 8180, 8329 | AAGunBoatFlak | Warhead@SmallArmsPercentage |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 8219, 8331 | AAGunBoatFlak | Warhead@GrenadePercentage |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 8268, 8333 | AAGunBoatFlak | Warhead@ChaingunPercentage |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 8309, 8335 | AAGunBoatFlak | Warhead@Concrete |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 8311, 8337 | AAGunBoatFlak | Warhead@Glow |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 8314, 8340 | AAGunBoatFlak | Warhead@ShieldHit |
| mods/cameo/ContentPacks/RedAlert2Mod/AsianAlliance/yaml/weapons.yaml | 8316, 8342 | AAGunBoatFlak | Warhead@ShieldHitEffect |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 5, 29 | schwarzermond_lunarsoldier_rifle | ReloadDelay |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 6, 30 | schwarzermond_lunarsoldier_rifle | Range |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 7, 31 | schwarzermond_lunarsoldier_rifle | Report |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 9, 32 | schwarzermond_lunarsoldier_rifle | Projectile |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 755, 917 | NaxiMP40Laser | ReloadDelay |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 756, 918 | NaxiMP40Laser | Burst |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 758, 916 | NaxiMP40Laser | Range |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 759, 915 | NaxiMP40Laser | Report |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 760, 919 | NaxiMP40Laser | Projectile |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 881, 1258 | NaxiMP40Laser | Warhead@Smudge |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 884, 1237 | NaxiMP40Laser | Warhead@DuneRock |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 887, 1240 | NaxiMP40Laser | Warhead@DuneSand |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 890, 1243 | NaxiMP40Laser | Warhead@RA2Crater |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 893, 1232 | NaxiMP40Laser | Warhead@Effect |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 898, 1254 | NaxiMP40Laser | Warhead@EffectAir |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 904, 1246 | NaxiMP40Laser | Warhead@EffectWater |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 907, 1252 | NaxiMP40Laser | Warhead@Concrete |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 909, 1256 | NaxiMP40Laser | Warhead@ShieldHit |
| mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml | 911, 1261 | NaxiMP40Laser | Warhead@ShieldHitEffect |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 728, 906 | RA2FreedomAK47_elite | Warhead@SniperWeaponExtraDamage |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 729, 945 | RA2FreedomAK47_elite | Warhead@SniperWeaponPercentage |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 730, 864 | RA2FreedomAK47_elite | Warhead@Effect |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 731, 889 | RA2FreedomAK47_elite | Warhead@Effect1 |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 732, 894 | RA2FreedomAK47_elite | Warhead@Effect2 |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 733, 876 | RA2FreedomAK47_elite | Warhead@EffectWater |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 734, 882 | RA2FreedomAK47_elite | Warhead@ShieldHit |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 735, 880 | RA2FreedomAK47_elite | Warhead@Concrete |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 736, 884 | RA2FreedomAK47_elite | Warhead@ShieldHitEffect |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 737, 848 | RA2FreedomAK47_elite | Warhead@Glow |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 738, 852 | RA2FreedomAK47_elite | Warhead@Smudge |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 739, 855 | RA2FreedomAK47_elite | Warhead@DuneRock |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 740, 858 | RA2FreedomAK47_elite | Warhead@DuneSand |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 741, 861 | RA2FreedomAK47_elite | Warhead@RA2Crater |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 742, 870 | RA2FreedomAK47_elite | Warhead@EffectAir |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 743, 765 | RA2FreedomAK47_elite | Warhead@Bullet_Medium_Flat |
| mods/cameo/ContentPacks/RedAlert2Mod/Syndicate/yaml/weapons.yaml | 744, 985 | RA2FreedomAK47_elite | Warhead@ChaingunPercentage |
| mods/cameo/ContentPacks/StarCraft/Protoss/yaml/weapons.yaml | 1538, 1545 | ManifoldMG | ValidTargets |
| mods/cameo/ContentPacks/StarCraft/Protoss/yaml/weapons.yaml | 1539, 1547 | ManifoldMG | ReloadDelay |
| mods/cameo/ContentPacks/StarCraft/Protoss/yaml/weapons.yaml | 1540, 1546 | ManifoldMG | Range |
| mods/cameo/ContentPacks/StarCraft/Terran/yaml/weapons.yaml | 2706, 2716 | WyvernRockets | ReloadDelay |
| mods/cameo/ContentPacks/StarCraft/Terran/yaml/weapons.yaml | 2707, 2715 | WyvernRockets | Range |
| mods/cameo/ContentPacks/StarCraft/Zerg/yaml/weapons.yaml | 145, 152 | MutaliskSpore | ReloadDelay |
| mods/cameo/ContentPacks/StarCraft/Zerg/yaml/weapons.yaml | 146, 153 | MutaliskSpore | Range |
| mods/cameo/ContentPacks/StarCraft/Zerg/yaml/weapons.yaml | 500, 506 | GuardianShoot | ReloadDelay |
| mods/cameo/ContentPacks/StarCraft/Zerg/yaml/weapons.yaml | 501, 507 | GuardianShoot | Range |
| mods/cameo/ContentPacks/StarCraft/Zerg/yaml/weapons.yaml | 1249, 1257 | Tentacle | ReloadDelay |
| mods/cameo/ContentPacks/StarCraft/Zerg/yaml/weapons.yaml | 1250, 1258 | Tentacle | Range |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml | 948, 960 | CabalReaperMissiles | Projectile |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml | 1157, 1169 | CabalReaperMissiles_AA | Projectile |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml | 1361, 1373 | CabalHeavyReaperMissiles | Projectile |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml | 1571, 1583 | CabalHeavyReaperMissiles_AA | Projectile |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml | 3060, 3075 | CabalRocketCyborgRockets | Projectile |
| mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml | 3097, 3112 | CabalRocketCyborgRocketsUpgraded | Projectile |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/weapons.yaml | 46, 54 | TS70mmTur | ReloadDelay |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/weapons.yaml | 47, 55 | TS70mmTur | Range |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/weapons.yaml | 370, 377 | TSScoopDualTur | ReloadDelay |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/weapons.yaml | 371, 380 | TSScoopDualTur | Range |
| mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/weapons.yaml | 4095, 4103 | TSMutApcCannon | ValidTargets |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/weapons.yaml | 1241, 1253 | TSBombSonic | ValidTargets |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/weapons.yaml | 1242, 1248 | TSBombSonic | ReloadDelay |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/weapons.yaml | 1243, 1251 | TSBombSonic | Range |
| mods/cameo/ContentPacks/TiberianSun/GDI/yaml/weapons.yaml | 1767, 1775 | TSAAPCCannon | ValidTargets |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/weapons.yaml | 658, 883 | ScrinRiftDamage | ReloadDelay |
| mods/cameo/ContentPacks/TiberiumWars/Scrin/yaml/weapons.yaml | 661, 885 | ScrinRiftDamage | Projectile |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/sequences.yaml | 150, 153 | wc2_humans_guardtower | Defaults |
| mods/cameo/ContentPacks/Warcraft2/Humans/yaml/sequences.yaml | 158, 161 | wc2_humans_cannontower | Defaults |
| mods/cameo/rules/ants.yaml | 71, 80 | QANT | Voiced |
| mods/cameo/rules/ants.yaml | 754, 774 | defenseant | AutoTarget |
| mods/cameo/rules/generals.yaml | 4904, 4936 | glworker | AutoTarget |
| mods/cameo/rules/generals.yaml | 7385, 7400 | charty | Explodes |
| mods/cameo/rules/lostunits.yaml | 1214, 1323 | dalek | AttackFrontal |
| mods/cameo/rules/shockwave.yaml | 3105, 3142 | susadecoydrone | Disguise |
| mods/cameo/rules/shockwave.yaml | 8281, 8292 | sglkatyusha | RenderSprites |
| mods/cameo/rules/shockwave.yaml | 9281, 9296 | sglbadger | RenderSprites |
| mods/cameo/rules/simcity.yaml | 1666, 1673 | CITYFIREFIGHTER | Voiced |
| mods/cameo/rules/starwars.yaml | 4302, 4310 | swindustrialplant | HitShape |
| mods/cameo/rules/starwars.yaml | 8575, 8604 | swjabbaparty | Cargo |
| mods/cameo/weapons/d2k.yaml | 1009, 1021 | DeathHandCluster | Projectile |
| mods/cameo/weapons/d2k.yaml | 1812, 1820 | o110mm_Gun | Projectile |
| mods/cameo/weapons/d2k.yaml | 1815, 1823 | o110mm_Gun | Warhead@CannonHE_Medium |
| mods/cameo/weapons/d2k.yaml | 1915, 1924 | oDevBullet | Warhead@CannonHE_Medium |
| mods/cameo/weapons/d2k.yaml | 1934, 1948 | o155mm | Warhead@CannonHE_Medium |
| mods/cameo/weapons/d2k.yaml | 2040, 2053 | oDeviatorMissile | Warhead@MissileAP_Heavy |
| mods/cameo/weapons/d2k.yaml | 2188, 2199 | oDeathHandCluster | Projectile |
| mods/cameo/weapons/starwars.yaml | 814, 818 | SWNapalm | Burst |
| mods/cameo/weapons/starwars.yaml | 843, 847 | SWNapalm2 | Burst |
| mods/cameo/weapons/starwars.yaml | 867, 871 | SWNapalm3 | Burst |


**FAIL** — D2 count 170 exceeds the baseline 158: a new duplicate key was introduced.

