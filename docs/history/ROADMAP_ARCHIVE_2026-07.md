# ROADMAP archive — closed items (July → early August 2026)

> ⛔ **ARCHIVED — not a work queue.** These sections were lifted out of
> [`docs/design/ROADMAP.md`](../design/ROADMAP.md) on 2026-08-23 because every item in them
> is closed. They record *what happened*, never *what is true now*. The live queue is
> `docs/design/ROADMAP.md`; the entry point for a new contributor is
> [`docs/HANDOFF.md`](../HANDOFF.md).
>
> ⚠ **Commit hashes below cannot be resolved in a shallow clone.** Cameo's cloud/CI
> checkouts are shallow; run `git fetch --unshallow` before `git show <hash>`.

---

## 🔴 BUG — campaign maps vanish from editor + mission selector

- [x] **FIXED** (`42ba6f34c`, 2026-07-27): Root cause was `LockFaction: Random`
  (string) instead of `LockFaction: True` (boolean) in 6 map.yaml files — a
  regression from commit `6ccb9a749`. OpenRA silently dropped maps with invalid
  `LockFaction` values. Also fixed invalid fluent key `bot-campaign-ai.name` →
  `CampaignAI` in delivery/deliverycoop rules.yaml and added missing
  `bot_ai.campaign` fluent key to en.ftl.

---

### P0 — Completed (2026-07-26 session)

- [x] **RA1 Soviet atomic bomb lost its directional flash**: bulk YAML lint
  commit `d42ad53a1` deleted the `Warhead@NuclearFlash` header from active
  `RAAtomic`, leaving its tuning fields under a removal node. Split the shared
  weapon into `^AtomicCore` and an `Atomic` wrapper so `RAAtomic` can define the
  approved 40-tick effect without a regex-fragile negative removal. Added an
  active-ruleset contract audit covering RA1 `RAAtomic`, Ixian `PulseMissile`,
  and CABAL `CabalMagicNuke`.

---

### P0 — Completed (2026-07-24 session)

- [x] **RA2 weapons migration to ContentPack** (`fix/ra2-weapons-migration`):
  The ContentPack `RedAlert2/Shared/yaml/weapons.yaml` only had templates
  (`^RA2*` prefixed), missing 134 weapon definitions (RA2CarrierTarget,
  RA2BrutePunch, MigMissiles, V3Launch, etc.) that were only in
  `mods/cameo/weapons/redalert2.yaml` (commented out in mod.yaml). Replaced
  ContentPack weapons.yaml with full copy of redalert2.yaml and applied all
  lint fixes from commit d42ad53a1 (NegativeRemovals, invalid fields, etc.).
  This resolves the `RA2CarrierTarget not found` error.
- [x] **Yuri weapons missing headers** (`fix/ra2-weapons-migration`): The lint
  commit d42ad53a1 accidentally removed 6 weapon/warhead headers in
  `RedAlert2/Yuri/yaml/weapons.yaml` while doing NegativeRemoval cleanup.
  Restored: `RA2DiskSteal:`, `Warhead@Cloud: SpawnSmokeParticle` (RA2Chemspray),
  `Warhead@MediumChemicalWeaponPercentage: HealthPercentageDamage` (RA2Chemspray),
  `Warhead@LaserWeapon: SpreadDamage` (RA2Magnet),
  `Warhead@FlakWeapon: SpreadDamage` (RA2Virusgun2),
  `Warhead@Smudge: LeaveSmudge` (RA2CosmonautLaser).
  The missing `Warhead@Cloud: SpawnSmokeParticle` header caused the
  `Sequences` field error (orphaned SpawnSmokeParticle child nodes under a
  removal line).
- [x] **Naxis Kübelwagen weapon encoding fix** (`fix/ra2-weapons-migration`):
  Weapon name `NaxiWW2KÃ¼belwagenMachinegun` in Naxis weapons.yaml had
  double-encoded UTF-8 (mojibake), causing weapon-not-found crash for
  `naxis_kbelwagen` actor. Fixed to `NaxiWW2KübelwagenMachinegun`.
- [x] **Missing postprocess_nuclearflash.frag shader** (prior session):
  `NuclearFlashRenderer.cs` expects `postprocess_nuclearflash.frag` in
  `engine/glsl/` but the file was never created. Created shader with proper
  uniforms (LightPosition, LightRadius, LightColor, Brightness, Darkness,
  SourceTexture). NOTE: file lives in engine/ which is .gitignored; must be
  recreated after `make all` fetches engine. See history/AI_AGENT_HANDOFF.md.

---

### New orders 2026-07-17 (second batch)

