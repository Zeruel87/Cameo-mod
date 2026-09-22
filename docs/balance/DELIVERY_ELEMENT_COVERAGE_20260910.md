# Delivery and element coverage — 10 September 2026

The four requested Sonic combinations now have 12 active templates and eight converted weapons. The pure Sonic emitter retains its original family. The other authored combinations and missing options below come from the active manifest and generator definitions. An absent option is not automatically a missing gameplay requirement.

## Exact named element combinations

Delivery parents are removed before matching the remaining elemental proportions. Thus Cryo means Laser x Prism, Plasma means Flame x Chemical, and Quantum means Railgun x Laser x Tesla. The full JSON preserves repeated-parent weights; this table does not assert every mixture is 50/50.

| Delivery | Represented named combinations | Unrepresented named elements |
| --- | --- | --- |
| Bullet | Flame (BulletFire); Chemical (BulletChem); Tesla (BulletTesla); Sonic (BulletSonic); Cryo (BulletCryo); Thermobaric (BulletThermobaric) | Toxic, Laser, Prism, Magic, Nuclear, Railgun, Plasma, Quantum, Waveforce |
| Cannon | Flame (CannonFire); Chemical (CannonChem); Tesla (CannonTesla); Sonic (CannonSonic); Nuclear (CannonNuke); Cryo (CannonCryo) | Toxic, Laser, Prism, Magic, Railgun, Plasma, Quantum, Thermobaric, Waveforce |
| Missile | Flame (MissileFire); Chemical (MissileChem); Tesla (MissileTesla); Sonic (MissileSonic); Nuclear (MissileNuke); Cryo (MissileCryo); Quantum (MissileQuantum); Thermobaric (MissileThermobaric) | Toxic, Laser, Prism, Magic, Railgun, Plasma, Waveforce |
| Flak | Cryo (FlakCryo) | Flame, Chemical, Toxic, Laser, Prism, Tesla, Sonic, Magic, Nuclear, Railgun, Plasma, Quantum, Thermobaric, Waveforce |
| Arrow | None | Flame, Chemical, Toxic, Laser, Prism, Tesla, Sonic, Magic, Nuclear, Railgun, Cryo, Plasma, Quantum, Thermobaric, Waveforce |
| Melee | None | Flame, Chemical, Toxic, Laser, Prism, Tesla, Sonic, Magic, Nuclear, Railgun, Cryo, Plasma, Quantum, Thermobaric, Waveforce |
| GrenadeBlast | Flame (Thermobaric); Sonic (BlastSonic); Cryo (BlastCryo) | Chemical, Toxic, Laser, Prism, Tesla, Magic, Nuclear, Railgun, Plasma, Quantum, Thermobaric, Waveforce |

BulletHE also exists as Bullet x Demolition. PhotonCannon is a multi-delivery mixture and is retained in the raw inventory rather than mislabeled as a simple CannonPlasma or MissileQuantum family. GrenadeBlast is a grouping for the explicit Demolition/Concussion delivery; BlastSonic uses equal Demolition, Concussion and Sonic shares as Aedis specified at 17:38.

## Work still needed

1. Scoped insertion is complete. Existing live shield slots were reserved, and pre-addition plating calibration was retained. All 2969 prior resolved weapons were unchanged by the template addition. Full-table regeneration remains a separate review because it renormalizes unrelated families.
2. Eight weapon mappings are complete: Kodiak cannon to CannonSonic; Hellfire/Zone Hellfire to MissileSonic; disc grenade and bomb to BlastSonic; Vulcan/assault rounds to BulletSonic. Pure sonic-wave emitters retain Sonic. The assault weapons retain their existing dual-target role.
3. The eight converted weapons pass the centered role-damage comparison without further raw-damage increases. Minimum gains over base range from 5.63% to 59.69% in the checked armor set. Burst, reload, projectile and other non-warhead fields remain unchanged. The existing debuff duration, range and targets are preserved explicitly; blast geometry and armor curves intentionally change.
4. Audit active bespoke multi-warhead stacks for a concrete unmet delivery/element role. Prioritize existing weapons that need a family; do not create every empty cell merely for symmetry.
5. All 67 generated ledger outputs are reconciled. Three raw ledgers change only armament fields. The new templates change the diagnostic shield mean from 177.11 to 180.43, which refreshes derived context values across other factions; their live rules do not change. No upgrade prices or HP/cost changes are applied. Historical converters remain fail-closed, with exact test-only before/current fixtures for their earlier checkpoints.

## Scope and reproducibility

The primitive inventory has 11 deliveries x 10 elements, 26 authored combination families and 43 represented primitive cells. The exact named matrix above additionally distinguishes composite elements. This is not a universal content-completeness certificate. Direct armament ancestry can include removed inherited payloads; dynamic actors, secondary weapons and map-local scripts need separate analysis.

```powershell
python tools/audit/delivery_element_inventory.py --output delivery-element-inventory.json
```
