# Original Unit Stats — ground-truth matrix for relative balancing

**Purpose.** Real stats from the *source games*, so faction identity and relative unit
strength are derived from DATA, not assumption. Companion to `FACTION_IDENTITY.md`
(the lean directions) and the balance pipeline (the mechanical enforcement).

## Two hard-won rules (2026-07-25, from the maintainer + the data)

1. **Faction identity is PER-UNIT-TYPE, not global.** A faction can be tanky in one
   type and frail in another. Confirmed by source stats:
   - **RA2 Soviets:** *infantry weak*, *tanks strongest & slowest*. **Allies:** *infantry
     tankiest/most-powerful & slow*, *tanks weakest & fast*. (So a Soviet-infantry frail
     reading is CORRECT, not a bug.)
   - **StarCraft Terran:** *infantry frail* (Marine 40 HP), *vehicles tanky* (Siege 150).
   - **Protoss:** tanky in every type (shields). **Zerg:** small units frailest/cheapest,
     Ultralisk a monster-tank.
   → The leans in `FACTION_IDENTITY.md` are the **infantry** leans; a faction's vehicle
   / aircraft lean is set separately (from this matrix) in the vehicle/aircraft passes.
2. **The in-game unit template encodes the role — trust it, don't override by HP.**
   `LineBreaker` = melee-range VEHICLE (heavy assault: Ultralisk, WC2 Knight/Ogre),
   `MainBattleTank` = tank, `MeleeInfantry`/`ScoutInfantry`/… = infantry. Balance class
   follows the template subtype; do not force a unit into another class because its HP
   looks big for the class.

---

## The three-layer balancing framework (maintainer plan 2026-07-25)

