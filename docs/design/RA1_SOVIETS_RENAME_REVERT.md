# Revert the ra1_soviets rename — all 32 ids got WORSE

**Maintainer, 2026-09-07:** *"Why the hell would it be renamed? The name was already nice,
short and unique! Now soviets are like double in the name which should not be the case!"*

Correct. **Every one of the 32 actor renames `ad7c5e232` applied made the id longer and
worse. There is not a single improvement in the set.** This is the top naming item.

## What it did

```
buildings (9)   ra1_soviets_barracks          -> ra1_soviets_sovietbarracks
                ra1_soviets_constructionyard  -> ra1_soviets_sovietconstructionyard
                ra1_soviets_airfield / orerefinery / radardome / servicedepot /
                techcenter / warfactory / largefactory   ... all + "soviet"

infantry (5)    ra1_soviets_attackdog         -> ra1_soviets_actordogname   ⛔ a FLUENT KEY
                ra1_soviets_flamethrower      -> ra1_soviets_sovietflamethrower
                grenadier / mortarsoldier / rocketsoldier   ... all + "soviet"

vehicles (5)    ra1_soviets_heavytank         -> ra1_soviets_sovietheavytank
                mammothtank / oretruck / heavyindustrialminer /
                mobileconstructionvehicle                   ... all + "soviet"

upgrades (13)   ra1_soviets_doctrine_conscription -> ..._doctrine_conscriptiondoctrine
                ra1_soviets_upgrade_hammertank    -> ..._upgrade_hammertankupgrade
```

The upgrades are the clearest proof the rename was mechanical rather than considered:
the tech marker is **duplicated** — `doctrine_X` became `doctrine_Xdoctrine`, `upgrade_X`
became `upgrade_Xupgrade`.

## Why it happened, and why it cannot happen again

`gen_rename_maps.proposed_id` derives the name from `Tooltip/Name`. "Soviet Barracks"
slugifies to `sovietbarracks`, and the old dedupe stripped only the **slug**
(`ra1_soviets`), never the English **adjective** (`soviet`). Every Soviet building is
named "Soviet Something" in its tooltip, so every one gained a second "soviet".

**Fixed on 2026-09-06** (`c9437f4f8`, defect E): `FACTION_ADJECTIVE` now strips the
adjective too. The fixed generator proposes `ra1_soviets_airfield` — **the original
name.** So the revert target is not a judgement call: it is what the corrected tool
produces.

`ra1_soviets_actordogname` came from a different defect in the same commit — the
fluent-key guard tested `actor-` while this tree also uses `actor_`, so the dangling key
`actor_dog.name` was slugified into an id. Also fixed (defect C).

## The cost this already caused

* **7 `.oramap` files broke**, including **both shellmaps**, because they still placed the
  old ids. Repaired in `1e30a1cb9`, but a tester hit both crashes on a stale checkout —
  `No rules definition for unit ra1_soviets_barracks` and
  `... ra1_soviets_constructionyard` at `LoadShellMap`.
* **236 removal nodes** were deleted in the same commit, resurrecting cancelled warheads
  (multi-main 396 -> 461) and killing 44 tesla-arc terminators. Restored in `7b63045fd`.
* **69 of the 345 N4 "faction named twice" findings** are this one commit's doing.

## The revert — 32 ids back to their originals

1. Generate the map with the FIXED generator to scratch and read all 32 lines:
   `python tools/audit/gen_rename_maps.py --out /tmp/rev` (no `--files`).
2. Confirm each target equals the pre-`ad7c5e232` id:
   `git show ad7c5e232^:mods/cameo/ContentPacks/RedAlert/Soviets/yaml/<file>.yaml`
3. Apply with `safe_rename.py`. It updates yaml references and repacks `.oramap`
   archives — **both shellmaps are affected, so a boot gate is mandatory.**
4. ⚠ Also fix the **Tooltip** for the dog: `actor_dog.name` does not exist in
   `mods/cameo/fluent/en.ftl`, so the unit has no display name. Renaming the actor
   without fixing the tooltip lets the next generator run re-derive garbage.
5. Gates: `audit_naming_damage` (N4 should fall by ~69), `audit_map_actors` M1 = 0,
   `find_empty_warhead` 0, then the boot gate.

⛔ **Do not batch this with any other rename.** It is a revert of one commit's ids, it
touches both shellmaps, and it must be reviewable as exactly that.

## The rule this earns

**A rename that makes an id longer is a regression until proven otherwise.** The whole
point of the naming grammar is that the faction prefix carries the faction; anything that
re-states it in English is the N4 defect. `audit_naming_damage` N4 counts them — a rename
batch that raises N4 has failed, no matter what the compliance percentage says.
