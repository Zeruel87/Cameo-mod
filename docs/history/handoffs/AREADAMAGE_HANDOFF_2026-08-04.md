# AreaDamage universal conversion — AGENT HANDOFF (2026-08-04)

> ⛔ **ARCHIVED — SUPERSEDED by [`docs/HANDOFF.md`](../../HANDOFF.md) (2026-08-23).**
> This is a dated session record, kept for provenance and for the technique notes in it.
> It is **not** current state: statuses, branch names, counts and "next steps" below were
> true on 2026-08-04 and have moved since. Never resume work from this file — read
> `docs/HANDOFF.md`, then verify against the artifact. Its conversion work is COMPLETE. Still useful for: the C# build/deploy gotchas (§1, §5) and the design rationale.

> **✅ HISTORICAL — this handoff's work is COMPLETE (as of 2026-08-08).** The universal AreaDamage
> conversion, both C# warheads, the generator reconcile (A1), the MissileAA spread reduction, and the
> energy-chip rework are all DONE and merged to `master` (the `fix/production-queue-crash` branch +
> `48245737e` references below are stale — we are well past them). Keep this doc for the C# build/deploy
> gotchas (§1, §5) and the design rationale, but for **remaining** work and current status read
> **`BALANCE_MEGAPLAN.md` §1 + §12** (the live phase-map) and `ROADMAP.md` (the live queue). Do NOT
> treat §0/§2/§3/§7 below as current state.

Written by Claude (Opus 4.8) at a token/weekly limit, mid-operation. Another agent
continues from here. **Read this top-to-bottom before touching anything.** Then read
the memory index + `docs/design/AREADAMAGE_WARHEAD_REBALANCE.md` (the full design).

---

## 0. TL;DR — exactly where we are

- **Branch:** `fix/production-queue-crash`. **Last commit `48245737e`** (generator reconcile +
  sync guard). **The tree BOOTS to a stable menu** (`MenuPostProcessEffect.PostWorldLoaded`, alive
  25s+ past load, no new exception log).
- **The C# is DONE** (both warheads built, deployed, boot-proven in-game via AtomicCore).
- **The UNIVERSAL CONVERSION IS DONE + COMMITTED + BOOTS** (2026-08-04): sweep `3dac92ee8`
  (559 weapons), 54-template flip `b2fbc372f`. EVERY live weapon main is now `AreaDamage` with
  universal baked FF (`Ally, Neutral, Enemy` + `FriendlyFireDamage/Spread 50`); all `_FriendlyFire`
  twins retired (0 left); `^Warhead_Nuclear_Super` preserved. Pipeline audits recognize AreaDamage
  (`7b62a5414`). Empty-warhead guard is in `run_all.sh` (`b6a58b76d`).
- **✅ GENERATOR DRIFT — RESOLVED (`48245737e`).** `tools/balance/gen_weapon_template.py` now emits
  `AreaDamage` mains + baked universal FF + `^Warhead_<Family>_<Level>` naming + `Warhead@<tag>_Percentage`,
  drops the `_FriendlyFire` twin, and excludes hand-tuned `^Warhead_Nuclear_Super` (`HAND_TUNED`).
  New guard `tools/balance/verify_generator_sync.py` (wired into `run_all.sh` as `gen_sync`) regenerates
  the families and diffs them block-for-block against `weapons.yaml`: **drift = 0** across all 54 shared
  templates → **a regenerate+splice is now a verified no-op** (safe to regenerate). Section 3c is DONE.
- **✅ MissileAA spread reduction** — applied per-family `spreads` override in
  `tools/balance/gen_weapon_template.py` (`MissileAA`: Light=200, Medium=300, Heavy=400),
  regenerated the `^Warhead_MissileAA_*` blocks, spliced them into `mods/cameo/weapons/weapons.yaml`,
  `verify_generator_sync.py` reports drift = 0, and the game boot-gates to menu.
  **NEXT (remaining):** balance items (Section 6 / `BALANCE_MEGAPLAN.md` Phases A2→G).
  Old design docs (§2/§7 below) describe the pre-conversion plan — treat §0 as truth.
