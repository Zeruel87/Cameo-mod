# Basic Infantry Damage Audit

> ⛔ **ARCHIVED 2026-08-23.** A one-off dated audit, not live evidence. Current audit output is
> regenerated into `docs/audit/latest/` by `bash tools/audit/run_all.sh`.

Date: 2026-08-02
Scope: active factions loaded by `mods/cameo/mod.yaml`; unupgraded, non-elite entry-level combat infantry only.

## Executive summary

The basic-infantry roster is not on a common damage scale. The most obvious conventional-rifle mismatch is the RA2 Soviet Conscript: its carbine deals 2,000 damage once per 18 ticks, while the Allied G.I. deals the same 2,000 damage in a three-round burst with a 15-tick reload. On the simple `damage × burst / reload` measure, the G.I. has **3.6 times** the Conscript's nominal output, while costing only twice as much.

The spread is much wider once crossover factions are included. Some of that is intentional because melee units, shields, deployment, anti-air capability, upgrades, health, range, and multi-warhead weapons have different value. Even so, the ordinary firearm units alone vary enough to justify a dedicated normalization pass.

No balance values were changed by this audit.

## Method

- Followed the active `Include`, `Rules`, and `Weapons` lists in `mods/cameo/mod.yaml`.
- Selected the first general-purpose combat infantry available from the faction's normal infantry production structure.
- Excluded engineers, dogs, dedicated anti-tank/anti-air troops, commandos, promotion replacements, and elite/upgraded weapons.
- `Nominal output` is `primary Damage × Burst / ReloadDelay × 100`. It is a comparison index, not literal in-game DPS. Burst delays, accuracy, armor modifiers, projectile travel, splash, conditions, and multiple simultaneous warheads can change real results.
- A `complex` result means the weapon combines several inherited damage/targeting warheads and should be measured with a controlled in-game or utility test instead of adding every YAML `Damage` line blindly.

## Active faction roster

### Tiberian Dawn

| Faction | Basic infantry | Actor | Cost | HP | Base weapon | Range | Damage / burst / reload | Nominal output | Notes |
|---|---|---|---:|---:|---|---:|---|---:|---|
| GDI TD | GDI Minigunner | `td_gdi_minigunner` | 100 | 31,000 | `td_gdi_minigunner_minigun` | 5,499 | 2,000 × 4 / 50 | 16,000 | Longer range than Nod; AP upgrade excluded. |
| Nod TD | Nod Minigunner | `td_nod_minigunner` | 100 | 30,000 | `td_nod_minigunner_minigun` | 4,609 | 2,000 × 4 / 50 | 16,000 | Shorter burst delay than GDI; laser upgrade excluded. |

### Red Alert

| Faction | Basic infantry | Actor | Cost | HP | Base weapon | Range | Damage / burst / reload | Nominal output | Notes |
|---|---|---|---:|---:|---|---:|---|---:|---|
| Allies RA1 | Rifle Infantry | `ra1_allies_rifleinfantry` | 100 | 27,000 | `ra1_allies_rifleinfantry_carbine` | 5,500 | 2,000 × 3 / 50 | 12,000 | Cryo upgrade excluded. |
| Soviets RA1 | Rifle Infantry | `ra1_soviets_rifleinfantry` | 100 | 34,000 | `ra1_soviets_rifleinfantry_carbine` | 4,668 | 2,000 × 3 / 50 | 12,000 | Replaced by the AK-47 Conscript after Conscription doctrine. |
| Soviets RA1, Conscription | AK-47 Conscript | `ra1_soviets_ak47conscript` | 200 | 44,000 | `ra1_soviets_ak47conscript_rifle` | 4,822 | 2,000 × 3 / 11 | 54,545 | Very large doctrine power jump: 4.55× the base rifleman's nominal output and much more HP for 2× cost. |
| Japan RA1 | Imperial Scoutsman | `japan_imperialscoutsman` | 200 | 15,000 | `japan_imperialscoutsman_rifle` | 6,000 | 4,000 × 1 / 50 | 8,000 | Long range and attacks air, but extremely fragile and low-output for its price. |

### Tiberian Sun

