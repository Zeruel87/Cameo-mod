To: Claude

> ⛔ **ARCHIVED — SUPERSEDED by [`docs/HANDOFF.md`](../../HANDOFF.md) (2026-08-23).**
> This is a dated session record, kept for provenance and for the technique notes in it.
> It is **not** current state: statuses, branch names, counts and "next steps" below were
> true on 2026-08-11 and have moved since. Never resume work from this file — read
> `docs/HANDOFF.md`, then verify against the artifact. Still useful for: the Shattered Paradise projectile/effect parity research.

From: Devin
Date: 2026-08-11
Re: Shattered Paradise TS projectile / effect parity plan + GDI Sonic conversion handoff

This is the current state of the GDI Sonic 3-way split and the deep
Shattered Paradise (SP) research needed to make all Tiberian Sun
projectiles and effects look and behave exactly like SP.

## 1. What Devin completed today

- Engine resynced to `26cab57a7e628a2e14c226a7fd04b7d2b49eed40` (was stale).
- `tools/audit/find_mechanical_phase_a.py` audit tool committed.
- `Tesla_ExtraDamage` and `AreaDamage` `ValidRelationships` cleanups committed.
- `TSVulcanGunSonic` converted to `Bullet_Medium + Sonic_Medium` with new
  `^Projectile_Sonic_Shell` / `^Effect_Sonic_Shell` templates.
- `TSAssaultCannonTalSonic` converted to child of `TSAssaultCannonTal` +
  `Sonic_Medium`.
- `TSAssaultCannonSonic` converted to `Flak_Medium + Sonic_Medium`.
  Then fixed to use `^Projectile_Sonic_Shell` / `^Effect_Sonic_Shell` so it
  keeps the original `TSSonicGrenade` BOMB shell look.
- `TSHellfireSonic` and `TSZoneHellfireSonic` converted to Missile + Sonic
  using new TS-specific projectile templates.
- Added shared `^Projectile_TS_Missile_Medium` and `^Projectile_TS_Missile_Heavy`
  templates in `mods/cameo/weapons/tiberiansun.yaml`.
- Added `ts_small_smoke_trail` and `ts_large_smoke_trail` sequences pointing at
  the existing `tssmokey2.shp` and `smokey.shp` assets.

All changes were boot-gated (menu reached, no new exceptions) and ledgers
re-extracted / 0 drift.

## 2. Current todo (in priority order)

1. Convert remaining GDI Sonic weapons one by one:
   - `TSBombSonic` — Demolition_Heavy + Sonic_Heavy
   - `KodiakCannonSonic` — CannonHE_Heavy + Sonic_Heavy
   - `TSSonicZapWeaponSonic` — only Sonic_Heavy
   - `TSGrenadeSonic` — Concussion_Light + Sonic_Light
2. Add TS projectile/effect/sequence aliases so the whole TS arsenal matches
   SP looks and behavior as closely as possible (see research below).
3. Re-verify every converted weapon with `tools/audit/review_resolve_diff.py`.

## 3. Design decisions the maintainer already made

- `TSVulcanGunSonic` and `TSAssaultCannonSonic/TalSonic` use the Sonic shell
  projectile/effect template, not the old `^TSSonicGrenade` full-stack.
- `TSHellfireSonic` (normal Orca) uses `Sonic_Medium`.
- `TSZoneHellfireSonic` (Zone Orca) uses `Sonic_Heavy`.
- `TSBombSonic` uses `Demolition_Heavy + Sonic_Heavy`.
- `KodiakCannonSonic` uses `CannonHE_Heavy + Sonic_Heavy`.
- `TSSonicZapWeaponSonic` uses only `Sonic_Heavy`.
- `TSGrenadeSonic` uses `Concussion_Light + Sonic_Light`.
- Damage values are chosen by the user per weapon and must not be hand-edited
  in the ledger — use `extract_stats.py` + ledger round-trip.

## 4. Deep Shattered Paradise research results

SP's Tiberian Sun engine has a clear default set of projectiles, explosions,
and smoke effects. Cameo already owns many of the TS assets, but under
`ts`/`tss`/`tst` prefixes. To make weapons reference the same SP names, add
sequence aliases to `mods/cameo/sequences/misc.yaml`.

### 4.1 TS projectiles already present in Cameo bits

