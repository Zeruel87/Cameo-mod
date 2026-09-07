# Split definitions — one weapon, two live files, one silent merge

Live weapon files in the manifest: **40** · names defined more than once: **26**

The engine MERGES same-named top-level nodes across files. Editing one copy leaves the other supplying its own fields, so a removal can silently do nothing — see the `HMG` incident in this file's docstring.

| bucket | count | baseline |
|---|--:|--:|
| S1 legacy global + ContentPack | 22 | 56 |
| S2 same tier twice | 4 | 2 |


## S1 — defined in a legacy global AND a ContentPack (22)

ContentPack-migration residue. **Fix by deleting the LEGACY copy** once the pack copy is complete — never by editing both, which is how the two drift apart. ⚠ Check `mod.yaml` load order before deleting: if the global loads LATER it is the one whose fields win today, so a naive delete changes behaviour. Diff the resolved weapon before and after with `tools/audit/review_resolve_diff.py`.

| weapon | defined at |
|---|---|
| `ChemTibAtomic` | `ContentPacks/RedAlert/Shared/yaml/weapons.yaml:1214` · `weapons/tiberiandawn.yaml:226` |
| `RocketsG` | `ContentPacks/RedAlert/Shared/yaml/weapons.yaml:1335` · `ContentPacks/RedAlert/Shared/yaml/weapons.yaml:1339` · `weapons/weapons.yaml:12035` |
| `SardDeath` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2495` · `weapons/d2k.yaml:1034` |
| `Sound` | `ContentPacks/D2k/Atreides/yaml/weapons.yaml:15` · `weapons/d2k.yaml:644` |
| `Sound2` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2465` · `ContentPacks/D2k/Atreides/yaml/weapons.yaml:63` · `weapons/d2k.yaml:691` |
| `WormSwallow` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2480` · `weapons/d2k.yaml:781` |
| `^D2K155mmLegacy` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2309` · `weapons/d2k.yaml:156` |
| `^OCannon` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2863` · `weapons/d2k.yaml:1856` |
| `d2k25mm` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2540` · `weapons/d2k.yaml:1231` |
| `d2kFlameTurret` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2697` · `weapons/d2k.yaml:1473` |
| `d2k_APCo_AA` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2423` · `weapons/d2k.yaml:541` |
| `d2k_APCo_AG` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2414` · `weapons/d2k.yaml:533` |
| `d2k_aircraft_eater` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2795` · `weapons/d2k.yaml:1788` |
| `d2k_airdefenseplatform` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2742` · `weapons/d2k.yaml:1765` |
| `d2k_laser_qafza` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2706` · `weapons/d2k.yaml:1691` |
| `d2k_laser_qafza_aa` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2723` · `weapons/d2k.yaml:1708` |
| `d2k_sard_crossbow` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2835` · `weapons/d2k.yaml:1828` |
| `d2k_sard_heatblade` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2814` · `weapons/d2k.yaml:1807` |
| `d2k_sardaukar_elite` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2566` · `weapons/d2k.yaml:1394` |
| `d2k_tyrant` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2351` · `weapons/d2k.yaml:494` |
| `emperor_sardaukar_chief_c4` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2692` · `weapons/d2k.yaml:1442` |
| `mtank_pri` | `ContentPacks/D2k/Shared/yaml/weapons.yaml:530` · `weapons/d2k.yaml:477` |


## S2 — defined twice within the same tier (4)

| weapon | defined at |
|---|---|
| `Flamethrower` | `weapons/tiberiandawn.yaml:72` · `weapons/starcraft.yaml:1` |
| `OrniBombC` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2491` · `ContentPacks/D2k/Atreides/yaml/weapons.yaml:89` |
| `OrniGunC` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:2586` · `ContentPacks/D2k/Atreides/yaml/weapons.yaml:151` |
| `ZClaw3` | `weapons/tiberiansun.yaml:1213` · `weapons/tiberiansun.yaml:1855` |


**FAIL** — S1 22/56, S2 4/2. A new split definition landed. Delete the duplicate rather than editing both copies.