| Faction | Basic infantry | Actor | Cost | HP | Base weapon | Range | Damage / burst / reload | Nominal output | Notes |
|---|---|---|---:|---:|---|---:|---|---:|---|
| GDI TS | Light Infantry | `ts_gdi_lightinfantry` | 120 | 16,000 | `TSMinigun` | 4,062 | 2,000 × 1 / 12 | 16,667 | Uses the shared `TSE1` baseline. |
| Nod TS | Light Infantry | `ts_nod_lightinfantry` | 120 | 16,000 | `TSMinigun` | 4,062 | 2,000 × 1 / 12 | 16,667 | Tiberium-lens laser upgrade excluded. |
| Forgotten TS | Mutant | `forgotten_mutant` | 160 | 45,000 | `forgotten_mutant_dualwield` | 5,219 | 2,000 × 2 / 18 | 22,222 | Strong health, range, and output for only 33% more cost than TS light infantry. |
| CABAL TS | Cyborg Infantry | `cabal_cyborginfantry` | 500 | 45,000 | `CabalCyborgChaingun` | 5,800 | 10,000 × 1 / 60 | 16,667 | Expensive armored infantry; weapon can also target air. Raw output alone understates its role. |

### Red Alert 2

| Faction | Basic infantry | Actor | Cost | HP | Base weapon | Range | Damage / burst / reload | Nominal output | Notes |
|---|---|---|---:|---:|---|---:|---|---:|---|
| Allies RA2 | G.I. | `ra2_allies_gi` | 200 | 50,000 | `ra2_allies_gi_mg` | 4,680 | 2,000 × 3 / 15 | 40,000 | Can deploy; this row uses the weaker undeployed weapon. |
| Soviets RA2 | Conscript | `ra2_soviets_conscript` | 100 | 26,000 | `ra2_soviets_conscript_carbine` | 4,500 | 2,000 × 1 / 18 | 11,111 | Main confirmed underperformer. G.I. has 3.6× output and 1.92× HP for 2× cost. |
| Yuri | Yuri Initiate | `yuri_initiate` | 200 | 24,000 | `RA2PsychicJab` | 4,440 | complex / 15 | complex | Multi-warhead, all-target weapon; power-surge upgrade excluded. Requires controlled testing. |

### Red Alert 2 Mod factions

| Faction | Basic infantry | Actor | Cost | HP | Base weapon | Range | Damage / burst / reload | Nominal output | Notes |
|---|---|---|---:|---:|---|---:|---|---:|---|
| Asian Alliance | Asian Militia | `asianalliance_asianmilitia` | 110 | 24,000 | `asianalliance_asianmilitia_shotgun` | 4,500 | 6,000 × 1 / 50 | 12,000 | Grenadier doctrine replacement excluded. |
| Steel Consortium | Clone Trooper | `steelconsortium_clonetrooper` | 143 | 17,000 | `SteelCloneGun` | 6,463 | complex / 25 | complex | Long range, attacks air, and combines several inherited weapon classes. |
| Latin Syndicate | Latin Militia | `latinsyndicate_latinmilitia` | 130 | 25,000 | `latinsyndicate_latinmilitia_ak47` | 5,395 | 2,000 × 3 / 22 | 27,273 | Molotov doctrine and stolen-tech chainguns excluded. Strong firearm baseline for cost. |
| Naxis | Naxi Rifle Soldier | `naxis_naxiriflesoldier` | 100 | 20,000 | `naxis_naxiriflesoldier_rifle` | 5,000 | 4,000 × 1 / 50 | 8,000 | Even lower nominal output than the RA2 Conscript, partly offset by range. |
| Schwarzer Mond | Lunar Soldier | `schwarzermond_lunarsoldier` | 500 | 30,000 | `schwarzermond_lunarsoldier_rifle` | 6,000 | 12,000 × 1 / 50 | 24,000 | YAML explicitly says this 2×-Japan damage baseline is intentional and flagged for in-game testing. |
| FutureTech | Enforcer | `futuretech_enforcer` | 300 | 30,000 | `FutureEnforcerShotgun` | 3,000 | complex / 40 | complex | Multi-warhead shotgun; can deploy. Needs controlled testing. |
| TKM | Rifleman | `tkm_rifleman` | 120 | 29,000 | `tkm_rifleman_rifle` | 5,042 | 6,000 × 1 / 75 | 8,000 | Low sustained output but respectable health/range; semi-auto upgrade excluded. |

### Dune 2000 / Dune Universe

| Faction | Basic infantry | Actor | Cost | HP | Base weapon | Range | Damage / burst / reload | Nominal output | Notes |
|---|---|---|---:|---:|---|---:|---|---:|---|
| Atreides DU | None | — | — | — | — | — | — | — | Active faction file explicitly contains `# No infantry units.` |
| Harkonnen DU | Light Infantry | `light_inf` | 150 | 40,000 | `light_inf_lmg` | 5,475 | 2,000 × 1 / 20 | 10,000 | Uses the shared non-Ordos/non-Ixian actor. |
| Ixian DU | Ixian Light Infantry | `ixian_lightinfantry` | 150 | 32,000 | `light_inf_lmg` | 5,475 | 2,000 × 1 / 20 | 10,000 | Same base gun as Harkonnen but 20% less HP; needle-gun upgrade excluded. |
| Ordos DU | Ordos Light Infantry | `ordos_lightinfantry` | 120 | 28,000 | `light_inf_lmg` | 5,475 | 2,000 × 1 / 20 | 10,000 | Same base output for lower cost and lower HP; laser-cartridge upgrade excluded. |

