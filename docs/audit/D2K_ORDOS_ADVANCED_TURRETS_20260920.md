# D2K Ordos advanced turrets audit — 2026-09-20

## User playtest correction

The 2026-09-20 Ordos playtest correction tightens the two advanced-defense
turrets while preserving their existing 64-facing frames, facings, sequence
offsets, projectile geometry, ranges, reports, and laser damage per shot.

- Both turret defaults use `Scale: 0.9`. The production widget uses standard
  64x48 source icons around a 62x46 interior and a `-1,-1` sprite offset. The
  authentic 64x64 EBFD source icons remain unchanged; separate 64x48 build-menu
  crops render at `Scale: 1`.
- The Gas Turret muzzle origin follows the scaled art at `LocalOffset: 540,0,450`.
  Playtesting identified the Laser Turret's firing barrel on the lower horizontal
  arm. After the half-tile correction landed too low, the source was raised by
  one-quarter tile to the final candidate `LocalOffset: 540,0,194`.
- `ordos_laserturret` fires a three-shot salvo with `BurstDelays: 5`, while
  retaining `ReloadDelay: 55`, range 7275, `LaserZap`, and 10000 damage per
  shot. Its report is the EBFD `PopupTurretAttack.wav`, replacing the authentic
  but vehicle-specific Laser Tank report.
- `ordos_chemturret` is named **Gas Turret** with the exact description
  `Ballistic toxic-gas defense.\n  Strong vs Infantry\n  Weak vs Vehicles`.
- The gas weapon uses the dedicated `^Warhead_Toxic_AntiInfantryDefense`
  profile over `^Warhead_Toxic_Light`, plus `^Projectile_Shell_Light` and
  `^Effect_Chem_Light`. Its local `Warhead@Toxic_Light` deals 20000 damage to
  Ground/Water targets in a 1536-unit (1.5-tile) spread and excludes
  `wall, Mine, ToxinImmune`. `PercentageScale: 0` removes the hidden max-health
  hit. At the impact center this resolves to 40000 against None and 31800
  against Flak. Scout is pinned to `Versus: 100` and receives 20000, exactly
  50% of the unarmored-infantry hit. Light is pinned to `Versus: 40` and
  receives 8000, exactly 20%. Medium, Heavy, and Superheavy are pinned to `Versus: 20`, so
  each receives exactly 4000 damage: 10% of the unarmored-infantry hit before
  distance falloff.
- Gas Turret firing uses the EBFD `ChemTurretAttack.wav`. Both structure firing
  sounds are copied byte-for-byte from the local EBFD SFX archive. SHA256:
  `ChemTurretAttack.wav` =
  `9206203411377dd43df81dac61f61ff5fb241b13defd46020154d0c45a0e4559`;
  `PopupTurretAttack.wav` =
  `eb0927c6c349c6b19526c9a835c8d65bc00b035447523f6ecd8dbf10c2efc1c1`.
- Lethal Gas Turret hits use the D2K-only `ToxicDeath` damage type. D2K
  infantry map it to poisoned death sequence 6 and the poisoned voice, while
  `FireWarheadsOnDeath@Virus` remains restricted to `RA2VirusDeath`. The visual
  therefore matches Yuri's toxic death without spawning `RA2VirusExplode` or
  adding secondary damage.
- The resolved role profile retains `None: 200`, `Flak: 159`, uses 100 for
  Scout, 40 for Light, and 20 for Medium/Heavy/Superheavy, and has no Corrosion physical state. Its impact is
  the new `d2k_toxic_large_explosion`: the original 22-frame
  `d2k_large_explosion` animation rendered through the dedicated full-ramp
  `d2k_toxic_explosion` palette, with no lingering damaging cloud attached.
  The 768-byte palette SHA256 is
  `046724ae18607b2d87be8bfe98c6765eea9dc5563d5c40d14fe5453d7cdad065`.

## Asset provenance

The source icons are the supplied EBFD wiki assets. Their 64x48 build-menu
derivatives are pinned by SHA256:

| In-game asset | Source wiki file page | SHA256 |
| --- | --- | --- |
| `ordos_chemtur_build_icon.png` | [EBFD OR Gas Turret Icon](https://dunerts.wiki.gg/wiki/File:EBFD_OR_Gas_Turret_Icon.png) | `0f0a17e59fa181ba0922241bf4c2c934cbb9e4ba88e549f39c42060e3438d815` |
| `ordos_lasertur_build_icon.png` | [EBFD OR PopUp Turret Icon](https://dunerts.wiki.gg/wiki/File:EBFD_OR_PopUp_Turret_Icon.png) | `e2f8694fd6377ff223ca0d56af6d294546e14c585b3b97340e54c0b6592e9df1` |

## Static contract

The active `ContentPacks/D2k/Ordos/content.yaml` includes the buildings,
weapons, and sequences files. The focused contract in
`tools/tests/test_ordos_advanced_turrets.py` covers buildability and gating,
icon dimensions and hashes, sequence scales and frame layout, the scaled
muzzle origins, laser salvo timing, the exact Gas Turret copy, the resolved
Toxic family, bounded green D2K explosion, and ballistic shell geometry.

The remaining visual gate is an in-game check of the 0.9 turret scale, the
two corrected muzzle origins, the 1.5-tile gas impact radius, and the green impact
effect. The external comparison is
`C:\Users\Blackrobe\Documents\agents\d2k-ebfd-icons\ordos-turret-playtest-correction.png`.

## Validation

- `python -m unittest tools.tests.test_ordos_advanced_turrets -v` — 7 tests,
  all passing.
- The three faction contracts pass 21 tests, including all 7 Ordos tests.
- Empty-warhead and physical-state audits pass. Asset crash references remain
  at zero; the sequence audit retains one unrelated Soviet-airfield baseline.
- The canonical full extraction and `extract_stats.py --check` report 34
  ledgers with zero drift, and `git diff --check` is clean.
- A hidden final boot with the exact pinned engine reached
  `MenuPostProcessEffect.PostWorldLoaded` with zero exception logs.

No build, visible game launch, merge, or `--check-yaml` invocation is part of
this correction.
