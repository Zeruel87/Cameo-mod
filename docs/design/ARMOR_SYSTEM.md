# ARMOR SYSTEM — the weapon-class Versus law (canonical, 2026-07-19)

_How every weapon template's Versus table is constructed. This is THE
reference for creating or renaming weapon templates (MEGAPLAN §3).
Confirmed against the live weapons/weapons.yaml, not guessed._

## The two orthogonal axes

Every damage weapon's Versus table is fully determined by two choices:

1. **LEVEL (power)** = the STEP SIZE by which effectiveness falls from
   100 down the armor ladder. Bigger step = steeper falloff =
   specialist; smaller step = flatter = good-against-everything.
2. **PROFILE (role)** = the ORDER of the 17 armor types — which armor
   sits at 100 (the best target) and the descending sequence after it.
   The step is constant; the ORDER is the weapon's identity.

## LEVEL — the step law (main AreaDamage warhead)

| level | step | runs 100 → | Shield | WC (K) |
|---|---|---|---|---|
| **Light** | **6** | **10** | generated separately | 0.75 |
| **Medium** | **5** | **25** | generated separately | 1.00 |
| **Heavy** | **4** | **40** | generated separately | 1.25 |
| **Super** | **3** | **55** | generated separately | **1.50** |

`Super` (step 3) is the CONFIRMED superweapon band (maintainer 2026-08-02) for **Nuclear** and
**charged Tesla** — one notch above Heavy in both flatness and WeaponClass.

> ⚠ **The `WC (K)` column no longer prices anything (W4, 2026-08-11).** It still names
> the LEVEL of a warhead family, which is what the step law above is about, but
> `formula.dps()` dropped its `weapon_class` factor and the workbook's DPS cell dropped
> `*WeapClass` to match. Weapon quality is now measured directly by the K coefficient in
> `weapon_efficiency.py` — the tier weight and the measurement would otherwise charge a
> weapon twice for the same property. Do not reintroduce WC into a price formula.
>
> Note the name collision: this `WC (K)` and the pricing `K` are **different quantities**.
> This one is a per-level design weight (0.75 / 1.00 / 1.25 / 1.50); the pricing K is a
> measured dimensionless coefficient per weapon (`EFFECTIVE_DAMAGE.md`).

- 16 non-Shield armor types, so 100 down in 15 steps to the floor:
  light 100,94,88,…,10 · medium 100,95,…,25 · heavy 100,96,…,40.
- ⚠ **`Shield = top + floor` is RETIRED (W25, 2026-08-16).** It held only while every
  profile peaked at exactly 100; once profiles were renormalised, "top" became a function
  of each family's SHARPNESS and the rule rewarded sharpness instead of anti-shield design
  (a sword read 200, a Tesla coil 151). Replaced by `DESIGN.md §12.0c`:
  `Shield = PHYSICS_RANK x SHIELD_LEVEL x damped structural scale`, compressed onto exactly
  [100, 400] with every value distinct and Tesla top at every level. The text below is kept
  as the historical statement of the old law.
  Main warhead: top 100 + floor (10/25/40) = **110 / 125 / 140**.
  Shield is the only main value above 100; heavier weapons hit shields
  hardest.
- Flatter = tougher target set survives less: a HEAVY weapon never
  drops below 40% vs anything (relatively universal); a LIGHT weapon
  drops to 10% vs its worst target (hard specialist).
- DESIGN §12 notes the ladder extends to steps 3/2/1 for
  superheavy/superweapon bands — the L/M/H (6/5/4) triple is the
  standard set. **Step 3 = `Super` (floor 55, WC 1.5) is CONFIRMED** (Nuclear +
  charged Tesla, 2026-08-02); steps 2/1 remain unused — confirm before using.

## The folded percentage half — its own armor profile

Each generated family carries one `AreaDamage` warhead. Its flat hit uses
`Damage` and `Versus`; its folded max-health hit is enabled by
`PercentageScale` and uses `PercentageVersus`. The percentage armor profile
still ladders down by step 1 in a level-dependent window:

| level | % top → floor | Shield % (= top + floor) |
|---|---|---|
| Light | 16 → 1 | **17** |
| Medium | 20 → 5 | **25** |
| Heavy | 25 → 10 | **35** |
| Super | 30 → 15 | **45** |