### StarCraft

| Faction | Basic infantry | Actor | Cost | HP | Base weapon | Range | Damage / burst / reload | Nominal output | Notes |
|---|---|---|---:|---:|---|---:|---|---:|---|
| Terran | Marine | `terran_marine` | 689 | 41,000 | `MarineMG` | 6,105 | 12,000 × 3 / 26 | 138,462 | Attacks ground and air and combines inherited warhead classes. Raw index likely exaggerates direct comparability. |
| Protoss | Zealot | `protoss_zealot` | 300 | 40,000 | `psi_blades` | 1,335 | 8,000 × 2 / 30 | 53,333 | Melee; shield value is not represented by HP or this index. |
| Zerg | Zergling | `zerg_zergling` | 200 | 11,000 | `ZerglingClaw` | 1,350 | 2,000 × 1 / 11 | 18,182 | Melee, very low HP, and has an actor `FireDelay: 3`; should be tested as a swarm unit. |

### Warcraft II

| Faction | Basic infantry | Actor | Cost | HP | Base weapon | Range | Damage / burst / reload | Nominal output | Notes |
|---|---|---|---:|---:|---|---:|---|---:|---|
| Humans WC2 | Footman | `wc2_humans_footman` | 500 | 50,000 | `wc2footmanslice` | 1,333 | 12,000 × 1 / 15 | 80,000 | Melee; actor has `FireDelay: 5`. |
| Orcs WC2 | Grunt | `wc2_orcs_grunt` | 600 | 65,000 | `wc2gruntslice` | 1,555 | 16,000 × 1 / 18 | 88,889 | Melee; higher cost, HP, range, and output than Footman. |

### Outpost 2

| Faction | Basic infantry | Notes |
|---|---|---|
| Eden | None | The active faction is vehicle/structure based and exposes no normal infantry roster. |
| Plymouth | None | The active faction is vehicle/structure based and exposes no normal infantry roster. |

## Priority balance findings

1. **RA2 Conscript is genuinely weak, not just visually weak.** Its nominal output is 27.8% of an undeployed G.I.'s, while its HP is 52% and its cost is 50%. The G.I. therefore wins both per-unit combat and nominal damage-per-credit.
2. **The low-output firearm cluster needs review.** Japan Scoutsman, Naxi Rifle Soldier, and TKM Rifleman each score 8,000; Dune light infantry score 10,000; RA2 Conscript scores 11,111. Their range/health differences do not automatically explain their large gap from Latin Militia (27,273), G.I. (40,000), or the RA1 AK Conscript (54,545).
3. **RA1 Conscription is a major discontinuity.** The AK Conscript costs twice the Soviet Rifle Infantry but has about 4.55× nominal output and 29% more HP. If the doctrine has no equally large opportunity cost, it is likely overtuned.
4. **Forgotten Mutant is unusually efficient inside the TS group.** For 33% more credits than TS Light Infantry it gains about 33% nominal output, 181% more HP, and substantially more range.
5. **Do not normalize crossover melee and complex weapons from YAML damage alone.** Terran, Protoss, Zerg, Warcraft II, Yuri, Steel Consortium, and FutureTech need controlled time-to-kill tests because range, shields, multi-warheads, and melee contact time dominate the paper figure.

## Recommended next pass

Use a fixed test target for each relevant armor class and record time-to-kill at rookie rank with no upgrades. Start with the conventional firearm group:

`td_gdi_minigunner`, `td_nod_minigunner`, `ra1_allies_rifleinfantry`, `ra1_soviets_rifleinfantry`, `japan_imperialscoutsman`, `ts_gdi_lightinfantry`, `ts_nod_lightinfantry`, `ra2_allies_gi` (undeployed), `ra2_soviets_conscript`, `asianalliance_asianmilitia`, `latinsyndicate_latinmilitia`, `naxis_naxiriflesoldier`, `tkm_rifleman`, `light_inf`, `ixian_lightinfantry`, and `ordos_lightinfantry`.

That test will separate real damage imbalance from accuracy, armor-versus modifiers, projectile misses, and burst-cycle behavior before any values are edited.
