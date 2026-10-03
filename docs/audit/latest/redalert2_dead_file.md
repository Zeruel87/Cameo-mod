# Dead-file audit: central `weapons/*.yaml` scanned by `phase_b_survey` but not loaded

Generated: 2026-08-25 (Devin, zero-collision audit — no weapon yaml or shared
counter file was modified to produce this).

## Finding

Two files in the `CENTRAL` list (`tools/audit/weapon_families.py`) are **not
loaded by `mods/cameo/mod.yaml`**, so every weapon defined in them is dead code
and the live version ships from a ContentPack file. `phase_b_survey.py` scans
them anyway (it uses `weapon_files()` + a regex line-parser, not the resolver),
so its report lists dead copies and points W24 agents at the wrong file.

### 1. `mods/cameo/weapons/redalert2.yaml` — 162 weapons, DEAD

- `mods/cameo/mod.yaml` line 306:
  `# cameo|weapons/redalert2.yaml  # migrated to ContentPacks/RedAlert2/Shared`
  — commented out of the `Weapons:` list with an explicit migration note.
- Resolver check (`miniyaml.Ruleset('.').resolve_weapon`): **all 162** top-level
  weapons resolve to
  `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml`; **0** resolve
  back to `redalert2.yaml`.
- File size 79,807 bytes.

### 2. `mods/cameo/weapons/missiles.yaml` — 25 weapons, DEAD

- Absent from the `mods/cameo/mod.yaml` `Weapons:` list entirely (not even
  commented).
- Resolver check: weapons resolve to
  `mods/cameo/ContentPacks/TiberianDawn/Nod/yaml/weapons.yaml` and
  `mods/cameo/weapons/tiberiandawn.yaml`; **0** resolve back to `missiles.yaml`.
- File size 11,781 bytes.

### Live central weapons files (for contrast — do NOT mark dead)

Uncommented in `mod.yaml` `Weapons:` (lines 302–339): `weapons.yaml`,
`tiberiandawn.yaml`, `redalert2mod.yaml`, `d2k.yaml`, `starcraft.yaml`,
`warcraft2.yaml`, `tiberiansun.yaml`, `outpost2.yaml`. Also dead-but-not-scanned
(not in `CENTRAL`): `weapons/redalert.yaml` (line 305, migrated to
`ContentPacks/RedAlert/Shared`).

## Why this matters for the W24 burn-down

`docs/audit/latest/phase_b_survey.md` lists weapons with
`(weapons\redalert2.yaml)` as their location, e.g. `RA2CRM60H`, `RA2SCUD`,
`RA2MultiHoverMissile`. Those are the **dead copies**. The live versions are in
`ContentPacks/RedAlert2/Shared/yaml/weapons.yaml`. Converting the dead copy is
wasted work — the change does not ship. The A11 coordination note in
`DEVELOPMENT_LOG.md` flagged "several weapons are shadowed"; the truth is the
entire `redalert2.yaml` file is dead, and `missiles.yaml` is too.

## Root cause

`tools/audit/weapon_families.py` `CENTRAL` (lines 23–26) hardcodes:
`weapons/weapons.yaml, weapons/redalert2.yaml, weapons/redalert2mod.yaml,
weapons/tiberiansun.yaml, weapons/tiberiandawn.yaml, weapons/warcraft2.yaml,
weapons/missiles.yaml`. It does not consult `mod.yaml`'s `Weapons:` list, so it
keeps scanning files that were migrated to ContentPacks.

## Recommended action (needs maintainer sign-off — NOT done here)

Per CLAUDE.md / repo rules, deletes need maintainer sign-off, so this report
makes no changes. Proposed follow-up:

1. **Remove `weapons/redalert2.yaml` and `weapons/missiles.yaml` from `CENTRAL`**
   in `tools/audit/weapon_families.py` (one-line edit each) so `phase_b_survey`
   stops scanning dead files. Low risk; re-run `phase_b_survey.py` to confirm
   the dead entries disappear.
2. **Optionally delete the two dead files** (and any remaining reference) after
   `--check-yaml` + boot-gate confirm no regression. The `redalert2.yaml` header
   comment in `mod.yaml` already documents the migration.

Re-verify deadness before either step:
```sh
python -c "import sys; sys.path.insert(0,'tools/audit'); import miniyaml; \
rs=miniyaml.Ruleset('.'); \
print([k for k in ['Dragon','Rockets','RA2CRM60H'] if \
rs.resolve_weapon(k).file.replace('/','\\\\').endswith(('missiles.yaml','redalert2.yaml'))])"
```
(must print `[]`).

## Reproduce

```sh
python scratchpad/find_shadowed_ra2.py   # redalert2.yaml detail
python -c "import sys; sys.path.insert(0,'tools/audit'); import miniyaml; \
nodes=miniyaml.load('mods/cameo/weapons/missiles.yaml'); rs=miniyaml.Ruleset('.'); \
[print(n.key,'->',rs.resolve_weapon(n.key).file) for n in nodes if not n.key.startswith('^')]"
```
