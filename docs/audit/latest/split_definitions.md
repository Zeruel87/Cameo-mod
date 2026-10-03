# Split definitions — one weapon, two live files, one silent merge

Live weapon files in the manifest: **48** · names defined more than once: **2**

The engine MERGES same-named top-level nodes across files. Editing one copy leaves the other supplying its own fields, so a removal can silently do nothing — see the `HMG` incident in this file's docstring.

| bucket | count | baseline |
|---|--:|--:|
| S1 legacy global + ContentPack | 0 | 56 |
| S2 same tier twice | 2 | 2 |


## S1 — defined in a legacy global AND a ContentPack (0)

ContentPack-migration residue. **Fix by deleting the LEGACY copy** once the pack copy is complete — never by editing both, which is how the two drift apart. ⚠ Check `mod.yaml` load order before deleting: if the global loads LATER it is the one whose fields win today, so a naive delete changes behaviour. Diff the resolved weapon before and after with `tools/audit/review_resolve_diff.py`.

_none found_


## S2 — defined twice within the same tier (2)

| weapon | defined at |
|---|---|
| `Flamethrower` | `weapons/tiberiandawn.yaml:168` · `weapons/starcraft.yaml:1` |
| `Sound2` | `ContentPacks/D2k/Ordos/yaml/weapons.yaml:4864` · `ContentPacks/D2k/Atreides/yaml/weapons.yaml:15` |


_at or below baseline_ — pre-existing migration residue. **Lower `S1_BASELINE`/`S2_BASELINE` as duplicates are deleted; never raise them.**