- **⚠ Two PRE-EXISTING content issues surfaced by `--check-yaml` (NOT from warhead work, non-blocking —
  the game still boots):** `mammothbunker.husk` missing `ArmamentInfo` (its `WithSpriteTurret` needs an
  `Armament`); `rules.yaml:8 ShortGameEnabled` no longer exists on `MapOptions` (engine drift); plus
  benign voice-set gaps (Move/Guard/Action) and a `DeliversCash`/`Valued` unresolved. Flag to maintainer.
- **⚠ First game launch of a cold session threw a logless post-menu "fatal error" ~18s in (voxel sheet
  overflow on the busy menu shellmap); the SECOND launch reached a stable menu.** Intermittent runtime/
  render issue, not a content crash — if a boot gate "crashes" post-menu with no exception log, relaunch.
- **⚠ The maintainer has ~73 files of unrelated uncommitted WIP** (faction rebalances, docs,
  CLAUDE.md, harvester tool, `noid_resolved.json`). **NEVER `git add -A`. Scoped adds only.**

---

## 1. The two warheads (DONE — committed `851537a03` + `1b638bf28`)

MOD code at the **repo root** (`OpenRA.Mods.Cameo/`, NOT the `engine/` submodule):
- `OpenRA.Mods.Cameo/Warheads/AreaDamageWarhead.cs` — `SpreadDamage` + expanding rings/DoT
  + **baked friendly fire**. Fields: `Spread`, `Falloff[]`, `Range[]`, `DamageCalculationType`,
  `Ticks`(1), `TickDelay`(0), `MinRadius`/`MaxRadius`(0), `FriendlyFireDamage`(50),
  `FriendlyFireSpread`(50), `TickDamage[]`. **At defaults (Ticks 1, MaxRadius 0) it is
  byte-behaviour-identical to SpreadDamage + baked FF** — so it is a safe universal main type.
- `OpenRA.Mods.Cameo/Warheads/AreaDamagePercentageWarhead.cs` — 1-method subclass; deals
  **% of max HP** (like HealthPercentageDamage). Its `Falloff` replaces a whole STACK of
  concentric HealthPercentageDamage rings.

**KEY MATH (memorise): the impact center is inside every tick's radius, so**
`center damage = authored Damage × Versus/100`, **independent of ring geometry.** That is how
AtomicCore hits exactly 75% of a 1,000,000-HP Concrete CY: flat `Damage 500000 × Concrete 100/100 =
500k` + `% Damage 25 → 25% × 100/100 = 250k` = 750k. (The weapon sets only `Damage` + `MaxRadius`;
falloff/ticks/25%/Versus live in `^Warhead_Nuclear_Super`.)

**Build + deploy (see memory `cameo-dll-deploy-engine-bin` — this cost hours):**
```
DOTNET_ROLL_FORWARD=LatestMajor dotnet build -c Release --nologo -p:TargetPlatform=win-x64
```
outputs to **`engine/bin`** (what the running `engine/bin/OpenRA.exe` LOADS; gitignored). Then
**also copy** to the git-TRACKED `mods/cameo/OpenRA.Mods.Cameo.dll` (it does NOT auto-update; it was
a month stale). A new warhead only truly runs when a **concrete** weapon instantiates it — abstract
`^Template`s are skipped at boot, so a "pilot template booted" is a FALSE pass.

---

## 2. Design decisions (LOCKED by maintainer)

- **UNIVERSAL friendly fire:** every template main = AreaDamage with `FriendlyFireDamage: 50` +
  `FriendlyFireSpread: 50` (50% dmg within 50% radius vs allies), INCLUDING precise/energy/AA and
  aircraft AA missiles. `ValidRelationships` opens to `Ally, Neutral, Enemy` so FF can see allies.
- **`_Percentage` twin stays `HealthPercentageDamage`** (own per-template Versus) EXCEPT the Nuclear
  template, whose `_Percentage` is now **`AreaDamagePercentage`** (maintainer request).
