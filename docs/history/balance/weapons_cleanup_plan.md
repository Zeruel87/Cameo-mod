# Central weapons.yaml cleanup plan (below the DO-NOT-INHERIT divider)

> ⛔ **ARCHIVED 2026-08-23 — not current.** Moved out of the live documentation set: it is either machine-generated (regenerate it rather than reading this copy) or the programme it belonged to is finished or dormant. Kept for provenance. Start at [`docs/HANDOFF.md`](../../HANDOFF.md).

_Maintainer directive (2026-07-25): everything below the `DO NOT INHERIT BELOW THIS LINE` divider
(weapons.yaml:3241) should leave the central file — used-by-a-faction → its ContentPack, unused →
deleted, the rest → a separate yaml. Analysis by `scratchpad/below_divider_usage.py` (reproducible)._

## Reality check — the divider is heavily VIOLATED

Below the divider: **148 top-level defs = 28 `^`-templates (inheritable) + 120 concrete weapons.**
The catch: **many below-divider `^`-templates are generic class templates that everything inherits**
— `^BallisticWeapon` (19 files), `^Cannon`, `^Artillery`, `^MissileWeapon`, `^AntiGroundMissile`,
`^AntiAirMissile`, `^DamagingExplosion(HE)`, `^FireWeapon`, `^FlameWeapon`, `^HeavyMG`, `^LightMG`,
`^MG`, `^EMPDamage`. **These cannot go to a pack — they belong ABOVE the divider as real class
templates.** So the cleanup is NOT "move everything below to packs"; it's a sort into 4 buckets.

## The 4 buckets

### A. DELETE — unused (30, zero references) ✅ safe
`RockDebris2/3/4`, `SmallHeliCrash`, `LargeHeliCrash`, `CosmeticExplodeSmall`, `Tail`, `Horn`,
`Teeth`, `AnthraxCloudLarge/Blue/BlueLarge/Purple`, `BigChemSpray`, `Short8Inch`, the `GLToxin*`
cluster variants, **`^TSRailgun`**, and the **6 Demolition/Concussion families**
(`^LightDemolition`…`^HeavyConcussion` — confirmed 0 inheritors, never wired up). All safe to remove.

### B. PROMOTE ABOVE the divider — real generic class templates (⚠ decision)
Heavily-inherited `^`-templates that ARE the weapon-class system and must stay inheritable:
`^BallisticWeapon`, `^Cannon`, `^Artillery`, `^MissileWeapon`, `^AnyMissile`, `^AntiGroundMissile`,
`^AntiAirMissile`, `^Explosion`, `^DamagingExplosion`, `^DamagingExplosionHE`, `^FireWeapon`,
`^FlameWeapon`, `^HeavyMG`, `^LightMG`, `^MG`, `^EMPDamage`. **Move these ABOVE the divider** (and
they then qualify for `WeaponClass`). *Maintainer: confirm which of these are canonical class
templates vs redundant (e.g. `^MG`/`^HeavyMG`/`^LightMG` may overlap `^SmallArms`/`^Chaingun`).*

### C. MOVE to a ContentPack — used by exactly one faction pack
`^AADeployTargeting` → Naxis · `TSEMPulseCannon` → TS/GDI · `AnthraxCloud` → D2k/Ordos ·
`AnthraxCloudPurpleLarge` → SC/Zerg · plus theme templates `^TSLaser`/`^DRPlasmaWeapon`/`^DinoWeapon`
→ their theme (TS / DarkReign / dinos). *(Only a handful are truly single-pack.)*

### D. KEEP in a separate central file — concrete weapons shared by the theme yamls
The remaining ~90 concrete weapons (`UnitExplode*`, `BuildingExplode`, `HeliExplode`, `GenericC4`,
`DemoTruckTargeting`, `Atomic`, `IonCannon`, `Patriot`, `Pistol`, `Claw`, the `GL*` Generals weapons,
`SW*` Star Wars lasers, etc.) are referenced by the **central theme files**
(`generals.yaml`, `darkreign.yaml`, `dune2.yaml`, `starwars.yaml`, `wh40k.yaml`, …) and/or several
packs. They can't collapse into one pack. **Move them to a new engine-loaded
`mods/cameo/weapons/misc_weapons.yaml`** (registered in `mod.yaml`) so `weapons.yaml` is left with
ONLY the class templates. References are preserved (the new file is loaded).

## Execution order (each phase = its own boot-gated commit)

1. **A — delete the 30 unused** (safest; shrinks the problem). Boot-gate.
2. **B — promote the ~16 generic templates above the divider** (after you confirm the list). Boot-gate.
3. **D — split the remaining concrete weapons into `misc_weapons.yaml`** + register in `mod.yaml`.
   Now `weapons.yaml` = class templates only. Boot-gate.
4. **C — move the single-pack weapons/templates into their ContentPacks.** Boot-gate.

## Decisions needed from the maintainer
1. **Bucket B list** — confirm which below-divider `^`-templates are canonical class templates to
   promote above the divider (esp. the `^MG`/`^HeavyMG`/`^LightMG` vs `^SmallArms`/`^Chaingun`
   overlap — consolidate or keep both?).
2. **OK to delete bucket A** (the 30 unused, incl. the never-wired Demolition/Concussion families)?
3. **Separate file name** — `misc_weapons.yaml` OK, or you prefer another split (e.g. per theme)?
