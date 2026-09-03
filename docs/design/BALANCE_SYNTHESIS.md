# Balance Synthesis Plan — mods → Cameo (master capture)

**Status:** living plan, captured 2026-07-25 from a long maintainer strategy session. This is the
**durable record** of the whole "extract-the-mods → synthesize → fix Cameo balance" program, so
work can resume from a fresh session with nothing lost. Read alongside:
`ORIGINAL_UNIT_STATS.md` (the extracted reference data + reference map), `FORMULA_V2.md` (the
class-baseline formula), `ARMOR_SYSTEM.md` + `mods/cameo/weapons/weapons.yaml` (weapon/warhead
templates), `DESIGN.md` (binding laws — the §7–§10 rules below must be promoted there).

---

## 0. Why we did all this (the goal)

Cameo has real balance problems: **extreme values** — some units are so tanky they can't be
killed, some deal so much damage nothing survives, some whole classes (e.g. **MBTs**) deal *too
little* damage while others deal too much; and units with a wide warhead mix have **no weakness**
(good against everything). The old Cameo balance had good *ideas*, executed poorly.

**The fix:** deeply analyse the best C&C / crossover mods, extract their stats, **normalize** them
to a common scale, **synthesize** the multiple mods + the original games + the old Cameo balance
into coherent targets, and run those through our algorithmic formula. We are NOT plug-and-playing
mod numbers — we normalize, reason, and extrapolate them into Cameo's own system.

---

## 1. Source library — the mods & how to read each (paths + extraction)