Balance interpolates THREE reference layers. The original stats are a **rough identity
lookup, NOT a prescription** — the source games were often poorly balanced (e.g. RA1
multiplayer devolved to main-battle-tank spam because everything else was inferior; Cameo
instead buffed the Mammoth's HP/firepower). So we mine them for *who a unit is*, then set
numbers ourselves.

| Layer | What | Use |
|---|---|---|
| **1. Original-game identity** (this doc, normalized per-game) | source stats ÷ that game's basic combat unit → relative role | *who each unit/faction is* — the identity lookup (inspiration only) |
| **2. Old-balance snapshot** (`docs/balance/*.json` ledger, via `extract_stats.py`) | our units' current pre-rebalance stats | *keep what already works* — only change what conflicts |
| **3. Formula pipeline** (`FORMULA_V2.md` + converter) | class baselines, Δ≤1, 5-stat uniqueness | *the mechanical target* |

**Interpolation rule (per unit):** start from Layer 2 (keep the current stat if it's fine
and non-conflicting) → bias toward Layer 1 (its faction/role identity) → enforce Layer 3
(Δ≤1, unique, class baseline). Result: coherent, identity-true, mechanically valid.

**Cross-game comparison is invalid on raw numbers** (WC2 HP 30–150, SC 25–500, C&C in the
thousands) — only *relative role within a game* transfers. Normalize each game to its basic
combat unit before reading identity across games.

**Sourcing gaps:** Cameo-original units (no original twin) extrapolate from the nearest
real unit *by role* + faction identity + class baseline. Mod/new factions source from their
parent works (see `FACTION_IDENTITY.md` citations) + FACTIONS.md.

> **★ Key insight — the originals are HOMOGENEOUS, so they set identity, not unique numbers
> (maintainer 2026-07-25).** Westwood gave nearly every *basic* infantry the **same** durability
> — RA2 **GI = Conscript = 125**, TS **Light Infantry = 125**, TD **Minigunner = 50** — and
> differentiated units by **cost, tech tier, role, and special ability, NOT by HP**. So Layer 1
> tells us *who a unit is and roughly what tier/role it occupies* (via cost + `TechLevel` + the
> genuinely-varied **vehicle** heavy↔light spread — e.g. Grizzly 300 < Rhino 400 < Apocalypse
> 800), but it **cannot supply unique per-unit stats — the originals aren't unique.** Cameo's
> every-unit-unique law (`DESIGN.md`) means we take the original's *identity + tier* as the
> anchor and then assign **our own distinct HP / speed / damage / range / reload** around it via
> the formula + faction bias (`FACTION_IDENTITY.md`). **The homogeneous 125 is a baseline to
> spread FROM, not a target to copy.** This is exactly why Layer 1 is *inspiration, not
> prescription*.

---

## ★ Balance reference map — which peer anchors which Cameo faction (maintainer 2026-07-25)

The whole point of extracting the mods: **each Cameo faction is balanced against chosen peers
that already field that faction (or its closest analog).** We borrow the peers' *normalized
relative ordering*, NOT their raw numbers, and map it onto Cameo's own class anchors + formula.

**→ Full synthesis plan (all sources per faction, extraction format, methodology, and the new
weapon/AA/spread laws): [`BALANCE_SYNTHESIS.md`](BALANCE_SYNTHESIS.md).**
**Cross-reference principle:** synthesize from **all** sources that contain a unit, not just the
"primary" mod (CA's Apocalypse tank informs RA2 too; pool every appearance).

| Cameo faction(s) | Layer-1 source | **Peer references (synthesize all)** | Why |
|---|---|---|---|
| **RA2 Allies / Soviets / Yuri** | RA2 + YR | **Mental Omega + Romanov's Vengeance + CnC Reloaded** | MO best-balanced; RV = RA2-in-OpenRA; CnCR = RA2+TS |
| **TS GDI / Nod / Forgotten / CABAL** | TS + FS | **Shattered Paradise + CnC Reloaded** | SP has GDI/Nod/CABAL/Mutant; CnCR adds TS depth |
| **TD GDI / Nod** | Tiberian Dawn | **Combined Arms + DTA** | both crossover the TD factions |
| **RA1 Allies / Soviets / Japan** | RA1 (Japan ← RA3 Empire + WW2 + **Touhou**) | **Combined Arms + DTA** | CA/DTA field the RA1 rosters |
| **Scrin** (structures foundation; roster future) | — | **Shattered Paradise + Combined Arms** (synthesis) | two independent Scrin → richer Cameo Scrin, OUR assets |
| **Steel Consortium** | — | **MO Foehn Revolt** | inspired, not identical; Foehn = tankiest infantry → durable lean ✓ |
| **Latin Syndicate** | — | **MO Latin Confederation** (Soviet subfaction) | "basically the same" — black-market Soviet surplus, explosives |
| **Asian Alliance** | Generals China | **Generals China + MO China (Soviet subfaction) + CA** | mass horde |
| **Naxis / Schwarzer Mond / FutureTech** | — | mixed inspirations (Iron Sky / Earth-2150 LC / robotic) per faction | TBD each |

**Two hard rules when borrowing:**
1. **Normalize first.** Map the peer's ratios (÷ its own basic rifleman) onto Cameo's scale
   (Cameo rifle anchor = 20000). *Never paste a peer's HP* — MO rifle 135, CA 5000, SP 15000 all
   differ. Copy the **ordering**, not the value.
2. **Uniqueness spans all ~30 Cameo factions,** not just one mod's 3–4. Each peer gives a *starting
   ordering*; our converter then spreads units apart so no two units in the WHOLE crossover collide
   (a much harder constraint than any single mod solves).

**Asset independence (maintainer law):** we port *identity + balance inspiration only, never
assets.* Any borrowed unit (esp. Scrin) gets fresh Cameo assets + at least one unique twist.

---

## StarCraft: Brood War (complete — [unitstatistics.com](https://unitstatistics.com/starcraft/), [Liquipedia](https://liquipedia.net/starcraft/Unit_Statistics))

Effective HP = HP + Shield. Cost = minerals/gas. Supply in parens.

### Terran — frail infantry, tanky vehicles
| Unit | HP | eff-HP | GrndDmg | AirDmg | Rng | Cost m/g | Sup |
|---|--:|--:|--:|--:|--:|--:|--:|
| Marine | 40 | 40 | 6 | 6 | 4 | 50/0 | 1 |
| Firebat | 50 | 50 | 16 | 0 | 2 | 50/25 | 1 |
| Ghost | 45 | 45 | 10 | 10 | 7 | 25/75 | 1 |
| Medic | 60 | 60 | 0 | 0 | — | 50/25 | 1 |
| Vulture | 80 | 80 | 20 | 0 | 5 | 75/0 | 2 |
| Goliath | 125 | 125 | 12 | 20 | 5 | 100/50 | 2 |
| Siege Tank | 150 | 150 | 30/70 | 0 | 7/12 | 150/100 | 2 |
| Wraith | 120 | 120 | 8 | 20 | 5 | 150/100 | 2 |
| Battlecruiser | 500 | 500 | 25 | 25 | 6 | 400/300 | 6 |

### Protoss — tanky everywhere (shields), expensive
| Unit | HP | eff-HP | GrndDmg | AirDmg | Rng | Cost m/g | Sup |
|---|--:|--:|--:|--:|--:|--:|--:|
| Zealot | 100 | 160 | 16 | 0 | 1 | 100/0 | 2 |
| Dragoon | 100 | 180 | 20 | 20 | 4 | 125/50 | 2 |
| Dark Templar | 80 | 120 | 40 | 0 | 1 | 125/100 | 2 |
| High Templar | 40 | 80 | 0 | 0 | — | 50/150 | 2 |
| Archon | 10 | 360 | 30 | 30 | 2 | 100/300 | 4 |
| Reaver | 100 | 180 | 100 | 0 | 8 | 200/100 | 4 |
| Scout | 150 | 250 | 8 | 28 | 4 | 275/125 | 3 |
| Carrier | 300 | 450 | 6×8 | 6×8 | 8 | 350/250 | 6 |

### Zerg — cheap/frail small units, monster Ultralisk
| Unit | HP | GrndDmg | AirDmg | Rng | Cost m/g | Sup |
|---|--:|--:|--:|--:|--:|--:|
| Zergling | 35 | 5 | 0 | 1 | 25/0 | 0.5 |
| Hydralisk | 80 | 10 | 10 | 4 | 75/25 | 1 |
| Lurker | 125 | 20 | 0 | 6 | 200/200 | 2 |
| Infested Terran | 60 | 500 | 0 | 1 | 100/50 | 1 |
| Defiler | 80 | 0 | 0 | — | 50/150 | 2 |
| Ultralisk | 400 | 20 | 0 | 1 | 200/200 | 4 |
| Mutalisk | 120 | 9 | 9 | 3 | 100/100 | 2 |
| Guardian | 150 | 20 | 0 | 8 | 150/200 | 2 |
| Devourer | 250 | 0 | 25 | 6 | 250/150 | 2 |
| Scourge | 25 | 0 | 110 | 1 | 12/38 | 0.5 |

**Relative read:** Protoss eff-HP (160–450) ≫ Terran (40–150) ≈ Zerg small (25–125).
Cheapest→dearest supply-cost: Zergling/Scourge (0.5) < Marine (1) < most (2) < heavies (4–6).

---

## Warcraft 2 (complete — [unitstatistics.com](https://unitstatistics.com/warcraft2/))

**Original WC2 is a MIRROR** (Human ↔ Orc identical). Cameo de-mirrors (WC3 approach,
DESIGN.md §10) — these are the shared baseline to diverge FROM (Human defensive/+range,
Orc aggressive/+HP). Damage shown as min–max.

| Human / Orc | HP | Armor | Dmg | Rng | Speed | Gold/Wood |
|---|--:|--:|:-:|--:|--:|--:|
| Peasant / Peon | 30 | 0 | 2–9 | 1 | 10 | 400/0 |
| Footman / Grunt | 60 | 2 | 6 | 1 | 10 | 600/0 |
| Elven Archer / Troll Axethrower | 40 | 2 | 3–9 | 4 | 10 | 500/50 |
| Knight / Ogre | 90 | 4 | 2–12 | 1 | **13** | 800/100 |
| Ballista / Catapult (siege) | 110 | 0 | 25–80 | 8 | **5** | 900/300 |
| Demo Squad / Sappers | 40 | 0 | 1–6 | 1 | 11 | 750/250 |
| Mage / Death Knight | 60 | 0 | 2–9 | 2/3 | 10 | 1200/0 |
| Gryphon / Dragon (air) | 100 | 0 | 8–16 | 4 | 14 | 2500/0 |
| Flying Machine / Zeppelin (air scout) | 150 | 0 | 0 | — | 17 | 500/100 |

**Relative read:** HP: Ballista/Catapult 110 > Knight/Ogre 90 > Footman/Grunt 60 =
Mage/DK 60 > Archer 40 = Demo 40 > Peasant 30. Speed: Zeppelin 17 > Dragon 14 >
Knight 13 > Sappers 11 > most 10 > siege 5. (Knights are the *fast* heavy melee; siege is slow.)

---

## Red Alert 1 + Aftermath (complete — [unitstatistics.com](https://unitstatistics.com/red-alert/))

"Strength" = HP. Speed/Range are the game's coarse relative scale. Both factions share the
Rifle Infantry and Engineer; the divergence is in vehicles, air and navy, not the rifleman.

### Infantry — narrow HP band, shared rifleman
| Unit | Faction | HP | Cost | Speed | Weapon | Range | Role |
|---|---|--:|--:|--:|---|---|---|
| Rifle Infantry | both | 50 | 100 | A4 / S5 | M16 / AK-47 | Short | basic fodder (Soviet slightly faster) |
| Grenadier | Soviet | 50 | 160 | 5 | Grenades | Medium | anti-structure |
| Rocket Soldier | both | 45 | 300 | 3 | RedEye SAM | Medium | AT + AA |
| Flamethrower | Soviet | 40 | 300 | 3 | Flamer | Medium | anti-inf/structure |
| Shock Trooper | Soviet | 80 | 900 | 3 | Portable Tesla | Medium | Aftermath, tanky |
| Engineer | both | 25 | 500 | 4 | — | — | capture |
| Medic | Allied | 80 | 800 | 4 | Medkit | Short | Aftermath, heal |
| Mechanic | Allied | 60 | 950 | 4 | Wrench | Short | Aftermath, repair |
| Spy / Thief | Allied | 25 | 500 | 4 | — | — | infiltration |
| Tanya | Allied | 60→100 | 950→1200 | 4→5 | pistol + C4 | Medium | hero (Aftermath buffed) |
| Attack Dog | Soviet | low* | ~200 | 3 | Dogjaw | Short | anti-inf scout (*site value looks corrupt) |

### Vehicles — Allied light/fast/cheap, Soviet heavy/slow/strong
| Unit | Faction | HP | Cost | Speed | Armor | Weapon | Range |
|---|---|--:|--:|--:|---|---|---|
| Ranger | Allied | 150 | 600 | 10 | Light | MG | Medium |
| Light Tank | Allied | 300 | 700 | 9 | Medium | 75mm | Medium |
| Medium Tank | Allied | 400 | 800 | 8 | Heavy | 90mm | Medium |
| Heavy Tank | Soviet | 400 | 950 | 7 | Heavy | 105mm (dual) | Medium |
| **Mammoth Tank** | Soviet | **600** | 1700 | **4** | Heavy | 120mm + AA missiles | Medium |
| APC | Allied | 200 | 800 | 10 | Heavy | MG | Short |
| Artillery | Allied | **75** | 600 | 6 | Light | 155mm | Long |
| V2 Rocket | Soviet | 150 | 700 | 7 | Light | ballistic | Long |
| Tesla Tank | Soviet | 110 | 1500 | 8 | Heavy | Tesla | Medium |
| Chrono Tank | Allied | 350 | 2400 | 5 | Light | AP Tusk | Medium |
| M.A.D. Tank | Soviet | 300 | 2300 | 3 | Heavy | Timequake | V.Long |
| Demo Truck | both | 110 | 2400 | 8 | Light | demo charge | — |

### Air (Soviet-dominant) & Navy (Allied-dominant)
| Unit | Faction | HP | Cost | Speed | Weapon |
|---|---|--:|--:|--:|---|
| Longbow | Allied | 225 | 1200 | 16 | Hellfire |
| Hind | Soviet | 225 | 1200 | 12 | chaingun |
| Yak | Soviet | 60 | 800 | 16 | chaingun |
| MiG | Soviet | 50 | 1200 | 20 | Maverick |
| Gunboat | Allied | 200 | 500 | 9 | cannon + depth charge |
| Destroyer | Allied | 400 | 1000 | 6 | homing missile + depth charge |
| **Cruiser** | Allied | **700** | 2000 | 4 | 8-inch cannon (V.Long) |
| Submarine | Soviet | 120 | 950 | 6 | torpedo |
| Missile Sub | Soviet | 150 | 1650 | 5 | NtS missile (V.Long) |

**Relative read / per-type identity:**
- **Infantry are NOT the differentiator in RA1** — both sides share the 50-HP rifleman and
  25-HP engineer. Soviets get the *offensive* variety (Grenadier, Flamethrower, Shock Trooper)
  and marginally faster/cheaper fodder; Allies get *utility* (Medic, Spy, Thief, Mechanic).
  The tanky-slow-Allied-infantry lean is an **RA2-era development, not present in RA1.**
- **Vehicles ARE the differentiator:** Allied = lighter/faster/cheaper (Light 300/spd9,
  Ranger scout spd10); Soviet = heavier/slower/stronger and monopolizes the super-heavy
  (**Mammoth 600 HP / spd 4**). This is the same tank axis RA2 keeps.
- **Navy = Allied** (Cruiser 700, Destroyer, Gunboat); **Air variety = Soviet** (Hind/Yak/MiG
  vs the lone Longbow).
- **Poor-balance caveat (maintainer-cited):** RA1 MP devolved to Medium/Heavy **tank spam** —
  Artillery (75 HP glass cannon), infantry and navy were underused. Identity, NOT prescription.
- **Japan RA1 (custom — no RA1 twin):** identity is imported from **Red Alert 3's Empire of
  the Rising Sun** — "what the RA3 Empire would be if it existed in the RA1 era." Source its
  lore + unit identity (Imperial Warrior, Tankbuster, Rocket Angel, transforming mecha,
  balloon-bomb / naval-air focus, honor-driven fast-aggressive doctrine) from **RA3 Empire**,
  not from RA1. → Tier B extrapolation, seeded from RA3 Empire relative roles (see RA3 section).
- **Expansions:** all **Aftermath** combat units are in the table above (Shock Trooper 80,
  Chrono 350 / Tesla / M.A.D. 300 Tank, Demo Truck 110, Mechanic 60, Medic 80). **Not yet
  listed** — **Phase Transport** (Aftermath cloaked APC, transport) and the secret **Giant
  Ants** (Warrior / Fire / Scout Ant + Ant Queen, neutral creatures from *Counterstrike*);
  unitstatistics omits them, so exact HP awaits a `rules.ini`/local extraction. *Counterstrike*
  added no new buildable combat units.

---

## Tiberian Dawn (complete raw — Nyerguds' `RULES.INI` from the C&C95 binary: [gist](https://gist.github.com/Mailaender/41415be1769a1625f16b), [rules ref](http://nyerguds.arsaneus-design.com/cnc95upd/inirules/))

Ground-truth `Strength=` HP. TD speed is its own scale (vehicle ÷4 vs RA). Owner: GoodGuy=GDI,
BadGuy=Nod. (Building HP is doubled in-game; unit HP is as listed.)

### Infantry
| Unit | HP | Cost | Spd | Weapon | Owner |
|---|--:|--:|--:|---|---|
| Minigunner (E1) | 50 | 100 | 8 | M16 | both |
| Grenadier (E2) | 50 | 160 | 10 | grenade | GDI |
| Rocket Soldier (E3) | 25 | 300 | 6 | rocket (AT+AA) | both |
| Flamethrower (E4) | 70 | 200 | 10 | flame | Nod |
| Chem Warrior (E5) | 70 | 300 | 8 | chem | Nod |
| Engineer (E6) | 25 | 500 | 8 | — | both |
| Commando (RMBO) | 100 | 1000 | 10 | sniper + C4 | both |

### Vehicles
| Unit | HP | Cost | Spd | Armor | Weapon | Owner |
|---|--:|--:|--:|---|---|---|
| Medium Tank | 400 | 800 | 18 | heavy | 105mm | GDI |
| **Mammoth Tank** | **600** | 1500 | 12 | heavy | 120mm + AA | GDI |
| Light Tank | 300 | 600 | 18 | heavy | 75mm | Nod |
| Flame Tank | 300 | 800 | 18 | heavy | flame | Nod |
| Stealth Tank | 110 | 900 | **30** | light | rocket | Nod |
| Recon Bike | 160 | 500 | **40** | wood | rocket | Nod |
| Buggy | 140 | 300 | 30 | light | MG | Nod |
| Humvee | 150 | 400 | 30 | light | MG | GDI |
| APC | 200 | 700 | 35 | heavy | MG | both |
| Artillery | **75** | 450 | 12 | light | 155mm | Nod |
| SSM Launcher | 100 | 800 | 18 | light | 227mm | both |
| Rocket Launcher (MLRS) | 120 | 750 | 18 | light | rockets | Nod |

### Air & ships
| Unit | HP | Cost | Spd | Armor | Owner |
|---|--:|--:|--:|---|---|
| Orca | 125 | 1200 | 40 | heavy | GDI |
| Apache | 125 | 1200 | 40 | heavy | Nod |
| Chinook | 90 | 1500 | 30 | light | both |
| Gunboat | 700 | 300 | 8 | heavy | both |

**Relative read / per-type identity:**
- **Infantry near-shared** — both field the Minigunner (50). Nod's Flamethrower/Chem specialists
  are actually **tankier (70 HP)** than the rifleman; Rocket Soldier is the fragile AT/AA (25);
  Commando 100. Again **infantry is not the differentiator; vehicles are.**
- **GDI = heavy armor:** Medium (400) + **Mammoth (600, GDI-only)**, all heavy.
- **Nod = fast / light / stealth / flame / artillery:** Light & Flame (300), **Stealth Tank
  (110, spd 30)**, **Recon Bike (spd 40, fastest)**, Buggy, glass-cannon **Artillery (75)**.
- Air near-mirrored (Orca ↔ Apache, both 125); Gunboat (700) the lone heavy naval.
- **Poor-balance caveat:** Nod Stealth Tank + Artillery and GDI Mammoth dominated MP.
- **Expansions:** *Covert Operations* added missions, **no new buildable units** — the Nyerguds
  INI already covers every hidden/mission unit above (SSM, A10, C17, Gunboat). Easter-egg
  creatures (dinosaurs, Visceroid) are excluded as non-faction.

---

## Tiberian Sun + Firestorm (COMPLETE RAW — local `Rules.ini`)

Ground-truth `Strength=` / `Cost=` / `Speed=` / `TechLevel=` from the maintainer's TS+Firestorm
`Rules.ini` (same format as RA2). Covers **GDI, Nod, the Forgotten (mutants), and CABAL /
Firestorm**. (TS speed is its own scale.)

### Infantry
| Unit | Faction | HP | Cost | Spd | T |
|---|---|--:|--:|--:|:-:|
| Light Infantry | both | 125 | 50 | 5 | 1 |
| Disc Thrower | GDI | 150 | 150 | 4 | 2 |
| Rocket Infantry | Nod | 100 | 150 | 4 | 2 |
| Medic | GDI | 125 | 300 | 4 | 4 |
| Engineer | both | 100 | 500 | 4 | 2 |
| Jumpjet Infantry | GDI | 120 | 400 | 8 | 6 |
| Chameleon Spy | both | 100 | 1000 | 6 | 1 |
| Chem Spray Infantry | Nod | 130 | 400 | 3 | 5 |
| **Cyborg** | Nod | **400** | 350 | 4 | 4 |
| Umagon | Forgotten | 150 | 600 | 5 | 8 |
| Ghost Stalker | Forgotten | 200 | 1200 | 4 | 10 |
| Cyborg Commando | Nod | 400 | 2500 | 4 | 10 |
| Tiberian Fiend | Forgotten | 250 | 100 | 8 | — |

### Vehicles
| Unit | Faction | HP | Cost | Spd | T |
|---|---|--:|--:|--:|:-:|
| Wolverine | GDI | 175 | 400 | 7 | 2 |
| Titan | GDI | 400 | 650 | 4 | 3 |
| Hover MLRS | GDI | 230 | 700 | 7 | 7 |
| Juggernaut | GDI | 350 | 1000 | 5 | 6 |
| Disruptor | GDI | 500 | 1400 | 5 | 9 |
| **Mammoth Mk. II** | GDI | **800** | 4000 | 3 | 10 |
| Amphibious APC | GDI | 200 | 700 | 8 | 6 |
| Attack Buggy | Nod | 220 | 400 | 10 | 2 |
| Attack Cycle | Nod | 150 | 500 | 12 | 5 |
| Tick Tank | Nod | 350 | 600 | 6 | 3 |
| Flame Tank | Nod | 300 | 550 | 6 | 1 |
| Stealth Tank | Nod | 200 | 800 | 6 | 8 |
| Devil's Tongue (subterr. flame) | Nod | 300 | 850 | 5 | 7 |
| Artillery | Nod | 300 | 1000 | 5 | 6 |
| Subterranean APC | Nod | 175 | 800 | 5 | 6 |
| Mobile Stealth Generator | Nod | 200 | 1300 | 6 | 9 |
| Cyborg Reaper | Nod/CABAL | 400 | 1200 | 5 | 6 |
| Weed Eater | both | 600 | 1400 | 5 | 10 |
| Mobile EM-Pulse | GDI | 800 | 750 | 7 | 6 |
| **Core Defender** (Firestorm epic) | CABAL | **2000** | 10000 | 5 | 10 |
| Mobile War Factory | both | 800 | 1800 | 3 | 10 |

### Firestorm-added ground + air
| Unit | Faction | HP | Cost | Spd | T |
|---|---|--:|--:|--:|:-:|
| GDI Medium Strike Tank | GDI | 250 | 255 | 5 | 5 |
| Nod Assault Tank | Nod | 350 | 300 | 4 | 6 |
| GDI MLRS | GDI | 300 | 600 | 3 | 5 |
| Nod Heavy Artillery | Nod | 450 | 1000 | 4 | 3 |
| Orca Fighter | GDI | 200 | 1000 | 20 | 5 |
| Orca Bomber | GDI | 260 | 1600 | 12 | 8 |
| Harpy | Nod | 225 | 800 | 14 | 5 |
| Banshee | Nod | 280 | 1200 | 18 | 9 |
| Dropship | GDI | 900 | 3000 | 20 | 8 |

**Per-type identity (ground-truth):**
- **GDI = heavy walkers:** Titan (400), Disruptor (500), Juggernaut (350), **Mammoth Mk II
  (800, epic)** — all slow/heavy — plus air (Orca).
- **Nod = fast / light / stealth / cyborg:** Attack Buggy (220, spd10), **Attack Cycle (150,
  spd12)**, Stealth Tank (200), Devil's Tongue (subterranean), Flame/Tick Tank; **plus tanky
  Cyborgs (400)**.
- **Infantry twist:** both share Light Infantry (125), but **Nod's Cyborg (400) is the tankiest
  infantry-class unit** — TS is the one era where *Nod* fields the beefier infantry (cyborgs)
  while GDI stays lighter. Forgotten mutants are sturdy scavengers (Umagon 150, Ghost Stalker
  200, Tiberian Fiend 250).
- **CABAL / Firestorm:** **Core Defender (2000 HP / 10000cr)** = the epic anchor; Cyborg Reaper
  (400) + Mobile War Factory (800) round out the cyborg-heavy roster.
- TechLevel again gives the tier (Light Inf T1 … Titan T3 … Mammoth Mk II / Cyborg Commando /
  Core Defender T10).

---

## Red Alert 2 + Yuri's Revenge (COMPLETE RAW — local `YRinis/rulesmd.ini` + `RA2inis/rules.ini`)

Ground-truth `Strength=` HP + `Cost=` + `Speed=` + `TechLevel=` (tier 1–11; −1 = non-buildable),
parsed from the maintainer's local INIs. **Key correction: GI = Conscript = 125 HP in BOTH RA2
and YR** — the old "GI 100" stub was wrong. Vanilla RA2 matches YR on core units; the notable
YR change is **Tanya 125→200 HP**.

### Infantry (HP band 75–200; T = tech tier)
| Unit | Faction | HP | Cost | Spd | T |
|---|---|--:|--:|--:|:-:|
| Conscript | Soviet | 125 | 100 | 4 | 1 |
| GI | Allied | 125 | 200 | 4 | 1 |
| Initiate | Yuri | 100 | 200 | 4 | 1 |
| Guardian GI | Allied | 100 | 400 | 3 | 2 |
| Flak Trooper | Soviet | 100 | 300 | 4 | 1 |
| Attack Dog | both | 100 | 200 | 8 | 2 |
| Terrorist | Soviet | 75 | 200 | 6 | 5 |
| Engineer | both | 75 | 500 | 4 | 1 |
| Shock/Tesla Trooper | Soviet | 130 | 500 | 4 | 5 |
| Crazy Ivan | Soviet | 125 | 600 | 4 | 5 |
| Desolator | Soviet | 150 | 600 | 4 | 8 |
| Sniper | Allied | 125 | 600 | 4 | 1 |
| Rocketeer | Allied | 125 | 600 | 9 | 3 |
| Spy | Allied | 100 | 1000 | 4 | 5 |
| Navy SEAL | Allied | 125 | 1000 | 5 | 9 |
| Chrono Legionnaire | Allied | 125 | 1500 | 5 | 10 |
| Virus | Yuri | 100 | 700 | 4 | 1 |
| Yuri Clone | Yuri | 100 | 800 | 4 | 10 |
| Brute | Yuri | 200 | 500 | 6 | 5 |
| Tanya | Allied | 200 | 1500 | 6 | 9 |
| Boris | Soviet | 200 | 1500 | 5 | 9 |
| Yuri Prime | Yuri | 150 | 1500 | 6 | 10 |

### Vehicles (tanks confirm the per-type law cleanly)
| Unit | Faction | HP | Cost | Spd | T |
|---|---|--:|--:|--:|:-:|
| Grizzly Tank | Allied | 300 | 700 | 7 | 2 |
| Rhino Tank | Soviet | 400 | 900 | 6 | 2 |
| Lasher Tank | Yuri | 300 | 700 | 7 | 2 |
| Apocalypse | Soviet | 800 | 1750 | 4 | 7 |
| Tesla Tank | Soviet | 300 | 1200 | 6 | 10 |
| Mirage Tank | Allied | 200 | 1000 | 7 | 9 |
| Prism Tank | Allied | 150 | 1200 | 4 | 8 |
| Tank Destroyer | Allied | 400 | 900 | 5 | 2 |
| Battle Fortress | Allied | 600 | 2000 | 4 | 10 |
| IFV | Allied | 200 | 600 | 10 | 3 |
| Robot Tank | Allied | 180 | 600 | 10 | 2 |
| Gattling Tank | Yuri | 210 | 600 | 6 | 4 |
| Magnetron | Yuri | 150 | 1000 | 5 | 2 |
| Chaos Drone | Yuri | 200 | 800 | 8 | 4 |
| Master Mind | Yuri | 500 | 1750 | 4 | 2 |
| Flak Track | Soviet | 180 | 500 | 8 | 3 |
| Terror Drone | Soviet | 100 | 500 | 10 | 4 |
| V3 Launcher | Soviet | 150 | 800 | 4 | 3 |
| Siege Chopper | Soviet | 300 | 1400 | 12 | 7 |
| War Miner | Soviet | 1000 | 1400 | 4 | 1 |
| Slave Miner | Yuri | 2000 | 1500 | 3 | 1 |
| Kirov Airship | Soviet | 2000 | 2000 | 5 | 10 |
| Floating Disk | Yuri | 600 | 1750 | 15 | 2 |
| Boomer Sub | Yuri | 1200 | 2000 | 5 | 2 |

### Air & naval
| Unit | Faction | HP | Cost | Spd | T |
|---|---|--:|--:|--:|:-:|
| Harrier (Intruder) | Allied | 150 | 1200 | 14 | 3 |
| Black Eagle | Allied | 200 | 1200 | 14 | 3 |
| Destroyer | Allied | 600 | 1000 | 6 | 4 |
| Aegis Cruiser | Allied | 800 | 1200 | 4 | 7 |
| Aircraft Carrier | Allied | 800 | 2000 | 4 | 7 |
| Dolphin | Allied | 200 | 500 | 8 | 5 |
| Typhoon Sub | Soviet | 600 | 1000 | 4 | 2 |
| Dreadnought | Soviet | 800 | 2000 | 4 | 6 |
| Sea Scorpion | Soviet | 400 | 600 | 8 | 6 |
| Giant Squid | Soviet | 200 | 1000 | 8 | 9 |

**Per-type identity (ground-truth corrected):**
- **Infantry HP band 75–200; GI = Conscript = 125 (IDENTICAL).** Tankiest infantry are the
  elites/heroes — **Tanya / Boris / Brute = 200**, then Desolator / Yuri Prime 150, Shock
  Trooper 130. Frailest: Terrorist / Engineer 75, then the 100-club (Guardian GI, Flak, Yuri
  Clone, Virus, Initiate, Spy). **So "weak Soviet / tanky Allied infantry" is DOCTRINE, not raw
  HP** — Conscript (100cr, weak gun, no deploy/utility) is disposable fodder; the Allied GI
  (200cr) deploys to +range/+armor and Allies field the deeper elite/utility line. Encode the
  doctrine, **never a naive HP inversion** (GI and Conscript literally share 125).
- **Tanks confirm the per-type law cleanly:** Grizzly **300**/spd7 (Allied) < Rhino **400**/spd6
  (Soviet) < **Apocalypse 800/spd4** (Soviet heaviest + slowest). Allied fast-light (IFV/Robot
  spd 10); Yuri sits mid (Lasher = Grizzly clone, 300).
- **TechLevel (1–11)** is the source-game tech tier — a ready input for tech-tier-relative
  balancing (Conscript/GI T1 … Apocalypse T7 … Chrono Legionnaire/Kirov/Yuri Prime T10).
- Extremes: Kirov & Slave Miner **2000 HP**; Boomer Sub 1200; War Miner 1000. Naval clusters at
  600–800 (Destroyer/Sub 600, Aegis/Dreadnought/Carrier 800).

---

## Red Alert 3 — Empire of the Rising Sun (source for Japan RA1) `[IDENTITY, web-verified]`

**Faction identity (Wikipedia-confirmed):** rapid expansion (builds anywhere via nano-cores),
tech-sophisticated, **transforming units** (land↔air, sea↔air), **strong navy**, honor +
advanced tech; **core units are deliberately weaker individually → played in numbers / with
support.** Fast, dynamic, mobility- and transformation-based — **NOT brute force.**

**Roster → Japan RA1 mapping** (Japan = "the RA3 Empire as if it existed in the RA1 era"):

| RA3 Empire unit | Role / signature | → Japan RA1 |
|---|---|---|
| Imperial Warrior | basic; rifle at range + **katana charge** in melee; cheap, massed | **Samurai** |
| Tankbuster | anti-armor plasma; can **burrow** (stealth, immobile) | tank-killer |
| Shinobi | ninja commando; **stealth**, katana + shuriken, anti-infantry | Ninja |
| Rocket Angel | **flying** infantry; paralysis whip, AA/AG | **Rocket Angel** (direct) |
| Yuriko Omega | **psionic hero**; telekinesis, mind-crush | psi hero |
| Tsunami Tank | main tank, **amphibious** (drives underwater) | **Tsunami** carrier |
| Mecha / Jet Tengu | **transforms** gatling-mech ↔ AA-jet | **Mecha** (transforming) |
| Striker / Chopper-VX | **transforms** AA-heli ↔ AG-walker | transforming mecha |
| Wave-Force Artillery | long-range charging **wave beam** | artillery |
| King Oni | **heavy assault mech** (giant robot); eye-beams, crush | heavy walker |
| Yari Mini-Sub | cheap sub, **suicide-ram** | **Kamikaze** / Speedboat |
| Naginata Cruiser / Shogun Battleship | anti-ship / heavy battleship (ram) | naval |
| Sea-Wing / Sky-Wing | **transforms** sub ↔ aircraft | naval-air |

**Per-type lean for Japan RA1:** infantry **individually weak (−HP), fast (+SPD), aggressive**
(need mass/support); the identity is **transforming units + naval/air dominance + psionics**,
not durability.

---

## C&C Generals + Zero Hour — China (source for Asian Alliance) `[IDENTITY, web-verified]`

**Faction identity (Wikipedia-confirmed):** **mass doctrine** — numerical superiority over tech.
**Horde bonus** (tanks AND infantry gain power when grouped) rewards massing. Foundation =
**stronger, heavier tanks + artillery** (Battlemaster, **Overlord**, Nuke/Inferno cannon);
**notably weak air force**; **hacker economy** (steal funds / capture); nuclear weapons;
propaganda/heal towers; stealth-detecting transports. Aggressive, momentum, overwhelming
massed pushes — the "traditional military powerhouse."

**→ Asian Alliance mapping:** cheap **mass infantry** (Militia/Grenadier, horde bonus),
weak-individually, **SLOW** (massing doctrine); **heavy tanks + strong artillery**; **weak air**;
nuclear/superweapon finish. **Confirms the corrected AA lean** (−SPD mass-horde, not +SPD).

---

## Dawn of the Tiberium Age (DTA) — peer crossover mod `[STAT ÷10]`

Local `INI/Rules.ini` + `INI/Enhance.ini`. **TS engine, ×10 HP** (Minigunner 500 → ÷10 = **50**
= exactly TD; Bazooka 250→25, Nod Flamethrower 700→70). A **TD + RA1 crossover** fielding all
four classic sides (GDI / Nod / Allied / Soviet) + secret dinos + Tiberian Fiends. Two modes:

- **Classic** = faithful TD/RA1 → **homogeneous** (every rifleman variant E1 / E1N / E1A / E1S =
  50 HP). Reinforces the ★ insight: even a crossover mod inherited Westwood's flat baseline.
- **Enhanced** = DTA's OWN rebalance — **the peer reference for de-homogenizing.** It spreads the
  flat values along ROLE (HP ÷10 shown; 130 total stat changes):

| Unit | Classic | Enhanced | DTA's intent |
|---|--:|--:|---|
| Grenadier | 50 | 40 | frail attacker |
| Bazooka / Rocket Soldier | 25 | 50 | dedicated AT made sturdier |
| Chem Warrior | 70 | **200** | elite specialist |
| Volkov (cyborg hero) | 80 | **400** | hero tankiness |
| Shock Trooper | 80 | 110 | tanky Tesla infantry |
| Medic | 80 | 125 | support survivability |
| Attack Dog | 12 | 25 | — |
| Commando / Tanya | 80 / 100 | 70 / 70 | glass-cannon heroes (HP traded for damage) |
| GDI / Soviet Mammoth | 600 | 735 / 760 | heavy anchors |
| Flame Tank | 300 | 410 | — |
| Chrono Tank | 350 | 500 | — |
| Longbow / MIG | 125 / 50 | 260 / 105 | air survivability |
| Harvesters | 600 | 1000 | durable economy |

**Takeaway for us:** DTA's designers hit our exact problem (flat classic infantry) and solved it
by **spreading HP along role** — frail attackers low, dedicated AT / specialists / heroes high,
glass-cannon commandos trading HP for damage. A concrete precedent for our de-homogenizing pass.

---

## Combined Arms & Shattered Paradise — OpenRA peer crossovers `[STAT — same engine]`

Both are **OpenRA mods → same engine as Cameo**, BUT **each mod sets its own power level**, so
raw HP is **NOT** directly comparable (my earlier "directly comparable" was wrong — maintainer
2026-07-25). Scale anchors (basic rifleman): **CA = 5000**, **SP GDI rifle = 15000**, **Cameo
scout anchor = 20000** — i.e. **Cameo runs the highest numbers (~4× CA, ~1.33× SP)**. So
**normalize each mod to its own basic rifleman (= 1.00)** and read the *relative spread*, then map
that onto Cameo's own scale. Both are crossovers like us, and — critically — **both DE-HOMOGENIZE
infantry by role (and faction)**, exactly our plan.

### Combined Arms — GDI / Nod / Allied / Soviet / Yuri crossover (`mods/ca/rules/`)
| role | example | HP |
|---|---|--:|
| scout / dog | DOG | 1800 |
| AT / rocket infantry | E3 / N3 | 3500 |
| sniper | SNIP | 4500 |
| **basic rifle / grenadier / medic** | E1 / E2 / MEDI | **5000** |
| guardian / jumpjet | U3 / JJET | 6000–6500 |
| heavy trooper / flame / cyborg | SHOK 7500, E4 9000, ACOL 9000 | 7500–9000 |
| heroes | Tanya (E7) / Commando (RMBO) / Boris (BORI) | 11000 |
| elite specialists | Yuri 18000, Desolator 18500 | 18000+ |

→ **~10× spread** frailest→tankiest; **AT infantry deliberately frail (3500)**, heroes & elite
specialists tankiest. Vehicles echo it: Bike 11000/spd170 (fast-light), Buggy 13250, Jeep/Humvee
15000, glass Artillery 10000.

### Shattered Paradise — GDI / Nod / CABAL / Scrin / Mutant crossover (`mods/sp/rules/`)
Faction tags explicit (`Infantry.GDI/Nod/Scrin/CABAL/Mutant`); spread by role AND faction:
| faction lean | examples (HP) |
|---|---|
| **Scrin** | frail-swarm early (Chusk 3500, Shark 6400) → heavier casters (Colossi 25000) |
| **GDI** | mid-heavy (Medic 10k, rifle 15k, Grenadier/E2 20k, Eagleguard 40k) |
| **Nod** | mid (Crusader 10k, Confessor 20k, Templar/Exemplar 25k) |
| **CABAL** | **tankiest** — cyborgs 30k–50k (Gladiator 50000), drones 11k–40k |
| **Mutant** (Forgotten) | sturdy scavengers (Marauder 10k, Mutfiend 12k, Psyker 25k) |

### Normalized to each mod's basic rifleman (the only comparable view)
| role | CA (rifle=5000) | SP (GDI rifle=15000) | **Cameo anchor** (scout=20000) |
|---|--:|--:|--:|
| AT / rocket trooper | 0.70 | — | **0.50** |
| basic rifle / scout | 1.00 | 1.00 | **1.00** |
| grenadier | 1.00 | 1.33 | **0.40** |
| sniper | 0.90 | — | **0.55** |
| flame / close-combat | 1.8 | — | **2.5** |
| heavy infantry | 1.5 | — | **2.5** |
| hero / commando | 2.2 | 1.67 | **4.0** |
| elite specialist | 3.6 (Yuri) | 3.3 (CABAL Gladiator) | — |

**Takeaway (corrected):** the *direction* is shared across all three — **AT/rocket & grenadiers
frail; close-combat / heavy / commando tanky** — but the **magnitudes differ per mod.** Cameo
already runs a *wider* spread at the tanky end (close-combat 2.5×, commando **4.0×**) than CA
(flame 1.8×, hero 2.2×). So CA/SP give us the **role ORDERING and a sanity band, not target
numbers**; Cameo's own anchors (Layer 2) set the absolute scale. CABAL-cyborg-tankiest and
Scrin-swarm-frail still match identities we already hold — use them for *ordering*, then map onto
Cameo's scale.

---

## Mental Omega 3.3.6 — professionally-balanced RA2 peer `[STAT — YR scale]`

Extracted from `expandmo99.mix` (entry `0xe8df0937`, "MO 3.3.6 RULES", 2.29 MB) by **content-scan**
(the encrypted `ra2md.mix` only held vanilla YR; scratchpad `extract_all.py` dumps unencrypted-mix
entries and keeps those containing `[InfantryTypes]`). **569 units, 4 factions** — Allied, Soviet,
**Epsilon** (→ Yuri), **Foehn** (→ **Steel Consortium**). MO keeps the **vanilla-YR HP scale**
(rifle ~135, NOT inflated) → normalize to MO's rifle; Cameo ≈ **148×** MO in absolute HP.

**MO already applies BOTH Cameo laws — the strongest precedent we have:**
- **De-homogenized basic infantry:** the three riflemen differ — **G.I. 135 ≠ Conscript 125 ≠
  Initiate 150** (vanilla YR had all three at 125).
- **Every unit unique:** MO tanks are all distinct HP — Bulldog 395, Kappa 420, Cavalier 450,
  Mirage 440, Abrams 500, Rhino 480, Jaguar 435, Qilin 510, Catastrophe 620, Apocalypse 1050,
  Lasher 420, Mantis 310, Shadow 350… no two equal.

**Infantry HP band** ~40 (Scout Raven) / 75 (dogs) → rifle 125–150 → elites/heroes 200–750:
| faction | lean (HP examples) |
|---|---|
| Allied | GI 135, Guardian 170, SEAL 170, Riot 265, Suppressor 340, Siegfried 430 |
| Soviet | Conscript 125, Flak 145, Tesla 270, Shock 320, Volkov 600 (hero) |
| **Epsilon** (→ Yuri) | Initiate 150, Adept 110, Brute 365, Stalker 345, Rahn 410, Libra 300 |
| **Foehn** (→ **Steel Consortium**) | **tankiest** — Knightframe 270, Lancer 300, Railguneer 450, Deviatress 480, **Giantsbane 750** |

**Big confirmation:** **Foehn fields the tankiest infantry in MO** (Giantsbane 750 tops the roster)
— directly validating the **Steel Consortium = durable / tanky** lean we already set, now backed
by its literal source faction.

**Takeaway:** MO — one of the best-balanced C&C mods — independently enforces *both* Cameo laws
(de-homogenize by role/faction + every-unit-unique) across the RA2 roster. It's the premier
RA2-family peer for unit **ordering** (normalized to its rifle); Foehn seeds Steel Consortium,
Epsilon seeds Yuri.

---

# Source library — full scope & status

This matrix is a **reference library, not a prescription.** Cameo draws units from across
the **entire Westwood RTS catalogue** (Dune II → Emperor, and all of Command & Conquer
Tiberian Dawn → Tiberian Twilight), the **Earth 21x0 series**, the StarCraft and Warcraft
families, Outpost 2, and several **famous mods** — frequently as
**promotion units, elite variants, or planned future units**. Recording each source unit's
*original identity* (role, relative durability / speed / firepower, signature ability) lets
us place a borrowed unit correctly instead of guessing, and lets us decide a faction's
*playstyle* from real precedent.

**Three hard caveats (read before using any number):**
1. **Cross-game raw numbers do not compare.** Westwood C&C (hundreds–thousands HP), SAGE
   (Generals/C&C3/RA3, different scale again), C&C4 (no economy at all), Blizzard SC
   (25–500), WC (30–150s) — only **per-game-normalized *relative role*** transfers.
2. **Later-game / campaign / co-op / mod stats are IDENTITY references, not balance
   references.** Campaign & co-op units are deliberately over/under-tuned and commander-
   modified; mod stats are the modder's taste. Mine them for *who a unit is*, never *what
   its HP should be*.
3. **Tag every source:** `[STAT]` = usable as a normalized stat/identity seed;
   `[IDENTITY]` = lore / role / ability reference only.

## Status table

| Source | Era / engine | Cameo use | Status |
|---|---|---|---|
| **Tiberian Dawn** + Covert Ops (1995) | Westwood C&C1 | GDI TD, Nod TD | ✅ **done — raw** (Nyerguds INI) `[STAT]` |
| **Red Alert 1** + Aftermath (1996) | Westwood | RA1 Allies/Soviets | ✅ **done** `[STAT]` |
| **Tiberian Sun** + Firestorm (1999) | Westwood TS | GDI/Nod TS, Forgotten, CABAL | ✅ **done — raw** (local Rules.ini) `[STAT]` |
| **Red Alert 2** + Yuri (2000–01) | Westwood RA2 | RA2 Allies/Soviets/Yuri **+ all 7 RA2-mod factions** | ✅ **done — raw** (local rulesmd.ini) `[STAT]` |
| **C&C Generals** + Zero Hour (2003) | SAGE | **Asian Alliance ← China**, promotion/future | ✅ **identity done** (web) `[IDENTITY]` |
| **C&C3 Tiberium Wars** + Kane's Wrath (2007) | SAGE/RNA | advanced GDI/Nod + Scrin promotion/future | ⏳ pending `[IDENTITY]` |
| **Red Alert 3** + Uprising (2008) | SAGE | **Japan RA1 ← Empire of the Rising Sun**, promotion/future | ✅ **identity done** (web) `[STAT/IDENTITY]` |
| **C&C4 Tiberian Twilight** (2010) | SAGE (no economy) | late-Tiberium promotion/future flavor only | ⏳ pending `[IDENTITY only]` |
| **Dune II** (1992) | Westwood (genre origin) | Dune-house root identity (Atreides/Harkonnen/Ordos) | ⏳ pending `[IDENTITY]` |
| **Dune 2000** (1998) | Westwood | Ordos (Atreides/Harkonnen parked) | ⏳ pending `[STAT]` |
| **Emperor: Battle for Dune** (2001) | Westwood 3D | Dune houses + **House Ix → Ixian root** + sub-houses | ⏳ pending `[IDENTITY/STAT]` |
| **Outpost 2** (1997) | Sierra/Dynamix | Eden, Plymouth | ⏳ pending `[STAT]` |
| **Earth 2140** (1997) | Reality Pump | sci-fi archetypes: UCS robots vs ED humans | ⏳ pending `[IDENTITY]` |
| **Earth 2150** (2000) | Reality Pump 3D | UCS / ED / **LC (lunar anti-grav → Schwarzer Mond parallel)** | ⏳ pending `[IDENTITY]` |
| **Earth 2160** (2005) | Reality Pump | + Alien/Morphid organic faction; unit designer | ⏳ pending `[IDENTITY]` |
| **StarCraft** + Brood War (1998) | Blizzard | Terran/Protoss/Zerg | ✅ **done** `[STAT]` |
| **StarCraft II** WoL/HotS/LotV + Co-op | Blizzard | SC identity depth; campaign/co-op units as promotion/future | ⏳ pending `[IDENTITY]` |
| **StarCraft Cosmonarchy** (mod) | fan mod | peer-design reference for expanded SC rosters | ⏳ pending `[IDENTITY]` |
| **Warcraft II**: Tides of Darkness (1995) | Blizzard | WC2 Humans/Orcs | ✅ **done** `[STAT]` |
| **Warcraft III**: RoC + TFT (2002) | Blizzard | **WC2 de-mirror / WC3-style balance target** | ⏳ pending `[IDENTITY]` |
| — *famous mods — do LAST* — | | | |
| **Mental Omega 3.3.6** (RA2/YR mod) | Westwood RA2 | **Foehn → Steel Consortium**, Epsilon → Yuri; Allied/Soviet depth | ✅ **done** — content-scanned from `expandmo99.mix`; de-homogenized + every-unit-unique `[STAT]` |
| **Dawn of the Tiberium Age** | **TS engine** (HP & vs-armor ×10) | TD+RA1 crossover peer | ✅ **done** — Classic + Enhanced `[STAT ÷10]` |
| **Combined Arms** (OpenRA) | **Cameo's exact engine** | direct crossover peer — *own power level, normalize* | ✅ **done** — de-homogenizes by role `[STAT peer]` |
| **Shattered Paradise** (OpenRA) | **Cameo's exact engine** | TS-era peer (GDI/Nod/CABAL/Scrin/Mutant) | ✅ **done** — by role + faction `[STAT peer]` |
| **CnC Reloaded 2.7.0** | Ares (RA2 **+ TS** combined) | RA2 **and** TS synthesis | ✅ **done** — 325 units in `ORIGINAL_UNITS_RAW.md` (§CnC Reloaded), from `Downloads/CnCReloaded-2.7.0/Tools/Map Editor/rulesmd.ini` `[STAT]` |
| **Romanov's Vengeance** | OpenRA (RA2 remake) | RA2 synthesis | ✅ **done** — 208 units in `ORIGINAL_UNITS_RAW.md` (§Romanov's Veng.), from `Downloads/Romanovs-Vengeance-master/mods/rv/rules`+`weapons` `[STAT]`. Remember: RV is a faithful remake → weight {vanilla+RV} as ~one vote |
| **Red Resurrection** (YR mod, OmegaBolt) | Ares/YR | RA2 weapon + unit synthesis | ✅ **done — warheads** `[STAT]` — **480 profiles**. 333ggg was right that it is unprotected, but the rules are NOT loose: they sit inside `rr_update_2213/expandmd99.mix` (the MO pattern). `extract_mix_ini.py` → `~/Downloads/_extracted_rr/expandmd99_8218f9f4.ini` (1.47 MB, 499 `Verses=`). Units for Document 1 still pending |
| **RA2 Reborn** (Community 1.0.31, Phobos) | Phobos/YR | RA2 weapon + unit synthesis | ✅ **done — warheads** `[STAT]` — **176 profiles**, from `Resources/INI.mix` → `~/Downloads/_extracted_reborn/INI_c5d7f6ce.ini` (864 KB, 359 `Verses=`). This resolves the earlier "which Reborn?" ambiguity: the maintainer supplied the RA2 Phobos one, not a W3D-engine mod. Units for Document 1 still pending |

## Identity / playstyle stubs (safe from lore + design knowledge; exact stats pending web)

_These are the decision-useful reads I can commit now without fabricating numbers. Fill the
numeric tables per-game as the web pull proceeds._

- **Tiberian Dawn** — GDI = heavy / slow / expensive armor (Medium Tank, **Mammoth**),
  air (Orca), Ion Cannon; few but tough. Nod = light / fast / cheap, **stealth** (Stealth
  Tank), **flame**, artillery, chem-warrior, buggy/bike speed; glass swarm + Obelisk.
  Infantry largely shared (Minigunner, Grenadier, Bazooka/rocket, Engineer, Commando); Nod
  adds Flamethrower / Chem. Per-type: **GDI armor-heavy, Nod speed/stealth.** Poor-balance:
  Nod Stealth Tank + Artillery and GDI Mammoth dominated.
- **Tiberian Sun** — GDI = **walkers** (Titan, Wolverine, Juggernaut, hero Mammoth Mk II),
  Disruptor sonic, orbital, heavy/positional. Nod = **stealth + subterranean + cyborgs**,
  Banshee, Tick Tank, Artillery, hit-and-run. Forgotten = mutant scavengers (already a
  Cameo faction). CABAL = cyborg/AI (Firestorm). Per-type: **GDI heavy walkers, Nod
  stealth/subterranean/cyborg.**
- **C&C Generals + Zero Hour** — **USA** = hi-tech, air, lasers, drones, precise/expensive;
  **China** = **mass / hordes / tanks / nuke / propaganda**, cheap, slow, Overlord tank
  (THE root of **Asian Alliance**: slow mass-horde identity — matches the corrected AA
  lean); **GLA** = cheap, stealth, tunnels, scavenge, toxin, **no air**, guerrilla. SAGE HP
  scale ≠ Westwood — identity only.
- **C&C3 Tiberium Wars + Kane's Wrath** — GDI (heavy mech: Predator/Mammoth/Juggernaut,
  orbital, air), Nod (stealth, flame, lasers, **Avatar**, fast), **Scrin** (alien air-
  superiority, tripods, Motherships, phase). KW subfactions add flavor (Steel Talons = mech
  GDI; Black Hand = Nod flame; Marked of Kane = cyborg; Reaper/Traveler Scrin). Use for
  advanced GDI/Nod promotion units and any Scrin-flavored future content.
