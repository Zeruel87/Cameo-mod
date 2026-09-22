# Weapon redesign research and current review boundary

Status: **proposal only — no gameplay authority is implied by this document.**

## Current upstream-master review boundary

After PR #320, the active reachable queue is **14 definitions in 12 inheritance
families**. Every remaining family needs a player-facing role, progression, or
state-delivery decision; none has a mechanically exact fold. The generated
[decision bundle](../audit/latest/weapon_decision_bundle.md) is the authoritative
current grouping because it resolves the active include graph and records every
consumer and delivery chain.

| review group | definitions | maintainer decision needed |
|---|---:|---|
| Tactical missile payloads | 2 | Choose one role for the shared silo/crate missile closure before changing either chemical or conventional delivery. |
| Ixian Air Drone base and paid gun | 2 | Define a monotonic base-to-Tungsten progression across its four distinct damage profiles. |
| Allied vehicle closures | 4 | Choose the Tank Destroyer, Tiger, and Sheridan cannon/missile roles together with their paid replacements. |
| Specialist multi-consumer roles | 2 | Confirm Rapier AA and the Raynor/Pythean shared-gun role before any profile becomes canonical. |
| TS progression and state routes | 2 | Choose the Cannon Tug progression and Disruptor's Magic/Tesla state-delivery contract. |
| Japan Chi-Ha base/plasma closure | 2 | Define the coordinated vehicle/plasma progression without silently dropping its electrical state route. |

These are holds, not conversion candidates. Preserve their resolved profiles and
active closures until a maintainer makes the relevant role call. HydraSpit is not
part of this queue: it remains a reviewed raw structural exception with four
separate 18,000-damage profiles.

## Historical pre-PR #320 research snapshot

The analysis below records the broader pre-PR #320 planning queue. Most entries
were resolved, reclassified, or superseded by the merged pipeline; it is useful
as research history only and must not be treated as the live conversion queue.

Two evidence-backed state composites were removed from that historical open queue
without changing gameplay: Devastator `ExplosiveDebris` remains a weak wide blast
plus a close burning payload, and `SyndicateFireballLauncherExplode` retains all
nine independently applied Temperature-bearing nodes.

## Proposed redesign contract

If the maintainer authorizes this package, implementation should follow these rules:

1. Preserve nominal flat damage, cadence, projectile, effects, targeting, relationships,
   and non-damage payloads unless a row explicitly says otherwise.
2. Move overlapping ordinary damage onto the named canonical family. This intentionally
   changes armor effectiveness and blast geometry.
3. Keep documented status, relationship, and outer-ring routes separate. Do not fake
   equivalence by combining independently rounded state applications.
4. Treat every paid or rank replacement as one progression closure. An upgrade must not
   become weaker against the unit's stated primary targets.
5. Keep pricing and the 100 currently unreached stacks outside this package.

`Convert` means one canonical main. `Split` means consolidate only the ordinary overlap
while retaining a named status/route payload. `Preserve` means fingerprint the current
role as intentional. `Hold` means the evidence is not yet sufficient for a safe live edit.

## Target and route decisions — 23 definitions / 18 families