| Source | Game(s) | Engine | Local path | Extraction | Status |
|---|---|---|---|---|---|
| original TD | Tiberian Dawn | Westwood | Nyerguds gist | `parse_ini.py` | ✅ HP/Cost/Speed |
| original RA1(+Aftermath) | Red Alert 1 | Westwood | unitstatistics | web | ✅ HP |
| original TS+FS | Tiberian Sun | Westwood | `C:\Users\AedisToru\Downloads\Rules.ini` | `parse_ini.py` | ✅ |
| original RA2+YR | Red Alert 2 | Westwood | `Downloads\RA2inis`, `YRinis` | `parse_ini.py` | ✅ |
| StarCraft / Warcraft 2 | — | Blizzard | unitstatistics | web | ✅ |
| **DTA** | TD+RA1 crossover | **TS engine ×10** | `G:\...\DTA\DTA Release\INI\Rules.ini` + `Enhance.ini` | `parse_ini.py`, `compare_ini.py` | ✅ Classic+Enhanced |
| **Combined Arms** | TD/RA1/RA2/Yuri/**Scrin** | **OpenRA** | `Downloads\CAmod-master\mods\ca\rules\`+`\weapons\` | `openra_full.py` | ✅ **full weapons** (`ca_units.csv`) |
| **Shattered Paradise** | GDI/Nod/CABAL/**Scrin**/Mutant | **OpenRA** | `Downloads\Shattered-Paradise-SDK-bleed\mods\sp\rules\`+`\weapons\` | `openra_full.py` | ✅ **full weapons** (`sp_units.csv`) |
| **Mental Omega 3.3.6** | RA2 (Allied/Soviet/Epsilon/Foehn) | Ares/YR | `expandmo99.mix` (content-scan → `mo_ini/*.ini`) | `extract_all.py`→`ini_full.py` | ✅ HP/Cost/Speed; weapons split across mix entries (partial) |
| **CnC Reloaded 2.7.0** | **RA2 + TS combined** | Ares/YR | `Downloads\CnCReloaded-2.7.0\Tools\Map Editor\rulesmd.ini` (loose, full) | `ini_full.py` | ✅ **full weapons** (`cncr_units.csv`) |
| **Romanov's Vengeance** | **RA2 remake** | **OpenRA** | `Downloads\Romanovs-Vengeance-master\mods\rv\rules\` + `\weapons\` | `openra_full.py` | ✅ **full weapons** (`rv_units.csv`) |
| **OpenRA vanilla TD/RA1/TS** | TD, RA1, TS | **OpenRA (ref engine)** | `Downloads\OpenRA-bleed\mods\cnc`,`ra`,`ts` | `openra_full.py` | ✅ **full weapons** (`ora_cnc/ra/ts_units.csv`) — independent TD/RA1/TS voices |
| **Dune 2000 (OpenRA)** | Dune (Atr/Hark/Ordos) | **OpenRA** | `Downloads\OpenRA-bleed\mods\d2k` | `openra_full.py` | ✅ **full weapons** (`ora_d2k_units.csv`) — Ordos/Dune reference |
| Dune II / Emperor | Dune | Westwood | TBD (maintainer has no local copy) | — | ⏳ blocked (no folder) |
| Outpost 2 | — | Sierra | TBD | — | ⏳ TODO |
| SC2 / Cosmonarchy / WC3 | — | Blizzard | web | web | ⏳ identity-only |

**Scratchpad tools** (session scratchpad): **`ini_full.py`** (INI → full spreadsheet rows: unit →
Primary/Secondary weapon `Damage/ROF/Range/Burst` → warhead `Verses` profile + role classification;
writes CSV), **`openra_full.py`** (OpenRA rules+weapons with **recursive inheritance resolution** →
unit → Armament(Weapon,Damage-override) → weapon `ReloadDelay/Range/Burst/BurstDelays` → warhead
`Damage`+`Versus` map; writes CSV), **`synth_hp.py`** (normalizes archetype HP to each source's
rifleman → cross-source band vs Cameo anchor). Legacy: `parse_ini.py`, `compare_ini.py` (DTA
Classic-vs-Enhanced), `extract_openra.py`, `mix_extract.py`, `extract_all.py` (dump ALL mix
entries, keep INIs — **how MO was recovered**). Blowfish-encrypted mixes (flags `0x30000`, e.g.
`ra2md.mix`) still need XCC Mixer. **CSVs produced (uniform schema):** `ra2_units.csv`,
`yr_units.csv`, `ts_units.csv`, `cncr_units.csv`, `rv_units.csv`, `ca_units.csv`, `sp_units.csv`.

---

## 2. The synthesis map — which sources feed which Cameo faction

**★ CROSS-REFERENCE PRINCIPLE (maintainer 2026-07-25):** synthesize from **ALL** source material,
including cross-references. A unit that appears in several mods pools **every** appearance — e.g.
the **Apocalypse tank** is in vanilla RA2 **+ MO + Romanov's + CnC Reloaded + Combined Arms**, so
all five feed its synthesis, even though CA "mainly" targets TD/RA1. Each mod's cross-references
influence the other factions too; never restrict a mod to only its "primary" factions.

| Cameo faction group | Sources to synthesize (all pooled) |
|---|---|
| **RA2** — Allies / Soviets / Yuri | original RA2+YR **+ Mental Omega + Romanov's Vengeance + CnC Reloaded** (+ CA / SP cross-refs) |
| **TS** — GDI / Nod / Forgotten / CABAL | original TS+FS **+ Shattered Paradise + CnC Reloaded** (+ CA / MO cross-refs) |
| **TD + RA1** — GDI / Nod / Allies / Soviets / Japan | original TD+RA1 **+ DTA + Combined Arms** (+ cross-refs) |
| **Dune** — Ordos / Ixian (+ parked Atreides/Harkonnen) | **all Dune games**: Dune II + Dune 2000 + Emperor (Ixian ← Emperor House Ix) + any Dune-mod stats |
| **StarCraft / Warcraft** | original + SC2 / Cosmonarchy (SC) / WC3 (WC) — identity |
| **RA2 modded factions** | see §3 |

### 3. RA2-modded factions — specific inspirations
| Cameo faction | Inspiration sources |
|---|---|
| **Steel Consortium** | **MO Foehn Revolt** (durable/tanky — confirmed: Foehn Giantsbane 750 = tankiest infantry in MO) + Earth 2150 LC |
| **Latin Syndicate** | **MO Latin Confederation** (Soviet subfaction — black-market Soviet surplus, explosives, guerrilla; "basically the same") |
| **Asian Alliance** | **Generals China + MO China** (Soviet subfaction) **+ Combined Arms** (China refs) — mass horde |
| **Naxis** | WW2 parody + Iron Sky refs |
| **Schwarzer Mond** | Iron Sky (moon-Nazis) + **Earth 2150 Lunar Corporation** (anti-grav / hover / energy) |
| **FutureTech** | robotic (Earth 2140/50 **UCS** + RA3 FutureTech + CA/MO high-tech) |
| **Japan RA1** | **RA3 Empire of the Rising Sun + WW2 Japan + TOUHOU + misc** — a funny mix (transforming mecha, Rocket Angels, Touhou characters/bullet-hell flavour, imperial WW2) |

---

## 4. Extraction format — capture the FULL balance-spreadsheet stat set

**Directive:** extract every reference unit with the **same stats we put into the Cameo balance
spreadsheet**, so the reference is directly usable. Per unit:
- **HP** (Strength), **Cost**, **Speed**, **Tech tier**, **Armor type**
- Per weapon: **Damage per shot**, **Burst**, **BurstDelays**, **ReloadDelay**, **Range**,
  **MinRange**, **Warhead(s)**, and each warhead's **Versus values** (vs each armor type) + spread
- Then: **normalize** to that mod's basic rifleman and **convert to our system**.

**Tooling gap — CLOSED (2026-07-25):** `ini_full.py` + `openra_full.py` now extract the full weapon
set. Westwood INIs: `[Weapon]` `Damage`/`ROF`/`Range`/`Burst` + `[Warhead]` `Verses=` (11-column
order `none,flak,plate,light,medium,heavy,wood,steel,concrete,sp10,sp11`). OpenRA: `Armament:`
(with inline `Damage:` override) + `weapons/*.yaml` `ReloadDelay/Range/MinRange/Burst/BurstDelays`
+ `Warhead@…: Versus:` map, resolved through `Inherits:`. Each row is auto-classified
anti-inf / anti-armor / general from its versus profile. **The DPS/versus side (§8) is now
extractable.** See §12 for the first grounded output.

---

## 5. The methodology — normalize → synthesize → formula (the HOW)

The hard question the maintainer posed: we can't plug-and-play mod numbers (different scales), so
**how** do we combine mods + old Cameo + our formula? The method:

1. **Extract** every mod's FULL stats (§4), **normalized to that mod's basic rifleman** → a common
   *relative* scale (ratios, not raw numbers).
2. **Synthesize a target relative-profile** per Cameo class/faction by pooling the relevant sources
   (§2, weighted by relevance) **+ old Cameo Layer-2** (current stats — keep what works) **+ the
   original game**. Reason/extrapolate to a coherent relative target; fill gaps by role-analogy.
3. **Map** the relative target onto **Cameo's absolute scale** (basic rifle anchor = **20000 HP**).
4. **Set the CLASS ANCHORS** from these synthesized targets. *This is where per-class multipliers
   get baked in* (§7) — the anchor **is** the baseline actor.
5. **Run the formula** (`FORMULA_V2`, Δ≤1, 5-stat uniqueness) to price + **spread units within the
   class** around the synthesized anchor.
6. Result: the **formula still does the pricing/spreading** (keeps Cameo's system); the **mods set
   the anchors** (grounds the previously-arbitrary anchor picks in real, synthesized data). We
   never write a mod's HP into a unit — we write synthesized-normalized targets into the *anchors*.

**Formula may need changes:** anchor **ratios** should come from synthesized mod data (tighter than
today — see §6); the **DPS side** must be reworked around the weapon-template binding (§8).

---

## 6. The spread-width decision (maintainer question + honest recommendation)

**Question:** Cameo's spreads are wider than the mods (Cameo close-combat 2.5× / commando **4.0×**
the rifle, vs CA flame 1.8× / hero 2.2×). Is that a *problem*, or is it *necessary* because we have
so many units that must all be unique? Large spreads = unique but maybe too extreme + hard to
balance. Where's the middle ground?

**Honest recommendation:**
- The extreme spread is **likely a real cause of the "unkillable / unstoppable" complaint** — but
  the every-unit-unique law does **NOT** actually require it.
- **Uniqueness is cheap; extremes come from the ANCHORS, not from uniqueness.** Within a class,
  ~30 faction variants at small steps (e.g. 1000-HP steps on a 20000 base) span only ~2.5× —
  modest. The 16× total range (support anchor 5000 → commando 80000) comes from the **class-anchor
  ratios**, not from making units unique.
- **Uniqueness ≠ unique HP.** A unit can be unique via a *different* one of the 5 stats (speed,
  range, damage/shot, reload). Spread uniqueness across all five → HP can stay in a sane band.
- **Middle ground:** tighten the **class-anchor HP band** to roughly the mod-normalized range
  (**≈0.4× … ≈3.5×** the basic rifleman; the mods top out ~3.3–3.7×). Compress the total class
  band from ~16× toward **~8–9×**. Keep **within-class steps small**. This preserves uniqueness AND
  removes the extremes. Concretely: pull commando 4.0×→~3.5×, re-check support 0.25× (too frail?),
  and re-derive every class anchor from the §5 synthesis instead of arbitrary picks.

---

## 7. Baseline-only balancing — bake out per-class multipliers

**Directive:** stop balancing with per-class **multipliers**; balance **baseline actors only**.
- `mods/cameo/rules/.../defaults.yaml` currently gives class templates per-class
  `FirepowerMultiplier` / `DamageMultiplier` (extra firepower + damage-resistance). **Bake these
  into the baseline actor stats** so the baseline is WYSIWYG. Changing a baseline stat then reruns
  the whole class rebalance and updates every member.
- **KEEP (the only allowed global multipliers):** the global **50% firepower reduction** (ironically
  named *"global buff"*) **+ 150% damage multiplier**. Their unit/defense-versus-building
  asymmetry is now an explicit durability rule: the 150% applies **only to units + defenses**, so
  **regular buildings are exempt and stay much more durable**. The historical 2000-damage-step +
  1% actor-firepower tuning mechanism that originally motivated these values is retired; current
  weapon tuning uses a 100-damage grid and no per-actor FP residual knob.
- Everything else = resolved into baseline actors.

---

## 8. Weapon / warhead rework — STRICT class ↔ weapon binding

**The core problem:** mixing many warheads on one unit **averages** their versus-profiles → the
unit becomes **good against everything with no weakness**. Offenders: **StarCraft Ghost/Specter**
(anti-inf + anti-air + anti-tank all at once), **WC2 axethrowers / archers** and their upgrades
(**High Elven Archer, Head Hunter** — insane damage to everything, too much range, unstoppable),
mismatched mixes like **TD Nod Light Tank Mk2** (cannon + chemical, but the tank has no chemical
lore connection).

**The law (promote to DESIGN.md):**
- **Every unit class is bound to a specific weapon class/type.** MBTs → medium cannon; scouts →
  small arms; etc. A fixed connection unit-class ↔ weapon-class.
- **Warhead MIXING is only allowed via UPGRADES** (lore-justified, balance-costed) or **well-marked
  special-case units** (must be explicitly flagged as exceptions so we know they're intentional).
- **Every unit gets a STRENGTH and a WEAKNESS** — no unit may damage everything on its own.
- **Grow the warhead library:** make **more templates per role/situation** so units don't have to
  mix. E.g. **SmallArmsAP** (upgraded SmallArms, more vs tanks); dedicated anti-air, anti-armor,
  anti-structure warheads — each **good vs SOME armor types, BAD vs others** (real trade-offs).
- **Good mixing (allowed, thematic + from upgrade):** RA1 Soviet *Incendiary Bullets* (adds a light
  flame warhead to bullets); **Chemical Attack Bike** (upgrades Recon Bike: missile + chemical),
  **Chemical Stealth Tank** (upgrades Stealth Tank), **Chemical SSM** (replaces the SSM's fire
  warheads with chemical). These *replace/augment* along a lore line, from an upgrade.
- **Versus system:** the fixed **descending-order versus values** (spread + percentage; only the
  *order of armor types* is swapped per warhead) is fine **per warhead** — the failure is *mixing*,
  which averages the profile away. **One primary warhead per unit** keeps its weakness intact;
  upgrades add costed exceptions.

**Work:** audit `weapons.yaml` (all current templates + their versus-profiles), compare to the
mods' weapon/versus data (§4 extension), define the **unit-class ↔ weapon-class binding matrix**,
expand the warhead library, and remove the wild mixes (converting real ones to upgrade-gated).

---

## 9. Anti-Air capability — class-gated (promote to DESIGN.md)

Which classes may hit air (everything else = ground-only):
- **Infantry:** ONLY **Special Forces, Archers, Rocket Infantry**.
- **Vehicles:** **Support-Vehicle class** (APCs + dedicated AA — *consider splitting transport-APC
  vs dedicated-AA*, different roles), **Scout vehicles** (all have AA — they fill the AA role), and
  **high-tech tanks** with *limited* AA (unit-dependent — e.g. Mammoth / Apocalypse AA rockets;
  not every MBT).
- **Aircraft:** **all helicopters + planes** get AA (dogfights), and big **spaceships**. EXCEPT
  **flying artillery** and some support weapons (**Cryocopter beam**) = **anti-ground only** (too
  strong as AA, and slow projectiles don't make sense against air).

---

## 10. The rock-paper-scissors counter mandate

The end goal is a **real multi-layered rock-paper-scissors** system: **every role clearly counters
some roles while being countered by others**, expressed through clear roles + armor types + weapon
versus values. This is the giant unifying task that all the extracted data feeds. Class↔weapon
binding (§8), AA gating (§9), tightened spreads (§6), and baseline-only balancing (§7) are the
mechanisms; the mod synthesis (§2–§5) supplies the reference numbers.

---

## 11. Sequencing & open questions

**Sequence:** (a) finish extraction — CnC Reloaded + Romanov's Vengeance, then Dune + Outpost 2,
extend tooling to **weapons/versus** (§4); (b) build **normalized full reference tables** per mod
per faction (§5.1); (c) synthesize per-class/faction targets → **re-derive class anchors** (§5–§6);
(d) rework the **weapon/warhead library + class binding** (§8) and **AA gating** (§9); (e) **bake
out multipliers** (§7); (f) rerun the formula per class → apply. All under the RPS goal (§10).

**Open questions:** does the formula itself need reshaping to hit synthesized targets, or just
better anchors? How exactly to weight each source in the synthesis? Where to draw each class's
spread band precisely? — resolve with the data in hand, class by class.

---

## 12. GROUNDED SYNTHESIS FINDINGS — the HP-spread audit (2026-07-25)

First real cross-source output, from the seven uniform CSVs (§1). Every unit's HP is normalized to
**its own source's basic rifleman** (GI / Light Infantry / e1), so the numbers are directly
comparable *as multiples of the rifle*. Cameo's rifle anchor = **20000 HP = 1.00×**.

**Rifle HP per source (the ÷ anchor):** RA2 125 · YR 125 · CnCR 125 · TS 125 · RV 12500 · CA 5000
· SP 12500. (Raw scales differ 100×; normalization erases that.)

### 12.1 Infantry — normalized HP (×rifle)

| Archetype (Cameo class) | RA2 | YR | CnCR | TS | RV | CA | SP | **Source band** | **Cameo now** |
|---|--:|--:|--:|--:|--:|--:|--:|:--:|:--:|
| rifle / GI (scout) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | **1.00** | 1.00 |
| grenadier | – | – | – | – | 1.00 | 1.00 | – | **1.00** | **0.40** |
| rocket soldier (rocket_trooper) | – | – | – | 0.80 | 0.96 | 0.70 | 0.80 | **0.70–0.96** | **0.50** |
| flak/AA trooper (rocket_trooper) | – | 0.80 | 0.80 | – | 1.00 | – | – | **0.80–1.00** | **0.50** |
| engineer (support) | 0.60 | 0.60 | 0.60 | 0.80 | 0.80 | 0.50 | 0.80 | **0.50–0.80** | **0.25** |
| sniper (pure_sniper) | 1.00 | 1.00 | 1.00 | – | 1.00 | 0.90 | – | **0.90–1.00** | **0.55** |
| flame / pyro (special_forces) | – | – | – | – | 1.00 | 1.80 | – | **1.00–1.80** | 0.75 |
| shock / tesla (heavy_infantry) | 1.04 | 1.04 | 1.04 | – | 1.04 | – | – | **1.04** | **2.50** |
| desolator (heavy_sniper) | – | 1.20 | 1.20 | – | 1.20 | – | – | **1.20** | 1.25 |
| virus (heavy_sniper) | – | 0.80 | 0.80 | – | 1.00 | – | – | **0.80–1.00** | 1.25 |
| rocketeer / jet (flying) | 1.00 | 1.00 | 0.84 | 0.96 | 1.00 | – | – | **0.84–1.00** | 0.90 |
| commando / Tanya (commando) | 1.00 | 1.60 | – | – | 1.20 | 2.20 | – | **1.00–2.20** | **4.00** |
| Boris (commando) | – | 1.60 | 1.60 | – | 1.20 | – | – | **1.20–1.60** | **4.00** |

**★ The governing result — every C&C game/mod keeps basic-roster infantry inside a ~0.5×–1.8×
rifle band (a ~3× total spread).** Even elite heroes (Tanya/Boris) top out ~1.6× (CA's Tanya 2.2×
is the single widest). Infantry are differentiated by **role / weapon / cost / tech, NOT HP** — the
homogeneity insight, now quantified. Cameo violates this at both ends:
- **commando 4.0×** — nearly **double** the widest source (CA 2.2×), **3–4× the RA2 norm (1.0–1.2×)**.
- **heavy_infantry 2.5×** — vs shock/tesla's **1.04×** everywhere. Cameo made it **~2.4× too tanky**.
- **too fragile:** grenadier 0.40× (src 1.00×), engineer/support 0.25× (src 0.5–0.8×), sniper 0.55×
  (src ~1.0× — a deliberate Cameo glass-cannon choice, but far below every source).

### 12.2 Vehicles — normalized HP (×rifle)

| Tier / unit | RA2·YR·CnCR | TS | RV | CA | SP | **Consensus (RA2-fam+TS)** |
|---|--:|--:|--:|--:|--:|:--:|
| light tank | Lasher 2.4 | – | 1tnk 2.0 | 1TNK 5.4 | – | **~2.0–2.4** |
| MBT (Grizzly / Titan / medium) | Grizzly 2.4 | Titan 3.2 · Tick 2.8 | mtnk 2.4 | MTNK 10.4* | MMCH 3.6 · 4TNK 2.8 | **~2.4–3.2** |
| heavy tank (Rhino / assault) | Rhino 3.2 | 3TNK 2.8 | htnk 3.2 · 3tnk 3.2 | HTNK 19* | – | **~3.2** |
| Mammoth / super-heavy | – | Mammoth 4.8 | 4tnk 4.8 | 2TNK 9.4* | G4TNK 7.2 | **~4.8** |
| Apocalypse / epic | Apoc(YR/CnCR) 6.4 | – | apoc 6.4 | – | – | **~6.4** |

\* CA's wide inf↔vehicle gap is **NOT an outlier — it faithfully reflects the TD/RA1 era** (see the
CORRECTION in §17). CA is built on OpenRA's TD/RA1 base, where the MBT is genuinely ~9–10× rifle.
The "consensus" in this table is **RA2-era-specific**; the TD/RA1 era has its own, much wider ladder.

**Consensus vehicle ladder (RA2-family + TS agree tightly):** light **2.0–2.4×** · MBT **2.4–3.2×**
· heavy **3.2×** · Mammoth **4.8×** · Apocalypse/epic **6.4×**. **The whole tank ladder lives in a
~2–6.4× rifle window (~3× internal spread).**

### 12.3 Cameo TODAY vs the consensus — the quantified problem

Cameo current vehicle HP ÷ 20000 rifle (from the ledgers):

| Cameo unit | HP | ×rifle | consensus for its tier | verdict |
|---|--:|--:|:--:|---|
| TD Stealth Tank | 25000 | 1.25× | ~2.0 (light) | ok/low |
| RA1 Allied Medium | 90000 | 4.5× | ~2.4–3.2 (MBT) | high |
| **RA2 Grizzly** | 100000 | **5.0×** | ~2.4 (MBT) | **2× too tanky** |
| Naxis Tiger (MBT anchor) | 100000 | 5.0× | ~2.4–3.2 | high |
| RA2 Rhino | 130000 | 6.5× | ~3.2 (heavy) | 2× |
| TD Mammoth | 225000 | 11.25× | ~4.8 (mammoth) | 2.3× |
| **RA2 Apocalypse** | 350000 | **17.5×** | ~6.4 (epic) | **2.7× too tanky** |
| RA1 Soviet Mammoth | 375000 | 18.75× | ~4.8–6.4 | ~3× |
| Naxis Sturm Tiger | 250000 | 12.5× | epic ~6.4 | ~2× |
| Futuretech Future Tank | 650000 | 32.5× | epic ~6.4 | **5× — "unkillable"** |
| Japan Exorcist O-I | 750000 | 37.5× | epic ~6.4 | **6×** |
| Syndicate Tortuga | 875000 | 43.75× | epic ~6.4 | **7×** |
| Soviet Monster Tank | 1,000,000 | 50× | epic ~6.4 | **8× — "unstoppable"** |

**Diagnosis — both complaints are the SAME root cause: Cameo stretched a ~11× total spread into
~200×.**
- Sources span **support engineer 0.5× → Apocalypse 6.4× ≈ 11× total**.
- Cameo spans **support 0.25× → Monster Tank 50× ≈ 200× total** — ~18× wider than any source.
- **"Some units unkillable / unstoppable"** = the epic/experimental tier at **17–50× rifle** — no
  tech-appropriate enemy unit can trade with a 32–50× HP monster.
- **"MBTs feel too weak"** = *relative* — a basic MBT at 5× looks fine in isolation, but in a game
  where same-side super-units sit at 17–50×, the MBT is dwarfed; the ceiling is so high the whole
  floor feels flat. (Damage compounding it: the 2000-step made damage too high → the global 50%
  cut; §7.)

### 12.4 The data-grounded target band (feed this to the pipeline — §5)

Keep rifle = 20000 (1.00×). Allow Cameo ~1.5× more spread than the tight sources (a **middle
ground**, not a copy), and enforce a hard ceiling. Proposed anchor multiples:

| Band | ×rifle | HP @ 20000 rifle | notes |
|---|:--:|--:|---|
| support / engineer | 0.5–0.7× | 10–14k | up from 0.25× |
| grenadier / light support inf | 0.8–1.0× | 16–20k | up from 0.40× |
| **scout / rifle (anchor)** | **1.00×** | **20000** | unchanged |
| rocket / flak / sniper / SF | 0.8–1.3× | 16–26k | snipers back toward ~1.0× |
| heavy infantry (tesla/shock) | 1.5–2.0× | 30–40k | **down from 2.5×** |
| mortar / heavy sniper / melee | 1.2–1.6× | 24–32k | ~unchanged |
| **commando** | **2.0–2.5×** | **40–50k** | **HALVE from 4.0× / 80k** |
| light / scout vehicle | 1.5–2.0× | 30–40k | |
| **MBT** | **2.5–3.5×** | **50–70k** | the "too weak" fix is *relative* — bring the ceiling down, not the MBT up |
| heavy / Mammoth tank | 4–5× | 80–100k | down from 11–19× |
| super-heavy / Apocalypse-class | 6–8× | 120–160k | down from 17× |
| **epic / experimental (HARD CAP)** | **8–10×** | **160–200k** | down from 32–50× — this is the "unkillable" fix |

**Resulting total spread: ~0.5× … ~10× ≈ 20× total** (vs sources 11×, vs current ~200×). A true
middle ground: still wider than any single game (Cameo has more units to separate), but with a
firm ceiling so nothing is untradeable. **No infantry class exceeds the MBT's durability; no unit
exceeds ~10× rifle.** These become the re-derived class anchors in §5 step 4 — run through the
pipeline, never hand-edited.

**⚠️ SUPERSEDED IN PART BY §18 (maintainer, 2026-07-25):** the hard HP bands below are **retracted**
as *caps* — they become *descriptive* only. The real "unkillable" cause is **defensive upgrade
stacking**, not base HP; **epics (build-limit-1) are fine as-is**; and the correct base-unit limiter
is the **cost-band (50–400% class cost)**, not an HP ceiling. Read §18 first.

**Caveats / honesty:** (a) this pass covers **HP only** — DPS/versus (§8) and cost still need the
same treatment; a low-HP unit can still be oppressive via damage. (b) The epic tier is a **build-
limit-1 promotion role**, deliberately extreme — NOT squeezed into normal bands (§18.1).
(c) CA's wide gap shows some mods deliberately spread more; the 20× target is a judgement call the
maintainer signs off, not a law from the data. (d) Numbers are **proposals for the pipeline**, not
applied — no yaml/anchor was edited to produce this section.

---

## 13. GROUNDED WARHEAD LIBRARY + class↔weapon binding (2026-07-25)

The versus profiles the §8 rework needs, pulled from CnCR (RA2+TS combined, the richest set) and
cross-checked against RA2/YR/RV. Armor order below: **none · flak · plate · light · medium ·
heavy · wood · steel · concrete** (first three = infantry armors, light/medium/heavy = vehicle
armors, wood/steel/concrete = structures). All normalized to a 100-scale.

### 13.1 The rock-paper-scissors CORE triad (this IS §10's mechanism)

| Warhead | none flak plate · light med heavy · wood steel conc | Beats | Loses to |
|---|---|---|---|
| **SA** (small arms) | `100 80 80 · 25 13 13 · 38 25 13` | infantry | **all armor** |
| **AP** (armor-piercing cannon) | `25 25 15 · 75 100 100 · 65 45 60` | vehicles | **infantry** |
| **HE** (high-explosive splash) | `100 100 100 · 70 70 35 · 75 40 20` | infantry + light veh | **heavy armor** |

**This is a complete rock-paper-scissors already:** SA shreds infantry but pings off tanks; AP kills
tanks but wastes on infantry; HE covers the middle (infantry + light) but bounces off heavy armor.
**Each warhead has a built-in weakness — as long as a unit carries only ONE.** This is the whole
argument for the binding law: it's not our versus values that are broken, it's *mixing*.

**Proof that mixing erases the weakness** (the §8 core problem, quantified): averaging SA+AP →
`62 52 47 · 50 56 56 · …` — now roughly *flat* ~50 vs everything, **no weakness left**. A unit with
both is good against all targets. That is exactly StarCraft Ghost / WC2 archers / Nod LightTank Mk2.

### 13.2 The extended warhead library (each with a real trade-off)

| Warhead | Profile (none/plate · light/med/heavy · struct) | Role | Weakness |
|---|---|---|---|
| **Fire / Flame** | `100 80 60 · 15 9 10 · struct 50` | anti-infantry + anti-structure | armor |
| **Chemical / Toxin** | `100 100 100 · 25 20 15 · 10-25` | anti-infantry (ignores inf armor tiers) | armor, and no-op vs robotic |
| **Radiation** (Desolator) | `100 100 100 · 70 15 15` | anti-inf + anti-light | heavy armor |
| **Tesla / Electric** | `low inf · light 100 heavy 75 · struct 65-100` | anti-armor + anti-structure | infantry |
| **Prism / Laser** | `100 100 100 · 75 50 50 · wood 200` | general + anti-structure | heavy armor (dmg falloff) |
| **Sniper** (targets infantry only) | `100 · 50 · heavy 25` + ValidTargets:infantry | pure anti-infantry, huge/shot | **cannot target vehicles at all** |
| **Sonic / Wave** | broad, ignores some armor | general anti-armor | (specialty — cost-gate) |
| **AA (Flak/SAM/rocket)** | reuses a ground profile + **ValidTargets:air** | anti-air | **class-gated (§9), ground-limited** |

**Key structural finding:** **AA is a *targeting gate*, not a versus profile.** CnCR AA weapons
just reuse ground warheads with `ValidTargets=air` (GaussAA→SSA anti-inf, DualAABazooka→TTAP
anti-armor, TSSuperHE→general). So §9's "which classes may hit air" is enforced by ValidTargets on
the armament, exactly as planned — we do **not** need special AA versus columns, just the class gate.

### 13.3 The class ↔ weapon binding matrix (the §8 law, made concrete)

Each Cameo class binds to ONE primary warhead (mix only via upgrade / flagged exception, §8):

| Cameo class | Primary warhead | Role | Air? (§9) |
|---|---|---|:--:|
| scout / rifle | **SA** | anti-infantry | no |
| closecombat | **SA (+Chaingun, both anti-inf)** | anti-infantry brawler | no |
| grenadier | **HE / Grenade** | splash, anti-inf + light | no |
| mortar | **HE (indirect arc)** | long-range anti-inf/structure | no |
| pure_sniper | **Sniper (inf-only)** | anti-infantry, per-shot | no |
| heavy_sniper | **AP / Railgun** | all-ground anti-armor | no |
| heavy_infantry (tesla/shock) | **Tesla/Electric** | anti-armor + structure | no |
| rocket_trooper | **AP-rocket** | anti-armor **+ AA** | **yes** |
| archer | **arrow (arc)** | anti-inf **+ AA** | **yes** |
| special_forces | ⚠️ see flag below | versatile | **yes** |
| melee | **melee (inf-only)** | anti-infantry, no range | no |
| flying_infantry | per-unit | varies | (self) |
| commando | **C4 / pistol** | anti-inf + demolition vs buildings | no |
| support | none | — | no |
| **MBT** | **AP cannon** | anti-armor | no |
| light / scout vehicle | **SA autocannon** | anti-inf **+ AA** | **yes** |
| artillery vehicle | **HE (indirect)** | anti-inf/structure | no |
| flame vehicle | **Fire** | anti-inf/structure | no |
| heavy / Mammoth tank | **AP + limited AA rocket** | anti-armor (+situational AA) | **limited** |
| dedicated AA vehicle | **AA (Flak/SAM)** | anti-air | **yes (primary)** |

**⚠️ FLAG for the maintainer — the special_forces class contradicts the binding law.** Cameo's SF
template deliberately SUMs SA+Chaingun+Railgun (anti-inf + anti-armor + anti-air) — precisely the
"good against everything, no weakness" pattern §8 outlaws. Options: (a) declare SF the *one marked
class-wide exception* (versatile is its identity, costed accordingly), or (b) bind SF to a single
warhead + make its versatility an upgrade. This is a real design decision, not a bug to silently
fix — **needs a maintainer ruling.** (closecombat's SA+Chaingun is fine — both are anti-inf, so no
weakness is averaged away.)

**Work remaining on §8:** audit `mods/cameo/weapons/weapons.yaml` against this matrix (which actors
violate their binding), grow the template library to cover every row above, convert real thematic
mixes (Chem Bike, Incendiary Bullets) to upgrade-gated, and remove the wild ones. Then the DPS
side (§4 damage numbers) gets the same normalize→synthesize pass as HP got in §12.

---

## 14. AA-GATING AUDIT — first scan (2026-07-25)

§9 says only **Special Forces / Archer / Rocket** infantry may hit air. First scan across the whole
mod (detect armaments whose weapon has `ValidTargets: … Air …`, then cross-reference infantry
actors):

- **632 AA-capable weapon templates** mod-wide; **4856** air-targeting armament lines total.
- **190 INFANTRY actors carry an AA weapon** — far more than the SF/archer/rocket gate allows.
- A crude role-keyword filter flags **~141 as candidate violations.** Clear offenders (not
  false-positives): `ordos_lightinfantry` (basic LMG rifleman), `schwarzermond_lunarsoldier` (basic
  rifle), `ra2_soviets_crazyivan` (**IvanBomb** — a demolition charge targeting *air*),
  `yuri_initiate` (**PsychicJab** melee hitting air), `protoss_hightemplar` (**PsiStorm** AoE hitting
  air), `terran_jimraynor` / `latinsyndicate_narco` (pistols), `latinsyndicate_freedomfighter`
  (AK-47 + rocket both AA). **Basic rifle/pistol/melee/bomb weapons should never target air.**

**This confirms §9 is widely violated at the infantry level** — a major, concrete source of "AA is
everywhere / air is useless" imbalance. **BUT the per-actor list needs a refined, dedicated audit
tool** (the keyword filter has false positives — legit snipers like `asianalliance_asiancommando`
got flagged; and some `…AA`/`…SmallAA` weapons are the *intended* AA variant). 

**Next step (scripted, not manual):** add `tools/audit/audit_aa_gating.py` ⚠ (**proposed, never built** — no such script) to the suite that (a)
resolves each armed actor's Cameo **class** (via the `class_anchor`/`balance_include` tags or
template inheritance, not a name heuristic), (b) lists actors whose class is NOT in the §9
air-allowed set yet carry an unconditional (non-upgrade) AA armament, and (c) emits to
`docs/audit/latest/aa_gating.md` **via `run_all.sh`** (bash only — PowerShell `>` writes UTF-16,
). The vehicle/aircraft gate (support/scout/hi-tank; no
flying-artillery AA) is the same check over `vehicles.yaml`/`aircraft.yaml`. This tool is the
clean way to enforce §9 mod-wide; the scan above is only the scoping evidence that it's needed.

---

## 15. THE THREE-DOCUMENT PROGRAM (maintainer spec, 2026-07-25)

The maintainer wants the reference materialised as **three linked documents**, each a full
spreadsheet-style table of **every reference unit** across every source game/mod. This section is
the binding spec; §16 proves it end-to-end on one unit. The three documents are generated by
tooling from the seven CSVs (+ future Dune/Outpost2), not hand-typed.

### 15.1 Document 1 — `ORIGINAL_UNITS_RAW.md` (raw, translated to our naming)

Every unit **exactly as it is in its own game**, only the *field names* translated to Cameo's
system (Strength→**HP**, ROF→**ReloadDelay**, Verses→**Versus**, etc.). Columns:

`Game/Mod · Unit (source name) · HP · Cost · Speed · Tech · Armor · Weapon · Damage · Burst ·
BurstDelays · ReloadDelay · Range · MinRange · Warhead · Versus-profile · **Cameo category** ·
**Description**`

- **Cameo category** = one of the class templates in `defaults.yaml`. **Maintainer ruling
  (2026-07-25) — the vehicle taxonomy expands; these templates are TO BE CREATED** (a downstream
  boot-gated `defaults.yaml` task) and used as category names now:
  - **`^LightTankTemplate`** (NEW) — light tank, distinct from and below the MBT.
  - **`^MainBattleTankTemplate`** — the MBT.
  - **`^HighTechTankTemplate`** — advanced/high-tech tank.
  - **`^TankDestroyerTemplate`** (NEW) — dedicated AP anti-armor glass-cannon.
  - **`^AntiAirTankTemplate`** (NEW) — mobile AA tank (HAS a weapon); **moved OUT of Support
    Vehicle.**
  - **`^ArtilleryTankTemplate`** (NEW) — *between* tank and artillery (tanky, indirect-ish).
  - **`^ArtilleryTemplate`** — real artillery (fragile, long-range, indirect).
  - **`^SupportVehicleTemplate`** — **REDEFINED: unarmed transports / real support only, NO weapon.**
  - Plus existing `^LineBreakerTemplate`, `^FireSupportTemplate`, `^EpicVehicleTemplate`,
    `^ScoutVehicleTemplate`, `^HarvesterTemplate`, and the infantry / aircraft / ship / defense
    templates.
- **Description** = a **short deep-web-researched blurb** per unit (role, faction, what makes it
  distinct in its own game). This is the one column that needs manual/web fill — auto-fill the rest.

### 15.2 Document 2 — `ORIGINAL_UNITS_NORMALIZED.md` (converted to Cameo power level)

Same rows, **every stat normalized+converted onto Cameo's scale** (rifle = 20000 HP; the §5
method), formatted like our existing balance spreadsheet so a reader compares source units to Cameo
units directly. HP = ×rifle × 20000; cost via the §15.5 conversion; damage/versus via the §15.4
role-map (NOT raw-number copy). One row per (unit × source).

### 15.3 Document 3 — `SYNTHESIS_DELTA.md` (the payoff)

Pool **the same unit across all sources** (Apocalypse ∈ {RA2, YR, MO, RV, CnCR, CA}), compute a
**synthesized compromise** per stat (§15.6 weighting), then show the **Δ vs Cameo's current value**
for every stat, and a **recommendation** phrased for the formula pipeline. Ends with a **report**:
ranked list of how far each Cameo unit is from its synthesized target + the anchor/formula change to
close the gap. Columns:

`Unit · [per source: HP×rifle] · **Synth target (×rifle → HP)** · **Cameo now** · **Δ HP** ·
[same for cost, DPS] · **Class** · **Recommendation**`

### 15.4 Versus / damage handling — THE scale trap (maintainer's warning), solved

Raw Versus values are **NOT comparable across sources** and must never be numerically averaged:
- **Westwood** (TD/RA1/TS/RA2/YR): any %, routinely **>100** (e.g. Boris AKM 200 vs infantry).
- **DTA:** Westwood values **×10** → up to **1000%**.
- **Combined Arms / Shattered Paradise / Romanov's Vengeance:** each its **own** OpenRA `Versus:`
  scale (CA uses `Tree/Drone/Rocket` armor names + values to ~200; RV to ~200; SP different again).
- **Cameo:** a **generated** ladder, 100→floor(10/25/40) by step 6/5/4, Shield the only value >100
  (§ARMOR_SYSTEM). So Cameo versus ≈ **10–140**, deterministic from (armor-order, step).

**The rule (scale-invariant):** we do **not** convert versus numbers. We read each source warhead's
**relative profile** — *which armor classes it is best→worst against* (the ORDER, which is
scale-free) — classify its **role** (anti-inf / anti-armor / HE / AA / anti-structure / chemical /
tesla / …, §13), then assign Cameo's matching **generated template**. Magnitude differences
(Westwood 300, DTA 1000, OpenRA 200) are irrelevant because only the ordering carries the identity.
Damage-per-shot is likewise normalized to the source's **rifle DPS**, never copied raw.

### 15.5 Cost conversion — VERIFIED

- **Westwood C&C (TD/RA1/TS/RA2/YR/mods):** cost is already credits → **use directly** (then
  normalize to the source's rifle cost for cross-mod compare). DTA cost is Westwood-scale (no ×10 on
  cost, only HP/versus) → direct.
- **StarCraft (two resources):** **`credits = 4 × minerals + 8 × vespene`** — VERIFIED exact against
  the ledger: Wraith 150/100→1400, Battlecruiser 400/300→4000, Science Vessel 100/225→2200 (three
  exact fits). Ratio **1 mineral : 2 gas** = the maintainer's remembered "2×/4×", at 4×/8× magnitude.
- **Warcraft (gold/wood):** by symmetry **`credits = 4 × gold + 8 × wood`** (assume same; verify
  against a WC2 ledger unit before locking).
- **SAGE / C&C4 / Earth:** economies don't map → **identity only**, no cost row.

### 15.6 Source-weighting rules for the synthesis (§15.3)

1. **A faithful REMAKE is not an independent vote.** Romanov's Vengeance reproduces vanilla RA2
   ratios *exactly* (Apoc 6.4× in both) — counting RV separately **double-counts vanilla.** Weight
   {vanilla + RV} as ~one source; the true independent voices are the *rebalances* (MO, CnCR, CA).
2. **Normalize each mod to its OWN rifle before pooling** (per-mod scale differs; §12.2). 
3. **Flag wide-gap outliers.** CA runs a deliberately wide inf↔vehicle spread (Apoc **26×** rifle vs
   the 6.4× consensus) → down-weight or exclude from the HP compromise, keep for role/identity.
4. **The compromise is a judgement, not a mean.** Prefer the tight consensus of the independent
   rebalances, then apply Cameo's intended extra-spread allowance (§12.4) as a deliberate offset.

---

## 16. WORKED EXAMPLE — the Apocalypse Tank (proves §15 end-to-end)

The maintainer's own example. All numbers from the extracted CSVs + the Cameo ledger.

**Document 1 row (raw, translated):**

| Source | Unit | HP | Cost | Spd | Armor | Weapon | Dmg | Burst | Reload | Range | Warhead | role | Category |
|---|---|--:|--:|--:|---|---|--:|--:|--:|--:|---|---|---|
| RA2/YR | Apocalypse | 800 | 1750 | 4 | heavy | 120mmx | 100 | 2 | 80 | 5.75 | ApocAP | anti-armor | Epic/HighTech Tank |
| CnCR | Apocalypse | 800 | 1750 | 4 | super_heavy | 120mmx | 100 | 2 | 90 | 5.75 | ApocAP | anti-armor | Epic Tank |
| RV | apoc | 80000 | 1750 | 75 | Heavy | 120mmx | 100 | – | 65 | 6.0 | (AP) | anti-armor | Epic Tank |
| CA | apoc | 130000 | 2600 | 43 | Heavy | 152mm | 4500 | – | 135 | 5.75 | (AP) | anti-armor | Epic Tank |
| **Cameo** | ra2_soviets_apocalypse | **350000** | — | — | — | (AP cannon) | — | — | — | — | AP | anti-armor | ^EpicVehicleTemplate |

Secondary on all: **MammothTusk** (HE anti-air rockets) → matches §9 "high-tech/epic tanks may carry
*limited* AA." Weapon identity is **rock-solid across every source: AP anti-armor primary + AA-rocket
secondary** — so the §13 binding is already correct; only the HP/cost magnitude is off.

**Document 2 (normalized to rifle):** ÷ each source's rifle HP (RA2-fam 125, RV 12500, CA 5000):

| Source | HP ×rifle |
|---|--:|
| RA2/YR | 800/125 = **6.4×** |
| CnCR | 800/125 = **6.4×** |
| RV | 80000/12500 = **6.4×** |
| CA | 130000/5000 = **26.0×** (wide-gap outlier) |
| **Cameo** | 350000/20000 = **17.5×** |

**Document 3 (synthesis + delta):**
- Independent voices: {RA2/YR = RV (remake, one vote)} = **6.4×**; CnCR (rebalance) = **6.4×**; CA =
  26× (**outlier, down-weighted** per §15.6.3). → **consensus = 6.4× rifle.**
- Apply Cameo's epic-tier extra-spread allowance (§12.4 caps epic at 6–8×) → **synth target ≈ 7×
  = ~140,000 HP** (consensus 6.4× nudged up to honour Cameo's "wider than sources" intent).
- **Δ HP: 350,000 → ~140,000 = −210,000 (−60%).** The Cameo Apocalypse is **2.7× too tanky** vs the
  pure consensus, **2.5× over** the epic cap.

**Recommendation (formula-phrased) — CORRECTED per §18:** the Apocalypse is a **regular MBT/
HighTech tank, NOT epic** (§18.1). With MO added, the RA2-era Apoc consensus is **3.0–6.4× rifle**
(MO 3.0×, vanilla/CnCR/RV 6.4×) → a Cameo target roughly **80–140k**, reached **not by a hard HP cut
but by the cost-band** (§18.4): price the Apocalypse in-formula and let its 50–400%-cost envelope
settle its HP. **Keep the weapon binding as-is** (AP anti-armor + limited AA rocket — correct across
every source). **Do NOT** apply this to Monster Tank / Tortuga / Exorcist — those are, respectively,
an intended epic, an intended slow-tank trade-off, and an ability-pricing bug (§18.3), not base-HP
problems.

**Method proven:** raw → normalized → synthesized → Δ → formula recommendation, with the versus
scale-trap avoided (weapon identity read by role, not number) and the remake double-count caught.
Next: run this generation over **all** units (tooling), fill Document 1 descriptions from deep web
research, and produce the ranked "how far off is every Cameo unit" report (§15.3).

---

## 17. OpenRA-vanilla extraction + the ERA-DEPENDENT ratio (2026-07-25) — corrects §12

Extracted the **vanilla OpenRA** implementations from `Downloads\OpenRA-bleed\mods\` (the reference
engine's own TD/RA1/TS + Dune 2000) via `openra_full.py` → `ora_cnc/ra/ts/d2k_units.csv`. Four new
**independent voices**, plus the **Dune 2000 reference** for the Dune factions.

### 17.1 Per-game tank ladder (HP ÷ that game's rifle)

| Source | rifle | light | **MBT** | heavy | mammoth | epic/apoc |
|---|--:|--:|--:|--:|--:|--:|
| TD (Westwood raw) | 50 | – | **8.0×** (400) | – | 12.0× (600) | – |
| TD (OpenRA cnc) | 5000 | 6.4× | **9.0×** | – | 17.4× | – |
| RA1 (OpenRA ra) | 5000 | 4.6× | **9.2×** | 12.0× | 18.0× | – |
| RA1 (Combined Arms) | 5000 | 5.4× | **10.4×** | 9.4× | 19.0× | – |
| RA2 (vanilla INI) | 125 | – | **2.4×** | 3.2× | – | – |
| RA2 (Yuri / CnCR) | 125 | – | **2.4×** | 3.2× | – | 6.4× |
| RA2 (Romanov's V) | 12500 | 2.0× | **2.4×** | 3.2× | 4.8× | 6.4× |
| Dune 2000 (OpenRA) | 6000 | – | **3.2–4.8×** (Ordos 3.2 / Atreides 3.7 / Harkonnen 4.8) | – | (Devastator ~8×) | – |

### 17.2 ★ The finding — the inf:tank ratio is ERA-DEPENDENT, and it corrects §12

- **TD/RA1 era:** frail infantry → **MBT ≈ 9–10× rifle, mammoth ≈ 17–19×.** Agreed by Westwood-raw,
  OpenRA-cnc/ra, AND Combined Arms.
- **RA2 era:** tanky infantry → **MBT ≈ 2.4×, heavy 3.2×, mammoth 4.8×, apoc 6.4×.** Agreed by
  RA2/YR/CnCR/RV.
- **Cause:** Westwood ~2.5×'d infantry HP from TD (50) to RA2 (125) while tank HP held flat (TD
  Medium 400 ≈ RA2 Grizzly 300), so the ratio compressed ~4×.
- **★ CORRECTION to §12.2:** I earlier flagged CA's ~10× MBT as a *wide-gap outlier*. **It is not** —
  CA (and DTA, and OpenRA-cnc/ra) faithfully reproduce the TD/RA1 era's genuinely wide ratio. §12's
  "MBT ≈ 2.4–3.2×" is **RA2-era-specific**, and must be labelled as such; there is no single
  cross-era MBT multiple.

### 17.3 ★ The implication for Cameo — it needs ONE unified vehicle ladder

Cameo uses **one rifle anchor (20000) for every faction on one battlefield.** The eras disagree ~4×
on inf:MBT, so Cameo **cannot preserve both** (TD Medium at 9× → 180k HP while an RA2 Grizzly at
2.4× → 48k would be incoherent when they fight side by side). Therefore:

- **Infantry: keep normalizing to the source rifle** — infantry sit at **0.5–1.8× in every era**
  (stable; §12.1), so the rifle-multiple transfers cleanly.
- **Vehicles: do NOT copy the source rifle-multiple** (it's era-dependent). Set the Cameo **vehicle
  class anchors by cross-era judgement**, preserving only each game's **within-roster ORDER**
  (mammoth > heavy > MBT > light). Recommended unified ladder (consistent with §12.4): **light 2×,
  MBT 3×, heavy 4×, mammoth 5×, epic 6–8× rifle.** This lands between the RA2 (narrow) and TD/RA1
  (wide) eras, leaning RA2 because Cameo's rifle anchor is itself tanky-infantry-scaled (like RA2's
  125, not TD's 50).
- **Nuance this exposes:** Cameo's *RA2* units are over-scaled vs their own era (Apoc 17.5× vs 6.4×,
  Grizzly 5× vs 2.4×), while Cameo's *TD* Mammoth (11.25×) actually sits *below* its native 17–19×.
  So "bring the tanks down" is really **"harmonize every faction's tanks onto the one unified
  ladder"** — some RA2 units come way down, a few TD heavies barely move. Pure-Cameo epics (Monster
  50×, Tortuga 44×) exceed every era and come down hardest.

### 17.4 Dune 2000 reference (for the Dune factions)

Rifle = `light_inf` 6000. Infantry: light_inf 1.0×, trooper 1.17×, grenadier 1.0×, **sardaukar
1.67×** (elite). Vehicles: trike 1.5×, quad 1.83×, siege_tank 1.9×, missile_tank 2.17×, **combat
tank — Ordos 3.2× / Atreides 3.7× / Harkonnen 4.8×** (the house durability order), Devastator ~8×.
This is the **Ordos** synthesis anchor (Dune faction). Note the house identity is already in the HP:
Harkonnen tankiest, Ordos lightest — matches `FACTION_IDENTITY.md`. Dune II + Emperor still needed
(maintainer has no local copy) for the full Dune synthesis; D2K-OpenRA covers the core now.

---

## 18. MAINTAINER CORRECTIONS (2026-07-25) — the "unkillable" cause is UPGRADES, not base HP

Critical course-correction from the maintainer. **My §12 diagnosis was partly wrong.** Recording it
in full; §12/§16 are superseded where they conflict with this section.

### 18.1 "Epic" is a ROLE, not a high HP number — Apocalypse is NOT epic

- **Epic units in Cameo** = hero-like: **build limit 1**, *deliberately allowed to be far stronger
  than everything else*, a heavy investment, **easily focus-fired down**. **Working as intended.**
  - **The reliable signal is `BuildLimit: 1`, NOT the promotion.** MOST epics sit behind a Tier-4
    promotion (4 promo points), but **not all** — e.g. the **RA1 Soviet MAD Tank** is epic with **no
    promotion** (so far).
  - **Hero infantry split the same way:** some (**Volkov, Exorcist**) need a **Tier-4 promotion**;
    others (**Commando, Tanya**) are **regular hero units, no promotion.** Detect epic/hero from
    `BuildLimit`/the hero template; treat the promotion as an *optional tech-tier* attribute.
- **Monster Tank at 1,000,000 HP is FINE** — it's an epic (build-limit-1, promotion-gated), and has
  *never* been particularly strong in practice. My §12 "Monster 50× = unstoppable" was **WRONG**.
- **The Apocalypse is a REGULAR unit** (no build limit), so its category is **NOT `^EpicVehicle`** —
  it's a `^MainBattleTank` / `^HighTechTank`. §16 miscategorised it; the HP comparison still holds as
  data, but "epic re-anchor" was the wrong framing — see the cost-band below.
- **Doc-1 generator fix:** `category()` must NOT map high HP → epic. Epic = build-limit-1 +
  promotion-gate (a rules property: `BuildLimit: 1` + promotion prereq), detected from the actor,
  never from HP.

### 18.2 The REAL "unkillable / unstoppable" cause = DEFENSIVE UPGRADE STACKING

Base units **without upgrades are basically fine.** Units become unkillable when **defensive
upgrades stack**, especially combined:
- **Armor upgrades** (damage multiplier / damage resistance),
- **Regeneration** (nanobots / self-heal),
- **Shields** (Steel Consortium, Dune factions).

Several of these together → unstoppable. **So the fix is NOT re-anchoring base HP down — it's fixing
upgrade stacking/pricing.** This is a **new top work-item** (see 18.5). My §12 "Cameo stretched HP
to 200×" over-indexed on base HP; the base spread wants only *modest* tightening (18.4), the
*upgrades* are the actual bug.

### 18.3 Unit-specific corrections (not the problems I thought)

- **Tortuga (875k HP):** intentionally **ultra-slow + ultra-tanky** → in practice **one of the WORST
  units** (so slow it's trivially outplayed/kited; nobody builds it despite the HP). Its durability
  is a *deliberate trade-off*, correctly costed by being unusable. **Leave it.**
- **Exorcist O-I (750k HP):** the problem is **NOT tankiness** — it's her **ability**, a
  superweapon-like nuke that blows up everything around her. **Underpriced:** its **special-category
  ability modifier is 1.25×** and should be **~2.0×**. Fix the ability price, not the HP.

### 18.4 The maintainer's COST-BAND proposal — assessment (asked: "what do you think?")

**Proposal:** run the formula so **every unit sits within 50%–400% of its class-baseline COST** (hard
caps), with the **verifier at exactly 2.5× cost**. E.g. scout baseline 100 → hard floor 50, hard
ceiling 400.

**My honest assessment — this is a GOOD mechanism, and better than my §12.4 HP-cap idea:**
- ✅ **It caps AGGREGATE power, and cost already IS the power proxy** (Cost = cost0·(O/O0+P/P0+Q/Q0)/3
  — HP, DPS, range folded into one). A hard 400% cost ceiling ⇒ no unit exceeds 4× its class's total
  power. That's a real, clean limit.
- ✅ **It respects trade-offs — which my HP-cap did NOT.** A unit can still be very tanky *if it pays
  by being weak elsewhere* (exactly the Tortuga: huge HP, but so slow it's bad). My "HP ≤ 10× rifle"
  rule would have wrongly *forbidden* the Tortuga; the cost-band *allows* it because its low speed/
  utility keeps its cost in band. **The cost-band is the correct tool; retract the hard HP cap.**
- ✅ **Verifier at 2.5× cost** sits comfortably inside the 0.5–4.0× band (upper-middle), leaving
  headroom for genuinely maxed units without them blowing past 4×.
- ⚠️ **Caveat 1 — it bounds aggregate, not any single stat.** A 400%-cost unit that dumps everything
  into HP could still be ~8–10× baseline HP if its DPS/range are minimal. Usually fine (it's a
  trade-off), but if you ever want a *specific* stat ceiling too, add a per-stat sub-cap on top.
- ⚠️ **Caveat 2 — it does NOT touch UPGRADES** (priced separately), so **it will not fix the
  unkillable problem** (18.2). The cost-band tidies *base* units (modest, welcome); the upgrade-
  stacking fix is a separate track.
- ⚠️ **Caveat 3 — it's per-class.** Cross-class absolute spread still reflects the class baselines
  (support 500 vs commando 3000, etc.) — which is correct; classes *should* differ.

**Verdict: adopt it.** It's the right amount of tightening ("not as much as I recommended" — agreed),
it's formula-native, and it preserves design intent. It **supersedes §12.4's hard HP bands** (those
become *descriptive* "where units tend to land," not caps). Pair it with the upgrade fix (18.5).

**★ Refinement — it's a BASEBAND, not just two points (maintainer 2026-07-25):** the baseline and the
verifier define a **band where most units should live**, and the distribution is deliberately uneven:
- **Sweet spot = 100%–250% cost** (baseline → verifier): **~80% of all units** should land here,
  and **skewed toward the baseline** (100%). This is where the formula is most trustworthy.
- **Hard caps = 50%–400%** — only a **few** units below baseline or above the verifier.
- **★ The formula BREAKS DOWN below ~75% cost** — units get too weak for their price. Real examples:
  a **600-credit tank** against an 800 baseline, and the **Naxis Rifle Recruit at 75¢** vs the 100¢
  base version — both already *extremely* weak. So **75% is the practical floor**, not 50%.
- **High end is more forgiving:** a unit with **4× HP + 4× firepower that only reaches ~3.5× cost** is
  very strong but *acceptable* — gate it behind a **later tech tier**. (Above the verifier = "pays a
  tech-tier tax," not "banned.")
- **Implication for the pipeline:** the class **verifier** should be placed so that 2× HP + 2× DPS
  lands near **2.5× cost** (upper-middle of the band), and the fit tool should **flag any member
  priced below ~75%** as a break-down risk, not just clamp at 50%.

### 18.5 Revised work-items (this section supersedes §12's conclusions)

1. **Fix defensive-upgrade stacking** — audit armor(damage-mult) / regen(nanobots,self-heal) /
   shield(Consortium,Dune) upgrades; cap or diminish stacking so combined defensives can't make a
   unit unkillable. **This is the actual "unkillable" fix — new top priority.**
2. **Adopt the cost-band** (50–400% class-baseline cost, verifier 2.5×) as the base-unit power cap.
3. **Re-price the Exorcist ability** (special modifier 1.25× → ~2.0×); audit other superweapon-like
   abilities for the same under-pricing.
4. **Fix the epic definition in tooling** — epic = build-limit-1 + promotion-gate, never HP.
   Recategorise Apocalypse (regular MBT/HighTech), keep Monster/epics as-is.
5. Base-HP re-anchoring is **demoted** to whatever the cost-band naturally produces — no drastic cut.

### 18.6 Mental Omega — re-included (639 units, `mo_units.csv`)

Reconstructed MO's full roster by merging its split `expandmo99.mix` INIs → `ini_full.py`. **MO is
the key per-faction-differentiation reference** (the maintainer's point): unlike vanilla's flat
baselines, MO re-stats every faction's basic units — **Conscript 205 ≠ GI**, and it re-tunes heavies
(**Rhino 500, Apocalypse 620** — MO *lowered* the Apoc). MO rifle ≈ 205 (buffed infantry), so MO's
inf:MBT ratio = 500/205 = **2.4×** (matches vanilla) but its Apoc is only **3.0× rifle** (vs vanilla
6.4×) — MO compressed the top. **MO is now a first-class synthesis voice** for the RA2 factions and
the template for how Cameo should de-homogenise per faction.

---

## 19. INTER-CLASS COMPARISON — do Cameo's classes relate correctly? (2026-07-25)

The maintainer's question: we found the **rifle** is 5000 in CA / vanilla-OpenRA-TD/RA1 vs Cameo's
**20000** (Cameo = 4× that base). But is the **4× consistent across every class**, or did some
classes drift? I.e. **do scout↔MBT↔helicopter↔defense relate to each other in Cameo the way they do
in the source games?** Method: normalize each class to **its own game's rifle**, then compare the
per-class multiple. If Cameo's multiple ≠ the reference's, that class has drifted *relative to
infantry*. (RA2 used as the primary reference — most Cameo factions are RA2-engine; TD/RA1 era-caveat
below.)

| Class (representative) | Reference RA2 ÷rifle(125) | Cameo ÷rifle(20000) | **Distortion (Cameo÷Ref)** |
|---|--:|--:|:--:|
| rifle / scout | 1.00 | 1.00 anchor (factions 1.2–1.3) | ~1.1× |
| **MBT** (Grizzly) | 2.4 | 5.0 | **2.1×** |
| heavy tank (Rhino) | 3.2 | 6.5 | **2.0×** |
| Apocalypse | 6.4 | 17.5 | **2.7×** |
| artillery (V3) | 1.2 | 1.9 | 1.6× |
| **aircraft** (attack heli/jet) | 1.2–1.6 | 2.9–4.25 | **~2.5×** |
| basic defense (Pillbox/Sentry) | 3.2 | 5.0 | 1.6× |
| advanced defense (Tesla/Prism) | 4.8 | 6.0–6.75 | ~1.3× |

### 19.1 ★ The answer — the 4× is NOT uniform; tanks & aircraft drifted UP relative to infantry

Ordered by how much Cameo inflated each class *relative to its own infantry*:

> **infantry ~1.1× < advanced-defense ~1.3× < artillery / basic-defense ~1.6× < tanks ~2.0× <
> aircraft ~2.5× < Apocalypse-class ~2.7×.**

- **Infantry are on-scale** (~1× the reference ratio) — the 20000 rifle is a faithful 4×/160× lift.
- **Tanks are ~2× over.** In RA2 an MBT is worth **2.4 riflemen** of HP; in Cameo it's **5.0**. So
  **Cameo infantry are ~2× weaker vs armor** than the source intends → armor feels dominant, infantry
  feel disposable against tanks. This is the clearest inter-class break.
- **Aircraft are ~2.5× over** — RA2 aircraft were deliberately *fragile* (1.2–1.6× rifle, killed fast
  by AA); Cameo made them **2.9–4.25×**, so air is far harder to shoot down relative to everything
  else. (Compounds the §14 "AA is everywhere" issue from the *other* side.)
- **Defenses drifted the LEAST** (1.3–1.6×) — closest to reference. Note buildings *also* get the §7
  damage-exemption, so their *effective* durability is a bit higher than the HP ratio alone shows.

### 19.2 Era caveat + what it means for the pipeline

- **Era caveat (§17):** this is the RA2 reference. TD/RA1 units have a *wide* native ratio (MBT
  9×), so Cameo's TD tanks are **less** distorted vs their own era. But Cameo is **one battlefield**,
  so the RA2 tanks sitting at 5× while the unified target is ~3–4× is the real inconsistency.
- **Pipeline consequence — this is exactly the data the class anchors need.** To make classes relate
  correctly, the **vehicle and aircraft anchors must come DOWN relative to the infantry anchor**:
  - **MBT anchor** → ~**2.5–3× rifle** (50–60k), not the current ~5× (100k).
  - **Aircraft anchor** → ~**1.5–2× rifle**, not the current ~3–4×.
  - **Defenses** → roughly keep (they're near reference); mind the §7 damage-exemption interaction.
  - **Infantry anchors** → keep (on-scale).
- **HP-only caveat:** inter-class balance also rides DPS + cost; the **cost-band (§18.4)** governs
  aggregate power, and this HP finding says *where the HP portion of the vehicle/aircraft anchors
  should sit.* Feed both into the anchor re-derivation — never hand-set. This makes the classes
  **relate to each other** the way the source games (and thus real RTS balance) intend.

### 19.3 ⚠️ MAINTAINER PUSHBACK (2026-07-25) — the baseline ratios are probably FINE

The maintainer's call on §19.1: **the baseline inter-class ratios are acceptable as-is.** Scout
baseline 20k HP / 100¢ vs Tiger MBT 100k / 800¢ (a **5× HP** tank, 2.5× helicopter) "seems really
fair." So the "bring vehicle/aircraft anchors DOWN to the RA2 reference" recommendation is **NOT a
mandate** — it's descriptive. The more likely problem is **specific later-game units scaling too
much with HP**, not the class *baselines*. **Approach: change nothing wholesale; test alternatives
in-game.** §19.1 stays as reference data (Cameo tanks *are* ~2× the RA2 ratio), but acting on it is a
per-case, test-driven decision, not an anchor cut. The §8.4 "vehicle anchors down" step is
**downgraded to "review, don't presume."**

---

## 20. PRICE COMPARISON + the NOSTALGIA↔UNIQUENESS resolution (2026-07-25)

The maintainer's core design tension: **keep units close to their original games (nostalgic) AND
make each faction as unique as possible (interesting)** — informed by how DTA Enhanced / Mental Omega
did it. These pull opposite ways. Grounding data first, then a framework that dissolves the conflict.

### 20.1 How close ARE Cameo's prices to the originals? (RA2 family)

| Unit | Cameo ¢ | YR ¢ | CnCR ¢ | MO ¢ | Cameo/orig | verdict |
|---|--:|--:|--:|--:|--:|---|
| Apocalypse | 1750 | 1750 | 1750 | 1600 | **1.00×** | nostalgic |
| Conscript | 100 | 100 | 100 | 60 | **1.00×** | nostalgic |
| Grizzly | 750 | 700 | 700 | – | 1.07× | nostalgic |
| Rhino | 850 | 900 | – | 900 | 0.94× | nostalgic |
| War Miner | 1200 | 1400 | 1400 | 1400 | 0.86× | nostalgic |
| Terror Drone | 600 | 500 | 500 | 500 | 1.20× | ~nostalgic |
| Flak Trooper | 416 | 300 | 300 | 150 | 1.39× | deviated |
| Tesla Tank | 1800 | 1200 | 1200 | – | **1.50×** | deviated (specialist) |
| Mirage Tank | 1600 | 1000 | 1000 | – | **1.60×** | deviated (specialist) |
| Prism Tank | 2000 | 1200 | 1200 | – | **1.67×** | deviated (specialist) |

**★ Finding — Cameo ALREADY threads the needle, and it does it by a principle:** the **iconic core**
(Apocalypse, Conscript, Grizzly, Rhino, War Miner) stays at **~1.0× the original price**, while the
**specialist / high-tech units** (Mirage stealth, Prism, Tesla) are re-priced **1.5–1.67× up** to pay
for added power/identity. That's not drift — it's *nostalgic core + priced-up specialists.* The mods
agree: **MO** re-prices along **economy identity** (Conscript **60¢** — cheaper, Soviet spam-doctrine
— *and* tankier at 205 HP), showing price itself is a legitimate uniqueness lever when it expresses a
faction's economy.

### 20.2 The framework — three tiers of deviation freedom (dissolves the conflict)

The tension is only real if nostalgia and uniqueness compete on the **same** axis. Split the axes:

| Layer | Nostalgia rule | Uniqueness freedom |
|---|---|---|
| **Role + silhouette** | **NEVER change** — a Rhino is always a heavy Soviet tank, an Apocalypse always a slow super-heavy. This recognizability *is* the nostalgia. | none — this is the anchor |
| **Stat-mix (HP/spd/rng/DPS at a given cost)** | default = the original feel | **ALWAYS free** — express faction character (tanky-slow vs fast-frail) at the same role/cost. **"Free" uniqueness:** the formula holds cost stable while the mix varies. This is the PRIMARY lever (how MO/DTA de-homogenise). |
| **Price** | default = the **original price** for iconic units (nostalgic, recognizable) | **deviate PURPOSEFULLY** — (a) for genuine power/role enhancements (Mirage/Prism/Tesla ↑), or (b) for faction **economy identity** (spam-faction ↓ cheaper, elite-faction ↑ pricier). Never random, always in-band. |

**★ The guarantee that makes this safe:** the **formula + cost-band (§18.4) mean you cannot make a
unit that is unique-but-broken.** Every stat-mix and every price gets priced and band-checked
(`check_band.py`), so *pursue uniqueness freely* — the pipeline is the safety net. Nostalgia is the
**default**; uniqueness is a **deliberate, priced deviation from it**; the formula keeps every
deviation honest.

### 20.3 The operating rule (feeds Documents 1–3)

1. **Document 1** already carries every unit's **original price** — that is the nostalgic anchor.
2. **Default a Cameo unit to its original price + role.** Keep it unless a faction-identity reason
   moves it.
3. **Spend uniqueness on the stat-mix first** (free, formula-stable), on **price second** (only for
   real enhancements or economy identity), and **never on role/silhouette.**
4. **Synthesis (Document 3)** proposes, per unit, `original → (stat-mix deviation for faction X) →
   priced by formula`, and the Δ report shows how far each landed from nostalgic — so the maintainer
   sees the nostalgia cost of each uniqueness choice explicitly. **Nostalgic where it can be, unique
   where it should be, balanced always.**