- [x] **Umlaut transliteration** (2026-07-17): `schwarzermond_bermensch`
  → `schwarzermond_ubermensch` (Ü was dropped instead of transliterated),
  `ÜbermenschLaser(E)` → `UbermenschLaser(E)`, assets git-mv'd. RULE in
  DESIGN §1: Ü→u, Ö→o, Ä→a, ß→ss in ids; display names keep umlauts.

- [x] **BUG: cameo tileset palettes** — FIXED 2026-07-30: root cause was
  that CAMEO's `terrain` and `staticterrain` palettes used `temperat.pal`
  while all CAMEO tile templates use `Palette: ra_temperat` and all
  bib/smudge sprites (`.tem` files) were designed for `ra_temperat.pal`.
  The `temperat.pal` and `ra_temperat.pal` are different palette files,
  causing color mismatches on smudges, craters, and building bibs.
  Fix: changed both `PaletteFromFile@terrain-cameo` and
  `PaletteFromFile@staticterrain-cameo` in `rules/palettes.yaml` from
  `temperat.pal` to `ra_temperat.pal`. Reported by maintainer; was lost
  from an earlier queue.
- [x] **SM promotion grid (maintainer's design, image 2026-07-17)** —
  3 columns x 4 ranks implemented in `SchwarzerMond/yaml/promotions.yaml`.
  [Übermensch/Laser Tank(rpl Beetle)/Crystal Tank/Parzival] |
  [Noid MG/Lunar Tiger(rpl Panzer)/Korruptes Biest/Dalek] |
  [Piercer/Haunebu 3(rpl H2)/MARS(rpl Jagerline)/Die Glocke]. Unit
  prerequisites wired to require the matching promotion; replaced units
  disabled when the replacement promotion is bought. Promotion-unit
  `^PromotionUnitBuff` inheritance verified on all grid units. Boot
  test passed (2026-07-17). FINAL layout re-chained 2026-07-17 after
  the maintainer's decision — see P2 (RESOLVED) for the binding grid;
  do not rearrange promotions.yaml except through a new design order.
- [x] **cabal_plasmaturret not buildable** — root cause: no sequence/
  icon defined for `cabal_plasmaturret`. Added sequence in `ContentPacks/
  TiberianSun/CABAL/yaml/sequences.yaml` and voxel turret mapping in
  `sequences/voxels.yaml`, using TS Nod laser turret assets as placeholder
  (2026-07-17). Boot test passed.
- [x] **cabal_mobilestealthgenerator removed** — CABAL should not have
  it (design 2026-07-17); actor + AI references deleted.
- [x] **RA1 LEGACY-ID RENAME** — DONE 2026-07-17 (`fdd466494`): all 52
  legacy ids renamed via tools/rename/apply_ra1_legacy.py +
  rename_map_ra1_legacy.yaml; zerofighter collision resolved as
  japan_zerofighter_slave; registry 3910/2365, zero old ids, boot green.
  Follow-up fix same day: explicit `actor_<oldid>.description/.name`
  refs in yaml (13) broke when ftl keys renamed — applicator now has a
  fluent-stem pass; warcraft2_en.ftl + tkm_en.ftl were never registered
  in mod.yaml FluentMessages (added). audit_fluent: 0 unresolved.
- [x] **Stale copy cleanup** — DONE 2026-07-17 (`fdd466494`):
  rules/weapons/sequences redalert.yaml + dead RedAlert wrapper
  content.yaml/ai.yaml deleted.

---

### P2 — SM promotion grid tier ladder (RESOLVED 2026-07-17 — maintainer picked the reshuffle)

**FINAL LAYOUT (implemented; column convention: left = infantry, middle =
vehicles/tanks, right = aircraft/artillery/support):**

| Rank | Infantry | Vehicles | Air/Artillery/Support |
|---|---|---|---|
| 1 | Noid MG (T2) | Lunar Tiger (rpl Panzer, T2) | Laser Tank (rpl Beetle, T1) |
| 2 | Übermensch (T3) | MARS (rpl Jagerline, T2) | Haunebu III (rpl H2, T3) |
| 3 | Korruptes Biest (T3) | Crystal Tank (T3) | Piercer (T3) |
| 4 | Parzival | Dalek | Die Glocke |

Implemented 2026-07-17: promotions.yaml re-chained + BuildPaletteOrder
row-major; promotion actor `..._bermensch` renamed `..._ubermensch`
(umlaut law); `^PromotionUnitBuff` corrected to the FutureTech
convention — EXACTLY the 12 grid units inherit it (was also on 10 base
units incl. all 4 replaced ones: Lunar Soldier/Rocket, Laser Beetle,
Lunar Panzer, Jagerline, Haunebu II, Neo Jagdpanzer, Lunar Grille,
Gravity Core Tank, Black Bomb — an unintended faction-wide buff).
Follow-up: fluent-ify the 12 promotion tooltips (raw strings), part of
the SM rebalance pass below.

<details><summary>Decision record (superseded analysis)</summary>

#### Original analysis — kept for the record

**Maintainer input (2026-07-17):** MARS is an AA artillery unit (ground +
air, long range); Laser Beetle and Laser Tank are AA too, so MARS replacing
Jagerline is fine — the earlier "loses mobile AA" concern is WITHDRAWN.
Binding principle: promotion rank should ladder with tech tier. Open
dilemma: Übermensch is T3 yet sits at rank 1; making it a base unit leaves
an empty cell; SM also feels thin on early-game units.

**Implemented state:** the grid exists in `SchwarzerMond/yaml/promotions.yaml`
with CABAL-pattern gating already in place (the promotion gates the option;
units keep their tech prereqs — e.g. Dalek needs warfactory + techcenter +
promotion; replaced units carry `!promotion_x`). NOTE: the implemented
chains DEVIATE from the maintainer's image: col1 Übermensch→Crystal
Tank→Korruptes Biest→Parzival, col2 Laser Tank→Lunar Tiger→Noid MG→Dalek,
col3 MARS→Haunebu III→Piercer→Die Glocke (the image had Noid MG + Piercer
at rank 1 and MARS at rank 3). Needs maintainer sign-off either way.

**The structural fact:** 8 of the 12 grid units are T3 payoffs. Only Laser
Tank (T1 replace), Noid MG, Lunar Tiger and MARS (T2) are early/mid-game.
A strict tier-per-rank ladder is impossible with these 12 units — but a
clean monotone ladder IS possible, because rank 2+ arrives around the T3
tech era anyway. Only rank 1 must be early-tier.

**Base roster reference (after promotion extraction):**
T1 base: Lunar Soldier, Lunar Rocket, Engineering Armor, Laser Beetle,
Lunar Panzer, Sturm Cannon, Laser Tower. T2 base: Jagerline, Lunar
Grille, Space Zeppelin, Noid Harvester. T3 base: Neo Jagdpanzer,
Gravity Core Tank, Black Bomb. (Everything else is promotion-gated.)

**Option 1 — RESHUFFLE (recommended; zero balance impact — only
promotions.yaml chains + BuildPaletteOrder change, unit files untouched):**

| Rank | Vehicles | Infantry & walkers | Armor & air |
|---|---|---|---|
| 1 | Laser Tank (rpl Beetle, T1) | Noid MG (T2) | Lunar Tiger (rpl Panzer, T2) |
| 2 | MARS (rpl Jagerline, T2) | Übermensch (T3) | Haunebu III (rpl H2, T3) |
| 3 | Crystal Tank (T3) | Korruptes Biest (T3) | Piercer (T3) |
| 4 | Dalek (capstone) | Parzival (capstone) | Die Glocke (capstone) |

Ladder: rank 1 = T1/T2, rank 2 = T2/T3, rank 3 = T3, rank 4 = buildlimit-1
capstones. Replacements (straight upgrades) all land in ranks 1–2, pure
unlocks in ranks 2–4. Übermensch keeps its promotion prestige at rank 2,
matching its techcenter timing.

**Option 2 — Übermensch to base roster, swap in an existing T3 base unit**
(if the flagship must always be visible): Übermensch becomes a regular T3
buildable; its cell is filled by promoting an existing base T3 unit into
the grid instead (candidates: Gravity Core Tank, Neo Jagdpanzer, Black
Bomb) — no new art needed, roster depth unchanged. Then apply Option 1's
ladder to the resulting 12.

**Option 3 — early-game retier pass** (independent lever for "not enough
early units"; sheet-first + maintainer approval since stats/prices move):
candidates Noid MG T2→T1 (classic MG-infantry tier) and/or Lunar Grille
earlier. Combines freely with Option 1; does NOT block it.

**Rejected:** keeping the image order with pure visibility-gating (rank 1
unlocking T3 options) — contradicts the maintainer's tier principle. New
early-game units (old Option E) stays a separate long-term roster item.

(Maintainer picked Option 1 with two switches: infantry column left,
vehicles middle; Laser Tank ↔ Lunar Tiger swapped — Lunar Tiger is a
line tank, Laser Tank plays as support. See the FINAL LAYOUT above.)

</details>

---

### ~~P0 — ENGINE PIN vs LOCAL ENGINE MISMATCH~~ RESOLVED 2026-07-19

Commit a4b2eb8a7 (#210) bumped mod.config ENGINE_VERSION to `b89ae60`
but the local engine/ is still `7ba39d9` and NO engine fetch/build ran
— `launch-game.cmd` refuses to start ("Required engine files not
found") for EVERYONE on a fresh pull until the engine is updated
(make all / fetch b89ae60 + dotnet rebuild) or the pin is reverted.
Owner: whoever landed #210 (their session likely has the context).
My boot gates ran against the proven 7ba39d9 via a temporary LOCAL
pin revert (never committed). **RESOLVED: `make.cmd all` fetched b89ae60 and rebuilt engine + all mod assemblies (0 errors); boot to menu verified on the new engine. TEAMMATES: run `make.cmd all` once after pulling if your local engine is still 7ba39d9.**

---

### P2b — CABAL promotion grid tier-mismatch (DESIGN DECISION NEEDED)

**Same problem as SM.** CABAL's 3×4 grid also has tier mismatches:

| Row | Col 1 (Infantry) | Col 2 (Vehicles) | Col 3 (Aircraft) |
|---|---|---|---|
| 1 | Devout **T2** | Spider CNC4 **T1** | Cyborg Assassin **T2** |
| 2 | Ascended **T2** | Heavy Reaper **T2** | Super Hunter Killer **T1** |
| 3 | Beholder **T3** | Widow **T2** | Overkill Gunship **T1** |
| 4 | Cyborg Commando V2 **T3** | Core Defender **T2** | Mothership **T1** |

Col 3 (Aircraft) is inverted: Row 1 is T2, but Rows 2-4 are all T1 (helipad
only). Capstones (Row 4) include T1 and T2 units alongside T3.

**How FutureTech solved it:** All 12 FutureTech promotion-units are T3.
Every unit requires high-tier buildings (`battlelab`, `hypercore`,
`robotcontrolcenter`, `transmissioncenter`). The promotion grid only
determines *which* T3 units you can see — the tech buildings gate the
actual power. No tier mismatch because all units are the same tier.

This works for FutureTech because it's a high-tech faction where everything
is advanced. CABAL is more diverse — it has T1 helipad units, T2 cyborg
factory units, and T3 techcenter units.

**Solution options for CABAL:**

**Option FT — Make all promotion-units T3 (FutureTech pattern)**
- Add `cabal_techcenter` (or `cabal_core`) as a prerequisite to every
  promotion-unit that doesn't already have it.
- The promotion grid then just gates visibility — all units are T3 power.
- **Pro:** Cleanest, proven pattern (FutureTech works). Zero grid
  restructuring. Matches the CABAL pattern already in use.
- **Con:** T1/T2 units (Overkill Gunship, Hunter Killer, Devout, etc.)
  become T3 — delayed availability, possible balance shift. Mothership
  and Overkill Gunship are currently early-game options; making them T3
  changes CABAL's early game feel.
- **Effort:** S (add prereq to ~6 units, boot test).

**Option SR — Sort grid rows by tier (restructure)**
- Row 1 → T1 units: Spider CNC4, (new T1 vehicle), Hunter Killer
- Row 2 → T2 units: Devout, Heavy Reaper, Cyborg Assassin
- Row 3 → T3 units: Beholder, Widow, Overkill Gunship (rebalance to T3)
- Row 4 → Capstones: Cyborg Commando V2, Core Defender, Mothership
- **Pro:** Clean tier ladder.
- **Con:** Requires rebalancing several units (Overkill Gunship T1→T3,
  Mothership T1→T3). Need a T1 vehicle for Col 2 Row 1 (or move an
  existing unit down). Significant balance pass.
- **Effort:** L (rebalance + grid restructure + test).

**Option HY — Hybrid: tier-sort columns + CABAL gating**
- Sort each column so tiers go T1→T2→T3→capstone within the column.
- Keep the CABAL pattern: promotion gates visibility, tech gates power.
- Col 1: Devout (T2) → Ascended (T2) → Beholder (T3) → Cyborg Commando V2 (T3)
- Col 2: Spider CNC4 (T1) → Heavy Reaper (T2) → Widow (T2) → Core Defender (T2)
- Col 3: Hunter Killer (T1) → Overkill Gunship (T1) → Cyborg Assassin (T2) → Mothership (T1)
- **Pro:** Best tier progression within columns. Minimal unit changes.
- **Con:** Col 3 is still mostly T1 — aircraft are inherently low-tier
  for CABAL. Would need to rebalance aircraft to higher tiers for a
  clean ladder, or accept that CABAL aircraft are early-game.
- **Effort:** M (rearrange grid + minor rebalance + test).

**Option KP — Keep as-is, promotion gates option (accept the mismatch)**
- CABAL already uses the "promotion gates visibility, tech gates power"
  pattern. The tier mismatch is acceptable because:
  - Row 1 unlocks options you can build once you have the right building.
  - Row 4 capstones are powerful regardless of tier (Mothership is T1
    but requires `cabal_core` which is a late-game building).
- **Pro:** Zero changes needed. Already works.
- **Con:** Tier progression doesn't feel intuitive. A new player might
  expect Row 4 to be "bigger" than Row 1 but it's not always.
- **Effort:** S (zero).

**Recommendation:** Option FT (FutureTech pattern) is the cleanest if
we're willing to make all CABAL promotion-units require `cabal_techcenter`
or `cabal_core`. This is the proven solution. However, it changes CABAL's
early game by delaying T1/T2 promotion-units to T3. Option KP (keep
as-is) is the lowest-risk if the maintainer is comfortable with the
existing CABAL pattern where `cabal_core` already gates the capstones.

**Note:** `cabal_core` (CABAL Core building) is already a high-tier
prerequisite for Core Defender, Widow, and Mothership. It's effectively
CABAL's T3.5 gate. If we standardize all promotion-units to require
either `cabal_techcenter` or `cabal_core`, we get the FutureTech pattern
without changing the feel of individual units — just their availability
window.

**Awaiting maintainer decision before implementation.**

---

---

## CABAL — recently completed (this push)

- [x] Confident quick fixes: missile arc, HK mk1 blue laser, Core
  Defender offset, Mantis sound (`87a716b41`).
- [x] Crab → **Ravager** infantry plasma line-breaker + plasma bullet
  effect (`e4ac0ce40`, `b31113a6d`). Crab id retired.
- [x] CABAL weapons get their own firing sounds (`1281a71f5`).
- [x] Rocket-launcher offsets/counts + Manticore dual laser (`c4691e758`).
- [x] Mantis + Laser Spider → AttackFrontal fire support (`cc6a290db`).
- [x] Dissolver: cloak → corrosion (`corroded` cond) + TankDestroyer +
  LightChemical combo + new `cabal_dissolveimpact` effect (`de25b469d`);
  effect re-rendered to fit its frame (`45b8f0caa`).
- [x] Eliminator 800: real `^GatlingSpeedUpUnitBehavior` spin-up (drop
  the AmmoPool hack), single ground + Air-only twin, dune autogun muzzle
  @3671 (`33c13a553`).
- [x] All CABAL infantry: vehicle-style turn rate 2×Speed/5 (`f98bf8155`).
- [x] Devin sound pass (uncommitted, verified, keep): DarkObeliskLaser /
  CabalCommandoPlasma / Mk2 → obelcor3.aud; Reaper/TwinBazooka/rocket
  weapons → samshot1.aud; Core Defender offset raise; magicnuke Tick tune.
- [x] Effect-naming: CABAL authored weapons already clean. `TS90mm_bluenuke`
  `@3Eff` is NOT a violation — it overrides `^TSCannonEffect`'s own
  `@3Eff`. Mod-wide sweep still pending (CE).

---

---

## Dune factions (D2K) — split + naming + upgrades (P2)

- [x] **Split dune Light Infantry + Rocket Trooper per faction** (neutral
  base template → per-faction Ixian/Ordos actors) so upgrades apply
  separately (`b180aef36`).
- [x] **Ordos Light Infantry gets Laser Cartridges** once it's its own actor
  (`b180aef36`).
- [x] **Rename Ordos "Armor-Piercing Rounds" → "Rapid Fire Armor-Piercing
  Belts"** (actor id, template, condition, sequence, icon — full rename)
  (`b180aef36`).
- [x] No-hyphen naming scheme across all dune factions.
  Verified 2026-07-14: no hyphenated actor IDs, weapon IDs, or asset
  references in any D2k ContentPack yaml. All hyphens found are
  engine-defined conditions/sequence names (build-incomplete, damaged-idle,
  etc.) which are engine-owned and stay as-is per DESIGN.md §1.
- [x] **D2K shared effect-template concrete cleanup** (2026-08-20) —
  resolved duplicate `DamagesConcrete` warheads across the D2K rocket/missile/
  155mm effect families, fixed `^D2KMissile`/`^D2KRocket`/`^ORocket`/`^OMissile`
  3-way split inheritance, `effect_audit` reports 0 duplicate concrete warheads,
  boot-gated with `MenuPostProcessEffect.PostWorldLoaded` and no new
  exception log.
- [x] **D2K Devastator/Plasma cannon 3-way split** (2026-08-20) —
  converted `DevBullet`/`PlasBullet` to explicit `Inherits@wh/@proj/@fx` using
  new `^Warhead_CannonHE_Heavy_D2K_DevBullet`, `^Projectile_Shell_Heavy_D2K_DevBullet`,
  and `^Effect_CannonHE_Heavy_D2K_DevBullet` in D2K Shared; preserved damage,
  projectile, effect, concrete, glow, and merged the duplicate ground
  `d2k_small_napalm` + `d2k_shockwave` effects into a single `d2k_shockwave`
  impact; `audit_balance_drift` clean, boot-gated with no new exception log.
- [x] **D2K Rocket Trooper family 3-way split** (2026-08-23) —
  converted the five `D2K_Rocket_Trooper*` weapons in `mods/cameo/weapons/d2k.yaml`,
  `ContentPacks/D2k/Ixian/yaml/weapons.yaml`, and `ContentPacks/D2k/Ordos/yaml/weapons.yaml`
  to explicit `Inherits@wh/@proj/@fx`; removed `Inherits: ^D2KRocket` and
  `Inherits: ^D2K_Cannon`; added per-weapon `^Projectile_*_D2K_Rocket_Trooper*`
  templates and `^Effect_MissileAP_Heavy_D2K_Rocket_Trooper` in D2K Shared.
  Preserved triple warhead damage (Light/Medium/Heavy missile AP and
  Demolition/Railgun/Cannon mixes), d2k_RPG projectile visuals, and Dune
  smudge/glow/shield/concrete effects; `review_resolve_diff.py` OK, all
  targeted audits clean, ledgers re-extracted and `audit_balance_drift` clean,
  boot-gated with no new exception log.
- [x] **Ixian D2K missile 3-way split** (2026-08-23) — converted
  `D2K_TowerMissile` and `mtank_pri2` in `ContentPacks/D2k/Ixian/yaml/weapons.yaml`
  to a single `Inherits: ^D2KMissile` warhead plus per-weapon
  `Inherits@proj: ^Projectile_Missile_Heavy_D2K_TowerMissile` /
  `^Projectile_Missile_Heavy_D2K_mtank_pri2` and
  `Inherits@fx: ^Effect_MissileAP_Heavy_D2K_TowerMissile` /
  `^Effect_MissileAP_Heavy_D2K_mtank_pri2`. Removed the 7 per-weapon
  `^Warhead_*_D2K_TowerMissile` / `^Warhead_*_D2K_mtank_pri2` templates from
  D2K Shared and deleted the legacy multi-warhead `Inherits: ^Grenade` /
  `^MediumFlameWeapon` / `^FlakWeapon` stacks. Preserved missile `Damage` 4000/8000
  and percentage `Damage` 2/4 as local overrides, D2K heavy missile projectile
  visuals, and the resolved smudge/glow/shield/concrete effects. Resolver diff
  and targeted audits clean, ledgers re-extracted, `audit_balance_drift` clean,
  boot-gated with no new exception log.
- Note: 7 Ordos armor-rework files are the maintainer's live WIP — leave.

---

---

## Barrier & Wall Assignment Refactor (2026-07-17, COMPLETED)

**Goal:** Thematic and balanced barrier assignment across all factions.
Only classic TD and RA1 factions have dual wall types (light + heavy).
All other factions have a single, thematically appropriate wall type.

### Final Barrier Assignment Map

| Faction | Wall Type | Prerequisite Token |
|---------|-----------|-------------------|
| TD GDI | SBAG (sandbag) + BRIK (concrete) | `sandbagbarrier` + `concretebarrier` (^FACT) |
| TD Nod | CYCL (chainlink) + BRIK (concrete) | `chainlinkfence` + `concretebarrier` (^FACT) |
| RA1 Allies | SBAG (sandbag) + BRIK (concrete) | `sandbagbarrier` + `concretebarrier` (^RAFACT) |
| RA1 Soviets | FENC (wire) + BRIK (concrete) | `wirefence` + `concretebarrier` (^RAFACT) |
| RA1 Japan | CYCL (chainlink) + BRIK (concrete) | `chainlinkfence` + `concretebarrier` (^RAFACT) |
| RA2 Allies | ra2_awall | `ra2awall` |
| RA2 Soviets | ra2_swall | `ra2swall` |
| RA2 Yuri | ra2_ywall | `ra2ywall` |
| FutureTech | ra2_awall | `ra2awall` |
| Consortium | ra2_awall | `ra2awall` |
| Syndicate | ra2_swall | `ra2swall` |
| Naxis | ra2_swall | `ra2swall` |
| Schwarzer Mond | ra2_ywall | `ra2ywall` |
| Asian Alliance | asianalliance_concretebarrier | `asianalliancebarrier` |
| TS GDI | asianalliance_concretebarrier | `asianalliancebarrier` |
| TS Nod | ts_nod_laserfence | `tslaserfence` |
| CABAL | ts_nod_laserfence | `tslaserfence` |
| Forgotten | FENC (wire) | `wirefence` |
| TKM | FENC (wire) | `wirefence` |
| D2k Ordos | D2k wall | `d2k_construction_yard` |
| D2k Ixian | D2k wall | `d2k_construction_yard` |

### Changes Made
- Restored missing RA2 faction wall actors (`ra2_awall`, `ra2_swall`, `ra2_ywall`)
  with sprites and sequences from golden reference.
- Changed TD Nod from `wirefence` to `chainlinkfence` per maintainer request.
- Added shared `tslaserfence` prerequisite token so both TS Nod and CABAL
  can build the laser fence.
- Added shared `asianalliancebarrier` prerequisite token so both Asian
  Alliance and TS GDI can build the Asian Alliance concrete barrier.
- Removed `ra2fact` prerequisite from FutureTech (was enabling secondary
  `ra2brik` wall).
- Negated inherited `ra2awall` on RA2 Soviets and Yuri so they only get
  their own faction-specific wall.
- Removed `concretebarrier` and `sandbagbarrier` from all non-classic
  faction construction yards.

---

---

## Faction Internal Name & Inherits Consistency

- [x] **FACTION-RENAME: Rename faction internal names for consistency**
  — DONE 2026-07-16. Renamed 11 faction InternalNames to match actor
  prefixes, plus WC2 actor prefix rename. All YAML, Python, MD, AI files
  and asset files updated:
  - `gdi` → `td_gdi`, `nod` → `td_nod` (TD factions)
  - `allies` → `ra1_allies`, `soviets` → `ra1_soviets` (RA1 factions)
  - `ra2allies` → `ra2_allies`, `ra2soviets` → `ra2_soviets` (RA2 factions)
  - `tsgdi` → `ts_gdi`, `tsnod` → `ts_nod` (TS factions)
  - `consortium` → `steelconsortium`, `syndicate` → `latinsyndicate` (RA2 mod)
  - `warcraft_humans` → `wc2_humans`, `warcraft_orcs` → `wc2_orcs` (WC2 factions + actors)
  - `asian_alliance` → `asianalliance` (fixed underscore-in-faction-name violation)
  - Already consistent: `schwarzermond`, `naxis`, `futuretech`, `japan`, `yuri`,
    `forgotten`, `cabal`, `terran`, `zerg`, `protoss`, `tkm`, etc.
  - Verified by `audit_consistency_report.py` checks C6-C11 (73 checks, 0 failures).
  - Remaining: `.oramap` map files may need `tools/fix-oramap.ps1` update.
  - Remaining: WC1 factions (`human` → `wc1human`, `orc` → `wc1orc`) not yet done.

- [x] **INHERITS-PASCAL: Convert camelCase/snake_case inherits to PascalCase**
  — all inherits templates converted to PascalCase per DESIGN.md §1.
  Commit `3f5c53915` (WC2/WC1, 301 replacements/20 files): WC2 Humans
  (`^wc2_h_*`/`^wc2_humans_*` → `^WC2Humans*`), WC2 Orcs
  (`^wc2_o_*`/`^wc2_orcs_*` → `^WC2Orcs*`), WC2 shared (`^wc2_*` → `^WC2*`),
  WC1 Humans (`^wc_h_*` → `^WCHumans*`). Full faction names used (no
  single-letter abbreviations).
  Commit `cf0e4485d` (all remaining, ~2158 replacements/126 files): RA2
  Soviets camelCase, CABAL snake_case, Outpost 2/SOW, TKM, USA, RA1 Allies,
  D2K, generic templates (`^wall`→`^Wall`, `^refinery`→`^Refinery`, etc.),
  and Sidebar faction name capitalization. D2K-specific `^Refinery` renamed
  to `^D2KRefinery` to avoid collision with base `^Refinery`. Boot-gate
  clean (zero "Parent type not found" errors).

---

## Starcraft Rank Decoration Fix

- [x] **SC-RANKS: Split alien rank decoration per Starcraft faction**
  — FIXED: commit `c3e3490f7` reverted the blanket `^AlienRankDecoration`,
  commit `031c54d6b` created 3 separate decorations (`^ZergRankDecoration`
  with `alienrank`, `^TerranRankDecoration` with `terranrank`,
  `^ProtossRankDecoration` with `protossrank`). All use `alienranks.png`
  as placeholder. 7 actors missing faction decorations fixed and
  `audit_rank_decoration.py` reports 0 StarCraft issues.

---

## Weapon Suffix Standardization

- [x] **WEAPON-SUFFIX-ELITE: Migrate legacy E suffix to _elite**
  — DONE 2026-07-30: Renamed 117 elite-gated weapons from `<base>E` to
  `<base>_elite` across 44 files (339 lines changed) via
  `tools/rename_elite_weapons.py`. Handles compound suffixes: `AAE`→`AA_elite`,
  `EMPE`→`EMP_elite`, `EResonance`→`_eliteResonance` + bounce variants.
  Skipped `MigMissiles_AA_ELITE` (already contains ELITE) and 45 doctrine
  variants (`_rad`/`_fire`/`_tesla`), upgrade combos, and gatling spin-ups
  that are intentionally non-standard. Boot-gated: menu reached, 0 new
  exception logs. Audit: X1 count dropped from 112+ to 45 (intentional
  non-standard remnants).
  **Follow-up** (2026-07-31): Renamed 17 remaining deprecated `E`-suffix
  weapons missed by the first pass (33 replacements across 15 files) via
  `tools/archive/rename_elite_E_suffix.py` (one-time, archived). X4 dropped 19→2 (only `HE` =
  High Explosive false positives remain). Boot-gated, O2=0, V3=0.

- [x] **WEAPON-SUFFIX-EMP: Standardize EMP weapon names to _EMP suffix**
  — DONE 2026-07-31: Renamed 62 EMP weapons across 44 files (179 lines
  changed) via `tools/rename_emp_weapons.py`. Handles: EMP suffix ->
  _EMP, mid-name EMP -> _EMP_, compound EMPAA -> _EMP_AA, EMPulse ->
  _EMP_Pulse, ArcTeslaFragment sub-variants. Case-insensitive global
  replacement catches Weapon:, Weapons: list entries, and Inherits:
  references. Skipped DREMPDeviceSound (audio VoiceSet) and EMPGrenade
  (EMP is prefix). Boot-gated: menu reached, 0 new exception logs.

- [x] **WEAPON-SUFFIX-AA: Standardize anti-air weapon names to _AA suffix**
  (2026-07-31) — per corrected DESIGN.md §1 rule: `_AA` marks the
  air-only sibling of a **dual-weapon actor** (an actor/template that
  equips two separate weapons via different `Armament` traits — one
  ground-capable, one air-only — e.g. an Anti-Air Tank). Standalone
  AA-only weapons with no ground-capable sibling on the same actor (SAM
  Sites, etc.) are intentionally excluded, as are single weapons whose
  own `ValidTargets` already covers both Ground and Air.
  **Renamed 111 weapons** via `tools/rename_aa_weapons.py`
  (structurally-scoped exact-token replacement — top-level def key,
  `*Weapon:`/`*Weapons:` fields, indexed superweapon lists,
  block-context-gated `Inherits:` — never a blind substring match).
  Verified: `audit_weapon_suffixes.py` X3 = 0, `audit_orphans.py`
  dangling weapon refs = 0, `audit_inherits.py` V3 dangling = 0, rename
  script is idempotent (second run finds nothing to do).
  **Bugs found/fixed during this task** (see `docs/LESSONS_LEARNED.md`):
  an earlier draft of the rename script did a blind file-wide
  word-boundary substitution of bare weapon names, corrupting unrelated
  Tooltip/Name/RequiresCondition/Prerequisite text and comments across
  ~30 files (reverted via `git reset --hard` before merge, never
  pushed); `AA_LEGACY_KEYWORDS` including bare `"aa"` silently excluded
  every weapon that already contained "AA" without an underscore;
  identical names reused across actor/weapon/sequence namespaces (e.g.
  `sow_mech_avenger`, `d2k_aircraft_eater`) required block-type gating
  before renaming `Inherits:` or top-level definition keys; many
  weapons declare `ValidTargets` only on a `^Template` ancestor,
  requiring Inherits-chain resolution.
  Effort: M. See DESIGN.md §1.

---

## Superweapon Documentation Audit (2026-07-25, COMPLETED)

Full cross-reference of all superweapon and support power YAML traits vs
`FACTIONS.md`. Raw data: `docs/audit/latest/superweapon_audit.yaml`.
Summary: `docs/audit/SUMMARY.md` § "Superweapon documentation audit".

**14 findings** — all FACTIONS.md discrepancies FIXED:
- SW-001 (HIGH): Harkonnen Palace has `^PrimarySuperweapon` but no power trait (parked faction, not a regression)
- SW-002 (MED): Forgotten superweapon corrected from "Tiberian Wildlife Rampage" to "Nuclear Missile"
- SW-003 (MED): CABAL corrected — added Nuclear Missile, removed unimplemented "Satellite Hack"
- SW-004–011 (LOW): Added missing support powers (Cluster Missile, Chrono Reinforcements, Force Shield, EMP Disable, Traitors, Slow, Invisibility, Bloodlust, Haste) + fixed name mismatches (Meteor Blitzkrieg, Chaos Storm)
- SW-012–014 (INFO): Added Drop Pods, Federation Support Teleport to reference table; noted Protoss reuses SteelIonCannon

**WIP factions discovered** (not in FACTIONS.md): Warzone 2100, Worms, Win98, Warcraft 1, WH40K all have superweapon traits in rules/ YAML. Document when factions become active.
