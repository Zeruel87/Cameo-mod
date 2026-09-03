# AI Agent Handoff — Comprehensive Session Log

> ⛔ **ARCHIVED — SUPERSEDED by [`docs/HANDOFF.md`](../../HANDOFF.md) (2026-08-23).**
> This is a dated session record, kept for provenance and for the technique notes in it.
> It is **not** current state: statuses, branch names, counts and "next steps" below were
> true on 2026-07-25 and have moved since. Never resume work from this file — read
> `docs/HANDOFF.md`, then verify against the artifact. Still useful for: the 2026-07-24 YAML-lint incident timeline and the glossary at the end.

> **Last updated:** 2026-07-25 (session log; repository state updated 2026-07-25)
>
> **Purpose:** This document gives the next AI agent (or human contributor) a complete
> picture of everything that happened on and around 2026-07-24, so they can pick up
> where the previous agent left off without missing context. It covers what was done,
> why it was done, what other contributors did in parallel, what remains unfinished,
> and exactly how to continue.

---

## 1. Current Repository State

| Item | Value |
|---|---|
| **Branch** | `master` (feature branch `fix/ra2-weapons-migration` was merged) |
| **HEAD commit** | `aa0d8194b` — "docs(balance): finalize Dreadnought (no cloak, Pulverizer range 6000) + resume block" (balance doc updates; prior session was `388005dbb`) |
| **Master status** | Local commits ahead of `origin/master` (`18d3c43e8`) — balance doc commits not yet pushed |
| **Uncommitted changes** | None |
| **Engine pin** | `2949af84d08e2087237281c14937c2086ff6b113` (in `mod.config` → `ENGINE_VERSION`; also must be in `engine/VERSION` after `make all`) |

---

## 2. Full Timeline — Everything That Happened on 2026-07-24

### 2.1 Early Session (12:00–15:00 UTC+02:00) — AI Agent (pre-Claude Opus)

| Time | Commit | What | Why |
|---|---|---|---|
| 12:41 | `6258b2b10` | Fix cross-faction inheritance violations and document git workflow rules | V2 faction actors were inheriting from concrete actors in other factions, violating DESIGN.md §12. Also added git workflow rules to AGENT_WORKSPACE.md. |
| 15:01 | `bea61f58b` | Refactor D2K MCV production, remove ground husks, inline RMBO template, fix prerequisite references | D2K MCV production was using stale prerequisite chains. Ground husks were dead content. RMBO template was inlined for clarity. |