| family | recommendation | main player-visible consequence and constraint |
|---|---|---|
| `RA160mmE_rad_elite` | **Split:** `Chemical_Light` 108k core + `Nuclear_Super` 36k | Elite Siege Chopper keeps nuclear/radiation delivery; ordinary damage becomes consistently corrosive. Preserve deployed/rank/doctrine gates. |
| `SandmarineTuskFire` | **Split:** `MissileHE_Heavy` 80k + AP 2k + `Flame_Light` 6k | Incendiary Sand Marine/Big Shiee matches the base rocket while retaining heat and the small AP impact. Keep cryo/twin routes separate. |
| `SteelVulcan*` (4) | **Convert:** `Bullet_Medium` 6k, Ground/Water | Cougar and Sentry Vulcan become clearly anti-infantry/light armor; HE splash and incidental air collateral disappear. Preserve resonance/bounce chain scales. |
| `ArmoredCarMG_AA*` (2) | **Split:** `Bullet_Medium` 16k Air-only; Waveforce retains Railgun 3k | Japan Armored Car AA follows the ground gun's bullet identity while keeping the paid Waveforce payload and separate AG/AA gates. |
| `GradRockets*` (2) | **Convert:** `MissileHE_Heavy` 16k | Grad loses the wider Concussion layer and incidental air collateral. Preserve Scorched Earth replacement and death route. |
| `CabalReaperMissiles` | **Convert:** `MissileHE_Medium` 32k | Cyborg Reaper receives one medium ground-missile profile; preserve the separate 32k AA sibling. |
| `CabalHeavyReaperMissiles` | **Convert:** `MissileHE_Heavy` 48k | Heavy Reaper receives the heavier form of the same role; preserve the separate 48k AA sibling. |
| `Future_Cryocopter_Rocket` | **Split:** `MissileAP_Medium` 32k plus the existing hostile 16k/allied 8k relationship slice | Preserves 48k hostile versus 40k allied impact and three cryo applications; do not flatten the relationship asymmetry. |
| `GLBarrelExplode` | **Split:** `Demolition_Heavy` 100k inner + unchanged hostile 14k outer ring | Shared booby-trap/barrel contract gains one inner profile while preserving ally exclusion and the authored wide ring across 560 actors. |
| `GuardianShoot` | **Convert:** `Concussion_Medium` 24k | Zerg Guardian loses the Light/Ship-only slice and keeps one medium bomber blast. |
| `HMG_fremen` | **Convert:** `Bullet_Medium` 6k | Fremen HMG becomes consistently anti-infantry/light; apply locally rather than changing the shared HMG parent. |
| `NaxCorrosionRocketTrooper_elite` | **Convert:** `MissileAP_Medium` 16k | Lunar Rocket follows its already-consolidated parent; preserve corrosion, fragment chain, rank, and garrison routes. |
| `RashidanGun_upgrade` | **Split:** `Bullet_Medium` 12k all-target + 4k ground bonus | Tungsten upgrade remains 16k ground/12k air with one bullet identity. Preserve base and garrison gates. |
| `SteelHoverMissile_elite` | **Convert:** `MissileAP_Light` 16k | Implements the authored red-missile 2x damage contract without the Arrow profile. Actor remains production-disabled. |
| `TS30mmRail` | **Convert:** `Flak_Medium` 18k | Falcon Enforcer absorbs the 2k legacy remainder into its selected core; preserve rail effect and paid gating. |
| `TSAegisMissile` | **Convert:** `MissileAA_Medium` 25k, Air-only | Production-disabled Aegis becomes an actual dedicated AA cruiser and loses undocumented ground/naval attack. |
| `Tentacle` | **Convert:** `Melee_Heavy` 25k, Ground-only | Sunken Colony keeps a clear tentacle role and loses cannon splash/water damage. Preserve the `sunken` condition. |
| `v1rockets` | **Convert:** `MissileHE_Medium` 24k | V1 becomes one ground artillery rocket and loses incidental air collateral. Preserve thermobaric replacement and death weapon. |

## State, legacy, and numbered decisions — 19 definitions / 12 families

