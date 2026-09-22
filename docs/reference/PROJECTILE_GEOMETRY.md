# Projectile and warhead geometry — a separate review corpus

> **Maintainer, 2026-09-12:**
> *"check reference data for projectile speed, acceleration and spread and falloff"* ·
> *"those should all be also collected but not automatically be applied, only after I review
> and approve them"* · *"all the requested data must always be collected for every unit"* ·
> *"it's for later when we review projectiles and warhead template spread and damage falloff
> but it has **nothing to do with the unit itself**. It's a **separate review process**."*

Built by `tools/reference/extract_projectile_geometry.py` into
`docs/reference/projectile_geometry_evidence.json` (JSONL, one record per line).

⛔ **NOTHING IN THIS FILE VOTES ON A UNIT TARGET.** `reference_distribution` builds its
distributions from `WEAPON_STATS` and `ARMOR_STATS`; no field here joins either tuple, and
`reference_targets.target_for` is only ever called on those. Wiring any of it into a unit
estimate is a separate, deliberate approval — which is exactly what the maintainer reserved.

## Why it is keyed by projectile and by warhead, not by unit

A projectile is shared by dozens of weapons across dozens of units. Hanging its geometry off
one unit row would duplicate it and imply the unit owns it — and the unit does not: a template
does. The first attempt did attach `w_phys_*` columns to the unit row and it was wrong for
exactly that reason; the helper survives in `extract_ini_units.physics_of`, the wiring does not.

What the units give us instead is **coverage**. Every unit's primary and secondary weapon slots
are walked, so every projectile and warhead any unit can actually fire is present, with the
units listed against it. `units` and `weapons` on a record are that coverage evidence.

## What is in it

| | records | |
|---|--:|---|
| projectiles | **1,091** | across 9 INI sources |
| warheads | **1,803** | |
| distinct units contributing coverage | **2,602** | |

| field | coverage | lives on | note |
|---|--:|---|---|
| projectile speed | **1,080 / 1,091** | the **WEAPON** section | so one projectile legitimately has several; recorded as `{speed: how many weapons}` and **never averaged** |
| `Acceleration` | 295 / 1,091 | the PROJECTILE section | |
| `ROT` | 413 / 1,091 | the PROJECTILE section | guided-missile turn rate — the movement model `PROJECTILE_TRAVEL.md` names as still missing |
| `Arcing` / `Inaccurate` | — | the PROJECTILE section | qualifiers: they say whether a speed number describes a straight line at all |
| warhead spread | **1,187 / 1,803** | the WARHEAD section | `CellSpread` 893 · `Spread` 294 · absent 616 |
| `PercentAtMax` (falloff) | 705 / 1,803 | the WARHEAD section | the INI analogue of Cameo's `Falloff` tail |

8 projectiles are referenced by a weapon but have no section in `rules.ini` — TS-era mods
declare projectiles in `art.ini` as often as in rules, and this extractor does not read
`art.ini`. They are recorded with `declared: false` rather than dropped.

## ⛔ Units differ per engine. Do not average, do not convert without a ruling

* **TD/TS-era** warheads (DTA Classic, DTA Enhanced, Twisted Insurrection) declare `Spread`
  in **leptons** — `DemoAtomicWH` 512, `MultiClusterWH` 48, `NukeLaunchWH` 4. 256 leptons to
  a cell.
* **RA2/YR-era** warheads declare `CellSpread`, and the range of magnitudes is the open
  question: `AAHE` reads 0.5 (half a cell, plainly), while `BlueJammer` reads 225 and
  `TrueSuperIronWeaponWH` 200. Ares fixed-point providers are in play. **Deciding what 225
  means is the review this data was collected for** — it is not something the extractor
  should guess.

`spread_key` records which key supplied each number, so a reviewer never has to infer which
engine's units they are reading. Falloff is the tell that the two eras differ in kind, not
just in scale: `PercentAtMax` covers 705 RA2-era warheads and **1, 2 and 0** in DTA Classic,
DTA Enhanced and Twisted Insurrection respectively — TD-era warheads mostly do not have the
concept.

Reads are **exact-case**, like every read in `extract_ini_units`: OpenTS looks INI names up by
raw bytes, so a near-miss spelling reads as absent rather than as a value.

## Relationship to the other reference documents

* `PROJECTILE_TRAVEL.md` — the **OpenRA** peer side: 598 weapon records, interpolation-length
  and impact-tick modelling for `Bullet` and `InstantHit`. That is travel *time*; this is
  authored *geometry*, and the two are complementary. Its open item — "guided missiles and
  custom beams still need their own movement/impact models" — is what the `ROT` column here
  is for.
* `WARHEAD_REFERENCE.md` / `docs/reference/versus_raw.json` — the armor **profile** side
  (`Verses` / `Modifier.*`). Spread and falloff are the *shape* of the same warhead;
  `DESIGN.md`'s Spread/Falloff law (radius = (N−1) × Spread, shape from value spacing) is what
  this evidence will eventually be read against.

## Re-running it

```
python tools/reference/extract_projectile_geometry.py                      # all 9 sources
python tools/reference/extract_projectile_geometry.py --source "Mental Omega"
```

⚠ A `--source` run **merges** rather than overwrites: rows from sources not in the run are
kept. That guard exists because `extract_ini_units` once replaced every other source's rows
with one source's when given `--source X --json <corpus>`, and this corpus is built from the
same nine files.