Same armor ORDER as the main hit; step always 1. Shield obeys the same percentage-profile
law. This table is a SHAPE, not the final percent of max health.

At the standard `PercentageScale: 10000`, every 2000 flat `Damage` produces 100 basis
points (1.00% of max health) before `PercentageVersus`. The engine rounds that derived
basis-point amount once, then applies the armor row and the victim's maximum HP. This is
therefore a **modest contribution proportional to the same `Damage`**, not an independent
16–30% hit and not a fixed damage floor. Low final values can still truncate to zero, but
hard immunity is not a design guarantee and must not be inferred from the retired
whole-percent twin. A nonstandard `PercentageScale` is the explicit flat-vs-percentage
ratio dial.

Standalone `AreaDamagePercentage` or `HealthPercentageDamage` warheads still exist on
bespoke weapons. Those are independent max-health hits and create a real output floor;
the balance model prices them separately from folded damage. See `EFFECTIVE_DAMAGE.md`.

## PROFILE — the standard armor orderings (which type is at 100)

The 17 armor types: Shield, None, Flak, Plate, Heroic, Scout, Fighter,
Wood, Light, Bomber, Steel, Medium, Helicopter, Concrete, Heavy,
Spaceship, Superheavy. The profile picks the descending order:

| profile | leads with (100) → … | good vs | example today |
|---|---|---|---|
| **anti-infantry** | None, Flak, Plate, Heroic… | infantry | ^SmallArms (light), ^Chaingun (medium) |
| **universal** | Scout, None, Wood, Light, Flak, Concrete, Medium… | everything (gentle slope) | ^ShrapnelWeapon (medium) |
| **HE / anti-vehicle** | Scout, Wood, Light, Concrete, Medium… | light-medium vehicles + structures | ^MediumCannon (medium), ^HeavyCannon (heavy) |
| **AP / anti-heavy** | Superheavy, Heavy, Medium, Light… (inverted) | heavy + superheavy | ^TankDestroyerCannon (light-step, AP order) |
| **anti-structure** | Wood, Concrete… | buildings | ^HeavyBomb |
| **AA** | Fighter, Bomber, Spaceship, Helicopter… | aircraft | ^FlakWeapon (medium) |

## PROFILE construction — the TWO-LEVEL ordering law (maintainer 2026-08-01)

**This is the authoritative way to build every order — the profile table above
is just a summary of it.** An order is DERIVED, never hand-typed, from two
decisions, so it is impossible to introduce the sub-ladder bugs the legacy
tables have (e.g. `^HeavyBomb` ran buildings `Wood > Concrete > Steel`, and
AP weapons ran infantry `None → Heroic`).

1. **MACRO-TYPE PRIORITY** — rank which unit TYPE the weapon is strongest
   against, best→worst: **Infantry / Vehicle / Building / Aircraft.** Types may
   be TIED = *combined* (interleaved) when the weapon is equally good vs several.
2. **LIGHT↔HEAVY DIRECTION** — within EVERY type, better vs light or heavy armor?
   Applied to the fixed **armor SUB-LADDERS (lightest → heaviest):**
   - Infantry: **None < Flak < Plate < Heroic**
   - Vehicle: **Scout < Light < Medium < Heavy < Superheavy**
   - Building: **Wood < Steel < Concrete**
   - Aircraft: **Fighter < Bomber < Helicopter < Spaceship**

   anti-**LIGHT** (HE, flame, bullets, arrows) → `None > … > Heroic`;
   anti-**HEAVY** (AP, tesla, railgun, chemical, missiles) → `Heroic > … > None`.
   **HE deals more to None than to Plate; AP deals more to Plate than to None.**

