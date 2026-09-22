# Faction Identity & Balance Bias

**Purpose.** This is the binding reference for *how each faction's units differ within a
class*. The per-class formula (`FORMULA_V2.md`) fixes each unit's **cost** and holds
**Δ≤1**; this document decides the *direction* of the leftover uniqueness budget so
differentiation is **lore-directed**, not arbitrary. Source-game research is cited; the
lore compendium is `../FACTIONS.md` (this doc is the balance interpretation of it).

## Core principle

Within a class, cost is pinned and price must stay Δ≤1. Because the price is fixed,
raising one stat forces another down — so each faction spends its budget on the stat
its source-game identity leans into, and pays for it in the opposite stat.

**Narrow classic-four duplicate exception (maintainer, 2026-09-15).** For a complete
TD GDI / TD Nod / RA Allies / RA Soviets combat cohort that still shares duplicate
values, apply a slight faction-themed change to **each** stat, following the already
accepted Minigunner/Rifle Infantry pattern. This direct ruling allows cost to move
inside that duplicate cohort despite the general cost pin above. Preserve the TD and
RA pair totals, shared cadence, roles and behavior; it does not authorize drifting
unrelated units or incomplete role matches.

**Primary axis (confirmed across every source game): HP ↔ Speed.**
- **Brute / Heavy / Turtle** factions → **+HP, +Damage, −Speed** (tanky, hard-hitting, slow; in the original games also more expensive / fewer units — here that becomes stat weight since cost is pinned).
- **Rush / Mobile / Stealth / Swarm** factions → **+Speed, −HP** (fast, fragile; cheaper/more numerous in-game → here they trade raw durability for reach/speed).

**Secondary axes:**
- **Tech / Power** factions → **+Damage, +Range** (elite units; Protoss/Steel-Consortium "shields" read as +HP).
- **Special mechanic** (not a stat bias — a per-unit trait, priced via the special-K multiplier): stealth, mind-control, self-heal, decoys, transforming, cyborg turn-rate, area-denial.

**⚠️ Per-TYPE, not global (maintainer 2026-07-25).** A faction's lean can INVERT between
unit types. From the source stats (`ORIGINAL_UNIT_STATS.md`): RA2 **Soviet infantry is
frail** while Soviet *tanks* are the tankiest+slowest; **Allied infantry is tanky+slow**
while Allied *tanks* are weak+fast; StarCraft **Terran infantry is frail** while its
*vehicles* are tanky. **So the bias tables below are the INFANTRY leans** — vehicle and
aircraft leans are derived separately (from the matrix) in those passes. And a unit's
balance class always follows its in-game TEMPLATE (`LineBreaker` = vehicle, etc.), never
an HP guess. (The **StarCraft / Warcraft 2 / Red Alert 1** leans below are now
Layer-1-verified against `ORIGINAL_UNIT_STATS.md`; the other factions await their pull.)

**NO mirror factions (Cameo departs from Warcraft 2 here).** In the original WC2, Humans
and Orcs are stat-mirrors. Cameo deliberately does **not** do this — mirror factions are
dull. We follow the **Warcraft 3 philosophy**: every faction, and every individual unit,
gets its own distinct stats (**no two units may share a stat value** — the uniqueness law,
see `../DESIGN.md`). So WC2 Humans and Orcs are differentiated like any other pair, and
their counterpart units (Footman vs Grunt, Knight vs Ogre, …) are re-statted apart, never
mirrored: Humans lean **defensive / versatile / support-magic**, Orcs lean **aggressive /
brute**.

## Faction bias table

Legend: **HP** / **SPD** / **DMG** / **RNG** columns are the lean (＋ high, − low, ・ neutral).
"Special" is the signature mechanic (priced separately, not a stat lean).

### Tiberium (C&C: Tiberian Dawn / Tiberian Sun)