- **`_FriendlyFire` twin is DELETED everywhere** (folded into the main's baked FF).
- **`_ExtraDamage` stays `SpreadDamage`** (bespoke). Energy chips get repurposed ladders later
  (Section 7 / doc §3).
- **Nuclear template shape (already committed):** flat + % are BOTH `Ticks 10`, `Falloff
  100,90,…,10`, sharing the SAME 16-armor Versus order (Concrete 100 … None 55, Shield 155).
  Reduce MissileAA spread when regenerating (tighter than 400/600/800).

---

## 3. NEXT STEPS — the universal conversion (do in this order, boot-gate each ★)

### 3a. Typos — DONE (uncommitted)
Fixed the 2 duplicate `Warhead@MissileAP_Medium` keys (→ `_Percentage`) in
`ContentPacks/RedAlert2Mod/TKM/yaml/weapons.yaml` (HueyMissiles) and
`.../AsianAlliance/yaml/weapons.yaml` (AsianHarbingerPlasma).

### 3b. Apply the resolution-aware sweep (weapons)
```
python tools/balance/sweep_areadamage.py            # dry-run: 637 class2, 156 class3, 11 class2d, 3 class1
python tools/balance/sweep_areadamage.py --apply     # writes 37 live weapon files
python tools/audit/find_empty_warhead.py             # MUST print 0
```
This strips ` SpreadDamage`→bare from 637 main overrides, deletes 156 `_FriendlyFire` twin blocks +
3 removal nodes, strips 11 restated `ValidRelationships: Neutral, Enemy`. It is RESOLUTION-AWARE
(only touches keys a weapon actually inherits from a `^Warhead_*` template; it verified 0 surprises).
**★ boot-gate** (templates are still SpreadDamage here → bare mains inherit SpreadDamage; this
intermediate state BOOTS. Confirms the sweep alone is clean.)

### 3c. Convert the 54 non-Nuclear templates → AreaDamage
Update `tools/balance/gen_weapon_template.py` (`family()` + emitters):
1. main warhead: `SpreadDamage` → `AreaDamage`.
2. `ValidRelationships: Neutral, Enemy` → `Ally, Neutral, Enemy` on the main.
3. add `FriendlyFireDamage: 50` + `FriendlyFireSpread: 50` on the main.
4. DELETE the FF twin emission (the `aoe`/`ff_wh` block) entirely.
5. naming fix (generator is STALE vs file): emit `^Warhead_{tag}` (not `^{tag}`) and
   `Warhead@{tag}_Percentage` (not `Warhead@{tag}Percentage`).
6. reduce the `MissileAA` family spread (per-family override, ~250/350/450).

Then regenerate and **splice ONLY the pre-Nuclear region**:
- The 55 templates live in `mods/cameo/weapons/weapons.yaml` from `^Warhead_Bullet_Light:`
  (~line 3252) to the end of `^Warhead_Nuclear_Super_Percentage` (~6819). **`^Warhead_Nuclear_Super`
  is LAST (~6755–6819) and is HAND-TUNED — do NOT regenerate/overwrite it.**
- Replace only `^Warhead_Bullet_Light` … just-before `^Warhead_Nuclear_Super` with the regenerated
  54 templates (take the generator output up to but excluding `^Warhead_Nuclear_Super:`).
- Spot-check one template diff (e.g. `^Warhead_Bullet_Light`) = only the intended type/FF/naming
  changes.
- `python tools/audit/find_empty_warhead.py` → **0**. **★ boot-gate.**

### 3d. Commit
Scoped: `git add tools/balance/gen_weapon_template.py mods/cameo/weapons/weapons.yaml <the 37 swept
weapon files> tools/balance/sweep_areadamage.py tools/audit/find_empty_warhead.py
docs/design/AREADAMAGE_HANDOFF.md docs/design/AREADAMAGE_WARHEAD_REBALANCE.md`. **NEVER `-A`.**
Commit message ends with your OWN `Co-Authored-By:` trailer carrying your REAL model name
(CLAUDE.md rule 10) — do not copy the literal from this file or from an older commit.

### 3e. Pipeline recognition — DONE (this checkpoint)
`formula._is_main_spread` + `audit_warhead_split.classify_warheads` now accept `AreaDamage` as a
damage main alongside `SpreadDamage` (2-line gate changes; `python tools/balance/formula.py`
self-test passes). `_Percentage`/`_ExtraDamage`/`_FriendlyFire` handling is SUFFIX-based so it
already works; `AreaDamagePercentage` is correctly ignored by the audit (like HealthPercentageDamage).
**STILL TODO:** add `python tools/audit/find_empty_warhead.py` to `tools/audit/run_all.sh` (fail on
>0) so the empty-warhead guard runs with the suite, and confirm `audit_balance_drift` still reads the
AreaDamage `Damage` correctly after the conversion.

---

## 4. Scripts (now in the repo — were in an ephemeral scratchpad)

- **`tools/audit/find_empty_warhead.py`** — resolves every LIVE weapon's full inheritance across
  the 37 live weapon files; lists any weapon whose final `Warhead@X` type is EMPTY (0 = safe).
  **RUN AFTER ANY TEMPLATE WARHEAD DELETION/RENAME.** It names the weapon the boot stack won't
  (see the crash class in memory `cameo-empty-warhead-crash`). Promote to `run_all.sh`.
- **`tools/balance/sweep_areadamage.py`** — the resolution-aware sweep. Dry-run by default,
  `--apply` to write. Resolves the PROVIDES graph so it only touches `^Warhead_*`-inherited keys
  (skips local explosion templates, standalone twins like Napalm_Crate, condition warheads).

---

## 5. GOTCHAS (each one cost real time — do not relearn)

1. **The loaded DLL is `engine/bin`, not the tracked `mods/cameo` copy.** Rebuild → engine/bin; copy
   to mods/cameo for the commit. (memory `cameo-dll-deploy-engine-bin`)
2. **Empty-type warhead = boot NRE with no weapon name in the stack.** Deleting `Warhead@X` from a
   `^template` orphans child BARE `Warhead@X:` overrides → engine builds the abstract `Warhead` →
   `NullReferenceException in ObjectCreator.CreateBasic`. Guard = `find_empty_warhead.py`.
   (memory `cameo-empty-warhead-crash`) — this is what crashed the AtomicCore work; fixed RA2Atomic.
3. **`check-yaml` reproduces LoadDefaults crashes FAST without a full boot:**
   `MOD_SEARCH_PATHS=./mods,engine/mods ENGINE_DIR=.. DOTNET_ROLL_FORWARD=LatestMajor
   engine/bin/OpenRA.Utility.exe cameo --check-yaml`. (It then times out on exhaustive actor/map
   lint — the "consumes conditions not granted" errors are pre-existing noise, not boot blockers.)
4. **Restating a main override as a DIFFERENT concrete type** (e.g. `Warhead@X: HealthPercentageDamage`
   while the template is AreaDamage) merges AreaDamage-only fields onto it → FieldLoader crash. The
   sweep flags these as "surprise" and skips them; handle manually. (Both current surprises were the
   duplicate-key typos, now fixed.)
5. **weapons.yaml has a UTF-8 BOM** (maintainer edit) + is LF. Scripts here preserve both. Never write
   yaml/reports with PowerShell `>` (UTF-16 hazard, memory `cameo-powershell-utf16-hazard`).
6. **BOOT GATE is absolute** (memory `cameo-launch-before-commit`): snapshot `%APPDATA%/OpenRA/Logs/
   exception-*.log` + a cutoff time BEFORE launching; `.\launch-game.cmd`; PASS = fresh `perf.log`
   ends with `MenuPostProcessEffect.PostWorldLoaded` AND no exception newer than the cutoff; then
   `Stop-Process -Name OpenRA -Force`. Rebuild C# first only if C# changed.

---

## 6. Balance pipeline (the maintainer's sanctioned loop — DO NOT hand-edit numbers)

Full spec: `docs/design/BALANCE_PIPELINE.md` + `docs/design/FORMULA_V2.md` (read FIRST). Never
hand-edit a balance number in yaml; `audit_balance_drift` (in `run_all.sh`) fails red when yaml and
the committed ledger disagree.
1. `python tools/balance/extract_stats.py` — refresh the ledger (`docs/balance/*.json`).
2. Edit the ledger, or the workbench (`tools/balance/build_workbook.py` → xlsx → edit input cells →
   `import_workbook.py`).
3. `python tools/balance/apply_balance.py --faction X --confirm` (dry-run without `--confirm`;
   **maintainer order required for `--confirm`**).
4. `extract_stats.py` again, run `tools/audit/run_all.sh` + BOOT GATE, commit yaml+ledger together.

**Balance work still OPEN (from `docs/design/AREADAMAGE_WARHEAD_REBALANCE.md` + memory index):**
- Spread pricing term (diminishing returns, expected-targets model) + overall spread reduction.
- Projectile-speed / tank-shell rules (regular tank speed=maxRange/10 CannonHE 2×spread; TD +
  cannon-turret speed=maxRange/5 CannonAP small spread; hybrid 50/50 CannonAP+HE speed=maxRange/10×1.5).
- Energy `_ExtraDamage` chips repurposed with LOCKED ladders (doc §3): Laser=anti-infantry, Railgun=
  anti-building+superheavy (Concrete 200>Steel 175>Wood 150, Shield 10), Tesla=anti-inf+shield keep,
  Prism/Magic=none; thin the energy main Spread ~800→150.
- Epic vehicle template rework (mirror epic AIR template: template only adds build-limit/speed/
  commando decoration, no unit type/armor; e.g. Chrono Tank = fire-support template + epic template).
- 13-class vehicle anchors restat + `fit_class` + `apply_balance --confirm` (needs cannon/weapon
  rebuild first). See memory `cameo-anchor-definition`.

---

## 7. Superweapon note the maintainer must decide
The `Damage 500000` + `MaxRadius 10000` sit on the **`^AtomicCore` template**, so EVERY nuke that
inherits it (in-game `Atomic`, `RA2Atomic`, plus TD/RA2Mod/RA1 nuke-silo weapons) is now a 75%-CY
superweapon. If only one weapon should be that strong, move `Damage`/`MaxRadius` onto the concrete
`Atomic`/`RA2Atomic` instead. (`^AtomicCore` is abstract; the real weapons are `Atomic`/`RA2Atomic`.)

---

## 8. Uncommitted state at handoff (so you can tell mine from the maintainer's)
- **MINE, safe, part of this work (commit with the conversion):** the 2 typo files
  (`RedAlert2Mod/TKM/yaml/weapons.yaml`, `RedAlert2Mod/AsianAlliance/yaml/weapons.yaml`),
  `tools/balance/sweep_areadamage.py`, `tools/audit/find_empty_warhead.py`, this doc.
- **MAINTAINER WIP — DO NOT COMMIT/REVERT:** ~73 files incl. faction infantry/vehicle/naval yaml
  across a dozen factions, `docs/*.md`, `CLAUDE.md`, `.gitignore`, `mods/cameo/rules/*.yaml`,
  `tools/balance/harvester_table.py` + its outputs, `noid_resolved.json`. Also small maintainer
  edits ride inside `weapons.yaml` (a BOM on line 1) and `RedAlert2/{Allies,Shared}/…/weapons.yaml`
  (a MirageGun `Warhead@EffectWater` removal) — those bundle unavoidably when you commit those files.

---

## 9. Cross-agent handoff protocol
Handoff docs live in `docs/design/` (`AREADAMAGE_HANDOFF.md`). The `~/.claude/.../memory/` index
(loaded every session) points here. When resuming: read the memory index, then this doc, then
`AREADAMAGE_WARHEAD_REBALANCE.md`. Leave your own handoff here when you stop; note the last commit
hash + the exact resume step. **Verify the other agent's changes on return** (diff review + boot gate).
