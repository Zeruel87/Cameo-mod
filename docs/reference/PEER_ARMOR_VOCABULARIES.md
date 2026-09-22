# Peer `Versus` armor vocabularies ΓÇö the input to armor-aware effective DPS

_AUTO-MEASURED from the 13 cloned OpenRA reference mods, read through `miniyaml.Ruleset`. This is DATA, not a mapping: the mapping must be hand-authored per source with confidence, and this file exists so that authoring starts from measurement rather than assumption._

## Why there is no universal mapping

**76 distinct armor tags across 13 mods.** Only **five** are shared by six or more: `None`, `Light`, `Heavy`, `Wood`, `Concrete` ΓÇö the Westwood core. Everything else is source-specific. Three findings make a guessed taxonomy indefensible:

* **Generals Alpha declares 37 tags, several of them PER-UNIT** (`vehicle.battle_bus.crate-1`, `aircraft.comanche.countermeasures`). Those are not an armor ladder, they are targeting switches, and they cannot map onto anyone else's classes.
* **OpenRA Dune II declares NO Versus at all** ΓÇö it cannot participate in armor-aware DPS.
* **OpenRA Dune 2000 ships case-duplicated tags** (`none` and `None`, `wood` and `Wood`), so even within one mod the vocabulary is not self-consistent.

ΓÜá `Versus` is a NODE WITH AN EMPTY VALUE whose CHILDREN are the armor rows. A probe reading `node.get("Versus")` gets the empty value and concludes the mod has none ΓÇö which is how this measurement first came back as "0 peers expose Versus" for all 13.

## Per-source vocabulary

| source | tags | Westwood core present | source-specific |
|---|--:|---|---|
| Combined Arms | 8 | `Concrete`, `Heavy`, `Light`, `None`, `Wood` | `Aircraft`, `Brick`, `Tree` |
| Crystallized Nexus | 13 | `Heavy`, `Light`, `None` | `Aircraft`, `Building`, `Cyborg`, `Flora`, `Infantry`, `Medium`, `Shield`, `Stability`, `Superheavy`, `Vehicle` |
| Generals Alpha | 37 | `Concrete`, `Heavy`, `Light`, `None`, `Wood` | `aircraft.chinook`, `aircraft.comanche`, `aircraft.comanche.countermeasures`, `aircraft.normal`, `aircraft.normal.countermeasures`, `aircraft.spectre`, `aircraft.spectre.countermeasures`, `building.defense`, `building.internet_center`, `building.normal` _+22 more_ |
| OpenE2140 | 4 | ΓÇö | `aircraft`, `building`, `infantry`, `vehicle` |
| OpenHV | 6 | `Concrete`, `Heavy`, `Light`, `None`, `Wood` | `Steel` |
| OpenRA Dune 2000 | 15 | `Concrete`, `Heavy`, `Light`, `None`, `Wood` | `building`, `concrete`, `cy`, `harvester`, `heavy`, `invulnerable`, `light`, `none`, `wall`, `wood` |
| OpenRA Dune II | 0 | ΓÇö | ΓÇö |
| OpenRA Red Alert | 6 | `Concrete`, `Heavy`, `Light`, `None`, `Wood` | `Tree` |
| OpenRA Tiberian Dawn | 5 | `Concrete`, `Heavy`, `Light`, `None`, `Wood` | ΓÇö |
| OpenRA Tiberian Sun | 5 | `Concrete`, `Heavy`, `Light`, `None`, `Wood` | ΓÇö |
| Romanov's Vengeance | 11 | `Concrete`, `Heavy`, `Light`, `None`, `Wood` | `Drone`, `Flak`, `Medium`, `Plate`, `Rocket`, `Steel` |
| Shattered Paradise | 14 | `Concrete`, `Heavy`, `Light` | `Aircraft`, `Boss`, `Building`, `BuildingArmor`, `ConcreteArmor`, `Defense`, `DefenseArmor`, `Infantry`, `InfantryArmor`, `Shield` _+1 more_ |
| Valiant Shades | 13 | `Concrete`, `Heavy`, `Light`, `None`, `Wood` | `Drone`, `Flak`, `Medium`, `Mine`, `Plate`, `ResistSupers`, `Rocket`, `Steel` |

## Tag frequency across mods

| tag | mods declaring it |
|---|--:|
| `Light` | 11 |
| `Heavy` | 11 |
| `None` | 10 |
| `Concrete` | 10 |
| `Wood` | 9 |
| `Medium` | 3 |
| `Steel` | 3 |
| `Aircraft` | 3 |
| `Flak` | 2 |
| `Plate` | 2 |
| `Drone` | 2 |
| `Rocket` | 2 |
| `Tree` | 2 |
| `Infantry` | 2 |
| `Building` | 2 |
| `Shield` | 2 |
| `building` | 2 |
| `Brick` | 1 |
| `Defense` | 1 |
| `Boss` | 1 |
| `InfantryArmor` | 1 |
| `BuildingArmor` | 1 |
| `VehicleArmor` | 1 |
| `DefenseArmor` | 1 |

## What this unblocks

Part 1 of the weapon layer ΓÇö range, damage, burst, reload and raw sustained DPS ΓÇö needs none of this and is already measured. Part 2, **armor-aware effective DPS**, needs a mapping table carrying `source_tag`, `normalized_class`, `confidence` and `reason` per source. The Westwood core maps at high confidence; everything else needs a judgement, and a few sources cannot participate at all.