| Faction | Playstyle | HP | SPD | DMG | RNG | Special / signature |
|---|---|:-:|:-:|:-:|:-:|---|
| GDI TD | Brute Force / Heavy Armor | ＋ | − | ＋ | ・ | Air power, strong defense; Mammoth/Orca/Commando. Expensive, few, slow. |
| Nod TD | Rush / Stealth / Guerrilla | − | ＋ | ・ | ・ | Stealth, cheap & numerous, better AA, nuke; harassment. |
| GDI TS | Turtle / Positional | ＋ | − | ＋ | ＋ | Titans (mechs), Juggernaut long-range artillery, drop pods. |
| Nod TS | Stealth / Hit & Run | − | ＋ | ・ | ・ | Tick Tanks (burrow), Mobile Stealth Generators, cyborgs, chemical. |
| Forgotten | Adaptive / Promotion | ＋ | − | ・ | ・ | **Self-heal from Tiberium**; scavenged mixed units; mutants. |
| CABAL | Tech Rush / Promotion | ＋ | − | ＋ | ・ | **Cyborg = vehicle turn-rate (speed ×5)**; AI, promotion tech. |

### Red Alert 1 (+ Cameo's Japan)

| Faction | Playstyle | HP | SPD | DMG | RNG | Special / signature |
|---|---|:-:|:-:|:-:|:-:|---|
| Allies RA1 | Tech / Mobility / Naval | − | ＋ | − | ＋ | For duplicate Cameo combat infantry, follow the accepted Rifle pattern: slightly lighter/faster with more reach. Utility identity remains in Medic/Spy/Thief/Mechanic; vehicle/naval identity is still stronger. |
| Soviets RA1 | Brute Force | ＋ | − | ＋ | − | For duplicate Cameo combat infantry, follow the accepted Rifle pattern: slightly tougher/slower with a harder, shorter-ranged shot. Offensive variety remains Grenadier/Flamethrower/Shock Trooper; vehicle/air identity is still stronger. |
| Japan RA1 | Rush / Mobility (← RA3 Empire + WW2 + Touhou) | − | ＋ | ・ | ・ | ← a **funny mix: RA3 Empire of the Rising Sun + WW2 Japan + Touhou + misc**. Core units weak → fast + massed; **transforming** mecha, naval/air, Rocket Angels, Samurai/Tsunami; **Touhou** bullet-hell / character flavour. |

### Red Alert 2 / Yuri

| Faction | Playstyle | HP | SPD | DMG | RNG | Special / signature |
|---|---|:-:|:-:|:-:|:-:|---|
| Allies RA2 | Mobility / Garrison | − | ＋ | ・ | ＋ | Hit-and-run, micro, air force, versatile tech, GI garrison. |
| Soviets RA2 | Brute Force / Tank Rush | ＋ | − | ＋ | ・ | Heavy defense, macro; tanks, flak, Desolator. |
| Yuri | Mind Control | ・ | ＋ | ＋ | ・ | **Mind control**; cheap-but-strong psychic Initiates; Brutes = melee anti-tank; Gattling ramp-up. |

**Layer-1 source note (RA1 — `ORIGINAL_UNIT_STATS.md`):** Source RA1 infantry are not a
durability differentiator — both factions share the 50-HP rifleman and 25-HP engineer, and
the Soviet rifleman is faster (speed 5 vs 4). Cameo now deliberately departs from that source
symmetry for complete duplicate combat cohorts: the maintainer's 2026-09-15 ruling follows
the already accepted Cameo Rifle pattern, giving Allies a slight mobility/reach lean and
Soviets a slight durability/damage lean. Do not infer this narrow choice from source RA1 or
apply the stronger Soviet vehicle bias wholesale to other infantry.

### Dune (Dune 2000 / Emperor)

| Faction | Playstyle | HP | SPD | DMG | RNG | Special / signature |
|---|---|:-:|:-:|:-:|:-:|---|
| Ordos | Mobility / Stealth | − | ＋ | − | ・ | Fastest, less punch; Deviator (mind control); Raider trikes; stealth. |
| Ixians | Turtle / Tech Rush | ・ | ＋ | ・ | ・ | **Holographic decoys** (Projector), stealth Infiltrator, hover/tech; fascist technocrat. |
| Atreides | Balanced | ・ | ・ | ・ | ・ | Middle-of-road; Sonic Tank; quick+powerful (reference-like). |
| Harkonnen | Power / Heavy Armor | ＋ | − | ＋ | ・ | Power at expense of speed; Devastator; Death Hand. |

### StarCraft