| SP/TS name | Cameo asset | What it is |
|------------|-------------|------------|
| `DRAGON` | `dragon.shp` | TS rocket/missile projectile |
| `120mm` | `120mm.shp` | Artillery / tank shell |
| `DISCUS` | `tsdiscus.shp` | Disc grenade |
| `FLAMEALL` | `tsflameall.shp` | Flamethrower stream image |
| `TORPEDO` | `tstorpedo.shp` | Sub / naval torpedo |

### 4.2 TS smoke trails

| SP/TS name | Cameo asset | Proposed alias |
|------------|-------------|----------------|
| `small_smoke_trail` | `tssmokey2.shp` | `ts_small_smoke_trail` ✓ already added |
| `large_smoke_trail` | `smokey.shp` | `ts_large_smoke_trail` ✓ already added |

### 4.3 TS explosions already present in Cameo (with prefixes)

Cameo already has these .shp files; they should be exposed under the
SP/TS standard names with a `ts_` prefix so 3-way split effect templates
and weapons can reference them consistently:

| SP/TS effect name | Cameo asset | Proposed `ts_*` alias |
|-------------------|-------------|-----------------------|
| `s_clsn16` (tiny_clsn) | `tss_clsn16.shp` | `ts_tiny_clsn` |
| `s_clsn22` (small_clsn) | `tss_clsn22.shp` | `ts_small_clsn` |
| `s_clsn30` (medium_clsn) | `tss_clsn30.shp` | `ts_medium_clsn` |
| `s_clsn42` (large_clsn) | `tss_clsn42.shp` | `ts_large_clsn` |
| `s_clsn58` (verylarge_clsn) | `tss_clsn58.shp` | `ts_verylarge_clsn` |
| `twlt026` (tiny_twlt) | `tstwlt026.shp` | `ts_tiny_twlt` |
| `twlt036` (small_twlt) | `tstwlt036.shp` | `ts_small_twlt` |
| `twlt050` (medium_twlt) | `tstwlt050.shp` | `ts_medium_twlt` |
| `twlt070` (large_twlt) | `tstwlt070.shp` | `ts_large_twlt` |
| `twlt100` (verylarge_twlt) | `tstwlt100.shp` | `ts_verylarge_twlt` |
| `explosml` (small_explosion) | `tsexplosml.shp` | `ts_small_explosion` |
| `explomed` (medium_explosion) | `tsexplomed.shp` | `ts_medium_explosion` |
| `explolrg` (large_explosion) | `tsexplolrg.shp` | `ts_large_explosion` |
| `s_bang16` (tiny_bang) | `tss_bang16.shp` | `ts_tiny_bang` |
| `s_bang24` (small_bang) | `tss_bang24.shp` | `ts_small_bang` |
| `s_bang34` (medium_bang) | `tss_bang34.shp` | `ts_medium_bang` |
| `s_bang48` (large_bang) | `tss_bang48.shp` | `ts_large_bang` |
| `s_brnl20` (tiny_brnl) | `tss_brnl20.shp` | `ts_tiny_brnl` |
| `s_brnl30` (small_brnl) | `tss_brnl30.shp` | `ts_small_brnl` |
| `s_brnl40` (medium_brnl) | `tss_brnl40.shp` | `ts_medium_brnl` |
| `s_brnl58` (large_brnl) | `tss_brnl58.shp` | `ts_large_brnl` |
| `s_tumu22` (tiny_tumu) | `tss_tumu22.shp` | `ts_tiny_tumu` |
| `s_tumu30` (small_tumu) | `tss_tumu30.shp` | `ts_small_tumu` |
| `s_tumu42` (medium_tumu) | `tss_tumu42.shp` | `ts_medium_tumu` |
| `s_tumu60` (large_tumu) | `tss_tumu60.shp` | `ts_large_tumu` |

### 4.4 TS effects NOT in Cameo bits (need real files)

These .shp/.png files are not in `mods/cameo` and must come from the base
Tiberian Sun game install or new art:

- `smokey2.shp` (Cameo has `tssmokey2.shp` instead)
- `cannonball.shp` / `cannonsmokecircle.shp`
- `greenplasma2.shp`
- `clusterbomb.shp`
- `sparks.shp`, `sparks2.shp`, `sparks3.shp`
- `litning.shp`
- `piff.shp`, `piffpiff.shp`, `w_piff.shp`
- `h2o_exp1.shp`, `h2o_exp2.shp`
- `xgrysml2.shp`, `xgrymed1.shp`, `xgrymed2.shp`
- `sgrysmk1.shp`, `lgrysmk1.shp`
- `dbrissm.shp`, `dbrislg.shp`
- `canister.shp`, `pulsball.shp`