- **Red Alert 3 + Uprising** — Allied (hi-tech, cryo, chrono, precise, versatile), Soviet
  (heavy armor, Tesla, Apocalypse, Kirov — brute mass), **Empire of the Rising Sun**
  (**transforming units**, honor, nanotech, fast-aggressive, wave-force naval/air: Tsunami
  Tank, Tengu/Jet, **Rocket Angel**, King Oni, Mecha/Tengu transforms, Yari sub, balloon
  bombs). **Empire = the identity source for Japan RA1.** RA3 stats reasonably documented →
  usable as `[STAT/IDENTITY]` when pulled.
- **C&C4 Tiberian Twilight** — no base/economy: **Crawler** deploy, unit **classes**
  (Offense / Defense / Support) for both GDI & Nod, tiered by persistent progression, point
  cap. Stats **do not map** to Cameo's economy → **identity only**; useful for late-
  Tiberium-era GDI/Nod unit concepts as promotion/future flavor.
- **Dune 2000** — Westwood houses: **Atreides** (balanced/honorable — infantry + air +
  sonic tank), **Harkonnen** (brute: Devastator, heavy, cheap troopers, no finesse),
  **Ordos** (stealth/tech/mercenary: Deviator, Raider speed, no heavy infantry). Ordos is
  the active Cameo faction; its lean = **mobility / stealth / tech**.