**Order = concatenate the macro blocks in priority order; inside each block emit
the sub-ladder in the chosen direction; interleave tied blocks round-robin with the
LONGEST sub-ladder LEADING** (so categories alternate evenly). inf(4)+veh(5) heavy =
`Superheavy Heroic Heavy Plate Medium Flak Light None Scout` (vehicle leads, 5>4);
all-4 combined = 5→4→4→3 (`V I A B …`). Ties keep the listed order.
LEVEL (Light/Medium/Heavy = step 6/5/4) only changes the falloff slope — **ONE
order per weapon TYPE, shared by all L/M/H versions.** `tools/balance/
gen_weapon_template.py` holds the per-type matrix (macro blocks + direction +
hits_air) and generates the whole table; `--orders` prints every order.
Combined examples: Concussion = all 3 ground types (light); Chemical =
infantry+vehicle (heavy); Flame = infantry+building (light); MissileAA =
air→vehicle (heavy); Flak = air→infantry (light). Full matrix + the current
weapon-type set: `docs/design/WEAPON_TYPE_SYSTEM.md`.

## Consequences for the new templates (MEGAPLAN §3)

Creating `CannonAP_Light/Medium/Heavy` = the AP armor ORDER with step
6/5/4. `MissileAA_Heavy` = the air ORDER with step 4. The "good vs
everything" explosion = the UNIVERSAL order at whichever step gives the
right flatness (medium step 5 = today's Shrapnel; heavy step 4 = even
flatter). So:

- The FAMILY name = the PROFILE (armor order).
- The Light/Medium/Heavy suffix = the STEP (6/5/4), i.e. power/flatness.
- A tool generates the whole 17-row Versus table from (order, step) —
  no hand-typing; every template stays law-conformant by construction.

## Special cases to confirm with the maintainer

- HAZMAT armor overrides (e.g. ^ShrapnelWeapon HAZMAT:50) — per-family
  exceptions, not part of the step ladder.
- The step 3/2/1 superheavy/superweapon bands (heavy-% Shield now
  confirmed = 35 via the top+floor law).
- Friendly-fire variant — RULE (maintainer 2026-08-02): **every AoE weapon** deals
  reduced friendly fire = **HALF radius + HALF damage** (a `*FriendlyFire` twin at 50%
  damage / smaller spread). Single-target/hitscan weapons have none. See
  `WEAPON_TYPE_SYSTEM.md` §13.4.

## The two explosion families (maintainer decision 2026-07-19)

Explosions consolidate to **TWO** families (was Grenade/Shrapnel/
HeavyBomb), each Light/Medium/Heavy, generated by
`tools/balance/gen_weapon_template.py`:

### DEMOLITION — anti-structure, soft-priority
Order: Wood, Concrete, Steel, None, Flak, Plate, Heroic, Scout, Light,
Medium, Heavy, Superheavy, Fighter, Bomber, Helicopter, Spaceship.
Structures first, then infantry, then vehicles, then air. Good vs soft
and buildings, useless vs armour/air.
- **^LightDemolition** (step 6) — grenadiers. Spread 400.
- **^MediumDemolition** (step 5) — NEW mid-tier. Spread 600.
- **^HeavyDemolition** (step 4) — bombs. Spread 800. Versus is
  BYTE-IDENTICAL to today's ^HeavyBomb (confirmed).

### CONCUSSION — universal, gentle slope
Order (from today's ^ShrapnelWeapon): Scout, None, Wood, Light, Flak,
Concrete, Medium, Plate, Steel, Heavy, Heroic, Superheavy, Fighter,
Bomber, Helicopter, Spaceship. Good vs EVERYTHING, never great, never
useless. **^MediumConcussion** (step 5) == today's ^ShrapnelWeapon.

### Migration mapping (the ~300-weapon batch — SEPARATE, awaits go-ahead)
- `^Grenade` → `^LightDemolition`
- `^HeavyBomb` → `^HeavyDemolition`
- `^ShrapnelWeapon` → `^MediumConcussion`
- **Mixed-warhead weapons keep their other components**: e.g. the Soviet
  grenadier's `^Grenade + ^LightFlameWeapon` → `^LightDemolition +
  ^LightFlameWeapon`. Each such weapon is repointed per the pair-rename
  law (base + every variant together), resolver-diffed, boot-gated.
- Common `DamageTypes: Prone75Percent, TriggerProne, ExplosionDeath`;
  HeavyDemolition's old FireDeath/Incendiary flavour was demolition-ised
  (flame belongs to the flame families) — confirm if you want it kept.
