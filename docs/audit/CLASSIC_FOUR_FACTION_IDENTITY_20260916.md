# Classic-four faction identity audit (2026-09-16)

Scope: active TD GDI, TD Nod, RA Allies and RA Soviets combat actors after PRs
#401 and #402. The audit applies Aedis's 2026-09-15 request to give complete
duplicate combat cohorts a slight change to each stat like the accepted
Minigunner/Rifle Infantry pattern. It excludes support, economy, MCV,
static-defense, cargo-chassis and hero actors.

## Candidate cohorts

| Cohort | Disposition | Evidence |
|---|---|---|
| Basic rifle infantry | Already distinct; no change | GDI Minigunner, Nod Minigunner, Allied Rifle Infantry and Soviet Rifle Infantry already have distinct resolved chassis and owned weapon values after #401. |
| Rocket Soldier | Applied | The GDI/Nod pair had identical chassis and weapon values. The Allied/Soviet pair had identical chassis except cost and identical baseline weapon values. All four use the same anti-tank/anti-air infantry role, so this is the only complete four-faction duplicate cohort. |
| Engineer | Rejected | Support role; explicitly outside this pass. |
| Harvester / ore truck | Rejected | Economy role; explicitly outside this pass. |
| MCV | Rejected | MCV role; explicitly outside this pass. |
| APC / Chinook transport | Rejected | Cargo chassis; explicitly outside this pass. |
| Commando / Tanya | Rejected | Hero actors; explicitly outside this pass. |
| Guard tower / turret / SAM | Rejected | Static defense; explicitly outside this pass. |
| Scout vehicles | Rejected | Humvee, Buggy and Ranger are related battlefield roles but have different source weapons and target access; Soviets have no same-role four-way counterpart. |
| Main battle tanks | Rejected | GDI Battle Tank, Nod Light Tank, Allied Medium Tank and Soviet Heavy Tank are deliberately different source-game chassis and weapon packages, not duplicate units. |
| Artillery | Rejected | Archer/MLRS, Nod Artillery/SSM, Allied Artillery and Soviet V2 occupy different direct-fire, ballistic and missile roles; there is no exact four-way cohort. |
| Specialist infantry | Rejected | Grenadiers exist only for GDI/Soviets, while flame, sniper, chemical and other specialists do not form complete equivalent four-way cohorts. |

## Applied Rocket Soldier values

| Faction | Cost | HP | Speed | Range | Damage | Identity |
|---|---:|---:|---:|---:|---:|---|
| TD GDI | 450 | 16000 | 42 | 6500 | 15800 | Sturdiest, disciplined reach, slower advance. |
| TD Nod | 390 | 14000 | 48 | 6028 | 16882 | Cheapest, faster, shorter-ranged and more aggressive. |
| RA Allies | 480 | 13000 | 54 | 7500 | 11500 | Fastest and longest-ranged, with the lightest frame and shot. |
| RA Soviets | 440 | 15000 | 46 | 6910 | 13216 | Tougher and slower than Allies, with the harder RA shot. |

This is a deliberate identity exception to formula-pinned cost. The unrounded
formula prices are GDI 423.35, Nod 419.46, Allies 414.17 and Soviets 427.26;
the authored costs above follow the explicit request to drift every stat and
preserve the two source-pair totals, rather than claiming formula-neutral cost.

The cohort keeps the exact pre-change arithmetic means: cost 440, HP 14500,
speed 47.5, range 6734.5 and damage 14349.5. Each source pair also retains its
HP, range, damage and cost sum. Preserving the damage sums inside the shared-
cadence pairs (TD 32682 at reload 56; RA 24716 at reload 50) keeps total nominal
DPS unchanged. Target masks, cadence, burst, armor, upgrade gates, percentage
coefficients and effect/state types are unchanged. Flat damage and any folded
percentage or damage-linked state magnitude intentionally follow each faction's
new weapon damage. GDI normal/advanced-targeting weapons and Allied normal/cryo
weapons carry the same new range and damage inside their mutually exclusive
pairs. The generic `E3` map compatibility alias retains its legacy chassis and
generic weapons.