| family | recommendation | main player-visible consequence and constraint |
|---|---|---|
| `NaxGrilleArty*` (4) | **Split:** conventional 48k to `CannonHE_Heavy`; Lunar retains Tesla 16k + extra 8k | Grille becomes heavy artillery while the paid Vril/Lunar electrical payload remains separate. Includes elite, bunker, and Shoe Karn consumers. |
| `HammerTankCannon*` (2) | **Convert:** base `CannonHE_Heavy` 12k; paid `Thermobaric_Heavy` 16k with Temperature share 25 | Clear cannon-to-thermobaric progression. Preserve armament and death-route swap. |
| `KotinCannon*` (2) | **Convert:** base `CannonHE_Heavy` 12k; paid `Thermobaric_Heavy` 16k with Temperature share 25 | Same policy as Hammer while retaining the Kotin radiation field unchanged. |
| `NaxSturmArty*` (2) | **Split:** conventional 80k to `Demolition_Heavy`; Lunar retains Tesla payload | Sturm becomes a true heavy demolition/bunker-buster shot. Preserve Naxis tank and Schwarzer Mond defense closures. |
| `SkyHawkCannon*` (2) | **Split:** base `CannonAP_Light` 16k; paid version 12k AP + Tesla 4k and extra 2k | Base becomes more anti-armor; paid plasma keeps a measurable electrical/integrity bonus. Review with simultaneous Sky Hawk upgrades. |
| `GrenadeRA` | **Convert:** `Demolition_Light` 16k, remove base Temperature | Soviet Grenadier gets a normal base grenade; Scorched Earth becomes the distinct fire/thermobaric upgrade. Preserve primary/garrison/death pairs. |
| `LightTank2Missiles` | **Convert:** `MissileAP_Medium` 8k | Nod Light Tank Mk. II Black Market missile becomes clean anti-vehicle/air and loses incidental burn. |
| `TSChem120mmx` | **Split:** chemical 60k unchanged + `CannonHE_Medium` 33.6k | Removes only the numbered 3.6k curve without increasing corrosion-bearing damage. Review with base `TS120mmx`. |
| `TSSonicZapWeapon` | **Hold progression redesign** | Base Magic/Tesla identity is ambiguous and the paid Sonic replacement is no better than 0.88x across judged core armor. Do not register away the downgrade. |
| `Type97PlasmaCannon` | **Hold coordinated base/plasma redesign** | Current paid plasma drops to 0.78x Wood and 0.81x Scout. Its electrical split is defensible, but progression must be fixed with base `Type97Cannon`. |
| `facedancer_grenade` | **Convert:** fold HE 20k into `MissileAP_Heavy` for 180k | Face Dancer becomes a coherent anti-heavy direct hit with less HE splash. Retain every percentage/status companion. |
| `TS120mmx` | **Convert:** `CannonHE_Medium` 63.6k | Removes Concussion and numbered legacy curves for the active Forgotten Experimental Mammoth. Similar Tiberian Alliances definitions are inactive and do not govern live behavior. |

## Ordinary role decisions — 33 definitions / 26 families