For now we can only use what Cameo already has.

## 5. Concrete instructions for Claude

### A. Remaining Sonic weapon conversions

Convert one weapon per commit with this checklist:

1. Read the current block and the non-Sonic parent it is based on.
2. Replace with the user's chosen base + Sonic tier from Section 3.
3. Preserve `ReloadDelay`, `Burst`, `BurstDelays`, `Range`, `Report`, and
   any custom `Projectile` fields. When in doubt, `review_resolve_diff.py`.
4. Use `^Projectile_*` and `^Effect_*` templates. If the old visual came from
   `^TSSonicGrenade`, use `^Projectile_Sonic_Shell` / `^Effect_Sonic_Shell`.
5. Run:
   - `python tools/audit/find_empty_warhead.py` (must be 0)
   - `python tools/audit/find_orphan_old_keys.py` (0 real orphans)
   - `python tools/balance/extract_stats.py` then `... --check` (0 drift)
   - `launch-game.cmd` to main menu, no new exceptions.
6. Scoped `git add`: only the affected `*weapons.yaml` and the one
   `docs/balance/tiberiansun_gdi.json` ledger.
7. Commit with Devin attribution (not Claude attribution).

### B. Apply the SP parity sequence aliases

Add all aliases from Section 4.3 to `mods/cameo/sequences/misc.yaml` in one
block under the smoke trails, then boot-gate. This is purely additive, no
balance numbers, and does not require ledger changes unless a weapon is
updated to use the new names.

Suggested format for each alias (match the existing `ts_small_smoke_trail`
style):

```yaml
ts_small_clsn:
	idle:
		Filename: tss_clsn22.shp
		Length: *
		ZOffset: 1023
```

Use `tools/audit/find_empty_warhead.py` and `launch-game.cmd` to verify.

### C. Update TS effect templates to use the new `ts_*` names

After the aliases exist, update `^Effect_Sonic_Light`, `^Effect_Sonic_Medium`,
`^Effect_Sonic_Heavy`, `^Effect_Bullet_*`, `^Effect_Concussion_*`,
`^Effect_CannonHE_*`, `^Effect_Demolition_*`, `^Effect_MissileAP_*`,
`^Effect_MissileHE_*`, etc., so their `Explosions:` and `ImpactSounds:` match
SP where possible. Take each `CreateEffect` warhead in SP's
`weapondefaults.yaml`, `explodefaults.yaml`, and `explosions.yaml` and map the
Cameo equivalent.

### D. Long-term SP parity

- For every TS weapon that uses a `Projectile: Missile`, use
  `^Projectile_TS_Missile_Medium` / `Heavy`.
- For every TS shell, use `Image: 120mm` and the correct `Contrail` settings.
- For every TS grenade/disc, use `Image: tsdiscus`.
- For TS flamers, use `Image: tsflameall`.
- Replace `TrailImage: smokey` in TS weapons with `ts_small_smoke_trail` or
  `ts_large_smoke_trail` depending on SP research.
- Update `^Warhead_*` templates to use `ts_*` explosion names for the correct
  visual class (clsn, twlt, bang, brnl, tumu, explosion, etc.).

## 6. Verification always required

- `find_empty_warhead.py = 0`
- `find_orphan_old_keys.py = 0 real orphans`
- `extract_stats.py --check = 0 drifted`
- `launch-game.cmd` reaches `MenuPostProcessEffect.PostWorldLoaded` and
  produces no new `exception-*.log`.

## 7. Files to avoid touching

- Do not `git add -A` / `git add .`.
- Do not stage generated `docs/audit/latest/*` reports or scratch scripts.
- Do not commit `CameoMod.sln` or `mod.config` unless an engine update was
  intentional.

Current branch: `master`
Next safe commits expected:
- `TSBombSonic` Demolition + Sonic Heavy
- `KodiakCannonSonic` CannonHE + Sonic Heavy
- `TSSonicZapWeaponSonic` only Sonic Heavy
- `TSGrenadeSonic` Concussion + Sonic Light
- Bulk `ts_*` sequence aliases for SP parity

Generated by Devin AI