- **Outpost 2** — Eden (aggressive research: Laser, Rail Gun, Acid Cloud) vs Plymouth
  (survival/attrition: StickyFoam, ESG, Microwave, Spider). Modular Lynx/Panther/Tiger
  chassis with swappable turrets — the chassis = the "class," the turret = the weapon.
- **StarCraft II (all branches)** — MP refines BW identities (Terran frail-bio/tanky-mech +
  siege; Protoss shields/elite/expensive; Zerg swarm cheap→monster). **Campaign** adds a
  huge bespoke roster (Terran: Marauder, Reaper, Diamondback, Spectre, Thor; Protoss:
  Immortal, Colossus, Stalker, Sentry, Void Ray, Tempest, Disruptor, Vanguard, Ascendant;
  Zerg: Roach, Baneling, Swarm Host, Viper, Aberration, Brood Lord, Impaler) — many over-
  tuned. **Co-op** adds hero/commander units (Tychus, Nova, Zeratul, Fenix, Alarak, Dehaka,
  Stukov, Mengsk, Stetmann…) with bespoke mechanics. All `[IDENTITY]` — role/ability
  references for promotion & future units, never balance targets.
- **StarCraft Cosmonarchy** (mod) — large fan overhaul expanding SC rosters (UED and extra
  Terran/Protoss/Zerg units + factions). Value = **peer-design reference**: how another
  modder scaled an *expanded* SC roster. `[IDENTITY]`.