**Contributor commits interleaved (not by AI agent):**
- `80030028b` (Blackrobe, 20:07 +0700 = 15:07 CEST) — Extend transient notification duration (#221). UI-only change, no YAML/rules impact.
- `e57fd5a53` (Blackrobe, 20:40 +0700 = 15:40 CEST) — Add directional superweapon exposure flashes (#220). Added a new post-process effect for superweapon flashes. This is relevant because it introduced the `NuclearFlashRenderer` pattern (or a similar one) that later needed a shader file.
- `2ffb1583c` (Blackrobe, 12:16 +0700 next day = 07:16 CEST next day) — Update engine pin for audio controls. This changed the engine VERSION, which is why `make all` must be re-run if the engine directory gets reset.

### 2.2 Mid Session (15:30–17:30 UTC+02:00) — AI Agent (pre-Claude Opus)

| Time | Commit | What | Why |
|---|---|---|---|
| 15:37 | `7f704c981` | Rename dotted template names to underscores per DESIGN.md naming convention | Templates like `^ra.tank` were renamed to `^ra_tank` to comply with DESIGN.md §1 naming rules. |
| 15:38 | `45ba34048` | Update ROADMAP: mark dots-to-underscores naming task as completed | Documentation update for the above. |
| 16:23 | `3f5c53915` | Convert Warcraft 2 and Warcraft 1 inherits templates to PascalCase | Templates like `^wc2_orc_*` → `^Wc2Orc*` (or similar PascalCase form) per DESIGN.md §1. |
| 17:10 | `cf0e4485d` | Convert all remaining snake_case/camelCase inherits templates to PascalCase | Final batch of template renames across all factions. |
| 17:12 | `843a0afba` | Mark INHERITS-PASCAL task complete in roadmap | Documentation update for the above. |
| 17:20 | `236785955` | Update all docs: correct boot-gate definition and add mandatory doc-update rule | Clarified that boot-gate = launching the game and checking for exceptions, NOT just running check-yaml. Added rule that docs MUST be updated before every commit. |
| 17:22 | `41abb7bb1` | Add merge-when-done rule to git workflow documentation | Added rule: "When a task is completely done, merge the feature branch to master." |
| 17:22 | `d2ce46278` | Merge branch 'fix/v2-inheritance-violations-and-documentation' | Merged the above work to master. |
| 17:33 | `d23114b9d` | Clarify utility vs boot-gate usage and record latest check-yaml findings | Further documentation clarification. |

### 2.3 The Problematic Lint Commit (18:43 UTC+02:00) — AI Agent (pre-Claude Opus)

| Time | Commit | What | Why |
|---|---|---|---|
| 18:43 | `d42ad53a1` | **Fix YAML lint errors: LaunchAngle, UndefinedCursor, NegativeRemoval, InvalidWeaponField, DuplicateInteractable, MissingTooltip, ProductionCostMultiplier Prerequisites** | This was a bulk lint cleanup responding to `check-yaml` output. It fixed ~900+ lint errors across 46 files. **However, it also introduced bugs** (see below). |

**What this commit fixed (correctly):**
- **LaunchAngle (363→0):** Converted `LaunchAngle` ↔ `Min/MaxLaunchAngle` per projectile type; removed `LaunchAngle` from `WarheadTrailProjectileCA`; added missing `MaximumLaunchAngle` where Min>Max.
- **UndefinedCursor chrono-target (195→0):** Added `chrono-target` cursor sequence alias in `cursors.yaml` (hyphen variant of `chrono_target`).
- **NegativeRemoval (64→0):** Stripped values from `-Trait: value` removal lines across 15 weapon YAML files. **This is where the bug was introduced** — see §3 below.
- **InvalidWeaponField (55→0):** Removed `WeaponClass` (40 lines, deprecated); fixed `Burstdelays`→`BurstDelays` (9); `BurstDelay`→`BurstDelays` (4); `Angle`→`LaunchAngle` on Bullet (1); removed weapon-level `ValidStances` (4); `ChangeOwnerValidStances`→`ValidStances` (2).
- **DuplicateInteractable (234→0):** Added `-Selectable:` to all bridge actors to remove inherited `Selectable` (which includes `InteractableInfo`), keeping only explicit `Interactable:` with custom `Bounds`. **This was later partially reverted** — see §2.4.
- **MissingTooltip (39→0):** Added `Tooltip` trait to `camera.gpssat`.
- **OverrideActor on Tooltip (2→0):** Removed invalid `OverrideActor` field from Tooltip traits in TD GDI vehicles and TD Shared aircraft.
- **ProductionCost/TimeMultiplier RequiresCondition (10→0):** Converted `RequiresCondition`→`Prerequisites` on `ProductionCostMultiplier` and `ProductionTimeMultiplier` in `^ScaledProducer` template and 9 other instances.
- **ValidStances on AutoTargetPriority (3→0):** Removed invalid `ValidStances` fields from `AutoTargetPriority` traits in `outpost2.yaml`.

**What this commit BROKE (the bugs):**
1. **NegativeRemoval header deletion:** When stripping values from `-Trait: value` lines, the lint script also accidentally deleted adjacent weapon/warhead HEADER lines. For example, `RA2DiskSteal:` (a weapon definition header) was deleted, leaving its child nodes orphaned. This caused YAML parse errors and `MissingFieldsException` crashes. Affected files: `RedAlert2/Shared/yaml/weapons.yaml`, `RedAlert2/Yuri/yaml/weapons.yaml`, and potentially others.
2. **Bridge actor -Selectable: was wrong:** The `-Selectable:` addition to bridge actors removed `Selectable` entirely, making bridges unselectable. This was later reverted in `e884bb5c9`.

### 2.4 Repository Cleanup (21:33 UTC+02:00) — AI Agent (pre-Claude Opus)

| Time | Commit | What | Why |
|---|---|---|---|
| 21:33 | `00d34354a` | Repository cleanup and documentation update: remove temp scripts, stale audit artifacts, update Knowledge Base Manual to v.0.3 with ContentPack migration refs, add policy/analysis docs | Cleaned up temporary scripts and stale docs. Updated the Knowledge Base Manual to v.0.3 reflecting the ContentPack migration. |

### 2.5 First Fix Session (22:11–22:27 UTC+02:00) — AI Agent (Claude Opus, session 1)

This was the first session of the Claude Opus agent responding to the bugs introduced by the lint commit.

| Time | Commit | What | Why |
|---|---|---|---|
| 22:11 | `e884bb5c9` | **Fix boot crashes:** remove invalid `-Selectable:` removals from bridge actors, restore accidentally deleted weapon headers | The game was crashing on boot due to the lint commit's bugs. This commit: (1) Reverted the `-Selectable:` additions from bridge actors (the DuplicateInteractable fix was wrong — it made bridges unselectable). (2) Restored missing weapon headers: `MachineGun`, `VenomLaser`, `Dragon`, `KirovExplode`, `RA2BrutePunchE`, `ra120mmThermobaricTargetingComputer`, `ra120mm2ThermobaricTargetingComputer`. |
| 22:26 | `dc6d55de5` | **Fix: restore missing `^RA2RailgunWeapon` header** accidentally removed during NegativeRemoval fix | One more header that was missed in the previous commit. The `^RA2RailgunWeapon` template header was deleted by the lint script, orphaning its child nodes. |
| 22:27 | `4f325e0cf` | Merge branch 'fix/yaml-lint-cleanup' to master | Merged the fixes. |

**Contributor commits interleaved (not by AI agent):**
- `6a01ad934` (Blackrobe, 02:56 +0700 = 21:56 CEST) — Expand career statistics summary (#223). Added more career statistics features. 8 files changed, 630 insertions, 154 deletions. No YAML/rules impact.
- `bb25a33ec` (Blackrobe, 03:43 +0700 = 22:43 CEST) — Update 2026-07-25 (#222). Three sub-PRs: (1) Restore D2k Spice Sifter footprint, (2) Fix D2K Starport behavior and Koda palettes, (3) Fix Koda player colors and color picker preview. 14 files changed. No RA2 impact.

### 2.6 RA2 Weapons Migration Session (22:30–23:25 UTC+02:00) — AI Agent (Claude Opus, session 2)

This was the second session of the Claude Opus agent, where the major RA2 weapons migration was done.

| Time | Commit | What | Why |
|---|---|---|---|
| 23:25 | `46e4b140e` | **Fix RA2 YAML crashes: migrate weapons to ContentPack, restore Yuri headers, fix Kübelwagen encoding, add AI agent handoff doc** | The big fix. See §3 below for full details. |

### 2.7 Post-Commit Session (23:25–present UTC+02:00) — AI Agent (Claude Opus, session 3 = current)

After the commit was made, additional documentation work was done and later committed in `388005dbb`:

1. **Updated `docs/Cameo_Knowledge_Base_Manual.md`:**
   - Bumped version from v.0.3 to v.0.3.1 (later further updated to v.0.4)
   - Updated version note to mention full RA2 weapons migration and NuclearFlashRenderer
   - Updated `redalert2.yaml` references to say "fully migrated" instead of "superseded"
   - Added `NuclearFlashRenderer.cs` to the custom trait reference table with note about the shader file requirement

2. **Attempted to run `utility.cmd cameo --check-yaml`** to verify remaining errors — this was canceled by the user before completion.

All changes from this session were committed in `388005dbb`.

---

## 3. Detailed Breakdown of Commit `46e4b140e` (The Big Fix)

### 3.1 RA2 Weapons Migration (ContentPack vs redalert2.yaml)

**Root cause:** The ContentPack `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml` was created as a migration of `mods/cameo/weapons/redalert2.yaml`, but only the templates (`^RA2*` prefixed) were migrated. **134 weapon definitions** (RA2CarrierTarget, RA2BrutePunch, RA2OspreyTarget, MigMissiles, V3Launch, etc.) were never copied to the ContentPack. Since `redalert2.yaml` is commented out in `mod.yaml` (line 295: `# cameo|weapons/redalert2.yaml  # migrated to ContentPacks/RedAlert2/Shared`), these weapons were missing from the ruleset, causing `Parent type RA2CarrierTarget not found` errors.

**Fix applied:** Replaced the ContentPack weapons.yaml with a full copy of `redalert2.yaml` (which has all 134 weapons + all templates + correct headers). Then applied the lint fixes from the previous lint commit (d42ad53a1) to the copy:

- Removed `ValidTargets: Ground, Ship` from `^RA2FlakWeapon` Warhead@Effect
- Removed `-TrailInterval:` from `^RA2LightMissile` and `^RA2MediumMissile`
- Fixed `TeslaArmorDischargeDummy`: removed `Projectile: LightningZap`, changed `-Image: DRAGON` to `-Image:`, changed `-TrailImage: smokey` to `-TrailImage:`
- Fixed `-Warhead@TeslaArc: FireShrapnel` to `-Warhead@TeslaArc:` (NegativeRemoval)
- Removed `-Warhead@Effect2:` from RA2HornetMissile, MigMissiles, RA2Terrorist, IvanBomb
- Removed `-Projectile:` from RA2SCUD
- Removed `Range: 20000` from YRBoomerSCUD
- Fixed `-Projectile: Missile` to `-Projectile:` in RA2TorpTube (restored `Projectile: Missile` + `Image: Patriot` after the removal line)
- Fixed `-Warhead@Smudge: LeaveSmudge` to `-Warhead@Smudge:` (NegativeRemoval)
- Fixed `-Warhead@EffectAir: CreateEffect` to `-Warhead@EffectAir:` (NegativeRemoval)
- Removed `Warhead@HeavyBomb: SpreadDamage` from RA2Terrorist
- Removed `Range: 1000` from LightningBolt

**File:** `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml`

### 3.2 Yuri Weapons YAML — Missing Headers (NegativeRemoval bug)

**File:** `mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml`

The lint commit (d42ad53a1) accidentally removed several weapon/warhead headers while doing NegativeRemoval cleanup. The bodies remained but became orphaned, causing YAML parse errors.

**Headers restored:**
- `RA2DiskSteal:` — weapon definition header (line 355)
- `Warhead@Cloud: SpawnSmokeParticle` — in RA2Chemspray (line 848). This was causing the `Sequences` field error because `SpawnSmokeParticle` warhead's child nodes were orphaned under a `-Warhead@Effect:` removal line.
- `Warhead@MediumChemicalWeaponPercentage: HealthPercentageDamage` — in RA2Chemspray (line 844)
- `Warhead@LaserWeapon: SpreadDamage` — in RA2Magnet (line 384)
- `Warhead@FlakWeapon: SpreadDamage` — in RA2Virusgun2 (line 774)
- `Warhead@Smudge: LeaveSmudge` — in RA2CosmonautLaser (line 932)

**Legitimate lint fixes left in place (not restored):**
- `StartBurstReport: vmagatta.wav` removed from RA2Magnet
- `StartBurstReport: flamtnk1.aud` removed from RA2Chemspray
- `ImpactActors: false` removed from RA2PsychicJab Warhead@Effect
- `-Warhead@Smudge:` removal line removed from RA2Magnet (after -Warhead@EffectAir:)
- `-Warhead@Effect2:` removed from RA2LasherToxicMortar
- `-Warhead@HeavyChemicalWeaponFriendlyFire: SpreadDamage` changed to `-Warhead@HeavyChemicalWeaponFriendlyFire:` (NegativeRemoval fix)

### 3.3 Missing Shader File — postprocess_nuclearflash.frag

**File:** `engine/glsl/postprocess_nuclearflash.frag` (new file, NOT tracked by mod git — lives in the .gitignored engine submodule)

**Root cause:** The custom trait `NuclearFlashRenderer` in `OpenRA.Mods.Cameo/Traits/World/NuclearFlashRenderer.cs` calls `base("nuclearflash", PostProcessPassType.AfterWorld)` which makes `RenderPostProcessPassBase` look for `postprocess_nuclearflash.frag` in `engine/glsl/`. This file was never created, causing a crash when the game tries to load post-processing shaders.

**Fix:** Created the shader file with proper uniforms matching what the C# code sets:
- `LightPosition` (vec2) — screen-space position of the nuclear blast
- `LightRadius` (float) — radius of the flash effect
- `LightColor` (vec3) — color of the flash
- `Brightness` (float) — brightness intensity (decreases over time)
- `Darkness` (float) — darkness amount for surrounding area (decreases over time)
- `SourceTexture` (sampler2D) — the rendered frame buffer (set by RenderPostProcessPassBase)

The shader brightens pixels near the blast center and darkens the surrounding area, with a smooth falloff using a squared clamp.

**⚠️ CRITICAL NOTE:** This file is in the `engine/` directory which is .gitignored. It must be created manually after `make all` fetches the engine. The shader source is NOT in the mod repo. If you need to recreate it, look at `NuclearFlashRenderer.cs` for the uniform names and implement a simple radial brighten/darken shader.

### 3.4 Naxis Kübelwagen Mojibake Fix

**File:** `mods/cameo/ContentPacks/RedAlert2Mod/Naxis/yaml/weapons.yaml`

**Error:** `Actor type naxis_kbelwagen: Weapons Ruleset does not contain an entry 'naxiww2kübelwagenmachinegun'`

**Root cause:** The weapon name `NaxiWW2KübelwagenMachinegun` was double-encoded as `NaxiWW2KÃ¼belwagenMachinegun` (mojibake — `ü` became `Ã¼` when UTF-8 bytes were re-interpreted as Latin-1). The actor `naxis_kbelwagen` in `vehicles.yaml` references the correct name with proper `ü`, but the weapon definition had the mojibake version, so they didn't match.

**Fix:** Corrected the weapon name from `NaxiWW2KÃ¼belwagenMachinegun:` to `NaxiWW2KübelwagenMachinegun:` (line 46).

### 3.5 Engine VERSION File

The `engine/VERSION` file is not tracked by git. It must contain the same hash as `mod.config`'s `ENGINE_VERSION` (`2949af84d08e2087237281c14937c2086ff6b113` as of 2026-07-25). If `make all` is run, it sets this correctly. If the file gets corrupted or reverted, `utility.cmd` and the game will fail with "Required engine files not found."

### 3.6 Documentation Updates in the Commit

The commit also updated:
- `docs/design/ROADMAP.md` — added 32 lines documenting the RA2 weapons migration, Yuri header restoration, Kübelwagen encoding fix, and nuclearflash shader
- `docs/LESSONS_LEARNED.md` — added 9 lines with lessons about NegativeRemoval header deletion, ContentPack migration completeness, UTF-8 mojibake, and engine shader files
- `docs/audit/SUMMARY.md` — updated B8 crash-class count to 0 and added the 2026-07-24 fix note
- `docs/AI_AGENT_HANDOFF.md` — created this handoff document (now being updated)

### 3.7 Boot-Gate Result

Boot-gate **passed** for commit `46e4b140e`: game launched to main menu with no new exception logs, `perf.log` ended with `MenuPostProcessEffect.PostWorldLoaded`.

---

## 4. What Other Contributors Did (2026-07-24)

These commits were made by human contributors (not AI agents) and are interleaved with the AI agent work:

### Blackrobe (3 commits)

1. **`80030028b`** — "Extend transient notification duration (#221)" — UI-only change to notification display time. No YAML/rules impact.

2. **`e57fd5a53`** — "Add directional superweapon exposure flashes (#220)" — Added a new post-process visual effect for superweapon directional flashes. This is relevant because it may have introduced or been related to the `NuclearFlashRenderer` pattern. If the game crashes on post-process loading, check whether this commit added new shader requirements.

3. **`bb25a33ec`** — "Update 2026-07-25 (#222)" — Three sub-PRs:
   - Restore D2k Spice Sifter footprint (building yaml fix)
   - Fix D2K Starport behavior and Koda palettes (StarportBatchProduction.cs fix + palette fixes)
   - Fix Koda player colors and color picker preview (palette and color picker fixes)
   14 files changed. No RA2 impact.

4. **`6a01ad934`** — "Expand career statistics summary (#223)" — Major expansion of career statistics: `CameoCareer.cs`, `CameoStatistics.cs`, `CameoCareerRecorder.cs`, `StatisticsWindowLogic.cs`, `statistics_window.yaml`, `en.ftl`. 8 files, 630 insertions, 154 deletions. No RA2 impact.

5. **`2ffb1583c`** — "Update engine pin for audio controls" — Changed the engine VERSION to a newer commit that includes audio control features. This is why `make all` must be re-run if the engine directory gets reset.

### ElPollo315 (4 commits, 2026-07-23)

1. **`d8d7482bd`** — "Working on Naval Stuff for CABAL" — CABAL naval units work.
2. **`660217500`** — "Merge remote-tracking branch 'github.com/master'" — Merge.
3. **`b08f94192`** — "Cabal Naval Icons Added" — CABAL naval unit icons.
4. **`01f9293ff`** — "Merge remote-tracking branch 'github.com/master'" — Merge.

### tjk-ws (2 commits)

1. **`3179d1905`** — "Remove redundant/overriding conyard yaml and improve FutureTech building glows" — Cleaned up construction yard YAML and improved FutureTech building visual effects.
2. **`1bf5d66f0`** — "Fix latin conyard crash" — Fixed a crash related to construction yard YAML.

---

## 5. Remaining Issues (NOT yet fixed)

### 5.1 Pre-existing check-yaml errors (not introduced by our work)

These errors existed before the RA2 weapons migration and are NOT our responsibility to fix (per task scope). They are listed here for awareness:

| Error class | Count | Description |
|---|---|---|
| UngrantedConditions | 72,813 | Actors consume conditions not granted by any trait (biggest error category) |
| InvalidField | ~700 | Trait fields that don't exist on their trait |
| MissingSequences | 209 | Images with no sequence definitions (includes `Image 'plasma' does not have any sequences defined`) |
| UndefinedNotification | 39 | Missing notification references |
| CannotParse | 12 | Cannot parse `Random` into `LockFaction.System.Boolean` — actors have `LockFaction: Random` but the engine expects a boolean |
| UndefinedActor | 11 | Husk actors not defined by any rule |
| InvalidOwner | 9 | Map actors with wrong owner |
| InvalidChildNodes | 4 | Traits with invalid child nodes |
| MissingPrereq | 2 | Buildable actors with unprovided prerequisites |
| UnknownTrait | 2 | Unknown traits in player.yaml |
| MissingFluentVariable | 1 | Missing fluent variable |

**Warning breakdown:**
| Warning class | Count | Description |
|---|---|---|
| UnconsumedConditions | 62,640 | Actors grant conditions not consumed (biggest warning) |
| UnusedFluentAttribute | 375 | Unused fluent attributes in en.ftl files |
| UnusedFluentVariable | 1 | Unused fluent variable |

### 5.2 `postprocess_nuclearflash.frag` not in git

The shader file lives in `engine/glsl/` which is .gitignored. It needs to be either:
1. Added to the engine repo (if we control it), or
2. Created by a post-fetch script in the mod repo, or
3. Documented as a manual step after `make all`

Currently option 3 is what we have. The Knowledge Base Manual has been updated to document this requirement.

### 5.3 `redalert2.yaml` still present but not loaded

The file `mods/cameo/weapons/redalert2.yaml` is still present in the repo but commented out in `mod.yaml` (line 295). The ContentPack now has a full copy of its contents. Consider:
1. Removing the commented-out line from `mod.yaml` entirely (cosmetic)
2. Eventually deleting `mods/cameo/weapons/redalert2.yaml` once all references are confirmed migrated
3. The ContentPack `content.yaml` still has a `Weapons:` entry pointing to the ContentPack weapons.yaml — this is correct and should remain

### 5.4 Knowledge Base Manual update (COMMITTED in `388005dbb`)

`docs/Cameo_Knowledge_Base_Manual.md` was updated with:
- Version bump from v.0.3 to v.0.3.1 (later further updated to v.0.4)
- NuclearFlashRenderer entry in the custom trait table
- Updated `redalert2.yaml` references to say "fully migrated"

This was committed in `388005dbb`.

---

## 6. What Needs To Be Done Next

### Step 1: ~~Commit the Knowledge Base Manual update~~ (DONE — committed in `388005dbb`)

### Step 2: Run `make all` to ensure engine is synced
```powershell
make all
```
This ensures the engine is fetched and built. After this, you MUST recreate `engine/glsl/postprocess_nuclearflash.frag` if it was removed by the engine fetch.

### Step 3: Run `utility.cmd cameo --check-yaml` and save to file
```powershell
cmd /c "utility.cmd cameo --check-yaml 2>&1" > check-yaml-output.txt
```
**⚠️ IMPORTANT:** Always save check-yaml output to a file. Do NOT pipe it directly to console — it produces ~140,000+ lines and takes 10+ minutes. The user has explicitly requested this multiple times.

### Step 4: Analyze remaining errors
Read `check-yaml-output.txt` and check for any NEW errors introduced by our changes. The pre-existing errors listed in §5.1 are expected. Any new `MissingFieldsException`, `Parent type not found`, or `weapon not found` errors need to be fixed.

### Step 5: Fix the `Image 'plasma'` and `LockFaction: Random` errors (if in scope)
- **`Image 'plasma' does not have any sequences defined`:** Find which weapon/actor uses `Image: plasma` and either add sequence definitions for `plasma` in the appropriate sequences YAML, or change the image to one that has sequences.
- **`Cannot parse 'Random' into LockFaction.System.Boolean`:** Find actors with `LockFaction: Random` and change to `LockFaction: false` (or `true` if locking is intended). The `LockFaction` trait expects a boolean, not a string.

### Step 6: Boot-gate test
```powershell
# Snapshot logs before
# Run launch-game.cmd
# Wait 30 seconds (or until main menu appears)
# Kill the game process
# Check for new exception logs
# Verify perf.log ends with: MenuPostProcessEffect.PostWorldLoaded
```

### Step 7: Update documentation (if any new fixes were made)
- `docs/design/ROADMAP.md` — update error breakdown with new counts
- `docs/audit/SUMMARY.md` — update if crash-class count changed
- `docs/LESSONS_LEARNED.md` — add any new lessons learned
- `docs/Cameo_Knowledge_Base_Manual.md` — update if new traits or patterns were discovered

### Step 8: Commit, push, and merge
```powershell
git add <specific files>
git commit -m "Descriptive commit message that ALL developers can understand"
git push origin master
```

**Never `git add -A`** — the maintainer usually has live uncommitted edits. Always scope `git add` to the specific files changed.

---

## 7. Key Files Modified (All Sessions Combined)

### Committed in `46e4b140e`:
- `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml` — replaced with full `redalert2.yaml` + lint fixes (48 lines changed)
- `mods/cameo/ContentPacks/RedAlert2/Yuri/yaml/weapons.yaml` — restored 6 missing headers (9 lines changed)
- `mods/cameo/ContentPacks/RedAlert2Mod/Naxis/yaml/weapons.yaml` — fixed mojibake weapon name (4 lines changed)
- `docs/AI_AGENT_HANDOFF.md` — created (138 lines)
- `docs/LESSONS_LEARNED.md` — added NegativeRemoval/mojibake/shader lessons (9 lines)
- `docs/audit/SUMMARY.md` — updated B8 crash-class count (2 lines)
- `docs/design/ROADMAP.md` — added RA2 migration details (32 lines)

### Committed in `e884bb5c9` (first fix session):
- `mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml` — restored `MachineGun` header
- `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml` — restored `RA2BrutePunchE`, `ra120mmThermobaricTargetingComputer`, `ra120mm2ThermobaricTargetingComputer` headers
- `mods/cameo/ContentPacks/TiberianDawn/Nod/yaml/weapons.yaml` — restored `VenomLaser`, `Dragon`, `KirovExplode` headers
- `mods/cameo/rules/civilian.yaml` — reverted `-Selectable:` additions from bridge actors

### Committed in `dc6d55de5` (second fix):
- `mods/cameo/ContentPacks/RedAlert2/Shared/yaml/weapons.yaml` — restored `^RA2RailgunWeapon` header

### Previously uncommitted (now committed in `388005dbb`):
- `docs/Cameo_Knowledge_Base_Manual.md` — NuclearFlashRenderer entry + version bump (now v.0.4)

### NOT in git (engine directory, .gitignored):
- `engine/glsl/postprocess_nuclearflash.frag` — must be recreated after `make all`

---

## 8. Key Files NOT Modified (but relevant)

- `mods/cameo/mod.yaml` — `redalert2.yaml` still commented out (line 295). The ContentPack weapons.yaml now has all weapons, so this is correct.
- `mods/cameo/ContentPacks/RedAlert2/Shared/content.yaml` — still has `Weapons:` entry pointing to ContentPack weapons.yaml. This is correct.
- `mods/cameo/weapons/redalert2.yaml` — original file, still present but not loaded. Can be deleted in a future cleanup.
- `OpenRA.Mods.Cameo/Traits/World/NuclearFlashRenderer.cs` — the C# trait that requires the shader file. Not modified, but documented in Knowledge Base Manual.

---

## 9. Binding Rules Reminder

1. **Always boot-gate before committing** — launch game, wait for main menu, check for exception logs. `check-yaml` is NOT a boot-gate substitute.
2. **Always update docs before committing** — ROADMAP, SUMMARY, LESSONS_LEARNED, Knowledge Base.
3. **Always fetch/pull/merge before committing.**
4. **Use PRs, don't push directly to master** (unless the user explicitly says to, as was done for this session).
5. **Commit titles must be self-explanatory to ALL developers.** No internal jargon.
6. **Merge to master when task is complete.** Don't leave work stranded on feature branches.
7. **`utility.cmd cameo --check-yaml` is NOT a boot-gate substitute** — it's a linting tool only. It takes 10+ minutes and produces ~140,000 lines. ALWAYS save output to a file, never pipe to console.
8. **Run `make all` after engine pin changes** — ensures engine is synced and built.
9. **After `make all`, recreate `engine/glsl/postprocess_nuclearflash.frag`** — the engine fetch will wipe custom shader files.
10. **When removing prerequisites and the `Prerequisites:` line becomes empty, KEEP the empty `Prerequisites:` line** — do NOT delete it.
11. **No gameplay or design changes** unless explicitly requested.
12. **No blind file deletions.**
13. **No committing without passing boot-gate.**

---

## 10. Quick Reference — How to Recreate the NuclearFlash Shader

If `engine/glsl/postprocess_nuclearflash.frag` is missing after `make all`, recreate it with these uniforms (derived from `NuclearFlashRenderer.cs`):

```glsl
uniform vec2 LightPosition;
uniform float LightRadius;
uniform vec3 LightColor;
uniform float Brightness;
uniform float Darkness;
uniform sampler2D SourceTexture;

void main()
{
    vec2 fragCoord = gl_FragCoord.xy;
    float dist = distance(fragCoord, LightPosition);
    float falloff = clamp(1.0 - (dist / LightRadius), 0.0, 1.0);
    falloff = falloff * falloff;

    vec4 source = texture2D(SourceTexture, fragCoord / vec2(textureSize(SourceTexture, 0)));

    vec3 brightened = source.rgb + (LightColor * Brightness * falloff);
    vec3 darkened = mix(source.rgb, source.rgb * (1.0 - Darkness), clamp(dist / LightRadius, 0.0, 1.0));

    vec3 result = mix(darkened, brightened, falloff);
    gl_FragColor = vec4(result, source.a);
}
```

**Note:** The exact shader implementation may need adjustment based on the engine's shader framework. Check `ConditionalTintPostProcessEffect.cs` and its corresponding shader for the correct pattern.

---

## 11. Glossary

| Term | Meaning |
|---|---|
| **NegativeRemoval** | YAML syntax where `-Trait:` removes an inherited trait. Writing `-Trait: value` is invalid — the value must be stripped: `-Trait:`. |
| **ContentPack** | A modular content package in `mods/cameo/ContentPacks/` that loads faction-specific rules, weapons, sequences, etc. via `content.yaml` manifests. |
| **Boot-gate** | The process of launching the game, waiting for the main menu, and checking for exception logs. Required before every commit. |
| **check-yaml** | `utility.cmd cameo --check-yaml` — a linting tool that checks YAML rules for errors. NOT a substitute for boot-gate. |
| **Mojibake** | Double-encoded UTF-8 characters, e.g., `ü` becoming `Ã¼` when UTF-8 bytes are re-interpreted as Latin-1. |
| **Orphaned nodes** | YAML child nodes whose parent header was accidentally deleted, causing them to be interpreted as children of the wrong parent. |
| **Engine pin** | The specific engine commit hash that the mod is built against. Stored in `mod.config` → `ENGINE_VERSION` and `engine/VERSION`. |
| **`make all`** | Fetches the pinned engine version, builds it, and sets up the mod for development. Wipes custom files in `engine/glsl/`. |

---

## 12. 2026-07-25 Session — Superweapon Documentation Audit

### 12.1 What Was Done

A comprehensive cross-reference audit of all superweapon and support power YAML traits against `docs/FACTIONS.md` was completed. This was a documentation-only audit — no game files were modified.

**Files modified (all committed in `388005dbb`):**
- `docs/audit/latest/superweapon_audit.yaml` — new file, raw audit data (607 lines)
- `docs/FACTIONS.md` — 14 discrepancies corrected across detailed faction sections and the superweapon reference table
- `docs/audit/SUMMARY.md` — added "Superweapon documentation audit" section
- `docs/design/ROADMAP.md` — added "Superweapon Documentation Audit (2026-07-25, COMPLETED)" section
- `docs/LESSONS_LEARNED.md` — added "Superweapon documentation audit (2026-07-25)" section
- `docs/history/AI_AGENT_HANDOFF.md` — this update

### 12.2 Audit Findings (14 total)

| ID | Severity | Faction | Issue | Status |
|---|---|---|---|---|
| SW-001 | HIGH | D2K Harkonnen | Palace has `^PrimarySuperweapon` but no power trait — Death Hand Missile unimplemented | Parked faction, not a regression |
| SW-002 | MED | TS Forgotten | Docs said "Tiberian Wildlife Rampage" but YAML has `NukePowerCA` (nuclear missile) | FIXED in FACTIONS.md |
| SW-003 | MED | TS CABAL | Docs said "Data Worm, Satellite Hack" but YAML has `NukePowerCA` + `FireArmamentPower` (Data Worm). Satellite Hack not found | FIXED — added Nuclear Missile, removed Satellite Hack |
| SW-004 | LOW | TS Nod | Docs only listed "Chemical Missile" but YAML has Cluster Missile + Chemical Missile | FIXED — added Cluster Missile |
| SW-005 | LOW | RA1 Allies | Docs missing "Chrono Reinforcements" support power | FIXED |
| SW-006 | LOW | RA2 Allies | Docs missing "Force Shield" support power | FIXED |
| SW-007 | LOW | Latin Syndicate | Docs missing "EMP Disable" and "Traitors" support powers | FIXED |
| SW-008 | LOW | Schwarzer Mond | Docs said "Meteor Traction Beam" but YAML power name is "Meteor Blitzkrieg" | FIXED |
| SW-009 | LOW | D2K Ordos | Docs said "Chaos Lightning" but YAML uses AsianChaosSuperweapon (same as Asian Alliance's "Chaos Storm") | FIXED — renamed to "Chaos Storm" |
| SW-010 | LOW | WC2 Humans | Docs missing "Slow" and "Invisibility" support powers | FIXED |
| SW-011 | LOW | WC2 Orcs | Docs missing "Bloodlust" and "Haste" support powers | FIXED |
| SW-012 | INFO | SC Protoss | Docs call it "Purifier Beam" but YAML reuses SteelIonCannon weapon | Noted in docs |
| SW-013 | INFO | Steel Consortium | Reference table missing "Federation Support Teleport" (4-tier support power) | FIXED — added to reference table |
| SW-014 | INFO | TS GDI | Reference table only said "Ion Cannon" but DropPodsPower is also implemented | FIXED — added Drop Pods to reference table |

### 12.3 WIP Faction Superweapons Discovered

These are documented in the audit YAML but NOT in FACTIONS.md (factions are WIP):
- **Warzone 2100** (`rules/wz2100.yaml`): IonCannonPower (charge 4000), AirstrikePower (charge 3000), NukePower (charge 9000)
- **Worms** (`rules/worms.yaml`): AirstrikePower/Sheep Strike (charge 6000), NukePower/Concrete Donkey (charge 9000)
- **Win98** (`rules/win98.yaml`): DetonateWeaponPower/Demo Disk Strike (charge 9000), DetonateWeaponPower/Red Ring of Death (charge 9000)
- **Warcraft 1** (`rules/warcraft1.yaml`): NukePower/Rain of Fire (charge 9000), NukePower/Poison Cloud (charge 9000)
- **WH40K** (`rules/wh40k.yaml`): 8 Deep Strike variants on `wh40korbitalrelay`, AirstrikePower/Marauder Bomber (charge 6000), IonCannonPower/Inquisition (charge 10000)

### 12.4 Outpost 2 Verification

The Supernova Missile IS implemented in `rules/outpost2.yaml` (not yet migrated to ContentPacks):
- Building: `EDEN_OBSERVATORY` (and `PLYMOUTH_OBSERVATORY`)
- Power trait: `NukePower`
- Weapon: `supernova_missile_super`
- Charge interval: 9000
- Missile delay: 11
- FACTIONS.md was already correct for both Eden and Plymouth.

### 12.5 What Needs To Be Done Next

1. **~~Commit the documentation changes~~** (DONE — committed in `388005dbb`)
2. **Pick up the next task from ROADMAP.md** — the superweapon audit is complete. The next priorities per ROADMAP are the balance class-formula program (infantry restat pass) and the remaining check-yaml error fixes.