| family | recommendation | main player-visible consequence and constraint |
|---|---|---|
| `LatinBuggyChaingun*` (2) | **Convert candidate:** `Bullet_Medium` 8k | Raider/Tortuga gun becomes anti-infantry/light and loses AP/Flak universality. Base/elite move together. |
| `LatinBuggyRocket*` (2) | **Convert candidate:** `MissileAP_Medium` 40k | Raider/Nokana rocket becomes sharply anti-vehicle with much less splash. Confirm shared Nokana role first. |
| `SCScourgeDroneExplosion*` (2) | **Convert:** `Demolition_Heavy` 20k | Scourge Drone attack/death blast becomes concentrated demolition; aliases remain identical. |
| `SCScourgeExplosion*` (2) | **Convert:** `MissileAA_Heavy` 100k, Air-only | Zerg Scourge becomes honest dedicated AA suicide damage; attack/death payloads change together. |
| `TSTacticalMissileDamage*` (2) | **Hold parent-payload review** | Tactical, chemical, silo, and crate routes must be understood before introducing canonical percentage/blast behavior. |
| `d2k_air_drone_guns*` (2) | **Hold progression redesign** | Paid Tungsten version falls to 0.70x unarmored and 0.83x Scout. Base and upgrade need an explicitly monotonic Bullet/Flak-to-AP progression. |
| `tkmjuggap*` (2) | **Convert candidate:** `CannonAP_Light` 8k | Paid AP gun becomes vehicle-specialized and weaker versus infantry; preserve its current 1.39–1.93x vehicle gains. |
| `110mm_Gun` | **Convert:** `CannonAP_Light` 30k | Ixian Gun Turret becomes clearly anti-vehicle and loses broad infantry/building splash. |
| `AlliedTankDestroyerCannon` | **Hold progression redesign** | Candidate is AP Light 24k, but the Cryo replacement already falls to 0.91x Superheavy/0.92x Heavy. |
| `Aphid_AA` | **Convert with closure:** `MissileAA_Heavy` 16k, Air-only | Rapier secondary becomes genuine AA; Cryo replacement must remain monotonic. |
| `GlaveCanon` | **Convert candidate:** `Railgun_Heavy` 16k | Protoss Adept gains focused energy/vehicle damage and loses demolition splash; source role needs confirmation. |
| `JimRaynorMachineGun` | **Hold; split consumers if required** | A Bullet profile would narrow Raynor's “strong against everything” role and may not fit the Pythean aircraft consumer. |
| `RA2Terrorist` | **Isolate descendants, then convert:** `Demolition_Heavy` 100k | Bombs become structure/demolition focused with less broad Concussion coverage. Never edit the large shared root in place. |
| `SandmarineTuskTwin` | **Preserve candidate:** intentional generalist ground role | Maintains the advertised “strong against everything ground” super-unit behavior for Sand Marine/Big Shiee. |
| `ScoutMG` | **Convert candidate:** `Bullet_Medium` 4k, Ground-only | Protoss Scout ground guns lose demolition splash; separate AA weapon remains responsible for air. |
| `SheridanCannon` | **Convert with closure:** `CannonAP_Light` 16k | Cannon becomes the vehicle part of Sheridan's combined kit; coordinate Vulcan, missiles, and Cryo replacements. |
| `SheridanMissiles` | **Convert with closure:** `MissileHE_Medium` 16k | Missile becomes one all-target splash profile; combined Cryo route must not remain 0.94x Steel. |
| `SiegeTankCannon` | **Convert candidate:** `CannonHE_Heavy` 30k | Terran Siege Tank gains a clearer siege/building splash role and loses focused AP contribution. |
| `TSBoatcannon` | **Hold progression redesign** | Candidate is Demolition Heavy 18k, but the chemical replacement is only 0.49x Wood and 0.73x Steel. |
| `TSBomb` | **Convert with closure:** `Demolition_Heavy` 20k | Orca bomb becomes vehicle/building focused; Sonic replacement must not remain 0.79x Scout/0.83x unarmored. |
| `TigerCannon` | **Hold progression redesign** | Candidate is CannonHE Heavy 16k, but Cryo loses Wood, Medium, and Scout performance. |
| `Type97Cannon` | **Hold coordinated base/plasma redesign** | Candidate is `CannonAP_Medium` 12k for the “strong vs vehicles” role; paid plasma monotonicity must be solved simultaneously. |
| `YakovlevCannon` | **Convert candidate:** `Bullet_Medium` 8k | Yakovlev becomes infantry/light focused and loses universal HE/AP/Flak coverage. |
| `YakovlevCannon_elite` | **Follow base Yakovlev decision** | Preserve elite cadence/range and stolen-tech routing; never reprofile independently. |
| `ordos_autogunturret` | **Preserve candidate:** intentional broad autogun role | Keeps good infantry/vehicle/building coverage but weakness versus tanks; requires maintainer acceptance as a deliberate generalist. |
| `t30shell` | **Convert candidate:** `Railgun_Heavy` 80k, scale 3000, spread 512 | T-30 becomes vehicle-focused and loses demolition splash/structure bias; summed percentage units remain 1200. |

## Suggested execution order after authorization

1. Resolve the explicit `Preserve` candidates as fingerprints only.
2. Apply isolated single-family conversions without paid replacements.
3. Apply state/relationship splits with exact resolved comparisons.
4. Repair every paid progression closure and prove role-target monotonicity.
5. Handle global shared roots (`GLBarrelExplode`, `RA2Terrorist`) last through
   descendant isolation, then run the full static and boot gates.