- **Warcraft III (RoC + TFT)** — four factions on an **armor-type × attack-type triangle**
  with **hero units + upkeep**: Human Alliance (versatile — footman/rifleman/knight/priest/
  sorceress/gryphon/mortar), Orc Horde (tanky-aggressive — grunt/raider/tauren/kodo/shaman/
  wyvern), Night Elf (mobile-ranged/stealth — archer/huntress/dryad/druid/glaive/chimaera),
  Undead Scourge (attrition/summon — ghoul/crypt fiend/abomination/gargoyle/necromancer/
  frost wyrm). **This is the balance target for Cameo's WC2**: unique per-unit stats, the
  armor/attack triangle, and hero/elite units. Use WC3 identities to de-mirror & enrich WC2
  Humans/Orcs (HP in the hundreds → normalize).

- **Dune II: The Building of a Dynasty (1992)** — the genre progenitor. Three houses share a
  roster with one signature weapon each — Atreides **Sonic Tank**, Harkonnen **Devastator**,
  Ordos **Deviator** (+ Saboteur) — plus house elites (Atreides **Fremen**, Harkonnen
  **Sardaukar**). This is the *root* of the Dune-house identities; stats are coarse/early.
- **Emperor: Battle for Dune (2001)** — Dune 2000's 3D sequel. Three main houses (Atreides
  balanced/air/sonic, Harkonnen brute/flame/Devastator/heavy, Ordos stealth/chem/speed)
  **plus five allyable sub-houses**: **House Ix** (tech — holographic **Projector**,
  **Infiltrator** — the lore root of Cameo's **Ixian** faction), **Tleilaxu** (bio —
  Contaminator/Leech), **Guild** (worm rider, NIAB teleport tank), **Fremen** (desert
  stealth warriors), **Sardaukar** (Imperial elite infantry). Emperor is where "Ixian" units
  actually exist → mine it directly for the Cameo Ixian identity.