| Faction | Playstyle | HP | SPD | DMG | RNG | Special / signature |
|---|---|:-:|:-:|:-:|:-:|---|
| Terran | Turtle / Positional | − | ・ | ・ | ・ | **Infantry FRAIL** (Marine 40 HP, cheapest); *mech/vehicles invert to +HP tanky* (Siege 150, Goliath 125); Ghost/Siege = +RNG. |
| Protoss | Tech / Power Units | ＋ | − | ＋ | ＋ | **Shields → eff-HP 160–450 (tanky every type, confirmed)**; expensive, few, powerful. Melee Zealot = short-range exception. |
| Zerg | Swarm / Map Control | − | ＋ | − | − | Swarm infantry frailest/cheapest (Zergling 35, Scourge 25); *heavy Zerg use the LineBreaker VEHICLE template → monster-tanks (Ultralisk 400) handled in the vehicle pass, not here.* |

**Layer-1 verified (`ORIGINAL_UNIT_STATS.md`):** Protoss eff-HP (160–450) ≫ Terran (40–150)
≈ Zerg-small (25–125). Terran & Zerg rows are the **infantry** read; both **invert to +HP for
their vehicle-template heavies** (Siege Tank, Ultralisk). Protoss shields make it tanky in
*every* type.

### Warcraft 2 — distinct stats (WC3 approach, NOT mirrored)

Original WC2 mirrors Human/Orc; Cameo re-stats them apart. Counterpart units
(Footman↔Grunt, Knight↔Ogre, …) must NOT share stats — split them along this lean:

| Faction | Playstyle | HP | SPD | DMG | RNG | Special / signature |
|---|---|:-:|:-:|:-:|:-:|---|
| Humans WC2 | Defensive / Versatile / Magic | ・ | ・ | ・ | ＋ | Healing (Paladin/Mage), towers, tech; methodical, longer reach. |
| Orcs WC2 | Aggressive / Brute | ＋ | ・ | ＋ | − | Bloodlust + Raise Dead; high-HP grunts, raw offensive power. |

**Layer-1 verified (`ORIGINAL_UNIT_STATS.md`):** original WC2 is a stat **MIRROR** (Footman =
Grunt 60 HP, Knight = Ogre 90, Archer = Axethrower 40, …) — so there is **no source lean to
inherit**. The Human-defensive / Orc-aggressive split is a **Cameo design choice (WC3
direction)**, magnitudes to be refined by the pending **WC3 pull**.

### Outpost 2

| Faction | Playstyle | HP | SPD | DMG | RNG | Special / signature |
|---|---|:-:|:-:|:-:|:-:|---|
| Eden | Colony / Tech Rush | ＋ | − | ＋ | ・ | Better tech, brute-force military, defense-oriented. |
| Plymouth | Colony / Area Denial | − | ＋ | ・ | ・ | Speed & trickery, stolen/improvised tech, Action Bomb, area denial. |

### RA2-Mod factions (Cameo-original / obscure — from `FACTIONS.md`; deeper source research pending)

| Faction | Playstyle (FACTIONS.md) | HP | SPD | DMG | RNG | Special / signature |
|---|---|:-:|:-:|:-:|:-:|---|
| Asian Alliance | Mass Horde / Cheap / Superweapons | − | − | − | ・ | ← **Eagle Red + Generals China** (web-verified): cheap, numerous, **SLOW** mass infantry (**horde bonus**), weak individually; heavy tanks (Overlord) + strong artillery, **weak air**, nuclear/superweapon finish. |
| Steel Consortium | Tech / Shields / Long-range defense | ＋ | − | ＋ | ＋ | ← **Foehn Revolt (Mental Omega) Last Bastion**: durable + **long-range area-denial** + defensive; nano-upgrades that swap roles; shields = +HP. |
| Latin Syndicate | Turtle / Artillery / Explosives | ＋ | − | ＋ | ＋ | ← maintainer: **turtle masters** (bunker), **best artillery + huge explosive power**; black-market Soviet surplus. (corrected from −HP/+SPD 2026-07-25.) |
| Naxis | Turtle / Heavy Armor | ＋＋ | −− | ＋ | ・ | **WW2 parody**; very tanky, slow; undead-revival superweapon. |
| Schwarzer Mond | Timing / Anti-gravity | ・ | ＋ | ＋ | ・ | ← **Iron Sky moon-Nazis**: anti-gravity → hover/flying units + saucers (aircraft); sci-fi tech; timing/burst spike; Götterdämmerung superweapon. |
| FutureTech | Tech Rush / Robotics | ＋ | − | ＋ | ＋ | **Droids = vehicle turn-rate (speed ×5)**; robotic, high-tech. |
| TKM | Modular (WIP) | ・ | ・ | ・ | ・ | Modular units — flagged WIP; treat as neutral until designed. |