- **Earth 2140 / 2150 / 2160 (Reality Pump)** — sci-fi faction archetypes worth borrowing:
  **UCS** = robotic / mech / laser / stealth, no infantry → parallels **FutureTech**; **ED**
  (Eurasian Dynasty) = conventional armor + nuclear, cheaper/human; **LC** (Lunar
  Corporation, from 2150) = **anti-gravity / hover / plasma / energy shields** → strong
  parallel to **Schwarzer Mond** (lunar/anti-grav); **Alien/Morphid** (2160) = organic /
  evolving. 2150/2160 use deep **vehicle customization** (chassis + weapon + equipment),
  echoing Outpost 2's and TKM's modular ethos. Identity references for our sci-fi factions.
- **Famous mods (deferred — pulled LAST, after every base game):**
  - **Mental Omega** (RA2/YR total conversion) — the definitive RA2 overhaul; four factions:
    Allied, Soviet, **Epsilon** (Yuri lineage — mind control/subversion), **Foehn Revolt**
    (anti-grav / coilgun / drone high-tech = the **Steel Consortium** root, already cited in
    `FACTION_IDENTITY.md`). **Maintainer has the local folder** (preferred — exact
    `rulesmd.ini` Strength/Damage/Verses); web wiki is only a fallback.
  - **Dawn of the Tiberium Age (DTA)** — TD + RA1-era total conversion running on the **TS
    engine** (behaves exactly like Tiberian Sun). ⚠ DTA **multiplies HP and weapon-vs-armor
    ×10** vs TS → **normalize ÷10** for any raw comparison. *Moot under relative balancing:* a
    uniform ×10 on both HP and damage preserves every durability/firepower **ratio** and TTK,
    so the relative identity is identical to TS. **Local folder.**
  - **Combined Arms** and **Shattered Paradise** — **OpenRA mods on Cameo's exact engine**, so
    the *format* is identical, BUT **each sets its own power level** (CA rifle 5000, SP 15000,
    Cameo 20000) → still **normalize each to its basic unit** before comparing. Highest-*fidelity*
    peers (same engine, same trait model), used for role **ordering** not raw numbers. **Local.**
  - → **All four have local folders** (preferred — exact, and they bypass the web rate limit
    entirely). When we reach this step, ask the maintainer for the paths.

### Data-source reality (learned 2026-07-25)

Web gives **clean raw HP only for RA1, StarCraft, Warcraft 2** (unitstatistics "Strength" is
true HP); for **TS and RA2/YR** it gives only a misleading **1–5 rating**. **The definitive
route for classic C&C is an extracted rules INI**, and those are now in hand: **TD ✅**
(Nyerguds gist), **TS + Firestorm ✅** and **RA2 + YR ✅** (maintainer's local `Rules.ini` /
`rulesmd.ini`, parsed by a small script → real `Strength` / `Cost` / `Speed` / `TechLevel`).
**Still needing a local/extracted INI: Dune (2000 / Emperor) + Outpost 2.** Web remains fully
sufficient for **identity / relative role** and the **identity-only** later games.

## Pull order (when web access resets — session limit until ~04:40 Europe/Berlin)
1. Finish **RA2/YR** raw HP (highest leverage — 10 factions ride the RA2 engine).
2. **Tiberian Dawn** → **Tiberian Sun** (`[STAT]`, Westwood scale, direct faction owners).
3. **Dune II** → **Dune 2000** → **Emperor** (Ixian root) → **Outpost 2** (`[STAT/IDENTITY]`).
4. **RA3 Empire** (`[STAT/IDENTITY]` — unlocks Japan RA1).
5. **Generals/ZH, C&C3/KW, C&C4** (`[IDENTITY]` — promotion/future sourcing).
6. **Earth 2140 / 2150 / 2160** (`[IDENTITY]` — sci-fi faction archetypes).
7. **StarCraft II** (MP → campaign → co-op) + **Cosmonarchy** (`[IDENTITY]`).
8. **Warcraft III** (`[IDENTITY]` — WC2 de-mirror target).
9. Per-game normalization → corrected per-type leans in `FACTION_IDENTITY.md` → encode bias
   into the converter → resume the Δ≤1 conversion.
10. **LAST — famous mods (all four have local folders — ask maintainer for paths):** Combined
    Arms / Shattered Paradise (OpenRA → normalize each to its basic unit); Mental Omega (`rulesmd.ini`);
    DTA (TS engine, ÷10 normalize). Local avoids the web rate limit entirely.