## How this feeds the converter (implementation note)

The converter (`propose_class_rebalance.py`) currently makes stats unique by arbitrary
nudging. The next step is to bias the uniqueness step by the acting unit's faction lean
above: e.g. in the scout class, GDI/Soviet/Naxis scouts take the high-HP/low-speed end
of the spread, Nod/Ordos/Zerg scouts the high-speed/low-HP end — all still Δ≤1, all still
5-stat unique. **WC2 counterparts (Footman↔Grunt, …) are re-statted APART** along the
Human-defensive / Orc-aggressive lean — never mirrored (no-mirror law). This keeps every
unit unique **and** lore-true.

## Sources

- C&C TD: [GameReplays beginner guide](https://www.gamereplays.org/cnctiberiandawnremastered/portals.php?show=page&name=beginners_guide_tiberian_dawn), [Neo Encyclopedia](https://neoencyclopedia.fandom.com/wiki/Factions_of_Command_%26_Conquer)
- C&C TS: [Hardcore Gaming 101](https://www.hardcoregaming101.net/command-and-conquer-tiberian-sun/), [TV Tropes](https://tvtropes.org/pmwiki/pmwiki.php/VideoGame/CommandAndConquerTiberianSun)
- RA1: [TV Tropes](https://tvtropes.org/pmwiki/pmwiki.php/VideoGame/CommandAndConquerRedAlert), [CNC Wiki](https://cnc.fandom.com/wiki/Command_%26_Conquer:_Red_Alert)
- RA2/Yuri: [XWIS comparison](https://xwis.net/forums/index.php/topic/174385-sovs-and-allies-the-official-comparison/), [Yuri faction (CNC Wiki)](https://cnc.fandom.com/wiki/Yuri_(faction)), [Yuri's Revenge (Wikipedia)](https://en.wikipedia.org/wiki/Command_%26_Conquer:_Yuri's_Revenge)
- Dune: [Dune 2000 Q&A (GameSpot)](https://www.gamespot.com/articles/dune-2000-qanda/1100-2463781/), [Emperor: Battle for Dune (Dune Wiki)](https://dune.fandom.com/wiki/Emperor:_Battle_for_Dune)
- StarCraft: [Gameplay of StarCraft (Wiki)](https://starcraft.fandom.com/wiki/Gameplay_of_StarCraft), [TechEdvocate deep dive](https://www.thetechedvocate.org/the-three-races-of-starcraft-a-deep-dive-into-terrans-zerg-and-protoss/)
- Warcraft 2: [Wayward Strategy — Acute Asymmetry](https://waywardstrategy.com/2020/12/01/the-beauty-of-acute-asymmetry-in-warcraft-orcs-and-humans/), [Battle.net Orcs vs Humans](http://classic.battle.net/war2/ovh/index.shtml)
- Outpost 2: [Cola Powered Gamer review](https://colapoweredgamer.wordpress.com/2019/03/16/review-outpost-2-divided-destiny/), [Liquisearch gameplay](https://www.liquisearch.com/outpost_2/gameplay)
- Modded factions: [Foehn Revolt (Mental Omega Wiki)](https://moapyr.fandom.com/wiki/Foehn_Revolt) → Steel Consortium; [Generals China (StrategyWiki)](https://strategywiki.org/wiki/Command_&_Conquer:_Generals/China) + [Eagle Red (CNC Wiki)](https://cnc.fandom.com/wiki/Eagle_Red) → Asian Alliance; [Iron Sky (TV Tropes)](https://tvtropes.org/pmwiki/pmwiki.php/Film/IronSky) → Schwarzer Mond; Latin Syndicate + Naxis per maintainer.
